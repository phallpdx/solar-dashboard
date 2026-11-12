"""The bespoke plates: after the Morning pages are written, measure the free room on every sheet of every page
in a browser at the Kindle's 618x714, ask that page's engraver (solar/plates/<slug>.py: plate(w, h, ctx) -> svg)
for a plate cut to exactly that room, put it through the e-ink normaliser, and write orn/plate-<slug>-<sheet>.svg.
Each page gets a small map, <body data-kplates='[[sheet,h,w],...]'>, which the pager uses to show the plate as a
fixed-size <img> outside #kmain, so a plate can never change the fit or add a sheet. A page with no plate module
simply gets no plate; a plate that fails costs only itself."""
import glob
import html as _html
import importlib.util
import json
import os
import re
import sys
import time
import zlib

from . import plate_slots

HERE = os.path.dirname(os.path.abspath(__file__))
PLATES = os.path.join(HERE, "plates")
MIN_H = 40   # below this a sheet gets no plate
MIN_SCENE = 90   # a planned plate is never set shorter than this (or than its own planned height, if smaller)

MEASURE = """async (n0) => {
  const wait = (f, ms) => new Promise(r => { const t0 = Date.now(); (function k() { if (f() || Date.now() - t0 > ms) r(); else setTimeout(k, 30); })(); });
  await wait(() => window.KROOM, 4000);
  await new Promise(r => setTimeout(r, 500));
  if (!window.KROOM) return null;
  const main = document.getElementById('kmain'), q = s => { const e = main && main.querySelector(s); return e ? e.textContent.trim().replace(/\\s+/g, ' ') : ''; };
  const ctx = { title: q('h2') || q('.kftitle') || q('.kname') || document.title, kicker: q('.kkick') || q('.kfsub'),
                section: document.body.getAttribute('data-ksec') || (/kendpage/.test(document.body.className) ? 'end' : 'cover'),
                sample: (main ? main.textContent : '').replace(/\\s+/g, ' ').trim().slice(0, 1200) };
  const rooms = [], n = window.KROOM.sheets;
  for (let i = 0; i < n; i++) {
    if (i) { const more = document.getElementById('kmore'); if (!more) break; more.click();
             await wait(() => window.KROOM.sheet === i, 3000); await new Promise(r => setTimeout(r, 300)); }
    rooms.push(Object.assign({}, window.KROOM));
  }
  return { ctx, rooms, fit: document.documentElement.getAttribute('data-kfit-now') || '' };
}"""


SHAPES = {
    "oval": lambda w, h: f"M0,{h / 2:.1f}A{w / 2:.1f},{h / 2:.1f} 0 1 0 {w:.1f},{h / 2:.1f}A{w / 2:.1f},{h / 2:.1f} 0 1 0 0,{h / 2:.1f}Z",
    "circle": lambda w, h: (lambda r: f"M{w / 2 - r:.1f},{h / 2:.1f}a{r:.1f},{r:.1f} 0 1 0 {2 * r:.1f},0a{r:.1f},{r:.1f} 0 1 0 {-2 * r:.1f},0Z")(min(w, h) / 2),
    "arch": lambda w, h: (lambda r: f"M0,{h}V{r:.1f}A{w / 2:.1f},{r:.1f} 0 0 1 {w},{r:.1f}V{h}Z")(min(h * .6, w / 2)),
    "lunette": lambda w, h: (lambda r: f"M0,0H{w}V{h - r:.1f}A{w / 2:.1f},{r:.1f} 0 0 1 0,{h - r:.1f}Z")(min(h * .6, w / 2)),
    "banner": lambda w, h: (lambda n: f"M0,{h * .12:.1f}H{w}L{w - n:.1f},{h / 2:.1f}L{w},{h * .88:.1f}H0L{n:.1f},{h / 2:.1f}Z")(min(h * .45, w * .08)),
    "irregular": lambda w, h: _irregular(w, h),
    "cut": lambda w, h: (lambda c: f"M{c:.1f},0H{w - c:.1f}L{w},{c:.1f}V{h - c:.1f}L{w - c:.1f},{h}H{c:.1f}L0,{h - c:.1f}V{c:.1f}Z")(min(w, h) * .12),
}


def _irregular(w, h, n=14):
    """A scalloped cartouche: an ellipse whose rim swells into lobes, so the silhouette is never a box."""
    import math
    pts = []
    for i in range(n * 8):
        a = 2 * math.pi * i / (n * 8)
        k = 1 - .07 * (1 - abs(math.cos(a * n / 2)))
        c, s_ = math.cos(a), math.sin(a)
        e = 3.
        x = abs(c) ** (2 / e) * (1 if c >= 0 else -1)
        y = abs(s_) ** (2 / e) * (1 if s_ >= 0 else -1)
        pts.append((w / 2 + x * w / 2 * k, h / 2 + y * h / 2 * k))
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


