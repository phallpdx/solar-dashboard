"""New shows and seasons on the big streaming services (TVmaze), the best-rated new movies and a daily kids' movie
on those services (TMDB, needs a free TMDB_API_KEY), and new albums (Wikipedia)."""
import datetime as dt
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = {"User-Agent": "solar-dashboard/1.0 (personal home dashboard; github.com/phallpdx/solar-dashboard)"}


def _get(url, as_json=True):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return json.loads(data) if as_json else data.decode("utf-8", "replace")


def _strip(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


# ------------------------------------------------------------------ streaming

def _service(show):
    """Which of the six services a TVmaze show streams on, or None."""
    web = ((show.get("webChannel") or {}).get("name") or "").lower()
    net = ((show.get("network") or {}).get("name") or "").lower()
    if "netflix" in web:
        return "Netflix"
    if "apple tv" in web:
        return "Apple TV"
    if "disney+" in web:
        return "Disney+"
    if web in ("max", "hbo max") or net == "hbo":
        return "HBO Max"
    if "hulu" in web:
        return "Hulu"
    if "prime video" in web:
        return "Prime Video"
    return None


def _premieres(start, days):
    """Series premieres and new seasons on the six services, from TVmaze's daily schedules."""
    seen, out, errors = set(), [], 0
    for i in range(days):
        day = (start + dt.timedelta(days=i)).isoformat()
        for url in (f"https://api.tvmaze.com/schedule/web?date={day}",
                    f"https://api.tvmaze.com/schedule?country=US&date={day}"):
            try:
                episodes = _get(url)
            except Exception:
                errors += 1
                continue
            finally:
                time.sleep(0.6)  # TVmaze allows about 20 calls every 10 seconds
            for ep in episodes:
                show = ep.get("show") or (ep.get("_embedded") or {}).get("show") or {}
                service = _service(show)
                if not service or ep.get("number") != 1 or not ep.get("season"):
                    continue
                key = (show.get("id"), ep["season"])
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    "date": ep.get("airdate") or day,
                    "service": service,
                    "title": show.get("name"),
                    "kind": "New series" if ep["season"] == 1 else f"Season {ep['season']}",
                    "type": show.get("type"),
                    "genres": show.get("genres") or [],
                    "language": show.get("language"),
                    "runtime": ep.get("runtime") or show.get("averageRuntime"),
                    "summary": _strip(show.get("summary"))[:320],
                    "image": (show.get("image") or {}).get("medium"),
                    "url": show.get("officialSite") or show.get("url"),
                    "rating": (show.get("rating") or {}).get("average"),
                    "rating_url": show.get("url"),
                })
    if not out and errors:
        raise RuntimeError(f"TVmaze didn't answer ({errors} calls failed)")
    out.sort(key=lambda x: (x["date"], x["service"], x["title"] or ""))
    return out


def streaming(days=30):
    """Series premieres and new seasons starting in the next few weeks."""
    return _premieres(dt.date.today(), days)


def top_shows(days=45, min_rating=7.5, limit=10):
    """Series and seasons that premiered in the last few weeks and that TVmaze viewers rate highly (out of 10)."""
    today = dt.date.today()
    found = [x for x in _premieres(today - dt.timedelta(days=days), days) if (x["rating"] or 0) >= min_rating]
    found.sort(key=lambda x: (-x["rating"], x["date"]))
    return found[:limit]


# ------------------------------------------------------------------ movies (TMDB, availability from JustWatch)

TMDB = "https://api.themoviedb.org/3"
# How each service is named in TMDB's US provider list. Add-on channels sold through another store are left out.
PROVIDERS = {"Netflix": ("netflix",), "Apple TV": ("apple tv", "apple tv+"), "Disney+": ("disney plus", "disney+"),
             "HBO Max": ("hbo max", "max"), "Hulu": ("hulu",), "Prime Video": ("amazon prime video", "prime video")}


