---
name: open-in-chrome
description: Open the current project's home page (its index.html) in Google Chrome as a local file. Finds the file whether it sits in the project folder or in a site folder such as public/. Trigger on /open-in-chrome, alone or with a page name or path ("/open-in-chrome now", "/open-in-chrome writings/some-article"), and when the user asks to open, view or pull up the site, the project, the home page or a named page in Chrome or in the browser. Not for starting a dev server, the app's built-in Browser pane, driving Chrome with Claude in Chrome, checking a page yourself after an edit, or opening a live URL.
argument-hint: "[page]"
allowed-tools: Bash(~/.claude/skills/open-in-chrome/scripts/open-page.sh:*)
---

# open-in-chrome

One command does the job. Run it from the session's working folder, and add the page only when the user named one:

```bash
~/.claude/skills/open-in-chrome/scripts/open-page.sh [page]
```

With no page it opens the project's `index.html`. It looks in Netlify's publish folder first (from `netlify.toml`), then the project folder, then the usual site folders (`public`, `dist`, `build`, `_site`, `site`, `docs`, `www`, `out`, `src`), then up to three levels down.

A page can be a name or a path, with or without `.html`: `now`, `writings/some-article`, `prototypes/demo.html`. A path is tried from the shell's folder, the project folder and the site folder. A name that is not an exact path is searched for in the site folder.

Two options go before the page. `-C "<folder>"` looks in that folder when the shell is not in the project. `--dry-run` prints what would open and opens nothing.

In a worktree session the script opens the worktree's files, which is right: that is where the session's edits are.

## What the first line of output means

| Output | What to do |
|---|---|
| `OPENED <file>` | Reply with one sentence naming the file relative to the project folder, such as "Opened `public/index.html` in Chrome." Nothing else. |
| `AMBIGUOUS <why>`, then candidates | Nothing opened. Ask the user which one, with the candidates one per line. Run the script again with the chosen one as the page. |
| `NONE <why>` | Nothing opened. Say so in one sentence. |
| `NEEDS_SERVER <config file>` | Nothing opened. A generator or bundler builds the project (Hugo, Jekyll, Vite and others), so its pages do not work as local files, and an `index.html` in its output folder is a stale build. Say that in one sentence and name the dev command when the project makes it plain (`hugo server`, the `dev` script in `package.json`). Do not start the server unless the user asks. |
| `ERROR <message>` | Report the message. |

## Limits

- Open what was asked for. No page named means the home page, even if the session has been editing another page. "The page we're working on" in the user's words is a named page: pass its path.
- A page given as an exact path opens even in a `NEEDS_SERVER` project, so the user can still open one static file there.
- Opening is the whole job. Do not screenshot the page, read it, or check it afterwards; the point is for the user to look at it.
- Each run opens a new tab. The script does not look for a tab that is already open.

## Reflect and improve (SUGGEST ONLY)

Last step of a run, after the reply.

**This skill never edits itself.** It does not change its own `SKILL.md`, `scripts/open-page.sh`, the folder list, or the list of generator config files. It writes suggestions to a log that the user reviews. To act on them, the user says "review the open-in-chrome improvement log".

**Log:** `~/.claude/skills/open-in-chrome/improvement-log.md`. Newest entries on top. It lives in the skill's own folder because the skill runs in a different project each time and has no data folder.

### Friction note: only when something was off

A clean run writes nothing. This skill runs many times a day and a clean run is one command, so a "No notable friction" entry each time would double the work and bury the entries that matter. A clean run is `OPENED` on the first try with no correction from the user.

Otherwise, add a dated entry of one to three lines at the top of the log, naming the project. Things worth catching in this skill specifically:

- `AMBIGUOUS`: which project, what the candidates were, and which one the user picked. A project that is ambiguous every time needs a rule.
- `NONE` in a project that does have a page to open, and where that page was.
- `NEEDS_SERVER` in a project that works fine as local files, or the reverse: `OPENED` on a page that came up blank or unstyled because the project needs a server and the script did not recognize its config file.
- A page that opened but looked broken as a local file: root-absolute paths (`/assets/...`), a `fetch` that a `file://` page cannot make, an endpoint that only exists when deployed.
- The wrong file opened: a stale build folder, a prototype, the main repo's copy when the session was in a worktree, or the reverse.
- A page name the user typed that did not resolve, or matched several pages, and what was meant.
- A request for something the skill does not do: reusing an open tab, starting the dev server and opening `localhost`, another browser.
- Chrome did not come forward, or opened in an unexpected window or profile.
- `ERROR`, with the message.

### Synthesis

This skill is invoked by hand, so a fixed weekly synthesis does not fit. When writing a friction note, check the log and synthesize when **either** there are 5 or more friction notes since the last synthesis, **or** the last synthesis is more than 30 days old.

When it triggers, read the notes since the last synthesis, look for recurring patterns, and add a dated `## Synthesis` entry at the top with a short, prioritized list of concrete proposed refinements. Tag each `STATUS: AWAITING REVIEW`. Do not apply any of them.

### Heads-up

When a synthesis produced proposals, add one line to the reply pointing at the log. At most one heads-up per synthesis.
