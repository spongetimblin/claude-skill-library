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

1. Read the whole session. Run `python3 ~/.claude/skills/done/scripts/session_text.py --out <your scratchpad folder>/session_text.txt`, which prints any turns that were summarized out of your context, since early requests may be missing from it. If it says nothing was summarized, you already have everything. If those turns are too long to print, it saves them to that file and prints only the user's messages, one line each: list the requests from those, and grep the file for what Claude said it would do. If this check already ran earlier in the session, check only the work since then, plus whatever that run reported as still needing action or waiting on others.
2. List every request the user made, every step Claude gave them, every question still unanswered, and everything Claude said it would do. If the session followed a written process (an article, a checklist), list that process's own steps too, not only the ones the session mentioned. A question Claude asked counts only when its answer could change the work. A waiting item carried in from a handoff or a record file counts too; confirm it at the thread or task it lives in before calling it open, because the record can be stale. Findings that an audit or review reported earlier in this session and left for his yes or no count as well, even when the audit's own ledger records them: they go under Needs you, and the verdict is "Not yet."
3. Confirm each one at its source, not from memory: the file, thread, task, or event itself. An item this session already read back counts, unless it could have changed since. Check that work is committed and pushed, background jobs have stopped, and files worth keeping aren't only in a temporary session folder. When looking for leftover processes, count only what this session's tool calls started; a system process the session never ran (a window server, a virtual machine) is not a leftover. In a repo other sessions also write to, judge only the files this session's tool calls changed, not the whole `git status`. Uncommitted edits in a repo that an automatic backup job commits on a schedule count as handled; only a repo with no such job needs them committed and pushed. When you know which places such a job covers, count edits there as handled without looking the job up again. An empty search proves nothing: to-do searches often skip completed items, so check the completed or archived view (a logbook) before deciding a to-do is still open or was never made.
4. For anything waiting on another person or a later date, look for its reminder: a to-do in their task manager, or a calendar event. With no reminder, it counts as something the user needs to act on. A work task counts only if it has a due date. Anything else counts only if it will bring the item back without anyone having to remember it, such as a help desk conversation snoozed to a date, a project's to-do file that its own process reads, or a recurring routine's log that carries open items forward; a tag or an assignment doesn't count. A reminder due today or earlier counts as none, and so does an item tied to a later event today that has no reminder of its own. Look for a reminder by the subject line or title of what was sent as well as by the names of the people involved, and for a repeating to-do read today's list or the logbook instead of a title search, which fills with projected repeats. A meeting or calendar block on a later day that the item rides on counts, and so does a documented hand-off that moves the item to someone else, such as a task handed to code review; a check that exists only in this session counts only with the caveat that it ends when the app quits. An item whose answer arrives on its own in a place already read every day, where no answer means nothing is left to do (a submitted job application), goes under Waiting on others with that place named and does not change the verdict. If you have no way to look, list it under Couldn't check.

## Reply

Line one is the verdict. "Yes, you're done for now." means nothing needs them. Otherwise, write "Not yet." Never open with yes when something needs them, however small. If one of their questions went unanswered, answer it right after the verdict.

Then give these groups, leaving out any that are empty:

- **Needs you:** exact steps, in order.
- **Waiting on others:** who, what, and where the reminder is.
- **Couldn't check:** what, and why, only where the answer could change the verdict. A step reported as done that cannot be read back goes here only, and does not change the verdict.

Leave out suggestions, polish, and anything optional. List only what the work they asked for requires.

Change nothing except the log below. If Claude can finish an item itself, such as creating a missing reminder, end with one question asking whether to.

## Reflect and improve (suggest only)

Do this after the checks and before writing the reply, because the reply has to be the last thing in the turn. It runs even when the checks failed or stopped early. Never edit this `SKILL.md` or change how the skill works; only write to `~/.claude/skills/done/improvement-log.md`, newest entry on top, creating it if it doesn't exist.

- **Every run:** a dated note of one to three lines on what got in the way. Examples: a source that could not be checked, and why (a connector missing on this account); a waiting item with no obvious place to look for its reminder; `session_text.py` failing or printing too much to read; an item the user had already handled or didn't care about. If a later message shows the verdict was wrong, add that to the entry, because a missed item is the most useful thing this log can hold. "No notable friction" is a valid note.
- **Keep it free of names.** This skill runs in all kinds of sessions, so describe the kind of item ("a task", "an email reply"). Never quote the session or name a person.
- **Synthesis:** when there are 10 or more notes since the last synthesis, or the last synthesis is over 30 days old and at least one new note exists, read those notes and add a dated `## Synthesis` entry at the top with a short prioritized list of proposed refinements, each tagged `STATUS: AWAITING REVIEW`. Apply none of them. If it adds proposals, say so in one line at the end of the reply.
