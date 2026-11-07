// Browser fallback for YouTube: open the video's "Show transcript" panel, read every
// line, and hand the text to receive_post.py on 127.0.0.1:8765 with a form POST.
// (YouTube's page blocks fetch() to other hosts, but not a form submission. The tab
// navigates to a "saved" page afterwards, which is expected.)
// Paste the whole file into the built-in browser's javascript_tool on the watch page.
const sleep = ms => new Promise(r => setTimeout(r, ms));
document.querySelector('#description-inline-expander #expand, tp-yt-paper-button#expand')?.click();
await sleep(1000);
const SEG = 'transcript-segment-view-model, ytd-transcript-segment-renderer';
let segs = document.querySelectorAll(SEG);
// The page holds more than one "Show transcript" button (some hidden); try each.
const buttons = [...document.querySelectorAll('button')]
  .filter(b => /^show transcript$/i.test((b.innerText || b.getAttribute('aria-label') || '').trim()));
for (const b of buttons) {
  if (segs.length) break;
  b.click();
  for (let i = 0; i < 16 && !segs.length; i++) {
    await sleep(500);
    segs = document.querySelectorAll(SEG);
  }
}
const lines = [];
for (const s of segs) {
  const t = s.querySelector('.ytwTranscriptSegmentViewModelTimestamp, .segment-timestamp')?.innerText.trim() || '';
  let x = s.innerText.trim().replace(t, '').trim().replace(/\s*\n\s*/g, ' ');
  x = x.replace(/^(\d+ hours?,? ?)?(\d+ minutes?,? ?)?(\d+ seconds?)?\s*/, '');
  if (t) lines.push('[' + t + '] ' + x);
}
if (!lines.length) {
  'NO_TRANSCRIPT_PANEL: no transcript lines found (no captions, or YouTube changed the panel)';
} else {
  const f = document.createElement('form');
  f.method = 'POST';
  f.action = 'http://127.0.0.1:8765/';
  f.style.display = 'none';
  const ta = document.createElement('textarea');
  ta.name = 't';
  ta.value = lines.join('\n');
  f.appendChild(ta);
  document.body.appendChild(f);
  f.submit();
  'SENT ' + lines.length + ' lines';
}
