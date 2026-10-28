# search

A Claude Code skill that finds past Claude conversations by what was said in them, and lists them by topic. Type `/search` and a few words, or ask Claude something like "find the session where we set up the backups", and it returns a numbered list of matching sessions and chats. Type `/search 🏥` and it lists your sessions on that topic, newest first. Claude can then read one of them for you, or open a Claude Code session in the desktop app.

## What it searches

- **Claude Code sessions run in the Claude desktop app.** Titles and folders come from the app's session records under `~/Library/Application Support/Claude*`, and the conversation text from the transcripts in `~/.claude/projects`. Every copy of the app, and every account in it, is read.
- **Claude Code sessions run in a terminal.** These are transcripts in `~/.claude/projects` that the app has no record of.
- **Cowork sessions** from the desktop app.
- **Claude Chat conversations** from claude.ai, through the data export, once it is unzipped into the folder layout described below. This part is optional.

Only what the user and Claude said is searched, plus titles. Tool output, system text, Claude's thinking and helper agents' transcripts are left out, so a word that appears in a CLAUDE.md file does not match every session that loaded it.

Matching is by word, with word endings ignored (SQLite FTS5 with Porter stemming). It does not match meaning. `SKILL.md` tells Claude how to make up for that: by trying related words with `--any`, and by reading the titles with `--titles` and picking out the likely ones.

The desktop app's session records and transcripts are its own files, and their layout is undocumented, so an app update can break this. The skill only reads them.

## Listing by topic

A topic is an emoji. Two keys say what each emoji stands for:

- **The folder key** pairs an emoji with a folder, such as 🏥 with `~/Documents/Health`. A session that ran in that folder, or in a folder inside it, is on that topic.
- **The topic key** pairs an emoji with a subject, such as 💻 with "Mac and tech support". It is for sessions that are not tied to a folder. A session is on that topic when its title starts with that emoji.

The skill does not add emoji to titles. You do that yourself, or you ask Claude to in your CLAUDE.md, for example: "Start every session title with the emoji from my topic key that fits the session."

A session's topic is the first of these that applies:

1. Its folder, or a folder above it, is in the folder key. The deepest keyed folder wins, so a subfolder can have its own emoji. If a keyed folder was renamed after a session ran in it, the session is still matched by the folder's name. A folder listed in `no_emoji_folders` gives no topic, and keeps a folder above it from giving one; rules 2 and 3 still apply to its sessions.
2. Its title starts with an emoji from either key. This applies to sessions you started yourself, not to runs of scheduled tasks, whose titles carry the task's own emoji.
3. The optional `fallback` rule in `config.json`, described below.

A session no rule places is "untagged".

`/search 🏥` lists the sessions on a topic, newest first, 30 of them unless `--limit` says otherwise. `/search 🏥 dentist` lists the sessions on the topic that mention the word, best match first, like any other search. `--topic` names a topic instead of the leading emoji: by its emoji, by a word from its folder's name or its key line, or as `untagged` for the sessions no rule places. Claude turns other words into the emoji using the keys, so "/search my medical sessions" works when the key says "Health". `--topics` prints how many sessions each topic has. Topics come from the desktop app's session records, so they cover Claude Code sessions run in the app; a search with a topic lists no Cowork sessions or chats.

## Requirements

- macOS.
- Python 3.9 or later. Its `sqlite3` module needs the FTS5 extension, which the usual builds include. This prints nothing if yours has it:
  `python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('create virtual table t using fts5(x)')"`
- The Claude desktop app's data folders under `~/Library/Application Support`, for desktop sessions, topics and opening a session, and Claude Code transcripts under `~/.claude/projects`. Sessions run with `claude` in a terminal have no record in the app, so they have no topic and cannot be opened.
- Claude Code, to use it as a skill. The script also runs on its own in a terminal: `python3 scripts/search.py --help`.

## Install

```
cp -R search ~/.claude/skills/search
```

The `allowed-tools` line in `SKILL.md` assumes that location. To change any settings, copy `config.example.json` to `config.json` in the same folder and edit it. Topics need keys: in `config.json`, or in a Markdown file it names, as described under "Topic keys". Without any, `--topics` and `--topic` say how to set them up, and a leading emoji is searched for as a word.

