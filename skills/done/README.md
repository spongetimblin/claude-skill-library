# done

A Claude Code skill for leaving a session with nothing forgotten. Type `/done` and Claude goes back through the session: every request you made, every step it gave you, every question left open, and everything it said it would do. It confirms each one at its source, then answers "Yes, you're done for now" or "Not yet", followed by what still needs you, what is waiting on someone else, and what it couldn't check. It reports only, and changes nothing except its own log.

You can add context: `/done sent: <link>`, `/done with the billing work`, or `/done skip the deploy check`.

## Install

Copy this folder to `~/.claude/skills/done/`. It needs Python 3 and nothing else, but it works better with an MCP for your task manager (Things, Todoist, Reminders, Asana), so it can confirm that anything waiting on someone else has a reminder. Without one, those items appear under "Couldn't check".

`scripts/session_text.py` prints any early turns that a long session's summary replaced, so a request made hours ago still counts. It reads the session's transcript under `~/.claude/projects/` and sends nothing anywhere.

## Reflect and improve

After each run the skill adds a short note to `improvement-log.md` in this folder, and every so often turns those notes into proposed refinements for you to review. It never edits itself.
