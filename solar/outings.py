"""Reasons to go outside, refreshed every day: whether the mountains are out, the mushroom outlook in the
forests near Portland, whales off the north coast, new bars and restaurants opening around town, and
Wikipedia's picture of the day.

Weather comes from Open-Meteo, whales from iNaturalist sightings, openings from Eater Portland and Google
News, and the picture from Wikipedia's featured feed. Each card also carries something picked by the date
(a fact, a spot or a species) so it reads differently every morning even when the data hasn't moved.
"""
import datetime as dt
import email.utils
import html
import json
import math
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

UA = {"User-Agent": "solar-dashboard/1.0 (personal home dashboard; github.com/phallpdx/solar-dashboard)"}
TZ = "America/Los_Angeles"
HOME_TZ = ZoneInfo(TZ)


def _get(url, as_json=True):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        body = r.read()
    return json.loads(body) if as_json else body


def _pick(items, day, salt=0):
    return items[(day.toordinal() + salt) % len(items)] if items else None


def _text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# ---------------------------------------------------------------- weather for the mountains and forests

PEAKS = [
    {"id": "hood", "name": "Mount Hood", "lat": 45.3736, "lon": -121.6959, "feet": 11249, "facts": [
        "Oregon's tallest peak, and a stratovolcano that last erupted in the 1790s, just before Lewis and Clark arrived.",
        "Timberline Lodge on its south side was built by WPA crews in the 1930s and stood in for the Overlook Hotel in The Shining.",
        "Twelve named glaciers cover its upper slopes. Palmer Snowfield keeps skiing going into summer.",
        "Climbers summit it about 10,000 times a year, which makes it one of the most climbed glaciated peaks in the world.",
        "The Multnomah people called it Wy'east. The name Hood comes from a British admiral who never saw it.",
        "It is about 50 miles away, so on a clear day you are looking through a lot of air. Morning light shows the most detail.",
    ]},
    {"id": "helens", "name": "Mount St. Helens", "lat": 46.1912, "lon": -122.1944, "feet": 8363, "facts": [
        "It lost about 1,300 feet of its summit in the May 18, 1980 eruption. The flat top you see is the crater rim.",
        "A new glacier, Crater Glacier, has grown inside the crater since 1980. It is one of the few growing glaciers anywhere.",
        "It erupted again from 2004 to 2008 and built a new lava dome inside the crater.",
        "On calm mornings after the 1980 eruption, ash reached Portland. Today the volcano is quiet and closely monitored.",
        "Spirit Lake below it still holds a floating mat of trees knocked down by the blast in 1980.",
        "Before 1980 it was so symmetrical that people called it the Mount Fuji of America.",
    ]},
    {"id": "adams", "name": "Mount Adams", "lat": 46.2024, "lon": -121.4906, "feet": 12276, "facts": [
        "Washington's second-tallest peak. It is broad and rounded, so it looks smaller than it is.",
        "Its South Spur route is one of the easiest ways up a 12,000-foot peak in the lower 48. No technical climbing is needed in summer.",
        "Huckleberry fields on its flanks have been a Yakama gathering place for thousands of years.",
        "It is about 70 miles away, so it only shows on the clearest days. Seeing it counts as a good-sky day.",
        "Volcanic gases have rotted parts of its summit rock to clay, and big landslides have come off the southwest face.",
    ]},
]
FORESTS = [
    {"id": "coast", "name": "Coast Range (Tillamook State Forest)", "lat": 45.62, "lon": -123.37},
    {"id": "cascades", "name": "Cascade foothills (Mt. Hood National Forest)", "lat": 45.30, "lon": -122.02},
]


def weather(home_lat, home_lon):
    """One Open-Meteo call for home, the three peaks and two forests: two weeks back and three days ahead."""
    spots = [(home_lat, home_lon)] + [(p["lat"], p["lon"]) for p in PEAKS] + [(f["lat"], f["lon"]) for f in FORESTS]
    data = _get("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
        "latitude": ",".join(str(a) for a, _ in spots), "longitude": ",".join(str(b) for _, b in spots),
        "hourly": "cloud_cover,cloud_cover_low,visibility,soil_temperature_6cm,temperature_2m",
        "daily": "precipitation_sum,temperature_2m_min,sunrise,sunset",
        "past_days": 14, "forecast_days": 3, "timezone": TZ,
        "temperature_unit": "fahrenheit", "precipitation_unit": "inch"}))
    if isinstance(data, dict):
        data = [data]
    if len(data) != len(spots):
        raise RuntimeError(f"Open-Meteo returned {len(data)} places, expected {len(spots)}")
    return {"home": data[0], "peaks": data[1:1 + len(PEAKS)], "forests": data[1 + len(PEAKS):]}


