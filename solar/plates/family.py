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
    kk_sky(cv, x, y, w, gy + 2, int(w + h), 0)


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


def _rect_d(x, y, w, h):
    return f"M{_kn(x)},{_kn(y)}h{_kn(w)}v{_kn(h)}h{_kn(-w)}z"


def _ell_d(cx, cy, rx, ry, n=72):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n)[:-1], True, .1)


def kk_beads(pts, r=1.5):
    """Beads (white, .5 outlined, a black shadow speck lower right) centred on pts. 2 elements."""
    rr = _kn(r)
    a = "".join(f"M{_kn(x - r)},{_kn(y)}a{rr},{rr} 0 1,0 {_kn(2 * r)},0a{rr},{rr} 0 1,0 {_kn(-2 * r)},0z" for x, y in pts)
    s = max(.5, round(r * .7 * 2) / 2)
    b = "".join(f"M{_kn(x + r * .25)},{_kn(y + r * .2)}h{_kn(s)}v{_kn(s)}h{_kn(-s)}z" for x, y in pts)
    return (f'<path d="{a}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{b}" fill="#000" stroke="none"/>')


def _along(poly, pitch, closed=True):
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

def _leaf(cv, x, y, ang, L, W, c, teeth=2, seed=0):
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


class _Spiral:
    __slots__ = ("cx", "cy", "r", "w", "par", "kids", "pts", "S", "deg")

    def __init__(self, cx, cy, r):
        self.cx, self.cy, self.r = cx, cy, r
        self.w = 1
        self.par = None
        self.kids = []
        self.pts = None


def _spiral_pts(cx, cy, R, th0, w, turns=1.45, end=.15):
    T = _TAU * turns
    b = -_m.log(end) / T
    n = max(24, int(R * T * .35))
    return [(cx + R * _m.exp(-b * T * i / n) * _m.cos(th0 + w * T * i / n),
             cy + R * _m.exp(-b * T * i / n) * _m.sin(th0 + w * T * i / n)) for i in range(n + 1)]


def _bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _resample(pts, step=1.5):
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
        s = _Spiral(px + rng.uniform(-.4, .4) * gx, py + rng.uniform(-.4, .4) * gy, r)
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
        rn = _Spiral(rx_, ry_, 0.)
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
        spi = _spiral_pts(s.cx, s.cy, R, th0, s.w, rng.uniform(1.3, 1.6))
        S0 = spi[0]
        st = (spi[1][0] - S0[0], spi[1][1] - S0[1])
        sl = _m.hypot(*st) or 1.
        st = (st[0] / sl, st[1] / sl)
        L = _m.hypot(S0[0] - P0[0], S0[1] - P0[1])
        k = max(2., L * .42)
        stem = _bez(P0, (P0[0] + t0[0] * k, P0[1] + t0[1] * k), (S0[0] - st[0] * k, S0[1] - st[1] * k), S0,
                    max(4, int(L / 2)))
        s.pts = _resample(stem[:-1] + spi, 1.4)
        s.S = len(_resample(stem[:-1], 1.4)) if len(stem) > 1 else 0
    # paint: twigs first, root last
    for s in order[::-1]:
        _scroll(cv, s, rng, leafy)


