"""A/V and tech headlines, and the latest hands-on product reviews, from public RSS feeds."""
import datetime as dt
import email.utils
import html
import math
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
    ("FlatpanelsHD", ["https://www.flatpanelshd.com/rss/news.xml"]),
    ("AVForums", ["https://www.avforums.com/news/index.rss"]),
    ("Audioholics", ["https://www.audioholics.com/rss.xml", "https://www.audioholics.com/news/RSS"]),
    ("Digital Trends", ["https://www.digitaltrends.com/feed/"]),
    ("CNET", ["https://www.cnet.com/rss/all/"]),
    ("ZDNet", ["https://www.zdnet.com/news/rss.xml"]),
    ("Tom's Hardware", ["https://www.tomshardware.com/feeds/all"]),
    ("ecoustics", ["https://www.ecoustics.com/feed/"]),
    ("Darko.Audio", ["https://darko.audio/feed/"]),
    # Sound & Vision, Stereophile, Gizmodo and HomeTheaterReview sit behind a bot check and don't answer feed readers.
]
REVIEW_SOURCES = [
    ("The Verge", ["https://www.theverge.com/rss/reviews/index.xml"]),
    ("What Hi-Fi?", ["https://www.whathifi.com/feeds.xml"]),
    ("Engadget", ["https://www.engadget.com/rss.xml"]),
    ("AVForums", ["https://www.avforums.com/reviews/index.rss"]),
    ("TechRadar", ["https://www.techradar.com/reviews/feeds.xml", "https://www.techradar.com/feeds.xml"]),
    ("Tom's Guide", ["https://www.tomsguide.com/reviews/feeds.xml", "https://www.tomsguide.com/feeds.xml"]),
    ("Tom's Hardware", ["https://www.tomshardware.com/feeds/all"]),
    ("Digital Trends", ["https://www.digitaltrends.com/feed/"]),
    ("CNET", ["https://www.cnet.com/rss/all/"]),
    ("ZDNet", ["https://www.zdnet.com/news/rss.xml"]),
    ("Wired", ["https://www.wired.com/feed/tag/review/latest/rss", "https://www.wired.com/feed/category/gear/latest/rss"]),
    ("PCMag", ["https://www.pcmag.com/feeds/rss/reviews", "https://www.pcmag.com/feeds/rss/latest"]),
    ("SoundGuys", ["https://www.soundguys.com/feed/"]),
    ("Headphonesty", ["https://www.headphonesty.com/feed/"]),
    ("ecoustics", ["https://www.ecoustics.com/feed/"]),
    ("Darko.Audio", ["https://darko.audio/feed/"]),
    ("Audioholics", ["https://www.audioholics.com/rss.xml"]),
    # Only items whose link or title says "review" are kept, so a site's main feed works where its reviews feed is gone.
]
# Big national and world news: outlets with working public feeds (AP and Reuters have none).
BIG_SOURCES = [
    ("NPR", ["https://feeds.npr.org/1001/rss.xml"]),
    ("New York Times", ["https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"]),
    ("CNN", ["http://rss.cnn.com/rss/cnn_topstories.rss"]),
    ("ABC News", ["https://feeds.abcnews.com/abcnews/topstories"]),
    ("CBS News", ["https://www.cbsnews.com/latest/rss/main"]),
    ("NBC News", ["https://feeds.nbcnews.com/nbcnews/public/news"]),
    ("PBS NewsHour", ["https://www.pbs.org/newshour/feeds/rss/headlines"]),
    ("Wall Street Journal", ["https://feeds.a.dj.com/rss/RSSWorldNews.xml"]),
    ("Axios", ["https://api.axios.com/feed/"]),
    ("Politico", ["https://rss.politico.com/politics-news.xml"]),
    ("Fox News", ["https://moxie.foxnews.com/google-publisher/latest.xml"]),
    ("BBC", ["https://feeds.bbci.co.uk/news/world/rss.xml"]),
    ("The Guardian", ["https://www.theguardian.com/us-news/rss", "https://www.theguardian.com/world/rss"]),
    ("Al Jazeera", ["https://www.aljazeera.com/xml/rss/all.xml"]),
]
# Portland-area newsrooms. Willamette Week has no working feed, and KXL's feed isn't valid XML.
LOCAL_SOURCES = [
    ("OPB", ["https://www.opb.org/arc/outboundfeeds/rss/?outputType=xml"]),
    ("The Oregonian", ["https://www.oregonlive.com/arc/outboundfeeds/rss/?outputType=xml"]),
    ("KGW", ["https://www.kgw.com/feeds/syndication/rss/news/local"]),
    ("KOIN", ["https://www.koin.com/news/feed/"]),
    ("KATU", ["https://katu.com/news/local.rss"]),
    ("KPTV", ["https://www.kptv.com/arc/outboundfeeds/rss/?outputType=xml"]),
    ("Portland Mercury", ["https://www.portlandmercury.com/feed"]),
    ("Oregon Capital Chronicle", ["https://oregoncapitalchronicle.com/feed/"]),
]
# Feed items that aren't news stories: shopping, puzzles, horoscopes, live blogs of games and the like.
NOT_NEWS = re.compile(r"\b(wordle|connections hint|crossword|horoscope|best deals?|deals? of the day|coupon|"
                      r"promo code|sponsored|newsletter|podcast|quiz|recipe|watch live|how to watch|live stream|"
                      r"what to watch|obituar\w*|photos?:|gallery|readers respond|letters to the editor|opinion:|editorial:)\b", re.I)
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


