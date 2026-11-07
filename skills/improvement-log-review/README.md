# The /improvement-log-review skill and the Reflect & Improve prompt

Two halves of one pattern for skills that get better with use:

1. **`reflect-and-improve-prompt.md`** is a prompt you paste while building a skill or scheduled task. It adds a suggest-only "Reflect & improve" step: every run, the skill writes a short friction note to its own `improvement-log.md`, and now and then it proposes concrete changes, tagged `STATUS: AWAITING REVIEW`. It never edits itself.
2. **`/improvement-log-review`** is the skill that reviews those logs: it finds every log, decides each open proposal (apply, decline, defer, or ask you), makes the changes it recommends, marks each item's status in the log, and reports.

The background is in the "Make Your Skills Self-Improving" tip of [Claude Workflow Tips](https://chadtimbl.in/writings/claude-workflow-tips.html).

## Install

1. Copy the `improvement-log-review` folder to `~/.claude/skills/improvement-log-review/`.
2. To add the loop to a skill, open `reflect-and-improve-prompt.md`, copy the PROMPT block, and paste it into the conversation where you are building or reworking that skill.
3. If your skills or tasks live somewhere other than `~/.claude/skills/` and `~/.claude/scheduled-tasks/`, add those places to step 1 of `SKILL.md`.

By default the review applies and declines items as it recommends, without asking item by item, and stops to ask you only about things like sending messages, changing a task's schedule, loosening a guardrail or reversing your own decisions. To approve every item yourself, change the "Default" line near the top of `SKILL.md`.

## Run it

`/improvement-log-review` reviews every log. Add "skills" or "tasks" for one kind, or names to review only those (`/improvement-log-review app-audit`). Saying "review the app-audit improvement log" works too.

## What is in the folder

| File | What it is |
|---|---|
| `SKILL.md` | The review skill. |
| `reflect-and-improve-prompt.md` | The prompt that adds the loop to a skill, with optional parameters (autonomy, cadence, where the log lives). |

No warranty. Its author runs it every week or two across all of their skills and scheduled tasks.