def _shape(svg, w, h, shape, arms=False):
    """Clip a plate to its slot's shape, with a fine black rule round the edge."""
    inner = re.sub(r"^\s*<\?xml[^>]*>\s*", "", svg)
    seal = ""
    if arms:   # the Somaster dedication cartouche at the vignette's foot (plan: section fronts)
        from .arms import arms as _arms
        ah = 34
        aw = int(ah * 120 / 140)
        seal = f'<g transform="translate({(w - aw) / 2:.1f},{h - ah - 1:.1f})">{_arms(aw, ah, 7)}</g>'
    if shape not in SHAPES:
        if not seal:
            return svg
        d = f"M0,0H{w}V{h}H0Z"
    else:
        d = SHAPES[shape](w, h)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><clipPath id="kshape"><path d="{d}"/></clipPath></defs><g clip-path="url(#kshape)">{inner}</g>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1.5"/>{seal}</svg>')


def _insert_slots(src, slug, slots):
    """Reserve each in-flow slot in the page: a fixed-size <div class="kslot"> holding the plate's <img>,
    at the top of #kmain (head) or before/after the element with the given id. Returns the new html."""
    from html.parser import HTMLParser
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
    lines = src.split("\n")
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln) + 1)

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.spans, self.cls = [], {}, {}

        def handle_starttag(self, tag, attrs):
            pos = offs[self.getpos()[0] - 1] + self.getpos()[1]
            a = dict(attrs)
            if tag in VOID:
                if a.get("id"):
                    self.spans[a["id"]] = (pos, pos + len(self.get_starttag_text()))
                return
            self.stack.append((tag, a.get("id"), pos, (a.get("class") or "").split()))

        def handle_endtag(self, tag):
            pos = offs[self.getpos()[0] - 1] + self.getpos()[1]
            for k in range(len(self.stack) - 1, -1, -1):
                if self.stack[k][0] == tag:
                    t, i, p0, cl = self.stack[k]
                    del self.stack[k:]
                    if i and i not in self.spans:
                        self.spans[i] = (p0, pos + len(f"</{tag}>"))
                    for c in cl:
                        self.cls.setdefault(c, (p0, pos + len(f"</{tag}>")))
                    break

    pr = P()
    pr.feed(src)
    ins = []
    for k, sl in enumerate(slots):
        pos = sl["pos"]
        div = (f'<div class="kslot kslot-{sl["form"]}" data-kslot="{k}" style="width:{sl["w"]}px;height:{sl["h"]}px">'
               f'<img alt="" src="orn/plate-{slug}-s{k}.svg" width="{sl["w"]}" height="{sl["h"]}"></div>')
        if pos == "after:.kfhead" and "kfhead khasslot" not in src:   # a front's planned vignette replaces the head's stock plate
            src = re.sub(r'class="kfhead"', 'class="kfhead khasslot"', src, count=1)
            pr = P()
            pr.feed(src)
        if pos == "head":
            m = re.search(r'<main id="kmain">', src)
            if m:
                ins.append((m.end(), div))
        elif pos.startswith(("before:", "after:")):
            ref = pos.split(":", 1)[1]
            sp = pr.spans.get(ref[1:]) if ref.startswith("#") else pr.cls.get(ref[1:])
            if sp:
                ins.append((sp[0] if pos.startswith("before") else sp[1], div))
            else:
                print(f"kindle_plates: {slug}: slot anchor {pos} not found", file=sys.stderr)
    for at, div in sorted(ins, reverse=True):
        src = src[:at] + div + src[at:]
    return src


def _load(slug):
    p = os.path.join(PLATES, slug + ".py")
    spec = importlib.util.spec_from_file_location("kindle_plate_" + re.sub(r"\W", "_", slug), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.plate


def _snap(svg):
    try:
        from . import snap_svg
        snap_svg.FINE_MAX = 0.6
        return snap_svg.snap(svg)
    except Exception as e:  # noqa: BLE001  -- an unsnapped plate still prints
        print(f"kindle_plates: snap skipped ({e!r})", file=sys.stderr)
        return svg


def run(out, date_iso, exe=None):
    slugs = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(PLATES, "*.py")) if not os.path.basename(p).startswith("_"))
    pages = [s for s in slugs if os.path.exists(os.path.join(out, s + ".html"))]
    if not pages:
        return 0
    if HERE not in sys.path:   # plate modules import the house library (engraving_codex) and its siblings by name
        sys.path.insert(0, HERE)
    od = os.path.join(out, "orn")
    os.makedirs(od, exist_ok=True)
    for f in glob.glob(os.path.join(od, "plate-*.svg")):
        os.remove(f)
    made, t0 = 0, time.time()
    import functools
    import http.server
    import threading
    # served over http, not file://, so the self-hosted fonts load and the sheets cut exactly as on the Kindle
    srv = _QuietServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=out))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    for f in glob.glob(os.path.join(od, "fill-*.svg")) + glob.glob(os.path.join(od, "fill-*.png")):
        os.remove(f)
    for f in glob.glob(os.path.join(od, "plate-*.png")):
        if re.search(r"-s\d+\.png$", f):
            os.remove(f)
    try:
        nw = _nworkers()
        if nw > 1 and len(pages) > 1:   # pages are independent: each worker measures and engraves its share with its own browser
            import multiprocessing as _mp
            from concurrent.futures import ProcessPoolExecutor
            heavy = sorted(pages, key=lambda s_: -os.path.getsize(os.path.join(PLATES, s_ + ".py")))
            with ProcessPoolExecutor(max_workers=nw, mp_context=_mp.get_context("spawn")) as px:
                made = sum(px.map(_pass_chunk, [(heavy[i::nw], out, od, base, date_iso, exe) for i in range(nw) if heavy[i::nw]]))
        else:
            made = _pass(pages, out, od, base, date_iso, exe)
        print(f"kindle_plates: {made} plates on {len(pages)} pages in {time.time() - t0:.1f}s")
        t1 = time.time()
        try:
            del SPACE[:]
            nf = _fills(pages, out, od, base, date_iso, exe)
            SPACE.sort(key=lambda e: (e["page"], e["sheet"]))   # measured in parallel: a stable order
            with open(os.path.join(out, "space-map.json"), "w") as f:
                json.dump(dict(date=date_iso, sheet=[618, 714], note="CSS px; rooms are open rectangles after panels and plates, "
                               "kind gap = between panels, room = elsewhere (foot of the sheet), strip = thin bands", sheets=SPACE), f, indent=1)
            print(f"kindle_plates: {nf} engraved fills in {time.time() - t1:.1f}s")
        except Exception as e:  # noqa: BLE001  -- no fills: the light ground and fleurons stay
            print(f"kindle_plates: fills skipped ({e!r})", file=sys.stderr)
        try:
            t2 = time.time()
            print(f"kindle_plates: {_raster(pages, out, od, base, exe)} slot plates and fills as 16-grey PNG in {time.time() - t2:.1f}s")
        except Exception as e:  # noqa: BLE001  -- the SVGs stay
            print(f"kindle_plates: PNG pass skipped ({e!r})", file=sys.stderr)
    finally:
        srv.shutdown()
    return made


