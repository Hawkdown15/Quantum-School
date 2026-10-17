#!/usr/bin/env python3
"""IST (channel-timezone) slots -> UTC publishAt, with past-slot skipping and next-day overflow.

  python3 slots.py --date auto --count EVS=7 --count Maths=9
  python3 slots.py --date 2026-10-18 --count EVS=3 --slots EVS=18:00-21:00/30
  python3 slots.py --default-date                 # just print the default date

Rules:
- Slots run start..end inclusive every interval_min (from config unless --slots overrides).
- A slot is usable only if it is >= now + --buffer minutes (default 15). Past ones are skipped.
- Slots listed in --busy (already-scheduled publishAt, UTC) are skipped too.
- Video k of a subject takes the k-th usable slot; when a day's slots run out, it overflows to
  the next day at the same slots.
- --date auto = today if the earliest first slot of the chosen subjects is 30+ min away, else tomorrow.
"""
import argparse, json, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CONFIG = Path(__file__).resolve().parent.parent / "config.json"


def load_channel(key=None):
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    key = key or cfg["default_channel"]
    return key, cfg["channels"][key]


def parse_slot_override(s):
    # "EVS=17:00-23:00/60"  (window)   or   "EVS=17:15,18:40,21:00"  (exact custom times)
    subj, rest = s.split("=", 1)
    if "-" not in rest:
        times = sorted({t.strip().zfill(5) for t in rest.split(",") if t.strip()})
        for t in times:
            h, m = map(int, t.split(":"))
            assert 0 <= h < 24 and 0 <= m < 60, f"bad time {t}"
        return subj, {"times": times}
    rng, _, iv = rest.partition("/")
    start, end = rng.split("-")
    return subj, {"start": start, "end": end, "interval_min": int(iv or 60)}


def day_slots(spec):
    if spec.get("times"):
        return [tuple(map(int, t.split(":"))) for t in spec["times"]]
    if not spec.get("start") or not spec.get("end"):
        raise SystemExit("slot window not configured for this subject: pass --slots SUBJ=HH:MM-HH:MM/MIN")
    h1, m1 = map(int, spec["start"].split(":"))
    h2, m2 = map(int, spec["end"].split(":"))
    t, end, out = h1 * 60 + m1, h2 * 60 + m2, []
    while t <= end:
        out.append((t // 60, t % 60))
        t += int(spec["interval_min"])
    return out


def default_date(specs, tz, now=None, lead_min=30):
    now = now or datetime.now(tz)
    first = min(day_slots(s)[0] for s in specs.values())
    first_dt = datetime.combine(now.date(), datetime.min.time(), tz).replace(hour=first[0], minute=first[1])
    return now.date() if first_dt - now >= timedelta(minutes=lead_min) else now.date() + timedelta(days=1)


def load_busy(path):
    """One UTC publishAt per line (already-scheduled videos on the channel). Those slots are skipped."""
    if not path: return set()
    return {l.strip() for l in open(path) if l.strip()}


def assign(count, spec, start_date, tz, now=None, buffer_min=15, busy=frozenset()):
    """Return [(local_dt, utc_iso)] for `count` videos."""
    now = now or datetime.now(tz)
    cutoff = now + timedelta(minutes=buffer_min)
    slots, out, d = day_slots(spec), [], start_date
    while len(out) < count:
        for h, m in slots:
            local = datetime(d.year, d.month, d.day, h, m, tzinfo=tz)
            if local < cutoff:
                continue  # skip past / too-soon slots
            utc = local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if utc in busy:
                continue  # slot already taken by a scheduled video
            out.append((local, utc))
            if len(out) == count:
                break
        d += timedelta(days=1)  # overflow to next day, same slots
    return out


def resolve_specs(ch, subjects, overrides):
    specs = {}
    for s in subjects:
        if s in overrides:
            specs[s] = overrides[s]
        else:
            if s not in ch["subjects"]:
                raise SystemExit(f"unknown subject {s!r}; configured: {list(ch['subjects'])}")
            specs[s] = ch["subjects"][s]["slots"]
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel")
    ap.add_argument("--date", default="auto", help="YYYY-MM-DD | today | tomorrow | auto")
    ap.add_argument("--count", action="append", default=[], help="SUBJ=N")
    ap.add_argument("--slots", action="append", default=[], help="SUBJ=HH:MM-HH:MM/MIN or SUBJ=HH:MM,HH:MM,...")
    ap.add_argument("--buffer", type=int, default=15)
    ap.add_argument("--busy", help="file of already-scheduled UTC publishAt values to avoid")
    ap.add_argument("--now", help="fake current time for testing, YYYY-MM-DDTHH:MM (channel tz)")
    ap.add_argument("--default-date", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    key, ch = load_channel(a.channel)
    tz = ZoneInfo(ch["timezone"])
    now = datetime.fromisoformat(a.now).replace(tzinfo=tz) if a.now else datetime.now(tz)
    overrides = dict(parse_slot_override(s) for s in a.slots)
    counts = {c.split("=")[0]: int(c.split("=")[1]) for c in a.count}
    subjects = list(counts) or [s for s, v in ch["subjects"].items() if v.get("enabled")]
    specs = resolve_specs(ch, subjects, overrides)

    if a.date == "auto":
        start = default_date(specs, tz, now)
    elif a.date == "today":
        start = now.date()
    elif a.date == "tomorrow":
        start = now.date() + timedelta(days=1)
    else:
        start = date.fromisoformat(a.date)

    if a.default_date:
        print(start.isoformat()); return

    rows = []
    for s in subjects:
        for i, (loc, utc) in enumerate(assign(counts.get(s, 0), specs[s], start, tz, now, a.buffer, load_busy(a.busy)), 1):
            rows.append({"subject": s, "n": i, "ist": loc.strftime("%d %b %H:%M"),
                         "studio_date": loc.strftime("%b %-d, %Y"), "studio_time": loc.strftime("%-I:%M %p"),
                         "publishAt": utc, "_sort": loc})
    rows.sort(key=lambda r: r["_sort"])
    for r in rows: r.pop("_sort")
    if a.json:
        json.dump({"channel": key, "start_date": start.isoformat(), "slots": rows}, sys.stdout, ensure_ascii=False, indent=1)
    else:
        print(f"channel={key} tz={ch['timezone']} start={start}")
        print("| subj | # | local slot | Studio date | Studio time | publishAt (UTC) |\n|---|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['subject']} | {r['n']} | {r['ist']} | {r['studio_date']} | {r['studio_time']} | {r['publishAt']} |")


if __name__ == "__main__":
    main()
