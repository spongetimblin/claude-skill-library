#!/usr/bin/env python3
"""List backticked paths in a CLAUDE.md that resolve to nothing in its repo.

Usage: python3 claude-md-paths.py <repo dir> [extra base dir ...]
Run from anywhere. Reads only.
A token is each whitespace-separated word inside a one-line backticked
span, with anything up to a "=" dropped (`FOO=/x cmd a/b.py` gives /x, cmd
and a/b.py). A token counts as a path when it holds a "/" or ends in a code or doc
extension. It is found when it exists under the repo root or one of the
extra base dirs, or when a tracked file ends with it. Routes (/friends),
URL schemes and naming templates show up as "missing" and need a look by hand.
"""
import os, re, subprocess, sys

root = os.path.abspath(sys.argv[1])
bases = [""] + [b.rstrip("/") + "/" for b in sys.argv[2:]]
text = open(os.path.join(root, "CLAUDE.md")).read()
tokens = set(w.rsplit("=", 1)[-1] for span in re.findall(r"`([^`\n]+)`", text) for w in span.split())
ext = r"\.(ts|tsx|mjs|js|sql|md|sh|json|swift|toml|py|kt|xml|plist|gradle|css|yml|yaml)$"
cands = sorted(t for t in tokens if "/" in t or re.search(ext, t))
tracked = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split("\n")
missing = []
for c in cands:
    c = c.rstrip(".,;:)")
    if c.startswith(("http", "~", "$", "@", "--")) or "*" in c or "<" in c:
        continue
    if any(os.path.exists(os.path.join(root, b + c)) for b in bases):
        continue
    if any(f == c or f.endswith("/" + c) for f in tracked):
        continue
    missing.append(c)
print(f"{len(cands)} path-like tokens, {len(missing)} not found:")
print("\n".join(missing))
