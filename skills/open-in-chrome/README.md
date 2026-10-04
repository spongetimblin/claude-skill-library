# open-in-chrome

A Claude Code skill for static sites: `/open-in-chrome` opens the home page of the project you are working in (its `index.html`) in Google Chrome as a local file, and `/open-in-chrome about` opens a named page. It saves switching to an editor or Finder to open the file yourself each time you want to look at a change.

It looks for the page in Netlify's publish folder, the project folder, and the usual site folders such as `public/` and `dist/`. If more than one page fits, it lists them and asks which. In a project built by a generator or bundler (Hugo, Jekyll, Vite and others) it opens nothing and says the project needs its dev server, because those pages do not work as local files.

macOS and Google Chrome only. The script opens the page with `open -a "Google Chrome"`; change that one line in `scripts/open-page.sh` to use another browser.

## Install

Copy this folder to `~/.claude/skills/open-in-chrome/`, start a new Claude Code session, and type `/open-in-chrome`. If the script will not run, make it executable with `chmod +x ~/.claude/skills/open-in-chrome/scripts/open-page.sh`.

## The improvement log

The last section of `SKILL.md` has the skill write a note to `improvement-log.md` in its folder when a run goes wrong, and suggest changes to itself there (it never edits its own instructions). That file is not included here. Create an empty one if you want the log, or delete that section of `SKILL.md` if you do not.
