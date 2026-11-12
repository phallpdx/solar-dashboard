"""Book plates for the Kindle Evening Edition: engraved page border, historiated initials,
headpiece and tailpiece, in the Kelmscott / Doves / Golden Cockerel manner, cut for a
Kindle Paperwhite at DPR 2 (0.5 CSS px = one device pixel).

API (each returns a complete <svg> string):
  border(width, height, seed, inner=(x, y, w, h))  page frame, band 14-22 px, wider corners
  initial(letter, size, seed)                       historiated roman drop-cap A-Z, 60-90 px
  headpiece(width, height, seed)                    acanthus band, ends dissolve into paper
  tailpiece(width, height, seed)                    small acanthus finial
  demo(path)                                        writes /tmp/claude-0/shots/plates/book.html

Leaves are acanthus: swell_line edges, interior modelled by contour hatching that follows the
leaf's own curl and thickens into the hollows. Standard library only.
"""
import math
import random

try:
    from solar.engraving_eink import swell_d, contour_hatch
except Exception:  # run as a script from inside solar/
    from engraving_eink import swell_d, contour_hatch

BK = "#000"


def _f(v):
    s = "%.1f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _sw(pts, ws):
    return swell_d(pts, ws, 1)


def _prof(n, w0, wm, w1):
    out = []
    for i in range(n):
        t = i / (n - 1.0)
        out.append(w0 + (w1 - w0) * t + (wm - (w0 + w1) / 2.0) * math.sin(math.pi * t))
    return out


def _stroke(pts, w0, wm, w1):
    return _sw(pts, _prof(len(pts), w0, wm, w1))


def _hair(pts, closed=False):
    d = "M" + " ".join("%s %s" % (_f(x), _f(y)) for x, y in pts)
    return d + ("z" if closed else "")


def _ellipse(cx, cy, rx, ry, n=24, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def _arc(cx, cy, rx, ry, a0, a1, n=None):
    n = n or max(6, int(abs(a1 - a0) / 6))
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _norm(pts):
    out = []
    for i in range(len(pts)):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(len(pts) - 1, i + 1)]
        L = math.hypot(x1 - x0, y1 - y0) or 1
        out.append((-(y1 - y0) / L, (x1 - x0) / L))
    return out


class _Ink:
    """Collects filled burin cuts, hairlines and white knock-outs."""

    def __init__(self):
        self.fill, self.hair, self.white, self.top = [], [], [], []

    def svg(self):
        o = []
        if self.white:
            o.append('<path d="%s" fill="#fff"/>' % "".join(self.white))
        if self.fill:
            o.append('<path d="%s"/>' % "".join(self.fill))
        if self.hair:
            o.append('<path d="%s" fill="none" stroke="#000" stroke-width=".5"/>' % "".join(self.hair))
        o.extend(self.top)
        return "".join(o)


# ---------------------------------------------------------------- the acanthus leaf

def _spiral(cx, cy, r0, a0, turns, sgn, shrink=0.78, n=40):
    return [(cx + r0 * (1 - shrink * t) * math.cos(a0 + sgn * t * turns * 2 * math.pi),
             cy + r0 * (1 - shrink * t) * math.sin(a0 + sgn * t * turns * 2 * math.pi))
            for t in (i / (n - 1.0) for i in range(n))]


def _leaf(ink, spine, wmax, side, lobes=4, pitch=1.5, dark=0.9):
    """An acanthus leaf laid along `spine` (list of points), bulging to `side` (+1/-1).
    Edges are swelling cuts; inside, contour lines parallel to the spine carry the shade,
    darkest along the curled-under hollow (the spine side) and toward the leaf's root."""
    n = len(spine)
    nr = _norm(spine)
    hs = []
    for i in range(n):
        t = i / (n - 1.0)
        h = wmax * math.sin(math.pi * min(1, t ** 0.75)) * (1 - 0.15 * t)
        h *= 1 + 0.22 * abs(math.sin(t * math.pi * lobes))  # serrated lobes
        hs.append(max(0.0, h))
    edge = [(x + nx * h * side, y + ny * h * side) for (x, y), (nx, ny), h in zip(spine, nr, hs)]
    ink.white.append(_hair(edge + spine[::-1] + [edge[0]], True))
    ink.fill.append(_sw(edge, _prof(n, 0.3, 1.5, 0.3)))
    ink.fill.append(_sw(spine, _prof(n, 0.5, 1.2, 0.4)))
    # lobe notches: short cuts from the edge toward the midrib, like acanthus fingers
    for k in range(1, lobes):
        i = int(n * (k - 0.0) / lobes)
        if 2 < i < n - 3 and hs[i] > 1.5:
            (x, y), (nx, ny) = spine[i], nr[i]
            a = (x + nx * hs[i] * side, y + ny * hs[i] * side)
            b = (x + nx * hs[i] * 0.45 * side, y + ny * hs[i] * 0.45 * side)
            ink.fill.append(_sw([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b], [1.0, 0.6, 0.1]))
    lines = []
    nl = max(2, int(wmax / pitch))
    for j in range(1, nl):
        s = j / float(nl)
        lines.append([(x + nx * h * s * side, y + ny * h * s * side)
                      for (x, y), (nx, ny), h in zip(spine, nr, hs)])
    L = float(n - 1)
    idx = {}
    for li, ln in enumerate(lines):
        for i, p in enumerate(ln):
            idx[(round(p[0], 2), round(p[1], 2))] = (li / max(1.0, len(lines) - 1.0), i / L)

    def tone(x, y):
        s, t = idx.get((round(x, 2), round(y, 2)), (0.5, 0.5))
        return dark * (1 - s) ** 1.4 * (1 - 0.55 * t) + 0.08

    ink.fill.append(contour_hatch(lines, tone, pitch, wmin=0.3, nd=1))


