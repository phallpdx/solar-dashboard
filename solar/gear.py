"""Underpriced music gear on Portland Craigslist (musical instruments, "msa").

Listings come from Craigslist's no-script search page. Each asking price is compared with what that
piece of gear usually sells for used: a rough used price from the list below for well-known models,
otherwise the median of matching used listings on Reverb when Reverb has enough of them. Anything at 70% or less is a deal.
"""
import html
import json
import re
import statistics
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
SEARCH = "https://portland.craigslist.org/search/msa"
SKIP = re.compile(r"\b(wanted|wtb|iso|looking for|lessons?|teacher|repair|rehearsal|studio time|band|trade only|"
                  r"for parts|broken|case only|stand only|rental)\b", re.I)
DEAL = 0.7
# A part or accessory for a model is not the model: skip the price list for these.
ACCESSORY = re.compile(r"\b(throne|stand|case|gig ?bag|bag|strap|cover|pickguard|pickups?|neck|body|tuners?|knobs?|"
                       r"snare|kick|bass drum|tom|hardware|pedal board|footswitch|cable|parts?|manual|box only)\b", re.I)

# (pattern, name, rough used price in dollars). Ballpark used prices; Reverb wins when it has data.
MODELS = [
    (r"american (professional|standard|ultra|original|performer).*strat|strat.*american (professional|standard|ultra|performer)", "Fender American Stratocaster", 1100),
    (r"american (professional|standard|ultra|original|performer).*tele|tele.*american (professional|standard|ultra|performer)", "Fender American Telecaster", 1100),
    (r"(player|mexic|mim).*(strat|tele)|(strat|tele).*(player|mexic|mim)", "Fender Player Strat/Tele", 550),
    (r"squier.*(classic vibe|cv)", "Squier Classic Vibe", 300),
    (r"(american|usa).*(precision|p.?bass)|(precision|p.?bass).*(american|usa)", "Fender American Precision Bass", 1100),
    (r"(american|usa).*jazz bass|jazz bass.*(american|usa)", "Fender American Jazz Bass", 1100),
    (r"(player|mexic|mim).*(precision|jazz) bass|(precision|jazz) bass.*(player|mexic|mim)", "Fender Player bass", 550),
    (r"gibson.*les paul (standard|traditional)", "Gibson Les Paul Standard", 1900),
    (r"gibson.*les paul (studio|tribute|special|junior)", "Gibson Les Paul Studio/Special", 900),
    (r"gibson.*sg", "Gibson SG", 1000),
    (r"gibson.*(es-?335|es 335)", "Gibson ES-335", 2400),
    (r"epiphone.*les paul", "Epiphone Les Paul", 350),
    (r"prs.*\bse\b", "PRS SE", 450),
    (r"rickenbacker.*4003", "Rickenbacker 4003", 1800),
    (r"martin.*d-?28", "Martin D-28", 2100),
    (r"martin.*d-?18", "Martin D-18", 1900),
    (r"taylor.*(114|214)", "Taylor 100/200 series", 650),
    (r"taylor.*(314|414|514)", "Taylor 300-500 series", 1400),
    (r"hot rod deluxe", "Fender Hot Rod Deluxe", 500),
    (r"blues junior", "Fender Blues Junior", 400),
    (r"deluxe reverb", "Fender Deluxe Reverb", 1000),
    (r"twin reverb", "Fender Twin Reverb", 1000),
    (r"vox.*ac-?30", "Vox AC30", 900),
    (r"vox.*ac-?15", "Vox AC15", 550),
    (r"marshall.*dsl ?40", "Marshall DSL40", 450),
    (r"orange.*rockerverb", "Orange Rockerverb", 1300),
    (r"boss.*katana(?!.*\b(go|mini|air)\b)", "Boss Katana", 200),
    (r"line ?6.*helix(?! stomp)", "Line 6 Helix", 1100),
    (r"helix stomp|hx stomp", "Line 6 HX Stomp", 450),
    (r"kemper", "Kemper Profiler", 1300),
    (r"quad cortex", "Neural DSP Quad Cortex", 1400),
    (r"strymon.*(timeline|bigsky|big sky)", "Strymon Timeline/BigSky", 350),
    (r"strymon", "Strymon pedal", 220),
    (r"\bboss\b.*\b(ds|sd|bd|dd|rv|ch|ce|tu)-?\d", "Boss compact pedal", 70),
    (r"shure.*sm-?58", "Shure SM58", 70),
    (r"shure.*sm-?57", "Shure SM57", 70),
    (r"shure.*sm-?7b", "Shure SM7B", 300),
    (r"scarlett.*(2i2|4i4)", "Focusrite Scarlett", 100),
    (r"apollo twin", "UA Apollo Twin", 650),
    (r"roland.*td-?(17|27)", "Roland TD-17/TD-27 kit", 1100),
    (r"alesis.*(nitro|surge|strike)", "Alesis e-kit", 250),
    (r"(ludwig|\bdw\b|tama|pearl|gretsch|yamaha).*(drum ?kit|shell ?pack|\d-piece|\d pc)", "Pro drum kit", 700),
    (r"zildjian.*(k |a custom)|sabian.*(hhx|aax)", "Pro cymbal", 200),
    (r"yamaha.*p-?(45|125|145|225)", "Yamaha P-series piano", 400),
    (r"nord (stage|electro|piano)", "Nord keyboard", 1800),
    (r"(moog|sequential|prophet|korg minilogue|korg prologue|arturia minibrute)", "Synth", 600),
    (r"\bmpc\b", "Akai MPC", 550),
    (r"roland.*juno", "Roland Juno", 700),
]


