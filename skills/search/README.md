# search

A Claude Code skill that finds past Claude conversations by what was said in them. Type `/search` and a few words, or ask Claude something like "find the session where we set up the backups", and it returns a numbered list of matching sessions and chats. Claude can then read one of them for you, or open a Claude Code session in the desktop app.

## What it searches

- **Claude Code sessions run in the Claude desktop app.** Titles and folders come from the app's session records under `~/Library/Application Support/Claude*`, and the conversation text from the transcripts in `~/.claude/projects`. Every copy of the app, and every account in it, is read.
- **Claude Code sessions run in a terminal.** These are transcripts in `~/.claude/projects` that the app has no record of.
- **Cowork sessions** from the desktop app.
- **Claude Chat conversations** from claude.ai, through the data export, once it is unzipped into the folder layout described below. This part is optional.

Only what the user and Claude said is searched, plus titles. Tool output, system text, Claude's thinking and helper agents' transcripts are left out, so a word that appears in a CLAUDE.md file does not match every session that loaded it.

Matching is by word, with word endings ignored (SQLite FTS5 with Porter stemming). It does not match meaning. `SKILL.md` tells Claude how to make up for that: by trying related words with `--any`, and by reading the titles with `--titles` and picking out the likely ones.

The desktop app's session records and transcripts are its own files, and their layout is undocumented, so an app update can break this. The skill only reads them.

## Requirements

- macOS.
- Python 3.9 or later. Its `sqlite3` module needs the FTS5 extension, which the usual builds include. This prints nothing if yours has it:
  `python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('create virtual table t using fts5(x)')"`
- The Claude desktop app's data folders under `~/Library/Application Support`, for desktop sessions, and Claude Code transcripts under `~/.claude/projects`.
- Claude Code, to use it as a skill. The script also runs on its own in a terminal: `python3 scripts/search.py --help`.

## Install

```
cp -R search ~/.claude/skills/search
```

The `allowed-tools` line in `SKILL.md` assumes that location. To change any settings, copy `config.example.json` to `config.json` in the same folder and edit it.

The first search builds the index, which takes from half a minute to a few minutes depending on how much history there is. After that, each search first reads only what is new or changed, and takes under a second.

## Settings: config.json

`config.json` sits next to `SKILL.md`. The file and every key in it are optional. `config.example.json` holds every key at its default, so copying it unchanged behaves the same as having no file.

Without settings, the skill reads every folder named `Claude*` under `~/Library/Application Support`, labels each account with the first 8 characters of its folder id, does not search Chat, and has no scopes.

| Key | What it sets | Default |
|---|---|---|
| `exports` | The folder holding Claude Chat exports. `~` is allowed; a relative path is taken from the skill folder. | Not set: Chat is not searched, and `--status` says so. |
| `export_accounts` | Map of account folder name under `exports` to the label for that account. When set, only the folders it names are read. | Every subfolder of `exports` is an account, labeled with its own name. |
| `accounts` | Map of the desktop app's account folder id to a label. | The first 8 characters of the id. |
| `apps` | Map of the app's data folder name under `~/Library/Application Support` to a label. Results from another copy of the app say "open it in the *label*". When set, only these folders are read. | Every folder named `Claude*`, labeled "*name* app". |
| `scopes` | A list of scopes, described below. | None. |
| `default_scope` | The scope for sessions and chats that match no scope. Ignored when `scopes` is empty. | None: they are in no scope, and only a search without a scope word finds them. |
| `index` | Where the index file goes. | `data/search-index.db` in the skill folder. |

An unknown key, or a value of the wrong kind, stops the script with a message and exit code 2, so that a typing mistake does not silently turn a setting off.

When any setting except `index` changes, the next search builds the index again, since the change can alter what it holds.

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
- The script only reads the app's files and the exports. It sends nothing anywhere and makes no network requests.
- A search never lists the session it is run from.

## Opening a session (--open)

`--open SESSION_ID` shows a Claude Code session in the desktop app. That part is not built in. It borrows a separate script at `~/.claude/skills/sessions/scripts/sessions.py`, which has to provide:

- `load(problems)`: the sessions read from the app's records, as a list. `problems` is a list it can add messages to.
- `current(sessions)`: the session this is running in, or `None`.
- `open_session(session_id, sessions, current)`: shows that session in the app, prints one line, and returns an exit code.

Without that script, `--open` says so and exits with code 1, result lists carry no `open=` marks, and results can still be read with `--show`. Even with it, a session opens only from inside the desktop app, and only in the copy of the app and the account that holds it.

## Command reference

```
search.py [SCOPE] [word ...] [--any WORD ...] [--source code|cowork|chat]
          [--since DATE] [--before DATE] [--limit N] [--recent] [--runs]
search.py [SCOPE] --titles [--page N] [--source ...] [--since ...] [--before ...]
search.py --pick ID [ID ...] [--label TEXT] [--grep WORD ...]
search.py --show KEY [--grep WORD ...] [--max-chars N]
search.py --open SESSION_ID
search.py --status
search.py --rebuild
```

Exit codes: 0 fine, 1 a key or id that matched no session or a session that could not be opened, 2 bad usage or a `config.json` that could not be used.
