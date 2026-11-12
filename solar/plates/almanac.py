"""Almanac plate: an armillary sphere (the almanac's heavens, its polar axis set to Portland's
45.5 degrees) standing on the bank at Cathedral Park, the St. Johns Bridge's gothic towers behind
it over the Willamette, tonight's real moon phase in a ruled sky. A ribbon carries the date in
Roman numerals, the pedestal tablet a row of the lunar month with today marked.
Easter eggs: a Sauvie Island heron fishing in the shallows; a Loy Krathong float drifting
with its candle lit (Loy Krathong is on the page's 'Days to celebrate')."""
import sys
import math
import random
import datetime
import engraving_codex as C

_d, _n = C._d, C._n
TAU = math.tau
LAT = math.radians(45.5)
EPS = math.radians(23.44)


# ------------------------------------------------------------------------------------------
# date helpers
# ------------------------------------------------------------------------------------------

def _date(ctx):
    try:
        return datetime.date.fromisoformat((ctx or {}).get("date", "")[:10])
    except Exception:
        return datetime.date(2026, 11, 11)


def _moon_phase(day):
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    t = datetime.datetime(day.year, day.month, day.day, 20)
    return ((t - ref).total_seconds() / 86400 / 29.530588853) % 1.


def _roman(n):
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
                 (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s
            n -= v
    return out


# ------------------------------------------------------------------------------------------
# geometry
# ------------------------------------------------------------------------------------------

def _ell(cx, cy, rx, ry, n=40, a0=0., a1=TAU):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _moon(cv, cx, cy, r, ph):
    """Moon disc of radius r at phase ph (0 new, .5 full). Dark limb cross-hatched (earthshine),
    lit part white with a few crater rings."""
    disc = _ell(cx, cy, r, r, 40)[:-1]
    cv.obj([disc], 1.)
    k = math.cos(TAU * ph)                  # terminator x-radius factor
    waxing = ph < .5
    s = 1 if waxing else -1                 # lit side: +1 right
    # dark region: limb on the dark side (-s) + terminator
    limb = [(cx - s * r * math.sin(math.pi * i / 30), cy - r * math.cos(math.pi * i / 30)) for i in range(31)]
    term = [(cx + s * r * k * math.sin(math.pi * i / 30), cy + r * math.cos(math.pi * i / 30)) for i in range(31)]
    dark = limb + term
    cv.hair(C.hatch_poly(dark, 0, 1.5))
    cv.hair(C.hatch_poly(dark, 60, 3 if r > 6 else 2))
    lit = [(cx + s * r * math.sin(math.pi * i / 30), cy - r * math.cos(math.pi * i / 30)) for i in range(31)]
    cv.heavy(lit[3:-3] if abs(k) > .9 and ph < .5 or ph < .25 or ph > .75 else lit)
    rng = random.Random(7)
    for _ in range(4):
        a, rr = rng.uniform(0, TAU), rng.uniform(.15, .6) * r
        px, py = cx + rr * math.cos(a), cy + rr * math.sin(a)
        if r > 5 and s * (px - cx) > k * math.sqrt(max(0, r * r - (py - cy) ** 2)) + r * .12:
            cv.hair(_ell(px, py, r * .1, r * .08, 10))
    return dark


def _star(cv, x, y, s):
    p = []
    for i in range(8):
        a = TAU * i / 8 - math.pi / 2
        rr = s if i % 2 == 0 else s * .28
        p.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    cv.obj([p], .5)


# --- armillary sphere ----------------------------------------------------------------------

def _rot_view(p, el):
    x, y, z = p
    c, s = math.cos(el), math.sin(el)
    return (x, y * c - z * s, y * s + z * c)


def _circle3(u, v, c, R, n):
    return [tuple(c[k] + R * (u[k] * math.cos(TAU * i / n) + v[k] * math.sin(TAU * i / n)) for k in range(3))
            for i in range(n + 1)]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    m = math.sqrt(sum(x * x for x in a))
    return tuple(x / m for x in a)


class _Sphere:
    def __init__(self, cx, cy, R, el=math.radians(14), turn=0.):
        self.cx, self.cy, self.R, self.el = cx, cy, R, el
        self.turn = turn

    def P(self, p):
        x, y, z = p
        c, s = math.cos(self.turn), math.sin(self.turn)
        x, z = x * c + z * s, -x * s + z * c
        x, y, z = _rot_view((x, y, z), self.el)
        return (self.cx + x, self.cy - y, z)


def _ring_runs(S, u, v, c, R, t, n=120):
    """A flat ring (washer) radius R..R-t in the plane (u, v) about centre c, split into runs by
    depth. Returns list of (z_mean, outer_pts, inner_pts, mid_pts, ticks_base)."""
    out3 = _circle3(u, v, c, R, n)
    in3 = _circle3(u, v, c, R - t, n)
    O = [S.P(p) for p in out3]
    I = [S.P(p) for p in in3]
    runs, cur = [], []
    sign = None
    for i in range(n + 1):
        sg = (O[i][2] + I[i][2]) >= 0
        if sign is None or sg == sign:
            cur.append(i)
        else:
            cur.append(i)
            runs.append((sign, cur))
            cur = [i]
        sign = sg
    if cur:
        runs.append((sign, cur))
    # merge wrap-around
    if len(runs) > 1 and runs[0][0] == runs[-1][0]:
        runs[0] = (runs[0][0], runs[-1][1][:-1] + runs[0][1])
        runs.pop()
    res = []
    for front, idx in runs:
        o = [(O[i][0], O[i][1]) for i in idx]
        ii = [(I[i][0], I[i][1]) for i in idx]
        zs = sum(O[i][2] for i in idx) / len(idx)
        res.append((front, zs, o, ii, idx))
    return res, O, I


def _draw_ring(cv, run, O, I, ticks=0, shade=0., heavy=False, n=120, bp=1.5):
    front, zs, o, ii, idx = run
    poly = o + ii[::-1]
    cv.obj([poly], 1.5 if heavy and front else 1.)
    if not front:
        cv.hair(C.hatch_poly(poly, 70, bp))
        return
    # light contour along the band
    mid = [((a[0] + b[0]) * .5, (a[1] + b[1]) * .5) for a, b in zip(o, ii)]
    if ticks:
        for i in idx:
            if i % ticks == 0:
                q = 1. if i % (ticks * 3) == 0 else .55
                a, b = O[i], I[i]
                cv.hair([(a[0], a[1]), (a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q)])
        cv.hair(mid)
    else:
        cv.hair(mid)
    # shade the lower (shadow) side of each front run: hatch where the band faces down
    if shade:
        sh = []
        for k in range(len(idx) - 1):
            a, b = o[k], o[k + 1]
            if (a[1] + b[1]) * .5 > O[0][1] * 0 + _cyof(O):
                sh.append([a, b, ii[k + 1], ii[k]])
        for q in sh:
            cv.hair(C.hatch_poly(q, 0, 1.5))


def _cyof(O):
    ys = [p[1] for p in O]
    return (min(ys) + max(ys)) / 2 + (max(ys) - min(ys)) * .12


def _armillary(cv, cx, cy, R, detail=1.):
    """An armillary sphere at (cx, cy), celestial rings radius R, set for latitude 45.5 N."""
    S = _Sphere(cx, cy, R)
    t = max(1.6, R * .085)
    a = (-math.cos(LAT), math.sin(LAT), 0.)           # polar axis, north to the left
    u = (math.sin(LAT), math.cos(LAT), 0.)
    v = (0., 0., 1.)
    rings = []                                         # (u, v, centre, R, width, ticks, heavy)
    rings.append((u, v, (0, 0, 0), R, t, 0, False, "eq"))
    ne = _norm(tuple(a[k] * math.cos(EPS) + v[k] * math.sin(EPS) for k in range(3)))
    w = _norm(_cross(ne, u))
    rings.append((u, w, (0, 0, 0), R, t * 1.9, 4 if detail > .6 else 0, False, "ecl"))
    for th in ((math.radians(50), math.radians(140)) if detail > .6 else ()):
        nn = tuple(u[k] * math.cos(th) + v[k] * math.sin(th) for k in range(3))
        b2 = _norm(_cross(nn, a))
        rings.append((a, b2, (0, 0, 0), R, t * .8, 0, False, "col"))
    if detail > .6:
        for sg in (-1, 1):
            c = tuple(a[k] * R * math.sin(EPS) * sg for k in range(3))
            rings.append((u, v, c, R * math.cos(EPS), t * .7, 0, False, "trop"))
    Rm = R * 1.13
    rings.append(((1, 0, 0), (0, 1, 0), (0, 0, 0), Rm, t * 1.25, 3, True, "mer"))
    rings.append(((1, 0, 0), (0, 0, 1), (0, 0, 0), Rm * 1.02, t * 1.5, 3 if detail > .6 else 0, True, "hor"))
    allruns = []
    for (uu, vv, c, rr, tt, tk, hv, nm) in rings:
        runs, O, I = _ring_runs(S, uu, vv, c, rr, tt)
        for run in runs:
            allruns.append((run, O, I, tk, hv))
    back = sorted([r for r in allruns if not r[0][0]], key=lambda r: r[0][1])
    front = sorted([r for r in allruns if r[0][0]], key=lambda r: r[0][1])
    for run, O, I, tk, hv in back:
        _draw_ring(cv, run, O, I, tk, 0, hv, bp=1.5 if detail > .6 else 3)
    # polar axis rod
    ax0, ax1 = S.P(tuple(-a[k] * R * 1.32 for k in range(3))), S.P(tuple(a[k] * R * 1.32 for k in range(3)))
    dx, dy = ax1[0] - ax0[0], ax1[1] - ax0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * max(.9, R * .03), dx / L * max(.9, R * .03)
    rod = [(ax0[0] + nx, ax0[1] + ny), (ax1[0] + nx, ax1[1] + ny), (ax1[0] - nx, ax1[1] - ny), (ax0[0] - nx, ax0[1] - ny)]
    cv.obj([rod], 1.)
    # earth globe
    gr = R * .24
    g = _ell(cx, cy, gr, gr, 36)[:-1]
    cv.obj([g], 1.)
    for th in range(0, 180, 30):                   # meridians of the globe
        tt = math.radians(th)
        nn = tuple(u[k] * math.cos(tt) + v[k] * math.sin(tt) for k in range(3))
        b2 = _norm(_cross(nn, a))
        pts = [S.P(p) for p in _circle3(a, b2, (0, 0, 0), gr, 40)]
        seg = []
        for p in pts:
            if p[2] >= 0:
                seg.append((p[0], p[1]))
            elif seg:
                cv.hair(seg) if len(seg) > 1 else None
                seg = []
        if len(seg) > 1:
            cv.hair(seg)
    for lat in (-50, -25, 0, 25, 50):              # parallels
        la = math.radians(lat)
        c = tuple(a[k] * gr * math.sin(la) for k in range(3))
        pts = [S.P(p) for p in _circle3(u, v, c, gr * math.cos(la), 40)]
        seg = []
        for p in pts:
            if p[2] >= 0:
                seg.append((p[0], p[1]))
            elif seg:
                if len(seg) > 1:
                    cv.hair(seg)
                seg = []
        if len(seg) > 1:
            cv.hair(seg)
    # globe shadow: crescent lower right
    cres = ([(cx + gr * math.cos(x), cy + gr * math.sin(x)) for x in [math.radians(-50 + 190 * i / 20) for i in range(21)]]
            + [(cx + gr * .45 + gr * .55 * math.cos(x), cy + gr * .25 + gr * .75 * math.sin(x))
               for x in [math.radians(140 - 190 * i / 20) for i in range(21)]])
    cv.hair(C.hatch_poly(cres, 40, 1.5))
    cv.hair(C.hatch_poly(cres[:12] + cres[-12:], -40, 2))
    for run, O, I, tk, hv in front:
        _draw_ring(cv, run, O, I, tk, 1, hv)
    # axis caps (small knobs)
    for p in (ax0, ax1):
        cv.obj([_ell(p[0], p[1], max(1.5, R * .05), max(1.5, R * .05), 12)[:-1]], 1.)
        cv.hair(C.hatch_poly(_ell(p[0] + .4, p[1] + .4, max(1.2, R * .04), max(1.2, R * .04), 10)[:-1], 0, 1.5))
    return S, Rm


def _baluster(cv, cx, y0, y1, wmax):
    """A turned stand from y0 (top) to y1 (foot): cup, neck, vase knop, neck, spreading foot."""
    prof = [(0., .18), (.04, .30), (.08, .14), (.18, .10), (.26, .22), (.36, .34), (.46, .30), (.54, .16),
            (.62, .10), (.70, .12), (.76, .26), (.80, .18), (.86, .30), (.93, .50), (1., .52)]
    H = y1 - y0
    L = [(cx - hw * wmax, y0 + t * H) for t, hw in prof]
    Rr = [(cx + hw * wmax, y0 + t * H) for t, hw in prof]
    poly = L + Rr[::-1]
    cv.obj([poly], 1.)
    # contour shading: lines following the profile, dense to the right (shadow)
    for f in (.1, .32, .5, .64, .76, .86, .94):
        cv.hair([(cx + f * hw * wmax, y0 + t * H) for t, hw in prof])
    cv.hair([(cx - .8 * hw * wmax, y0 + t * H) for t, hw in prof])
    # rings at the knops
    for t, hw in prof[1::3]:
        cv.hair([(cx - hw * wmax, y0 + t * H), (cx + hw * wmax, y0 + t * H)])


# --- landscape -------------------------------------------------------------------------------

def _bridge(cv, X0, Y0, BW, BH, yH, s):
    """The St. Johns Bridge: two gothic towers, the deck, the main cables and hangers."""
    deck = yH - BH * .07
    tops = []
    for fx in (.16, .84):
        tx = X0 + BW * fx
        top = yH - BH * .43
        tw0, tw1 = BW * .034 + 1.5, BW * .024 + 1.2
        # pier
        pier = _rect(tx - tw0 * 1.25, deck, tw0 * 2.5, yH - deck + 1)
        cv.obj([pier], 1.)
        cv.hair(C.hatch_poly(pier, 0, 1.5))
        cv.hair(C.hatch_poly(pier, 90, 2))
        # two legs with a pointed gothic arch between, joined at the top
        tower = [(tx - tw0, deck), (tx - tw1, top + 6 * s), (tx - tw1 * .55, top), (tx, top - 9 * s - 3),
                 (tx + tw1 * .55, top), (tx + tw1, top + 6 * s), (tx + tw0, deck)]
        cv.obj([tower], 1.)
        cv.hair(C.hatch_poly(tower, 90, 1.5))
        # pointed arch openings (sky through), stacked
        hh = deck - top
        for k, (fa, fb) in enumerate(((.18, .36), (.42, .66), (.72, .98))):
            ya, yb = top + hh * fa, top + hh * fb
            aw = (tw1 + (tw0 - tw1) * fb) * .55
            arch = [(tx - aw, yb), (tx - aw, ya + aw * 1.3)] + \
                   [(tx - aw * math.cos(math.radians(a)) * 1, ya + aw * 1.3 - aw * 1.3 * math.sin(math.radians(a)) ** .7)
                    for a in range(10, 90, 20)] + [(tx, ya)] + \
                   [(tx + aw * math.cos(math.radians(a)), ya + aw * 1.3 - aw * 1.3 * math.sin(math.radians(a)) ** .7)
                    for a in range(80, 0, -20)] + [(tx + aw, ya + aw * 1.3), (tx + aw, yb)]
            cv.obj([arch], .5)
            cv.hair(C.hatch_poly(arch, 0, 3))
        tops.append((tx, top + 1))
    # main cables
    (xa, ya), (xb, yb) = tops
    sag = deck - 2 - ya
    cab = [(xa + (xb - xa) * i / 40, ya + sag * (1 - (2 * i / 40 - 1) ** 2)) for i in range(41)]
    sideL = [(xa + (X0 - 4 - xa) * i / 12, ya + (deck - 1 - ya) * (i / 12) ** 1.4) for i in range(13)]
    sideR = [(xb + (X0 + BW + 4 - xb) * i / 12, yb + (deck - 1 - yb) * (i / 12) ** 1.4) for i in range(13)]
    # deck with truss
    dk = _rect(X0 - 4, deck - 1.5 * s - 1.5, BW + 8, 3 * s + 3)
    hang = []
    for c in (cab, sideL, sideR):
        for i in range(1, len(c) - 1):
            x, y = c[i]
            if deck - y > 2.5:
                hang.append([(x, y), (x, deck - 1.5 * s - 1.5)])
    cv.obj([], 0)
    cv.hair(hang)
    cv.obj([dk], 1.)
    cv.hair(C.hatch_poly(dk, 50, 2.5 if s > .6 else 3))
    cv.hair(C.hatch_poly(dk, -50, 2.5 if s > .6 else 3))
    cv.obj([], 0)
    cv.line(cab)
    cv.line(sideL)
    cv.line(sideR)
    return deck


def _ridge(cv, X0, Y0, BW, BH, yH, rng):
    """The West Hills / Forest Park ridge on the far bank, dark, with a ruled tree-line."""
    n = 60
    top = []
    for i in range(n + 1):
        x = X0 - 3 + (BW + 6) * i / n
        f = i / n
        y = yH - BH * (.10 + .07 * math.sin(f * 3.1 + .4) ** 2 + .012 * math.sin(f * 37) + .008 * rng.random())
        top.append((x, y))
    poly = top + [(X0 + BW + 3, yH + .5), (X0 - 3, yH + .5)]
    cv.obj([poly], .5)
    cv.hair(C.hatch_poly(poly, 0, 1.5))
    cv.hair(C.hatch_poly(poly, 75, 3))
    # tree crowns along the crest
    for i in range(0, n, 2):
        x, y = top[i]
        cv.hair([(x - 1.2, y + 1.5), (x, y - 1.2), (x + 1.2, y + 1.5)])


def _water(cv, X0, Y0, BW, BH, yH, y1, rng, moon_x, towers):
    poly = _rect(X0 - 3, yH, BW + 6, y1 - yH + 3)
    cv.obj([poly], 0)
    y = yH + 1.5
    k = 0
    while y < y1 + 3:
        pitch = 1.5 if y - yH < BH * .06 else (2. if y - yH < BH * .16 else 2.)
        x = X0 - 3
        while x < X0 + BW + 3:
            L = rng.uniform(5, 26) * (1 + (y - yH) / BH)
            gap = rng.uniform(1.2, 3.)
            if abs(x - moon_x) < 4 + (y - yH) * .25:
                L, gap = rng.uniform(1.5, 4), rng.uniform(1.5, 3)
            wob = rng.uniform(-.3, .3)
            cv.hair([(x, y + wob), (x + L * .5, y + wob - .35), (x + L, y + wob)])
            x += L + gap
        # dark tower reflections
        for tx in towers:
            if y - yH < BH * .25:
                cv.hair([(tx - 2 + rng.uniform(-1, 1), y + 1), (tx + 2 + rng.uniform(-1, 1), y + 1)])
        y += pitch
        k += 1


def _bank(cv, X0, Y0, BW, BH, ytop, y1, rng, cx):
    """The near bank (Cathedral Park): a low mound rising to the stand, grass tufts on its crest."""
    n = 50
    top = []
    for i in range(n + 1):
        x = X0 - 3 + (BW + 6) * i / n
        f = (x - cx) / (BW * .5)
        y = ytop + BH * .07 * min(1, f * f) + BH * .008 * math.sin(i * 1.7)
        top.append((x, y))
    poly = top + [(X0 + BW + 3, y1 + 3), (X0 - 3, y1 + 3)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 12, 2))
    cv.hair(C.hatch_poly(poly, -35, 3))
    for i in range(0, n + 1):
        x, y = top[i]
        for j in range(3):
            dx = rng.uniform(-2.5, 2.5)
            hh = rng.uniform(2, 4.5)
            cv.hair([(x + dx * .3, y + .5), (x + dx, y - hh)])
    return top


