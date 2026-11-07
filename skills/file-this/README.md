# The /file-this skill

A Claude Code skill for sorting your downloads or "pending" folder. Paste one or more file paths and it opens each one (reads the PDF, looks at the photo, checks the dates), finds the folder it belongs in, and recommends a name that matches the files already there. It moves nothing until you say "do it".

## Install

1. Copy the `file-this` folder to `~/.claude/skills/file-this/`.
2. Open `SKILL.md` and fill in the "Setup" table: your inbox folder, the root of your filing system, its main areas, your default naming, and any folders to leave alone.
3. Optional: replace the example line in `places.md`, or leave it; the skill adds a line each time a filing shows where a kind of thing goes.

`pdftotext` (from poppler, `brew install poppler`) lets it read PDFs. On a Mac it uses `sips` to shrink large photos before looking at them.

## Run it

Type `/file-this` and paste or drag in the paths, or paste a path and ask "where should this go?" It answers with a folder and a name for each item, then waits. Say "do it" (or "yes" to one item) and it moves and renames the file, removes a folder the move emptied, and fixes references to the old path.

## What is in the folder

| File | What it is |
|---|---|
| `SKILL.md` | The skill: setup, rules, steps and how it answers. |
| `places.md` | The homes you've approved for each kind of thing, which the skill reads first and adds to. |

No warranty. Its author uses it to sort a pending folder a few items at a time.
