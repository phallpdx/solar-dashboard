"""roads-04 "Is the mountain out?": the view east from Sauvie Island across the Columbia to the three
Cascade volcanoes (St. Helens NE, Adams ENE, Hood ESE). When the page says they are hidden, the
peaks stand as ghosts behind a carved cloud bank; when out, they are cut in full relief.
Easter egg: a great blue heron of Sauvie Island fishing in the shallows (and a P cut in a stone)."""
import sys
import math
import random
import engraving_codex as C

TAU = 2 * math.pi


def _peak_profile(cx, base, hw, ht, kind, rng, n=60):
    """Left base -> right base silhouette of one volcano."""
    pts = []
    for i in range(n + 1):
        u = -1 + 2 * i / n
        a = abs(u)
        if kind == "hood":       # sharp horn, steep upper cone, long skirts
            k = (1 - a) ** 2.2 * .55 + (1 - a) ** .9 * .45
            if u > 0:
                k *= .97
            j = .025 * math.sin(u * 23) * (1 - a)
        elif kind == "helens":   # truncated, crater notch open to the north (left)
            k = min((1 - a) ** 1.25, .78)
            if -.12 < u < .08:
                k -= .07 * math.cos((u + .02) / .1 * math.pi / 2)
            j = .02 * math.sin(u * 31) * (1 - a)
        else:                     # adams: broad dome
            k = (1 - a ** 1.6) ** 1.8
            j = .02 * math.sin(u * 19 + 1) * (1 - a)
        pts.append((cx + u * hw, base - ht * max(0., k + j)))
    return pts


def _crossings(prof, ys):
    """Indices bracketing where the profile rises above ys and drops below it again."""
    i0 = next((i for i, p in enumerate(prof) if p[1] < ys), None)
    i1 = next((i for i in range(len(prof) - 1, -1, -1) if prof[i][1] < ys), None)
    return i0, i1


def _lerp_y(a, b, ys):
    t = (ys - a[1]) / ((b[1] - a[1]) or 1e-6)
    return (a[0] + (b[0] - a[0]) * t, ys)


def _snow_poly(prof, ys, rng, ragged):
    i0, i1 = _crossings(prof, ys)
    if i0 is None or i1 is None or i1 <= i0:
        return None
    top = [_lerp_y(prof[i0 - 1], prof[i0], ys)] + prof[i0:i1 + 1] + [_lerp_y(prof[i1 + 1], prof[i1], ys)]
    x0, x1 = top[0][0], top[-1][0]
    m = max(3, int((x1 - x0) / 3))
    low = []
    for k in range(m, -1, -1):
        x = x0 + (x1 - x0) * k / m
        dy = ragged * (rng.random() * 1.6 - .2) * (1 if k % 2 else -.4)
        low.append((x, ys + dy))
    return top + low[1:-1]


def _face(prof, si, base, drop):
    """Shadow (east) face: summit index si down the right flank, back up a ridge line."""
    sx, sy = prof[si]
    return prof[si:] + [(sx + drop, base)]


def _mountain(cv, prof, base, kind, veiled, rng, snow_frac):
    si = min(range(len(prof)), key=lambda i: prof[i][1])
    sx, sy = prof[si]
    ht = base - sy
    hw = (prof[-1][0] - prof[0][0]) / 2
    poly = prof + [(prof[-1][0], base + 1), (prof[0][0], base + 1)]
    ys = sy + ht * snow_frac
    snow = _snow_poly(prof, ys, rng, max(1.5, ht * .06))
    if veiled:
        # a ghost behind the mist: the sky's own rules run on across it, the silhouette is dotted
        cv.obj([poly], 0)
        cv.hair([[(prof[i][0], prof[i][1]), (prof[i + 1][0], prof[i + 1][1])] for i in range(0, len(prof) - 1, 2)])
        y = math.floor(sy) + .25
        lines = C.hatch_poly(poly, 0, 3, .25)
        cv.hair(lines)
        face = _face(prof, si, base, hw * .18)
        cv.hair(C.hatch_poly(face, 45, 3))
        return
    cv.obj([poly], 1.)
    # west face in light bulino along the slope, east face dense and cross-cut
    cv.hair(C.hatch_poly(poly, 60 if kind != "adams" else 30, 3))
    face = _face(prof, si, base, hw * .18)
    cv.hair(C.hatch_poly(face, -45, 2))
    cv.hair(C.hatch_poly(face, 45, 3))
    if snow:
        cv.obj([snow], .5)
        cv.hair(C.hatch_poly(snow, 0, 3, .25))
        sface = [p for p in snow if p[0] >= sx - .01]
        if len(sface) > 2:
            cv.hair(C.hatch_poly([(sx, sy)] + sface, -45, 3))
        # glaciers and ridges: dark cuts falling from the summit
        for k in range(-3, 4):
            if k == 0:
                continue
            x2 = sx + k * hw * .09
            cv.line([(sx + k * .6, sy + 2), (x2, ys + ht * .04 * (1 + abs(k) % 2))])


