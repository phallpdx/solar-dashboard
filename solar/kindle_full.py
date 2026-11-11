"""Snapshot the full dashboard into static, paged pages for the Kindle browser.

The live dashboard builds every card with ~275 KB of JavaScript, which the
Kindle's browser runs slowly or not at all. This renders it once in headless
Chromium (Pacific time, at the Kindle Paperwhite 11's screen size), then
saves what it drew as "The Morning Edition":

    kindle/index.html          cover and contents
    kindle/<section>.html      section fronts
    kindle/<section>-NN.html   one page per card
    kindle/kindle.css          the dashboard's own styles plus the e-ink design
    kindle/fonts/, kindle/img/ Literata and greyscale copies of pictures

Nothing scrolls: the pager cuts a long card into screens at whole items.

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
WIDTH, HEIGHT = 618, 714  # Paperwhite 11 browser: 1236 px / 2, less the toolbar that never hides

# Runs after the e-ink styles are applied: fix any text that is now too faint
# (light text that sat on a coloured card now sits on white) and undo fades.
CONTRAST = r"""
() => {
  for (const el of document.querySelectorAll('.bars *, .rain-bars *, .legend .sw, .legend i, .mix *')) {
    if (el.classList.contains('ly')) continue;
    const m = getComputedStyle(el).backgroundColor.match(/\d+/g);
    if (m && m.length >= 3 && (m.length < 4 || +m[3] > 0) && +m[0] > 150 && +m[0] < 250) el.style.setProperty('background-color', '#5a5a5a', 'important');
  }
  for (const el of document.querySelectorAll('section.group *, header *')) {
    if (el.closest('svg')) continue;
    let own = false;
    for (const n of el.childNodes) if (n.nodeType === 3 && n.nodeValue.trim()) { own = true; break; }
    if (own && parseFloat(getComputedStyle(el).fontSize) < 13) el.style.setProperty('font-size', '13px', 'important');
  }
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
    // Everything past three in a list, and "Also from Alfred", has its own page elsewhere.
    for (const ul of brief.querySelectorAll(':scope > ul.brief-rest')) [...ul.children].slice(3).forEach(kill);
    kill(brief.querySelector('.brief-more'));
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
    money.innerHTML = '<div class="sec-head"><div class="sec-titles"><h2 class="sec-h">Money and markets</h2>' +
      '<p class="sec-sub">The markets this morning, helium and Portland real estate</p></div></div><div class="sec-body"></div>';
    const mb = money.querySelector('.sec-body');
    for (const s of ['#mkt-h', '#he-h', '#re-h']) { const c = cardOf(s); if (c) mb.appendChild(c); }
    if (mb.children.length) sports.after(money);
  }
  const SEC = { sports: ['Sports', 'Blazers, Timbers, the Vikings and Pilots, and Formula 1'], delights: ['Diversions', null],
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

  // 9. Fit for the page: cut repeats and noise so lists read in one screen.
  try {
    // Text the feeds cut off mid-word ends at its last whole sentence.
    for (const el of $$('.story p, .sci-means, .summary')) {
      const t = el.textContent.trim();
      if (t.length >= 150 && !/[.!?"')\]]$/.test(t)) {
        const m = t.match(/^[\s\S]*[.!?](?=\s)/);
        if (m && m[0].length > 60) {
          const i = el.querySelector(':scope > i');
          el.textContent = i ? m[0].replace(txt(i), '').trim() : m[0];
          if (i) el.prepend(i);
        }
      }
    }
    // Today: "Act soon" repeats the calendar page; the hour strip becomes one line.
    kill($('#day-act'));
    const hours = $('#hours');
    if (hours) {
      const cells = [...hours.children].map(c => c.children.length ? [...c.children].map(txt).filter(Boolean).join(' ') : txt(c)).filter(Boolean).slice(0, 8);
      if (cells.length) { const p = document.createElement('p'); p.className = 'note khours'; p.textContent = cells.join(' · '); hours.replaceWith(p); }
      else kill(hours);
    }
    // Lists: drop per-item source lines where the headline is already the link.
    for (const s of ['#finds .cite', '#plan .cite', '#big .cite', '#ski-open .cite']) $$(s).forEach(kill);
    for (const s of $$('#plan small')) { const t = s.textContent; if (t.includes(' · ')) s.textContent = t.split(' · ')[0]; }
    // News: "also CBS News, NBC News, ..." becomes a count; live streams are not stories.
    for (const s of $$('.story small')) {
      const n = (s.innerHTML.match(/ · also [\s\S]*$/) || [''])[0];
      if (n) s.innerHTML = s.innerHTML.replace(/ · also [\s\S]*$/, ` · ${(n.match(/<a /g) || []).length + 1} outlets`);
      s.innerHTML = s.innerHTML.replace(/\S+@\S+ \((.*?)\)/, '$1');
    }
    for (const s of $$('.story')) if (/^LIVE:/.test(txt(s.querySelector('b')))) kill(s);
    // Streaming list: titles only, no posters or synopses.
    $$('#tv img.poster, #tv .poster').forEach(kill);
    $$('#tv .story p').forEach(kill);
    // Liquor store: every blurb says the same thing.
    $$('#liquor .story p').forEach(kill);
    // Planes: a chart that cannot be read on e-ink, and a missing speed.
    kill($('#over'));
    $$('.tide-doodle').forEach(kill);
    // Every card opens with its headline.
    for (const h of $$('section.card > .head')) if (h.parentNode.firstElementChild !== h) h.parentNode.prepend(h);
    for (const b of $$('section.group b, section.group strong')) if (txt(b).length > 160) { const q = document.createElement('span'); q.innerHTML = b.innerHTML; b.replaceWith(q); }  // the tide table below says it in words
    for (const el of $$('#planes *, #flights *')) if (!el.children.length) el.textContent = el.textContent.replace(/ · undefined mph/g, '');
    // Sky: events nobody here will see.
    for (const r of $$('#sky > div')) if (/not much to see|Not visible from Oregon/.test(txt(r))) kill(r);
    if ($('#sats') && !txt($('#sats'))) kill($('#sats'));
    // Sports: empty injury reports and empty pulse boxes.
    for (const p of $$('p.note')) if (/^Nobody on the injury report/.test(txt(p))) { const h = p.previousElementSibling; if (h && /^H3$/.test(h.tagName)) kill(h); kill(p); }
    for (const h of $$('h3')) if (/^r\/\w+/i.test(txt(h))) { const n = h.nextElementSibling; if (n && /lines|note/.test(n.className)) kill(n); kill(h); }
    for (const el of $$('[id^="pulse-"]')) if (!txt(el)) kill(el);
    // Books: a pick "because you loved" the same book, and the formulaic reasons.
    for (const a of $$('#books a.book')) { const t = txt(a.querySelector('b')), why = txt(a.querySelector('.why')); if (t && why.includes(t)) kill(a); }
    $$('#books .why').forEach(kill);
    // Album art placeholders print as black discs.
    $$('#albums img, #albums .art').forEach(kill);
    // Live music: the albums paragraph belongs to "New music out".
    for (const p of $$('#gigs ~ p, #shows ~ p, #concerts ~ p')) if (/no Portland show/i.test(txt(p))) kill(p);
    // Coast events: rating links.
    for (const a of $$('#coast-events a')) if (txt(a) === 'Rating') kill(a.closest('small') || a);
    // Weather station: rain bars are letters with no bars on e-ink.
    $$('.rain-bars').forEach(kill);
    // Calendar: the venue sits on the same line, short.
    for (const s of $$('#cal small')) s.textContent = s.textContent.replace(/, (Portland|Beaverton|Vancouver|Hillsboro|Gresham)?,? ?(OR|WA)\b.*$/, '');
    // Earthquakes: short place names.
    for (const el of $$('#quakes *')) if (!el.children.length) el.textContent = el.textContent.replace(/\d+ km [NSEW]{1,3} of /, '').replace(/, Washington\b/, ', WA').replace(/, Oregon\b/, ', OR');
    // Almanac: the US observance first.
    const obs = $('#observed') || $('#obs');
    if (obs) [...obs.children].sort((a, b) => /Veterans|United States/.test(txt(b)) - /Veterans|United States/.test(txt(a))).forEach(c => obs.appendChild(c));
    // Civics: senators who voted the same way share one list.
    let prevVotes = '', prevName = '';
    for (const r of $$('#reps .rep')) {
      const h = [...r.querySelectorAll('h3')].find(x => /floor votes/i.test(txt(x)));
      const list = h && h.nextElementSibling;
      if (!list) continue;
      const v = txt(list).replace(/\d+/g, '');
      const who = txt(r.querySelector('.rep-head b, .rep-head strong, .rep-head a')) || 'the senator above';
      if (v && v === prevVotes) { const n = document.createElement('p'); n.className = 'note'; n.textContent = `Voted the same way as ${prevName} on each of these.`; list.replaceWith(n); }
      else { prevVotes = v; prevName = who; }
    }
  } catch (e) { console.log('kindle fit cuts: ' + e); }
  // 10. Editor's pass: clean feed leftovers, repeats and house style.
  try {
    const sentenceCut = el => {
      const t = el.textContent.trim();
      const cut = /(…|\.\.\.)$/.test(t) || (t.length >= 200 && /[a-z,]$/.test(t) && !/\d ?[ap]m$/.test(t));
      if (!cut) return;
      const m = t.replace(/(…|\.\.\.)$/, '').match(/^[\s\S]*[.!?]["”’)]?(?=\s)/);
      if (m && m[0].length > 40) el.textContent = m[0];
    };
    for (const el of $$('section.group *')) if (!el.children.length && el.textContent.trim().length >= 60 && !el.closest('.poem-text')) sentenceCut(el);
    // Trailing "· Source", "· Details" and dangling separators in decks and meta lines.
    for (const el of $$('.meta, small, .cite, .sub-meta')) {
      let h = el.innerHTML, prev;
      do { prev = h; h = h.replace(/\s*·\s*(<a\b[^>]*>)?\s*(Source|Details|Rating)\s*(<\/a>)?\s*$/i, '').replace(/\s*·\s*$/, ''); } while (h !== prev);
      if (h !== el.innerHTML) el.innerHTML = h;
    }
    // House style on every text node.
    const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      let t = n.nodeValue, o = t;
      t = t.replace(/\b([ap])\.m\.(?=\W|$)/g, '$1m');
      t = t.replace(/(\d)(?::(\d\d))? ?([ap]m) ?[-–] ?(\d{1,2}(?::\d\d)?) ?\3\b/g, (m, h, mm, ap, end) => `${h}${mm ? ':' + mm : ''}–${end} ${ap}`);
      t = t.replace(/(\d ?[ap]m) - (\d)/g, '$1–$2');
      t = t.replace(/\b(1[0-2]|0?[1-9])\/(\d{1,2})\/(20\d\d)\b/g, (m, mo, d) => `${MON[+mo - 1]} ${+d}`);
      t = t.replace(/opened about to open/g, 'opening soon');
      t = t.replace(/No reading yet today/g, "The inverter hasn't reported yet today");
      t = t.replace(/\b(Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.(?= \d)/g, '$1');
      if (t !== o) n.nodeValue = t;
    }
    // The same story told twice in one list keeps the first telling.
    const words = s => new Set(s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(w => w.length > 3));
    const alike = (a, b) => { if (!a.size || !b.size) return false; let k = 0; for (const w of a) if (b.has(w)) k++; return k / Math.min(a.size, b.size) >= 0.6; };
    for (const box of $$('#bignews, #localnews, #reviews, #gadgets, #tech, .scroll')) {
      const seen = [];
      for (const s of box.querySelectorAll('.story')) {
        const w = words(txt(s.querySelector('b')));
        if (seen.some(x => alike(x, w))) kill(s); else seen.push(w);
      }
    }
    // Portland news: sports results live in Sports.
    for (const s of $$('#localnews .story')) if (/Blazers|Timbers|Thorns|Winterhawks/.test(txt(s.querySelector('b')))) kill(s);
    // Holidays shared by two countries are one row.
    const hol = new Set();
    for (const r of $$('#holidays > div')) { const k = txt(r); if (hol.has(k)) kill(r); else hol.add(k); }
    // A small chart is not blown up to the full width (its labels would grow with it).
    for (const svg of $$('section.group svg[viewBox]')) {
      const vb = (svg.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number);
      if (vb.length === 4 && vb[2] > 60 && vb[2] < 420) { svg.style.setProperty('max-width', Math.round(vb[2] * 1.35) + 'px', 'important'); svg.style.setProperty('height', 'auto', 'important'); }
    }
    // Decorative icons (drawn with colour or emoji on the live page) print as empty frames.
    for (const el of $$('section.group [aria-hidden="true"]')) if (!txt(el) && !el.querySelector('img, svg') && el.tagName !== 'svg') el.remove();
    // Empty bordered boxes (icons and thumbnails that have nothing in them on e-ink).
    for (const el of $$('section.group div, section.group span, section.group i')) {
      if (el.children.length || txt(el) || el.closest('svg, .bars, .legend, .rain, .tile, .mini')) continue;
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
      if (r.width >= 16 && r.height >= 16 && (parseFloat(cs.borderTopWidth) > 0 || cs.backgroundImage !== 'none')) el.remove();
    }
  } catch (e) { console.log('kindle editor pass: ' + e); }

}
"""

# Runs in the rendered page: strip it down to static HTML and split it up.
EXTRACT = r"""
() => {
  const abs = u => { try { return new URL(u, location.href).href } catch (e) { return u } };
  for (const g of document.querySelectorAll('.facts, .tiles, .minis')) g.dataset.n = g.children.length;
  // A witty card title keeps its plain name as a kicker above it.
  for (const h of document.querySelectorAll('.card h2[data-base]')) {
    const base = (h.dataset.base || '').trim();
    if (base && base !== 'None' && base.toLowerCase() !== h.textContent.trim().toLowerCase() && !(h.closest('.card') || h.parentNode).querySelector('.kkick, .kkicker, .shelf-h, .eyebrow, .sci-topic, .joy-k, .kicker')) {
      const k = document.createElement('p'); k.className = 'kkick'; k.textContent = base; h.before(k);
    }
  }
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
    img.removeAttribute('srcset'); img.removeAttribute('loading');
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
  // The front page: the weather in figures, five things about the day, three lead stories.
  const front = {};
  const hw = document.querySelector('#hero-wx');
  if (hw) {
    const sm = hw.querySelector('small');
    front.where = t(sm);
    front.temp = t(hw).replace(front.where, '').trim();
  }
  front.date = t(document.querySelector('#stamp'));
  front.summary = t(document.querySelector('#out-summary'));
  const glance2 = [];
  const cal = document.querySelector('#cal .lines > div');
  const calRows = document.querySelector('#cal .lines');
  if (calRows) {
    const items = [...calRows.children].map(d => {
      const a = d.children[0], b = d.children[1];
      const name = (t(a).replace(t(a && a.querySelector('small')), '').trim());
      const when = b ? t(b) : '', m = /^(\d{1,2}(?::\d\d)?)(?:\s*[–-]\s*\d{1,2}(?::\d\d)?)?\s*([ap]m)/.exec(when);
      return name + (when ? ' ' + (m ? m[1] + ' ' + m[2] : when) : '');
    }).filter(Boolean);
    if (items.length) glance2.push(['Today', items.slice(0, 3).join(' · ')]);
  }
  const big = document.querySelector('#day-big');
  const bigT = big ? t(big).replace(/^Big in town:\s*/, '') : '';
  if (bigT && !(glance2[0] && glance2[0][1].includes(bigT.slice(0, 18)))) glance2.push(['In town', bigT]);
  const planRows = [...document.querySelectorAll('#plan > div')];
  const plan = planRows.find(r => /last chance|must|deadline|ends|by (mon|tue|wed|thu|fri|sat|sun)/i.test(t(r))) || planRows[0];
  if (plan) glance2.push(['Act soon', t(plan.querySelector('b') || plan)]);
  if (drv && t(drv)) glance2.push(['Drive', t(drv).replace(/^([A-Z][A-Z ]+?)\s+(\d+ min)\s*·\s*[\d.]+ mi\s*/, (m, w, mins) => `To ${w.toLowerCase()} ${mins}, `).replace(/,\s*Normal traffic/i, ', normal traffic')]);
  const aq = [...document.querySelectorAll('#out-facts .mini')].find(m => /air|aqi/i.test(t(m)));
  if (aq) glance2.push(['Air', t(aq).replace(/^Air( quality)?\s*/i, '')]);
  const leads = [];
  const rc = document.querySelector('section[data-sec=sports] .recap b');
  if (rc) leads.push([t(rc), 'sports', '']);
  const ln = document.querySelector('#localnews .story b');
  if (ln) leads.push([t(ln), 'news', 'localnews']);
  const bn = document.querySelector('#bignews .story b');
  if (bn) leads.push([t(bn), 'news', 'bignews']);
  const hm = t(document.querySelector('#brief')).match(/\b([A-Z][\w']+(?: [A-Z][\w']+)* Day) is today\b/);
  if (hm) front.holiday = hm[1];
  // Every card becomes its own page. Section wrappers are kept (shallow) so
  // the dashboard's own section-scoped styles still apply to each card.
  const groups = [...document.querySelectorAll('section.group')];
  const UNIT = '.card, .brief, .tiles, .alerts';
  const titleOf = (el, fallback) => {
    const h = el.querySelector('h2, h3, .sci-title');
    const t = (h ? h.textContent : '') || el.getAttribute('aria-label') || fallback;
    return t.replace(/\s+/g, ' ').trim();
  };
  const wrap = (g, inner) => {
    const outer = g.cloneNode(false), body = document.createElement('div');
    body.className = 'sec-body';
    body.innerHTML = inner;
    outer.appendChild(body);
    return outer.outerHTML;
  };
  const sections = groups.map(g => {
    const h = g.querySelector('.sec-h'), sub = g.querySelector('.sec-sub');
    const title = (g.dataset.ktitle || (h ? h.textContent : g.id)).replace(/\s+/g, ' ').trim();
    const body = g.querySelector('.sec-body') || g;
    const cards = [];
    let pending = '';
    const collect = node => {
      for (const ch of [...node.children]) {
        if (ch.classList.contains('sec-head')) continue;
        if (ch.matches(UNIT)) {
          const label = ch.matches('.tiles') ? (ch.getAttribute('aria-label') || 'Right now') : titleOf(ch, title);
          let unitHtml = pending + ch.outerHTML;
          const head = pending && ch.querySelector(':scope > .head');
          if (head) { const c = ch.cloneNode(true); c.querySelector(':scope > .head').insertAdjacentHTML('afterend', pending); unitHtml = c.outerHTML; }
          cards.push({ title: label, html: unitHtml }); pending = '';
        } else if (ch.querySelector(UNIT)) {
          collect(ch);
        } else if (ch.textContent.trim() || ch.querySelector('img, svg')) {
          if (ch.classList.contains('ksources') && cards.length) cards[cards.length - 1].html += ch.outerHTML;
          else pending += ch.outerHTML;
        }
      }
    };
    collect(body);
    if (pending) {
      if (cards.length) cards[cards.length - 1].html += pending;
      else cards.push({ title, html: pending });
    }
    return { id: g.dataset.sec || g.id, title,
             sub: g.dataset.ksub || (sub ? sub.textContent.trim() : ''),
             cards: cards.map(c => ({ title: c.title, html: wrap(g, c.html) })) };
  });
  // The greeting above the first section is Today's opening page.
  if (groups.length) {
    const top = groups[0];
    const range = document.createRange();
    range.setStart(document.querySelector('main') || document.body, 0);
    range.setEndBefore(top);
    const box = document.createElement('div');
    box.appendChild(range.cloneContents());
    if (box.textContent.trim() && sections.length) sections[0].cards.unshift({ title: 'Good morning', html: box.innerHTML });
  }
  const bodyClass = document.body.className, htmlClass = document.documentElement.className;
  return { css, links, sections, bodyClass, htmlClass, glance, glance2, front, leads };
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
.kseckick{display:flex;justify-content:space-between;align-items:baseline;margin:2px 0 14px !important;padding:0 0 8px;border-bottom:3px double #000;
  font:600 12px/1.3 var(--k-serif);letter-spacing:.16em;text-transform:uppercase}
.kseckick a{text-decoration:none !important}
.kseckick span{color:var(--k-grey);letter-spacing:.1em}
main .sec-body>.card,main .sec-body>.brief,main .sec-body>.tiles{border-top:0 !important;padding-top:0 !important;margin-top:0 !important}
main .card h2,main .brief h2{font-size:30px !important;line-height:1.15 !important;margin:4px 0 8px !important}
.ktoc .ksec{border-bottom:1px solid var(--k-hair);padding:4px 0 10px}
.ktoc .ksec>a{padding:10px 0 4px !important}
.ktoc .kcards{list-style:none;padding:0 0 0 2.2em !important;margin:0 !important;columns:1}
.ktoc .kcards li{margin:0 !important;border:0}
.ktoc .kcards a{display:block !important;font:400 16.5px/1.35 var(--k-serif);padding:5px 0 !important;color:#222 !important}

.kfoot .knext span{font-size:20px !important}

/* Undo the dashboard's fixed card heights, inner scrollers and two-line clamps */
main .sec-body{display:block !important}
main .card,main .sec-body>*{flex:none !important;height:auto !important;min-height:0 !important;max-height:none !important;overflow:visible !important}
main .scroll{max-height:none !important;overflow:visible !important;margin:0 !important;padding:0 !important;border-top:0 !important}
main .story p{display:block !important;-webkit-line-clamp:none !important;overflow:visible !important}
#coast-events,#kid-out{max-height:none !important;overflow:visible !important}
#fish-card .row{display:block !important}
/* ===== v3: the Paperwhite 11 page system (618 x ~714 CSS px, Chrome 75) ===== */
:root{--t1:44px;--l1:46px;--t2:30px;--l2:34px;--t3:22px;--l3:28px;--t4:18px;--l4:26px;--t5:15px;--l5:21px;--t6:13px;--l6:16px;
  --ink2:#3a3a3a;--hair:#8a8a8a;--k-grey:#3a3a3a;--k-hair:#8a8a8a;--m:24px;--s1:6px;--s2:13px;--s3:26px}
html body{padding:0 var(--m) !important;max-width:none !important;font:430 var(--t4)/var(--l4) var(--k-serif) !important;
  font-feature-settings:"kern","liga","pnum" !important;color:#000 !important}
#kmain *{color:#000;-webkit-text-fill-color:currentColor !important}
#kmain .scroll,#kmain .rain,#kmain .facts,#kmain .poem-long,#kmain .card,#kmain .sec-body,#kmain .group,#kmain .lines,#kmain ul,#kmain ol{
  max-height:none !important;overflow:visible !important}
#kmain .card,#kmain .sec-body,#kmain .group,#kmain .brief{margin-left:0 !important;margin-right:0 !important;padding-left:0 !important;padding-right:0 !important;
  border:0 !important;box-shadow:none !important;background:none !important}
#kmain .group{margin:0 !important;padding:0 !important}
#kmain .unclamp,#kmain .more-btn{display:none !important}
#kmain .clamped>*{display:block !important}

/* Running head: section (links to its front) and folio */
html body .krun{display:flex !important;justify-content:space-between;align-items:baseline;height:34px;box-sizing:border-box;padding:12px 0 5px !important;
  margin:0 0 16px !important;border:0 !important;border-bottom:1px solid #000 !important;
  font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em !important;text-transform:uppercase}
.krun a,.krun span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-decoration:none !important}
.krun span{font-variant-numeric:tabular-nums;padding-left:12px}
.kseckick{display:none !important}

/* Title zone */
#kmain .head,#kmain .brief-head,#kmain .card-head{display:block !important;margin:0 0 16px !important;padding:0 !important;border:0 !important}
#kmain .kkick,#kmain .shelf-h,#kmain .sci-topic{display:block !important;font:600 var(--t6)/var(--l6) var(--k-serif) !important;
  letter-spacing:.12em !important;text-transform:uppercase !important;margin:0 0 6px !important;padding:0 !important;border:0 !important}
#kmain h2,#kmain .sci-title,#kmain .kh2{display:block;font:700 var(--t2)/var(--l2) var(--k-serif) !important;letter-spacing:-.012em !important;
  margin:0 0 var(--s2) !important;padding:0 !important;border:0 !important;text-transform:none !important}
#kmain .card>.head h2,#kmain .brief-head h2{margin:0 !important}
#kmain .card .head .meta,#kmain .brief-intro{display:block !important;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;
  color:var(--ink2) !important;margin:6px 0 0 !important}

