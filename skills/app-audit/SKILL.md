---
name: app-audit
description: >-
  Audit the user's own apps (every project folder in one apps folder) against a fixed
  checklist: docs that match the code, stale paths, secrets in files, .gitignore gaps,
  uncommitted or unpushed work, leftover files, vulnerable dependencies, failing checks. Applies
  only provably safe fixes, records the rest in a ledger, and reports; commits or pushes only
  when the user asks afterwards. Trigger on /app-audit (alone, "all", "open", or app names) and
  when the user asks to audit, review, check over or tidy up their apps, the apps folder or one
  named app. Not a code review of a diff or PR, and not for building features or refactoring.
argument-hint: "[all | open | app names]"
---

# app-audit

Audits the user's apps against the fixed checklist in step 3 and applies the fixes that qualify under the rule in step 4.

This is an audit, not a code review. Do not read every source file looking for things to improve. The findings come from the checklist. Features, refactors, style, naming and performance are out of scope, apart from the short "noticed in passing" allowance in step 3.

**Standing instruction: apply only changes that do not alter what the app does, and bug fixes that are proved.** Do not ask for approval finding by finding. Decide, apply what qualifies, record everything in the ledger, and report at the end.

## Setup

Fill these in before the first run.

| Setting | Value |
|---|---|
| Apps folder | `~/code` (change this) |
| Grouping folders (folders whose subfolders are the apps) | none (for example `mcp/` for a folder of MCP servers) |
| Folders never audited | any folder named `zObsolete` or `archive` (change this) |
| Where secrets belong | environment variables in `~/.zshenv` (change this to your own rule) |
| Apps that deploy on push | none (name them, for example "pushing `my-site` deploys to Netlify") |

The ledger is `~/.claude/skills/app-audit/audit-ledger.md`. Create it empty on the first run.

## Scope

- An app is each folder directly inside the apps folder, and each folder directly inside a grouping folder. A grouping folder is not itself an app.
- **Never audit, read for findings, or change anything inside a folder on the "never audited" list,** at any depth.
- Never audit or edit third-party or generated code inside an app: `node_modules`, `venv`, `.venv`, `.build`, `dist`, `__pycache__`, and vendored library copies.
- Arguments (`$ARGUMENTS`):
  - none: the apps that changed since their last audit (step 1 says how to tell). An app with no ledger entry counts as changed.
  - `all`: every app.
  - one or more app names: those apps, changed or not. Match a name loosely against the folder names. If a name matches nothing, say so and carry on with the others.
  - `open`: do not audit. Read the ledger and list every finding under "Open", grouped by app, then stop.

## Never, during the audit

These hold from the start of a run until the report is sent. What changes once the user replies is in "After the report".

- Commit, push, pull, merge or stash. Pushing can deploy an app.
- Delete, move or rename a file or folder.
- Install, upgrade or remove a dependency, or run `npm install`, `pip install`, `brew` or anything like them. The one exception is `uvx pip-audit` in step F, which puts nothing in the app.
- Run an app's main action, installer or deploy step: no sending email, no scraping, no migrations, no loading or unloading LaunchAgents or services.
- Change anything outside the app's own folder, apart from this skill's ledger and improvement log. LaunchAgents, Claude Desktop's config and the user's shell profile are read-only here.
- Print, log or copy the value of a key, token or password. Name the file, the line and the variable only.
- Change an app's data files (state files, logs, exported archives, databases).

## 1. Find the apps

List every app with its git state. For each app folder, print its git repo path, current commit (`git rev-parse --short HEAD`), last commit date, the number of uncommitted files (`git status --short | wc -l`) and unpushed commits (`git log --oneline @{u}..`), or `NO GIT` with the date of its newest file. Read the folder as it is now, so a new app is picked up automatically.

Then read the ledger.

**An app is unchanged, and skipped on a run with no argument, when any of these holds:**

- Its current commit is the one the ledger recorded, and `git status --short` lists the same files the ledger recorded at the end of the last audit.
- Its commit has moved, but `git diff --name-only <ledger commit> HEAD` lists only files the last audit itself changed, and the working tree is clean: the user committed the audit's own edits. Update the commit in the ledger and skip it.
- Its commit has moved, but the diff lists only the app's to-do or done files (`TODO.md`, `TASKS.md`, `DONE.md`), alone or with files the last audit changed. Update the commit in the ledger and skip it.