import http.server as _hs  # noqa: E402


class _QuietServer(_hs.ThreadingHTTPServer):
    def handle_error(self, request, client_address):   # a browser hanging up early is not news
        pass


class _Quiet(_hs.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _nworkers():
    return max(1, int(os.environ.get("KINDLE_FIELD_WORKERS") or (4 if os.environ.get("CI") else min(8, os.cpu_count() or 1))))


def _pass_chunk(job):
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    return _pass(*job)


def _pass(pages, out, od, base, date_iso, exe):
    from playwright.sync_api import sync_playwright  # only the morning build needs a browser
    made = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=exe or os.environ.get("KINDLE_CHROMIUM") or None)
        for slug in pages:   # a fresh context each page: no section-change flash or saved place from the page before
            cx = br.new_context(viewport={"width": 618, "height": 714}, has_touch=True)
            pg = cx.new_page()
            fp = os.path.join(out, slug + ".html")
            src = re.sub(r'<div class="kslot[^"]*" data-kslot="\d+"[^>]*><img[^>]*></div>', "", open(fp).read())
            slots = plate_slots.for_page(slug, src)
            planned = bool(slots)
            slots = [sl for sl in slots if sl["form"] != "none"]
            flow = [(k, sl) for k, sl in enumerate(slots) if sl["pos"] not in ("tail", "margin")]
            tails = [sl for sl in slots if sl["pos"] == "tail"]
            margins = [sl for sl in slots if sl["pos"] == "margin"]
            cx.close()

            def meas(html):
                with open(fp, "w") as f:
                    f.write(html)
                c2 = br.new_context(viewport={"width": 618, "height": 714}, has_touch=True)
                p2 = c2.new_page()
                try:
                    p2.goto(base + slug + ".html", wait_until="load")
                    p2.evaluate("document.fonts ? document.fonts.ready.then(() => 0) : 0")
                    return p2.evaluate(MEASURE, 0)
                finally:
                    c2.close()
            rung = lambda r: len(re.findall(r"kfit\d", (r or {}).get("fit", "")))
            src_orig = src
            if any(sl["pos"] == "after:.kfhead" for _, sl in flow):   # the base a front is judged against: no stock head plate
                src = re.sub(r'class="kfhead"', 'class="kfhead khasslot"', src, count=1)
            try:
                res = meas(src)
                if flow and res:
                    # in-flow art never reflows the data: no extra sheet and no tighter type than the page had
                    # without it; else the slot steps down (100, 80, 65 %) and is dropped if it still does not fit
                    base0, n0, ok = res, len(res["rooms"]), False
                    for sc in (1., .8, .65, .5):
                        # a slot keeps its shape: width and height step down together, never under MIN_SCENE
                        # tall (a squashed band cannot read); a full-width headpiece does not step down at all
                        trial = [sl if (k, sl) not in flow else
                                 dict(sl, w=int(sl["w"] * (1 if sl["form"] == "headpiece" else sc)), h=int(sl["h"] * (1 if sl["form"] == "headpiece" else sc)))
                                 for k, sl in enumerate(slots)]
                        if sc < 1 and any(sl["form"] == "headpiece" or sl["h"] < min(MIN_SCENE, slots[k]["h"]) for k, sl in flow):
                            break
                        for k, sl in enumerate(trial):   # a stand-in at each slot's path: a missing image lays out unlike the plate
                            with open(os.path.join(od, f"plate-{slug}-s{k}.svg"), "w") as f:
                                f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{sl["w"]}" height="{sl["h"]}"/>')
                        r2 = meas(_insert_slots(src, slug, [sl if (k, sl0) in flow else dict(sl, pos="none") for k, (sl, sl0) in enumerate(zip(trial, slots))]))
                        if os.environ.get("KSLOT_DEBUG"):
                            print(f"kindle_plates: {slug} slot x{sc}: base {n0} {base0.get('fit')!r} -> {len(r2['rooms']) if r2 else None} {(r2 or {}).get('fit')!r}", file=sys.stderr)
                        if r2 and len(r2["rooms"]) <= n0 and rung(r2) <= max(rung(base0), 1):
                            slots, res, ok = trial, r2, True
                            flow = [(k, sl) for k, sl in enumerate(slots) if sl["pos"] not in ("tail", "margin")]
                            break
                    if not ok:   # no room in the flow: the plate moves to a sheet with room after its last panel
                        print(f"kindle_plates: {slug}: no room for its {flow[0][1]['form']} in the flow; set in a sheet's open room instead", file=sys.stderr)
                        tails = tails + [dict(sl, pos="tail", sheet=None) for _, sl in flow]
                        flow, res = [], meas(src_orig)
            except Exception as e:  # noqa: BLE001
                print(f"kindle_plates: {slug}: measure failed ({e!r})", file=sys.stderr)
                continue
            if not res:
                continue
            try:
                plate = _load(slug)
            except Exception as e:  # noqa: BLE001
                print(f"kindle_plates: {slug}: plate module failed ({e!r})", file=sys.stderr)
                continue
            for k, sl in flow:   # the in-flow slots: drawn to their exact size and shape
                ctx = dict(res["ctx"], slug=slug, date=date_iso, sheet=-1, form=sl["form"], shape=sl["shape"], egg=sl.get("egg", ""), subject=sl.get("subject", ""))
                try:
                    svg = plate(sl["w"], sl["h"], ctx)
                    with open(os.path.join(od, f"plate-{slug}-s{k}.svg"), "w") as f:
                        f.write(_snap(_shape(svg, sl["w"], sl["h"], sl["shape"], sl.get("arms"))))
                    made += 1
                except Exception as e:  # noqa: BLE001
                    print(f"kindle_plates: {slug} slot {k}: plate failed ({e!r})", file=sys.stderr)
            for sl in margins:   # a marginal device: drawn now, set into the fill layer on the frame band
                ctx = dict(res["ctx"], slug=slug, date=date_iso, sheet=-1, form="device", shape="circle", egg=sl.get("egg", ""), subject=sl.get("subject", ""))
                try:
                    with open(os.path.join(od, f"plate-{slug}-m.svg"), "w") as f:
                        f.write(_snap(_shape(plate(sl["w"], sl["h"], ctx), sl["w"], sl["h"], "circle")))
                except Exception as e:  # noqa: BLE001
                    print(f"kindle_plates: {slug}: device failed ({e!r})", file=sys.stderr)
            kmap = []
            nsh = len(res["rooms"])
            place = {}   # sheet -> (room, spec): each planned tail art in a room that holds it unsquashed

            def seat(spec):
                fit = []
                for r in res["rooms"]:
                    sc = min(1., r["h"] / spec["h"], r["w"] / spec["w"])   # never enlarged; shrunk only whole
                    if r["sheet"] in place or spec["h"] * sc < min(MIN_SCENE, spec["h"]) or r["h"] < MIN_H:
                        continue
                    own = spec.get("sheet") is not None and (spec["sheet"] % nsh) == r["sheet"]
                    fit.append((not own, sc < 1, -r["sheet"], r, sc))   # its own sheet, then whole, then the later sheet
                if not fit:
                    return False
                _, _, _, r, sc = min(fit, key=lambda f: f[:3])
                place[r["sheet"]] = (dict(r, w=int(spec["w"] * sc), h=int(spec["h"] * sc)), spec)
                return True
            for spec in tails:
                if seat(spec):
                    continue
                if spec["form"] not in ("tailpiece", "device"):   # else the plan's smaller form, at its own size
                    w_, h_ = plate_slots._size("tailpiece", .08, spec["shape"])
                    if seat(dict(spec, form="tailpiece", w=w_, h=h_)):
                        print(f"kindle_plates: {slug}: its {spec['form']} set as a tailpiece (no open room holds it unsquashed)", file=sys.stderr)
                        continue
                print(f"kindle_plates: {slug}: no open room holds its {spec['form']} unsquashed; left out", file=sys.stderr)
            for r in res["rooms"]:
                if r["h"] < MIN_H:
                    continue
                spec = None
                if tails:   # a planned tailpiece, vignette or plate: its own size and shape, in a room that holds it
                    if r["sheet"] not in place:
                        continue
                    r, spec = place[r["sheet"]]
                elif planned:
                    continue    # planned art only: never a plate cut to the leftover room
                ctx = dict(res["ctx"], slug=slug, date=date_iso, sheet=r["sheet"])
                if spec:
                    ctx.update(form=spec["form"], shape=spec["shape"], egg=spec.get("egg", ""), subject=spec.get("subject", ""))
                try:
                    svg = plate(r["w"], r["h"], ctx)
                    if spec:
                        svg = _shape(svg, r["w"], r["h"], spec["shape"])
                except Exception as e:  # noqa: BLE001
                    print(f"kindle_plates: {slug}~{r['sheet'] + 1}: plate({r['w']},{r['h']}) failed ({e!r})", file=sys.stderr)
                    continue
                if not svg or "<svg" not in svg:
                    continue
                with open(os.path.join(od, f"plate-{slug}-{r['sheet']}.svg"), "w") as f:
                    f.write(_snap(svg))
                kmap.append([r["sheet"], r["h"], r["w"]] + ([1] if spec else []))
            s = re.sub(r" data-kplates='[^']*'", "", open(fp).read(), count=1)
            if kmap:
                s = re.sub(r"<body\b", "<body data-kplates='" + _html.escape(json.dumps(kmap, separators=(",", ":"))) + "'", s, count=1)
            with open(fp, "w") as f:
                f.write(s)
            made += len(kmap)
        br.close()
    return made