def _volute(ink, cx, cy, r, a0, sgn, w=1.6):
    sp = _spiral(cx, cy, r, a0, 1.15, sgn, 0.8, 44)
    ink.fill.append(_sw(sp, _prof(len(sp), 0.6, w, 0.4)))
    x, y = sp[-1]
    ink.fill.append(_sw(_ellipse(x, y, 0.6, 0.6, 8), [0.5] * 9))
    # inner shade of the volute eye: two hatched turns
    sp2 = _spiral(cx, cy, r * 0.62, a0 + 0.4 * sgn, 0.8, sgn, 0.6, 28)
    ink.fill.append(_sw(sp2, _prof(len(sp2), 0.2, 0.7, 0.2)))


def _scroll_unit(ink, ox, oy, P, B, flip, mapf, rng, side=1):
    """One bay of rinceau: a stem sweeping into a large acanthus leaf that rolls up into a
    volute. The leaf is white-backed (it stands in relief above the hatched ground), its edge a
    swelling cut, its body contour-hatched along the curl, darkest in the hollow by the midrib."""
    c = B / 2.0
    A = B * 0.26 * side
    n = 24
    stem = [mapf(ox + P * i / float(n), c + A * math.sin(math.pi * i / float(n))) for i in range(n + 1)]
    ink.white.append(_sw(stem, [3.5] * (n + 1)))
    ink.fill.append(_sw(stem, _prof(n + 1, 1.2, 1.8, 1.2)))
    r0 = B * 0.38
    cu, cv = ox + P * 0.56, c - side * B * 0.06
    a0 = math.pi * (0.5 + 0.55) if side > 0 else -math.pi * (0.5 + 0.55)
    sg = -1 if side > 0 else 1
    m = 44
    spine = [(cu + r0 * (1 - 0.72 * t) * math.cos(a0 + sg * t * 2.2 * math.pi),
              cv + r0 * (1 - 0.72 * t) * math.sin(a0 + sg * t * 2.2 * math.pi)) for t in (i / (m - 1.0) for i in range(m))]
    # leaf grows from the stem crest outward to the spiral
    root = (ox + P * 0.32, c + A * math.sin(math.pi * 0.32))
    spine = [((root[0] * (1 - k) + spine[0][0] * k), (root[1] * (1 - k) + spine[0][1] * k)) for k in (0.0, 0.25, 0.5, 0.75)] + spine
    gs = [mapf(u, v) for u, v in spine]
    _leaf(ink, gs, B * 0.24, sg if flip else -sg, lobes=6, pitch=1.5)
    x, y = gs[-1]
    ink.fill.append(_sw(_ellipse(x, y, 0.8, 0.8, 8), [0.7] * 9))
    # a secondary leaflet curling back from the root into the other half of the bay
    sp2 = [mapf(ox + P * (0.3 - 0.26 * t) + B * 0.12 * math.sin(math.pi * t ** 1.5) ,
                c + A * (0.85 - 1.2 * t) - side * B * 0.18 * t ** 3)
           for t in (i / 23.0 for i in range(24))]
    _leaf(ink, sp2, B * 0.14, side if not flip else -side, lobes=3, pitch=1.5, dark=0.75)
    return stem[-1]


# ---------------------------------------------------------------- Parker's motifs

def _drumsticks(ink, x, y, C, rng):
    m = C * 0.17
    j = rng.uniform(-1, 1)
    sticks = [((x + m, y + C - m), (x + C - m + j, y + m)), ((x + C - m, y + C - m), (x + m - j, y + m))]
    for k, (a, b) in enumerate(sticks):
        pts = [(a[0] + (b[0] - a[0]) * t / 12.0, a[1] + (b[1] - a[1]) * t / 12.0) for t in range(13)]
        ws = [2.2 - 1.4 * t / 12.0 for t in range(13)]
        if k == 1:  # passes over: white halo first
            ink.top.append('<path d="%s" fill="#fff"/>' % _sw(pts, [w + 2 for w in ws]))
            ink.top.append('<path d="%s"/>' % _sw(pts, ws))
            ink.top.append('<path d="%s" fill="#fff" stroke="#000" stroke-width=".5"/>'
                           % _hair(_ellipse(b[0], b[1], 1.3, 1.3, 10), True))
            # grip hatching on the butt
            for i in range(1, 4):
                p = pts[i]
                ink.top.append('<path d="M%s %sl1.2 -1.2" stroke="#fff" stroke-width=".5"/>' % (_f(p[0] - .6), _f(p[1] + .6)))
        else:
            ink.fill.append(_sw(pts, ws))
            ink.hair.append(_hair(_ellipse(b[0], b[1], 1.3, 1.3, 10), True))


