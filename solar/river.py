"""The Columbia and the Willamette in front of home: stage, flow and water temperature (USGS), the
National Water Prediction Service forecast, and Coast Guard / NWS warnings for the Columbia River bar."""
import datetime as dt
import json
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)", "Accept": "application/json"}

# USGS gauges: the Columbia at Vancouver (stage, the closest gauge upstream of home), the Columbia at Port
# Westward (the nearest gauge below the island with flow) and the Willamette at Portland, which carries the
# water-temperature sensor.
GAUGES = [("vancouver", "14144700", "Columbia at Vancouver"), ("columbia", "14246900", "Columbia at Port Westward"),
          ("willamette", "14211720", "Willamette at Portland")]
PARAMS = {"00065": "stage_ft", "00060": "flow_cfs", "00010": "temp_c"}
# NWPS gauge ids for the forecast: the Columbia at Vancouver and the Willamette at Portland.
NWPS = [("columbia", "VAPW1", "Columbia at Vancouver"), ("willamette", "PRTO3", "Willamette at Portland")]


def _get(url, as_json=True):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = resp.read()
    return json.loads(data) if as_json else data.decode("utf-8", "replace")


def parse_usgs(data):
    out = {}
    for ts in (data.get("value") or {}).get("timeSeries") or []:
        site = ts["sourceInfo"]["siteCode"][0]["value"]
        key = next((k for k, s, _ in GAUGES if s == site), None)
        code = ts["variable"]["variableCode"][0]["value"]
        if not key or code not in PARAMS:
            continue
        values = [(v["dateTime"], float(v["value"])) for v in (ts["values"][0]["value"] or []) if v.get("value") not in (None, "", "-999999")]
        if not values:
            continue
        g = out.setdefault(key, {"name": next(n for k, _, n in GAUGES if k == key), "site": site,
                                 "url": f"https://waterdata.usgs.gov/monitoring-location/{site}/"})
        field = PARAMS[code]
        g[field] = round(values[-1][1], 2)
        g["at"] = values[-1][0]
        # The day's average for a small sparkline: the lower river rises and falls with each tide, so a single
        # reading a day would jump around; the mean shows the river's own trend. USGS times are local.
        by_day = {}
        for when, val in values:
            by_day.setdefault(when[:10], []).append(val)
        g[field + "_days"] = [{"date": d, "v": round(sum(v) / len(v), 2)} for d, v in sorted(by_day.items())[-8:]]
        if field == "temp_c":
            g["temp_f"] = round(values[-1][1] * 9 / 5 + 32)
    if not out:
        raise RuntimeError("USGS returned no readings")
    return out


def usgs():
    """Latest stage, flow and temperature for the last 7 days (USGS Water Services, 15-minute data)."""
    url = "https://waterservices.usgs.gov/nwis/iv/?" + urllib.parse.urlencode(
        {"format": "json", "sites": ",".join(s for _, s, _ in GAUGES), "parameterCd": ",".join(PARAMS), "period": "P7D"})
    return parse_usgs(_get(url))


PACIFIC = dt.timezone(dt.timedelta(hours=-8))  # standard time is close enough to bin a day's forecast


def forecast_days(points):
    """The hourly NWS forecast as one average a day (Pacific dates), like the observed line. The hourly values
    swing with the tide; sampling them every few hours drew a zigzag. Days missing more than a few hours are dropped, since a part day skews the tidal average."""
    by_day = {}
    for t, v in points:
        try:
            when = dt.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(PACIFIC)
        except ValueError:
            continue
        by_day.setdefault(when.date().isoformat(), []).append(v)
    full = max((len(v) for v in by_day.values()), default=0)
    return [{"date": d, "v": round(sum(v) / len(v), 2)} for d, v in sorted(by_day.items()) if len(v) * 6 >= full * 5]


