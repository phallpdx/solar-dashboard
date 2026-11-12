"""Family / "Little one" plate.

The page: ideas for a two-to-three year old (blanket fort story time, a pinecone bird feeder,
worm hunts, a nature treasure bag) and places to go together (the zoo, the Holiday Express
steam train). The vignette is a blanket-fort story time under the evening sky: a patchwork
quilt pitched as a tent, a little girl inside reading by flashlight, a stack of books at the
door, a pinecone feeder with a chickadee hanging from a Douglas fir, Mt. Hood on the horizon and
tonight's moon. The pedestal tablet carries the Holiday Express steam train; the ribbon reads
LITTLE ONE.
Easter egg: Parker's dog curled asleep at the fort door (and a "P" pennant on the tent pole).
"""
import sys
import math
import random
import datetime
import engraving_codex as C
import engraving_morning as EM

_n, _d = C._n, C._d
PI, TAU = math.pi, 2 * math.pi


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def ell(cx, cy, rx, ry, n=36, a0=0., a1=TAU):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def clip_convex(subject, clipper):
    """Sutherland-Hodgman: subject polygon clipped by a convex clipper (either winding)."""
    def side(a, b, p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    sgn = 1 if C._area(clipper) > 0 else -1
    out = list(subject)
    n = len(clipper)
    for i in range(n):
        a, b = clipper[i], clipper[(i + 1) % n]
        inp, out = out, []
        if not inp:
            break
        s = inp[-1]
        for e in inp:
            ein = side(a, b, e) * sgn >= 0
            sin_ = side(a, b, s) * sgn >= 0
            if ein:
                if not sin_:
                    out.append(_isect(s, e, a, b))
                out.append(e)
            elif sin_:
                out.append(_isect(s, e, a, b))
            s = e
    return out


def _isect(p, q, a, b):
    x1, y1 = p
    x2, y2 = q
    x3, y3 = a
    x4, y4 = b
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return q
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def bil(A, B, Cc, D, u, v):
    """Bilinear point in quad A(0,0) B(1,0) C(1,1) D(0,1)."""
    return lerp(lerp(A, B, u), lerp(D, Cc, u), v)


def qbez(p0, p1, p2, n=12):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def solid(cv, poly):
    """Black mass from 1 px lines 0.9 apart."""
    cv.line(C.hatch_poly(poly, 0, .9, .45))


def tone(cv, poly, kind, phase=0.):
    """Hatch tones from light to dark."""
    H = C.hatch_poly
    if kind == 1:       # light
        cv.hair(H(poly, 0, 3, phase))
    elif kind == 2:     # light-mid
        cv.hair(H(poly, 45, 2, phase))
    elif kind == 3:     # mid
        cv.hair(H(poly, 0, 2, phase))
    elif kind == 4:     # mid-dark cross
        cv.hair(H(poly, 45, 2, phase))
        cv.hair(H(poly, -45, 2, phase))
    elif kind == 5:     # dark
        cv.line(H(poly, 0, 2, phase))
        cv.hair(H(poly, 60, 2, phase))
    elif kind == 6:     # near black
        cv.line(H(poly, 0, 1.5, phase))
        cv.hair(H(poly, 45, 1.5, phase))


def moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (datetime.datetime(d.year, d.month, d.day, 6) - datetime.datetime(2000, 1, 6, 18, 14)).total_seconds() / 86400
    return (days / 29.530588) % 1.


# ------------------------------------------------------------------------------------------------
# the vignette pieces (all into one Canvas, in paint order)
# ------------------------------------------------------------------------------------------------

def sky(cv, x, y, w, h, gy):
    rect = [(x, y), (x + w, y), (x + w, gy + 2), (x, gy + 2)]
    cv.obj([rect], 0)
    t1 = y + (gy - y) * .38
    t2 = y + (gy - y) * .74
    cv.line(C.hatch_poly([(x, y), (x + w, y), (x + w, t1), (x, t1)], 0, 2, .5))
    cv.hair(C.hatch_poly([(x, t1), (x + w, t1), (x + w, t2), (x, t2)], 0, 2, .5))
    cv.hair(C.hatch_poly([(x, t2), (x + w, t2), (x + w, gy + 2), (x, gy + 2)], 0, 3, .5))


def star(cv, cx, cy, r):
    pts = []
    for i in range(8):
        a = PI / 4 * i - PI / 2
        rr = r if i % 2 == 0 else r * .3
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    cv.obj([pts], 0)


def moon(cv, cx, cy, r, p):
    disc = ell(cx, cy, r, r, 40)
    cv.obj([ell(cx, cy, r + 1.5, r + 1.5, 40)], 0)       # halo gap
    cv.obj([disc], .5)
    k = math.cos(TAU * p)
    n = 20
    if p < .5:
        limb = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [PI / 2 + PI * i / n for i in range(n + 1)]]
        term = [(cx + k * r * math.cos(t), cy + r * math.sin(t)) for t in [-PI / 2 + PI * i / n for i in range(n + 1)]]
    else:
        limb = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [-PI / 2 + PI * i / n for i in range(n + 1)]]
        term = [(cx - k * r * math.cos(t), cy - r * math.sin(t)) for t in [-PI / 2 + PI * i / n for i in range(n + 1)]]
    dark = limb + term
    if abs(C._area(dark)) > 2:
        cv.hair(C.hatch_poly(dark, 0, 1.5, .3))
    # maria
    cv.hair([(cx + r * 1.6 * math.cos(a), cy + r * 1.6 * math.sin(a)) for a in [TAU * i / 48 for i in range(49)]])


