"""markets-03 -- Portland real estate.
An old Portland Craftsman house in three-quarter view: a steep front gable with shingled peak and
attic window, a deep porch on tapered columns, clapboard walls, a brick chimney, rhododendrons at the
foundation and a brick walk down the lawn. Behind it Douglas firs, Mount Hood on the right, and on the
left the Gothic towers of the St. Johns Bridge over the Willamette (the page names St. Johns).
The house sits in the codex cartouche between the big volutes; on tall plates a house key lies on
the pedestal tablet (its bow a carved volute), and the ribbon is ruled.
Easter egg: Parker's dog sits on the porch beside the steps, waiting at the door.
"""
import sys
import math
import random
import engraving_codex as C


# ==== GM ENGINE BEGIN ====
# The grandmaster frame (one copy per plate file; edit gm_engine.py in the studio and re-inject).
# Rounded, lobed acanthus with central and secondary veins and bulino that runs dark into the
# turn; volutes that wind into drilled spiral eyes; a cut-away ground of black punched with white
# stipple and engraved with white background tendrils and florets (every white line >= 1 CSS px);
# carved cartouche mouldings; a twisting ribbon banner; a cylinder-knurled pedestal; a continuous
# rinceau. Every motif paints into an engraving_codex Canvas so a plate stays far under budget.
import math
import random
import zlib
_n, _d = C._n, C._d
_GR = C._Rib
_Geu = C._euler
_Gsm = C._smooth
_Gel = C._ell_pts
_Ghp = C.hatch_poly
_Gfl = C._fill_lines
_Gsh = C._shadow
_GPI = math.pi
_GTAU = 2 * math.pi
class _GPen:
    """path data in integer half-px for a transform="scale(.5)" path"""

    def __init__(self, q=2):
        self.o = []
        self.cur = None
        self.q = q

    def add(self, pts, close=False, tol=.3):
        if len(pts) < 2:
            return
        if tol:
            pts = C._dp(pts, tol)
        q = self.q
        X = [int(round(p[0] * q)) for p in pts]
        Y = [int(round(p[1] * q)) for p in pts]
        o = self.o
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
        if not seg:
            seg = ["0 0"]
        o.append("l" + " ".join(seg).replace(" -", "-"))
        if close:
            o.append("z")
            self.cur = (X[0], Y[0])
        else:
            self.cur = (X[-1], Y[-1])

    def d(self):
        return "".join(self.o)



def _g_clip_runs(pl, mask, x0, y0, W, H, out, step=1.4):
    """engraving_codex._clip_runs, sampled every `step` px: the runs of pl not under mask."""
    run = []
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L = abs(dx) + abs(dy)
        if L > step:
            k = int(L / step)
            ix, iy = dx / (k + 1), dy / (k + 1)
            for j in range(1, k + 1):
                pts.append((px + ix * j, py + iy * j))
        pts.append(q)
        px, py = q
    for (x, y) in pts:
        xi = int(x - x0)
        yi = int(y - y0)
        if 0 <= yi < H and 0 <= xi < W and mask[yi][xi]:
            if len(run) > 1:
                out.append(run)
            run = []
        else:
            run.append((x, y))
    if len(run) > 1:
        out.append(run)


class GmCanvas(C.Canvas):
    """engraving_codex.Canvas emitting half-px path data with a coarser simplification (about
    40 % smaller), same occlusion rules. clip=(x0, y0, x1, y1) drops everything outside.
    Modelling pass: obj(..., fill="#000") paints a solid black shape (a burin's cleared black,
    the deepest shade), and white(pl) cuts a 1 px white line (only over black)."""
    fill_tol, line_tol = .7, .5
    shadow = None

    def obj(self, polys=(), outline=1., fill="#fff"):
        o = C.Canvas.obj(self, polys, outline)
        o[2]["w"] = []
        if not hasattr(self, "fills"):
            self.fills = []
        self.fills.append(fill)
        return o

    def extend(self, other):
        mf = getattr(self, "fills", [])
        mf += ["#fff"] * (len(self.objs) - len(mf))
        of = getattr(other, "fills", [])
        self.fills = mf + of + ["#fff"] * (len(other.objs) - len(of))
        self.objs.extend(other.objs)

    def white(self, pl):
        if not pl:
            return
        if not self.objs:
            self.obj()
        if isinstance(pl[0][0], (int, float)):
            if len(pl) > 1:
                self.objs[-1][2]["w"].append(pl)
        else:
            self.objs[-1][2]["w"].extend(q for q in pl if len(q) > 1)

    def svg(self, clip=None):
        if not self.objs:
            return ""
        fills = getattr(self, "fills", [])
        fills = fills + ["#fff"] * (len(self.objs) - len(fills))
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: [], "w": []}
        for polys, ow, strokes in reversed(self.objs):
            for w, lines in strokes.items():
                for pl in lines:
                    _g_clip_runs(pl, mask, x0, y0, W, H, out[w])
            if ow:
                for poly in polys:
                    _g_clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                C._fill_mask(poly, mask, x0, y0, W, H)
        if clip:
            cx0, cy0, cx1, cy1 = clip

            def keep(pl):
                return any(cx0 - 2 <= p[0] <= cx1 + 2 and cy0 - 2 <= p[1] <= cy1 + 2 for p in pl)
        else:
            def keep(pl):
                return True
        res = []
        T = ' transform="scale(.5)"'
        # fills in paint order, one path per run of a colour
        runs = []
        for (polys, _, _), f in zip(self.objs, fills):
            if not polys:
                continue
            if not runs or runs[-1][0] != f:
                runs.append((f, _GPen()))
            for poly in polys:
                if keep(poly):
                    runs[-1][1].add(poly if C._area(poly) >= 0 else poly[::-1], True, self.fill_tol)
        for f, pen in runs:
            if not pen.o:
                continue
            if self.shadow and f == "#fff":
                pid = "gmF%x" % (zlib.crc32(pen.d()[:400].encode()) & 0xffffff)
                dx, dy = self.shadow
                res.append(f'<defs><path id="{pid}"{T} d="{pen.d()}"/></defs>'
                           f'<use href="#{pid}" transform="translate({_n(dx)},{_n(dy)})" fill="#000"/>'
                           f'<use href="#{pid}" fill="#fff"/>')
            else:
                res.append(f'<path{T} d="{pen.d()}" fill="{f}" stroke="none"/>')
        if out["w"]:
            pen = _GPen()
            for pl in out["w"]:
                if keep(pl):
                    pen.add(pl, False, self.line_tol)
            if pen.o:
                res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#fff" stroke-width="2"/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _GPen()
                for pl in out[w]:
                    if keep(pl):
                        pen.add(pl, False, self.line_tol)
                if pen.o:
                    res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_n(w * 2)}"/>')
        return "".join(res)


_GN50 = sum(_Gsm(.5, 1., (i + .5) / 50) ** 2 for i in range(50)) / 50


def _g_rot(p, c, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return (c[0] + (p[0] - c[0]) * ca - (p[1] - c[1]) * sa, c[1] + (p[0] - c[0]) * sa + (p[1] - c[1]) * ca)


# ---------------------------------------------------------------------------------- the leaf

def gm_leaf(cv, x, y, ang, L, W, bend=.5, curl=1.4, rng=None, lobes=None, turn=True, dark=1., vein=True):
    """An acanthus leaf from (x, y) heading ang (radians), L long, W its greatest half-width:
    the outer edge cut into rounded lobes with forward serrations and drilled notches, the inner
    edge smooth; a central vein, fine parallel cuts on the shadow (inner) side running dark into
    the turn, slanting cuts across every lobe stopping short of a bright cut edge, the tip rolled."""
    rng = rng or random.Random(int(x * 7 + y * 13))
    if L < 3:
        return None
    n = max(16, int(L / .8))

    def k(u):
        return (bend + curl * _Gsm(.45, 1., u) ** 2 / _GN50) / L
    pts = _Geu(x, y, ang, L, k, n)
    c = 1 if bend + curl >= 0 else -1
    nl = lobes or max(1, min(5, int(L / max(4.5, W * 1.15))))
    ua, ub = .04, .9
    ph = rng.uniform(.0, .12)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        env = W * math.sin(_GPI * min(1., u ** .75 * .97 + .015)) ** .7 + .35
        if ua < u < ub:
            f = ((u - ua) / (ub - ua) * nl + ph) % 1.
            sh = math.sin(_GPI / 2 * min(1., f / .8)) ** .6 * (1 - .75 * _Gsm(.8, 1., f))
            if .45 < f < .85:
                sh *= .88 + .12 * (((f - .45) / .4 * 2) % 1.) ** 1.5
            wo.append(env * (.42 + .58 * sh))
        else:
            wo.append(env * .55)
        wi.append(env * (.6 + .08 * math.sin(u * 9 + ph * 10)))
    R = _GR(pts, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], 1. if W > 3.5 else .5)
    # shadow side: cuts along the form, a dark band where it turns under
    cv.hair(_Gfl(R, .14 * c, .86 * c, 1.5, .02, .97, 3))
    _Gsh(cv, R, c, min(1.8, W * .22) * dark, .35, .97)
    if vein:
        (cv.line if L > 16 else cv.hair)(R.contour(0., .02, .86))
    # each lobe: slanting cuts from the vein toward its front, a drilled notch behind it
    span = (ub - ua) / nl
    m = max(1, min(2, int(span * L / 2.4)))
    for j in range(-1, nl + 1):
        u0 = ua + (j - ph) * span
        if u0 + span * .2 < ua or u0 > ub:
            continue
        for q in range(m):
            ua_ = u0 + span * (.12 + .7 * q / max(1, m))
            if ua_ > .9:
                continue
            cv.hair([R.at(ua_, -.08 * c), R.at(ua_ + span * .16, -.4 * c), R.at(ua_ + span * .3, -.66 * c)])
        if ua + .02 < u0 < ub - .02 and W > 2.5:
            cv.heavy([R.at(u0 - .006, -.97 * c), R.at(u0 + span * .06, -.62 * c)])
    if turn and L > 18:
        k0 = int(n * .86)
        tp = pts[k0:]
        if len(tp) > 3:
            ww = [max(.6, (wo[k0 + i] + wi[k0 + i]) * .4) for i in range(len(tp))]
            T = _GR(tp, ww, ww)
            cv.obj([T.outline()], 1.)
            cv.hair(_Gfl(T, -.7, .7, 1.5, 0., 1., 2))
    return R


def gm_frond(cv, x, y, ang, L, W=None, n=3, spread=.42, bend=.8, curl=3.5, rng=None):
    """A spray of n leaves from one root, the middle one longest; outer ones painted first."""
    rng = rng or random.Random(int(x * 3 + y * 5))
    W = W or L * .26
    sg = 1 if bend >= 0 else -1
    for i in sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2)):
        off = i - (n - 1) / 2
        gm_leaf(cv, x, y, ang + off * spread, L * (1 - .2 * abs(off)) * rng.uniform(.92, 1.04),
                W * (1 - .15 * abs(off)), bend * (1 + .35 * off * sg) * rng.uniform(.9, 1.1),
                curl * rng.uniform(.85, 1.1), rng)


# ---------------------------------------------------------------------------------- the volute

def gm_spine(root, heading, r, turns=1.4, flip=False, tail=0., tail_bend=0., end=.1):
    """A volute's centre line whose stem leaves `root` heading `heading` (radians): tail*r px of
    lead-in stem bending tail_bend radians, then a log spiral from radius r winding in to r*end.
    Clockwise on screen unless flip. Points run root -> eye."""
    sg = -1 if flip else 1
    L = tail * r
    pre = []
    h = heading
    if L > 1:
        pre = _Geu(root[0], root[1], heading, L, lambda u: tail_bend / L, max(6, int(L / 2.5)))
        h = heading + tail_bend
    th = _GTAU * turns
    b = -math.log(end) / th
    a0 = h - sg * (_GPI / 2 + math.atan(b) * 0)
    # start of spiral: tangent along h; centre lies to the inside
    sx, sy = (pre[-1] if pre else root)
    cxx = sx + r * math.cos(h + sg * _GPI / 2)
    cyy = sy + r * math.sin(h + sg * _GPI / 2)
    a0 = math.atan2(sy - cyy, sx - cxx)
    n = max(30, int(r * th * .4))
    sp = []
    for i in range(n + 1):
        t = th * i / n
        rr = r * math.exp(-b * t)
        sp.append((cxx + rr * math.cos(a0 + sg * t), cyy + rr * math.sin(a0 + sg * t)))
    return (pre[:-1] + sp) if pre else sp, (cxx, cyy)


