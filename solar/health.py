"""Flu, COVID and RSV going around Portland, from CDC's weekly wastewater viral activity levels."""
import datetime as dt
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
PORTLAND = ("Multnomah", "Washington", "Clackamas", "Columbia", "Clark")
NAMES = {"Influenza A virus": "Flu", "SARS-CoV-2": "COVID", "RSV": "RSV"}
ORDER = ["Very Low", "Low", "Moderate", "High", "Very High"]


def _rows(today):
    since = (today - dt.timedelta(days=42)).isoformat()
    url = "https://data.cdc.gov/resource/atcp-73re.json?" + urllib.parse.urlencode({
        "$where": f"state_territory in ('Oregon','Washington') AND week_end >= '{since}'", "$limit": 20000})
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)


def _level(rows):
    """Population-weighted activity level across sites, and the category most people's sites are in."""
    total = sum(float(r.get("population_served") or 0) or 1 for r in rows)
    wval = sum(float(r["site_wval"]) * (float(r.get("population_served") or 0) or 1) for r in rows) / total
    weights = {}
    for r in rows:
        c = r.get("site_wval_category")
        if c in ORDER:
            weights[c] = weights.get(c, 0) + (float(r.get("population_served") or 0) or 1)
    cat = max(weights, key=weights.get) if weights else None
    return wval, cat


def wastewater(today):
    rows = [r for r in _rows(today) if r.get("site_wval") not in (None, "")]
    area = [r for r in rows if r.get("state_territory") == "Oregon" or
            any(c in (r.get("counties_served") or "") for c in ("Clark",))]
    local = [r for r in area if any(c in (r.get("counties_served") or "") for c in PORTLAND)]
    use = local or [r for r in rows if r.get("state_territory") == "Oregon"]
    if not use:
        raise RuntimeError("CDC had no recent Oregon wastewater readings")
    out = []
    for target, name in NAMES.items():
        mine = [r for r in use if r.get("pathogen_target") == target]
        weeks = sorted({r["week_end"][:10] for r in mine})
        if not weeks:
            continue
        cur, cat = _level([r for r in mine if r["week_end"][:10] == weeks[-1]])
        trend = None
        if len(weeks) > 1:
            prev, _ = _level([r for r in mine if r["week_end"][:10] == weeks[-2]])
            trend = "rising" if cur > prev * 1.15 else "falling" if cur < prev * 0.85 else "steady"
        history = [round(_level([r for r in mine if r["week_end"][:10] == w])[0], 2) for w in weeks]
        out.append({"name": name, "level": cat, "rank": ORDER.index(cat) if cat in ORDER else None,
                    "trend": trend, "week_end": weeks[-1], "history": history,
                    "sites": len({r["site"] for r in mine if r["week_end"][:10] == weeks[-1]})})
    return {"area": "Portland area" if local else "Oregon", "items": out,
            "url": "https://www.cdc.gov/nwss/"}