def _note(ink, x, y):
    ink.white.append(_hair(_ellipse(x + 1.5, y - 3.5, 4.5, 6.5, 20), True))
    ink.fill.append(_sw(_ellipse(x, y, 1.7, 1.2, 12, -0.4), [1.6] * 13))
    ink.fill.append(_sw([(x + 1.4, y - 0.4), (x + 1.4, y - 8)], [0.75, 0.75]))
    fl = [(x + 1.4, y - 8), (x + 2.6, y - 6.2), (x + 4, y - 4.8), (x + 3.4, y - 2.8)]
    ink.fill.append(_sw(fl, [1.4, 1.2, 0.8, 0.2]))


def _paw(ink, x, y, s=1.0):
    ink.white.append(_hair(_ellipse(x, y, 5.5 * s, 5.5 * s, 20), True))
    pad = _ellipse(x, y + 1.6 * s, 2.8 * s, 2.2 * s, 20)
    ink.fill.append(_sw(pad, [0.9] * len(pad)))
    for k in range(-1, 2):
        ink.hair.append(_hair([(x - 1.6 * s, y + (1.6 + k) * s), (x + 1.6 * s, y + (1.6 + k) * s)]))
    for dx, dy in ((-2.9, -1.4), (-1.0, -3.0), (1.0, -3.0), (2.9, -1.4)):
        e = _ellipse(x + dx * s, y + dy * s, 0.9 * s, 1.2 * s, 10)
        ink.fill.append(_sw(e, [1.0] * len(e)))


def _cone(ink, x, y, s=1.0):
    ink.white.append(_hair(_ellipse(x, y - .5, 4 * s, 6.5 * s, 20), True))
    ink.fill.append(_sw([(x, y - 6 * s), (x + .3, y - 4.5 * s)], [0.7, 0.9]))
    out = _ellipse(x, y, 2.6 * s, 4.4 * s, 22)
    ink.fill.append(_sw(out, [0.6] * len(out)))
    for r in range(4):
        yy = y - 3 * s + r * 1.9 * s
        for k in (-1, 1):
            ink.fill.append(_sw([(x, yy), (x + k * 1.2 * s, yy + 0.9 * s), (x + k * 2.2 * s, yy + 0.4 * s)],
                                [0.2, 0.9, 0.2]))


def _kranok(ink, x, y, ang, size, flip=1):
    """Thai kranok flame: a hooked flame, outlined, with an inner tongue."""
    ca, sa = math.cos(ang), math.sin(ang)
    cen, hw = [], []
    for i in range(18):
        t = i / 17.0
        u = size * t
        v = flip * size * (0.55 * t ** 2.4 - 0.12 * math.sin(math.pi * t))
        cen.append((x + u * ca - v * sa, y + u * sa + v * ca))
        hw.append(size * 0.2 * math.sin(math.pi * t ** 0.55) * (1 - t) ** 0.25)
    nr = _norm(cen)
    for sgn in (1, -1):
        e = [(px + nx * h * sgn, py + ny * h * sgn) for (px, py), (nx, ny), h in zip(cen, nr, hw)]
        ink.fill.append(_sw(e, _prof(18, 0.4, 1.1, 0.2)))
    ink.fill.append(_sw(cen[2:13], _prof(11, 0.2, 1.0, 0.2)))


def _moon(ink, cx, cy, r, seed):
    ink.white.append(_hair(_ellipse(cx, cy, r + 2.5, r + 2.5, 24), True))
    ink.hair.append(_hair(_ellipse(cx, cy, r, r, 32), True))
    off = r * (0.55 + 0.1 * (seed % 3))
    y = cy - r + 0.75
    while y < cy + r:
        dy = y - cy
        hx = math.sqrt(max(0, r * r - dy * dy))
        lx = math.sqrt(max(0, r * r - dy * dy))  # lit disc of the same radius, shifted
        x0, x1 = cx - hx, min(cx + hx, cx + off - lx)
        if x1 - x0 > 0.6:
            w = 0.5 if abs(dy) > r * 0.6 else 1.0
            ink.fill.append(_sw([(x0 + .2, y), ((x0 + x1) / 2, y), (x1, y)], [w * .5, w, 0.2]))
        y += 1.5


# ---------------------------------------------------------------- border