def _get(url, headers=UA):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read().decode("utf-8", "replace")


def _text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def listings():
    """Newest instrument listings with a price, from the no-script search results."""
    page = _get(SEARCH + "?" + urllib.parse.urlencode({"sort": "date", "min_price": 40}))
    out = []
    for block in re.findall(r'<li class="cl-static-search-result"(.*?)</li>', page, re.S):
        link = re.search(r'href="([^"]+)"', block)
        title = re.search(r'class="title">(.*?)</div>', block, re.S)
        price = re.search(r'class="price">\s*\$([\d,]+)', block)
        where = re.search(r'class="location">(.*?)</div>', block, re.S)
        if not (link and title and price):
            continue
        out.append({"title": _text(title.group(1)), "price": int(price.group(1).replace(",", "")),
                    "url": link.group(1), "where": _text(where.group(1)) if where else None})
    if not out:
        raise RuntimeError("Craigslist returned no listings (blocked or the page changed)")
    return out


def _reverb(query):
    """Median asking price of used Reverb listings for this search, or None if too few."""
    data = json.loads(_get("https://api.reverb.com/api/listings/all?" + urllib.parse.urlencode(
        {"query": query, "condition": "used", "per_page": 24}),
        {**UA, "Accept": "application/hal+json", "Accept-Version": "3.0"}))
    prices = [float(x["price"]["amount"]) for x in data.get("listings") or [] if (x.get("price") or {}).get("amount")]
    return (statistics.median(prices), len(prices)) if len(prices) >= 8 else None


def _query(title):
    words = re.sub(r"[^\w\s-]", " ", title).split()
    return " ".join(w for w in words if not re.fullmatch(r"(?i)obo|firm|\$[\d.,]+|[\d,]+\.\d\d|mint|great|excellent|condition|sale|new|used", w))[:60]


def deals(found, cache, reverb_budget=25):
    """Score each listing against a typical used price. cache keeps Reverb lookups between runs."""
    out = []
    for item in found:
        title = item["title"]
        if SKIP.search(title):
            continue
        match = None if ACCESSORY.search(title) else next(((name, price) for pat, name, price in MODELS if re.search(pat, title, re.I)), None)
        ref = {"typical": match[1], "basis": f"usual used price for a {match[0]}"} if match else None
        q = _query(title).lower()
        if not ref and q in cache:
            ref = cache[q]
        elif not ref and reverb_budget > 0 and item["price"] >= 100 and len(q.split()) >= 2:
            reverb_budget -= 1
            try:
                got = _reverb(q)
                cache[q] = ref = {"typical": round(got[0]), "basis": f"median of {got[1]} used listings on Reverb"} if got else None
            except Exception:
                pass
        if not ref or not ref["typical"]:
            continue
        ratio = item["price"] / ref["typical"]
        if ratio <= DEAL and ratio >= 0.15:  # far below usually means a part, a typo or a scam
            out.append(item | {"typical": ref["typical"], "basis": ref["basis"], "pct_off": round(100 * (1 - ratio))})
    for k in list(cache)[:-400]:
        cache.pop(k)
    return sorted(out, key=lambda x: -x["pct_off"])[:15]
