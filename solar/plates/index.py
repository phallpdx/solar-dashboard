"""Front page (index) plate: The Morning Edition's own frontispiece.

Subject, from the page itself (Sauvie Island, cloudy, the day's edition): the view from Parker's
island at first light. A great blue heron stands in the shallows of the Multnomah Channel; behind
it the St. Johns Bridge throws its gothic towers and cables across the river, and Mt. Hood rises
between the towers under a banked, sun-broken cloud sky. The scene is cut into a carved Codex
cartouche between big shaded acanthus volutes; on tall sheets a ribbon banner is lettered THE
MORNING EDITION and the pedestal tablet carries the date in Roman numerals.
Easter egg: the Blazers pinwheel (today's top story) is carved as a rosette boss in the frame.
"""
import sys
import math
import random
import engraving_codex as C

_n, _d = C._n, C._d
PI = math.pi


# ----------------------------------------------------------------------------------------------
# small geometry
# ----------------------------------------------------------------------------------------------

def _hy(y):
    """snap a horizontal hairline to the device grid (k*.5 + .25)"""
    return round((y - .25) * 2) / 2 + .25


def _clip_y(poly, y0, keep_below=True):
    """Sutherland-Hodgman clip of a polygon against the line y = y0."""
    out = []
    n = len(poly)
    inside = (lambda p: p[1] >= y0) if keep_below else (lambda p: p[1] <= y0)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ia, ib = inside(a), inside(b)
        if ia:
            out.append(a)
        if ia != ib:
            t = (y0 - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * t, y0))
    return out


def _hlines(x0, x1, y0, y1, pitch, rng=None, brk=0., seg=(14, 40), gap=(1.5, 3.)):
    """horizontal hairlines on the grid, optionally broken into dashes (water)"""
    out = []
    y = _hy(y0)
    while y <= y1:
        if brk and rng:
            x = x0 - rng.uniform(0, 20)
            while x < x1:
                L = rng.uniform(*seg)
                out.append([(max(x, x0), y), (min(x + L, x1), y)])
                x += L + rng.uniform(*gap)
        else:
            out.append([(x0, y), (x1, y)])
        y += pitch
    return out


def _bez(p0, p1, p2, p3, n=12):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return pts


# ----------------------------------------------------------------------------------------------
# lettering: a small engraver's stroke alphabet (unit cap height), drawn as paths
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_S = .1  # serif half-length
_GLYPHS = {
    "T": (.72, [[(0, 0), (.72, 0)], [(.36, 0), (.36, 1)], [(.36 - _S, 1), (.36 + _S, 1)]]),
    "H": (.7, [[(0, 0), (0, 1)], [(.7, 0), (.7, 1)], [(0, .5), (.7, .5)],
               [(-_S, 0), (_S, 0)], [(-_S, 1), (_S, 1)], [(.7 - _S, 0), (.7 + _S, 0)], [(.7 - _S, 1), (.7 + _S, 1)]]),
    "E": (.58, [[(.58, 0), (0, 0), (0, 1), (.6, 1)], [(0, .5), (.42, .5)], [(-_S, 0), (0, 0)], [(-_S, 1), (0, 1)]]),
    "M": (.86, [[(0, 1), (.04, 0), (.43, .78), (.82, 0), (.86, 1)], [(-_S, 1), (_S, 1)], [(.86 - _S, 1), (.86 + _S, 1)]]),
    "O": (.8, [_arc(.4, .5, .42, .5, 0, 360, 28)]),
    "R": (.64, [[(0, 1), (0, 0), (.36, 0)] + _arc(.36, .26, .26, .26, -90, 90, 10) + [(0, .52)],
                [(.3, .52), (.66, 1)], [(-_S, 0), (0, 0)], [(-_S, 1), (_S, 1)]]),
    "N": (.7, [[(0, 1), (0, 0), (.7, 1), (.7, 0)], [(-_S, 1), (_S, 1)], [(.7 - _S, 0), (.7 + _S, 0)]]),
    "I": (0., [[(0, 0), (0, 1)], [(-_S, 0), (_S, 0)], [(-_S, 1), (_S, 1)]]),
    "G": (.78, [_arc(.42, .5, .42, .5, -40, -350, 24) + [(.84, .58), (.5, .58)]]),
    "D": (.72, [[(0, 0), (.3, 0)] + _arc(.3, .5, .42, .5, -90, 90, 16) + [(0, 1), (0, 0)],
                [(-_S, 0), (0, 0)], [(-_S, 1), (0, 1)]]),
    "V": (.72, [[(0, 0), (.36, 1), (.72, 0)], [(-_S, 0), (_S, 0)], [(.72 - _S, 0), (.72 + _S, 0)]]),
    "X": (.66, [[(0, 0), (.66, 1)], [(.66, 0), (0, 1)], [(-_S, 0), (_S, 0)], [(.66 - _S, 1), (.66 + _S, 1)],
                [(.66 - _S, 0), (.66 + _S, 0)], [(-_S, 1), (_S, 1)]]),
    "L": (.54, [[(0, 0), (0, 1), (.56, 1)], [(-_S, 0), (_S, 0)]]),
    "C": (.72, [_arc(.42, .5, .42, .5, -45, -315, 22)]),
    "·": (0., [_arc(0, .5, .07, .07, 0, 360, 8)]),
    " ": (.3, []),
}


