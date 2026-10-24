"""Columbia River fishing outlook: fish counts over Bonneville Dam, river level and temperature, what's in season,
and the best times to be on the water from tides, moon and light."""
import csv
import datetime as dt
import io
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}

# USGS gauges: Columbia at Vancouver (stage), Columbia at Beaver Army Terminal near Quincy (water temperature).
GAUGES = [("14144700", "Columbia River at Vancouver"), ("14246900", "Columbia River near Quincy")]

# What's typically worth fishing for on the lower Columbia around Sauvie Island, by month.
SEASONS = {
    1: [("Winter steelhead", "Plunking from the beaches on the rising river"), ("Sturgeon", "Catch and release")],
    2: [("Winter steelhead", "Plunking from the beaches"), ("Spring Chinook", "First early fish show up late in the month"),
        ("Sturgeon", "Catch and release")],
    3: [("Spring Chinook", "Springers build through the month; check the season dates"),
        ("Winter steelhead", "Tail end of the run"), ("Sturgeon", "Catch and release")],
    4: [("Spring Chinook", "Peak of the springer run"), ("Sturgeon", "Catch and release")],
    5: [("Spring Chinook", "Late springers, if the season is open"), ("Shad", "Run starts mid-May"),
        ("Bass and crappie", "Island sloughs and lakes warm up")],
    6: [("Shad", "Peak run, easy action from shore"), ("Summer Chinook", "Usually opens mid-June"),
        ("Summer steelhead", "Early fish moving through"), ("Bass and crappie", "Sloughs and Sturgeon Lake")],
    7: [("Summer steelhead", "Best early mornings"), ("Summer Chinook", None), ("Shad", "Tapering off"),
        ("Bass and catfish", "Warm water in the sloughs")],
    8: [("Fall Chinook", "Upriver brights start arriving late August"), ("Summer steelhead", None),
        ("Bass and catfish", "Warm water in the sloughs")],
    9: [("Fall Chinook", "Peak of the fall run"), ("Coho", "Building through the month"),
        ("Summer steelhead", None)],
    10: [("Coho", "Late coho moving upriver"), ("Fall Chinook", "Tail end; darker fish"),
         ("Sturgeon", "Catch and release"), ("Crappie", "Sloughs as water cools")],
    11: [("Coho", "Last of the late run"), ("Sturgeon", "Catch and release"),
         ("Winter steelhead", "First fish show up late in the month")],
    12: [("Winter steelhead", "Plunking from the beaches"), ("Sturgeon", "Catch and release")],
}
LINKS = [
    ("ODFW fishing report", "https://myodfw.com/recreation-report/fishing-report/columbia-zone"),
    ("ODFW regulation updates", "https://myodfw.com/fishing/regulation-updates"),
    ("WDFW emergency rules", "https://wdfw.wa.gov/fishing/regulations/emergency-rules"),
]


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def dam_counts(today):
    """Adult fish counted over Bonneville Dam, last 7 days (Columbia Basin Research DART)."""
    start = today - dt.timedelta(days=10)
    url = "https://www.cbr.washington.edu/dart/cs/php/rpt/adult_daily.php?" + urllib.parse.urlencode({
        "sc": 1, "outputFormat": "csv", "year": today.year, "proj": "BON", "span": "no",
        "startdate": f"{start.month}/{start.day}", "enddate": f"{today.month}/{today.day}"})
    text = _get(url)
    rows = [r for r in csv.reader(io.StringIO(text)) if r]
    head_i = next((i for i, r in enumerate(rows) if any("date" in c.lower() for c in r)), None)
    if head_i is None:
        raise RuntimeError("DART returned no table: " + text[:200].replace("\n", " "))
    head = [c.strip() for c in rows[head_i]]
    want = {"Chinook": ("chin",), "Coho": ("coho",), "Steelhead": ("stlhd", "steelhead"),
            "Sockeye": ("sock",), "Shad": ("shad",), "Lamprey": ("lmpry", "lamprey")}
    cols = {}
    for name, keys in want.items():
        for i, h in enumerate(head):
            low = h.lower()
            # Skip jack and wild-only columns; adults are the plain species column.
            if any(k in low for k in keys) and not low.startswith("j") and "wild" not in low and not low.startswith("w"):
                cols[name] = i
                break
    date_i = next(i for i, h in enumerate(head) if "date" in h.lower())
    days = []
    for r in rows[head_i + 1:]:
        if len(r) <= date_i or not r[date_i].strip()[:1].isdigit():
            continue
        counts = {}
        for name, i in cols.items():
            try:
                counts[name] = int(float(r[i]))
            except (IndexError, ValueError):
                pass
        if counts:
            days.append({"date": r[date_i].strip(), "counts": counts})
    days = days[-7:]
    if not days:
        raise RuntimeError("DART table had no counts; columns: " + ", ".join(head))
    totals = {}
    for d in days:
        for k, v in d["counts"].items():
            totals[k] = totals.get(k, 0) + v
    return {"dam": "Bonneville", "days": len(days), "through": days[-1]["date"],
            "week": dict(sorted(totals.items(), key=lambda kv: -kv[1])), "last_day": days[-1]["counts"]}


