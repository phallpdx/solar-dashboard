"""The Morning Edition's type and its small engraved frames: one type scale, book typography, no bare boxes.

Three jobs, all owned here so the other layers (kindle_full, kindle_present, ornament, kindle_frame) stay as
they are:

1. One type scale (CSS below, appended last to the stylesheet). Every role has one size on every page:

     role       size/leading  why
     display    48/52   the cover nameplate and each section's title page: a part title, seen across the room
     headline   30/36   the page's question or title: the first thing read ("Is the mountain out?", "Good morning").
                        Slot for the hand-lettering (solar/lettering.py, branch claude/headline-lettering): every
                        headline carries class .khl and data-khl="<plain text>"; a lettered headline replaces the
                        element's content with one <img class="klet"> per line, 36 px high, at most the column wide
                        (506 px in a panel), leaving the text in alt.
     lead       24/30   the answer, or the lead figure (53°, ~69 kWh, $32): second, and smaller than the question
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
   from a per-page list (script#kfrm) applied once on load. Frames never change the layout, so the fast path
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
import http.server
import json
import os
import re
import sys
import threading
import zlib

# ---------------------------------------------------------------- the frame families (see frame-spec.md)
# role: (selector, band (t, r, b, l), fixed size or None, lit selector, seed per instance)
FAMILIES = {
    "chip":      ("#kmain .kst-off, #kmain .kst-on, #kmain .kchip, #kmain b.kval-on, #kmain .vote, #kmain .sun-clouds>span",
                  (4, 11, 4, 11), None, ".kst-on, .kval-on", True),
    "button":    (".kbar a.kprev, .kbar a.knx, .kbar #kmore, #kjump .kjtop a, #kmain .kend .kbig, #kmain .kresume",
                  (6, 14, 6, 14), None, ".kjskip", False),
    "sections":  (".krun .ksecbtn", (4, 12, 5, 12), None, "", False),
    "runhead":   (".krun > a, .krun #ksheet", (4, 13, 4, 13), None, "", False),
    "banner":    ("#kmain .kmast .kdate", (8, 34, 8, 34), None, "", False),
    "tile":      ("#kmain .tiles>.tile, #kmain .facts>.mini, #kmain .minis>.mini, #kmain .bug, #kmain .open-pick, "
                  "#kmain p.ask, #kmain .look-weather>p, #kmain .sp.kblock",
                  (7, 7, 7, 7), None, "", True),
    "tablehead": ("#kmain .kth", (6, 12, 6, 12), None, "", True),
    "barbase":   ("#kmain .khr, #kmain .bars", (0, 0, 14, 0), "barbase", "", False),
    "gauge":     ("#kmain .kgauge, #kmain .progress", (2, 4, 2, 4), None, "", False),
    "divider":   ("#kmain .kpanel h3:not(.kfold), #kmain .kpanel .sub, #kmain .kpanel .day-h, #kmain .kpanel .shelf-h",
                  (0, 0, 0, 0), (120, 12), "", False),
    "initial":   ("#kmain .kdropcap", (5, 5, 5, 5), (50, 50), "", False),
}
# where each family's picture sits in its element (CSS background-position / size)
PLACE = {"barbase": ("0 100%", "100% 14px"), "divider": ("50% 0", "120px 12px")}

X = "html.kme:not(#k0):not(#k1):not(#k2)"      # three ids: outranks every earlier !important rule
M = X + " #kmain"

S = {  # the scale: font shorthand per role
    "display": "700 48px/52px var(--k-serif)",
    "head":    "700 30px/36px var(--k-serif)",
    "lead":    "700 24px/30px var(--k-serif)",
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
    c += (f"{X} body {nb},{X} body {nb}::before,{X} body {nb}::after,{X} body {nb}::first-letter"
          "{border-style:none !important;outline-style:none !important;box-shadow:none !important}\n")
    c += f"{X} body hr{{display:none !important}}\n"
    # ---- the base: body text, figures, features
    c += (f"{X} body{{font-feature-settings:normal !important;font-variant-ligatures:common-ligatures !important;"
          f"font-kerning:normal;text-rendering:optimizeLegibility}}\n")
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
    c += _r(".kanswer .kans, .kanswer .kans.klong, .kpanel .kverdict, .kdeg, .tile .big, .tiles[data-n] .tile .big, .kscore b",
            f"font:{S['lead']} !important;letter-spacing:0 !important;{LIN}")
    c += _r(".kdeg small, .tile .u, .tile .s", f"font:{S['caption']} !important;{OLD}")
    # ---- section headings: under an engraved section mark, no rule
    c += _r(".kpanel h3:not(.kfold), .kpanel .sub, .kpanel .day-h, .kpanel .cal-day, .kpanel details>summary, .kpanel h4, .kpanel .shelf-h, "
            "h3:not(.kfold), .sub, .day-h, .cal-day, #krail h4",
            f"font:{S['sect']} !important;letter-spacing:0 !important;text-transform:none !important;font-variant-caps:normal !important;"
            "padding:18px 0 0 !important;margin:14px 0 6px !important;background-repeat:no-repeat !important;"
            "background-position:50% 0 !important;background-size:120px 12px !important;text-align:left")
    c += _r(".kpanel>h3:first-child, .kpanel>.sub:first-child, .kpanel>.day-h:first-child, .head+h3, h2+h3",
            "margin-top:2px !important")
    # ---- values: tiles and fact boxes
    c += _r(".mini .v, .joy-stats b, .kcell b.kval", f"font:{S['value']} !important;letter-spacing:0 !important;{LIN}")
    c += _r(".mini .v small, .kcell b.kval small", f"font:{S['caption']} !important;{OLD}")
    # ---- labels: true small caps at the body size
    lab = (".kkick, .kkicker, .k, .tile .k, .mini .k, .mini>span:first-child, .kth, .kth>span, .rec-k, .sci-topic, .klab, .kpart, "
           ".aside, .brief-rest .aside, .pill, .tag, .badge, .rt2, .rt3, .rt4, .kfl .kn, .kidea-k, .kpanel .kidea-k, .kmast .kear span, .kfhead .kkick")
    c += _r(lab, f"font:{S['label']} !important;{SC};{OLD};color:#000 !important")
    c += _r(".kst, .kchip, .kpanel .kchip, .kpanel .st, .kpanel .lvl, .vote, .kpanel .vote b, .kpanel .sp .pill, .ktm .kst, .ktrail .ktags .kst",
            f"font:{S['labelb']} !important;{SC};{OLD};color:#000 !important;-webkit-text-fill-color:#000 !important;background-color:transparent !important")
    c += _r(".kst-on, b.kval-on", "background-color:transparent !important;color:#000 !important;-webkit-text-fill-color:#000 !important")
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

    # ---- frames: each family's band as padding; the picture is set per element at build time
    c += _r(".kst-off, .kst-on, .kchip, .kpanel .kchip, b.kval-on, .vote, .sun-clouds>span, .ktrail .ktags .kst-off, .ktrail .ktags .kst-on",
            "display:inline-block !important;box-sizing:border-box !important;height:26px !important;line-height:22px !important;"
            "padding:2px 13px !important;vertical-align:middle;white-space:nowrap !important;"
            "background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important")
    c += _r(".kcell b.kval", "display:inline-block")
    c += _r(".tiles, .facts, .minis, .facts[data-n], .minis[data-n], .tiles[data-n]",
            "display:grid !important;grid-template-columns:1fr 1fr !important;grid-gap:8px 8px !important;padding:0 !important;margin:8px 0 10px !important")
    c += _r(".tiles>.tile, .facts>.mini, .minis>.mini, .facts[data-n]>.mini, .minis[data-n]>.mini, .tiles>.tile:nth-child(even), "
            ".facts>.mini:nth-child(even), .minis>.mini:nth-child(even), .facts[data-n]>.mini:not(:nth-child(3n+1)), .minis[data-n]>.mini:not(:nth-child(3n+1)), "
            ".bug, .open-pick, p.ask, .look-weather>p, .sp.kblock",
            "box-sizing:border-box !important;padding:10px 13px 11px !important;background-color:#fff !important;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important")
    c += _r(".tile .k, .mini .k, .mini>span:first-child", "margin:0 0 2px !important")
    c += _r(".kth", "box-sizing:border-box !important;min-height:34px !important;padding:6px 14px !important;margin:0 !important;"
            "-webkit-box-align:center;align-items:center;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important")
    c += _r(".kroads .kright, .kroads .kth>span:last-child", "padding-left:10px")
    c += _r(".krow", "padding-left:14px !important;padding-right:14px !important")
    c += _r(".khr, .bars", "padding-bottom:16px !important;background-repeat:no-repeat !important;background-position:0 100% !important;background-size:100% 14px !important;box-sizing:border-box")
    c += _r(".kgauge", "box-sizing:content-box !important;width:80px !important;height:8px !important;padding:2px 4px !important;"
            "margin:3px 0 3px !important;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important;position:relative")
    c += _r(".kgauge i", "position:relative !important;left:auto !important;top:auto !important;bottom:auto !important;height:8px !important")
    c += _r(".progress", "padding:2px 4px !important;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important")
    # data marks that were bordered squares: filled for on, stippled for off
    c += _r(".kq>i", "background:repeating-linear-gradient(45deg,#000 0,#000 1px,#fff 1px,#fff 3px) !important")
    c += _r(".kq>i.on", "background:#000 !important")
    c += _r(".legend .sw, .legend i[class^='ksw']", "background:repeating-linear-gradient(45deg,#000 0,#000 1px,#fff 1px,#fff 3px) !important")
    # the cover's date banner
    c += _r(".kmast .kdate", f"font:{S['label']} !important;{SC};{OLD};box-sizing:border-box;min-height:44px;padding:11px 36px !important;"
            "margin:10px 0 6px !important;text-align:center;white-space:normal !important;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important")
    # the engraved initial opening a section's first page
    c += _r(".kmast .kdate .kded", "display:block")
    c += _r(".kdropcap", "float:left;display:block;box-sizing:border-box;width:50px;height:50px;margin:4px 8px 0 0;padding:0;"
            "font:600 36px/50px var(--k-serif) !important;text-align:center;font-variant:normal !important;"
            "background-color:#fff;background-repeat:no-repeat;background-position:0 0;background-size:50px 50px")
    c += _r(".khang", "margin-left:-.42em")
    c += _r(".khang1", "margin-left:-.25em")
    # ---- chrome: running head, sections button, bottom bar, the section list
    C = X + " body"
    c += _r(".krun, .krun a, .krun span, .krun b, .krun i, .kbar, .kbar a, .kbar span, #kmore",
            f"font:{S['label']} !important;{SC};{OLD}", C)
    c += _r(".krun", "-webkit-box-align:center !important;align-items:center !important", C)
    c += _r(".krun>a", "display:inline-block !important;box-sizing:border-box;height:26px;line-height:26px !important;padding:0 14px !important;"
            "max-width:300px;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important", C)
    c += _r(".krun>span", "display:inline-block;padding-left:8px;line-height:26px !important;height:26px", C)
    c += _r(".krun #ksheet", "display:inline-block;box-sizing:border-box;width:116px;height:26px;line-height:26px !important;text-align:center;"
            "font-style:normal !important;margin:0 8px 0 0;vertical-align:top;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:116px 26px !important", C)
    c += _r(".krun #ksheet:empty", "display:none !important", C)
    c += _r(".krun .ksecbtn", "display:inline-block !important;box-sizing:border-box;width:108px;height:26px;line-height:26px !important;"
            "padding:0 !important;margin:0 !important;text-align:center;vertical-align:top;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:108px 26px !important;"
            "color:#000 !important", C)
    c += _r(".kbar", "-webkit-box-pack:justify !important;justify-content:space-between !important", X + ".kpaged body")
    c += _r(".kbar .kprev, .kbar .knx", "-webkit-box-flex:0 !important;flex:none !important;box-sizing:border-box;width:200px;height:38px;"
            "line-height:38px !important;padding:0 16px !important;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important", C)
    c += _r(".kbar .knx", "text-align:right", C)
    c += _r(".kbar span.kprev", "display:none !important", C)
    c += _r(".kbar span.kprev~.knx", "width:398px", C)
    c += _r(".kbar .kmid", "flex:none !important;width:96px;padding:0 !important", C)
    c += _r(".kbar #kmore", "display:block !important;box-sizing:border-box;width:96px;height:38px !important;line-height:38px !important;"
            "padding:0 12px !important;text-align:center;font-style:normal !important;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:96px 38px !important", C)
    c += _r("#kjump .kjtop a", "box-sizing:border-box;padding:8px 20px !important;background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important;color:#000 !important", C)
    c += _r("#kjump .kjtop a small, #kjump .kjh, #kjump .kjg a i", f"font:{S['label']} !important;{SC};{OLD};color:#000 !important", C)
    c += _r("#kjump .kjtop a", f"font:{S['bodyb']} !important", C)
    c += _r("#kjump .kjg a", f"font:{S['body']} !important;height:31px;line-height:31px !important", C)
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
    c += _r(".kmain .kend .kbig, .kend .kbig, .kresume", "background-repeat:no-repeat !important;background-position:0 0 !important;background-size:100% 100% !important;padding:10px 20px !important")
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
  const SCALE = [14, 17, 20, 24, 30, 48];
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
for _k, _v in (("cap", (14, 20)), ("body", (17, 25)), ("val", (20, 26)), ("lead", (24, 30)), ("head", (30, 36))):
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
            src = os.path.join(cache, f"literata-{style}-full.woff2")
            if not os.path.exists(src):
                from fontTools.ttLib import TTFont
                import io
                raw = urllib.request.urlopen(url, timeout=60).read()
                f = TTFont(io.BytesIO(raw))
                feats = {fr.FeatureTag for fr in f["GSUB"].table.FeatureList.FeatureRecord}
                if not {"smcp", "onum", "lnum"} <= feats:
                    raise ValueError("full font lacks smcp/onum")
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
    """The studio's frame for this role at exactly w x h CSS px (an <svg> string), or None."""
    try:
        from solar import scroll  # the studio's composer (claude/engrave-frames)
        return scroll.compose(w, h, role, seed=seed, variant=variant)
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001
        print(f"kindle_ornate: scroll.compose({role}, {w}x{h}) failed: {e!r}", file=sys.stderr)
        return None
    try:
        import importlib
        mod = importlib.import_module(f"solar.frames.{role}")
        return mod.frame(w, h, {"variant": variant, "seed": seed})
    except ImportError:
        return standin(role, w, h, variant)
    except Exception as e:  # noqa: BLE001
        print(f"kindle_ornate: frames.{role}.frame({w}x{h}) failed: {e!r}", file=sys.stderr)
        return None