def hills(cv, x, w, gy, h, seed):
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6) for _ in range(3)]
    top = [(x + w * i / 40, gy - h * (.035 + .018 * math.sin(i / 40 * 9 + ph[0]) + .012 * math.sin(i / 40 * 23 + ph[1])))
           for i in range(41)]
    poly = top + [(x + w, gy + 3), (x, gy + 3)]
    cv.obj([poly], .5)
    cv.hair(C.hatch_poly(poly, 0, 1.5, .25))
    # fir silhouettes along the ridge
    for i in range(int(w / 9)):
        fx = x + 4 + i * 9 + rng.uniform(-2, 2)
        j = min(40, max(0, int((fx - x) / w * 40)))
        by = top[j][1] + 1.5
        fh = rng.uniform(3, 6) * max(.7, h / 220)
        tri = [(fx, by - fh), (fx + fh * .32, by), (fx - fh * .32, by)]
        cv.obj([tri], 0)
        cv.line(C.hatch_poly(tri, 0, .9, .45))


def mt_hood(cv, cx, gy, hw, hh):
    """Mt. Hood: a lopsided snow cone, ridges running down, forest skirt hatched."""
    peak = (cx + hw * .05, gy - hh)
    pts = [(cx - hw, gy), (cx - hw * .55, gy - hh * .32), (cx - hw * .22, gy - hh * .7), (cx - hw * .08, gy - hh * .93),
           peak, (cx + hw * .14, gy - hh * .9), (cx + hw * .3, gy - hh * .66), (cx + hw * .62, gy - hh * .28), (cx + hw, gy)]
    cv.obj([pts], 1.)
    # the forest skirt below the snow line
    snow = gy - hh * .42
    skirt = [p for p in pts if p[1] >= snow - .01]
    lowband = [(cx - hw, gy), (cx - hw * .5, snow + hh * .05), (cx - hw * .25, snow + hh * .12), (cx, snow - hh * .02),
               (cx + hw * .2, snow + hh * .1), (cx + hw * .45, snow + hh * .02), (cx + hw, gy)]
    cv.hair(C.hatch_poly(lowband, -60, 1.5))
    cv.hair(C.hatch_poly(lowband, 0, 2))
    # ridges (glacier gullies) on the snow, shadow side on the right
    for f in (-.45, -.25, -.08, .12, .28, .48):
        top = lerp(peak, (cx + f * hw * .3, gy - hh * .9), .5)
        bot = (cx + f * hw * 1.05, snow + hh * .05)
        cv.hair(qbez(top, ((top[0] + bot[0]) / 2 + 2, (top[1] + bot[1]) / 2), bot, 6))
    shade = [peak, (cx + hw * .14, gy - hh * .9), (cx + hw * .3, gy - hh * .66), (cx + hw * .5, snow),
             (cx + hw * .12, snow), (cx + hw * .08, gy - hh * .6)]
    cv.hair(C.hatch_poly(shade, -70, 2))


def ground(cv, x, w, gy, bot):
    poly = [(x, gy), (x + w, gy), (x + w, bot), (x, bot)]
    cv.obj([poly], 0)
    cv.line([(x, gy + .5), (x + w, gy + .5)])
    mid = gy + (bot - gy) * .45
    cv.hair(C.hatch_poly([(x, gy + 1), (x + w, gy + 1), (x + w, mid), (x, mid)], 0, 2, .3))
    cv.line(C.hatch_poly([(x, mid), (x + w, mid), (x + w, bot), (x, bot)], 0, 2, .3))


def grass(cv, x0, x1, y, hgt, rng):
    x = x0
    while x < x1:
        hh = hgt * rng.uniform(.5, 1.)
        lean = rng.uniform(-1, 1) * hh * .4
        cv.hair([(x, y), (x + lean * .3, y - hh * .6), (x + lean, y - hh)])
        x += rng.uniform(1.4, 2.6)


def fir(cv, tx, top, base, wmax, rng, detail=1.):
    """A Douglas fir: drooping tiers of boughs, needles laid as strokes radiating from each tier's
    crown and bending down, dark on the shadow (left) side, a lit fringe on the right."""
    n = max(4, int(7 * detail))
    trunk = [(tx - 2, base), (tx - 1, top + 8), (tx + 1, top + 8), (tx + 2, base)]
    cv.obj([trunk], 1.)
    cv.line(C.hatch_poly(trunk, 90, 1.5))
    for i in range(n):
        f = (i + 1) / n
        yt = top + (base - top) * .72 * (i / n)
        yb = top + (base - top) * (.16 + .7 * f)
        wi = wmax * (.28 + .72 * f)
        k = max(6, int(wi / 2.2))
        edge = []
        for j in range(k + 1):
            u = j / k
            xx = tx - wi + 2 * wi * u
            droop = (abs(2 * u - 1) ** 1.6) * (yb - yt) * .18
            edge.append((xx, yb + droop - (1.8 if j % 2 else 0)))
        poly = [(tx, yt)] + edge
        cv.obj([poly], 1.)
        # needle strokes from the crown, bowed downward
        m = int(2 * wi / 1.6)
        for j in range(m + 1):
            u = j / m
            ex = tx - wi + 2 * wi * u
            ey = yb + (abs(2 * u - 1) ** 1.6) * (yb - yt) * .18 - 1
            mid = ((tx + ex) / 2, (yt + ey) / 2 - (ey - yt) * .12 * (1 - abs(2 * u - 1)))
            line = qbez((tx, yt + 2), mid, (ex, ey), 6)
            if u < .55:
                cv.hair(line)
            elif j % 2 == 0:
                cv.hair(line[2:])
        # shadow side darkened, and the shade the tier above throws
        sh = [(tx, yt + (yb - yt) * .3), (tx - wi * .95, edge[0][1] - 1), (tx - wi * .2, yb + 1), (tx, yb)]
        cv.hair(C.hatch_poly(sh, 0, 1.5, .3))
        band = [(tx - wi, yt + (yb - yt) * .55), (tx + wi, yt + (yb - yt) * .55), (tx + wi, yb + 6), (tx - wi, yb + 6)]
        cv.line(C.hatch_poly(clip_convex(band, [(tx, yt), (tx + wi * 1.1, yb + 8), (tx - wi * 1.1, yb + 8)]), 0, 2, 1))


