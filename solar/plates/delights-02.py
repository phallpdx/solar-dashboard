"""delights-02 -- Artwork of the day.

Today's picture is Rosa Bonheur's "Cattle at Rest on a Hillside in the Alps" (1885), so the plate is
that painting re-cut in bulino: snow peaks under a ruled sky, a dark pine ridge, and piebald cattle
lying on a grassy slope, every hide modelled in contour hatching. It hangs in a carved Codex frame of
acanthus volutes; the ribbon carries the painter's name and the pedestal tablet the picture's title.
Easter egg: Parker's dog lying in the grass among the cattle, and a tiny "P" cut as the painter's
signature in the corner of the canvas."""
import sys
import math
import random
import re
import unicodedata

import engraving_codex as C          # noqa: E402
import engraving_morning as M        # noqa: E402  (stroke-font glyphs)

_n, _d = C._n, C._d
TAU = math.tau


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _cr(pts, closed=True, n=5):
    """Catmull-Rom through pts."""
    m = len(pts)
    out = []
    for i in range(m if closed else m - 1):
        p0 = pts[i - 1] if (closed or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if (closed or i + 2 < m) else p2
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def _cl(x, a=0., b=1.):
    return a if x < a else b if x > b else x


class Mask:
    """1 px raster of a set of polygons (union), for clipping shading lines to a form."""

    def __init__(self, polys):
        xs = [p[0] for q in polys for p in q]
        ys = [p[1] for q in polys for p in q]
        self.x0, self.y0 = int(math.floor(min(xs))) - 1, int(math.floor(min(ys))) - 1
        self.W, self.H = int(max(xs)) - self.x0 + 3, int(max(ys)) - self.y0 + 3
        self.m = [bytearray(self.W) for _ in range(self.H)]
        for q in polys:
            C._fill_mask(q, self.m, self.x0, self.y0, self.W, self.H)

    def has(self, x, y):
        i, j = int(x - self.x0), int(y - self.y0)
        return 0 <= i < self.W and 0 <= j < self.H and self.m[j][i]


CYC4 = (.04, .52, .27, .76)
CYC3 = (.06, .4, .72)


def shade(cv, mask, lines, tone, cyc=CYC4, weight=.5, minrun=1.6):
    """Keep each line where it is inside the mask and the tone there beats its threshold: tone 0 is
    white, 1 is every line (pitch). Lines are pre-sampled at about 1 px."""
    out = []
    nc = len(cyc)
    for i, pl in enumerate(lines):
        thr = cyc[i % nc]
        run = []
        for p in pl:
            if mask.has(p[0], p[1]) and tone(p[0], p[1]) > thr:
                run.append(p)
            else:
                if len(run) > 1 and abs(run[-1][0] - run[0][0]) + abs(run[-1][1] - run[0][1]) > minrun:
                    out.append(run)
                run = []
        if len(run) > 1 and abs(run[-1][0] - run[0][0]) + abs(run[-1][1] - run[0][1]) > minrun:
            out.append(run)
    {.5: cv.hair, 1.: cv.line, 1.5: cv.heavy}[weight](out)


def straight(bb, ang, pitch, step=1.2, phase=0.):
    x0, y0, x1, y1 = bb
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    cs = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pv = [x * vx + y * vy for x, y in cs]
    pu = [x * ux + y * uy for x, y in cs]
    out = []
    v = math.floor((min(pv) - phase) / pitch) * pitch + phase
    while v <= max(pv):
        n = int((max(pu) - min(pu)) / step) + 2
        out.append([(v * vx + (min(pu) + k * step) * ux, v * vy + (min(pu) + k * step) * uy) for k in range(n)])
        v += pitch
    return out


def curved_v(bb, pitch, fx, step=1.2):
    """Lines x = c + fx(y, c) down bb."""
    x0, y0, x1, y1 = bb
    out = []
    c = x0 - (x1 - x0) * .3
    n = int((y1 - y0) / step) + 2
    while c < x1 + (x1 - x0) * .3:
        out.append([(c + fx(y0 + k * step, c), y0 + k * step) for k in range(n)])
        c += pitch
    return out


def curved(bb, pitch, fy, step=1.2):
    """Lines y = c + fy(x, c) across bb."""
    x0, y0, x1, y1 = bb
    out = []
    c = y0 - (y1 - y0) * .5
    n = int((x1 - x0) / step) + 2
    while c < y1 + (y1 - y0) * .5:
        pl = [(x0 + k * step, c + fy(x0 + k * step, c)) for k in range(n)]
        if any(y0 - 2 <= p[1] <= y1 + 2 for p in pl):
            out.append(pl)
        c += pitch
    return out


def _bb(polys, pad=1):
    xs = [p[0] for q in polys for p in q]
    ys = [p[1] for q in polys for p in q]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _ell(cx, cy, rx, ry, n=24, a0=0., a1=TAU):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + (0 if a1 - a0 >= TAU - 1e-9 else 1))]


