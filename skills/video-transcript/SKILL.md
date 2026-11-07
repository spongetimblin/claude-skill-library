---
name: video-transcript
description: >-
  Get the transcript of an online video from its link and save it as a timestamped .txt in
  ~/Downloads: YouTube videos, Shorts, live replays and playlists, plus Vimeo, Wistia, Loom,
  TED and anything else yt-dlp supports. Uses the video's own captions; falls back to YouTube's
  transcript panel in a browser Claude can drive when YouTube blocks downloads, and to a local
  Whisper transcription when a video has no captions. Trigger on /video-transcript with a link,
  when the user asks to get, extract, pull, download or save the transcript or captions of a
  video or YouTube link, or pastes a video link and asks for its text. Not for audio or video
  files already on the computer, or for summarizing a transcript the user already has.
---

# video-transcript - online video link to a .txt transcript

The usual flow: `/video-transcript <link>`, sometimes with a word or two of options. The user wants the file, not the text in chat.

**Default output:** one file, `~/Downloads/<video title> - transcript.txt`. A header (title; channel, upload date, length; link; where the text came from), then one line per 8-20 seconds of speech, each starting with its timestamp (`[12:45]`), with the video's chapters as headings. On YouTube's auto-generated captions, a line starting `>>` is a change of speaker. An existing file is never overwritten; the new one gets ` (2)`.

**Script:** `~/.claude/skills/video-transcript/scripts/get_transcript.py`. Run it with `python3 -I`. Its last output line is always `RESULT {json}`; act on `status`.

## Options the user can give