def border(width, height, seed, inner=None):
    rng = random.Random(seed)
    W, H = float(width), float(height)
    if inner is None:
        inner = (46, 46, W - 92, H - 92)
    ix, iy, iw, ih = inner
    O = 3.0
    m = min(ix, iy, W - ix - iw, H - iy - ih) - O
    B = float(max(14, min(22, int((m - 4) / 1.6))))
    C = float(int(B * 1.6))
    ink = _Ink()
    oid = "bk%d" % seed
    # rules: outer 1px + hairline, inner jogged polygon around the corners
    X0, Y0, X1, Y1 = O, O, W - O, H - O
    ink.top.insert(0, '<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="#000"/>'
                   % (_f(X0 + .5), _f(Y0 + .5), _f(X1 - X0 - 1), _f(Y1 - Y0 - 1)))
    ink.hair.append(_hair([(X0 + 3.25, Y0 + 3.25), (X1 - 3.25, Y0 + 3.25), (X1 - 3.25, Y1 - 3.25),
                           (X0 + 3.25, Y1 - 3.25)], True))

    def inpoly(d):
        a, b, c = X0, Y0, None
        return [(a + C + d, b + B + d), (X1 - C - d, b + B + d), (X1 - C - d, b + C + d), (X1 - B - d, b + C + d),
                (X1 - B - d, Y1 - C - d), (X1 - C - d, Y1 - C - d), (X1 - C - d, Y1 - B - d), (a + C + d, Y1 - B - d),
                (a + C + d, Y1 - C - d), (a + B + d, Y1 - C - d), (a + B + d, b + C + d), (a + C + d, b + C + d)]

    ink.top.insert(0, '<path d="%s" fill="none" stroke="#000"/>' % _hair(inpoly(-0.5), True))
    ink.hair.append(_hair(inpoly(2.75), True))
    for (x, y, dx, dy) in ((X0 + C, Y0, 0, 1), (X1 - C, Y0, 0, 1), (X0 + C, Y1, 0, -1), (X1 - C, Y1, 0, -1),
                           (X0, Y0 + C, 1, 0), (X0, Y1 - C, 1, 0), (X1, Y0 + C, -1, 0), (X1, Y1 - C, -1, 0)):
        ink.hair.append(_hair([(x, y), (x + dx * B, y + dy * B)]))
    # sides: local (u along, v across from outer edge) -> page
    sides = {
        "top": (W - 2 * C - 2 * O, lambda u, v: (X0 + C + u, Y0 + v)),
        "right": (H - 2 * C - 2 * O, lambda u, v: (X1 - v, Y0 + C + u)),
        "bottom": (W - 2 * C - 2 * O, lambda u, v: (X1 - C - u, Y1 - v)),
        "left": (H - 2 * C - 2 * O, lambda u, v: (X0 + v, Y1 - C - u)),
    }
    ground = []
    for name, (L, mp) in sides.items():
        v = 5.25
        while v < B - 4:
            a, b = mp(0, v), mp(L, v)
            ground.append("M%s %sL%s %s" % (_f(a[0]), _f(a[1]), _f(b[0]), _f(b[1])))
            v += 2.0
    ink.top.insert(0, '<path d="%s" stroke="#000" stroke-width=".5"/>' % "".join(ground))
    P0 = B * 1.9 + rng.uniform(-1, 2)
    # one bay is cut once as a die and struck along every rail (keeps the plate small)
    die = _Ink()
    _scroll_unit(die, 0, 0, P0, B, False, lambda u, v: (u, v), rng, 1)
    dk = die.svg()
    dw = '<path d="%s" fill="#fff"/>' % "".join(die.white)
    dk = dk[len(dw):] if dk.startswith(dw) else dk
    uses_w, uses_k = [], []
    for name, (L, mp) in sides.items():
        gap = B * 0.9 if name in ("top", "bottom") else 0
        half = (L - 2 * gap) / 2.0 if gap else L
        segs = [(0, half, 1), (L - half, half, -1)] if gap else [(0, L, 1)]
        ox_, oy_ = mp(0, 0)
        eu = (mp(1, 0)[0] - ox_, mp(1, 0)[1] - oy_)
        ev = (mp(0, 1)[0] - ox_, mp(0, 1)[1] - oy_)
        for s0, sl, direction in segs:
            k = max(1, int(round((sl - 4) / P0)))
            P = (sl - 4) / k
            for i in range(k):
                u0 = s0 + 2 + i * P if direction > 0 else L - 2 - i * P
                sx = direction * P / P0
                fv = 1 if i % 2 == 0 else -1
                vb = 0 if fv > 0 else B
                m6 = (eu[0] * sx, eu[1] * sx, ev[0] * fv, ev[1] * fv,
                      ox_ + eu[0] * u0 + ev[0] * vb, oy_ + eu[1] * u0 + ev[1] * vb)
                tr = ' transform="matrix(%s)"' % " ".join("%.4g" % q for q in m6)
                uses_w.append('<use href="#%sw"%s/>' % (oid, tr))
                uses_k.append('<use href="#%sk"%s/>' % (oid, tr))
            # kranok flame where the stem meets the corner / centre medallion
            xa, ya = mp(s0 + 1 if direction > 0 else L - 1, B / 2.0)
        # ornaments in the vine
        if name == "top":
            cx, cy = mp(L / 2.0, B / 2.0)
            _moon(ink, cx, cy, B * 0.3, seed)
            for sg in (-1, 1):
                kx, ky = mp(L / 2.0 + sg * B * 0.85, B / 2.0)
                _kranok(ink, kx, ky, math.pi if sg > 0 else 0, B * 0.35, sg)
        elif name == "bottom":
            cx, cy = mp(L / 2.0, B / 2.0)
            _paw(ink, cx, cy - 0.5, B / 20.0)
            for sg in (-1, 1):
                kx, ky = mp(L / 2.0 + sg * B * 0.85, B / 2.0)
                _kranok(ink, kx, ky, 0 if sg > 0 else math.pi, B * 0.35, sg)
    # fir cones on the left, notes on the right, set at seed-chosen bays (drawn upright)
    Ls = H - 2 * C - 2 * O
    for f in (rng.uniform(.25, .38), rng.uniform(.62, .75)):
        y = Y0 + C + Ls * f
        _cone(ink, X0 + B * 0.5, y, B / 22.0)
    for f in (rng.uniform(.3, .45), rng.uniform(.55, .7)):
        y = Y0 + C + Ls * f
        _note(ink, X1 - B * 0.55, y)
    # corners: drumsticks crossing, kranok flicks
    pcorner = rng.randrange(4)
    for k, (x, y) in enumerate(((X0, Y0), (X1 - C, Y0), (X0, Y1 - C), (X1 - C, Y1 - C))):
        ink.hair.append(_hair([(x + 3, y + 3), (x + C - 3, y + 3), (x + C - 3, y + C - 3), (x + 3, y + C - 3)], True))
        if k == pcorner:
            ink.hair.append(_hair(_ellipse(x + C / 2.0, y + C / 2.0, C / 2.0 - 5, C / 2.0 - 5, 28), True))
            sp = _spiral(x + C / 2.0, y + C / 2.0, C / 2.0 - 7, math.pi * .75, 0.9, 1, 0.25, 24)
            ink.fill.append(_sw(sp, _prof(24, 0.3, 1.2, 0.3)))
            ink.top.append(_letter_ink("P", x + C / 2.0 - C * .23, y + C / 2.0 - C * .24, C * .46 / 100, 2))
        else:
            _drumsticks(ink, x, y, C, rng)
    defs = '<defs><g id="%sw">%s</g><g id="%sk">%s</g></defs>' % (oid, dw, oid, dk)
    # z-order: ground, rules, all knock-outs, all cuts, then the motifs above the scroll
    head = "".join(ink.top[:3])
    rest = _Ink()
    rest.white, rest.fill, rest.hair, rest.top = ink.white, ink.fill, ink.hair, ink.top[3:]
    body = ('<g id="%s">' % oid) + defs + head + "".join(uses_w) + "".join(uses_k) + rest.svg() + "</g>"
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">%s</svg>'
            % (_f(W), _f(H), _f(W), _f(H), body))


