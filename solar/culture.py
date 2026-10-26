"""What's trending online, book picks from Goodreads, and a long read for each day."""
import datetime as dt
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from . import news

UA = {"User-Agent": "solar-dashboard/1.0 (personal home dashboard; github.com/phallpdx/solar-dashboard)"}
HT = "{https://trends.google.com/trending/rss}"


def _open(url, headers=UA, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)


# ---------------------------------------------------------------- trending

def google_trends(n=8):
    """Today's fastest-rising US searches, each with a news story that explains it."""
    with _open("https://trends.google.com/trending/rss?geo=US") as r:
        root = ET.fromstring(r.read())
    out = []
    for it in root.iter("item"):
        story = it.find(HT + "news_item")
        traffic = (it.findtext(HT + "approx_traffic") or "").strip()
        out.append({"title": (it.findtext("title") or "").strip(), "traffic": traffic,
                    "picture": it.findtext(HT + "picture"),
                    "story": html.unescape(story.findtext(HT + "news_item_title") or "") if story is not None else None,
                    "url": story.findtext(HT + "news_item_url") if story is not None else None,
                    "source": story.findtext(HT + "news_item_source") if story is not None else None})
    def size(t):
        m = re.match(r"([\d,]+)(K|M)?", t["traffic"].replace("+", ""))
        return int(m.group(1).replace(",", "")) * {"K": 1e3, "M": 1e6}.get(m.group(2), 1) if m else 0
    return sorted(out, key=size, reverse=True)[:n]


def wiki_most_read(day, n=8):
    """Yesterday's most-read English Wikipedia articles: a good read on what people are curious about."""
    y = day - dt.timedelta(days=1)
    with _open(f"https://en.wikipedia.org/api/rest_v1/feed/featured/{y:%Y/%m/%d}") as r:
        data = json.load(r)
    out = []
    for a in (data.get("mostread") or {}).get("articles") or []:
        if a.get("namespace", {}).get("id", 0) != 0 or a.get("title") in ("Main_Page", "Special:Search"):
            continue
        out.append({"title": a.get("normalizedtitle") or a["title"].replace("_", " "), "views": a.get("views"),
                    "about": a.get("description"), "url": (a.get("content_urls") or {}).get("desktop", {}).get("page"),
                    "image": (a.get("thumbnail") or {}).get("source")})
        if len(out) >= n:
            break
    return out


def reddit_popular(n=8):
    """The top of Reddit's front page today."""
    headers = {"User-Agent": "linux:solar-dashboard:1.0 (personal dashboard)"}
    for host in ("www.reddit.com", "old.reddit.com"):
        try:
            with _open(f"https://{host}/r/popular/top.json?t=day&limit=40&raw_json=1", headers) as r:
                posts = [c["data"] for c in json.load(r)["data"]["children"]]
            break
        except Exception:
            posts = None
    if posts is None:
        raise RuntimeError("Reddit blocked the request")
    posts = [p for p in posts if not p.get("over_18") and not p.get("stickied")]
    return [{"title": p.get("title"), "sub": p.get("subreddit"), "score": p.get("score"),
             "comments": p.get("num_comments"), "url": "https://www.reddit.com" + (p.get("permalink") or "")}
            for p in posts[:n]]


# ---------------------------------------------------------------- books

def goodreads_user(text):
    """Accept a profile link, a shelf link or a bare id."""
    m = re.search(r"(\d{3,})", text or "")
    return m.group(1) if m else None


def _shelf(user, shelf):
    url = f"https://www.goodreads.com/review/list_rss/{user}?" + urllib.parse.urlencode({"shelf": shelf, "per_page": 200})
    with _open(url, {"User-Agent": "Mozilla/5.0 (solar-dashboard personal dashboard)"}) as r:
        root = ET.fromstring(r.read())
    out = []
    for it in root.iter("item"):
        out.append({"title": (it.findtext("title") or "").strip(), "author": (it.findtext("author_name") or "").strip(),
                    "rating": int(it.findtext("user_rating") or 0), "read_at": it.findtext("user_read_at") or "",
                    "year": it.findtext("book_published")})
    return out


def _norm(title):
    return re.sub(r"[^a-z0-9]+", " ", re.split(r"[:(]", title.lower())[0]).strip()