def _puff(cv, cx, cy, r, shade=True):
    circ = C._ell_pts(cx, cy, r, r * .82, 36)
    cv.obj([circ], 1.)
    if not shade:
        return
    # rolled body: hair rules everywhere below the lit crown, denser rules in the turned-under belly
    body = [p for p in circ if p[1] > cy - r * .35] or circ
    cv.hair(C.hatch_poly(body, 0, 3, .25))
    belly = [p for p in circ if p[1] > cy + r * .25]
    if len(belly) > 2:
        cv.hair(C.hatch_poly(belly, 0, 3, 1.75))
    # the curl of the crown
    arc = [(cx + r * .8 * math.cos(a), cy + r * .66 * math.sin(a)) for a in [math.pi * (1.15 + .5 * i / 12) for i in range(13)]]
    cv.hair(arc)


def _cloud_bank(cv, x0, x1, y, h, rng, n):
    """A rolling cumulus bank: back row first, front row last, every puff overlapping its neighbours."""
    for row, (dy, rs) in enumerate(((-.35, .8), (0., 1.), (.35, 1.1))):
        k = n + row
        for i in range(k):
            t = (i + .5 + rng.uniform(-.3, .3)) / k
            cx = x0 + (x1 - x0) * t
            r = h * .38 * rs * rng.uniform(.75, 1.2)
            _puff(cv, cx, y + h * dy + rng.uniform(-.1, .1) * h, r)


def _fir(cv, x, base, hgt, dark=True):
    w = hgt * .36
    pts = [(x, base - hgt)]
    tiers = 4
    for i in range(1, tiers + 1):
        f = i / tiers
        pts.append((x + w * f, base - hgt + hgt * f * .92))
        pts.append((x + w * f * .45, base - hgt + hgt * f * .92 - .5))
    pts += [(x + .6, base), (x - .6, base)]
    for i in range(tiers, 0, -1):
        f = i / tiers
        pts.append((x - w * f * .45, base - hgt + hgt * f * .92 - .5))
        pts.append((x - w * f, base - hgt + hgt * f * .92))
    cv.obj([pts], .5)
    cv.hair(C.hatch_poly(pts, 45, 1.5 if dark else 3))


