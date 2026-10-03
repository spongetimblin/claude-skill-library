# Claude skill library

The skills I use in [Claude Code](https://claude.com/product/claude-code), published so anyone can use them. A skill is a folder with a `SKILL.md` that Claude Code loads when you type its slash command or ask for what it does in words. How I use skills, and much else, is in my article [Claude Workflow Tips](https://chadtimbl.in/writings/claude-workflow-tips.html).

Some skills are exact copies of what runs on my Mac. Others had my personal details (paths, names, data sources) replaced with placeholders, and each of those has a README or a setup section saying what to fill in before the first run. Nothing here reaches outside your computer unless its README says so.

## Install one

Copy the skill's folder into `~/.claude/skills/` (so `~/.claude/skills/search/SKILL.md` exists), fill in anything its README asks for, and start a new Claude Code session. Type `/` to see it in the menu.

## The skills

<!-- catalog:start -->
| Skill | What it does | How it is published |
|---|---|---|
| [`search`](skills/search/) | Search your past Claude sessions by what was said in them: Claude Code, Cowork and exported Claude Chat conversations, with ranking, related-word search and title browsing. | exact copy of the skill I use (2026-10-03) |
| [`surprise`](skills/surprise/) | An overnight run that builds a few things you did not ask for and leaves them in a dated folder, with strict rules about what it may touch. | written by hand from the skill I use, with personal details removed (2026-10-03) |
<!-- catalog:end -->

Published from my private skills repo by a script that copies the opted-in skills, scans the result for personal details and secrets, and commits only when the scan is clean. The date in the last column is when a skill was last published or, for a hand-sanitized one, last checked against the version I use.

## License

[MIT](LICENSE). No warranty; these are personal tools that work for me.
