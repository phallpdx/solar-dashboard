"""News front plate: a library globe turned to the Americas (Portland starred) set in a glory of
rays, standing on a stack of folded newspapers, over the Willamette with the St Johns Bridge, the
West Hills, a broadcast mast sending its waves and Mt Hood. Framed in the house Codex acanthus.
Easter egg: a pair of crossed drumsticks lying on the top newspaper."""
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
# ------------------------------------------------------------------------------------------------

def _medallion_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.6, 120)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    inner = _ell(cx, cy, rx - 4, ry - 4, 64)
    o.append(_scene(cx - rx, cy - ry, rx * 2, ry * 2, seed, _d(inner, True, 0), lod=0))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.6)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, seed, inner_d, lod=1 if b * 2 < 150 else 2))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _letter_ribbon(centre, h, text):
    xs = [p[0] for p in centre]
    ys = [p[1] for p in centre]

    def yat(x):
        if x <= xs[0]:
            return ys[0]
        for i in range(1, len(xs)):
            if x <= xs[i]:
                t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
                return ys[i - 1] + (ys[i] - ys[i - 1]) * t
        return ys[-1]
    cx = (xs[0] + xs[-1]) / 2
    ch = min(8., h * .5)
    polys, _ = _text(text, cx, 0, ch, 2.2, lambda x: yat(x) + h * .34 - ch / 2)
    return f'<path d="{_pl_d(polys)}" stroke="#000" stroke-width="1.5" fill="none"/>'


def _tablet(tx, ty, tw, th, text):
    o = [f'<path d="M{_n(tx + 3)},{_n(ty + 3)}h{_n(tw - 5)}v{_n(th - 5)}h{_n(-(tw - 5))}z" fill="{C.pat("L")}" stroke="none"/>']
    ch = min(9., th * .55)
    polys, width = _text(text, tx + tw / 2, ty + (th - ch) / 2 + .5, ch, 1.8)
    pad = 5
    o.append(f'<path d="M{_n(tx + tw / 2 - width / 2 - pad)},{_n(ty + 3)}h{_n(width + 2 * pad)}v{_n(th - 5)}h{_n(-(width + 2 * pad))}z" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_pl_d(polys)}" stroke="#000" stroke-width="1" fill="none"/>')
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .02, 8.)
    px0, py0 = 4., top_free
    pw = w - 8
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # everything below the panel sits on the cut-away ground too: no bare paper at the sides
    o.append(C.dark_ground((0, py0 + ph - 2, w, h - (py0 + ph - 2)), "G"))
    o.append(f'<path d="M{_n(px0 - 3)},{_n(py0 - 3)}h{_n(pw + 6)}v{_n(ph + 6)}h{_n(-pw - 6)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=9, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, seed, inner_d, lod=2))
    o.append(C.palmette(cx, cy - ch / 2 + 6, min(ch * .16 + top_free, 50), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .48, cw * 1.3, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_letter_ribbon(centre, bh, "THE NEWS"))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, "PORTLAND · THE NATION · THE WORLD"))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _medallion_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