def _compass(lat1, lon1, lat2, lon2):
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2), math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)))
    names = ["north", "north-northeast", "northeast", "east-northeast", "east", "east-southeast", "southeast", "south-southeast",
             "south", "south-southwest", "southwest", "west-southwest", "west", "west-northwest", "northwest", "north-northwest"]
    miles = 3958.8 * math.acos(min(1, math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)))
    return names[round(((brg + 360) % 360) / 22.5) % 16], round(miles)


def _windows(hours):
    """[(start, end)] runs of consecutive clear hours."""
    out = []
    for h in hours:
        if out and h == out[-1][1] + 1:
            out[-1][1] = h
        else:
            out.append([h, h])
    return [tuple(w) for w in out]


def mountains(w, home_lat, home_lon, now_local):
    """For today and tomorrow, the daylight hours each peak should be visible from home."""
    home = w["home"]
    hh = home["hourly"]
    times = hh["time"]
    sun = {d: (rise[11:13], sets[11:13]) for d, rise, sets in zip(home["daily"]["time"], home["daily"]["sunrise"], home["daily"]["sunset"])}
    days = [now_local.date(), now_local.date() + dt.timedelta(days=1)]
    out = []
    for peak, pw in zip(PEAKS, w["peaks"]):
        pc = pw["hourly"]["cloud_cover"]
        direction, miles = _compass(home_lat, home_lon, peak["lat"], peak["lon"])
        entry = {"id": peak["id"], "name": peak["name"], "feet": peak["feet"], "look": direction, "miles": miles, "days": []}
        for d in days:
            iso = d.isoformat()
            rise, sets = (int(x) for x in sun.get(iso, ("07", "18")))
            clear = []
            for i, t in enumerate(times):
                if not t.startswith(iso):
                    continue
                hour = int(t[11:13])
                if not rise <= hour <= sets:
                    continue
                low, total, vis = hh["cloud_cover_low"][i], hh["cloud_cover"][i], hh["visibility"][i]
                if None in (low, total, vis, pc[i]):
                    continue
                # Low cloud or haze at home hides everything; cloud over the peak hides the peak.
                if low <= 25 and total <= 70 and vis >= 30000 and pc[i] <= 35:
                    clear.append(hour)
            entry["days"].append({"date": iso, "hours": clear, "windows": _windows(clear)})
        hour_now = now_local.hour
        entry["out_now"] = hour_now in entry["days"][0]["hours"]
        out.append(entry)
    return out


# ---------------------------------------------------------------- mushrooms

# (name, months, soil temperature range in °F, inches of rain wanted over two weeks, where, how to know it)
SPECIES = [
    ("Pacific golden chanterelle", (9, 10, 11), (45, 62), 1.0, "coast",
     "Under second-growth Douglas fir and hemlock.",
     "False gills: blunt, forking ridges that run down the stem. The flesh tears like string cheese and smells faintly of apricot."),
    ("King bolete (porcini)", (9, 10), (50, 65), 0.8, "coast",
     "Under Sitka spruce near the coast, and in the Cascades at middle elevations.",
     "A sponge of pores, not gills, under a brown bun-shaped cap, on a fat white stem with a fine net pattern near the top."),
    ("Lobster mushroom", (8, 9, 10), (50, 65), 0.8, "cascades",
     "Where chanterelles and russulas grow, under conifers.",
     "Bright orange-red and crusty, with no real gills. It is a mold that has taken over another mushroom."),
    ("Matsutake", (10, 11), (45, 58), 1.0, "cascades",
     "In sandy soil under lodgepole pine and true firs. Mostly the Cascades.",
     "White with a thick ring on the stem. The smell is the giveaway: spicy and cinnamon-like."),
    ("Hedgehog", (10, 11, 12, 1), (38, 55), 1.0, "coast",
     "In mossy conifer forest, often near chanterelles.",
     "Little spines instead of gills under a buff or orange cap. No poisonous lookalike has spines like these."),
    ("Yellowfoot (winter chanterelle)", (11, 12, 1, 2), (35, 50), 1.5, "coast",
     "On rotting logs and moss in wet coastal forest.",
     "Small, with a brown cap, a hollow yellow stem and false gills like a chanterelle's. It often grows in big troops."),
    ("Cauliflower mushroom", (9, 10, 11), (45, 60), 0.8, "cascades",
     "At the base of Douglas fir trees.",
     "A big cream-colored mass of flat curly lobes, like a pile of egg noodles."),
    ("Morel", (4, 5, 6), (45, 60), 0.5, "cascades",
     "In the Cascades in spring, especially in the year after a forest fire.",
     "A honeycomb cap that is hollow all the way through when you slice it lengthwise. False morels are stuffed with cottony tissue."),
]
FORAGE_TIPS = [
    "Never eat a wild mushroom unless you're sure what it is. The Oregon Mycological Society holds ID sessions, and its fall show is a great place to learn.",
    "Bring a basket or a mesh bag, not plastic, so spores fall as you walk and the mushrooms stay firm.",
    "Cut or twist each mushroom at the base and leave the small ones to grow. Most patches come back year after year.",
    "Mt. Hood National Forest asks for a free personal-use mushroom permit, and state forests have daily gallon limits. Check before you go.",
    "Hunting season is on in fall. Wear blaze orange in the woods.",
    "Write down where you found a good patch. The same trees will fruit again after the next soaking rain.",
    "Death caps have turned up in the Portland area, often under planted oaks and hornbeams in town. Leave white-gilled mushrooms with a cup at the base alone.",
]


