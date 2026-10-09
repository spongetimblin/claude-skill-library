# The /surprise skill, sanitized

A Claude Code skill that works through the night and leaves things for you to find in the morning. This is a copy of a personal skill with the personal details removed: paths, names, data sources and house rules are placeholders for you to fill in.

It comes from the article "Claude Workflow Tips" at https://chadtimbl.in/writings/claude-workflow-tips.html, under the tip "Spend Your Leftover Tokens Before They Reset".

## Install

1. Copy the `surprise` folder to `~/.claude/skills/surprise/`.
2. Open `SKILL.md` and fill in the "Setup" table at the top: where runs go, where large files go, what is off limits, which of your own maintenance skills may apply fixes, where your apps and websites live, and your house style for writing.
3. Fill in `reference/data-sources.md` for your own files, apps and connectors, and the "Truth" and "Writing style" sections of `reference/agent-rules.md`. Put your app and website folders into "The order of work" in `reference/maintenance.md`.
4. Create the Surprises folder you named, with an empty `ledger.md` in it.

## Run it

Type `/surprise` before bed, optionally with a hint (`/surprise something for the garden`). The skill checks power, permissions and usage while you are still at the keyboard, then works until the morning and leaves an `index.html` in a dated folder.

A run spends all of your remaining weekly usage unless you limit it. It builds up to five items, then spends the rest on maintenance of what you already have: your apps, MCP servers, skills, scheduled tasks and websites. Edits and the morning report are finished by 97% of the weekly limit, and read-only review runs to 100%. The run ends before your weekly limit resets and spends nothing after it. `/surprise light` or `/surprise stop at 60%` limits a run, and `no maintenance` skips the maintenance.

Maintenance may change files outside the run folder, but only within the safe-fix rule in `reference/maintenance.md`: a factual correction in a doc, or a bug fix proved by a command. Read that rule first, and make maintenance report-only there if you prefer.

Run it in Bypass permissions mode, or the first permission prompt stalls the whole night. That is a lot of trust to extend, which is why the rules in `SKILL.md` and `reference/agent-rules.md` exist. Read them before the first run, and keep the computer plugged in with the lid open.

## What is in the folder

| File | What it is |
|---|---|
| `SKILL.md` | The skill: rules, preflight, how to pick items, budget, the night, the morning hand-off, and how to keep records afterwards. |
| `reference/agent-rules.md` | The rules every agent reads first (copied into each run as `RULES.md`). |
| `reference/data-sources.md` | A template for where to learn what you would like. |
| `reference/maintenance.md` | What maintenance checks and in what order, the safe-fix rule, the stricter rule for CLAUDE.md files, and when it stops. |
| `reference/record-template.md` | The format of each run's `RECORD.md`. |
| `scripts/cdp.mjs` | A small headless Chrome driver over the DevTools protocol, for checking pages without touching your screen. Needs Node 22+ and Google Chrome. |
| `scripts/set_status.py` | Updates an item's status on the morning page. |
| `scripts/stylecheck.py` | Counts em dashes and curly quotes in a folder. Change or drop it to match your own style. |
| `scripts/index-template.html` | The morning page. |

No warranty. It has run twice for its author, and the lessons from both runs are written into it. The rules for pacing a run to the 5-hour usage window were added after the second run, on 2026-10-09, and have not been through a run yet.
