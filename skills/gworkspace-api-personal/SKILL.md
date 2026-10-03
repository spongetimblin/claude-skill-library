---
name: gworkspace-api-personal
description: >-
  Load context for WRITING to Google Sheets and EDITING Google Docs on your PERSONAL Google
  account (you@example.com) through his token-gated Apps Script web app, and for
  attaching Drive files to events on his personal calendar. Use whenever a task needs to add,
  update or clear cells or rows in a personal sheet, or find-and-replace, replace, insert or
  delete a paragraph in a personal doc, or when tempted to edit one through Claude in Chrome.
  Not needed for read-only
  access; the Google Drive connector reads sheets and docs.
---

# gworkspace-api-personal: Google Sheets and Google Docs write path (personal account)

## When to use this skill

The description in this file's frontmatter is a short version of the text below. It was shortened on 2026-10-03 so that every skill's description fits in Claude's skill list. Nothing was dropped: this is the original description, word for word.

Load context for editing Google Sheets AND Google Docs on your PERSONAL Google account (you@example.com) via a token-gated Apps Script web app (any spreadsheet or document that account can edit), plus attaching Drive files to Calendar events on his personal calendar. Use whenever a task needs to WRITE to a personal-account Google Sheet (add/update/clear cells or rows) or to EDIT the body of a personal-account Google Doc (find-and-replace, replace/insert/delete a paragraph), or when tempted to edit a personal sheet or doc via Claude in Chrome (this path replaces that). Also for attaching files to personal calendar events. Not needed for read-only access (the Google Drive connector reads sheets and docs fine, including comments).

A standalone Apps Script web app deployed from the user's personal account, you@example.com ("Execute as: Me"), exposes a fixed op whitelist over any spreadsheet or Google Doc that account can edit. This is the sanctioned way to edit personal-account Google Sheets and Google Docs; do NOT use Claude in Chrome for sheet or doc edits. The Drive connector can read a Doc but cannot edit its body.

If a sheet or doc lives on a second Google account, deploy a second copy of the script from that account with its own env var names.

## Credentials

Naming note (renamed 2026-09-04 from `gsheets-personal`): the env vars, the Apps Script project name (`gsheets-personal` in the Apps Script project list), the web app URL, the audit spreadsheet name, and the comments inside `Code.gs` keep the historical `gsheets-personal` name on purpose, for the same reasons as the work-account twin: renaming would mean a redeploy and shell-config edits for no functional gain, and `Code.gs` must stay byte-identical to the deployed copy so checksum verification keeps working.

- Env vars `GSHEETS_PERSONAL_API_URL` and `GSHEETS_PERSONAL_API_TOKEN` are set in `~/.zshenv` and available in every Claude Code shell.
- **Never print, echo, log, or store the token's value anywhere** (chat, files, command output). Reference it only via the env var. Never ask the user to paste it.
- If the env vars are empty, the script isn't deployed yet. Point the user to `~/.claude/skills/gworkspace-api-personal/apps-script/SETUP.md` instead of improvising another write path.

## Call pattern

POST JSON; always use `-sL`, and NEVER pass `-X POST`. Apps Script answers with a 302 redirect, and `-X POST` forces POST onto the redirect, which returns Google's "Page Not Found" HTML instead of your result (`-d` alone already makes the first request a POST):

```bash
curl -sL -H 'Content-Type: application/json' \
  -d "{\"token\":\"$GSHEETS_PERSONAL_API_TOKEN\",\"op\":\"ping\"}" "$GSHEETS_PERSONAL_API_URL"
```

For payloads with real content, build the JSON in Python (proper escaping of emoji/quotes) rather than hand-rolling shell strings. Responses are `{"ok":true,"result":{...}}` or `{"ok":false,"error":"..."}`; always check `ok`. Latency is ~1–3s per call.

## Ops

