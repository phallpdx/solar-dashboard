"""family-02 "Places to go together": holiday outings around Portland, winter 2026.

The vignette is a winter night under the St. Johns Bridge (Cathedral Park): the Gothic towers
and the cathedral arches of the approach, a Christmas Ship strung with lights on the Willamette,
a lit tree with a star (the tree lightings), and a sandhill crane from Sauvie Island on the
frozen shore. Moon phase and stars follow ctx["date"]. In the tall plate two sandhill cranes rise
out of the acanthus like the Codex's bearded faces, the pedestal tablet carries the Christmas
Ships parade, and the ribbon is hung with a string of lights.
Easter egg: a tiny ZooLights elephant (Parker's Thai elephant) on the shore by the tree.
"""
import sys
import math
import random
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
PI, TAU = math.pi, 2 * math.pi


# ------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------

def _hlines(x0, x1, y0, y1, pitch, w, rng=None, gap=0.):
    """Horizontal lines on the device grid between y0..y1 (w .5 -> centres k*.5+.25, w 1 -> k*.5).
    rng+gap: break each line into dashes (water)."""
    off = .25 if w < 1 else 0.
    y = math.ceil((y0 - off) / pitch) * pitch + off
    out = []
    while y <= y1:
        if rng is None:
            out.append([(x0, y), (x1, y)])
        else:
            x = x0 - rng.uniform(0, 20)
            while x < x1:
                L = rng.uniform(6, 34)
                out.append([(x, y), (x + L, y)])
                x += L + rng.uniform(1.5, gap)
        y += pitch
    return out


def _circle(cx, cy, r, n=10):
    return _ell(cx, cy, r, r, n)[:-1]


def _star(cx, cy, r, ri, n=4, rot=-PI / 2):
    return [(cx + (r if i % 2 == 0 else ri) * math.cos(rot + PI * i / n),
             cy + (r if i % 2 == 0 else ri) * math.sin(rot + PI * i / n)) for i in range(2 * n)]


def _lancet(cx, yb, w, h):
    """A pointed (Gothic) arch opening: base yb, width w, total height h."""
    r = w * .85
    yt = yb - h + w * .75
    pts = [(cx - w / 2, yb), (cx - w / 2, yt)]
    # left arc centred at (cx - w/2 + r, yt) from 180deg up to the apex
    ax = math.acos(max(-1, min(1, (w / 2 - r) / -r)))
    for i in range(1, 7):
        a = PI + (ax - PI) * 0 + (PI - (PI - ax)) * 0
    # simpler: build apex by quadratic-ish points
    apex = (cx, yb - h)
    for i in range(1, 6):
        t = i / 6
        x = cx - w / 2 + (w / 2) * t
        y = yt - (yt - apex[1]) * math.sin(t * PI / 2) ** .8
        pts.append((x, y))
    pts.append(apex)
    for (x, y) in reversed(pts[2:-1]):
        pts.append((2 * cx - x, y))
    pts += [(cx + w / 2, yt), (cx + w / 2, yb)]
    return pts


class Layer:
    """A Canvas plus black fills painted after it."""

    def __init__(self):
        self.cv = C.Canvas()
        self.black = []

    def ink(self, poly):
        self.black.append(_d(poly, True, .1))

    def svg(self):
        s = self.cv.svg()
        if self.black:
            s += f'<path d="{"".join(self.black)}" fill="#000" stroke="none"/>'
        return s


def _moon_phase(date):
    try:
        y, m, d = (int(v) for v in date[:10].split("-"))
    except Exception:
        y, m, d = 2026, 11, 11
    import datetime
    days = (datetime.date(y, m, d) - datetime.date(2000, 1, 6)).days - .26
    return (days / 29.530588) % 1.


# ------------------------------------------------------------------------------------------
# the subjects
# ------------------------------------------------------------------------------------------

