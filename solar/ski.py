"""Mt. Hood ski report: measured snow (NRCS SNOTEL), mountain forecast (Open-Meteo), avalanche danger (NWAC)."""
import csv
import io
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
# Mt. Hood Test Site SNOTEL, 5,370 ft, next to Mt. Hood Meadows.
SNOTEL = ("651:OR:SNTL", "Mt. Hood Test Site (5,370 ft)")
# Timberline Lodge, about 6,000 ft.
LODGE = {"lat": 45.331, "lon": -121.711, "elevation_m": 1830}
RESORTS = [
    ("Timberline", "https://www.timberlinelodge.com/conditions"),
    ("Mt. Hood Meadows", "https://www.skihood.com/the-mountain/conditions"),
    ("Mt. Hood Skibowl", "https://www.skibowl.com/winter/mountain-report/"),
    ("Cooper Spur", "https://www.cooperspur.com/"),
]
DANGER = {1: "Low", 2: "Moderate", 3: "Considerable", 4: "High", 5: "Extreme"}


def _open(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30)


def snow():
    """Snow depth and new snow at the SNOTEL site over the last week."""
    url = ("https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/"
           f"{SNOTEL[0]}%7Cid=%22%22%7Cname/-8,0/SNWD::value,WTEQ::value,TOBS::value")
    with _open(url) as resp:
        text = resp.read().decode("utf-8", "replace")
    lines = [l for l in text.splitlines() if l and not l.startswith("#")]
    rows = list(csv.reader(io.StringIO("\n".join(lines))))
    days = []
    for r in rows[1:]:
        def num(i):
            try:
                return float(r[i])
            except (IndexError, ValueError):
                return None
        days.append({"date": r[0], "depth_in": num(1), "swe_in": num(2), "temp_f": num(3)})
    days = [d for d in days if d["depth_in"] is not None]
    if not days:
        raise RuntimeError("SNOTEL returned no snow depth")
    now = days[-1]
    gain = lambda back: (round(max(0.0, now["depth_in"] - days[-1 - back]["depth_in"]))
                         if len(days) > back else None)
    return {"station": SNOTEL[1], "date": now["date"], "depth_in": round(now["depth_in"]),
            "change_24h_in": round(now["depth_in"] - days[-2]["depth_in"]) if len(days) > 1 else None,
            "new_7d_in": gain(7), "temp_f": now["temp_f"],
            "series": [{"date": d["date"], "depth_in": d["depth_in"]} for d in days]}


def forecast():
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
        "latitude": LODGE["lat"], "longitude": LODGE["lon"], "elevation": LODGE["elevation_m"],
        "timezone": "America/Los_Angeles", "forecast_days": 7,
        "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,snowfall_sum,precipitation_sum,wind_gusts_10m_max",
        "hourly": "freezing_level_height",
    })
    with _open(url) as resp:
        f = json.load(resp)
    d, h = f["daily"], f.get("hourly") or {}
    # Open-Meteo reports heights in feet when imperial units are requested, otherwise meters.
    to_ft = 1 if (f.get("hourly_units") or {}).get("freezing_level_height") == "ft" else 3.281
    out = []
    for i, day in enumerate(d["time"]):
        levels = [v for t, v in zip(h.get("time", []), h.get("freezing_level_height", []))
                  if t.startswith(day) and v is not None]
        out.append({"date": day, "code": d["weather_code"][i],
                    "hi": round(d["temperature_2m_max"][i]), "lo": round(d["temperature_2m_min"][i]),
                    "snow_in": round(d["snowfall_sum"][i] or 0, 1), "gust": round(d["wind_gusts_10m_max"][i] or 0),
                    "snow_level_ft": round(min(levels) * to_ft / 100) * 100 if levels else None})
    return out


def avalanche():
    """NWAC danger rating for the Mt Hood zone, when a forecast is issued (winter only)."""
    with _open("https://api.avalanche.org/v2/public/products/map-layer/NWAC") as resp:
        data = json.load(resp)
    for f in data.get("features", []):
        p = f.get("properties") or {}
        if "hood" in (p.get("name") or "").lower():
            level = p.get("danger_level")
            return {"zone": p.get("name"), "level": level if isinstance(level, int) and level > 0 else None,
                    "danger": DANGER.get(level) if isinstance(level, int) else None,
                    "advice": p.get("travel_advice"), "url": p.get("link") or "https://nwac.us/avalanche-forecast/#/mt-hood",
                    "off_season": p.get("off_season")}
    return None


def resorts():
    return [{"name": n, "url": u} for n, u in RESORTS]
