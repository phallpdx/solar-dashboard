"""delights-04 "Good news / Faith in humanity": US Highway 101 turned 100 (finished 11 Nov 1926)
and a woman was pulled from the high surf at Secret Beach on the south Oregon coast. King tier.

The scene, inlaid in a beaded medallion in fine scroll on a punched matte: the Oregon coast at
dawn cut as copperplate. The sky is laid in flowing burin lines that swell in the shadowed rays
and break into light round the half-risen sun; cumulus roll over in contour lines; Highway 101
is benched into the forested headland and leaps the gorge on a McCullough concrete arch; Secret
Beach's sea stacks and natural arch stand in a sea cut in wavering lines that break into the
sun's glitter path; a life ring floats by a swimmer's raised arm and the breaker curls into an
acanthus volute. The tall plate is crowned by the US 101 shield, lettered on the banner, and its
tablet runs the highway's century from MCMXXVI to MMXXVI past ten decade mileposts.
Easter eggs: a great blue heron on the tallest sea stack (Sauvie Island), and a little McCullough
deck arch in the eye of the lowest scroll."""
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
    """A Thai kranok flame rising from a lotus calyx, its tip flicking over; cut bold on a white
    disc so it reads in a small eye."""
    s = r / 10.
    cv.obj([ell(cx, cy, r * .98, r * .98, 32)[:-1]], 0)
    fl = []
    for i in range(25):
        t = i / 24
        a = PI * t
        fl.append((cx + (4.6 * math.sin(a) * (1 - t * .3)) * s - 2.3 * s, cy + 5 * s - 12 * t * s))
    for i in range(10):
        t = i / 9
        fl.append((cx + (2.3 * s) * math.cos(PI * t) * .9 - 1.4 * s, cy - 7 * s + 2.6 * t * s))
    cv.obj([fl], 1.5)
    cv.line(_offset_pl(fl[3:21], 1.8 * s))
    cv.heavy([(cx - .2 * s, cy + 4.4 * s), (cx + .4 * s, cy), (cx - .2 * s, cy - 3.6 * s), (cx - 1.6 * s, cy - 5.4 * s)])
    cal = [(cx - 5.5 * s, cy + 4.6 * s), (cx - 2.8 * s, cy + 8 * s), (cx + 2.8 * s, cy + 8 * s), (cx + 5.5 * s, cy + 4.6 * s),
           (cx + 2.2 * s, cy + 5.8 * s), (cx, cy + 4.2 * s), (cx - 2.2 * s, cy + 5.8 * s)]
    cv.obj([cal], 1.5)
    cv.line([(cx - 2.4 * s, cy + 6.2 * s), (cx - 1.4 * s, cy + 7.6 * s)])
    cv.line([(cx + 2.4 * s, cy + 6.2 * s), (cx + 1.4 * s, cy + 7.6 * s)])


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


TONE_K = [1.]   # a global tone scale: the free vignettes lighten every ground (black budget)


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
                t = tone(x, y) * TONE_K[0]
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
                if (not ok or ok(px, py)) and tone(px, py) * TONE_K[0] > cross:
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


# ----------------------------------------------------------------------------------------------
# planned forms (edition plan 1.6): the plate takes the page's own shape - roundel, oval, arched
# top, banner (ribbon with swallowtails), lunette or frieze - and leaves the page ground showing
# outside it. The medallion carries the scene; scroll grows from stems placed in the widest parts
# of the ground between the medallion and the border.
# ----------------------------------------------------------------------------------------------

def egg_castle(cv, cx, cy, r):
    """The Somaster castle as a sandcastle: two crenellated towers, a crenellated wall, an arched
    gate, a pennant, on a mound of sand."""
    s = r / 10.
    cv.obj([ell(cx, cy, r * .98, r * .98, 32)[:-1]], 0)
    base = cy + 5.5 * s

    def crenel(x0, x1, y):
        n = max(2, int((x1 - x0) / (1.6 * s)))
        pts = [(x0, y)]
        for i in range(n):
            a = x0 + (x1 - x0) * i / n
            b = x0 + (x1 - x0) * (i + .5) / n
            pts += [(a, y - 1.3 * s), (b, y - 1.3 * s), (b, y)]
        return pts + [(x1, y)]
    for tx in (-5.2, 2.4):
        t = [(cx + tx * s, base)] + crenel(cx + tx * s, cx + (tx + 2.8) * s, cy - 6 * s) + [(cx + (tx + 2.8) * s, base)]
        cv.obj([t], 1.5)
        cv.line([(cx + (tx + 1.4) * s, cy - 3.6 * s), (cx + (tx + 1.4) * s, cy - 2 * s)])
    wall = [(cx - 2.4 * s, base)] + crenel(cx - 2.4 * s, cx + 2.4 * s, cy - 2 * s) + [(cx + 2.4 * s, base)]
    cv.obj([wall], 1.5)
    gate = [(cx - 1.2 * s, base)] + [(cx + 1.2 * s * math.cos(PI - PI * i / 8), cy + 1.6 * s - 1.4 * s * math.sin(PI * i / 8)) for i in range(9)] + [(cx + 1.2 * s, base)]
    cv.obj([gate], 1.)
    cv.line([(cx - .4 * s, base), (cx - .4 * s, cy + .6 * s)])
    cv.line([(cx + .4 * s, base), (cx + .4 * s, cy + .6 * s)])
    cv.line([(cx + 3.8 * s, cy - 7.4 * s), (cx + 3.8 * s, cy - 10 * s)])
    cv.obj([[(cx + 3.8 * s, cy - 10 * s), (cx + 6.4 * s, cy - 9.2 * s), (cx + 3.8 * s, cy - 8.4 * s)]], 1.)
    cv.obj([[(cx - 8 * s, base + 2 * s), (cx - 6.5 * s, base), (cx + 6.5 * s, base), (cx + 8 * s, base + 2 * s)]], 1.)
    for k in range(5):
        cv.hair([(cx - 6 * s + k * 3 * s, base + 1.2 * s), (cx - 5 * s + k * 3 * s, base + 1.2 * s)])


def egg_flag(cv, cx, cy, r):
    """A chequered flag on its staff."""
    s = r / 10.
    cv.obj([ell(cx, cy, r * .98, r * .98, 32)[:-1]], 0)
    cv.heavy([(cx - 5 * s, cy + 7.5 * s), (cx - 5 * s, cy - 7 * s)])
    n, m = 4, 3
    for i in range(n):
        for j in range(m):
            x0 = cx - 4.5 * s + i * 2.4 * s
            y0 = cy - 6.5 * s + j * 2.4 * s + .5 * s * math.sin(i * 1.3)
            q = [(x0, y0), (x0 + 2.4 * s, y0 + .4 * s), (x0 + 2.4 * s, y0 + 2.8 * s), (x0, y0 + 2.4 * s)]
            cv.obj([q], .5)
            if (i + j) % 2 == 0:
                cv.line([[(x0 + .3 * s, y0 + k * .8 * s + .5 * s), (x0 + 2.1 * s, y0 + k * .8 * s + .8 * s)] for k in range(3)])


EGGS["castle"] = egg_castle
EGGS["flag"] = egg_flag


