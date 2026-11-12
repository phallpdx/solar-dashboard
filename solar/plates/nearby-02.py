"""Moon watch (nearby-02): tonight's moon over the Columbia, engraved at king tier.
The medallion holds a copperplate night: the moon at today's phase (from ctx["date"]) with
earthshine, strata of cloud drifting past in flowing burin lines, Mt. Hood on the horizon, the
river laying the moon's broken glitter path, and on the Sauvie Island bank Parker's dog howling
beside a heron. Fine scroll on a punched matte surrounds it; Easter egg: the dog's head carved in
the eye of the lowest scroll. Tall plates add the coming phases on the pedestal tablet and the
dedication cartouche (arms placeholder) under the scene."""
# ==============================================================================================
# STUDIO: the king-tier engraving kit shared by this batch of plates (embedded verbatim in each
# plate so every plate stays self-contained). Built on the house Canvas (engraving_codex).
#   fine scroll    a branching tree of small logarithmic volutes grown from one stem, every
#                  volute carrying veined, lobed acanthus leaves (Ken Hunt panels, the GRS vise)
#   matte ground   cut-away background punched to a dark matte (white 1 px punch-dots in black)
#   gold lines     double / triple border lines and bead rows that follow each panel's shape
#   medallion      the subject inlaid in a beaded oval, scroll all round it (the Colt cylinder)
#   lettering      engraved Roman capitals with thick-thin stress and serifs, as filled paths
# ==============================================================================================
import math
import random
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_n = C._n
_d = C._d
_Rib = C._Rib
_euler = C._euler
_sm = C._smooth
_fill = C._fill_lines
_shadow = C._shadow
_CR = C._CR
Canvas = C.Canvas


def ell(cx, cy, rx, ry, n=48, a0=0., a1=TAU):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def poly_d(polys):
    return "".join(_d(p, True, 0) for p in polys if len(p) > 2)


def lines_d(pls, tol=.2):
    return "".join(_d(p, False, tol) for p in pls if len(p) > 1)


def clip_g(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def rect_d(x, y, w, h):
    return f"M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z"


def mirror_g(w, body, gid=None):
    if gid:
        return (f'<g id="{gid}">{body}</g><use href="#{gid}" xlink:href="#{gid}" '
                f'transform="matrix(-1 0 0 1 {_n(w)} 0)"/>')
    return f'<g transform="matrix(-1 0 0 1 {_n(w)} 0)">{body}</g>'


def inside(poly, x, y):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            c = not c
        j = i
    return c


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        m = 1 - t
        out.append((m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
                    m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def rrect(x, y, w, h, r, n=6):
    """A rounded rectangle as a point list."""
    r = min(r, w / 2, h / 2)
    pts = []
    for cx, cy, a in ((x + w - r, y + r, -PI / 2), (x + w - r, y + h - r, 0), (x + r, y + h - r, PI / 2),
                      (x + r, y + r, PI)):
        for i in range(n + 1):
            t = a + PI / 2 * i / n
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def offset_poly(poly, d):
    """Offset a closed convex-ish polygon by d (positive = outward for a counter-clockwise screen poly)."""
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sg = 1 if area > 0 else -1
    out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        t1 = (b[0] - a[0], b[1] - a[1])
        t2 = (c[0] - b[0], c[1] - b[1])
        l1 = math.hypot(*t1) or 1
        l2 = math.hypot(*t2) or 1
        n1 = (t1[1] / l1, -t1[0] / l1)
        n2 = (t2[1] / l2, -t2[0] / l2)
        nx, ny = n1[0] + n2[0], n1[1] + n2[1]
        nl = math.hypot(nx, ny) or 1
        cosh = max(.35, (n1[0] * nx + n1[1] * ny) / nl)
        out.append((b[0] - sg * d * nx / nl / cosh, b[1] - sg * d * ny / nl / cosh))
    return out


# ----------------------------------------------------------------------------------------------
# the matte ground: cut-away black punched with white dots (a 12 px tile of irregular punches,
# whole device pixels so every punch prints crisp; the scroll covers the repeat)
# ----------------------------------------------------------------------------------------------

def matte_defs(pid):
    rng = random.Random(4242)
    T = 12
    cells = []
    for j in range(8):
        for i in range(8):
            if rng.random() < .3:
                x = i * 1.5
                y = j * 1.5
                cells.append(f"M{_n(x)},{_n(y)}h1v1h-1z" if rng.random() < .8 else f"M{_n(x)},{_n(y)}h1.5v.5h-1.5z")
    tile = (f'<path d="M0,0h{T}v{T}h-{T}z" fill="#000"/>'
            f'<path d="{"".join(cells)}" fill="#fff"/>')
    rng2 = random.Random(77)
    cells2 = []
    for j in range(8):
        for i in range(8):
            if rng2.random() < .16:
                cells2.append(f"M{_n(i * 1.5)},{_n(j * 1.5)}h1v1h-1z")
    tile2 = (f'<path d="M0,0h{T}v{T}h-{T}z" fill="#000"/>'
             f'<path d="{"".join(cells2)}" fill="#fff"/>')
    return (f'<defs><pattern id="{pid}m" width="{T}" height="{T}" patternUnits="userSpaceOnUse">{tile}</pattern>'
            f'<pattern id="{pid}k" width="{T}" height="{T}" patternUnits="userSpaceOnUse">{tile2}</pattern></defs>')


def matte(d, pid, deep=False):
    return f'<path d="{d}" fill="url(#{pid}{"k" if deep else "m"})" stroke="none"/>'


# ----------------------------------------------------------------------------------------------
# the acanthus leaf: lobed blade on a curved midrib; bulino along the form on the shadow side,
# a bright cut edge on the lit side, lobes veined, clefts drilled, the tip rolled over
# ----------------------------------------------------------------------------------------------

LEAF_MAX = 30.
_GN = sum(_sm(.6, 1., (i + .5) / 50) ** 2 for i in range(50)) / 50


def _lobe_f(u, k, ph, a, b, depth):
    if k <= 0 or u <= a or u >= b:
        return 1.
    v = ((u - a) / (b - a) * k + ph) % 1.
    g = math.sin(PI * min(1., v * 1.06)) ** .32          # a rounded scallop with a narrow cleft
    fade = _sm(a, a + .04, u) * (1 - _sm(b - .04, b, u))
    return 1 - (1 - (depth + (1 - depth) * g)) * fade


def mid_lines(R, side, pitch=1.5, frac=.7, u0=.03, u1=.95, d0=None):
    """Bulino at absolute spacing: lines `pitch` px apart running parallel to the midrib on one
    side, each stopping where it would come within (1 - frac) of the edge."""
    out = []
    step = 1.2 / R.L
    d = d0 if d0 is not None else pitch * .8
    while True:
        segs, cur, anyw = [], [], False
        u = u0
        while u <= u1:
            w = R.width(u, side)
            if w * frac > d:
                cur.append(R.at(u, side * d / w))
                anyw = True
            else:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            u += step
        if len(cur) > 1:
            segs.append(cur)
        if not anyw:
            break
        out += segs
        d += pitch
    return out


def leaf(cv, x, y, ang, L, W, bend=.6, curl=3., k_out=3, k_in=1, seed=0, dark=1.):
    """An acanthus leaf from (x, y) heading ang (radians), L long, W wide. bend: radians the midrib
    turns; curl: radians rolled in at the tip (sign gives the sense)."""
    rng = random.Random(seed)
    n = max(14, int(L / 1.1))
    c = 1 if bend + curl >= 0 else -1

    def kf(u):
        return (bend + curl * _sm(.6, 1., u) ** 2 / _GN) / L

    pts = _euler(x, y, ang, L, kf, n)
    ph_o, ph_i = rng.uniform(0, .25), rng.uniform(.3, .6)
    a_o, b_o = .12, .86
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        e = W * (u ** .5 * (1 - u) ** .7) / .42 * (1 - .3 * _sm(.72, 1, u)) + .4
        wo.append(e * _lobe_f(u, k_out, ph_o, a_o, b_o, .55))
        wi.append(e * .7 * _lobe_f(u, k_in, ph_i, .2, .8, .6) + .3)
    R = _Rib(pts, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5 if W < 9 else 1.)
    # shadow side (inside of the curve): fine parallel cuts along the form, a black turned-under rim
    cv.hair(mid_lines(R, c, 1.5, .94, .03, .99))
    if W >= 4.5:
        _shadow(cv, R, c, min(2.2, W * .2) * dark, .12, .8)
    # lit side: bulino beside the midrib fading out toward a bright cut edge
    cv.hair(mid_lines(R, -c, 2., .6, .05, .9, 1.))
    lu = (b_o - a_o) / max(1, k_out)
    for j in range(-1, k_out + 2):
        un = a_o + (j - ph_o) * lu
        if un < a_o - .02 or un > b_o - .03:
            continue
        pk = min(b_o, un + lu * .7)
        if R.width(min(pk, .99), -c) < 2.2:
            continue
        cv.hair([R.at(un + (pk - un) * t * .9 + lu * .1 * (1 - t), -c * (.16 + .66 * t ** .8))
                 for t in (0, .35, .7, 1.)])
        if un > a_o + .01 and W >= 5:
            cv.hair([R.at(un, -c * .9), R.at(un + lu * .06, -c * .5)])
    return R


# ----------------------------------------------------------------------------------------------
# the volute and the scroll tree
# ----------------------------------------------------------------------------------------------

class Scroll:
    __slots__ = ("cx", "cy", "r", "sg", "pts", "tail", "depth", "kids", "eye", "leafy", "W")

    def __init__(self, cx, cy, r, sg, pts, tail, depth, eye=None):
        self.cx, self.cy, self.r, self.sg, self.pts, self.tail, self.depth = cx, cy, r, sg, pts, tail, depth
        self.kids = 0
        self.eye = eye
        self.leafy = True
        self.W = None


def spiral(cx, cy, r, phi0, sg, turns=1.6, end=.1, n=None):
    th = TAU * turns
    b = math.log(1 / end) / th
    n = n or max(24, int(r * th * .45))
    return [(cx + r * math.exp(-b * th * i / n) * math.cos(phi0 + sg * th * i / n),
             cy + r * math.exp(-b * th * i / n) * math.sin(phi0 + sg * th * i / n)) for i in range(n + 1)]


def _tang(pts, k):
    a, b = pts[max(0, k - 1)], pts[min(len(pts) - 1, k + 1)]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    return (b[0] - a[0]) / L, (b[1] - a[1]) / L


class Tree:
    """Grows a scroll tree inside a region. ok(x, y) says whether a point may hold scroll.
    Volutes are held as circles (with clearance) in a coarse grid for fast collision tests."""

    def __init__(self, ok, seed=0, rmin=6., gap=.9, turns=1.6):
        self.ok = ok
        self.rng = random.Random(seed)
        self.rmin = rmin
        self.gap = gap
        self.turns = turns
        self.sc = []
        self.blocks = []          # extra circles (cx, cy, r) to keep clear

    def free(self, x, y, r):
        for (bx, by, br) in self.blocks:
            if math.hypot(x - bx, y - by) < br + r * .8:
                return False
        for s in self.sc:
            if math.hypot(x - s.cx, y - s.cy) < (s.r + r) * self.gap:
                return False
        for i in range(8):
            a = TAU * i / 8
            if not self.ok(x + r * .55 * math.cos(a), y + r * .55 * math.sin(a)):
                return False
        return self.ok(x, y)

    def root(self, cx, cy, r, sg, phi0, tail_from=None, eye=None, turns=None):
        """A first volute; tail_from=(x, y, tx, ty): the stem comes in from there with that heading."""
        pts = spiral(cx, cy, r, phi0, sg, turns or self.turns, .5 if eye else .1)
        tail = []
        if tail_from:
            x0, y0, tx, ty = tail_from
            tl = math.hypot(tx, ty) or 1
            tx, ty = tx / tl, ty / tl
            dx, dy = _tang(pts, 0)
            D = math.hypot(pts[0][0] - x0, pts[0][1] - y0)
            tail = bezier((x0, y0), (x0 + tx * D * .4, y0 + ty * D * .4),
                          (pts[0][0] - dx * D * .4, pts[0][1] - dy * D * .4), pts[0], max(6, int(D / 3)))[:-1]
        s = Scroll(cx, cy, r, sg, tail + pts, len(tail), 0, eye)
        self.sc.append(s)
        return s

    def branch(self, p, kmax=3, shrink=(1., .86, .72, .6, .48), spots=(.04, .14, .24, .34, .44, .54)):
        """Children off p's outer run (spots in turns from the spiral's start, plus the lead-in
        stem): the stem leaves p tangentially and winds the other way."""
        made = []
        rng = self.rng
        n = len(p.pts) - p.tail
        turns = self.turns
        ks = [p.tail + int(f / turns * n) for f in spots]
        if p.tail > 6:
            ks += [int(p.tail * .45), int(p.tail * .8)]
        rng.shuffle(ks)
        for k in ks:
            if len(made) >= kmax:
                break
            if k < 2 or k > len(p.pts) - 3:
                continue
            qx, qy = p.pts[k]
            tx, ty = _tang(p.pts, k)
            ox, oy = qx - p.cx, qy - p.cy
            ol = math.hypot(ox, oy) or 1
            ox, oy = ox / ol, oy / ol
            for sh in shrink:
                rc = p.r * sh * rng.uniform(.9, 1.06)
                if rc < self.rmin:
                    continue
                # heading: the parent's tangent turned outward
                a = math.atan2(ty, tx)
                ao = math.atan2(oy, ox)
                da = (ao - a + PI) % TAU - PI
                hd = a + da * rng.uniform(.3, .5)
                hx, hy = math.cos(hd), math.sin(hd)
                tl = rc * rng.uniform(.5, .9)
                psx, psy = qx + hx * tl, qy + hy * tl
                best = None
                for sgn in (1, -1):
                    nx, ny = -hy * sgn, hx * sgn
                    ccx, ccy = psx + nx * rc, psy + ny * rc
                    dpar = math.hypot(ccx - p.cx, ccy - p.cy)
                    if best is None or dpar > best[0]:
                        best = (dpar, ccx, ccy)
                _, ccx, ccy = best
                if not self.free(ccx, ccy, rc):
                    continue
                phi0 = math.atan2(psy - ccy, psx - ccx)
                # winding sense that continues the heading
                sg = 1 if (-math.sin(phi0) * hx + math.cos(phi0) * hy) > 0 else -1
                pts = spiral(ccx, ccy, rc, phi0, sg, self.turns * rng.uniform(.92, 1.06), .1)
                dx, dy = _tang(pts, 0)
                D = math.hypot(pts[0][0] - qx, pts[0][1] - qy)
                tail = bezier((qx, qy), (qx + tx * D * .45, qy + ty * D * .45),
                              (pts[0][0] - dx * D * .45, pts[0][1] - dy * D * .45), pts[0], max(5, int(D / 3)))[:-1]
                s = Scroll(ccx, ccy, rc, sg, tail + pts, len(tail), p.depth + 1)
                self.sc.append(s)
                made.append(s)
                break
        return made

    def grow(self, roots, kmax=3, gens=12):
        q = list(roots)
        g = 0
        while q and g < 400:
            p = q.pop(0)
            q.extend(self.branch(p, kmax))
            g += 1
        return self.sc

    def sprigs(self, step=7., rmin=None):
        """Fill leftover gaps: small volutes branching from the nearest scroll."""
        rmin = rmin or self.rmin
        for s in list(self.sc):
            if s.r < rmin * 1.6:
                continue
            self.branch(s, 2, shrink=(.5, .4, .32), spots=(.1, .3, .5, .62, .72))


def draw_scroll(cv, s, rng, leaf_k=1., dark=1.):
    """Paint one volute: a slender round-carved stem, slender acanthus blades sweeping along its
    back (each curving with the spiral, tip turned out), a blade rolling into the curl, and the
    drilled eye (or the figure carved in it)."""
    pts = s.pts
    n = len(pts)
    S = [0.]
    for k in range(1, n):
        S.append(S[-1] + math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]))
    tot = S[-1] or 1
    W0 = s.W or max(1., s.r * .11)
    ws = [W0 * (1 - .65 * (S[k] / tot) ** 1.2) + .3 for k in range(n)]
    R = _Rib(pts, ws, ws)
    k = s.tail + (n - s.tail) // 3
    px, py = pts[k]
    tx, ty = _tang(pts, k)
    c = 1 if (-ty) * (s.cx - px) + tx * (s.cy - py) > 0 else -1
    cv.obj([R.outline()], .5 if W0 < 2 else 1.)
    if W0 >= 1.5:
        cv.hair(R.contour(.4 * c, 0., 1., minw=1.6))
    if W0 >= 2.2:
        _shadow(cv, R, c, W0 * .5 * dark, 0., 1.)
    r = s.r
    # blades along the back: from the lead-in to about three quarters of a turn
    ksp = n - s.tail
    k_end = s.tail + int(ksp * min(.5, .78 / 1.6))
    spots = []
    kk = 2 if s.tail > 4 else s.tail + 1
    while kk < k_end and len(spots) < 6:
        base = pts[kk]
        rad = max(r * .35, math.hypot(base[0] - s.cx, base[1] - s.cy))
        ll = min(r * 1.9, max(r * .8, rad * 1.7), LEAF_MAX) * leaf_k * rng.uniform(.9, 1.05)
        spots.append((kk, rad, ll))
        step = ll * (.85 if kk < s.tail else .72)
        while kk < n - 1 and S[kk] < S[spots[-1][0]] + step:
            kk += 1
    for kk, rad, ll in spots[::-1]:
        tx, ty = _tang(pts, kk)
        base = R.at(kk / (n - 1), -c * .5)
        ang = math.atan2(ty, tx) - c * rng.uniform(.08, .2)
        lw = ll * rng.uniform(.3, .36)
        leaf(cv, base[0], base[1], ang, ll, lw, c * min(2.4, ll / (rad + lw * .5)), -c * rng.uniform(.5, .9),
             3 if ll > 18 else 2, 1, rng.randrange(1 << 20), dark)
    # a blade curling into the eye
    if not s.eye and r > 6:
        kk = s.tail + int(ksp * .36)
        tx, ty = _tang(pts, kk)
        base = R.at(kk / (n - 1), c * .6)
        ll = r * .85 * leaf_k
        leaf(cv, base[0], base[1], math.atan2(ty, tx) + c * .2, ll, ll * .3, c * 1.6, c * 2.6, 2, 0,
             rng.randrange(1 << 20), 1.2)
    ex, ey = pts[-1]
    if s.eye:
        er = s.r * .5
        cv.obj([ell(s.cx, s.cy, er, er, 28)[:-1]], 1.)
        q = er - .5
        while q > .4:
            cv.line(ell(s.cx, s.cy, q, q, max(10, int(q * 5))))
            q -= .9
        cv.obj([], 0)
        s.eye(cv, s.cx, s.cy, er * .92)
    else:
        rr = max(.9, ws[-1] * .7)
        cv.obj([ell(ex, ey, rr + .8, rr + .8, 12)[:-1]], 0)
        q = rr - .25
        while q > .25:
            cv.line(ell(ex, ey, q, q, max(8, int(q * 6))))
            q -= .75
        cv.line([(ex - .3, ey), (ex + .3, ey)])


def paint_tree(cv, scrolls, seed=0, leaf_k=1.):
    rng = random.Random(seed)
    for s in sorted(scrolls, key=lambda s: (-s.depth, s.r)):
        draw_scroll(cv, s, random.Random(rng.randrange(1 << 30)), leaf_k)


def scroll_field(ok, roots, seed=0, rmin=6., kmax=3, leaf_k=1., sprigs=True, gap=.9, blocks=()):
    """Grow and paint a scroll tree. roots: list of dicts for Tree.root. Returns a Canvas."""
    T = Tree(ok, seed, rmin, gap)
    T.blocks = list(blocks)
    rs = [T.root(**r) for r in roots]
    T.grow(rs, kmax)
    if sprigs:
        T.sprigs()
    cv = Canvas()
    paint_tree(cv, T.sc, seed, leaf_k)
    return cv, T


# ----------------------------------------------------------------------------------------------
# gold-line borders, bead rows, the medallion
# ----------------------------------------------------------------------------------------------

def gold_border(poly, outward=True, beads=True, r=1.5):
    """Inlay lines following a closed outline: a black fillet, a bright (white) wire line 1.5 px
    between black edges, a second fine wire, then (optionally) a bead row. Draw on top of the
    ground/scroll; returns svg."""
    sg = 1 if outward else -1
    o = []
    p0 = offset_poly(poly, 0)
    p1 = offset_poly(poly, sg * 2.5)
    p2 = offset_poly(poly, sg * 5.)
    band = offset_poly(poly, sg * 6.)
    # solid band behind the wires
    o.append(f'<path d="{_d(p0, True, 0)}{_d(band[::-1], True, 0)}" fill="#000" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_d(p1 + [p1[0]], False, 0)}" stroke="#fff" stroke-width="1.5" fill="none"/>')
    o.append(f'<path d="{_d(p2 + [p2[0]], False, 0)}" stroke="#fff" stroke-width="1" fill="none"/>')
    if beads:
        o.append(bead_row(offset_poly(poly, sg * (6 + r + .5)), r))
    return "".join(o)


def _resample(poly, step, closed=True):
    pts = poly + [poly[0]] if closed else poly
    out = [pts[0]]
    acc = 0.
    for i in range(1, len(pts)):
        ax, ay = pts[i - 1]
        bx, by = pts[i]
        L = math.hypot(bx - ax, by - ay)
        t = step - acc
        while t <= L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L))
            t += step
        acc = L - (t - step)
    return out


