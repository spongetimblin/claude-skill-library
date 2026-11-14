#!/usr/bin/env python3
"""Turn an online video's captions into a timestamped .txt transcript.

Uses yt-dlp, so it works on YouTube (videos, Shorts, live replays, playlists)
and every other site yt-dlp supports (Vimeo, Wistia, Loom, TED, podcasts...).

Modes
  get_transcript.py URL                     captions -> ~/Downloads/<title> - transcript.txt
  get_transcript.py URL --playlist          every video in a playlist, into one folder
  get_transcript.py URL --from-subs FILE    format an .srt/.vtt/.json3 you already have
                                            (Whisper output, a Wistia caption file)
  get_transcript.py URL --from-panel FILE   format text copied from YouTube's
                                            "Show transcript" panel (browser fallback)

Options
  --out-dir DIR     where the .txt goes (default ~/Downloads)
  --lang CODE       caption language wanted (default en)
  --translate       if the video's own language isn't --lang, take YouTube's
                    machine translation instead of the original-language captions
  --plain           paragraphs without timestamps
  --title TEXT      title for the header and file name when there is no URL metadata
  --link URL        with --from-subs or --from-panel and no URL: the link to print in
                    the header, with no metadata lookup (a site yt-dlp cannot read)
  --byline TEXT     with --link: the header's second line, such as
                    "Show name, November 9, 2026, length 2:21:12"
  --source TEXT     override the "Transcript source" line in the header
  --referer URL     pass a Referer to yt-dlp (embedded Vimeo/Wistia players)

The last line printed is always `RESULT {json}` with "status":
  ok, no_captions, blocked, needs_signin, playlist, error
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path


def result(status, code, **kw):
    kw["status"] = status
    print("RESULT " + json.dumps(kw, ensure_ascii=False))
    sys.exit(code)


# ---------- yt-dlp ----------

def run_ytdlp(args, timeout=300):
    p = subprocess.run(["yt-dlp", "--no-warnings", *args], capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def classify_error(err):
    e = err.lower()
    if "429" in e or "too many requests" in e or "not a bot" in e or "page needs to be reloaded" in e:
        return "blocked"
    if any(s in e for s in ("sign in", "members-only", "member", "private video", "login", "your age", "age-restricted", "age restricted", "cookies")):
        return "needs_signin"
    return "error"


def clean_url(url):
    """Drop playlist/time/share params from a single-video YouTube link."""
    if re.search(r"(youtube\.com|youtu\.be)", url) and ("v=" in url or "youtu.be/" in url or "/shorts/" in url or "/live/" in url):
        url = re.sub(r"[?&](list|index|t|si|pp|start_radio|feature)=[^&]*", "", url)
        if "?" not in url and "&" in url:
            url = url.replace("&", "?", 1)
    return url


def is_playlist_only(url):
    return bool(re.search(r"youtube\.com/(playlist|@|c/|channel/|user/)", url)) and "v=" not in url


def get_meta(url, referer=None, playlist=False):
    args = ["-J"] + ([] if playlist else ["--no-playlist"])
    if playlist:
        args.append("--flat-playlist")
    if referer:
        args += ["--referer", referer]
    for attempt in range(2):
        code, out, err = run_ytdlp(args + [url])
        if code == 0 and out.strip():
            return json.loads(out)
        kind = classify_error(err)
        if kind == "blocked" and attempt == 0:
            time.sleep(15)
            continue
        result(kind, 3 if kind == "blocked" else 5 if kind == "needs_signin" else 1,
               stage="metadata", detail=err.strip()[-600:])


def pick_track(meta, lang, translate):
    """Return (key, is_auto, description) or None."""
    manual = {k: v for k, v in (meta.get("subtitles") or {}).items() if k != "live_chat"}
    auto = meta.get("automatic_captions") or {}

    def name(tracks, key):
        n = (tracks.get(key) or [{}])[0].get("name") or key
        return re.sub(r"\s*\(.*?\)\s*$", "", n)

    for k in [lang] + sorted(k for k in manual if re.match(rf"{lang}[-_]", k)):
        if k in manual:
            return k, False, f"captions uploaded by the creator ({name(manual, k)})"
    if f"{lang}-orig" in auto:
        return f"{lang}-orig", True, f"auto-generated captions ({name(auto, lang)})"
    origs = [k for k in auto if k.endswith("-orig")]
    if not origs and lang in auto:  # non-YouTube sites have no -orig marker
        return lang, True, f"auto-generated captions ({name(auto, lang)})"
    if origs and translate and lang in auto:
        return lang, True, f"auto-generated captions machine-translated from {name(auto, origs[0][:-5])} into {name(auto, lang)}"
    if manual:
        k = sorted(manual)[0]
        return k, False, f"captions uploaded by the creator ({name(manual, k)}; no {lang} track)"
    if origs:
        k = origs[0]
        return k, True, f"auto-generated captions in the video's own language ({name(auto, k[:-5])})"
    return None


def download_track(url, key, is_auto, tmp, referer=None):
    args = ["--skip-download", "--no-playlist", "--write-auto-subs" if is_auto else "--write-subs",
            "--sub-langs", key, "--sub-format", "json3/vtt/srt/best",
            "-P", tmp, "-o", "subs.%(ext)s"]
    if referer:
        args += ["--referer", referer]
    for attempt in range(3):
        code, out, err = run_ytdlp(args + [url])
        files = [f for f in Path(tmp).iterdir() if f.name.startswith("subs.")]
        if files:
            return files[0]
        kind = classify_error(err)
        if kind == "blocked" and attempt < 2:
            time.sleep(20 * (attempt + 1))
            continue
        result(kind, 3 if kind == "blocked" else 5 if kind == "needs_signin" else 1,
               stage="captions", detail=err.strip()[-600:])


# ---------- parsing into units: (start_seconds, text, speaker) ----------

def units_from_json3(path):
    d = json.load(open(path, encoding="utf-8"))
    units = []
    for ev in d.get("events", []):
        segs = ev.get("segs")
        if not segs or ev.get("aAppend"):
            continue
        t0 = ev.get("tStartMs", 0)
        for s in segs:
            txt = s.get("utf8", "")
            if not txt.strip():
                continue
            units.append(((t0 + s.get("tOffsetMs", 0)) / 1000, txt.replace("\n", " "), None))
    return units


TS = r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})"


def _secs(h, m, s, ms):
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def units_from_cues(path):
    """SRT or VTT. Handles YouTube-style rolling cues and 'Speaker: text' prefixes."""
    raw = open(path, encoding="utf-8", errors="replace").read().replace("\r", "")
    cues, cur = [], None
    for line in raw.split("\n"):
        m = re.search(TS + r"\s*-->\s*" + TS, line)
        if m:
            cur = [_secs(*m.groups()[:4]), []]
            cues.append(cur)
        elif cur is not None and line.strip():
            cur[1].append(line.strip())
        elif not line.strip():
            cur = None
    units, prev = [], ""
    for start, lines in cues:
        if lines and re.fullmatch(r"\d+", lines[-1]):
            lines = lines[:-1]
        text = " ".join(lines)
        text = re.sub(r"<[^>]+>", "", html.unescape(text)).strip()
        text = re.sub(r"\s+", " ", text)
        if not text or text == prev:
            continue
        new = text[len(prev):].strip() if prev and text.startswith(prev) else text
        prev = text
        if not new:
            continue
        speaker = None
        sm = re.match(r"^((?:SPEAKER_\d+|Speaker \d+|[A-Z][\w.' -]{0,40})):\s+(.*)$", new)
        if sm and len(sm.group(1).split()) <= 4:
            speaker, new = sm.group(1), sm.group(2)
        units.append((start, new, speaker))
    return units


def units_from_panel(path):
    units = []
    for line in open(path, encoding="utf-8").read().replace("\r", "").split("\n"):
        m = re.match(r"^\[(?:(\d+):)?(\d+):(\d{2})\]\s*(.*)$", line.strip())
        if m:
            h, mi, s, txt = m.groups()
            txt = re.sub(r"^(\d+ hours?,? ?)?(\d+ minutes?,? ?)?(\d+ seconds?)?\s*", "", txt)
            units.append((int(h or 0) * 3600 + int(mi) * 60 + int(s), txt, None))
    return units


def load_units(path):
    p = str(path).lower()
    if p.endswith(".json3") or p.endswith(".json"):
        return units_from_json3(path)
    return units_from_cues(path)


# ---------- grouping and output ----------

def ts(sec, long):
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if long else f"{m}:{s:02d}"


def group(units, chapters):
    """Lines of about 8-20 s, broken at sentence ends, speaker changes (YouTube's '>>'),
    chapters and pauses."""
    bounds = sorted(c["start_time"] for c in chapters or [])
    # A pause is a gap well beyond the usual spacing: words (json3) are ~0.3 s apart,
    # subtitle cues and panel lines several seconds apart.
    steps = sorted(b[0] - a[0] for a, b in zip(units, units[1:]))
    gap = max(4, 2.5 * steps[len(steps) // 2]) if steps else 4
    lines, cur = [], None
    for start, text, spk in units:
        crossed = cur and any(cur["start"] < b <= start for b in bounds)
        turn = text.strip().startswith(">>")
        if cur:
            dur = start - cur["start"]
            t = cur["text"].strip()
            ends = re.search(r"[.?!][\"')\]]*$", t)
            pause = re.search(r"[,;:][\"')\]]*$", t)
            if (crossed or turn or spk != cur["spk"] or start - cur["last"] >= gap or dur >= 30
                    or (dur >= 8 and ends) or (dur >= 20 and pause)):
                lines.append(cur)
                cur = None
        if cur is None:
            cur = {"start": start, "text": "", "spk": spk, "last": start}
        sep = "" if (not cur["text"] or text.startswith(" ") or cur["text"].endswith(" ")) else " "
        cur["text"] += sep + text
        cur["last"] = start
    if cur:
        lines.append(cur)
    for l in lines:
        l["text"] = re.sub(r"\s+", " ", l["text"]).strip()
    return [l for l in lines if l["text"]]


def render(lines, chapters, header, plain, long):
    out = header[:]
    chs = sorted(chapters or [], key=lambda c: c["start_time"])
    ci, last_spk, para = 0, None, []

    def flush():
        if para:
            out.append(" ".join(para))
            out.append("")
            para.clear()

    for l in lines:
        while ci < len(chs) and chs[ci]["start_time"] <= l["start"] + 0.5:
            flush()
            if not plain and out and out[-1] != "":
                out.append("")
            title = (chs[ci].get("title") or "").strip()
            if not re.match(r"(?i)chapter\b", title):
                title = f"Chapter {ci + 1}: {title}" if title else f"Chapter {ci + 1}"
            out.append(f"{title} ({ts(chs[ci]['start_time'], long)})")
            out.append("")
            ci += 1
        spk = f"{l['spk']}: " if l["spk"] and l["spk"] != last_spk else ""
        last_spk = l["spk"] or last_spk
        if plain:
            if spk or len(para) >= 6 or l["text"].startswith(">>"):
                flush()
            para.append(spk + l["text"])
        else:
            out.append(f"[{ts(l['start'], long)}] {spk}{l['text']}")
    flush()
    return "\n".join(out).rstrip() + "\n"


def make_header(meta, url, source, title, speaker_marks=False, byline=None):
    t = title or meta.get("title") or "Untitled video"
    h = [t]
    if byline and not meta:
        h.append(byline)
    bits = []
    who = meta.get("channel") or meta.get("uploader")
    if who:
        bits.append(who)
    d = meta.get("upload_date") or meta.get("release_date")
    if d:
        try:
            bits.append(datetime.strptime(d, "%Y%m%d").strftime("%B %-d, %Y"))
        except ValueError:
            pass
    if meta.get("duration"):
        bits.append("length " + ts(meta["duration"], meta["duration"] >= 3600))
    if bits:
        h.append(", ".join(bits))
    link = meta.get("webpage_url") or url
    if link:
        h.append(link)
    h.append(f"Transcript source: {source}.")
    if "auto-generated" in source or "Whisper" in source:
        h.append("Machine transcription: names and some words may be misheard.")
    if speaker_marks:
        h.append('">>" marks a change of speaker (YouTube does not say who).')
    h.append("")
    return h, t


def safe_name(title):
    s = title.replace("/", " ").replace(":", " -")
    s = re.sub(r'[\\?*"<>|\x00-\x1f]', "", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s[:150] or "Untitled video"


def unique(path):
    if not path.exists():
        return path
    i = 2
    while True:
        p = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not p.exists():
            return p
        i += 1


def write_transcript(units, meta, url, source, args, out_dir, prefix=""):
    if not units:
        result("error", 1, detail="captions file had no text")
    if len({u[2] for u in units}) == 1:  # one voice: a label on it adds nothing
        units = [(s, t, None) for s, t, _ in units]
    chapters = meta.get("chapters") or []
    dur = meta.get("duration") or units[-1][0]
    long = dur >= 3600
    marks = any(u[1].strip().startswith(">>") for u in units)
    header, title = make_header(meta, url, source, args.title, marks, getattr(args, "byline", None))
    lines = group(units, chapters)
    text = render(lines, chapters, header, args.plain, long)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = unique(out_dir / f"{prefix}{safe_name(title)} - transcript.txt")
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "title": title, "lines": len(lines), "chapters": len(chapters),
            "words": len(text.split()), "source": source,
            "duration": ts(dur, long), "last_timestamp": ts(lines[-1]["start"], long) if lines else None}


def one_video(url, args, out_dir, prefix=""):
    meta = get_meta(url, args.referer)
    if meta.get("live_status") in ("is_live", "is_upcoming"):
        result("error", 1, detail=f"video is {meta['live_status']}; captions exist only after the stream ends")
    pick = pick_track(meta, args.lang, args.translate)
    if not pick:
        size = None
        for f in meta.get("formats") or []:
            if f.get("vcodec") == "none" and (f.get("filesize") or f.get("filesize_approx")):
                s = f.get("filesize") or f.get("filesize_approx")
                size = s if size is None else min(size, s)
        return {"status": "no_captions", "title": meta.get("title"), "url": meta.get("webpage_url") or url,
                "duration_sec": meta.get("duration"), "smallest_audio_mb": round(size / 1e6, 1) if size else None}
    key, is_auto, desc = pick
    key_ = (meta.get("extractor_key") or "").lower()
    site = {"youtube": "YouTube", "tedtalk": "TED", "vimeo": "Vimeo", "wistia": "Wistia", "loom": "Loom"}.get(
        key_, meta.get("webpage_url_domain") or meta.get("extractor_key") or "Site")
    if key_.startswith("youtube"):
        site = "YouTube"
    source = args.source or f"{site} {desc}"
    with tempfile.TemporaryDirectory() as tmp:
        f = download_track(meta.get("webpage_url") or url, key, is_auto, tmp, args.referer)
        units = load_units(f)
    info = write_transcript(units, meta, url, source, args, out_dir, prefix)
    info["status"] = "ok"
    info["track"] = key
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?")
    ap.add_argument("--out-dir", default=str(Path.home() / "Downloads"))
    ap.add_argument("--lang", default="en")
    ap.add_argument("--translate", action="store_true")
    ap.add_argument("--plain", action="store_true")
    ap.add_argument("--playlist", action="store_true")
    ap.add_argument("--from-subs")
    ap.add_argument("--from-panel")
    ap.add_argument("--title")
    ap.add_argument("--link")
    ap.add_argument("--byline")
    ap.add_argument("--source")
    ap.add_argument("--referer")
    args = ap.parse_args()
    out_dir = Path(os.path.expanduser(args.out_dir))

    if args.from_subs or args.from_panel:
        meta = {}
        if args.url:
            meta = get_meta(clean_url(args.url), args.referer)
        if args.from_subs:
            units = load_units(args.from_subs)
            source = args.source or ("captions file" if args.from_subs.lower().endswith((".json3", ".json"))
                                     else "local Whisper transcription of the audio")
        else:
            units = units_from_panel(args.from_panel)
            source = args.source or "YouTube auto-generated captions, copied from the video's transcript panel"
        info = write_transcript(units, meta, args.url or args.link, source, args, out_dir)
        result("ok", 0, **info)

    if not args.url:
        ap.error("a URL is required")

    url = args.url
    if args.playlist or is_playlist_only(url):
        pl = get_meta(url, args.referer, playlist=True)
        entries = [e for e in (pl.get("entries") or []) if e]
        if not args.playlist:
            result("playlist", 4, title=pl.get("title"), count=len(entries),
                   videos=[{"n": i + 1, "title": e.get("title"), "url": e.get("url")} for i, e in enumerate(entries[:50])])
        folder = out_dir / f"{safe_name(pl.get('title') or 'Playlist')} transcripts"
        done, missing = [], []
        width = len(str(len(entries)))
        for i, e in enumerate(entries, 1):
            vurl = e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}"
            try:
                info = one_video(vurl, args, folder, prefix=f"{i:0{width}d} ")
            except SystemExit:
                info = {"status": "failed", "title": e.get("title"), "url": vurl}
            (done if info.get("status") == "ok" else missing).append(info)
            print(f"{i}/{len(entries)} {info.get('status')}: {info.get('title')}", flush=True)
            time.sleep(3)
        result("ok" if done else "error", 0 if done else 1, folder=str(folder), playlist=pl.get("title"),
               transcribed=len(done), not_transcribed=[{"title": m.get("title"), "url": m.get("url"),
                                                         "why": m.get("status")} for m in missing])

    info = one_video(clean_url(url), args, out_dir)
    status = info.pop("status")
    result(status, 0 if status == "ok" else 2, **info)


if __name__ == "__main__":
    main()
