"""Records for this morning: a classic and a modern classic, picked once a day.

The catalogs are records_classic.txt and records_modern.txt (year | artist | album | tags). Every pick is
written to a history that lives in state.json on the data branch, and an album is only picked again once
more than a year has passed since it was last recommended. Tags match the day: season, weather, holidays.
"""
import datetime as dt
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request

HERE = os.path.dirname(__file__)
UA = {"User-Agent": "solar-dashboard/1.0 (personal home dashboard; github.com/phallpdx/solar-dashboard)"}
REPEAT_AFTER_DAYS = 365  # an album comes back only when it was last recommended more than this many days ago
CLASSIC_AGE = 15         # "the classic" is over this many years old; newer records are modern classics
HISTORY_DAYS = 800


def load_catalog():
    out, seen = [], set()
    for name in ("records_classic.txt", "records_modern.txt"):
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                year, artist, album, tags = (x.strip() for x in (line.split("|") + [""])[:4])
                k = key(artist, album)
                if k in seen:
                    continue
                seen.add(k)
                out.append({"artist": artist, "album": album, "year": int(year), "tags": tags.split()})
    return out


def load_notes():
    with open(os.path.join(HERE, "records_notes.json"), encoding="utf-8") as f:
        return json.load(f)


def key(artist, album):
    return f"{artist} | {album}".lower().replace("’", "'")


def day_tags(today, day=None, moon_lit=None, elections=(), thai=()):
    """How well each tag suits today. Same idea as the page used to do, now done once a day here."""
    m, d = today.month, today.day
    tags = {"any": 0.1, "local": 0.5}
    tags["winter" if m in (12, 1, 2) else "spring" if m <= 5 else "summer" if m <= 8 else "fall"] = 1
    if day:
        if (day.get("rain_pct") or 0) >= 60:
            tags["rain"] = 2
        if (day.get("snow_in") or 0) > 0.2:
            tags["snow"] = 3
        if (day.get("rain_pct") or 0) < 20 and (day.get("hi") or 0) >= 70:
            tags["sun"] = 2
    if moon_lit is not None and moon_lit >= 97:
        tags["full"] = 2
    if today.weekday() == 6:
        tags["sunday"] = 2
    if m == 10 and d >= 18:
        tags["halloween"] = 4
    if m == 12 and d <= 26:
        tags["xmas"] = 4
    if m == 11 and 18 <= d <= 28:
        tags["thanks"] = 3
    if (m == 12 and d >= 28) or (m == 1 and d <= 3):
        tags["newyear"] = 3
    if m == 2 and 10 <= d <= 14:
        tags["valentine"] = 4
    if m in (3, 9) and 19 <= d <= 23:
        tags["equinox"] = 3
    if any(0 <= (dt.date.fromisoformat(e["date"]) - today).days <= 9 for e in elections):
        tags["election"] = 3
    if any(t.get("date") == today.isoformat() for t in thai):
        tags["thai"] = 3
    return tags


def last_picked(history):
    last = {}
    for h in history:
        k = key(h["artist"], h["album"])
        last[k] = max(last.get(k, ""), h["date"])
    return last


def choose(pool, tags, last, today, salt, boost=None, spare=()):
    """Best-fitting record for today among those not recommended in the past year.

    When this slot's pool runs dry it borrows from `spare` (the rest of the catalog) before it would ever
    repeat; only if the whole catalog was used within the year does the longest-ago record come back."""
    def fresh(r):
        when = last.get(key(r["artist"], r["album"]))
        return not when or (today - dt.date.fromisoformat(when)).days > REPEAT_AFTER_DAYS
    eligible = [r for r in pool if fresh(r)] or [r for r in spare if fresh(r)]
    if not eligible:
        everything = list(pool) + list(spare)
        eligible = sorted(everything, key=lambda r: last.get(key(r["artist"], r["album"]), ""))[:20]
    def score(r):
        return sum(tags.get(t, 0) for t in r["tags"]) + (boost or {}).get(r["artist"].lower(), 0)
    scored = sorted(((score(r), r) for r in eligible), key=lambda x: -x[0])
    best = scored[0][0]
    shortlist = [r for s, r in scored if s >= best - 1]
    seed = int(hashlib.sha256(f"{today.isoformat()}:{salt}".encode()).hexdigest(), 16)
    return shortlist[seed % len(shortlist)]


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)


