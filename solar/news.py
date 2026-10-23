"""A/V and tech headlines, and the latest hands-on product reviews, from public RSS feeds."""
import datetime as dt
import email.utils
import html
import re
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (solar-dashboard personal dashboard)"}

# Each source lists feed URLs to try in order.
NEWS_SOURCES = [
    ("The Verge", ["https://www.theverge.com/rss/index.xml"]),
    ("Ars Technica", ["https://feeds.arstechnica.com/arstechnica/index"]),
    ("Engadget", ["https://www.engadget.com/rss.xml"]),
    ("What Hi-Fi?", ["https://www.whathifi.com/feeds.xml", "https://www.whathifi.com/feeds/all"]),
    ("FlatpanelsHD", ["https://www.flatpanelshd.com/rss/news.xml", "https://www.flatpanelshd.com/rss.php"]),
    ("Sound & Vision", ["https://www.soundandvision.com/rss.xml", "https://www.soundandvision.com/content/feed"]),
    ("Audioholics", ["https://www.audioholics.com/rss.xml", "https://www.audioholics.com/news/RSS"]),
    ("Digital Trends", ["https://www.digitaltrends.com/feed/"]),
]
REVIEW_SOURCES = [
    ("The Verge", ["https://www.theverge.com/rss/reviews/index.xml"]),
    ("What Hi-Fi?", ["https://www.whathifi.com/reviews/feeds.xml", "https://www.whathifi.com/feeds.xml"]),
    ("Engadget", ["https://www.engadget.com/reviews/rss.xml"]),
    ("Sound & Vision", ["https://www.soundandvision.com/rss.xml"]),
    ("TechRadar", ["https://www.techradar.com/reviews/feeds.xml", "https://www.techradar.com/feeds.xml"]),
    ("Tom's Guide", ["https://www.tomsguide.com/reviews/feeds.xml", "https://www.tomsguide.com/feeds.xml"]),
    ("Digital Trends", ["https://www.digitaltrends.com/product-reviews/feed/"]),
    ("CNET", ["https://www.cnet.com/rss/reviews/"]),
    ("Wired", ["https://www.wired.com/feed/tag/review/latest/rss", "https://www.wired.com/feed/category/gear/latest/rss"]),
    ("PCMag", ["https://www.pcmag.com/feeds/rss/reviews", "https://www.pcmag.com/feeds/rss/latest"]),
]
PER_SOURCE = 6  # keep one busy site from filling the whole list
AV_WORDS = re.compile(r"\b(tv|oled|qled|mini-?led|projector|soundbar|speaker|headphone|earbud|airpods|amp|"
                      r"amplifier|receiver|av|a/v|hdmi|dolby|atmos|imax|streaming|turntable|vinyl|hi-?fi|"
                      r"audio|sonos|bose|lg|samsung|sony|panasonic|hisense|tcl|roku|apple tv|4k|8k|hdr)\b", re.I)
STOP = set("the a an and or of to in on for with is are was be by at from as it its this that new how why what "
           "you your can will just now more than over after into about".split())


def _text(node):
    return html.unescape(re.sub(r"<[^>]+>", " ", node or "")).strip()


def _first_img(raw):
    m = re.search(r'<img[^>]+src="([^"]+)"', raw or "")
    return html.unescape(m.group(1)) if m else None


