"""Tree, grass and weed pollen for the next few days (Google Pollen API, needs a GOOGLE_POLLEN_KEY)."""
import json
import urllib.parse
import urllib.request


def forecast(lat, lon, key, days=3):
    url = "https://pollen.googleapis.com/v1/forecast:lookup?" + urllib.parse.urlencode(
        {"key": key, "location.latitude": lat, "location.longitude": lon, "days": days, "plantsDescription": "false"})
    req = urllib.request.Request(url, headers={"User-Agent": "solar-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    out = []
    for day in data.get("dailyInfo") or []:
        d = day.get("date") or {}
        types = []
        for t in day.get("pollenTypeInfo") or []:
            idx = t.get("indexInfo") or {}
            types.append({"name": t.get("displayName"), "in_season": bool(t.get("inSeason")),
                          "value": idx.get("value"), "category": idx.get("category")})
        plants = [p.get("displayName") for p in day.get("plantInfo") or []
                  if p.get("inSeason") and ((p.get("indexInfo") or {}).get("value") or 0) >= 2]
        out.append({"date": f"{d.get('year')}-{d.get('month', 0):02d}-{d.get('day', 0):02d}", "types": types,
                    "top_plants": plants[:4]})
    if not out:
        raise RuntimeError("Google Pollen returned no days")
    return out
