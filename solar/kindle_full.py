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

# Turn every remaining colour into one of a few greys that e-ink shows cleanly:
# pale fills become paper, mid tones a light or mid grey, dark ones black.
GRAYSCALE = r"""
() => {
  const rgb = c => { const m = (c || '').match(/[\d.]+/g); return m ? m.map(Number) : null; };
  const L = c => (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255;
  const fill = l => l > .86 ? null : l > .6 ? '#e4e4e4' : l > .35 ? '#9a9a9a' : '#000';
  const line = l => l > .8 ? '#bbb' : l > .45 ? '#777' : '#000';
  for (const el of document.body.querySelectorAll('*')) {
    const s = getComputedStyle(el);
    const bg = rgb(s.backgroundColor);
    if (bg && (bg.length < 4 || bg[3] > 0.05)) {
      // Never reverse text out of a dark block: it ghosts on e-ink. Only
      // text-free marks (bars, swatches, chart segments) keep a fill.
      const texty = !(el instanceof SVGElement) && el.textContent.trim().length > 0;
      el.style.setProperty('background-color', texty ? 'transparent' : (fill(L(bg)) || 'transparent'), 'important');
    }
    if (el.tagName === 'text' || el.tagName === 'tspan') {
      el.style.setProperty('fill', L(rgb(s.fill) || [0, 0, 0]) < .7 ? '#000' : '#444', 'important');
      continue;
    }
    if (!(el instanceof SVGElement)) {
      const c = rgb(s.color);
      if (c) el.style.setProperty('color', L(c) < .5 ? '#000' : '#555', 'important');
    }
    if (el instanceof SVGElement) {
      for (const prop of ['fill', 'stroke']) {
        const c = rgb(s[prop]);
        if (c && s[prop] !== 'none' && (c.length < 4 || c[3] > 0)) {
          const l = L(c);
          el.style.setProperty(prop, prop === 'fill' ? (fill(l) || '#fff') : line(l), 'important');
        }
      }
    } else {
      for (const side of ['Top', 'Right', 'Bottom', 'Left']) {
        if (parseFloat(s['border' + side + 'Width']) > 0) {
          const c = rgb(s['border' + side + 'Color']);
          if (c) el.style.setProperty('border-' + side.toLowerCase() + '-color', line(L(c)), 'important');
        }
      }
    }
  }
}
"""

