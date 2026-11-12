"""The Morning Edition's type and its small engraved frames: one type scale, book typography, no bare boxes.

Three jobs, all owned here so the other layers (kindle_full, kindle_present, ornament, kindle_frame) stay as
they are:

1. One type scale (CSS below, appended last to the stylesheet). Every role has one size on every page:

     role       size/leading  why
     display    48/52   the cover nameplate and each section's title page: a part title, seen across the room
     headline   34/40   the page's question or title: the first thing read ("Is the mountain out?", "Good morning").
                        The hand-lettering (solar/lettering.py, via kindle_fast.letter) draws each headline at
                        the size this scale gives its kind (LETTER_SIZES below), the column wide; every headline
                        also carries class .khl and data-khl="<plain text>". 34 rather than 30: a script's
                        x-height is half its size, and the question must still out-rank the bold answer under it.
     figure     44/48   the one key number on a page or tile (53°, ~69 kWh, $32): bold lining figures, so the page
                        answers at a glance before anything is read
     lead       24/30   the answer sentence: second, and smaller than the question.
                        Steps 14-17-20-24 rise by about 1.2 (reading sizes); 24-34-44/48 by about 1.4 (display sizes)
     section    20/26   a section heading inside a page ("Today", "On the prairie"), under an engraved section mark
     value      20/26   a figure in a tile or fact box (7:05 am, 54): bold lining figures, one step above the text
     body       17/25   running text and table rows: about 60 characters to the line in a panel, leading 1.47
     label      17/22   labels, running heads, buttons, statuses: true small caps (smcp) at the body size, so a
                        label has the body's x-height instead of being tiny tracked capitals
     caption    14/20   italic asides: sources, units, dates, notes. The smallest size, kept legible on e-ink

   The page-fit ladder (kfit1..4) may tighten spacing but never changes these sizes.
   Book typography: old-style proportional figures in running text, lining tabular figures in tables, tiles and
   leads; true small caps (Literata's full font, which has smcp/c2sc/onum, replaces Google's cut);
   italic for asides; ligatures and kerning on; curly quotes and apostrophes; opening quotes hang into the margin;
   an engraved initial opens the lead paragraph of each section's first page.

2. Small frames. Every small element with an edge gets an engraved frame drawn for its job by the engraving
   studio (solar/scroll.py, branch claude/engrave-frames; spec in /mnt/project-files/kindle/redesign/frame-spec.md).
   CSS reserves the band (padding) and removes every border; at build time each framed element is measured at
   the Kindle's size and a frame composed for its exact w x h is rasterised to a 16-grey PNG and set behind it,
   from a per-page list (script#kfrm) applied once on load. The chrome's frames (running head, buttons, the
   Sections menu) share one sprite for the whole edition; each page's own frames share one sprite per page,
   placed with background-position, so a page load fetches two pictures instead of dozens. Frames never change the layout, so the fast path
   (script#kpre) is unchanged.

3. No bare boxes: check(out) visits every page and fails any visible CSS border, outline or ring shadow that is
   not an engraved frame (the frame-detail layer's own knock-out labels and panels are counted separately).

    from solar import kindle_ornate
    kindle_ornate.CSS                         # appended last to the stylesheet
    kindle_ornate.typeset(pages, files)       # curly quotes, hanging quotes, initials, headline hooks
    kindle_ornate.full_fonts(out)             # Literata with small caps and old-style figures
    kindle_ornate.frames(out)                 # compose, rasterise and attach every small frame
    python3 -m solar.kindle_ornate check <site>/kindle
"""
import asyncio
import functools
import hashlib
import html.parser
import http.server
import json
import os
import re
import sys
import threading
import zlib

# ---------------------------------------------------------------- the frame families (see frame-spec.md)
# role: (selector, band (t, r, b, l), fixed size or None, lit selector, seed per instance)
# The frame families' bands as drawn in frame-spec.md (used only when solar/frames is missing)
FAMILIES = {"chip": (3, 18, 3, 18), "button": (4, 22, 4, 22), "sections": (3, 14, 3, 14), "runhead": (3, 16, 3, 16),
            "banner": (14, 30, 14, 30), "tile": (14, 14, 14, 14), "tablehead": (3, 20, 3, 20), "barbase": (0, 0, 14, 0),
            "gauge": (2, 14, 2, 14), "divider": (0, 0, 0, 0), "initial": (14, 14, 14, 14)}
# Every framed thing on a page: slot -> (family, selector, fixed size or None, lit selector, seed per element, pack)
#   pack "chrome": in the edition's one chrome sprite (the same on every page, cached once)
#   pack "page":   in the page's own sprite
#   pack "solo":   its own picture, placed by CSS (a base line, a section mark, an initial, a table's head band)
SLOTS = {
    "chip":      ("chip", "#kmain .kst, #kmain b.kval, #kmain .kchip, #kmain .vote, #kmain .sun-clouds>span", None,
                  ".kst-on, .kval-on", True, "page"),
    "button":    ("button", ".kbar a.kprev, .kbar a.knx, .kbar #kmore, #kjump .kjtop a, #kmain .kend .kbig", None, ".kjskip", False, "chrome"),
    "sections":  ("sections", ".krun .ksecbtn", None, "", False, "chrome"),
    "runhead":   ("runhead", ".krun > a, .krun #ksheet", None, "", False, "chrome"),
    "menu":      ("runhead", "#kjump .kjg a", None, ".kjcur", False, "chrome"),
    "banner":    ("banner", "#kmain .kmast .kdate", None, "", False, "page"),
    "tile":      ("tile", "#kmain .tiles>.tile, #kmain .facts>.mini, #kmain .minis>.mini, #kmain .bug, #kmain .open-pick, "
                  "#kmain p.ask, #kmain .look-weather>p, #kmain .sp.kblock", None, "", True, "page"),
    "tablehead": ("tablehead", "#kmain .kth", None, "", True, "page"),
    "matrixhead": ("tablehead", "#kmain table.kmatrix", "thead", "", True, "solo"),
    "gauge":     ("gauge", "#kmain .kgauge, #kmain .progress", None, "", False, "page"),
    "barbase":   ("barbase", "#kmain .khr, #kmain .bars", "base", "", False, "solo"),
    "divider":   ("divider", "#kmain .kpanel h3:not(.kfold), #kmain .kpanel .sub, #kmain .kpanel .day-h, #kmain .kpanel .shelf-h",
                  (140, 16), "", False, "solo"),
    "initial":   ("initial", "#kmain .kdropcap", (74, 74), "", False, "solo"),
}
# drawn once per edition and set by the stylesheet: things the pager makes after the page loads
STATIC = {"resume": ("button", "body.kcontents #kmain .kresume", (526, 64), "")}

# the type size each kind of hand-lettered headline stands in for (solar/lettering.py via kindle_fast.letter):
# section title pages are display, page and card titles are headline, the cover's top lead is lead, story
# headlines in lists are bold body
LETTER_SIZES = {"section": 48, "contents": 34, "title": 34, "poem": 34, "sub": 34, "science": 34,
                "lead": 24, "leads": 17, "story": 17}

# the size each family is drawn at in the layout (CSS px); variable ones are measured per element
NOMINAL = {"chip": (96, 26), "button": (200, 48), "sections": (120, 26), "runhead": (200, 26), "banner": (526, 80),
           "tile": (250, 96), "tablehead": (506, 34), "gauge": (88, 12), "initial": (74, 74), "divider": (140, 16), "barbase": (506, 14)}


def bands(role):
    """(t, r, b, l): the studio's band for this family (solar/frames/<role>.insets), else the spec's numbers."""
    try:
        import importlib
        return tuple(int(round(x)) for x in importlib.import_module(f"solar.frames.{role}").insets(*NOMINAL[role], {}))
    except Exception:  # noqa: BLE001
        return FAMILIES[role]


X = "html.kme:not(#k0):not(#k1):not(#k2)"      # three ids: outranks every earlier !important rule
M = X + " #kmain"

S = {  # the scale: font shorthand per role
    "display": "700 48px/52px var(--k-serif)",
    "figure":  "700 44px/48px var(--k-serif)",
    "head":    "700 34px/40px var(--k-serif)",
    "lead":    "650 24px/30px var(--k-serif)",
    "sect":    "600 20px/26px var(--k-serif)",
    "value":   "700 20px/26px var(--k-serif)",
    "body":    "430 17px/25px var(--k-serif)",
    "bodyb":   "700 17px/25px var(--k-serif)",
    "label":   "600 17px/22px var(--k-serif)",
    "labelb":  "700 17px/22px var(--k-serif)",
    "caption": "italic 430 14px/20px var(--k-serif)",
}
OLD = "font-variant-numeric:oldstyle-nums proportional-nums !important"
LIN = "font-variant-numeric:lining-nums tabular-nums !important"
SC = "font-variant-caps:small-caps !important;text-transform:none !important;letter-spacing:.04em !important;font-style:normal !important"


def _r(sel, decl, pre=M):
    sels = ",".join(pre + " " + s.strip() if s.strip() else pre for s in sel.split(","))
    return sels + "{" + decl + "}\n"


