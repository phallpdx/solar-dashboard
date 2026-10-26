r"""Refresh the dashboard's researched lists with a local model in LM Studio.

Runs on Parker's laptop every night (see local\setup.ps1). For each list it
fetches the pages in local\sources.json, asks the LM Studio model to pull out
items as JSON, checks them (real future dates, links that exist on the page
and still load, no duplicates), merges them into the current list from main,
and pushes the changed files to the claude/local-lists branch. The "Publish
researched lists" workflow then copies them onto main.

Only the standard library is used, so a plain Python install is enough.

    python local\refresh_lists.py                  # refresh everything and push
    python local\refresh_lists.py --only jazz,kids # just some lists
    python local\refresh_lists.py --dry-run        # write to local\out\ instead of pushing
    python local\refresh_lists.py --check-sources  # fetch each source and report, no model needed
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONFIG = json.load(open(os.path.join(HERE, "sources.json"), encoding="utf-8"))
LLM = CONFIG["lmstudio"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) solar-dashboard-local/1.0"
TODAY = dt.date.today()


LOG_FILE = os.environ.get("SOLAR_LISTS_LOG")


def log(*args):
    line = " ".join([time.strftime("%H:%M:%S"), *map(str, args)])
    print(line, flush=True)
    if LOG_FILE:  # set by run_daily.ps1 so progress shows up while the run is going
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def _alive(pid):
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes  # on Windows os.kill(pid, 0) would end the process, so ask the kernel instead
    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    k32.GetExitCodeProcess(handle, ctypes.byref(code))
    k32.CloseHandle(handle)
    return code.value == 259  # STILL_ACTIVE


def watch_parent():
    """Stops this run when run_daily.ps1 goes away, so End in Task Scheduler stops everything."""
    pid = int(os.environ.get("SOLAR_PARENT_PID") or 0)
    if not pid:
        return

    def loop():
        while _alive(pid):
            time.sleep(10)
        log("The scheduled task was stopped; stopping too.")
        os._exit(1)

    threading.Thread(target=loop, daemon=True).start()


# ---------------------------------------------------------------- fetching

class _TextAndLinks(HTMLParser):
    """Turns a page into plain text, keeping links as [text](url)."""

    SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer", "form", "iframe"}
    BLOCK = {"p", "div", "li", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6", "article", "section", "time"}

    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base, self.out, self.links = base, [], set()
        self.skip, self.href, self.atext = 0, None, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag == "a" and not self.skip:
            href = dict(attrs).get("href") or ""
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                self.href, self.atext = urllib.parse.urljoin(self.base, href), []
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag == "a" and self.href:
            text = " ".join("".join(self.atext).split())
            if text:
                self.out.append(f"[{text}]({self.href})")
                self.links.add(self.href)
            self.href = None
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip:
            return
        (self.atext if self.href else self.out).append(data)


def _squeeze(text):
    lines = (" ".join(l.split()) for l in text.splitlines())
    return "\n".join(l for l in lines if l)


def _strip_tags(s):
    return _squeeze(html.unescape(re.sub(r"<[^>]+>", " ", s or "")))


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
    for wait in (20, 60, None):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read(3_000_000)
                charset = resp.headers.get_content_charset() or "utf-8"
                return raw.decode(charset, "replace"), resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            # Reddit answers 429 when feeds are read back to back; wait and try again.
            if e.code != 429 or wait is None:
                raise
            time.sleep(wait)


def page_text(source, max_age_days=None):
    """Returns (text, links) for a source: an RSS/Atom feed or an HTML page."""
    body, ctype = fetch(source["url"])
    head = body.lstrip()[:300].lower()
    if "xml" in ctype or head.startswith("<?xml") or "<rss" in head or "<feed" in head:
        return feed_text(body, max_age_days)
    p = _TextAndLinks(source["url"])
    p.feed(body)
    return _squeeze("".join(p.out)), p.links


def feed_text(body, max_age_days=None):
    root = ET.fromstring(re.sub(r"^\s*<\?xml[^>]*\?>", "", body))
    out, links = [], set()
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        f = {c.tag.split("}")[-1]: c for c in el}
        title = _strip_tags(f["title"].text if "title" in f else "")
        link = ""
        if "link" in f:
            link = (f["link"].text or "").strip() or f["link"].get("href", "")
        when = None
        for k in ("pubDate", "published", "updated", "date"):
            if k in f and f[k].text:
                try:
                    when = parsedate_to_datetime(f[k].text)
                except (TypeError, ValueError):
                    try:
                        when = dt.datetime.fromisoformat(f[k].text.strip().replace("Z", "+00:00"))
                    except ValueError:
                        pass
                break
        if when and max_age_days is not None:
            age = dt.datetime.now(dt.timezone.utc) - (when if when.tzinfo else when.replace(tzinfo=dt.timezone.utc))
            if age.days > max_age_days:
                continue
        summary = ""
        for k in ("description", "summary", "content", "encoded"):
            if k in f and f[k].text:
                summary = _strip_tags(f[k].text)[:600]
                break
        stamp = when.date().isoformat() if when else "date unknown"
        out.append(f"- {title} ({stamp}) [{link}]\n  {summary}")
        if link:
            links.add(link)
    return "\n".join(out), links


# ---------------------------------------------------------------- model

def ask_model(task, text, schema):
    """Asks the LM Studio model to fill `schema` from `text`. Returns a dict or None."""
    messages = [
        {"role": "system", "content": "You extract facts from web pages into JSON. Use only what the page says. "
                                      "Never invent dates, prices or links. Links on the page are numbered like (#12); for a link "
                                      "field give that number, e.g. \"#12\". Keep every text field short, under 20 words. "
                                      "Write dates as YYYY-MM-DD. Write compact JSON with no indentation or line breaks. "
                                      f"Today is {TODAY:%A, %B %d, %Y} ({TODAY.isoformat()}). Reply with JSON only."},
        {"role": "user", "content": f"{task}\n\n--- PAGE ---\n{text}\n--- END ---"},
    ]
    payload = {
        "model": LLM["model"],
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 3000,
        # Gemma's thinking step is slow on this laptop and not needed for extraction.
        # LM Studio honours reasoning_effort for Gemma 4; enable_thinking is for other models.
        "reasoning_effort": "none",
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {"type": "json_schema", "json_schema": {"name": "result", "strict": True, "schema": schema}},
    }
    for attempt in range(2):
        try:
            choice = _post("/v1/chat/completions", payload)["choices"][0]
            content = choice["message"].get("content") or ""
        except urllib.error.HTTPError as e:
            if e.code == 400 and "response_format" in payload:
                payload.pop("response_format")  # model or server without structured output
                continue
            log("  model error:", e)
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            log("  model error:", e)
            return None
        parsed = _parse_json(content)
        if parsed is not None:
            return parsed
        if choice.get("finish_reason") == "length":
            # Asking again would spend the same minutes the same way.
            thought = len(choice["message"].get("reasoning_content") or "")
            log(f"  model ran out of tokens{' while thinking' if thought else ''}; skipping this page")
            return None
        log("  model reply was not JSON, retrying")
    return None


def _post(path, payload):
    req = urllib.request.Request(LLM["url"] + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=LLM.get("timeout_seconds", 900)) as resp:
        return json.load(resp)


def _parse_json(content):
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    start, end = content.find("{"), content.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return json.loads(content[start:end + 1])
    except json.JSONDecodeError:
        return None


def items_schema(props, required=None):
    item = {"type": "object", "properties": props, "required": required or list(props), "additionalProperties": False}
    return {"type": "object", "properties": {"items": {"type": "array", "items": item, "maxItems": 12}},
            "required": ["items"], "additionalProperties": False}


S = {"type": "string"}
NS = {"type": ["string", "null"]}
DATE = {"anyOf": [{"type": "string", "pattern": "^20(2[6-9]|3[0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"}, {"type": "null"}],
        "description": "YYYY-MM-DD or null"}
DATE_FIELDS = ("date", "ends", "starts", "by")


# ---------------------------------------------------------------- checks

def as_date(s):
    try:
        return dt.date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def loose_date(s):
    """Reads the dates a model writes despite being asked for YYYY-MM-DD:
    "October 26", "Tue, Oct 27, 2026", "10/26". Without a year, the next one to come."""
    d = as_date(s)
    if d and d.year < 2000:
        # Gemma sometimes puts the month in the year ("1027-10-27"); keep month and day.
        try:
            d = dt.date(TODAY.year, d.month, d.day)
        except ValueError:
            return s
        return (d if d >= TODAY - dt.timedelta(days=60) else d.replace(year=d.year + 1)).isoformat()
    if not s or d:
        return s
    text = str(s).lower()
    m = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?", text)
    if m:
        month, day, year = MONTHS[m.group(1)], int(m.group(2)), m.group(3)
    else:
        m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
        if not m:
            return s
        month, day, year = int(m.group(1)), int(m.group(2)), m.group(3)
        if year and len(year) == 2:
            year = "20" + year
    try:
        if year:
            return dt.date(int(year), month, day).isoformat()
        d = dt.date(TODAY.year, month, day)
        return (d if d >= TODAY - dt.timedelta(days=60) else d.replace(year=d.year + 1)).isoformat()
    except ValueError:
        return s


def clean(s, limit=400):
    s = " ".join(str(s or "").split())
    return s[:limit].rstrip() if s else ""


_url_ok_cache = {}


def url_ok(url):
    """False only when a link is clearly dead (404/410, bad host). Sites that block bots still count."""
    if url in _url_ok_cache:
        return _url_ok_cache[url]
    ok = True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
        urllib.request.urlopen(req, timeout=20).close()
    except urllib.error.HTTPError as e:
        ok = e.code not in (404, 410)
    except (urllib.error.URLError, ValueError):
        ok = False
    except (TimeoutError, OSError):
        ok = True
    _url_ok_cache[url] = ok
    return ok


def pick_url(url, links, fallback):
    """Uses the model's link only if it was really on the page and still loads."""
    url = (url or "").strip()
    if url.startswith("http") and url in links and url_ok(url):
        return url
    return fallback