def _heron(cv, x, y, sz):
    """Great blue heron standing in the shallows, facing left, neck in its S."""
    s = sz / 30.
    P = lambda pts: [(x + px * s, y + py * s) for px, py in pts]
    body = P([(-3, -14), (2, -17), (8, -16), (13, -12), (16, -7), (11, -8), (5, -7), (-1, -9)])
    neck = P([(-2, -15), (-5, -19), (-2.5, -23), (0, -26.5), (-2.5, -30), (-6, -31.2), (-8.5, -29.8), (-6.5, -27.6),
              (-4.5, -26), (-7, -23), (-9, -18.5), (-1, -9)])
    beak = P([(-8, -29.5), (-15, -28.6), (-7.5, -28.4)])
    cv.obj([neck], 1.)
    cv.hair(C.hatch_poly(neck, 0, 1.5))
    cv.obj([body], 1.)
    cv.hair([P([(-1, -12), (5, -14), (12, -11)]), P([(1, -10.5), (8, -11), (14, -8.5)])])
    cv.hair(C.hatch_poly(body[3:] + body[:1], 30, 1.5))
    cv.obj([beak], .5)
    cv.line(P([(-7, -30.5), (-1, -31.5)]))                 # crest plume
    cv.obj([], 0)
    cv.hair([P([(3, -8), (2, 0)]), P([(6, -8), (7, 0)])])  # legs
    cv.hair([P([(-1, .5), (10, .5)]), P([(-3, 1.6), (12, 1.6)])])  # ripples