def _css():
    c = "/* ===== kindle_ornate: one type scale, book typography, engraved small frames, no bare boxes ===== */\n"
    # ---- no bare boxes: every CSS border, outline and ring shadow goes (frames are pictures). The frame-detail
    # layer's own panels, knock-out labels, fills and plate slots are theirs and left alone.
    nb = "*:not(.kl):not(.kpanel):not(.kslot):not(#kfill)"
    # (no ::first-letter here: a universal first-letter rule makes every block build a first-letter style, ~30 ms a load)
    c += (f"{X} body {nb},{X} body {nb}::before,{X} body {nb}::after"
          "{border-style:none !important;outline-style:none !important;box-shadow:none !important}\n")
    c += f"{X} body hr{{display:none !important}}\n"
    # ---- the base: body text, figures, features
    c += (f"{X} body{{font-feature-settings:normal !important;font-variant-ligatures:common-ligatures !important;"
          f"font-kerning:normal}}\n")
    c += _r("p, .summary, .note, li, .kansd, .story, .lines>div, .idea>span, .kmile li, .brief-top>li, .brief-rest>li, .ksum, "
            ".kfsub, .kpanel .klong, .rec, .recap p", f"font:{S['body']} !important;{OLD}")
    c += _r(".story b, .lines>div>span:first-child>b, .lines>div>span:first-child>a>b, .kcell b, .idea>b, .kpanel .recap>b, "
            ".kpanel .recap>b *, .kfl .kt b, #krail b", f"font:{S['bodyb']} !important;{OLD}")
    c += _r("i, em, .kquote, .ktrail .kquote", "font-style:italic")
    # ---- display and headline
    c += _r(".kmast .kname, .kend .kfname", f"font:{S['display']} !important;letter-spacing:-.01em !important;{LIN}")
    c += _r("body.ksecfront #kmain .kfname, body.kcontents #kmain .kname", f"font:{S['display']} !important;letter-spacing:-.01em !important;{LIN}", X)
    c += _r("h2, .kh2, .sci-title, .kpanel h2, .kpanel .kh2, .kpanel h3.kfold, h3.kfold, .ktochead",
            f"font:{S['head']} !important;letter-spacing:-.005em !important;text-transform:none !important;{LIN}")
    # ---- lead: the answer and the lead figure
    c += _r(".kanswer .kans, .kanswer .kans.klong, .kpanel .kverdict, .kscore b",
            f"font:{S['lead']} !important;letter-spacing:0 !important;{LIN}")
    # ---- figure: the one key number on a page or tile (the temperature now, the solar kWh, the dollars)
    c += _r(".kdeg, .tile .big, .tiles[data-n] .tile .big, .tiles .tile .big",
            f"font:{S['figure']} !important;letter-spacing:-.01em !important;display:block;{LIN}")
    c += _r(".kdeg small", "display:block;margin-top:2px")
    c += _r(".kdeg small, .tile .u, .tile .s", f"font:{S['caption']} !important;{OLD}")
    # ---- section headings: under an engraved section mark, no rule
    c += _r(".kpanel h3:not(.kfold), .kpanel .sub, .kpanel .day-h, .kpanel .cal-day, .kpanel details>summary, .kpanel h4, .kpanel .shelf-h, "
            "h3:not(.kfold), .sub, .day-h, .cal-day, #krail h4",
            f"font:{S['sect']} !important;letter-spacing:0 !important;text-transform:none !important;font-variant-caps:normal !important;"
            "padding:20px 0 0 !important;margin:14px 0 6px !important;background-repeat:no-repeat !important;"
            "background-position:50% 0 !important;background-size:140px 16px !important;text-align:left")
    c += _r(".kpanel>h3:first-child, .kpanel>.sub:first-child, .kpanel>.day-h:first-child, .head+h3, h2+h3",
            "margin-top:2px !important")
    # ---- values: tiles and fact boxes
    c += _r(".mini .v, .joy-stats b, .kcell b.kval", f"font:{S['value']} !important;letter-spacing:0 !important;{LIN}")
    c += _r(".mini .v small, .kcell b.kval small", f"font:{S['caption']} !important;{OLD}")
    # ---- labels: true small caps at the body size
    lab = (".kkick, .kkicker, .k, .tile .k, .mini .k, .mini>span:first-child, .kth, .kth>span, .rec-k, .sci-topic, .klab, .kpart, "
           ".aside, .brief-rest .aside, .pill, .tag, .badge, .rt2, .rt3, .rt4, .kfl .kn, .kidea-k, .kpanel .kidea-k, .kmast .kear span, .kfhead .kkick")
    c += _r(lab, f"font:{S['label']} !important;{SC};{OLD};color:#000 !important")
    chips = (".kst, .kchip, .kpanel .kchip, .kpanel .st, .kpanel .lvl, .vote, .kpanel .vote b, .kpanel .sp .pill, .ktm .kst, .ktrail .ktags .kst, "
             ".kcell b.kst, .kcell b.kval, .kcell .ktm b.kst, b.kval")
    c += _r(chips, f"font:{S['labelb']} !important;{SC};{LIN};color:#000 !important;-webkit-text-fill-color:#000 !important;background-color:transparent !important")
    # the lit chip (the one notable state): a solid black ground inside the same engraved frame, white letters
    t, r, b, l = bands("chip")
    lit = ".kst-on, b.kval-on, .kcell b.kval-on, .kcell b.kst-on"
    c += _r(lit, "background-color:transparent !important;color:#fff !important;-webkit-text-fill-color:#fff !important;position:relative;z-index:0")
    c += _r(", ".join(x.strip() + "::before" for x in lit.split(",")),
            f"content:'' !important;display:block !important;position:absolute !important;top:{t}px;right:{r}px;bottom:{b}px;left:{l}px;"
            "background:#000 !important;z-index:-1;margin:0 !important;width:auto !important;height:auto !important")
    # ---- captions: italic asides
    cap = (".kpanel small, small, .meta, .cite, .src-line, figcaption, .muted, .s, .u, .kunit, .kcredit, .kpanel .kcredit, .ksources, "
           ".kfoot-note, .kpanel .kfoot-note, .kcell small, .kmile-k, .kfc .kth em, .kfl .kc, .kfl .kt small, .head .meta, .kpanel .head .meta, "
           ".kmeta, .brief-intro, .kfc .kday small, .kkwh sup, .kendsrc, .kcolophon p")
    c += _r(cap, f"font:{S['caption']} !important;letter-spacing:0 !important;text-transform:none !important;font-variant-caps:normal !important;{OLD}")
    c += _r(".kpanel .kcredit", "margin:10px 0 0 !important;padding:0 !important")
    # tables: lining tabular figures, whitespace instead of rules
    c += _r(".ktable, .ktable *, .kgrid, .kgrid *, table, table *, .lines>div>span:last-child, .krain b, .kkwh b, .ktrack em, .khr b, .khr span",
            LIN)
    c += _r(".krow", "min-height:44px !important;padding:6px 0 !important")
    c += _r(".ktable, .kgrid", "margin:8px 0 0 !important")
    c += _r(".krain b, .kkwh b, .ktrack em", f"font:{S['bodyb']} !important;font-style:normal !important;{LIN}")
    c += _r(".ktrack .klo", "font-weight:430 !important")
    c += _r(".khr b", f"font:{S['bodyb']} !important;{LIN}")
    c += _r(".khr span", f"font:{S['label']} !important;{SC};{OLD}")
    # the kicker loses its trailing rule; its lozenge stays
    c += _r(".kkick:after, .kkicker:after", "display:none !important")

    # ---- frames: each family's band (the studio's insets) as padding; the picture is set per element at build time
    BG = "background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important"
    t, r, b, l = bands("chip")
    c += _r(".kst, .kst-off, .kst-on, .kchip, .kpanel .kchip, b.kval, b.kval-on, .kcell b.kval, .kcell b.kst, .vote, .sun-clouds>span, .ktrail .ktags .kst-off, .ktrail .ktags .kst-on",
            f"display:inline-block !important;box-sizing:border-box !important;height:{max(24, 20 + t + b)}px !important;line-height:18px !important;"
            f"padding:{t + 1}px {r + 2}px {b + 1}px {l + 2}px !important;vertical-align:middle;white-space:nowrap !important;{BG}")
    c += _r(".kroads .kright, .kroads .kth>span:last-child", "width:auto !important;-webkit-box-flex:0;flex:none !important;text-align:right")
    # the peaks table: a chip and its ears need a wider status column
    c += _r(".kmtn .kth>span:not(:first-child), .kmtn .krow>.kcell:not(.kname)", "width:122px !important;-webkit-box-flex:0;flex:none !important")
    t, r, b, l = bands("tile")
    c += _r(".tiles, .facts, .minis, .facts[data-n], .minis[data-n], .tiles[data-n]",
            "display:grid !important;grid-template-columns:1fr 1fr !important;grid-gap:6px 6px !important;padding:0 !important;margin:8px 0 10px !important")
    c += _r(".tiles>.tile, .facts>.mini, .minis>.mini, .facts[data-n]>.mini, .minis[data-n]>.mini, .tiles>.tile:nth-child(even), "
            ".facts>.mini:nth-child(even), .minis>.mini:nth-child(even), .facts[data-n]>.mini:not(:nth-child(3n+1)), .minis[data-n]>.mini:not(:nth-child(3n+1)), "
            ".bug, .open-pick, p.ask, .look-weather>p, .sp.kblock",
            f"box-sizing:border-box !important;padding:{t + 2}px {r + 3}px {b + 2}px {l + 3}px !important;background-color:#fff !important;{BG}")
    c += _r(".tile .k, .mini .k, .mini>span:first-child", "margin:0 0 2px !important")
    t, r, b, l = bands("tablehead")
    c += _r(".kth", f"box-sizing:border-box !important;min-height:{22 + t + b + 4}px !important;padding:{t + 2}px {r + 2}px {b + 2}px {l + 2}px !important;margin:0 !important;"
            f"-webkit-box-align:center;align-items:center;{BG}")
    c += _r(".kroads .kright, .kroads .kth>span:last-child", "padding-left:10px")
    c += _r(".kmtn .krow>.kcell:not(.kname), .kroads .kright", "align-self:center")
    c += _r(".krow", f"padding-left:{l + 2}px !important;padding-right:{r + 2}px !important")
    bw, bh = NOMINAL["barbase"]
    c += _r(".khr, .bars", f"padding-bottom:{bh + 2}px !important;background-repeat:no-repeat !important;background-position:0 100% !important;"
            f"background-size:100% {bh}px !important;box-sizing:border-box")
    t, r, b, l = bands("gauge")
    gw, gh = NOMINAL["gauge"]
    c += _r(".kgauge", f"box-sizing:content-box !important;width:{gw - l - r}px !important;height:{max(4, gh - t - b)}px !important;padding:{t}px {r}px {b}px {l}px !important;"
            f"margin:3px 0 3px !important;{BG};position:relative")
    c += _r(".kgauge i", f"position:relative !important;left:auto !important;top:auto !important;bottom:auto !important;height:{max(4, gh - t - b)}px !important")
    c += _r(".progress", f"padding:{t}px {r}px {b}px {l}px !important;{BG}")
    # data marks that were bordered squares: filled for on, stippled for off
    c += _r(".kq>i", "background:repeating-linear-gradient(45deg,#000 0,#000 1px,#fff 1px,#fff 3px) !important")
    c += _r(".kq>i.on", "background:#000 !important")
    c += _r(".legend .sw, .legend i[class^='ksw']", "background:repeating-linear-gradient(45deg,#000 0,#000 1px,#fff 1px,#fff 3px) !important")
    # the cover's date banner
    t, r, b, l = bands("banner")
    c += _r(".kmast .kdate", f"font:{S['label']} !important;{SC};{OLD};box-sizing:border-box;padding:{t + 3}px {r + 4}px {b + 3}px {l + 4}px !important;"
            f"margin:10px 0 6px !important;text-align:center;white-space:normal !important;{BG}")
    c += _r(".kmast .kdate .kded", "display:block")
    # the engraved initial opening a section's first page: three lines of text deep
    iw, ih = NOMINAL["initial"]
    t, r, b, l = bands("initial")
    c += _r(".kdropcap", f"float:left;display:block;box-sizing:border-box;width:{iw}px;height:{ih}px;margin:4px 10px 0 0;padding:0;"
            f"font:600 {min(44, ih - t - b - 6)}px/{ih}px var(--k-serif) !important;text-align:center;font-variant:normal !important;"
            f"background-color:#fff;background-repeat:no-repeat;background-position:0 0;background-size:{iw}px {ih}px")
    c += _r(".khang", "margin-left:-.42em")
    c += _r(".khang1", "margin-left:-.25em")
    # ---- chrome: running head, sections button, bottom bar, the section list
    C = X + " body"
    c += _r(".krun, .krun a, .krun span, .krun b, .krun i, .kbar, .kbar a, .kbar span, #kmore",
            f"font:{S['label']} !important;{SC};{OLD};letter-spacing:.02em !important", C)
    c += _r(".krun", "display:-webkit-box !important;display:flex !important;-webkit-box-align:center !important;align-items:center !important;"
            "-webkit-box-pack:justify !important;justify-content:space-between !important", C)
    t, r, b, l = bands("runhead")
    rh = max(26, 20 + t + b)
    # never truncated: a long section name takes a second line inside the same plaque
    c += _r(".krun>a", f"display:-webkit-inline-box !important;display:inline-flex !important;-webkit-box-align:center;align-items:center;box-sizing:border-box;"
            f"min-height:{rh}px;height:auto;line-height:18px !important;padding:{t + 1}px {r + 2}px {b + 1}px {l + 2}px !important;"
            f"-webkit-box-flex:0;flex:0 1 auto;min-width:0;white-space:normal !important;overflow:visible !important;text-overflow:clip !important;{BG}", C)
    c += _r("body.kcontents .krun", "display:none !important", X)
    c += _r(".krun>a:before", "display:none !important", C)   # the ears carry the ornament now
    c += _r(".krun>a, .krun #ksheet", "letter-spacing:0 !important", C)
    c += _r(".krun>span", f"display:block;-webkit-box-flex:0;flex:none;overflow:visible !important;padding-left:6px;line-height:{rh}px !important;height:{rh}px;white-space:nowrap", C)
    c += _r(".krun #ksheet", f"display:inline-block;box-sizing:border-box;height:{rh}px;line-height:{rh - t - b}px !important;padding:{t}px {r + 3}px {b}px {l + 3}px !important;text-align:center;"
            f"font-style:normal !important;margin:0 6px 0 0;vertical-align:top;{LIN};{BG}", C)
    c += _r(".krun #ksheet:empty", "display:none !important", C)
    t, r, b, l = bands("sections")
    sh = max(26, 20 + t + b)
    c += _r(".krun .ksecbtn", f"display:inline-block !important;box-sizing:border-box;height:{sh}px;line-height:{sh - t - b}px !important;"
            f"padding:{t}px {r + 3}px {b}px {l + 3}px !important;margin:0 !important;text-align:center;vertical-align:top;{BG};color:#000 !important", C)
    t, r, b, l = bands("button")
    bh = NOMINAL["button"][1]   # two lines of label fit: a long page name wraps, never trails off
    c += _r(".kbar", "-webkit-box-pack:justify !important;justify-content:space-between !important", X + ".kpaged body")
    c += _r(".kbar .kprev, .kbar .knx", f"-webkit-box-flex:1 !important;flex:1 1 0 !important;min-width:0;box-sizing:border-box;height:{bh}px;"
            "display:-webkit-box !important;display:flex !important;-webkit-box-align:center;align-items:center;"
            f"line-height:18px !important;padding:{t}px {r}px {b}px {l}px !important;letter-spacing:0 !important;"
            f"white-space:normal !important;overflow:hidden;text-overflow:clip !important;{BG}", C)
    c += _r(".kbar .knx", "text-align:right;-webkit-box-pack:end;justify-content:flex-end", C)
    c += _r(".kbar span.kprev", "display:none !important", C)
    # fixed: More hides on a page's last sheet, and the buttons either side must keep their size (and frame)
    c += _r(".kbar .kmid", f"-webkit-box-flex:0 !important;flex:none !important;width:{62 + l + r + 6 + 8}px;box-sizing:border-box;padding:0 4px !important", C)
    c += _r(".kbar #kmore", f"display:block !important;box-sizing:border-box;height:{bh}px !important;line-height:{bh - t - b}px !important;"
            f"width:100%;padding:{t}px 0 {b}px !important;text-align:center;font-style:normal !important;white-space:nowrap;{BG}", C)
    c += _r("#kjump .kjtop a", f"box-sizing:border-box;padding:{t + 2}px {r + 4}px {b + 2}px {l + 4}px !important;{BG};color:#000 !important;"
            "white-space:normal !important;text-overflow:clip !important", C)
    # the skip button is the menu's lit one: black ground inside the frame
    c += _r("#kjump .kjtop a.kjskip, #kjump .kjtop a.kjskip *", "color:#fff !important;-webkit-text-fill-color:#fff !important", C)
    c += _r("#kjump .kjtop a.kjskip", "background-color:transparent !important;color:#fff !important;position:relative;z-index:0", C)
    c += _r("#kjump .kjskip small", "color:#fff !important", C)
    c += _r("#kjump .kjskip::before", f"content:'';position:absolute;top:{t}px;right:{r}px;bottom:{b}px;left:{l}px;background:#000;z-index:-1", C)
    c += _r("#kjump .kjtop a small, #kjump .kjh, #kjump .kjg a i", f"font:{S['label']} !important;{SC};{OLD};color:#000 !important", C)
    c += _r("#kjump .kjtop a", f"font:{S['bodyb']} !important", C)
    t, r, b, l = bands("runhead")
    c += _r("#kjump .kjg", "-webkit-box-pack:justify;justify-content:space-between", C)
    # a long page name takes a second line in its plaque rather than trailing off
    c += _r("#kjump .kjg a", f"font:{S['body']} !important;width:49% !important;height:auto !important;min-height:{22 + t + b + 2}px !important;"
            "display:-webkit-box !important;display:flex !important;-webkit-box-align:center;align-items:center;"
            f"line-height:20px !important;padding:{t + 1}px {r + 2}px {b + 1}px {l + 2}px !important;margin:0 0 2px !important;"
            f"white-space:normal !important;overflow:visible !important;text-overflow:clip !important;{BG}", C)
    c += _r("#kjump .kjg a i", "line-height:22px !important;width:24px !important;-webkit-box-flex:0;flex:none", C)
    c += _r("#kjump .kjh", "margin:8px 0 2px !important", C)
    c += _r("#kjump .kjg a.kjcur", "color:#fff !important;-webkit-text-fill-color:#fff !important;position:relative;z-index:0", C)
    c += _r("#kjump .kjg a.kjcur i", "color:#fff !important", C)
    c += _r("#kjump .kjg a.kjcur::before", f"content:'';position:absolute;top:{t}px;right:{r}px;bottom:{b}px;left:{l}px;background:#000;z-index:-1", C)
    c += _r("#kjump .kjg a.kjcur i:before", "content:none !important", C)
    c += _r(".kfl .kn", f"font:{S['label']} !important;{SC};{LIN}")
    c += _r(".kfl .kt", f"font:{S['bodyb']} !important;{OLD}")
    c += _r(".kleads b, .kleads a b", f"font:{S['bodyb']} !important;{OLD}")
    c += _r("body.ksecfront #kmain .kfnum, body.ksecfront #kmain .kfhead .kfnum", "font-size:17px !important;font-variant-caps:small-caps !important", X)
    c += _r("body.ksecfront #kmain .kfsub", f"font:italic 430 17px/25px var(--k-serif) !important;{OLD}", X)
    # the market board: label over figure in each cell
    c += _r("#mkt>div", "display:block !important")
    c += _r("#mkt>div>span", "display:block !important;max-width:none !important;padding:0 !important;text-align:left !important;white-space:normal !important")
    c += _r("#mkt>div>span:first-child", f"font:{S['label']} !important;{SC};{OLD}")
    c += _r("#kcont", f"font:{S['caption']} !important", C)
    t, r, b, l = bands("button")
    c += _r(".kend .kbig, .kresume", f"{BG};padding:{t + 4}px {r + 4}px {b + 4}px {l + 4}px !important")
    c += _r("body.kcontents #kmain .kresume", "display:block;width:auto !important;margin:0 0 14px !important", X)
    c += _r("body.kcontents #kmain .kresume small", f"display:block;font:{S['label']} !important;{SC};{OLD}", X)
    c += _r("body.kcontents #kmain .kresume b", f"display:block;font:{S['bodyb']} !important;{OLD}", X)
    # the surf matrix: its head row carries a table-head plaque; the image covers the head only
    t, r, b, l = bands("tablehead")
    c += _r("table.kmatrix", "background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% auto !important")
    c += _r("table.kmatrix thead th", f"padding-top:{t + 4}px !important;padding-bottom:{b + 4}px !important;font:{S['label']} !important;{SC};{OLD}")
    c += _r("table.kmatrix thead th:first-child", f"padding-left:{l + 2}px !important;width:{104 + l}px !important")
    c += _r("table.kmatrix thead th:last-child", f"padding-right:{r + 2}px !important")
    # today's facts: compact tiles, label and figure on one line, two by two and the tide across
    t, r, b, l = bands("tile")
    c += _r("#out-facts>.mini, #out-facts[data-n]>.mini, #out-facts>.mini:nth-child(even), #out-facts[data-n]>.mini:not(:nth-child(3n+1))",
            "display:-webkit-box !important;display:flex !important;-webkit-box-orient:horizontal !important;-webkit-flex-direction:row !important;"
            "flex-direction:row !important;flex-wrap:wrap !important;-webkit-box-pack:justify;justify-content:space-between !important;"
            f"-webkit-box-align:baseline;align-items:baseline !important;padding:{t + 1}px {r + 4}px {b + 1}px {l + 4}px !important;min-height:0 !important")
    c += _r("#out-facts>.mini>.k, #out-facts>.mini>span:first-child", "margin:0 8px 0 0 !important")
    c += _r("#out-facts>.mini>.v", "text-align:right;white-space:nowrap")
    c += _r("#out-facts>.mini:nth-child(5):last-child, #out-facts>.mini:nth-child(odd):last-child", "grid-column:1 / span 2 !important")
    c += _r("#out-facts", "margin:4px 0 6px !important")
    # the fit ladder may tighten space, never the type: the roles above are fixed and outrank it
    return c


