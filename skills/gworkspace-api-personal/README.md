# gworkspace-api-personal

A Claude Code skill that lets Claude write to your Google Sheets and edit your Google Docs, and attach Drive files to Calendar events, through a small Apps Script web app that you deploy from your own Google account. Claude's connectors can read Sheets and Docs but not change them; this fills that gap without giving Claude your password or a broad API key.

## How it fits together

- `apps-script/Code.gs` is the web app. It accepts a fixed list of operations (read a range, set a cell, add a row, find and replace in a doc, and so on), every request must carry a secret token, and every change is logged with its old value to an audit spreadsheet in your Drive.
- `apps-script/SETUP.md` is the short deployment checklist: create the script, set the token, deploy, store the URL and token as environment variables.
- `SKILL.md` tells Claude how to call it and the rules it follows (show you a write before it overwrites anything, verify after writing, never print the token).

The friendlier walkthrough, where Claude does most of the setup for you by driving your browser, is here: https://chadtimbl.in/writings/files/claude-google-sheets-docs-setup-guide.md

## Before you deploy

- In `Code.gs`, set `ALLOWED_CALENDARS` to the calendars Claude may attach files to (the placeholder is `you@example.com`).
- The skill reads the web app's URL and token from the environment variables `GSHEETS_PERSONAL_API_URL` and `GSHEETS_PERSONAL_API_TOKEN`. `SETUP.md` shows how to set them in `~/.zshenv` without the values passing through a chat.

## Install

Copy this folder to `~/.claude/skills/gworkspace-api-personal/`, deploy the script, set the two variables, then open a new Claude Code session and ask Claude to add a row to a sheet. The skill's `ping` check confirms the deployment before the first write.
