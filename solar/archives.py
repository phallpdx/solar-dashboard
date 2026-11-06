"""Free archives for the "of the day" shelf: a public-domain artwork, an old photograph of Portland from the
Library of Congress and a live concert recorded in Portland on the Internet Archive."""
import datetime as dt
import hashlib
import json
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}


def _get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _pick(items, day, salt=""):
    """The same item all day, a different one tomorrow, without a counter to keep."""
    if not items:
        return None
    n = int(hashlib.sha256(f"{day}{salt}".encode()).hexdigest()[:8], 16)
    return items[n % len(items)]


# ---------------------------------------------------------------- artwork of the day (Art Institute of Chicago, CC0)

ART_QUERIES = ["landscape", "river", "garden", "winter", "seascape", "forest", "night", "harvest", "mountain", "rain", "birds", "boats"]


def artwork(day):
    """A public-domain painting or print from the Art Institute of Chicago, matched loosely to the season."""
    q = ART_QUERIES[(day.month * 3 + day.day) % len(ART_QUERIES)]
    url = "https://api.artic.edu/api/v1/artworks/search?" + urllib.parse.urlencode(
        {"q": q, "query[term][is_public_domain]": "true", "fields": "id,title,artist_display,date_display,image_id,thumbnail,medium_display,place_of_origin",
         "limit": 40})
    data = _get(url)
    items = [a for a in data.get("data") or [] if a.get("image_id")]
    a = _pick(items, day, "art")
    if not a:
        raise RuntimeError("no artworks with images")
    iiif = (data.get("config") or {}).get("iiif_url") or "https://www.artic.edu/iiif/2"
    return {"title": a.get("title"), "artist": (a.get("artist_display") or "").split("\n")[0], "when": a.get("date_display"),
            "medium": a.get("medium_display"), "query": q,
            "image": f"{iiif}/{a['image_id']}/full/843,/0/default.jpg",
            "url": f"https://www.artic.edu/artworks/{a['id']}", "source": "Art Institute of Chicago"}


# ---------------------------------------------------------------- old Portland (Library of Congress)

def old_portland(day):
    """A photograph or print of Portland, Oregon from the Library of Congress, a different one each day."""
    url = "https://www.loc.gov/photos/?" + urllib.parse.urlencode({"q": "portland oregon", "dates": "1850/1979", "fo": "json", "c": 100})
    data = _get(url)
    items = []
    for r in data.get("results") or []:
        imgs = r.get("image_url") or []
        if isinstance(imgs, str):
            imgs = [imgs]
        imgs = [i for i in imgs if "#" in i or i.endswith((".jpg", ".gif", ".png"))]
        year = (r.get("date") or "")[:4]
        if not imgs or not year.isdigit() or int(year) >= 1980:  # old Portland, not last year's protest
            continue
        big = max(imgs, key=lambda i: int(re.search(r"w=(\d+)", i).group(1)) if re.search(r"w=(\d+)", i) else 0)
        items.append({"title": r.get("title"), "when": (r.get("date") or "")[:10], "year": (r.get("date") or "")[:4],
                      "image": big.split("#")[0], "url": r.get("url") or r.get("id"),
                      "subjects": [s for s in (r.get("subject") or []) if isinstance(s, str)][:4]})
    item = _pick(items, day, "loc")
    if not item:
        raise RuntimeError("LOC returned no Portland pictures")
    return {**item, "source": "Library of Congress"}


# ---------------------------------------------------------------- a Portland show (Internet Archive, Live Music Archive)

def portland_show(day):
    """A live recording made at a Portland venue, from the Internet Archive's Live Music Archive."""
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        {"q": "collection:etree AND venue:(portland)", "fl[]": ["identifier", "title", "date", "creator", "venue"], "rows": 300, "output": "json"}, doseq=True)
    docs = (_get(url).get("response") or {}).get("docs") or []
    docs = [d for d in docs if d.get("date") and d.get("title")]
    d = _pick(docs, day, "show")
    if not d:
        raise RuntimeError("no Portland shows on the Live Music Archive")
    # Many entries carry no creator or venue field, but the title follows "Artist Live at Venue on YYYY-MM-DD".
    m = re.match(r"^(.*?)\s+Live at (.*?)\s+on \d{4}-\d{2}-\d{2}", d["title"])
    artist = d.get("creator") if isinstance(d.get("creator"), str) else (d.get("creator") or [None])[0]
    return {"title": d["title"], "when": (d.get("date") or "")[:10], "artist": artist or (m.group(1) if m else None),
            "venue": d.get("venue") or (m.group(2) if m else None), "url": f"https://archive.org/details/{d['identifier']}",
            "embed": f"https://archive.org/embed/{d['identifier']}", "count": len(docs), "source": "Internet Archive"}
