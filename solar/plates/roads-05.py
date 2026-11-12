"""roads-05 -- "Wildfires in the region" (NIFC list: Grasshopper Fire, Wasco County, 68 mi away...).

The plate: a fire season seen from a Mt. Hood lookout. Inside a carved cartouche, Mt. Hood stands
snow-white on the left; behind the far ridge the Grasshopper Fire burns as a line of kranok flame
tongues (the house acanthus finger, turned up and set alight), its smoke column boiling up past a
veiled sun; a stand of black firs on the mid ridge, a burned snag and a fire lookout on the near
knoll. Easter egg: a Sauvie Island heron beats away from the smoke, and Parker's dog sits at the
foot of the lookout. The pedestal tablet carries the day's fires as a row of flames sized by acreage.
Short plates: a scroll frieze round a medallion of flames under Hood. Medium: cartouche + volutes.
"""
import sys
import math
import random
import re
import engraving_codex as C

PI = math.pi
_n = C._n


# ------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------

def _circ(cx, cy, r, n=None):
    n = n or max(16, int(r * 1.6))
    return [(cx + r * math.cos(2 * PI * i / n), cy + r * math.sin(2 * PI * i / n)) for i in range(n)]


def _arc(cx, cy, r, a0, a1, n=None):
    n = n or max(4, int(abs(a1 - a0) * r / 2))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _solid(cv, poly, ang=0.):
    """black mass: 1 px lines laid 0.8 apart"""
    cv.line(C.hatch_poly(poly, ang, .8))


def _ridge(x0, x1, base, amp, rng, n=40, f=(3., 7., 13.)):
    ph = [rng.uniform(0, 6.28) for _ in f]
    pts = []
    for i in range(n + 1):
        t = i / n
        y = base
        for k, (fr, p) in enumerate(zip(f, ph)):
            y -= amp / (k + 1) * math.sin(t * fr + p)
        pts.append((x0 + (x1 - x0) * t, y))
    return pts


def _ridge_y(pts, x):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if ax <= x <= bx:
            return ay + (by - ay) * (x - ax) / max(1e-6, bx - ax)
    return pts[-1][1]


# ------------------------------------------------------------------------------------------
# motifs
# ------------------------------------------------------------------------------------------

def _flame(cv, x, y, h, rng, lean=0., n=3):
    """a kranok flame: a fan of swept acanthus fingers rising and curling, the house finger set alight"""
    order = sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2))
    for i in order:
        off = i - (n - 1) / 2
        side = 1 if off > 0 else (-1 if off < 0 else rng.choice((-1, 1)))
        ln = h * (1 - .22 * abs(off)) * rng.uniform(.9, 1.05)
        a = -PI / 2 + lean + off * .32
        b = side * .45 * rng.uniform(.8, 1.2)
        C._finger(cv, x + off * h * .08, y, a, ln, ln * .13, b, side * rng.uniform(3.8, 5.), .9)


def _fir(cv, x, base, h, burnt=False):
    """a black fir silhouette: tiered drooping boughs"""
    w = h * .36
    pts = [(x, base - h)]
    tiers = 6
    for i in range(1, tiers + 1):
        t = i / tiers
        yy = base - h + h * .9 * t
        ww = w * (.18 + .82 * t) / 2
        pts.append((x + ww, yy + h * .02))
        if i < tiers:
            pts.append((x + ww * .45, yy - h * .02))
    right = pts[1:]
    left = [(2 * x - px, py) for px, py in right[::-1]]
    poly = [pts[0]] + right + [(x + w * .05, base - h * .1), (x + w * .05, base), (x - w * .05, base),
                               (x - w * .05, base - h * .1)] + left
    cv.obj([poly], 1.)
    _solid(cv, poly, 90 if burnt else 0)
    return poly


def _snag(cv, x, base, h):
    """a burned dead tree: forked trunk and broken limbs, black with a white highlight edge"""
    tw = h * .045
    trunk = [(x - tw, base), (x - tw * .5, base - h * .6), (x - tw * .2, base - h), (x + tw * .2, base - h * .97),
             (x + tw * .5, base - h * .6), (x + tw, base)]
    cv.obj([trunk], 1.)
    _solid(cv, trunk, 90)
    for (fy, ln, a) in ((.35, .28, -2.5), (.5, .22, -.6), (.66, .2, -2.7), (.78, .14, -.5), (.88, .1, -2.4)):
        sx, sy = x, base - h * fy
        ex, ey = sx + math.cos(a) * h * ln, sy + math.sin(a) * h * ln
        cv.heavy([(sx, sy), ((sx + ex) / 2, (sy + ey) / 2 + 1), (ex, ey)])
        cv.line([(ex, ey), (ex + math.cos(a - .9) * h * .05, ey + math.sin(a - .9) * h * .05)])