def _tmdb(path, key, **params):
    params = {"language": "en-US", **params}
    headers = dict(UA)
    if key.startswith("eyJ"):  # the "API Read Access Token" is a bearer token; the shorter v3 API key goes in the URL
        headers["Authorization"] = "Bearer " + key
    else:
        params["api_key"] = key
    req = urllib.request.Request(f"{TMDB}{path}?{urllib.parse.urlencode(params)}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _provider_ids(key):
    """{provider id: service name} for the six services, looked up by name so ids are never guessed."""
    ids = {}
    for p in _tmdb("/watch/providers/movie", key, watch_region="US").get("results") or []:
        name = (p.get("provider_name") or "").lower()
        if "channel" in name or "kids" in name:
            continue
        for service, names in PROVIDERS.items():
            if any(name == n or name.startswith(n + " ") for n in names):
                ids[p["provider_id"]] = service
    if not ids:
        raise RuntimeError("TMDB's provider list had none of the six services")
    return ids


def _where(movie_id, key, ids):
    """Which of the six services stream a movie in the US with the subscription (no rent or buy)."""
    us = (_tmdb(f"/movie/{movie_id}/watch/providers", key).get("results") or {}).get("US") or {}
    return sorted({ids[p["provider_id"]] for p in us.get("flatrate") or [] if p.get("provider_id") in ids})


def _movie(m, services, **extra):
    return {"title": m.get("title"), "date": m.get("release_date"), "services": services,
            "rating": m.get("vote_average"), "votes": m.get("vote_count"),
            "summary": (m.get("overview") or "")[:320],
            "image": f"https://image.tmdb.org/t/p/w185{m['poster_path']}" if m.get("poster_path") else None,
            "url": f"https://www.themoviedb.org/movie/{m['id']}", "id": m["id"], **extra}


def _discover(key, ids, **params):
    return _tmdb("/discover/movie", key, watch_region="US", with_watch_monetization_types="flatrate",
                 with_watch_providers="|".join(map(str, ids)), include_adult="false", **params).get("results") or []


def top_movies(key, days=180, min_rating=7.0, min_votes=100, limit=10):
    """Movies first released in the last six months, now streaming on the six services, that TMDB users rate highly."""
    today = dt.date.today()
    ids = _provider_ids(key)
    out = []
    for m in _discover(key, ids, sort_by="vote_average.desc",
                       **{"primary_release_date.gte": (today - dt.timedelta(days=days)).isoformat(),
                          "primary_release_date.lte": today.isoformat(),
                          "vote_average.gte": min_rating, "vote_count.gte": min_votes}):
        services = _where(m["id"], key, ids)
        if services:
            out.append(_movie(m, services))
        if len(out) >= limit:
            break
    return out


def _easter(year):
    """Western Easter Sunday (the anonymous Gregorian algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return dt.date(year, month, day + 1)


def _nth_weekday(year, month, weekday, n):
    first = dt.date(year, month, 1)
    return first + dt.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def kid_themes(day):
    """What's in the air on a given day, most specific first: (why, TMDB keywords to try)."""
    y = day.year
    windows = [
        (dt.date(y, 10, 17), dt.date(y, 10, 31), "Halloween is coming", ["halloween", "witch", "ghost", "monster"]),
        (_nth_weekday(y, 11, 3, 4) - dt.timedelta(days=7), _nth_weekday(y, 11, 3, 4), "Thanksgiving week",
         ["thanksgiving", "family dinner", "gratitude"]),
        (dt.date(y, 12, 1), dt.date(y, 12, 26), "Christmas season", ["christmas", "santa claus", "snowman"]),
        (dt.date(y, 12, 27), dt.date(y, 12, 31), "the new year is coming", ["new year's eve", "winter"]),
        (dt.date(y, 1, 1), dt.date(y, 1, 2), "a brand new year", ["new year's eve", "winter"]),
        (dt.date(y, 2, 7), dt.date(y, 2, 14), "Valentine's Day is coming", ["valentine's day", "friendship", "love"]),
        (dt.date(y, 3, 14), dt.date(y, 3, 17), "St. Patrick's Day", ["ireland", "leprechaun"]),
        (_easter(y) - dt.timedelta(days=7), _easter(y), "Easter is coming", ["easter", "easter bunny", "rabbit"]),
        (dt.date(y, 4, 15), dt.date(y, 4, 22), "Earth Day is April 22", ["nature", "environment", "ocean"]),
        (dt.date(y, 7, 1), dt.date(y, 7, 4), "the Fourth of July", ["fireworks", "independence day", "summer"]),
        (dt.date(y, 8, 20), dt.date(y, 9, 10), "back-to-school time", ["school", "first day of school"]),
    ]
    out = [(why, words) for start, end, why, words in windows if start <= day <= end]
    season = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
              6: "summer", 7: "summer", 8: "summer", 9: "fall", 10: "fall", 11: "fall"}[day.month]
    out.append((f"it's {season}", {"winter": ["snow", "winter"], "spring": ["spring", "garden", "rain"],
                                   "summer": ["summer", "beach", "camping"], "fall": ["autumn", "harvest", "forest"]}[season]))
    out.append(("a family favorite", []))
    return out