def _headlines(sources, hours, limit, keep=None):
    """Stories from the last `hours`, grouped so each story appears once, ranked by how many outlets cover it.
    Words are weighted by rarity, so two items only count as one story when they share its distinctive words
    (names, places), not common ones like "man" or "sentenced"."""
    items, failed = _collect(sources, hours / 24)
    now = dt.datetime.now(dt.timezone.utc)
    items = [it for it in items if not NOT_NEWS.search(it["title"]) and (keep is None or keep(it))]
    if not items:
        raise RuntimeError("no news feeds answered (" + ", ".join(failed) + ")")
    words = [_words(it["title"]) | _words(it["summary"][:160]) for it in items]
    df = {}
    for w in words:
        for x in w:
            df[x] = df.get(x, 0) + 1
    n = len(items)
    weight = {x: math.log(n / c) for x, c in df.items()}
    mass = [sum(weight[x] for x in w) or 1 for w in words]

    def similar(i, j):
        shared = sum(weight[x] for x in words[i] & words[j] if df[x] > 1)
        return shared / min(mass[i], mass[j]) >= 0.28 and shared >= 8

    parent = list(range(n))  # union-find: items about the same story end up in one group

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if items[i]["source"] != items[j]["source"] and similar(i, j):
                parent[root(i)] = root(j)
    groups = {}
    for i in range(n):
        groups.setdefault(root(i), []).append(i)
    order = {name: k for k, (name, _) in enumerate(sources)}
    stories = []
    for members in groups.values():
        latest = max(dt.datetime.fromisoformat(items[i]["utc"]) for i in members)
        outlets = {}
        for i in sorted(members, key=lambda i: items[i]["utc"]):
            outlets.setdefault(items[i]["source"], i)  # each outlet's first story on it
        # Lead with the version that best matches the rest of the group; ties go to the earlier-listed outlet.
        lead = max(outlets.values(), key=lambda i: (sum(similar(i, j) for j in outlets.values() if j != i),
                                                    -order[items[i]["source"]]))
        age_h = (now - latest).total_seconds() / 3600
        it = items[lead]
        stories.append({**{k: it[k] for k in ("title", "url", "source", "utc", "summary", "image")},
                        "coverage": len(outlets),
                        "also": [{"source": items[i]["source"], "url": items[i]["url"]}
                                 for i in sorted(outlets.values(), key=lambda i: order[items[i]["source"]]) if i != lead],
                        "score": len(outlets) * 3 - age_h / 8})
    stories.sort(key=lambda x: -x["score"])
    picked, per = [], {}
    for st in stories:  # no single outlet fills the list with its own exclusives
        if st["coverage"] == 1 and per.get(st["source"], 0) >= 2:
            continue
        per[st["source"]] = per.get(st["source"], 0) + 1
        picked.append({k: v for k, v in st.items() if k != "score"})
        if len(picked) >= limit:
            break
    return {"items": picked, "failed": failed}


def big_news(limit=12):
    """The biggest national and world stories right now: the ones the most outlets are covering."""
    return _headlines(BIG_SOURCES, 24, limit)


# OPB, The Oregonian and the Capital Chronicle also carry national wire and NPR stories; from them, keep only
# items that name a place or thing around here. The TV stations' feeds above are local-only already.
MIXED_FEEDS = {"OPB", "The Oregonian", "Oregon Capital Chronicle"}
NEARBY = re.compile(r"\b(portland\w*|oregon\w*|ore\.|pdx|multnomah|clackamas|washington county|clark county|"
                    r"vancouver|gresham|beaverton|hillsboro|tigard|tualatin|lake oswego|oregon city|milwaukie|"
                    r"troutdale|happy valley|wilsonville|sherwood|forest grove|salem|eugene|bend|corvallis|medford|"
                    r"astoria|columbia river|willamette|mount hood|mt\. hood|trimet|max line|pge|pacific power|"
                    r"kotek|blazers|timbers|thorns|ducks|beavers|pacific northwest|washington state|wash\.|"
                    r"st\. johns|sauvie|scappoose|st\. helens|ice building|i-5|i-84|i-205)\b", re.I)


def local_news(limit=12):
    """Portland-area news from local newsrooms, with stories several of them cover first."""
    from .portland import about_maine

    def keep(it):
        text = it["title"] + " " + it["summary"]
        return not about_maine(text) and (it["source"] not in MIXED_FEEDS or bool(NEARBY.search(text)))
    return _headlines(LOCAL_SOURCES, 36, limit, keep=keep)


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
