---
name: surprise
description: >-
  Overnight surprise run: while the user sleeps, review what is known about them and build
  things they will be glad to find in the morning (something fun, something useful, a plan
  they can approve), in a new dated folder under the Surprises folder named in the Setup
  section. At most five items a run; the rest of the weekly budget goes to checking them and
  then to maintenance of what the user already has (apps, MCP servers, skills, scheduled
  tasks, websites). The run ends before the weekly limit resets. Nothing is sent or deleted,
  and nothing outside that folder changes apart from safe fixes made during maintenance.
  Trigger on /surprise, optionally with a hint ("/surprise something for the garden"), when
  the user asks Claude to surprise them, work while they sleep, or use up their tokens before
  they reset, and when they review, update, move or delete an item from a past run (to keep
  its RECORD.md and the ledger current). Not for a task the user has specified themselves.
---

# surprise

The user goes to bed and Claude works through the night. In the morning they find things they did not ask for by name and are glad to have: cool, interesting, useful, fun, and mostly things they would not have thought of themselves. The run uses the usage limits that would otherwise reset unused, and it carries on by itself after a 5-hour limit resets. It spends nothing after the weekly reset.

This skill has two uses. Starting a run is everything from "Rules for the whole run" through "Morning hand-off". If the user is instead reviewing, updating, moving or deleting an item from a past run, go straight to "After the run: reviews, updates and moves".

## Setup: fill these in before the first run

This is a sanitized copy of a personal skill. Everything that was specific to its author has been replaced with the placeholders below. Edit this section once; the rest of the file refers to it.

| Placeholder | What to put there |
|---|---|
| `<SURPRISES>` | The folder where every run gets a dated subfolder, for example `~/Documents/Surprises`. It also holds `ledger.md`, the short list of every past surprise and how the user reacted. Create the folder and an empty `ledger.md` before the first run. |
| `<CACHE>` | A folder outside cloud sync for large files (video, audio, datasets over about 50 MB), for example `~/Library/Caches/surprise`. |
| Off-limits paths | Anything on the computer that must never be read: a private disk image, a folder of someone else's files, a work drive. List each one in "Rules for the whole run" and in `reference/agent-rules.md`. Reading is otherwise allowed. |
| Data sources | `reference/data-sources.md` lists where to learn what the user would like and how to read each source. Fill it in for the user's own files, apps and connectors. |
| Maintenance skills | The user's own audit or housekeeping skills that carry a standing instruction to apply changes without asking, if any. They run first in `reference/maintenance.md`. Leave the list empty and maintenance starts at that file's next step. |
| `<APPS>`, `<WEBSITES>` | The folders that hold the user's app and website repos, so maintenance can find them. Written into "The order of work" in `reference/maintenance.md`. Skills, scheduled tasks and CLAUDE.md files are found under `~/.claude` and in each project. |
| Maintenance fixes | `reference/maintenance.md` lets the run apply two narrow kinds of fix outside the run folder while the user sleeps. Read its safe-fix rule before the first run. To make maintenance report-only, say so at the top of that file. |
| House style | The writing rules anything the user reads should follow. Written into `reference/agent-rules.md` under "Writing style". `scripts/stylecheck.py` checks for em dashes and curly quotes; change or drop it to match. |
| People | Names, pronouns and household facts that agents must get right (a spouse, children, pets). Written into `reference/agent-rules.md` under "Truth". |

## Rules for the whole run

These hold from the first tool call to the morning message, for the main session and for every agent it starts. Copy `reference/agent-rules.md` into the run folder as `RULES.md` and make every agent read it first.

**Never:**