CSS = _css()

# ---------------------------------------------------------------- book typography pass (build time, in Chromium)
TYPESET = r"""
(args) => {
  const pages = args.pages, OPEN = /[\u201c\u2018"']/;
  const blockTags = /^(P|LI|DIV|H1|H2|H3|H4|TD|TH|BLOCKQUOTE|FIGCAPTION|SECTION|ARTICLE|HEADER|FOOTER|NAV|UL|OL|SPAN)$/;
  function quotes(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let prev = ' ', n;
    const ns = []; while ((n = tw.nextNode())) ns.push(n);
    let lastPar = null;
    for (const t of ns) {
      if (t.parentNode.closest('script,style,svg,code,pre,[data-raw]')) { prev = ' '; continue; }
      if (t.parentNode !== lastPar) prev = ' ';   // a new element: what came before is another phrase
      lastPar = t.parentNode;
      const v = t.nodeValue; let o = '';
      for (let i = 0; i < v.length; i++) {
        const c = v[i], p = i ? v[i - 1] : prev;
        const opener = /[\s(\[{\u2014\u2013\/-]/.test(p);
        const nx = v[i + 1] || '';
        if (c === '"') o += opener && nx && !/[\s.,;:!?)\]]/.test(nx) ? '\u201c' : '\u201d';
        else if (c === "'") o += (opener && !/^\d\d?s\b/.test(v.slice(i + 1))) ? '\u2018' : '\u2019';
        else o += c;
      }
      if (o !== v) t.nodeValue = o;
      if (v.length) prev = v[v.length - 1];
    }
  }
  // the first visible character of a block: an opening quote hangs into the margin
  function hang(root) {
    for (const b of root.querySelectorAll('.kpanel p, .kpanel li, .kquote, .kans, .kansd, .summary')) {
      const tw = document.createTreeWalker(b, NodeFilter.SHOW_TEXT); let t;
      while ((t = tw.nextNode()) && !t.nodeValue.trim()) {}
      if (!t || t.parentNode.closest('.khang')) continue;
      const m = /^(\s*)([\u201c\u2018])/.exec(t.nodeValue); if (!m) continue;
      const s = document.createElement('span'); s.className = m[2] === '\u201c' ? 'khang' : 'khang1'; s.textContent = m[2];
      const rest = t.splitText(m[1].length); rest.nodeValue = rest.nodeValue.slice(1); rest.parentNode.insertBefore(s, rest);
    }
  }
  // the engraved initial: the lead paragraph of a section's first page
  function initial(root) {
    const ps = Array.from(root.querySelectorAll('.kpanel p, .kpanel .ksum, .kpanel .summary')).filter(p =>
      !p.closest('.ktable, .kgrid, .tiles, .facts, .minis, .head, .kanswer, .kfrontwx, .bug, .look-weather, .kmile, .story, .lines, li, table') &&
      (p.textContent || '').trim().length > 120 && /^[A-Z]/.test((p.textContent || '').trim()) && !p.querySelector('img, svg'));
    const p = ps[0]; if (!p) return;
    const tw = document.createTreeWalker(p, NodeFilter.SHOW_TEXT); let t;
    while ((t = tw.nextNode()) && !t.nodeValue.trim()) {}
    if (!t) return;
    const m = /^(\s*)([A-Z])/.exec(t.nodeValue); if (!m) return;
    const s = document.createElement('span'); s.className = 'kdropcap'; s.setAttribute('aria-hidden', 'true'); s.textContent = m[2];
    const rest = t.splitText(m[1].length); rest.nodeValue = rest.nodeValue.slice(1);
    const sr = document.createElement('span'); sr.className = 'ksr'; sr.textContent = m[2];
    rest.parentNode.insertBefore(s, rest); rest.parentNode.insertBefore(sr, rest);
    p.classList.add('kdrop');
  }
  function headlines(root) {
    for (const h of root.querySelectorAll('h2, .kh2, .sci-title, h3.kfold, .kfname, .kname')) {
      h.classList.add('khl'); h.setAttribute('data-khl', (h.textContent || '').replace(/\s+/g, ' ').trim()); }
  }
  // sizes the cards set for themselves, off the scale: each element takes the nearest role (the stylesheet is loaded
  // into this page so the computed sizes are the edition's own)
  const SCALE = [14, 17, 20, 24, 34, 48];
  function snap(d) {
    const todo = [];
    for (const el of d.querySelectorAll('*')) {
      if (el.closest('svg, .kdropcap, .khl, .kst, .kchip, .vote, .kfnum, .kanswer, .kkick, .kkicker, .kth, .k, .head .meta, script, style')) continue;
      let own = false; for (const n of el.childNodes) if (n.nodeType === 3 && n.nodeValue.trim()) { own = true; break; }
      if (!own) continue;
      const cs = getComputedStyle(el), fs = parseFloat(cs.fontSize); if (!fs || SCALE.indexOf(fs) >= 0) continue;
      const t = (el.textContent || '').trim(), fig = /^[\s\d.,:%°$≈~+\u2212\u2013-]+[A-Za-z%°]{0,4}$/.test(t);
      const lab = cs.textTransform === 'uppercase' || parseFloat(cs.letterSpacing) > fs * .05;
      const r = lab && fs < 22.5 ? 'lab' : fs < 15.5 ? (t.length > 60 ? 'body' : 'cap') : fs < 18.75 ? 'body' : fs < 22.5 ? 'val' : fs < 27.5 || fig ? 'lead' : 'head';
      todo.push([el, 'kr-' + r + (el.closest('.bars, .khr, .kchart, .ktrack, .kgauge, .legend, .axis, .kbx, .kq, table, .kfc') ? 'n' : '')]);
    }
    for (const [el, c] of todo) el.classList.add(c);
  }
  let host = null;
  if (args.css) {
    const st = document.createElement('style'); st.textContent = args.css; document.head.appendChild(st);
    document.documentElement.className = args.htmlClass || '';
    document.body.className = args.bodyClass || '';
    document.body.innerHTML = '<div id="kview"><div id="kclip"><main id="kmain"></main></div></div>';
    host = document.getElementById('kmain');
  }
  return pages.map(pg => {
    const d = document.createElement('div'); d.innerHTML = pg.html;
    if (host) { host.innerHTML = ''; host.appendChild(d); try { snap(d); } catch (e) {} }
    try { quotes(d); } catch (e) {}
    try { hang(d); } catch (e) {}
    try { if (pg.first) initial(d); } catch (e) {}
    try { headlines(d); } catch (e) {}
    return d.innerHTML;
  });
}
"""

