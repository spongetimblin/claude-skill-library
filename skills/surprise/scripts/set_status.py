#!/usr/bin/env python3
"""Update one item's status on a run's index.html.

Usage: set_status.py <run folder> "<item title>" ok|warn|wip ["note"]

ok   = finished and checked
warn = finished with a caveat, or partly done (put the caveat in the note)
wip  = still being built
The page's "last updated" time is set from the clock.
"""
import json, os, re, sys, time

if len(sys.argv) < 4 or sys.argv[3] not in ("ok", "warn", "wip"):
    sys.exit(__doc__)
run, title, status = sys.argv[1], sys.argv[2], sys.argv[3]
note = sys.argv[4] if len(sys.argv) > 4 else None
p = os.path.join(run, "index.html")
s = open(p, encoding="utf-8").read()
pat = re.compile(r'(title: ' + re.escape(json.dumps(title, ensure_ascii=False)) + r', status: )"(?:ok|warn|wip)",(\s*\n\s*note: "(?:[^"\\]|\\.)*",)?')
if not pat.search(s):
    sys.exit("title not found in index.html: " + title)
s = pat.sub(lambda m: m.group(1) + '"' + status + '",' + ("\n      note: " + json.dumps(note, ensure_ascii=False) + "," if note else ""), s, count=1)
s = re.sub(r'const UPDATED = "[^"]*";', 'const UPDATED = "' + time.strftime("%-I:%M %p, %B %-d") + '";', s)
open(p, "w", encoding="utf-8").write(s)
print("set", title, "->", status)
