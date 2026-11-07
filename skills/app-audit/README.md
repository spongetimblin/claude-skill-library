# The /app-audit skill

A Claude Code skill that audits every project in your apps folder against a fixed checklist and fixes only what is provably safe. It checks that each app's README and CLAUDE.md match the code, and looks for stale paths, secrets in files, `.gitignore` gaps, uncommitted or unpushed work, leftover files, dependencies with known vulnerabilities, and scripts that no longer pass their own checks.

It applies two kinds of fix on its own: changes that don't alter what an app does (a doc correction, a `.gitignore` line) and bug fixes it can prove with a command that fails before and passes after. Everything else goes into a ledger as an open finding for you to decide. During the audit it never commits, pushes, deletes, installs or deploys anything.

## Install

1. Copy the `app-audit` folder to `~/.claude/skills/app-audit/`.
2. Open `SKILL.md` and fill in the "Setup" table: your apps folder, any grouping folders, folders to skip, where your secrets belong, and which apps deploy when pushed.
3. Optional: install [uv](https://docs.astral.sh/uv/) so the Python vulnerability check (`uvx pip-audit`) can run.

## Run it

- `/app-audit` audits the apps that changed since their last audit.
- `/app-audit all` audits every app.
- `/app-audit my-app other-app` audits the apps you name.
- `/app-audit open` lists the findings still waiting on you, without auditing.

After the report, you can ask it to commit and push its edits, walk you through the open findings one at a time, or apply a finding it only reported.

## What is in the folder

| File | What it is |
|---|---|
| `SKILL.md` | The skill: scope, the "never" rules, the checklist, the apply rule, the ledger format, the report, and what it may do after the report. |
| `scripts/claude-md-paths.py` | Lists the backticked paths in a CLAUDE.md that don't exist in its repo. Read-only. |

The skill creates `audit-ledger.md` (findings per app) and `improvement-log.md` (its own suggest-only friction log) in its folder on first use.

No warranty. Its author runs it regularly on a mixed folder of Python, Node and Swift apps and MCP servers.