CSS += f"{M} .kr-lab,{M} .kr-labn{{font-size:17px !important;line-height:22px !important;font-variant-caps:small-caps !important;text-transform:none !important;letter-spacing:.04em !important;font-weight:600 !important;font-style:normal !important}}\n"
for _k, _v in (("cap", (14, 20)), ("body", (17, 25)), ("val", (20, 26)), ("lead", (24, 30)), ("head", (34, 40))):
    CSS += f"{M} .kr-{_k}{{font-size:{_v[0]}px !important;line-height:{_v[1]}px !important}}{M} .kr-{_k}n{{font-size:{_v[0]}px !important}}\n"
CSS += (M + " .ksr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}\n")


def typeset(pages, css="", html_class="", body_class=""):
    """Book typography on every page's card HTML (pages: [{"html", "file"}], edited in place). Never fatal."""
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("KINDLE_CHROMIUM") or None
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=exe)
            p = br.new_page()
            res = p.evaluate(TYPESET, {"css": css, "htmlClass": html_class, "bodyClass": body_class, "pages": [{"html": pg["html"], "first": bool(re.search(r"-01\.html$", pg.get("file", "")))}
                                                 for pg in pages]})
            br.close()
        for pg, h in zip(pages, res):
            pg["html"] = h
    except Exception as e:  # noqa: BLE001
        print(f"kindle_ornate: typeset skipped: {e!r}", file=sys.stderr)