# Editorial pass on the live page before it is flattened: drop leftovers that
# only make sense on the interactive dashboard, make Today read like a front
# page, split Sports from Money, rename sections, tidy dates and sources.
CURATE = r"""
() => {
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const kill = el => el && el.remove();
  const cardOf = sel => { const h = $(sel); return h ? (h.closest('.card') || h.closest('section')) : null; };
  const txt = el => (el ? el.textContent : '').replace(/\s+/g, ' ').trim();

  // 1-2. Interactive leftovers, status text, broken or empty widgets.
  $$('.refresh, form, label, .kid-setup, #books-meta, .sci-ph, .brief-icon').forEach(kill);
  kill(cardOf('#radar-h'));
  for (const a of $$('a')) if (/^(Run a full update|Full map|More deals)$/i.test(txt(a))) kill(a);
  const perf = $('#t-perf');
  if (perf && /^[–-]?$/.test(txt(perf))) kill(perf.closest('.tile'));
  const forest = $('#forest-meta');
  if (forest) forest.textContent = forest.textContent.replace(/\s*·\s*tick them off as you go/i, '');
  const junk = /^(Web search:|Sources: Daily web check|Sources: Play ideas|Goodreads no longer)/i;
  for (const el of $$('p, small, div, span, li')) {
    if (el.isConnected && !el.querySelector('p,div,li') && junk.test(txt(el))) kill(el);
  }
  for (const el of $$('.lines>div')) if (/Test Election/i.test(txt(el))) kill(el);
  const main = cardOf('#main-h');
  if (main && /No production yet/i.test(txt(main))) kill(main);
  // Reddit thread titles under the fan-mood lines read as noise in print.
  for (const h of $$('h3.sub')) {
    if (/^r\//i.test(txt(h)) || /^Talked about on r\//i.test(txt(h))) {
      const nx = h.nextElementSibling;
      if (nx && nx.classList.contains('lines')) kill(nx);
    }
  }
  // Doodles that only repeat another section.
  ['#harvest-card', '#ahead-card', '#therm-card', '#stake-card'].forEach(s => kill($(s)));

  // 3. Today as a front page: weather, then calendar, then Alfred, then the rest.
  const today = $('section.group[data-sec=today]'), tbody = today && today.querySelector('.sec-body');
  const brief = $('#brief');
  if (tbody) {
    const order = ['#today-card', '#fc-card', '#cal-card', '#brief', '#yard-card', '#shade-card', '#plan-card']
      .map(s => $(s)).filter(Boolean);
    let anchor = null;
    for (const el of order) {
      const host = el.closest('.row, .split, .pair') && el.closest('.row, .split, .pair') !== tbody ? el : el;
      if (anchor) anchor.after(host); else tbody.prepend(host);
      anchor = host;
    }
    const ts = today.querySelector('.sec-sub');
    today.dataset.ktitle = 'Today'; today.dataset.ksub = ts ? txt(ts) : '';
    kill(today.querySelector('.sec-head'));
  }
  if (brief) {
    // Alfred: the numbered list leads; each other list keeps three, the rest fold to the end.
    const extra = [];
    const seen = new Set();
    for (const li of brief.querySelectorAll('li')) {
      const key = txt(li.querySelector('b')).toLowerCase();
      if (key && seen.has(key)) { kill(li); continue; }
      if (key) seen.add(key);
    }
    for (const ul of brief.querySelectorAll(':scope > ul.brief-rest')) {
      [...ul.children].slice(3).forEach(li => extra.push(li));
    }
    let more = brief.querySelector('.brief-more');
    if (more || extra.length) {
      if (!more) { more = document.createElement('details'); more.className = 'brief-more'; more.innerHTML = '<summary></summary>'; }
      more.open = true;
      const sum = more.querySelector('summary'); if (sum) sum.textContent = 'Also from Alfred';
      if (extra.length) { const ul = document.createElement('ul'); ul.className = 'brief-rest'; extra.forEach(li => ul.appendChild(li)); sum ? sum.after(ul) : more.prepend(ul); }
      if (tbody) tbody.appendChild(more);
    }
    const h2 = brief.querySelector('h2');
    if (h2) { const k = document.createElement('p'); k.className = 'kkicker'; k.textContent = 'From Alfred'; h2.before(k); }
  }
  // Calendar video-call addresses read as a word, not a raw URL.
  for (const el of $$('#cal-card *')) {
    if (!el.children.length && /^https?:\/\/\S+$/.test(el.textContent.trim())) {
      const a = document.createElement('a'); a.href = el.textContent.trim(); a.textContent = 'Video call';
      el.replaceWith(a);
    }
  }
  // Forecast rows: line breaks inside a cell become separators.
  for (const br of $$('.fd br, .sday br')) br.replaceWith(document.createTextNode(' · '));
  // Header: one edition time lives in the running head, not here.
  for (const el of $$('header *')) {
    if (!el.children.length && /·\s*Updated/i.test(el.textContent)) el.textContent = el.textContent.replace(/\s*·\s*Updated.*$/i, '');
  }

  // 5. Money gets its own section; section and card renames.
  const sports = $('section.group[data-sec=sports]');
  if (sports) {
    const money = document.createElement('section');
    money.className = 'group'; money.dataset.sec = 'markets'; money.id = 'markets';
    money.innerHTML = '<div class="sec-head"><div class="sec-titles"><h2 class="sec-h">Money and Markets</h2>' +
      '<p class="sec-sub">The markets this morning, helium and Portland real estate</p></div></div><div class="sec-body"></div>';
    const mb = money.querySelector('.sec-body');
    for (const s of ['#mkt-h', '#he-h', '#re-h']) { const c = cardOf(s); if (c) mb.appendChild(c); }
    if (mb.children.length) sports.after(money);
  }
  const SEC = { sports: ['Sports', 'Blazers, Timbers, the Vikings and Pilots, and Formula 1'], delights: ['The Back Page', null],
                almanac: ['Almanac', null], science: ['Science', null], civics: ['Civics', null], doodles: ['By the Numbers', null],
                world: ['Bangkok', null], nearby: ['The Sky', null] };
  for (const [id, [title, sub]] of Object.entries(SEC)) {
    const g = $(`section.group[data-sec=${id}]`); if (!g) continue;
    const h = g.querySelector('.sec-h'); if (h) h.textContent = title;
    if (sub) { const p = g.querySelector('.sec-sub'); if (p) p.textContent = sub; }
  }
  const CARD = { '#finds-h': 'New to try', '#localnews-h': 'Portland news', '#reps-h': 'Who speaks for you' };
  for (const [s, t] of Object.entries(CARD)) { const h = $(s); if (h) h.textContent = t; }

  // 18. Almanac: holidays move in; "Observed today" keeps three; extracts go.
  const alm = $('section.group[data-sec=almanac] .sec-body'), hol = cardOf('#holidays');
  if (alm && hol) alm.appendChild(hol);
  const obs = $('#hol-today');
  if (obs) { const as = [...obs.querySelectorAll('a, span')].filter(a => a.parentElement === obs);
    if (as.length > 3) obs.innerHTML = '<b>Observed today:</b> ' + as.slice(0, 3).map(a => a.outerHTML).join(' · '); }
  for (const sm of $$('section.group[data-sec=almanac] .lines span > br + small')) { kill(sm.previousElementSibling); kill(sm); }

  // 19. What leads: Solar before sunrise, Civics, Sports.
  const sbody = $('section.group[data-sec=solar] .sec-body'), now = $('#t-now');
  if (sbody && now && parseFloat(txt(now)) === 0) {
    const tiles = sbody.querySelector('.tiles');
    for (const s of ['#bill-h', '#loads-h'].reverse()) { const c = cardOf(s); if (c) sbody.prepend(c); }
    if (tiles) { const after = cardOf('#bill-h'); if (after) after.after(tiles); }
  }
  const cbody = $('section.group[data-sec=civics] .sec-body'), reps = cardOf('#reps-h');
  if (cbody && reps) cbody.prepend(reps);
  // Senators' identical vote lists: keep three each.
  for (const h of $$('h3.sub')) if (/Recent floor votes/i.test(txt(h))) {
    const l = h.nextElementSibling; if (l) [...l.children].slice(3).forEach(kill);
  }

  // 9 & 17. Text tidying: times, dates, feed boilerplate, stale relative times.
  const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const fix = t => t
    .replace(/\b(\d{1,2}):00\s?([AaPp])\.?[Mm]\.?/g, (m, h, ap) => `${h} ${ap.toLowerCase()}m`)
    .replace(/\b(\d{1,2}:\d\d)\s?([AaPp])\.?[Mm]\.?/g, (m, h, ap) => `${h} ${ap.toLowerCase()}m`)
    .replace(/\b(20\d\d)-(\d\d)-(\d\d)\b/g, (m, y, mo, d) => `${MON[+mo - 1]} ${+d}${y !== String(new Date().getFullYear()) ? ', ' + y : ''}`)
    .replace(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2}) (20\d\d)\b/g, '$1 $2, $3')
    .replace(/\b(\d{1,2}(?::\d\d)? [ap]m) (?:–|-|to) \1\b/g, '$1')
    .replace(/\s*The post .* appeared first on .*$/i, '')
    .replace(/\s*The post .*$/i, m => m.length > 20 ? '' : m);
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const v = fix(n.nodeValue); if (v !== n.nodeValue) n.nodeValue = v;
  }
  for (const el of $$('small, .meta, .cite, p, span')) {
    if (el.children.length) continue;
    const t = el.textContent;
    if (/…$/.test(t.trim()) && t.length > 60) {
      const cut = t.slice(0, t.lastIndexOf('…')).match(/^.*[.!?](?=\s|$)/s);
      if (cut && cut[0].length > 40) el.textContent = cut[0];
    }
  }
  const todayLong = new Date().toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric'});
  for (const el of $$('.meta, small')) {
    if (!el.children.length && /^(Checked|Updated|Listened)\b/i.test(el.textContent.trim()) &&
        (/\bago\b/.test(el.textContent) || el.textContent.includes(todayLong) || /today/i.test(el.textContent))) kill(el);
  }

  // 11. Sources: gather each section's source lines into one note at its foot.
  for (const g of $$('section.group')) {
    const lines = [...g.querySelectorAll('.src-line')];
    if (!lines.length) continue;
    const seen = new Set(), parts = [];
    for (const l of lines) {
      for (const a of l.querySelectorAll('a[href]')) {
        const k = txt(a); if (!k || seen.has(k)) continue; seen.add(k); parts.push(a.cloneNode(true).outerHTML);
      }
      if (!l.querySelector('a[href]')) { const k = txt(l).replace(/^Sources?:\s*/i, ''); if (k && !seen.has(k)) { seen.add(k); parts.push(k); } }
      l.remove();
    }
    if (parts.length) {
      const p = document.createElement('p'); p.className = 'ksources';
      p.innerHTML = '<b>Sources</b> ' + parts.join(' · ');
      (g.querySelector('.sec-body') || g).appendChild(p);
    }
  }

  // 8. Whole-card links: only the headline should look like a link.
  for (const a of $$('a[href]')) {
    if (a.querySelector('div, p, img, h2, h3, small') || txt(a).length > 120) a.classList.add('kblock');
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
  // Colour emoji print as grey smudges on e-ink; a publisher would drop them.
  const EMO = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F000}-\u{1F2FF}\u{FE0F}\u{200D}]/gu;
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) if (EMO.test(n.nodeValue)) n.nodeValue = n.nodeValue.replace(EMO, '').replace(/^\s+(?=\S)/, '');
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
    if (h.startsWith('javascript:') || h === '#') { a.removeAttribute('href'); continue; }
    if (h.startsWith('#')) { a.setAttribute('href', 'KHASH:' + h.slice(1)); continue; }
    a.href = abs(h); a.removeAttribute('target');
  }
  for (const el of document.querySelectorAll('[style*="url("]')) {
    if (/background/.test(el.getAttribute('style') || '')) el.style.backgroundImage = 'none';
  }
  for (const el of document.querySelectorAll('*')) {
    for (const at of [...el.attributes]) if (at.name.startsWith('on')) el.removeAttribute(at.name);
  }
  // Keep only the dashboard rules that still match something here, flattening
  // media queries at this screen size. Cuts the stylesheet the Kindle parses.
  const used = [];
  const strip = sel => sel.replace(/::?(before|after|marker|placeholder|selection|first-letter|first-line|-webkit-[a-z-]+)\b/g, '')
                          .replace(/:(hover|focus|focus-visible|focus-within|active|visited|target)\b/g, '');
  const walk = rules => {
    for (const r of rules) {
      if (r.type === 1) {
        let hit = false;
        for (const part of r.selectorText.split(',')) {
          try { if (document.querySelector(strip(part).trim() || '*')) { hit = true; break; } } catch (e) { hit = true; break; }
        }
        if (hit) used.push(r.cssText);
      } else if (r.type === 4) {
        if (window.matchMedia(r.conditionText || r.media.mediaText).matches) walk(r.cssRules);
      } else if (r.type === 12) {
        try { if (CSS.supports(r.conditionText)) walk(r.cssRules); } catch (e) {}
      }
    }
  };
  for (const sh of document.styleSheets) {
    if (!sh.ownerNode || sh.ownerNode.tagName !== 'STYLE' || sh.ownerNode.id === 'keink') continue;
    try { walk(sh.cssRules); } catch (e) {}
  }
  const css = used.join('\n');
  // A few lines for the front of the edition.
  const t = el => (el ? (el.innerText || el.textContent) : '').replace(/\s+/g, ' ').trim();
  const glance = [];
  const wx = t(document.querySelector('#hero-wx'));
  if (wx) glance.push(wx);
  const tc = document.querySelector('#today-card');
  if (tc) { const p = tc.querySelector('p, .summary, .note'); if (p && t(p)) glance.push(t(p)); }
  document.querySelectorAll('#brief ol li').forEach((li, i) => { if (i < 3) glance.push(t(li)); });
  const drv = document.querySelector('#drives > *');
  if (drv && t(drv)) glance.push('Drive: ' + t(drv));
  const links = [...document.querySelectorAll('link[rel=stylesheet]')].map(l => l.href);
  const groups = [...document.querySelectorAll('section.group')];
  const sections = groups.map(g => {
    const heads = [...g.querySelectorAll('.sec-body .card h2[id], .sec-body > section h2[id]')].filter(h => h.textContent.trim());
    if (g.getBoundingClientRect().height > 4 * innerHeight && heads.length >= 4) {
      const p = document.createElement('p'); p.className = 'kinthis';
      p.innerHTML = '<b>In this section</b> ' + heads.map(h => `<a href="#${h.id}">${h.textContent.trim()}</a>`).join(' · ');
      const sh = g.querySelector('.sec-head'); if (sh) sh.after(p); else g.prepend(p);
    }
    const h = g.querySelector('.sec-h, h2'), sub = g.querySelector('.sec-sub');
    return { id: g.dataset.sec || g.id, title: (g.dataset.ktitle || (h ? h.textContent : g.id)).trim(),
             sub: g.dataset.ksub || (sub ? sub.textContent.trim() : ''), html: g.outerHTML };
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
  return { css, links, sections, intro, bodyClass, htmlClass, glance };
}
"""