# ---------------------------------------------------------------- roman capitals

def _L(a, b, n=8):
    return [(a[0] + (b[0] - a[0]) * i / float(n), a[1] + (b[1] - a[1]) * i / float(n)) for i in range(n + 1)]


def _cat(*parts):
    out = []
    for p in parts:
        out.extend(p if not out else p[1:] if out[-1] == p[0] else p)
    return out


T_, t_, c_ = "T", "t", "c"
GLYPHS = {
    "A": [(t_, _L((20, 88), (50, 12))), (T_, _L((50, 12), (80, 88))), (t_, _L((33, 60), (67, 60)))],
    "B": [(T_, _L((25, 12), (25, 88))),
          (c_, _cat(_L((25, 12), (55, 12), 4), _arc(55, 30, 17, 18, -90, 90), _L((55, 48), (25, 48), 4))),
          (c_, _cat(_L((25, 48), (58, 48), 4), _arc(58, 68, 20, 20, -90, 90), _L((58, 88), (25, 88), 4)))],
    "C": [(c_, _arc(54, 50, 32, 38, -40, -320)), (t_, _L((79, 14), (79, 28), 3))],
    "D": [(T_, _L((25, 12), (25, 88))),
          (c_, _cat(_L((25, 12), (45, 12), 4), _arc(45, 50, 34, 38, -90, 90), _L((45, 88), (25, 88), 4)))],
    "E": [(T_, _L((25, 12), (25, 88))), (t_, _L((25, 12), (74, 12))), (t_, _L((25, 50), (64, 50))),
          (t_, _L((25, 88), (76, 88))), (t_, _L((74, 12), (74, 22), 3)), (t_, _L((76, 88), (76, 77), 3)),
          (t_, _L((64, 44), (64, 56), 3))],
    "F": [(T_, _L((25, 12), (25, 88))), (t_, _L((25, 12), (74, 12))), (t_, _L((25, 50), (64, 50))),
          (t_, _L((74, 12), (74, 22), 3)), (t_, _L((64, 44), (64, 56), 3))],
    "G": [(c_, _arc(52, 50, 32, 38, -40, -360)), (t_, _L((64, 54), (88, 54), 4)), (T_, _L((83, 54), (83, 84), 4))],
    "H": [(T_, _L((22, 12), (22, 88))), (T_, _L((78, 12), (78, 88))), (t_, _L((22, 50), (78, 50)))],
    "I": [(T_, _L((50, 12), (50, 88)))],
    "J": [(c_, _cat(_L((58, 12), (58, 68), 6), _arc(42, 68, 16, 19, 0, 160)))],
    "K": [(T_, _L((24, 12), (24, 88))), (t_, _L((76, 12), (26, 60))), (T_, _L((42, 44), (80, 88)))],
    "L": [(T_, _L((26, 12), (26, 88))), (t_, _L((26, 88), (76, 88))), (t_, _L((76, 88), (76, 77), 3))],
    "M": [(t_, _L((16, 88), (20, 12))), (T_, _L((20, 12), (50, 86))), (t_, _L((50, 86), (80, 12))),
          (T_, _L((80, 12), (84, 88)))],
    "N": [(t_, _L((22, 88), (22, 12))), (T_, _L((22, 12), (78, 88))), (t_, _L((78, 88), (78, 12)))],
    "O": [(c_, _arc(50, 50, 33, 38, 0, 360, 72))],
    "P": [(T_, _L((25, 12), (25, 88))),
          (c_, _cat(_L((25, 12), (56, 12), 4), _arc(56, 32, 21, 20, -90, 90), _L((56, 52), (25, 52), 4)))],
    "Q": [(c_, _arc(50, 48, 33, 36, 0, 360, 72)), (T_, _L((50, 78), (86, 97)))],
    "R": [(T_, _L((25, 12), (25, 88))),
          (c_, _cat(_L((25, 12), (56, 12), 4), _arc(56, 32, 21, 20, -90, 90), _L((56, 52), (25, 52), 4))),
          (T_, _L((46, 52), (80, 88)))],
    "S": [(c_, _cat(_arc(50, 31, 24, 19, -25, -270), _arc(50, 69, 26, 19, -90, 140))),
          (t_, _L((71, 14), (72, 26), 3)), (t_, _L((28, 86), (27, 74), 3))],
    "T": [(t_, _L((16, 12), (84, 12))), (T_, _L((50, 12), (50, 88))), (t_, _L((16, 12), (16, 23), 3)),
          (t_, _L((84, 12), (84, 23), 3))],
    "U": [(c_, _cat(_L((22, 12), (22, 60), 6), _arc(50, 60, 28, 28, 180, 0), _L((78, 60), (78, 12), 6)))],
    "V": [(T_, _L((18, 12), (50, 88))), (t_, _L((50, 88), (82, 12)))],
    "W": [(T_, _L((10, 12), (30, 88))), (t_, _L((30, 88), (50, 24))), (T_, _L((50, 24), (70, 88))),
          (t_, _L((70, 88), (90, 12)))],
    "X": [(T_, _L((20, 12), (80, 88))), (t_, _L((80, 12), (20, 88)))],
    "Y": [(T_, _L((18, 12), (50, 52))), (t_, _L((82, 12), (50, 52))), (T_, _L((50, 52), (50, 88)))],
    "Z": [(t_, _L((22, 12), (78, 12))), (T_, _L((78, 12), (22, 88))), (t_, _L((22, 88), (80, 88)))],
}


