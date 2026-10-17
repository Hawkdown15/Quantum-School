# Session analysis: Quantum School shorts run, 16–17 Oct 2026

## Steps in order
| # | Step | Tool |
|---|---|---|
| 1 | Confirm the channel and vidIQ connection | `vidiq-qs__vidiq_user_channels`, `vidiq_connect_youtube_channel`, `vidiq_balance` |
| 2 | List all videos (privacy, schedule, duration) | `vidiq-qs__vidiq_user_videos` (read works) |
| 3 | Read every unpublished short (157) to classify subject and check the answer | `vidiq-qs__vidiq_video_transcript` (~174 calls) |
| 4 | Keyword sanity check for tags | `vidiq_keyword_research`; `vidiq_generate_titles` tried but not used |
| 5 | Classification → `notes.tsv`; hook/learn/tags → `meta.tsv` | written by hand |
| 6 | Build titles, descriptions, tags and IST→UTC slots | `build.py` → `plan.json`, `plan_sorted.json` |
| 7 | Approval table (150 rows) | `approval_table.md`, then Raj said "OK" |
| 8 | Write via vidIQ | `vidiq_update_video` ×14 → all `verification_required` |
| 9 | Re-auth attempts | `vidiq_authorize_with_youtube`, `/mcp` re-login (no effect) |
| 10 | Switch to the Studio UI | Claude in Chrome: `browser_batch` (~920), `find`, `computer`, `navigate`, `select_browser` |
| 11 | Per short: title, description, playlist, tags, schedule, save, verify | Studio edit page |
| 12 | Add the 7 Maths shorts from day 1 to Math • Shorts | Studio |
| 13 | Related video on all 150 (EVS → Y-cqZo-FCI8, Maths → -QLsPTrQMys) | Studio related-video picker |
| 14 | Final report, plus memory update | `vidiq_user_videos` re-check |
| 15 | Wrong-answer review PDF for the team | thumbnails via i.ytimg.com, headless Chrome PDF |

## Inputs (given vs assumed)
- **Given by Raj:** channel + Studio URL; start "today, 16 Oct"; EVS 17:00–23:00 and Maths 17:30–23:30, 7 per subject per day with overflow; playlists "EVS • Shorts" and "the first Math • Shorts" (Studio links PLNkmnaUMEU24 / PLJiwh-0GtG6Y); "lean pipeline"; use Studio in Chrome on Browser 1; skip related videos, then later add them one per subject.
- **Assumed:** 60-min interval; all unscheduled private/unlisted shorts; subject from the transcript, not the title; long videos metadata-only; Studio time zone GMT+05:30 = IST; related videos = the top long video per subject by views.

## Errors, retries and fixes
| Problem | Fix |
|---|---|
| vidIQ `update_video` → `verification_required` (youtube_mfa) every time, even after re-auth and /mcp re-login | Abandoned; Studio UI instead |
| vidIQ extension in Studio: iframe errors, `javascript_tool` blocked, "Leave site?" dialog | Raj turned the extension off; new tab |
| JS call to Studio's internal save endpoint | Blocked by the safety classifier; UI clicks only |
| Playlist picker reorders by recency, so an EVS short went into Math | Pick by name and zoom-verify before Done |
| Hashtag popup reverted titles (#26, 27, 29, 43 → "#shortsbeta"); description once pasted into title | Trailing space after `#shorts`; title by `find` ref; verify after save |
| Coordinate click missed after a page scroll | Always use `find` refs for fields |
| Visibility panel didn't open, so stray clicks wiped tags | Open visibility first, wait, zoom-check; tag counter check after each save |
| Old tags present (e.g. 396/500) | "Delete all" first |
| Clicking a ticked playlist un-ticked it | Read playlist state before clicking |
| Session switched to Browser 2 ("Oops") | `select_browser` back to Browser 1 |
| "Cannot save until errors are resolved" (#43) | Fixed the flagged field |
| `find` rate limit; usage-limit pauses; context resets | Pause/resume from `progress.tsv` |
| Related picker: panel jump, typing lost, default grid picked a short (2 cases) | Heading no-op click; double-click the search box; `find` the exact option; bin then re-pick |
| Stray click hit vidIQ "Suggestions Apply" on 5X5v76uE0Yk (description + 3 tags) | Description restored; tags kept (15) |

## Approval vs automatic
- **Approval asked:** pipeline choice, start date, playlists, the 150-row plan table, switching to Studio, browser choice, related-video scope.
- **Automatic:** fetching, transcripts, classification, drafting, slot maths, every Studio save after approval, verification, report.
- **Raj had to act:** vidIQ verification attempts (no effect), turning off the vidIQ extension, dismissing a browser dialog, /login after the usage limit.

## SEO rules used
- Title: `<Hindi hook question> | JNVST EVS #shorts` or `| JNVST Maths #shorts`, ≤70 characters, Hindi-first, specific (numbers, names).
- Description: hook → "इस short में सीखें: <learn>, JNVST Class 6 <subject> के अंदाज़ में, स्टेप बाय स्टेप।" → daily-practice line → Subscribe/@quantumschool45 CTA → `#JNVST #NavodayaVidyalaya #QuantumSchool #NavodayaEVS|#NavodayaMaths #shorts`.
- Tags: 10 subject base tags + 1 Hindi + 1 English topic tag = 12 (limits 10–15, ≤500 characters).
- Class 6 only (never mix with Class 9); no "PYQ" (use स्मृति-आधारित / पैटर्न-आधारित); no free-test or Free Level Check promise; no selection claims.

## Outcome
150 scheduled (62 EVS, 88 Maths, 16–28 Oct) and playlisted, with related videos set. Held back for wrong answers: AVP5oRQLCA0, tyWVXCkxAEo, CQ0WJATP_yI, Ecu1IdQpZfY. Duplicates: vd9CZd43AJ0, 5RzUNINq39o. Unclear: WsKBw0gwnpE. Left alone: BwlWwfOa13M, rUMJo6qzEN4 (already scheduled), long video U2bUikV7wbs.
