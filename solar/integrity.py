"""Edition integrity: one pass over everything the dashboard and the Kindle edition print, so a fact
reads the same on every page, an item is printed once, and nothing old is passed off as new.

It runs after the cloud update has written dashboard.json and the site folder holds the PC-written
lists (web/*.json), and before either edition is built:

    python -m solar.integrity _site

Each rule is a small function that takes the parsed data and edits it in place. They are pure
(no network), so tests can feed them fixtures. Every change is logged to stderr in one line.

Rules
  marine     an active NWS marine *warning* caps surf ratings at Poor for the days it covers and
             is attached to the coast and surf data so those pages lead with it; the NWS surf-zone
             forecast becomes the one wave height printed for the days it covers
  calendar   the same event on two calendars (same title and start time, a day apart) prints once
  events     one event, one page: an event listed by several feeds stays in the first page of
             the edition that prints it
  news       one story, one state: headlines about the same people are folded into the newest
             one; a product's several reviews become one item
  fresh      lists labelled "latest", "new" or "just released" drop items past their shelf life;
             data that is days old carries its date ("as_of") so pages can say so
  civics     procedural votes on the same bill fold into the final vote, each joined to its
             outcome; election-season guides drop once the election is past
"""

import datetime as dt
import json
import os
import re
import sys

TZ = "America/Los_Angeles"

# How long an item may be called "latest" or "new", in days.
SHELF = {"team_news": 14, "albums": 14, "food_finds": 21, "whales": 14, "trail_reports": 7, "live_blog": 2}


def log(msg):
    print(f"integrity: {msg}", file=sys.stderr)


def _today(now):
    try:
        from zoneinfo import ZoneInfo
        return now.astimezone(ZoneInfo(TZ)).date()
    except Exception:  # noqa: BLE001  (no tz database: Pacific is UTC-8 most of the edition's year)
        return (now - dt.timedelta(hours=8)).date()


def _date(s):
    """A date from 'YYYY-MM-DD...', 'MM/DD/YYYY' or an ISO stamp, else None."""
    if not s or not isinstance(s, str):
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return dt.date(*map(int, m.groups()))
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    return None


def _when(s):
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except (AttributeError, ValueError):
        return None


# ------------------------------------------------------------------ marine warnings and wave height

def marine(d, now):
    """Active NWS marine warnings cap the surf ratings and lead the coast pages."""
    today = _today(now)
    raw = list(((d.get("river") or {}).get("bar")) or []) + list(((d.get("coast") or {}).get("alerts")) or [])
    warnings = []
    for a in raw:
        ev = a.get("event") or ""
        end = _when(a.get("expires") or a.get("ends") or "")
        if not re.search(r"warning", ev, re.I) or (end and end <= now):
            continue
        desc = a.get("description") or ""
        m = re.search(r"For the " + re.escape(ev) + r",?\s*([^*]+?)(?=\s+For the |\s*\*|$)", desc, re.I)
        text = (m.group(1) if m else "").strip().rstrip(".")
        seas = re.search(r"seas (\d+) to (\d+) ft", text)
        warnings.append({"event": ev, "onset": a.get("onset"), "until": a.get("expires") or a.get("ends"),
                         "seas_ft": f"{seas.group(1)}-{seas.group(2)}" if seas else None,
                         "text": text[:1].upper() + text[1:] if text else None, "where": a.get("area") or "Columbia River bar"})
    if warnings:
        last = max((_date(w["until"]) or today) for w in warnings)
        lead = warnings[0]
        for key in ("coast", "surf"):
            if d.get(key) is not None:
                d[key]["warning"] = lead
                d[key]["warnings"] = warnings
        capped = 0
        for b in ((d.get("surf") or {}).get("breaks")) or []:
            for day in [b.get("now")] + list(b.get("days") or []):
                if not day:
                    continue
                on = _date(day.get("date")) or today
                if on <= last and (day.get("score") or 0) > 1:
                    day.update(rating="Poor", score=1, capped_by=lead["event"])
                    capped += 1
        for day in ((d.get("coast") or {}).get("days")) or []:
            if (_date(day.get("date")) or today) <= last:
                day["warning"] = lead["event"]
        log(f"marine: {lead['event']} until {lead['until']}; {capped} surf ratings capped at Poor")

    # One wave height: the NWS surf-zone forecast (the official one, and the one the warning matches)
    # for the days it covers; the Open-Meteo model only past them. Pages print `surf_ft` + `surf_src`.
    sz = (d.get("river") or {}).get("surf_zone") or {}
    by_day = {}
    for i, x in enumerate(sz.get("days") or []):
        m = re.search(r"(\d+)\s*(?:to|-|–)\s*(\d+)\s*ft", x.get("surf") or "")
        if m:
            by_day[today + dt.timedelta(days=i)] = f"{m.group(1)}-{m.group(2)}"
    for day in ((d.get("coast") or {}).get("days")) or []:
        on = _date(day.get("date"))
        if on in by_day:
            day.update(surf_ft=by_day[on], surf_src="NWS")
        elif day.get("waves_ft") is not None:
            day.update(surf_ft=str(day["waves_ft"]), surf_src="model")
    if by_day and d.get("surf") is not None:
        d["surf"]["official_ft"] = by_day.get(today)
    # One water temperature: the buoy's measured reading over the model's.
    bw = ((d.get("surf") or {}).get("buoy") or {}).get("water_f")
    if bw is not None and d.get("coast") is not None and d["coast"].get("water_f") not in (None, bw):
        log(f"marine: coast water {d['coast']['water_f']}° replaced by the buoy's {bw}°")
        d["coast"]["water_f"] = bw


