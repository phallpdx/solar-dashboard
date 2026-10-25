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


GOOGLE_HOLIDAY_ICS = "https://calendar.google.com/calendar/ical/{cal}/public/basic.ics"
CALENDARS = (("en.usa%23holiday%40group.v.calendar.google.com", "USA"),
             ("en.th%23holiday%40group.v.calendar.google.com", "Thailand"))


def _ics_events(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", "replace")
    text = text.replace("\r\n ", "").replace("\n ", "")  # unfold long lines
    for block in text.split("BEGIN:VEVENT")[1:]:
        fields = {}
        for line in block.splitlines():
            key, _, value = line.partition(":")
            fields[key.split(";")[0]] = value.strip()
        start = fields.get("DTSTART", "")
        if len(start) >= 8:
            yield {"date": f"{start[:4]}-{start[4:6]}-{start[6:8]}", "name": fields.get("SUMMARY", ""),
                   "observance": "observance" in fields.get("DESCRIPTION", "").lower()}


# Thai Buddhist and cultural days. Most follow the Thai lunar calendar, so their dates are kept here by
# year (from Thai government holiday announcements); "approx" marks a date not yet announced.
THAI_BUDDHIST = [
    ("2026-10-26", None, "Ok Phansa", "End of Buddhist Lent. Temples hold merit-making at dawn, and the Naga fireballs rise over the Mekong.", False),
    ("2026-11-24", None, "Loy Krathong", "Floating krathongs on rivers and canals under the full moon; Yi Peng lanterns in Chiang Mai.", False),
    ("2027-02-21", None, "Makha Bucha", "Full-moon day for the Buddha's teaching to 1,250 disciples. Candlelit walks around temples.", False),
    ("2027-04-13", "2027-04-15", "Songkran", "Thai New Year: water fights, pouring water on elders' hands, and temple visits.", False),
    ("2027-05-20", None, "Visakha Bucha", "Marks the Buddha's birth, enlightenment and death. Candlelit processions at temples.", False),
    ("2027-07-18", None, "Asahna Bucha", "Marks the Buddha's first sermon.", False),
    ("2027-07-19", None, "Khao Phansa", "Start of the three-month Buddhist Lent; candle processions and gifts to monks.", False),
    ("2027-10-15", None, "Ok Phansa", "End of Buddhist Lent, with merit-making at dawn.", True),
    ("2027-11-13", None, "Loy Krathong", "Floating krathongs under the full moon; Yi Peng lanterns in Chiang Mai.", True),
    ("2028-04-13", "2028-04-15", "Songkran", "Thai New Year: water fights, pouring water on elders' hands, and temple visits.", False),
]


def thai_buddhist(today):
    t = today.isoformat()
    return [{"date": d, "ends": e, "name": n, "about": a, "approx": x} for d, e, n, a, x in THAI_BUDDHIST if (e or d) >= t][:8]


def _nager(country, today):
    """Fallback source: Nager.Date public holidays."""
    events = []
    for year in (today.year, today.year + 1):
        try:
            rows = _get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}")
        except Exception:
            continue
        events += [{"date": r["date"], "name": r["name"], "observance": False} for r in rows]
    return events


def holidays(today):
    """Upcoming public holidays in the USA and Thailand (Google's public holiday calendars)."""
    out = []
    for cal, label in CALENDARS:
        try:
            events = list(_ics_events(GOOGLE_HOLIDAY_ICS.format(cal=cal)))
        except Exception:
            events = _nager("US" if label == "USA" else "TH", today)
        for ev in events:
            if today.isoformat() <= ev["date"] <= (today + dt.timedelta(days=200)).isoformat():
                out.append({"date": ev["date"], "name": ev["name"].replace("\\,", ","), "country": label,
                            "observance": ev["observance"]})
    out = sorted({(h["date"], h["country"], h["name"]): h for h in out}.values(), key=lambda h: h["date"])
    if not out:
        raise RuntimeError("no holidays returned")
    return out[:30]


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