EINK_CSS = r"""
/* ===== Kindle edition: editorial black-and-white override =====
   One serif family (Literata, designed for e-reading), small caps for labels,
   hairline rules instead of boxes, and no colour, shadows or motion. */
:root{--k-ink:#111;--k-grey:#555;--k-rule:#000;--k-hair:#bbb;--k-serif:'Literata',Georgia,'Times New Roman',serif}
html,body{background:#fff !important;background-image:none !important}
html body{color:var(--k-ink) !important;margin:0 !important;padding:0 22px 48px !important;max-width:none !important;
  font:400 19px/1.55 var(--k-serif) !important;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  font-feature-settings:"kern","liga","pnum","onum"}
html body *,html body *::before,html body *::after{animation:none !important;transition:none !important;box-shadow:none !important;
  text-shadow:none !important;backdrop-filter:none !important;-webkit-backdrop-filter:none !important;
  font-family:var(--k-serif) !important;letter-spacing:normal;transform:none !important;filter:none !important}
html body main *{border-radius:0 !important;background-image:none !important}
html body main *::before,html body main *::after{background-image:none !important}
.magic .card.ink,.card,.dd .wash,.dd text{opacity:1 !important}

/* Decoration that only made sense in colour */
.sec-icon,.doodle,.sec-tools,.sec-head::before,.sec-head::after,header>.puff,header svg,header .scene,
.unclamp,.stripes,.j-tape,.tape{display:none !important}

/* Masthead / greeting */
main>header,header{display:block !important;min-height:0 !important;height:auto !important;padding:0 0 14px !important;margin:0 0 6px !important;
  background:#fff !important;border:0 !important;border-bottom:1px solid var(--k-rule) !important}
header h1{font:700 40px/1.05 var(--k-serif) !important;letter-spacing:-.01em !important;margin:6px 0 8px !important;color:#000 !important}

/* Section openers */
.group{margin:0 !important;padding:0 !important;background:none !important}
.sec-head{display:block !important;background:none !important;border:0 !important;outline:0 !important;padding:6px 0 12px !important;
  margin:4px 0 18px !important;border-bottom:3px double var(--k-rule) !important;opacity:1 !important}
.sec-head .sec-h,.group[data-tier] .sec-head .sec-h{font:700 38px/1.05 var(--k-serif) !important;letter-spacing:-.015em !important;
  color:#000 !important;text-transform:none !important;margin:0 !important}
.sec-sub,.group[data-tier] .sec-sub{font:italic 400 17px/1.45 var(--k-serif) !important;color:var(--k-grey) !important;margin:8px 0 0 !important}
.sec-head .pill,.sec-sub::before{display:none !important;content:none !important}
.sec-h .cap{font:inherit !important;color:inherit !important;margin:0 !important;display:inline !important}

/* Cards become articles separated by rules */
.card,.joy-card,.brief,.tile{background:#fff !important;border:0 !important;outline:0 !important;padding:0 !important;margin:0 0 26px !important;
  color:var(--k-ink) !important}
.sec-body>.card+.card,.sec-body .card+.card,.row>.card+.card{border-top:1px solid var(--k-rule) !important;padding-top:22px !important}
.card h2,.card .head h2,.brief h2{font:700 25px/1.2 var(--k-serif) !important;color:#000 !important;margin:0 0 6px !important;
  letter-spacing:-.005em !important;text-transform:none !important}
.card h3,h3.sub,.day-h,.sub{font:600 13px/1.3 var(--k-serif) !important;text-transform:uppercase !important;letter-spacing:.12em !important;
  color:#000 !important;margin:20px 0 8px !important;padding:0 0 4px !important;border-bottom:1px solid var(--k-hair) !important;background:none !important;position:static !important}
.card .head{display:block !important;margin:0 0 6px !important}
.card .head small,.card .head .meta,.meta,.cite,.src-line,.note,small{font:italic 400 15px/1.45 var(--k-serif) !important;color:var(--k-grey) !important}
p{margin:0 0 .7em !important}
b,strong{font-weight:700 !important;color:#000 !important;background:none !important}
mark,.mark,.hl{background:none !important;font-weight:700 !important;text-decoration:none !important;border-bottom:0 !important}

/* Figures: tiles and big numbers */
.tiles{display:grid !important;grid-template-columns:1fr 1fr !important;gap:0 !important;border-top:1px solid var(--k-rule) !important;margin:0 0 26px !important}
.tiles .tile{margin:0 !important;padding:14px 12px 14px 0 !important;border-bottom:1px solid var(--k-hair) !important}
.tiles .tile:nth-child(odd){border-right:1px solid var(--k-hair) !important}
.tiles .tile:nth-child(even){padding-left:14px !important}
.tile .k,.k{display:block !important;font:600 12px/1.3 var(--k-serif) !important;text-transform:uppercase !important;letter-spacing:.12em !important;color:var(--k-grey) !important}
.tile .big,.big{font:700 34px/1.1 var(--k-serif) !important;color:#000 !important;letter-spacing:-.01em !important}
.tile .u,.u{font:400 17px var(--k-serif) !important;color:var(--k-grey) !important}
.tile .s{font:italic 15px/1.4 var(--k-serif) !important;color:var(--k-grey) !important}

/* Lists and rows */
ul,ol{padding-left:1.15em !important;margin:0 0 .8em !important}
li{margin:0 0 .45em !important}
li::marker{color:#000 !important;font-weight:600}
.lines>div,.story,.row-line{border:0 !important;border-bottom:1px solid var(--k-hair) !important;padding:9px 0 !important;background:none !important}
.lines>div:last-child,.story:last-child{border-bottom:0 !important}
.story .headline,.headline{font:600 19px/1.35 var(--k-serif) !important;color:#000 !important}
.story .summary,.summary{font:400 16.5px/1.5 var(--k-serif) !important;color:#222 !important}

/* Chips and pills read as quiet labels */
.pill,.chip,.tag,.badge{background:none !important;border:1px solid #000 !important;color:#000 !important;
  font:600 12px/1.2 var(--k-serif) !important;letter-spacing:.06em !important;text-transform:uppercase !important;padding:3px 7px !important}

/* Images: full width, quiet grey, captions in italic */
main img{max-width:100% !important;height:auto !important;display:block;margin:8px 0 6px !important;border:0 !important;
  filter:grayscale(1) contrast(1.08) !important;-webkit-filter:grayscale(1) contrast(1.08) !important}
main svg{max-width:100% !important;height:auto}
.poster,.poster img{float:none !important}
figcaption,.caption{font:italic 15px/1.4 var(--k-serif) !important;color:var(--k-grey) !important}

a,a:visited{color:inherit !important}

/* Old "show more" folds are open; their summary reads as a sub-head */
details>summary{list-style:none;font:600 13px/1.3 var(--k-serif) !important;text-transform:uppercase;letter-spacing:.12em;margin:18px 0 8px !important;color:#000 !important}
details>summary::-webkit-details-marker{display:none}

/* ---- Edition chrome: running head, folio, contents ---- */
.krun{display:flex;justify-content:space-between;align-items:baseline;font:600 12px/1 var(--k-serif);text-transform:uppercase;letter-spacing:.14em;
  color:#000;padding:14px 0 9px;border-bottom:1px solid #000;margin:0 0 18px}
.krun a{text-decoration:none !important}
.kfoot{margin:36px 0 0;border-top:1px solid #000;padding:14px 0 0;font:400 16px/1.4 var(--k-serif)}
.kfoot .knext{display:block;text-decoration:none !important;padding:6px 0 10px}
.kfoot .knext small{display:block;font:600 12px/1.2 var(--k-serif) !important;font-style:normal !important;text-transform:uppercase;letter-spacing:.14em;color:var(--k-grey) !important}
.kfoot .knext span{font:700 24px/1.2 var(--k-serif)}
.kfoot .kmeta{display:flex;justify-content:space-between;font:italic 14px var(--k-serif);color:var(--k-grey);padding-top:8px;border-top:1px solid var(--k-hair)}
.kfoot .kmeta a{color:var(--k-grey) !important}
.kmast{text-align:center;padding:26px 0 0}
.kmast .kname{font:700 46px/1 var(--k-serif);letter-spacing:-.01em;margin:0}
.kmast .kdate{font:600 12px/1 var(--k-serif);text-transform:uppercase;letter-spacing:.18em;border-top:3px double #000;border-bottom:1px solid #000;
  padding:9px 0;margin:16px 0 0}
.kmast .kdeck{font:italic 17px/1.45 var(--k-serif);color:var(--k-grey);margin:14px 0 0}
.ktoc{list-style:none;padding:0 !important;margin:18px 0 0 !important;counter-reset:k}
.ktoc li{margin:0 !important;border-bottom:1px solid var(--k-hair)}
.ktoc a{display:grid;grid-template-columns:2.2em 1fr;padding:13px 0;text-decoration:none !important}
.ktoc .kn{font:600 14px/1.9 var(--k-serif);color:var(--k-grey);font-variant-numeric:tabular-nums}
.ktoc .kt{font:700 21px/1.25 var(--k-serif)}
.ktoc .kteaser{display:block;font:italic 15.5px/1.4 var(--k-serif);color:var(--k-grey);margin-top:3px}
.khint{font:italic 14px/1.4 var(--k-serif);color:var(--k-grey);text-align:center;margin:12px 0 0}

/* ===== Second pass, from the design and publishing review ===== */
:root{--fs-label:12.5px;--fs-meta:15px;--fs-small:16.5px;--fs-body:18.5px;--fs-head:23px;--fs-sec:36px}
html body{font-size:var(--fs-body) !important;line-height:1.5 !important}
.card h2,.card .head h2,.brief h2{font-size:var(--fs-head) !important}
.sec-head .sec-h,.group[data-tier] .sec-head .sec-h{font-size:var(--fs-sec) !important}
.summary,.story .summary,.card p,.lines small,.task p{font:400 var(--fs-small)/1.5 var(--k-serif) !important;color:#222 !important}
.note,.cite{font:400 var(--fs-small)/1.5 var(--k-serif) !important;color:#333 !important;font-style:normal !important}
.meta,.card .head .meta,.src-line,figcaption,.caption{font:italic 400 var(--fs-meta)/1.4 var(--k-serif) !important;color:var(--k-grey) !important}

/* Links: headlines read as headlines; only inline text links are underlined */
a{text-decoration:none !important}
p a[href],.note a[href],.cite a[href],.meta a[href],small a[href],.ksources a[href],li a[href]:not(.story):not(.kblock){text-decoration:underline !important;
  text-decoration-thickness:1px !important;text-underline-offset:3px !important;text-decoration-color:#999 !important}
a:not([href]),a.kblock,a.kblock *,a.story,a.story *,a.card,a.sci,a.book,a.read-fresh{text-decoration:none !important}

/* Colour-coded words become typographic */
.look-col li::before{background:#000 !important;opacity:1 !important;width:5px !important;height:5px !important;top:.85em !important}
.rt{background:none !important;padding:0 !important;font:400 15px/1.3 var(--k-serif) !important;color:#000 !important}
.rt4{font-weight:700 !important;font-variant:small-caps;letter-spacing:.04em}
.rt3{font-weight:600 !important}
.rt1{font-style:italic !important;color:var(--k-grey) !important}
.party{border:0 !important;padding:0 !important;font-weight:400 !important;color:var(--k-grey) !important;background:none !important}
.party::before{content:"("} .party::after{content:")"}

/* Boxes become rules */
.mini,.facts>div,.joy-stats div,.load,.brk,.rep,.look-col,.spot,.empty,.recap,.idea,.rec{border:0 !important;outline:0 !important;padding:0 !important;background:none !important}
.facts,.joy-stats{display:grid !important;grid-template-columns:1fr 1fr !important;gap:0 !important;border-top:1px solid #000 !important;margin:14px 0 22px !important}
.facts>*,.joy-stats>div{padding:10px 12px 10px 0 !important;border-bottom:1px solid var(--k-hair) !important;text-align:left !important}
.facts>*:nth-child(odd),.joy-stats>div:nth-child(odd){border-right:1px solid var(--k-hair) !important}
.facts>*:nth-child(even),.joy-stats>div:nth-child(even){padding-left:14px !important}
.mini .v,.joy-stats b{font:700 26px/1.15 var(--k-serif) !important;text-transform:none !important;letter-spacing:-.005em !important}
.mini .v small{font:400 15px var(--k-serif) !important;color:var(--k-grey) !important;text-transform:none !important}
.mini .k,.mini>span:first-child{text-transform:uppercase !important}
.load,.brk,.rep,.idea,.rec,.recap,.look-col{border-top:1px solid var(--k-hair) !important;padding-top:12px !important;margin-top:12px !important}
.ideas,.recs,.look-grid{display:block !important}
.rec::before,.rec::after,.rec-art,.vinyl{display:none !important}
.rec b{display:block;font:700 20px/1.25 var(--k-serif) !important}
.rec-k{display:block;font:600 12px/1.3 var(--k-serif) !important;letter-spacing:.14em;text-transform:uppercase;color:var(--k-grey) !important}
.kid-setup,.empty,.brief-icon,.refresh,.poem-more{display:none !important}

/* Forecast strips become ruled tables, one day per line */
.fc,.sdays{display:block !important;overflow:visible !important;margin:8px 0 0 !important;border-top:1px solid #000 !important}
.fd,.sday{display:grid !important;grid-template-columns:4.2em 5.6em 1fr auto;column-gap:10px;align-items:baseline;text-align:left !important;
  border:0 !important;border-bottom:1px solid var(--k-hair) !important;padding:7px 0 !important;font:400 16px/1.35 var(--k-serif) !important;color:#000 !important;min-width:0 !important}
.fd svg{display:none !important}
.fd .d,.sday .d{font-weight:700 !important}
.fd .meta{font-style:normal !important}
.fd .t,.sday>span{font-variant-numeric:tabular-nums lining-nums}

/* Science */
.sci-ph{display:none !important}
.sci-lead,.sci-grid{display:block !important}
.sci-topic{background:none !important;padding:0 !important;font:600 12px/1.3 var(--k-serif) !important;letter-spacing:.12em !important;color:var(--k-grey) !important}
.sci-title{display:block;font:700 22px/1.22 var(--k-serif) !important;margin:2px 0 6px !important}
.sci-lead .sci-title{font-size:28px !important;line-height:1.15 !important}
.sci-means i{display:inline !important;font:italic 600 16px var(--k-serif) !important;text-transform:none !important;letter-spacing:0 !important;color:#000 !important}
.sci-means i::after{content:". "}

/* Buttons become quiet text links */
.joy-btn,.rec a.link,.lines a.link,a.link{display:inline !important;border:0 !important;background:none !important;padding:0 !important;min-height:0 !important;
  font:600 13px/1.3 var(--k-serif) !important;letter-spacing:.1em !important;text-transform:uppercase !important;color:#000 !important}
.joy-btn::after,a.link[href]::after{content:" \2192"}
.shelf-h{display:block !important;font:600 12px/1.3 var(--k-serif) !important;letter-spacing:.14em !important;text-transform:uppercase !important;color:var(--k-grey) !important;margin:0 0 4px !important;padding:0 !important}
.shelf-h span,.shelf-h::after{display:none !important}

/* Verse in full, at body size */
.poem-long{max-height:none !important;overflow:visible !important;-webkit-mask-image:none !important;mask-image:none !important}
.poem-text{font:400 18px/1.5 var(--k-serif) !important;color:#000 !important}
.poem-text span{padding-left:1.5em !important;text-indent:-1.5em !important}

/* Standing heads: rule above, not below */
.card h3,h3.sub,.day-h,.sub,details>summary{border-bottom:0 !important;border-top:1px solid #000 !important;padding:7px 0 0 !important;margin:26px 0 6px !important}
.lines>div:first-child{border-top:0 !important}

/* One rule system between articles */
.src-line{border-top:0 !important;margin:8px 0 0 !important;padding:0 !important;font-size:14px !important}
.sec-body .card,.row>.card,.joy-card{margin:0 !important;padding:0 0 28px !important}
.sec-body .card+.card,.row>.card+.card,.row+.card,.card+.row>.card:first-child,.sec-body>.brief{border-top:1px solid #000 !important;padding-top:20px !important}
.sec-head{margin:4px 0 22px !important}

/* Badges lose their boxes */
.pill,.tag,.badge{border:0 !important;padding:0 0 0 .4em !important;font:600 11.5px/1.2 var(--k-serif) !important;letter-spacing:.1em !important;color:var(--k-grey) !important;vertical-align:1px}
.pill::before,.tag::before,.badge::before{content:"\00B7\00A0";letter-spacing:0}

/* Almanac facts read as a sentence, not shouting chips */
.chips{display:block !important;background:none !important;margin:0 0 18px !important}
.chip{display:inline !important;border:0 !important;padding:0 !important;text-transform:none !important;letter-spacing:0 !important;font:italic 400 var(--fs-small)/1.5 var(--k-serif) !important;color:#000 !important}
.chip+.chip::before{content:" \00B7  "}
#hol-today{background:none !important;color:#000 !important;padding:10px 0 0 !important;border-top:1px solid var(--k-hair)}

/* Chart labels knock out of the lines beneath them */
main svg text{paint-order:stroke fill;stroke:#fff !important;stroke-width:5px !important;stroke-linejoin:round;font-size:13px !important;font-weight:600 !important}
.dd text{font-size:15px !important}
main svg{overflow:visible}

/* Figures in columns */
.lines>div>span:last-child,.lines>div>b:last-child{font-weight:500 !important;font-variant-numeric:tabular-nums lining-nums;white-space:nowrap;padding-left:12px}
.tile .big,.big,.mini .v,.ktoc .kn{font-variant-numeric:tabular-nums lining-nums}

/* Images, logos, covers */
.team-top img{display:none !important} .team-top{display:block !important}
.poster,.book img,.book svg{float:right !important;width:56px !important;height:auto !important;margin:2px 0 6px 12px !important;background:none !important;border:1px solid var(--k-hair) !important}
.book{display:block !important;overflow:hidden}
main img{filter:grayscale(1) contrast(1.15) brightness(1.05) !important;-webkit-filter:grayscale(1) contrast(1.15) brightness(1.05) !important}

/* Edition furniture added by the generator */
.kkicker{font:600 12px/1.3 var(--k-serif) !important;letter-spacing:.14em !important;text-transform:uppercase !important;color:var(--k-grey) !important;margin:0 0 4px !important}
.ksources{font:italic 14px/1.5 var(--k-serif) !important;color:var(--k-grey) !important;border-top:1px solid var(--k-hair);padding-top:10px;margin-top:8px !important}
.ksources b{font:600 12px var(--k-serif) !important;font-style:normal !important;letter-spacing:.12em;text-transform:uppercase;color:#000 !important;margin-right:6px}
.kinthis{font:400 15px/1.6 var(--k-serif) !important;color:var(--k-grey);margin:-10px 0 22px !important}
.kinthis b{font:600 12px var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;color:#000 !important;margin-right:6px}
.kinthis a{text-decoration:underline !important;text-decoration-color:#999 !important;text-underline-offset:3px}
.krun{font-weight:500 !important;letter-spacing:.12em !important}
.kcontents .krun{display:none}
.ktoc a{display:flex !important;align-items:baseline;gap:0;padding:10px 0 !important}
.ktoc .kn{width:2.2em;flex:none;line-height:1 !important}
.ktoc .kteaser{font-size:15px !important;line-height:1.35 !important}
.kpart{font:600 12px/1.3 var(--k-serif);letter-spacing:.16em;text-transform:uppercase;border-top:1px solid #000;padding:8px 0 0;margin:26px 0 0;list-style:none}
.kglance{border:1px solid #000;padding:14px 16px 6px;margin:22px 0 4px}
html body .ktoc li a[href],html body .ktoc li a[href] *{text-decoration:none !important}
.kglance h2{font:600 12px/1.3 var(--k-serif) !important;letter-spacing:.16em;text-transform:uppercase;margin:0 0 8px !important}
.kglance ul{list-style:none;padding:0 !important}
.kglance li{font:400 16.5px/1.45 var(--k-serif);border-bottom:1px solid var(--k-hair);padding:0 0 7px;margin:0 0 7px !important}
.kglance li:last-child{border-bottom:0}
.kfoot .knext small{letter-spacing:.14em}
.kfoot .knext span{font-size:20px !important}
"""