def _krathong(cv, x, y, sz):
    """A Loy Krathong float: lotus petals on a banana-trunk base, a candle with its flame."""
    s = sz / 16.
    base = _ell(x, y, 8 * s, 2.4 * s, 20, 0, math.pi)
    base = [(x - 8 * s, y)] + base
    pet = []
    for i in range(5):
        px = x - 6.5 * s + i * 3.25 * s
        pet.append([(px - 1.8 * s, y), (px, y - 4.2 * s - (1.2 * s if i == 2 else 0)), (px + 1.8 * s, y)])
    cv.obj(pet, .5)
    cv.hair([[(p[0][0] + .4, p[0][1] - .3), (p[1][0], p[1][1] + 1)] for p in pet])
    cv.obj([base], .5)
    cv.hair(C.hatch_poly(base, 0, 1.5))
    cv.obj([], 0)
    cv.line([(x, y - 4 * s), (x, y - 8.5 * s)])
    fl = [(x, y - 13 * s), (x + 1.3 * s, y - 10 * s), (x, y - 8.8 * s), (x - 1.3 * s, y - 10 * s)]
    cv.obj([fl], .5)
    for i in range(3):
        cv.hair([(x - 3 * s - i * 1.5, y + 3 * s + i * 1.5), (x + 3 * s + i * 1.5, y + 3 * s + i * 1.5)])