# ------------------------------------------------------------------------------------------------
# engraved fills: after the plates are in, measure each sheet's panels (window.KLAB, the pager's own
# measure: every block of text is one full-width white panel) and cut the paper left between them inside
# the frame into rectangles: gaps of 14 px and more get a Himmapan frieze, thinner ones beading, slivers
# plain black. Nothing is ever drawn beside text: the panels span the column. One SVG per
# sheet, orn/fill-<slug>-<sheet>.svg; <body data-kfills='[[sheet, labels, decor], ...]'> lets the pager
# show it only when the device lays the sheet out the same way.
# ------------------------------------------------------------------------------------------------

FX0, FY0, FX1, FY1, FC = 40, 40, 578, 674, 2      # the panel inside the frame, and the grid cell (px)

FILL_MEASURE = """async (P) => {
  const wait = (f, ms) => new Promise(r => { const t0 = Date.now(); (function k() { if (f() || Date.now() - t0 > ms) r(); else setTimeout(k, 30); })(); });
  await wait(() => window.KROOM && window.KLAB, 4000);
  if (!window.KROOM || !window.KLAB || window.innerWidth !== 618 || window.innerHeight !== 714) return null;
  await new Promise(r => setTimeout(r, 500));
  const [X0, Y0, X1, Y1, C] = P, gw = Math.floor((X1 - X0) / C), gh = Math.floor((Y1 - Y0) / C);
  function cut(L) {
    const occ = new Uint8Array(gw * gh), lab = new Uint8Array(gw * gh);
    const mark = (r, m, a) => { const i0 = Math.max(0, Math.floor((r[0] - m - X0) / C)), i1 = Math.min(gw, Math.ceil((r[0] + r[2] + m - X0) / C)),
                                      j0 = Math.max(0, Math.floor((r[1] - m - Y0) / C)), j1 = Math.min(gh, Math.ceil((r[1] + r[3] + m - Y0) / C));
      for (let j = j0; j < j1; j++) for (let i = i0; i < i1; i++) { occ[j * gw + i] = 1; if (a) a[j * gw + i] = 1; } };
    L.o.forEach(r => mark(r, 1, lab)); L.p.forEach(r => mark(r, 1, lab)); L.d.forEach(r => mark(r, 2, null));
    const H = new Int32Array(gw);
    function best(minS, minL) {   // the largest free rectangle with both sides >= minS cells and one >= minL
      H.fill(0); let B = null, ba = 0;
      for (let j = 0; j < gh; j++) {
        for (let i = 0; i < gw; i++) H[i] = occ[j * gw + i] ? 0 : H[i] + 1;
        const st = [];
        for (let i = 0; i <= gw; i++) { const hh = i < gw ? H[i] : 0; let s0 = i;
          while (st.length && st[st.length - 1][1] >= hh) { const [si, sh] = st.pop(); const w = i - si;
            if (sh >= minS && w >= minS && Math.max(sh, w) >= minL && w * sh > ba) { ba = w * sh; B = [si, j - sh + 1, w, sh]; } s0 = si; }
          st.push([s0, hh]); } }
      return B; }
    const take = (b) => { for (let j = b[1]; j < b[1] + b[3]; j++) for (let i = b[0]; i < b[0] + b[2]; i++) occ[j * gw + i] = 1; };
    const px = b => [X0 + b[0] * C, Y0 + b[1] * C, b[2] * C, b[3] * C];
    const panels = [], strips = [], ground = [];
    let b;
    while ((b = best(7, 7)) && panels.length < 60) {   // panels: grown from the side that meets the most label
      const sc = { l: 0, r: 0, t: 0, b: 0 };
      for (let j = b[1]; j < b[1] + b[3]; j++) { if (b[0] > 0 && lab[j * gw + b[0] - 1]) sc.l++; if (b[0] + b[2] < gw && lab[j * gw + b[0] + b[2]]) sc.r++; }
      for (let i = b[0]; i < b[0] + b[2]; i++) { if (b[1] > 0 && lab[(b[1] - 1) * gw + i]) sc.t++; if (b[1] + b[3] < gh && lab[(b[1] + b[3]) * gw + i]) sc.b++; }
      let g = 'l'; for (const k of ['l', 'r', 't', 'b']) if (sc[k] > sc[g]) g = k;
      if (b[2] > 3 * b[3]) g = 'l'; else if (b[3] > 3 * b[2]) g = 't';   // a gap between panels runs as a frieze
      take(b); panels.push(px(b).concat([g])); }
    while ((b = best(2, 7)) && strips.length < 120) { take(b); strips.push(px(b)); }
    for (let j = 0; j < gh && false; j++) { let i = 0;   // (slivers keep the light ground)
      while (i < gw) { if (occ[j * gw + i]) { i++; continue; } let e = i; while (e < gw && !occ[j * gw + e]) e++;
        const last = ground.length && ground[ground.length - 1];
        if (last && last[0] === X0 + i * C && last[2] === (e - i) * C && last[1] + last[3] === Y0 + j * C) last[3] += C;
        else ground.push([X0 + i * C, Y0 + j * C, (e - i) * C, C]);
        i = e; } }
    // and black under every label's edge, so no paper shows between a label's rule and the fill
    L.o.forEach(r => { const x0 = Math.max(X0, r[0] - 2), y0 = Math.max(Y0, r[1] - 2), x1 = Math.min(X1, r[0] + r[2] + 2), y1 = Math.min(Y1, r[1] + r[3] + 2);
      if (x1 > x0 && y1 > y0) ground.push([x0, y0, x1 - x0, y1 - y0]); });
    const between = r => { const i0 = Math.floor((r[0] - X0) / C), i1 = i0 + Math.floor(r[2] / C), ja = Math.floor((r[1] - Y0) / C) - 1, jb = Math.floor((r[1] + r[3] - Y0) / C);
      let up = false, dn = false;
      for (let i = i0; i < i1; i++) { if (ja >= 0 && lab[ja * gw + i]) up = true; if (jb < gh && lab[jb * gw + i]) dn = true; }
      return up && dn; };
    panels.forEach(p => p.push(between(p))); strips.forEach(p => p.push(between(p)));
    return { panels, strips, ground };
  }
  const out = [], n = window.KROOM.sheets;
  for (let i = 0; i < n; i++) {
    if (i) { const more = document.getElementById('kmore'); if (!more) break; more.click();
             await wait(() => window.KROOM.sheet === i, 3000); await new Promise(r => setTimeout(r, 400)); }
    const L = window.KLAB();
    const vr = document.getElementById('kclip').getBoundingClientRect();
    out.push(Object.assign({ sheet: i, n, vr: [vr.left, vr.top, vr.width, vr.height], o: L.o, d: L.d, p: L.p }, cut(L)));
  }
  return out;
}"""


