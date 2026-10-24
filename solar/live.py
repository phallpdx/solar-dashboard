"""Other live local feeds: earthquakes, wildfires, planes overhead and PDX airport delays."""
import datetime as dt
import json
import math
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
VOLCANOES = [("Mount St. Helens", 46.20, -122.19), ("Mount Hood", 45.37, -121.70), ("Mount Rainier", 46.85, -121.76),
             ("Mount Adams", 46.20, -121.49)]


def _get(url, as_json=True):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return json.loads(data) if as_json else data


def _km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def earthquakes(lat, lon, radius_km=300):
    """Quakes in the last week within a few hundred km, biggest first (USGS)."""
    data = _get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson")
    out = []
    for f in data.get("features", []):
        p, (qlon, qlat, depth) = f["properties"], f["geometry"]["coordinates"][:3]
        km = _km(lat, lon, qlat, qlon)
        if km > radius_km or p.get("mag") is None:
            continue
        near = next((n for n, vlat, vlon in VOLCANOES if _km(qlat, qlon, vlat, vlon) < 15), None)
        out.append({"mag": round(p["mag"], 1), "place": p.get("place"), "miles": round(km / 1.609),
                    "depth_km": round(depth or 0, 1), "utc": dt.datetime.fromtimestamp(p["time"] / 1000, dt.timezone.utc).isoformat(),
                    "volcano": near, "felt": p.get("felt"), "url": p.get("url")})
    out.sort(key=lambda q: (-q["mag"], q["utc"]))
    return {"count": len(out), "biggest": out[:8],
            "volcano_counts": {n: sum(1 for q in out if q["volcano"] == n) for n, _, _ in VOLCANOES}}


def wildfires(lat, lon, radius_km=400):
    """Active wildfires nearby (NIFC WFIGS current incidents)."""
    url = ("https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/"
           "FeatureServer/0/query?" + urllib.parse.urlencode({
               "where": "POOState IN ('US-OR','US-WA') AND IncidentTypeCategory='WF'",
               "outFields": "IncidentName,IncidentSize,PercentContained,FireDiscoveryDateTime,POOCounty,POOState",
               "returnGeometry": "true", "outSR": 4326, "f": "json"}))
    data = _get(url)
    if "error" in data:
        raise RuntimeError(data["error"].get("message"))
    out = []
    for f in data.get("features", []):
        a, g = f["attributes"], f.get("geometry") or {}
        if g.get("y") is None:
            continue
        km = _km(lat, lon, g["y"], g["x"])
        acres = a.get("IncidentSize") or 0
        if km > radius_km or acres < 100:
            continue
        out.append({"name": (a.get("IncidentName") or "").title() + " Fire", "acres": round(acres),
                    "contained": a.get("PercentContained"), "miles": round(km / 1.609),
                    "where": f"{a.get('POOCounty')} County, {(a.get('POOState') or '')[-2:]}"})
    out.sort(key=lambda x: -x["acres"])
    return out[:8]


def planes(lat, lon):
    """Aircraft overhead right now within about 25 miles (OpenSky Network)."""
    box = {"lamin": lat - 0.35, "lamax": lat + 0.35, "lomin": lon - 0.5, "lomax": lon + 0.5}
    data = _get("https://opensky-network.org/api/states/all?" + urllib.parse.urlencode(box))
    out = []
    for s in data.get("states") or []:
        callsign, plat, plon, alt_m, on_ground, speed, heading = (s[1] or "").strip(), s[6], s[5], s[7], s[8], s[9], s[10]
        if on_ground or plat is None or alt_m is None:
            continue
        out.append({"callsign": callsign or s[0], "miles": round(_km(lat, lon, plat, plon) / 1.609, 1),
                    "feet": round(alt_m * 3.281 / 100) * 100, "mph": round((speed or 0) * 2.237),
                    "heading": round(heading or 0), "country": s[2],
                    "url": f"https://globe.adsbexchange.com/?icao={s[0]}"})
    out.sort(key=lambda p: p["miles"])
    return {"count": len(out), "closest": out[:8]}


def pdx_status():
    """FAA delay programs and closures affecting PDX, if any."""
    root = ET.fromstring(_get("https://nasstatus.faa.gov/api/airport-status-information", as_json=False))
    out = []
    for node in root.iter():
        arpt = node.findtext("ARPT") or node.findtext("ARPT_ID")
        if arpt and arpt.upper() in ("PDX", "KPDX"):
            reason = node.findtext("Reason") or node.findtext(".//Reason") or ""
            avg = node.findtext("Avg") or node.findtext(".//Avg") or ""
            out.append({"type": node.tag.replace("_", " "), "reason": reason, "average": avg})
    return {"delays": out}