def smarten(s):
    """Curly quotes for a plain string (titles and labels built in Python)."""
    s = re.sub(r'(^|[\s(\[{\u2014\u2013/-])"', "\\1\u201c", s)
    s = s.replace('"', "\u201d")
    s = re.sub(r"(^|[\s(\[{\u2014\u2013/-])'(?!\d\ds)", "\\1\u2018", s)
    return s.replace("'", "\u2019")


# ---------------------------------------------------------------- fonts: the full Literata (small caps, old-style figures)
FULL_FONTS = {
    "normal": "https://raw.githubusercontent.com/google/fonts/main/ofl/literata/Literata%5Bopsz%2Cwght%5D.ttf",
    "italic": "https://raw.githubusercontent.com/google/fonts/main/ofl/literata/Literata-Italic%5Bopsz%2Cwght%5D.ttf",
}


FONT_FEATURES = ["smcp", "onum", "lnum", "pnum", "tnum", "liga", "kern", "ccmp", "locl", "mark", "mkmk", "rvrn"]
FONT_AXES = {"wght": (400, 900), "opsz": (12, 48)}
# Latin-1, general punctuation, arrows and the symbols the edition prints; kindle_fast cuts further per edition
FONT_UNICODES = (list(range(0x20, 0x7f)) + list(range(0xa0, 0x180)) + list(range(0x2000, 0x2070)) + [0x20ac, 0x2116, 0x2122]
                 + list(range(0x2190, 0x21a0)) + [0x2212, 0x2215, 0x2219, 0x221e, 0x2248, 0x2260, 0x2264, 0x2265, 0x25b2, 0x25bc, 0x25cf,
                                                  0x25e6, 0x2605, 0x2606, 0x2665, 0x2713, 0x2766, 0x2767, 0x00a7, 0x00b6, 0x02c6, 0x02dc])


def full_fonts(out):
    """Swap Google's trimmed Literata (no smcp, c2sc or onum) for the family's full variable font, as woff2 under the
    same names; kindle_fast later cuts it to this edition's characters with every feature kept. Cached; never fatal."""
    import urllib.request
    cache = os.path.join(os.path.expanduser("~"), ".cache", "solar-fonts")
    done = []
    for style, url in FULL_FONTS.items():
        dst = os.path.join(out, "fonts", f"literata-{style}.woff2")
        if not os.path.exists(dst):
            continue
        try:
            os.makedirs(cache, exist_ok=True)
            src = os.path.join(cache, f"literata-{style}-book-v2.woff2")
            if not os.path.exists(src):
                from fontTools.ttLib import TTFont
                from fontTools import subset
                from fontTools.varLib import instancer
                import io
                raw = urllib.request.urlopen(url, timeout=60).read()
                f = TTFont(io.BytesIO(raw))
                feats = {fr.FeatureTag for fr in f["GSUB"].table.FeatureList.FeatureRecord}
                if not {"smcp", "onum", "lnum"} <= feats:
                    raise ValueError("full font lacks smcp/onum")
                # the features the edition sets, the characters it can print, and only the axes' used ranges
                o = subset.Options()
                o.layout_features = FONT_FEATURES
                o.name_IDs = ["*"]
                o.notdef_outline = True
                o.drop_tables += ["DSIG"]
                sub = subset.Subsetter(o)
                sub.populate(unicodes=FONT_UNICODES)
                sub.subset(f)
                b = io.BytesIO()
                f.save(b)
                f = TTFont(io.BytesIO(b.getvalue()))
                f = instancer.instantiateVariableFont(f, FONT_AXES)
                f.flavor = "woff2"
                f.save(src + ".tmp")
                os.replace(src + ".tmp", src)
            with open(src, "rb") as a, open(dst, "wb") as b:
                b.write(a.read())
            done.append(style)
        except Exception as e:  # noqa: BLE001
            print(f"kindle_ornate: full Literata {style} skipped ({e!r}); small caps will be synthesised", file=sys.stderr)
    return done


# ---------------------------------------------------------------- frames: compose, rasterise, attach
def compose(role, w, h, seed=0, variant="plain"):
    """The studio's frame for this role at exactly w x h CSS px (an <svg> string), or None.
    solar/frames/<role>.frame(w, h, ctx) first (claude/engrave-frames), then scroll.compose, then a plain stand-in."""
    import importlib
    try:
        mod = importlib.import_module(f"solar.frames.{role}")
    except ImportError:
        mod = None
    if mod is not None:
        try:
            return mod.frame(w, h, {"variant": variant, "seed": seed})
        except Exception as e:  # noqa: BLE001
            print(f"kindle_ornate: frames.{role}.frame({w}x{h}) failed: {e!r}", file=sys.stderr)
            return None
    try:
        from solar import scroll
        if hasattr(scroll, "compose"):
            return scroll.compose(w, h, role, seed=seed, variant=variant)
    except Exception as e:  # noqa: BLE001
        print(f"kindle_ornate: scroll.compose({role}, {w}x{h}) failed: {e!r}", file=sys.stderr)
    return standin(role, w, h, variant)


def _compose_key(k):
    role, w, h, seed, v = k
    return compose(role, w, h, seed, v)


def standin(role, w, h, variant="plain"):
    """Until the studio's art lands: a plain stand-in (fine double rule) so the wiring can be checked. Not the design."""
    t, r, b, l = FAMILIES.get(role, (3, 3, 3, 3))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" stroke="#000">']
    if role in ("divider",):
        o.append(f'<path d="M4 {h/2}H{w/2-8}M{w/2+8} {h/2}H{w-4}" stroke-width=".5"/><path d="M{w/2} {h/2-4}l4 4-4 4-4-4z" stroke-width="1"/>')
    elif role == "barbase":
        o.append(f'<path d="M0 {h-12.5}H{w}M0 {h-9.5}H{w}" stroke-width="1"/><path d="M0 {h-2.5}H{w}" stroke-width=".5"/>')
    else:
        o.append(f'<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" stroke-width="1.5"/>')
        if min(t, r, b, l) >= 3:
            o.append(f'<rect x="{max(1, min(t, l) - 1.25)}" y="{max(1, t - 1.25)}" width="{w - 2 * max(1, min(t, l) - 1.25)}" '
                     f'height="{h - 2 * max(1, t - 1.25)}" stroke-width=".5"/>')
        if variant == "lit":
            o.append(f'<rect x="0" y="0" width="{l}" height="{h}" fill="#000"/><rect x="{w-r}" y="0" width="{r}" height="{h}" fill="#000"/>')
    o.append("</svg>")
    return "".join(o)