def words(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower())) - {"the", "a", "and", "with", "at", "of", "in", "live"}


def same_thing(a_title, a_date, b_title, b_date):
    if a_date and b_date and a_date != b_date:
        return False
    a, b = words(a_title), words(b_title)
    if not a or not b:
        return False
    if a_date and a_date == b_date and _first_word(a_title) == _first_word(b_title):
        return True  # "Gorillaz The Mountain Tour" and "Gorillaz with Little Simz" on the same night
    return len(a & b) / min(len(a), len(b)) >= 0.6


def _first_word(title):
    found = re.findall(r"[a-z0-9]+", (title or "").lower())
    return next((w for w in found if w not in ("the", "a", "an")), "")


def last_date(item, fields):
    dates = [as_date(item.get(f)) for f in fields]
    dates = [d for d in dates if d]
    return max(dates) if dates else None


def still_current(item, fields):
    d = last_date(item, fields)
    return d is None or d >= TODAY


def merge(old, new, title_key, date_key, keep, sort_key, limit, reverse=False):
    out = [x for x in old if keep(x)]
    for item in new:
        if not any(same_thing(item[title_key], item.get(date_key), o[title_key], o.get(date_key)) for o in out):
            out.append(item)
    out.sort(key=sort_key, reverse=reverse)
    return out[:limit]


