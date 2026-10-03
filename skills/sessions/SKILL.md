---
name: sessions
description: >-
  List the user's past Claude Code sessions on one topic and open one. A topic is an emoji; a
  session's topic comes from its folder, or the emoji at the start of its title, by the keys in
  config.json or the user's CLAUDE.md. Trigger on /sessions with a topic word or emoji
  ("/sessions health", "/sessions 🏥"), optionally a word to narrow by title, then "open 3";
  /sessions alone counts sessions per topic, "/sessions untagged" lists those with none. Also
  when the user asks "show me my health sessions", "which sessions were about X" or to "list my
  sessions on" a topic. Not for searching inside sessions, or renaming, moving, archiving,
  grouping or adding emoji to sessions.
allowed-tools: Bash(python3 ~/.claude/skills/sessions/scripts/sessions.py:*)
---

# sessions

Lists the user's past Claude Code sessions by topic, and opens the one they pick. It is the nearest thing Claude Code has to opening a Project in Claude Chat and seeing its chats.

The work is done by `scripts/sessions.py`. It reads the topic keys and the desktop app's own record of each session, and it never writes a file. How it decides a session's topic is written at the top of the script. Its settings are in `config.json` in this folder, and `README.md` describes them.

## Topics

A topic is an emoji. Two keys say what each emoji stands for: the folder key pairs emoji with folders, and the topic key pairs emoji with subjects. A session is on a topic when it ran in a keyed folder or a folder inside it, or else when its title starts with a key emoji. `config.json` can add a last rule, `fallback`, for sessions neither of those places.

The keys are written in `config.json`, or in a Markdown file it names with `keys_from`. Without that setting, they come from the "### Folder emoji key" and "### Topic emoji key" sections of `~/.claude/CLAUDE.md`, if it has them.

## 1. Work out the topic

The user gives a topic as a word or an emoji. Turn a word into the emoji it means, and pass the emoji, because the script only knows the words that appear in the keys themselves: it knows "health" when the key says "Health", but not "medical". If the keys are in the user's global CLAUDE.md, they are already in your context. If not, run the script with no arguments, which lists every topic.

- A word that fits no topic: say so in one sentence and list the topics. Do not pick the nearest one.
- "untagged" is passed as it is. It lists the sessions with no topic.
- No topic at all: run the script with no arguments, which prints a count per topic.

Anything after the topic is words to narrow the list. Every word has to be in the session's title or in the name of its folder.

## 2. Run it

```
python3 ~/.claude/skills/sessions/scripts/sessions.py '🏥'
python3 ~/.claude/skills/sessions/scripts/sessions.py '🏥' 'dentist'
python3 ~/.claude/skills/sessions/scripts/sessions.py
```

Put each argument in its own quotes. For a word with an apostrophe in it, use double quotes.

| The user asks for | Add |
|---|---|
| every session, not the 30 most recent | `--all` |
| a different number | `--limit N` |
| each run of a scheduled task, not one line per task | `--runs` |
| sessions held by another copy of the app, or by another account | `--everywhere` |

## 3. Reply

Reply with what the script printed, from its first line down to the end of the numbered list, and nothing else.

- Copy each line as it is, numbers included. The user goes by the numbers to say which one to open.
- Leave out the block that starts "IDS for --open". It is there for step 4, and the ids mean nothing to the user.
- No summary above the list, no remarks about what is in it, no offer after it.
- If the output ends with a "Problems:" section, pass each problem on in a sentence. A problem can mean the list is incomplete, so it must not be dropped.
- If the script says "No topics are set up", tell the user in a sentence or two that no topics are set up yet and where they go, as the script's message says. Do not write `config.json` or change their CLAUDE.md unless they ask.

## 4. Open a session

Only when the user asks, as in "open 3" or "open the dentist one". Find that number's id in the IDS block of the list you last ran, and run:

```
python3 ~/.claude/skills/sessions/scripts/sessions.py --open 'local_…'
```

The app switches to that session, in the copy of the app the user is in. This session keeps running, and the user comes back to it through the sidebar. Reply with one short sentence saying which session was opened, or with the script's reason if it refused.

- Take the id from the script's output, never from memory. If the list has scrolled out of your context, run the list again first.
- One session per request. If the user names two, open the first and say the second is next.
- Never open a session the user did not ask for. It changes what is on their screen.

## What it cannot do

- **Make a title in the list clickable.** Nothing in a reply can be clicked to open a session: the app shows a Markdown link to a session as plain text, and macOS hands a `claude://` link to whichever copy of the app it picks. That is why the list is numbered and opening is step 4.
- **Open a session held by another copy of the app.** The desktop app can be installed more than once, for example one copy per account. A session opens only in the copy, and under the account, that holds it. `--everywhere` lists the others by title, marked "cannot be opened from here".
- **Place a session that has neither a keyed folder nor a key emoji at the start of its title**, and that the fallback rule does not catch. Those are "untagged": usually sessions from before the user started giving titles an emoji, and sessions whose subject fits no line in the keys.
- **Search what was said.** It reads titles and folders only. For the content of sessions, use a transcript search, such as the search skill or the app's `mcp__ccd_session_mgmt__search_session_transcripts` tool.
- **Rename, move, archive or group sessions, or add emoji to their titles.**

If the script says "No session records found", the app has probably changed where it keeps them. Say that, and do not try to rebuild the list another way.