def _forest_readings(fw, today):
    d = fw["daily"]
    past = [(t, p, m) for t, p, m in zip(d["time"], d["precipitation_sum"], d["temperature_2m_min"]) if t <= today.isoformat()]
    rain14 = sum(p or 0 for _, p, _ in past[-14:])
    rain3 = sum(p or 0 for _, p, _ in past[-3:])
    frosts = sum(1 for _, _, m in past[-5:] if m is not None and m <= 30)
    h = fw["hourly"]
    now_key = dt.datetime.now(HOME_TZ).strftime("%Y-%m-%dT%H")
    soil = [s for t, s in zip(h["time"], h["soil_temperature_6cm"]) if s is not None and t[:13] <= now_key][-72:]
    ahead = sum(p or 0 for t, p in zip(d["time"], d["precipitation_sum"]) if t > today.isoformat())
    return {"rain14": round(rain14, 2), "rain3": round(rain3, 2), "frost_nights": frosts,
            "soil_f": round(sum(soil) / len(soil)) if soil else None, "rain_ahead": round(ahead, 2)}


def mushrooms(w, today):
    """Which edible mushrooms are in season, and whether the forests are wet and warm enough for them now."""
    readings = {f["id"]: {"name": f["name"], **_forest_readings(fw, today)} for f, fw in zip(FORESTS, w["forests"])}
    species = []
    for name, months, (lo, hi), rain, where, habitat, tell in SPECIES:
        if today.month not in months:
            continue
        r = readings[where]
        soil_ok = r["soil_f"] is not None and lo <= r["soil_f"] <= hi
        wet = r["rain14"] >= rain
        frozen = r["frost_nights"] >= 2 and lo >= 45
        score = (2 if soil_ok else 0) + (2 if wet else 1 if r["rain14"] >= rain / 2 else 0) - (2 if frozen else 0)
        status = "Good" if score >= 4 else "Possible" if score >= 2 else "Slow"
        why = []
        why.append(f"{r['rain14']:.1f} in of rain in two weeks" + ("" if wet else f", and it likes {rain:.1f}+"))
        if r["soil_f"] is not None:
            why.append(f"soil {r['soil_f']}°F" + ("" if soil_ok else f", and it likes {lo}–{hi}°F"))
        if frozen:
            why.append("recent frosts")
        species.append({"name": name, "status": status, "score": score, "where": readings[where]["name"],
                        "habitat": habitat, "tell": tell, "why": "; ".join(why)})
    species.sort(key=lambda s: -s["score"])
    return {"forests": list(readings.values()), "species": species}


# ---------------------------------------------------------------- whales