def fast_inside(poly):
    """inside(poly, x, y) with the scanline crossings cached per half-pixel row."""
    cache = {}
    n = len(poly)

    def ok(x, y):
        k = int(y * 2)
        xs = cache.get(k)
        if xs is None:
            yy = k / 2 + .25
            xs = sorted(ax + (bx - ax) * (yy - ay) / (by - ay) for (ax, ay), (bx, by) in
                        ((poly[i], poly[(i + 1) % n]) for i in range(n)) if (ay > yy) != (by > yy))
            cache[k] = xs
        c = 0
        for v in xs:
            if v < x:
                c += 1
            else:
                break
        return c % 2 == 1
    return ok


def shape_poly(form, w, h, maxk=9.):
    """The plate outline (screen coords) for a planned form."""
    if form == "roundel":
        r = min(w, h) / 2 - 1
        return ell(w / 2, h / 2, r, r, 120)[:-1]
    if form == "oval":
        ry = h / 2 - 1
        rx = min(w / 2 - 1, ry * 2.7)
        return ell(w / 2, h / 2, rx, ry, 120)[:-1]
    if form == "arched":
        c = w - 2
        a = min(h * .32, c / 2)
        R = (c * c / 4 + a * a) / (2 * a)
        cy = 1 + R
        a0 = math.asin(min(1., (c / 2) / R))
        arc = [(w / 2 + R * math.sin(t), cy - R * math.cos(t)) for t in [-a0 + 2 * a0 * i / 60 for i in range(61)]]
        return [(1, h - 1), (1, arc[0][1])] + arc + [(w - 1, arc[-1][1]), (w - 1, h - 1)]
    if form == "lunette":
        R = min(w / 2 - 1, h - 2)
        return [(w / 2 + R * math.cos(PI + PI * i / 80), h - 1 + R * math.sin(PI + PI * i / 80)) for i in range(81)]
    if form == "banner":
        bw = min(w - 2, h * maxk)
        x0 = (w - bw) / 2
        nd = min(h * .32, 18)
        return [(x0, 1), (x0 + bw, 1), (x0 + bw - nd, h / 2), (x0 + bw, h - 1), (x0, h - 1), (x0 + nd, h / 2)]
    return [(1, 1), (w - 1, 1), (w - 1, h - 1), (1, h - 1)]


def auto_roots(ok, x0, x1, y0, y1, n=3, rmax=40., rmin=5., axis=None, step=7.):
    """Stems for a scroll field: the n widest clear spots of the ground (largest empty circles),
    each fed by a stem from the side nearer the plate's axis."""
    cands = []
    y = y0 + step / 2
    while y < y1:
        x = x0 + step / 2
        while x < x1:
            if ok(x, y):
                r = rmin
                while r < rmax and all(ok(x + r * math.cos(TAU * i / 10), y + r * math.sin(TAU * i / 10)) for i in range(10)):
                    r += 2.
                if r > rmin:
                    cands.append((r, x, y))
            x += step
        y += step
    cands.sort(reverse=True)
    out = []
    for r, x, y in cands:
        if all(math.hypot(x - q[1], y - q[2]) > (r + q[0]) * 1.1 for q in out):
            out.append((r, x, y))
            if len(out) >= n:
                break
    roots = []
    for i, (r, x, y) in enumerate(out):
        rr = r * .62
        ax = axis if axis is not None else x1
        dirn = 1 if ax > x else -1
        roots.append(dict(cx=x, cy=y, r=rr, sg=1 if i % 2 == 0 else -1, phi0=PI / 2 - .3 if i % 2 == 0 else -PI / 2 + .3,
                          tail_from=(x + dirn * rr * 1.25, y + rr * .9, dirn, -.2)))
    return roots


def shaped_frame(w, h, ctx, scene, opts):
    """A plate in a planned form (opts['form']): roundel, oval, arched, lunette, banner, frieze."""
    form = opts.get("form", "oval")
    pid = opts.get("pid", "p")
    seed = opts.get("seed", 1)
    egg = EGGS.get(opts.get("egg")) if opts.get("egg") else None
    o = [matte_defs(pid)]
    if form in ("banner", "frieze", "headpiece") or h < 56:
        o += _banner_form(w, h, ctx, scene, opts, pid, seed, egg, form)
    else:
        P = shape_poly(form, w, h)
        xs = [p[0] for p in P]
        ys = [p[1] for p in P]
        X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
        PW, PH = X1 - X0, Y1 - Y0
        cx = w / 2
        med = opts.get("med")
        if med:
            mcx, mcy, mrx, mry = med(X0, Y0, PW, PH)
        elif form == "roundel":
            mcx, mcy, mrx, mry = cx, Y0 + PH / 2, PW * .33, PH * .33
        elif form == "oval":
            k = max(0., min(1., (PH - 60) / 80))
            mcx, mcy, mrx, mry = cx, Y0 + PH / 2, min(PW * (.4 - .1 * k), PH * .62 + PH * .2 * (1 - k)), PH * (.42 - .06 * k)
        elif form == "lunette":
            mcx, mcy, mrx, mry = cx, Y1 - PH * .42, PW * .3, PH * .38
        else:
            mcx, mcy, mrx, mry = cx, Y0 + PH * .57, min(PW * .36, PH * .78), PH * .4
        o.append(matte(_d(P, True, 0), pid))
        inner = offset_poly(P, -6)
        okP = fast_inside(inner)
        bh = min(16., PH * .07) if (opts.get("banner") and PH > 150) else 0
        holes = [(mcx, mcy, mrx + 5, mry + 5)]
        if bh:
            holes.append((mcx, mcy + mry + 1, mrx * 1.2, bh * 1.2))

        def ok(x, y):
            if x > cx + 2 or not okP(x, y):
                return False
            for hx, hy, rx, ry in holes:
                if ((x - hx) / rx) ** 2 + ((y - hy) / ry) ** 2 < 1:
                    return False
            return True
        rmin = max(4., min(PW, PH) * .02)
        roots = auto_roots(ok, X0, cx, Y0, Y1, 6, min(30., PH * .12), rmin, cx, max(5., PH / 60))
        if roots and egg:
            roots[0]["eye"] = egg
        cv, T = scroll_field(ok, roots, seed, rmin, 3, 1., True, .9)
        o.append(clip_g(f"{pid}sc", _d(inner, True, 0), mirror_g(w, cv.svg(), f"{pid}sg")))
        o.append(gold_border(P, False, PH > 90, 1.5 if PH > 160 else 1.))
        ring, inn = medallion_ring(mcx, mcy, mrx, mry, 1.5 if mry > 40 else 1.)
        ix = [p[0] for p in inn]
        iy = [p[1] for p in inn]
        o.append(f'<path d="{_d(inn, True, 0)}" fill="#fff"/>')
        o.append(clip_g(f"{pid}sm", _d(inn, True, 0), scene(min(ix), min(iy), max(ix) - min(ix), max(iy) - min(iy), _d(inn, True, 0), form)))
        o.append(ring)
        if bh:
            bsvg, _ = banner(mcx, mcy + mry + 1, mrx * 2.3, bh, opts["banner"], .04, None, seed)
            o.append(bsvg)
        if opts.get("extra"):
            o.append(opts["extra"](w, h, (mcx, mcy, mrx, mry), P))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{_n(w)}" height="{_n(h)}" viewBox="0 0 {_n(w)} {_n(h)}" '
            f'fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + C.codex_defs() + "".join(o) + "</svg>")


