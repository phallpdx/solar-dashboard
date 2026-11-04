"""Underpriced music gear on Portland Craigslist (musical instruments, "msa").

Listings come from Craigslist's no-script search page. Each asking price is compared with what the same
gear actually sold for used on Reverb: the middle of the matching sales. A sale only counts when it is the
same brand and model, not a different version of it, the same kind of gear, and from the same era (see
comps below). When nothing matches confidently the listing gets no price, and the reason is kept so the
page can say why. Anything at 70% or less of the usual price is a deal.
"""
import datetime
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
SEARCH = "https://portland.craigslist.org/search/msa"
SKIP = re.compile(r"\b(wanted|wtb|iso|looking for|lessons?|teacher|repair|rehearsal|studio time|band|trade only|"
                  r"for parts|broken|case only|stand only|rental)\b", re.I)
DEAL = 0.7
DRUM_DEAL = 0.75  # drums and percussion are what Parker is shopping for, so a smaller discount still shows
# Drums and percussion get looked up first and marked, since that's what Parker is after.
DRUMS = re.compile(r"\b(drums?|snares?|kick|toms?|floor tom|cymbals?|ride|crash|hi-?hats?|hats|splash|china|congas?|"
                   r"bongos?|timbales?|djembes?|cajons?|percussion|shakers?|tambourines?|cowbell|marimba|vibraphone|"
                   r"glockenspiel|xylophone|steel ?pan|tabla|darbuka|doumbek|frame drum|octapad|spd|e-?kit|v-?drums|"
                   r"ludwig|tama|pearl|\bdw\b|gretsch|sonor|mapex|zildjian|sabian|paiste|meinl|istanbul|bosphorus|"
                   r"latin percussion|\blp\b|gon bops|toca|remo|evans|rogers|slingerland|craviotto|c&c|canopus|sakae)\b", re.I)
# Parker's wish list: any listing for these shows up flagged at the top, priced or not.
WATCH = [
    (re.compile(r"craviotto", re.I), "Craviotto"),
    # Old K Zildjians: the Istanbul-made Ks (to the late 1970s) and Canadian Ks, not the modern K line.
    (re.compile(r"(?=.*\b(k\.? ?zildjian|zildjian k\b|\bk\b.*zildjian|zildjian.*\bk\b|old k|istanbul k))"
                r"(?=.*\b(vintage|old|istanbul|turkish|canadian|early|stamp|(19)?[3-8]0'?s|19[3-8]\d))", re.I), "Vintage K Zildjian"),
]
WATCH_QUERIES = ["craviotto", "k zildjian", "zildjian k", "old k zildjian"]
# Reselling costs about 15% of the price in fees and haggling, so that's taken off before calling it profit.
RESALE = 0.85
FLIP_PROFIT = 150
# A flip also has to pay Parker at least $50 an hour for the trip to pick it up (EV, so driving costs next to
# nothing) and about 1.5 hours of listing, messages and handing it over.
FLIP_HOURLY = 50
SELL_HOURS = 1.5
# Rough round-trip hours from home on Sauvie Island by the Craigslist location text; unknown places count as 1.5.
TRIP_HOURS = [
    (r"scappoose|st\.? helens|sauvie|linnton|st\.? johns|north portland|\bn portland\b|kenton", 0.75),
    (r"portland|\b(ne|nw|se|sw|n)\b|pdx|beaverton|tigard|milwaukie|lake oswego|vancouver|hazel dell|cedar mill|bethany|"
     r"aloha|gresham|clackamas|happy valley|tualatin|west linn|hillsboro|camas|troutdale|fairview", 1.5),
    (r"oregon city|sherwood|wilsonville|forest grove|cornelius|battle ground|washougal|ridgefield|sandy|estacada|"
     r"canby|newberg|woodland|kelso|longview|vernonia|banks|boring|damascus|gladstone", 2.25),
    (r"salem|keizer|mcminnville|woodburn|silverton|hood river|the dalles|astoria|seaside|tillamook|centralia|"
     r"chehalis|dallas|monmouth|albany|corvallis|eugene", 3.5),
]


def trip_hours(where):
    return next((h for pat, h in TRIP_HOURS if re.search(pat, where or "", re.I)), 1.5) if where else 1.5
