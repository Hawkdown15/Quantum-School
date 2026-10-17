# Nav Fusion Media • QS — Shorts Scheduler

A Claude Code skill for **Quantum School (@quantumschool45)**. It turns unlisted YouTube Shorts into SEO-ready, scheduled and playlisted videos. You answer three forms and approve one table; the skill does the rest in YouTube Studio.

**Team guide (PDF):** [`docs/Nav Fusion Media - QS Shorts Scheduler Guide.pdf`](docs/)

## Install

```bash
git clone https://github.com/Hawkdown15/Quantum-School.git ~/.claude/skills/nfm-qs-shorts-scheduler
```
Restart Claude Code. Typing `/nfm` should show the skill.

You also need:
- the vidIQ MCP server for Quantum School (`vidiq-qs`), connected with the channel owner account
- the Claude in Chrome extension, signed in to YouTube Studio as @quantumschool45
- the vidIQ Chrome extension turned **off** on studio.youtube.com

## Run

```
/nfm-qs-shorts-scheduler
/nfm-qs-shorts-scheduler kal ke EVS aur Maths shorts schedule kar do
```

1. **Form 1 — the run:** subjects, date, which videos, mode
2. **Form 2 — per subject:** time window, interval, playlist, related video
3. **Form 3 — custom:** exact times, extra tags/hashtags, extra description line, free notes
4. **One approval table**, then everything is applied and verified

## Files

| Path | What |
|---|---|
| `SKILL.md` | The workflow Claude follows (forms, fetch, draft, approve, apply, report) |
| `config.json` | Channels, subject → playlist IDs, slot windows, SEO rules. Add channels here. |
| `scripts/slots.py` | IST slots → UTC `publishAt`. Skips past and taken slots, overflows to the next day. |
| `scripts/plan.py` | `meta.tsv` → `plan.json` + approval table, with SEO validation |
| `input-template.md` | What the forms ask |
| `reference/studio-ui.md` | The Studio click recipe and the fix for every known error |
| `reference/session-analysis.md` | How the workflow was built (Oct 2026, 150 shorts) |

Naming rule for every Quantum School skill: slug `nfm-qs-<work>`, display `Nav Fusion Media • QS — <Work Name>`.