The first search builds the index, which takes from half a minute to a few minutes depending on how much history there is. After that, each search first reads only what is new or changed, and takes under a second.

## Settings: config.json

`config.json` sits next to `SKILL.md`. The file and every key in it are optional. `config.example.json` holds every key at its default, so copying it unchanged behaves the same as having no file.

Without settings, the skill reads every folder named `Claude*` under `~/Library/Application Support`, labels each account with the first 8 characters of its folder id, does not search Chat, has no scopes, and reads the topic keys from `~/.claude/CLAUDE.md` if that file has them.

| Key | What it sets | Default |
|---|---|---|
| `exports` | The folder holding Claude Chat exports. `~` is allowed; a relative path is taken from the skill folder. | Not set: Chat is not searched, and `--status` says so. |
| `export_accounts` | Map of account folder name under `exports` to the label for that account. When set, only the folders it names are read. | Every subfolder of `exports` is an account, labeled with its own name. |
| `accounts` | Map of the desktop app's account folder id to a label. | The first 8 characters of the id. |
| `apps` | Map of the app's data folder name under `~/Library/Application Support` to a label. Results from another copy of the app say "open it in the *label*". When set, only these folders are read. | Every folder named `Claude*`, labeled "*name* app". |
| `scopes` | A list of scopes, described below. | None. |
| `default_scope` | The scope for sessions and chats that match no scope. Ignored when `scopes` is empty. | None: they are in no scope, and only a search without a scope word finds them. |
| `index` | Where the index file goes. | `data/search-index.db` in the skill folder. |
| `keys_from` | A Markdown file to read the folder key and the topic key from, as described under "Keeping the keys in a Markdown file". `~` is allowed; a relative path is taken from the skill folder. `false` reads no file. | `~/.claude/CLAUDE.md`. It is skipped without a message when it has neither section. |
| `folders` | Folder key entries, as a list of `{"emoji": "...", "path": "..."}`. The path is a full path, starting with `/` or `~`. | None. |
| `topics` | Topic key entries, as a list of `{"emoji": "...", "label": "..."}`. The label is the topic's name. Text after its first colon or comma is not part of the name, but its words also call up the topic: `"Claude setup: skills, MCP"` is named "Claude setup", and `--topic mcp` finds it. | None. |
| `no_emoji_folders` | A list of folders whose sessions take no topic from their folder, even when a folder above them is in the key. | None. |
| `fallback` | A last rule for sessions that nothing above placed. See "The fallback rule". | None. |

An unknown key, or a value of the wrong kind, stops the script with a message and exit code 2, so that a typing mistake does not silently turn a setting off.

When any of the first six settings changes, the next search builds the index again, since the change can alter what it holds. The topic keys are not part of the index: a session's topic is worked out at search time from the app's session records, so changing them costs nothing.

### Scopes

A scope is a named part of your sessions, such as work and everything else. With scopes defined, a search whose first word is a scope name (in any case) searches only that scope, and `--status` counts each scope in its own column. Without them, every word is a search word.

Each scope has a `"name"`, one word not starting with `-`, and any of these rules:

- `"accounts"`: account labels, from `accounts` or `export_accounts`. Every session and chat on these accounts is in the scope.
- `"path_contains"`: pieces of a folder path, compared in lower case. A session is in the scope when one of them appears in its working folder, the folder it started in, the folders picked for a Cowork session, or, for a terminal session, the name of its transcript folder under `~/.claude/projects`.
- `"task_prefixes"`: the start of a scheduled task's id. Runs of those tasks are in the scope.
- `"chat_lists"`: glob patterns, relative to the `exports` folder, of text files. Every chat whose id appears in one of those files is in the scope. Use it for chats that belong to a scope their account does not, such as work chats held in a personal account. Any format works: the script picks out anything shaped like a chat id (a UUID), so a list of claude.ai chat links will do.

A session or chat belongs to the first scope with any rule that matches it. `path_contains` and `task_prefixes` apply to sessions only, `chat_lists` to chats only, and `accounts` to both.

### Example

Two copies of the desktop app, one per account, plus Chat exports from both accounts, split into work and home:

