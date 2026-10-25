"""Surf report for breaks near the coast house: swell and wind forecasts (Open-Meteo marine and
weather, free, no key) and the latest reading from the nearest NOAA NDBC wave buoy.

Ratings are a rough call from swell size, period, how squarely the swell hits each break, and
whether the wind is offshore, cross or onshore there. They're a guide, not a substitute for a look.
"""
import datetime as dt
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
# Public surf spots from north to south. lat/lon is the break (for wind); sea is a point a few km
# offshore so the wave model has open water. faces is the direction the beach looks out to sea, and
# shelter lists wind directions (from) that the break is tucked away from.
BREAKS = [
    {"name": "Sunset Beach / Gearhart", "lat": 46.03, "lon": -123.93, "sea": (46.03, -124.02), "faces": 270,
     "shelter": [], "note": "Open beach break, a few minutes from the house"},
    {"name": "Seaside Cove", "lat": 45.99, "lon": -123.935, "sea": (45.99, -124.02), "faces": 290,
     "shelter": [135, 225], "note": "Cobblestone point under Tillamook Head; experienced surfers, holds bigger swell"},
    {"name": "Indian Beach (Ecola)", "lat": 45.93, "lon": -123.98, "sea": (45.93, -124.04), "faces": 280,
     "shelter": [], "note": "Cove in Ecola State Park ($5 day pass)"},
    {"name": "Short Sands (Oswald West)", "lat": 45.762, "lon": -123.962, "sea": (45.76, -124.02), "faces": 250,
     "shelter": [315, 360], "note": "Sheltered cove, often cleanest on summer north wind"},
]
# Clatsop Spit wave buoy first (closest), then the Columbia River Bar and Astoria Canyon buoys.
BUOYS = [("46243", "Clatsop Spit buoy"), ("46029", "Columbia River Bar buoy"), ("46248", "Astoria Canyon buoy")]
RATINGS = ["Flat", "Poor", "Fair", "Good", "Great"]


def _get(url, **params):
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)


def compass(deg):
    return None if deg is None else COMPASS[round(deg / 22.5) % 16]


def _diff(a, b):
    return abs((a - b + 180) % 360 - 180)


def surf_ft(swell_ft, period_s, swell_dir, faces):
    """Rough breaking face height: longer periods stand up taller; swell from the side wraps in smaller."""
    if not swell_ft:
        return 0.0
    grow = 0.8 if period_s < 9 else 1.0 if period_s < 12 else 1.25 if period_s < 15 else 1.45
    off = _diff(swell_dir, faces) if swell_dir is not None else 0
    reach = 1.0 if off <= 30 else 0.75 if off <= 60 else 0.45 if off <= 90 else 0.2
    return swell_ft * grow * reach


def wind_kind(speed, wind_from, brk):
    """Offshore when the wind blows from land to sea at the break."""
    if speed is None or wind_from is None or speed < 5:
        return "light"
    if any(_diff(wind_from, s) <= 25 for s in brk["shelter"]):
        return "sheltered"
    off = _diff(wind_from, brk["faces"])
    return "onshore" if off <= 60 else "cross" if off <= 120 else "offshore"


def rate(face_ft, period_s, wind, speed):
    if face_ft < 1.5:
        return 0
    score = 1 if face_ft < 2.5 else 2 if face_ft < 4 else 3
    score += 1 if period_s >= 12 else -1 if period_s < 8 else 0
    clean = wind in ("light", "offshore", "sheltered") and (speed or 0) < 18
    if clean:
        score += 1
    elif wind == "onshore":
        score -= 3 if (speed or 0) >= 12 else 1
    elif wind == "cross" and (speed or 0) >= 15:
        score -= 1
    if not clean:
        score = min(score, 3)  # Great needs clean wind
    if face_ft < 2.5:
        score = min(score, 2)  # knee to waist high is fair at best
    # Past about 12 ft most of this coast closes out; only the point holds it.
    if face_ft >= 12:
        score = min(score, 1)
    return max(1, min(4, score))


def _as_list(x):
    return x if isinstance(x, list) else [x]