/* Body defaults */
#kmain p,#kmain .summary,#kmain .note{font:430 var(--t4)/var(--l4) var(--k-serif) !important;margin:0 0 var(--s2) !important}
#kmain small,#kmain .cite,#kmain .src-line,#kmain figcaption,#kmain .muted{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;color:var(--ink2) !important}
#kmain h3,#kmain .day-h,#kmain .cal-day,#kmain details>summary{display:block;font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em !important;
  text-transform:uppercase !important;border:0 !important;border-top:1px solid #000 !important;padding:7px 0 0 !important;margin:var(--s3) 0 var(--s1) !important;background:none !important}
#kmain .card>.head+h3,#kmain .head+.cal-day,#kmain h2+h3,#kmain .head+*>h3:first-child,#kmain .head+*>.day-h:first-child,#kmain .head+*>*:first-child>h3:first-child{margin-top:0 !important}
#kmain .pill,#kmain .tag,#kmain .badge{font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.1em !important;color:var(--ink2) !important;
  background:none !important;border:0 !important;padding:0 !important;text-transform:uppercase}
#kmain .rt4{font:700 var(--t6)/var(--l6) var(--k-serif) !important;font-variant:normal !important;letter-spacing:.1em;text-transform:uppercase}
#kmain .rt3{font:600 var(--t6)/var(--l6) var(--k-serif) !important;font-variant:normal !important;letter-spacing:.1em;text-transform:uppercase}
#kmain .rt2{font:430 var(--t6)/var(--l6) var(--k-serif) !important;font-variant:normal !important;letter-spacing:.1em;text-transform:uppercase}
#kmain .rt1{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;font-variant:normal !important;color:var(--ink2) !important}
#kmain .ksources{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;color:var(--ink2) !important;border:0 !important;
  border-top:1px solid var(--hair) !important;padding:var(--s1) 0 0 !important;margin:var(--s3) 0 0 !important}