def _lookout(cv, x, base, h):
    """a fire lookout: splayed braced legs, a glazed cab with a catwalk, a hipped roof and finial"""
    cw = h * .34
    cab_y = base - h * .78
    ch = h * .17
    tl, tr = x - cw * .42, x + cw * .42
    bl, br = x - cw * .8, x + cw * .8
    # legs and bracing (black, drawn first so the cab covers them)
    cv.obj([], 0)
    cv.heavy([(bl, base), (tl, cab_y)])
    cv.heavy([(br, base), (tr, cab_y)])
    lv = 4
    for i in range(lv):
        t0, t1 = i / lv, (i + 1) / lv
        y0, y1 = base - (base - cab_y) * t0, base - (base - cab_y) * t1
        l0, r0 = bl + (tl - bl) * t0, br + (tr - br) * t0
        l1, r1 = bl + (tl - bl) * t1, br + (tr - br) * t1
        cv.line([(l0, y0), (r1, y1)])
        cv.line([(r0, y0), (l1, y1)])
        cv.hair([(l1, y1), (r1, y1)])
    # stair zig-zag
    for i in range(5):
        t = i / 5
        y0 = base - (base - cab_y) * t
        y1 = base - (base - cab_y) * (t + .2)
        cv.hair([(x - cw * .1, y0), (x + cw * .1, y1)])
    # catwalk
    walk = [(x - cw * .62, cab_y), (x + cw * .62, cab_y), (x + cw * .62, cab_y + 2), (x - cw * .62, cab_y + 2)]
    cv.obj([walk], 1.)
    _solid(cv, walk)
    cv.hair([(x - cw * .62, cab_y - ch * .35), (x + cw * .62, cab_y - ch * .35)])
    for i in range(7):
        xx = x - cw * .62 + cw * 1.24 * i / 6
        cv.hair([(xx, cab_y), (xx, cab_y - ch * .35)])
    # cab with windows
    cab = [(x - cw * .5, cab_y), (x + cw * .5, cab_y), (x + cw * .5, cab_y - ch), (x - cw * .5, cab_y - ch)]
    cv.obj([cab], 1.)
    cv.hair(C.hatch_poly(cab, 0, 1.5))
    for i in range(4):
        wx = x - cw * .42 + cw * .84 * i / 3.0
        win = [(wx - cw * .08, cab_y - ch * .82), (wx + cw * .08, cab_y - ch * .82),
               (wx + cw * .08, cab_y - ch * .38), (wx - cw * .08, cab_y - ch * .38)]
        cv.obj([win], .5)
    # roof
    roof = [(x - cw * .66, cab_y - ch), (x + cw * .66, cab_y - ch), (x + cw * .08, cab_y - ch - h * .12),
            (x - cw * .08, cab_y - ch - h * .12)]
    cv.obj([roof], 1.)
    cv.hair(C.hatch_poly([roof[0], roof[1], roof[2], roof[3]], -70, 1.5))
    cv.line([(x, cab_y - ch - h * .12), (x, cab_y - ch - h * .17)])
    return cab_y


def _dog(cv, x, base, s, face=-1):
    """Parker's dog, sitting, seen in profile: the Easter egg at the foot of the lookout"""
    f = face

    def P(px, py):
        return (x + f * px * s, base - py * s)
    body = [P(0, 0), P(4.2, 0), P(4.8, 1.5), P(4.4, 4.2), P(3.6, 6.3), P(4.2, 7.6), P(5.6, 7.9), P(6.4, 7.4),
            P(6.1, 8.4), P(5.1, 9.2), P(3.5, 9.3), P(2.6, 8.3), P(2.3, 6.4), P(.8, 4.4), P(-.2, 2.2), P(-1.6, 1.4),
            P(-2.3, 2.2), P(-1.4, .4)]
    cv.obj([body], 1.)
    _solid(cv, body)
    cv.obj([[P(2.9, 9.1), P(3.3, 10.6), P(3.9, 9.2)]], .5)
    _solid(cv, [P(2.9, 9.1), P(3.3, 10.6), P(3.9, 9.2)])