An app with no git is unchanged when no file in it is newer than the ledger's audit date (`find <app> -type f -newermt <date> -not -path '*/node_modules/*'`).

## 2. Read before judging

Take one app at a time. Finish it completely, including its ledger section, before starting the next, so an interrupted session leaves no app half-audited.

- **The app's CLAUDE.md,** if it has one. Its rules outrank this skill wherever it is stricter. A dependency pin it explains is a decision, not a finding.
- **The app's README and any TODO, TASKS, DONE or checklist file.** Something already on the app's own to-do list is known. Do not report it again.
- **The app's section in the ledger.** A finding under "Declined" is never raised or applied again. A finding under "Open" is not reported as new.
- **What changed since the last audit:** `git log --oneline <ledger commit>..HEAD`.
- **The starting state.** Before the first edit, run `git status --short` and keep the output, so the audit's changes can be told apart from work the user had in progress. Never edit a file that already has uncommitted changes; report the finding instead.

## 3. The checklist

Run every check on every audited app. A check that does not apply (no dependencies, no CLAUDE.md) is skipped without comment.

**A. The docs match the code.** Verify each checkable claim in the README, the CLAUDE.md and any other doc that describes how the app works, with `ls`, `grep` and the code itself: paths, file listings, commands, script names, ports, env var names, install and run steps, what a setting does. The project is the truth and the doc conforms to it; a change to a rule in a CLAUDE.md is proposed, never made. To list the backticked paths in a CLAUDE.md that resolve to nothing, run `python3 ~/.claude/skills/app-audit/scripts/claude-md-paths.py <app folder> [extra base folder ...]`; routes, URL schemes and naming templates show up in its list too and need a look by hand. A dated entry in a changelog records what was true then and is not a current claim.

**B. Stale paths.** Absolute paths in scripts, plists, configs and docs that no longer resolve. Then the other direction, read-only: references to this app from `~/Library/LaunchAgents/*.plist`, Claude Desktop's `claude_desktop_config.json`, `~/.claude/skills` and `~/.claude/scheduled-tasks`. Check that each path they give for this app exists. The desktop config holds secrets, so grep it for the app's path only and never print a whole entry.

**C. Secrets in files.** Look for keys, tokens and passwords in tracked files, in files that sync to a cloud drive, and in git history for a file that was once tracked (`git log --all --oneline -- <file>`). A secret in a tracked file or in history goes at the top of the report. A value that is public by design is not a secret: a Supabase anon key or other `NEXT_PUBLIC_` value, a browser extension's public `key`, a certificate fingerprint. Work out what a key-shaped string is before reporting it, without printing it.

**D. Git state.** `.gitignore` gaps: generated or private files that are tracked or would be picked up by `git add -A` (`__pycache__`, `.DS_Store`, `node_modules`, `venv`, build output, `*.tsbuildinfo`, logs, a config file that holds a secret). Uncommitted work, unpushed commits, and an app with no git or no remote. Check every remote, not only the upstream: for each name in `git remote`, compare `git log --oneline <remote>/<branch>..HEAD`. Also run `git worktree list` and `git branch --merged` and report leftover worktrees and merged branches. A local branch that only mirrors a remote's default branch is not a leftover.

**E. Leftover files.** Backup copies (`*.bak*`, `* copy*`, `*.orig`), empty files, and build output or caches outside `.gitignore`. Google Drive's zero-size folder-icon files (named `Icon` followed by a carriage return) are not leftovers; exclude them with `-not -name 'Icon'$'\r'`. They are a finding only inside `.git/`, where they break `git fetch`.

**F. Dependencies with known vulnerabilities.** Read-only checks. Where there is a `package-lock.json`, run `npm audit --omit=dev` and report high and critical findings with the package and the fixed version, saying which `npm audit fix` fixes and which need a breaking upgrade. Decide that from `npm audit fix --dry-run`, which changes nothing, not from the "fix available via `npm audit fix`" line, which npm also prints for an advisory whose only fix is a major upgrade of the parent package. For a Python app with a virtual environment, run `uvx pip-audit --path <venv>/lib/python*/site-packages`. Audit the environment the installed command actually uses, found from its launch config or running process, which is not always the repo's virtual environment. In a uv environment, audit the folder that its `_uv_ephemeral_overlay.pth` file names (under `~/.cache/uv/archive-v0/`), which is where the packages are. Before proposing a major-version upgrade, check whether another installed package pins the version (`pip show <package>`, `npm ls <package>`) and say so in the finding. Check two more things before proposing one: that the library which calls the package works with the new major version, and that the advisory reaches the app at all (an advisory about a server handling untrusted input does not reach a client). Say in the finding what each check showed.

**G. It still passes its own checks.** Run only checks that send nothing, deploy nothing, touch no live data, and leave nothing behind:

- the app's tests, where it has them (`test.sh`, `npm test`), and the type-check and lint its CLAUDE.md names;
- `python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" <file>` on Python files (not `py_compile`, which writes `__pycache__` into the app), `bash -n` or `zsh -n` on shell scripts, `node --check` on JavaScript, `swiftc -parse <file>` on Swift files one at a time, `plutil -lint` on plists, and a parse check on JSON and YAML config.