#kmain .ksources *{font:inherit !important}
#kmain a{text-decoration-thickness:1px}
#kmain img{max-width:100% !important;height:auto}

/* Lists of stories */
#kmain .story,#kmain .lines>div{padding:10px 0 !important;margin:0 !important;border:0 !important;border-bottom:1px solid var(--hair) !important;
  font:430 var(--t4)/var(--l4) var(--k-serif) !important;background:none !important}
#kmain .story.headline{font-weight:430 !important}
#kmain .story b,#kmain .lines>div>span:first-child>b,#kmain .lines>div>span:first-child>a>b{font:680 var(--t4)/var(--l4) var(--k-serif) !important}
#kmain .story p,#kmain .story .sum{display:block;font:430 var(--t5)/var(--l5) var(--k-serif) !important;margin:3px 0 0 !important}
#kmain .story small{display:block;margin-top:3px}
#kmain .story img,#kmain .poster{float:right;width:72px !important;height:72px !important;object-fit:cover;margin:4px 0 6px 14px !important}
#kmain .lines>div{display:flex !important;justify-content:space-between;align-items:baseline}
#kmain .lines>div>span:first-child{-webkit-box-flex:1;flex:1 1 auto;min-width:0}
#kmain .lines>div>span:last-child:not(:first-child){flex:none;max-width:170px;white-space:normal !important;overflow:visible !important;padding-left:14px;text-align:right;
  font:430 var(--t5)/var(--l5) var(--k-serif) !important;font-variant-numeric:tabular-nums}
#kmain .lines>div>span:first-child>small{display:block}

/* Alfred */
#kmain .brief-top{list-style:none !important;padding:0 !important;margin:0 0 var(--s2) !important;counter-reset:b}
#kmain .brief-top>li{position:relative;padding:0 0 0 34px !important;margin:0 0 var(--s2) !important;counter-increment:b;
  font:430 var(--t4)/var(--l4) var(--k-serif) !important;border:0 !important;list-style:none !important}
#kmain .brief-top>li::before{content:counter(b);position:absolute;left:0;top:-1px;font:680 var(--t3)/var(--l3) var(--k-serif)}
#kmain .brief-top>li::marker{content:''}
#kmain .brief li>a{text-decoration:none !important}
#kmain .brief-rest{list-style:none !important;padding:0 !important;margin:0 0 var(--s2) !important}
#kmain .brief-rest>li{font:430 var(--t5)/var(--l5) var(--k-serif) !important;padding:7px 0 !important;margin:0 !important;border:0 !important;
  border-bottom:1px solid var(--hair) !important;list-style:none !important}
#kmain .brief-rest .aside{display:block;font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;font-style:normal !important}

/* Figures */
#kmain .tiles,#kmain .facts,#kmain .minis{display:grid !important;grid-template-columns:1fr 1fr !important;grid-gap:0 !important;
  border:0 !important;border-top:1px solid #000 !important;margin:var(--s2) 0 var(--s3) !important;padding:0 !important;text-align:left !important;background:none !important}
#kmain .tiles>.tile,#kmain .facts>.mini,#kmain .minis>.mini{display:block !important;margin:0 !important;border:0 !important;border-radius:0 !important;background:none !important;
  border-bottom:1px solid var(--hair) !important;padding:10px 12px 12px 0 !important;text-align:left !important;min-height:0 !important}
#kmain .tiles>.tile:nth-child(even),#kmain .facts>.mini:nth-child(even),#kmain .minis>.mini:nth-child(even){border-left:1px solid var(--hair) !important;padding-left:14px !important}
#kmain .tiles>.tile:last-child:nth-child(odd),#kmain .facts>.mini:last-child:nth-child(odd),#kmain .minis>.mini:last-child:nth-child(odd){grid-column:1 / -1}
#kmain .facts[data-n="5"],#kmain .facts[data-n="6"],#kmain .facts[data-n="9"],#kmain .minis[data-n="6"]{grid-template-columns:1fr 1fr 1fr !important}
#kmain .facts[data-n="5"]>.mini,#kmain .facts[data-n="6"]>.mini,#kmain .facts[data-n="9"]>.mini,#kmain .minis[data-n="6"]>.mini{border-left:0 !important;padding-left:0 !important;grid-column:auto}
#kmain .facts[data-n="5"]>.mini:not(:nth-child(3n+1)),#kmain .facts[data-n="6"]>.mini:not(:nth-child(3n+1)),#kmain .facts[data-n="9"]>.mini:not(:nth-child(3n+1)),
#kmain .minis[data-n="6"]>.mini:not(:nth-child(3n+1)){border-left:1px solid var(--hair) !important;padding-left:12px !important}
#kmain .facts[data-n="5"]>.mini:nth-child(5){grid-column:2 / span 2}
#kmain .tile .k,#kmain .mini .k,#kmain .mini>span:first-child{display:block;font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em !important;
  text-transform:uppercase !important;color:var(--ink2) !important;margin:0 0 4px !important}
#kmain .tile .big{display:block;font:700 var(--t1)/var(--l1) var(--k-serif) !important;font-variant-numeric:tabular-nums}
#kmain .tiles[data-n="5"] .tile .big,#kmain .tiles[data-n="6"] .tile .big{font-size:var(--t2) !important;line-height:var(--l2) !important}
#kmain .mini .v{display:block;font:650 var(--t3)/var(--l3) var(--k-serif) !important;font-variant-numeric:tabular-nums}
#kmain .tile .u,#kmain .mini .v small{font:430 var(--t5)/var(--l5) var(--k-serif) !important;color:var(--ink2) !important}
#kmain .tile .s,#kmain .mini .s{display:block;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;margin-top:2px}