def _heron(cv, x, y, s, face=-1):
    """great blue heron in flight: neck folded back, legs trailing, wings arched -- off Sauvie Island"""
    f = face

    def P(px, py):
        return (x + f * px * s, y + py * s)
    body = [P(-6, 0), P(-2, -1.4), P(3, -1.2), P(5, -2.4), P(6.4, -2.6), P(9.4, -2.0), P(6.6, -1.6),
            P(5.8, -.6), P(4.2, .6), P(0, 1.2), P(-5, .8)]
    wing_up = [P(-2.6, -.8), P(-6, -6), P(-10, -9.6), P(-6.4, -9.2), P(-2, -6.4), P(1.6, -1.2)]
    wing_dn = [P(-1.6, .4), P(-3.6, 4.4), P(-7.8, 6.2), P(-4.2, 6.6), P(.6, 3.2), P(1.8, .8)]
    cv.obj([wing_dn], .5)
    cv.hair(C.hatch_poly(wing_dn, 30, 1.5))
    cv.obj([body], 1.)
    cv.hair([P(-5, .2), P(0, .5), P(4, -.2)])
    cv.obj([wing_up], 1.)
    cv.hair(C.hatch_poly(wing_up, -50, 1.5))
    cv.line([P(-6, .3), P(-12.5, 1.6)])
    cv.line([P(-6, .6), P(-12.4, 2.2)])


def _billow(cv, cx, cy, r, dark=0., rot=0.):
    """single billow (used by the small medallion)"""
    _plume(cv, [(cy, cx, r, dark, rot)])


def _plume(cv, bl):
    """a smoke mass from billows (cy, cx, r, dark, rot): one pass lays the silhouette, a second pass
    lays each lobe slightly inside it with no outline, so only the outer scallops are cut; inside,
    each lobe is turned by arcs on its shadowed lower right and its own lower rim (light upper left)"""
    for cy, cx, r, dark, rot in bl:
        cv.obj([_circ(cx, cy, r)], 1.)
    for cy, cx, r, dark, rot in bl:
        cv.obj([_circ(cx, cy, r - 1.2)], 0)
        body = _circ(cx + r * .1, cy + r * .2, r * .85)
        cv.hair(C.hatch_poly(body, 0, 3 if dark < .4 else 2, cy % 3))
        mid = PI * .3 + rot
        cv.line(_arc(cx, cy, r - 1.2, mid - 1.1, mid + 1.3))
        rr = r - 3
        lim = r * (.55 - .35 * dark)
        while rr > lim:
            f = (rr - lim) / max(1e-6, r - 3 - lim)
            span = (.5 + .9 * dark) * (.35 + .65 * f)
            cv.hair(_arc(cx, cy, rr, mid - span, mid + span * (1.1 + .3 * dark)))
            rr -= 1.5


# ------------------------------------------------------------------------------------------
# the vignette: Mt. Hood, the burning ridge, the smoke column, the lookout
# ------------------------------------------------------------------------------------------

def _hood_fns(X, Y, pu=.4, L=.42, R=.46, vpk=.12, vb=.66):
    def top(u):
        d = (u - pu) / (L if u < pu else R)
        if abs(d) >= 1:
            return Y(vb)
        e = (1 - abs(d)) ** 1.6
        bump = .035 * math.exp(-((d + .3) / .07) ** 2) + .02 * math.exp(-((d - .45) / .06) ** 2)
        return Y(vb - (vb - vpk) * (e + bump * (1 - abs(d))))
    return top


