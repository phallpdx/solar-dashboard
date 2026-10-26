"""The date and the place: today in history and holidays (Wikipedia's On This Day feed), notable places
near home (Wikipedia geosearch), and recent Columbia Gorge trip reports (Washington Trails Association)."""
import datetime as dt
import html
import json
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard/1.0 (personal home dashboard; github.com/phallpdx/solar-dashboard)"}
WIKI = "https://en.wikipedia.org"
LOCAL = re.compile(r"\b(Oregon|Portland|Columbia River|Willamette|Mount Hood|Mount St\. Helens|Pacific Northwest|Washington \(state\)|Vancouver, Washington|Astoria)\b")
# Washington-side Columbia Gorge hikes near Portland (WTA covers Washington trails only).
HIKES = [("dog-mountain", "Dog Mountain"), ("hamilton-mountain", "Hamilton Mountain"),
         ("beacon-rock", "Beacon Rock"), ("cape-horn", "Cape Horn"), ("coyote-wall-labyrinth-loop", "Coyote Wall")]
WTA = "https://www.wta.org/go-hiking/hikes/"


def _get(url, as_json=True):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        body = resp.read().decode("utf-8", "replace")
    return json.loads(body) if as_json else body


def _page(p):
    return {"title": (p.get("titles") or {}).get("normalized") or p.get("title", "").replace("_", " "),
            "summary": p.get("extract") or p.get("description"),
            "url": ((p.get("content_urls") or {}).get("desktop") or {}).get("page"),
            "image": (p.get("thumbnail") or {}).get("source")}


def _entry(x):
    pages = [_page(p) for p in x.get("pages") or []]
    return {"year": x.get("year"), "text": x.get("text"), "page": pages[0] if pages else None,
            "local": bool(LOCAL.search(" ".join([x.get("text") or ""] + [p["summary"] or "" for p in pages[:2]])))}


# Today in history leans fun: wars, crimes and disasters are left out, and firsts, inventions, music,
# film, sport and space float to the top.
GRIM = re.compile(r"\b(war|wars|battle|killed|kills|killing|murder\w*|massacre\w*|bomb\w*|attack\w*|invad\w*|invasion|"
                  r"execut\w*|assassinat\w*|shot|shooting|genocide|siege|terror\w*|crash\w*|disaster|dead|deaths?|died|"
                  r"fatal\w*|hostage\w*|riot\w*|coup|troops|army|armies|military|soldiers|surrender\w*|bombard\w*|"
                  r"sinks?|sank|collapse\w*|explosion|hurricane|famine|plague|lynch\w*|kidnap\w*|prison|arrested)\b", re.I)
FUN = re.compile(r"\b(first|invent\w*|patent\w*|record|released?|premiere\w*|album|single|song|film|movie|opens?|opened|"
                 r"founded|discover\w*|launch\w*|space|moon|orbit|world series|championship|wins?|won|olympic\w*|"
                 r"television|radio|broadcast|computer|internet|video game|comic|novel|published|museum|zoo|festival|"
                 r"debut\w*|unveil\w*|introduc\w*|world's|tallest|largest)\b", re.I)


def _cheerful(x):
    return not GRIM.search(x["text"] or "") and not GRIM.search(((x["page"] or {}).get("summary") or "")[:200])


def _fun(x):
    return len(FUN.findall(x["text"] or "")) + (2 if x["local"] else 0)


def on_this_day(day):
    """Lighter events, births and holidays for this calendar date. Local ones are flagged."""
    data = _get(f"{WIKI}/api/rest_v1/feed/onthisday/all/{day.month:02d}/{day.day:02d}")
    events = [_entry(x) for x in (data.get("selected") or []) + (data.get("events") or [])]
    births = [_entry(x) for x in data.get("births") or []]
    pool, seen = [], set()
    for x in events:
        if x["text"] not in seen and _cheerful(x):
            seen.add(x["text"])
            pool.append(x)
    pool.sort(key=lambda x: -_fun(x))
    local = [x for x in pool + births if x["local"]][:5]
    return {
        "v": 2,
        "date": day.isoformat(),
        "selected": sorted([x for x in pool if not x["local"]][:8], key=lambda x: x["year"] or 0),
        "local": local,
        "births": sorted(births, key=lambda x: -(x["year"] or 0))[:6],
        "deaths": [],
        "holidays": [{"text": x.get("text"), "page": _page(x["pages"][0]) if x.get("pages") else None}
                     for x in data.get("holidays") or []][:10],
    }


