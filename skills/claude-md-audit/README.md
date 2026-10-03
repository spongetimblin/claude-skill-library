# claude-md-audit

A Claude Code skill that audits a CLAUDE.md against the project it describes: every checkable claim (paths, commands, counts, file names, workflows) is verified mechanically rather than read for plausibility, factual drift is fixed in place, and anything that would change what sessions are told to do is proposed for you to decide. It works on any CLAUDE.md; what to check is derived from the file itself.

## Install

Copy this folder to `~/.claude/skills/claude-md-audit/`, start a new Claude Code session, and type `/claude-md-audit` with the path to a CLAUDE.md or its folder. The skill asks you to confirm which file before it starts.

## The improvement log

The last section of `SKILL.md` has the skill write suggestions about itself to `improvement-log.md` in its folder (it never edits its own instructions). That file is not included here. Create it with one line, `<!-- New entries below, newest first. -->`, if you want the log, or delete that section of `SKILL.md` if you do not.
