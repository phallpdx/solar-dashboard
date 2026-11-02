"""Underpriced music gear on Portland Craigslist (musical instruments, "msa").

Listings come from Craigslist's no-script search page. Each asking price is compared with what that
piece of gear usually sells for used: a rough used price from the list below for well-known models,
otherwise the low end of matching used listings on Reverb. Reverb is only asked when the title names a
brand and a model, and only listings whose titles carry that model count, so "hollow body electric guitar"
is never priced against $1,200 guitars. Asking prices run above what gear sells for, so the lower
quartile stands in for the usual price. Anything at 70% or less of it is a deal.
"""
import html
import json
import re
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
# A part or accessory for a model is not the model: skip the price list for these.
ACCESSORY = re.compile(r"\b(throne|stand|case|gig ?bag|bag|strap|cover|pickguard|pickups?|neck|body|tuners?|knobs?|"
                       r"hardware|pedal board|footswitch|cable|parts?|manual|box only)\b", re.I)  # a snare or tom is the item itself

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
    (r"alesis.*(nitro|surge|strike)", "Alesis e-kit", 250),    (r"yamaha.*p-?(45|125|145|225)", "Yamaha P-series piano", 400),
    (r"nord (stage|electro|piano)", "Nord keyboard", 1800),
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
    """Newest instrument listings with a price, from the no-script search results, plus a search for each
    watched item so an older listing for one isn't missed."""
    out, seen = [], set()
    for extra in [{}] + [{"query": q} for q in WATCH_QUERIES]:
        try:
            page = _get(SEARCH + "?" + urllib.parse.urlencode({"sort": "date", "min_price": 40, **extra}))
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


def _query(title):
    title = re.sub(r"\$[\d.,]+|\b[\d,]+\.\d\d\b", " ", title)  # prices in the title
    words = re.sub(r"[^\w\s-]", " ", title).split()
    return " ".join(w for w in words if not re.fullmatch(r"(?i)obo|firm|\$[\d.,]+|[\d,]+\.\d\d|mint|great|excellent|condition|sale|new|used", w))[:60]


def _model_words(query):
    """The words that name the model once the brand and the kind of gear are taken out ("spider", "2")."""
    return [w.lower() for w in BRANDS.sub(" ", query).split() if re.search(r"[a-z0-9]", w, re.I) and not GENERIC.fullmatch(w)]


NOT_USED = {"brand-new", "b-stock", "mint-inventory"}  # Reverb ignores condition=used, so this is checked per listing
BUNDLE = re.compile(r"\b(bundle|lot|package|pack|kit|studio)\b|\+", re.I)
PARTS = re.compile(ACCESSORY.pattern + r"|\b(replacement|switch|battery|potentiometer|pot|keys?|contacts?|jack|pcb|board|"
                   r"power supply|adapter|cord|tubes|strings|decal|faceplate|panel|screws?|only)\b", re.I)


def _reverb(query, model):
    """Lower-quartile asking price of used Reverb listings whose titles carry the model words, or None if too few.
    New, B-stock and bundled listings don't count, since they are what made the old medians run high."""
    prices = []
    for page in (1, 2, 3):
        data = json.loads(_get("https://api.reverb.com/api/listings/all?" + urllib.parse.urlencode(
            {"query": query, "per_page": 50, "page": page}),
            {**UA, "Accept": "application/hal+json", "Accept-Version": "3.0"}))
        for x in data.get("listings") or []:
            title = (x.get("title") or "").lower()
            if ((x.get("price") or {}).get("amount") and (x.get("price") or {}).get("currency", "USD") == "USD"
                    and (x.get("condition") or {}).get("slug") not in NOT_USED
                    and not (BUNDLE.search(title) and not BUNDLE.search(query))
                    and not (PARTS.search(title) and not PARTS.search(query))
                    and all(re.search(r"\b" + re.escape(w) + r"\b", title) for w in model[:3])):
                prices.append(float(x["price"]["amount"]))
        if len(prices) >= 12 or len(data.get("listings") or []) < 50:
            break
    if prices:  # a $5 badge or a single drum out of a "kit" search is not the thing itself
        mid = sorted(prices)[len(prices) // 2]
        prices = [p for p in prices if mid / 3 <= p <= mid * 3]
    prices.sort()
    return (prices[len(prices) // 4], len(prices)) if len(prices) >= 5 else None


def deals(found, cache, reverb_budget=25):
    """Score each listing against a typical used price. cache keeps Reverb lookups between runs."""
    out = []
    watched = lambda t: next((label for pat, label in WATCH if pat.search(t)), None)  # noqa: E731
    # Watched items, then drums and percussion, get the Reverb lookups first when there are more listings than budget.
    for item in sorted(found, key=lambda x: (not watched(x["title"]), not DRUMS.search(x["title"]))):
        title = item["title"]
        if SKIP.search(title):
            continue
        watch = watched(title)
        match = None if ACCESSORY.search(title) else next(((name, price) for pat, name, price in MODELS if re.search(pat, title, re.I)), None)
        ref = {"typical": match[1], "basis": f"usual used price for a {match[0]}"} if match else None
        q = _query(title).lower()
        model, key = _model_words(q), "v3 " + q  # older cache entries came from looser matches
        if ref or not (BRANDS.search(q) and model):
            pass  # a title like "hollow body electric guitar" has nothing fair to compare against
        elif key in cache:
            ref = cache[key]
        elif reverb_budget > 0 and item["price"] >= 100:
            reverb_budget -= 1
            try:
                # Brand and model only: Reverb wants every word, and sellers word the rest differently.
                got = _reverb(f"{BRANDS.search(q).group(0)} {' '.join(model[:3])}", model)
                cache[key] = ref = {"typical": round(got[0]), "basis": f"low end of {got[1]} matching used listings on Reverb"} if got else None
            except Exception:
                pass
        drums = bool(DRUMS.search(title))
        if not ref or not ref["typical"]:
            if watch:  # on the wish list: worth a look even with nothing to price it against
                out.append(item | {"typical": None, "basis": None, "pct_off": None, "drums": drums, "flip_profit": None, "watch": watch})
            continue
        ratio = item["price"] / ref["typical"]
        profit = round(ref["typical"] * RESALE - item["price"])
        if watch or (ratio <= (DRUM_DEAL if drums else DEAL) and ratio >= 0.15):  # far below usually means a part, a typo or a scam
            out.append(item | {"typical": ref["typical"], "basis": ref["basis"], "pct_off": round(100 * (1 - ratio)),
                               "drums": drums, "flip_profit": profit if profit >= FLIP_PROFIT else None, "watch": watch})
    for k in list(cache)[:-400]:
        cache.pop(k)
    # Wish-list items first, then flips worth the trouble, then drums, then the rest by discount.
    return sorted(out, key=lambda x: (not x["watch"], -(x["flip_profit"] or 0), not x["drums"], -(x["pct_off"] or 0)))[:15]