def gm_volute(cv, root, heading, r, turns=1.4, flip=False, tail=0., tail_bend=0., rng=None,
              stem=None, leaves=4, leaf=1., inner=True, eye=None, from_u=0.):
    """A leafy acanthus volute: round-carved stem (dark on the inside of the curl, white
    highlight outside), leaves sheathing its outside that flare and roll their tips out, an
    inner leaf rolling into the eye, a drilled spiral eye (or eye(cv, x, y, r) draws a figure
    there). Returns (centre, spine)."""
    rng = rng or random.Random(int(root[0] * 11 + root[1] * 3))
    pts, (cx, cy) = gm_spine(root, heading, r, turns, flip, tail, tail_bend)
    n = len(pts)
    S = [0.]
    for i in range(1, n):
        S.append(S[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    tot = S[-1] or 1.
    W0 = stem or max(1.6, r * .13)
    ws = [W0 * (1 - .7 * (S[i] / tot) ** 1.15) * (.45 + .55 * _Gsm(0, .06, S[i] / tot)) + .5 for i in range(n)]
    ins = -1 if flip else 1        # +normal side is the inside of a clockwise (screen) spiral
    # leaves first (under the stem), from the eye back so the root ones lie on top
    spots = []
    u = max(.03, from_u)
    lim = .62
    while u < lim and len(spots) < leaves:
        k = min(n - 2, int(u * (n - 1)))
        ta = math.atan2(pts[k + 1][1] - pts[k][1], pts[k + 1][0] - pts[k][0])
        rad = max(3., math.hypot(pts[k][0] - cx, pts[k][1] - cy))
        ll = min(r * 1.5, max(r * .55, rad * 1.25)) * leaf * rng.uniform(.88, 1.05)
        spots.append((k, ta, ll, rad))
        u += ll * .5 / tot
    R = _GR(pts, ws, ws)
    for k, ta, ll, rad in spots[::-1]:
        base = R.at(k / (n - 1), -ins * .3)
        gm_leaf(cv, base[0], base[1], ta - ins * rng.uniform(.18, .32), ll, ll * rng.uniform(.3, .36),
                ins * (ll / rad * .55 + .1), -ins * rng.uniform(2.4, 3.4), rng)
    # the stem
    cv.obj([R.outline()], 1.)
    c = ins
    cv.hair(_Gfl(R, .12 * c, .88 * c, 1.5, 0., 1., 3))
    _Gsh(cv, R, c, W0 * .45, .02, .98)
    cv.hair(R.contour(-.45 * c, .02, .85, minw=2.2))
    # inner leaf curling into the eye
    if inner and r > 9:
        u = .6
        k = int(u * (n - 1))
        ta = math.atan2(pts[k + 1][1] - pts[k][1], pts[k + 1][0] - pts[k][0])
        base = R.at(u, ins * .5)
        ll = r * .72 * leaf
        gm_leaf(cv, base[0], base[1], ta + ins * .25, ll, ll * .3, ins * 1.5, ins * 2.6, rng)
    ex, ey = pts[-1]
    if eye:
        eye(cv, ex, ey, max(2., r * .28))
    else:
        er = max(1.6, ws[-1] * 1.25 + .6)
        cv.obj([_Gel(ex, ey, er + .8, er + .8, 18)[:-1]], 1.)
        sp = []
        for i in range(40):
            t = i / 39
            rr = er * (1 - t) * .95
            a = (6.5 * t) * (-1 if flip else 1)
            sp.append((ex + rr * math.cos(a), ey + rr * math.sin(a)))
        cv.line(sp)
        cv.line([(ex - .3, ey), (ex + .3, ey)])
    return (cx, cy), pts


# ---------------------------------------------------------------------------------- the ground

_GPID = "gmS"


def gm_defs():
    """Stipple tiles: white punch dots in black (1 CSS px and up, irregular in a 10 px tile)."""
    def tile(pid, dots, s=12):
        d = "".join(f"M{x},{y}h0" for x, y in dots)
        return (f'<pattern id="{pid}" width="{s}" height="{s}" patternUnits="userSpaceOnUse">'
                f'<path d="M0,0h{s}v{s}h-{s}z" fill="#000"/><path d="{d}" stroke="#fff" stroke-width="1" '
                f'stroke-linecap="round" fill="none"/></pattern>')
    dark = [(7.5, 8.5), (9.0, 11.0), (1.0, 5.5), (11.0, 7.5), (10.5, 1.5), (5.5, 3.0), (3.5, 10.5), (0.5, 10.0), (2.0, 1.0), (4.0, 7.0), (8.0, 5.0)]
    lite = dark + [(5.5, 11.5), (10.0, 4.0), (2.5, 3.5), (6.0, 6.0), (7.5, 2.0), (1.5, 8.0)]
    grit = ("".join(f"M{x},{y}h0" for x, y in [(1.5, 1.5), (6.5, 2.5), (10.5, .5), (3.5, 6.0), (8.5, 7.5), (.5, 9.5), (5.5, 10.5), (11.0, 11.0), (9.5, 4.5)]))
    gravel = (f'<pattern id="{_GPID}g" width="12" height="12" patternUnits="userSpaceOnUse">'
              f'<path d="{grit}" stroke="#000" stroke-width="1" '
              f'stroke-linecap="round" fill="none"/></pattern>')
    return "<defs>" + tile(_GPID + "d", dark) + tile(_GPID + "l", lite) + gravel + "</defs>"


def gm_ground(shape, tone="d"):
    """The cut-away: black punched with white stipple. shape: (x, y, w, h) or a point list."""
    if isinstance(shape, tuple):
        x, y, w, h = shape
        d = f"M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z"
    else:
        d = _d(shape, True, 0)
    return f'<path d="{d}" fill="url(#{_GPID}{tone})" stroke="none"/>'


def gm_tendrils(x, y, w, h, rng, density=1., avoid=None, florets=True):
    """Background foliage cut into the ground in white: thin vines that wander and roll into tiny
    curls, set with leaflets and five-petal florets. avoid(px, py) -> True skips a start point
    (under the relief, where it would never show). Two elements."""
    lines, fills, dots = [], [], []
    area = w * h
    nv = int(area / 900 * density)
    for _ in range(nv):
        px, py = x + rng.random() * w, y + rng.random() * h
        if avoid and avoid(px, py):
            continue
        a = rng.uniform(0, _GTAU)
        L = rng.uniform(14, 34)
        sg = rng.choice((-1, 1))
        k0 = rng.uniform(.02, .06) * sg
        pts = _Geu(px, py, a, L, lambda u, k0=k0: k0 + sg * .35 * _Gsm(.65, 1., u) ** 2, int(L / 1.5))
        lines.append(pts)
        # leaflets along it, alternating sides
        for j in range(2, len(pts) - 4, 4):
            (ax, ay), (bx, by) = pts[j], pts[j + 1]
            ta = math.atan2(by - ay, bx - ax) + (.8 if j % 8 == 2 else -.8)
            ll = rng.uniform(1.8, 2.8)
            fills.append([(ax, ay), (ax + ll * math.cos(ta), ay + ll * math.sin(ta))])
        if florets and rng.random() < .45:
            ex, ey = pts[-1] if rng.random() < .5 else pts[len(pts) // 2]
            ex += rng.uniform(-3, 3)
            ey += rng.uniform(-3, 3)
            r0 = rng.uniform(1.6, 2.1)
            a0 = rng.random()
            dots.extend((ex + r0 * math.cos(a0 + _GTAU * i / 5), ey + r0 * math.sin(a0 + _GTAU * i / 5)) for i in range(5))
    o = []
    if lines:
        o.append(f'<path d="{"".join(_d(p, tol=.4) for p in lines)}" fill="none" stroke="#fff" stroke-width="1"/>')
    if fills or dots:
        dd = "".join(_d(p, tol=0) for p in fills) + "".join(f"M{_n(p[0])},{_n(p[1])}h0" for p in dots)
        o.append(f'<path d="{dd}" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>')
    return "".join(o)


def gm_cast(cv, dx=1.5, dy=2.):
    """The relief's cast shadow on the ground: every object in cv, offset down-right, in black."""
    pen = _GPen()
    for polys, _, _ in cv.objs:
        for poly in polys:
            pen.add([(p[0] + dx, p[1] + dy) for p in poly], True, .9)
    if not pen.o:
        return ""
    return f'<path transform="scale(.5)" d="{pen.d()}" fill="#000" stroke="none"/>'


def gm_relief(cv, rng, x, y, w, h, density=1., avoid=None):
    """ground stipple + tendrils, the canvas's cast shadow, then the canvas."""
    return gm_cast(cv) + cv.svg()


# ---------------------------------------------------------------------------------- shapes

def gm_shape(kind, cx, cy, a, b, n=120):
    """Cartouche outlines (half-width a, half-height b): oval, cushion, shield, arch, quatre,
    ogee, lozenge."""
    if kind in ("lunette", "archtop"):
        # built from arcs and straights, then resampled evenly (clockwise on screen like the rest)
        raw = []
        rc = min(a, b) * .12
        if kind == "lunette":
            # a half-round: the arc over the top, a flat sill below with eased corners
            for i in range(61):
                t = _GPI + _GPI * i / 60
                raw.append((cx + a * math.cos(t), cy + b - 2 * b * .97 * (-math.sin(t)) + 0))
            raw = [(x, min(y, cy + b - rc)) for x, y in raw]
            raw += [(cx + a - rc * .4, cy + b), (cx - a + rc * .4, cy + b)]
        else:
            # an arched-top window: straight jambs, a round head, a flat sill
            ra = min(a, b * 1.4)
            yc = cy - b + ra * min(1., b / a)
            ry = ra * min(1., b / a)
            for i in range(61):
                t = _GPI + _GPI * i / 60
                raw.append((cx + a * math.cos(t), yc + ry * math.sin(t)))
            raw += [(cx + a, cy + b - rc), (cx + a - rc * .3, cy + b - rc * .3), (cx + a - rc, cy + b),
                    (cx - a + rc, cy + b), (cx - a + rc * .3, cy + b - rc * .3), (cx - a, cy + b - rc)]
        per = sum(math.hypot(raw[i][0] - raw[i - 1][0], raw[i][1] - raw[i - 1][1]) for i in range(len(raw)))
        return [p for p, _ in _g_resample(raw, per / n)]
    pts = []
    for i in range(n):
        t = _GTAU * i / n
        c, s = math.cos(t), math.sin(t)
        if kind in ("oval", "roundel"):
            pts.append((cx + a * c, cy + b * s))
        elif kind == "cushion":
            e = 2.7
            pts.append((cx + a * math.copysign(abs(c) ** (2 / e), c), cy + b * math.copysign(abs(s) ** (2 / e), s)))
        elif kind == "quatre":
            f = 1 + .07 * math.cos(4 * t) - .04
            e = 2.3
            pts.append((cx + a * f * math.copysign(abs(c) ** (2 / e), c), cy + b * f * math.copysign(abs(s) ** (2 / e), s)))
        elif kind == "shield":
            e = 2.8
            xx = math.copysign(abs(c) ** (2 / e), c)
            yy = math.copysign(abs(s) ** (2 / e), s)
            if s > 0:
                xx *= (1 - .55 * s ** 2.2)
                yy = yy * (1 + .12 * s ** 4)
            pts.append((cx + a * xx, cy + b * yy))
        elif kind == "arch":
            e = 3.2 if s > 0 else 2.
            xx = math.copysign(abs(c) ** (2 / e), c)
            yy = math.copysign(abs(s) ** (2 / e), s)
            if s < 0:
                yy *= 1 + .12 * (1 - abs(c)) ** 3
            pts.append((cx + a * xx, cy + b * yy))
        elif kind == "ogee":
            e = 2.2
            xx = math.copysign(abs(c) ** (2 / e), c)
            yy = math.copysign(abs(s) ** (2 / e), s)
            xx *= 1 - .3 * abs(s) ** 3
            pts.append((cx + a * xx, cy + b * yy * (1 + .1 * abs(s) ** 6)))
        else:
            e = 2.4
            pts.append((cx + a * math.copysign(abs(c) ** (2 / e), c), cy + b * math.copysign(abs(s) ** (2 / e), s)))
    return pts


def gm_offset(poly, d):
    """offset a closed (counter-clockwise or clockwise) smooth polygon outward by d px."""
    n = len(poly)
    ar = C._area(poly)
    sg = 1 if ar > 0 else -1
    out = []
    for i in range(n):
        a, b = poly[i - 1], poly[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = ty / tl * sg, -tx / tl * sg
        out.append((poly[i][0] + nx * d, poly[i][1] + ny * d))
    return out


def _g_resample(poly, step):
    pts = poly + [poly[0]]
    S = [0.]
    for i in range(1, len(pts)):
        S.append(S[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out = []
    m = max(8, int(S[-1] / step))
    j = 0
    for k in range(m):
        s = S[-1] * k / m
        while S[j + 1] < s:
            j += 1
        t = (s - S[j]) / max(1e-9, S[j + 1] - S[j])
        p = (pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t)
        q = pts[j + 1]
        out.append((p, math.atan2(q[1] - pts[j][1], q[0] - pts[j][0])))
    return out


def gm_cartouche(kind, cx, cy, a, b, style="bead", bw=None):
    """A carved moulding round a field (a x b half-axes of the field): outer roll, a running
    ornament (bead / rope / egg / leaf / gadroon), a shaded inner bevel and a black sunk fillet.
    Returns (svg, field_polygon)."""
    bw = bw or max(7., min(a, b) * .12)
    field = gm_shape(kind, cx, cy, a, b)
    outer = gm_offset(field, bw)
    cv = C.Canvas()
    cv.obj([outer], 1.)
    rim = gm_offset(field, bw * .82)
    cv.hair([rim + [rim[0]]])
    mid = gm_offset(field, bw * .55)
    zone = bw * .42
    # the running ornament
    if style == "bead":
        rr = max(1., zone * .45)
        for p, ta in _g_resample(mid, rr * 2 + 1.):
            bead = _Gel(p[0], p[1], rr, rr, 10)[:-1]
            cv.obj([bead], .5)
            cv.line(_Gel(p[0] + rr * .15, p[1] + rr * .15, rr * .62, rr * .62, 8, .2, 1.9))
    elif style == "rope":
        for p, ta in _g_resample(mid, 2.5):
            nx, ny = -math.sin(ta), math.cos(ta)
            tx, ty = math.cos(ta), math.sin(ta)
            h = zone * .55
            cv.line([(p[0] - nx * h - tx * 1.2, p[1] - ny * h - ty * 1.2), (p[0], p[1]),
                     (p[0] + nx * h + tx * 1.2, p[1] + ny * h + ty * 1.2)])
    elif style == "egg":
        for i, (p, ta) in enumerate(_g_resample(mid, zone * 1.5)):
            nx, ny = -math.sin(ta), math.cos(ta)
            egg = [_g_rot((p[0] + zone * .62 * math.cos(t), p[1] + zone * .42 * math.sin(t)), p, ta + _GPI / 2)
                   for t in [_GTAU * j / 12 for j in range(12)]]
            cv.obj([egg], .5)
            cv.hair(_Ghp(egg, math.degrees(ta) + 45, 1.5)[:2])
            q = (p[0] + math.cos(ta) * zone * .75, p[1] + math.sin(ta) * zone * .75)
            cv.obj([], 0)
            cv.heavy([(q[0] - nx * zone * .5, q[1] - ny * zone * .5), (q[0] + nx * zone * .3, q[1] + ny * zone * .3)])
    elif style == "leaf":
        for p, ta in _g_resample(mid, zone * 1.3):
            nx, ny = -math.sin(ta), math.cos(ta)
            base = (p[0] - math.cos(ta) * zone * .6, p[1] - math.sin(ta) * zone * .6)
            tip = (p[0] + math.cos(ta) * zone * .9, p[1] + math.sin(ta) * zone * .9)
            lf = [base, (p[0] + nx * zone * .48, p[1] + ny * zone * .48), tip, (p[0] - nx * zone * .48, p[1] - ny * zone * .48)]
            cv.obj([lf], .5)
            cv.hair([base, tip])
            cv.hair([(p[0] - nx * zone * .3, p[1] - ny * zone * .3), tip])
    else:  # gadroon
        for p, ta in _g_resample(mid, 3.):
            nx, ny = -math.sin(ta), math.cos(ta)
            h = zone * .6
            cv.line([(p[0] - nx * h, p[1] - ny * h), (p[0] + math.cos(ta) * .8, p[1] + math.sin(ta) * .8),
                     (p[0] + nx * h, p[1] + ny * h)])
    # inner bevel shaded with lines that run across it (light on the upper left)
    bev_o = gm_offset(field, bw * .26)
    for p, ta in _g_resample(bev_o, 1.5):
        nx, ny = -math.sin(ta), math.cos(ta)
        lit = (nx * -.7 + ny * -.7)
        if lit < .45:
            L = bw * .24 * (1. if lit < -.2 else .55)
            cv.obj([], 0) if False else None
            cv.hair([(p[0], p[1]), (p[0] - nx * L, p[1] - ny * L)])
    cv.heavy([gm_offset(field, 1.)[:] + [gm_offset(field, 1.)[0]]])
    return cv, field


# ---------------------------------------------------------------------------------- lettering

_GH = 1.5
_GL = .5
_GLY = {}


def _g_arc(cx, cy, rx, ry, a0, a1, n=12):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _g_def():
    A = _g_arc
    g = {
        "A": (.74, [("h", [(.37, 0), (.72, 1)]), ("l", [(.37, 0), (.02, 1)]), ("l", [(.17, .64), (.57, .64)]),
                    ("l", [(-.06, 1), (.12, 1)]), ("l", [(.62, 1), (.82, 1)])]),
        "B": (.6, [("h", [(0, 0), (0, 1)]), ("l", [(0, 0), (.32, 0)] + A(.32, .245, .22, .245, -90, 90) + [(0, .49)]),
                   ("l", [(0, .49), (.36, .49)] + A(.36, .745, .25, .255, -90, 90) + [(0, 1)]),
                   ("h", A(.33, .245, .19, .2, -50, 50, 6)), ("h", A(.37, .745, .22, .21, -50, 50, 6))]),
        "C": (.7, [("l", A(.42, .5, .4, .5, -40, -320, 20)), ("h", A(.42, .5, .36, .45, 145, 215, 6))]),
        "D": (.74, [("h", [(0, 0), (0, 1)]), ("l", [(0, 0), (.3, 0)] + A(.3, .5, .42, .5, -90, 90, 14) + [(0, 1)]),
                    ("h", A(.3, .5, .38, .44, -50, 50, 6))]),
        "E": (.58, [("h", [(0, 0), (0, 1)]), ("l", [(0, 0), (.54, 0), (.56, .14)]), ("l", [(0, .5), (.4, .5)]),
                    ("l", [(0, 1), (.58, 1), (.6, .84)])]),
        "F": (.56, [("h", [(0, 0), (0, 1)]), ("l", [(0, 0), (.54, 0), (.56, .14)]), ("l", [(0, .5), (.4, .5)])]),
        "G": (.76, [("l", A(.42, .5, .4, .5, -40, -330, 20)), ("h", A(.42, .5, .36, .45, 145, 215, 6)),
                    ("h", [(.8, .6), (.8, .95)]), ("l", [(.56, .6), (.9, .6)])]),
        "H": (.74, [("h", [(0, 0), (0, 1)]), ("h", [(.74, 0), (.74, 1)]), ("l", [(0, .5), (.74, .5)])]),
        "I": (0., [("h", [(0, 0), (0, 1)])]),
        "J": (.4, [("h", [(.4, 0), (.4, .78)]), ("l", A(.2, .78, .2, .22, 0, 160, 8))]),
        "K": (.66, [("h", [(0, 0), (0, 1)]), ("l", [(.62, 0), (0, .6)]), ("h", [(.22, .42), (.68, 1)])]),
        "L": (.56, [("h", [(0, 0), (0, 1)]), ("l", [(0, 1), (.56, 1), (.58, .84)])]),
        "M": (.88, [("l", [(0, 1), (.06, 0)]), ("h", [(.06, 0), (.44, 1)]), ("l", [(.44, 1), (.82, 0)]),
                    ("h", [(.82, 0), (.88, 1)])]),
        "N": (.72, [("l", [(0, 1), (0, 0)]), ("h", [(0, 0), (.72, 1)]), ("l", [(.72, 1), (.72, 0)])]),
        "O": (.8, [("l", A(.4, .5, .41, .5, 0, 360, 24)), ("h", A(.4, .5, .36, .46, 150, 210, 6)),
                   ("h", A(.4, .5, .36, .46, -30, 30, 6))]),
        "P": (.6, [("h", [(0, 0), (0, 1)]), ("l", [(0, 0), (.32, 0)] + A(.32, .27, .26, .27, -90, 90) + [(0, .54)]),
                   ("h", A(.33, .27, .22, .22, -50, 50, 6))]),
        "Q": (.8, [("l", A(.4, .5, .41, .5, 0, 360, 24)), ("h", A(.4, .5, .36, .46, 150, 210, 6)),
                   ("h", A(.4, .5, .36, .46, -30, 30, 6)), ("h", [(.42, .88), (.8, 1.1)])]),
        "R": (.66, [("h", [(0, 0), (0, 1)]), ("l", [(0, 0), (.32, 0)] + A(.32, .26, .26, .26, -90, 90) + [(0, .52)]),
                    ("h", A(.33, .26, .22, .21, -50, 50, 6)), ("h", [(.3, .52), (.68, 1)])]),
        "S": (.6, [("l", [(.56, .14), (.46, .03), (.28, 0), (.1, .07), (.04, .22)]),
                   ("h", [(.04, .22), (.14, .37), (.32, .47), (.48, .56), (.58, .7), (.56, .86)]),
                   ("l", [(.56, .86), (.42, .98), (.22, 1), (.05, .93), (.02, .82)])]),
        "T": (.7, [("l", [(-.02, .14), (0, 0), (.7, 0), (.72, .14)]), ("h", [(.35, 0), (.35, 1)])]),
        "U": (.72, [("h", [(0, 0), (0, .7)]), ("l", A(.36, .7, .36, .3, 180, 0, 10)), ("l", [(.72, .7), (.72, 0)])]),
        "V": (.72, [("h", [(0, 0), (.36, 1)]), ("l", [(.36, 1), (.72, 0)])]),
        "W": (1., [("h", [(0, 0), (.24, 1)]), ("l", [(.24, 1), (.5, .1)]), ("h", [(.5, .1), (.76, 1)]), ("l", [(.76, 1), (1., 0)])]),
        "X": (.68, [("h", [(0, 0), (.68, 1)]), ("l", [(.68, 0), (0, 1)])]),
        "Y": (.68, [("h", [(0, 0), (.34, .52)]), ("l", [(.68, 0), (.34, .52)]), ("h", [(.34, .52), (.34, 1)])]),
        "Z": (.62, [("l", [(0, 0), (.62, 0)]), ("h", [(.62, 0), (0, 1)]), ("l", [(0, 1), (.64, 1), (.66, .86)])]),
        "0": (.56, [("l", A(.28, .5, .28, .5, 0, 360, 20)), ("h", A(.28, .5, .24, .46, 150, 210, 6)),
                    ("h", A(.28, .5, .24, .46, -30, 30, 6))]),
        "1": (.3, [("h", [(.2, 0), (.2, 1)]), ("l", [(.2, 0), (0, .16)]), ("l", [(0, 1), (.4, 1)])]),
        "2": (.56, [("l", A(.28, .27, .26, .27, 200, 360, 10) + [(.5, .44)]), ("h", [(.5, .44), (0, 1)]), ("l", [(0, 1), (.56, 1)])]),
        "3": (.54, [("l", A(.26, .25, .24, .25, 200, 450, 12)), ("l", A(.26, .74, .27, .26, -90, 160, 12)),
                    ("h", A(.26, .74, .24, .22, -50, 50, 6))]),
        "4": (.6, [("l", [(.44, 0), (0, .72), (.6, .72)]), ("h", [(.44, 0), (.44, 1)])]),
        "5": (.54, [("l", [(.52, 0), (.08, 0)]), ("h", [(.08, 0), (.04, .44)]), ("l", [(.04, .44)] + A(.26, .7, .27, .3, -110, 160, 12))]),
        "6": (.56, [("h", A(.3, .5, .28, .5, 230, 130, 10)), ("l", A(.28, .7, .26, .3, 0, 360, 14))]),
        "7": (.56, [("l", [(0, 0), (.56, 0)]), ("h", [(.56, 0), (.2, 1)])]),
        "8": (.56, [("l", A(.28, .25, .22, .25, 0, 360, 14)), ("l", A(.28, .74, .27, .26, 0, 360, 14)),
                    ("h", A(.28, .74, .24, .22, -50, 50, 6))]),
        "9": (.56, [("l", A(.28, .3, .26, .3, 0, 360, 14)), ("h", A(.26, .5, .28, .5, -50, 50, 10))]),
        "·": (.1, [("h", A(.05, .52, .06, .06, 0, 360, 6))]),
        ".": (.1, [("h", A(.05, .94, .06, .06, 0, 360, 6))]),
        ",": (.12, [("h", [(.08, .9), (.02, 1.12)])]),
        "'": (.1, [("h", [(.05, 0), (.03, .22)])]),
        "-": (.36, [("l", [(0, .55), (.36, .55)])]),
        "&": (.7, [("l", [(.7, 1), (.12, .36)] + A(.26, .2, .16, .2, 150, 380, 8) + [(.08, .68)] + A(.28, .78, .24, .22, 180, 70, 8) + [(.66, .5)])]),
        "%": (.6, [("l", A(.12, .16, .1, .14, 0, 360, 8)), ("l", A(.48, .84, .1, .14, 0, 360, 8)), ("h", [(.56, 0), (.04, 1)])]),
        "$": (.56, [("l", [(.52, .2), (.4, .1), (.2, .1), (.06, .22), (.08, .38), (.3, .48), (.5, .6), (.52, .78), (.36, .9), (.16, .9), (.02, .8)]),
                    ("h", [(.28, -.05), (.28, 1.05)])]),
        " ": (.34, []),
    }
    _GLY.update(g)


_g_def()


def gm_text_width(s, cap, track=.3):
    s = s.upper()
    return sum((_GLY.get(ch, _GLY[" "])[0] + track) * cap for ch in s) - track * cap


def gm_letters(s, cap, along=None, cx=0., cy=0., track=.3):
    """Engraved Roman capitals: thick strokes and hairlines with bracketed serifs.
    along(offset) -> (x, y, angle) bends the line. Returns {weight: [polylines]}."""
    s = s.upper()
    tw = gm_text_width(s, cap, track)
    x = -tw / 2
    hv = 1.5 if cap >= 8 else 1.
    out = {hv: [], .5: []}
    for ch in s:
        gw, strokes = _GLY.get(ch, _GLY[" "])
        mid = x + gw * cap / 2
        px, py, a = along(mid) if along else (cx + mid, cy, 0.)
        ca, sa = math.cos(a), math.sin(a)

        def T(u, v):
            lx, ly = (u - gw / 2) * cap, (v - .5) * cap
            return (px + lx * ca - ly * sa, py + lx * sa + ly * ca)
        for wt, st in strokes:
            out[hv if wt == "h" else .5].append([T(u, v) for u, v in st])
            if wt == "h" and len(st) == 2:
                for (u, v) in st:
                    if v in (0, 1) and abs(st[1][0] - st[0][0]) < .5:
                        out[.5].append([T(u - .1, v), T(u + .1, v)])
        x += (gw + track) * cap
    return out


def gm_letters_svg(groups, color="#000"):
    o = []
    for wt, pls in groups.items():
        if pls:
            o.append(f'<path d="{"".join(_d(p, tol=.08) for p in pls)}" fill="none" stroke="{color}" stroke-width="{_n(wt)}"/>')
    return "".join(o)


def gm_along(centre):
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    mid = S[-1] / 2

    def f(off):
        s = mid + off
        for i in range(1, len(S)):
            if S[i] >= s:
                t = (s - S[i - 1]) / max(1e-6, S[i] - S[i - 1])
                return (centre[i - 1][0] + (centre[i][0] - centre[i - 1][0]) * t,
                        centre[i - 1][1] + (centre[i][1] - centre[i - 1][1]) * t,
                        math.atan2(centre[i][1] - centre[i - 1][1], centre[i][0] - centre[i - 1][0]))
        return centre[-1][0], centre[-1][1], 0.
    return f


# ---------------------------------------------------------------------------------- the banner

def gm_banner(cx, cy, w, h, arch=.05, text="", wave=.25):
    """A twisting ribbon: a lettered face (white, it carries the text) arched and gently waved,
    turning back at each end over shaded folds into forked tails that curl down behind.
    Returns svg."""
    cv = C.Canvas()
    fw = w * .72
    n = 48
    centre = [(cx - fw / 2 + fw * i / n, cy - arch * w * math.sin(_GPI * i / n) + wave * h * math.sin(_GTAU * i / n))
              for i in range(n + 1)]
    R = _GR(centre, [h / 2] * (n + 1), [h / 2] * (n + 1))
    for side in (-1, 1):
        e = centre[0] if side < 0 else centre[-1]
        tl = (w - fw) / 2 + h * .4
        sx, sy = e[0] - side * h * .35, e[1] + h * .5
        tp = _Geu(sx, sy, (_GPI if side < 0 else 0.) + side * .25, tl,
                  lambda u, sd=side: -sd * 1.8 * _Gsm(.4, 1, u) / tl, 24)
        T = _GR(tp, [h * .44] * len(tp), [h * .44] * len(tp))
        ol = T.outline()
        tip = tp[-1]
        a = math.atan2(tp[-1][1] - tp[-2][1], tp[-1][0] - tp[-2][0])
        notch = (tip[0] - math.cos(a) * h * .55, tip[1] - math.sin(a) * h * .55)
        k = len(ol) // 2
        ol = ol[:k] + [notch] + ol[k:]
        cv.obj([ol], 1.)
        cv.hair(_Gfl(T, -.85, .85, 1.5, 0., .92, 3))
        _Gsh(cv, T, -1 if side < 0 else 1, h * .18, .05, .9)
        p0, p1 = R.at(0 if side < 0 else 1, 1), R.at(0 if side < 0 else 1, -1)
        fold = [p0, p1, T.at(0, -1), T.at(0, 1)]
        if C._area(fold) * C._area([p0, p1, T.at(0, 1), T.at(0, -1)]) > 0 and abs(C._area(fold)) < abs(C._area([p0, p1, T.at(0, 1), T.at(0, -1)])):
            fold = [p0, p1, T.at(0, 1), T.at(0, -1)]
        cv.obj([fold], 1.)
        cv.line(_Ghp(fold, -45 * side, 1.5, inset=.2))
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(.8, 0., 1.))
    cv.hair(R.contour(-.8, 0., 1.))
    # the face rolls: shade lines across it where it turns toward the folds and in the wave troughs
    for i in range(n + 1):
        u = i / n
        sh = max(1 - _Gsm(0., .1, u), _Gsm(.9, 1., u))
        tw_ = math.cos(_GTAU * u)
        if sh > .25:
            cv.hair([R.at(u, -.7), R.at(u, -.7 + 1.4 * sh)])
    _Gsh(cv, R, -1, h * .12, .03, .97)
    o = cv.svg()
    if text:
        cap = h * .52
        while gm_text_width(text, cap) > fw * .8 and cap > 4:
            cap *= .94
        o += gm_letters_svg(gm_letters(text, cap, gm_along(centre)))
    return o, centre


# ---------------------------------------------------------------------------------- architecture

def gm_bar(x, y, w, h):
    """A knurled rod shaded as a cylinder: lit top fillet, diagonal knurl, dark underside."""
    r = h / 2
    body = (f"M{_n(x + r)},{_n(y)}h{_n(w - 2 * r)}a{_n(r)},{_n(r)} 0 0,1 0,{_n(h)}"
            f"h{_n(-(w - 2 * r))}a{_n(r)},{_n(r)} 0 0,1 0,{_n(-h)}z")
    k = f"M{_n(x + r * .7)},{_n(y + h * .3)}h{_n(w - r * 1.4)}v{_n(h * .42)}h{_n(-(w - r * 1.4))}z"
    sh = f"M{_n(x + r * .8)},{_n(y + h * .72)}h{_n(w - r * 1.6)}v{_n(h * .2)}h{_n(-(w - r * 1.6))}z"
    return (f'<path d="{body}" fill="#fff" stroke="#000" stroke-width="1"/>'
            f'<path d="{k}" fill="{C.pat("K")}" stroke="none"/>'
            f'<path d="{sh}" fill="{C.pat("G")}" stroke="none"/>'
            f'<path d="M{_n(x + r)},{_n(y + h * .16)}h{_n(w - 2 * r)}" stroke="#000" stroke-width=".5"/>')


def gm_rosette(cv, cx, cy, r, rng, petals=8):
    """A carved rosette: shaded petals round a drilled boss."""
    cv.obj([_Gel(cx, cy, r, r, 28)[:-1]], 1.)
    for i in range(petals):
        a = _GTAU * i / petals + .2
        L = r * .95
        gm_leaf(cv, cx + math.cos(a) * r * .22, cy + math.sin(a) * r * .22, a, L * .8, L * .42, .3, 1., rng, lobes=2, turn=False, vein=False)
    cv.obj([_Gel(cx, cy, r * .26, r * .26, 12)[:-1]], 1.)
    cv.line(_Gel(cx + r * .04, cy + r * .04, r * .14, r * .14, 8))


def gm_pedestal(x, y, w, h, rng, tablet=None, rosette=None):
    """Codex base filling x..x+w, y..y+h: knurled cornice; a slab whose top is seen in
    perspective and whose front is a stippled cut-away carved with tendrils round a moulded,
    bevelled tablet (tablet(tx, ty, tw, th) -> svg); rosettes either side (rosette(cv, x, y, r)
    may replace one); a second knurled bar; a gadrooned, flared plinth. Returns svg."""
    o = []
    kb = max(6., min(10., h * .12))
    inset = w * .03
    o.append(gm_bar(x, y, w, kb))
    yy = y + kb
    slab = h * .5
    top = slab * .2
    # top surface in perspective: converging rules model the receding plane
    tp = [(x + inset, yy), (x + w - inset, yy), (x + w - inset * 1.5, yy + top), (x + inset * 1.5, yy + top)]
    cv = C.Canvas()
    cv.obj([tp], .5)
    for i in range(1, 40):
        t = i / 40
        cv.hair([(x + inset + (w - 2 * inset) * t, yy), (x + inset * 1.5 + (w - 3 * inset) * t, yy + top)])
    o.append(cv.svg())
    fy, fh = yy + top, slab - top
    fx, fw_ = x + inset * 1.5, w - 3 * inset
    o.append(gm_ground((fx, fy, fw_, fh)))
    o.append(gm_tendrils(fx, fy, fw_, fh, rng, 1.3))
    o.append(f'<path d="M{_n(fx)},{_n(fy)}h{_n(fw_)}v{_n(fh)}h{_n(-fw_)}z" fill="none" stroke="#000" stroke-width="1"/>')
    th = fh * .72
    tw = w * .58
    tx, ty = x + (w - tw) / 2, fy + (fh - th) / 2
    # moulded tablet: bevel frame lit top-left, dark bottom-right
    bv = min(4., th * .14)
    cvb = C.Canvas()
    cvb.obj([[(tx - bv, ty - bv), (tx + tw + bv, ty - bv), (tx + tw + bv, ty + th + bv), (tx - bv, ty + th + bv)]], 1.)
    cvb.hair(_Ghp([(tx + tw, ty), (tx + tw + bv, ty - bv), (tx + tw + bv, ty + th + bv), (tx - bv, ty + th + bv), (tx, ty + th)], 45, 1.5))
    cvb.line(_Ghp([(tx + tw, ty + th * .3), (tx + tw + bv, ty), (tx + tw + bv, ty + th + bv), (tx + tw * .7, ty + th + bv)], -45, 1.5)[:6])
    o.append(cvb.svg())
    o.append(f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    if tablet:
        o.append(tablet(tx, ty, tw, th))
    rcv = C.Canvas()
    for sx in (-1, 1):
        rx = x + w / 2 + sx * (tw / 2 + (fw_ - tw) / 4)
        rr = min(fh * .36, (fw_ - tw) / 4 - 3, 13)
        if rosette and sx > 0:
            rosette(rcv, rx, fy + fh / 2, rr)
        else:
            gm_rosette(rcv, rx, fy + fh / 2, rr, rng)
    o.append(gm_cast(rcv, 1., 1.5) + rcv.svg())
    yy = fy + fh
    o.append(gm_bar(x + inset * .5, yy, w - inset, kb))
    yy += kb
    ph = y + h - yy
    if ph > 4:
        fl = [(x + inset * 1.4 - inset * 1.3 * (i / 12) ** 2.2, yy + ph * i / 12) for i in range(13)]
        fr = [(2 * x + w - p[0], p[1]) for p in fl[::-1]]
        poly = fl + fr
        cvp = C.Canvas()
        cvp.obj([poly], 1.)
        # gadroons: tongues that swell toward the foot, shaded on one side
        nG = int(w / 9)
        for i in range(nG):
            t = (i + .5) / nG
            xa = x + inset * 1.4 + (w - inset * 2.8) * t
            xb = x + inset * .1 + (w - inset * .2) * t
            g = [(xa - 3, yy + .5), (xa + 3, yy + .5), (xb + 3.6, y + h - 1.5), (xb - 3.6, y + h - 1.5)]
            cvp.hair([(xa - 3.2, yy + .5), (xb - 3.8, y + h - 1)])
            cvp.hair(_Ghp([(xa + .5, yy + .5), (xa + 3, yy + .5), (xb + 3.6, y + h - 1.5), (xb + .6, y + h - 1.5)], 90 + (xb - xa) * 2, 1.5))
            cvp.line([((xa + xb) / 2 + 2.2, yy + ph * .55), ((xa + xb) / 2 + 2.6, y + h - 2)])
        o.append(cvp.svg())
    return "".join(o), (tx, ty, tw, th)


# ---------------------------------------------------------------------------------- fine scroll

def _g_spiral(root, heading, r, turns, flip, tail, tail_bend, end=.09):
    return gm_spine(root, heading, r, turns, flip, tail, tail_bend, end)


def gm_scroll_unit(cv, pts, centre, r, flip, rng, nleaves, leaf=1., eye=None):
    """Paint one fine scroll along its spine: leaves first, then the round-cut stem and the eye."""
    n = len(pts)
    S = [0.]
    for i in range(1, n):
        S.append(S[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    tot = S[-1] or 1.
    W0 = max(.9, r * .085)
    ws = [W0 * (1 - .6 * (S[i] / tot) ** 1.1) * (.55 + .45 * _Gsm(0, .05, S[i] / tot)) + .45 for i in range(n)]
    ins = -1 if flip else 1
    R = _GR(pts, ws, ws)
    cx, cy = centre
    spots = []
    if nleaves:
        lo, hi = .03, .4
        for j in range(nleaves):
            spots.append(lo + (hi - lo) * (j + rng.uniform(.3, .7)) / nleaves)
    for j, u in enumerate(spots[::-1]):
        k = min(n - 2, int(u * (n - 1)))
        ta = math.atan2(pts[k + 1][1] - pts[k][1], pts[k + 1][0] - pts[k][0])
        rad = max(2., math.hypot(pts[k][0] - cx, pts[k][1] - cy))
        ll = r * (1.55 - .3 * (len(spots) - 1 - j) / max(1, len(spots))) * leaf * rng.uniform(.88, 1.06)
        base = R.at(k / (n - 1), -ins * .3)
        gm_leaf(cv, base[0], base[1], ta - ins * rng.uniform(.2, .35), ll, ll * rng.uniform(.26, .32),
                ins * (ll / (rad * 1.25)), -ins * rng.uniform(.8, 1.3), rng)
    cv.obj([R.outline()], 1. if r > 9 else .5)
    c = ins
    cv.hair(R.contour(.35 * c, 0., .9, minw=1.6))
    cv.hair(R.contour(-.5 * c, .05, .5, minw=2.4))
    ex, ey = pts[-1]
    if eye:
        eye(cv, ex, ey, max(2., r * .3))
        return R
    er = max(1.2, ws[-1] * 1.1 + .5)
    cv.obj([_Gel(ex, ey, er + .6, er + .6, 14)[:-1]], .5)
    sp = []
    for i in range(24):
        t = i / 23
        rr = er * (1 - t) * .95
        a = (5.5 * t) * (-1 if flip else 1) + math.atan2(ey - cy, ex - cx)
        sp.append((ex + rr * math.cos(a), ey + rr * math.sin(a)))
    cv.line(sp)
    return R


class GmField:
    """Fine scroll grown from stem sources into a region, Ken Hunt fashion: every scroll a true
    log spiral ending in a drilled curl, throwing smaller scrolls off its outside in alternating
    S-rhythm, each sheathed by leaves; packed until no gap larger than rmin is left.
    inside(x, y) -> True where scroll may grow; holes: list of ('c', x, y, r) / ('r', x0, y0, x1, y1)."""

    def __init__(self, x, y, w, h, rng, inside=None, holes=(), rmin=5., rmax=16., overlap=.9):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.rng = rng
        self.inside = inside or (lambda px, py: x <= px <= x + w and y <= py <= y + h)
        self.holes = list(holes)
        self.rmin, self.rmax, self.ov = rmin, rmax, overlap
        self.discs = []
        self.cell = max(8., rmax * 1.5)
        self.grid = {}
        self.units = []
        self.cap = 1 << 30

    def _near(self, px, py, rr):
        c = self.cell
        i0, i1 = int((px - rr) // c) - 1, int((px + rr) // c) + 1
        j0, j1 = int((py - rr) // c) - 1, int((py + rr) // c) + 1
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                for d in self.grid.get((i, j), ()):
                    yield d

    def _hole_d(self, px, py):
        best = 1e9
        for sh in self.holes:
            best = min(best, C._shape_dist(px, py, sh))
        return best

    def free(self, px, py, r):
        if not self.inside(px, py):
            return False
        if self._hole_d(px, py) < r * .55:
            return False
        for (qx, qy, qr) in self._near(px, py, r + self.rmax * 1.3):
            if math.hypot(px - qx, py - qy) < (r * .84 + qr) * self.ov:
                return False
        return True

    def _add(self, px, py, r):
        d = (px, py, r)
        self.discs.append(d)
        c = self.cell
        self.grid.setdefault((int(px // c), int(py // c)), []).append(d)

    def grow(self, root, heading, r, flip, depth=0, eye=None, turns=None):
        """try to place a scroll whose stem leaves root heading `heading`; recurse into children."""
        q = [(root, heading, r, flip, depth, eye, turns)]
        while q:
            q.sort(key=lambda t: -t[2])
            root, heading, r, flip, depth, eye, turns = q.pop(0)
            if len(self.units) >= self.cap:
                break
            placed = None
            rr = r
            for _ in range(4):
                if rr < self.rmin:
                    break
                tail = self.rng.uniform(.5, .9)
                tb = (-1 if flip else 1) * self.rng.uniform(-.2, .5)
                tn = turns or self.rng.uniform(1.15, 1.45)
                pts, cen = _g_spiral(root, heading, rr, tn, flip, tail, tb)
                if self.free(cen[0], cen[1], rr):
                    placed = (pts, cen, rr, tn)
                    break
                rr *= .78
            if not placed:
                continue
            pts, cen, rr, tn = placed
            self._add(cen[0], cen[1], rr * .84)
            # the tail occupies too: a small disc at its midpoint
            m = pts[len(pts) // 6]
            self.units.append((pts, cen, rr, flip, self.rng.randrange(1 << 30), eye))
            n = len(pts)
            # children from the outside of the outer turn and from the tail
            kids = (.06, .24, .42) if rr > self.rmin * 2.2 else (.1, .32)
            for j, u in enumerate(kids):
                k = min(n - 2, int(u * (n - 1)))
                ta = math.atan2(pts[k + 1][1] - pts[k][1], pts[k + 1][0] - pts[k][0])
                out = 1 if flip else -1            # outward normal side sign for heading rotation
                hd = ta + out * self.rng.uniform(.55, 1.0)
                cr = rr * self.rng.uniform(.55, .78)
                q.append((pts[k], hd, cr, not flip, depth + 1, None, None))

    def pack(self, step=None, tries=600):
        """gap fill: scrolls sized to every gap left, springing toward their nearest neighbour."""
        step = step or self.rmin * 1.1
        rng = self.rng
        pts = []
        yy = self.y + step / 2
        while yy < self.y + self.h:
            xx = self.x + step / 2 + (step / 2 if int((yy - self.y) / step) % 2 else 0)
            while xx < self.x + self.w:
                pts.append((xx + rng.uniform(-1, 1), yy + rng.uniform(-1, 1)))
                xx += step
            yy += step
        rng.shuffle(pts)
        cand = []
        for (px, py) in pts:
            if not self.inside(px, py) or self._hole_d(px, py) < self.rmin * .6:
                continue
            best = self._hole_d(px, py) / .55
            nb = None
            for (qx, qy, qr) in self._near(px, py, self.rmax * 3):
                dd = math.hypot(px - qx, py - qy) / self.ov - qr
                if dd < best:
                    best, nb = dd, (qx, qy)
            cand.append((min(best, self.rmax), px, py, nb))
        cand.sort(key=lambda t: -t[0])
        for r, px, py, nb in cand:
            if len(self.units) >= self.cap:
                break
            r = min(r, self.rmax) * .95
            if r < self.rmin or not self.free(px, py, r):
                continue
            flip = rng.random() < .5
            if nb:
                a = math.atan2(py - nb[1], px - nb[0])
            else:
                a = rng.uniform(0, _GTAU)
            # root on the side toward the neighbour, stem heading tangentially
            root = (px - math.cos(a) * r, py - math.sin(a) * r)
            hd = a + (-_GPI / 2 if not flip else _GPI / 2)
            pts_, cen = _g_spiral(root, hd, r, rng.uniform(1.2, 1.45), flip, .0, 0.)
            self._add(px, py, r * .84)
            self.units.append((pts_, cen, r, flip, rng.randrange(1 << 30), None))

    def paint(self, cv, leaf=1.):
        for pts, cen, r, flip, sd, eye in self.units[::-1]:
            rng = random.Random(sd)
            nl = 1 if r < 7 else 2 if r < 12 else 3
            gm_scroll_unit(cv, pts, cen, r, flip, rng, nl, leaf, eye)


# ---------------------------------------------------------------------------------- gold lines

def gm_goldline(poly, widths=(1.5, 1.), gap=2., beads=True, closed=True):
    """Fine inlaid border following a shape: white wire lines (>= 1 px) on the black ground with
    a beaded row between them. poly: the line's path (closed polygon or open polyline)."""
    o = []
    pa = poly + ([poly[0]] if closed else [])
    o.append(f'<path d="{_d(pa, tol=.1)}" fill="none" stroke="#fff" stroke-width="{_n(widths[0] + 2)}"/>')
    o.append(f'<path d="{_d(pa, tol=.1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def gm_frame_lines(poly, d0=0., rng=None, bead_r=1., closed=True):
    """Triple wire border: an outer white line, a bead row, an inner white line, each following
    the shape (offsets of the closed poly, inward positive). Returns svg (3-4 elements)."""
    def off(dd):
        return gm_offset(poly, -dd)
    a = off(d0 + 1.)
    b = off(d0 + 3.5 + bead_r)
    cl = off(d0 + 6. + 2 * bead_r)
    o = [f'<path d="{_d(a + [a[0]], tol=.1)}{_d(cl + [cl[0]], tol=.1)}" fill="none" stroke="#fff" stroke-width="1.5"/>',
         f'<path d="{_d(a + [a[0]], tol=.1)}{_d(cl + [cl[0]], tol=.1)}" fill="none" stroke="#000" stroke-width=".5"/>']
    dots = "".join(f"M{_n(p[0])},{_n(p[1])}h0" for p, _ in _g_resample(b, bead_r * 2 + 1.5))
    o.append(f'<path d="{dots}" fill="none" stroke="#fff" stroke-width="{_n(bead_r * 2)}" stroke-linecap="round"/>')
    return "".join(o), d0 + 7. + 2 * bead_r


def gm_medallion(kind, cx, cy, a, b, bead_r=1.5):
    """An inlaid portrait medallion: double wire ring with a bold bead row between, black sunk
    fillet. a, b: half-axes of the scene field. Returns (svg_ring, field_poly, outer_poly)."""
    field = gm_shape(kind, cx, cy, a, b)
    r1 = gm_offset(field, 1.2)
    r2 = gm_offset(field, 3. + bead_r)
    r3 = gm_offset(field, 5. + 2 * bead_r)
    r4 = gm_offset(field, 6.5 + 2 * bead_r)
    o = [f'<path d="{_d(r4, True, .1)}{_d(field[::-1], True, .1)}" fill="#000" stroke="none" fill-rule="evenodd"/>',
         f'<path d="{_d(r1 + [r1[0]], tol=.1)}{_d(r3 + [r3[0]], tol=.1)}" fill="none" stroke="#fff" stroke-width="1"/>']
    rr = bead_r
    bp = _g_resample(r2, rr * 2 + 1.2)
    o.append(f'<path d="{"".join(f"M{_n(p[0])},{_n(p[1])}h0" for p, _ in bp)}" fill="none" stroke="#fff" stroke-width="{_n(rr * 2)}" stroke-linecap="round"/>')
    o.append(f'<path d="{"".join(f"M{_n(p[0] + rr * .35)},{_n(p[1] + rr * .35)}h0" for p, _ in bp)}" fill="none" stroke="#000" stroke-width="{_n(max(.5, rr * .6))}" stroke-linecap="round"/>')
    o.append(f'<path d="{_d(r4 + [r4[0]], tol=.1)}" fill="none" stroke="#fff" stroke-width="1.5"/>')
    return "".join(o), field, r4


def gm_sun_drums(cv, cx, cy, s, rng):
    """The placeholder for Parker's arms: crossed drumsticks over a rayed sun."""
    R = s * .42
    for i in range(16):
        a = _GTAU * i / 16
        r1 = R * (1.55 if i % 2 else 1.25)
        w = .16 if i % 2 else .1
        p = [(cx + R * 1.05 * math.cos(a - w), cy + R * 1.05 * math.sin(a - w)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
             (cx + R * 1.05 * math.cos(a + w), cy + R * 1.05 * math.sin(a + w))]
        cv.obj([p], .5)
        cv.hair([(cx + R * 1.1 * math.cos(a + w * .3), cy + R * 1.1 * math.sin(a + w * .3)), (cx + r1 * .92 * math.cos(a), cy + r1 * .92 * math.sin(a))])
    disc = _Gel(cx, cy, R, R, 28)[:-1]
    cv.obj([disc], 1.)
    cv.hair(_Ghp(_Gel(cx + R * .15, cy + R * .15, R * .8, R * .8, 20)[:-1], 45, 1.5))
    for sd in (-1, 1):
        a = math.radians(90 + sd * 38)
        L = s * 1.05
        p0 = (cx - math.cos(a) * L * .5, cy + math.sin(a) * L * .5)
        p1 = (cx + math.cos(a) * L * .5, cy - math.sin(a) * L * .5)
        ww = [max(.7, s * .045 * (1 - .55 * i / 20)) for i in range(21)]
        pts = [(p0[0] + (p1[0] - p0[0]) * i / 20, p0[1] + (p1[1] - p0[1]) * i / 20) for i in range(21)]
        Rr = _GR(pts, ww, ww)
        cv.obj([Rr.outline()], 1.)
        cv.hair(Rr.contour(.45, 0, 1))
        cv.line(Rr.contour(-.55, 0, .95))
        cv.obj([_Gel(p1[0], p1[1], ww[-1] * 1.5, ww[-1] * 1.5, 10)[:-1]], 1.)
# ---------------------------------------------------------------------------------- eggs (scroll eyes)

def _g_disc(cv, x, y, r, ow=1.):
    p = _Gel(x, y, r, r, max(10, int(r * 4)))[:-1]
    cv.obj([p], ow)
    return p


def gm_eye_dog(cv, x, y, s, face=1):
    """Parker's dog's head curled in the eye of a scroll: muzzle, drop ear, eye, nose, fur cuts."""
    f = face

    def P(u, v):
        return (x + f * u * s, y + v * s)
    head = [P(-1, -.2), P(-.7, -.9), P(0, -1.05), P(.6, -.8), P(1.05, -.35), P(1.75, -.2), P(1.95, .15),
            P(1.75, .45), P(1.0, .6), P(.4, .95), P(-.4, 1.), P(-1, .6)]
    cv.obj([head], 1.)
    for i in range(6):
        a = -1.1 + i * .38
        cv.hair([P(-.6 + .35 * math.cos(a), .1 + .5 * math.sin(a)), P(-.95 + .6 * math.cos(a), .2 + .8 * math.sin(a))])
    ear = [P(-.35, -.75), P(.15, -.7), P(.05, .2), P(-.25, .6), P(-.55, .2)]
    cv.obj([ear], 1.)
    cv.hair(_Ghp(ear, 70 * f, 1.5))
    cv.line(_Gel(*P(.6, -.38), max(.6, s * .14), max(.6, s * .14), 8))
    nose = _Gel(*P(1.85, .02), max(.8, s * .16), max(.6, s * .12), 8)[:-1]
    cv.obj([nose], 1.)
    cv.line(_Ghp(nose, 0, 1.))
    cv.hair([P(1.75, .3), P(1.3, .38), P(1.0, .3)])


def gm_eye_pinwheel(cv, x, y, s):
    """the Blazers pinwheel cut as a boss: two interlocked sets of swept stripes."""
    _g_disc(cv, x, y, s, 1.)
    for sd in (-1, 1):
        for k in range(4):
            off = (k - 1.5) * s * .26
            p = [(x + sd * (-s * .9 + s * 1.2 * t), y + sd * (off - s * .5 * math.sin(_GPI * t) + s * .25 * t)) for t in [i / 8 for i in range(9)]]
            cv.hair(p)


def gm_eye_cymbal(cv, x, y, s):
    """a tiny ride cymbal on edge: lathe grooves, a bell, a glint."""
    p = _Gel(x, y, s * 1.2, s * .45, 20)[:-1]
    cv.obj([p], 1.)
    for k in range(1, 4):
        cv.hair(_Gel(x, y, s * 1.2 * k / 4, s * .45 * k / 4, 16, .3, _GPI - .3))
    b = _Gel(x, y - s * .2, s * .32, s * .22, 10)[:-1]
    cv.obj([b], 1.)
    cv.line([(x, y + s * .45), (x, y + s * 1.4)])


def gm_eye_note(cv, x, y, s):
    """an eighth note of swing."""
    hd = [_g_rot(p, (x, y + s * .5), -.4) for p in _Gel(x, y + s * .5, s * .5, s * .34, 12)[:-1]]
    cv.obj([hd], 1.)
    cv.line(_Ghp(hd, -20, 1.))
    cv.heavy([(x + s * .45, y + s * .4), (x + s * .45, y - s * 1.1)])
    cv.line([(x + s * .45, y - s * 1.1), (x + s * .95, y - s * .6), (x + s * .85, y - s * .1)])


def gm_eye_P(cv, x, y, s):
    """a P monogram in a beaded boss."""
    _g_disc(cv, x, y, s * 1.05, 1.)
    cv.heavy([(x - s * .25, y + s * .65), (x - s * .25, y - s * .6)])
    cv.line([(x - s * .25, y - s * .6)] + _g_arc(x + s * .05, y - s * .25, s * .35, s * .35, -90, 90, 8) + [(x - s * .25, y + s * .1)])
    cv.hair([(x - s * .5, y + s * .65), (x, y + s * .65)])


def gm_eye_heron(cv, x, y, s, face=1):
    """a heron's head rising from the curl: black crown plume, eye, dagger bill."""
    f = face

    def P(u, v):
        return (x + f * u * s, y + v * s)
    head = [P(-.8, .5), P(-.8, -.3), P(-.2, -.7), P(.5, -.55), P(.9, -.2), P(2.6, .05), P(.9, .25), P(.4, .55), P(-.2, .9)]
    cv.obj([head], 1.)
    cv.heavy([P(.4, -.55), P(-.3, -.6), P(-1.3, -.2), P(-1.9, .4)])
    cv.line(_Gel(*P(.35, -.2), max(.6, s * .13), max(.6, s * .13), 8))
    cv.hair([P(.9, 0.), P(2.5, .05)])
    cv.hair(_Ghp([P(-.7, .3), P(.3, .3), P(-.2, .85)], 60 * f, 1.5))


def gm_eye_kranok(cv, x, y, s):
    """a Thai kranok flame: a hooked flame-leaf with flicking tips."""
    for i, (a, L) in enumerate(((-1.9, 1.6), (-1.3, 2.), (-.7, 1.5))):
        gm_leaf(cv, x, y, a, L * s, s * .4, .6, -2.2 + i * .3, random.Random(i), lobes=1, turn=False)
    _g_disc(cv, x, y, s * .45, 1.)


def gm_eye_hood(cv, x, y, s):
    """Mt Hood in a boss: snow face lit, the shade flank hatched, a glacier cut."""
    _g_disc(cv, x, y, s * 1.1, 1.)
    m = [(x - s * .95, y + s * .5), (x - s * .25, y - s * .35), (x, y - s * .75), (x + s * .2, y - s * .45), (x + s * .95, y + s * .5)]
    cv.obj([m], 1.)
    cv.hair(_Ghp([(x, y - s * .75), (x + s * .05, y + s * .5), (x + s * .95, y + s * .5), (x + s * .2, y - s * .45)], 60, 1.5))


GM_EGGS = {"dog": gm_eye_dog, "pinwheel": gm_eye_pinwheel, "cymbal": gm_eye_cymbal, "note": gm_eye_note,
           "P": gm_eye_P, "heron": gm_eye_heron, "kranok": gm_eye_kranok, "hood": gm_eye_hood}


# ---------------------------------------------------------------------------------- layouts

def _g_pip(px, py, P):
    c = False
    j = len(P) - 1
    for i in range(len(P)):
        if (P[i][1] > py) != (P[j][1] > py) and px < (P[j][0] - P[i][0]) * (py - P[i][1]) / (P[j][1] - P[i][1]) + P[i][0]:
            c = not c
        j = i
    return c


def _g_bbox(P):
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    return min(xs), min(ys), max(xs), max(ys)


def _g_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def gm_scroll_region(x, y, w, h, holes, rng, sources, rmin, rmax, eggs=(), pack=True, clip=None, cap=1 << 30):
    """Grow a fine-scroll field over x,y,w,h, keeping out of the hole polygons, from stem
    sources [(root, heading, r, flip)], then pack every gap. eggs: [(name, kw)] become the eyes
    of the largest scrolls. Returns svg."""
    bbs = [(_g_bbox(P), P) for P in holes]

    def inside(px, py):
        if not (x - 4 <= px <= x + w + 4 and y - 4 <= py <= y + h + 4):
            return False
        for (bx0, by0, bx1, by1), P in bbs:
            if bx0 - 2 <= px <= bx1 + 2 and by0 - 2 <= py <= by1 + 2 and _g_pip(px, py, P):
                return False
        return True
    hd = []
    for (bx0, by0, bx1, by1), P in bbs:
        for p in P[::3]:
            hd.append(("c", p[0], p[1], 1.))
    F = GmField(x, y, w, h, rng, inside, (), rmin, rmax)
    F.holes = hd
    F.cap = cap
    for root, heading, r, flip in sources:
        F.grow(root, heading, r, flip)
    if pack:
        F.pack()
    # eggs into the eyes of mid-sized scrolls spread over the field
    if eggs:
        cands = sorted(range(len(F.units)), key=lambda i: -F.units[i][2])
        cands = [i for i in cands if F.units[i][2] < rmax * .95][:max(1, len(eggs) * 3)]
        for j, (name, kw) in enumerate(eggs):
            if j * 3 < len(cands):
                i = cands[j * 3]
                pts, cen, r, flip, sd, _ = F.units[i]
                fn = GM_EGGS[name]
                F.units[i] = (pts, cen, r, flip, sd, (lambda cv, ex, ey, s, fn=fn, kw=kw: fn(cv, ex, ey, s * 1.25, **kw)))
    cv = GmCanvas()
    cv.shadow = (1.5, 2.)
    F.paint(cv)
    cid = "gmr%x" % (zlib.crc32(repr((x, y, w, h, len(F.units))).encode()) & 0xffffff)
    return _g_clip(cid, f"M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z", cv.svg(clip or (x, y, x + w, y + h)))


def gm_scene_in(field, scene, uid):
    """the subject, clipped into its field polygon, over a white underlay."""
    d = _d(field, True, 0)
    x0, y0, x1, y1 = _g_bbox(field)
    return (f'<path d="{d}" fill="#fff"/>' + _g_clip(uid, d, scene(x0, y0, x1 - x0, y1 - y0))
            + f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>')


def _g_rect(x0, y0, x1, y1, cut=0.):
    if cut <= 0:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [(x0 + cut, y0), (x1 - cut, y0), (x1, y0 + cut), (x1, y1 - cut), (x1 - cut, y1), (x0 + cut, y1), (x0, y1 - cut), (x0, y0 + cut)]


def gm_border(w, h, cut=0.):
    """the plate's wire-inlay border: white wire, a bead row, a second wire, following the
    (optionally cut-cornered) rectangle. Returns (svg, inner_poly)."""
    poly = _g_rect(1, 1, w - 1, h - 1, cut)
    svg, depth = gm_frame_lines(poly[::-1] if C._area(poly) > 0 else poly, 0., None, .9)
    return svg, _g_rect(1 + depth, 1 + depth, w - 1 - depth, h - 1 - depth, max(0., cut - depth * .4))


def gm_corner_fleurons(w, h, inset, rng, size):
    """leafy fleurons thrown into the four corners from little bosses."""
    cv = GmCanvas()
    cv.shadow = (1., 1.5)
    for (cx, cy, a) in ((inset, inset, _GPI / 4), (w - inset, inset, 3 * _GPI / 4),
                        (w - inset, h - inset, -3 * _GPI / 4), (inset, h - inset, -_GPI / 4)):
        for sd in (-1, 1):
            gm_leaf(cv, cx, cy, a + sd * .55, size, size * .3, sd * .5, sd * 1.4, rng)
        gm_leaf(cv, cx, cy, a, size * 1.15, size * .3, .05, .4, rng, turn=False)
        _g_disc(cv, cx, cy, size * .18)
        cv.line(_Gel(cx, cy, size * .08, size * .08, 8))
    return cv.svg()


def gm_plate(w, h, ctx, P):
    """The king-tier plate. P: dict with
         scene(x, y, w, h, level) -> svg (level 0 band, 1 medium, 2 tall) drawn on white,
         shape: medallion kind; banner: text; tablet(tx, ty, tw, th) -> svg or None for the
         arms placeholder; eggs: [(name, kwargs)]; seed."""
    seed_ = P.get("seed", 0)
    rng = random.Random(seed_)
    o = [gm_defs(), gm_ground((0, 0, w, h))]
    eggs = P.get("eggs", [("dog", {})])
    shape = P.get("shape", "oval")
    form = (ctx or {}).get("form") or P.get("form", "vignette")
    aspect = {"roundel": 1., "lunette": 1.9, "archtop": 1.05}
    if w < 200 or (form == "device" and h < 110 and w < 260):
        # the marginal device (or a small tailpiece): one medallion carries the whole plate
        bead = .9 if min(w, h) < 80 else 1.2
        dep = 6.5 + 2 * bead
        b = h / 2 - dep - 2.5
        a = b if shape == "roundel" else min(w / 2 - dep - 2.5, b * P.get("band_aspect", 1.6))
        cx, cy = w / 2, h / 2
        ring, field, outer = gm_medallion(shape, cx, cy, a, b, bead)
        o.append(gm_tendrils(1, 1, w - 2, h - 2, rng, .6))
        side = (w - 2 * (a + dep)) / 2
        if side > 14:
            rr = min(12., side * .45, h * .3)
            src = [((cx - a - dep, cy + b * .2), _GPI, rr, False), ((cx + a + dep, cy + b * .2), 0., rr, True)]
            o.append(None)
            fargs = (1, 1, w - 2, h - 2, [outer], random.Random(seed_ + 1), src, max(3.5, rr * .35), rr, eggs[:1])
        o.append(ring)
        o.append(gm_scene_in(field, lambda X, Y, W, H: P["scene"](X, Y, W, H, 0), "gmc%x" % (P.get("seed", 0) & 0xfff)))
        o.append(f'<path d="M.5,.5H{_n(w - .5)}V{_n(h - .5)}H.5z" fill="none" stroke="#000" stroke-width="1"/>')
        if None not in o:
            return C.svg_doc(w, h, "".join(o))
    elif h < 46 or (h < 110 and P.get("band_banner")):
        # a gap frieze (or a lettered headpiece): a running scroll between wires, the page's
        # motif small at the centre (or a carved banner with the heading between fleurons)
        if h < 46:
            dep = 3.5 if h < 30 else 5.
            wires = (f'<path d="M0,1.25H{_n(w)}M0,{_n(dep - .75)}H{_n(w)}M0,{_n(h - 1.25)}H{_n(w)}M0,{_n(h - dep + .75)}H{_n(w)}" '
                     f'stroke="#fff" stroke-width="1" fill="none"/>')
            if h >= 30:
                bd = "".join(f"M{_n(x)},{_n(dep / 2 + .25)}h0M{_n(x)},{_n(h - dep / 2 - .25)}h0" for x in [1.5 + 3. * i for i in range(int(w / 3))])
                wires += f'<path d="{bd}" stroke="#fff" stroke-width="1" stroke-linecap="round" fill="none"/>'
            bsvg, inner = wires, _g_rect(0, dep, w, h - dep)
        else:
            bsvg, inner = gm_border(w, h)
        ix0, iy0, ix1, iy1 = _g_bbox(inner)
        cx, cy = w / 2, h / 2
        ih = iy1 - iy0
        txt = P.get("band_banner")
        if txt:
            bh = min(22., ih * .5)
            bw_ = min(w * .5, max(160., gm_text_width(txt, bh * .52) * 1.7))
            ring, centre = gm_banner(cx, cy - bh * .1, bw_, bh, .04, txt, .15)
            hole = [(cx - bw_ / 2 - 2, iy0), (cx + bw_ / 2 + 2, iy0), (cx + bw_ / 2 + 2, iy1), (cx - bw_ / 2 - 2, iy1)]
            fl = GmCanvas()
            fl.shadow = (1., 1.5)
            fs = min(ih * .5, 22.)
            for sd in (-1, 1):
                fx_ = cx + sd * (bw_ / 2 + fs * .7)
                for k in (-1, 1):
                    gm_leaf(fl, fx_, cy, (0. if sd > 0 else _GPI) + k * .75, fs * 1.1, fs * .34, k * .5, k * 1.4, rng)
                gm_leaf(fl, fx_, cy, 0. if sd > 0 else _GPI, fs * 1.35, fs * .32, .05, .4, rng, turn=False)
                if sd < 0 and eggs:
                    GM_EGGS[eggs[0][0]](fl, fx_, cy, fs * .42, **eggs[0][1])
                else:
                    _g_disc(fl, fx_, cy, fs * .2)
            holes = [hole, _g_rect(cx - bw_ / 2 - fs * 2.1, iy0, cx + bw_ / 2 + fs * 2.1, iy1)]
            scene_svg = ring + fl.svg()
            src = [((cx - bw_ / 2 - fs * 2.4, cy), _GPI, min(14., ih * .4), False), ((cx + bw_ / 2 + fs * 2.4, cy), 0., min(14., ih * .4), True)]
            eg = []
        else:
            # the page's motif small in a beaded roundel that breaks the frieze
            fr = max(5., h / 2 - 1 - (5.5 + 1.6))
            mring, field, outer = gm_medallion("roundel", cx, cy, fr, fr, .8)
            holes = [outer]
            scene_svg = mring + gm_scene_in(field, lambda X, Y, W, H: P["scene"](X, Y, W, H, 0), "gmz%x" % (seed_ & 0xfff))
            # the running rinceau: a wave stem throwing alternate curls up and down
            vine = GmCanvas()
            vine.shadow = (.8, 1.)
            rr = max(3.5, ih * .29)
            step = rr * 2.3
            amp = ih * .16
            vr = random.Random(seed_ + 5)
            for sd in (-1, 1):
                x0 = cx + sd * (fr + 7)
                # the wave stem, one round-cut ribbon from the roundel to the plate's end
                L = (w - x0) if sd > 0 else x0
                ns = max(8, int(L / 2))
                stem = [(x0 + sd * L * i / ns, cy + amp * math.sin(_GPI * (L * i / ns) / step)) for i in range(ns + 1)]
                ws = [max(.7, rr * .09)] * len(stem)
                vine.obj([_GR(stem, ws, ws).outline()], 1.)
                k = 0
                x = x0 + sd * step * .5
                while 0 < x < w:
                    up = k % 2 == 0
                    yb = cy + amp * math.sin(_GPI * abs(x - x0) / step)
                    head = (0. if sd > 0 else _GPI) + (-.7 if up else .7) * sd
                    pts, cen = gm_spine((x, yb), head, rr, 1.1, up == (sd > 0), .5, (-.4 if up else .4) * sd)
                    gm_scroll_unit(vine, pts, cen, rr, up == (sd > 0), vr, 1 if rr < 7 else 2)
                    x += sd * step
                    k += 1
            scene_svg = vine.svg() + scene_svg
            src = []
            eg = []
        o.append(gm_tendrils(ix0 + 1, iy0 + 1, ix1 - ix0 - 2, ih - 2, rng, .5))
        rr = min(12., ih * .42)
        if src:
            o.append(None)
            fargs = (ix0, iy0, ix1 - ix0, ih, holes, random.Random(seed_ + 1), src, max(3.2, rr * .32), rr, eg)
        o.append(scene_svg)
        o.append(bsvg)
        if None not in o:
            return C.svg_doc(w, h, "".join(o))
    elif h < 110:
        bsvg, inner = gm_border(w, h)
        ix0, iy0, ix1, iy1 = _g_bbox(inner)
        cx, cy = w / 2, h / 2
        b = (iy1 - iy0) / 2 - 8
        a = min(w * (.3 if w < 420 else .16), b * aspect.get(shape, P.get("band_aspect", 1.9)))
        ring, field, outer = gm_medallion(shape, cx, cy, a, b, 1.2)
        rr = min(15., (iy1 - iy0) * .3)
        src = [((cx - a - 8, cy + b * .3), _GPI, rr, False), ((cx + a + 8, cy + b * .3), 0., rr, True),
               ((cx - a - 8, cy - b * .3), _GPI, rr * .8, True), ((cx + a + 8, cy - b * .3), 0., rr * .8, False)]
        o.append(gm_tendrils(ix0 + 2, iy0 + 2, ix1 - ix0 - 4, iy1 - iy0 - 4, rng, .5))
        o.append(None)
        fargs = (ix0, iy0, ix1 - ix0, iy1 - iy0, [outer], random.Random(seed_ + 1), src, max(4., rr * .32), rr, eggs[:1])
        o.append(ring)
        o.append(gm_scene_in(field, lambda X, Y, W, H: P["scene"](X, Y, W, H, 0), "gmc%x" % (P.get("seed", 0) & 0xfff)))
        o.append(bsvg)
    elif h <= 260:
        cut = min(14., h * .08)
        bsvg, inner = gm_border(w, h, cut)
        ix0, iy0, ix1, iy1 = _g_bbox(inner)
        cx, cy = w / 2, h / 2
        b = (iy1 - iy0) / 2 - 10
        foot = P.get("arms_foot") and h > 140
        dr = min(15., b * .3)
        if foot:
            cy -= dr * .55
            b -= dr * .55
        a = min(w * (.3 if shape == "lunette" else .24), b * aspect.get(shape, P.get("med_aspect", 1.45)))
        ring, field, outer = gm_medallion(shape, cx, cy, a, b, 1.5)
        rr = min(19., h * .14)
        src = [((cx - a * .6, cy + b + 9), _GPI, rr, False), ((cx + a * .6, cy + b + 9), 0., rr, True),
               ((cx - a * .6, cy - b - 9), _GPI, rr * .9, True), ((cx + a * .6, cy - b - 9), 0., rr * .9, False)]
        o.append(gm_tendrils(ix0 + 2, iy0 + 2, ix1 - ix0 - 4, iy1 - iy0 - 4, rng, .5))
        o.append(None)
        fargs = (ix0, iy0, ix1 - ix0, iy1 - iy0, [outer], random.Random(seed_ + 1), src, 4.5, rr, eggs)
        o.append(ring)
        o.append(gm_scene_in(field, lambda X, Y, W, H: P["scene"](X, Y, W, H, 1), "gmc%x" % (P.get("seed", 0) & 0xfff)))
        if foot:
            # the small Somaster dedication cartouche at the vignette's foot
            dcy = cy + b + dr * .55
            dring, dfield, douter = gm_medallion("oval", cx, dcy, dr * 1.25, dr, .9)
            fargs[4].append(douter)
            o.append(dring)
            o.append(f'<path d="{_d(dfield, True, 0)}" fill="#fff"/>')
            o.append(_g_clip("gmf%x" % (P.get("seed", 0) & 0xfff), _d(dfield, True, 0), gm_arms(cx, dcy, dr * .95, seed_)))
        o.append(bsvg)
        o.append(gm_corner_fleurons(w, h, cut * .45 + 2, rng, cut * .9))
    else:
        cut = 18.
        bsvg, inner = gm_border(w, h, cut)
        ix0, iy0, ix1, iy1 = _g_bbox(inner)
        cx = w / 2
        # the copperplate scene: an arched panel
        aw = (ix1 - ix0) * P.get("panel", .41)
        top = iy0 + 14
        bot = iy0 + (iy1 - iy0) * (.62 + .06 * _Gsm(320, 548, h))
        a, b = aw, (bot - top) / 2
        if P.get("tall_shape") == "lunette":
            b = min(b, a * .62)
            top = bot - 2 * b
        tsh = P.get("tall_shape", "arch")
        if tsh == "roundel":
            a = min(a, b)
            b = a
        ring, field, outer = gm_medallion(tsh, cx, top + b, a, b, 1.8)
        # banner under it, then the dedication cartouche
        bh = min(21., max(15., h * .038))
        by = bot + 14 + bh / 2
        bw_ = a * 2.5
        banner, centre = gm_banner(cx, by, bw_, bh, .03, P.get("banner", ""), .2)
        dy0 = by + bh + 8
        dr = max(14., min(40., (iy1 - dy0) * .42))
        dcy = dy0 + dr + 4
        dring, dfield, douter = gm_medallion("oval", cx, dcy, dr * 1.45, dr, 1.3)
        band_poly = [(cx - bw_ / 2 - 4, by - bh * 1.2), (cx + bw_ / 2 + 4, by - bh * 1.2), (cx + bw_ / 2 + 4, by + bh * 1.5), (cx - bw_ / 2 - 4, by + bh * 1.5)]
        rr = 26. * P.get("tall_scale", 1.) * (1 + .15 * _Gsm(320, 548, h))
        src = [((cx - a * .5, bot + 9), _GPI, rr, False), ((cx + a * .5, bot + 9), 0., rr, True),
               ((cx - a - 10, top + b * .4), _GPI * .5, rr * .9, False), ((cx + a + 10, top + b * .4), _GPI * .5, rr * .9, True),
               ((cx - a * .3, top - 6), _GPI, rr * .7, True), ((cx + a * .3, top - 6), 0., rr * .7, False),
               ((cx - dr * 1.5 - 8, dcy), _GPI, rr * .8, True), ((cx + dr * 1.5 + 8, dcy), 0., rr * .8, False)]
        o.append(gm_tendrils(ix0 + 2, iy0 + 2, ix1 - ix0 - 4, iy1 - iy0 - 4, rng, .28))
        o.append(None)
        fargs = (ix0, iy0, ix1 - ix0, iy1 - iy0, [outer, douter, band_poly], random.Random(seed_ + 1), src, rr * .42, rr, eggs)
        o.append(ring)
        o.append(gm_scene_in(field, lambda X, Y, W, H: P["scene"](X, Y, W, H, 2), "gmc%x" % (P.get("seed", 0) & 0xfff)))
        o.append(dring)
        tab = P.get("tablet")
        dx0, dy0_, dx1, dy1 = _g_bbox(dfield)
        o.append(f'<path d="{_d(dfield, True, 0)}" fill="#fff"/>')
        if tab:
            o.append(_g_clip("gmd%x" % (P.get("seed", 0) & 0xfff), _d(dfield, True, 0), tab(dx0, dy0_, dx1 - dx0, dy1 - dy0_)))
        else:
            o.append(gm_arms(cx, dcy, dr, seed_))
        o.append(f'<path d="{_d(dfield, True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
        o.append(banner)
        o.append(bsvg)
        o.append(gm_corner_fleurons(w, h, cut * .45 + 2, rng, cut * .9))
    fixed = sum(len(p) for p in o if p)
    seed = P.get("seed", 0)
    cap = max(25, int((P.get("budget", 192000) - fixed - 600) / (300 + 40 * fargs[8])))
    for _ in range(3):
        fld = gm_scroll_region(*fargs, cap=cap)
        if fixed + len(fld) < 196000:
            break
        cap = int(cap * .8)
    o[o.index(None)] = fld
    return C.svg_doc(w, h, "".join(o))


def gm_arms(cx, cy, r, seed=0):
    """the dedication cartouche: Parker's arms (Somaster, from the shared solar/arms.py) on a
    field of fine engraved rays; crossed drumsticks over a sun if the module is missing."""
    cv = GmCanvas()
    for i in range(60):
        a = _GTAU * i / 60
        cv.hair([(cx + r * .45 * math.cos(a), cy + r * .45 * math.sin(a)), (cx + r * 1.7 * math.cos(a), cy + r * 1.7 * math.sin(a))])
    try:
        try:
            from solar.arms import arms as _arms
        except ImportError:
            from arms import arms as _arms
        ah = r * 1.9
        aw = ah * 120 / 140
        return cv.svg() + f'<g transform="translate({_n(cx - aw / 2)},{_n(cy - ah / 2)})">{_arms(aw, ah, seed)}</g>'
    except Exception:
        gm_sun_drums(cv, cx, cy, r * 1.25, random.Random(7))
        return cv.svg()


def gm_emblem(name, **kw):
    """a tablet for the dedication oval: the named egg carved large on a field of fine rays."""
    def tab(tx, ty, tw, th):
        cx, cy = tx + tw / 2, ty + th / 2
        r = min(tw, th) / 2
        cv = GmCanvas()
        for i in range(60):
            a = _GTAU * i / 60
            cv.hair([(cx + r * .5 * math.cos(a), cy + r * .5 * math.sin(a)), (cx + r * 1.8 * math.cos(a), cy + r * 1.8 * math.sin(a))])
        GM_EGGS[name](cv, cx, cy, r * .78, **kw)
        # the boss's ground punched with grit so no plain white is left round the device
        rb = r * .78 * 1.05 - 1.2
        grit = f'<path d="{_d(_Gel(cx, cy, rb, rb, 48), True, 0)}" fill="url(#{_GPID}g)"/>'
        return cv.svg() + grit
    return tab


# ---------------------------------------------------------------------------------- sky and water

def gm_cloud(cv, cx, cy, w, h, rng, lit=(-1, -1)):
    """a cumulus bank (modelling pass: see mk_cloud)"""
    mk_cloud(cv, cx, cy, w, h * 1.25, rng, _mk_unit(lit))


def gm_sky(cv, X, Y, W, H, rng, sun=None, clouds=3, dark=1.):
    """an engraved sky over X..X+W, Y..Y+H: long, gently undulating burin lines that swell to
    1 px in their middles and taper to hairlines, closer aloft, opening into the glow round the
    sun (sun=(x, y, r)) where rays are cut; cumulus banks modelled in curved lines float in it
    (painted after the lines, so the canvas cuts the lines away behind them)."""
    cv.obj([], 0)
    y = round((Y - 2.25) * 2) / 2 + .25
    k = 0
    while y < Y + H:
        f = (y - Y) / max(1., H)
        pitch = 2. if f < .62 else 3.
        ph = rng.uniform(0, _GTAU)
        per = rng.uniform(70, 140)
        amp = .35 + .25 * f
        pts = [(x, y + amp * math.sin(_GTAU * x / per + ph)) for x in [X - 4 + i * 3 for i in range(int((W + 8) / 3) + 1)]]
        segs = [pts]
        if sun:
            sx, sy, sr = sun
            g = sr * 3.4
            if abs(y - sy) < g:
                half = math.sqrt(g * g - (y - sy) ** 2)
                segs = [[p for p in pts if p[0] < sx - half], [p for p in pts if p[0] > sx + half]]
                if k % 2 == 0:
                    segs.append([p for p in pts if sx - half * .85 < p[0] < sx - sr * 1.25])
                    segs.append([p for p in pts if sx + sr * 1.25 < p[0] < sx + half * .85])
        for sg in segs:
            if len(sg) < 2:
                continue
            # the swell: the middle of each run at 1 px where the sky is deep
            if f < .34 * dark + .06 and len(sg) > 8:
                a = int(len(sg) * rng.uniform(.04, .2))
                b = int(len(sg) * rng.uniform(.8, .96))
                cv.hair(sg[:a + 1])
                cv.line(sg[a:b + 1])
                cv.hair(sg[b:])
            else:
                cv.hair(sg)
        y += pitch
        k += 1
    if sun:
        sx, sy, sr = sun
        nr = 40
        for i in range(nr):
            a = _GTAU * (i + .5) / nr
            r1 = sr * (3.2 if i % 2 else 2.3)
            cv.hair([(sx + sr * 1.35 * math.cos(a), sy + sr * 1.35 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
        disc = _Gel(sx, sy, sr, sr, 32)[:-1]
        cv.obj([disc], 1.)
        q = sr - 2.
        while q > 1.5:
            cv.hair(_Gel(sx + (sr - q) * .15, sy + (sr - q) * .15, q, q, max(10, int(q * 2.5))))
            q -= 2.
    for i in range(clouds):
        t = (i + rng.uniform(.2, .8)) / clouds
        cw = W * rng.uniform(.24, .4)
        ch = H * rng.uniform(.16, .24)
        cx = X + W * t
        cy = Y + H * rng.uniform(.18, .62)
        if sun and math.hypot(cx - sun[0], cy - sun[1]) < sun[2] * 2:
            cy += sun[2] * 2.5
        mk_cloud(cv, cx, cy, cw, ch, rng, _mk_unit((sun[0] - cx, sun[1] - cy)) if sun else _MKL)


def gm_water(cv, X, Y, W, H, rng, glint_x=None, refl=()):
    """water in broken, rippled lines, long and fine toward the far shore, closing up and
    darkening toward the viewer, each ripple a dash that dips and kicks; a glitter path broken
    into sparkles under glint_x; refl=[(x, half_width, y_end)] lays a dark reflection, 1 px
    dashes broken by the ripples, under each object."""
    y = round((Y + .25) * 2) / 2 + .25
    k = 0
    while y < Y + H + 2:
        f = (y - Y) / max(1., H)
        pitch = 3. if f < .2 else 2. if f < .55 else 1.5
        x = X - 6 - rng.uniform(0, 12)
        while x < X + W + 6:
            L = rng.uniform(10, 30) * (1.35 - f * .7)
            gap = rng.uniform(1.5, 3.5) * (1 + f)
            if glint_x is not None and abs(x + L / 2 - glint_x) < 5 + 18 * f:
                L *= .3
                gap += 2 + 3 * f
            n = max(2, int(L / 3))
            amp = rng.uniform(.2, .45) * (.6 + f)
            seg = [(x + L * i / n, y + amp * math.sin(_GPI * i / n)) for i in range(n + 1)]
            heavy = False
            for (rx, rh, ry) in refl:
                if y < ry and abs(x + L / 2 - rx) < rh * (1 - .3 * (y - Y) / max(1., ry - Y)) + rng.uniform(-2, 2):
                    heavy = True
            if heavy and pitch >= 2:
                cv.line(seg)
            elif f > .6 and rng.random() < (f - .6) * 1.1:
                # the near ripples: their shaded troughs cut 1 px
                m = len(seg) // 2
                cv.hair(seg[:m + 1])
                cv.line(seg[m:])
            else:
                cv.hair(seg)
            x += L + gap
        y += pitch
        k += 1


# ---------------------------------------------------------------------------------- the vignette
# (art director, batch 2: the subject is the composition; a shaped scene standing free on the page,
# its edge ruled or dissolving into white as in Bewick; ornament only from the page's own motifs;
# no black field: darks come from line work)

def vg_noise(rng, k=4):
    ph = [(rng.uniform(0, _GTAU), rng.choice((3, 5, 7, 9, 13, 17)), rng.uniform(.3, 1.)) for _ in range(k)]
    tot = sum(a for _, _, a in ph)
    return lambda t: sum(a * math.sin(f * t + p) for p, f, a in ph) / tot


def vg_dissolve(poly, rng, amp, cx, cy, bottom_only=False):
    """the scene's edge broken irregularly inward, so its lines end raggedly as in a Bewick
    tailpiece. amp px deep. bottom_only keeps the top edge clean."""
    nz = vg_noise(rng, 5)
    nz2 = vg_noise(rng, 3)
    out = []
    n = len(poly)
    for i, (x, y) in enumerate(poly):
        t = _GTAU * i / n
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.
        f = 1.
        if bottom_only:
            f = _Gsm(-.2, .5, dy / max(1., L))
        d = amp * f * (.55 + .45 * nz(t * 1.0) + .25 * nz2(t * 3.1))
        d = max(0., d)
        out.append((x - dx / L * d, y - dy / L * d))
    return out


def vg_leaf(cv, base, ang, L, W, rng, kind="lance", shade=1, dark=1.):
    """one leaf, modelled: outline, midrib, the shade half cut in fine swelling lines that follow
    the veins. kind: lance (laurel, olive), ellip (coffee, walnut), blade (reed), spiky (holly),
    needle (a fir needle tuft), round (a lotus pad seen edge on)."""
    c, s = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (base[0] + c * u * L - s * v * W, base[1] + s * u * L + c * v * W)
    n = 14
    prof = {"lance": lambda u: math.sin(math.pi * u) ** .8 * (1 - .25 * u),
            "ellip": lambda u: math.sin(math.pi * u) ** .6,
            "blade": lambda u: (1 - u) ** .7 * min(1., u * 8),
            "spiky": lambda u: math.sin(math.pi * u) ** .6,
            "round": lambda u: math.sin(math.pi * u) ** .5}.get(kind, lambda u: math.sin(math.pi * u) ** .7)
    bend = rng.uniform(-.12, .12)
    top, bot = [], []
    for i in range(n + 1):
        u = i / n
        w = prof(u) * .5
        if kind == "spiky" and 0 < i < n and i % 2 == 0:
            w *= 1.35
        if kind == "ellip" and 0 < i < n:
            w *= 1 + .05 * math.sin(i * 1.7)
        bv = bend * math.sin(math.pi * u) * 2
        top.append(P(u, bv + w))
        bot.append(P(u, bv - w))
    poly = top + bot[::-1]
    cv.obj([poly], 1.)
    mid = [P(i / n, bend * math.sin(math.pi * i / n) * 2) for i in range(n + 1)]
    cv.line(mid[:-2] if kind != "blade" else mid[:-1])
    half = (top if shade > 0 else bot)
    sh = mid + half[::-1]
    pitch = 1.5 if dark > .6 else 2.
    cv.hair(_Ghp(sh, math.degrees(ang) + 55 * shade, pitch))
    if kind in ("lance", "ellip", "spiky") and L > 9:
        other = bot if shade > 0 else top
        for i in range(2, n - 1, 3):
            cv.hair([mid[i], ((mid[i][0] + other[i + 1][0]) / 2, (mid[i][1] + other[i + 1][1]) / 2)])
    return poly


def vg_stem(cv, pts, w0, w1=None):
    w1 = w0 * .35 if w1 is None else w1
    n = len(pts)
    ws = [w0 + (w1 - w0) * i / max(1, n - 1) for i in range(n)]
    R = _GR(pts, ws, ws)
    cv.obj([R.outline()], 1.)
    if w0 > 1.4:
        cv.hair(R.contour(-.4, 0., .85))
    return R


def vg_spray(cv, pts, kind, rng, size, side=1, fruit=True, twigs=True):
    """a branch of the page's own plant along the stem pts (root first), with side twigs
    carrying their own leaves. kind: laurel, olive, holly, coffee, walnut, reed, fir, lotus,
    kelp, pine, apple, oak."""
    n = len(pts)
    if twigs and kind not in ("reed", "lotus", "kelp") and n > 4:
        tot_ = sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, n))
        nt = max(1, int(tot_ / (size * 1.3)))
        for j in range(nt):
            t = (j + .6) / (nt + .4)
            i = min(n - 2, int(t * (n - 1)))
            a = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
            sd = 1 if j % 2 else -1
            L = size * rng.uniform(.9, 1.4) * (1 - .4 * t)
            tw = _Geu(pts[i][0], pts[i][1], a + sd * .75, L, lambda u, s_=sd: -s_ * .9 / L, 10)
            vg_spray(cv, tw, kind, rng, size * .7, side, fruit and j % 2 == 0, False)
    vg_stem(cv, pts, max(.9, size * .05), .6)

    def at(t):
        i = min(n - 2, int(t * (n - 1)))
        r = t * (n - 1) - i
        p = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r)
        a = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
        return p, a
    if kind in ("laurel", "olive", "coffee", "walnut", "holly", "apple", "oak"):
        lk = {"laurel": "lance", "olive": "lance", "coffee": "ellip", "walnut": "ellip", "holly": "spiky",
              "apple": "ellip", "oak": "ellip"}[kind]
        Lf = size * {"olive": .32, "laurel": .38, "coffee": .44, "walnut": .4, "holly": .36, "apple": .36, "oak": .38}[kind]
        Wf = Lf * {"olive": .26, "laurel": .34, "coffee": .48, "walnut": .42, "holly": .55, "apple": .5, "oak": .5}[kind]
        step = .5 * Lf
        tot = sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, n))
        k = 0
        s_ = Lf * .3
        while s_ < tot - Lf * .2:
            t = s_ / tot
            p, a = at(t)
            sz = 1 - .45 * t
            for sd in ((-1, 1) if kind in ("coffee", "laurel", "olive") or k % 3 == 0 else ((-1,) if k % 2 else (1,))):
                vg_leaf(cv, p, a + sd * rng.uniform(.5, .9), Lf * sz * rng.uniform(.85, 1.1), Wf * sz, rng, lk, shade=side * sd)
            if fruit and kind == "coffee" and k % 2 == 1:
                for j in range(3):
                    _g_disc(cv, p[0] + rng.uniform(-1, 1) * Lf * .15, p[1] + rng.uniform(-1, 1) * Lf * .15, max(1.2, Lf * .1), 1.)
            if fruit and kind == "holly" and k % 3 == 1:
                for j in range(3):
                    q = (p[0] + math.cos(j * 2.1) * Lf * .12, p[1] + math.sin(j * 2.1) * Lf * .12)
                    b = _g_disc(cv, q[0], q[1], max(1.2, Lf * .1), 1.)
                    cv.line(_Ghp(b, 45, 1.5))
            if fruit and kind == "laurel" and k % 3 == 2:
                q = (p[0] + math.cos(a + 1.6 * side) * Lf * .2, p[1] + math.sin(a + 1.6 * side) * Lf * .2)
                b = _g_disc(cv, q[0], q[1], max(1.1, Lf * .09), 1.)
                cv.hair(_Ghp(b, 45, 1.5))
            s_ += step
            k += 1
        if fruit and kind in ("walnut", "apple"):
            p, a = at(.55)
            r = size * .16
            q = (p[0] + math.cos(a + 1.57 * side) * r * 1.3, p[1] + math.sin(a + 1.57 * side) * r * 1.3)
            b = _g_disc(cv, q[0], q[1], r, 1.)
            # the round modelled by crescent cuts that follow it into the shade
            for j in range(1, 5):
                rr = r * (1 - j * .18)
                cv.hair([(q[0] + rr * math.cos(t) + r * .15, q[1] + rr * math.sin(t) + r * .1) for t in [-.4 + 2.2 * u / 10 for u in range(11)]])
            cv.line([(q[0], q[1] - r), (q[0] + r * .1, q[1] - r * 1.35)])
    elif kind == "reed":
        tot_p = pts
        # blades from the root fanning up, and the cattail at the tip
        p0 = pts[0]
        a0 = math.atan2(pts[-1][1] - pts[0][1], pts[-1][0] - pts[0][0])
        for j in range(5):
            aa = a0 + (j - 2) * .22 + rng.uniform(-.08, .08)
            L = size * rng.uniform(.9, 1.5)
            bl = _Geu(p0[0], p0[1], aa, L, lambda u, sg=(j - 2): sg * .25 / L * 6 * u, 12)
            ws = [max(.4, size * .07 * (1 - i / 12) ** .7) for i in range(13)]
            R = _GR(bl, ws, ws)
            cv.obj([R.outline()], 1.)
            cv.hair(R.contour(.3, .05, .9))
        tip, a = at(1.)
        hd = [tip]
        p_, a_ = at(.8)
        ln = size * .32
        head = [(p_[0] + math.cos(a_) * ln * u - math.sin(a_) * size * .06 * math.sin(math.pi * u) ** .5 * sg,
                 p_[1] + math.sin(a_) * ln * u + math.cos(a_) * size * .06 * math.sin(math.pi * u) ** .5 * sg)
                for sg in (1, -1) for u in ([i / 10 for i in range(11)] if sg > 0 else [1 - i / 10 for i in range(11)])]
        cv.obj([head], 1.)
        cv.line(_Ghp(head, math.degrees(a_) + 90, 1.5))
    elif kind in ("fir", "pine"):
        tot = sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, n))
        s_ = 1.
        tufts = []
        nl = size * (.42 if kind == "fir" else .6)
        while s_ < tot:
            p, a = at(s_ / tot)
            f = 1 - .4 * s_ / tot
            for sd in (-1, 1):
                aa = a + sd * (.95 if kind == "fir" else .55)
                tufts.append([p, (p[0] + math.cos(aa) * nl * f, p[1] + math.sin(aa) * nl * f)])
            s_ += 2.2 if size < 20 else 1.5
        cv.line(tufts[::2])
        cv.hair(tufts[1::2])
        if fruit:
            p, a = at(.6)
            cr = size * .12
            q = (p[0] + math.cos(a + 1.57 * side) * cr * 1.8, p[1] + math.sin(a + 1.57 * side) * cr * 1.8)
            cone = _Gel(q[0], q[1], cr * .7, cr * 1.3, 18)[:-1]
            cv.obj([cone], 1.)
            for j in range(1, 6):
                yy = q[1] - cr * 1.3 + cr * 2.6 * j / 6
                cv.hair([(q[0] - cr * .7, yy - cr * .2), (q[0], yy + cr * .15), (q[0] + cr * .7, yy - cr * .2)])
    elif kind == "lotus":
        tip, a = at(1.)
        br = size * .3
        # the bud: overlapping pointed petals, each modelled
        for j, (da, sc) in enumerate(((-.5, .8), (.5, .8), (-.2, 1.), (.2, 1.), (0., 1.1))):
            vg_leaf(cv, tip, a + da, br * 2 * sc, br * 1.1 * sc, rng, "lance", shade=1 if da >= 0 else -1)
        p, a2 = at(.35)
        pad = _Gel(p[0] + math.cos(a2 + 1.57 * side) * size * .35, p[1] + math.sin(a2 + 1.57 * side) * size * .35 - size * .05,
                   size * .38, size * .12, 28)[:-1]
        cv.obj([pad], 1.)
        pc = ((pad[0][0] + pad[14][0]) / 2, (pad[0][1] + pad[14][1]) / 2)
        cv.hair([[pc, q] for q in pad[::3]])
        cv.line(_Ghp([q for q in pad if q[1] > pc[1]], 0, 1.5))
    elif kind == "kelp":
        tot = sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, n))
        for j in range(7):
            p, a = at(.1 + j * .13)
            sd = 1 if j % 2 else -1
            L = size * .7
            bl = _Geu(p[0], p[1], a + sd * .6, L, lambda u, s=sd: s * 2.5 * math.sin(u * 9) / L, 16)
            ws = [max(.5, size * .09 * math.sin(math.pi * min(1, (i + 1) / 16)) ** .6) for i in range(17)]
            R = _GR(bl, ws, ws)
            cv.obj([R.outline()], 1.)
            cv.hair(R.contour(-.4, .1, .9))
            b = _g_disc(cv, p[0], p[1], max(1., size * .06), 1.)


def vg_wreath(cv, cx, cy, r, kind, rng, span=2.3, size=None, gap=.5):
    """two branches of the page's plant rising from a knot at the foot of a roundel and curving
    up round it, tips not meeting (span radians each side)."""
    size = size or r * .3
    for sd in (-1, 1):
        pts = [(cx + r * math.cos(_GPI / 2 + sd * (gap * .5 + span * i / 30)), cy + r * math.sin(_GPI / 2 + sd * (gap * .5 + span * i / 30)))
               for i in range(31)]
        vg_spray(cv, pts, kind, rng, size, side=-sd)
    # the knot: a ribbon bow tied at the foot
    k = r * .09
    for sd in (-1, 1):
        lp = [(cx, cy + r), (cx + sd * k * 2.4, cy + r - k * 1.2), (cx + sd * k * 2.6, cy + r + k * .9)]
        vg_leaf(cv, (cx, cy + r), (0. if sd > 0 else _GPI) - sd * .35, k * 2.8, k * 1.6, rng, "ellip", shade=sd)
    _g_disc(cv, cx, cy + r, k * .7, 1.)


def vg_rays(cv, cx, cy, r0, r1, n, rng):
    """a glory: alternate long and short rays swelling out from the roundel and fading."""
    for i in range(n):
        t = _GTAU * (i + .5) / n
        rr = r1 * (1. if i % 2 else .78) * rng.uniform(.92, 1.05)
        ww = max(.6, (r0 * _GTAU / n) * (.38 if i % 2 else .26))
        p0 = (cx + r0 * math.cos(t), cy + r0 * math.sin(t))
        pts = [(cx + (r0 + (rr - r0) * u) * math.cos(t), cy + (r0 + (rr - r0) * u) * math.sin(t)) for u in [j / 10 for j in range(11)]]
        ws = [ww * (1 - j / 10) ** .8 + .25 for j in range(11)]
        R = _GR(pts, ws, ws)
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(-.3, 0., .7))


def vg_filmstrip(cv, cx, cy, r, w, rng):
    """a strip of film wound round the roundel: its band, the sprocket holes, frames between."""
    n = 72
    out = _Gel(cx, cy, r + w, r + w, n)[:-1]
    inn = _Gel(cx, cy, r, r, n)[:-1]
    cv.obj([out + [out[0]] + inn[::-1] + [inn[-1]]], 1.)
    cv.line(_Gel(cx, cy, r + w * .78, r + w * .78, n))
    cv.line(_Gel(cx, cy, r + w * .22, r + w * .22, n))
    nh = int(_GTAU * (r + w * .5) / max(3., w * .55))
    for i in range(nh):
        t = _GTAU * i / nh
        for rr in (r + w * .11, r + w * .89):
            q = (cx + rr * math.cos(t), cy + rr * math.sin(t))
            cv.obj([[(q[0] + w * .07 * math.cos(t + a), q[1] + w * .07 * math.sin(t + a)) for a in (0., 1.57, 3.14, 4.71)]], .5)
        if i % 4 == 0:
            cv.hair([(cx + (r + w * .22) * math.cos(t), cy + (r + w * .22) * math.sin(t)),
                     (cx + (r + w * .78) * math.cos(t), cy + (r + w * .78) * math.sin(t))])
    cv.hair(_Ghp(out[n // 8: n * 5 // 8] + inn[n // 8: n * 5 // 8][::-1], 30, 2.))


def vg_rule(poly, double=True, beads=0.):
    """a fine engraved rule round the shape: a 1 px line, a hair 2.5 px inside, beads between."""
    o = [f'<path d="{_d(poly, True, .1)}" fill="none" stroke="#000" stroke-width="1"/>']
    if double:
        o.append(f'<path d="{_d(gm_offset(poly, -2.5), True, .1)}" fill="none" stroke="#000" stroke-width=".5"/>')
        o.append(f'<path d="{_d(gm_offset(poly, 3.), True, .1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    if beads:
        bp = _g_resample(gm_offset(poly, 3. + beads + 1.5), beads * 2 + 1.4)
        o.append(f'<path d="{"".join(f"M{_n(p[0])},{_n(p[1])}h0" for p, _ in bp)}" fill="none" stroke="#000" stroke-width="{_n(beads * 2)}" stroke-linecap="round"/>')
        o.append(f'<path d="{"".join(f"M{_n(p[0] - beads * .3)},{_n(p[1] - beads * .3)}h0" for p, _ in bp)}" fill="none" stroke="#fff" stroke-width="1" stroke-linecap="round"/>')
        o.append(f'<path d="{_d(gm_offset(poly, 3. + 2 * beads + 3), True, .1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def vg_tooled_border(w, h, rng, depth=14.):
    """the binding's tooled border, cut light: two fillets, a run of small tooled fleurons and
    dots between them, corner fleurons. For the cover only."""
    cv = GmCanvas()
    o = []
    for d, sw in ((1., 1.5), (3.5, .5), (depth - 1.5, .5), (depth + 1., 1.)):
        o.append(f'<path d="M{_n(d)},{_n(d)}H{_n(w - d)}V{_n(h - d)}H{_n(d)}z" fill="none" stroke="#000" stroke-width="{sw}"/>')
    m = (depth + 3.5) / 2 + .5
    s = (depth - 6) * .5
    for (x0, y0, x1, y1) in ((m, m, w - m, m), (w - m, m, w - m, h - m), (w - m, h - m, m, h - m), (m, h - m, m, m)):
        L = math.hypot(x1 - x0, y1 - y0)
        ang = math.atan2(y1 - y0, x1 - x0)
        k = int(L / (s * 3.2))
        for i in range(1, k):
            t = i / k
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if i % 2:
                vg_leaf(cv, (px - math.cos(ang) * s * .9, py - math.sin(ang) * s * .9), ang, s * 1.8, s * .9, rng, "lance", 1, .5)
            else:
                _g_disc(cv, px, py, max(1., s * .3), .5)
    for (x, y) in ((m, m), (w - m, m), (w - m, h - m), (m, h - m)):
        for j in range(4):
            vg_leaf(cv, (x, y), _GPI / 4 + j * _GPI / 2, s * 2.2, s * 1., rng, "lance", 1, .5)
        _g_disc(cv, x, y, s * .4, 1.)
    return "".join(o) + cv.svg()


def vg_plate(w, h, ctx, V):
    """The batch-2 plate: one shaped engraved scene that carries the page, standing free on the
    white page. V: scene(x, y, w, h, level) -> svg; shape (oval roundel archtop lunette cut
    irregular); edge ("rule", "beads", "dissolve", "dissolve_foot"); frame: (kind, plant) with
    kind in wreath/rays/film/sprays/none; banner text; arms (bool); seed; aspect."""
    seed_ = V.get("seed", 0)
    rng = random.Random(seed_)
    o = [gm_defs()]
    form = (ctx or {}).get("form") or V.get("form", "vignette")
    shape = V.get("shape", "oval")
    edge = V.get("edge", "rule")
    fk, plant = V.get("frame", ("sprays", "laurel"))
    level = 0 if h < 110 or w < 200 else (1 if h <= 260 else 2)
    cx = w / 2
    pad = 3.
    if h < 46 and w > 3 * h:
        # the gap frieze: two fine rules, the page's plant running out both ways from a small
        # beaded roundel that holds the scene
        rr = h / 2 - 5.
        cy = h / 2
        o.append(f'<path d="M0,1H{_n(w)}M0,3H{_n(w)}M0,{_n(h - 1)}H{_n(w)}M0,{_n(h - 3)}H{_n(w)}" stroke="#000" stroke-width=".5" fill="none"/>')
        fr = GmCanvas()
        for sd in (-1, 1):
            x0 = cx + sd * (rr + 7)
            L = (w - 4 - x0) if sd > 0 else (x0 - 4)
            n = max(10, int(L / 3))
            pts = [(x0 + sd * L * i / n, cy + h * .12 * math.sin(L * i / n / (h * .9))) for i in range(n + 1)]
            vg_spray(fr, pts, plant, rng, min(h * .42, 14.), side=sd)
        field = gm_shape("roundel", cx, cy, rr, rr)
        o.append(fr.svg())
        o.append(f'<path d="{_d(field, True, 0)}" fill="#fff"/>')
        o.append(gm_scene_in(field, lambda X, Y, W, H: V["scene"](X, Y, W, H, 0), "vgf%x" % (seed_ & 0xfff)))
        o.append(vg_rule(field, True, .7))
        return C.svg_doc(w, h, "".join(o))
    banner = V.get("banner") if (level >= 1 and h >= 150) else None
    arms = V.get("arms") and level >= 1 and h >= 150
    foot = 0.
    if banner:
        foot += min(22., h * .09) + 4
    if arms and not banner:
        foot += min(30., h * .14)
    elif arms:
        foot += min(30., h * .1)
    # the frame's room round the scene
    if w < 120 or (level == 0 and shape == "roundel" and w < 3 * h):
        fk = "none"          # at device size: one bold motif, no wreath
    ring = {"wreath": .24, "rays": .24, "film": .16, "sprays": .0, "none": 0.}.get(fk, 0.)
    if form == "frontispiece" and level == 2:
        bd = 16.
        o.append(vg_tooled_border(w, h, rng, bd))
        top, bot = bd + 10, h - bd - 8 - foot
        lx0, lx1 = bd + 10, w - bd - 10
    else:
        top, bot = pad, h - pad - foot
        lx0, lx1 = pad, w - pad
    avail_h = bot - top
    if shape == "roundel":
        R = min(avail_h, lx1 - lx0) / 2 / (1 + ring)
        a = b = R
    else:
        asp = V.get("aspect", {"oval": 2.3, "archtop": 2., "lunette": 2.3, "cut": 2.1, "irregular": 2.3}.get(shape, 2.))
        if level == 0:
            asp = V.get("band_aspect", asp * 1.6)
        b = avail_h / 2 / (1 + ring)
        sz0 = min(b * .75, 46.) if level else min(b * .9, 16.)
        room = (lx1 - lx0) / 2 / (1 + ring * .6) - (sz0 * 1.05 if fk == "sprays" else 2)
        a = min(room, b * max(asp, 3.4 if V.get("fill", True) else asp))
    cy = top + avail_h / 2
    sz = min(b * .75, 46.) if level else min(b * .9, 16.)
    kind = {"irregular": "oval", "cut": "cut"}.get(shape, shape)
    if kind == "cut":
        cc = min(a, b) * .28
        field = [(cx - a + cc, cy - b), (cx + a - cc, cy - b), (cx + a, cy - b + cc), (cx + a, cy + b - cc),
                 (cx + a - cc, cy + b), (cx - a + cc, cy + b), (cx - a, cy + b - cc), (cx - a, cy - b + cc)]
        field = [p for p, _ in _g_resample(field, (a + b) * 4 / 120)]
    else:
        field = gm_shape(kind, cx, cy, a, b)
    # the frame behind / round the scene
    fr = GmCanvas()
    if fk == "wreath":
        vg_wreath(fr, cx, cy, max(a, b) * (1 + ring * .5), plant, rng, 2.4, max(a, b) * .42)
    elif fk == "rays":
        vg_rays(fr, cx, cy, max(a, b) + 2, max(a, b) * (1 + ring), 48 if level else 32, rng)
    elif fk == "film":
        vg_filmstrip(fr, cx, cy, max(a, b) + 1.5, max(a, b) * ring * .8, rng)
    elif fk == "sprays":
        # branches rising from the scene's foot and sweeping up its flanks
        for sd in (-1, 1):
            n = 30
            pts = []
            for i in range(n + 1):
                t = i / n
                ang = _GPI / 2 + sd * (.3 + (1.15 if plant == "lotus" else 1.6) * t)
                rr = 1.02 + .05 * math.sin(math.pi * t)
                pts.append((cx + (a * rr + sz * .25) * math.cos(ang), cy + (b * rr + sz * .1) * math.sin(ang)))
            vg_spray(fr, pts, plant, rng, sz, side=-sd)
    side_plant = V.get("side_plant")
    if shape == "roundel" and side_plant and (lx1 - lx0) > 2.6 * a * (1 + ring):
        r_out = a * (1 + ring * .8)
        for sd in (-1, 1):
            x0 = cx + sd * r_out
            L = (lx1 - x0) if sd > 0 else (x0 - lx0)
            n = 30
            for k_, (dy, amp, ln) in enumerate(((0., .16, 1.), (-.35, .1, .62), (.38, .1, .55))):
                pts = [(x0 + sd * L * ln * i / n, cy + b * dy * (i / n) ** .7 + b * amp * math.sin(i / n * 3.6 + k_))
                       for i in range(n + 1)]
                vg_spray(fr, pts, side_plant, rng, min(b * (.5 if k_ == 0 else .38), 34.), side=sd)
    frame_svg = fr.svg()
    # the scene, its edge ruled or broken
    if edge.startswith("dissolve"):
        clip = vg_dissolve(field, random.Random(seed_ + 3), max(3., min(a, b) * .12), cx, cy, edge == "dissolve_foot")
    else:
        clip = field
    bx0, by0, bx1, by1 = _g_bbox(field)
    _cd = _d(clip, True, 0)
    sc = _g_clip("vgc%x" % (seed_ & 0xfff), _cd, V["scene"](bx0, by0, bx1 - bx0, by1 - by0, level))
    o.append(frame_svg)
    # the cut is white under the scene; outside it the plate stays transparent so the frame
    # designer's engraved ground shows through (Parker: no white unless behind text)
    o.append(f'<path d="{_cd}" fill="#fff"/>')
    o.append(sc)
    if edge == "rule":
        o.append(vg_rule(field, True, 0.))
    elif edge == "beads":
        o.append(vg_rule(field, True, 1.1 if level else .8))
    elif edge == "dissolve_foot":
        o.append(f'<path d="{_d(field[: len(field) // 2 + 1][::-1], tol=.1)}" fill="none" stroke="none"/>')
    # caption ribbon and the arms
    yb = cy + b * (1 + ring * .6) + 4
    if banner:
        bh = min(20., h * .08)
        bsvg, _ = gm_banner(cx, yb + bh * .6, min(w * .7, max(a * 2.2, 200.)), bh, .03, banner, .15)
        o.append(bsvg)
        yb += bh * 1.4
    if arms:
        ar = min(14., (h - yb) * .4)
        if ar > 7:
            acy = min(h - ar - 3, yb + ar + 1)
            o.append(gm_arms_light(cx, acy, ar, seed_))
    return C.svg_doc(w, h, "".join(o))


def gm_arms_light(cx, cy, r, seed=0):
    """the Somaster arms in a small oval cartouche, on white: fine rule and a ring of hair rays."""
    cv = GmCanvas()
    ov = _Gel(cx, cy, r * 1.3, r * 1.08, 40)[:-1]
    for i in range(40):
        t = _GTAU * i / 40
        cv.hair([(cx + r * 1.36 * math.cos(t), cy + r * 1.14 * math.sin(t)), (cx + r * 1.62 * math.cos(t), cy + r * 1.38 * math.sin(t))])
    s = cv.svg() + vg_rule(ov, False)
    try:
        try:
            from solar.arms import arms as _arms
        except ImportError:
            from arms import arms as _arms
        ah = r * 1.9
        aw = ah * 120 / 140
        s += f'<g transform="translate({_n(cx - aw / 2)},{_n(cy - ah / 2)})">{_arms(aw, ah, seed)}</g>'
    except Exception:
        pass
    return s
# ---------------------------------------------------------------------------------- modelling kit
# (batch-1 modelling pass: light from dark. Every round form is cut in crescents of line that
# follow it, closest and heaviest at the shadow edge, opening to bare paper where the light
# strikes; foliage in flicked masses; water broken by ripples; a rich near ground.)

_MKL = (-.6, -.8)       # the light: from the upper left


def _mk_bez(p0, p1, p2, p3, n=10):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _mk_runs(pts, pred):
    """split a closed point ring into contiguous runs by pred, joining the wrap-around"""
    runs = []
    for q in pts:
        v = pred(q)
        if runs and runs[-1][1] == v:
            runs[-1][0].append(q)
        else:
            runs.append(([q], v))
    if len(runs) > 1 and runs[0][1] == runs[-1][1]:
        runs[0] = (runs[-1][0] + runs[0][0], runs[0][1])
        runs.pop()
    return runs


def _mk_unit(v):
    l = math.hypot(v[0], v[1]) or 1.
    return (v[0] / l, v[1] / l)


def mk_blob(cx, cy, rx, ry, rng=None, lobes=0, amp=.0, n=40, rot=0.):
    """an ellipse, optionally scalloped into `lobes` leafy bumps (amp of the radius)"""
    out = []
    ph = rng.uniform(0, _GTAU) if rng else 0.
    for i in range(n):
        t = _GTAU * i / n
        k = 1.
        if lobes:
            k = 1 - amp + amp * abs(math.sin(lobes * t / 2 + ph)) ** .55
            if rng:
                k *= 1 + rng.uniform(-amp, amp) * .25
        x, y = rx * k * math.cos(t), ry * k * math.sin(t)
        if rot:
            x, y = x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot)
        out.append((cx + x, cy + y))
    return out


def _mk_inside(px, py, cx, cy, rx, ry):
    return ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2


def mk_crescent(cv, cx, cy, rx, ry, light=_MKL, depth=.7, pitch=2., heavy=.3, trim=.1, flick=None,
                rng=None, ycut=None, hair_pitch=None, deep=0., rot=0.):
    """Form shading for a round: copies of the outline slid toward the light; the part of each
    inside the round is one crescent line on the shade side. They lie closest at the shadow edge
    (1 px there, to `heavy` of the depth), thin to hairlines and stop at `depth` of the diameter,
    so the lit side is bare paper. flick=(dash, gap) breaks them into flicked leaf texture.
    deep>0 crosses the darkest band with a second set of short strokes."""
    if rot:
        # work in the round's own frame, then turn the lines back
        cr, sr_ = math.cos(rot), math.sin(rot)
        L = _mk_unit(light)
        sub = GmCanvas()
        sub.obj([], 0)
        mk_crescent(sub, 0., 0., rx, ry, (L[0] * cr + L[1] * sr_, -L[0] * sr_ + L[1] * cr), depth, pitch, heavy, trim,
                    flick, rng, None, hair_pitch, deep, 0.)
        for w, lines in sub.objs[-1][2].items():
            if w == "w":
                continue
            for pl in lines:
                cv._add(w, [(cx + x * cr - y * sr_, cy + x * sr_ + y * cr) for x, y in pl])
        return
    lx, ly = _mk_unit(light)
    D = 2 * min(rx, ry) * depth
    d = pitch * .75
    k = 0
    hp = hair_pitch or pitch * .75
    while d < D:
        f = d / D
        n = max(16, int((rx + ry) * 1.2))
        ox, oy = cx + lx * d * (rx / max(rx, ry)), cy + ly * d * (ry / max(rx, ry))
        pts = []
        for i in range(n + 1):
            t = _GTAU * i / n
            p = (ox + rx * math.cos(t), oy + ry * math.sin(t))
            pts.append((p, _mk_inside(p[0], p[1], cx, cy, rx, ry) < .985))
        # rotate so the run of inside points is contiguous
        st = next((i for i in range(n + 1) if not pts[i][1]), None)
        if st is None:
            break
        seq = pts[st:] + pts[:st]
        arc = [p for p, ins in seq if ins]
        if len(arc) > 3:
            m = int(len(arc) * (trim + f * .18))
            arc = arc[m: len(arc) - m] if len(arc) - 2 * m > 2 else []
        if ycut is not None:
            arc = [p for p in arc if p[1] < ycut]
        if len(arc) > 1:
            w = cv.line if f < heavy else cv.hair
            if flick and rng:
                dash, gap = flick
                i = 0
                while i < len(arc) - 1:
                    L = max(2, int(rng.uniform(dash * .6, dash * 1.3)))
                    seg = arc[i: i + L]
                    if len(seg) > 1:
                        a, b = seg[0], seg[-1]
                        # a flick: the stroke kicks out a little at its tail
                        seg = seg + [(b[0] + (b[0] - a[0]) * .25 - lx * .8, b[1] + (b[1] - a[1]) * .25 - ly * .8)]
                        w(seg)
                    i += L + max(1, int(rng.uniform(gap * .5, gap * 1.4) * (1 + f)))
            else:
                w(arc)
            if deep and f < deep and k % 2 == 0:
                # cross strokes, short, across the darkest band
                for j in range(2, len(arc) - 2, 3):
                    p = arc[j]
                    cv.hair([(p[0] - ly * 1.6, p[1] + lx * 1.6), (p[0] + ly * 1.6, p[1] - lx * 1.6)])
        d += pitch if f < heavy else hp
        k += 1


def mk_rim(cv, cx, cy, rx, ry, light=_MKL, a=.55, heavy=True):
    """the outline's shadow side only, swelling to 1.5 px at the darkest point"""
    lx, ly = _mk_unit(light)
    ang = math.atan2(-ly, -lx)
    pts = [(cx + rx * math.cos(ang + t), cy + ry * math.sin(ang + t)) for t in [(-a + 2 * a * i / 16) * _GPI for i in range(17)]]
    cv.line(pts)
    if heavy:
        cv.heavy(pts[5:12])


def mk_cloud(cv, cx, cy, w, h, rng, light=_MKL, dark=1.):
    """a cumulus bank modelled light from dark: billows lit on top, each turned in crescents of
    line to a dark, flat, ruled underside; the tops left as clean paper with a broken rim."""
    h = min(h, 30.)
    nb = max(3, min(7, int(w / max(7., h * .9))))
    bills = []
    for k in range(nb):
        t = (k + rng.uniform(.3, .7)) / nb
        r = h * (.3 + .5 * math.sin(_GPI * t) ** 1.3) * rng.uniform(.85, 1.1)
        bills.append((cx - w / 2 + w * t, cy - r * .3, r))
    nu = max(2, nb // 2 + 1)
    for k in range(nu):
        t = .22 + .56 * (k + rng.uniform(.3, .7)) / nu
        r = h * (.42 + .3 * math.sin(_GPI * t)) * rng.uniform(.85, 1.1)
        bills.append((cx - w / 2 + w * t, cy - h * .42 - r * .25, r))
    for k in range(1 if w < 4 * h else 2):
        t = rng.uniform(.38, .62) if w < 4 * h else (.36 + .28 * k)
        r = h * rng.uniform(.42, .55)
        bills.append((cx - w / 2 + w * t, cy - h * .82, r))
    nb = len(bills) - nu - (1 if w < 4 * h else 2)
    base = cy + h * .32
    order = bills[nb + nu:] + bills[nb:nb + nu] + sorted(bills[:nb], key=lambda b: -abs(b[0] - cx))
    for bx, by, r in order:
        p = [(q[0], min(q[1], base)) for q in mk_blob(bx, by, r, r * .86, rng, int(r / 3) + 3, .06, 36)]
        cv.obj([p], 0)
        rim = [q for q in _Gel(bx, by, r, r * .86, 28) if q[1] < base - .3]
        # the rim: a hairline on the lit top, broken, heavier into the shade
        lx, ly = _mk_unit(light)
        for run, lit in _mk_runs(rim, lambda q: ((q[0] - bx) * lx + (q[1] - by) * ly) > r * .2):
            if lit:
                for i in range(0, len(run) - 2, 5):
                    cv.hair(run[i: i + 3])
            elif len(run) > 1:
                cv.line(run)
        mk_crescent(cv, bx, by, r, r * .86, light, .52 * dark, 2., .2, .14, ycut=base - .5, hair_pitch=2.)
    # the shadowed underside: flat, ruled dark, fading at the ends
    y = base - h * .22
    k = 0
    while y < base + .6:
        f = (y - base + h * .22) / (h * .22 + .6)
        hw = w * (.38 + .1 * f)
        (cv.line if k % 2 == 0 and f > .3 else cv.hair)([(cx - hw, y), (cx - hw * .3, y + .2), (cx + hw * .3, y - .2), (cx + hw, y)])
        y += 1.5
        k += 1


def mk_foliage(cv, cx, cy, w, h, rng, light=_MKL, n=None, dark=1., outline=.5, deep=True, leaf=None):
    """a mass of leafage in the engraver's leaf-touch: rows of small cupped leaf strokes laid over
    the crown, each clump of the crown turned light to dark, so the touches thin to broken
    hairlines where the light strikes the bosses and swell to 1 and 1.5 px, close-set, in the
    shade, in the hollows between clumps and under the mass; a leafy broken edge."""
    n = n or max(4, int(w * h / 220) + 3)
    n = min(n, 14)
    clumps = []
    for i in range(n):
        a = _GTAU * (i + rng.uniform(.1, .9)) / n
        rr = math.sqrt((i % 3 + rng.uniform(.2, 1.)) / 3)
        x = cx + math.cos(a) * rr * w * .3
        y = cy + math.sin(a) * rr * h * .28
        r = min(w, h) * rng.uniform(.2, .3)
        clumps.append((x, y, r * rng.uniform(1., 1.2), r * rng.uniform(.8, .92)))
    clumps.sort(key=lambda c: c[1] - c[0] * .15)
    lx, ly = _mk_unit(light)
    polys = []
    for x, y, rx, ry in clumps:
        nl = max(6, int((rx + ry) / 2.4))
        polys.append(mk_blob(x, y, rx, ry, rng, nl, .15, nl * 4))
    cv.obj(polys, 0)
    x0 = min(p[0] for q in polys for p in q)
    x1 = max(p[0] for q in polys for p in q)
    y0 = min(p[1] for q in polys for p in q)
    y1 = max(p[1] for q in polys for p in q)
    sx = leaf or (3.2 if w > 30 else 2.6)
    sy = sx * .72
    row = 0
    y = y0 + sy * .5
    while y < y1:
        x = x0 + (sx * .5 if row % 2 else 0) + rng.uniform(-.4, .4)
        while x < x1:
            # the front-most clump holding this touch decides its tone
            top = -1
            for i in range(len(clumps) - 1, -1, -1):
                X_, Y_, rx, ry = clumps[i]
                if _mk_inside(x, y, X_, Y_, rx * .97, ry * .97) < 1:
                    top = i
                    break
            if top >= 0:
                X_, Y_, rx, ry = clumps[top]
                u = ((x - X_) * -lx / rx + (y - Y_) * -ly / ry)        # -1 lit .. +1 shade
                t = .5 + .45 * u
                # the hollow under a clump that lies in front
                for j in range(top + 1, len(clumps)):
                    Xj, Yj, rj, sj = clumps[j]
                    if _mk_inside(x + lx * 2.5, y + ly * 2.5, Xj, Yj, rj, sj) < 1:
                        t += .2
                        break
                t += .3 * (y - y0) / max(1., y1 - y0) - .02
                t *= dark
                t += rng.uniform(-.08, .08)
                if t > .22:
                    c = sx * (.3 if t < .66 else .36)
                    d = sy * (.5 if t < .55 else .7)
                    cup = [(x - c, y - d * .6), (x, y + d * .35), (x + c, y - d * .6)]
                    if t < .42:
                        if rng.random() < .55:
                            cv.hair(cup[1:] if rng.random() < .5 else cup[:2])
                    elif t < .66:
                        cv.hair(cup)
                    elif t < .86:
                        cv.line(cup)
                    else:
                        cv.heavy([(x - c * 1.1, y - d * .2), (x + c * 1.1, y + d * .2)])
            x += sx
        y += sy
        row += 1
    # the leafy edge: broken on the lit side, firm in the shade
    for i, q in enumerate(polys):
        cxq = sum(p[0] for p in q) / len(q)
        cyq = sum(p[1] for p in q) / len(q)
        later = clumps[i + 1:]

        def kind(p):
            if any(_mk_inside(p[0], p[1], X_, Y_, rx, ry) < 1 for X_, Y_, rx, ry in later):
                return 2
            return 1 if ((p[0] - cxq) * lx + (p[1] - cyq) * ly) > 0 else 0
        for run, k in _mk_runs(q, kind):
            if k == 1:
                for j in range(0, len(run) - 2, 4):
                    cv.hair(run[j: j + 3])
            elif k == 0 and len(run) > 1:
                cv.line(run)


def mk_trunk(cv, x, yb, yt, wb, wt, rng, light=_MKL, lean=0.):
    """a tapering trunk with bark cut in long lines along it, black on the shade side"""
    L = [(x - wb / 2, yb), (x - wt / 2 + lean, yt), (x + wt / 2 + lean, yt), (x + wb / 2, yb)]
    cv.obj([L], 1.)
    n = 7
    for k in range(1, n):
        s = k / n
        pts = []
        for i in range(9):
            t = i / 8
            xx = (x - wb / 2 + wb * s) * (1 - t) + (x - wt / 2 + lean + wt * s) * t
            pts.append((xx + rng.uniform(-.3, .3), yb + (yt - yb) * t))
        (cv.line if s > .62 else cv.hair)(pts if s > .3 else pts[::2])


def mk_tree(cv, x, yb, hh, rng, kind="oak", light=_MKL, wd=None, dark=1.):
    """a modelled tree, base at (x, yb), hh tall: oak/round crowns in flicked clumps on a barked
    trunk; fir in drooping tiers each dark beneath."""
    wd = wd or hh * (.75 if kind == "oak" else .38)
    if kind == "fir":
        cv.obj([], 0)
        cv.line([(x, yb), (x, yb - hh)])
        tiers = max(4, int(hh / 5))
        for i in range(tiers):
            t = (i + 1) / tiers
            yy = yb - hh + hh * t * .92
            half = wd / 2 * (.18 + .82 * t) * rng.uniform(.85, 1.1)
            top = yb - hh + hh * (t - 1.25 / tiers) * .92
            P = [(x, top), (x + half * .55, yy - (yy - top) * .35), (x + half, yy + 1.2)]
            # a ragged bough hem
            m = max(3, int(half / 2))
            for j in range(m + 1):
                u = 1 - j / m
                P.append((x + half * (2 * u - 1) * (1 if True else 1), yy + (1.6 if j % 2 else 0) + rng.uniform(-.3, .3)))
            P += [(x - half * .55, yy - (yy - top) * .35)]
            cv.obj([P], .5)
            # needles: strokes falling out from the stem, close and heavy on the shade side and
            # under the hem
            q = max(5, int(half / 1.3))
            for j in range(q + 1):
                u = j / q
                sx = x + half * (2 * u - 1) * .95
                if abs(sx - x) < .6:
                    continue
                sy = yy + 1.2 - abs(2 * u - 1) * .3
                ty = top + (yy - top) * .25 + (yy - top) * .5 * abs(2 * u - 1)
                tx = x + (sx - x) * .2
                (cv.line if u > .55 else cv.hair)([(tx, ty), (sx, sy)])
            cv.line([(x - half * .8, yy + 1), (x + half, yy + 1.4)])
        return
    trunk_h = hh * .42
    mk_trunk(cv, x, yb, yb - trunk_h, wd * .1, wd * .06, rng, light)
    # limbs into the crown
    cv.obj([], 0)
    for sd in (-1, 1):
        cv.line([(x, yb - trunk_h * .8), (x + sd * wd * .18, yb - trunk_h * 1.25), (x + sd * wd * .26, yb - trunk_h * 1.45)])
    mk_foliage(cv, x, yb - hh + (hh - trunk_h) * .52, wd, (hh - trunk_h) * 1.05, rng, light, dark=dark)


def mk_stone(cv, cx, cy, rx, ry, rng, light=_MKL, shadow=True):
    """a modelled stone with its cast shadow on the ground"""
    if shadow:
        sh = mk_blob(cx + rx * .35, cy + ry * .55, rx * 1.15, ry * .45, None, 0, 0, 24)
        cv.obj([sh], 0)
        y = cy + ry * .2
        while y < cy + ry * 1.05:
            cv.line([(cx - rx * .4, y), (cx + rx * 1.4, y)])
            y += 2.
    poly = mk_blob(cx, cy, rx, ry, rng, 4, .12, 28)
    cv.obj([poly], 1.)
    mk_crescent(cv, cx, cy, rx, ry, light, .75, 2., .45, .05, hair_pitch=1.5, deep=.3)
    # a crack or two
    if rx > 4:
        a = (cx - rx * .2, cy - ry * .6)
        cv.hair([a, (a[0] + rx * .2, a[1] + ry * .5), (a[0] + rx * .1, a[1] + ry * .9)])


def mk_tuft(cv, x, yb, hh, rng, n=None, spread=.6, light_blades=True):
    """a tuft of grass: dark swept blades, a few lit blades over them, a dark root"""
    n = n or rng.randint(5, 9)
    cv.obj([], 0)
    for i in range(n):
        t = (i + .5) / n - .5
        L = hh * rng.uniform(.55, 1.)
        ang = -_GPI / 2 + t * spread * 2 + rng.uniform(-.15, .15)
        bend = rng.uniform(.15, .45) * (1 if t > 0 else -1)
        bx = x + t * hh * .25
        p0 = (bx, yb)
        p1 = (bx + math.cos(ang) * L * .45, yb + math.sin(ang) * L * .45)
        p2 = (bx + math.cos(ang + bend) * L, yb + math.sin(ang + bend) * L)
        pts = _mk_bez(p0, p1, ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2), p2, 7)
        if L > 6:
            cv.line(pts[:5])
            cv.hair(pts[4:])
        else:
            cv.hair(pts)
    if light_blades and hh > 8:
        for i in range(2):
            L = hh * rng.uniform(.6, .9)
            sd = rng.choice((-1, 1))
            bx = x + rng.uniform(-2, 2)
            tip = (bx + sd * L * .4, yb - L)
            bl = [(bx - 1., yb), (bx + sd * L * .15 - .6, yb - L * .55), tip, (bx + sd * L * .15 + 1., yb - L * .5), (bx + 1., yb)]
            cv.obj([bl], .5)
            cv.hair([(bx + sd * .2, yb - 1), (bx + sd * L * .18, yb - L * .5)])
    # the root shadow
    cv.obj([], 0)
    for k in range(3):
        y = yb - k * 1.5
        cv.line([(x - hh * .2 + k, y), (x + hh * .2 - k, y)])


def mk_ground(cv, X, y0, W, y1, rng, light=_MKL, stones=2, tufts=6, pebbles=True, top=None):
    """a near bank: earth worked in short broken strokes that close up and darken toward the
    viewer, with modelled stones, pebbles and grass tufts. top(x) gives the bank's crest."""
    if top is None:
        ph = rng.uniform(0, 9)

        def top(x):
            return y0 + 2.5 * math.sin((x - X) / 37. + ph) + 1.5 * math.sin((x - X) / 13. + ph * 2)
    xs = [X - 6 + (W + 12) * i / 60 for i in range(61)]
    poly = [(x, top(x)) for x in xs] + [(X + W + 6, y1 + 6), (X - 6, y1 + 6)]
    cv.obj([poly], 0)
    cv.line([(x, top(x)) for x in xs])
    H = y1 - y0
    k = 0
    y = 1.5
    while y < H + 6:
        f = min(1., y / max(1., H))
        x = X - 6 + rng.uniform(0, 8)
        while x < X + W + 6:
            L = rng.uniform(4, 13) * (1.2 - f * .5)
            yy = top(x) + y
            seg = [(x, yy), (x + L * .5, yy + rng.uniform(-.4, .4)), (x + L, yy + rng.uniform(-.3, .5))]
            (cv.line if f > .3 and rng.random() < .25 + f * .7 else cv.hair)(seg)
            x += L + rng.uniform(1.5, 4.) * (1.3 - f * .6)
        y += 3. if f < .15 else 2.
        k += 1
    if pebbles:
        for i in range(int(W / 14)):
            px = X + rng.uniform(0, W)
            py = top(px) + rng.uniform(.3, .9) * H
            r = rng.uniform(.9, 1.8)
            cv.obj([mk_blob(px, py, r * 1.3, r, None, 0, 0, 10)], .5)
            cv.line([(px - r * .4, py + r * .9), (px + r * 1.3, py + r * .6)])
    for i in range(stones):
        sx = X + W * (i + rng.uniform(.2, .8)) / max(1, stones)
        r = min(H * .35, rng.uniform(4, 8))
        mk_stone(cv, sx, top(sx) + H * rng.uniform(.35, .6), r * 1.4, r, rng, light)
    for i in range(tufts):
        tx = X + W * (i + rng.uniform(.1, .9)) / max(1, tufts)
        mk_tuft(cv, tx, top(tx) + rng.uniform(.5, 3), min(H * 1.3, rng.uniform(9, 18)), rng)


def mk_hill(cv, top_pts, ybot, rng, light=_MKL, pitch=2., outline=.5, dark=1., fade=1.):
    """a hill or headland modelled by lines draped parallel to its crest, close and 1 px where
    the slope turns from the light, opening on the lit slope; crossed where deepest."""
    top_pts = sorted(top_pts)
    poly = top_pts + [(top_pts[-1][0], ybot), (top_pts[0][0], ybot)]
    cv.obj([poly], outline)
    lx = _mk_unit(light)[0]

    def T(x):
        for i in range(len(top_pts) - 1):
            (a, b), (c, d) = top_pts[i], top_pts[i + 1]
            if a <= x <= c:
                return b + (d - b) * (x - a) / ((c - a) or 1), (d - b) / ((c - a) or 1)
        return top_pts[-1][1], 0.
    x0, x1 = top_pts[0][0], top_pts[-1][0]
    H = ybot - min(p[1] for p in top_pts)
    k = 1
    off = pitch
    while off < H:
        run, wt = [], None
        x = x0
        while x <= x1:
            y, sl = T(x)
            yy = y + off + .4 * math.sin(x * .2 + k)
            if yy < ybot - .3:
                shade = sl * (-lx) * 1.  # slope descending away from the light
                w = 1 if (shade > .18 * fade and off < H * .7 * dark) else 0
                if w != wt and run:
                    (cv.line if wt else cv.hair)(run + [(x, yy)])
                    run = []
                wt = w
                run.append((x, yy))
                if w and shade > .5 and k % 2 == 0:
                    cv.hair([(x, yy), (x + 1.5, yy + 1.5)])
            elif run:
                (cv.line if wt else cv.hair)(run)
                run = []
            x += 2.
        if len(run) > 1:
            (cv.line if wt else cv.hair)(run)
        off += pitch * (1 + .5 * (off / H)) if fade else pitch
        k += 1


def mk_reflect(cv, x, ytop, ybot, half, rng, weight=1., pitch=1.5):
    """a reflection laid in the water: short 1 px strokes under the object, wobbling sideways
    and breaking more as the ripples carry it toward the viewer"""
    y = round((ytop + .25) * 2) / 2 + .25
    while y < ybot:
        f = (y - ytop) / max(1., ybot - ytop)
        hw = half * (1 - .35 * f) * rng.uniform(.75, 1.1)
        sh = rng.uniform(-1, 1) * (1 + 3 * f)
        segs = 1 + int(f * 3)
        a = x - hw + sh
        L = 2 * hw / segs
        for s_ in range(segs):
            g = rng.uniform(.5, 1.5) * f * 2
            (cv.line if weight >= 1 and rng.random() > f * .6 else cv.hair)([(a + s_ * L, y), (a + (s_ + 1) * L - g, y)])
        y += pitch if f < .5 else pitch * 1.34


def mk_drape(cv, top, poly, rng, pitch=2., heavy_from=.45, depth=None, dash=(6, 2.), step=1.5, dy=None):
    """form lines draped under a curve: copies of `top` (a polyline along the form's lit crest)
    stepped down by `pitch`, kept inside `poly`, broken into short burin strokes; hairlines
    under the crest, 1 px from `heavy_from` of the depth down into the shade (a belly, a hull,
    the underside of a bough). dy(x) can bend the offsets."""
    ys = [p[1] for p in poly]
    depth = depth or (max(ys) - min(ys))
    # resample the crest
    pts = []
    for i in range(len(top) - 1):
        (ax, ay), (bx, by) = top[i], top[i + 1]
        n = max(1, int(math.hypot(bx - ax, by - ay) / step))
        pts += [(ax + (bx - ax) * j / n, ay + (by - ay) * j / n) for j in range(n)]
    pts.append(top[-1])
    off = pitch * .75
    while off < depth:
        f = off / depth
        run = []
        for (x, y) in pts:
            yy = y + off * (dy(x) if dy else 1.)
            if _g_pip(x, yy, poly):
                run.append((x, yy))
            elif run:
                run.append(None)
        segs, cur = [], []
        for q in run:
            if q is None:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            else:
                cur.append(q)
        if len(cur) > 1:
            segs.append(cur)
        w = cv.line if f >= heavy_from else cv.hair
        for sg in segs:
            i = int(rng.uniform(0, dash[0]))
            while i < len(sg) - 1:
                L = max(2, int(rng.uniform(dash[0] * .6, dash[0] * 1.4)))
                w(sg[i: i + L])
                i += L + max(1, int(rng.uniform(dash[1] * .5, dash[1] * 1.5) * (1.4 - f)))
        off += pitch
# ==== GM ENGINE END ====


from engraving_codex import Canvas, hatch_poly, _n, _d, _ell_pts, pat, dark_ground

PI = math.pi


# ------------------------------------------------------------------ geometry helpers
def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def quad_lines(q, pitch_px, along=True):
    """Lines across a quad q=[p0,p1,p2,p3] (p0-p1 top edge, p3-p2 bottom edge): if along, lines run
    p0->p1 direction, spaced down the p0->p3 / p1->p2 sides; else run p0->p3 direction, spaced across."""
    p0, p1, p2, p3 = q
    if along:
        L = max(math.dist(p0, p3), math.dist(p1, p2))
        n = max(1, int(L / pitch_px))
        return [[lerp(p0, p3, i / n), lerp(p1, p2, i / n)] for i in range(1, n)]
    L = max(math.dist(p0, p1), math.dist(p3, p2))
    n = max(1, int(L / pitch_px))
    return [[lerp(p0, p1, i / n), lerp(p3, p2, i / n)] for i in range(1, n)]


def solid(cv, poly, w=1.5):
    """Black fill as tight heavy hatch (Canvas has white fills only)."""
    cv.heavy(hatch_poly(poly, 0, 1.25))


def bez(p0, p1, p2, p3, n=10):
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


_DOG_SIT = ("M.6,0C-.4,-1.6 -.2,-4 1.4,-5.2C2.6,-6 3.6,-6.6 4.3,-7.7L4.6,-9.5C4.8,-10.5 5.9,-10.9 6.7,-10.5"
            "L7.3,-9.7L8.9,-9.3C9.6,-9.1 9.6,-8.2 8.9,-8L7.4,-7.6C6.9,-6.6 6.9,-5.3 7,-4.3L7.2,-.4L7.8,0"
            "H5.9L5.8,-3.2L4.4,-1.6L4.6,-.4L5.2,0Z")


def flatten(d):
    import re
    toks = re.findall(r"[MLCHVZ]|-?\d*\.?\d+", d)
    pts, i, cmd, cur = [], 0, None, (0, 0)
    while i < len(toks):
        t = toks[i]
        if t in "MLCHVZ":
            cmd = t
            i += 1
            if cmd == "Z":
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
            c = [(float(toks[i + k]), float(toks[i + k + 1])) for k in (0, 2, 4)]
            pts += bez(cur, c[0], c[1], c[2], 6)
            cur = c[2]
            i += 6
        else:
            i += 1
    return pts


DOG = flatten(_DOG_SIT)


# ------------------------------------------------------------------ the scene
def scene(field, seed=0, tall=False):
    """Draw the Portland house scene filling `field` (polygon). Returns svg fragment (Canvas)."""
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
    FW, FH = fx1 - fx0, fy1 - fy0
    s = min(FW / 168., FH / 108.)
    if tall:
        s = min(FW / 215., FH / 150.)
    ox = (fx0 + fx1) / 2
    oy = (fy0 + fy1) / 2 + (-8 * s if tall else -2 * s)
    rng = random.Random(seed)

    def P(x, y):
        return (ox + x * s, oy + y * s)

    def PL(pts):
        return [P(x, y) for x, y in pts]

    cv = GmCanvas()
    BIGL, BIGR = -400, 400
    yb = (fy1 - oy) / s + 4     # field bottom in design units
    yt = (fy0 - oy) / s - 4

    # ---- sky: swelling burin lines opening into the glow of a morning sun rising behind Mount Hood,
    # low winter cumulus modelled in it
    cv.obj([field], 0)
    sx, sy, sr = 80, -40, 8.5
    hz = P(0, 16)[1]
    gm_sky(cv, fx0 - 2, fy0 - 2, FW + 4, hz - fy0 + 2, rng, (P(sx, sy)[0], P(sx, sy)[1], sr * s), 3 if tall else 2)

    # ---- Mount Hood
    HX = 20
    peak = (54 + HX, -44)
    left = [(-20 + HX, 16), (0 + HX, 6), (14 + HX, -4), (26 + HX, -16), (36 + HX, -26), (44 + HX, -34), (49 + HX, -40), peak]
    right = [(58 + HX, -41), (63 + HX, -36), (70 + HX, -28), (80 + HX, -18), (94 + HX, -6), (112 + HX, 6), (130 + HX, 16)]
    hood = PL(left + right)
    cv.obj([hood], 1.)
    snow = [(16, -6), (22, -12), (26, -10), (31, -18), (35, -15), (39, -24), (43, -20), (47, -30), (51, -24),
            (56, -31), (60, -22), (66, -27), (71, -17), (77, -20), (84, -10), (92, -12), (104, 0), (130, 16)]
    snow = [(x + HX, y) for x, y in snow]
    below = PL([(-20 + HX, 16)] + snow + [(150, 30), (-20, 30)])
    # below the snow: a timbered slope of little firs over a dark draped foot
    bx0, by0_ = P(-20 + HX, 16)
    bx1 = P(130 + HX, 16)[0]
    xx = bx0 + 2
    while xx < bx1 - 2:
        u = (xx - bx0) / (bx1 - bx0)
        sy_ = None
        sn = PL(snow)
        for (ax, ay), (cx_, cy_) in zip(sn[:-1], sn[1:]):
            if ax <= xx <= cx_:
                sy_ = ay + (cy_ - ay) * (xx - ax) / ((cx_ - ax) or 1)
                break
        if sy_ is not None:
            ty = sy_ + rng.uniform(1, 3)
            yy = ty
            while yy < by0_ - 1:
                (cv.line if u > .55 else cv.hair)([(xx, yy), (xx + 1.1, yy + 2.6), (xx - .2, yy + 2.6)])
                yy += 3.2
        xx += 2.2
    # east face in shadow: fall lines from the ridge, 1 px under it
    east = PL([(x + HX if i else x, y) for i, (x, y) in enumerate([peak, (58, -41), (63, -36), (70, -28), (80, -18), (94, -6), (112, 6), (60, 6), (57, -20)])])
    for ln in hatch_poly(east, 62, 2):
        (ax, ay), (bx_, by_) = sorted(ln, key=lambda q: q[1])
        cv.line([(ax, ay), ((ax + bx_) / 2, (ay + by_) / 2)])
        cv.hair([((ax + bx_) / 2, (ay + by_) / 2), (bx_, by_)])
    # glacier ridges on the lit snow
    for k in range(7):
        a = (peak[0] - 2 - k * 1.2, peak[1] + 3 + k * 2.2)
        b = (a[0] - 6 - k * 4, a[1] + 10 + k * 1.5)
        cv.hair([P(*a), P(*lerp(a, b, .5)), P(b[0] + 1, b[1])])
    cv.line([P(*peak), P(57 + HX, -30), P(58 + HX, -20)])
    # rock ribs on the west face
    for k in range(5):
        a = (peak[0] - 5 - k * 6, peak[1] + 8 + k * 6)
        cv.hair([P(*a), P(a[0] - 3, a[1] + 4), P(a[0] - 2, a[1] + 8)])

    # ---- Forest Park ridge (left) and the Willamette
    ridge = [(BIGL, 16)] + [(x, 2 - 3 * math.sin(x * .05) - 2 * math.sin(x * .13 + 1)) for x in range(-130, 31, 5)] + [(30, 16)]
    rp = PL(ridge)
    cv.obj([rp], .5)
    # Forest Park: a dark ridge of firs, cut as rows of little spires
    yrow = min(p[1] for p in rp) + .5
    k = 0
    while yrow < P(0, 16)[1]:
        zz = []
        x = fx0 - 4 + (1.2 if k % 2 else 0)
        while x < P(30, 0)[0]:
            zz += [(x, yrow + 1.2), (x + 1.2, yrow - .9)]
            x += 2.4
        cv.hair(zz)
        yrow += 2.
        k += 1
    river = PL([(BIGL, 8), (-20, 8), (-20, 16), (BIGL, 16)])
    cv.obj([river], 0)
    for j, y in enumerate(range(9, 16)):
        x = -120 + (j * 7) % 9
        while x < -24:
            ln = 6 + (j * 5 + int(x)) % 8
            cv.hair([P(x, y), P(x + ln, y)])
            x += ln + 3

    # ---- St. Johns Bridge: two Gothic towers, cables and deck
    deck_y = 4
    towers = (-94, -70)
    cv.obj([], 0)
    cab = []
    for i in range(41):
        x = towers[0] + (towers[1] - towers[0]) * i / 40
        t = i / 40
        cab.append((x, -20 + 22 * 4 * t * (1 - t) * .8))
    for x, y in cab[2:-2:2]:
        cv.hair([P(x, y), P(x, deck_y)])
    cv.line(PL(cab))
    side_l = [(towers[0] - 30 + 30 * t, deck_y - 22 * t ** 1.6) for t in [i / 12 for i in range(13)]]
    side_r = [(towers[1] + 16 * t, -20 + 24 * t ** .7) for t in [i / 12 for i in range(13)]]
    cv.line(PL(side_l))
    cv.line(PL(side_r))
    for x, y in side_l[1:-1]:
        cv.hair([P(x, y), P(x, deck_y)])
    deck = PL([(-140, deck_y - .8), (-40, deck_y - .8), (-40, deck_y + 1.2), (-140, deck_y + 1.2)])
    cv.obj([deck], .5)
    cv.hair([P(-140, deck_y + .2), P(-40, deck_y + .2)])
    for tx in towers:
        tw = 2.4
        tp = PL([(tx - tw * 1.15, 9), (tx - tw, -16), (tx - tw * 1.1, -18), (tx - tw * .7, -19), (tx - tw * .7, -21.5),
                 (tx - tw * .3, -21.5), (tx, -25), (tx + tw * .3, -21.5), (tx + tw * .7, -21.5), (tx + tw * .7, -19),
                 (tx + tw * 1.1, -18), (tx + tw, -16), (tx + tw * 1.15, 9)])
        cv.obj([tp], .5)
        cv.hair(hatch_poly(PL([(tx, -26), (tx + tw, -18), (tx + tw, 9), (tx, 9)]), 90, 1.5))
        for (a0, a1) in ((-16, -8), (-5, 2)):
            op = PL([(tx - tw * .55, a1), (tx - tw * .55, a0 + 1.6), (tx, a0), (tx + tw * .55, a0 + 1.6), (tx + tw * .55, a1)])
            cv.obj([op], 0)
            solid(cv, op)
        # piers in the river
        pier = PL([(tx - tw * 1.3, 8), (tx + tw * 1.3, 8), (tx + tw * 1.3, 12), (tx - tw * 1.3, 12)])
        cv.obj([pier], .5)
        cv.hair(hatch_poly(pier, 90, 1.5))

    # ---- far lawn / meadow ground
    ground = PL([(BIGL, 16), (BIGR, 16), (BIGR, yb), (BIGL, yb)])
    cv.obj([ground], .5)
    # grass: rows of strokes, growing toward the viewer
    r2 = random.Random(seed + 7)
    tufts = []
    gy = 17.
    xl, xr = (fx0 - ox) / s - 2, (fx1 - ox) / s + 2
    while gy < yb:
        f = max(0., min(1., (gy - 16) / max(1., yb - 16)))
        hgt = (1.6 + 4.5 * f) / s
        stepx = (2.3 + 2. * f) / s * (1 + max(0., FH - 250) / 500)
        gx = xl + r2.uniform(0, stepx)
        row = []
        while gx < xr:
            lean = r2.uniform(-.4, .7) / s
            row += [P(gx, gy), P(gx + lean, gy - hgt * r2.uniform(.6, 1.2))]
            gx += stepx * r2.uniform(.7, 1.3)
        tufts.append(row)
        gy += (1.9 + 2.6 * f) / s
    cv.hair(tufts)

    # ---- Douglas firs
    def fir(x, base, hgt, dark=True):
        # a Douglas fir in drooping tiers, each bough's needles falling dark into its shade side
        bx_, by_ = P(x, base)
        mk_tree(cv, bx_, by_, hgt * s, rng, "fir", wd=hgt * .72 * s)

    fir(-62, 44, 70)
    fir(-104, 40, 56)
    fir(-82, 34, 22)
    fir(70, 40, 66)
    fir(84, 36, 44)
    fir(96, 32, 30)

    # ---- the house (drawn larger, set forward on the lawn) --------------------
    base_P = P
    HK = 1.3

    def P(x, y):
        return base_P(-2 + (x + 8) * HK, 54 + (y - 46) * HK)

    def PL(pts):
        return [P(x, y) for x, y in pts]

    # side wall (in shade), receding to the right
    sw = [(-8, 8), (34, 3), (34, 42), (-8, 46)]
    swp = PL(sw)
    cv.obj([swp], 1.)
    cv.hair(quad_lines(swp, 1.5))
    cv.hair(hatch_poly(swp, 90, 3))
    # side windows
    for (a, b) in ((2, 11), (19, 27)):
        def yt_(x):
            return 8 + (3 - 8) * (x + 8) / 42
        def yb_(x):
            return 46 + (42 - 46) * (x + 8) / 42
        top = lambda x: yt_(x) + 9
        bot = lambda x: yt_(x) + 26
        win = PL([(a, top(a)), (b, top(b)), (b, bot(b)), (a, bot(a))])
        cv.obj([win], 1.)
        inner = PL([(a + 1.2, top(a) + 1.4), (b - 1.2, top(b) + 1.4), (b - 1.2, bot(b) - 1.4), (a + 1.2, bot(a) - 1.4)])
        cv.obj([inner], 0)
        solid(cv, inner)
        m = (a + b) / 2
        mid = lambda x: (top(x) + bot(x)) / 2
        cv.obj([PL([(a + 1, mid(a) - .6), (b - 1, mid(b) - .6), (b - 1, mid(b) + .6), (a + 1, mid(a) + .6)])], 0)
        cv.obj([PL([(m - .4, top(m)), (m + .4, top(m)), (m + .4, bot(m)), (m - .4, bot(m))])], 0)
        # sill
        cv.obj([PL([(a - 1.2, bot(a)), (b + 1.2, bot(b)), (b + 1.2, bot(b) + 1.4), (a - 1.2, bot(a) + 1.4)])], .5)
    # eave shadow under the side roof
    es = PL([(-8, 8), (34, 3), (34, 6), (-8, 11.5)])
    cv.obj([es], 0)
    solid(cv, es)

    # chimney (behind the roof ridge, drawn before roof so the roof clips it)
    ch = PL([(14, -38), (21, -38.6), (21, -6), (14, -6)])
    cv.obj([ch], 1.)
    cv.hair(hatch_poly(ch, 0, 2))
    bricks = []
    for j, yy in enumerate(range(-37, -6, 2)):
        for xx in ([15.6, 18.4] if j % 2 else [17, 19.8]):
            bricks.append([P(xx, yy), P(xx, yy + 2)])
    cv.hair(bricks)
    cv.hair(hatch_poly(PL([(18.5, -38.4), (21, -38.6), (21, -6), (18.5, -6)]), 90, 1.5))
    cap = PL([(13, -40.4), (22, -41), (22, -38.4), (13, -38)])
    cv.obj([cap], 1.)
    cv.hair(hatch_poly(cap, 0, 1.5))

    # side roof plane: ridge from gable peak back to the right, eave along the side wall top
    rf = PL([(-28, -26), (14, -30), (38, 4), (-6, 10)])
    cv.obj([rf], 1.)
    cv.hair(quad_lines(rf, 2.))                       # shingle courses
    cv.hair(quad_lines(rf, 3., along=False))          # down-slope shading
    cv.hair(hatch_poly(PL([(-6, 10), (38, 4), (34, -2), (-10, 4)]), 70, 1.5))  # darker near the eave
    cv.line([P(-28, -26), P(14, -30)])

    # front wall below the gable
    fw = PL([(-50, 10), (-8, 10), (-8, 46), (-50, 46)])
    cv.obj([fw], 1.)
    cv.hair(hatch_poly(fw, 0, 2, .7))                  # clapboards
    # porch shade
    shade = PL([(-50, 24), (-8, 24), (-8, 42), (-50, 42)])
    cv.hair(hatch_poly(shade, 45, 2))
    cv.hair(hatch_poly(PL([(-50, 24), (-8, 24), (-8, 28), (-50, 28)]), -45, 2))
    # front window (big Craftsman window with transom)
    win = PL([(-46, 27), (-33, 27), (-33, 40), (-46, 40)])
    cv.obj([win], 1.)
    tr = PL([(-45, 28), (-34, 28), (-34, 31), (-45, 31)])
    cv.obj([tr], 0)
    solid(cv, tr)
    for k in range(3):
        cv.obj([PL([(-42.6 + k * 3.7, 28), (-42 + k * 3.7, 28), (-42 + k * 3.7, 31), (-42.6 + k * 3.7, 31)])], 0)
    gl = PL([(-45, 32.2), (-34, 32.2), (-34, 39), (-45, 39)])
    cv.obj([gl], 0)
    solid(cv, gl)
    cv.obj([PL([(-39.9, 32), (-39.1, 32), (-39.1, 39), (-39.9, 39)])], 0)
    # door with its lights
    dr = PL([(-24, 26), (-16, 26), (-16, 42), (-24, 42)])
    cv.obj([dr], 1.)
    cv.hair(hatch_poly(dr, 90, 1.5))
    cv.obj([PL([(-23, 27.2), (-17, 27.2), (-17, 30.5), (-23, 30.5)])], .5)
    solid(cv, PL([(-22.7, 27.6), (-17.3, 27.6), (-17.3, 30.1), (-22.7, 30.1)]))
    cv.obj([PL([(-17.8, 34), (-17, 34), (-17, 35), (-17.8, 35)])], 0)

    # gable: shingled triangle with attic window, deep bargeboards
    gab = PL([(-28, -26), (-48, 10), (-10, 10)])
    cv.obj([gab], 1.)
    sh_lines = hatch_poly(gab, 0, 2)
    cv.hair(sh_lines)
    ticks = []
    for j, yy in enumerate(range(-22, 10, 2)):
        half = 20 * (yy + 26) / 36
        x = -28 - half + (1.5 if j % 2 else .4)
        while x < -28 + half:
            ticks.append([P(x, yy - 1.0), P(x, yy)])
            x += 3
    cv.hair(ticks)
    aw = PL([(-33, -8), (-23, -8), (-23, 4), (-33, 4)])
    cv.obj([aw], 1.)
    awi = PL([(-32, -7), (-24, -7), (-24, 3), (-32, 3)])
    cv.obj([awi], 0)
    solid(cv, awi)
    cv.obj([PL([(-28.4, -7), (-27.6, -7), (-27.6, 3), (-28.4, 3)]), PL([(-32, -2.4), (-24, -2.4), (-24, -1.6), (-32, -1.6)])], 0)
    # knee braces under the eaves
    for bx, d in ((-48, 1), (-10, -1)):
        br = PL([(bx, 10), (bx + d * 4, 10), (bx + d * .8, 14)])
        cv.obj([br], .5)
        cv.hair(hatch_poly(br, 0, 1.5))
    # bargeboards: thick rake trim with a black underside
    for (a, b) in (((-28, -27.4), (-52, 11)), ((-28, -27.4), (-6, 11))):
        n = (b[1] - a[1], -(b[0] - a[0]))
        L = math.hypot(*n)
        nx, ny = n[0] / L * 2.2, n[1] / L * 2.2
        if nx > 0:
            nx, ny = -nx, -ny
        bb = PL([a, b, (b[0] - nx * .2, b[1] + 2.2), (a[0], a[1] + 2.4)])
        cv.obj([bb], 1.)
        cv.hair([P(a[0], a[1] + 1.1), P(b[0], b[1] + 1.1)])
    # porch roof (a shed across the front)
    pr = PL([(-53, 20), (-5, 20), (-5, 24.5), (-53, 24.5)])
    cv.obj([pr], 1.)
    cv.hair(hatch_poly(PL([(-53, 20), (-5, 20), (-5, 22), (-53, 22)]), 0, 1.5))
    solid(cv, PL([(-53, 23), (-5, 23), (-5, 24.5), (-53, 24.5)]))
    # tapered Craftsman columns on brick piers
    for cx in (-49, -29.5, -9):
        col = PL([(cx - 1.4, 24.5), (cx + 1.4, 24.5), (cx + 2.2, 36), (cx - 2.2, 36)])
        cv.obj([col], 1.)
        cv.hair(hatch_poly(PL([(cx + .2, 24.5), (cx + 1.4, 24.5), (cx + 2.2, 36), (cx + .4, 36)]), 90, 1.5))
        pier = PL([(cx - 3, 36), (cx + 3, 36), (cx + 3, 42), (cx - 3, 42)])
        cv.obj([pier], 1.)
        cv.hair(hatch_poly(pier, 0, 1.5))
        cv.hair([[P(cx - 1, yy), P(cx - 1, yy + 1.5)] for yy in (36, 39)] + [[P(cx + 1.5, yy), P(cx + 1.5, yy + 1.5)] for yy in (37.5, 40.5)])
    # porch floor and foundation
    fl = PL([(-53, 42), (-5, 42), (-5, 44), (-53, 44)])
    cv.obj([fl], 1.)
    fd = PL([(-52, 44), (-6, 44), (-6, 47), (-52, 47)])
    cv.obj([fd], .5)
    cv.hair(hatch_poly(fd, 45, 2))
    cv.hair(hatch_poly(fd, -45, 2))
    fd2 = PL([(-8, 46), (34, 42), (34, 44.5), (-8, 48.5)])
    cv.obj([fd2], .5)
    solid(cv, fd2)
    # steps
    for k in range(3):
        st = PL([(-33 - k * 1.2, 44 + k * 2), (-25 + k * 1.2, 44 + k * 2), (-25 + k * 1.2, 46 + k * 2), (-33 - k * 1.2, 46 + k * 2)])
        cv.obj([st], 1.)
        cv.hair([P(-33 - k * 1.2, 45.4 + k * 2), P(-25 + k * 1.2, 45.4 + k * 2)])
        cv.hair(hatch_poly(PL([(-33 - k * 1.2, 45.4 + k * 2), (-25 + k * 1.2, 45.4 + k * 2), (-25 + k * 1.2, 46 + k * 2), (-33 - k * 1.2, 46 + k * 2)]), 0, 1.5))

    # rhododendrons along the foundation
    def shrub(x, y, w_, h_, sd):
        rr = random.Random(sd)
        top = []
        nb = 9
        for i in range(nb + 1):
            t = i / nb
            top.append((x - w_ / 2 + w_ * t, y - h_ * math.sin(PI * t) ** .6 - rr.uniform(0, h_ * .25)))
        bump = []
        for i in range(len(top) - 1):
            a, b = top[i], top[i + 1]
            mid = lerp(a, b, .5)
            bump += [a, (mid[0], mid[1] - 1.4)]
        poly = PL(bump + [top[-1], (x + w_ / 2, y), (x - w_ / 2, y)])
        cx_, cy_ = P(x, y - h_ * .45)
        mk_foliage(cv, cx_, cy_, w_ * s * HK, h_ * s * HK * 1.1, rr, (-.6, -.8), dark=1.1, leaf=2.4)
        # blossoms: tiny white rings
        for i in range(int(w_ / 3)):
            bx = x - w_ / 2 + 2 + rr.uniform(0, w_ - 4)
            by = y - rr.uniform(1.5, h_ * .7)
            ring = _ell_pts(*P(bx, by), .9 * s, .9 * s, 10)
            cv.obj([ring], .5)

    shrub(-46, 49, 13, 7, seed + 1)
    shrub(4, 49, 16, 8, seed + 2)
    shrub(26, 46, 14, 7, seed + 3)

    # brick walk from the steps down the lawn
    wk = [(-33.5, 50), (-24.5, 50), (-12, yb), (-48, yb)]
    wkp = PL(wk)
    cv.obj([wkp], 1.)
    yy, j = 51.0, 0
    rows = []
    while yy < yb:
        t = (yy - 50) / max(1, yb - 50)
        xl = -33.5 + (-48 + 33.5) * t
        xr = -24.5 + (-12 + 24.5) * t
        rows.append([P(xl, yy), P(xr, yy)])
        nb = 4
        for k in range(1, nb):
            bx = xl + (xr - xl) * (k - (.5 if j % 2 else 0)) / nb
            rows.append([P(bx, yy), P(bx, yy + 1.4 + t * 2)])
        yy += 1.4 + t * 2
        j += 1
    cv.hair(rows)
    cv.hair(hatch_poly(PL([(-24.5, 50), (-12, yb), (-20, yb), (-27.5, 50)]), 70, 3))

    # ---- Easter egg: Parker's dog sitting on the porch by the steps, looking out
    dx0, dy0, dk = -15.5, 43.9, .95
    dg = PL([(dx0 + x * dk, dy0 + y * dk) for x, y in DOG])
    halo_d = PL([(dx0 + 4 + (x - 4) * 1.22 * dk, dy0 + .6 + y * 1.12 * dk) for x, y in DOG])
    cv.obj([halo_d], 0)
    cv.obj([dg], 1.)
    solid(cv, dg)
    eye = _ell_pts(*P(dx0 + 6.7 * dk, dy0 - 8.7 * dk), .3 * s * HK, .3 * s * HK, 8)
    cv.obj([eye], 0)
    collar = PL([(dx0 + 4.3 * dk, dy0 - 7 * dk), (dx0 + 7.2 * dk, dy0 - 6.6 * dk), (dx0 + 7.2 * dk, dy0 - 6.1 * dk), (dx0 + 4.2 * dk, dy0 - 6.5 * dk)])
    cv.obj([collar], 0)

    # mailbox post at the walk with the house number plate (a tiny engraved P)
    mb = PL([(-6, 54), (-1, 54), (-1, 57.5), (-6, 57.5)])
    post = PL([(-4, 57.5), (-3, 57.5), (-3, 66), (-4, 66)])
    cv.obj([post], .5)
    cv.hair(hatch_poly(post, 90, 1.5))
    cv.obj([mb], 1.)
    cv.hair(hatch_poly(PL([(-6, 56), (-1, 56), (-1, 57.5), (-6, 57.5)]), 0, 1.5))
    cv.line([P(-1, 54.4), P(.6, 52.6), P(.6, 54)])

    return cv.svg()


def scene_svg(field, cid, seed=0, tall=False):
    d = _d(field, True, 0)
    return (f'<clipPath id="{cid}"><path d="{d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{scene(field, seed, tall)}</g>')


# ------------------------------------------------------------------ house key (tall tablet)
def key_svg(x, y, w, h, seed=0):
    """A house key lying across the tablet, its bow a carved volute, on a ruled ground."""
    o = [gm_ground((x - 4, y - 4, w + 8, h + 8), "l")]
    cv = GmCanvas()
    cy = y + h / 2
    kh = h * .55
    bx = x + w * .2
    # bow: a ring
    ring = _ell_pts(bx, cy, kh * .55, kh * .55, 40)
    hole = _ell_pts(bx, cy, kh * .2, kh * .2, 24)
    cv.obj([ring], 1.)
    cv.hair(hatch_poly(ring, 0, 1.5))
    cv.obj([hole], 1.)
    cv.hair(hatch_poly(hole, 0, 1.5))
    # shank
    x0, x1 = bx + kh * .5, x + w * .8
    sh = [(x0, cy - kh * .12), (x1, cy - kh * .12), (x1 + kh * .15, cy), (x1, cy + kh * .12), (x0, cy + kh * .12)]
    cv.obj([sh], 1.)
    cv.hair([[(x0, cy + kh * .04), (x1, cy + kh * .04)]])
    cv.hair(hatch_poly([(x0, cy + kh * .04), (x1, cy + kh * .04), (x1, cy + kh * .12), (x0, cy + kh * .12)], 0, 1.5))
    # bit with cuts
    bit = [(x1 - kh * 1.4, cy + kh * .12)]
    cuts = [.35, .2, .45, .28, .4]
    for i, c in enumerate(cuts):
        xa = x1 - kh * 1.4 + kh * 1.3 * i / len(cuts)
        xb = x1 - kh * 1.4 + kh * 1.3 * (i + 1) / len(cuts)
        bit += [(xa, cy + kh * (.12 + c)), (xb, cy + kh * (.12 + c))]
    bit += [(x1 - kh * .1, cy + kh * .12)]
    cv.obj([bit], 1.)
    cv.hair(hatch_poly(bit, 90, 1.5))
    # collar
    col = [(x0 - 1, cy - kh * .22), (x0 + 3, cy - kh * .22), (x0 + 3, cy + kh * .22), (x0 - 1, cy + kh * .22)]
    cv.obj([col], 1.)
    cv.hair(hatch_poly(col, 90, 1.5))
    o.append(cv.svg())
    # volute growing out of the bow
    o.append(C.acanthus_scroll(bx, cy, kh * .7, a0=200, turns=1.1, seed=seed, fronds=2, leaf_scale=.6))
    return "".join(o)


# ------------------------------------------------------------------ layouts (from the codex, the field filled)
def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.0, 150)
    o.append(C._clip(C._uid("b3", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _ell_pts(cx, cy, rx - 4.3, ry - 4.3, 72)
    o.append(scene_svg(field, C._uid("bs", w, h, seed), seed))
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 4, ry - 4, 72), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _cartouche_field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - .3, b - .3)


def _layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.85)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(10 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m3", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene_svg(_cartouche_field(cx, cy, cw, gh + 4), C._uid("ms", w, h, seed), seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, density=1.):
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
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(8 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t3", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene_svg(_cartouche_field(cx, cy, cw, ch), C._uid("ts", w, h, seed), seed, tall=True))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # rule the ribbon face so no white field remains
    lines = []
    for f in (-.5, -.3, -.1, .1, .3, .5):
        lines.append(_d([(px, py + f * bh) for px, py in centre], tol=.2))
    o.append(f'<path d="{"".join(lines)}" stroke="#000" stroke-width=".5" fill="none"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(C._clip(C._uid("k3", w, h, seed), tx, ty, tw, th, key_svg(tx, ty, tw, th, seed)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f3", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3

    def sc(X, Y, W, H, level):
        f = [(X - 3, Y - 3), (X + W + 3, Y - 3), (X + W + 3, Y + H + 3), (X - 3, Y + H + 3)]
        return scene(f, seed, level == 2)
    # the edition plan: a vignette with an arched top, the island house; egg the dog on the porch
    # art director, batch 2: a free-standing shaped scene, its frame from the page's own motifs
    V = {"seed": seed, "scene": sc, "shape": "archtop", "edge": "dissolve", "frame": ("none", None)}
    return vg_plate(w, h, ctx, V)
