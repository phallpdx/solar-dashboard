"""Tonight's sky and tomorrow's weather for the evening edition, worked out from dashboard.json.

Planets and the moon come from PyEphem (pip install ephem); without it those lines are left out.
Everything here follows the edition's bedtime rules: only what can be seen from home tonight, late
events only when they are rare, and never a reason to set an alarm.
"""
import datetime as dt
import math
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Los_Angeles")
POINTS = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
SHORT = {"N": "north", "NNE": "north-northeast", "NE": "northeast", "ENE": "east-northeast", "E": "east",
         "ESE": "east-southeast", "SE": "southeast", "SSE": "south-southeast", "S": "south", "SSW": "south-southwest",
         "SW": "southwest", "WSW": "west-southwest", "W": "west", "WNW": "west-northwest", "NW": "northwest",
         "NNW": "north-northwest"}
BIG_SHOWERS = {"Quadrantids", "Perseids", "Geminids", "Eta Aquariids"}  # 50+ an hour: worth a late night
LATE = dt.time(22, 30)  # after this, only rare things get a mention


def clock(t):
    """7:42 pm, 9 pm, midnight."""
    if t.hour == 0 and t.minute == 0:
        return "midnight"
    s = f"{t.hour % 12 or 12}" + (f":{t.minute:02d}" if t.minute else "")
    return s + (" am" if t.hour < 12 else " pm")


def hhmm(s):
    h, m = (int(x) for x in s.split(":"))
    return clock(dt.time(h, m))


def compass(az_deg):
    return POINTS[int((az_deg % 360) / 45 + 0.5) % 8]


def height(alt_deg):
    return "low" if alt_deg < 20 else "high" if alt_deg > 55 else "halfway up"


def evening_of(now_local):
    """The evening this edition is for: before 4 am it is still last night."""
    return (now_local - dt.timedelta(hours=4)).date()


# ------------------------------------------------------------------ planets and moon

def _observer(lat, lon, when_utc):
    import ephem
    o = ephem.Observer()
    o.lat, o.lon, o.elevation = str(lat), str(lon), 5
    o.pressure = 0  # no refraction: rise and set to the minute is plenty
    o.date = when_utc.replace(tzinfo=None)
    return o


def _local(d):
    import ephem
    return ephem.Date(d).datetime().replace(tzinfo=dt.timezone.utc).astimezone(TZ)


def dusk(night, lat, lon):
    """When the sky is dark enough to see planets (sun 8° down), and sunset, for an evening."""
    import ephem
    start = dt.datetime.combine(night, dt.time(12), TZ).astimezone(dt.timezone.utc)
    o = _observer(lat, lon, start)
    sunset = _local(o.next_setting(ephem.Sun()))
    o.horizon = "-8"
    dark = _local(o.next_setting(ephem.Sun(), use_center=True))
    return sunset, dark


def planets(night, lat, lon):
    """Bright planets up between dark and 11 pm: where to look, how high, when they set.
    Brightest first."""
    import ephem
    sunset, dark = dusk(night, lat, lon)
    end = dt.datetime.combine(night, dt.time(23), TZ)
    out = []
    for name, body in (("Venus", ephem.Venus()), ("Jupiter", ephem.Jupiter()), ("Mars", ephem.Mars()),
                       ("Saturn", ephem.Saturn()), ("Mercury", ephem.Mercury())):
        # Venus and Mercury hang low in the twilight, bright enough to see before full dark.
        inner = name in ("Venus", "Mercury")
        t, seen = (sunset + dt.timedelta(minutes=20) if inner else dark), None
        while t <= end:
            o = _observer(lat, lon, t.astimezone(dt.timezone.utc))
            body.compute(o)
            alt = math.degrees(body.alt)
            if alt >= (5 if inner else 10):
                seen = (t, alt, math.degrees(body.az), body.mag)
                break
            t += dt.timedelta(minutes=15)
        if not seen:
            continue
        when, alt, az, mag = seen
        if name == "Mercury" and mag > 0.5:
            continue
        if name == "Mars" and mag > 1.4:
            continue
        o = _observer(lat, lon, when.astimezone(dt.timezone.utc))
        try:
            sets = _local(o.next_setting(body))
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            sets = None
        # Where it is at 9 pm (or when it first clears the trees, if later), which is when most people look.
        look = max(when, dt.datetime.combine(night, dt.time(21), TZ))
        if sets and look > sets:
            look = when
        o = _observer(lat, lon, look.astimezone(dt.timezone.utc))
        body.compute(o)
        out.append({"name": name, "mag": round(body.mag, 1), "first": when, "look": look,
                    "alt": round(math.degrees(body.alt)), "dir": compass(math.degrees(body.az)),
                    "sets": sets if sets and sets.date() <= night + dt.timedelta(days=1) else None})
    out.sort(key=lambda p: p["mag"])
    return out


