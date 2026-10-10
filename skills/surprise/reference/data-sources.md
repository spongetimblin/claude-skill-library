# Data sources for a surprise run

Where to learn what the user would like, and how to read each source without changing it or raising a prompt. Fill this in for the user. The original skill listed about twenty sources; the rows below show the shape, with the kinds of source that mattered most on its first run.

Rules that apply to every row: read-only, never through a visible browser after the user has gone to bed, and anything that raises a permission prompt is tried once in preflight or skipped. Work files, tools and accounts are not sources: the user's job is out of scope in every run.

## Sources the user named

| Source | How to read it | Notes |
|---|---|---|
| Task manager | Its MCP tools or export files | Old tasks and anything filed under "someday" are the best signal of what has been languishing. Never add, edit or complete a task. Some task apps hide repeating tasks from their API; do not report one as missing on the strength of an API read. |
| Mail | The mail connector's search and read tools | Preflight: confirm which account the connector is signed into. Search before asking the user anything; the answer is often in a thread. Never send, reply, forward or draft. |
| Calendar | The calendar connector's list and search tools | Appointments and deadlines in the next two weeks. Never create, change or respond to an event. |
| Cloud files | The local sync folder | Note which file types are pointers rather than content (a Google Sheet or Doc in a Drive folder is a small JSON file holding an id; read it through the Drive connector instead). |
| Personal site or profiles | Local repo or the live site | The best plain statement of what the user loves, in their own words. |
| Apps and projects | Each project's `README.md`, `CLAUDE.md`, `TODO.md` or `TASKS.md` | What is built, what is parked, what the user has written down as a next step. |
| Pets, health, finances | Local folders, each starting from its own `CLAUDE.md` or README if there is one | Sensitive. Patterns from the user's own records only, with the source file cited for every fact, and no advice. |
| Notes | A notes vault or notes folder | Often the richest source of half-formed ideas. |
| Home folder | Desktop, Documents, Downloads, code | Read-only. Never the off-limits paths from the Setup section. |
| Browser bookmarks | The bookmarks file (Chrome keeps JSON under its profile folder) | What the user meant to get back to. |
| Music library, watch history and the like | Only what can be read without a signed-in browser or an automation prompt; an export file is the safe route | Lists of things the user means to listen to or watch. |

## Also worth reading

| Source | How to read it | Why |
|---|---|---|
| The user's Claude history | Claude Code transcripts under `~/.claude/projects/`, the app's session records, chat exports | What they keep asking for, what they corrected, what they liked. |
| Global and project instructions | `~/.claude/CLAUDE.md`, each project's `CLAUDE.md` | Their rules, and the dated incidents behind them. |
| Their skills and scheduled tasks | `~/.claude/skills/`, `~/.claude/scheduled-tasks/`, and each one's state and output | What already runs for them. Do not rebuild it. |
| A folder of parked notes | Local files | Notes the user filed for later, often with a written "next step". |
| The Surprises ledger | `<SURPRISES>/ledger.md` | Past surprises and how the user reacted. Read it first. |
| Media lists | Music, film, game and book lists | Things they mean to get to. |
| Their own work | Music, writing, podcasts, art | Material for retrospectives and "by the numbers" pages. |
| Memories and year-in-reviews | Local files | People who keep these like retrospectives. |
