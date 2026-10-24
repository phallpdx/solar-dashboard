"""Coming soon: new shows and seasons on the big streaming services (TVmaze), and new albums (Wikipedia)."""
import datetime as dt
import html
import json
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


def streaming(days=30):
    """Series premieres and new seasons starting in the next few weeks."""
    today = dt.date.today()
    seen, out, errors = set(), [], 0
    for i in range(days):
        day = (today + dt.timedelta(days=i)).isoformat()
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
                })
    if not out and errors:
        raise RuntimeError(f"TVmaze didn't answer ({errors} calls failed)")
    out.sort(key=lambda x: (x["date"], x["service"], x["title"] or ""))
    return out


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