def twig(cv, p0, p1, sag, rng, detail):
    """A fir branch with needle fans, from p0 to p1."""
    pts = qbez(p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + sag), p1, 14)
    R = C._Rib(pts, [2.2 - 1.6 * i / 14 for i in range(15)], [2.2 - 1.6 * i / 14 for i in range(15)])
    for i in range(1, 14):
        px, py = pts[i]
        L = (6 + 3 * (1 - i / 14)) * max(.7, detail)
        for k in range(-3, 4):
            a = PI / 2 + k * .28 + rng.uniform(-.08, .08)
            cv.hair([(px, py), (px + L * math.cos(a) * .9, py + L * math.sin(a))])
            if k in (-2, 0, 2):
                cv.hair([(px, py), (px + L * .7 * math.cos(-a), py + L * .5 * math.sin(-a))])
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(-.4, 0, 1))
    return pts


def pinecone(cv, cx, cy, rx, ry):
    poly = ell(cx, cy, rx, ry, 28)
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 0, 1.5))
    # scales: staggered cups, each a dark crescent under a lit lip
    rows = max(3, int(ry * 2 / 3.2))
    for j in range(rows):
        v = -1 + (j + .5) * 2 / rows
        half = rx * math.sqrt(max(0, 1 - v * v)) * .95
        cols = max(2, int(half * 2 / 3.2))
        for i in range(cols):
            u = -1 + (i + .5 + (.5 if j % 2 else 0)) * 2 / (cols + (1 if j % 2 else 0))
            sx, sy = cx + u * half, cy + v * ry
            s = 1.5
            cup = [(sx - s, sy - .6), (sx - s * .6, sy + s * .6), (sx + s * .6, sy + s * .6), (sx + s, sy - .6)]
            cv.line(cup)
    # birdseed specks on the sunflower butter
    rng = random.Random(int(cx * 7 + cy))
    for _ in range(int(rx * ry / 6)):
        a = rng.uniform(0, TAU)
        rr = math.sqrt(rng.random())
        px, py = cx + rx * rr * math.cos(a) * .85, cy + ry * rr * math.sin(a) * .85
        cv.heavy([(px, py), (px + .3, py + .3)])


def chickadee(cv, x, y, s, facing=-1):
    """Black-capped chickadee perched at (x, y) (its feet), s = body length."""
    f = facing

    def P(px, py):
        return (x + f * px * s, y - py * s)
    tail = [P(.35, .35), P(.95, .55), P(1.0, .45), P(.4, .2)]
    cv.obj([tail], 1.)
    cv.hair(C.hatch_poly(tail, 20 * f, 1.5))
    body = [P(-.45, .62), P(-.3, .82), P(0, .86), P(.3, .7), P(.5, .45), P(.35, .18), P(0, .08), P(-.3, .2), P(-.5, .42)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly([P(0, .12), P(.4, .2), P(.45, .5), P(0, .4)], 0, 2))
    wing = [P(-.05, .6), P(.28, .66), P(.6, .4), P(.2, .3)]
    cv.obj([wing], .5)
    cv.hair(C.hatch_poly(wing, -30 * f, 1.5))
    cv.hair([P(0, .5), P(.4, .45)])
    head = ell(*P(-.38, .78), s * .26, s * .24, 18)
    cv.obj([head], 1.)
    cap = [P(-.62, .82), P(-.55, 1.0), P(-.3, 1.02), P(-.13, .86), P(-.3, .82)]
    solid(cv, cap)
    bib = [P(-.55, .66), P(-.35, .64), P(-.3, .5), P(-.48, .52)]
    solid(cv, bib)
    cv.heavy([P(-.47, .78), P(-.46, .79)])
    cv.line([P(-.64, .76), P(-.78, .74)])          # bill
    cv.hair([P(-.05, .08), P(-.05, -.08)])
    cv.hair([P(.08, .08), P(.1, -.08)])


def books(cv, x, y, w, h, rng):
    """A stack of picture books, bottom at y, width w, total height h."""
    n = 3
    bh = h / n
    yy = y
    for i in range(n):
        off = rng.uniform(-.12, .12) * w
        bw = w * rng.uniform(.82, 1.)
        x0 = x + off + (w - bw) / 2
        dep = bh * .55
        front = [(x0, yy - bh), (x0 + bw, yy - bh), (x0 + bw, yy), (x0, yy)]
        topf = [(x0, yy - bh), (x0 + dep, yy - bh - dep * .6), (x0 + bw + dep, yy - bh - dep * .6), (x0 + bw, yy - bh)]
        side = [(x0 + bw, yy - bh), (x0 + bw + dep, yy - bh - dep * .6), (x0 + bw + dep, yy - dep * .6), (x0 + bw, yy)]
        cv.obj([side], 1.)
        # page edges
        cv.hair(C.hatch_poly(side, -31, 1.5))
        cv.obj([topf], 1.)
        cv.hair(C.hatch_poly(topf, 0, 2))
        cv.obj([front], 1.)
        # cloth spine: tone + bands
        k = (i + 1) % 3
        if k == 0:
            cv.hair(C.hatch_poly(front, 45, 1.5))
        elif k == 1:
            cv.hair(C.hatch_poly(front, 0, 1.5))
        else:
            cv.hair(C.hatch_poly(front, 45, 2))
            cv.hair(C.hatch_poly(front, -45, 2))
        for f in (.14, .86):
            band = [(x0 + bw * f - .8, yy - bh), (x0 + bw * f + .8, yy - bh), (x0 + bw * f + .8, yy), (x0 + bw * f - .8, yy)]
            cv.obj([band], .5)
        yy -= bh


