#!/usr/bin/env python3
"""Search past Claude sessions: Claude Code, Cowork, and exported Claude Chat.

Usage:  search.py [SCOPE] [word ...] [--any WORD ...] [--source code|cowork|chat]
                  [--since DATE] [--before DATE] [--limit N] [--recent] [--runs]
        search.py [SCOPE] --titles [--page N] [--source ...] [--since ...] [--before ...]
        search.py --pick ID [ID ...] [--label TEXT] [--grep WORD ...]
        search.py --show KEY [--grep WORD ...] [--max-chars N]
        search.py --open SESSION_ID
        search.py --status
        search.py --rebuild

  search.py invoice template       sessions mentioning both words
  search.py "standing desk"        a quoted argument is a phrase
  search.py work invoice           only the scope "work", if config.json defines it
  search.py --since 2026-09-01     no words: the most recent sessions
  search.py --any dryer washer squeak       any one of the words is enough
  search.py --titles --source code          titles only, to pick from by meaning

What it searches is what the user and Claude said, plus titles. It leaves out
tool output, system text, Claude's thinking, and the helper agents' transcripts.
That matters: many Claude Code transcripts carry the full text of a CLAUDE.md
file, so a search of the raw files for a word that appears there matches every
session that loaded the file, whether or not the word was ever discussed.

The matching is by word, with word endings ignored. It does not match meaning,
so a session is missed when it is described in words it never used. Two
options exist for whoever runs this to make up for that: --any, which takes a
list of related words and ranks the sessions holding any of them, and --titles,
which prints the titles alone so that they can be read and picked from.

Settings come from config.json in the skill folder, the folder above this
script's. Every key in it is optional, and README.md describes each one.
Without the file, this reads every folder named Claude* under
~/Library/Application Support, labels each account with the start of its
folder id, skips Chat, and has no scopes.

A scope is a named part of the sessions, such as work and everything else,
defined in config.json. A session or chat belongs to the first scope with a
rule that matches it: its account, a piece of its folder path, the start of
its scheduled task's id, or, for a chat, a list file that holds its id. What
matches no scope goes to "default_scope", or to no scope when that is not set.
A word is taken as a scope only when it comes first and config.json defines
it; otherwise it is a search word like any other.

The index is a cache. It holds a copy of the conversation text in one SQLite
file, so that a search takes under a second instead of re-reading gigabytes of
transcripts. Every search first looks for sources that are new or changed and
reads only those. Deleting the file, or running --rebuild, loses nothing: it is
built again from the originals. It is also built again when config.json
changes in a way that would change what the index holds.

Chat is only as current as the newest export. Each account's exports are read
oldest first, and a chat is replaced by a later copy unless the later copy
holds less text, because a newer export sometimes arrives with a chat emptied.
An export folder is read once and then left alone.

Session records and transcripts are the desktop app's own files, and their
layout is undocumented. This only reads them.

Exit codes: 0 fine, 1 a key or id that matched no session or a session that
could not be opened, 2 bad usage or a config.json that could not be used.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

HOME = Path.home()
APP_SUPPORT = HOME / "Library" / "Application Support"
TRANSCRIPTS = HOME / ".claude" / "projects"
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = SKILL_DIR / "config.json"
DEFAULT_INDEX = SKILL_DIR / "data" / "search-index.db"
# --open borrows the code of a separate "sessions" skill that shows a session in
# the desktop app. It is optional; without it, results can still be read.
SESSIONS_SCRIPT = HOME / ".claude" / "skills" / "sessions" / "scripts" / "sessions.py"

SCHEMA = 1
DEFAULT_LIMIT = 8
NEAR_WORDS = 60   # how close together, in words, counts as about the same thing
STALE_EXPORT_DAYS = 30

SOURCES = {"code": "Claude Code", "cowork": "Cowork", "chat": "Chat"}
SESSION_FOLDERS = {"code": "claude-code-sessions", "cowork": "local-agent-mode-sessions"}
UNKNOWN = "unknown"   # the account of a transcript the app has no record of

DATED = re.compile(r"\d{4}\.\d{2}\.\d{2}")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
# Text the app wraps around a message. None of it is something the user typed.
WRAPPED = re.compile(
    r"<(system-reminder|local-command-[a-z-]+|command-[a-z-]+|task-notification)\b[^>]*>.*?</\1>",
    re.S)
# Chat tools whose input is a draft Claude wrote, which is worth finding.
DRAFT_TOOLS = {"artifacts", "create_file", "message_compose_v1"}

# Speaker marks in the stored text. Symbols, so that they add no searchable word.
USER, CLAUDE = "▶ ", "◀ "
# The first words of this script's own output. A reply that relays a result list
# would otherwise make its session match every word in the titles it listed.
RESULT_MARK = "Search results for"


# ---------------------------------------------------------------- settings

KEYS = ("exports", "export_accounts", "accounts", "apps", "scopes", "default_scope", "index")
RULES = ("accounts", "path_contains", "task_prefixes", "chat_lists")
NO_SCOPE = "no scope"
SCOPE_NAME = re.compile(r"[^\s-]\S*")   # one word, not starting with "-"


def text_of(raw, key, where="config.json"):
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'"{key}" in {where} has to be text')
    return value.strip()


def path_of(raw, key):
    value = text_of(raw, key)
    if value is None:
        return None
    path = Path(os.path.expanduser(value))
    return path if path.is_absolute() else SKILL_DIR / path


def labels_of(raw, key):
    value = raw.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in value.items()):
        raise ValueError(f'"{key}" has to map names to labels, like {{"name": "label"}}')
    return {k: v.strip() for k, v in value.items()}


def words_of(raw, key, where):
    value = raw.get(key)
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f'"{key}" in {where} has to be a list of text')
    return [v for v in value if v]


def scope_of_config(raw, n):
    if not isinstance(raw, dict):
        raise ValueError(f'scope {n} in "scopes" has to be an object')
    name = raw.get("name")
    if not isinstance(name, str) or not SCOPE_NAME.fullmatch(name):
        raise ValueError(f'scope {n} in "scopes" needs a "name": one word, not starting with "-"')
    unknown = sorted(set(raw) - {"name", *RULES})
    if unknown:
        raise ValueError(f'scope "{name}" has an unknown key {", ".join(unknown)}; '
                         f'a scope takes "name", {", ".join(RULES)}')
    rules = {key: words_of(raw, key, f'scope "{name}"') for key in RULES}
    rules["path_contains"] = [p.lower() for p in rules["path_contains"]]
    for pattern in rules["chat_lists"]:
        if os.path.isabs(os.path.expanduser(pattern)):
            raise ValueError(f'"chat_lists" in scope "{name}" are relative to the exports folder, '
                             f"and {pattern} is not")
    return {"name": name, **rules}


class Config:
    """config.json, checked, with every key it leaves out at its default."""

    def __init__(self, raw):
        unknown = sorted(set(raw) - set(KEYS))
        if unknown:
            raise ValueError(f"unknown key {', '.join(unknown)}; the keys are {', '.join(KEYS)}")
        self.exports = path_of(raw, "exports")
        self.export_accounts = labels_of(raw, "export_accounts")
        self.accounts = labels_of(raw, "accounts")
        self.apps = labels_of(raw, "apps")
        self.index = path_of(raw, "index") or DEFAULT_INDEX
        given = raw.get("scopes")
        if given is not None and not isinstance(given, list):
            raise ValueError('"scopes" has to be a list')
        self.scopes = [scope_of_config(s, n) for n, s in enumerate(given or [], 1)]
        names = [s["name"].lower() for s in self.scopes]
        if len(set(names)) < len(names):
            raise ValueError("two scopes have the same name")
        default = text_of(raw, "default_scope")
        if default is not None and not SCOPE_NAME.fullmatch(default):
            raise ValueError('"default_scope" has to be one word, not starting with "-"')
        if default is not None and default.lower() in names:
            default = self.scopes[names.index(default.lower())]["name"]
        # A default scope with no scopes to fall back from would hold everything.
        self.default_scope = default if self.scopes else None

    def scope_names(self):
        """Every scope a session can be in, in order, the default scope last."""
        names = [s["name"] for s in self.scopes]
        if self.default_scope and self.default_scope not in names:
            names.append(self.default_scope)
        return names

    def fingerprint(self):
        """Changes whenever a setting that decides what the index holds changes."""
        held = {"exports": str(self.exports or ""), "export_accounts": self.export_accounts,
                "accounts": self.accounts, "apps": self.apps, "scopes": self.scopes,
                "default_scope": self.default_scope}
        return hashlib.sha256(json.dumps(held, sort_keys=True).encode()).hexdigest()[:16]


def load_config():
    if not CONFIG_FILE.is_file():
        return Config({})
    raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("it has to hold one JSON object")
    return Config(raw)


CFG = Config({})   # replaced in main() by what config.json says


def account_label(org):
    """The label config.json gives an account's folder id, or the start of the id."""
    return CFG.accounts.get(org) or org[:8]


