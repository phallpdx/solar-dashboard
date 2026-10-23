"""Moon and sky events: phases, moonrise, eclipses, meteor showers, aurora.

Moon times and phase dates come from the US Naval Observatory API when it
answers, with a built-in calculation as the fallback. Eclipse dates are a
curated list (NASA eclipse catalog); whether each one is visible from home is
worked out here from where the sun is at that moment.
"""
import datetime as dt
import json
import math
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
SYNODIC = 29.530588853
KNOWN_NEW_MOON = dt.datetime(2000, 1, 6, 18, 14, tzinfo=dt.timezone.utc)

# (date, max time UTC, kind, where it's seen, note). NASA eclipse catalog.
ECLIPSES = [
    ("2027-02-06", "16:00", "Annular solar eclipse", "South America, the South Atlantic and West Africa", None),
    ("2027-02-20", "23:13", "Penumbral lunar eclipse", None, "A subtle shading on the moon"),
    ("2027-07-18", "16:03", "Penumbral lunar eclipse", None, "Very slight; barely noticeable"),
    ("2027-08-02", "10:07", "Total solar eclipse", "Spain, North Africa and Egypt, over 6 minutes of totality", None),
    ("2027-08-17", "07:14", "Penumbral lunar eclipse", None, "A subtle shading on the moon"),
    ("2028-01-12", "04:13", "Partial lunar eclipse", None, "A small bite out of the moon"),
    ("2028-01-26", "15:08", "Annular solar eclipse", "Ecuador, Peru, Brazil, Spain and Portugal", None),
    ("2028-07-06", "18:20", "Partial lunar eclipse", None, None),
    ("2028-07-22", "02:56", "Total solar eclipse", "Australia and New Zealand", None),
    ("2028-12-31", "16:52", "Total lunar eclipse", None, "The moon turns red"),
    ("2029-01-14", "17:13", "Partial solar eclipse", "North America", None),
]

# Peak nights (month, day) and typical hourly rates in dark skies (IMO calendar).
METEOR_SHOWERS = [
    (1, 3, "Quadrantids", 80), (4, 22, "Lyrids", 18), (5, 6, "Eta Aquariids", 30),
    (7, 30, "Southern Delta Aquariids", 20), (8, 12, "Perseids", 100), (10, 21, "Orionids", 20),
    (11, 17, "Leonids", 15), (12, 14, "Geminids", 120), (12, 22, "Ursids", 10),
]


def _get(url, **params):
    url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


# ------------------------------------------------------------- calculations

def moon_age(when):
    """Days since new moon (0-29.5) for an aware datetime."""
    return ((when - KNOWN_NEW_MOON).total_seconds() / 86400) % SYNODIC


def moon_state(when):
    age = moon_age(when)
    frac = age / SYNODIC
    lit = (1 - math.cos(2 * math.pi * frac)) / 2
    names = ["New moon", "Waxing crescent", "First quarter", "Waxing gibbous",
             "Full moon", "Waning gibbous", "Last quarter", "Waning crescent"]
    return {"name": names[int(frac * 8 + 0.5) % 8], "lit_pct": round(lit * 100),
            "age_days": round(age, 1), "waxing": frac < 0.5}


def mean_phases(start, count=4):
    """Approximate next new/first quarter/full/last quarter moments (within ~half a day)."""
    names = ["New Moon", "First Quarter", "Full Moon", "Last Quarter"]
    age = moon_age(start)
    out = []
    k = int(age // (SYNODIC / 4)) + 1
    while len(out) < count:
        when = start + dt.timedelta(days=k * SYNODIC / 4 - age)
        out.append({"phase": names[k % 4], "utc": when.isoformat(), "approx": True})
        k += 1
    return out


def sun_altitude(when, lat, lon):
    """Sun altitude in degrees (good to a fraction of a degree)."""
    d = (when - dt.datetime(2000, 1, 1, 12, tzinfo=dt.timezone.utc)).total_seconds() / 86400
    g = math.radians((357.529 + 0.98560028 * d) % 360)
    q = (280.459 + 0.98564736 * d) % 360
    ecl_lon = math.radians(q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.00000036 * d)
    ra = math.atan2(math.cos(eps) * math.sin(ecl_lon), math.cos(ecl_lon))
    dec = math.asin(math.sin(eps) * math.sin(ecl_lon))
    gmst = (280.46061837 + 360.98564736629 * d) % 360
    ha = math.radians(gmst + lon) - ra
    la = math.radians(lat)
    return math.degrees(math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha)))