def book_picks(user, today, n=8):
    """New and recent books by the authors you rate highest, skipping ones already on your shelves."""
    read = _shelf(user, "read")
    if not read:
        raise RuntimeError("The Goodreads shelf came back empty; is the profile public?")
    try:
        to_read = _shelf(user, "to-read")
    except Exception:
        to_read = []
    known = {_norm(b["title"]) for b in read + to_read}
    # Authors ranked by how much you liked them: 5 stars counts most, and reading many of theirs helps too.
    score = {}
    for b in read:
        if b["author"]:
            score[b["author"]] = score.get(b["author"], 0) + {5: 3, 4: 2, 3: 0.5}.get(b["rating"], 0.25)
    authors = sorted(score, key=score.get, reverse=True)[:12]
    picks, seen = [], set()
    for author in authors:
        url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(
            {"author": author, "sort": "new", "limit": 15, "fields": "title,first_publish_year,key,cover_i,author_name,language"})
        try:
            with _open(url) as r:
                docs = json.load(r).get("docs") or []
        except Exception:
            continue
        for d in docs:
            year = d.get("first_publish_year") or 0
            t = _norm(d.get("title") or "")
            if year < today.year - 2 or not t or t in known or t in seen or "eng" not in (d.get("language") or ["eng"]):
                continue
            seen.add(t)
            picks.append({"title": d["title"], "author": author, "year": year, "because": f"You rated {author} highly",
                          "url": f"https://www.goodreads.com/search?" + urllib.parse.urlencode({"q": f"{d['title']} {author}"}),
                          "cover": f"https://covers.openlibrary.org/b/id/{d['cover_i']}-M.jpg" if d.get("cover_i") else None})
            break  # one per author keeps the list varied
        if len(picks) >= n:
            break
    recent = sorted([b for b in read if b["read_at"]], key=lambda b: _when(b["read_at"]), reverse=True)[:3]
    return {"picks": picks, "read_count": len(read), "to_read_count": len(to_read),
            "recent": [{"title": b["title"], "author": b["author"], "rating": b["rating"]} for b in recent],
            "top_authors": authors[:5]}


def _when(text):
    try:
        return dt.datetime.strptime(text[:25].strip(), "%a, %d %b %Y %H:%M:%S")
    except ValueError:
        return dt.datetime.min


# ---------------------------------------------------------------- long reads

