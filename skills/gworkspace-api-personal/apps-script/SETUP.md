# gworkspace-api-personal Apps Script: one-time setup

This standalone script gives Claude a token-gated path to edit any Google Sheet or Google Doc your PERSONAL account (you@example.com) can edit, plus attach Drive files to calendar events. Nothing works until you deploy it from you@example.com. ~15 minutes.

## 1. Create the standalone script project

1. Go to [script.google.com](https://script.google.com) (signed in as the account that owns the sheets and docs) → **New project**. Name it `gworkspace-api-personal`.
   (Standalone, NOT Extensions → Apps Script from inside a sheet. Standalone is what lets it open any spreadsheet or document by ID.)
2. Delete the placeholder code and paste in the full contents of `Code.gs` (this folder).
3. In the left sidebar, next to **Services**, click **+** and add **Google Calendar API** (identifier must stay `Calendar`). This enables the advanced service used for event attachments.

## 2. Set the secret token

1. Generate a token in Terminal:
   ```bash
   openssl rand -hex 24
   ```
2. In the Apps Script editor: **Project Settings (gear) → Script Properties → Add script property**. Property: `SECRET_TOKEN`, Value: the generated token. (Generate a NEW token; do not reuse the work script's token.)

## 3. Deploy as a web app

1. **Deploy → New deployment → type: Web app**.
2. **Execute as**: Me. **Who has access**: Anyone. (The token is what gates it; requests without the token are rejected.)
3. Authorize the scopes when prompted (Sheets, Docs, Drive, Calendar). Make sure the OAuth consent screen shows the right account.
4. Copy the **Web app URL** (ends in `/exec`).

## 4. Store URL + token as env vars

Add to `~/.zshenv` (the `_PERSONAL_` in the names leaves room for a second deployment on another account):

```bash
echo 'export GSHEETS_PERSONAL_API_URL="PASTE_WEB_APP_URL"' >> ~/.zshenv
```

```bash
echo 'export GSHEETS_PERSONAL_API_TOKEN="PASTE_TOKEN"' >> ~/.zshenv
```

New shells pick these up automatically; restart any open Claude Code sessions that need them.

## 5. Test

```bash
curl -sL -H 'Content-Type: application/json' -d "{\"token\":\"$GSHEETS_PERSONAL_API_TOKEN\",\"op\":\"ping\"}" "$GSHEETS_PERSONAL_API_URL"
```

(Do not add `-X POST`: Apps Script 302-redirects the response, and forcing POST on the redirect returns a "Page Not Found" page instead of the JSON.)

Expected: `{"ok":true,"result":{"pong":true,...}}`. Then tell Claude it's deployed; the `gworkspace-api-personal` skill has it run `ping` + a read-only sanity check before first use on any sheet or doc.

## Notes

- **Redeploying after code changes**: Deploy → Manage deployments → edit (pencil) → Version: New version → Deploy. The URL stays the same. In Claude in Chrome, the `find` tool with plain-language queries ("Edit (pencil) button for the deployment", "Version combobox", "New version option", "Deploy button in dialog footer") located every control reliably; coordinate clicks on the Version dropdown did not.
- **New scopes need a fresh authorization, and redeploying does NOT prompt for it.** Learned on the work twin 2026-09-04 and applied here the same day when the Docs ops were ported: after adding code that touches a new Google service, run any function that uses it from the editor (Run button) and accept the "Authorization required" → "Review permissions" prompt before testing the web app. Otherwise every `doc_*` call fails with "cannot open document" while `ping` still works. For the 2026-09-04 port, a temporary `zzTestDoc()` that called `DocumentApp.create(...)` did double duty: it raised the prompt and created the throwaway test Doc. Two details: the function dropdown next to Run needs a click on the option's screen position (the `find` ref did not register the selection), and the OAuth consent opens in a separate popup window that Claude in Chrome's tab group cannot see, so a person has to click through that popup. Remove the temporary function afterwards, save, and re-verify the checksum; no new deployment is needed for the authorization to take effect.
- **Editing the code from Claude Code**: the Apps Script editor exposes Monaco at `window.monaco`. Read `monaco.editor.getModels()[0].getValue()`, checksum it against the local `Code.gs` (iterate characters, `t = (t * 31 + codePoint) % 4294967296`, same formula in Python and JS) and stop if they differ, because that means the deployed script has drifted from the file on disk. Then either `setValue(<full new contents>)` or, when the file is too large for one tool call, apply anchored replacements: for each `[old, new]` pair assert `v.split(old).length === 2` then `v = v.split(old).join(new)` (split/join, not `String.replace`, so `$` in the code cannot be misread as a replacement pattern). Re-checksum, click into the editor body, Cmd+S, confirm the header says "Saved to Drive", checksum once more. Typing into the editor would trigger auto-indent and auto-close; pasting via the clipboard raced with the user's own copying on 2026-08-27. Done via Claude in Chrome 2026-09-04.
- **Deployment history**: v1 2026-08-27 (initial), v2 2026-08-27 (description not recorded), v3 2026-08-27 (read_links, set_link), v4 2026-09-04 (read_notes, set_note), v5 2026-09-04 (Google Docs ops `doc_*` ported from the work twin's v7; tested end to end on a throwaway Doc, then trashed).
- **Audit trail**: every mutating call, sheet or doc, is logged to a "Claude Sheets Audit (gsheets-personal)" spreadsheet, auto-created in the personal account's My Drive on first write. Old cell values and old paragraph text are captured there (truncated), so accidental overwrites are recoverable by hand.
- **Revoking access**: delete the deployment (or change `SECRET_TOKEN`) and the whole write path is gone instantly.
- **Scope reality check**: the web app runs with the personal account's full Sheets/Docs/Drive/Calendar authority. The fixed op whitelist and the token are the entire safety boundary, so treat `GSHEETS_PERSONAL_API_TOKEN` like a password (it lives only in `~/.zshenv`; Claude is instructed never to print it).
- **Calendar allowlist**: `attach_to_event`/`strip_meet` only touch calendars listed in `ALLOWED_CALENDARS` at the top of `Code.gs` (currently just you@example.com). Edit there + redeploy to add one.