def _ribbon(cl, w0, w1):
    """Closed polygon of a stroke along centre line cl, width tapering w0 -> w1."""
    L, R = [], []
    n = len(cl)
    for i, (x, y) in enumerate(cl):
        a = cl[max(0, i - 1)]
        b = cl[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        w = (w0 + (w1 - w0) * i / max(1, n - 1)) / 2
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    return L + R[::-1], L, R


def _bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def _heron(cv, x, y, s, flip=False):
    """Great blue heron wading, feet at (x, y), s = height in px. Faces right unless flip."""
    f = -1 if flip else 1

    def P(u, v):
        return (x + f * u * s, y - v * s)
    # legs
    cv.obj([], 0)
    cv.line([P(-.02, .0), P(-.03, .36)])
    cv.line([P(.06, .0), P(.03, .36)])
    # body: a tilted teardrop with the drooping plumes behind
    body = [P(.0, .34), P(-.16, .36), P(-.3, .4), P(-.38, .44)]
    top = _bez(P(-.38, .44), P(-.25, .62), P(.05, .66), P(.16, .55), 14)
    bot = _bez(P(.16, .55), P(.18, .45), P(.1, .36), P(.0, .34), 10)
    bpoly = body[::-1][:-1] + top + bot
    cv.obj([bpoly], 1.)
    cv.hair(C.hatch_poly(bpoly, -30 * f, 1.5))
    for k in range(4):   # wing coverts
        cv.hair(_bez(P(.12 - k * .05, .58 - k * .02), P(-.02 - k * .05, .56 - k * .03), P(-.18 - k * .04, .48 - k * .02), P(-.36, .43), 10))
    # neck S-curve
    cl = _bez(P(.12, .56), P(.24, .7), P(.06, .78), P(.13, .9), 14)
    neck, Ln, Rn = _ribbon(cl, .07 * s, .045 * s)
    cv.obj([neck], 1.)
    cv.hair(C.hatch_poly(neck, 90, 3, .25))
    # head and dagger bill
    hx, hy = P(.15, .92)
    head = C._ell_pts(hx, hy, .05 * s, .035 * s, 16)
    cv.obj([head], 1.)
    bill = [P(.18, .935), P(.36, .9), P(.18, .895)]
    cv.obj([bill], .5)
    cv.hair([P(.19, .915), P(.34, .9)])
    crest = [P(.12, .945), P(-.04, .95), P(.1, .925)]
    cv.obj([crest], .5)
    cv.hair(C.hatch_poly(crest, 0, 1.5))
    ex, ey = P(.165, .925)
    cv.obj([C._ell_pts(ex, ey, .6, .6, 8)], 1.)
    # ripples round the legs
    for k, r in enumerate((.1, .17)):
        cv.hair([P(-.0 - r, .0 - k * .01), P(.02 + r, .0 - k * .01)])


def _water(cv, x0, x1, y0, y1, rng):
    """The Columbia: the far shore's reflection in close rules, then long broken rules with a
    heavier stroke on the wave backs, opening toward the near bank."""
    poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    cv.obj([poly], 0)
    y = math.floor(y0) + .25
    while y < y1:
        d = (y - y0) / max(1., y1 - y0)
        pitch = 1.5 if d < .1 else 2
        x = x0 - rng.uniform(0, 20)
        while x < x1:
            seg = rng.uniform(10, 40)
            gap = rng.uniform(1.5, 3.5) if d > .1 else 1.2
            q = [(max(x0, x), y), (min(x1, x + seg), y)]
            if q[1][0] > q[0][0]:
                (cv.line if (d > .25 and rng.random() < .12) else cv.hair)(q)
            x += seg + gap
        y += pitch


def _ridge(cv, x0, x1, base, top_fn, rng, firs=True, dark=True):
    n = 60
    edge = [(x0 + (x1 - x0) * i / n, top_fn(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]
    poly = edge + [(x1, base), (x0, base)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 45, 1.5 if dark else 2))
    if dark:
        cv.hair(C.hatch_poly(poly, -45, 3))
    if firs:
        x = x0 + rng.uniform(1, 4)
        while x < x1:
            hgt = rng.uniform(5, 9)
            _fir(cv, x, top_fn(x) + 2, hgt, dark)
            x += rng.uniform(3.5, 7)


def _hidden(ctx):
    s = ((ctx or {}).get("sample") or "").lower()
    if "hidden" in s and " out" not in s.split("hidden")[0][-40:]:
        return True
    if "visible" in s or "are out" in s or "is out" in s:
        return False
    return "hidden" in s


def _monogram(cv, x, y, s):
    """A tiny P cut into a river stone (Parker's mark)."""
    stone = C._ell_pts(x, y, s * .8, s * .55, 18)
    cv.obj([stone], 1.)
    cv.hair(C.hatch_poly(stone, 45, 2))
    cv.obj([[(x - s * .28, y + s * .4), (x - s * .28, y - s * .4), (x + s * .2, y - s * .4), (x + s * .3, y - s * .15),
             (x + s * .2, y + .05 * s), (x - s * .1, y + .05 * s), (x - s * .1, y + s * .4)]], .5)



# ----------------------------------------------------------------------------------------------
# path lettering: a single-stroke roman capital on a 4 x 6 grid
# ----------------------------------------------------------------------------------------------

_GL = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "D": [[(0, 0), (0, 6), (2.2, 6), (3.6, 4.8), (4, 3), (3.6, 1.2), (2.2, 0), (0, 0)]],
    "E": [[(3.6, 0), (0, 0), (0, 6), (3.6, 6)], [(0, 3), (2.8, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 0), (1, 6)]],
    "L": [[(0, 0), (0, 6), (3.4, 6)]],
    "M": [[(0, 6), (0, 0), (2.5, 6), (5, 0), (5, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(2, 0), (3.4, .5), (4.1, 2), (4.1, 4), (3.4, 5.5), (2, 6), (.6, 5.5), (-.1, 4), (-.1, 2), (.6, .5), (2, 0)]],
    "S": [[(3.6, .8), (2.6, 0), (1.2, 0), (.2, .8), (.2, 2), (1.2, 2.8), (2.8, 3.2), (3.8, 4), (3.8, 5.2), (2.8, 6), (1.2, 6), (.2, 5.2)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 4.4), (.7, 5.6), (2, 6), (3.3, 5.6), (4, 4.4), (4, 0)]],
    "?": [[(.2, 1.2), (1, .1), (2.6, 0), (3.6, .9), (3.6, 2.1), (2, 3.1), (2, 4.4)], [(2, 5.6), (2, 6)]],
    "·": [[(1, 2.9), (1, 3.1)]],
}
_ADV = {"I": 2.2, "M": 6.2, " ": 2.6, "·": 2.2, "?": 4.8}


def _text_w(s, k):
    return sum(_ADV.get(c, 5.2) for c in s) * k - 1.2 * k


def _letter_along(cv, s, pts, cap, heavy=False):
    """Letter s in capitals cap px tall, centred along the polyline pts (baseline under centre)."""
    k = cap / 6
    L = [0.]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))

    def at(d):
        d = min(max(d, 0), L[-1])
        i = 1
        while i < len(L) - 1 and L[i] < d:
            i += 1
        t = (d - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
        a, b = pts[i - 1], pts[i]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, ang
    d = L[-1] / 2 - _text_w(s, k) / 2
    out = []
    for c in s:
        g = _GL.get(c)
        adv = _ADV.get(c, 5.2) * k
        if g:
            gw = (max(p[0] for st in g for p in st)) * k
            mx, my, ang = at(d + gw / 2)
            ca, sa = math.cos(ang), math.sin(ang)
            for st in g:
                q = []
                for gx, gy in st:
                    u, v = gx * k - gw / 2, (gy - 3) * k
                    q.append((mx + u * ca - v * sa, my + u * sa + v * ca))
                out.append(q)
        d += adv
    (cv.heavy if heavy else cv.line)(out)
    return L[-1] / 2 - _text_w(s, k) / 2, L[-1] / 2 + _text_w(s, k) / 2, L[-1]


# ----------------------------------------------------------------------------------------------
# the vignette
# ----------------------------------------------------------------------------------------------

def _puff2(cv, cx, cy, r, ry=.66):
    """One billow of cumulus: lit crown, contour lines tightening into the turned-under belly."""
    circ = C._ell_pts(cx, cy, r, r * ry, 40)[:-1]
    cv.obj([circ], 1.)
    k = 1
    while True:
        rr = r - 2 * k
        if rr < r * .3 or rr < 2:
            break
        span = math.pi * (1.25 - .16 * k)
        if span < .5:
            break
        mid = math.pi * .58
        a0, a1 = mid - span / 2, mid + span / 2
        m = max(6, int(rr * span / 2))
        cv.hair([(cx + rr * math.cos(a0 + (a1 - a0) * i / m), cy + rr * ry * math.sin(a0 + (a1 - a0) * i / m)) for i in range(m + 1)])
        k += 1
    # the crown: light rules so nothing is left bare
    crown = [(px, py) for px, py in circ if py < cy - r * ry * .15]
    if len(crown) > 2:
        cv.hair(C.hatch_poly(circ, 0, 3, .25, 0)[:0])
    cv.hair([l for l in C.hatch_poly(circ, 0, 3, .25) if l[0][1] < cy - r * ry * .1])


def _lobe(cv, bx, by, r, base, ry=.78, belly=False):
    """One cauliflower lobe: white crown, contours rolling round its shaded lower right, ruled shade."""
    e = [(qx, min(qy, base)) for qx, qy in C._ell_pts(bx, by, r, r * ry, 32)[:-1]]
    cv.obj([e], 1.)
    for k, f in enumerate((.8, .6)):
        rr = r * f
        if rr < 2.5:
            continue
        a0, a1 = -.15 * math.pi + k * .15, .72 * math.pi - k * .1
        arc = [(bx + rr * math.cos(a0 + (a1 - a0) * j / 14), by + rr * ry * math.sin(a0 + (a1 - a0) * j / 14)) for j in range(15)]
        cv.hair([q for q in arc if q[1] < base - .5])
    for ln in C.hatch_poly(e, 0, 3, .25):
        if ln[0][1] > by - r * ry * .2:
            cv.hair(ln)
    for ln in C.hatch_poly(e, 0, 3, 1.75):
        if ln[0][1] > by + r * ry * (-.1 if belly else .35):
            cv.hair(ln)
    if belly:
        for ln in C.hatch_poly(e, 0, 3, 1.):
            if ln[0][1] > base - r * .35:
                cv.hair(ln)


def _cloud_mass(cv, cx, base, W, H, rng):
    """A cumulus W wide, H tall standing on a flat base: tiers of lobes painted top first, each tier
    wider and overlapping the one above, so only crowns show; the flat belly ruled dark."""
    L = 3 if H > 26 else 2
    r = H / (L + .3) * .8
    for j in range(L):
        f = (j + 1) / L
        span = W * (.35 + .65 * f)
        y = base - H + r * .8 + (H - r * 1.1) * j / max(1, L - 1) * .9
        n = max(1, int(span / (r * 1.5)) + 1)
        for i in range(n):
            x = cx - span / 2 + span * (i + .5) / n + rng.uniform(-.3, .3) * r
            rr = r * rng.uniform(.65, 1.3) * (.9 + .2 * f)
            _lobe(cv, x, y + rng.uniform(-.25, .2) * r, rr, base, belly=(j == L - 1))
    belly = [(cx - W / 2 - r * .3, base), (cx + W / 2 + r * .3, base)]
    cv.obj([], 0)
    cv.heavy(belly)


def _bank(cv, x0, x1, ytop, ybot, rng, rows=3):
    """Rows of cumulus masses, back to front, the front row lowest and largest."""
    h = ybot - ytop
    for row in range(rows):
        f = (row + 1) / rows
        H = h * (.42 + .3 * f)
        base = ytop + h * (.5 + .5 * f)
        x = x0 - rng.uniform(10, 40)
        while x < x1:
            W = H * rng.uniform(1.6, 3.2)
            _cloud_mass(cv, x + W / 2, base + rng.uniform(-.03, .05) * h, W, H, rng)
            x += W * rng.uniform(.45, .62)


def _mountain2(cv, prof, base, kind, veiled, rng, snow_frac):
    si = min(range(len(prof)), key=lambda i: prof[i][1])
    sx, sy = prof[si]
    ht = base - sy
    hw = (prof[-1][0] - prof[0][0]) / 2
    poly = prof + [(prof[-1][0], base + 2), (prof[0][0], base + 2)]
    ys = sy + ht * snow_frac
    snow = _snow_poly(prof, ys, rng, max(1.5, ht * .07))
    face = _face(prof, si, base, hw * .2)
    if veiled:
        cv.obj([poly], 0)
        cv.hair([[prof[i], prof[i + 1]] for i in range(0, len(prof) - 1, 2)])
        cv.hair(C.hatch_poly(face, -45, 3))
        cv.hair([l for l in C.hatch_poly(poly, 0, 3, 1.75)])
        for k in (-2, -1, 1, 2):
            x2 = sx + k * hw * .1
            cv.hair([[(sx + k * .5 + (x2 - sx) * t / 6, sy + 2 + (ys - sy) * t / 6) for t in (j, j + .6)] for j in range(6)])
        return
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 45, 3))
    cv.hair(C.hatch_poly(face, -45, 1.5))
    if snow:
        cv.obj([snow], .5)
        cv.hair(C.hatch_poly(snow, 0, 3, .25))
        sface = [p for p in snow if p[0] >= sx - .01]
        if len(sface) > 2:
            cv.hair(C.hatch_poly([(sx, sy)] + sface, -45, 3))
        for k in range(-3, 4):
            if k:
                cv.line([(sx + k * .6, sy + 2), (sx + k * hw * .09, ys + ht * .04 * (1 + abs(k) % 2))])