# ------------------------------------------------------------------ calendar

def calendar(d, sports_dates=None):
    """The same event copied onto two calendars a day apart (time zone or feed drift) prints once.
    When the sports schedule knows the real date, that one wins; otherwise the first."""
    cal = d.get("calendar") or []
    sports_dates = sports_dates or set()
    keep, drop = [], set()
    for i, e in enumerate(cal):
        if i in drop:
            continue
        for j in range(i + 1, len(cal)):
            f = cal[j]
            if j in drop or e.get("all_day") or f.get("all_day") or _norm(e.get("title")) != _norm(f.get("title")):
                continue
            a, b = _date(e.get("date")), _date(f.get("date"))
            same_clock = (e.get("start") or "")[11:16] == (f.get("start") or "")[11:16]
            if a and b and abs((a - b).days) <= 1 and same_clock:
                loser = i if (f.get("date") in sports_dates and e.get("date") not in sports_dates) else j
                drop.add(loser)
                log(f"calendar: '{e.get('title')}' listed on {e.get('date')} and {f.get('date')}; kept {cal[i + j - loser].get('date')}")
                if loser == i:
                    break
    d["calendar"] = [e for k, e in enumerate(cal) if k not in drop]


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


# ------------------------------------------------------------------ events across the edition

STOP = set("""the and for with from into this that your their our its at in on of to a an by or vs v
    portland pdx annual free night nights show live event events festival fest day days tour
    holiday holidays season new presents presented feat featuring all ages""".split())
MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}


def _tokens(s):
    s = re.sub(r"\([^)]*\)", " ", s or "")  # "(Nov 19)", "(through Dec 6)"
    return {w for w in _norm(s).split() if len(w) > 2 and w not in STOP and w not in MONTHS and not w.isdigit()}


def _same(a, b):
    ta, tb = a["tok"], b["tok"]
    if not ta or not tb:
        return False
    k = len(ta & tb)
    if k < min(2, len(ta), len(tb)):
        return False
    if k / min(len(ta), len(tb)) < 0.75:
        return False
    # Different dates mean different events (two Blazers games); unknown dates don't block a match.
    if a["from"] and b["from"]:
        a_to, b_to = a["to"] or a["from"], b["to"] or b["from"]
        if a["from"] > b_to + dt.timedelta(days=1) or b["from"] > a_to + dt.timedelta(days=1):
            return False
    return True


