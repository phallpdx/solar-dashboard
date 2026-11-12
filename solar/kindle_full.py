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

from . import ornament as kindle_orn
from . import kindle_present


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
                almanac: ['Almanac', null], science: ['Science', null], civics: ['Civics', null], doodles: ['By the numbers', null],
                world: ['Bangkok', null], nearby: ['The sky', null], family: ['Little one', 'Ideas for ages 2 to 3, places to go and what is going around'],
                roads: ['Roads and mountains', 'Traffic, road work, Mt. Hood, trails, fires and quakes'] };
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

  // 12. Data pages, designed for the page: the one number that matters biggest,
  // a verdict line, grids instead of repeated rows. Each step stands alone.
  const step = (name, f) => { try { f(); } catch (e) { console.log('kindle design ' + name + ': ' + e); } };
  const verdict = (text, before) => { if (!text || !before) return; const v = document.createElement('p'); v.className = 'kverdict'; v.textContent = text; before.before(v); return v; };
  const todayShort = new Date().toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric', timeZone: 'America/Los_Angeles'});

  step('swatches', () => {
    for (const card of $$('.card')) { const leg = [...card.querySelectorAll('.legend .sw, .legend i')].slice(0, 2).map(x => getComputedStyle(x).backgroundColor);
      if (leg.length < 2) continue;
      card.querySelectorAll('.sw, .legend i').forEach(x => { const k = leg.indexOf(getComputedStyle(x).backgroundColor); if (k >= 0) x.classList.add('ksw' + k); }); }
  });
  step('bullets', () => {
    for (const li of $$('li')) { const p = li.previousElementSibling; if (p && p.tagName === 'LI' && /^[a-z]/.test(li.textContent.trim())) { p.append('; ' + li.textContent.trim()); li.remove(); } }
  });
  step('surf', () => {
    const brks = $$('#surf-breaks .brk');
    if (!brks.length) return;
    const days = [...brks[0].querySelectorAll('.sday')].map(r => txt(r.firstElementChild).replace(/^Today$/, 'Today'));
    const pips = n => '<em class="kq">' + [1, 2, 3, 4].map(i => `<i class="${i <= n ? 'on' : ''}"></i>`).join('') + '</em>';
    const t = document.createElement('table'); t.className = 'kmatrix ksurf';
    t.innerHTML = '<thead><tr><th></th>' + days.map(d => `<th>${d}</th>`).join('') + '</tr></thead><tbody>' +
      brks.map(b => '<tr><th>' + txt(b.querySelector('.brk-top b') || b.querySelector('b')).replace(/ \/ Gearhart| \(.*\)/, '') + '</th>' +
        [...b.querySelectorAll('.sday')].map(r => {
          const ch = [...r.children], rt = ch[1], sz = ch[2], when = ch[3];
          const n = +((rt && rt.className.match(/rt(\d)/)) || [0, 0])[1];
          const m = txt(sz).match(/([\d.]+-[\d.]+|[\d.]+) ft · (\d+)s/) || [0, txt(sz), ''];
          return `<td class="q${n}">${pips(n)}<b>${txt(rt)}</b><span>${String(m[1]).replace('-', '–')} ft</span><small>${m[2] ? m[2] + 's · ' : ''}${txt(when)}</small></td>`;
        }).join('') + '</tr>').join('') + '</tbody>';
    const key = document.createElement('p'); key.className = 'note kkey';
    key.textContent = brks.map(b => txt(b.querySelector('.brk-top b') || b.querySelector('b')) + ': ' + txt(b.querySelector('small'))).filter(s => s.length > 4).join('. ') + '.';
    $('#surf-breaks').replaceWith(t); t.after(key);
  });

  step('morning units', () => {
    for (const s of $$('#out-facts small')) s.textContent = s.textContent.replace(/ PM2\.5 today · .*/, '').replace(/^\s*·\s*/, '');
  });

  step('hours', () => {
    const p = $('p.khours'); if (!p) return;
    const cells = [...p.textContent.matchAll(/(\d{1,2} ?[ap]m) (-?\d+)°/g)].map(m => [m[1], +m[2]]);
    if (cells.length < 4) return;
    const lo = Math.min(...cells.map(c => c[1])), hi = Math.max(...cells.map(c => c[1]));
    const k = document.createElement('div'); k.className = 'khr';
    k.innerHTML = cells.map(([h, t]) => `<div${t === hi ? ' class="hot"' : ''}><b>${t}°</b><i style="height:${4 + Math.round((t - lo) / Math.max(1, hi - lo) * 26)}px"></i><span>${h.replace(/ ?([ap])m/, '$1').replace(/^12p$/, 'noon')}</span></div>`).join('');
    p.replaceWith(k);
  });

  step('markets', () => {
    const mk = $('#mkt'), sp = $('#mkt-spark'), ms = $('#mkt-summary');
    if (mk && ms) { ms.after(mk); if (sp) mk.after(sp);
      const keep = txt(ms).split(/(?<=\.)\s+/).filter(x => !/^The (Nasdaq|Dow|10-year)|Treasury yields/.test(x));
      if (keep.length) ms.textContent = keep.join(' ').replace(/^The S&P 500 is (up|down) [\d.]+% at [\d,]+, /, 'The S&P 500 is ').replace(/^The S&P 500 is up/, 'The S&P 500 is up'); }
    const sx = sp && sp.querySelector('.axis span'); if (sx) sx.textContent = 'S&P 500, 30 trading days ago';
  });

  step('sports', () => {
    for (const top of $$('.team-top')) {
      const card = top.closest('.card'); if (!card) continue;
      const rows = [...card.querySelectorAll('.lines>div')];
      const nx = rows.find(d => /^Next:/.test(txt(d.firstElementChild))), w = rows.find(d => /^Watch on/.test(txt(d.firstElementChild)));
      const ln = [...card.querySelectorAll('p.note')].find(p => /^Last game:/.test(txt(p)));
      const m = ln && txt(ln).match(/^Last game: (\w+) ([\d–-]+) (vs\.?|at) (.+?) on (\w+)/);
      if (!nx && !m) continue;
      const k = document.createElement('div'); k.className = 'kscore'; let h = '';
      if (m) h += `<div><span class="k">Last game</span><b>${({won: 'W', lost: 'L', drew: 'D', tied: 'T'})[m[1]] || ''} ${m[2].replace('-', '–')}</b><small>${m[3]} ${m[4]} · ${m[5]}</small></div>`;
      if (nx) {
        const when = txt(nx.lastElementChild), opp = txt(nx.firstElementChild).replace(/^Next:\s*/, '');
        let big = when;
        if (when.indexOf(todayShort) === 0) { const hr = +(when.match(/(\d+)(?::\d\d)? pm/) || [0, 0])[1]; big = when.replace(todayShort + ', ', hr >= 5 && hr < 12 ? 'Tonight ' : 'Today '); }
        h += `<div><span class="k">Next</span><b>${big}</b><small>${opp}${w ? ' · ' + txt(w.lastElementChild) : ''}</small></div>`;
      }
      k.innerHTML = h; top.after(k); [nx, w, ln].forEach(kill);
    }
  });

  step('seven days', () => {
    const fds = $$('#forecast .fd'); if (fds.length < 3) return;
    for (const f of fds) { const r = f.querySelector('.r'); const c = f.getAttribute('title'); if (r && c && !txt(r).includes(c)) r.textContent = `${c} · ${txt(r)}`; }
    const kwh = f => +(txt(f.querySelector('.e')).match(/\d+/) || [0])[0];
    const wet = f => +(txt(f.querySelector('.r')).match(/(\d+)%/) || [0, 0])[1] >= 70;
    const name = f => txt(f.querySelector('.d')).replace(/^Today$/, 'today');
    const best = [...fds].sort((a, b) => kwh(b) - kwh(a)).slice(0, 2).filter(f => kwh(f) > 0);
    if (best[0]) { const e = best[0].querySelector('.e'); if (e) e.style.setProperty('font-weight', '700', 'important'); }
    const runs = fds.filter(wet).map(name);
    verdict((best.length ? `Sunniest: ${best.map(f => `${name(f)} (~${kwh(f)} kWh)`).join(' and ')}.` : '') +
      (runs.length ? ` Wettest: ${runs.length > 2 ? runs[0] + ' to ' + runs[runs.length - 1] : runs.join(' and ')}.` : ''), $('#forecast'));
    const rs = $('#roof-sun'); if (rs) kill(rs);
  });

  step('solar asleep', () => {
    const now = $('#t-now'), load = $('#loads .load');
    if (!now || parseFloat(txt(now)) !== 0 || !load) return;
    if (/No reading yet today|hasn.t reported yet/.test(txt($('#t-now-s')))) { const td = $('#t-today'), ts = $('#t-today-s');
      if (td) td.textContent = '–'; if (ts) ts.textContent = 'No inverter reading yet today · ' + txt(ts).replace(/ · last year this day: .*$/, ''); }
    const kw = txt(load).match(/~?(\d+) kWh/), when = txt(load.querySelector('b'));
    const tile = now.closest('.tile'); if (!tile || !kw) return;
    const k = tile.querySelector('.k'); if (k) k.textContent = 'Expected today';
    now.textContent = `~${kw[1]} kWh`;
    const s = $('#t-now-s'); if (s) s.textContent = when ? `Best ${when}` : 'The inverter wakes at sunrise';
  });

  step('bill', () => {
    const bb = $('#bill .bars'); if (!bb) return;
    const ds = [...bb.children].filter(d => d.title), val = d => +((d.title.match(/\$([\d,.]+)/) || [0, '0'])[1].replace(/,/g, ''));
    if (ds.length < 3) return;
    const peak = ds.reduce((a, b) => val(b) > val(a) ? b : a), last = ds[ds.length - 1];
    for (const d of new Set([peak, last])) { const s = document.createElement('b'); s.className = 'kbv'; s.textContent = '$' + Math.round(val(d)); d.prepend(s); const fi = d.querySelector('i'); if (fi && fi.style.height) s.style.bottom = fi.style.height; }
    const ax = document.createElement('div'); ax.className = 'kbx';
    ax.innerHTML = ds.map(d => `<span>${((d.title.match(/^\s*(\w)/) || ['', ''])[1])}</span>`).join('');
    const old = bb.nextElementSibling; if (old && /axis/.test(old.className)) old.replaceWith(ax); else bb.after(ax);
    const lines = $$('#bill .lines>div').map(d => [txt(d.firstElementChild), txt(d.lastElementChild)]);
    const lastBill = lines.find(l => /^Last bill/i.test(l[0])), ly = lines.find(l => /last year/i.test(l[0]));
    if (lastBill && ly) verdict(`Your last bill was ${lastBill[1].match(/\$[\d,.]+/) ? lastBill[1].match(/\$[\d,.]+/)[0] : lastBill[1]}. This time last year it was ${ly[1].match(/\$[\d,.]+/) ? ly[1].match(/\$[\d,.]+/)[0] : ly[1]}.`, $('#bill'));
  });

  step('grid', () => {
    const sp = $$('#grid-legend span').map(s => txt(s).match(/^(.*?) (\d+)%$/)).filter(Boolean);
    if (sp.length < 2) return;
    sp.sort((a, b) => b[2] - a[2]);
    const fossil = /gas|coal|oil|biomass|other/i;
    const k = document.createElement('div'); k.className = 'kmix';
    k.innerHTML = sp.map(m => `<div class="${fossil.test(m[1]) ? 'fossil' : ''}"><span>${m[1]}</span><em><i style="width:${m[2]}%"></i></em><b>${m[2]}%</b></div>`).join('');
    const bar = $('#grid-bar'); if (bar) bar.replaceWith(k); else $('#grid-legend').before(k);
    kill($('#grid-legend'));
    const gs = $('#grid-summary'), m = gs && txt(gs).match(/(\d+)% carbon-free/);
    if (m) { const b = document.createElement('p'); b.className = 'kbignum'; b.innerHTML = `<b>${m[1]}%</b> carbon-free right now`; gs.before(b);
      const wk = txt(gs).match(/past week averaged (\d+%)/); if (wk) gs.textContent = `The past week averaged ${wk[1]}.`; else kill(gs); }
  });

  step('mountain', () => {
    const rows = $$('#mtn > div, #mtn .mtn');
    if (rows.length > 1 && rows.every(r => /Hidden today/.test(txt(r)) && /Tomorrow: hidden/i.test(txt(r))))
      verdict('All three peaks are hidden today and tomorrow.', $('#mtn'));
    for (const el of $$('#ski-card .k, #ski-card .tile span')) if (/^Last 24 hours$/i.test(txt(el))) el.textContent = '24-hour change';
  });

  step('pollen', () => {
    const rows = $$('#pollen > div, #pollen .lines > div');
    if (!rows.length) return;
    if (rows.every(r => /Off season/i.test(txt(r)) && !/(Low|Moderate|High)\b/.test(txt(r).replace(/Off season/g, '')))) {
      const v = document.createElement('p'); v.className = 'kverdict'; v.textContent = 'Nothing in the air: grass, tree and weed pollen are all off season for the next three days.';
      const box = $('#pollen'); box.replaceWith(v);
    }
  });

  step('river', () => {
    for (const el of $$('#columbia-facts .mini, #columbia-card .mini')) {
      const t = txt(el), m = t.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})/);
      if (/crest|tops out|peak/i.test(t) && m) {
        const d = new Date(`${m[1]} ${m[2]}, ${new Date().getFullYear()}`), today = new Date(); today.setHours(0, 0, 0, 0);
        if (d < today) kill(el);
      }
    }
    for (const el of $$('#columbia-card p, #columbia-summary')) if (/tops out at [\d.]+ ft (Mon|Tue|Wed|Thu|Fri|Sat|Sun)/.test(txt(el))) {
      const m = txt(el).match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})/);
      if (m) { const d = new Date(`${m[1]} ${m[2]}, ${new Date().getFullYear()}`), t0 = new Date(); t0.setHours(0, 0, 0, 0);
        if (d < t0) el.textContent = el.textContent.replace(/\s*(?:The NWS )?forecast tops out at \d+(?:\.\d+)? ft [^]*?\.(?=\s|$)/i, '').trim(); }
    }
  });

  step('bangkok', () => {
    if (typeof D === 'undefined' || !D.bangkok || !D.bangkok.days) return;
    $$('#bkk .lines>div>span:first-child, #world .lines>div>span:first-child').forEach((s, i) => {
      const d = D.bangkok.days[i]; if (!d || !d.date) return;
      s.textContent = new Date(d.date + 'T12:00:00+07:00').toLocaleDateString('en-US', {timeZone: 'Asia/Bangkok', weekday: 'short', month: 'short', day: 'numeric'}) + (i === 0 ? ' (today there)' : '');
    });
  });
  $$('i.aqi, .aqi-dot').forEach(kill);

  step('rain totals', () => {
    for (const s of $$('.rain-tot > span')) s.innerHTML = s.innerHTML.replace(/(\d)(?:″|")/g, '$1 in');
  });

  step('album birthdays', () => {
    for (const b of $$('.bday')) {
      const t = b.querySelector('b'); if (t && t.nextSibling && t.nextSibling.nodeType === 1) t.after(document.createTextNode(' '));
      const age = b.querySelector('.age'); if (age) age.textContent = txt(age).replace(/\s*yrs?\.?$/, '');
    }
  });

  step('quakes', () => {
    for (const el of $$('#quakes *, #quake-card *')) if (!el.children.length) {
      el.textContent = el.textContent.replace(/Under the volcanoes: (.+?) (\d+)\./, (m, v, n) => `${n} small quake${n === '1' ? '' : 's'} under ${v} this week.`);
    }
  });

  // 13. Copy desk: web-isms out, house style in, long lists edited down, wrong facts fixed.
  step('bangkok rows', () => {
    if (typeof D === 'undefined' || !D.bangkok || !D.bangkok.days) return;
    const bkToday = new Date().toLocaleDateString('en-CA', {timeZone: 'Asia/Bangkok'});
    const rows = $$('#bkk .lines>div, #world .lines>div').filter(r => r.firstElementChild);
    rows.forEach((r, i) => {
      const d = D.bangkok.days[i]; if (!d || !d.date) return;
      if (d.date < bkToday) { kill(r); return; }
      const lab = d.date === bkToday ? 'Today' : new Date(d.date + 'T12:00:00+07:00').toLocaleDateString('en-US', {timeZone: 'Asia/Bangkok', weekday: 'short', month: 'short', day: 'numeric'});
      r.firstElementChild.textContent = lab;
    });
  });

  step('web-isms', () => {
    kill($('#kid-change'));
    for (const el of $$('button, .joy-btn')) if (/Change|Listen|Play|Show|Hide|Refresh/i.test(txt(el))) kill(el);
    $$('#jazz .cite, #gigs .cite, #shows .cite, #kid-out .cite, #big .cite, #concerts .cite').forEach(kill);
    for (const a of $$('a, span.pill, span.tag')) if (/^(Tickets|Buy|Book|Deadline|Permit)\s*(→|›)?$/i.test(txt(a)) && a.closest('#jazz, #gigs, #plan, #shows, #concerts')) kill(a);
    for (const el of $$('#plan *')) if (!el.children.length && /^\s*·\s*(Tickets|Buy|Book|Deadline|Permit)\s*$/i.test(el.textContent)) kill(el);
    const PROV = /\b(listing|guide|page|site) (gives|lists|reports|says)\b|\breports? (Nov|Dec|Jan|Fri|Sat|Sun|Mon|Tue|Wed|Thu)|hasn['’]t (fully )?posted|doesn['’]t state a year|found (only )?on (ticket|event) listings|date confirmed by|comes from an event listing|not yet confirmed by the organizer|^Source:|^Sources?:|A third-party guide/i;
    for (const el of $$('#kid-out small, #kid-out p, #jazz small, #jazz p, #big small, #plan small, #coast-events small, #bluray small, #gigs small, #gigs p, #family small, #family p')) {
      if (el.children.length > 1) continue;
      const parts = el.textContent.split(/(?<=[.;])\s+/), keep = parts.filter(x => !PROV.test(x));
      let s2 = keep.join(' ').replace(/,? (?:per|according to) (?:the )?[A-Z][\w'’&. ]+(?=[.;]|$)/g, '').replace(/\s*Price not given\.?/g, '').trim();
      if (s2 !== el.textContent.trim()) { if (s2) el.textContent = s2; else kill(el); }
    }
    for (const el of $$('section.group small, section.group .cite')) if (/^Source: /.test(txt(el)) && el.closest('#jazz, #gigs, #shows')) kill(el);
    for (const sel of ['#jazz-regulars', '#br-upcoming']) {
      const el = $(sel); if (!el) continue;
      const t = txt(el).replace(/\.$/, ''), m = t.match(/^([^:]{3,30}):\s*(.*)$/);
      if (!m) continue;
      const items = m[2].split(/\s*;\s*/).filter(Boolean);
      if (items.length < 2) continue;
      el.innerHTML = `<b>${m[1]}</b><ul class="kplain">${items.map(i => `<li>${i}</li>`).join('')}</ul>`;
    }
    // Chips every row shares say nothing.
    for (const box of $$('#kid-out, #family-out, .places')) {
      const chips = [...box.querySelectorAll('.pill, .when')]; const set = new Set(chips.map(txt));
      if (chips.length > 3 && set.size === 1) chips.forEach(kill);
    }
    for (const el of $$('.pill')) { const h = el.closest('section') && el.closest('section').querySelector('h3'); if (h && txt(h).toLowerCase().startsWith(txt(el).toLowerCase()) && txt(el).length > 4) kill(el); }
  });

  step('lists', () => {
    // Streaming: the best of what's new, not every release in every language.
    const tv = $('#tv');
    if (tv) {
      let section = '', kept = {recent: 0, soon: 0};
      for (const el of [...tv.children]) {
        if (/day-h|sub/.test(el.className) || /^H3$/.test(el.tagName)) { section = /later this month/i.test(txt(el)) ? 'later' : /recent|out now|new/i.test(txt(el)) ? 'recent' : 'soon'; if (section === 'later') kill(el); continue; }
        if (section === 'later') { kill(el); continue; }
        const score = +(txt(el).match(/(\d\.\d) on TMDB/) || [0, 0])[1];
        if (section === 'recent') { if (kept.recent >= 8) kill(el); else kept.recent++; }
        else { if (kept.soon >= 8 || (score && score < 6.5)) kill(el); else kept.soon++; }
      }
    }
    // Play ideas: three for the season, three for any day, a new set each morning.
    const ideas = $$('#play .idea, #play-card .idea');
    if (ideas.length > 6) {
      const doy = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 864e5);
      const season = ideas.filter(i => /season/i.test(txt(i.querySelector('.k, small, .when')) + i.className)), any = ideas.filter(i => !season.includes(i));
      const pick = (arr, n) => arr.length <= n ? arr : arr.map((x, k) => [x, (k - doy % arr.length + arr.length) % arr.length]).sort((a, b) => a[1] - b[1]).slice(0, n).map(x => x[0]);
      const keep = new Set([...pick(season, 3), ...pick(any, 3)]);
      ideas.forEach(i => { if (!keep.has(i)) kill(i); });
    }
    // Tickets and deadlines: the next three weeks in full; the rest on one line.
    const plan = $('#plan');
    if (plan) {
      const rest = [];
      for (const it of [...plan.children]) {
        const t = txt(it), m = t.match(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b/);
        const dated = /\b(Today|Tomorrow|In \d+ days|Starts|By)\b/.test(t);
        if (!dated) { const b = it.querySelector('b'); if (b) rest.push(txt(b).replace(/\s*(Tickets|Buy|Book|Deadline|Permit)$/, '')); kill(it); }
      }
      if (rest.length) { const p = document.createElement('p'); p.className = 'note kalso'; p.innerHTML = '<b>Already on sale:</b> ' + rest.join(' · '); plan.after(p); }
    }
    // Reviews: audio and video first; no business software.
    const rv = $('#reviews');
    if (rv) {
      const st = [...rv.querySelectorAll('.story')];
      st.forEach(s => { if (/VoIP|Password Manager|Case review|\bAIO\b|CRM|Payroll/i.test(txt(s))) kill(s); });
      const live = st.filter(s => s.isConnected), av = live.filter(s => /A\/V|TV|headphone|speaker|turntable|soundbar|projector|OLED|4K|audio/i.test(txt(s)));
      av.reverse().forEach(s => rv.prepend(s));
      [...rv.querySelectorAll('.story')].slice(10).forEach(kill);
    }
    for (const box of $$('#stories, #finds, #openings, #restaurants')) [...box.querySelectorAll('.story')].slice(8).forEach(kill);
    for (const s of $$('#openings .story, #restaurants .story')) if (/Not named/.test(txt(s))) kill(s);
    // Blu-ray: US deals only, each title once.
    const seenBr = new Set();
    for (const d of $$('#bluray .deal, #bluray .story')) {
      if (/£|\bUK\b|Amazon (Italy|UK|Germany|France|Spain)/.test(txt(d))) { kill(d); continue; }
      const k = txt(d.querySelector('b')).replace(/\(.*?\)|:? The Criterion Collection|4K.*$/gi, '').trim().toLowerCase();
      if (k && seenBr.has(k)) kill(d); else seenBr.add(k);
    }
    // Holidays: the next two months; Thailand's marked.
    for (const r of $$('#holidays > div, #holidays .lines > div')) {
      if (/(Second|Third) Day of Chinese New Year|\bobserved/i.test(txt(r))) { kill(r); continue; }
      const m = txt(r).match(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})(?:, (20\d\d))?\b/);
      if (m) { const now = new Date(), d = new Date(`${m[1]} ${m[2]}, ${m[3] || now.getFullYear()}`); if (d < new Date(now - 864e5)) d.setFullYear(now.getFullYear() + 1); if (d - now > 62 * 864e5) kill(r); }
    }
    // Albums: skip compilations; round birthdays get a word.
    for (const b of $$('.bday')) {
      const t = txt(b.querySelector('b')), age = +(txt(b.querySelector('.age')).match(/\d+/) || [0])[0];
      if (/Greatest|Best of|Sessions|Collection|Anthology|Hits\b/i.test(t)) kill(b);
      else if (age && age % 10 === 0) { const s = b.querySelector('small'); if (s) s.textContent += ` · turns ${age} today`; }
    }
    // Sky: meteor showers in the next two months.
    for (const r of $$('#sky > div')) {
      const m = txt(r).match(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b/);
      if (m && /meteor/i.test(txt(r))) { const now = new Date(), d = new Date(`${m[1]} ${m[2]}, ${now.getFullYear()}`); if (d < now) d.setFullYear(now.getFullYear() + 1); if (d - now > 62 * 864e5) kill(r); }
    }
    // Kids' movie: little ones get G and animation.
    const km = $('#kidmov-card');
    if (km && /\b(PG-13|teen)\b/i.test(txt(km))) kill(km);
  });

  step('trim', () => {
    for (const h of $$('#reps h3')) {
      const l = h.nextElementSibling;
      if (/sponsored/i.test(txt(h))) { kill(l); kill(h); }
      else if (/floor votes/i.test(txt(h)) && l) [...l.children].slice(2).forEach(kill);
      else if (/in the news/i.test(txt(h)) && l) [...l.children].slice(2).forEach(kill);
    }
    for (const el of $$('#reps *')) if (!el.children.length && el.textContent.length > 120) el.textContent = el.textContent.slice(0, 104).replace(/[\s;,:]+\S*$/, '') + '…';
    [...document.querySelectorAll('#restaurants .lines > div')].slice(8).forEach(kill);
    for (const el of [...document.querySelectorAll('#restaurants span')]) if (!el.children.length && /^Not named, /.test(el.textContent)) el.textContent = el.textContent.replace(/^Not named, /, '');
    for (const d of [...document.querySelectorAll('#finds > div')]) if (!/Where to buy/.test(txt(d))) kill(d);
    for (const box of [...document.querySelectorAll('#finds, #openings, #restaurants')]) [...box.children].filter(c => !/^H[2-4]$/.test(c.tagName)).slice(5).forEach(kill);
    const now = new Date(), days = d => (d - now) / 864e5;
    const dateOf = t => { const m = t.match(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b/); if (!m) return null;
      const d = new Date(`${m[1]} ${m[2]}, ${now.getFullYear()}`); if (days(d) < -2) d.setFullYear(now.getFullYear() + 1); return d; };
    for (const r of $$('#jazz > *')) { const d = dateOf(txt(r)); if (!d) continue;
      if (days(d) > 45) kill(r); else if (days(d) > 10) r.querySelectorAll('p, small, .cite').forEach(kill); }
    for (const r of $$('#kid-out a.story, #kid-out .story')) { const d = dateOf(txt(r)); if (d && days(d) > 30) kill(r); }
    const any = $$('#kid-out .story').filter(r => /Any time|In season/.test(txt(r))); any.slice(4).forEach(kill);
  });

  step('civics', () => {
    for (const el of $$('#reps *, #elect *')) if (!el.children.length) {
      el.textContent = el.textContent
        .replace(/Read twice and referred to the (.+?)\./g, 'In the $1.').replace(/Referred to the (.+?)\./g, 'In the $1.')
        .replace(/Chapter \d+, \(\d{4} Laws\): Effective date (\w+ \d+), \d{4}\.?/g, 'Law since $1.')
        .replace(/In committee upon adjournment\.?/g, 'Died in committee.')
        .replace(/Oregon Public Broadcasting - OPB/g, 'OPB').replace(/KOIN\.com/g, 'KOIN');
      if (/^A bill to /.test(el.textContent) && el.textContent.length > 110) el.textContent = el.textContent.slice(0, 100).replace(/\s+\S*$/, '') + '…';
    }
    for (const el of $$('#reps .story, #reps .lines>div')) if (/^[SH]D-\d+ — Oregon$/.test(txt(el.querySelector('b')))) kill(el);
    // Bills they sponsored: the three latest.
    for (const h of $$('#reps h3')) if (/sponsored/i.test(txt(h))) { const l = h.nextElementSibling; if (l) [...l.children].slice(3).forEach(kill); }
  });

  step('repeats', () => {
    const words = s => new Set(s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(w => w.length > 3));
    const names = s => new Set((s.match(/\b[A-Z][a-z]{3,}\b/g) || []).slice(1));
    const alike = (a, b) => { let k = 0; for (const w of a.w) if (b.w.has(w)) k++; const ov = k / Math.max(1, Math.min(a.w.size, b.w.size));
      let n = 0; for (const w of a.n) if (b.n.has(w)) n++; return ov >= 0.6 || (n >= 2 && ov >= 0.35); };
    for (const box of $$('#bignews, #localnews, #reviews, #stories, #finds')) {
      const seen = [];
      for (const s of box.querySelectorAll('.story')) {
        const t = txt(s.querySelector('b')), x = {w: words(t), n: names(t)};
        if (seen.some(y => alike(x, y))) kill(s); else seen.push(x);
      }
    }
    // Repeated small print under each row of a list.
    for (const list of $$('.lines, #mush, #re, #he')) {
      let prev = '';
      for (const c of list.querySelectorAll('.cite, small')) { const t = txt(c); if (t && t === prev && (c.matches('.cite') || /[.!]$/.test(t))) kill(c); else prev = t; }  // repeated notes only, never data (team, position, place, date)
    }
    const mm = txt($('#mush-meta')).replace(/″/g, ' in');
    if (mm) for (const s of $$('#mush small')) if (mm.includes(txt(s).replace(/″/g, ' in'))) kill(s);
    // Standings bullets that repeat the table above.
    for (const li of $$('[id^="pulse-"] li')) if (/^(Standings|Beat \w+ \d+-\d+):/.test(txt(li))) kill(li);
    // A deck that says what the first line says.
    for (const c of $$('section.card, .card')) {
      const m = c.querySelector('.head .meta'), f = c.querySelector('.head ~ * p, .head ~ p');
      if (m && f && txt(f).indexOf(txt(m)) === 0 && txt(m).length > 10) kill(m);
    }
    // Freshness stamps from this morning.
    const td = new Date().toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric'});
    for (const el of $$('p, small, .meta, span')) if (!el.children.length && /^(Summary|Analysis) as of /.test(txt(el)) && txt(el).includes(td)) kill(el);
    // Germ report that contradicts itself.
    for (const el of $$('#bug-card p, #bug-note, #germ-card p')) if (/Nothing much going around/i.test(txt(el)) && /Moderate|High/.test(txt(el.closest('.card') || el))) el.textContent = 'Mostly quiet; one thing is running at a moderate level, below.';
  });

  step('small copy', () => {
    for (const el of $$('#trail-card *, #trails *')) if (!el.children.length) el.textContent = el.textContent.replace(/^(\d+) in (\d+) weeks?$/, (m, n, w) => `${n} report${n === '1' ? '' : 's'} in ${w} weeks`);
    for (const el of $$('#mo-card *, #month-card *')) if (!el.children.length) el.textContent = el.textContent.replace(/\((\d+(?:\.\d+)?) a day\)/, '($1 kWh a day)');
    for (const el of $$('#blooms *')) if (!el.children.length && /^[a-z]/.test(el.textContent.trim())) el.textContent = el.textContent.trim().replace(/^./, c => c.toUpperCase());
    const ws = $('#whale-card');
    if (ws) for (const r of ws.querySelectorAll('.story, .lines>div, a')) if (/^(Cetaceans|Whales)\b/.test(txt(r.querySelector('b') || r))) { const h = r.closest('div, a'); kill(r); }
    for (const el of $$('#out-facts *')) if (!el.children.length && /^Next tide$/i.test(txt(el))) el.textContent = 'River tide';
    const intro = $('#brief .brief-intro');
    // (Alfred's intro is rewritten with the planner below.)
    for (const h of $$('h3')) { const h2 = h.closest('.card') && h.closest('.card').querySelector('h2'); if (h2 && txt(h2).toLowerCase() === txt(h).toLowerCase()) kill(h); }
    for (const el of $$('.story p, .story small')) { const t = txt(el); if (/\b(Camera|Editor|Motion GFX|Colour):/.test(t) || (t.length < 200 && t.length > 20 && /[a-z]$/.test(t) && !/[.!?]/.test(t))) kill(el); }
    for (const el of $$('section.group *')) if (!el.children.length && /\s[A-Z ]{6,}!$/.test(el.textContent)) el.textContent = el.textContent.replace(/\s*[A-Z ]{6,}!$/, '');
    for (const el of $$('#potd *, #art-card *')) if (!el.children.length && /^[a-z0-9_.-]{3,30}$/.test(txt(el)) && el.tagName === 'SMALL') el.textContent = 'Photo: ' + txt(el);
  });

  step('house style', () => {
    const tdate = new Date(), tm = new Date(Date.now() + 864e5);
    const fmt = d => d.toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric'});
    const T = fmt(tdate), M = fmt(tm);
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      let t = n.nodeValue, o = t;
      if (n.parentElement && n.parentElement.closest('script, style, svg')) continue;
      t = t.replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b/g, '$1, $2 $3');
      t = t.replace(/ +([,.;:!?])(?=\s|$)/g, '$1');
      t = t.replace(/(\d) %/g, '$1%');
      t = t.replace(/\b12 pm\b/g, 'noon').replace(/\b12 am\b/g, 'midnight');
      t = t.replace(/(\d{1,2}(?::\d\d)? [ap]m) (?:PT|Pacific|local)\b/g, '$1');
      t = t.replace(/(\d(?::\d\d)?(?: [ap]m)?) – (\d)/g, '$1–$2');
      t = t.replace(/\b(\d+)h (\d+)m\b/g, '$1 hr $2 min');
      t = t.replace(/(\d)(?:″)(?=[\s,.;)]|$)/g, '$1 in');
      t = t.replace(/(\d)-(\d+(?:\.\d+)?) (ft|in|mph|kt)\b/g, '$1–$2 $3');
      t = t.replace(/(^|[\s(])-(\d)/g, '$1−$2');
      t = t.replace(/\bMPH\b/g, 'mph').replace(/ · Other · /g, ' · ').replace(/\$(\d+)\.00\b/g, '$$$1');
      t = t.replace(/(\d+) \/100\b/g, '$1/100').replace(/from the (\w+) to the \1\b/g, 'in the $1');
      t = t.replace(/\b(Ii|Iii|Iv|Vi|Vii|Viii)\b/g, m => m.toUpperCase());
      t = t.replace(/\bcovered by (\d+) outlets\b/g, '$1 outlets');
      if (t.length > 60 && n.parentElement && !n.parentElement.closest('#cal, .sday, .fd, .kmatrix, #plan .when')) {
        t = t.replace(new RegExp('(\\b(?:on|is|opens|starts|ends|from) )' + T + '\\b', 'g'), '$1today').replace(new RegExp('(\\b(?:on|is|opens|starts|ends|from) )' + M + '\\b', 'g'), '$1tomorrow');
      }
      if (t !== o) n.nodeValue = t;
    }
  });

  // 14. Alfred plans the day: one judgement, then the day in time order, built
  // from the rest of the edition (calendar, shades, the sun, the sky, the game).
  step('alfred', () => {
    const brief = $('#brief'); if (!brief) return;
    const mins = s => { s = (s || '').toLowerCase().trim(); if (s === 'noon') return 720;
      const m = s.match(/(\d{1,2})(?::(\d\d))?\s*(?:([ap])m?)?(?:\s*[–-]\s*\d{1,2}(?::\d\d)?\s*([ap])m?)?/); if (!m || !(m[3] || m[4])) return null;
      let h = +m[1] % 12; if ((m[3] || m[4]) === 'p') h += 12; return h * 60 + (+m[2] || 0); };
    const label = n => { const h = Math.floor(n / 60), mm = n % 60; if (n === 720) return 'Noon';
      return `${h % 12 || 12}${mm ? ':' + String(mm).padStart(2, '0') : ''} ${h < 12 ? 'am' : 'pm'}`; };
    const nowM = (() => { const d = new Date(new Date().toLocaleString('en-US', {timeZone: 'America/Los_Angeles'})); return d.getHours() * 60 + d.getMinutes(); })();
    const plan = [];
    const add = (t, text) => { if (t !== null && t >= nowM - 30 && text) plan.push([t, text]); };
    // Calendar, today.
    const day = $$('#cal h3.cal-day').find(h => /^Today$/i.test(txt(h)));
    const calRows = day && day.nextElementSibling ? [...day.nextElementSibling.children] : [];
    let gameInCal = false;
    for (const r of calRows) { const t = txt(r.firstElementChild).replace(/\s*(Moda Center|Video call)$/, ''), w = txt(r.lastElementChild);
      if (/Blazers|Timbers/.test(t)) { gameInCal = true; continue; }
      add(mins(w), t); }
    // The game, with the channel.
    for (const k of $$('.kscore')) { const nx = [...k.children].find(d => /Next/.test(txt(d.querySelector('.k'))));
      if (nx && /^(Tonight|Today)/.test(txt(nx.querySelector('b')))) {
        const team = txt(k.closest('.card') && k.closest('.card').querySelector('h2')).replace(/^Portland (Trail Blazers|Timbers|Thorns)/, '$1');
        const parts = txt(nx.querySelector('small')).replace(/^vs\.? /, 'v. ').split(' · ');
        add(mins(txt(nx.querySelector('b')).replace(/^(Tonight|Today) /, '')), `${team} ${parts[0]}${parts[1] ? ', on ' + parts[1].split(',')[0] : ''}`); } }
    // Shades, today.
    const sd = $('#shades .shade-day');
    if (sd) for (const b of sd.querySelectorAll('.shade-step b')) { const m = txt(b).match(/^(.*?) at (\d{1,2}(?::\d\d)? [ap]m|noon)$/i);
      if (m) add(mins(m[2]), m[1].replace(/^Open sunny-side shades$/i, 'Open the sunny-side shades').replace(/^Close all shades$/i, 'Close the shades to hold the warmth')); }
    // Sun for the big loads.
    const ld = $('#loads .load'), lb = ld && txt(ld.querySelector('b'));
    const lm = lb && lb.match(/(\d{1,2}(?::\d\d)? ?[ap]m|noon)\s*[–-]\s*(\d{1,2}(?::\d\d)? ?[ap]m|noon)/i);
    if (lm) add(mins(lm[1]), `Dishwasher, laundry, the car: the panels cover it until ${lm[2].replace(/ ?([ap])m/, ' $1m')}`);
    // Warmest hour.
    const hot = $('.khr .hot');
    if (hot) add(mins(txt(hot.querySelector('span')).replace(/^(\d+)([ap])$/i, '$1 $2m')), `Warmest hour, ${txt(hot.querySelector('b'))}: a good time outside with the little one`);
    // Sunset and the sky.
    const ss = $$('#out-facts > div, #out-facts .f').find(d => /^Sunset/i.test(txt(d)));
    const sst = ss && txt(ss).match(/(\d{1,2}:\d\d [ap]m)/);
    if (sst) add(mins(sst[1]) - 15, 'Look west: the sun sets at ' + sst[1]);
    const iss = $$('#sats > div, #sats .lines > div').find(r => /Good/.test(txt(r)) && txt(r).includes(new Date().toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric'})));
    const im = iss && txt(iss).match(/at (\d{1,2}:\d\d [ap]m)[^,]*?(\d+ min), (from the [A-Z]+)/);
    if (im) add(mins(im[1]), `The space station passes over, ${im[3]}, for ${im[2]}`);
    plan.sort((a, b) => a[0] - b[0]);
    // The judgement: what kind of day, and what is coming.
    const fds = $$('#forecast .fd'), kwh = f => +(txt(f.querySelector('.e')).match(/\d+/) || [0])[0];
    const rain = f => +(txt(f.querySelector('.r')).match(/(\d+)%/) || [0, 0])[1];
    let say = '';
    if (fds.length > 3) {
      const t0 = fds[0], best = Math.max(...fds.map(kwh)), wet = fds.slice(1).filter(f => rain(f) >= 70).map(f => txt(f.querySelector('.d')));
      if (kwh(t0) >= best && rain(t0) < 40) say = 'Today is the pick of the week, sir: the driest and sunniest day we will see.';
      else if (rain(t0) >= 70) say = 'A wet one today, sir. Indoor plans are wise.';
      else say = 'A fair day, sir.';
      if (wet.length) say += ` Rain settles in ${wet.length > 1 ? `from ${wet[0]} to ${wet[wet.length - 1]}` : 'on ' + wet[0]}, so anything outdoors belongs to ${kwh(t0) >= best ? 'today' : 'the dry days'}.`;
    }
    const smoke = [...brief.querySelectorAll('li')].find(li => /Smoke is forecast tomorrow/i.test(txt(li)));
    if (smoke) { say += ' Smoke arrives tomorrow; I shall keep the windows shut.'; kill(smoke); }
    kill(brief.querySelector('.brief-intro'));
    // Lines the plan now carries.
    for (const li of brief.querySelectorAll('ul li')) if (plan.some(([, x]) => /Blazers|Timbers|Vikings|Pilots/.test(x) && /Blazers|Timbers|Vikings|Pilots/.test(txt(li)) && (txt(li).match(/Blazers|Timbers|Vikings|Pilots/) || [''])[0] && x.includes((txt(li).match(/Blazers|Timbers|Vikings|Pilots/) || [''])[0]))) kill(li);
    const v = document.createElement('p'); v.className = 'kverdict kalfred'; v.textContent = say.trim();
    const ol = document.createElement('ol'); ol.className = 'kplan';
    ol.innerHTML = plan.map(([t, x]) => `<li><span class="kt">${label(t)}</span><span>${x}</span></li>`).join('');
    const head = brief.querySelector('.brief-head') || brief.querySelector('h2');
    for (const ul of brief.querySelectorAll('ul')) if (!ul.querySelector('li')) { const h = ul.previousElementSibling; if (h && h.tagName === 'H3') kill(h); kill(ul); }
    if (head) { head.after(v); if (plan.length) { const lab = document.createElement('h3'); lab.className = 'sub'; lab.textContent = 'The day, as I would arrange it'; v.after(lab); lab.after(ol); } }
  });

  // 15. Final desk: the sign-off list.
  step('final', () => {
    // River: a stale crest sentence goes whole.
    for (const el of $$('#columbia-card p, #columbia-summary, #columbia-card .summary')) {
      const t = el.textContent.replace(/\s*The NWS forecast tops out at \d+(?:\.\d+)? ft [^]*?stage\.(?=\s|$)/i, m => {
        const d = m.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})/); if (!d) return m;
        const dd = new Date(`${d[1]} ${d[2]}, ${new Date().getFullYear()}`), t0 = new Date(); t0.setHours(0, 0, 0, 0); return dd < t0 ? '' : m; });
      if (t !== el.textContent) el.textContent = t;
    }
    // Volcano line.
    for (const el of [...$$('#volc'), ...$$('#volc *')]) if (!el.children.length) el.textContent = el.textContent.replace(/Under the volcanoes: (.+?) (\d+)\./, (m, v, n) => `${n} small quake${n === '1' ? '' : 's'} under ${v} this week.`);
    // Standings: the table is the truth.
    for (const card of $$('.card')) {
      const rank = [...card.querySelectorAll('.lines>div')].find(d => /\d+(st|nd|rd|th) of \d+/.test(txt(d)));
      const meta = card.querySelector('.head .meta, .team-top .meta');
      if (rank && meta) meta.textContent = meta.textContent.replace(/ · \d+(st|nd|rd|th) in .+$/, '');
      if (meta && /Timbers|Thorns/.test(txt(card.querySelector('h2')))) { const m = txt(meta).match(/^(\d+)-(\d+)-(\d+)\b/);
        if (m) meta.textContent = txt(meta).replace(/^\d+-\d+-\d+/, `${m[1]}W ${m[3]}L ${m[2]}D`); }
    }
    $$('.card small, .card p').filter(s => /^Goals:/.test(txt(s))).forEach(kill);
    // Stale night and surf-zone rows.
    const dow = new Date().toLocaleDateString('en-US', {weekday: 'short', timeZone: 'America/Los_Angeles'});
    const nr = $$('#nights>div');
    if (nr[1] && new RegExp('^' + dow + ' night').test(txt(nr[1].querySelector('b') || nr[1]))) { kill(nr[0]); const b = nr[1].querySelector('b'); if (b) b.textContent = 'Tonight'; }
    const longDow = new Date().toLocaleDateString('en-US', {weekday: 'long', timeZone: 'America/Los_Angeles'});
    const zs = $$('#surfzone .mini, #surfzone > div');
    if (zs.length > 1 && zs.slice(1).some(z => new RegExp('^' + longDow).test(txt(z.querySelector('b, .k') || z))) && /^Today/.test(txt(zs[0].querySelector('b, .k') || zs[0]))) {
      kill(zs[0]); for (const z of zs.slice(1)) { const b = z.querySelector('b, .k'); if (b && new RegExp('^' + longDow).test(txt(b))) b.textContent = b.textContent.replace(longDow, 'Today'); }
    }
    for (const r of $$('#nights>div')) if (/Clouded out/.test(txt(r))) { const sm = r.querySelector('small'); if (sm) kill(sm); }
    // Doubled stories and shows.
    const key = s => new Set((s.match(/\b[A-Z][a-z]{4,}\b/g) || []).map(w => w.toLowerCase()));
    for (const box of $$('#stories, #bignews, #localnews')) { const seen = [];
      for (const s of box.querySelectorAll('.story')) { const k = key(txt(s.querySelector('b')));
        if (seen.some(x => { let n = 0; for (const w of k) if (x.has(w)) n++; return n >= 2; })) kill(s); else seen.push(k); } }
    const js = new Set();
    for (const r of $$('#jazz > *')) { const b = r.querySelector('b'); if (!b) continue;
      const k = txt(b).toLowerCase().replace(/\W+/g, ' ').trim().split(' ').slice(0, 2).join(' ');
      if (js.has(k) && !/mel brown|chuck israels/.test(k)) kill(r); else js.add(k); }
    // Web chrome: inline source lines and link rows.
    $$('small, .cite, p.note, p, span').filter(e => !e.children.length && /^Sources?:/.test(txt(e))).forEach(kill);
    for (const p of $$('p.note, small, p')) if (p.children.length <= 3 && /^Sources?:/.test(txt(p))) kill(p);
    for (const p of $$('.note')) if (!p.children.length) p.textContent = p.textContent.replace(/\s*Source: .*$/, '');
    kill($('#ski-links'));
    for (const p of $$('.note, p, div')) if (p.isConnected && txt(p).length < 140 && /^(Check (seasons|your registration)|Razor clam seasons|Lifts and grooming:)/.test(txt(p))) kill(p);
    for (const a of $$('a, span')) if (a.isConnected && /^(About the album|Email|Site|Contact)$/.test(txt(a))) {
      const prev = a.previousSibling; if (prev && prev.nodeType === 3) prev.nodeValue = prev.nodeValue.replace(/\s*·\s*$/, ''); kill(a); }
    for (const el of $$('section.group small, section.group span, section.group p')) if (!el.children.length && /·\s*$/.test(el.textContent)) el.textContent = el.textContent.replace(/\s*·\s*$/, '');
    const sun = $('#sunact-card') || $('#sun-card');
    if (sun && !sun.querySelector('img')) for (const el of sun.querySelectorAll('p, small')) if (!el.children.length) el.textContent = el.textContent.replace(/The picture is[^.]*\.\s*/, '');
    // Rows.
    for (const r of $$('#openings .lines>div, #restaurants .lines>div')) if (/Not named/.test(txt(r)) && !txt(r).replace(/Not named,?/, '').trim()) kill(r);
    for (const el of $$('#openings *, #restaurants *')) if (!el.children.length) el.textContent = el.textContent.replace(/Not named, /, '').replace(/(.{6,}?) · \1/, '$1');
    for (const el of $$('#restaurants small')) el.innerHTML = el.innerHTML.replace(/(<span>[^<]*<\/span>: [^·<]+)\s*·\s*\1/, '$1');
    for (const s of $$('#good .story, #good > div')) if (/East Hampton|Connecticut|Maine|Wangunk/.test(txt(s))) kill(s);
    for (const r of $$('#kid-out .story, #kid-out > div')) { const b = r.querySelector('b'); if (b && txt(r) === txt(b)) kill(r); }
    // Copy nits.
    for (const el of $$('#fires *, #fire-card *')) if (!el.children.length) el.textContent = el.textContent.replace(/^\d{3,4} (?=[A-Z])/, '').replace(/\bMc([a-z])/g, (m, c) => 'Mc' + c.toUpperCase());
    for (const el of $$('.bday small')) el.textContent = el.textContent.replace(/(turns (\d+) today) \2$/, '$1');
    for (const r of $$('#reps .story, #reps .lines>div, #reps a')) if (/^[SH]D-\d+ — Oregon/.test(txt(r))) kill(r);
    const tnow = $('#t-now');
    for (const t of $$('.tile')) if (/^Produced today/i.test(txt(t.querySelector('.k'))) && /^0\.0/.test(txt(t.querySelector('.v, b, strong') || t).replace(/^Produced today\s*/i, ''))) {
      const v = t.querySelector('.v') || t.querySelector('b'); if (v) v.innerHTML = 'Not reported yet'; }
    // Long lists: about eight, the next three weeks first.
    for (const sel of ['#big', '#liquor']) { const box = $(sel); if (box) [...box.children].filter(c => !/^H\d$/.test(c.tagName)).slice(8).forEach(kill); }
    const jz = $$('#jazz > *').filter(r => r.querySelector('b')); jz.slice(12).forEach(kill);
    const also = $('.kalso'); if (also) { const items = also.innerHTML.split(' · '); if (items.length > 8) also.innerHTML = items.slice(0, 8).join(' · ') + ` · and ${items.length - 8} more`; }
  });

}
"""

# Runs in the rendered page: strip it down to static HTML and split it up.
EXTRACT = r"""
() => {
  const abs = u => { try { return new URL(u, location.href).href } catch (e) { return u } };
  // Chrome 75 has no flex gap: write the spacing as margins.
  for (const el of document.querySelectorAll('body *')) { const c = getComputedStyle(el); if (!/flex/.test(c.display)) continue;
    const cg = parseFloat(c.columnGap) || 0, rg = parseFloat(c.rowGap) || 0; if (!cg && !rg) continue;
    const col = /column/.test(c.flexDirection); let prev = null;
    for (const k of el.children) { const kc = getComputedStyle(k); if (kc.display === 'none' || kc.position === 'absolute') continue;
      if (prev) { if (col || k.offsetTop > prev.offsetTop + 2) { if (rg) k.style.setProperty('margin-top', (parseFloat(kc.marginTop) + rg) + 'px', 'important'); }
        else if (cg) k.style.setProperty('margin-left', (parseFloat(kc.marginLeft) + cg) + 'px', 'important'); }
      prev = k; }
    el.style.setProperty('gap', '0', 'important'); }
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

/* ===== PROTO: art-director review ===== */
:root{--hair:#5c5c5c;--k-hair:#5c5c5c;--ink2:#222;--k-grey:#222}
/* Cover */
.kcontents #kmain .kmast{padding:4px 0 0}
.kcontents #kmain .kear{display:flex;justify-content:space-between;align-items:baseline;font:600 13px/16px var(--k-serif);letter-spacing:.12em;text-transform:uppercase;margin:0 0 6px}
.kcontents #kmain .kname{font:700 50px/52px var(--k-serif) !important;letter-spacing:-.02em;margin:0 0 10px !important}
.kcontents #kmain .kdate{border-top:4px solid #000;border-bottom:1px solid #000;margin:0 0 18px !important;padding:7px 0 !important}
.kcontents #kmain .kgl{border-bottom:2px solid #000;margin:0 0 16px;padding:0 0 12px}
.kcontents #kmain .kgl .kdeg{width:150px;font:700 76px/0.9 var(--k-serif)}
.kcontents #kmain .kgl li{font:430 16px/21px var(--k-serif);padding:6px 0 !important}
.kcontents #kmain .kgl li b{display:block;margin:0 0 1px}
.kcontents #kmain .klab{border-top:0;padding:0 !important;margin:0 0 4px !important}
.kcontents #kmain .kleads a{padding:9px 0 10px}
.kcontents #kmain .kleads a:first-child b{font:700 26px/31px var(--k-serif)}
.kcontents #kmain .kleads small{margin:0 0 2px}
.kcontents #kmain .kpart{margin:10px 0 0 !important}
.kcontents #kmain .kpartbox a{padding:6px 0 5px !important}
/* Section fronts */
.ksecfront #kmain .kfhead{display:flex;align-items:flex-end;border-bottom:4px solid #000;padding:0 0 10px;margin:8px 0 0}
.ksecfront #kmain .kfhead>div{-webkit-box-flex:1;flex:1 1 auto;min-width:0}
.ksecfront #kmain .kfnum{flex:none;font:700 120px/88px var(--k-serif);letter-spacing:-.05em;font-variant-numeric:lining-nums;margin:0 0 -2px 16px}
.ksecfront #kmain .kfsub{border-bottom:0;padding:0 !important}
.ksecfront #kmain .kfl .kt b{white-space:normal}
.ksecfront #kmain .kfl .kt small{display:block !important;font:italic 430 15px/20px var(--k-serif);color:#222 !important;margin-top:2px}
.ksecfront #kmain .kfl a{padding:10px 0 !important}
/* Album birthdays */
#kmain .bday{display:flex !important;align-items:center;padding:9px 0 !important;border-bottom:1px solid var(--hair) !important}
#kmain .bday>span:first-child{flex:1 1 auto !important;display:block !important;min-width:0}
#kmain .bday>span:first-child b{display:block;font:680 var(--t4)/var(--l4) var(--k-serif) !important}
#kmain .bday>span:first-child small{display:block;font:italic 430 var(--t5)/var(--l5) var(--k-serif) !important}
#kmain .bday .age{flex:none !important;display:block !important;min-width:64px;text-align:right;padding:0 0 0 16px !important;color:#000 !important;font:700 30px/30px var(--k-serif) !important;font-variant-numeric:lining-nums}
#kmain .bday .age::after{content:"years";display:block;font:600 13px/16px var(--k-serif);letter-spacing:.12em;text-transform:uppercase;opacity:1}
/* Markets quote board */
#kmain #mkt{display:grid !important;grid-template-columns:repeat(12,1fr);border-top:3px solid #000 !important;border-bottom:1px solid #000 !important;margin:4px 0 14px !important}
#kmain #mkt>div{display:block !important;grid-column:span 4;border:0 !important;padding:8px 8px 10px 0 !important}
#kmain #mkt>div:nth-child(n+4){grid-column:span 3;border-top:1px solid var(--hair) !important}
#kmain #mkt>div+div:not(:nth-child(4)){border-left:1px solid var(--hair) !important;padding-left:10px !important}
#kmain #mkt>div>span:first-child{display:block;font:600 13px/16px var(--k-serif) !important;letter-spacing:.1em;text-transform:uppercase}
#kmain #mkt>div>span:last-child{display:block !important;max-width:none !important;padding:0 !important;text-align:left !important;font:700 26px/30px var(--k-serif) !important;font-variant-numeric:lining-nums tabular-nums}
#kmain #mkt>div:nth-child(n+4)>span:last-child{font-size:19px !important;line-height:24px !important}
#kmain #mkt .up,#kmain #mkt .down{display:block;font:600 15px/19px var(--k-serif) !important}
#kmain #mkt .up::before{content:"\25B2\00A0";font-size:11px} #kmain #mkt .down::before{content:"\25BC\00A0";font-size:11px}
#kmain #mkt-spark{margin:0 0 6px}
.kcontents #kmain .kname{font-size:46px !important;line-height:48px !important;margin:0 0 8px !important}
.kcontents #kmain .kdate{margin:0 0 14px !important}
.kcontents #kmain .kgl{padding:0 0 8px;margin:0 0 12px}
.kcontents #kmain .kgl li{padding:4px 0 !important}
.kcontents #kmain .kleads a{padding:7px 0 8px}
.kcontents #kmain .kleads a:first-child b{font:700 24px/29px var(--k-serif)}
.kcontents #kmain .kpartbox a{padding:4px 0 3px !important}
.kcontents #kmain .kpart{margin:8px 0 0 !important}
.kcontents #kmain .ktochead{margin:0 0 6px !important}
#kmain #tv{display:grid !important;grid-template-columns:1fr 1fr;grid-column-gap:22px}
#kmain #tv>.day-h{grid-column:1 / -1}
#kmain #tv>.story{padding:8px 0 !important}
#kmain #tv>.story b{font-size:17px !important;line-height:22px !important}
#kmain #tv>.story small{font-size:14px !important;line-height:19px !important}
#kmain #tv .pill{display:block;font-size:13px !important}
#kmain #tv .pill::before{content:none}

.kcontents #kmain .kgl{display:flex;align-items:center}
.kcontents #kmain .kgl .kdeg small{display:block;font:600 13px/16px var(--k-serif);letter-spacing:.1em;text-transform:uppercase;margin-top:6px}
.kcontents #kmain .kwx{flex:1 1 auto;margin:0 0 0 18px !important;font:italic 430 18px/26px var(--k-serif)}
.kcontents #kmain .kpart a{color:#000 !important;text-decoration:underline}
.kcontents #kmain .kc{font:italic 430 13px/16px var(--k-serif) !important}
#kmain .kbrief{border-top:1px solid #000;margin-top:16px !important;padding-top:12px}
#kmain h3.kfold{font:700 var(--t3)/var(--l3) var(--k-serif) !important;margin:0 0 6px !important;text-transform:none !important;letter-spacing:0 !important;border:0 !important;padding:0 !important}
#kmain .kbrief .head{display:block}
#kmain .kbrief .meta{display:block;font:italic 430 13px/16px var(--k-serif) !important}
#kmain .kcredits h3{font:600 13px/16px var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase;margin:14px 0 2px !important}
#kmain .kcredits p{font:italic 430 15px/21px var(--k-serif) !important;margin:0 !important}
#kmain .kcredits a{text-decoration:none !important}
#kmain .chips:empty{display:none !important}
#kmain small,#kmain .meta{font-weight:480 !important}



/* Data pages */
#kmain .kverdict{font:600 18px/26px var(--k-serif) !important;color:#000 !important;margin:8px 0 12px !important}
#kmain table.kmatrix{width:100%;table-layout:fixed;border-collapse:collapse;border-top:1px solid #000;margin:12px 0 10px}
#kmain .kmatrix thead th{font:600 13px/16px var(--k-serif) !important;letter-spacing:.08em;text-transform:uppercase;text-align:left;padding:6px 4px}
#kmain .kmatrix thead th:first-child{width:104px}
#kmain .kmatrix tbody th{font:700 15px/19px var(--k-serif) !important;text-align:left;vertical-align:top;padding:8px 6px 8px 0;border-top:1px solid #000}
#kmain .kmatrix td{vertical-align:top;padding:7px 4px;border-top:1px solid #000}
#kmain .kmatrix td.q4{outline:2px solid #000;outline-offset:-2px}
#kmain .kmatrix td b,#kmain .kmatrix td span,#kmain .kmatrix td small,#kmain .kq{display:block}
#kmain .kmatrix td b{font:600 13px/16px var(--k-serif) !important;letter-spacing:.06em;text-transform:uppercase}
#kmain .kmatrix td.q1 b{font-weight:400 !important;font-style:italic}
#kmain .kmatrix td span{font:700 15px/19px var(--k-serif) !important;font-variant-numeric:tabular-nums}
#kmain .kmatrix td small{font:italic 430 13px/16px var(--k-serif) !important}
#kmain .kq{margin:0 0 3px}
#kmain .kq i{display:inline-block;width:9px;height:9px;margin-right:2px;border:1px solid #000;background:#fff}
#kmain .kq i.on{background:#000 !important}
#kmain .kkey{font:italic 430 13px/18px var(--k-serif) !important}
#kmain .khr{display:flex;align-items:flex-end;border-top:1px solid #000;border-bottom:1px solid #000;padding:8px 0;margin:12px 0}
#kmain .khr>div{flex:1 1 0;text-align:center}
#kmain .khr b{display:block;font:680 17px/20px var(--k-serif) !important}
#kmain .khr i{display:block;width:55%;margin:4px auto;background:#5a5a5a}
#kmain .khr .hot i{background:#000}
#kmain .khr .hot b{text-decoration:underline}
#kmain .khr span{display:block;font:600 13px/16px var(--k-serif) !important;letter-spacing:.06em;text-transform:uppercase}
#kmain #out-facts .v small{display:inline !important;font:430 13px/16px var(--k-serif) !important;margin-left:4px}
#kmain .kscore{display:flex;border-top:2px solid #000;border-bottom:1px solid #000;margin:10px 0 12px}
#kmain .kscore>div{flex:1 1 0;padding:8px 10px 8px 0}
#kmain .kscore>div+div{border-left:1px solid #000;padding-left:12px}
#kmain .kscore .k{display:block;font:600 13px/16px var(--k-serif) !important;letter-spacing:.12em;text-transform:uppercase}
#kmain .kscore b{display:block;font:700 26px/32px var(--k-serif) !important;font-variant-numeric:tabular-nums}
#kmain .kscore small{display:block;font:italic 430 14px/19px var(--k-serif) !important}
#kmain #bill .progress{border:1px solid #000 !important;height:10px !important;background:#fff !important}
#kmain #bill .progress>div,#kmain #bill .progress>i{height:100% !important;background:#000 !important}
#kmain .kbx{display:table;width:100%;table-layout:fixed}
#kmain .kbx span{display:table-cell;text-align:center;font:600 13px/16px var(--k-serif) !important}
#kmain .kbv{display:block;font:700 13px/16px var(--k-serif) !important;text-align:center;margin-bottom:2px;white-space:nowrap}
#kmain .kmix>div{display:table;width:100%;padding:6px 0;border-bottom:1px solid #000}
#kmain .kmix span,#kmain .kmix em,#kmain .kmix b{display:table-cell;vertical-align:middle}
#kmain .kmix span{width:170px;font:430 15px/20px var(--k-serif) !important}
#kmain .kmix b{width:52px;text-align:right;font:700 15px var(--k-serif) !important}
#kmain .kmix em{padding-right:8px}
#kmain .kmix i{display:block;height:12px;background:#000}
#kmain .kmix .fossil i{background:#5a5a5a}
#kmain .kbignum{font:italic 430 17px/24px var(--k-serif) !important;margin:6px 0 10px !important}
#kmain .kbignum b{font:700 44px/48px var(--k-serif) !important;font-style:normal;margin-right:8px}

/* Alfred's plan for the day */
#kmain .kalfred{font:italic 430 19px/28px var(--k-serif) !important;margin:10px 0 14px !important}
#kmain ol.kplan{list-style:none !important;padding:0 !important;margin:0 0 12px !important;border-top:2px solid #000}
#kmain ol.kplan li{display:table;width:100%;border-bottom:1px solid #000;padding:8px 0 !important;margin:0 !important}
#kmain ol.kplan li::before{display:none !important;content:none !important}
#kmain ol.kplan .kt{display:table-cell;width:5.2em;font:700 16px/22px var(--k-serif) !important;font-variant-numeric:tabular-nums;vertical-align:top}
#kmain ol.kplan .kt+span{display:table-cell;font:430 17px/24px var(--k-serif) !important}
#kmain ul.kplain{margin:4px 0 0 !important;padding:0 0 0 18px !important}
#kmain .kalso{font:430 15px/22px var(--k-serif) !important}

/* Final sign-off */
html.kfit4{--s2:8px;--s3:14px;--l4:22px;--l5:19px}
html.kfit4 #kmain .story,html.kfit4 #kmain .lines>div,html.kfit4 #kmain .fd,html.kfit4 #kmain .sday,html.kfit4 #kmain .rep,html.kfit4 #kmain li{padding-top:5px !important;padding-bottom:5px !important}
.ksecfront #kmain .kfl.ktight a{padding:6px 0 !important}
.ksecfront #kmain .kfl.ktight .kt small{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ksecfront #kmain .kfl.kcompact .kt small{display:none !important}
#kmain .bars>div{position:relative}
#kmain .bars .kbv{position:absolute;left:-14px;right:-14px;margin:0 0 2px !important}
#kmain #bill .bars{margin-top:22px !important}
#kmain .sw,#kmain .legend i{width:12px;height:12px}
#kmain .ksw0{background:#000 !important}
#kmain .ksw1{background:#fff !important;border:2px solid #000;box-sizing:border-box}
.kcontents #kmain .kt{white-space:normal !important;line-height:20px}
.kcontents #kmain .kgl .kdeg{display:flex;align-items:flex-end;width:auto}
.kcontents #kmain .kgl .kdeg small{margin:0 0 10px 16px !important;font-size:15px !important}
#kmain .book img{display:none !important}
#kmain .arch-img,#kmain .card img.photo{max-height:330px;width:auto;max-width:100%}
/* Controls a finger can hit */
html body .krun{height:44px !important;padding:16px 0 6px !important;cursor:pointer}
.kbar #kmore{height:44px !important;padding:13px 16px !important}
.ksecfront #kmain .kfl a{padding:12px 0 !important}
/* Section list from the running head */
#kjump{display:none}
html.kjumpopen #kjump{display:block;position:absolute;left:24px;right:24px;top:44px;bottom:52px;background:#fff;z-index:50;
  border-top:4px solid #000;-webkit-column-count:2;column-count:2;-webkit-column-gap:24px;column-gap:24px;padding-top:8px}
#kjump a{display:block;min-height:44px;line-height:44px;border-bottom:1px solid #000;font:430 17px/44px var(--k-serif);color:#000;text-decoration:none;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;-webkit-column-break-inside:avoid;break-inside:avoid}
.ksecfront #kmain .kfl .kt b{white-space:normal !important;overflow:visible !important;text-overflow:clip !important}
/* The navigator: skip a section, jump to a page or any section */
.krun .ksecbtn{display:inline-block;margin-left:12px;border:1px solid #000;padding:5px 8px 4px;margin-top:-6px;font:600 12px/1 var(--k-serif);
  letter-spacing:.12em;text-transform:uppercase;vertical-align:baseline}
html.kjumpopen .krun .ksecbtn{background:#000;color:#fff}
html.kjumpopen #kjump{display:block;position:absolute;left:24px;right:24px;top:44px;bottom:52px;background:#fff;z-index:50;
  border-top:4px solid #000;-webkit-column-count:auto;column-count:auto;padding-top:10px;overflow:hidden}
#kjump .kjtop{display:flex;margin:0 0 4px}
#kjump .kjtop a{display:block;border:2px solid #000;padding:7px 12px 8px;min-height:0;line-height:22px;font:700 18px/22px var(--k-serif);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
#kjump .kjtop small{display:block;font:600 11px/14px var(--k-serif);letter-spacing:.12em;text-transform:uppercase}
#kjump .kjskip{-webkit-box-flex:1;flex:1 1 auto;min-width:0;background:#000;color:#fff !important}
#kjump .kjskip small{color:#fff !important}
#kjump .kjfront{flex:none;margin-left:10px !important;font-weight:500 !important}
#kjump .kjh{font:600 11px/14px var(--k-serif);letter-spacing:.14em;text-transform:uppercase;margin:14px 0 0 !important;border-bottom:1px solid #000;padding-bottom:4px !important}
#kjump .kjg{display:flex;flex-wrap:wrap}
#kjump .kjg a{width:50%;box-sizing:border-box;padding-right:12px;min-height:0;height:31px;line-height:31px;font:430 16px/31px var(--k-serif);
  border-bottom:1px solid #bbb}
#kjump .kjg a i{display:inline-block;width:26px;font:600 12px/31px var(--k-serif);font-style:normal}
#kjump .kjg a.kjcur{font-weight:700}
#kjump .kjg a.kjcur i:before{content:'\25B8 '}
/* Pick up where you stopped */
.kcontents #kmain .kresume{display:block;border:2px solid #000;padding:8px 14px;margin:0 0 14px;color:#000;text-decoration:none}
.kcontents #kmain .kresume small{display:block;font:600 13px/16px var(--k-serif);letter-spacing:.12em;text-transform:uppercase}
.kcontents #kmain .kresume b{font:700 19px/26px var(--k-serif)}
/* The end */
#kmain .kend .kfname{font-size:40px !important;line-height:46px !important;margin-top:40px !important}
#kmain .kend .kbig{display:block;border:2px solid #000;text-align:center;font:700 20px/56px var(--k-serif);margin:24px 0;color:#000;text-decoration:none}
#kmain .kendl{-webkit-column-count:2;column-count:2;-webkit-column-gap:24px;column-gap:24px;padding:0;margin:0;list-style:none}
#kmain .kendl li{-webkit-column-break-inside:avoid;break-inside:avoid}
#kmain .kendl a{display:block;line-height:40px;border-bottom:1px solid #000;color:#000;text-decoration:none;font:430 16px/40px var(--k-serif)}
#kmain .kendsrc{margin-top:18px !important;font:italic 430 15px/20px var(--k-serif)}

/* Bottom bar: one 52px row */
.kbar{display:none}
html.kpaged,html.kpaged body{height:100% !important;overflow:hidden !important;overscroll-behavior:none;touch-action:none;-webkit-tap-highlight-color:rgba(0,0,0,0)}
html.kpaged body{display:flex !important;flex-direction:column !important;padding-bottom:0 !important}
html.kpaged .krun{flex:none}
html.kpaged #kview{flex:none;position:relative;overflow:hidden}
html.kpaged #kclip{position:relative;overflow:hidden}
html.kpaged #kmain{position:relative;top:0;display:flow-root}
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
# The designer layer: shared engraved kit plus Morning Edition rules scoped to html.kme.
EINK_CSS += kindle_orn.DESIGN_CSS

# Performance layer (kindle_full_perf): the card moves on its own layer; art boxes are fixed-size and contained.
EINK_CSS += """
html.kpaged body #kmain{will-change:transform}
.kart{display:block;margin:0 auto;contain:strict;overflow:hidden}
"""
# How the data is presented (answer first, statuses, one .kpanel per text block): last, so it governs.
EINK_CSS += kindle_present.CSS

PAGER_JS = r"""
<script>
/* The Morning Edition pager, written for the Paperwhite 11 browser (Chrome 75, ES5).
   No scrolling: each card is cut into screen-sized sheets at whole-item
   boundaries and shown one sheet at a time.
   Right tap or swipe left: the next sheet, then the next page.
   Left tap or swipe right: back. The bar's right link skips to the next page. If anything here fails the page is left as a plain page. */
(function(){
  var NEXT_URL = __NEXT__, PREV_URL = __PREV__, busy = false, store = {};
  try { store = window.sessionStorage || {}; } catch (e) {}
  var FLOW = /\b(kcontents|ksecfront)\b/.test(document.body.className);
  var root = document.documentElement, kview = document.getElementById('kview');
  var view = document.getElementById('kclip'), main = document.getElementById('kmain');
  var more = document.getElementById('kmore'), pos = document.getElementById('kpos');
  var kcont = document.getElementById('kcont'), rail = document.getElementById('krail');
  var run = document.querySelector('.krun'), bar = document.querySelector('.kbar'), st = root.style;
  if (!view || !main || !kview || !bar || !window.getComputedStyle || !('flexBasis' in st || 'webkitFlexBasis' in st)) return;
  var lastBoxes = null, lastSig = '', cuts = [0], tops = [0], heads = [], brk = [], sheet = 0, H = 0, C = 0, turns = 0, timer = 0, FLASH_EVERY = 6, hashDone = false;
  var knx = document.querySelector('.kbar .knx'), knxLabel = knx ? knx.innerHTML : '';
  var UNITS = '.kleads>a,.kresume,.kbrief,.sp,.bday,.deal,.mush,.rep-head,.story,.lines>div,li,.fd,.sday,.brk,.rec,.idea,.book,.book-today,.rep,.recap,.mini,.tile,.tiles,.facts,figure,img,svg,.bars,.rain,.vote,.poem-text>span,h3,.sub,.day-h,.cal-day,.kscore,table,tr,.allclear,.krail,.kgl,.kchart,.kpanel,.krow';
  var TITLE = (function(){ var h = main.querySelector('h2,.sci-title,.poem-title'); return h ? (h.textContent || '').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '') : document.title; })();
  function on() { return (' ' + root.className + ' ').indexOf(' kpaged ') >= 0; }
  function cls(name, v) { root.className = root.className.replace(new RegExp('(^|\\s)' + name + '(?=\\s|$)', 'g'), '') + (v ? ' ' + name : ''); }
  function blockish(el) { var d = window.getComputedStyle(el).display; return d !== 'inline' && d !== 'none' && d !== 'contents'; }
  function txt(el) { return (el.textContent || '').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, ''); }
  function boxes() {
    var all = main.getElementsByTagName('*'), ls = [], us = [], hs = [], lb = 0, base = main.getBoundingClientRect().top;
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.ownerSVGElement) continue;          // an engraving is one box: never walk its paths
      if (el.ownerSVGElement || !blockish(el)) continue;
      var r = el.getBoundingClientRect();
      if (r.height <= 0) continue;
      var top = r.top - base, bottom = r.bottom - base, tag = el.tagName.toUpperCase();
      var isHead = /^(H3|H4|SUMMARY)$/.test(tag) || /\b(cal-day|day-h|sub|shelf-h|rep-head|kkick|kkicker|klab|kpart|rec-k|sci-topic)\b/.test(el.className || '');
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
          if (!seen[lbt] && lbt < bottom - 2) { seen[lbt] = 1; ls.push({ top: Math.round(lr[m].top - base), bottom: lbt, head: false }); } }
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
  var LADDER = ['', 'kfit1', 'kfit1 kfit2', 'kfit1 kfit2 kfit3', 'kfit1 kfit2 kfit3 kfit4'];
  function fits() { if (drawn() > H) return false; var b = boxes(); var off = main.getBoundingClientRect().top - view.getBoundingClientRect().top; return !b.lb || b.lb + off + 4 <= H && main.scrollHeight + off <= H + 2; }
  function fit() {
    cls('kfit1', false); cls('kfit2', false); cls('kfit3', false); cls('kfit4', false); main.style.zoom = '';
    if (rail) rail.style.display = 'none';
    if (FLOW) { var kfl = main.querySelector('ol.kfl'); if (kfl) { kfl.className = 'kfl'; var st2 = ['kfl ktight', 'kfl ktight kcompact']; for (var s2 = 0; s2 < st2.length && drawn() > H; s2++) kfl.className = st2[s2]; } return; }
    var h0 = drawn();
    if (fits()) {
      if (rail && h0 < H * 0.6) { rail.style.display = 'block'; if (drawn() > H) rail.style.display = 'none'; }
      return;
    }
    if (h0 > H * 1.6) return;                 // clearly a long read: page it at full size
    for (var i = 1; i < LADDER.length; i++) {
      var p = LADDER[i].split(' ');
      for (var k = 0; k < p.length; k++) cls(p[k], true);
      if (fits()) return;
    }
    cls('kfit1', false); cls('kfit2', false); cls('kfit3', false); cls('kfit4', false);
  }
  function splits(u, c) { for (var i = 0; i < u.length; i++) { var x = u[i];
    if (x.top < c - 1 && x.bottom > c + 1 && x.bottom - x.top < H * 0.6) return true; } return false; }
  function plan() {
    var total = drawn(), start = 0, guard = 0, mtop = main.getBoundingClientRect().top;
    var c = [0], t = [0];
    var b = lastBoxes = boxes(), ls = b.ls, us = b.us;   // show() reuses these: no DOM walk per turn
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
    if (c.length > 2 && b.lb - start < 8) { c.pop(); t.pop(); start = t[t.length - 1]; }
    c.push(Math.max(total, start + 1));
    return { cuts: c, tops: t, last: Math.max(total, start + 1) - start };
  }
  function sig() { var f = document.fonts ? document.fonts.status : '', im = main.getElementsByTagName('img'), c = 0;
    for (var q = 0; q < im.length; q++) if (im[q].complete) c++;
    return window.innerWidth + 'x' + window.innerHeight + f + c; }
  var HINT = root.getAttribute('data-kfit');
  function hinted() {                       // the build's measured answer, checked once; null = run the ladder
    var m = /^([fp]):(.*)$/.exec(HINT || ''); if (!m || FLOW) return null;
    cls('kfit1', false); cls('kfit2', false); cls('kfit3', false); cls('kfit4', false); main.style.zoom = '';
    if (rail) rail.style.display = 'none';
    var p = m[2].split(' '); for (var k = 0; k < p.length; k++) if (p[k]) cls(p[k], true);
    if (m[1] === 'p') return plan();
    if (!fits()) return null;
    if (rail && drawn() < H * 0.6) { rail.style.display = 'block'; if (drawn() > H) rail.style.display = 'none'; }
    return { cuts: [0, drawn()], tops: [0], last: 0 };
  }
  function layout(force) {
    var s0 = sig(); if (!force && s0 === lastSig) return; lastSig = s0;
    try {
      cls('kpaged', true);
      main.style.top = '0px'; unscroll();
      if (kcont && !FLOW) { kcont.innerHTML = '<b>' + TITLE.replace(/</g, '&lt;') + '</b> (continued)'; kcont.style.display = 'block'; C = outer(kcont); kcont.style.display = 'none'; }
      H = Math.max(240, window.innerHeight - outer(run) - outer(bar));
      kview.style.height = H + 'px';
      var pl = hinted();
      if (!pl) {
      fit();
      pl = { cuts: [0, drawn()], tops: [0], last: 0 };
      if (!main.style.zoom && !root.className.match(/kfit1/)) {
        pl = plan();
        // A last screen with a line or two on it: set the card a little tighter instead.
        if (!FLOW && pl.cuts.length > 2 && pl.last < H * 0.28) {
          var tries = [['kfit1'], ['kfit1', 'kfit2'], ['kfit1', 'kfit2', 'kfit4']];
          for (var w = 0; w < tries.length; w++) {
            for (var y = 0; y < tries[w].length; y++) cls(tries[w][y], true);
            var p2 = plan();
            if (p2.cuts.length < pl.cuts.length) { pl = p2; break; }
            cls('kfit1', false); cls('kfit2', false); cls('kfit4', false);
          }
        }
      }
      }
      cuts = pl.cuts; tops = pl.tops;
      root.setAttribute('data-kfit-now', (cuts.length > 2 ? 'p:' : 'f:') + (root.className.match(/kfit\d/g) || []).join(' '));
      show(Math.min(sheet, cuts.length - 2));
      if (!hashDone) { hashDone = true;
        var back2 = 0; try { back2 = performance.navigation.type === 2; } catch (e) {}
        if (location.hash) toHash();
        else if (back2 && store['kme:' + location.pathname]) show(Math.min(+store['kme:' + location.pathname] || 0, cuts.length - 2)); }
    } catch (err) {
      if (kcont) kcont.style.display = 'none';
      cls('kpaged', false); main.style.zoom = ''; main.style.top = ''; view.style.height = ''; kview.style.height = '';
    }
  }
  function toHash() {
    var hs = location.hash.slice(1);
    if (hs === 'kend') { show(cuts.length - 2); return; }
    if (/^s\d+$/.test(hs)) { show(Math.min(+hs.slice(1), cuts.length - 2)); return; }
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
    var tl = document.getElementById('ktail'), kme = / kme /.test(' ' + root.className + ' ');
    if (kme) {   /* no white unless behind text: the engraved ground shows everywhere else. White knock-outs hug
                    each line of text (and each chart and picture) in a layer behind #kmain, never inside it */
      var ko = document.getElementById('kko');
      if (!ko) { ko = document.createElement('div'); ko.id = 'kko'; ko.setAttribute('aria-hidden', 'true'); view.insertBefore(ko, main); }
      if (!main.getAttribute('data-kink')) { main.setAttribute('data-kink', '1');
        var ka = main.getElementsByTagName('*');
        for (var ki = 0; ki < ka.length; ki++) { var ke = ka[ki];
          if (getComputedStyle(ke).backgroundColor === 'rgb(255, 255, 255)' && !(ke.closest && ke.closest('.bars,.rain,.mix,.kchart,figure,table,svg,.kpanel')))
            ke.style.setProperty('background-color', 'transparent', 'important'); } }
      var mr = main.getBoundingClientRect(), sig = Math.round(mr.width) + 'x' + main.offsetHeight + ' ' + root.className;
      if (ko.getAttribute('data-sig') !== sig) { ko.setAttribute('data-sig', sig);
        /* text blocks print on clean white labels set into the engraved paper: the line boxes of each block
           (paragraph, stat cell, list) are united, neighbours a line apart merge, and each label gets a fine
           double rule; charts and pictures keep a plain white ground */
        var kr = [], rg = document.createRange(), tw = document.createTreeWalker(main, 4, null, false), tn, PX = 7, PY = 5;
        while ((tn = tw.nextNode())) {
          if (!/\S/.test(tn.nodeValue)) continue;
          var pe = tn.parentNode; if (pe.closest && pe.closest('svg,script,style,.kchart,table')) continue;
          var bk = pe; while (bk !== main && !blockish(bk)) bk = bk.parentNode;
          rg.selectNodeContents(tn); var cr = rg.getClientRects(), pb = pe.getBoundingClientRect();
          for (var ci = 0; ci < cr.length; ci++) { var c0 = cr[ci], cl = Math.max(c0.left, pb.left), cw = Math.min(c0.right, pb.right) - cl;
            if (cw < 1 || c0.height < 1) continue;   /* clipped to its element: an ellipsis never leaves white beyond it */
            var x0 = cl - mr.left, y0b = c0.top - mr.top, hit = null;
            for (var rj = 0; rj < kr.length; rj++) if (kr[rj].b === bk) { hit = kr[rj]; break; }
            if (!hit) kr.push({ b: bk, l: x0, t: y0b, r: x0 + cw, d: y0b + c0.height });
            else { hit.l = Math.min(hit.l, x0); hit.t = Math.min(hit.t, y0b); hit.r = Math.max(hit.r, x0 + cw); hit.d = Math.max(hit.d, y0b + c0.height); } } }
        for (var ra = 0; ra < kr.length; ra++) { kr[ra].l -= PX; kr[ra].r += PX; kr[ra].t -= PY; kr[ra].d += PY; }
        var merged = true;
        while (merged) { merged = false;
          for (var m1 = 0; m1 < kr.length && !merged; m1++) for (var m2 = m1 + 1; m2 < kr.length; m2++) { var A = kr[m1], Bq = kr[m2];
            var ox = Math.min(A.r, Bq.r) - Math.max(A.l, Bq.l), oy = Math.min(A.d, Bq.d) - Math.max(A.t, Bq.t);
            if ((ox > 0 && oy > -6) || (oy > 0 && ox > -6)) {   /* touching or a line apart: one label */
              A.l = Math.min(A.l, Bq.l); A.t = Math.min(A.t, Bq.t); A.r = Math.max(A.r, Bq.r); A.d = Math.max(A.d, Bq.d); kr.splice(m2, 1); merged = true; break; } } }
        var mw = main.offsetWidth, kl = [];
        for (var rb = 0; rb < kr.length; rb++) { var L0 = kr[rb], t0 = L0.t;   /* never across a sheet cut: each sheet's part is its own label */
          L0.l = Math.max(L0.l, -1.5); L0.r = Math.min(L0.r, mw + 1.5);
          for (var cq = 1; cq < cuts.length - 1; cq++) if (t0 < cuts[cq] - 4 && L0.d > cuts[cq] + 4) { kl.push([L0.l, t0, L0.r, cuts[cq] - 2]); t0 = Math.max(tops[cq] + 2, t0); }
          kl.push([L0.l, t0, L0.r, L0.d]); }
        var kh = '';
        for (var ri = 0; ri < kl.length; ri++) kh += '<i class="kl" style="left:' + Math.floor(kl[ri][0]) + 'px;top:' + Math.floor(kl[ri][1]) + 'px;width:' + Math.ceil(kl[ri][2] - kl[ri][0]) + 'px;height:' + Math.ceil(kl[ri][3] - kl[ri][1]) + 'px"></i>';
        var kq = main.querySelectorAll('img,.kchart,.bars,.rain,.mix,table,figure,svg');
        for (var qi = 0; qi < kq.length; qi++) { var qr = kq[qi].getBoundingClientRect(); if (qr.width < 1 || qr.height < 1) continue;
          if (kq[qi].tagName.toLowerCase() === 'svg' && kq[qi].closest('.kchart,figure')) continue;
          kh += '<i style="left:' + Math.floor(qr.left - mr.left) + 'px;top:' + Math.floor(qr.top - mr.top) + 'px;width:' + Math.ceil(qr.width + 1) + 'px;height:' + Math.ceil(qr.height + 1) + 'px"></i>'; }
        ko.innerHTML = kh; }
      ko.style.top = main.style.top; ko.style.left = main.offsetLeft + 'px';
      setTimeout(function () {   /* after show() has set the bar's labels */
      var kf = document.getElementById('kkf'), fsig = window.innerWidth + ' ' + sig + ' ' + (kcont && kcont.style.display) + (kcont ? kcont.textContent : '') + (more ? more.textContent + more.style.display : '') + (pos ? pos.textContent : '');
        if (!kf) { kf = document.createElement('div'); kf.id = 'kkf'; kf.setAttribute('aria-hidden', 'true'); document.body.appendChild(kf); }
        if (kf.getAttribute('data-sig') !== fsig) { kf.setAttribute('data-sig', fsig);   /* the running head, the bar, "continued": white only under their words */
          var fh = '', fls = [], fr = document.createRange(), fq = [run, bar, kcont];
          for (var fi = 0; fi < fq.length; fi++) { if (!fq[fi] || fq[fi].offsetParent === null) continue;
            var fw = document.createTreeWalker(fq[fi], 4, null, false), fn;
            while ((fn = fw.nextNode())) { if (!/\S/.test(fn.nodeValue) || fn.parentNode.offsetParent === null || (fn.parentNode.closest && fn.parentNode.closest('#kmore'))) continue; fr.selectNodeContents(fn);
              var fc = fr.getClientRects(), fb = fn.parentNode.getBoundingClientRect();
              for (var fj = 0; fj < fc.length; fj++) { var f0 = fc[fj], fl = Math.max(f0.left, fb.left), fw2 = Math.min(f0.right, fb.right) - fl; if (fw2 < 1) continue;
                var fx = [fl - 6, f0.top - 3, fl + fw2 + 6, f0.bottom + 3], fm = false;
              for (var fk = 0; fk < fls.length; fk++) { var G = fls[fk]; if (fx[0] < G[2] + 10 && fx[2] > G[0] - 10 && fx[1] < G[3] && fx[3] > G[1]) {
                G[0] = Math.min(G[0], fx[0]); G[1] = Math.min(G[1], fx[1]); G[2] = Math.max(G[2], fx[2]); G[3] = Math.max(G[3], fx[3]); fm = true; break; } }
              if (!fm) fls.push(fx); } } }
          for (var fk2 = 0; fk2 < fls.length; fk2++) fh += '<i class="kl" style="left:' + Math.floor(fls[fk2][0]) + 'px;top:' + Math.floor(fls[fk2][1]) + 'px;width:' + Math.ceil(fls[fk2][2] - fls[fk2][0]) + 'px;height:' + Math.ceil(fls[fk2][3] - fls[fk2][1]) + 'px"></i>';
          if (more && more.offsetParent !== null) { var mb2 = more.getBoundingClientRect(); fh += '<i style="left:' + Math.floor(mb2.left) + 'px;top:' + Math.floor(mb2.top) + 'px;width:' + Math.ceil(mb2.width) + 'px;height:' + Math.ceil(mb2.height) + 'px"></i>'; }
          kf.innerHTML = fh; }
      }, 0); }
    if (tl) {   /* fill what this sheet leaves empty: art beside #kmain, never in it, so it never adds a sheet */
      var t2 = document.getElementById('ktail2');
      if (!t2) { t2 = document.createElement('div'); t2.id = 'ktail2'; t2.setAttribute('aria-hidden', 'true'); tl.parentNode.appendChild(t2); }
      var used = Math.min(h, end - top);
      if (i === n - 1) { var bx = (typeof lastBoxes !== 'undefined' && lastBoxes) || boxes(); if (bx.lb) used = Math.min(h, bx.lb - top + 6); }
      var y0 = (i && !FLOW ? C : 0) + used + 6, room = H - y0 - 6;
      tl.style.display = t2.style.display = 'none';
      if (kme && room >= 40) {   /* never print a plate over a line of type: start below the last text visible on this sheet */
        var vt = view.getBoundingClientRect().top, cb = document.getElementById('kclip').getBoundingClientRect(), tw = document.createTreeWalker(main, 4, null, false), tn, tb = 0;
        while ((tn = tw.nextNode())) { if (!/\S/.test(tn.nodeValue)) continue; var rg = document.createRange(); rg.selectNodeContents(tn); var rs = rg.getClientRects();
          for (var ri = 0; ri < rs.length; ri++) { var q = rs[ri]; if (q.bottom > cb.top + 1 && q.top < cb.bottom - 1 && q.bottom > tb) tb = Math.min(q.bottom, cb.bottom); } }
        if (tb && tb - vt + 6 > y0) { y0 = tb - vt + 6; room = H - y0 - 6; } }
      var vr = view.getBoundingClientRect();
      window.KROOM = { sheet: i, sheets: n, x: Math.round(vr.left), y: Math.round(vr.top + y0), w: Math.round(vr.width), h: Math.round(room) };
      var kp = kme && room >= 40 && document.body.getAttribute('data-kplates'), pk = null;
      if (kp) { try { kp = JSON.parse(kp); } catch (e) { kp = []; }   /* this page's plates: [sheet, h, w], cut to this morning's rooms */
        for (var pi = 0; pi < kp.length; pi++) if (kp[pi][0] === i && kp[pi][1] <= room + 2 && kp[pi][1] >= room - 16) pk = kp[pi];
        if (!pk) for (pi = 0; pi < kp.length; pi++) if (kp[pi][1] <= room && (!pk || kp[pi][1] > pk[1])) pk = kp[pi]; }
      if (pk) {   /* ONE bespoke engraved plate fills the free space: a fixed-size <img>, outside #kmain, so it never adds a sheet */
        var slug = location.pathname.split('/').pop().replace(/\.html$/, ''), im = t2.firstChild;
        if (!im) { im = document.createElement('img'); im.alt = ''; t2.appendChild(im); }
        var src = 'orn/plate-' + slug + '-' + pk[0] + '.svg';
        if (im.getAttribute('src') !== src) im.setAttribute('src', src);
        im.width = pk[2]; im.height = pk[1]; t2.className = 'kplate';
        t2.style.top = (y0 + Math.max(0, room - pk[1]) / 2) + 'px'; t2.style.height = pk[1] + 'px'; t2.style.display = 'block'; 
        setTimeout(function () {   /* after the sheet settles: if any visible line of type reaches under the plate, move the plate below it, or drop it */
          var tr = t2.getBoundingClientRect(), vr2 = view.getBoundingClientRect(), cb = document.getElementById('kclip').getBoundingClientRect(), tw = document.createTreeWalker(main, 4, null, false), tn, tb = 0;
          while ((tn = tw.nextNode())) { if (!/\S/.test(tn.nodeValue)) continue; var rg = document.createRange(); rg.selectNodeContents(tn); var rs = rg.getClientRects();
            for (var ri = 0; ri < rs.length; ri++) { var q = rs[ri]; if (q.height && q.bottom > cb.top + 1 && q.top < cb.bottom - 1 && q.top < vr2.bottom - 1 && q.bottom > tb) tb = Math.min(q.bottom, cb.bottom, vr2.bottom); } }
          if (tb > tr.top - 4) { var d = tb + 6 - tr.top, lim = vr2.top + H - 6;
            if (tr.bottom + d <= lim) t2.style.top = (parseFloat(t2.style.top) + d) + 'px'; else t2.style.display = 'none'; }
        }, 60); }
    }
    var gq = view.querySelectorAll('.kgap');   /* and the gaps between blocks: a fleuron in each, never over print */
    for (var g = 0; g < gq.length; g++) view.removeChild(gq[g]);
    if (kme) {
      var gl = ((typeof lastBoxes !== 'undefined' && lastBoxes) || boxes()).ls.slice(), mt0 = main.getBoundingClientRect().top, vis = Math.min(h, end - top), mb = null;
      var kpq = main.querySelectorAll('.kpanel');   /* panels are whole blocks: the fleurons go in the gaps between them only */
      if (kpq.length) { gl = []; for (var kq0 = 0; kq0 < kpq.length; kq0++) { var kr0 = kpq[kq0].getBoundingClientRect(); if (kr0.height > 0) gl.push({ top: kr0.top - mt0, bottom: kr0.bottom - mt0 }); } }
      var dq = main.querySelectorAll('.kfhead,.kmast,.kend,.kgl,.kendsrc,.ktoc');   /* drawn by pseudo-elements: printed too */
      for (var d0 = 0; d0 < dq.length; d0++) { var dr = dq[d0].getBoundingClientRect(); gl.push({ top: dr.top - mt0, bottom: dr.bottom - mt0 }); }
      gl.sort(function (a, b) { return a.top - b.top; });
      for (var g2 = 0; g2 < gl.length; g2++) { var gi = gl[g2];
        if (gi.bottom <= top + 1 || gi.top >= top + vis - 1) continue;
        if (mb !== null && gi.top - mb > 40) {
          var gd = document.createElement('div'); gd.className = 'kgap' + (gi.top - mb > 110 ? ' kbig' : gi.top - mb < 64 ? ' kthin' : '');
          var gh = Math.min(gi.top - mb - 10, 120); gd.style.top = (mb - top + (gi.top - mb - gh) / 2) + 'px'; gd.style.height = gh + 'px'; view.appendChild(gd); }
        if (mb === null || gi.bottom > mb) mb = gi.bottom; } }
    unscroll();
    if (more) {
      more.style.display = (i < n - 1) ? '' : 'none';
      more.innerHTML = 'More &darr;<span class="kfol" hidden>' + (i + 1) + '/' + n + '</span>';
    }
    if (pos) pos.innerHTML = '';
    var ksh = document.getElementById('ksheet');   /* one counter: this page's sheets, in the running head */
    if (ksh) ksh.innerHTML = n > 1 ? 'Sheet ' + (i + 1) + ' of ' + n : '';
    if (knx && knxLabel && NEXT_URL) { var kl0 = knxLabel.replace(/^Next: /, ''), kl1 = kl0.replace(/<[^>]+>|&\w+;/g, '');
      knx.innerHTML = i < n - 1 ? (kl1.length > 16 ? 'Next page &rsaquo;' : 'Skip to ' + kl0) : (kl1.length > 26 ? 'Next page &rsaquo;' : kl0); }
    try { store['kme:' + location.pathname] = i;
      if (!FLOW && window.localStorage) localStorage.setItem('kme:last', JSON.stringify({ u: location.pathname.split('/').pop(), s: i, t: TITLE, ed: root.getAttribute('data-ed') || '' })); } catch (e) {}
  }
  function turn(i) {                            // in-page turns are partial e-ink updates: flash now and then
    if (busy) return;
    if (++turns % FLASH_EVERY && !root.hasAttribute('data-flash')) { show(i); return; }
    busy = true;
    var f = document.createElement('div');
    f.style.cssText = 'position:fixed;left:0;top:0;width:100%;height:100%;background:#000;z-index:2147483647';
    document.body.appendChild(f);
    var raf = window.requestAnimationFrame || function(cb){ return setTimeout(cb, 16); };
    raf(function(){ raf(function(){ setTimeout(function(){ f.style.background = '#fff';
      setTimeout(function(){ show(i); document.body.removeChild(f); busy = false; }, 120); }, 420); }); });
  }
  function go(url) { location.href = url || 'index.html'; }
  function forward() { var n = cuts.length - 1;
    if (sheet < n - 1) turn(sheet + 1); else go(NEXT_URL); }
  function back() { if (sheet > 0) turn(sheet - 1); else if (PREV_URL) go(PREV_URL + (/#/.test(PREV_URL) ? '' : '#kend')); }
  // The running head opens a list of every section.
  var jump = document.getElementById('kjump');
  if (run && jump) run.onclick = function(e){ if (!on()) return; e.preventDefault(); e.stopPropagation();
    cls('kjumpopen', !/kjumpopen/.test(root.className)); };
  // Swipes turn pages, as in the Kindle's own reader.
  var x0 = null, y0 = 0, swallow = false;
  document.addEventListener('touchstart', function(e){ if (e.touches && e.touches.length === 1) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; } }, false);
  document.addEventListener('touchend', function(e){
    if (x0 === null || !on() || !e.changedTouches) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null;
    if (Math.abs(dx) > 50 && Math.abs(dx) > 1.5 * Math.abs(dy)) { swallow = true; setTimeout(function(){ swallow = false; }, 400); if (dx < 0) forward(); else back(); }
  }, false);
  // The cover offers to pick up where you stopped.
  if (/kcontents/.test(document.body.className)) try {
    var last = JSON.parse(localStorage.getItem('kme:last') || 'null'), mast = main.querySelector('.kmast');
    if (last && last.u && mast && last.ed === root.getAttribute('data-ed')) { var a = document.createElement('a'); a.className = 'kresume';
      var ld = main.querySelectorAll('.kleads > a'); if (ld.length > 2) ld[ld.length - 1].parentNode.removeChild(ld[ld.length - 1]);
      a.href = last.u + (last.ed === root.getAttribute('data-ed') && last.s ? '#s' + last.s : '');
      a.innerHTML = '<small>Pick up where you stopped</small><b>' + String(last.t).replace(/</g, '&lt;') + ' &rsaquo;</b>';
      mast.parentNode.insertBefore(a, mast.nextSibling); }
  } catch (e) {}
  function later(e) { clearTimeout(timer); var force = !!(e && e.type === 'toggle'); timer = setTimeout(function(){ layout(force); }, 60); }
  if (more) more.onclick = function(e){ e.preventDefault(); e.stopPropagation(); if (on()) forward(); };
  document.addEventListener('click', function(e){
    if (!on() || swallow) return;
    if (/kjumpopen/.test(root.className) && !(jump && jump.contains(e.target))) { e.preventDefault(); cls('kjumpopen', false); return; }
    for (var t = e.target; t && t !== document.body; t = t.parentNode) {
      var n = (t.nodeName || '').toUpperCase();
      if ((n === 'A' && t.getAttribute('href')) || t === more || /^(SUMMARY|BUTTON|INPUT|LABEL|SELECT|TEXTAREA)$/.test(n)) return;
    }
    e.preventDefault();
    if (e.clientX < window.innerWidth / 3) back(); else forward();
  }, false);
  document.addEventListener('touchmove', function(e){ if (on() && !(jump && jump.contains(e.target))) e.preventDefault(); }, { passive: false });
  document.addEventListener('scroll', function(){ if (on()) unscroll(); }, true);
  document.addEventListener('toggle', later, true);
  document.addEventListener('keydown', function(e){
    if (e.keyCode === 34 || e.keyCode === 39 || e.keyCode === 32) { e.preventDefault(); forward(); }
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
  // The next page is fetched ahead into the browser cache. An offline copy
  // from an earlier version is removed.
  var KART = ['orn/ground-%s.svg', 'orn/motif-%s.svg'];   // a section's CSS-background art, warmed before entry
  function warm(u) { if (!u) return; try { var x = new XMLHttpRequest(); x.open('GET', u, true);
    x.onload = function(){ var m = (x.responseText || '').match(/<img[^>]+src="[^"]+"/g) || [];
      for (var i = 0; i < m.length && i < 4; i++) { var im = new Image(); im.src = m[i].replace(/^.*src="/, '').replace(/"$/, ''); }
      var ks = (x.responseText || '').match(/data-ksec="([\w-]+)"/), here = document.body.getAttribute('data-ksec');
      if (ks && ks[1] !== here) for (var a = 0; a < KART.length; a++) { var ia = new Image(); ia.src = KART[a].replace('%s', ks[1]); } };
    x.send(); } catch (e) {} }
  setTimeout(function(){
    try { var sw = navigator.serviceWorker;
      if (sw && sw.getRegistrations) sw.getRegistrations().then(function(rs){ for (var i = 0; i < rs.length; i++) rs[i].unregister(); }).catch(function(){});
      if (window.caches && caches.keys) caches.keys().then(function(ks){ for (var i = 0; i < ks.length; i++) if (/^kme-/.test(ks[i])) caches['delete'](ks[i]); }).catch(function(){});
    } catch (e) {}
    warm(NEXT_URL);
  }, 900);
})();
</script>
"""


SW_JS = r"""// Switched off: removes the offline copy an earlier version saved, then itself.
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) await caches.delete(k);
  await self.registration.unregister();
})()));
"""


def write_offline(out, ed):
    """sw.js stays only to switch off the offline copy an earlier version saved."""
    stale = os.path.join(out, "edition.json")
    if os.path.exists(stale):
        os.remove(stale)
    with open(os.path.join(out, "sw.js"), "w") as f:
        f.write(SW_JS)


FONT_CSS = ("https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@"
            "0,7..72,400..700;1,7..72,400..700&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=block")


BUILD = {}  # this edition's id, for the saved copy and "pick up where you stopped"


def page(title, body, html_class, body_class, prev=None, nxt=None, stamp="", run_left="", run_right="",
         fonts="", next_label=None, run_href="index.html", jump=None, sec=""):
    esc = html.escape
    nav = (_JUMP[0] if jump is None else jump) if run_left else ""
    btn = '<b class="ksecbtn">Sections &#9662;</b>' if nav else ""
    top = (f'<nav class="krun"><a href="{run_href}">{run_left}</a><span>{esc(run_right)}<i id="ksheet"></i>{btn}</span></nav>'
           if run_left else f'<nav class="krun"><a href="{run_href}">{run_left}</a><span>{esc(run_right)}{btn}</span></nav>')
    nxt_name = esc(next_label) if next_label else esc(prev_title(nxt)) if nxt else ""
    nxt_block = (f'<a class="knext" href="{nxt}"><small>Next</small><span>{nxt_name} &rarr;</span></a>' if nxt
                 else '<a class="knext" href="index.html"><small>The end</small><span>Back to the front &rarr;</span></a>')
    prev_link = (f'<a class="kprev" href="{prev}">&lsaquo; {esc(prev_title(prev)) or "Back"}</a>' if prev
                 else '<span class="kprev"></span>')
    nxt_short = (f'<a class="knx" href="{nxt}">{"Next: " if next_label is None else ""}{nxt_name} &rsaquo;</a>' if nxt
                 else '<a class="knx" href="index.html">The front &rsaquo;</a>')
    foot = (f'<footer class="kbar">{prev_link}<span class="kmid"><a id="kmore" href="#" role="button">More &darr;</a>'
            f'<span id="kpos"></span></span>{nxt_short}</footer>'
            f'<footer class="kfoot">{nxt_block}<div class="kmeta"><span></span><span>{stamp}</span></div></footer>')
    js = PAGER_JS.replace("__NEXT__", repr(nxt or "")).replace("__PREV__", repr(prev or ""))
    return f"""<!doctype html>
<html lang="en" class="{esc(html_class)}" data-ed="{esc(BUILD.get("id") or stamp)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>{esc(title)}</title>{fonts}<link rel="stylesheet" href="kindle.css"></head>
<body class="{esc(body_class)}"{f' data-ksec="{esc(sec)}"' if sec else ""}>
{top}
<div id="kview"><div id="kcont"></div><div id="kclip"><main id="kmain">{body}</main></div><div id="ktail" aria-hidden="true"></div></div>
{nav}
{foot}
{kindle_orn.FLASH_JS if " kme" in " " + html_class else ""}{js}
</body></html>
"""


_TITLES = {}
OWNER_INITIAL = "P"   # the crest on the cover
_JUMP = [""]


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


def _data_time(site):
    """When dashboard.json was gathered (aware datetime), or None. Warn when it is stale."""
    import datetime as _d
    import json as _j
    try:
        with open(os.path.join(site, "dashboard.json")) as f:
            at = _d.datetime.fromisoformat(_j.load(f)["generated_at"])
    except Exception:
        return None
    age_h = (_d.datetime.now(_d.timezone.utc) - at).total_seconds() / 3600
    if age_h > 2:
        print(f"kindle_full: WARNING dashboard.json is {age_h:.1f} h old; printing it as of {at.isoformat()}", file=sys.stderr)
    return at


def snapshot(site):
    from playwright.sync_api import sync_playwright  # only the morning snapshot needs a browser
    srv = serve(site)
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html?kindle"
    exe = os.environ.get("KINDLE_CHROMIUM") or None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=exe)
        ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, timezone_id=TZ, device_scale_factor=2,
                                  has_touch=True, locale="en-US", reduced_motion="reduce")
        p = ctx.new_page()
        # run the page's clock from the moment the data was gathered, so the
        # edition stamp, "today/tonight", "N hr ago", the next tide and every past-event
        # filter agree with the numbers on the page instead of with the build machine.
        data_at = _data_time(site)
        if data_at is not None:
            p.clock.install(time=data_at)
            p.clock.resume()
        p.on("pageerror", lambda e: print(f"kindle_full: page error: {e}", file=sys.stderr))
        p.on("console", lambda m: m.text.startswith("kindle ") and print(f"kindle_full: {m.text}", file=sys.stderr))
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

# ---- The edition plan (redesign/edition-plan.md): merges, item caps and cuts, in one place.
# A merge folds one card into another as a titled block (key: heading id or card title).
PLAN_MERGES = [
    ("shade-h", "brief-h"),                       # Window shades -> Alfred
    ("yard-h", "wx-h"), ("jar-h", "wx-h"),        # Yard vs. forecast, rain jar -> weather station
    ("road-h", "drive-h"),                        # Road cams -> Drive times
    ("ski-h", "mtn-h"), ("trail-h", "mtn-h"),     # The mountain: visibility, then Mt. Hood, then trail reports
    ("quake-h", "fire-h"),                        # Hazards
    ("ask-h", "play-h"), ("bug-h", "play-h"),     # Dinner question, germ report -> Little adventures
    ("loads-h", "Solar right now"),               # Solar today
    ("wins-h", "bill-h"),                         # Milestones -> billing cycle
    ("burn-h", "look-h"), ("pollen-h", "look-h"), ("plant-h", "look-h"), ("forest-h", "look-h"),
    ("bloom-h", "look-h"), ("food-h", "look-h"),  # Walk the land
    ("moor-h", "columbia-h"),                     # Ship -> The Columbia
    ("light-h", "sunset-h"), ("set-h", "sunset-h"),  # Daylight, sunset on the move -> tonight's sunset
    ("sunact-h", "sky-h"),                        # Spots on the sun -> sky events
    ("reviews-h", "stories-h"),                   # A/V and tech desk
    ("Portland State Vikings", "Portland Timbers"), ("Portland Pilots", "Portland Timbers"),
    ("f1-h", "Portland Timbers"), ("title-h", "Portland Timbers"),   # The scoreboard
    ("drum-h", "rec-h"), ("bday-h", "rec-h"),     # The record page
    ("plane-h", "sky-h"),                         # Planes overhead -> two rows in Sky events
    ("Portland Timbers", "Portland Trail Blazers"),   # one scoreboard: the Blazers lead, the rest follow
    ("show-h", "gig-h"),                          # Live from Portland -> live music
    ("clsmov-h", "kidmov-h"),                     # Tonight's movies
    ("oldpdx-h", "near-h"),                       # Old Portland -> local history
    ("shelf-h", "books-h"),                       # Bookshelf -> books
    ("minus-h", "This week at the coast"), ("cev-h", "shell-h"),
]
# Most items a card's main list prints (the plan's item caps: the main tool against orphan sheets).
PLAN_CAPS = {"plan-h": 5, "cal-h": 8, "out-h": 8, "localnews-h": 6, "bignews-h": 7, "stories-h": 4, "reviews-h": 4, "finds-h": 3,
             "open-h": 5, "big-h": 5, "liq-h": 6, "br-h": 5, "tv-h": 6, "alb-h": 6, "jazz-h": 8, "gig-h": 6, "good-h": 3,
             "play-h": 4, "mush-h": 5, "birds-h": 5, "fire-h": 4, "road-h": 4, "hol-h": 8}
PLAN_SCIENCE_BRIEFS = 4
# Parker on the plan's cut list: "Merge, don't cut." Each item shrinks to a line or two inside the page it
# belongs with (the merges above put it there); these say how much of it stays. Set a value to 0 to drop it.
PLAN_SHRINK = {
    "planes": 2,                # Planes overhead -> two rows in Sky events
    "civics-votes": 1,          # the newest vote per member: one compact summary
    "civics-news": 1,           # one news line per member
    "born-today": 2,            # Born today -> two names in This day in history
    "also-nearby": 2,           # Local history: two nearby places
    "asteroids": 1,             # Sky events: one line
    "bday-lists": 2,            # Album birthdays -> two lines on the record page
    "team-news": 1,             # team pages -> one headline each on the scoreboard
    "long-writeups": 2,         # market and helium narratives -> a two-line summary (paragraphs)
}

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
          if (prev && root.contains(prev) && c.closest('.lines, ul, ol, table') && prev.closest('.lines, ul, ol, table')) { visit(c); c = nx; continue; }
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
  for (const d of docs) for (const a of [...d.querySelectorAll('a[href^="http"], a[href^="tel:"]')]) {
    if (a.classList.contains('read-fresh')) continue;
    if (/^(Listen|Spotify|Tickets|Buy|Book|Watch|Read more|More)\b.{0,12}$/i.test(norm(a.textContent))) { a.remove(); continue; }
    const sp = document.createElement('span'); if (a.className) sp.className = a.className;
    while (a.firstChild) sp.appendChild(a.firstChild); a.replaceWith(sp);
  }
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
      if (li.closest('.kplan')) continue;
      const bs = [...li.querySelectorAll('b, strong')].map(x => norm(x.textContent)).filter(x => x.length >= 6);
      if (bs.length && texts.some(pt => bs.every(x => pt.includes(x)))) { prune(li); continue; }
      const t = norm(li.textContent);
      const b = [...li.querySelectorAll('b')].map(x => norm(x.textContent)).filter(x => x.length >= 12);
      const subj = t.split(': ').pop().replace(/[.!]+$/, '');
      if (/ is today\.?$/.test(t) || keys.some(k => t.includes(k) || b.some(x => k.includes(x)) || (subj.length >= 15 && k.includes(subj)))) prune(li);
    }
    for (const ul of [...d.querySelectorAll('ul')]) if (!ul.querySelector('li')) ul.remove();
    for (const h of [...d.querySelectorAll('h3')]) {
      const nx = h.nextElementSibling;
      if (!nx || /^H3$/.test(nx.tagName) || !norm(nx.textContent) || /brief-sign/.test(nx.className)) h.remove();
    }
  });
  for (const d of docs) {
    const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT);
    let prev = null;
    for (let n = tw.nextNode(); n; n = tw.nextNode()) {
      if (/^\s+[,.;:!?](\s|$)/.test(n.nodeValue)) n.nodeValue = n.nodeValue.replace(/^\s+/, '');
      if (prev && /^[,.;:!?](\s|$)/.test(n.nodeValue) && /\s$/.test(prev.nodeValue)) prev.nodeValue = prev.nodeValue.replace(/\s+$/, '');
      n.nodeValue = n.nodeValue.replace(/ +([,.;:!?])(?=\s|$)/g, '$1');
      prev = n;
    }
  }
  return docs.map(d => d.innerHTML);
}
"""


def dedupe(pages, titles):
    """Run DEDUPE over the pages in reading order (in place)."""
    import json
    from playwright.sync_api import sync_playwright
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
            fam = re.search(r"font-family:\s*'([^']+)'", blk).group(1).lower().replace(" ", "-")
            name = f"{fam}-{re.search(r'font-style:\s*(\w+)', blk).group(1)}.woff2"
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
    kindle_orn.write_plates(out)
    me = (data["htmlClass"] + " kme").strip()

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

    def as_sub(h):
        """A card's body as a block inside another card: its headline becomes an h3."""
        h = re.sub(r'<p class="kkick(?:er)?"[^>]*>.*?</p>', "", h, flags=re.S)
        return re.sub(r"<h2\b([^>]*)>(.*?)</h2>", r'<h3 class="kfold"\1>\2</h3>', h, flags=re.S)

    # The plan's merges: the folded card becomes a titled block inside its host.
    def find_card(key):
        for sid_, sec_ in by_id.items():
            for c_ in sec_["cards"]:
                if f'id="{key}"' in c_["html"] or c_["title"] == key:
                    return sid_, c_
        return None, None
    for src_k, dst_k in PLAN_MERGES:
        ss, sc = find_card(src_k)
        ds, dc = find_card(dst_k)
        if sc is None or dc is None or sc is dc:
            continue
        by_id[ss]["cards"].remove(sc)
        dc["html"] += f'<div class="kbrief">{as_sub(sc["html"])}</div>'
    by_id = {k: s_ for k, s_ in by_id.items() if s_["cards"]}
    # Science: one page of briefs, not seven taps of three lines each.
    sci = by_id.get("science", {}).get("cards", [])
    seen_subj, kept_sci = set(), []
    for c_ in sci:   # at most one brief per subject (three origin-of-life stories become one)
        subj = "life" if re.search(r"\blife\b|\blife.s\b", c_["title"], re.I) else c_["title"]
        if subj in seen_subj:
            continue
        seen_subj.add(subj)
        kept_sci.append(c_)
    sci = kept_sci[:PLAN_SCIENCE_BRIEFS]
    if len(sci) > 2:
        by_id["science"]["cards"] = [{"title": "Science this morning",
                                      "html": '<div class="head"><p class="kkick">Science</p><h2>This morning in science</h2></div>'
                                              + "".join(f'<div class="kbrief">{as_sub(c["html"])}</div>' for c in sci)}]
    # Thailand: Bangkok and the phrase of the day on one page.
    wc = by_id.get("world", {}).get("cards", [])
    if len(wc) > 1:
        wc[0]["html"] += "".join(f'<div class="kbrief">{as_sub(c["html"])}</div>' for c in wc[1:])
        del wc[1:]
    # A card with a line or two in it joins the card before it.
    KEEP = ("ask-h", "drum-h", "brief-h", "today-card", "rec-h", "poem-h")
    for sid, sec in by_id.items():
        kept = []
        for c in sec["cards"]:
            thin = (len(body_text(c["html"])) < 140 and "<img" not in c["html"] and "<svg" not in c["html"]
                    and not any(f'id="{k}"' in c["html"] for k in KEEP))
            if thin and kept:
                kept[-1]["html"] += f'<div class="kbrief">{as_sub(c["html"])}</div>'
            else:
                kept.append(c)
        sec["cards"] = kept
    # Before the panels wake up, "Solar right now" is a page of zeros: it goes last.
    if "solar" in by_id:
        sc = by_id["solar"]["cards"]
        for c in list(sc):
            if 'id="t-now"' in c["html"] and re.search(r"hasn.t reported|Producing now\s*0\.0", _text(c["html"])):
                sc.remove(c)
                sc.append(c)
    # Source credits leave the reading pages for one page at the back.
    credits = {}
    for sid, sec in by_id.items():
        for c in sec["cards"]:
            for m in re.findall(r'<p class="ksources"[^>]*>(.*?)</p>', c["html"], flags=re.S):
                m = re.sub(r"^\s*<b>[^<]*</b>\s*", "", m).strip(" ·")
                if m and m not in credits.setdefault(sid, []):
                    credits[sid].append(m)
                if m:   # and each page keeps its own as a one-line credit at its foot
                    c["credit"] = (c.get("credit", "") + " · " + _text(m)).strip(" ·")
            c["html"] = re.sub(r'<p class="ksources"[^>]*>.*?</p>', "", c["html"], flags=re.S)

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
            pages.append({"sec": i, "file": f"{i}-{k + 1:02d}.html", "title": NAMES.get(c["title"], c["title"]), "html": body, "credit": c.get("credit", ""),
                          "k": k + 1, "of": len(cards)})
    dedupe(pages, [])
    import datetime as _dt0
    kindle_present.run(pages, _dt0.datetime.strptime(longdate, "%A, %B %d, %Y").date().isoformat(),
                       caps=PLAN_CAPS, shrink=PLAN_SHRINK)
    # A card the presentation pass emptied (a trail list with no report text) is not a page.
    pages = [pg for pg in pages if len(body_text(pg["html"])) >= 25 or re.search(r"<img\b", pg["html"])]
    for sid in order:
        mine = [pg for pg in pages if pg["sec"] == sid]
        for k, pg in enumerate(mine, 1):
            pg.update(file=f"{sid}-{k:02d}.html", k=k, of=len(mine))
    order = [i for i in order if any(pg["sec"] == i for pg in pages)]
    parts = [(name, [i for i in ids if i in order]) for name, ids in parts]
    parts = [(name, ids) for name, ids in parts if ids]
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

    SKIP = re.compile(r"^(Updated|Checked|As of|Summary as of|Analysis as of|Events checked|Next \d+ days|From home)\b"
                      r"|\b(TomTom|TripCheck|WTA|NIFC|USGS|BPA|Google|Wikidata|Metacritic|Wikipedia|eBird|iNaturalist|Open-Meteo"
                      r"|NOAA|SWPC|CDC|Goodreads|Library of Congress|Internet Archive|Art Institute|TVmaze|TMDB|Yahoo|ODOT|NWS)\b"
                      r"|\b(outlets|sources)$|^Source", re.I)

    TEASER = {}
    for pg in pages:
        if pg["sec"] == "civics" and 'id="reps' in pg["html"]:
            who = [_text(x) for x in re.findall(r'<div class="rep-head"[^>]*>.*?<b[^>]*>(.*?)</b>', pg["html"], re.S)]
            if who:
                TEASER[pg["file"]] = ", ".join(who[:3]) + (" and more" if len(who) > 3 else "")
        if pg["sec"] == "world":
            m = re.search(r"(\d+°F)", _text(pg["html"]))
            TEASER[pg["file"]] = f"Bangkok right now{', ' + m.group(1) if m else ''}, the next days, and a Thai phrase to try"

    BAD = re.compile(r"not named|stories first|:$|^(Because|A \d{4}s classic)|^Learned from|^Inside now|^Expected solar|^\d+ in the next")

    def teaser(pg):
        h = pg["html"]
        if pg["sec"] == "science":
            return ""
        if pg["file"] in TEASER:
            return TEASER[pg["file"]]
        cands = []
        m = re.search(r'class="meta"[^>]*>(.*?)</span>', h, re.S)
        meta = _text(m.group(1)) if m else ""
        if meta and not SKIP.search(meta) and meta.lower() != pg["title"].lower() and len(meta) > 12:
            cands.append(meta)
        body = re.sub(r'<h2\b.*?</h2>|<p class="kkick[^"]*".*?</p>|<span class="meta".*?</span>|<h3\b.*?</h3>', "", h, flags=re.S)
        body = re.sub(r'<p class="(?:note )?kalso".*?</p>', "", body, flags=re.S)
        for para in re.findall(r'<(?:p|li|div class="ksum")\b[^>]*>(.*?)</(?:p|li|div)>', body, re.S):
            t = _text(para)
            if (t.count(" · ") >= 2 or re.match(r"(Tones:|Voted the same|Already on sale|Mostly quiet)", t)
                    or re.search(r"\(\w+ announced", t) or re.search(r" is an? [\w ]+ in [A-Z]\w+, [A-Z]", t)):
                continue
            if len(t) >= 30 and not SKIP.search(t):
                sm = re.match(r"(.{25,110}?[a-z0-9)%°]{2}[.!?])(\s+[A-Z(\"]|$)", t)
                one = sm.group(1) if sm else t
                cands.append(one if len(one) <= 62 else one[:60].rsplit(" ", 1)[0].rstrip(",;:·") + "…")
        for b in re.findall(r"<(?:b|strong)\b[^>]*>(.*?)</(?:b|strong)>", body, re.S):
            t = _text(b)
            if len(t) > 8:
                cands.append(t)
        for t in cands:
            t = re.sub(r"\s+([,.;:])", r"\1", t)
            if not BAD.search(t) and t.lower() != pg["title"].lower():
                return t
        return ""

    edition = stamp.split(" ", 1)[-1].replace("AM", "am").replace("PM", "pm")
    stamp_txt = html.escape(f"Edition of {edition}")
    BUILD["id"] = f"{longdate} {edition}"
    seq = []  # reading order of every file
    for i in order:
        seq.append(front[i])
        seq.extend(pg["file"] for pg in pages if pg["sec"] == i)
    seq.append("end.html")
    _TITLES["end.html"] = "The end"
    _JUMP[0] = ('<nav id="kjump"><a href="index.html"><b>The front</b></a>'
                + "".join(f'<a href="{front[i]}">{html.escape(by_id[i]["title"])}</a>' for i in order) + "</nav>")
    def navigator(sec=None, cur=None):
        e = html.escape
        cc = ' class="kjcur"'
        out_ = ['<nav id="kjump"><div class="kjtop">']
        if sec in order:
            k = order.index(sec)
            nx = order[k + 1] if k + 1 < len(order) else None
            href, name = (front[nx], by_id[nx]["title"]) if nx else ("end.html", "The end")
            out_.append(f'<a class="kjskip" href="{href}"><small>Skip {e(by_id[sec]["title"])}</small>{e(name)} &rsaquo;</a>')
        out_.append('<a class="kjfront" href="index.html"><small>Back to</small>The front</a></div>')
        if sec in order:
            sib = [pg for pg in pages if pg["sec"] == sec]
            if len(sib) > 1:
                out_.append(f'<p class="kjh">In {e(by_id[sec]["title"])}</p><div class="kjg">')
                out_ += [f'<a href="{pg["file"]}"{cc if pg["file"] == cur else ""}><i>{pg["k"]}</i>{e(pg["title"])}</a>'
                         for pg in sib]
                out_.append("</div>")
        out_.append('<p class="kjh">Every section</p><div class="kjg">')
        out_ += [f'<a href="{front[i]}"{cc if i == sec else ""}><i>{n}</i>{e(by_id[i]["title"])}</a>'
                 for n, i in enumerate(order, 1)]
        out_.append("</div></nav>")
        return "".join(out_)

    _JUMP[0] = navigator()
    after = {f: (seq[n + 1] if n + 1 < len(seq) else None) for n, f in enumerate(seq)}
    before = {f: (seq[n - 1] if n else "index.html") for n, f in enumerate(seq)}
    nsec = len(order)

    for n, pg in enumerate(pages):
        sec = by_id[pg["sec"]]
        sib = [p for p in pages if p["sec"] == pg["sec"]]
        rail_items = []  # "Also in" repeated the section front's list: the free room goes to the engraved plate
        rail = ""
        if rail_items:
            rail = (f'<nav id="krail"><h4>Also in {html.escape(sec["title"])}</h4>'
                    + "".join(f'<a href="{p["file"]}"><b>{html.escape(p["title"])}</b></a>' for p in rail_items)
                    + "</nav>")
        nxt = after[pg["file"]]
        label = None
        if nxt and nxt in front.values():
            label = f'Next: {_TITLES[nxt]}'
        doc = page(pg["title"], slim(link_fix(pg["html"])) + rail, me, data["bodyClass"] + " kcard", sec=pg["sec"],
                   prev=before[pg["file"]], nxt=nxt, stamp=stamp_txt, run_left=html.escape(sec["title"]),
                   run_right="", fonts=font_links, next_label=label,
                   run_href=front[pg["sec"]], jump=navigator(pg["sec"], pg["file"]))
        with open(os.path.join(out, pg["file"]), "w") as f:
            f.write(doc)

    # Section fronts: the name, the deck and every story in it.
    for num, i in enumerate(order, 1):
        sec = by_id[i]
        cards = [pg for pg in pages if pg["sec"] == i]
        rows = "".join(
            f'<li><a href="{pg["file"]}"><span class="kn">{pg["k"]:02d}</span><span class="kt"><b>{html.escape(pg["title"])}</b>'
            f'<small>{html.escape(teaser(pg))}</small></span></a></li>' for pg in cards)
        if i == "science" and cards:
            # One page of briefs: the front lists the briefs themselves.
            rows = "".join(
                f'<li><a href="{cards[0]["file"]}"><span class="kn">{n:02d}</span><span class="kt"><b>{html.escape(_text(t))}</b></span></a></li>'
                for n, t in enumerate(re.findall(r'<(?:h3 class="kfold"|b class="sci-title")[^>]*>(.*?)</(?:h3|b)>', cards[0]["html"], re.S), 1))
        body = (f'<div class="kfhead" data-n="{len(cards) if i != "science" else rows.count("<li>")}"><div><p class="kkick">{html.escape(part_of[i])}</p>'
                f'<h2 class="kfname">{html.escape(sec["title"])}</h2>'
                f'<p class="kfsub">{html.escape(sec.get("sub") or "")}</p></div><span class="kfnum">{kindle_orn.roman(num)}</span></div>'
                f'<ol class="kfl">{rows}</ol>')
        with open(os.path.join(out, front[i]), "w") as f:
            f.write(page(sec["title"], body, me, data["bodyClass"] + " ksecfront", sec=i,
                         prev=before[front[i]], nxt=after[front[i]], stamp=stamp_txt,
                         run_left="&lsaquo; The front", run_right="", fonts=font_links, jump=navigator(i)))

    # The end of the edition: where to go from here.
    with open(os.path.join(out, "end.html"), "w") as f:
        f.write(page("The end", f'<div class="kend"><p class="kkick">The Morning Edition</p><h2 class="kfname">That&rsquo;s the edition.</h2>'
                     f'<p class="kfsub">A new one is printed every hour. Have a good day.</p>'
                     f'<a class="kbig" href="index.html">Back to the front &rsaquo;</a>'
                     + ('<div class="kpanel kcolophon"><p class="kkick">Supplied by</p><p>' + " ".join(
                         f'<b>{html.escape(by_id[i]["title"])}:</b> {html.escape(", ".join(list(dict.fromkeys(re.sub(r"^(Sources?|From|Data:?)\s+", "", n.strip()).split(" (")[0] for m in credits[i] for n in re.split(r"\s*[·,;]\s*", _text(m)) if 2 < len(n.strip()) < 32))[:3]))}.'
                         for i in order if credits.get(i)).replace(':</b> .', ':</b>').replace(' <b>Little one:</b>', '') + '</p></div>' if credits else "") + '</div>',
                     "kme", "ksecfront kendpage", prev=before["end.html"], nxt="index.html", stamp=stamp_txt,
                     run_left="&lsaquo; The front", run_right="", fonts=font_links, next_label="The front"))

    if False:   # the Sources pages: replaced by each page's credit line and the colophon on The end
        rows = "".join(f'<h3>{html.escape(by_id[i]["title"])}</h3><p>{" &middot; ".join(credits[i])}</p>'
                       for i in order if credits.get(i))
        with open(os.path.join(out, "sources.html"), "w") as f:
            f.write(page("Sources and credits", f'<div class="head"><p class="kkick">The back page</p><h2>Sources and credits</h2></div>'
                         f'<div class="kcredits">{rows}</div>', me, data["bodyClass"] + " kcard",
                         prev="index.html", nxt=None, stamp=stamp_txt, run_left="The Morning Edition",
                         run_right="", fonts=font_links))

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
                         f'<span class="kc">{cnt} {"page" if cnt == 1 else "pages"}</span></a></li>')
        toc.append(f'<p class="kpart">{html.escape(name)}</p><ul class="kpartbox">{"".join(cells)}</ul>')
    import datetime as _dt
    doy = _dt.datetime.strptime(longdate, "%A, %B %d, %Y").timetuple().tm_yday  # Pacific date
    hi = re.search(r"High (\d+°)", _text(by_id.get("today", {}).get("cards", [{}])[0].get("html", "")) if by_id.get("today") else "")
    wx = ""
    if g.get("temp"):
        wx = (f'<div class="kgl {kindle_orn.wx_class(g.get("where", ""))}"><div class="kdeg">{html.escape(g["temp"])}<small>{html.escape(g.get("where", ""))}</small></div>'
              '</div>')
    body = (f'<div class="kmast"><div class="kear"><span>Sauvie Island, Ore.</span><span class="kcrest">{OWNER_INITIAL}</span><span>No. {doy}</span></div>'
            f'<p class="kname"><i>The</i> Morning Edition</p>'
            f'<p class="kdate">{html.escape(longdate.rsplit(",", 1)[0])}{" &middot; " + html.escape(g["holiday"]) if g.get("holiday") else ""}'
            f' &middot; {html.escape(edition)} edition</p></div>'
            + wx
            + (f'<p class="klab">Top of the edition</p><div class="kleads">{leads}</div>' if leads else "")
            + f'<div class="ktoc kbreak"><h2 class="ktochead" id="contents">Contents</h2>{"".join(toc)}</div>'
)
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(page("The Morning Edition", body, "kme", "kcontents", nxt=(seq[1] if len(seq) > 1 and seq[0] == "today.html" else seq[0]) if seq else None,
                     stamp=stamp_txt, run_left="", run_right="", fonts=font_links))
    _t1 = os.path.join(out, "today-01.html")
    _sr = re.search(r'Sunrise</span><span class="v"[^>]*>([^<]+)<', open(_t1).read()) if os.path.exists(_t1) else None
    _tf = re.search(r"-?\d+", data.get("front", {}).get("temp", "") or "")
    kindle_orn.COVER_DAY.update({"temp_f": int(_tf.group(0)) if _tf else None, "sky": (data.get("front", {}).get("where", "") or "").split("·")[-1].strip()})
    kindle_orn.write_frames(out, _dt.datetime.strptime(longdate, "%A, %B %d, %Y").date().isoformat(),
                            ("Sunrise " + _sr.group(1)) if _sr else "")
    try:  # each page's own engraved plate, cut to the room its sheets leave this morning
        from . import kindle_plates
        kindle_plates.run(out, _dt.datetime.strptime(longdate, "%A, %B %d, %Y").date().isoformat())
    except Exception as e:  # noqa: BLE001  -- never lose the edition over the art
        print(f"kindle_full: plates skipped: {e!r}", file=sys.stderr)
    write_offline(out, BUILD["id"])
    n = len(pages)
    # The old bookmark (kindle.html) opens the edition.
    with open(os.path.join(site, "kindle.html"), "w") as f:
        f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=kindle/index.html">'
                '<a href="kindle/index.html">Open the Morning Edition</a>')
    print(f"kindle_full: wrote {n} pages in {len(order)} sections to {out}")


if __name__ == "__main__":
    main(sys.argv[1])