# Tap the right two thirds of the screen to go forward a screen, the left
# third to go back. Taps on links still follow the link. Old-browser safe.
PAGER_JS = """
<script>
(function(){
  function turn(dir){
    var H = window.innerHeight, step = Math.round(H * 0.92);
    if (dir > 0 && document.elementFromPoint) {
      var el = document.elementFromPoint(window.innerWidth / 2, H - 6);
      if (el) { var top = el.getBoundingClientRect().top; if (top > H * 0.45 && top < H - 4) step = Math.round(top - 10); }
    }
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


FONT_CSS = ("https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@"
            "0,7..72,400..700;1,7..72,400..700&display=block")


def page(title, body, html_class, body_class, prev=None, nxt=None, stamp="", run_left="", run_right="", fonts=""):
    esc = html.escape
    top = f'<nav class="krun"><a href="index.html">{run_left}</a><span>{esc(run_right)}</span></nav>'
    nxt_block = (f'<a class="knext" href="{nxt}"><small>Continued in</small><span>{esc(prev_title(nxt))} &rarr;</span></a>' if nxt
                 else '<a class="knext" href="index.html"><small>The end</small><span>Back to contents &rarr;</span></a>')
    prev_link = f'<a href="{prev}">&larr; {esc(prev_title(prev))}</a>' if prev else '<span></span>'
    foot = f'<footer class="kfoot">{nxt_block}<div class="kmeta">{prev_link}<span>{stamp}</span></div></footer>'
    js = PAGER_JS.replace("NEXT", repr(nxt or "")).replace("PREV", repr(prev or ""))
    return f"""<!doctype html>