def app_folders():
    """The desktop app's data folders: the ones config.json names, or every Claude* folder."""
    if CFG.apps:
        return [APP_SUPPORT / name for name in CFG.apps]
    return sorted(p for p in APP_SUPPORT.glob("Claude*") if p.is_dir())


def app_label(name):
    return CFG.apps.get(name) or f"{name} app"


def session_scope(account, task, paths):
    """The first scope with a rule that matches this session, or the default scope."""
    task = task or ""
    low = [(p or "").lower() for p in paths]
    for s in CFG.scopes:
        if (account in s["accounts"]
                or any(task.startswith(prefix) for prefix in s["task_prefixes"])
                or any(mark in p for mark in s["path_contains"] for p in low)):
            return s["name"]
    return CFG.default_scope


def chat_scope(account, uuid, listed):
    """The first scope whose accounts or chat lists take in this chat, or the default scope."""
    for s in CFG.scopes:
        if account in s["accounts"] or uuid in listed.get(s["name"], ()):
            return s["name"]
    return CFG.default_scope


# ---------------------------------------------------------------- the index

def connect(rebuild=False):
    """The open index, and why it was built again, if it was."""
    index = CFG.index
    index.parent.mkdir(parents=True, exist_ok=True)
    if rebuild:
        for suffix in ("", "-wal", "-shm"):
            Path(str(index) + suffix).unlink(missing_ok=True)
    if not index.exists():
        # Made private before anything is written to it: it holds conversation text.
        os.close(os.open(index, os.O_CREAT | os.O_WRONLY, 0o600))
    db = sqlite3.connect(index, timeout=60)
    os.chmod(index, 0o600)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    made = db.execute("SELECT name FROM sqlite_master WHERE name='meta'").fetchone()
    if made and (get(db, "schema") != str(SCHEMA) or get(db, "config") != CFG.fingerprint()):
        db.close()
        return connect(rebuild=True)[0], "The index was made with other settings, so it was built again."
    if not made:
        db.executescript("""
            CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE files(path TEXT PRIMARY KEY, mtime REAL, size INTEGER);
            CREATE TABLE docs(
                id INTEGER PRIMARY KEY, key TEXT UNIQUE, source TEXT, account TEXT,
                scope TEXT, title TEXT, folder TEXT, place TEXT, session_id TEXT,
                cli_id TEXT, url TEXT, created INTEGER, updated INTEGER,
                archived INTEGER, scheduled TEXT, chars INTEGER);
            CREATE INDEX docs_source ON docs(source, scope);
            CREATE VIRTUAL TABLE fts USING fts5(
                title, body, tokenize='porter unicode61 remove_diacritics 2');
        """)
        put_meta(db, "schema", SCHEMA)
        put_meta(db, "config", CFG.fingerprint())
        db.commit()
    return db, None


