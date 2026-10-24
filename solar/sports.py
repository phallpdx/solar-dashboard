"""Next games and standings: Trail Blazers, Timbers (ESPN), and Formula 1 (Jolpica/Ergast)."""
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ESPN = "https://site.api.espn.com/apis/site/v2/sports"
STANDINGS = "https://site.api.espn.com/apis/v2/sports"
UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _find_team(league_path, name):
    data = _get(f"{ESPN}/{league_path}/teams")
    for group in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
        team = group.get("team", {})
        if name.lower() in (team.get("displayName", "") + " " + team.get("name", "")).lower():
            return team["id"]
    raise RuntimeError(f"{name} not found on ESPN")


def _game(event, team_id):
    comp = (event.get("competitions") or [{}])[0]
    us, them = None, None
    for c in comp.get("competitors", []):
        if str(c.get("id") or c.get("team", {}).get("id")) == str(team_id):
            us = c
        else:
            them = c
    status = (comp.get("status") or event.get("status") or {}).get("type", {})

    def score(c):
        s = (c or {}).get("score")
        return s.get("displayValue") if isinstance(s, dict) else s

    broadcasts = [n for b in comp.get("broadcasts", []) for n in (b.get("names") or
                  [b.get("media", {}).get("shortName")]) if n]
    return {
        "utc": event.get("date"),
        "opponent": (them or {}).get("team", {}).get("displayName"),
        "home": (us or {}).get("homeAway") == "home",
        "venue": comp.get("venue", {}).get("fullName"),
        "tv": ", ".join(dict.fromkeys(broadcasts)) or None,
        "completed": bool(status.get("completed")),
        "us": score(us), "them": score(them),
        "won": (us or {}).get("winner"),
        "note": (comp.get("notes") or [{}])[0].get("headline") if comp.get("notes") else None,
    }


def _stat(entry, name):
    for s in entry.get("stats", []):
        if s.get("name") == name or s.get("type") == name:
            return s.get("value")
    return None


def _groups(node):
    if (node.get("standings") or {}).get("entries"):
        yield node
    for child in node.get("children") or []:
        yield from _groups(child)


def _ordered(entries):
    if all(_stat(e, "rank") is not None for e in entries):
        return sorted(entries, key=lambda e: _stat(e, "rank"))
    if all(_stat(e, "winPercent") is not None for e in entries):
        return sorted(entries, key=lambda e: (-_stat(e, "winPercent"), _stat(e, "playoffSeed") or 99))
    if all(_stat(e, "points") is not None for e in entries):
        return sorted(entries, key=lambda e: -_stat(e, "points"))
    return entries


def group_rank(league_path, team_id, level=None):
    """Where the team sits in its division (NBA) or conference (MLS)."""
    data = _get(f"{STANDINGS}/{league_path}/standings" + (f"?level={level}" if level else ""))
    for g in _groups(data):
        entries = _ordered(g["standings"]["entries"])
        for i, e in enumerate(entries):
            if str(e.get("team", {}).get("id")) == str(team_id):
                name = g.get("name") or ""
                if level == 3 and "Division" not in name:
                    name += " Division"
                return {"group": name, "rank": i + 1, "of": len(entries)}
    return None


def _recent(league_path, team_id, days=45):
    """Completed games from the league scoreboard, for when the team schedule lags."""
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    data = _get(f"{ESPN}/{league_path}/scoreboard?dates={start:%Y%m%d}-{end:%Y%m%d}&limit=1000")
    games = []
    for e in data.get("events", []):
        ids = {str(c.get("id") or c.get("team", {}).get("id"))
               for c in (e.get("competitions") or [{}])[0].get("competitors", [])}
        if str(team_id) in ids:
            games.append(_game(e, team_id))
    return sorted((g for g in games if g["completed"]), key=lambda g: g["utc"] or "")


def team(league_path, name, standings_level=None):
    team_id = _find_team(league_path, name)
    info = _get(f"{ESPN}/{league_path}/teams/{team_id}").get("team", {})
    record = next((i.get("summary") for i in (info.get("record") or {}).get("items", [])
                   if i.get("type") in ("total", None)), None)
    schedule = _get(f"{ESPN}/{league_path}/teams/{team_id}/schedule").get("events", [])
    games = sorted((_game(e, team_id) for e in schedule), key=lambda g: g["utc"] or "")
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    # Some ESPN schedules omit the final status, so a past game with a score counts too.
    done = [g for g in games if g["completed"] or ((g["utc"] or "") < now_iso[:16] and g["us"] not in (None, ""))]
    stale = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=21)).isoformat()[:16]
    if not done or (done[-1]["utc"] or "") < stale:
        try:
            done = _recent(league_path, team_id) or done
        except Exception:
            pass
    try:
        rank = group_rank(league_path, team_id, standings_level)
    except Exception:
        rank = None
    upcoming = [_game(e, team_id) for e in info.get("nextEvent", [])] or \
        [g for g in games if not g["completed"]]
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    upcoming = [g for g in upcoming if not g["completed"] and (g["utc"] or "") >= now[:16]]
    return {
        "name": info.get("displayName") or name,
        "logo": (info.get("logos") or [{}])[0].get("href"),
        "record": record,
        "standing": info.get("standingSummary"),
        "group_rank": rank,
        "last": done[-1] if done else None,
        "next": upcoming[0] if upcoming else None,
        "injuries": _safe(lambda: injuries(league_path, team_id)),
        "news": _safe(lambda: news(league_path, team_id, ("Portland", name.split()[-1]))),
    }


