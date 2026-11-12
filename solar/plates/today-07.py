"""today-07 "Window shades / Curtain call": a theatre-curtained window in the house acanthus.

The vignette is the page's own advice made into a stage: a two-light window under a swagged,
tasselled valance, its velvet curtains drawn back to tie-backs.  The left light has its shade
rolled up and the morning sun (open the sunny side at 10) rising over the hills and Mt. Hood;
the right light has its Roman shade let down for the evening (close at 4:44) with the moon and
a star above it.  Easter egg: the right shade's pull cord ends in a drumstick.
"""
import sys
import math
import random
import engraving_codex as C
import engraving_morning as M
import re

_n = C._n
PI = math.pi
TAU = 2 * PI


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _lerp(a, b, t):
    return a + (b - a) * t


def _sm(t):
    t = min(max(t, 0.), 1.)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------------------------
# pieces of the scene, all drawn into one Canvas
# ---------------------------------------------------------------------------------------------

def _crescent(cx, cy, r, phi=-.5, d=.45, ri=.82, n=40):
    """A crescent moon: the disc less an offset disc toward angle phi."""
    ix, iy = cx + r * d * math.cos(phi), cy + r * d * math.sin(phi)
    rr = r * ri
    outer = [(cx + r * math.cos(phi + TAU * i / n), cy + r * math.sin(phi + TAU * i / n)) for i in range(n + 1)]
    outer = [q for q in outer if math.hypot(q[0] - ix, q[1] - iy) > rr]
    inner = [(ix + rr * math.cos(phi + TAU * i / n), iy + rr * math.sin(phi + TAU * i / n)) for i in range(n + 1)]
    inner = [q for q in inner if math.hypot(q[0] - cx, q[1] - cy) < r]
    return outer + inner[::-1]


def _disc_shade(cx, cy, r, pitch=1.5):
    """Horizontal shading across a disc, leaving a highlight upper left."""
    hx, hy, hr = cx - r * .3, cy - r * .3, r * .62
    out = []
    yy = cy - r + .25
    while yy < cy + r:
        half = math.sqrt(max(0., r * r - (yy - cy) ** 2)) - .8
        if half > .6:
            a, b = cx - half, cx + half
            dy = yy - hy
            if abs(dy) < hr:
                hh = math.sqrt(hr * hr - dy * dy)
                if hx - hh > a + .6:
                    out.append([(a, yy), (hx - hh, yy)])
                if b > hx + hh + .6:
                    out.append([(max(a, hx + hh), yy), (b, yy)])
            else:
                out.append([(a, yy), (b, yy)])
        yy += pitch
    return out


def _sky(cv, poly, pitch, phase=.25):
    cv.obj([poly], 0)
    cv.hair(C.hatch_poly(poly, 0, pitch, phase))


