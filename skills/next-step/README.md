# next-step

A Claude Code skill for finishing a task when you cannot hold the whole job in your head. Type `/next-step` with whatever context you have (a to-do, a topic, a link, a screenshot, some notes), and Claude does the research and every part of the task it can do itself, then gives you one short numbered step per message and waits for "done". No reasons, no options, no recaps: just the next thing to do, with the exact screen labels and values to type.

## Install

Copy this folder to `~/.claude/skills/next-step/`. It needs nothing else, but it works better with:

- An MCP for your task manager (Things, Todoist, Reminders, Asana), so Claude can read the to-do you name and, at the end, mark it done. With no context given, the skill continues whatever you are working on in the session and otherwise asks; it never picks a to-do for you.
- Connectors for your mail, calendar and cloud drive, so Claude fills gaps from your own records instead of asking you.
- Writing rules in your `~/.claude/CLAUDE.md`, which the skill follows for any email or message it drafts for you to paste.

At the end of each walk-through, Claude adds a short note on what got in the way to `improvement-log.md` in the skill's folder, and from time to time proposes changes there for you to review. It never changes the skill itself.

Claude never sends, pays or deletes anything in this loop; those steps are yours. Publishing is yours only when no API or connector can do it; otherwise Claude publishes after your go-ahead.