def events(d, feeds):
    """Print each event once, on the first page of the edition that lists it. Edition order:
    Today (week ahead, coming soon), Little one, Music, On screen, Around Portland."""
    order = [
        ("calendar", lambda: d.get("calendar") or [], lambda x: (x.get("title"), x.get("date"), x.get("last_day"))),
        ("planahead", lambda: (feeds.get("planahead") or {}).get("items") or [],
         lambda x: (x.get("title"), x.get("starts") or x.get("by"), None)),
        ("kids", lambda: (feeds.get("kids") or {}).get("events") or [], lambda x: (x.get("title"), x.get("date"), x.get("ends"))),
        ("jazz", lambda: (feeds.get("jazz") or {}).get("shows") or [], lambda x: (x.get("artist"), x.get("date"), None)),
        ("concerts", lambda: (feeds.get("concerts") or {}).get("shows") or [], lambda x: (x.get("artist"), x.get("date"), None)),
        ("bluray", lambda: (feeds.get("bluray") or {}).get("deals") or [], lambda x: (x.get("title"), None, None)),
        ("events", lambda: (feeds.get("events") or {}).get("events") or [], lambda x: (x.get("title"), x.get("date"), x.get("ends"))),
    ]
    seen = []
    for name, get, key in order:
        items = get()
        keep = []
        for x in items:
            title, start, end = key(x)
            me = {"tok": _tokens(title), "from": _date(start), "to": _date(end), "title": title, "feed": name}
            dup = next((s for s in seen if s["feed"] != name and _same(me, s)), None)
            if dup:
                log(f"events: '{title}' ({name}) already printed as '{dup['title']}' ({dup['feed']}); dropped")
                continue
            keep.append(x)
            seen.append(me)
        if len(keep) != len(items):
            items[:] = keep


# ------------------------------------------------------------------ news

NAME_STOP = {"The", "A", "An", "New", "How", "Why", "What", "When", "Who", "WATCH", "Review", "Live", "In", "On",
             "After", "Before", "Here", "This", "These", "Best", "I", "My", "Your", "Is", "Are"}


def _names(title):
    """Pairs of capitalised words: 'Jensen Huang', 'Silver Rail', 'Apple TV'."""
    words = re.findall(r"[A-Z][\w'’.-]*", title or "")
    toks = re.findall(r"\S+", title or "")
    out = set()
    for a, b in zip(toks, toks[1:]):
        a2, b2 = a.strip("“”\"'‘’:,;()"), b.strip("“”\"'‘’:,;()")
        if a2[:1].isupper() and b2[:1].isupper() and a2 not in NAME_STOP and b2 not in NAME_STOP \
                and a2.isalpha() and b2.isalpha() and not a2.isupper() and not b2.isupper() and len(a2) > 2 and len(b2) > 2:
            # names, not products or acronyms ("Apple TV", "NBA Cup" are not one story)
            out.add(f"{a2} {b2}")
    return out if words else set()


def news(d, now):
    """Fold the same story across Top stories, Portland news and Tech so it prints once, in its newest
    state, where it first appears; drop live blogs and other stale items; fold multiple reviews."""
    n = d.get("news") or {}
    lists = [k for k in ("big", "local", "stories") if isinstance(n.get(k), list)]
    flat = [(k, i, x) for k in lists for i, x in enumerate(n[k])]
    groups = []
    for k, i, x in flat:
        nm = _names(x.get("title"))
        g = next((g for g in groups if nm & g["names"]), None)
        if g:
            g["members"].append((k, i, x))
            g["names"] |= nm
        else:
            groups.append({"names": set(nm), "members": [(k, i, x)]})
    drop = set()
    for g in groups:
        if len(g["members"]) < 2:
            continue
        first = g["members"][0]
        newest = max(g["members"], key=lambda m: m[2].get("utc") or "")
        if newest is not first:
            first[2].update({k: v for k, v in newest[2].items() if k in ("title", "url", "utc", "source", "summary", "image")})
        also = first[2].setdefault("also", [])
        for m in g["members"][1:]:
            drop.add((m[0], m[1]))
            if m[2].get("url") and all(a.get("url") != m[2]["url"] for a in also):
                also.append({"source": m[2].get("source"), "url": m[2]["url"]})
        log(f"news: '{first[2].get('title')}' printed once ({len(g['members'])} tellings folded)")
    for k, i, x in flat:
        t = _when(x.get("utc") or "")
        if re.search(r"\blive\b.*\bupdates?\b|^live:|\blive blog\b", x.get("title") or "", re.I):
            # A live blog's own date is today's refresh; the event it follows is what is old. Keep only
            # live blogs whose summary/title name nothing older than two days (they rarely qualify).
            old = re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}\b", (x.get("summary") or "") + " " + x["title"])
            if old or (t and now - t > dt.timedelta(days=SHELF["live_blog"])):
                drop.add((k, i))
                log(f"news: live blog '{x.get('title')}' dropped (follows an older event)")
    for k in lists:
        n[k] = [x for i, x in enumerate(n[k]) if (k, i) not in drop]

    # Reviews of one product fold into one item: "Apple TV 4K (2026) — 4 reviews".
    rv = n.get("reviews")
    if isinstance(rv, list):
        out, by = [], {}
        for x in rv:
            key = _product(x.get("title"))
            if key and key in by:
                by[key].setdefault("also", []).append({"source": x.get("source"), "url": x.get("url"), "title": x.get("title")})
                continue
            if key:
                by[key] = x
            out.append(x)
        for key, x in by.items():
            if x.get("also"):
                x["review_count"] = 1 + len(x["also"])
                x["title"] = f"{x['title']} ({x['review_count']} reviews: {', '.join([x.get('source') or ''] + [a.get('source') or '' for a in x['also']])})"
                log(f"news: {x['review_count']} reviews of {key} folded into one")
        n["reviews"] = out