Every sheet op takes `spreadsheet_id` (the long id from the sheet's URL) and, except `list_tabs`, a `sheet` tab name. Exact payloads are documented in `apps-script/Code.gs`.

| op | what it does |
|---|---|
| `ping` | liveness + auth check |
| `list_tabs` | tab names, dimensions, hidden flags |
| `get_headers` | row-1 headers (trimmed) + last data row |
| `read_range` | values for an A1 range (or whole data region); `render`: `display` (default) / `raw` / `formula` |
| `write_range` | overwrite an exact A1 range with a matching 2-D array |
| `append_rows` | append raw rows after the last data row |
| `add_row` | header-keyed append: `values` maps header text → cell; unknown headers error; duplicate guard on cols A/B (`allow_duplicate: true` to force) |
| `set_cell` | one cell, located by `row_match` (`col_a_contains` + optional `col_b_equals`) × `column_header`; refuses ambiguous matches |
| `clear_range` | clear values in an A1 range (formatting untouched) |
| `read_links` | cell text + rich-text hyperlink URLs for an A1 range (UI "Insert link" links, invisible to plain reads) |
| `set_link` | write one cell as text hyperlinked to a URL (rich text, like Insert link in the UI); plain writes to a linked cell strip the link |
| `read_notes` | cell text + each cell's NOTE for an A1 range (the "Insert note" annotation, invisible to plain reads) |
| `set_note` | set one cell's NOTE, leaving its value and formatting alone; empty/null note clears it. NOT threaded comments, which need the Drive API and aren't available here |
| `attach_to_event` | attach a Drive file to a Calendar event (allowlisted calendars only, currently you@example.com); pass `share_with`, since API attachments are not auto-shared |
| `strip_meet` | remove the Google Meet conference from a Calendar event (allowlisted calendars only) |

### Google Docs ops (ported from the work twin 2026-09-04)

Every doc op takes `doc_id` (the long id from the Doc's URL). Elements are addressed by their index among the body's direct children, as returned by `doc_get_text`. Every mutating op except `doc_replace_text` and `doc_set_link` requires a `contains` guard: the target element's current text must contain it, or the op refuses. Re-run `doc_get_text` after any insert or delete, because indices shift.

| op | what it does |
|---|---|
| `doc_get_text` | body children as `{index, type, text}` (text capped at 3000 chars each); optional `contains` filter (case-sensitive) returns only matching elements |
| `doc_replace_text` | literal find-and-replace across the body; keeps the matched run's formatting; `expect_count` refuses the whole op if the occurrence count differs. Best tool for most edits. |
| `doc_replace_paragraph` | replace the full text of the element at `index` (guarded by `contains`); paragraph attributes kept, inline formatting reset |
| `doc_insert_paragraph_after` | insert a new paragraph after the PARAGRAPH at `index` (guarded by `contains`), copying its attributes |
| `doc_delete_paragraph` | remove the element at `index` (guarded by `contains`); old text goes to the audit log |
| `doc_set_text_style` | `copy_style_from: <index>` copies a reference element's text attributes (font, size, colour, bold...) and paragraph attributes (spacing, indents, alignment) onto the element at `index` (guarded by `contains`); explicit `bold`, `italic`, `underline`, `foreground_color`, `font_family`, `font_size` apply afterwards. Always run this after `doc_insert_paragraph_after`, pointing at a plain body paragraph. |
| `doc_set_link` | set the hyperlink (`url`, or `null` to remove) on every literal occurrence of `find`; `expect_count` refuses on a count mismatch |

`doc_get_text` also accepts `with_links: true` (adds a `links` array, `{text, url}`, per element: the only way to see where a URL's text actually points) and `with_style: true` (adds `style: {paragraph, text}` per element, for comparing an edited paragraph against its neighbours).

Docs caveats, learned on the work twin 2026-09-04 and confirmed here on a throwaway test Doc the same day: `doc_replace_text` keeps the hyperlink attribute of the matched run, so replacing a URL's text does not change where it links (check with `with_links`, fix with `doc_set_link`). `doc_insert_paragraph_after` copies attributes imperfectly (on the work account's DPA template the new paragraph came out bold, black, and with default spacing next to navy 10.5pt Arial neighbours; on the personal test Doc it lost the neighbour's spacing and indent attributes); always follow it with `doc_set_text_style` using `copy_style_from` a plain body paragraph, then confirm with `with_style` that the two elements' `style` objects are identical. `copy_style_from` can only copy attributes the reference paragraph has set explicitly; if the neighbour uses document defaults, the text attributes it copies are empty. `with_style` reports only the attributes set explicitly on the element's first character, so an empty `text` style means "no explicit attributes", not "default appearance": on the personal test Doc, a paragraph whose text had been replaced with `doc_replace_paragraph` next to a styled neighbour rendered bold navy Arial 11 in the Docs UI while `with_style` returned `{}` for it. When appearance matters, open the Doc in the browser and check. Paragraphs that look separate in the Drive connector's rendering can be one element with line breaks, so read `doc_get_text` before choosing an insert point. A call occasionally returns a non-JSON Google redirect page even though the write succeeded (seen here on a read right after `doc_set_link`): re-read before retrying, never blindly retry a mutation.

## Rules

1. **Read before you write.** `get_headers` (or `read_range`) first for sheets, `doc_get_text` first for docs; never write to a range or element you haven't looked at this session.
2. **Show the user the proposed write and get his OK** before `write_range`, `clear_range`, or anything that overwrites non-empty cells. `set_cell`/`add_row`/`append_rows` on cells that are empty or expected checklist updates can proceed when the task already authorizes them.
3. **Verify after writing**: re-read the range (or check the op's returned `old_value`/`new_value`) and confirm to the user what changed.
4. Prefer `set_cell`/`add_row` for header-keyed checklist sheets (they validate headers and refuse ambiguity); use `write_range`/`append_rows` for everything else.
5. Formula guard: values starting with `=` are rejected unless you pass `allow_formulas: true`. Only pass it when a formula is genuinely intended (e.g. `HYPERLINK`).
6. Dates: write them as display strings in the sheet's existing format (e.g. `1/25/2027`); Sheets parses them into real dates.
7. Every mutation (sheet or doc) is auto-logged (with old values) to the "Claude Sheets Audit (gsheets-personal)" spreadsheet, which sits with the script in your Drive; mention this if the user worries about an overwrite.
8. Caps: reads ≤ 20,000 cells, writes ≤ 5,000 cells per call; `doc_get_text` output ≤ 200,000 chars (use `contains` to narrow). Split larger jobs.
9. This path can't do everything (no tab creation, formatting, comments, filters for sheets; no tables, images, or partial-run formatting for docs). If a task needs an op that doesn't exist, tell the user and propose adding it to `Code.gs` (he redeploys; URL stays the same). Don't fall back to Claude in Chrome without asking.

## Reading (no write needed)

Use the Google Drive connector (`read_file_content`, which can include comments) for read-only work on sheets and docs when it's connected to the personal account (verified 2026-08-27 and again 2026-09-04 in the user's you@example.com Claude Code environment; check `list_recent_files` or `search_files` owners if unsure, since which account a connector is signed into varies by environment). `read_range` here works for any personal-account sheet regardless, and is handy when you need exact cell coordinates, formulas, or a fresh read immediately after a write; `doc_get_text` when you need element indices or a fresh read after a doc write.

## Related

- First consumer of the Sheets ops: `~/.claude/skills/cat-food-log/` (Cat Food & Weight Log; uses `add_row`, `set_link`, `set_note`).
- Deploy/redeploy/revoke instructions: `apps-script/SETUP.md`.