def sleeping_dog(cv, cx, cy, d):
    """Parker's dog curled nose-to-tail, asleep (the Easter egg)."""
    sh = ell(cx, cy + d * .5, d * 1.2, d * .2, 20)
    cv.obj([sh], 0)
    cv.line(C.hatch_poly(sh, 0, 1.5, .3))
    body = ell(cx + d * .1, cy, d, d * .58, 32)
    cv.obj([body], 1.5)
    # coat in bulino: arcs following the curl, shadow toward the ground
    for k in (.45, .62, .78, .9):
        cv.hair(ell(cx + d * .1, cy + d * .04, d * k, d * .58 * k, 20, -PI * .98, -PI * .05))
    lower = clip_convex(body, [(cx - 2 * d, cy + d * .18), (cx + 2 * d, cy + d * .05), (cx + 2 * d, cy + d), (cx - 2 * d, cy + d)])
    cv.hair(C.hatch_poly(lower, 0, 1.5, .3))
    # haunch
    cv.line(ell(cx + d * .55, cy + d * .05, d * .32, d * .3, 14, -PI * .9, PI * .4))
    # tail curling round the front
    tail = qbez((cx + d * 1.0, cy + d * .25), (cx + d * .5, cy + d * .78), (cx - d * .55, cy + d * .5), 12)
    R = C._Rib(tail, [d * .05 + d * .1 * math.sin(PI * i / 12) for i in range(13)],
               [d * .05 + d * .1 * math.sin(PI * i / 12) for i in range(13)])
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(.3, 0, 1))
    # head resting on the tail, muzzle to the left
    hx, hy = cx - d * .58, cy + d * .12
    head = [(hx + d * .3, hy - d * .25), (hx - d * .05, hy - d * .3), (hx - d * .35, hy - d * .12),
            (hx - d * .62, hy + d * .02), (hx - d * .62, hy + d * .16), (hx - d * .3, hy + d * .25), (hx + d * .25, hy + d * .25)]
    cv.obj([head], 1.5)
    cv.hair(C.hatch_poly(clip_convex(head, [(hx - d, hy + d * .08), (hx + d, hy + d * .02), (hx + d, hy + d), (hx - d, hy + d)]), 0, 1.5))
    cv.heavy(ell(hx - d * .6, hy + d * .06, d * .05, d * .05, 6))      # nose
    cv.line(qbez((hx - d * .22, hy - d * .06), (hx - d * .14, hy + d * .02), (hx - d * .05, hy - d * .06), 4))   # closed eye
    ear = [(hx - d * .02, hy - d * .26), (hx + d * .3, hy - d * .3), (hx + d * .28, hy + d * .12), (hx + d * .08, hy + d * .02)]
    cv.obj([ear], 1.)
    solid(cv, ear)
    # paws
    for k in (0, 1):
        p = ell(hx - d * .2 + k * d * .22, hy + d * .34, d * .14, d * .08, 10)
        cv.obj([p], 1.)


def girl_reading(cv, cx, by, s):
    """A little girl in silhouette, seated with her knees up, reading a picture book by torchlight:
    s = her seated height, facing left. Pigtails, a slim neck, an arm out to the book."""
    head = ell(cx, by - s * .8, s * .13, s * .14, 20)
    tails = [ell(cx + s * .15, by - s * .86, s * .06, s * .045, 10), ell(cx + s * .1, by - s * .7, s * .045, s * .06, 10)]
    neck = [(cx - s * .03, by - s * .7), (cx + s * .05, by - s * .7), (cx + s * .06, by - s * .6), (cx - s * .04, by - s * .6)]
    torso = [(cx - s * .1, by - s * .62), (cx + s * .1, by - s * .62), (cx + s * .17, by - s * .5), (cx + s * .2, by - s * .2),
             (cx + s * .22, by), (cx - s * .5, by), (cx - s * .54, by - s * .05), (cx - s * .42, by - s * .08),
             (cx - s * .3, by - s * .34), (cx - s * .2, by - s * .36), (cx - s * .12, by - s * .3), (cx - s * .12, by - s * .5)]
    arm = [(cx - s * .08, by - s * .54), (cx - s * .3, by - s * .44), (cx - s * .3, by - s * .38), (cx - s * .06, by - s * .44)]
    for p in (torso, neck, head, arm) + tuple(tails):
        cv.obj([p], 0)
        solid(cv, p)
    # the open picture book held up before her, white, a sun on its page
    bx, bk = cx - s * .36, by - s * .58
    pg = s * .22
    left = [(bx - pg * .9, bk - pg * .3), (bx, bk), (bx, bk + pg * .85), (bx - pg * .9, bk + pg * .55)]
    right = [(bx, bk), (bx + pg * .3, bk - pg * .45), (bx + pg * .3, bk + pg * .4), (bx, bk + pg * .85)]
    cv.obj([left, right], 1.)
    for t in (.66, .82):
        cv.hair([lerp(left[0], left[3], t), lerp(left[1], left[2], t)])
    cv.hair(ell(bx - pg * .45, bk + pg * .08, pg * .13, pg * .13, 10))
    cv.hair(C.hatch_poly(right, 75, 1.5))


