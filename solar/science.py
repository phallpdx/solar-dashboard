"""New science worth knowing about, from outlets that explain what a finding means."""
import datetime as dt
import html
import re

from . import news

SOURCES = [
    ("Quanta", ["https://www.quantamagazine.org/feed/"]),
    ("Science News", ["https://www.sciencenews.org/feed"]),
    ("Ars Technica", ["https://feeds.arstechnica.com/arstechnica/science"]),
    ("New Scientist", ["https://www.newscientist.com/subject/space/feed/", "https://www.newscientist.com/feed/home/"]),
    ("NASA", ["https://www.nasa.gov/news-release/feed/"]),
]

# Words that tend to mark a finding rather than a column, deal or listicle.
FINDING = re.compile(r"\b(discover\w*|first|new\w*|reveal\w*|find\w*|found|breakthrough|scientists?|researchers?|study|"
                     r"evidence|detect\w*|observ\w*|unveil\w*|solv\w*|prove[ds]?|proof|could|may|oldest|largest|smallest)\b", re.I)
APOD = re.compile(r"(APOD: )?\d{4} \w+ \d{1,2} [–-] ")
SKIP = re.compile(r"\b(podcast|quiz|crossword|puzzle|deal|deals|sale|review:|opinion|letters?|newsletter|how to watch|"
                  r"best .* to buy|weekly|this week in|photos of the week|book club)\b", re.I)

TOPICS = [
    ("🔭", "Space", r"\b(galax|star|planet|nasa|telescope|astro|cosmic|universe|moon|mars|jupiter|black hole|asteroid|comet|webb|solar system|exoplanet|orbit)"),
    ("🧬", "Biology", r"\b(gene|dna|cell|protein|virus|bacteri|evolution|species|brain|neuro|microb|immune|enzyme)"),
    ("💊", "Health", r"\b(cancer|disease|vaccine|drug|patient|health|medic|heart|diabet|alzheimer|therapy|clinical)"),
    ("🦖", "Fossils", r"\b(fossil|dinosaur|ancient|archaeolog|neanderthal|prehistoric|bones?|million years)"),
    ("🌍", "Earth & climate", r"\b(climate|ocean|earthquake|volcan|glacier|ice sheet|warming|carbon|weather|wildfire|forest|coral)"),
    ("🐾", "Animals", r"\b(animal|bird|fish|whale|insect|bee|frog|shark|mammal|octopus|spider|dog|cat)s?\b"),
    ("⚛️", "Physics", r"\b(quantum|physic|particle|atom|laser|photon|electron|neutrino|gravity|superconduct)"),
    ("➗", "Math & computing", r"\b(math|proof|conjecture|theorem|prime|algorithm|computer|comput|equation|AI\b|artificial intelligence|machine learning)"),
    ("🔋", "Energy & tech", r"\b(battery|solar|fusion|energy|reactor|robot|material|chip|semiconductor)"),
]


def _clean(text, limit=320):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*(The post .* appeared first on .*|Continue reading.*|Read more.*)$", "", text)
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return text


def _topic(text):
    for icon, name, pat in TOPICS:
        if re.search(pat, text, re.I):
            return icon, name
    return "🔬", "Science"


def breakthroughs(n=7, per_source=3):
    """The freshest science findings, each with a plain-language line on what it means."""
    items, failed = news._collect(SOURCES, 7)
    now = dt.datetime.now(dt.timezone.utc)
    scored = []
    for it in items:
        title, summary = _clean(it["title"], 200), _clean(it.get("summary", ""), 230)
        if SKIP.search(title) or APOD.match(title) or not summary:  # the picture of the day has its own card
            continue
        age_h = (now - dt.datetime.fromisoformat(it["utc"])).total_seconds() / 3600
        score = len(FINDING.findall(title + " " + summary)) * 1.5 - age_h / 18
        icon, topic = _topic(title + " " + summary)
        scored.append((score, {"title": title, "means": summary, "url": it["url"], "source": it["source"],
                               "image": it.get("image"), "utc": it["utc"], "icon": icon, "topic": topic}))
    scored.sort(key=lambda x: -x[0])
    out, per, seen = [], {}, set()
    for _, it in scored:
        key = re.sub(r"[^a-z0-9]+", " ", it["title"].lower())[:50]
        if key in seen or per.get(it["source"], 0) >= per_source:
            continue
        seen.add(key)
        per[it["source"]] = per.get(it["source"], 0) + 1
        out.append(it)
        if len(out) >= n:
            break
    if not out:
        raise RuntimeError("no science feeds answered (" + ", ".join(failed) + ")")
    return out
