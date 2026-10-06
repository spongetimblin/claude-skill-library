#!/usr/bin/env python3
"""Client for the gworkspace-api-personal web app (the personal account,
you@example.com). See ../SKILL.md for the ops.

This is the personal skill's own copy. The work skill has a separate copy at
~/.claude/skills/ko-gworkspace-api/scripts/gws_call.py that calls only the
work web app. The two share no files, variables or state. A change to the
retry logic in one should be made in the other as well.

Why this exists: Google intermittently fails to deliver this web app's replies.
The script runs and finishes (the Apps Script execution log shows it), but the
reply, which Google serves from script.googleusercontent.com after a redirect,
stalls for 10 to 30 seconds and then comes back as a 404 page or a redirect
back to the web app. Sometimes the first request stalls too. A bare curl with
no timeout turns that into a hang or a non-JSON reply. Measured 2026-10-06:
12 of 40 pings failed this way in 23 minutes while every execution completed
in about half a second.

What it does: puts a timeout on both requests, and resends the ops that are
safe to send twice. For the ops that are not, it stops and says the outcome is
unknown, so the caller can read the sheet or doc back before sending again.

Command line:
  gws_call.py ping
  gws_call.py read_range '{"spreadsheet_id": "ID", "sheet": "Tab", "range": "A1:C5"}'
  gws_call.py write_range - < params.json          (params from stdin)
  gws_call.py --batch < steps.json                 (several calls, in order)

  A batch is a JSON list of steps, or {"defaults": {...}, "steps": [...]}.
  Each step is {"op": "...", ...params}; defaults are merged into every step.
  It prints one JSON line per step and stops at the first failure.

Python:
  sys.path.insert(0, os.path.expanduser("~/.claude/skills/gworkspace-api-personal/scripts"))
  from gws_call import call, ApiError, ReplyLost, NoReply
  result = call("read_range", spreadsheet_id="ID", sheet="Tab", range="A1:C5")

Exit codes: 0 ok. 1 the web app answered with an error. 2 no reply after every
retry. 3 the reply was lost for an op that is not safe to resend. 4 bad usage
or missing environment variables.

The token comes from the environment. It is never printed and never placed in
a process argument (a curl command line shows it in the process list).
"""

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

URL_VAR = "GSHEETS_PERSONAL_API_URL"
TOKEN_VAR = "GSHEETS_PERSONAL_API_TOKEN"

# Sending these twice leaves the sheet, doc or event in the same state as
# sending them once, so a lost reply is handled by sending again.
RETRY_SAFE = {
    "ping", "list_tabs", "get_headers", "read_range", "read_links", "read_notes",
    "doc_get_text",
    "write_range", "set_cell", "clear_range", "set_link", "set_note",
    "attach_to_event", "strip_meet",
    "doc_set_link", "doc_set_text_style", "doc_replace_paragraph",
}
# Everything else (append_rows, add_row, doc_replace_text,
# doc_insert_paragraph_after, doc_delete_paragraph) could apply twice.

POST_TIMEOUT = 60    # seconds to wait for the web app to run the op
# Seconds to wait for the reply. A healthy one takes under 1; a failing one
# stalls for 10 to 30 and then fails anyway. An op that can be resent gives up
# early and sends again. An op that cannot waits longer, because giving up
# leaves its outcome unknown.
REPLY_TIMEOUT_SAFE = 8
REPLY_TIMEOUT_UNSAFE = 30
ATTEMPTS = 5
BACKOFF = [2, 5, 10, 20]


class ApiError(Exception):
    """The web app replied {"ok": false}. Resending will not help."""


class NoReply(Exception):
    """No usable reply after every attempt, for an op that is safe to resend."""


class ReplyLost(Exception):
    """The request was sent but its reply never arrived, and the op is not
    safe to resend. The change may or may not have been made."""


class ConfigError(Exception):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _request(req, timeout):
    """Returns (status, location, body). Raises OSError on transport failure."""
    try:
        with _opener.open(req, timeout=timeout) as resp:
            return resp.status, None, resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return e.code, e.headers.get("Location"), b""
        return e.code, None, e.read()


def _not_sent(err):
    """True when the failure happened before Google could have received the request."""
    reason = getattr(err, "reason", err)
    return isinstance(reason, (socket.gaierror, ConnectionRefusedError))


def _parse(body):
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        return None
    return data if isinstance(data, dict) and "ok" in data else None