def blanket_fort(cv, fx, gy, W, H, rng, detail=1.):
    """A patchwork quilt pitched over a pole: front gable with the door, one long slope receding."""
    A = (fx, gy - H)
    L = (fx - W * .5, gy)
    R = (fx + W * .5, gy)
    dep = (W * .4, -H * .09)
    A2 = (A[0] + dep[0], A[1] + dep[1])
    R2 = (R[0] + dep[0], R[1] + dep[1])
    # receding right slope: patchwork quilt
    slope = [A, A2, R2, R]
    cv.obj([slope], 1.)
    nu, nv = 4, max(3, int(5 * detail))
    for i in range(nv):
        for j in range(nu):
            q = [bil(A, A2, R2, R, j / nu, i / nv), bil(A, A2, R2, R, (j + 1) / nu, i / nv),
                 bil(A, A2, R2, R, (j + 1) / nu, (i + 1) / nv), bil(A, A2, R2, R, j / nu, (i + 1) / nv)]
            k = (i + 2 * j) % 3
            if k == 0:
                tone(cv, q, 4)
            elif k == 1:
                tone(cv, q, 5)
            else:
                cv.hair(C.hatch_poly(q, 0, 2))
                for t in (.33, .66):     # a small star-check in the patch
                    cv.hair([lerp(q[0], q[3], t), lerp(q[1], q[2], t)])
    # seams with quilting stitches
    for i in range(1, nv):
        p0, p1 = bil(A, A2, R2, R, 0, i / nv), bil(A, A2, R2, R, 1, i / nv)
        cv.line([p0, p1])
    for j in range(1, nu):
        p0, p1 = bil(A, A2, R2, R, j / nu, 0), bil(A, A2, R2, R, j / nu, 1)
        cv.line([p0, p1])
    # hem: scalloped lower edge of the slope
    m = int(math.hypot(R2[0] - R[0], R2[1] - R[1]) / 4)
    for k in range(m):
        a, b = lerp(R, R2, k / m), lerp(R, R2, (k + 1) / m)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 1.6)
        cv.hair([a, mid, b])
    # front gable: quilt patches clipped to the triangle
    tri = [A, R, L]
    cv.obj([tri], 1.)
    rows = max(3, int(4 * detail))
    for i in range(rows):
        y0 = A[1] + H * i / rows
        y1 = A[1] + H * (i + 1) / rows
        cols = 2 + i
        for j in range(cols):
            x0 = fx - W * .5 + W * j / cols
            x1 = fx - W * .5 + W * (j + 1) / cols
            q = clip_convex([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], tri)
            if len(q) < 3 or abs(C._area(q)) < 4:
                continue
            k = (i + j) % 3
            if k == 0:
                cv.hair(C.hatch_poly(q, 45, 2))
            elif k == 1:
                cv.hair(C.hatch_poly(q, 0, 1.5))
            else:
                cv.hair(C.hatch_poly(q, 90, 2))
                cv.hair(C.hatch_poly(q, 0, 3))
            cv.hair([(q[0][0], q[0][1]) for _ in range(1)] + [q[1]])
    for i in range(1, rows):
        y = A[1] + H * i / rows
        t = (y - A[1]) / H
        cv.line([(fx - W * .5 * t, y), (fx + W * .5 * t, y)])
    # door: dark interior with the reading girl and her torch-light
    dh = H * .74
    dw = W * .3
    door = qbez((fx - dw, gy), (fx - dw * .3, gy - dh * .6), (fx, gy - dh), 10)[:-1] + \
        qbez((fx, gy - dh), (fx + dw * .3, gy - dh * .6), (fx + dw, gy), 10)
    cv.obj([door], 1.)
    tone(cv, door, 6)
    glow = ell(fx - dw * .05, gy - dh * .42, dw * .85, dh * .5, 28)
    glow = clip_convex(glow, [(fx - dw * .8, gy), (fx - dw * .3, gy - dh * .62), (fx, gy - dh * .85), (fx + dw * .3, gy - dh * .62), (fx + dw * .8, gy)])
    if len(glow) > 2:
        cv.obj([glow], 0)
        cv.hair(C.hatch_poly(glow, 0, 3, .5))
        inner = ell(fx - dw * .3, gy - dh * .4, dw * .32, dh * .2, 20)
        cv.obj([inner], 0)
        cv.hair(C.hatch_poly(inner, 30, 3, .5))
    girl_reading(cv, fx + dw * .3, gy - .5, dh * .62)
    # door flaps tied back: folded triangles showing the striped lining
    for sd in (-1, 1):
        flap = [(fx, gy - dh), (fx + sd * dw * 1.0, gy), (fx + sd * dw * 1.45, gy - dh * .35)]
        flap = [(fx + sd * dw * .05, gy - dh * .95), (fx + sd * dw * 1.0, gy), (fx + sd * dw * 1.3, gy - dh * .38)]
        cv.obj([flap], 1.)
        cv.hair(C.hatch_poly(flap, 90 - sd * 25, 1.5))
        tie = (fx + sd * dw * 1.18, gy - dh * .3)
        cv.obj([ell(tie[0], tie[1], 1.6, 1.6, 8)], 1.)
    # ridge pole poking out with a little pennant
    pole_top = (A[0] - W * .04, A[1] - H * .28)
    cv.obj([[(A[0] - .8, A[1] + 2), (pole_top[0] - .8, pole_top[1]), (pole_top[0] + .8, pole_top[1]), (A[0] + .8, A[1] + 2)]], 1.)
    pen = [(pole_top[0] + .8, pole_top[1]), (pole_top[0] + H * .3, pole_top[1] + H * .06), (pole_top[0] + .8, pole_top[1] + H * .13)]
    cv.obj([pen], 1.)
    cv.hair(C.hatch_poly(pen, 0, 1.5))
    # a tiny "P" cut white in the pennant
    s = H * .085
    if s > 2.2:
        px, py = pole_top[0] + H * .07, pole_top[1] + H * .02
        pp = [(px, py + s * 1.0), (px, py), (px + s * .5, py), (px + s * .7, py + s * .25), (px + s * .5, py + s * .5), (px, py + s * .5)]
        cv.obj([], 0)
        R = C._Rib(pp, [.6] * len(pp), [.6] * len(pp))
        cv.obj([R.outline()], 0)
    cv.obj([ell(*pole_top, 1.4, 1.4, 8)], 1.)
    return door, A, R2