def kids_movie(key, history, day=None):
    """A G or PG family movie that streams on the six services and fits the day, never one picked before."""
    day = day or dt.date.today()
    ids = _provider_ids(key)
    family = next((g["id"] for g in _tmdb("/genre/movie/list", key).get("genres") or [] if g.get("name") == "Family"), None)
    if family is None:
        raise RuntimeError("TMDB has no Family genre")
    used = set(history)
    for why, words in kid_themes(day):
        keyword_ids = []
        for w in words:
            hits = _tmdb("/search/keyword", key, query=w).get("results") or []
            keyword_ids += [str(k["id"]) for k in hits if (k.get("name") or "").lower() == w]
        if words and not keyword_ids:
            continue
        params = {"with_genres": family, "certification_country": "US", "certification.lte": "PG",
                  "vote_count.gte": 200, "sort_by": "vote_average.desc"}
        if keyword_ids:
            params["with_keywords"] = "|".join(keyword_ids)
        for page in range(1, 6):
            for m in _discover(key, ids, page=page, **params):
                if m["id"] in used:
                    continue
                services = _where(m["id"], key, ids)
                if services:
                    return _movie(m, services, why=why, date_picked=day.isoformat())
    raise RuntimeError("no family movie left on the six services that hasn't been picked already")


# ------------------------------------------------------------------ albums