def bead_row(path, r=1.5, closed=True):
    """White beads strung along a polyline on a black fillet; each bead is set a hair up-left so a
    black crescent shadow shows at its lower right (dash-array beads: two paths at any length)."""
    pts = path + ([path[0]] if closed else [])
    d = _d(pts, False, 0)
    p = _n(2 * r + 1.)
    return (f'<path d="{d}" stroke="#000" stroke-width="{_n(2 * r + 1.5)}" fill="none" stroke-linecap="butt"/>'
            f'<g transform="translate(-.5 -.5)"><path d="{d}" stroke="#fff" stroke-width="{_n(2 * r - .5)}" '
            f'stroke-dasharray="0 {p}" stroke-linecap="round" fill="none"/></g>')


def medallion_ring(cx, cy, rx, ry, r=1.5):
    """The inlaid medallion's frame: gold wire, bead ring, gold wire, a fine fillet. Returns
    (svg, inner_points) - the scene goes inside inner_points."""
    o = []
    outer = ell(cx, cy, rx, ry, 96)[:-1]
    w1 = ell(cx, cy, rx - 1.75, ry - 1.75, 96)[:-1]
    bd = ell(cx, cy, rx - 4.5 - r, ry - 4.5 - r, 96)[:-1]
    w2r = 4.5 + 2 * r + 2.5
    w2 = ell(cx, cy, rx - w2r, ry - w2r, 96)[:-1]
    inner = ell(cx, cy, rx - w2r - 1.75, ry - w2r - 1.75, 96)[:-1]
    o.append(f'<path d="{_d(outer, True, 0)}{_d(inner[::-1], True, 0)}" fill="#000" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_d(w1 + [w1[0]], False, 0)}{_d(w2 + [w2[0]], False, 0)}" stroke="#fff" stroke-width="1.5" fill="none"/>')
    o.append(bead_row(bd, r))
    return "".join(o), inner


# ----------------------------------------------------------------------------------------------
# engraved Roman capitals: thick-thin stress and bracketed serifs, filled paths
# ----------------------------------------------------------------------------------------------