MEASURE_JS = r"""(F) => {
  // every framed element's border box at the Kindle's size (the Sections menu measured open)
  const out = {}, r = document.documentElement, open = r.classList.contains('kjumpopen');
  r.classList.add('kjumpopen');
  for (const k in F) {
    const [sel, fixed, lit, baseH] = F[k]; const L = [];
    for (const el of document.querySelectorAll(sel)) {
      const b = el.getBoundingClientRect(); let w = Math.round(b.width), h = Math.round(b.height);
      if (fixed === 'base') h = baseH;
      else if (fixed === 'thead') { const t = el.tHead; h = t ? Math.round(t.getBoundingClientRect().height) : 0; }
      else if (fixed) { w = fixed[0]; h = fixed[1]; }
      const v = lit && el.matches(lit) ? 'lit' : 'plain';
      L.push(w >= 8 && h >= 6 && getComputedStyle(el).display !== 'none' ? [w, h, v] : null);
    }
    out[k] = L;
  }
  if (!open) r.classList.remove('kjumpopen');
  return out;
}"""

# applied once on load, before the pager: each element gets its frame (a cell of a sprite, or its own picture)
APPLY = ("<script>(function(){try{var d=JSON.parse(document.getElementById('kfrm').textContent),k,q,L,i,e,s;"
         "for(k in d.r){q=document.querySelectorAll(d.s[k]);L=d.r[k];for(i=0;i<L.length&&i<q.length;i++){e=L[i];if(!e)continue;s=q[i].style;"
         "s.setProperty('background-image','url('+d.u[e[0]]+')','important');"
         "if(e.length>1){s.setProperty('background-position',-e[1]+'px '+(-e[2])+'px','important');"
         "s.setProperty('background-size',e[3]+'px '+e[4]+'px','important');s.setProperty('background-repeat','no-repeat','important');}}}}"
         "catch(x){}})();</script>")


# run in the page as parsed, scripts off (the same elements, in the same order, as the load-time script would see:
# the page prep before it only wraps charts and hides links): each framed element's place among all elements, and
# the declarations its style attribute gains. The source is then patched tag by tag, so nothing else in it changes.
INLINE_JS = r"""() => { const j = document.getElementById('kfrm'); if (!j) return null; const d = JSON.parse(j.textContent);
  const all = [...document.getElementsByTagName('*')], at = new Map(all.map((e, i) => [e, i])), add = [];
  for (const k in d.r) { const q = document.querySelectorAll(d.s[k]), L = d.r[k];
    for (let i = 0; i < L.length && i < q.length; i++) { const e = L[i]; if (!e) continue;
      let v = 'background-image:url(' + d.u[e[0]] + ') !important';
      if (e.length > 1) v += ';background-position:' + (-e[1]) + 'px ' + (-e[2]) + 'px !important;background-size:' + e[3] + 'px ' + e[4] +
        'px !important;background-repeat:no-repeat !important';
      add.push([at.get(q[i]), v, e.length > 5 ? e[5] + ' ' + e[6] : '']); } }
  return { tags: all.map(e => e.tagName.toLowerCase() + '.' + (e.getAttribute('class') || '')), add }; }"""


class _Tags(html.parser.HTMLParser):
    """Every start tag in the source, in order: (name.class, start offset, end offset)."""
    def __init__(self, src):
        super().__init__(convert_charrefs=True)
        self.src, self.tags = src, []
        self._lines = [0]
        for m in re.finditer("\n", src):
            self._lines.append(m.end())
        self.feed(src)

    def handle_starttag(self, tag, attrs):
        ln, col = self.getpos()
        st = self._lines[ln - 1] + col
        self.tags.append((tag + "." + (dict(attrs).get("class") or ""), st, st + len(self.get_starttag_text())))

    handle_startendtag = handle_starttag


def _patch(src, info):
    """src with each framed element's start tag carrying its frame; None if the tags cannot be lined up."""
    import difflib
    T = _Tags(src).tags
    sm = difflib.SequenceMatcher(None, info["tags"], [t[0] for t in T], autojunk=False)
    dom2src = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            dom2src[a + k] = b + k
    edits = []
    for di, decl, kf in info["add"]:
        si = dom2src.get(di)
        if si is None:
            return None
        _, st, en = T[si]
        tag = src[st:en]
        m = re.search(r'\sstyle=(["\'])(.*?)\1', tag, re.S)
        extra = f' data-kf="{kf}"' if kf else ""
        if m:
            q = m.group(1)
            val = m.group(2).rstrip().rstrip(";")
            new = tag[:m.start()] + f" style={q}{val + ';' if val else ''}{decl}{q}" + extra + tag[m.end():]
        else:
            cut = en - st - (2 if tag.endswith("/>") else 1)
            new = tag[:cut] + f' style="{decl}"' + extra + tag[cut:]
        edits.append((st, en, new))
    for st, en, new in sorted(edits, reverse=True):
        src = src[:st] + new + src[en:]
    return src


def _inline(out, pages):
    from playwright.async_api import async_playwright
    srv, base = _serve(out)
    done = [0]

    async def go():
        async with async_playwright() as pw:
            br = await pw.chromium.launch(executable_path=os.environ.get("KINDLE_CHROMIUM") or None)
            cx = await br.new_context(java_script_enabled=False)
            sem = asyncio.Semaphore(4)

            async def one(p):
                async with sem:
                    pg = await cx.new_page()
                    try:
                        await pg.goto(base + p + ".html", wait_until="domcontentloaded")
                        info = await pg.evaluate(INLINE_JS)
                    finally:
                        await pg.close()
                    if not info:
                        return
                    fp = os.path.join(out, p + ".html")
                    src = open(fp, encoding="utf-8").read()
                    new = _patch(src, info)
                    if new is None:
                        print(f"kindle_ornate: {p}: frames left to the load-time script (tags did not line up)", file=sys.stderr)
                        return
                    new = re.sub(r'<script type="application/json" id="kfrm">.*?</script><script>\(function\(\)\{try\{var d=JSON\.parse\(document\.getElementById\(\'kfrm\'\).*?</script>',
                                 "", new, flags=re.S)
                    with open(fp, "w", encoding="utf-8") as f:
                        f.write(new)
                    done[0] += 1
            await asyncio.gather(*(one(p) for p in pages))
            await br.close()
    try:
        asyncio.run(go())
    finally:
        srv.shutdown()
    return done[0]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class _Srv(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):   # a browser hanging up early is not news
        pass


def _serve(out):
    srv = _Srv(("127.0.0.1", 0), functools.partial(_Quiet, directory=out))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


# the bottom bar's labels never trail off: each label the pager may show is tried in its button at build time;
# one that does not fit in two lines gives way to "Previous page" / "Next page"
FIT_JS = r"""(L) => {
  const fits = (el, html) => { const keep = el.innerHTML; el.innerHTML = html; const cs = getComputedStyle(el), b = el.getBoundingClientRect();
    const g = document.createRange(); g.selectNodeContents(el); const t = g.getBoundingClientRect();
    // at most two lines (glyph boxes overhang the 18 px lines by a few px), and nothing past the slot's sides
    const lh = parseFloat(cs.lineHeight) || 18;
    const ok = t.height <= 2 * lh + 10 && t.top >= b.top - 1 && t.bottom <= b.bottom + 1 &&
               t.left >= b.left + parseFloat(cs.paddingLeft) - 1 && t.right <= b.right - parseFloat(cs.paddingRight) + 1;
    el.innerHTML = keep; return ok; };
  const pv = document.querySelector('.kbar a.kprev'), nx = document.querySelector('.kbar .knx');
  return { prev: pv && L.prev ? fits(pv, L.prev) : true,
           skip: nx && L.next ? fits(nx, 'Skip to ' + L.next) : true, last: nx && L.next ? fits(nx, L.next) : true };
}"""


async def _measure_all(br, base, pages, F, fit=None):
    sem = asyncio.Semaphore(4)
    res = {}

    async def one(p):
        async with sem:
            cx = await br.new_context(viewport={"width": 618, "height": 714}, device_scale_factor=2)
            try:
                pg = await cx.new_page()
                await pg.goto(base + p + ".html", wait_until="load")
                await pg.evaluate("document.fonts ? document.fonts.ready.then(() => 0) : 0")
                await pg.wait_for_timeout(150)
                res[p] = await pg.evaluate(MEASURE_JS, F)
                if fit is not None:
                    doc = open(os.path.join(fit["out"], p + ".html"), encoding="utf-8").read()
                    pv = re.search(r'<a class="kprev"[^>]*>(.*?)</a>', doc)
                    nx = re.search(r'<a class="knx"[^>]*>(?:Next: )?(.*?)</a>', doc)
                    fit["res"][p] = await pg.evaluate(FIT_JS, {"prev": pv.group(1) if pv else "", "next": nx.group(1) if nx else ""})
            except Exception as e:  # noqa: BLE001
                print(f"kindle_ornate: measure {p}: {e!r}", file=sys.stderr)
            finally:
                await cx.close()
    await asyncio.gather(*(one(p) for p in pages))
    return res