WHALE_SPOTS = [
    ("Ecola State Park", "Look north from the Ecola Point viewpoint, toward Tillamook Rock lighthouse."),
    ("Cape Falcon (Oswald West)", "Walk the 2.5-mile trail out to the headland. Whales often pass close below the cliff."),
    ("Neahkahnie Mountain viewpoints", "The pullouts on US 101 sit 700 feet above the water, which makes spouts easy to spot."),
    ("Cape Meares", "From the lighthouse overlook. Bring binoculars, because the view is wide."),
    ("Cape Lookout", "Hike the 2.4 miles to the tip of the cape. It reaches farther out to sea than almost anywhere on the coast."),
    ("Tillamook Head", "From the Clatsop Loop trail above Indian Beach."),
    ("Depoe Bay Whale Watching Center", "A bit of a drive, but summer gray whales feed right in the bay and volunteers help you find them."),
]
WHALE_FACTS = [
    "Gray whales make one of the longest migrations of any mammal, about 10,000 to 12,000 miles round trip between Alaska and Baja.",
    "Look for the heart-shaped spout. A gray whale's blow is a low V or heart, about 10 to 15 feet tall.",
    "About 200 gray whales skip the full trip and spend summer and fall feeding off Oregon. They are called the Pacific Coast Feeding Group.",
    "The best viewing is in the morning with the sun behind you and the wind down. Whitecaps hide spouts.",
    "A gray whale feeds by rolling on its side and sucking up mud from the bottom, then straining out shrimp-like amphipods.",
    "During the winter migration's peak, up to 30 whales an hour pass the Oregon coast.",
    "Orcas come by now and then, usually transients hunting seals and sea lions, and sometimes gray whale calves in spring.",
    "Humpbacks have been showing up more often off Oregon in summer and fall. Look for long white flippers and high, arching dives.",
]


def whale_season(day):
    md = (day.month, day.day)
    if md >= (12, 15) or md <= (1, 31):
        return {"phase": "Winter migration", "level": "peak",
                "text": "Gray whales are heading south to Baja, and this is the busiest stretch of the year. "
                        "Oregon State Parks volunteers staff 'Whale Watching Spoken Here' sites the week after Christmas."}
    if (3, 15) <= md <= (6, 15):
        return {"phase": "Spring migration", "level": "good",
                "text": "Gray whales are heading back north, with mothers and calves passing close to shore into May and June. "
                        "Volunteers staff 'Whale Watching Spoken Here' sites during spring break week."}
    if (6, 16) <= md <= (10, 31):
        return {"phase": "Summer feeding", "level": "some",
                "text": "The summer resident gray whales are feeding near shore, often in coves and near rocky reefs."}
    if (11, 1) <= md <= (12, 14):
        days = (dt.date(day.year, 12, 15) - day).days
        return {"phase": "Early winter", "level": "some",
                "text": f"The first southbound gray whales are passing. The migration's peak starts in about {days} days."}
    return {"phase": "Between migrations", "level": "low",
            "text": "Quiet between migrations, but a few stragglers and resident gray whales still pass."}


def whales(today):
    """Whale sightings on the north and central Oregon coast in the last three weeks, from iNaturalist."""
    data = _get("https://api.inaturalist.org/v1/observations?" + urllib.parse.urlencode({
        "taxon_name": "Cetacea", "swlat": 43.9, "swlng": -124.8, "nelat": 46.3, "nelng": -123.75,
        "d1": (today - dt.timedelta(days=21)).isoformat(), "order_by": "observed_on", "order": "desc",
        "per_page": 30, "photos": "true"}))
    out = []
    for o in data.get("results") or []:
        t = o.get("taxon") or {}
        photo = ((o.get("photos") or [{}])[0].get("url") or "").replace("square", "medium") or None
        out.append({"what": (t.get("preferred_common_name") or t.get("name") or "Whale").capitalize(),
                    "date": o.get("observed_on"), "where": o.get("place_guess"), "url": o.get("uri"), "photo": photo})
    return {"sightings": out[:12], "count": len(out)}


# ---------------------------------------------------------------- openings around town

OPENING = re.compile(r"\b(open(s|ing|ed)?|now open|debut\w*|coming soon|to open|soft open\w*|new (bar|restaurant|cafe|bakery|brewery|spot|location)|"
                     r"first look|grand opening|reopen\w*)\b", re.I)
SHUT = re.compile(r"\b(clos(e|es|ed|ing|ure)|shutter\w*|final (day|service)|last call|goodbye)\b", re.I)
FOOD = re.compile(r"\b(restaurant|bar|cafe|café|bakery|brewery|brewpub|taproom|pizz\w*|taco\w*|ramen|sushi|coffee|wine|cocktail\w*|"
                  r"diner|deli|cart|pod|kitchen|eatery|bistro|tavern|pub|food hall|dumpling\w*|noodle\w*|bbq|barbecue|ice cream|donut\w*|"
                  r"izakaya|lounge|chef)\b", re.I)