# A part or accessory for a model is not the model: skip the price list for these.
ACCESSORY = re.compile(r"\b(throne|stand|case|gig ?bag|bag|strap|cover|pickguard|pickups?|neck|body|tuners?|knobs?|"
                       r"hardware|pedal board|footswitch|cable|parts?|manual|box only)\b", re.I)  # a snare or tom is the item itself


def _get(url, headers=UA):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read().decode("utf-8", "replace")


def _text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def listings(search=SEARCH, queries=WATCH_QUERIES, min_price=40):
    """Newest listings with a price from a Craigslist category's no-script search results (musical instruments
    unless told otherwise), plus a search for each watched item so an older listing for one isn't missed."""
    out, seen = [], set()
    for extra in [{}] + [{"query": q} for q in queries]:
        try:
            page = _get(search + "?" + urllib.parse.urlencode({"sort": "date", "min_price": min_price, **extra}))
        except Exception:
            if not extra:
                raise
            continue
        for block in re.findall(r'<li class="cl-static-search-result"(.*?)</li>', page, re.S):
            link = re.search(r'href="([^"]+)"', block)
            title = re.search(r'class="title">(.*?)</div>', block, re.S)
            price = re.search(r'class="price">\s*\$([\d,]+)', block)
            where = re.search(r'class="location">(.*?)</div>', block, re.S)
            if not (link and title and price) or link.group(1) in seen:
                continue
            seen.add(link.group(1))
            out.append({"title": _text(title.group(1)), "price": int(price.group(1).replace(",", "")),
                        "url": link.group(1), "where": _text(where.group(1)) if where else None})
    if not out:
        raise RuntimeError("Craigslist returned no listings (blocked or the page changed)")
    return out


BRANDS = re.compile(r"\b(fender|squier|gibson|epiphone|prs|ibanez|esp|ltd|jackson|charvel|evh|schecter|gretsch|rickenbacker|"
                    r"martin|taylor|guild|takamine|ovation|yamaha|roland|boss|korg|moog|nord|akai|line ?6|vox|marshall|"
                    r"orange|mesa|boogie|peavey|ampeg|traynor|music ?man|sterling|danelectro|supro|friedman|bogner|soldano|"
                    r"kemper|fractal|shure|sennheiser|neumann|akg|rode|audio[- ]?technica|electro[- ]?voice|focusrite|"
                    r"presonus|universal audio|apogee|motu|behringer|arturia|novation|elektron|sequential|strymon|"
                    r"electro[- ]?harmonix|ehx|mxr|dunlop|walrus|earthquaker|chase bliss|eventide|keeley|jhs|digitech|"
                    r"zoom|tascam|ludwig|tama|pearl|dw|sabian|zildjian|meinl|paiste|remo|alesis|kawai|casio|hammond|"
                    r"leslie|wurlitzer|rhodes|mackie|jbl|qsc|warwick|spector|lakland|aguilar|darkglass|fishman|deering|"
                    r"gold tone|hohner|washburn|kramer|heritage|cort|reverend|silvertone|harmony|teisco|hagstrom|dean|"
                    r"suhr|collings|eastman|ernie ball|markbass|tech 21|radial|neve|warm audio|dbx|lexicon|"
                    r"keith mcmillen|kmi|sonor|mapex|istanbul|agop|bosphorus|latin percussion|lp|gon bops|toca|"
                    r"rogers|slingerland|premier|craviotto|c&c|canopus|sakae|noble|cooley|q drum|schlagwerk|evans|"
                    r"aquarian|natal|ufip|dream|zildjian|stagg)\b", re.I)