def get(db, key):
    row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def put_meta(db, key, value):
    db.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (key, str(value)))


FIELDS = ("source", "account", "scope", "title", "folder", "place", "session_id",
          "cli_id", "url", "created", "updated", "archived", "scheduled")


def put(db, key, doc, titles, body=None):
    """Add or replace one session. body=None keeps the text already stored."""
    row = db.execute("SELECT id FROM docs WHERE key=?", (key,)).fetchone()
    values = [doc.get(f) for f in FIELDS]
    if row is None:
        cur = db.execute(
            f"INSERT INTO docs(key, {', '.join(FIELDS)}, chars) VALUES (?{', ?' * len(FIELDS)}, ?)",
            [key] + values + [len(body or "")])
        db.execute("INSERT INTO fts(rowid, title, body) VALUES (?, ?, ?)",
                   (cur.lastrowid, titles, body or ""))
        return
    db.execute(f"UPDATE docs SET {', '.join(f + '=?' for f in FIELDS)} WHERE id=?",
               values + [row["id"]])
    if body is None:
        db.execute("UPDATE fts SET title=? WHERE rowid=?", (titles, row["id"]))
    else:
        db.execute("UPDATE docs SET chars=? WHERE id=?", (len(body), row["id"]))
        db.execute("UPDATE fts SET title=?, body=? WHERE rowid=?", (titles, body, row["id"]))


def drop(db, key):
    row = db.execute("SELECT id FROM docs WHERE key=?", (key,)).fetchone()
    if row:
        db.execute("DELETE FROM fts WHERE rowid=?", (row["id"],))
        db.execute("DELETE FROM docs WHERE id=?", (row["id"],))


class Files:
    """Which source files are new or changed since the last search."""

    def __init__(self, db):
        self.before = {r["path"]: (r["mtime"], r["size"])
                       for r in db.execute("SELECT * FROM files")}
        self.now = {}

    def changed(self, path):
        try:
            st = path.stat()
        except OSError:
            return False
        self.now[str(path)] = (st.st_mtime, st.st_size)
        return self.before.get(str(path)) != self.now[str(path)]

    def save(self, db):
        db.execute("DELETE FROM files")
        db.executemany("INSERT INTO files VALUES (?, ?, ?)",
                       [(p, m, s) for p, (m, s) in self.now.items()])


# ------------------------------------------------------- reading the sources

def said(record):
    """What the user or Claude said in one transcript record, with its speaker mark."""
    who = record.get("type")
    if who not in ("user", "assistant"):
        return None
    if record.get("isMeta") or record.get("isSidechain") or record.get("isCompactSummary"):
        return None
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        parts = [content]
    elif isinstance(content, list):
        parts = [b.get("text") or "" for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return None
    text = WRAPPED.sub(" ", "\n".join(parts)).strip()
    if not text or (who == "assistant" and text.startswith(RESULT_MARK)):
        return None
    return (USER if who == "user" else CLAUDE) + text


def read_transcript(path):
    """(text, title, folder, first and last time in ms) from one transcript."""
    spoken, title, folder, first, last = [], None, None, None, None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(r, dict):
                    continue
                kind = r.get("type")
                if kind == "custom-title" and r.get("customTitle"):
                    title = r["customTitle"]
                elif kind == "ai-title" and r.get("aiTitle") and title is None:
                    title = r["aiTitle"]
                folder = folder or r.get("cwd")
                stamp = r.get("timestamp")
                if isinstance(stamp, str):
                    ms = to_ms(stamp)
                    if ms:
                        first = first or ms
                        last = ms
                text = said(r)
                if text:
                    spoken.append(text)
    except OSError:
        return None
    return "\n\n".join(spoken), title, folder, first, last


def to_ms(stamp):
    try:
        return int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp() * 1000)
    except (ValueError, AttributeError):
        return None