def worm(cv, x, y, s):
    pts = [(x + s * t, y + s * .12 * math.sin(t * 8)) for t in [i / 16 for i in range(17)]]
    R = C._Rib(pts, [s * .055] * 17, [s * .055] * 17)
    cv.obj([R.outline()], 1.)
    for i in range(1, 9):
        cv.hair([R.at(i / 9, -1), R.at(i / 9, 1)])
    cv.hair(R.contour(-.5, 0, 1))


def pebble(cv, x, y, rx, ry):
    p = ell(x, y, rx, ry, 16)
    cv.obj([p], 1.)
    cv.hair(C.hatch_poly(clip_convex(p, [(x - rx, y), (x + rx, y - ry * .3), (x + rx * 2, y + ry * 2), (x - rx * 2, y + ry * 2)]), 30, 1.5))


def leaf(cv, x, y, s, ang):
    ca, sa = math.cos(ang), math.sin(ang)

    def T(u, v):
        return (x + (u * ca - v * sa) * s, y + (u * sa + v * ca) * s)
    lobes = []
    for i in range(11):
        t = i / 10
        lobes.append(T(t, .35 * math.sin(PI * t) * (1 + .25 * math.sin(t * 15))))
    for i in range(10, -1, -1):
        t = i / 10
        lobes.append(T(t, -.35 * math.sin(PI * t) * (1 + .25 * math.sin(t * 15 + 1))))
    cv.obj([lobes], 1.)
    cv.hair(C.hatch_poly(lobes, math.degrees(ang) + 60, 1.5))
    cv.line([T(-.15, 0), T(.9, 0)])


# ------------------------------------------------------------------------------------------------
# the whole scene
# ------------------------------------------------------------------------------------------------

def stick(cv, x, y, L, ang):
    p0 = (x, y)
    p1 = (x + L * math.cos(ang), y + L * math.sin(ang))
    pts = [lerp(p0, p1, i / 10) for i in range(11)]
    R = C._Rib(pts, [1.6] * 11, [1.6] * 11)
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(-.4, 0, 1))
    m = lerp(p0, p1, .6)
    cv.line([m, (m[0] + L * .15 * math.cos(ang - .7), m[1] + L * .15 * math.sin(ang - .7))])