def _product(title):
    """'Apple TV 4K (2026) review: …' -> 'apple tv 4k'; 'Apple HomeView review' -> 'apple homeview'."""
    t = re.sub(r"[’']s\b", "", title or "")
    m = re.search(r"\b(Apple|Google|Samsung|Sony|Amazon|Meta|Microsoft|Nintendo)\s+([A-Z][\w-]*(?:\s+\d+K)?)", t)
    if m:
        return f"{m.group(1)} {m.group(2)}".lower()
    m = re.match(r"([A-Z][\w-]*(?:\s+[A-Z0-9][\w-]*){1,3})\s+[Rr]eview\b", t)
    return m.group(1).lower() if m else None


# ------------------------------------------------------------------ freshness

def fresh(d, feeds, now):
    today = _today(now)

    def old(s, days):
        x = _date(s) or (_when(s).date() if _when(s or "") else None)
        return x is not None and (today - x).days > days

    sp = d.get("sports") or {}
    for team, t in sp.items():
        if isinstance(t, dict) and isinstance(t.get("news"), list):
            keep = [x for x in t["news"] if not old(x.get("utc"), SHELF["team_news"])]
            if len(keep) != len(t["news"]):
                log(f"fresh: {team} news, {len(t['news']) - len(keep)} items older than {SHELF['team_news']} days dropped")
                t["news"] = keep
    if isinstance(d.get("albums"), list):
        keep = [a for a in d["albums"] if not old(a.get("date"), SHELF["albums"])]
        if len(keep) != len(d["albums"]):
            log(f"fresh: albums, {len(d['albums']) - len(keep)} released more than {SHELF['albums']} days ago dropped")
            d["albums"] = keep
    wh = (d.get("outings") or {}).get("whales")
    if wh and isinstance(wh.get("sightings"), list):
        keep = [s for s in wh["sightings"] if not old(s.get("date"), SHELF["whales"])]
        if len(keep) != len(wh["sightings"]):
            log(f"fresh: whale sightings, {len(wh['sightings']) - len(keep)} older than {SHELF['whales']} days dropped")
            wh["sightings"], wh["count"] = keep, len(keep)
    al = d.get("almanac") or {}
    if isinstance(al.get("trails"), list):
        keep = [t for t in al["trails"] if not old(((t.get("latest") or {}).get("date")), SHELF["trail_reports"])]
        if len(keep) != len(al["trails"]):
            log(f"fresh: trail reports, {len(al['trails']) - len(keep)} older than {SHELF['trail_reports']} days dropped")
            al["trails"] = keep
    # "Happy news" is happy, and today's: no rescues from disaster, no yesterday's "Good News in History".
    gn = d.get("good_news")
    if isinstance(gn, list):
        grim = re.compile(r"\b(killed|kills|dies|died|dead|death|shot|shooting|washed|swept|injur\w*|attack\w*|crash\w*|missing|rescue\w*)\b", re.I)
        def stale_history(x):
            m = re.search(r"in History, (\w+ \d{1,2})", x.get("title") or "")
            return bool(m) and m.group(1) != f"{today:%B} {today.day}"
        keep = [x for x in gn if not grim.search(x.get("title") or "") and not stale_history(x)]
        if len(keep) != len(gn):
            log(f"fresh: good news, {len(gn) - len(keep)} grim or dated items dropped")
            d["good_news"] = keep
    # Data that is days old says so: pages print "as of" from these.
    sh = d.get("shellfish")
    if sh and _date(sh.get("updated")):
        sh["as_of"] = _date(sh["updated"]).isoformat()
        sh["stale_days"] = (today - _date(sh["updated"])).days
    h = d.get("health")
    if h and h.get("items"):
        wk = _date(h["items"][0].get("week_end"))
        if wk:
            h["as_of"], h["stale_days"] = wk.isoformat(), (today - wk).days
    ff = feeds.get("foodfinds")
    if ff and isinstance(ff.get("items"), list):
        keep = [x for x in ff["items"] if not old(x.get("date"), SHELF["food_finds"])]
        if len(keep) != len(ff["items"]):
            log(f"fresh: food finds, {len(ff['items']) - len(keep)} older than {SHELF['food_finds']} days dropped")
            ff["items"] = keep
    # Boilerplate about a scheduled update that has come and gone.
    so = feeds.get("skioutlook")
    if so:
        for k, v in list(so.items()):
            if isinstance(v, str) and re.search(r"next update is scheduled for", v, re.I):
                so[k] = _drop_past_update(v, today)
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, str):
                        v[k2] = _drop_past_update(v2, today)
    for key in ("events", "kids"):
        f = feeds.get(key)
        if f and isinstance(f.get("events"), list):
            keep = [e for e in f["events"] if not (_date(e.get("ends") or e.get("date")) and _date(e.get("ends") or e.get("date")) < today)]
            if len(keep) != len(f["events"]):
                log(f"fresh: {key}, {len(f['events']) - len(keep)} past events dropped")
                f["events"] = keep
    ce = feeds.get("coast")
    if ce and isinstance(ce.get("events"), list):
        keep = [e for e in ce["events"] if _date(e.get("date")) and (_date(e.get("end") or e.get("date")) >= today)]
        if len(keep) != len(ce["events"]):
            log(f"fresh: coast events, {len(ce['events']) - len(keep)} past or undated dropped")
            ce["events"] = keep


