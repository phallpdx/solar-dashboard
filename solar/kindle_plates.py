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

HERE = os.path.dirname(os.path.abspath(__file__))
PLATES = os.path.join(HERE, "plates")
MIN_H = 40   # below this a sheet gets no plate

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
  return { ctx, rooms };
}"""


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
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=out))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    try:
        made = _pass(pages, out, od, base, date_iso, exe)
    finally:
        srv.shutdown()
    print(f"kindle_plates: {made} plates on {len(pages)} pages in {time.time() - t0:.1f}s")
    return made


import http.server as _hs  # noqa: E402


class _Quiet(_hs.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _pass(pages, out, od, base, date_iso, exe):
    from playwright.sync_api import sync_playwright  # only the morning build needs a browser
    made = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=exe or os.environ.get("KINDLE_CHROMIUM") or None)
        for slug in pages:   # a fresh context each page: no section-change flash or saved place from the page before
            cx = br.new_context(viewport={"width": 618, "height": 714}, has_touch=True)
            pg = cx.new_page()
            fp = os.path.join(out, slug + ".html")
            try:
                pg.goto(base + slug + ".html", wait_until="load")
                pg.evaluate("document.fonts ? document.fonts.ready.then(() => 0) : 0")
                res = pg.evaluate(MEASURE, 0)
            except Exception as e:  # noqa: BLE001
                print(f"kindle_plates: {slug}: measure failed ({e!r})", file=sys.stderr)
                cx.close()
                continue
            cx.close()
            if not res:
                continue
            try:
                plate = _load(slug)
            except Exception as e:  # noqa: BLE001
                print(f"kindle_plates: {slug}: plate module failed ({e!r})", file=sys.stderr)
                continue
            kmap = []
            for r in res["rooms"]:
                if r["h"] < MIN_H:
                    continue
                ctx = dict(res["ctx"], slug=slug, date=date_iso, sheet=r["sheet"])
                try:
                    svg = plate(r["w"], r["h"], ctx)
                except Exception as e:  # noqa: BLE001
                    print(f"kindle_plates: {slug}~{r['sheet'] + 1}: plate({r['w']},{r['h']}) failed ({e!r})", file=sys.stderr)
                    continue
                if not svg or "<svg" not in svg:
                    continue
                with open(os.path.join(od, f"plate-{slug}-{r['sheet']}.svg"), "w") as f:
                    f.write(_snap(svg))
                kmap.append([r["sheet"], r["h"], r["w"]])
            s = re.sub(r" data-kplates='[^']*'", "", open(fp).read(), count=1)
            if kmap:
                s = re.sub(r"<body\b", "<body data-kplates='" + _html.escape(json.dumps(kmap, separators=(",", ":"))) + "'", s, count=1)
            with open(fp, "w") as f:
                f.write(s)
            made += len(kmap)
        br.close()
    return made
