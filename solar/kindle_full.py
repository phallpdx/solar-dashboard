"""Snapshot the full dashboard into static, paged pages for the Kindle browser.

The live dashboard builds every card with ~275 KB of JavaScript, which the
Kindle's browser runs slowly or not at all. This renders it once in headless
Chromium (Pacific time, phone-sized screen), then saves what it drew:

    kindle/index.html      contents, with a link to every section
    kindle/<section>.html  one file per dashboard section, images and links kept
    kindle/kindle.css      the dashboard's own styles plus an e-ink override

Each page has Prev / Contents / Next links, and tapping the right or left
side of the screen turns one screen forward or back.

    python -m solar.kindle_full _site
"""

import functools
import html
import http.server
import os
import sys
import threading

from playwright.sync_api import sync_playwright

TZ = "America/Los_Angeles"
WIDTH, HEIGHT = 600, 800  # roughly the Paperwhite browser's CSS viewport

# Runs after the e-ink styles are applied: fix any text that is now too faint
# (light text that sat on a coloured card now sits on white) and undo fades.
CONTRAST = r"""
() => {
  const rgb = c => { const m = c.match(/[\d.]+/g); return m ? m.map(Number) : [0, 0, 0, 0]; };
  const lum = ([r, g, b]) => {
    const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b);
  };
  const bgOf = el => {
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const c = rgb(getComputedStyle(e).backgroundColor);
      if ((c.length < 4 || c[3] > .5) && !(c[0] === 0 && c[1] === 0 && c[2] === 0 && c[3] === 0)) return c;
    }
    return [255, 255, 255];
  };
  for (const el of document.body.querySelectorAll('*')) {
    const s = getComputedStyle(el);
    if (parseFloat(s.opacity) < 1) el.style.setProperty('opacity', '1', 'important');
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasText) continue;
    const fg = lum(rgb(s.color)), bg = lum(bgOf(el));
    const ratio = (Math.max(fg, bg) + .05) / (Math.min(fg, bg) + .05);
    if (ratio < 7) el.style.setProperty('color', bg > .15 ? '#000' : '#fff', 'important');
    el.style.setProperty('-webkit-text-fill-color', 'currentcolor', 'important');
  }
}
"""

# Runs in the rendered page: strip it down to static HTML and split it up.
EXTRACT = r"""
() => {
  const abs = u => { try { return new URL(u, location.href).href } catch (e) { return u } };
  // Canvases become images so charts survive without scripts.
  for (const c of document.querySelectorAll('canvas')) {
    try {
      const img = document.createElement('img');
      img.src = c.toDataURL('image/png');
      img.width = c.clientWidth; img.height = c.clientHeight;
      img.className = c.className;
      c.replaceWith(img);
    } catch (e) { c.remove(); }
  }
  // Drop what is not shown, and things that only work with scripts.
  const gone = el => {
    const s = getComputedStyle(el);
    return el.hidden || s.display === 'none' || s.visibility === 'hidden';
  };
  for (const el of [...document.body.querySelectorAll('*')]) {
    if (el.isConnected && gone(el)) el.remove();
  }
  document.querySelectorAll('script,noscript,iframe,video,audio,button,input,select,textarea,.secnav,.leaflet-container,.rune,.durin')
    .forEach(el => el.remove());
  for (const img of document.querySelectorAll('img')) {
    if (img.currentSrc && !img.src.startsWith('data:')) img.src = img.currentSrc;
    img.removeAttribute('srcset'); img.setAttribute('loading', 'lazy');
  }
  for (const a of document.querySelectorAll('a[href]')) {
    const h = a.getAttribute('href');
    if (h.startsWith('#') || h.startsWith('javascript:')) { a.removeAttribute('href'); continue; }
    a.href = abs(h); a.removeAttribute('target');
  }
  for (const el of document.querySelectorAll('[style*="url("]')) {
    if (/background/.test(el.getAttribute('style') || '')) el.style.backgroundImage = 'none';
  }
  for (const el of document.querySelectorAll('*')) {
    for (const at of [...el.attributes]) if (at.name.startsWith('on')) el.removeAttribute(at.name);
  }
  const css = [...document.querySelectorAll('style')].map(s => s.textContent).join('\n');
  const links = [...document.querySelectorAll('link[rel=stylesheet]')].map(l => l.href);
  const groups = [...document.querySelectorAll('section.group')];
  const sections = groups.map(g => {
    const h = g.querySelector('.sec-h, h2');
    return { id: g.dataset.sec || g.id, title: (h ? h.textContent : g.id).trim(), html: g.outerHTML };
  });
  // Everything above the first section (greeting, brief) opens the first page.
  let intro = '';
  if (groups.length) {
    const top = groups[0];
    const range = document.createRange();
    range.setStart(document.querySelector('main') || document.body, 0);
    range.setEndBefore(top);
    const box = document.createElement('div');
    box.appendChild(range.cloneContents());
    intro = box.innerHTML;
  }
  const bodyClass = document.body.className, htmlClass = document.documentElement.className;
  return { css, links, sections, intro, bodyClass, htmlClass };
}
"""