def _banner_form(w, h, ctx, scene, opts, pid, seed, egg, form):
    """Headpiece / tailpiece banner (swallowtailed ribbon) or a gap frieze: a running scroll from
    both ends into a central cartouche holding the scene."""
    o = []
    P = shape_poly("banner" if form == "banner" else "rect", w, h, opts.get("maxk", 9.))
    xs = [p[0] for p in P]
    bx0, bx1 = min(xs), max(xs)
    bw = bx1 - bx0
    cx, cy = w / 2, h / 2
    o.append(matte(_d(P, True, 0), pid))
    rb = 1. if h < 50 else 1.5
    top = 3 + 2 * rb + (2 if h >= 50 else 1)
    y0, y1 = top, h - top
    gh = y1 - y0
    mry = h / 2 - 1
    mrx = min(bw * .22, mry * opts.get("mk", 5. if form == "frieze" else 2.2))
    rmin = max(3., gh * .085)
    nd = min(h * .32, 18) if form == "banner" else 0
    okP = fast_inside(offset_poly(P, -3))

    def ok(x, y):
        return y0 - 3 < y < y1 + 3 and x <= cx + 2 and okP(x, y) and ((x - cx) / (mrx * .96 + 3)) ** 2 + ((y - cy) / (mry + 3)) ** 2 >= 1
    roots = rinceau_roots(cx - mrx * .92, bx0 + nd * .5, cy, gh, seed, egg if gh > 34 else None)
    cv, T = scroll_field(ok, roots, seed, rmin, 2, 1., True, .9)
    o.append(clip_g(f"{pid}bc", _d(P, True, 0), mirror_g(w, cv.svg(), f"{pid}bg")))
    # wires along the long edges, following the swallowtails
    for yy, s in ((1.5, 1), (h - 1.5, -1)):
        o.append(f'<path d="M{_n(bx0)},{_n(yy)}H{_n(bx1)}" stroke="#000" stroke-width="3"/>')
        o.append(bead_row([(bx0 + nd * .4, yy + s * (2.5 + rb)), (bx1 - nd * .4, yy + s * (2.5 + rb))], rb, False))
    o.append(f'<path d="{_d(P, True, 0)}" stroke="#000" stroke-width="1.5" fill="none"/>')
    if h < 44:
        # a slim cartouche: a black fillet with one bright wire, so the scene keeps its room
        inner = ell(cx, cy, mrx - 2.5, mry - 2.5, 96)[:-1]
        wire = ell(cx, cy, mrx - 1.2, mry - 1.2, 96)
        ring = (f'<path d="{_d(ell(cx, cy, mrx, mry, 96)[:-1], True, 0)}{_d(inner[::-1], True, 0)}" fill="#000" fill-rule="evenodd"/>'
                f'<path d="{_d(wire, False, 0)}" stroke="#fff" stroke-width="1"/>')
    else:
        ring, inner = medallion_ring(cx, cy, mrx, mry, 1. if h < 70 else 1.5)
    ix = [p[0] for p in inner]
    iy = [p[1] for p in inner]
    o.append(f'<path d="{_d(ell(cx, cy, mrx + 1, mry + 1, 96)[:-1], True, 0)}" fill="#000"/>')
    o.append(f'<path d="{_d(inner, True, 0)}" fill="#fff"/>')
    o.append(clip_g(f"{pid}bq", _d(inner, True, 0), scene(min(ix), min(iy), max(ix) - min(ix), max(iy) - min(iy), _d(inner, True, 0), "band")))
    o.append(ring)
    return o


# ----------------------------------------------------------------------------------------------
# free vignettes (art direction, batch review): the subject IS the plate. A shaped engraved scene
# standing free on the page, its edge dissolving into the paper the way Bewick's tailpieces do
# (white cuts that break the lines up more and more toward the rim), no black field, no generic
# scroll. Structure comes from the subject's own motifs (opts['motifs']) and a lettered ribbon.
# ----------------------------------------------------------------------------------------------

def _ragged(P, amp, seed):
    rng = random.Random(seed)
    n = len(P)
    cx = sum(p[0] for p in P) / n
    cy = sum(p[1] for p in P) / n
    out = []
    ph = [rng.uniform(0, 6) for _ in range(3)]
    for i, (x, y) in enumerate(P):
        t = i / n * TAU
        k = 1 - amp * (.5 + .25 * math.sin(7 * t + ph[0]) + .15 * math.sin(13 * t + ph[1]) + .1 * math.sin(29 * t + ph[2]))
        out.append((cx + (x - cx) * k, cy + (y - cy) * k))
    return out


def strip_poly(w, h, maxk=9.):
    """A long lens for headpieces and tailpieces: the scene runs out to points at both ends."""
    bw = min(w - 2, h * maxk)
    x0 = (w - bw) / 2
    pts = []
    for i in range(61):
        t = i / 60
        pts.append((x0 + bw * t, h / 2 - (h / 2 - 1) * math.sin(PI * t) ** .35))
    for i in range(61):
        t = 1 - i / 60
        pts.append((x0 + bw * t, h / 2 + (h / 2 - 1) * math.sin(PI * t) ** .35))
    return pts


def free_vignette(w, h, ctx, scene, opts):
    form = opts.get("form", "oval")
    pid = opts.get("pid", "p")
    seed = opts.get("seed", 1)
    TONE_K[0] = opts.get("tone", .74)
    if form == "strip":
        P = strip_poly(w, h, opts.get("maxk", 9.))
    else:
        P = shape_poly(form, w, h)
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
    R = _ragged(P, min(.05, 6. / max(1., min(X1 - X0, Y1 - Y0))), seed)
    o = []
    mode = "band" if (form == "strip" or Y1 - Y0 < 70) else ("medium" if Y1 - Y0 < 200 else "tall")
    body = scene(X0, Y0, X1 - X0, Y1 - Y0, _d(R, True, 0), mode)
    o.append(clip_g(f"{pid}fv", _d(R, True, 0), f'<path d="{_d(R, True, 0)}" fill="#fff"/>' + body))
    # the dissolving edge: white cuts laid over the rim, closer together toward the paper
    m = min(X1 - X0, Y1 - Y0)
    rings = ((1.2, 2.6, None), (3.4, 1.5, "4 1.2"), (5.6, 1.5, "2 2"), (8., 1., "1.2 3.2"), (10.5, 1., ".8 5"))
    for d, sw, da in rings:
        if d > m * .18:
            break
        ring = offset_poly(R, -d)
        dash = f' stroke-dasharray="{da}" stroke-dashoffset="{_n(d * 1.7)}"' if da else ""
        o.append(f'<path d="{_d(ring + [ring[0]], False, 0)}" stroke="#fff" stroke-width="{_n(sw)}" fill="none"{dash}/>')
    if opts.get("motifs"):
        o.append(opts["motifs"](w, h, (X0, Y0, X1, Y1), R))
    if opts.get("banner") and (Y1 - Y0) >= 150:
        bh = min(16., (Y1 - Y0) * .07)
        bsvg, _ = banner(w / 2, Y1 - bh * .9, min((X1 - X0) * .62, 360), bh, opts["banner"], .04, None, seed)
        o.append(bsvg)
    if opts.get("extra"):
        o.append(opts["extra"](w, h, None, P))
    TONE_K[0] = 1.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{_n(w)}" height="{_n(h)}" viewBox="0 0 {_n(w)} {_n(h)}" '
            f'fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + C.codex_defs() + "".join(o) + "</svg>")



