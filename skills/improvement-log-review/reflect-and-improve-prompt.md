# The "Reflect & Improve" loop: a reusable prompt

A copy-paste prompt that tells Claude to add a final continuous-improvement step to any skill or scheduled task you are building. The skill keeps a running "friction log" and periodically proposes its own improvements, but it is suggest-only: it never edits itself. You review the proposals and apply them, which is what `/improvement-log-review` does.

The idea comes from Tom Johnson of the I'd Rather Be Writing blog and podcast. The background, and what took longest to get right (where the log lives), is in the "Make Your Skills Self-Improving" tip of [Claude Workflow Tips](https://chadtimbl.in/writings/claude-workflow-tips.html).

## How to use it

1. Optionally edit the Parameters below, or leave them for the defaults.
2. Paste everything in the PROMPT block into the conversation where you are building or reworking the skill.

## Parameters (optional)

- **Autonomy:** `suggest only` (default), or `auto-fix small mechanical stuff only`, or `full self-editing`
- **Synthesis day:** `Sunday` (default)
- **Cadence:** `light note every run + weekly synthesis` (default), or `every run only`, or `weekly only`
- **Where the log lives:** the skill's existing data or output folder (default)
- **How you review:** say "review the [skill name] improvement log", or run `/improvement-log-review`

## PROMPT

```
I'm building a skill (see above/below). Before we finish, add a final "Reflect & improve" continuous-improvement step to it, following the spec below. This is a reusable pattern I add to my skills, so understand the full intent and adapt it to THIS skill specifically.

WHY: I want the skill to get sharper over time by learning from how its own runs actually go (a built-in "friction log"), WITHOUT ever silently changing its own behavior. The reflection step is a closed suggestion box; I'm the human-in-the-loop who reviews and applies changes.

NON-NEGOTIABLE RULES:
1. SUGGEST ONLY (default). The skill must NEVER edit its own instructions/SKILL.md or change any of its rules, thresholds, inputs, sources, output format, or behavior on its own. It only writes suggestions to a separate log for me to review and apply. (If I've set the autonomy knob to "auto-fix small mechanical stuff only," it may directly apply low-risk mechanical fixes like a dead/changed URL or a stale date, and must log everything else as a suggestion. Never go beyond the level I set.)
2. This reflection step is the LAST step of every run / invocation, and it runs even when a run fails or stops early; those are the runs whose friction matters most.
3. Keep it lightweight: it shouldn't bloat runtime or the skill's normal output.

WHAT TO IMPLEMENT:
A. Create a dedicated `improvement-log.md` in the skill's existing data/output folder (wherever its other working files live; if it has none, pick a sensible stable path and tell me). Seed it with a short header that explains: it's a suggest-only friction + improvement log, the skill writes here but never edits itself, and how I review/apply suggestions. Newest entries on top.
B. Add this improvement log to the skill's list of known working files, so the agent reads recent entries during the weekly synthesis.
C. Add a "Reflect & improve (SUGGEST ONLY)" section as the skill's final step, containing:
   - EVERY RUN (light friction note): add a dated 1–3 line entry at the top of the log capturing this run's friction, such as tools/sources that errored or returned an empty/JS-shell response, dead or stale data, steps that wasted effort, coverage gaps, and any calibration/quality observations specific to this skill's job. "No notable friction" is a valid entry.
   - WEEKLY SYNTHESIS ([Sunday by default] only): read the last ~7 days of friction notes plus the skill's run log/history, look for recurring patterns, and add a dated "Weekly synthesis" entry at the top with a short, prioritized list of concrete, actionable proposed refinements. Tag each `STATUS: AWAITING REVIEW`. Do NOT apply them.
   - NO HEADS-UP: never point me at the log, or send its proposals, in an email or other notification, alone or folded into a message that's already going out. The skill's messages stay about the skill's own job. I review every log on a regular schedule (with /improvement-log-review), so the log is enough.
D. TAILOR everything to THIS skill's domain. Don't copy generic examples; name the actual tools, sources, file paths, and realistic failure modes this specific skill has. The friction-note examples should read like they were written for this skill.
E. If the skill also has a separate human-readable instructions/README doc, mirror a short version of this "Reflect & improve" section there so the two stay in sync.
F. DEFAULTS to assume unless I said otherwise in a Parameters block: suggest-only autonomy; friction note every run + weekly synthesis on Sundays; human-in-the-loop review (I'll say "review the [skill] improvement log" when I want to act). If any default genuinely doesn't fit this skill (e.g., it isn't scheduled/recurring, has no persistent storage, or has no output channel), don't force it; tell me and propose the right adaptation. Adaptations that have worked: a skill that runs only weekly synthesizes monthly instead, or it reasons from too little. A skill run by hand at irregular times synthesizes when there are 5 or more friction notes since the last synthesis, or when the last one is over 30 days old. A skill whose output lands in a different folder every run keeps its log in its own skill folder. A cloud routine that runs in a fresh container can commit its log to its own repo each run. Whatever the adaptation, keep the log and its synthesis in a file, never only in an email, where a filter can archive it unseen and a review can't find it.
G. ARCHIVING: put this rule in the log's header, as part of the review instructions. At the end of each review, if the log is over about 100 KB (past the 25K-token limit on what Claude reads in one pass), move applied or otherwise resolved entries, plus friction notes a synthesis has already covered, into `improvement-log-archive-through-YYYY-MM.md` in the same folder, starting that file with a note that it is history only and naming the live log. Keep in the live log anything AWAITING REVIEW, DEFERRED or DECLINED, and whatever recent entries the synthesis reads. When a declined or still-open item sits inside an entry being archived, copy that paragraph verbatim into a "Carried forward from archived entries" section at the top of the live log, so the same idea isn't proposed again. If the live log is git-ignored, make sure the archive is too.

When you're done, show me exactly what you added (the new log file + the section) and confirm the skill itself was not otherwise changed.
```
