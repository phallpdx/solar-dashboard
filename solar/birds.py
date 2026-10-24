"""Rare and notable birds reported near home in the last week (eBird, needs a free EBIRD_KEY)."""
import json
import urllib.parse
import urllib.request


def notable(lat, lon, key, km=15, days=7, limit=15):
    url = "https://api.ebird.org/v2/data/obs/geo/recent/notable?" + urllib.parse.urlencode(
        {"lat": lat, "lng": lon, "dist": km, "back": days, "detail": "simple"})
    req = urllib.request.Request(url, headers={"X-eBirdApiToken": key, "User-Agent": "solar-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        rows = json.load(resp)
    seen, out = {}, []
    for r in sorted(rows, key=lambda r: r.get("obsDt") or "", reverse=True):
        if r.get("locationPrivate"):  # someone's yard: leave it off a public page
            continue
        code = r.get("speciesCode")
        if code in seen:
            seen[code]["reports"] += 1
            continue
        seen[code] = {"name": r.get("comName"), "where": r.get("locName"), "when": r.get("obsDt"),
                      "count": r.get("howMany"), "confirmed": bool(r.get("obsReviewed") and r.get("obsValid")),
                      "reports": 1, "url": f"https://ebird.org/species/{code}"}
        out.append(seen[code])
    return out[:limit]
