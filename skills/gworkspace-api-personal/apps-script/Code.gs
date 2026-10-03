/**
 * gsheets-personal — standalone Google Apps Script that gives Claude Code a
 * narrow, token-gated path to:
 *   1. Read and edit ANY Google Sheet your PERSONAL account
 *      (you@example.com) can edit (standalone + "Execute as: Me" means
 *      SpreadsheetApp.openById() reaches everything — no per-sheet setup).
 *   2. Attach Drive files to Google Calendar events (no connector can do this).
 *   3. Read and edit ANY Google Doc your PERSONAL account can edit (doc_* ops): the Drive connector can read
 *      Docs but cannot edit them.
 *
 * Security model:
 *   - Every request must carry the SECRET_TOKEN stored in Script Properties
 *     (never hardcoded here). Requests without it are rejected.
 *   - Ops are a fixed whitelist; there is no arbitrary-code or eval path.
 *   - String values starting with "=" are rejected unless allow_formulas:true,
 *     so a write can never silently plant a formula.
 *   - Reads/writes are size-capped (MAX_CELLS_*) to prevent runaway calls.
 *   - Calendar attachment only works on calendars in ALLOWED_CALENDARS.
 *   - Every mutating call is appended to a dedicated "Claude Sheets Audit"
 *     spreadsheet, auto-created in My Drive on first mutation.
 *
 * Setup: see SETUP.md next to this file.
 * Callers: see the gsheets-personal skill (~/.claude/skills/gworkspace-api-personal/SKILL.md).
 */

const ALLOWED_CALENDARS = [
  'you@example.com',
];

const MAX_CELLS_READ = 20000;
const MAX_CELLS_WRITE = 5000;
const AUDIT_SS_NAME = 'Claude Sheets Audit (gsheets-personal)';
const MAX_DOC_CHARS_READ = 200000;

// ---------------------------------------------------------------------------
// Entry points
// ---------------------------------------------------------------------------

function doGet() {
  // Unauthenticated liveness check only — reveals nothing and changes nothing.
  return ContentService.createTextOutput('gsheets-api alive');
}

