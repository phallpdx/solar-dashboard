"""Fetch solar, weather and PGE data and write dashboard.json.

Run once an hour. APsystems allows about 1,000 calls a month, so this spends
one call per daytime run plus two a day, and refuses to go past
APS_MONTHLY_BUDGET (default 850). Everything fetched is cached in state.json.

Settings come from environment variables:
  APSYSTEMS_APP_ID, APSYSTEMS_APP_SECRET, APSYSTEMS_SID   solar (required)
  AMBIENT_API_KEY, AMBIENT_APP_KEY                        weather (optional)
  PGE_CYCLE_START_DAY                                     bill cycle start day (optional)
  HOME_ADDRESS                                            for forecast, air, tides, birds
  DATA_DIR                                                where state.json, dashboard.json
                                                          and pge/*.csv live (default ./data)
"""
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
import time
import traceback
from zoneinfo import ZoneInfo

from . import alerts, almanac, ambient, aps, birds, civics, coastsafety, culture, daily, deals, fishing, garden, gear, grid, health, live, markets, mycal, nature, news, outside, pge, places, poems, pollen, releases, roads, science, ships, ski, sky, sports, surf, world

DATA_DIR = os.environ.get("DATA_DIR", "data")
BUDGET = int(os.environ.get("APS_MONTHLY_BUDGET", "850"))
MIN_GAP_MIN = int(os.environ.get("APS_MIN_MINUTES", "50"))
# Google lists 5,000 free Pollen API calls a month; never go past that.
POLLEN_MONTHLY_CAP = int(os.environ.get("POLLEN_MONTHLY_CAP", "5000"))
DAY_START, DAY_END = 6, 20  # local hours when panels get polled
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


LEGACY_ZONES = {"US/Pacific": "America/Los_Angeles", "US/Mountain": "America/Denver",
                "US/Central": "America/Chicago", "US/Eastern": "America/New_York",
                "US/Arizona": "America/Phoenix", "US/Alaska": "America/Anchorage",
                "US/Hawaii": "Pacific/Honolulu"}


def zone(name):
    """APsystems reports legacy names like US/Pacific; map them to ones every system has."""
    name = LEGACY_ZONES.get(name or "", name or "America/Los_Angeles")
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("America/Los_Angeles")


def env(name):
    return (os.environ.get(name) or "").strip()


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------- APsystems