# ------------------------------------------------------------- live sources

def usno_day(day, lat, lon, tz_hours):
    """Moonrise, moonset and USNO's phase name for one local day."""
    data = _get("https://aa.usno.navy.mil/api/rstt/oneday", date=day.isoformat(),
                coords=f"{lat},{lon}", tz=tz_hours)
    props = data["properties"]["data"]
    times = {p["phen"]: p["time"][:5] for p in props.get("moondata", [])}
    return {"moonrise": times.get("Rise"), "moonset": times.get("Set"),
            "phase": props.get("curphase"), "lit": props.get("fracillum")}


def usno_phases(day, count=4):
    data = _get("https://aa.usno.navy.mil/api/moon/phases/date", date=day.isoformat(), nump=count)
    out = []
    for p in data.get("phasedata", []):
        when = dt.datetime(p["year"], p["month"], p["day"], *map(int, p["time"].split(":")),
                           tzinfo=dt.timezone.utc)
        out.append({"phase": p["phase"], "utc": when.isoformat(), "approx": False})
    return out


def aurora():
    """Highest planetary Kp forecast over the next ~3 days (NOAA SWPC)."""
    rows = _get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json")
    # The feed has been both a header row plus lists, and a list of objects.
    if rows and isinstance(rows[0], list):
        rows = [dict(zip(rows[0], r)) for r in rows[1:]]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H")
    future = [r for r in rows if str(r.get("time_tag", "")).replace(" ", "T")[:13] >= now
              and r.get("observed") in ("predicted", "estimated")]
    if not future:
        return None
    top = max(future, key=lambda r: float(r["kp"]))
    return {"kp": float(top["kp"]), "when_utc": str(top["time_tag"]).replace(" ", "T")[:16] + ":00+00:00"}


# ------------------------------------------------------------- events list

def upcoming_events(now_utc, lat, lon, limit=8):
    events = []
    for date, hhmm, kind, where, note in ECLIPSES:
        when = dt.datetime.fromisoformat(f"{date}T{hhmm}:00+00:00")
        if when < now_utc - dt.timedelta(days=1):
            continue
        if "lunar" in kind:
            # A lunar eclipse is seen wherever the moon is up, i.e. where the sun is down.
            visible = sun_altitude(when, lat, lon) < -1
            if not visible:
                continue  # nothing to see, so leave it off the list
            detail = (note + ". " if note else "") + "Visible from home."
        else:
            visible = where == "North America"
            detail = f"Seen from {where}." + ("" if visible else " Not visible from Oregon.")
        events.append({"utc": when.isoformat(), "title": kind, "detail": detail,
                       "visible": visible, "kind": "eclipse"})

    for year in (now_utc.year, now_utc.year + 1):
        for month, day, name, rate in METEOR_SHOWERS:
            # Peak is overnight; judge the moon at 3 am Pacific (about 11:00 UTC).
            when = dt.datetime(year, month, day, 11, tzinfo=dt.timezone.utc)
            if when < now_utc - dt.timedelta(hours=12):
                continue
            lit = moon_state(when)["lit_pct"]
            sky = ("dark skies, great timing" if lit < 25 else
                   "some moonlight" if lit < 60 else "a bright moon will wash out fainter ones")
            events.append({"utc": when.isoformat(), "title": f"{name} meteor shower peak",
                           "detail": f"Up to about {rate} an hour after midnight; {sky}.",
                           "visible": True, "kind": "meteors"})

    events.sort(key=lambda e: e["utc"])
    return events[:limit]