def moon(night, lat, lon):
    """The moon in the evening (7 to 10 pm), or None when it isn't up then."""
    import ephem
    m = ephem.Moon()
    best = None
    for hour in (19, 20, 21, 22):
        o = _observer(lat, lon, dt.datetime.combine(night, dt.time(hour), TZ).astimezone(dt.timezone.utc))
        m.compute(o)
        alt = math.degrees(m.alt)
        if alt > 3 and (best is None or hour == 21):
            best = (hour, alt, math.degrees(m.az), o)
    o = _observer(lat, lon, dt.datetime.combine(night, dt.time(21), TZ).astimezone(dt.timezone.utc))
    m.compute(o)
    lit = round(m.phase)
    waxing = (o.date - ephem.previous_new_moon(o.date)) < 14.77
    if 45 <= lit <= 55:
        name = "First quarter" if waxing else "Last quarter"
    elif lit > 97:
        name = "Full moon"
    else:
        name = ("Waxing" if waxing else "Waning") + (" crescent" if lit < 50 else " gibbous")
    if lit < 3 or not best:
        return None
    hour, alt, az, ob = best
    rise = sets = None
    try:
        start = _observer(lat, lon, dt.datetime.combine(night, dt.time(17), TZ).astimezone(dt.timezone.utc))
        m.compute(start)
        if m.alt <= 0:
            rise = _local(start.next_rising(m))
        sets = _local(ob.next_setting(m))
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        pass
    return {"name": name, "lit": lit, "alt": round(alt), "dir": compass(az), "hour": hour, "rise": rise, "sets": sets}


def _lit_words(lit):
    return ("a thin sliver" if lit < 15 else "a quarter lit" if lit < 35 else "half lit" if lit < 60
            else "mostly lit" if lit < 90 else "nearly full" if lit < 98 else "full")


def _when_sets(t, night):
    if t is None:
        return "up all night"
    if t.date() > night and t.hour >= 4:
        return "up all night"
    if t.date() > night or t.hour >= 23:
        return "sets after midnight" if t.date() > night else f"sets at {clock(t.timetz())}"
    return f"sets at {clock(t.timetz())}"


def moon_line(m, night):
    if not m:
        return None
    if m["name"] == "Full moon":
        phase = "Full"
    else:
        phase = f"{m['name']}, {_lit_words(m['lit'])}"
    if m["rise"] and m["rise"].hour >= 19:
        where = f"rises at {clock(m['rise'].timetz())} in the east"
    else:
        where = f"{height(m['alt'])} in the {m['dir']}" + ("" if m["hour"] == 21 else f" at {clock(dt.time(m['hour']))}")
    return f"{phase}, {where}; {_when_sets(m['sets'], night)}."


LOOKS = {"Venus": "the brightest light in the sky after the moon", "Jupiter": "a bright, steady light",
         "Mars": "a steady, rusty-orange light", "Saturn": "a steady, pale gold light", "Mercury": "a small steady light in the glow"}


def planet_line(p, night):
    if p["look"].hour >= 21 and p["look"] == p["first"] and p["first"].hour >= 21 and p["first"].minute:
        where = f"{p['dir'].capitalize()}, clearing the trees around {clock(p['first'].timetz())}"
    else:
        where = f"{height(p['alt']).capitalize()} in the {p['dir']}" + (
            "" if p["look"].hour == 21 and not p["look"].minute else f" at {clock(p['look'].timetz())}")
    return f"{where}, {LOOKS[p['name']]}; {_when_sets(p['sets'], night)}."


# ------------------------------------------------------------------ tonight's sky

