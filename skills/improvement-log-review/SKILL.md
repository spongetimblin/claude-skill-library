---
name: improvement-log-review
description: >-
  Review and clear the Reflect-and-Improve improvement logs of the user's skills and scheduled
  tasks: decide each open item (apply, decline or defer), make the changes, mark each item's
  status, and report. Trigger on /improvement-log-review, alone or with "skills", "tasks" or
  names, and when the user asks to review, process, work through or clear the improvement logs
  or their backlog, or says "review the <name> improvement log". Not for adding the loop to a
  skill (use the prompt in reflect-and-improve-prompt.md for that).
---

# improvement-log-review

Works through the improvement log of every skill and scheduled task that has one, and clears its backlog. The logs come from the "Reflect & Improve" loop: each skill writes friction notes and proposals to its own log but never edits itself. This skill is the human-in-the-loop half: it reads the proposals, decides them, applies the ones that hold up, and records every decision. The prompt that adds the loop to a skill is `reflect-and-improve-prompt.md` in this folder.

A log's backlog is every item tagged `STATUS: AWAITING REVIEW`, plus any proposal in a friction note that no synthesis or review has covered yet. The review is finished when no item in a reviewed log is still waiting, apart from the few that step 4 says to put to the user.

**Default: apply and skip items as recommended.** Do not ask for approval item by item. Decide, make the change, record it in the log, and report at the end. (If you'd rather approve each item, change this line to say so.)

## Scope

- Skills in `~/.claude/skills/` and scheduled tasks in `~/.claude/scheduled-tasks/`. Add any other place your skills live (a project's `.claude/skills/`, a repo of cloud routines) to step 1.
- No argument means all of them. "skills" or "tasks" means that kind only. When the user names skills or tasks, review only those.
- **A paused scheduled task is skipped,** and named in the report, unless the user names it.
- A skill or task with no improvement log is skipped. Do not add the loop to it.

## 1. Find the logs

**Skills.** List every `improvement-log.md` in a skill folder or its `data/` folder, with its size and how many lines mention `AWAITING REVIEW`. Then list every `SKILL.md` that mentions an improvement log, a `"friction"` array, or "Reflect & Improve": a skill in the second list with no log in the first keeps its log somewhere else, and its `SKILL.md` gives the path. Read the folders as they are now, so a new skill is picked up automatically.

**Scheduled tasks.** A task's log usually sits next to the task's data, not in the task's folder. Grep each task's `SKILL.md` (and any instructions file it hands off to) for the log's path. A task that mentions no log has no loop.

**Paused tasks.** Check which tasks are enabled before reviewing (the scheduled-tasks tool's list, or your app's own record of them). Go by what it says now, not by what was paused last time.

**Notices about the logs.** A task's emails, chat posts and other notifications are only about its own job. None of them carries an improvement-log heads-up, a synthesis, a count of proposals, or a pointer to a log; this review is how the user hears about proposals. On every review that covers tasks, scan every task for rules that break this, whether or not it has a log:

```
P='heads-up|improvement (ideas|suggestions|notes)|pointer to the (improvement )?log|pointing ([a-z]+ )?(to|at) the (improvement )?log|friction synthesis|synthesis (email|section|line)|proposals? (are )?(waiting|awaiting review) in'
cd ~/.claude/scheduled-tasks && grep -n -H -iE "$P" */SKILL.md | grep -viE 'no heads-up|never mention|heads-up out of'
```

Run the same `grep` on any instructions file a task hands off to. Read each match. A rule that puts the log, a synthesis, proposals or a pointer to the log into an email, a chat post, a push notification or any other message that leaves the run is a notice: replace it with one line, `No heads-up (changed <date>): never mention the improvement log or its proposals in an email or any other notification. The user reviews every log with /improvement-log-review.`, and delete any send condition or subject line that exists only for the notice. This is a plain fix: make it without asking and name it in the report. A match that is not a notice stays, such as a line about a task's own proposals file or a note about a failed send. A hand-run skill's chat reply is not a notification, so a heads-up line there stays.

Two things about the counts:

- **The grep count is an upper bound.** A log's header usually mentions the tag while explaining it, and some logs strike a decided tag through. The real number of open items comes from reading the log.
- **Know what can be undone.** If a folder is a git repo, run `git status --short` before the first edit and keep the output, so `git diff` shows what the review changed. Files outside git (a cloud drive folder) get small targeted replacements, never a regenerated whole file.

## 2. Read before judging

Take one skill or task at a time. Finish it completely, including the record in its log, before starting the next, so an interrupted session leaves no log half-reviewed.

- **The log's header.** It sets that log's status words, where new entries go, its synthesis trigger and its archiving rule. Where the header and this skill differ, follow the header.
- **The whole log.** Read a log over about 100 KB in parts. If it has a "Carried forward from archived entries" section, read that too: an idea declined there is not proposed or applied again.
- **The file that holds the rules,** and every other file a proposal would change: `SKILL.md`, a task's instructions file, scripts, reference files, and the code of an app the skill drives.
- **The user's CLAUDE.md files.** A rule in one outranks a proposal in a log.

## 3. List the open items

- Every item tagged `STATUS: AWAITING REVIEW`.
- Every proposal in a friction note newer than the last synthesis or review entry, tagged or not. A note that only records what happened is not an item.

The same proposal raised in several entries is one item. Decide it once and mark it in every place it appears.

## 4. Decide each item

| Decision | When |
|---|---|
| **Apply** | The log's evidence supports the change, the problem still exists in the current files, and the change fits what the skill or task is for. |
| **Already done** | The current files already do it, or a later entry overtook it. Name where. |
| **Decline** | It happened once and has not come back, it conflicts with a later decision or a CLAUDE.md rule, it costs more than the problem does, or it was declined before. Give the reason in one sentence. |
| **Defer** | It cannot be settled yet. Name the specific run or event that would settle it. |
| **Ask the user** | See the list below. |

**Watch items.** Some entries record a change already made and stay open only because it was "not yet exercised in a real run". Look at the run notes after it. If a later run exercised it and it held, mark it resolved and name the run. If a later run showed a fault, the fault is the item. If no run has exercised it yet, defer it and say which kind of run would.

**Ask the user, and do not act, when the item would:**

- send, post or delete something outside this computer, change who receives a message, or switch a task between drafting and sending;
- change a scheduled task's schedule, enabled state, title, model, permission mode or working folder, or rename a skill or task;
- loosen a suggest-only rule or any other guardrail on what a skill or task may do unattended;
- cost money, or need a new key or secret;
- reverse something the user decided (an entry marked DECIDED or DECLINED, or a CLAUDE.md rule), or add or change a rule in a CLAUDE.md;
- turn on a preference of the user's that nothing in the log or the rules settles.

These items stay `AWAITING REVIEW`. Put them to the user at the end in one message: one line per item, with the recommended answer first. Everything else gets decided without them.

## 5. Apply

- Make the smallest edit that does what the proposal says, in the voice of the file being edited. Leave existing text as it is.
- Put the change in the file that holds the rule. When a task's `SKILL.md` only launches an instructions file elsewhere, the change goes in that file.
- When a change alters when or how a skill is triggered, update the `description` in its frontmatter too.
- When a file is moved or renamed, search for references to the old path and update them in the same step.
- **Files outside the skill's or task's own folder,** such as an app a skill drives, may be changed when the proposal is about that file. Read that project's CLAUDE.md first and follow it. Leave commits and pushes there to the user unless that CLAUDE.md says otherwise, and say in the report that they are waiting.
- **Test what can be tested.** Run a changed script against real input and compare with the result before the change. After editing instructions, reread the edited section against the rest of the file for contradictions. Do not run the reviewed skill or task itself as a test. If a change could not be tested, say so in the log and the report.
- If an edit turns out larger or riskier than the proposal suggested, stop that item, defer it with what was found, and move on.

**For scheduled tasks:** a task's `SKILL.md` is its whole prompt and is read fresh at each run, so an edit takes effect at the next run. Edit the file directly; never start a run from this skill. A task's data files (trackers, state, findings logs) are its own records: change one only when a proposal is about that file, and only the part it names.

## 6. Record it in the log

Use the status words the log's header defines. Where it defines none, use these, each with today's date:

- `STATUS: APPLIED 2026-10-01` and one sentence saying what changed and in which file.
- `STATUS: RESOLVED 2026-10-01` for an item that was already done or was overtaken, saying where.
- `STATUS: DECLINED 2026-10-01` and the reason.
- `STATUS: DEFERRED 2026-10-01` and what would settle it.

Change the `STATUS: AWAITING REVIEW` tag in place and add the sentence after it. Do not delete an entry or reword its reasoning; the entry is the record. If the log keeps a separate list of open items, bring it up to date as well.

Then add one review entry where the header says new entries go, at the heading level the log's other entries use, with one line per item: the decision, and what changed or why not. The heading depends on how the log triggers its synthesis:

- **The trigger counts friction notes since the last synthesis** (skills run by hand): `## 2026-10-01 - Review and synthesis (covers every note through 2026-10-01)`. The word "synthesis" makes the skill count its notes from this entry.
- **The synthesis runs on a calendar** (scheduled tasks): `## 2026-10-01 - Review`. Leave "synthesis" out, so the task doesn't take the review for the synthesis it still owes.

If the log is a `friction` array in a JSON state file, add one entry at the front of the array with notes that begin `REVIEW <date>:`, using a short script that loads the JSON, edits only the array and writes it back, and confirm the file still parses.

Do not add new `AWAITING REVIEW` proposals of your own. If the review turned up a problem the log does not mention, fix it when it is a plain error, and otherwise name it in the report.

## 7. Archive check

Check each reviewed log's size with `wc -c`. If it is over about 100 KB, archive it now, following rule G of `reflect-and-improve-prompt.md` in this folder. Read the rule from that file rather than working from memory.

## 8. Verify and report

Run `grep -n 'AWAITING REVIEW'` on every reviewed log. Each line that still matches must be header text, a struck-through tag, or an item being put to the user.

Lead the report with the result:

- One line per skill or task: how many items were applied, already done, declined and deferred, and how many are waiting on the user.
- Each decision the user might reverse, in one line.
- Each notice the step 1 scan removed, one line each (task and file).
- Changes made outside the skills and tasks folders, and any commit or push left for the user.
- Anything that could not be tested.
- The questions for the user, if any, as step 4 describes.
- The tasks skipped for being paused, and the skills and tasks skipped for having no log, in one line each.

Do not list every item. The review entry in each log is the full record.