def wiki_about(artist, album, year):
    """A sentence or two about the album from its Wikipedia article, and the link, so every note has a source."""
    q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": f'"{album}" {artist} album',
                                "srlimit": 4, "format": "json"})
    hits = _get("https://en.wikipedia.org/w/api.php?" + q)["query"]["search"]
    surname = re.sub(r"^the ", "", artist.lower()).split()[-1].strip(".,'")
    for h in hits:
        s = _get("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(h["title"].replace(" ", "_")))
        text, desc = s.get("extract") or "", (s.get("description") or "").lower()
        if s.get("type") != "standard" or not ("album" in desc or "album" in text[:200].lower() or "soundtrack" in desc):
            continue
        if surname not in (text + " " + desc).lower():
            continue
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        why = sentences[0]
        for extra in sentences[1:3]:
            if len(why) + len(extra) > 300:
                break
            why += " " + extra
        return {"why": why, "url": (s.get("content_urls") or {}).get("desktop", {}).get("page"),
                "image": (s.get("thumbnail") or {}).get("source")}
    return None


def daily_picks(store, today, day=None, moon_lit=None, elections=(), thai=(), shows=()):
    """Today's two records. Picked on the first run of the day and kept all day; the history only grows."""
    t = today.isoformat()
    if (store.get("today") or {}).get("date") == t:
        for slot in ("classic", "modern"):  # the Wikipedia lookup failed earlier: try again
            r = store["today"].get(slot) or {}
            if r and not r.get("url"):
                try:
                    about = wiki_about(r["artist"], r["album"], r["year"]) or {}
                    r.update(about=about.get("why"), url=about.get("url"), image=about.get("image"), why=r.get("why") or about.get("why") or "")
                except Exception:
                    pass
        return store["today"]
    catalog, notes = load_catalog(), load_notes()
    history = [h for h in store.get("history") or [] if h["date"] < t]
    last = last_picked(history)
    tags = day_tags(today, day, moon_lit, elections, thai)
    classic = [r for r in catalog if today.year - r["year"] > CLASSIC_AGE]
    modern = [r for r in catalog if today.year - r["year"] <= CLASSIC_AGE]
    # A modern pick whose artist plays Portland this week beats the calendar.
    soon = {s["artist"].lower(): s for s in shows if s.get("date") and 0 <= (dt.date.fromisoformat(s["date"]) - today).days < 7}
    picks = {"date": t, "why": sorted(k for k, v in tags.items() if v >= 2)}
    for slot, pool, salt, boost in (("classic", classic, 0, None), ("modern", modern, 3, {a: 50 for a in soon})):
        taken = {key(picks[x]["artist"], picks[x]["album"]) for x in ("classic", "modern") if x in picks}
        r = choose([x for x in pool if key(x["artist"], x["album"]) not in taken], tags, last, today, salt, boost,
                   [x for x in catalog if x not in pool and key(x["artist"], x["album"]) not in taken])
        about = None
        try:
            about = wiki_about(r["artist"], r["album"], r["year"])
        except Exception:
            pass
        picks[slot] = {"artist": r["artist"], "album": r["album"], "year": r["year"],
                       "why": notes.get(key(r["artist"], r["album"])) or (about or {}).get("why") or "",
                       "about": (about or {}).get("why"), "url": (about or {}).get("url"), "image": (about or {}).get("image"),
                       "last_picked": last.get(key(r["artist"], r["album"]))}
        history.append({"date": t, "slot": slot, "artist": r["artist"], "album": r["album"]})
        if slot == "modern" and r["artist"].lower() in soon:
            s = soon[r["artist"].lower()]
            picks["live"] = {"venue": s.get("venue"), "date": s.get("date"), "tickets": s.get("tickets")}
    cutoff = (today - dt.timedelta(days=HISTORY_DAYS)).isoformat()
    store["history"] = [h for h in history if h["date"] >= cutoff]
    store["today"] = picks
    return picks
