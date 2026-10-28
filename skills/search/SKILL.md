---
name: search
description: >-
  Search the user's past Claude sessions by what was said in them, or list them by topic:
  Claude Code and Cowork sessions from the desktop app, and exported Claude Chat conversations.
  Trigger on /search followed by keywords or a plain description, optionally led by a scope name
  from config.json or by a topic emoji ("/search 🏥", "/search 🏥 dentist"); afterwards "open 2"
  opens a result and "what did we decide in 3" reads one. Also when the user asks "find the
  session where...", "which chat was about...", "did I ever ask Claude about...", "show me my
  health sessions", "which sessions were about X", or to search or list their past sessions or
  chats. Not for searching files, email or the web, or for renaming, archiving or grouping
  sessions, or adding emoji to their titles.
allowed-tools: Bash(python3 ~/.claude/skills/search/scripts/search.py:*)
---

# search

Finds past sessions by what the user and Claude said in them, across Claude Code, Cowork and Claude Chat, and lists Claude Code sessions by topic.

The work is done by `scripts/search.py`. It keeps an index of the conversation text, brings that index up to date at the start of every search, and then searches it. How it works and why is written at the top of the script. `scripts/sessions.py`, next to it, reads the desktop app's own record of each session: it says which session is on which topic, and opens a session in the app. The settings for both are in `config.json` in this folder, and `README.md` describes them. `improvement-log.md`, also in this folder, is the skill's friction log; step 6 writes to it, and its synthesis reads the recent entries.

The script matches words. You supply the understanding: it is your job to turn what the user means into words the session is likely to contain, and, when no words work, to read the titles and recognize the session by what it is about.

## 1. Turn what the user typed into a search

- **Scope.** `config.json` can define scopes, such as work and everything else. If the first word the user typed is a scope name from `config.json`, pass it first, as typed. Otherwise pass no scope, and everything is searched. The scope names are the column headings of `--status`; when there are none, no scopes are defined and every word is a search word.
- **Topic.** A topic is an emoji from the user's keys: the folder key pairs emoji with folders, and the topic key pairs emoji with subjects. A session is on a topic when it ran in a keyed folder, or when its title starts with the emoji. The keys are read from `config.json`, or from the Markdown file it names with `keys_from`, by default the "### Folder emoji key" and "### Topic emoji key" sections of `~/.claude/CLAUDE.md`, so they may already be in your context. When the user names a topic ("my health sessions", "/search 🏥"), pass its emoji after the scope and before the words. Turn a word into the emoji yourself: the script knows only the words in the keys ("health" when the key says "Health", not "medical"), and a word that fits no topic is searched for as a plain word. If you cannot tell which topic the user means, say so in one sentence and list the topics; do not pick the nearest one. A topic alone lists its sessions, newest first; with words, it lists the sessions on the topic that mention them. `--topic untagged` lists the sessions no key places. Topics are known for Claude Code sessions run in the desktop app, so a search with a topic lists no Cowork sessions or chats.
- **Words.** Every word has to be in the session, so fewer words find more. From what the user typed, keep the two or three most distinctive words: names, products, unusual terms. Drop filler such as "the session where I asked about". A phrase that has to appear exactly goes in one quoted argument. Sessions that have the words close together are listed first.
- **Endings.** Word endings do not matter. "quote" also finds "quotes" and "quoted".
- **Time.** "in July", "last week" or "before September" become `--since` and `--before`, with the date written as 2026-07-01.
- **Source.** "in Chat" or "a Cowork session" becomes `--source chat`, `--source cowork` or `--source code`.

## 2. Run it

```
python3 ~/.claude/skills/search/scripts/search.py invoice template
python3 ~/.claude/skills/search/scripts/search.py "standing desk" warranty
python3 ~/.claude/skills/search/scripts/search.py dryer --since 2026-09-01
python3 ~/.claude/skills/search/scripts/search.py SCOPE invoice template
python3 ~/.claude/skills/search/scripts/search.py '🏥'
python3 ~/.claude/skills/search/scripts/search.py '🏥' dentist
python3 ~/.claude/skills/search/scripts/search.py SCOPE '🦉' demo
```

In the SCOPE lines, SCOPE stands for a scope name from `config.json`, if any are defined.

Put each argument in its own quotes when it has a space, an apostrophe or an emoji in it.

| The user asks for | Add |
|---|---|
| more than 8 results per source, or more than the 30 a topic alone shows | `--limit N` |
| newest first, not best match first | `--recent` |
| runs of scheduled tasks too | `--runs` |
| one source only | `--source code`, `--source cowork` or `--source chat` |
| the sessions with no topic | `--topic untagged` |
| how many sessions each topic has | `--topics` |

The first search after the skill is installed builds the index, which takes from half a minute to a few minutes, depending on how much history there is. Later searches take under a second.

