---
name: nfm-qs-shorts-scheduler
description: "Nav Fusion Media • QS — Shorts Scheduler. Optimizes (Hindi-first title, description, tags), schedules in IST slots, and playlists unpublished YouTube Shorts for Quantum School (@quantumschool45), with one approval table before any write. Use when Raj says /nfm-qs-shorts-scheduler, or asks in English/Hinglish to schedule, optimize, or playlist QS shorts (e.g. \"kal ke EVS aur Maths shorts schedule kar do\"). Channel-config driven, so Navodayans Talk / The Social Animals can be added later."
---

# Nav Fusion Media • QS — Shorts Scheduler

Naming rule for every Quantum School skill: slug `nfm-qs-<work>`, display `Nav Fusion Media • QS — <Work Name>`.

Files (all paths relative to this skill folder):
- `config.json`: channels, subjects → playlist + slots, SEO rules. **Read it first. Never hardcode values that are in it.**
- `scripts/slots.py`: slot window → UTC `publishAt`. Skips past and already-taken slots, and overflows to the next day.
- `scripts/plan.py`: `meta.tsv` → `plan.json` + the approval table, with SEO validation.
- `input-template.md`: what Raj types.
- `reference/studio-ui.md`: the Studio click recipe with every known fix.
- `reference/session-analysis.md`: how this workflow was learned (the 16–17 Oct 2026 run of 150 shorts).

Work in the session scratchpad. Never do mental time maths; always use the scripts.

## Step 0: Input form (ALWAYS, on every run)

**Every run starts with the input form, whoever runs the skill and whatever they typed.** Open it with `AskUserQuestion` as the very first action, before any fetch. The only thing to do first is read `config.json` and work out the default date (`python3 scripts/slots.py --default-date`).

If the person typed free text (Hinglish too: "kal" = tomorrow, "aaj" = today, "parso" = +2 days, "sirf maths", "6 baje se", "har 30 min", "related video bhi"), still show the form, but put the matching option **first** and mark it "(Recommended)". Otherwise the config default is first and Recommended. Every question also gets the automatic "Other" box, where they can type a custom value.

### Form 1: the run (one AskUserQuestion, 4 questions)
| header | question | options (default first) |
|---|---|---|
| Subjects | Which subjects' shorts? (multiSelect) | EVS · Maths · Hindi · MAT. Hindi/MAT note "needs a time slot" while `enabled:false`. |
| Date | Start scheduling from which date? | `<default date> (Recommended)` · Today · Tomorrow · (Other: type YYYY-MM-DD) |
| Videos | Which videos? | All unscheduled private/unlisted shorts · Title search (type it in Other) · Specific IDs (paste in Other) |
| Mode | What should I do? | Optimize + schedule + playlist, long videos SEO-only · Same but skip long videos · Optimize only (no schedule) · Schedule + playlist only (keep titles) |

### Form 2: one AskUserQuestion per selected subject (4 questions)
Skip Time and Interval when the mode is "Optimize only".

| header | question | options |
|---|---|---|
| `<Subj>` time | `<Subj>` time window (IST, first to last slot)? | `<config start>–<config end> (Recommended)` · one hour earlier · one hour later · (Other: e.g. 18:00-22:00). For Hindi/MAT with no config window: "17:00–23:00" · "18:00–22:00" · Other. |
| Interval | Gap between `<Subj>` shorts? | `interval_choices_min` from config: 60 min (Recommended) · 30 min · 120 min |
| Playlist | Which playlist for `<Subj>` shorts? | `<playlist_name> (<playlist_id>) (Recommended)` · each `alt_playlists` entry · No playlist · (Other: type exact name or ID; it must already exist) |
| Related | Related video for `<Subj>` shorts? | `<related_video_title> – https://youtu.be/<related_video_id>` · None (leave as is) · (Other: paste a YouTube link) |

Each option's `description` shows the effect. For example: "7 slots/day: 17:00, 18:00 … 23:00".

### Form 3: custom inputs (one AskUserQuestion, 4 questions, always shown)
Every option set starts with "None (Recommended)". The person types their custom value in the automatic **Other** box.