def _reeds(cv, x0, x1, ybase, hgt, rng):
    x = x0
    while x < x1:
        top = ybase - hgt * rng.uniform(.6, 1.)
        lean = rng.uniform(-4, 4)
        cv.line(_bez((x, ybase + 2), (x, ybase - hgt * .3), (x + lean * .3, top + hgt * .2), (x + lean, top), 8))
        if rng.random() < .35:     # cattail head
            hx, hy = x + lean * .9, top + hgt * .12
            head = C._ell_pts(hx, hy, 1.4, hgt * .1, 10)[:-1]
            cv.obj([head], 1.)
            cv.hair(C.hatch_poly(head, 0, 1.5))
        x += rng.uniform(2.5, 5)


def _heron2(cv, x, y, s, flip=False):
    """A great blue heron wading, feet at (x, y), about s tall; faces right unless flip."""
    f = -1 if flip else 1

    def P(u, v):
        return (x + f * u * s, y - v * s)

    cv.obj([], 0)
    cv.line([P(-.02, .0), P(-.01, .4)])
    cv.line([P(.07, .02), P(.04, .4)])
    cv.hair([P(-.08, .0), P(.04, .0)])
    top = _bez(P(-.34, .37), P(-.2, .6), P(.05, .66), P(.17, .56), 16)
    bot = _bez(P(.17, .56), P(.18, .44), P(.06, .37), P(-.06, .38), 10)
    tail = [P(-.2, .36), P(-.3, .32)]
    bpoly = top + bot + tail
    cv.obj([bpoly], 1.)
    for k in range(7):      # wing feathers laid along the body, dense below
        o = k * .03
        cv.hair(_bez(P(.15 - o * .3, .55 - o), P(.02, .57 - o * 1.2), P(-.15, .5 - o), P(-.33, .37 - o * .3), 10))
    cv.hair(C.hatch_poly(bot + [P(-.06, .38)], 90, 1.5))
    for k in range(4):      # drooping back plumes
        cv.line(_bez(P(-.12 - k * .03, .5 - k * .01), P(-.25, .44), P(-.32, .36), P(-.4 - k * .02, .3 - k * .02), 8))
    cl = _bez(P(.15, .54), P(.27, .68), P(.03, .76), P(.13, .9), 16)
    neck, Ln, Rn = _ribbon(cl, .075 * s, .045 * s)
    cv.obj([neck], 1.)
    for k in range(1, 3):
        t = k / 3
        cv.hair([(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(Ln, Rn)][2:-2])
    for i in range(2, len(Ln) - 3, 2):     # the streaked throat
        cv.hair([Ln[i], ((Ln[i][0] + Rn[i][0]) / 2, (Ln[i][1] + Rn[i][1]) / 2 + 1)])
    hx, hy = P(.15, .925)
    head = C._ell_pts(hx, hy, .055 * s, .038 * s, 16)[:-1]
    cv.obj([head], 1.)
    cv.hair(C.hatch_poly([p for p in head if p[1] > hy - .5] or head, 0, 1.5))
    bill = [P(.19, .94), P(.4, .905), P(.19, .9)]
    cv.obj([bill], .5)
    cv.hair([P(.2, .92), P(.38, .907)])
    crest = [P(.12, .955), P(-.08, .93), P(.11, .935)]
    cv.obj([crest], 1.)
    ex, ey = P(.17, .93)
    cv.obj([C._ell_pts(ex, ey, .7, .7, 8)[:-1]], 1.)
    for r in (.12, .2, .3):
        cv.hair(_bez(P(-r, .0), P(-r * .5, -.015), P(r * .5 + .03, -.015), P(r + .03, .0), 8))


def _sky(cv, x, y, w, h):
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([sky], 0)
    yy = math.floor(y - 2) + .25
    while yy < y + h + 2:
        cv.hair([(x - 2, yy), (x + w + 2, yy)])
        yy += 1.5 if (yy - y) < h * .18 else (2 if (yy - y) < h * .4 else 3)


def _ghost(cv, prof, cut, step=5.):
    """A hidden summit's silhouette pricked out in beads over the cloud, like a peak-finder's guide."""
    run = [p for p in prof if p[1] < cut]
    d, acc = 0., step / 2
    beads = []
    for i in range(1, len(run)):
        (ax, ay), (bx, by) = run[i - 1], run[i]
        L = math.hypot(bx - ax, by - ay)
        while acc <= d + L:
            t = (acc - d) / (L or 1)
            beads.append(C._ell_pts(ax + (bx - ax) * t, ay + (by - ay) * t, 1.3, 1.3, 8)[:-1])
            acc += step
        d += L
    cv.obj(beads, 1.)


def _hamilton(cv, cx, base, hw, ht, rng):
    """Hamilton Mountain on the Washington side of the Gorge: a wooded whaleback with a sheer
    basalt face toward the river, the trail switchbacking up its flank in a pricked line."""
    n = 40
    prof = []
    for i in range(n + 1):
        u = -1 + 2 * i / n
        if u < .25:
            k = (1 - ((u - .25) / 1.25) ** 2) ** 1.3
        else:
            k = max(0., 1 - ((u - .25) / .75) ** .7 * .95)
        prof.append((cx + u * hw, base - ht * k + .6 * math.sin(i * 1.7)))
    poly = prof + [(cx + hw, base + 2), (cx - hw, base + 2)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 45, 1.5))
    cv.hair(C.hatch_poly(poly, -45, 3))
    # the basalt cliff: vertical columns, black in the clefts
    cliff = [p for p in prof if p[0] > cx + hw * .3] + [(cx + hw * .95, base - ht * .1), (cx + hw * .35, base - ht * .35)]
    cv.obj([cliff], 1.)
    cv.hair(C.hatch_poly(cliff, 90, 2, .25))
    for i in range(5):
        xx = cx + hw * (.42 + .1 * i)
        cv.line([(xx, base - ht * (.9 - .14 * i)), (xx + 1, base - ht * (.45 - .06 * i))])
    # firs along the crown
    for i in range(10):
        q = prof[3 + i * 2]
        _fir(cv, q[0], q[1] + 2, rng.uniform(4, 7), True)
    # the trail, pricked in white dots up the west flank
    t = [(cx - hw * (.7 - .07 * j) + (6 if j % 2 else -6), base - ht * (.1 + .1 * j)) for j in range(8)]
    dots = []
    for i in range(1, len(t)):
        for k in range(4):
            f = k / 4
            dots.append(C._ell_pts(t[i - 1][0] + (t[i][0] - t[i - 1][0]) * f, t[i - 1][1] + (t[i][1] - t[i - 1][1]) * f, .9, .9, 6)[:-1])
    cv.obj(dots, 0)