<html lang="en" class="{esc(html_class)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>{fonts}<link rel="stylesheet" href="kindle.css"></head>
<body class="{esc(body_class)}">
{top}
<main>{body}</main>
{foot}
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
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html?kindle"
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
        # Show everything that sits behind "N more" / "Show all" on the live page.
        p.evaluate("""() => {
          document.querySelectorAll('details').forEach(d => { d.open = true; });
          document.querySelectorAll('.clamped').forEach(c => c.classList.remove('clamped'));
        }""")
        p.evaluate(CURATE)
        p.evaluate("css => { const s = document.createElement('style'); s.id = 'keink'; s.textContent = css; document.head.appendChild(s); }", EINK_CSS)
        p.wait_for_timeout(300)
        p.evaluate(GRAYSCALE)
        p.evaluate(CONTRAST)
        longdate = p.evaluate("new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'})")
        data = p.evaluate(EXTRACT)
        browser.close()
    srv.shutdown()
    return data, stamp, longdate


# A morning read: your day first, then the news, then home, town and the back pages.
PARTS = [
    ("Your day", ["today", "roads"]),
    ("The news", ["news", "sports", "markets"]),
    ("Home and land", ["solar", "family", "garden", "river", "nearby"]),
    ("Town and culture", ["local", "music", "watch", "coast"]),
    ("The back pages", ["science", "civics", "almanac", "world", "delights", "doodles"]),
]