def fetch_solar(state, now_utc):
    sid = env("APSYSTEMS_SID")
    if not (env("APSYSTEMS_APP_ID") and env("APSYSTEMS_APP_SECRET")):
        return "Add your APsystems App ID and Secret."
    if not sid:
        return "Add your APsystems System ID (SID)."

    month_key = now_utc.strftime("%Y-%m")
    calls = state.setdefault("calls", {"month": month_key, "count": 0})
    if calls["month"] != month_key:
        calls.update(month=month_key, count=0)

    def count(_path):
        if calls["count"] >= BUDGET:
            raise RuntimeError(f"Paused: used {calls['count']} APsystems calls this month")
        calls["count"] += 1

    client = aps.Client(env("APSYSTEMS_APP_ID"), env("APSYSTEMS_APP_SECRET"), count)
    solar = state.setdefault("solar", {})

    if solar.get("sid") != sid:
        solar.clear()
        solar["sid"] = sid
    if "details" not in solar:
        details = client.details(sid)
        details.pop("authorization_code", None)  # never store the EMA login token
        solar["details"] = details
        solar["ecus"] = client.inverters(sid)

    tz = zone(solar["details"].get("timezone"))
    now = now_utc.astimezone(tz)
    today = now.strftime("%Y-%m-%d")
    last = solar.get("last_power_fetch")
    gap_ok = not last or (now_utc - dt.datetime.fromisoformat(last)).total_seconds() > MIN_GAP_MIN * 60
    first_run_today = solar.get("power_day") != today and now.hour >= DAY_START
    evening_final = now.hour > DAY_END and solar.get("final_day") != today

    # Daily totals for this month (and last month once, for the 30-day chart).
    if first_run_today or evening_final:
        months = solar.setdefault("months", {})
        months[now.strftime("%Y-%m")] = client.energy(sid, "daily", now.strftime("%Y-%m"))
        prev = (now.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
        if prev not in months:
            months[prev] = client.energy(sid, "daily", prev)
        solar["summary"] = client.summary(sid)

    # Same dates last year: two months of daily totals once (they never change),
    # plus last year's hour-by-hour curve for today's date, once a day.
    months = solar.setdefault("months", {})
    ly_today = year_ago(now.date())
    for d in (ly_today - dt.timedelta(days=30), ly_today):
        if d.strftime("%Y-%m") not in months:
            months[d.strftime("%Y-%m")] = client.energy(sid, "daily", d.strftime("%Y-%m"))
    if solar.get("ly_hourly_day") != today and now.hour >= DAY_START:
        try:
            solar["ly_hourly"] = client.energy(sid, "hourly", ly_today.isoformat())
        except aps.APSError as e:
            if e.code not in (1000, 1001):
                raise
            solar["ly_hourly"] = []
        solar["ly_hourly_day"] = today

    # Every panel's power through the day: one call per ECU.
    if (DAY_START <= now.hour <= DAY_END and gap_ok) or first_run_today or evening_final:
        series = {}
        for ecu in solar["ecus"]:
            if ecu.get("inverter"):
                try:
                    series[ecu["eid"]] = client.batch_power(sid, ecu["eid"], today)
                except aps.APSError as e:
                    if e.code not in (1000, 1001):  # "no data" just means no sun yet
                        raise
        solar["power"] = series
        solar["power_day"] = today
        # Remember every channel that has ever made power. Dual-channel microinverters can have an input
        # with no panel wired to it; those never produce and are left off the panel grid.
        live = set(solar.get("ever_live") or [])
        for data in series.values():
            for key, values in (data.get("power") or {}).items():
                if max((fnum(v) for v in values), default=0) >= 5:
                    live.add(key)
        solar["ever_live"] = sorted(live)
        solar["last_power_fetch"] = now_utc.isoformat()
        if evening_final:
            solar["final_day"] = today
    return None


def year_ago(day):
    try:
        return day.replace(year=day.year - 1)
    except ValueError:  # Feb 29
        return day.replace(year=day.year - 1, day=28)


def solar_view(state, now_utc):
    solar = state.get("solar") or {}
    if "details" not in solar:
        return None
    details = solar["details"]
    tz = zone(details.get("timezone"))
    now = now_utc.astimezone(tz)
    today = now.strftime("%Y-%m-%d")

    # Sum all panels into one curve; keep each panel's latest reading.
    curve, panels = {}, {}
    if solar.get("power_day") == today:
        for data in (solar.get("power") or {}).values():
            times = data.get("time") or []
            for key, values in (data.get("power") or {}).items():
                vals = [fnum(v) for v in values]
                kwh = sum((a + b) / 2 / 1000 * h for a, b, h in
                          zip(vals, vals[1:], _step_hours(times)))
                panels[key] = (vals[-1] if vals else 0.0, kwh)
                for t, v in zip(times, vals):
                    curve[t] = curve.get(t, 0.0) + v
    times = sorted(curve)
    points = [{"t": t, "kw": round(curve[t] / 1000, 3)} for t in times]

    kwh_today = sum((curve[a] + curve[b]) / 2 / 1000 * h
                    for a, b, h in zip(times, times[1:], _step_hours(times)))

    # Daily history from the monthly series (today's entry may be partial).
    daily = {}
    for month, values in sorted((solar.get("months") or {}).items()):
        for i, v in enumerate(values or [], start=1):
            daily[f"{month}-{i:02d}"] = fnum(v)
    summary = solar.get("summary") or {}
    kwh_today = max(kwh_today, fnum(summary.get("today")) if solar.get("power_day") == today else 0)
    daily[today] = round(kwh_today, 2)

    pace = None
    lit = [p for p in points if p["kw"] > 0.02]
    if lit and now.hour < 19:
        first = _minutes(lit[0]["t"])
        noon = 13 * 60 if now.dst() else 12 * 60
        sunset = 2 * noon - first
        elapsed = min(max(now.hour * 60 + now.minute - first, 0) / max(sunset - first, 1), 1)
        import math
        frac = (1 - math.cos(math.pi * elapsed)) / 2  # share of a sunny day's energy so far
        if frac > 0.15:
            pace = round(kwh_today / frac, 1)

    # Judge panels on energy so far today, not the latest reading: late in the
    # day roof angles and shade make instant watts uneven even on healthy panels.
    # Channels that have never made power (no panel attached) drop out once others are producing.
    ever = set(solar.get("ever_live") or [])
    if ever and any(panels[k][1] > 0.05 for k in panels):
        panels = {k: v for k, v in panels.items() if k in ever}
    names = sorted(panels, key=_panel_sort)
    median = statistics.median(panels[k][1] for k in names) if names else 0
    panel_list = [{
        "id": f"P{i + 1}",
        "key": k,
        "w": round(panels[k][0]),
        "kwh": round(panels[k][1], 2),
        "dead": bool(median > 0.2 and panels[k][1] < 0.05 * median),
        "low": bool(median > 0.2 and panels[k][1] < 0.6 * median),
    } for i, k in enumerate(names)]

    ly_date = year_ago(now.date()).isoformat()
    ly_hourly = [fnum(v) for v in solar.get("ly_hourly") or []] if solar.get("ly_hourly_day") == today else []
    # Last year at this time of day, from the hourly totals (each hour's kWh = its average kW).
    ly_so_far = sum(v for h, v in enumerate(ly_hourly) if h < now.hour) + \
        (ly_hourly[now.hour] * now.minute / 60 if now.hour < len(ly_hourly) else 0)
    last_year = {
        "date": ly_date,
        "day_kwh": daily.get(ly_date),
        "so_far_kwh": round(ly_so_far, 1) if ly_hourly else None,
        "curve": [{"t": f"{h:02d}:30", "kw": round(v, 2)} for h, v in enumerate(ly_hourly)],
    }

    return {
        "last_year": last_year,
        "capacity_kw": fnum(details.get("capacity")),
        "timezone": str(tz),
        "now_kw": points[-1]["kw"] if points else 0.0,
        "as_of": f"{today} {times[-1]}" if times else None,
        "today_kwh": round(kwh_today, 1),
        "pace_kwh": pace,
        "curve": points,
        "daily": daily,
        "summary": {k: fnum(summary.get(k)) for k in ("month", "year", "lifetime")},
        "panels": panel_list,
        "calls_this_month": (state.get("calls") or {}).get("count", 0),
    }


def _minutes(hhmm):
    parts = hhmm.split(" ")[-1].split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _step_hours(times):
    """Hours between readings; gaps over 30 minutes count as no data."""
    steps = [(_minutes(b) - _minutes(a)) / 60 for a, b in zip(times, times[1:])]
    return [h if 0 < h <= 0.5 else 0 for h in steps]


def _panel_sort(key):
    uid, _, ch = key.rpartition("-")
    return (uid, int(ch) if ch.isdigit() else 0)


# ---------------------------------------------------------------- Ambient

def fetch_weather(state, now_utc):
    if not (env("AMBIENT_API_KEY") and env("AMBIENT_APP_KEY")):
        return "Not connected yet."
    client = ambient.Client(env("AMBIENT_API_KEY"), env("AMBIENT_APP_KEY"))
    devices = client.devices()
    if not devices:
        return "No weather station found on this Ambient account."
    device = devices[0]
    history = client.history(device["macAddress"])
    tz = zone(device.get("lastData", {}).get("tz"))
    weather = state.setdefault("weather", {})
    weather["latest"] = device.get("lastData", {})
    weather["name"] = (device.get("info") or {}).get("name") or "Ambient station"

    by_day = {}
    for rec in history:
        when = dt.datetime.fromtimestamp(rec["dateutc"] / 1000, dt.timezone.utc).astimezone(tz)
        by_day.setdefault(when.strftime("%Y-%m-%d"), []).append((when, rec))
    days = weather.setdefault("days", {})
    for day, recs in by_day.items():
        recs.sort(key=lambda x: x[0])
        sun = sum(fnum(r.get("solarradiation")) * 5 / 60 / 1000 for _, r in recs)  # kWh/m²
        temps = [fnum(r.get("tempf")) for _, r in recs if r.get("tempf") is not None]
        rain = [fnum(r.get("dailyrainin")) for _, r in recs if r.get("dailyrainin") is not None]
        entry = days.get(day, {})
        if len(recs) >= entry.get("n", 0):  # keep the most complete copy of a day
            days[day] = {"n": len(recs), "sun_kwh_m2": round(sun, 3),
                         "hi": round(max(temps)) if temps else None,
                         "lo": round(min(temps)) if temps else None}
        if rain:  # the gauge's running total for the day, so the biggest reading is the day's total
            days[day]["rain_in"] = round(max(rain + [entry.get("rain_in") or 0]), 2)
    today = now_utc.astimezone(tz).strftime("%Y-%m-%d")
    weather["today_curve"] = [{"t": w.strftime("%H:%M"), "wm2": fnum(r.get("solarradiation"))}
                              for w, r in sorted(by_day.get(today, []), key=lambda x: x[0])]
    weather["today"] = today
    for old in sorted(days)[:-60]:
        del days[old]
    return None


def weather_view(state):
    weather = state.get("weather")
    if not weather or not weather.get("latest"):
        return None
    last = weather["latest"]
    today = weather["days"].get(weather.get("today"), {})
    temp_f = fnum(last.get("tempf"))
    sun = fnum(last.get("solarradiation"))
    # Panels run roughly 25°C above air in full sun and lose ~0.4% per °C above 25°C.
    cell_c = (temp_f - 32) * 5 / 9 + 25 * min(sun / 1000, 1.2)
    heat_loss = round(max(0.0, cell_c - 25) * 0.4)
    wind_dir = last.get("winddir")
    return {
        "station": weather.get("name"),
        "updated_ms": last.get("dateutc"),
        "temp_f": round(temp_f),
        "hi_f": today.get("hi"),
        "lo_f": today.get("lo"),
        "sun_wm2": round(sun),
        "uv": last.get("uv"),
        "humidity": last.get("humidity"),
        "wind_mph": round(fnum(last.get("windspeedmph"))),
        "wind_dir": COMPASS[round(fnum(wind_dir) / 45) % 8] if wind_dir is not None else "",
        "heat_loss_pct": heat_loss if sun > 200 else None,
        "curve": weather.get("today_curve", []),
        "days": weather.get("days", {}),
        "rain": rain_view(weather),
    }


def rain_view(weather):
    """Rainfall from the station's own gauge. Ambient's totals reset at local midnight, Sunday, the 1st and Jan 1."""
    last = weather.get("latest") or {}
    if last.get("dailyrainin") is None:
        return None
    tz = zone(last.get("tz"))
    reading_day = dt.datetime.fromtimestamp(last["dateutc"] / 1000, dt.timezone.utc).astimezone(tz).strftime("%Y-%m-%d")
    fresh = reading_day == weather.get("today")
    recent = [{"date": d, "in": v.get("rain_in")} for d, v in sorted(weather.get("days", {}).items())[-7:]
              if v.get("rain_in") is not None]
    return {
        "rate_in_hr": fnum(last.get("hourlyrainin")) if fresh else 0,
        "today_in": fnum(last.get("dailyrainin")) if fresh else 0,
        "event_in": fnum(last.get("eventrainin")),
        "week_in": fnum(last.get("weeklyrainin")),
        "month_in": fnum(last.get("monthlyrainin")),
        "year_in": fnum(last.get("yearlyrainin")),
        "last_rain": last.get("lastRain"),
        "recent": recent,
    }


# ---------------------------------------------------------------- PGE

def bills_view(bills, today, solar_daily):
    """Monthly PGE bills: history, this cycle's progress and what the solar is worth."""
    bills = sorted(bills, key=lambda b: b["start"])
    last = bills[-1]
    start = dt.date.fromisoformat(last["end"])
    lengths = [(dt.date.fromisoformat(b["end"]) - dt.date.fromisoformat(b["start"])).days for b in bills[-6:]]
    cycle_days = round(statistics.mean(lengths)) if lengths else 30
    end = start + dt.timedelta(days=cycle_days)
    # Fixed monthly charge: what a bill costs when no energy was billed.
    zero = [b["cost"] for b in bills if b["import"] == 0 and b["cost"] is not None]
    base = statistics.median(zero) if zero else min(b["cost"] or 0 for b in bills)
    rates = [(b["cost"] - base) / b["import"] for b in bills if b["cost"] and b["import"] >= 100]
    rate = round(statistics.median(rates), 3) if rates else None
    solar_kwh = sum(v for d, v in solar_daily.items() if start.isoformat() <= d <= today and v)
    year_ago = start - dt.timedelta(days=365)
    same = min(bills, key=lambda b: abs((dt.date.fromisoformat(b["start"]) - year_ago).days))
    if abs((dt.date.fromisoformat(same["start"]) - year_ago).days) > 20:
        same = None
    last12 = [b for b in bills if b["end"] > (start - dt.timedelta(days=365)).isoformat()]
    winter = [b for b in last12 if int(b["start"][5:7]) in (10, 11, 12, 1, 2, 3)]
    total12 = sum(b["cost"] or 0 for b in last12)
    return {
        "kind": "bills",
        "cycle_start": start.isoformat(),
        "cycle_end": end.isoformat(),
        "cycle_day": (dt.date.fromisoformat(today) - start).days + 1,
        "cycle_days": cycle_days,
        "last": {"start": last["start"], "end": last["end"], "kwh": round(last["import"]), "cost": last["cost"]},
        "same_last_year": {"start": same["start"], "end": same["end"], "kwh": round(same["import"]),
                           "cost": same["cost"]} if same else None,
        "last12_cost": round(total12, 2),
        "winter_share": round(sum(b["cost"] or 0 for b in winter) / total12, 2) if total12 else None,
        "base_charge": base,
        "rate": rate,
        "solar_kwh_cycle": round(solar_kwh),
        "solar_value_cycle": round(solar_kwh * rate, 2) if rate else None,
        "history": [{"start": b["start"], "end": b["end"], "kwh": round(b["import"]), "cost": b["cost"]}
                    for b in bills[-13:]],
    }


def bill_view(rows, today):
    if not rows:
        return None
    last_date = max(r["date"] for r in rows)
    start_day = int(env("PGE_CYCLE_START_DAY") or 1)
    end = dt.date.fromisoformat(last_date)
    start = end.replace(day=min(start_day, 28))
    if start > end:
        start = (start.replace(day=1) - dt.timedelta(days=1)).replace(day=min(start_day, 28))
    nxt = (start.replace(day=28) + dt.timedelta(days=5)).replace(day=start.day)
    cycle = [r for r in rows if start.isoformat() <= r["date"] <= last_date]
    costs = [r["cost"] for r in cycle if r["cost"] is not None]
    # PGE Time of Day on-peak: 5-9 pm on weekdays.
    peak = [r for r in cycle if r["hour"] is not None and 17 <= r["hour"] < 21
            and dt.date.fromisoformat(r["date"]).weekday() < 5]
    imported = sum(r["import"] for r in cycle)
    return {
        "cycle_start": start.isoformat(),
        "cycle_end": (nxt - dt.timedelta(days=1)).isoformat(),
        "cycle_day": (dt.date.fromisoformat(today) - start).days + 1,
        "cycle_days": (nxt - start).days,
        "data_through": last_date,
        "imported_kwh": round(imported),
        "exported_kwh": round(sum(r["export"] for r in cycle)),
        "peak_kwh": round(sum(r["import"] for r in peak)) if peak else None,
        "peak_share": round(sum(r["import"] for r in peak) / imported, 2) if peak and imported else None,
        "cost": round(sum(costs), 2) if costs else None,
        "cycle_explicit": bool(env("PGE_CYCLE_START_DAY")),
    }


# ---------------------------------------------------------------- Outside



def fetch_outside(state, now_utc):
    # Location comes from config.json (rounded, safe to publish) or a HOME_ADDRESS secret.
    loc = load_json("config.json", {}).get("location") or {}
    address = env("HOME_ADDRESS")
    if not (address or loc.get("lat")):
        return "Add your home location."
    out = state.setdefault("outside", {})
    # Saved data is public on a public repo: keep only a fingerprint of the address.
    key = address.lower() if address else f"{loc['lat']},{loc['lon']}"
    fingerprint = hashlib.sha256(key.encode()).hexdigest()[:16]
    if out.get("address_id") != fingerprint:
        out.clear()
        out["address_id"] = fingerprint
        lat, lon = outside.geocode(address) if address else (loc["lat"], loc["lon"])
        out["lat"], out["lon"] = round(lat, 2), round(lon, 2)  # never save the exact spot
    lat, lon, tz_name = out["lat"], out["lon"], "America/Los_Angeles"
    now = now_utc.astimezone(zone(tz_name))
    errors = []

    def attempt(key, fn, every_hours=0):
        stamp = out.get(key + "_at")
        if stamp and every_hours and (now_utc - dt.datetime.fromisoformat(stamp)).total_seconds() < every_hours * 3600:
            return
        try:
            out[key] = fn()
            out[key + "_at"] = now_utc.isoformat()
        except Exception as e:  # one source failing shouldn't blank the rest
            errors.append(f"{key}: {e}")

    attempt("forecast", lambda: outside.forecast(lat, lon, tz_name))
    attempt("air", lambda: outside.air(lat, lon, tz_name))
    if "tide_station" not in out:
        attempt("tide_station", lambda: outside.tide_station(lat, lon))
    if out.get("tide_station"):
        attempt("tides", lambda: outside.tides(out["tide_station"]["id"], now.date()), 6)
    tz_hours = round(now.utcoffset().total_seconds() / 3600)
    attempt("moon_today", lambda: sky.usno_day(now.date(), lat, lon, tz_hours), 6)
    attempt("phases", lambda: sky.usno_phases(now.date()), 12)
    attempt("aurora", sky.aurora, 3)
    attempt("iss_tle", sky.iss_tle, 12)
    attempt("launches", sky.launches, 3)
    attempt("nws_alerts", lambda: alerts.nws(lat, lon))
    attempt("birds", lambda: outside.birds(lat, lon), 6)
    attempt("blooms", lambda: outside.blooms(lat, lon), 12)
    return "; ".join(errors) or None


def outside_view(state, now_utc):
    out = state.get("outside") or {}
    f = out.get("forecast")
    if not f:
        return None
    tz = zone("America/Los_Angeles")
    now = now_utc.astimezone(tz)
    today = now.strftime("%Y-%m-%d")
    daily = f.get("daily") or {}
    dates = daily.get("time") or []

    def col(name, i):
        values = daily.get(name) or []
        return values[i] if i < len(values) else None

    days = []
    sun_by_day = {}
    for i, d in enumerate(dates):
        sw = col("shortwave_radiation_sum", i)
        if sw is not None:
            sun_by_day[d] = round(sw / 3.6, 3)  # MJ/m² -> kWh/m²
        if d >= today:
            days.append({
                "date": d,
                "code": col("weather_code", i),
                "hi": round(col("temperature_2m_max", i) or 0),
                "lo": round(col("temperature_2m_min", i) or 0),
                "rain_pct": col("precipitation_probability_max", i),
                "rain_in": col("precipitation_sum", i),
                "uv": col("uv_index_max", i),
                "wind": round(col("wind_speed_10m_max", i) or 0),
                "gust": round(col("wind_gusts_10m_max", i) or 0),
                "snow_in": col("snowfall_sum", i),
                "sunrise": (col("sunrise", i) or "T")[11:16],
                "sunset": (col("sunset", i) or "T")[11:16],
                "daylight_min": round((col("daylight_duration", i) or 0) / 60),
                "sun": sun_by_day.get(d),
            })

    hourly = f.get("hourly") or {}
    sun_so_far = 0.0
    next_hours, sun_curve = [], []
    for i, t in enumerate(hourly.get("time") or []):
        if t[:10] == today:
            # Open-Meteo radiation is the average over the hour that ends at t.
            sun_curve.append({"t": t[11:16], "wm2": hourly["shortwave_radiation"][i] or 0})
            if t <= now.strftime("%Y-%m-%dT%H:%M"):
                sun_so_far += (hourly["shortwave_radiation"][i] or 0) / 1000
        if now.strftime("%Y-%m-%dT%H") <= t[:13] and len(next_hours) < 24:
            next_hours.append({"t": t[11:16], "temp": round(hourly["temperature_2m"][i] or 0),
                               "rain_pct": hourly["precipitation_probability"][i],
                               "cloud": hourly["cloud_cover"][i]})

    sunsets = sunset_scores(hourly, days[:2])

    aq = (out.get("air") or {}).get("current") or {}
    aqi = aq.get("us_aqi")
    levels = [(50, "Good"), (100, "Moderate"), (150, "Unhealthy for sensitive groups"),
              (200, "Unhealthy"), (300, "Very unhealthy"), (10 ** 6, "Hazardous")]
    cur = f.get("current") or {}
    cfg = load_json("config.json", {})
    return {
        "label": (cfg.get("location") or {}).get("label") or "Home",
        "lat": round(out["lat"], 1), "lon": round(out["lon"], 1),  # island level, a few miles
        "river_view": cfg.get("river_view"),
        "now": {"temp": round(cur.get("temperature_2m") or 0), "feels": round(cur.get("apparent_temperature") or 0),
                "code": cur.get("weather_code"), "cloud": cur.get("cloud_cover"),
                "humidity": cur.get("relative_humidity_2m"), "wind": round(cur.get("wind_speed_10m") or 0),
                "wind_dir": COMPASS[round((cur.get("wind_direction_10m") or 0) / 45) % 8]},
        "days": days,
        "next_hours": next_hours,
        "sun_by_day": sun_by_day,
        "sun_so_far": round(sun_so_far, 3),
        "sun_curve": sun_curve,
        "sunsets": sunsets,
        "air": {"aqi": aqi, "label": next(l for lim, l in levels if (aqi or 0) <= lim) if aqi is not None else None,
                "pm25": aq.get("pm2_5"), "ozone": aq.get("ozone")},
        "tide_station": out.get("tide_station"),
        "tides": out.get("tides") or [],
        "birds": out.get("birds") or [],
        "blooms": out.get("blooms") or [],
        "produce": outside.PRODUCE[now.month],
        "moon": {**sky.moon_state(now_utc),
                 **({k: v for k, v in (out.get("moon_today") or {}).items() if k in ("moonrise", "moonset")}
                    if out.get("moon_today_at", "")[:10] == now_utc.strftime("%Y-%m-%d") else {})},
        "phases": [p for p in (out.get("phases") or sky.mean_phases(now_utc)) if p["utc"] > now_utc.isoformat()][:4]
                  or sky.mean_phases(now_utc),
        "aurora": out.get("aurora"),
        "sky_events": sorted(sky.upcoming_events(now_utc, out["lat"], out["lon"])
                             + sky.launch_events(out.get("launches"), out["lat"], out["lon"], now_utc),
                             key=lambda e: e["utc"])[:10],
        "iss": _iss(out, now_utc),
        "stargazing": sky.stargazing(next_hours, sky.moon_state(now_utc)["lit_pct"], now),
    }


def _iss(out, now_utc):
    try:
        return sky.iss_passes(out["iss_tle"], out["lat"], out["lon"], now_utc) if out.get("iss_tle") else None
    except Exception:
        return None


# ---------------------------------------------------------------- Sports, markets, ships

def _refresh(store, key, fn, every_hours, now_utc, errors):
    stamp = store.get(key + "_at")
    if stamp and (now_utc - dt.datetime.fromisoformat(stamp)).total_seconds() < every_hours * 3600:
        return
    try:
        store[key] = fn()
        store[key + "_at"] = now_utc.isoformat()
    except Exception as e:  # keep the last good copy
        errors.append(f"{key}: {e}")


def fetch_sports(state, now_utc):
    store, errors = state.setdefault("sports", {}), []
    if store.get("v") != 6:  # new fields (game ids and recaps): fetch again now
        store.clear()
        store["v"] = 6
    watch = store.setdefault("watch", {})

    def every(key):
        """Check every run from tip-off until a few hours after, so results and recaps show up right away."""
        for utc in (watch.get(key), ((store.get(key) or {}).get("next") or {}).get("utc")):
            try:
                start = dt.datetime.fromisoformat((utc or "").replace("Z", "+00:00"))
            except ValueError:
                continue
            if start - dt.timedelta(minutes=10) <= now_utc <= start + dt.timedelta(hours=5):
                watch[key] = utc
                return 0
        return 2.5

    _refresh(store, "blazers", lambda: sports.team("basketball/nba", "Trail Blazers", 3), every("blazers"), now_utc, errors)
    _refresh(store, "timbers", lambda: sports.team("soccer/usa.1", "Timbers"), every("timbers"), now_utc, errors)
    _refresh(store, "f1", sports.f1, 5.5, now_utc, errors)
    reddit = store.setdefault("reddit", {})
    for key, sub in (("blazers", "ripcity"), ("timbers", "timbers"), ("f1", "formula1")):
        if reddit.get(key + "_at") is None or (now_utc - dt.datetime.fromisoformat(reddit[key + "_at"])).total_seconds() >= 7200:
            time.sleep(4)
        _refresh(reddit, key, lambda sub=sub: sports.reddit(sub), 2, now_utc, errors)
    return "; ".join(errors) or None


def fetch_markets(state, now_utc):
    store, errors = state.setdefault("markets", {}), []
    _refresh(store, "quotes", markets.snapshot, 0.5, now_utc, errors)
    return "; ".join(errors) or None


def fetch_world(state, now_utc):
    store, errors = state.setdefault("world", {}), []
    today = now_utc.astimezone(zone("America/Los_Angeles")).date()
    _refresh(store, "holidays", lambda: world.holidays(today), 12, now_utc, errors)
    _refresh(store, "bangkok", world.bangkok, 0.3, now_utc, errors)
    return "; ".join(errors) or None


def fetch_almanac(state, now_utc):
    """Today in history, places near home, Gorge trip reports and Parker's calendar."""
    store, errors = state.setdefault("almanac", {}), []
    today = now_utc.astimezone(zone("America/Los_Angeles")).date()
    if (store.get("history") or {}).get("date") != today.isoformat() or (store.get("history") or {}).get("v") != 2:
        store.pop("history_at", None)
        store.pop("nearby_at", None)
    _refresh(store, "history", lambda: almanac.on_this_day(today), 24, now_utc, errors)
    out = state.get("outside") or {}
    if out.get("lat"):
        _refresh(store, "nearby", lambda: almanac.nearby(out["lat"], out["lon"], today), 24, now_utc, errors)
    _refresh(store, "trails", lambda: almanac.trip_reports(today), 6, now_utc, errors)
    _refresh(store, "apod", lambda: sky.apod(env("NASA_KEY") or "DEMO_KEY"), 3, now_utc, errors)
    if (store.get("albums") or {}).get("date") != today.isoformat():
        store.pop("albums_at", None)
    _refresh(store, "albums", lambda: daily.album_birthdays(today), 24, now_utc, errors)
    _refresh(store, "good_news", daily.good_news, 3, now_utc, errors)
    if env("CALENDAR_ICS"):
        _refresh(store, "calendar", lambda: mycal.upcoming(env("CALENDAR_ICS"), now_utc), 0.3, now_utc, errors)
    return "; ".join(errors) or None


def fetch_culture(state, now_utc):
    """What's trending, book picks from Goodreads and long reads."""
    store, errors = state.setdefault("culture", {}), []
    today = now_utc.astimezone(zone("America/Los_Angeles")).date()
    _refresh(store, "trends", culture.google_trends, 1.5, now_utc, errors)
    if (store.get("wiki") or {}).get("date") != today.isoformat():
        store.pop("wiki_at", None)
    _refresh(store, "wiki", lambda: {"date": today.isoformat(), "articles": culture.wiki_most_read(today)}, 24, now_utc, errors)
    _refresh(store, "reddit", culture.reddit_popular, 3, now_utc, errors)
    _refresh(store, "longreads", culture.fresh_longreads, 12, now_utc, errors)
    user = culture.goodreads_user(env("GOODREADS_USER") or str(load_json("config.json", {}).get("goodreads") or ""))
    if user and not user.isdigit():
        if store.get("goodreads_name") != user:
            try:
                store["goodreads_id"], store["goodreads_name"] = culture.resolve_goodreads(user), user
            except Exception as e:
                errors.append(f"goodreads: {e}")
        user = store.get("goodreads_id") if store.get("goodreads_name") == user else None
    if user:
        if store.get("books_user") != user or store.get("books_v") != 2:  # v2 skips reprints and classic authors
            store.pop("books_at", None)
            store["books_user"], store["books_v"] = user, 2
        _refresh(store, "books", lambda: culture.book_picks(user, today), 12, now_utc, errors)
    return "; ".join(errors) or None


def fetch_science(state, now_utc):
    """Fresh science findings and what they mean."""
    store, errors = state.setdefault("science", {}), []
    _refresh(store, "items", science.breakthroughs, 3, now_utc, errors)
    return "; ".join(errors) or None


def fetch_civics(state, now_utc):
    """Districts, representatives and what they've been doing, and upcoming elections."""
    store, errors = state.setdefault("civics", {}), []
    today = now_utc.astimezone(zone("America/Los_Angeles")).date()
    out = state.get("outside") or {}
    address = env("HOME_ADDRESS")
    if not (address or out.get("lat")):
        return "Needs the home location first."
    fingerprint = (state.get("outside") or {}).get("address_id")
    if store.get("address_id") != fingerprint or store.get("v") != 3:  # v3 drops Congress from the state legislators
        store.clear()
        store.update(address_id=fingerprint, v=3)
    _refresh(store, "districts", lambda: civics.districts(address or None, out.get("lat"), out.get("lon")), 24 * 7, now_utc, errors)
    d = store.get("districts")
    if not d:
        return "; ".join(errors)
    _refresh(store, "congress", lambda: civics.congress_members(d["state"], d["congress"]), 24, now_utc, errors)
    if env("OPENSTATES_KEY") and out.get("lat"):
        _refresh(store, "legislature", lambda: civics.state_legislators(out["lat"], out["lon"], env("OPENSTATES_KEY")), 24, now_utc, errors)
    in_congress = {p["name"] for p in store.get("congress") or []}
    people = (store.get("congress") or []) + [p for p in store.get("legislature") or [] if p["name"] not in in_congress]
    cache = store.setdefault("vote_cache", {})

    def votes():
        found, failed = dict(store.get("votes") or {}), []
        for p in people:
            if p["chamber"] == "house":
                try:
                    found[p["bioguide"]] = civics.house_votes(today, p["bioguide"], cache)
                except Exception as e:
                    failed.append(f"House: {e}")
        lis = [p["lis"] for p in people if p["chamber"] == "senate" and p.get("lis")]
        if lis:
            try:
                found.update(civics.senate_votes(today, lis, cache))
            except Exception as e:  # senate.gov often refuses cloud runners: try GovTrack
                for p in people:
                    if p["chamber"] == "senate" and p.get("lis") and p.get("govtrack"):
                        try:
                            found[p["lis"]] = civics.govtrack_votes(p["govtrack"])
                        except Exception as e2:
                            failed.append(f"Senate: {e}; GovTrack: {e2}")
                            break
        if failed:
            errors.extend(failed)
        return found
    _refresh(store, "votes", votes, 3, now_utc, errors)

    def bills():
        found = {}
        for p in people:
            if p.get("bioguide") and env("CONGRESS_KEY"):
                found[p["bioguide"]] = civics.sponsored(p["bioguide"], env("CONGRESS_KEY"))
            elif p.get("openstates_id"):
                found[p["openstates_id"]] = civics.state_bills(p["openstates_id"], env("OPENSTATES_KEY"))
        return found
    if env("CONGRESS_KEY") or env("OPENSTATES_KEY"):
        _refresh(store, "bills", bills, 24, now_utc, errors)
    _refresh(store, "news", lambda: {p["name"]: civics.news(p["name"]) for p in people}, 6, now_utc, errors)
    if env("GOOGLE_CIVIC_KEY") and address:
        _refresh(store, "ballot", lambda: civics.civic_elections(address, env("GOOGLE_CIVIC_KEY"), today), 24, now_utc, errors)
    return "; ".join(errors) or None


def yard_view(state, now_utc):
    """How this yard differs from the forecast model, learned from the station's full days, and what that means next."""
    weather, f = state.get("weather") or {}, (state.get("outside") or {}).get("forecast") or {}
    daily = f.get("daily") or {}
    model = {d: i for i, d in enumerate(daily.get("time") or [])}
    today = now_utc.astimezone(zone("America/Los_Angeles")).strftime("%Y-%m-%d")
    pairs = [(d, v, model[d]) for d, v in sorted((weather.get("days") or {}).items())
             if d < today and d in model and v.get("n", 0) >= 240 and v.get("hi") is not None]
    if len(pairs) < 2:
        return None
    col = lambda k, i: (daily.get(k) or [None] * (i + 1))[i]
    hi_bias = statistics.median(v["hi"] - col("temperature_2m_max", i) for _, v, i in pairs)
    lo_bias = statistics.median(v["lo"] - col("temperature_2m_min", i) for _, v, i in pairs)
    wet = [(v["rain_in"], col("precipitation_sum", i)) for _, v, i in pairs
           if v.get("rain_in") is not None and (col("precipitation_sum", i) or 0) >= 0.1]
    rain_ratio = sum(a for a, _ in wet) / sum(b for _, b in wet) if wet else None
    ahead = []
    for d in sorted(model):
        if d < today or len(ahead) >= 3:
            continue
        i = model[d]
        hi, lo = col("temperature_2m_max", i), col("temperature_2m_min", i)
        if hi is None or lo is None:
            continue
        ahead.append({"date": d, "model_hi": round(hi), "model_lo": round(lo),
                      "hi": round(hi + hi_bias), "lo": round(lo + lo_bias),
                      "rain_in": round((col("precipitation_sum", i) or 0) * (rain_ratio or 1), 2)})
    frost = next((a for a in ahead if a["lo"] <= 33), None)
    return {"days": len(pairs), "hi_bias": round(hi_bias, 1), "lo_bias": round(lo_bias, 1),
            "rain_ratio": round(rain_ratio, 2) if rain_ratio is not None else None, "rain_days": len(wet),
            "ahead": ahead, "frost": frost}


def shades_view(state, now_utc, yard):
    """When to open or close window shades to save on heating or cooling, from the hourly forecast and indoor temp."""
    f = (state.get("outside") or {}).get("forecast") or {}
    hourly, daily = f.get("hourly") or {}, f.get("daily") or {}
    if not hourly.get("time") or not daily.get("time"):
        return None
    tz = zone("America/Los_Angeles")
    now = now_utc.astimezone(tz)
    indoor = fnum(((state.get("weather") or {}).get("latest") or {}).get("tempinf")) or None
    bias = (yard or {}).get("hi_bias") or 0
    plans = []
    for offset in (0, 1):
        day = (now + dt.timedelta(days=offset)).strftime("%Y-%m-%d")
        if day not in daily["time"]:
            continue
        i = daily["time"].index(day)
        hi = (daily["temperature_2m_max"][i] or 0) + bias
        sunrise, sunset = (daily["sunrise"][i] or "T")[11:16], (daily["sunset"][i] or "T")[11:16]
        hours = [(t[11:13], w or 0, temp) for t, w, temp in zip(hourly["time"], hourly["shortwave_radiation"], hourly["temperature_2m"])
                 if t[:10] == day]
        sunny = [h for h, w, _ in hours if w >= 300]
        mode = "cool" if hi >= 75 or (indoor and indoor >= 77 and hi >= 68) else "heat" if hi < 65 else "mild"
        steps = []
        if mode == "cool" and sunny:
            east = [h for h in sunny if int(h) <= 11]
            south = [h for h in sunny if 11 <= int(h) <= 15]
            west = [h for h in sunny if int(h) >= 15]
            if east:
                steps.append({"time": sunrise, "do": "close", "where": "east-facing", "why": f"Morning sun until about {int(east[-1])}:00"})
            if south:
                steps.append({"time": f"{int(south[0]) - 1:02d}:00", "do": "close", "where": "south-facing", "why": "Strongest sun of the day"})
            if west:
                steps.append({"time": f"{int(west[0]) - 1:02d}:00", "do": "close", "where": "west-facing", "why": f"Low afternoon sun heats rooms most, high near {round(hi)}°"})
            cool_eve = next((t for t, _, temp in hours if int(t) >= 17 and temp is not None and indoor and temp + bias < indoor - 3), None)
            if cool_eve:
                steps.append({"time": f"{cool_eve}:00", "do": "open", "where": "windows", "why": "Outside gets cooler than inside: let the breeze cool the house"})
        elif mode == "heat":
            if sunny:
                steps.append({"time": f"{int(sunny[0]) - 1:02d}:00", "do": "open", "where": "south and west-facing",
                              "why": f"Free solar heat from about {int(sunny[0]) - 1}:00 to {int(sunny[-1])}:00"})
            else:
                steps.append({"time": sunrise, "do": "keep closed", "where": "all", "why": "Too cloudy for useful solar heat; closed shades insulate the glass"})
            steps.append({"time": sunset, "do": "close", "where": "all", "why": "Trap the day's heat once the sun is down"})
        else:
            if len(sunny) >= 3:
                steps.append({"time": f"{int(sunny[0]) - 1:02d}:00", "do": "open", "where": "sunny-side", "why": "Mild day: sun is welcome, no heating or cooling needed"})
            steps.append({"time": sunset, "do": "close", "where": "all", "why": "Hold the warmth overnight"})
        if offset == 0:
            if now.strftime("%H:%M") >= sunset:
                continue  # today's sun is done; tomorrow's plan is what matters
            steps = [s for s in steps if s["time"] >= now.strftime("%H:%M") or s["do"] == "keep closed"]
        if steps:
            plans.append({"date": day, "mode": mode, "high": round(hi), "steps": steps})
    return {"indoor_f": round(indoor) if indoor else None, "plans": plans} if plans else None


def sunset_scores(hourly, days):
    """How colorful each sunset should be. Mid and high clouds catch the light; low cloud and rain block it."""
    times = hourly.get("time") or []
    out = []
    for d in days:
        if not d.get("sunset") or d["sunset"] == "":
            continue
        hour = f"{d['date']}T{d['sunset'][:2]}:00"
        if hour not in times:
            continue
        i = times.index(hour)
        val = lambda k: (hourly.get(k) or [None] * len(times))[i] or 0
        low, mid, high, rain = val("cloud_cover_low"), val("cloud_cover_mid"), val("cloud_cover_high"), val("precipitation_probability")
        canvas = max(mid, high)  # the clouds that light up
        score = 100 - abs(canvas - 50) * 1.2 if canvas >= 10 else 35 + canvas  # some color even when clear
        score -= low * 0.7 + max(0, rain - 20) * 0.6
        score = max(0, min(100, round(score)))
        label = ("Spectacular" if score >= 80 else "Pretty" if score >= 60 else "Decent" if score >= 40
                 else "Meh" if score >= 20 else "Gray")
        out.append({"date": d["date"], "sunset": d["sunset"], "score": score, "label": label,
                    "low": low, "mid": mid, "high": high, "rain_pct": rain})
    return out


def loads_view(state, ratio, now_utc):
    """Best three-hour stretch today and tomorrow to run big loads on sunshine, from the hourly forecast."""
    hourly = ((state.get("outside") or {}).get("forecast") or {}).get("hourly") or {}
    times, wm2 = hourly.get("time") or [], hourly.get("shortwave_radiation") or []
    if not (ratio and times):
        return None
    now = now_utc.astimezone(zone("America/Los_Angeles"))
    days = []
    for offset in (0, 1):
        day = (now + dt.timedelta(days=offset)).strftime("%Y-%m-%d")
        # Radiation is the average over the hour ending at t, so each entry covers t-1h to t.
        hours = [(t, (w or 0) / 1000 * ratio) for t, w in zip(times, wm2)
                 if t[:10] == day and (offset or t[11:13] > now.strftime("%H"))]
        if len(hours) < 3:
            continue
        kw, i = max((sum(k for _, k in hours[j:j + 3]) / 3, j) for j in range(len(hours) - 2))
        if offset == 0 and kw < 1:
            continue  # nothing worth planning around for the rest of today
        start = dt.datetime.fromisoformat(hours[i][0]) - dt.timedelta(hours=1)
        days.append({"date": day, "from": start.strftime("%H:%M"), "to": hours[i + 2][0][11:16],
                     "kw": round(kw, 1), "day_kwh": round(sum(k for _, k in hours))})
    return days or None


def civics_view(state, today):
    c = state.get("civics") or {}
    d = c.get("districts")
    if not d:
        return None
    votes, bills, news = c.get("votes") or {}, c.get("bills") or {}, c.get("news") or {}
    people = []
    in_congress = {p["name"] for p in c.get("congress") or []}
    for p in (c.get("congress") or []) + [p for p in c.get("legislature") or [] if p["name"] not in in_congress]:
        vid = p.get("bioguide") if p["chamber"] == "house" else p.get("lis")
        people.append({k: v for k, v in p.items() if k not in ("lis", "govtrack")} | {
            "votes": votes.get(vid) or [], "bills": bills.get(p.get("bioguide") or p.get("openstates_id")) or [],
            "news": news.get(p["name"]) or []})
    ballot = {b["date"]: b for b in c.get("ballot") or [] if b["date"] >= today}
    elections = []
    for e in civics.oregon_elections(dt.date.fromisoformat(today)):
        b = ballot.pop(e["date"], None)
        elections.append(e | ({"name": b["name"] or e["name"], "contests": b["contests"], "info_url": b["info_url"]} if b else {}))
    elections += [b for b in ballot.values()]
    elections.sort(key=lambda e: e["date"])
    return {"districts": d, "people": people, "elections": elections[:4],
            "statewide": [{"role": r, "name": n, "party": p, "url": u} for r, n, p, u in civics.OREGON_STATEWIDE],
            "links": [{"name": n, "url": u} for n, u in civics.VOTE_LINKS],
            "keys": {"congress": bool(env("CONGRESS_KEY")), "openstates": bool(env("OPENSTATES_KEY")),
                     "ballot": bool(env("GOOGLE_CIVIC_KEY"))}}


def fetch_gear(state, now_utc):
    """Underpriced music gear on Portland Craigslist, checked twice a day."""
    store, errors = state.setdefault("gear", {}), []
    if store.get("v") != 3:  # better matching: score the listings again now
        store.pop("scan_at", None)
        store["v"] = 3

    def scan():
        found = gear.listings()
        first = store.setdefault("first_seen", {})
        today = now_utc.astimezone(zone("America/Los_Angeles")).date().isoformat()
        picks = gear.deals(found, store.setdefault("reverb", {}))
        for d in picks:
            d["first_seen"] = first.setdefault(d["url"], today)
        for url in list(first)[:-500]:
            first.pop(url)
        return {"deals": picks, "checked": len(found)}
    _refresh(store, "scan", scan, 12, now_utc, errors)
    return "; ".join(errors) or None


def fetch_news(state, now_utc):
    store, errors = state.setdefault("news", {}), []
    _refresh(store, "stories", news.top_stories, 1.5, now_utc, errors)
    if (store.get("reviews") or {}).get("v") != 2:  # pick up filter changes now
        store.pop("reviews_at", None)
    _refresh(store, "reviews", news.reviews, 3, now_utc, errors)
    failed = sorted(set((store.get("stories") or {}).get("failed", []) + (store.get("reviews") or {}).get("failed", [])))
    if failed:
        errors.append("feeds not answering: " + ", ".join(failed))
    kept = (store.get("reviews") or {}).get("kept")
    if kept is not None:
        errors.append("reviews kept " + json.dumps(kept) + " of " + json.dumps((store.get("reviews") or {}).get("feed_items")))
    return "; ".join(errors) or None


def fetch_releases(state, now_utc):
    store, errors = state.setdefault("releases", {}), []
    _refresh(store, "streaming", releases.streaming, 12, now_utc, errors)
    _refresh(store, "albums", releases.albums, 12, now_utc, errors)
    return "; ".join(errors) or None


def fetch_ski(state, now_utc):
    store, errors = state.setdefault("ski", {}), []
    _refresh(store, "snow", ski.snow, 3, now_utc, errors)
    _refresh(store, "forecast", ski.forecast, 2, now_utc, errors)
    _refresh(store, "avalanche", ski.avalanche, 3, now_utc, errors)
    return "; ".join(errors) or None


def fetch_surf(state, now_utc):
    store, errors = state.setdefault("surf", {}), []
    _refresh(store, "forecast", surf.forecast, 2, now_utc, errors)
    _refresh(store, "buoy", lambda: surf.buoy(now_utc), 0.9, now_utc, errors)
    return "; ".join(errors) or None


def surf_view(state, now_utc):
    """Ratings are worked out here, not at fetch time, so "now" stays current between forecast pulls."""
    store = state.get("surf") or {}
    if not store.get("forecast"):
        return None
    try:
        breaks = surf.report(store["forecast"], now_utc.astimezone(zone("America/Los_Angeles")))
    except Exception:
        return None
    return {"breaks": breaks, "buoy": store.get("buoy"), "updated": store.get("forecast_at")}


def fetch_places(state, now_utc):
    spots = places.parse(env("PLACES")) or [(p["label"], p.get("query") or (p["lat"], p["lon"]))
                                                for p in load_json("config.json", {}).get("places", [])]
    if not spots:
        return "No places set up."
    store, errors = state.setdefault("places", {}), []
    # Without a traffic key the drive times never change, so look them up once a day.
    if any("error" in x for x in store.get("commute") or []):
        store.pop("commute_at", None)  # retry places that failed
    _refresh(store, "commute", lambda: places.commute(spots, env("TOMTOM_KEY")),
             0 if env("TOMTOM_KEY") else 24, now_utc, errors)
    coast = dict(spots).get("Coast house")
    if coast:
        today = now_utc.astimezone(zone("America/Los_Angeles")).date()
        _refresh(store, "coast", lambda: places.coast(coast, today), 2, now_utc, errors)
    return "; ".join(errors) or None


def fetch_fishing(state, now_utc):
    store, errors = state.setdefault("fishing", {}), []
    today = now_utc.astimezone(zone("America/Los_Angeles")).date()
    if "water_f" not in (store.get("dam") or {}):
        store.pop("dam_at", None)
    _refresh(store, "dam", lambda: fishing.dam_counts(today), 6, now_utc, errors)
    _refresh(store, "river", fishing.river, 1, now_utc, errors)
    return "; ".join(errors) or None


def fetch_live(state, now_utc):
    out = state.get("outside") or {}
    if not out.get("lat"):
        return "Needs the home location first."
    store, errors, lat, lon = state.setdefault("live", {}), [], out["lat"], out["lon"]
    _refresh(store, "quakes", lambda: live.earthquakes(lat, lon), 1, now_utc, errors)
    _refresh(store, "fires", lambda: live.wildfires(lat, lon), 3, now_utc, errors)
    _refresh(store, "planes", lambda: live.planes(lat, lon), 0, now_utc, errors)
    try:
        live.add_details(store.get("planes"), state.setdefault("flight_lookups", {}), now_utc)
    except Exception as e:
        errors.append(f"flight details: {e}")
    _refresh(store, "pdx", live.pdx_status, 0.3, now_utc, errors)
    return "; ".join(errors) or None


def fetch_extras(state, now_utc):
    """Grid mix, what's going around, and shellfish safety at the coast."""
    store, errors = state.setdefault("extras", {}), []
    today = now_utc.astimezone(zone("America/Los_Angeles")).date()
    _refresh(store, "grid", grid.status, 0.3, now_utc, errors)
    _refresh(store, "health", lambda: health.wastewater(today), 12, now_utc, errors)
    _refresh(store, "shellfish", coastsafety.status, 6, now_utc, errors)
    _refresh(store, "cameras", roads.cameras, 24, now_utc, errors)
    _refresh(store, "roads", roads.incidents, 0.3, now_utc, errors)
    out = state.get("outside") or {}
    if env("GOOGLE_POLLEN_KEY") and out.get("lat"):
        # Count every attempt (failed ones too) against the monthly free cap.
        month = today.strftime("%Y-%m")  # Google bills by Pacific-time month
        if (store.get("pollen_calls") or {}).get("month") != month:
            store["pollen_calls"] = {"month": month, "count": 0}
        calls = store["pollen_calls"]

        def pollen_call():
            if calls["count"] >= POLLEN_MONTHLY_CAP:
                raise RuntimeError(f"monthly cap of {POLLEN_MONTHLY_CAP} calls reached")
            calls["count"] += 1
            return pollen.forecast(out["lat"], out["lon"], env("GOOGLE_POLLEN_KEY"))
        _refresh(store, "pollen", pollen_call, 6, now_utc, errors)
    if env("EBIRD_KEY") and out.get("lat"):
        _refresh(store, "birds", lambda: birds.notable(out["lat"], out["lon"], env("EBIRD_KEY")), 3, now_utc, errors)
    return "; ".join(errors) or None


def garden_view(state, out, now_utc):
    today = now_utc.astimezone(zone("America/Los_Angeles")).date()
    soil = None
    hourly = ((state.get("outside") or {}).get("forecast") or {}).get("hourly") or {}
    temps = [v for t, v in zip(hourly.get("time") or [], hourly.get("soil_temperature_6cm") or [])
             if t[:10] == today.isoformat() and v is not None]
    if temps:
        soil = round(sum(temps) / len(temps))  # forecast is requested in °F
    station = (state.get("weather") or {}).get("days") or {}
    recent_rain = sum((station.get((today - dt.timedelta(days=i)).isoformat()) or {}).get("rain_in") or 0 for i in range(3))
    return {"plant": garden.plant_now(today), "tips": garden.tips((out or {}).get("days") or [], soil),
            "forest": garden.forest_tasks(today),
            "look": nature.look_for(today, (out or {}).get("days") or [], recent_rain),
            "burn": garden.burn_check(today, (out or {}).get("days") or [],
                                      alerts.active((state.get("outside") or {}).get("nws_alerts") or [], now_utc),
                                      ((out or {}).get("air") or {}).get("aqi"))}


def fishing_view(state, out, now_utc):
    if not out:
        return None
    tz = zone("America/Los_Angeles")
    now = now_utc.astimezone(tz)
    moon = (state.get("outside") or {}).get("moon_today") or {}
    fresh = (state.get("outside") or {}).get("moon_today_at", "")[:10] == now_utc.strftime("%Y-%m-%d")
    t = out["days"][0] if out["days"] else {}
    store = state.get("fishing") or {}
    return {
        "windows": fishing.best_times(now.date(), tz, moon.get("transit") if fresh else None,
                                      moon.get("moonrise") if fresh else None, moon.get("moonset") if fresh else None,
                                      out.get("tides") or [], t.get("sunrise"), t.get("sunset")),
        "dam": store.get("dam"),
        "river": store.get("river"),
        "moon": out["moon"]["name"],
        "links": [{"name": n, "url": u} for n, u in fishing.LINKS],
    }


def fetch_deals(state, now_utc):
    store, errors = state.setdefault("deals", {}), []
    zip_code = load_json("config.json", {}).get("shopping_zip")
    if not zip_code:
        return "Add a shopping ZIP code to config.json."
    if store.get("v") != 4:  # new ordering and price format
        store.clear()
        store["v"] = 4
    _refresh(store, "weekly", lambda: deals.weekly(zip_code), 12, now_utc, errors)
    w = store.get("weekly") or {}
    if w.get("missing"):
        errors.append("no weekly ad found for " + ", ".join(w["missing"]) + "; ads nearby: " + ", ".join(w.get("merchants") or []))
    return "; ".join(errors) or None


def alerts_view(state, out, now_utc):
    if not out:
        return None
    official = alerts.active((state.get("outside") or {}).get("nws_alerts") or [], now_utc)
    return {"official": official, "forecast": alerts.from_forecast(out["days"], official), "days": 3}


def fetch_ships(state, now_utc):
    if not env("AISSTREAM_KEY"):
        return "Add your aisstream.io key."
    store = state.setdefault("ships", {})
    heard = ships.listen(env("AISSTREAM_KEY"))
    ships.merge(store.setdefault("cache", {}), heard, now_utc)
    store["last_listen"] = {"at": now_utc.isoformat(), "heard": len(heard)}
    return None


def ships_view(state, now_utc):
    store = state.get("ships") or {}
    loc = (load_json("config.json", {}).get("river_view") or {})
    if not store.get("cache") or not loc:
        return None
    return {
        "approaching": ships.approaching(store["cache"], loc["lat"], loc["lon"], now_utc)[:8],
        "in_area": len(store["cache"]),
        "listened": store.get("last_listen"),
    }


# ---------------------------------------------------------------- Assemble

def build(state, status, now_utc):
    solar = solar_view(state, now_utc)
    weather = weather_view(state)
    al = state.get("almanac") or {}
    cu = state.get("culture") or {}
    all_rows = pge.read_folder(os.path.join(DATA_DIR, "pge"))
    rows = [r for r in all_rows if not r.get("bill")]
    bills = [r for r in all_rows if r.get("bill")]
    tz = zone(solar["timezone"] if solar else None)
    today = now_utc.astimezone(tz).strftime("%Y-%m-%d")

    meter = {}
    for r in rows:
        g = meter.setdefault(r["date"], {"import": 0.0, "export": 0.0})
        g["import"] += r["import"]
        g["export"] += r["export"]

    out = outside_view(state, now_utc)
    model_sun = (out or {}).get("sun_by_day") or {}
    # Never mix sources: a backyard sensor and the weather model read differently.
    # Use the station once it has a week of full days, else the model throughout.
    station_days = {d: v for d, v in ((weather or {}).get("days") or {}).items() if v.get("n", 0) >= 250}
    use_station = bool(weather) and (len(station_days) >= 7 or not out)

    days = []
    for i in range(29, -1, -1):
        d = (dt.date.fromisoformat(today) - dt.timedelta(days=i)).isoformat()
        produced = (solar or {}).get("daily", {}).get(d)
        g = meter.get(d)
        used = round(produced + g["import"] - g["export"], 1) if g and produced is not None else None
        sun = (((weather or {}).get("days") or {}).get(d, {}).get("sun_kwh_m2") if use_station
               else model_sun.get(d))
        ly = (solar or {}).get("daily", {}).get(year_ago(dt.date.fromisoformat(d)).isoformat())
        days.append({"date": d, "produced": produced, "used": used, "sun": sun, "last_year": ly})

    # Panels vs. sunlight: today's kWh per unit of sunlight, against this system's usual ratio.
    performance = None
    if solar and (weather or out):
        ratios = [x["produced"] / x["sun"] for x in days[:-1]
                  if x["produced"] and x["sun"] and x["sun"] > 1.0]
        # Compare against sunlight so far today, not the whole day's.
        sun_today = days[-1]["sun"] if use_station else (out or {}).get("sun_so_far")
        performance = {"pct": None, "baseline_days": len(ratios)}
        if len(ratios) >= 5:
            ratio = statistics.median(ratios)
            performance["kwh_per_sun"] = round(ratio, 2)
            # Expected output for the coming days works any time; today's score needs some sun first.
            for d in (out or {}).get("days", []):
                if d["sun"]:
                    d["solar_kwh"] = round(d["sun"] * ratio)
            if sun_today and sun_today > 0.3:
                performance["pct"] = round(solar["today_kwh"] / sun_today / ratio * 100)

    produced = [x["produced"] for x in days[:-1] if x["produced"]]
    typical = statistics.median(produced) if produced else 0
    low_days = [x for x in days[:-1] if x["produced"] is not None and typical and x["produced"] < 0.6 * typical]
    for x in low_days:
        suns = [y["sun"] for y in days if y["sun"]]
        typical_sun = statistics.median(suns) if suns else None
        x["cloudy"] = bool(x["sun"] and typical_sun and x["sun"] < 0.7 * typical_sun)

    if weather:
        weather = {k: v for k, v in weather.items() if k != "days"}
    solar_daily = (solar or {}).get("daily") or {}
    if solar:
        solar = {k: v for k, v in solar.items() if k != "daily"}
    return {
        "generated_at": now_utc.isoformat(),
        "today": today,
        "sample": False,
        "status": status,
        "solar": solar,
        "weather": weather,
        "bill": bill_view(rows, today) or (bills_view(bills, today, solar_daily) if bills else None),
        "days": days,
        "low_days": [{"date": x["date"], "cloudy": x.get("cloudy")} for x in low_days],
        "sun_source": "station" if use_station else ("model" if out else None),
        "performance": performance,
        "loads": loads_view(state, (performance or {}).get("kwh_per_sun"), now_utc),
        "yard": (yard := yard_view(state, now_utc)),
        "shades": shades_view(state, now_utc, yard),
        "outside": {k: v for k, v in out.items() if k != "sun_by_day"} if out else None,
        "sports": {**{k: v for k, v in (state.get("sports") or {}).items() if not k.endswith("_at") and k not in ("v", "reddit", "watch")},
                   "reddit": {k: v for k, v in ((state.get("sports") or {}).get("reddit") or {}).items()
                              if not k.endswith("_at")}} if state.get("sports") else None,
        "markets": (state.get("markets") or {}).get("quotes"),
        "ships": ships_view(state, now_utc),
        "holidays": [h for h in (state.get("world") or {}).get("holidays") or [] if h["date"] >= today],
        "bangkok": (state.get("world") or {}).get("bangkok"),
        "thai_buddhist": world.thai_buddhist(dt.date.fromisoformat(today)),
        "alerts": alerts_view(state, out, now_utc),
        "streaming": [x for x in (state.get("releases") or {}).get("streaming") or [] if x["date"] >= today],
        "albums": [x for x in (state.get("releases") or {}).get("albums") or [] if x["date"] >= today],
        "ski": {**{k: v for k, v in (state.get("ski") or {}).items() if not k.endswith("_at")},
                "resorts": ski.resorts()} if state.get("ski") else None,
        "fishing": fishing_view(state, out, now_utc),
        "garden": garden_view(state, out, now_utc),
        "commute": (state.get("places") or {}).get("commute"),
        "coast": (state.get("places") or {}).get("coast"),
        "surf": surf_view(state, now_utc),
        "live": {k: v for k, v in (state.get("live") or {}).items() if not k.endswith("_at")} or None,
        "deals": {k: v for k, v in ((state.get("deals") or {}).get("weekly") or {}).items()
                  if k in ("stores", "missing")} or None,
        "news": {k: ((state.get("news") or {}).get(k) or {}).get("items") for k in ("stories", "reviews")},
        "grid": (state.get("extras") or {}).get("grid"),
        "health": (state.get("extras") or {}).get("health"),
        "roads": {"cameras": (state.get("extras") or {}).get("cameras") or [],
                  "incidents": (state.get("extras") or {}).get("roads") or []},
        "rare_birds": (state.get("extras") or {}).get("birds") if env("EBIRD_KEY") else None,
        "pollen": (state.get("extras") or {}).get("pollen") if env("GOOGLE_POLLEN_KEY") else None,
        "almanac": {"history": al.get("history") if (al.get("history") or {}).get("date") == today else None,
                    "facts": almanac.date_facts(dt.date.fromisoformat(today)),
                    "nearby": al.get("nearby"), "trails": al.get("trails")},
        "calendar": al.get("calendar") if env("CALENDAR_ICS") else None,
        "apod": al.get("apod"),
        "picks": daily.picks(dt.date.fromisoformat(today)),
        "album_birthdays": (al.get("albums") or {}).get("albums") if (al.get("albums") or {}).get("date") == today else None,
        "good_news": al.get("good_news"),
        "trending": {"google": cu.get("trends"), "wiki": (cu.get("wiki") or {}).get("articles")
                     if (cu.get("wiki") or {}).get("date") == today else None, "reddit": cu.get("reddit")} if cu else None,
        "books": cu.get("books") if cu.get("books_user") else None,
        "long_read": culture.long_read(dt.date.fromisoformat(today)),
        "poem": poems.poem_of_the_day(dt.date.fromisoformat(today), ((out or {}).get("days") or [None])[0]),
        "science": (state.get("science") or {}).get("items"),
        "longreads": cu.get("longreads"),
        "civics": civics_view(state, today),
        "gear": {**((state.get("gear") or {}).get("scan") or {}), "at": (state.get("gear") or {}).get("scan_at")}
                if (state.get("gear") or {}).get("scan") else None,
        "shellfish": {**((state.get("extras") or {}).get("shellfish") or {}),
                      "crab_season": coastsafety.crab_season(dt.date.fromisoformat(today))},
    }


def main():
    os.makedirs(os.path.join(DATA_DIR, "pge"), exist_ok=True)
    state_path = os.path.join(DATA_DIR, "state.json")
    state = load_json(state_path, {})
    now_utc = dt.datetime.now(dt.timezone.utc)
    status = {}
    for name, fn in (("solar", fetch_solar), ("weather", fetch_weather), ("outside", fetch_outside),
                     ("sports", fetch_sports), ("markets", fetch_markets), ("world", fetch_world),
                     ("news", fetch_news), ("releases", fetch_releases), ("deals", fetch_deals), ("ski", fetch_ski), ("surf", fetch_surf), ("fishing", fetch_fishing),
                     ("live", fetch_live), ("places", fetch_places), ("extras", fetch_extras),
                     ("ships", fetch_ships), ("almanac", fetch_almanac), ("civics", fetch_civics), ("gear", fetch_gear),
                     ("culture", fetch_culture), ("science", fetch_science)):
        try:
            status[name] = fn(state, now_utc) or "ok"
        except Exception as e:  # keep going so the page still shows cached data
            traceback.print_exc()
            status[name] = f"Error: {e}"
    save_json(state_path, state)
    status["pge"] = "ok" if any(f.endswith(".csv") for f in os.listdir(os.path.join(DATA_DIR, "pge"))) \
        else "No PGE file yet."
    out = build(state, status, now_utc)
    save_json(os.path.join(DATA_DIR, "dashboard.json"), out)
    print(json.dumps(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