def scene(x, y, w, h, field_d, ctx, cid):
    date = (ctx or {}).get("date", "2026-11-11")
    seed = sum(map(ord, date))
    rng = random.Random(seed)
    S = min(w, h)
    detail = max(.45, min(1., S / 200))
    small = S < 95
    cv = C.Canvas()
    gy = y + h * (.6 if not small else .66)
    sky(cv, x, y, w, h, gy)
    for _ in range(int(w * (gy - y) / 1100)):
        sx, sy = rng.uniform(x + 4, x + w - 4), rng.uniform(y + 3, y + (gy - y) * .6)
        star(cv, sx, sy, rng.choice((2.4, 3., 3.6)) * (1 if not small else .7))
    moon(cv, x + w * (.8 if not small else .2), y + h * .16 + 2, max(4, S * .06), moon_phase(date))
    hills(cv, x, w, gy, h, seed)
    if not small:
        mt_hood(cv, x + w * .3, gy - h * .02, w * .16, h * .2)
    ground(cv, x, w, gy, y + h)
    if small:
        fx, FW, FH, fbase = x + w * .5, w * .5, h * .5, gy + h * .16
    else:
        fx, FW, FH, fbase = x + w * .57, w * .4, h * .42, gy + h * .14
        fir(cv, x + w * .1, y - h * .03, gy + h * .07, w * .12, rng, detail)
        tp = twig(cv, (x - 4, y + h * .09), (x + w * .55, y + h * .05), h * .06, rng, detail)
        fxx = tp[10][0]
        pr = max(4, S * .045)
        top = y + h * .2
        cv.obj([], 0)
        cv.hair([(fxx, tp[10][1] + 1), (fxx, top)])
        pinecone(cv, fxx, top + pr * 1.4, pr, pr * 1.45)
        chickadee(cv, fxx + pr * .1, top + pr * .15, max(7, S * .09), -1)
    blanket_fort(cv, fx, fbase, FW, FH, rng, detail)
    beam = [(fx - FW * .2, fbase), (fx + FW * .2, fbase), (fx + FW * .3, fbase + h * .06), (fx - FW * .4, fbase + h * .07)]
    beam = clip_convex(beam, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    cv.obj([beam], 0)
    cv.hair(C.hatch_poly(beam, 0, 3, .5))
    rg = random.Random(seed + 1)
    grass(cv, x, fx - FW * .5, gy + h * .02, 3 * detail + 1, rg)
    if not small:
        books(cv, fx - FW * .95, fbase + h * .035, FW * .34, FH * .4, rng)
        # the nature treasure bag, laid out in the grass: pinecone, leaf, smooth rock, stick, and a worm
        ty = y + h * .9
        cv.obj([], 0)
        grass(cv, x, x + w, y + h * .985, 5 * detail + 1, rg)
        pinecone(cv, x + w * .2, ty - S * .01, S * .055, S * .034)
        leaf(cv, x + w * .3, ty + S * .01, S * .13, -.35)
        pebble(cv, x + w * .5, ty, S * .055, S * .032)
        stick(cv, x + w * .58, ty + S * .025, S * .19, -.18)
        worm(cv, x + w * .79, ty - S * .005, S * .13)
    else:
        sleeping_dog(cv, fx + FW * .62, fbase + h * .01, FW * .16)
    body = cv.svg()
    if not small:
        body += EM._dog(fx + FW * .86, fbase + h * .065, FW * .0062, True)
    return (f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g>')


def banner_letters(centre, text, cap):
    xs = [p[0] for p in centre]
    x0, x1 = xs[0], xs[-1]
    polys, width = EM._text_polys(text, (x0 + x1) / 2, 0, cap, track=2.2)
    out = []

    def yat(px):
        t = (px - x0) / (x1 - x0) * (len(centre) - 1)
        i = max(0, min(len(centre) - 2, int(t)))
        f = t - i
        return centre[i][1] + (centre[i + 1][1] - centre[i][1]) * f
    for p in polys:
        out.append([(px, yat(px) - cap / 2 + py) for px, py in p])
    d = "".join(_d(p, tol=.1) for p in out)
    # flanking diamonds
    cx = (x0 + x1) / 2
    orn = ""
    for sd in (-1, 1):
        for k, r in ((width / 2 + cap * .9, cap * .28), (width / 2 + cap * 1.7, cap * .18)):
            ox = cx + sd * k
            oy = yat(ox)
            orn += _d([(ox - r, oy), (ox, oy - r), (ox + r, oy), (ox, oy + r)], True, 0)
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{1.5 if cap >= 8 else 1}"/>'
            f'<path d="{orn}" fill="#000" stroke="none"/>'), width


def steam_train(tx, ty, tw, th, seed):
    """The Holiday Express: a little engine and two lit cars on the tablet, steam rolling back."""
    cv = C.Canvas()
    box = [(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th)]
    cv.obj([box], 0)
    cv.line(C.hatch_poly(box, 0, 1.5, .4))          # night ground
    s = th * .82
    base = ty + th - 1.6
    cv.obj([[(tx, base), (tx + tw, base), (tx + tw, base + 1.6), (tx, base + 1.6)]], 0)
    cv.line([(tx, base + .5), (tx + tw, base + .5)])
    # sleepers
    xx = tx + 1
    while xx < tx + tw:
        cv.hair([(xx, base + .6), (xx - .6, base + 1.6)])
        xx += 2.5
    ex = tx + tw - s * 2.6
    # cars (behind the engine, to the left)
    cl = s * 1.9
    ncar = max(1, min(6, int((tw - s * 3.2) / (s * 2.1))))
    for c in range(ncar):
        cx0 = ex - (c + 1) * (cl + s * .18)
        car = [(cx0, base - s * .2), (cx0 + cl, base - s * .2), (cx0 + cl, base - s * .82), (cx0 + cl * .96, base - s * .9),
               (cx0 + cl * .04, base - s * .9), (cx0, base - s * .82)]
        cv.obj([car], 1.)
        cv.hair(C.hatch_poly(car, 0, 2))
        nwin = max(2, int(cl / (s * .38)))
        for i in range(nwin):
            wx = cx0 + cl * (i + .3) / nwin
            win = [(wx, base - s * .72), (wx + cl * .4 / nwin, base - s * .72), (wx + cl * .4 / nwin, base - s * .45), (wx, base - s * .45)]
            cv.obj([win], .5)
        for wx in (cx0 + cl * .2, cx0 + cl * .8):
            cv.obj([ell(wx, base - s * .12, s * .13, s * .13, 10)], 1.)
        # garland swags along the roof
        for i in range(4):
            a = cx0 + cl * i / 4
            cv.hair(qbez((a, base - s * .86), (a + cl / 8, base - s * .7), (a + cl / 4, base - s * .86), 4))
        cv.line([(cx0 + cl, base - s * .4), (cx0 + cl + s * .18, base - s * .4)])
    # engine
    boiler = [(ex, base - s * .25), (ex + s * 1.5, base - s * .25), (ex + s * 1.5, base - s * .68), (ex, base - s * .68)]
    cab = [(ex - s * .05, base - s * .2), (ex + s * .55, base - s * .2), (ex + s * .55, base - s * .92),
           (ex + s * .62, base - s * .92), (ex + s * .62, base - s * 1.0), (ex - s * .12, base - s * 1.0),
           (ex - s * .12, base - s * .92), (ex - s * .05, base - s * .92)]
    stack = [(ex + s * 1.12, base - s * .66), (ex + s * 1.3, base - s * .66), (ex + s * 1.36, base - s * 1.0), (ex + s * 1.06, base - s * 1.0)]
    cow = [(ex + s * 1.5, base - s * .32), (ex + s * 1.8, base), (ex + s * 1.5, base)]
    lamp = ell(ex + s * 1.56, base - s * .55, s * .09, s * .09, 8)
    for p in (stack, boiler):
        cv.obj([p], 1.)
        cv.hair(C.hatch_poly(p, 90, 1.5))
    cv.obj([cab], 1.)
    cv.hair(C.hatch_poly(cab, 0, 1.5))
    cv.obj([[(ex + s * .12, base - s * .82), (ex + s * .42, base - s * .82), (ex + s * .42, base - s * .55), (ex + s * .12, base - s * .55)]], .5)
    cv.obj([cow], 1.)
    cv.hair(C.hatch_poly(cow, 70, 1.5))
    cv.obj([lamp], .5)
    for wx, wr in ((ex + s * .3, .3), (ex + s * .95, .3), (ex + s * 1.35, .18)):
        cv.obj([ell(wx, base - wr * s, wr * s, wr * s, 14)], 1.)
        cv.hair([(wx - wr * s * .7, base - wr * s), (wx + wr * s * .7, base - wr * s)])
    cv.line([(ex + s * .3, base - s * .3), (ex + s * .95, base - s * .3)])
    # headlamp beam, steam trailing back over the cars
    rng = random.Random(seed)
    px, py = ex + s * 1.2, base - s * 1.05
    r = s * .16
    k = 0
    while px > tx + r * 2 and k < 9:
        p = ell(px, py, r, r * .8, 14)
        cv.obj([p], .5)
        cv.hair(C.hatch_poly(clip_convex(p, [(px - r * 2, py), (px + r * 2, py), (px + r * 2, py + r), (px - r * 2, py + r)]), 0, 1.5))
        px -= r * 1.5
        py = max(ty + r * .9, py - r * .5 + rng.uniform(-.2, .2) * r)
        r = min(r * 1.12, th * .22)
        k += 1
    return cv.svg()


def my_pedestal(x, y, w, h, seed=0):
    """The reference's base, filling x..x+w, y..y+h: a knurled cornice; a slab whose top is lightly
    ruled in perspective and whose front face is ruled mid-tone round a sunk blank tablet (for path
    lettering) flanked by rosettes; a second knurled bar; a flared plinth over a bead row.
    Returns (svg, (tx, ty, tw, th)), the tablet."""
    o = []
    kb = max(5, min(10, h * .11))
    inset = w * .035
    o.append(C.knurled_bar(x, y, w, kb))
    yy = y + kb
    slab = h * .5
    top = slab * .22
    o.append(f'<path d="M{_n(x + inset)},{_n(yy)}h{_n(w - 2 * inset)}v{_n(slab)}h{_n(-(w - 2 * inset))}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="M{_n(x + inset)},{_n(yy)}h{_n(w - 2 * inset)}l{_n(-inset * .5)},{_n(top)}'
             f'h{_n(-(w - 3 * inset))}z" fill="{C.pat("L")}" stroke="#000" stroke-width=".5"/>')
    fy = yy + top
    fh = slab - top
    o.append(f'<path d="M{_n(x + inset * 1.5)},{_n(fy)}h{_n(w - 3 * inset)}v{_n(fh)}'
             f'h{_n(-(w - 3 * inset))}z" fill="{C.pat("M")}" stroke="#000" stroke-width="1"/>')
    th = fh * .84
    tw = w * .62
    tx, ty = x + (w - tw) / 2, fy + (fh - th) / 2
    o.append(f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(tx + .5)},{_n(ty + .5)}h{_n(tw - 1)}l-1.5,1.5h{_n(-(tw - 4))}v{_n(th - 4)}l-1.5,1.5z" fill="#000" stroke="none"/>')
    for sx in (-1, 1):
        rx = x + w / 2 + sx * (tw / 2 + (w - 3 * inset - tw) / 4)
        rcy = fy + fh / 2
        rr = min(fh * .32, 9)
        o.append(f'<path d="{_d(C._ell_pts(rx, rcy, rr, rr, 24), True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        petals = "".join(_d([(rx, rcy), (rx + rr * .9 * math.cos(a + .25), rcy + rr * .9 * math.sin(a + .25)),
                             (rx + rr * .9 * math.cos(a - .25), rcy + rr * .9 * math.sin(a - .25))], True, 0)
                         for a in [TAU * i / 8 for i in range(8)])
        o.append(f'<path d="{petals}" fill="{C.pat("D")}" stroke="#000" stroke-width=".5"/>')
        o.append(f'<path d="{_d(C._ell_pts(rx, rcy, rr * .25, rr * .25, 10), True, 0)}" fill="#000"/>')
    yy = fy + fh
    o.append(C.knurled_bar(x + inset * .4, yy, w - inset * .8, kb))
    yy += kb
    ph = y + h - yy
    if ph > 6:
        fl = [(x + inset * 1.2 - inset * 1.1 * (i / 12) ** 2.2, yy + ph * .7 * i / 12) for i in range(13)]
        fr = [(2 * x + w - p[0], p[1]) for p in fl[::-1]]
        o.append(f'<path d="{_d(fl + fr, True, 0)}" fill="{C.pat("V")}" stroke="none"/>')
        o.append(f'<path d="{_d(fl, tol=0)}{_d(fr, tol=0)}" stroke="#000" stroke-width="1"/>')
        o.append(C.bead_moulding(x + inset * .1, yy + ph * .85, w - inset * .2, max(1., ph * .12)))
    return "".join(o), (tx, ty, tw, th)


