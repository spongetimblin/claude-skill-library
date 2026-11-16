# transcript-path

A one-line Claude Code skill: `/transcript-path` replies with the full path of the transcript (`.jsonl`) of the session you are in, in a code block ready to copy. I use it to bring one session's context into another. I run it in the session that has the background, then paste the path into a different session with a line like "See this separate Claude Code session for context." Claude reads that transcript and picks up its decisions, drafts, and file paths, so I don't have to explain them again. Claude Code keeps every transcript under `~/.claude/projects/`, but the path includes a rewritten folder name and the session ID, so it's slow to find by hand.

Install by copying this folder to `~/.claude/skills/transcript-path/`. It needs nothing else. If the session's folder was renamed or the session was moved, the skill names the stale copy as well as the current one.
