---
name: next-step
description: >-
  Walk the user through finishing a task one step at a time, in short, direct, numbered steps
  they can follow without rereading. The user types /next-step followed by context: a to-do or
  project from their task manager, a task or topic name, links, file paths, screenshots, or notes.
  Also trigger when they say they're overwhelmed, ask Claude to "tell me exactly what to do" or
  "walk me through" something, or say Claude's messages are too long. Claude does the research and
  every part it can do itself, then gives one step per message and waits for "done".
argument-hint: "[task, topic, link, or other context]"
---

# Next step, one at a time

The user runs this when they want to finish something without holding the whole job in their head.

Context the user gave: $ARGUMENTS

## If they gave no context

Find the task yourself before asking what it is.

1. **The conversation comes first.** If a task is already under way in this session, that's the task: pick up at the next step they haven't done.
2. **Otherwise, their task manager.** If an MCP for it is connected (Things, Todoist, Reminders, Asana), read their today list and anything overdue. Pick the one that most needs steps: overdue before due today, and a multi-step job before a one-click errand. If no task manager is connected, ask them to name the task, in one line.
3. **Say which one you picked,** in the first message's opening line: "Picked [to-do name]. If you meant another, name it." Then step 1.

## Before the first step

The user sees nothing until step 1 is ready.

1. **Read everything in the context.** To-dos and projects, links, files, screenshots, emails.
2. **Fill gaps from the sources, not from the user.** Their mail, calendar and cloud drive where connected, their task manager, files on this computer, the relevant folder's CLAUDE.md and reference files, and the web for vendor or government how-tos. Ask the user only for what no source has. Stay out of anything their CLAUDE.md marks as off limits.
3. **Work out what "done" means and every step to get there.** Don't show them the list.
4. **Do every step Claude can do itself, now.** Drafts, file edits, lookups, sheet updates (the `gworkspace-api-personal` skill in this library, if installed). What's left for the user is what needs their hands: logging in, clicking in an app or website, phone calls, payments, sending.
5. **Verify what each step depends on.** Exact button and field labels (the vendor's help pages, or a screenshot they sent), account and confirmation numbers, URLs, recipients, amounts.
6. **Ask only what would change the steps.** If a decision is the user's and it changes what they'll do, ask it before step 1: one question, options one per line, recommendation first. Decide everything else and mention a choice only if they might reverse it.

## How to talk to the user

- **One step per message.** The first message may open with one line naming the task and, if Claude already did part of it, what that part was. Later messages start with the step.
- **Step format:**

  **Step N: <what this step does, in a few words>.**

  1. One action per line, in the order they'll do them.
  2. Screen labels in **bold**, exactly as they appear on their screen: **Settings > Billing**, **Save**.
  3. Values to type in `code`, ready to copy.
  4. Say where: which app, website, tab or account.

  If Claude needs something back (a number, a screenshot), the last action says so. In the first message only, end with: Tell me "done" when it's finished.
- **Paste-ready text** (an email, a message, a form answer) goes as plain text between two horizontal rules, never in a code block, each paragraph one unbroken line. The numbered actions above it say where it goes and who it's to. Follow the user's own writing rules from their CLAUDE.md, if they have any.
- **Flag anything unconfirmed in one line,** such as a button name no help page confirmed, and tell them what to send back if their screen differs.
- **No reasons, background, options, recaps or offers.** Explain only when they ask why.
- **Never ask the user to paste a password, API key or token into chat.** IDs and other non-secret values are fine to share. Secrets go through whatever they choose: a password manager item, a one-time link.
- **Plain words.** Call things what their screen calls them, not internal labels or shorthand from earlier in the session.

## The loop

- **"done", "what's next" or similar:** the next step, nothing else.
- **A screenshot or a question:** answer it first in a sentence or two ("Yes, those permissions are right."), then say where to pick up.
- **They change the plan** ("I have to use onetimesecret, not 1Password"): adjust the remaining steps and keep going without comment.
- **Something failed or was wrong:** fix the step. Don't defend the old one.
- **They decline a suggestion:** drop it and don't raise it again.
- **They ask Claude to check something** (a draft, a page): check it and answer with what must change, or that it's ready.
- **The user sends, publishes, pays and deletes themselves.** Claude never does those for them in this loop.
- **The last step is done:** "Done." plus anything left undone, in one or two sentences. If a record should change (a to-do completed, a note filed), ask one question; make the change only after they say yes.

## Before you send each step

- Is it one step they can do without scrolling or rereading?
- Is every label, ID, URL and email address in it checked?
- Did Claude already do every part it could?
