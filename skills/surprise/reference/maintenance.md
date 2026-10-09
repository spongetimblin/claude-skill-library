# Maintenance: what to check, what may be fixed, when to stop

The main thread reads this before maintenance starts and copies it into the run folder as `MAINTENANCE.md`. Every maintenance agent reads it after `RULES.md`.

Maintenance keeps finding work until the budget is used. It works down the list below and stops only at a stop in "When it stops". Nothing is spent after the weekly limit resets.

To make maintenance report-only, write that here, and treat every "apply" below as "report".

## The order of work

The list order is the priority when budget is short. One agent per asset, never two on the same asset. How many run at once is set by the pace rule in "Budget and models" in `SKILL.md`: at most four agents that may edit at a time, and as many read-only agents as the pace needs. The mid-size model for audits, the small model for bulk extraction that a script or a second agent verifies, a script for anything computable. Read usage before starting each agent.

1. **The maintenance skills named in the Setup section of `SKILL.md`,** as written.
2. **Whatever those skills skipped as unchanged:** run them again, naming what was skipped.
3. **CLAUDE.md files:** `~/.claude/CLAUDE.md`, any rules files it points to, and each project's CLAUDE.md.
4. **Skills:** each folder in `~/.claude/skills`.
5. **Scheduled tasks:** each one the user has set up (in the Claude desktop app, each folder in `~/.claude/scheduled-tasks`).
6. **Websites and apps:** each git repo under `<WEBSITES>` and `<APPS>` that no skill in step 1 already covers.
7. **Connected MCP servers:** one read-only call on each.
8. **The second pass** (below), repeated until a stop.

Step 1 follows those skills' own rules. Steps 2 to 8 follow this file. "CLAUDE.md files: extra care" below applies in every step, step 1 included. Within steps 3 to 6, take the asset checked longest ago first, going by the maintenance ledger.

**Left out of every step:** the off-limits paths from the Setup section; any folder the user has marked as archived or obsolete; `node_modules`, `venv`, build output and vendored code; this skill's own folder (a problem found in the surprise skill is a friction note in its improvement log). Without `work` in the invocation, also the user's work skills, tasks, repos and drives.

## CLAUDE.md files: extra care (every step)

A CLAUDE.md holds the instructions for a project, or for every project. This section covers `~/.claude/CLAUDE.md`, any rules files it points to, and every project's CLAUDE.md. It also binds the maintenance skills in step 1 for the length of the run: say so in those agents' briefs.

**The only edit allowed is replacing a stale path, filename, command name or count with the correct one,** and only when all of these hold:

- A command shows the old value is wrong (the path does not exist, the script is gone, the count differs) and shows the new value is right.
- Only one correct value is possible. For a path, exactly one file on the computer can be the intended target.
- The edit replaces that value and nothing else. No word around it changes.
- The value does not set what a session does. A threshold, limit, schedule, date, model name or person's name is a rule, even when it reads like a fact.
- The original is copied to `maintenance/before/` first. If the file is not in git, that copy is its only undo.

**Everything else is suggest-only:** a rule added, changed, reworded, moved or removed; a dead reference with no single replacement; a contradiction between rules; text that looks outdated or redundant; a missing rule. Report it with the exact text proposed.

**Each edit is reported by itself,** first under "Changed" in the report: the file, the line number, the old value and the new one. Before the hand-off, an agent that has not read the first agent's notes rechecks every one against the conditions above and restores the original where any of them fails.

## The safe-fix rule (steps 2 to 8)

**Apply a fix only when one of these is true:**

1. **It corrects a fact in a doc and changes nothing about what runs or what a session is told to do.** A stale path where exactly one file on the computer can be the intended target (search by filename; on a Mac, `mdfind -name`), a wrong filename, count or command name, a dead reference, a comment, a line added to `.gitignore`.
2. **It is a bug fix that is proved.** All of these hold: the file is in git and had no uncommitted changes when the agent started; a command shows the failure before the edit; the same command passes after it; the edit is the smallest one that does that; the project's own tests and checks still pass.

**Everything else is a finding, never applied.** It goes in the report with a proposed fix or a patch file. That includes:

- a change to a rule, step, threshold, trigger, description or instruction in a `SKILL.md`, a scheduled task's prompt or a CLAUDE.md, and the removal of anything from one;
- the user's own prose: site pages, articles, notes. A typo there is a finding;
- anything that optimizes, refactors, restyles, rewords or reorganizes something that works;
- any dependency change, and any deletion, move or rename;
- settings and registry files: `settings.json`, the desktop app's config files, launch agents, shell environment files;
- a file that had uncommitted changes of the user's when the agent started;
- anything the project's own CLAUDE.md forbids. Read it first; it outranks this file wherever it is stricter.

If it is unclear whether a fix is safe, it is not. Report it.

**Before the first edit to any file,** copy the original to `maintenance/before/<its full path>` in the run folder, so every change has an undo whether or not the file is in git. Make the smallest edit, in the voice of the file. The house style applies to new text unless the project's CLAUDE.md sets its own.

**Never, during maintenance:**