def forecast(days=5):
    sea = _as_list(_get("https://marine-api.open-meteo.com/v1/marine",
                        latitude=",".join(str(b["sea"][0]) for b in BREAKS),
                        longitude=",".join(str(b["sea"][1]) for b in BREAKS),
                        timezone="America/Los_Angeles", forecast_days=days, length_unit="imperial",
                        hourly="wave_height,swell_wave_height,swell_wave_period,swell_wave_direction"))
    air = _as_list(_get("https://api.open-meteo.com/v1/forecast",
                        latitude=",".join(str(b["lat"]) for b in BREAKS),
                        longitude=",".join(str(b["lon"]) for b in BREAKS),
                        timezone="America/Los_Angeles", forecast_days=days, wind_speed_unit="mph",
                        hourly="wind_speed_10m,wind_direction_10m,is_day"))
    out = []
    for brk, m, w in zip(BREAKS, sea, air):
        mh, wh = m["hourly"], w["hourly"]
        wind_at = {t: i for i, t in enumerate(wh["time"])}
        hours = []
        for i, t in enumerate(mh["time"]):
            j = wind_at.get(t)
            swell = mh["swell_wave_height"][i]
            if swell is None:
                swell = mh["wave_height"][i]
            if swell is None:
                continue
            period = mh["swell_wave_period"][i] or 0
            sdir = mh["swell_wave_direction"][i]
            speed = wh["wind_speed_10m"][j] if j is not None else None
            wdir = wh["wind_direction_10m"][j] if j is not None else None
            face = surf_ft(swell, period, sdir, brk["faces"])
            kind = wind_kind(speed, wdir, brk)
            hours.append({"t": t, "day": bool(wh["is_day"][j]) if j is not None else 6 <= int(t[11:13]) < 18,
                          "face": face, "swell_ft": round(swell, 1), "period_s": round(period),
                          "swell_dir": compass(sdir), "wind_mph": round(speed) if speed is not None else None,
                          "wind_dir": compass(wdir), "wind": kind, "rating": rate(face, period, kind, speed)})
        out.append({"name": brk["name"], "note": brk["note"], "hours": hours})
    return out


def _range(face):
    lo = max(0, int(face))
    return f"{lo}-{lo + 1}" if face < 4 else f"{lo}-{round(face * 1.25)}"


def report(fc, now_local):
    """Per break: conditions now and the best daylight window for each day."""
    stamp = now_local.strftime("%Y-%m-%dT%H:00")
    out = []
    for b in fc:
        hours = b["hours"]
        if not hours:
            continue
        cur = next((h for h in hours if h["t"] >= stamp), hours[-1])
        days = []
        for day in sorted({h["t"][:10] for h in hours}):
            light = [h for h in hours if h["t"][:10] == day and h["day"] and (h["t"] >= stamp or day > stamp[:10])]
            if not light:
                continue
            best = max(light, key=lambda h: (h["rating"], -abs(h["face"] - 4)))
            # Stretch the window over neighbouring hours that rate the same.
            lo = hi = light.index(best)
            while lo > 0 and light[lo - 1]["rating"] == best["rating"]:
                lo -= 1
            while hi < len(light) - 1 and light[hi + 1]["rating"] == best["rating"]:
                hi += 1
            run = light[lo:hi + 1]
            days.append({"date": day, "rating": RATINGS[best["rating"]], "score": best["rating"],
                         "surf_ft": _range(best["face"]), "period_s": best["period_s"], "swell_dir": best["swell_dir"],
                         "wind_mph": best["wind_mph"], "wind_dir": best["wind_dir"], "wind": best["wind"],
                         "from": run[0]["t"][11:16], "to": run[-1]["t"][11:16]})
        out.append({"name": b["name"], "note": b["note"],
                    "now": {"rating": RATINGS[cur["rating"]], "score": cur["rating"], "surf_ft": _range(cur["face"]),
                            "swell_ft": cur["swell_ft"], "period_s": cur["period_s"], "swell_dir": cur["swell_dir"],
                            "wind_mph": cur["wind_mph"], "wind_dir": cur["wind_dir"], "wind": cur["wind"]},
                    "days": days})
    if not out:
        raise RuntimeError("the wave model returned no data for the breaks")
    return out


def parse_buoy(text, now_utc, max_age_h=3):
    rows = [l.split() for l in text.splitlines() if l and not l.startswith("#")]
    head = next((l.lstrip("#").split() for l in text.splitlines() if l.startswith("#YY")), None)
    if not head:
        raise RuntimeError("unexpected NDBC format")
    col = {name: i for i, name in enumerate(head)}
    num = lambda r, k: None if k not in col or r[col[k]] == "MM" else float(r[col[k]])
    for r in rows:
        if len(r) < len(head) or num(r, "WVHT") is None:
            continue
        at = dt.datetime(*(int(x) for x in r[:5]), tzinfo=dt.timezone.utc)
        if now_utc - at > dt.timedelta(hours=max_age_h):
            return None
        wtmp = num(r, "WTMP")
        return {"at": at.isoformat(), "wave_ft": round(num(r, "WVHT") * 3.281, 1),
                "period_s": round(num(r, "DPD")) if num(r, "DPD") is not None else None,
                "dir": compass(num(r, "MWD")), "water_f": round(wtmp * 9 / 5 + 32) if wtmp is not None else None}
    return None


def buoy(now_utc):
    for sid, name in BUOYS:
        try:
            req = urllib.request.Request(f"https://www.ndbc.noaa.gov/data/realtime2/{sid}.txt", headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                reading = parse_buoy(resp.read().decode("utf-8", "replace"), now_utc)
        except Exception:
            continue
        if reading:
            return {**reading, "station": name, "url": f"https://www.ndbc.noaa.gov/station_page.php?station={sid}"}
    raise RuntimeError("no recent reading from the nearby wave buoys")