/* Charts: e-ink solids */
#kmain .bars{border-bottom:1px solid #000 !important}
#kmain .bars i,#kmain .legend .sw,#kmain .rain-bars i{background:#4d4d4d !important;border-radius:0 !important}
#kmain .bars .ly,#kmain #ly-legend i{background:#000 !important}
#kmain .rain{background:none !important;border:0 !important;border-top:1px solid #000 !important;padding:var(--s2) 0 0 !important;border-radius:0 !important;height:auto !important}
#kmain .rain-drop{display:none !important}

/* Tables: forecast and similar day rows */
#kmain .fc,#kmain .sdays{border:0 !important;border-top:1px solid #000 !important;margin:var(--s1) 0 var(--s2) !important;padding:0 !important}
#kmain .fd,#kmain .sday{border:0 !important;border-bottom:1px solid var(--hair) !important;font:430 var(--t5)/var(--l5) var(--k-serif) !important;padding:7px 0 !important;background:none !important}
#kmain .fd .d,#kmain .sday .d{font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.1em;text-transform:uppercase}
#kmain .fd .t{font:650 var(--t3)/var(--l3) var(--k-serif) !important;font-variant-numeric:tabular-nums;white-space:nowrap}
#kmain .vote{font:700 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.1em;text-transform:uppercase;padding:1px 6px !important;
  border:1px solid #000 !important;background:none !important;border-radius:0 !important}
#kmain .vote.v-nay,#kmain .vote.nay{background:#000 !important;color:#fff !important;-webkit-text-fill-color:#fff !important}

/* Story pages */
#kmain .sci{display:block;text-decoration:none !important}
#kmain .sci-means{display:block;font:430 var(--t4)/var(--l4) var(--k-serif) !important;margin:var(--s2) 0 !important}
#kmain .sci-means i{display:block !important;font:600 var(--t6)/var(--l6) var(--k-serif) !important;font-style:normal !important;letter-spacing:.12em !important;
  text-transform:uppercase !important;margin:0 0 4px}
#kmain .sci-means i::after{content:none !important}
#kmain .sci>small{display:block;font:600 var(--t6)/var(--l6) var(--k-serif) !important;font-style:normal !important;letter-spacing:.12em;text-transform:uppercase}
#kmain .sci img,#kmain .sci-img{display:block;width:100% !important;max-height:260px;object-fit:cover;margin:var(--s2) 0 var(--s1) !important;float:none !important}

/* Features */
#kmain .poem-title{display:block;font:700 var(--t2)/var(--l2) var(--k-serif) !important;margin:0 0 4px !important}
#kmain .poem-by{display:block;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;margin:0 0 var(--s2) !important}
#kmain .poem-text{font:430 var(--t4)/var(--l4) var(--k-serif) !important}
#kmain .poem-text span{display:block;padding-left:1.5em !important;text-indent:-1.5em !important}
#kmain .poem-text .gap{height:13px}
#kmain .potd-img img,#kmain .look img,#kmain .then img{display:block;width:100% !important;max-height:420px;object-fit:contain;margin:0 0 var(--s2) !important}
#kmain .potd-title{display:block;font:650 var(--t3)/var(--l3) var(--k-serif) !important}
#kmain .look-weather{border:0 !important;padding:0 !important;background:none !important;font:italic 430 var(--t4)/var(--l4) var(--k-serif) !important}
#kmain .look-cols{display:grid !important;grid-template-columns:1fr 1fr;grid-column-gap:24px}
#kmain .look-col li{font:430 var(--t5)/var(--l5) var(--k-serif) !important;border:0 !important;padding:0 !important;margin:0 0 var(--s1) !important}

/* Sports */
#kmain .kscore{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #000;border-bottom:1px solid #000;margin:0 0 var(--s3)}
#kmain .kscore>div{padding:10px 12px 10px 0}
#kmain .kscore>div+div{border-left:1px solid var(--hair);padding-left:14px}
#kmain .kscore b{display:block;font:680 var(--t3)/var(--l3) var(--k-serif) !important}
#kmain .recap{border:0 !important;padding:0 !important;margin:0 0 var(--s2) !important;background:none !important}

/* Front page (Good morning) */
#kmain .kfrontwx{display:flex;align-items:flex-start;border-bottom:1px solid #000;padding:0 0 var(--s2);margin:0 0 var(--s2)}
#kmain .kfrontwx .kdeg{flex:none;width:150px;font:700 64px/1 var(--k-serif);letter-spacing:-.02em;font-variant-numeric:tabular-nums}
#kmain .kfrontwx .kdeg small{display:block;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;letter-spacing:0;margin-top:6px}
#kmain .kfrontwx .ksum{-webkit-box-flex:1;flex:1 1 auto;min-width:0;font:430 var(--t4)/var(--l4) var(--k-serif)}
#kmain #today-card>.head{display:none !important}
#kmain #today-card #out-summary{display:none !important}
#kmain #day-events>span{display:block;font:430 var(--t5)/var(--l5) var(--k-serif) !important;margin:0 0 var(--s1)}
#kmain #day-events b{font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;margin-right:6px}
#kmain #out-facts>.mini{display:flex !important;justify-content:space-between;align-items:baseline;padding:8px 12px 6px 0 !important;grid-column:auto !important}
#kmain #out-facts>.mini:nth-child(even){padding-left:14px !important}
#kmain #out-facts .k{margin:0 !important}
#kmain #out-facts .v{font:680 var(--t4)/var(--l4) var(--k-serif) !important;white-space:nowrap;text-align:right}
#kmain #out-facts .v small{display:none !important}
#kmain .allclear{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;border:0 !important;border-top:1px solid var(--hair) !important;padding:var(--s1) 0 0 !important;background:none !important}
#kmain .allclear i{display:none !important}

/* Chrome 75 has no flex gap: spacing is margins, so the preview matches the Kindle */
#kmain .group,#kmain .card,#kmain .rep,#kmain .shade-day,#kmain .mini,#kmain #longread,#kmain .rep-head,#kmain .elect-next,#kmain .drum,
#kmain .shade-step,#kmain a.story,#kmain a.sp,#kmain .allclear,#kmain .legend,#kmain .legend>span,#kmain .bars,#kmain .bars>div{gap:0 !important}
#kmain .card>*+*{margin-top:12px}
#kmain .rep>*+*,#kmain .shade-day>*+*{margin-top:8px}
#kmain .rep-head>*+*,#kmain .elect-next>*+*,#kmain .drum>*+*,#kmain .shade-step>*+*,#kmain a.story>*+*,#kmain a.sp>*+*,#kmain .legend>*+*{margin-left:10px}
#kmain .legend>span>*+*{margin-left:6px}
#kmain .bars>*+*{margin-left:3px}
#kmain .bars>div>*+*{margin-left:1px}
/* Lists in two columns and empty decorations */
#kmain .look-col li{padding-left:0 !important;list-style:none !important}
#kmain .look-col li::before{display:none !important}
#kmain .look-col{border-top:0 !important}
#kmain .drum-ic,#kmain .cake,#kmain #albums a.story::before,#kmain #albums .story::before{display:none !important}
#kmain .lines>div>span:last-child{white-space:normal !important}
#kmain .lines>div>span:only-child{padding-left:0 !important;max-width:none !important;text-align:left !important}
#kmain svg{overflow:visible}

/* Bottom bar: one 52px row */
.kbar{display:none}
html.kpaged,html.kpaged body{height:100% !important;overflow:hidden !important;overscroll-behavior:none;touch-action:none;-webkit-tap-highlight-color:rgba(0,0,0,0)}
html.kpaged body{display:flex !important;flex-direction:column !important;padding-bottom:0 !important}
html.kpaged .krun{flex:none}
html.kpaged #kview{flex:none;position:relative;overflow:hidden}
html.kpaged #kclip{position:relative;overflow:hidden}
html.kpaged #kmain{position:relative;top:0}
html.kpaged .kfoot{display:none}
html.kpaged .kbar{flex:none;display:flex;align-items:center;height:52px;box-sizing:border-box;padding:0 !important;margin:0 !important;border-top:1px solid #000;
  font:600 var(--t6)/var(--l6) var(--k-serif);letter-spacing:.1em;text-transform:uppercase}