```json
{
  "exports": "~/Documents/Claude exports",
  "export_accounts": {
    "Me": "personal",
    "Acme": "work"
  },
  "accounts": {
    "11111111-2222-3333-4444-555555555555": "personal",
    "66666666-7777-8888-9999-000000000000": "work"
  },
  "apps": {
    "Claude": "personal app",
    "Claude-Work": "work app"
  },
  "scopes": [
    {
      "name": "work",
      "accounts": ["work"],
      "path_contains": ["acme"],
      "task_prefixes": ["acme-"],
      "chat_lists": ["Acme/work chats on the personal account/*.md"]
    }
  ],
  "default_scope": "home"
}
```

With this, `/search work roadmap` searches work only, `/search home dryer` searches everything else, and `/search dryer` searches both.

To find your account ids, run `python3 scripts/search.py --status` with no `accounts` set: the Account column shows the first 8 characters of each. The full ids are the folder names two levels under `~/Library/Application Support/Claude/claude-code-sessions/`.

### Topic keys

Entries in `config.json` are added after the ones read from `keys_from`, so the two can be combined. Several folders can share an emoji; the topic is named after the one nearest the top of the folder tree, unless a topic key entry for the same emoji gives it a label.

#### The fallback rule

Some sessions belong to a topic but carry no sign of it in their folder or title, such as runs of scheduled tasks, whose titles carry the task's own emoji. `fallback` catches those. It is an object with these keys:

- `"emoji"`: the topic to put them under. It has to be in one of the keys; if it is not, the rule places nothing, and the script says so.
- `"task_prefixes"`: the start of a scheduled task's id. Every run of a matching task goes under the emoji.
- `"path_contains"`: pieces of a folder path, compared in lower case. A session whose folder path contains one goes under the emoji.
- `"words"`: optional extra words that call up this topic, such as `"work"`.

At least one of `task_prefixes` and `path_contains` is needed. The rule is checked last, because if it came before the title rule it would take sessions whose title gives them a more specific topic.

#### Example

```json
{
  "folders": [
    {"emoji": "🏥", "path": "~/Documents/Health"},
    {"emoji": "🏦", "path": "~/Documents/Finances"},
    {"emoji": "💼", "path": "~/Work"}
  ],
  "topics": [
    {"emoji": "💻", "label": "Mac and tech support"},
    {"emoji": "🫟", "label": "Claude setup: Claude Code, skills, MCP"}
  ],
  "no_emoji_folders": ["~/Work/Timesheets"],
  "fallback": {
    "emoji": "💼",
    "task_prefixes": ["work-"],
    "path_contains": ["acme"],
    "words": ["job"]
  }
}
```

With this, `/search 🏥` lists the sessions that ran in `~/Documents/Health` and the ones whose title starts with 🏥. `--topic mcp` lists the 🫟 sessions. Sessions in `~/Work/Timesheets` are placed by their title, if at all, not by `~/Work`. Runs of any scheduled task whose id starts with `work-`, and sessions in any folder with "acme" in its path, are listed under 💼 when nothing earlier placed them, and `--topic job` finds them.

#### Keeping the keys in a Markdown file

The keys can live in a Markdown file instead of `config.json`, under two headings written exactly like this:

```markdown
### Folder emoji key

- 🏥 `~/Documents/Health`
- 🏦 `~/Documents/Finances` (words after the path also call up the topic)
- No emoji: `~/Work/Timesheets`

### Topic emoji key

- 💻 Mac and tech support
- 🫟 Claude setup: Claude Code, skills, MCP
```

- Each section runs from its heading to the next line that starts with `#`.
- Only lines starting with `- ` are read, so other text in a section, such as an explanation of the key, is left alone.
- A folder line is an emoji, a space and the folder in backticks, optionally followed by notes. A topic line is an emoji, a space and the label. A folder line starting `No emoji:` is the same as an entry in `no_emoji_folders`.
- A line that cannot be read is reported under "Problems:" at the end of the output, not skipped silently, because a dropped line would make a whole topic look empty.