def _raster(pages, out, od, base, exe):
    """The slot plates and the sheet fills as 16-grey PNGs at the Kindle's 2x: an <img> of an SVG is a whole
    document to parse and lay out on the page's own thread (as the next page is warmed, too); a PNG is a decode."""
    from playwright.sync_api import sync_playwright
    from .kindle_fast import _png16
    n = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=exe or os.environ.get("KINDLE_CHROMIUM") or None)
        pg = br.new_context(device_scale_factor=2).new_page()

        def shot(name, w, h):
            pg.set_viewport_size({"width": w, "height": h})
            pg.set_content(f'<!doctype html><html style="background:transparent"><body style="margin:0;background:transparent">'
                           f'<img src="{base}orn/{name}.svg" width="{w}" height="{h}" style="display:block"></body></html>', wait_until="load")
            _png16(pg.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h}), os.path.join(od, name + ".png"), False)
        for slug in pages:
            fp = os.path.join(out, slug + ".html")
            s = open(fp).read()
            slots = re.findall(r'<img alt="" src="orn/(plate-[\w-]+-s\d+)\.svg" width="(\d+)" height="(\d+)">', s)
            for name, w, h in slots:
                shot(name, int(w), int(h))
                s = s.replace(f'src="orn/{name}.svg"', f'src="orn/{name}.png"')
                n += 1
            with open(fp, "w") as f:
                f.write(s)
        br.close()
    for f in glob.glob(os.path.join(od, "plate-*.svg")):   # stand-ins of slots that were dropped
        if re.search(r"-s\d+\.svg$", f) and not os.path.exists(f[:-4] + ".png"):
            os.remove(f)
    return n