.kbar a{text-decoration:none !important}
.kbar .kprev,.kbar .knx{-webkit-box-flex:1;flex:1 1 0;min-width:0;padding:18px 0 !important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kbar .knx{text-align:right}
.kbar .kmid{flex:none;display:block;text-align:center;padding:0 10px}
.kbar #kmore{display:inline-block;border:1px solid #000;height:34px;box-sizing:border-box;padding:8px 14px !important;line-height:16px;white-space:nowrap}
.kbar #kmore .kfol{font-variant-numeric:tabular-nums;margin-left:6px}
.kbar #kpos{font-variant-numeric:tabular-nums}
#kcont{display:none;font:italic 430 var(--t5)/var(--l5) var(--k-serif);padding:0 0 8px;margin:0 0 13px;border-bottom:1px solid var(--hair);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#kcont b{font-style:normal;font-weight:680}

/* Related rail on short pages */
#krail{display:none;margin-top:var(--s3);border-top:1px solid #000;padding-top:7px}
#krail h4{font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;margin:0 0 var(--s1) !important;border:0 !important;padding:0 !important}
#krail a{display:block;padding:7px 0;border-bottom:1px solid var(--hair);text-decoration:none !important}
#krail b{display:block;font:680 var(--t4)/var(--l4) var(--k-serif) !important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* Fit ladder: tighter leading, then type, then two-column short lists */
html.kfit1{--l4:24px;--l5:20px;--s2:10px;--s3:18px}
html.kfit2{--t2:28px;--l2:32px;--t4:17px;--l4:23px;--t3:20px;--l3:25px}
html.kfit3 #kmain .brief-rest,html.kfit3 #kmain ul.note,html.kfit3 #kmain .look-cols ul{-webkit-columns:2;columns:2;-webkit-column-gap:24px;column-gap:24px}
html.kfit3 #kmain .facts[data-n="4"],html.kfit3 #kmain .facts[data-n="8"]{grid-template-columns:1fr 1fr 1fr 1fr !important}

/* Cover */
.kcontents #kmain .kmast{text-align:center;padding:10px 0 0;margin:0}
.kcontents #kmain .kname{font:700 var(--t1)/var(--l1) var(--k-serif) !important;letter-spacing:-.015em;margin:0 0 var(--s2) !important}
.kcontents #kmain .kdate{font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;
  border-top:3px double #000;border-bottom:1px solid #000;padding:9px 0 !important;margin:0 0 var(--s3) !important}
.kcontents #kmain .kgl{display:flex;align-items:flex-start;border-bottom:1px solid #000;padding:0 0 var(--s2);margin:0 0 var(--s3)}
.kcontents #kmain .kgl .kdeg{flex:none;width:170px;font:700 64px/1 var(--k-serif);letter-spacing:-.02em}
.kcontents #kmain .kgl .kdeg small{display:block;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;letter-spacing:0;margin-top:8px;color:#000 !important}
.kcontents #kmain .kgl ul{-webkit-box-flex:1;flex:1 1 auto;min-width:0;list-style:none;margin:0 !important;padding:0 !important}
.kcontents #kmain .kgl li{font:430 var(--t5)/var(--l5) var(--k-serif);padding:5px 0 !important;margin:0 !important;border-bottom:1px solid var(--hair)}
.kcontents #kmain .kgl li:last-child{border-bottom:0}
.kcontents #kmain .kgl li b{display:inline;margin-right:8px;font:600 var(--t6)/var(--l6) var(--k-serif);letter-spacing:.12em;text-transform:uppercase}
.kcontents #kmain .klab{font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;
  border-top:1px solid #000;padding:7px 0 0 !important;margin:0 0 var(--s1) !important}
.kcontents #kmain .kleads a{display:block;padding:8px 0;border-bottom:1px solid var(--hair);text-decoration:none !important}
.kcontents #kmain .kleads b{display:block;font:680 var(--t4)/var(--l4) var(--k-serif)}
.kcontents #kmain .kleads small{display:block;font:600 var(--t6)/var(--l6) var(--k-serif) !important;font-style:normal !important;letter-spacing:.12em;text-transform:uppercase;color:var(--ink2) !important}
.kcontents #kmain .khint{text-align:center;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;margin:var(--s3) 0 0 !important;color:var(--ink2) !important}
/* Contents */
.kcontents #kmain .ktochead{font:700 var(--t2)/var(--l2) var(--k-serif) !important;margin:0 0 var(--s2) !important;padding:0 !important}
.kcontents #kmain .kpart{font:600 var(--t6)/var(--l6) var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;
  border-top:1px solid #000;padding:5px 0 0 !important;margin:6px 0 0 !important}
.kcontents #kmain .kpartbox{display:grid;grid-template-columns:1fr 1fr;grid-column-gap:24px;margin:0;padding:0;list-style:none}
.kcontents #kmain .kpartbox a{display:flex;align-items:baseline;padding:4px 0 3px !important;border-bottom:1px solid var(--hair);text-decoration:none !important}
.kcontents #kmain .kn{flex:none;width:28px;font:600 var(--t6)/1 var(--k-serif);font-variant-numeric:tabular-nums}
.kcontents #kmain .kt{-webkit-box-flex:1;flex:1 1 auto;min-width:0;font:680 var(--t4)/1.2 var(--k-serif);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kcontents #kmain .kc{flex:none;padding-left:6px;font:italic 430 var(--t5)/1 var(--k-serif);color:var(--ink2) !important}
.kcontents .krun{display:none !important}
/* Section fronts */
.ksecfront #kmain .kkick{margin:var(--s2) 0 6px !important}
.ksecfront #kmain .kfname{font:700 var(--t1)/var(--l1) var(--k-serif) !important;letter-spacing:-.015em;margin:0 !important}
.ksecfront #kmain .kfsub{font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important;margin:6px 0 0 !important;padding:0 0 var(--s2) !important;border-bottom:3px double #000}
.ksecfront #kmain .kfl{list-style:none;margin:0 !important;padding:0 !important}
.ksecfront #kmain .kfl a{display:flex;align-items:baseline;padding:9px 0 !important;border-bottom:1px solid var(--hair);text-decoration:none !important}
.ksecfront #kmain .kfl .kn{flex:none;width:34px;font:600 var(--t6)/var(--l6) var(--k-serif);font-variant-numeric:tabular-nums}
.ksecfront #kmain .kfl .kt{-webkit-box-flex:1;flex:1 1 auto;min-width:0}
.ksecfront #kmain .kfl .kt b{display:block;font:680 var(--t4)/var(--l4) var(--k-serif);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ksecfront #kmain .kfl .kt small{display:block}
.ksecfront #kmain .kfl.kcompact a{padding:7px 0 !important}
.ksecfront #kmain .kfl.kcompact small{display:none !important}
.ksecfront #kmain .kfl .kc{flex:none;padding-left:8px;font:italic 430 var(--t5)/var(--l5) var(--k-serif);color:var(--ink2)}
"""

# Tap the right two thirds of the screen to go forward a screen, the left
# third to go back. Taps on links still follow the link. Old-browser safe.
PAGER_JS = r"""
<script>
/* The Morning Edition pager, written for the Paperwhite 11 browser (Chrome 75, ES5).
   No scrolling: each card is cut into screen-sized sheets at whole-item
   boundaries and shown one sheet at a time.
   Right tap: next page (or, after "More", the next sheet of this card).
   Left tap: back. If anything here fails the page is left as a plain page. */
(function(){
  var NEXT_URL = __NEXT__, PREV_URL = __PREV__;
  var FLOW = /\b(kcontents|ksecfront)\b/.test(document.body.className);
  var root = document.documentElement, kview = document.getElementById('kview');
  var view = document.getElementById('kclip'), main = document.getElementById('kmain');
  var more = document.getElementById('kmore'), pos = document.getElementById('kpos');
  var kcont = document.getElementById('kcont'), rail = document.getElementById('krail');
  var run = document.querySelector('.krun'), bar = document.querySelector('.kbar'), st = root.style;
  if (!view || !main || !kview || !bar || !window.getComputedStyle || !('flexBasis' in st || 'webkitFlexBasis' in st)) return;
  var cuts = [0], tops = [0], heads = [], brk = [], sheet = 0, H = 0, C = 0, turns = 0, timer = 0, FLASH_EVERY = 6, hashDone = false;
  var UNITS = '.sp,.bday,.deal,.mush,.rep-head,.story,.lines>div,li,.fd,.sday,.brk,.rec,.idea,.book,.book-today,.rep,.recap,.mini,.tile,.tiles,.facts,figure,img,svg,.bars,.rain,.vote,.poem-text>span,h3,.sub,.day-h,.cal-day,.kscore,table,tr,.allclear,.krail';
  var TITLE = (function(){ var h = main.querySelector('h2,.sci-title,.poem-title'); return h ? (h.textContent || '').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '') : document.title; })();
  function on() { return (' ' + root.className + ' ').indexOf(' kpaged ') >= 0; }
  function cls(name, v) { root.className = root.className.replace(new RegExp('(^|\\s)' + name + '(?=\\s|$)', 'g'), '') + (v ? ' ' + name : ''); }
  function blockish(el) { var d = window.getComputedStyle(el).display; return d !== 'inline' && d !== 'none' && d !== 'contents'; }
  function txt(el) { return (el.textContent || '').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, ''); }
  function boxes() {
    var all = main.getElementsByTagName('*'), ls = [], us = [], hs = [], lb = 0, base = main.getBoundingClientRect().top;
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (!blockish(el)) continue;
      var r = el.getBoundingClientRect();
      if (r.height <= 0) continue;
      var top = r.top - base, bottom = r.bottom - base, tag = el.tagName.toUpperCase();
      var isHead = /^(H3|H4|SUMMARY)$/.test(tag) || /\b(cal-day|day-h|sub|shelf-h|rep-head)\b/.test(el.className || '');
      if (isHead) hs.push({ top: top, text: txt(/rep-head/.test(el.className) ? (el.querySelector('b,strong,a') || el) : el) });
      if (el.matches ? el.matches(UNITS) : (el.webkitMatchesSelector && el.webkitMatchesSelector(UNITS))) {
        us.push({ top: top, bottom: bottom }); ls.push({ top: top, bottom: bottom, head: isHead });   // a whole item is a good place to turn
      }
      var kids = el.children, hasBlock = false;
      for (var j = 0; j < kids.length; j++) if (blockish(kids[j])) { hasBlock = true; break; }
      for (var n = el.firstChild; n; n = n.nextSibling)
        if ((n.nodeType === 3 && /\S/.test(n.nodeValue)) || (n.nodeType === 1 && !blockish(n) && /\S/.test(n.textContent || ''))) { if (bottom > lb) lb = bottom; break; }
      if (hasBlock && !/^(LI|P|H1|H2|H3|H4|TR|FIGURE|IMG|SVG)$/.test(tag)) continue;
      if (bottom > lb) lb = bottom;
      ls.push({ top: top, bottom: bottom, head: isHead || tag === 'H2' });
      // A long paragraph may turn between its lines.
      if (tag === 'P' && r.height > H * 0.3 && document.createRange) {
        var rg = document.createRange(); rg.selectNodeContents(el);
        var lr = rg.getClientRects(), seen = {};
        for (var m = 0; m < lr.length; m++) { var lbt = Math.round(lr[m].bottom - base);
          if (!seen[lbt] && lbt < bottom - 2) { seen[lbt] = 1; ls.push({ top: top, bottom: lbt, head: false }); } }
      }
    }
    return { ls: ls, us: us, hs: hs, lb: lb };
  }
  function outer(el) { if (!el) return 0; var c = getComputedStyle(el); return el.offsetHeight + (parseFloat(c.marginTop) || 0) + (parseFloat(c.marginBottom) || 0); }
  // #kclip is never zoomed, so its box is the drawn height under old and new zoom alike.
  function drawn() { view.style.height = ''; return view.getBoundingClientRect().height; }
  function unscroll() { view.scrollTop = 0; kview.scrollTop = 0; document.body.scrollTop = 0; root.scrollTop = 0;
    if (window.pageYOffset || window.pageXOffset) window.scrollTo(0, 0); }
  // Design to fit: tighten leading, then type, then set short lists in two
  // columns. Only if none of that fits is the card paged at full size.
  var LADDER = ['', 'kfit1', 'kfit1 kfit2', 'kfit1 kfit2 kfit3'];
  function fit() {
    cls('kfit1', false); cls('kfit2', false); cls('kfit3', false); main.style.zoom = '';
    if (rail) rail.style.display = 'none';
    if (FLOW) return;
    var h0 = drawn();
    if (h0 <= H) {
      if (rail && h0 < H * 0.6) { rail.style.display = 'block'; if (drawn() > H) rail.style.display = 'none'; }
      return;
    }
    if (h0 > H * 1.6) return;                 // clearly a long read: page it at full size
    for (var i = 1; i < LADDER.length; i++) {
      var p = LADDER[i].split(' ');
      for (var k = 0; k < p.length; k++) cls(p[k], true);
      if (drawn() <= H) return;
    }
    cls('kfit1', false); cls('kfit2', false); cls('kfit3', false);
    main.style.zoom = '0.95';
    if (drawn() <= H) return;
    main.style.zoom = '';
  }
  function splits(u, c) { for (var i = 0; i < u.length; i++) { var x = u[i];
    if (x.top < c - 1 && x.bottom > c + 1 && x.bottom - x.top < H * 0.6) return true; } return false; }
  function plan() {
    var total = drawn(), start = 0, guard = 0, mtop = main.getBoundingClientRect().top;
    var c = [0], t = [0];
    var b = boxes(), ls = b.ls, us = b.us;
    heads = b.hs; brk = [];
    var bs = main.querySelectorAll('.kbreak');
    for (var q = 0; q < bs.length; q++) brk.push(bs[q].getBoundingClientRect().top - mtop);
    if (b.lb > 0) total = b.lb + 14;                       // what is printed, not boxes that overflow or trail          // trailing margins are not a sheet
    while (start + (c.length === 1 ? H : H - C) < total - 2 && guard++ < 80) {
      var limit = start + (c.length === 1 ? H : H - C), cut = start, any = start, lastHead = null, anyHead = null;
      for (var i = 0; i < ls.length; i++) { var l = ls[i];
        if (l.top >= start - 1 && l.bottom <= limit && l.bottom > start + 1) {
          if (l.bottom > any) { any = l.bottom; anyHead = l.head ? l.top : null; }
          if (l.bottom > cut && !splits(us, l.bottom)) { cut = l.bottom; lastHead = l.head ? l.top : null; }
        } }
      if (cut <= start + 40 || (cut - start < 0.6 * (limit - start) && any - cut > 0.25 * (limit - start))) { cut = any; lastHead = anyHead; }  // never leave half a screen empty
      if (lastHead !== null && lastHead > start + 40) cut = lastHead;    // never leave a heading at the foot
      for (var hh = 0; hh < heads.length; hh++) { var hd = heads[hh];
        if (hd.top > start + 40 && hd.top < cut && cut - hd.top < 90 && cut < total - 20) { cut = hd.top; break; } }
      if (cut <= start + 40) cut = limit;                                // one block taller than the screen
      for (var z = 0; z < brk.length; z++) if (brk[z] > start + 40 && brk[z] < cut) { cut = brk[z]; break; }
      // The next sheet starts at the next thing printed, not at a margin.
      var nt = total;
      for (var k = 0; k < ls.length; k++) if (ls[k].top >= cut - 1 && ls[k].top < nt) nt = ls[k].top;
      if (nt > cut + 80 || nt >= total) nt = cut;
      c.push(cut); t.push(nt); start = nt;
    }
    c.push(Math.max(total, start + 1));
    return { cuts: c, tops: t, last: Math.max(total, start + 1) - start };
  }
  function layout() {
    try {
      cls('kpaged', true);
      main.style.top = '0px'; unscroll();
      if (kcont && !FLOW) { kcont.innerHTML = '<b>' + TITLE.replace(/</g, '&lt;') + '</b> (continued)'; kcont.style.display = 'block'; C = outer(kcont); kcont.style.display = 'none'; }
      H = Math.max(240, window.innerHeight - outer(run) - outer(bar));
      kview.style.height = H + 'px';
      fit();
      var pl = { cuts: [0, drawn()], tops: [0], last: 0 };
      if (!main.style.zoom && !root.className.match(/kfit1/)) {
        pl = plan();
        // A last screen with a line or two on it: set the card a little tighter instead.
        if (!FLOW && pl.cuts.length > 2 && pl.last < H * 0.2) {
          var tries = [['kfit1'], ['kfit1', 'kfit2']];
          for (var w = 0; w < tries.length; w++) {
            for (var y = 0; y < tries[w].length; y++) cls(tries[w][y], true);
            var p2 = plan();
            if (p2.cuts.length < pl.cuts.length) { pl = p2; break; }
            cls('kfit1', false); cls('kfit2', false);
          }
        }
      }
      cuts = pl.cuts; tops = pl.tops;
      show(Math.min(sheet, cuts.length - 2));
      if (!hashDone && location.hash) { hashDone = true; toHash(); }
    } catch (err) {
      cls('kpaged', false); main.style.zoom = ''; main.style.top = ''; view.style.height = ''; kview.style.height = '';
    }
  }
  function toHash() {
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!el || !main.contains(el)) return;
    var y = el.getBoundingClientRect().top - main.getBoundingClientRect().top;
    for (var i = 0; i < cuts.length - 1; i++) if (y < cuts[i + 1] - 1) { show(i); return; }
  }
  function show(i) {
    sheet = i;
    var top = tops[i], end = cuts[i + 1], n = cuts.length - 1, h = i ? H - C : H;
    if (kcont) {
      if (i > 0 && !FLOW) {
        var sub = '';
        for (var k = 0; k < heads.length; k++) if (heads[k].top < top - 2 && heads[k].text) sub = heads[k].text;
        kcont.innerHTML = '<b>' + TITLE.replace(/</g, '&lt;') + '</b> (continued)' + (sub ? ' &middot; ' + sub.replace(/</g, '&lt;') : '');
        kcont.style.display = 'block';
      } else kcont.style.display = 'none';
    }
    main.style.top = (-top) + 'px';
    view.style.height = Math.min(h, end - top) + 'px';
    unscroll();
    if (more) {
      more.style.display = (i < n - 1) ? '' : 'none';
      more.innerHTML = 'More &darr; <span class="kfol">' + (i + 1) + '/' + n + '</span>';
    }
    if (pos) pos.innerHTML = (n > 1 && i === n - 1) ? n + '/' + n : '';
  }
  function turn(i) {                            // in-page turns are partial e-ink updates: flash now and then
    if (++turns % FLASH_EVERY) { show(i); return; }
    var f = document.createElement('div');
    f.style.cssText = 'position:fixed;left:0;top:0;width:100%;height:100%;background:#000;z-index:2147483647';
    document.body.appendChild(f);
    setTimeout(function(){ show(i); document.body.removeChild(f); }, 250);
  }
  function go(url) { if (url) location.href = url; }
  function forward(fromMore) { var n = cuts.length - 1;
    if ((fromMore || FLOW || sheet > 0) && sheet < n - 1) turn(sheet + 1); else go(NEXT_URL); }
  function back() { if (sheet > 0) turn(sheet - 1); else go(PREV_URL); }
  function later() { clearTimeout(timer); timer = setTimeout(layout, 60); }
  if (more) more.onclick = function(e){ e.preventDefault(); e.stopPropagation(); if (on()) forward(true); };
  document.addEventListener('click', function(e){
    if (!on()) return;
    for (var t = e.target; t && t !== document.body; t = t.parentNode) {
      var n = (t.nodeName || '').toUpperCase();
      if ((n === 'A' && t.getAttribute('href')) || t === more || /^(SUMMARY|BUTTON|INPUT|LABEL|SELECT|TEXTAREA)$/.test(n)) return;
    }
    e.preventDefault();
    if (e.clientX < window.innerWidth / 3) back(); else forward(false);
  }, false);
  document.addEventListener('touchmove', function(e){ if (on()) e.preventDefault(); }, { passive: false });
  document.addEventListener('scroll', function(){ if (on()) unscroll(); }, true);
  document.addEventListener('toggle', later, true);
  document.addEventListener('keydown', function(e){
    if (e.keyCode === 34 || e.keyCode === 39 || e.keyCode === 32) { e.preventDefault(); forward(false); }
    if (e.keyCode === 33 || e.keyCode === 37) { e.preventDefault(); back(); }
  }, false);
  window.addEventListener('resize', later, false);
  window.addEventListener('load', later, false);
  if (document.fonts) {
    if (document.fonts.ready) document.fonts.ready.then(later);
    if (document.fonts.addEventListener) document.fonts.addEventListener('loadingdone', later);
  }
  var imgs = main.getElementsByTagName('img');
  for (var k = 0; k < imgs.length; k++) {
    imgs[k].addEventListener('error', function(){
      var pn = this.parentNode; this.style.display = 'none';
      if (pn && pn !== main && !txt(pn) && pn.getElementsByTagName('img').length === 1) pn.style.display = 'none';
      later(); }, false);
    if (!imgs[k].complete) imgs[k].addEventListener('load', later, false);
    else if (!imgs[k].naturalWidth) { imgs[k].style.display = 'none'; var ip = imgs[k].parentNode; if (ip && ip !== main && !txt(ip)) ip.style.display = 'none'; }
  }
  layout();
})();
</script>
"""


FONT_CSS = ("https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@"
            "0,7..72,400..700;1,7..72,400..700&display=block")


def page(title, body, html_class, body_class, prev=None, nxt=None, stamp="", run_left="", run_right="",
         fonts="", next_label=None, run_href="index.html"):
    esc = html.escape
    top = f'<nav class="krun"><a href="{run_href}">{run_left}</a><span>{esc(run_right)}</span></nav>'
    nxt_name = esc(next_label) if next_label else esc(prev_title(nxt)) if nxt else ""
    nxt_block = (f'<a class="knext" href="{nxt}"><small>Next</small><span>{nxt_name} &rarr;</span></a>' if nxt
                 else '<a class="knext" href="index.html"><small>The end</small><span>Back to the front &rarr;</span></a>')
    prev_link = f'<a class="kprev" href="{prev}">&lsaquo; Back</a>' if prev else '<span class="kprev"></span>'
    nxt_short = (f'<a class="knx" href="{nxt}">{nxt_name} &rsaquo;</a>' if nxt
                 else '<a class="knx" href="index.html">The front &rsaquo;</a>')
    foot = (f'<footer class="kbar">{prev_link}<span class="kmid"><a id="kmore" href="#">More &darr;</a>'
            f'<span id="kpos"></span></span>{nxt_short}</footer>'
            f'<footer class="kfoot">{nxt_block}<div class="kmeta"><span></span><span>{stamp}</span></div></footer>')
    js = PAGER_JS.replace("__NEXT__", repr(nxt or "")).replace("__PREV__", repr(prev or ""))
    return f"""<!doctype html>