def _scroll(cv, s, rng, leafy):
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
        _leaf(cv, b[0], b[1], tang(i) - ins * rng.uniform(.32, .5), ll, ll * .32, ins, 2 if ll > 6 else 1,
              rng.randrange(97))
    for (j, side) in st:
        b = Rb.at(j / (n - 1), side * .6)
        ll = min(9., s.r * .7) * rng.uniform(.8, 1.)
        if ll > 3:
            _leaf(cv, b[0], b[1], tang(j) + side * .7, ll, ll * .3, -side, 1, rng.randrange(97))
    # the stem: a bright cut edge outside, a shadow line inside
    cv.obj([Rb.outline()], .5)
    if w0 > 1.2:
        cv.hair(Rb.contour(.3 * ins, 0., 1., minw=1.25))
    # one leaf rolling in toward the eye
    i = iS + int((n - iS) * .55)
    if i < n - 2 and s.r > 7:
        b = Rb.at(i / (n - 1), ins * .5)
        ll = s.r * .42
        _leaf(cv, b[0], b[1], tang(i) + ins * .35, ll, ll * .28, ins, 1, rng.randrange(97))
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
    o.append(f'<path d="{_rect_d(x - 3, y - 3, w + 6, h + 6)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_rect_d(x - 1.25, y - 1.25, w + 2.5, h + 2.5)}" fill="none" stroke="#000" stroke-width=".5"/>')
    # bead row in a white channel outside
    g = 3 + bead + 1.5
    o.append(f'<path d="{_rect_d(x - g - bead - 1.5, y - g - bead - 1.5, w + 2 * (g + bead + 1.5), h + 2 * (g + bead + 1.5))}'
             f'{_rect_d(x - 3.5, y - 3.5, w + 7, h + 7)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    pts = _along([(x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)], bead * 2 + 1)
    o.append(kk_beads(pts, bead))
    e = g + bead + 1.5
    o.append(f'<path d="{_rect_d(x - e, y - e, w + 2 * e, h + 2 * e)}" fill="none" stroke="#000" stroke-width="1"/>')
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
    return (f'<path d="{_ell_d(cx, cy, r + 1, r + 1, 24)}" fill="#000" stroke="none"/>'
            f'<path d="{d}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{_ell_d(cx, cy, r * .28, r * .28, 10)}" fill="#fff" stroke="#000" stroke-width=".5"/>')


def kk_medallion(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval scene: a black fillet, a bead ring, a gold wire and a fine
    rule. Returns (svg_over, clip_d of the scene, outer rx, outer ry)."""
    o = []
    g = 2.5
    a1, b1 = rx + g + bead, ry + g + bead
    outer = (rx + g + 2 * bead + 3.5, ry + g + 2 * bead + 3.5)
    o.append(f'<path d="{_ell_d(cx, cy, outer[0], outer[1])}{_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + g - .25, ry + g - .25)}" fill="none" stroke="#000" stroke-width=".5"/>')
    per = _C._ell_pts(cx, cy, a1, b1, 180)[:-1]
    o.append(kk_beads(_along(per, bead * 2 + 1.1), bead))
    o.append(f'<path d="{_ell_d(cx, cy, a1 + bead + 1, b1 + bead + 1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_ell_d(cx, cy, outer[0] - .5, outer[1] - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), _ell_d(cx, cy, rx + .5, ry + .5), outer[0], outer[1]


def kk_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
# ---- a leaner emitter: half-px path units, coarser simplification --------------------------

def _pd(pen):
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


def _zig(lines):
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
            res.append(f'<path{T} d="{_pd(pen)}" fill="#fff" stroke="none"/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _C._Pen()
                for pl in out[w]:
                    pen.add(pl, False, tol_line if w < 1 else tol_line + .05)
                res.append(f'<path{T} d="{_pd(pen)}" fill="none" stroke="#000" stroke-width="{_kn(w * q)}"/>')
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


def _pd_poly(poly, close=True):
    return _C._d(poly, close, .1)


def kk_bead_row(d, r=1.5, closed=True):
    """A row of beads along any path d: a black channel, white beads with round caps on a dash
    pattern, and a black speck in each bead's shadow. 3 elements, whatever the length."""
    p = r * 2 + 1.
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_kn(2 * r + 2)}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_kn(2 * r)}" stroke-dasharray="0 {_kn(p)}" stroke-linecap="round"/>'
            f'<path d="{d}" transform="translate(.5,.5)" fill="none" stroke="#000" stroke-width="1" stroke-dasharray="0 {_kn(p)}" stroke-linecap="round"/>')


