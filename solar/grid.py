"""What's powering the Northwest grid right now, from BPA's 5-minute balancing authority data."""
import datetime as dt
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
URL = "https://transmission.bpa.gov/business/operations/wind/baltwg.txt"


def parse(text):
    rows = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 6 or not parts[0][:2].isdigit():
            continue
        try:
            when = dt.datetime.strptime(parts[0].strip(), "%m/%d/%Y %H:%M")
            load, ver, hydro, fossil, nuclear = (float(p) if p.strip() else None for p in parts[1:6])
        except ValueError:
            continue
        if None in (hydro, fossil) or ver is None:
            continue
        rows.append((when, load, ver, hydro, fossil, nuclear or 0.0))
    if not rows:
        raise RuntimeError("BPA file had no readings")
    return rows


def _mix(r):
    _, load, ver, hydro, fossil, nuclear = r
    gen = max(1.0, ver + hydro + fossil + nuclear)
    return {"hydro": round(hydro / gen * 100), "wind_solar": round(ver / gen * 100),
            "nuclear": round(nuclear / gen * 100), "fossil": round(fossil / gen * 100),
            "clean": round((1 - fossil / gen) * 100), "load_mw": round(load or 0), "gen_mw": round(gen)}


def _span(hours):
    """[1, 2, 3, 4] -> '1 am to 5 am'."""
    fmt = lambda h: f"{h % 12 or 12} {'am' if h % 24 < 12 else 'pm'}"
    return f"{fmt(hours[0])} to {fmt(hours[-1] + 1)}"


def _best_run(values, n, lowest=True):
    """Start hour of the n-hour stretch (wrapping midnight) with the lowest (or highest) average."""
    score = lambda s: sum(values[(s + k) % 24] for k in range(n))
    start = (min if lowest else max)(range(24), key=score)
    return [(start + k) % 24 for k in range(n)]


def status():
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        rows = parse(resp.read().decode("utf-8", "replace"))
    now = rows[-1]
    by_hour = {h: [] for h in range(24)}
    load_hour = {h: [] for h in range(24)}
    for r in rows:
        m = _mix(r)
        by_hour[r[0].hour].append(m["fossil"])
        load_hour[r[0].hour].append(m["load_mw"])
    avg = lambda xs: sum(xs) / len(xs) if xs else 0
    fossil_h = [avg(by_hour[h]) for h in range(24)]
    load_h = [avg(load_hour[h]) for h in range(24)]
    week_clean = round(100 - avg([_mix(r)["fossil"] for r in rows]))
    return {"as_of": now[0].strftime("%Y-%m-%dT%H:%M"), **_mix(now), "week_clean": week_clean,
            "cleanest": _span(_best_run(fossil_h, 4, True)), "peak": _span(_best_run(load_h, 3, False)),
            "url": "https://transmission.bpa.gov/business/operations/wind/"}