class _Tables(HTMLParser):
    """Collects wikitable rows as lists of cells: {text, href, rowspan, colspan, header}."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.depth, self.row, self.cell, self.skip, self.spans = [], 0, None, None, 0, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.depth += 1
            if self.depth == 1 and "wikitable" in (a.get("class") or ""):
                self.tables.append([])
            elif self.depth == 1:
                self.tables.append(None)
        if self.depth != 1 or not self.tables or self.tables[-1] is None:
            return
        if tag == "tr":
            self.row = []
            self.tables[-1].append(self.row)
        elif tag in ("td", "th") and self.row is not None:
            def num(v):
                m = re.match(r"\d+", v or "")
                return int(m.group()) if m else 1
            self.cell = {"text": "", "href": None, "rowspan": num(a.get("rowspan")),
                         "colspan": num(a.get("colspan")), "header": tag == "th"}
            self.row.append(self.cell)
        elif tag == "span":
            hide = "sortkey" in (a.get("class") or "") or "display:none" in (a.get("style") or "").replace(" ", "")
            self.spans.append(hide)
            self.skip += hide
        elif tag in ("sup", "style"):
            self.skip += 1
        elif tag == "br" and self.cell is not None:
            self.cell["text"] += "\n"
        elif tag == "a" and self.cell is not None and not self.skip and not self.cell["href"]:
            href = a.get("href") or ""
            if href.startswith("./") or href.startswith("/wiki/"):
                self.cell["href"] = "https://en.wikipedia.org/wiki/" + href.split("/")[-1]

    def handle_endtag(self, tag):
        if tag == "table":
            self.depth -= 1
        elif tag in ("sup", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag == "span" and self.spans:
            self.skip -= self.spans.pop()
        if tag in ("td", "th"):
            self.cell = None

    def handle_data(self, data):
        if self.cell is not None and not self.skip:
            self.cell["text"] += data


def _grid(rows):
    """Expand rowspan/colspan into a plain grid of cells."""
    grid, carry = [], {}
    for row in rows:
        out, col, cells = [], 0, list(row)
        while cells or col in carry:
            if col in carry:
                cell, left = carry[col]
                out.append(cell)
                if left <= 1:
                    del carry[col]
                else:
                    carry[col] = (cell, left - 1)
                col += 1
                continue
            cell = cells.pop(0)
            for _ in range(cell["colspan"]):
                out.append(cell)
                if cell["rowspan"] > 1:
                    carry[col] = (cell, cell["rowspan"] - 1)
                col += 1
        grid.append(out)
    return grid


MONTHS = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
          "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]


def _albums_on_page(title, year):
    url = ("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": title, "prop": "text", "format": "json", "formatversion": 2, "redirects": 1}))
    data = _get(url)
    if "error" in data:
        return None
    parser = _Tables()
    parser.feed(data["parse"]["text"])
    found, heads = [], []
    for table in filter(None, parser.tables):
        grid = _grid(table)
        # Skip navigation rows ("Go to: January | February ...") above the real header.
        start = next((i for i, row in enumerate(grid)
                      if any(c["text"].strip().lower().startswith("artist") for c in row)
                      and any(c["text"].strip().lower().startswith("album") for c in row)), None)
        if start is None:
            continue
        grid = grid[start:]
        head = [(c["text"] or "").strip().lower() for c in grid[0]]
        heads.append("/".join(head)[:80])
        col = {name: next((i for i, h in enumerate(head) if h.startswith(name)), None)
               for name in ("release date", "artist", "album", "genre", "label")}
        if col["artist"] is None or col["album"] is None:
            continue
        date_cols = [i for i, h in enumerate(head) if h.startswith("release date")] or list(range(col["artist"]))
        for row in grid[1:]:
            if len(row) <= max(col["artist"], col["album"]) or all(c["header"] for c in row):
                continue
            date_text = " ".join(row[i]["text"] for i in date_cols if i < len(row))
            squashed = re.sub(r"\s+", "", date_text).upper()
            month = next((m for m in MONTHS if m in squashed), None) or next((m for m in MONTHS if m[:3] in squashed), None)
            day = re.findall(r"\d{1,2}", date_text)
            if not month or not day:
                continue
            try:
                when = dt.date(year, MONTHS.index(month) + 1, int(day[-1]))
            except ValueError:
                continue

            def text(name):
                i = col[name]
                return re.sub(r"\s+", " ", row[i]["text"]).strip() if i is not None and i < len(row) else ""

            album_cell = row[col["album"]]
            found.append({"date": when.isoformat(), "artist": text("artist"), "album": text("album"),
                          "genre": text("genre") or None, "label": text("label") or None,
                          "url": album_cell["href"] or row[col["artist"]]["href"]})
    if not found and heads:
        raise RuntimeError(f"{len(heads)} tables, headers like {heads[:2]}")
    return found


def albums(days=60, limit=250):
    """Notable albums due out in the next couple of months, from Wikipedia's yearly album lists."""
    today = dt.date.today()
    end = today + dt.timedelta(days=days)
    out, pages, notes = [], [], []
    for year in sorted({today.year, end.year}):
        for title in (f"List of {year} albums", f"List of {year} albums (January–June)",
                      f"List of {year} albums (July–December)"):
            try:
                rows = _albums_on_page(title, year)
                notes.append(f"{title}: {'missing' if rows is None else len(rows)}")
            except Exception as e:
                rows = None
                notes.append(f"{title}: {e}")
            if rows:
                pages.append(title)
                out.extend(rows)
    if not pages:
        raise RuntimeError("couldn't read Wikipedia's album lists (" + "; ".join(notes) + ")")
    seen, picked = set(), []
    for a in sorted(out, key=lambda x: (x["date"], x["artist"].lower())):
        key = (a["artist"].lower(), a["album"].lower())
        if today.isoformat() <= a["date"] <= end.isoformat() and a["artist"] and a["album"] and key not in seen:
            seen.add(key)
            picked.append(a)
    return picked[:limit]
