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

# Peak nights (month, day) and peak hourly rates (ZHR) in ideal dark skies, from the IMO 2026 meteor shower
# calendar (https://www.imo.net/files/meteor-shower/cal2026.pdf).
METEOR_SHOWERS = [
    (1, 3, "Quadrantids", 80), (4, 22, "Lyrids", 18), (5, 6, "Eta Aquariids", 50),
    (7, 31, "Southern Delta Aquariids", 25), (8, 13, "Perseids", 100), (10, 21, "Orionids", 20),
    (11, 17, "Leonids", 15), (12, 14, "Geminids", 150), (12, 22, "Ursids", 10),
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
    return {"moonrise": times.get("Rise"), "moonset": times.get("Set"), "transit": times.get("Upper Transit"),
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
                           "detail": f"Up to about {rate} an hour under ideal dark skies; {sky}.",
                           "visible": True, "kind": "meteors"})

    events.sort(key=lambda e: e["utc"])
    return events[:limit]


# ------------------------------------------------------------- satellites and launches

def iss_tle():
    """Current ISS orbit (two-line elements) from CelesTrak."""
    req = urllib.request.Request("https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        lines = [l.strip() for l in resp.read().decode().splitlines() if l.strip()]
    tle = [l for l in lines if l[:2] in ("1 ", "2 ")]
    if len(tle) != 2:
        raise RuntimeError("CelesTrak returned no ISS elements")
    return tle


def _sun_vec(when):
    """Unit vector to the sun in the same equatorial frame as SGP4's output (close enough to see a pass)."""
    d = (when - dt.datetime(2000, 1, 1, 12, tzinfo=dt.timezone.utc)).total_seconds() / 86400
    g = math.radians((357.529 + 0.98560028 * d) % 360)
    q = (280.459 + 0.98564736 * d) % 360
    lam = math.radians(q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.00000036 * d)
    return (math.cos(lam), math.cos(eps) * math.sin(lam), math.sin(eps) * math.sin(lam))


def _gmst(when):
    d = (when - dt.datetime(2000, 1, 1, 12, tzinfo=dt.timezone.utc)).total_seconds() / 86400
    return math.radians((280.46061837 + 360.98564736629 * d) % 360)


COMPASS16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def iss_passes(tle, lat, lon, now_utc, days=5, limit=4):
    """Evening and morning ISS passes you can see from home: the station is sunlit, high enough,
    and your sky is dark. Worked out minute by minute from the orbit."""
    from sgp4.api import Satrec, jday
    sat = Satrec.twoline2rv(tle[0], tle[1])
    re_km = 6378.137
    la, lo = math.radians(lat), math.radians(lon)
    # Observer position in Earth-fixed coordinates (spherical Earth is fine for this).
    obs = (re_km * math.cos(la) * math.cos(lo), re_km * math.cos(la) * math.sin(lo), re_km * math.sin(la))
    passes, cur = [], None
    t = now_utc.replace(second=0, microsecond=0)
    for _ in range(days * 24 * 60 * 2):
        t += dt.timedelta(seconds=30)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
        err, r, _v = sat.sgp4(jd, fr)
        if err:
            continue
        th = _gmst(t)
        # Rotate inertial to Earth-fixed.
        x = r[0] * math.cos(th) + r[1] * math.sin(th)
        y = -r[0] * math.sin(th) + r[1] * math.cos(th)
        z = r[2]
        dx, dy, dz = x - obs[0], y - obs[1], z - obs[2]
        # East, north, up at the observer.
        e = -math.sin(lo) * dx + math.cos(lo) * dy
        n = -math.sin(la) * math.cos(lo) * dx - math.sin(la) * math.sin(lo) * dy + math.cos(la) * dz
        u = math.cos(la) * math.cos(lo) * dx + math.cos(la) * math.sin(lo) * dy + math.sin(la) * dz
        rng = math.sqrt(dx * dx + dy * dy + dz * dz)
        alt = math.degrees(math.asin(u / rng))
        visible = False
        if alt >= 10 and sun_altitude(t, lat, lon) < -6:
            s = _sun_vec(t)
            dot = r[0] * s[0] + r[1] * s[1] + r[2] * s[2]
            perp = math.sqrt(max(0.0, (r[0] ** 2 + r[1] ** 2 + r[2] ** 2) - dot * dot))
            visible = dot > 0 or perp > re_km  # outside Earth's shadow
        az = (math.degrees(math.atan2(e, n)) + 360) % 360
        if visible:
            if cur is None:
                cur = {"start": t, "from": COMPASS16[round(az / 22.5) % 16], "max_alt": alt, "end": t, "to": None}
            cur["end"], cur["to"] = t, COMPASS16[round(az / 22.5) % 16]
            cur["max_alt"] = max(cur["max_alt"], alt)
        elif cur is not None:
            passes.append(cur)
            cur = None
            if len(passes) >= limit:
                break
    out = []
    for p in passes:
        minutes = max(1, round((p["end"] - p["start"]).total_seconds() / 60))
        out.append({"utc": p["start"].isoformat(), "minutes": minutes, "max_alt": round(p["max_alt"]),
                    "from": p["from"], "to": p["to"],
                    "bright": p["max_alt"] >= 40})
    return out


def launches():
    """Upcoming launches from Vandenberg, California. Ones near dusk or dawn can light up the sky over Oregon."""
    data = _get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/", location__ids=11, limit=8, mode="list")
    out = []
    for r in data.get("results") or []:
        status = (r.get("status") or {}).get("abbrev")
        if status in ("Success", "Failure", "Partial Failure"):
            continue
        out.append({"name": r.get("name"), "utc": r.get("net"), "status": status,
                    "confirmed": status == "Go" and (r.get("net_precision") or {}).get("abbrev") in ("SEC", "MIN"),
                    "url": "https://www.google.com/search?q=" + urllib.parse.quote((r.get("name") or "") + " launch")})
    return out


def launch_events(items, lat, lon, now_utc, limit=3):
    """Vandenberg launches in the next two weeks, flagged when the timing makes a show over Oregon likely:
    the sky here is dark but the rocket climbs into sunlight (sun 4 to 18 degrees below the horizon)."""
    out = []
    for x in items or []:
        try:
            when = dt.datetime.fromisoformat(x["utc"].replace("Z", "+00:00"))
        except (TypeError, ValueError, KeyError):
            continue
        if not now_utc - dt.timedelta(hours=1) <= when <= now_utc + dt.timedelta(days=14):
            continue
        sun = sun_altitude(when, lat, lon)
        show = -18 <= sun <= -4
        detail = ("Twilight launch: look south about 5 to 10 minutes after liftoff for a glowing plume."
                  if show else "From Vandenberg, California. Daytime or deep night, so not much to see from here.")
        if not x.get("confirmed"):
            detail += " Time not final."
        out.append({"utc": when.isoformat(), "title": x["name"].split("|")[-1].strip() + " launch",
                    "detail": detail, "visible": show, "kind": "launch"})
    shows = [e for e in out if e["visible"]]
    return (shows + [e for e in out if not e["visible"]])[:limit]


def stargazing(hours, moon_lit_pct, now_local):
    """Tonight's verdict from cloud cover between 9 pm and 1 am and how bright the moon is."""
    night = [h["cloud"] for h in hours if h.get("cloud") is not None and h["t"][:2] in ("21", "22", "23", "00")]
    if not night or now_local.hour < 6:
        return None
    cloud = round(sum(night) / len(night))
    if cloud >= 75:
        verdict = "Cloudy tonight"
    elif cloud >= 40:
        verdict = "Patchy clouds tonight"
    else:
        verdict = "Clear skies tonight" if moon_lit_pct < 50 else "Clear tonight, but a bright moon"
    return {"cloud": cloud, "verdict": verdict, "good": cloud < 40 and moon_lit_pct < 50}


def apod(key="DEMO_KEY"):
    """NASA's Astronomy Picture of the Day. DEMO_KEY allows about 50 calls a day per IP, plenty at a few a day."""
    url = "https://api.nasa.gov/planetary/apod?" + urllib.parse.urlencode({"api_key": key, "thumbs": "true"})
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        a = json.load(r)
    video = a.get("media_type") == "video"
    image = a.get("thumbnail_url") if video else a.get("url")
    if not image:
        return None
    return {"date": a.get("date"), "title": (a.get("title") or "").strip(), "image": image,
            "explanation": (a.get("explanation") or "").strip(), "credit": (a.get("copyright") or "").strip() or None,
            "video": a.get("url") if video else None,
            "page": f"https://apod.nasa.gov/apod/ap{a['date'][2:4]}{a['date'][5:7]}{a['date'][8:10]}.html" if a.get("date") else
                    "https://apod.nasa.gov/apod/astropix.html"}
