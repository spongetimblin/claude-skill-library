---
name: search
description: >-
  Search the user's past Claude sessions by what was said in them: Claude Code and Cowork
  sessions from the desktop app, and exported Claude Chat conversations. Trigger on /search
  followed by keywords or a plain description, optionally led by a scope name from
  config.json; afterwards "open 2" opens a result and "what did we decide in 3" reads one.
  Also when the user asks "find the session where...", "which chat was about...", "did I ever
  ask Claude about..." or to search their past sessions or chats. Not for searching files,
  email or the web, or for renaming or organizing sessions.
allowed-tools: Bash(python3 ~/.claude/skills/search/scripts/search.py:*)
---

# search

Finds past sessions by what the user and Claude said in them, across Claude Code, Cowork and Claude Chat.

The work is done by `scripts/search.py`. It keeps an index of the conversation text, brings that index up to date at the start of every search, and then searches it. How it works and why is written at the top of the script. Its settings are in `config.json` in this folder, and `README.md` describes them.

The script matches words. You supply the understanding: it is your job to turn what the user means into words the session is likely to contain, and, when no words work, to read the titles and recognize the session by what it is about.

## 1. Turn what the user typed into a search

- **Scope.** `config.json` can define scopes, such as work and everything else. If the first word the user typed is a scope name from `config.json`, pass it first, as typed. Otherwise pass no scope, and everything is searched. The scope names are the column headings of `--status`; when there are none, no scopes are defined and every word is a search word.
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
```

In the last line, SCOPE stands for a scope name from `config.json`, if any are defined.

Put each argument in its own quotes when it has a space, an apostrophe or an emoji in it.

| The user asks for | Add |
|---|---|
| more than 8 results per source | `--limit N` |
| newest first, not best match first | `--recent` |
| runs of scheduled tasks too | `--runs` |
| one source only | `--source code`, `--source cowork` or `--source chat` |

The first search after the skill is installed builds the index, which takes from half a minute to a few minutes, depending on how much history there is. Later searches take under a second.

## 3. When that does not find it

Before replying to any search, read the titles and the matching text and ask whether any result is about what the user described. A long session holds most common words somewhere, so a search can return sessions that contain every word and have nothing to do with the subject.

Go down these steps when a search finds nothing, when none of its results fits what the user described, and when the user says that none of them is the one. Stop at the first step that finds it. When the user gave a scope, put it first in every command here too.

**A. Other words.** Search again with fewer words, or with another word for the same thing. Two tries at most.

**B. Related words.** Think of six to ten words a session on this subject would be likely to contain: other names for the thing, its brand or product name, the people involved, the parts of it, what it is a kind of. Pass them after `--any`. One of them is enough for a session to match, and the sessions holding more of them, or rarer ones, come first. A word that has to be there goes before `--any`, as a plain word.

```
python3 ~/.claude/skills/search/scripts/search.py --any laundry washer dryer squeak rattle noise appliance
python3 ~/.claude/skills/search/scripts/search.py website --any redesign theme layout homepage
```

**C. Titles, read for meaning.** Print the titles alone and read them. A title says what a session was about, so this finds a session that shares no word with the user's description.

```
python3 ~/.claude/skills/search/scripts/search.py --titles --source code
python3 ~/.claude/skills/search/scripts/search.py --titles --source chat --since 2026-06-01 --page 2
```

- Read Claude Code and Cowork titles first. They are the shortest lists. Read Chat titles after that.
- Use every hint of time or source the user gave, to shorten the list.
- A page is 350 titles. If a list runs to more than four pages, stop and ask the user one question that narrows it, such as roughly when it was. Reading every page of a long list costs tens of thousands of tokens.
- Each line starts with an id. For a title that looks likely, check what was said: `--show ID --grep WORD` prints the turns that hold a word, and `--show ID --max-chars 1500` prints how the session opened.
- Print the ones that fit as a result list, and reply with that list: `--pick ID ID --label "what the user was looking for" --grep WORD`. `--grep` makes each result show the text near that word.

If all three steps fail, say so, name the words tried and the lists read, and ask the user for one more detail: a name, a date, or a word they remember using.

## 4. Reply

Reply with what the script printed, from its first line to the last numbered result, and nothing else.

- Copy each line as it is, with its number and its link. The user goes by the numbers to say which one to open or read.
- Leave out the block that starts "IDS for --show and --open". It is there for step 5.
- No summary above the list, no remarks about what is in it, no offer after it.
- When step 3 found it, add one sentence under the list saying how: by which other words, by related words, or by title. It tells the user how much to trust the match.
- If the output ends with a "Problems:" section, pass each problem on in a sentence.

## 5. Open or read a result

Only when the user asks. Take the key or id from the IDS block of the list you last printed, never from memory.

- **"open 2", for a Claude Code result with `open=` in the IDS block.** Run `python3 ~/.claude/skills/search/scripts/search.py --open 'local_…'`. The app switches to that session, and this session keeps running. Reply with one sentence naming the session that was opened.
- **A Claude Code result with no `open=`.** If its line says "open it in the ...", it is held by another copy of the app or another account, and opens only from there: say which. If no result in the list has `open=`, opening is not set up on this computer (README.md says what it needs), or this session is not running in the desktop app. Say so; the result can still be read.
- **A Chat result.** Its title is a link to the chat on claude.ai. It opens only in a browser signed in to the account that holds the chat.
- **A Cowork result.** It cannot be opened from here. It can be read.
- **"what did we decide in 3", or any question about what a result says.** Run `python3 ~/.claude/skills/search/scripts/search.py --show 'KEY' --grep WORD`, with a word or two from the question. Answer from that text. Without `--grep` it prints the session from the start. If the output says it was cut short, say so, or run it again with a larger `--max-chars`.

Never open a session the user did not ask for. It changes what is on their screen.

## What it cannot do

- **Read every conversation for meaning.** Meaning is matched on titles, and on the words you think of. A session is still missed when its title says nothing about the subject and it holds none of the words tried.
- **Find a chat newer than the last export.** The second line of every result list names the export dates. When the user is looking for a recent chat and it is not found, tell them the export date for that account, and that a new export brings the missing chats in. Chat is searched only when `config.json` names an exports folder.
- **Search the text of a Claude Code session whose transcript is gone.** The app keeps a session's record, with its title, after its transcript has left `~/.claude/projects`, so only the title can match. `--status` counts these.
- **Find a word that appeared only in tool output or in a file.** It searches what was said. The desktop app's `search_session_transcripts` tool, where it is available, searches raw transcripts for the copy of the app it runs in.
- **Search runs of cloud routines.** Those are stored on Anthropic's servers.

## The index

`data/search-index.db` inside this skill's folder, or the path set by `"index"` in `config.json`. It is a copy of conversation text from every account the skill reads, so it is created readable by its owner only, and it should stay on this computer: do not sync it or commit it.

Nothing is lost if it is deleted. `python3 ~/.claude/skills/search/scripts/search.py --rebuild` builds it again from the originals, and `--status` shows what it holds. It is also built again on its own when `config.json` changes in a way that changes what it holds.