def _sky(L, X, Y, W, H, yh, rng, phase, moon=True):
    cv = L.cv
    cv.obj([[(X, Y), (X + W, Y), (X + W, yh), (X, yh)]], 0)
    band1 = Y + (yh - Y) * .42
    band2 = Y + (yh - Y) * .8
    cv.line(_hlines(X, X + W, Y - 1, band1, 2., 1.))      # deep night, 50 %
    cv.hair(_hlines(X, X + W, band1, band2, 1.5, .5))     # 33 %
    cv.hair(_hlines(X, X + W, band2, yh + 1, 2., .5))     # city glow at the horizon, 25 %
    m = None
    if moon:
        r = max(5., min(W, H) * .065)
        mx, my = X + W * .62, Y + H * .13 + r * .4
        m = (mx, my, r)
        cv.obj([_circle(mx, my, r + 2.5, 30)], 0)          # halo
        cv.obj([_circle(mx, my, r, 30)], 1.)
        k = math.cos(TAU * phase)
        wax = phase < .5
        s = -1 if wax else 1
        dark = [(mx + s * r * math.sin(PI * i / 24), my - r * math.cos(PI * i / 24)) for i in range(25)]
        dark += [(mx - s * r * k * math.sin(PI * i / 24), my + r * math.cos(PI * i / 24)) for i in range(25)]
        cv.hair(C.hatch_poly(_circle(mx, my, r - 1, 30), 0, 3., 1.25))
        cv.line(C.hatch_poly(dark, 0, 1.5, 0.))
        for (cx, cy, rr) in ((.3, -.25, .18), (-.2, .3, .13), (.1, .45, .1)):
            cv.hair(_ell(mx + cx * r, my + cy * r, rr * r, rr * r * .8, 10))
    # stars
    for i in range(int(W * (yh - Y) / 900) + 3):
        sx, sy = X + rng.uniform(.03, .97) * W, Y + rng.uniform(.03, .7) * (yh - Y)
        if m and math.hypot(sx - m[0], sy - m[1]) < m[2] + 8:
            continue
        big = rng.random() < .3
        rr = rng.uniform(3.5, 5.5) if big else rng.uniform(1.6, 2.6)
        cv.obj([_star(sx, sy, rr, rr * .22, 4, rng.uniform(-.2, .2) - PI / 2)], 0)


def _tower(L, cx, yt, yb, hw, yd, H):
    cv = L.cv
    ht = hw * .78
    poly = [(cx - hw, yb), (cx - ht, yt), (cx - ht * .95, yt - ht * 1.5), (cx - ht * .6, yt - ht * .2),
            (cx - ht * .25, yt - ht * .2), (cx, yt - ht * 3.2), (cx + ht * .25, yt - ht * .2),
            (cx + ht * .6, yt - ht * .2), (cx + ht * .95, yt - ht * 1.5), (cx + ht, yt), (cx + hw, yb)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 90, 3., .25))
    right = [(cx + .5, yb), (cx + .5, yt - ht * 3)] + poly[6:]
    cv.hair(C.hatch_poly(right, 90, 3., 1.75))
    edge = [(cx + hw * .55, yb), (cx + ht * .55, yt), (cx + ht, yt), (cx + hw, yb)]
    cv.hair(C.hatch_poly(edge, 90, 1.5, 1.))
    # tiers
    for f in (.0, .3, .58):
        y = yt + (yd - yt) * f
        k = (y - yt) / max(1, yb - yt)
        w2 = ht + (hw - ht) * k
        cv.line([(cx - w2, y), (cx + w2, y)])
    # Gothic openings between the legs, stacked; black
    h_all = yd - yt
    for f0, f1 in ((.04, .28), (.34, .56), (.62, .96)):
        y0, y1 = yt + h_all * f0, yt + h_all * f1
        k = (y1 - yt) / max(1, yb - yt)
        ow = (ht + (hw - ht) * k) * .62
        L.ink(_lancet(cx, y1, ow, y1 - y0))
    # under the deck, a tall pier arch
    ow = hw * .7
    L.ink(_lancet(cx, yb - 1, ow, (yb - yd) * .75))
    # pinnacle finials
    for s in (-1, 1):
        cv.hair([(cx + s * ht * .95, yt - ht * 1.5), (cx + s * ht * .95, yt - ht * 1.9)])
    cv.hair([(cx, yt - ht * 3.2), (cx, yt - ht * 3.8)])