def date_facts(day):
    """What's special about the date that needs no API: day of year, season turns, and a few fun ones."""
    start = dt.date(day.year, 1, 1)
    leap = day.year % 4 == 0 and (day.year % 100 != 0 or day.year % 400 == 0)
    total = 366 if leap else 365
    n = (day - start).days + 1
    facts = [f"Day {n} of {total}, so {100 * n / total:.0f}% of {day.year} is behind you."]
    # Approximate dates; they move by a day at most.
    turns = [(dt.date(day.year, 3, 20), "the spring equinox"), (dt.date(day.year, 6, 21), "the summer solstice"),
             (dt.date(day.year, 9, 22), "the fall equinox"), (dt.date(day.year, 12, 21), "the winter solstice"),
             (dt.date(day.year + 1, 3, 20), "the spring equinox")]
    nxt = next((d, name) for d, name in turns if d >= day)
    gap = (nxt[0] - day).days
    facts.append(f"{'Today is' if gap == 0 else f'{gap} days until'} {nxt[1]}.")
    if day.month == day.day:
        facts.append(f"A doubled date: {day.month}/{day.day}.")
    if day.strftime("%m%d") == "0314":
        facts.append("Pi Day.")
    if day.weekday() == 4 and day.day == 13:
        facts.append("Friday the 13th.")
    us = f"{day.month}{day.day}{day.year % 100:02d}"
    if us == us[::-1]:
        facts.append(f"{day.month}/{day.day}/{day.year % 100:02d} reads the same backwards.")
    first_sun_nov = dt.date(day.year, 11, 1) + dt.timedelta(days=(6 - dt.date(day.year, 11, 1).weekday()) % 7)
    if 0 <= (first_sun_nov - day).days <= 10:
        g = (first_sun_nov - day).days
        facts.append("Clocks fall back an hour tonight." if g == 1 else
                     "Clocks fell back an hour last night." if g == 0 else f"Clocks fall back in {g} days (Nov {first_sun_nov.day}).")
    return facts


def nearby(lat, lon, day, radius_m=10000):
    """Wikipedia articles about places near home, with one featured place that changes each day."""
    data = _get(f"{WIKI}/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "list": "geosearch", "gscoord": f"{lat}|{lon}", "gsradius": radius_m,
        "gslimit": 100, "format": "json"}))
    hits = [h for h in data["query"]["geosearch"] if not h["title"].startswith(("List of", "Category:"))]
    if not hits:
        raise RuntimeError("No Wikipedia places nearby")
    pick = hits[day.toordinal() % len(hits)]
    s = _get(f"{WIKI}/api/rest_v1/page/summary/" + urllib.parse.quote(pick["title"].replace(" ", "_")))
    feature = {**_page(s), "miles": round(pick["dist"] / 1609.34, 1)}
    others = [{"title": h["title"], "miles": round(h["dist"] / 1609.34, 1),
               "url": f"{WIKI}/wiki/" + urllib.parse.quote(h["title"].replace(" ", "_"))}
              for h in hits if h is not pick][:8]
    return {"feature": feature, "others": others, "count": len(hits)}


def _text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _reports(page):
    """Trip report links (their URLs carry the hike date) and the text after each one."""
    out = []
    marks = list(re.finditer(r'href="(https://www\.wta\.org/go-hiking/trip-reports/trip_report-(\d{4}-\d\d-\d\d)[^"]*)"', page))
    for i, m in enumerate(marks):
        if any(r["url"] == m.group(1) for r in out):
            continue
        chunk = page[m.end():marks[i + 1].start() if i + 1 < len(marks) else m.end() + 4000]
        body = re.search(r'class="[^"]*report-text[^"]*"[^>]*>(.*?)</div>', chunk, re.S)
        by = re.search(r'class="[^"]*\b(?:wta-icon-headline__text|CreatorInfo)[^"]*"[^>]*>(.*?)</', chunk, re.S)
        issues = re.search(r'class="[^"]*trail-issues[^"]*"[^>]*>(.*?)</div>', chunk, re.S)
        snippet = _text(body.group(1)) if body else ""
        out.append({"url": m.group(1), "date": m.group(2), "by": _text(by.group(1)) if by else None,
                    "issues": _text(issues.group(1)) or None if issues else None,
                    "text": (snippet[:277] + "…") if len(snippet) > 280 else snippet or None})
    return sorted(out, key=lambda r: r["date"], reverse=True)


def trip_reports(today):
    """Latest trip reports for a few Gorge hikes, newest first, from the last three weeks."""
    hikes, errors = [], []
    for slug, name in HIKES:
        reports = []
        for url in (f"{WTA}{slug}/@@related_tripreport_listing", f"{WTA}{slug}"):
            try:
                reports = _reports(_get(url, as_json=False))
            except Exception as e:
                errors.append(f"{name}: {e}")
            if reports:
                break
        recent = [r for r in reports if (today - dt.date.fromisoformat(r["date"])).days <= 21]
        if recent:
            hikes.append({"hike": name, "url": WTA + slug, "count": len(recent), "latest": recent[0]})
    if not hikes and errors:
        raise RuntimeError("; ".join(errors[:3]))
    return sorted(hikes, key=lambda h: h["latest"]["date"], reverse=True)
