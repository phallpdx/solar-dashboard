"""News front plate (edition plan: an arched vignette for the section front, with the Somaster
dedication cartouche at its foot).

The subject is the Oregonian's old clock tower: the Romanesque tower of the 1892 Oregonian
Building, its masonry coursed in fine cuts, the shaded face cross-hatched, arched belfry
openings, the clock showing the edition's hour, and the steep shingled spire, rising over the
Willamette at morning with the St Johns Bridge behind, the West Hills and Mt. Hood.
Easter egg: a Blazers pinwheel in a roundel in the scroll.
"""
import sys
import math
import random
import engraving_codex as C
import engraving_morning as M

TAU = math.tau
_n = C._n
_d = C._d
_ell = C._ell_pts

# ------------------------------------------------------------------------------------------------
# lettering (path strokes; own copy of the house glyphs plus the letters we need)
# ------------------------------------------------------------------------------------------------
_G = dict(M._G)
_G["S"] = (5, [("s", [(4.4, 1.2), (3, 0), (1.4, .2), (.6, 1.4), (1, 3), (2.5, 3.9), (4, 4.8), (4.5, 6.5),
                     (3.6, 7.8), (2, 8), (.4, 6.9)])])
_G["U"] = (5.6, [("s", [(.9, 0), (.9, 5.4), (1.6, 7.5), (2.8, 8), (4, 7.5), (4.7, 5.4), (4.7, 0)]),
                 ("l", [(0, 0), (1.8, 0)]), ("l", [(3.8, 0), (5.6, 0)])])


def _glyphs(ch):
    adv, strokes = _G.get(ch, _G[" "])
    return adv, [M._spline(p, False, 4) if k == "s" else list(p) for k, p in strokes]


def _text(s, cx, y, h, track=1.4, yfun=None):
    k = h / 8
    width = (sum(_G.get(c, _G[" "])[0] + track for c in s) - track) * k
    x = cx - width / 2
    out = []
    for c in s:
        adv, polys = _glyphs(c)
        for p in polys:
            q = []
            for px, py in p:
                X = x + px * k
                q.append((X, y + py * k + (yfun(X) if yfun else 0)))
            out.append(q)
        x += (adv + track) * k
    return out, width


def _pl_d(polys):
    return "".join(_d(p, tol=.05) for p in polys if len(p) > 1)


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _runs(lines, pred, step=.6):
    """Keep the parts of 2-point lines where pred(x, y) holds."""
    out = []
    for (x0, y0), (x1, y1) in lines:
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        run = []
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if pred(x, y):
                run.append((x, y))
            else:
                if len(run) > 1:
                    out.append([run[0], run[-1]])
                run = []
        if len(run) > 1:
            out.append([run[0], run[-1]])
    return out


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _ring(cx, cy, r0, r1, n=72):
    return _ell(cx, cy, r1, r1, n) + _ell(cx, cy, r0, r0, n)[::-1]


# ------------------------------------------------------------------------------------------------
# the globe
# ------------------------------------------------------------------------------------------------
_NA = [(-165, 64), (-160, 70), (-140, 70), (-128, 70), (-115, 68), (-95, 72), (-85, 68), (-80, 63), (-95, 58),
       (-92, 57), (-80, 52), (-78, 58), (-70, 60), (-62, 58), (-56, 52), (-60, 47), (-66, 44), (-70, 42),
       (-74, 40), (-76, 35), (-81, 31), (-80, 26), (-82, 27), (-84, 30), (-90, 29), (-97, 27), (-97, 22),
       (-92, 18), (-88, 21), (-87, 16), (-83, 10), (-79, 9), (-81, 7), (-86, 12), (-92, 15), (-100, 17),
       (-106, 23), (-112, 29), (-110, 23), (-115, 30), (-118, 34), (-121, 36), (-124, 40), (-124, 46),
       (-123, 48), (-128, 51), (-135, 57), (-145, 60), (-152, 58), (-158, 56), (-165, 60)]
_SA = [(-79, 9), (-75, 11), (-70, 12), (-62, 10), (-52, 5), (-50, 0), (-44, -2), (-35, -6), (-37, -12),
       (-39, -17), (-41, -22), (-48, -26), (-53, -33), (-58, -38), (-62, -39), (-65, -45), (-68, -50),
       (-70, -54), (-74, -52), (-73, -45), (-72, -35), (-71, -28), (-70, -18), (-76, -14), (-81, -6),
       (-80, -2), (-78, 2), (-77, 7)]
_GL = [(-55, 60), (-45, 60), (-40, 65), (-22, 70), (-20, 78), (-35, 83), (-60, 82), (-72, 78), (-58, 75),
       (-52, 68)]
_EU = [(-10, 36), (-6, 43), (-9, 44), (-2, 48), (-5, 50), (4, 52), (8, 58), (5, 62), (14, 68), (20, 72),
       (30, 70), (30, 40), (20, 36), (10, 37), (0, 36)]
_AF = [(-17, 21), (-16, 13), (-12, 7), (-5, 5), (6, 4), (10, 0), (13, -12), (20, -35), (30, -30), (40, -15),
       (51, 12), (43, 12), (33, 30), (20, 32), (10, 37), (-6, 36), (-10, 30)]


class _Globe:
    def __init__(self, cx, cy, R, lon0=-95., lat0=22.):
        self.cx, self.cy, self.R = cx, cy, R
        self.l0, self.p0 = math.radians(lon0), math.radians(lat0)

    def p(self, lon, lat):
        l, ph = math.radians(lon) - self.l0, math.radians(lat)
        x = math.cos(ph) * math.sin(l)
        y = math.cos(self.p0) * math.sin(ph) - math.sin(self.p0) * math.cos(ph) * math.cos(l)
        z = math.sin(self.p0) * math.sin(ph) + math.cos(self.p0) * math.cos(ph) * math.cos(l)
        if z < 0:
            k = 1 / (math.hypot(x, y) or 1)
            x, y = x * k, y * k
        return (self.cx + self.R * x, self.cy - self.R * y), z >= 0

    def poly(self, ll):
        pts = []
        vis = False
        for i in range(len(ll)):
            a, b = ll[i], ll[(i + 1) % len(ll)]
            n = max(1, int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / 1.5))
            for k in range(n):
                t = k / n
                q, v = self.p(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                vis = vis or v
                pts.append(q)
        return pts if vis else None

    def curve(self, f, t0, t1, n=60):
        out, run = [], []
        for i in range(n + 1):
            lon, lat = f(t0 + (t1 - t0) * i / n)
            q, v = self.p(lon, lat)
            if v:
                run.append(q)
            elif len(run) > 1:
                out.append(run)
                run = []
            else:
                run = []
        if len(run) > 1:
            out.append(run)
        return out


def _globe(cv, cx, cy, R, ring=True, detail=2, lon0=-100.):
    G = _Globe(cx, cy, R, lon0, 24.)
    disc = _ell(cx, cy, R, R, max(48, int(R * 1.2)))
    inside = lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 < R * R
    shade = lambda x, y: (x - cx + R * .38) ** 2 + (y - cy + R * .38) ** 2 > (R * 1.08) ** 2
    deep = lambda x, y: (x - cx + R * .5) ** 2 + (y - cy + R * .5) ** 2 > (R * 1.3) ** 2
    lit = lambda x, y: (x - cx + R * .4) ** 2 + (y - cy + R * .4) ** 2 < (R * .7) ** 2
    light = lambda x, y: (x - cx + R * .42) ** 2 + (y - cy + R * .42) ** 2 < (R * .13) ** 2
    if ring:
        # brass meridian ring with degree ticks, axis pins
        r0, r1 = R + 2.5, R + max(6., R * .1)
        cv.obj([_ring(cx, cy, r0, r1, 96)], 1.)
        ticks = []
        for i in range(72):
            a = TAU * i / 72
            rr = r1 - (r1 - r0) * (.75 if i % 6 == 0 else .4)
            ticks.append([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)), (cx + rr * math.cos(a), cy + rr * math.sin(a))])
        cv.hair(ticks)
        cv.hair(_runs(C.hatch_poly(_ring(cx, cy, r0, r1, 96), 45, 2), lambda x, y: (x - cx) + (y - cy) > R * .2))
        for s in (-1, 1):
            a = math.radians(-90 + 23.5) if s < 0 else math.radians(90 + 23.5)
            px, py = cx + (r1 + 2) * math.cos(a), cy + (r1 + 2) * math.sin(a)
            cv.obj([_ell(px, py, 2.6, 2.6, 14)], 1.)
            cv.heavy([(px - 1, py), (px + 1, py)])
    # ocean
    cv.obj([disc], 1.5)
    ocean = C.hatch_poly(disc, 0, 3, .25)
    cv.hair(_runs(ocean, lambda x, y: not light(x, y)))
    cv.hair(_runs(C.hatch_poly(disc, 0, 3, 1.75), lambda x, y: not light(x, y) and not lit(x, y)))
    cv.hair(_runs(C.hatch_poly(disc, 0, 3, 1.25), shade))
    cv.hair(_runs(C.hatch_poly(disc, 45, 3), deep))
    # land
    lands = [G.poly(ll) for ll in (_NA, _SA, _GL, _EU, _AF)]
    lands = [p for p in lands if p]
    cv.obj(lands, 1.)
    for p in lands:
        cv.hair(_runs(C.hatch_poly(p, 90, 3, .25), lambda x, y: not light(x, y)))
        cv.hair(_runs(C.hatch_poly(p, 45, 3), shade))
        cv.hair(_runs(C.hatch_poly(p, -45, 3), deep))
        if detail >= 2:
            # an inner contour along the coast: engraved relief edge
            cxp = sum(q[0] for q in p) / len(p)
            cyp = sum(q[1] for q in p) / len(p)
            inner = [(q[0] + (cxp - q[0]) * .06, q[1] + (cyp - q[1]) * .06) for q in p]
            cv.hair([inner + [inner[0]]])
    # graticule
    cv.obj([], 0)
    lines = []
    for lon in range(-180, 180, 30):
        lines += G.curve(lambda t, lo=lon: (lo, t), -88, 88, 50)
    for lat in (-60, -30, 0, 30, 60):
        lines += G.curve(lambda t, la=lat: (t, la), -180, 180, 120)
    cv.hair(lines)
    cv.line(G.curve(lambda t: (t, 23.4 * math.sin(math.radians(t - lon0 + 90))), -180, 180, 120))
    (px, py), _ = G.p(-122.7, 45.5)
    star = []
    rs = max(2.2, R * .05)
    for i in range(10):
        a = -math.pi / 2 + TAU * i / 10
        rr = rs if i % 2 == 0 else rs * .45
        star.append((px + rr * math.cos(a), py + rr * math.sin(a)))
    cv.obj([star], 1.)
    return (px, py, rs)


# ------------------------------------------------------------------------------------------------
# the scene pieces
# ------------------------------------------------------------------------------------------------

def _sky(cv, X, Y, W, H, gx, gy, nray=36):
    box = _rect(X, Y, W, H)
    cv.obj([box], 0)
    lines = C.hatch_poly(box, 0, 3, .25)
    dark = C.hatch_poly(box, 0, 3, 1.75)

    def in_dark(x, y):
        a = math.atan2(y - gy, x - gx) % TAU
        return int(a / TAU * nray) % 2 == 0
    cv.hair(_runs(lines, lambda x, y: not in_dark(x, y)))
    cv.line(_runs(C.hatch_poly(box, 0, 3, .5), in_dark))
    cv.hair(_runs(dark, lambda x, y: in_dark(x, y) and y < gy))


def _mt_hood(cv, x, base, w, h):
    pk = (x + w * .52, base - h)
    prof = [(0, 0), (.1, .1), (.18, .16), (.24, .3), (.3, .36), (.36, .55), (.4, .6), (.45, .8), (.48, .88),
            (.5, .97), (.52, 1), (.55, .96), (.57, .9), (.6, .84), (.63, .78), (.66, .66), (.7, .6), (.74, .44),
            (.8, .36), (.86, .22), (.93, .12), (1, 0)]
    left = [(x + w * u, base - h * v) for u, v in prof]
    cv.obj([left], 1.)
    poly = left
    snow = lambda yy: yy < base - h * .45
    # shadow side (right of the ridge from the peak) and the timbered foot
    ridge = lambda x_, y_: x_ > pk[0] + (y_ - pk[1]) * .18
    cv.hair(_runs(C.hatch_poly(poly, 60, 2), lambda a, b: ridge(a, b) and snow(b)))
    cv.hair(_runs(C.hatch_poly(poly, -60, 3), lambda a, b: not ridge(a, b) and snow(b) and a < pk[0] - w * .12))
    cv.hair(_runs(C.hatch_poly(poly, 0, 2, .25), lambda a, b: not snow(b)))
    cv.hair(_runs(C.hatch_poly(poly, 0, 2, 1.25), lambda a, b: not snow(b) and ridge(a, b)))
    # glacier gullies
    g = []
    for i, f in enumerate((-.3, -.12, .08, .22)):
        g.append([(pk[0] + f * w * .1, pk[1] + h * .12), (pk[0] + f * w * .5, base - h * .5)])
    cv.hair(g)


def _hills(cv, X, Y, W, top, bot, seed):
    rng = random.Random(seed)
    pts = []
    n = 40
    ph = rng.random() * 6
    for i in range(n + 1):
        t = i / n
        pts.append((X + W * t, top + (bot - top) * (.35 + .25 * math.sin(t * 5.3 + ph) + .15 * math.sin(t * 13 + ph * 2))))
    poly = pts + [(X + W, bot), (X, bot)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 0, 2, .25))
    cv.hair(C.hatch_poly(poly, 0, 2, 1.25))
    # fir tips along the crest
    firs = []
    i = 0
    while i < n:
        t = i / n
        x0, y0 = pts[i]
        hh = 3 + rng.random() * 4
        firs.append([(x0 - 1.6, y0 + 1), (x0, y0 - hh), (x0 + 1.6, y0 + 1)])
        i += rng.choice((1, 1, 2))
    cv.obj(firs, .5)
    cv.hair([[(f[1][0], f[1][1] + 1.5), (f[1][0], f[0][1])] for f in firs])
    return pts


def _mast(cv, x, base, h, waves=3, wy0=None, clip=None):
    """A lattice broadcast mast with its signal rings."""
    top = (x, base - h)
    bw = h * .14
    legs = [[(x - bw / 2, base), top], [(x + bw / 2, base), top]]
    cv.obj([], 0)
    cv.line(legs)
    zig = []
    k = 0
    y = base
    while y > base - h + 3:
        y2 = y - max(3., h * .08)
        f1 = (base - y) / h
        f2 = (base - y2) / h
        a = (x - bw / 2 * (1 - f1), y) if k % 2 == 0 else (x + bw / 2 * (1 - f1), y)
        b = (x + bw / 2 * (1 - f2), y2) if k % 2 == 0 else (x - bw / 2 * (1 - f2), y2)
        zig.append([a, b])
        zig.append([(x - bw / 2 * (1 - f2), y2), (x + bw / 2 * (1 - f2), y2)])
        y = y2
        k += 1
    cv.hair(zig)
    cv.obj([_ell(top[0], top[1], 1.6, 1.6, 10)], 1.)
    arcs = []
    for i in range(waves):
        r = 5 + i * 4.5
        for s in (-1, 1):
            a0 = (math.pi if s < 0 else 0) - .55
            pts = [(top[0] + r * math.cos(a0 + 1.1 * t / 10), top[1] + r * math.sin(a0 + 1.1 * t / 10)) for t in range(11)]
            arcs.append(pts)
    cv.line(arcs)


def _bridge(cv, x0, x1, deck, tower_h, river_bot, tf=(.28, .72)):
    """The St Johns Bridge: two gothic towers, catenary main cables and suspenders, green-steel deck."""
    w = x1 - x0
    tx = [x0 + w * tf[0], x0 + w * tf[1]]
    tw = max(4., w * .045)
    top = deck - tower_h
    # main cables first (behind towers)
    cv.obj([], 0)
    cab = []
    hangers = []
    for sx in range(3):
        a = x0 if sx == 0 else tx[sx - 1]
        b = tx[0] if sx == 0 else (tx[1] if sx == 1 else x1)
        ya = top + 2 if sx else deck - 2
        yb = top + 2 if sx < 2 else deck - 2
        sag = tower_h * (.82 if sx == 1 else .3)
        pts = []
        for i in range(25):
            t = i / 24
            y = ya + (yb - ya) * t + sag * 4 * t * (1 - t) * (1 if sx == 1 else .4)
            pts.append((a + (b - a) * t, y))
        cab.append(pts)
        step = 3.
        xx = a + step
        while xx < b - 1:
            t = (xx - a) / (b - a)
            y = ya + (yb - ya) * t + sag * 4 * t * (1 - t) * (1 if sx == 1 else .4)
            if deck - y > 1.5:
                hangers.append([(xx, y), (xx, deck)])
            xx += step
    cv.hair(hangers)
    cv.line(cab)
    # deck with truss
    dh = max(3., tower_h * .1)
    dk = _rect(x0, deck, w, dh)
    cv.obj([dk], 1.)
    tr = []
    xx = x0
    k = 0
    while xx < x1 - 2:
        tr.append([(xx, deck + (dh if k % 2 else 0)), (xx + 2.5, deck + (0 if k % 2 else dh))])
        xx += 2.5
        k += 1
    cv.hair(tr)
    # piers and towers
    for X in tx:
        pier = _rect(X - tw * .7, deck + dh, tw * 1.4, river_bot - deck - dh)
        cv.obj([pier], 1.)
        cv.hair(_runs(C.hatch_poly(pier, 90, 1.5, .25), lambda a, b, X=X: a > X))
        tower = [(X - tw / 2, deck), (X - tw / 2, top + tw * .6), (X - tw * .25, top), (X, top - tw * .7),
                 (X + tw * .25, top), (X + tw / 2, top + tw * .6), (X + tw / 2, deck)]
        cv.obj([tower], 1.)
        cv.hair(_runs(C.hatch_poly(tower, 90, 1.5, .25), lambda a, b, X=X: a > X + tw * .1))
        # gothic arch openings, stacked
        ah = (deck - top) / 3.4
        arches = []
        for j in range(3):
            yb_ = deck - j * ah * 1.05 - 1.5
            hw = tw * .22
            pts = [(X - hw, yb_), (X - hw, yb_ - ah * .6), (X, yb_ - ah * .92), (X + hw, yb_ - ah * .6), (X + hw, yb_)]
            arches.append(pts)
        cv.obj(arches, .5)
        for a in arches:
            cv.line(C.hatch_poly(a, 90, 1.5, .25))
    return tx, top


def _river(cv, X, y0, W, y1, seed):
    rng = random.Random(seed)
    box = _rect(X, y0, W, y1 - y0)
    cv.obj([box], 0)
    lines = C.hatch_poly(box, 0, 2, .25)
    out = []
    for (a, b) in lines:
        x = a[0]
        y = a[1]
        depth = (y - y0) / max(1., y1 - y0)
        while x < b[0]:
            L = 6 + rng.random() * (30 * (1 - depth) + 8)
            g = 1 + rng.random() * (4 * (1 - depth))
            out.append([(x, y), (min(b[0], x + L), y)])
            x += L + g
    cv.hair(out)