def _bridge(L, X, Y, W, H, yd, yw, rng):
    cv = L.cv
    t1, t2 = X + W * .3, X + W * .7
    yt = Y + H * .17
    hw = max(4.5, W * .036)
    dh = max(3., H * .028)
    yb = yw + 3
    # main cable and side spans (behind the towers' tops, in front of the sky)
    sag = yd - H * .045
    cab = []
    for i in range(41):
        t = i / 40
        x = t1 + (t2 - t1) * t
        cab.append((x, yt + 3 + (sag - yt - 3) * (1 - (2 * t - 1) ** 2)))
    sides = []
    for s, tx in ((-1, t1), (1, t2)):
        pts = []
        for i in range(21):
            t = i / 20
            x = tx + s * (tx - X + 6 if s < 0 else X + W - tx + 6) * t
            pts.append((x, yt + 3 + (yd - 3 - yt - 3) * (t ** 1.6)))
        sides.append(pts)
    cv.obj([], 0)
    # suspenders
    x = t1 + 3
    while x < t2 - 2:
        t = (x - t1) / (t2 - t1)
        cv.hair([(x, yt + 3 + (sag - yt - 3) * (1 - (2 * t - 1) ** 2)), (x, yd)])
        x += 3.
    for pts in sides:
        for i in range(1, 20, 2):
            px, py = pts[i]
            cv.hair([(px, py), (px, yd)])
    cv.heavy(cab)
    for pts in sides:
        cv.heavy(pts)
    # Cathedral Park arches under the east approach (left)
    ax0, ax1 = X - 2, t1 - hw - 1
    if ax1 - ax0 > 20:
        ap = [(ax0, yd + dh), (ax1, yd + dh), (ax1, yw + 2), (ax0, yw + 2)]
        cv.obj([ap], 1.)
        cv.hair(C.hatch_poly(ap, 90, 3., .25))
        n = max(2, int((ax1 - ax0) / 15))
        step = (ax1 - ax0) / n
        for i in range(n):
            cx = ax0 + step * (i + .5)
            L.ink(_lancet(cx, yw + 2, step * .62, (yw - yd - dh) * .8))
    for tx in (t1, t2):
        _tower(L, tx, yt, yb, hw, yd, H)
    # deck truss
    deck = [(X - 2, yd), (X + W + 2, yd), (X + W + 2, yd + dh), (X - 2, yd + dh)]
    cv.obj([deck], 1.)
    cv.hair(C.hatch_poly(deck, 90, 1.5, .25))
    cv.hair([(X - 2, yd - 1.5), (X + W + 2, yd - 1.5)])
    # little deck lamps
    x = X + 4
    while x < X + W:
        cv.obj([_circle(x, yd - 2.2, .9, 6)], .5)
        x += 9
    return t1, t2, hw