def _text_width(s, ch, track=.32):
    return sum((_GLYPHS[c][0] + track) * ch for c in s) - track * ch


def _letter(s, cx, cy, ch, track=.32, along=None):
    """polylines spelling s, centred on (cx, cy), cap height ch. along(x_offset) -> (x, y, angle)
    bends the line of text onto a curve."""
    tw = _text_width(s, ch, track)
    x = -tw / 2
    out = []
    for c in s:
        gw, strokes = _GLYPHS[c]
        mid = x + gw * ch / 2
        if along:
            px, py, a = along(mid)
        else:
            px, py, a = cx + mid, cy, 0.
        ca, sa = math.cos(a), math.sin(a)
        for st in strokes:
            q = []
            for (u, v) in st:
                lx, ly = (u - gw / 2) * ch, (v - .5) * ch
                q.append((px + lx * ca - ly * sa, py + lx * sa + ly * ca))
            out.append(q)
        x += (gw + track) * ch
    return out


_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
          (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _roman(n):
    s = ""
    for v, r in _ROMAN:
        while n >= v:
            s += r
            n -= v
    return s


def _date_parts(ctx):
    try:
        y, m, d = [int(v) for v in (ctx or {}).get("date", "2026-11-11")[:10].split("-")]
    except Exception:
        y, m, d = 2026, 11, 11
    return y, m, d


# ----------------------------------------------------------------------------------------------
# the Blazers pinwheel (easter egg), as a carved boss
# ----------------------------------------------------------------------------------------------

def _pinwheel_boss(cx, cy, r):
    o = [f'<path d="{_d(C._ell_pts(cx, cy, r + 1.5, r + 1.5, 28), True, 0)}" fill="#000" stroke="none"/>',
         f'<path d="{_d(C._ell_pts(cx, cy, r, r, 28), True, 0)}" fill="#fff" stroke="none"/>']
    g = ""
    for k in range(5):
        off = (k - 2) * r * .24
        # two interlocked sets of five swept stripes, as on the logo
        a = _bez((cx - r * .95, cy - r * .1 + off * .9), (cx - r * .5, cy - r * .55 + off),
                 (cx - r * .1, cy - r * .7 + off), (cx + r * .25, cy - r * .95 + off * .5), 6)
        b = [(2 * cx - p[0], 2 * cy - p[1]) for p in a]
        g += _d(a, tol=0) + _d(b, tol=0)
    o.append(f'<path d="{g}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, r, r, 28), True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# the heron (unit: feet at y=100, facing right)
# ----------------------------------------------------------------------------------------------

_HERON = [(64, 13.6), (52, 11.4), (45, 9.6), (41, 8.4), (37, 8.6), (30, 10.4), (22, 13.2), (30, 12.6), (34, 13.2),
          (35.5, 16), (37.2, 22), (39.8, 28.5), (39.2, 33.5), (35.5, 38.5), (30.5, 42.5), (25, 45.5), (17, 49.5),
          (9, 55), (3, 61), (-1, 67.5), (5, 67), (11, 66.2), (19, 65), (26, 63), (31.5, 59.5), (36, 54.5),
          (40.2, 48.5), (43.4, 42), (45.3, 35), (45.2, 29), (43, 24.2), (41.6, 20), (42.6, 16.6), (45.5, 15.2),
          (52, 14.6)]
_WING = [(14, 51), (24, 47.2), (31.5, 47.5), (34, 52.5), (29, 59.5), (20, 63.2), (9, 65.6), (2, 66.5), (6, 60)]


def _heron(cv, x, y, s, rng):
    """the great blue heron, feet at (x, y), s px per unit. Painted into cv."""
    def P(u, v):
        return (x + (u - 22) * s, y + (v - 100) * s)
    sil = [P(*p) for p in _HERON]
    # legs first (behind the body)
    cv.obj([], 0)
    for (u0, v0), (u1, v1) in (((22.5, 63.5), (21, 100)), ((27, 62), (30.5, 100))):
        cv.line([P(u0, v0), P((u0 + u1) / 2 + .6, (v0 + v1) / 2), P(u1, v1)])
    cv.obj([sil], 1.)
    # back and body: soft slate-blue tone, lines running with the body
    body = [P(*p) for p in [(30.5, 42.5), (25, 45.5), (17, 49.5), (9, 55), (3, 61), (-1, 67.5), (5, 67), (11, 66.2),
                            (19, 65), (26, 63), (31.5, 59.5), (36, 54.5), (40.2, 48.5), (38, 44)]]
    cv.hair(C.hatch_poly(body, -32, 2., .3))
    # neck: the front streaked, the back of the neck shaded
    for k in range(7):
        v = 24 + k * 3.6
        cv.hair([P(43.6 - k * .15, v), P(42.4 - k * .2, v + 2.2)])
    neckb = [P(*p) for p in [(35.5, 16), (37.2, 22), (39.8, 28.5), (39.2, 33.5), (35.5, 38.5), (37.5, 39),
                             (41, 34), (41.8, 28.5), (39.6, 22), (38, 16)]]
    cv.hair(C.hatch_poly(neckb, 70, 1.5, .2))
    # breast plumes hanging over the front
    for k in range(5):
        a = P(39.5 - k * 1.4, 47 + k * 1.2)
        b = P(35 - k * 1.5, 58 + k * 1.1)
        cv.hair([a, ((a[0] + b[0]) / 2 + s * .6, (a[1] + b[1]) / 2), b])
    # the folded wing: darker, with long scapular plumes and covert scallops
    wing = [P(*p) for p in _WING]
    cv.obj([wing], .5)
    cv.hair(C.hatch_poly(wing, -24, 1.5, .1))
    for k in range(5):
        cv.hair(_bez(P(17 + k * 3.2, 49.5 - k * .5), P(15 + k * 2.4, 56), P(8 + k * 2, 62.5), P(1 + k * 2.2, 66.6 - k * .2), 8))
    for k in range(4):
        cx_, cy_ = P(25 + k * 2.2, 50.5 + k * 2.2)
        cv.hair(C._ell_pts(cx_, cy_, s * 2.2, s * 1.2, 10, 0, PI))
    # head: black crown stripe into the trailing plume, the eye, the dagger bill
    cv.heavy([P(46, 10.2), P(40, 9.7), P(33, 11.2), P(24, 13.2)])
    cv.line([P(45, 11.8), P(40, 11.6), P(35.5, 13.2)])
    ex, ey = P(46.6, 11.6)
    cv.line(C._ell_pts(ex, ey, max(.6, s * .5), max(.6, s * .5), 8))
    cv.hair([P(48, 12.6), P(63, 13.6)])
    bill = [P(47.5, 11.2), P(63.5, 13.6), P(48, 13.4)]
    cv.hair(C.hatch_poly(bill, 8, 1.5, .1))
    # feet in the water: ripples round the shins
    cv.obj([], 0)
    for (u, v) in ((21, 99.2), (30.5, 99.2)):
        cx_, cy_ = P(u, v)
        for k, rr in enumerate((2.2, 4.4, 7)):
            cv.hair(C._ell_pts(cx_, cy_, rr * s, rr * s * .22, 20, PI * (.05 + k * .05), PI * (.95 - k * .05)))
            cv.hair(C._ell_pts(cx_, cy_, rr * s, rr * s * .22, 20, PI * (1.1 + k * .04), PI * (1.4)))


def _reeds(cv, x0, x1, ybot, h, rng, n=9):
    """cattails and blades in the near shallows"""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + rng.uniform(.1, .9)) / n
        hh = h * rng.uniform(.55, 1.)
        lean = rng.uniform(-.25, .25) * hh
        top = (x + lean, ybot - hh)
        cv.obj([], 0)
        cv.line(_bez((x, ybot), (x, ybot - hh * .5), (x + lean * .6, ybot - hh * .8), top, 8))
        if rng.random() < .55:
            # a cattail head: a black capsule with a spike
            a = math.atan2(top[1] - (ybot - hh * .8), top[0] - (x + lean * .6))
            L = max(4., h * .16)
            w = max(1.4, L * .2)
            cxh, cyh = top[0] - math.cos(a) * L * .7, top[1] - math.sin(a) * L * .7
            ca, sa = math.cos(a), math.sin(a)
            cap = [(cxh + ca * L * .5 * math.cos(t) - sa * w * math.sin(t), cyh + sa * L * .5 * math.cos(t) + ca * w * math.sin(t))
                   for t in [2 * PI * k / 14 for k in range(14)]]
            cv.obj([cap], 1.)
            cv.line(C.hatch_poly(cap, math.degrees(a), 1., 0))
            cv.hair([top, (top[0] + ca * L * .4, top[1] + sa * L * .4)])
        # a pair of swept blades
        for sd in (-1, 1):
            if rng.random() < .7:
                bl = hh * rng.uniform(.5, .85)
                tip = (x + sd * bl * .45, ybot - bl)
                cv.obj([], 0)
                cv.hair(_bez((x, ybot), (x + sd * bl * .05, ybot - bl * .5), (tip[0] - sd * bl * .1, tip[1] + bl * .15), tip, 8))
                cv.hair(_bez((x + sd * .8, ybot), (x + sd * bl * .08, ybot - bl * .45), (tip[0] - sd * bl * .06, tip[1] + bl * .2), tip, 8))


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def _scene(X, Y, W, H, seed, doy, level=2):
    """The island view filling the box X,Y,W,H (draw beyond it; the caller clips).
    level 2 full (heron, bridge, Hood), 1 medium, 0 tiny medallion."""
    rng = random.Random(seed)
    cv = C.Canvas()
    yw = Y + H * (.64 if level else .62)           # water line
    # --- sky: ruled, denser aloft, opening to a glow round the low sun
    sun_x = X + W * (.8 + .06 * math.sin(2 * PI * doy / 365.))
    sun_y = Y + H * (.3 if level else .36)
    sr = max(4., min(W, H) * (.075 if level else .1))
    glow = sr * 3.2
    cv.obj([], 0)
    y = _hy(Y - 4)
    while y < yw:
        pitch = 1.5 if y < Y + H * .14 else 2. if y < Y + H * .3 else 3.
        segs = [[(X - 4, y), (X + W + 4, y)]]
        dy = y - sun_y
        if abs(dy) < glow:
            half = math.sqrt(glow * glow - dy * dy)
            segs = [[(X - 4, y), (sun_x - half, y)], [(sun_x + half, y), (X + W + 4, y)]]
            # inside the glow: a finer, broken line every other row
            if int((y - Y) / 3) % 2 == 0:
                segs.append([(sun_x - half * .9, y), (sun_x - sr * 1.2, y)])
                segs.append([(sun_x + sr * 1.2, y), (sun_x + half * .9, y)])
        cv.hair(segs)
        y += pitch
    # rays
    nr = 36 if level else 20
    for i in range(nr):
        a = 2 * PI * (i + .5) / nr
        r1 = glow * (1.05 if i % 2 else .7)
        cv.hair([(sun_x + sr * 1.35 * math.cos(a), sun_y + sr * 1.35 * math.sin(a)),
                 (sun_x + r1 * math.cos(a), sun_y + r1 * math.sin(a))])
    disc = C._ell_pts(sun_x, sun_y, sr, sr, 32)[:-1]
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 3, .25))
    # --- clouds: billows painted back to front, each lit on top, ruled in its shade
    banks = []
    if level:
        banks = [(X + W * .36, Y + H * .16, W * .5, H * .08), (X + W * .9, Y + H * .15, W * .34, H * .06),
                 (X + W * .42, Y + H * .4, W * .4, H * .05), (X + W * .06, Y + H * .3, W * .3, H * .05)]
    else:
        banks = [(X + W * .3, Y + H * .2, W * .5, H * .1)]
    for bx, by, bw, bh in banks:
        _cloud(cv, bx + rng.uniform(-.04, .04) * W, by, bw, bh, rng)
    # --- Mt. Hood, framed between the bridge towers
    hx = X + W * (.52 if level else .5)
    hb = yw - H * .05
    hh = H * (.33 if level else .4)
    hw = W * (.36 if level else .55)
    top = (hx, hb - hh)
    left = [top, (hx - hw * .05, hb - hh * .9), (hx - hw * .12, hb - hh * .8), (hx - hw * .2, hb - hh * .62),
            (hx - hw * .26, hb - hh * .55), (hx - hw * .4, hb - hh * .32), (hx - hw * .62, hb - hh * .12), (hx - hw * .9, hb + 2)]
    right = [(hx + hw, hb + 2), (hx + hw * .72, hb - hh * .12), (hx + hw * .44, hb - hh * .3), (hx + hw * .3, hb - hh * .48),
             (hx + hw * .16, hb - hh * .68), (hx + hw * .07, hb - hh * .86), (hx + hw * .02, hb - hh * .97)]
    mtn = left + right
    cv.obj([mtn], 1.)
    ridge = [top, (hx + hw * .03, hb - hh * .7), (hx - hw * .04, hb - hh * .5), (hx + hw * .06, hb - hh * .25), (hx + hw * .12, hb + 2)]
    shade = ridge[::-1] + right
    cv.hair(C.hatch_poly(shade, 60, 1.5, 0))
    cv.hair(ridge)
    # couloirs on the lit snow face, and a light ruling low down for the morning haze
    for k in range(5):
        u = .2 + k * .14
        a = (hx - hw * .05 * u * 4, hb - hh * (1 - u * .6))
        b = (a[0] - hw * .1, a[1] + hh * (.18 + .06 * k))
        cv.hair([a, ((a[0] + b[0]) / 2 + 1, (a[1] + b[1]) / 2), b])
    snowy = hb - hh * .42
    lowface = _clip_y(mtn, hb - hh * .8)
    if len(lowface) > 2:
        cv.hair(C.hatch_poly(lowface, 0, 3, .25))
    # timber below the snowline: close vertical strokes with a ragged top
    forest = _clip_y(mtn, snowy)
    if len(forest) > 2:
        for ln in C.hatch_poly(forest, 90, 1.5, .25):
            (ax, ay), (bx_, by_) = ln
            ya, yb = min(ay, by_), max(ay, by_)
            ya += rng.uniform(0, hh * .12) + max(0, (abs(ax - hx) / hw) * hh * .1)
            if yb - ya > 1:
                cv.hair([(ax, ya), (ax, yb)])
    # --- the far shore: the West Hills ridge, dark with timber
    sh_top = yw - H * .085
    hills = [(X - 6, yw + 1)]
    for i in range(41):
        t = i / 40
        hills.append((X - 6 + (W + 12) * t, sh_top + H * .025 * math.sin(t * 9 + seed % 7) + H * .015 * math.sin(t * 23)))
    hills.append((X + W + 6, yw + 1))
    cv.obj([hills], .5)
    cv.hair(C.hatch_poly(hills, 0, 1.5, .25))
    # tree tips along the crest
    for i in range(int(W / 3)):
        t = (i + .5) / int(W / 3)
        px = X - 6 + (W + 12) * t
        py = sh_top + H * .025 * math.sin(t * 9 + seed % 7) + H * .015 * math.sin(t * 23)
        hgt = rng.uniform(1.5, 3.5)
        cv.hair([(px - 1, py + .5), (px, py - hgt), (px + 1, py + .5)])
    # --- the St. Johns Bridge
    if level:
        yd = yw - H * .045
        xt = [X + W * .28, X + W * .76]
        tt = yw - H * .43
        tw = max(4., W * .032)
        # main cables and suspenders, behind the towers
        cv.obj([], 0)
        cab = [(X - 8, yd - 1)]
        for i in range(1, 11):
            t = i / 10
            cab.append((X - 8 + (xt[0] - X + 8) * t, yd - 1 - (yd - 1 - (tt + tw * .8)) * t ** 1.4))
        span = []
        for i in range(31):
            t = i / 30
            xx = xt[0] + (xt[1] - xt[0]) * t
            sag = 4 * t * (1 - t)
            span.append((xx, tt + tw * .8 + (yd - 4 - tt - tw * .8) * sag))
        tail = [(xt[1] + (X + W + 8 - xt[1]) * (i / 10), tt + tw * .8 + (yd - 1 - tt - tw * .8) * (i / 10) ** 1.4)
                for i in range(11)]
        for dx in (-tw * .25, tw * .25):
            cv.line([(p[0] + dx * (0 if p[0] in (X - 8, X + W + 8) else 1) * 0, p[1]) for p in cab + span + tail])
        xs = xt[0] + 3
        while xs < xt[1] - 2:
            t = (xs - xt[0]) / (xt[1] - xt[0])
            cy_ = tt + tw * .8 + (yd - 4 - tt - tw * .8) * 4 * t * (1 - t)
            if yd - cy_ > 2:
                cv.hair([(xs, cy_), (xs, yd - 1.5)])
            xs += 3
        # the deck: white road edge over a truss band
        deck = [(X - 8, yd - 1.5), (X + W + 8, yd - 1.5), (X + W + 8, yd + 3), (X - 8, yd + 3)]
        cv.obj([deck], 1.)
        cv.hair(C.hatch_poly([(X - 8, yd + .5), (X + W + 8, yd + .5), (X + W + 8, yd + 3), (X - 8, yd + 3)], 90, 1.5, .25))
        # gothic towers: tapering legs, pointed crown with corner pinnacles, lancet openings
        for x in xt:
            b = tw * .62
            tp = [(x - b, yw + 1), (x - tw * .5, tt + tw * .9), (x - tw * .62, tt + tw * .4), (x - tw * .5, tt - tw * .5),
                  (x - tw * .35, tt + tw * .2), (x, tt - tw * 1.1), (x + tw * .35, tt + tw * .2),
                  (x + tw * .5, tt - tw * .5), (x + tw * .62, tt + tw * .4), (x + tw * .5, tt + tw * .9), (x + b, yw + 1)]
            cv.obj([tp], 1.)
            # shaded east half
            sh = [(x + tw * .12, yw + 1), (x + tw * .12, tt - tw * .3), (x + tw * .35, tt + tw * .2), (x + tw * .5, tt - tw * .5),
                  (x + tw * .62, tt + tw * .4), (x + tw * .5, tt + tw * .9), (x + b, yw + 1)]
            cv.hair(C.hatch_poly(sh, 90, 1.5, .25))
            # stacked lancet arches, solid black
            th = yw - tt
            for k, (f0, f1) in enumerate(((.12, .34), (.4, .62))):
                y0, y1 = tt + th * f0, tt + th * f1
                ww = tw * .2
                for sx in (-1, 1):
                    xc = x + sx * tw * .2
                    lan = [(xc - ww, y1), (xc - ww, y0 + ww * 1.6), (xc, y0), (xc + ww, y0 + ww * 1.6), (xc + ww, y1)]
                    cv.obj([lan], .5)
                    yy = y0 + .5
                    while yy < y1:
                        cv.line([(xc - ww, yy), (xc + ww, yy)])
                        yy += .9
            cv.obj([], 0)
            cv.hair([(x - tw * .5, tt + tw * 1.4), (x + tw * .5, tt + tw * 1.4)])
    # --- the river: broken ruled water, darker toward the viewer, the towers' reflections
    cv.obj([[(X - 8, yw), (X + W + 8, yw), (X + W + 8, Y + H + 8), (X - 8, Y + H + 8)]], 0)
    y = _hy(yw + 1)
    while y < Y + H + 6:
        f = (y - yw) / max(1., Y + H - yw)
        pitch = 3. if f < .25 else 2. if f < .6 else 1.5
        x = X - 8 - rng.uniform(0, 12)
        segs = []
        while x < X + W + 8:
            L = rng.uniform(10, 34) * (1.4 - f * .6)
            if abs((x + L / 2) - sun_x) < sr * 1.4 and f < .5:
                L *= .4
            segs.append([(x, y), (x + L, y)])
            x += L + rng.uniform(1.5, 3.5)
        cv.hair(segs)
        y += pitch
    if level:
        for x in xt:
            y = _hy(yw + 2)
            k = 0
            while y < yw + H * .2:
                ww = tw * (.6 - .3 * (y - yw) / (H * .2)) * rng.uniform(.7, 1.1)
                cv.line([(x - ww, y), (x + ww, y)])
                y += 3.
                k += 1
    # --- foreground: the heron in the shallows, reeds before it
    if level:
        hs = H * (.006 if level == 2 else .0054)
        hxp = X + W * (.17 if level == 2 else .16)
        cv_feet_y = Y + H * .95
        _heron(cv, hxp, cv_feet_y, hs, rng)
        _reeds(cv, X + W * .7, X + W * 1.02, Y + H + 2, H * .3, rng, 7 if level == 2 else 5)
        _reeds(cv, X - W * .02, X + W * .08, Y + H + 2, H * .22, rng, 3)
    return cv.svg()


