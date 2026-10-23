"""Strong-weather alerts: official NWS alerts for home, plus a check of the next few days of forecast."""
import datetime as dt
import json
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)", "Accept": "application/geo+json"}
SEVERITY = {"Extreme": 3, "Severe": 3, "Moderate": 2, "Minor": 1}


def nws(lat, lon):
    """Active National Weather Service alerts covering this point."""
    req = urllib.request.Request(f"https://api.weather.gov/alerts/active?point={lat},{lon}", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    out = []
    for f in data.get("features", []):
        p = f.get("properties") or {}
        if p.get("status") != "Actual" or p.get("messageType") == "Cancel":
            continue
        out.append({"event": p.get("event"), "headline": p.get("headline"), "severity": p.get("severity"),
                    "onset": p.get("onset") or p.get("effective"), "ends": p.get("ends") or p.get("expires"),
                    "description": (p.get("description") or "").strip()[:1500],
                    "instruction": (p.get("instruction") or "").strip()[:800]})
    return out


# Kinds of forecast alert, and NWS event words that already cover them.
COVERED_BY = {"wind": ("Wind", "Storm"), "rain": ("Flood", "Rain"), "snow": ("Snow", "Winter", "Blizzard", "Ice"),
              "ice": ("Ice", "Freezing", "Winter"), "storm": ("Thunderstorm",), "heat": ("Heat",),
              "freeze": ("Freeze", "Frost", "Cold")}


def from_forecast(days, official, limit_days=3):
    """Flag strong weather in the next few days of the forecast that NWS hasn't already issued."""
    events = " ".join(a.get("event") or "" for a in official)
    out = []
    for d in days[:limit_days]:
        found = []
        gust = d.get("gust") or 0
        if gust >= 35:
            found.append(("wind", 3 if gust >= 50 else 2, "Strong wind", f"Gusts up to {gust} mph."))
        code = d.get("code") or 0
        if code in (95, 96, 99):
            found.append(("storm", 2, "Thunderstorms", "Thunderstorms in the forecast."))
        if code in (56, 57, 66, 67):
            found.append(("ice", 3, "Freezing rain", "Freezing rain could ice roads, trees and power lines."))
        snow = d.get("snow_in") or 0
        if snow >= 0.5 or code in (71, 73, 75, 77, 85, 86):
            found.append(("snow", 3 if snow >= 3 else 2, "Snow",
                          f"About {snow:.0f} in of snow." if snow >= 1 else "Some snow in the forecast."))
        rain = d.get("rain_in") or 0
        if rain >= 1:
            found.append(("rain", 2, "Heavy rain", f"About {rain:.1f} in of rain."))
        if (d.get("hi") or 0) >= 95:
            found.append(("heat", 3 if d["hi"] >= 103 else 2, "Heat", f"High of {d['hi']}°F."))
        if d.get("lo") is not None and d["lo"] <= 28:
            found.append(("freeze", 2, "Hard freeze", f"Low of {d['lo']}°F. Protect pipes and plants."))
        for kind, level, title, text in found:
            if any(w in events for w in COVERED_BY[kind]):
                continue
            out.append({"kind": kind, "level": level, "date": d["date"], "title": title, "text": text})
    return out


def active(official, now_utc):
    """Official alerts that haven't ended, most severe first."""
    live = [a for a in official if not a.get("ends") or dt.datetime.fromisoformat(a["ends"]) > now_utc]
    return sorted(({**a, "level": SEVERITY.get(a.get("severity"), 1)} for a in live), key=lambda a: -a["level"])
