"""music-07 "Meet a local artist": the house Codex frame round a bespoke vignette of today's artist.

Today (and whenever the page names a writer): an open book lies on a ruled table, its pages set
with engraved lines of type, a combination wrench crossing behind it and a toothed gear rising like
a sun over the horizon (Palahniuk wrote Fight Club while working as a diesel mechanic).
The subject follows the page text: a writer gets the book, a musician a record, anyone else a
painter's palette; "mechanic"/"diesel" adds the wrench and gear sun.
Tall plates letter the artist's name on the ribbon and LOCAL ARTIST OF THE DAY on the pedestal
tablet, drawn as engraved paths.
Easter egg: Parker's crossed drumsticks lie on the table beside the book.
"""
import sys
import math
import random
import re
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
    40 % smaller), same occlusion rules. clip=(x0, y0, x1, y1) drops everything outside."""
    fill_tol, line_tol = .7, .5
    shadow = None

    def svg(self, clip=None):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
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
        pen = _GPen()
        for polys, _, _ in self.objs:
            for poly in polys:
                if keep(poly):
                    pen.add(poly if C._area(poly) >= 0 else poly[::-1], True, self.fill_tol)
        T = ' transform="scale(.5)"'
        if pen.o:
            if self.shadow:
                pid = "gmF%x" % (zlib.crc32(pen.d()[:400].encode()) & 0xffffff)
                dx, dy = self.shadow
                res.append(f'<defs><path id="{pid}"{T} d="{pen.d()}"/></defs>'
                           f'<use href="#{pid}" transform="translate({_n(dx)},{_n(dy)})" fill="#000"/>'
                           f'<use href="#{pid}" fill="#fff"/>')
            else:
                res.append(f'<path{T} d="{pen.d()}" fill="#fff" stroke="none"/>')
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
    """a cumulus bank: billows painted back to front, each lit on its upper side and modelled by
    arcs that follow its round into the shade, over a flat, ruled-dark base."""
    h = min(h, 22.)
    nb = max(3, int(w / max(5., h * .8)))
    bills = []
    for k in range(nb):
        t = (k + rng.uniform(.25, .75)) / nb
        r = h * (.42 + .62 * math.sin(_GPI * t) ** .8) * rng.uniform(.8, 1.12)
        bills.append((cx - w / 2 + w * t, cy - r * .35, r))
    for k in range(max(1, nb // 3)):
        t = rng.uniform(.3, .7)
        r = h * rng.uniform(.6, .85)
        bills.append((cx - w / 2 + w * t, cy - h * .55 - r * .2, r))
    base = cy + h * .3
    order = bills[nb:] + sorted(bills[:nb], key=lambda b: -abs(b[0] - cx))
    for bx, by, r in order:
        p = [q for q in _Gel(bx, by, r, r * .9, 30)[:-1]]
        p = [(q[0], min(q[1], base)) for q in p]
        cv.obj([p], .5)
        # the billow's round: arcs that follow it, close in the shade (lower right), opening
        # to a thin lit rim on the upper left
        j = 1
        while True:
            rr = r - 1.5 * j
            if rr < 1.2:
                break
            a0 = math.radians(-60 + 25 * (rr / r))
            a1 = math.radians(150 + 40 * (1 - rr / r))
            arc = [(bx + (r - rr) * .25 + rr * math.cos(t), by + (r - rr) * .2 + rr * .9 * math.sin(t))
                   for t in [a0 + (a1 - a0) * i / 18 for i in range(19)]]
            arc = [q for q in arc if q[1] < base - .5]
            if len(arc) > 1:
                (cv.line if j == 1 and r > 7 else cv.hair)(arc)
            j += 1 if rr > r * .5 else 2
        # a light tone of gently waved lines over the whole billow, leaving a lit rim
        if r > 5:
            yy = by - r * .9 + 2.5
            while yy < min(base, by + r * .9) - 1:
                hw = r * math.sqrt(max(0., 1 - ((yy - by) / (r * .9)) ** 2)) - 2.2
                if hw > 1.5:
                    cv.hair([(bx - hw + i * hw / 4, yy + .3 * math.sin(i * 1.3)) for i in range(9)])
                yy += 3.
    und = [(cx - w * .5, base - h * .25), (cx + w * .5, base - h * .25), (cx + w * .44, base + .5), (cx - w * .44, base + .5)]
    cv.obj([und], 0)
    yy = base - h * .2
    while yy < base:
        cv.hair([(cx - w * .46, yy), (cx + w * .46, yy)])
        yy += 1.5


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
        pitch = 1.5 if f < .22 * dark else 2. if f < .55 else 3.
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
            if f < .45 and len(sg) > 8:
                a = int(len(sg) * rng.uniform(.15, .3))
                b = int(len(sg) * rng.uniform(.7, .85))
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
        cw = W * rng.uniform(.22, .38)
        ch = H * rng.uniform(.1, .16)
        cx = X + W * t
        cy = Y + H * rng.uniform(.18, .62)
        if sun and math.hypot(cx - sun[0], cy - sun[1]) < sun[2] * 2:
            cy += sun[2] * 2.5
        gm_cloud(cv, cx, cy, cw, ch, rng)


def gm_water(cv, X, Y, W, H, rng, glint_x=None):
    """water in broken, gently waved lines, closer toward the viewer, a glitter path left open
    under glint_x."""
    y = round((Y + .25) * 2) / 2 + .25
    while y < Y + H + 2:
        f = (y - Y) / max(1., H)
        pitch = 3. if f < .25 else 2. if f < .6 else 1.5
        x = X - 6 - rng.uniform(0, 12)
        while x < X + W + 6:
            L = rng.uniform(8, 26) * (1.3 - f * .5)
            if glint_x is not None and abs(x + L / 2 - glint_x) < 6 + 14 * f:
                L *= .35
            n = max(2, int(L / 3))
            amp = rng.uniform(.2, .5)
            cv.hair([(x + L * i / n, y + amp * math.sin(_GPI * i / n)) for i in range(n + 1)])
            x += L + rng.uniform(1.5, 3.5)
        y += pitch
# ==== GM ENGINE END ====



_n, _d, _ell = C._n, C._d, C._ell_pts
PI, TAU = math.pi, 2 * math.pi


# ----------------------------------------------------------------------------------------------
# the page's subject
# ----------------------------------------------------------------------------------------------

def _subject(ctx):
    s = ((ctx or {}).get("sample") or "")
    low = s.lower()
    if re.search(r"novel|book|writer|author|poet|essay|memoir", low):
        kind = "book"
    elif re.search(r"band|music|song|singer|jazz|drum|album|record|guitar|rapper|composer", low):
        kind = "record"
    else:
        kind = "palette"
    mech = bool(re.search(r"mechanic|diesel|engine|machin|welder", low))
    name = ""
    m = re.search(r"Of the day\s+(.*)", s)
    if m:
        words = []
        for wd in m.group(1).split():
            if wd[:1].isupper() or wd in ("&", "de", "van", "von"):
                words.append(wd)
            else:
                break
        name = " ".join(words[:4])
    name = "".join(ch for ch in name.upper() if ch in _G or ch == " ")
    return kind, mech, name.strip()


# ----------------------------------------------------------------------------------------------
# a little stroke alphabet for engraved lettering (glyphs on a 4 x 6 grid, y down)
# ----------------------------------------------------------------------------------------------

_G = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "B": [[(0, 6), (0, 0), (2.8, 0), (3.6, .8), (3.6, 2.2), (2.8, 3), (0, 3)], [(2.8, 3), (3.8, 3.8), (3.8, 5.2), (3, 6), (0, 6)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.6, 6), (4, 4.6), (4, 1.4), (2.6, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (2.8, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (2.8, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.4), (2.4, 3.4)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.3, 2.6), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2, 3.6), (4, 0), (4, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2.2), (3, 3.2), (0, 3.2)]],
    "Q": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)], [(2.4, 4.4), (4.2, 6.4)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2.2), (3, 3.2), (0, 3.2)], [(2, 3.2), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1, 6), (2, 2.4), (3, 6), (4, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "&": [[(4, 6), (1, 2), (1, .8), (2, 0), (3, .8), (3, 1.6), (0, 4), (0, 5), (1, 6), (2.6, 6), (4, 3.6)]],
    ".": [[(1.8, 5.6), (2.2, 6)]],
    "-": [[(1, 3), (3, 3)]],
    "'": [[(2, 0), (1.6, 1.6)]],
}


def _letters(text, cx, cy, cap, centre=None):
    """Polylines spelling text centred on (cx, cy), cap px tall; centre: an optional list of
    points (a ribbon's centre line) to bend the baseline along. Returns (polylines, width)."""
    k = cap / 6
    adv = [(2.6 if ch == " " else 4) + 2.2 for ch in text]
    W = (sum(adv) - 2.2) * k
    x = cx - W / 2
    out = []

    def yoff(px):
        if not centre:
            return 0.
        for i in range(1, len(centre)):
            if centre[i][0] >= px:
                a, b = centre[i - 1], centre[i]
                t = (px - a[0]) / ((b[0] - a[0]) or 1)
                return a[1] + (b[1] - a[1]) * t - cy
        return centre[-1][1] - cy

    for ch, a in zip(text, adv):
        for st in _G.get(ch, []):
            out.append([(x + px * k, cy - cap / 2 + py * k + yoff(x + px * k)) for px, py in st])
        x += a * k
    return out, W


def _lettering(text, cx, cy, cap, centre=None, sw=1.):
    pl, W = _letters(text, cx, cy, cap, centre=centre)
    d = "".join(_d(p, tol=0) for p in pl)
    return (f'<path d="{d}" stroke="#fff" stroke-width="{_n(sw + 2)}"/>'
            f'<path d="{d}" stroke="#000" stroke-width="{_n(sw)}"/>'), W


def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


# ----------------------------------------------------------------------------------------------
# the vignette pieces (all draw into Canvases; later canvases paint over earlier ones)
# ----------------------------------------------------------------------------------------------

def _gear_sun(cv, cx, cy, R, teeth):
    """A toothed gear half-risen over the horizon: turned rings on its face, shaded tooth flanks,
    a black hub and bolt holes."""
    pts = []
    n = teeth * 4
    for i in range(n + 1):
        a = PI + PI * i / n
        r = R if (i % 4) in (1, 2) else R * .86
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    poly = pts + [(cx + R * .86, cy + 1), (cx - R * .86, cy + 1)]
    cv.obj([poly], 1.)
    r = R * .8
    while r > R * .22:
        cv.hair(_ell(cx, cy, r, r, 48, PI, TAU))
        r -= 1.5 if r < R * .45 else 3.
    cv.line(_ell(cx, cy, R * .82, R * .82, 48, PI, TAU))
    for i in range(teeth):
        a0 = PI + PI * (4 * i + 1) / n
        a1 = PI + PI * (4 * i + 2) / n
        p0 = (cx + R * math.cos(a0), cy + R * math.sin(a0))
        p1 = (cx + R * math.cos(a1), cy + R * math.sin(a1))
        q0 = (cx + R * .86 * math.cos(a0), cy + R * .86 * math.sin(a0))
        q1 = (cx + R * .86 * math.cos(a1), cy + R * .86 * math.sin(a1))
        cv.hair(C.hatch_poly([q0, p0, p1, q1], math.degrees((a0 + a1) / 2) + 90, 1.5))
    hub = _ell(cx, cy, R * .2, R * .2, 24, PI, TAU) + [(cx + R * .2, cy + 1), (cx - R * .2, cy + 1)]
    cv.obj([hub], 1.)
    cv.line(C.hatch_poly(hub, 0, .8))


def _rays(cv, cx, cy, R0, x0, y0, x1, y1, n=28):
    """Ray wedges, each hatched across, radiating over the ruled sky."""
    far = max(x1 - x0, y1 - y0) * 1.5
    for i in range(0, n, 2):
        a = PI + PI * (i + .5) / n
        da = PI / n * .5
        wdg = [(cx + R0 * math.cos(a - da * .3), cy + R0 * math.sin(a - da * .3)),
               (cx + far * math.cos(a - da), cy + far * math.sin(a - da)),
               (cx + far * math.cos(a + da), cy + far * math.sin(a + da)),
               (cx + R0 * math.cos(a + da * .3), cy + R0 * math.sin(a + da * .3))]
        cv.obj([wdg], 0)
        cv.hair(C.hatch_poly(wdg, math.degrees(a) + 90, 1.5))


def _wrench(cv, p0, p1, wd):
    """A combination wrench from p0 (open jaw) to p1 (ring end), steel shaded along its length."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    R = wd * 1.3

    def at(t, s):
        hw = wd / 2 * (1 - .2 * math.sin(PI * t)) * s
        return (p0[0] + dx * t + nx * hw, p0[1] + dy * t + ny * hw)

    T = [k / 24 for k in range(25)]
    sh = [at(t, 1) for t in T] + [at(t, -1) for t in T[::-1]]
    sw = R * .9
    a1 = math.asin(min(.95, sw / 2 / R))
    base = math.atan2(-uy, -ux)
    jaw = [(p0[0] + R * math.cos(base + a1 + (TAU - 2 * a1) * i / 28),
            p0[1] + R * math.sin(base + a1 + (TAU - 2 * a1) * i / 28)) for i in range(29)]
    c0 = (p0[0] - ux * R * .1, p0[1] - uy * R * .1)
    jaw += [(c0[0] - nx * sw / 2, c0[1] - ny * sw / 2), (c0[0] + nx * sw / 2, c0[1] + ny * sw / 2)]
    ring = _ell(p1[0], p1[1], R * .95, R * .95, 32)
    cv.obj([sh], 1.)
    for s in (.55, .2, -.15):
        cv.hair([at(t, s) for t in T[2:23]])
    for s in (-.45, -.7):
        cv.line([at(t, s) for t in T[2:23]])
    for P, poly, rad in ((p0, jaw, R), (p1, ring, R * .95)):
        cv.obj([poly], 1.)
        for rr in (.82, .66):
            cv.hair([(P[0] + rad * rr * math.cos(a), P[1] + rad * rr * math.sin(a))
                     for a in [base + .85 + (PI * .95 - .85) * k / 14 for k in range(15)]])
        cv.line([(P[0] + rad * .9 * math.cos(a), P[1] + rad * .9 * math.sin(a))
                 for a in [base + PI * 1.1 + PI * .6 * k / 12 for k in range(13)]])
    hexp = [(p1[0] + R * .5 * math.cos(a), p1[1] + R * .5 * math.sin(a)) for a in [TAU * k / 6 + .3 for k in range(6)]]
    cv.obj([hexp], 1.)
    cv.line(C.hatch_poly(hexp, 0, .8))


def _pen(cv, p0, p1, wd):
    """A fountain pen from p0 (nib) to p1 (cap end): turned barrel shaded along its length, a
    cap band, the clip, and a split steel nib."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux

    def at(t, s, hw):
        return (p0[0] + dx * t + nx * hw * s, p0[1] + dy * t + ny * hw * s)

    nib_t = .16
    nib = [at(0, 0, 0), at(nib_t, 1, wd * .42), at(nib_t + .02, 0, 0), at(nib_t, -1, wd * .42)]
    T = [nib_t + (1 - nib_t) * k / 20 for k in range(21)]

    def hw(t):
        return wd / 2 * (.72 + .28 * min(1, (t - nib_t) / .12)) * (1 - .15 * max(0, t - .85) / .15)

    body = [at(t, 1, hw(t)) for t in T] + [at(t, -1, hw(t)) for t in T[::-1]]
    cv.obj([nib], 1.)
    cv.hair(C.hatch_poly(nib, math.degrees(math.atan2(uy, ux)) + 90, 1.5))
    cv.line([at(.02, 0, 0), at(nib_t - .02, 0, 0)])
    cv.obj([body], 1.)
    for sv in (.5, .15):
        cv.hair([at(t, sv, hw(t)) for t in T[1:-1]])
    for sv in (-.4, -.65):
        cv.line([at(t, sv, hw(t)) for t in T[1:-1]])
    for tb in (.56, .6):
        cv.line([at(tb, 1, hw(tb)), at(tb, -1, hw(tb))])
    clip = [at(.62, .55, hw(.62)), at(.95, .55, hw(.95)), at(.95, .2, hw(.95)), at(.66, .2, hw(.66))]
    cv.obj([clip], 1.)
    cv.hair(C.hatch_poly(clip, math.degrees(math.atan2(uy, ux)), 1.5))


def _mt_hood(cv, x, base, w, h):
    """Mt. Hood on the horizon: a snow-capped cone, lit flank ruled lightly, shadow flank dark."""
    pk = (x + w * .48, base - h)
    pts = [(x, base + 1), (x + w * .2, base - h * .3), (x + w * .36, base - h * .72), pk,
           (x + w * .6, base - h * .76), (x + w * .78, base - h * .32), (x + w, base + 1)]
    cv.obj([pts], 1.)
    # lit west flank cut along its fall line, the east flank in close slope-following shade
    cv.hair(C.hatch_poly(pts, -math.degrees(math.atan2(h, w * .48)), 3.))
    shade = [pk, (x + w * .6, base - h * .76), (x + w * .78, base - h * .32), (x + w, base + 1), (x + w * .55, base + 1)]
    cv.line(C.hatch_poly(shade, math.degrees(math.atan2(h, w * .52)), 1.5))
    snow = [(x + w * .36, base - h * .72), pk, (x + w * .6, base - h * .76), (x + w * .52, base - h * .66),
            (x + w * .46, base - h * .74), (x + w * .41, base - h * .64)]
    cv.obj([snow], 1.)


def _nut(cv, cx, cy, r):
    """A hex nut lying on the table: shaded flats, a lit top face, a black bore."""
    top = [(cx + r * math.cos(a), cy - r * .45 + r * .45 * math.sin(a)) for a in [TAU * k / 6 for k in range(6)]]
    body = [(cx - r, cy - r * .45), (cx - r, cy + r * .05), (cx - r * .5, cy + r * .44), (cx + r * .5, cy + r * .44),
            (cx + r, cy + r * .05), (cx + r, cy - r * .45)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly(body, 90, 1.5))
    cv.obj([top], 1.)
    cv.hair(C.hatch_poly(top, 0, 3, 1))
    hole = _ell(cx, cy - r * .45, r * .42, r * .2, 16)
    cv.obj([hole], 1.)
    cv.line(C.hatch_poly(hole, 0, .8))


def _drumsticks(cv, cx, cy, L):
    """Parker's crossed drumsticks (the Easter egg): tapered sticks with turned bead tips."""
    for s in (-1, 1):
        a = s * .5
        ux, uy = math.cos(a), math.sin(a) * .75
        ul = math.hypot(ux, uy)
        ux, uy = ux / ul, uy / ul
        nx, ny = -uy, ux
        p0 = (cx - ux * L / 2, cy - uy * L / 2)
        pl, pr = [], []
        for i in range(13):
            t = i / 12
            hw = max(.8, L * .04 * (1 - .6 * t ** 1.5))
            px, py = p0[0] + ux * L * t, p0[1] + uy * L * t
            pl.append((px + nx * hw, py + ny * hw))
            pr.append((px - nx * hw, py - ny * hw))
        cv.obj([pl + pr[::-1]], 1.)
        cv.hair([_lerp(a_, b_, .7) for a_, b_ in zip(pl, pr)][:11])
        tip = (p0[0] + ux * L * 1.04, p0[1] + uy * L * 1.04)
        bead = _ell(tip[0], tip[1], L * .05 + .6, L * .04 + .5, 12)
        cv.obj([bead], 1.)
        cv.hair(C.hatch_poly(bead, 30, 1.5))


def _book(cv, cx, by, B, rng):
    """An open book on the table: black boards, page blocks with stacked fore-edges, curving pages
    set with lines of engraved type (chapter head, drop cap), a shadowed gutter, a ribbon marker."""
    lift = B * .13
    ph = B * .34
    dep = max(3., B * .05)

    def cur(u):
        return math.sin(PI * .75 * min(max(u, 0), 1)) ** .6

    def top(u):
        return by - ph - lift * cur(u)

    def bot(u):
        return by - lift * .55 * cur(u)

    def pt(s, u, v):
        return (cx + s * B / 2 * u, top(u) * (1 - v) + bot(u) * v)

    U = [k / 30 for k in range(31)]
    for s in (-1, 1):
        ex = B / 2 + max(2., B * .025)
        cov = ([(cx, by + dep * .2 + 3)] + [(cx + s * ex * u, bot(u) + dep * u + 3) for u in U[1:]] +
               [(cx + s * ex, top(1) + 2)] + [(cx + s * ex * u, top(u) + 2) for u in U[::-1]])
        cv.obj([cov], 1.)
        cv.line(C.hatch_poly(cov, 0, .8))
    nl = max(4, int(ph / 3.))
    for s in (-1, 1):
        blk = ([(cx + s * B / 2 * u, bot(u) + dep * u) for u in U] +
               [(cx + s * B / 2, top(1) + dep * .3)] + [(cx + s * B / 2 * u, top(u)) for u in U[::-1]])
        cv.obj([blk], 1.)
        k = 1.
        while k < dep - .4:
            cv.hair([(cx + s * B / 2 * u, bot(u) + k * u) for u in U[3:]])
            k += 1.5
        page = [pt(s, u, 1) for u in U] + [pt(s, u, 0) for u in U[::-1]]
        cv.obj([page], 1.)
        V = [m / 16 for m in range(17)]
        gw = [pt(s, 0, 0), pt(s, .025, 0), pt(s, .025, 1), pt(s, 0, 1)]
        cv.line(C.hatch_poly(gw, 90, .8))
        for j, uu in enumerate([.035, .05, .068, .09, .115, .145, .18, .22]):
            (cv.line if j < 3 else cv.hair)([pt(s, uu, v) for v in V])
        for uu in (.955, .98):
            cv.hair([pt(s, uu, v) for v in V])
        for li in range(nl):
            v = (li + 1.2) / (nl + .8)
            if s < 0 and li < 2:
                if li == 1:
                    cv.line([pt(s, u, v) for u in [.36 + .38 * m / 10 for m in range(11)]])
                continue
            if s > 0 and li == nl - 1:
                continue
            u = .34 if (s < 0 and li in (2, 3)) else .22
            uend = .9 if li % 6 != 5 else .58
            while u < uend:
                u1 = min(uend, u + rng.uniform(.04, .15))
                cv.hair([pt(s, uu, v) for uu in [u + (u1 - u) * m / 4 for m in range(5)]])
                u = u1 + .024
        if s < 0:
            v0, v1 = 2.6 / (nl + .8), 4.4 / (nl + .8)
            dcp = [pt(s, .3, v0), pt(s, .22, v0), pt(s, .22, v1), pt(s, .3, v1)]
            cv.obj([dcp], 1.)
            cv.line(C.hatch_poly(dcp, 0, .8))
    cv.line([(cx, by - ph), (cx, by + 1)])


def _record(cv, cx, cy, R):
    """A long-player lying on the table: grooves of fine rings with a lit sector, label, spindle."""
    ry = R * .42
    cv.obj([_ell(cx, cy, R, ry, 64)], 1.)
    r = R * .97
    while r > R * .38:
        cv.hair(_ell(cx, cy, r, r * .42, 64, PI * 1.25, PI * 2.95))
        r -= 1.5
    lab = _ell(cx, cy, R * .36, ry * .36, 32)
    cv.obj([lab], 1.)
    cv.hair(C.hatch_poly(lab, 0, 2))
    sp = _ell(cx, cy, 1.8, 1.1, 10)
    cv.obj([sp], 1.)
    cv.line(C.hatch_poly(sp, 0, .8))


def _palette(cv, cx, cy, R):
    pts = [(cx + R * (1 + .08 * math.sin(3 * a)) * math.cos(a), cy + R * .5 * (1 + .08 * math.sin(3 * a)) * math.sin(a))
           for a in [TAU * i / 48 for i in range(48)]]
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, -20, 3))
    hole = _ell(cx + R * .45, cy + R * .1, R * .14, R * .08, 16)
    cv.obj([hole], 1.)
    cv.line(C.hatch_poly(hole, 0, .8))
    for k in range(6):
        a = PI * 1.05 + PI * .85 * k / 5
        b = _ell(cx + R * .7 * math.cos(a), cy + R * .35 * math.sin(a), R * .09, R * .055, 12)
        cv.obj([b], 1.)
        cv.hair(C.hatch_poly(b, 45 * (k % 3), [1.5, 2, 3][k % 3]))