def _water(L, X, Y, W, H, yw, rng, towers):
    cv = L.cv
    wp = [(X - 2, yw), (X + W + 2, yw), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([wp], 0)
    cv.hair(_hlines(X - 2, X + W + 2, yw + .5, Y + H + 2, 2., .5, rng, 5))
    # tower reflections: denser broken strokes
    for tx, hw in towers:
        for y in [l[0][1] for l in _hlines(tx, tx, yw + 1.5, yw + H * .16, 2., 1.)]:
            ww = hw * (1 - (y - yw) / (H * .2))
            x = tx - ww + rng.uniform(-1, 1)
            while x < tx + ww:
                Ld = rng.uniform(2, 5)
                cv.line([(x, y + 1), (min(tx + ww, x + Ld), y + 1)])
                x += Ld + rng.uniform(1.5, 3)


def _ship(L, cx, wy, Ls, rng):
    """A Christmas Ship: a cruiser with a mast strung with lights in a tree shape."""
    cv = L.cv
    hh = Ls * .11
    hull = [(cx - Ls * .5, wy - hh), (cx + Ls * .42, wy - hh), (cx + Ls * .5, wy - hh * 1.5),
            (cx + Ls * .42, wy + hh * .2), (cx - Ls * .44, wy + hh * .2)]
    cab = [(cx - Ls * .3, wy - hh), (cx - Ls * .3, wy - hh * 2.2), (cx + Ls * .05, wy - hh * 2.2),
           (cx + Ls * .15, wy - hh)]
    top = cab[2][1]
    mast_t = wy - Ls * .62
    lights = []
    # light strings mast-top to bow and stern, and a lit tree shape on the mast
    for (ex, ey) in ((cx - Ls * .5, wy - hh), (cx + Ls * .5, wy - hh * 1.5)):
        n = int(math.hypot(ex - cx, ey - mast_t) / 4.2)
        for i in range(1, n):
            t = i / n
            lights.append((cx + (ex - cx) * t, mast_t + (ey - mast_t) * t + math.sin(t * PI) * 2.5))
    cv.obj([], 0)
    cv.line([(cx - Ls * .02, top), (cx - Ls * .02, mast_t)])
    for (ex, ey) in ((cx - Ls * .5, wy - hh), (cx + Ls * .5, wy - hh * 1.5)):
        cv.hair([(cx + (ex - cx) * t, mast_t + (ey - mast_t) * t + math.sin(t * PI) * 2.5)
                 for t in [i / 12 for i in range(13)]])
    cv.obj([cab], 1.)
    cv.hair(C.hatch_poly(cab, 0, 3., .25))
    for i in range(4):
        wx = cx - Ls * .26 + i * Ls * .075
        cv.obj([[(wx, wy - hh * 1.95), (wx + Ls * .045, wy - hh * 1.95), (wx + Ls * .045, wy - hh * 1.4),
                 (wx, wy - hh * 1.4)]], .5)
    cv.obj([hull], 1.)
    cv.line(C.hatch_poly(hull, 0, 1.5, 0.))
    cv.obj([[(cx - Ls * .44, wy - hh * .55), (cx + Ls * .45, wy - hh * .55),
             (cx + Ls * .45, wy - hh * .3), (cx - Ls * .44, wy - hh * .3)]], 0)    # white boot stripe
    # tree of lights on the cabin roof
    tb = top - 1
    th = (top - mast_t) * .55
    for row in range(5):
        y = tb - th * row / 5
        hwid = Ls * .13 * (1 - row / 5)
        k = max(1, int(hwid * 2 / 4))
        for j in range(k + 1):
            lights.append((cx - Ls * .02 - hwid + 2 * hwid * j / k, y - 1))
    for (lx, ly) in lights:
        cv.obj([_circle(lx, ly, 1.15, 7)], .5)
    cv.obj([_star(cx - Ls * .02, mast_t - 2, 4, 1.4, 5)], .5)
    # reflections of the lights: short bright breaks under the ship
    cv.obj([], 0)
    for (lx, ly) in lights[::3]:
        y = wy + hh * .8 + rng.uniform(0, hh * 2)
        cv.hair([(lx - 1.5, y), (lx + 1.5, y)])


def _shore(L, X, Y, W, H, ys, rng):
    cv = L.cv
    pts = [(X - 2, ys + 2)]
    for i in range(1, 30):
        x = X + W * i / 30
        pts.append((x, ys + math.sin(i * .9) * 1.5 + math.sin(i * 2.3) * 1.))
    pts += [(X + W + 2, ys), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([pts], 1.)
    cv.line(_hlines(X - 2, X + W + 2, ys + 2, Y + H + 2, 2., 1.))
    # snow crust highlight under the edge
    cv.obj([[(p[0], p[1] + .5) for p in pts[:31]] + [(p[0], p[1] + 2.5) for p in pts[30::-1]]], 0)
    # reeds
    for i in range(int(W / 7)):
        x = X + rng.uniform(0, W)
        y = ys + 1
        hgt = rng.uniform(4, 10)
        lean = rng.uniform(-2.5, 2.5)
        cv.hair([(x, y), (x + lean * .5, y - hgt * .6), (x + lean, y - hgt)])


def _tree(L, tx, ytop, ybase, wb, rng, egg=None):
    cv = L.cv
    n = 5
    span = ybase - ytop
    tiers = []
    for i in range(n):
        y0 = ytop + span * (i / n) * .92
        y1 = ytop + span * ((i + 1.15) / n) * .92
        hw = wb * (.28 + .72 * (i + 1) / n) / 2
        tiers.append((y0, y1, hw))
    # trunk
    trunk = [(tx - wb * .06, ybase - span * .1), (tx + wb * .06, ybase - span * .1),
             (tx + wb * .07, ybase), (tx - wb * .07, ybase)]
    cv.obj([trunk], 1.)
    cv.line(C.hatch_poly(trunk, 90, 1.5, 0.))
    for i in range(n - 1, -1, -1):
        y0, y1, hw = tiers[i]
        pts = [(tx, y0)]
        for j in range(1, 7):
            t = j / 6
            pts.append((tx + hw * t, y0 + (y1 - y0) * t ** 1.2 * .9))
        k = max(3, int(hw * 2 / 5))
        for j in range(k + 1):
            t = 1 - j / k
            pts.append((tx - hw + 2 * hw * t, y1 + (1.8 if j % 2 else -.5)))
        for j in range(5, 0, -1):
            t = j / 6
            pts.append((tx - hw * t, y0 + (y1 - y0) * t ** 1.2 * .9))
        cv.obj([pts], 1.)
        cv.hair(C.hatch_poly(pts, 62, 2., .25))
        rgt = [(tx, y0), (tx + hw * 1.1, y1 + 2), (tx + hw * .1, y1 + 2)]
        cv.hair(C.hatch_poly([p for p in pts if p[0] >= tx - .1] + [(tx, y1 + 2)], -62, 2., 1.))
        hem = [(tx - hw, y1 - 3.5), (tx + hw, y1 - 3.5), (tx + hw, y1 + 2), (tx - hw, y1 + 2)]
        cv.hair([[a, b] for a, b in C.hatch_poly(hem, 90, 1.5, .25)
                 if _inside(pts, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)])
        # garland of lights
        gy = y0 + (y1 - y0) * .62
        gw = hw * .78
        m = max(3, int(gw * 2 / 4.5))
        gl = [(tx - gw + 2 * gw * j / m, gy + math.sin(PI * j / m) * 3 - (j / m) * 2.5) for j in range(m + 1)]
        cv.obj([], 0)
        cv.hair(gl)
        for (gx, gyy) in gl[1:-1]:
            cv.obj([_circle(gx, gyy + 1.4, 1.2, 7)], .5)
    # star on top with rays
    r = max(4., wb * .13)
    sy = ytop - r * .3
    cv.obj([_circle(tx, sy, r * 2.1, 20)], 0)
    for i in range(24):
        a = TAU * i / 24 + .1
        r1 = r * (2.4 if i % 2 == 0 else 1.7)
        cv.hair([(tx + r * 1.15 * math.cos(a), sy + r * 1.15 * math.sin(a)),
                 (tx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    sp = _star(tx, sy, r, r * .42, 5)
    cv.obj([sp], 1.)
    cv.hair([[(tx, sy), p] for p in sp[1::2]])
    cv.hair(C.hatch_poly([(tx, sy)] + sp[0:4], 90, 1.5, .25))


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            c = not c
    return c


def _elephant(L, x, yb, e, face=1):
    """The Easter egg: a ZooLights elephant, trunk up, e px tall, standing at (x, yb)."""
    cv = L.cv
    P = [(0.05, .55), (0, .35), (.08, .15), (.3, .05), (.6, .07), (.75, .0), (.92, .06), (1.0, .25),
         (1.08, .12), (1.12, -.04), (1.2, -.06), (1.16, .04), (1.12, .22), (1.04, .42), (.94, .5),
         (.9, .62), (.9, 1), (.79, 1), (.77, .72), (.32, .72), (.31, 1), (.2, 1), (.18, .7), (.08, .62)]
    pts = [(x + face * (px - .6) * e, yb - (1 - py) * e) for px, py in P]
    cv.obj([pts], .5)
    cv.hair([(x + face * (.62 - .6) * e, yb - .92 * e), (x + face * (.55 - .6) * e, yb - .62 * e),
             (x + face * (.72 - .6) * e, yb - .5 * e)])
    cv.hair([(x + face * (.0 - .6) * e, yb - .62 * e), (x + face * (-.1 - .6) * e, yb - .4 * e)])
    cv.obj([_circle(x + face * (.86 - .6) * e, yb - .8 * e, .5, 5)], .5)
    # a crown of three bulbs over its back (it is lit)
    for t in (.2, .4, .6):
        cv.obj([_circle(x + face * (t - .6) * e, yb - 1.06 * e, .9, 6)], .5)


def _ribbon(spine, w0, w1):
    """A tapering band along a spine: polygon (left edge out, right edge back)."""
    n = len(spine)
    L, R = [], []
    for i, (x, y) in enumerate(spine):
        a = spine[max(0, i - 1)]
        b = spine[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        wd = (w0 + (w1 - w0) * i / (n - 1)) / 2
        L.append((x + nx * wd, y + ny * wd))
        R.append((x - nx * wd, y - ny * wd))
    return L, R


def _bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def _crane_head(L, cv, hx, hy, s, f, eye=True):
    """Sandhill crane head at (hx, hy) (its centre), size s = head length; f=+1 faces right."""
    head = [(hx + f * dx * s, hy + dy * s) for dx, dy in
            ((-.5, .1), (-.42, -.25), (-.1, -.42), (.25, -.38), (.5, -.15), (.52, .1), (.3, .3),
             (0, .38), (-.35, .32))]
    beak = [(hx + f * .45 * s, hy - .18 * s), (hx + f * 1.55 * s, hy + .08 * s),
            (hx + f * .45 * s, hy + .18 * s)]
    cv.obj([beak], 1.)
    cv.hair([(hx + f * .5 * s, hy), (hx + f * 1.35 * s, hy + .07 * s)])
    cv.hair(C.hatch_poly([(hx + f * .5 * s, hy + .02 * s), (hx + f * 1.5 * s, hy + .09 * s),
                          (hx + f * .5 * s, hy + .17 * s)], 0, 1.5, .25))
    cv.obj([head], 1.)
    # red crown: dark cross-hatch over the forehead
    crown = [(hx + f * dx * s, hy + dy * s) for dx, dy in
             ((-.05, -.4), (.25, -.37), (.5, -.15), (.4, -.02), (.12, -.08))]
    cv.line(C.hatch_poly(crown, 45, 1.5, 0))
    cv.hair(C.hatch_poly(crown, -45, 1.5, .75))
    # grey nape, white cheek left clean but lined lightly
    nape = [(hx + f * dx * s, hy + dy * s) for dx, dy in ((-.5, .1), (-.42, -.25), (-.15, -.3), (-.2, .35), (-.35, .32))]
    cv.hair(C.hatch_poly(nape, 70 * f, 1.5, .25))
    cv.hair(C.hatch_poly(head, 0, 3., 1.25))
    if eye:
        ex, ey = hx + f * .3 * s, hy - .1 * s
        cv.obj([_circle(ex, ey, max(1.2, s * .09), 8)], .5)
        L.ink(_circle(ex, ey, max(.6, s * .05), 6))


def _crane(L, cx, yf, s, face=1):
    """A sandhill crane standing on the shore, s px tall, facing left when face=-1."""
    cv = L.cv
    f = face

    def P(px, py):
        return (cx + f * px * s, yf - py * s)
    cv.obj([], 0)
    for lx, kx, bend in ((-.02, -.035, 0), (.05, .07, 1)):
        cv.line([P(lx, .45), P(kx, .23), P(lx + .005 * bend, 0)])
        cv.hair([P(lx, 0), P(lx + .08, -.005)])
        cv.hair([P(lx, 0), P(lx - .05, .003)])
    body = [P(.22, .62), P(.14, .7), P(0, .72), P(-.14, .69), P(-.25, .6), P(-.27, .52),
            P(-.18, .46), P(-.02, .42), P(.12, .44), P(.2, .5)]
    spine = _bez(P(.17, .64), P(.24, .74), P(.14, .84), P(.2, .95), 14)
    Lr, Rr = _ribbon(spine, s * .07, s * .035)
    neck = Lr + Rr[::-1]
    bustle = [P(-.08, .7), P(-.2, .7), P(-.31, .63), P(-.36, .5), P(-.33, .43), P(-.3, .5),
              P(-.28, .41), P(-.25, .49), P(-.22, .42), P(-.19, .51), P(-.15, .47), P(-.12, .55)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly(body, -15 * f, 2., .25))
    low = [P(.2, .5), P(-.27, .52), P(-.18, .46), P(-.02, .42), P(.12, .44)]
    cv.hair(C.hatch_poly(low, 45, 3., .25))
    for row in range(3):
        y = .64 - row * .05
        cv.hair([P(.1 - row * .03 - k * .05, y - .018 * math.sin(k * 1.4 + 1)) for k in range(5)])
    cv.obj([neck], 1.)
    cv.hair(C.hatch_poly(neck, 15, 2., .25))
    cv.obj([bustle], 1.)
    cv.hair(C.hatch_poly(bustle, 70 * f, 1.5, .25))
    for k in range(4):
        cv.hair([P(-.12 - k * .05, .66 - k * .01), P(-.2 - k * .04, .5 + k * .01)])
    hx, hy = P(.215, .965)
    _crane_head(L, cv, hx, hy, s * .09, f)


def scene(X, Y, W, H, ctx, mode):
    """The whole vignette inside the box X, Y, W, H (clipped by the caller)."""
    date = (ctx or {}).get("date", "2026-11-11")
    rng = random.Random(date + str(mode) + str(int(W)))
    phase = _moon_phase(date)
    out = []
    if mode == "small":
        L = Layer()
        ys = Y + H * .8
        _sky(L, X, Y, W, H, ys, rng, phase, moon=W > 90)
        out.append(L.svg())
        L2 = Layer()
        _shore(L2, X, Y, W, H, ys, rng)
        _tree(L2, X + W * .5, Y + H * .18, ys + 2, min(W * .45, H * .5), rng)
        out.append(L2.svg())
        return "".join(out)
    yd = Y + H * .55
    yw = Y + H * .7
    L = Layer()
    _sky(L, X, Y, W, H, yw, rng, phase)
    out.append(L.svg())
    L = Layer()
    _water(L, X, Y, W, H, yw, rng, [(X + W * .3, max(4.5, W * .036)), (X + W * .7, max(4.5, W * .036))])
    _bridge(L, X, Y, W, H, yd, yw, rng)
    out.append(L.svg())
    L = Layer()
    _ship(L, X + W * .52, yw + H * .1, W * .3, rng)
    ys = Y + H * .87
    _shore(L, X, Y, W, H, ys, rng)
    _tree(L, X + W * .17, Y + H * .3, ys + 4, W * .27, rng)
    _elephant(L, X + W * .36, ys + 3, max(6., H * .05), 1)
    if mode == "full" and H > 150:
        _crane(L, X + W * .81, ys + 6, H * .5, -1)
    out.append(L.svg())
    return "".join(out)


def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _boxpath(x, y, w, h):
    return f"M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z"


# ------------------------------------------------------------------------------------------
# carved crane heads growing from the scrolls (the Codex's bearded faces)
# ------------------------------------------------------------------------------------------

def _crane_bust(L, cv, cx, cy, s, face):
    """A crane's neck rising in an S out of the acanthus with its head in relief, s px tall;
    face=+1 looks right. Draws into cv (blacks into L)."""
    f = face

    def P(px, py):
        return (cx + f * px * s, cy - py * s)
    spine = _bez(P(0, 0), P(-.22, .32), P(.24, .5), P(.06, .82), 30)
    w0, w1 = s * .15, s * .095
    Lr, Rr = _ribbon(spine, w0, w1)
    neck = Lr + Rr[::-1]
    cv.obj([neck], 1.)
    # contour lines along the neck (smooth grey plumage), packed into the shade side
    for fr, wt in ((.82, 1.), (.66, .5), (.5, .5), (.34, .5), (.18, .5), (.0, .5), (-.3, .5), (-.62, .5)):
        a, b = _ribbon(spine, w0 * fr, w1 * fr)
        line = (a if f > 0 else b)
        (cv.line if wt == 1. else cv.hair)(line[1:])
    # throat highlight and a dark cast shadow where the neck turns
    sh = [Rr[i] if f > 0 else Lr[i] for i in range(8, 20)]
    cv.hair([(x + 1.5 * f, y) for x, y in sh])
    hx, hy = spine[-1][0] + f * s * .05, spine[-1][1] - s * .035
    _crane_head(L, cv, hx, hy, s * .2, f)


# ------------------------------------------------------------------------------------------
# layouts (house frame, with the field engraved edge to edge)
# ------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.1, 170)
    o.append(C._clip(C._uid("fb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 3.6, ry - 3.6
    d = _d(_ell(cx, cy, fx, fy, 64), True, 0)
    o.append(_field_clip(C._uid("fbv", w, h, seed), d, scene(cx - fx, cy - fy, 2 * fx, 2 * fy, ctx,
                                                            "mid" if gh > 70 else "small")))
    o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _cart_field(o, cx, cy, cw, ch, seed, ctx, mode, uid):
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, seed)
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    fd = _d(C._superellipse(cx, cy, a - 5, b - 5), True, .1)
    o.append(_field_clip(uid, fd, scene(cx - a + 5, cy - b + 5, 2 * a - 10, 2 * b - 10, ctx, mode)))
    o.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')


def _layout_medium(w, h, seed, ctx):
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
    o.append(C._clip(C._uid("fm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    mode = "full" if gh > 150 else ("mid" if gh > 95 else "small")
    _cart_field(o, cx, cy, cw, gh + 4, rng.randrange(1 << 20), ctx, mode, C._uid("fmv", w, h, seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _ships_tablet(x, y, w, h, seed):
    """The pedestal tablet: the Christmas Ships parade on the night river."""
    rng = random.Random(seed)
    L = Layer()
    cv = L.cv
    box = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([box], 0)
    wl = y + h * .66
    cv.line(_hlines(x, x + w, y, wl, 2., 1.))
    cv.hair(_hlines(x, x + w, wl + 1, y + h, 2., .5, rng, 4))
    n = 5
    for i in range(n):
        bx = x + w * (i + .5) / n + rng.uniform(-4, 4)
        Ls = min(w / n * .7, h * 1.7)
        hh = Ls * .12
        hull = [(bx - Ls * .5, wl - hh), (bx + Ls * .42, wl - hh), (bx + Ls * .5, wl - hh * 1.6),
                (bx + Ls * .42, wl + hh * .3), (bx - Ls * .44, wl + hh * .3)]
        cab = [(bx - Ls * .3, wl - hh), (bx - Ls * .3, wl - hh * 2.3), (bx + Ls * .05, wl - hh * 2.3),
               (bx + Ls * .15, wl - hh)]
        mt = max(y + 2.5, wl - Ls * .62)
        cv.obj([cab + hull[:0]], .5)
        cv.obj([hull], 1.)
        cv.hair(C.hatch_poly(hull, 0, 1.5, .25))
        cv.obj([], 0)
        cv.line([(bx, wl - hh * 2.3), (bx, mt)])
        for (ex, ey) in ((bx - Ls * .5, wl - hh), (bx + Ls * .5, wl - hh * 1.6)):
            m = max(2, int(math.hypot(ex - bx, ey - mt) / 3.6))
            for j in range(1, m):
                t = j / m
                cv.obj([_circle(bx + (ex - bx) * t, mt + (ey - mt) * t, .95, 6)], .5)
        cv.obj([_star(bx, mt - 1, 2.6, 1., 4)], .5)
    s = L.svg()
    s += f'<path d="{_boxpath(x, y, w, h)}" fill="none" stroke="#000" stroke-width="1"/>'
    return s


def _banner_lights(centre, bh, seed):
    """Fill the ribbon face: a light rule ground and a swag of holiday lights."""
    rng = random.Random(seed)
    n = len(centre) - 1
    top = [(px, py - bh * .5 + 1.6) for px, py in centre[2:-2]]
    bot = [(px, py + bh * .5 - 1.6) for px, py in centre[2:-2]][::-1]
    face = top + bot
    o = [f'<path d="{_d(face, True, 0)}" fill="{C.pat("L")}" stroke="none"/>']
    wire = []
    bulbs = []
    k = 0
    pts = centre[2:-2]
    seg = 4
    for i in range(0, len(pts) - seg, seg):
        a, b = pts[i], pts[i + seg]
        for j in range(seg + 1):
            t = j / seg
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t - bh * .28 + math.sin(PI * t) * bh * .32
            wire.append((x, y))
        for t in (.25, .5, .75):
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t - bh * .28 + math.sin(PI * t) * bh * .32
            bulbs.append((x, y + 1.6))
    o.append(f'<path d="{_d(wire, tol=.1)}" stroke="#000" stroke-width=".5"/>')
    bd = "".join(_d(_ell(x, y, 1.1, 1.6, 8)[:-1], True, 0) for x, y in bulbs)
    o.append(f'<path d="{bd}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    hd = "".join(f"M{_n(x - .8)},{_n(y - 1.6)}h1.6" for x, y in bulbs)
    o.append(f'<path d="{hd}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_tall(w, h, seed, ctx, density=.85):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = 9.
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    o.append(C.dark_ground((0, py0 - 2, w, h - py0 + 2), "G"))
    cw, ch = pw * .5, ph * .66
    cx, cy = w / 2, py0 + ph * .44
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    BL = Layer()
    busts = BL.cv
    r1 = min(pw * .17, ph * .23)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    # the two cranes rise from the outer acanthus, facing the cartouche
    bs = min(ph * .42, 150)
    for side in (-1, 1):
        bx = cx + side * (cw * .5 + (w / 2 - cw * .5) * .62)
        by = py0 + ph * .74
        _crane_bust(BL, busts, bx, by, bs, -side)
        C.acanthus_frond(bx - side * bs * .05, by + bs * .04, -90 - side * 38, bs * .32, n=3, spread=34,
                         seed=seed + side, cv=busts)
        C.acanthus_frond(bx + side * bs * .04, by + bs * .06, -90 + side * 30, bs * .26, n=2, spread=26,
                         seed=seed + 3 * side, cv=busts)
        occ.append(("c", bx, by - bs * .45, bs * .32))
        occ.append(("c", bx, by - bs * .1, bs * .25))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    cv.extend(busts)
    o.append(C._clip(C._uid("ft", w, h, seed), 0, py0, w, ph, cv.svg() +
                     (f'<path d="{"".join(BL.black)}" fill="#000" stroke="none"/>' if BL.black else "")))
    _cart_field(o, cx, cy, cw, ch, rng.randrange(1 << 20), ctx, "full", C._uid("ftv", w, h, seed))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_lights(centre, bh, seed))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_ships_tablet(tx + 2, ty + 2, tw - 3, th - 3, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("ff", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