def self_host_fonts(out):
    """Save Literata next to the pages so the Kindle never paints a fallback
    font and refreshes again. Falls back to Google Fonts if this fails."""
    import re
    import urllib.request
    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    try:
        req = urllib.request.Request(FONT_CSS, headers={"User-Agent": ua})
        css = urllib.request.urlopen(req, timeout=20).read().decode()
        blocks = re.findall(r"/\* latin \*/\s*(@font-face\s*{[^}]*})", css)
        if not blocks:
            raise ValueError("no latin font faces")
        os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
        local, preload = [], []
        for i, blk in enumerate(blocks):
            url = re.search(r"url\((https://[^)]+\.woff2)\)", blk).group(1)
            name = f"literata-{i}.woff2"
            with open(os.path.join(out, "fonts", name), "wb") as f:
                f.write(urllib.request.urlopen(url, timeout=30).read())
            local.append(blk.replace(url, f"fonts/{name}"))
            preload.append(f'<link rel="preload" href="fonts/{name}" as="font" type="font/woff2" crossorigin>')
        return "\n".join(local), "".join(preload)
    except Exception as e:  # network trouble only costs the font, not the edition
        print(f"kindle_full: using Google Fonts link ({e!r})", file=sys.stderr)
        return "", f'<link rel="stylesheet" href="{FONT_CSS}">'