def _scene(fx, fy, fw, fh, clip_d, ctx, seed, big):
    """The engraved vignette filling the field bbox (fx, fy, fw, fh), clipped to clip_d."""
    kind, mech, _ = _subject(ctx)
    rng = random.Random(seed)
    cx = fx + fw / 2
    hor = fy + fh * (.5 if big else .56)
    o = []
    cvb = GmCanvas()
    gm_sky(cvb, fx - 2, fy - 2, fw + 4, hor - fy + 3, rng, None, 2 if big else 0)
    B = min(fw * (.8 if big else .6), fh * 1.2)
    by = hor + (fy + fh - hor) * (.5 if big else .42)
    R = min(fw * .3, (hor - fy) * .95)
    _rays(cvb, cx, hor, R * 1.06, fx, fy, fx + fw, hor, 30 if big else 22)
    if mech:
        _gear_sun(cvb, cx, hor, R, 11 if big else 8)
    else:
        disc = _ell(cx, hor, R * .8, R * .8, 40, PI, TAU) + [(cx + R * .8, hor + 1), (cx - R * .8, hor + 1)]
        cvb.obj([disc], 1.)
        cvb.hair(C.hatch_poly(disc, 0, 2))
    mh = (hor - fy) * (.34 if big else .3)
    _mt_hood(cvb, fx + fw * .02, hor, fw * .3, mh)
    hills = [(fx + fw * .62, hor + 1)] + [(fx + fw * (.62 + .4 * t / 20), hor - mh * .28 * math.sin(PI * t / 20) ** .7 - mh * .08 * math.sin(t))
                                          for t in range(21)] + [(fx + fw + 2, hor + 1)]
    cvb.obj([hills], 1.)
    # the hills: contour cuts that follow the crest down to the horizon
    crest = hills[1:-1]
    for k in range(1, 40):
        run = [(x, y + 1.5 * k) for x, y in crest if y + 1.5 * k < hor - .3]
        if len(run) > 1:
            (cvb.line if k % 3 == 0 else cvb.hair)(run)
    tab = [(fx - 2, hor), (fx + fw + 2, hor), (fx + fw + 2, fy + fh + 2), (fx - 2, fy + fh + 2)]
    cvb.obj([tab], 1.)
    # the table top: planks running back to the horizon, each cut with waved grain and a knot or two
    nk = 22
    for k in range(-nk, nk + 1):
        a = (cx + k * fw * .045 / 2, hor)
        b = (cx + k * fw * .16 / 2, fy + fh + 2)
        if k % 2 == 0:
            cvb.line([a, b])
            continue
        for g in (-.3, 0., .3):
            ph = rng.uniform(0, TAU)
            pts = []
            for j in range(25):
                t = j / 24
                x = a[0] + (b[0] - a[0]) * t
                wdt = (fw * .045 / 2 + (fw * .16 / 2 - fw * .045 / 2) * t)
                pts.append((x + wdt * (g + .12 * math.sin(ph + t * 9)), a[1] + (b[1] - a[1]) * t))
            cvb.hair(pts)
        if rng.random() < .3:
            t = rng.uniform(.3, .9)
            kx = a[0] + (b[0] - a[0]) * t
            ky = a[1] + (b[1] - a[1]) * t
            kr = (fw * .045 / 2 + (fw * .16 / 2 - fw * .045 / 2) * t) * .22
            cvb.hair(_ell(kx, ky, kr, kr * .6, 10))
    o.append(cvb.svg())
    cv = GmCanvas()
    if kind == "book":
        sh = [(cx - B * .56, by + B * .03), (cx + B * .56, by + B * .03), (cx + B * .66, by + B * .11), (cx - B * .46, by + B * .12)]
        cv.obj([sh], 0)
        cv.line(C.hatch_poly(sh, 0, 1.5))
        _book(cv, cx, by, B, rng)
        # the writer's pen lying across the right-hand page
        pg = by - B * .34 * .5 - B * .13 * .6
        _pen(cv, (cx + B * .1, pg + B * .1), (cx + B * .46, pg - B * .1), max(3.5, B * .055))
        if mech:
            # the mechanic's wrench lying on the table in front
            wy = by + (fy + fh - by) * .42
            _wrench(cv, (cx - B * .5, wy + B * .03), (cx + B * .02, wy - B * .01), max(3.5, B * .055))
    elif kind == "record":
        _record(cv, cx, by - B * .05, B * .45)
    else:
        _palette(cv, cx, by - B * .02, B * .42)
        if mech:
            _wrench(cv, (cx - B * .55, by + B * .1), (cx + B * .55, by - B * .15), max(3., B * .05))
    # Easter egg: Parker's crossed drumsticks lying on the table in front, right of centre
    L = max(16., B * .27)
    _drumsticks(cv, cx + B * .34, by + (fy + fh - by) * .45, L)
    o.append(cv.svg())
    cid = C._uid("v", fx, fy, fw, fh, seed)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{"".join(o)}</g>'