def _feed(url):
    root = ET.fromstring(_get(url, as_json=False))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items = []
    for it in root.iter("item"):
        src = it.findtext("source")
        title = _text(it.findtext("title"))
        if src and title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        when = it.findtext("pubDate")
        items.append({"title": title, "url": it.findtext("link"), "source": src,
                      "summary": _text(it.findtext("description"))[:240] or None,
                      "date": email.utils.parsedate_to_datetime(when).date().isoformat() if when else None})
    for e in root.iter("{http://www.w3.org/2005/Atom}entry"):
        link = e.find("a:link[@rel='alternate']", ns)
        if link is None:
            link = e.find("a:link", ns)
        when = e.findtext("a:published", namespaces=ns) or e.findtext("a:updated", namespaces=ns)
        items.append({"title": _text(e.findtext("a:title", namespaces=ns)), "url": link.get("href") if link is not None else None,
                      "source": None, "summary": _text(e.findtext("a:summary", namespaces=ns) or e.findtext("a:content", namespaces=ns))[:240] or None,
                      "date": (when or "")[:10] or None})
    return items


def openings(today):
    """New and coming-soon bars, restaurants and cafes around Portland from the last month."""
    q = 'Portland Oregon (restaurant OR bar OR cafe OR bakery OR brewery) (opening OR "now open" OR opens OR "coming soon") when:30d'
    sources = [("Eater Portland", "https://pdx.eater.com/rss/index.xml"),
               (None, "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "en-US", "gl": "US", "ceid": "US:en"}))]
    found, seen, errors = [], set(), []
    for name, url in sources:
        try:
            items = _feed(url)
        except Exception as e:
            errors.append(f"{name or 'Google News'}: {e}")
            continue
        for x in items:
            words = x["title"]
            if not (OPENING.search(words) and FOOD.search(words + " " + (x["summary"] or ""))) or SHUT.search(words):
                continue
            if x["date"] and (today - dt.date.fromisoformat(x["date"])).days > 35:
                continue
            key = re.sub(r"[^a-z0-9]", "", words.lower())[:50]
            if key in seen:
                continue
            seen.add(key)
            found.append(x | {"source": x["source"] or name})
    if not found and errors:
        raise RuntimeError("; ".join(errors))
    found.sort(key=lambda x: x["date"] or "", reverse=True)
    return found[:15]


# ---------------------------------------------------------------- picture of the day

def wiki_picture(day):
    """Wikipedia's featured picture of the day."""
    data = _get(f"https://en.wikipedia.org/api/rest_v1/feed/featured/{day.year}/{day.month:02d}/{day.day:02d}")
    img = data.get("image") or {}
    if not img:
        return None
    thumb = (img.get("thumbnail") or {}).get("source") or (img.get("image") or {}).get("source")
    return {"date": day.isoformat(), "title": re.sub(r"^File:|\.\w+$", "", img.get("title") or "").replace("_", " "),
            "image": thumb, "full": (img.get("image") or {}).get("source"),
            "caption": _text((img.get("description") or {}).get("html") or (img.get("description") or {}).get("text")),
            "artist": _text((img.get("artist") or {}).get("text") or (img.get("artist") or {}).get("html")) or None,
            "url": img.get("file_page")}


# ---------------------------------------------------------------- daily rotation

def rotation(day, mush):
    """What changes every day on its own, even when the data doesn't: a fact, a spot, a species, a tip."""
    in_season = (mush or {}).get("species") or []
    return {
        "date": day.isoformat(),
        "peak_fact": {p["name"]: _pick(p["facts"], day, i) for i, p in enumerate(PEAKS)},
        "featured_peak": _pick([p["name"] for p in PEAKS], day),
        "mushroom": _pick([s["name"] for s in in_season], day),
        "forage_tip": _pick(FORAGE_TIPS, day, 3),
        "whale_spot": dict(zip(("name", "how"), _pick(WHALE_SPOTS, day, 1))),
        "whale_fact": _pick(WHALE_FACTS, day, 2),
        "whale_season": whale_season(day),
        "opening_pick": day.toordinal(),
    }