# ----------------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------------

def _runs(y, x0, x1, keep, step=1.):
    """Horizontal runs at y between x0..x1 where keep(x) is true."""
    out, a, b = [], None, None
    x = x0
    while x <= x1:
        if keep(x):
            if a is None:
                a = x
            b = x
        else:
            if a is not None and b - a > .5:
                out.append([(a, y), (b, y)])
            a = None
        x += step
    if a is not None and b - a > .5:
        out.append([(a, y), (b, y)])
    return out


def _clip_y(segs, ylo, yhi):
    out = []
    for (ax, ay), (bx, by) in segs:
        if ay > by:
            ax, ay, bx, by = bx, by, ax, ay
        if by < ylo or ay > yhi:
            continue
        if by - ay < 1e-6:
            out.append([(ax, ay), (bx, by)])
            continue
        t0 = max(0., (ylo - ay) / (by - ay))
        t1 = min(1., (yhi - ay) / (by - ay))
        if t1 > t0:
            out.append([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)])
    return out


def _clip_x(segs, xlo, xhi):
    out = []
    for (ax, ay), (bx, by) in segs:
        if ax > bx:
            ax, ay, bx, by = bx, by, ax, ay
        if bx < xlo or ax > xhi:
            continue
        if bx - ax < 1e-6:
            out.append([(ax, ay), (bx, by)])
            continue
        t0 = max(0., (xlo - ax) / (bx - ax))
        t1 = min(1., (xhi - ax) / (bx - ax))
        if t1 > t0:
            out.append([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)])
    return out


def _poly_y(prof, x):
    """y of a left-to-right profile polyline at x."""
    for i in range(len(prof) - 1):
        (ax, ay), (bx, by) = prof[i], prof[i + 1]
        if ax <= x <= bx and bx > ax:
            return ay + (by - ay) * (x - ax) / (bx - ax)
    return None


def _ins_fast(poly):
    """inside(poly) as a fast test: the scanline crossings are cached per half-pixel row."""
    cache = {}
    n = len(poly)

    def ok(x, y):
        k = int(y * 2)
        xs = cache.get(k)
        if xs is None:
            yy = k / 2 + .25
            xs = sorted(ax + (bx - ax) * (yy - ay) / (by - ay) for (ax, ay), (bx, by) in
                        ((poly[i], poly[(i + 1) % n]) for i in range(n)) if (ay > yy) != (by > yy))
            cache[k] = xs
        c = 0
        for v in xs:
            if v < x:
                c += 1
            else:
                break
        return c % 2 == 1
    return ok


def _prof_fast(prof):
    """_poly_y as a 1 px lookup table."""
    x0 = int(prof[0][0]) - 1
    tab = [_poly_y(prof, float(x)) for x in range(x0, int(prof[-1][0]) + 2)]

    def f(x):
        i = int(x) - x0
        return tab[i] if 0 <= i < len(tab) else None
    return f