def _reeds(cv, x, y, h, rng, n=6):
    for i in range(n):
        bx = x + i * 2.4 + rng.uniform(-.8, .8)
        hh = h * rng.uniform(.6, 1.)
        lean = rng.uniform(-3, 2)
        stem = [(bx + lean * (t / 8) ** 2, y - hh * t / 8) for t in range(9)]
        cv.obj([], 0)
        cv.hair(stem)
        if i % 2 == 0:
            tx, ty = stem[-2]
            head = _ell(tx, ty, 1.2, h * .09, 10)[:-1]
            cv.obj([head], .5)
            cv.hair(C.hatch_poly(head, 0, 1.5))


# ------------------------------------------------------------------------------------------
# the vignette
# ------------------------------------------------------------------------------------------

def _scene(field, ctx, mini=False):
    """Draw the scene into the bbox of field (a polygon), clipped to it by the caller."""
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    X0, Y0, X1, Y1 = min(xs), min(ys), max(xs), max(ys)
    BW, BH = X1 - X0, Y1 - Y0
    day = _date(ctx)
    rng = random.Random(day.toordinal())
    ph = _moon_phase(day)
    cv = C.Canvas()
    s = min(1.3, max(.45, BH / 250.))
    yH = Y0 + BH * (.70 if not mini else 2)
    # sky: graded ruled lines, fine above, opening toward the horizon
    sky = _rect(X0 - 3, Y0 - 3, BW + 6, min(yH, Y1) - Y0 + 4)
    cv.obj([sky], 0)
    bands = [(0., .28, 1.5), (.28, .55, 2.), (.55, 1.01, 2.)]
    hy = min(yH, Y1 + 3) - (Y0 - 3)
    for f0, f1, p in bands:
        q = _rect(X0 - 3, Y0 - 3 + hy * f0, BW + 6, hy * (f1 - f0))
        cv.hair(C.hatch_poly(q, 0, p, phase=.25))
    # second, crossing tone at the top of the sky (night)
    cv.hair(C.hatch_poly(_rect(X0 - 3, Y0 - 3, BW + 6, hy * .2), 30, 3))
    # moon + stars
    mr = max(5, BH * .06) if not mini else max(4, BH * .16)
    mx = X0 + BW * (.74 if not mini else .2)
    my = Y0 + BH * (.12 if not mini else .3)
    cv.obj([_ell(mx, my, mr + 5.5, mr + 5.5, 40)[:-1]], 0)
    for k in range(1, 3):
        cv.hair(_ell(mx, my, mr + 2 * k, mr + 2 * k, 40))
    _moon(cv, mx, my, mr, ph)
    for i in range(int(14 * (BW * BH) / 50000) + 3):
        sx, sy = X0 + rng.uniform(.05, .95) * BW, Y0 + rng.uniform(.05, .5 if not mini else .9) * BH
        if math.hypot(sx - mx, sy - my) < mr * 2.5:
            continue
        _star(cv, sx, sy, rng.choice((1.6, 2.2, 2.2, 3.)) * (1 if not mini else .8))
    if mini:
        R = min(BW * .28, BH * .36)
        _armillary(cv, X0 + BW * .55, Y0 + BH * .5, R, detail=.4)
        return cv.svg()
    _ridge(cv, X0, Y0, BW, BH, yH, rng)
    deck = _bridge(cv, X0, Y0, BW, BH, yH, s)
    bank_y = Y0 + BH * .86
    R = min(BW * .25, BH * .225)
    scx, scy = X0 + BW * .5, Y0 + BH * .37
    _water(cv, X0, Y0, BW, BH, yH, Y1, rng, mx, (X0 + BW * .16, X0 + BW * .84))
    _krathong(cv, X0 + BW * .26, yH + BH * .09, max(10, 19 * s))
    _heron(cv, X0 + BW * .82, bank_y + BH * .01, max(20, 50 * s))
    _bank(cv, X0, Y0, BW, BH, bank_y, Y1, rng, scx)
    _reeds(cv, X0 + BW * .06, bank_y + BH * .06, BH * .14, rng, 7)
    # stand, then sphere on it
    _baluster(cv, scx, scy + R * 1.15, bank_y + BH * .015, R * .42)
    _armillary(cv, scx, scy, R, detail=1. if R > 42 else .4)
    return cv.svg()


