---
name: claude-md-audit
description: Audit any CLAUDE.md against its real project — verify every claim, fix drift, flag rule problems
argument-hint: "[path to a CLAUDE.md or its folder] [commit]"
---

Audit a CLAUDE.md file so it is **accurate, current, internally consistent, and lean**. A CLAUDE.md is read at the start of every session in its project, so an error in it doesn't sit quietly — it steers every future session wrong. Projects change under their file constantly; assume drift and go find it.

**The standard: verify, don't read.** Audits that merely read a CLAUDE.md for plausibility miss real errors; audits that check its claims mechanically against the project find them. Check everything checkable. "It looks right" is not a finding.

This skill is project-agnostic: derive what to check from the target file itself, not from assumptions about any particular project.

## Step 0 — Resolve the target, then CONFIRM before auditing

Arguments: `$ARGUMENTS` (a path and/or the word `commit`).

- If given a **file path** to a CLAUDE.md: that's the candidate.
- If given a **folder path**: look for `CLAUDE.md` in that folder, and list any nested `CLAUDE.md` files below it (monorepos often have several).
- If given **no path**: look in the current working directory (and its ancestors up to the repo root), and mention `~/.claude/CLAUDE.md` (the global file) as a candidate too.

**Always confirm with the user before auditing** — even when the argument seems unambiguous. State what you found in one line (full path, size, last modified) and ask "Audit this one?" If several candidates exist, list them and ask which. Do not start the audit until they confirm.

## The audit, in order

**1. Read fresh.** The confirmed CLAUDE.md top to bottom, plus every companion document it cites (READMEs, protocol docs, style guides, contributing guides). Never audit from memory of a previous version.

**2. Catch up on what changed since the file last did.** If the project is a git repo: `git log` since the CLAUDE.md was last touched, looking for renames, moves, restructures, new tooling, and decisions the file doesn't yet reflect. Skim any changelogs, trackers, or handoff docs the file points to.

**3. Verify every checkable claim mechanically** — with `ls`, `find`, `grep`, not by eye. What counts as a claim depends on the file, but typically:
   - Every cited path resolves to a real file or directory. (Backticked *naming templates* like `YYYY.MM.DD_<name>.md` are not paths — don't flag them.)
   - Every referenced command, script, or make/npm target actually exists where the file says.
   - Directory structures and folder listings match reality — nothing missing, nothing phantom.
   - Tooling claims hold: gitignore contents, CI/hooks, config files, ports, env var names, scheduled jobs.
   - Embedded counts and "current state" statements are still true. **Prefer replacing volatile counts with pointers** to where the live number can be found, so they can't silently go stale.
   - Line-number references ("see lines 1-102") rot as files grow. Flag them even when they are currently correct, and suggest a descriptive anchor instead, such as a section name or element ID.
   - If other CLAUDE.md files apply to the same sessions (a global `~/.claude/CLAUDE.md`, parent or nested project files), check the target doesn't contradict them.

**4. Trace the file's own workflows through its rules.** This catches what fact-checking can't. Identify who reads this file (just the user? teammates? a non-technical collaborator?) and what a session literally following it would do in its common situations — session start, creating a file, editing, committing, responding to the people it names. Then:
   - Walk each prescribed workflow end to end. Does any step produce friction, contradiction, or behavior the file elsewhere forbids?
   - **Test rule pairs for collisions**: does any rule instruct what another prohibits? (Classic finds: a tidy-up rule that violates a never-touch rule; a startup checklist that violates a brevity rule; a filing rule and a placement rule giving opposite instructions for the same file.)

**5. Internal consistency.** Each rule stated once, with cross-references instead of restatements; "above"/"below" references point the right way; summaries match the full statements they summarize; section headers' claims about their contents are true; no task-list or pipeline state living in the rules file if the file says it belongs elsewhere.

**6. Bloat and gaps — "less is more," honestly applied.** Cut what isn't load-bearing: dead history, double descriptions, meta-commentary, rules for situations that no longer exist. But a **missing** rule is a finding too — a decision visible in the record (git history, referenced docs, the owner's stated intent) that no session would honor because the file never says it. Don't confuse brevity with health: a short file with a contradiction in it is worse than a longer file without one.

## Fixing rules

- **The project is the truth about its own state; CLAUDE.md conforms to the project** — never the other way around. Never change the project to make the file's claim true.
- **Fix factual drift directly** (stale paths, wrong counts, dead references). **Propose rule changes** — anything that alters what sessions are told to do — rather than making them silently; list them in the report for the user's decision. Never remove a rule without their explicit OK.
- After any consolidation, verify mechanically (string-match against the pre-edit version, e.g. `git show HEAD:<path>`) that **every load-bearing rule survived**.
- Follow the file's own conventions (date-stamped rules, origin notes, formatting). If it keeps rule origins in a companion file, put new origins there.
- Verify every edit on disk after making it.

## Report

Lead with the verdict, then: what was verified clean (so the clean bill is evidence, not vibes), each finding with its fix, proposed rule changes awaiting the user's decision, and the word-count delta with one honest sentence on whether the file got healthier or just shorter.

## Committing

By default, leave changes uncommitted and say so. If `$ARGUMENTS` includes the word `commit` and the project is a git repo: commit and push, staged **only** to the files this audit touched — never stage unrelated work sitting in the tree.

## Reflect and improve (SUGGEST ONLY)

Last step of every audit that got past Step 0. Do it after the audit and any commit, and before you send the report, so a heads-up can go in the report.

**This skill never edits itself.** It does not change its own `SKILL.md`, its audit steps, its fixing rules or its report format. It writes suggestions to a log that the user reviews. They act on them by saying "review the claude-md-audit improvement log".

**Log:** `~/.claude/skills/claude-md-audit/improvement-log.md`. Add each entry at the top, directly under the `<!-- New entries below, newest first. -->` marker, never at the bottom.

The log lives in the skill's own folder because every audit runs in a different project, so there is no stable data folder to put it in.

### Every run: friction note

Add a dated entry of one to three lines that names the audited file and covers what went wrong or felt wasteful. Things worth catching in this skill specifically:

- Claims that could not be verified mechanically, and why: a Google Doc or other cloud-only file, a URL behind a login, an env var whose value must not be printed, a path Drive would not resolve.
- False positives: a naming template, placeholder or deliberate piece of history flagged as broken, or a fix the user reverted.
- Whether the project was a git repo. Without one, step 2 has no history to read.
- Proposed rule changes the user declined, with their reason, so the same proposal is not raised again.
- Places where the line between fixing factual drift directly and proposing a rule change was unclear.
- Companion documents that were missing, stale, or too large to read in full.
- Whether Step 0 caught a wrong target, or the confirmation felt redundant.
- Whether the file got healthier or just shorter, when the word-count delta says something.

"No notable friction" is a valid entry.

### Synthesis

This skill is invoked by hand and runs irregularly, so a weekly Sunday synthesis does not fit. At the start of this step, synthesize when **either** there are 5 or more friction notes since the last synthesis, **or** the last synthesis is more than 30 days old and at least one new note exists.

When it triggers, read the notes since the last synthesis and look for recurring patterns. Before proposing anything, check the log for earlier proposals that were declined. Then add a dated `## Synthesis` entry at the top of the log with a short prioritized list of concrete proposed refinements. Tag each `STATUS: AWAITING REVIEW`. Do not apply any of them.

### Heads-up

When a synthesis produced notable proposals, add **one line** to the report pointing at the log. Do not send a separate message. At most one heads-up per synthesis.