# (title, author, publication, year, why it's worth your time)
LONG_READS = [
    ("Hiroshima", "John Hersey", "The New Yorker", 1946, "Six survivors of the bombing, told so plainly it took over an entire issue of the magazine."),
    ("Notes of a Native Son", "James Baldwin", "Harper's", 1955, "Baldwin on his father's death, the Harlem riot and rage. One of the great American essays."),
    ("Letter from a Region in My Mind", "James Baldwin", "The New Yorker", 1962, "The piece that became The Fire Next Time."),
    ("Superman Comes to the Supermarket", "Norman Mailer", "Esquire", 1960, "Mailer at the 1960 convention, inventing a new kind of political writing."),
    ("The Last American Hero Is Junior Johnson. Yes!", "Tom Wolfe", "Esquire", 1965, "Moonshine, stock cars and Wolfe's New Journalism at full throttle."),
    ("Frank Sinatra Has a Cold", "Gay Talese", "Esquire", 1966, "A profile written without ever interviewing its subject. Often called the best magazine story ever."),
    ("Slouching Towards Bethlehem", "Joan Didion", "The Saturday Evening Post", 1967, "Didion in Haight-Ashbury as the sixties curdle."),
    ("Goodbye to All That", "Joan Didion", "The Saturday Evening Post", 1967, "Falling in and out of love with New York."),
    ("The Kentucky Derby Is Decadent and Depraved", "Hunter S. Thompson", "Scanlan's Monthly", 1970, "The birth of gonzo."),
    ("The Search for Marvin Gardens", "John McPhee", "The New Yorker", 1972, "Atlantic City told through a game of Monopoly."),
    ("American Man, Age Ten", "Susan Orlean", "Esquire", 1992, "A season with a ten-year-old boy. Funny and tender."),
    ("Ticket to the Fair", "David Foster Wallace", "Harper's", 1994, "DFW at the Illinois State Fair."),
    ("Shipping Out", "David Foster Wallace", "Harper's", 1996, "A week on a luxury cruise. Later titled A Supposedly Fun Thing I'll Never Do Again."),
    ("Into Thin Air", "Jon Krakauer", "Outside", 1996, "The 1996 Everest disaster, by someone who was on the mountain."),
    ("The Falling Man", "Tom Junod", "Esquire", 2003, "The search for the identity of one man in one photograph from 9/11."),
    ("Consider the Lobster", "David Foster Wallace", "Gourmet", 2004, "A food-festival assignment that turns into a question about pain."),
    ("Upon This Rock", "John Jeremiah Sullivan", "GQ", 2004, "A skeptic at a Christian rock festival. Generous and very funny."),
    ("The Ketchup Conundrum", "Malcolm Gladwell", "The New Yorker", 2004, "Why there are dozens of mustards but only one ketchup."),
    ("The Squid Hunter", "David Grann", "The New Yorker", 2004, "One man's obsession with finding a live giant squid."),
    ("The New Mecca", "George Saunders", "GQ", 2005, "Saunders in Dubai."),
    ("Lost in the Meritocracy", "Walter Kirn", "The Atlantic", 2005, "A brilliant student who learns to game school without learning much."),
    ("Federer as Religious Experience", "David Foster Wallace", "The New York Times", 2006, "Watching Roger Federer at Wimbledon."),
    ("Pearls Before Breakfast", "Gene Weingarten", "The Washington Post", 2007, "A star violinist busks in a subway station. Won the Pulitzer Prize."),
    ("Men Explain Things to Me", "Rebecca Solnit", "TomDispatch", 2008, "The essay that gave us the word mansplaining."),
    ("Fatal Distraction", "Gene Weingarten", "The Washington Post", 2009, "Parents who forget a child in a hot car. Devastating, and it won the Pulitzer."),
    ("Trial by Fire", "David Grann", "The New Yorker", 2009, "Did Texas execute an innocent man?"),
    ("The Cost Conundrum", "Atul Gawande", "The New Yorker", 2009, "Why one Texas town's health care cost twice the national average."),
    ("Letting Go", "Atul Gawande", "The New Yorker", 2010, "What medicine should do when it can't save your life."),
    ("Mister Lytle", "John Jeremiah Sullivan", "The Paris Review", 2011, "A young writer and an old Southern novelist."),
    ("The Innocent Man", "Pamela Colloff", "Texas Monthly", 2012, "Michael Morton's 25 years in prison for a murder he didn't commit."),
    ("Snow Fall: The Avalanche at Tunnel Creek", "John Branch", "The New York Times", 2012, "Skiers caught in a Cascades avalanche. Won the Pulitzer."),
    ("Thanksgiving in Mongolia", "Ariel Levy", "The New Yorker", 2013, "A short, shattering essay about loss far from home."),
    ("Joy", "Zadie Smith", "The New York Review of Books", 2013, "The difference between pleasure and joy."),
    ("The Case for Reparations", "Ta-Nehisi Coates", "The Atlantic", 2014, "Housing, redlining and what is owed."),
    ("The Ballad of Geeshie and Elvie", "John Jeremiah Sullivan", "The New York Times Magazine", 2014, "Hunting for two mystery blues singers from the 1930s."),
    ("The Really Big One", "Kathryn Schulz", "The New Yorker", 2015, "The Cascadia earthquake waiting under Oregon. Won the Pulitzer, and it's about your backyard."),
    ("An Unbelievable Story of Rape", "T. Christian Miller and Ken Armstrong", "ProPublica and The Marshall Project", 2015, "A teenager who wasn't believed, and the detectives who found the truth. Won the Pulitzer."),
    ("The Lonely Death of George Bell", "N. R. Kleinfield", "The New York Times", 2015, "What happens when someone dies alone in New York."),
    ("When Things Go Missing", "Kathryn Schulz", "The New Yorker", 2017, "On losing keys, losing things and losing a father."),
    ("Losing Earth", "Nathaniel Rich", "The New York Times Magazine", 2018, "The decade when we almost stopped climate change."),
    ("How the Pandemic Defeated America", "Ed Yong", "The Atlantic", 2020, "Why the US fell apart against Covid. Won the Pulitzer."),
]


def long_read(day):
    title, author, pub, year, why = LONG_READS[(day.toordinal() * 5) % len(LONG_READS)]
    q = f"{title} {author} {pub}"
    return {"title": title, "author": author, "pub": pub, "year": year, "why": why,
            "url": "https://duckduckgo.com/?" + urllib.parse.urlencode({"q": "! " + q}),
            "search": "https://www.google.com/search?" + urllib.parse.urlencode({"q": q})}


def fresh_longreads(n=4):
    """The newest picks from Longreads, whose editors spotlight the best long-form writing each week."""
    items, failed = news._collect([("Longreads", ["https://longreads.com/feed/"])], 10)
    if not items:
        raise RuntimeError("Longreads feed didn't answer")
    items.sort(key=lambda x: x["utc"], reverse=True)
    return [{"title": it["title"], "url": it["url"], "summary": it["summary"], "author": it.get("author"),
             "image": it.get("image")} for it in items[:n]]
