"""Everything useful before heading outside, from free keyless APIs.

- Forecast, sunrise/sunset, UV and sunlight: Open-Meteo (open-meteo.com)
- Air quality: Open-Meteo air quality (US AQI)
- Tides: NOAA CO-OPS, nearest tide station (coastal homes only)
- Birds and flowering native plants: iNaturalist observations nearby
- Food in season: a California produce calendar kept in this file
"""
import datetime as dt
import json
import math
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}


def _get(url, **params):
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)


def geocode(address):
    """Address -> (lat, lon) with OpenStreetMap Nominatim. Called once, then cached."""
    hits = _get("https://nominatim.openstreetmap.org/search", q=address, format="json", limit=1,
                countrycodes="us")
    if not hits:
        raise RuntimeError(f"Couldn't find that address: {address}")
    return float(hits[0]["lat"]), float(hits[0]["lon"])


def forecast(lat, lon, tz):
    return _get(
        "https://api.open-meteo.com/v1/forecast",
        latitude=lat, longitude=lon, timezone=tz, forecast_days=7, past_days=31,
        temperature_unit="fahrenheit", wind_speed_unit="mph", precipitation_unit="inch",
        current="temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,"
                "cloud_cover,relative_humidity_2m",
        daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
              "precipitation_sum,sunrise,sunset,daylight_duration,uv_index_max,shortwave_radiation_sum,"
              "wind_speed_10m_max,wind_gusts_10m_max,snowfall_sum",
        hourly="temperature_2m,precipitation_probability,cloud_cover,shortwave_radiation",
    )


def air(lat, lon, tz):
    return _get(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        latitude=lat, longitude=lon, timezone=tz, forecast_days=2,
        current="us_aqi,pm2_5,ozone",
        hourly="us_aqi",
    )


def tide_station(lat, lon, max_km=25.0):
    """Nearest NOAA water-level station within ~25 km, or None for inland homes."""
    data = _get("https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json",
                type="tidepredictions")
    best, best_km = None, max_km
    for s in data.get("stations", []):
        km = _km(lat, lon, float(s["lat"]), float(s["lng"]))
        if km < best_km:
            best, best_km = {"id": s["id"], "name": s["name"], "km": round(km, 1)}, km
    return best


def tides(station_id, day, hours=48):
    data = _get("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                product="predictions", station=station_id, datum="MLLW", units="english",
                time_zone="lst_ldt", interval="hilo", format="json",
                begin_date=day.strftime("%Y%m%d"), range=hours)
    return [{"t": p["t"], "ft": round(float(p["v"]), 1), "type": "High" if p["type"] == "H" else "Low"}
            for p in data.get("predictions", [])]


def _inat_species(lat, lon, days, **filters):
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    data = _get("https://api.inaturalist.org/v1/observations/species_counts",
                lat=lat, lng=lon, radius=15, d1=since, quality_grade="research",
                per_page=12, locale="en", **filters)
    out = []
    for r in data.get("results", []):
        taxon = r["taxon"]
        photo = (taxon.get("default_photo") or {}).get("square_url")
        out.append({
            "name": taxon.get("preferred_common_name") or taxon.get("name"),
            "sci": taxon.get("name"),
            "count": r.get("count"),
            "photo": photo,
            "url": f"https://www.inaturalist.org/taxa/{taxon['id']}",
        })
    return out


def birds(lat, lon):
    """Birds people reported within 15 km in the last two weeks, most-seen first."""
    return _inat_species(lat, lon, 14, iconic_taxa="Aves")


def blooms(lat, lon):
    """Native plants seen flowering within 15 km in the last month."""
    return _inat_species(lat, lon, 30, iconic_taxa="Plantae", native="true",
                         term_id=12, term_value_id=13)


# Portland and the Willamette Valley, by month (1-12). Peak picks, not every crop.
PRODUCE = {
    1: ["Storage apples and pears", "Kale", "Leeks", "Winter squash", "Dungeness crab"],
    2: ["Hazelnuts", "Kale", "Parsnips", "Storage potatoes", "Dungeness crab"],
    3: ["Nettles", "Purple sprouting broccoli", "Overwintered greens", "Morels (late)"],
    4: ["Asparagus", "Rhubarb", "Morels", "Radishes", "Spring onions"],
    5: ["Strawberries", "Asparagus", "Peas", "Rhubarb", "Spring chinook"],
    6: ["Strawberries", "Cherries", "Marionberries (late)", "Snap peas", "Spring chinook"],
    7: ["Marionberries", "Blueberries", "Raspberries", "Cherries", "Sweet corn"],
    8: ["Peaches", "Blueberries", "Tomatoes", "Sweet corn", "Melons", "Albacore"],
    9: ["Apples", "Pears", "Tomatoes", "Peppers", "Hazelnuts", "Fall chinook"],
    10: ["Apples", "Pears", "Winter squash", "Chanterelles", "Cranberries", "Pumpkins"],
    11: ["Chanterelles", "Cranberries", "Brussels sprouts", "Winter squash", "Hazelnuts"],
    12: ["Dungeness crab", "Kale", "Leeks", "Storage apples", "Citrus (shipped in)"],
}


def moon(day):
    """Moon phase name and illumination for a date (simple synodic-month model)."""
    known_new = dt.date(2000, 1, 6)
    age = ((day - known_new).days % 29.530588) / 29.530588
    lit = round((1 - math.cos(2 * math.pi * age)) / 2 * 100)
    names = ["New moon", "Waxing crescent", "First quarter", "Waxing gibbous",
             "Full moon", "Waning gibbous", "Last quarter", "Waning crescent"]
    return {"name": names[int(age * 8 + 0.5) % 8], "lit_pct": lit}


def _km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))
