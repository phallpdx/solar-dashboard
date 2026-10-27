"""Ships heading past home on the Columbia, from live AIS radio data (aisstream.io).

Each run listens for a couple of minutes to every ship transmitting between
Longview and Portland, then estimates which moving vessels are heading
toward the river spot in front of home and roughly when they will pass,
and which ship is parked (anchored or moored) across from home.
"""
import asyncio
import datetime as dt
import json
import re
import math

LISTEN_SECONDS = 150
POS_MAX_AGE_MIN = 90
PARKED_KN = 0.5     # slower than this counts as stopped (anchored ships drift a little as they swing)
PARKED_MOVE_KM = 0.5  # moving further than this from where it stopped starts a new stop
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
                            callsign=body.get("CallSign"), eta=body.get("Eta"))
            else:
                # Only Class A position reports carry a navigational status (1 = at anchor, 5 = moored).
                ship.update(lat=meta.get("latitude"), lon=meta.get("longitude"), nav=body.get("NavigationalStatus"),
                            sog=body.get("Sog"), cog=body.get("Cog"), seen=meta.get("time_utc"))
    return ships


def listen(key):
    return asyncio.run(_listen(key))


def _pos_at(ship):
    """When the ship's position was last reported. A name-only (static data) message doesn't count."""
    if ship.get("pos_at"):
        return dt.datetime.fromisoformat(ship["pos_at"])
    m = re.match(r"(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d)", ship.get("seen") or "")
    return dt.datetime.fromisoformat(f"{m[1]}T{m[2]}+00:00") if m else None


def _track_stop(ship, now_utc):
    """Remember when and where a ship stopped, and which way it was going just before."""
    sog = ship.get("sog") or 0
    if sog < PARKED_KN or (ship.get("nav") in (1, 5) and sog < 1.5):
        stop = ship.get("stop")
        if not stop or _km(stop["lat"], stop["lon"], ship["lat"], ship["lon"]) > PARKED_MOVE_KM:
            # If we never saw it moving, it was already parked when we first heard it.
            ship["stop"] = {"lat": ship["lat"], "lon": ship["lon"], "since": now_utc.isoformat(),
                            "arrived_cog": ship.get("moving_cog"), "since_known": "moving_cog" in ship}
    else:
        ship.pop("stop", None)
        ship["moving_cog"] = ship.get("cog")


def merge(cache, fresh, now_utc):
    """Keep ship details (name, type) between runs; drop ships with no position for 6 hours
    (24 for parked ones, which can go quiet for a while at anchor)."""
    for mmsi, ship in fresh.items():
        cached = cache.setdefault(str(mmsi), {})
        old_dest = cached.get("destination")
        cached.update({k: v for k, v in ship.items() if v not in (None, "")})
        if old_dest and ship.get("destination") and ship["destination"] != old_dest:
            cached["prev_destination"] = old_dest  # often the port it just left
        cached["heard"] = now_utc.isoformat()
        if ship.get("lat") is not None:
            cached["pos_at"] = now_utc.isoformat()
            _track_stop(cached, now_utc)
    for mmsi in [m for m, s in cache.items()
                 if (_pos_at(s) or dt.datetime.fromisoformat(s["heard"])) < now_utc - dt.timedelta(hours=24 if s.get("stop") else 6)]:
        del cache[mmsi]
    return cache