# ------------------------------------------------------------------------------------------------
# stroke lettering (house glyphs + the capitals they lack)
# ------------------------------------------------------------------------------------------------

_G = dict(M._G)
_G.update({
    "B": (5, [("l", [(0, 0), (1, 0), (1, 8), (0, 8)]), ("s", [(1, 0), (3.2, 0), (4.2, 1), (4.2, 3), (3, 3.9), (1, 3.9)]),
              ("s", [(1, 3.9), (3.4, 3.9), (4.7, 5), (4.7, 6.9), (3.4, 8), (1, 8)])]),
    "S": (4.8, [("s", [(4.3, 1), (2.6, 0), (.9, .6), (.6, 2.2), (1.6, 3.5), (3.4, 4.4), (4.3, 6), (3.8, 7.5), (2, 8), (.4, 7)])]),
    "U": (5.6, [("s", [(.9, 0), (.9, 5.5), (1.6, 7.5), (2.8, 8), (4, 7.5), (4.7, 5.5), (4.7, 0)]),
                ("l", [(0, 0), (1.8, 0)]), ("l", [(3.8, 0), (5.6, 0)])]),
    "K": (5.4, [("l", [(.9, 0), (.9, 8)]), ("l", [(4.8, 0), (.9, 4.6)]), ("l", [(2.2, 3.2), (5, 8)]),
                ("l", [(0, 0), (1.8, 0)]), ("l", [(0, 8), (1.8, 8)])]),
    "Y": (5.4, [("l", [(.3, 0), (2.7, 4), (5.1, 0)]), ("l", [(2.7, 4), (2.7, 8)]), ("l", [(1.6, 8), (3.8, 8)])]),
    "J": (4, [("s", [(3, 0), (3, 6), (2.3, 7.7), (1, 8), (0, 7)]), ("l", [(2, 0), (4, 0)])]),
    "Q": (5.4, [("p", M._oval(2.7, 4, 2.5, 4, 20)), ("l", [(3, 6.4), (5.4, 8.8)])]),
    "Z": (5, [("l", [(.4, 1), (.4, 0), (4.6, 0), (.4, 8), (4.6, 8), (4.6, 7)])]),
    "-": (3.4, [("l", [(.6, 4.4), (2.8, 4.4)])]),
    ",": (2.4, [("l", [(1.3, 7.6), (.8, 9)])]),
    "'": (2, [("l", [(1, 0), (1, 2)])]),
})


def _glyph(ch):
    adv, strokes = _G.get(ch, _G[" "])
    return adv, [M._spline(p, False, 4) if k == "s" else list(p) for k, p in strokes]


def _ascii_upper(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.upper()).strip()


def text_width(s, cap, track=1.3):
    return (sum(_G.get(c, _G[" "])[0] + track for c in s) - track) * cap / 8


