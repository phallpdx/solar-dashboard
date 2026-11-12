"""Engraved banknote-style panorama band and microtext for the Kindle Evening Edition.

Mt St Helens and Mt Hood behind, St Johns Bridge's gothic towers, West Hills
firs, the Columbia with a ship and a heron, evening sky line work and an
optional moon.  Pure black line work (hatch, stipple, solid black), no greys.
All pattern/clip ids are prefixed with the seed.  Standard library only.
"""
import math
import os
import random


def _f(v):
    s = ('%.1f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def _id(seed, name):
    s = ''.join(c if c.isalnum() else '_' for c in str(seed))
    return 'pn%s_%s' % (s, name)


def _hp(pid, ang, sp, w=0.5):
    return ('<pattern id="%s" width="%s" height="%s" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(%s)"><path d="M0 %sH%s" stroke="#000" '
            'stroke-width="%s"/></pattern>' % (pid, _f(sp), _f(sp), _f(ang),
                                               _f(sp / 2), _f(sp), w))


def _poly(pts, close=True):
    d = 'M' + 'L'.join('%s %s' % (_f(x), _f(y)) for x, y in pts)
    return d + ('Z' if close else '')


def _fir(x, base, h, w):
    top = base - h
    d = ['M%s %sV%s' % (_f(x), _f(top), _f(base))]
    n = max(3, int(h / 1.6))
    for i in range(1, n + 1):
        y = top + h * i / n
        hw = w * i / n
        d.append('M%s %sL%s %sL%s %s' % (_f(x - hw), _f(y + 1), _f(x), _f(y - 0.6),
                                         _f(x + hw), _f(y + 1)))
    return ''.join(d)


def _moon(cx, cy, r, phase, pid):
    """Moon disc; dark part hatched, lit part blank.  phase 0=new .5=full."""
    phase = phase % 1.0
    out = ['<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke="#000" '
           'stroke-width="0.8"/>' % (_f(cx), _f(cy), _f(r))]
    k = math.cos(2 * math.pi * phase)  # terminator x-scale: 1 new, -1 full
    if phase < 0.02 or phase > 0.98:
        dark = 'M%s %sA%s %s 0 1 1 %s %sA%s %s 0 1 1 %s %sZ' % (
            _f(cx), _f(cy - r), _f(r), _f(r), _f(cx), _f(cy + r), _f(r), _f(r),
            _f(cx), _f(cy - r))
    elif abs(phase - 0.5) < 0.02:
        dark = ''
    else:
        waxing = phase < 0.5
        # dark limb side: left when waxing (lit on right, northern hemisphere)
        sweep_limb = 0 if waxing else 1
        rx = abs(k) * r
        # terminator bulges into dark side if gibbous (k<0)
        if waxing:
            sweep_t = 1 if k > 0 else 0
        else:
            sweep_t = 0 if k > 0 else 1
        dark = 'M%s %sA%s %s 0 0 %d %s %sA%s %s 0 0 %d %s %sZ' % (
            _f(cx), _f(cy - r), _f(r), _f(r), sweep_limb, _f(cx), _f(cy + r),
            _f(max(rx, 0.01)), _f(r), sweep_t, _f(cx), _f(cy - r))
    if dark:
        out.append('<path d="%s" fill="url(#%s)" stroke="none"/>' % (dark, pid))
    return ''.join(out)


def panorama(width=600, height=110, seed='p', moon_phase=None):
    """Return an <svg> string: the engraved Columbia River panorama band."""
    W = float(width)
    H = float(max(60, min(140, height)))
    rng = random.Random(str(seed))
    sx = W / 600.0
    hz = H * 0.66          # river line / horizon
    p = lambda n: _id(seed, n)
    defs = [
        _hp(p('mt'), 35, 2.8, 0.5),
        _hp(p('mt2'), -35, 3.0, 0.45),
        _hp(p('hill'), 60, 1.6, 0.6),
        _hp(p('moon'), 90, 1.2, 0.5),
        '<clipPath id="%s"><rect x="3" y="3" width="%s" height="%s"/></clipPath>'
        % (p('clip'), _f(W - 6), _f(H - 6)),
    ]
    b = []
    # --- evening sky: horizontal rules, tight at top, opening toward horizon
    d = []
    y = 4.0
    while y < hz - H * 0.18:
        d.append('M3 %sH%s' % (_f(y), _f(W - 3)))
        t = (y - 4) / max(1, hz - 4)
        y += 1.3 + 3.2 * t
    b.append('<path d="%s" stroke="#000" stroke-width="0.4"/>' % ''.join(d))
    # few cloud streaks (white breaks drawn as heavier short strokes)
    d = []
    for _ in range(int(5 * sx)):
        cx = rng.uniform(20, W - 20)
        cy = rng.uniform(H * 0.12, H * 0.32)
        ln = rng.uniform(25, 60)
        d.append('M%s %sH%s' % (_f(cx - ln / 2), _f(cy), _f(cx + ln / 2)))
        d.append('M%s %sH%s' % (_f(cx - ln / 3), _f(cy + 1.4), _f(cx + ln / 2.5)))
    b.append('<path d="%s" stroke="#000" stroke-width="0.9"/>' % ''.join(d))
    # --- moon
    if moon_phase is not None:
        mr = H * 0.085
        mx, my = W * 0.885, H * 0.2
        b.append('<circle cx="%s" cy="%s" r="%s" fill="#fff"/>'
                 % (_f(mx), _f(my), _f(mr + 2.5)))
        b.append(_moon(mx, my, mr, float(moon_phase), p('moon')))
    # --- mountains (outline + hatched lower flanks, snow left white)
    def mountain(pts, snow_y, pat):
        path = _poly(pts)
        b.append('<path d="%s" fill="#fff" stroke="none"/>' % path)
        cid = p('c%d' % len(b))
        b.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, path))
        b.append('<rect x="0" y="%s" width="%s" height="%s" fill="url(#%s)" '
                 'clip-path="url(#%s)"/>' % (_f(snow_y), _f(W), _f(H), pat, cid))
        b.append('<path d="%s" fill="none" stroke="#000" stroke-width="1"/>'
                 % _poly(pts[1:-1], False))
    hb = hz + 1
    # Mt St Helens: low, broad, flat truncated crater top, left
    c = W * 0.27
    t = H * 0.29
    mountain([(c - 120 * sx, hb), (c - 60 * sx, hb - (hb - t) * 0.55),
              (c - 22 * sx, t + 2), (c - 12 * sx, t), (c - 4 * sx, t + 3),
              (c + 6 * sx, t + 1), (c + 16 * sx, t + 1.5), (c + 30 * sx, t + 6),
              (c + 70 * sx, hb - (hb - t) * 0.45), (c + 125 * sx, hb)],
             t + (hb - t) * 0.42, p('mt2'))
    # crater notch shadow
    b.append('<path d="M%s %sL%s %sL%s %s" stroke="#000" stroke-width="0.6" '
             'fill="none"/>' % (_f(c - 10 * sx), _f(t + 1), _f(c - 2 * sx),
                                _f(t + 5), _f(c + 12 * sx), _f(t + 2)))
    # Mt Hood: tall sharp asymmetric peak, right
    c = W * 0.76
    t = H * 0.05
    hh = hb - t
    pts = [(c - 140 * sx, hb), (c - 80 * sx, hb - hh * 0.30),
           (c - 40 * sx, hb - hh * 0.58), (c - 18 * sx, hb - hh * 0.80),
           (c - 6 * sx, t + 3), (c, t), (c + 5 * sx, t + 4),
           (c + 14 * sx, hb - hh * 0.78), (c + 22 * sx, hb - hh * 0.70),
           (c + 50 * sx, hb - hh * 0.50), (c + 95 * sx, hb - hh * 0.25),
           (c + 150 * sx, hb)]
    mountain(pts, t + hh * 0.62, p('mt'))
    # Hood glacier ridges/couloirs in the snow
    d = []
    for dx, l in ((-10, 0.42), (-3, 0.5), (4, 0.38), (11, 0.33)):
        d.append('M%s %sL%s %s' % (_f(c + dx * 0.3 * sx), _f(t + 6),
                                   _f(c + dx * 2.2 * sx), _f(t + hh * l)))
    b.append('<path d="%s" stroke="#000" stroke-width="0.5" fill="none"/>' % ''.join(d))
    # --- far shore band (stipple + dark line)
    d = []
    for _ in range(int(90 * sx)):
        d.append('M%s %sh0.6' % (_f(rng.uniform(3, W - 3)), _f(rng.uniform(hz - 2.5, hz))))
    b.append('<path d="%s" stroke="#000" stroke-width="0.8"/>' % ''.join(d))
    b.append('<path d="M3 %sH%s" stroke="#000" stroke-width="0.9"/>' % (_f(hz + 0.5), _f(W - 3)))
    # --- river: broken horizontal strokes, tighter toward viewer
    d = []
    y = hz + 2.5
    while y < H - 3:
        x = 3 + rng.random() * 4
        while x < W - 3:
            ln = rng.uniform(10, 40)
            e = min(x + ln, W - 3)
            d.append('M%s %sH%s' % (_f(x), _f(y), _f(e)))
            x = e + rng.uniform(2.5, 8)
        y += 2.8 - 1.2 * (y - hz) / (H - hz)
    b.append('<path d="%s" stroke="#000" stroke-width="0.45"/>' % ''.join(d))
    # --- St Johns Bridge: two gothic towers, suspension cables, deck
    t1, t2 = W * 0.43, W * 0.57
    deck = hz - H * 0.10
    ttop = H * 0.13 + 4
    tw = max(6.0, 8 * sx)
    # clear behind
    b.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff"/>'
             % (_f(t1 - tw), _f(deck - 1), _f(t2 - t1 + 2 * tw), _f(3)))
    # main cables (catenary) and back spans
    def cable(x0, y0, x1, y1, sag):
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2 + sag
        return 'M%s %sQ%s %s %s %s' % (_f(x0), _f(y0), _f(mx), _f(my), _f(x1), _f(y1))
    ct = ttop + 6
    cab = (cable(t1, ct, t2, ct, (deck - ct) * 1.75) +
           cable(t1 - W * 0.10, deck, t1, ct, -6) +
           cable(t2, ct, t2 + W * 0.10, deck, -6))
    b.append('<path d="%s" fill="none" stroke="#000" stroke-width="0.9"/>' % cab)
    # suspenders
    d = []
    n = 14
    for i in range(1, n):
        x = t1 + (t2 - t1) * i / n
        u = i / n
        cy = (1 - u) ** 2 * ct + 2 * u * (1 - u) * (ct + (deck - ct) * 1.75) + u * u * ct
        cy = ct * ((1 - u) ** 2 + u * u) + 2 * u * (1 - u) * (ct + (deck - ct) * 1.75)
        d.append('M%s %sV%s' % (_f(x), _f(cy), _f(deck)))
    b.append('<path d="%s" stroke="#000" stroke-width="0.4"/>' % ''.join(d))
    # deck (double rule) and approaches
    b.append('<path d="M%s %sH%sM%s %sH%s" stroke="#000" stroke-width="1.1"/>'
             % (_f(t1 - W * 0.11), _f(deck), _f(t2 + W * 0.11),
                _f(t1 - W * 0.11), _f(deck + 2), _f(t2 + W * 0.11)))
    # truss hatch between deck rules
    d = []
    x = t1 - W * 0.11
    while x < t2 + W * 0.11:
        d.append('M%s %sl2 2' % (_f(x), _f(deck)))
        x += 2.5
    b.append('<path d="%s" stroke="#000" stroke-width="0.4"/>' % ''.join(d))
    # gothic towers: black silhouettes with pointed-arch openings and spires
    for tx in (t1, t2):
        hw = tw / 2
        sil = _poly([(tx - hw, hz + 1), (tx - hw, ttop + 2), (tx - hw * 0.8, ttop - 5),
                     (tx - hw * 0.6, ttop + 2), (tx - hw * 0.3, ttop + 2),
                     (tx, ttop - 9), (tx + hw * 0.3, ttop + 2), (tx + hw * 0.6, ttop + 2),
                     (tx + hw * 0.8, ttop - 5), (tx + hw, ttop + 2), (tx + hw, hz + 1)])
        # cathedral arch windows (white)
        ah = (deck - ttop) * 0.40
        aw = hw * 0.55
        ay = ttop + 7
        arch = ('M%s %sV%sQ%s %s %s %sQ%s %s %s %sV%sZ' % (
            _f(tx - aw), _f(ay + ah), _f(ay + ah * 0.35), _f(tx - aw), _f(ay + ah * 0.08),
            _f(tx), _f(ay), _f(tx + aw), _f(ay + ah * 0.08), _f(tx + aw),
            _f(ay + ah * 0.35), _f(ay + ah)))
        ay2 = ay + ah + 3
        ah2 = deck - 2 - ay2
        arch2 = ('M%s %sV%sQ%s %s %s %sQ%s %s %s %sV%sZ' % (
            _f(tx - aw), _f(ay2 + ah2), _f(ay2 + ah2 * 0.4), _f(tx - aw), _f(ay2 + ah2 * 0.1),
            _f(tx), _f(ay2), _f(tx + aw), _f(ay2 + ah2 * 0.1), _f(tx + aw),
            _f(ay2 + ah2 * 0.4), _f(ay2 + ah2)))
        b.append('<path d="%s" fill="#000"/>' % sil)
        b.append('<path d="%s%s" fill="#fff"/>' % (arch, arch2 if ah2 > 3 else ''))
        # pier below deck into water: hatched reflection
        b.append('<path d="M%s %sv%sM%s %sv%s" stroke="#000" stroke-width="0.5"/>'
                 % (_f(tx - hw * 0.6), _f(hz + 2), _f(H * 0.12),
                    _f(tx + hw * 0.4), _f(hz + 3), _f(H * 0.09)))
    # --- West Hills: hatched slope at left with firs on its crest
    hill = [(3, hz - H * 0.26)]
    for i in range(1, 21):
        xx = 3 + i * W * 0.24 / 20
        hill.append((xx, hz - H * 0.26 + (H * 0.26) * (i / 20.0) ** 1.6
                     - math.sin(i * 0.9) * 1.2))
    hill += [(W * 0.24 + 3, hz + 1), (3, hz + 1)]
    b.append('<path d="%s" fill="url(#%s)" stroke="none"/>' % (_poly(hill), p('hill')))
    d = []
    for i in range(0, 22):
        u = i / 21.0 * 0.95
        xx = 3 + u * W * 0.24 + rng.uniform(-2, 2)
        k = min(20, int(u * 20))
        yb = hill[k][1] + 2
        h = rng.uniform(H * 0.09, H * 0.17) * (1.15 - u * 0.6)
        b.append('<path d="M%s %sL%s %sL%s %sZ" fill="#fff"/>'
                 % (_f(xx - h * 0.2), _f(yb), _f(xx), _f(yb - h), _f(xx + h * 0.2), _f(yb)))
        d.append(_fir(xx, yb, h, h * 0.2))
    b.append('<path d="%s" fill="none" stroke="#000" stroke-width="0.6"/>' % ''.join(d))
    b.append('<path d="%s" fill="none" stroke="#000" stroke-width="1"/>'
             % _poly(hill[:-2], False))
    # --- ship (freighter heading downstream), right of bridge
    sxp = W * 0.86
    sy = hz + (H - hz) * 0.45
    L = 44 * sx
    hull = _poly([(sxp - L / 2, sy - 5), (sxp + L / 2 + 4, sy - 5), (sxp + L / 2, sy),
                  (sxp - L / 2 + 2, sy)])
    b.append('<path d="M%s %sH%s" stroke="#fff" stroke-width="5"/>'
             % (_f(sxp - L / 2 - 2), _f(sy - 2.5), _f(sxp + L / 2 + 6)))
    b.append('<path d="%s" fill="#000"/>' % hull)
    # containers stacked, hatched vertical
    d = []
    x = sxp - L / 2 + 8
    while x < sxp + L / 2 - 2:
        d.append('M%s %sV%s' % (_f(x), _f(sy - 9), _f(sy - 5)))
        x += 1.4
    b.append('<path d="%s" stroke="#000" stroke-width="0.6"/>' % ''.join(d))
    b.append('<path d="M%s %sh%sv-4h%s" fill="none" stroke="#000" stroke-width="0.8"/>'
             % (_f(sxp - L / 2 + 8), _f(sy - 9), _f(L - 10), _f(0)))
    # bridge house aft
    b.append('<path d="M%s %sv-9h5v9M%s %sv-3" fill="#000" stroke="#000" stroke-width="0.8"/>'
             % (_f(sxp - L / 2 + 1.5), _f(sy - 5), _f(sxp - L / 2 + 4), _f(sy - 14)))
    # wake
    b.append('<path d="M%s %sH%sM%s %sH%s" stroke="#000" stroke-width="0.5"/>'
             % (_f(sxp - L / 2 - 14), _f(sy + 1.5), _f(sxp + L / 2), _f(sxp - L / 2 - 8),
                _f(sy + 3), _f(sxp + L / 2 - 6)))
    # --- heron on the near shore, lower left
    hx = W * 0.11
    hy = H - 6
    s = H / 110.0 * 1.15
    def P(dx, dy):
        return '%s %s' % (_f(hx + dx * s), _f(hy + dy * s))
    b.append('<path d="M%s Q%s %s L%s L%s Z" fill="#fff" stroke="none"/>' % (
        P(-8, -14), P(-2, -22), P(6, -16), P(2, -10), P(-6, -10)))
    heron = ('M%s Q%s %s Q%s %s L%s' % (P(-9, -13), P(-2, -21), P(5, -15),
                                        P(1, -10), P(-7, -11), P(-9, -13)) +
             'M%s Q%s %s Q%s %s' % (P(1, -17), P(-1, -23), P(1, -27), P(3, -30), P(2, -31)) +
             'M%s L%s' % (P(2, -31), P(8, -30.3)) +
             'M%s L%s M%s L%s' % (P(-1, -11), P(-1, 0), P(1, -11), P(2, 0)) +
             'M%s L%s' % (P(-4, 0), P(6, 0)))
    b.append('<path d="%s" fill="none" stroke="#000" stroke-width="1.1" '
             'stroke-linejoin="round" stroke-linecap="round"/>' % heron)
    # wing hatching
    d = []
    for i in range(4):
        d.append('M%s L%s' % (P(-6 + i * 2.5, -11), P(-3 + i * 2.5, -16 + i * 0.6)))
    b.append('<path d="%s" stroke="#000" stroke-width="0.5"/>' % ''.join(d))
    # --- frame: banknote double rule
    frame = ('<rect x="1" y="1" width="%s" height="%s" fill="none" stroke="#000" '
             'stroke-width="1.4"/><rect x="3" y="3" width="%s" height="%s" fill="none" '
             'stroke="#000" stroke-width="0.5"/>' % (_f(W - 2), _f(H - 2), _f(W - 6), _f(H - 6)))
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 %s %s" width="%s" height="%s"><defs>%s</defs>'
            '<rect width="%s" height="%s" fill="#fff"/><g clip-path="url(#%s)">%s</g>%s</svg>'
            % (_f(W), _f(H), _f(W), _f(H), ''.join(defs), _f(W), _f(H), p('clip'),
               ''.join(b), frame))