def _letter_ink(letter, ox, oy, s, halo):
    """Engraved roman capital: swelling cuts with stress, bracketed serifs, a white inline."""
    strokes = GLYPHS.get(letter.upper(), GLYPHS["O"])
    thick, thin = 11.0 * s, 3.4 * s
    black, white, inline = [], [], []
    ends = {}
    for kind, pts in strokes:
        for p in (pts[0], pts[-1]):
            ends[(round(p[0]), round(p[1]))] = ends.get((round(p[0]), round(p[1])), 0) + 1
    for kind, pts in strokes:
        P = [(ox + x * s, oy + y * s) for x, y in pts]
        ws = []
        for i in range(len(P)):
            a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            if kind == "T":
                w = thick
            elif kind == "t":
                w = thin
            else:
                w = thin + (thick - thin) * abs(math.sin(ang + 0.2)) ** 1.6
            ws.append(w)
        ws[0] *= 0.92
        ws[-1] *= 0.92
        black.append(_sw(P, ws))
        white.append(_sw(P, [w + halo for w in ws]))
        if kind == "T" or (kind == "c" and max(ws) > thick * 0.8):
            seg = [P[i] for i in range(len(P)) if ws[i] > thick * 0.75]
            if len(seg) > 2:
                inline.append(_hair(seg))
        # bracketed serifs on vertical / diagonal ends at cap line and baseline
        for idx, j in ((0, 1), (-1, -2)):
            x, y = pts[idx]
            if abs(y - 12) > 1 and abs(y - 88) > 1:
                continue
            if ends[(round(x), round(y))] > 1:
                continue
            dx, dy = pts[j][0] - x, pts[j][1] - y
            if abs(dy) < abs(dx):
                continue
            hl = (9 if kind == "T" else 6.5) * s
            X, Y = ox + x * s, oy + y * s
            sy = 1 if y < 50 else -1
            sp = [(X - hl, Y), (X - hl * .4, Y + sy * .3 * s), (X, Y + sy * 1.5 * s),
                  (X + hl * .4, Y + sy * .3 * s), (X + hl, Y)]
            sw = [0.4 * s, 2.6 * s, 6 * s, 2.6 * s, 0.4 * s]
            sp = [(px, py + sy * w / 2) for (px, py), w in zip(sp, sw)]
            black.append(_sw(sp, sw))
            white.append(_sw(sp, [w + halo for w in sw]))
    return ('<path d="%s" fill="#fff"/><path d="%s"/>'
            '<path d="%s" fill="none" stroke="#fff" stroke-width=".5"/>'
            % ("".join(white), "".join(black), "".join(inline)))