EINK_CSS = """
/* ---- Kindle / e-ink override ---- */
html,body{background:#fff !important;background-image:none !important}
body{color:#000;margin:0;padding:0 12px 60px !important;max-width:none !important}
*,*::before,*::after{animation:none !important;transition:none !important;box-shadow:none !important;text-shadow:none !important;
  backdrop-filter:none !important;-webkit-backdrop-filter:none !important}
.card,.tile,.joy-card,.sec-head,.brief,header{background:#fff !important;background-image:none !important;border-color:#000 !important}
.card,.tile{border:2px solid #000 !important;border-radius:10px !important}
.magic .card.ink,.card,.dd .wash,.dd text{opacity:1 !important;transform:none !important}
img{max-width:100% !important;height:auto;filter:grayscale(1) contrast(1.1)}
a{color:#000 !important;text-decoration:underline}
header{min-height:0 !important;height:auto !important;padding:16px !important}
.sec-head,.sec-head *{color:#000 !important}
.group{margin-top:0 !important;padding-top:0 !important}
.kpager{display:flex;justify-content:space-between;align-items:center;gap:8px;font:600 18px/1.2 Georgia,serif;
  border-bottom:3px solid #000;padding:10px 0;margin:0 0 12px;background:#fff}
.kpager.bottom{border-bottom:0;border-top:3px solid #000;margin:24px 0 0}
.kpager a{padding:8px 4px;text-decoration:none}
.kpager .off{color:#999}
.kstamp{font:14px Georgia,serif;color:#333;margin:6px 0 0}
.ktoc{font:22px/1.3 Georgia,serif;list-style:none;padding:0;margin:12px 0}
.ktoc li{border-bottom:1px solid #000}
.ktoc a{display:block;padding:14px 4px;text-decoration:none}
.khint{font:15px Georgia,serif;color:#333}
"""

# Tap the right two thirds of the screen to go forward a screen, the left
# third to go back. Taps on links still follow the link. Old-browser safe.
PAGER_JS = """
<script>
(function(){
  function turn(dir){
    var step = Math.round(window.innerHeight * 0.92);
    var y = (window.pageYOffset || document.documentElement.scrollTop) + dir * step;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (dir > 0 && y > max + step * 0.5 && NEXT) { location.href = NEXT; return; }
    if (dir < 0 && (window.pageYOffset || 0) <= 2 && PREV) { location.href = PREV; return; }
    window.scrollTo(0, Math.max(0, y));
  }
  document.addEventListener('click', function(e){
    var t = e.target;
    while (t && t !== document.body) { if (t.tagName === 'A' && t.href) return; t = t.parentNode; }
    turn(e.clientX < window.innerWidth / 3 ? -1 : 1);
  }, false);
  document.addEventListener('keydown', function(e){
    if (e.keyCode === 34 || e.keyCode === 39 || e.keyCode === 32) { e.preventDefault(); turn(1); }
    if (e.keyCode === 33 || e.keyCode === 37) { e.preventDefault(); turn(-1); }
  }, false);
})();
</script>
"""