def _papers(cv, cx, top, w, h, seed, drumsticks=True):
    """A stack of folded newspapers seen slightly from above; top one with a masthead,
    headline rules, columns of type and a picture; crossed drumsticks lie on it."""
    rng = random.Random(seed)
    n = 3
    sh = h / (n + 1.6)
    face_h = sh * 1.6
    sk = w * .06
    y = top + h
    faces = []
    for i in range(n):
        ww = w * (1 - .04 * i)
        off = (rng.random() - .5) * w * .05
        x0 = cx - ww / 2 + off
        ey = y - sh * .62
        edge = _rect(x0, ey, ww, sh * .62)
        cv.obj([edge], 1.)
        cv.hair(C.hatch_poly(edge, 0, 1.5, .25))
        cv.hair([[(x0 + ww * .5, ey), (x0 + ww * .5, ey + sh * .62)]])
        y = ey
        faces.append((x0, ww))
    x0, ww = faces[-1]
    fy = y - face_h
    face = [(x0 + sk, fy), (x0 + ww + sk, fy), (x0 + ww, y), (x0, y)]
    cv.obj([face], 1.)
    # page inside: shading of the fold
    cv.hair(_runs(C.hatch_poly(face, 45, 3), lambda a, b: a > x0 + ww * .5 + (b - fy) * 0))
    # masthead and type
    lx = lambda yy, f: x0 + sk * (1 - (yy - fy) / face_h) + ww * f
    m = []
    yy = fy + face_h * .14
    mh = max(2., face_h * .13)
    for k in range(int(mh / 1.5) + 1):
        y_ = round((yy + k * 1.5) * 2) / 2 + .25
        m.append([(lx(y_, .1), y_), (lx(y_, .9), y_)])
    cv.line(m)
    yy += mh + 2
    cv.hair([[(lx(yy, .06), yy), (lx(yy, .94), yy)], [(lx(yy + 1.5, .06), yy + 1.5), (lx(yy + 1.5, .94), yy + 1.5)]])
    yy += 4
    typ = []
    pic = None
    cols = 4 if ww > 90 else 3
    for c in range(cols):
        f0 = .08 + .84 * c / cols
        f1 = f0 + .84 / cols - .04
        y_ = yy
        if c == 1:
            pic = (f0, f1, y_, y_ + face_h * .3)
            y_ += face_h * .3 + 2
        while y_ < y - 3:
            typ.append([(lx(y_, f0), y_), (lx(y_, f1 - (rng.random() * .03 if rng.random() < .3 else 0)), y_)])
            y_ += 2
    cv.hair(typ)
    if pic:
        f0, f1, a, b = pic
        pp = [(lx(a, f0), a), (lx(a, f1), a), (lx(b, f1), b), (lx(b, f0), b)]
        cv.obj([pp], .5)
        cv.hair(C.hatch_poly(pp, 45, 2))
    # head rule
    cv.line([[(lx(yy - 2, .06), yy - 2), (lx(yy - 2, .5), yy - 2)]])
    if drumsticks:
        L = ww * .5
        mx, my = x0 + ww * .62 + sk * .5, fy + face_h * .55
        for s in (-1, 1):
            a = math.radians(s * 14)
            dx, dy = math.cos(a), math.sin(a)
            nx, ny = -dy, dx
            p0 = (mx - dx * L / 2, my - dy * L / 2)
            wt = max(1.2, face_h * .055)
            stick = []
            for t in (0, .7, 1):
                ww_ = wt * (1 if t < .75 else .45)
                stick.append((p0[0] + dx * L * t + nx * ww_, p0[1] + dy * L * t + ny * ww_))
            for t in (1, .7, 0):
                ww_ = wt * (1 if t < .75 else .45)
                stick.append((p0[0] + dx * L * t - nx * ww_, p0[1] + dy * L * t - ny * ww_))
            tip = _ell(p0[0] + dx * (L + wt * .6), p0[1] + dy * (L + wt * .6), wt * .9, wt * .9, 10)
            cv.obj([stick, tip], 1.)
            cv.hair([[(p0[0] + dx * L * .05 - nx * wt * .5, p0[1] + dy * L * .05 - ny * wt * .5),
                      (p0[0] + dx * L * .7 - nx * wt * .5, p0[1] + dy * L * .7 - ny * wt * .5)]])
    return fy


def _stand(cv, cx, top, bot, R):
    """Turned brass stand: a stem with a knop and a domed foot."""
    sw = max(2., R * .08)
    stem = _rect(cx - sw / 2, top, sw, bot - top)
    cv.obj([stem], 1.)
    cv.hair(_runs(C.hatch_poly(stem, 90, 1.5, .25), lambda a, b: a > cx))
    kn = _ell(cx, top + (bot - top) * .45, sw * 1.4, sw * .8, 16)
    cv.obj([kn], 1.)
    cv.hair(_runs(C.hatch_poly(kn, 90, 1.5, .25), lambda a, b: a > cx))
    fw = R * .55
    fh = max(4., R * .16)
    foot = [(cx - fw, bot)] + [(cx + fw * math.cos(math.pi - math.pi * i / 16), bot - fh * math.sin(math.pi * i / 16)) for i in range(17)]
    cv.obj([foot], 1.)
    cv.hair(_runs(C.hatch_poly(foot, 90, 1.5, .25), lambda a, b: a > cx + fw * .15))
    cv.hair(_runs(C.hatch_poly(foot, 90, 3, 1.75), lambda a, b: a < cx - fw * .45))


# ------------------------------------------------------------------------------------------------
# the vignette
# ------------------------------------------------------------------------------------------------

def _scene(X, Y, W, H, seed, clip_d=None, lod=2):
    cv = C.Canvas()
    if lod == 0:
        gx, gy = X + W / 2, Y + H / 2
        _sky(cv, X, Y, W, H, gx, gy, 24)
        R = min(W, H) * .44
        _globe(cv, gx, gy, R, ring=R > 18, detail=1)
    else:
        big = lod == 2
        hor = Y + H * (.6 if big else .66)
        gx = X + W / 2
        R = min(W * (.24 if big else .22), H * (.24 if big else .27))
        pap_h = H * (.235 if big else .25)
        pap_top = Y + H * (.655 if big else .6)
        gy = Y + H * (.37 if big else .4)
        if H < 110:
            R = min(W * .2, H * .32)
            gy = Y + H * .42
        _sky(cv, X, Y, W, hor - Y + 2, gx, gy, 28)
        rng = random.Random(seed)
        _mt_hood(cv, X + W * .6, hor - H * .04, W * .4, H * (.3 if big else .26))
        _mast(cv, X + W * .21, hor - H * .045, H * (.24 if big else .22), 3 if big else 2)
        _hills(cv, X, Y, W, hor - H * .06, hor + 1, rng.randrange(1 << 20))
        river_bot = Y + H
        _river(cv, X, hor, W, river_bot, rng.randrange(1 << 20))
        _bridge(cv, X - 4, X + W + 4, hor + H * .07, H * (.3 if big else .26), river_bot, (.1, .9))
        if H >= 110:
            _papers(cv, gx, pap_top, W * (.66 if big else .58), pap_h, rng.randrange(1 << 20), True)
            _stand(cv, gx, gy + R, pap_top + pap_h * .3, R)
        else:
            _stand(cv, gx, gy + R, Y + H * .92, R)
        _globe(cv, gx, gy, R, ring=True, detail=2)
    body = cv.svg()
    if clip_d:
        cid = C._uid("nv", X, Y, W, H, seed)
        return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
    return body


# ------------------------------------------------------------------------------------------------
# layouts (house layouts, adapted: vignette fills the whole field, lettering, no bare paper)


# ==============================================================================================
# KING-TIER KIT (batch 7). Fine English scroll as on the GRS vise, the Hunt panels and the
# presentation Colt: dozens of small true spirals grown from one stem and branching on in a
# continuous rhythm, every leaf cut with fine parallel shading on its shadow side and a bright
# edge; the ground between punched to a dark matte; every panel framed in gold-line borders and
# beading; the page's subject set in an inlaid, bead-ringed portrait medallion.
#   kk_defs()                         the matte and bead patterns (put once in the body)
#   kk_matte(d)                       punched matte ground filling path d
#   kk_field(cv, box, obst, roots, seed, rmin, rmax)   the scroll field (see its doc)
#   kk_frame(x, y, w, h, ...)         gold-line + beaded border round a panel; corner rosettes
#   kk_medallion(cx, cy, rx, ry)      bead-ringed inlay setting -> (svg_under, svg_over, clip d)
#   kk_plate(w, h, scene, egg, seed)  the whole plate at any size (band / cartouche / tall)
# ==============================================================================================
import math as _m
import random as _r
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _PI


def _kn(x):
    return _C._n(x)


# ---- matte, beads -----------------------------------------------------------------------------

def kk_defs():
    rng = _r.Random(11)
    cells = set()
    while len(cells) < 8:
        cells.add((rng.randrange(6), rng.randrange(6)))
    punch = "".join(f"M{x},{y}h1v1h-1z" for x, y in sorted(cells))
    return ('<defs><pattern id="kkM" width="6" height="6" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h6v6h-6z" fill="#000"/><path d="{punch}" fill="#fff"/></pattern></defs>')


def kk_matte(d):
    return f'<path d="{d}" fill="url(#kkM)" stroke="none"/>'


def kk_rect_d(x, y, w, h):
    return f"M{_kn(x)},{_kn(y)}h{_kn(w)}v{_kn(h)}h{_kn(-w)}z"


def _kk_ell_d(cx, cy, rx, ry, n=72):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n)[:-1], True, .1)


def kk_beads(pts, r=1.5):
    """Beads (white, .5 outlined, a black shadow speck lower right) centred on pts. 2 elements."""
    rr = _kn(r)
    a = "".join(f"M{_kn(x - r)},{_kn(y)}a{rr},{rr} 0 1,0 {_kn(2 * r)},0a{rr},{rr} 0 1,0 {_kn(-2 * r)},0z" for x, y in pts)
    s = max(.5, round(r * .7 * 2) / 2)
    b = "".join(f"M{_kn(x + r * .25)},{_kn(y + r * .2)}h{_kn(s)}v{_kn(s)}h{_kn(-s)}z" for x, y in pts)
    return (f'<path d="{a}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{b}" fill="#000" stroke="none"/>')


def _kk_along(poly, pitch, closed=True):
    """Points spaced `pitch` apart along a polyline."""
    P = poly + [poly[0]] if closed else poly
    out = []
    carry = 0.
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        L = _m.hypot(bx - ax, by - ay)
        t = carry
        while t < L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L))
            t += pitch
        carry = t - L
    return out


# ---- the scroll field -----------------------------------------------------------------------

def _kk_leaf(cv, x, y, ang, L, W, c, teeth=2, seed=0):
    """A small acanthus leaf: rolled tip, forward rounded teeth on its outer edge, a vein, fine
    parallel cuts on its shadow side (+c, the side it curls toward), a bright outer edge."""
    n = max(8, int(L / 1.1))
    pts = _C._euler(x, y, ang, L, lambda u: c * (.5 + 3.4 * _C._smooth(.55, 1., u) ** 2) / L * 1.6, n)
    ph = (seed * .41) % 1.

    def prof(u, t, amp):
        w = W * (u ** .5) * ((1 - u) ** .75) / .41 + .3
        if t and .3 < u < .97:
            v = ((u - .3) / .67 * t + ph * .3) % 1.
            w *= 1 - amp * (1 - v) ** 2
        return w
    wo = [prof(i / n, teeth, .36) for i in range(n + 1)]
    wi = [prof(i / n, 0, 0) * .85 for i in range(n + 1)]
    R = _C._Rib(pts, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    # burin cuts: curved strokes that leave the light half and sweep forward over the shadow
    # half to the edge, following the leaf's own curve; longer (darker) toward the root
    Lr = R.L
    du = 1.5 / Lr
    cuts = []
    u = .05
    while u < .9:
        s0 = -.5 * c * (1 - u) ** .6
        cuts.append([R.at(u, s0), R.at(u + .08, .93 * c)])
        u += du
    out = []
    for k, q in enumerate(cuts):
        out.extend(q if k % 2 == 0 else q[::-1])
    if out:
        cv.hair(out)
    if W > 2.6:
        cv.line(R.inset(c, lambda u: .5 if .12 < u < .88 else None, .05, .95))
    return R


class _KKSpiral:
    __slots__ = ("cx", "cy", "r", "w", "par", "kids", "pts", "S", "deg")

    def __init__(self, cx, cy, r):
        self.cx, self.cy, self.r = cx, cy, r
        self.w = 1
        self.par = None
        self.kids = []
        self.pts = None


def _kk_spiral_pts(cx, cy, R, th0, w, turns=1.45, end=.15):
    T = _TAU * turns
    b = -_m.log(end) / T
    n = max(24, int(R * T * .35))
    return [(cx + R * _m.exp(-b * T * i / n) * _m.cos(th0 + w * T * i / n),
             cy + R * _m.exp(-b * T * i / n) * _m.sin(th0 + w * T * i / n)) for i in range(n + 1)]


def _kk_bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _kk_resample(pts, step=1.5):
    out = [pts[0]]
    acc = 0.
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = _m.hypot(bx - ax, by - ay)
        if L == 0:
            continue
        t = step - acc
        while t <= L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L))
            t += step
        acc = (acc + L) % step
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def kk_field(cv, box, obst, roots, seed=0, rmin=6., rmax=16., grid=None, leafy=1., inside=None):
    """Fill box (x, y, w, h) with fine scroll. obst: shapes kept clear, ('e', cx, cy, rx, ry)
    ellipses, ('r', x0, y0, x1, y1) rects and ('c', cx, cy, r) circles. roots: [(x, y, ang_degrees)] stem sources: every
    spiral is joined, by a stem branching tangentially off its neighbour, back to a root, so the
    whole field flows from them. inside(x, y) -> bool optionally limits the field to a shape.
    Spirals are packed largest-first (radius rmax down to rmin) and painted from the twigs back
    to the root, so each parent stem lies over the branches it throws."""
    x, y, w, h = box
    rng = _r.Random(seed)
    grid = grid or max(3., min(4.5, rmin * .36))
    nx, ny = max(2, int(w / grid)), max(2, int(h / grid))
    gx = w / nx
    gy = h / ny
    D = []
    for j in range(ny):
        py = y + (j + .5) * gy
        for i in range(nx):
            px = x + (i + .5) * gx
            d = min(px - x, x + w - px, py - y, y + h - py) + rmin * .35
            if inside is not None and not inside(px, py):
                d = -1.
            for o in obst:
                if o[0] == "c":
                    continue
                if o[0] == "e":
                    _, ox, oy, rx, ry = o
                    q = _m.hypot((px - ox) / rx, (py - oy) / ry)
                    dd = (q - 1) * min(rx, ry)
                else:
                    _, x0, y0, x1, y1 = o
                    ddx = max(x0 - px, 0., px - x1)
                    ddy = max(y0 - py, 0., py - y1)
                    dd = _m.hypot(ddx, ddy) if (ddx or ddy) else -1.
                if dd < d:
                    d = dd
            D.append(d)

    def stamp(cx, cy, r, reach):
        i0, i1 = max(0, int((cx - reach - x) / gx)), min(nx - 1, int((cx + reach - x) / gx))
        j0, j1 = max(0, int((cy - reach - y) / gy)), min(ny - 1, int((cy + reach - y) / gy))
        for jj in range(j0, j1 + 1):
            qy = y + (jj + .5) * gy
            base = jj * nx
            for ii in range(i0, i1 + 1):
                dd = _m.hypot(x + (ii + .5) * gx - cx, qy - cy) - r
                if dd < D[base + ii]:
                    D[base + ii] = dd
    for o in obst:
        if o[0] == "c":
            stamp(o[1], o[2], o[3], o[3] + rmax + 2)
    sp = []
    while len(sp) < 400:
        m = max(D)
        if m < rmin:
            break
        k = D.index(m)
        i, j = k % nx, k // nx
        px, py = x + (i + .5) * gx, y + (j + .5) * gy
        r = min(rmax, m) * rng.uniform(.86, 1.)
        r = max(r, rmin)
        s = _KKSpiral(px + rng.uniform(-.4, .4) * gx, py + rng.uniform(-.4, .4) * gy, r)
        sp.append(s)
        reach = r + rmax + 2
        i0, i1 = max(0, int((px - reach - x) / gx)), min(nx - 1, int((px + reach - x) / gx))
        j0, j1 = max(0, int((py - reach - y) / gy)), min(ny - 1, int((py + reach - y) / gy))
        for jj in range(j0, j1 + 1):
            qy = y + (jj + .5) * gy
            base = jj * nx
            for ii in range(i0, i1 + 1):
                qx = x + (ii + .5) * gx
                dd = _m.hypot(qx - s.cx, qy - s.cy) - r * .97
                if dd < D[base + ii]:
                    D[base + ii] = dd
    if not sp:
        return
    # the tree: Prim from the roots
    done = []
    todo = list(sp)
    rootn = []
    for (rx_, ry_, ra) in roots:
        rn = _KKSpiral(rx_, ry_, 0.)
        rn.pts = None
        rn.deg = ra
        rootn.append(rn)

    def gap(a, b):
        return _m.hypot(a.cx - b.cx, a.cy - b.cy) - a.r - b.r
    best = {}
    for s in todo:
        bd, bp = 1e9, None
        for rn in rootn:
            dd = _m.hypot(s.cx - rn.cx, s.cy - rn.cy) - s.r
            if dd < bd:
                bd, bp = dd, rn
        best[id(s)] = (bd, bp)
    order = []
    while todo:
        s = min(todo, key=lambda q: best[id(q)][0])
        todo.remove(s)
        s.par = best[id(s)][1]
        s.par.kids.append(s)
        order.append(s)
        for q in todo:
            dd = gap(q, s) * 1.0
            if dd < best[id(q)][0]:
                best[id(q)] = (dd, s)
    # geometry, from the roots outward: winding alternates (S-rhythm), the stem leaves its parent
    # running forward and arrives tangentially at the child's outer turn
    for s in order:
        p = s.par
        dx, dy = s.cx - p.cx, s.cy - p.cy
        dl = _m.hypot(dx, dy) or 1.
        ux, uy = dx / dl, dy / dl                 # parent -> child
        if p.pts is None:                         # a root
            pa = _m.radians(p.deg)
            P0, t0 = (p.cx, p.cy), (_m.cos(pa), _m.sin(pa))
            # wind so that arriving along t0 the curl turns away from the root's line
            cr = t0[0] * uy - t0[1] * ux
            s.w = 1 if cr >= 0 else -1
            if rng.random() < .25:
                s.w = -s.w
        else:
            s.w = -p.w if rng.random() < .82 else p.w
            # the branch point: on the parent's outer turn, nearest the child, heading toward it
            pts = p.pts
            lim = max(3, int(len(pts) * .5))
            bi, bv = 1, 1e9
            for i in range(1, lim):
                qx, qy = pts[i]
                tx, ty = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
                tl = _m.hypot(tx, ty) or 1.
                dd = _m.hypot(qx - s.cx, qy - s.cy)
                fw = (tx * (s.cx - qx) + ty * (s.cy - qy)) / tl / max(dd, 1.)
                v = dd - fw * s.r * 1.2
                if v < bv:
                    bv, bi = v, i
            P0 = pts[bi]
            tx, ty = pts[bi + 1][0] - pts[bi - 1][0], pts[bi + 1][1] - pts[bi - 1][1]
            tl = _m.hypot(tx, ty) or 1.
            t0 = (tx / tl, ty / tl)
            # if the parent runs away from the child here, wind the child to suit the turn
            cr = t0[0] * (s.cy - P0[1]) - t0[1] * (s.cx - P0[0])
            s.w = 1 if cr >= 0 else -1
            if rng.random() < .2:
                s.w = -s.w
        # the child's start point: where its tangent runs away from P0
        ddx, ddy = s.cx - P0[0], s.cy - P0[1]
        dl = _m.hypot(ddx, ddy) or 1.
        dx_, dy_ = -ddx / dl, -ddy / dl           # child -> P0
        R = s.r * .86
        if s.w > 0:
            nvx, nvy = -dy_, dx_
        else:
            nvx, nvy = dy_, -dx_
        # rotate the start a little forward so the stem wraps into the curl
        th0 = _m.atan2(nvy, nvx) - s.w * .35
        spi = _kk_spiral_pts(s.cx, s.cy, R, th0, s.w, rng.uniform(1.3, 1.6))
        S0 = spi[0]
        st = (spi[1][0] - S0[0], spi[1][1] - S0[1])
        sl = _m.hypot(*st) or 1.
        st = (st[0] / sl, st[1] / sl)
        L = _m.hypot(S0[0] - P0[0], S0[1] - P0[1])
        k = max(2., L * .42)
        stem = _kk_bez(P0, (P0[0] + t0[0] * k, P0[1] + t0[1] * k), (S0[0] - st[0] * k, S0[1] - st[1] * k), S0,
                    max(4, int(L / 2)))
        s.pts = _kk_resample(stem[:-1] + spi, 1.4)
        s.S = len(_kk_resample(stem[:-1], 1.4)) if len(stem) > 1 else 0
    # paint: twigs first, root last
    for s in order[::-1]:
        _kk_scroll(cv, s, rng, leafy)