## 3. When that does not find it

Before replying to any search, read the titles and the matching text and ask whether any result is about what the user described. A long session holds most common words somewhere, so a search can return sessions that contain every word and have nothing to do with the subject.

Go down these steps when a search finds nothing, when none of its results fits what the user described, and when the user says that none of them is the one. Stop at the first step that finds it. When the user gave a scope or a topic, put it first in every command here too.

**A. Other words.** Search again with fewer words, or with another word for the same thing. Two tries at most.

**B. Related words.** Think of six to ten words a session on this subject would be likely to contain: other names for the thing, its brand or product name, the people involved, the parts of it, what it is a kind of. Pass them after `--any`. One of them is enough for a session to match, and the sessions holding more of them, or rarer ones, come first. A word that has to be there goes before `--any`, as a plain word.

```
python3 ~/.claude/skills/search/scripts/search.py --any laundry washer dryer squeak rattle noise appliance
python3 ~/.claude/skills/search/scripts/search.py website --any redesign theme layout homepage
```

**C. Titles, read for meaning.** Print the titles alone and read them. A title says what a session was about, so this finds a session that shares no word with the user's description. A topic narrows this list too.

```
python3 ~/.claude/skills/search/scripts/search.py --titles --source code
python3 ~/.claude/skills/search/scripts/search.py --titles --source chat --since 2026-06-01 --page 2
python3 ~/.claude/skills/search/scripts/search.py '🏥' --titles
```

- Read Claude Code and Cowork titles first. They are the shortest lists. Read Chat titles after that.
- Use every hint of time, source or topic the user gave, to shorten the list.
- A page is 350 titles. If a list runs to more than four pages, stop and ask the user one question that narrows it, such as roughly when it was. Reading every page of a long list costs tens of thousands of tokens.
- Each line starts with an id. For a title that looks likely, check what was said: `--show ID --grep WORD` prints the turns that hold a word, and `--show ID --max-chars 1500` prints how the session opened.
- Print the ones that fit as a result list, and reply with that list: `--pick ID ID --label "what the user was looking for" --grep WORD`. `--grep` makes each result show the text near that word.

If all three steps fail, say so, name the words tried and the lists read, and ask the user for one more detail: a name, a date, or a word they remember using.

## 4. Reply

Reply with what the script printed, from its first line to the last numbered result, and nothing else.

- Copy each line as it is, with its number and its link. The user goes by the numbers to say which one to open or read.
- Leave out the block that starts "IDS for --show and --open". It is there for step 5.
- No summary above the list, no remarks about what is in it, no offer after it. The one exception is the one-line heads-up of step 6, when a synthesis was just written.
- When step 3 found it, add one sentence under the list saying how: by which other words, by related words, or by title. It tells the user how much to trust the match.
- If the output ends with a "Problems:" section, pass each problem on in a sentence. A problem can mean the list is incomplete, so it must not be dropped.
- If the script says no topics are set up, tell the user in a sentence or two that no topics are set up yet and where they go, as the script's message says. Do not write `config.json` or change their CLAUDE.md unless they ask.

## 5. Open or read a result

Only when the user asks. Take the key or id from the IDS block of the list you last printed, never from memory.

- **"open 2", for a Claude Code result with `open=` in the IDS block.** Run `python3 ~/.claude/skills/search/scripts/search.py --open 'local_…'`. The app switches to that session, and this session keeps running. Then move the session to the user's Active group in the sidebar, unless it is pinned:
  1. Load `mcp__ccd_session_mgmt__get_session`, `mcp__ccd_sidebar__list_groups` and `mcp__ccd_sidebar__move_sessions` in one ToolSearch call.
  2. Call `get_session` with the `local_…` id. If `pinned` is true, leave the session where it is: moving a pinned session into a group removes its pin. A missing `pinned` means not pinned. If its group's name already contains "Active", leave it too.
  3. Call `list_groups` and find the group whose name contains "Active". Both accounts have one named "🟢 Active"; match by name, since group ids differ between accounts. Call `move_sessions` with that group's id and the `local_…` id. Move it from Ungrouped or from any other group, such as Paused or Waiting.
  4. Call `get_session` again and check that its group is now Active.

  Reply with one sentence naming the session that was opened and saying it is now in Active, or that it stayed where it was because it is pinned. If no group's name contains "Active", a call fails, or step 4 shows the session didn't move, leave it and say so in a second sentence. Don't create the group.
