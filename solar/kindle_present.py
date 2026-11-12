"""How the Morning Edition presents its data: answer first, statuses stated, one panel per block of text.

Runs over every page's card HTML after the snapshot (so it works the same on a fresh snapshot and on a
cached one), in a blank Chromium page, before the pages are written:

  * per-card editing: the answer is written out in plain words and set first and largest; each row says its
    status in a word (Hidden / Out, Open / Closed ...); numbers compared across rows get a shared-scale bar;
    rows with nothing to say (a trail with no report text, an empty box) are dropped;
  * the contract with the frame and engraving team: every block of readable text sits in one
    <div class="kpanel">, the full column wide. Their ornament goes only outside .kpanel rectangles, so the
    gaps between panels are deliberate (CSS var --kgap);
  * inline styles the live dashboard left behind (margins, sizes, gaps) are taken off so the edition's own
    type scale (CSS below) is the only one.

    from solar import kindle_present
    kindle_present.run(pages, today_iso)      # pages: [{"html", "file", "sec"}], edited in place
"""
import json
import os
import sys

PRESENT = r"""
(args) => {
  const pages = args.pages, TODAY = new Date(args.today + 'T12:00:00');
  const $$ = (r, s) => Array.from(r.querySelectorAll(s));
  const txt = el => el ? (el.textContent || '').replace(/\s+/g, ' ').trim() : '';
  const make = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const kill = el => { if (el && el.parentNode) el.parentNode.removeChild(el); };
  const MON = {Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5, Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11};
  const daysAgo = s => { const m = /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* (\d{1,2})/.exec(s || ''); if (!m) return null;
    let d = new Date(TODAY.getFullYear(), MON[m[1]], +m[2], 12); if (d - TODAY > 864e5 * 2) d = new Date(TODAY.getFullYear() - 1, MON[m[1]], +m[2], 12);
    return Math.round((TODAY - d) / 864e5); };
  const ago = n => n == null ? '' : n <= 0 ? 'today' : n === 1 ? 'yesterday' : n < 14 ? n + ' days ago' : Math.round(n / 7) + ' weeks ago';
  const words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
  const num = n => words[n] || String(n);
  const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  const answer = (card, html, detail) => {   // the page's answer, set first and largest under the title
    for (const v of $$(card, '.kverdict:not(.kalfred)')) kill(v);
    const a = make('div', 'kanswer', '<p class="kans' + (html.length > 64 ? ' klong' : '') + '">' + html + '</p>' + (detail ? '<p class="kansd">' + detail + '</p>' : ''));
    const head = card.querySelector(':scope > .head');
    if (head) head.after(a); else card.prepend(a);
    return a;
  };
  const status = (word, tone) => '<b class="kst' + (tone ? ' kst-' + tone : '') + '">' + esc(word) + '</b>';
  const step = (name, f) => { try { f(); } catch (e) { console.log('kindle present ' + name + ': ' + e); } };

  // ---- inline styles the live page left: only geometry that carries data survives
  const DROP = /^(margin|margin-top|margin-bottom|padding-top|padding-bottom|gap|row-gap|column-gap|font|font-size|font-family|line-height|letter-spacing|color|-webkit-text-fill-color|border-top-color|border-bottom-color|border-left-color|border-right-color)$/;
  function clean(d) {
    for (const el of $$(d, '[style]')) {
      if (el.closest('svg')) continue;
      const keep = [];
      for (const decl of el.getAttribute('style').split(';')) {
        const i = decl.indexOf(':'); if (i < 0) continue;
        const p = decl.slice(0, i).trim().toLowerCase(), v = decl.slice(i + 1).trim();
        if (DROP.test(p)) continue;
        keep.push(p + ':' + v);
      }
      if (keep.length) el.setAttribute('style', keep.join(';')); else el.removeAttribute('style');
    }
    for (const el of $$(d, 'b[style], strong[style]')) el.removeAttribute('style');
    // empty boxes: notes with nothing in them, camera strips with no cameras
    for (const el of $$(d, 'p, .cams, .note, .meta, small, .mtn-st')) if (!txt(el) && !el.querySelector('img,svg,i[style]')) kill(el);
    for (const el of $$(d, 'font')) el.replaceWith(...el.childNodes);
  }

  // ---- the cards
  const CARDS = {
    // Is the mountain out?  The answer in a word, each peak's status in a word.
    'mtn-card': card => {
      const rows = $$(card, '.mtn'); if (!rows.length) return;
      const v = card.querySelector('.kverdict'), allHidden = /hidden today and tomorrow/i.test(txt(v));
      const peaks = rows.map(r => {
        const name = txt(r.querySelector('b')), sm = txt(r.querySelector('small'));
        const st = r.querySelector('.mtn-st'), s = st ? txt(st.querySelector('.st')) : '', tm = st ? txt(st.querySelector('small')).replace(/^Tomorrow:\s*/i, '') : '';
        let now = 'Hidden', tone = 'off', when = '';
        if (/Out now/i.test(s)) { now = 'Out now'; tone = 'on'; }
        else if (s && !/Hidden/i.test(s)) { now = 'Clears'; tone = 'on'; when = s; }
        else if (!s && !allHidden) now = '';
        const tomorrow = tm || (allHidden ? 'hidden' : '');
        const m = /Look ([\w-]+), (\d+) miles · ([\d,]+) ft/.exec(sm);
        return { name, now, tone, when, tomorrow, look: m ? m[1] : '', mi: m ? m[2] : '', ft: m ? m[3] : '', sm };
      });
      const out = peaks.filter(p => p.now === 'Out now'), clr = peaks.filter(p => p.now === 'Clears'), all = peaks.length;
      const tmOpen = peaks.filter(p => p.tomorrow && !/hidden/i.test(p.tomorrow));
      let a, d = '';
      if (out.length) a = 'Yes — ' + (out.length === all ? 'all ' + num(all) + ' peaks are out now.' : out.map(p => p.name).join(' and ') + (out.length > 1 ? ' are' : ' is') + ' out now.');
      else if (clr.length) a = 'Not yet — ' + clr.map(p => p.name + ' clears ' + p.when).join('; ') + '.';
      else if (peaks.every(p => p.now === 'Hidden')) a = 'No — ' + (all === 3 ? 'all three' : 'all ' + num(all)) + ' peaks hidden today' + (tmOpen.length ? '.' : peaks.every(p => p.tomorrow) ? ' and tomorrow.' : '.');
      if (!a) return;
      if (tmOpen.length && !out.length) d = 'Tomorrow: ' + tmOpen.map(p => p.name + ' ' + p.tomorrow).join('; ') + '.';
      const fact = card.querySelector('#mtn > p.note');
      const t = make('div', 'ktable kmtn');
      t.innerHTML = '<div class="kth"><span>Peak</span><span>Today</span><span>Tomorrow</span></div>' + peaks.map(p =>
        '<div class="krow"><span class="kcell kname"><b>' + esc(p.name) + '</b><small>' + (p.look ? esc('Look ' + p.look + ' · ' + p.mi + ' mi · ' + p.ft + ' ft') : esc(p.sm)) + '</small></span>' +
        '<span class="kcell">' + status(p.now === 'Clears' ? p.when : p.now, p.tone) + '</span>' +
        '<span class="kcell ktm">' + (p.tomorrow ? status(/hidden/i.test(p.tomorrow) ? 'Hidden' : p.tomorrow) : '') + '</span></div>').join('');
      const box = card.querySelector('#mtn'); box.innerHTML = ''; box.appendChild(t);
      if (fact) { fact.className = 'kfoot-note'; box.appendChild(fact); }
      answer(card, esc(a), d && esc(d));
    },

    // Trail reports: only a report that says something, as the payload.
    'trail-card': card => {
      const rows = $$(card, '#trails > div');
      let kept = 0;
      for (const r of rows) {
        const left = r.firstElementChild, right = r.lastElementChild;
        const name = txt(left.querySelector('b'));
        const smalls = $$(left, 'small'), issues = smalls.map(txt).filter(s => /^·/.test(s)).map(s => s.replace(/^·\s*/, ''))[0] || '';
        const quote = smalls.map(txt).filter(s => /^[“"]/.test(s))[0] || '';
        if (!issues && !quote) { kill(r); continue; }
        const date = ((/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* \d{1,2}(?!\d)/.exec(right.firstChild ? right.firstChild.textContent : txt(right)) || [''])[0]), n = daysAgo(date);
        if (n != null && n > 21) { kill(r); continue; }
        const tags = issues.split(/;\s*/).filter(Boolean);
        const q = quote.replace(/^[“"]/, '').replace(/[”"](\s*·.*)?$/, ''), by = (/[”"]\s*·\s*(.+)$/.exec(quote) || [])[1] || '';
        r.className = 'krow ktrail'; r.innerHTML =
          '<span class="kcell kname"><b>' + esc(name) + '</b><small>' + esc(date) + (n != null ? ' · ' + ago(n) : '') + '</small></span>' +
          '<span class="kcell kwide">' + (tags.length ? '<span class="ktags">' + tags.map(t => status(t)).join('<i> · </i>') + '</span>' : '') +
          (q ? '<span class="kquote">“' + esc(q.length > 230 ? q.slice(0, 220).replace(/\s+\S*$/, '') + '…' : q) + '”' + (by ? ' <small>— ' + esc(by) + '</small>' : '') + '</span>' : '') + '</span>';
        kept++;
      }
      if (!kept) return 'drop';
      card.querySelector('#trails').className = 'ktable ktrails';
    },

    // Road incidents: the answer, then one ruled table, nearest to Portland first.
    'road-card': card => {
      const rows = $$(card, '#road-incidents > div'); if (!rows.length) return;
      const NEAR = /portland|beaverton|hillsboro|gresham|tigard|lake oswego|scappoose|st\.? helens|sauvie|cornelius|union rd|linnton|st\.? johns|vancouver|\bi-?5\b|\bi-?84\b|\bi-?205\b|\bi-?405\b|\bor-?127\b/i;
      const COAST = /astoria|seaside|cannon beach|tillamook|lincoln city|newport|coast|us-?101|warrenton|gearhart|manzanita/i;
      const it = rows.map(r => {
        const b = txt(r.querySelector('b')), sm = txt(r.querySelector('small')), delay = txt(r.lastElementChild);
        const [what, road] = b.split(/\s*·\s*/);
        const parts = sm.split(/\s*·\s*/), where = (parts[0] || '').replace(/^[A-Z]{2,3}\d+,\s*/, ''), say = parts.slice(1).join(' · ');
        const all = b + ' ' + sm, rank = NEAR.test(all) && !COAST.test(where) ? 0 : COAST.test(all) ? 2 : 1;
        const closed = /clos/i.test(all + delay);
        const d = delay.replace(/^Delay (of )?/i, '').replace(/hours?/, 'hr').replace(/\s+-\s+/, '–');
        const sev = /hour|hr/.test(delay) ? 2 : closed ? 3 : 1;
        const why = say.replace(/\s*Prepare to [^.]*\.|\s*Use caution[^.]*\.|\s*Expect delays[^.]*\./gi, '').trim();
        return { what, road: road || '', where, why, d: closed ? 'Closed' : cap(d), rank, closed, sev };
      }).sort((a, b) => a.rank - b.rank || b.sev - a.sev);
      const near = it.filter(x => x.rank === 0), coast = it.filter(x => x.rank === 2), mid = it.filter(x => x.rank === 1);
      const roads = xs => xs.map(x => x.road).filter((v, i, a) => v && a.indexOf(v) === i).join(', ');
      const closures = it.filter(x => x.closed).length;
      let a = closures ? cap(num(closures)) + ' closure' + (closures > 1 ? 's' : '') : 'No closures';
      a += near.length ? '. Near home: ' + near.map(x => x.road + ' ' + x.what.toLowerCase().replace(/ operations/, '') + ', ' + x.d.toLowerCase()).join('; ') + '.' : ' near Portland.';
      let dd = [];
      if (mid.length) dd.push(cap(num(mid.length)) + ' elsewhere (' + roads(mid) + ').');
      if (coast.length) dd.push(cap(num(coast.length)) + ' minor work zone' + (coast.length > 1 ? 's' : '') + ' on the coast (' + roads(coast) + ')' +
        (coast.every(x => /under 20/i.test(x.d)) ? ', delays under 20 min.' : '.'));
      const t = make('div', 'ktable kroads');
      t.innerHTML = '<div class="kth"><span>Road</span><span>Delay</span></div>' + it.map(x =>
        '<div class="krow"><span class="kcell kwide"><b>' + esc(x.road + (x.road ? ' · ' : '') + x.what.replace(/ Operations$/, '')) + '</b>' +
        '<small>' + esc(x.where) + (x.why ? ' — ' + esc(x.why.length > 90 ? x.why.slice(0, 86).replace(/\s+\S*$/, '') + '…' : x.why) : '') + '</small></span>' +
        '<span class="kcell kright">' + (x.closed ? status('Closed', 'on') : '<b class="kval' + (x.sev > 1 ? ' kval-on' : '') + '">' + esc(x.d) + '</b>') + '</span></div>').join('');
      card.querySelector('#road-incidents').replaceWith(t);
      answer(card, esc(a), esc(dd.join(' ')));
    },

    // Seven days: temperature range, rain and solar on shared scales, one aligned grid.
    'fc-card': card => { forecastGrid(card, '#forecast'); },
  };

  // A row of days compared: shared-scale range bars (temperature), gauges (rain), bars (energy).
  function forecastGrid(card, sel) {
    const box = card.querySelector(sel); if (!box) return;
    const fds = $$(box, '.fd'); if (fds.length < 3) return;
    const days = fds.map(f => {
      const t = txt(f.querySelector('.t')).match(/-?\d+/g) || [], r = txt(f.querySelector('.r')), e = txt(f.querySelector('.e'));
      const cond = (f.getAttribute('title') || r.split('·')[0] || '').trim();
      return { d: txt(f.querySelector('.d')), hi: +t[0], lo: t[1] != null ? +t[1] : +t[0], rain: +((/(\d+)%/.exec(r) || [0, NaN])[1]), cond,
               kwh: +((/(\d+)\s*kWh/.exec(e) || [0, NaN])[1]), meta: txt(f.querySelector('.meta')) };
    });
    const hasRain = days.some(x => !isNaN(x.rain)), hasSun = days.some(x => !isNaN(x.kwh));
    const lo = Math.min(...days.map(x => x.lo)), hi = Math.max(...days.map(x => x.hi)), span = Math.max(1, hi - lo);
    const kmax = Math.max(1, ...days.filter(x => !isNaN(x.kwh)).map(x => x.kwh)), best = days.reduce((a, b) => (b.kwh > (a ? a.kwh : -1) ? b : a), null);
    const g = make('div', 'kgrid kfc' + (hasSun ? ' ksun' : '') + (hasRain ? '' : ' knorain'));
    let h = '<div class="kth"><span>Day</span><span>Low – high °F <em>' + lo + '° to ' + hi + '° this week</em></span>' + (hasRain ? '<span>Rain chance</span>' : '') + (hasSun ? '<span>Solar kWh</span>' : '') + '</div>';
    for (const x of days) {
      const L = (x.lo - lo) / span * 100, W = Math.max(2, (x.hi - x.lo) / span * 100);
      h += '<div class="krow"><span class="kcell kday"><b>' + esc(x.d) + '</b><small>' + esc(x.cond) + '</small></span>' +
        '<span class="kcell ktemp"><span class="ktrack"><i class="kbr" style="left:' + L.toFixed(1) + '%;width:' + W.toFixed(1) + '%"></i>' +
        '<em class="klo" style="right:' + (100 - L).toFixed(1) + '%">' + x.lo + '°</em><em class="khi" style="left:' + (L + W).toFixed(1) + '%">' + x.hi + '°</em></span></span>' +
        (hasRain ? '<span class="kcell krain"><span class="kgauge"><i style="width:' + (isNaN(x.rain) ? 0 : x.rain) + '%"></i></span><b>' + (isNaN(x.rain) ? '–' : x.rain + '%') + '</b></span>' : '') +
        (hasSun ? '<span class="kcell kkwh"><span class="kgauge ksolid"><i style="width:' + (isNaN(x.kwh) ? 0 : x.kwh / kmax * 100).toFixed(1) + '%"></i></span><b>' + (isNaN(x.kwh) ? '–' : x.kwh) + (x === best ? '<sup>best</sup>' : '') + '</b></span>' : '') +
        (x.meta && !hasSun ? '<span class="kcell kmeta">' + esc(x.meta) + '</span>' : '') + '</div>';
    }
    g.innerHTML = h; box.replaceWith(g); g.id = sel.slice(1);
    const v = card.querySelector('.kverdict');
    if (v) { const m = txt(v); kill(v); answer(card, esc(m.replace(/~/g, '').replace(/\(([\d]+) kWh\)/g, '($1 kWh)'))); }
  }

  // ---- panels: one per block of readable text, the whole column wide
  const HEAD = ':scope > .head, :scope > .brief-head, :scope > h2, :scope > .kh2, :scope > .team-top, :scope > h3.kfold';
  const BREAK = /^(H3|H4|DETAILS)$/;
  function panelize(root) {
    const conts = [];
    const isCont = el => !el.matches('.head, .brief-head, .team-top, .kanswer, .kgrid, .ktable') && el.querySelector(HEAD);
    const walk = el => { if (isCont(el)) conts.push(el); for (const c of el.children) if (!/^(svg|SVG|TABLE|UL|OL|P)$/.test(c.tagName)) walk(c); };
    if (isCont(root)) conts.push(root);
    for (const c of root.children) walk(c);
    const hasCont = el => conts.some(c => c !== el && el.contains(c));
    for (const c of conts.reverse()) {
      let cur = null;
      for (const ch of Array.from(c.children)) {
        if (ch.classList.contains('kpanel') || ch.id === 'krail' || conts.includes(ch) || hasCont(ch)) { cur = null; continue; }
        const head = ch.matches(HEAD.replace(/:scope > /g, ''));
        const brk = (BREAK.test(ch.tagName) || ch.classList.contains('sub') || ch.classList.contains('day-h')) && !(cur && cur.children.length === 1 && cur.firstElementChild.matches('.head,.brief-head,h2,.kh2'));
        if (!cur || head || brk) { cur = make('div', 'kpanel'); ch.before(cur); }
        cur.appendChild(ch);
      }
    }
    // a panel holding only an empty shell goes
    for (const p of $$(root, '.kpanel')) if (!txt(p) && !p.querySelector('img,svg,.bars,.khr,.kmix,.kgrid')) kill(p);
  }

  // ---- the plan: item caps, held cuts, the credit line
  const LISTS = ['.story', '.lines > div', '.idea', '.deal', '.sp', '.mush', '.ktable > .krow', '.rep', '.bday', 'li'];
  function capList(card, n) {
    const mine = sel => $$(card, sel).filter(e => !e.closest('.kbrief') || !!card.closest('.kbrief'));
    for (const sel of LISTS) { const xs = mine(sel).filter(e => !e.closest('.kmile')); if (xs.length > n) { xs.slice(n).forEach(kill); return; } }
  }
  const HEADS = 'h3, h4, .sub, .day-h, summary, .shelf-h';
  function cutSection(card, re) {
    for (const h of $$(card, HEADS)) {
      if (!card.contains(h) || !re.test(txt(h))) continue;
      let n = h.nextElementSibling; kill(h);
      while (n && !n.matches(HEADS)) { const nx = n.nextElementSibling; kill(n); n = nx; }
    }
  }
  // keep a section's heading and its first n items (rows of its list, or paragraphs)
  function shrinkSection(card, re, n) {
    for (const h of $$(card, HEADS)) {
      if (!card.contains(h) || !re.test(txt(h))) continue;
      const sib = []; for (let x = h.nextElementSibling; x && !x.matches(HEADS); x = x.nextElementSibling) sib.push(x);
      if (!n) { kill(h); sib.forEach(kill); continue; }
      if (sib.length === 1 && sib[0].children.length > n && !/^P$/.test(sib[0].tagName)) Array.from(sib[0].children).slice(n).forEach(kill);
      else sib.slice(n).forEach(kill);
    }
  }
  const SHRINK = {
    'civics-votes': ['reps-h', /floor votes/i], 'civics-news': ['reps-h', /in the news/i], 'born-today': ['hist-h', /born today/i],
    'also-nearby': ['near-h', /also nearby/i], 'asteroids': ['sky-h', /asteroid|close approach/i],
    'team-news': [null, /in the news|fan pulse|latest news|what fans|latest/i], 'long-writeups': ['mkt-h', /what moved|worth watching|why it moved/i],
    'planes': ['plane-h', null], 'bday-lists': ['bday-h', null],
  };
  const SRC = /\b(TomTom|TripCheck|ODOT|WTA|NIFC|USGS|BPA|Google( News)?|Wikidata|Metacritic|Wikipedia|eBird|iNaturalist|Open-Meteo|NOAA|SWPC|NWS|CDC|Goodreads|Library of Congress|Internet Archive|Art Institute|TVmaze|TMDB|Yahoo|PVGIS|NASA|SDO|APsystems|Ambient|ESPN|7Timer|CelesTrak|JPL|AISstream|EIA|Redfin|Zillow|Ticketmaster|Songkick)\b/;
  function credit(d, extra) {
    const names = [];
    for (const m of $$(d, '.head .meta')) {
      const parts = txt(m).split(/\s*·\s*/), keep = [];
      for (const p of parts) (SRC.test(p) && p.length < 40 ? names : keep).push(p);
      if (keep.length !== parts.length) { if (keep.length) m.textContent = keep.join(' · '); else kill(m); }
    }
    for (const n of (extra || '').split(/\s*·\s*/)) if (n) names.push(n.replace(/^Sources?:?\s*/i, ''));
    for (const p of $$(d, 'p, small, span.cite, .src-line')) { const t = txt(p);
      if (/^Sources?:?\s/i.test(t) && t.length < 120) { names.push(t.replace(/^Sources?:?\s*/i, '')); kill(p); } }
    const uniq = names.map(x => x.trim()).filter((x, i, a) => x && a.indexOf(x) === i);
    if (!uniq.length) return;
    const last = $$(d, '.kpanel').pop(); if (!last) return;
    last.appendChild(make('p', 'kcredit', 'Source' + (uniq.length > 1 ? 's' : '') + ': ' + esc(uniq.join(' · '))));
  }

  return pages.map(pg => {
    const d = document.createElement('div'); d.innerHTML = pg.html;
    step('clean', () => clean(d));
    step('shrink', () => { const sh = args.shrink || {}; for (const k in SHRINK) if (k in sh) { const c = SHRINK[k], n = sh[k];
      const h = c[0] && d.querySelector('#' + c[0]), card = h ? (h.closest('.card, .brief, section') || d) : (c[0] ? null : (pg.sec === 'sports' ? d : null));
      if (!card) continue;
      if (c[1]) shrinkSection(card, c[1], n); else capList(card, n);
      if (k === 'long-writeups') for (const id of ['mkt-h', 'he-h']) { const hh = d.querySelector('#' + id); if (!hh) continue;
        for (const p of $$(hh.closest('.card') || d, 'p.summary, p.note, .summary')) { const t = txt(p);
          if (t.length > 220) { const cut = t.slice(0, 210).replace(/\s+\S*$/, ''); const m = /^(.{60,210}?[.!?])\s/.exec(t); p.textContent = m ? m[1] : cut + '…'; } } } } });
    // today's front: one title, no tiles that belong to other pages, no quiet-alert line
    step('today', () => { const tc = d.querySelector('#today-card'); if (!tc || !d.querySelector('.kfrontwx')) return;
      kill(tc.querySelector(':scope > .head'));
      for (const m of $$(tc, '.mini')) if (/^(Daylight|Solar tomorrow|Smoke outlook)/i.test(txt(m.querySelector('.k')))) kill(m);
      for (const a of $$(d, '.allclear')) if (/^No strong weather/i.test(txt(a))) kill(a); });
    // the weather station: the answer and the jar; not the 3-day yard table, the heat filler or the since-start total
    step('station', () => { const w = d.querySelector('#wx-h'); if (!w) return;
      for (const p of $$(d, 'p, .note')) if (/^Solar panels lose some output/.test(txt(p))) kill(p);
      for (const x of $$(d, '.yd')) kill(x.closest('.yd-row, .yard-days') || x);
      for (const x of $$(d, 'span, div, small')) if (/^Since your gauge started/.test(txt(x)) && txt(x).length < 40) kill(x); });
    // the little one: "Coming up at 3" as its own titled block with the skills as a list; the CDC credit to the foot
    step('milestones', () => { const g = d.querySelector('#kid-grow'); if (!g) return;
      const src = Array.from(g.querySelectorAll('span')).filter(x => /CDC/.test(txt(x)));
      src.forEach(kill); if (src.length) pg.credit = (pg.credit ? pg.credit + ' · ' : '') + 'CDC developmental milestones';
      const m = /^Coming up:\s*by (\d+) (years?|months?),? most kids can (.+?)\.?$/i.exec(txt(g)); if (!m) return;
      const items = [];
      for (const x of m[3].split(/,\s*(?:and\s+)?|\s+and\s+/).map(x => x.trim()).filter(Boolean)) {
        if (items.length && /^(who|what|where|when|why|how)\b/i.test(x) && /\b(who|what|where|when|why|how)$/i.test(items[items.length - 1]))
          items[items.length - 1] += (/questions$/.test(x) ? ' and ' : ', ') + x; else items.push(x); }
      const box = make('div', 'kmile', '<h3>Coming up at ' + esc(m[1]) + (/month/.test(m[2]) ? ' months' : '') + '</h3><p class="kmile-k">Most kids can:</p><ul>' +
        items.map(x => '<li>' + esc(cap(x)) + '</li>').join('') + '</ul>');
      g.replaceWith(box); });
    // the play ideas: when to do it is a kicker, the idea a row label, the how a line
    step('ideas', () => { for (const i of $$(d, '.idea')) { const sm = i.querySelector(':scope > small'); if (sm) sm.className = 'kkick kidea-k'; } });
    // the scoreboard: merged teams print score, next game and standing; their recaps and fan talk shrink away
    step('scoreboard', () => { if (pg.sec !== 'sports') return;
      for (const k of $$(d, '.kbrief')) { for (const r of $$(k, '.recap p, .recap small')) kill(r);
        shrinkSection(k, /fan pulse|championship|standings|title fight/i, 3); } });
    // tickets: the run-on "Already on sale" paragraph is noise
    step('tickets', () => { for (const p of $$(d, 'p.kalso')) if (/^Already on sale/.test(txt(p))) kill(p); });
    step('caps', () => { for (const id in (args.caps || {})) { const h = d.querySelector('#' + id); if (!h) continue;
      capList(h.closest('section.card, .card, .brief') || h.parentElement, args.caps[id]); } });
    for (const id in CARDS) {
      const card = d.querySelector('#' + id); if (!card) continue;
      step(id, () => {
        if (CARDS[id](card) === 'drop') { let x = card.closest('.kbrief') || card; kill(x); }
      });
    }
    step('panels', () => panelize(d));
    step('credit', () => credit(d, pg.credit));
    return d.innerHTML;
  });
}
"""

