"""music-01 "Put this record on" (records for this morning). King-tier plate.

Band/medium: the medallion looks down on a turntable: a walnut plinth cut in swelling grain lines
around two knots, a platter rim knurled with strobe marks, a black LP whose grooves are cut in
white with two sheen sectors and track gaps, a rose-engine (guilloche) label carrying tonight's
moon at its true phase and the classic pick's year, and a tonearm set down on the lead-in.
Tall: the arch opens on a parlour at night - an arched window with the moon and a cloud bank,
a draped curtain, a vine-striped wallpaper falling into shadow, a walnut cabinet gramophone with a
brass horn modelled in petal seams, and his dog listening at the bell, fur cut in bulino.
Fine scroll grown from one stem source packs the stippled black ground; corner roundels hold a
ride cymbal and a lyre; the ribbon reads PUT THIS RECORD ON; the pedestal tablet is a bar of
swing ride rhythm cut in white on black.
Easter eggs: Parker's drumsticks lying by the record (and on the rug in the parlour); the moon on
the label is tonight's moon.
"""
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
    """O(n)-ish simplification: extend each chord from the last kept point while the newest
    skipped point and the middle skipped point both stay within tol of it."""
    n = len(pts)
    if n < 3:
        return pts
    out = [pts[0]]
    a = 0
    ax, ay = pts[0]
    for i in range(1, n - 1):
        bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        L = (dx * dx + dy * dy) ** .5
        if L < 1e-9:
            continue
        px, py = pts[i]
        mx, my = pts[(a + i + 1) // 2]
        lim = tol * L
        if abs((px - ax) * dy - (py - ay) * dx) > lim or abs((mx - ax) * dy - (my - ay) * dx) > lim:
            out.append(pts[i])
            a = i
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
                    pen.add(poly if C._area(poly) >= 0 else poly[::-1], True, .45)
            sw = f' stroke="#000" stroke-width="{_n(ow * 4)}"' if ow else ' stroke="none"'
            res.append(f'<path{T} d="{pen.d()}" fill="#fff"{sw}/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _Pen()
                for pl in out[w]:
                    pen.add(pl, False, .4)
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
    return (f'<defs><pattern id="gkS" width="36" height="36" patternUnits="userSpaceOnUse">'
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
            if k < .55 and STYLE[0] == "thai":
                # a Thai cloud scroll: a curl with two smaller curls budding off it
                rr = cell * rng.uniform(.18, .26)
                sg = rng.choice((-1, 1))
                a0 = rng.uniform(0, TAU)
                L1.append(k_spiral(cx, cy, rr, a0, 1.3, sg, .25, 18))
                for j in (-1, 1):
                    bx_ = cx + j * rr * 1.5
                    L1.append(k_spiral(bx_, cy + rr * .35, rr * .55, a0 + PI * (j > 0), 1.1, -sg * j, .3, 12))
            elif k < .55:
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
    return (f'<path d="{d}" fill="#000" stroke="none"/><path d="{d}" fill="url(#gkS)" stroke="none"/>'
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
    M_ = max(16, int(L / 1.8))
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

STYLE = ["acanthus"]


def small_leaf(cv, x, y, ang, L, curl=1, seed=0, lobes=None):
    """A small acanthus leaf for fine scroll (L about 5-16 px); in the Thai style (STYLE[0] ==
    "thai") a kranok flame: narrow, lobed on its back, its tip hooked hard over."""
    lobes = lobes or (2 if L < 9 else 3)
    if STYLE[0] == "thai":
        return acanthus_leaf(cv, x, y, ang, L * 1.1, L * .27, bend=curl * .5, curl=curl * 2.4, lobes=lobes + 1,
                             seed=seed, pitch=1.5 if L < 13 else 2., inner_lobes=1)
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
    sw = with_heading(resample(pts, 2.2))
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
    STYLE[0] = spec.get("style", "acanthus")
    o = []
    avoid = []
    cv = Canvas()
    roots = []
    fronts = []           # svg drawn over the scroll
    mot = spec.get("motif")
    M = 3.
    if h < 110 and spec.get("form") == "tailpiece":
        return _tailpiece(w, h, ctx, spec)
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
    elif h <= spec.get("medium_max", 260):
        level = 1
        mh = h - 26
        mw = min(w * spec.get("mw", .44), mh * 1.45)
        my = h / 2
        shape = spec.get("shape", "oval")
        if shape == "circle":
            mh = mw = min(mh, w * .62)
            med = ellipse_poly(w / 2, my, mw / 2, mh / 2, 120)
        elif shape == "arch":
            med = arch_poly(w / 2 - mw / 2, my - mh / 2, mw, mh)
        elif shape == "cut":
            med = cut_poly(w / 2 - mw / 2, my - mh / 2, mw, mh, min(mw, mh) * .16)
        else:
            med = ellipse_poly(w / 2, my, mw / 2, mh / 2, 96)
        ring, outer = medallion_ring(med, 1.5)
        fronts.append(spec["scene"](w / 2 - mw / 2, my - mh / 2, mw, mh, _d(med, True, 0), 1))
        fronts.append(ring)
        avoid.append(_poly_contains_margin(med, 11))
        if spec.get("ribbon") and spec.get("med_ribbon") and h >= 220:
            rb_h = min(20., h * .07)
            ry = my + mh / 2 - rb_h * .9
            fronts.append(ribbon(w / 2, ry, min(w * .8, mw * 1.6), rb_h, spec["ribbon"], .03, seed))
            avoid.append(lambda a, b, ry=ry, rw=min(w * .8, mw * 1.6): abs(b - ry) < rb_h * .9 + 4 and abs(a - w / 2) < rw / 2 + 4)
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
    fixed = [black_ground((0, 0, w, h), seed, dens=spec.get("ground_dens", .12)), border_lines] + fronts
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


def _tailpiece(w, h, ctx, spec):
    """A tailpiece: a small shaped device (arch, oval or banner lozenge) holding the scene, with
    two sprays of fine scroll on stippled black tapering out to beaded drops; the whole spans
    about 56% of the width and stands free on the page."""
    seed = spec.get("seed", 1)
    STYLE[0] = spec.get("style", "acanthus")
    cx, cy = w / 2, h / 2
    tw = min(w * spec.get("tail_w", .58), max(h * 7.5, w * .4))
    shape = spec.get("tail_shape", "arch")
    sh = h - 10
    if shape == "banner":
        sw = min(tw * .56, h * 4.2)
        hh = sh / 2
        med = [(cx - sw / 2, cy)] + [(cx - sw / 2 + hh * .9 * (1 - _m.cos(PI / 2 * i / 8)), cy - hh * _m.sin(PI / 2 * i / 8)) for i in range(1, 9)] \
            + [(cx + sw / 2 - hh * .9 * (1 - _m.cos(PI / 2 * i / 8)), cy - hh * _m.sin(PI / 2 * i / 8)) for i in range(8, 0, -1)] \
            + [(cx + sw / 2, cy)] + [(cx + sw / 2 - hh * .9 * (1 - _m.cos(PI / 2 * i / 8)), cy + hh * _m.sin(PI / 2 * i / 8)) for i in range(1, 9)] \
            + [(cx - sw / 2 + hh * .9 * (1 - _m.cos(PI / 2 * i / 8)), cy + hh * _m.sin(PI / 2 * i / 8)) for i in range(8, 0, -1)]
    elif shape == "oval":
        sw = min(tw * .4, sh * 1.7)
        med = ellipse_poly(cx, cy, sw / 2, sh / 2, 72)
    else:
        sw = min(tw * .36, sh * 1.25)
        med = arch_poly(cx - sw / 2, cy - sh / 2, sw, sh, 32)
    ring, outer = medallion_ring(med, 1.)
    o = []
    # the two sprays: lenses of black ground from the device's flanks out to the tips
    lens = []
    for sx in (-1, 1):
        x0 = cx + sx * (sw / 2 - 4)
        L = tw / 2 - sw / 2 + 4
        top, bot = [], []
        for i in range(25):
            t = i / 24
            hgt = sh * .4 * (1 - t) ** .85 + .6
            sweep = -sh * .12 * t * t
            xx = x0 + sx * L * t
            top.append((xx, cy - hgt + sweep))
            bot.append((xx, cy + hgt * .8 + sweep))
        poly = top + bot[::-1]
        if sx < 0:
            poly = poly[::-1]
        lens.append(poly)
    for k, poly in enumerate(lens):
        o.append(black_ground(poly, seed + k, dens=.3))
        o.append(f'<path d="{_d(poly, True, 0)}" fill="none" stroke="#000" stroke-width="1.5"/>')
        o.append(f'<path d="{_d(offset_poly(poly, 2.2), True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    cv = Canvas()
    roots = []
    for sx in (-1, 1):
        roots.append((cx + sx * (sw / 2 + 6), cy, 0. if sx > 0 else PI, -sx))

    keep_out = _poly_contains_margin(med, 7)
    inner = [offset_poly(p, -2.5) for p in lens]

    def ok(a, b):
        return any(pt_in(a, b, p) for p in inner) and not keep_out(a, b)
    marks = []
    scroll_field(cv, 0, 0, w, h, roots, seed=seed, rmax=min(13., h * .2), rmin=max(4.5, h * .075), inside_fn=ok,
                 leafk=spec.get("leafk", 1.), marks=marks)
    o.append(cv.svg())
    for sx in (-1, 1):
        tx = cx + sx * (tw / 2 + 3)
        ty = cy - sh * .12 + .6
        o.append(f'<path d="{_d(_ell(tx, ty, 3., 3., 14)[:-1], True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{_d(_ell(tx + sx * 1., ty + .6, 1.2, 1.2, 10)[:-1], True, 0)}" fill="#000"/>')
    o.append(spec["scene"](cx - sw / 2, cy - sh / 2, sw, sh, _d(med, True, 0), -1))
    o.append(ring)
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


# ---------------------------------------------------------------------------------------------
# landscape pieces shared by the plates: Mt. Hood and the Douglas fir
# ---------------------------------------------------------------------------------------------

def mountain(cv, x0, x1, base, px, ph, seed=0, snow=.6, forest=True, light=-1):
    """Mt. Hood seen from the south-west: the steep cone with Illumination Rock on the west
    shoulder; the lit face left almost white, cut only by glacier ribs with their shadow ticks;
    the shadowed east face cut in fall lines that swell from hair to 1 px below the snow line;
    rock strata under the snow; a dark fir apron along the foot. Returns the outline polygon."""
    rng = _r.Random(seed)
    py = base - ph
    wl, wr = ph * 1.35, ph * 1.55

    def lp(t):
        return (px - wl * t ** 1.7, py + ph * t - ph * .05 * _m.exp(-((t - .38) / .06) ** 2))

    def rp(t):
        return (px + wr * t ** 1.55, py + ph * t - ph * .035 * _m.exp(-((t - .5) / .07) ** 2))
    L = [lp(i / 30) for i in range(31)]
    R = [rp(i / 30) for i in range(31)]
    poly = L[::-1] + R[1:]
    cv.obj([poly], 1.)
    ys = py + ph * snow
    # east face: fall lines from the summit ridge, crowding toward the shadowed foot
    n = max(10, int(wr * .75 / 2.)) if ph >= 70 else 0
    if ph < 70:
        east = [(px + wr * .06 * t, py + ph * t) for t in [i / 12 for i in range(13)]][::-1] + R[1:]
        cv.hair(C.hatch_poly(east, 62, 2.))
        cv.hair(clip_in(C.hatch_poly(east, -20, 2.5), [(px - wr, ys), (px + 2 * wr, ys), (px + 2 * wr, base + 2), (px - wr, base + 2)]))
    for k in range(1, n + 1):
        f = k / n
        t0 = (.02 if k % 4 == 0 else (.1 if k % 2 == 0 else .22)) if ph >= 70 else (.12 if k % 2 else .3)
        pts = []
        for i in range(17):
            t = t0 + (1 - t0) * i / 16
            xr = rp(t)[0]
            xm = px + wr * .06 * t
            pts.append((xm + (xr - xm) * f * (.98 if f < 1 else .96) + _m.sin(t * 6 + k) * .5, py + ph * t))
        up = [p for p in pts if p[1] < ys]
        dn = [p for p in pts if p[1] >= ys - 3]
        if len(up) > 1:
            cv.hair(up)
        if len(dn) > 1:
            (cv.line if k % 3 == 0 else cv.hair)(dn)
    # the ridge between the faces
    cv.line([(px + wr * .06 * t + _m.sin(t * 9) * .5, py + ph * t) for t in [i / 12 for i in range(13)]])
    # west face: glacier ribs with short shadow ticks on their east side
    for k, f in enumerate((.18, .36, .55, .74)):
        a = lp((.04 + .12 * f) if ph >= 70 else (.3 + .2 * f))
        b = lp(1.)
        b = (px - wl * .78 * f, base)
        rib = [(a[0] + (b[0] - a[0]) * t + _m.sin(t * 7 + k) * ph * .012, a[1] + (b[1] - a[1]) * t) for t in [i / 14 for i in range(15)]]
        cv.hair(rib)
        for i in range(2, 14, (1 if k % 2 else 2) if ph >= 70 else 3):
            q = rib[i]
            ln = 1.5 + 2.5 * (i / 14)
            cv.hair([q, (q[0] + ln, q[1] + ln * .5)])
    # wind-scoured snow on the lit face: broken lines parallel to the west skyline
    for k in range(1, 7 if ph >= 70 else 1):
        d = k * ph * .06
        seg = []
        for i in range(25):
            t = .06 + .9 * i / 24
            q = lp(t)
            qx = q[0] + d * (1.2 - t * .4)
            if qx > px + wr * .06 * t - 2 or q[1] > ys:
                if len(seg) > 1:
                    cv.hair(seg)
                seg = []
                continue
            if (i + k) % 5 == 0:
                if len(seg) > 1:
                    cv.hair(seg)
                seg = []
            seg.append((qx, q[1]))
        if len(seg) > 1:
            cv.hair(seg)
    # rock strata below the snow line on the lit face
    yy = ys + 2
    while yy < base - 1:
        t = (yy - py) / ph
        xa, xb = lp(min(1., t))[0], px + wr * .06 * t
        xx = xa + 1
        while xx < xb - 2:
            ln = rng.uniform(3, 9)
            cv.hair([(xx, yy + rng.uniform(-.4, .4)), (min(xb, xx + ln), yy + rng.uniform(-.6, .6))])
            xx += ln + rng.uniform(2, 6)
        yy += 2.5
    if forest:
        fy = base - ph * .1
        fp = [(x0, fy + 2)]
        x = x0
        while x < x1:
            hh = rng.uniform(2.5, 5.5)
            fp += [(x + 1.3, fy - hh), (x + 2.6, fy + rng.uniform(-.5, 1.))]
            x += 2.6
        fp += [(x1, base + 1), (x0, base + 1)]
        cv.obj([fp], .5)
        cv.hair(C.hatch_poly(fp, 70, 2.))
        cv.hair(C.hatch_poly(fp, -60, 3.))
        cv.line([p for p in fp[1:-2]])
    return poly


def fir(cv, x, base, h, rng, wfac=.36, snow=False):
    """A Douglas fir carved in relief: drooping tiers lit on the upper left (open cuts),
    shadowed on the lower right (close cuts, a heavy shade line under each bough); with snow,
    each bough carries a white cap."""
    tiers = max(4, int(h / 11))
    top = base - h * .93
    trunk = [(x - h * .025, base - h * .1), (x + h * .025, base - h * .1), (x + h * .035, base), (x - h * .035, base)]
    cv.obj([trunk], .5)
    cv.line(C.hatch_poly(trunk, 90, 1.5))
    for k in range(tiers):
        t1 = (k + 1) / tiers
        ya = top + (base - h * .07 - top) * max(0, k / tiers - .08)
        yb = top + (base - h * .07 - top) * t1
        hw = h * wfac * (t1 ** .9) * rng.uniform(.9, 1.08) + 1
        droop = (yb - ya) * .35
        Lf = [(x, ya), (x - hw * .55, yb - droop * .6), (x - hw, yb + droop * .3), (x - hw * .55, yb + droop * .05), (x, yb + droop * .25)]
        Rf = [(x + hw * .55, yb + droop * .05), (x + hw, yb + droop * .3), (x + hw * .55, yb - droop * .6)]
        cv.obj([Lf + Rf], .5)
        if snow:
            cv.hair(C.hatch_poly([(x, ya + (yb - ya) * .45)] + Lf[2:], 25, 3.))
            cv.line(C.hatch_poly([(x, ya + (yb - ya) * .4), (x, yb + droop * .25)] + Rf, -25, 2.))
        else:
            cv.hair(C.hatch_poly(Lf, 25, 3.))
            cv.hair(C.hatch_poly([(x, ya), (x, yb + droop * .25)] + Rf, -25, 2.))
        cv.heavy([(x - hw * .9, yb + droop * .2), (x - hw * .55, yb + droop * .05), (x, yb + droop * .25),
                  (x + hw * .55, yb + droop * .05), (x + hw * .9, yb + droop * .2)])


# ---------------------------------------------------------------------------------------------
# the free-standing vignette: a shaped scene whose edge dissolves (Bewick), framed only by
# devices built from the page's own subject
# ---------------------------------------------------------------------------------------------

def ragged(poly, amp=3., seed=0):
    """Wobble a closed shape's edge in and out so line work ends raggedly, the way a vignette's
    tone dissolves into the paper."""
    rng = _r.Random(seed)
    ph = [rng.uniform(0, TAU) for _ in range(4)]
    pts = resample(poly + [poly[0]], 2.)[:-1]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a = TAU * i / n
        d = amp * (.45 * _m.sin(5 * a + ph[0]) + .3 * _m.sin(13 * a + ph[1]) + .25 * _m.sin(29 * a + ph[2])
                   + .35 * _m.sin(61 * a + ph[3]) * rng.uniform(.3, 1.))
        dx, dy = x - cx, y - cy
        L = _m.hypot(dx, dy) or 1.
        out.append((x + dx / L * d, y + dy / L * d))
    return out


def shape_poly(shape, x, y, w, h):
    if shape in ("oval", "roundel"):
        return ellipse_poly(x + w / 2, y + h / 2, w / 2, h / 2, 120)
    if shape == "arch":
        return arch_poly(x, y, w, h, 48)
    if shape == "lunette":
        return [(x + w / 2 - w / 2 * _m.cos(PI * i / 48), y + h - h * _m.sin(PI * i / 48)) for i in range(49)]
    if shape == "cut":
        return cut_poly(x, y, w, h, min(w, h) * .14)
    return ellipse_poly(x + w / 2, y + h / 2, w / 2, h / 2, 120)


def vignette_plate(w, h, ctx, spec):
    """spec: shape, aspect (w/h of the shape), scene(x, y, w, h, clip_d, level) -> svg, frame(poly,
    (x, y, w, h)) -> (back_svg, front_svg), seed, rag (edge amplitude), margins (l, t, r, b)."""
    seed = spec.get("seed", 1)
    STYLE[0] = spec.get("style", "acanthus")
    ml, mt, mr, mb = spec.get("margins", (4, 4, 4, 4))
    sh = h - mt - mb
    sw = min(w - ml - mr, sh * spec.get("aspect", 1.6))
    x = ml + (w - ml - mr - sw) / 2
    y = mt
    poly = shape_poly(spec.get("shape", "oval"), x, y, sw, sh)
    rag = ragged(poly, spec.get("rag", 3.), seed)
    back, front = ("", "")
    if spec.get("frame"):
        back, front = spec["frame"](poly, (x, y, sw, sh))
    body = spec["scene"](x, y, sw, sh, _d(rag, True, 0), spec.get("level", 1))
    return plate_doc(w, h, back + body + front, seed)


# walnut and other woods: swelling grain lines bowing round knots
def wood(cv, x, y, w, h, seed, pitch=2., knots=2, vertical=False, poly=None, outline=0.):
    rng = random.Random(seed)
    if poly is None:
        poly = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([poly], outline)
    L_, B_ = (h, w) if vertical else (w, h)
    ks = [(rng.uniform(.15, .85) * L_, rng.uniform(.2, .8) * B_, rng.uniform(4, 9) * (B_ / 120) ** .3) for _ in range(knots)]
    ph = rng.uniform(0, 6)
    b = -6.
    while b < B_ + 6:
        cur, heavy = [], None
        u = -4.
        while u < L_ + 4:
            v = b + 2.2 * math.sin(u / 53. + b / 37. + ph) + .8 * math.sin(u / 17. + b * .21)
            for kx, ky, ksz in ks:
                du = (u - kx) / (ksz * 2.6)
                g = math.exp(-du * du)
                dv = b - ky
                v += math.copysign(ksz * 1.3, dv) * g * math.exp(-abs(dv) / (ksz * 1.6))
            nz = math.sin(b * .53 + .3 * math.sin(u / 29.) + ph) + .6 * math.sin(u / 41. - b * .11)
            hv = nz > .55
            p = (x + v, y + u) if vertical else (x + u, y + v)
            if heavy is None or hv == heavy:
                cur.append(p)
            else:
                cur.append(p)
                (cv.line if heavy else cv.hair)(cur)
                cur = [p]
            heavy = hv
            u += 3.
        if len(cur) > 1:
            (cv.line if heavy else cv.hair)(cur)
        b += pitch
    for kx, ky, ksz in ks:
        cx, cy = (x + ky, y + kx) if vertical else (x + kx, y + ky)
        ex, ey = (ksz * .55, ksz) if vertical else (ksz, ksz * .55)
        for f in (.25, .55, .85):
            cv.line(E(cx, cy, ex * f, ey * f, 18))
    return ks
# ==== end of studio kit ====

import re
import datetime


def _P(d, fill="none", sw=None, stroke="#000", extra=""):
    s = f' stroke="{stroke}" stroke-width="{_n(sw)}"' if sw else ' stroke="none"'
    return f'<path d="{d}" fill="{fill}"{s}{extra}/>'


def _circ(cx, cy, r):
    return (f"M{_n(cx - r)},{_n(cy)}a{_n(r)},{_n(r)} 0 1,0 {_n(2 * r)},0"
            f"a{_n(r)},{_n(r)} 0 1,0 {_n(-2 * r)},0z")


def _arc(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    big = 1 if (a1 - a0) % (2 * PI) > PI else 0
    return f"M{_n(x0)},{_n(y0)}A{_n(r)},{_n(r)} 0 {big},1 {_n(x1)},{_n(y1)}"


def _moon_phase(date):
    try:
        d = datetime.datetime.strptime(date[:10], "%Y-%m-%d") + datetime.timedelta(hours=12)
    except Exception:
        return .3
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    return ((d - ref).total_seconds() / 86400. / 29.530588) % 1.


def _year(ctx):
    m = re.search(r"classic.{0,90}?\b(19\d\d|20\d\d)\b", (ctx or {}).get("sample", "") or "")
    return m.group(1) if m else "33"


def moon(cv, x, y, r, phase, pitch=1.5):
    """The moon at its phase: the dark limb cut in curved lines that follow the sphere (heavier
    toward the far edge), the lit part clear with a few stippled seas."""
    cv.obj([E(x, y, r, r, 28)[:-1]], 1.)
    k = math.cos(phase * TAU)
    waxing = phase < .5
    yy = -r + pitch * .5
    while yy <= r:
        hw = math.sqrt(max(0., r * r - yy * yy))
        term = hw * k
        a0, a1 = (-hw, term) if waxing else (-term, hw)
        if a1 - a0 > .8:
            seg = [(x + a0 + (a1 - a0) * i / 6 + .3, y + yy + .35 * math.sin(i * .9) * (r > 8)) for i in range(7)]
            far = a0 if waxing else a1
            (cv.line if abs(far) > hw * .5 and a1 - a0 > hw * .5 else cv.hair)(seg)
        yy += pitch
    if r > 5:
        for sx, sy, sr in ((.28, -.3, .2), (-.18, .12, .16), (.34, .34, .13), (-.3, -.38, .1)):
            px = x + sx * r
            if (px - x > -r * k) if waxing else (px - x < r * k):
                for j in range(5):
                    a = TAU * j / 5 + sx
                    q = (px + sr * r * .6 * math.cos(a), y + sy * r + sr * r * .6 * math.sin(a))
                    cv.hair([q, (q[0] + .6, q[1] + .2)])


# ------------------------------------------------------------------------------------------
# turned objects
# ------------------------------------------------------------------------------------------

def drumstick(cv, x0, y0, x1, y1, w=5.):
    """A turned hickory stick from butt to tip: shoulder taper, olive bead, grain lines along it
    and a shade line down one side."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    vx, vy = -uy, ux

    def hw(t):
        return w / 2 * (1 - .62 * C._smooth(.62, .95, t))
    n = 28
    ts = [i / n * .95 for i in range(n + 1)]
    L_ = [(x0 + ux * L * t + vx * hw(t), y0 + uy * L * t + vy * hw(t)) for t in ts]
    R_ = [(x0 + ux * L * t - vx * hw(t), y0 + uy * L * t - vy * hw(t)) for t in ts]
    tx, ty = x0 + ux * L * .965, y0 + uy * L * .965
    a, b = w * .5, w * .33
    tip = [(tx + ux * a * math.cos(t) + vx * b * math.sin(t), ty + uy * a * math.cos(t) + vy * b * math.sin(t))
           for t in [TAU * i / 16 for i in range(16)]]
    cv.obj([L_ + R_[::-1]], 1. if w > 2.5 else .5)
    if w > 2.5:
        for f in (-.7, -.4, -.1):
            cv.hair([(x0 + ux * L * t + vx * hw(t) * f, y0 + uy * L * t + vy * hw(t) * f) for t in ts[1:-2]])
        cv.line([(x0 + ux * L * t - vx * hw(t) * .72, y0 + uy * L * t - vy * hw(t) * .72) for t in ts[1:-1]])
        cv.hair([(x0 + vx * hw(0) * .9, y0 + vy * hw(0) * .9), (x0 - vx * hw(0) * .9, y0 - vy * hw(0) * .9)])
    cv.obj([tip], 1. if w > 2.5 else .5)
    if w > 2.5:
        cv.hair([(tx - ux * a * .5 - vx * b * .45, ty - uy * a * .5 - vy * b * .45),
                 (tx + ux * a * .5 - vx * b * .45, ty + uy * a * .5 - vy * b * .45)])


def tonearm(cv, px, py, nx, ny, s=1.):
    """A tonearm pivoting at (px, py) and resting its stylus at (nx, ny): counterweight with
    knurling, S-bowed tube with a highlight, headshell with finger lift, pivot housing turned
    in rings."""
    ang = math.atan2(ny - py, nx - px)
    L = math.hypot(nx - px, ny - py)
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux

    def P(a, b):
        return (px + ux * a + vx * b, py + uy * a + vy * b)
    rr = 7 * s
    cv.obj([E(px + 1.5 * s, py + 2 * s, rr + 1, rr + 1, 32)[:-1]], 0)
    cv.line(C.hatch_poly(E(px + 1.5 * s, py + 2 * s, rr + 1, rr + 1, 24)[:-1], 45, 1.5))
    cw = [P(-7 * s, 5 * s), P(-19 * s, 5 * s), P(-19 * s, -5 * s), P(-7 * s, -5 * s)]
    cv.obj([cw], 1.)
    t = 8.5
    while t < 19:
        cv.hair([P(-t * s, 5 * s), P(-t * s, -5 * s)])
        t += 1.5 / s if s < 1 else 1.5
    cv.heavy([P(-7 * s, 3.8 * s), P(-19 * s, 3.8 * s)])
    hw = 2.1 * s
    spine = [P(L * .86 * i / 30, math.sin(i / 30 * PI) * L * .07) for i in range(31)]
    left = [(x + vx * hw, y + vy * hw) for x, y in spine]
    right = [(x - vx * hw, y - vy * hw) for x, y in spine]
    cv.obj([left + right[::-1]], 1.)
    cv.line([(x - vx * hw * .5, y - vy * hw * .5) for x, y in spine])
    if s >= .8:
        cv.hair([(x - vx * hw * .1, y - vy * hw * .1) for x, y in spine])
    ex, ey = spine[-1]
    hs = 5 * s
    a2 = ang + .4
    u2, v2 = (math.cos(a2), math.sin(a2)), (-math.sin(a2), math.cos(a2))

    def Q(a, b):
        return (ex + u2[0] * a + v2[0] * b, ey + u2[1] * a + v2[1] * b)
    shell = [Q(0, hs * .6), Q(hs * 2.5, hs * .85), Q(hs * 2.5, -hs * .85), Q(0, -hs * .6)]
    cv.obj([shell], 1.)
    cv.hair(C.hatch_poly(shell, math.degrees(a2), 1.5))
    cv.heavy([shell[1], shell[2]])
    cv.line([Q(hs * 1.1, -hs * .8), Q(hs * 1.5, -hs * 1.8), Q(hs * 2.2, -hs * 2.0)])
    cv.obj([E(px, py, rr, rr, 36)[:-1]], 1.)
    q = rr - 1.5
    while q > 1.6:
        cv.hair(E(px, py, q, q, 28))
        q -= 1.5
    cv.heavy(E(px, py, rr - .6, rr - .6, 24, PI * .1, PI * .9))
    cv.obj([E(px, py, 2.2 * s + .5, 2.2 * s + .5, 12)[:-1]], 1.)
    cv.line(E(px, py, 1. * s, 1. * s, 8))


# ------------------------------------------------------------------------------------------
# walnut: swelling grain lines bowing round knots (a real texture, not a ruled ground)
# ------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------
# the record and its label
# ------------------------------------------------------------------------------------------

def record_svg(cx, cy, R, sy=1.):
    """A black LP (an ellipse when sy < 1): white grooves cut 1 px at 3 px pitch between track
    gaps, two sheen sectors where the light catches extra grooves, an edge highlight."""
    o = [_P(_d(E(cx, cy, R, R * sy, 72)[:-1], True, 0), "#000")]
    RL = R * .34
    r0, r1 = RL + 3, R - 2.5
    gaps = {4, 9, 15}
    rings, sheen, hl = [], [], []
    k = 0
    r = r0
    a1, a2 = math.radians(-60), math.radians(120)
    while r < r1:
        if k not in gaps:
            rings.append(E(cx, cy, r, r * sy, max(24, int(r * .9))))
        wdt = .34 * (1 - .35 * (r - r0) / max(1, r1 - r0))
        for a in (a1, a2):
            sheen.append(E(cx, cy, r + 1.5, (r + 1.5) * sy, 8, a - wdt * .7, a + wdt * .7))
            hl.append(E(cx, cy, r, r * sy, 8, a - wdt * .4, a + wdt * .4))
        k += 1
        r += 3.
    pen = _Pen()
    for pl in rings:
        pen.add(pl, False, .3)
    o.append(f'<path{C._QT} d="{pen.d()}" fill="none" stroke="#fff" stroke-width="4"/>')
    pen = _Pen()
    for pl in sheen:
        pen.add(pl, False, .3)
    o.append(f'<path{C._QT} d="{pen.d()}" fill="none" stroke="#fff" stroke-width="4"/>')
    pen = _Pen()
    for pl in hl:
        pen.add(pl, False, .3)
    o.append(f'<path{C._QT} d="{pen.d()}" fill="none" stroke="#fff" stroke-width="8"/>')
    o.append(_P(_d(E(cx, cy, R - 1, (R - 1) * sy, 64), tol=0), sw=1, stroke="#fff"))
    return "".join(o)


def label(cx, cy, RL, phase, year, sticks=False):
    """The record label: a rose-engine guilloche band, a white field with the moon at today's
    phase above the spindle and the year below."""
    cv = Canvas()
    cv.obj([E(cx, cy, RL, RL, 48)[:-1]], 1.)
    cv.hair(E(cx, cy, RL - 1.5, RL - 1.5, 48))
    o = []
    if RL >= 13:
        rin, rout = RL * .58, RL - 2.5
        rm, amp = (rin + rout) / 2, (rout - rin) / 2 - .3
        n = 14
        lobes = max(6, int(RL / 2.4))
        for i in range(n):
            pl = []
            for j in range(161):
                t = TAU * j / 160
                rr = rm + amp * math.sin(lobes * t + TAU * i / n)
                pl.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
            cv.hair(pl)
        cv.line(E(cx, cy, rin - .8, rin - .8, 40))
        mr = RL * .2
        moon(cv, cx, cy - RL * .3, mr, phase, 1.5 if mr > 5 else 1.)
        cap = RL * .16
        if cap >= 2.6:
            tw_ = text_width(year, cap)
            o.append(letter_svg(year, cx - tw_ / 2, cy + RL * .2, cap))
    else:
        cv.hair(E(cx, cy, RL * .6, RL * .6, 32))
    cv.obj([E(cx, cy, max(1.8, RL * .09), max(1.8, RL * .09), 14)[:-1]], 1.)
    return cv.svg() + "".join(o) + _P(_circ(cx, cy, max(.9, RL * .045)), "#000")


def sleeve(cv, cx, cy, S, rot):
    """The classic pick's sleeve, lying under the turntable: a dark studio photograph of the duo,
    two heads turned in three-quarter light against a black-cut ground, the card edge bevelled."""
    c, s_ = math.cos(rot), math.sin(rot)

    def T(u, v):
        return (cx + u * c - v * s_, cy + u * s_ + v * c)
    sq = [T(-S / 2, -S / 2), T(S / 2, -S / 2), T(S / 2, S / 2), T(-S / 2, S / 2)]
    cv.obj([[(px + 2, py + 2.5) for px, py in sq]], 0)
    cv.heavy(C.hatch_poly([(px + 2, py + 2.5) for px, py in sq], 45, 1.5))
    cv.obj([sq], 1.)
    cv.line(C.hatch_poly(sq, math.degrees(rot), 2.))
    cv.hair(C.hatch_poly(sq, math.degrees(rot) + 90, 2.))
    for k, (hu, hv, hs) in enumerate(((-.17, -.06, .2), (.16, .02, .19))):
        head = [T(S * (hu + hs * .55 * math.cos(t)), S * (hv + hs * .72 * math.sin(t))) for t in [TAU * i / 28 for i in range(28)]]
        sh = [T(S * (hu - hs * 1.25), S * .5), T(S * (hu - hs * .9), S * (hv + hs * 1.05)), T(S * (hu - hs * .25), S * (hv + hs * .7)),
              T(S * (hu + hs * .25), S * (hv + hs * .7)), T(S * (hu + hs * .9), S * (hv + hs * 1.05)), T(S * (hu + hs * 1.25), S * .5)]
        for poly in (sh, head):
            cv.obj([poly], .5)
            ang = math.degrees(rot) + (70 if k else 110)
            side = [T(S * (hu + (-1 if k else 1) * hs * .1), S * -.5), T(S * (hu + (-1 if k else 1) * hs * 1.6), S * -.5),
                    T(S * (hu + (-1 if k else 1) * hs * 1.6), S * .5), T(S * (hu + (-1 if k else 1) * hs * .1), S * .5)]
            cv.hair(clip_in(C.hatch_poly(poly, ang, 2.), side))
            cv.hair(clip_in(C.hatch_poly(poly, ang + 70, 2.), side))
    cv.heavy([sq[1], sq[2], sq[3]])


# ------------------------------------------------------------------------------------------
# band and medium: the turntable seen from above
# ------------------------------------------------------------------------------------------

def turntable(x, y, w, h, clip_d, ctx, level, seed):
    cid = C._uid("m1t", x, y, w, h)
    o = [f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">']
    phase = _moon_phase((ctx or {}).get("date", ""))
    rng = random.Random(seed)
    rnd = abs(w - h) < 2
    R = min(h * (.44 if level == 0 else .37), w * .3)
    cx, cy = x + w * (.42 if level else .4), y + h * .5
    if rnd:
        R = w * .3
        cx, cy = x + w * .45, y + h * .56
    cv = Canvas()
    wood(cv, x - 4, y - 4, w + 8, h + 8, seed, pitch=2. if level else 2.5, knots=2)
    if rnd:
        sleeve(cv, x + w * .27, y + h * .3, w * .44, -.2)
    # platter: a white rim knurled with two rows of strobe marks, its shadow cast down-right
    pr = R + (5 if level else 3.5)
    sh = E(cx + 2.5, cy + 3, pr, pr, 48)[:-1]
    cv.obj([sh], 0)
    cv.heavy(C.hatch_poly(sh, -45, 1.5))
    cv.hair(C.hatch_poly(sh, 45, 1.5))
    cv.obj([E(cx, cy, pr, pr, 72)[:-1]], 1.)
    if level:
        for rr, off in ((pr - 1.4, 0.), (pr - 3.4, .5)):
            n = int(TAU * rr / 2.2)
            for i in range(n):
                a = TAU * (i + off) / n
                cv.heavy([(cx + (rr - .5) * math.cos(a), cy + (rr - .5) * math.sin(a)),
                          (cx + (rr + .5) * math.cos(a), cy + (rr + .5) * math.sin(a))])
    else:
        cv.hair(E(cx, cy, pr - 1.5, pr - 1.5, 48))
    # Easter egg: Parker's drumsticks lying on the plinth beside the record
    if rnd:
        Ls = R * .95
        qx, qy = cx + R * 1.2, cy + R * .05
        for ang in (-1.25, -2.05):
            drumstick(cv, qx - math.cos(ang) * Ls * .45, qy - math.sin(ang) * Ls * .45,
                      qx + math.cos(ang) * Ls * .55, qy + math.sin(ang) * Ls * .55, max(2.6, Ls * .065))
    elif level:
        Ls = h * .5
        bx, by = cx + R * .55, cy + R * 1.22
        drumstick(cv, bx, by, bx + Ls * math.cos(-.42), by + Ls * math.sin(-.42), max(2.6, Ls * .06))
        drumstick(cv, bx + R * .3, by + 5, bx + R * .3 + Ls * math.cos(-.78), by + 5 + Ls * math.sin(-.78), max(2.6, Ls * .06))
    o.append(cv.svg())
    o.append(record_svg(cx, cy, R))
    o.append(label(cx, cy, R * .34, phase, _year(ctx)))
    cv = Canvas()
    s = R / 70.
    px, py = cx + R * 1.18, cy - R * .78
    ang = rng.uniform(-.05, .05)
    nx, ny = cx + R * (.64 + ang) , cy + R * .28
    tonearm(cv, px, py, nx, ny, max(.5, s * 1.1))
    o.append(cv.svg())
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------------------------------
# tall: the parlour with the gramophone
# ------------------------------------------------------------------------------------------

_DOG_SIT = ("M.6,0C-.4,-1.6 -.2,-4 1.4,-5.2C2.6,-6 3.6,-6.6 4.3,-7.7L4.6,-9.5C4.8,-10.5 5.9,-10.9 6.7,-10.5"
            "L7.3,-9.7L8.9,-9.3C9.6,-9.1 9.6,-8.2 8.9,-8L7.4,-7.6C6.9,-6.6 6.9,-5.3 7,-4.3L7.2,-.4L7.8,0"
            "H5.9L5.8,-3.2L4.4,-1.6L4.6,-.4L5.2,0Z")


def _parse_poly(d, x, y, s):
    toks = re.findall(r"[MLHVCZ]|-?\d*\.?\d+", d)
    pts, i, cur, cmd = [], 0, (0., 0.), None
    while i < len(toks):
        t = toks[i]
        if t in "MLHVCZ":
            cmd = t
            i += 1
            if t == "Z":
                continue
        if cmd in "ML":
            cur = (float(toks[i]), float(toks[i + 1]))
            pts.append(cur)
            i += 2
        elif cmd == "H":
            cur = (float(toks[i]), cur[1])
            pts.append(cur)
            i += 1
        elif cmd == "V":
            cur = (cur[0], float(toks[i]))
            pts.append(cur)
            i += 1
        elif cmd == "C":
            c1 = (float(toks[i]), float(toks[i + 1]))
            c2 = (float(toks[i + 2]), float(toks[i + 3]))
            e = (float(toks[i + 4]), float(toks[i + 5]))
            for k in range(1, 9):
                t_ = k / 8
                a, b = (1 - t_) ** 3, 3 * (1 - t_) ** 2 * t_
                c, dd = 3 * (1 - t_) * t_ ** 2, t_ ** 3
                pts.append((a * cur[0] + b * c1[0] + c * c2[0] + dd * e[0], a * cur[1] + b * c1[1] + c * c2[1] + dd * e[1]))
            cur = e
            i += 6
        else:
            i += 1
    return [(x + px * s, y + py * s) for px, py in pts]


def dog(cv, x, y, s, seed):
    """His dog sitting, facing right, feet at (x, y): the coat cut in short bulino strokes that
    run with the fur (back to haunch, chest down, muzzle back), denser on the shadowed rear;
    a dark ear, an eye with its catch-light, the haunch and foreleg modelled."""
    rng = random.Random(seed)
    poly = _parse_poly(_DOG_SIT, x, y, s)
    cv.obj([poly], 1.)
    step = 2.3
    yy = y - 11 * s
    j = 0
    while yy < y:
        xx = x - s + (j % 2) * step * .5
        while xx < x + 10 * s:
            px, py = xx + rng.uniform(-.6, .6), yy + rng.uniform(-.6, .6)
            ux, uy = (px - x) / s, (py - y) / s
            if pt_in(px, py, poly):
                if uy < -7.4 and ux > 4.2:
                    a = PI + .25 * (ux - 6) / 3
                    L = 2.4
                elif ux < 4.6:
                    a = PI * .5 + .7 * (1 - (ux + 1) / 5.6) + .15 * math.sin(uy)
                    L = 3.4
                else:
                    a = PI * .5 - .12
                    L = 3.
                keep = .45 + .5 * (1 - min(1, max(0, (ux + 1) / 9)))
                if rng.random() < keep:
                    cv.hair([(px - math.cos(a) * L / 2, py - math.sin(a) * L / 2),
                             (px + math.cos(a) * L / 2 + .4 * math.sin(a), py + math.sin(a) * L / 2)])
            xx += step
        yy += step
        j += 1
    # rear shadow and haunch, foreleg contour
    cv.line([(x + 1 * s, y - 1.2 * s), (x - .1 * s, y - 2.8 * s), (x + .5 * s, y - 4.4 * s), (x + 2.1 * s, y - 5 * s)])
    cv.line([(x + 5.8 * s, y - .3 * s), (x + 5.9 * s, y - 3.3 * s), (x + 6.3 * s, y - 5 * s)])
    cv.heavy([(x + .65 * s, y - .1 * s), (x - .25 * s, y - 1.7 * s), (x - .1 * s, y - 3.6 * s), (x + 1.2 * s, y - 5.1 * s)])
    # the dark ear: lines packed tight with one white glint
    ear = [(x + 4.7 * s, y - 9.9 * s), (x + 5.8 * s, y - 10.3 * s), (x + 6.4 * s, y - 9.2 * s), (x + 6.1 * s, y - 7.6 * s),
           (x + 5.3 * s, y - 7.0 * s), (x + 4.6 * s, y - 8.2 * s)]
    cv.obj([ear], 1.)
    cv.line(C.hatch_poly(ear, 75, 2.))
    cv.hair([ear[0], ear[3]])
    # eye, nose, mouth line, collar
    cv.obj([E(x + 7.7 * s, y - 9.1 * s, .3 * s, .24 * s, 12)[:-1]], 1.)
    cv.line(C.hatch_poly(E(x + 7.7 * s, y - 9.1 * s, .3 * s, .24 * s, 12)[:-1], 90, 1.))
    cv.heavy([(x + 7.2 * s, y - 9.45 * s), (x + 7.8 * s, y - 9.5 * s), (x + 8.1 * s, y - 9.3 * s)])
    cv.obj([E(x + 9.1 * s, y - 8.75 * s, .3 * s, .26 * s, 12)[:-1]], 1.)
    cv.line(C.hatch_poly(E(x + 9.1 * s, y - 8.75 * s, .3 * s, .26 * s, 12)[:-1], 90, 1.))
    cv.line([(x + 8.9 * s, y - 8.1 * s), (x + 8.1 * s, y - 8.0 * s), (x + 7.6 * s, y - 8.2 * s)])
    col = [(x + 4.3 * s, y - 7.7 * s), (x + 7.1 * s, y - 6.8 * s), (x + 7.0 * s, y - 6.3 * s), (x + 4.2 * s, y - 7.1 * s)]
    cv.obj([col], 1.)
    cv.hair(C.hatch_poly(col, 15, 1.5))


def _win_half(y, wy0, wy1, wr):
    if y < wy0 or y > wy1:
        return -1
    if y >= wy0 + wr:
        return wr
    d = wy0 + wr - y
    return math.sqrt(max(0., wr * wr - d * d))


def parlour(x, y, w, h, clip_d, ctx, seed):
    cid = C._uid("m1p", x, y, w, h)
    o = [f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">']
    rng = random.Random(seed)
    phase = _moon_phase((ctx or {}).get("date", ""))
    X0, X1, Y0, Y1 = x - 3, x + w + 3, y - 3, y + h + 3
    fl = y + h * .7
    cv = Canvas()
    # the window: night sky with the moon and a cloud bank
    wx0, wx1 = x + w * .58, x + w * .9
    wr = (wx1 - wx0) / 2
    wy0, wy1 = y + h * .17, fl - h * .17
    mx, my, mr = wx0 + wr * 1.2, wy0 + wr * .95, wr * .3
    burin_sky(cv, wx0 - 2, wy0 - 2, wx1 - wx0 + 4, wy1 - wy0 + 4, rng.randrange(1 << 20), pitch=1.5,
              holes=[(mx, my, mr + 3)], banks=[(wx0 + wr * .8, wy1 - (wy1 - wy0) * .2, wr * 1.5, (wy1 - wy0) * .22)])
    moon(cv, mx, my, mr, phase)
    for i in range(6):
        sx, sy = wx0 + rng.uniform(.1, .9) * 2 * wr, wy0 + rng.uniform(.15, .55) * (wy1 - wy0)
        if math.hypot(sx - mx, sy - my) > mr + 6 and _win_half(sy, wy0, wy1, wr) > abs(sx - (wx0 + wr)) + 3:
            r_ = rng.choice((1.5, 2., 2.5))
            cv.obj([[(sx - r_, sy), (sx - r_ * .25, sy - r_ * .25), (sx, sy - r_), (sx + r_ * .25, sy - r_ * .25),
                     (sx + r_, sy), (sx + r_ * .25, sy + r_ * .25), (sx, sy + r_), (sx - r_ * .25, sy + r_ * .25)]], .5)
    # the wall: vine-striped paper falling into shadow away from the window
    wall_bot = fl
    lc = wx0 + wr
    pieces = [[(X0, Y0), (wx0, Y0), (wx0, wall_bot), (X0, wall_bot)],
              [(wx1, Y0), (X1, Y0), (X1, wall_bot), (wx1, wall_bot)],
              [(wx0, wy1), (wx1, wy1), (wx1, wall_bot), (wx0, wall_bot)],
              [(wx0, Y0), (wx1, Y0), (wx1, wy0 + wr)] + [(lc + wr * math.cos(-PI * i / 24), wy0 + wr + wr * math.sin(-PI * i / 24)) for i in range(25)][::-1][::-1] + [(wx0, wy0 + wr)]]
    pieces[3] = [(wx0, Y0), (wx1, Y0), (wx1, wy0 + wr)] + [(lc + wr * math.cos(-PI * i / 24), wy0 + wr + wr * math.sin(-PI * i / 24)) for i in range(25)] + [(wx0, wy0 + wr)]
    cv.obj(pieces, 0)
    wain = fl - h * .14
    yy = Y0 + .75
    while yy < wain:
        hwin = _win_half(yy, wy0 - 2, wy1 + 2, wr + 2)
        spans = [(X0, X1)] if hwin < 0 else [(X0, lc - hwin), (lc + hwin, X1)]
        for a, b in spans:
            if b - a < 2:
                continue
            seg = [(a + (b - a) * i / max(1, int((b - a) / 6)), yy) for i in range(int((b - a) / 6) + 1)]
            cur, hv0 = [], None
            for p in seg:
                dl = math.hypot((p[0] - lc) / w, (p[1] - (wy0 + wy1) / 2) / h)
                hv = dl > .3 or p[1] < y + h * .06
                if hv0 is None or hv == hv0:
                    cur.append(p)
                else:
                    cur.append(p)
                    (cv.line if hv0 else cv.hair)(cur)
                    cur = [p]
                hv0 = hv
            if len(cur) > 1:
                (cv.line if hv0 else cv.hair)(cur)
        yy += 1.5
    # vine stripes: a wavy stem with paired leaflets every 22 px
    vx = X0 + 9
    while vx < X1:
        if not (wx0 - 6 < vx < wx1 + 6):
            stem = [(vx + 2.2 * math.sin(t / 9.), t) for t in [Y0 + k * 2. for k in range(int((wain - Y0) / 2) + 1)]]
            cv.obj([[(px - 1.2, py) for px, py in stem] + [(px + 1.2, py) for px, py in stem][::-1]], 0)
            cv.hair(stem)
            t = Y0 + 4 + (vx * 7) % 9
            while t < wain - 6:
                sx = vx + 2.2 * math.sin(t / 9.)
                for sg in (-1, 1):
                    a = (-PI / 2 + sg * 1.0)
                    lf = [(sx + 5 * math.cos(a) * u + sg * 1.6 * math.sin(PI * u) * math.cos(a + PI / 2) * 1.,
                           t + 5 * math.sin(a) * u + 1.6 * math.sin(PI * u) * math.sin(a + PI / 2) * sg) for u in [i / 6 for i in range(7)]]
                    lf2 = [(sx + 5 * math.cos(a) * u - sg * 1.6 * math.sin(PI * u) * math.cos(a + PI / 2),
                            t + 5 * math.sin(a) * u - 1.6 * math.sin(PI * u) * math.sin(a + PI / 2) * sg) for u in [i / 6 for i in range(7)]]
                    cv.obj([lf + lf2[::-1][1:-1]], .5)
                    cv.hair([lf[0], lf[4]])
                cv.obj([E(sx, t + 5, 1.3, 1.3, 8)[:-1]], .5)
                t += 15
        vx += 30
    # wainscot: raised walnut panels below a dado rail
    wood(cv, X0, wain, X1 - X0, fl - wain, seed + 21, pitch=1.5, knots=0)
    cv.obj([[(X0, wain - 3), (X1, wain - 3), (X1, wain + .5), (X0, wain + .5)]], 1.)
    cv.hair([(X0, wain - 1.5), (X1, wain - 1.5)])
    pw_ = w / 5.
    k = 0
    px_ = X0
    while px_ < X1:
        panel = [(px_ + 3, wain + 3), (px_ + pw_ - 3, wain + 3), (px_ + pw_ - 3, fl - 2.5), (px_ + 3, fl - 2.5)]
        wood(cv, px_ + 3, wain + 3, pw_ - 6, fl - wain - 5.5, seed + k, pitch=1.5, knots=1, poly=panel, outline=1.)
        cv.line([(px_ + 5, fl - 4.5), (px_ + 5, wain + 5), (px_ + pw_ - 5, wain + 5)])
        cv.heavy([(px_ + pw_ - 3, wain + 3), (px_ + pw_ - 3, fl - 2.5), (px_ + 3, fl - 2.5)])
        px_ += pw_
        k += 1
    # the window casing and mullions, the sill
    outer = [(wx0 - 4, wy1)] + [(lc - (wr + 4) * math.cos(PI * i / 30), wy0 + wr - (wr + 4) * math.sin(PI * i / 30)) for i in range(31)] + [(wx1 + 4, wy1)]
    inner = [(wx1, wy1)] + [(lc + wr * math.cos(PI * i / 30), wy0 + wr - wr * math.sin(PI * i / 30)) for i in range(31)] + [(wx0, wy1)]
    cv.obj([outer + inner], 1.)
    cv.hair([(lc - (wr + 2) * math.cos(PI * i / 30), wy0 + wr - (wr + 2) * math.sin(PI * i / 30)) for i in range(31)])
    for xx_ in (lc,):
        bar = [(xx_ - 1.5, wy0), (xx_ + 1.5, wy0), (xx_ + 1.5, wy1), (xx_ - 1.5, wy1)]
        cv.obj([bar], .5)
        cv.hair([(xx_ + .6, wy0 + 1), (xx_ + .6, wy1)])
    for yy_ in (wy0 + wr + (wy1 - wy0 - wr) * .4,):
        bar = [(wx0, yy_ - 1.5), (wx1, yy_ - 1.5), (wx1, yy_ + 1.5), (wx0, yy_ + 1.5)]
        cv.obj([bar], .5)
        cv.hair([(wx0, yy_ + .6), (wx1, yy_ + .6)])
    sill = [(wx0 - 8, wy1), (wx1 + 8, wy1), (wx1 + 6, wy1 + 5), (wx0 - 6, wy1 + 5)]
    cv.obj([sill], 1.)
    cv.hair(C.hatch_poly(sill, 0, 1.5, .5))
    cv.heavy([(wx0 - 6, wy1 + 5), (wx1 + 6, wy1 + 5)])
    # the curtain, drawn back to the left of the window: folds modelled in swelling lines
    cx0, cx1 = wx0 - 22, wx0 + 10
    ctop = wy0 - 8
    cbot = fl - 3
    tie = wy1 - (wy1 - wy0) * .1
    edge = []
    for i in range(41):
        t = i / 40
        yy_ = ctop + (cbot - ctop) * t
        pinch = math.exp(-((yy_ - tie) / ((cbot - ctop) * .12)) ** 2)
        edge.append((cx1 - (cx1 - cx0) * .55 * pinch + 2 * math.sin(t * 7), yy_))
    cur_poly = [(cx0, ctop)] + edge + [(cx0 - 2, cbot)]
    cv.obj([cur_poly], 1.)
    nf = 5
    for f in range(nf * 3):
        u = (f + .5) / (nf * 3)
        fold = []
        for i in range(41):
            ex, ey = edge[i]
            xx_ = cx0 + (ex - cx0) * u + 1.2 * math.sin(u * nf * TAU + ey / 23.)
            fold.append((xx_, ey))
        dark = math.sin(u * nf * TAU) < -.2
        (cv.line if dark else cv.hair)(fold)
    cv.obj([E(cx0 + (edge[20][0] - cx0) * .5 + 2, tie, (cx1 - cx0) * .42, 3, 16)[:-1]], 1.)
    cv.hair(E(cx0 + (edge[20][0] - cx0) * .5 + 2, tie, (cx1 - cx0) * .3, 1.5, 16))
    rod = [(cx0 - 6, ctop - 3), (wx1 + 14, ctop - 3), (wx1 + 14, ctop), (cx0 - 6, ctop)]
    cv.obj([rod], 1.)
    for ex_ in (cx0 - 6, wx1 + 14):
        cv.obj([E(ex_, ctop - 1.5, 3, 3, 12)[:-1]], 1.)
        cv.hair(E(ex_, ctop - 1.5, 1.5, 1.5, 10))
    # the floor: boards in perspective, grain wandering down each board
    cv.obj([[(X0, fl), (X1, fl), (X1, Y1), (X0, Y1)]], 1.)
    vx_, vy_ = x + w * .45, fl - h * .9
    tt = (fl - vy_) / (Y1 - vy_)
    pl = w * .065
    for k in range(-30, 31):
        fx = x + w / 2 + k * pl
        a, b = (vx_ + (fx - vx_) * tt, fl), (fx, Y1)
        if b[0] < X0 - 40 or b[0] > X1 + 40:
            continue
        cv.line([a, b])
        for gg in (.3, .6):
            fx2 = fx + pl * gg
            a2 = (vx_ + (fx2 - vx_) * tt, fl)
            cv.hair([(a2[0] + (fx2 - a2[0]) * s_ + math.sin(s_ * 8 + k) * pl * .06 * s_, fl + (Y1 - fl) * s_) for s_ in [j / 10 for j in range(11)]])
        if k % 2:
            s_ = .35 + .3 * ((k * 37) % 10) / 10
            fx3 = fx + pl
            a3 = (vx_ + (fx3 - vx_) * tt, fl)
            cv.line([(a[0] + (b[0] - a[0]) * s_, fl + (Y1 - fl) * s_), (a3[0] + (fx3 - a3[0]) * s_, fl + (Y1 - fl) * s_)])
    # depth: the floor darkens toward the back wall in cross lines
    yy = fl + 1.5
    while yy < fl + h * .07:
        cv.hair([(X0, yy), (X1, yy)])
        yy += 1.5 + (yy - fl) * .25
    cv.heavy([(X0, fl + .5), (X1, fl + .5)])
    # the rug: an oval of border bands, a zigzag running round, florets in the field, fringe
    rcx, rcy, rrx, rry = x + w * .5, fl + (Y1 - fl) * .55, w * .46, (Y1 - fl) * .36
    cv.obj([E(rcx, rcy, rrx, rry, 72)[:-1]], 1.)
    for f in (.97, .86, .83):
        cv.hair(E(rcx, rcy, rrx * f, rry * f, 72))
    zz = []
    for i in range(121):
        t = TAU * i / 120
        f = .915 + .035 * (1 if i % 2 else -1)
        zz.append((rcx + rrx * f * math.cos(t), rcy + rry * f * math.sin(t)))
    cv.line(zz)
    fld = E(rcx, rcy, rrx * .8, rry * .8, 48)[:-1]
    cv.hair(C.hatch_poly(fld, 18, 6.))
    cv.hair(C.hatch_poly(fld, -18, 6.))
    for i in range(-6, 7):
        for j in range(-3, 4):
            fx, fy = rcx + i * rrx * .12, rcy + j * rry * .25 + (i % 2) * rry * .125
            if ((fx - rcx) / (rrx * .74)) ** 2 + ((fy - rcy) / (rry * .74)) ** 2 < 1:
                cv.obj([[(fx - 2.2, fy), (fx, fy - 1.3), (fx + 2.2, fy), (fx, fy + 1.3)]], .5)
                cv.hair([(fx - 1, fy), (fx + 1, fy)])
    med = [(rcx - rrx * .22, rcy), (rcx, rcy - rry * .4), (rcx + rrx * .22, rcy), (rcx, rcy + rry * .4)]
    cv.obj([med], 1.)
    cv.hair(C.hatch_poly(med, 0, 1.5))
    cv.obj([E(rcx, rcy, rrx * .08, rry * .16, 16)[:-1]], 1.)
    for i in range(40):
        t = PI * .02 + PI * .96 * i / 39
        p = (rcx + rrx * math.cos(t), rcy + rry * math.sin(t))
        if p[1] > rcy + rry * .6:
            cv.hair([p, (p[0], p[1] + 2.5)])
    o.append(cv.svg())

    # ---- the gramophone cabinet
    cv = Canvas()
    bx0, bx1 = x + w * .38, x + w * .74
    by0, by1 = fl - h * .02, fl + (Y1 - fl) * .52
    dep = h * .07
    sk = w * .06
    # cast shadow on the rug
    shd = [(bx1, by1), (bx1 + w * .07, by1 - dep * .5), (bx1 + w * .07, by1 + 4), (bx0 + 6, by1 + 6)]
    cv.obj([shd], 0)
    cv.line(C.hatch_poly(shd, 30, 1.5))
    cv.hair(C.hatch_poly(shd, -30, 1.5))
    front = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
    wood(cv, bx0, by0, bx1 - bx0, by1 - by0, seed + 3, pitch=2., knots=1, poly=front, outline=1.)
    pin = 5
    pnl = [(bx0 + pin, by0 + pin + 3), (bx1 - pin, by0 + pin + 3), (bx1 - pin, by1 - pin), (bx0 + pin, by1 - pin)]
    wood(cv, pnl[0][0], pnl[0][1], pnl[1][0] - pnl[0][0], pnl[2][1] - pnl[0][1], seed + 4, pitch=1.5, knots=1, poly=pnl, outline=1.)
    # the panel's carved fret: a small scroll from the centre to each side
    pcx, pcy = (bx0 + bx1) / 2, (pnl[0][1] + pnl[2][1]) / 2
    ph_ = pnl[2][1] - pnl[0][1]
    for sg in (-1, 1):
        sp = k_spiral(pcx + sg * (bx1 - bx0) * .22, pcy, ph_ * .36, PI / 2 if sg > 0 else -PI / 2, 1.4, sg)
        spo = [(px_ + 1.2, py_ + 1.2) for px_, py_ in sp]
        cv.obj([sp + spo[::-1]], 1.)
        cv.heavy(spo)
    cv.obj([E(pcx, pcy, 3, 3, 12)[:-1]], 1.)
    cv.heavy(E(pcx, pcy, 3, 3, 12, 0, PI))
    cv.heavy([pnl[0], pnl[1]])
    cv.heavy([pnl[0], pnl[3]])
    side = [(bx0, by0), (bx0 - sk, by0 - dep), (bx0 - sk, by1 - dep), (bx0, by1)]
    cv.obj([side], 1.)
    cv.line(C.hatch_poly(side, 90, 1.5))
    cv.hair(C.hatch_poly(side, 20, 2.))
    for fxp in (bx0 + 5, bx1 - 5):
        foot = [(fxp - 4, by1), (fxp + 4, by1), (fxp + 2.5, by1 + 5), (fxp - 2.5, by1 + 5)]
        cv.obj([foot], 1.)
        cv.line(C.hatch_poly(foot, 90, 1.5))
    topf = [(bx0, by0), (bx1, by0), (bx1 - sk, by0 - dep), (bx0 - sk, by0 - dep)]
    cv.obj([topf], 1.)
    yy = by0 - dep + 1.5
    while yy < by0:
        t_ = (by0 - yy) / dep
        cv.hair([(bx0 - sk * t_ + 1, yy), (bx1 - sk * t_ - 1, yy)])
        yy += 2.
    cv.heavy([(bx0, by0), (bx1, by0)])
    # the crank
    cx_, cy_ = bx1 + 1, by0 + (by1 - by0) * .4
    cv.obj([[(cx_, cy_ - 1.5), (cx_ + 9, cy_ - 1.5), (cx_ + 9, cy_ + 1.5), (cx_, cy_ + 1.5)]], 1.)
    cv.obj([[(cx_ + 7.5, cy_), (cx_ + 10.5, cy_), (cx_ + 10.5, cy_ + 12), (cx_ + 7.5, cy_ + 12)]], 1.)
    cv.line([(cx_ + 9.6, cy_ + 1), (cx_ + 9.6, cy_ + 11)])
    cv.obj([E(cx_ + 9, cy_ + 13.5, 3, 2.2, 12)[:-1]], 1.)
    cv.hair(C.hatch_poly(E(cx_ + 9, cy_ + 13.5, 3, 2.2, 12)[:-1], 0, 1.))
    # platter
    pcx2, pcy2 = (bx0 + bx1) / 2 - sk / 2 - w * .02, by0 - dep / 2
    prx, pry = (bx1 - bx0) * .4, dep * .44
    cv.obj([E(pcx2, pcy2 + 1.5, prx, pry, 60)[:-1]], 1.)
    cv.hair(E(pcx2, pcy2 + 1.5, prx, pry, 60, 0, PI))
    o.append(cv.svg())
    o.append(record_svg(pcx2, pcy2, prx - 1.2, (pry - .8) / (prx - 1.2)))
    cv = Canvas()
    cv.obj([E(pcx2, pcy2, prx * .3, pry * .3, 24)[:-1]], 1.)
    cv.hair(E(pcx2, pcy2, prx * .2, pry * .2, 20))
    cv.obj([E(pcx2, pcy2, 1.2, .8, 8)[:-1]], 1.)
    # sound box and arm on the record
    tax, tay = bx1 - sk * .8 - 7, by0 - dep * .72
    cv.obj([E(tax, tay, 4, 2.3, 14)[:-1]], 1.)
    cv.hair(E(tax, tay, 2.5, 1.4, 10))
    arm = [(tax, tay), (tax - prx * .5, tay + pry * .15), (tax - prx * .66, tay + pry * .5)]
    cv.obj([[(px_, py_ - 1.2) for px_, py_ in arm] + [(px_, py_ + 1.2) for px_, py_ in arm][::-1]], 1.)
    cv.hair(arm)
    sb = (tax - prx * .7, tay + pry * .6)
    cv.obj([E(sb[0], sb[1], 4, 3, 14)[:-1]], 1.)
    cv.hair(E(sb[0], sb[1], 2.6, 1.8, 12))
    # ---- the horn: neck from the back of the deck, a flared bell of petals opening left
    nx, ny = bx1 - sk - w * .05, by0 - dep * .9
    elbow = (nx + w * .01, y + h * .42)
    hw = 3.
    neck = [(nx, ny), (nx + 1.5, (ny + elbow[1]) / 2), (elbow[0], elbow[1] + 4)]
    cv.obj([[(px_ - hw, py_) for px_, py_ in neck] + [(px_ + hw, py_) for px_, py_ in neck][::-1]], 1.)
    cv.line([(px_ + hw * .5, py_) for px_, py_ in neck])
    cv.hair([(px_ - hw * .3, py_) for px_, py_ in neck])
    mcx, mcy = x + w * .25, y + h * .3
    mry, mrx = h * .2, w * .075
    ax = []
    n = 40
    for i in range(n + 1):
        t = i / n
        qx = (1 - t) ** 2 * elbow[0] + 2 * (1 - t) * t * (elbow[0] - w * .2) + t * t * mcx
        qy = (1 - t) ** 2 * elbow[1] + 2 * (1 - t) * t * (elbow[1] - h * .03) + t * t * mcy
        ax.append((qx, qy))
    rad = [3.2 + (mry - 3.2) * (i / n) ** 2.6 for i in range(n + 1)]
    Rb = C._Rib(ax, rad, rad)
    cv.obj([Rb.outline()], 1.)
    # brass: a bright band along the top, petal seams, the underside cut dark in close contours
    # crossed by the flare's rings
    for s_ in (.75, .45, .15, -.15, -.45, -.75):
        cv.heavy(Rb.contour(s_, .05, 1.))
    for s_ in [-.06 - .06 * k for k in range(15)]:
        cv.hair(Rb.contour(s_, .12, 1.))
    for s_ in (.9, .6, .3):
        cv.hair(Rb.contour(s_, .4, 1.))
    for u in (.3, .45, .57, .67, .75, .82, .88, .93, .97):
        cv.hair([Rb.at(u, s_ / 10) for s_ in range(-10, 1)])
    tilt = math.radians(8)

    def mouth(t, k=1.):
        ex, ey = mrx * k * math.cos(t), mry * k * math.sin(t)
        return (mcx + ex * math.cos(tilt) - ey * math.sin(tilt), mcy + ex * math.sin(tilt) + ey * math.cos(tilt))
    rim = [mouth(TAU * i / 72) for i in range(72)]
    cv.obj([rim], 1.5)
    inner = [mouth(TAU * i / 72, .86) for i in range(72)]
    cv.obj([inner], 1.)
    cv.line(C.hatch_poly(inner, 8, 1.5))
    cv.hair(C.hatch_poly([mouth(TAU * i / 48, .62) for i in range(48)], 98, 1.5))
    th = [mouth(TAU * i / 24, .24) for i in range(24)]
    cv.obj([th], 1.)
    cv.heavy(C.hatch_poly(th, 8, 1.5))
    cv.line(C.hatch_poly(th, 98, 1.5))
    for i in range(8):
        a = TAU * i / 8
        cv.hair([mouth(a, .3), mouth(a, .84)])
    cv.hair([mouth(TAU * i / 72, .93) for i in range(72)])
    cv.heavy([mouth(PI * .3 + PI * .9 * i / 30, 1.03) for i in range(31)])
    # ---- his dog, sitting on the rug at the left, listening at the bell
    s_ = h * .3 / 11.
    dog(cv, x + w * .02, fl + (Y1 - fl) * .55, s_, seed)
    # Easter egg: Parker's drumsticks crossed on the rug before the cabinet
    dl = w * .2
    dx, dy = x + w * .48, fl + (Y1 - fl) * .8
    drumstick(cv, dx - dl * .5, dy + 3, dx + dl * .5, dy - 4, 3.6)
    drumstick(cv, dx - dl * .3, dy - 6, dx + dl * .55, dy + 5, 3.6)
    o.append(cv.svg())
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------------------------------
# roundels and tablet
# ------------------------------------------------------------------------------------------

def cymbal(cv, cx, cy, r):
    """A ride cymbal on its stand, tipped toward us: lathe grooves in ellipses, a bright wedge of
    light, the bell turned in rings, a stick resting on the bow."""
    rx, ry = r * .9, r * .36
    cyy = cy - r * .15
    cv.obj([[(cx - 1.3, cyy), (cx + 1.3, cyy), (cx + 1.3, cy + r * .95), (cx - 1.3, cy + r * .95)]], .5)
    for sg in (-1, 1):
        cv.obj([[(cx, cy + r * .55), (cx + sg * r * .5, cy + r * .95), (cx + sg * r * .5 + sg * 1.2, cy + r * .95), (cx + 1.2 * sg, cy + r * .5)]], .5)
    cv.obj([E(cx, cyy, rx, ry, 56)[:-1]], 1.)
    k = .93
    i = 0
    while k > .3:
        a0, a1 = (PI * 1.05, PI * 1.6) if i % 2 else (PI * .05, PI * .95)
        cv.hair(E(cx, cyy, rx * k, ry * k, 40))
        k -= max(.06, 1.5 / ry)
        i += 1
    cv.line(E(cx, cyy, rx, ry, 32, PI * .05, PI * .95))
    cv.obj([E(cx, cyy - ry * .12, rx * .28, ry * .4, 24)[:-1]], 1.)
    cv.hair(E(cx, cyy - ry * .12, rx * .18, ry * .26, 18))
    cv.line(E(cx, cyy - ry * .12, rx * .28, ry * .4, 16, PI * .1, PI * .9))
    if r > 14:
        drumstick(cv, cx - r * .95, cyy - r * .55, cx + r * .2, cyy - ry * .25, max(2., r * .1))


def lyre(cv, cx, cy, r):
    """A lyre: two horned arms curling out at the top (each a tapering ribbon with a shade line),
    the yoke, five strings, a turned base."""
    for sg in (-1, 1):
        pts = []
        for i in range(25):
            t = i / 24
            a = PI * (1.05 + .95 * t)
            rr = r * (.55 - .2 * t)
            pts.append((cx + sg * (r * .05 + rr * .65 * (1 + math.cos(a))), cy + r * .5 - r * 1.05 * t + r * .1 * math.sin(PI * t)))
        wid = [max(.8, r * .09 * (1 - .6 * i / 24)) for i in range(25)]
        hd = with_heading(pts)
        L_ = [(px_ - math.sin(a) * wd, py_ + math.cos(a) * wd) for (px_, py_, a), wd in zip(hd, wid)]
        R_ = [(px_ + math.sin(a) * wd, py_ - math.cos(a) * wd) for (px_, py_, a), wd in zip(hd, wid)]
        cv.obj([L_ + R_[::-1]], 1.)
        cv.line([((a_[0] + b_[0]) / 2 + sg * .4, (a_[1] + b_[1]) / 2) for a_, b_ in zip(L_, R_)][2:])
        ex, ey = pts[-1]
        sp = k_spiral(ex - sg * r * .06, ey + r * .06, r * .1, PI if sg > 0 else 0, 1.2, -sg)
        cv.line(sp)
    yk = [(cx - r * .62, cy - r * .42), (cx + r * .62, cy - r * .42), (cx + r * .62, cy - r * .34), (cx - r * .62, cy - r * .34)]
    cv.obj([yk], 1.)
    for i in range(5):
        sx = cx + (i - 2) * r * .14
        cv.hair([(sx, cy - r * .34), (sx, cy + r * .5)])
    base = [(cx - r * .45, cy + r * .5), (cx + r * .45, cy + r * .5), (cx + r * .35, cy + r * .72), (cx - r * .35, cy + r * .72)]
    cv.obj([base], 1.)
    cv.line(C.hatch_poly(base, 90, 1.5))
    cv.obj([E(cx, cy + r * .78, r * .3, r * .08, 16)[:-1]], 1.)


def motif(cx, cy, r, i, seed):
    o = [black_ground(E(cx, cy, r + 1, r + 1, 32)[:-1], seed + 13, dens=0)]
    cv = Canvas()
    if i == 0:
        cymbal(cv, cx, cy, r * .82)
    else:
        lyre(cv, cx, cy, r * .82)
    o.append(cv.svg())
    return "".join(o)


def swing_tablet(x, y, w, h, seed):
    """A bar of swing ride rhythm cut in white on the engraved black: five staff lines, the
    percussion clef, 4/4, ride-cymbal x-heads in swung eighths and the hi-hat on 2 and 4."""
    o = [black_ground((x, y, w, h), seed + 5, dens=0)]
    sp = min(h / 6., 4.5)
    top = y + h / 2 - 2 * sp + sp * .4
    st = "".join(f"M{_n(x + 4)},{_n(top + i * sp)}h{_n(w - 8)}" for i in range(5))
    bars = f"M{_n(x + 4)},{_n(top)}v{_n(4 * sp)}M{_n(x + w - 4)},{_n(top)}v{_n(4 * sp)}"
    o.append(_P(st, sw=1, stroke="#fff"))
    o.append(_P(bars, sw=1, stroke="#fff"))
    o.append(_P(f"M{_n(x + w - 7)},{_n(top)}v{_n(4 * sp)}", sw=1.5, stroke="#fff"))
    cx0 = x + 10
    o.append(_P(f"M{_n(cx0)},{_n(top + sp)}v{_n(2 * sp)}M{_n(cx0 + 3)},{_n(top + sp)}v{_n(2 * sp)}", sw=1.5, stroke="#fff"))

    def four(fx, fy, s):
        return f"M{_n(fx + s * .4)},{_n(fy + s)}V{_n(fy - s)}L{_n(fx - s * .6)},{_n(fy + s * .3)}H{_n(fx + s * .8)}"
    tx = x + 22
    o.append(_P(four(tx, top + sp, sp * .95) + four(tx, top + 3 * sp, sp * .95), sw=1, stroke="#fff"))
    x0, x1 = x + 34, x + w - 14
    beat = (x1 - x0) / 4
    ry = top - sp * .5
    heads, stems, beams = [], [], []
    s = sp * .45
    for bi in range(4):
        bx = x0 + bi * beat + beat * .2
        notes = [bx] if bi % 2 == 0 else [bx, bx + beat * .62]
        for nx_ in notes:
            heads.append(f"M{_n(nx_ - s)},{_n(ry - s)}l{_n(2 * s)},{_n(2 * s)}M{_n(nx_ - s)},{_n(ry + s)}l{_n(2 * s)},{_n(-2 * s)}")
            stems.append(f"M{_n(nx_ + s)},{_n(ry)}v{_n(-sp * 2.2)}")
        if len(notes) == 2:
            beams.append(f"M{_n(notes[0] + s)},{_n(ry - sp * 2.2)}H{_n(notes[1] + s)}")
            hy = top + 4 * sp + sp * .5
            heads.append(f"M{_n(bx - s)},{_n(hy - s)}l{_n(2 * s)},{_n(2 * s)}M{_n(bx - s)},{_n(hy + s)}l{_n(2 * s)},{_n(-2 * s)}")
    o.append(_P("".join(heads), sw=1, stroke="#fff"))
    o.append(_P("".join(stems), sw=1, stroke="#fff"))
    o.append(_P("".join(beams), sw=2, stroke="#fff", extra=' stroke-linecap="butt"'))
    return "".join(o)


def reel(cv, cx, cy, R, rot=0.):
    """A reel of quarter-inch tape: the aluminium flange turned in lathe rings, three kidney
    windows showing the dark wound pack, the hub with its three keys, a raking highlight."""
    cv.obj([E(cx, cy, R, R, 64)[:-1]], 1.)
    q = R - 1.5
    while q > R * .84:
        cv.hair(E(cx, cy, q, q, 56))
        q -= 1.5
    pack = R * .74
    for k in range(3):
        a0 = rot + TAU * k / 3 + .25
        a1 = a0 + TAU / 3 - .5
        win = [(cx + R * .8 * math.cos(a0 + (a1 - a0) * i / 16), cy + R * .8 * math.sin(a0 + (a1 - a0) * i / 16)) for i in range(17)]
        win += [(cx + R * .32 * math.cos(a1 - (a1 - a0) * i / 10), cy + R * .32 * math.sin(a1 - (a1 - a0) * i / 10)) for i in range(11)]
        cv.obj([win], 1.)
        rr = R * .3
        while rr < pack:
            cv.line(E(cx, cy, rr, rr, 24, a0 - .02, a1 + .02))
            rr += 1.5
        cv.hair(E(cx, cy, pack + 1.5, pack + 1.5, 20, a0, a1))
    for k in range(3):
        a = rot + TAU * k / 3 + .25 - .25
        cv.hair([(cx + R * .34 * math.cos(a), cy + R * .34 * math.sin(a)), (cx + R * .8 * math.cos(a), cy + R * .8 * math.sin(a))])
    cv.obj([E(cx, cy, R * .2, R * .2, 24)[:-1]], 1.)
    cv.hair(E(cx, cy, R * .15, R * .15, 20))
    for k in range(3):
        a = rot + TAU * k / 3
        cv.obj([[(cx + R * .06 * math.cos(a + .4), cy + R * .06 * math.sin(a + .4)), (cx + R * .14 * math.cos(a + .2), cy + R * .14 * math.sin(a + .2)),
                 (cx + R * .14 * math.cos(a - .2), cy + R * .14 * math.sin(a - .2)), (cx + R * .06 * math.cos(a - .4), cy + R * .06 * math.sin(a - .4))]], .5)
    cv.heavy(E(cx, cy, R - .5, R - .5, 40, PI * .15, PI * .8))


def frame(poly, box, w, h):
    """The plate's frame is the music's own machinery: a reel of tape at either hand, the tape
    running off both reels and looping beneath the roundel as the banner that carries the
    title; a capstan guide where it turns."""
    x, y, sw, sh = box
    cx, cy = x + sw / 2, y + sh / 2
    R = min(sh * .3, (w - sw) / 2 * .78)
    cv = Canvas()
    reels = [(cx - sw / 2 - R * .62, y + R + 4, .3), (cx + sw / 2 + R * .62, y + R + 4, 1.1)]
    tape_y = y + sh - 11
    tw = 17.
    pts = []
    for i in range(61):
        t = i / 60
        xx = reels[0][0] + (reels[1][0] - reels[0][0]) * t
        sag = math.sin(PI * t)
        pts.append((xx, reels[0][1] + R * .74 + (tape_y - reels[0][1] - R * .74) * (sag ** .45)))
    top = [(px, py - tw / 2) for px, py in pts]
    bot = [(px, py + tw / 2) for px, py in pts]
    for rx, ry, rot in reels:
        reel(cv, rx, ry, R, rot)
    back = cv.svg()
    cv = Canvas()
    cv.obj([top + bot[::-1]], 1.)
    for f in (-.4, .4):
        cv.hair([(px, py + tw * f) for px, py in pts])
    cv.hair(C.hatch_poly([p for p in top[:20]] + [p for p in bot[:20]][::-1], 70, 2.))
    cv.hair(C.hatch_poly([p for p in top[-20:]] + [p for p in bot[-20:]][::-1], 110, 2.))
    # the turn of the tape under the reels: twist shading at both ends
    for k in (0, 1):
        seg = pts[:9] if k == 0 else pts[-9:]
        for j in range(len(seg) - 1):
            px, py = seg[j]
            cv.hair([(px, py - tw / 2 + 1), (px + 2, py + tw / 2 - 1)])
    for sg, (px, py) in ((-1, pts[12]), (1, pts[-13])):
        cv.obj([E(px, py + tw * .9, 4, 4, 16)[:-1]], 1.)
        cv.line(E(px, py + tw * .9, 2.2, 2.2, 12))
    front = cv.svg()
    txt = "PUT THIS RECORD ON"
    cap = tw * .52
    tw_ = text_width(txt, cap, .14)
    x0 = cx - tw_ / 2

    def warp(px, py):
        t = (px - reels[0][0]) / (reels[1][0] - reels[0][0])
        t = min(1., max(0., t))
        i = t * 60
        j = min(59, int(i))
        f = i - j
        ty = pts[j][1] * (1 - f) + pts[j + 1][1] * f
        return px, py - tape_y + ty
    front += letter_svg(txt, x0, tape_y - cap / 2, cap, .14, warp)
    return back, front


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = (sum(map(ord, ctx.get("date", ""))) + 3) % 9973
    spec = dict(shape="roundel", aspect=1., seed=seed, rag=3.5, margins=(4, 3, 4, 3),
                scene=lambda x, y, ww, hh, clip, lv: turntable(x, y, ww, hh, clip, ctx, 1, seed),
                frame=lambda poly, box: frame(poly, box, w, h))
    return vignette_plate(w, h, ctx, spec)