A check that needs a local service that is not running is skipped and named in the report; do not start the service. A test that writes to a local service is skipped unless it is known to remove everything it writes. A test that rewrites a tracked file is followed by `git checkout -- <file>`, so the audit leaves nothing behind.

**H. Installed copies match the repo.** Where the app keeps a LaunchAgent plist or similar file that is installed elsewhere, compare the repo's copy with the installed one and report any difference.

**Noticed in passing.** Something outside the checklist may stand out while running it: a clear bug in code that was read, or a risk the user would want to hear about. Record at most three per app. Do not go looking for them.

## 4. Decide each finding

| Decision | When |
|---|---|
| **Apply** | It meets the rule below. |
| **Report** | Everything else that is real. It goes under "Open" in the ledger with the fix proposed in one sentence. |
| **Known** | It is on the app's own to-do list, or already under "Open". Not reported again. |
| **Declined before** | It is under "Declined" in the ledger. Skip it silently. |

**Apply a fix only when one of these is true:**

1. **It does not change what the app does when it runs.** Corrections to a README, a CLAUDE.md fact, a comment or a docstring; a stale path in a doc; a line added to `.gitignore`.
2. **It is a bug fix that is proved.** All four must hold: a command shows the failure before the edit; the same command passes after it; the edit is the smallest one that does that; and the app's existing tests and step G checks still pass. A stale path in a script counts when the old path does not exist and exactly one file on the computer can be the intended target.

**Everything else is reported, never applied.** That includes anything that would break a "Never" rule, and also:

- any dependency change, deletion, move or rename, and any refactor or cleanup of working code;
- a secret found in a file (moving it changes how the app reads it);
- a `.gitignore` gap where the file is already tracked: add the `.gitignore` line, and report the `git rm --cached` command;
- a change to a rule in a CLAUDE.md, or the removal of anything from one;
- a proved bug fix in an app with no git, where an edit has no undo (doc corrections there are still applied);
- a proved bug fix in a file that runs live from the repo with nobody present (a script a scheduler runs, an always-on server), since the edit takes effect at once;
- a fix to a file that had uncommitted changes when the audit started;
- in a fork, anything in the original author's code or docs that the user has not changed, unless it is a proved bug.

If it is unclear whether a change alters what the app does, it does. Report it.

## 5. Apply

- Make the smallest edit that fixes the finding, in the voice of the file being edited. Leave existing text as it is.
- Follow the app's CLAUDE.md for anything it says about how to edit, test or check the project.
- For a rule 2 fix, run the failing command before the edit and keep its output, then run it after. If the fix does not pass on the first attempt, undo it and report the finding.
- If an edit turns out larger or riskier than the finding suggested, undo it, report the finding, and move on.
- Leave every change uncommitted. The report says which apps have changes waiting.

## 6. Record it in the ledger

The ledger has one `## <app path>` section per app, in the order step 1 prints them. Edit sections in place with small targeted replacements. Its form:

```
## my-app

Last audit: 2026-10-01 at commit 3674ceb. Uncommitted at the end: CLAUDE.md, README.md.
Changed by the last audit: README.md.

### Open
- 2026-10-01 [C] `scripts/example.py` line 12 holds an API token in `TOKEN`. Proposed: read it from an environment variable.

### Declined
- 2026-10-01 [E] `notes copy.md`. The user keeps it on purpose.

### History
- 2026-10-01: applied 2, reported 1, checks skipped: F (no audit tool).
```

- The letter in brackets is the checklist item; `[P]` is a finding noticed in passing.
- **Open** holds every reported finding that is still true. At each audit, recheck each against the current code before carrying it forward, remove one that has been fixed, and say in the History line how many were cleared.
- **Declined** holds findings the user said not to raise again, each with their reason. Only the user moves a finding here.
- **History** gets one line per audit. Work done after the report gets its own line: `- 2026-10-01, after the audit, at the user's instruction: <what was done> (cleared 2).` When a fix was committed, name the commit, so the next audit can check it with `git show`.
- "Last audit" records the date, the commit, and the files `git status --short` lists at the end. "Changed by the last audit" lists the files this audit edited. Step 1 depends on both lines.

## 7. Verify and report

For each audited app, run `git status --short` again and confirm the only new entries, compared with step 2, are the files the audit meant to change. Rerun the step G checks on any app where code was edited.

Lead the report with the result:

- A secret in a tracked file or in git history, first, if there is one.
- One line per audited app: fixes applied, findings reported, earlier findings still open.
- Each new reported finding, one line each, most important first, with the proposed fix and a recommendation (do it soon, when convenient, or decline) with the reason and a rough size. Earlier open findings are counted, not listed; `/app-audit open` lists them.
- Each applied bug fix, one line each, with the command that proved it. Doc and `.gitignore` fixes are counted, not listed.
- The apps with uncommitted audit edits, and any with unpushed commits; the user can ask for the edits to be committed and pushed.
- Checks that could not be run, and why.
- The apps skipped as unchanged, in one line.

## After the report

The audit ends when the report is sent. What the user asks for next is their instruction, so the "Never" list no longer decides it. These rules do.

- **"Walk me through the open findings."** One finding per message, in ledger order: what it is, the recommendation first ("apply" or "decline") with the reason and a rough size. Wait for an answer before the next.
- **"Commit and push the audit edits."** In each app, stage only the files the audit changed, by name, never `git add -A`. Run `git fetch` first and stop if the branch is behind its remote. Follow the app's CLAUDE.md for anything it requires before a commit. One commit per app, saying what changed and that the app audit found it. Never force-push or amend. If a push deploys the app, say so and check afterwards that it still responds.
- **"Apply" or "fix" a reported finding.** Do it, keep the edit as small as the finding needs, and verify it as step 5 describes. After a dependency upgrade, run `pip check` or `npm ls` and import the app's main packages as well as re-auditing. Commit only if asked.
- **A deletion the user asks for is a move to the Trash,** never `rm`.
- **An install, an upgrade, a LaunchAgent change or a deploy** needs the user to name that action for that app. "Fix everything" does not cover it.
- **Secrets stay the user's.** Never write a key's value into any file. Give them a command that reads it into their secrets store without printing it.
- **Keep the ledger true.** Remove each cleared finding from Open, update "Last audit", and add the "after the audit" History line. A declined finding moves to Declined with the reason.

## Reflect and improve (SUGGEST ONLY)

Last step of every audit run, including one that failed or stopped early, before sending the report.

**This skill never edits itself.** It writes suggestions to `~/.claude/skills/app-audit/improvement-log.md` (newest on top; create it if missing). Findings about the apps belong in the ledger, not here.

Add a dated note of one to three lines about this skill's own friction: checks that misfired or reported false positives, steps the checklist missed, apps whose layout the scope rules didn't fit, apply-rule calls that felt unclear, and what the user asked for after the report (several requests of one kind are evidence about the apply rule). "No notable friction" is a valid note.

When there are 5 or more notes since the last synthesis, add a dated `## Synthesis` entry at the top with a short prioritized list of proposed changes, each tagged `STATUS: AWAITING REVIEW`, and mention it in one line of the report. Apply none of them.