def _hourglass(cx, ybot, H, frac_left):
    """An hourglass standing on the cartouche crest: turned caps and posts, glass bulbs, the upper
    bulb holding the fraction of the year still to come, the rest heaped below."""
    cv = C.Canvas()
    hw = H * .3
    cap = H * .085
    y0, y1 = ybot - H, ybot
    gy0, gy1 = y0 + cap, y1 - cap
    gh = gy1 - gy0
    ym = (gy0 + gy1) / 2

    def wid(u):                       # u 0 at cap .. 1 at neck
        return hw * .07 + hw * .78 * (1 - u ** 1.8) ** .6

    L, Rr = [], []
    for i in range(21):
        u = i / 20
        L.append((cx - wid(u), gy0 + gh / 2 * u)); Rr.append((cx + wid(u), gy0 + gh / 2 * u))
    for i in range(1, 21):
        u = 1 - i / 20
        L.append((cx - wid(u), ym + gh / 2 * (1 - u))); Rr.append((cx + wid(u), ym + gh / 2 * (1 - u)))
    glass = L + Rr[::-1]
    # posts behind the glass corners
    for sx in (-1, 1):
        px = cx + sx * hw * .92
        post = [(px - 1.6, gy0), (px + 1.6, gy0), (px + 1.6, gy1), (px - 1.6, gy1)]
        cv.obj([post], 1.)
        cv.hair([(px + .6 * sx, gy0), (px + .6 * sx, gy1)])
        for f in (.2, .5, .8):
            k = _ell(px, gy0 + gh * f, 2.4, 1.6, 12)[:-1]
            cv.obj([k], .5)
            cv.hair(C.hatch_poly(k, 0, 1.5))
    cv.obj([glass], 1.)
    cv.hair([(x + 1.6, y) for x, y in L[2:-2]])
    cv.hair([(x - 2.2, y) for x, y in Rr[3:-3]])
    # sand above: level so area ~ frac_left
    lev = 1 - max(.04, min(.95, frac_left)) ** .5
    top = [(cx - wid(u), gy0 + gh / 2 * u) for u in [lev + (1 - lev) * i / 12 for i in range(13)]]
    sand = top + [(2 * cx - x, y) for x, y in top[::-1]]
    cv.hair(C.hatch_poly(sand, 0, 1.5))
    cv.hair(C.hatch_poly(sand, 60, 2))
    # heap below
    fill = 1 - frac_left
    hy = gy1 - gh / 2 * (.15 + .7 * fill)
    heap = [(cx - wid(.98 - .97 * ((gy1 - y) / (gh / 2))), y) for y in [gy1 - (gy1 - hy) * i / 10 for i in range(11)]]
    heap = [(cx - wid(.05) * .98, gy1)] + [(cx - wid(1 - (gy1 - y) / (gh / 2)) * .98, y) for y in [gy1 - (gy1 - hy + 2) * i / 10 for i in range(1, 10)]]
    mound = heap + [(cx, hy - 2.5)] + [(2 * cx - x, y) for x, y in heap[::-1]]
    cv.hair(C.hatch_poly(mound, 0, 1.5))
    cv.hair(C.hatch_poly(mound, -60, 2))
    cv.hair([(cx, ym), (cx, hy - 2.5)])
    # caps
    for yc, up in ((y0, True), (y1 - cap, False)):
        c = [(cx - hw * 1.12, yc), (cx + hw * 1.12, yc), (cx + hw * 1.12, yc + cap), (cx - hw * 1.12, yc + cap)]
        cv.obj([c], 1.)
        cv.hair(C.hatch_poly(c, 0, 1.5) if up else C.hatch_poly(c, 90, 1.5))
        cv.hair([(cx - hw * 1.12, yc + cap * .5), (cx + hw * 1.12, yc + cap * .5)])
    fin = _ell(cx, y0 - 2.2, 2.6, 2.4, 14)[:-1]
    cv.obj([fin], 1.)
    cv.hair(C.hatch_poly(fin, 45, 1.5))
    return cv.svg()