_O = [(2 + 2 * math.cos(t * PI / 10), 3 + 3 * math.sin(t * PI / 10)) for t in range(21)]
FONT = {
    "A": (4.2, [[(0, 6), (2.1, 0)], [(2.1, 0), (4.2, 6)], [(.8, 4), (3.4, 4)]]),
    "B": (3.8, [[(0, 0), (0, 6)], [(0, 0), (2.6, 0), (3.4, .7), (3.4, 2.2), (2.6, 2.9), (0, 2.9)], [(0, 2.9), (2.8, 2.9), (3.8, 3.8), (3.8, 5.1), (2.9, 6), (0, 6)]]),
    "C": (4, [[(4, 1.1), (3, .1), (1.3, .1), (0, 1.5), (0, 4.5), (1.3, 5.9), (3, 5.9), (4, 4.9)]]),
    "D": (4.2, [[(0, 0), (0, 6)], [(0, 0), (2.3, 0), (4.2, 1.6), (4.2, 4.4), (2.3, 6), (0, 6)]]),
    "E": (3.4, [[(0, 0), (0, 6)], [(0, 0), (3.4, 0)], [(0, 2.9), (2.6, 2.9)], [(0, 6), (3.4, 6)]]),
    "F": (3.3, [[(0, 0), (0, 6)], [(0, 0), (3.3, 0)], [(0, 2.9), (2.5, 2.9)]]),
    "G": (4.2, [[(4, 1.1), (3, .1), (1.3, .1), (0, 1.5), (0, 4.5), (1.3, 5.9), (3, 5.9), (4.2, 4.9), (4.2, 3.5)], [(2.7, 3.5), (4.2, 3.5)]]),
    "H": (4.2, [[(0, 0), (0, 6)], [(4.2, 0), (4.2, 6)], [(0, 2.9), (4.2, 2.9)]]),
    "I": (0, [[(0, 0), (0, 6)]]),
    "J": (2.8, [[(2.8, 0), (2.8, 4.6), (1.9, 6), (.7, 6), (0, 5.2)]]),
    "K": (4, [[(0, 0), (0, 6)], [(4, 0), (0, 3.7)], [(1.4, 2.5), (4, 6)]]),
    "L": (3.4, [[(0, 0), (0, 6)], [(0, 6), (3.4, 6)]]),
    "M": (5.2, [[(0, 6), (.3, 0)], [(.3, 0), (2.6, 6)], [(2.6, 6), (4.9, 0)], [(4.9, 0), (5.2, 6)]]),
    "N": (4.2, [[(0, 6), (0, 0)], [(0, 0), (4.2, 6)], [(4.2, 6), (4.2, 0)]]),
    "O": (4.4, [[(2.2 + 2.2 * math.cos(t * PI / 10), 3 + 3 * math.sin(t * PI / 10)) for t in range(21)]]),
    "P": (3.7, [[(0, 0), (0, 6)], [(0, 0), (2.7, 0), (3.7, .9), (3.7, 2.3), (2.7, 3.2), (0, 3.2)]]),
    "Q": (4.4, [[(2.2 + 2.2 * math.cos(t * PI / 10), 3 + 3 * math.sin(t * PI / 10)) for t in range(21)], [(2.4, 4.6), (4.4, 6.6)]]),
    "R": (4, [[(0, 0), (0, 6)], [(0, 0), (2.7, 0), (3.7, .9), (3.7, 2.2), (2.7, 3.1), (0, 3.1)], [(1.9, 3.1), (4, 6)]]),
    "S": (3.6, [[(3.5, .9), (2.6, 0), (1, 0), (.1, .9), (.1, 2.1), (1, 2.8), (2.6, 3.2), (3.6, 4), (3.6, 5.1), (2.6, 6), (1, 6), (0, 5.1)]]),
    "T": (4, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
    "U": (4.2, [[(0, 0), (0, 4.6), (1.2, 6), (3, 6), (4.2, 4.6)], [(4.2, 0), (4.2, 6)]]),
    "V": (4.2, [[(0, 0), (2.1, 6)], [(2.1, 6), (4.2, 0)]]),
    "W": (5.8, [[(0, 0), (1.4, 6)], [(1.4, 6), (2.9, 0)], [(2.9, 0), (4.4, 6)], [(4.4, 6), (5.8, 0)]]),
    "X": (4, [[(0, 0), (4, 6)], [(4, 0), (0, 6)]]),
    "Y": (4, [[(0, 0), (2, 3)], [(4, 0), (2, 3)], [(2, 3), (2, 6)]]),
    "Z": (3.8, [[(0, 0), (3.8, 0)], [(3.8, 0), (0, 6)], [(0, 6), (3.8, 6)]]),
    "0": (3.6, [[(1.8 + 1.8 * math.cos(t * PI / 10), 3 + 3 * math.sin(t * PI / 10)) for t in range(21)]]),
    "1": (2.2, [[(.2, 1.1), (1.4, 0)], [(1.4, 0), (1.4, 6)]]),
    "2": (3.6, [[(.1, 1.2), (1, 0), (2.6, 0), (3.5, 1), (3.5, 2.1), (0, 6)], [(0, 6), (3.6, 6)]]),
    "3": (3.5, [[(0, .8), (1, 0), (2.5, 0), (3.4, .9), (3.4, 2), (2.5, 2.9), (1.3, 2.9)], [(1.3, 2.9), (2.6, 2.9), (3.5, 3.9), (3.5, 5.1), (2.6, 6), (1, 6), (0, 5.2)]]),
    "4": (3.8, [[(2.9, 6), (2.9, 0)], [(2.9, 0), (0, 4.3), (3.8, 4.3)]]),
    "5": (3.5, [[(3.4, 0), (.4, 0)], [(.4, 0), (0, 2.8), (1, 2.4), (2.5, 2.4), (3.5, 3.4), (3.5, 5), (2.5, 6), (1, 6), (0, 5.2)]]),
    "6": (3.6, [[(3.3, .6), (2.4, 0), (1.2, 0), (0, 1.4), (0, 4.8), (1, 6), (2.6, 6), (3.6, 5), (3.6, 3.7), (2.6, 2.7), (1, 2.7), (0, 3.6)]]),
    "7": (3.5, [[(0, 0), (3.5, 0)], [(3.5, 0), (1.2, 6)]]),
    "8": (3.6, [[(1.8, 2.9), (.5, 2.2), (.4, .9), (1.2, 0), (2.4, 0), (3.2, .9), (3.1, 2.2), (1.8, 2.9), (.3, 3.8), (0, 5), (1, 6), (2.6, 6), (3.6, 5), (3.3, 3.8), (1.8, 2.9)]]),
    "9": (3.6, [[(3.6, 2.4), (2.6, 3.3), (1, 3.3), (0, 2.3), (0, 1), (1, 0), (2.6, 0), (3.6, 1.2), (3.6, 4.6), (2.4, 6), (1.2, 6), (.3, 5.4)]]),
    "·": (.8, [[(.4, 3), (.4, 3.01)]]),
    "-": (2, [[(0, 3.2), (2, 3.2)]]),
    "'": (.6, [[(.3, 0), (.3, 1.6)]]),
    ".": (.6, [[(.3, 5.9), (.3, 5.91)]]),
    ",": (.6, [[(.4, 5.6), (0, 7)]]),
    "&": (4.2, [[(4.2, 6), (1, 2.2), (1, .8), (1.8, 0), (2.6, .8), (2.6, 1.8), (.3, 3.8), (.3, 5.1), (1.3, 6), (2.6, 6), (4, 3.8)]]),
    "%": (4, [[(0, 6), (4, 0)], [(.9 + .9 * math.cos(t * PI / 5), 1 + 1 * math.sin(t * PI / 5)) for t in range(11)], [(3.1 + .9 * math.cos(t * PI / 5), 5 + 1 * math.sin(t * PI / 5)) for t in range(11)]]),
    "$": (3.6, [[(3.5, .9), (2.6, 0), (1, 0), (.1, .9), (.1, 2.1), (1, 2.8), (2.6, 3.2), (3.6, 4), (3.6, 5.1), (2.6, 6), (1, 6), (0, 5.1)], [(1.8, -.7), (1.8, 6.7)]]),
    ":": (.6, [[(.3, 2), (.3, 2.01)], [(.3, 5.9), (.3, 5.91)]]),
}


def text_width(s, cap, track=1.3):
    k = cap / 6.
    w = 0.
    for ch in s:
        if ch == " ":
            w += 2.6 * k
        else:
            w += (FONT.get(ch, FONT["·"])[0] + track) * k
    return w - track * k


def _glyph_polys(ch, ox, oy, k, xf, wt):
    """Filled shapes for one glyph at local origin (ox, oy) scaled k; xf maps local -> page."""
    adv, strokes = FONT.get(ch, FONT["·"])
    thick = wt * k * 6 / 6.
    thin = max(.55, thick * .36)
    polys = []
    for st in strokes:
        pts = [(ox + x * k, oy + y * k) for x, y in st]
        if len(pts) == 2 and math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) < .1:
            x, y = pts[0]
            polys.append([xf(x + thick * .5 * math.cos(a), y + thick * .5 * math.sin(a)) for a in [TAU * i / 8 for i in range(8)]])
            continue
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L
            # stress: strokes falling to the right (and verticals) are thick, rising ones thin
            a = math.atan2(abs(dy), dx if dy >= 0 else -dx)
            f = max(0., math.sin(a)) ** 1.6 if (dx * dy >= 0 or abs(dx) < .05 * L) else .15 * abs(math.sin(a))
            if abs(dy) < .02 * L:
                f = 0.
            t = thin + (thick - thin) * f
            nx, ny = -uy * t / 2, ux * t / 2
            ex, ey = ux * min(t, thin) * .3, uy * min(t, thin) * .3
            polys.append([xf(ax + nx - ex, ay + ny - ey), xf(bx + nx + ex, by + ny + ey),
                          xf(bx - nx + ex, by - ny + ey), xf(ax - nx - ex, ay - ny - ey)])
        # serifs at free ends that sit on the cap line or the baseline
        for (x, y), (x2, y2) in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            if (abs(y - oy) < .05 or abs(y - (oy + 6 * k)) < .05) and abs(y2 - y) > 1.5 * k:
                sw = k * 1.0
                sy = y + (thin * .5 if abs(y - oy) < .05 else -thin * .5)
                polys.append([xf(x - sw, sy - thin * .5), xf(x + sw, sy - thin * .5), xf(x + sw, sy + thin * .5),
                              xf(x - sw, sy + thin * .5)])
    return polys, adv


def letters(s, cx, cy, cap, track=1.3, wt=.95, centre=None):
    """Polygons for string s centred on (cx, cy), cap height cap. With centre (a polyline), the
    letters are set along it instead, each turned to the local tangent."""
    k = cap / 6.
    total = text_width(s, cap, track)
    polys = []
    if centre is None:
        x = cx - total / 2
        y0 = cy - cap / 2
        for ch in s:
            if ch == " ":
                x += 2.6 * k
                continue
            p, adv = _glyph_polys(ch, x, y0, k, lambda a, b: (a, b), wt)
            polys += p
            x += (adv + track) * k
        return polys
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    pos = L[-1] / 2 - total / 2
    for ch in s:
        if ch == " ":
            pos += 2.6 * k
            continue
        adv = FONT.get(ch, FONT["·"])[0]
        mid = pos + adv * k / 2
        j = 1
        while j < len(L) - 1 and L[j] < mid:
            j += 1
        t = (mid - L[j - 1]) / ((L[j] - L[j - 1]) or 1)
        px = centre[j - 1][0] + (centre[j][0] - centre[j - 1][0]) * t
        py = centre[j - 1][1] + (centre[j][1] - centre[j - 1][1]) * t
        a = math.atan2(centre[j][1] - centre[j - 1][1], centre[j][0] - centre[j - 1][0])
        ca, sa = math.cos(a), math.sin(a)

        def xf(x, y, px=px, py=py, ca=ca, sa=sa):
            lx, ly = x - adv * k / 2, y - cap / 2
            return (px + lx * ca - ly * sa, py + lx * sa + ly * ca)

        p, _ = _glyph_polys(ch, 0, 0, k, xf, wt)
        polys += p
        pos += (adv + track) * k
    return polys


