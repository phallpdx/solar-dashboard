"""The Evening Edition: a short bedtime read for the Kindle, a sibling of the Morning Edition.

Cover, the day's three biggest stories, one from close to home, tomorrow's weather, tonight's
sky, a poem and a quiet close: about nine pages, five or six minutes. It uses the Morning
Edition's type, chrome, pager and Sections navigator (solar/kindle_full.py), with no pictures
and no section fronts.

Story summaries come from web/evening.json, written each evening by the local model on
Parker's PC (local/refresh_lists.py, list "evening"). Without a fresh one, the feed summaries
are used instead. The editorial rules (what goes in, the order, the tone) came from a
sleep-psychology review: close the day's loops, end calm, never a reason to stay up late.

    python -m solar.kindle_evening data/dashboard.json web/evening.json _site
"""
import datetime as dt
import html
import json
import math
import os
import re
import sys

from . import bedtime_poems, evening
from .kindle_full import EINK_CSS, page, self_host_fonts, _JUMP, _TITLES, BUILD

TZ = evening.TZ
E = html.escape

EVENING_CSS = r"""
/* ===== The Evening Edition: the Morning Edition's quieter sibling ===== */
.kcontents #kmain .kname{font-style:italic !important}
.kcontents #kmain .kdate{border-top:1px solid #000 !important}
.kcontents #kmain .kgl{display:flex;align-items:center}
.kcontents #kmain .kgl .kdeg{flex:none;width:auto;min-width:130px;display:block}
.kcontents #kmain .kgl .kdeg small{display:block !important;margin:6px 0 0 !important;white-space:nowrap}
.kcontents #kmain .kgl .kwx{flex:1 1 auto;margin:0 0 0 22px !important;font:italic 430 var(--t3)/var(--l3) var(--k-serif) !important}
#kmain .kevrest{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;color:var(--ink2) !important;margin:var(--s2) 0 0 !important}
#kmain h2.khed{font:700 var(--t2)/var(--l2) var(--k-serif) !important;letter-spacing:-.01em;margin:0 0 var(--s2) !important}
#kmain .kbody p{margin:0 0 var(--s2) !important}
#kmain .knextstep{border-top:1px solid var(--hair);padding-top:var(--s1) !important}
#kmain .knextstep b,#kmain .kwarn b,#kmain .ksky b{display:block;font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase}
#kmain .ksources{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;color:var(--ink2) !important}
#kmain .kover{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;border-top:1px solid #000;padding-top:var(--s2) !important;margin-top:var(--s3) !important}
#kmain .kwarn{border-top:2px solid #000;border-bottom:1px solid #000;padding:var(--s1) 0 !important}
#kmain .kplan,#kmain .kchoice{font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important}
#kmain .kchoice{border-top:1px solid #000;padding-top:var(--s2) !important;margin-top:var(--s2) !important}
#kmain ul.ksky{list-style:none !important;padding:0 !important;margin:0 0 var(--s2) !important;border-top:1px solid #000}
#kmain .ksky li{border-bottom:1px solid var(--hair);padding:7px 0 !important;margin:0 !important}
#kmain .kquiet{font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important;margin-top:var(--s3) !important;border-top:1px solid var(--hair);padding-top:var(--s2) !important}
#kmain .kfrontwx .kdeg small{font-style:italic !important}
#kmain .poem-text .gap{height:var(--l4)}
#kmain .kend .kfsub{border-bottom:0 !important}
"""

ALARM = re.compile(r"\b(breaking|urgent|shocking|slams?|chaos|deadly|crisis|developing|live|exclusive|horrific|massive)\b", re.I)
# Stories that make poor bedtime reading unless they're the day's biggest by far.
GRAPHIC = re.compile(r"\b(kill(s|ed|ing)?|dead|deaths?|dies|died|murder\w*|shoot\w*|shot|stab\w*|buried alive|rape\w*|"
                     r"abuse\w*|massacre|bodies|body|corpse|hit-and-run|gunman|assault\w*|torture\w*|molest\w*|child porn\w*|"
                     r"overdose\w*|suicide|injur\w*|wounded|trapped|bomb\w*|attack\w*)\b", re.I)