- **A Claude Code result with no `open=`.** If its line says "open it in the ...", it is held by another copy of the app or another account, and opens only from there: say which. If no result in the list has `open=`, this session is not running in the desktop app, or `scripts/sessions.py` is missing (README.md says what opening needs). Say so; the result can still be read.
- **A Chat result.** Its title is a link to the chat on claude.ai. It opens only in a browser signed in to the account that holds the chat.
- **A Cowork result.** It cannot be opened from here. It can be read.
- **"what did we decide in 3", or any question about what a result says.** Run `python3 ~/.claude/skills/search/scripts/search.py --show 'KEY' --grep WORD`, with a word or two from the question. Answer from that text. Without `--grep` it prints the session from the start. If the output says it was cut short, say so, or run it again with a larger `--max-chars`.

Never open a session the user did not ask for. It changes what is on their screen. One session per request: if the user names two, open the first and say the second is next.

## 6. Reflect and improve (SUGGEST ONLY)

Last step of every run. A run is one search request and its follow-ups (open, read). Do this step right before the reply to the search goes out, and add to the same entry if a follow-up hits friction. It runs when the script errored or the user stopped the search too; those are the runs whose friction matters most.

**This skill never edits itself.** It does not change its own `SKILL.md`, `README.md`, the scripts, `config.json`, the topic keys, or what it searches and how it ranks. It writes suggestions to a log that the user reviews. They act on them by saying "review the search improvement log".

**Log:** `~/.claude/skills/search/improvement-log.md`. Newest entries on top. It sits in the skill's own folder because `data/` holds only the index and is not committed.

### Every run: friction note

Add a dated entry of one to three lines, under a heading that says what was searched for, covering what went wrong or felt wasteful. Never copy the session text it found into the log; name the session by its title. Things worth catching in this skill specifically:

- Words that found nothing, and which of steps A to C found the session, or that none did and what the user then remembered.
- A list where every result held the words and none was about the subject.
- A topic word the script did not know and the emoji it had to be turned into, a topic the user asked for that fits no key line, or a session placed on a surprising topic by its folder or its title's emoji.
- A "Problems:" line: session records that could not be read, a key line not understood, an exports folder missing.
- A recent chat not found because the export is old; note the export's age.
- A search that took more than a few seconds, or the index built again when nothing in `config.json` had changed.
- An open that failed or was refused: the session held by the other copy of the app, this session not running in the app, the Active move failing or skipped for a pin.
- The wanted session having only a title in the index, being a Cowork or terminal session, or being a scheduled-task run that needed `--runs`.
- A `--show` that was cut short, or whose `--grep` missed the turn because of the word's form.

"No notable friction" is a valid entry.

### Synthesis

This skill is invoked by hand and runs irregularly, so a fixed weekly Sunday synthesis does not fit. Instead, at the start of this step, check the log and synthesize when **either**: there are 5 or more friction notes since the last synthesis, **or** the last synthesis is more than 30 days old and at least one new note exists.

When it triggers, read the notes since the last synthesis, look for recurring patterns, and add a dated `## Synthesis` entry at the top with a short prioritized list of concrete proposed refinements. Tag each `STATUS: AWAITING REVIEW`. Do not apply any of them.

### Heads-up

When a synthesis produced notable proposals, add **one line** under the result list pointing at the log. Do not send a separate message. At most one heads-up per synthesis.

## What it cannot do

- **Read every conversation for meaning.** Meaning is matched on titles, and on the words you think of. A session is still missed when its title says nothing about the subject and it holds none of the words tried.
- **Find a chat newer than the last export.** The second line of every result list names the export dates. When the user is looking for a recent chat and it is not found, tell them the export date for that account, and that a new export brings the missing chats in. Chat is searched only when `config.json` names an exports folder.
- **Search the text of a Claude Code session whose transcript is gone.** The app keeps a session's record, with its title, after its transcript has left `~/.claude/projects`, so only the title can match. `--status` counts these.
- **Find a word that appeared only in tool output or in a file.** It searches what was said. The desktop app's `search_session_transcripts` tool, where it is available, searches raw transcripts for the copy of the app it runs in.
- **Search runs of cloud routines.** Those are stored on Anthropic's servers.
- **Place a session with no keyed folder and no key emoji at the start of its title.** Those are untagged: mostly sessions from before the user started giving titles an emoji, and sessions whose subject fits no line in the keys. It does not add emoji to titles; the user does, or asks for it in their CLAUDE.md.
- **Rename, archive or group sessions**, beyond moving the one it opened into Active.

## The index

`data/search-index.db` inside this skill's folder, or the path set by `"index"` in `config.json`. It is a copy of conversation text from every account the skill reads, so it is created readable by its owner only, and it should stay on this computer: do not sync it or commit it.

Nothing is lost if it is deleted. `python3 ~/.claude/skills/search/scripts/search.py --rebuild` builds it again from the originals, and `--status` shows what it holds. It is also built again on its own when `config.json` changes in a way that changes what it holds. The topic keys are not part of it: a session's topic is worked out at search time from the app's session records.
