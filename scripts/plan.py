#!/usr/bin/env python3
"""Build the full plan (title/description/tags/slot/playlist) from meta.tsv and print the approval table.

meta.tsv columns (tab-separated, header row):
  id  kind(short|long)  subject  old_title  hook  learn  tag_hi  tag_en  [related_id  related_search  keywords]
  - keywords (optional): comma list for the [..] block; blank = tag_en, tag_hi, learn + subject keyword_tail.
  - related_id/related_search (optional): the topic-matched published long video for this short;
    blank = the subject's default from config.
  - subject must be a configured+enabled subject, else the row is SKIPPED and reported.
  - kind=long rows get metadata only: no slot, no playlist, no privacy change.

  python3 plan.py meta.tsv --date auto --out plan.json [--mode both|optimize|schedule]
             [--slots EVS=17:00-23:00/60] [--playlist Maths=PLNkmnaUMEU24] [--extra-tags "a,b"] [--extra-hashtags "#X #Y"] [--desc-extra "line"] [--now 2026-10-17T10:00] [--busy busy.txt]
Exits non-zero if any row fails validation (title length, banned phrase, tag count/chars).
"""
import argparse, csv, json, re, sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slots import assign, default_date, load_busy, load_channel, parse_slot_override, resolve_specs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("meta")
    ap.add_argument("--channel")
    ap.add_argument("--date", default="auto")
    ap.add_argument("--mode", default="both", choices=["both", "optimize", "schedule"])
    ap.add_argument("--slots", action="append", default=[])
    ap.add_argument("--playlist", action="append", default=[], help="SUBJ=PLAYLIST_ID")
    ap.add_argument("--extra-tags", default="", help="comma list added to every video's tags")
    ap.add_argument("--extra-hashtags", default="", help="space/comma list added before #shorts")
    ap.add_argument("--desc-extra", default="", help="extra block (e.g. the WhatsApp Channel line); \\n = line break")
    ap.add_argument("--now")
    ap.add_argument("--busy", help="file of already-scheduled UTC publishAt values to avoid")
    ap.add_argument("--out", default="plan.json")
    a = ap.parse_args()

    key, ch = load_channel(a.channel)
    tz, seo = ZoneInfo(ch["timezone"]), ch["seo"]
    now = datetime.fromisoformat(a.now).replace(tzinfo=tz) if a.now else datetime.now(tz)
    rows = list(csv.DictReader(open(a.meta, encoding="utf-8"), delimiter="\t"))
    pl_over = dict(p.split("=", 1) for p in a.playlist)

    ok, skipped, errors = [], [], []
    for r in rows:
        subj = (r.get("subject") or "").strip()
        conf = ch["subjects"].get(subj)
        if not conf or not conf.get("enabled"):
            skipped.append((r["id"], subj or "?", "subject not configured/enabled"))
            continue
        ok.append((r, subj, conf))

    shorts_by_subj = {}
    for r, subj, _ in ok:
        if (r.get("kind") or "short") == "short":
            shorts_by_subj.setdefault(subj, []).append(r["id"])

    slot_map = {}
    if a.mode in ("both", "schedule") and shorts_by_subj:
        specs = resolve_specs(ch, list(shorts_by_subj), dict(parse_slot_override(s) for s in a.slots))
        if a.date == "auto":
            start = default_date(specs, tz, now)
        elif a.date in ("today", "tomorrow"):
            start = now.date() + timedelta(days=a.date == "tomorrow")
        else:
            start = date.fromisoformat(a.date)
        for subj, ids in shorts_by_subj.items():
            for vid, (loc, utc) in zip(ids, assign(len(ids), specs[subj], start, tz, now, busy=load_busy(a.busy))):
                slot_map[vid] = (loc, utc)
    else:
        start = None

    banned = [b.lower() for b in seo.get("banned_phrases", [])]
    plan = []
    for r, subj, conf in ok:
        item = {"videoId": r["id"], "kind": r.get("kind") or "short", "subject": subj, "old_title": r.get("old_title", "")}
        if a.mode in ("both", "optimize"):
            title = r["hook"].strip() + conf["title_suffix"]
            kw = (r.get("keywords") or "").strip()
            if not kw:
                learn_kw = re.sub(r"[()]", "", r["learn"]).strip()
                parts = [r["tag_en"].strip(), r["tag_hi"].strip()]
                if not any(p_.lower() in learn_kw.lower() for p_ in parts if p_): parts.append(learn_kw)
                kw = ", ".join(dict.fromkeys(x for x in parts if x))
            kw = ", ".join(x for x in [kw, conf.get("keyword_tail", "")] if x)
            extra_h = [h if h.startswith("#") else "#" + h for h in re.split(r"[\s,]+", a.extra_hashtags) if h.strip("#")]
            fill = dict(cta=seo.get("cta_top", ""), hook=r["hook"].strip(), learn=r["learn"].strip(), keywords=kw,
                        extra=a.desc_extra.replace("\\n", "\n").strip(), subject_label=conf["desc_subject_label"],
                        subject_hashtag=" ".join([conf["subject_hashtag"]] + extra_h))
            gap = "\n" * (seo.get("description_block_gap_lines", 1) + 1)
            blocks = [b.format(**fill).strip() for b in seo["description_blocks"]]
            desc = gap.join(b.replace("\n\n", gap) for b in blocks if b and b != "[]")
            if len(desc) > 5000: errors.append((r["id"], f"description {len(desc)} chars"))
            extra_t = [t.strip() for t in a.extra_tags.split(",") if t.strip()]
            tags = list(dict.fromkeys(conf["base_tags"] + [r["tag_hi"].strip(), r["tag_en"].strip()] + extra_t))
            tags = [t for t in tags if t]
            item.update(title=title, description=desc, tags=tags)
            if len(title) > seo["title_max_chars"]: errors.append((r["id"], f"title {len(title)} chars"))
            if not title.rstrip().endswith(seo["title_must_end_with"]): errors.append((r["id"], "title must end with #shorts"))
            if not seo["tags_min"] <= len(tags) <= seo["tags_max"]: errors.append((r["id"], f"{len(tags)} tags"))
            if len(",".join(tags)) > seo["tags_max_chars"]: errors.append((r["id"], "tags > 500 chars"))
            blob = (title + " " + desc + " " + " ".join(tags)).lower()
            for b in banned:
                if re.search(r"(?<!\w)" + re.escape(b) + r"(?!\w)", blob): errors.append((r["id"], f"banned phrase '{b}'"))
        if item["kind"] == "short":
            item["related_video_id"] = (r.get("related_id") or "").strip() or conf.get("related_video_id", "")
            item["related_video_search"] = (r.get("related_search") or "").strip() or conf.get("related_video_search", "")
        if r["id"] in slot_map:
            loc, utc = slot_map[r["id"]]
            item.update(publishAt=utc, ist=loc.strftime("%d %b %H:%M"),
                        studio_date=loc.strftime("%b %-d, %Y"), studio_time=loc.strftime("%-I:%M %p"),
                        playlist_name=conf["playlist_name"], playlist_id=pl_over.get(subj, conf["playlist_id"]))
            item["_sort"] = loc
        plan.append(item)

    plan.sort(key=lambda i: (i.get("_sort") is None, i.get("_sort") or 0))
    for i in plan: i.pop("_sort", None)
    Path(a.out).write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"channel={key} mode={a.mode} start={start} planned={len(plan)} skipped={len(skipped)} -> {a.out}\n")
    print("| # | ID | Subj | Old title → New title | Slot (local) | Playlist | Related |\n|---|---|---|---|---|---|---|")
    for n, i in enumerate(plan, 1):
        old = (i["old_title"] or "—")[:40]
        new = i.get("title", "(unchanged)").replace("|", "\\|")
        print(f"| {n} | {i['videoId']} | {i['subject']} | {old} → {new} | {i.get('ist', 'no change' if i['kind']=='long' else '—')} | {i.get('playlist_name', '—')} | {i.get('related_video_id') or '—'} |")
    if skipped:
        print("\nSKIPPED:")
        for s in skipped: print(f"- {s[0]} ({s[1]}): {s[2]}")
    if errors:
        print("\nVALIDATION ERRORS (fix meta.tsv, re-run):")
        for e in errors: print(f"- {e[0]}: {e[1]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