SPACE = []   # filled by _fills; written to orn/space-map.json


def _fills(pages, out, od, base, date_iso, exe):
    import zlib
    from concurrent.futures import ProcessPoolExecutor
    made, jobs, fmaps = 0, [], {}
    nw = _nworkers()
    import multiprocessing as _mp
    pool = ProcessPoolExecutor(max_workers=max(1, nw), mp_context=_mp.get_context("spawn"))   # a field is 1-3 s a sheet: drawn in parallel processes
    from concurrent.futures import as_completed
    if True:   # each page is measured in a worker too (its own browser): the fields are queued as pages come back
        meas = {pool.submit(_fill_measure, (slug, base, exe)): slug for slug in pages}
        for fu in as_completed(meas):
            slug = meas[fu]
            res, title = fu.result()
            fmap = []
            sec = slug.split("-")[0]
            for r in res or []:   # the space map: every open room on the sheet, for the studio to draw bespoke art to
                rooms = ([dict(x=p[0], y=p[1], w=p[2], h=p[3], kind="gap" if p[5] else "room") for p in r["panels"]]
                         + [dict(x=p[0], y=p[1], w=p[2], h=p[3], kind="strip") for p in r["strips"]])
                if rooms:
                    SPACE.append(dict(page=slug, sheet=r["sheet"], section=sec, title=title,
                                      subject=plate_slots.FRONTS[sec][1] if slug == sec and sec in plate_slots.FRONTS else title,
                                      rooms=rooms))
            for r in res or []:   # the sheet's ground: one composed scroll field round its panels (claude/engrave-frames)
                vt, vb = r["vr"][1], r["vr"][1] + r["vr"][3]
                boxes = [(q, True) for q in r["o"]] + [(q, False) for q in r["p"]]
                boxes += [(q, False) for q in r["d"] if not any(o[0] <= q[0] + 1 and o[1] <= q[1] + 1 and o[0] + o[2] >= q[0] + q[2] - 1
                                                                and o[1] + o[3] >= q[1] + q[3] - 1 for o in r["o"])]
                edges = []
                for q, white in boxes:
                    x, y, w, h = q[:4]
                    ot = white and r["sheet"] > 0 and y <= vt + 1
                    ob = white and r["sheet"] < r["n"] - 1 and y + h >= vb - 1
                    edges.append((x, y, w, h, ot, ob))
                seed = zlib.crc32(f"{slug}/{r['sheet']}".encode()) % 100003   # no date: an unchanged sheet reuses its cached field
                dev = None
                dp = os.path.join(od, f"plate-{slug}-m.svg")
                if r["sheet"] == 0 and os.path.exists(dp):   # the plan's marginal device: a roundel on the frame band, beside the widest panel gap
                    ob = sorted(r["o"], key=lambda q: q[1])
                    gaps = [(b2[1] - (a2[1] + a2[3]), a2[1] + a2[3] + (b2[1] - (a2[1] + a2[3])) / 2) for a2, b2 in zip(ob, ob[1:])]
                    gy = max(gaps)[1] if gaps and max(gaps)[0] > 0 else (vt + vb) / 2
                    dev = (open(dp).read(), 1, int(min(max(gy - 19, FY0), FY1 - 38)))
                jobs.append(((slug, r["sheet"]), pool.submit(_field_svg, (slug, r["sheet"], edges, seed, MOTIF_OF(slug), od, exe, dev))))   # drawn while the browser measures on
                enc = lambda L: " ".join(",".join(str(v) for v in q) for q in L)
                fmap.append([r["sheet"], enc(r["o"]), enc(r["d"]), enc(r["p"])])
            fmaps[slug] = fmap
    done = {k: f.result() for k, f in jobs}
    pool.shutdown()
    for f in glob.glob(os.path.join(od, "plate-*-m.svg")):   # the devices are in the fields now
        os.remove(f)
    for slug, fmap in fmaps.items():
        fmap = [e for e in fmap if done.get((slug, e[0]))]
        fp = os.path.join(out, slug + ".html")
        s = re.sub(r" data-kfills='[^']*'", "", open(fp).read(), count=1)
        if fmap:   # the fields are PNG already (drawn and rasterised in the workers; no SVG written)
            s = re.sub(r"<body\b", "<body data-kfills='" + _html.escape(json.dumps(fmap, separators=(",", ":"))) + "'", s, count=1)
            s = re.sub(r"<body\b", '<body data-kfx=".png"', s, count=1) if " data-kfx=" not in s else s
        with open(fp, "w") as f:
            f.write(s)
        made += len(fmap)
    return made