def _attempt(url, body, post_timeout, reply_timeout):
    """One try. Returns (state, data, detail); state is ok, not_sent, unknown or lost."""
    t0 = time.time()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        status, location, raw = _request(req, post_timeout)
    except (OSError, urllib.error.URLError) as e:
        state = "not_sent" if _not_sent(e) else "unknown"
        return state, None, "no response to the request after %.0fs (%s)" % (time.time() - t0, type(e).__name__)

    if not location:
        data = _parse(raw)
        if data is not None:
            return "ok", data, ""
        return "unknown", None, "the request got HTTP %s with no redirect" % status

    # The op has run. Its reply is waiting at the redirect target.
    t1 = time.time()
    host = urllib.parse.urlparse(location).netloc
    try:
        status, _, raw = _request(urllib.request.Request(location), reply_timeout)
    except (OSError, urllib.error.URLError) as e:
        return "lost", None, "the op ran, but its reply from %s timed out after %.0fs" % (host, time.time() - t1)
    data = _parse(raw) if status == 200 else None
    if data is not None:
        return "ok", data, ""
    return "lost", None, "the op ran, but its reply from %s was HTTP %s after %.0fs" % (host, status, time.time() - t1)


def call(op, attempts=ATTEMPTS, post_timeout=POST_TIMEOUT, reply_timeout=None,
         full=False, **params):
    """Run one op and return its result (the whole response when full=True).

    Raises ApiError, NoReply, ReplyLost or ConfigError.
    After a resent write, old_value / old_values in the result can already be
    the new value; the audit spreadsheet keeps the original.
    """
    url = os.environ.get(URL_VAR)
    token = os.environ.get(TOKEN_VAR)
    if not url or not token:
        raise ConfigError("%s / %s are not set in this shell. See apps-script/SETUP.md." % (URL_VAR, TOKEN_VAR))

    payload = dict(params)
    payload["op"] = op
    payload["token"] = token
    body = json.dumps(payload).encode("utf-8")
    safe = op in RETRY_SAFE
    if reply_timeout is None:
        reply_timeout = REPLY_TIMEOUT_SAFE if safe else REPLY_TIMEOUT_UNSAFE

    detail = ""
    for n in range(1, attempts + 1):
        state, data, detail = _attempt(url, body, post_timeout, reply_timeout)
        if state == "ok":
            if not data.get("ok"):
                raise ApiError(str(data.get("error")))
            if n > 1:
                data["attempts"] = n
            return data if full else data.get("result")
        if not safe and state != "not_sent":
            raise ReplyLost(
                "%s: %s. This op is not safe to resend, so nothing was resent. "
                "The change may or may not have been made: read the sheet or doc back before sending it again."
                % (op, detail))
        if n < attempts:
            wait = BACKOFF[min(n - 1, len(BACKOFF) - 1)]
            sys.stderr.write("[gws_call] %s: %s; attempt %d of %d in %ds\n" % (op, detail, n + 1, attempts, wait))
            sys.stderr.flush()
            time.sleep(wait)
    raise NoReply("%s: no usable reply after %d attempts (last: %s)" % (op, attempts, detail))


def _run(op, params):
    """Returns (exit_code, printable dict)."""
    try:
        return 0, call(op, full=True, **params)
    except ApiError as e:
        return 1, {"ok": False, "error": str(e)}
    except NoReply as e:
        return 2, {"ok": False, "error": str(e), "no_reply": True}
    except ReplyLost as e:
        return 3, {"ok": False, "error": str(e), "outcome_unknown": True}
    except ConfigError as e:
        return 4, {"ok": False, "error": str(e)}


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.stdout.write(__doc__)
        return 0 if argv else 4

    if argv[0] == "--batch":
        try:
            spec = json.load(sys.stdin)
        except ValueError as e:
            sys.stderr.write("batch input is not valid JSON: %s\n" % e)
            return 4
        defaults, steps = ({}, spec) if isinstance(spec, list) else (spec.get("defaults", {}), spec.get("steps", []))
        for i, step in enumerate(steps, 1):
            params = dict(defaults)
            params.update(step)
            op = params.pop("op", None)
            params.pop("token", None)
            if not op:
                sys.stderr.write("step %d has no op\n" % i)
                return 4
            code, out = _run(op, params)
            out = dict(out, step=i, op=op)
            print(json.dumps(out, ensure_ascii=False), flush=True)
            if code:
                return code
        return 0

    op = argv[0]
    raw = argv[1] if len(argv) > 1 else "{}"
    if raw == "-":
        raw = sys.stdin.read()
    try:
        params = json.loads(raw)
    except ValueError as e:
        sys.stderr.write("params are not valid JSON: %s\n" % e)
        return 4
    if not isinstance(params, dict):
        sys.stderr.write("params must be a JSON object\n")
        return 4
    params.pop("op", None)
    params.pop("token", None)
    code, out = _run(op, params)
    print(json.dumps(out, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