ROUND = [5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
PREFER = ["AP", "Associated Press", "Reuters", "NPR", "PBS NewsHour", "BBC", "The Guardian", "The New York Times",
          "The Washington Post", "Axios", "CBS News", "ABC News", "NBC News", "Politico", "Al Jazeera"]


def outlets_line(st):
    n = st.get("coverage") or 0
    names = [st.get("source")] + [a.get("source") if isinstance(a, dict) else a for a in st.get("also") or []]
    names = [x for x in dict.fromkeys(names) if x]
    names.sort(key=lambda x: PREFER.index(x) if x in PREFER else 99)
    top = names[:3]
    if n <= 1 or not top:
        return f"Source: {E(st.get('source') or 'news reports')}."
    listed = top[0] if len(top) == 1 else ", ".join(top[:-1]) + " and " + top[-1]
    if n < 5:
        return f"Covered by {n} outlets, including {E(listed)}." if n > len(top) else f"Covered by {E(listed)}."
    about = min(ROUND, key=lambda r: abs(r - n))
    return f"Covered by about {about} outlets, including {E(listed)}."


def _fresh(ev, night, now):
    if not ev or ev.get("date") != night.isoformat():
        return False
    try:
        written = dt.datetime.fromisoformat(ev["written_at"].replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return False
    return now - written < dt.timedelta(hours=10)


def _recent(items, now, hours=18):
    out = []
    for it in items or []:
        try:
            t = dt.datetime.fromisoformat(it["utc"].replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            t = now
        if now - t <= dt.timedelta(hours=hours):
            out.append(it)
    return out


def _from_feed(it, major=False):
    summary = (it.get("summary") or "").strip()
    return {**it, "headline": re.sub(r"\s+", " ", it.get("title") or "").strip(), "paras": [summary] if summary else [],
            "next": None, "major": major}


def pick_feed(items, n):
    """Without the local model: the most-covered stories, leaving out graphic ones unless one is far bigger than the rest."""
    items = sorted(items, key=lambda x: -(x.get("coverage") or 0))
    out = []
    for k, it in enumerate(items):
        text = f"{it.get('title', '')} {it.get('summary', '')}"
        nxt = items[k + 1].get("coverage", 0) if k + 1 < len(items) else 0
        major = (it.get("coverage") or 0) >= max(6, 2 * nxt) and k == 0
        if GRAPHIC.search(text) and not major:
            continue
        out.append(_from_feed(it, major))
        if len(out) >= n:
            break
    return out


def _from_model(st):
    paras = [p for p in (st.get("happened"), st.get("tonight")) if p]
    return {**st, "paras": paras, "next": st.get("next")}


def stories(d, ev, night, now):
    news = d.get("news") or {}
    if _fresh(ev, night, now) and ev.get("stories"):
        big = [_from_model(s) for s in ev["stories"]][:3]
        loc = _from_model(ev["local"]) if ev.get("local") else None
        return big, loc, True
    big = pick_feed(_recent(news.get("big"), now), 3)
    loc = pick_feed(_recent(news.get("local"), now, 24), 1)
    return big, (loc[0] if loc else None), False


def poem_html(p):
    stanzas = p["text"].strip().split("\n\n")
    body = '<div class="gap"></div>'.join("".join(f"<span>{E(line.strip())}</span>" for line in s.split("\n")) for s in stanzas)
    by = E(p["poet"]) + (f" &middot; {p['year']}" if p.get("year") else "")
    return (f'<p class="kkick">Before bed</p><span class="poem-title">{E(p["title"])}</span>'
            f'<span class="poem-by">{by}</span><div class="poem-text">{body}</div>')


def main(dash_path, ev_path, site):
    with open(dash_path) as f:
        d = json.load(f)
    ev = None
    if ev_path and os.path.exists(ev_path):
        try:
            with open(ev_path) as f:
                ev = json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"kindle_evening: ignoring {ev_path} ({e!r})")
    now = dt.datetime.now(dt.timezone.utc)
    if os.environ.get("EVENING_NOW"):  # for previews: build as if at this local time
        now = dt.datetime.fromisoformat(os.environ["EVENING_NOW"]).replace(tzinfo=TZ).astimezone(dt.timezone.utc)
    local = now.astimezone(TZ)
    night = evening.evening_of(local)
    out = os.path.join(site, "evening")
    os.makedirs(out, exist_ok=True)
    font_css, font_links = self_host_fonts(out)
    with open(os.path.join(out, "kindle.css"), "w") as f:
        f.write(font_css + "\n" + EINK_CSS + "\n" + EVENING_CSS)

    big, loc, by_model = stories(d, ev, night, now)
    wx = evening.tomorrow(d, local)
    sky = evening.tonight(d, local)
    morning_poem = (d.get("poem") or {}).get("title")
    poem = bedtime_poems.tonight(night, morning_poem)
    weekday = night.strftime("%A")
    tmr = night + dt.timedelta(days=1)

    # ---- the pages, in reading order: (file, title, part, kicker, body)
    pages = []
    for k, st in enumerate(big, 1):
        pages.append({"file": f"day-{k}.html", "title": st["headline"], "part": "The day", "kick": f"The day &middot; {k} of {len(big)}",
                      "story": st})
    if not big:
        pages.append({"file": "day-1.html", "title": "A quiet day in the news", "part": "The day", "kick": "The day",
                      "body": '<h2 class="khed">It was a quiet day in the news</h2><p>No major story changed today.</p>'})
    if loc:
        pages.append({"file": "local.html", "title": loc["headline"], "part": "Close to home", "kick": "Close to home &middot; Portland",
                      "story": loc})
    over = '<p class="kover">Anything that changes overnight will be in your Morning Edition.</p>'
    pages[-1]["over"] = True

    # Tomorrow
    if wx:
        cells = "".join(f'<div><span class="k">{lab}</span><b>{E(v.replace(" am", "").replace(" pm", ""))}</b></div>'
                        for lab, v in (("Sunrise", wx["sunrise"]), ("Sunset", wx["sunset"])) if v)
        lines = []
        if wx["timing"] or wx["amount"]:
            lines.append(" ".join(x for x in (wx["timing"], wx["amount"]) if x))
        if wx["wind"]:
            lines.append(wx["wind"])
        warn = ""
        if wx["alerts"]:
            warn = f'<p class="kwarn"><b>{E(wx["alerts"][0])}</b>From the National Weather Service. Check the details in the morning.</p>'
        body = (f'<div class="kfrontwx"><div class="kdeg">{wx["hi"]}&deg;<small>low {wx["lo"]}&deg;</small></div>'
                f'<p class="ksum">{E(wx["lead"])}</p></div>'
                + "".join(f"<p>{E(x)}</p>" for x in lines)
                + (f'<div class="kscore">{cells}</div>' if cells else "") + warn
                + f'<p class="kplan">{E(wx["plan"])}</p>')
        title = f"{wx['hi']}° and {wx['sky'] or 'mixed'}"
    else:
        body = ('<h2 class="khed">Tomorrow&rsquo;s forecast didn&rsquo;t come through tonight</h2>'
                '<p>It will be in your Morning Edition.</p>')
        title = "Tomorrow's weather"
    pages.append({"file": "tomorrow.html", "title": "Tomorrow's weather", "part": "Tomorrow",
                  "kick": f"Tomorrow &middot; {tmr:%A, %B} {tmr.day}", "body": body, "toc": title})

    # Tonight's sky
    if sky["clouds"] == "Clouded out":
        body = f'<h2 class="khed">Clouded out tonight</h2><p>{E(sky["later"] or "")}</p>'
    elif sky["items"] or sky["choice"]:
        items = "".join(f"<li><b>{E(k)}</b>{E(v)}</li>" for k, v in sky["items"])
        body = (f'<h2 class="khed">{E(sky["headline"])}</h2>' + (f'<ul class="ksky">{items}</ul>' if items else "")
                + (f'<p class="kchoice">{E(sky["choice"])}</p>' if sky["choice"] else ""))
    else:
        body = None
    if body:
        pages.append({"file": "sky.html", "title": "Tonight's sky", "part": "Tonight's sky",
                      "kick": f"Tonight&rsquo;s sky &middot; {weekday}", "body": body})

    if poem:
        pages.append({"file": "poem.html", "title": poem["title"], "part": "Before bed", "kick": "", "body": poem_html(poem)})
    pages.append({"file": "goodnight.html", "title": "Goodnight", "part": "", "kick": "", "close": True,
                  "body": '<div class="kend"><p class="kkick">The Evening Edition</p><h2 class="kfname">That&rsquo;s the day.</h2>'
                          '<p class="kfsub">Everything else can wait until morning.</p>'
                          '<p class="kquiet">One good thing from today: think of it, then let it go.</p></div>'})

    for pg in pages:
        st = pg.get("story")
        if st:
            nxt = (f'<p class="knextstep"><b>Next</b>{E(st["next"])}</p>' if st.get("next") else "")
            pg["body"] = (f'<h2 class="khed">{E(st["headline"])}</h2><div class="kbody">'
                          + "".join(f"<p>{E(p)}</p>" for p in st["paras"]) + "</div>" + nxt
                          + f'<p class="ksources">{outlets_line(st)}</p>')
        if pg.get("over"):
            pg["body"] += over
        if pg["kick"]:
            pg["body"] = f'<p class="kkick">{pg["kick"]}</p>' + pg["body"]

    # ---- chrome shared with the Morning Edition
    total = len(pages)
    files = [pg["file"] for pg in pages]
    _TITLES.clear()
    _TITLES.update({pg["file"]: pg["title"] for pg in pages})
    _TITLES["index.html"] = "The front"
    _TITLES["tomorrow.html"] = "Tomorrow's weather"
    edition = local.strftime("%-I:%M %p").lower().replace(":00 ", " ")
    gen = d.get("generated_at")
    stamp = E(f"Edition of {edition}")
    BUILD["id"] = f"evening {night.isoformat()} {edition}"

    def first_of(part_names):
        return next((pg["file"] for pg in pages if pg["part"] in part_names), None)

    def navigator(cur):
        pg = next(p for p in pages if p["file"] == cur)
        top = ['<nav id="kjump"><div class="kjtop">']
        if pg["part"] in ("The day", "Close to home"):
            to = first_of(("Tomorrow",))
            if to:
                top.append(f'<a class="kjskip" href="{to}"><small>Skip the news</small>Tomorrow&rsquo;s weather &rsaquo;</a>')
        elif pg["part"] in ("Tomorrow", "Tonight's sky"):
            to = first_of(("Before bed",))
            if to:
                top.append(f'<a class="kjskip" href="{to}"><small>Skip to</small>The poem &rsaquo;</a>')
        top.append('<a class="kjfront" href="index.html"><small>Back to</small>The front</a></div>')
        top.append('<p class="kjh">This evening</p><div class="kjg">')
        top += [f'<a href="{p["file"]}"{" class=\"kjcur\"" if p["file"] == cur else ""}><i>{n}</i>{E(p["title"])}</a>'
                for n, p in enumerate(pages, 1)]
        top.append("</div></nav>")
        return "".join(top)

    for n, pg in enumerate(pages):
        prev = files[n - 1] if n else "index.html"
        nxt = files[n + 1] if n + 1 < total else None
        label = None
        if nxt == "tomorrow.html":
            label = "Next: Tomorrow's weather"
        doc = page(pg["title"], pg["body"], "kev", "kcard" if not pg.get("close") else "ksecfront kendpage",
                   prev=prev, nxt=nxt, stamp=stamp, run_left=E(pg["part"]) if pg["part"] else "&lsaquo; The front",
                   run_right=f"{n + 1} of {total}", fonts=font_links, next_label=label, run_href="index.html",
                   jump=navigator(pg["file"]))
        if pg.get("close"):
            # The last page: nothing after it, and a right tap stays put.
            doc = re.sub(r'<a class="knx"[^>]*>.*?</a>', '<span class="knx"></span>', doc)
            doc = re.sub(r'<a class="knext"[^>]*>.*?</a>', "", doc, flags=re.S)
            doc = doc.replace("else go(NEXT_URL); }", "else if (NEXT_URL) go(NEXT_URL); }")
        with open(os.path.join(out, pg["file"]), "w") as f:
            f.write(doc)

    # ---- the cover
    leads = "".join(f'<a href="{pg["file"]}"><b>{E(pg["title"])}</b></a>'
                    for pg in pages if pg.get("story") and pg["part"] == "The day")
    rest = [x for x, f in (("Portland", "local.html"), ("tomorrow&rsquo;s weather", "tomorrow.html"),
                           ("tonight&rsquo;s sky", "sky.html"), ("a poem", "poem.html")) if f in files]
    rest_txt = (("Then " + (rest[0] if len(rest) == 1 else ", ".join(rest[:-1]) + " and " + rest[-1]) + ". ") if rest else "")
    minutes = max(3, total - 3)
    gl = ""
    if wx:
        gl = (f'<div class="kgl"><div class="kdeg">{wx["hi"]}&deg;<small>Tomorrow &middot; low {wx["lo"]}&deg;</small></div>'
              f'<p class="kwx">{E(wx["lead"])}</p></div>')
    body = (f'<div class="kmast"><div class="kear"><span>Sauvie Island, Ore.</span><span>No. {night.timetuple().tm_yday}</span></div>'
            f'<p class="kname">The Evening Edition</p>'
            f'<p class="kdate">{night:%A, %B} {night.day} &middot; {E(edition)} edition</p></div>'
            + gl
            + (f'<p class="klab">The day</p><div class="kleads">{leads}</div>' if leads else "")
            + f'<p class="kevrest">{rest_txt}About {minutes} minutes.</p>')
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(page("The Evening Edition", body, "kev", "kcontents", nxt=files[0], stamp=stamp, run_left="",
                     run_right="", fonts=font_links, next_label=_TITLES[files[0]]))
    with open(os.path.join(site, "evening.html"), "w") as f:
        f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=evening/index.html">'
                '<a href="evening/index.html">Open the Evening Edition</a>')
    _JUMP[0] = ""
    print(f"kindle_evening: {total} pages for the evening of {night} "
          f"({'local model summaries' if by_model else 'feed summaries'}; data from {gen})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else "_site")