function doPost(e) {
  let req;
  try {
    req = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, error: 'invalid JSON body' });
  }

  const token = PropertiesService.getScriptProperties().getProperty('SECRET_TOKEN');
  if (!token || req.token !== token) {
    return json_({ ok: false, error: 'unauthorized' });
  }

  try {
    let result;
    switch (req.op) {
      case 'ping':            result = { pong: true, time: new Date().toISOString() }; break;
      case 'list_tabs':       result = listTabs_(req); break;
      case 'get_headers':     result = getHeaders_(req); break;
      case 'read_range':      result = readRange_(req); break;
      case 'write_range':     result = writeRange_(req); break;
      case 'append_rows':     result = appendRows_(req); break;
      case 'add_row':         result = addRow_(req); break;
      case 'set_cell':        result = setCell_(req); break;
      case 'clear_range':     result = clearRange_(req); break;
      case 'read_links':      result = readLinks_(req); break;
      case 'set_link':        result = setLink_(req); break;
      case 'read_notes':      result = readNotes_(req); break;
      case 'set_note':        result = setNote_(req); break;
      case 'attach_to_event': result = attachToEvent_(req); break;
      case 'strip_meet':      result = stripMeet_(req); break;
      case 'doc_get_text':               result = docGetText_(req); break;
      case 'doc_replace_text':           result = docReplaceText_(req); break;
      case 'doc_replace_paragraph':      result = docReplaceParagraph_(req); break;
      case 'doc_insert_paragraph_after': result = docInsertParagraphAfter_(req); break;
      case 'doc_delete_paragraph':       result = docDeleteParagraph_(req); break;
      case 'doc_set_text_style':         result = docSetTextStyle_(req); break;
      case 'doc_set_link':               result = docSetLink_(req); break;
      default:
        return json_({ ok: false, error: 'unknown op: ' + req.op });
    }
    return json_({ ok: true, result: result });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

// ---------------------------------------------------------------------------
// Read ops
// ---------------------------------------------------------------------------

/**
 * list_tabs — { spreadsheet_id }
 * Returns every tab's name, dimensions, and hidden flag.
 */
function listTabs_(req) {
  const ss = getSs_(req);
  return {
    spreadsheet: ss.getName(),
    tabs: ss.getSheets().map(function (s) {
      return { name: s.getName(), rows: s.getLastRow(), cols: s.getLastColumn(), hidden: s.isSheetHidden() };
    }),
  };
}

/**
 * get_headers — { spreadsheet_id, sheet }
 * Returns row 1 as trimmed header texts plus the last data row, so callers can
 * validate column names before writing.
 */
function getHeaders_(req) {
  const sheet = getSheet_(req);
  const lastCol = Math.max(sheet.getLastColumn(), 1);
  const headers = sheet.getRange(1, 1, 1, lastCol).getDisplayValues()[0].map(function (h) { return String(h).trim(); });
  return { spreadsheet: sheet.getParent().getName(), sheet: sheet.getName(), headers: headers, last_row: sheet.getLastRow() };
}

/**
 * read_range — { spreadsheet_id, sheet, range?, render? }
 * range: A1 notation (e.g. "A1:E20"). Omit to read the whole data region.
 * render: "display" (default, what a user sees), "raw" (underlying values),
 *         or "formula" (formulas where present, else values).
 */
function readRange_(req) {
  const sheet = getSheet_(req);
  const range = req.range ? sheet.getRange(String(req.range)) : sheet.getDataRange();
  if (range.getNumRows() * range.getNumColumns() > MAX_CELLS_READ) {
    throw new Error('range exceeds ' + MAX_CELLS_READ + ' cells — read a narrower range');
  }
  let values;
  if (req.render === 'raw') values = range.getValues();
  else if (req.render === 'formula') {
    values = range.getValues();
    const formulas = range.getFormulas();
    formulas.forEach(function (row, r) { row.forEach(function (f, c) { if (f) values[r][c] = f; }); });
  } else values = range.getDisplayValues();
  return { sheet: sheet.getName(), range: range.getA1Notation(), values: values };
}

// ---------------------------------------------------------------------------
// Write ops
// ---------------------------------------------------------------------------

/**
 * write_range — { spreadsheet_id, sheet, range, values, allow_formulas? }
 * values: 2-D array whose dimensions must exactly match the A1 range.
 * Overwrites in place; old display values go to the audit log.
 */
function writeRange_(req) {
  const sheet = getSheet_(req);
  if (!req.range) throw new Error('range (A1 notation) is required');
  const values = req.values;
  if (!Array.isArray(values) || !values.length || !Array.isArray(values[0])) {
    throw new Error('values must be a 2-D array, e.g. [["a","b"],["c","d"]]');
  }
  const range = sheet.getRange(String(req.range));
  if (range.getNumRows() !== values.length || range.getNumColumns() !== values[0].length) {
    throw new Error('values are ' + values.length + 'x' + values[0].length +
      ' but range ' + range.getA1Notation() + ' is ' + range.getNumRows() + 'x' + range.getNumColumns());
  }
  capCells_(values, MAX_CELLS_WRITE);
  guardFormulas_(values, req.allow_formulas);

  const oldValues = range.getDisplayValues();
  range.setValues(values);

  audit_('write_range', {
    spreadsheet: sheet.getParent().getName(), spreadsheet_id: req.spreadsheet_id,
    sheet: sheet.getName(), range: range.getA1Notation(),
    old_values: truncate_(oldValues), new_values: truncate_(values),
  });
  return { sheet: sheet.getName(), range: range.getA1Notation(), cells_written: values.length * values[0].length };
}

/**
 * append_rows — { spreadsheet_id, sheet, values, allow_formulas? }
 * values: 2-D array of new rows (ragged rows are padded with ""). Appended
 * starting at the first row after the current last data row.
 */
function appendRows_(req) {
  const sheet = getSheet_(req);
  const values = req.values;
  if (!Array.isArray(values) || !values.length || !Array.isArray(values[0])) {
    throw new Error('values must be a 2-D array of rows');
  }
  const width = Math.max.apply(null, values.map(function (r) { return r.length; }));
  const padded = values.map(function (r) { return r.concat(new Array(width - r.length).fill('')); });
  capCells_(padded, MAX_CELLS_WRITE);
  guardFormulas_(padded, req.allow_formulas);

  const startRow = sheet.getLastRow() + 1;
  sheet.getRange(startRow, 1, padded.length, width).setValues(padded);

  audit_('append_rows', {
    spreadsheet: sheet.getParent().getName(), spreadsheet_id: req.spreadsheet_id,
    sheet: sheet.getName(), start_row: startRow, rows: padded.length, values: truncate_(padded),
  });
  return { sheet: sheet.getName(), start_row: startRow, rows_appended: padded.length };
}

/**
 * add_row — {
 *   spreadsheet_id, sheet,
 *   values: { "Header text": "cell value", ... },   // keys must match row-1 headers exactly (after trimming)
 *   allow_duplicate?: false
 * }
 * Header-keyed append for checklist-style sheets: unknown headers are an error
 * (typos never land in the wrong column), and unless allow_duplicate is true it
 * refuses when column A (+ column B when supplied) already matches an existing row.
 */
function addRow_(req) {
  const sheet = getSheet_(req);
  const lastCol = sheet.getLastColumn();
  const headers = sheet.getRange(1, 1, 1, lastCol).getDisplayValues()[0].map(function (h) { return String(h).trim(); });

  const rowValues = new Array(lastCol).fill('');
  Object.keys(req.values || {}).forEach(function (key) {
    const idx = headers.indexOf(String(key).trim());
    if (idx === -1) throw new Error('unknown column header: "' + key + '"');
    rowValues[idx] = req.values[key];
  });
  guardFormulas_([rowValues], req.allow_formulas);

  const first = String(rowValues[0] || '').trim();
  if (!first) throw new Error('a value for the first column is required');
  if (!req.allow_duplicate && sheet.getLastRow() > 1) {
    const existing = sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getDisplayValues();
    existing.forEach(function (r) {
      if (String(r[0]).trim().toLowerCase() === first.toLowerCase() &&
          (!rowValues[1] || String(r[1]).trim() === String(rowValues[1]).trim())) {
        throw new Error('a matching row appears to exist already — pass allow_duplicate: true to force');
      }
    });
  }

  const newRow = sheet.getLastRow() + 1;
  sheet.getRange(newRow, 1, 1, lastCol).setValues([rowValues]);

  audit_('add_row', {
    spreadsheet: sheet.getParent().getName(), spreadsheet_id: req.spreadsheet_id,
    sheet: sheet.getName(), row: newRow, values: req.values,
  });
  return { row: newRow };
}

/**
 * set_cell — {
 *   spreadsheet_id, sheet,
 *   row_match: { col_a_contains: "Row label", col_b_equals: "9/25/2026" },  // col_b_equals optional
 *   column_header: "Status",
 *   value: "Yes"
 * }
 * Locates exactly ONE data row by case-insensitive substring match on column A
 * (and, when given, exact display match on column B), then writes one cell in
 * the column whose row-1 header matches column_header exactly. Refuses on zero
 * or multiple matches.
 */
function setCell_(req) {
  const sheet = getSheet_(req);
  const col = findColumn_(sheet, req.column_header);
  const row = findRow_(sheet, req.row_match);
  guardFormulas_([[req.value]], req.allow_formulas);

  const cell = sheet.getRange(row, col);
  const oldValue = cell.getDisplayValue();
  cell.setValue(req.value);

  audit_('set_cell', {
    spreadsheet: sheet.getParent().getName(), spreadsheet_id: req.spreadsheet_id,
    sheet: sheet.getName(), row: row, column_header: req.column_header,
    old_value: oldValue, new_value: req.value, row_match: req.row_match,
  });
  return { row: row, column_header: req.column_header, old_value: oldValue, new_value: req.value };
}

/**
 * clear_range — { spreadsheet_id, sheet, range }
 * Clears values (not formatting). Old display values go to the audit log.
 */
function clearRange_(req) {
  const sheet = getSheet_(req);
  if (!req.range) throw new Error('range (A1 notation) is required');
  const range = sheet.getRange(String(req.range));
  if (range.getNumRows() * range.getNumColumns() > MAX_CELLS_WRITE) {
    throw new Error('range exceeds ' + MAX_CELLS_WRITE + ' cells — clear a narrower range');
  }
  const oldValues = range.getDisplayValues();
  range.clearContent();

  audit_('clear_range', {
    spreadsheet: sheet.getParent().getName(), spreadsheet_id: req.spreadsheet_id,
    sheet: sheet.getName(), range: range.getA1Notation(), old_values: truncate_(oldValues),
  });
  return { sheet: sheet.getName(), range: range.getA1Notation(), cells_cleared: range.getNumRows() * range.getNumColumns() };
}

/**
 * read_links — { spreadsheet_id, sheet, range }
 * Returns each cell's text plus any rich-text hyperlink (the kind added via
 * the Sheets UI "Insert link", which plain value reads can't see). `link` is
 * the whole-cell link or null; `runs` appears only when a cell has multiple
 * differently-linked text runs.
 */
function readLinks_(req) {
  const sheet = getSheet_(req);
  if (!req.range) throw new Error('range (A1 notation) is required');
  const range = sheet.getRange(String(req.range));
  if (range.getNumRows() * range.getNumColumns() > MAX_CELLS_READ) {
    throw new Error('range exceeds ' + MAX_CELLS_READ + ' cells — read a narrower range');
  }
  const cells = range.getRichTextValues().map(function (row) {
    return row.map(function (rtv) {
      const cell = { text: rtv.getText(), link: rtv.getLinkUrl() };
      if (!cell.link) {
        const runs = rtv.getRuns()
          .map(function (r) { return { text: r.getText(), link: r.getLinkUrl() }; })
          .filter(function (r) { return r.link; });
        if (runs.length) cell.runs = runs;
      }
      return cell;
    });
  });
  return { sheet: sheet.getName(), range: range.getA1Notation(), cells: cells };
}

/**
 * set_link — { spreadsheet_id, sheet, cell, text, url }
 * Writes one cell as rich text whose full text is hyperlinked to url
 * (equivalent to typing the text and using Insert link in the UI).
 */
function setLink_(req) {
  const sheet = getSheet_(req);
  if (!req.cell) throw new Error('cell (A1 notation) is required');
  if (!req.text || !req.url) throw new Error('text and url are required');
  if (!/^https?:\/\//.test(String(req.url))) throw new Error('url must start with http:// or https://');
  const range = sheet.getRange(String(req.cell));
  if (range.getNumRows() !== 1 || range.getNumColumns() !== 1) {
    throw new Error('cell must be a single cell, e.g. "F305"');
  }
  const oldValue = range.getDisplayValue();
  range.setRichTextValue(
    SpreadsheetApp.newRichTextValue().setText(String(req.text)).setLinkUrl(String(req.url)).build()
  );

  audit_('set_link', {
    spreadsheet: sheet.getParent().getName(), spreadsheet_id: req.spreadsheet_id,
    sheet: sheet.getName(), cell: range.getA1Notation(),
    old_value: oldValue, text: req.text, url: req.url,
  });
  return { cell: range.getA1Notation(), old_value: oldValue, text: req.text, url: req.url };
}

/**
 * read_notes — { spreadsheet_id, sheet, range }
 * Returns each cell's display text plus its NOTE (the yellow-corner annotation
 * from "Insert note" — a different feature from threaded comments, and invisible
 * to plain value reads). `note` is the note text, or null when the cell has none.
 * Threaded comments are NOT readable here; nothing in the Sheets service exposes them.
 */
function readNotes_(req) {
  const sheet = getSheet_(req);
  if (!req.range) throw new Error('range (A1 notation) is required');
  const range = sheet.getRange(String(req.range));
  if (range.getNumRows() * range.getNumColumns() > MAX_CELLS_READ) {
    throw new Error('range exceeds ' + MAX_CELLS_READ + ' cells — read a narrower range');
  }
  const texts = range.getDisplayValues();
  const notes = range.getNotes();
  const cells = notes.map(function (row, r) {
    return row.map(function (n, c) {
      return { text: texts[r][c], note: n ? n : null };
    });
  });
  return { sheet: sheet.getName(), range: range.getA1Notation(), cells: cells };
}

/**
 * set_note — { spreadsheet_id, sheet, cell, note }
 * Sets one cell's NOTE (the "Insert note" annotation), leaving the cell's value
 * and formatting untouched. Pass an empty string or null to clear an existing note.
 * This does NOT create a threaded comment — those need the Drive API and are not
 * available through this script.
 */
function setNote_(req) {
  const sheet = getSheet_(req);
  if (!req.cell) throw new Error('cell (A1 notation) is required');
  const range = sheet.getRange(String(req.cell));
  if (range.getNumRows() !== 1 || range.getNumColumns() !== 1) {
    throw new Error('cell must be a single cell, e.g. "M313"');
  }
  const note = (req.note === null || req.note === undefined) ? '' : String(req.note);
  if (note.length > 5000) throw new Error('note exceeds 5000 characters');

  const oldNote = range.getNote();
  range.setNote(note);

  audit_('set_note', {
    spreadsheet: sheet.getParent().getName(), spreadsheet_id: req.spreadsheet_id,
    sheet: sheet.getName(), cell: range.getA1Notation(),
    old_note: String(oldNote).slice(0, 500), new_note: note.slice(0, 500),
  });
  return {
    cell: range.getA1Notation(),
    old_note: oldNote ? oldNote : null,
    new_note: note ? note : null,
    cleared: !note,
  };
}

// ---------------------------------------------------------------------------
// Calendar op
// ---------------------------------------------------------------------------

/**
 * attach_to_event — {
 *   calendar_id: "you@example.com",
 *   event_id: "abc123...",            // plain event id (no @google.com suffix needed)
 *   file_id: "1AbC...",               // Drive file id
 *   title: "optional display title",  // defaults to the Drive file's name
 *   share_with: ["someone@example.com"]  // optional viewers
 * }
 * Appends a Drive-file attachment to an existing Calendar event, preserving any
 * attachments already on it. Requires the Calendar advanced service (SETUP.md).
 * Files attached via API are NOT auto-shared, so pass share_with for anyone who
 * must open them.
 */
function attachToEvent_(req) {
  if (ALLOWED_CALENDARS.indexOf(req.calendar_id) === -1) {
    throw new Error('calendar not in allowlist: ' + req.calendar_id);
  }
  const file = DriveApp.getFileById(req.file_id);

  (req.share_with || []).forEach(function (email) {
    file.addViewer(email);
  });

  const event = Calendar.Events.get(req.calendar_id, req.event_id);
  const attachments = event.attachments || [];
  const fileUrl = 'https://drive.google.com/open?id=' + req.file_id;
  if (attachments.some(function (a) { return a.fileUrl === fileUrl; })) {
    return { event_id: req.event_id, already_attached: true, attachment_count: attachments.length };
  }
  attachments.push({
    fileUrl: fileUrl,
    title: req.title || file.getName(),
    mimeType: file.getMimeType(),
  });

  Calendar.Events.patch({ attachments: attachments }, req.calendar_id, req.event_id, { supportsAttachments: true });

  audit_('attach_to_event', {
    calendar_id: req.calendar_id, event_id: req.event_id,
    file: file.getName(), file_id: req.file_id, shared_with: req.share_with || [],
  });
  return { event_id: req.event_id, attached: file.getName(), attachment_count: attachments.length };
}

/**
 * strip_meet — { calendar_id, event_id }
 * Removes the Google Meet conference from an existing event (the Calendar
 * connector auto-adds Meet links on creation and cannot remove them). Uses a
 * full Events.update with conferenceData omitted + conferenceDataVersion 1,
 * which is the reliable removal path. Allowlisted calendars only.
 */
function stripMeet_(req) {
  if (ALLOWED_CALENDARS.indexOf(req.calendar_id) === -1) {
    throw new Error('calendar not in allowlist: ' + req.calendar_id);
  }
  const event = Calendar.Events.get(req.calendar_id, req.event_id);
  if (!event.conferenceData) {
    return { event_id: req.event_id, had_meet: false };
  }
  delete event.conferenceData;
  Calendar.Events.update(event, req.calendar_id, req.event_id, { conferenceDataVersion: 1 });

  audit_('strip_meet', { calendar_id: req.calendar_id, event_id: req.event_id, summary: event.summary || '' });
  return { event_id: req.event_id, had_meet: true, removed: true };
}

// ---------------------------------------------------------------------------
// Google Docs ops (DocumentApp). Elements are addressed by their index among
// the document body's direct children (see doc_get_text). Every mutating op
// requires a `contains` guard: the target element's current text must contain
// it, so a stale index can never edit the wrong paragraph.
// ---------------------------------------------------------------------------

/**
 * doc_get_text — { doc_id, contains?, with_links?, with_style? }
 * Returns the body's direct children as { index, type, text }. type is the
 * element type (PARAGRAPH, LIST_ITEM, TABLE, ...); text is the element's text,
 * truncated to 3000 chars per element. Pass `contains` (case-sensitive
 * substring) to return only matching elements. with_links: true adds a `links`
 * array per element: { text, url } for every hyperlinked run. with_style: true
 * adds a `style` object: the element's paragraph attributes plus the text
 * attributes of its first character (font, size, colour, bold...). Total output
 * capped at MAX_DOC_CHARS_READ.
 */
function docGetText_(req) {
  const doc = getDoc_(req);
  const body = doc.getBody();
  const n = body.getNumChildren();
  const needle = req.contains ? String(req.contains) : null;
  const out = [];
  let total = 0;
  for (let i = 0; i < n; i++) {
    const child = body.getChild(i);
    const text = elementText_(child);
    if (needle && text.indexOf(needle) === -1) continue;
    const t = text.slice(0, 3000);
    total += t.length;
    if (total > MAX_DOC_CHARS_READ) throw new Error('document text exceeds ' + MAX_DOC_CHARS_READ + ' chars — use `contains` to narrow');
    const item = { index: i, type: String(child.getType()), text: t };
    if (req.with_links) item.links = elementLinks_(child);
    if (req.with_style) item.style = elementStyle_(child);
    out.push(item);
  }
  return { title: doc.getName(), doc_id: doc.getId(), num_children: n, elements: out };
}

/**
 * doc_replace_text — { doc_id, find, replace, expect_count? }
 * Literal (not regex) find-and-replace across the whole body. Formatting of
 * the matched run is preserved. Counts occurrences first; if expect_count is
 * given and differs, refuses without changing anything. Returns the count.
 */
function docReplaceText_(req) {
  const doc = getDoc_(req);
  if (!req.find) throw new Error('find is required');
  if (typeof req.replace !== 'string') throw new Error('replace (string) is required');
  const body = doc.getBody();
  const pattern = escapeRegex_(String(req.find));
  let count = 0;
  let r = body.findText(pattern);
  while (r) { count++; r = body.findText(pattern, r); }
  if (count === 0) throw new Error('find text not present in document');
  if (req.expect_count !== undefined && req.expect_count !== null && Number(req.expect_count) !== count) {
    throw new Error('found ' + count + ' occurrence(s) but expect_count is ' + req.expect_count + ' — nothing changed');
  }
  body.replaceText(pattern, String(req.replace));
  audit_('doc_replace_text', { doc: doc.getName(), doc_id: doc.getId(), find: String(req.find).slice(0, 500), replace: String(req.replace).slice(0, 500), count: count });
  return { doc: doc.getName(), replaced: count };
}

/**
 * doc_replace_paragraph — { doc_id, index, contains, text }
 * Replaces the full text of the paragraph/list item at body-child `index`,
 * keeping its paragraph attributes (heading, alignment, spacing). Refuses
 * unless the element's current text contains `contains`.
 */
function docReplaceParagraph_(req) {
  const doc = getDoc_(req);
  const el = getGuardedChild_(doc, req);
  if (typeof req.text !== 'string') throw new Error('text (string) is required');
  const oldText = elementText_(el);
  el.asText().setText(req.text);
  audit_('doc_replace_paragraph', { doc: doc.getName(), doc_id: doc.getId(), index: Number(req.index), old_text: oldText.slice(0, 2000), new_text: req.text.slice(0, 2000) });
  return { doc: doc.getName(), index: Number(req.index), old_text: oldText, new_text: req.text };
}

/**
 * doc_insert_paragraph_after — { doc_id, index, contains, text }
 * Inserts a new paragraph immediately after the body child at `index`
 * (guarded by `contains`), copying that element's attributes so the new
 * paragraph matches its neighbour's formatting. Reference must be a PARAGRAPH.
 */
function docInsertParagraphAfter_(req) {
  const doc = getDoc_(req);
  const ref = getGuardedChild_(doc, req);
  if (String(ref.getType()) !== 'PARAGRAPH') throw new Error('reference element is ' + ref.getType() + ', not PARAGRAPH — pick a plain paragraph to insert after');
  if (typeof req.text !== 'string' || !req.text) throw new Error('text (non-empty string) is required');
  const body = doc.getBody();
  const at = Number(req.index) + 1;
  const p = body.insertParagraph(at, req.text);
  try { p.setAttributes(ref.getAttributes()); } catch (err) { /* keep default formatting if copy fails */ }
  audit_('doc_insert_paragraph_after', { doc: doc.getName(), doc_id: doc.getId(), after_index: Number(req.index), after_text: elementText_(ref).slice(0, 300), new_index: at, text: req.text.slice(0, 2000) });
  return { doc: doc.getName(), new_index: at, text: req.text };
}

/**
 * doc_delete_paragraph — { doc_id, index, contains }
 * Removes the body child at `index` (guarded by `contains`). Old text goes to
 * the audit log. Refuses to remove the body's only child.
 */
function docDeleteParagraph_(req) {
  const doc = getDoc_(req);
  const el = getGuardedChild_(doc, req);
  if (doc.getBody().getNumChildren() < 2) throw new Error('refusing to remove the only element in the body');
  const oldText = elementText_(el);
  el.removeFromParent();
  audit_('doc_delete_paragraph', { doc: doc.getName(), doc_id: doc.getId(), index: Number(req.index), old_text: oldText.slice(0, 2000) });
  return { doc: doc.getName(), removed_index: Number(req.index), old_text: oldText };
}

/**
 * doc_set_text_style — { doc_id, index, contains, copy_style_from?, bold?, italic?, underline?, foreground_color?, font_family?, font_size? }
 * copy_style_from: body-child index of a reference element whose paragraph
 * attributes and first-character text attributes are copied onto the target
 * (the reliable way to make an inserted paragraph match its neighbours).
 * The explicit flags are applied after the copy, across the element's whole
 * text. Omitted ones are untouched. Target is `index`, guarded by `contains`.
 */
function docSetTextStyle_(req) {
  const doc = getDoc_(req);
  const el = getGuardedChild_(doc, req);
  const t = el.asText();
  const applied = {};
  if (req.copy_style_from !== undefined && req.copy_style_from !== null) {
    const body = doc.getBody();
    const ri = Number(req.copy_style_from);
    if (isNaN(ri) || ri < 0 || ri >= body.getNumChildren()) throw new Error('copy_style_from index out of range');
    const ref = body.getChild(ri);
    const style = elementStyle_(ref);
    // Paragraph attributes go through explicit setters: setAttributes() silently
    // drops enum-valued keys (alignment, heading) and the numeric ones with them.
    // setHeading() also wipes inline text formatting, so it only runs when the
    // heading differs, and the text attributes are applied AFTER this block.
    try {
      const rp = ref.asParagraph ? ref.asParagraph() : ref;
      const tp = el.asParagraph ? el.asParagraph() : el;
      if (rp.getHeading && tp.setHeading && rp.getHeading() && String(rp.getHeading()) !== String(tp.getHeading())) tp.setHeading(rp.getHeading());
      if (rp.getAlignment && tp.setAlignment && rp.getAlignment()) tp.setAlignment(rp.getAlignment());
      if (rp.getLineSpacing && tp.setLineSpacing && rp.getLineSpacing() !== null) tp.setLineSpacing(rp.getLineSpacing());
      if (rp.getSpacingBefore && tp.setSpacingBefore && rp.getSpacingBefore() !== null) tp.setSpacingBefore(rp.getSpacingBefore());
      if (rp.getSpacingAfter && tp.setSpacingAfter && rp.getSpacingAfter() !== null) tp.setSpacingAfter(rp.getSpacingAfter());
      if (rp.getIndentStart && tp.setIndentStart && rp.getIndentStart() !== null) tp.setIndentStart(rp.getIndentStart());
      if (rp.getIndentEnd && tp.setIndentEnd && rp.getIndentEnd() !== null) tp.setIndentEnd(rp.getIndentEnd());
      if (rp.getIndentFirstLine && tp.setIndentFirstLine && rp.getIndentFirstLine() !== null) tp.setIndentFirstLine(rp.getIndentFirstLine());
    } catch (err) { applied.paragraph_copy_error = String(err && err.message ? err.message : err); }
    if (Object.keys(style.text).length) t.setAttributes(style.text);
    applied.copied_from = ri;
  }
  if (typeof req.bold === 'boolean')      { t.setBold(req.bold);           applied.bold = req.bold; }
  if (typeof req.italic === 'boolean')    { t.setItalic(req.italic);       applied.italic = req.italic; }
  if (typeof req.underline === 'boolean') { t.setUnderline(req.underline); applied.underline = req.underline; }
  if (typeof req.foreground_color === 'string') { t.setForegroundColor(req.foreground_color); applied.foreground_color = req.foreground_color; }
  if (typeof req.font_family === 'string')      { t.setFontFamily(req.font_family);           applied.font_family = req.font_family; }
  if (typeof req.font_size === 'number')        { t.setFontSize(req.font_size);               applied.font_size = req.font_size; }
  if (!Object.keys(applied).length) throw new Error('pass copy_style_from or at least one of bold, italic, underline, foreground_color, font_family, font_size');
  audit_('doc_set_text_style', { doc: doc.getName(), doc_id: doc.getId(), index: Number(req.index), text: elementText_(el).slice(0, 300), applied: applied });
  return { doc: doc.getName(), index: Number(req.index), applied: applied };
}

/**
 * doc_set_link — { doc_id, find, url, expect_count? }
 * Sets (or, with url: null, removes) the hyperlink on every literal occurrence
 * of `find` in the body. expect_count refuses if the occurrence count differs.
 */
function docSetLink_(req) {
  const doc = getDoc_(req);
  if (!req.find) throw new Error('find is required');
  if (req.url !== null && typeof req.url !== 'string') throw new Error('url (string, or null to remove the link) is required');
  const body = doc.getBody();
  const pattern = escapeRegex_(String(req.find));
  const hits = [];
  let r = body.findText(pattern);
  while (r) { hits.push(r); r = body.findText(pattern, r); }
  if (!hits.length) throw new Error('find text not present in document');
  if (req.expect_count !== undefined && req.expect_count !== null && Number(req.expect_count) !== hits.length) {
    throw new Error('found ' + hits.length + ' occurrence(s) but expect_count is ' + req.expect_count + ' — nothing changed');
  }
  const before = [];
  hits.forEach(function (h) {
    const t = h.getElement().asText();
    const a = h.getStartOffset(), b = h.getEndOffsetInclusive();
    before.push(t.getLinkUrl(a));
    t.setLinkUrl(a, b, req.url);
  });
  audit_('doc_set_link', { doc: doc.getName(), doc_id: doc.getId(), find: String(req.find).slice(0, 300), old_urls: before, new_url: req.url, count: hits.length });
  return { doc: doc.getName(), updated: hits.length, old_urls: before, new_url: req.url };
}

const PARA_ATTRS = ['HEADING', 'HORIZONTAL_ALIGNMENT', 'LINE_SPACING', 'SPACING_BEFORE', 'SPACING_AFTER', 'INDENT_START', 'INDENT_END', 'INDENT_FIRST_LINE'];
const TEXT_ATTRS = ['FONT_FAMILY', 'FONT_SIZE', 'FOREGROUND_COLOR', 'BACKGROUND_COLOR', 'BOLD', 'ITALIC', 'UNDERLINE', 'STRIKETHROUGH'];

function elementStyle_(el) {
  const out = { paragraph: {}, text: {} };
  let pa = {};
  try { pa = el.getAttributes() || {}; } catch (err) { pa = {}; }
  PARA_ATTRS.forEach(function (k) { if (pa[k] !== null && pa[k] !== undefined) out.paragraph[k] = pa[k]; });
  try {
    const t = el.asText();
    if (t.getText()) {
      const ta = t.getAttributes(0) || {};
      TEXT_ATTRS.forEach(function (k) { if (ta[k] !== null && ta[k] !== undefined) out.text[k] = ta[k]; });
    }
  } catch (err) { /* not a text element */ }
  return out;
}

function elementLinks_(el) {
  const links = [];
  let t;
  try { t = el.asText(); } catch (err) { return links; }
  const text = t.getText();
  if (!text) return links;
  const idx = t.getTextAttributeIndices();
  for (let k = 0; k < idx.length; k++) {
    const start = idx[k];
    const end = (k + 1 < idx.length ? idx[k + 1] : text.length) - 1;
    const url = t.getLinkUrl(start);
    if (url) links.push({ text: text.slice(start, end + 1), url: url });
  }
  return links;
}

function getDoc_(req) {
  if (!req.doc_id) throw new Error('doc_id is required');
  try {
    return DocumentApp.openById(String(req.doc_id));
  } catch (err) {
    throw new Error('cannot open document ' + req.doc_id + ' — check the id and that this account can edit it');
  }
}

function getGuardedChild_(doc, req) {
  if (req.index === undefined || req.index === null || isNaN(Number(req.index))) throw new Error('index (body child index from doc_get_text) is required');
  if (!req.contains) throw new Error('contains (substring of the target element\'s current text) is required as a safety guard');
  const body = doc.getBody();
  const i = Number(req.index);
  if (i < 0 || i >= body.getNumChildren()) throw new Error('index ' + i + ' out of range (body has ' + body.getNumChildren() + ' children)');
  const el = body.getChild(i);
  const text = elementText_(el);
  if (text.indexOf(String(req.contains)) === -1) {
    throw new Error('element ' + i + ' does not contain "' + req.contains + '" — re-run doc_get_text, indices may have shifted. Current text starts: "' + text.slice(0, 120) + '"');
  }
  return el;
}

function elementText_(el) {
  try { return el.asText().getText(); } catch (err) { /* not a text-bearing element */ }
  try { return el.getText(); } catch (err) { return ''; }
}

function escapeRegex_(s) {
  return s.replace(/[.*+?^${}()|[\]\\\/-]/g, '\\$&');
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getSs_(req) {
  if (!req.spreadsheet_id) throw new Error('spreadsheet_id is required');
  try {
    return SpreadsheetApp.openById(String(req.spreadsheet_id));
  } catch (err) {
    throw new Error('cannot open spreadsheet ' + req.spreadsheet_id + ' — check the id and that this account can access it');
  }
}

function getSheet_(req) {
  const ss = getSs_(req);
  if (!req.sheet) throw new Error('sheet (tab name) is required, e.g. "2026"');
  const sheet = ss.getSheetByName(String(req.sheet));
  if (!sheet) {
    throw new Error('no tab named "' + req.sheet + '" in "' + ss.getName() + '" — tabs: ' +
      ss.getSheets().map(function (s) { return s.getName(); }).join(', '));
  }
  return sheet;
}

function findColumn_(sheet, header) {
  if (!header) throw new Error('column_header is required');
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getDisplayValues()[0];
  const wanted = String(header).trim();
  const matches = [];
  headers.forEach(function (h, i) {
    if (String(h).trim() === wanted) matches.push(i + 1);
  });
  if (matches.length === 0) throw new Error('no column with header "' + wanted + '"');
  if (matches.length > 1) throw new Error('multiple columns share header "' + wanted + '"');
  return matches[0];
}

function findRow_(sheet, rowMatch) {
  if (!rowMatch || !rowMatch.col_a_contains) {
    throw new Error('row_match.col_a_contains is required');
  }
  const needle = String(rowMatch.col_a_contains).trim().toLowerCase();
  const wantB = rowMatch.col_b_equals ? String(rowMatch.col_b_equals).trim() : null;
  const numRows = Math.max(sheet.getLastRow() - 1, 1);
  const data = sheet.getRange(2, 1, numRows, 2).getDisplayValues();

  const matches = [];
  data.forEach(function (r, i) {
    const aOk = String(r[0]).toLowerCase().indexOf(needle) !== -1;
    const bOk = !wantB || String(r[1]).trim() === wantB;
    if (aOk && bOk) matches.push(i + 2);
  });

  if (matches.length === 0) throw new Error('no row matches row_match ' + JSON.stringify(rowMatch));
  if (matches.length > 1) throw new Error('row_match is ambiguous (rows ' + matches.join(', ') + ') — add col_b_equals or a longer substring');
  return matches[0];
}

function guardFormulas_(values, allowFormulas) {
  if (allowFormulas) return;
  values.forEach(function (row) {
    row.forEach(function (v) {
      if (typeof v === 'string' && v.charAt(0) === '=') {
        throw new Error('a value starts with "=" and would become a formula — pass allow_formulas: true if intentional');
      }
    });
  });
}

function capCells_(values, max) {
  const cells = values.length * values[0].length;
  if (cells > max) throw new Error('write of ' + cells + ' cells exceeds the ' + max + '-cell cap — split into smaller calls');
}

function truncate_(values) {
  // Keep audit entries bounded: at most 20 rows x 10 cols, 200 chars per cell.
  return values.slice(0, 20).map(function (row) {
    return row.slice(0, 10).map(function (v) { return String(v).slice(0, 200); });
  });
}

function audit_(op, details) {
  const props = PropertiesService.getScriptProperties();
  let ss = null;
  const id = props.getProperty('AUDIT_SPREADSHEET_ID');
  if (id) {
    try { ss = SpreadsheetApp.openById(id); } catch (err) { ss = null; }
  }
  if (!ss) {
    ss = SpreadsheetApp.create(AUDIT_SS_NAME);
    props.setProperty('AUDIT_SPREADSHEET_ID', ss.getId());
    ss.getSheets()[0].appendRow(['Timestamp', 'Op', 'Details']);
  }
  ss.getSheets()[0].appendRow([new Date().toISOString(), op, JSON.stringify(details).slice(0, 45000)]);
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