def _safe(fn):
    try:
        return fn()
    except Exception as e:
        return {"error": str(e)[:120]}


def injuries(league_path, team_id):
    """Players on the injury report, from the team roster."""
    data = _get(f"{ESPN}/{league_path}/teams/{team_id}/roster")
    athletes = data.get("athletes") or []
    if athletes and isinstance(athletes[0], dict) and "items" in athletes[0]:  # grouped by position
        athletes = [a for group in athletes for a in group.get("items", [])]
    out = []
    for a in athletes:
        for inj in a.get("injuries") or []:
            details = inj.get("details") or {}
            out.append({"player": a.get("displayName") or a.get("fullName"),
                        "position": (a.get("position") or {}).get("abbreviation"),
                        "status": inj.get("status") or (inj.get("type") or {}).get("description"),
                        "injury": " ".join(x for x in (details.get("location"), details.get("type")) if x) or None,
                        "detail": details.get("detail"), "return": details.get("returnDate"),
                        "date": (inj.get("date") or "")[:10] or None})
            break
    return out


def news(league_path, team_id, words=("Portland",), limit=4):
    """ESPN stories that are actually about the team, not league-wide roundups."""
    data = _get(f"{ESPN}/{league_path}/news?team={team_id}&limit=25")
    out = []
    for a in data.get("articles", []):
        text = f"{a.get('headline') or ''} {a.get('description') or ''}"
        if any(w.lower() in text.lower() for w in words):
            out.append({"headline": a.get("headline"), "description": a.get("description"), "utc": a.get("published"),
                        "url": ((a.get("links") or {}).get("web") or {}).get("href")})
    return out[:limit]


GOOD = set("win wins won beat great love awesome amazing huge clutch dominant best happy excited proud hype "
           "goat incredible fantastic impressive brilliant solid strong comeback victory elite progress".split())
BAD = set("lose loses lost loss bad awful terrible injury injured hurt worst sad angry frustrating frustrated "
          "embarrassing trade fire fired sucks disaster blown mess ugly concern worried pathetic boring tank".split())


def reddit(sub, limit=25):
    """Hot posts on a team subreddit and a rough mood from their titles, weighted by votes."""
    headers = {"User-Agent": "linux:solar-dashboard:1.0 (personal dashboard)"}
    posts, last_error = None, None
    for host in ("www.reddit.com", "old.reddit.com", "api.reddit.com"):
        try:
            req = urllib.request.Request(f"https://{host}/r/{sub}/hot.json?limit={limit}&raw_json=1", headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                posts = [c["data"] for c in json.load(resp)["data"]["children"]]
            break
        except Exception as e:
            last_error = e
            time.sleep(3)  # Reddit rate-limits quick retries
    if posts is None:  # the RSS feed has no vote counts, but still shows what people are talking about
        try:
            req = urllib.request.Request(f"https://www.reddit.com/r/{sub}/hot/.rss?limit={limit}", headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                root = ET.fromstring(resp.read())
            ns = {"a": "http://www.w3.org/2005/Atom"}
            posts = [{"title": e.findtext("a:title", namespaces=ns),
                      "permalink": urllib.parse.urlparse(e.find("a:link", ns).get("href")).path}
                     for e in root.findall("a:entry", ns)]
        except Exception:
            raise RuntimeError(f"Reddit blocked the request ({last_error})")
    posts = [p for p in posts if not p.get("stickied")]
    score = weight = 0
    for p in posts:
        words = set(re.findall(r"[a-z']+", (p.get("title") or "").lower()))
        w = 1 + min(p.get("score") or 0, 2000) / 200
        score += w * (len(words & GOOD) - len(words & BAD))
        weight += w
    mood = score / weight if weight else 0
    label = "Upbeat" if mood > 0.15 else "Grumpy" if mood < -0.15 else "Mixed"
    top = sorted(posts, key=lambda p: -(p.get("score") or 0))[:5]
    return {"sub": sub, "mood": label, "mood_score": round(mood, 2),
            "posts": [{"title": p.get("title"), "score": p.get("score"), "comments": p.get("num_comments"),
                       "flair": p.get("link_flair_text"), "url": "https://www.reddit.com" + (p.get("permalink") or "")}
                      for p in top]}


def f1():
    base = "https://api.jolpi.ca/ergast/f1/current"
    races = _get(f"{base}/races.json")["MRData"]["RaceTable"]["Races"]
    now = dt.datetime.now(dt.timezone.utc)
    upcoming = []
    for r in races:
        when = dt.datetime.fromisoformat(f"{r['date']}T{r.get('time', '12:00:00Z').replace('Z', '+00:00')}")
        if when > now - dt.timedelta(hours=3):
            upcoming.append({"utc": when.isoformat(), "name": r["raceName"],
                             "where": f"{r['Circuit']['Location']['locality']}, {r['Circuit']['Location']['country']}",
                             "round": int(r["round"]), "sprint": "Sprint" in r})
    lists = _get(f"{base}/driverStandings.json")["MRData"]["StandingsTable"]["StandingsLists"]
    drivers = []
    if lists:
        for d in lists[0]["DriverStandings"][:5]:
            drv = d["Driver"]
            drivers.append({"pos": int(d["position"]), "name": f"{drv['givenName']} {drv['familyName']}",
                            "team": d["Constructors"][-1]["name"] if d.get("Constructors") else "",
                            "points": float(d["points"])})
    return {"next": upcoming[:3], "rounds": len(races),
            "standings": drivers, "season": races[0]["season"] if races else None}