def MOTIF_OF(slug):
    """The centre motif of a section's field, by name (resolved in the worker by _motif): the section's own
    when the studio's field module carries it (SECTION_MOTIFS[section], a callable(cv, x, y, size)), else
    one of its stock set, fixed per section."""
    sec = slug.split("-")[0]
    if _section_motif(sec):
        return "sec:" + sec
    return ("fleuron", "shell", "rosette")[zlib.crc32(sec.encode()) % 3]


def _section_motif(sec):
    try:
        from .frames import field as FF
    except Exception:  # noqa: BLE001
        return None
    m = getattr(FF, "SECTION_MOTIFS", None) or getattr(FF.scroll, "SECTION_MOTIFS", None) or {}
    f = m.get(sec)
    return f if callable(f) else None


def _motif(name):
    return (_section_motif(name[4:]) or "fleuron") if name.startswith("sec:") else name


_WPG = []


def _worker_browser(exe):
    """One playwright and one browser per worker process (sync playwright allows one per process), kept for
    all its jobs: page measures and field rasters."""
    if not _WBR:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        br = pw.chromium.launch(executable_path=exe or os.environ.get("KINDLE_CHROMIUM") or None)
        _WBR.append(br)
        import atexit
        from multiprocessing import util as _mu

        def _close():
            try:
                br.close()
                pw.stop()
            except Exception:  # noqa: BLE001
                pass
        atexit.register(_close)
        _mu.Finalize(None, _close, exitpriority=10)
    return _WBR[0]


_WBR = []


def _worker_page(exe):
    """The worker's 2x page: the field is drawn and rasterised in the worker."""
    if not _WPG:
        _WPG.append(_worker_browser(exe).new_context(device_scale_factor=2, viewport={"width": 618, "height": 714}).new_page())
    return _WPG[0]


FIELD_MAX = 100 * 1024
FIELD_GREYS = ((0, 136, 204, 255), (0, 204, 255), (0, 255))   # tried in turn until the sheet fits FIELD_MAX