# UN/LOCODEs ships commonly put in their AIS destination on the lower Columbia and across the Pacific.
PORTS = {
    "USPDX": "Portland", "USVAN": "Vancouver, WA", "USKAM": "Kalama", "USLOG": "Longview", "USLON": "Longview",
    "USLGV": "Longview", "USAST": "Astoria", "USSTH": "St. Helens", "USGHR": "Grays Harbor", "USSEA": "Seattle",
    "USTIW": "Tacoma", "USEVE": "Everett", "USOAK": "Oakland", "USLAX": "Los Angeles", "USLGB": "Long Beach",
    "USSFO": "San Francisco", "USPSC": "Pasco", "CAVAN": "Vancouver, BC", "CAPRR": "Prince Rupert",
    "CNSHA": "Shanghai", "CNNGB": "Ningbo", "CNQDG": "Qingdao", "CNTAO": "Qingdao", "CNTXG": "Tianjin",
    "CNDLC": "Dalian", "CNXMN": "Xiamen", "CNYTN": "Yantian", "CNNSA": "Nansha", "CNCFD": "Caofeidian",
    "KRPUS": "Busan", "KRINC": "Incheon", "KRUSN": "Ulsan", "KRKAN": "Gwangyang", "JPTYO": "Tokyo",
    "JPYOK": "Yokohama", "JPNGO": "Nagoya", "JPOSA": "Osaka", "JPUKB": "Kobe", "JPKSM": "Kashima",
    "JPCHB": "Chiba", "TWKHH": "Kaohsiung", "TWTXG": "Taichung", "PHMNL": "Manila", "VNSGN": "Ho Chi Minh City",
    "VNVUT": "Vung Tau", "THLCH": "Laem Chabang", "SGSIN": "Singapore", "IDJKT": "Jakarta", "MYPKG": "Port Klang",
    "AUSYD": "Sydney", "AUMEL": "Melbourne", "AUNTL": "Newcastle", "NZAKL": "Auckland", "MXZLO": "Manzanillo",
    "MXLZC": "Lázaro Cárdenas", "PAPAM": "Panama Canal", "PABLB": "Balboa", "CLSAI": "San Antonio", "PECLL": "Callao",
    "SAJED": "Jeddah", "EGSUZ": "Suez", "INMUN": "Mundra", "BDCGP": "Chittagong", "HKHKG": "Hong Kong",
}
COUNTRIES = {"US": "USA", "CA": "Canada", "CN": "China", "KR": "South Korea", "JP": "Japan", "TW": "Taiwan",
             "PH": "Philippines", "VN": "Vietnam", "TH": "Thailand", "SG": "Singapore", "ID": "Indonesia",
             "MY": "Malaysia", "AU": "Australia", "NZ": "New Zealand", "MX": "Mexico", "PA": "Panama",
             "CL": "Chile", "PE": "Peru", "IN": "India", "SA": "Saudi Arabia", "HK": "Hong Kong", "BD": "Bangladesh"}
LOCAL = ("OPS", "OPPS", "HARBOR", "NARBOR", "COL RIV", "COLUMBIA RIVER", "COL RIVER", "CR HARBOR")


def _place(code):
    code = code.strip().strip("-_,.").upper()
    squashed = re.sub(r"[\s_]", "", code)
    if squashed[:5] in PORTS:
        return PORTS[squashed[:5]]
    if any(k in code for k in LOCAL):
        return "Local river work"
    if re.fullmatch(r"[A-Z]{5}", squashed) and squashed[:2] in COUNTRIES:
        return f"{COUNTRIES[squashed[:2]]} ({squashed})"
    if squashed in ("LGV", "PDX", "VAN", "KAM", "AST"):
        return PORTS["US" + squashed if squashed != "LGV" else "USLGV"]
    words = re.sub(r"[_,]+", ", ", code).strip(", ")
    if not (words and re.search(r"[A-Z]{3}", words)):
        return None
    words = re.sub(r",\s*(USA|US)$", "", words).title()
    return re.sub(r", (Or|Wa)\b", lambda m: ", " + m.group(1).upper(), words)


def route(destination):
    """Turn an AIS destination like 'USKAM-CNQDG', 'US PDX' or 'PORTLAND,OR' into (from, to)."""
    d = (destination or "").strip().upper()
    if not d or "^" in d or d in ("--", "0", "NOT AVAILABLE", "NONE"):  # ^ marks coded Coast Guard fields
        return None, None
    if any(k in d for k in LOCAL):
        return None, "Local river work"
    for sep in (">", " - ", "-", "/"):
        if sep in d and not d.startswith(sep):
            a, b = d.split(sep, 1)
            fa, tb = _place(a), _place(b)
            if fa and tb and fa != tb:
                return fa, tb
    return None, _place(d)


