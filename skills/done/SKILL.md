---
name: done
description: >-
  Check whether the user can leave the current session with nothing forgotten: what is finished,
  what still needs them, and what could fall through the cracks. Trigger on /done, alone or with
  context ("/done sent: <link>", "/done with the billing work", "/done skip the X check"), and when
  they ask "am I done", "are we done here", "anything else I need to do", or "am I forgetting
  anything". Reports only. Not for walking through a task (/next-step).
argument-hint: "[what you just did, what to check, or what you're skipping]"
allowed-tools: Bash(python3 ~/.claude/skills/done/scripts/session_text.py:*)
---

# done

The user wants to leave this session knowing nothing will fall through the cracks. Find out whether they can, and tell them plainly.

What they added: $ARGUMENTS

Count anything they say they did, and check it where you can. Leave out anything they say they're skipping or already know about. If they name a scope, check only that; otherwise check the whole session.

## Check

1. Read the whole session. Run `python3 ~/.claude/skills/done/scripts/session_text.py`, which prints any turns that were summarized out of your context, since early requests may be missing from it. If it says nothing was summarized, you already have everything.
2. List every request the user made, every step Claude gave them, every question still unanswered, and everything Claude said it would do.
3. Confirm each one at its source, not from memory: the file, thread, task, or event itself. An item this session already read back counts, unless it could have changed since. Check that work is committed and pushed, background jobs have stopped, and files worth keeping aren't only in a temporary session folder.
4. For anything waiting on another person or a later date, look for its reminder: a to-do in their task manager, or a calendar event. With no reminder, it counts as something the user needs to act on. If you have no way to look, list it under Couldn't check.

## Reply

Line one is the verdict. "Yes, you're done for now." means nothing needs them. Otherwise, write "Not yet." Never open with yes when something needs them, however small. If one of their questions went unanswered, answer it right after the verdict.

Then give these groups, leaving out any that are empty:

- **Needs you:** exact steps, in order.
- **Waiting on others:** who, what, and where the reminder is.
- **Couldn't check:** what, and why, only where the answer could change the verdict.

Leave out suggestions, polish, and anything optional. List only what the work they asked for requires.

Change nothing except the log below. If Claude can finish an item itself, end with one question asking whether to.

## Reflect and improve (suggest only)

Do this after the checks and before writing the reply, because the reply has to be the last thing in the turn. It runs even when the checks failed or stopped early. Never edit this `SKILL.md` or change how the skill works; only write to `~/.claude/skills/done/improvement-log.md`, newest entry on top, creating it if it doesn't exist.

- **Every run:** a dated note of one to three lines on what got in the way. Examples: a source that could not be checked, and why (a connector missing on this account); a waiting item with no obvious place to look for its reminder; `session_text.py` failing or printing too much to read; an item the user had already handled or didn't care about. If a later message shows the verdict was wrong, add that to the entry, because a missed item is the most useful thing this log can hold. "No notable friction" is a valid note.
- **Keep it free of names.** This skill runs in all kinds of sessions, so describe the kind of item ("a task", "an email reply"). Never quote the session or name a person.
- **Synthesis:** when there are 10 or more notes since the last synthesis, or the last synthesis is over 30 days old and at least one new note exists, read those notes and add a dated `## Synthesis` entry at the top with a short prioritized list of proposed refinements, each tagged `STATUS: AWAITING REVIEW`. Apply none of them. If it adds proposals, say so in one line at the end of the reply.