def scene(x, y, w, h, ctx, seed, detail=2):
    """The view east from Sauvie Island, filling the box x, y, w, h (clip it to the field)."""
    rng = random.Random(seed)
    veiled = _hidden(ctx)
    cv = C.Canvas()
    _sky(cv, x, y, w, h)
    hor = y + h * (.6 if detail else .66)
    if detail == 0:
        peaks = [("hood", .5, .34, .48)]
    else:
        peaks = [("helens", .2, .17, .34), ("adams", .5, .21, .36), ("hood", .79, .23, .52)]
    profs = []
    for kind, fx, fhw, fht in peaks:
        prof = _peak_profile(x + w * fx, hor, w * fhw, h * fht, kind, random.Random(len(kind)))
        profs.append(prof)
        _mountain2(cv, prof, hor, kind, False, random.Random(seed + len(kind)), .42 if kind != "helens" else .5)
    deck = hor - h * (.27 if detail else .2)
    if veiled:
        # the cloud deck sits on the mountains: their skirts show, every summit is wrapped
        _bank(cv, x - 4, x + w + 4, y + h * (.04 if detail else .08), deck, rng, 2)
        for prof in profs:
            _ghost(cv, prof, deck - h * .12)
    else:
        for kind, fx, fhw, fht in peaks:
            _puff2(cv, x + w * (fx + .12), hor - h * fht * .2, h * .045)
    if detail > 0 and ctx.get("sheet", 0) >= 1:
        _hamilton(cv, x + w * .36, hor + h * .1, w * .2, h * .3, rng)
    # far (Washington) shore, wooded
    _ridge(cv, x - 2, x + w + 2, hor + h * .1,
           lambda t: hor + h * .005 + h * .025 * math.sin((t - x) / w * 9 + seed % 7), rng, detail > 0)
    _water(cv, x - 2, x + w + 2, hor + h * .1, y + h + 2, rng)
    if detail > 0:
        # Sauvie Island's near bank: reeds and cattails, the heron wading off its point
        bw = w * .34
        bank = [(x - 2, y + h * .84)] + [(x + bw * i / 14, y + h * (.86 + .12 * (i / 14) ** 2 - .03 * math.sin(i / 14 * math.pi))) for i in range(15)] \
            + [(x + bw + 6, y + h + 2), (x - 2, y + h + 2)]
        _reeds(cv, x - 2, x + bw * .7, y + h * .88, h * .2, rng)
        cv.obj([bank], 1.)
        cv.hair(C.hatch_poly(bank, 45, 1.5))
        cv.hair(C.hatch_poly(bank, -45, 3))
        _monogram(cv, x + bw * .8, y + h * .95, max(4, h * .05))
        _heron2(cv, x + w * .72, y + h * .86, h * (.34 if detail > 1 else .42), flip=True)
    return cv.svg()