# ----------------------------------------------------------------------------------------------
# layouts (the house frames, with the whole cartouche field handed to the vignette)
# ----------------------------------------------------------------------------------------------

def _bead_ring(cx, cy, a, b):
    bp = C._superellipse(cx, cy, a, b)
    d = _d(bp + [bp[0]], tol=.15)
    return (f'<path d="{d}" fill="none" stroke="#fff" stroke-width="3.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.2, 160)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip = _d(_ell(cx, cy, rx - 4.5, ry - 4.5, 64), True)
    o.append(_scene(cx - rx + 4, cy - ry + 4, 2 * rx - 8, 2 * ry - 8, clip, ctx, seed, False))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.7)
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
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, inner, ctx, seed, h > 200))
    o.append(_bead_ring(cx, cy, a - 3.2, b - 3.2))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    _, _, name = _subject(ctx)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
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
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, inner, ctx, seed, True))
    o.append(_bead_ring(cx, cy, a - 3.2, b - 3.2))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bcy = cy + ch * .47
    bsvg, centre = C.ribbon_banner(cx, bcy, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    if name:
        cap = bh * .5
        lim = cw * 1.45 * .64
        _, W = _letters(name, cx, bcy, cap)
        if W > lim:
            cap *= lim / W
        o.append(_lettering(name, cx, bcy, cap, centre=centre, sw=1.)[0])
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 2.5)},{_n(ty + 2.5)}h{_n(tw - 4)}v{_n(th - 4)}h{_n(-tw + 4)}z" fill="{C.pat("L")}" stroke="none"/>')
    cap = min(th * .5, 11)
    _, W = _letters("LOCAL ARTIST OF THE DAY", 0, 0, cap)
    if W > tw * .8:
        cap *= tw * .8 / W
    t, W = _lettering("LOCAL ARTIST OF THE DAY", w / 2, ty + th / 2 + .8, cap, sw=1.5 if cap > 8 else 1.)
    o.append(t)
    for sx in (-1, 1):
        x = w / 2 + sx * (W / 2 + cap * .9)
        o.append(f'<path d="{_d(_ell(x, ty + th / 2 + .8, cap * .2, cap * .2, 12), True)}" fill="#000"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    _, _, name = _subject(ctx)

    def sc(X, Y, W, H, level):
        d = f"M{_n(X - 3)},{_n(Y - 3)}h{_n(W + 6)}v{_n(H + 6)}h{_n(-W - 6)}z"
        return _scene(X - 3, Y - 3, W + 6, H + 6, d, ctx, seed, level == 2)
    P = {"seed": seed, "scene": sc, "shape": "lozenge", "tall_shape": "arch", "band_aspect": 2.,
         "banner": (name or "MEET A LOCAL ARTIST").upper(), "tablet": gm_emblem("note"),
         "eggs": [("cymbal", {})]}
    return gm_plate(w, h, ctx, P)
