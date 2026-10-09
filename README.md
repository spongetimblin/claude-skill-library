# Claude skill library

The skills I use in [Claude Code](https://claude.com/product/claude-code), published so anyone can use them. A skill is a folder with a `SKILL.md` that Claude Code loads when you type its slash command or ask for what it does in words. How I use skills, and much else, is in my article [Claude Workflow Tips](https://chadtimbl.in/writings/claude-workflow-tips.html).

Some skills are exact copies of what runs on my Mac. Others had my personal details (paths, names, data sources) replaced with placeholders, and each of those has a README or a setup section saying what to fill in before the first run. Nothing here reaches outside your computer unless its README says so.

## Install one

Copy the skill's folder into `~/.claude/skills/` (so `~/.claude/skills/search/SKILL.md` exists), fill in anything its README asks for, and start a new Claude Code session. Type `/` to see it in the menu.

## The skills

<!-- catalog:start -->
| Skill | What it does | How it is published |
|---|---|---|
| [`claude-md-audit`](skills/claude-md-audit/) | Audits any CLAUDE.md against the project it describes: verifies every checkable claim mechanically, fixes factual drift, and proposes rule changes for you to decide. | copy of the skill I use, with personal details replaced (2026-10-09) |
| [`gworkspace-api-personal`](skills/gworkspace-api-personal/) | Lets Claude write to your Google Sheets, edit your Google Docs and attach Drive files to Calendar events, through a token-gated Apps Script web app you deploy from your own account. | copy of the skill I use, with personal details replaced (2026-10-09) |
| [`open-in-chrome`](skills/open-in-chrome/) | Opens the home page of the project you are working in, or a page you name, in Google Chrome as a local file. For static sites, on macOS. | copy of the skill I use, with personal details replaced (2026-10-09) |
| [`search`](skills/search/) | Search your past Claude sessions by what was said in them: Claude Code, Cowork and exported Claude Chat conversations, with ranking, related-word search and title browsing. | exact copy of the skill I use (2026-10-09) |
| [`sessions`](skills/sessions/) | Lists your Claude Code desktop sessions by topic, using the emoji at the start of each title or the session's folder, and opens one. | exact copy of the skill I use (2026-10-09) |
| [`surprise`](skills/surprise/) | An overnight run that builds a few things you did not ask for and leaves them in a dated folder, then uses the rest of your weekly usage to check and maintain what you already have, with strict rules about what it may touch. | written by hand from the skill I use, with personal details removed (2026-10-09) |
| [`transcript-path`](skills/transcript-path/) | Replies with the full path of the current session's transcript file, ready to copy. | copy of the skill I use, with personal details replaced (2026-10-09) |
<!-- catalog:end -->

Published from my private skills repo by a script that copies the opted-in skills, scans the result for personal details and secrets, and commits only when the scan is clean. The date in the last column is when a skill was last published or, for a hand-sanitized one, last checked against the version I use.

## License

[MIT](LICENSE). No warranty; these are personal tools that work for me.