def _clip_poly(cid, poly, body):
    return (f'<clipPath id="{cid}"><path d="{_d(poly, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g>')


# ------------------------------------------------------------------------------------------
# lettering: Roman numerals as strokes along the banner face
# ------------------------------------------------------------------------------------------

_GLYPH = {
    "I": ([[(0, 0), (0, 1)]], .25),
    "V": ([[(-.42, 0), (0, 1), (.42, 0)]], .95),
    "X": ([[(-.42, 0), (.42, 1)], [(.42, 0), (-.42, 1)]], .95),
    "L": ([[(-.3, 0), (-.3, 1), (.35, 1)]], .75),
    "C": ([[(.38, .15), (.2, .02), (-.05, 0), (-.3, .12), (-.42, .35), (-.42, .65), (-.3, .88), (-.05, 1), (.2, .98), (.38, .85)]], .9),
    "D": ([[(-.35, 0), (-.35, 1)], [(-.35, 0), (0, 0), (.3, .15), (.42, .5), (.3, .85), (0, 1), (-.35, 1)]], .9),
    "M": ([[(-.5, 1), (-.42, 0), (0, .8), (.42, 0), (.5, 1)]], 1.15),
    "·": ([[(-.06, .5), (.06, .5)]], .7),
}


def _letter(cv, centre, text, gh):
    # arc-length param of centre line
    acc = [0.]
    for i in range(1, len(centre)):
        acc.append(acc[-1] + math.dist(centre[i], centre[i - 1]))
    total = acc[-1]

    def at(sv):
        sv = max(0, min(total, sv))
        for i in range(1, len(acc)):
            if acc[i] >= sv:
                f = (sv - acc[i - 1]) / max(1e-6, acc[i] - acc[i - 1])
                p0, p1 = centre[i - 1], centre[i]
                return (p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f,
                        math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
        return centre[-1][0], centre[-1][1], 0.
    gap = gh * .32
    widths = [_GLYPH[ch][1] * gh * .7 for ch in text]
    tw = sum(widths) + gap * (len(text) - 1)
    pos = (total - tw) / 2
    cv.obj([], 0)
    for ch, wd in zip(text, widths):
        mx, my, a = at(pos + wd / 2)
        ca, sa = math.cos(a), math.sin(a)
        for stroke in _GLYPH[ch][0]:
            pts = []
            for gx, gy in stroke:
                lx, ly = gx * gh * .7, (gy - .5) * gh
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            if ch == "·":
                cv.heavy(pts)
            else:
                cv.line(pts) if gh < 9 else cv.heavy(pts)
        # serifs on verticals of I
        if ch == "I":
            for gy in (0, 1):
                ly = (gy - .5) * gh
                p = [(mx + lx * ca - ly * sa, my + lx * sa + ly * ca) for lx in (-gh * .16, gh * .16)]
                cv.hair(p)
        pos += wd + gap


def _tablet(x, y, w, h, ph):
    """The pedestal tablet: a row of the lunar month's phases on a ruled ground, tonight's ringed."""
    cv = C.Canvas()
    bg = _rect(x + 1, y + 1, w - 2, h - 2)
    cv.obj([bg], 0)
    cv.hair(C.hatch_poly(bg, 0, 1.5))
    n = max(9, min(29, int(w / (h * 1.15))))
    r = min(h * .36, w / n * .38)
    today = round(ph * n) % n
    for i in range(n):
        px = x + w * (i + .5) / n
        py = y + h / 2
        p = i / n
        if i == today:
            ring = _ell(px, py, r + 2.2, r + 2.2, 24)[:-1]
            cv.obj([ring], 1.)
        _moon(cv, px, py, r, p if p > 0 else .001)
    return cv.svg()


# ------------------------------------------------------------------------------------------
# layouts (house frame, copied so the vignette can fill the cartouche field completely)
# ------------------------------------------------------------------------------------------

def _field(cx, cy, cw, ch, inset=4.5):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - inset, b - inset, n=96)


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fld = _ell(cx, cy, rx - 3.5, ry - 3.5, 64)[:-1]
    o.append(_clip_poly(C._uid("bv", w, h, seed), fld, _scene(fld, ctx, mini=True)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx, density=1.):
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
                   max_n=int(10 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fld = _field(cx, cy, cw, gh + 4)
    o.append(_clip_poly(C._uid("mv", w, h, seed), fld, _scene(fld, ctx)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .03, 11.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # soft stippled air above the panel so the crest rises out of tone, not bare paper
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .68
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
                   max_n=int(9 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fld = _field(cx, cy, cw, ch)
    o.append(_clip_poly(C._uid("tv", w, h, seed), fld, _scene(fld, ctx)))
    o.append(C.palmette(cx, cy - ch / 2 + 6, min(ch * .16 + top_free, 52), True, rng.randrange(1 << 20)))
    day = _date(ctx)
    yd = day.timetuple().tm_yday
    ndays = 366 if day.year % 4 == 0 and (day.year % 100 or day.year % 400 == 0) else 365
    hh = min(ch * .5 - (cy - py0) + ch * .5 + top_free + 4, 58.)
    hh = min(54., cy - ch / 2 - 2)
    o.append(_hourglass(cx, cy - ch / 2 + 6, hh, 1 - yd / ndays))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    day = _date(ctx)
    lv = C.Canvas()
    _letter(lv, centre[3:-3], f"{_roman(day.month)}·{_roman(day.day)}·{_roman(day.year)}", bh * .55)
    o.append(lv.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx + 2, ty + 2, tw - 3, th - 3, _moon_phase(day)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 315
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