def _drop_past_update(text, today):
    def repl(m):
        when = _date(m.group(1))
        return "" if when and when <= today else m.group(0)
    return re.sub(r"\s*The next update is scheduled for (\d{4}-\d{2}-\d{2})\.", repl, text)


# ------------------------------------------------------------------ civics

ELECTION_GUIDE = re.compile(r"voter(s'?)? guide|know your candidates|primary (election )?guide|candidate (q&a|questionnaire)|endorsement", re.I)


def civics(d, now):
    c = d.get("civics")
    if not c:
        return
    today = _today(now)
    # A test entry from the Google Civic API is not an election.
    c["elections"] = [e for e in c.get("elections") or [] if not re.search(r"\btest election\b", e.get("name") or "", re.I)]
    # Guides written for an election that has happened are done. November: the Tuesday after the
    # first Monday; May: the third Tuesday (Oregon's primary).
    nov1 = dt.date(today.year, 11, 1)
    general = nov1 + dt.timedelta(days=(0 - nov1.weekday()) % 7 + 1)
    may1 = dt.date(today.year, 5, 1)
    primary = may1 + dt.timedelta(days=(1 - may1.weekday()) % 7 + 14)
    last_election = general if today > general else primary if today > primary else dt.date(today.year - 1, 11, 7)
    for p in c.get("people") or []:
        news_ = p.get("news") or []
        keep = [x for x in news_ if not (ELECTION_GUIDE.search(x.get("title") or "") and (_date(x.get("date")) or today) <= last_election)]
        if len(keep) != len(news_):
            log(f"civics: {p.get('name')}: {len(news_) - len(keep)} pre-election guides dropped")
            p["news"] = keep
        p["votes"] = fold_votes(p.get("votes") or [])
        if p["votes"]:
            p["vote_summary"] = vote_summary(p)


PROCEDURAL = re.compile(r"cloture|motion to proceed|motion to table|motion to waive|motion to recommit|previous question|rule providing", re.I)


def fold_votes(votes):
    """Procedural votes (cloture, motion to proceed) on a bill that also has a later vote fold into
    that later vote, which keeps a count of them. Each vote carries `outcome`: passed / failed / …"""
    out, by_bill = [], {}
    for v in sorted(votes, key=lambda v: v.get("date") or "", reverse=True):
        v = dict(v)
        v["outcome"] = _outcome(v.get("result"))
        v["plain"] = _plain(v)
        bill = v.get("bill")
        if bill and bill in by_bill:
            head = by_bill[bill]
            head.setdefault("steps", []).append({"question": v.get("question"), "vote": v.get("vote"), "date": v.get("date"), "result": v.get("result")})
            continue
        if bill:
            by_bill[bill] = v
        out.append(v)
    return out


