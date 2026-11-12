"""sports-02 (Portland Timbers). King-tier plate: the scene sits in an inlaid medallion ringed in
beading - a ball, struck from the left, bulges the top corner of a goal net set before a stand of
Douglas firs and Mt. Hood under a burin sky; two cut log slabs (Timber Joey's slab for every goal;
their number follows the last score) lie in the foreground. Fine scroll grown from one stem source
packs the stippled black ground; corner roundels hold a Douglas fir and the ball; the ribbon reads
PORTLAND TIMBERS and the pedestal tablet carries the last result, read from the page.
Easter egg: a tiny Timbers Army snare with crossed drumsticks hides in the grass."""
# ==== studio kit (batch 3): grandmaster acanthus, engraved black grounds, mouldings, lettering ====
# Shared verbatim by this batch's plates (the house rule forbids a new shared module, so each plate
# carries its own copy). Pure standard library, deterministic.
import math
import math as _m
import random
import random as _r
import engraving_codex as C

PI = _m.pi
TAU = 2 * PI
_n, _d, _ell = C._n, C._d, C._ell_pts
E = C._ell_pts
_LIGHT = (-.62, -.78)          # light from the upper left


def _f1(v):
    return f"{v:.1f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))


# ---------------------------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------------------------

def euler(x, y, ang, L, kf, n=28):
    """Centre line from (x, y) heading ang (rad), length L, curvature kf(u) (rad/px).
    Returns [(x, y, heading)]."""
    out = [(x, y, ang)]
    ds = L / n
    th = ang
    for i in range(n):
        u = (i + .5) / n
        k = kf(u)
        thm = th + k * ds * .5
        x += _m.cos(thm) * ds
        y += _m.sin(thm) * ds
        th += k * ds
        out.append((x, y, th))
    return out


def offs(sp, wf, s):
    """Offset of a centre line: point at s * wf(u) along the left normal."""
    n = len(sp) - 1
    return [(p[0] - _m.sin(p[2]) * s * wf(i / n), p[1] + _m.cos(p[2]) * s * wf(i / n)) for i, p in enumerate(sp)]


def plen(pl):
    return sum(_m.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pl, pl[1:]))


def resample(pl, step):
    out = [pl[0]]
    acc = 0.
    for a, b in zip(pl, pl[1:]):
        L = _m.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / step + .5))
        for j in range(1, k + 1):
            out.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    return out


def pt_in(px, py, poly):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def clip_in(lines, poly, keep_in=True):
    out = []
    for pl in lines:
        cur = []
        for p in resample(pl, 1.5):
            if pt_in(p[0], p[1], poly) == keep_in:
                cur.append(p)
            else:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
        if len(cur) > 1:
            out.append(cur)
    return out


def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def with_heading(pl):
    out = []
    for i, p in enumerate(pl):
        a = pl[max(0, i - 1)]
        b = pl[min(len(pl) - 1, i + 1)]
        out.append((p[0], p[1], _m.atan2(b[1] - a[1], b[0] - a[0])))
    return out


def sstep(e0, e1, x):
    if x <= e0:
        return 0.
    if x >= e1:
        return 1.
    t = (x - e0) / (e1 - e0)
    return t * t * (3 - 2 * t)


def shadow(cv, poly, dx=1., dy=1.):
    """A cast-shadow fringe: the outline shifted down-right, under the object painted next."""
    if not SHADOW[0]:
        return
    cv.obj([], 0)
    cv.heavy([(x + dx, y + dy) for x, y in poly + [poly[0]]])


# ---------------------------------------------------------------------------------------------
# a layered canvas: same API as engraving_codex.Canvas, but each object's white fill and outline go
# out together in painter's-order depth layers (one path per layer), and the hatching is clipped by
# a 1 px occlusion raster and laid on top: about half the bytes of fill + outline + clip
# ---------------------------------------------------------------------------------------------

def _clip_runs(pl, mask, x0, y0, W, H, out, step=1.6):
    run = []
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L_ = abs(dx) + abs(dy)
        if L_ > step:
            k = int(L_ / step)
            for j in range(1, k + 1):
                t = j / (k + 1)
                pts.append((px + dx * t, py + dy * t))
        pts.append(q)
        px, py = q
    for (x, y) in pts:
        xi, yi = int(x - x0), int(y - y0)
        if 0 <= xi < W and 0 <= yi < H and mask[yi][xi]:
            if len(run) > 1:
                out.append(run)
            run = []
        else:
            run.append((x, y))
    if len(run) > 1:
        out.append(run)


def _thin(pts, tol):
    """O(n) simplification: drop a point while the chord from the last kept point stays within tol
    of every point it skips (checked against the newest skipped point only)."""
    n = len(pts)
    if n < 3:
        return pts
    out = [pts[0]]
    ax, ay = pts[0]
    for i in range(1, n - 1):
        bx, by = pts[i + 1]
        px, py = pts[i]
        dx, dy = bx - ax, by - ay
        L = abs(dx) + abs(dy)
        if L < 1e-9 or abs((px - ax) * dy - (py - ay) * dx) > tol * (dx * dx + dy * dy) ** .5:
            out.append(pts[i])
            ax, ay = px, py
    out.append(pts[-1])
    return out


class _Pen:
    """Quarter-px relative path data (as engraving_codex._Pen) with the O(n) thinning."""

    def __init__(self):
        self.o = []
        self.cur = None

    def add(self, pts, close=False, tol=.3):
        if len(pts) < 2:
            return
        if tol:
            pts = _thin(pts, tol)
        o = self.o
        X = [int(round(p[0] * 4)) for p in pts]
        Y = [int(round(p[1] * 4)) for p in pts]
        if self.cur is None:
            o.append(f"M{X[0]} {Y[0]}")
        else:
            dx, dy = X[0] - self.cur[0], Y[0] - self.cur[1]
            o.append(f"m{dx}{'' if dy < 0 else ' '}{dy}")
        seg = []
        for i in range(1, len(X)):
            dx, dy = X[i] - X[i - 1], Y[i] - Y[i - 1]
            if dx or dy:
                seg.append(f"{dx}{'' if dy < 0 else ' '}{dy}")
        o.append("l" + (" ".join(seg).replace(" -", "-") if seg else "0 0"))
        if close:
            o.append("z")
            self.cur = (X[0], Y[0])
        else:
            self.cur = (X[-1], Y[-1])

    def d(self):
        return "".join(self.o)