| They say | Pass |
|---|---|
| "no timestamps", "as paragraphs", "plain" | `--plain` |
| "save it to <folder>" | `--out-dir "<folder>"` |
| a language ("the Spanish captions") | `--lang es` |
| "in English" for a video in another language | `--translate` (YouTube's machine translation; say so in the report) |
| "the whole playlist", "every video in this playlist" | `--playlist` |

A YouTube link with `&list=...` is the one video, not the playlist, unless the user asks for the playlist. The script strips the playlist part.

## Step 1: run the script

```bash
python3 -I ~/.claude/skills/video-transcript/scripts/get_transcript.py "<link>" [options]
```

| status | Meaning | What to do |
|---|---|---|
| `ok` | Saved. `path`, `source`, `lines`, `chapters`, `duration`, `last_timestamp` | Check `last_timestamp` is near `duration`, then report (Step 3). |
| `blocked` | The site refused (YouTube's 429, "not a bot", "page needs to be reloaded") | Update yt-dlp once (`brew upgrade yt-dlp`, or `python3 -m pip install -U yt-dlp`) and retry: YouTube changes often, and an out-of-date yt-dlp is the most common cause. Still blocked on YouTube: the browser path. |
| `needs_signin` | Private, members-only, age-restricted, or a site that needs an account | YouTube: the browser path, after the user signs in there. Other sites: "Videos behind a sign-in". |
| `no_captions` | The video has no caption track at all | The Whisper path. |
| `playlist` | The link is a playlist or channel page; `count` and the first 50 `videos` are listed | Ask whether they want all `count` videos (`--playlist`) or which ones. |
| `error` | Anything else; `detail` says what. A live or upcoming stream has captions only after it ends. | Report it. |

`--playlist` writes `~/Downloads/<playlist title> transcripts/` with numbered files in playlist order, pauses 3 seconds between videos, and lists videos it could not do (`not_transcribed`). Offer the Whisper path for any that had no captions. Above about 25 videos, say how many and confirm before starting.

The script never reads the user's browser sign-ins: do not add `--cookies-from-browser` or `--cookies`. Use the browser path instead.

## The browser path (YouTube blocked or needs a sign-in)

Needs a browser Claude can run JavaScript in: the Claude desktop app's built-in browser, or Claude in Chrome. It uses YouTube's own "Show transcript" panel. YouTube's page blocks `fetch()` to other hosts but not a form submission, so the page posts the text to a one-shot receiver on 127.0.0.1, on the user's own computer.

1. Start the receiver in the background. It takes one POST and exits, or gives up after 5 minutes:
   ```bash
   python3 -I ~/.claude/skills/video-transcript/scripts/receive_post.py "<scratch folder>/panel.txt"
   ```
2. Open the plain watch link, `https://www.youtube.com/watch?v=<id>`, in the browser. If the video needs a sign-in, ask the user to sign in there and say "done".
3. Read `~/.claude/skills/video-transcript/scripts/panel_extract.js` and run its whole text in the page. It opens the panel, reads every line and submits them; it returns `SENT <n> lines` or `NO_TRANSCRIPT_PANEL`. The tab then shows "Transcript saved", which is expected.
4. Format it, with the link so the header and chapters come from the video's details:
   ```bash
   python3 -I ~/.claude/skills/video-transcript/scripts/get_transcript.py "<link>" --from-panel "<scratch folder>/panel.txt"
   ```
   If the details lookup itself is blocked, add `--title "<title from the page>"` and leave the link out.

`NO_TRANSCRIPT_PANEL` means the video has no captions (the Whisper path) or YouTube changed the panel's markup. To tell which, take a screenshot: a panel with lines means the selectors in `panel_extract.js` need updating. The panel's lines are coarser than the script's (one per 5-10 seconds, no `>>` speaker marks).

If the receiver fails (port 8765 taken, or the form is blocked), the fallback is reading the text out in chunks with JavaScript and writing the file directly. It costs far more tokens, so it is the last resort.

## The Whisper path (no captions)

Needs a local Whisper install (see the README). On Apple Silicon, `mlx-whisper` runs several times faster than real time.

1. Tell the user in one line that the video has no captions, how long it is, and roughly how long transcription will take, then go ahead. **Ask first instead** when the audio is over about 2 hours, or when the site has turned off downloads for the video.
2. Download the audio only, into a scratch folder:
   ```bash
   yt-dlp -q -f "bestaudio[ext=m4a]/bestaudio/worst" -x --audio-format m4a -o "<scratch folder>/audio.%(ext)s" "<link>"
   ```
3. Transcribe to SRT. Over about 10 minutes of audio, run it in the background. Use whichever is installed:
   ```bash
   mlx_whisper "<scratch folder>/audio.m4a" --model mlx-community/whisper-large-v3-turbo -f srt -o "<scratch folder>/whisper"
   whisper "<scratch folder>/audio.m4a" --model turbo --output_format srt --output_dir "<scratch folder>/whisper"
   ```
   Pass names from the title or description as an initial prompt (`--initial-prompt` / `--initial_prompt`) to help with spelling.
4. Format it. If the SRT carries speaker labels (`Speaker 1: ...`, from a transcriber that does diarization), the script keeps them when there is more than one voice:
   ```bash
   python3 -I ~/.claude/skills/video-transcript/scripts/get_transcript.py "<link>" --from-subs "<scratch folder>/whisper/audio.srt"
   ```
   Add `--title` when the site's title is a file name (Wistia gives names like `cgf1ulkrs669pcdu8m50.mp4`).
5. Delete the audio unless the user asked to keep it.

## Videos behind a sign-in

yt-dlp can't sign in, and this skill doesn't hand it the user's cookies. Transcribe only videos the user has the right to, within the site's terms.

Many course and membership sites embed a standard player (Wistia, Vimeo). When the player's own link plays without a sign-in, run the script on that link:

- Wistia: `https://fast.wistia.net/embed/iframe/<id>`
- Vimeo: `https://player.vimeo.com/video/<id>`, with `--referer "<the page's URL>"` when the video is restricted to its site. Plain `vimeo.com/<id>` links may need a login in yt-dlp; the player link often does not.

## Step 3: report

Lead with the result: the file's full path, the video's title and length, and where the text came from, since that sets how far to trust it. Creator captions are usually accurate; YouTube's auto-generated captions and Whisper misspell names and have no speaker names. Say if the lines stop well short of the video's length, if a different language or YouTube's translation was used, or if the browser or Whisper path was needed. Don't paste the transcript into chat unless asked.

## Reflect and improve (SUGGEST ONLY)

Last step of every run, including runs that failed or stopped early, after the report.

**This skill never edits itself.** It writes suggestions to a log that the user reviews: `~/.claude/skills/video-transcript/improvement-log.md`, newest entries on top. Create the file if it does not exist.

Add a dated note of one to three lines: which path produced the text (captions, browser panel, Whisper) and what forced a fallback; sites or link shapes the script didn't handle; transcript problems (lines stopping short, duplicates, chapter headings in the wrong place); YouTube panel changes that broke `panel_extract.js`; options the user asked for that the script had no flag for. "No notable friction" is a valid note.

When there are 5 or more notes since the last synthesis, add a dated `## Synthesis` entry at the top with a short prioritized list of proposed changes, each tagged `STATUS: AWAITING REVIEW`, and mention it in one line of the report. Apply none of them.