def _parse(xml_bytes):
    root = ET.fromstring(xml_bytes.lstrip(b"\xef\xbb\xbf \r\n\t"))
    ns = {"a": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/"}
    items = []
    for it in root.iter("item"):
        date = it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")
        # Elements with no children are falsy, so compare with None explicitly.
        thumb = it.find("media:thumbnail", ns)
        if thumb is None:
            thumb = it.find("media:content", ns)
        enc = it.find("enclosure")
        body = it.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or it.findtext("description")
        items.append({"title": _text(it.findtext("title")), "url": (it.findtext("link") or "").strip(),
                      "date": date, "summary": _text(it.findtext("description"))[:240],
                      "author": _text(it.findtext("{http://purl.org/dc/elements/1.1/}creator") or it.findtext("author")),
                      "image": (thumb.get("url") if thumb is not None else None) or
                               (enc.get("url") if enc is not None and "image" in (enc.get("type") or "") else None) or
                               _first_img(body)})
    for e in root.findall("a:entry", ns):
        link = next((l.get("href") for l in e.findall("a:link", ns) if l.get("rel") in (None, "alternate")), "")
        content = e.findtext("a:content", namespaces=ns)
        items.append({"title": _text(e.findtext("a:title", namespaces=ns)), "url": link,
                      "date": e.findtext("a:published", namespaces=ns) or e.findtext("a:updated", namespaces=ns),
                      "summary": _text(e.findtext("a:summary", namespaces=ns) or content)[:240],
                      "author": _text(e.findtext("a:author/a:name", namespaces=ns)), "image": _first_img(content)})
    return items


def _when(text):
    if not text:
        return None
    try:
        return email.utils.parsedate_to_datetime(text).astimezone(dt.timezone.utc)
    except (TypeError, ValueError):
        pass
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def _collect(sources, days, counts=None):
    now = dt.datetime.now(dt.timezone.utc)
    out, failed = [], []
    for name, urls in sources:
        for url in urls:
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    items = _parse(resp.read())
                break
            except Exception:
                items = None
        if items is None:
            failed.append(name)
            continue
        if counts is not None:
            counts[name] = len(items)
        for it in items:
            when = _when(it["date"])
            if not it["title"] or not it["url"] or not when or now - when > dt.timedelta(days=days):
                continue
            out.append({**it, "source": name, "utc": when.isoformat(), "date": None})
    return out, failed


def _words(title):
    return {w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) > 2 and w not in STOP}


def top_stories(limit=25):
    """Recent A/V and tech headlines; stories several outlets are covering rank first."""
    items, failed = _collect(NEWS_SOURCES, 3)
    now = dt.datetime.now(dt.timezone.utc)
    for it in items:
        w = _words(it["title"])
        it["coverage"] = 1 + len({o["source"] for o in items if o["source"] != it["source"]
                                  and len(w & _words(o["title"])) >= 3})
        age_h = (now - dt.datetime.fromisoformat(it["utc"])).total_seconds() / 3600
        it["av"] = bool(AV_WORDS.search(it["title"] + " " + it["summary"]))
        it["score"] = it["coverage"] * 3 + (2 if it["av"] else 0) - age_h / 12
    items.sort(key=lambda x: -x["score"])
    picked, seen = [], []
    for it in items:  # one entry per story
        w = _words(it["title"])
        if any(len(w & s) >= 3 for s in seen):
            continue
        seen.append(w)
        picked.append({k: it[k] for k in ("title", "url", "source", "utc", "summary", "coverage", "av", "image")})
        if len(picked) >= limit:
            break
    if not picked:
        raise RuntimeError("no news feeds answered (" + ", ".join(failed) + ")")
    return {"items": picked, "failed": failed}


def reviews(limit=25):
    """Latest hands-on product reviews written by named reviewers."""
    counts = {}
    items, failed = _collect(REVIEW_SOURCES, 14, counts)
    out, urls, per = [], set(), {}
    for it in sorted(items, key=lambda x: x["utc"], reverse=True):
        url = it["url"].lower()
        is_review = re.search(r"(^|[/_-])reviews?([/_.-]|$)", url) or re.search(r"\breview\b", it["title"], re.I)
        if re.search(r"/(entertainment|movies?|tv-shows?|streaming|games?/reviews?|books?)/", url):
            continue  # product reviews only, not films, shows or books
        if not is_review or it["url"] in urls or per.get(it["source"], 0) >= PER_SOURCE:
            continue
        urls.add(it["url"])
        per[it["source"]] = per.get(it["source"], 0) + 1
        out.append({k: it[k] for k in ("title", "url", "source", "utc", "summary", "author", "image")}
                   | {"av": bool(AV_WORDS.search(it["title"]))})
        if len(out) >= limit:
            break
    if not out:
        raise RuntimeError("no review feeds answered (" + ", ".join(failed) + ")")
    return {"items": out, "failed": failed, "feed_items": counts, "kept": per, "v": 2}