def _field_bbox(d_pts):
    xs = [p[0] for p in d_pts]
    ys = [p[1] for p in d_pts]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def layout_band(w, h, ctx, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.6, 120)
    o.append(C._clip(C._uid("fb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fld = C._ell_pts(cx, cy, rx - 2.2, ry - 2.2, 64)
    bx, by, bw, bh = _field_bbox(fld)
    o.append(scene(bx, by, bw, bh, _d(fld, True, 0), ctx, C._uid("fsb", w, h)))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2.2, ry - 2.2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def layout_medium(w, h, ctx, seed, density=1.):
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
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("fm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fld = _field_pts(cx, cy, cw, gh + 4)
    bx, by, bw, bh = _field_bbox(fld)
    o.append(scene(bx, by, bw, bh, fd, ctx, C._uid("fsm", w, h)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _field_pts(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a, b)


def layout_tall(w, h, ctx, seed, density=1.):
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
    cw, ch = pw * .5, ph * .66
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("ft", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fld = _field_pts(cx, cy, cw, ch)
    bx, by, bw, bh = _field_bbox(fld)
    o.append(scene(bx, by, bw, bh, fd, ctx, C._uid("fst", w, h)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh_ = min(18, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .5, cw * 1.45, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lt, _ = banner_letters(centre, "LITTLE ONE", bh_ * .5)
    o.append(lt)
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = my_pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(steam_train(tx + 2, ty + 2, tw - 3, th - 3, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("ff", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", "2026-11-11"))) + 11
    if h < 110:
        body = layout_band(w, h, ctx, seed)
    elif h <= 260:
        body = layout_medium(w, h, ctx, seed)
    else:
        body = layout_tall(w, h, ctx, seed)
    return C.svg_doc(w, h, body)