def standin(role, w, h, variant="plain"):
    """Until the studio's art lands: a plain stand-in (fine double rule) so the wiring can be checked. Not the design."""
    t, r, b, l = FAMILIES[role][1]
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
  const out = {}, r = document.documentElement, open = r.classList.contains('kjumpopen');
  r.classList.add('kjumpopen');
  for (const role in F) {
    const [sel, fixed, lit] = F[role]; const L = [];
    for (const el of document.querySelectorAll(sel)) {
      const b = el.getBoundingClientRect(); let w = Math.round(b.width), h = Math.round(b.height);
      if (role === 'barbase') h = 14;
      if (fixed) { w = fixed[0]; h = fixed[1]; }
      const v = lit && el.matches(lit) ? 'lit' : 'plain';
      L.push(w >= 8 && h >= 6 ? [w, h, v, (el.textContent || '').trim().slice(0, 40)] : null);
    }
    out[role] = L;
  }
  if (!open) r.classList.remove('kjumpopen');
  return out;
}"""

APPLY = ("<script>(function(){try{var d=JSON.parse(document.getElementById('kfrm').textContent),k,q,L,i;"
         "for(k in d.r){q=document.querySelectorAll(d.s[k]);L=d.r[k];for(i=0;i<L.length&&i<q.length;i++)"
         "if(L[i])q[i].style.setProperty('background-image','url('+d.b+L[i]+')','important');}}catch(e){}})();</script>")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _serve(out):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=out))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


async def _measure_all(br, base, pages, F):
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


def frames(out):
    """Measure every framed element on every page at the Kindle's size, compose and rasterise each distinct frame,
    and write each page's list (script#kfrm) with the line that applies it. Never fatal."""
    import time
    t0 = time.time()
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None
    pages = sorted(os.path.basename(p)[:-5] for p in os.listdir(out) if p.endswith(".html"))
    pages = [p for p in pages if os.path.exists(os.path.join(out, p + ".html"))]
    F = {role: [f[0], list(f[2]) if isinstance(f[2], tuple) else None, f[3]] for role, f in FAMILIES.items()}
    odir = os.path.join(out, "orn", "kf")
    os.makedirs(odir, exist_ok=True)
    srv, base = _serve(out)
    stats = {"pages": 0, "frames": 0, "pngs": 0, "missing": 0}
    try:
        async def go():
            async with async_playwright() as pw:
                br = await pw.chromium.launch(executable_path=os.environ.get("KINDLE_CHROMIUM") or None)
                meas = await _measure_all(br, base, [p.replace(".html", "") for p in pages], F)
                jobs, plan = {}, {}
                for p, roles in meas.items():
                    plan[p] = {}
                    for role, L in roles.items():
                        urls = []
                        for i, it in enumerate(L):
                            if not it:
                                urls.append(0)
                                continue
                            w, h, v, _t = it
                            seed = zlib.crc32(f"{p}:{role}:{i}".encode()) & 0xffff if FAMILIES[role][4] else 0
                            svg = compose(role, w, h, seed, v)
                            if not svg:
                                urls.append(0)
                                stats["missing"] += 1
                                continue
                            name = f"{role}-{w}x{h}-{v[0]}-{hashlib.sha1(svg.encode()).hexdigest()[:8]}.png"
                            jobs.setdefault(name, (svg, w, h))
                            urls.append(name)
                            stats["frames"] += 1
                        if any(urls):
                            plan[p][role] = urls
                await _raster(br, {n: j for n, j in jobs.items() if not os.path.exists(os.path.join(odir, n))}, odir)
                stats["pngs"] = len(jobs)
                await br.close()
                return plan
        plan = asyncio.run(go())
    finally:
        srv.shutdown()
    sels = {role: f[0] for role, f in FAMILIES.items()}
    for p, roles in plan.items():
        if not roles:
            continue
        data = json.dumps({"b": "orn/kf/", "s": {r: sels[r] for r in roles}, "r": roles}, separators=(",", ":")).replace("</", "<\\/")
        fp = os.path.join(out, p + ".html")
        s = open(fp, encoding="utf-8").read()
        s = re.sub(r'<script type="application/json" id="kfrm">.*?</script><script>\(function\(\)\{try\{var d=JSON\.parse\(document\.getElementById\(\'kfrm\'\).*?</script>',
                   "", s, flags=re.S)
        block = f'<script type="application/json" id="kfrm">{data}</script>{APPLY}'
        # after the page prep (which moves charts) and before the pager: the same DOM as measured
        m = re.search(r'<script src="[^"]*pager[^"]*"></script>|<script>\s*/\*[^*]*pager|<script>\(function \(\) \{', s)
        i = s.rfind("</body>") if not m else m.start()
        s = s[:i] + block + s[i:]
        with open(fp, "w", encoding="utf-8") as f:
            f.write(s)
        stats["pages"] += 1
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
    if (txt && !el.closest('#kjump')) { const k = parseFloat(cs.fontSize) + '/' + parseFloat(cs.lineHeight || 0);
      (sizes[k] = sizes[k] || []).length < 3 && sizes[k].push(name(el) + ': ' + (el.textContent || '').trim().slice(0, 20)); }
  }
  for (const role in F) for (const el of document.querySelectorAll(F[role])) {
    const b = el.getBoundingClientRect(); if (!b.width || getComputedStyle(el).display === 'none') continue;
    const bi = getComputedStyle(el).backgroundImage; if (!/url\(/.test(bi)) unframed.push(role + ': ' + name(el));
    else { const m = /-(\d+)x(\d+)-/.exec(bi); if (m && role !== 'divider' && role !== 'barbase' && role !== 'initial' && (Math.abs(+m[1] - b.width) > 1.5 || Math.abs(+m[2] - b.height) > 1.5))
      unframed.push(role + ' size ' + m[1] + 'x' + m[2] + ' vs ' + Math.round(b.width) + 'x' + Math.round(b.height) + ': ' + name(el)); }
  }
  return { bad, theirs, sizes, unframed, kpre: !!document.getElementById('kpre'), fast: !!(window.KROOM) };
}"""


def check(out, shots=None, only=None):
    """Every page, every sheet, at 618 x 714: bare boxes (ours must be 0), type sizes in use, frames attached, the
    fast path's data present. Optionally saves a PNG per sheet. Returns the report dict."""
    from playwright.async_api import async_playwright
    pages = sorted(p[:-5] for p in os.listdir(out) if p.endswith(".html"))
    if only:
        pages = [p for p in pages if p in only]
    F = {role: f[0] for role, f in FAMILIES.items()}
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
                    v["usedpre"] = await pg.evaluate("!!document.getElementById('kpre') && document.documentElement.hasAttribute('data-kfit-now')")
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
            "no_kpre": [p for p, v in res.items() if not v["kpre"]], "sizes": sizes.most_common()}


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


def frame_source():
    """Where the frames come from in this build (for the contact sheet and the build log)."""
    try:
        from solar import scroll  # noqa: F401
        return "Frames by the engraving studio (solar/scroll.py, composed per element)."
    except ImportError:
        pass
    try:
        import solar.frames  # noqa: F401
        return "Frames by the engraving studio (solar/frames/)."
    except ImportError:
        return "STAND-INS: the studio's art (solar/scroll.py) is not in this build; plain double rules mark where each frame goes."