def river():
    """Latest river stage (ft) and water temperature (°F), with the 24-hour change in stage."""
    url = "https://waterservices.usgs.gov/nwis/iv/?" + urllib.parse.urlencode({
        "format": "json", "sites": ",".join(g for g, _ in GAUGES), "parameterCd": "00065,00010", "period": "P1D"})
    data = json.loads(_get(url))
    out = {}
    for ts in data["value"]["timeSeries"]:
        code = ts["variable"]["variableCode"][0]["value"]
        values = [v for v in ts["values"][0]["value"] if v["value"] not in ("", "-999999")]
        if not values:
            continue
        last, first = float(values[-1]["value"]), float(values[0]["value"])
        site = ts["sourceInfo"]["siteName"].title()
        if code == "00065" and "stage_ft" not in out:
            out.update(stage_ft=round(last, 1), stage_change_ft=round(last - first, 1), stage_site=site,
                       stage_at=values[-1]["dateTime"])
        elif code == "00010" and "water_f" not in out:
            out.update(water_f=round(last * 9 / 5 + 32), water_site=site)
    if not out:
        raise RuntimeError("USGS returned no readings")
    return out


def _window(center, half_min, label):
    return {"start": center - dt.timedelta(minutes=half_min), "end": center + dt.timedelta(minutes=half_min),
            "why": [label]}


def best_times(day, tz, moon_transit, moonrise, moonset, tides, sunrise, sunset):
    """Fishing windows for one day: solunar periods, tide turns and low light, ranked by how many line up."""
    def at(hhmm):
        if not hhmm:
            return None
        h, m = map(int, hhmm.split(":")[:2])
        return dt.datetime(day.year, day.month, day.day, h, m, tzinfo=tz)

    windows = []
    t = at(moon_transit)
    if t:
        windows.append(_window(t, 60, "moon overhead"))
        under = t + dt.timedelta(hours=12, minutes=25)
        if under.date() != day:
            under -= dt.timedelta(hours=24, minutes=50)
        windows.append(_window(under, 60, "moon underfoot"))
    for hhmm, label in ((moonrise, "moonrise"), (moonset, "moonset")):
        if at(hhmm):
            windows.append(_window(at(hhmm), 40, label))
    for x in tides:
        when = dt.datetime.fromisoformat(x["t"].replace(" ", "T")).replace(tzinfo=tz)
        if when.date() == day:
            windows.append(_window(when, 60, f"tide turning ({x['type'].lower()} {x['ft']} ft)"))
    if at(sunrise):
        windows.append(_window(at(sunrise), 60, "dawn"))
    if at(sunset):
        windows.append(_window(at(sunset), 60, "dusk"))
    windows.sort(key=lambda w: w["start"])
    merged = []
    for w in windows:  # overlapping windows reinforce each other
        if merged and w["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], w["end"])
            merged[-1]["why"] += w["why"]
        else:
            merged.append(dict(w, why=list(w["why"])))
    for w in merged:
        w["score"] = len(w["why"])
        w["start"], w["end"] = w["start"].strftime("%H:%M"), w["end"].strftime("%H:%M")
    return merged