async def _raster(br, jobs, odir):
    """jobs: {name: svg}; each to a 16-grey PNG with alpha at 2x."""
    from solar.kindle_fast import _png16
    sem = asyncio.Semaphore(4)
    cx = await br.new_context(device_scale_factor=2)

    async def one(name, svg, w, h):
        async with sem:
            pg = await cx.new_page()
            try:
                await pg.set_viewport_size({"width": w, "height": h})
                await pg.set_content('<!doctype html><html><head><style>html,body{margin:0;background:transparent}svg{display:block}</style>'
                                     f'</head><body>{svg}</body></html>')
                png = await pg.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h})
                _png16(png, os.path.join(odir, name), opaque=False)
            finally:
                await pg.close()
    await asyncio.gather(*(one(n, s, w, h) for n, (s, w, h) in jobs.items()))
    await cx.close()


def _pack(names, sizes):
    """Shelf-pack frames (CSS px sizes) with a 2 px gutter: {name: (x, y)}, (W, H)."""
    order = sorted(names, key=lambda n: (-sizes[n][1], -sizes[n][0]))
    W = max([512] + [sizes[n][0] + 4 for n in order])
    x = y = shelf = 0
    pos = {}
    for n in order:
        w, h = sizes[n]
        if x + w + 2 > W:
            x, y, shelf = 0, y + shelf + 2, 0
        pos[n] = (x, y)
        x += w + 2
        shelf = max(shelf, h)
    return pos, (W, y + shelf)


def _sprite(odir, names, sizes, dst):
    """One 16-grey sprite (2x) from the frames' own PNGs; returns {name: (x, y)} and its CSS size."""
    import io
    from PIL import Image
    from solar.kindle_fast import _png16
    pos, (W, H) = _pack(names, sizes)
    im = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    for n, (x, y) in pos.items():
        im.paste(Image.open(os.path.join(odir, n)).convert("RGBA"), (x * 2, y * 2))
    b = io.BytesIO()
    im.save(b, "PNG")
    _png16(b.getvalue(), dst, opaque=False)
    return pos, (W, H)


def frames(out):
    """Measure every framed element on every page at the Kindle's size; compose each distinct frame (the studio's
    solar/frames) and rasterise it; pack the chrome's frames into one sprite for the edition and each page's own
    into one sprite per page; write each page's list (script#kfrm) with the line that applies it, and the
    stylesheet's fixed frames. Never fatal."""
    import time
    t0 = time.time()
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None
    pages = sorted(p[:-5] for p in os.listdir(out) if p.endswith(".html"))
    F = {k: [v[1], list(v[2]) if isinstance(v[2], tuple) else v[2], v[3], NOMINAL["barbase"][1]] for k, v in SLOTS.items()}
    odir = os.path.join(out, "orn", "kf")
    os.makedirs(odir, exist_ok=True)
    srv, base = _serve(out)
    stats = {"pages": 0, "frames": 0, "pictures": 0, "sprites": 0, "missing": 0, "labels_replaced": 0}
    fitd = {"out": out, "res": {}}
    try:
        async def go():
            async with async_playwright() as pw:
                br = await pw.chromium.launch(executable_path=os.environ.get("KINDLE_CHROMIUM") or None)
                meas = await _measure_all(br, base, pages, F, fitd)
                keys, plan = {}, {}
                for p, slots in meas.items():
                    plan[p] = {}
                    for k, L in slots.items():
                        role = SLOTS[k][0]
                        ks = []
                        for i, it in enumerate(L):
                            if not it:
                                ks.append(None)
                                continue
                            w, h, v = it
                            seed = zlib.crc32(f"{p}:{k}:{i}".encode()) & 0xffff if SLOTS[k][4] else 0
                            key = (role, w, h, seed, v)
                            keys[key] = None
                            ks.append(key)
                        plan[p][k] = ks
                for k, (role, sel, (w, h), lit) in STATIC.items():
                    keys[(role, w, h, 0, "plain")] = None
                from concurrent.futures import ProcessPoolExecutor
                ks = list(keys)
                with ProcessPoolExecutor(max_workers=max(1, min(8, os.cpu_count() or 1))) as ex:
                    svgs = list(ex.map(_compose_key, ks, chunksize=8))
                jobs = {}
                for key, svg in zip(ks, svgs):
                    if not svg:
                        stats["missing"] += 1
                        continue
                    role, w, h, seed, v = key
                    name = f"{role}-{w}x{h}-{v[0]}-{hashlib.sha1(svg.encode()).hexdigest()[:8]}.png"
                    jobs.setdefault(name, (svg, w, h))
                    keys[key] = name
                await _raster(br, {n: j for n, j in jobs.items() if not os.path.exists(os.path.join(odir, n))}, odir)
                await br.close()
                return plan, keys, {n: (j[1], j[2]) for n, j in jobs.items()}
        plan, keys, sizes = asyncio.run(go())
    finally:
        srv.shutdown()
    used = set()
    # the chrome: one sprite for the whole edition
    chrome = sorted({keys[k] for p in plan for s, L in plan[p].items() if SLOTS[s][5] == "chrome" for k in L if k and keys.get(k)})
    cpos, csz, cname = {}, (0, 0), None
    if chrome:
        tmp = os.path.join(odir, "chrome.tmp.png")
        cpos, csz = _sprite(odir, chrome, sizes, tmp)
        cname = "chrome-" + hashlib.sha1(open(tmp, "rb").read()).hexdigest()[:10] + ".png"
        os.replace(tmp, os.path.join(odir, cname))
        stats["sprites"] += 1
    sels = {k: v[1] for k, v in SLOTS.items()}
    for p, slots in plan.items():
        urls, R = [], {}
        if cname:
            urls.append("orn/kf/" + cname)
        mine = sorted({keys[k] for s, L in slots.items() if SLOTS[s][5] == "page" for k in L if k and keys.get(k)})
        ppos, psz, pi = {}, (0, 0), None
        if mine:
            tmp = os.path.join(odir, f"page.tmp.png")
            ppos, psz = _sprite(odir, mine, sizes, tmp)
            pn = f"page-{p}-" + hashlib.sha1(open(tmp, "rb").read()).hexdigest()[:10] + ".png"
            os.replace(tmp, os.path.join(odir, pn))
            urls.append("orn/kf/" + pn)
            pi = len(urls) - 1
            stats["sprites"] += 1
        for s, L in slots.items():
            row = []
            for k in L:
                n = keys.get(k) if k else None
                if not n:
                    row.append(0)
                    continue
                pack = SLOTS[s][5]
                if pack == "chrome":
                    x, y = cpos[n]
                    row.append([0, x, y, csz[0], csz[1], sizes[n][0], sizes[n][1]])
                elif pack == "page":
                    x, y = ppos[n]
                    row.append([pi, x, y, psz[0], psz[1], sizes[n][0], sizes[n][1]])
                else:
                    used.add(n)
                    if "orn/kf/" + n not in urls:
                        urls.append("orn/kf/" + n)
                    row.append([urls.index("orn/kf/" + n)])
                stats["frames"] += 1
            if any(row):
                R[s] = row
        if not R:
            continue
        data = json.dumps({"u": urls, "s": {s: sels[s] for s in R}, "r": R}, separators=(",", ":")).replace("</", "<\\/")
        fp = os.path.join(out, p + ".html")
        doc = open(fp, encoding="utf-8").read()
        ft = fitd["res"].get(p)
        if ft:
            if not ft["prev"]:
                doc, k = re.subn(r'(<a class="kprev"[^>]*>).*?</a>', r'\1&lsaquo;&nbsp;Previous page</a>', doc, count=1)
                stats["labels_replaced"] += k
            doc = re.sub(r'<a class="knx"', f'<a data-klab="{int(ft["skip"])}{int(ft["last"])}" class="knx"', doc, count=1)
        doc = re.sub(r'<script type="application/json" id="kfrm">.*?</script><script>\(function\(\)\{try\{var d=JSON\.parse\(document\.getElementById\(\'kfrm\'\).*?</script>',
                     "", doc, flags=re.S)
        block = f'<script type="application/json" id="kfrm">{data}</script>{APPLY}'
        # after the page prep (which moves charts) and before the pager: the same DOM as measured
        m = re.search(r'<script src="[^"]*pager[^"]*"></script>', doc)
        at = doc.rfind("</body>") if not m else m.start()
        with open(fp, "w", encoding="utf-8") as f:
            f.write(doc[:at] + block + doc[at:])
        stats["pages"] += 1
    # bake the frames into the pages: each element's background goes into its own style attribute in the HTML, so
    # the Kindle parses it with the element (no script, no second style pass); the list and script are dropped
    try:
        stats["inlined"] = _inline(out, list(plan))
    except Exception as e:  # noqa: BLE001
        print(f"kindle_ornate: inline frames skipped ({e!r}); the load-time script applies them", file=sys.stderr)
    # fixed frames the stylesheet sets (what the pager makes after load)
    css = ""
    for k, (role, sel, (w, h), lit) in STATIC.items():
        n = keys.get((role, w, h, 0, "plain"))
        if n:
            used.add(n)
            css += (f"{X} {sel}{{background-image:url(orn/kf/{n}) !important;background-repeat:no-repeat !important;"
                    f"background-size:{w}px {h}px !important;background-position:0 0 !important;box-sizing:border-box;width:{w}px;height:{h}px}}\n")
    if css:
        with open(os.path.join(out, "kindle.css"), "a", encoding="utf-8") as f:
            f.write("\n/* kindle_ornate: fixed frames */\n" + css)
    # the single frames now live in the sprites
    for n in os.listdir(odir):
        if n.endswith(".png") and n not in used and not n.startswith(("chrome-", "page-")):
            os.remove(os.path.join(odir, n))
    stats["pictures"] = len(sizes)
    stats["secs"] = round(time.time() - t0, 1)
    return stats