def text_on(s, centre, cap, track=1.3):
    """Glyph polylines centred along polyline `centre`, cap height cap."""
    k = cap / 8
    acc = [0.]
    for a, b in zip(centre, centre[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = text_width(s, cap, track)
    pos = acc[-1] / 2 - total / 2
    out = []

    def at(sv):
        sv = _cl(sv, 0, acc[-1] - 1e-6)
        i = max(0, min(len(acc) - 2, next((j for j in range(len(acc) - 1) if acc[j + 1] >= sv), len(acc) - 2)))
        t = (sv - acc[i]) / max(1e-6, acc[i + 1] - acc[i])
        a, b = centre[i], centre[i + 1]
        return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, math.atan2(b[1] - a[1], b[0] - a[0])

    for ch in s:
        adv, polys = _glyph(ch)
        mx, my, ang = at(pos + adv * k / 2)
        ca, sa = math.cos(ang), math.sin(ang)
        for p in polys:
            q = []
            for gx, gy in p:
                lx, ly = (gx - adv / 2) * k, (gy - 4) * k
                q.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            out.append(q)
        pos += (adv + track) * k
    return out


def _poly_path(pls, w):
    d = "".join(_d(p, tol=.1) for p in pls)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>' if d else ""


# ------------------------------------------------------------------------------------------------
# what is on the page today
# ------------------------------------------------------------------------------------------------

def page_info(ctx):
    s = (ctx or {}).get("sample", "") or ""
    title, artist, year = "", "", ""
    m = re.search(r"From the archives\s+(.+?)\s+,\s+(.+?)\s*\(", s)
    if m:
        title, artist = m.group(1), m.group(2)
    m = re.search(r"\)\s+(\d{3,4})\b", s)
    if m:
        year = m.group(1)
    low = s.lower()
    cattle = any(k in low for k in ("cattle", " cow", "cows", " oxen", " ox ", "bull", "herd", "calf", "calves"))
    if not s:
        cattle = True
    return dict(title=_ascii_upper(title) or "ARTWORK OF THE DAY", artist=_ascii_upper(artist),
                year=year, cattle=cattle)


# ------------------------------------------------------------------------------------------------
# the cattle (Bonheur's subject) and the dog (Parker's)
# ------------------------------------------------------------------------------------------------

# a cow lying down, head raised, facing left. u along the body (0 muzzle .. 1 rump), v down, in body lengths
_COW = [(.2, .035), (.27, .07), (.36, .115), (.46, .12), (.6, .155), (.78, .165), (.9, .185), (.975, .26),
        (1., .37), (.975, .465), (.9, .515), (.7, .53), (.5, .532), (.36, .522), (.3, .532), (.2, .542),
        (.135, .528), (.15, .5), (.25, .478), (.27, .41), (.235, .35), (.18, .32), (.1, .35), (.06, .37),
        (.02, .36), (.005, .32), (.03, .23), (.075, .12), (.115, .06), (.16, .035)]
_EAR = [(.17, .075), (.25, .05), (.31, .07), (.27, .105), (.2, .105)]
_HORN = [(.145, .055), (.12, .015), (.095, -.02), (.075, -.045), (.1, -.04), (.135, -.01), (.18, .045)]
_PATCH = [(.62, .3, .13, .1), (.86, .26, .09, .07), (.42, .38, .07, .08), (.13, .14, .05, .06)]


def cow(cv, x, y, L, facing=-1, seed=0, dark=0.):
    """x, y: top-left of the body box (v=0 line); L body length."""
    rng = random.Random(seed)
    U = (lambda u: x + u * L) if facing < 0 else (lambda u: x + (1 - u) * L)

    def P(u, v):
        return (U(u), y + v * L)

    def loc(X, Y):
        u = (X - x) / L
        return (u if facing < 0 else 1 - u), (Y - y) / L

    patches = [(pu + rng.uniform(-.03, .03), pv + rng.uniform(-.02, .02), ru, rv) for pu, pv, ru, rv in _PATCH]
    pitch = 1.5 if L > 60 else 2.
    # cast shadow on the turf, to the right of the beast (light from the upper left)
    sh = _ell(U(.6) + L * .12, y + .535 * L, L * .5, L * .045, 28)
    cv.obj([sh], 0)
    cv.hair(C.hatch_poly(sh, 0, 1.5))
    # horn behind (far horn), body, ear, near horn
    body = [P(*p) for p in _cr(_COW, True, 4)]
    far = [P(u + .03, v + .005) for u, v in _HORN]
    cv.obj([far], .5)
    cv.hair(C.hatch_poly(far, 90, 1.5))
    cv.obj([body], 1.)
    mk = Mask([body])

    def tone(X, Y):
        u, v = loc(X, Y)
        wl = (X - x) / L
        t = .3 + .62 * _cl((v - .15) / .34) ** 1.3 + .15 * wl + dark
        if u < .27:                                                  # head and neck: face lit
            t = .22 + .45 * _cl((v - .04) / .3) + dark
            if u < .07 and v > .24:
                t += .5                      # dark muzzle
        for pu, pv, ru, rv in patches:
            if ((u - pu) / ru) ** 2 + ((v - pv) / rv) ** 2 < 1:
                t += .65
        if v > .47:
            t += .35
        return t

    # barrel contours that arch over the body, and steeper lines on head and neck
    def arch(X, c):
        u, _ = loc(X, c)
        return -L * .07 * math.sin(math.pi * _cl((u - .25) / .78))
    bb = _bb([body])
    shade(cv, mk, curved(bb, pitch, arch), tone)
    # cross-contours wrapping round the girth: they bow toward the rump (away from the light)
    def girth(Yv, c):
        v = (Yv - y) / L
        return facing * -1 * L * .05 * math.sin(math.pi * _cl((v - .1) / .45))
    shade(cv, mk, curved_v(bb, 2., girth), lambda X, Y: tone(X, Y) - .55, (0.05, .3, .55))
    # anatomy: foreleg fold, thigh, ribs, dewlap, back line light
    cv.line([P(u, v) for u, v in _cr([(.33, .53), (.28, .49), (.2, .5), (.16, .515)], False, 4)])
    cv.hair([P(u, v) for u, v in _cr([(.74, .2), (.8, .3), (.83, .42), (.86, .51)], False, 4)])
    cv.line([P(u, v) for u, v in _cr([(.87, .47), (.82, .5), (.75, .515)], False, 4)])
    for k in range(3):
        cv.hair([P(u, v) for u, v in _cr([(.5 + k * .05, .25), (.49 + k * .05, .35), (.5 + k * .05, .44)], False, 3)])
    for k in range(3):
        cv.hair([P(u, v) for u, v in _cr([(.21 + k * .015, .34 + k * .02), (.235 + k * .012, .4 + k * .015)], False, 2)])
    # tail
    tail = [P(u, v) for u, v in _cr([(.99, .3), (1.035, .4), (1.03, .48), (1.0, .52)], False, 4)]
    cv.line(tail)
    tx, ty = tail[-1]
    for k in range(5):
        cv.hair([(tx, ty), (tx + facing * -1 * (k - 2) * .6 - 1, ty + 3)])
    # hooves of the folded legs
    hv = [P(.14, .515), P(.18, .53)]
    cv.heavy(hv)
    # ear, near horn, eye, nostril, mouth
    ear = [P(*p) for p in _cr(_EAR, True, 3)]
    cv.obj([ear], .5)
    cv.hair(C.hatch_poly(ear, 30, 1.5))
    horn = [P(*p) for p in _HORN]
    cv.obj([horn], .5)
    cv.hair([P(.15, .03), P(.13, -.02)])
    ex, ey = P(.115, .14)
    eye = _ell(ex, ey, max(1.2, L * .014), max(.8, L * .009), 10)
    cv.obj([eye], 1.)
    cv.heavy([(ex - .3, ey), (ex + .3, ey)])
    cv.hair([P(.1, .12), P(.14, .125)])
    cv.heavy([P(.022, .315), P(.028, .318)])
    cv.hair([P(.03, .35), P(.09, .345)])
    cv.hair([P(.17, .08), P(.15, .2), P(.2, .31)])      # cheek line
    return body


# a dog lying in the grass, head up, facing right; u 0 tail .. 1 nose, v down, in body lengths
_DOG = [(.02, .44), (.04, .3), (.13, .22), (.3, .2), (.48, .22), (.6, .19), (.66, .07), (.72, -.03),
        (.8, -.07), (.87, -.04), (.94, .0), (1., .045), (.995, .1), (.93, .12),
        (.86, .15), (.82, .24), (.85, .36), (1., .4), (1.04, .45), (1.0, .49), (.7, .5), (.3, .5), (.06, .5)]


def dog(cv, x, y, L, facing=1):
    U = (lambda u: x + u * L) if facing > 0 else (lambda u: x + (1 - u) * L)

    def P(u, v):
        return (U(u), y + v * L)
    sh = _ell(x + L * .62, y + .5 * L, L * .5, L * .05, 20)
    cv.obj([sh], 0)
    cv.hair(C.hatch_poly(sh, 0, 1.5))
    body = [P(*p) for p in _cr(_DOG, True, 4)]
    cv.obj([body], 1.)
    mk = Mask([body])

    def tone(X, Y):
        v = (Y - y) / L
        return .3 + .6 * _cl((v - .2) / .3) + .2 * _cl(-(v - .05) / .1)

    def fur(X, c):
        return L * .012 * math.sin((X - x) / L * 25 + c * .7)
    shade(cv, mk, curved(_bb([body]), 1.5, fur, 1.), lambda a, b: tone(a, b) + .15, CYC4)
    rng = random.Random(int(x * 7 + y))
    for k in range(int(L * .9)):                      # fur flicks along the back and haunch
        u, v = rng.uniform(.05, .8), rng.uniform(.22, .45)
        px, py = P(u, v)
        if mk.has(px, py) and mk.has(px + facing * 2.5, py + 1):
            cv.hair([(px, py), (px + facing * 2.5, py + .8)])
    # ear flap, eye, nose, collar, paw lines, tail curled along the ground
    ear = [P(u, v) for u, v in _cr([(.74, -.04), (.8, -.03), (.79, .08), (.75, .14), (.71, .09)], True, 3)]
    cv.obj([ear], .5)
    cv.hair(C.hatch_poly(ear, 80, 1.5))
    cv.heavy([P(.87, .0), P(.875, .0)])
    cv.heavy([P(.99, .06), P(1.0, .075)])
    cv.line([P(.62, .17), P(.7, .23), P(.8, .23)])
    cv.hair([P(.88, .41), P(.88, .48)])
    cv.hair([P(.94, .42), P(.94, .48)])
    cv.line([P(u, v) for u, v in _cr([(.03, .4), (-.03, .45), (.05, .5), (.25, .49)], False, 4)])
    return body


# ------------------------------------------------------------------------------------------------
# the painting: Alps, sky, pine ridge, meadow, herd
# ------------------------------------------------------------------------------------------------

def scene(bx, by, bw, bh, clip_d, seed, info, small=False):
    rng = random.Random(seed)
    cv = C.Canvas()
    X = lambda u: bx + u * bw
    Y = lambda v: by + v * bh
    box = [(bx - 2, by - 2), (bx + bw + 2, by - 2), (bx + bw + 2, by + bh + 2), (bx - 2, by + bh + 2)]
    bb = (bx - 2, by - 2, bx + bw + 2, by + bh + 2)

    # sky: ruled, darker at the zenith, with soft clouds left open
    clouds = [(.16 + rng.uniform(-.03, .03), .14, .1), (.27, .1, .07), (.08, .2, .06),
              (.78 + rng.uniform(-.03, .03), .1, .09), (.88, .15, .07)]

    def sky(px, py):
        u, v = (px - bx) / bw, (py - by) / bh
        t = max(.2, .85 - .75 * v)
        for cu, cvv, r in clouds:
            dd = ((u - cu) / (r * 1.5)) ** 2 + ((v - cvv) / r) ** 2
            if dd < 1:
                t = .08 + (.4 if v > cvv + r * .2 else 0) + .5 * dd ** 3
        return t
    cv.obj([box], 0)
    shade(cv, Mask([box]), straight(bb, 0, 1.5, 1.5), sky)

    # the far Alps: snow peaks, lit faces left open, shadow faces cut deep
    ridge_u = [0, .05, .1, .15, .2, .25, .3, .34, .38, .43, .48, .53, .58, .63, .68, .72, .76, .81, .86, .91, .95, 1]
    ridge_v = [.4, .36, .3, .32, .23, .17, .12, .19, .17, .27, .24, .3, .21, .13, .07, .14, .12, .23, .2, .28, .3, .34]
    ridge_v = [v + rng.uniform(-.015, .015) for v in ridge_v]
    rp = [(X(u), Y(v)) for u, v in zip(ridge_u, ridge_v)]
    mtn = rp + [(X(1) + 2, Y(.62)), (X(0) - 2, Y(.62))]
    cv.obj([mtn], 1.)
    mm = Mask([mtn])

    def ridge_at(px):
        u = _cl((px - bx) / bw, 0, .9999)
        i = max(0, min(len(ridge_u) - 2, next(j for j in range(len(ridge_u) - 1) if ridge_u[j + 1] >= u)))
        t = (u - ridge_u[i]) / (ridge_u[i + 1] - ridge_u[i])
        return i, ridge_v[i] + (ridge_v[i + 1] - ridge_v[i]) * t

    peaks = [i for i in range(1, len(rp) - 1) if ridge_v[i] < ridge_v[i - 1] and ridge_v[i] < ridge_v[i + 1]]
    vals = [0] + [i for i in range(1, len(rp) - 1) if ridge_v[i] > ridge_v[i - 1] and ridge_v[i] > ridge_v[i + 1]] + [len(rp) - 1]

    def mtone(px, py):
        v = (py - by) / bh
        _, rv = ridge_at(px)
        depth = v - rv
        # which mountain: nearest peak; its shadow face lies right of a line slanting down-right
        best = min(peaks, key=lambda i: abs(px - rp[i][0]) + .3 * abs(py - rp[i][1]))
        bx_ = rp[best][0] + (py - rp[best][1]) * .45
        lit = px < bx_
        t = .14 if lit else .95
        if depth < .06:
            t -= .14          # snow cap
        return t + .4 * _cl((v - .4) / .2)
    shade(cv, mm, straight(_bb([mtn]), 62, 1.5), mtone)
    shade(cv, mm, straight(_bb([mtn]), 150, 2.), lambda a, b: mtone(a, b) - .4, (.05, .3))
    # couloirs and rock ribs falling from the peaks
    for i in range(1, len(rp) - 1):
        if ridge_v[i] < ridge_v[i - 1] and ridge_v[i] < ridge_v[i + 1]:
            px, py = rp[i]
            for k in range(3 if not small else 1):
                pts = [(px, py)]
                ang = math.radians(100 + k * 25 + rng.uniform(-8, 8))
                for s in range(6):
                    lx, ly = pts[-1]
                    a2 = ang + rng.uniform(-.4, .4)
                    pts.append((lx + math.cos(a2) * bh * .03, ly + math.sin(a2) * bh * .03))
                cv.hair(pts)

    # the dark pine ridge across the middle distance
    hill_v = lambda u: .44 + .05 * math.sin(u * 5.3 + 1.2) + .03 * math.sin(u * 13 + seed % 7)
    hill = [(X(i / 40), Y(hill_v(i / 40))) for i in range(41)] + [(X(1) + 2, Y(.75)), (X(0) - 2, Y(.75))]
    cv.obj([hill], 1.)
    hm = Mask([hill])
    shade(cv, hm, curved(_bb([hill]), 1.5, lambda px, c: (Y(hill_v((px - bx) / bw)) - Y(.44)) * .8),
          lambda a, b: .9)
    shade(cv, hm, straight(_bb([hill]), 60, 2.), lambda a, b: .5 + (b - by) / bh, (.6, .8))
    # pines standing along the ridge and down its face
    nt = 18 if not small else 7
    th = bh * (.07 if not small else .1)
    for k in range(nt):
        u = (k + rng.uniform(.1, .9)) / nt
        base = Y(hill_v(u)) + rng.uniform(.005, .04) * bh
        hh = th * rng.uniform(.75, 1.2)
        cx = X(u)
        tiers = []
        for t in range(4):
            yt = base - hh * (t / 4)
            wt = hh * .32 * (1 - t / 4.6)
            tiers += [(cx - wt, yt), (cx - wt * .3, yt - hh * .2)]
        tree = tiers + [(cx, base - hh * 1.05)] + [(2 * cx - p[0], p[1]) for p in tiers[::-1]]
        cv.obj([tree], .5)
        cv.hair([(cx + .7, base - hh * 1.0), (cx + .7, base)])
        cv.hair(C.hatch_poly(tree, 0, 1.5))
        cv.hair([(p[0], p[1]) for p in C.hatch_poly([q for q in tree if q[0] >= cx - .2] or tree, 90, 1.5)])

    # the meadow the herd rests on, rising to the left
    crest = lambda u: .6 - .07 * _cl(1 - u) ** 1.5 + .02 * math.sin(u * 7 + seed % 5)
    mead = [(X(i / 40), Y(crest(i / 40))) for i in range(41)] + [(X(1) + 2, Y(1) + 2), (X(0) - 2, Y(1) + 2)]
    cv.obj([mead], 1.)
    md = Mask([mead])
    shade(cv, md, curved(_bb([mead]), 2., lambda px, c: (Y(crest((px - bx) / bw)) - Y(.6)) * _cl(1 - (c - Y(.6)) / (bh * .5))),
          lambda a, b: .14 + .9 * _cl(((b - by) / bh - .74) / .26) ** 1.5)
    # tufts of grass, denser toward the front
    for k in range(int(bw * bh / (330 if not small else 500))):
        u, v = rng.random(), rng.random()
        v = crest(u) + .02 + (1 - crest(u)) * v ** .7
        gx, gy = X(u), Y(v)
        sz = 1.5 + 5 * (v - .6) / .4
        lean = rng.uniform(-.3, .3)
        for j in range(-2, 3):                       # a tuft: blades fanning from one root
            a = -math.pi / 2 + j * .32 + lean
            cv.hair([(gx, gy), (gx + math.cos(a) * sz * .5 + lean, gy + math.sin(a) * sz * .55),
                     (gx + math.cos(a) * sz * (1 - .1 * abs(j)) + lean * 2, gy + math.sin(a) * sz * (1 - .15 * abs(j)))])
    # a boulder in the near grass (left)
    rx, ry, rr = X(.06), Y(.9), bw * .07
    rock = [(rx + rr * math.cos(a) * (1 + .15 * math.sin(3 * a)), ry + rr * .6 * math.sin(a) - (rr * .25 if math.sin(a) < 0 else 0))
            for a in [TAU * i / 18 for i in range(18)]]
    if not small:
        cv.obj([rock], 1.)
        rmk = Mask([rock])
        shade(cv, rmk, straight(_bb([rock]), 45, 1.5), lambda a, b: .15 + .9 * _cl((a - rx + rr * .3) / rr) + .4 * _cl((b - ry) / rr))
        shade(cv, rmk, straight(_bb([rock]), -45, 2.), lambda a, b: .6 * _cl((a - rx) / rr) + .5 * _cl((b - ry) / rr) - .2, (.2, .5))

    # the herd
    S = min(bw, bh * 1.2)
    L1 = S * .5
    if info.get("cattle", True):
        if small:
            L = S * .62
            cow(cv, X(.38) - L * .5, Y(.97) - L * .535, L, -1, seed)
        else:
            L2 = S * .3
            cow(cv, X(.6), Y(crest(.72) + .07) - L2 * .53, L2, -1, seed + 3, .08)
            L3 = S * .22
            cow(cv, X(.4) - L3, Y(crest(.38) + .05) - L3 * .53, L3, 1, seed + 7, .12)
            cow(cv, X(.5) - L1 * .85, Y(.88) - L1 * .535, L1, 1, seed + 1)
    if small and bw > 70:
        Ld = S * .2
        dog(cv, X(.72), Y(.97) - Ld * .5, Ld, 1)
    elif small:
        cv.obj([], 0)
        cv.line(text_on("P", [(X(.8) - 3, Y(.84)), (X(.8) + 3, Y(.84))], 4.5))
    if not small:
        Ld = S * .19
        dog(cv, X(.5) + L1 * .3, Y(.875) - Ld * .5, Ld, -1)
        # the painter's signature, lower right: a "P" monogram cut in the turf
        sg = text_on("P", [(X(.9) - 4, Y(.9)), (X(.9) + 4, Y(.9))], 6)
        cv.obj([], 0)
        cv.line(sg)
        cv.hair([(X(.9) - 3.5, Y(.9) + 4.2), (X(.9) + 5, Y(.9) + 3.6)])
    cid = C._uid("sc", bx, by, bw, bh, seed)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{cv.svg()}</g>'


# ------------------------------------------------------------------------------------------------
# the painter's crest (palette and crossed brushes) and an Alpine cowbell
# ------------------------------------------------------------------------------------------------

def _brush(cv, x0, y0, x1, y1, wd):
    """A paintbrush from handle end (x0, y0) to bristle tip (x1, y1)."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux

    def P(t, s):
        return (x0 + ux * t * L + nx * s, y0 + uy * t * L + ny * s)
    handle = [P(0, -wd * .35), P(.66, -wd * .5), P(.66, wd * .5), P(0, wd * .35)]
    cv.obj([handle], 1.)
    cv.hair([P(.02, wd * .1), P(.64, wd * .2)])
    cv.hair([P(.02, wd * .22), P(.64, wd * .34)])
    ferr = [P(.66, -wd * .55), P(.8, -wd * .6), P(.8, wd * .6), P(.66, wd * .55)]
    cv.obj([ferr], 1.)
    for k in range(5):
        t = .68 + k * .025
        cv.hair([P(t, -wd * .55), P(t, wd * .55)])
    tip = [P(.8, -wd * .6), P(.9, -wd * .7), P(1., 0), P(.9, wd * .7), P(.8, wd * .6)]
    cv.obj([tip], 1.)
    for k in range(-2, 3):
        cv.hair([P(.81, wd * .22 * k), P(.97, wd * .06 * k)])


def painter_crest(cx, cy, size, seed=0):
    """A painter's palette, thumb hole and paint dabs, with two brushes crossed behind it."""
    rng = random.Random(seed)
    cv = C.Canvas()
    rx, ry = size * .5, size * .32
    for sd in (-1, 1):
        _brush(cv, cx + sd * rx * 1.25, cy + ry * 1.15, cx - sd * rx * 1.15, cy - ry * 1.9, max(3., size * .07))
    an = math.radians(40)
    outline = []
    for i in range(72):
        a = TAU * i / 72
        dn = math.atan2(math.sin(a - an), math.cos(a - an))
        r = 1 - .33 * math.exp(-(dn / .32) ** 2) + .04 * math.sin(3 * a)
        outline.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    cv.obj([outline], 1.5)
    mk = Mask([outline])
    # wood grain: the palette's own contour repeated inward, darker toward the lower right
    rings = []
    for k in range(1, int(ry / 1.5)):
        f = 1 - k * 1.5 / ry
        ring = [(cx + (px - cx) * f + (1 - f) * rx * .15, cy + (py - cy) * f - (1 - f) * ry * .1) for px, py in outline]
        rings.append(ring + [ring[0]])
    shade(cv, mk, rings, lambda X, Y: .25 + .55 * _cl(((X - cx) / rx + (Y - cy) / ry + .3) / 1.6), CYC3)
    hole = _ell(cx + rx * .42, cy + ry * .18, rx * .12, ry * .16, 14)
    cv.obj([hole], 1.)
    cv.line(C.hatch_poly(hole, 0, 1.5))
    for k in range(6):
        a = math.radians(160 + k * 38 + rng.uniform(-6, 6))
        px, py = cx + rx * .7 * math.cos(a), cy + ry * .64 * math.sin(a)
        dr = size * rng.uniform(.06, .08)
        dab = [(px + dr * math.cos(t) * (1 + .18 * math.sin(3 * t + k)), py + dr * .8 * math.sin(t) * (1 + .18 * math.sin(3 * t + k)))
               for t in [TAU * i / 14 for i in range(14)]]
        cv.obj([dab], 1.)
        ang = (0, 45, 90, -45, 0, 90)[k]
        cv.hair(C.hatch_poly(dab, ang, (1.5, 2., 1.5, 3., 3., 2.)[k]))
        if k % 2 == 0:
            cv.hair(C.hatch_poly(dab, ang + 90, 2.))
        cv.hair([(px - dr * .4, py - dr * .35), (px - dr * .1, py - dr * .5)])
    return cv.svg()


def cowbell(cx, top, size):
    """A Swiss cowbell on its strap, hanging from top."""
    cv = C.Canvas()
    sw = size * .26
    strap = [(cx - sw / 2, top), (cx + sw / 2, top), (cx + sw * .3, top + size * .2), (cx - sw * .3, top + size * .2)]
    cv.obj([strap], 1.)
    cv.hair(C.hatch_poly(strap, 0, 1.5))
    cv.line([(cx - sw / 2 + 1, top + size * .05), (cx + sw / 2 - 1, top + size * .05)])
    by = top + size * .18
    tw, bw_, bh = size * .4, size * .78, size * .6
    dome = size * .12
    side = [(cx + tw / 2 + (bw_ - tw) / 2 * (t / 10) ** 2.6, by + dome + (bh - dome) * t / 10) for t in range(11)]
    bell = ([(cx + tw / 2 * math.cos(a), by + dome - dome * math.sin(a)) for a in [math.pi * (1 - i / 10) for i in range(11)]][:-1] +
            side + [(cx + bw_ / 2 * math.cos(a), by + bh + size * .06 * math.sin(a)) for a in [math.pi * i / 10 for i in range(1, 10)]] +
            [(2 * cx - px, py) for px, py in side[::-1]])
    cv.obj([bell], 1.)
    mk = Mask([bell])
    lines = []
    for k in range(-14, 15):
        f = k / 14
        lines.append([(cx + f * (tw / 2 + (bw_ - tw) / 2 * (max(0, j) / 10) ** 2.6 - (tw * .25 if j < 0 else 0)), by + bh * j / 10 + size * .06 * math.sqrt(max(0, 1 - f * f)) * (max(0, j) / 10) ** 4)
                      for j in range(-2, 11)])
    shade(cv, mk, lines, lambda X, Y: .2 + 1.4 * abs((X - cx) / bw_ + .15) + .2 * (Y - by) / bh)
    cv.line([(cx - tw / 2 - .5, by + dome + 1.5), (cx + tw / 2 + .5, by + dome + 1.5)])
    cv.hair([(cx - bw_ * .4, by + bh * .72), (cx + bw_ * .4, by + bh * .72)])
    cl = _ell(cx + size * .03, by + bh + size * .07, size * .07, size * .07, 10)
    cv.obj([cl], 1.)
    cv.line(C.hatch_poly(cl, 0, 1.5))
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# frame layouts (adapted from the house frame so the picture fills the whole field)
# ------------------------------------------------------------------------------------------------

def _field(cx, cy, w, h, inset=4.5):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6 - inset, h / 2 - bw * 1.6 - inset
    pts = C._superellipse(cx, cy, a, b)
    return _d(pts, True, .1), (cx - a, cy - b, 2 * a, 2 * b)


def layout_band(w, h, seed, info):
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
    clip = _d(_ell(cx, cy, rx - 4, ry - 4, 48), True, 0)
    o.append(scene(cx - rx + 4, cy - ry + 4, 2 * rx - 8, 2 * ry - 8, clip, seed, info, small=True))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def layout_medium(w, h, seed, info):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.5)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    clip, (fx, fy, fw, fh) = _field(cx, cy, cw, gh + 4)
    o.append(scene(fx, fy, fw, fh, clip, seed, info, small=fh < 90))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, info, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .66
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    clip, (fx, fy, fw, fh) = _field(cx, cy, cw, ch)
    o.append(scene(fx, fy, fw, fh, clip, seed, info))
    crest_seed = rng.randrange(1 << 20)
    bh = min(17, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(cowbell(cx, cy + ch * .47 + bh * .2, min(50., ph * .12)))
    o.append(bsvg)
    o.append(painter_crest(cx, cy - ch / 2 - 2, min(96., ch * .36 + top_free), crest_seed))
    name = info["artist"] or "ARTWORK OF THE DAY"
    if info["year"]:
        name += " · " + info["year"]
    cap = min(bh * .5, 8.)
    face = centre[3:-3]
    flen = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(face, face[1:]))
    cap = min(cap, cap * flen * .92 / max(1, text_width(name, cap)))
    o.append(_poly_path(text_on(name, [(p[0], p[1] + .3) for p in face], cap), 1))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, tth) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    title = info["title"]
    tcap = min(tth * .5, 9.)
    tcap = min(tcap, tcap * tw * .9 / max(1, text_width(title, tcap)))
    o.append(_poly_path(text_on(title, [(tx, ty + tth / 2 + .5), (tx + tw, ty + tth / 2 + .5)], tcap), 1))
    fy2 = py + ped_h
    fh2 = h - fy2
    if fh2 > 14:
        o.append(C.dark_ground((w * .06, fy2, w * .88, fh2 - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy2, w * .88, fh2 - 2,
                         C.scroll_band(w * .06, fy2, w * .88, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy2 + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    info = page_info(ctx)
    seed = sum(map(ord, ctx.get("date", ""))) + 1885
    if h < 110:
        body = layout_band(w, h, seed, info)
    elif h <= 260:
        body = layout_medium(w, h, seed, info)
    else:
        body = layout_tall(w, h, seed, info)
    return C.svg_doc(w, h, C.dark_ground((0, 0, w, h), "L") + body)
