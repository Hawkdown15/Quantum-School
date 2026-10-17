# YouTube Studio recipe (Claude in Chrome)

Proven on 150 shorts, 16–17 Oct 2026, with a 1568×783 frame. Coordinates are hints only. Always use `find` refs where possible and confirm each step with a `zoom`.

## Before the first video
- Load all needed chrome tools in ONE ToolSearch: tabs_context_mcp, navigate, computer, find, browser_batch, select_browser, read_page.
- Edit page: `https://studio.youtube.com/video/<ID>/edit`. Wait 6 s after navigating.
- vidIQ extension OFF for studio.youtube.com, or you get iframe errors, "Leave site?" dialogs and the stray "Suggestions Apply" button. If a "Leave site?" dialog appears, ask Raj to dismiss it and continue in a new tab.
- Studio shows "Oops" or a different account: the session switched to Browser 2. Fix with `select_browser` back to the configured browser.
- Studio's scheduling time zone defaults to local GMT+05:30, which matches IST. Type local times exactly as `plan.json` → `studio_time` gives them.

## Per-video batch (one `browser_batch` per video)
1. `find` "title textbox, description textbox, tags input, visibility button, playlists dropdown". Use these refs, never raw coordinates for text fields: a page scroll makes coordinate clicks miss.
2. **Title:** click the ref, `cmd+a`, type the title **with a trailing space after `#shorts`**. Without the space, the hashtag autocomplete popup opens and a click-away reverts or mangles the title (it became "#shortsbeta"). Don't press Escape.
3. **Description:** click the ref, `cmd+a`, type it, ending `#shorts ` (trailing space, same reason).
4. **Playlist:** scroll_to and click the playlists ref, wait 2 s. The picker reorders by most-recently-used, so `find` the checkbox **by exact name**; for Maths, use the first "Math • Shorts" (`PLNkmnaUMEU24`). Zoom to confirm the tick. Clicking an already-ticked playlist UN-ticks it, so read its state first. Click Done, then **wait 1 s** before anything else.
5. **Tags:** scroll_to the tags ref. If old tags exist (the counter shows more than 0/500), use the field's "Delete all" first. Type tags comma-separated, ending with a trailing comma.
6. **Visibility / schedule:** open visibility first and wait 2 s. Expand "Schedule", click the date button, pick the date, click the time box, `cmd+a`, type e.g. `5:30 PM`, Return. Done. A blank zoom here means the panel didn't open: stop, because any further clicks land on the page and can wipe the tags.
7. **Save** (top right). Wait 5 s.
8. **Verify** with `find`: title text, tag counter `N/500`, visibility "Scheduled <date> <time>", playlist value. Then append to `progress.tsv`.

## Errors seen and the fix
| Error | Fix |
|---|---|
| vidIQ `update_video` → `verification_required` (youtube_mfa), even after /mcp re-auth | Don't retry. Use the Studio UI. |
| `javascript_tool`: "Cannot access a chrome-extension:// URL" | The vidIQ extension is injected. Turn it off, or don't use JS. |
| Internal save API via JS | Blocked by the safety classifier. Never attempt it. |
| Wrong playlist (recency reorder) | Pick by exact name and zoom to verify before Done. |
| Title reverted / "#shortsbeta" / description pasted into title | Trailing space after `#shorts`; title by ref; re-verify after save. |
| "Cannot save until errors are resolved" | Read the red field (usually title >100 or a bad tag), fix it, save. |
| Tags wiped | Caused by stray clicks after a visibility panel that didn't open. Re-type the tags; check `N/500` after every save. |
| `find` rate limit | Pause until the reset. `progress.tsv` tells you where to resume. |
| Usage limit / context reset mid-run | Resume from `progress.tsv`. Never redo DONE rows. |
| Panel jumps on the first click after page load (related-video picker) | Click the "Video details" heading once (a no-op), then scroll_to the field. |

## Related video (optional)
- If the field shows **None**, there's a pencil icon. If a video is already set, there's a bin icon: click the bin first, and the pencil appears.
- Pencil → "Choose specific video" dialog. `find` the search box (if it isn't found, the dialog didn't open, so abort this video). Click the search box twice, type the config's `related_video_search`, wait 4 s. `find` the exact option title before clicking it. **Never** click the default grid: it picked a short by mistake twice.
- Zoom to confirm the title, then Save.