# Words that say what kind of thing it is, or its condition or color, not which model it is.
GENERIC = re.compile(r"(?i)guitars?|bass(es)?|electric|acoustic|amp(lifier)?s?|heads?|cab(inet)?s?|combo|tube|valve|solid|"
                     r"state|hollow|semi|body|vintage|drums?|kit|set|pedals?|effects?|keyboards?|synth(esizer)?|piano|"
                     r"digital|analog|mic(rophone)?s?|interface|mixer|speakers?|monitors?|stereo|mono|with|and|the|for|of|"
                     r"in|w|plus|black|white|red|blue|green|sunburst|natural|finish|color|left|handed|lefty|made|japan|"
                     r"usa|mexico|mij|mim|korea|original|rare|clean|nice|works|working|perfect|like|pro|series|edition|"
                     r"model|controller|foot|midi|piece|pc|pcs|shells?|snares?|toms?|cymbals?|percussion|hand|"
                     r"electronic|double|single|pedals?|chain|pack|chrome|brass|steel|aluminum|wood|maple|birch|"
                     r"sparkle|gold|silver|wine|stain|by|to|from|each|all|three|two|one|full|offer|price|reduced|shoot|"
                     r"me|an|a|s|x|inches|included|excellent|logo|case|mount|condition|"
                     r"\d{4}s?|\d+(\.\d+)?(w|watt|watts|in|inch|pc|piece|g)|\d+(\.\d+)?x\d+(\.\d+)?|\d+\.\d+|\d+-piece")


# ---------------------------------------------------------------- matching Craigslist gear to Reverb sales
#
# A comparable has to be the same thing: same brand, every model word in the Craigslist title, no pricier or
# cheaper version word the title doesn't have (Tribute, Special, Custom Shop, Vintera, Murphy Lab...), the same
# kind of gear (Reverb's category), and the same era. When the title gives a year, only sales from about
# that year count; when it doesn't, vintage pieces don't. When the matches still disagree (a "Lonestar 2x12"
# could be the combo or the cabinet), the listing gets no price and the reason is shown instead.

# Spelled the same way on both sides before comparing.
SYNONYMS = [
    (r"\bjr\b\.?", "junior"), (r"\bteles?\b", "telecaster"), (r"\bstrats?\b", "stratocaster"),
    (r"\bgold ?top\b", "goldtop"), (r"\bp[- ]?bass\b", "precision bass"), (r"\bj[- ]?bass\b", "jazz bass"),
    (r"\bsingle[- ]?cut(away)?\b|\bsc\b", "singlecut"), (r"\bdouble[- ]?cut(away)?\b|\bdc\b", "doublecut"),
    (r"\bmk\.? ?(ii|2)\b", "mk2"), (r"\bmk\.? ?(iii|3)\b", "mk3"), (r"\bmk\.? ?(iv|4)\b", "mk4"),
    (r"\bavri\b", "american vintage reissue"), (r"\bre-?issue\b|\bri\b", "reissue"), (r"\bhollow ?body\b", "hollowbody"), (r"\bsemi[- ]?hollow\b", "semihollow"),
    (r"\b12[- ]?string\b", "12string"), (r"\bleft[- ]?handed\b|\blefty\b|\blh\b", "lefthanded"),
    (r"\bextension cab(inet)?\b|\bcab(inet)?\b", "cabinet"), (r"\bthin ?line\b", "thinline"),
    (r"\bstar ?cast(er)?\b", "starcaster"), (r"\bjazz ?master\b", "jazzmaster"), (r"\bjag ?uar\b", "jaguar"),
    (r"\bes[- ]?(\d{3})\b", r"es\1"), (r"\b([a-z]{1,4})-(\d{1,4}[a-z]{0,3})\b", r"\1\2"),
    (r"\b(sm|ac|ds|sd|bd|dd|rv|ch|ce|tu|td|dsl|jcm|ad|ts|mt|gt|me|rc|hx|p|g)\s(\d{1,3}[a-z]{0,2})\b", r"\1\2"),
]
YEAR = re.compile(r"(?<![\d$])(19[3-9]\d|20[0-2]\d)(?!\d)")
DECADE = re.compile(r"(?<!\d)(?:19)?'?([3-9]0)'?s\b", re.I)
# A year after one of these is the model's name, not its age: a "Historic 1957 Les Paul" was made recently.
REISSUE = re.compile(r"\b(reissue|historic|custom shop|vos|tribute|anniversary|vintera|classic vibe|"
                     r"american vintage|avri|original series|'?\d0s (classic|vintage|series)|road worn|replica|re-?creation)\b", re.I)
