"""Speed pass for the Morning Edition, run last in the build (after the plates are cut).

The Paperwhite's browser is Chrome 75 on a slow ARM CPU, so every page turn has to cost it as little as possible.
Everything here is post-processing of what kindle_full / kindle_plates / ornament already wrote to <site>/kindle/;
the art and layout code stay the source of truth, this pass only changes how the result is delivered:

1. Raster art. The page's background (the engraved frame, the section's paper ground and cartouche) is drawn by
   headless Chromium exactly as the Kindle draws it, at device pixels (618 x 714 CSS px, DPR 2), and saved as one
   opaque 16-grey PNG per section; the bespoke plates likewise become 16-grey PNGs at exactly their shown size x 2.
   The SVGs stay in orn/ as the source. On a 16-grey e-ink panel this is the same picture, minus the work of
   parsing and rasterising thousands of vector paths on every page.
2. Smaller CSS. kindle.css keeps only the rules that match something on some page of this edition (in any state
   the pager can put a page in), and only the custom properties that are still referenced.
3. Less work at load. Every page is laid out once here, in the same browser at the Kindle's size, and the pager's
   answer (fit classes, sheet cuts, white labels, plate placement, gap ornaments: everything show() would compute)
   is written into the page as data-kpre. The pager applies it without measuring anything, and checks once after
   the fonts and pictures are in that the page still has the measured height; if not it lays out as before.

Never fatal: any failure leaves the edition as it was written.
"""
import functools
import glob
import html as _html
import http.server
import json
import os
import re
import sys
import threading
import time

VW, VH, DPR = 618, 714, 2
LEVELS = 16


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


# ---------------------------------------------------------------- 16-grey PNG

