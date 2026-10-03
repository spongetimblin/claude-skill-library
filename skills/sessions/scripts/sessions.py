#!/usr/bin/env python3
"""List Claude Code desktop sessions by topic, and open one. Never writes a file.

Usage:  sessions.py [topic] [word ...] [--runs] [--all | --limit N] [--everywhere]
        sessions.py --open SESSION_ID

  sessions.py                 counts per topic
  sessions.py 🏥              sessions on that topic, most recent first
  sessions.py health          the same, by a word from the key
  sessions.py 🏥 dentist      narrowed to sessions with "dentist" in the title or folder
  sessions.py untagged        sessions no rule could place
  sessions.py --open local_…  show that session in the app

A topic is an emoji. Two keys say what each emoji stands for: the folder key
pairs emoji with folders, and the topic key pairs emoji with subjects. A
session's topic is the first of these that applies:
  1. Its folder, or a folder above it, is in the folder key. A folder renamed
     since the session ran is matched by the keyed folder's own name. A folder
     with no emoji ("no_emoji_folders", or a "No emoji" line in a Markdown
     key) gives no topic and keeps a folder above it from giving one; rules 2
     and 3 still apply.
  2. Its title starts with an emoji from either key. Hand-started sessions only:
     a scheduled task's title carries the task's own emoji, which is not a topic.
  3. The "fallback" rule in config.json, when there is one: a scheduled task
     whose id starts with one of its "task_prefixes", or a folder whose path
     contains one of its "path_contains", puts the session under its emoji.
     This is for the list only. It is not how a session's title gets its emoji.

Settings come from config.json in the skill folder, the folder above this
script's. Every key in it is optional, and README.md describes each one. The
keys can be written into config.json ("folders" and "topics"), read from the
"### Folder emoji key" and "### Topic emoji key" sections of a Markdown file
("keys_from", by default ~/.claude/CLAUDE.md), or both. The Markdown file is
read on every run, so there is no second list to keep in step. A key line this
cannot parse is reported, not skipped silently, because a dropped line would
make a whole topic look empty. With no keys anywhere, this says how to set
them up and exits 1.

The functions load, current and open_session are also used by the search
skill's --open, so their names and arguments should stay as they are.

Session records are the desktop app's own files, one JSON per session, at
~/Library/Application Support/Claude*/claude-code-sessions/<account>/<org>/.
That layout is undocumented and can change with an app update. This only ever
reads those files.

A session opens only in the copy of the app, and the account, that holds it.
So the list covers the folder holding the current session, found through
CLAUDE_CODE_HOST_SESSION_ID. --everywhere adds the rest, which cannot be opened
from here.

The list is numbered, with the ids in a block underneath, because nothing in a
reply can be clicked to open a session. Both kinds of link were tried on
2026-09-29 with app 2.9939.4. The app showed [title](#local_…) as plain text.
And macOS hands a claude:// link to one running copy of the app, which with two
copies running was the wrong one. --open sends that same link to the one copy
this session runs under.

Exit codes: 0 fine, 1 nothing to read (no keys or no session records) or a
session that could not be opened, 2 bad usage, a config.json that could not be
used, or a topic that matched nothing or more than one thing.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HOME = Path.home()
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = SKILL_DIR / "config.json"
DEFAULT_KEYS_FROM = HOME / ".claude" / "CLAUDE.md"
APP_SUPPORT = HOME / "Library" / "Application Support"
FOLDER_HEADING = "### Folder emoji key"
TOPIC_HEADING = "### Topic emoji key"

UNTAGGED = "untagged"
DEFAULT_LIMIT = 30

FOLDER_LINE = re.compile(r"^- (.+?) `([^`]+)`\s*(.*)$")
TOPIC_LINE = re.compile(r"^- (\S+) (.+)$")
NO_EMOJI = re.compile(r"^no emoji:?$", re.IGNORECASE)
NUMBERING = re.compile(r"^\d+\.\s*")
WORD = re.compile(r"[a-z0-9][a-z0-9._-]*")
SESSION_ID = re.compile(r"local_[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")

# The app itself, not the claude binary it runs for each session, which sits at
# a path ending claude.app/Contents/MacOS/claude in lower case.
APP_PROCESS = re.compile(r"/Claude\.app/Contents/MacOS/Claude( |$)")

# The "open this link" event macOS sends an app, addressed to one process.
SEND_LINK = """
ObjC.import('Foundation');
function run(argv) {
  var GURL = 0x4755524c, DIRECT = 0x2d2d2d2d;
  var target = $.NSAppleEventDescriptor.descriptorWithProcessIdentifier(parseInt(argv[0], 10));
  var ev = $.NSAppleEventDescriptor.appleEventWithEventClassEventIDTargetDescriptorReturnIDTransactionID(GURL, GURL, target, -1, 0);
  ev.setParamDescriptorForKeyword($.NSAppleEventDescriptor.descriptorWithString(argv[1]), DIRECT);
  ev.sendEventWithOptionsTimeoutError(1, 5, null);
  return 'sent';
}
"""


def norm(s):
    """Drop variation selectors, so an emoji typed with and without one compares equal."""
    return s.replace("\ufe0f", "").replace("\ufe0e", "")


def words_in(text):
    return {w.strip("._-") for w in WORD.findall(text.lower())}


def section(lines, heading):
    """Lines under a heading, up to the next heading. None when the heading is absent."""
    found, out = False, []
    for line in lines:
        if line.strip() == heading:
            found = True
        elif found and line.startswith("#"):
            break
        elif found:
            out.append(line.rstrip())
    return out if found else None


# ---------------------------------------------------------------- settings

KEYS = ("keys_from", "folders", "topics", "fallback", "no_emoji_folders")
FALLBACK_KEYS = ("emoji", "task_prefixes", "path_contains", "words")

SETUP = (
    "No topics are set up, so there is nothing to sort sessions by. A topic is an emoji that "
    "stands for a folder or a subject: a session is on that topic when it ran in that folder, "
    "or when its title starts with that emoji. To set topics up, create {config} with a "
    '"folders" list, such as [{{"emoji": "🏥", "path": "~/Documents/Health"}}], and a "topics" '
    'list, such as [{{"emoji": "💻", "label": "Mac and tech support"}}], or with "keys_from" '
    'naming a Markdown file that has "{folder}" and "{topic}" sections. README.md in {skill} '
    "describes every key."
)


def text_of(value, what):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} has to be text")
    return value.strip()


def emoji_of(value, what):
    emoji = text_of(value, what)
    if re.search(r"[A-Za-z0-9\s]", emoji):
        raise ValueError(f'{what} has to be one emoji, and "{emoji}" is not')
    return emoji


def folder_of(value, what):
    """A folder as a session record writes it: full, with ~ expanded."""
    folder = os.path.normpath(os.path.expanduser(text_of(value, what)))
    if not os.path.isabs(folder):
        raise ValueError(f'{what} has to be a full path, starting with / or ~, and "{value}" is not')
    return folder


def texts_of(raw, key, where):
    value = raw.get(key)
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f'"{key}" in {where} has to be a list of text')
    return [v for v in value if v]


def entries_of(raw, key, fields, example):
    value = raw.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f'"{key}" has to be a list of objects, like [{example}]')
    for n, item in enumerate(value, 1):
        if not isinstance(item, dict) or set(item) != set(fields):
            raise ValueError(f'entry {n} in "{key}" has to be an object with exactly '
                             f'{" and ".join(repr(f) for f in fields)}, like {example}')
    return value


def fallback_of(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError('"fallback" has to be an object, like {"emoji": "💼", "task_prefixes": ["work-"]}')
    unknown = sorted(set(value) - set(FALLBACK_KEYS))
    if unknown:
        raise ValueError(f'"fallback" has an unknown key {", ".join(unknown)}; '
                         f'it takes {", ".join(FALLBACK_KEYS)}')
    fallback = {
        "emoji": emoji_of(value.get("emoji"), '"emoji" in "fallback"'),
        "task_prefixes": texts_of(value, "task_prefixes", '"fallback"'),
        "path_contains": [p.lower() for p in texts_of(value, "path_contains", '"fallback"')],
        "words": {w.lower() for w in texts_of(value, "words", '"fallback"')},
    }
    if not fallback["task_prefixes"] and not fallback["path_contains"]:
        raise ValueError('"fallback" needs "task_prefixes", "path_contains" or both')
    return fallback


class Config:
    """config.json, checked, with every key it leaves out at its default."""

    def __init__(self, raw):
        unknown = sorted(set(raw) - set(KEYS))
        if unknown:
            raise ValueError(f"unknown key {', '.join(unknown)}; the keys are {', '.join(KEYS)}")
        given = raw.get("keys_from")
        # Not set: read the default file if it has the keys, and say nothing if it does not.
        self.explicit = given is not None
        if given is None:
            self.keys_from = DEFAULT_KEYS_FROM
        elif given is False:
            self.keys_from = None
        else:
            path = Path(os.path.expanduser(text_of(given, '"keys_from"')))
            self.keys_from = path if path.is_absolute() else SKILL_DIR / path
        self.folders = [(emoji_of(e["emoji"], f'"emoji" in entry {n} of "folders"'),
                         folder_of(e["path"], f'"path" in entry {n} of "folders"'))
                        for n, e in enumerate(entries_of(raw, "folders", ("emoji", "path"),
                                                         '{"emoji": "🏥", "path": "~/Documents/Health"}'), 1)]
        self.topics = [(emoji_of(e["emoji"], f'"emoji" in entry {n} of "topics"'),
                        text_of(e["label"], f'"label" in entry {n} of "topics"'))
                       for n, e in enumerate(entries_of(raw, "topics", ("emoji", "label"),
                                                        '{"emoji": "💻", "label": "Mac and tech support"}'), 1)]
        self.no_emoji = [folder_of(p, '"no_emoji_folders"')
                         for p in texts_of(raw, "no_emoji_folders", "config.json")]
        self.fallback = fallback_of(raw.get("fallback"))


def load_config():
    if not CONFIG_FILE.is_file():
        return Config({})
    raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("it has to hold one JSON object")
    return Config(raw)


# ---------------------------------------------------------------- keys

def key_lines(path, explicit):
    """The key lines of a Markdown file, as (folder lines, topic lines, problems).

    folder lines: [(emoji or None for "No emoji", folder path, note)]
    topic lines:  [(emoji, text)]
    """
    if path is None:
        return [], [], []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        return [], [], ([f"Could not read {path}: {e}"] if explicit else [])
    folder_body, topic_body = section(lines, FOLDER_HEADING), section(lines, TOPIC_HEADING)
    if folder_body is None and topic_body is None and not explicit:
        return [], [], []   # the default file, not set up for this: not a problem

    problems, folders, topics = [], [], []
    if folder_body is None:
        problems.append(f'No "{FOLDER_HEADING}" heading in {path}.')
    for line in folder_body or []:
        if not line.startswith("- "):
            continue
        m = FOLDER_LINE.match(line)
        if not m:
            problems.append(f"Folder key line not understood: {line}")
            continue
        lead, folder, note = m.group(1).strip(), m.group(2), m.group(3)
        root = os.path.normpath(os.path.expanduser(folder))
        if NO_EMOJI.match(lead):
            folders.append((None, root, note))
            continue
        if re.search(r"[A-Za-z0-9]", lead):
            problems.append(f"Folder key line does not start with an emoji: {line}")
            continue
        folders.append((lead, root, note))

    if topic_body is None:
        problems.append(f'No "{TOPIC_HEADING}" heading in {path}.')
    for line in topic_body or []:
        if not line.startswith("- "):
            continue
        m = TOPIC_LINE.match(line)
        if not m or re.search(r"[A-Za-z0-9]", m.group(1)):
            problems.append(f"Topic key line not understood: {line}")
            continue
        topics.append((m.group(1), m.group(2)))
    return folders, topics, problems


def read_keys(cfg):
    """Return (folders, topics, problems): the Markdown file's keys, then config.json's.

    folders: [(folder path, normalized emoji or None)], longest path first
    topics:  {normalized emoji: {"emoji", "label", "words"}}, in key order
    """
    file_folders, file_topics, problems = key_lines(cfg.keys_from, cfg.explicit)
    folder_lines = (file_folders + [(e, root, "") for e, root in cfg.folders]
                    + [(None, root, "") for root in cfg.no_emoji])
    topic_lines = file_topics + cfg.topics

    folders, topics, depth = [], {}, {}

    def topic(emoji):
        return topics.setdefault(norm(emoji), {"emoji": emoji, "label": None, "words": set()})

    for lead, root, note in folder_lines:
        if lead is None:
            folders.append((root, None))
            continue
        t = topic(lead)
        name = NUMBERING.sub("", Path(root).name)
        t["words"] |= words_in(name) | words_in(note)
        # Several folders can share an emoji. The one nearest the top names the topic.
        parts = len(Path(root).parts)
        if norm(lead) not in depth or parts < depth[norm(lead)]:
            depth[norm(lead)] = parts
            t["label"] = name
        for r in {root, os.path.realpath(root)}:
            folders.append((r, norm(lead)))

    # A topic line's label replaces one taken from a folder's name.
    for emoji, text in topic_lines:
        t = topic(emoji)
        t["label"] = re.split(r"[:,]", text, maxsplit=1)[0].strip()
        t["words"] |= words_in(text)

    fb = cfg.fallback
    if fb and norm(fb["emoji"]) in topics:
        topics[norm(fb["emoji"])]["words"] |= fb["words"]
    elif fb and topics:
        problems.append(f'{fb["emoji"]}, the "fallback" emoji in config.json, is in neither key, '
                        "so the fallback rule places no session.")

    folders.sort(key=lambda f: len(f[0]), reverse=True)
    return folders, topics, problems


class Session:
    def __init__(self, rec, directory):
        self.id = rec.get("sessionId") or ""
        self.cli_id = rec.get("cliSessionId") or ""
        self.title = (rec.get("title") or "(untitled)").strip()
        self.cwd = rec.get("cwd") or ""
        self.origin = rec.get("originCwd") or self.cwd
        self.last = rec.get("lastActivityAt") or rec.get("createdAt") or 0
        self.archived = bool(rec.get("isArchived"))
        self.task = rec.get("scheduledTaskId") or ""
        self.dir = directory
        self.topic = None

    @property
    def no_folder(self):
        return "/scratch-workspaces/" in self.cwd

    @property
    def folder(self):
        if self.no_folder:
            return "No folder"
        if self.cwd == "/":
            return "/"
        # A worktree's own name says nothing. Show the project it was cut from.
        shown = self.origin if "worktrees" in self.cwd and self.origin else self.cwd
        return Path(shown).name

    def searchable(self):
        where = "" if self.no_folder else "/".join(Path(self.origin).parts[-2:])
        return f"{self.title} {where}".lower()


def load(problems):
    dirs = sorted(d for d in APP_SUPPORT.glob("Claude*/claude-code-sessions/*/*") if d.is_dir())
    sessions, unreadable = [], 0
    for d in dirs:
        for f in d.glob("local_*.json"):
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                unreadable += 1
                continue
            if isinstance(rec, dict) and rec.get("sessionId"):
                sessions.append(Session(rec, d))
            else:
                unreadable += 1
    if unreadable:
        problems.append(f"{unreadable} session records could not be read and are left out.")
    return sessions


def current(sessions):
    """The session this is running in, or None from a terminal or an unknown app."""
    host = os.environ.get("CLAUDE_CODE_HOST_SESSION_ID")
    cli = os.environ.get("CLAUDE_CODE_SESSION_ID")
    for s in sessions:
        if host and s.id == host:
            return s
    for s in sessions:
        if cli and s.cli_id == cli:
            return s
    return None


def renamed(path, folders):
    """The keyed folder a vanished path used to sit in, as (found, emoji).

    The app records a session's folder under the name it had at the time. Once
    that folder, or one above it, is renamed, the recorded path matches no key
    line. A keyed folder's own name usually survives in the old path, so look
    for it there, deepest first. Only for paths that no longer exist: a folder
    that is still there and matches no key line is simply not in the key.
    """
    if not path or path == "/" or os.path.isdir(path):
        return False, None
    parts = Path(path).parts
    best = (-1, None)
    for root, emoji in folders:
        name = Path(root).name
        if name in parts:
            at = len(parts) - 1 - parts[::-1].index(name)
            if at > best[0]:
                best = (at, emoji)
    return best[0] >= 0, best[1]


def place(s, folders, topics, fallback=None):
    matched = False
    for p in (s.cwd, s.origin):
        for root, emoji in folders:
            if p == root or p.startswith(root + "/"):
                if emoji:
                    return emoji
                matched = True   # a "No emoji" folder: carry on to the other rules
                break
        if matched:
            break
    if not matched and not s.no_folder:
        matched, emoji = renamed(s.origin, folders)
        if emoji:
            return emoji
    if not s.task:
        title = norm(s.title)
        for key in sorted(topics, key=len, reverse=True):
            if title.startswith(key):
                return key
    # Last. Checked before the title, it would take sessions whose title gives them
    # a more specific topic.
    if fallback and norm(fallback["emoji"]) in topics:
        key = norm(fallback["emoji"])
        if any(s.task.startswith(p) for p in fallback["task_prefixes"]):
            return key
        paths = (s.cwd.lower(), s.origin.lower())
        if any(mark in p for mark in fallback["path_contains"] for p in paths):
            return key
    return None


def resolve(query, topics):
    """Return (topic key or UNTAGGED, None), or (None, why not)."""
    q = norm(query.strip())
    if q.lower() in (UNTAGGED, "none"):
        return UNTAGGED, None
    for key in sorted(topics, key=len, reverse=True):
        if q.startswith(key):
            return key, None
    w = q.lower()
    exact = [k for k, t in topics.items() if w == t["label"].lower() or w in t["words"]]
    loose = [k for k, t in topics.items() if w in t["label"].lower()]
    hits = exact or loose
    if len(hits) == 1:
        return hits[0], None
    names = ", ".join(f'{topics[k]["emoji"]} {topics[k]["label"]}' for k in (hits or topics))
    if hits:
        return None, f'"{query}" fits more than one topic: {names}. Pass the emoji.'
    return None, f'No topic fits "{query}". The topics are: {names}, and "{UNTAGGED}".'


def md(text):
    return re.sub(r"([\\\[\]*`])", r"\\\1", text)


def day(ms):
    d = datetime.fromtimestamp(ms / 1000)
    return d.strftime("%b %-d") if d.year == datetime.now().year else d.strftime("%b %-d, %Y")


def name_of(key, topics):
    if key in (None, UNTAGGED):
        return "Untagged"
    return f'{topics[key]["emoji"]} {topics[key]["label"]}'


def count(n, noun):
    return f"{n} {noun}" + ("" if n == 1 else "s")


def line(n, s, here, me):
    bits = [md(s.title), md(s.folder), day(s.last)]
    if s.archived:
        bits.append("archived")
    if me and s.id == me.id:
        bits.append("this session")
    elif here is None or s.dir != here:
        bits.append(f"in {s.dir.parts[-4]}, cannot be opened from here")
    return f"{n}. " + " · ".join(bits)


def app_pid():
    """The desktop app process this session runs under, or None outside the app."""
    pid = os.getpid()
    for _ in range(20):
        out = subprocess.run(["ps", "-o", "ppid=,command=", "-p", str(pid)],
                             capture_output=True, text=True).stdout.split(None, 1)
        if len(out) < 2:
            return None
        if APP_PROCESS.search(out[1]):
            return pid
        pid = int(out[0])
        if pid <= 1:
            return None
    return None


def open_session(wanted, sessions, me):
    if not SESSION_ID.fullmatch(wanted):
        print(f'"{wanted}" is not a session id. One looks like local_ followed by 36 characters.')
        return 2
    s = next((s for s in sessions if s.id == wanted), None)
    if s is None:
        print("No session has that id.")
        return 1
    pid = app_pid()
    if me is None or pid is None:
        print("This is not running inside the desktop app, so there is no copy of it to show the session in.")
        return 1
    if s.dir != me.dir:
        print(f'"{s.title}" is held by another copy of the app or another account '
              f"({s.dir.parts[-4]}), and only opens from there.")
        return 1
    try:
        sent = subprocess.run(["osascript", "-l", "JavaScript", "-e", SEND_LINK,
                               str(pid), f"claude://claude.ai/epitaxy/{s.id}"],
                              capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"Could not reach the app: {e}")
        return 1
    if sent.returncode != 0:
        print("The app did not take the request: " + (sent.stderr.strip() or "no reason given"))
        return 1
    print(f'Asked the app to show "{s.title}".')
    return 0


def show_counts(sessions, topics, elsewhere, scoped):
    by = defaultdict(lambda: [0, 0])
    for s in sessions:
        by[s.topic][1 if s.task else 0] += 1
    archived = sum(1 for s in sessions if s.archived)
    where = "in this copy of the app" if scoped else "across every copy of the app"
    print(f"{len(sessions)} sessions {where}, {archived} of them archived.")
    if elsewhere:
        print(f"{elsewhere} more are held by other copies or accounts; --everywhere adds them.")
    print()
    print("| Topic | Sessions | Scheduled runs |")
    print("|---|---|---|")
    order = sorted((k for k in by if k), key=lambda k: -sum(by[k]))
    for k in order + ([None] if None in by else []):
        print(f"| {name_of(k, topics)} | {by[k][0]} | {by[k][1]} |")
    empty = [name_of(k, topics) for k in topics if k not in by]
    if empty:
        print()
        print("No sessions yet: " + ", ".join(empty) + ".")


def show_list(sessions, topics, key, words, args, here, me):
    want = None if key == UNTAGGED else key
    found = [s for s in sessions if s.topic == want]
    found = [s for s in found if all(w in s.searchable() for w in words)]
    found.sort(key=lambda s: s.last, reverse=True)

    runs = [] if args.runs else [s for s in found if s.task]
    listed = found if args.runs else [s for s in found if not s.task]

    head = f"{name_of(key, topics)}: {count(len(listed), 'session')}"
    if words:
        head += ' matching "' + " ".join(words) + '"'
    limit = None if args.all else args.limit
    if limit and len(listed) > limit:
        head += f", the {limit} most recent shown (--all shows the rest)"
    print(head)
    print()
    numbered = []
    for s in listed[:limit]:
        numbered.append(s)
        print(line(len(numbered), s, here, me))
    if not listed:
        print("None.")

    if runs:
        tasks = defaultdict(list)
        for s in runs:
            tasks[s.task].append(s)
        print()
        print("Scheduled tasks on this topic, latest run of each (--runs lists every run):")
        print()
        for task, group in sorted(tasks.items(), key=lambda kv: -kv[1][0].last):
            numbered.append(group[0])
            print(line(len(numbered), group[0], here, me) + f" · {task} · {count(len(group), 'run')}")

    can_open = [(n, s) for n, s in enumerate(numbered, 1)
                if here is not None and s.dir == here and not (me and s.id == me.id)]
    if can_open:
        print()
        print("IDS for --open. Keep this block out of the reply.")
        for n, s in can_open:
            print(f"{n} {s.id}")


def main():
    ap = argparse.ArgumentParser(description="List Claude Code desktop sessions by topic, and open one.")
    ap.add_argument("topic", nargs="?", help='an emoji from the keys, a word, or "untagged"')
    ap.add_argument("words", nargs="*", help="every word must be in the title or folder")
    ap.add_argument("--runs", action="store_true", help="list each scheduled run, not one line per task")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--all", action="store_true", help="no limit")
    ap.add_argument("--everywhere", action="store_true", help="include other copies of the app and other accounts")
    ap.add_argument("--open", metavar="SESSION_ID", help="show this session in the app")
    args = ap.parse_args()

    problems = []
    sessions = load(problems)
    if not sessions:
        print(f"No session records found under {APP_SUPPORT}/Claude*/claude-code-sessions/.")
        print("The desktop app may have changed where it keeps them.")
        return 1
    me = current(sessions)
    if args.open:
        return open_session(args.open, sessions, me)

    try:
        cfg = load_config()
    except (OSError, ValueError) as e:
        print(f"Could not use {CONFIG_FILE}: {e}")
        return 2
    folders, topics, key_problems = read_keys(cfg)
    problems = key_problems + problems
    if not topics:
        print(SETUP.format(config=CONFIG_FILE, folder=FOLDER_HEADING, topic=TOPIC_HEADING,
                           skill=SKILL_DIR))
        if key_problems:
            print()
            print("Problems:")
            for p in key_problems:
                print(f"- {p}")
        return 1

    here = me.dir if me else None
    scoped = here is not None and not args.everywhere
    if here is None and not args.everywhere:
        problems.append("Could not tell which copy of the app this is, so every copy is listed and nothing can be opened.")
    elsewhere = sum(1 for s in sessions if s.dir != here) if scoped else 0
    if scoped:
        sessions = [s for s in sessions if s.dir == here]

    for s in sessions:
        s.topic = place(s, folders, topics, cfg.fallback)

    status = 0
    if args.topic is None:
        show_counts(sessions, topics, elsewhere, scoped)
    else:
        key, why = resolve(args.topic, topics)
        if why:
            print(why)
            status = 2
        else:
            show_list(sessions, topics, key, [w.lower() for w in args.words], args, here, me)

    if problems:
        print()
        print("Problems:")
        for p in problems:
            print(f"- {p}")
    return status


if __name__ == "__main__":
    sys.exit(main())
