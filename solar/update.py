"""Fetch solar, weather and PG&E data and write dashboard.json.

Run once an hour. APsystems allows about 1,000 calls a month, so this spends
one call per daytime run plus two a day, and refuses to go past
APS_MONTHLY_BUDGET (default 850). Everything fetched is cached in state.json.

Settings come from environment variables:
  APSYSTEMS_APP_ID, APSYSTEMS_APP_SECRET, APSYSTEMS_SID   solar (required)
  AMBIENT_API_KEY, AMBIENT_APP_KEY                        weather (optional)
  PGE_CYCLE_START_DAY                                     bill cycle start day (optional)
  DATA_DIR                                                where state.json, dashboard.json
                                                          and pge/*.csv live (default ./data)
"""
import datetime as dt
import json
import os
import statistics
import sys
import traceback
from zoneinfo import ZoneInfo

from . import ambient, aps, pge

DATA_DIR = os.environ.get("DATA_DIR", "data")
BUDGET = int(os.environ.get("APS_MONTHLY_BUDGET", "850"))
MIN_GAP_MIN = int(os.environ.get("APS_MIN_MINUTES", "50"))
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
        solar["last_power_fetch"] = now_utc.isoformat()
        if evening_final:
            solar["final_day"] = today
    return None


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

    return {
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
        entry = days.get(day, {})
        if len(recs) >= entry.get("n", 0):  # keep the most complete copy of a day
            days[day] = {"n": len(recs), "sun_kwh_m2": round(sun, 3),
                         "hi": round(max(temps)) if temps else None,
                         "lo": round(min(temps)) if temps else None}
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
    }


# ---------------------------------------------------------------- PG&E

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
    peak = [r for r in cycle if r["hour"] is not None and 16 <= r["hour"] < 21]
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


# ---------------------------------------------------------------- Assemble

def build(state, status, now_utc):
    solar = solar_view(state, now_utc)
    weather = weather_view(state)
    rows = pge.read_folder(os.path.join(DATA_DIR, "pge"))
    tz = zone(solar["timezone"] if solar else None)
    today = now_utc.astimezone(tz).strftime("%Y-%m-%d")

    grid = {}
    for r in rows:
        g = grid.setdefault(r["date"], {"import": 0.0, "export": 0.0})
        g["import"] += r["import"]
        g["export"] += r["export"]

    days = []
    for i in range(29, -1, -1):
        d = (dt.date.fromisoformat(today) - dt.timedelta(days=i)).isoformat()
        produced = (solar or {}).get("daily", {}).get(d)
        g = grid.get(d)
        used = round(produced + g["import"] - g["export"], 1) if g and produced is not None else None
        sun = ((weather or {}).get("days") or {}).get(d, {}).get("sun_kwh_m2")
        days.append({"date": d, "produced": produced, "used": used, "sun": sun})

    # Panels vs. sunlight: today's kWh per unit of sunlight, against this system's usual ratio.
    performance = None
    if solar and weather:
        ratios = [x["produced"] / x["sun"] for x in days[:-1]
                  if x["produced"] and x["sun"] and x["sun"] > 1.0]
        sun_today = days[-1]["sun"]
        if len(ratios) >= 5 and sun_today and sun_today > 0.3:
            pct = round(solar["today_kwh"] / sun_today / statistics.median(ratios) * 100)
            performance = {"pct": pct, "baseline_days": len(ratios)}
        else:
            performance = {"pct": None, "baseline_days": len(ratios)}

    produced = [x["produced"] for x in days[:-1] if x["produced"]]
    typical = statistics.median(produced) if produced else 0
    low_days = [x for x in days[:-1] if x["produced"] is not None and typical and x["produced"] < 0.6 * typical]
    for x in low_days:
        typical_sun = statistics.median([y["sun"] for y in days if y["sun"]]) if weather else None
        x["cloudy"] = bool(x["sun"] and typical_sun and x["sun"] < 0.7 * typical_sun)

    if weather:
        weather = {k: v for k, v in weather.items() if k != "days"}
    if solar:
        solar = {k: v for k, v in solar.items() if k != "daily"}
    return {
        "generated_at": now_utc.isoformat(),
        "today": today,
        "sample": False,
        "status": status,
        "solar": solar,
        "weather": weather,
        "bill": bill_view(rows, today),
        "days": days,
        "low_days": [{"date": x["date"], "cloudy": x.get("cloudy")} for x in low_days],
        "performance": performance,
    }


def main():
    os.makedirs(os.path.join(DATA_DIR, "pge"), exist_ok=True)
    state_path = os.path.join(DATA_DIR, "state.json")
    state = load_json(state_path, {})
    now_utc = dt.datetime.now(dt.timezone.utc)
    status = {}
    for name, fn in (("solar", fetch_solar), ("weather", fetch_weather)):
        try:
            status[name] = fn(state, now_utc) or "ok"
        except Exception as e:  # keep going so the page still shows cached data
            traceback.print_exc()
            status[name] = f"Error: {e}"
    save_json(state_path, state)
    status["pge"] = "ok" if any(f.endswith(".csv") for f in os.listdir(os.path.join(DATA_DIR, "pge"))) \
        else "No PG&E file yet."
    out = build(state, status, now_utc)
    save_json(os.path.join(DATA_DIR, "dashboard.json"), out)
    print(json.dumps(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