def _kk_scroll(cv, s, rng, leafy):
    pts = s.pts
    n = len(pts)
    if n < 4:
        return
    iS = min(s.S, n - 3)
    R = s.r * .8
    w0 = max(1., min(3.2, R * .2))
    W = []
    for i in range(n):
        if i < iS:
            f = i / max(1, iS)
            W.append(w0 * (.55 + .45 * f))
        else:
            f = (i - iS) / max(1, n - 1 - iS)
            W.append(max(.45, w0 * (1 - .78 * f)))
    Rb = _C._Rib(pts, W, W)
    ins = s.w                                      # the spiral turns toward +normal when w > 0? test
    # normal side toward the centre at the spiral's start
    m = min(n - 2, iS + 2)
    q = Rb.at(m / (n - 1), 1.)
    ins = 1 if _m.hypot(q[0] - s.cx, q[1] - s.cy) < _m.hypot(pts[m][0] - s.cx, pts[m][1] - s.cy) else -1
    Ltot = Rb.L

    def tang(i):
        i = min(n - 2, max(1, i))
        a, b = pts[i - 1], pts[i + 1]
        return _m.atan2(b[1] - a[1], b[0] - a[0])
    # leaves on the outer side of the curl, nearer the root on top: laid from the eye back
    spots = []
    i = iS + 1
    lim = iS + int((n - iS) * .62)
    while i < lim:
        px, py = pts[i]
        rad = _m.hypot(px - s.cx, py - s.cy)
        ll = (s.r * 1.1 - rad * .2) * .9 * rng.uniform(.85, 1.1) * leafy ** .3
        ll = min(ll, s.r * 1.05)
        if ll < 3.2:
            break
        spots.append((i, ll, rad))
        i += max(2, int(ll * .62 / 1.4))
    # leaves along the connecting stem, alternating, springing forward
    st = []
    if iS > 6 and leafy > .3:
        j = 3
        side = 1
        while j < iS - 2:
            st.append((j, side))
            side = -side
            j += max(5, int(11 / 1.4))
    for (i, ll, rad) in spots[::-1]:
        b = Rb.at(i / (n - 1), -ins * .6)
        _kk_leaf(cv, b[0], b[1], tang(i) - ins * rng.uniform(.32, .5), ll, ll * .32, ins, 2 if ll > 6 else 1,
              rng.randrange(97))
    for (j, side) in st:
        b = Rb.at(j / (n - 1), side * .6)
        ll = min(9., s.r * .7) * rng.uniform(.8, 1.)
        if ll > 3:
            _kk_leaf(cv, b[0], b[1], tang(j) + side * .7, ll, ll * .3, -side, 1, rng.randrange(97))
    # the stem: a bright cut edge outside, a shadow line inside
    cv.obj([Rb.outline()], .5)
    if w0 > 1.2:
        cv.hair(Rb.contour(.3 * ins, 0., 1., minw=1.25))
    # one leaf rolling in toward the eye
    i = iS + int((n - iS) * .55)
    if i < n - 2 and s.r > 7:
        b = Rb.at(i / (n - 1), ins * .5)
        ll = s.r * .42
        _kk_leaf(cv, b[0], b[1], tang(i) + ins * .35, ll, ll * .28, ins, 1, rng.randrange(97))
    ex, ey = pts[-1]
    rr = max(.9, W[-1] * 1.3)
    cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)


# ---- frames, medallion --------------------------------------------------------------------