def _parse_utc(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def tonight(d, now_local):
    """Tonight's sky page: a headline, up to five lines (moon, planets, station), an optional
    'if you want to' paragraph for a rare event, and the cloud verdict."""
    import re
    o = d.get("outside") or {}
    lat, lon = o.get("lat") or 45.7, o.get("lon") or -122.8
    night = evening_of(now_local)
    out = {"night": night, "items": [], "choice": None, "clouds": None, "later": None, "headline": None}
    brightest = None
    try:
        mo = moon(night, lat, lon)
        if mo:
            out["items"].append(("Moon", moon_line(mo, night)))
        pl = [p for p in planets(night, lat, lon) if p["mag"] <= 1.5][:3]
        for p in pl:
            out["items"].append((p["name"], planet_line(p, night)))
        if pl:
            brightest = pl[0]
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001 - the rest of the sky still prints
        print(f"evening: planets/moon skipped ({e!r})")

    start = dt.datetime.combine(night, dt.time(16), TZ)
    late = dt.datetime.combine(night, LATE, TZ)
    for p in o.get("iss") or []:
        t = _parse_utc(p["utc"]).astimezone(TZ)
        if start <= t <= late and (p.get("max_alt") or 0) >= 40 and p.get("bright"):
            out["items"].append(("Space station",
                                 f"{clock(t.timetz())}, {SHORT.get(p['from'], p['from'])} to {SHORT.get(p['to'], p['to'])}, "
                                 f"high and bright, about {p.get('minutes') or 4} minutes. A steady moving star, no blinking."))
            break

    for e in o.get("sky_events") or []:
        if e.get("kind") != "meteors":
            continue
        peak = _parse_utc(e["utc"]).astimezone(TZ)  # about 3 am, the morning after the peak night
        if (peak - dt.timedelta(hours=12)).date() != night:
            continue
        name = e["title"].replace(" meteor shower peak", "")
        m = re.search(r"about (\d+) an hour", e.get("detail", ""))
        rate = int(m.group(1)) if m else 0
        if rate >= 50:
            out["choice"] = (f"The {name} peak tonight, one of the best showers of the year: up to {rate} an hour from a dark "
                             f"spot after 10 pm. If you'd rather sleep, ten minutes outside before bed still shows a few.")
        else:
            out["items"].append(("Meteors", f"The {name} peak tonight, a light shower of a few an hour, mostly before dawn. "
                                            "Not one to stay up for."))

    au = o.get("aurora_now") or {}
    if (au.get("here_pct") or 0) >= 30 or (au.get("north_pct") or 0) >= 50:
        out["choice"] = ((out["choice"] + " ") if out["choice"] else "") + (
            "There's a real chance of northern lights tonight. Look low over the northern horizon from somewhere dark; "
            "a phone camera picks up more colour than your eyes. Ten minutes outside is enough to know.")

    nights = o.get("nights") or []
    tn = next((n for n in nights if n.get("night") == night.isoformat()), None)
    verdict = tn.get("verdict") if tn else None
    if not verdict:
        hrs = [h.get("cloud") for h in o.get("next_hours") or [] if "19:00" <= h["t"] <= "23:00" and h.get("cloud") is not None]
        if hrs:
            c = sum(hrs) / len(hrs)
            verdict = "Clouded out" if c >= 85 else "Some gaps" if c >= 40 else "Clear"
    out["clouds"] = verdict
    if verdict == "Clouded out":
        better = next((n for n in nights if n.get("night", "") > night.isoformat() and n.get("verdict") != "Clouded out"), None)
        if better:
            day = dt.date.fromisoformat(better["night"])
            label = "Tomorrow night" if day == night + dt.timedelta(days=1) else day.strftime("%A night")
            out["later"] = f"{label} looks clearer."
        else:
            out["later"] = "The next few nights stay cloudy."
        out["headline"] = "Clouded out tonight"
        if out["choice"]:  # a rare event behind cloud: say so once, gently
            out["later"] = "It would have been a good night for a look up, but the clouds have it. " + out["later"]
            out["choice"] = None
        return out
    star = brightest["name"] if brightest else ("the moon" if any(k == "Moon" for k, _ in out["items"]) else None)
    if star and brightest:
        star = f"{star} in the {brightest['dir']}"
    lead = {"Clear and steady": "Clear and steady", "Clear but twinkly": "Clear and twinkly", "Some gaps": "Some clear gaps",
            "Clear": "Clear skies"}.get(verdict or "", None)
    if lead and star:
        out["headline"] = f"{lead}, with {star}"
    elif lead:
        out["headline"] = lead + " tonight"
    elif star:
        out["headline"] = f"{star[0].upper() + star[1:]} tonight"
    else:
        out["headline"] = "A quiet sky tonight"
    return out



# ------------------------------------------------------------------ tomorrow's weather

WMO = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "cloudy", 45: "foggy", 48: "foggy with frost",
       51: "light drizzle", 53: "drizzle", 55: "steady drizzle", 56: "freezing drizzle", 57: "freezing drizzle",
       61: "light rain", 63: "rain", 65: "heavy rain", 66: "freezing rain", 67: "freezing rain",
       71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains", 80: "showers", 81: "showers",
       82: "heavy showers", 85: "snow showers", 86: "snow showers", 95: "thunderstorms", 96: "thunderstorms with hail",
       99: "thunderstorms with hail"}


