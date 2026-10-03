# sessions

A Claude Code skill that lists your past Claude Code sessions by topic and opens one in the desktop app. Type `/sessions health` and Claude replies with a numbered list of your sessions on that topic, most recent first. Say "open 3" and the app switches to that session. `/sessions` on its own gives a count of sessions per topic, and `/sessions untagged` lists the sessions that have no topic.

It is the nearest thing Claude Code has to opening a Project in Claude Chat and seeing its chats.

## How topics work

A topic is an emoji. Two keys say what each emoji stands for:

- **The folder key** pairs an emoji with a folder, such as 🏥 with `~/Documents/Health`. A session that ran in that folder, or in a folder inside it, is on that topic.
- **The topic key** pairs an emoji with a subject, such as 💻 with "Mac and tech support". It is for sessions that are not tied to a folder. A session is on that topic when its title starts with that emoji.

The skill does not add emoji to titles. You do that yourself, or you ask Claude to in your CLAUDE.md, for example: "Start every session title with the emoji from my topic key that fits the session."

A session's topic is the first of these that applies:

1. Its folder, or a folder above it, is in the folder key. The deepest keyed folder wins, so a subfolder can have its own emoji. If a keyed folder was renamed after a session ran in it, the session is still matched by the folder's name. A folder listed in `no_emoji_folders` gives no topic, and keeps a folder above it from giving one; rules 2 and 3 still apply to its sessions.
2. Its title starts with an emoji from either key. This applies to sessions you started yourself, not to runs of scheduled tasks, whose titles carry the task's own emoji.
3. The optional `fallback` rule in `config.json`, described below.

A session no rule places is "untagged".

A topic can be asked for by its emoji or by a word: the topic's name, a word from its folder's name, or a word from its topic key line. Claude turns other words into the emoji using the keys, so "/sessions medical" works when the key says "Health".

## Requirements

- macOS.
- The Claude desktop app. It keeps a record of each Claude Code session it runs under `~/Library/Application Support/Claude*/claude-code-sessions/`, and those records are what the skill lists. Sessions run with `claude` in a terminal have no record there and are not listed. The layout of these files is undocumented, so an app update can break the skill. The skill only reads them.
- Python 3.9 or later. Nothing beyond the standard library.
- Claude Code, to use it as a skill. The script also runs on its own in a terminal: `python3 scripts/sessions.py --help`.

## Install

```
cp -R sessions ~/.claude/skills/sessions
```

The `allowed-tools` line in `SKILL.md` assumes that location. Then set up your keys, either in `config.json` or in your CLAUDE.md, as described below. Until there is at least one key, the script prints how to set them up and exits with code 1.

## Settings: config.json

`config.json` sits next to `SKILL.md`. The file and every key in it are optional. `config.example.json` holds every key at its default, so copying it unchanged behaves the same as having no file.

Without settings, the skill reads both keys from `~/.claude/CLAUDE.md`, if that file has the sections described under "Keeping the keys in a Markdown file", and there is no fallback rule.

| Key | What it sets | Default |
|---|---|---|
| `keys_from` | A Markdown file to read the folder key and the topic key from. `~` is allowed; a relative path is taken from the skill folder. `false` reads no file. | `~/.claude/CLAUDE.md`. It is skipped without a message when it has neither section. |
| `folders` | Folder key entries, as a list of `{"emoji": "...", "path": "..."}`. The path is a full path, starting with `/` or `~`. | None. |
| `topics` | Topic key entries, as a list of `{"emoji": "...", "label": "..."}`. The label is the topic's name. Text after its first colon or comma is not part of the name, but its words also call up the topic: `"Claude setup: skills, MCP"` is named "Claude setup", and "mcp" finds it. | None. |
| `no_emoji_folders` | A list of folders whose sessions take no topic from their folder, even when a folder above them is in the key. | None. |
| `fallback` | A last rule for sessions that nothing above placed. See below. | None. |

Entries in `config.json` are added after the ones read from `keys_from`, so the two can be combined. Several folders can share an emoji; the topic is named after the one nearest the top of the folder tree, unless a topic key entry for the same emoji gives it a label.

An unknown key, or a value of the wrong kind, stops the script with a message and exit code 2, so that a typing mistake does not silently turn a setting off.

### The fallback rule

Some sessions belong to a topic but carry no sign of it in their folder or title, such as runs of scheduled tasks, whose titles carry the task's own emoji. `fallback` catches those. It is an object with these keys:

- `"emoji"`: the topic to put them under. It has to be in one of the keys; if it is not, the rule places nothing, and the script says so.
- `"task_prefixes"`: the start of a scheduled task's id. Every run of a matching task goes under the emoji.
- `"path_contains"`: pieces of a folder path, compared in lower case. A session whose folder path contains one goes under the emoji.
- `"words"`: optional extra words that call up this topic, such as `"work"`.

At least one of `task_prefixes` and `path_contains` is needed. The rule is checked last, because if it came before the title rule it would take sessions whose title gives them a more specific topic.

### Example

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

With this, `/sessions health` lists the sessions that ran in `~/Documents/Health` and the ones whose title starts with 🏥. `/sessions mcp` lists the 🫟 sessions. Sessions in `~/Work/Timesheets` are placed by their title, if at all, not by `~/Work`. Runs of any scheduled task whose id starts with `work-`, and sessions in any folder with "acme" in its path, are listed under 💼 when nothing earlier placed them, and `/sessions job` finds them.

### Keeping the keys in a Markdown file

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

## Opening a session (--open)

- It works only from a session running inside the desktop app. It sends the app a `claude://` link addressed to the app process that session runs under.
- A session opens only in the copy of the app, and under the account, that holds it. The desktop app can be installed more than once, for example one copy per account. The list covers the copy and account the current session runs in. `--everywhere` adds the rest, marked "cannot be opened from here".
- Titles in the list cannot be clicked. The app shows a Markdown link to a session as plain text, and macOS hands a `claude://` link to whichever copy of the app it picks. So the list is numbered, the ids are in a block under it, and Claude opens the one you name by number.
- Opening a session switches the app to it. The session you asked from keeps running, and you come back to it through the sidebar.

The search skill's own `--open` uses three functions from this script: `load(problems)`, `current(sessions)` and `open_session(session_id, sessions, current)`. Keep their names and arguments if you change it.

## Command reference

```
sessions.py [topic] [word ...] [--runs] [--all | --limit N] [--everywhere]
sessions.py --open SESSION_ID
```

| Option | What it does |
|---|---|
| `topic` | An emoji from the keys, a word that names a topic, or `untagged`. Left out: a count per topic. |
| `word ...` | Narrows the list. Every word has to be in the session's title or the name of its folder. |
| `--limit N` | Shows the N most recent sessions. The default is 30. |
| `--all` | Shows every session on the topic. |
| `--runs` | Lists each run of a scheduled task, not one line per task. |
| `--everywhere` | Adds sessions held by other copies of the app and other accounts. |
| `--open SESSION_ID` | Shows that session in the app. |

Exit codes: 0 fine, 1 nothing to read (no keys or no session records) or a session that could not be opened, 2 bad usage, a `config.json` that could not be used, or a topic that matched nothing or more than one thing.

## Privacy

- The script reads the app's session records and the file named by `keys_from`. It writes no file and makes no network requests.
- `.gitignore` leaves out `config.json`, which holds folder paths.
