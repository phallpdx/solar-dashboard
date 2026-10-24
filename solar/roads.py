"""Road cameras and what's slowing traffic on Parker's usual drives, from ODOT TripCheck's public map data."""
import json
import math
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (solar-dashboard personal dashboard)"}
DATA = "https://www.tripcheck.com/Scripts/map/data/"
CAMS = "https://tripcheck.com/RoadCams/cams/"
# Spots worth a look on the regular drives: (label, lat, lon, how many cameras).
WATCH = [("Near home", 45.62, -122.77, 3), ("Interstate Bridge", 45.615, -122.68, 1),
         ("Sunset Highway summit", 45.82, -123.37, 1), ("US 30 toward Astoria", 46.11, -123.18, 1)]
# Incidents count when they're near home, on the drives to Portland, or on the way to the coast.
AREAS = [(45.64, -122.76, 15), (45.82, -123.37, 25), (46.12, -123.3, 30), (46.1, -123.9, 20)]


def _get(name):
    req = urllib.request.Request(DATA + name, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def _km(a, b, c, d):
    p = math.pi / 180
    h = 0.5 - math.cos((c - a) * p) / 2 + math.cos(a * p) * math.cos(c * p) * (1 - math.cos((d - b) * p)) / 2
    return 12742 * math.asin(math.sqrt(h))


def cameras():
    feats = _get("cctvinventory.js").get("features") or []
    cams = []
    for f in feats:
        a = f.get("attributes") or {}
        if a.get("latitude") and a.get("filename"):
            cams.append(a)
    out, used = [], set()
    for label, lat, lon, n in WATCH:
        near = sorted(cams, key=lambda a: _km(lat, lon, a["latitude"], a["longitude"]))
        picked = 0
        for a in near:
            title = (a.get("title") or "").strip()
            spot = re.sub(r"\(.*?\)|\b(NB|SB|EB|WB|Top|North|South|East|West|End|Midspan)\b", "", title.split(" at ")[-1]).strip()
            if spot in used or _km(lat, lon, a["latitude"], a["longitude"]) > 15:
                continue
            used.add(spot)
            out.append({"title": title.replace("Portland - ", ""), "group": label,
                        "img": CAMS + urllib.parse.quote(a["filename"])})
            picked += 1
            if picked >= n:
                break
    if not out:
        raise RuntimeError("no TripCheck cameras near the usual drives")
    return out


def _near(lat, lon):
    return lat is not None and any(_km(lat, lon, a, b) <= r for a, b, r in AREAS)


def incidents():
    out = []
    for name, roadwork in (("INCD.js", False), ("EVENT.js", True)):
        for f in _get(name).get("features") or []:
            a = f.get("attributes") or {}
            lat, lon = a.get("startLatitude"), a.get("startLongitude")
            sev = a.get("odotSeverityID")
            if not _near(lat, lon) or sev == 0 or (roadwork and sev == 7):
                continue  # leave out notices with no delay
            out.append({"what": a.get("eventSubTypeName") or a.get("eventTypeName"), "road": (a.get("route") or "").strip(),
                        "where": (a.get("beginMarker") or a.get("locationName") or "").strip(),
                        "delay": a.get("odotSeverityDescript"), "severity": sev, "roadwork": roadwork,
                        "note": (a.get("comments") or "").strip()[:200], "since": a.get("startTime")})
    seen, unique = set(), []
    for x in out:
        key = (x["road"], x["where"], x["note"][:60].lower())
        if key not in seen:
            seen.add(key)
            unique.append(x)
    out = unique
    rank = {4: 0, 3: 1, 2: 2, 1: 3, 7: 4}
    out.sort(key=lambda x: (x["roadwork"], rank.get(x["severity"], 5)))
    return out[:8]