def _scene(kind, x0, y0, w, h, rng):
    ink = _Ink()
    if kind in ("river", "stars", "firs"):
        moon = (x0 + w * rng.uniform(.68, .82), y0 + h * .25, h * .1)
        stars = [(x0 + rng.uniform(4, w - 4), y0 + rng.uniform(3, h * .55)) for _ in range(9 if kind == "stars" else 5)]
        horizon = y0 + h * (0.62 if kind == "river" else 0.74)
        y = y0 + 1.0
        while y < horizon:
            segs = [(x0, x0 + w)]
            cuts = [(moon[0], moon[1], moon[2] + 1.5)] + [(sx, sy, 1.8) for sx, sy in stars]
            for cx, cy, r in cuts:
                if abs(y - cy) < r:
                    hx = math.sqrt(r * r - (y - cy) ** 2)
                    ns = []
                    for a, b in segs:
                        if b <= cx - hx or a >= cx + hx:
                            ns.append((a, b))
                        else:
                            if a < cx - hx:
                                ns.append((a, cx - hx))
                            if b > cx + hx:
                                ns.append((cx + hx, b))
                    segs = ns
            for a, b in segs:
                if b - a > 1:
                    ink.hair.append(_hair([(a, y), (b, y)]))
            y += 2.0
        for sx, sy in stars:
            ink.fill.append(_sw([(sx - 1.4, sy), (sx, sy), (sx + 1.4, sy)], [0, .6, 0]))
            ink.fill.append(_sw([(sx, sy - 1.4), (sx, sy), (sx, sy + 1.4)], [0, .6, 0]))
        ink.hair.append(_hair(_ellipse(moon[0], moon[1], moon[2], moon[2], 20), True))
        if kind == "river":
            y = horizon + 1.5
            k = 0
            while y < y0 + h - 1:
                pts = [(x0 + i * w / 30.0, y + 0.5 * math.sin(i * 0.9 + k)) for i in range(31)]
                ws = [0.5 + 0.6 * abs(math.sin(i * .35 + k)) * (1 - abs(i / 15.0 - 1) * .3) for i in range(31)]
                ink.fill.append(_sw(pts, ws))
                y += 2.0
                k += 1.7
            # St Johns Bridge: two gothic towers and the catenary, tiny, on the horizon
            bx, bw = x0 + w * .08, w * .55
            by = horizon
            ink.top.append('<path d="M%s %sL%s %s" stroke="#fff" stroke-width="3"/>' % (_f(bx - 2), _f(by - 1), _f(bx + bw + 2), _f(by - 1)))
            ink.top.append('<path d="M%s %sL%s %s" stroke="#000" stroke-width="1"/>' % (_f(bx - 2), _f(by - 1), _f(bx + bw + 2), _f(by - 1)))
            dd = []
            for tx in (bx + bw * .25, bx + bw * .75):
                dd.append("M%s %sL%s %sL%s %sL%s %s" % (_f(tx - 1.2), _f(by), _f(tx - 1), _f(by - 9), _f(tx + 1), _f(by - 9), _f(tx + 1.2), _f(by)))
            cab = [(bx + bw * i / 20.0, by - 8.5 + 7 * ((i / 20.0 * 2 - 1) ** 2 if i <= 10 else 0)) for i in range(21)]
            cab = [(bx + bw * i / 20.0, by - 1 - 7.5 * abs(math.cos(math.pi * (i / 20.0) * 2)) ** 1.0 if 5 <= i <= 15 else by - 1 - 7.5 * (i / 5.0 if i < 5 else (20 - i) / 5.0)) for i in range(21)]
            ink.top.append('<path d="%s" fill="none" stroke="#000" stroke-width=".5"/>' % ("".join(dd) + _hair(cab)))
            # heron standing in the shallows
            hx, hy = x0 + w * .86, y0 + h - 4
            ink.top.append('<path d="M%s %sl0 -4M%s %sl.6 -4M%s %sc-2 -1 -3 -3 -1.5 -4.5c1 -.8 .6 -2.2 -.3 -3l2.4 .4" fill="none" stroke="#000" stroke-width=".5"/>'
                           % (_f(hx), _f(hy), _f(hx + .8), _f(hy), _f(hx + 2.5), _f(hy - 4)))
            ink.top.append('<path d="%s"/>' % _sw([(hx - .5, hy - 4.5), (hx + 1.5, hy - 5), (hx + 3.5, hy - 4.2)], [.4, 2.2, .3]))
            # moon's reflection: a broken column of white
            ink.top.append('<rect x="%s" y="%s" width="2" height="%s" fill="#fff"/>'
                           % (_f(moon[0] - 1), _f(horizon + 2), _f(h * .2)))
        # firs on the horizon
        nf = 3 if kind == "river" else 5
        for i in range(nf):
            fx = x0 + w * (i + rng.uniform(.2, .8)) / nf
            fh = h * rng.uniform(.25, .4)
            base = horizon + (0 if kind == "river" else h * .12)
            ink.top.append('<path d="M%s %sL%s %sL%s %sz" fill="#fff"/>'
                           % (_f(fx), _f(base - fh), _f(fx - fh * .3), _f(base), _f(fx + fh * .3), _f(base)))
            yy = base - fh + 1.5
            while yy < base:
                t = (yy - base + fh) / fh
                hw = fh * .3 * t
                ink.top.append('<path d="M%s %sL%s %sL%s %s" fill="none" stroke="#000" stroke-width="%s"/>'
                               % (_f(fx - hw), _f(yy + 1), _f(fx), _f(yy), _f(fx + hw), _f(yy + 1),
                                  "1" if t > .5 else ".5"))
                yy += 1.5
        if kind == "firs":
            ink.hair.append(_hair([(x0, horizon + h * .12), (x0 + w, horizon + h * .12)]))
    else:  # vine scroll ground
        for i, (cx, cy, sg) in enumerate(((x0 + w * .22, y0 + h * .28, 1), (x0 + w * .78, y0 + h * .72, -1),
                                          (x0 + w * .78, y0 + h * .26, -1), (x0 + w * .22, y0 + h * .74, 1))):
            _volute(ink, cx, cy, h * .16, i * 1.3, sg, 1.2)
            spine = _spiral(cx, cy, h * .3, i * 1.3 + math.pi, 0.35, sg, 0.2, 14)
            _leaf(ink, spine, h * .08, sg, 3, 1.5, 0.7)
    return ink.svg()