def kk_frame(x, y, w, h, bead=1.5, rosette=True):
    """A panel's border drawn just outside x..x+w, y..y+h: a gold wire (white 1.5 line in fine
    black rules), a bead row, a black fillet; corner rosettes. Returns (svg, outer margin)."""
    o = []
    m1 = 1.
    # the gold wire
    o.append(f'<path d="{kk_rect_d(x - 3, y - 3, w + 6, h + 6)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{kk_rect_d(x - 1.25, y - 1.25, w + 2.5, h + 2.5)}" fill="none" stroke="#000" stroke-width=".5"/>')
    # bead row in a white channel outside
    g = 3 + bead + 1.5
    o.append(f'<path d="{kk_rect_d(x - g - bead - 1.5, y - g - bead - 1.5, w + 2 * (g + bead + 1.5), h + 2 * (g + bead + 1.5))}'
             f'{kk_rect_d(x - 3.5, y - 3.5, w + 7, h + 7)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    pts = _kk_along([(x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)], bead * 2 + 1)
    o.append(kk_beads(pts, bead))
    e = g + bead + 1.5
    o.append(f'<path d="{kk_rect_d(x - e, y - e, w + 2 * e, h + 2 * e)}" fill="none" stroke="#000" stroke-width="1"/>')
    if rosette:
        for cx, cy in ((x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)):
            o.append(kk_rosette(cx, cy, bead * 2.6))
    return "".join(o), e


def kk_rosette(cx, cy, r):
    pet = []
    for i in range(8):
        a = i * _PI / 4
        pet.append([(cx + r * .3 * _m.cos(a - .5), cy + r * .3 * _m.sin(a - .5)),
                    (cx + r * _m.cos(a), cy + r * _m.sin(a)),
                    (cx + r * .3 * _m.cos(a + .5), cy + r * .3 * _m.sin(a + .5))])
    d = "".join(_C._d(p, True, 0) for p in pet)
    return (f'<path d="{_kk_ell_d(cx, cy, r + 1, r + 1, 24)}" fill="#000" stroke="none"/>'
            f'<path d="{d}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{_kk_ell_d(cx, cy, r * .28, r * .28, 10)}" fill="#fff" stroke="#000" stroke-width=".5"/>')


def kk_medallion(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval scene: a black fillet, a bead ring, a gold wire and a fine
    rule. Returns (svg_over, clip_d of the scene, outer rx, outer ry)."""
    o = []
    g = 2.5
    a1, b1 = rx + g + bead, ry + g + bead
    outer = (rx + g + 2 * bead + 3.5, ry + g + 2 * bead + 3.5)
    o.append(f'<path d="{_kk_ell_d(cx, cy, outer[0], outer[1])}{_kk_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + g - .25, ry + g - .25)}" fill="none" stroke="#000" stroke-width=".5"/>')
    per = _C._ell_pts(cx, cy, a1, b1, 180)[:-1]
    o.append(kk_beads(_kk_along(per, bead * 2 + 1.1), bead))
    o.append(f'<path d="{_kk_ell_d(cx, cy, a1 + bead + 1, b1 + bead + 1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, outer[0] - .5, outer[1] - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), _kk_ell_d(cx, cy, rx + .5, ry + .5), outer[0], outer[1]


def kk_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
# ---- a leaner emitter: half-px path units, coarser simplification --------------------------

def _kk_pd(pen):
    o = pen.o
    out = []
    prev_m = False
    for t in o:
        if t[0] == "l" and prev_m:
            t = t[1:]
            out.append(t if t[0] == "-" else " " + t)
        else:
            out.append(t)
        prev_m = t[0] == "m"
    return "".join(out)


def _kk_zig(lines):
    """Join a sweep of hatch segments into boustrophedon polylines (the joins run along the
    region's edges, where an outline or vein is drawn anyway): about half the path data."""
    out = []
    cur = None
    flip = False
    last_v = None
    for a, b in lines:
        if flip:
            a, b = b, a
        if cur is not None and _m.hypot(a[0] - cur[-1][0], a[1] - cur[-1][1]) < 3.2:
            cur += [a, b]
        else:
            if cur:
                out.append(cur)
            cur = [a, b]
        flip = not flip
    if cur:
        out.append(cur)
    return out


def kk_svg(cv, q=2, tol_fill=.55, tol_line=.42):
    """Canvas.svg with path data in 1/q px (q=2: one device pixel) and slightly coarser
    simplification: the same occlusion, about 30 % fewer bytes."""
    if not cv.objs:
        return ""
    xs = [p[0] for o in cv.objs for poly in o[0] for p in poly] or [0.]
    ys = [p[1] for o in cv.objs for poly in o[0] for p in poly] or [0.]
    x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
    W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
    mask = [bytearray(W) for _ in range(H)]
    out = {.5: [], 1.: [], 1.5: []}
    for polys, ow, strokes in reversed(cv.objs):
        for w, lines in strokes.items():
            for pl in lines:
                _C._clip_runs(pl, mask, x0, y0, W, H, out[w])
        if ow:
            for poly in polys:
                _C._clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
        for poly in polys:
            _C._fill_mask(poly, mask, x0, y0, W, H)
    oq = _C._Q
    _C._Q = q
    try:
        T = f' transform="scale({_kn(1. / q) if q != 2 else ".5"})"'
        res = []
        pen = _C._Pen()
        for polys, _, _ in cv.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path{T} d="{_kk_pd(pen)}" fill="#fff" stroke="none"/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _C._Pen()
                for pl in out[w]:
                    pen.add(pl, False, tol_line if w < 1 else tol_line + .05)
                res.append(f'<path{T} d="{_kk_pd(pen)}" fill="none" stroke="#000" stroke-width="{_kn(w * q)}"/>')
    finally:
        _C._Q = oq
    return "".join(res)


# ---- shaped panels, offsets, bead rows ------------------------------------------------------

def kk_shape(kind, x, y, w, h, c=20.):
    """A panel outline (clockwise on screen): 'rect', 'cut' (cut corners c), 'arch' (an
    elliptical arch of rise c on a rectangle), 'oval'."""
    if kind == "cut":
        return [(x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c), (x + w - c, y + h),
                (x + c, y + h), (x, y + h - c), (x, y + c)]
    if kind == "arch":
        n = 28
        top = [(x + w / 2 - w / 2 * _m.cos(_PI * i / n), y + c - c * _m.sin(_PI * i / n)) for i in range(n + 1)]
        return top + [(x + w, y + h), (x, y + h)]
    if kind == "oval":
        return _C._ell_pts(x + w / 2, y + h / 2, w / 2, h / 2, 72)[:-1]
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def kk_offset(poly, d):
    """Offset a convex clockwise-on-screen polygon outward by d (inward if d < 0), mitred."""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1])
        e2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = _m.hypot(*e1) or 1.
        l2 = _m.hypot(*e2) or 1.
        n1 = (e1[1] / l1, -e1[0] / l1)            # outward for clockwise-on-screen
        n2 = (e2[1] / l2, -e2[0] / l2)
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        bl = _m.hypot(bx, by) or 1.
        cs = max(.35, (bx * n1[0] + by * n1[1]) / bl)
        out.append((p1[0] + bx / bl * d / cs, p1[1] + by / bl * d / cs))
    return out


class kk_inside:
    """Point-in-polygon test with the crossings of each scan row cached."""

    def __init__(self, poly):
        self.p = poly
        self.rows = {}

    def __call__(self, px, py):
        xs = self.rows.get(py)
        if xs is None:
            xs = []
            P = self.p
            n = len(P)
            for i in range(n):
                (ax, ay), (bx, by) = P[i], P[(i + 1) % n]
                if (ay > py) != (by > py):
                    xs.append(ax + (bx - ax) * (py - ay) / (by - ay))
            xs.sort()
            self.rows[py] = xs
        k = 0
        for x in xs:
            if x > px:
                break
            k += 1
        return k % 2 == 1


def _kk_pd_poly(poly, close=True):
    return _C._d(poly, close, .1)


def kk_bead_row(pts, r=1.5, closed=True):
    """A row of beads along a polyline: a black channel 2r+2 wide cut as a filled band, white
    beads as filled discs spaced 2r+1 apart, and a black speck in each bead's shadow. Every
    part is a fill, so no stroke is wider than the 0.5/1/1.5 burin. 3 elements."""
    p = r * 2 + 1.
    h = r + 1.
    P = []
    for q in pts:
        if not P or abs(q[0] - P[-1][0]) + abs(q[1] - P[-1][1]) > 1e-6:
            P.append(q)
    if closed and len(P) > 2 and abs(P[0][0] - P[-1][0]) + abs(P[0][1] - P[-1][1]) < 1e-6:
        P.pop()
    n = len(P)
    L, Rr = [], []
    for i in range(n):
        a = P[i - 1] if (closed or i > 0) else None
        b = P[(i + 1) % n] if (closed or i < n - 1) else None
        ns = []
        for u, v in ((a, P[i]), (P[i], b)):
            if u is not None and v is not None:
                dx, dy = v[0] - u[0], v[1] - u[1]
                ln = _m.hypot(dx, dy) or 1.
                ns.append((-dy / ln, dx / ln))
        nx, ny = sum(q[0] for q in ns), sum(q[1] for q in ns)
        ln = _m.hypot(nx, ny) or 1.
        nx, ny = nx / ln, ny / ln
        s = h / max(.6, nx * ns[0][0] + ny * ns[0][1])
        L.append((P[i][0] + nx * s, P[i][1] + ny * s))
        Rr.append((P[i][0] - nx * s, P[i][1] - ny * s))
    if closed:
        band = _kk_pd_poly(L) + _kk_pd_poly(Rr)
    else:
        band = _kk_pd_poly(L + Rr[::-1])
    B = _kk_along(P, p, closed)

    def discs(cs, rr):
        k = _kn(rr)
        return "".join(f"M{_kn(x - rr)},{_kn(y)}a{k},{k} 0 1,0 {_kn(2 * rr)},0a{k},{k} 0 1,0 {_kn(-2 * rr)},0z" for x, y in cs)
    return (f'<path d="{band}" fill="#000" fill-rule="evenodd" stroke="none"/>'
            f'<path d="{discs(B, r)}" fill="#fff" stroke="none"/>'
            f'<path d="{discs([(x + .5, y + .5) for x, y in B], .5)}" fill="#000" stroke="none"/>')


def kk_border(poly, bead=1.5):
    """Gold-line border round a panel whose clockwise outline is poly: from the panel out, a 1 px
    rule, a bright gap, a fine rule, a bead row, a 1 px rule. Returns (svg, total width)."""
    o = []
    g1 = kk_offset(poly, .5)
    g2 = kk_offset(poly, 2.75)
    gb = kk_offset(poly, 4. + bead)
    ge = kk_offset(poly, 5.5 + 2 * bead)
    o.append(f'<path d="{_kk_pd_poly(ge)}{_kk_pd_poly(poly[::-1])}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_pd_poly(g1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_kk_pd_poly(g2)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(gb, bead))
    o.append(f'<path d="{_kk_pd_poly(ge)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), 5.5 + 2 * bead + .5


def kk_ring(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval: a 1.5 rule, a gold gap, a fine rule, a bead ring, a rule.
    Returns (svg, outer rx, outer ry)."""
    o = []
    e = 5.5 + 2 * bead
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + e, ry + e)}{_kk_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + 2.75, ry + 2.75)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_C._ell_pts(cx, cy, rx + 4 + bead, ry + 4 + bead, 72)[:-1], bead))
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + e - .5, ry + e - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), rx + e, ry + e


# ---- Easter eggs: small figures cut white out of the matte --------------------------------

def _kk_U(cx, cy, r, pts):
    return [(cx + px * r, cy + py * r) for px, py in pts]


def _kk_cut(cv, poly, ang=45., pitch=1.5):
    cv.hair(_kk_zig(_C.hatch_poly(poly, ang, pitch)))


def _kk_wline(cv, pts, hw):
    """A white line hw px each side of pts, cut out of the matte."""
    pts = _kk_resample(pts, 1.5) if len(pts) > 1 else pts
    if len(pts) < 2:
        return
    R = _C._Rib(pts, [hw] * len(pts), [hw] * len(pts))
    cv.obj([R.outline()], 0)


def kk_egg(kind, cx, cy, r):
    """A small engraved figure filling a disc of radius r (white relief, fine shadow cuts)."""
    cv = _C.Canvas()
    E = lambda pts: _kk_U(cx, cy, r, pts)
    if kind == "drumsticks" or kind == "arms":
        if kind == "arms":
            # a sun behind: a disc and rays
            rays = []
            for i in range(16):
                a = i * _TAU / 16
                r0, r1 = .42, (.92 if i % 2 == 0 else .72)
                rays.append(E([(r0 * _m.cos(a - .08), r0 * _m.sin(a - .08)), (r1 * _m.cos(a), r1 * _m.sin(a)),
                               (r0 * _m.cos(a + .08), r0 * _m.sin(a + .08))]))
            cv.obj(rays, .5)
            for p in rays[::2]:
                cv.hair([p[1], ((p[0][0] + p[2][0]) / 2, (p[0][1] + p[2][1]) / 2)])
            disc = _C._ell_pts(cx, cy, r * .4, r * .4, 28)[:-1]
            cv.obj([disc], 1.)
            cv.hair(_C._ell_pts(cx, cy, r * .3, r * .3, 22))
            cut = [p for p in disc if p[0] - cx + p[1] - cy > -r * .1]
            _kk_cut(cv, _C._ell_pts(cx + r * .08, cy + r * .08, r * .3, r * .3, 18)[:-1], -45, 1.5)
        for sg in (-1, 1):
            a = _m.radians(45 if sg > 0 else 135)
            ux, uy = _m.cos(a), _m.sin(a)
            vx, vy = -uy, ux
            L0, L1 = -.95, .95
            tw = lambda t: .035 + .06 * (t - L0) / (L1 - L0)
            pts = [(cx + r * (t * ux + tw(t) * vx), cy + r * (t * uy + tw(t) * vy)) for t in (L0, 0, L1)]
            pts += [(cx + r * (t * ux - tw(t) * vx), cy + r * (t * uy - tw(t) * vy)) for t in (L1, 0, L0)]
            cv.obj([pts], .5)
            cv.hair([(cx + r * (t * ux - tw(t) * .4 * vx), cy + r * (t * uy - tw(t) * .4 * vy)) for t in (L0 + .1, L1 - .1)])
            tip = (cx + r * L0 * ux, cy + r * L0 * uy)
            cv.obj([_C._ell_pts(tip[0], tip[1], r * .07, r * .07, 10)[:-1]], .5)
    elif kind == "cymbal":
        e = _C._ell_pts(cx, cy - r * .2, r * .9, r * .28, 40)[:-1]
        cv.obj([E([(-.05, .05), (.05, .05), (.05, .95), (-.05, .95)])], .5)
        cv.obj([e], .5)
        for k in (.25, .45, .65, .85):
            cv.hair(_C._ell_pts(cx, cy - r * .2, r * .9 * k, r * .28 * k, 28, 0, _PI))
        _kk_cut(cv, [p for p in e if p[1] > cy - r * .2], 60, 1.5)
        cv.obj([_C._ell_pts(cx, cy - r * .25, r * .14, r * .07, 12)[:-1]], .5)
    elif kind == "castle":
        # the Somaster castle: two crenellated towers, a crenellated curtain wall between, an
        # arched gate with its portcullis
        def cren(x0, x1, ytop, yb, n):
            pts = [(x0, yb), (x0, ytop)]
            wd = (x1 - x0) / (2 * n - 1)
            for k in range(2 * n - 1):
                xa, xb = x0 + k * wd, x0 + (k + 1) * wd
                if k % 2 == 0:
                    pts += [(xa, ytop), (xb, ytop)]
                else:
                    pts += [(xa, ytop + .14), (xb, ytop + .14)]
            return pts + [(x1, ytop), (x1, yb)]
        wall = E(cren(-.5, .5, -.25, .8, 4))
        cv.obj([wall], .5)
        _kk_cut(cv, E([(.15, -.1), (.5, -.1), (.5, .8), (.15, .8)]), 90, 1.5)
        for tx in (-.78, .44):
            tw_ = E(cren(tx, tx + .34, -.85, .8, 2))
            cv.obj([tw_], .5)
            _kk_cut(cv, E([(tx + .2, -.7), (tx + .34, -.7), (tx + .34, .8), (tx + .2, .8)]), 90, 1.5)
            cv.obj([E([(tx + .13, -.5), (tx + .21, -.5), (tx + .21, -.3), (tx + .13, -.3)])], .5)
        gate = [(cx + r * .2 * _m.cos(t), cy + r * .32 + r * .26 * _m.sin(t)) for t in [_PI + _PI * k / 10 for k in range(11)]]
        gate = [(cx + r * .2, cy + r * .8)] + gate[::-1] + [(cx - r * .2, cy + r * .8)]
        cv.obj([gate], .5)
        for k in (-.1, 0, .1):
            cv.hair(E([(k, .1), (k, .8)]))
        for k in (.3, .48, .66):
            cv.hair(E([(-.19, k), (.19, k)]))
        for k in range(4):
            cv.hair(E([(-.48 + k * .03, .05 + k * .2), (.13, .05 + k * .2)]))
    elif kind == "drum":
        # a toddler's snare: a short cylinder, its rims and zigzag cords, two sticks crossed on it
        top = _C._ell_pts(cx, cy - r * .3, r * .72, r * .25, 32)[:-1]
        side = _C._ell_pts(cx, cy - r * .3, r * .72, r * .25, 16, 0, _PI) + _C._ell_pts(cx, cy + r * .45, r * .72, r * .25, 16, _PI, 0)
        cv.obj([side], .5)
        _kk_cut(cv, [p for p in side if p[0] > cx + r * .25], 90, 1.5)
        cv.obj([top], .5)
        cv.hair(_C._ell_pts(cx, cy - r * .3, r * .55, r * .17, 28))
        zz = [(cx + r * .72 * _m.cos(t), cy + (.45 if k % 2 else -.15) * r + r * .25 * _m.sin(t)) for k, t in enumerate([_PI * (1 - j / 8) for j in range(9)])]
        cv.line(zz)
        cv.line(_C._ell_pts(cx, cy + r * .45, r * .72, r * .25, 16, 0, _PI))
        for sg in (-1, 1):
            _kk_wline(cv, E([(sg * .1, -.45), (sg * .85, -.95)]), r * .05)
    elif kind == "cymbalP":
        e = _C._ell_pts(cx, cy - r * .2, r * .9, r * .32, 40)[:-1]
        cv.obj([E([(-.05, .05), (.05, .05), (.05, .95), (-.05, .95)])], .5)
        cv.obj([e], .5)
        for k in (.3, .55, .8):
            cv.hair(_C._ell_pts(cx, cy - r * .2, r * .9 * k, r * .32 * k, 28, 0, _PI))
        _kk_cut(cv, [p for p in e if p[1] > cy - r * .12], 60, 1.5)
        cv.obj([_C._ell_pts(cx, cy - r * .25, r * .12, r * .06, 12)[:-1]], .5)
        # the P engraved in the bow of the cymbal
        cv.line(E([(.42, -.05), (.42, -.4), (.6, -.4), (.66, -.32), (.6, -.24), (.42, -.24)]))
    elif kind == "note":
        # two swung eighth notes, beamed: white heads cut with a shadow crescent, white stems
        for dx, dy in ((-.45, .5), (.35, .38)):
            hd = _C._ell_pts(cx + dx * r, cy + dy * r, r * .26, r * .17, 18)[:-1]
            hd = [(cx + dx * r + (px - cx - dx * r) * .94 - (py - cy - dy * r) * .35, cy + dy * r + (py - cy - dy * r) + (px - cx - dx * r) * .25) for px, py in hd]
            cv.obj([hd], .5)
            _kk_cut(cv, [p for p in hd if p[1] > cy + dy * r - r * .02], 60, 1.5)
            _kk_wline(cv, E([(dx + .22, dy - .05), (dx + .22, -.62 - (dy - .5) * .3)]), r * .045)
        beam = E([(-.25, -.66), (.6, -.82), (.6, -.64), (-.25, -.48)])
        cv.obj([beam], .5)
        _kk_cut(cv, beam, -10, 1.5)
        for k in range(3):
            _kk_wline(cv, E([(-.85 + k * .55, .88), (-.6 + k * .55, .88)]), .5)
    elif kind == "P":
        stem = E([(-.45, -.8), (-.12, -.8), (-.12, .8), (-.45, .8)])
        bowl = [(cx - r * .14 + r * .5 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .42 * _m.sin(t))
                for t in [(-_PI / 2) + _PI * i / 20 for i in range(21)]]
        inner = [(cx - r * .14 + r * .28 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .2 * _m.sin(t))
                 for t in [(-_PI / 2) + _PI * i / 16 for i in range(17)]]
        cv.obj([bowl + inner[::-1]], 1.)
        _kk_cut(cv, bowl + inner[::-1], -45, 1.5)
        cv.obj([stem], 1.)
        _kk_cut(cv, E([(-.25, -.8), (-.12, -.8), (-.12, .8), (-.25, .8)]), 90, 1.5)
        cv.obj([E([(-.62, .62), (.05, .62), (.05, .8), (-.62, .8)]), E([(-.62, -.8), (-.05, -.8), (-.05, -.66), (-.62, -.66)])], .5)
    elif kind == "bridge":
        for tx in (-.45, .45):
            cv.obj([E([(tx - .09, .85), (tx - .05, -.75), (tx, -.92), (tx + .05, -.75), (tx + .09, .85)])], .5)
            cv.hair([(cx + (tx + .03) * r, cy - r * .7), (cx + (tx + .05) * r, cy + r * .8)])
            cv.hair(E([(tx - .05, -.35), (tx + .05, -.35)]))
        deck = E([(-1, .3), (1, .3), (1, .4), (-1, .4)])
        cv.obj([deck], .5)
        main = [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)) for t in [-.45 + .9 * i / 20 for i in range(21)]]
        _kk_wline(cv, main, .7)
        for sg in (-1, 1):
            _kk_wline(cv, [(cx + sg * r * (.45 + .53 * k / 8), cy - r * .72 + r * 1.02 * (k / 8) ** 1.6) for k in range(9)], .7)
        for k in range(1, 9):
            t = -.45 + .9 * k / 9
            _kk_wline(cv, [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)), (cx + r * t, cy + r * .3)], .5)
    elif kind == "hood":
        m = E([(-1, .7), (-.55, .1), (-.2, -.55), (0, -.8), (.15, -.62), (.5, -.05), (1, .7)])
        cv.obj([m], .5)
        _kk_cut(cv, E([(0, -.8), (.15, -.62), (.5, -.05), (1, .7), (.1, .7)]), -60, 1.5)
        snow = E([(-.35, -.3), (-.2, -.55), (0, -.8), (.15, -.62), (.3, -.35), (.15, -.42), (.02, -.25), (-.12, -.4)])
        cv.obj([snow], .5)
        for k in range(5):
            t = -.3 + k * .15
            cv.hair(E([(0, -.75), (t * .6, -.35)]))
    elif kind == "heron":
        # a great blue heron standing in the shallows, facing left: S-curved neck, dagger bill,
        # a plume off the crown, long legs, the back feathers cut in fine lines
        body = E([(-.25, -.05), (.05, -.22), (.4, -.18), (.62, .02), (.72, .22), (.45, .18), (.1, .2), (-.18, .12)])
        cv.obj([body], .5)
        _kk_cut(cv, E([(.05, -.05), (.4, -.1), (.62, .02), (.72, .22), (.45, .18), (.1, .2)]), 20, 1.5)
        _kk_wline(cv, E([(-.12, -.08), (-.3, -.3), (-.22, -.5), (-.08, -.62), (-.2, -.78)]), r * .05)
        cv.obj([E([(-.28, -.84), (-.12, -.8), (-.1, -.74), (-.24, -.72)])], .5)
        _kk_wline(cv, E([(-.25, -.79), (-.72, -.72)]), r * .03)
        _kk_wline(cv, E([(-.12, -.83), (.12, -.88)]), r * .015)
        _kk_wline(cv, E([(.15, .18), (.1, .55), (.12, .9)]), r * .025)
        _kk_wline(cv, E([(.3, .18), (.32, .55), (.4, .9)]), r * .025)
        for k in range(5):
            _kk_wline(cv, E([(-.85 + k * .1, .93 + (k % 2) * .03), (-.55 + k * .3, .93)]), .5)
    elif kind == "kranok":
        # a Thai kranok flame: a tall leaf rising, its back serrated into flame tongues, the tip
        # hooking over, a smaller flame nested inside it and a curl at its foot
        _kk_leaf(cv, cx - r * .25, cy + r * .9, -_PI / 2 + .25, r * 1.85, r * .5, -1, 4, 3)
        _kk_leaf(cv, cx - r * .1, cy + r * .7, -_PI / 2 + .35, r * 1.1, r * .3, -1, 2, 5)
        _kk_wline(cv, [(cx - r * .25 + r * .4 * _m.cos(t), cy + r * .62 + r * .3 * _m.sin(t)) for t in [_PI * (.1 + 1.4 * k / 12) for k in range(13)]], .6)
    elif kind == "elephant":
        # a caparisoned Lanna elephant walking left: domed head, ear, a trunk curling down and
        # out, a tusk, pillar legs, a patterned saddle cloth over the back
        for lx in (-.42, -.18, .3, .52):
            leg = E([(lx - .1, .15), (lx + .1, .15), (lx + .11, .82), (lx - .11, .82)])
            cv.obj([leg], .5)
            _kk_cut(cv, E([(lx + .02, .2), (lx + .1, .2), (lx + .11, .8), (lx + .02, .8)]), 90, 1.5)
        body = _C._ell_pts(cx + r * .08, cy - r * .02, r * .62, r * .4, 30)[:-1]
        cv.obj([body], .5)
        _kk_cut(cv, [p for p in body if p[1] > cy + r * .08], 10, 1.5)
        head = _C._ell_pts(cx - r * .55, cy - r * .2, r * .3, r * .32, 20)[:-1]
        cv.obj([head], .5)
        trunk = [(cx - r * (.75 + .12 * _m.sin(t * 2.2)), cy - r * .05 + r * .8 * t) for t in [k / 10 for k in range(11)]]
        trunk += [(cx - r * (.95 - .1 * k / 4), cy + r * (.75 - .08 * k)) for k in range(5)]
        _kk_wline(cv, trunk, r * .07)
        _kk_wline(cv, E([(-.62, .05), (-.8, .18), (-.9, .15)]), r * .03)
        ear = E([(-.5, -.42), (-.22, -.38), (-.18, -.05), (-.3, .12), (-.45, -.05)])
        cv.obj([ear], .5)
        _kk_cut(cv, ear, 70, 1.5)
        cloth = E([(-.12, -.42), (.5, -.42), (.55, .05), (.2, .18), (-.08, .05)])
        cv.obj([cloth], .5)
        for k in range(3):
            cv.hair(E([(-.08 + k * .02, -.3 + k * .12), (.52 - k * .01, -.3 + k * .12)]))
        _kk_cut(cv, E([(-.1, .0), (.53, .0), (.2, .15), (-.08, .05)]), 45, 1.5)
        cv.obj([_C._ell_pts(cx - r * .62, cy - r * .26, r * .04, r * .04, 6)[:-1]], .5)
    elif kind == "panel":
        fr = E([(-.85, -.2), (.55, -.75), (.85, .2), (-.55, .75)])
        cv.obj([fr], 1.)
        _kk_cut(cv, fr, -22, 1.5)
        for k in (1, 2, 3):
            t = k / 4
            a = (-.85 + 1.4 * t, -.2 - .55 * t)
            b = (-.55 + 1.4 * t, .75 - .55 * t)
            cv.line(E([a, b]))
        cv.line(E([(-.7, .275), (.7, -.275)]))
        cv.line(E([(0, .4), (0, .95)]))
    elif kind == "pinwheel":
        for i in range(5):
            a0 = i * _TAU / 5
            arm = [(cx + r * .92 * t * _m.cos(a0 + 1.4 * t), cy + r * .92 * t * _m.sin(a0 + 1.4 * t)) for t in [k / 12 for k in range(13)]]
            arm2 = [(cx + r * .92 * t * _m.cos(a0 + .5 + 1.4 * t), cy + r * .92 * t * _m.sin(a0 + .5 + 1.4 * t)) for t in [k / 12 for k in range(12, -1, -1)]]
            poly = arm + arm2
            cv.obj([poly], .5)
            if i % 2 == 0:
                _kk_cut(cv, poly, a0 * 57 + 30, 1.5)
    elif kind == "paw":
        cv.obj([_C._ell_pts(cx, cy + r * .3, r * .38, r * .32, 20)[:-1]], .5)
        _kk_cut(cv, _C._ell_pts(cx + r * .05, cy + r * .35, r * .3, r * .24, 16)[:-1], -45, 1.5)
        for a in (-2.4, -1.85, -1.3, -.75):
            px, py = cx + r * .62 * _m.cos(a), cy + r * .1 + r * .62 * _m.sin(a)
            cv.obj([_C._ell_pts(px, py, r * .15, r * .19, 12)[:-1]], .5)
    elif kind == "fleur":
        mid = E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4), (-.1, .25), (-.22, -.2), (-.2, -.62)])
        cv.obj([mid], .5)
        _kk_cut(cv, E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4)]), 70, 1.5)
        cv.hair(E([(0, -.85), (0, .3)]))
        for sg in (-1, 1):
            pet = E([(sg * .12, .2), (sg * .45, -.25), (sg * .8, -.42), (sg * .95, -.2), (sg * .78, -.05),
                     (sg * .62, -.18), (sg * .45, .05), (sg * .3, .38)])
            cv.obj([pet], .5)
            _kk_cut(cv, pet, -sg * 50, 1.5)
            cv.obj([_C._ell_pts(cx + sg * r * .82, cy - r * .28, r * .1, r * .1, 10)[:-1]], .5)
        band = E([(-.42, .32), (.42, .32), (.42, .5), (-.42, .5)])
        cv.obj([band], .5)
        _kk_cut(cv, band, 90, 1.5)
        cv.obj([E([(-.15, .5), (.15, .5), (.1, .95), (0, .82), (-.1, .95)])], .5)
    else:   # "dog": a retriever's head in profile, looking left
        head = E([(.55, .9), (.35, .25), (.1, .05), (-.15, .05), (-.55, .12), (-.82, .05), (-.88, -.12),
                  (-.7, -.22), (-.35, -.3), (-.1, -.55), (.2, -.62), (.45, -.5), (.62, -.2), (.75, .35), (.9, .9)])
        cv.obj([head], .5)
        _kk_cut(cv, E([(.35, .25), (.62, -.2), (.75, .35), (.9, .9), (.55, .9)]), 75, 1.5)
        ear = E([(.15, -.55), (.42, -.48), (.5, -.1), (.42, .35), (.3, .4), (.22, .0)])
        cv.obj([ear], .5)
        _kk_cut(cv, ear, 80, 1.5)
        cv.obj([_C._ell_pts(cx - r * .86, cy - r * .1, r * .07, r * .07, 8)[:-1]], 1.)
        cv.line(_C._ell_pts(cx - r * .12, cy - r * .3, r * .05, r * .05, 8))
        cv.hair(E([(-.82, .05), (-.5, .1)]))
    return cv.svg()


def kk_roundel(cx, cy, r, kind, bead=1.2):
    """An egg in a small bead-ringed roundel on the matte (the arms: Parker's real arms)."""
    ring, ox, oy = kk_ring(cx, cy, r, r, bead)
    if kind == "arms":
        return (f'<path d="{_kk_ell_d(cx, cy, r + .5, r + .5, 40)}" fill="#fff" stroke="none"/>'
                + bu_arms(cx - r * .72, cy - r * .95, r * 1.44, r * 1.9) + ring), ox
    return (f'<path d="{_kk_ell_d(cx, cy, r + .5, r + .5, 40)}" fill="url(#kkM)" stroke="none"/>'
            + kk_egg(kind, cx, cy, r * .86) + ring), ox


# ---- skies: burin lines that darken upward, broken by modelled cloud banks --------------------

def kk_cloud(cv, x0, x1, yb, hgt, rng):
    """A cumulus bank: a white heaped top, dark rounded underside cut in lines that follow it."""
    n = max(3, int((x1 - x0) / (hgt * .8)))
    bumps = []
    for i in range(n):
        t = (i + .5) / n
        r = hgt * (.35 + .55 * _m.sin(_PI * t) ** .7) * rng.uniform(.8, 1.1)
        bumps.append((x0 + (x1 - x0) * t, yb - r * .7, r))
    top = []
    N = int((x1 - x0) / 1.5) + 2
    for k in range(N + 1):
        x = x0 + (x1 - x0) * k / N
        y = yb
        for bx, by, br in bumps:
            dx = x - bx
            if abs(dx) < br:
                y = min(y, by - _m.sqrt(br * br - dx * dx))
        top.append((x, min(y, yb - .5)))
    bot = [(x1 - (x1 - x0) * k / 16, yb + hgt * .08 * _m.sin(_PI * k / 16)) for k in range(17)]
    cv.obj([top + bot], .5)
    # undersides: lines following the base, stacked up into the cloud, dense low and fading
    for j, d in enumerate([1., 2.5, 4., 5.5, 7.5, 10., 13.]):
        if d > hgt * .9:
            break
        cv.line([(x, max(y, yb - d)) for (x, y) in top if y < yb - d]) if j < 2 else cv.hair(
            [(x, max(y + d * .25, yb - d)) for (x, y) in top if y < yb - d - 1])
    # the heaped tops: a contour inside each bump on its shadow side
    for bx, by, br in bumps:
        if br > 4:
            cv.hair([(bx + br * .85 * _m.cos(a), by + br * .85 * _m.sin(a)) for a in [_PI * (.1 + .6 * i / 10) for i in range(11)]])


def kk_sky(cv, X, Y, W, yb, seed=0, clouds=2):
    """Sky from Y down to the horizon yb: 1 px rules at a 2 px pitch high up (dark), thinning to
    0.5 px at 2 then 3 px toward the horizon (light), with tapered 1 px bulino streaks swelling
    out of the mid sky, and cloud banks laid over it. Lines on the device grid (k/2 + 1/4)."""
    rng = _r.Random(seed * 17 + 3)
    cv.obj([[(X, Y), (X + W, Y), (X + W, yb), (X, yb)]], 0)
    H = yb - Y
    y = _m.floor(Y * 2) / 2 + .25
    while y < yb:
        f = (y - Y) / max(1., H)
        if f < .22:
            cv.line([(X, y + .25), (X + W, y + .25)])
            y += 2.
            continue
        cv.hair([(X, y), (X + W, y)])
        if f < .6 and rng.random() < .55:
            x = X + rng.uniform(-.2, 1.) * W
            L = rng.uniform(.15, .45) * W * (.6 - f) / .38
            cv.line([(x, y + .25), (x + L, y + .25)])
        y += 1.5 if f < .5 else (2. if f < .78 else 3.)
    for k in range(clouds):
        cw = W * rng.uniform(.28, .42)
        x0 = X + W * (.05 + .62 * (k / max(1, clouds - 1) if clouds > 1 else .3)) + rng.uniform(-8, 8)
        cb = Y + H * rng.uniform(.38, .62)
        kk_cloud(cv, x0, x0 + cw, cb, min(H * .2, cw * .25), rng)


# ---- the plate ------------------------------------------------------------------------------

def kk_med_poly(shape, cx, cy, rx, ry, seed=0):
    """The medallion's outline (clockwise on screen) in the box cx +- rx, cy +- ry:
    'oval', 'roundel' (a circle), 'arch' (an arched top on straight sides), 'banner' (a bowed
    ribbon with swallowtail notches), 'lunette' (a half oval on its flat side) or 'irregular'
    (a silhouette that swells up into a peak top-left, like a pine over a hummock)."""
    if shape == "roundel":
        r = min(rx, ry)
        return _C._ell_pts(cx, cy, r, r, 72)[:-1]
    if shape == "arch":
        return kk_shape("arch", cx - rx, cy - ry, 2 * rx, 2 * ry, min(rx * .55, ry * .7))
    if shape == "lunette":
        n = 40
        return [(cx - rx * _m.cos(_PI * i / n), cy + ry - 2 * ry * _m.sin(_PI * i / n)) for i in range(n + 1)]
    if shape == "banner":
        bow = ry * .3
        n = 24
        nt = min(ry * .9, rx * .14)
        us = [-1 + 2. * i / n for i in range(n + 1)]
        top = [(cx + rx * u, cy - ry + bow * u * u) for u in us]
        bot = [(cx + rx * u, cy + ry - bow + bow * u * u) for u in us[::-1]]
        return top + [(cx + rx - nt, cy + bow * .5)] + bot + [(cx - rx + nt, cy + bow * .5)]
    if shape == "irregular":
        pts = []
        n = 90
        rng = _r.Random(seed * 3 + 11)
        ph = rng.uniform(0, _TAU)
        for i in range(n):
            a = _TAU * i / n
            k = 1 + .05 * _m.sin(5 * a + ph) + .03 * _m.sin(9 * a + 2 * ph)
            da = (a - 3.92 + _PI) % _TAU - _PI          # the peak, up and to the left (the pine)
            k += .42 * _m.exp(-(da / .3) ** 2)
            pts.append((cx + rx * .9 * k * _m.cos(a), cy + ry * .78 * k * _m.sin(a) + ry * .12))
        return pts
    return _C._ell_pts(cx, cy, rx, ry, 72)[:-1]


def _kk_setting(shape, poly, cx, cy, rx, ry, bead):
    """The medallion's setting: the bead ring for an oval, the gold-line border otherwise.
    Returns (svg, width)."""
    if shape == "oval":
        s, ox, oy = kk_ring(cx, cy, rx, ry, bead)
        return s, ox - rx
    return kk_border(poly, bead)


def kk_plate(w, h, scene, egg="dog", seed=0, arms=False, egg2=None, dens=1., limit=188000,
             shape="oval", form="plate", flank=None):
    """The whole plate, edge to edge. The page's planned form (edition plan 1.6) and shape steer
    the composition; its size picks the layout:
      h < 110   form 'headpiece': a bead row and gold line, the matte carrying fine scroll that
                flows out both ways from the medallion, an egg roundel.
                form 'tailpiece' / 'marginal': a pointed cul-de-lampe silhouette (or, in a squarish
                box, a roundel) set in a gold-line border on a stippled frame ground, the scroll
                inside it flowing from the medallion; the egg lives in the scene.
      110-260   a cut-cornered panel in a gold-line, beaded border; spandrels of scroll and
                rosettes outside it; the medallion at the centre, the scroll flowing from its foot;
                on section fronts the dedication cartouche (arms) at the medallion's foot.
      > 260     an arched panel: a great copperplate scene in the medallion; under it a roundel
                (the arms on fronts, else the egg); flank roundels either side if asked; a bordered
                frieze at the foot with scroll flowing both ways from a palmette.
    The medallion takes `shape` (see kk_med_poly). scene(x, y, w, h, mode) -> svg filling that
    rect (it is clipped to the medallion); mode is 'band', 'medium' or 'tall'."""
    rng = _r.Random(seed)
    o = [kk_defs()]
    deferred = []

    def run_field(box, obst, roots, rmin, rmax, inside=None, poly=None, sd=0, area=None, cut=None):
        d = (_kk_pd_poly(poly) if poly else kk_rect_d(*box)) + (_kk_pd_poly(cut) if cut else "")
        o.append(kk_matte(d))
        if area is not None:
            deferred.append((len(o), box, obst, roots, rmin, rmax, inside, d, sd, area))
            o.append("")
            return
        cv = _C.Canvas()
        kk_field(cv, box, obst, roots, seed * 7 + sd, rmin * dens, rmax * dens, inside=inside)
        o.append(kk_clip(_C._uid("kkf", w, h, seed, sd), d, kk_svg(cv)))

    def finish():
        """The main field is grown last, its scroll size set so the plate lands under budget
        (field bytes ~ 20 * area / rmin^1.2, measured)."""
        for (k, box, obst, roots, rmin, rmax, inside, d, sd, area) in deferred:
            used = sum(len(t) for t in o) + 1800
            room = max(30000., limit - used)
            need = (20. * area / room) ** (1 / 1.2)
            f = max(dens, need / rmin)
            for tries in range(3):
                cv = _C.Canvas()
                kk_field(cv, box, obst, roots, seed * 7 + sd, rmin * f, rmax * f, inside=inside)
                o[k] = kk_clip(_C._uid("kkf", w, h, seed, sd), d, kk_svg(cv))
                over = used + len(o[k]) - limit - 6000
                if over <= 0:
                    break
                f *= (1 + over / len(o[k])) ** .85
        return _C.svg_doc(w, h, "".join(o))

    def medallion(cx, cy, rx, ry, mode, bead):
        """Paint the medallion: white base, the scene clipped to the shape, the setting."""
        poly = kk_med_poly(shape, cx, cy, rx, ry, seed)
        o.append(f'<path d="{_kk_pd_poly(kk_offset(poly, 1.))}" fill="#fff" stroke="none"/>')
        o.append(kk_clip(_C._uid("kks", w, h, seed, mode), _kk_pd_poly(poly), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, mode)))
        s, e = _kk_setting(shape, poly, cx, cy, rx, ry, bead)
        o.append(s)
        return poly, e

    def keep_clear(cx, cy, rx, ry, pad):
        """inside() test that keeps the scroll off the medallion and its setting."""
        q = kk_inside(kk_offset(kk_med_poly(shape, cx, cy, rx, ry, seed), pad))
        return lambda px, py: not q(px, py)

    if h < 110 and form in ("tailpiece", "marginal"):
        o.append(_C.dark_ground((0, 0, w, h), "S"))
        o.append(f'<path d="M0,.5H{_kn(w)}M0,{_kn(h - .5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        cx, cy = w / 2, h / 2
        if w < h * 2.6:
            # a marginal device: the roundel alone in a beaded square with rosettes at the corners
            r = min(w, h) / 2 - 9
            sq = kk_shape("rect", 3, 3, w - 6, h - 6)
            o.append(kk_matte(_kk_pd_poly(sq)))
            for (qx, qy) in ((7, 7), (w - 7, 7), (w - 7, h - 7), (7, h - 7)):
                o.append(kk_rosette(qx, qy, 3.))
            medallion(cx, cy, r, r, "band", 1.)
            return finish()
        # the cul-de-lampe: a pointed lozenge with swelling, curved sides
        a, b = w / 2 - 4, h / 2 - 4
        sil = []
        for i in range(96):
            t = _TAU * i / 96
            c_, s_ = _m.cos(t), _m.sin(t)
            sil.append((cx + a * _m.copysign(abs(c_) ** .75, c_),
                        cy + b * _m.copysign(abs(s_) ** 1.25, s_) * (1 - .25 * abs(c_) ** 3)))
        border, bw = kk_border(sil, 1.)
        ry = h / 2 - 10.5          # the medallion's setting rides over the silhouette's border
        rx = ry if shape == "roundel" else min(w * (.3 if shape == "banner" else .2), max(ry * (2.6 if shape == "banner" else 1.7), 26))
        ins = kk_inside(sil)
        clear = keep_clear(cx, cy, rx, ry, 8.)
        run_field((0, 0, w, h), [], [(cx - rx - 7, cy, 180), (cx + rx + 7, cy, 0)], max(3.6, h * .07), max(8, h * .26),
                  lambda px, py: ins(px, py) and clear(px, py), sil, 1,
                  area=.62 * w * h - _PI * (rx + 8) * (ry + 8))
        o.append(border)
        medallion(cx, cy, rx, ry, "band", 1.)
        return finish()

    if h < 110:
        top = 8.
        gy, gh = top, h - top - 3
        cx, cy = w / 2, gy + gh / 2
        ry = gh / 2 - 7.5
        if shape == "banner":
            rx = w * .36
        elif shape == "roundel":
            rx = ry
        else:
            rx = min(w * .17, max(ry * 2.2, 26))
        er = min(gh / 2 - 7, 17)
        ex = w * (.08 if seed % 2 else .92) if shape == "banner" else w * (.13 if seed % 2 else .87)
        obst = [("c", ex, cy, er + 7)] if egg else []
        if shape == "oval":
            obst.append(("e", cx, cy, rx + 9, ry + 9))
        clear = keep_clear(cx, cy, rx, ry, 9.)
        run_field((0, gy, w, gh), obst, [(cx - rx - 8, cy, 180), (cx + rx + 8, cy, 0)],
                  max(4.5, gh * .1), max(9, gh * .33), clear, sd=1,
                  area=w * gh - 3.4 * (rx + 9) * (ry + 9) - (_PI * (er + 7) ** 2 if egg else 0))
        medallion(cx, cy, rx, ry, "band", 1.)
        if egg:
            rr, _ = kk_roundel(ex, cy, er, egg, 1.)
            o.append(rr)
        o.append(f'<path d="M0,1.5H{_kn(w)}M0,{_kn(top - .5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(kk_bead_row([(0., top / 2 + .25), (w, top / 2 + .25)], 1., False))
        o.append(f'<path d="M0,{_kn(h - 1.5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(f'<path d="M0,{_kn(h - 2.75)}H{_kn(w)}" stroke="#000" stroke-width=".5"{_C._CR}/>')
        return finish()

    if h <= 260:
        m = 10.
        c = min(30., h * .17)
        poly = kk_shape("cut", m, m, w - 2 * m, h - 2 * m, c)
        outer = kk_inside(kk_offset(poly, 9.))
        run_field((0, 0, w, h), [], [(0, 0, 45), (w, 0, 135), (w, h, -135), (0, h, -45)], 4.5, 10.,
                  lambda px, py: not outer(px, py), sd=2, cut=kk_offset(poly, 4.))
        cx, cy = w / 2, h / 2
        ry = (h - 2 * m) / 2 - 12
        ar = min(15., h * .075) if arms else 0
        if arms:                       # room for the dedication cartouche at the foot
            ry -= ar + 3
            cy -= ar + 3
        rx = ry if shape == "roundel" else min(w * (.27 if shape in ("banner", "lunette") else .2), ry * (1.6 if shape in ("banner", "lunette") else 1.25))
        if shape == "irregular":
            rx = min(w * .22, ry * 1.4)
        er = min(15., h * .1)
        ex = cx + (rx + 30 + er) * (-1 if seed % 2 else 1)
        obst = [("c", ex, cy, er + 8)] if egg else []
        if arms:
            obst.append(("c", cx, cy + ry + 6 + ar, ar + 8))
        border, bw = kk_border(poly)
        for q in _kk_along(poly, 3.):
            obst.append(("c", q[0], q[1], 3.))
        pin = kk_inside(poly)
        clear = keep_clear(cx, cy, rx, ry, 10.)
        run_field((m, m, w - 2 * m, h - 2 * m), obst,
                  [(cx - rx * .55, cy + ry + 8, 160), (cx + rx * .55, cy + ry + 8, 20), (cx, cy - ry - 9, 0 if seed % 2 else 180)],
                  max(6, h * .045), max(13, h * .14), lambda px, py: pin(px, py) and clear(px, py), poly, 3,
                  area=(w - 2 * m) * (h - 2 * m) - 2 * c * c - 3.4 * (rx + 10) * (ry + 10) - _PI * (er + 8) ** 2)
        o.append(border)
        for (qx, qy) in ((m * .6 + c * .3, m * .6 + c * .3), (w - m * .6 - c * .3, m * .6 + c * .3),
                         (w - m * .6 - c * .3, h - m * .6 - c * .3), (m * .6 + c * .3, h - m * .6 - c * .3)):
            o.append(kk_rosette(qx, qy, 3.6))
        medallion(cx, cy, rx, ry, "medium", 1.5)
        if egg:
            rr, _ = kk_roundel(ex, cy, er, egg, 1.)
            o.append(rr)
        if arms:
            rr, _ = kk_roundel(cx, cy + ry + 6 + ar, ar, "arms", 1.)
            o.append(rr)
        return finish()

    # tall
    m = 10.
    fh = min(max(h * .12, 34), 60)
    yb = h - fh - 12
    rise = min(70., (yb - m) * .16)
    poly = kk_shape("arch", m, m, w - 2 * m, yb - m, rise)
    outer = kk_inside(kk_offset(poly, 9.))
    run_field((0, 0, w, yb + 6), [], [(0, 0, 45), (w, 0, 135)], 10., 22.,
              lambda px, py: not outer(px, py) and py < m + rise + 4, sd=4, cut=kk_offset(poly, 4.))
    border, bw = kk_border(poly)
    cx = w / 2
    ph = yb - m
    rr_ = min(24., ph * .07)
    ry = min(ph * .4, 175, (ph - rise * .5 - 18 - 2 * rr_ - 44) / 2)
    rx = ry if shape == "roundel" else min((w - 2 * m) * (.36 if flank else .4), ry * 1.45)
    cy = m + rise * .5 + ry + 18
    ey = min(cy + ry + 14 + rr_ + 6, yb - rr_ - 10)
    obst = [("c", cx, ey, rr_ + 10)]
    fr = 0
    if flank:
        fr = min(20., ((w - 2 * m) / 2 - rx - 18) / 2 - 2)
        fx = (cx - rx - 12 - fr, cx + rx + 12 + fr)
        for x_ in fx:
            obst.append(("c", x_, cy + ry * .35, fr + 8))
    for q in _kk_along(poly, 3.):
        obst.append(("c", q[0], q[1], 3.))
    roots = [(cx - rr_ - 10, ey, 180), (cx + rr_ + 10, ey, 0), (cx, cy - ry - 10, 0 if seed % 2 else 180)]
    pin = kk_inside(poly)
    clear = keep_clear(cx, cy, rx, ry, 10.)
    run_field((m, m, w - 2 * m, ph), obst, roots, max(9, h * .019), max(19, h * .048),
              lambda px, py: pin(px, py) and clear(px, py), poly, 5,
              area=(w - 2 * m) * ph - 3.4 * (rx + 10) * (ry + 10) - _PI * (rr_ + 10) ** 2 - .43 * rise * (w - 2 * m))
    o.append(border)
    medallion(cx, cy, rx, ry, "tall", 1.5)
    if arms or egg:
        rr, _ = kk_roundel(cx, ey, rr_, "arms" if arms else egg, 1.2)
        o.append(rr)
    if flank:
        for x_, kind in zip(fx, flank):
            rr, _ = kk_roundel(x_, cy + ry * .35, fr, kind, 1.)
            o.append(rr)
    # the frieze
    fy = yb + 8
    fp = kk_shape("rect", m + 6, fy + 4, w - 2 * m - 12, h - fy - 8)
    fb, _ = kk_border(fp, 1.2)
    pr = (h - fy - 8) / 2 - 1
    pcx, pcy = w / 2, fy + 4 + (h - fy - 8) / 2
    o.append(kk_matte(kk_rect_d(0, yb + 4, w, h - yb - 4)))
    run_field((m + 6, fy + 4, w - 2 * m - 12, h - fy - 8), [("c", pcx, pcy, pr * 1.05)] + ([("c", w * .2, pcy, pr * .8)] if egg2 else []),
              [(pcx - pr, pcy, 180), (pcx + pr, pcy, 0)], max(5.5, pr * .42), pr * 1.05, sd=7)
    o.append(fb)
    o.append(kk_egg(egg2 or "fleur", pcx, pcy, pr * .95))
    return finish()


# ---- the vignette kit: a free-standing engraved scene on a light ground -----------------------
# (art direction of Nov 12: the subject is the composition; no black field, no generic scroll; the
# frame, where there is one, is built from the page's own motifs; at most a quarter of the plate dark)


def vg_defs():
    """No ground of our own: outside the vignette's cut the plate is transparent, so the frame
    designer's light engraved ground shows through and the scene dissolves into it."""
    return ""


def vg_ragged(poly, amp=3., seed=0, step=1.6):
    """The vignette's dissolving edge: the outline pulled in by an irregular amount, slow swells
    and quick jags, so the lines of the scene stop raggedly as in Bewick's tailpieces."""
    rng = _r.Random(seed * 13 + 5)
    pts = _kk_resample(list(poly) + [poly[0]], step)[:-1]
    n = len(pts)
    ph = [rng.uniform(0, _TAU) for _ in range(3)]
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    out = []
    for i, (x, y) in enumerate(pts):
        t = _TAU * i / n
        d = amp * (.55 + .25 * _m.sin(3 * t + ph[0]) + .2 * _m.sin(7 * t + ph[1]))
        d += amp * .55 * rng.random() ** 2 * (1 if i % 2 else .4)
        dx, dy = cx - x, cy - y
        L = _m.hypot(dx, dy) or 1.
        out.append((x + dx / L * d, y + dy / L * d))
    return out


def vg_rule(poly, double=True):
    """A plate-mark: a 1 px rule round the shape and a fine rule just outside it."""
    s = f'<path d="{_kk_pd_poly(poly)}" fill="none" stroke="#000" stroke-width="1"/>'
    if double:
        s += f'<path d="{_kk_pd_poly(kk_offset(poly, 2.5))}" fill="none" stroke="#000" stroke-width=".5"/>'
    return s


def vg_leaf(cv, x, y, ang, L, W, bend=.25, shade=1, veins=True):
    """A leaf from its base (x, y) along ang: two swelling edges meeting at the tip, the midrib
    cut, the shadow half modelled in fine cuts that follow the leaf's turn."""
    ux, uy = _m.cos(ang), _m.sin(ang)
    vx, vy = -uy, ux
    n = 10
    L_, R_ = [], []
    for i in range(n + 1):
        t = i / n
        c = bend * L * t * t
        wd = W * _m.sin(_PI * t ** .8) * (1 - .15 * t)
        mx, my = x + ux * L * t + vx * c, y + uy * L * t + vy * c
        L_.append((mx + vx * wd, my + vy * wd))
        R_.append((mx - vx * wd, my - vy * wd))
    poly = L_ + R_[::-1]
    cv.obj([poly], .5)
    mid = [(x + ux * L * t + vx * bend * L * t * t, y + uy * L * t + vy * bend * L * t * t) for t in [i / 8 for i in range(9)]]
    half = (L_ if shade > 0 else R_) + mid[::-1]
    cv.hair(_kk_zig(_C.hatch_poly(half, _m.degrees(ang) + 65 * shade, 1.5)))
    cv.hair(mid[:-1])
    if veins and L > 14:
        for k in range(2, 7, 2):
            p = mid[k]
            q = (L_ if shade < 0 else R_)[min(n, k + 2)]
            cv.hair([p, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)])
    return poly


def vg_reed(cv, x, base, hgt, lean, rng, cattail=True):
    """A reed: a tapering stalk leaning off true, two blade leaves with a twist, and on most a
    cattail head, its shadow side cross-cut."""
    top = (x + lean * hgt, base - hgt)
    mid = (x + lean * hgt * .45, base - hgt * .55)
    pts = _kk_bez((x, base), mid, mid, top, 10)
    R = _C._Rib(pts, [max(.6, hgt * .012 * (1 - i / 10) + .5) for i in range(11)], [max(.6, hgt * .012 * (1 - i / 10) + .5) for i in range(11)])
    cv.obj([R.outline()], .5)
    for sg in (-1, 1):
        a = -_PI / 2 + sg * rng.uniform(.25, .55) + lean
        vg_leaf(cv, x + sg * .5, base - hgt * rng.uniform(.05, .2), a, hgt * rng.uniform(.5, .8), max(1., hgt * .018), -sg * .55, sg, False)
    if cattail:
        hx, hy = pts[7]
        hh = max(4., hgt * .16)
        head = _C._ell_pts(hx, hy, max(1.4, hgt * .028), hh / 2, 16)[:-1]
        cv.obj([head], .5)
        cv.line(_C.hatch_poly([p for p in head if p[0] >= hx - .3], 0, 1.5))
        cv.hair(_C.hatch_poly(head, 35, 2))


def vg_ribbon(cv, x0, x1, yc, hgt, bow=.3, tails=True, seed=0):
    """A ribbon banner: a bowed face from x0 to x1 (centre line yc, depth hgt), its ends turning
    back behind it in folds that are cut dark, with swallowtail ends. Returns the face polygon
    (for the content) after drawing the tails and the fold shadows."""
    n = 28
    us = [-1 + 2. * i / n for i in range(n + 1)]
    cx, rx = (x0 + x1) / 2, (x1 - x0) / 2
    b = hgt * bow
    top = [(cx + rx * u, yc - hgt / 2 + b * u * u) for u in us]
    bot = [(cx + rx * u, yc + hgt / 2 + b * u * u) for u in us[::-1]]
    face = top + bot
    if tails:
        d = hgt * .32
        for sg in (-1, 1):
            ex, ey = cx + sg * rx, yc + b
            tail = [(ex - sg * hgt * .5, ey - hgt / 2 + d), (ex + sg * hgt * 1.5, ey - hgt / 2 + d),
                    (ex + sg * hgt * 1.08, ey + d), (ex + sg * hgt * 1.5, ey + hgt / 2 + d),
                    (ex - sg * hgt * .5, ey + hgt / 2 + d)]
            cv.obj([tail], 1.)
            cv.hair(_kk_zig(_C.hatch_poly(tail, 0, 1.5)))
            cv.hair(_C.hatch_poly([(ex, ey - hgt / 2 + d), (ex + sg * hgt * .45, ey - hgt / 2 + d), (ex + sg * hgt * .3, ey + hgt / 2 + d), (ex, ey + hgt / 2 + d)], 90, 2.))
            fold = [(ex, ey - hgt / 2 + d), (ex, ey + hgt / 2), (ex - sg * hgt * .38, ey + hgt / 2 + d)]
            cv.obj([fold], .5)
            cv.line(_C.hatch_poly(fold, 90 - 30 * sg, 1.5))
    cv.obj([face], 1.)
    # the face turns: shade near each end following the bow
    for sg in (-1, 1):
        sh = [p for p in top if sg * (p[0] - cx) > rx * .82] + [p for p in bot if sg * (p[0] - cx) > rx * .82]
        if len(sh) > 2:
            cv.hair(_C.hatch_poly(sh, 90, 1.5))
    return face


def vg_cartouche(cx, cy, r):
    """The Somaster dedication cartouche: Parker's arms (solar/arms.py) in a small beaded oval,
    modelled leaves scrolling out either side (bu_cartouche in the burin kit)."""
    return bu_cartouche(cx, cy, r)


def vg_plate(w, h, scene, shape="oval", form="vignette", frame=None, arms=False, seed=0,
             ragged=True, amp=None, pad=None, aspect=None, limit=192000):
    """A plate in the planned form, transparent outside its cut: the scene, shaped
    (kk_med_poly) and either dissolving at a ragged edge or set in a plate-mark; the page's own
    frame (frame(box, poly, w, h, mode) -> svg) round it; on section fronts the dedication
    cartouche at the foot. scene(x, y, w, h, mode) -> svg filling that rect."""
    o = [kk_defs(), vg_defs()]
    m = 4.
    res = 0.
    if arms and h >= 110:
        res = min(40., h * .16)
    ar = aspect or {"oval": 1.7, "roundel": 1., "arch": 1.25, "banner": 4.2, "lunette": 2.1, "irregular": 1.55}.get(shape, 1.6)
    pd = 8. if pad is None else pad
    aw, ah = w - 2 * m - 2 * pd, h - 2 * m - 2 * pd - res
    if form == "headpiece":
        bw, bh = aw, ah
    else:
        bw = min(aw, ah * ar)
        bh = min(ah, bw / ar)
        if shape == "roundel":
            bw = bh = min(aw, ah)
    cx, cy = w / 2, m + pd + ah / 2
    rx, ry = bw / 2, bh / 2
    mode = "band" if bh < 80 else ("medium" if bh <= 230 else "tall")
    poly = kk_med_poly(shape, cx, cy, rx, ry, seed)
    cp = vg_ragged(poly, amp if amp is not None else max(3., min(9., bh * .05)), seed) if ragged else poly
    o.append(f'<path d="{_kk_pd_poly(cp)}" fill="#fff" stroke="none"/>')
    o.append(kk_clip(_C._uid("vgs", w, h, seed), _kk_pd_poly(cp), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, mode)))
    if not ragged:
        o.append(vg_rule(poly))
    if frame:
        o.append(frame((cx - rx, cy - ry, 2 * rx, 2 * ry), poly, w, h, mode))
    if res:
        r = res * .38
        o.append(vg_cartouche(cx, h - m - res / 2 - 1, r))
    return _C.svg_doc(w, h, "".join(o))


def vg_wheat(cv, pts, ear=.42, k=1.):
    """A wheat stalk along pts (base first): the straw, and on its last part the ear, kernels set
    in pairs and each shaded on its lower side, long awns combed back from them."""
    R = _C._Rib(pts, [max(.5, .9 * k)] * len(pts), [max(.5, .9 * k)] * len(pts))
    cv.obj([R.outline()], .5)
    n = len(pts)
    i0 = int(n * (1 - ear))
    for i in range(i0, n - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        a = _m.atan2(y1 - y0, x1 - x0)
        for sg in (-1, 1):
            ka = a + sg * .55
            L = 4.2 * k * (1 - .35 * (i - i0) / max(1, n - i0))
            vg_leaf(cv, x0, y0, ka, L, 1.3 * k, 0, -sg, False)
            tx, ty = x0 + _m.cos(ka) * L, y0 + _m.sin(ka) * L
            cv.hair([(tx, ty), (tx + _m.cos(a + sg * .25) * L * 1.4, ty + _m.sin(a + sg * .25) * L * 1.4)])


def vg_wreath(cv, cx, cy, r, kind="wheat", seed=0, k=1.):
    """A wreath round a roundel, two branches rising from a bow at the foot to meet at the top:
    'wheat' (ears on curving straws) or 'fir' (Douglas-fir sprigs with a cone or two)."""
    rng = _r.Random(seed)
    for sg in (-1, 1):
        n = 7
        for j in range(n):
            a0 = _PI / 2 + sg * (.25 + j * (2.5 / n))
            a1 = a0 + sg * .55
            pts = [(cx + (r + 1.5 + 2 * _m.sin(_PI * t)) * _m.cos(a0 + (a1 - a0) * t), cy + (r + 1.5 + 2 * _m.sin(_PI * t)) * _m.sin(a0 + (a1 - a0) * t)) for t in [i / 8 for i in range(9)]]
            if kind == "wheat":
                vg_wheat(cv, pts, .55, k)
            else:
                px, py = pts[4]
                for q in range(5):
                    t = q / 4
                    x_, y_ = pts[int(t * 8)]
                    aa = a0 + (a1 - a0) * t
                    for s2 in (-1, 1):
                        cv.hair([(x_, y_), (x_ + _m.cos(aa + sg * _PI / 2 + s2 * .9) * 4 * k, y_ + _m.sin(aa + sg * _PI / 2 + s2 * .9) * 4 * k)])
                Rb = _C._Rib(pts, [.7] * 9, [.7] * 9)
                cv.obj([Rb.outline()], .5)
                if j % 3 == 1:
                    cone = _C._ell_pts(px, py, 2.2 * k, 3.4 * k, 12)[:-1]
                    cv.obj([cone], .5)
                    cv.line(_C.hatch_poly(cone, 0, 1.5))
    # the bow
    for sg in (-1, 1):
        loop = [(cx, cy + r + 3), (cx + sg * 5 * k, cy + r - 1), (cx + sg * 7 * k, cy + r + 3), (cx + sg * 4 * k, cy + r + 5)]
        cv.obj([loop], .5)
        cv.hair(_C.hatch_poly(loop, 60 * sg, 1.5))
        tail = [(cx, cy + r + 4), (cx + sg * 3 * k, cy + r + 11 * k), (cx + sg * 5 * k, cy + r + 10 * k), (cx + sg * 1.5, cy + r + 4)]
        cv.obj([tail], .5)
        cv.hair(_C.hatch_poly(tail, 90, 1.5))
    cv.obj([_C._ell_pts(cx, cy + r + 3.5, 2 * k, 1.7 * k, 10)[:-1]], .5)


def vg_bough(cv, pts, k=1., seed=0, twigs=True):
    """A Douglas-fir bough along pts (base first): a tapering limb, side twigs thrown forward,
    and every part clothed in needles combed forward, light above and cut heavier beneath, so the
    bough has a lit top and a shadowed belly."""
    rng = _r.Random(seed)
    pts = _kk_resample(pts, 1.5)
    n = len(pts)
    wl = [max(.6, 2.4 * k * (1 - i / n)) for i in range(n)]
    R = _C._Rib(pts, wl, wl)

    def needles(P, L0, dens=1.6):
        m = len(P)
        up, dn = [], []
        acc = 0.
        for i in range(1, m):
            (x0, y0), (x1, y1) = P[i - 1], P[i]
            seg = _m.hypot(x1 - x0, y1 - y0)
            acc += seg
            if acc < dens:
                continue
            acc = 0.
            a = _m.atan2(y1 - y0, x1 - x0)
            t = i / m
            L = L0 * (1 - .45 * t) * rng.uniform(.8, 1.1)
            for sg, bag in ((-1, up), (1, dn)):
                b = a + sg * rng.uniform(.75, 1.05)
                bag.append([(x1, y1), (x1 + _m.cos(b) * L, y1 + _m.sin(b) * L)])
        cv.hair(up)
        cv.line(dn[::2])
        cv.hair(dn[1::2])

    if twigs:
        for i in range(6, n - 6, max(6, int(10 / k))):
            (x0, y0), (x1, y1) = pts[i - 1], pts[i]
            a = _m.atan2(y1 - y0, x1 - x0)
            sg = 1 if (i // 7) % 2 else -1
            L = 14 * k * (1 - .5 * i / n) * rng.uniform(.8, 1.2)
            b = a + sg * .6
            tw = [(x1 + _m.cos(b) * L * u + _m.cos(a) * L * .3 * u * u, y1 + _m.sin(b) * L * u + _m.sin(a) * L * .3 * u * u) for u in [j / 8 for j in range(9)]]
            cv.obj([], 0)
            cv.line(tw)
            needles(tw, 5. * k)
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(.5, 0, 1))
    needles(pts, 6.5 * k, 1.3)


def vg_rope(cv, pts, r=3., closed=False):
    """A laid rope along pts: strands twisting across it, each a lozenge lit on its upper edge
    and cut in fine lines on its lower, the lay running at a steady pitch."""
    P = _kk_resample(list(pts) + ([pts[0]] if closed else []), 1.)
    n = len(P)
    step = max(2, int(r * 1.3))
    for i in range(0, n - step - 1, step):
        (x0, y0), (x1, y1) = P[i], P[min(n - 1, i + step)]
        a = _m.atan2(y1 - y0, x1 - x0)
        nx, ny = -_m.sin(a), _m.cos(a)
        ux, uy = _m.cos(a), _m.sin(a)
        L = r * 1.3
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        q = [(c[0] - nx * r - ux * L * .9, c[1] - ny * r - uy * L * .9), (c[0] - nx * r + ux * L * .1, c[1] - ny * r + uy * L * .1),
             (c[0] + nx * r + ux * L * .9, c[1] + ny * r + uy * L * .9), (c[0] + nx * r - ux * L * .1, c[1] + ny * r - uy * L * .1)]
        cv.obj([q], .5)
        cv.hair([((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2), ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2)])
        cv.hair([(q[2][0] - ux * .8, q[2][1] - uy * .8), (q[3][0] + ux * .3, q[3][1] + uy * .3)])


def vg_coil(cv, cx, cy, r):
    """A coil of rope lying flat: turns of laid rope round a dark centre."""
    rr = r
    while rr > 3:
        vg_rope(cv, _C._ell_pts(cx, cy, rr, rr * .45, max(16, int(rr * 3))), 2.2, True)
        rr -= 4.6
    cv.obj([_C._ell_pts(cx, cy, max(1.5, rr), max(1., rr * .45), 10)[:-1]], .5)


# ---- the plate ------------------------------------------------------------------------------

# Edition plan: section front vignette, 25-30%, arched, with the dedication cartouche at its foot.
FORM = {"form": "vignette", "share": .28, "shape": "arch", "egg": "a Blazers pinwheel roundel", "arms": True}


def _courses(cv, x0, x1, y0, y1, pitch, shade, stagger):
    """Masonry: course lines, the vertical joints staggered course by course."""
    lines, joints = [], []
    y = y0 + pitch
    k = 0
    while y < y1:
        lines.append([(x0, y), (x1, y)])
        x = x0 + (stagger if k % 2 else stagger * .5 + pitch * 1.2)
        while x < x1 - 1:
            joints.append([(x, y - pitch + .5), (x, y - .3)])
            x += pitch * 2.4
        y += pitch
        k += 1
    cv.hair(lines)
    if pitch >= 3:
        cv.hair(joints)


def _clock_face(cv, ccx, ccy, cr, hh, mm):
    """The tower clock, made to read at a glance: a moulded bezel lit top-left, a white dial with
    sixty minute dots and twelve bold hour bars (the twelve doubled), a short spade-tipped hour
    hand and a long fine minute hand with a counterweight tail."""
    bu_ball(cv, ccx, ccy, cr + 2.2, None, .25, .6, 1.5, None, 1., 40, False)
    cv.obj([C._ell_pts(ccx, ccy, cr, cr, 40)[:-1]], 1.)
    tk, mk = [], []
    for i in range(60):
        a = math.pi * 2 * i / 60
        if i % 5 == 0:
            r0 = cr * (.7 if i % 15 == 0 else .76)
            tk.append([(ccx + r0 * math.sin(a), ccy - r0 * math.cos(a)), (ccx + cr * .93 * math.sin(a), ccy - cr * .93 * math.cos(a))])
        elif cr > 7:
            mk.append([(ccx + cr * .88 * math.sin(a), ccy - cr * .88 * math.cos(a)), (ccx + cr * .93 * math.sin(a), ccy - cr * .93 * math.cos(a))])
    cv.line(tk)
    cv.hair(mk)
    ah = math.pi * 2 * ((hh % 12) + mm / 60) / 12
    am = math.pi * 2 * mm / 60
    ux, uy = math.sin(ah), -math.cos(ah)
    hl = cr * .52
    if cr > 18:
        sp = [(ccx - uy * .9, ccy + ux * .9), (ccx + ux * hl * .7 - uy * 1.4, ccy + uy * hl * .7 + ux * 1.4),
              (ccx + ux * hl, ccy + uy * hl), (ccx + ux * hl * .7 + uy * 1.4, ccy + uy * hl * .7 - ux * 1.4), (ccx + uy * .9, ccy - ux * .9)]
        cv.obj([sp], 1.)
    cv.obj([], 0)
    cv.heavy([(ccx - ux * cr * .1, ccy - uy * cr * .1), (ccx + ux * hl, ccy + uy * hl)])
    vx, vy = math.sin(am), -math.cos(am)
    cv.obj([], 0)
    cv.line([(ccx - vx * cr * .2, ccy - vy * cr * .2), (ccx + vx * cr * .86, ccy + vy * cr * .86)])
    cv.obj([C._ell_pts(ccx, ccy, 1.4, 1.4, 10)[:-1]], 1.)


def _clock_tower(cv, cx, base, tw, th, hh, mm):
    """The Oregonian tower in the morning light from the left: the lit front in coursed masonry
    whose courses swell toward the shaded corner, the side face dark in crossed cuts, corner
    piers rounded off, deep-set arched windows, the clock at the edition's hour, a corbelled
    cornice and the steep shingled spire, lit left and dark right, its finial."""
    sw = tw * .42
    top = base - th
    roof_b = top + th * .02
    sp_h = th * .55
    x0, x1 = cx - tw / 2, cx + tw / 2
    side = [(x1, base), (x1, roof_b), (x1 + sw, roof_b - sw * .18), (x1 + sw, base - sw * .05)]
    bu_form(cv, side, lambda x, y: .62 + .15 * (y - roof_b) / th, 90., 1.5, 0, -32., 1., cross_at=.66)
    front = [(x0, base), (x0, roof_b), (x1, roof_b), (x1, base)]
    cv.obj([front], 1.)
    pc = max(2., tw * .045)
    ftone = lambda x, y: .12 + .42 * ((x - x0) / tw) ** 1.3 + .18 * (y - roof_b) / th
    y = roof_b + pc
    k = 0
    while y < base - .5:
        bu_cut(cv, [(x0 + 1, y), (x1 - 1, y)], lambda px, py: ftone(px, py) + .12)
        x = x0 + (tw * .07 if k % 2 else tw * .035 + pc * 1.2)
        while x < x1 - 1:
            bu_cut(cv, [(x, y - pc + .5), (x, y - .3)], ftone)
            x += pc * 2.4
        y += pc
        k += 1
    for px in (x0, x1 - tw * .1):
        R = C._Rib([(px + tw * .05, base), (px + tw * .05, roof_b)], [tw * .05] * 2, [tw * .05] * 2)
        bu_rib(cv, R, .1 if px == x0 else .3, .55, 1.5, -1, .5)
    for k in range(3):
        wy1 = base - th * (.08 + .19 * k)
        wy0 = wy1 - th * .12
        for wx in (cx - tw * .2, cx + tw * .2):
            ww = tw * .12
            arch = [(wx - ww / 2, wy1), (wx - ww / 2, wy0 + ww / 2)] + \
                   [(wx - ww / 2 * math.cos(math.pi * i / 8), wy0 + ww / 2 - ww / 2 * math.sin(math.pi * i / 8)) for i in range(9)] + \
                   [(wx + ww / 2, wy1)]
            bu_form(cv, arch, lambda px, py, wx=wx: .9 - .25 * max(0., (px - wx) / ww), 90., 1.5, 0, 0., .5, cross_at=.7)
            cv.obj([[(wx - ww / 2 - 1, wy1), (wx + ww / 2 + 1, wy1), (wx + ww / 2 + 1, wy1 + 1.5), (wx - ww / 2 - 1, wy1 + 1.5)]], .5)
    _clock_face(cv, cx, roof_b + th * .21, tw * .4, hh, mm)
    cor = [(x0 - 2, roof_b + 3), (x1 + 2, roof_b + 3), (x1 + 2, roof_b - 2), (x0 - 2, roof_b - 2)]
    bu_form(cv, cor, lambda px, py: .25 + .4 * (py - roof_b + 2) / 5 + .2 * (px - x0) / tw, 0., 1.5, 0, None, 1.)
    cv.obj([], 0)
    cv.hair([(x, roof_b + 3) for x in (x0,)] + [(x1, roof_b + 3)])
    tip = (cx + sw * .3, roof_b - sp_h)
    sp_l = [(x0 - 2, roof_b - 2), tip, (cx + sw * .3, roof_b - 2)]
    sp_r = [(cx + sw * .3, roof_b - 2), tip, (x1 + sw + 1, roof_b - sw * .18 - 2)]
    cv.obj([sp_l + [sp_r[2]]], 1.)
    k = 1
    rh = max(2., tw * .05)
    while True:
        t = k * rh / sp_h
        if t > .94:
            break
        yy = roof_b - 2 - sp_h * t
        xl = x0 - 2 + (tip[0] - x0 + 2) * t
        xm = tip[0]
        xr = x1 + sw + 1 + (tip[0] - x1 - sw - 1) * t
        bu_cut(cv, [(xl, yy), (xm, yy)], lambda px, py: .12 + .38 * (px - xl) / max(1., xm - xl))
        k += 1
    for pl in bu_hatch(sp_r, 75., 2., 0):
        bu_cut(cv, pl, lambda px, py: .42 + .25 * (py - tip[1]) / sp_h)
    cv.line([tip, (tip[0], tip[1] - th * .08)])
    bu_ball(cv, tip[0], tip[1] - th * .08, 1.8, None, .1, .8, 1.5, None, .5, 10)
    for tx in (x0 - 1, x1 + 1):
        tt = [(tx - tw * .06, roof_b - 2), (tx, roof_b - 2 - th * .14), (tx + tw * .06, roof_b - 2)]
        bu_form(cv, tt, lambda px, py, tx=tx: .1 + .7 * max(0., (px - tx) / (tw * .06)), 85., 1.5, 0, None, .5)


def _bridge_m(cv, x0, x1, deck, tower_h, river_bot, tf=(.28, .72)):
    """The St Johns Bridge in the middle distance: towers lit on their left faces, cables, the
    hangers fine, the deck truss in light, the piers dark into the water."""
    w = x1 - x0
    tx = [x0 + w * tf[0], x0 + w * tf[1]]
    tw = max(4., w * .045)
    top = deck - tower_h
    cv.obj([], 0)
    cab, hangers = [], []
    for sx in range(3):
        a = x0 if sx == 0 else tx[sx - 1]
        b = tx[0] if sx == 0 else (tx[1] if sx == 1 else x1)
        ya = top + 2 if sx else deck - 2
        yb = top + 2 if sx < 2 else deck - 2
        sag = tower_h * (.82 if sx == 1 else .3)
        cab.append([(a + (b - a) * i / 24, ya + (yb - ya) * i / 24 + sag * 4 * (i / 24) * (1 - i / 24) * (1 if sx == 1 else .4)) for i in range(25)])
        xx = a + 3.
        while xx < b - 1:
            t = (xx - a) / (b - a)
            y = ya + (yb - ya) * t + sag * 4 * t * (1 - t) * (1 if sx == 1 else .4)
            if deck - y > 1.5:
                hangers.append([(xx, y), (xx, deck)])
            xx += 3.
    cv.hair(hangers)
    cv.line(cab)
    dh = max(3., tower_h * .1)
    dk = _rect(x0, deck, w, dh)
    bu_form(cv, dk, lambda px, py: .3 + .4 * (py - deck) / dh, 0., 1.5, 0, None, 1.)
    for X in tx:
        pier = _rect(X - tw * .7, deck + dh, tw * 1.4, river_bot - deck - dh)
        bu_form(cv, pier, lambda px, py, X=X: .3 + .45 * (px - X + tw * .7) / (tw * 1.4), 90., 1.5, 0, None, 1.)
        tower = [(X - tw / 2, deck), (X - tw / 2, top + tw * .6), (X - tw * .25, top), (X, top - tw * .7),
                 (X + tw * .25, top), (X + tw / 2, top + tw * .6), (X + tw / 2, deck)]
        bu_form(cv, tower, lambda px, py, X=X: .1 + .7 * max(0., (px - X + tw * .1) / (tw * .6)), 90., 1.5, 0, None, 1.)
        ah = (deck - top) / 3.4
        arches = []
        for j in range(3):
            yb_ = deck - j * ah * 1.05 - 1.5
            hw = tw * .22
            arches.append([(X - hw, yb_), (X - hw, yb_ - ah * .6), (X, yb_ - ah * .92), (X + hw, yb_ - ah * .6), (X + hw, yb_)])
        for a in arches:
            bu_form(cv, a, lambda px, py: .85, 90., 1.5, 0, None, .5)
    return tx, top


def tower_scene(X, Y, W, H, mode, seed, date):
    """The Oregonian clock tower over the Willamette at morning. Background: the sky in burin
    lines opening to the light on the left, modelled clouds, Mt. Hood and the West Hills.
    Middle: the St Johns Bridge and the river, the tower and the bridge broken in its ripples.
    Foreground: the stone embankment and the tower, richest and nearest."""
    rng = random.Random(seed)
    cv = C.Canvas()
    big = mode == "tall"
    band = mode == "band"
    hor = Y + H * (.66 if not band else .7)
    bu_sky(cv, X, Y, W, hor + 2 - Y, lambda x, y: .62 - .3 * max(0., (y - Y) / (hor - Y)) - .22 * max(0., 1 - (x - X) / (W * .5)), None, seed, 2.)
    crng = random.Random(seed + 4)
    if not band:
        bu_cloud(cv, X + W * .38, X + W * .78, Y + H * .3, H * .12, crng)
        if big:
            bu_cloud(cv, X + W * .62, X + W * 1.02, Y + H * .16, H * .08, crng)
        bu_hood(cv, X + W * .76, hor - H * .04, H * .24, seed)
    # the West Hills: a long modelled ridge, firs along its crest
    hrng = random.Random(seed + 8)
    ph = hrng.random() * 6
    top, bot = hor - H * .06, hor + 1
    pts = [(X - 2 + (W + 4) * i / 60, top + (bot - top) * (.35 + .25 * math.sin(i / 60 * 5.3 + ph) + .15 * math.sin(i / 60 * 13 + ph * 2))) for i in range(61)]
    hp = pts + [(X + W + 2, bot), (X - 2, bot)]
    bu_form(cv, hp, lambda x, y: .3 + .3 * (y - top) / max(1., bot - top) + .1 * math.sin(x * .2), 70., 2., 1.5, None, .5)
    i = 0
    while i < 60:
        x0_, y0_ = pts[i]
        hh = 2.5 + hrng.random() * 3.5
        f = [(x0_ - 1.5, y0_ + 1), (x0_, y0_ - hh), (x0_ + 1.5, y0_ + 1)]
        bu_form(cv, f, lambda x, y, x0_=x0_: .3 + .5 * max(0., (x - x0_) / 1.5), 90., 1.5, 0, None, .5)
        i += hrng.choice((1, 2, 2))
    tw = min(W * (.18 if not band else .2), H * .24)
    th = H * .52
    tcx, tbase = X + W * .26, Y + H * .9
    bx0 = X + W * .35

    def refl(x, y):
        d = y - hor
        if abs(x - tcx) < tw / 2 and d < th * .9:
            return .2 if x < tcx + tw * .1 else .5
        if tcx + tw / 2 <= x < tcx + tw / 2 + tw * .42 and d < th * .8:
            return .8
        return None
    bu_water(cv, X - 2, hor, W + 4, Y + H - hor + 2, refl, seed, lambda x, y: .35 + .3 * (y - hor) / max(1., Y + H - hor), 2., (X + W * .12, 6.))
    _bridge_m(cv, bx0, X + W + 6, hor + H * .07, H * (.26 if not band else .3), Y + H, (.28, .78))
    # the stone embankment the tower stands on, in coursed blocks, the river lapping its foot
    bank = [(X - 2, Y + H * .86), (X + W * .45, Y + H * .9), (X + W * .55, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([bank], 1.)
    y = Y + H * .86 + 2
    k = 0
    while y < Y + H + 2:
        xr = X + W * .45 + (y - Y - H * .9) * (W * .1) / (H * .1 + 2)
        bu_cut(cv, [(X - 2, y), (xr, y)], lambda px, py: .35 + .35 * (py - Y - H * .86) / (H * .14) + .1 * px / W)
        xx = X + (k % 2) * 5
        while xx < xr - 2:
            cv.hair([(xx, y - 2), (xx, y)])
            xx += 10
        y += 2.
        k += 1
    _clock_tower(cv, tcx, tbase, tw, th, 8, 34)
    return kk_svg(cv)


def _gothic_tower(cv, cx, base, tw, th):
    """A St Johns Bridge tower in the foreground: two tapering legs lit on the left and cut dark
    on the right, joined by pointed lancet arches, a spired cap, spirelets at the corners."""
    top = base - th
    for sg in (-1, 1):
        xo = cx + sg * tw * .5
        xi = cx + sg * tw * .2
        leg = [(xo, base), (cx + sg * tw * .38, top), (cx + sg * tw * .12, top), (xi, base)] if sg < 0 else \
              [(xi, base), (cx + sg * tw * .12, top), (cx + sg * tw * .38, top), (xo, base)]
        lx0 = min(p[0] for p in leg)
        bu_form(cv, leg, (lambda px, py: .15 + .25 * (px - (cx - tw * .5)) / (tw * .3)) if sg < 0 else
                (lambda px, py: .45 + .35 * (px - (cx + tw * .12)) / (tw * .38)), 90., 1.5, 0, None if sg < 0 else 25., 1., cross_at=.66)
    for k in range(4):
        yb = base - th * (.15 + .22 * k)
        ww = tw * (.42 - .05 * k)
        ah = ww * 1.3
        arch = [(cx - ww / 2, yb), (cx - ww / 2, yb - ah * .45), (cx, yb - ah), (cx + ww / 2, yb - ah * .45), (cx + ww / 2, yb),
                (cx + ww / 2 + 1.5, yb), (cx + ww / 2 + 1.5, yb - ah * .5), (cx, yb - ah - 2), (cx - ww / 2 - 1.5, yb - ah * .5), (cx - ww / 2 - 1.5, yb)]
        bu_form(cv, arch, lambda px, py: .2 + .4 * (px - cx + ww) / (2 * ww), 0., 1.5, 0, None, .5)
    cap = [(cx - tw * .42, top + 1), (cx, top - th * .1), (cx + tw * .42, top + 1)]
    bu_form(cv, cap, lambda px, py: .1 + .7 * max(0., (px - cx) / (tw * .42)), 80., 1.5, 0, None, 1.)
    for sg in (-1, 1):
        sp = [(cx + sg * tw * .38 - 1.2, top + 1), (cx + sg * tw * .38, top - th * .07), (cx + sg * tw * .38 + 1.2, top + 1)]
        cv.obj([sp], .5)


def _bridge_frame(box, poly, w, h, mode, seed):
    """The arched vignette is carried between the two gothic towers of the St Johns Bridge: they
    stand either side of the arch on the river line, their back-stay cables sweeping down and out
    to the page edges with the suspenders hanging from them, the deck running out level."""
    bx, by, bw, bh = box
    cv = C.Canvas()
    base = by + bh
    tw = max(10., bh * .13)
    th = bh * .9
    for sg in (-1, 1):
        cx = bx + bw / 2 + sg * (bw / 2 + tw * .75)
        ex = bx + bw / 2 + sg * min(w / 2 - 6, bw / 2 + tw * .75 + bh * 1.3)
        top = base - th + 3
        D = base - bh * .2 - top
        cab = [(cx + (ex - cx) * t, top + D * t + D * .18 * math.sin(math.pi * t)) for t in [i / 24 for i in range(25)]]
        deck = base - bh * .16
        cv.obj([], 0)
        sus = []
        for i in range(2, 24, 2):
            x, y = cab[i]
            sus.append([(x, y), (x, deck)])
        cv.hair(sus)
        R = C._Rib(cab, [1.2] * 25, [1.2] * 25)
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.3, 0, 1))
        dk = [(cx, deck - 2.5), (ex, deck - 2.5), (ex, deck + 1.5), (cx, deck + 1.5)]
        bu_form(cv, dk, lambda px, py: .2 + .5 * (py - deck + 2.5) / 4, 0., 1.5, 0, None, 1.)
        # the truss under the deck
        tr = []
        x = cx
        while sg * (ex - x) > 4:
            tr.append([(x, deck + 1.5), (x + sg * 3, deck + 5), (x + sg * 6, deck + 1.5)])
            x += sg * 6
        cv.hair(tr)
        _gothic_tower(cv, cx, base, tw, th)
        # the river line running out from under the arch
        for k in range(3):
            y = base + 2 + k * 2
            cv.obj([], 0)
            cv.hair([(bx + bw / 2 + sg * bw * .3, y), (bx + bw / 2 + sg * min(w / 2 - 8, bw / 2 + bh * (1.2 - .3 * k)), y)])
    return kk_svg(cv)


def plate(w, h, ctx):
    """News (section front): the Oregonian's old clock tower over the Willamette, the St Johns
    Bridge, the West Hills and Mt. Hood, in an arched vignette carried between the bridge's two
    gothic towers; the dedication cartouche at its foot. Easter egg: the clock stands at the
    edition's hour, 8:34."""
    ctx = ctx or {}
    date = ctx.get("date", "")
    seed = sum(map(ord, date)) + 7 * int(ctx.get("sheet", 0) or 0)

    def sc(x, y, ww, hh, mode):
        return tower_scene(x - 2, y - 2, ww + 4, hh + 4, mode, seed, date)
    return vg_plate(w, h, sc, shape="arch", form="vignette", seed=seed, arms=True, ragged=False,
                    frame=lambda *a: _bridge_frame(*a, seed))


# ==== BURIN KIT (begin) ==========================================================================
# The modelling pass (Nov 12, batch 7 v2). Tone is cut, never filled: every form is laid in lines at
# a fixed pitch that follow its surface, and each line swells from nothing in the light through
# 0.5 and 1 px to 1.5 px in the shadow (bu_cut), so the subject comes up light out of a dark,
# layered ground as in Dore, Bewick and Goltzius. Light falls from the upper left unless a form
# says otherwise. The same block is pasted into every batch-7 plate; edit it in one place.
#   bu_cut(cv, pl, tone)                a polyline cut as a swelling line, tone(x, y) in 0..1
#   bu_form(cv, poly, tone, ang, ...)   a shape, hatched along ang (bowed to follow the form),
#                                       cross-cut in its darkest part
#   bu_rib(cv, R, ...)                  a round member (_Rib): lines along it, lit on one side
#   bu_ball(cv, cx, cy, rx, ry, ...)    a sphere / ovoid in curved cuts
#   bu_sky / bu_cloud / bu_water / bu_tuft / bu_clump: sky, modelled cumulus, broken
#                                       reflections, foreground grass, foliage masses
#   bu_arms(x, y, w, h, seed)           Parker's arms (solar/arms.py) placed in a box
import math as _bm
import random as _br
from arms import arms as _bu_arms_markup

_BLX, _BLY, _BLZ = -.52, -.62, .59          # toward the light: upper left, a little in front


def bu_w(t, lo=.16):
    """Tone (0 paper .. 1 black) -> burin width: none, 0.5, 1 or 1.5 px."""
    if t < lo:
        return 0.
    if t < .43:
        return .5
    if t < .7:
        return 1.
    return 1.5


def _bu_rs(pl, step):
    out = [pl[0]]
    for (ax, ay), (bx, by) in zip(pl, pl[1:]):
        L = _bm.hypot(bx - ax, by - ay)
        k = int(L / step)
        for j in range(1, k + 1):
            t = j / (k + 1)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        out.append((bx, by))
    return out


def bu_cut(cv, pl, tone, lo=.16, step=1.4, cap=1.5, jit=.07):
    """Cut polyline pl as one swelling line: where tone(x, y) is light the line breaks off, then
    swells 0.5 -> 1 -> 1.5 px into the shadow (cap limits the widest cut). A small jitter staggers
    the swells from line to line, so a tone step never runs straight across the lay."""
    if len(pl) < 2:
        return
    pts = _bu_rs(pl, step)
    em = {.5: cv.hair, 1.: cv.line, 1.5: cv.heavy}
    cur, cw = [], 0.
    j = jit * _bm.sin(1.37 * pl[0][1] + .91 * pl[0][0]) if jit else 0.
    for p in pts:
        w = min(cap, bu_w(tone(p[0], p[1]) + j, lo))
        if w != cw:
            if cw and len(cur) > 1:
                em[cw](cur)
            cur = [cur[-1], p] if (cur and w and cw) else [p]
            cw = w
        else:
            cur.append(p)
    if cw and len(cur) > 1:
        em[cw](cur)


def bu_hatch(poly, ang, pitch=2., bow=0., phase=0.):
    """Parallel cuts across poly at ang (degrees), pitch apart, each bowed by up to bow px (scaled
    by its chord, so short cuts at the edge stay inside) so the lay of lines turns with the form."""
    out = []
    segs = _C.hatch_poly(poly, ang, pitch, phase)
    if not segs:
        return out
    a = _bm.radians(ang)
    nx, ny = -_bm.sin(a), _bm.cos(a)
    Lmax = max(_bm.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in segs) or 1.
    for (p, q) in segs:
        L = _bm.hypot(q[0] - p[0], q[1] - p[1])
        if not bow or L < 3:
            out.append([p, q])
            continue
        k = bow * (L / Lmax)
        n = max(2, int(L / 3))
        out.append([(p[0] + (q[0] - p[0]) * i / n + nx * k * 4 * (i / n) * (1 - i / n),
                     p[1] + (q[1] - p[1]) * i / n + ny * k * 4 * (i / n) * (1 - i / n)) for i in range(n + 1)])
    return out


def bu_form(cv, poly, tone, ang=45., pitch=2., bow=0., cross=None, outline=.5, lo=.16, cap=1.5,
            cross_at=.62, phase=0.):
    """A shape cut in tone: white body outlined, lines along ang bowed to the form, a second
    layer at cross (degrees) laid only where the tone passes cross_at."""
    cv.obj([poly], outline)
    for pl in bu_hatch(poly, ang, pitch, bow, phase):
        bu_cut(cv, pl, tone, lo, cap=cap)
    if cross is not None:
        t2 = lambda x, y: (tone(x, y) - cross_at) * 2.6 + .2
        for pl in bu_hatch(poly, cross, max(3., pitch * 1.5), bow * .5):
            bu_cut(cv, pl, t2, .25, cap=1.)


# ---- tone fields ------------------------------------------------------------------------------

def bu_lin(x0, y0, x1, y1, t0, t1):
    """A ramp from tone t0 at (x0, y0) to t1 at (x1, y1)."""
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1.
    return lambda x, y: t0 + (t1 - t0) * min(1., max(0., ((x - x0) * dx + (y - y0) * dy) / L2))


def bu_sph(cx, cy, rx, ry, base=.15, amp=.75, rim=.18, L=None):
    """Lambert shading of an ovoid lit from the upper left: highlight up-left, core shadow down-
    right, a little reflected light on the far rim."""
    lx, ly, lz = L or (_BLX, _BLY, _BLZ)

    def f(x, y):
        u, v = (x - cx) / rx, (y - cy) / ry
        r2 = u * u + v * v
        nz = _bm.sqrt(max(0., 1 - r2)) if r2 < 1 else 0.
        lam = max(0., u * lx + v * ly + nz * lz)
        t = base + amp * (1 - lam)
        if r2 > .72 and u * lx + v * ly < 0:
            t -= rim * (r2 - .72) / .28
        return t
    return f


def bu_radial(cx, cy, r, t0, t1, p=1.):
    """Light pooled round (cx, cy): t0 at the centre to t1 at r and beyond."""
    return lambda x, y: t0 + (t1 - t0) * min(1., (_bm.hypot(x - cx, y - cy) / r)) ** p


def bu_noise(seed, sc=24.):
    """Smooth value noise in -1..1 with feature size sc px."""
    rng = _br.Random(seed)
    tab = [rng.uniform(-1, 1) for _ in range(256)]
    perm = list(range(256))
    rng.shuffle(perm)

    def g(i, j):
        return tab[perm[(perm[i & 255] + j) & 255]]

    def f(x, y):
        x, y = x / sc, y / sc
        i, j = int(_bm.floor(x)), int(_bm.floor(y))
        fx, fy = x - i, y - j
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = g(i, j) + (g(i + 1, j) - g(i, j)) * fx
        b = g(i, j + 1) + (g(i + 1, j + 1) - g(i, j + 1)) * fx
        return a + (b - a) * fy
    return f


# ---- forms ------------------------------------------------------------------------------------

def bu_rib(cv, R, base=.2, amp=.7, pitch=1.5, lit=-1, outline=1., u0=0., u1=1., cross=False, shadow=True, lo=.16):
    """A round member (a _Rib) lit on its `lit` side (+1 = the +normal edge): lines along it at
    about pitch px, swelling into the core shadow with reflected light on the far edge, a 1.5 cut
    on the shadow edge."""
    if outline is not None:
        cv.obj([R.outline()], outline)
    wm = max(max(R.wl), max(R.wr))
    n = max(1, int(2 * wm / pitch))
    for k in range(n + 1):
        s = -1 + 2. * (k + .5) / (n + 1)
        th = _bm.asin(max(-1., min(1., s)))
        lam = max(0., _bm.cos(th - lit * .85))
        t = base + amp * (1 - lam)
        if s * lit < -.75:
            t -= .14
        tt = t
        for pl in R.contour(s, u0, u1, minw=pitch * .7):
            bu_cut(cv, pl, lambda x, y, tt=tt: tt, lo)
    if cross:
        u = u0
        step = 2.5 / R.L
        while u < u1:
            a, b = R.at(u, -lit * .25), R.at(u, -lit * .98)
            cv.hair([a, b])
            u += step
    if shadow:
        cv.heavy(R.contour(-lit * .93, u0, u1))


def bu_ball(cv, cx, cy, rx, ry=None, base=.12, amp=.78, pitch=1.5, ang=None, outline=1., n=None, glint=True):
    """A sphere or ovoid: curved cuts that run round it parallel to the terminator, swelling into
    the shadow, a lit crown and a white glint."""
    ry = ry or rx
    poly = _C._ell_pts(cx, cy, rx, ry, n or max(16, int((rx + ry) * 2)))[:-1]
    tone = bu_sph(cx, cy, rx, ry, base, amp)
    a = 45. if ang is None else ang
    bu_form(cv, poly, tone, a, pitch, max(1., min(rx, ry) * .5), None, outline)
    return poly


def bu_slab(cv, x0, y0, x1, y1, base=.25, amp=.45, along="v", pitch=2., outline=1., lit=-1, edge=True):
    """A block lit from the side: cuts along it that swell across into its shadowed side."""
    poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if along == "v":
        tone = bu_lin(x0 if lit < 0 else x1, 0, x1 if lit < 0 else x0, 0, base, base + amp)
        bu_form(cv, poly, tone, 90., pitch, 0, None, outline)
        if edge and x1 - x0 > 3:
            cv.heavy([(x1 - .8 if lit < 0 else x0 + .8, y0 + .4), (x1 - .8 if lit < 0 else x0 + .8, y1 - .4)])
    else:
        tone = bu_lin(0, y0, 0, y1, base, base + amp)
        bu_form(cv, poly, tone, 0., pitch, 0, None, outline)
        if edge and y1 - y0 > 3:
            cv.heavy([(x0 + .4, y1 - .8), (x1 - .4, y1 - .8)])
    return poly


# ---- sky, clouds, water, ground ----------------------------------------------------------------

def bu_sky(cv, X, Y, W, H, tone=None, glow=None, seed=0, pitch=2.):
    """Sky in horizontal burin lines on the device grid, dark high up and opening toward the
    horizon (or round glow=(x, y, r), the sun), with a slow noise so it never reads as ruled."""
    nz = bu_noise(seed + 41, 70.)
    if tone is None:
        tone = lambda x, y: .62 - .5 * (y - Y) / max(1., H)
    cv.obj([[(X, Y), (X + W, Y), (X + W, Y + H), (X, Y + H)]], 0)
    y = _bm.floor(Y * 2) / 2 + .25
    while y < Y + H:
        def t(x, yy, y=y):
            v = tone(x, y) + .1 * nz(x, y)
            if glow:
                gx, gy, gr = glow
                d = _bm.hypot(x - gx, (y - gy) * 1.3) / gr
                if d < 1:
                    v -= (1 - d) ** 1.5 * .42
            return v
        bu_cut(cv, [(X, y), (X + W, y)], t, .17, 2.)
        f = (y - Y) / max(1., H)
        y += pitch if f < .7 else pitch + 1.


def bu_cloud(cv, x0, x1, yb, hgt, rng, lit=(-1, -1), base=.08, amp=.7, dark=1.):
    """A modelled cumulus: heaped round bumps, each lit on its upper-left and cut in arcs that run
    round it into a shadowed lower right, over a flat, dark, line-cut base."""
    n = max(3, int((x1 - x0) / (hgt * .75)))
    bumps = []
    for i in range(n):
        t = (i + .5) / n
        r = hgt * (.32 + .55 * _bm.sin(_bm.pi * t) ** .7) * rng.uniform(.8, 1.12)
        bumps.append((x0 + (x1 - x0) * t + rng.uniform(-2, 2), yb - r * .72, r))
    # second tier of bumps on top of the big ones
    for bx, by, br in list(bumps):
        if br > hgt * .55 and rng.random() < .8:
            bumps.append((bx + rng.uniform(-.4, .4) * br, by - br * .55, br * rng.uniform(.45, .6)))
    N = max(8, int((x1 - x0) / 1.5))
    top = []
    for k in range(N + 1):
        x = x0 + (x1 - x0) * k / N
        y = yb
        for bx, by, br in bumps:
            dx = x - bx
            if abs(dx) < br:
                y = min(y, by - _bm.sqrt(br * br - dx * dx))
        top.append((x, min(y, yb - .5)))
    bot = [(x1 - (x1 - x0) * k / 16, yb + hgt * .06 * _bm.sin(_bm.pi * k / 16)) for k in range(17)]
    poly = top + bot
    # each bump its own white form, the higher (farther) ones first so the nearer cut over them;
    # fine arcs run round its shadowed right and underside, the lit crown left as paper
    for bx, by, br in sorted(bumps, key=lambda b: b[1]):
        circ = [(bx + br * _bm.cos(a), min(yb, by + br * _bm.sin(a))) for a in [2 * _bm.pi * i / 36 for i in range(36)]]
        cv.obj([circ], .5)
        tone = bu_sph(bx, by, br, br, base * dark + .1, amp * dark * .8, .25)
        r = br - 1.2
        k = 0
        while r > br * .3 and k < 6:
            arc = [(bx + r * _bm.cos(a), by + r * _bm.sin(a)) for a in [_bm.pi * (-.8 + 1.35 * i / 20) for i in range(21)]]
            arc = [p for p in arc if p[1] < yb - .8]
            if len(arc) > 1:
                bu_cut(cv, arc, tone, .24, cap=1.)
            r -= 1.6 if k < 3 else 2.
            k += 1
    # the flat underside in front of them all: horizontal cuts, darkest at the base
    yc = yb - hgt * .38
    under = [(px, max(py, yc)) for px, py in top] + bot
    cv.obj([under], 0)
    d = 1.
    while d < hgt * .38:
        y = yb - d
        xs = [p[0] for p in top if p[1] < y - .5]
        if len(xs) > 1:
            tt = (.62 - d / (hgt * .38) * .5) * dark
            (cv.line if tt > .43 else cv.hair)([(xs[0] + 1, y), (xs[-1] - 1, y)])
        d += 1.5 if d < 4 else 2.
    cv.line(bot)
    return poly


def bu_water(cv, X, Y, W, H, refl=None, seed=0, base=None, pitch=2., spark=None):
    """Water in horizontal cuts broken into ripples: short dashes with gaps that open toward the
    viewer, tone from the sky's own ramp plus the broken reflection refl(x, y) of what stands on
    the bank (a tone 0..1 or None), and a glitter path (spark=(x, width)) where the light lies."""
    rng = _br.Random(seed * 31 + 7)
    nz = bu_noise(seed + 5, 18.)
    if base is None:
        base = lambda x, y: .3 + .25 * (y - Y) / max(1., H)
    cv.obj([[(X, Y), (X + W, Y), (X + W, Y + H), (X, Y + H)]], 0)
    y = _bm.floor(Y * 2) / 2 + .25
    while y < Y + H:
        f = (y - Y) / max(1., H)
        x = X - rng.uniform(0, 6)
        while x < X + W:
            L = rng.uniform(4, 16) * (1 + 2.5 * f)
            g = rng.uniform(.8, 2.5) * (1 + 1.5 * f)
            wob = 2.5 * _bm.sin(y * .7 + seed)

            def t(xx, yy, y=y, wob=wob):
                v = base(xx, y) + .12 * nz(xx, y * 3)
                if refl:
                    r = refl(xx + wob, y)
                    if r is not None:
                        v = .25 * v + .75 * r
                if spark:
                    sx, sw = spark
                    if abs(xx - sx) < sw * (1 + f):
                        v -= .45 * (1 - abs(xx - sx) / (sw * (1 + f)))
                return v
            bu_cut(cv, [(max(X, x), y), (min(X + W, x + L), y)], t, .18, 2.)
            x += L + g
        y += pitch if f < .55 else pitch + 1.


def bu_tuft(cv, x, yb, hgt, rng, n=7, lean=0., dark=1.):
    """A foreground tuft of grass: blades as long tapering cuts, heavy at the root, curving out."""
    for i in range(n):
        a = lean + rng.uniform(-.55, .55)
        L = hgt * rng.uniform(.5, 1.)
        bx = x + rng.uniform(-hgt * .18, hgt * .18)
        c = rng.uniform(-.35, .35) * L
        pts = [(bx + _bm.sin(a) * L * t + c * t * t, yb - _bm.cos(a) * L * t) for t in [k / 6 for k in range(7)]]
        cv.obj([], 0)
        if dark > .6:
            cv.heavy(pts[:3])
        cv.line(pts[1:5])
        cv.hair(pts[3:])


def bu_clump(cv, cx, cy, rx, ry, rng, leaf=3., base=.3, amp=.6, pitch=1.5, outline=.5):
    """A mass of foliage: small scalloped bumps heaped over an ovoid, each cut in short curved
    strokes; the mass lit up-left and darkening into its lower right and its hollows."""
    tone0 = bu_sph(cx, cy, rx, ry, base, amp, .1)
    pts = []
    n = 56
    for i in range(n):
        a = 2 * _bm.pi * i / n
        k = 1 + .08 * _bm.sin(a * 7 + rng.random()) + .05 * rng.uniform(-1, 1)
        pts.append((cx + rx * k * _bm.cos(a), cy + ry * k * _bm.sin(a)))
    # scalloped edge
    sc = []
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        dx, dy = mx - cx, my - cy
        L = _bm.hypot(dx, dy) or 1.
        sc += [p, (mx + dx / L * leaf * .5, my + dy / L * leaf * .5)]
    cv.obj([sc], outline)
    # leaf strokes: little comma cuts laid in rows following the mass
    y = cy - ry
    row = 0
    while y < cy + ry:
        x = cx - rx + (row % 2) * leaf * .7
        while x < cx + rx:
            u, v = (x - cx) / rx, (y - cy) / ry
            if u * u + v * v < .95:
                t = tone0(x, y) + .12 * rng.uniform(-1, 1)
                w = bu_w(t, .2)
                if w:
                    pl = [(x - leaf * .55, y - leaf * .15), (x, y + leaf * .25), (x + leaf * .55, y - leaf * .1)]
                    {.5: cv.hair, 1.: cv.line, 1.5: cv.heavy}[w](pl)
            x += leaf * 1.4
        y += pitch + .5
        row += 1
    return sc


def bu_blade(cv, x, yb, L, ang, bend, wd, shade=1, outline=.5):
    """One reed or grass blade: a long tapering leaf from (x, yb) along ang (0 = straight up),
    curving by bend, its shadow half cut in a line that swells to the root."""
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((x + _bm.sin(ang) * L * t + bend * L * t * t, yb - _bm.cos(ang) * L * t))
    ws = [max(.35, wd * (1 - t) ** .8) for t in [i / 8 for i in range(9)]]
    R = _C._Rib(pts, ws, ws)
    cv.obj([R.outline()], outline)
    if wd > 1.1:
        cv.hair(R.contour(shade * .35, 0., .8))
        if wd > 1.8:
            cv.line(R.contour(shade * .7, 0., .45))
    return pts


def bu_reeds(cv, x0, x1, yb, hmax, rng, grow=1, n=None, heads=.35, wd=1.4):
    """A reed bed from x0 to x1 standing on yb, tallest at the x0 end when grow > 0 (x1 when < 0):
    reeds of uneven height leaning and curving, blades crossing, cattails modelled round, and a
    dark tussock of short blades at the foot."""
    n = n or max(6, int(abs(x1 - x0) / 3.2))
    items = []
    for i in range(n):
        t = rng.random()
        x = x0 + (x1 - x0) * t
        f = (1 - t) if grow > 0 else t
        hh = hmax * (.3 + .7 * f ** .8) * rng.uniform(.6, 1.05)
        items.append((rng.random(), x, hh))
    items.sort()
    for _, x, hh in items:
        lean = rng.uniform(-.18, .18)
        bend = rng.uniform(-.12, .12)
        pts = bu_blade(cv, x, yb, hh, lean, bend, wd * rng.uniform(.8, 1.2), 1 if lean > 0 else -1)
        if rng.random() < heads and hh > hmax * .4:
            hx, hy = pts[6]
            hr = max(1.3, wd * 1.05)
            bu_ball(cv, hx, hy, hr, max(3., hh * .09), .15, .75, 1.5, 90., .5, 16)
            cv.obj([], 0)
            cv.hair([pts[6], pts[8]])
        else:
            for sg in (-1, 1):
                if rng.random() < .55:
                    bu_blade(cv, x + sg * .5, yb, hh * rng.uniform(.4, .75), lean + sg * rng.uniform(.25, .6), sg * rng.uniform(0, .25), wd * .9, -sg)
    # the tussock: short dark blades in a mass at the foot
    k = int(abs(x1 - x0) / 2.2)
    for i in range(k):
        x = x0 + (x1 - x0) * rng.random()
        bu_blade(cv, x, yb + 1, hmax * rng.uniform(.08, .2), rng.uniform(-.7, .7), rng.uniform(-.2, .2), wd * .8, 1)


def bu_hood(cv, hx, yh, H, seed=7, skirt=True, outline=.5):
    """Mt. Hood standing on the horizon yh, its summit H above it at x = hx: the west face lit in
    snow and touched only by its gullies, the east face cut down the fall line and darkening to
    its foot, the timbered skirt below the snow line. Returns its outline."""
    L = [(hx - H * 1.45, yh), (hx - H * 1.0, yh - H * .22), (hx - H * .62, yh - H * .45),
         (hx - H * .34, yh - H * .68), (hx - H * .18, yh - H * .83), (hx - H * .07, yh - H * .94), (hx, yh - H)]
    R = [(hx + H * .05, yh - H * .97), (hx + H * .12, yh - H * .9), (hx + H * .2, yh - H * .8),
         (hx + H * .28, yh - H * .74), (hx + H * .45, yh - H * .58), (hx + H * .8, yh - H * .32),
         (hx + H * 1.2, yh - H * .12), (hx + H * 1.6, yh)]

    def spl(P):
        out = []
        for i in range(len(P) - 1):
            p0, p1, p2 = P[max(0, i - 1)], P[i], P[i + 1]
            p3 = P[min(len(P) - 1, i + 2)]
            for k in range(3):
                t = k / 3
                t2, t3 = t * t, t * t * t
                out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
        out.append(P[-1])
        return out
    prof = spl(L) + spl(R)[1:]
    hpk = yh - H
    poly = prof + [(hx + H * 1.6, yh + 2), (hx - H * 1.45, yh + 2)]
    cv.obj([poly], outline)
    ins = kk_inside(poly)
    wedge = [(hx, hpk), (hx + H * .02, hpk + H * .3), (hx - H * .05, yh - H * .3), (hx + H * .1, yh),
             (hx + H * 1.7, yh), (hx + H * 1.7, hpk - 2)]
    for pl in bu_hatch(wedge, 64., 1.5, 1.):
        pl = [p for p in pl if ins(p[0], p[1])]
        if len(pl) > 1:
            bu_cut(cv, pl, lambda px, py: .3 + .45 * (py - hpk) / H + .12 * (px - hx) / H)
    rng = _br.Random(seed)
    for k in range(9):
        t = (k + 1) / 10
        x0, y0 = hx - H * .05 * t, hpk + H * (.1 + .1 * t)
        gx = hx - H * (.25 + 1.05 * t)
        g = [(x0 + (gx - x0) * u + _bm.sin(u * 5 + k) * .8, y0 + (yh - H * (.2 + .1 * rng.random()) - y0) * u ** .9)
             for u in [i / 12 for i in range(13)]]
        g = [p for p in g if ins(p[0], p[1] - 1)]
        if len(g) > 1:
            bu_cut(cv, g, lambda px, py: .1 + .5 * (py - hpk) / H)
    if skirt:
        sk = [(hx - H * 1.5, yh), (hx - H * .9, yh - H * .25), (hx - H * .5, yh - H * .3), (hx, yh - H * .36),
              (hx + H * .5, yh - H * .33), (hx + H * 1.0, yh - H * .2), (hx + H * 1.65, yh),
              (hx + H * 1.65, yh + 2), (hx - H * 1.5, yh + 2)]
        bu_form(cv, sk, lambda px, py: .4 + .3 * (px - hx + H) / (2.6 * H) + .2 * (py - yh + H * .3) / (H * .3), 30., 1.5, 1., None, 0)
    return poly


def bu_arms(x, y, w, h, seed=0):
    """Parker's arms (Somaster: Or, a castle between five fleurs-de-lis sable) set in the box
    (x, y, w, h); under about 100 px wide it is the shield alone. Placed on whole pixels so the
    Or stipple stays on the device grid."""
    xi, yi = int(round(x)), int(round(y))
    return f'<g transform="translate({xi},{yi})">{_bu_arms_markup(int(round(w)), int(round(h)), seed)}</g>'


def bu_cartouche(cx, cy, r, seed=0):
    """The section-front dedication cartouche: the arms in a small beaded oval, a modelled leaf
    scrolling out either side."""
    cv = _C.Canvas()
    for sg in (-1, 1):
        for j, (dy, da, L, W) in enumerate(((.45, -.35, 1.25, .3), (-.1, .1, 1.05, .26), (-.6, .55, .8, .22))):
            vg_leaf(cv, cx + sg * r * .82, cy + r * dy, (_PI if sg < 0 else 0) + sg * da, r * L, r * W, sg * (.35 if j != 1 else -.3), sg if j % 2 else -sg, r * L > 14)
    s = kk_svg(cv)
    ring, _, _ = kk_ring(cx, cy, r, r * 1.08, 1.)
    bg = f'<path d="{_kk_ell_d(cx, cy, r + .5, r * 1.08 + .5, 40)}" fill="#fff" stroke="none"/>'
    aw = r * 1.5
    return s + bg + bu_arms(cx - aw / 2, cy - r * .98, aw, r * 1.96, seed) + ring
# ==== BURIN KIT (end) ============================================================================


# ==== FLAT STROKES (batch 7 fix pass) ===========================================================
# The canvas writes its cuts in quarter- or half-px integers under transform="scale(...)", so the
# literal stroke-width was 2, 3, 4 or 6 though it renders 0.5, 1 or 1.5 px. bu_flat rescales those
# paths' data (M/m/l/z only) to px and drops the transform, so every stroke-width in the plate
# reads as what the burin cuts: 0.5, 1 or 1.5.
import re as _bre
_BU_SCALED = _bre.compile(r'<path transform="scale\(([\d.]+)\)" d="([^"]*)"([^>]*?) stroke-width="([\d.]+)"')
_BU_NUM = _bre.compile(r'-?(?:\d+\.?\d*|\.\d+)')


def _bu_fmt(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return "0" if s in ("", "-0") else s


def bu_flat(svg):
    def sub(m):
        k = float(m.group(1))
        d = m.group(2)
        if _bre.search(r"[^MmLlHhVvZz\d\s,.\-]", d):
            return m.group(0)
        out, last, prev = [], 0, ""
        for n in _BU_NUM.finditer(d):
            sep = d[last:n.start()]
            v = _bu_fmt(float(n.group()) * k)
            # "1.5 .5" may be written "1.5.5": a number already holding a point ends at the next
            if sep == " " and v[0] == "." and "." in prev:
                sep = ""
            out.append(sep + v)
            prev = v
            last = n.end()
        out.append(d[last:])
        return f'<path d="{"".join(out)}"{m.group(3)} stroke-width="{_bu_fmt(float(m.group(4)) * k)}"'
    return _BU_SCALED.sub(sub, svg)


_bu_plate_raw = plate


def plate(w, h, ctx):
    return bu_flat(_bu_plate_raw(w, h, ctx))