def _sun(cv, cx, cy, r):
    """A rising sun: white rays cut out of the sky hatch, a modelled disc."""
    n = 14
    for i in range(0, n, 2):
        a0 = PI + PI * (i + .2) / n - .02
        a1 = PI + PI * (i + .8) / n + .02
        R = r * 3.2
        wedge = [(cx + r * 1.15 * math.cos(a0), cy + r * 1.15 * math.sin(a0)),
                 (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                 (cx + R * math.cos(a1), cy + R * math.sin(a1)),
                 (cx + r * 1.15 * math.cos(a1), cy + r * 1.15 * math.sin(a1))]
        cv.obj([wedge], 0)
        if r > 6:
            am = (a0 + a1) / 2
            cv.hair([(cx + r * 1.4 * math.cos(am), cy + r * 1.4 * math.sin(am)),
                     (cx + R * .8 * math.cos(am), cy + R * .8 * math.sin(am))])
    disc = C._ell_pts(cx, cy, r, r, 40)[:-1]
    cv.obj([disc], 1.)
    if r > 5:
        cv.hair(_disc_shade(cx, cy, r, 2. if r < 9 else 1.5))
    elif r > 3:
        cv.hair([C._ell_pts(cx, cy, r * .6, r * .6, 24, -.2, 1.9)])


def _hills(cv, x0, x1, ybase, h, seed, hood=True):
    """Rolling hills across a light, Mt. Hood standing behind them."""
    rng = random.Random(seed)
    w = x1 - x0
    yb = ybase
    if hood and h > 6:
        px = x0 + w * .66
        top_y = ybase - h * 1.05
        mt = [(x0 + w * .18, yb), (px - w * .3, ybase - h * .4), (px - w * .14, ybase - h * .72),
              (px - w * .04, top_y + h * .08), (px, top_y), (px + w * .05, top_y + h * .1),
              (px + w * .16, ybase - h * .66), (px + w * .34, ybase - h * .36), (x1 + 2, ybase - h * .2), (x1 + 2, yb)]
        cv.obj([mt], .5)
        snow_y = ybase - h * .62
        cv.hair([q for q in C.hatch_poly(mt, -45, 1.5) if min(p[1] for p in q) > snow_y - .5])
        cv.hair([q for q in C.hatch_poly(mt, 0, 3, .25) if q[0][1] <= snow_y and q[0][0] > px - .2])
        for f in (-.12, -.05, .04, .11):
            cv.hair([(px + w * f * .3, top_y + h * .12), (px + w * f, snow_y + h * .06)])
    pts = [(x0, yb)]
    m = 24
    ph = rng.random() * 6
    for i in range(m + 1):
        t = i / m
        pts.append((x0 + w * t, ybase - h * (.32 + .16 * math.sin(t * 5.2 + ph) + .08 * math.sin(t * 13 + ph))))
    pts.append((x1, yb))
    cv.obj([pts], .5)
    cv.hair(C.hatch_poly(pts, 0, 1.5, .25))


def _rolled_shade(cv, x0, x1, y0, hgt):
    """A roller blind wound up at the head of the light."""
    y1 = y0 + hgt
    cv.obj([_rect(x0, y0, x1, y1)], 1.)
    yy = y0 + hgt * .5
    while yy < y1 - .8:
        cv.hair([(x0 + .5, yy), (x1 - .5, yy)])
        yy += 1.5
    if hgt > 4:
        cv.line([(x0 + .5, y1 - 1), (x1 - .5, y1 - 1)])


def _roman_shade(cv, x0, x1, y0, y1, folds):
    """A Roman shade let down: stacked pleats, each bellying out and shaded under its fold."""
    fh = (y1 - y0) / folds
    m = 20
    for j in range(folds):
        ya = y0 + j * fh
        yb = ya + fh
        bulge = min(fh * .3, 2.5)
        low = [(x0 + (x1 - x0) * i / m, yb + bulge * math.sin(PI * i / m)) for i in range(m + 1)]
        poly = [(x0, ya), (x1, ya)] + low[::-1]
        cv.obj([poly], .5)
        for f in (.45, .62, .76, .88):
            if fh * (1 - f) < .9:
                continue
            cv.hair([(x0 + (x1 - x0) * i / m, ya + (yb - ya) * f + bulge * f * f * math.sin(PI * i / m))
                     for i in range(m + 1)])
        cv.line([(p[0], p[1] - .6) for p in low])
    cv.hair([[(x0 + 1.2, y0), (x0 + 1.2, y1)], [(x1 - 1.2, y0), (x1 - 1.2, y1)]])


def _drumstick(cv, x, y, L):
    """The shade pull: a cord ending in a drumstick, bead down."""
    cord = L * .38
    cv.obj([], 0)
    cv.hair([(x, y), (x, y + cord)])
    s0 = y + cord
    s1 = y + L - L * .1
    wt, wb = max(1.1, L * .05), max(.55, L * .02)
    shaft = [(x - wt, s0), (x + wt, s0), (x + wb, s1), (x - wb, s1)]
    cv.obj([shaft], .5)
    br = max(1.2, L * .08)
    bead = C._ell_pts(x, s1 + br * .8, br * .62, br, 16)[:-1]
    cv.obj([bead], .5)
    if wt > 1.4:
        cv.hair([(x + wt * .4, s0 + .8), (x + wb * .4, s1 - .5)])


def _curtain(cv, side, xo, y0, y1, wtop, wtie, wbot, tie_t, seed):
    """A velvet curtain hanging from y0 to y1 against the outer edge xo (side -1: left curtain,
    its inner edge to the right), drawn back to a tie-back at tie_t. Folds in bulino."""
    rng = random.Random(seed)
    H = y1 - y0
    inw = -side

    def width(t):
        if t < tie_t:
            return _lerp(wtop, wtie, _sm(t / tie_t) ** .8)
        return _lerp(wtie, wbot, _sm((t - tie_t) / (1 - tie_t)))

    m = max(24, int(H / 1.5))
    k = max(3, int(round(wtop / 5.5)))
    ph = rng.random()
    amp = 1.6 if H > 20 else .8

    def at(s, t):
        y = y0 + H * t
        if t >= .999:
            y += amp * math.sin(2 * PI * (s * k + ph))
        return (xo + inw * width(t) * s, y)

    inner = [at(1, i / m) for i in range(m + 1)]
    bottom = [at(1 - i / 16, 1) for i in range(17)]
    poly = [(xo, y0)] + inner + bottom + [(xo, y1)]
    cv.obj([poly], 1.)
    N = max(4, int(wtop / 1.6))
    for i in range(1, N):
        s = i / N
        lvl = 1 if i % 4 == 0 else (2 if i % 2 == 0 else 4)
        fold_phase = (s * k + ph) % 1.
        dark = abs(fold_phase - .75) < .17
        seg, segs = [], []
        for j in range(m + 1):
            t = j / m
            gap = width(t) / N * lvl
            if gap >= 1.6 or (dark and gap >= 1.):
                seg.append(at(s, t))
            else:
                if len(seg) > 1:
                    segs.append(seg)
                seg = []
        if len(seg) > 1:
            segs.append(seg)
        (cv.line if dark and lvl <= 2 else cv.hair)(segs)
    cv.line([(p[0] + side * .8, p[1]) for p in inner[1:-1]])


def _tieback(cv, side, xo, y, wtie, h):
    """A rope tie-back with a tassel, gathering the curtain."""
    inw = -side
    x1 = xo + inw * (wtie + 1.5)
    band = [(xo, y - h * .5), (x1, y - h * .4), (x1, y + h * .4), (xo, y + h * .5)]
    cv.obj([band], 1.)
    xx = min(xo, x1)
    while xx < max(xo, x1) - .5:
        cv.hair([(xx, y - h * .45), (xx + h * .7, y + h * .45)])
        xx += 2.
    tx = x1 - inw * .5
    th = h * 2.4
    tw = h * .7
    cap = C._ell_pts(tx, y + h * .4 + tw * .5, tw * .55, tw * .55, 12)[:-1]
    skirt = [(tx - tw * .4, y + h * .4 + tw * .8), (tx + tw * .4, y + h * .4 + tw * .8),
             (tx + tw * .8, y + h * .4 + th), (tx - tw * .8, y + h * .4 + th)]
    cv.obj([skirt], .5)
    xx = tx - tw * .55
    while xx < tx + tw * .6:
        cv.hair([(xx * .6 + tx * .4, y + h * .4 + tw * .9), (xx, y + h * .4 + th - .4)])
        xx += 1.5
    cv.obj([cap], .5)


def _valance(cv, x0, x1, y0, vh, seed):
    """A swagged pelmet: festoons of draped cloth hung between tasselled jabots."""
    w = x1 - x0
    n = max(2, int(round(w / (vh * 3.2))))
    sw = w / n
    m = 16
    top = vh * .28
    for i in range(n):
        a = x0 + sw * i
        low = [(a + sw * j / m, y0 + top + (vh - top) * math.sin(PI * j / m)) for j in range(m + 1)]
        poly = [(a, y0), (a + sw, y0)] + low[::-1]
        cv.obj([poly], 1.)
        for f in (.25, .42, .56, .68, .78, .87, .94):
            if (vh - top) * .1 < .9 and f < .8:
                continue
            yy = [(a + sw * j / m, y0 + top * f + (vh - top) * f * math.sin(PI * j / m) ** (1.2 - .4 * f))
                  for j in range(m + 1)]
            (cv.line if f > .9 else cv.hair)(yy)
    cv.obj([_rect(x0 - 1, y0 - .5, x1 + 1, y0 + max(2., top * .8))], 1.)
    if top > 3:
        cv.hair([(x0, y0 + top * .45), (x1, y0 + top * .45)])
    for i in range(1, n):
        jx = x0 + sw * i
        th = vh * .9
        tw = max(1.6, vh * .16)
        cap = C._ell_pts(jx, y0 + top + tw, tw, tw, 12)[:-1]
        skirt = [(jx - tw * .6, y0 + top + tw * 1.6), (jx + tw * .6, y0 + top + tw * 1.6),
                 (jx + tw * 1.2, y0 + top + th), (jx - tw * 1.2, y0 + top + th)]
        cv.obj([skirt], .5)
        xx = jx - tw
        while xx < jx + tw:
            cv.hair([(jx + (xx - jx) * .5, y0 + top + tw * 1.8), (xx, y0 + top + th - .3)])
            xx += 1.5
        cv.obj([cap], .5)


def scene(x, y, w, h, seed=0, clip_d=None):
    """The whole curtained window filling x..x+w, y..y+h (and, if clip_d is given, the field
    that outline describes): no white left but highlights."""
    rng = random.Random(seed)
    cv = C.Canvas()
    big = h > 70
    bleed = 6 if clip_d else 0
    vh = max(6., min(h * .2, 34.))
    cw = w * (.23 if big else .19)
    sill_h = max(2.5, h * .05)
    wy0 = y + vh * .55
    wy1 = y + h - (h * .14 if big else sill_h + 1.5)
    ww = w - 2 * cw + cw * .5
    wx0 = x + (w - ww) / 2
    wx1 = wx0 + ww
    fr = max(2., min(ww, h) * .035)
    gx0, gx1, gy0, gy1 = wx0 + fr, wx1 - fr, wy0 + fr, wy1 - fr
    mx = (gx0 + gx1) / 2
    lw = (gx1 - gx0 - fr) / 2
    L0, L1 = (gx0, mx - fr / 2), (mx + fr / 2, gx1)
    lh = gy1 - gy0
    _sky(cv, _rect(L0[0], gy0, L0[1], gy1), 2)
    _sky(cv, _rect(L1[0], gy0, L1[1], gy1), 1.5)
    # the right light: moon and stars above the let-down shade
    hem = gy0 + lh * .55
    mr = max(1.8, min(lw, lh) * .1)
    mcx, mcy = L1[0] + lw * .78, hem + (gy1 - hem) * .5 + 1.5
    cv.obj([C._ell_pts(mcx, mcy, mr + .8, mr + .8, 24)[:-1]], 0)
    cres = _crescent(mcx, mcy, mr, -.6)
    cv.obj([cres], .5)
    if mr > 5:
        cv.hair(C.hatch_poly(cres, 0, 2, .25, .8))
    for sx, sy, ss in ((L1[0] + lw * .2, hem + (gy1 - hem) * .55 + 1, 1.6), (L1[0] + lw * .33, hem + (gy1 - hem) * .8, 1.1)):
        ss = max(ss, min(lw, lh) * .045)
        cv.obj([[(sx, sy - ss * 1.6), (sx + ss * .4, sy), (sx, sy + ss * 1.6), (sx - ss * .4, sy)]], 0)
        cv.obj([[(sx - ss * 1.6, sy), (sx, sy - ss * .4), (sx + ss * 1.6, sy), (sx, sy + ss * .4)]], 0)
    # the left light: the sun over the hills and Mt. Hood
    sr = max(2.5, min(lw * .2, lh * .17))
    _sun(cv, L0[0] + lw * .38, gy0 + lh * .58, sr)
    _hills(cv, L0[0], L0[1], gy1, lh * .3, rng.randrange(1 << 20), hood=lh > 18)
    _rolled_shade(cv, L0[0], L0[1], gy0, max(2.5, lh * .1))
    _roman_shade(cv, L1[0], L1[1], gy0, hem, max(2, int(round((hem - gy0) / 6.5))))
    bars = [_rect(wx0, wy0, wx1, gy0), _rect(wx0, gy1, wx1, wy1), _rect(wx0, gy0, gx0, gy1),
            _rect(gx1, gy0, wx1, gy1), _rect(mx - fr / 2, gy0, mx + fr / 2, gy1)]
    for b in bars:
        cv.obj([b], .5)
        if fr >= 3:
            cv.hair(C.hatch_poly(b, 45, 3, .5, .6))
    _drumstick(cv, (L1[0] + L1[1]) / 2, hem + 1.5, min(lh * .32, (gy1 - hem) * .85))
    sx0, sx1 = wx0 - fr * 1.6, wx1 + fr * 1.6
    cv.obj([_rect(sx0, wy1, sx1, wy1 + sill_h)], 1.)
    cv.heavy([(sx0 + 1, wy1 + sill_h - .75), (sx1 - 1, wy1 + sill_h - .75)])
    if sill_h > 3:
        cv.hair([(sx0 + 1, wy1 + 1.25), (sx1 - 1, wy1 + 1.25)])
    yb = y + h + bleed
    tie_t = .52 if big else .5
    for side in (-1, 1):
        xo = (x - bleed) if side < 0 else (x + w + bleed)
        wt = cw + bleed
        _curtain(cv, side, xo, y + vh * .5, yb, wt, wt * .5, wt * .82, tie_t, rng.randrange(1 << 20))
        _tieback(cv, side, xo, y + vh * .5 + (yb - y - vh * .5) * tie_t, wt * .5, max(2.5, h * .045))
    _valance(cv, x - bleed, x + w + bleed, y - bleed + .5, vh + bleed, rng.randrange(1 << 20))
    wall = C.dark_ground((x - 8, y - 8, w + 16, h + 16) if clip_d else (x, y, w, h), "D")
    body = wall + cv.svg()
    if clip_d:
        cid = C._uid("tw", x, y, w, h, seed)
        return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
    return C._clip(C._uid("tr", x, y, w, h, seed), x, y, w, h, body)


# ---------------------------------------------------------------------------------------------
# layouts
# ---------------------------------------------------------------------------------------------

def _frieze(x, y, w, h, seed, gap):
    """Interlocking volutes flowing out from the window to both ends, the gaps grown full."""
    rng = random.Random(seed)
    main = C.Canvas()
    occ = [("r", x + w / 2 - gap / 2 - 2, y, x + w / 2 + gap / 2 + 2, y + h)]
    half = (w - gap) / 2
    cy = y + h / 2
    rs = 1.3 * max(1., 62. / h)
    r = h * .4 * rs
    n = max(1, int(round(half / (r * 2.35))))
    P = half / n
    r = min(r, P * .46)
    for side, x0, mir in ((1, x + w / 2 + gap / 2, False), (-1, x + w / 2 - gap / 2, True)):
        C.running_scroll(x0, cy, 0 if side > 0 else 180, half, h, seed, mir, n=n, r_scale=rs, cv=main)
        for i in range(n):
            down = i % 2 == 0
            off = (.12 if down else -.12) * h
            nyy = (-1 if mir else 1) * (1 if side > 0 else -1)
            occ.append(("c", x0 + side * P * (i + .62), cy + nyy * off, r * .95))
    fill = C.Canvas()
    C.fill_scrolls(x, y, w, h, occ, rng.randrange(1 << 20), rmin=max(5., h * .1), rmax=r * .6,
                   max_n=14, edge=.7, grid=3., fronds=2, cv=fill)
    fill.extend(main)
    return fill.svg()


def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    vw = min(gh * 3.1, 190.)
    fb = 3.
    gap = vw + 2 * fb
    o.append(C._clip(C._uid("b7", w, h, seed), 0, top, w, gh, _frieze(0, top, w, gh, seed, gap)))
    cx = w / 2
    fx0, fx1 = cx - gap / 2, cx + gap / 2
    fy0, fy1 = top + .5, h - 2
    o.append(f'<path d="M{_n(fx0)},{_n(fy0)}H{_n(fx1)}V{_n(fy1)}H{_n(fx0)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(fx0 + 1.5)},{_n(fy0 + 1.25)}H{_n(fx1 - 1.5)}V{_n(fy1 - 1.25)}H{_n(fx0 + 1.5)}z" fill="#000" stroke="none"/>')
    o.append(scene(fx0 + fb, fy0 + 2, vw, fy1 - fy0 - 4, seed))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return C.svg_doc(w, h, "".join(o))


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        return _band(w, h, seed)
    rng = random.Random(seed)
    rng.randrange(1 << 20)
    cs = rng.randrange(1 << 20)
    if h <= 260:
        em = min(12., 6 + h * .025)
        gy0, gy1 = em + 1, h - 7.
        cw = min(w * .4, (gy1 - gy0) * 1.45)
        ccx, ccy, cww, chh = w / 2, (gy0 + gy1) / 2, cw, gy1 - gy0 + 4
        _, _, field = C.cartouche(ccx, ccy, cww, chh, cs)
    else:
        ped_h = min(max(h * .17, 48), 86.)
        frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
        top_free = min(h * .055, 26.)
        ph = h - top_free - ped_h - frieze + ped_h * .3
        cw, ch = (w - 12) * .44, ph * .58
        ccx, ccy, cww, chh = w / 2, top_free + ph * .45, cw, ch
        _, _, field = C.cartouche(ccx, ccy, cww, chh, cs)

    bw = max(5., min(cww, chh) * .07)
    fa, fb = cww / 2 - bw * 1.6, chh / 2 - bw * 1.6
    bx0, by0, bx1, by1 = ccx - fa, ccy - fb, ccx + fa, ccy + fb

    def fill(ix, iy, iw, ih):
        return scene(bx0, by0, bx1 - bx0, by1 - by0, seed, field)

    svg = C.frame_plate(w, h, seed, fill)
    if h <= 260:
        return svg
    # tall: letter the banner with today's times, engrave the pedestal tablet, rule the open paper
    rng.randrange(1 << 20)
    bs = rng.randrange(1 << 20)
    ps = rng.randrange(1 << 20)
    cx, cy = w / 2, top_free + ph * .45
    bh = min(16, ph * .05)
    _, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, bs)
    extra = _letter_on(centre, _times(ctx), bh * .5)
    py = top_free + ph - ped_h * .3 + 4 if frieze else h - ped_h
    _, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, ps)
    extra += _tablet(tx, ty, tw, th)
    under = C.dark_ground((0, 0, w, h), "L")
    k = svg.index("</defs>") + 7
    svg = svg[:k] + under + svg[k:]
    return svg.replace("</svg>", extra + "</svg>")