def approaching(cache, home_lat, home_lon, now_utc):
    """Ships moving toward home, soonest first, plus ones passing right now."""
    out = []
    for ship in cache.values():
        pos_at = _pos_at(ship)
        # Projecting a position forward gets unreliable fast on a winding river, so skip stale ones.
        if ship.get("lat") is None or not pos_at or now_utc - pos_at > dt.timedelta(minutes=POS_MAX_AGE_MIN):
            continue
        km = _km(ship["lat"], ship["lon"], home_lat, home_lon)
        sog = ship.get("sog") or 0
        if ship.get("stop") and sog < PARKED_KN:
            continue  # parked, shown in its own box
        heading_home = abs((_bearing(ship["lat"], ship["lon"], home_lat, home_lon) - (ship.get("cog") or 0) + 180) % 360 - 180) < 50
        if km < 1.5:
            eta_min = 0
        elif sog >= 2 and heading_home:
            # River distance runs about 1.3x the straight line on this stretch.
            eta_min = round(km * 1.3 / (sog * 1.852) * 60)
        else:
            continue
        eta_min -= round((now_utc - pos_at).total_seconds() / 60)
        if eta_min < -10 or eta_min > 360:
            continue
        code = ship.get("type")
        # The Columbia runs north-west past the island toward the ocean.
        if eta_min <= 0:
            upriver = 90 < (ship.get("cog") or 0) < 270
        else:
            upriver = ship["lat"] > home_lat  # north of home and closing in means heading upriver
        direction = "Headed toward Portland" if upriver else "Headed toward Astoria"
        origin, dest = route(ship.get("destination"))
        if not origin:
            # AIS only carries the destination, so infer where it came from by which way it's going.
            origin = "the ocean or a downriver port" if upriver else "Portland or Vancouver"
            origin_guess = True
        else:
            origin_guess = False
        out.append({
            "direction": direction,
            "name": (ship.get("name") or f"MMSI {ship['mmsi']}").title(),
            "type": type_name(code) if code else "Vessel",
            "destination": dest,
            "origin": origin, "origin_guess": origin_guess,
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


# Ports above home (toward Portland); everything else on a ship's route is downriver or overseas.
UPRIVER = ("Portland", "Vancouver, WA", "Pasco", "Rivergate", "Terminal", "Tic Vancouver")
COMPASS = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]


def _eta(raw, now_utc):
    """AIS ETA has month, day, hour and minute in UTC but no year: take the nearest sensible one."""
    if not isinstance(raw, dict) or not raw.get("Month") or not raw.get("Day") or raw.get("Hour", 24) > 23 or raw.get("Minute", 60) > 59:
        return None
    for year in (now_utc.year, now_utc.year + 1, now_utc.year - 1):
        try:
            when = dt.datetime(year, raw["Month"], raw["Day"], raw["Hour"], raw["Minute"], tzinfo=dt.timezone.utc)
        except ValueError:
            return None
        if -60 <= (when - now_utc).days <= 300:
            return when
    return None


def _is_up(place):
    return bool(place) and any(place.startswith(p) for p in UPRIVER)


def _big(ship):
    code, length = ship.get("type") or 0, ship.get("length_m") or 0
    return 70 <= code < 90 or length >= 80


def parked(cache, home_lat, home_lon, now_utc, radius_km=5):
    """The ship stopped across from home: the nearest big ship parked within radius_km, or else
    any vessel parked within 1.5 km. Returns (ship, other big ships parked nearby)."""
    found = []
    for ship in cache.values():
        stop, pos_at = ship.get("stop"), _pos_at(ship)
        if not stop or ship.get("lat") is None or (ship.get("sog") or 0) >= 1.5 or not pos_at:
            continue
        km = _km(ship["lat"], ship["lon"], home_lat, home_lon)
        if km <= radius_km and (_big(ship) or km <= 1.5):
            found.append((not _big(ship), km, ship))
    if not found:
        return None, []
    found.sort(key=lambda f: (f[0], f[1]))
    _, km, ship = found[0]
    stop, code = ship["stop"], ship.get("type")
    origin, dest = route(ship.get("destination"))
    origin_how = "ais" if origin else None
    if not origin and ship.get("prev_destination"):
        prev = route(ship["prev_destination"])[1]
        if prev and prev != dest and prev != "Local river work":
            origin, origin_how = prev, "previous destination"
    if not origin and stop.get("arrived_cog") is not None:
        # The river runs north-west past the island toward the ocean.
        up = 90 < stop["arrived_cog"] < 270
        origin, origin_how = ("the ocean or a downriver port" if up else "Portland or Vancouver"), "direction"
    if not origin and dest and dest != "Local river work":
        # Headed upriver means it came in from the sea; headed down or overseas means it is leaving Portland.
        origin, origin_how = ("the ocean or a downriver port" if _is_up(dest) else "Portland or Vancouver"), "destination"
    eta = _eta(ship.get("eta"), now_utc)
    nav = ship.get("nav")
    others = [{"name": (s.get("name") or f"MMSI {s['mmsi']}").title(), "km": round(k, 1)}
              for small, k, s in found[1:] if not small][:3]
    return {
        "name": (ship.get("name") or f"MMSI {ship['mmsi']}").title(),
        "type": type_name(code) if code else "Vessel",
        "length_m": ship.get("length_m"),
        "status": "At anchor" if nav == 1 else "Moored" if nav == 5 else "Stopped",
        "km": round(km, 1),
        "side": COMPASS[round(_bearing(home_lat, home_lon, ship["lat"], ship["lon"]) / 45) % 8],
        "since": stop["since"], "since_known": stop.get("since_known", False),
        "origin": origin, "origin_how": origin_how,
        "destination": dest,
        "dest_upriver": _is_up(dest),
        "eta_utc": eta.isoformat() if eta and eta > now_utc else None,
        "big": _big(ship),
        "last_heard": pos_at.isoformat(),
        "url": f"https://www.vesselfinder.com/vessels/details/{ship['mmsi']}",
    }, others