def _scene(x, y, w, h, clip_d, seed, cid, detail=1.):
    rng = random.Random(seed)
    cv = C.Canvas()
    X = lambda u: x + w * u
    Y = lambda v: y + h * v
    S = min(w, h * 1.9)            # a size unit
    hu = lambda u: (u - x) / w      # inverse of X

    # sky: fine horizontal rules, denser toward the zenith
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([sky], 0)
    cv.hair(C.hatch_poly([(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, Y(.3)), (x - 2, Y(.3))], 0, 2, .3))
    cv.hair(C.hatch_poly([(x - 2, Y(.3)), (x + w + 2, Y(.3)), (x + w + 2, y + h + 2), (x - 2, y + h + 2)], 0, 3, .3))

    # the veiled sun, half lost in the smoke; its place shifts a little with the date
    su, sv = .66 + rng.uniform(-.02, .02), .15 + rng.uniform(-.02, .02)
    sr = h * .08
    cv.obj([_circ(X(su), Y(sv), sr)], 1.)
    cv.hair(C.hatch_poly(_circ(X(su), Y(sv), sr - 1), 0, 3, Y(sv) % 3))
    rays = []
    for i in range(24):
        aa = 2 * PI * i / 24
        r0, r1 = sr + 2.5, sr + (6 if i % 2 else 11)
        rays.append([(X(su) + r0 * math.cos(aa), Y(sv) + r0 * math.sin(aa)), (X(su) + r1 * math.cos(aa), Y(sv) + r1 * math.sin(aa))])
    cv.hair(rays)

    # Mt. Hood: concave flanks rising to the pointed summit, a shoulder on the west ridge
    pu, vpk, vb = .4, .17, .7
    top = _hood_fns(X, Y, pu, .5, .56, vpk, vb)
    us = [-.06 + 1.0 * i / 120 for i in range(121)]
    prof = [(X(u), top(u)) for u in us]
    hood = prof + [(X(.94), Y(vb + .05)), (X(-.06), Y(vb + .05))]
    cv.obj([hood], 1.)
    # the shadowed east face, ruled along the fall line
    ridge = [(X(pu + .006 * t + .03 * t * t), Y(vpk + (vb - vpk) * t)) for t in [i / 20 for i in range(21)]]
    east = ridge + [(px, py) for px, py in prof if px > X(pu)][::-1][:] + []
    east = ridge + [p for p in prof[::-1] if p[0] > ridge[-1][0]] + [(X(.94), Y(vb + .05))][:0]
    east = [p for p in prof if p[0] >= X(pu)] + ridge[::-1]
    cv.hair(C.hatch_poly(east, 58, 1.5))
    cv.hair(C.hatch_poly([p for p in east if p[1] > Y(vpk + .18)] or east, -30, 3))
    cv.line(ridge)
    west = [p for p in prof if p[0] <= X(pu)] + ridge
    cv.hair(C.hatch_poly(west, -62, 3, inset=0))
    # rock bands and cleavers breaking the snow near the summit
    for (u0, v0, ln) in ((.37, .2, .05), (.43, .22, .06), (.35, .27, .04), (.46, .3, .05), (.39, .33, .03)):
        if top(u0) < Y(v0):
            cv.heavy([(X(u0), Y(v0)), (X(u0 + ln * .5), Y(v0 + ln * 1.2))])
    # glaciers on the sunlit west face: fall-line ribs, each with a crevasse shadow
    for k in range(7):
        u0 = pu - .012 - k * .028
        pts = []
        for i in range(14):
            t = i / 13
            u = u0 - .1 * t * (1 + k * .15)
            v = (top(u) - y) / h + .01 + (.42 - .02 * k) * t
            if Y(v) < top(u) + 1:
                v = (top(u) - y) / h + .01
            pts.append((X(u + .004 * math.sin(t * 8 + k)), Y(min(v, .56))))
        cv.hair(pts)
        if k % 2:
            cv.hair([(px + 1.6, py + .8) for px, py in pts[4:10]])
    # forested foothills below the snowline
    snow = lambda u: Y(.48 + .03 * math.sin(u * 37) + .02 * math.sin(u * 91) + .06 * abs(u - pu))
    fpoly = [(X(u), max(top(u), snow(u))) for u in us] + [(X(.94), Y(vb + .05)), (X(-.06), Y(vb + .05))]
    cv.obj([fpoly], 0)
    cv.hair(C.hatch_poly(fpoly, 0, 1.5))
    cv.hair([[(X(u), max(top(u), snow(u)) + .5), (X(u) + .4, max(top(u), snow(u)) - 2.2)] for u in us[::2]])

    # Sauvie Island heron beating away from the smoke (Easter egg)
    _heron(cv, X(.24), Y(.1), S * .009, 1)

    # the smoke column, boiling up from behind the far ridge and bent east by the wind
    src = (X(.76), Y(.62))
    bl = []
    nl = int(13 + 11 * detail)
    for i in range(nl):
        t = i / (nl - 1)
        ccx = src[0] + w * (.03 * t + .12 * t * t)
        ccy = src[1] - h * .7 * t ** .9
        spread = h * (.025 + .17 * t ** 1.2)
        m = 1 + int(3.6 * t + .5)
        for j in range(m):
            off = (j - (m - 1) / 2) / max(1, m - 1) * spread * 2 + rng.uniform(-1, 1) * spread * .25
            r = h * (.03 + .055 * t) * rng.uniform(.65, 1.3)
            bl.append((ccy + rng.uniform(-1, 1) * h * .025, ccx + off, r, t))
    _plume(cv, [(cy, cx, r, max(0., .9 - t * 1.5) + (.3 if cx > src[0] + w * (.03 * t + .12 * t * t) else 0.),
                 rng.uniform(-.25, .25)) for cy, cx, r, t in sorted(bl)])
    # wind-torn streaks trailing from the column's head
    for k in range(int(4 + 3 * detail)):
        yy = Y(.06 + .05 * k)
        x0 = X(.86 + .03 * k)
        cv.obj([], 0)
        cv.hair([(x0, yy), (x0 + w * .08, yy + 1.5), (x0 + w * .2, yy + 1)])

    # the far ridge, burning: a crest of kranok flame tongues
    far = _ridge(X(.46), X(1.06), Y(.63), h * .025, rng, 30)
    farp = far + [(X(1.06), Y(.82)), (X(.46), Y(.82))]
    pall = [(px, py - h * (.1 + .04 * math.sin(px * .21) + .03 * math.sin(px * .07))) for px, py in far]
    pall = pall + [(px, py + 3) for px, py in far[::-1]]
    cv.obj([pall], 0)
    cv.hair(C.hatch_poly(pall, 0, 1.5))
    cv.hair(C.hatch_poly(pall, 60, 2))
    nfl = int(6 + 5 * detail)
    for i in range(nfl):
        fx = X(.56 + .42 * i / (nfl - 1)) + rng.uniform(-2, 2)
        _flame(cv, fx, _ridge_y(far, fx) + 2, h * (.2 if i % 2 else .13) * rng.uniform(.85, 1.1), rng, rng.uniform(-.15, .3), 3)
    cv.obj([farp], 1.)
    cv.hair(C.hatch_poly(farp, 0, 1.5))
    cv.line([[(px, py + 1.2), (px + 1.5, py + 4.5)] for px, py in far[::2]])

    # the mid ridge with its stand of black firs; the ones nearest the fire are crowning
    mid = _ridge(X(-.06), X(.84), Y(.74), h * .02, rng, 30, (4., 9., 17.))
    midp = mid + [(X(.84), Y(.77)), (X(.92), Y(.95)), (X(-.06), Y(.95))]
    firs = []
    nf = int(14 + 12 * detail)
    for i in range(nf):
        fx = X(-.02 + .82 * i / (nf - 1)) + rng.uniform(-3, 3)
        firs.append((fx, _ridge_y(mid, fx) + 2, h * rng.uniform(.09, .17)))
    for fx, fb, fh in firs:
        if fx > X(.6):
            _flame(cv, fx, fb - fh * .55, fh * 1.1, rng, rng.uniform(-.1, .25), 2)
    cv.obj([midp], 1.)
    cv.hair(C.hatch_poly(midp, 0, 2))
    for fx, fb, fh in sorted(firs, key=lambda f: f[2]):
        _fir(cv, fx, fb, fh, fx > X(.64))

    # the near knoll: contour-ruled ground under grass, the burned snag and the lookout
    near = [(X(-.06), Y(.79))] + [(X(-.04 + 1.1 * t), Y(.81 - .055 * math.sin(t * 3.4 + .2) + .1 * t * t)) for t in [i / 40 for i in range(41)]]
    nearp = near + [(X(1.08), Y(1.06)), (X(-.06), Y(1.06))]
    cv.obj([nearp], 1.)
    cont = []
    for k in range(1, 70):
        dy = 2. * k
        seg = []
        for i, (px, py) in enumerate(near):
            on = True
            if on:
                seg.append((px, py + dy + .6 * math.sin(i * .9 + k)))
            elif len(seg) > 1:
                cont.append(seg)
                seg = []
            else:
                seg = []
        if len(seg) > 1:
            cont.append(seg)
    cv.hair(cont)
    tuft = []
    for px, py in near:
        for k in (-1, 0, 1):
            tuft.append([(px + k * 1.6, py + .5), (px + k * 2.4 + 1, py - 3.2 - abs(k))])
    for j in range(int(30 * detail + 14)):
        u = rng.uniform(0, 1)
        gx = X(u)
        gy = _ridge_y(near, gx) + rng.uniform(.04, .2) * h
        s = 2.5 + (gy - Y(.8)) / h * 14
        for k in (-2, -1, 0, 1, 2):
            tuft.append([(gx + k * s * .35, gy), (gx + k * s * .55 + s * .2, gy - s * (1 - .15 * abs(k)))])
    cv.hair(tuft)
    lx = X(.15)
    lb = _ridge_y(near, lx) + 1
    _lookout(cv, lx, lb, h * .5)
    dx = lx + h * .2
    _dog(cv, dx, _ridge_y(near, dx) + h * .09, S * .0072, -1)
    sx = X(.9)
    _snag(cv, sx, _ridge_y(near, sx) + 3, h * .34)

    body = cv.svg()
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _medallion_scene(cx, cy, rx, ry, seed, cid):
    """for the short band: Mt. Hood over a line of kranok flames inside the oval"""
    rng = random.Random(seed)
    cv = C.Canvas()
    x, y, w, h = cx - rx, cy - ry, rx * 2, ry * 2
    sky = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([sky], 0)
    cv.hair(C.hatch_poly(sky, 0, 2, .3))
    X = lambda u: x + w * u
    Y = lambda v: y + h * v
    pu, vpk, vb = .34, .12, .84
    top = _hood_fns(X, Y, pu, .42, .5, vpk, vb)
    us = [-.1 + 1.2 * i / 80 for i in range(81)]
    prof = [(X(u), top(u)) for u in us]
    cv.obj([prof + [(X(1.1), Y(1.1)), (X(-.1), Y(1.1))]], 1.)
    ridge = [(X(pu + .03 * t * t), Y(vpk + (vb - vpk) * t)) for t in [i / 12 for i in range(13)]]
    east = [p for p in prof if p[0] >= X(pu)] + ridge[::-1]
    cv.hair(C.hatch_poly(east, 58, 1.5))
    cv.hair(C.hatch_poly([p for p in prof if p[0] <= X(pu)] + ridge + [(X(-.1), Y(1.1))], -62, 3))
    cv.line(ridge)
    for k in range(4):
        u0 = pu - .02 - k * .05
        cv.hair([(X(u0 - .08 * t), max(top(u0 - .08 * t) + 1, Y(.3 + .3 * t))) for t in [i / 6 for i in range(7)]])
    # smoke
    pl = []
    for i in range(12):
        t = i / 11
        pl.append((Y(.66 - .6 * t + rng.uniform(-.03, .03)), X(.76 + .08 * t + rng.uniform(-1, 1) * .05 * t),
                   h * (.07 + .09 * t) * rng.uniform(.8, 1.2), max(0., .9 - 1.5 * t), rng.uniform(-.2, .2)))
    _plume(cv, sorted(pl))
    for i in range(int(w / 8)):
        fx = x + 4 + (w - 8) * i / max(1, int(w / 8) - 1)
        _flame(cv, fx, y + h * .86, h * rng.uniform(.22, .34) * (1.3 if fx > X(.55) else .8), rng, rng.uniform(-.2, .2), 3)
    band = [(x - 2, y + h * .8)] + [(x + w * t, y + h * (.8 + .03 * math.sin(t * 19))) for t in [i / 20 for i in range(21)]] + [(x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([band], 1.)
    _solid(cv, band)
    for i in range(int(w / 7)):
        fx = x + 2 + (w - 4) * i / max(1, int(w / 7) - 1)
        if abs(fx - (x + w * .5)) > 2:
            _fir(cv, fx, y + h * 1.0, h * rng.uniform(.16, .26))
    d = C._d(C._ell_pts(cx, cy, rx, ry, 64), True, 0)
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{cv.svg()}</g>'


# ------------------------------------------------------------------------------------------
# the day's fires on the pedestal tablet: one flame per fire, sized by acreage
# ------------------------------------------------------------------------------------------

_DEFAULT_ACRES = [93972, 61380, 50224, 15658, 13604, 12888, 9656, 9575]


def _acres(ctx):
    vals = [int(a.replace(",", "")) for a in re.findall(r"([\d,]{3,}) acres", (ctx or {}).get("sample", ""))]
    vals = [v for v in vals if v > 0]
    if len(vals) < 4:
        vals = (vals + [v for v in _DEFAULT_ACRES if v not in vals])[:8]
    return vals[:10]


def _tablet(tx, ty, tw, th, acres, seed):
    rng = random.Random(seed)
    cv = C.Canvas()
    box = [(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th)]
    cv.obj([box], 0)
    cv.hair(C.hatch_poly(box, 0, 1.5))
    n = len(acres)
    mx = max(acres)
    # a carved ember bed along the foot
    bed = [(tx, ty + th * .78), (tx + tw, ty + th * .78), (tx + tw, ty + th), (tx, ty + th)]
    for i in range(n):
        fx = tx + tw * (i + .5) / n
        fh = (th * .8) * (.55 + .75 * math.sqrt(acres[i] / mx))
        _flame(cv, fx, ty + th * .82, fh, rng, rng.uniform(-.15, .15), 3)
    cv.obj([bed], 1.)
    _solid(cv, bed)
    # a ruled ground-line with tiny firs between the flames
    for i in range(n - 1):
        fx = tx + tw * (i + 1) / n
        _fir(cv, fx, ty + th * .8, th * .32)
    return C._clip(C._uid("tab", tx, ty, tw, th, seed), tx, ty, tw, th, cv.svg())


# ------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex so the vignette fills the whole cartouche field)
# ------------------------------------------------------------------------------------------

def _ribbon_rules(cen, bh):
    """rule the banner's face lightly: a plate keeps no blank white"""
    d = []
    for off in (-bh * .3, -bh * .1, bh * .1, bh * .3):
        pts = []
        for i in range(len(cen)):
            (x0, y0) = cen[max(0, i - 1)]
            (x1, y1) = cen[min(len(cen) - 1, i + 1)]
            L = math.hypot(x1 - x0, y1 - y0) or 1
            nx, ny = -(y1 - y0) / L, (x1 - x0) / L
            pts.append((cen[i][0] + nx * off, cen[i][1] + ny * off))
        d.append(C._d(pts[1:-1], tol=.2))
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width=".5"/>'


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .19 if h > 380 else h * .16, 44), 88.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * (.6 if h < 400 else .56), ph * .8
    cx, cy = w / 2, py0 + ph * .47
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    side_w = (pw - cw) / 2
    r1 = min(side_w * .62, ph * .26)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.05
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(side_w * .55, ph * .22)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.05
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    # kranok flames licking up out of the scrollwork at both lower corners
    fr = random.Random(seed + 11)
    for side in (-1, 1):
        for k in range(3):
            fx = cx + side * (pw * .5 - 14 - k * 13)
            _flame(main, fx, py0 + ph - 2, ph * (.16 - .025 * k), fr, side * -.25, 3)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, inner_d, seed, C._uid("sc", w, h, seed)))
    # re-lay the cartouche's bead row over the scene
    bp = C._superellipse(cx, cy, a - 0.5, b - 0.5)
    o.append(f'<path d="{C._d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1"/>')
    # crest: a flame palmette rising out of the cartouche
    pr = random.Random(seed + 3)
    crest = C.Canvas()
    C.palmette(cx, cy - ch / 2 + 6, min(ch * .16 + top_free, 56), True, pr.randrange(1 << 20), cv=crest)
    o.append(crest.svg())
    bh = min(15, ph * .055)
    bsvg, cen = C.ribbon_banner(cx, cy + ch * .48, cw * 1.25, bh, .035, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_ribbon_rules(cen, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx + 2, ty + 2, tw - 3, th - 3, _acres(ctx), seed + 5))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        pc = C.Canvas()
        fr2 = random.Random(seed + 9)
        _flame(pc, w / 2, fy + fh - 4, fh * .85, fr2, 0, 3)
        o.append(pc.svg())
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.9)
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
                   max_n=8, edge=.7, cv=cv)
    fr = random.Random(seed + 11)
    for side in (-1, 1):
        for k in range(2):
            _flame(main, cx + side * (w / 2 - 10 - k * 12), gy1 - 1, gh * (.3 - .05 * k), fr, side * -.25, 3)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, inner_d, seed, C._uid("sc", w, h, seed), .5))
    bp = C._superellipse(cx, cy, a - .5, b - .5)
    o.append(f'<path d="{C._d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    o.append(_medallion_scene(cx, cy, rx - 3, ry - 3, seed, C._uid("md", w, h, seed)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) * 7 + 5
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