def _times(ctx):
    t = (ctx or {}).get("sample", "")
    o = re.search(r"Open[^.]*?at (\d{1,2}(?::\d\d)?) ?(am|pm)", t, re.I)
    c = re.search(r"Close[^.]*?at (\d{1,2}(?::\d\d)?) ?(am|pm)", t, re.I)
    a = (o.group(1) + " " + o.group(2).upper()) if o else "10 AM"
    b = (c.group(1) + " " + c.group(2).upper()) if c else "4:44 PM"
    return a + " \u00b7 " + b


def _letter_on(centre, text, cap):
    """Stroke lettering centred along a banner's face line."""
    polys, width = M._text_polys(text, 0, 0, cap, 1.6, False)
    x0 = centre[0][0]
    span = centre[-1][0] - x0
    mid = x0 + span / 2
    n = len(centre) - 1

    def ymid(x):
        f = min(max((x - x0) / span, 0.), 1.) * n
        i = min(int(f), n - 1)
        return centre[i][1] + (centre[i + 1][1] - centre[i][1]) * (f - i)

    out = []
    for pl in polys:
        out.append([(mid - width / 2 + px, ymid(mid - width / 2 + px) - cap / 2 + py) for px, py in pl])
    d = "".join(C._d(pl, tol=.05) for pl in out)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>'


def _tablet(x, y, w, h):
    """The pedestal's sunk tablet: a ruled field with the shades' day drawn as a frieze of
    alternating suns and crescent moons."""
    o = [C.dark_ground((x, y, w, h), "M")]
    cv = C.Canvas()
    r = max(1.5, h / 2 - 1.5)
    n = max(3, int(w / (r * 5)))
    for i in range(n):
        cx = x + w * (i + .5) / n
        cy = y + h / 2
        if i % 2 == 0:
            cv.obj([C._ell_pts(cx, cy, r, r, 20)[:-1]], .5)
            cv.hair(_disc_shade(cx, cy, r, 2.))
            for k in range(8):
                a = k * PI / 4
                cv.obj([[(cx + r * 1.35 * math.cos(a - .18), cy + r * 1.35 * math.sin(a - .18)),
                         (cx + r * 1.9 * math.cos(a), cy + r * 1.9 * math.sin(a)),
                         (cx + r * 1.35 * math.cos(a + .18), cy + r * 1.35 * math.sin(a + .18))]], .5)
        else:
            cv.obj([_crescent(cx, cy, r * 1.25, -.6)], .5)
    return "".join(o) + cv.svg()
