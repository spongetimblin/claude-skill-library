---
name: file-this
description: >-
  Advise where a file or folder should live on the user's computer and what to name it. The
  user pastes one or more local paths, usually from a downloads or "pending" folder, and the
  skill opens each one, finds the folder it belongs in, matches that folder's naming, and
  answers with one recommended place and name. Trigger on /file-this followed by paths, or when
  the user pastes a path and asks where it should go, how to name it, or how to file or
  organize it. Advice only: it moves nothing until the user says so. Not for bulk clean-up
  plans or scripts.
---

# file-this: where a file goes and what to call it

The user sorts their inbox folder themselves. This skill speeds that up: they paste paths, and it recommends a home and a name for each.

## Setup

Fill these in before the first run.

| Setting | Value |
|---|---|
| Inbox folder (where unsorted things wait) | `~/Downloads` (change this) |
| Root of the filing system | `~/Documents` (change this, for example a cloud drive folder) |
| Top-level areas | describe the main folders and what goes in each, for example: `Finances` (taxes, statements), `Health` (one subfolder per person), `Home`, `Projects` |
| Default naming | `YYYY.MM.DD Description` (change this) |
| Folders to leave alone | none (for example a standing folder inside the inbox, or a work drive this skill should not touch) |

## Rules

- **Advice first. Never move, rename or delete anything until the user says so** for that item ("do it", "yes", "move it"). No bulk plans and no scripts for them to run.
- **Open it before naming it.** Look at the image, read the PDF's text, check the dates. Never name a file from its file name alone.
- **The destination decides the name.** Look at the files already in the folder: dated or not, download names kept or not. Use the default naming only when the folder has no pattern.
- **Look a date up; never guess it.** Use the document itself, the photo's own date, the user's calendar or email if connected, or a web search for a public event. Use the date the thing is about, not the download date.
- **One version, no duplicates.** Move, never copy. If the destination already holds a version, say so and ask which to keep. Nothing is deleted: a replaced file goes to the Trash, and you say so.
- **Folder rules outrank this skill.** If the destination, or a folder above it, has a `CLAUDE.md` or README with filing rules, read it first.
- **If the user names a folder** ("it should go somewhere in ..."), stay inside it.
- **Leave the "folders to leave alone" alone.** Advise on something in one only when the user pastes its path.
- Never print a password, key or account number found in a file; say what kind of thing it is.
- No medical, legal or financial advice about what a document says. Describe it only as far as filing needs.

## Steps

1. **Read `places.md`** in this skill's folder: the homes the user has already approved, and how files are named there.
2. **Look at each path.** For a folder, list it and look at what is inside. Shrink a large photo into a scratch folder before reading it (on a Mac, `sips -Z 1600 "<file>" --out "<scratch copy>"`). Read a PDF's text with `pdftotext`. Note what the thing is, whose it is, and the date it is about.
3. **Find the home,** in this order:
   - a line in `places.md`;
   - an existing folder for the same thing. Search by name with `find` under the filing root. Spotlight (`mdfind`) is faster but can return short results, so confirm "no such folder" with `find`;
   - the nearest folder for that kind of thing (see the top-level areas in Setup), with a new subfolder only when nothing fits.
4. **Choose the name** from the files already there. When several files belong together, say what each one shows in its name, not "1 of 2".
5. **Answer, then stop.**
   - One item: the folder and the new name, each on its own line, then one or two short reasons, then an alternative only if there is a real one.
   - Several items: one table (now, move to, rename to), then any notes.
   - Say plainly what you could not tell, such as who a doctor is or which product a photo shows.
6. **When the user says to do it:** check that the destination does not already exist, move with `mv -n`, rename, and list the result. Remove a folder the move emptied with `rmdir`, which fails if anything is left. Search for references to the old path in notes and docs and fix them. Report what moved and what was fixed.
7. **Add a line to `places.md`** when the filing shows where a kind of thing goes. One line each; no line for a one-off.

## What to report

Lead with the recommendation, or with what moved. Keep it short: the user reads these one after another while sorting.