def _outcome(result):
    r = (result or "").lower()
    if re.search(r"agreed|passed|confirmed|adopted|sustained", r):
        return "passed"
    if re.search(r"rejected|failed|not agreed|defeated|not sustained", r):
        return "failed"
    return r or None


def _plain(v):
    """A short plain line for the vote: the clerk's text without the procedural wrapper."""
    t = v.get("desc") or v.get("question") or ""
    # "Motion to Invoke Cloture on the Motion to Proceed to H.R. 9340; A bill to …" -> "amend …"
    t = re.sub(r"^(?:(?:Motion to Invoke Cloture|Cloture Motion|Cloture|Motion to Proceed|Motion to Table)\b(?: on)?(?: the)?\s*:?\s*(?:to\s*)?)+", "", t, flags=re.I)
    t = re.sub(r"^(?:Motion to Proceed\s*(?:to|:)\s*)?[HS]\.?\s?(?:R|J|RES|Res)?\.?\s?(?:Res\.?\s?)?\d+\s*[;:]\s*", "", t)
    t = re.sub(r"^A (bill|joint resolution|resolution) to\s+", "", t, flags=re.I)
    t = re.sub(r"\bthe Internal Revenue Code of 1986 to\s+", "the tax code to ", t)
    t = re.sub(r"^Confirmation:\s*", "confirming ", t)
    t = t.strip().rstrip(".")
    if len(t) > 110:
        t = t[:110].rsplit(" ", 1)[0] + "…"
    return t[:1].lower() + t[1:] if t and not re.match(r"[A-Z][a-z]+ [A-Z]", t) else t


def vote_summary(p):
    """One line for the member's recent votes: 'Voted no on 3 of 4 recent roll calls; 3 of those passed.'"""
    vs = p["votes"]
    n = len(vs)
    by = {}
    for v in vs:
        by.setdefault((v.get("vote") or "").lower(), []).append(v)
    yes, no = len(by.get("yea", []) + by.get("yes", []) + by.get("aye", [])), len(by.get("nay", []) + by.get("no", []))
    parts = []
    if no:
        lost = sum(1 for v in by.get("nay", []) + by.get("no", []) if v["outcome"] == "passed")
        parts.append(f"no on {no}" + (f" ({lost} passed anyway)" if lost else ""))
    if yes:
        won = sum(1 for v in by.get("yea", []) + by.get("yes", []) + by.get("aye", []) if v["outcome"] == "passed")
        parts.append(f"yes on {yes}" + (f" ({won} passed)" if won else ""))
    other = n - yes - no
    if other:
        parts.append(f"{other} not voting")
    return f"{n} recent vote{'s' if n != 1 else ''}: " + ", ".join(parts) + "." if parts else None


# ------------------------------------------------------------------ driver

FEEDS = ["planahead", "kids", "events", "jazz", "concerts", "bluray", "foodfinds", "skioutlook", "coast", "marketbrief"]


def apply(d, feeds, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    marine(d, now)
    sports_dates = set()
    for t in (d.get("sports") or {}).values():
        if isinstance(t, dict):
            for g in (t.get("schedule") or t.get("next") or []) if isinstance(t.get("schedule") or t.get("next"), list) else []:
                if isinstance(g, dict) and (g.get("date") or g.get("utc")):
                    sports_dates.add((g.get("date") or "")[:10] or (_when(g["utc"]) and _today(_when(g["utc"])).isoformat()))
    calendar(d, sports_dates)
    fresh(d, feeds, now)
    events(d, feeds)
    news(d, now)
    civics(d, now)
    d.setdefault("integrity", {})["checked_at"] = now.isoformat()
    return d


def main(site):
    path = os.path.join(site, "dashboard.json")
    with open(path) as f:
        d = json.load(f)
    feeds = {}
    for name in FEEDS:
        p = os.path.join(site, name + ".json")
        if os.path.exists(p):
            try:
                with open(p) as f:
                    feeds[name] = json.load(f)
            except ValueError as e:
                log(f"{name}.json unreadable ({e}); left alone")
    now = os.environ.get("INTEGRITY_NOW")
    apply(d, feeds, dt.datetime.fromisoformat(now) if now else None)
    with open(path, "w") as f:
        json.dump(d, f, separators=(",", ":"))
    for name, data in feeds.items():
        with open(os.path.join(site, name + ".json"), "w") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_site")