def by_date(*fields):
    def key(x):
        d = [as_date(x.get(f)) for f in fields]
        d = [v for v in d if v]
        return min(d) if d else dt.date.max
    return key


# ---------------------------------------------------------------- lists

LINK_FIELDS = ("url", "buy_url")


def number_links(text):
    """Swaps each link for a short number: a URL costs the model 30-40 tokens to copy, "#12" costs two."""
    table = {}

    def swap(m):
        n = table.setdefault(m.group(2), len(table) + 1)
        return f"{m.group(1)}#{n}{m.group(3)}"

    text = re.sub(r"([(\[])(https?://[^)\]\s]+)([)\]])", swap, text)
    return text, {n: url for url, n in table.items()}


def unnumber(value, table):
    m = re.fullmatch(r"#?(\d+)", str(value or "").strip())
    return table.get(int(m.group(1))) if m else value


CACHE_PATH = os.path.join(HERE, "cache", "pages.json")
_cache = None


def cached_items(key, digest):
    global _cache
    if _cache is None:
        try:
            _cache = json.load(open(CACHE_PATH, encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
    entry = _cache.get(key)
    return entry["items"] if entry and entry["hash"] == digest else None


def remember_items(key, digest, items):
    _cache[key] = {"hash": digest, "items": items, "seen": TODAY.isoformat()}
    for k in [k for k, v in _cache.items() if v.get("seen", "") < (TODAY - dt.timedelta(days=14)).isoformat()]:
        del _cache[k]
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(_cache, f)


def extract(sources, task, props, build, max_age_days=None, focus=None):
    """Runs one extraction task over each source and returns the built items.

    The model is the slow part (about 10 tokens a second on the laptop), so a page
    whose text hasn't changed since an earlier run reuses that run's answer, and
    `focus` can cut a page down to the lines worth reading, or to nothing."""
    found = []
    for src in sources:
        try:
            text, links = page_text(src, max_age_days)
        except Exception as e:  # noqa: BLE001 - one broken source must not stop the rest
            log(f"  {src['name']}: fetch failed ({e})")
            continue
        if len(text) < 200:
            log(f"  {src['name']}: almost no text (the page probably needs JavaScript)")
            continue
        if focus:
            text = focus(text)
            if not text:
                log(f"  {src['name']}: nothing relevant on the page, skipped the model")
                continue
        text, table = number_links(text)
        text = text[:LLM.get("max_chars_per_page", 9000)]
        key = src["url"] + " " + hashlib.sha1(task.encode()).hexdigest()[:8]
        digest = hashlib.sha1(text.encode()).hexdigest()
        t0 = time.time()
        raw = cached_items(key, digest)
        if raw is not None:
            how = "page unchanged, reused the last answer"
        else:
            log(f"  {src['name']}: asking the model ({len(text)} chars)")
            result = ask_model(task, text, items_schema(props))
            raw = (result or {}).get("items") or []
            if result is not None:
                remember_items(key, digest, raw)
            how = f"{time.time() - t0:.0f}s"
        kept = 0
        for r in raw:
            r = dict(r)
            for f in DATE_FIELDS:
                if f in r:
                    r[f] = loose_date(r[f])
            for f in LINK_FIELDS:
                if f in r:
                    r[f] = unnumber(r[f], table)
            item = build(r, src, links)
            if item:
                found.append(item)
                kept += 1
        log(f"  {src['name']}: {kept} of {len(raw)} items passed checks ({how})")
    return found


def future_ok(*fields, days=400):
    """Dates must be real, still to come, and within `days`: pages list next summer's
    festivals with guessed first-of-the-month dates, which aren't worth showing yet."""
    def check(r):
        dates = [as_date(r.get(f)) for f in fields]
        if any(r.get(f) and not d for f, d in zip(fields, dates)):
            return False  # a date that isn't a real date
        dates = [d for d in dates if d]
        return bool(dates) and max(dates) >= TODAY and min(dates) <= TODAY + dt.timedelta(days=days)
    return check


def refresh_jazz(data, sources):
    kinds = ["Local", "Touring", "Big band", "Vocal", "Latin", "Festival"]
    ok = future_ok("date", days=75)

    def build(r, src, links):
        if not ok(r) or not clean(r.get("artist")):
            return None
        url = pick_url(r.get("url"), links, src["url"])
        return {"artist": clean(r["artist"], 120), "kind": r["kind"] if r.get("kind") in kinds else "Local",
                "date": r["date"], "time": clean(r.get("time"), 20) or None, "venue": clean(r.get("venue"), 80) or src["name"],
                "price": clean(r.get("price"), 40) or None, "what": clean(r.get("what"), 300),
                "tickets": url, "sources": [{"name": src["name"], "url": url}]}

    new = extract(sources, "List every upcoming JAZZ performance in the Portland, Oregon area on this page. "
                           f"kind is one of {kinds}. time like '7:30 pm' or null. price like '$25' or null. "
                           "what is one plain sentence about the act. url is the event or ticket link number.",
                  {"artist": S, "kind": {"type": "string", "enum": kinds}, "date": DATE, "time": NS, "venue": S,
                   "price": NS, "what": S, "url": S}, build)
    data["shows"] = merge(data.get("shows", []), new, "artist", "date", lambda x: still_current(x, ["date"]),
                          by_date("date"), 30)
    return data


def refresh_concerts(data, sources):
    """Moves an artist from 'missing' to 'shows' once a venue lists a Portland date."""
    ok = future_ok("date", days=400)

    def build(r, src, links):
        if not ok(r) or not clean(r.get("artist")):
            return None
        return {"artist": clean(r["artist"], 120), "date": r["date"], "venue": clean(r.get("venue"), 80) or src["name"],
                "tickets": pick_url(r.get("url"), links, src["url"])}

    shows = [x for x in data.get("shows", []) if still_current(x, ["date"])]
    missing = data.get("missing", [])
    if not missing:
        data["shows"] = shows
        return data
    names = [m["artist"].lower() for m in missing]

    def focus(text):
        # Only the calendar lines that name an artist we're waiting on, plus a little context.
        lines = text.splitlines()
        keep = sorted({j for i, l in enumerate(lines) if any(n in l.lower() for n in names)
                       for j in range(max(0, i - 2), min(len(lines), i + 4))})
        return "\n".join(lines[j] for j in keep)

    listed = extract(sources, "List the upcoming concerts on this venue calendar excerpt: headlining artist, date, venue and the event or ticket url.",
                     {"artist": S, "date": DATE, "venue": S, "url": S}, build, focus=focus)
    still_missing = []
    for m in missing:
        name = words(m["artist"])
        hit = next((s for s in listed if name and name <= words(s["artist"])), None)
        if not hit:
            still_missing.append(m)
            continue
        log(f"  found a date for {m['artist']}: {hit['date']} at {hit['venue']}")
        shows.append({"artist": m["artist"], "album": m["album"], "score": m["score"],
                      "score_source": "Metacritic" if "metacritic" in (m.get("score_url") or "") else "Critics",
                      "score_url": m.get("score_url"), "date": hit["date"], "venue": hit["venue"], "tickets": hit["tickets"]})
    data["shows"] = sorted(shows, key=by_date("date"))
    data["missing"] = still_missing
    return data


def refresh_events(data, sources):
    kinds = ["Concert", "Sports", "Convention", "Expo", "Festival", "Parade", "Holiday", "Holiday lights", "Theater", "Other"]
    ok = future_ok("date", "ends", days=90)

    def build(r, src, links):
        if not ok(r) or not clean(r.get("title")):
            return None
        return {"title": clean(r["title"], 140), "date": r.get("date"), "ends": r.get("ends"),
                "venue": clean(r.get("venue"), 100), "kind": r["kind"] if r.get("kind") in kinds else "Other",
                "why": clean(r.get("why"), 240),
                "sources": [{"name": src["name"], "url": pick_url(r.get("url"), links, src["url"])}]}

    new = extract(sources, "List BIG upcoming events in Portland, Oregon on this page: arena concerts, big games, conventions, "
                           "festivals, parades, holiday lights. Skip small club shows and classes. ends is the last day or null. "
                           "why is one sentence on crowds or traffic to expect.",
                  {"title": S, "date": DATE, "ends": DATE, "venue": S, "kind": {"type": "string", "enum": kinds}, "why": S, "url": S},
                  build)
    data["events"] = merge(data.get("events", []), new, "title", "date", lambda x: still_current(x, ["date", "ends"]),
                           by_date("date", "ends"), 25)
    return data


def refresh_kids(data, sources):
    ok = future_ok("date", "ends", days=60)

    def build(r, src, links):
        if not ok(r) or not clean(r.get("title")):
            return None
        return {"title": clean(r["title"], 140), "date": r.get("date"), "ends": r.get("ends"),
                "where": clean(r.get("where"), 80), "detail": clean(r.get("detail"), 300),
                "url": pick_url(r.get("url"), links, src["url"])}

    new = extract(sources, "List upcoming events on this page that suit a TODDLER (ages 1 to 4) and family in or near Portland, Oregon. "
                           "Only real events at a place; skip holidays and closures on their own. "
                           "ends is the last day for multi-day events, else null. where is the neighborhood or town. "
                           "detail is one or two sentences with hours and price if given.",
                  {"title": S, "date": DATE, "ends": DATE, "where": S, "detail": S, "url": S}, build)
    data["events"] = merge(data.get("events", []), new, "title", "date", lambda x: still_current(x, ["date", "ends"]),
                           by_date("date", "ends"), 25)
    return data


def refresh_bluray(data, sources):
    def build(r, src, links):
        if not clean(r.get("title")):
            return None
        if r.get("ends") and (not as_date(r["ends"]) or as_date(r["ends"]) < TODAY):
            return None
        return {"title": clean(r["title"], 140), "store": clean(r.get("store"), 60), "detail": clean(r.get("detail"), 300),
                "ends": r.get("ends"), "url": pick_url(r.get("url"), links, src["url"])}

    new = extract(sources, "List current Blu-ray or 4K UHD disc deals and sales on this page. store is the retailer. "
                           "detail gives the price and what is included. ends is the end date if stated, else null.",
                  {"title": S, "store": S, "detail": S, "ends": DATE, "url": S}, build, max_age_days=4)
    old = data.get("deals", [])
    # Deals with no end date are only replaced when there is fresh news to replace them with.
    keep = (lambda x: x.get("ends") and still_current(x, ["ends"])) if len(new) >= 3 else (lambda x: still_current(x, ["ends"]))
    data["deals"] = merge(old, new, "title", "ends", keep, by_date("ends"), 12)
    return data


def refresh_foodfinds(data, sources):
    kinds = ["New product", "New brand", "Seasonal", "Award"]

    def build(r, src, links):
        d = as_date(r.get("date"))
        if not clean(r.get("name")) or not d or d > TODAY or (TODAY - d).days > 45:
            return None
        url = pick_url(r.get("url"), links, None)
        if not url:
            return None
        buy = pick_url(r.get("buy_url"), links, None)
        return {"name": clean(r["name"], 100), "maker": clean(r.get("maker"), 80),
                "kind": r["kind"] if r.get("kind") in kinds else "New product", "what": clean(r.get("what"), 320),
                "where_to_buy": [{"store": clean(r.get("buy_store"), 80) or "Buy", "url": buy}] if buy else [],
                "date": r["date"], "sources": [{"name": clean(r.get("headline"), 140) or src["name"], "url": url}]}

    new = extract(sources, "From these news items, list NEW food or drink products, brands, seasonal releases or awards from makers "
                           "in OREGON (Portland especially) that people can buy to take home. Skip restaurants, bars, hotels and "
                           "anything not from Oregon. date is the news date. "
                           f"kind is one of {kinds}. url is the article link. buy_url and buy_store only if the item gives one, else null.",
                  {"name": S, "maker": S, "kind": {"type": "string", "enum": kinds}, "what": S, "date": DATE,
                   "headline": S, "url": S, "buy_store": NS, "buy_url": NS}, build, max_age_days=14)
    cutoff = TODAY - dt.timedelta(days=120)
    data["items"] = merge(data.get("items", []), new, "name", None,
                          lambda x: (as_date(x.get("date")) or TODAY) >= cutoff,
                          lambda x: x.get("date") or "", 15, reverse=True)
    return data


def refresh_planahead(data, sources):
    kinds = ["Tickets", "Book", "Buy", "Deadline", "Permit"]
    ok = future_ok("by", "starts", days=120)

    def build(r, src, links):
        if not ok(r) or not clean(r.get("title")):
            return None
        return {"title": clean(r["title"], 160), "kind": r["kind"] if r.get("kind") in kinds else "Tickets",
                "action": clean(r.get("action"), 240), "starts": r.get("starts"), "by": r.get("by"),
                "why": clean(r.get("why"), 240),
                "sources": [{"name": src["name"], "url": pick_url(r.get("url"), links, src["url"])}]}

    new = extract(sources, "List things a Portland, Oregon family must ACT ON AHEAD of time: ticket presales or on-sale dates for "
                           "Portland shows, reservations that open, registration or permit deadlines. Skip anything not in Oregon "
                           "or SW Washington. action says what to do and when. starts is when sales or booking open, by is the "
                           f"deadline (YYYY-MM-DD or null). kind is one of {kinds}.",
                  {"title": S, "kind": {"type": "string", "enum": kinds}, "action": S, "starts": DATE, "by": DATE, "why": S, "url": S},
                  build, max_age_days=7)
    data["items"] = merge(data.get("items", []), new, "title", "starts", lambda x: still_current(x, ["by", "starts"]),
                          by_date("by", "starts"), 25)
    return data


def refresh_skioutlook(data, sources):
    season_src = [s for s in sources if s.get("use") == "season"]
    for src in season_src:
        try:
            text, _ = page_text(src)
        except Exception as e:  # noqa: BLE001
            log(f"  {src['name']}: fetch failed ({e})")
            continue
        log(f"  {src['name']}: asking the model")
        r = ask_model("Summarize this ENSO discussion for a skier in Oregon in 3 or 4 plain sentences: the current El Niño or "
                      "La Niña status and strength, the odds for this winter, the date of the next update, and what it usually "
                      "means for Pacific Northwest snowpack.",
                      text[:LLM.get("max_chars_per_page", 9000)],
                      {"type": "object", "properties": {"summary": S}, "required": ["summary"], "additionalProperties": False})
        summary = clean((r or {}).get("summary"), 900)
        if len(summary) > 120:
            data.setdefault("season", {})["summary"] = summary
    openings = data.get("openings", [])
    resorts = [o["resort"] for o in openings]
    statuses = ["Open", "Planned", "Depends on snow"]

    def build(r, src, links):
        o = next((o for o in openings if o["resort"].lower() == (r.get("resort") or "").lower()), None)
        if not o or r.get("status") not in statuses:
            return None
        if r.get("date") and not as_date(r["date"]):
            return None
        return {"resort": o["resort"], "date": r.get("date"), "status": r["status"], "note": clean(r.get("note"), 240),
                "source": {"name": src["name"], "url": src["url"]}}

    found = extract([s for s in sources if s.get("use") == "openings"],
                    f"For each of these ski areas, if the page mentions it: {resorts}. status is 'Open' if open now, 'Planned' "
                    "if the area itself has announced an opening date, else 'Depends on snow'. date is that opening date or null. "
                    "note is one sentence; say clearly when a date is only a projection. Use the resort names exactly as given.",
                    {"resort": {"type": "string", "enum": resorts or ["none"]}, "status": {"type": "string", "enum": statuses},
                     "date": DATE, "note": S}, build)
    for f in found:
        o = next(o for o in openings if o["resort"] == f["resort"])
        # A resort's own "Planned" date beats a projection; never downgrade Open or Planned from a guess page.
        rank = {"Depends on snow": 0, "Planned": 1, "Open": 2}
        if rank[f["status"]] >= rank.get(o.get("status"), 0):
            o.update({k: f[k] for k in ("date", "status", "note")})
            if f["source"]["url"] not in [s["url"] for s in o.get("sources", [])]:
                o.setdefault("sources", []).insert(0, f["source"])
    return data


def refresh_teams(data, team_sources):
    schema = {"type": "object", "properties": {
        "mood": {"type": "string", "description": "two to four words"},
        "pulse": {"type": "string", "description": "two sentences"},
        "storylines": {"type": "array", "items": S},
        "source_urls": {"type": "array", "items": S}},
        "required": ["mood", "pulse", "storylines", "source_urls"], "additionalProperties": False}
    names = {"blazers": "Portland Trail Blazers (NBA)", "timbers": "Portland Timbers (MLS)", "f1": "Formula 1"}
    changed = False
    for team, sources in team_sources.items():
        texts, links, names_by_url = [], set(), {}
        for src in sources:
            try:
                text, l = page_text(src, max_age_days=3)
            except Exception as e:  # noqa: BLE001
                log(f"  {src['name']}: fetch failed ({e})")
                continue
            texts.append(f"### {src['name']}\n{text[:LLM.get('max_chars_per_page', 9000) // max(1, len(sources))]}")
            links |= l
            names_by_url.update({u: src["name"] for u in l})
        if not texts:
            continue
        log(f"  {team}: asking the model")
        r = ask_model(f"These are the last few days of news and fan posts about the {names.get(team, team)}. Describe the fan mood. "
                      "mood: two to four words. pulse: two sentences on how fans feel right now and why. storylines: 3 to 5 "
                      "short factual lines (results, injuries, debates, next game). source_urls: up to 6 links from the list "
                      "that back this up.", "\n\n".join(texts), schema)
        if not r or len(clean(r.get("pulse"))) < 60 or len(r.get("storylines") or []) < 2:
            log(f"  {team}: model reply did not pass checks, keeping yesterday's")
            continue
        urls = [u for u in r.get("source_urls", []) if u in links][:6]
        data["teams"][team] = {"mood": clean(r["mood"], 40), "pulse": clean(r["pulse"], 500),
                               "storylines": [clean(s, 220) for s in r["storylines"][:5] if clean(s)],
                               "sources": [{"name": names_by_url[u], "url": u} for u in urls] or data["teams"].get(team, {}).get("sources", [])}
        changed = True
    if changed:
        data["updated_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return data


REFRESHERS = {
    "jazz": refresh_jazz, "concerts": refresh_concerts, "events": refresh_events, "kids": refresh_kids,
    "bluray": refresh_bluray, "foodfinds": refresh_foodfinds, "planahead": refresh_planahead,
    "skioutlook": refresh_skioutlook, "teams": refresh_teams,
}


# ---------------------------------------------------------------- git

def git(*args, env=None, stdin=None):
    # Bytes in and out, so Windows never turns the JSON's line endings into CRLF.
    out = subprocess.run(["git", "-C", REPO, *args], check=True, capture_output=True, env=env,
                         input=stdin.encode("utf-8") if stdin is not None else None).stdout
    return out.decode("utf-8").strip()


def current_lists(names):
    """Reads each list from origin/main, so local edits in this folder never get pushed."""
    git("fetch", "--quiet", "origin", "main")
    base = git("rev-parse", "origin/main")
    return base, {n: json.loads(git("show", f"{base}:web/{n}.json")) for n in names}


def push(base, files, branch):
    """Commits the files on top of origin/main without touching the working folder, then pushes."""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        git("read-tree", base, env=env)
        for path, text in files.items():
            blob = git("hash-object", "-w", "--stdin", stdin=text)
            git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = git("write-tree", env=env)
    names = ", ".join(os.path.splitext(os.path.basename(p))[0] for p in files)
    commit = git("commit-tree", tree, "-p", base, "-m", f"Local model refresh: {names}")
    git("push", "--force", "origin", f"{commit}:refs/heads/{branch}")
    return commit


# ---------------------------------------------------------------- main

def dump(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def check_sources():
    for name, sources in CONFIG["lists"].items():
        flat = [s for group in sources.values() for s in group] if isinstance(sources, dict) else sources
        for src in flat:
            try:
                text, links = page_text(src, max_age_days=7)
                verdict = "OK" if len(text) >= 200 else "almost no text (needs JavaScript?)"
                print(f"{name:11} {src['name']:38} {verdict}: {len(text)} chars, {len(links)} links")
            except Exception as e:  # noqa: BLE001
                print(f"{name:11} {src['name']:38} FAILED: {e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated list names, e.g. jazz,kids")
    ap.add_argument("--dry-run", action="store_true", help="write results to local/out/ instead of pushing")
    ap.add_argument("--check-sources", action="store_true", help="fetch every source and report, then stop")
    args = ap.parse_args()
    watch_parent()
    if args.check_sources:
        check_sources()
        return 0

    names = [n.strip() for n in args.only.split(",")] if args.only else list(REFRESHERS)
    unknown = [n for n in names if n not in REFRESHERS]
    if unknown:
        sys.exit(f"Unknown list(s): {', '.join(unknown)}. Choose from {', '.join(REFRESHERS)}.")
    try:
        ids = [m["id"] for m in json.load(urllib.request.urlopen(LLM["url"] + "/v1/models", timeout=60))["data"]]
    except Exception as e:  # noqa: BLE001
        sys.exit(f"LM Studio is not answering at {LLM['url']}: {e}")
    if LLM["model"] not in ids:
        # LM Studio sometimes lists a model without its publisher prefix.
        short = LLM["model"].split("/")[-1]
        match = [i for i in ids if i.split("/")[-1].startswith(short)] or ids
        if not match:
            sys.exit("LM Studio has no model loaded.")
        log(f"Model {LLM['model']} not listed by LM Studio ({', '.join(ids)}); using {match[0]}")
        LLM["model"] = match[0]
    try:
        reply = _post("/v1/chat/completions", {
            "model": LLM["model"], "messages": [{"role": "user", "content": "Say OK."}], "max_tokens": 20,
            "chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"})
    except Exception as e:  # noqa: BLE001
        sys.exit(f"LM Studio is not answering at {LLM['url']} with model {LLM['model']}: {e}")
    message = reply["choices"][0]["message"]
    if message.get("reasoning_content") and not (message.get("content") or "").strip():
        # With thinking on, one page takes 5+ minutes and usually runs out of tokens.
        sys.exit(f"{LLM['model']} is still thinking before it answers. Turn thinking off for it in LM Studio "
                 "(My Models, the gear next to the model), then run again.")

    base, lists = current_lists(names)
    changed, failed = {}, []
    for name in names:
        log(f"{name}:")
        before = dump(lists[name])
        try:
            data = REFRESHERS[name](json.loads(before), CONFIG["lists"][name])
        except Exception as e:  # noqa: BLE001 - keep going with the other lists
            log(f"  failed: {e!r}")
            failed.append(name)
            continue
        if dump(data) != before:
            data["updated"] = TODAY.isoformat()
            changed[f"web/{name}.json"] = dump(data)
            log(f"  changed")
        else:
            log(f"  no change")

    if not changed:
        log("Nothing changed.")
    elif args.dry_run:
        out = os.path.join(HERE, "out")
        os.makedirs(out, exist_ok=True)
        for path, text in changed.items():
            with open(os.path.join(out, os.path.basename(path)), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        log(f"Dry run: wrote {len(changed)} file(s) to {out}")
    else:
        commit = push(base, changed, CONFIG.get("push_branch", "claude/local-lists"))
        log(f"Pushed {commit[:8]} with {len(changed)} list(s); the publish workflow copies them to main.")
    if failed:
        log(f"Failed: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
