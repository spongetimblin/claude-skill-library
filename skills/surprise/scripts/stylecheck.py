#!/usr/bin/env python3
"""Counts em dashes and curly quotes in the text files of a folder (skips _checks, data dumps)."""
import os, sys, re
root = sys.argv[1]
bad = {"—": "em dash", "‘": "curly", "’": "curly", "“": "curly", "”": "curly"}
for dp, dn, fns in os.walk(root):
    dn[:] = [d for d in dn if d not in ("_checks", "node_modules", "hevc-test", "original", "app")]
    for fn in fns:
        if not fn.endswith((".html", ".md", ".txt", ".js", ".py", ".json")): continue
        p = os.path.join(dp, fn)
        try: t = open(p, encoding="utf-8").read()
        except Exception: continue
        c = {}
        for ch, name in bad.items():
            n = t.count(ch)
            if n: c[name] = c.get(name, 0) + n
        if c:
            i = min(t.find(ch) for ch in bad if ch in t)
            print(os.path.relpath(p, root), c, "| first:", repr(t[max(0, i - 50):i + 30]))
print("stylecheck done:", root)
