# Brief: read-only review

Every read-only review agent in a surprise run reads this first: deep reviews, verifiers and patch reviewers. Your prompt names one asset, a step name and a scope. This file holds the rules all of them share. It began as the brief the main thread wrote during the second run, after four read-only agents slipped in one night: a patch test ran against a real repo, `patch --dry-run` ran on real site files, a script opened a shell environment file, and a script compared a password with a public file.

The user is asleep. Nobody can answer questions or approve anything, and permission prompts are off, so nothing will stop a mistake.

Read first, in full: `RULES.md`, `MAINTENANCE.md` and `_briefs/maintenance.md` (if there is one) in the run folder. Then the asset's own CLAUDE.md, README and TODO or checklist files. They outrank the run's files wherever they are stricter, and anything they already list is known to the user and is not a finding. That includes a note saying something is kept on purpose.

## What you may write

You change no file of the user's. You write only:

- `maintenance/<step name>-report.md`
- lines appended to `maintenance/all-findings.md` with `>>`, as you find them, each starting `[<step name>]`
- patch files in `maintenance/patches/`
- temporary files in your own subfolder of the scratchpad, named after your step

Write report files with a shell command, not the Write tool.

## Do not repeat the night's work

Before you start, read the reports in `maintenance/` that cover your asset and the asset's lines in `maintenance/all-findings.md`. Report only what is new.

## Evidence and labels

- Every finding gives the file and line (or page and element), the input or path that triggers it, and why existing code or text does not already prevent it.
- Try to disprove each finding before you write it down.
- Label each: "reproduced on a copy", "measured", "confirmed by reading", "likely" or "worth checking". For a fact checked against a source: "matches", "differs", "not supported by the source" or "could not check".
- When a local copy or a local test stack exists, reproduce a "likely" finding before reporting it. After the second run, a password reset failure reported as "probably" was reproduced on a local stack in a few minutes.
- Confirm every negative finding (dead, broken, missing, wrong) a second way. A failure of your own script is the script's failure. "Could not check" is kept apart from "is broken". The user needs to be able to trust what you report.
- Do not pad. The report's first screen holds at most ten findings, ranked by harm. Say plainly where the asset is in good shape.

## Patches

- One finding per patch, the smallest change, in the voice of the file. Unified diff. Paths may have spaces, so put the apply command in a `#` comment at the top in this form and test that exact form on a copy: `patch -V none "<full path to the file>" < "<patch file>"`.
- Test on a COPY in your scratch subfolder only. Before any patch, build, script or server command, check that every path it writes to is inside your scratch subfolder. Never run `patch`, even with `--dry-run`, against a real file.
- Keep a file's line endings. Some files use CRLF, and rewriting them turns a three-line change into a whole-file change.
- Published words (site pages, posts, notes) and instructions (CLAUDE.md, SKILL.md, task prompts, guides) are the user's: give the exact replacement text in the report. Write a patch for those only when the change is one value with one clearly right answer.

## Limits

- No build, dev server, test run or generator in a repo folder. Serve or build a copy from your scratch subfolder, and stop it by parent id.
- No install, no deploy, no git command that changes a repo (no fetch). Compare `git status --short` at start and end.
- Network only as your prompt allows: plain GETs, one at a time with short pauses, nothing about the user or their household in any request. If a site blocks you, record "could not check" and do not try to get around it.
- Never read, print or compare a secret. Never open shell environment files (`~/.zshenv`, `~/.zprofile` and the like), shell history, `.env` files, keychains, token or credentials files. Config files are read for key names and structure only.
- Never: anything from the user's job (work drives, repos, skills, tasks and exported work chats), the off-limits paths your prompt lists, this skill's own folder (`~/.claude/skills/surprise`), or a folder the user has marked as archived or obsolete.
- No visible browser or computer-use tools. Headless Chrome through `_tools/cdp.mjs` only, and every one you start must be gone when you finish.
- Nothing that could raise a permission prompt.
- No subagents. No medical, legal or investment advice.
- Stop a script's children by parent id (`pgrep -P`), never by name. Before finishing, run `ps -axo pid,ppid,pcpu,etime,command | awk '$2 == 1 && $3 > 20'` and confirm nothing you started is in it.
- Check `date` before each new piece of work. Finish by the time your prompt gives, and do nothing after the deadline in it.

## Final message

The findings by label and seriousness, the top five in two lines each, the patches written, what you did not get to, and confirmation that nothing outside the run folder changed.