def initial(letter, size, seed):
    rng = random.Random(seed * 31 + ord(letter.upper()[0]))
    S = float(size)
    kind = ("river", "firs", "stars", "vine")[seed % 4]
    oid = "bk%d%s" % (seed, letter.upper())
    o = ['<rect x=".5" y=".5" width="%s" height="%s" fill="#fff" stroke="#000"/>' % (_f(S - 1), _f(S - 1)),
         '<rect x="2.75" y="2.75" width="%s" height="%s" fill="none" stroke="#000" stroke-width=".5"/>'
         % (_f(S - 5.5), _f(S - 5.5))]
    o.append('<g clip-path="url(#%sc)">%s</g>' % (oid, _scene(kind, 4, 4, S - 8, S - 8, rng)))
    s = S * 0.7 / 100.0
    o.append(_letter_ink(letter, (S - 100 * s) / 2, (S - 100 * s) / 2 + s * 1, s, 2.5))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">'
            '<clipPath id="%sc"><rect x="3" y="3" width="%s" height="%s"/></clipPath><g id="%s">%s</g></svg>'
            % (_f(S), _f(S), _f(S), _f(S), oid, _f(S - 6), _f(S - 6), oid, "".join(o)))


# ---------------------------------------------------------------- head and tail pieces

def _band(ink, cx, cy, half, h, rng, units):
    """Symmetric acanthus rinceau from a centre ornament out to dissolving tendrils."""
    for sg in (-1, 1):
        P = half / (units + 0.6)
        for i in range(units):
            fade = 1 - 0.18 * i
            u0 = cx + sg * (h * 0.55 + i * P)

            def mp(u, v, u0=u0, sg=sg, hf=h * fade):
                return (u0 + sg * u, cy - hf / 2.0 + v)
            _scroll_unit(ink, 0, 0, P, h * fade, sg < 0, mp, rng, 1 if i % 2 == 0 else -1)
        # dissolving tendril: thinning cut, then a dotted trail into the paper
        ux = cx + sg * (h * 0.55 + units * P)
        pts = [(ux + sg * t * P * 0.6, cy + math.sin(t * 3) * h * 0.12) for t in [i / 10.0 for i in range(11)]]
        ink.fill.append(_sw(pts, [1.0 - 0.07 * i for i in range(11)]))
        x, y = pts[-1]
        for k in range(4):
            r = 0.6 - 0.12 * k
            ink.fill.append(_sw(_ellipse(x + sg * (2.5 + 2.5 * k), y + 0.5 * k, r, r, 8), [r] * 9))


def headpiece(width, height, seed):
    rng = random.Random(seed)
    W, H = float(width), float(height)
    ink = _Ink()
    cx, cy = W / 2.0, H / 2.0
    units = max(2, int((W / 2 - H * .6) / (H * 1.25)))
    _band(ink, cx, cy, W / 2 - H * .6 - 12, H * 0.62, rng, units)
    _moon(ink, cx, cy, H * 0.2, seed)
    for sg in (-1, 1):
        _kranok(ink, cx + sg * H * 0.62, cy, (0 if sg < 0 else math.pi), H * 0.3, sg)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s"><g id="bk%dh">%s</g></svg>'
            % (_f(W), _f(H), _f(W), _f(H), seed, ink.svg()))


def tailpiece(width, height, seed):
    rng = random.Random(seed + 7)
    W, H = float(width), float(height)
    ink = _Ink()
    cx, cy = W / 2.0, H * 0.45
    _band(ink, cx, cy, W / 2 - 18, H * 0.55, rng, 1)
    _cone(ink, cx, cy, H / 26.0)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s"><g id="bk%dt">%s</g></svg>'
            % (_f(W), _f(H), _f(W), _f(H), seed, ink.svg()))


# ---------------------------------------------------------------- demo

def demo(path="/tmp/claude-0/shots/plates/book.html", seed=3):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    b = border(570, 580, seed, inner=(46, 46, 478, 488))
    text = ("<p>The river ran high and dark under the Hawthorne bridge tonight, and the firs on the west hills "
            "held the last of the light. Tomorrow brings rain by nine, clearing after noon.</p>" * 6)
    caps = "".join('<figure>%s<figcaption>%s</figcaption></figure>' % (initial(L, 76, seed + i), L)
                   for i, L in enumerate("DTWPC"))
    html = """<!doctype html><html><head><meta charset="utf-8"><title>Book plates</title>
<style>body{margin:0;padding:10px;background:#fff;color:#000;font:15px/1.45 Georgia,serif;width:580px}
.page{position:relative;width:570px;height:580px}.page>svg{position:absolute;left:0;top:0}
.txt{position:absolute;left:58px;top:56px;width:454px;height:470px;overflow:hidden;text-align:justify}
.txt svg{float:left;margin:3px 8px 0 0}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}figure{margin:0;text-align:center;font-size:11px}
.c{text-align:center;margin:8px 0}</style></head><body>
<div class="page">%s<div class="txt">%s%s</div></div>
<div class="row">%s</div>
<div class="c">%s</div><div class="c">%s</div></body></html>""" % (
        b, initial("T", 64, seed), text, caps, headpiece(528, 44, seed), tailpiece(160, 40, seed))
    with open(path, "w") as fh:
        fh.write(html)
    return path, len(b)


if __name__ == "__main__":
    print(demo())
