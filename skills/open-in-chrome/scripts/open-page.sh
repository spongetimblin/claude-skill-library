#!/bin/bash
# open-page.sh: open the current project's home page, or a named page, in
# Google Chrome as a local file.
#
# Usage: open-page.sh [--dry-run] [-C <project folder>] [page]
#   page       optional page name or path, with or without .html:
#              "now", "writings/some-article", "prototypes/demo.html"
#   -C         look in this folder instead of the shell's current folder
#   --dry-run  print what would open without opening it
#
# Prints one status line, with any details on the lines after it:
#   OPENED <file>         handed to Chrome (WOULD_OPEN under --dry-run)
#   AMBIGUOUS <why>       several candidates follow, one per line; nothing opened
#   NONE <why>            no HTML file to open
#   NEEDS_SERVER <file>   a generator or bundler builds this project (the file
#                         named is its config); nothing opened
#   ERROR <message>       something failed; exit status 1

set -u

dry=""
start="$PWD"
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) dry=1; shift ;;
    -C)
      [ $# -ge 2 ] || { echo "ERROR -C needs a folder"; exit 1; }
      start="$2"; shift 2 ;;
    *) break ;;
  esac
done
page="${1:-}"
page="${page#./}"

cd "$start" 2>/dev/null || { echo "ERROR cannot open folder: $start"; exit 1; }
start="$PWD"

# Project folder: the top of the Git repo when there is one. --show-cdup gives
# a relative path, so $PWD keeps the path as typed rather than resolving
# symlinks.
cdup="$(git rev-parse --show-cdup 2>/dev/null)"
[ -n "$cdup" ] && cd "$cdup"
root="$PWD"

open_file() {
  local f="${1#./}"
  case "$f" in /*) ;; *) f="$root/$f" ;; esac
  if [ -n "$dry" ]; then echo "WOULD_OPEN $f"; exit 0; fi
  open -a "Google Chrome" "$f" || { echo "ERROR Chrome did not open $f"; exit 1; }
  echo "OPENED $f"
  exit 0
}

count_lines() { printf '%s' "$1" | grep -c .; }

# ----------------------------------------
# 1. A page given as an exact path always opens, from the folder the shell
#    was in or from the project folder.
# ----------------------------------------
if [ -n "$page" ]; then
  for f in "$page" "$page.html" "$page/index.html" \
           "$start/$page" "$start/$page.html" "$start/$page/index.html"; do
    [ -f "$f" ] && open_file "$f"
  done
fi

# ----------------------------------------
# 2. A project built by a generator or bundler does not work as local files,
#    and an index.html in its output folder is a stale build.
# ----------------------------------------
generator=""
for f in hugo.toml hugo.yaml hugo.yml hugo.json config/_default _config.yml \
         vite.config.* astro.config.* next.config.* nuxt.config.* \
         svelte.config.* webpack.config.* eleventy.config.* .eleventy.js; do
  [ -e "$f" ] && { generator="$f"; break; }
done
[ -z "$generator" ] && [ -f config.toml ] && [ -d content ] && generator="config.toml"
if [ -n "$generator" ]; then
  echo "NEEDS_SERVER $generator"
  exit 0
fi

# ----------------------------------------
# 3. Find the site folder: Netlify's publish folder, then the project folder,
#    then the usual output folders, then anything up to three levels down.
# ----------------------------------------
publish="$(sed -n -E 's/^[[:space:]]*publish[[:space:]]*=[[:space:]]*//p' netlify.toml 2>/dev/null \
  | head -1 | sed -E 's/[[:space:]]*(#.*)?$//; s/^["'\'']//; s/["'\'']$//')"
publish="${publish%/}"

site=""
if [ -n "$publish" ] && [ -d "$publish" ]; then
  site="$publish"
elif [ -f index.html ]; then
  site="."
else
  found="$(for d in public dist build _site site docs www out src; do
    [ -f "$d/index.html" ] && echo "$d"
  done)"
  if [ -z "$found" ]; then
    found="$(find . -mindepth 2 -maxdepth 3 -name index.html \
      -not -path '*/node_modules/*' -not -path '*/.*/*' 2>/dev/null \
      | sed -E 's|^\./||; s|/index\.html$||' | sort)"
  fi
  case "$(count_lines "$found")" in
    0) site="." ;;
    1) site="$found" ;;
    *)
      echo "AMBIGUOUS more than one folder has an index.html"
      printf '%s\n' "$found" | sed 's|$|/index.html|'
      exit 0 ;;
  esac
fi

# ----------------------------------------
# 4. A named page: exact path inside the site folder, then a search by name.
# ----------------------------------------
if [ -n "$page" ]; then
  for f in "$site/$page" "$site/$page.html" "$site/$page/index.html"; do
    [ -f "$f" ] && open_file "$f"
  done
  name="${page%.html}"
  matches="$(find "$site" -type f -ipath "*$name*.html" \
    -not -path '*/node_modules/*' -not -path '*/.*/*' 2>/dev/null \
    | sed 's|^\./||' | sort)"
  case "$(count_lines "$matches")" in
    0) echo "NONE no page matching \"$page\" in $root/${site#.}" ;;
    1) open_file "$matches" ;;
    *) echo "AMBIGUOUS more than one page matches \"$page\""; printf '%s\n' "$matches" ;;
  esac
  exit 0
fi

# ----------------------------------------
# 5. No page named: the home page, or the only page there is.
# ----------------------------------------
[ -f "$site/index.html" ] && open_file "$site/index.html"

pages="$(ls -1 "$site"/*.html "$site"/*.htm 2>/dev/null | sed 's|^\./||')"
case "$(count_lines "$pages")" in
  0) echo "NONE no HTML file in $root" ;;
  1) open_file "$pages" ;;
  *) echo "AMBIGUOUS no index.html, and more than one page in the project folder"; printf '%s\n' "$pages" ;;
esac
exit 0