| header | question | options | maps to |
|---|---|---|---|
| Exact times | Custom exact publish times instead of the window/interval? (applies per subject, e.g. `EVS=17:15,18:40 Maths=19:10,21:30`, or one list for all) | None (Recommended) · (Other: type the times) | `--slots SUBJ=HH:MM,HH:MM,…`; overrides Form 2's time and interval. Extra videos overflow to the next day at the same times. |
| Tags | Extra tags or hashtags for every video? | None (Recommended) · (Other: e.g. `tags: पर्वत, mountains  hashtags: #EVSQuiz`) | `--extra-tags "a,b"` / `--extra-hashtags "#X"`. Still capped at 15 tags and 500 characters. |
| Desc line | Extra line in every description? | None (Recommended) · WhatsApp Channel link (`whatsapp_channel` from config) · (Other: type the line) | `--desc-extra "…"`, placed above the hashtag line |
| Notes | Any other custom instruction for this run? | None (Recommended) · (Other: free text, e.g. "skip videos about earthquakes", "title में 'Q.12' mat likho", "EVS ko 1 Nov tak hi rakho") | Apply it while classifying/drafting/planning |

Custom input can never override the Hard rules: banned phrases, never creating playlists, never touching public videos' privacy, and the single approval table. `plan.py` validates custom tags, hashtags and lines too. If a custom note conflicts with a hard rule, say so in the approval message and follow the rule.

### After the forms
- Map the answers to script flags: `--date`, `--slots SUBJ=HH:MM-HH:MM/MIN`, `--playlist SUBJ=ID`, `--mode`.
- **Pasted related-video link:** extract the 11-character ID, then find its title with `vidiq_user_videos` (search) and use that title as the picker search text. If the video isn't on this channel, say so and ask again.
- **Typed playlist name:** check it on Studio → Playlists. If it isn't found, ask. **Never create a playlist.**
- A typed window or interval that doesn't parse, for example an end time before the start: re-ask only that question.
- No more questions after the forms until the single approval table in Step 3.

## Step 1: Fetch (read-only, automatic)

1. `mcp__<vidiq_server>__vidiq_user_videos` for the channel: get every video with privacy, publishAt and duration. Read calls work fine; only writes hit MFA. **`vidiq_get_videos_by_ids` can't see private videos**, so don't use it for this.
2. Candidates: privacy `private`/`unlisted`, **no publishAt**, duration ≤ 3 min (short), filtered by Raj's selection. **Already public videos: never touch their privacy.** Long videos only go in if the mode includes optimize.
3. Write `busy.txt` with every existing future publishAt (UTC), one per line, so no two videos share a slot.

## Step 1b: Research what works (read-only, when Raj asks or once a month)

- QS: `vidiq_channel_analytics` report=top_videos (views, engagedViews, averageViewPercentage) for the last ~60 days, then `vidiq_get_videos_by_ids` on the top shorts to read their titles.
- Competitor (default ALL ROUNDER BSS, `@AllRounderBSS`): `vidiq_channel_videos` short, popular=true and popular=false.
- Write the findings to `research.md` in the run folder. What we found on 28 Oct 2026:
  - Hooks built as a challenge, curiosity or "ye galti mat karna" beat flat question titles 1.5–3×.
  - Shorts of 35 seconds or less loop to 60–120% average view percentage.
  - BSS's 1M+ shorts are parent/offer shorts, so a parent CTA goes at the top of the description.
  - Shorts bring about 0 subs, so link each short to a topic-matched long video.
- Budget: transcripts cost 5 vidIQ credits each. ~110 transcripts ran the account dry on 28 Oct, so check `vidiq_balance` first and leave unfetched shorts for the next run.

## Step 2: Classify and draft (read-only, automatic)

1. For each candidate, get `vidiq_video_transcript`. **Classify by what is taught, not by the old title** (old titles were dates). If the subject isn't clearly a configured, enabled subject (it's Hindi/MAT while disabled, mixed, or there's no transcript), **skip and report it**.
2. **Check the answer.** If the teacher's spoken or chosen answer is wrong, hold the short back (don't schedule it) and list it in the report with wrong → correct. In the Oct 2026 run, 4 of 157 were wrong (cactus spines, Narmada→Ganga, 33.15, ₹120). Use on-screen options from the thumbnail (`https://i.ytimg.com/vi/<id>/hq720.jpg`, crop x 439–841) when the transcript is unclear.
3. Skip duplicates, meaning the same question recorded twice. Keep the first and report the rest.
4. Write `meta.tsv` (tab-separated, header row): `id kind subject old_title hook learn tag_hi tag_en`
   - `hook`: **Hindi in Roman script** (Raj, 28 Oct 2026). Start with 1 emoji, then a specific challenge or curiosity hook built from the actual question (numbers, names). Keep it short enough that hook + `title_suffix` ≤ 70 characters.
   - Optional `related_id` / `related_search`: the topic-matched **published long video** for this short (e.g. every fractions short → "Master Fractions in One Shot"). Leave blank to use the subject default.
   - Optional `keywords`: the `[…]` keyword block. Leave blank to auto-build it from the tags + `keyword_tail`.
   - `learn`: the concept in 2–5 Hindi words.
   - `tag_hi` / `tag_en`: one topic tag in each language.
   - Optional: `vidiq_keyword_research` on 1–2 head terms per subject, only to sanity-check tag wording.