def kk_border(poly, bead=1.5):
    """Gold-line border round a panel whose clockwise outline is poly: from the panel out, a 1 px
    rule, a bright gap, a fine rule, a bead row, a 1 px rule. Returns (svg, total width)."""
    o = []
    g1 = kk_offset(poly, .5)
    g2 = kk_offset(poly, 2.75)
    gb = kk_offset(poly, 4. + bead)
    ge = kk_offset(poly, 5.5 + 2 * bead)
    o.append(f'<path d="{_pd_poly(ge)}{_pd_poly(poly[::-1])}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_pd_poly(g1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_pd_poly(g2)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_pd_poly(gb), bead))
    o.append(f'<path d="{_pd_poly(ge)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), 5.5 + 2 * bead + .5


def kk_ring(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval: a 1.5 rule, a gold gap, a fine rule, a bead ring, a rule.
    Returns (svg, outer rx, outer ry)."""
    o = []
    e = 5.5 + 2 * bead
    o.append(f'<path d="{_ell_d(cx, cy, rx + e, ry + e)}{_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + 2.75, ry + 2.75)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_ell_d(cx, cy, rx + 4 + bead, ry + 4 + bead), bead))
    o.append(f'<path d="{_ell_d(cx, cy, rx + e - .5, ry + e - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), rx + e, ry + e


# ---- Easter eggs: small figures cut white out of the matte --------------------------------

def _U(cx, cy, r, pts):
    return [(cx + px * r, cy + py * r) for px, py in pts]


def _cut(cv, poly, ang=45., pitch=1.5):
    cv.hair(_zig(_C.hatch_poly(poly, ang, pitch)))


def _wline(cv, pts, hw):
    """A white line hw px each side of pts, cut out of the matte."""
    pts = _resample(pts, 1.5) if len(pts) > 1 else pts
    if len(pts) < 2:
        return
    R = _C._Rib(pts, [hw] * len(pts), [hw] * len(pts))
    cv.obj([R.outline()], 0)


def kk_egg(kind, cx, cy, r):
    """A small engraved figure filling a disc of radius r (white relief, fine shadow cuts)."""
    cv = _C.Canvas()
    E = lambda pts: _U(cx, cy, r, pts)
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
            _cut(cv, _C._ell_pts(cx + r * .08, cy + r * .08, r * .3, r * .3, 18)[:-1], -45, 1.5)
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
        _cut(cv, [p for p in e if p[1] > cy - r * .2], 60, 1.5)
        cv.obj([_C._ell_pts(cx, cy - r * .25, r * .14, r * .07, 12)[:-1]], .5)
    elif kind == "note":
        for dx in (-.42, .38):
            cv.obj([_C._ell_pts(cx + dx * r - r * .05, cy + r * .5, r * .24, r * .16, 16)[:-1]], 1.)
            cv.line(_C.hatch_poly(_C._ell_pts(cx + dx * r - r * .05, cy + r * .5, r * .2, r * .12, 14)[:-1], 0, 1.))
            cv.obj([E([(dx + .15, .5), (dx + .2, .5), (dx + .2, -.6), (dx + .15, -.6)])], .5)
        cv.obj([E([(-.27, -.62), (.58, -.72), (.58, -.5), (-.27, -.4)])], .5)
        cv.line(_C.hatch_poly(E([(-.27, -.62), (.58, -.72), (.58, -.5), (-.27, -.4)]), 0, 1.))
    elif kind == "P":
        stem = E([(-.45, -.8), (-.12, -.8), (-.12, .8), (-.45, .8)])
        bowl = [(cx - r * .14 + r * .5 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .42 * _m.sin(t))
                for t in [(-_PI / 2) + _PI * i / 20 for i in range(21)]]
        inner = [(cx - r * .14 + r * .28 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .2 * _m.sin(t))
                 for t in [(-_PI / 2) + _PI * i / 16 for i in range(17)]]
        cv.obj([bowl + inner[::-1]], 1.)
        _cut(cv, bowl + inner[::-1], -45, 1.5)
        cv.obj([stem], 1.)
        _cut(cv, E([(-.25, -.8), (-.12, -.8), (-.12, .8), (-.25, .8)]), 90, 1.5)
        cv.obj([E([(-.62, .62), (.05, .62), (.05, .8), (-.62, .8)]), E([(-.62, -.8), (-.05, -.8), (-.05, -.66), (-.62, -.66)])], .5)
    elif kind == "bridge":
        for tx in (-.45, .45):
            cv.obj([E([(tx - .09, .85), (tx - .05, -.75), (tx, -.92), (tx + .05, -.75), (tx + .09, .85)])], .5)
            cv.hair([(cx + (tx + .03) * r, cy - r * .7), (cx + (tx + .05) * r, cy + r * .8)])
            cv.hair(E([(tx - .05, -.35), (tx + .05, -.35)]))
        deck = E([(-1, .3), (1, .3), (1, .4), (-1, .4)])
        cv.obj([deck], .5)
        main = [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)) for t in [-.45 + .9 * i / 20 for i in range(21)]]
        _wline(cv, main, .7)
        for sg in (-1, 1):
            _wline(cv, [(cx + sg * r * (.45 + .53 * k / 8), cy - r * .72 + r * 1.02 * (k / 8) ** 1.6) for k in range(9)], .7)
        for k in range(1, 9):
            t = -.45 + .9 * k / 9
            _wline(cv, [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)), (cx + r * t, cy + r * .3)], .5)
    elif kind == "hood":
        m = E([(-1, .7), (-.55, .1), (-.2, -.55), (0, -.8), (.15, -.62), (.5, -.05), (1, .7)])
        cv.obj([m], .5)
        _cut(cv, E([(0, -.8), (.15, -.62), (.5, -.05), (1, .7), (.1, .7)]), -60, 1.5)
        snow = E([(-.35, -.3), (-.2, -.55), (0, -.8), (.15, -.62), (.3, -.35), (.15, -.42), (.02, -.25), (-.12, -.4)])
        cv.obj([snow], .5)
        for k in range(5):
            t = -.3 + k * .15
            cv.hair(E([(0, -.75), (t * .6, -.35)]))
    elif kind == "heron":
        body = E([(-.5, .05), (-.1, -.2), (.35, -.12), (.55, .05), (.2, .25), (-.35, .2)])
        neck = E([(.25, -.15), (.15, -.55), (.3, -.82), (.45, -.82), (.62, -.78), (.4, -.72), (.3, -.55), (.38, -.15)])
        cv.obj([body], .5)
        _cut(cv, E([(-.5, .05), (-.1, -.05), (.55, .05), (.2, .25), (-.35, .2)]), 30, 1.5)
        cv.obj([neck], .5)
        cv.line(E([(.62, -.78), (.95, -.74)]))
        cv.line(E([(.0, .2), (.05, .95)]))
        cv.line(E([(.15, .2), (.25, .95)]))
        cv.line(E([(-.75, .97), (.8, .97)]))
    elif kind == "kranok":
        # a Thai kranok flame: a tall leaf rising, its back serrated into flame tongues, the tip
        # hooking over, a smaller flame nested inside it and a curl at its foot
        _leaf(cv, cx - r * .25, cy + r * .9, -_PI / 2 + .25, r * 1.85, r * .5, -1, 4, 3)
        _leaf(cv, cx - r * .1, cy + r * .7, -_PI / 2 + .35, r * 1.1, r * .3, -1, 2, 5)
        _wline(cv, [(cx - r * .25 + r * .4 * _m.cos(t), cy + r * .62 + r * .3 * _m.sin(t)) for t in [_PI * (.1 + 1.4 * k / 12) for k in range(13)]], .6)
    elif kind == "elephant":
        b = E([(-.75, .1), (-.6, -.35), (-.1, -.5), (.3, -.45), (.55, -.6), (.8, -.4), (.85, 0), (.78, .4),
               (.7, .65), (.62, .3), (.55, .15), (.45, .7), (.3, .7), (.28, .25), (-.35, .25), (-.38, .7),
               (-.55, .7), (-.58, .2)])
        cv.obj([b], .5)
        _cut(cv, E([(-.75, .1), (-.35, .25), (.28, .25), (.55, .15), (.5, -.1), (-.6, -.1)]), 20, 1.5)
        cv.hair(E([(.35, -.4), (.42, -.05), (.25, .05)]))
        cv.obj([E([(-.3, -.48), (.1, -.48), (.05, -.1), (-.25, -.1)])], .5)
        for k in range(4):
            cv.hair(E([(-.27 + k * .1, -.45), (-.25 + k * .1, -.13)]))
    elif kind == "panel":
        fr = E([(-.85, -.2), (.55, -.75), (.85, .2), (-.55, .75)])
        cv.obj([fr], 1.)
        _cut(cv, fr, -22, 1.5)
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
                _cut(cv, poly, a0 * 57 + 30, 1.5)
    elif kind == "paw":
        cv.obj([_C._ell_pts(cx, cy + r * .3, r * .38, r * .32, 20)[:-1]], .5)
        _cut(cv, _C._ell_pts(cx + r * .05, cy + r * .35, r * .3, r * .24, 16)[:-1], -45, 1.5)
        for a in (-2.4, -1.85, -1.3, -.75):
            px, py = cx + r * .62 * _m.cos(a), cy + r * .1 + r * .62 * _m.sin(a)
            cv.obj([_C._ell_pts(px, py, r * .15, r * .19, 12)[:-1]], .5)
    elif kind == "fleur":
        mid = E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4), (-.1, .25), (-.22, -.2), (-.2, -.62)])
        cv.obj([mid], .5)
        _cut(cv, E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4)]), 70, 1.5)
        cv.hair(E([(0, -.85), (0, .3)]))
        for sg in (-1, 1):
            pet = E([(sg * .12, .2), (sg * .45, -.25), (sg * .8, -.42), (sg * .95, -.2), (sg * .78, -.05),
                     (sg * .62, -.18), (sg * .45, .05), (sg * .3, .38)])
            cv.obj([pet], .5)
            _cut(cv, pet, -sg * 50, 1.5)
            cv.obj([_C._ell_pts(cx + sg * r * .82, cy - r * .28, r * .1, r * .1, 10)[:-1]], .5)
        band = E([(-.42, .32), (.42, .32), (.42, .5), (-.42, .5)])
        cv.obj([band], .5)
        _cut(cv, band, 90, 1.5)
        cv.obj([E([(-.15, .5), (.15, .5), (.1, .95), (0, .82), (-.1, .95)])], .5)
    else:   # "dog": a retriever's head in profile, looking left
        head = E([(.55, .9), (.35, .25), (.1, .05), (-.15, .05), (-.55, .12), (-.82, .05), (-.88, -.12),
                  (-.7, -.22), (-.35, -.3), (-.1, -.55), (.2, -.62), (.45, -.5), (.62, -.2), (.75, .35), (.9, .9)])
        cv.obj([head], .5)
        _cut(cv, E([(.35, .25), (.62, -.2), (.75, .35), (.9, .9), (.55, .9)]), 75, 1.5)
        ear = E([(.15, -.55), (.42, -.48), (.5, -.1), (.42, .35), (.3, .4), (.22, .0)])
        cv.obj([ear], .5)
        _cut(cv, ear, 80, 1.5)
        cv.obj([_C._ell_pts(cx - r * .86, cy - r * .1, r * .07, r * .07, 8)[:-1]], 1.)
        cv.line(_C._ell_pts(cx - r * .12, cy - r * .3, r * .05, r * .05, 8))
        cv.hair(E([(-.82, .05), (-.5, .1)]))
    return cv.svg()


def kk_roundel(cx, cy, r, kind, bead=1.2):
    """An egg in a small bead-ringed roundel on the matte."""
    ring, ox, oy = kk_ring(cx, cy, r, r, bead)
    return (f'<path d="{_ell_d(cx, cy, r + .5, r + .5, 40)}" fill="url(#kkM)" stroke="none"/>'
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

def kk_plate(w, h, scene, egg="dog", seed=0, arms=False, egg2=None, dens=1., limit=188000):
    """The whole plate, edge to edge, by height:
      h < 110   band: a bead row and gold line hang under the text; the matte carries fine scroll
                flowing out both ways from an oval medallion (the scene); an egg roundel.
      110-260   a cut-cornered panel in a gold-line, beaded border; spandrels of scroll and
                rosettes outside it; the medallion at the centre, scroll flowing from its foot.
      > 260     an arched panel: a great oval copperplate scene; under it a roundel (the arms
                placeholder on fronts, else the egg); spandrels; a bordered frieze at the foot
                with scroll flowing both ways from a palmette.
    scene(x, y, w, h, mode) -> svg filling that rect (it is clipped to the oval)."""
    rng = _r.Random(seed)
    o = [kk_defs()]
    field = _C.Canvas()

    deferred = []

    def run_field(box, obst, roots, rmin, rmax, inside=None, poly=None, sd=0, area=None, cut=None):
        d = (_pd_poly(poly) if poly else _rect_d(*box)) + (_pd_poly(cut) if cut else "")
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
        (field bytes ~ 19 * area / rmin^1.2, measured)."""
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

    if h < 110:
        top = 8.
        gy, gh = top, h - top - 3
        cx, cy = w / 2, gy + gh / 2
        ry = gh / 2 - 7.5
        rx = min(w * .17, max(ry * 2.2, 26))
        obst = [("e", cx, cy, rx + 9, ry + 9)]
        er = min(gh / 2 - 7, 17)
        ex = w * (.13 if seed % 2 else .87)
        obst.append(("c", ex, cy, er + 7))
        run_field((0, gy, w, gh), obst, [(cx - rx - 8, cy, 180), (cx + rx + 8, cy, 0)],
                  max(4.5, gh * .1), max(9, gh * .33), sd=1, area=w * gh - _PI * (rx + 9) * (ry + 9) - _PI * (er + 7) ** 2)
        o.append(kk_clip(_C._uid("kks", w, h, seed), _ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "band")))
        ring, _, _ = kk_ring(cx, cy, rx, ry, 1.)
        o.append(ring)
        rr, _ = kk_roundel(ex, cy, er, egg, 1.)
        o.append(rr)
        o.append(f'<path d="M0,1.5H{_kn(w)}M0,{_kn(top - .5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(kk_bead_row(f"M0,{_kn(top / 2 + .25)}H{_kn(w)}", 1., False))
        o.append(f'<path d="M0,{_kn(h - 1.5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(f'<path d="M0,{_kn(h - 2.75)}H{_kn(w)}" stroke="#000" stroke-width=".5"{_C._CR}/>')
        return finish()

    if h <= 260:
        m = 10.
        c = min(30., h * .17)
        poly = kk_shape("cut", m, m, w - 2 * m, h - 2 * m, c)
        # the spandrels and margins: matte with small scroll
        outer = kk_inside(kk_offset(poly, 9.))
        run_field((0, 0, w, h), [], [(0, 0, 45), (w, 0, 135), (w, h, -135), (0, h, -45)], 4.5, 10.,
                  lambda px, py: not outer(px, py), sd=2, cut=kk_offset(poly, 4.))
        cx, cy = w / 2, h / 2
        ry = (h - 2 * m) / 2 - 12
        rx = min(w * .2, ry * 1.25)
        er = min(15., h * .1)
        ex = cx + (rx + 30 + er) * (-1 if seed % 2 else 1)
        obst = [("e", cx, cy, rx + 10, ry + 10), ("c", ex, cy, er + 8)]
        border, bw = kk_border(poly)
        for q in _along(poly, 3.):
            obst.append(("c", q[0], q[1], 3.))
        run_field((m, m, w - 2 * m, h - 2 * m), obst,
                  [(cx - rx * .55, cy + ry + 8, 160), (cx + rx * .55, cy + ry + 8, 20), (cx, cy - ry - 9, 0 if seed % 2 else 180)],
                  max(6, h * .045), max(13, h * .14), kk_inside(poly), poly, 3,
                  area=(w - 2 * m) * (h - 2 * m) - 2 * c * c - _PI * (rx + 10) * (ry + 10) - _PI * (er + 8) ** 2)
        o.append(border)
        for p in (poly[0], poly[2], poly[4], poly[6]):
            pass
        for (qx, qy) in ((m * .6 + c * .3, m * .6 + c * .3), (w - m * .6 - c * .3, m * .6 + c * .3),
                         (w - m * .6 - c * .3, h - m * .6 - c * .3), (m * .6 + c * .3, h - m * .6 - c * .3)):
            o.append(kk_rosette(qx, qy, 3.6))
        o.append(kk_clip(_C._uid("kks", w, h, seed), _ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "medium")))
        ring, _, _ = kk_ring(cx, cy, rx, ry, 1.5)
        o.append(ring)
        rr, _ = kk_roundel(ex, cy, er, egg, 1.)
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
    ry = min(ph * .4, 175)
    rx = min((w - 2 * m) * .4, ry * 1.08)
    cy = m + rise * .5 + ry + 18
    rr_ = min(24., ph * .07)
    ey = min(cy + ry + 14 + rr_ + 6, yb - rr_ - 10)
    obst = [("e", cx, cy, rx + 10, ry + 10), ("c", cx, ey, rr_ + 10)]
    for q in _along(poly, 3.):
        obst.append(("c", q[0], q[1], 3.))
    roots = [(cx - rr_ - 10, ey, 180), (cx + rr_ + 10, ey, 0), (cx, cy - ry - 10, 0 if seed % 2 else 180)]
    run_field((m, m, w - 2 * m, ph), obst, roots, max(9, h * .019), max(19, h * .048), kk_inside(poly), poly, 5,
              area=(w - 2 * m) * ph - _PI * (rx + 10) * (ry + 10) - _PI * (rr_ + 10) ** 2 - .43 * rise * (w - 2 * m))
    o.append(border)
    o.append(kk_clip(_C._uid("kks", w, h, seed), _ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "tall")))
    ring, _, _ = kk_ring(cx, cy, rx, ry, 1.5)
    o.append(ring)
    rr, _ = kk_roundel(cx, ey, rr_, "arms" if arms else egg, 1.2)
    o.append(rr)
    # the frieze
    fy = yb + 8
    fp = kk_shape("rect", m + 6, fy + 4, w - 2 * m - 12, h - fy - 8)
    fb, _ = kk_border(fp, 1.2)
    pr = (h - fy - 8) / 2 - 1
    pcx, pcy = w / 2, fy + 4 + (h - fy - 8) / 2
    o.append(kk_matte(_rect_d(0, yb + 4, w, h - yb - 4)))
    run_field((m + 6, fy + 4, w - 2 * m - 12, h - fy - 8), [("c", pcx, pcy, pr * 1.05)] + ([("c", w * .2, pcy, pr * .8)] if egg2 else []),
              [(pcx - pr, pcy, 180), (pcx + pr, pcy, 0)], max(5.5, pr * .42), pr * 1.05, sd=7)
    o.append(fb)
    o.append(kk_egg(egg2 or "fleur", pcx, pcy, pr * .95))
    return finish()


# ---- the plate ------------------------------------------------------------------------------

def plate(w, h, ctx):
    """Little one (section front): blanket-fort story time under the evening sky in the inlaid
    medallion; on tall plates the arms placeholder (crossed drumsticks over a sun) under it; the
    dog asleep at the fort door and a paw roundel in the scroll (the Easter eggs)."""
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)

    def sc(x, y, ww, hh, mode):
        X, Y, W, H = x - 2, y - 2, ww + 4, hh + 4
        return scene(X, Y, W, H, _rect_d(X, Y, W, H), ctx, "fm%d" % int(hh * 10))
    return kk_plate(w, h, sc, egg="paw", seed=seed, arms=True)