def main(site):
    import re
    data, stamp, longdate = snapshot(site)
    out = os.path.join(site, "kindle")
    os.makedirs(out, exist_ok=True)
    font_css, font_links = self_host_fonts(out)
    with open(os.path.join(out, "kindle.css"), "w") as f:
        f.write(font_css + "\n" + data["css"] + "\n" + EINK_CSS)

    by_id = {s["id"]: s for s in data["sections"] if s["html"].strip()}
    known = [i for _, ids in PARTS for i in ids]
    parts = [(name, [i for i in ids if i in by_id]) for name, ids in PARTS]
    extra = [i for i in by_id if i not in known]
    if extra:
        parts.append(("More", extra))
    parts = [(name, ids) for name, ids in parts if ids]
    order = [i for _, ids in parts for i in ids]
    files = {i: f"{i}.html" for i in order}
    _TITLES.update({files[i]: by_id[i]["title"] for i in order})
    _TITLES["index.html"] = "Contents"

    # In-page links (Alfred's "see the calendar card") point at the page that holds that card.
    where = {}
    for i in order:
        for anchor in re.findall(r'\sid="([^"]+)"', by_id[i]["html"] + (data["intro"] if i == order[0] else "")):
            where.setdefault(anchor, files[i])

    def link_fix(doc):
        return re.sub(r'href="KHASH:([^"]*)"',
                      lambda m: f'href="{where[m.group(1)]}#{m.group(1)}"' if m.group(1) in where else "", doc)

    edition = stamp.split(" ", 1)[-1].replace("AM", "am").replace("PM", "pm")
    shortdate = longdate.split(",")[0][:3] + " " + " ".join(longdate.split(", ")[1].split()[:2]) if ", " in longdate else longdate
    run_left = f"The Morning Edition &middot; {html.escape(shortdate)}"
    stamp_txt = html.escape(f"Edition of {edition}")
    n = len(order)
    for k, i in enumerate(order):
        sec = by_id[i]
        body = (data["intro"] if k == 0 else "") + sec["html"]
        doc = page(sec["title"], link_fix(body), data["htmlClass"], data["bodyClass"],
                   prev=files[order[k - 1]] if k else "index.html", nxt=files[order[k + 1]] if k + 1 < n else None,
                   stamp=stamp_txt, run_left=run_left, run_right=f"{sec['title']} · {k + 1}/{n}", fonts=font_links)
        with open(os.path.join(out, files[i]), "w") as f:
            f.write(doc)

    rows, num = [], 0
    for name, ids in parts:
        rows.append(f'<li class="kpart">{html.escape(name)}</li>')
        for i in ids:
            num += 1
            sec = by_id[i]
            teaser = sec.get("sub", "")
            rows.append(f'<li><a href="{files[i]}"><span class="kn">{num:02d}</span><span><span class="kt">{html.escape(sec["title"])}</span>'
                        + (f'<span class="kteaser">{html.escape(teaser)}</span>' if teaser else "") + "</span></a></li>")
    glance = "".join(f"<li>{html.escape(g)}</li>" for g in data.get("glance", [])[:6])
    body = (f'<div class="kmast"><p class="kname">The Morning Edition</p>'
            f'<p class="kdate">{html.escape(longdate)} &nbsp;·&nbsp; Edition of {html.escape(edition)}</p>'
            f'<p class="kdeck">Your home, your day and the world beyond it, in {n} sections.</p>'
            f'<p class="khint">Tap the right side of a page to read on, the left side to go back.</p></div>'
            + (f'<section class="kglance"><h2>Today at a glance</h2><ul>{glance}</ul></section>' if glance else "")
            + f'<ol class="ktoc">{"".join(rows)}</ol>')
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(page("The Morning Edition", body, "", "kcontents", nxt=files[order[0]] if order else None,
                     stamp=stamp_txt, run_left=run_left, run_right="Contents", fonts=font_links))
    # The old bookmark (kindle.html) opens the edition.
    with open(os.path.join(site, "kindle.html"), "w") as f:
        f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=kindle/index.html">'
                '<a href="kindle/index.html">Open the Morning Edition</a>')
    print(f"kindle_full: wrote {n} sections to {out}")


if __name__ == "__main__":
    main(sys.argv[1])
