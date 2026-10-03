# transcript-path

A one-line Claude Code skill: `/transcript-path` replies with the full path of the transcript (`.jsonl`) of the session you are in, in a code block ready to copy. Claude Code keeps every session's transcript under `~/.claude/projects/`, and the path is useful when you want another session, a script or a skill to read this conversation.

Install by copying this folder to `~/.claude/skills/transcript-path/`. It needs nothing else. If the session's folder was renamed or the session was moved, the skill names the stale copy as well as the current one.