def mtime(path):
    try:
        return path.stat().st_mtime
    except OSError:
        return 0


def folder_name(path):
    if not path:
        return ""
    if "/scratch-workspaces/" in path:
        return "No folder"
    return "/" if path == "/" else Path(path).name


def all_transcripts():
    """Transcript file by session id. A moved session leaves a stale copy; take the newest."""
    found = {}
    if not TRANSCRIPTS.is_dir():
        return found
    for d in TRANSCRIPTS.iterdir():
        if not d.is_dir():
            continue
        for f in d.glob("*.jsonl"):
            old = found.get(f.stem)
            if old is None or f.stat().st_mtime > old.stat().st_mtime:
                found[f.stem] = f
    return found


def index_sessions(db, files, source, transcripts, problems):
    known = {r["key"]: r for r in db.execute(
        "SELECT key, cli_id FROM docs WHERE source=?", (source,))}
    seen, used, unreadable = set(), set(), 0
    # A session moved to another account folder can leave a stale copy of its
    # record behind under the same name. Take the newest, as for transcripts.
    records = {}
    for app in app_folders():
        for rec in app.glob(f"{SESSION_FOLDERS[source]}/*/*/local_*.json"):
            old = records.get(rec.stem)
            if old is None or mtime(rec) > mtime(old):
                records[rec.stem] = rec
    for rec in records.values():
        key = f"{source}:{rec.stem}"
        seen.add(key)
        had = known.get(key)
        rec_changed = files.changed(rec) or had is None
        meta = None
        if rec_changed:
            try:
                meta = json.loads(rec.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                unreadable += 1   # perhaps mid-write; what is stored for it stays
                continue
        cli = (meta or {}).get("cliSessionId") or (had["cli_id"] if had else "") or ""
        if source == "code":
            script = transcripts.get(cli)
            used.add(cli)
        else:
            script = rec.with_suffix("") / "audit.jsonl"
            script = script if script.is_file() else None
        body = None
        if script is not None and (files.changed(script) or had is None):
            read = read_transcript(script)
            body = read[0] if read else None
        if meta is None and body is None:
            continue
        if meta is None:
            # Only the transcript grew. Everything else about the session stands.
            row = db.execute("SELECT id FROM docs WHERE key=?", (key,)).fetchone()
            db.execute("UPDATE docs SET chars=? WHERE id=?", (len(body), row["id"]))
            db.execute("UPDATE fts SET body=? WHERE rowid=?", (body, row["id"]))
            continue
        # The app files each session under a folder named for the account that ran it.
        account = account_label(rec.parent.name)
        picked = meta.get("userSelectedFolders") or []
        where = meta.get("originCwd") or meta.get("cwd") or ""
        if source == "cowork":
            where = picked[0] if picked and isinstance(picked[0], str) else ""
        task = meta.get("scheduledTaskId") or ""
        paths = [meta.get("cwd"), meta.get("originCwd")] + [p for p in picked if isinstance(p, str)]
        title = (meta.get("title") or "(untitled)").strip()
        older = [t for t in meta.get("previousTitles") or [] if isinstance(t, str)]
        put(db, key, {
            "source": source, "account": account,
            "scope": session_scope(account, task, paths),
            "title": title, "folder": folder_name(where), "place": rec.parts[-5],
            "session_id": meta.get("sessionId") or rec.stem, "cli_id": cli, "url": None,
            "created": meta.get("createdAt"), "updated": meta.get("lastActivityAt") or meta.get("createdAt"),
            "archived": 1 if meta.get("isArchived") else 0, "scheduled": task,
        }, " / ".join([title] + older), body)

    if source == "code":
        # Transcripts the app has no record of, such as sessions run in a terminal.
        for cli, script in transcripts.items():
            if cli in used:
                continue
            key = f"code:cli:{cli}"
            seen.add(key)
            if not files.changed(script) and key in known:
                continue
            read = read_transcript(script)
            if not read:
                unreadable += 1
                continue
            body, title, where, first, last = read
            put(db, key, {
                "source": "code", "account": UNKNOWN,
                "scope": session_scope(UNKNOWN, "", [where, script.parent.name]),
                "title": title or "(untitled)", "folder": folder_name(where), "place": "",
                "session_id": "", "cli_id": cli, "url": None, "created": first,
                "updated": last, "archived": 0, "scheduled": "",
            }, title or "", body)

    for key in set(known) - seen:
        drop(db, key)   # the session was deleted
    if unreadable:
        problems.append(f"{unreadable} {SOURCES[source]} sessions could not be read and are left out.")


def chat_text(chat):
    spoken, count = [], 0
    for m in chat.get("chat_messages") or []:
        parts = []
        for b in m.get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                parts.append(b.get("text") or "")
            elif b.get("type") == "tool_use" and b.get("name") in DRAFT_TOOLS:
                made = b.get("input") or {}
                parts.extend(v for v in made.values() if isinstance(v, str) and len(v) > 40)
        if not any(p.strip() for p in parts):
            parts = [m.get("text") or ""]
        parts.extend(a.get("file_name") or "" for a in m.get("attachments") or []
                     if isinstance(a, dict))
        text = "\n".join(p for p in parts if p.strip()).strip()
        if text:
            spoken.append((USER if m.get("sender") == "human" else CLAUDE) + text)
            count += len(text)
    return "\n\n".join(spoken), count


def chat_off():
    """Why no Chat exports can be read, or None when they can."""
    if CFG.exports is None:
        return 'Chat is not searched: no "exports" folder is set in config.json.'
    if not CFG.exports.is_dir():
        return f"Chat exports cannot be read: there is no folder at {CFG.exports}."
    return None


def export_accounts():
    """(folder, account label) for each account folder under the exports folder."""
    root = CFG.exports
    if CFG.export_accounts:
        return [(root / name, label) for name, label in CFG.export_accounts.items()]
    return [(d, d.name) for d in sorted(root.iterdir())
            if d.is_dir() and not d.name.startswith(".")]


def listed_chats(db, files):
    """The chat ids each scope's list files hold, and whether those lists changed."""
    listed, changed, found = {}, False, set()
    for s in CFG.scopes:
        ids = set()
        for pattern in s["chat_lists"]:
            for listing in sorted(CFG.exports.glob(pattern)):
                if not listing.is_file():
                    continue
                found.add(str(listing))
                changed = files.changed(listing) or changed
                try:
                    ids.update(UUID.findall(listing.read_text(encoding="utf-8", errors="replace")))
                except OSError:
                    pass
        listed[s["name"]] = ids
    names = json.dumps(sorted(found))
    if get(db, "chat_lists") != names:   # a list file was added or taken away
        changed = True
        put_meta(db, "chat_lists", names)
    return listed, changed


def index_chats(db, files, problems):
    if CFG.exports is None:
        return
    if not CFG.exports.is_dir():
        problems.append(f"No Chat exports folder at {CFG.exports}.")
        return
    done = set(json.loads(get(db, "exports_read") or "[]"))
    listed, list_changed = listed_chats(db, files)
    newest = {}
    for base, account in export_accounts():
        if not base.is_dir():
            problems.append(f"No Chat exports folder at {base}.")
            continue
        dated = sorted(d for d in base.iterdir() if d.is_dir() and DATED.fullmatch(d.name))
        if dated:
            newest[account] = dated[-1].name
        for export in dated:               # oldest first, so that the newest copy wins
            if str(export) in done:
                continue
            sizes = {r["key"]: r["chars"] for r in db.execute(
                "SELECT key, chars FROM docs WHERE source='chat'")}
            for f in sorted(export.rglob("conversations.json")):
                try:
                    chats = json.loads(f.read_text(encoding="utf-8"))
                except (OSError, ValueError) as e:
                    problems.append(f"Could not read {f}: {e}")
                    continue
                for chat in chats:
                    uuid = chat.get("uuid")
                    if not uuid:
                        continue
                    key = f"chat:{uuid}"
                    body, count = chat_text(chat)
                    if count < sizes.get(key, -1):
                        continue           # this export holds less of the chat
                    sizes[key] = count
                    title = (chat.get("name") or "").strip() or "(untitled)"
                    put(db, key, {
                        "source": "chat", "account": account,
                        "scope": chat_scope(account, uuid, listed),
                        "title": title, "folder": "", "place": export.name,
                        "session_id": uuid, "cli_id": "", "url": f"https://claude.ai/chat/{uuid}",
                        "created": to_ms(chat.get("created_at") or ""),
                        "updated": to_ms(chat.get("updated_at") or chat.get("created_at") or ""),
                        "archived": 0, "scheduled": "",
                    }, title + " / " + (chat.get("summary") or "")[:400], body)
            done.add(str(export))
    if list_changed:
        rows = db.execute("SELECT key, account, session_id FROM docs WHERE source='chat'").fetchall()
        db.executemany("UPDATE docs SET scope=? WHERE key=?",
                       [(chat_scope(r["account"], r["session_id"], listed), r["key"]) for r in rows])
    put_meta(db, "exports_read", json.dumps(sorted(done)))
    put_meta(db, "newest_exports", json.dumps(newest))


def update(db, problems):
    started = time.time()
    first = get(db, "updated_at") is None
    files = Files(db)
    transcripts = all_transcripts()
    index_sessions(db, files, "code", transcripts, problems)
    index_sessions(db, files, "cowork", {}, problems)
    index_chats(db, files, problems)
    files.save(db)
    put_meta(db, "updated_at", int(time.time()))
    db.commit()
    return first, time.time() - started


# ------------------------------------------------------------------ output

def day(ms):
    if not ms:
        return "no date"
    d = datetime.fromtimestamp(ms / 1000)
    return d.strftime("%b %-d") if d.year == datetime.now().year else d.strftime("%b %-d, %Y")


def md(text):
    return re.sub(r"([\\\[\]*`])", r"\\\1", text or "")


def tidy(snippet):
    text = snippet.replace(USER.strip(), " ").replace(CLAUDE.strip(), " ")
    return re.sub(r"\s+", " ", text).strip()


def me():
    return os.environ.get("CLAUDE_CODE_HOST_SESSION_ID") or "", os.environ.get("CLAUDE_CODE_SESSION_ID") or ""


def my_place(db):
    """The copy of the app and the account folder this session runs under."""
    host = me()[0]
    if not host:
        return None, None
    for app in app_folders():
        for rec in app.glob(f"claude-code-sessions/*/*/{host}.json"):
            return rec.parts[-5], rec.parent.name
    return None, None


def export_note(db):
    newest = json.loads(get(db, "newest_exports") or "{}")
    bits, old = [], []
    for account, name in newest.items():
        taken = datetime.strptime(name, "%Y.%m.%d")
        age = (datetime.now() - taken).days
        bits.append(f"{account} {taken.strftime('%b %-d')}")
        if age > STALE_EXPORT_DAYS:
            old.append(f"the {account} export is {age} days old")
    if not bits:
        return None
    note = "Chat is searched through the last export: " + ", ".join(bits) + "."
    if old:
        note += " Chats since then are missing, and " + " and ".join(old) + "."
    return note


def fts_query(words, either=()):
    """Every one of `words`, and at least one of `either`."""
    def terms(given):
        out = []
        for w in given:
            w = w.replace('"', " ").strip()
            if re.search(r"\w", w):
                out.append(f'"{w}"')
        return out

    parts = terms(words)
    any_of = terms(either)
    if any_of:
        parts.append("(" + " OR ".join(any_of) + ")")
    return " AND ".join(parts)


def near_query(words, either=()):
    """The same words, but close together. None when that adds nothing.

    A long session holds most common words somewhere, so three words found
    anywhere in it say little. The same three within a few sentences of each
    other are very likely the subject.
    """
    found = [w.replace('"', " ").strip() for w in words if re.search(r"\w", w)]
    if either or len(found) < 2:
        return None
    return "NEAR(" + " ".join(f'"{w}"' for w in found) + f", {NEAR_WORDS})"


def scope_of(args):
    """The scope the first word names, if config.json defines it, and the other words."""
    words = list(args.words)
    names = {n.lower(): n for n in CFG.scope_names()}
    scope = names.get(words[0].lower()) if words else None
    if scope:
        words.pop(0)
    return scope, words


def conditions(args, scope):
    """The tests every listing shares, as (SQL pieces, values). None for a bad date."""
    where, values = [], []
    if scope:
        where.append("d.scope = ?")
        values.append(scope)
    if args.source:
        where.append("d.source = ?")
        values.append(args.source)
    if not args.runs:
        where.append("(d.scheduled IS NULL OR d.scheduled = '')")
    for flag, test in ((args.since, "d.updated >= ?"), (args.before, "d.created <= ?")):
        if flag:
            try:
                values.append(int(datetime.strptime(flag, "%Y-%m-%d").timestamp() * 1000))
            except ValueError:
                print(f'"{flag}" is not a date. Write it as 2026-09-01.')
                return None
            where.append(test)
    host, cli = me()
    where.append("d.session_id != ? AND d.cli_id != ?")   # never the session asking
    values += [host or "-", cli or "-"]
    return where, values


def print_list(db, heading, sources, groups):
    """groups: [(source, rows, how many were found)]. Each row has the docs columns and `piece`."""
    print(heading)
    note = export_note(db)
    if note and "chat" in sources:
        print(note)
    app, account_dir = my_place(db)
    can_open = SESSIONS_SCRIPT.is_file()
    number, ids = 0, []
    for source, rows, found in groups:
        if not rows:
            continue
        shown = "" if found <= len(rows) else f", the top {len(rows)} shown"
        print(f"\n{SOURCES[source]}: {found} found{shown}\n")
        for r in rows:
            number += 1
            bits = [day(r["updated"])]
            if r["account"] and r["account"] != UNKNOWN:
                bits.append(f"{r['account']} account")
            if r["folder"]:
                bits.append(md(r["folder"]))
            if r["archived"]:
                bits.append("archived")
            here = (source == "code" and app and r["session_id"] and r["place"] == app
                    and r["account"] == account_label(account_dir))
            if source == "code" and not here and r["place"]:
                bits.append("open it in the " + app_label(r["place"]))
            name = md(r["title"])
            if r["url"]:
                name = f"[{name}]({r['url']})"
            print(f"{number}. {name} · " + " · ".join(bits))
            piece = tidy(r["piece"] or "")
            if piece:
                print(f"   {md(piece)}")
            ids.append((number, r["key"], r["session_id"] if here and can_open else ""))
    if not ids:
        print("\nNothing found.")
        return
    print("\nIDS for --show and --open. Keep this block out of the reply.")
    for n, key, opens in ids:
        print(f"{n} {key}" + (f" open={opens}" if opens else ""))


def search(db, args, problems):
    scope, words = scope_of(args)
    either = list(args.any or [])
    query = fts_query(words, either)
    built = conditions(args, scope)
    if built is None:
        return 2
    where, values = built
    if query:
        where, values = ["fts MATCH ?"] + where, [query] + values
    if args.source == "chat" and CFG.exports is None:
        problems.append(chat_off())

    sources = [args.source] if args.source else list(SOURCES)
    ranked = query and not args.recent
    order = "bm25(fts, 8.0, 1.0), d.updated DESC" if ranked else "d.updated DESC"
    piece = "snippet(fts, 1, '', '', ' … ', 26)" if query else "substr(fts.body, 1, 200)"

    near = near_query(words, either) if ranked else None
    groups = []
    for source in sources:
        clause = " AND ".join(where + ["d.source = ?"])
        select = (f"SELECT d.*, {piece} AS piece FROM fts JOIN docs d ON d.id = fts.rowid "
                  f"WHERE {clause} ORDER BY {order} LIMIT ?")
        found = db.execute(
            f"SELECT count(*) FROM fts JOIN docs d ON d.id = fts.rowid WHERE {clause}",
            values + [source]).fetchone()[0]
        rows = []
        if found and near:
            # Sessions with the words close together come first.
            rows = db.execute(select, [near] + values[1:] + [source, args.limit]).fetchall()
        if found and len(rows) < args.limit:
            have = {r["id"] for r in rows}
            more = db.execute(select, values + [source, args.limit + len(have)]).fetchall()
            rows += [r for r in more if r["id"] not in have][:args.limit - len(rows)]
        groups.append((source, rows, found))

    spell = lambda given: ", ".join(f'"{w}"' if " " in w else w for w in given)
    asked = " ".join(f'"{w}"' if " " in w else w for w in words)
    if either:
        asked = (asked + " with " if asked else "") + "any of " + spell(either)
    heading = f"{RESULT_MARK} {asked or 'the most recent sessions'}" + (f", in {scope}" if scope else "")
    print_list(db, heading, sources, groups)
    return 0


TITLES_PER_PAGE = 350   # about 25 KB, which a tool result shows in full


def titles(db, args):
    """Titles only, for picking by meaning when no word search finds the session."""
    scope, _ = scope_of(args)
    built = conditions(args, scope)
    if built is None:
        return 2
    where, values = built
    rows = db.execute(
        f"SELECT d.id, d.source, d.title, d.updated FROM docs d WHERE {' AND '.join(where)} "
        "ORDER BY CASE d.source WHEN 'code' THEN 1 WHEN 'cowork' THEN 2 ELSE 3 END, d.updated DESC",
        values).fetchall()
    pages = max(1, -(-len(rows) // TITLES_PER_PAGE))
    page = min(max(args.page, 1), pages)
    print(f"{len(rows):,} titles" + (f" in {scope}" if scope else "") + f". Page {page} of {pages}.")
    print("Each line is an id, the date last active, and the title. "
          "Pass the ids of the likely ones to --pick.")
    last = None
    for r in rows[(page - 1) * TITLES_PER_PAGE: page * TITLES_PER_PAGE]:
        if r["source"] != last:
            last = r["source"]
            print(f"\n{SOURCES[last]}")
        print(f"{r['id']} · {day(r['updated'])} · {r['title']}")
    return 0


def passage(body, wanted, width=220):
    """A stretch of the conversation: around the first wanted word, or its opening."""
    low = body.lower()
    at = min((low.find(w) for w in wanted if w in low), default=0)
    start = max(0, at - width // 3)
    text = body[start:start + width]
    return ("… " if start else "") + text + (" …" if start + width < len(body) else "")


def pick(db, args, problems):
    """Print the sessions with these ids as a result list."""
    marks = ", ".join("?" * len(args.pick))
    rows = db.execute(
        "SELECT d.*, fts.body AS body FROM docs d JOIN fts ON fts.rowid = d.id "
        f"WHERE d.id IN ({marks})", args.pick).fetchall()
    place = {wanted: n for n, wanted in enumerate(args.pick)}
    missing = [str(i) for i in args.pick if i not in {r["id"] for r in rows}]
    if missing:
        problems.append("No session has the id " + ", ".join(missing) + ". Ids come from --titles.")
    wanted = [w.lower() for w in args.grep or []]
    groups = []
    for source in SOURCES:
        mine = []
        for r in sorted((r for r in rows if r["source"] == source), key=lambda r: place[r["id"]]):
            row = dict(r)
            row["piece"] = passage(r["body"] or "", wanted)
            mine.append(row)
        groups.append((source, mine, len(mine)))
    heading = f"{RESULT_MARK} {args.label or 'the sessions picked'}, picked by title"
    print_list(db, heading, [r["source"] for r in rows], groups)
    return 0


def show(db, args):
    by = "d.id" if args.show.isdigit() else "d.key"   # an id from --titles, or a key from a result
    row = db.execute("SELECT d.*, fts.body AS body FROM docs d JOIN fts ON fts.rowid = d.id "
                     f"WHERE {by} = ?", (args.show,)).fetchone()
    if row is None:
        print(f'No session has the key or id "{args.show}". Take it from a search result or from --titles.')
        return 1
    print(f"{row['title']} · {SOURCES[row['source']]} · {day(row['updated'])} · {row['account']} account")
    if row["url"]:
        print(row["url"])
    print()
    turns = [t for t in re.split(r"\n\n(?=[▶◀] )", row["body"] or "") if t.strip()]
    wanted = [w.lower() for w in args.grep or []]
    if wanted:
        turns = [t for t in turns if all(w in t.lower() for w in wanted)]
    left = args.max_chars
    for t in turns:
        who = "User" if t.startswith(USER.strip()) else "Claude"
        text = t[1:].strip()
        text = text if len(text) <= 1500 or not wanted else text[:1500] + " […]"
        piece = f"{who}: {text}\n"
        if len(piece) > left:
            print(piece[:left] + "\n[cut short; raise --max-chars or add --grep WORD]")
            break
        print(piece)
        left -= len(piece)
    if not turns:
        print("No conversation text is stored for this one. Only its title can be searched.")
    return 0


def open_session(session_id):
    if not SESSIONS_SCRIPT.is_file():
        print(f"Opening a session needs the sessions skill's script at {SESSIONS_SCRIPT}, "
              "which is not there. README.md says what it has to provide. "
              "A result can still be read with --show.")
        return 1
    spec = importlib.util.spec_from_file_location("sessions_skill", SESSIONS_SCRIPT)
    skill = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(skill)
    held = skill.load([])
    return skill.open_session(session_id, held, skill.current(held))


def status(db):
    print(f"Index: {CFG.index} ({CFG.index.stat().st_size / 1e6:.0f} MB)")
    when = get(db, "updated_at")
    if when:
        print("Last brought up to date: " + datetime.fromtimestamp(int(when)).strftime("%b %-d, %H:%M"))
    print()
    names = CFG.scope_names()
    if names:
        columns = names + ([] if CFG.default_scope else [NO_SCOPE])
        counts = ", ".join(["sum(ifnull(scope, '') = ?)"] * len(names))
        counts += "" if CFG.default_scope else ", sum(scope IS NULL)"
        values = names
    else:
        columns, counts, values = ["Total"], "count(*)", []
    print("| Source | Account | " + " | ".join(columns) + " |")
    print("|---|---|" + "---|" * len(columns))
    for r in db.execute(
            f"SELECT source, account, {counts} FROM docs "
            "GROUP BY source, account ORDER BY source, account", values):
        print(f"| {SOURCES[r[0]]} | {r[1]} | " + " | ".join(str(v) for v in tuple(r)[2:]) + " |")
    bare = db.execute("SELECT count(*) FROM docs WHERE chars = 0").fetchone()[0]
    runs = db.execute("SELECT count(*) FROM docs WHERE scheduled != ''").fetchone()[0]
    print(f"\n{bare} have a title but no conversation text. "
          f"{runs} are scheduled-task runs, left out unless --runs is given.")
    off = chat_off()
    if off:
        print(off)
    note = export_note(db) if CFG.exports is not None else None
    if note:
        print(note)
    return 0


def main():
    global CFG
    try:
        CFG = load_config()
    except (OSError, ValueError) as e:
        print(f"Could not use {CONFIG_FILE}: {e}")
        return 2

    names = CFG.scope_names()
    words_help = (f"a scope name first ({', '.join(names)}) to search only that scope, then the words"
                  if names else "the words to search for")
    ap = argparse.ArgumentParser(description="Search past Claude sessions.")
    ap.add_argument("words", nargs="*", help=words_help)
    ap.add_argument("--source", choices=list(SOURCES))
    ap.add_argument("--since", metavar="DATE", help="active on or after, as 2026-09-01")
    ap.add_argument("--before", metavar="DATE", help="started on or before, as 2026-09-01")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="results shown per source")
    ap.add_argument("--recent", action="store_true", help="newest first, not best match first")
    ap.add_argument("--runs", action="store_true", help="include scheduled-task runs")
    ap.add_argument("--any", nargs="+", metavar="WORD",
                    help="at least one of these has to be in the session")
    ap.add_argument("--titles", action="store_true", help="list titles in scope, to pick by meaning")
    ap.add_argument("--page", type=int, default=1, help="with --titles")
    ap.add_argument("--pick", nargs="+", type=int, metavar="ID",
                    help="print the sessions with these ids from --titles as a result list")
    ap.add_argument("--label", metavar="TEXT", help="with --pick: what was being looked for")
    ap.add_argument("--show", metavar="KEY", help="print what was said in one session, by key or by id")
    ap.add_argument("--grep", nargs="*", metavar="WORD",
                    help="with --show: only turns with these words. With --pick: show the text near them")
    ap.add_argument("--max-chars", type=int, default=8000)
    ap.add_argument("--open", metavar="SESSION_ID",
                    help="show a Claude Code session in the app (needs the sessions skill)")
    ap.add_argument("--status", action="store_true", help="what the index holds")
    ap.add_argument("--rebuild", action="store_true", help="build the index again from nothing")
    args = ap.parse_args()

    if args.open:
        return open_session(args.open)

    problems = []
    db, why = connect(rebuild=args.rebuild)
    first, took = update(db, problems)
    if why:
        print(why)
    if first:
        n = db.execute("SELECT count(*) FROM docs").fetchone()[0]
        print(f"Built the index: {n:,} sessions and chats in {took:.0f} seconds.\n")

    if args.show:
        code = show(db, args)
    elif args.pick:
        code = pick(db, args, problems)
    elif args.titles:
        code = titles(db, args)
    elif args.status or (args.rebuild and not args.words):
        code = status(db)
    else:
        code = search(db, args, problems)

    if problems:
        print("\nProblems:")
        for p in problems:
            print(f"- {p}")
    return code


if __name__ == "__main__":
    sys.exit(main())
