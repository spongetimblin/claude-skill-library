# RECORD.md: the record of one surprise run

Every run folder gets a `RECORD.md` at its top level, written at the morning hand-off. It is the lasting record of what that session produced, and it stays in the run folder even after items are updated, moved elsewhere or deleted. `ledger.md` in the Surprises folder is the short list across all runs; this file holds the detail for one run.

Rules for keeping it:

- One section per item, in the order of the morning page. Never remove a section, even when the item has left the folder.
- "Delivered" and "State when delivered" are written once and not edited afterwards. They say what the user woke up to.
- "Where it is now" is always a path that exists, or "deleted" with the date. Update it in the same turn as any move.
- "Since then" gets one dated line per change, oldest first: what was changed, moved or removed, and at whose request.
- "Reaction" uses the user's words where possible, with the date. Until they have looked at it, it says "not yet reviewed".
- Plain writing, no em dashes, straight quotes.

Copy the block below and fill it in.

```markdown
# Record: YYYY.MM.DD <run name>

What this surprise run produced, and what has become of each item since. Written at the morning hand-off and kept current afterwards. The morning page is `index.html` in this folder.

## The run

- **When:** started <date and time>; morning message <date and time>.
- **Asked for:** <the hint the user gave, or "no hint">.
- **Models:** <main thread>; <what the agents ran on, and any switch>.
- **Usage:** 5-hour / weekly all models / weekly top model at the start <x% / y% / z%> and at the end <x% / y% / z%>.
- **Interruptions:** <sleep, limits, failures, or "none">.
- **This folder:** <where it was created, and any move since, with dates>.

## Items

### <Item title, as on the morning page>

- **What it is:** <one or two sentences>
- **Delivered:** `<subfolder/>` (<the main files>), <date>
- **State when delivered:** <finished and checked / finished with a caveat / partly done, and the caveat>
- **Where it is now:** `<path>`
- **Since then:**
  - <date>: <what changed, moved or was removed, and why>
- **Reaction:** not yet reviewed

## Maintenance

<If the run did maintenance: one line per skill run (the maintenance skills named in the Setup section) saying what it changed and what it left for the user, and a pointer to `maintenance/README.md`. Otherwise "none".>

## Supporting files in this folder

<PROGRESS.md, RULES.md, _briefs/, _tools/ and anything else that is not an item, one line each.>
```
