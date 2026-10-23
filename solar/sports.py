"""Next games and standings: Trail Blazers, Timbers (ESPN), and Formula 1 (Jolpica/Ergast)."""
import datetime as dt
import json
import urllib.request

ESPN = "https://site.api.espn.com/apis/site/v2/sports"
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


def team(league_path, name):
    team_id = _find_team(league_path, name)
    info = _get(f"{ESPN}/{league_path}/teams/{team_id}").get("team", {})
    record = next((i.get("summary") for i in (info.get("record") or {}).get("items", [])
                   if i.get("type") in ("total", None)), None)
    schedule = _get(f"{ESPN}/{league_path}/teams/{team_id}/schedule").get("events", [])
    games = sorted((_game(e, team_id) for e in schedule), key=lambda g: g["utc"] or "")
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    # Some ESPN schedules omit the final status, so a past game with a score counts too.
    done = [g for g in games if g["completed"] or ((g["utc"] or "") < now_iso[:16] and g["us"] not in (None, ""))]
    upcoming = [_game(e, team_id) for e in info.get("nextEvent", [])] or \
        [g for g in games if not g["completed"]]
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    upcoming = [g for g in upcoming if not g["completed"] and (g["utc"] or "") >= now[:16]]
    return {
        "name": info.get("displayName") or name,
        "logo": (info.get("logos") or [{}])[0].get("href"),
        "record": record,
        "standing": info.get("standingSummary"),
        "last": done[-1] if done else None,
        "next": upcoming[0] if upcoming else None,
    }


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