def _cloud(cv, bx, by, bw, bh, rng):
    """a cumulus bank: overlapping billows painted back to front, each lit on its upper left and
    modelled with arcs that follow its round on the shaded lower right; a flat ruled base"""
    bills = []
    nb = max(3, int(bw / max(5., bh * .9)))
    for k in range(nb):
        t = (k + rng.uniform(.25, .75)) / nb
        r = bh * (.45 + .75 * math.sin(PI * t) ** .7) * rng.uniform(.8, 1.15)
        bills.append((bx - bw / 2 + bw * t, by - r * .5 + bh * .2, r))
    for k in range(max(1, nb // 3)):
        t = rng.uniform(.3, .7)
        r = bh * rng.uniform(.65, .9)
        bills.append((bx - bw / 2 + bw * t, by - bh * .45 - r * .3, r))
    base = by + bh * .25
    # paint the upper tier first (it sits behind), then the low billows from the ends inward
    order = bills[nb:] + sorted(bills[:nb], key=lambda b: -abs(b[0] - bx))
    for cx_, cy_, r in order:
        p = _clip_y(C._ell_pts(cx_, cy_, r, r * .92, 36)[:-1], base, keep_below=False)
        if len(p) < 3:
            continue
        cv.obj([p], .5)
        lit = _clip_y(C._ell_pts(cx_ + 1, cy_ + 1, r - 3.5, (r - 3.5) * .92, 30)[:-1], base - 1, keep_below=False)
        if len(lit) > 2 and r > 6:
            cv.hair(C.hatch_poly(lit, 0, 3, 1.75))
        j = 1
        while True:
            rr = r - 2. * j
            if rr < r * .3 or rr < 1.5:
                break
            a0, a1 = math.radians(-35 + j * 9), math.radians(150 - j * 14)
            if a1 - a0 < .3:
                break
            arc = [(cx_ + r * .06 * j + rr * math.cos(t), cy_ + r * .04 * j + rr * .92 * math.sin(t))
                   for t in [a0 + (a1 - a0) * i / 18 for i in range(19)]]
            arc = [q for q in arc if q[1] < base - .5]
            if len(arc) > 1:
                cv.hair(arc)
            j += 1
    und = [(bx - bw * .52, base - bh * .3), (bx + bw * .52, base - bh * .3), (bx + bw * .46, base + .5), (bx - bw * .46, base + .5)]
    cv.obj([und], 0)
    cv.hair(C.hatch_poly(und, 0, 1.5, .25))


def _heron_scroll(cv, root, Hn, face, head_s, rng):
    """a scroll stem that turns into a heron's neck and head: a shaded, tapering acanthus stem
    rising Hn px from `root` in an S, bursting from a leafy collar, the head facing `face`
    (+1 right, -1 left) with crest plume, eye and dagger bill."""
    x0, y0 = root

    def L(u, v):
        return (x0 + face * u * Hn, y0 + v * Hn)
    pts = _bez(L(0, 0), L(-.05, -.25), L(-.42, -.32), L(-.3, -.55), 16)[:-1] + \
        _bez(L(-.3, -.55), L(-.2, -.75), L(.12, -.72), L(.1, -.88), 10)[:-1] + \
        _bez(L(.1, -.88), L(.08, -.96), L(.02, -.98), L(.08, -1.), 6)
    n = len(pts)
    w0 = head_s * 2.6
    ws = [w0 * (1.7 - 1.05 * (i / (n - 1)) ** .6) for i in range(n)]
    R = C._Rib(pts, ws, ws)
    cv.obj([R.outline()], 1.)
    # which side of the ribbon faces away from the light (upper left) changes along the S
    for i0, i1 in ((0, n // 2), (n // 2, n - 1)):
        u0, u1 = i0 / (n - 1), i1 / (n - 1)
        mx = pts[(i0 + i1) // 2]
        nx, ny = R.N[(i0 + i1) // 2]
        sd = 1 if nx * 1 + ny * 1 > 0 else -1     # the normal pointing down-right is the shade
        for sv, mw in ((.2, 9), (.42, 6), (.62, 4), (.8, 3)):
            cv.hair(R.contour(sd * sv, u0, u1, minw=mw))
        cv.hair(R.contour(-sd * .75, u0, u1, minw=6))
        C._shadow(cv, R, sd, w0 * .5, u0 + .02, u1 - .02)
        for k in range(i0 + 2, i1 - 2, 2):
            cv.hair([R.at(k / (n - 1), -sd * .6), R.at((k + 1.3) / (n - 1), -sd * .25)])
    # the leafy collar the neck bursts from
    cu = .16
    base = R.at(cu, 0)
    k0 = int(cu * (n - 1))
    ta = math.atan2(pts[k0 + 1][1] - pts[k0][1], pts[k0 + 1][0] - pts[k0][0])
    for sd in (-1, 1):
        C.acanthus_frond(base[0], base[1], math.degrees(ta + sd * .95), head_s * 20, 3, 30,
                         .9 * sd, 4.5 * sd, rng.randrange(1 << 20), cv=cv)
    C._finger(cv, base[0], base[1], ta + .2 * face, head_s * 12, head_s * 2, -face * .8, -face * 4., 1.)
    # head
    hx, hy = pts[-1]
    hs2 = head_s * 2.2

    def Q(u, v):
        return (hx + face * u * hs2, hy + v * hs2)
    head = [Q(-3, .2), Q(-2.6, -1.4), Q(-1, -2.3), Q(1.4, -2.4), Q(3.4, -1.7), Q(4.6, -.9), Q(16, .1),
            Q(4.6, .9), Q(2.6, 1.6), Q(-.6, 2.2), Q(-2.4, 1.6)]
    cv.obj([head], 1.)
    # the black crown stripe running back into two long plumes
    cv.heavy([Q(3.8, -1.6), Q(1.2, -2.2), Q(-1.2, -2.1), Q(-4, -1.4), Q(-8, .2), Q(-11, 2.6)])
    cv.line([Q(-2.6, -1.2), Q(-6.5, .6), Q(-9.5, 3.6)])
    cv.line([Q(3.4, -1.3), Q(.6, -1.7), Q(-2, -1.5)])
    cv.line(C._ell_pts(*Q(2.6, -.6), max(.7, hs2 * .45), max(.7, hs2 * .45), 8))
    cv.hair([Q(4.6, -.1), Q(15.5, .15)])
    cv.line(C.hatch_poly([Q(4.6, -.9), Q(16, .1), Q(4.6, .9)], 0, 1.5, .25))
    cv.hair(C.hatch_poly([Q(-2.8, .3), Q(1, .5), Q(4.4, .5), Q(2.6, 1.6), Q(-.6, 2.2), Q(-2.4, 1.6)], 0, 2, .25))
    cv.hair([Q(-2.6, .3), Q(1.4, .1), Q(4.2, -.3)])
    return pts[-1]


def _clip_to(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _cart_field(cx, cy, w, h):
    """the cartouche's field outline and its bounding box (mirrors C.cartouche's geometry)"""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b


# ----------------------------------------------------------------------------------------------
# layouts
# ----------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, doy):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("ib", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 4, ry - 4
    field = C._ell_pts(cx, cy, fx, fy, 64)
    o.append(_clip_to(C._uid("ibf", w, h), _d(field, True, 0),
                      _scene(cx - fx, cy - fy, 2 * fx, 2 * fy, seed, doy, 0)))
    o.append(f'<path d="{_d(field, True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    # easter egg: the pinwheel boss under the medallion
    o.append(_pinwheel_boss(cx, cy + ry - 1, 4.5))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, doy):
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
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    if gh > 120:
        hs = max(1.1, min(1.9, gh * .0085))
        for side in (-1, 1):
            root = (cx + side * (cw * .5 + hs * 2.2 * 13), gy1 + 4)
            _heron_scroll(cv, root, gh * .78, -side, hs, rng)
    o.append(C._clip(C._uid("im", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, field_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_field(cx, cy, cw, ch)
    o.append(_clip_to(C._uid("imf", w, h), field_d, _scene(cx - a, cy - b, 2 * a, 2 * b, seed, doy, 1)))
    o.append(f'<path d="{field_d}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    o.append(_pinwheel_boss(cx, h - foot / 2, 5))
    return "".join(o)


def _banner_letters(centre, text, ch):
    """letter `text` along the banner's face centre line"""
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    mid = S[-1] / 2

    def along(off):
        s = mid + off
        for i in range(1, len(S)):
            if S[i] >= s:
                t = (s - S[i - 1]) / max(1e-6, S[i] - S[i - 1])
                p = (centre[i - 1][0] + (centre[i][0] - centre[i - 1][0]) * t,
                     centre[i - 1][1] + (centre[i][1] - centre[i - 1][1]) * t)
                a = math.atan2(centre[i][1] - centre[i - 1][1], centre[i][0] - centre[i - 1][0])
                return p[0], p[1], a
        return centre[-1][0], centre[-1][1], 0.
    return _letter(text, 0, 0, ch, .34, along)


def _layout_tall(w, h, seed, doy, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 470 else 0.
    top_free = 10.
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # a light ruled sky over the crest, so the breakouts never stand on bare paper
    o.append(C.dark_ground((0, 0, w, top_free + 2), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .53, ph * .72
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .155, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    # the supporters: from the lower volutes a stem rises and turns into a heron facing the scene
    hs = max(1.3, min(2.4, ph * .0068))
    sup = C.Canvas()
    Hn = ch * .56
    for side in (-1, 1):
        root = (cx + side * (cw * .5 + r1 * .25), py0 + ph - r1 * 1.3)
        _heron_scroll(sup, root, Hn, -side, hs, rng)
        occ.append(("c", root[0] + side * Hn * .3, root[1] - Hn * .5, Hn * .16))
        occ.append(("c", root[0] - side * hs * 6, root[1] - Hn, hs * 2.2 * 9))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=8, edge=.6, cv=cv)
    cv.extend(main)
    cv.extend(sup)
    o.append(C._clip(C._uid("it", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_field(cx, cy, cw, ch)
    o.append(_clip_to(C._uid("itf", w, h), field_d, _scene(cx - a, cy - b, 2 * a, 2 * b, seed, doy, 2)))
    o.append(f'<path d="{field_d}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 52), True, rng.randrange(1 << 20)))
    bh = min(18., max(13., ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lt = _banner_letters(centre, "THE MORNING EDITION", bh * .5)
    o.append(f'<path d="{"".join(_d(p, tol=.1) for p in lt)}" fill="none" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py + 2, w, h - py - 2), "G"))
    p, (tx, ty, tw_, th_) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: a deep-ruled sunk panel with the date cut in Roman capitals
    o.append(C.dark_ground((tx + 2, ty + 2, tw_ - 3, th_ - 3), "G"))
    yy, mm, dd = _date_parts(ctx)
    date = f"{_roman(dd)} · {_roman(mm)} · {_roman(yy)}"
    lc = min(th_ * .62, 11.)
    lt = _letter(date, tx + tw_ / 2, ty + th_ / 2 + .5, lc, .42)
    o.append(f'<path d="{"".join(_d(p, tol=.1) for p in lt)}" fill="none" stroke="#fff" stroke-width="1.5"/>')
    # easter egg: the right-hand rosette recut as the Blazers pinwheel
    inset = w * .035
    rx = w / 2 + (tw_ / 2 + (w - 3 * inset - tw_) / 4)
    kb = max(5, min(10, ped_h * .11))
    slab = ped_h * .42
    fy = py + kb + slab * .22
    fh = slab - slab * .22
    rr = min(fh * .32, 9)
    o.append(_pinwheel_boss(rx, fy + fh / 2, rr))
    fy2 = py + ped_h
    fh2 = h - fy2
    if fh2 > 14:
        o.append(C.dark_ground((0, fy2, w, fh2 - 2), "G"))
        o.append(C._clip(C._uid("if", w, h, seed), 0, fy2, w, fh2 - 2,
                         C.scroll_band(0, fy2, w, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy2 + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    y, m, d = _date_parts(ctx)
    doy = (m - 1) * 30.4 + d
    seed = (y * 372 + m * 31 + d) % 100003
    if h < 110:
        body = _layout_band(w, h, seed, doy)
    elif h <= 260:
        body = _layout_medium(w, h, seed, doy)
    else:
        body = _layout_tall(w, h, seed, doy, ctx)
    return C.svg_doc(w, h, body)