def _field_png(im):
    """The field as the smallest-level PNG that fits: 4 greys (2-bit), else 3 greys (2-bit), else 1 bit. Studio
    greys map to #ccc/#bbb -> light, #aaa/#888 -> mid. Rows unfiltered with Z_FILTERED deflate: on this art that
    beats PIL's adaptive filters by ~12%."""
    import numpy as np
    import struct
    v = np.asarray(im.convert("L"))
    h, w = v.shape
    out = b""
    for pal in FIELD_GREYS:
        if len(pal) == 4:
            idx = np.select([v < 68, v <= 170, v < 230], [0, 1, 2], 3)
        elif len(pal) == 3:
            idx = np.select([v < 102, v < 230], [0, 1], 2)
        else:
            idx = (v >= 128).astype(np.uint8)
        idx = idx.astype(np.uint8)
        bits = 1 if len(pal) == 2 else 2
        per = 8 // bits
        a = np.pad(idx, ((0, 0), (0, (-w) % per)))
        packed = np.zeros((h, a.shape[1] // per), np.uint8)
        for k in range(per):
            packed |= a[:, k::per] << (8 - bits * (k + 1))
        raw = np.concatenate([np.zeros((h, 1), np.uint8), packed], axis=1).tobytes()
        c = zlib.compressobj(9, zlib.DEFLATED, 15, 9, zlib.Z_FILTERED)
        z = c.compress(raw) + c.flush()

        def chunk(t, d):
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
        out = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, bits, 3, 0, 0, 0))
               + chunk(b"PLTE", b"".join(bytes((g, g, g)) for g in pal)) + chunk(b"IDAT", z) + chunk(b"IEND", b""))
        if len(out) <= FIELD_MAX:
            break
    return out


def _fill_measure(job):
    """One page's sheets, measured as the pager lays them out (window.KLAB), in a worker's own browser."""
    slug, base, exe = job
    try:
        cx = _worker_browser(exe).new_context(viewport={"width": 618, "height": 714}, has_touch=True)
        try:
            pg = cx.new_page()
            pg.goto(base + slug + ".html", wait_until="load")
            pg.evaluate("document.fonts ? document.fonts.ready.then(() => 0) : 0")
            res = pg.evaluate(FILL_MEASURE, [FX0, FY0, FX1, FY1, FC])
            title = pg.evaluate("(() => { const e = document.querySelector('#kmain h2, #kmain .kftitle'); return e ? e.textContent.trim().replace(/\\s+/g, ' ') : document.title; })()")
        finally:
            cx.close()
        return res, title
    except Exception as e:  # noqa: BLE001
        print(f"kindle_plates: {slug}: fill measure failed ({e!r})", file=sys.stderr)
        return None, ""


def _field_svg(job):
    """One sheet's ground: the studio's scroll field with a hole round every white box (its box plus the 4 px
    inlay), and the bright double inlay edge of each box. Rasterised later; the SVG is never shipped."""
    slug, sheet, edges, seed, motif, od, exe, dev = job
    try:
        from .frames import field as FF, kpanel as KP
        B = 4
        holes = [(max(0, x - B), max(0, y - B), min(618, x + w + B) - max(0, x - B), min(714, y + h + B) - max(0, y - B))
                 for x, y, w, h, ot, ob in edges]
        fsv = FF.field(618, 714, holes, seed, motif=_motif(motif), border=True)
        parts = []
        for k, (x, y, w, h, ot, ob) in enumerate(edges):
            esv = KP.panel_edge(w, h, ot, ob, seed + k, b=B)
            esv = re.sub(r"^\s*<\?xml[^>]*>\s*", "", esv)
            parts.append(re.sub(r"<svg\b", f'<svg x="{x - B}" y="{y - B}"', esv, count=1))
        fsv = re.sub(r"^\s*<\?xml[^>]*>\s*", "", fsv)
        if dev:   # set on a white roundel over the band's scrollwork
            dsv, dx, dy = dev
            dsv = re.sub(r"^\s*<\?xml[^>]*>\s*", "", dsv).replace("kshape", "kdevshape")
            dsv = re.sub(r'<svg\b([^>]*?)\swidth="[^"]*"', r"<svg\1", dsv, count=1)
            dsv = re.sub(r'<svg\b([^>]*?)\sheight="[^"]*"', r"<svg\1", dsv, count=1)
            parts.append(f'<circle cx="{dx + 19}" cy="{dy + 19}" r="19" fill="#fff" stroke="#000" stroke-width="1"/>'
                         + re.sub(r"<svg\b", f'<svg x="{dx}" y="{dy}" width="38" height="38"', dsv, count=1))
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="618" height="714" viewBox="0 0 618 714" shape-rendering="crispEdges">'
               + fsv + "".join(parts) + "</svg>")   # crisp: no anti-alias greys, so the four levels below are exact
        import io
        from PIL import Image
        pg = _worker_page(exe)
        pg.set_content('<!doctype html><html style="background:transparent"><body style="margin:0;background:#fff">' + svg + "</body></html>")
        # four greys at 2x (white, light, mid, black): the studio's silver modelling survives, in a 2-bit PNG.
        # A sheet over FIELD_MAX falls back to three greys, then to one bit. Opaque: the holes print white under
        # the white panels anyway.
        im = Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": 0, "width": 618, "height": 714}))).convert("L")
        with open(os.path.join(od, f"fill-{slug}-{sheet}.png"), "wb") as f:
            f.write(_field_png(im))
        return True
    except Exception as e:  # noqa: BLE001
        print(f"kindle_plates: {slug}~{sheet + 1}: field failed ({e!r})", file=sys.stderr)
        return None
