"""Physics-based solar expectations: Open-Meteo's irradiance forecast on the roof's tilt, and PVGIS's
long-term monthly yield for a system this size, to compare against what APsystems reports."""
import datetime as dt
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}


def _get(url, **params):
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)


def irradiance(lat, lon, tilt=25, azimuth=0, tz="America/Los_Angeles", days=7):
    """Hourly global tilted irradiance (W/m²) on the panels and the daily kWh/m² it adds up to."""
    data = _get("https://api.open-meteo.com/v1/forecast", latitude=lat, longitude=lon,
                hourly="shortwave_radiation,direct_normal_irradiance,diffuse_radiation,global_tilted_irradiance",
                tilt=tilt, azimuth=azimuth, timezone=tz, forecast_days=days)
    return parse_irradiance(data, tilt, azimuth)


def parse_irradiance(data, tilt, azimuth):
    h = data.get("hourly") or {}
    times, gti, ghi, dni = h.get("time") or [], h.get("global_tilted_irradiance") or [], h.get("shortwave_radiation") or [], h.get("direct_normal_irradiance") or []
    days = {}
    for i, t in enumerate(times):
        d = days.setdefault(t[:10], {"date": t[:10], "tilted_kwh_m2": 0.0, "flat_kwh_m2": 0.0, "direct_kwh_m2": 0.0, "peak_wm2": 0, "hours": []})
        g = gti[i] or 0
        d["tilted_kwh_m2"] += g / 1000
        d["flat_kwh_m2"] += (ghi[i] or 0) / 1000
        d["direct_kwh_m2"] += (dni[i] or 0) / 1000
        d["peak_wm2"] = max(d["peak_wm2"], round(g))
        d["hours"].append({"t": t[11:16], "wm2": round(g)})
    out = []
    for d in days.values():
        for k in ("tilted_kwh_m2", "flat_kwh_m2", "direct_kwh_m2"):
            d[k] = round(d[k], 2)
        # A day is "direct sun" when the beam carries most of the energy; diffuse days are flat and grey.
        d["kind"] = ("grey" if d["flat_kwh_m2"] < 0.8 else "sunny" if d["direct_kwh_m2"] > d["flat_kwh_m2"]
                     else "mixed" if d["direct_kwh_m2"] > d["flat_kwh_m2"] * 0.4 else "grey")
        out.append(d)
    if not out:
        raise RuntimeError("Open-Meteo returned no irradiance")
    return {"tilt": tilt, "azimuth": azimuth, "days": out}


def pvgis_monthly(lat, lon, kwp, tilt=25, azimuth=0, loss=14):
    """Long-term monthly yield (kWh) for a system of kwp on this roof, from PVGIS (ERA5, 2005-2023)."""
    data = _get("https://re.jrc.ec.europa.eu/api/v5_3/PVcalc", lat=lat, lon=lon, peakpower=kwp, loss=loss,
                angle=tilt, aspect=azimuth, outputformat="json")
    return parse_pvgis(data, kwp)


def parse_pvgis(data, kwp):
    months = (((data.get("outputs") or {}).get("monthly") or {}).get("fixed")) or []
    if not months:
        raise RuntimeError("PVGIS returned no monthly yield")
    year = sum(m["E_m"] for m in months)
    return {"kwp": kwp, "year_kwh": round(year), "months": [{"month": m["month"], "kwh": round(m["E_m"]), "per_day": round(m["E_d"], 1),
                                                           "sun_kwh_m2_day": round(m["H(i)_d"], 2)} for m in months],
            "db": ((data.get("inputs") or {}).get("meteo_data") or {}).get("radiation_db"),
            "url": "https://re.jrc.ec.europa.eu/pvg_tools/en/"}