CSS = r"""
/* ===== The data system (kindle_present): answer first, statuses stated, one panel per text block ===== */
:root{--kgap:16px;--kpx:10px;--kpy:6px;
  --ks-ans:27px;--kl-ans:33px;--ks-h:25px;--kl-h:30px;--ks-row:18px;--kl-row:24px;--ks-sm:15px;--kl-sm:20px;--ks-lab:13px;--kl-lab:16px}
/* the panel: white ground, the whole column wide, one left and one right edge, a fixed inset */
#kview #kmain .kpanel{display:block !important;position:relative;box-sizing:border-box !important;width:auto !important;
  margin:0 0 var(--kgap) !important;padding:var(--kpy) var(--kpx) !important;background:#fff !important;border:0 !important;float:none !important}
#kview #kmain .kpanel:last-child{margin-bottom:0 !important}
#kview #kmain .kpanel>*:first-child{margin-top:0 !important;border-top:0 !important;padding-top:0 !important}
#kview #kmain .kpanel>*:last-child{margin-bottom:0 !important}
/* wrappers around panels carry no space of their own */
#kview #kmain .group,#kview #kmain .sec-body,#kview #kmain section.card,#kview #kmain .brief,#kview #kmain .kbrief{margin:0 !important;padding:0 !important;border:0 !important;background:none !important}
#kview #kmain .kbrief,#kview #kmain .group+.kbrief,#kview #kmain .kpanel+.group,#kview #kmain .kpanel+.kbrief,#kview #kmain .group+.group,#kview #kmain .kpanel+.allclear{margin-top:var(--kgap) !important}
#kview #kmain .kpanel .head{background:none !important;padding:0 !important;margin:0 0 4px !important}
#kview #kmain .kpanel .head:before,#kview #kmain .kpanel .head:after{display:none !important}

/* one type scale: kicker, title, answer, row label, value, status, small detail */
#kview #kmain .kpanel *{font-family:var(--k-serif) !important}
#kview #kmain .kpanel .kkick,#kview #kmain .kpanel .kkicker,#kview #kmain .kpanel .shelf-h,#kview #kmain .kpanel .sci-topic,#kview #kmain .kpanel .rec-k,
#kview #kmain .kpanel .kth,#kview #kmain .kpanel .idea>small,#kview #kmain .kpanel .k,#kview #kmain .kpanel h3,#kview #kmain .kpanel .sub,#kview #kmain .kpanel .day-h{
  font:600 var(--ks-lab)/var(--kl-lab) var(--k-serif) !important;letter-spacing:.14em !important;text-transform:uppercase !important;font-style:normal !important;color:#000 !important}
#kview #kmain .kpanel h3,#kview #kmain .kpanel .sub,#kview #kmain .kpanel .day-h{border:0 !important;border-bottom:1px solid #000 !important;padding:0 0 3px !important;margin:0 0 6px !important;background:none !important}
#kview #kmain .kpanel h2,#kview #kmain .kpanel .kh2{font:800 var(--ks-h)/var(--kl-h) var(--k-disp) !important;margin:2px 0 0 !important;letter-spacing:-.005em !important}
#kview #kmain .kpanel h3.kfold{font:800 21px/26px var(--k-disp) !important;letter-spacing:0 !important;text-transform:none !important;border:0 !important;padding:0 !important;margin:2px 0 0 !important}
#kview #kmain .kpanel .head .meta{display:block !important;font:italic 430 var(--ks-sm)/var(--kl-sm) var(--k-serif) !important;margin:2px 0 0 !important}
#kview #kmain .kpanel p,#kview #kmain .kpanel .note,#kview #kmain .kpanel .summary{font:430 var(--ks-row)/var(--kl-row) var(--k-serif) !important;margin:0 0 6px !important}
#kview #kmain .kpanel small,#kview #kmain .kpanel .meta,#kview #kmain .kpanel .s{font:italic 430 var(--ks-sm)/var(--kl-sm) var(--k-serif) !important}
#kview #kmain .kpanel b,#kview #kmain .kpanel strong{font-weight:700 !important}

/* the answer: first and largest, plain words */
#kview #kmain .kanswer{margin:6px 0 2px !important;padding:6px 0 0 !important;border-top:3px double #000 !important}
#kview #kmain .kanswer .kans{font:700 var(--ks-ans)/var(--kl-ans) var(--k-serif) !important;letter-spacing:-.01em !important;margin:0 !important}
#kview #kmain .kanswer .kans.klong{font-size:23px !important;line-height:29px !important}
#kview #kmain .kanswer .kansd{font:430 var(--ks-row)/var(--kl-row) var(--k-serif) !important;margin:4px 0 0 !important}
#kview #kmain .kpanel .kverdict{font:700 22px/28px var(--k-serif) !important;margin:6px 0 4px !important}

/* statuses: the boldest thing in the row */
#kview #kmain .kst{font:700 14px/20px var(--k-serif) !important;letter-spacing:.07em !important;text-transform:uppercase !important;white-space:nowrap;color:#000 !important}
#kview #kmain .kst-on{background:#000 !important;color:#fff !important;-webkit-text-fill-color:#fff !important;padding:1px 6px !important}
#kview #kmain .kst-off{border:1.5px solid #000 !important;padding:0 5px !important}

/* a value that is the row's status (a delay, a level): bold figures, black when it matters */
#kview #kmain .kcell b.kval{display:inline-block;font:700 16px/21px var(--k-serif) !important;font-variant-numeric:lining-nums}
#kview #kmain .kcell b.kval-on{background:#000 !important;color:#fff !important;-webkit-text-fill-color:#fff !important;padding:1px 6px !important}
#kview #kmain .ktm .kst{font-weight:600 !important}
/* tables: aligned columns, equal rows, small-caps heads */
#kview #kmain .ktable,#kview #kmain .kgrid{display:block !important;margin:6px 0 0 !important;border-top:1.5px solid #000 !important}
#kview #kmain .kth{display:-webkit-box;display:flex !important;padding:4px 0 3px !important;border-bottom:1px solid #000 !important}
#kview #kmain .krow{display:-webkit-box;display:flex !important;align-items:center;min-height:46px;box-sizing:border-box;padding:5px 0 !important;margin:0 !important;
  border:0 !important;border-bottom:1px solid #8a8a8a !important;background:none !important}
#kview #kmain .krow:last-child{border-bottom:0 !important}
#kview #kmain .kcell{display:block;min-width:0}
#kview #kmain .kcell b{display:block;font:700 var(--ks-row)/var(--kl-row) var(--k-serif) !important}
#kview #kmain .kcell small{display:block;font:italic 430 var(--ks-sm)/var(--kl-sm) var(--k-serif) !important}
#kview #kmain .kcell b.kst{display:inline-block}
#kview #kmain .kpanel .kfoot-note{font:italic 430 var(--ks-sm)/var(--kl-sm) var(--k-serif) !important;margin:6px 0 0 !important;padding:5px 0 0 !important;border-top:1px solid #8a8a8a}
#kview #kmain .kpanel .kfoot-note b{font-style:normal}
/* mountains: peak | today | tomorrow */
#kview #kmain .kmtn .kth>span:first-child,#kview #kmain .kmtn .kname{-webkit-box-flex:1;flex:1 1 auto}
#kview #kmain .kmtn .kth>span:not(:first-child),#kview #kmain .kmtn .krow>.kcell:not(.kname){flex:none;width:104px;text-align:left}
/* roads: road and what | delay */
#kview #kmain .kroads .kwide,#kview #kmain .kroads .kth>span:first-child{-webkit-box-flex:1;flex:1 1 auto}
#kview #kmain .kroads .kright,#kview #kmain .kroads .kth>span:last-child{flex:none;width:124px;text-align:right;padding-left:10px}
#kview #kmain .kroads .kright .kst{white-space:normal;text-align:right}
/* trail reports */
#kview #kmain .ktrails{border-top:1.5px solid #000 !important}
#kview #kmain .ktrail{display:block !important}
#kview #kmain .ktrail .ktags{display:block;margin:3px 0 2px}
#kview #kmain .ktrail .ktags .kst{font-size:13px !important;line-height:18px !important;white-space:normal}
#kview #kmain .ktrail .ktags i{font-style:normal}
#kview #kmain .ktrail .kquote{display:block;font:italic 430 16px/22px var(--k-serif) !important}
#kview #kmain .ktrail .kname small{display:inline;margin-left:6px}
#kview #kmain .ktrail .kname b{display:inline}

/* the week: day | temperature range on one scale | rain gauge | solar bar */
#kview #kmain .kfc .kth>span,#kview #kmain .kfc .krow>.kcell{flex:none}
#kview #kmain .kfc .kday,#kview #kmain .kfc .kth>span:nth-child(1){width:88px}
#kview #kmain .kfc .ktemp,#kview #kmain .kfc .kth>span:nth-child(2){-webkit-box-flex:1;flex:1 1 auto !important;padding:0 6px}
#kview #kmain .kfc .krain,#kview #kmain .kfc .kth>span:nth-child(3){width:86px}
#kview #kmain .kfc .kkwh,#kview #kmain .kfc .kth>span:nth-child(4){width:100px;padding-left:8px}
#kview #kmain .kfc.knorain .kth>span:nth-child(3){width:100px;padding-left:8px}
#kview #kmain .kfc .kth em{font:italic 430 13px/16px var(--k-serif) !important;text-transform:none;letter-spacing:0;margin-left:4px}
#kview #kmain .kfc .kday small{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:14px !important;line-height:17px !important}
#kview #kmain .kfc .krow{min-height:36px;padding:2px 0 !important}
#kview #kmain .kfc .kday b{font-size:17px !important;line-height:20px !important}
#kview #kmain .ktrack{display:block;position:relative;height:24px;margin:0 30px}
#kview #kmain .ktrack .kbr{position:absolute;top:8px;height:8px;background:#000 !important;display:block}
#kview #kmain .ktrack em{position:absolute;top:0;font:700 16px/24px var(--k-serif) !important;font-style:normal !important;white-space:nowrap;font-variant-numeric:tabular-nums lining-nums}
#kview #kmain .ktrack .klo{padding-right:5px;font-weight:430 !important}
#kview #kmain .ktrack .khi{padding-left:5px}
#kview #kmain .kgauge{display:block;position:relative;height:10px;border:1px solid #000;box-sizing:border-box;margin:2px 0 3px;background:#fff !important}
#kview #kmain .kgauge i{display:block;position:absolute;left:0;top:0;bottom:0;
  background:repeating-linear-gradient(135deg,#000 0,#000 1.5px,#fff 1.5px,#fff 3.5px) !important}
#kview #kmain .kgauge.ksolid i{background:#000 !important}
#kview #kmain .krain b,#kview #kmain .kkwh b{font:700 15px/18px var(--k-serif) !important;font-variant-numeric:tabular-nums lining-nums}
#kview #kmain .kkwh sup{font:600 11px/1 var(--k-serif) !important;letter-spacing:.1em;text-transform:uppercase;margin-left:4px;vertical-align:1px}
#kview #kmain .kpanel .kcredit{font:600 11px/15px var(--k-serif) !important;letter-spacing:.12em !important;text-transform:uppercase !important;font-style:normal !important;
  margin:8px 0 0 !important;padding:4px 0 0 !important;border-top:1px solid #8a8a8a}
/* section fronts: a little slack so a four-story list never spills a blank sheet */
html .ksecfront #kview #kmain .kfl.kcompact a{padding-top:5px !important;padding-bottom:10px !important}
.kendpage #kview #kmain .kcolophon{margin:14px 0 0 !important;text-align:left}
.kendpage #kview #kmain .kcolophon p{font:430 12px/16px var(--k-serif) !important;margin:0 !important}
.kendpage #kview #kmain .kcolophon .kkick{font:600 12px/16px var(--k-serif) !important;letter-spacing:.14em !important;text-transform:uppercase;margin:0 0 4px !important}
#kview #kmain .kpanel .idea{display:block !important;padding:6px 0 !important;margin:0 !important;border:0 !important;border-bottom:1px solid #8a8a8a !important;background:none !important}
#kview #kmain .kpanel .idea:last-child{border-bottom:0 !important}
#kview #kmain .kpanel .idea>b{display:block;font:700 var(--ks-row)/var(--kl-row) var(--k-serif) !important}
#kview #kmain .kpanel .idea>span{display:block;font:430 16px/22px var(--k-serif) !important}
#kview #kmain .kpanel .kidea-k{display:block !important;margin:0 !important}
#kview #kmain .kpanel .kidea-k:before,#kview #kmain .kpanel .kidea-k:after{display:none !important}
#kview #kmain .kpanel .kmile ul{margin:2px 0 0 !important;padding-left:1.1em !important}
#kview #kmain .kpanel .kmile li{font:430 16px/22px var(--k-serif) !important;margin:0 !important}
#kview #kmain .kpanel .kmile-k{font:italic 430 var(--ks-sm)/var(--kl-sm) var(--k-serif) !important;margin:0 !important}
#kview #kmain .kunit{font:italic 430 var(--ks-sm)/var(--kl-sm) var(--k-serif) !important;margin:4px 0 0 !important}
"""


def run(pages, today_iso, caps=None, shrink=None):
    """Edit every page's HTML in place. Never loses the edition: on any failure the pages stay as they were."""
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("KINDLE_CHROMIUM") or None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=exe)
            p = browser.new_page()
            p.on("console", lambda m: m.text.startswith("kindle ") and print(f"kindle_present: {m.text}", file=sys.stderr))
            res = p.evaluate(PRESENT, {"pages": [{"html": pg["html"], "file": pg.get("file", ""), "sec": pg.get("sec", ""),
                                                  "credit": pg.get("credit", "")} for pg in pages],
                                       "today": today_iso, "caps": caps or {}, "shrink": shrink or {}})
            browser.close()
        for pg, h in zip(pages, res):
            pg["html"] = h
    except Exception as e:  # noqa: BLE001
        print(f"kindle_present: skipped: {e!r}", file=sys.stderr)


if __name__ == "__main__":
    print(json.dumps({"css_bytes": len(CSS)}))
