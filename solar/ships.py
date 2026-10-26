"""Ships heading past home on the Columbia, from live AIS radio data (aisstream.io).

Each run listens for a couple of minutes to every ship transmitting between
Longview and Portland, then estimates which moving vessels are heading
toward the river spot in front of home and roughly when they will pass.
"""
import asyncio
import datetime as dt
import json
import re
import math

LISTEN_SECONDS = 150
POS_MAX_AGE_MIN = 90
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


def _pos_at(ship):
    """When the ship's position was last reported. A name-only (static data) message doesn't count."""
    if ship.get("pos_at"):
        return dt.datetime.fromisoformat(ship["pos_at"])
    m = re.match(r"(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d)", ship.get("seen") or "")
    return dt.datetime.fromisoformat(f"{m[1]}T{m[2]}+00:00") if m else None


def merge(cache, fresh, now_utc):
    """Keep ship details (name, type) between runs; drop ships with no position for 6 hours."""
    for mmsi, ship in fresh.items():
        cached = cache.setdefault(str(mmsi), {})
        cached.update({k: v for k, v in ship.items() if v not in (None, "")})
        cached["heard"] = now_utc.isoformat()
        if ship.get("lat") is not None:
            cached["pos_at"] = now_utc.isoformat()
    cutoff = now_utc - dt.timedelta(hours=6)
    for mmsi in [m for m, s in cache.items() if (_pos_at(s) or dt.datetime.fromisoformat(s["heard"])) < cutoff]:
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