def page(title, body, links, html_class, body_class, prev=None, nxt=None, stamp=""):
    esc = html.escape
    head_links = "".join(f'<link rel="stylesheet" href="{esc(h)}">' for h in links)

    def pager(cls):
        p = f'<a href="{prev}">&larr; {esc(prev_title(prev))}</a>' if prev else '<span class="off">&larr;</span>'
        n = f'<a href="{nxt}">{esc(prev_title(nxt))} &rarr;</a>' if nxt else '<span class="off">&rarr;</span>'
        return f'<nav class="kpager {cls}">{p}<a href="index.html">Contents</a>{n}</nav>'

    js = PAGER_JS.replace("NEXT", repr(nxt or "")).replace("PREV", repr(prev or ""))
    return f"""<!doctype html>
<html lang="en" class="{esc(html_class)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>{head_links}<link rel="stylesheet" href="kindle.css"></head>
<body class="{esc(body_class)}">
{pager("top")}{stamp}
<main>{body}</main>
{pager("bottom")}
{js}
</body></html>
"""


_TITLES = {}


def prev_title(href):
    return _TITLES.get(href, "")


def serve(root):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def snapshot(site):
    srv = serve(site)
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    exe = os.environ.get("KINDLE_CHROMIUM") or None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=exe)
        ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, timezone_id=TZ,
                                  locale="en-US", reduced_motion="reduce")
        p = ctx.new_page()
        p.on("pageerror", lambda e: print(f"kindle_full: page error: {e}", file=sys.stderr))
        p.goto(url, wait_until="networkidle", timeout=90_000)
        # Scroll the whole page so cards that load on view get filled in.
        height = p.evaluate("document.body.scrollHeight")
        y = 0
        while y < height:
            y += HEIGHT
            p.evaluate(f"window.scrollTo(0, {y})")
            p.wait_for_timeout(150)
            height = p.evaluate("document.body.scrollHeight")
        try:
            p.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        p.wait_for_timeout(1500)
        stamp = p.evaluate("new Date().toLocaleString('en-US',{weekday:'short',hour:'numeric',minute:'2-digit'})")
        p.add_style_tag(content=EINK_CSS)
        p.wait_for_timeout(300)
        p.evaluate(CONTRAST)
        data = p.evaluate(EXTRACT)
        browser.close()
    srv.shutdown()
    return data, stamp


def main(site):
    data, stamp = snapshot(site)
    out = os.path.join(site, "kindle")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "kindle.css"), "w") as f:
        f.write(data["css"] + "\n" + EINK_CSS)
    secs = [s for s in data["sections"] if s["html"].strip()]
    files = [f"{s['id']}.html" for s in secs]
    _TITLES.update({f: s["title"] for f, s in zip(files, secs)})
    stamp_html = f'<p class="kstamp">Updated {html.escape(stamp)}</p>'
    for i, (s, fname) in enumerate(zip(secs, files)):
        body = (data["intro"] if i == 0 else "") + s["html"]
        doc = page(s["title"], body, data["links"], data["htmlClass"], data["bodyClass"],
                   prev=files[i - 1] if i else None, nxt=files[i + 1] if i + 1 < len(files) else None,
                   stamp=stamp_html)
        with open(os.path.join(out, fname), "w") as f:
            f.write(doc)
    toc = "".join(f'<li><a href="{f}">{html.escape(s["title"])}</a></li>' for f, s in zip(files, secs))
    body = (f'<h1 style="font:700 34px Georgia,serif;margin:8px 0">Dashboard</h1>'
            f'<p class="khint">Tap the right side of the screen to turn the page, the left side to go back.</p>'
            f'<ol class="ktoc">{toc}</ol>')
    _TITLES["index.html"] = "Contents"
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(page("Dashboard", body, [], "", "", nxt=files[0] if files else None, stamp=stamp_html))
    # The old bookmark (kindle.html) now opens the paged dashboard.
    with open(os.path.join(site, "kindle.html"), "w") as f:
        f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=kindle/index.html">'
                '<a href="kindle/index.html">Open the dashboard</a>')
    print(f"kindle_full: wrote {len(files)} sections to {out}")


if __name__ == "__main__":
    main(sys.argv[1])