## Step 3: Plan + ONE approval

```
python3 <skill>/scripts/plan.py meta.tsv --date <YYYY-MM-DD|auto> --mode <both|optimize|schedule> \
  --busy busy.txt --out plan.json [--slots EVS=17:00-23:00/60] [--playlist Maths=PLNkmnaUMEU24]
```

- Exit code 1 means a validation error (title > 70 characters, no `#shorts`, tags outside 10–15 or over 500 characters, or a banned phrase: PYQ, Free Level Check, free test, Class 9, …). Fix `meta.tsv` and re-run. Never show Raj a failing plan.
- **Playlist check:** make sure each `playlist_id` exists on the channel (Studio → Content → Playlists, `find` the links). If a name or ID isn't found, **ask. Never create a playlist.** Two playlists are named "Math • Shorts": always use `PLNkmnaUMEU24`.
- **CTA first:** if `seo.cta_top` is new or Raj asks to change it, show 2–3 CTA variants (AskUserQuestion with previews) and lock the one he picks into config before building the plan.
- Show **sample #1 in full** (title, description and tags exactly as they will be typed), then the table (`# | ID | Subj | old → new title | slot | playlist | related`), plus the skipped and held-back list. Ask **one** question: approve all / change something.
- Description layout (config `description_blocks`): 2-line blocks separated by `description_block_gap_lines` (2) blank lines: CTA → contact → hook+learn → subscribe → WhatsApp Channel → `[keywords]` → hashtags (last).
- After approval, **finish everything without further questions.** Only stop on a hard blocker: a missing playlist, a login wall, or the browser disconnecting.

## Step 4: Apply (writes)

**Path A: vidIQ (try once).** Call `vidiq_update_video` on the first item. If it succeeds, use it for all items (title, description, tags, privacy `private` + `publishAt`). Playlists still need Studio. If it returns `verification_required` / `youtube_mfa`, **don't retry, re-auth or ask for verification.** In Oct 2026 it failed every time, even after /mcp re-login. Go straight to Path B.

**Path B: YouTube Studio via Claude in Chrome.** This is the proven path. Follow `reference/studio-ui.md` exactly. In short:
- Load the chrome tools in one ToolSearch, call `tabs_context_mcp`, and make sure you're on the configured browser (`select_browser` if Studio shows "Oops", which means it silently switched browsers).
- vidIQ's Chrome extension must be **off on studio.youtube.com**. Its "Suggestions Apply" button and iframes catch stray clicks and break `javascript_tool`. If it's on, ask Raj once to disable it.
- Use one `browser_batch` per video, in slot order. Inside each batch: `find` refs, then title → description → playlist → tags → visibility/schedule → Save, then a verify `find`.
- **Never** call Studio's internal save API through JS (the safety classifier blocks it). Use UI clicks only.
- Keep `progress.tsv` (`id  status  slot  playlist`) up to date after every save, so a context reset or usage-limit pause resumes at the right row.

**Related video** (when Form 2 chose one for that subject): set it in the same per-video batch, using the picker recipe in `reference/studio-ui.md`. Search with the chosen video's title, and confirm the exact option before clicking.

## Step 5: Verify + report

1. Re-read 2–3 random videos plus the first and last of the run (Studio page `find`, or `vidiq_user_videos`). Check the title, tag count (`N/500`), visibility "Scheduled" with the right date and time, and the playlist.
2. Report table: `ID | subject | new title | IST slot | playlist | status`, followed by:
   - skipped, with the reason
   - held back for a wrong answer (wrong → correct)
   - errors hit and how each was fixed
   - anything Raj must do

   Offer the held-back list as a team-review PDF (thumbnail, link, wrong vs correct). Raj wants PDFs by default.
3. Update the memory file `quantum-school-shorts-scheduling.md` with the date range scheduled.

## Hard rules

- One approval table before any write; then no more questions.
- Never change privacy of already-public videos. Never create a playlist. Never touch videos outside the approved table.
- Skip and report shorts that aren't clearly a configured subject. Hold back wrong-answer shorts.
- SEO: Hindi-first, ≤70 characters, end with `#shorts`, 10–15 tags, the fixed hashtags plus the subject hashtag, Class 6 and Class 9 never mixed, स्मृति-आधारित/पैटर्न-आधारित instead of PYQ, and never promise a Free Level Check or free test.
- All times come from `scripts/slots.py` / `plan.py`. Never compute them by hand.