# Words that make a different (usually pricier or cheaper) version of a model. A comparable carrying one the
# Craigslist title doesn't is a different thing: a "Les Paul Junior Tribute" is not a "Les Paul Junior".
VARIANTS = ("valve tube signature artist custom shop elite ultra professional limited anniversary relic masterbuilt "
            "masterbuild murphy aged mk2 mk3 mk4 deluxe select usa american japan mij cij mexico mim korea indonesia "
            "china vintage original nos vintera player squier affinity bullet classic vibe standard studio tribute "
            "special junior traditional supreme modern faded plus thinline hollowbody semihollow acoustasonic baritone "
            "12string lefthanded mini micro reissue historic vos heavy light worn silverface blackface exclusive "
            "prototype goldtop partscaster copy clone").split()
VARIANT_FAMILY = {"reissue", "historic", "vos", "custom", "shop", "vintage"}  # all fine on a reissue listing
NOT_USED = {"brand-new", "b-stock", "mint-inventory"}  # Reverb ignores condition=used, so this is checked per listing
NOT_USED_TITLE = re.compile(r"\b(demo|open box|b-?stock|blem(ished)?|showroom|new old stock|brand new|factory sealed)\b", re.I)
BUNDLE = re.compile(r"\b(bundle|lot|package|pack|kit|studio set)\b|\+", re.I)
PARTS = re.compile(ACCESSORY.pattern + r"|\b(replacement|switch|battery|potentiometer|pot|keys?|contacts?|jack|pcb|board|"
                   r"power supply|adapter|cord|tubes|strings|decal|faceplate|panel|screws?|only)\b", re.I)
# Words that describe the listing, not the model.
FILLER = re.compile(r"(?i)hardshell|hsc|ohsc|gigbag|gig|bag|upgraded|upgrades?|loaded|shape|beautiful|awesome|amazing|"
                    r"sounds|plays|great|good|local|pickup|cash|trade|trades|firm|obo|or|best|lightly|barely|never|"
                    r"gently|super|sweet|killer|rare|minty|mint|excellent|condition|nice|clean|w|wow|deal|sale|sell|"
                    r"selling|price|reduced|drop|new|used|only|like|look|looks|very|tons|lot|lots|extras|box|boxes")
# Effect types a seller may or may not write ("Boss DS-1" vs "Boss DS-1 Distortion"): fine either way.
OPTIONAL = {"distortion", "overdrive", "delay", "fuzz", "chorus", "compressor", "looper", "boost", "tremolo", "phaser",
            "flanger", "wah", "echo", "analog", "preamp", "di"}
KINDS = {"cabinet": "cabinets", "combo": "combos", "head": "heads", "acoustic": "acoustic", "bass": "bass"}


def _stem(w):
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w[-2].isdigit() else w


def _has(token, have):
    """Whether a model word is among a listing's words: "rockers" matches "rocker", "5410t" matches "g5410t"."""
    t = _stem(token)
    return t in have or any(c.isdigit() for c in t) and len(t) >= 4 and any(h.endswith(t) for h in have)


def _norm(text):
    text = html.unescape(text or "").lower().replace("’", "'")
    for pat, rep in SYNONYMS:
        text = re.sub(pat, rep, text)
    return text


def _words(text):
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", _norm(text))


def _years(text):
    """The year a listing gives, as a (low, high) range, or None. "1960s" and "'60s" mean the decade."""
    d = re.search(r"(?<!\d)(19[3-9]0)'?s\b", text or "")
    if d:
        return int(d.group(1)), int(d.group(1)) + 9
    y = YEAR.search(text or "")
    if y:
        return int(y.group(1)), int(y.group(1))
    d = DECADE.search(text or "")
    return (1900 + int(d.group(1)), 1909 + int(d.group(1))) if d else None


def _comp_year(x):
    """When a Reverb listing was made: its year field, else a year in its title. None when it doesn't say, or
    gives a model-era span ("1950-Current", "2019 - Present") rather than a year."""
    field = (x.get("year") or "").strip()
    got = re.findall(r"(19[3-9]\d|20[0-2]\d)", field)
    if got and not re.search(r"current|present|now", field, re.I):
        lo, hi = int(got[0]), int(got[-1])
        return (lo, hi) if hi - lo <= 6 else None
    title = x.get("title") or ""
    if REISSUE.search(title):
        return None
    return _years(title)