def parse_nwps(gauge, series):
    status = gauge.get("status") or {}
    obs, fc = status.get("observed") or {}, status.get("forecast") or {}
    cats = ((gauge.get("flood") or {}).get("categories") or {})
    action = (cats.get("action") or {}).get("stage")
    minor = (cats.get("minor") or {}).get("stage")
    points = [(p["validTime"], p["primary"]) for p in ((series.get("forecast") or {}).get("data") or [])
              if p.get("primary") not in (None, -999, -9999)]
    crest = max(points, key=lambda p: p[1]) if points else None
    return {"lid": gauge.get("lid"), "name": gauge.get("name"), "stage_ft": obs.get("primary"), "at": obs.get("validTime"),
            "category": obs.get("floodCategory"), "action_ft": action if action not in (None, -9999) else None,
            "minor_ft": minor if minor not in (None, -9999) else None,
            "forecast_days": forecast_days(points),
            "crest_ft": round(crest[1], 2) if crest else None, "crest_at": crest[0] if crest else None,
            "forecast_issued": (series.get("forecast") or {}).get("issuedTime"),
            "url": f"https://water.noaa.gov/gauges/{gauge.get('lid')}"}


def nwps():
    """NWS river forecasts: current stage, flood stages and the forecast crest for the next days."""
    out = {}
    for key, lid, _ in NWPS:
        gauge = _get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}")
        series = _get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}/stageflow")
        out[key] = parse_nwps(gauge, series)
    return out


def parse_alerts(data):
    out = []
    for f in data.get("features") or []:
        p = f.get("properties") or {}
        out.append({"event": p.get("event"), "headline": p.get("headline"), "severity": p.get("severity"),
                    "onset": p.get("onset") or p.get("effective"), "expires": p.get("ends") or p.get("expires"),
                    "description": (p.get("description") or "").replace("\n", " ")[:400], "url": p.get("@id")})
    return out


def bar_alerts():
    """Active NWS marine alerts for the Columbia River bar (zone PZZ210): small craft advisories, gale warnings,
    hazardous seas and the Coast Guard's bar restrictions when the NWS relays them."""
    return parse_alerts(_get("https://api.weather.gov/alerts/active?zone=PZZ210"))


def surf_zone():
    """The Portland office's surf zone forecast for the north coast: rip current risk and surf heights.
    Returns the latest product's text split into the coastal segments."""
    listing = _get("https://api.weather.gov/products/types/SRF/locations/PQR")
    items = listing.get("@graph") or []
    if not items:
        return None
    latest = max(items, key=lambda x: x.get("issuanceTime") or "")
    product = _get(latest["@id"])
    text = product.get("productText") or ""
    return {"issued": latest.get("issuanceTime"), "text": text[:6000], "url": latest["@id"], **parse_surf_zone(text)}


def parse_surf_zone(text, want=("SEASIDE", "CANNON BEACH", "CLATSOP")):
    """Pull today's and tomorrow's surf height, offshore swell and wind for the north Oregon coast segment
    out of the plain-text product (segments are headed like "SEASIDE AND CANNON BEACH OREGON-")."""
    segment, days, cur = None, [], None
    for raw in text.splitlines():
        l = raw.strip()
        if re.match(r"^[A-Z][A-Z ,.]+-$", l) and l.rstrip("-").strip():
            if segment is not None and days:
                break  # the segment we wanted is complete
            segment = l.rstrip("-").title().replace(" And ", " and ") if any(w in l for w in want) else None
            continue
        if segment is None:
            continue
        m = re.match(r"^\.([A-Z ]+)\.\.\.$", l)
        if m:
            cur = {"day": m.group(1).title()}
            days.append(cur)
            continue
        if cur is None or "..." not in l:
            continue
        key, _, val = l.partition("...")
        val = val.lstrip(".").strip().rstrip(".")
        key = key.strip().lower()
        if key == "surf height":
            cur["surf"] = val
        elif key == "offshore swell":
            cur["swell"] = val
        elif key == "wind":
            cur["wind"] = val
        elif key == "weather":
            cur["weather"] = val
        elif "rip current" in key:
            cur["rip"] = val
    return {"segment": segment, "days": days[:3]}