<html lang="en" class="{esc(html_class)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>{esc(title)}</title>{fonts}<link rel="stylesheet" href="kindle.css"></head>
<body class="{esc(body_class)}">
{top}
<div id="kview"><div id="kcont"></div><div id="kclip"><main id="kmain">{body}</main></div></div>
{foot}
{js}
</body></html>
"""


_TITLES = {}


def prev_title(href):
    return _TITLES.get(href, "")


def _text(frag):
    import re
    t = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", frag, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()


# Inline styles the e-ink pass wrote that the stylesheet already says.
_SLIM = [
    "color: rgb(0, 0, 0) !important;",
    "-webkit-text-fill-color: currentcolor !important;",
    "opacity: 1 !important;",
]


def slim(doc):
    import re
    for s in _SLIM:
        doc = re.sub(r"(?<![-\w])\s?" + re.escape(s), "", doc)
    doc = re.sub(r'\sstyle="\s*"', "", doc)
    # Icons that were emoji on the live page are empty frames here.
    doc = re.sub(r'<(span|i|div)\b[^>]*aria-hidden="true"[^>]*>\s*</\1>', "", doc)
    return doc


def localize_images(pages, out):
    """Download every picture once, turn it into a small greyscale JPEG next to
    the pages (sharp on e-ink, nothing to fetch on the Kindle). A picture that
    cannot be fetched is dropped rather than left as a broken box."""
    import hashlib
    import io
    import re
    import urllib.request
    try:
        from PIL import Image, ImageOps, ImageFilter
    except Exception as e:
        print(f"kindle_full: images left remote ({e!r})", file=sys.stderr)
        return
    os.makedirs(os.path.join(out, "img"), exist_ok=True)
    done = {}
    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

    def fetch(src):
        if src in done:
            return done[src]
        name = None
        try:
            req = urllib.request.Request(src, headers={"User-Agent": ua})
            raw = urllib.request.urlopen(req, timeout=20).read()
            im = Image.open(io.BytesIO(raw))
            im = ImageOps.exif_transpose(im).convert("L")
            if im.width > 1100:
                im = im.resize((1100, round(im.height * 1100 / im.width)), Image.LANCZOS)
            im = ImageOps.autocontrast(im, cutoff=1)
            im = im.filter(ImageFilter.UnsharpMask(radius=1, percent=60, threshold=2))
            name = "img/" + hashlib.sha1(src.encode()).hexdigest()[:16] + ".jpg"
            im.save(os.path.join(out, name), "JPEG", quality=78, optimize=True, progressive=False)
        except Exception as e:
            print(f"kindle_full: image left remote {src[:80]} ({e!r})", file=sys.stderr)
        done[src] = name
        return name

    def fix(m):
        tag = m.group(0)
        src = re.search(r'\ssrc="([^"]+)"', tag)
        if not src:
            return ""
        url = html.unescape(src.group(1))
        if url.startswith("data:"):
            return tag
        if url.startswith("//"):
            url = "https:" + url
        if not url.startswith("http"):
            return tag
        name = fetch(url)
        if not name:  # leave it to the Kindle; the pager hides it if it fails there too
            return tag
        return tag.replace(src.group(0), f' src="{name}"')

    for pg in pages:
        pg["html"] = re.sub(r"<img\b[^>]*>", fix, pg["html"])


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
        ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, timezone_id=TZ, device_scale_factor=2,
                                  has_touch=True, locale="en-US", reduced_motion="reduce")
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
# Reading order for the first half hour awake: what the day needs, then a calm
# stretch at home, then the news once the reader is alert, then their own
# interests, and it ends on Thailand and, last of all, the beach.
PARTS = [
    ("Your day", ["today", "roads", "family"]),
    ("Home and land", ["solar", "garden", "river", "nearby"]),
    ("The news", ["news", "markets", "civics", "sports"]),
    ("Around town", ["music", "watch", "local"]),
    ("The back pages", ["almanac", "science", "doodles", "delights", "world", "coast"]),
]
# Card order inside a section, by the id of each card's heading (titles rotate).
CARD_ORDER = {
    "today": ["today-card", "brief-h", "wx-h", "cal-h", "plan-h", "yard-h", "shade-h", "fc-h"],
    "roads": ["drive-h", "road-h", "ski-h", "mtn-h", "trail-h", "fire-h", "quake-h"],
    "solar": ["t-now", "loads-h", "bill-h", "grid-h", "mo-h", "wins-h", "sunact-h"],
    "garden": ["look-h", "pollen-h", "burn-h", "birds-h", "plant-h", "bloom-h", "mush-h"],
    "news": ["localnews-h", "bignews-h", "stories-h", "reviews-h"],
    "markets": ["he-h", "mkt-h", "re-h"],
    "music": ["rec-h", "drum-h", "bday-h", "alb-h", "jazz-h", "gig-h", "artist-h"],
    "watch": ["br-h", "tv-h", "kidmov-h", "clsmov-h"],
    "almanac": ["hol-h", "hist-h", "near-h"],
    "delights": ["potd-h", "apod-h", "art-h", "poem-h", "good-h", "oldpdx-h", "show-h", "ask-h", "books-h", "read-h"],
    "world": ["bkk-h", "thai-h"],
    "coast": ["surf-h", "bar-h", "coast-summary", "minus-h", "shell-h", "cev-h", "whale-h"],
}
# Cards that read better in another section: (heading id, from, to).
CARD_MOVES = [("thai-h", "delights", "world")]

# No fact twice: an item already printed earlier in the edition is taken out
# of the later page. Alfred's briefing is a digest, so it goes last: any line of
# his that another page already carries is dropped from the briefing.
DEDUPE = r"""
(pages) => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const seen = new Map();           // text -> element that printed it first
  const MIN = 40;
  const docs = pages.map(pg => { const d = document.createElement('div'); d.innerHTML = pg.html; return d; });
  const isAlfred = pages.map(pg => /id="brief-h"/.test(pg.html));
  const prune = el => {
    let p = el.parentElement; el.remove();
    while (p && p.parentElement && !p.querySelector('img, svg, h2') && norm(p.textContent).length < 15) {
      const up = p.parentElement; p.remove(); p = up; }
  };
  const walk = (root) => {
    const stack = [root.firstElementChild ? root : null].filter(Boolean);
    const out = [];
    const visit = el => {
      for (let c = el.firstElementChild; c; ) { const nx = c.nextElementSibling;
        const tag = c.tagName;
        if (/^(H1|H2|SCRIPT|STYLE|SVG)$/.test(tag) || c.querySelector('h2') || c.classList.contains('head')) { visit(c); c = nx; continue; }
        const t = norm(c.textContent);
        if (t.length >= MIN) {
          const prev = seen.get(t);
          if (prev && !prev.contains(c) && !c.contains(prev)) { prune(c); c = nx; continue; }
          if (!prev) seen.set(t, c);
        }
        visit(c); c = nx; }
    };
    visit(root);
  };
  // The same event or story under its own name on two pages: keep the first.
  const named = new Set();
  docs.forEach((d, i) => {
    if (isAlfred[i]) return;
    const mine = [];
    for (const b of [...d.querySelectorAll('b, strong')]) {
      const t = norm(b.textContent).replace(/[.:]$/, '');
      if (t.length < 18 || !b.isConnected) continue;
      if (named.has(t)) {
        let it = b;
        while (it.parentElement && it.parentElement !== d && it.parentElement.querySelectorAll('b, strong').length === 1) it = it.parentElement;
        if (it !== b && !it.querySelector('h2') && !it.classList.contains('head')) prune(it);
      } else mine.push(t);
    }
    mine.forEach(t => named.add(t));
  });
  docs.forEach((d, i) => { if (!isAlfred[i]) walk(d); });
  // The front page's "Big in town" is the calendar's evening game again.
  docs.forEach(d => { const x = d.querySelector('#day-big'); if (x) x.remove(); });
  // Alfred: drop any line that repeats something printed elsewhere.
  const keys = [...seen.keys()].filter(k => k.length >= 25);
  for (const t of $titles) keys.push(t);
  for (const t of named) keys.push(t);
  const texts = docs.map((d, i) => isAlfred[i] ? '' : norm(d.textContent));
  docs.forEach((d, i) => {
    if (!isAlfred[i]) return;
    for (const li of [...d.querySelectorAll('li')]) {
      const bs = [...li.querySelectorAll('b, strong')].map(x => norm(x.textContent)).filter(x => x.length >= 6);
      if (bs.length && texts.some(pt => bs.every(x => pt.includes(x)))) { prune(li); continue; }
      const t = norm(li.textContent);
      const b = [...li.querySelectorAll('b')].map(x => norm(x.textContent)).filter(x => x.length >= 12);
      const subj = t.split(': ').pop().replace(/[.!]+$/, '');
      if (/ is today\.?$/.test(t) || keys.some(k => t.includes(k) || b.some(x => k.includes(x)) || (subj.length >= 15 && k.includes(subj)))) prune(li);
    }
    for (const h of [...d.querySelectorAll('h3')]) {
      const nx = h.nextElementSibling;
      if (!nx || /^H3$/.test(nx.tagName) || !norm(nx.textContent)) h.remove();
    }
  });
  return docs.map(d => d.innerHTML);
}
"""


def dedupe(pages, titles):
    """Run DEDUPE over the pages in reading order (in place)."""
    import json
    exe = os.environ.get("KINDLE_CHROMIUM") or None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=exe)
            p = browser.new_page()
            js = DEDUPE.replace("$titles", json.dumps([t.lower() for t in titles if len(t) >= 20]))
            res = p.evaluate(js, [{"html": pg["html"]} for pg in pages])
            browser.close()
        for pg, h in zip(pages, res):
            pg["html"] = h
    except Exception as e:  # never lose the edition over this
        print(f"kindle_full: dedupe skipped: {e}", file=sys.stderr)


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


# Plain names for cards whose on-page title is a play on words. The witty
# title stays on the page; contents, section fronts and "Next" use these.
NAMES = {
    "Rise and shine, sir.": "Alfred's briefing", "Curtain call": "Window shades",
    "Mark the calendar": "Tickets and deadlines", "Table talk": "Dinner question",
    "Brush pile check": "Burn day check", "Rumbles nearby": "Earthquakes this week",
    "Will they bite?": "Fishing the Columbia", "Faith in humanity": "Good news",
    "Something long and good": "Today's long read", "Something to look at": "Artwork of the day",
    "Listen to this drummer": "Drum break of the day", "Happy birthday, records": "Album birthdays",
    "Worth buying?": "Consumer reviews", "Big nights out": "Big events in town",
    "Race weekend watch": "Formula 1", "The light is leaving": "Daylight",
    "Who can still win it": "F1 title fight", "The library so far": "Your bookshelf",
    "Tidepool days": "Minus tides", "Solar right now": "Solar right now",
}


def main(site):
    import json
    import re
    cache = os.environ.get("KINDLE_CACHE")
    if cache and os.path.exists(cache):
        with open(cache) as f:
            data, stamp, longdate = json.load(f)
    else:
        data, stamp, longdate = snapshot(site)
        if cache:
            with open(cache, "w") as f:
                json.dump([data, stamp, longdate], f)
    out = os.path.join(site, "kindle")
    os.makedirs(out, exist_ok=True)
    font_css, font_links = self_host_fonts(out)
    with open(os.path.join(out, "kindle.css"), "w") as f:
        f.write(font_css + "\n" + data["css"] + "\n" + EINK_CSS)

    by_id = {s["id"]: s for s in data["sections"] if s.get("cards")}
    # Cards with nothing to read are dropped; a quiet weather alert joins the front page.
    for s in by_id.values():
        kept = []
        for c in s["cards"]:
            t = _text(c["html"])
            if len(t) < 20 and "<img" not in c["html"]:
                if 'class="allclear"' in c["html"] and kept:
                    kept[0]["html"] += c["html"]
                continue
            if 'class="allclear"' in c["html"] and len(t) < 90 and kept:
                kept[0]["html"] += c["html"]
                continue
            kept.append(c)
        s["cards"] = kept
    by_id = {k: s for k, s in by_id.items() if s["cards"]}

    # A card whose body is only its headline and sources says nothing: drop it.
    def body_text(h):
        h = re.sub(r"<h2\b.*?</h2>", " ", h, flags=re.S)
        h = re.sub(r'<p class="(kkick|kkicker|ksources)".*?</p>', " ", h, flags=re.S)
        h = re.sub(r'<(span|p) class="meta".*?</\1>', " ", h, flags=re.S)
        return _text(h)
    for s in by_id.values():
        s["cards"] = [c for c in s["cards"] if len(body_text(c["html"])) >= 25 or re.search(r"<img\b", c["html"])]
    def move_first(sec, pred, to=0):
        cards = by_id.get(sec, {}).get("cards", [])
        for k, c in enumerate(cards):
            if pred(c):
                cards.insert(to, cards.pop(k))
                return
    move_first("solar", lambda c: c["title"].lower().startswith("solar right now"))
    # Repeats and one-liners.
    if "doodles" in by_id:
        by_id["doodles"]["cards"] = [c for c in by_id["doodles"]["cards"] if c["title"] != "Who can still win it"]
    if "garden" in by_id:
        gc = by_id["garden"]["cards"]
        a = next((c for c in gc if c["title"] == "What is blooming"), None)
        b = next((c for c in gc if c["title"] == "Eating with the season"), None)
        if a and b:
            a["html"] += re.sub(r"<h2\b", '<h3', re.sub(r"</h2>", "</h3>", b["html"]))
            gc.remove(b)
    for key, src, dst in CARD_MOVES:
        if src in by_id and dst in by_id:
            for c in list(by_id[src]["cards"]):
                if f'id="{key}"' in c["html"]:
                    by_id[src]["cards"].remove(c)
                    by_id[dst]["cards"].append(c)
    if "world" in by_id:
        by_id["world"]["title"] = "Thailand"
        by_id["world"]["sub"] = "Bangkok right now, and a phrase to try"
    by_id = {k: s for k, s in by_id.items() if s["cards"]}

    # Today opens with one front page: the greeting, the weather and the day ahead.
    if "today" in by_id:
        cards = by_id["today"]["cards"]
        if cards and cards[0]["title"] == "Good morning" and len(cards) > 1 and 'id="today-card"' in cards[1]["html"]:
            g = data.get("front", {})
            hero = (f'<div class="kfrontwx"><div class="kdeg">{html.escape(g.get("temp", ""))}'
                    f'<small>{html.escape(g.get("where", ""))}</small></div>'
                    f'<div class="ksum">{html.escape(g.get("summary", ""))}</div></div>')
            head = (f'<div class="head"><p class="kkick">{html.escape(g.get("date", ""))}'
                    f'{" &middot; " + html.escape(g["holiday"]) if g.get("holiday") else ""}</p>'
                    f'<h2>Good morning</h2></div>')
            alerts = "".join(re.findall(r'<div class="allclear".*?</div>', cards[0]["html"], re.S))
            cards[1] = {"title": "Good morning",
                        "html": head + (hero if g.get("temp") else "") + cards[1]["html"] + alerts}
            cards.pop(0)

    for sid, keys in CARD_ORDER.items():
        if sid not in by_id:
            continue
        def rank(c, keys=keys):
            for n, k in enumerate(keys):
                if f'id="{k}"' in c["html"]:
                    return n
            return len(keys)
        by_id[sid]["cards"].sort(key=rank)

    known = [i for _, ids in PARTS for i in ids]
    parts = [(name, [i for i in ids if i in by_id]) for name, ids in PARTS]
    extra = [i for i in by_id if i not in known]
    if extra:
        parts.append(("More", extra))
    parts = [(name, ids) for name, ids in parts if ids]
    order = [i for _, ids in parts for i in ids]
    part_of = {i: name for name, ids in parts for i in ids}

    # Flat reading order: section front, then every card of the section.
    pages = []
    for i in order:
        cards = by_id[i]["cards"]
        for k, c in enumerate(cards):
            body = c["html"]
            if "<h2" not in body and c["title"] not in _text(body):
                body = f'<h2 class="kh2">{html.escape(c["title"])}</h2>' + body
            if c["title"] in NAMES and NAMES[c["title"]] != c["title"]:
                plain = html.escape(NAMES[c["title"]])
                if re.search(r'<p class="kkick(?:er)?"[^>]*>.*?</p>', body):
                    body = re.sub(r'<p class="kkick(?:er)?"[^>]*>.*?</p>', f'<p class="kkick">{plain}</p>', body, count=1)
                else:
                    body = re.sub(r"(<h2\b)", f'<p class="kkick">{plain}</p>\\1', body, count=1)
            pages.append({"sec": i, "file": f"{i}-{k + 1:02d}.html", "title": NAMES.get(c["title"], c["title"]), "html": body,
                          "k": k + 1, "of": len(cards)})
    dedupe(pages, [])
    localize_images(pages, out)
    front = {i: f"{i}.html" for i in order}
    _TITLES.update({pg["file"]: pg["title"] for pg in pages})
    _TITLES.update({front[i]: by_id[i]["title"] for i in order})
    _TITLES["index.html"] = "The front"

    where = {}
    for pg in pages:
        for anchor in re.findall(r'\sid="([^"]+)"', pg["html"]):
            where.setdefault(anchor, pg["file"])

    def link_fix(doc):
        return re.sub(r'href="KHASH:([^"]*)"',
                      lambda m: f'href="{where[m.group(1)]}#{m.group(1)}"' if m.group(1) in where else "", doc)

    def teaser(pg):
        m = re.search(r'class="meta"[^>]*>(.*?)</span>', pg["html"], re.S)
        return _text(m.group(1)) if m else ""

    edition = stamp.split(" ", 1)[-1].replace("AM", "am").replace("PM", "pm")
    stamp_txt = html.escape(f"Edition of {edition}")
    seq = []  # reading order of every file
    for i in order:
        seq.append(front[i])
        seq.extend(pg["file"] for pg in pages if pg["sec"] == i)
    after = {f: (seq[n + 1] if n + 1 < len(seq) else None) for n, f in enumerate(seq)}
    before = {f: (seq[n - 1] if n else "index.html") for n, f in enumerate(seq)}
    nsec = len(order)

    for n, pg in enumerate(pages):
        sec = by_id[pg["sec"]]
        sib = [p for p in pages if p["sec"] == pg["sec"]]
        rail_items = [p for p in sib if p["k"] > pg["k"]][:3]
        rail = ""
        if rail_items:
            rail = (f'<nav id="krail"><h4>Also in {html.escape(sec["title"])}</h4>'
                    + "".join(f'<a href="{p["file"]}"><b>{html.escape(p["title"])}</b></a>' for p in rail_items)
                    + "</nav>")
        nxt = after[pg["file"]]
        label = None
        if nxt and nxt in front.values():
            label = f'Next: {_TITLES[nxt]}'
        doc = page(pg["title"], slim(link_fix(pg["html"])) + rail, data["htmlClass"], data["bodyClass"] + " kcard",
                   prev=before[pg["file"]], nxt=nxt, stamp=stamp_txt, run_left=html.escape(sec["title"]),
                   run_right=f'Page {pg["k"]} of {pg["of"]}', fonts=font_links, next_label=label,
                   run_href=front[pg["sec"]])
        with open(os.path.join(out, pg["file"]), "w") as f:
            f.write(doc)

    # Section fronts: the name, the deck and every story in it.
    for num, i in enumerate(order, 1):
        sec = by_id[i]
        cards = [pg for pg in pages if pg["sec"] == i]
        rows = "".join(
            f'<li><a href="{pg["file"]}"><span class="kn">{pg["k"]:02d}</span><span class="kt"><b>{html.escape(pg["title"])}</b>'
            f'<small>{html.escape(teaser(pg))}</small></span></a></li>' for pg in cards)
        body = (f'<p class="kkick">{html.escape(part_of[i])} &middot; Section {num} of {nsec}</p>'
                f'<h2 class="kfname">{html.escape(sec["title"])}</h2>'
                f'<p class="kfsub">{html.escape(sec.get("sub") or "")}</p>'
                f'<ol class="kfl{" kcompact" if len(cards) > 6 else ""}">{rows}</ol>')
        with open(os.path.join(out, front[i]), "w") as f:
            f.write(page(sec["title"], body, data["htmlClass"], data["bodyClass"] + " ksecfront",
                         prev=before[front[i]], nxt=after[front[i]], stamp=stamp_txt,
                         run_left="&lsaquo; The front", run_right=f"Section {num} / {nsec}", fonts=font_links))

    # The front: masthead, today at a glance, the top of the edition, then contents.
    g = data.get("front", {})
    gl = "".join(f"<li><b>{html.escape(k)}</b>{html.escape(v)}</li>" for k, v in data.get("glance2", [])[:5])
    deg = (f'<div class="kdeg">{html.escape(g.get("temp", ""))}<small>{html.escape(g.get("where", ""))}</small></div>'
           if g.get("temp") else "")
    leads = "".join(
        f'<a href="{where.get(a, front.get(s, "index.html")) if a else front.get(s, "index.html")}">'
        f'<small>{html.escape(by_id[s]["title"]) if s in by_id else ""}</small><b>{html.escape(t)}</b></a>'
        for t, s, a in data.get("leads", [])[:3])
    toc = []
    num = 0
    for name, ids in parts:
        cells = []
        for i in ids:
            num += 1
            cnt = len([pg for pg in pages if pg["sec"] == i])
            cells.append(f'<li><a href="{front[i]}"><span class="kn">{num:02d}</span><span class="kt">{html.escape(by_id[i]["title"])}</span>'
                         f'<span class="kc">{cnt}</span></a></li>')
        toc.append(f'<p class="kpart">{html.escape(name)}</p><ul class="kpartbox">{"".join(cells)}</ul>')
    body = (f'<div class="kmast"><p class="kname">The Morning Edition</p>'
            f'<p class="kdate">{html.escape(longdate.rsplit(",", 1)[0])}{" &middot; " + html.escape(g["holiday"]) if g.get("holiday") else ""}'
            f' &middot; {html.escape(edition)} edition</p></div>'
            + f'<h2 class="ktochead" id="contents">Contents</h2>{"".join(toc)}'
)
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(page("The Morning Edition", body, "", "kcontents", nxt=seq[0] if seq else None,
                     stamp=stamp_txt, run_left="", run_right="", fonts=font_links))
    n = len(pages)
    # The old bookmark (kindle.html) opens the edition.
    with open(os.path.join(site, "kindle.html"), "w") as f:
        f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=kindle/index.html">'
                '<a href="kindle/index.html">Open the Morning Edition</a>')
    print(f"kindle_full: wrote {n} pages in {len(order)} sections to {out}")


if __name__ == "__main__":
    main(sys.argv[1])
