---
name: transcript-path
description: Give the user the full local file path of the transcript (.jsonl) of the Claude Code session they are in right now. The usual flow is typing /transcript-path on its own, often as a side question in the middle of other work. Also trigger when the user asks for it in words, such as "give me the local file path for the transcript of this Claude Code session", "what's the path to this session's transcript" or "where is this conversation's jsonl". Not for finding a different or older session's transcript, or for exporting, reading or summarizing a transcript.
allowed-tools: Bash(find:*), Bash(ls:*)
---

# transcript-path

Every Claude Code session writes its transcript to `~/.claude/projects/<working folder, with / and other punctuation turned into ->/<session ID>.jsonl`. This session's ID is `${CLAUDE_SESSION_ID}`, and looking it up finds:

!`find ~/.claude/projects -maxdepth 2 -name ${CLAUDE_SESSION_ID}.jsonl`

## Reply

Give the path in a fenced code block with no language tag, and nothing else. The user pastes the path into other sessions and tools, so the code block's copy button is what they need. The file's size, format and session ID are noise unless they ask.

Add one short sentence only when the lookup above is off:

- **Two paths.** Renaming the session's working folder, or moving the session to a different folder, leaves a stale copy under the old folder's name. Run `ls -lt` on both, give the most recently modified one, and name the other as a stale copy.
- **No path.** The file is created when the session's first message is saved, so the lookup can come up empty if this is the first message. Run the same `find` with the Bash tool. If the session ID above shows as a variable name rather than an ID, use `$CLAUDE_CODE_SESSION_ID` in its place. If the file is still missing, say so. Do not fall back to the newest file in the project folder, because another session open in the same working folder would make that the wrong file.
