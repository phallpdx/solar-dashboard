"""Drive times from home to Parker's regular places, and a coast house report.

Addresses come only from the PLACES secret, one per line as "Label | address".
The line labeled Home is where drives start, and the one labeled Coast house also
gets a coast report. Nothing here saves an address or exact coordinates: places are
looked up fresh each time, and only labels, drive times and island-level (1 decimal)
coordinates for the coast forecast are written out.
"""
import datetime as dt
import json
import urllib.parse
import urllib.request

from . import alerts, outside

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def parse(secret):
    out = []
    for line in (secret or "").splitlines():
        if "|" in line:
            label, address = (x.strip() for x in line.split("|", 1))
            if label and address:
                out.append((label, address))
    return out


def _locate(address):
    """Never let an address reach an error message: errors end up in the public status."""
    if isinstance(address, (tuple, list)):
        return tuple(address)
    try:
        return outside.geocode(address)
    except Exception:
        pass
    # House numbers in rural areas are often missing from OpenStreetMap; fall back to the street.
    street = address.split(",", 1)
    parts = street[0].split(" ", 1)
    if parts[0].isdigit() and len(parts) > 1:
        try:
            return outside.geocode(parts[1] + ("," + street[1] if len(street) > 1 else ""))
        except Exception:
            pass
    raise RuntimeError("couldn't find that place on the map")


def _osrm(a, b):
    r = _get("https://router.project-osrm.org/route/v1/driving/"
             f"{a[1]},{a[0]};{b[1]},{b[0]}?overview=false")
    route = r["routes"][0]
    return route["duration"] / 60, route["distance"] / 1609.34


def _tomtom(a, b, key):
    r = _get(f"https://api.tomtom.com/routing/1/calculateRoute/{a[0]},{a[1]}:{b[0]},{b[1]}/json?"
             + urllib.parse.urlencode({"key": key, "traffic": "true", "travelMode": "car",
                                       "computeTravelTimeFor": "all"}))
    s = r["routes"][0]["summary"]
    return {"minutes": s["travelTimeInSeconds"] / 60,
            "usual": (s.get("noTrafficTravelTimeInSeconds") or s.get("historicTrafficTravelTimeInSeconds")
                      or s["travelTimeInSeconds"]) / 60,
            "delay": s.get("trafficDelayInSeconds", 0) / 60, "miles": s["lengthInMeters"] / 1609.34}


def commute(places, tomtom_key=None):
    lookup = dict(places)
    if "Home" not in lookup:
        raise RuntimeError("PLACES needs a line labeled Home")
    home = _locate(lookup["Home"])
    out = []
    for label, address in places:
        if label == "Home":
            continue
        try:
            there = _locate(address)
            if tomtom_key:
                t = _tomtom(home, there, tomtom_key)
                out.append({"label": label, "minutes": round(t["minutes"]), "usual": round(t["usual"]),
                            "delay": round(t["delay"]), "miles": round(t["miles"]), "live": True})
            else:
                minutes, miles = _osrm(home, there)
                out.append({"label": label, "minutes": round(minutes), "usual": round(minutes),
                            "delay": 0, "miles": round(miles), "live": False})
        except Exception as e:
            out.append({"label": label, "error": str(e)[:120]})
    return out


def coast(address, today):
    """Weather, surf, tides and warnings at the coast house, at island-level precision."""
    lat, lon = _locate(address)
    lat, lon = round(lat, 1), round(lon, 1)
    f = outside._get("https://api.open-meteo.com/v1/forecast", latitude=lat, longitude=lon,
                     timezone="America/Los_Angeles", forecast_days=7, temperature_unit="fahrenheit",
                     wind_speed_unit="mph", precipitation_unit="inch",
                     current="temperature_2m,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m",
                     daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,"
                           "precipitation_probability_max,wind_gusts_10m_max,sunset,uv_index_max")
    d = f["daily"]
    days = [{"date": t, "code": d["weather_code"][i], "hi": round(d["temperature_2m_max"][i]),
             "lo": round(d["temperature_2m_min"][i]), "rain_in": d["precipitation_sum"][i],
             "rain_pct": d["precipitation_probability_max"][i], "gust": round(d["wind_gusts_10m_max"][i] or 0),
             "sunset": (d["sunset"][i] or "T")[11:16], "uv": d["uv_index_max"][i]} for i, t in enumerate(d["time"])]
    out = {"now": f.get("current"), "days": days}
    # Surf: the ocean just offshore (the coast faces west).
    try:
        m = outside._get("https://marine-api.open-meteo.com/v1/marine", latitude=lat, longitude=round(lon - 0.1, 2),
                         timezone="America/Los_Angeles", forecast_days=7, length_unit="imperial",
                         daily="wave_height_max,wave_period_max,swell_wave_height_max",
                         hourly="sea_surface_temperature")
        md = m["daily"]
        for i, day in enumerate(days):
            if i < len(md["time"]):
                day["waves_ft"] = round(md["wave_height_max"][i] or 0)
                day["period_s"] = round(md["wave_period_max"][i] or 0)
        sst = [v for v in (m.get("hourly") or {}).get("sea_surface_temperature", []) if v is not None]
        out["water_f"] = round(sst[0] * 9 / 5 + 32) if sst and sst[0] < 40 else (round(sst[0]) if sst else None)
    except Exception as e:
        out["surf_error"] = str(e)[:120]
    try:
        out["alerts"] = alerts.nws(lat, lon)
    except Exception as e:
        out["alerts"] = []
        out["alerts_error"] = str(e)[:120]
    try:
        station = outside.tide_station(lat, lon, max_km=40)
        if station:
            tides = outside.tides(station["id"], today, hours=24 * 14)
            out["tide_station"] = station["name"]
            out["tides"] = [t for t in tides if t["t"][:10] <= (today + dt.timedelta(days=1)).isoformat()]
            out["minus_tides"] = [t for t in tides if t["type"] == "Low" and t["ft"] < 0][:10]
    except Exception as e:
        out["tides_error"] = str(e)[:120]
    return out
