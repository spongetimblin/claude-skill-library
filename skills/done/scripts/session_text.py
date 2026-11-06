#!/usr/bin/env python3
"""Print the turns of this Claude Code session that were summarized out of context.

A long session's context replaces its early turns with a summary, so a request or
promise made there can be missing when /done runs. The transcript still has them,
but it can be over 100 MB, nearly all of it tool output. This prints only the
user's and Claude's own words, in order, up to the last summary; anything after
that is still in context. Standard library only.

    python3 session_text.py                 this session
    python3 session_text.py PATH.jsonl      another transcript
    python3 session_text.py --all           every turn, not only the summarized ones
    python3 session_text.py --max-chars N   longest text kept per message (800)
    python3 session_text.py --out FILE      where to save the text if it is too long to print

Text longer than PRINT_LIMIT characters is saved to a file instead (--out, or a file in
the system's temporary folder), and only the user's own messages are printed, one short
line each, followed by the file's path. Read or grep the file for the rest.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
SKIP_TAGS = re.compile(r"<(system-reminder|task-notification)\b.*?</\1>", re.S)
PRINT_LIMIT = 25000   # above this, a tool's display cuts the output, so save it to a file
LIST_CHARS = 120      # longest line kept per user message in the short list


def find_transcript():
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        sys.exit("CLAUDE_CODE_SESSION_ID is not set. Pass the transcript's path instead.")
    # Moving a session to another folder leaves a stale copy under the old folder.
    matches = sorted(PROJECTS.glob(f"*/{session_id}.jsonl"), key=lambda p: p.stat().st_mtime)
    if not matches:
        sys.exit(f"No transcript for session {session_id} under {PROJECTS}.")
    return matches[-1]


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def shorten(text, limit):
    if len(text) <= limit:
        return text
    head, tail = limit * 2 // 3, limit // 3
    return f"{text[:head]}\n[... {len(text) - head - tail} characters cut ...]\n{text[-tail:]}"


def main():
    parser = argparse.ArgumentParser(description="Print what was said in a Claude Code session.")
    parser.add_argument("path", nargs="?", type=Path, help="a transcript; default is this session's")
    parser.add_argument("--all", action="store_true", help="print every turn")
    parser.add_argument("--max-chars", type=int, default=800)
    parser.add_argument("--out", type=Path, help="file for the text when it is too long to print")
    args = parser.parse_args()

    turns = []
    last_summary = 0
    path = args.path or find_transcript()
    with open(path, errors="replace") as transcript:
        for line in transcript:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("subtype") == "compact_boundary":
                last_summary = len(turns)
            if entry.get("type") not in ("user", "assistant"):
                continue
            if entry.get("isSidechain") or entry.get("isMeta") or entry.get("isCompactSummary"):
                continue
            text = SKIP_TAGS.sub("", text_of(entry.get("message", {}).get("content"))).strip()
            if text:
                turns.append((entry.get("timestamp", "")[:16], entry["type"].upper(), text))

    shown = turns if args.all else turns[:last_summary]
    if not shown:
        print("Nothing in this session was summarized, so every turn is already in context.")
        return
    full = "\n".join(f"[{stamp}] {role}: {shorten(text, args.max_chars)}\n" for stamp, role, text in shown)
    if len(full) <= PRINT_LIMIT:
        print(full)
        return

    out = args.out or Path(tempfile.gettempdir()) / f"session-text-{path.stem}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(full + "\n", encoding="utf-8")
    users = [(stamp, text) for stamp, role, text in shown if role == "USER"]
    print(f"{len(full):,} characters is too long to print, so all {len(shown)} turns are saved in:\n{out}\n"
          f"Read or grep that file for Claude's side. The user's {len(users)} messages, one line each:\n")
    for stamp, text in users:
        line = " ".join(text.split())
        print(f"[{stamp}] {line if len(line) <= LIST_CHARS else line[:LIST_CHARS - 3] + '...'}")


if __name__ == "__main__":
    main()