def tomorrow(d, now_local):
    o = d.get("outside") or {}
    night = evening_of(now_local)
    day = night + dt.timedelta(days=1)
    f = next((x for x in o.get("days") or [] if x.get("date") == day.isoformat()), None)
    if not f:
        return None
    # The hourly strip runs 24 hours from the last update; give each hour its date.
    hours, cur = [], None
    base = dt.datetime.fromisoformat(d["generated_at"]).astimezone(TZ) if d.get("generated_at") else now_local
    date, last = base.date(), None
    for h in o.get("next_hours") or []:
        if last is not None and h["t"] < last:
            date += dt.timedelta(days=1)
        last = h["t"]
        hours.append((date, h))
    wet = [h for dd, h in hours if dd == day and "06:00" <= h["t"] <= "21:00" and (h.get("rain_pct") or 0) >= 50]
    rain_in = f.get("rain_in") or 0
    hi, lo = round(f["hi"]), round(f["lo"])
    sky = WMO.get(f.get("code"), "")
    if rain_in >= 0.05 or (f.get("rain_pct") or 0) >= 60:
        if wet and wet[0]["t"] > "08:00":
            lead = f"Dry morning, rain from about {hhmm(wet[0]['t'])}; bring a hood."
            timing = f"Rain from about {hhmm(wet[0]['t'])}" + (f", easing by {hhmm(wet[-1]['t'])}" if wet[-1]["t"] < "20:00" else ", on and off into the evening") + "."
        else:
            lead = "Rain on and off through the day; bring a hood."
            timing = None
        amount = f"About {_inches(rain_in)} in all." if rain_in >= 0.1 else "Not much of it."
    elif (f.get("snow_in") or 0) > 0.1:
        lead, timing, amount = "Snow is possible; allow extra time on the bridge.", None, None
    else:
        lead = {"clear": "A clear, dry day.", "mostly clear": "Mostly sunny and dry.", "partly cloudy": "A dry day with some sun.",
                "cloudy": "Grey but dry.", "foggy": "A foggy start, then dry."}.get(sky, "A dry day.")
        timing, amount = None, None
    wind = None
    gust = f.get("gust") or 0
    if gust >= 30:
        wind = f"Gusty, up to {round(gust, -1):.0f} mph; tie down anything loose tonight."
    elif (f.get("wind") or 0) >= 15:
        wind = f"Breezy, around {round(f['wind'])} mph."
    plan = ("Good for getting outside." if rain_in < 0.05 and (f.get("rain_pct") or 0) < 40 and gust < 30 else
            f"Outdoor jobs go best before {hhmm(wet[0]['t'])}." if wet and wet[0]["t"] > "10:00" else
            "An indoor kind of day." if rain_in >= 0.25 else "Rain gear handles it.")
    alerts = [a.get("event") or a.get("headline") for a in (d.get("alerts") or {}).get("official") or []
              if (a.get("event") or a.get("headline"))]
    return {"date": day, "hi": hi, "lo": lo, "sky": sky, "lead": lead, "timing": timing, "amount": amount, "wind": wind,
            "sunrise": hhmm(f["sunrise"]) if f.get("sunrise") else None, "sunset": hhmm(f["sunset"]) if f.get("sunset") else None,
            "plan": plan, "alerts": alerts[:1], "rain_pct": f.get("rain_pct"), "rain_in": rain_in}


def _inches(x):
    if x < 0.15:
        return "a tenth of an inch"
    if x < 0.35:
        return "a quarter inch"
    if x < 0.65:
        return "half an inch"
    if x < 0.9:
        return "three quarters of an inch"
    return f"{round(x, 1):g} inches"