def _esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def _fill(text, length, size):
    """Repeat text to cover length (approx 0.55em per glyph for serif caps)."""
    text = str(text)
    if not text.endswith(' '):
        text += ' '
    per = max(1.0, len(text) * size * 0.58)
    n = max(1, int(math.ceil(length / per)) + 1)
    return text * n


def microtext_line(x1, y1, x2, y2, text, size=2.2, seed=''):
    """Banknote microtext along a straight line; returns an SVG <g> fragment."""
    L = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    cid = _id(seed, 'mtl%d' % (int(abs(x1 * 7 + y1 * 13 + x2 * 17 + y2 * 19)) % 99991))
    return ('<g transform="translate(%s %s) rotate(%s)"><clipPath id="%s"><rect x="0" y="%s" '
            'width="%s" height="%s"/></clipPath><text clip-path="url(#%s)" x="0" y="0" '
            'font-family="serif" font-size="%s" letter-spacing="0.15" fill="#000" '
            'dominant-baseline="middle">%s</text></g>'
            % (_f(x1), _f(y1), _f(ang), cid, _f(-size), _f(L), _f(size * 2), cid,
               _f(size), _esc(_fill(text, L, size))))


def microtext_ring(cx, cy, r, text, size=2.2, seed=''):
    """Banknote microtext around a circle via textPath; returns an SVG <g> fragment."""
    pid = _id(seed, 'mtr%d' % (int(abs(cx * 7 + cy * 13 + r * 17)) % 99991))
    circ = 2 * math.pi * r
    t = str(text)
    if not t.endswith(' '):
        t += ' '
    per = max(1.0, len(t) * size * 0.58)
    n = max(1, int(circ // per))
    body = t * n
    # stretch the whole run to exactly the circumference so it closes cleanly
    d = 'M%s %sa%s %s 0 1 1 %s 0a%s %s 0 1 1 %s 0' % (
        _f(cx - r), _f(cy), _f(r), _f(r), _f(2 * r), _f(r), _f(r), _f(-2 * r))
    return ('<g><path id="%s" d="%s" fill="none"/><text font-family="serif" font-size="%s" '
            'fill="#000"><textPath href="#%s" xlink:href="#%s" textLength="%s" '
            'lengthAdjust="spacing">%s</textPath></text></g>'
            % (pid, d, _f(size), pid, pid, _f(circ * 0.995), _esc(body)))


def demo(path='/tmp/claude-0/shots/team/panorama_demo.html'):
    a = panorama(600, 110, 'a', moon_phase=0.30)
    b = panorama(600, 70, 'b', moon_phase=0.72)
    msg = '45.70°N 122.80°W · 18.4 kWh TODAY · GOODNIGHT PARKER ·'
    micro = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             'width="600" height="150" viewBox="0 0 600 150"><rect width="600" height="150" fill="#fff"/>'
             + microtext_line(10, 10, 590, 10, msg, 2.2, 'd')
             + microtext_line(10, 18, 590, 18, msg, 3.0, 'd')
             + microtext_line(10, 140, 260, 40, msg, 2.6, 'd')
             + microtext_ring(400, 85, 50, msg, 2.4, 'd')
             + microtext_ring(400, 85, 40, msg, 3.0, 'd')
             + '<circle cx="400" cy="85" r="35" fill="none" stroke="#000" stroke-width="0.8"/>'
             + '</svg>')
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>Panorama</title>'
            '<style>body{margin:9px;background:#fff;font:12px serif}div{margin:0 0 8px}</style>'
            '</head><body><div>%s</div><div>%s</div><div>%s</div><div>sizes: %d B / %d B</div>'
            '</body></html>' % (a, b, micro, len(a), len(b)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write(html)
    return path


if __name__ == '__main__':
    print(demo())