- commit, push, pull, merge, stash or deploy (a push may deploy a site or an app). The one exception is a push that a maintenance skill in step 1 makes under its own rules;
- install, upgrade or remove anything;
- start, create, enable, disable, update or delete a scheduled task, or invoke a skill to test it. Many of them send email or write to the user's accounts;
- run a project's session-start steps (pull, install, dev server) or its main action;
- run a build or check that leaves anything behind. Compare `git status --short` before and after; if it differs, say so in the report;
- anything in "Rules for the whole run" in `SKILL.md` that maintenance is not excepted from: no deleting, no sending, no off-limits paths, no secrets printed, no visible browser or computer-use, nothing that can raise a permission prompt.

## What to check

**CLAUDE.md files (step 3).** Verify each checkable claim against the project: paths, file listings, commands, script names, counts. Look for rules that contradict each other or another CLAUDE.md that applies to the same sessions. If the `claude-md-audit` skill from this library is installed, use its audit steps to find problems, and skip its confirmation, commit and reflect steps. Decide what may be edited by "CLAUDE.md files: extra care" above, not by that skill's fixing rules.

**Skills (step 4) and scheduled tasks (step 5).** Read-only unless the safe-fix rule allows the edit:

- every path named in `SKILL.md`, its reference files and its scripts resolves;
- every tool, skill, MCP tool and connector it names exists in this session;
- its scripts pass a syntax check (`bash -n`, `node --check`, `python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())"`);
- the frontmatter parses and `name` matches the folder;
- `SKILL.md`, its reference files and `~/.claude/CLAUDE.md` do not contradict each other;
- no step has stopped being possible as written.

For a scheduled task, also read its recent runs with the app's read-only tools (list tasks, list runs) and no other scheduled-task tool. Report a task whose latest runs failed or that missed its schedule. A paused task is checked and reported as paused.

**Websites and apps (step 6).** Read the repo's CLAUDE.md first. Then:

- git state: uncommitted work, unpushed commits, `.gitignore` gaps;
- links and image references in the source resolve to files in the repo;
- the checks its CLAUDE.md or README names, where they leave nothing behind;
- `npm audit --omit=dev` where there is a lock file;
- for a website, the live site, read-only, with curl and `_tools/cdp.mjs`: pages load, no console errors, no broken internal links, laptop and phone widths. A password-protected site is checked only as far as its password page. Confirm every negative finding a second way before reporting it.

**Connected MCP servers (step 7).** One cheap read-only call on each server in the session. Report any that fails or is missing. Their config files hold secrets and are read-only.

## The second pass (step 8)

When steps 1 to 7 are done and budget is left:

1. An agent that has not read the first agents' notes rechecks every change the night made against the safe-fix rule. A change that fails it is restored from `maintenance/before/` and reported.
2. Turn the highest-ranked open findings into patch files in `maintenance/patches/`, each with the command that shows the problem and its output after the patch is applied to a copy.
3. Review one asset at a time in more depth, read-only, the one reviewed longest ago first: bugs, speed, accessibility, security, and wording that no longer matches what the thing does. Findings and patches only.

Repeat step 3 until a stop. It is the only maintenance work allowed after the hand-off, and each agent doing it adds its findings to `maintenance/all-findings.md` as it finds them, so that being cut off loses nothing. If a whole round of it turns up nothing new, turn what is left to checking what exists: independent verifiers that try to disprove the serious findings from primary evidence, a code review of every patch that changes behavior, and reviews of code no agent has read yet. Stop only at a stop below.

## When it stops

The exact lines and times are in "Budget and models" in `SKILL.md`. In short, whichever comes first:

- **The weekly limit is used.** At 95%, start no new agent that may edit; every edit, this report and the hand-off are finished by 97%; read-only review runs on to 100%.
- **The weekly reset is near.** No new editing agent in the last 60 minutes before it, hand-off at 45 minutes before, every agent stopped at 10 minutes before. Nothing is spent after the reset.
- **The last hour before the user is likely to be up.** Start no new agent that may edit, and write the report. Read-only review keeps going at the pace until the limit is used or until 10 minutes before the weekly reset.

## The maintenance ledger

`<SURPRISES>/maintenance-ledger.md` covers steps 3 to 8. What the maintenance skills in step 1 track stays in their own records. Create the file on the first run if it is not there.

- Read it before step 3. A finding under "Declined" is never raised or applied again. A finding under "Open" is not reported as new.
- In the first pass, skip an asset that has not changed since its "Last checked" line (same git commit, or no file newer than that date) and has no open findings.
- After each asset, update its section: the date, the commit or newest file date, what was applied, and what is open.

One section per asset, in this format:

```
## <kind>: <name or path>

- **Last checked:** <date>, <git commit or newest file date>
- **Applied:** <date>: <file>: <what changed>
- **Open:** <date>: <finding>. Proposed fix: <one sentence or a patch path>
- **Declined:** <date>: <finding>. <the user's reason, in their words>
```

`<kind>` is one of: CLAUDE.md, skill, scheduled task, website, app, MCP server.

## The report

`maintenance/README.md` in the run folder. Keep it to one screen:

- **Changed:** every file changed outside the run folder, one line each: the path, what changed, which step, and that the original is in `maintenance/before/`. CLAUDE.md edits come first, each with its line number, old value and new value.
- **Waiting for you:** at most ten findings, the ones most worth the user's time first, one line each with the proposed fix or the patch file.
- **Checked and clean:** one line per step with counts.
- **Not checked, and why.**
- **Where it stopped:** the step, the time, and the weekly percent used.

Every other finding goes in `maintenance/all-findings.md`, ranked, one line each.