# ---------------------------------------------------------------- the sheet check: no bare boxes, one scale, the fast path
CHECK_JS = r"""(F) => {
  const bad = [], theirs = [], sizes = {}, unframed = [];
  const own = el => el.closest('#kko, #kkf, #kfill, .kslot') || el.matches('.kpanel, .kl');
  const name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).join('.') : '');
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('svg') || /^(SCRIPT|STYLE|TEMPLATE)$/.test(el.tagName)) continue;
    const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0) && el.tagName !== 'HR') continue;
    for (const ps of [null, '::before', '::after']) {
      const c = ps ? getComputedStyle(el, ps) : cs;
      if (ps && (c.content === 'none' || c.display === 'none')) continue;
      let s = '';
      for (const k of ['Top', 'Right', 'Bottom', 'Left']) { const st = c['border' + k + 'Style'], w = parseFloat(c['border' + k + 'Width']), col = c['border' + k + 'Color'];
        if (st !== 'none' && st !== 'hidden' && w > 0 && !/rgba\(.*,\s*0\)$/.test(col) && col !== 'transparent') s += k[0]; }
      const ol = c.outlineStyle !== 'none' && parseFloat(c.outlineWidth) > 0;
      const sh = c.boxShadow && c.boxShadow !== 'none';
      const bi = c.borderImageSource && c.borderImageSource !== 'none';
      if ((s || ol || sh || el.tagName === 'HR') && !bi) (own(el) ? theirs : bad).push(name(el) + (ps || '') + ' [' + s + (ol ? 'O' : '') + (sh ? 'S' : '') + ']');
    }
    let txt = false; for (const n of el.childNodes) if (n.nodeType === 3 && n.nodeValue.trim()) { txt = true; break; }
    if (txt && !el.closest('#kjump, .kltx, .ksr') && cs.color !== 'rgba(0, 0, 0, 0)') { const k = parseFloat(cs.fontSize) + '/' + parseFloat(cs.lineHeight || 0);
      (sizes[k] = sizes[k] || []).length < 3 && sizes[k].push(name(el) + ': ' + (el.textContent || '').trim().slice(0, 20)); }
  }
  let D = null; try { D = JSON.parse(document.getElementById('kfrm').textContent); } catch (e) {}
  for (const role in F) { const q = document.querySelectorAll(F[role]); const R = D && D.r[role];
    q.forEach((el, i) => {
    const b = el.getBoundingClientRect(); if (!b.width || getComputedStyle(el).display === 'none') return;
    const bi = getComputedStyle(el).backgroundImage; if (!/url\(/.test(bi)) { unframed.push(role + ': ' + name(el)); return; }
    const e = R && R[i]; let fw = 0, fh = 0;
    if (e && e.length > 5) { fw = e[5]; fh = e[6]; }
    else if (el.getAttribute('data-kf')) { const z = el.getAttribute('data-kf').split(' '); fw = +z[0]; fh = +z[1]; }
    else { const m = /-(\d+)x(\d+)-/.exec(bi); if (m && !/^(divider|barbase|initial|matrixhead)$/.test(role)) { fw = +m[1]; fh = +m[2]; } }
    if (fw && (Math.abs(fw - b.width) > 1.5 || Math.abs(fh - b.height) > 1.5))
      unframed.push(role + ' size ' + fw + 'x' + fh + ' vs ' + Math.round(b.width) + 'x' + Math.round(b.height) + ': ' + name(el));
  }); }
  return { bad, theirs, sizes, unframed, kpre: !!document.getElementById('kpre'), fast: !!(window.KROOM) };
}"""


def check(out, shots=None, only=None):
    """Every page, every sheet, at 618 x 714: bare boxes (ours must be 0), type sizes in use, frames attached, the
    fast path's data present. Optionally saves a PNG per sheet. Returns the report dict."""
    from playwright.async_api import async_playwright
    pages = sorted(p[:-5] for p in os.listdir(out) if p.endswith(".html"))
    if only:
        pages = [p for p in pages if p in only]
    F = {k: v[1] for k, v in SLOTS.items()}
    F.update({k: v[1] for k, v in STATIC.items()})
    srv, base = _serve(out)
    res = {}

    async def go():
        async with async_playwright() as pw:
            br = await pw.chromium.launch(executable_path=os.environ.get("KINDLE_CHROMIUM") or None)
            sem = asyncio.Semaphore(4)

            async def one(p):
                async with sem:
                    cx = await br.new_context(viewport={"width": 618, "height": 714}, device_scale_factor=2)
                    pg = await cx.new_page()
                    await pg.goto(base + p + ".html", wait_until="load")
                    await pg.evaluate("document.fonts ? document.fonts.ready.then(() => 0) : 0")
                    await pg.wait_for_timeout(250)
                    n = await pg.evaluate("window.KROOM ? window.KROOM.sheets : 1")
                    v = await pg.evaluate(CHECK_JS, F)
                    v["sheets"] = n
                    # the pager's own check (verify): the recorded layout still holds, so the fast path stays on
                    v["usedpre"] = await pg.evaluate("""() => { const j = document.getElementById('kpre'); if (!j) return null;
                      const P = JSON.parse(j.textContent), m = document.getElementById('kmain'), r = document.querySelector('.krun'), b = document.querySelector('.kbar');
                      return innerWidth === P.vw && innerHeight === P.vh && m.offsetHeight === P.mh && (!r || r.offsetHeight === P.rh) && b.offsetHeight === P.bh; }""")
                    if shots:
                        os.makedirs(shots, exist_ok=True)
                        for i in range(n):
                            if i:
                                await pg.evaluate(f"window.KPAGER && window.KPAGER.show({i})")
                                await pg.wait_for_timeout(120)
                            await pg.screenshot(path=os.path.join(shots, f"{p}~{i + 1:02d}.png"))
                    res[p] = v
                    await cx.close()
            await asyncio.gather(*(one(p) for p in pages))
            await br.close()
    try:
        asyncio.run(go())
    finally:
        srv.shutdown()
    return res


def _summary(res):
    from collections import Counter
    bad = Counter(b.split(" [")[0].split("#")[0] + " [" + b.split(" [")[1] for v in res.values() for b in v["bad"])
    theirs = Counter(b.split(" [")[0] for v in res.values() for b in v["theirs"])
    sizes = Counter(k for v in res.values() for k in v["sizes"])
    unf = [p + ": " + u for p, v in res.items() for u in v["unframed"]]
    return {"pages": len(res), "sheets": sum(v["sheets"] for v in res.values()),
            "bare_boxes_ours": sum(len(v["bad"]) for v in res.values()), "bare_kinds": bad.most_common(40),
            "bare_boxes_frame_detail": sum(len(v["theirs"]) for v in res.values()), "theirs_kinds": theirs.most_common(10),
            "unframed": unf[:60], "unframed_n": len(unf),
            "no_kpre": [p for p, v in res.items() if not v["kpre"]],
            "kpre_broken": [p for p, v in res.items() if v.get("usedpre") is False], "sizes": sizes.most_common()}


def frame_source():
    """Where the frames come from in this build (for the contact sheet and the build log)."""
    try:
        import solar.frames  # noqa: F401
        return "Frames drawn by the engraving studio (solar/frames/, composed per element by solar/scroll.py)."
    except ImportError:
        return "STAND-INS: the studio's art (solar/frames/) is not in this build; plain double rules mark where each frame goes."


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "check":
        r = check(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None,
                  sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else None)
        sm = _summary(r)
        if len(sys.argv) > 5:
            json.dump(r, open(sys.argv[5], "w"))
        print(json.dumps(sm, indent=1, ensure_ascii=False))
        sys.exit(1 if sm["bare_boxes_ours"] else 0)
    elif len(sys.argv) > 2 and sys.argv[1] == "frames":
        print(frames(sys.argv[2]))
    else:
        print(json.dumps({"css_bytes": len(CSS)}))

