# Rules for every agent working on the overnight surprise

The user asked for things to be built overnight as a surprise. They are asleep. Nobody can answer questions or approve anything, and the session runs with permission prompts off, so nothing will stop a mistake. Follow these rules exactly.

## Hard limits

0. **One exception to rules 1, 3 and 4:** if your brief says you are a maintenance agent. For one of the user's own maintenance skills, run that skill as written and let its own rules decide what you may change. For any other maintenance work, read `MAINTENANCE.md` in the run folder and change only what its safe-fix rule allows, after copying the original into `maintenance/before/`. In both cases a CLAUDE.md, or a rules file one points to, is edited only as "CLAUDE.md files: extra care" in `MAINTENANCE.md` allows. Rules 2, 5 and 6 and the rest of this file still apply to you; skip any step that would break them and say so in your report.
1. **Write only inside your assigned output folder** under the run folder (and your scratchpad or /tmp for throwaway files). Everything else on this computer and in every account is read-only to you.
2. **Never delete anything, anywhere.** Not files, emails, tasks, events, drafts or branches. Leave your own scratch files in place too.
3. **Never move, rename or edit an existing file or folder** outside your output folder. Do not tidy or fix things where they live; note them in your README instead. No git commands that change a repo (no commit, add, checkout, stash, pull, push). No installs (no brew, npm install, pip install).
4. **Nothing leaves this computer and nothing reaches other people.** No email, drafts, messages, comments, posts, calendar events, and no writes to any task manager, support desk, spreadsheet, document, finance or list app. No publishing, no deploys, no scheduled tasks, no uploads, no purchases, no sign-ins. Read-only web lookups are allowed only when your brief says so, and never with anything about the user in the query.
5. **Never read an off-limits path.** Your brief lists them. Do not open, mount, attach, list, copy, move, hash, search or read one. Never mount a disk image. Exclude each off-limits path from every recursive search, walk or copy that starts at the home folder or above it.
6. **Reading is otherwise allowed across this computer,** with two practical limits. Paths that the operating system guards with a permission prompt (on a Mac: `~/Library/Group Containers`, Photos, Mail, Messages, Safari, Contacts, Notes) are read only if your brief says preflight cleared them, because a prompt nobody answers stalls the night. Secrets are never read or printed: shell environment files, keychains, browser cookies and saved logins, and any API key, token or password you happen to see.
7. **Work material** may be read if your brief says so. Do not query work tools (support desks, project trackers, chat) unless your brief says to, and keep customer and colleague names out of anything the user might show someone.
8. **Health and finance records** may be read if your brief says so. What you write from them stays in your output folder, cites the file each fact came from, and gives no medical, legal or investment advice.
9. **Do not use a visible browser or computer-use tools.** The user's screen is unattended. To check a page, use headless Chrome through `_tools/cdp.mjs` in the run folder (`import { open } from "../_tools/cdp.mjs"`), then read the screenshot.
10. **Large files** (video, audio, datasets over about 50 MB) go in the cache folder named in your brief, not in the run folder, which may sync to the cloud.
11. Do not start further agents unless your brief says you may. If you do, give each the same model your brief names, and stop them before you finish.
12. **If your brief gives a deadline, keep it.** Check `date` before each new piece of work. At the deadline, stop, write up what you have, and finish. Do nothing after it: the user's weekly usage limit resets then, and nothing may be spent after the reset.

## Truth

- Do not invent facts about the user, their household, their home or their history. A detail that is not in their own files is left out, or is plainly fiction (a boss fight with a vacuum cleaner is fiction; a habit attributed to a real pet is a claim).
- Every number is computed, not estimated, and every fact the user might rely on names its source.
- Say what you did not verify.
- People: <names, pronouns and household facts that must be right, filled in by the user>.

## Writing style (every word the user will read: page copy, docs, READMEs)

<The user's house style goes here. The original skill used these rules:>

- No em dashes. Use commas, periods, colons, or restructure. En dashes only in numeric ranges.
- Straight quotes and apostrophes only (' and "), never curly. A page meant for one of the user's site repos follows that repo's own rules instead.
- Plain and direct. No cute idioms, no metaphors standing in for plain description, no hype adjectives (effortless, seamless, elegant, magical), no "isn't just X, it's Y", no announcer sentences that only point at the next sentence.
- Warm and a little playful is fine in a game's dialogue or a fun page. The plain-writing rules are about prose.

## Web pages you build

- Vanilla HTML, CSS and JavaScript. No frameworks, no build step, no CDN links, no external fonts or images. Everything works when opened from `file://` with no network.
- Works in current Safari and Chrome, at laptop and phone widths.
- Respects `prefers-color-scheme` and `prefers-reduced-motion`.

## When you finish

Write `README.md` in your output folder: what you built, how to open it, what you verified and how, what you did not verify, and any assumption you made. Be honest about gaps. A README is the signal that you finished, so write it last. Your final message back is a short factual report with the same content, including anything that failed.
