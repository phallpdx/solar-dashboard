"""Ships heading past home on the Columbia, from live AIS radio data (aisstream.io).

Each run listens for a couple of minutes to every ship transmitting between
Longview and Portland, then estimates which moving vessels are heading
toward the river spot in front of home and roughly when they will pass.
"""
import asyncio
import datetime as dt
import json
import math

LISTEN_SECONDS = 150
# Columbia River from Longview down to Portland, plus the lower Willamette.
BOX = [[45.50, -123.20], [46.25, -122.55]]

TYPES = [
    (range(20, 30), "Wing-in-ground"), (range(30, 31), "Fishing boat"), (range(31, 33), "Tug and tow"),
    (range(33, 34), "Dredger"), (range(35, 36), "Military"), (range(36, 37), "Sailboat"),
    (range(37, 38), "Pleasure boat"), (range(50, 51), "Pilot boat"), (range(51, 52), "Search and rescue"),
    (range(52, 53), "Tug"), (range(55, 56), "Law enforcement"), (range(60, 70), "Passenger ship"),
    (range(70, 80), "Cargo ship"), (range(80, 90), "Tanker"),
]


def type_name(code):
    for r, name in TYPES:
        if code in r:
            return name
    return "Vessel"


def _km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _bearing(lat1, lon1, lat2, lon2):
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


async def _listen(key):
    import websockets  # installed in the workflow

    ships = {}
    sub = {"APIKey": key, "BoundingBoxes": [BOX],
           "FilterMessageTypes": ["PositionReport", "ShipStaticData", "StandardClassBPositionReport"]}
    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as ws:
        await ws.send(json.dumps(sub))
        end = asyncio.get_event_loop().time() + LISTEN_SECONDS
        while asyncio.get_event_loop().time() < end:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=end - asyncio.get_event_loop().time())
            except asyncio.TimeoutError:
                break
            msg = json.loads(raw)
            if "error" in msg:
                raise RuntimeError(msg["error"])
            meta = msg.get("MetaData", {})
            mmsi = meta.get("MMSI")
            if not mmsi:
                continue
            ship = ships.setdefault(mmsi, {"mmsi": mmsi})
            ship["name"] = (meta.get("ShipName") or ship.get("name") or "").strip()
            body = msg.get("Message", {}).get(msg.get("MessageType"), {})
            if msg["MessageType"] == "ShipStaticData":
                dim = body.get("Dimension") or {}
                ship.update(type=body.get("Type"), destination=(body.get("Destination") or "").strip(),
                            length_m=(dim.get("A") or 0) + (dim.get("B") or 0) or None,
                            callsign=body.get("CallSign"))
            else:
                ship.update(lat=meta.get("latitude"), lon=meta.get("longitude"),
                            sog=body.get("Sog"), cog=body.get("Cog"), seen=meta.get("time_utc"))
    return ships


def listen(key):
    return asyncio.run(_listen(key))


def merge(cache, fresh, now_utc):
    """Keep ship details (name, type) between runs; drop ships not heard for 6 hours."""
    for mmsi, ship in fresh.items():
        cache.setdefault(str(mmsi), {}).update({k: v for k, v in ship.items() if v not in (None, "")})
        cache[str(mmsi)]["heard"] = now_utc.isoformat()
    cutoff = (now_utc - dt.timedelta(hours=6)).isoformat()
    for mmsi in [m for m, s in cache.items() if s.get("heard", "") < cutoff]:
        del cache[mmsi]
    return cache


def approaching(cache, home_lat, home_lon, now_utc):
    """Ships moving toward home, soonest first, plus ones passing right now."""
    out = []
    for ship in cache.values():
        if ship.get("lat") is None:
            continue
        km = _km(ship["lat"], ship["lon"], home_lat, home_lon)
        sog = ship.get("sog") or 0
        heading_home = abs((_bearing(ship["lat"], ship["lon"], home_lat, home_lon) - (ship.get("cog") or 0) + 180) % 360 - 180) < 50
        if km < 1.5:
            eta_min = 0
        elif sog >= 2 and heading_home:
            # River distance runs about 1.3x the straight line on this stretch.
            eta_min = round(km * 1.3 / (sog * 1.852) * 60)
        else:
            continue
        heard = dt.datetime.fromisoformat(ship["heard"])
        eta_min -= round((now_utc - heard).total_seconds() / 60)
        if eta_min < -10 or eta_min > 360:
            continue
        code = ship.get("type")
        # The Columbia runs north-west past the island toward the ocean.
        if eta_min <= 0:
            upriver = 90 < (ship.get("cog") or 0) < 270
        else:
            upriver = ship["lat"] > home_lat  # north of home and closing in means heading upriver
        direction = "Headed toward Portland" if upriver else "Headed toward Astoria"
        out.append({
            "direction": direction,
            "name": (ship.get("name") or f"MMSI {ship['mmsi']}").title(),
            "type": type_name(code) if code else "Vessel",
            "destination": (ship.get("destination") or "").title() or None,
            "length_m": ship.get("length_m"),
            "km": round(km, 1),
            "knots": round(sog, 1),
            "eta_utc": (now_utc + dt.timedelta(minutes=max(eta_min, 0))).isoformat(),
            "passing_now": eta_min <= 0,
            "big": bool(code and code >= 60 and code < 90),
            "url": f"https://www.vesselfinder.com/vessels/details/{ship['mmsi']}",
        })
    out.sort(key=lambda s: s["eta_utc"])
    return out