class Canvas(C.Canvas):
    def svg(self, max_layers=90):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        for o in self.objs:
            for lines in o[2].values():
                for pl in lines:
                    for p in pl[::4]:
                        xs.append(p[0])
                        ys.append(p[1])
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for w, lines in strokes.items():
                for pl in lines:
                    _clip_runs(pl, mask, x0, y0, W, H, out[w])
            for poly in polys:
                C._fill_mask(poly, mask, x0, y0, W, H)
        # depth layers by bbox overlap
        G = {}
        depth = []
        for k, (polys, ow, _) in enumerate(self.objs):
            if not polys:
                depth.append(-1)
                continue
            bx0 = min(p[0] for q in polys for p in q) - 1
            bx1 = max(p[0] for q in polys for p in q) + 1
            by0 = min(p[1] for q in polys for p in q) - 1
            by1 = max(p[1] for q in polys for p in q) + 1
            dmax = -1
            cells = [(i, j) for i in range(int(bx0 // 16), int(bx1 // 16) + 1) for j in range(int(by0 // 16), int(by1 // 16) + 1)]
            seen = set()
            for c in cells:
                for (j, b) in G.get(c, ()):
                    if j in seen:
                        continue
                    seen.add(j)
                    if b[0] < bx1 and bx0 < b[2] and b[1] < by1 and by0 < b[3] and depth[j] > dmax:
                        dmax = depth[j]
            dk = min(max_layers - 1, dmax + 1)
            depth.append(dk)
            for c in cells:
                G.setdefault(c, []).append((k, (bx0, by0, bx1, by1)))
        layers = {}
        for k, (polys, ow, _) in enumerate(self.objs):
            if depth[k] < 0:
                continue
            layers.setdefault((depth[k], float(ow)), []).append(polys)
        res = []
        T = C._QT
        for (dk, ow) in sorted(layers):
            pen = _Pen()
            for polys in layers[(dk, ow)]:
                for poly in polys:
                    pen.add(poly if C._area(poly) >= 0 else poly[::-1], True, .3)
            sw = f' stroke="#000" stroke-width="{_n(ow * 4)}"' if ow else ' stroke="none"'
            res.append(f'<path{T} d="{pen.d()}" fill="#fff"{sw}/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _Pen()
                for pl in out[w]:
                    pen.add(pl, False, .3)
                res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_n(w * 4)}"/>')
        return "".join(res)


SHADOW = [False]


# ---------------------------------------------------------------------------------------------
# the engraved black ground: solid #000 cut with white stipple, tendrils, florets and sparkles
# (white work >= 1 CSS px, every 10 x 10 of black carries a cut)
# ---------------------------------------------------------------------------------------------

def _stip_tile(seed, T=36):
    rng = _r.Random(seed)
    o = []
    pts = []
    tries = 0
    while len(pts) < T * T // 15 and tries < 6000:
        tries += 1
        x, y = rng.uniform(0, T), rng.uniform(0, T)
        if all(min(abs(x - a), T - abs(x - a)) ** 2 + min(abs(y - b), T - abs(y - b)) ** 2 > 5.5 for a, b in pts):
            pts.append((x, y))
    for x, y in pts:
        o.append(f"M{_f1(round(x * 2) / 2)} {_f1(round(y * 2) / 2)}h0")
    return "".join(o)


def ground_defs(seed=0):
    """Pattern defs for the engraved ground (stipple); put once in the svg."""
    d = _stip_tile(seed)
    return (f'<defs><pattern id="gkS{seed % 97}" width="36" height="36" patternUnits="userSpaceOnUse">'
            f'<path d="{d}" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></pattern></defs>')


def tendril_ground(x, y, w, h, seed=0, dens=1., avoid=None):
    """White-line background foliage for a black ground: little curling tendrils with leaflets,
    five-dot florets and four-point sparkle cuts. Returns svg (white strokes 1 px)."""
    rng = _r.Random(seed * 7 + 3)
    L1, Ld = [], []
    n = int(w * h / 900 * dens) + 2
    cell = max(14., (w * h / n) ** .5)
    gx = max(1, int(w / cell))
    gy = max(1, int(h / cell))
    for j in range(gy):
        for i in range(gx):
            cx = x + (i + rng.uniform(.15, .85)) * w / gx
            cy = y + (j + rng.uniform(.15, .85)) * h / gy
            if avoid and avoid(cx, cy):
                continue
            k = rng.random()
            if k < .55:
                # a tendril: an arc winding into a curl, with one or two leaflets
                a = rng.uniform(0, TAU)
                L = cell * rng.uniform(.55, .9)
                sg = rng.choice((-1, 1))
                sp = euler(cx, cy, a, L, lambda u, sg=sg, L=L: sg * (1.5 + 9 * u ** 3) / L, 14)
                L1.append([(p[0], p[1]) for p in sp])
                for f in (.35, .6)[:rng.randint(1, 2)]:
                    p = sp[int(f * 14)]
                    b = p[2] - sg * 1.0
                    ll = cell * .22
                    q = (p[0] + _m.cos(b) * ll, p[1] + _m.sin(b) * ll)
                    mid = ((p[0] + q[0]) / 2 - _m.sin(b) * ll * .3, (p[1] + q[1]) / 2 + _m.cos(b) * ll * .3)
                    L1.append([(p[0], p[1]), mid, q])
            elif k < .78:
                rr = rng.uniform(1.8, 2.6)
                a0 = rng.uniform(0, TAU)
                for t in range(5):
                    Ld.append((cx + rr * _m.cos(a0 + TAU * t / 5), cy + rr * _m.sin(a0 + TAU * t / 5)))
            else:
                s = rng.uniform(1.8, 3.2)
                L1.append([(cx - s, cy), (cx + s, cy)])
                L1.append([(cx, cy - s), (cx, cy + s)])
    p = C._Pen()
    for pl in L1:
        p.add(pl, False, .3)
    o = ""
    if p.o:
        o += f'<path transform="scale(.25)" d="{p.d()}" fill="none" stroke="#fff" stroke-width="4"/>'
    if Ld:
        o += '<path d="' + "".join(f"M{_f1(round(a, 1))} {_f1(round(b, 1))}h0" for a, b in Ld) + \
             '" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>'
    return o


def black_ground(shape, seed=0, dens=1., bbox=None, avoid=None):
    """Solid black cut-away ground, engraved: stipple pattern + white tendrils. shape: (x, y, w, h)
    or a polygon (then pass bbox). Needs ground_defs(seed) in the document."""
    if isinstance(shape, tuple):
        x, y, w, h = shape
        d = f"M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z"
    else:
        d = _d(shape, True, 0)
        xs = [p[0] for p in shape]
        ys = [p[1] for p in shape]
        x, y, w, h = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    cid = C._uid("bg", d[:60], seed)
    return (f'<path d="{d}" fill="#000" stroke="none"/><path d="{d}" fill="url(#gkS{seed % 97})" stroke="none"/>'
            f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">'
            + tendril_ground(x, y, w, h, seed, dens, avoid) + '</g>')


# ---------------------------------------------------------------------------------------------
# the modelled acanthus leaf: a carved midrib blade over lobed leaflets; every leaflet has its
# secondary vein and bulino shading on its shadow half that runs dark into the root; the tip turns
# over and its underside is cut dark; a cast shadow fringe sits under it
# ---------------------------------------------------------------------------------------------

def _shade_side(ang, sgn):
    """True when the side at normal sgn of a direction ang faces away from the light."""
    nx, ny = -_m.sin(ang) * sgn, _m.cos(ang) * sgn
    return nx * _LIGHT[0] + ny * _LIGHT[1] < 0


def _flat_leaf(L, W, lobes, rng, inner_lobes=1):
    """Leaf outline in flat (U along, V across; +V outer) px coordinates: rounded scalloped lobes
    with sharp notches (the oak-and-acanthus leaf of fine English scroll), plus the lobe table."""
    def E(u):
        return W * _m.sin(PI * min(1., u ** .8 * .97 + .015)) ** .6 * (1 - .15 * u)
    ph = rng.uniform(.0, .25)
    n_o = lobes + .5
    tab = []
    edge = []
    M_ = max(28, int(L / 1.2))
    for i in range(M_ + 1):
        u = i / M_
        t = (u * n_o + ph) % 1.
        sc = .58 + .42 * _m.sin(PI * t) ** .45
        # lean the scallop forward a little
        edge.append(((u + .02 * _m.sin(PI * t)) * L, E(u) * sc))
    edge[-1] = (L, 0.)
    k0 = -ph
    while k0 < n_o:
        ua, ub = max(0., k0 / n_o), min(1., (k0 + 1) / n_o)
        if ub - ua > .05:
            tab.append((ua, ub, 1))
        k0 += 1
    inner = []
    n_i = inner_lobes + .5
    for i in range(M_, -1, -1):
        u = i / M_
        t = (u * n_i + .3) % 1.
        sc = .7 + .3 * _m.sin(PI * t) ** .45
        inner.append((u * L, -E(u) * .62 * sc))

    def iw(u):
        t = (u * n_i + .3) % 1.
        return E(u) * .62 * (.7 + .3 * _m.sin(PI * t) ** .45)

    def ow(u):
        t = (u * n_o + ph) % 1.
        return E(u) * (.58 + .42 * _m.sin(PI * t) ** .45)
    return edge + inner[1:], tab, E, iw, ow


def acanthus_leaf(cv, x, y, ang, L, W=None, bend=.5, curl=2.4, lobes=3, seed=0, turn=True, cast=True,
                  pitch=1.5, inner_lobes=1, depth=None):
    """A modelled acanthus leaf from (x, y) heading ang (rad), length L, max half-width W, bending by
    `bend` rad and rolling `curl` more at the tip (signs: +1 turns clockwise on screen). The convex
    margin is cut into lobes of convex-backed, forward-pointing fingers; the concave half is cut dark
    in bulino along the form with a cross-hatch layered in the deep shadow at the root; each lobe is
    shaded from its notch and carries its vein; the midrib is a carved groove. Returns (spine, poly)."""
    rng = _r.Random(seed)
    W = W or L * .4
    tot = bend + curl
    sg = 1 if tot >= 0 else -1
    N = max(10, min(40, int(L / 1.5)))
    sp = euler(x, y, ang, L, lambda u: (bend + curl * 4 * u ** 3) / L, N)
    flat, tab, E, iw, ow = _flat_leaf(L, W, lobes, rng, inner_lobes)

    def M(p):
        U, V = p
        f = U / L * N
        i = min(N - 1, max(0, int(f)))
        t = min(1., max(0., f - i))
        a, b = sp[i], sp[i + 1]
        px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        th = a[2] + (b[2] - a[2]) * t
        return (px + _m.sin(th) * sg * V, py - _m.cos(th) * sg * V)
    poly = [M(p) for p in flat]
    cv.obj([poly], 1. if L > 16 else .5)
    SX = [p[0] for p in sp]
    SY = [p[1] for p in sp]
    QX = [_m.sin(p[2]) * sg for p in sp]
    QY = [-_m.cos(p[2]) * sg for p in sp]
    IWs = [iw(i / N) for i in range(N + 1)]
    OWs = [ow(i / N) for i in range(N + 1)]
    # concave half: bulino along the form, fading toward the tip
    k = 1
    while k * pitch < W * .55:
        V = -k * pitch
        iend = int(N * (.94 - .35 * (k * pitch / (W * .55)) ** 1.5))
        seg = []
        lim = k * pitch + .7
        for i in range(iend + 1):
            if IWs[i] > lim:
                seg.append((SX[i] + QX[i] * V, SY[i] + QY[i] * V))
            elif len(seg) > 1:
                cv.hair(seg)
                seg = []
            else:
                seg = []
        if len(seg) > 1:
            cv.hair(seg)
        k += 1
    # convex half: a cut or two along each scallop's shaded root, the lit margin left bright
    k = 1
    i0, i1 = int(N * .06) + 1, int(N * .8)
    while k * pitch < W * .45 and k <= 2:
        V = k * pitch + .3
        lim = V + 1.6 * (1 + k)
        seg = []
        for i in range(i0, i1 + 1):
            if OWs[i] > lim:
                seg.append((SX[i] + QX[i] * V, SY[i] + QY[i] * V))
            elif len(seg) > 1:
                cv.hair(seg)
                seg = []
            else:
                seg = []
        if len(seg) > 1:
            cv.hair(seg)
        k += 1
    if L >= 18:
        for ua, ub, kk in tab:
            s0 = ub - ua
            um = ua + s0 * .55
            cv.hair([M(((ua + s0 * .1) * L, .5)), M(((ua + s0 * .32) * L, E(ua + s0 * .32) * .42)), M((um * L, E(um) * .72))])
    i9 = int(N * .92)
    cv.line([(SX[i], SY[i]) for i in range(1, i9)])
    if L > 14:
        cv.hair([(SX[i] + QX[i] * 1.2, SY[i] + QY[i] * 1.2) for i in range(2, int(N * .78))])
    return sp, poly


# ---------------------------------------------------------------------------------------------
# the volute: a round-carved stem winding into a tight spiral eye, sheathed by acanthus that
# springs from the outer turn and rolls over toward the eye
# ---------------------------------------------------------------------------------------------

def k_spiral(cx, cy, R, a0, turns=1.6, dirn=1, rmin=.1, n=None):
    """Logarithmic spiral from radius R at angle a0 (rad) inward over `turns` to R*rmin."""
    n = n or int(30 + 24 * turns)
    k = _m.log(1 / rmin) / (turns * TAU)
    pts = []
    for i in range(n + 1):
        t = turns * TAU * i / n
        r = R * _m.exp(-k * t)
        a = a0 + dirn * t
        pts.append((cx + r * _m.cos(a), cy + r * _m.sin(a)))
    return pts


def k_stem(cv, pl, w0, w1, dirn=1, cast=True, lines=3):
    """A round-carved stem along polyline pl tapering w0 -> w1 (full widths); shaded on the side
    dirn (the inside of its curl)."""
    sp = with_heading(resample(pl, 2.))
    n = len(sp) - 1

    def wf(u):
        return (w0 + (w1 - w0) * u) / 2
    left, right = offs(sp, wf, 1), offs(sp, wf, -1)
    poly = left + right[::-1]
    if cast:
        shadow(cv, poly)
    cv.obj([poly], 1.)
    for k in range(1, lines + 1):
        f = 1 - k * .22
        seg = [q for i, q in enumerate(offs(sp, lambda u: wf(u) * f, dirn)) if wf(i / n) * (1 - f) * 2 > 1.4 * k ** .5]
        if len(seg) > 1:
            cv.hair(seg)
    # a highlight hairline on the lit side
    seg = offs(sp, lambda u: wf(u) * .5, -dirn)
    cv.hair([q for i, q in enumerate(seg) if wf(i / n) > 2.2])
    return sp


def k_volute(cv, cx, cy, R, a0, turns=1.55, dirn=1, seed=0, leaves=3, wstem=None, eye=True, tail=None,
           leaf_scale=1., flare=True):
    """A complete scroll. a0 (rad) is where the outer turn starts, dirn +1 clockwise (svg), -1 ccw.
    tail: optional polyline that leads INTO the spiral start (drawn as the same stem).
    Returns the spiral centre line."""
    rng = _r.Random(seed)
    wstem = wstem or max(2.5, R * .2)
    sp = k_spiral(cx, cy, R, a0, turns, dirn, .09)
    full = (tail[:-1] if tail else []) + sp
    # leaves first that sit behind the stem (the flare at the scroll's entry)
    if flare and R > 9:
        p = sp[0]
        tang = _m.atan2(sp[1][1] - p[1], sp[1][0] - p[0])
        acanthus_leaf(cv, p[0], p[1], tang + PI + dirn * .9, R * .9 * leaf_scale, R * .34 * leaf_scale,
                      bend=-dirn * .5, curl=-dirn * 1.6, lobes=3, seed=rng.randrange(1 << 20))
    k_stem(cv, full, wstem, max(1.5, wstem * .3), dirn)
    # the eye: the innermost turn closes on a carved boss
    if eye:
        e = sp[-1]
        er = max(1.6, R * .1)
        boss = _ell(e[0], e[1], er, er, 14)[:-1]
        cv.obj([boss], 1.)
        cv.hair(C.hatch_poly(boss, 45, 1.5, .3))
        cv.obj([_ell(e[0] - er * .25, e[1] - er * .25, er * .35, er * .35, 8)[:-1]], 0)
    # sheathing leaves on the outer turn, springing from the stem and rolling toward the eye
    m = len(sp)
    for j in range(leaves):
        f = .04 + .33 * j / max(1, leaves) + rng.uniform(-.02, .02)
        i = int(f * m)
        p = sp[i]
        q = sp[min(m - 1, i + 2)]
        tang = _m.atan2(q[1] - p[1], q[0] - p[0])
        rr = _m.hypot(p[0] - cx, p[1] - cy)
        L = rr * (1.05 - .25 * j / max(1, leaves)) * leaf_scale
        # set the root on the outer edge of the stem
        ox = cx + (p[0] - cx) * (1 + wstem * .4 / max(rr, 1))
        oy = cy + (p[1] - cy) * (1 + wstem * .4 / max(rr, 1))
        acanthus_leaf(cv, ox, oy, tang - dirn * .35, L, L * .38, bend=dirn * 1.1, curl=dirn * 1.8,
                      lobes=3 + (L > 22), seed=rng.randrange(1 << 20))
    return sp


# ---------------------------------------------------------------------------------------------
# KING TIER fine scroll: small true spirals packed over a field, every one grown from a stem that
# leaves an earlier scroll (or the source), each carrying its own small shaded leaves
# ---------------------------------------------------------------------------------------------

def small_leaf(cv, x, y, ang, L, curl=1, seed=0, lobes=None):
    """A small acanthus leaf for fine scroll (L about 5-16 px)."""
    lobes = lobes or (2 if L < 9 else 3)
    return acanthus_leaf(cv, x, y, ang, L, L * .42, bend=curl * .6, curl=curl * .9, lobes=lobes,
                         seed=seed, pitch=1.5 if L < 13 else 2., inner_lobes=1 + (L > 11))


def fine_volute(cv, cx, cy, r, a0, dirn, rng, tail=None, leaves=True, thin=None, leafk=1.):
    """One small scroll: a log spiral from radius r at angle a0 winding (dirn) to a tight eye, its
    stem continuing from `tail`; leaves spring from the outer turn and one curls into the hollow.
    Returns the attach points [(x, y, heading)] of its outer turn."""
    turns = 1.75 if r > 8 else 1.5
    sp = k_spiral(cx, cy, r, a0, turns, dirn, .1, int(18 + r * 2.2))
    w0 = thin or max(3., min(5.5, r * .24))
    pts = (tail[:-1] if tail else []) + sp
    # the leaf in the hollow (painted first: the stem passes over its root)
    if leaves and r > 6:
        i = int(len(sp) * .52)
        p = sp[i]
        a = _m.atan2(cy - p[1], cx - p[0])
        small_leaf(cv, p[0], p[1], a - dirn * .9, r * .75 * leafk, dirn, rng.randrange(1 << 20))
    sw = with_heading(resample(pts, 1.6))
    nn = len(sw) - 1
    nt = len(tail) if tail else 0
    ntot = max(1, nn)

    def wf(u):
        return max(.75, (w0 * (1 - .78 * sstep(.0, 1., u))) / 2)
    left, right = offs(sw, wf, 1), offs(sw, wf, -1)
    poly = left + right[::-1]
    shadow(cv, poly, .5, .5)
    cv.obj([poly], .5)
    cv.hair([q for i, q in enumerate(offs(sw, lambda u: wf(u) * .35, dirn)) if wf(i / ntot) > 1.3])
    # eye
    e = sp[-1]
    er = max(1.1, r * .09)
    cv.obj([_ell(e[0], e[1], er, er, 10)[:-1]], .5)
    cv.hair([(e[0] - er * .5, e[1] + er * .3), (e[0] + er * .5, e[1] - er * .3)])
    # leaves along the outer turn, pointing with the flow and rolling outward
    if leaves:
        k = 2 + (r > 11) + (r > 19)
        m = len(sp)
        for j in range(k):
            f = .03 + .5 * (j + rng.uniform(.1, .6)) / k
            i = int(f * m)
            p, q = sp[i], sp[min(m - 1, i + 1)]
            tang = _m.atan2(q[1] - p[1], q[0] - p[0])
            rr = _m.hypot(p[0] - cx, p[1] - cy)
            ox = p[0] + (p[0] - cx) / max(rr, 1) * w0 * .3
            oy = p[1] + (p[1] - cy) / max(rr, 1) * w0 * .3
            L = r * rng.uniform(1., 1.3) * (1 - .35 * f) * leafk
            small_leaf(cv, ox, oy, tang - dirn * rng.uniform(.25, .55), max(5., L), dirn * .5, rng.randrange(1 << 20))
    att = []
    for i in range(0, int(len(sp) * .42), 4):
        p, q = sp[i], sp[i + 1]
        att.append((p[0], p[1], _m.atan2(q[1] - p[1], q[0] - p[0]), dirn))
    if tail:
        for p in with_heading(tail)[1:-1:4]:
            att.append((p[0], p[1], p[2], dirn))
    return att


class Field:
    """Free-space bookkeeping: candidate points, each with its clearance to the field's edge and to
    everything placed; placing a disc lowers the clearance around it."""

    def __init__(self, x, y, w, h, inside_fn=None, step=5., edge_pad=0.):
        self.pts = []
        self.d = []
        self.grid = {}
        self.step = step
        j = 0
        yy = y + step / 2
        while yy < y + h:
            xx = x + step / 2 + (step / 2 if j % 2 else 0)
            while xx < x + w:
                if inside_fn is None or inside_fn(xx, yy):
                    dd = min(xx - x, x + w - xx, yy - y, y + h - yy) + edge_pad
                    k = len(self.pts)
                    self.pts.append((xx, yy))
                    self.d.append(dd)
                    self.grid.setdefault((int(xx // 20), int(yy // 20)), []).append(k)
                xx += step
            yy += step * .87
            j += 1

    def disc(self, cx, cy, r, reach=40.):
        g0, g1 = int((cx - r - reach) // 20), int((cx + r + reach) // 20)
        h0, h1 = int((cy - r - reach) // 20), int((cy + r + reach) // 20)
        P, D = self.pts, self.d
        for gx in range(g0, g1 + 1):
            for gy in range(h0, h1 + 1):
                for k in self.grid.get((gx, gy), ()):
                    px, py = P[k]
                    v = _m.hypot(px - cx, py - cy) - r
                    if v < D[k]:
                        D[k] = v

    def best(self, rng=None):
        if not self.d:
            return None
        k = max(range(len(self.d)), key=self.d.__getitem__)
        return self.pts[k], self.d[k]


def _tangent_entry(ax, ay, px, py, r, dirn):
    """Where a stem from (ax, ay) meets the circle (px, py, r) on its tangent, winding dirn."""
    dx, dy = ax - px, ay - py
    D = _m.hypot(dx, dy)
    base = _m.atan2(dy, dx)
    if D <= r * 1.05:
        return base, None
    b = _m.acos(r / D)
    for phi in (base + b, base - b):
        sx, sy = px + r * _m.cos(phi), py + r * _m.sin(phi)
        hd = phi + dirn * PI / 2
        if (sx - ax) * _m.cos(hd) + (sy - ay) * _m.sin(hd) > 0:
            return phi, (sx, sy)
    return base, None


def scroll_field(cv, x, y, w, h, roots, seed=0, rmax=24., rmin=7., inside_fn=None, avoid=(), limit=400,
                 rfun=None, leafk=1., marks=None):
    """Pack the field (x, y, w, h) [and inside_fn] with fine scroll grown outward from roots
    [(x, y, heading, dirn)]: each new scroll takes the roomiest free spot within reach of an
    existing stem and grows from it on a tangent. avoid: [(cx, cy, r)] kept clear."""
    rng = _r.Random(seed)
    F = Field(x, y, w, h, inside_fn, step=max(4., min(6., rmin * .8)))
    for c in avoid:
        F.disc(*c, reach=rmax + 2)
    P, D = F.pts, F.d
    AD = [1e9] * len(P)          # distance to the nearest attach point
    att = []
    reach = rmax * 1.75 + 5

    def add_att(pts):
        for a in pts:
            att.append(a)
            ax, ay = a[0], a[1]
            for gx in range(int((ax - reach) // 20), int((ax + reach) // 20) + 1):
                for gy in range(int((ay - reach) // 20), int((ay + reach) // 20) + 1):
                    for k in F.grid.get((gx, gy), ()):
                        v = _m.hypot(P[k][0] - ax, P[k][1] - ay)
                        if v < AD[k]:
                            AD[k] = v
    add_att(roots)
    import heapq
    hp = [(-D[k], k) for k in range(len(P)) if D[k] >= rmin]
    heapq.heapify(hp)
    wait = []
    placed = 0
    since = 0
    while placed < limit:
        bk = -1
        while hp:
            nd, k = heapq.heappop(hp)
            dk = D[k]
            if dk < rmin:
                continue
            if -nd > dk + 1e-9:
                heapq.heappush(hp, (-dk, k))
                continue
            r = min(rmax, dk * .92)
            if AD[k] - r <= .7 * r + 4:
                bk, bd = k, dk
                break
            wait.append(k)
        if bk < 0:
            if wait and since:
                for k in wait:
                    if D[k] >= rmin:
                        heapq.heappush(hp, (-D[k], k))
                wait = []
                since = 0
                continue
            break
        since += 1
        if since >= 6 and wait:
            for k in wait:
                if D[k] >= rmin:
                    heapq.heappush(hp, (-D[k], k))
            wait = []
            since = 0
        px, py = P[bk]
        r = min(rmax if rfun is None else rfun(px, py), bd * .92)
        if r < rmin * .8:
            D[bk] = -1
            continue
        best = None
        for a in att:
            vx, vy = px - a[0], py - a[1]
            dd = _m.hypot(vx, vy) or 1.
            if dd > r * 1.75 + 4:
                continue
            cs = (vx * _m.cos(a[2]) + vy * _m.sin(a[2])) / dd
            sc = dd * (1.5 - .5 * cs)
            if best is None or sc < best[0]:
                best = (sc, a)
        if best is None:
            D[bk] = -1
            continue
        a = best[1]
        cross = _m.cos(a[2]) * (py - a[1]) - _m.sin(a[2]) * (px - a[0])
        dirn = 1 if cross > 0 else -1
        phi, S = _tangent_entry(a[0], a[1], px, py, r, dirn)
        tail = None
        if S:
            hd = phi + dirn * PI / 2
            L = _m.hypot(S[0] - a[0], S[1] - a[1])
            c1 = (a[0] + _m.cos(a[2]) * L * .4, a[1] + _m.sin(a[2]) * L * .4)
            c2 = (S[0] - _m.cos(hd) * L * .4, S[1] - _m.sin(hd) * L * .4)
            tail = bez((a[0], a[1]), c1, c2, S, max(5, int(L / 3)))
        new = fine_volute(cv, px, py, r, phi, dirn, rng, tail, leafk=leafk)
        if tail and len(tail) > 3:
            small_leaf(cv, a[0], a[1], a[2] - dirn * .5, max(6., min(r * 1., 16.)), -dirn, rng.randrange(1 << 20))
        F.disc(px, py, r * 1.05, rmax + 2)
        if tail:
            for q in tail[1::2]:
                F.disc(q[0], q[1], 3., rmax + 2)
        add_att(new)
        placed += 1
        if marks is not None:
            marks.append(len(cv.objs))
    return placed


# ---------------------------------------------------------------------------------------------
# Roman capitals drawn as paths: thick stems filled, thin strokes as hairlines, bracketed serifs.
# Glyph strokes on a box 0..w x 0..1 (y down): ("T", pts) thick, ("t", pts) thin; arcs are sampled.
# ---------------------------------------------------------------------------------------------

def _garc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * _m.cos(_m.radians(a0 + (a1 - a0) * i / n)), cy + ry * _m.sin(_m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_O = _garc(.38, .5, .36, .5, 0, 360, 20)
GLYPHS = {
    "A": (.72, [("t", [(.06, 1), (.36, 0)]), ("T", [(.36, 0), (.66, 1)]), ("t", [(.18, .64), (.54, .64)])]),
    "B": (.6, [("T", [(.08, 0), (.08, 1)]), ("t", [(.08, 0), (.36, 0)] + _garc(.36, .24, .2, .24, -90, 90, 8) + [(.08, .48)]),
               ("T", [(.36, .48)] + _garc(.36, .74, .22, .26, -90, 90, 8)[1:] + [(.08, 1)])]),
    "C": (.68, [("T", _garc(.38, .5, .34, .5, 205, 155 - 360 + 360, 1)[:0] + _garc(.38, .5, .34, .5, 145, 215, 8)),
                ("t", _garc(.38, .5, .34, .5, 215, 320, 8)), ("t", _garc(.38, .5, .34, .5, 40, 145, 8))]),
    "D": (.7, [("T", [(.08, 0), (.08, 1)]), ("t", [(.08, 0), (.3, 0)]), ("T", _garc(.3, .5, .32, .5, -60, 60, 10)),
               ("t", _garc(.3, .5, .32, .5, -90, -60, 3) + []), ("t", _garc(.3, .5, .32, .5, 60, 90, 3) + [(.08, 1)])]),
    "E": (.56, [("T", [(.08, 0), (.08, 1)]), ("t", [(.08, 0), (.5, 0)]), ("t", [(.08, .5), (.4, .5)]), ("t", [(.08, 1), (.52, 1)])]),
    "F": (.54, [("T", [(.08, 0), (.08, 1)]), ("t", [(.08, 0), (.5, 0)]), ("t", [(.08, .5), (.4, .5)])]),
    "G": (.72, [("T", _garc(.38, .5, .34, .5, 145, 215, 8)), ("t", _garc(.38, .5, .34, .5, 215, 320, 8)),
                ("t", _garc(.38, .5, .34, .5, 90, 145, 6)), ("T", [(.68, .56), (.68, .95)]), ("t", [(.46, .56), (.7, .56)])]),
    "H": (.72, [("T", [(.08, 0), (.08, 1)]), ("T", [(.62, 0), (.62, 1)]), ("t", [(.08, .5), (.62, .5)])]),
    "I": (.26, [("T", [(.12, 0), (.12, 1)])]),
    "J": (.4, [("T", [(.3, 0), (.3, .78)]), ("t", _garc(.14, .78, .16, .22, 0, 150, 6))]),
    "K": (.66, [("T", [(.08, 0), (.08, 1)]), ("t", [(.6, 0), (.08, .6)]), ("T", [(.26, .44), (.64, 1)])]),
    "L": (.54, [("T", [(.08, 0), (.08, 1)]), ("t", [(.08, 1), (.5, 1)])]),
    "M": (.86, [("t", [(.08, 1), (.1, 0)]), ("T", [(.1, 0), (.43, 1)]), ("t", [(.43, 1), (.76, 0)]), ("T", [(.76, 0), (.78, 1)])]),
    "N": (.72, [("t", [(.08, 1), (.08, 0)]), ("T", [(.08, 0), (.62, 1)]), ("t", [(.62, 1), (.62, 0)])]),
    "O": (.78, [("T", _garc(.39, .5, .35, .5, 130, 230, 8)), ("T", _garc(.39, .5, .35, .5, -50, 50, 8)),
                ("t", _garc(.39, .5, .35, .5, 230, 310, 6)), ("t", _garc(.39, .5, .35, .5, 50, 130, 6))]),
    "P": (.58, [("T", [(.08, 0), (.08, 1)]), ("t", [(.08, 0), (.32, 0)] + _garc(.32, .27, .22, .27, -90, 90, 8) + [(.08, .54)])]),
    "Q": (.78, [("T", _garc(.39, .5, .35, .5, 130, 230, 8)), ("T", _garc(.39, .5, .35, .5, -50, 50, 8)),
                ("t", _garc(.39, .5, .35, .5, 230, 310, 6)), ("t", _garc(.39, .5, .35, .5, 50, 130, 6)), ("T", [(.42, .86), (.74, 1.08)])]),
    "R": (.64, [("T", [(.08, 0), (.08, 1)]), ("t", [(.08, 0), (.32, 0)] + _garc(.32, .25, .22, .25, -90, 90, 8) + [(.08, .5)]),
                ("T", [(.3, .5), (.62, 1)])]),
    "S": (.54, [("t", _garc(.27, .25, .22, .25, -30, -90 - 90, 6)), ("T", _garc(.27, .25, .22, .25, 180, 90, 5) + _garc(.27, .75, .24, .25, -90, 0, 5)),
                ("t", _garc(.27, .75, .24, .25, 0, 150, 6))]),
    "T": (.62, [("t", [(.02, 0), (.6, 0)]), ("T", [(.31, 0), (.31, 1)])]),
    "U": (.7, [("T", [(.08, 0), (.08, .7)]), ("t", _garc(.34, .7, .26, .3, 180, 0, 8)[::-1][::-1]), ("t", [(.6, .7), (.6, 0)])]),
    "V": (.68, [("T", [(.04, 0), (.34, 1)]), ("t", [(.34, 1), (.64, 0)])]),
    "W": (.96, [("T", [(.04, 0), (.28, 1)]), ("t", [(.28, 1), (.48, .1)]), ("T", [(.48, .1), (.7, 1)]), ("t", [(.7, 1), (.92, 0)])]),
    "X": (.66, [("T", [(.06, 0), (.6, 1)]), ("t", [(.6, 0), (.06, 1)])]),
    "Y": (.64, [("T", [(.04, 0), (.32, .52)]), ("t", [(.6, 0), (.32, .52)]), ("T", [(.32, .52), (.32, 1)])]),
    "Z": (.6, [("t", [(.06, 0), (.54, 0)]), ("T", [(.54, 0), (.06, 1)]), ("t", [(.06, 1), (.56, 1)])]),
    "0": (.56, [("T", _garc(.28, .5, .24, .5, 140, 220, 6)), ("T", _garc(.28, .5, .24, .5, -40, 40, 6)), ("t", _garc(.28, .5, .24, .5, 220, 320, 6)), ("t", _garc(.28, .5, .24, .5, 40, 140, 6))]),
    "1": (.36, [("T", [(.2, 0), (.2, 1)]), ("t", [(.04, .16), (.2, 0)])]),
    "2": (.52, [("t", _garc(.26, .27, .22, .27, 200, 360, 7)), ("T", _garc(.26, .27, .22, .27, 0, 50, 3) + [(.04, 1)]), ("t", [(.04, 1), (.5, 1)])]),
    "3": (.52, [("t", _garc(.24, .24, .2, .24, 200, 450, 8)), ("T", _garc(.24, .74, .24, .26, -90, 90, 7)), ("t", _garc(.24, .74, .24, .26, 90, 160, 3))]),
    "4": (.56, [("t", [(.4, 0), (.02, .72), (.54, .72)]), ("T", [(.4, 0), (.4, 1)])]),
    "5": (.52, [("t", [(.48, 0), (.12, 0)]), ("T", [(.12, 0), (.08, .44)]), ("T", _garc(.24, .7, .24, .3, -120, 90, 8)), ("t", _garc(.24, .7, .24, .3, 90, 160, 3))]),
    "6": (.54, [("T", _garc(.28, .68, .24, .32, 0, 360, 14)[:9]), ("t", _garc(.28, .68, .24, .32, 0, 360, 14)[8:]), ("t", [(.06, .62), (.42, 0)])]),
    "7": (.5, [("t", [(.02, 0), (.48, 0)]), ("T", [(.48, 0), (.16, 1)])]),
    "8": (.54, [("t", _garc(.27, .24, .2, .24, 0, 360, 12)), ("T", _garc(.27, .74, .24, .26, -90, 90, 7)), ("t", _garc(.27, .74, .24, .26, 90, 270, 7))]),
    "9": (.54, [("T", _garc(.26, .32, .24, .32, 180, 540, 14)[:9]), ("t", _garc(.26, .32, .24, .32, 180, 540, 14)[8:]), ("t", [(.48, .38), (.14, 1)])]),
    ".": (.2, [("T", [(.1, .92), (.1, 1)])]),
    "·": (.3, [("T", [(.15, .46), (.15, .56)])]),
    "-": (.36, [("t", [(.04, .55), (.32, .55)])]),
    "'": (.18, [("T", [(.09, 0), (.07, .2)])]),
    "&": (.7, [("t", _garc(.26, .24, .16, .22, 90, 400, 10) + [(.62, 1)]), ("T", [(.2, .45), (.06, .7)] + _garc(.28, .76, .22, .24, 180, 60, 5) + [(.62, .5)])]),
    " ": (.3, []),
}


def _thick(pl, wid):
    """A filled stroke of width wid along pl (flat ends)."""
    hp = with_heading(pl)
    L_ = [(p[0] - _m.sin(p[2]) * wid / 2, p[1] + _m.cos(p[2]) * wid / 2) for p in hp]
    R_ = [(p[0] + _m.sin(p[2]) * wid / 2, p[1] - _m.cos(p[2]) * wid / 2) for p in hp]
    return L_ + R_[::-1]


def text_width(txt, cap, track=.12):
    return sum((GLYPHS.get(c, GLYPHS[" "])[0] + track) * cap for c in txt.upper()) - track * cap


def letters(txt, x, y, cap, track=.12, warp=None, serif=True):
    """Roman capitals from (x, y) (top-left of the cap line), cap high. warp(x, y) -> (x, y) bends
    the line (e.g. along a ribbon). Returns (fill_d, hair_d) path data."""
    fills, hairs = [], []
    W_ = warp or (lambda a, b: (a, b))
    xx = x
    tk = max(1., cap * .15)
    for c in txt.upper():
        adv, strokes = GLYPHS.get(c, GLYPHS[" "])
        for kind, pts in strokes:
            P_ = [(xx + px * cap, y + py * cap) for px, py in pts]
            P_ = resample(P_, max(.8, cap * .12))
            if kind == "T":
                fills.append(_d([W_(*p) for p in _thick(P_, tk)], True, 0))
            else:
                hairs.append(_d([W_(*p) for p in P_], tol=0))
            if serif and kind == "T" and len(pts) == 2 and abs(pts[0][0] - pts[1][0]) < .35:
                for (px, py) in pts:
                    if py in (0, 1):
                        sx, sy = xx + px * cap, y + py * cap
                        hairs.append(_d([W_(sx - cap * .14, sy), W_(sx + cap * .14, sy)], tol=0))
        xx += (adv + track) * cap
    return "".join(fills), "".join(hairs)


def letter_svg(txt, x, y, cap, track=.12, warp=None, color="#000"):
    f, hh = letters(txt, x, y, cap, track, warp)
    sw = "1" if cap >= 9 else ".5"
    return (f'<path d="{f}" fill="{color}" stroke="none"/>' if f else "") + \
           (f'<path d="{hh}" fill="none" stroke="{color}" stroke-width="{sw}"/>' if hh else "")


# ---------------------------------------------------------------------------------------------
# gold-line borders, beading, the inlaid medallion
# ---------------------------------------------------------------------------------------------

def offset_poly(poly, d):
    """Offset a closed (ccw or cw, convex-ish) polygon by d px outward (approx; vertex normals)."""
    n = len(poly)
    A = C._area(poly)
    sgn = 1 if A > 0 else -1
    out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        t1 = _m.atan2(b[1] - a[1], b[0] - a[0])
        t2 = _m.atan2(c[1] - b[1], c[0] - b[0])
        nx = (_m.sin(t1) + _m.sin(t2)) / 2
        ny = (-_m.cos(t1) - _m.cos(t2)) / 2
        L_ = _m.hypot(nx, ny) or 1.
        k = 1 / max(.35, L_)
        out.append((b[0] - sgn * nx / L_ * d * k, b[1] - sgn * ny / L_ * d * k))
    return out


def beads_along(pl, r=1.5, gap=1.2, closed=True):
    """A bead row along a polyline: each bead a white dot rimmed and crescent-shaded in black,
    drawn as round-capped dots (two short paths for the whole row). Returns svg."""
    pts = resample(pl + ([pl[0]] if closed else []), .5)
    step = 2 * r + gap
    last = None
    D = []
    for p in pts:
        if last is None or _m.hypot(p[0] - last[0], p[1] - last[1]) >= step:
            D.append(p)
            last = p
    if closed and len(D) > 2 and _m.hypot(D[-1][0] - D[0][0], D[-1][1] - D[0][1]) < step * .8:
        D.pop()
    k = "".join(f"M{_f1(round(x * 4) / 4)} {_f1(round(y * 4) / 4)}h0" for x, y in D)
    wd = "".join(f"M{_f1(round((x - r * .22) * 4) / 4)} {_f1(round((y - r * .22) * 4) / 4)}h0" for x, y in D)
    return (f'<path d="{k}" stroke="#000" stroke-width="{_n(2 * r + 1)}" stroke-linecap="round"/>'
            f'<path d="{wd}" stroke="#fff" stroke-width="{_n(2 * r - .5)}" stroke-linecap="round"/>')


def gold_border(poly, beads=True, triple=True, br=1.5):
    """A fine wire-inlay border following poly (closed): a white band edged by 1 px black lines with
    a hairline down its middle, and a bead row outside it. Returns svg."""
    o = []
    p1 = offset_poly(poly, 1.5)
    p2 = offset_poly(poly, 4.5)
    o.append(f'<path d="{_d(p2, True, 0)}{_d(p1[::-1], True, 0)}" fill="#fff" fill-rule="evenodd" stroke="#000" stroke-width="1"/>')
    if triple:
        o.append(f'<path d="{_d(offset_poly(poly, 3.), True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    if beads:
        pb = offset_poly(poly, 4.5 + br + 1.)
        o.append(beads_along(pb, br))
    return "".join(o)


def gold_frame(x, y, w, h, c):
    """The plate's wire-inlay frame: a cut-corner white band between 1 px rules with a centre
    hairline, a bead row inside it."""
    o = []
    a = cut_poly(x, y, w, h, c)
    b = cut_poly(x + 3, y + 3, w - 6, h - 6, c + 3)
    o.append(f'<path d="{_d(a, True, 0)}{_d(b[::-1], True, 0)}" fill="#fff" fill-rule="evenodd" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_d(cut_poly(x + 1.5, y + 1.5, w - 3, h - 3, c + 1.5), True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(beads_along(cut_poly(x + 6, y + 6, w - 12, h - 12, c + 6), 1.3, 1.))
    return "".join(o)


def ellipse_poly(cx, cy, rx, ry, n=96):
    return _ell(cx, cy, rx, ry, n)[:-1]


def arch_poly(x, y, w, h, n=40):
    """An arched-top panel: semicircular-ish head on a rectangle."""
    r = min(w / 2, h * .45)
    pts = [(x, y + h), (x, y + r)]
    pts += [(x + w / 2 - (w / 2) * _m.cos(PI * i / n), y + r - r * _m.sin(PI * i / n)) for i in range(1, n)]
    pts += [(x + w, y + r), (x + w, y + h)]
    return pts


def cut_poly(x, y, w, h, c, n=8):
    """A rectangle with its corners cut by concave quarter-circles of radius c (clockwise)."""
    pts = []
    for (cx, cy, a0, a1) in ((x, y, 90, 0), (x + w, y, 180, 90), (x + w, y + h, 270, 180), (x, y + h, 360, 270)):
        pts += [(cx + c * _m.cos(_m.radians(a0 + (a1 - a0) * i / n)), cy + c * _m.sin(_m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return pts


def medallion_ring(poly, br=None):
    """The inlaid medallion's carved ring around a scene field poly: an inner black fillet, a bead
    ring between gold lines and an outer moulding."""
    br = br or 1.6
    o = []
    a = offset_poly(poly, 0.)
    b = offset_poly(poly, 2 * br + 4.)
    o.append(f'<path d="{_d(b, True, 0)}{_d(a[::-1], True, 0)}" fill="#000" fill-rule="evenodd" stroke="#000" stroke-width="1"/>')
    o.append(beads_along(offset_poly(poly, br + 2.), br, 1.))
    c = offset_poly(poly, 2 * br + 4.)
    d = offset_poly(poly, 2 * br + 8.5)
    o.append(f'<path d="{_d(d, True, 0)}{_d(c[::-1], True, 0)}" fill="#fff" fill-rule="evenodd" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_d(offset_poly(poly, 2 * br + 6.5), True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    return "".join(o), d


# ---------------------------------------------------------------------------------------------
# scene textures: an engraved sky (swelling burin lines broken by modelled cloud banks) and water
# ---------------------------------------------------------------------------------------------

def burin_sky(cv, x, y, w, h, seed=0, clouds=3, dark_top=True, holes=(), pitch=2., banks=None):
    """Sky in swelling burin lines (1 px near the zenith thinning to 0.5 px, gently undulating),
    with banks of cumulus: each bank a heap of billows, every billow rimmed and cut in curved
    contour lines on its shadowed underside, lit crowns left bright. holes: [(cx, cy, r)] clear.
    banks: [(cx, base_y, width, height)] to place them yourself."""
    rng = _r.Random(seed)
    if banks is None:
        banks = []
        for i in range(clouds):
            banks.append((x + w * rng.uniform(.1, .9), y + h * rng.uniform(.35, .85),
                          w * rng.uniform(.2, .36), h * rng.uniform(.18, .3)))
    cv.obj([[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]], 0)
    yy = y + .5
    j = 0
    while yy < y + h:
        t = (yy - y) / h
        cur = []
        segs = []
        ph = rng.uniform(0, 6)
        for i in range(int(w / 3) + 2):
            px = x + i * 3.
            py = yy + .6 * _m.sin(px / 23. + ph + j * .3)
            if any((px - hx) ** 2 + (py - hy) ** 2 < hr * hr for hx, hy, hr in holes):
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            else:
                cur.append((px, py))
        if len(cur) > 1:
            segs.append(cur)
        for seg in segs:
            # swelling burin: the line thickens where the cloud-wrack is dark, thins in the clear
            cur, heavy = [], None
            for p in seg:
                nz = (_m.sin(p[0] / 37. + p[1] / 19. + ph * .3) + _m.sin(p[0] / 13. - p[1] / 29. + 1.7)
                      + .8 * _m.sin(p[0] / 61. + p[1] / 7.3)) / 2.8 + (.35 - t) * (1.2 if dark_top else .4)
                hv = nz > .22
                if heavy is None or hv == heavy:
                    cur.append(p)
                else:
                    cur.append(p)
                    if len(cur) > 1:
                        (cv.line if heavy else cv.hair)(cur)
                    cur = [p]
                heavy = hv
            if len(cur) > 1:
                (cv.line if heavy else cv.hair)(cur)
        yy += pitch if t < .55 else pitch * 1.5
        j += 1
    for bx, by, bw, bh in banks:
        n = max(4, int(bw / (bh * .55)))
        bil = []
        for i in range(n):
            u = -1 + 2 * (i + .5) / n
            r = bh * (.32 + .38 * (1 - u * u)) * rng.uniform(.8, 1.1)
            bil.append((bx + u * bw / 2 * .85, by - r * .55 - bh * .18 * (1 - u * u), r))
        # a second tier of smaller billows riding on the crown
        for i in range(max(2, n // 2)):
            u = -.6 + 1.2 * (i + .5) / max(2, n // 2)
            r = bh * .26 * rng.uniform(.8, 1.15)
            bil.append((bx + u * bw / 2 * .7, by - bh * .62 - r * .2, r))
        bil.sort(key=lambda c: -c[1])
        for cx, cy, r in sorted(bil, key=lambda c: c[1]):
            poly = [(cx + r * _m.cos(TAU * i / 44), min(by, cy + r * _m.sin(TAU * i / 44))) for i in range(44)]
            cv.obj([poly], .5)
            k = 1
            while r - k * 1.6 > 1.5:
                rr = r - k * 1.6
                arc = [(cx + rr * _m.cos(a), min(by - .8, cy + rr * _m.sin(a)))
                       for a in [PI * (.05 + .9 * i / 12) - PI * .05 * k for i in range(13)]]
                arc = [p for p in arc if p[1] < by - .8]
                if len(arc) > 1:
                    (cv.line if k <= 1 else cv.hair)(arc)
                k += 1
                if k > 3 + r / 4:
                    break
    return banks


def burin_water(cv, x, y, w, h, seed=0, glints=(), pitch=2.):
    """Water in tapering horizontal burin strokes broken into dashes, closer and darker toward the
    near shore; glints: [(cx, half_width)] columns of reflected light (lines broken there)."""
    rng = _r.Random(seed + 11)
    cv.obj([[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]], 0)
    yy = y + 1
    while yy < y + h:
        t = (yy - y) / h
        xx = x - rng.uniform(0, 8)
        while xx < x + w:
            L_ = rng.uniform(8, 26) * (1 - .4 * t)
            g = False
            for gx, gw in glints:
                if abs(xx + L_ / 2 - gx) < gw * (.5 + t):
                    g = True
            if not g or rng.random() < .3:
                seg = [(xx + L_ * i / 4, yy + .5 * _m.sin(xx * .2 + i)) for i in range(5)]
                (cv.line if t > .7 and rng.random() < .5 else cv.hair)(seg)
            xx += L_ + rng.uniform(1.5, 4)
        yy += pitch * (1.5 - .5 * t) if t < .5 else pitch


# ---------------------------------------------------------------------------------------------
# ribbon banner with lettering, the pedestal, the placeholder arms
# ---------------------------------------------------------------------------------------------

def ribbon(cx, cy, w, bh, text="", arch=.05, seed=0):
    """A folded ribbon: an arched face lettered in Roman capitals, folding behind at both ends into
    swallow-tailed tails cut dark on their backs. Returns svg."""
    cv = Canvas()
    fw = w * .74
    n = 40

    def C_(u):
        return (cx - fw / 2 + fw * u, cy - arch * w * _m.sin(PI * u))
    face_top = [(C_(i / n)[0], C_(i / n)[1] - bh / 2) for i in range(n + 1)]
    face_bot = [(C_(i / n)[0], C_(i / n)[1] + bh / 2) for i in range(n + 1)]
    for s in (-1, 1):
        e = C_(0 if s < 0 else 1)
        tl = (w - fw) / 2 + bh * .4
        x0 = e[0] - s * bh * .3
        y0 = e[1] + bh * .35
        x1 = x0 + s * tl
        notch = (x1 - s * bh * .55, y0 + bh * .5)
        tail = [(x0, y0 - bh * .5), (x1, y0 - bh * .5 + s * 0 + bh * .1), notch, (x1, y0 + bh * .5 + bh * .1), (x0, y0 + bh * .5)]
        cv.obj([tail], 1.)
        for k in range(1, int(bh / 2)):
            yy = y0 - bh * .5 + k * 2
            cv.hair([(x0, yy), (x1 - s * bh * .2, yy + bh * .05)])
        fold = [(e[0], e[1] - bh / 2), (e[0], e[1] + bh / 2), (x0, y0 + bh * .5), (x0, y0 - bh * .5 + 0)]
        cv.obj([fold], 1.)
        for k in range(0, int(bh) + 2, 1):
            cv.line([(e[0], e[1] - bh / 2 + k), (x0, y0 - bh * .5 + k)])
    cv.obj([face_top + face_bot[::-1]], 1.)
    cv.hair([(p[0], p[1] + 1.5) for p in face_top[1:-1]])
    cv.hair([(p[0], p[1] - 1.5) for p in face_bot[1:-1]])
    o = [cv.svg()]
    if text:
        cap = bh * .5
        tw = text_width(text, cap)
        if tw > fw * .9:
            cap *= fw * .9 / tw
            tw = text_width(text, cap)
        x0 = cx - tw / 2

        def warp(px, py):
            u = (px - (cx - fw / 2)) / fw
            return (px, py - arch * w * _m.sin(PI * min(1, max(0, u))))
        o.append(letter_svg(text, x0, cy - cap / 2, cap, warp=warp))
    return "".join(o)


def arms_placeholder(cx, cy, r):
    """Placeholder for Parker's family arms (do not invent arms): a beaded cartouche carrying
    crossed drumsticks over a rising sun."""
    cv = Canvas()
    ov = ellipse_poly(cx, cy, r * .78, r, 48)
    cv.obj([ov], 1.)
    # sun: a disc with rays, over a ruled horizon cut in swelling lines
    sy = cy + r * .25
    for i in range(13):
        a = PI + PI * (i + .5) / 13
        cv.hair([(cx + r * .28 * _m.cos(a), sy + r * .28 * _m.sin(a)), (cx + r * (.62 if i % 2 else .5) * _m.cos(a), sy + r * (.62 if i % 2 else .5) * _m.sin(a))])
    disc = _ell(cx, sy, r * .24, r * .24, 16, PI, TAU)
    cv.obj([disc], 1.)
    cv.hair([(cx - r * .62, sy + 1.5 * k) for k in range(1)] + [(cx + r * .62, sy)])
    for k in range(1, 4):
        yy = sy + k * 2
        hw = (r * r - (yy - cy) ** 2) ** .5 * .76 if abs(yy - cy) < r else 0
        cv.hair([(cx - hw, yy), (cx + hw, yy)])
    # crossed drumsticks
    for s in (-1, 1):
        a = _m.radians(90 + s * 38)
        x0, y0 = cx - _m.cos(a) * r * .7, cy + r * .6
        x1, y1 = cx + _m.cos(a) * r * .55, cy - r * .62
        st = _thick([(x0, y0), (x1, y1)], max(1.6, r * .09))
        cv.obj([st], .5)
        cv.obj([_ell(x1, y1, r * .07 + .6, r * .07 + .6, 8)[:-1]], .5)
    o = [cv.svg()]
    o.append(f'<path d="{_d(offset_poly(ov, 4.), True, 0)}{_d(ov[::-1], True, 0)}" fill="#000" fill-rule="evenodd"/>')
    o.append(beads_along(offset_poly(ov, 2.2), 1.2, .9))
    o.append(f'<path d="{_d(offset_poly(ov, 4.5), True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def pedestal(x, y, w, h, tablet=None, seed=0):
    """An architectural base filling x..x+w, y..y+h: a knurled cornice, a frieze whose sunk tablet
    carries the page (tablet(tx, ty, tw, th) -> svg), a torus of beads, and an ogee plinth modelled
    in swelling curved lines. Returns svg."""
    o = []
    kb = max(5., min(9., h * .1))
    o.append(C.knurled_bar(x, y, w, kb))
    fy = y + kb
    fh = h * .5
    o.append(f'<path d="M{_n(x + 2)},{_n(fy)}h{_n(w - 4)}v{_n(fh)}h{_n(-w + 4)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    # frieze face: fluting modelled in tapering lines (dark at each flute's shadowed side)
    cv = Canvas()
    cv.obj([], 0)
    xx = x + 4
    while xx < x + w - 4:
        for k in range(3):
            cv.hair([(xx + k * 1.5, fy + 2), (xx + k * 1.5, fy + fh - 2)])
        xx += 9
    o.append(cv.svg())
    th = fh * .74
    tw = w * .62
    tx, ty = x + (w - tw) / 2, fy + (fh - th) / 2
    o.append(gold_border([(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th)][::-1], beads=False, triple=False))
    o.append(f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    if tablet:
        o.append(tablet(tx + 1, ty + 1, tw - 2, th - 2))
    by = fy + fh
    o.append(f'<path d="M{_n(x)},{_n(by)}h{_n(w)}v6h{_n(-w)}z" fill="#000"/>')
    o.append(beads_along([(x + 4, by + 3), (x + w - 4, by + 3)], 2., 1., closed=False))
    py = by + 6
    ph = y + h - py
    if ph > 3:
        o.append(f'<path d="M{_n(x)},{_n(py)}h{_n(w)}v{_n(ph)}h{_n(-w)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(black_ground((x + 1, py + 1, w - 2, ph - 2), seed + 3, dens=0))
        cv = Canvas()
        lh = ph - 3
        n = max(6, int(w / (lh * .9)))
        rng = _r.Random(seed)
        for i in range(n):
            lx = x + (i + .5) * w / n
            small_leaf(cv, lx, py + ph - 1, -PI / 2 + rng.uniform(-.08, .08), lh * rng.uniform(.9, 1.05), 1 if i % 2 else -1, rng.randrange(1 << 20))
        o.append(cv.svg())
    return "".join(o), (tx, ty, tw, th)


# ---------------------------------------------------------------------------------------------
# composition: the three shaped plates
# ---------------------------------------------------------------------------------------------

def _poly_contains_margin(poly, m):
    """inside-test excluding a shape grown by m (for the scroll field)."""
    big = offset_poly(poly, m)
    xs = [p[0] for p in big]
    ys = [p[1] for p in big]
    bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)

    def f(px, py):
        return bx0 <= px <= bx1 and by0 <= py <= by1 and pt_in(px, py, big)
    return f


def _roots_on(poly, k, outward=True):
    """k stem sources spaced round a shape, heading along it."""
    pts = resample(poly + [poly[0]], 2.)
    out = []
    for i in range(k):
        j = int((i + .5) / k * (len(pts) - 1))
        a, b = pts[j], pts[min(len(pts) - 1, j + 1)]
        hd = _m.atan2(b[1] - a[1], b[0] - a[0])
        out.append((a[0], a[1], hd, 1 if i % 2 else -1))
    return out


def plate_doc(w, h, body, seed):
    return C.svg_doc(w, h, ground_defs(seed) + body)


def compose(w, h, ctx, spec):
    """spec: dict(scene=fn(x, y, w, h, clip_d, level)->svg, motif=fn(cx, cy, r, i)->svg (corner
    roundels, figural/egg), tablet=fn(tx, ty, tw, th)->svg, ribbon=str, seed=int, shape='oval'|
    'arch'|'cut', leafk, rmax)."""
    seed = spec.get("seed", 1)
    rng = _r.Random(seed)
    o = []
    avoid = []
    cv = Canvas()
    roots = []
    fronts = []           # svg drawn over the scroll
    mot = spec.get("motif")
    M = 3.
    if h < 110:
        level = 0
        my = h / 2
        mh = h - 14
        mw = min(w * .36, mh * 2.1)
        med = ellipse_poly(w / 2, my, mw / 2, mh / 2, 80)
        ring, outer = medallion_ring(med, 1.3)
        fronts.append(f'<clipPath id="mc{seed}"><path d="{_d(med, True, 0)}"/></clipPath>')
        fronts.append(spec["scene"](w / 2 - mw / 2, my - mh / 2, mw, mh, _d(med, True, 0), 0))
        fronts.append(ring)
        avoid.append(_poly_contains_margin(med, 9))
        roots += [(w / 2 - mw / 2 - 8, my, PI, 1), (w / 2 + mw / 2 + 8, my, 0., -1)]
        rings = []
        if mot and h >= 60:
            for i, sx in enumerate((-1, 1)):
                rr = (h - 16) * .34
                cx = w / 2 + sx * (w * .5 - rr - 12)
                rings.append((cx, my, rr, i))
        for cx, cy, rr, i in rings:
            rp = ellipse_poly(cx, cy, rr, rr, 40)
            rg, _ = medallion_ring(rp, 1.)
            fronts.append(mot(cx, cy, rr, i))
            fronts.append(rg)
            avoid.append(_poly_contains_margin(rp, 7))
        field = (0, 5.5, w, h - 11)
        rmax = spec.get("rmax", min(16., h * .2))
        border_lines = (f'<path d="M0,1h{_n(w)}M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="2"/>'
                        f'<path d="M0,3.25h{_n(w)}M0,{_n(h - 3.25)}h{_n(w)}" stroke="#fff" stroke-width="1.5"/>'
                        f'<path d="M0,5h{_n(w)}M0,{_n(h - 5)}h{_n(w)}" stroke="#fff" stroke-width="1"/>')
    elif h <= 260:
        level = 1
        mh = h - 26
        mw = min(w * .44, mh * 1.45)
        my = h / 2
        shape = spec.get("shape", "oval")
        if shape == "arch":
            med = arch_poly(w / 2 - mw / 2, my - mh / 2, mw, mh)
        elif shape == "cut":
            med = cut_poly(w / 2 - mw / 2, my - mh / 2, mw, mh, min(mw, mh) * .16)
        else:
            med = ellipse_poly(w / 2, my, mw / 2, mh / 2, 96)
        ring, outer = medallion_ring(med, 1.5)
        fronts.append(spec["scene"](w / 2 - mw / 2, my - mh / 2, mw, mh, _d(med, True, 0), 1))
        fronts.append(ring)
        avoid.append(_poly_contains_margin(med, 11))
        roots += _roots_on(offset_poly(med, 11), 6)
        if mot:
            for i, sx in enumerate((-1, 1)):
                rr = min(h * .17, 26)
                cx = w / 2 + sx * (w * .5 - rr - 16)
                cy = h * .5
                rp = ellipse_poly(cx, cy, rr, rr, 48)
                rg, _ = medallion_ring(rp, 1.2)
                fronts.append(mot(cx, cy, rr, i))
                fronts.append(rg)
                avoid.append(_poly_contains_margin(rp, 8))
        field = (M + 4, M + 4, w - 2 * M - 8, h - 2 * M - 8)
        rmax = spec.get("rmax", min(20., h * .11))
        border_lines = gold_frame(M, M, w - 2 * M, h - 2 * M, min(22., h * .12))
        # corner spandrels outside the cut corners: foliage roundels
        sp_ = min(22., h * .12)
        for (cx, cy) in ((0, 0), (w, 0), (0, h), (w, h)):
            fronts.append(_spandrel(cx, cy, sp_, rng.randrange(1 << 20)))
    else:
        level = 2
        ped_h = min(max(h * .16, 50), 84.)
        rb_h = min(22., h * .05)
        top = 16.
        pw = w * spec.get("pw", .7)
        arm_room = 44. if h > 380 else 0.
        ph = h - ped_h - top - rb_h * 1.6 - 10 - arm_room
        px = w / 2 - pw / 2
        shape = spec.get("tall_shape", "arch")
        if shape == "oval":
            med = ellipse_poly(w / 2, top + ph / 2, pw / 2, ph / 2, 120)
        elif shape == "cut":
            med = cut_poly(px, top, pw, ph, pw * .12)
        else:
            med = arch_poly(px, top, pw, ph, 48)
        ring, outer = medallion_ring(med, 1.6)
        fronts.append(spec["scene"](px, top, pw, ph, _d(med, True, 0), 2))
        fronts.append(ring)
        avoid.append(_poly_contains_margin(med, 12))
        ry = top + ph + 2
        fronts.append(ribbon(w / 2, ry, w * .86, rb_h, spec.get("ribbon", ""), .03, seed))
        avoid.append(lambda a, b, ry=ry: abs(b - ry) < rb_h * .9 + 4 and abs(a - w / 2) < w * .43)
        # the placeholder arms between ribbon and pedestal
        py = h - ped_h - 2
        ar = min(19., (py - ry - rb_h * .6) * .42)
        if ar > 9:
            ay = (ry + rb_h * .6 + py) / 2
            fronts.append(arms_placeholder(w / 2, ay, ar))
            avoid.append(_poly_contains_margin(ellipse_poly(w / 2, ay, ar * .8, ar, 30), 7))
        ped, _ = pedestal(5, py, w - 10, ped_h - 3, spec.get("tablet"), seed)
        fronts.append(ped)
        avoid.append(lambda a, b, py=py: b > py - 4)
        roots += [(6, py - 6, -PI / 2, 1), (w - 6, py - 6, -PI / 2, -1), (w / 2 - 30, py - 6, PI, 1), (w / 2 + 30, py - 6, 0., -1)]
        roots += _roots_on(offset_poly(med, 12), 6)
        if mot:
            for i, sx in enumerate((-1, 1)):
                rr = min(w * .07, 30)
                cx = w / 2 + sx * (pw / 2 + (w / 2 - pw / 2) / 2)
                cy = top + rr + 18
                rp = ellipse_poly(cx, cy, rr, rr, 48)
                rg, _ = medallion_ring(rp, 1.3)
                fronts.append(mot(cx, cy, rr, i))
                fronts.append(rg)
                avoid.append(_poly_contains_margin(rp, 8))
        field = (M + 4, M + 4, w - 2 * M - 8, h - 2 * M - 8)
        rmax = min(spec.get("rmax_tall", 24.) * max(1., (w * h / (526. * 548.)) ** .5), h * .075)
        border_lines = gold_frame(M, M, w - 2 * M, h - 2 * M, 26.)
        for (cx, cy) in ((0, 0), (w, 0), (0, h), (w, h)):
            fronts.append(_spandrel(cx, cy, 26., rng.randrange(1 << 20)))

    def ok(a, b):
        for f in avoid:
            if f(a, b):
                return False
        return True
    fixed = [black_ground((0, 0, w, h), seed, dens=.12), border_lines] + fronts
    budget = spec.get("budget", 191) * 1024 - sum(len(f.encode()) for f in fixed) - 1500
    cv = Canvas()
    marks = []
    scroll_field(cv, *field, roots, seed=seed, rmax=rmax, rmin=max(6., rmax * .36), inside_fn=ok,
                 leafk=spec.get("leafk", 1.), marks=marks)
    sv = cv.svg()
    tries = 0
    while len(sv) > budget and marks and tries < 3:
        # over budget: keep the larger scrolls (placed first) and let the matte show where the
        # smallest would have gone
        tries += 1
        n_obj = len(cv.objs)
        target = n_obj * (budget / len(sv)) ** 1.3 * .97
        ms = [m_ for m_ in marks if m_ <= target]
        cut = ms[-1] if ms else marks[0]
        cv.objs = cv.objs[:cut]
        marks = [m_ for m_ in marks if m_ <= cut]
        sv = cv.svg()
    o.append(fixed[0])
    o.append(sv)
    o += fixed[1:]
    return plate_doc(w, h, "".join(o), seed)


def _spandrel(cx, cy, r, seed):
    """A corner spandrel: a quarter rosette of radiating leaves on black, held by a bead."""
    cv = Canvas()
    rng = _r.Random(seed)
    sx = 1 if cx == 0 else -1
    sy = 1 if cy == 0 else -1
    base = _m.atan2(sy, sx)
    for k in range(5):
        a = base - .75 + 1.5 * k / 4
        small_leaf(cv, cx + sx * 2, cy + sy * 2, a, r * rng.uniform(.75, .95), 1 if k % 2 else -1, rng.randrange(1 << 20))
    cv.obj([_ell(cx + sx * 3, cy + sy * 3, 3, 3, 10)[:-1]], 1.)
    return cv.svg()
# ==== end of studio kit ====

import re
import zlib
PI = math.pi


def _uid(*a):
    return "spt" + format(zlib.crc32(repr(a).encode()) & 0xffffff, "x")


def _ell(cx, cy, rx, ry, n=48, a0=0., a1=2 * PI):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def _P(d, fill="none", sw=None, extra=""):
    s = f' stroke="#000" stroke-width="{_n(sw)}"' if sw else ' stroke="none"'
    return f'<path d="{d}" fill="{fill}"{s}{extra}/>'


def _lines(pls, tol=0.):
    return "".join(_d(p, tol=tol) for p in pls if len(p) > 1)


# ------------------------------------------------------------------------------------------------
# the football: a truncated icosahedron in orthographic projection, shaded as a sphere
# ------------------------------------------------------------------------------------------------

_PHI = (1 + 5 ** .5) / 2
_ICO = []
for _a in (-1, 1):
    for _b in (-_PHI, _PHI):
        _ICO += [(0, _a, _b), (_a, _b, 0), (_b, 0, _a)]


def _norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def _nbrs(i):
    v = _ICO[i]
    return [j for j, u in enumerate(_ICO) if j != i and abs(sum((a - b) ** 2 for a, b in zip(u, v)) - 4) < 1e-6]


def _rot(v, rx, ry, rz):
    x, y, z = v
    c, s = math.cos(rx), math.sin(rx)
    y, z = y * c - z * s, y * s + z * c
    c, s = math.cos(ry), math.sin(ry)
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(rz), math.sin(rz)
    x, y = x * c - y * s, x * s + y * c
    return (x, y, z)


def _slerp(a, b, t):
    return _norm(tuple(p + (q - p) * t for p, q in zip(a, b)))


def football(cx, cy, r, rot=(.4, .3, .2), shade=True):
    """A shaded football: white sphere, black pentagons, seams, and a hatched shadow crescent
    lower right with a black core and a reflected-light rim. 4-5 elements."""
    def pv(i, j):
        v, u = _ICO[i], _ICO[j]
        return _norm(tuple(a + (b - a) / 3 for a, b in zip(v, u)))

    def proj(p):
        q = _rot(p, *rot)
        return (cx + q[0] * r, cy - q[1] * r, q[2])

    pents, seams = [], []
    for i in range(12):
        nb = _nbrs(i)
        # order the neighbours around the vertex
        v = _ICO[i]
        ref = _norm(_ICO[nb[0]])
        e1 = _norm(tuple(a - sum(x * y for x, y in zip(ref, v)) / 5.236 * b for a, b in zip(ref, v)))
        vn = _norm(v)
        e2 = (vn[1] * e1[2] - vn[2] * e1[1], vn[2] * e1[0] - vn[0] * e1[2], vn[0] * e1[1] - vn[1] * e1[0])
        nb.sort(key=lambda j: math.atan2(sum(a * b for a, b in zip(_ICO[j], e2)), sum(a * b for a, b in zip(_ICO[j], e1))))
        ring = [pv(i, j) for j in nb]
        pts3 = []
        for k in range(5):
            a, b = ring[k], ring[(k + 1) % 5]
            pts3 += [_slerp(a, b, t / 4) for t in range(4)]
        P = [proj(p) for p in pts3]
        if min(p[2] for p in P) > -.05:
            pents.append([(p[0], p[1]) for p in P])
        elif max(p[2] for p in P) > 0:
            # partly round the limb: keep only the front part
            pents.append([(p[0], p[1]) if p[2] > 0 else
                          (cx + (p[0] - cx) / max(1e-6, math.hypot(p[0] - cx, p[1] - cy)) * r,
                           cy + (p[1] - cy) / max(1e-6, math.hypot(p[0] - cx, p[1] - cy)) * r) for p in P])
        for j in nb:
            if j > i:
                a, b = pv(i, j), pv(j, i)
                seg = [proj(_slerp(a, b, t / 6)) for t in range(7)]
                vis = [(p[0], p[1]) for p in seg if p[2] > 0]
                if len(vis) > 1:
                    seams.append(vis)
    # the hexagon seams also run between pentagon vertices of neighbouring pentagons (already
    # covered above), plus the pentagon outlines themselves.
    circ = _ell(cx, cy, r, r, 56)
    o = [_P(_d(circ, True, .1), "#fff", 1.)]
    o.append(_P("".join(_d(p, True, .15) for p in pents), "#000"))
    o.append(_P(_lines(seams, .15), sw=.5))
    if shade:
        # shadow crescent, lower right: hatched, then a black core under the limb
        n = 40
        outer = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in
                 [-.55 + (PI + .2) * k / n for k in range(n + 1)]]
        inner = [(cx + r * .42 + r * .62 * math.cos(t), cy + r * .3 + r * .62 * math.sin(t)) for t in
                 [-.55 + PI + .2 - (PI + .2) * k / n for k in range(n + 1)]]
        cres = outer + inner
        hl = C.hatch_poly(cres, -35, 1.5 if r < 14 else 2.)
        o.append(_P(_lines(hl), sw=.5))
        core = [(cx + (r - .4) * math.cos(t), cy + (r - .4) * math.sin(t)) for t in [.0 + 1.9 * k / 20 for k in range(21)]]
        core += [(cx + (r - r * .13) * math.cos(t), cy + (r - r * .13) * math.sin(t)) for t in [1.9 - 1.9 * k / 20 for k in range(21)]]
        o.append(_P(_d(core, True, .1), "#000"))
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# scene pieces
# ------------------------------------------------------------------------------------------------

def _fir(x, base, h, rng, wfac=.36):
    """Douglas fir: drooping tiers. Returns (outline polygon, branch-tip hatch polylines)."""
    tiers = max(4, int(h / 6))
    left, right = [], []
    top = base - h
    for k in range(tiers + 1):
        t = k / tiers
        y = top + h * t * .92
        hw = h * wfac * (t ** .95) * rng.uniform(.85, 1.1) + .6
        left.append((x - hw, y + h * .03))
        left.append((x - hw * .45, y + h * .012))
        right.append((x + hw, y + h * .03))
        right.append((x + hw * .45, y + h * .012))
    poly = [(x, top)] + right[1:] + [(x + h * .03, base), (x - h * .03, base)] + left[1:][::-1]
    return poly


def _fir_svg(x, base, h, rng, dark="G", wfac=.36):
    """A Douglas fir carved in relief: drooping tiers, each lit on the upper-left (open cuts) and
    shadowed lower-right (close cuts, a heavy shade line under each bough), a black trunk."""
    cv = Canvas()
    tiers = max(4, int(h / 11))
    top = base - h * .93
    trunk = [(x - h * .025, base - h * .1), (x + h * .025, base - h * .1), (x + h * .035, base), (x - h * .035, base)]
    cv.obj([trunk], .5)
    cv.line(C.hatch_poly(trunk, 90, 1.))
    for k in range(tiers):
        t1 = (k + 1) / tiers
        ya = top + (base - h * .07 - top) * max(0, k / tiers - .08)
        yb = top + (base - h * .07 - top) * t1
        hw = h * wfac * (t1 ** .9) * rng.uniform(.9, 1.08) + 1
        droop = (yb - ya) * .35
        L = [(x, ya), (x - hw * .55, yb - droop * .6), (x - hw, yb + droop * .3), (x - hw * .55, yb + droop * .05), (x, yb + droop * .25)]
        R = [(x + hw * .55, yb + droop * .05), (x + hw, yb + droop * .3), (x + hw * .55, yb - droop * .6)]
        cv.obj([L + R], .5)
        cv.hair(C.hatch_poly(L, 25, 3.))
        cv.hair(C.hatch_poly([(x, ya), (x, yb + droop * .25)] + R, -25, 2.))
        cv.heavy([(x - hw * .9, yb + droop * .2), (x - hw * .55, yb + droop * .05), (x, yb + droop * .25),
                  (x + hw * .55, yb + droop * .05), (x + hw * .9, yb + droop * .2)])
    return cv.svg()


def _log_slab(cx, cy, rx, ry, depth, rng):
    """A cut log slab standing on edge, its sawn face toward the viewer: the bark rim runs back to
    the left (dark, furrowed in white), the face carries growth rings, a check and the pith."""
    o = []
    arc = [(cx - depth + rx * math.cos(t), cy + ry * math.sin(t)) for t in [PI / 2 + PI * k / 24 for k in range(25)]]
    body = [(cx, cy + ry)] + arc + [(cx, cy - ry)]
    o.append(_P(_d(body, True, .1), "#000", 1.))
    fur = []
    for k in range(1, 10):
        t = PI / 2 + PI * k / 10
        y = cy + ry * math.sin(t)
        x0 = cx - depth + rx * math.cos(t) + .8
        fur.append([(x0, y), (x0 + depth * .45, y + rng.uniform(-.7, .7)), (cx - rx * .2, y + rng.uniform(-.5, .5))])
    o.append(f'<path d="{_lines(fur, .1)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    face = _ell(cx, cy, rx, ry, 44)
    o.append(_P(_d(face, True, .1), "#fff", 1.5))
    rings = []
    n = max(4, int(rx / 1.7))
    ox, oy = rx * .14, -ry * .12
    for k in range(1, n):
        f = k / n
        rings.append([(cx + ox * (1 - f) + rx * f * math.cos(t) * (1 + .05 * math.sin(5 * t + k * 1.7)),
                       cy + oy * (1 - f) + ry * f * math.sin(t) * (1 + .05 * math.sin(5 * t + k * 1.7)))
                      for t in [2 * PI * j / 40 for j in range(41)]])
    o.append(_P(_lines(rings, .15), sw=.5))
    o.append(_P(_d([(cx + ox, cy + oy), (cx + rx * .62, cy + ry * .68)], tol=0), sw=1.))
    o.append(_P(_d(_ell(cx + ox, cy + oy, .9, .9, 8), True, 0), "#000"))
    # cast shadow on the right of the face's rim and on the grass
    o.append(_P(_d(_ell(cx, cy, rx + .7, ry + .7, 40, -.3, PI * .7), tol=.1), sw=1.5))
    return "".join(o)


def _snare(cx, cy, s):
    """Parker's egg: a little Timbers Army snare with crossed sticks. s ~ drum radius."""
    o = []
    hgt = s * .9
    top = _ell(cx, cy, s, s * .35, 28)
    body = [(cx - s, cy)] + [(cx + s * math.cos(t), cy + hgt + s * .35 * math.sin(t)) for t in
                             [PI - PI * k / 14 for k in range(15)]][::-1][::-1] + [(cx + s, cy)]
    body = [(cx - s, cy), (cx - s, cy + hgt)] + \
        [(cx + s * math.cos(t), cy + hgt + s * .35 * math.sin(t)) for t in [PI - PI * k / 14 for k in range(15)]] + \
        [(cx + s, cy)]
    o.append(_P(_d(body, True, .1), "#fff", 1.))
    o.append(_P(_lines(C.hatch_poly(body, 90, 1.5)), sw=.5))
    # tension rods
    rods = [[(cx + s * math.cos(t), cy + s * .35 * math.sin(t) + 1), (cx + s * math.cos(t), cy + hgt + s * .35 * math.sin(t) - 1)]
            for t in [PI * (k + .5) / 5 for k in range(5)]]
    o.append(_P(_lines(rods), "none", 1.))
    o.append(_P(_d(top, True, .1), "#fff", 1.))
    # sticks crossed over the head
    L = s * 2.1
    sticks = []
    for sgn in (-1, 1):
        a = -PI / 2 + sgn * .62
        x0, y0 = cx - sgn * s * .55, cy + s * .1
        sticks.append([(x0, y0), (x0 + L * math.cos(a), y0 + L * math.sin(a))])
    o.append(_P(_lines(sticks), "none", 1.5))
    for p in sticks:
        x1, y1 = p[1]
        o.append(_P(_d(_ell(x1, y1, 1.1, 1.1, 10), True, 0), "#000"))
    return "".join(o)


def _score(ctx):
    m = re.search(r"Last game\s+([WLD])\s+(\d+)\s*[–\-]\s*(\d+)", (ctx or {}).get("sample", ""))
    if not m:
        return "W", 1, 0
    return m.group(1), int(m.group(2)), int(m.group(3))


# ------------------------------------------------------------------------------------------------
# the vignette: everything drawn inside the field bbox and clipped to the field outline
# ------------------------------------------------------------------------------------------------


def _net(gx0, gx1, top, gy, bcx, bcy, br, pitch):
    """Diamond net lattice over the goal mouth, pushed outward round the ball (the bulge)."""
    out = []
    W, H = gx1 - gx0, gy - top
    span = W + H
    for sgn in (1, -1):
        c = -H
        while c <= W:
            pl = []
            for i in range(41):
                t = i / 40
                y = top + H * t
                x = gx0 + c + (H * t if sgn > 0 else H * (1 - t))
                if gx0 <= x <= gx1:
                    dx, dy = x - bcx, y - bcy
                    d = math.hypot(dx, dy)
                    R = br * 3.2
                    if 1e-6 < d < R:
                        push = (R - d) / R
                        f = 1 + push * push * 1.3 * br / max(d, br * .5)
                        x, y = bcx + dx * f, bcy + dy * f
                    y += H * .05 * math.sin(PI * min(1, max(0, (x - gx0) / W)))
                    pl.append((x, y))
                elif len(pl) > 1:
                    out.append(pl)
                    pl = []
                else:
                    pl = []
            if len(pl) > 1:
                out.append(pl)
            c += pitch
    return out


def vignette(bx, by, bw, bh, clip_d, ctx, seed=0, small=False):
    rng = random.Random(seed)
    res, gf, ga = _score(ctx)
    cid = _uid("v", bx, by, bw, bh, seed)
    o = [f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">']
    x1, y1 = bx + bw, by + bh
    hor = by + bh * (.58 if not small else .66)
    # sky: a heavy Portland sky in swelling burin lines with a bank of cloud
    cv = Canvas()
    burin_sky(cv, bx - 2, by - 2, bw + 4, hor - by + 2, seed, pitch=3.,
              banks=[(bx + bw * .3, by + (hor - by) * .62, bw * .42, (hor - by) * .32)] if not small else
              [(bx + bw * .25, by + (hor - by) * .7, bw * .4, (hor - by) * .4)])
    # pitch: mowed stripes in perspective; the dark stripes cut along the mowing, the light ones
    # stippled with grass tufts
    vx, vy = bx + bw / 2, hor - bh * 1.6
    cv.obj([[(bx - 2, hor), (x1 + 2, hor), (x1 + 2, y1 + 2), (bx - 2, y1 + 2)]], 0)
    for k in range(-16, 16):
        def at(kk, y):
            x0 = vx + kk * bw * .085
            return (vx + (x0 - vx) * (y - vy) / (hor - vy), y)
        if k % 2:
            for j in range(1, 5):
                f = k + j / 5
                cv.hair([at(f, hor), at(f, y1 + 2)])
        elif not small:
            for j in (1,):
                f = k + j / 2
                cv.hair([at(f, hor), at(f, y1 + 2)])
        if small and k % 2 == 0:
            yy = hor + 3
            while yy < y1:
                a, b = at(k, yy), at(k + 1, yy)
                n = int((b[0] - a[0]) / 9)
                for i in range(n):
                    gx = a[0] + (i + .5 + .3 * math.sin(yy * 3 + i)) * (b[0] - a[0]) / max(1, n)
                    s = .8 + (yy - hor) / bh * 2.
                    cv.hair([(gx - s * .3, yy), (gx, yy - s)])
                yy += 4.5 + (y1 - yy) / bh * 5
    o.append(cv.svg())
    if not small:
        mx, mh = bx + bw * .73, bh * .36
        mt = [(mx - mh * 1.9, hor), (mx - mh * .4, hor - mh * .8), (mx - mh * .12, hor - mh * .97),
              (mx, hor - mh), (mx + mh * .2, hor - mh * .9), (mx + mh * 2., hor)]
        o.append(_P(_d(mt, True, 0), "#fff", .5))
        flank = [(mx, hor - mh), (mx + mh * .2, hor - mh * .9), (mx + mh * 2., hor), (mx + mh * .25, hor),
                 (mx + mh * .15, hor - mh * .45), (mx - mh * .05, hor - mh * .72)]
        o.append(_P(_lines(C.hatch_poly(flank, 62, 2.)), sw=.5))
        snow = [(mx - mh * 1.9, hor), (mx - mh * 1.1, hor - mh * .42), (mx - mh * .8, hor - mh * .5),
                (mx - mh * .6, hor - mh * .4), (mx - mh * .35, hor - mh * .58), (mx - mh * .1, hor - mh * .46),
                (mx + mh * .25, hor)]
        o.append(_P(_lines(C.hatch_poly(snow, 0, 2)), sw=.5))
        o.append(_P(_lines([[(mx - mh * .3, hor - mh * .7), (mx - mh * .55, hor - mh * .52)],
                            [(mx + mh * .02, hor - mh * .9), (mx - mh * .1, hor - mh * .62)]]), sw=.5))
        ridge = [(bx, hor + 1)]
        x = bx
        while x < x1:
            hh = rng.uniform(.035, .075) * bh
            ridge += [(x + 1.7, hor - hh), (x + 3.4, hor - hh * .4)]
            x += rng.uniform(3.4, 5.5)
        ridge += [(x1, hor + 1)]
        o.append(_P(_d(ridge, True, 0), "#000") + _P(_d(ridge[1:-1], False, 0), sw=.5))
    o.append(_P(f"M{_n(bx)},{_n(hor)}h{_n(bw)}", sw=1.))
    gw = bw * (.5 if not small else .62)
    gx0, gx1 = vx - gw / 2, vx + gw / 2
    gh = bh * (.33 if not small else .48)
    gy = hor + bh * (.07 if not small else .05)
    box = [(gx0 - gw * .14, gy), (gx0 - gw * .22, y1 - bh * .14), (gx1 + gw * .22, y1 - bh * .14), (gx1 + gw * .14, gy)]
    chalk = [[(bx, gy), (x1, gy)], box]
    o.append(f'<path d="{_lines(chalk)}" fill="none" stroke="#000" stroke-width="3"/>')
    o.append(f'<path d="{_lines(chalk)}" fill="none" stroke="#fff" stroke-width="1.5"/>')
    dep = gh * .3
    back_top = gy - gh + dep * .15
    inset = gw * .06
    mouth = [(gx0, gy), (gx0, gy - gh), (gx1, gy - gh), (gx1, gy)]
    o.append(_P(_d(mouth, True, 0), "#000"))
    br = max(4.5, min(bw, bh) * (.08 if not small else .17))
    bcx = gx1 - gw * .24 if not small else vx + gw * .13
    bcy = gy - gh * .62 if not small else gy - gh * .52
    pitch = 5. if not small else 3.
    net = _net(gx0, gx1, gy - gh, gy, bcx, bcy, br, pitch)
    o.append(f'<path d="{_lines(net, .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    st = [[(gx0 + inset, gy - dep * .3), (gx0 + inset, back_top), (gx1 - inset, back_top), (gx1 - inset, gy - dep * .3)]]
    o.append(f'<path d="{_lines(st)}" fill="none" stroke="#fff" stroke-width="1.5"/>')
    pw = max(2., bw * .014)
    frame = [(gx0 - pw, gy + .5), (gx0 - pw, gy - gh - pw), (gx1 + pw, gy - gh - pw), (gx1 + pw, gy + .5),
             (gx1, gy + .5), (gx1, gy - gh), (gx0, gy - gh), (gx0, gy + .5)]
    o.append(_P(_d(frame, True, 0), "#fff", .5))
    o.append(f'<path d="M{_n(gx0)},{_n(gy)}V{_n(gy - gh)}H{_n(gx1)}V{_n(gy)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(_P(_lines(C.hatch_poly([(gx0 - pw, gy + .8), (gx1 + pw, gy + .8), (gx1 + pw + gw * .1, gy + 3.5), (gx0 - pw + gw * .1, gy + 3.5)], 0, 1.5)), sw=1.))
    if not small:
        tr = []
        for k in (-.45, 0., .45):
            p0 = (bcx - br * 1.15, bcy + k * br)
            pts = []
            for i in range(13):
                t = i / 12
                pts.append((p0[0] - t * bw * (.3 - abs(k) * .12), p0[1] + t * t * bh * .2 + k * br * t * .6))
            tr.append(pts)
        o.append(f'<path d="{_lines(tr, .2)}" fill="none" stroke="#000" stroke-width="2"/>')
        o.append(f'<path d="{_lines(tr, .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    o.append(football(bcx, bcy, br, (.5 + seed % 7 * .2, .35, .3)))
    if not small:
        base = hor + bh * .12
        for (fx, fh, fd) in ((bx + bw * .1, bh * .58, "G"), (x1 - bw * .09, bh * .52, "G")):
            o.append(_fir_svg(fx, base + (fh - bh * .4) * .3, fh, rng, fd, .25))
        nlog = max(1, min(4, gf)) if res == "W" else 1
        lr = min(bh * .09, bw * .08)
        for k in range(nlog - 1, -1, -1):
            lx = bx + bw * .25 + k * lr * 1.25
            ly = y1 - bh * .2 + k * lr * .18
            o.append(_log_slab(lx, ly, lr * .8, lr, lr * .55, rng))
        o.append(_snare(x1 - bw * .3, y1 - bh * .2, max(4.5, bh * .05)))
    else:
        o.append(_snare(bx + bw * .22, y1 - bh * .22, max(3.5, bh * .07)))
    o.append("</g>")
    return "".join(o)


def _result(ctx):
    res, gf, ga = _score(ctx)
    m = re.search(r"Last game\s+[WLD]\s+\d+\s*[–\-]\s*\d+\s+(at|vs\.?)\s+([A-Za-z .]+?)\s*·", (ctx or {}).get("sample", ""))
    opp = (m.group(2).upper().replace(" FC", "") if m else "")
    return {"W": "WON", "L": "LOST", "D": "DREW"}[res] + f" {gf}-{ga}" + (f" · {('AT' if m.group(1) == 'at' else 'VS')} {opp}" if m else "")


def tablet(tx, ty, tw, th, ctx):
    o = [black_ground((tx, ty, tw, th), 11, dens=0)]
    txt = _result(ctx)
    cap = min(th * .5, 12.)
    W_ = text_width(txt, cap)
    if W_ > tw - 10:
        cap *= (tw - 10) / W_
        W_ = text_width(txt, cap)
    o.append(f'<path d="M{_n(tx + tw / 2 - W_ / 2 - 5)},{_n(ty + th / 2 - cap / 2 - 4)}h{_n(W_ + 10)}v{_n(cap + 8)}h{_n(-W_ - 10)}z" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(letter_svg(txt, tx + tw / 2 - W_ / 2, ty + th / 2 - cap / 2, cap))
    return "".join(o)


def motif(cx, cy, r, i, seed):
    o = [black_ground(E(cx, cy, r + 1, r + 1, 32)[:-1], 13, dens=0)]
    if i == 0:
        o.append(_fir_svg(cx, cy + r * .82, r * 1.6, random.Random(seed), "G", .3))
    else:
        o.append(football(cx, cy, r * .72, (.9, .4, .1)))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = (sum(map(ord, ctx.get("date", ""))) + 7) % 9973
    small = h < 110
    spec = dict(scene=lambda x, y, ww, hh, clip, lv: vignette(x, y, ww, hh, clip, ctx, seed, small),
                motif=lambda cx, cy, r, i: motif(cx, cy, r, i, seed),
                tablet=lambda tx, ty, tw, th: tablet(tx, ty, tw, th, ctx),
                ribbon="PORTLAND TIMBERS", seed=seed, shape="oval")
    return compose(w, h, ctx, spec)