def _offset(pl, d):
    """Polyline pl offset by d px along its left normal."""
    out = []
    n = len(pl)
    for i in range(n):
        a, b = pl[max(0, i - 1)], pl[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        out.append((pl[i][0] - ty / L * d, pl[i][1] + tx / L * d))
    return out


# ----------------------------------------------------------------------------------------------
# a single-stroke engraver's alphabet (grid 0..4 wide, 0..6 tall, y down) for path lettering
# ----------------------------------------------------------------------------------------------

_GLYPH = {
    "0": [[(2, 0), (.6, .8), (0, 3), (.6, 5.2), (2, 6), (3.4, 5.2), (4, 3), (3.4, .8), (2, 0)]],
    "1": [[(1, 1.2), (2.4, 0), (2.4, 6)], [(1, 6), (3.8, 6)]],
    "2": [[(.2, 1.3), (1, .2), (2.4, 0), (3.6, .8), (3.7, 2.2), (2.6, 3.6), (0, 6), (4, 6)]],
    "6": [[(3.5, .6), (2.2, 0), (.8, .7), (.1, 2.6), (.2, 4.6), (1, 5.8), (2.4, 6), (3.6, 5.2), (3.8, 4), (3, 3), (1.8, 2.8), (.4, 3.6)]],
    "9": [[(3.6, 2.4), (2.6, 3.2), (1.2, 3.1), (.3, 2.2), (.4, .9), (1.6, 0), (2.9, .2), (3.8, 1.4), (3.8, 3.6), (3.1, 5.4), (1.8, 6), (.6, 5.4)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "G": [[(3.8, 1), (2.6, 0), (1.2, .2), (.2, 1.6), (0, 3), (.3, 4.6), (1.4, 5.9), (2.8, 6), (4, 5), (4, 3.4), (2.4, 3.4)]],
    "W": [[(0, 0), (1, 6), (2, 2), (3, 6), (4, 0)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "U": [[(0, 0), (0, 4.4), (.8, 5.7), (2, 6), (3.2, 5.7), (4, 4.4), (4, 0)]],
    "S": [[(3.7, .9), (2.6, 0), (1.2, .1), (.3, 1), (.5, 2.3), (2, 3), (3.5, 3.7), (3.8, 5), (2.8, 5.9), (1.2, 6), (.2, 5.1)]],
    "-": [[(.6, 3.2), (3.4, 3.2)]],
    " ": [],
}


def _letter_along(text, centre, size, gap=1.25):
    """Lettering laid along a centre polyline (left to right), letters `size` px tall."""
    s = size / 6
    adv = [(4 + gap) * s if ch != " " else 3 * s for ch in text]
    total = sum(adv) - gap * s
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    mid = S[-1] / 2

    def at(d):
        for i in range(1, len(S)):
            if S[i] >= d:
                t = (d - S[i - 1]) / ((S[i] - S[i - 1]) or 1)
                a, b = centre[i - 1], centre[i]
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
        a, b = centre[-2], centre[-1]
        return b, math.atan2(b[1] - a[1], b[0] - a[0])

    out = []
    d = mid - total / 2
    for ch, ad in zip(text, adv):
        (px, py), ang = at(d + 2 * s)
        ca, sa = math.cos(ang), math.sin(ang)
        for stroke in _GLYPH.get(ch, []):
            out.append([(px + ((gx - 2) * s) * ca - ((gy - 3) * s) * sa, py + ((gx - 2) * s) * sa + ((gy - 3) * s) * ca)
                        for gx, gy in stroke])
        d += ad
    return out


def _letters(text, cx, cy, size, gap=1.25):
    s = size / 6
    w = sum((4 + gap) * s if ch != " " else 3 * s for ch in text)
    return _letter_along(text, [(cx - w, cy), (cx + w, cy)], size, gap)


def _stroke_path(pls, w):
    return (f'<path d="{"".join(_d(p, tol=0) for p in pls)}" fill="none" stroke="#000" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# ----------------------------------------------------------------------------------------------
# the US 101 route shield (drawn, never lettered)
# ----------------------------------------------------------------------------------------------

def _shield_pts(cx, cy, s):
    """US route shield outline, s = half width."""
    pts = [(-1, -.86), (-.62, -.86), (-.5, -1.0), (.5, -1.0), (.62, -.86), (1, -.86)]
    right = []
    for i in range(1, 14):
        t = i / 14
        right.append((1 + .06 * math.sin(PI * t) - t ** 2.4, -.86 + t * 1.98))
    pts += right + [(0, 1.12)] + [(-x, y) for x, y in right[::-1]]
    return [(cx + x * s, cy + y * s) for x, y in pts]


def shield_101(cx, cy, s):
    o = []
    outer = _shield_pts(cx, cy, s)
    inner = _shield_pts(cx, cy + s * .03, s * .8)
    o.append(f'<path d="{_d(outer, True, 0)}" fill="#fff" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_d(outer, True, 0)}{_d(inner[::-1], True, 0)}" fill="{C.pat("K")}" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(inner, True, 0)}" fill="{C.pat("L")}" stroke="#000" stroke-width="1"/>')
    o.append(letters_svg(letters("US", cx, cy - s * .5, s * .32, 1.6, 1.1) + letters("101", cx, cy + s * .2, s * .72, 1.1, 1.25)))
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# figures
# ----------------------------------------------------------------------------------------------

def _conifer(cv, x, base, hgt):
    """A small black fir: dense 1 px strokes fanned from the apex."""
    w = hgt * .36
    k = max(3, int(w * 2.2))
    cv.line([[(x, base - hgt), (x - w + 2 * w * i / k, base)] for i in range(k + 1)])
    cv.line([(x, base - hgt - .8), (x, base + 1)])


def _heron(cv, x, y, s):
    """Great blue heron standing, feet at (x, y), s ~ height px. The Easter egg."""
    P = lambda a, b: (x + a * s, y + b * s)
    body = [P(-.3, -.32), P(-.12, -.5), P(.1, -.55), P(.24, -.48), P(.12, -.38), P(-.1, -.34)]
    cv.obj([body], 1.)
    cv.hair([P(-.08, -.46), P(.14, -.48)])
    cv.heavy([P(.18, -.52), P(.26, -.68), P(.17, -.8), P(.22, -.94), P(.3, -.96)])   # S-neck
    cv.line([P(.3, -.96), P(.55, -.92)])                                               # dagger bill
    cv.hair([P(.2, -.97), P(.04, -.92)])                                               # plume
    cv.line([P(-.02, -.36), P(-.04, 0)])
    cv.line([P(.06, -.37), P(.09, 0)])


def _life_ring(cv, cx, cy, rx):
    ry = rx * .45
    cv.obj([C._ell_pts(cx, cy, rx, ry, 28)], 1.)
    hole = C._ell_pts(cx, cy, rx * .48, ry * .42, 18)
    cv.line(hole + [hole[0]])
    cv.hair(C.hatch_poly(hole, 0, 1.5))
    for a0 in (.35, 1.95, 3.5, 5.1):  # the four bands, cut solid
        f = 0.
        while f < .45:
            a = a0 + f
            cv.line([(cx + rx * .52 * math.cos(a), cy + ry * .46 * math.sin(a)), (cx + rx * .96 * math.cos(a), cy + ry * .94 * math.sin(a))])
            f += .07
    for a in (0.9, 2.6, 4.2, 5.8):  # grab line
        cv.hair([(cx + rx * math.cos(a), cy + ry * math.sin(a)),
                 (cx + rx * 1.14 * math.cos(a + .25), cy + ry * 1.3 * math.sin(a + .25)),
                 (cx + rx * math.cos(a + .5), cy + ry * math.sin(a + .5))])


def _swimmer(cv, x, y, s):
    """A head and one arm raised out of the water, reaching for the ring."""
    head = C._ell_pts(x, y - s * .3, s * .3, s * .32, 14)
    cv.obj([head], 1.)
    cv.line(_clip_y(C.hatch_poly(head, 0, 1.), y - s * .7, y - s * .36))  # wet hair
    cv.heavy([(x - s * .2, y - s * .05), (x - s * .5, y - s * .7), (x - s * .6, y - s * 1.25)])
    cv.line([(x - s * .6, y - s * 1.25), (x - s * .75, y - s * 1.35)])
    for r in (s * .6, s * 1.):
        cv.line(C._ell_pts(x, y, r, r * .3, 18, PI * .05, PI * .95))


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            c = not c
    return c


def _clip_in(pls, poly, step=1.2):
    """Keep only the parts of polylines inside poly."""
    _ok = _ins_fast(poly)
    out = []
    for pl in pls:
        run = []
        for i in range(len(pl)):
            pts = [pl[i]]
            if i + 1 < len(pl):
                (ax, ay), (bx, by) = pl[i], pl[i + 1]
                k = int(math.hypot(bx - ax, by - ay) / step)
                pts += [(ax + (bx - ax) * j / (k + 1), ay + (by - ay) * j / (k + 1)) for j in range(1, k + 1)]
            for p in pts:
                if _ok(p[0], p[1]):
                    run.append(p)
                else:
                    if len(run) > 1:
                        out.append(run)
                    run = []
        if len(run) > 1:
            out.append(run)
    return out


def _wave(cv, cx, cy, r, sea_y, X0, X1, Ybot, rng, claws=5, tb=1.0):
    """A breaker rolling in from the left and curling over to the right into a volute with a
    drilled eye, carved like an acanthus stem: lines along its form, packed and black on the
    hollow side, white on the lit back; its lip breaks into curling acanthus claws of foam."""
    tail = 2.4
    sp = C.volute_spine(cx, cy, r, 195, 1.3, False, tail, tb, .12)
    n = len(sp)
    S = [0.]
    for k in range(1, n):
        S.append(S[-1] + math.hypot(sp[k][0] - sp[k - 1][0], sp[k][1] - sp[k - 1][1]))
    tot = S[-1]
    u_sp = (tail * r) / tot
    Wd = [max(.8, r * .5 * (1 - S[k] / tot) ** .85 * (.04 + .96 * C._smooth(0, 1, S[k] / tot / u_sp))) for k in range(n)]
    i = n - n // 4
    a, b = sp[i - 1], sp[i + 1]
    ins = 1 if (-(b[1] - a[1])) * (cx - sp[i][0]) + (b[0] - a[0]) * (cy - sp[i][1]) > 0 else -1
    R = C._Rib(sp, Wd, Wd)
    # the water body: under the back of the wave and the falling lip, down to the foot
    ks = [k for k in range(n) if S[k] / tot <= u_sp + (1 - u_sp) * .42]
    back = [R.at(k / (n - 1), -ins) for k in ks]
    lip = back[-1]
    sea_y = back[0][1]
    body = [(X0, Ybot), (X0, back[0][1] + 1.5)] + back + [(lip[0] + r * .3, lip[1] + r * .2), (X1, lip[1] + r * .4), (X1, Ybot), (X0, Ybot)]
    cv.obj([body], 0)
    swell = [(X0, back[0][1] + 1.5)] + back
    lines = []
    d, k = 1.2, 0
    while d < (Ybot - cy) + r * 2:
        lines.append([(x, y + d) for x, y in swell])
        k += 1
        d += 1.5 if k < 10 else 2
    cv.hair(_clip_in(lines, body))
    cv.hair(_clip_y(C.hatch_poly(body, -35, 2), cy + r * .9, Ybot + 2))
    # the hollow inside the curl: dark, cross-cut
    hol = C._ell_pts(cx + r * .05, cy + r * .2, r * .62, r * .5, 30)
    cv.obj([hol], 0)
    cv.line(C.hatch_poly(hol, 0, 1.5))
    cv.hair(C.hatch_poly(hol, 70, 2))
    # the curling crest itself
    c = ins
    cv.obj([R.outline()], 1.)
    cv.hair(C._fill_lines(R, .04 * c, .98 * c, 1.5, .0, 1., 4))
    cv.hair(C._fill_lines(R, -.15 * c, -.65 * c, 2.5, .05, .9, 2))
    C._shadow(cv, R, c, r * .12, .1, .97)
    ex, ey = sp[-1]
    cv.obj([C._ell_pts(ex, ey, 2.4, 2.4, 14)], 0)
    q = 1.8
    while q > .3:
        cv.line(C._ell_pts(ex, ey, q, q, 10))
        q -= .8
    # foam claws along the lip, each a small acanthus finger reaching forward and rolling under
    for j in range(claws):
        u = u_sp + (1 - u_sp) * (.03 + .4 * j / max(1, claws - 1))
        kk = max(1, min(n - 2, next(k for k in range(n) if S[k] / tot >= u)))
        a, b = sp[kk - 1], sp[kk + 1]
        ta = math.atan2(b[1] - a[1], b[0] - a[0])
        p = R.at(kk / (n - 1), -ins * .6)
        L = r * (.5 + .3 * math.sin(PI * j / max(1, claws - 1))) * rng.uniform(.9, 1.1)
        C._finger(cv, p[0], p[1], ta - ins * .5, L, L * .17, ins * 1.1, ins * 3.2, .8)
    return sp


# ----------------------------------------------------------------------------------------------
# the vignette: Highway 101 above Secret Beach at dawn
# ----------------------------------------------------------------------------------------------

def _stack(cv, rr, xc, wb, wt, top, base, arch=None):
    """A sea stack: a tapering, weathered column of basalt with a rounded, grassy crown."""
    n = 12
    L, Rr = [], []
    for i in range(n + 1):
        t = i / n
        half = wb / 2 * (1 - t) ** .7 + wt / 2 * (1 - (1 - t) ** .7)
        wob = rr.uniform(-.6, .6) + .9 * math.sin(t * 9 + xc)
        L.append((xc - half + wob, base - (base - top) * t))
        Rr.append((xc + half + wob * .7, base - (base - top) * t))
    crown = [(xc - wt / 2 + wt * u / 8, top - wt * .22 * math.sin(PI * u / 8) ** .6 - rr.uniform(0, 1.2)) for u in range(1, 8)]
    poly = L + crown + Rr[::-1]
    if arch:
        hx0, hx1, htop = arch
        poly += [(hx0 + (hx1 - hx0) * (.5 + .5 * math.cos(PI * u / 16)), base - (base - htop) * math.sin(PI * u / 16) ** .7) for u in range(17)]
    cv.obj([poly], 1.)
    x0, x1 = xc - wb / 2, xc + wb / 2
    hw = wb / 2 + 1
    # bowed contour lines round the column: swelling on the shadow side, breaking on the lit edge
    burin_field(cv, x0 - 3, x1 + 3, top - 3, base + 1, lambda x, y: -1.6 * max(0., 1 - ((x - xc) / hw) ** 2),
                lambda x, y: .15 + .8 * max(0., min(1., (xc + wb * .32 - x) / wb)), 1.5, step=2.5,
                ok=_ins_fast(poly), cross=.72)
    cv.hair(crown)
    cv.hair(_clip_in([[(x0 - 2, top + (base - top) * f + rr.uniform(-1, 1)), (x1 + 2, top + (base - top) * f + rr.uniform(-1, 1))]
                      for f in (.25, .45, .62, .8)], poly))
    for k in range(3):  # surf breaking at the foot
        cv.line([(x0 - 3 - k * 2 + u, base + 1 + k * 1.6 - .8 * math.sin(u * .9)) for u in range(0, int(wb + 6 + k * 4), 2)])
    return crown


def _cloud(cv, ccx, ccy, cw, ch, rng):
    """A cumulus bank: white puffs over ruled sky, a contour on the lit top, hatched underside."""
    bumps = [(ccx + cw * rng.uniform(-.38, .38), ch * rng.uniform(.5, 1.)) for _ in range(4)]
    bumps.append((ccx, ch))
    top = []
    for u in range(25):
        x = ccx - cw / 2 + cw * u / 24
        hgt = max(b * max(0., 1 - ((x - bx) / (cw * .22)) ** 2) ** .5 for bx, b in bumps)
        hgt = max(hgt, ch * .18 * math.sin(PI * u / 24))
        top.append((x, ccy - hgt))
    cl = top + [(ccx + cw / 2, ccy + ch * .12), (ccx - cw / 2, ccy + ch * .12)]
    cv.obj([cl], 0)
    cv.line(top)
    cv.hair(_offset(top, -1.2))
    cv.hair(C.hatch_poly(cl, 0, 3, .4))
    cv.hair(_clip_y(C.hatch_poly(cl, 0, 3, 1.9), ccy - ch * .3, ccy + ch))
    cv.hair(_clip_y(C.hatch_poly(cl, -30, 2), ccy - ch * .05, ccy + ch))



# ----------------------------------------------------------------------------------------------
# burin grounds: the dawn sky and the sea, laid in flowing lines (no ruled filler)
# ----------------------------------------------------------------------------------------------

def _dawn_sky(cv, X, Y, W, hz, sx, sy, sr, puffs, rays=24):
    """Lines that bow up over each cloud bank, darkest at the zenith, swelling in the shadowed
    rays and breaking into pure light round the sun."""
    g = bumps([(cx, cy + ch * .3, cw * .45, ch * .9, ch * .35) for cx, cy, cw, ch in puffs])

    def tone(x, y):
        t = (y - Y) / max(1., hz - Y)
        d = math.hypot(x - sx, (y - sy) * 1.3) / max(sr, 1.)
        v = .78 - .42 * t
        if d < 1.7:
            return 0.
        if d < 5.:
            v *= (d - 1.7) / 3.3
        a = math.atan2(y - sy, x - sx)
        if (a / PI * rays) % 2. < 1.:
            v += .22 * max(0., 1 - d / 14)
        return min(1., v)
    cv.obj([[(X - 4, Y - 4), (X + W + 4, Y - 4), (X + W + 4, hz + 1), (X - 4, hz + 1)]], 0)
    burin_field(cv, X - 6, X + W + 6, Y - 6, hz - .5, g, tone, 2. if hz - Y > 40 else 1.5, cross=.86)


def _sea_lines(cv, X, Y, W, H, hz, sx, sr, rng):
    """Wavering water lines tight at the horizon, opening toward us, broken by the glitter path."""
    cv.obj([[(X - 4, hz), (X + W + 4, hz), (X + W + 4, Y + H + 4), (X - 4, Y + H + 4)]], 0)
    D = max(1., Y + H - hz)
    ph = rng.random() * 6

    def g(x, y):
        t = (y - hz) / D
        return (.3 + 1.3 * t) * math.sin(x / (8 + 16 * t) + y * .7 + ph)

    def tone(x, y):
        t = (y - hz) / D
        gl = sr * (.8 + 2.4 * t)
        if abs(x - sx) < gl and ((x * .37 + y * 1.3) % 4.) < 1.7:
            return 0.
        return .32 + .5 * t
    burin_field(cv, X - 6, X + W + 6, hz + .6, Y + H + 4, g, tone, 1.5 if D < 60 else 2.)
    cv.heavy([(X - 4, hz), (X + W + 4, hz)])


def scene(X, Y, W, H, seed, detail=1.):
    """The Oregon coast at dawn inside the box (X, Y, W, H) (the caller clips it)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    hz = Y + H * .44
    sx, sy = X + W * (.69 + .02 * rng.random()), hz - H * .15
    sr = min(W, H) * .065
    puffs = [(X + W * (.42 + .36 * j + rng.uniform(-.03, .03)), Y + H * (.17 + .07 * j), W * (.28 - .06 * j), H * .09) for j in range(2)]
    _dawn_sky(cv, X, Y, W, hz, sx, sy, sr, puffs)
    for cx, cy, cw, ch in puffs:
        cloud(cv, cx, cy, cw, ch * 1.4, rng, (.8, -.6))
    for j in range(4):  # gulls
        gx = X + W * rng.uniform(.4, .86)
        gy = Y + H * rng.uniform(.27, .37)
        gg = 1.8 + rng.random() * 1.4
        cv.line([(gx - gg, gy - gg * .2), (gx - gg * .45, gy - gg * .55), (gx, gy)])
        cv.line([(gx, gy), (gx + gg * .45, gy - gg * .55), (gx + gg, gy - gg * .2)])
    # the sun, half risen: a white disc ringed in fine lines (the light is the paper)
    for k, f in enumerate((1., 1.18, 1.36)):
        (cv.line if k == 0 else cv.hair)(C._ell_pts(sx, sy, sr * f, sr * f, 40))
    # the far headland across the water, modelled in contour lines
    fx0 = X + W * .74
    far = [(fx0, hz)] + [(fx0 + (X + W + 4 - fx0) * (i / 16),
                          hz - H * .06 * math.sin(PI * min(1, i / 16 * 1.3) * .5) ** 1.4 - H * .01 * math.sin(i / 16 * 9))
                         for i in range(1, 17)] + [(X + W + 4, hz + 1)]
    cv.obj([far], .5)
    cv.hair([[(x, y + d) for x, y in far[1:-1]] for d in (1.5, 3., 4.5)])
    _sea_lines(cv, X, Y, W, H, hz, sx, sr, rng)
    return _coast_rest(cv, X, Y, W, H, hz, rng, seed, detail)


def _coast_rest(cv, X, Y, W, H, hz, rng, seed, detail):
    """Stacks, the headland with Highway 101 and its arch, the breaker and the rescue."""
    # Secret Beach: sea stacks and the natural arch standing in the swell
    base = hz + H * .13
    T1 = _stack(cv, rng, X + W * .58, W * .085, W * .05, hz - H * .2, base)
    _stack(cv, rng, X + W * .655, W * .06, W * .04, hz - H * .085, base + 1)
    _stack(cv, rng, X + W * .5, W * .045, W * .03, hz - H * .03, base - H * .02)
    _stack(cv, rng, X + W * .8, W * .16, W * .12, hz - H * .1, base + H * .025, (X + W * .765, X + W * .835, hz + H * .005))
    tyy = min(p[1] for p in T1) + 1.
    _heron(cv, X + W * .59, tyy, max(9., H * .07))            # Easter egg: Parker's heron
    _conifer(cv, X + W * .567, tyy + 1.5, H * .04)

    # the near headland: firs on the ridge, a gorge, Highway 101 benched into the cliff
    hx1 = X + W * .52
    g0, g1 = X + W * .17, X + W * .25
    ridge = []
    for i in range(41):
        t = i / 40
        xx = X - 3 + (hx1 + 3 - X) * t
        yy = Y + H * (.27 + .02 * math.sin(t * 7 + 1)) + (hz + H * .02 - Y - H * .27) * max(0, (t - .55) / .45) ** 1.5
        ridge.append((xx, yy))
    shore = lambda x: hz + H * (.27 - .2 * max(0., (x - X) / (hx1 - X)) ** 1.3)
    sh_pts = [(X - 3 + (hx1 + 6 - X) * u / 20, shore(X - 3 + (hx1 + 6 - X) * u / 20)) for u in range(21)]
    gtop = _poly_y(ridge, g0) + H * .045
    gorge = [(g0 - 1, gtop - H * .02), (g1 + 1, gtop - H * .02), (g1 + 4, shore(g1)), (g0 - 4, shore(g0))]
    cv.obj([gorge], 0)
    burin_field(cv, g0 - 5, g1 + 5, gtop - H * .03, shore(g0) + 2, lambda x, y: 3 * math.cos((x - g0) / (g1 - g0) * PI),
                lambda x, y: .62, 1.5, ok=_ins_fast(gorge))
    gx = (g0 + g1) / 2
    cv.hair([[(gx - 1.2 + j * .8, gtop + H * .1), (gx - 1.5 + j * 1., shore(gx))] for j in range(4)])
    left_poly = [p for p in ridge if p[0] <= g0] + [(g0, gtop)] + [p for p in sh_pts if p[0] <= g0][::-1]
    right_poly = ([(g1, gtop)] + [p for p in ridge if p[0] >= g1] + [(hx1 + 6, shore(hx1 + 6))] +
                  [p for p in sh_pts if p[0] >= g1][::-1])
    for poly in (left_poly, right_poly):
        cv.obj([poly], 1.)
        top_y = min(p[1] for p in poly)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        # contour lines that follow the ridge down the forested slope, darkening into the cliff
        r0y = ridge[0][1]
        rf = _prof_fast(ridge)
        burin_field(cv, min(xs) - 2, max(xs) + 2, top_y - 2, max(ys) + 2,
                    lambda x, y: r0y - (rf(x) or r0y),
                    lambda x, y: min(1., .3 + .75 * (y - (rf(x) or r0y)) / max(1., hz - top_y) + .1 * math.sin(x * .7)),
                    1.5 if H < 120 else 2., step=3., ok=_ins_fast(poly), cross=.8)
        for j in range(int((max(xs) - min(xs)) / 7)):  # fissures in the cliff
            fx = min(xs) + 3 + j * 7 + rng.uniform(-2, 2)
            fy = shore(fx) - H * rng.uniform(.04, .1)
            cv.line(_clip_in([[(fx, fy), (fx + rng.uniform(-1, 1), shore(fx) - 1)]], poly))
    # surf along the foot of the cliffs
    for kk in range(3):
        cv.line([(x, y + 1.2 + kk * 1.7 + .6 * math.sin(x * .8 + kk)) for x, y in sh_pts])
    xx = X - 1
    while xx < hx1 - W * .02:
        if not (g0 - 3 < xx < g1 + 3):
            ry = _poly_y(ridge, xx)
            if ry is not None:
                _conifer(cv, xx, ry + 2, H * rng.uniform(.05, .08) * (1 if xx < hx1 - W * .12 else .7))
        xx += 3. + rng.random() * 1.5

    def _ry(x):
        return (_poly_y(ridge, x) or hz) + H * .055

    def road_y(x):
        if g0 - 4 <= x <= g1 + 4:
            a, b = _ry(g0 - 4), _ry(g1 + 4)
            return a + (b - a) * (x - g0 + 4) / (g1 - g0 + 8)
        return _ry(x)

    rp = []
    xx = X - 3
    while xx <= hx1 - W * .04:
        rp.append((xx, road_y(xx)))
        xx += 1.5
    Rd = C._Rib(rp, [2.] * len(rp), [2.] * len(rp))
    cv.obj([Rd.outline()], 1.)
    for c in Rd.contour(0, 0, 1):
        cv.hair([c[j:j + 3] for j in range(0, len(c) - 2, 5)])
    cv.hair(Rd.contour(-.75, 0, 1))
    # the concrete deck arch over the gorge (Conde McCullough's coast bridges)
    ax0, ax1 = g0 - 4, g1 + 4
    span = ax1 - ax0
    by0, by1 = road_y(ax0), road_y(ax1)
    rise = min(H * .1, span * .55)
    deck = [(ax0 + span * u / 24, by0 + 2. + (by1 - by0) * u / 24) for u in range(25)]
    arc = [(ax0 + span * u / 24, by0 + 4 + rise - rise * math.sin(PI * u / 24) ** .7 + (by1 - by0) * u / 24) for u in range(25)]
    cv.obj([[(p[0], p[1] - 4.4) for p in deck] + arc[::-1]], 1.)
    cv.heavy(arc)
    cv.line([(p[0], p[1] + 1.2) for p in arc])
    cv.heavy(deck)
    cv.hair([(p[0], p[1] - 4.4) for p in deck])
    for u in range(1, 24):
        if u % 2 == 0:
            cv.hair([(deck[u][0], deck[u][1] + .6), (arc[u][0], arc[u][1] - .6)])
        cv.hair([(deck[u][0], deck[u][1] - 4.4), (deck[u][0], deck[u][1] - 2.4)])

    # the breaker, curling over into a volute and breaking into acanthus foam
    r = min(W, H) * .15
    _wave(cv, X + W * .74, Y + H * .73, r, Y + H * .93, X - 3, X + W + 3, Y + H + 3,
          random.Random(seed + 7), 5 if detail >= 1 else 4)
    # the rescue, riding the swell: a life ring tossed beside a raised arm
    lr_x, lr_y = X + W * .16, Y + H * .84
    _life_ring(cv, lr_x, lr_y, max(6.5, W * .045))
    _swimmer(cv, lr_x + W * .09, lr_y + 1, max(5., H * .045))

    return cv.svg()


def mini(X, Y, W, H, seed=0):
    """The band medallion: dawn sun, the sea stack with the heron, burin sky and sea."""
    rng = random.Random(seed)
    cv = C.Canvas()
    hz = Y + H * .6
    sx, sy, sr = X + W * .66, hz, H * .2
    _dawn_sky(cv, X, Y, W, hz, sx, sy, sr, [(X + W * .3, Y + H * .25, W * .3, H * .18)], 16)
    for k, f in enumerate((1., 1.25)):
        (cv.line if k == 0 else cv.hair)(C._ell_pts(sx, sy, sr * f, sr * f, 30, PI, TAU))
    _sea_lines(cv, X, Y, W, H, hz, sx, sr, rng)
    cr = _stack(cv, rng, X + W * .28, W * .15, W * .09, hz - H * .4, hz + 2)
    _stack(cv, rng, X + W * .4, W * .07, W * .045, hz - H * .16, hz + 2)
    _heron(cv, X + W * .29, min(p[1] for p in cr) + .8, H * .24)
    return cv.svg()


def _century_tablet(tx, ty, tw, th):
    """The highway's century: 101 winding from MCMXXVI to MMXXVI past ten decade mileposts, the
    shield at the midpoint."""
    cv = Canvas()
    cap = min(th * .2, 8.)
    lw = text_width("MCMXXVI", cap)
    r0, r1 = tx + lw + 6, tx + tw - lw - 6
    my = ty + th * .55
    road = [(r0 + (r1 - r0) * i / 80, my + th * .14 * math.sin(i / 80 * TAU * 2.5)) for i in range(81)]
    R = C._Rib(road, [2.4] * 81, [2.4] * 81)
    # the land either side, cut in light contour lines that follow the road
    burin_field(cv, r0 - 2, r1 + 2, ty + 2, ty + th - 2, lambda x, y: th * .14 * math.sin((x - r0) / (r1 - r0) * TAU * 2.5),
                lambda x, y: .25 + .3 * abs(y - my) / th, 2.)
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(0, 0, 1))
    for d in range(11):
        x = r0 + (r1 - r0) * d / 10
        y = my + th * .14 * math.sin(d / 10 * TAU * 2.5) - 5
        post = [(x - 1.2, y - 4), (x + 1.2, y - 4), (x + 1.2, y + 1.5), (x - 1.2, y + 1.5)]
        cv.obj([post], 1.)
    o = [cv.svg()]
    pl = letters("MCMXXVI", tx + lw / 2, my, cap) + letters("MMXXVI", tx + tw - lw / 2, my, cap)
    o.append(letters_svg(pl))
    s = min(th * .3, 14.)
    o.append(shield_101(tx + tw / 2, ty + th * .42, s))
    return "".join(o)


def _crest(cx, base, size):
    s = size * .42
    return shield_101(cx, base - s * 1.15, s)


def egg_arch(cv, cx, cy, r):
    """A McCullough concrete deck arch over a gorge (the coast highway's own bridges)."""
    cv.obj([ell(cx, cy, r * .98, r * .98, 32)[:-1]], 0)
    dk = cy - r * .22
    a = [(cx - r * .8 + r * 1.6 * u / 20, dk + r * .75 - r * .7 * math.sin(PI * u / 20) ** .8) for u in range(21)]
    cv.obj([[(cx - r * .95, dk - r * .12), (cx + r * .95, dk - r * .12), (cx + r * .95, dk + r * .08)] + a[::-1] + [(cx - r * .95, dk + r * .08)]], 1.)
    cv.heavy(a)
    cv.heavy([(cx - r * .95, dk), (cx + r * .95, dk)])
    for u in range(2, 19, 2):
        cv.line([(a[u][0], dk + .5), (a[u][0], a[u][1] - .6)])
    for k in range(3):
        y = cy + r * (.62 + .14 * k)
        cv.line([(cx - r, y), (cx + r, y)])


EGGS["arch"] = egg_arch


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 11

    def sc(x, y, sw, sh, clip, mode):
        if sh < 90:
            return mini(x, y, sw, sh, seed)
        return scene(x, y, sw, sh, seed, 1. if sh > 200 else .8)

    # planned form: a small tailpiece, about 8% of the sheet, an oval (a sunrise)
    return free_vignette(w, h, ctx, sc, dict(form="oval", pid="de", seed=seed, egg="dog", banner="HIGHWAY CI · A CENTURY"))