- **Delete anything.** Not a file, an email, a task, a calendar event, a draft or a branch. Inside the run folder, leave even the run's own scratch files; say they can go and let the user decide.
- **Send any communication.** No email, text, chat message, comment, post, calendar invite or reply, and no email drafts either. Anything written for another person is a file in the run folder for the user to send themselves.
- **Reorganize.** Do not move, rename or edit any existing file or folder outside the run folder. Do not tidy, sort, dedupe or "fix" anything where it lives. A stale path or a typo found along the way goes in the morning notes. The one exception is "Maintenance with what is left" below.
- **Change any account or app.** Task managers, calendars, mail, cloud files, spreadsheets, documents, finance apps, GitHub, hosting providers, every site and app repo: all read-only. No commits, pushes, deploys, installs, upgrades, purchases, sign-ins, settings changes or scheduled tasks. The one exception is "Maintenance with what is left" below.
- **Read an off-limits path** from the Setup section. Do not open, mount, list, copy, move, hash, search or read it. Exclude it from every recursive search, walk or copy. Do not mount any disk image. Every agent brief repeats this rule.
- **Print or copy a secret.** No key, token or password, and no reading shell environment files that hold them.
- **Use a visible browser or computer-use tools after the user has gone to bed.** Their screen is unattended. Check pages with headless Chrome through `_tools/cdp.mjs` in the run folder (copied from this skill's `scripts/`).
- **Do anything that can raise a permission prompt while they are away.** A dialog nobody answers stalls the run. Sources that might prompt are tried once in preflight, while the user is present, or skipped.
- **Give medical, legal or investment advice.** Health and money surprises organize the user's own records, show patterns with their sources, and list questions for a professional.

**Fine:**

- Creating new things in the run folder.
- Plans, drafts, proposals and patch files that the user can review, edit and approve. A change to one of their repos or documents is delivered as a copy plus a patch, never applied.
- Reading pretty much anything on the computer and in the user's accounts, read-only, to learn what they would like (see "Know the user first"). The remaining limits on reading are practical ones: secrets are never read or printed, off-limits paths are never touched, and a source that raises a permission prompt is tried only in preflight.
- Read-only web lookups for public facts, with nothing about the user in the query.
- Running the user's other skills in proposal-only form, with their output redirected into the run folder and their state files left alone. Their maintenance skills are the exception: they run as written (see "Maintenance with what is left").

**Scope:**

- **Personal only. The user's job is out of scope in every run, and no option turns it on.** Nothing a run builds, reads, checks or reports on is work: not a work drive, work repos, work skills or scheduled tasks, exported work chats, or work tools and accounts (a support desk, a project tracker, chat, work mail). List each work location as an off-limits path in the Setup section. If a personal file turns out to hold work material, such as a work chat inside a personal export, leave it out and raise no finding about it.
- Something made for or about another person (a spouse, a friend) is fine as a file for the user. It is never shared with that person.

## Before they go to bed (preflight)

Keep this under two minutes of the user's time. They are still at the keyboard, so this is the only chance to get anything from them.

1. **Say what will happen** in two sentences, and that the result will be an `index.html` in a new folder. Say that once the items are built and checked, the rest of the budget goes to maintenance of their apps, MCP servers, skills, scheduled tasks and websites, which applies safe fixes only, and that `no maintenance` skips it.
2. **Power.** On a Mac, run `pmset -g batt`. If the computer is not on AC power, tell the user to plug it in now and wait for their reply. On this skill's first run the battery fell to about 1% and the Mac hibernated from roughly 1 AM until it was plugged in near 7 AM, so most of the night was lost; the app's keep-awake settings kept the Mac awake on battery, which is why it drained instead of sleeping. Also say: leave the lid open (a closed lid sleeps a Mac even on power, unless an external display is attached).
   Then make sure the computer stays awake: in the Claude desktop app, confirm "Keep computer awake while Claude works" is on (if it is off, tell the user; do not change it) and call the app's keep-awake tool for the session. If those tools are not in the session, start `caffeinate -ims` in the background for the length of the run instead.
3. **Permission mode.** Check the session's permission mode. If it is not the mode that skips permission prompts, tell the user one prompt will stall the whole night and ask them to switch it. They set it themselves.
4. **Model.** Check which model the session is on. If it is the top model, tell the user to switch it to the mid-size model in the app's model picker before they go to bed, wait for their reply, and check again. The main thread stays on its starting model all night and cannot switch itself. On the first run, orchestration alone used about 3 points of the top model's weekly limit in 30 minutes, and if that limit runs out the main thread stops and the run stalls. The flagship item still gets the top model through its own agent. If the user has walked away with the session on the top model, record it in `PROGRESS.md`, start no top-model agents that night so the main thread has that limit to itself, and keep the main thread's calls few.
5. **Usage.** Read each usage window's percent used and reset time with the app's usage tool, or ask the user for a screenshot of their usage page if the tool is not there. Tell the user the weekly percent used now, that the run will use all of it, when the weekly limit resets, and that the run ends before that reset and spends nothing after it. Say that `light` or `stop at N%` limits the run. Also tell the user what the night can actually spend: about 20 points of the weekly limit for each 5-hour window that opens before the reset (on the second run one full window moved it 18 points). A run with more weekly room than that cannot reach 100%, and they should hear so before they go to bed.
6. **Run folder.** Create `<SURPRISES>/YYYY.MM.DD <short name>/` and move the session there, so nothing has to be moved in the morning. Large binaries go in `<CACHE>/YYYY.MM.DD/` instead, because the run folder may sync to the cloud.
7. **Touch each data source once**, so any permission prompt appears while the user can answer it: one cheap read each from every connector and guarded folder in `reference/data-sources.md` this run might use. Note which answered. A source that fails or prompts is dropped for the night.
8. **Session title.** Give the session a title the user will recognize in their session list.
9. **One question at most**, and only if the answer changes what gets built. Otherwise tell the user they can go to bed, and start.

If the user invoked the skill and walked away, do steps 2 to 8 anyway, record what could not be confirmed in `PROGRESS.md`, and carry on.

## Know the user first

Spend the first stretch on the main thread learning what would land. This is cheap and it decides everything.

1. Read `<SURPRISES>/ledger.md`: every past surprise, how the user reacted, the idea bank, and the "do not repeat" list. Their reactions outrank everything below. For the detail on an item (what exactly was built, what they changed afterwards), open that run's `RECORD.md`.
2. Read the hint in `$ARGUMENTS`, if any. A hint steers the run; it does not have to be the only thing built.
3. Survey the sources in `reference/data-sources.md`. The signals that mattered most on the first run:
   - **What they say they love:** a personal site's "now" and favorites pages, profiles, the things they have made.
   - **What is parked:** a folder of pending notes, `TODO.md` and `TASKS.md` files in their projects, tasks that are old or filed under "someday", notes that end with "next step".
   - **What is dated soon:** appointments, releases and deadlines in the next two weeks, from their notes, task manager and calendar.
   - **Lists they keep:** spreadsheets and docs that are lists of things to get to.
   - **What already exists:** their skills, scheduled tasks and their outputs. Do not rebuild something a skill or task already does for them.
4. Write down eight to twelve candidates, then choose. A good night has a mix:
   - at least one thing that is plainly fun;
   - at least one thing that is useful this week;
   - at least one plan or proposal they can approve;
   - one flagship that gets the most care.
   Prefer things grounded in the user's own data over things anyone could be given. Prefer few finished things over many half-finished ones: each item costs the user time to review, and the cap is five.

Some kinds of surprise, as prompts and not as limits:

- Business ideas built on what the user already has (their apps, their site, their professional skills, their catalog of anything), each with a first step small enough to try.
- Tasks that have sat for months, carried as far as the rules allow: the research done, the draft written, the plan laid out, the options compared. The task itself is never marked complete or edited.
- Health insights from the user's own records: patterns across notes, a one-page brief before an appointment, questions to ask.
- A prototype page or feature for one of their sites or apps, in a copy, with a patch.
- A year-in-review or "by the numbers" page over data they have never seen charted.
- A printable brief for something coming up.
- A guide through a list they keep.
- A game, toy or piece of music made for them.
- A check they would not run themselves (dead links, stale paths, unused subscriptions, storage).
- The next step of a project they paused, done in a copy so they can compare.

Do not stay inside this list.

## Budget and models

The run exists partly to use limits that are about to reset, so read them and plan against them.

- Read usage at preflight, before each wave of agents, and whenever an agent finishes. Use `date` for times; do not estimate them.
- **How much to spend.** Use what is left, down to the stops below, whenever the run is started and however far off the weekly reset is. `stop at N%` in the invocation sets a lower final stop for that run. `light` means one or two small items and no more than 5 points.
- **The session cannot change its own model.** Model choice happens per agent, with `model` on the Agent call. If the main thread should run on a different model, the user picks it in the app before bed; preflight step 4 checks this and asks them to move off the top model.
- **Which model for what:**

| Work | Model |
|---|---|
| Orchestration on the main thread | the mid-size model. It runs on whatever the user started the session on, so preflight step 4 asks them to switch if that is the top model |
| The flagship creative or judgment-heavy item, and its final polish | the top model, one or two agents at most |
| Most builds, research and verification | the mid-size model |
| Bulk lookups and extraction that a second pass will verify | the small model |
| Anything computable (encodes, link checks, data passes, counts) | a script, which costs no tokens |

- **The top model may have its own weekly limit, and what is left of it at the reset is lost.** Before starting any agent on it, check that limit. When the weekly reset is more than 12 hours away, start no agent on it above 70% used, and if it passes 85% with agents still running on it, stop them and relaunch the same briefs on the mid-size model. When the reset is 12 hours away or less, spend it too: start top-model agents for the flagship, its polish and read-only reviews until it reaches 95%, then relaunch on the mid-size model. If the main thread itself runs on the top model, keep 5 points of it for orchestration and the morning message.
- **Stopping an agent does not stop the agents it started.** Stop the children too, or they keep spending.
- **5-hour window:** above 85% with more than 20 minutes to its reset, start nothing new until it resets.
- **Pace to the 5-hour window, not to a number of agents.** The weekly limit moves only as fast as the 5-hour windows are used. On the second run four mid-size-model agents at a time moved it about 2 points an hour, the second window was 21% used when new work stopped, and the run ended at 68% with 32 points unused. At every usage check, compare the 5-hour window's percent with a straight line from where it stood to 95% at its reset, or at 10 minutes before the weekly reset if that comes first. Behind the line: start more agents now. Ahead of it: start none until it is back on the line. Run a background timer that wakes the main thread every 30 minutes for this check; do not wait for an agent to finish.
- **Weekly all-models: spend all of it,** in four stretches. The lines cover the whole run, items included.
  - Below 90%: one agent per item, then as many maintenance agents as the pace needs. At most four of them may edit at a time, and never two on the same asset. Read-only agents (deep reviews, verifiers, patch reviews) have no fixed limit.
  - From 90%: no new agent that may edit beyond those already running. Read-only agents keep starting at the pace, and usage is read every 10 minutes so that the next two lines are not overshot.
  - At 95%: start no new agent that may edit anything, and do the morning hand-off. Every edit, the maintenance report and the hand-off are finished by 97%.
  - From there to 100%: read-only review only, as many agents as the pace needs, each adding its findings to `maintenance/all-findings.md` as it finds them, so that being cut off at the limit loses nothing.
  - `stop at N%` moves the 100 down to N and the other three lines down by the same amount.
- **Only two things end a run: the weekly limit is used, or the weekly reset is near. The user's wake time is not one of them.** The point of a run is to use what is left before the weekly reset. Do not read a wake time from the calendar, do not plan the hand-off around it, and do not slow or stop work because the user may be up. Preflight reads the reset time from the usage tool and writes it, with the hand-off time it gives, at the top of `PROGRESS.md`. On the second run a wake-up event on the calendar put the hand-off 45 minutes earlier than the reset required, and the user did not want that.
- **The weekly reset ends the run.** Read its exact time from the usage tool at preflight. Nothing is spent after it: no agent running, no tool call, no message, no scheduled check-in. Work back from the reset time R:
  - R minus 60 minutes: start no new agent that may edit anything.
  - R minus 45 minutes: stop any editing agent still running, with its children, and do the whole morning hand-off, "Reflect and improve" included.
  - Until R minus 10 minutes: read-only review may continue, one agent at a time.
  - R minus 10 minutes: stop every agent and its children, stop every timer, stop `caffeinate` if preflight started it, and end the turn. Leave nothing that can wake the session.
  - The main thread acts only when something wakes it. When the run starts, start two background timers, one for R minus 45 and one for R minus 10: `until [ "$(date +%s)" -ge <epoch seconds> ]; do sleep 30; done; echo "<which deadline>"`, run as a background command. Each wakes the main thread when it exits. If one exits early, check `date` and start it again. Check `date` at every wake, and put R minus 15 minutes in every agent's brief as its deadline.
  - If the main thread is woken after R anyway, do nothing and end the turn.
- Use background agents. Multi-agent workflow tools are for when the user has opted in to them.

## How many items, and what the rest of the budget is for

- **At most five items a run.** Fewer is fine. A hint that names a number ("/surprise two things") changes it for that run. The cap comes from the first run: it made eleven, reviewing them took the user a few hours, and two were not useful. Pick the five they would most want, lean toward small and specific, and make at least one of them fun.
- **Budget left once the items are built does not go to a sixth item.** It goes, in this order, to:
  1. Verifying and polishing the night's items (step 3 of "How to run the night").
  2. Maintenance of things the user already has (below), which carries on until a stop in "Budget and models" is reached.

### Maintenance with what is left

Maintenance does not end when the user's maintenance skills have run. It works through everything they already have and stops only when the weekly limit is used or the weekly reset is near.

- **Read `reference/maintenance.md` before starting.** Copy it into the run folder as `MAINTENANCE.md` and have every maintenance agent read it after `RULES.md`. It holds the order of work, the checks for each kind of asset, the safe-fix rule, the maintenance ledger and the report format. Copy `reference/read-only-review.md` into the run folder's `_briefs/` as well: every read-only review agent reads it before it starts.
- **The order of work:** the maintenance skills named in the Setup section; then whatever those skills skipped, CLAUDE.md files, skills, scheduled tasks, websites and apps, and the connected MCP servers; then a second pass that rechecks the night's changes, turns open findings into patch files, and reviews each asset in more depth, repeated until a stop.
- **CLAUDE.md files get extra care, in every step,** because they are a project's instructions. The one edit allowed in a CLAUDE.md, or in a rules file one points to, is replacing a stale path, filename, command name or count with the only correct one, proved by a command, with no word around it changed. Anything that touches a rule is suggest-only. The full conditions are in "CLAUDE.md files: extra care" in `reference/maintenance.md`, and they also bind the maintenance skills during a run.
- **The maintenance skills named in the Setup section run as written, apart from that CLAUDE.md limit,** each in its own agent, once the night's items are built. They may start while item verification is still running when the 5-hour window is under 70% used, because room left in a 5-hour window cannot be spent later. Otherwise they start once verification is done. Each must carry the user's standing instruction to apply what qualifies without asking, and each skill's own rules decide what may change: follow its "Never" list, its "apply only when" rule and its "ask the user" list exactly.
- **Everything after those skills follows the safe-fix rule in `reference/maintenance.md`.** A fix is applied only when it corrects a fact in a doc without changing what runs or what a session is told to do, or when it is a bug fix proved by a command that fails before the edit and passes after it. The original of every file changed is copied into `maintenance/before/` first. Every other finding, including anything that optimizes, restyles, rewords or changes a rule, is reported with a proposed fix or a patch file.
- **Maintenance is the one exception to "Reorganize" and "Change any account or app" above,** and only as far as those skills' rules and the safe-fix rule allow.
- **These rules of this skill still hold during maintenance:** never delete, never send a communication, never read an off-limits path, never print a secret, no visible browser or computer-use, and nothing that can raise a permission prompt. Nothing is committed, pushed or deployed unless a maintenance skill does so under its own rules. No scheduled task is started, created, enabled, disabled or deleted. This skill's own files are never edited; a problem found in them is a friction note. If a step needs one of these, skip that step and report it.
- **Never the user's job.** Run no maintenance skill that covers work, and leave out their work skills, tasks, repos, drives and exported work chats.
- **One short report,** `maintenance/README.md` in the run folder, in the format `reference/maintenance.md` gives: every file changed outside the run folder, at most ten findings waiting for the user, what was checked and clean, what was not checked, and where maintenance stopped. Every other finding goes in `maintenance/all-findings.md`. The report does not count toward the five. The morning page links to it in one line and the morning message says what was changed.
- **When it stops.** Whichever comes first: the weekly limit is used (edits end at 95%, read-only review runs to 100%), or the weekly reset is near (the times in "Budget and models"). It never stops for the hour or because the user may be up. `no maintenance` in the invocation skips all of it.

## How to run the night

1. **Set up the run folder:** `RULES.md` (from `reference/agent-rules.md`), `PROGRESS.md` (the plan, a status table, a log, and a recipe for relaunching an agent), `_briefs/<item>.md` for each item, `_tools/` (copy `scripts/` there), and `index.html` from `scripts/index-template.html` with every item marked `wip`. Write the index early: if the night is cut short, the user still finds a usable page.
2. **One background agent per item, five items at most,** each with its own subfolder and a brief that says who the user is for this item, which sources to read, what to build, how to verify it, and what to write when done. A `README.md` in the subfolder means the agent finished. Give briefs by file path so a relaunch is one short prompt. Running many agents fills the main thread's context (on the second run it reached 80% by 4 AM after about 50 agents), so keep every agent's prompt to a few lines that point at a brief file in `_briefs/`, with the rules all reviews share in one file.
3. **Verify each item as it lands,** before calling it done:
   - `python3 _tools/stylecheck.py <folder>` for the house style in anything the user will read;
   - look at one screenshot of anything visual;
   - for anything interactive, a scripted run in headless Chrome with no console errors;
   - for anything stating facts the user will rely on (dates, doses, money, facts about their life), a second agent that checks every claim against the primary source without reading the first agent's notes. On the first run this caught errors in a set of printable briefs and wrong facts in a game.
   - Nothing about the user's life is invented. A detail not in their own files is left out or labeled as fiction.
   - Before an item says something is unknown, unanswered or "not on file", search their mail, calendar and chat archives for it. On the first run the briefs left open questions that the user's mail answered.
   - Confirm every negative finding a second way. Anything an item calls dead, broken, missing, wrong or unanswered is rechecked with a different tool before it goes on the page (for a link: curl, then a real browser through `_tools/cdp.mjs`), and the page says how it was checked. A failure in the checking script is reported as the script's failure, and "could not check" is kept apart from "is broken". The first run's link check called two working sites dead, and the user's reaction was that they need to be able to trust the data they get.
   - Cut it down. The user found the first run's briefs overwhelming because they were so content-dense. Anything they will read or print holds only what they will use in the moment, in type they can read comfortably; the supporting detail goes in a separate file. Do not add a section because it could be relevant, and check whether the user already has their own version of the thing. The ledger's "What the user has said about how items should be" section has their words.
4. **Keep the index true:** `python3 _tools/set_status.py <run folder> "<item title>" ok|warn|wip "<note>"` after each verification, and a dated line in `PROGRESS.md`.
5. **Carrying on after a limit.** Agent completions wake the main thread, which is the main way the run continues. As a backstop, start one background timer for each 5-hour reset that comes before the weekly reset, set a few minutes after it, in the same form as the reset timers in "Budget and models". When one wakes the main thread, read `PROGRESS.md` and relaunch anything that died. Start none for after the weekly reset. Do not use scheduled check-ins for this: they failed to fire on both of the first two runs, and the timers fired every time. If an agent died at a limit, its folder has no `README.md`; relaunch it from its brief with "continue from the files already there".
6. **Maintenance, with all the budget that is left.** When every item is built and the 5-hour window is under 70% used, or once every item is verified, follow "Maintenance with what is left" and keep going down its list until a stop is reached. Do not end the run early because the maintenance skills have finished, and do not run past the weekly reset.
7. **Do not start what cannot finish.** From 60 minutes before the weekly reset, or once the weekly limit reaches 95%, start no new agent that may edit anything, and verify and write up. Read-only agents keep starting at the pace until the limit is used or until 10 minutes before the weekly reset; their findings go to `maintenance/all-findings.md`, and the report says where to find what came in after it was written. The user's wake time plays no part in this (see "Budget and models").

## Morning hand-off

Do it at whichever of these comes first: the weekly limit reaches 95%, or 45 minutes before the weekly reset. The user's wake time does not move it. In this order:

- Bring `index.html` up to date: every item `ok`, `warn` with the caveat, or `wip` with how far it got.
- If preflight started `caffeinate`, stop it.
- Check for leftover processes with `ps -axo pid,ppid,pcpu,etime,command | awk '$2 == 1 && $3 > 20'`. A process whose working folder (`lsof -a -p <pid> -d cwd`) is in the run folder or an agent's scratchpad belongs to the run. Stop each one the run left behind, with its children, and say in the morning message what was stopped. Rule 13 in `reference/agent-rules.md` has the background: on the first run, workers left by a stopped script used a CPU core each for almost six days.
- Write `RECORD.md` at the top of the run folder, following `reference/record-template.md`: the run's facts, then one section per item with what it is, where it was delivered, the state it was delivered in, where it is now, and "not yet reviewed" for the user's reaction. This is the lasting record of the session. It stays in the run folder whatever happens to the items later.
- Add the run to `<SURPRISES>/ledger.md`: the run's folder name, then one line per item (title, a phrase on what it is, "not yet reviewed"). The ledger is the short list the next run reads first; the detail lives in `RECORD.md`. The ledger, the maintenance ledger (`maintenance-ledger.md` in the same folder) and the improvement log are the only things this skill writes outside the run folder apart from maintenance fixes; what maintenance changed is listed in `maintenance/README.md` and under "Maintenance" in `RECORD.md`.
- Open `index.html` for the user, then one short chat message: what is ready, caveats that change what they should do, anything that failed or was skipped, and what was not verified. No claim that was not checked.

## After the run: reviews, updates and moves

**Look before asking, and advise instead of handing the user decisions.** When a review turns up an open question, check their mail, calendar, records and chat archives first, and ask only what no source can answer. Where a choice is a matter of judgment, make the recommendation, apply it, and say what was done so they can reverse it. Do not give them a list of decisions to make.

The user goes through the items afterwards, one at a time, in this session or a later one. They may ask for an item to be changed, moved to its real home (a prototype into a site repo, a brief into the folder it belongs with), or deleted. The overnight rules about not moving or deleting cover the unattended run; once the user is directing the work, do what they ask, and keep the record true in the same turn:

- **A reaction:** write it in that item's reaction line in `RECORD.md`, in their words, with the date. Put the matching keyword in the ledger (kept, used, liked, indifferent, do not repeat). Anything they never want again also goes in the ledger's "Do not repeat" list, and any idea they mention goes in its idea bank.
- **An update:** add a dated line under "Since then" saying what changed and why. Leave "Delivered" and "State when delivered" as written; they record what the user woke up to.
- **A move:** move it, then set "Where it is now" to the full new path, add a dated "Since then" line, fix the item's link in the run's `index.html`, and sweep for other references to the old path.
- **A deletion:** at the user's request only, and to the Trash. Set "Where it is now" to "deleted" with the date, and say why under "Since then".
- **A move of the whole run folder:** update the "This folder" line, and the folder name in the ledger if it changed.
- **A maintenance finding the user decides:** if they approve it, make the change and take it out of "Open" in `maintenance-ledger.md`. If they decline it, move it to "Declined" there with their reason, so no later run raises it. If they undo a fix the run applied, record that under "Declined" too.
- **"Keep going"** after a morning hand-off: resume "Maintenance with what is left" where `maintenance/README.md` says it stopped, under the same rules and stops, then bring the report and `RECORD.md` up to date. If the weekly limit has reset since the hand-off, say that carrying on would spend the new week's budget and wait for the user's answer.

A `CLAUDE.md` in `<SURPRISES>` can tell any session opened in that folder to do the same.

## Files

| What | Where |
|---|---|
| Rules every agent reads | `reference/agent-rules.md` (copied to the run folder as `RULES.md`) |
| Data sources and how to read each | `reference/data-sources.md` |
| Maintenance: order of work, checks, the safe-fix rule, report format | `reference/maintenance.md` (copied to the run folder as `MAINTENANCE.md`) |
| The brief every read-only review agent reads: what it may write, patch tests on copies only, the do-not-open list | `reference/read-only-review.md` (copied to the run folder as `_briefs/read-only-review.md`) |
| What maintenance has checked, and its open and declined findings | `<SURPRISES>/maintenance-ledger.md` |
| Headless Chrome driver, style check, index status setter, index template | `scripts/` |
| The record of one run: every item, where it is now, what changed, the user's reaction | `RECORD.md` in that run's folder (format in `reference/record-template.md`) |
| The short list across all runs: one line per item, reactions, do-not-repeat list, idea bank | `<SURPRISES>/ledger.md` |
| Friction and improvement log | `improvement-log.md` in this folder |
| Each run | `<SURPRISES>/YYYY.MM.DD <short name>/` |

## Reflect and improve (SUGGEST ONLY)

Last step of every run, after the morning message. On a night that ends at the weekly reset it is done before the reset, as part of the hand-off. It also runs when a run fails, stalls or is cut short; those runs matter most.

**This skill never edits itself.** It does not change its own `SKILL.md`, its rules, its budget thresholds, its model table, its reference files or its scripts. It writes suggestions to a log that the user reviews.

**Log:** `improvement-log.md` in this skill's folder. Newest entries on top. It lives in the skill's folder because every run writes to a different folder.

The log is about the skill. What the user thought of each surprise goes in that run's `RECORD.md` and the ledger, not here.

### Every run: friction note

Add a dated entry of one to three lines on what went wrong or wasted effort. Things worth catching in this skill:

- Power and sleep: whether the computer stayed awake all night, the battery level at the start and end, how long the run was actually working.
- Limits: each window's percent at the start and end, which limit was hit first, whether any agent died at a limit, and whether the thresholds above stopped work too early or too late.
- Model choices: an item that needed a stronger model than it got, or top-model budget spent on work a smaller model would have done as well.
- Continuation: whether the timers fired, and how the run resumed after a reset.
- Preflight: a source that prompted or hung overnight even though preflight passed, or a check the user had to be asked about that could have been read.
- Sources: one that was empty, stale, unreadable, or richer than expected.
- Verification: errors the second pass caught, and errors the user found that it missed.
- Rules: anything that came close to a rule in "Rules for the whole run", and any rule that blocked something the user would have wanted.
- The mix: too many items, too few, items that overlapped something the user already has.
- Maintenance: how far down the list the night got, what the second pass restored, any fix the user undid, and whether the report was short enough for them to read.
- The weekly reset: whether the timers fired, when the last agent stopped, and whether anything was spent after the reset.
- An agent blocked from writing a file, and anything left for the main thread to save.

"No notable friction" is a valid entry.

### Synthesis

This skill is invoked by hand and runs irregularly, so a fixed weekly synthesis does not fit. At the start of this step, check the log and synthesize when either there are 3 or more friction notes since the last synthesis, or the last synthesis is more than 60 days old and at least one new note exists.

When it triggers, read the notes since the last synthesis and the ledger's reactions, look for recurring patterns, and add a dated `## Synthesis` entry with a short prioritized list of concrete proposed refinements. Tag each `STATUS: AWAITING REVIEW`. Do not apply any of them.
