# The /video-transcript skill

A Claude Code skill that turns a link to an online video into a timestamped `.txt` transcript in your Downloads folder. It works on YouTube (videos, Shorts, finished livestreams, chapters, playlists) and on the other sites [yt-dlp](https://github.com/yt-dlp/yt-dlp) supports, such as Vimeo, Wistia, Loom and TED. It replaces transcript websites with something you can read, change and run on your own computer.

It tries three ways, in order:

1. **The video's own captions**, downloaded with yt-dlp. Fast, and accurate when the creator uploaded captions.
2. **YouTube's transcript panel**, read in a browser Claude can drive (the Claude desktop app's built-in browser, or Claude in Chrome), when YouTube blocks the download or the video needs you signed in.
3. **Local Whisper transcription** of the audio, when the video has no captions at all.

## Install

1. Copy the `video-transcript` folder to `~/.claude/skills/video-transcript/`.
2. Install yt-dlp: `brew install yt-dlp` on a Mac, or `python3 -m pip install -U yt-dlp`. Keep it current; YouTube changes often, and an old yt-dlp is the usual reason a download fails.
3. For videos with no captions, also install ffmpeg (`brew install ffmpeg`) and a Whisper transcriber: `python3 -m pip install mlx-whisper` on Apple Silicon Macs, or `python3 -m pip install openai-whisper` elsewhere. Skip this step if you only need videos that have captions.

Then type `/video-transcript <link>` in Claude Code, or paste a video link and ask for its transcript.

## Options

Say them in words after the link: "no timestamps" (paragraphs instead), "save it to <folder>", a language ("the Spanish captions"), "in English" (YouTube's machine translation), or "the whole playlist".

## What the output looks like

```
How to Make Bread at Home
Example Channel, March 4, 2026, length 12:41
https://www.youtube.com/watch?v=...
Transcript source: YouTube auto-generated captions (English).
Machine transcription: names and some words may be misheard.
">>" marks a change of speaker (YouTube does not say who).

Chapter 1: Intro (0:00)

[0:02] Welcome back. Today we're making a simple loaf...
[0:14] >> And I'm here to help with the shaping...
```

## What is in the folder

| File | What it is |
|---|---|
| `SKILL.md` | The skill: when to use each path, the options, and how to report. |
| `scripts/get_transcript.py` | Fetches the captions with yt-dlp and writes the `.txt`. Also formats a caption file you already have (`--from-subs`) or text from YouTube's transcript panel (`--from-panel`). Python 3, standard library only. |
| `scripts/panel_extract.js` | Run in a YouTube watch page: opens the transcript panel and sends its lines to the receiver. |
| `scripts/receive_post.py` | A one-shot receiver on 127.0.0.1:8765 that saves what `panel_extract.js` sends. It listens on your own computer only and exits after one request. |

## Privacy and fair use

Nothing leaves your computer except the requests yt-dlp and the browser make to the video site. The skill never reads your browser's saved sign-ins or cookies. Transcribe only videos you have the right to use, within each site's terms.

No warranty. Its author uses it regularly. Not yet tried in real use: a long playlist run, YouTube's translation, and members-only videos.