def want(title):
    """What a matching sale must be, from a Craigslist title, or a reason it can't be priced."""
    cut = re.split(r"\s(?:w/|with|\+|&|includes|including|comes with)\s", title, maxsplit=1, flags=re.I)[0]
    cut = re.sub(r"\$[\d.,]+|\b[\d,]+\.\d\d\b|\bfrom \$?\d+", " ", cut)  # prices in the title
    brand = BRANDS.search(cut)
    if not brand:
        return {"skip": "no brand in the title"}
    words = _words(cut)
    brand_words = set(_words(brand.group(0)))
    tokens = []
    for w in words:
        if w in brand_words or GENERIC.fullmatch(w) and not (re.fullmatch(r"\d{4}", w) and not YEAR.fullmatch(w)) or FILLER.fullmatch(w) or w in tokens or len(w) < 2 and not w.isdigit():
            continue
        if YEAR.fullmatch(w) or re.fullmatch(r"'?(19)?\d0s", w) or w in OPTIONAL:
            continue
        tokens.append(w)
    if not any(re.search(r"[a-z]", t) for t in tokens):
        return {"skip": "the title names a brand but no model"}
    reissue = bool(REISSUE.search(_norm(cut)))
    if reissue:  # "Custom Shop 1957 Les Paul Reissue" and "Historic '57 Les Paul" are the same guitar
        tokens = [t for t in tokens if t not in VARIANT_FAMILY] or tokens
    era = None if reissue else _years(cut)
    year_token = YEAR.search(cut).group(1) if reissue and YEAR.search(cut) else None
    if not era and not reissue and re.search(r"\bvintage\b", cut, re.I):
        return {"skip": "says vintage but not what year"}
    return {"brand": brand.group(0).lower(), "tokens": tokens, "words": set(words), "era": era, "reissue": reissue,
            "year_token": year_token, "accessory": bool(ACCESSORY.search(cut)), "kind": next((KINDS[w] for w in words if w in KINDS), None)}


def _category(x):
    return ((x.get("categories") or [{}])[0].get("full_name") or "").strip()


def _slug(category):
    top = category.split("/")[0].strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", top.replace("&", "and")).strip("-")


def _matches(x, w, optional=frozenset()):
    """Why this Reverb listing is not the same used thing as the Craigslist one, or None if it is."""
    price = x.get("price") or {}
    if not price.get("amount") or price.get("currency", "USD") != "USD":
        return "not priced in dollars"
    title = x.get("title") or ""
    if (x.get("condition") or {}).get("slug") in NOT_USED or NOT_USED_TITLE.search(title):
        return "new, demo or B-stock"
    text = f"{title} {x.get('make') or ''} {x.get('model') or ''}"
    have = set(_words(text))
    stems = {_stem(h) for h in have}
    if w["brand"] not in _norm(text):
        return "other brand"
    missing = [t for t in w["tokens"] if not _has(t, stems) and t not in optional]
    if missing:
        return "missing " + " ".join(missing)
    extra = [v for v in VARIANTS if v in have and v not in w["words"] and not (w["reissue"] and v in VARIANT_FAMILY)]
    if extra:
        return "a different version (" + extra[0] + ")"
    # A model year in the name ("'69 Telecaster Thinline") is a reissue of that year, not the plain model.
    if not w["reissue"] and re.search(r"(?<![\w$])'\d\d\b|\b(19)?[5-7]\d's?\s+(custom|reissue|classic|vintage|series)", _norm(title)):
        return "a different version (a reissue)"
    # Reverb's model field names the model plainly; two or more words in it the Craigslist title lacks
    # ("Jim Adkins JA-90 Telecaster Thinline" for a "Thinline Telecaster") make it a different model.
    mine = {_stem(t) for t in w["words"]} | {_stem(t) for t in optional}
    odd = [t for t in _words(x.get("model")) if _stem(t) not in mine and not GENERIC.fullmatch(t) and not FILLER.fullmatch(t)
           and t not in OPTIONAL and not YEAR.fullmatch(t) and t not in _words(x.get("make")) and t not in _words(x.get("finish"))
           and not BRANDS.fullmatch(t)]
    if len(odd) >= 2:
        return "a different model (" + " ".join(odd[:3]) + ")"
    if BUNDLE.search(title) and not BUNDLE.search(" ".join(w["words"])):
        return "a bundle"
    if PARTS.search(title) and not w["accessory"]:
        return "a part or accessory"
    if _category(x).startswith("Accessories") and not w["accessory"]:
        return "an accessory"
    made = _comp_year(x)
    if w["era"]:
        lo, hi = w["era"]
        pad = 2 if lo < 1990 else 3
        if not made or made[1] < lo - pad or made[0] > hi + pad:
            return "from another era" if made else "year unknown"
    elif made and made[0] < 1985 and not w["reissue"]:  # a reissue's own model year is checked below
        return "vintage"
    if w["reissue"] and (not REISSUE.search(_norm(text)) or made and made[0] < 1985):
        return "an original, not a reissue"
    if w["year_token"] and not re.search(r"(19)?'?" + w["year_token"][2:] + r"\b", title):
        return "another reissue year"
    return None