The file is read on every run. Keeping the keys in your global `~/.claude/CLAUDE.md` puts them in front of Claude in every session, so the instruction that gives new sessions their emoji and the list this skill reads are the same list. That file is the default `keys_from`, so nothing needs to be configured for it.

## Laying out Chat exports

Request an export on claude.ai (Settings, then Privacy, then Export data), and unzip the archive it sends into a new folder named for the date:

```
<exports>/
  Me/                        one folder per account
    2026.06.13/              one folder per export, named YYYY.MM.DD
      conversations.json     anywhere inside the dated folder
    2026.09.26/
      conversations.json
  Acme/
    2026.08.31/
      conversations.json
```

- Folders whose names are not exactly `YYYY.MM.DD` are skipped, so notes and other files can sit alongside the exports.
- Each export folder is read once. Exports are read oldest first, and a later copy of a chat replaces the earlier one unless it holds less text, because a newer export sometimes arrives with a chat emptied.
- Chat is only as current as the newest export. Result lists name each account's export date, and say so when an export is more than 30 days old.

## Privacy

- The index holds a copy of the conversation text from every account the skill reads. It is created readable by its owner only (mode 600). Keep it on your own computer: if the skill folder is synced or backed up to the cloud, point `index` somewhere that is not.
- `.gitignore` leaves out `data/` and `config.json`, which holds account ids and folder paths.
- The scripts only read the app's files, the exports and the keys file. They send nothing anywhere and make no network requests.
- A search never lists the session it is run from.

## Opening a session (--open)

`--open SESSION_ID` shows a Claude Code session in the desktop app. `scripts/sessions.py` does it, the same file that works out topics.

- It works only from a session running inside the desktop app. It sends the app a `claude://` link addressed to the app process that session runs under.
- A session opens only in the copy of the app, and under the account, that holds it. The desktop app can be installed more than once, for example one copy per account. A result held by another copy says "open it in the *label*" and carries no `open=` mark; it can still be read.
- Titles in the list cannot be clicked. The app shows a Markdown link to a session as plain text, and macOS hands a `claude://` link to whichever copy of the app it picks. So the list is numbered, the ids are in a block under it, and Claude opens the one you name by number.
- Opening a session switches the app to it. The session you asked from keeps running, and you come back to it through the sidebar.

After a session opens, Claude also moves it to the sidebar group whose name contains "Active" (SKILL.md, step 5). The script doesn't do this: only Claude can move sessions between groups, through the app's sidebar tools. A pinned session stays where it is, because moving it into a group would remove its pin. So does any session on an account with no such group.

## Reflect and improve (suggest only)

The last step of every search writes a dated friction note of one to three lines to `improvement-log.md` in the skill folder: words that found nothing and what did, a topic word the script did not know, a "Problems:" line, a stale export, a slow search, an open that failed. "No notable friction" is a valid entry. When five notes have piled up since the last synthesis, or the last one is over 30 days old, the step also adds a `## Synthesis` entry proposing refinements, tagged `STATUS: AWAITING REVIEW`, and says so in one line under the result list. The skill never edits itself, its scripts, `config.json` or the keys; every proposal waits for a review ("review the search improvement log"). The log names sessions by title and holds none of their text. It is this installation's own; a fresh copy of the skill starts with the header alone. `SKILL.md`, step 6, has the full rule.

## Command reference

```
search.py [SCOPE] [TOPIC] [word ...] [--any WORD ...] [--source code|cowork|chat]
          [--since DATE] [--before DATE] [--limit N] [--recent] [--runs]
search.py [SCOPE] [TOPIC] --titles [--page N] [--source ...] [--since ...] [--before ...]
search.py --pick ID [ID ...] [--label TEXT] [--grep WORD ...]
search.py --show KEY [--grep WORD ...] [--max-chars N]
search.py --open SESSION_ID
search.py --topics
search.py --status
search.py --rebuild
```

TOPIC is an emoji from the keys. `--topic TOPIC`, anywhere on the line, also takes a word from the keys or `untagged`. `--limit` is 8 per source, or 30 for a topic given with no words.

Exit codes: 0 fine, 1 a key or id that matched no session, a session that could not be opened, or no topic keys to list by, 2 bad usage, a `config.json` that could not be used, or a topic that matched nothing or more than one thing.