def letters_svg(polys, fill="#000"):
    return f'<path d="{poly_d(polys)}" fill="{fill}" stroke="none"/>' if polys else ""


# ----------------------------------------------------------------------------------------------
# ribbon banner (shaded folds, forked tails) carrying lettering
# ----------------------------------------------------------------------------------------------

def banner(cx, cy, w, h, text, arch=.05, cap=None, seed=0):
    svg, cen = C.ribbon_banner(cx, cy, w, h, arch, seed)
    cap = cap or h * .52
    face = cen[1:-1]
    k = 1.
    while text_width(text, cap * k) > w * .66 and k > .5:
        k -= .05
    pl = letters(text, 0, 0, cap * k, 1.2, 1.05, centre=[(px, py + .3) for px, py in face])
    return svg + letters_svg(pl), cen


# ----------------------------------------------------------------------------------------------
# small figures for eyes and eggs (each: fn(cv, cx, cy, r) inside a disc of radius r)
# ----------------------------------------------------------------------------------------------

def _sp(pts, cx, cy, r, f=1):
    return [(cx + f * x * r, cy + y * r) for x, y in pts]


_DOG = [(.62, .78), (.5, .2), (.46, -.1), (.36, -.38), (.16, -.58), (-.1, -.64), (-.3, -.58), (-.42, -.44),
        (-.52, -.3), (-.78, -.22), (-.9, -.12), (-.92, .0), (-.86, .08), (-.62, .14), (-.44, .2), (-.3, .3),
        (-.16, .46), (-.1, .78)]
_EAR = [(.06, -.56), (.34, -.5), (.46, -.26), (.42, .12), (.3, .3), (.18, .1), (.08, -.24)]


def egg_dog(cv, cx, cy, r, f=1):
    """Parker's dog, the head in profile (facing left): domed skull, long muzzle, black nose, a
    floppy ear in fine cuts, the eye and brow, fur cut along the neck."""
    head = _sp(_DOG, cx, cy, r, f)
    cv.obj([head], 1.)
    # fur along the form: cuts following the skull and down the neck
    for k in range(5):
        t = .12 + k * .14
        cv.hair([(cx + f * (.1 + t * .5) * r, cy + (-.5 + t * .2) * r), (cx + f * (.25 + t * .4) * r, cy + (.0 + t * .7) * r)])
    cv.hair([(cx + f * x * r, cy + y * r) for x, y in ((-.3, -.5), (-.4, -.36), (-.62, -.22), (-.8, -.15))])
    for k in range(4):
        cv.hair([(cx + f * (-.6 + k * .1) * r, cy + .1 * r), (cx + f * (-.45 + k * .12) * r, cy + (.24 + k * .04) * r)])
    ear = _sp(_EAR, cx, cy, r, f)
    cv.obj([ear], 1.)
    cv.hair(C.hatch_poly(ear, 75 if f > 0 else 105, 1.5))
    # eye and brow
    ex, ey = cx + f * -.2 * r, cy - .34 * r
    cv.obj([ell(ex, ey, r * .07, r * .055, 8)[:-1]], 0)
    q = r * .065
    while q > .25:
        cv.line(ell(ex, ey, q, q * .8, 8))
        q -= .7
    cv.line([(ex - f * r * .1, ey - r * .1), (ex + f * r * .1, ey - r * .12)])
    # nose and mouth
    nx, ny = cx + f * -.86 * r, cy - .1 * r
    cv.obj([ell(nx, ny, r * .08, r * .07, 8)[:-1]], 0)
    q = r * .075
    while q > .25:
        cv.line(ell(nx, ny, q, q * .85, 8))
        q -= .7
    cv.line([(cx + f * -.84 * r, cy + .05 * r), (cx + f * -.6 * r, cy + .1 * r), (cx + f * -.5 * r, cy + .06 * r)])
    # collar
    col = _sp([(-.18, .56), (.56, .52), (.6, .66), (-.14, .7)], cx, cy, r, f)
    cv.obj([col], .5)
    cv.line([(cx + f * .2 * r, cy + .63 * r), (cx + f * .2 * r, cy + .64 * r)])