def _reverb_page(query, page, sold=False, **extra):
    params = {"query": query, "per_page": 50, "page": page, **extra}
    if sold:  # sold listings, newest first; the public API has no sale date, so the listing date stands in for it
        params |= {"show_only_sold": "true", "sort": "published_at|desc"}
    data = json.loads(_get("https://api.reverb.com/api/listings/all?" + urllib.parse.urlencode(params),
                           {**UA, "Accept": "application/hal+json", "Accept-Version": "3.0"}))
    return data.get("listings") or []


def _trim(prices):
    """Drop a $5 badge or an odd one out: anything under half or over twice the middle."""
    if not prices:
        return prices
    mid = sorted(prices)[len(prices) // 2]
    return [p for p in prices if mid / 2 <= p <= mid * 2]


RECENT_DAYS = 90
MIN_SALES = 4


def _sell_time(days):
    return ("about a week" if days <= 10 else "about 2 weeks" if days <= 21 else "about a month" if days <= 45
            else "1 to 3 months" if days <= 90 else "over 3 months")


def _sale(x):
    return {"price": round(float(x["price"]["amount"])), "title": (x.get("title") or "").strip(),
            "url": ((x.get("_links") or {}).get("web") or {}).get("href"), "date": (x.get("published_at") or "")[:10] or None,
            "category": _category(x)}


def comps(title, today=None, log=None):
    """What gear matching this Craigslist title sold for on Reverb, or {"unsure": reason}.

    Returns the median sale (the price used to judge the deal), the most recent sale, the average of up to 30,
    a few of the sales it matched so the card can show what it compared with, and how fast it sells."""
    today = today or datetime.date.today()
    w = want(title)
    if w.get("skip"):
        return {"unsure": w["skip"]}
    query = " ".join([w["brand"]] + w["tokens"][:5] + ([w["year_token"]] if w["year_token"] else []))
    extra = {}
    if w["era"]:
        lo, hi = w["era"]
        pad = 2 if lo < 1990 else 3
        extra = {"year_min": lo - pad, "year_max": hi + pad}
    first = _reverb_page(query, 1, sold=True, **extra)
    optional = frozenset(t for x in first for t in _words(x.get("finish")))  # a finish named in the title is optional
    hits = [x for x in first if not _matches(x, w, optional)]
    if not hits and len(first) == 50:
        # Cases and parts can crowd the newest sales ("les paul junior" is mostly cases): look again within the
        # kind of gear the results that name the model are.
        named = [_category(x) for x in first if all(t in _words(f"{x.get('title')} {x.get('model')}") or t in optional
                                                    for t in w["tokens"]) and not _category(x).startswith("Accessories")]
        if named:
            first = _reverb_page(query, 1, sold=True, product_type=_slug(max(set(named), key=named.count)), **extra)
            optional |= frozenset(t for x in first for t in _words(x.get("finish")))
            hits = [x for x in first if not _matches(x, w, optional)]
    if not hits:
        why = {}
        for x in first:
            r = _matches(x, w, optional)
            why[r] = why.get(r, 0) + 1
        return {"unsure": "no Reverb sales of this exact model" + (f" ({len(first)} close ones were " +
                max(why, key=why.get) + ")" if first else "")}
    # Narrow to the kind of gear the matches are (Electric Guitars, Amps...), then read more pages of it.
    cats = {}
    for x in hits:
        cats[_category(x)] = cats.get(_category(x), 0) + 1
    top = max(cats, key=cats.get)
    sold = [x for x in first]
    if len(first) == 50:
        for page in (1, 2, 3):
            got = _reverb_page(query, page, sold=True, product_type=_slug(top), **extra)
            sold += got
            if len(got) < 50:
                break
    seen, sales = set(), []
    stale = (today - datetime.timedelta(days=3 * 365)).isoformat()
    for x in sold:
        if x.get("id") in seen or (x.get("published_at") or "")[:10] < stale or _matches(x, w, optional):
            continue
        seen.add(x.get("id"))
        sales.append(_sale(x))
    if not sales:
        return {"unsure": "no matching Reverb sales in the last 3 years"}
    sales.sort(key=lambda s: s["date"] or "", reverse=True)  # newest first, across the pages read
    # Same kind of thing: when the sales split between categories (combo vs. cabinet), the title has to say which.
    # A sale filed only under a parent ("Amps", "Effects and Pedals") could be either, so it's left out when
    # others name the exact kind.
    found = {s["category"] for s in sales}
    parent = lambda c: any(o.startswith(c + " /") for o in found)  # noqa: E731
    sales = [s for s in sales if not parent(s["category"])]
    cats = {}
    for s in sales:
        cats[s["category"]] = cats.get(s["category"], 0) + 1
    top = max(cats, key=cats.get)
    if cats[top] < 0.75 * len(sales):
        hinted = [c for c in cats if w["kind"] and w["kind"] in c.lower()]
        if hinted:
            top = hinted[0]
        else:
            two = sorted(cats, key=cats.get, reverse=True)[:2]
            return {"unsure": "Reverb sales under this name mix " + " and ".join(c.split("/")[-1].strip() for c in two)
                    + " and the title doesn't say which"}
    sales = [s for s in sales if s["category"] == top]
    kept = set(_trim([s["price"] for s in sales]))
    sales = [s for s in sales if s["price"] in kept]
    if len(sales) < MIN_SALES:
        return {"unsure": f"only {len(sales)} matching Reverb sale{'s' if len(sales) != 1 else ''} in 3 years, too few to price it"}
    prices = sorted(s["price"] for s in sales[:30])
    q1, q3 = prices[len(prices) // 4], prices[(3 * len(prices)) // 4]
    if q3 > 2.2 * q1:
        return {"unsure": f"matching Reverb sales run from ${q1:,} to ${q3:,}, likely different versions"}
    median = prices[len(prices) // 2]
    # How fast it sells: matching sales listed in the last 90 days against matching used listings up now.
    cutoff = (today - datetime.timedelta(days=RECENT_DAYS)).isoformat()
    recent = sum(1 for s in sales if (s["date"] or "") >= cutoff)
    live = []
    for page in (1, 2):
        got = _reverb_page(query, page, product_type=_slug(top), **extra)
        live += [x for x in got if not _matches(x, w, optional)]
        if len(got) < 50:
            break
    active = len(live)
    days = active / (recent / RECENT_DAYS) if recent else None
    speed = None if days is None else "fast" if days <= 21 else "steady" if days <= 60 else "slow"
    last, avg_of = sales[0], sales[:30]
    return {"typical": median, "n": len(avg_of), "category": top,
            "last": last["price"], "last_title": last["title"], "last_url": last["url"], "last_date": last["date"],
            "avg": round(sum(s["price"] for s in avg_of) / len(avg_of)),
            "examples": [{k: s[k] for k in ("price", "title", "url", "date")} for s in sales[:3]],
            "recent": recent, "recent_days": RECENT_DAYS, "active": active,
            "speed": speed or "slow", "sell_time": _sell_time(days) if days is not None else None,
            "query": query, "url": "https://reverb.com/marketplace?" + urllib.parse.urlencode({"query": query, "show_only_sold": "true"})}


def deals(found, cache, reverb_budget=25, today=None):
    """Score each listing against what the same gear sold for on Reverb. cache keeps lookups for 3 days."""
    today = today or datetime.date.today()
    fresh = (today - datetime.timedelta(days=3)).isoformat()
    out, unsure = [], []
    watched = lambda t: next((label for pat, label in WATCH if pat.search(t)), None)  # noqa: E731
    # Watched items, then drums and percussion, get the Reverb lookups first when there are more listings than budget.
    for item in sorted(found, key=lambda x: (not watched(x["title"]), not DRUMS.search(x["title"]), -x["price"])):
        title = item["title"]
        if SKIP.search(title):
            continue
        watch = watched(title)
        key = "v5 " + " ".join(_words(title))
        hit = cache.get(key)
        if not (hit and hit.get("at", "") >= fresh):
            if item["price"] < 100 and not watch:
                continue
            if want(title).get("skip"):
                continue  # "hollow body electric guitar" has nothing fair to compare against
            if reverb_budget <= 0:
                continue
            reverb_budget -= 1
            try:
                hit = cache[key] = {"at": today.isoformat(), "comp": comps(title, today)}
            except Exception:  # noqa: BLE001
                continue
        comp = hit["comp"]
        if comp.get("unsure"):
            unsure.append({"title": title, "price": item["price"], "url": item["url"], "why": comp["unsure"]})
        scored = _score(item, comp, watch) if comp.get("typical") or watch else None
        if scored:
            out.append((item, comp, watch, scored))
    for k in list(cache)[:-600]:
        cache.pop(k)
    # The search page can be wrong about the price ("from $225" when the ride is $400), so the post itself
    # is read for each one that would show, and its price is the one that counts.
    out.sort(key=lambda t: _rank(t[3]))
    picks = []
    for item, comp, watch, scored in out[:25]:
        post = read_post(item["url"])
        if post and post["gone"]:
            continue
        if post and post["price"] and post["price"] != item["price"]:
            item = item | {"price": post["price"], "listed_price": item["price"]}
            scored = _score(item, comp, watch)
        if scored:
            picks.append(scored | {"post_checked": bool(post)})
        if len(picks) >= 15:
            break
    deals.unsure = unsure
    return sorted(picks, key=_rank)


deals.unsure = []  # listings looked up in the last scan that couldn't be priced with confidence, and why


def _rank(x):
    # Wish-list items first, then flips by what they pay per hour, then drums, then the rest by discount.
    return (not x["watch"], -(x.get("flip_hourly") or 0), not x["drums"], -(x["pct_off"] or 0))


def _score(item, ref, watch):
    """The deal as shown, or None if it isn't one at this price. resale_* say what reselling it would pay even
    when that's under the flip bar, so the card can say so."""
    drums = bool(DRUMS.search(item["title"]))
    if not ref or not ref.get("typical"):  # on the wish list: worth a look even with nothing to price it against
        return item | {"typical": None, "basis": None, "pct_off": None, "drums": drums, "flip_profit": None,
                       "flip_hourly": None, "resale_profit": None, "resale_hourly": None, "watch": watch}
    ratio = item["price"] / ref["typical"]
    profit = round(ref["typical"] * RESALE - item["price"])
    hourly = round(profit / (trip_hours(item.get("where")) + SELL_HOURS))
    # Any gear at all, if it would resell at a profit worth the trouble and the time.
    flip = profit >= FLIP_PROFIT and hourly >= FLIP_HOURLY
    if not (watch or ((flip or ratio <= (DRUM_DEAL if drums else DEAL)) and ratio >= 0.3)):  # far below: a part, a typo, a scam or not the same thing
        return None
    sold = {k: v for k, v in ref.items() if k not in ("typical", "category", "query")}
    return item | {"typical": ref["typical"], "basis": f"middle of {ref['n']} matching used sales on Reverb", "sold": sold,
                   "pct_off": round(100 * (1 - ratio)), "drums": drums,
                   "flip_profit": profit if flip else None, "flip_hourly": hourly if flip else None,
                   "resale_profit": profit, "resale_hourly": hourly, "watch": watch}


def read_post(url):
    """The price on the post itself, and whether it's sold, pending or gone. None if the page can't be read."""
    try:
        page = _get(url)
    except urllib.error.HTTPError as e:
        return {"price": None, "gone": e.code in (404, 410)}
    except Exception:
        return None
    price = re.search(r'class="price">\s*\$([\d,]+)', page)
    body = re.search(r'<section id="postingbody">(.*?)</section>', page, re.S)
    text = _text(body.group(1)) if body else ""
    gone = bool(re.search(r"this posting has (been deleted|expired)|flagged for removal", page, re.I)
                or re.search(r"\b(sold|sale pending|pending sale|pending pickup)\b", text[:300], re.I))
    return {"price": int(price.group(1).replace(",", "")) if price else None, "gone": gone}
