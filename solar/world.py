"""Public holidays (USA and Thailand) and Bangkok weather, time and air quality."""
import datetime as dt
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
BANGKOK = (13.7563, 100.5018)


def _get(url, **params):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def holidays(today):
    """Next ~10 public holidays in each country, from Nager.Date."""
    out = []
    for country, label in (("US", "USA"), ("TH", "Thailand")):
        rows = []
        for year in (today.year, today.year + 1):
            rows += _get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}")
        seen = set()
        for r in rows:
            if r["date"] < today.isoformat() or (r["date"], r["name"]) in seen:
                continue
            seen.add((r["date"], r["name"]))
            out.append({"date": r["date"], "name": r["name"], "local": r.get("localName"),
                        "country": label, "nationwide": r.get("global", True)})
    out.sort(key=lambda h: h["date"])
    return out[:20]


def bangkok():
    lat, lon = BANGKOK
    wx = _get("https://api.open-meteo.com/v1/forecast", latitude=lat, longitude=lon,
              timezone="Asia/Bangkok", forecast_days=3, temperature_unit="fahrenheit",
              wind_speed_unit="mph",
              current="temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
              daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max")
    air = _get("https://air-quality-api.open-meteo.com/v1/air-quality", latitude=lat, longitude=lon,
               timezone="Asia/Bangkok", current="us_aqi,pm2_5")
    cur, d = wx.get("current", {}), wx.get("daily", {})
    days = [{"date": t, "code": d["weather_code"][i], "hi": round(d["temperature_2m_max"][i]),
             "lo": round(d["temperature_2m_min"][i]), "rain_pct": d["precipitation_probability_max"][i]}
            for i, t in enumerate(d.get("time", []))]
    return {
        "temp": round(cur.get("temperature_2m") or 0), "feels": round(cur.get("apparent_temperature") or 0),
        "humidity": cur.get("relative_humidity_2m"), "code": cur.get("weather_code"),
        "wind": round(cur.get("wind_speed_10m") or 0),
        "aqi": (air.get("current") or {}).get("us_aqi"), "pm25": (air.get("current") or {}).get("pm2_5"),
        "days": days,
    }