def _field(fill, cid, d, bx, by, bw, bh):
    return (f'<clipPath id="{cid}"><path d="{d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{fill(bx, by, bw, bh)}</g>')


# ----------------------------------------------------------------------------------------------
# compositions (the house frame, adapted so the scene fills the whole field)
# ----------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.4, 150)
    o.append(C._clip(C._uid("rb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(f'<path d="{C._d(C._ell_pts(cx, cy, rx + 1, ry + 1, 64), True)}" fill="#fff" stroke="none"/>')
    o.append(_field(lambda a, b, c, d: scene(a, b, c, d, ctx, seed, 1 if gh > 60 else 0), C._uid("rbf", w, h),
                    C._d(C._ell_pts(cx, cy, rx - 1.5, ry - 1.5, 64), True), cx - rx, cy - ry, 2 * rx, 2 * ry))
    ring = C._d(C._ell_pts(cx, cy, rx + 1, ry + 1, 64), True) + C._d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="M0,{C._n(h - .5)}h{C._n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _cartouche_field(cx, cy, cw, ch, seed, ctx, detail, scrolls=False):
    c, rect, d = C.cartouche(cx, cy, cw, ch, seed, scrolls=scrolls)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    # the cartouche's own field is white under its moulding: draw the scene over the whole field
    i = c.index('<path d="', c.index('fill="#fff" stroke="none"/>') + 5)
    fld = _field(lambda X, Y, W, H: scene(X, Y, W, H, ctx, seed, detail), C._uid("cf", cx, cy, cw, ch), d,
                 cx - a, cy - b, 2 * a, 2 * b)
    return c[:i] + fld + c[i:]


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 2.3)
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
    o.append(C._clip(C._uid("rm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    o.append(_cartouche_field(cx, cy, cw, gh + 4, rng.randrange(1 << 20), ctx, 1))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _bearing_tablet(tx, ty, tw, th, ctx, seed):
    """The pedestal tablet as a peak-finder: the eastern skyline from home in profile under a
    bearing scale, NE . E . SE, each volcano's summit marked."""
    cv = C.Canvas()
    cv.obj([[(tx + 1, ty + 1), (tx + tw - 1, ty + 1), (tx + tw - 1, ty + th - 1), (tx + 1, ty + th - 1)]], 0)
    # bearings 30..130 degrees across the tablet
    def bx(b):
        return tx + 6 + (tw - 12) * (b - 30) / 100.
    base = ty + th - 2
    sky = ty + th * .45
    prof = []
    peaks = {45: .5, 67.5: .38, 112.5: .9}
    for i in range(201):
        b = 30 + 100 * i / 200
        v = .12 + .05 * math.sin(b * .9) + .03 * math.sin(b * 2.3)
        for pb, ph in peaks.items():
            v = max(v, ph * max(0., 1 - abs(b - pb) / 7.) ** 1.3)
        prof.append((bx(b), base - (base - sky) * v))
    land = prof + [(bx(130), base + 1), (bx(30), base + 1)]
    cv.hair([l for l in C.hatch_poly([(tx + 1, ty + 1), (tx + tw - 1, ty + 1), (tx + tw - 1, base), (tx + 1, base)], 0, 3, .25)])
    cv.obj([land], 1.)
    cv.hair(C.hatch_poly(land, 45, 1.5))
    for b in range(30, 131, 5):
        L = 3 if b % 15 else 5
        cv.hair([(bx(b), ty + 1.5), (bx(b), ty + 1.5 + L)])
    for pb in peaks:
        px = bx(pb)
        py = base - (base - sky) * peaks[pb]
        cv.obj([[(px, py - 2.5), (px + 2, py - 5.5), (px - 2, py - 5.5)]], .5)
    cap = min(6., th * .28)
    for lab, b in (("NE", 45), ("E", 90), ("SE", 135 - 4)):
        _letter_along(cv, lab, [(bx(b) - 20, ty + 2 + cap / 2 + 4.5), (bx(b) + 20, ty + 2 + cap / 2 + 4.5)], cap)
    return cv.svg()


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{C._n(px0 - 3.5)},{C._n(py0 - 3.5)}h{C._n(pw + 7)}v{C._n(ph + 7)}h{C._n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{C._n(px0 - 1.5)},{C._n(py0 - 1.5)}h{C._n(pw + 3)}v{C._n(ph + 3)}h{C._n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .66
    cx, cy = w / 2, py0 + ph * .45
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("rt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    o.append(_cartouche_field(cx, cy, cw, ch, rng.randrange(1 << 20), ctx, 2))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, max(12, ph * .06))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lv = C.Canvas()
    lv.obj([], 0)
    words = "HAMILTON MOUNTAIN" if ctx.get("sheet", 0) >= 1 else "IS THE MOUNTAIN OUT?"
    cl = [(p[0], p[1] + .3) for p in centre]
    d0, d1, Lt = _letter_along(lv, words, cl, min(bh * .5, 8.))
    # a fine rule with a lozenge closes each end of the lettering
    seg = []
    acc = 0.
    for i in range(1, len(cl)):
        acc += math.hypot(cl[i][0] - cl[i - 1][0], cl[i][1] - cl[i - 1][1])
        seg.append((acc, cl[i]))
    for lo, hi in ((6, d0 - 5), (d1 + 5, Lt - 6)):
        run = [q for a, q in seg if lo <= a <= hi]
        if len(run) > 1:
            lv.hair(run)
            lv.hair([(q[0], q[1] - 2) for q in run[1:-1]])
            lv.hair([(q[0], q[1] + 2) for q in run[1:-1]])
            mx, my = run[len(run) // 2]
            lv.obj([[(mx - 4, my), (mx, my - 2.5), (mx + 4, my), (mx, my + 2.5)]], 1.)
            lv.hair([(mx - 2, my), (mx + 2, my)])
    o.append(lv.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_bearing_tablet(tx + 1.5, ty + 1.5, tw - 2, th - 2, ctx, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("rf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{C._n(w * .06)},{C._n(h - 1.5)}h{C._n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", "")))
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
