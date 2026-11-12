"""garden-01 "Walk the land" -- November on Sauvie Island.
The vignette: a wood-chip path running out across the wet prairie to the cottonwoods along the
lake, Mt. Hood beyond under rain cloud, a skein of tundra swans coming in, more swans resting on
Sturgeon Lake, a kestrel hovering over the grass, a hazel bough with next year's catkins hanging
into the scene, a cluster of mushrooms at the path edge, blackberry creeping in from the edge.
Easter egg: the dog's paw prints walking up the wet path toward the puddle.
Grown into the frame: hazel catkins hang from the upper volutes; the ribbon carries the page
title and the pedestal tablet the island and month, all in path lettering."""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
_n, _d = C._n, C._d

# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------


def ell(cx, cy, rx, ry, n=24, a0=0., a1=2 * PI):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + (0 if a1 - a0 >= 2 * PI - 1e-6 else 1))]


def rot(pts, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def offset(line, widths):
    """Left/right offsets of a centre polyline -> closed outline."""
    L, R = [], []
    n = len(line)
    for i, (x, y) in enumerate(line):
        a, b = line[max(0, i - 1)], line[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        w = widths[i]
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    return L + R[::-1], L, R


def along(line, widths, s):
    out = []
    n = len(line)
    for i, (x, y) in enumerate(line):
        a, b = line[max(0, i - 1)], line[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        out.append((x - dy / m * widths[i] * s, y + dx / m * widths[i] * s))
    return out


def clip_half(poly, y=None, keep_below=True):
    """Clip a polygon by a horizontal line (Sutherland-Hodgman)."""
    out = []
    n = len(poly)
    ins = (lambda p: p[1] >= y) if keep_below else (lambda p: p[1] <= y)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        if ins(p):
            out.append(p)
        if ins(p) != ins(q):
            t = (y - p[1]) / (q[1] - p[1])
            out.append((p[0] + (q[0] - p[0]) * t, y))
    return out


def clip_x(poly, x, keep_right=True):
    out = []
    n = len(poly)
    ins = (lambda p: p[0] >= x) if keep_right else (lambda p: p[0] <= x)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        if ins(p):
            out.append(p)
        if ins(p) != ins(q):
            t = (x - p[0]) / (q[0] - p[0])
            out.append((x, p[1] + (q[1] - p[1]) * t))
    return out


def hp(poly, ang, pitch, phase=0., inset=0.):
    return C.hatch_poly(poly, ang, pitch, phase, inset) if len(poly) > 2 else []


def black(pts_list):
    d = "".join(_d(p, True, 0) for p in pts_list if len(p) > 2)
    return f'<path d="{d}" fill="#000" stroke="none"/>' if d else ""


# ----------------------------------------------------------------------------------------------
# path lettering (a light engraved roman, drawn as strokes)
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_S = [(3.6, .9), (2.8, 0), (1, 0), (.2, .8), (.2, 2.2), (1, 3), (2.8, 3), (3.7, 3.8), (3.7, 5.2), (2.8, 6), (1, 6), (.1, 5.1)]
GLYPH = {
    "A": (4.4, [[(0, 6), (2.2, 0), (4.4, 6)], [(.9, 3.9), (3.5, 3.9)]]),
    "B": (3.8, [[(0, 0), (0, 6), (2.7, 6), (3.8, 5.1), (3.8, 3.9), (2.7, 3), (0, 3)], [(0, 0), (2.5, 0), (3.4, .8), (3.4, 2.2), (2.5, 3)]]),
    "C": (4, [_arc(2.2, 3, 2.2, 3, -40, -320)]),
    "D": (4, [[(0, 0), (0, 6), (1.8, 6), (3.6, 5), (4, 3), (3.6, 1), (1.8, 0), (0, 0)]]),
    "E": (3.4, [[(3.4, 0), (0, 0), (0, 6), (3.4, 6)], [(0, 3), (2.6, 3)]]),
    "F": (3.4, [[(3.4, 0), (0, 0), (0, 6)], [(0, 3), (2.6, 3)]]),
    "G": (4.2, [_arc(2.2, 3, 2.2, 3, -40, -320), [(2.4, 3.6), (4.2, 3.6), (4.2, 5.6)]]),
    "H": (4, [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]]),
    "I": (0, [[(0, 0), (0, 6)]]),
    "J": (3, [[(3, 0), (3, 4.6), (2.1, 6), (.9, 6), (0, 5)]]),
    "K": (3.8, [[(0, 0), (0, 6)], [(3.6, 0), (0, 3.8)], [(1.3, 2.6), (3.8, 6)]]),
    "L": (3.4, [[(0, 0), (0, 6), (3.4, 6)]]),
    "M": (5, [[(0, 6), (0, 0), (2.5, 4.2), (5, 0), (5, 6)]]),
    "N": (4, [[(0, 6), (0, 0), (4, 6), (4, 0)]]),
    "O": (4.4, [_arc(2.2, 3, 2.2, 3, 0, 360, 16)]),
    "P": (3.6, [[(0, 6), (0, 0), (2.6, 0), (3.6, .8), (3.6, 2.4), (2.6, 3.2), (0, 3.2)]]),
    "Q": (4.4, [_arc(2.2, 3, 2.2, 3, 0, 360, 16), [(2.6, 4.4), (4.4, 6.4)]]),
    "R": (3.8, [[(0, 6), (0, 0), (2.6, 0), (3.6, .8), (3.6, 2.4), (2.6, 3.2), (0, 3.2)], [(2.2, 3.2), (3.8, 6)]]),
    "S": (3.7, [_S]),
    "T": (4, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
    "U": (4, [[(0, 0), (0, 4.6), (1, 6), (3, 6), (4, 4.6), (4, 0)]]),
    "V": (4.2, [[(0, 0), (2.1, 6), (4.2, 0)]]),
    "W": (5.8, [[(0, 0), (1.4, 6), (2.9, 1.4), (4.4, 6), (5.8, 0)]]),
    "X": (4, [[(0, 0), (4, 6)], [(4, 0), (0, 6)]]),
    "Y": (4, [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]]),
    "Z": (4, [[(0, 0), (4, 0), (0, 6), (4, 6)]]),
    "'": (0, [[(0, 0), (0, 1.6)]]),
    "-": (2.4, [[(0, 3), (2.4, 3)]]),
    ".": (0, [[(0, 5.6), (0, 6)]]),
}
GAP, SPACE = 1.7, 3.2


def text_width(s):
    w = 0
    for ch in s:
        if ch == " ":
            w += SPACE
        else:
            w += GLYPH.get(ch, (3, []))[0] + GAP
    return w - GAP if s else 0


def text_strokes(s, x, y, size):
    """Strokes of s with the cap height `size`, top-left at (x, y)."""
    k = size / 6.
    out = []
    for ch in s:
        if ch == " ":
            x += SPACE * k
            continue
        gw, polys = GLYPH.get(ch, (3, []))
        for p in polys:
            out.append([(x + px * k, y + py * k) for px, py in p])
        x += (gw + GAP) * k
    return out


def text_on_curve(s, centre, size):
    """Letter s along a centre line (list of points), centred, each glyph turned to the tangent."""
    acc = [0.]
    for i in range(1, len(centre)):
        acc.append(acc[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    total = acc[-1]
    k = size / 6.

    def at(d):
        d = max(0, min(total, d))
        for i in range(1, len(acc)):
            if acc[i] >= d:
                t = (d - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
                a, b = centre[i - 1], centre[i]
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
        return centre[-1], 0.
    pos = (total - text_width(s) * k) / 2
    out = []
    for ch in s:
        if ch == " ":
            pos += SPACE * k
            continue
        gw, polys = GLYPH.get(ch, (3, []))
        (px, py), a = at(pos + gw * k / 2)
        for p in polys:
            q = [((gx - gw / 2) * k, (gy - 3) * k) for gx, gy in p]
            out.append([(px + qx * math.cos(a) - qy * math.sin(a), py + qx * math.sin(a) + qy * math.cos(a)) for qx, qy in q])
        pos += (gw + GAP) * k
    return out


def strokes_svg(strokes, w=1.):
    d = "".join(_d(p, tol=0) for p in strokes)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w)}" stroke-linecap="square" stroke-linejoin="miter"/>' if d else ""


# ----------------------------------------------------------------------------------------------
# the subjects
# ----------------------------------------------------------------------------------------------

def catkin(cv, x, y, length, cw, sway=0., rng=None):
    """A hazel catkin hanging from (x, y): a tapered tassel of imbricate scales, shaded on its
    right flank, each scale a small chevron."""
    n = 14
    line = [(x + sway * length * (i / n) ** 2, y + length * i / n) for i in range(n + 1)]
    wd = [cw * .5 * (.55 + .45 * math.sin(PI * min(1., .15 + i / n * .95))) for i in range(n + 1)]
    wd[-1] = cw * .18
    out, L, R = offset(line, wd)
    tip = (line[-1][0] + sway * cw, line[-1][1] + cw * .4)
    cv.obj([], 0)
    cv.line([(x - sway * 2, y - cw * .9), line[0]])
    cv.obj([L + [tip] + R[::-1]], .5)
    for s in (-.35, -.65, -.85):
        cv.hair(along(line, wd, s)[1:-1])
    k = max(3, int(length / (cw * .42)))
    for i in range(1, k):
        u = i / k
        j = min(n - 1, int(u * n))
        f = u * n - j
        cx_ = line[j][0] + (line[j + 1][0] - line[j][0]) * f
        cy_ = line[j][1] + (line[j + 1][1] - line[j][1]) * f
        w_ = wd[j] + (wd[j + 1] - wd[j]) * f
        cv.hair([(cx_ - w_ * .95, cy_ - w_ * .35), (cx_ - w_ * .2, cy_ + w_ * .25), (cx_ + w_ * .3, cy_ - w_ * .1)])
        cv.hair([(cx_ + w_ * .3, cy_ - w_ * .1), (cx_ + w_ * .95, cy_ - w_ * .45)])


def hazel_leaf(cv, cx, cy, size, ang, rng, flip=1):
    """Ovate, doubly serrate hazel leaf: midrib, pinnate veins, one half shaded along the veins."""
    n = 30
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        x, y = u * size * .5, v * flip
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    def hw(u):
        return size * .4 * math.sqrt(max(0., 1 - u * u)) * (1 - .25 * u) * (1.15 if u < -.6 else 1)
    top, bot = [], []
    for i in range(n + 1):
        u = -1 + 2 * i / n
        z = 1 - (.1 if i % 2 else 0) - (.06 if i % 4 == 1 else 0)
        top.append(P(u, hw(u) * z))
        bot.append(P(u, -hw(u) * z))
    tip = P(1.12, 0)
    outline = top + [tip] + bot[::-1]
    cv.obj([outline], .5)
    cv.line([P(-1.2, 0), P(1.05, 0)])
    cv.hair([P(-1.2, 0), P(-1.45, .08 * size)])
    # shaded half: lines running from the midrib out along the veins
    for i in range(1, 22):
        u = -.95 + 1.85 * i / 22
        cv.hair([P(u, .6), P(u + .16, hw(u + .16) * .74)])
    for k in range(-3, 4):
        u = k / 4.
        for sd in (-1, 1):
            u2 = min(.95, u + .32)
            cv.hair([P(u, 0), P((u + u2) / 2, sd * hw(u) * .5), P(u2, sd * hw(u2) * .86)])


def mushroom(cv, x, y, s, rng, kind=0, lean=0.):
    """A mushroom standing at ground point (x, y), cap radius s. kind 0 plain, 1 warted."""
    top = (x + lean * s, y - s * 1.55)
    sw = s * .22
    stem = [(x - sw * 1.15, y), (top[0] - sw, top[1] + s * .1), (top[0] + sw, top[1] + s * .1), (x + sw * 1.15, y)]
    cv.obj([stem], .5)
    cv.hair(hp([(x + sw * .15, y + 1), (top[0] + sw * .15, top[1]), (top[0] + sw * 2, top[1]), (x + sw * 2, y + 1)], 92, 1.5))
    cv.hair(hp([(x + sw * .7, y), (top[0] + sw * .6, top[1]), (top[0] + sw * 2, top[1]), (x + sw * 2, y)], 92, 1.5, .75))
    # ring
    cv.hair(_arc(top[0], top[1] + s * .45, sw * 1.05, sw * .35, 0, 180, 6))
    # gills: the underside seen from slightly below
    cx, cy = top[0], top[1]
    gill = ell(cx, cy, s * .98, s * .2, 28)
    cv.obj([gill], .5)
    for i in range(1, 22):
        t = PI * i / 22
        gx, gy = cx + math.cos(t) * s * .96, cy + math.sin(t) * s * .18
        cv.hair([(cx + math.cos(t) * sw * .9, cy + sw * .1), (gx, gy)])
    # cap
    cap = [(cx + math.cos(t) * s, cy - math.sin(t) * s * (.82 if kind else .7) - s * .02)
           for t in [PI * i / 26 for i in range(27)]]
    cap += [(cx - s * .8, cy + s * .05), (cx + s * .8, cy + s * .05)][::-1][:0]
    cv.obj([cap], 1.)
    hy = s * (.82 if kind else .7)
    # contour shading following the dome: dense toward the shadowed right and the rim
    for k in range(1, 9):
        f = k / 9.
        arc = [(cx + math.cos(t) * s * (1 - f * .12), cy - math.sin(t) * hy * (1 - f * .95) - s * .02)
               for t in [PI * i / 20 for i in range(21)]]
        lo = 0 if f > .55 else 3
        hi = 21 if f > .7 else (13 if f > .4 else 9)
        seg = arc[lo:hi] if k % 2 or f > .6 else arc[:7]
        cv.hair(seg)
    capr = clip_x(cap, cx + s * .25, True)
    cv.hair(hp(capr, -62, 1.5))
    if kind:
        cv.hair(hp(clip_x(cap, cx - s * .2, True), 30, 3))
        for i in range(9):
            t = PI * (.15 + .7 * rng.random())
            rr = rng.uniform(.25, .8)
            wx, wy = cx + math.cos(t) * s * rr, cy - math.sin(t) * hy * rr * 1.05
            cv.obj([ell(wx, wy, s * .07 + .4, s * .05 + .3, 8)], .5)


def _quad(p0, p1, p2, n=10):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def _wing(x, y, s, up, back=0.):
    """A swan's wing seen from the side: a long arched leading edge to the tip, the trailing
    edge scalloped with primaries. up: raised, else beating down."""
    sh = (x - s * .12 + back, y - s * .06)
    tip = (x + s * .55 + back, y - s * 1.05) if up else (x + s * .5 + back, y + s * .85)
    ctrl = (x - s * .05 + back, y - s * .95) if up else (x - s * .05 + back, y + s * .55)
    lead = _quad(sh, ctrl, tip, 12)
    rear = (x + s * .38 + back, y - s * .02)
    trail = []
    m = 7
    for i in range(m + 1):
        t = i / m
        bx = tip[0] + (rear[0] - tip[0]) * t
        by = tip[1] + (rear[1] - tip[1]) * t
        bx += (s * .12 if up else s * .1) * math.sin(PI * t)
        trail.append((bx, by))
        if 0 < i < m and t < .75:
            trail.append((bx - s * .06, by + (s * .07 if up else -s * .07)))
    return lead + trail, lead, tip, rear


def swan_flying(cv, x, y, s, up, rng):
    """Tundra swan in flight heading left; s is about half the wingspan."""
    far, _, ftip, _ = _wing(x, y, s * .9, up, s * .12)
    cv.obj([far], .5)
    cv.hair(hp(far, 60 if up else -60, 1.5))
    body = [(x - s * .45, y - s * .03)] + _quad((x - s * .4, y - s * .1), (x + s * .1, y - s * .24), (x + s * .62, y - s * .06), 8) + \
        [(x + s * .7, y)] + _quad((x + s * .55, y + s * .08), (x + s * .05, y + s * .28), (x - s * .42, y + s * .05), 8)
    cv.obj([body], .5)
    cv.hair(hp(clip_half(body, y + s * .02, True), 0, 1.5, .25))
    neck = _quad((x - s * .35, y - s * .02), (x - s * .7, y - s * .1), (x - s * 1.0, y - s * .1), 6)
    nk, _, _ = offset(neck, [s * .085 - i * s * .006 for i in range(7)])
    cv.obj([nk], .5)
    hd = ell(x - s * 1.04, y - s * .1, s * .11, s * .07, 10)
    cv.obj([hd], .5)
    cv.heavy([(x - s * 1.12, y - s * .09), (x - s * 1.26, y - s * .06)])
    near, lead, tip, rear = _wing(x, y, s, up)
    cv.obj([near], .5)
    # covert and primary lines laid along the wing
    for f in (.3, .55, .8):
        a = lead[int(f * 6)]
        cv.hair([a, (rear[0] + (tip[0] - rear[0]) * f * .9, rear[1] + (tip[1] - rear[1]) * f * .9)])
    cv.hair(hp([lead[0], lead[6], rear], 0, 1.5, .25))


def swan_resting(cv, x, y, s):
    body = [(x - s, y), (x - s * .6, y - s * .45), (x + s * .5, y - s * .5), (x + s * 1.1, y - s * .7),
            (x + s * .9, y)]
    cv.obj([body], .5)
    cv.hair([(x - s * .5, y - s * .2), (x + s * .6, y - s * .3)])
    nk = [(x - s * .55, y - s * .4), (x - s * .6, y - s * 1.6), (x - s * .95, y - s * 1.65)]
    cv.line(nk)
    cv.hair(hp([(x - s, y + .5), (x + s, y + .5), (x + s, y + s * .6), (x - s, y + s * .6)], 0, 1.5, .25))


def kestrel(cv, x, y, s):
    """A kestrel hanging in the wind, wings spread, tail fanned down."""
    wl = [(x, y), (x - s * .5, y - s * .35), (x - s * 1.2, y - s * .2), (x - s * .5, y + s * .05)]
    wr = [(2 * x - p[0], p[1]) for p in wl]
    tail = [(x - s * .1, y + s * .1), (x - s * .25, y + s * .65), (x + s * .25, y + s * .65), (x + s * .1, y + s * .1)]
    for p in (tail, wl, wr):
        cv.obj([p], .5)
        cv.hair(hp(p, 45, 1.5))
    b = ell(x, y + s * .02, s * .13, s * .26, 10)
    cv.obj([b], .5)
    cv.hair(hp(b, 0, 1.5, .25))


def bramble(cv, x0, y0, s, rng, side=1):
    """Arching blackberry canes with thorns and a few dark leaves."""
    for k in range(3):
        L = s * rng.uniform(1.0, 1.6)
        a0 = -PI / 2 + side * rng.uniform(.3, .7)
        pts = []
        x, y, a = x0 + side * k * s * .2, y0, a0
        for i in range(24):
            pts.append((x, y))
            a += side * .09
            x += math.cos(a) * L / 24
            y += math.sin(a) * L / 24
        cv.obj([], 0)
        cv.line(pts)
        for i in range(2, 23, 3):
            px, py = pts[i]
            cv.hair([(px, py), (px + side * 1.4, py - 1.2)])
        for i in (9, 16):
            px, py = pts[i]
            la = a0 + side * (.9 + .09 * i)
            lf = [(px, py), (px + math.cos(la - .5) * s * .14, py + math.sin(la - .5) * s * .14),
                  (px + math.cos(la) * s * .26, py + math.sin(la) * s * .26),
                  (px + math.cos(la + .5) * s * .14, py + math.sin(la + .5) * s * .14)]
            cv.obj([lf], .5)
            cv.hair(hp(lf, 30, 1.5))


def grass(cv, x, y, L, rng, n=4):
    for j in range(n):
        a = -PI / 2 + rng.uniform(-.5, .5)
        bend = rng.uniform(-.25, .25)
        pts = [(x, y)]
        px, py = x, y
        for i in range(3):
            a += bend
            px += math.cos(a) * L / 3
            py += math.sin(a) * L / 3
            pts.append((px, py))
        cv.hair(pts)


# ----------------------------------------------------------------------------------------------
# the vignette
# ----------------------------------------------------------------------------------------------

def scene(X, Y, W, H, seed, mode="full"):
    """The walk, filling X..X+W, Y..Y+H completely (clip it to the field)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    bl = []                     # small black fills laid on top
    S = min(W, H * 1.6)
    hy = Y + H * (.5 if mode != "band" else .56)
    bot = Y + H + 2

    # sky: ruled, darker aloft
    sky = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, hy + 1), (X - 2, hy + 1)]
    cv.obj([sky], 0)
    yA, yB = Y + (hy - Y) * .38, Y + (hy - Y) * .74
    cv.hair(hp([(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, yA), (X - 2, yA)], 0, 2, .25))
    cv.hair(hp([(X - 2, yA), (X + W + 2, yA), (X + W + 2, yB), (X - 2, yB)], 0, 2, .25))
    cv.hair(hp([(X - 2, yB), (X + W + 2, yB), (X + W + 2, hy + 1), (X - 2, hy + 1)], 0, 3, .25))
    # rain veils trailing from the clouds
    clouds = []
    if mode != "band":
        rc = random.Random(seed + 21)
        for k in range(3 if mode == "full" else 2):
            ccx = X + W * ((.12 + .38 * k) if mode == "full" else (.2 + .55 * k)) + W * rc.uniform(-.04, .04)
            ccy = Y + (hy - Y) * rc.uniform(.2, .32)
            clouds.append((ccx, ccy, S * rc.uniform(.06, .085)))
        for ccx, ccy, cr in clouds[:1]:
            veil = [(ccx - cr * 1.4, ccy + cr * .4), (ccx + cr * 1.2, ccy + cr * .4),
                    (ccx + cr * .4, hy), (ccx - cr * 2.2, hy)]
            cv.hair(hp(veil, 102, 3, 1))
        for ccx, ccy, cr in clouds:
            base = ccy + cr * .45
            puffs = [(-1.7, .15, .5), (1.7, .18, .48), (-.9, -.15, .75), (.9, -.1, .72), (0, -.45, .85), (-.35, -.9, .5)]
            for ox, oy, rr_ in puffs:
                cx2, cy2, r2 = ccx + ox * cr, ccy + oy * cr, rr_ * cr
                circ = [(px, min(py, base)) for px, py in ell(cx2, cy2, r2, r2 * .85, 28)]
                cv.obj([circ], .5)
                lower = clip_half(circ, cy2 + r2 * .15, True)
                cv.hair(hp(lower, 0, 1.5, .25))
                cv.hair(_arc(cx2, cy2, r2 * .78, r2 * .66, 15, 165, 8)[2:-1])
                cv.hair(_arc(cx2 + r2 * .1, cy2, r2 * .55, r2 * .5, 200, 300, 6))

    # Mt. Hood beyond the lake
    if mode != "band":
        mx, mpk = X + W * .66, hy - H * .2
        mw = W * .17
        rr = random.Random(seed + 7)
        L = [(mx - mw * 1.25, hy + 1)]
        for i in range(1, 10):
            t = i / 10
            L.append((mx - mw * 1.25 + mw * 1.25 * t, hy - (hy - mpk) * (t ** 1.7) + rr.uniform(-.5, .5)))
        R = []
        for i in range(1, 10):
            t = i / 10
            R.append((mx + mw * t, mpk + (hy - mpk) * (t ** .8) + rr.uniform(-.5, .5)))
        mtn = L + [(mx, mpk)] + R + [(mx + mw * 1.05, hy + 1)]
        cv.obj([mtn], .5)
        ridge = [(mx, mpk)]
        for i in range(1, 8):
            t = i / 7
            ridge.append((mx - mw * .18 * t + mw * .08 * math.sin(t * 9) + rr.uniform(-.5, .5), mpk + (hy - mpk) * t))
        sh = ridge + [(mx + mw * 1.05, hy + 1)] + R[::-1]
        cv.hair(hp(sh, 62, 1.5))
        # snow gullies on the lit face
        for g in range(4):
            gt = mpk + (hy - mpk) * (.18 + .1 * g)
            gx = mx - mw * (.2 + .22 * g) * ((gt - mpk) / (hy - mpk)) ** .6
            cv.hair([(gx + 1, gt), (gx - 1.5, gt + (hy - mpk) * .14), (gx - 2.5, gt + (hy - mpk) * .26)])
        # timber below the snowline
        sl = mpk + (hy - mpk) * .62
        cv.hair(hp(clip_half(mtn, sl, True), 0, 1.5, .25))

    # cottonwoods along the slough
    rr = random.Random(seed + 11)
    tb = hy + 1
    crowns = []
    x = X - 6
    while x < X + W + 8:
        r = S * rr.uniform(.025, .055) * (.55 if X + W * .48 < x < X + W * .82 else 1.)
        crowns.append((x, tb - r * rr.uniform(.5, 1.2), r))
        x += r * rr.uniform(1.0, 1.5)
    tl = [(X - 4, tb)]
    xx = X - 4
    while xx <= X + W + 4:
        top = tb
        for ccx, ccy, r in crowns:
            if abs(xx - ccx) < r:
                top = min(top, ccy - r * 1.1 * math.sqrt(1 - ((xx - ccx) / r) ** 2))
        tl.append((xx, top))
        xx += .7
    tl.append((X + W + 4, tb))
    cv.obj([tl], .5)
    cv.hair(hp(tl, 0, 1.5, .25))
    cv.hair(hp(tl, 50, 2))

    # the prairie
    gr = [(X - 4, hy + 1), (X + W + 4, hy + 1), (X + W + 4, bot), (X - 4, bot)]
    cv.obj([gr], 0)
    y = hy + 3
    pitch = 3.
    while y < bot:
        cv.hair([(X - 4, y), (X + W + 4, y)])
        f = (y - hy) / (bot - hy)
        y += 3 if f < .35 else (2 if f < .75 else 1.5)
    # tufts, larger toward us
    rr = random.Random(seed + 3)
    for i in range(int(W * H / 170)):
        gx = X + rr.uniform(-2, W + 2)
        f = rr.random() ** .45
        gy = hy + 3 + (bot - hy) * f
        grass(cv, gx, gy, 1.5 + S * .06 * f, rr, 2 + int(3 * f))

    # Sturgeon Lake, swans on the water
    if mode != "band":
        lk0, lk1 = X + W * .46, X + W * .98
        lky = hy + 1.5
        lake = [(lk0, lky)] + [(lk0 + (lk1 - lk0) * i / 12, lky + H * .055 * math.sin(PI * i / 12)) for i in range(13)] + [(lk1, lky)]
        lake = [(lk0, lky)] + [(lk1 - (lk1 - lk0) * i / 12, lky + H * .055 * math.sin(PI * i / 12)) for i in range(13)]
        cv.obj([lake], .5)
        for seg in hp(lake, 0, 2, .25):
            (a, b) = seg
            x0 = a[0]
            while x0 < b[0]:
                x1 = min(b[0], x0 + rr.uniform(3, 12))
                cv.hair([(x0, a[1]), (x1, a[1])])
                x0 = x1 + rr.uniform(1.5, 4)
        for k in range(5 if mode == "full" else 3):
            sx = lk0 + (lk1 - lk0) * (.15 + .15 * k + rr.uniform(-.04, .04))
            swan_resting(cv, sx, lky + H * .025 + rr.uniform(-.5, .5), S * .011 + .8)

    # the wood-chip path running out to the trees
    px0, px1 = X + W * (.36 if mode != "band" else .5), X + W * .52
    wb, wt = min(W, H * 1.6) * (.24 if mode != "band" else .3), 1.5
    cl = []
    for i in range(21):
        t = i / 20
        e = t ** .6
        cl.append((px0 + (px1 - px0) * e + min(W, H * 1.6) * .05 * math.sin(e * PI), bot - (bot - hy - 1.5) * e))
    widths = [wb / 2 * (1 - (i / 20) ** .6) + wt / 2 for i in range(21)]
    path, Lp, Rp = offset(cl, widths)
    cv.obj([path], .5)
    rr = random.Random(seed + 5)
    wmax = widths[0]
    for j in range(20):
        seg = math.hypot(cl[j + 1][0] - cl[j][0], cl[j + 1][1] - cl[j][1])
        ww = widths[j]
        cnt = int(ww * seg * (ww / wmax) ** .5 / 3.2 + rr.random())
        for _ in range(cnt):
            u = rr.random()
            cx_ = cl[j][0] + (cl[j + 1][0] - cl[j][0]) * u + ww * rr.uniform(-.88, .88)
            cy_ = cl[j][1] + (cl[j + 1][1] - cl[j][1]) * u
            L = .5 + ww * .07
            a = rr.uniform(-.5, .5)
            cv.hair([(cx_ - L * math.cos(a), cy_ - L * math.sin(a) * .5), (cx_ + L * math.cos(a), cy_ + L * math.sin(a) * .5)])
    # edges of the path: grass leaning in
    for side in (Lp, Rp):
        for (gx, gy) in side[::2]:
            f = (gy - hy) / (bot - hy)
            if f > .08:
                grass(cv, gx, gy + 1, 1 + S * .05 * f, rr, 2 + int(2 * f))
    # the rain puddle, holding the sky
    if mode != "band":
        j = 6
        pcx, pcy = cl[j][0] + widths[j] * .1, cl[j][1]
        prx, pry = widths[j] * .55, widths[j] * .12 + 1
        pud = ell(pcx, pcy, prx, pry, 24)
        cv.obj([pud], .5)
        cv.hair([seg for seg in hp(pud, 0, 1.5, .25) if not (pcy - pry * .3 < seg[0][1] < pcy + pry * .1)])
        # Easter egg: the dog's paw prints walking up the path to the puddle
        for k in range(4):
            jj = 1 + k * 1.2
            j0 = int(jj)
            u = jj - j0
            bx = cl[j0][0] * (1 - u) + cl[j0 + 1][0] * u + (1 if k % 2 else -1) * widths[j0] * .22
            by = cl[j0][1] * (1 - u) + cl[j0 + 1][1] * u
            ps = max(.55, widths[j0] / wb * 2 * S * .012)
            bl.append(ell(bx, by, ps * 1.1, ps * .8, 10))
            for tx, ty in ((-1.05, -1.0), (-.38, -1.45), (.38, -1.45), (1.05, -1.0)):
                bl.append(ell(bx + tx * ps, by + ty * ps, ps * .38, ps * .42, 7))

    # blackberry creeping in from the prairie edge
    if mode == "full":
        bramble(cv, X + W * .02, bot - H * .02, S * .16, random.Random(seed + 9), 1)

    # mushrooms at the path edge after the rain
    ms = S * (.105 if mode == "full" else (.12 if mode == "band" else .1))
    if mode == "band":
        mxs = [(X + W * .5 - ms * 1.2, bot - H * .12, 1.15, 1, -.1), (X + W * .5 + ms * .95, bot - H * .14, .8, 0, .15),
               (X + W * .5 + ms * 1.9, bot - H * .1, .5, 0, .2)]
    else:
        bx = X + W * .7
        mxs = [(bx, bot - H * .11, 1., 1, -.08), (bx + ms * 1.35, bot - H * .09, .72, 0, .12),
               (bx - ms * 1.05, bot - H * .07, .5, 0, -.2), (bx + ms * 2.1, bot - H * .06, .4, 0, .25)]
    mxs.sort(key=lambda m: m[1])
    for mx_, my_, sc, kind, lean in mxs:
        mushroom(cv, mx_, my_, ms * sc, rng, kind, lean)
    cv.obj([], 0)
    for mx_, my_, sc, kind, lean in mxs:
        for d in (-1, 1):
            grass(cv, mx_ + d * ms * sc * .35, my_ + 1, ms * sc * .5, rng, 3)

    # kestrel hanging over the grass
    if mode == "full":
        kestrel(cv, X + W * .86, hy - H * .1, S * .035)

    # tundra swans coming in, a long skein
    if mode != "band":
        n = 5 if mode == "full" else 3
        lx, ly = X + W * .5, Y + (hy - Y) * .4
        sz = S * (.06 if mode == "full" else .075)
        birds = [(lx, ly, sz)]
        for k in range(1, n):
            sd = 1 if k % 2 else -1
            r = (k + 1) // 2
            birds.append((lx + r * sz * 2.6, ly + sd * r * sz * 1.0 + r * sz * .3, sz * (1 - .06 * r)))
        for i, (bx, by, bs) in enumerate(birds):
            swan_flying(cv, bx, by, bs, (i + seed) % 2 == 0, rng)
    else:
        sz = S * .07
        for i, (fx, fy) in enumerate([(.28, .25), (.43, .33), (.58, .22)]):
            swan_flying(cv, X + W * fx, Y + H * fy, sz, i % 2 == 0, rng)

    # the hazel bough hanging into the scene, with next year's catkins and the last leaves
    if mode != "band":
        bs = min(S * (.58 if mode == "full" else .42), H * .7)
        line = []
        for i in range(16):
            t = i / 15
            line.append((X - 6 + bs * t, Y + H * .02 + bs * .12 * math.sin(t * 2.6) + bs * .05 * t))
        wds = [bs * .035 * (1 - .7 * i / 15) + .8 for i in range(16)]
        br, _, _ = offset(line, wds)
        rr = random.Random(seed + 13)
        nodes = [5, 9, 13, 15]
        # catkins first so the bough laps over their stalks
        for k, j in enumerate(nodes):
            px, py = line[j]
            for c in range(2 if k < 3 else 1):
                catkin(cv, px + c * bs * .03 - bs * .01, py + wds[j], bs * rr.uniform(.2, .3) * (1 - .15 * c),
                       max(3.5, bs * .05), rr.uniform(-.15, .15), rr)
        cv.obj([br], 1.)
        cv.hair(along(line, wds, -.45))
        cv.hair(along(line, wds, -.75))
        for i in range(1, 15, 2):
            a, b = line[i], line[i + 1]
            cv.hair([(a[0], a[1] - wds[i] * .2), (b[0], b[1] + wds[i] * .3)])
        hazel_leaf(cv, line[11][0] + bs * .05, line[11][1] - bs * .02, bs * .2, -.5, rr, 1)
        # one leaf dropping through the sky
        if H > 150:
            hazel_leaf(cv, X + W * .3, Y + (hy - Y) * .72, bs * .15, 1.1, rr, -1)
    return cv.svg() + black(bl)


# ----------------------------------------------------------------------------------------------
# frames (adapted from engraving_codex layouts so every white field is filled)
# ----------------------------------------------------------------------------------------------

def _clip_d(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _tablet(tx, ty, tw, th, words, uid):
    """Letter the pedestal's sunk tablet and rule what the lettering leaves bare."""
    o = []
    size = min(th * .55, 9.)
    if size < 3.5:
        return C.dark_ground((tx + 2, ty + 2, tw - 3, th - 3), "L")
    k = size / 6.
    tw_ = text_width(words) * k
    x0 = tx + (tw - tw_) / 2
    yy = ty + (th - size) / 2 + .5
    o.append(strokes_svg(text_strokes(words, x0, yy, size), 1. if size >= 5 else .5))
    pad = size * .9
    for a, b in ((tx + 2.5, x0 - pad), (x0 + tw_ + pad, tx + tw - 1.5)):
        if b - a > 3:
            o.append(C.dark_ground((a, ty + 2.5, b - a, th - 4), "M"))
            # a small leaf flourish at the inner end of each ruled field
            cx = b + pad * .45 if a < x0 else a - pad * .45
            o.append(f'<path d="{_d(ell(cx, ty + th / 2, pad * .32, size * .22, 10), True, 0)}" fill="#000"/>')
    o.append(f'<path d="M{_n(tx + 2.5)},{_n(ty + th - 2)}h{_n(tw - 4)}" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def _title_words(ctx):
    t = (ctx or {}).get("title") or "WALK THE LAND"
    t = "".join(ch for ch in t.upper() if ch in GLYPH or ch == " ")
    return " ".join(t.split()) or "WALK THE LAND"


MONTHS = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER",
          "OCTOBER", "NOVEMBER", "DECEMBER"]


def _month(ctx):
    try:
        return MONTHS[int(((ctx or {}).get("date") or "")[5:7]) - 1]
    except Exception:
        return "NOVEMBER"


def layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("gb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 4.5, ry - 4.5
    o.append(_clip_d(C._uid("gbm", w, h, seed), _d(ell(cx, cy, fx, fy, 48), True, 0),
                     scene(cx - fx, cy - fy, 2 * fx, 2 * fy, seed, "band")))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return a, b


def layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.75)
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
    o.append(C._clip(C._uid("gm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, gh + 4)
    fa, fb = a - 5.5, b - 5.5
    o.append(_clip_d(C._uid("gmf", w, h, seed), _d(C._superellipse(cx, cy, fa, fb), True, .1),
                     scene(cx - fa, cy - fb, 2 * fa, 2 * fb, seed, "small")))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _catkins_on_volute(cv, vx, vy, r, side, seed):
    """Hazel catkins dropping from the underside of an upper volute: the frame bears the crop."""
    rng = random.Random(seed)
    x, y = vx + side * r * .55, vy + r * .62
    for k in range(3):
        catkin(cv, x + (k - 1) * r * .09, y + abs(k - 1) * r * .03, r * (.42 - .08 * abs(k - 1)), max(3., r * .11),
               (k - 1) * .25, rng)


def layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.dark_ground((0, 0, w, h), "L"))
    o.append(C.bead_moulding(0, 2, w, 1.5))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .7
    cx, cy = w / 2, py0 + ph * .47
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
    tops = []
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
        tops.append((vx, vy, side))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    cat = C.Canvas()
    for vx, vy, side in tops:
        _catkins_on_volute(cat, vx, vy, r2, side, seed + int(vx))
    cv.extend(cat)
    o.append(C._clip(C._uid("gt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, ch)
    fa, fb = a - 5.5, b - 5.5
    o.append(_clip_d(C._uid("gtf", w, h, seed), _d(C._superellipse(cx, cy, fa, fb), True, .1),
                     scene(cx - fa, cy - fb, 2 * fa, 2 * fb, seed, "full")))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = max(12., min(18., ph * .055))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .49, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(strokes_svg(text_on_curve(_title_words(ctx), centre, min(bh * .5, 8.)), 1.))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, "SAUVIE ISLAND  " + _month(ctx), C._uid("tb", w, h)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("gf", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 17
    if h < 110:
        body = layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx)
    else:
        body = layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