def _png16(png_bytes, path, opaque):
    """Save a screenshot as a 16-grey palette PNG (with a 16-step alpha when not opaque)."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes))
    if opaque:
        g = im.convert("L").point(lambda v: (v * (LEVELS - 1) + 127) // 255)
        pal = []
        for k in range(LEVELS):
            c = round(k * 255 / (LEVELS - 1))
            pal += [c, c, c]
        p = Image.frombytes("P", g.size, g.tobytes())
        p.putpalette(pal)
        p.save(path, "PNG", optimize=True, bits=4)
        return
    im = im.convert("RGBA")
    import numpy as np
    a = np.asarray(im, dtype=np.int32)
    # luminance of the (straight-alpha) colour, as Chrome's greyscale would see it
    lum = (a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114 + 500) // 1000
    gq = (lum * (LEVELS - 1) + 127) // 255
    aq = (a[..., 3] * (LEVELS - 1) + 127) // 255
    gq[aq == 0] = 0
    idx = (aq * LEVELS + gq).astype(np.uint8)
    used = np.unique(idx)
    remap = np.zeros(256, dtype=np.uint8)
    remap[used] = np.arange(len(used), dtype=np.uint8)
    pal, trn = [], []
    for u in used.tolist():
        c = round((u % LEVELS) * 255 / (LEVELS - 1))
        pal += [c, c, c]
        trn.append(round((u // LEVELS) * 255 / (LEVELS - 1)))
    p = Image.fromarray(remap[idx], "P")
    p.putpalette(pal)
    bits = 8 if len(used) > 16 else 4
    p.save(path, "PNG", optimize=True, transparency=bytes(trn), bits=bits)


# ---------------------------------------------------------------- CSS

def _split_rules(css):
    """Top-level items of a flat stylesheet (no @media here): [(prelude, body, text)]."""
    out, i, n = [], 0, len(css)
    while i < n:
        j, q, depth, start = i, None, 0, i
        pre_end = None
        while j < n:
            c = css[j]
            if q:
                if c == "\\":
                    j += 2
                    continue
                if c == q:
                    q = None
            elif c == "/" and css.startswith("/*", j):
                e = css.find("*/", j + 2)
                j = n if e < 0 else e + 2
                continue
            elif c in "\"'":
                q = c
            elif c == "{":
                if depth == 0:
                    pre_end = j
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            elif c == ";" and depth == 0:   # @charset / @import
                j += 1
                break
            j += 1
        text = css[start:j]
        if text.strip():
            if pre_end is None:
                out.append((None, None, text))
            else:
                out.append((css[start:pre_end], css[pre_end + 1:j - 1], text))
        i = j
    return out


def _strip_comments(s):
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


_PSEUDO_EL = re.compile(r"::?(before|after|first-line|first-letter|marker|placeholder|selection|backdrop)\b|::-webkit-[\w-]+(\([^)]*\))?|::-moz-[\w-]+")
_PSEUDO_DYN = re.compile(r":(hover|focus|focus-within|focus-visible|active|visited|link|target|checked|default|indeterminate|-webkit-any-link|any-link|enabled|disabled)\b")


def _test_selector(sel):
    """The selector as querySelector can test it: pseudo-elements and state pseudo-classes dropped (a compound
    they leave empty becomes "*")."""
    if ":not(" in sel and (_PSEUDO_EL.search(sel) or _PSEUDO_DYN.search(sel)):
        return "*"   # "not hovered" and the like: keep the rule

    def strip(rx, s):
        def sub(m):
            after = s[m.end():].lstrip(" ")[:1]
            empty_before = s[:m.start()][-1:] in ("", " ", ">", "+", "~", "(", ",")
            empty_after = after in ("", ">", "+", "~", ")", ",") or s[m.end():m.end() + 1] == " "
            return "*" if empty_before and empty_after else ""
        return rx.sub(sub, s)
    s = strip(_PSEUDO_EL, sel.strip())
    s = strip(_PSEUDO_DYN, s)
    return s.strip() or "*"


def _decls(body):
    """Split a declaration block at top-level semicolons, keeping text exact."""
    parts, depth, q, cur = [], 0, None, []
    i = 0
    while i < len(body):
        c = body[i]
        cur.append(c)
        if q:
            if c == "\\" and i + 1 < len(body):
                cur.append(body[i + 1])
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == ";" and depth == 0:
            parts.append("".join(cur))
            cur = []
        i += 1
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def prune_css(css, used_idx, extra_text=""):
    """Keep @font-face/@-rules and the style rules whose index is in used_idx, then drop custom properties
    that nothing references any more."""
    items = _split_rules(css)
    kept = []
    k = 0
    for pre, body, text in items:
        if pre is None or pre.strip().startswith("@"):
            kept.append([pre, body, text])
            continue
        if k in used_idx:
            kept.append([pre, body, text])
        k += 1
    # custom properties: drop declarations of --x nothing refers to (repeat: vars refer to vars)
    for _ in range(6):
        refs = set(re.findall(r"var\(\s*(--[\w-]+)", "".join(t for _, _, t in kept) + extra_text))
        changed = False
        for it in kept:
            pre, body, text = it
            if pre is None or pre.strip().startswith("@") or "--" not in body:
                continue
            ds = _decls(body)
            keep = [d for d in ds if not (re.match(r"\s*(--[\w-]+)\s*:", d) and re.match(r"\s*(--[\w-]+)", d).group(1) not in refs)]
            if len(keep) != len(ds):
                changed = True
                nb = "".join(keep)
                it[1] = nb
                it[2] = pre + "{" + nb + "}"
        if not changed:
            break
    out = []
    for pre, body, text in kept:
        if pre is not None and not pre.strip().startswith("@") and not _strip_comments(body).strip(" \n\t;"):
            continue
        out.append(_strip_comments(text).strip())
    return "\n".join(x for x in out if x) + "\n"


# ---------------------------------------------------------------- browser side

STATE_JS = r"""() => {
  // what the slow pager worked out, sheet by sheet: replayed by the fast path
  const k = window.KPAGER; if (!k) return null;
  return k.snap();
}"""

MATCH_JS = r"""(sels) => {
  const r = document.documentElement, used = [];
  const states = [() => {}, () => { r.classList.add('kfit1','kfit2','kfit3','kfit4','kjumpopen'); r.setAttribute('data-flash','1');
                                    document.querySelectorAll('ol.kfl').forEach(e => e.classList.add('ktight','kcompact')); },
                  () => { r.classList.remove('kpaged'); }];
  const keep = r.className, kfl = [...document.querySelectorAll('ol.kfl')].map(e => e.className), fl = r.getAttribute('data-flash');
  for (const st of states) {
    st();
    for (let i = 0; i < sels.length; i++) {
      if (used[i]) continue;
      try { if (document.querySelector(sels[i])) used[i] = 1; } catch (e) { used[i] = 1; }
    }
    r.className = keep; document.querySelectorAll('ol.kfl').forEach((e, j) => e.className = kfl[j]);
    if (fl === null) r.removeAttribute('data-flash'); else r.setAttribute('data-flash', fl);
  }
  return used.map((u, i) => u ? i : -1).filter(i => i >= 0);
}"""

BG_JS = r"""() => {
  const c = getComputedStyle(document.body, '::before');
  return { img: c.backgroundImage, size: c.backgroundSize, pos: c.backgroundPosition, rep: c.backgroundRepeat,
           w: innerWidth, h: innerHeight };
}"""


ORN_JS = r"""() => {
  // every background layer drawn from an SVG, with the size it is drawn at (CSS px), on this sheet
  const out = [], LAYER = /url\((?:"[^"]*"|[^)]*)\)|[\w-]+\((?:[^()]|\([^()]*\))*\)|none/g;
  for (const el of document.querySelectorAll('*')) {
    if (!el.getClientRects().length) continue;
    for (const ps of [null, '::before', '::after']) {
      const c = getComputedStyle(el, ps), bi = c.backgroundImage;
      if (!bi || bi === 'none' || !/svg/.test(bi)) continue;
      if (ps && (c.content === 'none' || c.display === 'none')) continue;
      let W, H;
      if (!ps) { const r = el.getBoundingClientRect(); W = r.width - parseFloat(c.borderLeftWidth) - parseFloat(c.borderRightWidth); H = r.height - parseFloat(c.borderTopWidth) - parseFloat(c.borderBottomWidth); }
      else { if (!/px$/.test(c.width) || !/px$/.test(c.height)) continue;
        const bb = c.boxSizing === 'border-box';
        W = parseFloat(c.width) + (bb ? -parseFloat(c.borderLeftWidth) - parseFloat(c.borderRightWidth) : parseFloat(c.paddingLeft) + parseFloat(c.paddingRight));
        H = parseFloat(c.height) + (bb ? -parseFloat(c.borderTopWidth) - parseFloat(c.borderBottomWidth) : parseFloat(c.paddingTop) + parseFloat(c.paddingBottom)); }
      const layers = bi.match(LAYER) || [], sizes = c.backgroundSize.split(/,\s*/), origin = c.backgroundOrigin.split(/,\s*/);
      layers.forEach((l, i) => { if (!/^url\(/.test(l) || !/svg/.test(l)) return;
        out.push({ u: l.replace(/^url\("?|"?\)$/g, ''), sz: sizes[i % sizes.length], o: origin[i % origin.length], W, H, n: layers.length === sizes.length }); });
    }
  }
  return out;
}"""


def _pages(out):
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(out, "*.html")))


def _set_attr(doc, tag, name, value):
    """Set one attribute on the first <tag ...> of a page (never anywhere else: the pager's source names them too)."""
    m = re.search(r"<" + tag + r"\b[^>]*>", doc)
    if not m:
        return doc
    t = re.sub(r"\s" + name + r"=(\"[^\"]*\"|'[^']*')", "", m.group(0))
    t = t[:len(tag) + 1] + f' {name}="{value}"' + t[len(tag) + 1:]
    return doc[:m.start()] + t + doc[m.end():]


def _rewrite(fp, fn):
    s = open(fp, encoding="utf-8").read()
    s2 = fn(s)
    if s2 != s:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(s2)


def _layers(b):
    """[(url, w, h)] of the background layers, w/h the drawn size in CSS px (None when not a fixed size)."""
    urls = re.findall(r'url\("?([^")]+)"?\)', b["img"])
    sizes = [x.strip() for x in b["size"].split(",")]
    if len(urls) != len(sizes) or len(urls) != b["img"].count("url("):
        return []
    out = []
    for u, sz in zip(urls, sizes):
        m = re.match(r"^([\d.]+)(px|%) ([\d.]+)(px|%)$", sz)
        if not m:
            out.append((u, None, None))
            continue
        w = float(m.group(1)) * (b["w"] / 100 if m.group(2) == "%" else 1)
        h = float(m.group(3)) * (b["h"] / 100 if m.group(4) == "%" else 1)
        out.append((u, w, h) if w == int(w) and h == int(h) else (u, None, None))
    return out


def run(out, exe=None):
    t0 = time.time()
    if not os.path.exists(os.path.join(out, "kindle.css")):
        return
    try:
        import asyncio
        from playwright.async_api import async_playwright  # noqa: F401
    except Exception as e:  # noqa: BLE001
        print(f"kindle_fast: skipped ({e!r})", file=sys.stderr)
        return
    srv, base = _serve(out)
    try:
        stats = asyncio.run(_run(out, base, exe))
    finally:
        srv.shutdown()
    try:
        stats["fonts"] = subset_fonts(out)
    except Exception as e:  # noqa: BLE001
        print(f"kindle_fast: fonts left whole ({e!r})", file=sys.stderr)
    print(f"kindle_fast: {stats} in {time.time() - t0:.1f}s")


WORKERS = 4


async def _pool(items, fn):
    import asyncio
    q = list(items)
    res = {}

    async def worker():
        while q:
            it = q.pop(0)
            try:
                res[it] = await fn(it)
            except Exception as e:  # noqa: BLE001
                print(f"kindle_fast: {it}: {e!r}", file=sys.stderr)
                res[it] = None
    await asyncio.gather(*[worker() for _ in range(WORKERS)])
    return res


async def _run(out, base, exe):
    from playwright.async_api import async_playwright
    stats = {}
    async with async_playwright() as pw:
        br = await pw.chromium.launch(executable_path=exe or os.environ.get("KINDLE_CHROMIUM") or None)
        try:
            stats["plates"] = await _plates(br, out, base)
        except Exception as e:  # noqa: BLE001
            print(f"kindle_fast: plates left as SVG ({e!r})", file=sys.stderr)
        try:
            stats["letters"] = await _letters(br, out, base)
        except Exception as e:  # noqa: BLE001
            print(f"LETTERING FALLBACK: headlines left as SVG, not PNG ({e!r})", file=sys.stderr)
        css_path = os.path.join(out, "kindle.css")
        css = open(css_path, encoding="utf-8").read()
        sels = [_test_selector(_strip_comments(pre)) for pre, body, text in _split_rules(css)
                if pre is not None and not pre.strip().startswith("@")]
        visits = await _visit_all(br, out, base, sels)
        try:
            stats["pre"] = _write_pre(out, visits)
        except Exception as e:  # noqa: BLE001
            print(f"kindle_fast: layout pass skipped ({e!r})", file=sys.stderr)
        swap = {}
        try:
            swap, stats["art"] = await _ornaments(br, out, base, css, visits)
        except Exception as e:  # noqa: BLE001
            print(f"kindle_fast: CSS art left as SVG ({e!r})", file=sys.stderr)
        try:
            used = set()
            for v in visits.values():
                if v:
                    used.update(v["used"])
            extra = ""
            for p in _pages(out):
                extra += " ".join(re.findall(r'style="([^"]*var\(--[^"]*)"', open(os.path.join(out, p + ".html"), encoding="utf-8").read()))
            new = prune_css(css, used, extra)
            stats["css"] = f"{len(used)}/{len(sels)} rules, {len(css)} -> {len(new)} bytes"
        except Exception as e:  # noqa: BLE001
            print(f"kindle_fast: stylesheet left whole ({e!r})", file=sys.stderr)
            new = css
        if swap:
            new = _swap_urls(new, base, swap)
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(new)
        await br.close()
    return stats


async def _shot(pg, html_doc, w, h, opaque, dst):
    await pg.set_viewport_size({"width": max(w, 16), "height": max(h, 16)})
    await pg.set_content(html_doc, wait_until="load")
    await pg.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    _png16(await pg.screenshot(omit_background=not opaque, clip={"x": 0, "y": 0, "width": w, "height": h}), dst, opaque=opaque)


async def _plates(br, out, base):
    """Each plate at exactly its shown size, x2, as a 16-grey PNG with a 16-step alpha."""
    od = os.path.join(out, "orn")
    jobs, pages_ok = [], {}
    for p in _pages(out):
        s = open(os.path.join(out, p + ".html"), encoding="utf-8").read()
        m = re.search(r"<body\b[^>]*\sdata-kplates='([^']*)'", s)
        if not m:
            continue
        ks = json.loads(_html.unescape(m.group(1)))
        if all(os.path.exists(os.path.join(od, f"plate-{p}-{k[0]}.svg")) for k in ks):
            pages_ok[p] = ks
            jobs += [(p, k[0], k[1], k[2]) for k in ks]
    cx = await br.new_context(device_scale_factor=DPR)
    pages = [await cx.new_page() for _ in range(WORKERS)]
    free = list(pages)

    async def one(job):
        p, sheet, h, w = job
        pg = free.pop()
        try:
            await _shot(pg, f'<!doctype html><html style="background:transparent"><body style="margin:0;background:transparent">'
                            f'<img src="{base}orn/plate-{p}-{sheet}.svg" width="{w}" height="{h}" style="display:block"></body></html>',
                        w, h, False, os.path.join(od, f"plate-{p}-{sheet}.png"))
            return True
        finally:
            free.append(pg)
    res = await _pool(jobs, one)
    await cx.close()
    n = 0
    for p, ks in pages_ok.items():
        if all(res.get((p, k[0], k[1], k[2])) for k in ks):
            _rewrite(os.path.join(out, p + ".html"), lambda s: _set_attr(s, "body", "data-kpx", ".png"))
            n += len(ks)
    return n


async def _visit_all(br, out, base, sels):
    """Every page once, at the Kindle's size: the pager's worked-out layout, the page background, and which
    stylesheet rules match anything (in any state the pager can put the page in)."""
    ed = re.search(r'data-ed="([^"]*)"', open(os.path.join(out, "index.html"), encoding="utf-8").read()) \
        if os.path.exists(os.path.join(out, "index.html")) else None

    async def one(p):
        resume = p == "index~resume"
        cx = await br.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=DPR, has_touch=True)   # as the Kindle: sub-pixel text
        if resume:
            if not ed:
                await cx.close()
                return None
            await cx.add_init_script("try{localStorage.setItem('kme:last'," + json.dumps(json.dumps(
                {"u": "index.html", "s": 1, "t": "x", "ed": _html.unescape(ed.group(1))})) + ")}catch(e){}")
        try:
            pg = await cx.new_page()
            await pg.goto(base + p.split("~")[0] + ".html", wait_until="load")
            await pg.evaluate("document.fonts ? document.fonts.ready.then(() => 0) : 0")
            await pg.wait_for_timeout(200)
            v = {"bg": None, "snap": None}
            if not resume:
                v["bg"] = await pg.evaluate(BG_JS)
                v["snap"] = await pg.evaluate(STATE_JS)
            v["orn"] = []
            if not resume:
                n = await pg.evaluate("window.KROOM ? window.KROOM.sheets : 1")
                for i in range(n):
                    if i:
                        await pg.evaluate(f"window.KPAGER && window.KPAGER.show({i})")
                        await pg.wait_for_timeout(100)
                    v["orn"] += await pg.evaluate(ORN_JS)
                if n > 1:
                    await pg.evaluate("window.KPAGER && window.KPAGER.show(0)")
                    await pg.wait_for_timeout(100)
            got = await pg.evaluate(MATCH_JS, sels)
            v["used"] = got
            return v
        finally:
            await cx.close()
    return await _pool(_pages(out) + ["index~resume"], one)


def _write_pre(out, visits):
    done = 0
    for p in _pages(out):
        v = visits.get(p)
        if not v or not v.get("snap"):
            continue
        fp = os.path.join(out, p + ".html")
        s = open(fp, encoding="utf-8").read()
        # a picture still on the web may be a different size on the Kindle than here: measure there
        if re.search(r'<main id="kmain">.*<img\b[^>]*\ssrc="(https?:)?//', s, re.S):
            continue
        # as raw JSON in a data block, not an escaped attribute: about a third smaller, and no entity decoding
        data = json.dumps(v["snap"], separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

        def put(t, data=data):
            t = re.sub(r'<script type="application/json" id="kpre">.*?</script>', "", t, flags=re.S)
            m = re.search(r"<body\b[^>]*>", t)
            return t[:m.end()] + f'<script type="application/json" id="kpre">{data}</script>' + t[m.end():]
        _rewrite(fp, put)
        done += 1
    return done


def _intrinsic(svg):
    m = re.search(r"<svg\b[^>]*>", svg)
    if not m:
        return None
    t = m.group(0)
    w, h = re.search(r'\swidth="([\d.]+)(px)?"', t), re.search(r'\sheight="([\d.]+)(px)?"', t)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    vb = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', t)
    return (float(vb.group(1)), float(vb.group(2))) if vb else None


def _svg_text(out, base, u):
    import urllib.parse
    if u.startswith("data:"):
        head, _, body = u.partition(",")
        return urllib.parse.unquote(body) if "base64" not in head else None
    if u.startswith(base):
        fp = os.path.join(out, urllib.parse.unquote(u[len(base):]))
        return open(fp, encoding="utf-8").read() if os.path.exists(fp) else None
    return None


def _drawn(r, svg):
    """(w, h) in CSS px a layer is drawn at, or None when that is not one fixed size."""
    if not r["n"] or r["o"] != "padding-box":
        return None
    parts = r["sz"].split()
    if len(parts) == 1:
        parts.append("auto")
    if len(parts) != 2:
        return None
    vals = []
    for k, x in enumerate(parts):
        if x.endswith("px"):
            vals.append(float(x[:-2]))
        elif x.endswith("%"):
            vals.append(float(x[:-1]) / 100 * (r["W"] if k == 0 else r["H"]))
        elif x == "auto":
            vals.append(None)
        else:
            return None
    if None in vals:
        iw = _intrinsic(svg or "")
        if not iw:
            return None
        if vals[0] is None and vals[1] is None:
            vals = list(iw)
        elif vals[0] is None:
            vals[0] = vals[1] * iw[0] / iw[1]
        else:
            vals[1] = vals[0] * iw[1] / iw[0]
    return vals[0], vals[1]


async def _ornaments(br, out, base, css, visits):
    """Every SVG the stylesheet draws (frame, cartouche, corner pieces, rules) that is drawn at one fixed size on
    every page and sheet becomes a 16-grey PNG at exactly that size x DPR. One drawn at several sizes, or whose
    PNG would be much heavier than the SVG (the one-path hatched paper ground), stays an SVG."""
    import hashlib
    import urllib.parse
    sizes, bad = {}, set()
    for v in visits.values():
        for r in (v or {}).get("orn") or []:
            u = r["u"].replace('\\"', '"').replace("\\\\", "\\")
            svg = _svg_text(out, base, u)
            d = _drawn(r, svg) if svg else None
            if not d:
                bad.add(u)
                continue
            dw, dh = d[0] * DPR, d[1] * DPR
            if abs(dw - round(dw)) > .02 or abs(dh - round(dh)) > .02 or dw < 2 or dh < 2:
                bad.add(u)
                continue
            sizes.setdefault(u, set()).add((round(dw), round(dh)))
    todo = {u: next(iter(sz)) for u, sz in sizes.items() if u not in bad and len(sz) == 1}
    names = {}
    for u in todo:
        if u.startswith("data:"):
            names[u] = "orn/d-" + hashlib.sha1(u.encode()).hexdigest()[:12] + ".png"
        else:
            names[u] = urllib.parse.unquote(u[len(base):])[:-4] + ".png"
    cx = await br.new_context(device_scale_factor=DPR)
    free = [await cx.new_page() for _ in range(WORKERS)]

    async def one(u):
        dw, dh = todo[u]
        w, h = dw / DPR, dh / DPR
        pg = free.pop()
        try:
            dst = os.path.join(out, names[u])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            await _shot(pg, f'<!doctype html><html style="background:transparent"><body style="margin:0;background:transparent">'
                            f'<div style="width:{w}px;height:{h}px;background-image:url(&quot;{_html.escape(u)}&quot;);background-repeat:no-repeat;background-size:100% 100%"></div></body></html>',
                        max(1, int(-(-w // 1))), max(1, int(-(-h // 1))), False, dst)
            svg_b = len((_svg_text(out, base, u) or "").encode())
            if os.path.getsize(dst) > 3 * svg_b + 4000:
                os.remove(dst)
                return None
            return names[u]
        finally:
            free.append(pg)
    got = await _pool(list(todo), one)
    await cx.close()
    swap = {u: n for u, n in got.items() if n}
    # the pager warms the next section's cartouche: tell it which kind to fetch
    if any("/motif-" in u for u in swap):
        for p in _pages(out):
            _rewrite(os.path.join(out, p + ".html"), lambda s: _set_attr(s, "body", "data-kbg", "png"))
    return swap, {"png": len(swap), "kept_svg": len(sizes) - len(swap) + len(bad)}


def _swap_urls(css, base, swap):
    import urllib.parse

    def fix(m):
        raw = m.group(2) if m.group(2) is not None else m.group(3) if m.group(3) is not None else m.group(4).strip()
        u = raw if raw.startswith("data:") else urllib.parse.urljoin(base + "kindle.css", raw)
        return f"url({swap[u]})" if u in swap else m.group(0)
    return re.sub(r"""url\(\s*(?:("([^"]*)")|'([^']*)'|([^)"']*))\s*\)""", fix, css)


# ---------------------------------------------------------------- 4. fonts

EXTRA_CHARS = ("\u2018\u2019\u201c\u201d\u2013\u2014\u2026\u2022\u00b7\u2039\u203a\u00ab\u00bb\u2190\u2192\u2191\u2193"
               "\u25be\u00b0\u00d7\u00bd\u00bc\u00be\u2032\u2033\u00a0\u00e9\u00e8\u00e0\u00f1\u00fc\u00f6\u00e7")


def subset_fonts(out):
    """Each web font cut to the characters this edition prints (all of printable ASCII and common punctuation
    always), every OpenType feature and both variation axes kept; saved under a name that changes with the
    cut, so a cached cut from an earlier edition is never used for new text."""
    import hashlib
    from fontTools import subset
    text = set(chr(c) for c in range(0x20, 0x7f)) | set(EXTRA_CHARS)
    for fp in glob.glob(os.path.join(out, "*.html")) + glob.glob(os.path.join(out, "*.css")) + glob.glob(os.path.join(out, "*.js")):
        text |= set(_html.unescape(open(fp, encoding="utf-8").read()))
    for fp in glob.glob(os.path.join(out, "*.css")):   # content:'\2192' and the like
        for m in re.findall(r"\\([0-9a-fA-F]{2,6})", open(fp, encoding="utf-8").read()):
            text.add(chr(int(m, 16)))
    css_path = os.path.join(out, "kindle.css")
    css = open(css_path, encoding="utf-8").read()
    fonts = sorted(set(re.findall(r"url\((fonts/[\w.-]+\.woff2)\)", css)))
    renamed, before, after = {}, 0, 0
    for rel in fonts:
        src = os.path.join(out, rel)
        if not os.path.exists(src):
            continue
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.flavor = "woff2"
        opts.notdef_outline = True
        opts.name_IDs = ["*"]
        f = subset.load_font(src, opts)
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(text)))
        sub.subset(f)
        import io
        buf = io.BytesIO()
        subset.save_font(f, buf, opts)
        data = buf.getvalue()
        name = re.sub(r"(-[0-9a-f]{8})?\.woff2$", "", rel) + "-" + hashlib.sha1(data).hexdigest()[:8] + ".woff2"
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(data)
        before += os.path.getsize(src)
        after += len(data)
        renamed[rel] = name
    if not renamed:
        return None
    for fp in glob.glob(os.path.join(out, "*.html")) + [css_path]:
        _rewrite(fp, lambda s: re.sub(r"fonts/[\w.-]+\.woff2", lambda m: renamed.get(m.group(0), m.group(0)), s))
    for rel, name in renamed.items():
        if rel != name:
            os.remove(os.path.join(out, rel))
    return f"{len(text)} chars, {before} -> {after} bytes"


if __name__ == "__main__":
    run(sys.argv[1])


# ---------------------------------------------------------------- 5. hand-lettered headlines

# Which elements are headlines: page and section titles, the titles inside a page, and story headlines (the news
# pages, good news, science, the front page's leads). Lists of events, shows and records keep their type.
LETTER_SEL = ("#kmain h2, #kmain h3.kfold, #kmain .sci-title, #kmain .poem-title, #kmain .story.headline b,"
              " body[data-ksec=news] #kmain .story b, #kmain #good .story b, #kmain .kleads b")
# Tags that may hold one (each is tagged for the measuring pass, then untagged unless it is one).
_LET_TAG = re.compile(r'<(h2|h3|b)\b([^>]*)>')

LETTER_CSS = """
/* Hand-lettered headlines (solar/lettering.py): the drawing is the headline; the words stay in the page as plain
   text, unseen, for the pager, search and a screen reader, and come back in type if the drawing does not load.
   (No descendant rules here: a trailing * would cost every element on every page a style check.) */
#kmain .klet{position:relative !important;overflow:visible !important}
#kmain b.klet{display:block !important}
#kmain .klet>.kltx{position:absolute !important;left:0;top:0;width:100%;height:100%;overflow:hidden;margin:0 !important;padding:0 !important}
#kmain .klet>.kltx{color:transparent !important;-webkit-text-fill-color:transparent !important}
#kmain .klet>img.kli{display:block !important;float:none !important;position:static !important;margin:0 !important;padding:0 !important;
  border:0 !important;max-width:none !important;max-height:none !important;min-width:0 !important;min-height:0 !important;
  background:none !important;box-shadow:none !important;filter:none !important;vertical-align:top !important}
#kmain .klet.kletx>.kltx{position:static !important;overflow:visible}
#kmain .klet.kletx>.kltx{color:#000 !important;-webkit-text-fill-color:#000 !important}
#kmain .klet.kletx>.kli{display:none !important}
"""

LETTER_JS = r"""(sel) => {
  const out = {};
  const want = new Set(Array.from(document.querySelectorAll(sel)));
  for (const el of document.querySelectorAll('[data-kl]')) {
    if (!want.has(el)) continue;
    const t = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t) continue;
    const cs = getComputedStyle(el), d0 = el.style.display;
    el.style.display = 'block';
    const w = el.getBoundingClientRect().width - (parseFloat(cs.paddingLeft) || 0) - (parseFloat(cs.paddingRight) || 0);
    el.style.display = d0;
    let kind = 'title';
    if (el.matches('.kfname')) kind = 'section';
    else if (el.matches('.ktochead')) kind = 'contents';
    else if (el.matches('h3.kfold')) kind = 'sub';
    else if (el.matches('.sci-title')) kind = 'science';
    else if (el.matches('.poem-title')) kind = 'poem';
    else if (el.matches('b')) kind = el.closest('.kleads') ? (el.parentNode === el.closest('.kleads').firstElementChild ? 'lead' : 'leads') : 'story';
    out[el.getAttribute('data-kl')] = { t: t, w: Math.floor(w), fs: parseFloat(cs.fontSize), center: cs.textAlign === 'center', kind: kind };
  }
  return out;
}"""

# kind: (size the lettering is drawn at, flourish under it)
LETTER_KINDS = {"section": (44, True), "contents": (38, True), "title": (31, True), "poem": (30, True),
                "sub": (26, False), "science": (27, False), "lead": (29, False), "leads": (21, False), "story": (21, False)}


def letter(out, exe=None):
    """Hand-letter every headline of the Morning pages in <out>. Run after the pages are written and before the
    plates are cut (the lettering changes the page heights the plates are fitted to). Never fatal: a page, or a
    headline, that cannot be lettered keeps its type."""
    t0 = time.time()
    try:
        from . import lettering
        import asyncio
        from playwright.async_api import async_playwright  # noqa: F401  -- only to know it is there
    except Exception as e:  # noqa: BLE001
        print(f"LETTERING FALLBACK: every headline left in Literata ({e!r})", file=sys.stderr)
        return
    tagged = {}
    for p in _pages(out):   # tag every candidate, so the browser's answer can be found again in the source
        fp = os.path.join(out, p + ".html")
        s = open(fp, encoding="utf-8").read()
        m = re.search(r'<main id="kmain">', s)
        if not m:
            continue
        n = [0]

        def tag(mm, n=n):
            n[0] += 1
            return f'<{mm.group(1)}{mm.group(2)} data-kl="{n[0]}">'
        tagged[p] = (s, s[:m.end()] + _LET_TAG.sub(tag, s[m.end():]))
        with open(fp, "w", encoding="utf-8") as f:
            f.write(tagged[p][1])
    css_path = os.path.join(out, "kindle.css")
    css0 = open(css_path, encoding="utf-8").read()
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css0 + LETTER_CSS)
    srv, base = _serve(out)
    try:
        found = asyncio.run(_letter_measure(base, list(tagged), exe))
    except Exception as e:  # noqa: BLE001
        found = {}
        print(f"LETTERING FALLBACK: every headline left in Literata, the measuring pass failed ({e!r})", file=sys.stderr)
    finally:
        srv.shutdown()
    od = os.path.join(out, "orn")
    os.makedirs(od, exist_ok=True)
    done, kept, made = 0, 0, set()
    untag = re.compile(r' data-kl="\d+"')
    for p, (orig, s) in tagged.items():
        heads = found.get(p) or {}
        res, pos = [], 0
        for m in re.finditer(r'<(h2|h3|b)\b([^>]*) data-kl="(\d+)">', s):
            if m.start() < pos:
                continue
            res.append(untag.sub("", s[pos:m.start()]))
            pos = m.end()
            h = heads.get(m.group(3))
            close = s.find(f"</{m.group(1)}>", m.end()) if h and h["w"] >= 150 else -1
            if h and 0 < h["w"] < 150:   # (0: not shown on this page at all)
                kept += 1
                print(f"LETTERING FALLBACK: {p}: {h['t']!r} left in Literata (only {h['w']}px wide)", file=sys.stderr)
            if close < 0:
                res.append(f"<{m.group(1)}{m.group(2)}>")
                continue
            size, fl = LETTER_KINDS.get(h["kind"], (30, False))
            try:
                svg = lettering.headline(h["t"], h["w"], size, align="center" if h["center"] else "left",
                                         flourish=None if fl else False)
            except Exception as e:  # noqa: BLE001  -- a character the hand has no letter for: keep the type
                kept += 1
                print(f"LETTERING FALLBACK: {p}: {h['t']!r} left in Literata ({e})", file=sys.stderr)
                res.append(f"<{m.group(1)}{m.group(2)}>")
                continue
            import hashlib
            name = "let-" + hashlib.sha1(svg.encode()).hexdigest()[:12] + ".svg"
            if name not in made:
                with open(os.path.join(od, name), "w", encoding="utf-8") as f:
                    f.write(svg)
                made.add(name)
            w, hh = (int(v) for v in _intrinsic(svg))
            attrs = m.group(2)
            if re.search(r'\sclass="', attrs):
                attrs = re.sub(r'\sclass="([^"]*)"', lambda c: f' class="{c.group(1)} klet"', attrs, count=1)
            else:
                attrs += ' class="klet"'
            res.append(f'<{m.group(1)}{attrs}><span class="kltx">{_html.escape(h["t"], quote=False)}</span>'
                       f'<img class="kli" src="orn/{name}" width="{w}" height="{hh}" style="width:{w}px !important;height:{hh}px !important" alt=""'
                       f' onerror="this.parentNode.className+=\' kletx\'"></{m.group(1)}>')
            pos = close + len(m.group(1)) + 3
            done += 1
        res.append(untag.sub("", s[pos:]))
        new = "".join(res)
        with open(os.path.join(out, p + ".html"), "w", encoding="utf-8") as f:
            f.write(new if heads or new != s else orig)
    print(f"kindle_fast: lettered {done} headlines ({len(made)} drawings, {kept} kept in type) in {time.time() - t0:.1f}s")


async def _letter_measure(base, pages, exe):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch(executable_path=exe or os.environ.get("KINDLE_CHROMIUM") or None)

        async def one(p):
            cx = await br.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=DPR, has_touch=True)
            try:
                pg = await cx.new_page()
                await pg.goto(base + p + ".html", wait_until="load")
                await pg.evaluate("document.fonts ? document.fonts.ready.then(() => 0) : 0")
                return await pg.evaluate(LETTER_JS, LETTER_SEL)
            finally:
                await cx.close()
        got = await _pool(list(pages), one)
        await br.close()
    return got


async def _letters(br, out, base):
    """A page's lettered headlines as one 16-grey PNG at exactly their shown sizes x2, stacked: one request and one
    decode per page however many headlines it has (seven separate pictures made a news page turn measurably
    slower). Each <img> shows its own band of the sheet (srcset 2x, object-fit:none, object-position), on white:
    headlines sit on white. A page whose sheet cannot be made keeps its SVGs."""
    import io
    from PIL import Image
    IMG = re.compile(r'<img class="kli" src="orn/(let-[0-9a-f]+)\.svg" width="(\d+)" height="(\d+)" style="[^"]*"')
    per_page, jobs = {}, {}
    for p in _pages(out):
        got = IMG.findall(open(os.path.join(out, p + ".html"), encoding="utf-8").read())
        if got:
            per_page[p] = [(n, int(w), int(h)) for n, w, h in got]
            for n, w, h in per_page[p]:
                jobs[n] = (w, h)
    if not jobs:
        return 0
    cx = await br.new_context(device_scale_factor=DPR)
    free = [await cx.new_page() for _ in range(WORKERS)]

    async def one(name):
        w, h = jobs[name]
        pg = free.pop()
        try:
            await pg.set_viewport_size({"width": max(w, 16), "height": max(h, 16)})
            await pg.set_content(f'<!doctype html><html style="background:#fff"><body style="margin:0;background:#fff">'
                                 f'<img src="{base}orn/{name}.svg" width="{w}" height="{h}" style="display:block"></body></html>',
                                 wait_until="load")
            await pg.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
            im = Image.open(io.BytesIO(await pg.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}))).convert("L")
            return im if im.size == (w * DPR, h * DPR) else None
        finally:
            free.append(pg)
    shots = await _pool(list(jobs), one)
    await cx.close()
    pal = []
    for k in range(LEVELS):
        c = round(k * 255 / (LEVELS - 1))
        pal += [c, c, c]
    done = 0
    for p, items in per_page.items():
        if not all(shots.get(n) for n, _, _ in items):
            continue
        W = max(w for _, w, _ in items) * DPR
        sheet = Image.new("L", (W, sum(h for _, _, h in items) * DPR), 255)
        offs, y = [], 0
        for n, w, h in items:
            sheet.paste(shots[n], (0, y))
            offs.append(y // DPR)
            y += h * DPR
        g = sheet.point(lambda v: (v * (LEVELS - 1) + 127) // 255)
        q = Image.frombytes("P", g.size, g.tobytes())
        q.putpalette(pal)
        name = f"orn/lets-{p}.png"
        q.save(os.path.join(out, name), "PNG", optimize=True, bits=4)
        k = iter(offs)

        def swap(m):
            return (f'<img class="kli" src="{name}" srcset="{name} 2x" width="{m.group(2)}" height="{m.group(3)}"'
                    f' style="width:{m.group(2)}px !important;height:{m.group(3)}px !important;object-fit:none;'
                    f'object-position:0 -{next(k)}px"')
        _rewrite(os.path.join(out, p + ".html"), lambda s: IMG.sub(swap, s))
        done += len(items)
    return done