def arms(cx, cy, rx, ry, seed=0):
    """The dedication cartouche: a placeholder for Parker's family arms (to come): crossed
    drumsticks over a rayed sun in a beaded oval with a little leafage either side."""
    o = []
    cv = Canvas()
    for sd in (-1, 1):
        rng = random.Random(seed + sd)
        for j in range(3):
            a = (PI if sd < 0 else 0.) + sd * (-.5 + .5 * j)
            bx, by = cx + sd * rx * .92, cy + ry * .3 * (j - 1)
            leaf(cv, bx, by, (PI if sd < 0 else 0.) + sd * (.35 * (1 - j)), rx * .62, rx * .2, -sd * .5, -sd * 1.2 * (1 if j else -1), 2, 1,
                 rng.randrange(1 << 20))
    o.append(cv.svg())
    o.append(f'<path d="{_d(ell(cx, cy, rx + 3, ry + 3, 60)[:-1], True, 0)}" fill="#000"/>')
    o.append(bead_row(ell(cx, cy, rx + 1, ry + 1, 60)[:-1], 1.5))
    field = ell(cx, cy, rx - 2, ry - 2, 60)[:-1]
    o.append(f'<path d="{_d(field, True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    cv = Canvas()
    cv.obj([field], 0)
    # the sun: a face-less disc with alternating straight and wavy rays, all in fine cuts
    sr = min(rx, ry) * .38
    for k in range(16):
        t = TAU * k / 16 - PI / 2
        L = sr * (1.9 if k % 2 == 0 else 1.55)
        p0 = (cx + sr * 1.05 * math.cos(t), cy + sr * 1.05 * math.sin(t))
        if k % 2 == 0:
            ray = [(cx + sr * 1.05 * math.cos(t - .12), cy + sr * 1.05 * math.sin(t - .12)), (cx + L * math.cos(t), cy + L * math.sin(t)),
                   (cx + sr * 1.05 * math.cos(t + .12), cy + sr * 1.05 * math.sin(t + .12))]
            cv.obj([ray], .5)
            cv.line([p0, (cx + L * .85 * math.cos(t), cy + L * .85 * math.sin(t))])
        else:
            cv.line([(cx + (sr * 1.1 + (L - sr * 1.1) * i / 6) * math.cos(t + .07 * math.sin(i * 1.6)),
                      cy + (sr * 1.1 + (L - sr * 1.1) * i / 6) * math.sin(t + .07 * math.sin(i * 1.6))) for i in range(7)])
    disc = ell(cx, cy, sr, sr, 30)[:-1]
    cv.obj([disc], 1.)
    q = sr - 1.5
    while q > 1:
        cv.hair(ell(cx, cy, q, q, 30)[3:16])
        q -= 1.5
    egg_sticks_only(cv, cx, cy, min(rx, ry) * .95)
    o.append(cv.svg())
    return "".join(o)


def egg_sticks_only(cv, cx, cy, r):
    for sg in (-1, 1):
        a = math.radians(90 + sg * 42)
        x0, y0 = cx + math.cos(a) * r * .9, cy + math.sin(a) * r * .9
        x1, y1 = cx - math.cos(a) * r * .9, cy - math.sin(a) * r * .9
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy, ux
        w0, w1 = r * .07, r * .035
        p = [(x0 + nx * w0, y0 + ny * w0), (x1 + nx * w1, y1 + ny * w1), (x1 - nx * w1, y1 - ny * w1), (x0 - nx * w0, y0 - ny * w0)]
        cv.obj([p], .5)
        cv.hair([(x0 - nx * w0 * .4, y0 - ny * w0 * .4), (x1 - nx * w1 * .4, y1 - ny * w1 * .4)])
        cv.obj([ell(x1 + ux * r * .05, y1 + uy * r * .05, r * .07, r * .06, 10)[:-1]], .5)


def fleuron(cx, base, size, seed=0, up=True):
    """A leaf fleuron (the vise's fleur-de-lis): a tall central blade and two pairs of blades
    curling outward from a banded calyx."""
    cv = Canvas()
    rng = random.Random(seed)
    sd = -1 if up else 1
    for side in (-1, 1):
        leaf(cv, cx + side * size * .08, base, sd * PI / 2 - sd * side * 1.15, size * .7, size * .22,
             -sd * side * .9, -sd * side * 2.4, 2, 1, rng.randrange(1 << 20))
    for side in (-1, 1):
        leaf(cv, cx + side * size * .04, base, sd * PI / 2 - sd * side * .45, size * .85, size * .24,
             -sd * side * .7, -sd * side * 2., 3, 1, rng.randrange(1 << 20))
    leaf(cv, cx, base, sd * PI / 2, size * 1.05, size * .28, .05, .3, 3, 3, rng.randrange(1 << 20))
    cal = [(cx - size * .2, base - sd * size * .02), (cx + size * .2, base - sd * size * .02), (cx + size * .14, base - sd * size * .16),
           (cx - size * .14, base - sd * size * .16)]
    cv.obj([cal], 1.)
    cv.hair(C.hatch_poly(cal, 90, 1.5))
    cv.line([(cx - size * .2, base - sd * size * .09), (cx + size * .2, base - sd * size * .09)])
    return cv.svg()


def egg_heron(cv, cx, cy, r):
    """A Sauvie Island great blue heron standing in the eye: plume, S-neck, dagger bill."""
    s = r / 10.
    body = [(cx - 1 * s, cy - 1 * s), (cx + 3 * s, cy - 1.6 * s), (cx + 5.6 * s, cy + .6 * s), (cx + 7 * s, cy + 3 * s),
            (cx + 3.4 * s, cy + 3 * s), (cx - .6 * s, cy + 2 * s)]
    neck = [(cx - .8 * s, cy - .6 * s), (cx - 2.6 * s, cy - 3.6 * s), (cx - 1.4 * s, cy - 6.2 * s), (cx - 2.6 * s, cy - 7.6 * s),
            (cx - 1.4 * s, cy - 8.2 * s), (cx - .4 * s, cy - 7.4 * s), (cx - .6 * s, cy - 5.4 * s), (cx - 1 * s, cy - 3.8 * s),
            (cx + .6 * s, cy - .9 * s)]
    bill = [(cx - 2.4 * s, cy - 7.9 * s), (cx - 7 * s, cy - 7.2 * s), (cx - 2.2 * s, cy - 7.2 * s)]
    cv.obj([body, neck], 1.)
    for j in range(4):
        cv.hair([(cx + (.4 + j * 1.3) * s, cy - (.9 - j * .5) * s), (cx + (4 + j * .8) * s, cy + (1.2 + j * .45) * s)])
    cv.hair([(cx - 1.6 * s, cy - 5.8 * s), (cx - 1.9 * s, cy - 3.6 * s), (cx - .5 * s, cy - 1.2 * s)])
    cv.obj([bill], .5)
    cv.line([(cx - 1.6 * s, cy - 8.4 * s), (cx + 2 * s, cy - 8.8 * s)])
    cv.line([(cx + 1.6 * s, cy + 2.4 * s), (cx + 1.2 * s, cy + 9 * s)])
    cv.line([(cx + 2.8 * s, cy + 2.6 * s), (cx + 3.4 * s, cy + 9 * s)])
    cv.obj([ell(cx - 1.9 * s, cy - 7.6 * s, .35 * s, .35 * s, 6)[:-1]], 0)


def egg_sticks(cv, cx, cy, r):
    """Crossed drumsticks over a ride cymbal."""
    s = r / 10.
    cym = ell(cx, cy + 1 * s, 8 * s, 2.6 * s, 30)[:-1]
    cv.obj([cym], 1.)
    for k in (2.2, 4.4, 6.4):
        cv.hair(ell(cx, cy + 1 * s, k * s, k * .32 * s, 24))
    cv.obj([ell(cx, cy + .7 * s, 1 * s, .5 * s, 10)[:-1]], .5)
    for sg in (-1, 1):
        a = math.radians(90 + sg * 38)
        x0, y0 = cx + math.cos(a) * 9 * s, cy + math.sin(a) * 9 * s
        x1, y1 = cx - math.cos(a) * 9 * s, cy - math.sin(a) * 9 * s
        ux, uy = (x1 - x0) / 18 / s, (y1 - y0) / 18 / s
        nx, ny = -uy, ux
        w0, w1 = .9 * s, .45 * s
        p = [(x0 + nx * w0, y0 + ny * w0), (x1 + nx * w1, y1 + ny * w1), (x1 - nx * w1, y1 - ny * w1), (x0 - nx * w0, y0 - ny * w0)]
        cv.obj([p], .5)
        cv.hair([(x0 + nx * w0 * .3, y0 + ny * w0 * .3), (x1 + nx * w1 * .3, y1 + ny * w1 * .3)])
        cv.obj([ell(x1 + ux * .6 * s, y1 + uy * .6 * s, .9 * s, .9 * s, 8)[:-1]], .5)


def egg_P(cv, cx, cy, r):
    """A 'P' monogram, engraved, inside a tiny wreath."""
    pl = letters("P", cx, cy, r * 1.15, wt=1.2)
    cv.obj(pl, 0)
    for p in pl:
        cv.line(p + [p[0]])
    cv.hair(ell(cx, cy, r * .82, r * .82, 30))


def egg_hood(cv, cx, cy, r):
    """Mt. Hood: the steep north face, the long south-west shoulder, snow and rock ribs."""
    s = r / 10.
    prof = [(cx - 9 * s, cy + 5 * s), (cx - 5 * s, cy + 1 * s), (cx - 2 * s, cy - 2.6 * s), (cx - .6 * s, cy - 5.4 * s),
            (cx + .4 * s, cy - 6.6 * s), (cx + 1.2 * s, cy - 5.6 * s), (cx + 3.4 * s, cy - 1.6 * s), (cx + 6 * s, cy + 2.4 * s),
            (cx + 9 * s, cy + 5 * s)]
    cv.obj([prof], 1.)
    cv.hair(C.hatch_poly([(cx + .4 * s, cy - 6.6 * s), (cx + 9 * s, cy + 5 * s), (cx + 1 * s, cy + 5 * s)], 0, 1.5))
    for x0 in (-3, -1, 1.6):
        cv.line([(cx + x0 * s * .3, cy - 4.4 * s), (cx + x0 * s, cy + .4 * s)])
    cv.hair(C.hatch_poly([(cx - 9 * s, cy + 5 * s), (cx + 9 * s, cy + 5 * s), (cx + 9 * s, cy + 6 * s), (cx - 9 * s, cy + 6 * s)], 0, 1.5))


def egg_bridge(cv, cx, cy, r):
    """The St. Johns Bridge: two gothic towers and the cable sag."""
    s = r / 10.
    for tx in (-4.5, 4.5):
        tw = [(cx + (tx - 1) * s, cy + 6 * s), (cx + (tx - .7) * s, cy - 6 * s), (cx + tx * s, cy - 7.6 * s),
              (cx + (tx + .7) * s, cy - 6 * s), (cx + (tx + 1) * s, cy + 6 * s)]
        cv.obj([tw], .5)
        cv.hair([(cx + tx * s, cy - 5.6 * s), (cx + tx * s, cy + 5 * s)])
    cv.line([(cx - 10 * s, cy - 1 * s)] + [(cx + x * s, cy - 6 * s + (x * x / 20.25) * 5.4 * s * (1 if abs(x) <= 4.5 else 0) + (0 if abs(x) <= 4.5 else (abs(x) - 4.5) * 1.1 * s)) for x in [-4.5 + 9 * i / 16 for i in range(17)]] + [(cx + 10 * s, cy - 1 * s)])
    cv.line([(cx - 10 * s, cy + 1.6 * s), (cx + 10 * s, cy + 1.6 * s)])
    for x in range(-4, 5):
        cv.hair([(cx + x * s, cy - 6 * s + (x * x / 20.25) * 5.4 * s), (cx + x * s, cy + 1.6 * s)])
    cv.hair([(cx - 10 * s, cy + 4 * s), (cx + 10 * s, cy + 4 * s)])
    cv.hair([(cx - 8 * s, cy + 5.4 * s), (cx + 8 * s, cy + 5.4 * s)])


def egg_kranok(cv, cx, cy, r):
    """A Thai kranok flame rising from a lotus calyx."""
    s = r / 10.
    fl = []
    for i in range(25):
        t = i / 24
        a = PI * t
        fl.append((cx + (4.6 * math.sin(a) * (1 - t * .3)) * s - 2.3 * s, cy + 6 * s - 13 * t * s))
    for i in range(10):
        t = i / 9
        fl.append((cx + (2.3 * s) * math.cos(PI * t) * .9 - 1.4 * s, cy - 7 * s + 2.6 * t * s))
    cv.obj([fl], 1.)
    cv.hair(_offset_pl(fl[2:22], 1.5 * s))
    cv.hair(_offset_pl(fl[4:20], 3 * s))
    cal = [(cx - 5 * s, cy + 5 * s), (cx - 2.4 * s, cy + 8 * s), (cx + 2.4 * s, cy + 8 * s), (cx + 5 * s, cy + 5 * s),
           (cx + 2 * s, cy + 6 * s), (cx, cy + 4.6 * s), (cx - 2 * s, cy + 6 * s)]
    cv.obj([cal], 1.)
    cv.hair(C.hatch_poly(cal, 90, 1.5))


def _offset_pl(pl, d):
    out = []
    for i in range(len(pl)):
        tx, ty = _tang(pl, i)
        out.append((pl[i][0] - ty * d, pl[i][1] + tx * d))
    return out


def egg_note(cv, cx, cy, r):
    """A pair of beamed eighth notes, cut bold enough to read in a small eye."""
    s = r / 10.
    cv.obj([ell(cx, cy, r * .98, r * .98, 32)[:-1]], 0)
    for x, y in ((-4.2, 4.2), (3.6, 2.4)):
        hd = ell(cx + x * s, cy + y * s, 2.5 * s, 1.7 * s, 14)[:-1]
        cv.obj([hd], 1.5)
        cv.heavy([(cx + (x - 1.2) * s, cy + y * s), (cx + (x + 1.2) * s, cy + y * s)])
        cv.heavy([(cx + (x + 2.3) * s, cy + y * s), (cx + (x + 2.3) * s, cy + (y - 9.6) * s)])
    cv.heavy([(cx - 1.9 * s, cy - 5.4 * s), (cx + 5.9 * s, cy - 7.2 * s)])
    cv.heavy([(cx - 1.9 * s, cy - 3.2 * s), (cx + 5.9 * s, cy - 5. * s)])


def egg_panel(cv, cx, cy, r):
    """A solar panel tilted to the sun: cell grid and a tiny sun."""
    s = r / 10.
    A, B, Cc, D = (cx - 7 * s, cy + 1 * s), (cx + 3 * s, cy - 4 * s), (cx + 8 * s, cy + 1.6 * s), (cx - 2 * s, cy + 6.6 * s)
    cv.obj([[A, B, Cc, D]], 1.)
    for i in range(1, 4):
        t = i / 4
        cv.hair([(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t), (D[0] + (Cc[0] - D[0]) * t, D[1] + (Cc[1] - D[1]) * t)])
    for i in range(1, 3):
        t = i / 3
        cv.hair([(A[0] + (D[0] - A[0]) * t, A[1] + (D[1] - A[1]) * t), (B[0] + (Cc[0] - B[0]) * t, B[1] + (Cc[1] - B[1]) * t)])
    cv.line([(cx + .5 * s, cy + 4 * s), (cx + .5 * s, cy + 9 * s)])
    cv.obj([ell(cx - 5 * s, cy - 6 * s, 2 * s, 2 * s, 12)[:-1]], .5)
    for k in range(8):
        a = TAU * k / 8
        cv.hair([(cx - 5 * s + 2.8 * s * math.cos(a), cy - 6 * s + 2.8 * s * math.sin(a)),
                 (cx - 5 * s + 4 * s * math.cos(a), cy - 6 * s + 4 * s * math.sin(a))])


def egg_pinwheel(cv, cx, cy, r):
    """The Blazers pinwheel: two banks of five swept stripes."""
    s = r / 10.
    for sg in (1, -1):
        for i in range(5):
            o = (i - 2) * 1.7 * s
            pl = [(cx - 7.6 * s * sg, cy + o * sg + 3 * s * sg), (cx, cy + o * sg - .5 * s * sg), (cx + 7.6 * s * sg, cy + o * sg - 4 * s * sg)]
            cv.line(pl)
    cv.hair(ell(cx, cy, 9 * s, 9 * s, 30))


def egg_cymbal(cv, cx, cy, r):
    """A ride cymbal on its stand, seen from a little above: lathe rings, the bell, a stick's
    tip resting on the bow."""
    s = r / 10.
    cv.obj([[(cx - .5 * s, cy + 1 * s), (cx + .5 * s, cy + 1 * s), (cx + .7 * s, cy + 9.5 * s), (cx - .7 * s, cy + 9.5 * s)]], .5)
    for sg in (-1, 1):
        cv.line([(cx, cy + 7 * s), (cx + sg * 4 * s, cy + 9.6 * s)])
    rim = ell(cx, cy, 9 * s, 3 * s, 36)[:-1]
    cv.obj([rim], 1.)
    k = 8.
    while k > 2.2:
        cv.hair(ell(cx, cy - .15 * (9 - k) * s, k * s, k * .33 * s, 30)[2:17])
        k -= 1.1
    cv.hair([(cx + 8.4 * s, cy + .6 * s), (cx - 8.4 * s, cy + .6 * s)])
    bell = ell(cx, cy - .9 * s, 2.2 * s, 1 * s, 16)[:-1]
    cv.obj([bell], 1.)
    cv.hair(ell(cx, cy - .9 * s, 1.2 * s, .5 * s, 10)[1:8])
    st = [(cx + 3 * s, cy - 1.6 * s), (cx + 9.6 * s, cy - 8.4 * s), (cx + 10.4 * s, cy - 7.6 * s), (cx + 3.8 * s, cy - .9 * s)]
    cv.obj([st], .5)
    cv.obj([ell(cx + 2.8 * s, cy - 1 * s, .9 * s, .7 * s, 8)[:-1]], .5)


def egg_elephant(cv, cx, cy, r):
    """A Lanna elephant in profile (a Thai accent): domed head, fanned ear, trunk curled up, a
    saddle cloth with a kranok border, the legs as columns."""
    s = r / 10.
    body = [(-6.5, 1), (-6.6, -2.4), (-5, -4.6), (-1.5, -5.4), (2.5, -5.4), (4.4, -6.6), (6.2, -6.4), (7.4, -4.8),
            (7.6, -2.6), (8.2, -.6), (9, 1.2), (9.6, 3), (8.8, 3.2), (8.2, 1.6), (7, .2), (6.6, 2.2),
            (6.6, 6.4), (5.2, 6.4), (5, 3.2), (3.6, 3.2), (3.4, 6.4), (2, 6.4), (2, 3.4), (-2.6, 3.4),
            (-2.8, 6.4), (-4.2, 6.4), (-4.4, 3.4), (-5.2, 3.4), (-5.4, 6.4), (-6.6, 6.4)]
    P = [(cx + x * s - 1 * s, cy + y * s) for x, y in body]
    cv.obj([P], 1.)
    for k in range(4):
        cv.hair([(cx + (-5.6 + k * .3) * s, cy + (-1.8 + k * 1.2) * s), (cx + (-1.2 + k * .2) * s, cy + (-4.4 + k * 1.6) * s)])
    ear = [(cx + 3.2 * s, cy - 4.6 * s), (cx + 5.2 * s, cy - 4.8 * s), (cx + 5.6 * s, cy - 1.2 * s), (cx + 4 * s, cy + .4 * s), (cx + 2.8 * s, cy - 1.6 * s)]
    cv.obj([ear], .5)
    cv.hair(C.hatch_poly(ear, 80, 1.5))
    cloth = [(cx - 4.4 * s, cy - 4.8 * s), (cx + 1.8 * s, cy - 5.2 * s), (cx + 2 * s, cy - .4 * s), (cx - 4.2 * s, cy - .2 * s)]
    cv.obj([cloth], .5)
    cv.hair(C.hatch_poly(cloth, 45, 2.))
    for k in range(5):
        x = cx + (-4 + k * 1.45) * s
        cv.line([(x, cy - .2 * s), (x + .5 * s, cy + .8 * s), (x + 1 * s, cy - .2 * s)])
    cv.obj([ell(cx + 5.8 * s, cy - 4.6 * s, .45 * s, .45 * s, 8)[:-1]], .5)
    cv.line([(cx + 7.4 * s, cy - 1.6 * s), (cx + 8.8 * s, cy - 2.6 * s)])


EGGS = {"dog": egg_dog, "heron": egg_heron, "sticks": egg_sticks, "P": egg_P, "hood": egg_hood,
        "bridge": egg_bridge, "kranok": egg_kranok, "note": egg_note, "panel": egg_panel, "pinwheel": egg_pinwheel,
        "cymbal": egg_cymbal, "elephant": egg_elephant}


# ----------------------------------------------------------------------------------------------
# layouts: band (h < 110), cartouche (110-260), full plate (> 260)
# ----------------------------------------------------------------------------------------------

def _ok_box(x0, y0, x1, y1, holes=(), pad=0.):
    def ok(x, y):
        if x < x0 - pad or x > x1 + pad or y < y0 - pad or y > y1 + pad:
            return False
        for (hx, hy, rx, ry) in holes:
            if ((x - hx) / rx) ** 2 + ((y - hy) / ry) ** 2 < 1:
                return False
        return True
    return ok


def _half_field(w, x0, y0, y1, holes, seed, roots, rmin, kmax=3, leaf_k=1., blocks=(), gid=None):
    """Grow the left half (x <= w/2) and return svg for both halves (mirrored)."""
    ok = _ok_box(x0, y0, w / 2 + 2, y1, holes, 3.)
    cv, T = scroll_field(ok, roots, seed, rmin, kmax, leaf_k, True, .9, blocks)
    area = max(1., (w / 2 - x0) * (y1 - y0))
    cov = sum(s.r * s.r for s in T.sc) / area
    for k in (1, 2):
        if cov >= .1:
            break
        # a stem that strangled itself early: regrow from another cut (deterministic)
        cv2, T2 = scroll_field(ok, roots, seed + 101 * k, rmin, kmax, leaf_k, True, .9, blocks)
        c2 = sum(s.r * s.r for s in T2.sc) / area
        if c2 > cov:
            cv, T, cov = cv2, T2, c2
    return mirror_g(w, cv.svg(), gid), T


def plate_frame(w, h, ctx, scene, opts):
    """The whole plate. scene(x, y, w, h, clip_d, mode) -> svg filling that box (mode: band,
    medium, tall). opts: pid, egg, banner, tablet(tx, ty, tw, th) -> svg, crest(cx, base, size) -> svg,
    med (rx, ry fractions), seed."""
    pid = opts.get("pid", "p")
    seed = opts.get("seed", 1)
    egg = EGGS.get(opts.get("egg", "dog"), egg_dog)
    o = [matte_defs(pid)]
    o.append(matte(rect_d(0, 0, w, h), pid))
    if h < 110:
        o += _band(w, h, ctx, scene, opts, pid, seed, egg)
    elif h <= 260:
        o += _medium(w, h, ctx, scene, opts, pid, seed, egg)
    else:
        o += _tall(w, h, ctx, scene, opts, pid, seed, egg)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{_n(w)}" height="{_n(h)}" viewBox="0 0 {_n(w)} {_n(h)}" '
            f'fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + C.codex_defs() + "".join(o) + "</svg>")


def _edge_lines(w, y, down=True):
    """A gold-line rule across the plate: black fillet with a white wire and a fine wire."""
    s = 1 if down else -1
    return (f'<path d="M0,{_n(y)}h{_n(w)}v{_n(6 * s)}h{_n(-w)}z" fill="#000"/>'
            f'<path d="M0,{_n(y + 2 * s)}h{_n(w)}" stroke="#fff" stroke-width="1.5"{_CR}/>'
            f'<path d="M0,{_n(y + 4.5 * s)}h{_n(w)}" stroke="#fff" stroke-width="1"{_CR}/>')


def rinceau_roots(x_from, x_to, cy, gh, seed, egg=None, sizes=(1., .78, .92, .7, .86, .74)):
    """Volutes alternating up and down along a band from x_from to x_to (either direction), each
    springing from the one before so the stem runs unbroken. Returns Tree.root kwargs."""
    rng = random.Random(seed)
    dirn = 1 if x_to > x_from else -1
    out = []
    x = x_from
    up = True
    prev = (x_from, cy, dirn, 0.)
    i = 0
    while (x_to - x) * dirn > gh * .3 and i < 14:
        r = gh * .34 * sizes[i % len(sizes)] * rng.uniform(.95, 1.04)
        cx = x + dirn * r * 1.15
        ccy = cy + (-1 if up else 1) * gh * .14
        # the spiral starts on its far side from the band centre and winds back toward it
        phi0 = PI / 2 if up else -PI / 2
        sg = dirn if up else -dirn
        out.append(dict(cx=cx, cy=ccy, r=r, sg=sg, phi0=phi0, tail_from=prev,
                        eye=egg if (egg and i == 1) else None))
        # the next stem leaves from under/over this volute
        prev = (cx + dirn * r * .2, ccy + (r if up else -r) * .98, dirn, (-.4 if up else .4))
        x = cx + dirn * r * .95
        up = not up
        i += 1
    return out


def _band(w, h, ctx, scene, opts, pid, seed, egg):
    o = []
    rb = 1.5 if h < 75 else 2.
    top = 6 + 2 * rb + 2
    y0, y1 = top, h - top
    gh = y1 - y0
    cx, cy = w / 2, h / 2
    mry = h / 2 - 1
    mrx = min(w * .2, mry * 3.)
    rmin = max(3.5, gh * .085)
    roots = rinceau_roots(cx - mrx * .9, -gh * .4, cy, gh, seed, egg if gh > 40 else None)
    body, T = _half_field(w, -gh, y0 - 3, y1 + 3, [(cx, cy, mrx * .96, mry)], seed, roots, rmin, 2, 1.,
                          gid=f"{pid}bg")
    o.append(clip_g(f"{pid}bc", rect_d(0, y0, w, gh), body))
    o.append(_edge_lines(w, 0))
    o.append(bead_row([(-2, 6 + rb + .5), (w + 2, 6 + rb + .5)], rb, False))
    o.append(_edge_lines(w, h, False))
    o.append(bead_row([(-2, h - 6 - rb - .5), (w + 2, h - 6 - rb - .5)], rb, False))
    ring, inner = medallion_ring(cx, cy, mrx, mry, 1.)
    xs = [p[0] for p in inner]
    ys = [p[1] for p in inner]
    ix0, ix1, iy0, iy1 = min(xs), max(xs), min(ys), max(ys)
    o.append(f'<path d="{_d(ell(cx, cy, mrx + 1, mry + 1, 96)[:-1], True, 0)}" fill="#000"/>')
    o.append(f'<path d="{_d(inner, True, 0)}" fill="#fff"/>')
    o.append(clip_g(f"{pid}bm", _d(inner, True, 0), scene(ix0, iy0, ix1 - ix0, iy1 - iy0, _d(inner, True, 0), "band")))
    o.append(ring)
    return o


def _medium(w, h, ctx, scene, opts, pid, seed, egg):
    o = []
    m = 3.
    panel = rrect(m, m, w - 2 * m, h - 2 * m, 10)
    cx, cy = w / 2, h / 2
    mry = (h - 2 * m) / 2 - 9
    mrx = min(w * .26, mry * 1.32)
    mcy = cy
    r0 = min(h * .17, 26.)
    rmin = max(5., h * .026)
    # the stem source: under the medallion, curling out into a big volute (the egg in its eye)
    roots = [dict(cx=cx - mrx - r0 * 1.05, cy=h - m - 12 - r0 * .95, r=r0 * 1.3, sg=1, phi0=PI / 2 - .4,
                  tail_from=(cx - mrx * .3, h - m - 8, -1, 0.), eye=egg),
             dict(cx=cx - mrx - r0 * .55, cy=m + 12 + r0 * .7, r=r0 * .72, sg=-1, phi0=PI / 2 + .6,
                  tail_from=(cx - mrx * .35, m + 10, -1, 0.))]
    holes = [(cx, mcy, mrx + 4, mry + 4)]
    body, T = _half_field(w, m + 5, m + 5, h - m - 5, holes, seed, roots, rmin, 3, 1., gid=f"{pid}mg")
    o.append(clip_g(f"{pid}mc", _d(offset_poly(panel, -6), True, 0), body))
    o.append(gold_border(panel, False, True, 1.5))
    # crest and pendant palmettes on the medallion axis
    ring, inner = medallion_ring(cx, mcy, mrx, mry, 1.5)
    xs = [p[0] for p in inner]
    ys = [p[1] for p in inner]
    ix0, ix1, iy0, iy1 = min(xs), max(xs), min(ys), max(ys)
    o.append(f'<path d="{_d(inner, True, 0)}" fill="#fff"/>')
    o.append(clip_g(f"{pid}mm", _d(inner, True, 0), scene(ix0, iy0, ix1 - ix0, iy1 - iy0, _d(inner, True, 0), "medium")))
    o.append(ring)
    return o


def _tall(w, h, ctx, scene, opts, pid, seed, egg):
    o = []
    m = 3.
    ped_h = min(max(h * .17, 52), 92.)
    py0 = h - ped_h
    panel = rrect(m, m, w - 2 * m, py0 - m + 2, 12)
    cx = w / 2
    ph = py0 - m
    mry = min(ph * (.4 if ph < 300 else .36), 150.)
    mrx = min(w * .32, mry * (1.18 + .3 * max(0., min(1., (330 - ph) / 120))))
    mcy = m + ph * .44
    r0 = min(w * .06, ph * .08, 28.)
    rmin = max(5., w * .011)
    roots = [dict(cx=cx - mrx - r0 * .2, cy=py0 - 14 - r0 * 1.3, r=r0 * 1.4, sg=1, phi0=PI / 2 - .3,
                  tail_from=(cx - 16, py0 - 6, -1, -.1), eye=egg),
             dict(cx=cx - mrx * .55, cy=m + 14 + r0 * .75, r=r0 * .78, sg=-1, phi0=PI / 2 + .5,
                  tail_from=(cx - 12, m + 12, -1, 0.)),
             dict(cx=m + 16 + r0 * .7, cy=mcy, r=r0 * .82, sg=1, phi0=0.,
                  tail_from=(m + 10, mcy + r0 * 2.2, 0, -1))]
    bh = min(18., ph * .05)
    ay = (mcy + mry + bh + py0) / 2 + 2
    ary = min(26., (py0 - mcy - mry - bh) * .36)
    arx = ary * 1.2
    holes = [(cx, mcy, mrx + 5, mry + 5), (cx, mcy + mry + 2, mrx * 1.25, bh * 1.2)]
    if ary > 12:
        holes.append((cx, ay, arx * 1.9, ary + 6))
    holes.append((cx, mcy - mry - 8, mrx * .3, min(ph * .08, 30) + 12))
    body, T = _half_field(w, m + 5, m + 5, py0 - 5, holes, seed, roots, rmin, 3, 1., gid=f"{pid}tg")
    o.append(clip_g(f"{pid}tc", _d(offset_poly(panel, -6), True, 0), body))
    o.append(gold_border(panel, False, True, 1.5))
    ring, inner = medallion_ring(cx, mcy, mrx, mry, 2.)
    xs = [p[0] for p in inner]
    ys = [p[1] for p in inner]
    ix0, ix1, iy0, iy1 = min(xs), max(xs), min(ys), max(ys)
    o.append(f'<path d="{_d(inner, True, 0)}" fill="#fff"/>')
    o.append(clip_g(f"{pid}tm", _d(inner, True, 0), scene(ix0, iy0, ix1 - ix0, iy1 - iy0, _d(inner, True, 0), "tall")))
    o.append(ring)
    cs = min(mcy - mry - m - 6, 34.)
    if opts.get("crest"):
        o.append(opts["crest"](cx, mcy - mry + 2, cs))
    elif cs > 10:
        o.append(fleuron(cx, mcy - mry + 2, cs, seed))
    if ary > 12:
        o.append(arms(cx, ay, arx, ary, seed))
    if opts.get("banner"):
        bsvg, _ = banner(cx, mcy + mry + 1, mrx * 2.25, bh, opts["banner"], .04, None, seed)
        o.append(bsvg)
    o.append(_pedestal(0, py0, w, ped_h, pid, opts, seed))
    return o


def _pedestal(x, y, w, h, pid, opts, seed):
    """The plinth: knurled cornice, an inlaid tablet framed in gold lines and beads on a matte
    face, scroll-ended at both sides, a knurled base."""
    o = []
    kb = max(5., min(8., h * .1))
    o.append(C.knurled_bar(x + 2, y + 1, w - 4, kb))
    fy = y + kb + 2
    fh = h - 2 * kb - 5
    face = rrect(x + 8, fy, w - 16, fh, 4)
    o.append(matte(_d(face, True, 0), pid, True))
    tw = w * .62
    th = fh - 10
    tx, ty = x + (w - tw) / 2, fy + 5
    tab = rrect(tx, ty, tw, th, 3)
    o.append(f'<path d="{_d(tab, True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    if opts.get("tablet"):
        o.append(opts["tablet"](tx + 5, ty + 4, tw - 10, th - 8))
    o.append(gold_border(tab, True, False))
    # scrolls on the face either side of the tablet
    side_w = (w - 16 - tw) / 2 - 10
    if side_w > 20:
        ok = _ok_box(x + 9, fy + 1, tx - 7, fy + fh - 1)
        r0 = min(fh * .36, side_w * .3)
        roots = [dict(cx=tx - 8 - r0 * 1.1, cy=fy + fh / 2, r=r0, sg=-1, phi0=0., tail_from=(tx - 7, fy + fh - 3, -1, -.3))]
        cv, T = scroll_field(ok, roots, seed + 9, max(4., fh * .09), 3, 1., True, .9)
        o.append(clip_g(f"{pid}pc", _d(face, True, 0), mirror_g(w, cv.svg(), f"{pid}pg")))
    o.append(gold_border(face, False, False))
    o.append(C.knurled_bar(x + 2, y + h - kb - 1, w - 4, kb))
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# burin fields: tone laid as flowing contour lines that swell and taper (skies, water, ground)
# ----------------------------------------------------------------------------------------------

def bumps(specs):
    """g(x, y) for burin_field: a sum of soft bumps (cx, cy, sx, sy, amp) - lines rise over each
    bump the way strata of cloud roll over one another. Bumps are bucketed in 24 px columns."""
    B = {}
    for cx, cy, sx, sy, a in specs:
        for k in range(int((cx - 3 * sx) // 24), int((cx + 3 * sx) // 24) + 1):
            B.setdefault(k, []).append((cx, cy, 1 / sx, 1 / sy, a, cy - 3 * sy, cy + 3 * sy))
    ex = math.exp

    def g(x, y):
        v = 0.
        for cx, cy, isx, isy, a, ylo, yhi in B.get(int(x // 24), ()):
            if ylo < y < yhi:
                dx, dy = (x - cx) * isx, (y - cy) * isy
                q = dx * dx + dy * dy
                if q < 9:
                    v += a * ex(-q)
        return v
    return g


def burin_field(cv, x0, x1, y0, y1, g=None, tone=None, pitch=3., ok=None, step=2.5, phase=0., cross=None):
    """Lines y + g(x, y) = level, `pitch` apart, from x0..x1 within y0..y1. tone(x, y) in [0, 1]
    sets each stretch's weight (under .1 the line breaks: a highlight; .1-.42 a .5 px cut; .42-.72
    1 px; above 1.5 px), so the line swells and tapers with the form. ok(x, y) clips.
    cross: tone above which a second layer at 45 degrees is laid (cross-hatch in the shadows)."""
    g = g or (lambda x, y: 0.)
    tone = tone or (lambda x, y: .3)
    ws = {.5: [], 1.: [], 1.5: []}
    lev = y0 - 12 + phase
    nx = max(2, int((x1 - x0) / step))
    while lev < y1 + 12:
        cur, cw = [], None
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            y = lev - g(x, lev)
            y = lev - g(x, y)
            if y < y0 or y > y1 or (ok and not ok(x, y)):
                t = -1
            else:
                t = tone(x, y)
            w = None if t < .1 else (.5 if t < .42 else (1. if t < .72 else 1.5))
            if w != cw:
                if cw and len(cur) > 1:
                    ws[cw].append(cur)
                cur = [cur[-1]] if (cur and w and cw) else []
                cw = w
            if w:
                cur.append((x, y))
        if cw and len(cur) > 1:
            ws[cw].append(cur)
        lev += pitch
    cv.hair(ws[.5])
    cv.line(ws[1.])
    cv.heavy(ws[1.5])
    if cross is not None:
        box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for ln in C.hatch_poly(box, -45, 3., .7):
            (ax, ay), (bx, by) = ln
            L = math.hypot(bx - ax, by - ay)
            m = max(2, int(L / 1.5))
            run = []
            for k in range(m + 1):
                px, py = ax + (bx - ax) * k / m, ay + (by - ay) * k / m
                if (not ok or ok(px, py)) and tone(px, py) > cross:
                    run.append((px, py))
                else:
                    if len(run) > 1:
                        cv.hair([run[0], run[-1]])
                    run = []
            if len(run) > 1:
                cv.hair([run[0], run[-1]])


def cloud(cv, cx, cy, w, h, rng, lit=(0., -1.)):
    """A rolling cumulus: overlapping round lobes, each outlined, its belly shaded in contour
    lines on the side away from the light."""
    n = max(3, int(w / h * 2.2))
    lobes = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else .5
        lx = cx - w / 2 + w * t
        ly = cy - h * .5 * math.sin(PI * t) ** .8 + rng.uniform(-h * .08, h * .08)
        lr = h * (.38 + .32 * math.sin(PI * t)) * rng.uniform(.85, 1.1)
        lobes.append((lx, ly, lr))
    lobes.sort(key=lambda q: q[1])
    a0 = math.atan2(-lit[1], -lit[0])
    for lx, ly, lr in lobes:
        pts = ell(lx, ly, lr, lr * .82, 26)[:-1]
        cv.obj([pts], .5)
        # the belly turned from the light: arcs that close up and swell toward the shadowed edge
        f = .94
        k = 0
        while f > .3:
            span = 1.25 * (1.25 - f)
            arc = [(lx + lr * f * math.cos(a0 + t), ly + lr * .82 * f * math.sin(a0 + t)) for t in
                   [-span + 2 * span * j / 12 for j in range(13)]]
            (cv.line if k < 2 and lr > 8 else cv.hair)(arc)
            f -= 1.6 / max(lr, 4)
            k += 1
    base = [(cx - w / 2 - h * .2, cy + h * .1), (cx + w / 2 + h * .2, cy + h * .1), (cx + w / 2, cy + h * .34), (cx - w / 2, cy + h * .34)]
    cv.obj([base], 0)
    for k in range(3):
        yy = cy + h * (.14 + .08 * k)
        cv.line([(cx - w / 2 + k * 3, yy), (cx + w / 2 - k * 3, yy)]) if k else cv.hair([(cx - w / 2, yy), (cx + w / 2, yy)])



def dots_d(pts):
    """Zero-length dots as compact relative path data (stroke them with round caps)."""
    out = []
    px, py = 0, 0
    for x, y in pts:
        X, Y = int(round(x * 10)), int(round(y * 10))
        out.append(f"m{C._f(X - px)}{'' if Y - py < 0 else ' '}{C._f(Y - py)}h.5")
        px, py = X + 5, Y
    d = "".join(out)
    return "M" + d[1:] if d else ""


import datetime

_ell = C._ell_pts
SYN = 29.530588853


def _age(date):
    try:
        d = datetime.datetime.strptime((date or "")[:10], "%Y-%m-%d") + datetime.timedelta(hours=20)
    except ValueError:
        d = datetime.datetime(2026, 11, 11, 20)
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    return ((d - ref).total_seconds() / 86400.) % SYN


def _phase_polys(cx, cy, r, age, n=40, min_lit=.0):
    """(lit, dark) polygons of a moon disc at `age` days. Waxing lit on the right."""
    p = TAU * age / SYN
    k = (1 - math.cos(p)) / 2
    if min_lit and k < min_lit:
        p = math.acos(1 - 2 * min_lit) * (1 if p < math.pi else -1) % TAU
    waxing = p < math.pi
    c = math.cos(p)
    sx = 1 if waxing else -1
    ts = [-math.pi / 2 + math.pi * i / n for i in range(n + 1)]
    limb_lit = [(cx + sx * r * math.cos(t), cy + r * math.sin(t)) for t in ts]
    term = [(cx + sx * r * c * math.cos(t), cy + r * math.sin(t)) for t in ts[::-1]]
    limb_dark = [(cx - sx * r * math.cos(t), cy + r * math.sin(t)) for t in ts]
    lit = limb_lit + term
    dark = term[::-1] + limb_dark[::-1]
    return lit, dark, sx, c


def _star(x, y, s):
    return [(x, y - s), (x + s * .28, y - s * .28), (x + s, y), (x + s * .28, y + s * .28),
            (x, y + s), (x - s * .28, y + s * .28), (x - s, y), (x - s * .28, y - s * .28)]


def _dog(x, y, s, face=1):
    """A sitting dog, muzzle raised to the moon. (x, y) = front paws on the ground, s = height."""
    Q = [(78, 4), (74, 12), (68, 20), (62, 28), (60, 40), (62, 52), (62, 70), (63, 92), (68, 96), (68, 100),
         (54, 100), (54, 80), (52, 72), (46, 78), (44, 90), (46, 96), (48, 100), (12, 100), (2, 99), (0, 96),
         (8, 94), (12, 88), (13, 76), (18, 64), (26, 52), (36, 38), (44, 28), (46, 22), (40, 17), (44, 13),
         (50, 12), (58, 10), (64, 8), (72, 2)]
    P = [((qx - 60) / 100, (qy - 100) / 100) for qx, qy in Q]
    return [(x + face * px * s, y + py * s) for px, py in P]


def _heron(x, y, s, face=-1):
    """A great blue heron standing in the shallows, neck folded. (x, y) = feet."""
    body = [(0, -.48), (.16, -.56), (.30, -.60), (.36, -.66), (.32, -.76), (.30, -.86), (.36, -.94),
            (.44, -.97), (.62, -.92), (.46, -.90), (.40, -.86), (.42, -.76), (.46, -.64), (.42, -.52),
            (.30, -.42), (.12, -.38), (-.10, -.36), (-.30, -.28), (-.12, -.40)]
    legs = [[(.10, -.39), (.08, 0)], [(.16, -.39), (.22, 0)]]
    f = lambda q: (x + face * q[0] * s, y + q[1] * s)
    return [f(q) for q in body], [[f(q) for q in L] for L in legs]


def _phase_disc(cx, cy, r, age):
    cv = C.Canvas()
    lit, dark, sx, c = _phase_polys(cx, cy, r, age, 24)
    disc = _ell(cx, cy, r, r, 32)
    cv.obj([disc], 1.)
    k = (1 - math.cos(TAU * age / SYN)) / 2
    if k < .98:
        cv.hair(C.hatch_poly(dark, 45, 1.5))
        cv.hair(C.hatch_poly(dark, -45, 2))
    # maria on the lit face, cut in fine lines
    for (u, v, a, b) in ((-.3, -.3, .3, .22), (.1, -.1, .24, .26), (-.2, .35, .26, .16)):
        m = _ell(cx + u * r, cy + v * r, a * r, b * r, 14)[:-1]
        cv.hair(C.hatch_poly(m, 30, 2))
    return cv.svg()




def _scene(x, y, w, h, ctx, mode):
    date = (ctx or {}).get("date", "")
    rng = random.Random(date + "moon")
    age = _age(date)
    compact = mode == "band"
    cv = Canvas()
    hor = y + h * (.64 if not compact else .66)
    r = min(h * (.2 if not compact else .25), w * (.13 if not compact else .1))
    mx, my = x + w * .69, y + (hor - y) * (.42 if not compact else .52)
    halo = r * 2.1
    # sky: strata of cloud drifting across in flowing lines, darkest at the zenith, opening into a
    # halo of light round the moon; cross-hatch layered only in the deepest night
    specs = []
    for i in range(7 if not compact else 4):
        specs.append((x + w * rng.uniform(.0, 1.), y + (hor - y) * rng.uniform(.15, .85), w * rng.uniform(.12, .22),
                      (hor - y) * rng.uniform(.05, .1), (hor - y) * rng.uniform(.03, .07)))
    g = bumps(specs)

    def sky_tone(px, py):
        d = math.hypot(px - mx, py - my) / halo
        z = 1 - (py - y) / max(1., hor - y)
        t = .46 + .42 * z
        cl = g(px, py - 2) - g(px, py + 2)
        t += max(-.2, min(.3, cl * 1.8))
        if d < 1:
            t *= .25 + .75 * d ** 2
        return t

    cv.obj([[(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, hor + 1), (x - 2, hor + 1)]], 0)
    burin_field(cv, x - 2, x + w + 2, y - 2, hor + 1, g, sky_tone, 2. if compact else 3., cross=.78)
    # stars knocked out of the night
    n = int(w * (hor - y) / (220 if not compact else 140))
    stars = []
    for _ in range(n * 4):
        if len(stars) >= n:
            break
        sx_, sy_ = rng.uniform(x + 3, x + w - 3), rng.uniform(y + 3, hor - 10)
        if math.hypot(sx_ - mx, sy_ - my) < halo + 4 or any(math.hypot(sx_ - a, sy_ - b) < 10 for a, b, _ in stars):
            continue
        stars.append((sx_, sy_, rng.choice((1.6, 2., 2.4, 3., 3.6)) * (.8 if compact else 1.)))
    px_, py_ = x + w * .18, y + (hor - y) * .28
    for dx, dy in ((0, 0), (4, -1.5), (6.5, 1.5), (3, 3.5), (8.5, -.5), (1.5, -3.6)):
        stars.append((px_ + dx * (.8 if compact else 1.3), py_ + dy * (.8 if compact else 1.3), 1.3))
    for sx_, sy_, s in stars:
        cv.obj([_star(sx_, sy_, s)], 0)
        if s > 2.6:
            cv.obj([[(sx_ - .5, sy_ - s * 1.9), (sx_ + .5, sy_ - s * 1.9), (sx_ + .5, sy_ + s * 1.9), (sx_ - .5, sy_ + s * 1.9)]], 0)
    # the moon: a thin lit crescent, the rest of the disc in earthshine (cross-cut, maria darker)
    lit, dark, sx, c = _phase_polys(mx, my, r, age, 48, min_lit=.12)
    disc = _ell(mx, my, r, r, 60)
    cv.obj([disc], 1.)
    burin_field(cv, mx - r, mx + r, my - r, my + r, bumps([(mx - r * .3, my - r * .2, r * .4, r * .3, r * .08),
                                                           (mx + r * .1, my + r * .3, r * .35, r * .25, -r * .06)]),
                lambda px, py: .55 + .2 * ((px - mx) * -sx) / r, 1.5 if r < 20 else 2.,
                ok=lambda px, py: (px - mx) ** 2 + (py - my) ** 2 < (r - .8) ** 2)
    for (u, v, a, b) in ((-.35, -.35, .3, .22), (.05, -.12, .24, .28), (-.22, .32, .28, .18)):
        m = _ell(mx + u * r, my + v * r, a * r, b * r, 18)[:-1]
        cv.hair(C.hatch_poly(m, 45, 2))
    cv.obj([lit], .5)
    for f in (.2, .45):
        cv.hair([(mx + sx * r * (1 - f * .35) * math.cos(t), my + r * (1 - f * .1) * math.sin(t))
                 for t in [-PI / 2 * .8 + PI * .8 * i / 20 for i in range(21)]])
    # Mt. Hood on the horizon: north face steep, the long south-west shoulder, snow and ribs
    hx = x + w * (.3 if not compact else .28)
    hh = min(h * .36, (hor - y) * .62, w * .24)
    hw = hh * 1.75
    prof = [(hx - hw, hor + 1), (hx - hw * .6, hor - hh * .22), (hx - hw * .32, hor - hh * .5),
            (hx - hw * .14, hor - hh * .8), (hx - hw * .05, hor - hh * .95), (hx, hor - hh),
            (hx + hw * .04, hor - hh * .94), (hx + hw * .08, hor - hh * .96), (hx + hw * .2, hor - hh * .7),
            (hx + hw * .42, hor - hh * .42), (hx + hw * .65, hor - hh * .18), (hx + hw, hor + 1)]
    cv.obj([prof], .5 if compact else 1.)
    snow = hor - hh * .45
    cv.hair(C.hatch_poly([(hx, hor - hh), (hx - hw * .05, hor - hh * .95), (hx - hw * .14, hor - hh * .8),
                          (hx - hw * .32, hor - hh * .5), (hx - hw * .6, hor - hh * .22), (hx - hw, hor + 1),
                          (hx - hw * .08, hor + 1)], 60, 1.5 if not compact else 2))
    for i, f in enumerate((.1, .22, .34, .48, .6)):
        gx = hx + hw * f * .6
        cv.line([(hx + hw * .012 * i, hor - hh * (.94 - .05 * i)), (gx, hor - hh * .58 + rng.uniform(-2, 2))])
        cv.hair([(gx, hor - hh * .58), (gx + hw * .06, snow + rng.uniform(0, 4))])
    for ln in C.hatch_poly(prof, 0, 1.5):
        if ln[0][1] > snow + rng.uniform(-3, 3):
            cv.hair(ln)
    # foothills with a fir line, then the water
    hills = [(x - 2, hor + 1)]
    for i in range(41):
        t = i / 40
        hills.append((x + w * t, hor - h * .05 * (1 + math.sin(t * 9.1 + 1.3)) * (1.2 - t * .5) - h * .012 * math.sin(t * 31)))
    hills += [(x + w + 2, hor + 3), (x - 2, hor + 3)]
    cv.obj([hills], .5)
    burin_field(cv, x - 2, x + w + 2, hor - h * .12, hor + 3, bumps([(x + w * .3, hor, w * .2, h * .06, h * .02)]),
                lambda px, py: .62, 1.5, ok=lambda px, py: inside(hills, px, py))
    for k in range(int(w / 5)):
        tx_ = x + k * 5 + rng.uniform(0, 3)
        t = (tx_ - x) / w
        ty_ = hor - h * .05 * (1 + math.sin(t * 9.1 + 1.3)) * (1.2 - t * .5)
        th_ = h * rng.uniform(.015, .03)
        cv.line([(tx_, ty_ + 1), (tx_, ty_ - th_)])
        cv.hair([(tx_ - th_ * .35, ty_), (tx_, ty_ - th_), (tx_ + th_ * .35, ty_)])
    water = [(x - 2, hor + 2.5), (x + w + 2, hor + 2.5), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([water], 0)

    def w_tone(px, py):
        depth = (py - hor) / max(1., y + h - hor)
        half = r * (.25 + depth * .7)
        dd = abs(px - mx) / half
        t = .38 + .3 * depth
        if dd < 1:
            ripple = math.sin(px * 1.7 + py * 2.3) * math.sin(px * .6 - py * 1.1)
            t = .0 if ripple > -.2 + dd * .9 else .32
        return t

    ripples = bumps([(x + w * f, hor + (y + h - hor) * rng.uniform(.2, .9), w * .08, h * .03, rng.uniform(-1.4, 1.4))
                     for f in (.1, .25, .4, .55, .7, .85, .95)])
    burin_field(cv, x - 2, x + w + 2, hor + 3, y + h + 2, ripples, w_tone, 1.5 if compact else 2.)
    body = cv.svg()
    # the Sauvie Island bank in the foreground, black, cut with white grass lines; the dog
    # howling at the moon and a heron in the shallows
    by = y + h * (.86 if not compact else .88)
    bx1 = x + w * (.44 if not compact else .4)

    def bank_y(px):
        t = (px - x) / (bx1 - x)
        return by + (y + h - by) * (t ** 2) * .9 - h * .012 * math.sin(t * 7)

    bank = [(x - 2, y + h + 2), (x - 2, by - h * .02)] + [(x + (bx1 - x) * i / 12, bank_y(x + (bx1 - x) * i / 12)) for i in range(13)] + [(bx1 + 6, y + h + 2)]
    blk = [_d(bank, True, .2)]
    reeds = []
    for i in range(int(w * .32 / 3)):
        rx_ = x + w * .02 + i * 3 + rng.uniform(-1, 1)
        rh = h * rng.uniform(.03, .08)
        lean = rng.uniform(-.25, .35) * rh
        reeds.append([(rx_, bank_y(rx_) + 1), (rx_ + lean * .4, bank_y(rx_) - rh * .6), (rx_ + lean, bank_y(rx_) - rh)])
    ds = h * (.16 if not compact else .24)
    dxp = x + w * (.3 if not compact else .2)
    dog = _dog(dxp, bank_y(dxp) + 1, ds, 1)
    blk.append(_d(dog, True, .1))
    hs = h * (.18 if not compact else .22)
    hb, legs = _heron(x + w * (.55 if not compact else .47), by + h * .045, hs, -1)
    blk.append(_d(hb, True, .1))
    grass = []
    for i in range(int((bx1 - x) / 4)):
        gx = x + 2 + i * 4 + rng.uniform(-1, 1)
        gy = bank_y(gx) + rng.uniform(3, max(4, (y + h - bank_y(gx)) * .8))
        if gy < y + h - 1:
            grass.append([(gx, gy), (gx + rng.uniform(-1, 1.5), gy - rng.uniform(2, 4))])
    o = [body, f'<path d="{"".join(blk)}" fill="#000" stroke="none"/>',
         f'<path d="{"".join(_d(L, tol=0) for L in legs)}" stroke="#000" stroke-width="1"/>',
         f'<path d="{"".join(_d(L, tol=.1) for L in reeds)}" stroke="#000" stroke-width="1"/>',
         f'<path d="{"".join(_d(L, tol=0) for L in grass)}" stroke="#fff" stroke-width="1"/>',
         f'<path d="{_d(dog[25:] + dog[:1], tol=.1)}" stroke="#fff" stroke-width="1"/>']
    return "".join(o)


_PH = [("FIRST QTR", "XVII NOV", .25), ("FULL", "XXIV NOV", .5), ("LAST QTR", "XXX NOV", .75), ("NEW", "VIII DEC", 0.)]


def _tablet(tx, ty, tw, th):
    """The coming phases engraved on the pedestal tablet: four discs with their names and dates."""
    o = []
    rr = min(th * .32, tw / 16)
    cap = min(th * .17, 7.)
    pl = []
    for i, (nm, dt, f) in enumerate(_PH):
        c0 = tx + tw * i / 4
        dx = c0 + rr + 3
        o.append(_phase_disc(dx, ty + th / 2, rr, SYN * f))
        tc = (dx + rr + c0 + tw / 4) / 2 + 1
        pl += letters(nm, tc, ty + th / 2 - cap * .8, cap, wt=.9)
        pl += letters(dt, tc, ty + th / 2 + cap * .9, cap * .85, wt=.8)
    o.append(letters_svg(pl))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7

    def scene(x, y, sw, sh, clip, mode):
        return _scene(x, y, sw, sh, ctx, mode)

    return plate_frame(w, h, ctx, scene, dict(pid="nb", seed=seed, egg="dog", banner="MOON WATCH · IV PER CENT LIT",
                                              tablet=_tablet))
