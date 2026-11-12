"""Civics plate (section front X), to the edition plan: an arched vignette, free-standing on a light
stippled ground, of the Oregon Capitol's gilded Pioneer (bearded, bareheaded, the axe over his
shoulder and the blanket-cloak hanging from it) on the fluted lantern. Light breaks from behind him
into a dark sky in burin tone, the glory's wedges held light; a sea of cloud with the Cascades
standing out of it fills the foot, fraying out into the ground the way a Bewick vignette does. A
ruled arch heads it; the small Somaster dedication cartouche (Parker's arms, solar/arms.py) sits at
its foot. At tall sizes the full Capitol on its mall (ballot drop box with crossed drumsticks) fills
the arch instead."""
import sys
import math
import random
import re
import engraving_codex as C

# ==== VIGNETTE KIT BEGIN (batch 6) ====
# Shared by the batch-6 plates: a free-standing engraved vignette on a light stippled ground (no
# black field, no generic scrollwork). The scene is clipped to a shaped silhouette (oval, roundel,
# arch, lunette, banner or a ragged Bewick edge), optionally ringed by a fine double rule; the page's
# own motifs make any frame. House Canvas emitted at half-px precision; drawn capitals for mottoes;
# Parker's figures for Easter eggs; Parker's arms (solar/arms.py) for section fronts.
import math as _m
import random as _r
import re as _re
import engraving_codex as _C

_Rib, _eul, _sm, _ell, _dd, _nn = _C._Rib, _C._euler, _C._smooth, _C._ell_pts, _C._d, _C._n
_PI, _TAU = _m.pi, 2 * _m.pi
_CRS = ' shape-rendering="crispEdges"'


class _Pen2:
    """path data in integer half-px (for transform="scale(.5)"), relative after the first point"""

    def __init__(self):
        self.o = []
        self.cur = None

    def add(self, pts, close=False, tol=.3):
        if len(pts) < 2:
            return
        if tol:
            pts = _C._dp(pts, tol)
        X = [int(round(p[0] * 2)) for p in pts]
        Y = [int(round(p[1] * 2)) for p in pts]
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


class Canvas(_C.Canvas):
    """the house Canvas, emitted at half-px precision with coarser simplification (smaller)"""

    def svg(self, tol_w=.7, tol_l=.7):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for w, lines in strokes.items():
                for pl in lines:
                    _C._clip_runs(pl, mask, x0, y0, W, H, out[w])
            for poly in polys:
                _C._fill_mask(poly, mask, x0, y0, W, H)
        T = ' transform="scale(.5)"'
        res = []
        # white shapes go out in runs of equal outline weight, each run one path filled white and
        # stroked with its own outline: later runs cover earlier runs' outlines (painter's order)
        runs = []
        for polys, ow, _ in self.objs:
            if not polys:
                continue
            if not runs or runs[-1][0] != ow:
                runs.append((ow, []))
            runs[-1][1].extend(polys)
        for ow, polys in runs:
            pen = _Pen2()
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_w)
            if pen.o:
                st = f'stroke="#000" stroke-width="{_nn(ow * 2)}"' if ow else 'stroke="none"'
                res.append(f'<path{T} d="{pen.d()}" fill="#fff" {st}/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _Pen2()
                for pl in out[w]:
                    if len(pl) > 1 and (len(pl) > 2 or abs(pl[0][0] - pl[-1][0]) + abs(pl[0][1] - pl[-1][1]) > .7):
                        pen.add(pl, False, tol_l)
                res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_nn(w * 2)}"/>')
        return "".join(res)


# ---------------------------------------------------------------------------------------------
# growth: stems that curl into spirals and branch, with leaves
# ---------------------------------------------------------------------------------------------


def _stipple_tile(seed, T, n):
    rng = _r.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < 6000:
        tries += 1
        x, y = rng.randrange(T), rng.randrange(T)
        if any(min((x - a) % T, (a - x) % T) < 2 and min((y - b) % T, (b - y) % T) < 2 for a, b in out):
            continue
        out.append((x, y))
    return out


def bead_line(pts, r=1.5, closed=False):
    """beads strung along a polyline, drawn as round dashes: a black ring, a white bead, and a
    small dark crescent offset to the lower right (three strokes on one path)"""
    seq = pts + ([pts[0]] if closed else [])
    L = sum(_m.hypot(seq[i][0] - seq[i - 1][0], seq[i][1] - seq[i - 1][1]) for i in range(1, len(seq)))
    p = 2 * r + 1.
    n = max(1, int(L / p))
    p = L / n
    d = _dd(seq, tol=.1)
    da = f'stroke-dasharray="0 {_nn(p)}" stroke-linecap="round" fill="none"'
    return (f'<path d="{d}" stroke="#000" stroke-width="{_nn(2 * r + 1)}" {da}/>'
            f'<path d="{d}" stroke="#fff" stroke-width="{_nn(2 * r)}" {da}/>'
            f'<path d="{d}" stroke="#000" stroke-width="{_nn(max(.8, r * .7))}" {da} transform="translate({_nn(r * .45)},{_nn(r * .45)})"/>'
            f'<path d="{d}" stroke="#fff" stroke-width="{_nn(max(.8, r * .7))}" {da} transform="translate({_nn(r * .2)},{_nn(r * .2)})"/>')


def shape_pts(cx, cy, a, b, kind="oval", n=120):
    pts = []
    for i in range(n):
        t = _TAU * i / n
        c_, s_ = _m.cos(t), _m.sin(t)
        e = {"oval": 2., "squircle": 2.8, "cushion": 3.6, "round": 2., "banner": 5., "lunette": 2.}.get(kind, 2.)
        x = cx + a * _m.copysign(abs(c_) ** (2 / e), c_)
        y = cy + b * _m.copysign(abs(s_) ** (2 / e), s_)
        if kind == "shield":
            if s_ > 0:
                x = cx + a * _m.copysign(abs(c_) ** .7, c_) * (1 - .6 * s_ ** 2.2)
                y = cy + b * s_ ** .8
            else:
                x = cx + a * _m.copysign(abs(c_) ** .35, c_)
                y = cy + b * .9 * _m.copysign(abs(s_) ** .35, s_)
        elif kind == "arch":
            if s_ > 0:
                x = cx + a * _m.copysign(abs(c_) ** .3, c_)
                y = cy + b * _m.copysign(abs(s_) ** .3, s_)
        elif kind == "banner":
            # a ribbon cartouche: long and square-shouldered, a swallowtail notch cut into each end
            x = cx + a * _m.copysign(abs(c_) ** (2 / e), c_) * (1 - .1 * _m.exp(-(s_ / .22) ** 2))
        elif kind == "lunette":
            if s_ > 0:
                x = cx + a * _m.copysign(abs(c_) ** .25, c_)
                y = cy + b * _m.copysign(abs(s_) ** .2, s_)
        elif kind == "quatre":
            rr = 1 + .07 * _m.cos(4 * t)
            x, y = cx + a * c_ * rr, cy + b * s_ * rr
        elif kind == "ogee":
            # pointed top (Thai temple window)
            if s_ < 0:
                y = cy + b * s_ * (1 + .25 * (1 - abs(c_)) ** 3)
                x = cx + a * c_ * (1 - .2 * abs(s_) ** 3)
        pts.append((x, y))
    return pts


def clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ---------------------------------------------------------------------------------------------
# small figural terminals and eggs that can be carved into the scroll (drawn into a Canvas)
# ---------------------------------------------------------------------------------------------


def fig_drumsticks(cv, cx, cy, s, ang=0.):
    for sd in (-1, 1):
        a = ang + sd * .62 - _PI / 2
        x0, y0 = cx - _m.cos(a) * s * .5, cy - _m.sin(a) * s * .5
        P = [(x0 + _m.cos(a) * s * t, y0 + _m.sin(a) * s * t) for t in (0, .5, 1)]
        R = _Rib(P, [s * .05, s * .045, s * .02], [s * .05, s * .045, s * .02])
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.5, 0, 1))
        tx, ty = P[-1]
        cv.obj([_ell(tx, ty, s * .05, s * .05, 10)[:-1]], .5)


def fig_heron(cv, x, y, s, flip=False):
    """a standing great blue heron, s tall"""
    f = -1 if flip else 1

    def T(u, v):
        return (x + f * u * s, y - v * s)
    body = [T(-.18, .5), T(.05, .62), T(.2, .58), T(.26, .5), T(.12, .36), T(-.1, .34), T(-.3, .38)]
    neck = [T(.12, .58), T(.2, .74), T(.12, .84), T(.17, .95), T(.25, .97), T(.27, .92), T(.18, .86), T(.25, .76), T(.18, .58)]
    bill = [T(.25, .97), T(.46, .93), T(.26, .92)]
    cv.obj([body], .5)
    cv.hair(_C.hatch_poly(body, 30 * f, 1.5))
    cv.obj([neck], .5)
    cv.hair([T(.16, .62), T(.21, .74)])
    cv.obj([bill], .5)
    cv.line([T(.0, .35), T(.02, .0)])
    cv.line([T(.06, .35), T(.1, .0)])
    cv.hair([T(.22, .96), T(.05, .99)])


def fig_mthood(cv, cx, by, w, hgt):
    """Mt Hood: the asymmetric cone with its notched summit, glaciers in the gullies, the shadow
    flank cut in 45-degree bulino, foothills of fir at the foot"""
    sil = [(-.5, 0), (-.36, .18), (-.22, .46), (-.12, .74), (-.05, .92), (-.01, 1.), (.03, .96), (.06, .99),
           (.12, .8), (.2, .58), (.3, .36), (.42, .14), (.5, 0)]
    P = [(cx + u * w, by - v * hgt) for u, v in sil]
    cv.obj([P], .5)
    # shadow flank (right of the ridge): diagonal cuts
    sh = [(cx + .03 * w, by - .96 * hgt), (cx + .06 * w, by - .99 * hgt), (cx + .12 * w, by - .8 * hgt),
          (cx + .2 * w, by - .58 * hgt), (cx + .3 * w, by - .36 * hgt), (cx + .42 * w, by - .14 * hgt),
          (cx + .5 * w, by), (cx + .1 * w, by), (cx + .04 * w, by - .5 * hgt)]
    cv.hair(_C.hatch_poly(sh, 45, 1.5))
    # glaciers: white tongues reaching down the gullies, edged with rock
    for g0, g1, L in ((-.08, -.02, .45), (.0, .07, .5), (-.18, -.12, .3), (.12, .18, .28)):
        tongue = [(cx + g0 * w, by - (.98 - .2) * hgt), (cx + g1 * w, by - .9 * hgt),
                  (cx + (g1 + g0) / 2 * w * 1.6, by - (.9 - L) * hgt)]
        cv.obj([tongue], .5)
    # foothills of fir across the base
    n = max(5, int(w / 5))
    for i in range(n):
        tx = cx - w * .5 + w * (i + .5) / n
        th = hgt * (.12 + .06 * ((i * 7) % 3))
        cv.obj([[(tx - th * .3, by), (tx, by - th), (tx + th * .3, by)]], .5)
        cv.hair([(tx, by - th), (tx + th * .22, by - th * .2)])


def fig_dog(cv, cx, cy, s, flip=False):
    """Parker's dog, curled asleep (s across)"""
    f = -1 if flip else 1
    body = _ell(cx, cy, s * .5, s * .3, 24)[:-1]
    cv.obj([body], .5)
    for k in range(4):
        rr = s * (.42 - .08 * k)
        cv.hair([(cx + f * rr * _m.cos(t), cy + s * .24 * (rr / (s * .42)) * _m.sin(t)) for t in [_PI * (.1 + .8 * i / 10) for i in range(11)]])
    hx, hy = cx + f * s * .34, cy - s * .12
    head = _ell(hx, hy, s * .18, s * .14, 14)[:-1]
    cv.obj([head], .5)
    cv.obj([[(hx - f * s * .05, hy - s * .1), (hx + f * s * .02, hy - s * .26), (hx + f * s * .1, hy - s * .08)]], .5)
    cv.line(_ell(hx + f * s * .14, hy + s * .02, .5, .5, 6))
    cv.hair([(hx - f * s * .02, hy + s * .02), (hx + f * s * .06, hy + s * .03)])


def _keep_disc(segs, cx, cy, r):
    """clip polylines (lists of points) to a disc: the shadow side of a form"""
    out = []
    for pl in segs:
        cur = []
        for i in range(len(pl) - 1):
            (ax, ay), (bx, by) = pl[i], pl[i + 1]
            n = max(1, int(_m.hypot(bx - ax, by - ay) / 1.5))
            for j in range(n + 1):
                px, py = ax + (bx - ax) * j / n, ay + (by - ay) * j / n
                if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                    cur.append((px, py))
                elif cur:
                    if len(cur) > 1:
                        out.append(cur)
                    cur = []
        if len(cur) > 1:
            out.append(cur)
    return out


def fig_dogface(cv, cx, cy, r):
    """Parker's dog looking straight out, the head filling a circle of radius r (the O of a word)"""
    for sd in (-1, 1):   # floppy ears, hatched dark on the inside
        ear = [(cx + sd * r * .45, cy - r * .75), (cx + sd * r * 1.02, cy - r * .55), (cx + sd * r * 1.08, cy + r * .1),
               (cx + sd * r * .9, cy + r * .45), (cx + sd * r * .62, cy + r * .1)]
        cv.obj([ear], 1.)
        cv.hair(_C.hatch_poly(ear, 70 * sd, 1.5))
    head = _ell(cx, cy, r * .72, r * .82, 24)[:-1]
    cv.obj([head], 1.)
    for k in range(3):   # the brow and the coat over the skull
        cv.hair([(cx - r * (.35 - k * .05), cy - r * (.62 - k * .1)), (cx, cy - r * (.5 - k * .1)), (cx + r * (.35 - k * .05), cy - r * (.62 - k * .1))])
    for sd in (-1, 1):
        cv.obj([_ell(cx + sd * r * .28, cy - r * .12, r * .11, r * .11, 10)[:-1]], 1.)
        cv.hair(_ell(cx + sd * r * .28, cy - r * .12, r * .18, r * .15, 10))
    muz = _ell(cx, cy + r * .32, r * .4, r * .32, 18)[:-1]
    cv.obj([muz], .5)
    cv.hair(_C.hatch_poly(_ell(cx + r * .12, cy + r * .4, r * .25, r * .2, 12)[:-1], 45, 1.5))
    cv.obj([[(cx - r * .14, cy + r * .12), (cx + r * .14, cy + r * .12), (cx, cy + r * .28)]], 1.)
    cv.line([(cx, cy + r * .28), (cx, cy + r * .4), (cx - r * .14, cy + r * .48)])
    cv.line([(cx, cy + r * .4), (cx + r * .14, cy + r * .48)])


def fig_p(cv, cx, cy, s):
    """a P monogram cut as a ribbon"""
    st = [(cx - s * .2, cy + s * .5), (cx - s * .2, cy - s * .5)]
    bowl = [(cx - s * .2 + s * .36 * _m.sin(t) * 1.1, cy - s * .22 - s * .28 * _m.cos(t)) for t in [_PI * i / 12 for i in range(13)]]
    for pl in (st, bowl):
        R = _Rib(pl, [s * .08] * len(pl), [s * .08] * len(pl))
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.4, 0, 1))


def fig_sun(cv, cx, cy, r, rays=16):
    """a sun: a modelled disc with a face-less boss and alternating straight and waved rays"""
    for k in range(rays):
        t = _TAU * k / rays
        L = r * (1.75 if k % 2 == 0 else 1.45)
        wv = k % 2
        pts = []
        for i in range(9):
            u = i / 8
            rr = r * 1.02 + (L - r) * u
            off = (.08 * _m.sin(u * _PI * 2) if wv else 0.)
            pts.append((cx + _m.cos(t + off) * rr, cy + _m.sin(t + off) * rr))
        R = _Rib(pts, [r * .16 * (1 - i / 8) + .4 for i in range(9)], [r * .16 * (1 - i / 8) + .4 for i in range(9)])
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.45, 0, .85, minw=.9))
    disc = _ell(cx, cy, r, r, 36)[:-1]
    cv.obj([disc], 1.)
    for q in (.78, .55):
        cv.hair(_ell(cx, cy, r * q, r * q, 28))
    cv.hair(_C.hatch_poly(_ell(cx + r * .25, cy + r * .25, r * .62, r * .62, 20)[:-1], 45, 1.5))


def arms_placeholder(cx, cy, s):
    """Parker's arms are pending: a beaded cartouche with crossed drumsticks over a sun. s tall."""
    w = s * .86
    fr, field, outer = medallion(cx, cy, w, s, "shield", True)
    cv = Canvas()
    fig_sun(cv, cx, cy - s * .04, s * .17)
    fig_drumsticks(cv, cx, cy + s * .02, s * .62)
    body = fr + f'<path d="{_dd(field, True, .1)}" fill="#fff" stroke="none"/>'
    gr = Canvas()
    gr.obj([field], 0)
    gr.hair(_C.hatch_poly(field, 0, 1.5, .25))
    return body + clip(f"gmA{int(cx)}{int(cy)}", _dd(field, True, .1), gr.svg() + cv.svg())


# ---------------------------------------------------------------------------------------------
# shaped panels and the gold line
# ---------------------------------------------------------------------------------------------


def arms_somaster(cx, cy, s, seed=0):
    """Parker's arms (Somaster) from the shared solar/arms.py, s tall; the placeholder if it is missing."""
    try:
        import arms as _AR
    except Exception:
        return arms_placeholder(cx, cy, s)
    w = s * 120. / 140.
    return (f'<svg x="{_nn(cx - w / 2)}" y="{_nn(cy - s / 2)}" width="{_nn(w)}" height="{_nn(s)}" overflow="visible">'
            + _slim(_simp(_AR.arms(w, s, seed), .25)) + "</svg>")


def _garc(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * _m.cos(_m.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * _m.sin(_m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_GF = {
    "A": (.72, [[(0, 1), (.36, 0), (.72, 1)], [(.15, .64), (.57, .64)]]),
    "B": (.6, [[(0, 0), (0, 1), (.38, 1)] + _garc(.38, .76, .22, .24, 90, -90, 6) + [(0, .52)],
               [(0, 0), (.33, 0)] + _garc(.33, .26, .2, .26, -90, 90, 6)[1:] + [(0, .52)]]),
    "C": (.66, [_garc(.36, .5, .34, .5, -45, -315, 12)]),
    "D": (.68, [[(0, 0), (0, 1), (.3, 1)] + _garc(.3, .5, .36, .5, 90, -90, 10) + [(0, 0)]]),
    "E": (.56, [[(.54, 0), (0, 0), (0, 1), (.54, 1)], [(0, .5), (.42, .5)]]),
    "F": (.54, [[(.54, 0), (0, 0), (0, 1)], [(0, .5), (.42, .5)]]),
    "G": (.7, [_garc(.36, .5, .34, .5, -45, -315, 12) + [(.7, .58), (.42, .58)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    "I": (.08, [[(.04, 0), (.04, 1)]]),
    "J": (.46, [[(.44, 0), (.44, .74)] + _garc(.22, .74, .22, .26, 0, 180, 6)[1:]]),
    "K": (.62, [[(0, 0), (0, 1)], [(.6, 0), (0, .6)], [(.2, .45), (.62, 1)]]),
    "L": (.52, [[(0, 0), (0, 1), (.52, 1)]]),
    "M": (.84, [[(0, 1), (0, 0), (.42, .8), (.84, 0), (.84, 1)]]),
    "N": (.68, [[(0, 1), (0, 0), (.68, 1), (.68, 0)]]),
    "O": (.76, [_garc(.38, .5, .38, .5, 0, 360, 16)]),
    "P": (.58, [[(0, 1), (0, 0), (.32, 0)] + _garc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)]]),
    "Q": (.76, [_garc(.38, .5, .38, .5, 0, 360, 16), [(.45, .7), (.78, 1.04)]]),
    "R": (.62, [[(0, 1), (0, 0), (.32, 0)] + _garc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)],
                [(.28, .54), (.62, 1)]]),
    "S": (.56, [_garc(.28, .25, .26, .25, -20, -270, 7) + _garc(.28, .75, .28, .25, -90, 160, 7)[1:]]),
    "T": (.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "U": (.66, [[(0, 0), (0, .66)] + _garc(.33, .66, .33, .34, 180, 0, 8)[1:] + [(.66, 0)]]),
    "V": (.7, [[(0, 0), (.35, 1), (.7, 0)]]),
    "W": (.96, [[(0, 0), (.24, 1), (.48, .2), (.72, 1), (.96, 0)]]),
    "X": (.64, [[(0, 0), (.64, 1)], [(.64, 0), (0, 1)]]),
    "Y": (.66, [[(0, 0), (.33, .5), (.66, 0)], [(.33, .5), (.33, 1)]]),
    "Z": (.6, [[(0, 0), (.6, 0), (0, 1), (.6, 1)]]),
    "0": (.54, [_garc(.27, .5, .27, .5, 0, 360, 14)]),
    "1": (.36, [[(.04, .2), (.26, 0), (.26, 1)], [(.04, 1), (.48, 1)]]),
    "2": (.54, [_garc(.27, .27, .26, .27, -170, 10, 6) + [(0, 1), (.54, 1)]]),
    "3": (.52, [_garc(.25, .25, .25, .25, -160, 90, 6), _garc(.25, .74, .27, .26, -90, 160, 6)]),
    "4": (.58, [[(.42, 1), (.42, 0), (0, .7), (.58, .7)]]),
    "5": (.54, [[(.5, 0), (.08, 0), (.04, .44)] + _garc(.26, .7, .28, .3, -120, 150, 8)]),
    "6": (.56, [[(.46, .02), (.2, .2), (.02, .65)] + _garc(.28, .7, .26, .3, 180, 540, 12)]),
    "7": (.54, [[(0, 0), (.54, 0), (.2, 1)]]),
    "8": (.54, [_garc(.27, .25, .22, .25, 90, 450, 10), _garc(.27, .74, .27, .26, -90, 270, 12)]),
    "9": (.56, [_garc(.28, .3, .26, .3, 0, 360, 12) + [(.54, .35), (.36, .8), (.1, .98)]]),
    "-": (.4, [[(.04, .55), (.36, .55)]]),
    ".": (.2, [[(.1, .92), (.1, .96)]]),
    "·": (.36, [[(.18, .4), (.26, .51), (.18, .62), (.1, .51), (.18, .4), (.18, .62)]]),
}


def motto(centre, txt, rh, w=1., holes=None, fill=.86):
    """txt lettered in drawn capitals along the ribbon centre line, cap = half the ribbon height"""
    cap = rh * .5
    L = sum(_m.dist(centre[i - 1], centre[i]) for i in range(1, len(centre)))
    tw = sum((_GF.get(ch, (.5, []))[0] + .32) * cap if ch != " " else .5 * cap for ch in txt) - .32 * cap
    _GF.setdefault("@", (.76, []))
    while tw > L * fill and cap > 3:
        cap *= .92
        tw = sum((_GF.get(ch, (.5, []))[0] + .32) * cap if ch != " " else .5 * cap for ch in txt) - .32 * cap

    def along(s, off):
        acc = 0.
        for i in range(1, len(centre)):
            p, q = centre[i - 1], centre[i]
            Lq = _m.dist(p, q)
            if acc + Lq >= s or i == len(centre) - 1:
                t = (s - acc) / Lq if Lq else 0
                nx, ny = (-(q[1] - p[1]) / Lq, (q[0] - p[0]) / Lq) if Lq else (0, 1)
                return (p[0] + (q[0] - p[0]) * t + nx * off, p[1] + (q[1] - p[1]) * t + ny * off)
            acc += Lq
        return centre[-1]
    out, cur = [], (L - tw) / 2
    for ch in txt.upper():
        if ch == " ":
            cur += .5 * cap
            continue
        gw, strokes = _GF.get(ch, _GF["·"])
        if ch == "@" and holes is not None:
            holes.append(along(cur + gw * cap / 2, 0.) + (cap,))
        for st in strokes:
            out.append([along(cur + px * cap, -cap / 2 + py * cap) for px, py in st])
        cur += (gw + .32) * cap
    return f'<path d="{"".join(_dd(p, False, .05) for p in out)}" fill="none" stroke="#000" stroke-width="{_nn(w)}"/>'


def _rdp(P, tol):
    if len(P) < 3:
        return P
    (ax, ay), (bx, by) = P[0], P[-1]
    dx, dy = bx - ax, by - ay
    L = _m.hypot(dx, dy) or 1e-9
    i, dm = 0, -1.
    for j in range(1, len(P) - 1):
        dd = abs((P[j][0] - ax) * dy - (P[j][1] - ay) * dx) / L
        if dd > dm:
            i, dm = j, dd
    if dm <= tol:
        return [P[0], P[-1]]
    return _rdp(P[:i + 1], tol)[:-1] + _rdp(P[i:], tol)


def _simp(sv, tol=.3):
    """path data of absolute M/L/Z polylines -> simplified, relative, one decimal"""
    def one(m):
        d = m.group(1)
        if not _re.fullmatch(r"(?:[MLZz][-\d., ]*)+", d):
            return m.group(0)
        o, cx, cy = [], 0., 0.
        for sub in _re.findall(r"M[^M]*", d):
            closed = sub.rstrip().endswith(("Z", "z"))
            nums = [float(v) for v in _re.findall(r"-?\d*\.?\d+", sub)]
            P = _rdp(list(zip(nums[0::2], nums[1::2])), tol)
            q = []
            for k, (x, y) in enumerate(P):
                x, y = round(x, 1), round(y, 1)
                if k == 0:
                    q.append(f"M{_nn(x)} {_nn(y)}" if not o else f"m{_nn(round(x - cx, 1))} {_nn(round(y - cy, 1))}")
                else:
                    q.append(f"l{_nn(round(x - cx, 1))} {_nn(round(y - cy, 1))}")
                cx, cy = x, y
            if closed:
                q.append("z")
                cx, cy = round(P[0][0], 1), round(P[0][1], 1)
            o.append("".join(q))
        return ' d="' + "".join(o) + '"'
    return _re.sub(r' d="([^"]*)"', one, sv)


def _slim(sv):
    """one decimal, no 0. or .0 padding inside path data"""
    def dd(m):
        d = _re.sub(r"(\d\.\d)\d+", r"\1", m.group(1))
        d = _re.sub(r"(\d)\.0(?!\d)", r"\1", d)
        d = _re.sub(r"(?<![\d.])0\.(\d)", r".\1", d)
        return ' d="' + d + '"'
    return _re.sub(r' d="([^"]*)"', dd, sv)


def _rel_h(m):
    """d of absolute M x,y h l runs -> one relative path (same marks, fewer bytes)"""
    o, px, py = [], None, None
    for x, y, l in _re.findall(r"M([-\d.]+),([-\d.]+)h([-\d.]+)", m.group(1)):
        x, y, l = round(float(x), 1), round(float(y), 1), round(float(l), 1)
        if px is None:
            o.append(f"M{_nn(x)} {_nn(y)}h{_nn(l)}")
        else:
            o.append(f"m{_nn(round(x - px, 1))} {_nn(round(y - py, 1))}h{_nn(l)}")
        px, py = round(x + l, 1), y
    return 'd="' + "".join(o) + '"'


def tone_hatch(cv, poly, tone, ang=45., pitch=1.5, cross=.7, cross_ang=None, step=1.2, phase=0.):
    """burin tone: hatch the shape, each line swelling and tapering with tone(x, y) in 0..1 (0 =
    lit paper, 1 = deepest shadow): gaps in the light, 0.5 px, 1 px, then 1.5 px lines, and a
    second set of cuts laid across wherever the tone passes `cross`"""
    def run(segs, tf, lo):
        for a_, b_ in segs:
            L = _m.hypot(b_[0] - a_[0], b_[1] - a_[1])
            n = max(1, int(L / step))
            cur, cw = [], None
            for j in range(n + 1):
                x = a_[0] + (b_[0] - a_[0]) * j / n
                y = a_[1] + (b_[1] - a_[1]) * j / n
                t = tf(x, y)
                wv = 0 if t < lo else (.5 if t < lo + .3 else (1. if (t < lo + .6 or pitch < 2.5) else 1.5))
                if wv != cw:
                    if cw and len(cur) > 1:
                        {.5: cv.hair, 1.: cv.line, 1.5: cv.heavy}[cw](cur)
                    cur = [cur[-1]] if (cur and wv and cw) else []
                    cw = wv
                cur.append((x, y))
            if cw and len(cur) > 1:
                {.5: cv.hair, 1.: cv.line, 1.5: cv.heavy}[cw](cur)
    run(_C.hatch_poly(poly, ang, pitch, phase), tone, .14)
    if cross is not None and cross < 1:
        ca = ang + 72 if cross_ang is None else cross_ang
        run(_C.hatch_poly(poly, ca, max(1.5, pitch * 1.34), phase + .5), lambda x, y: (tone(x, y) - cross) / (1 - cross) * .9, .12)


def lit(cx, cy, a, b, base=.25, depth=.7, lx=-.6, ly=-.8, rim=.25):
    """a tone function for a rounded form centred (cx, cy), half-sizes a, b, lit from (lx, ly):
    lit side near base, the terminator swinging into depth, a little reflected light at the rim"""
    ln = _m.hypot(lx, ly)
    lx, ly = lx / ln, ly / ln

    def t(x, y):
        u, v = (x - cx) / a, (y - cy) / b
        r = min(1., _m.hypot(u, v))
        nz = _m.sqrt(max(0., 1 - r * r))
        d = u * lx + v * ly + nz * .55
        tv = base + depth * (1 - d) * .62
        if r > .8:
            tv -= rim * (r - .8) / .2 * (1 if d < 0 else 0)
        return max(0., min(1., tv))
    return t


def _hash(*a):
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(map(str, a)))) % 99991


def vk_ground(w, h, uid, dense=False):
    """the light ground the vignette stands on: a fine random stipple, never bare paper"""
    T = 30
    rng = _r.Random(_hash(uid))
    g = 4 if dense else 5
    pts = [(int(i * g + rng.uniform(0, g - 1)), int(j * g + rng.uniform(0, g - 1)))
           for i in range(T // g) for j in range(T // g) if rng.random() < .82]
    d = "".join(f"M{x},{y}h1v1h-1z" for x, y in pts)
    pid = f"vkL{uid}"
    return (f'<defs><pattern id="{pid}" width="{T}" height="{T}" patternUnits="userSpaceOnUse">'
            f'<path d="{d}" fill="#000"{_CRS}/></pattern></defs>'
            f'<path d="M0,0h{_nn(w)}v{_nn(h)}h-{_nn(w)}z" fill="#fff"/>'
            f'<path d="M0,0h{_nn(w)}v{_nn(h)}h-{_nn(w)}z" fill="url(#{pid})"/>')


def ragged(poly, amp, seed, cut=None):
    """roughen a silhouette the way a Bewick vignette frays: low-frequency wander plus short
    breaks; cut(x, y) -> bool keeps chosen stretches of the edge clean (e.g. a ruled top)"""
    rng = _r.Random(seed)
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    ph = [rng.uniform(0, _TAU) for _ in range(3)]
    out = []
    for i, (x, y) in enumerate(poly):
        if cut and cut(x, y):
            out.append((x, y))
            continue
        t = _TAU * i / n
        k = (.55 * _m.sin(3 * t + ph[0]) + .3 * _m.sin(11 * t + ph[1]) + .15 * _m.sin(29 * t + ph[2]))
        k = k * amp + rng.uniform(-amp * .35, amp * .35)
        dx, dy = x - cx, y - cy
        r = _m.hypot(dx, dy) or 1
        out.append((x - dx / r * (amp - k), y - dy / r * (amp - k)))
    return out


def vignette(w, h, uid, sil, body, rule=None, extra="", dense=False):
    """assemble: light ground over the whole w x h, the scene clipped to the silhouette, a fine
    double rule round it if asked (rule = the clean silhouette), then any over-laid ornament"""
    o = [vk_ground(w, h, uid, dense)]
    d = _dd(sil, True, .1)
    o.append(f'<path d="{d}" fill="#fff" stroke="none"/>')
    o.append(clip(f"vkC{uid}", d, _slim(body)))
    if rule:
        r1 = _dd(rule + [rule[0]], tol=.1)
        o.append(f'<path d="{r1}" fill="none" stroke="#000" stroke-width="1.5"/>')
        cx = sum(p[0] for p in rule) / len(rule)
        cy = sum(p[1] for p in rule) / len(rule)
        out = []
        for x, y in rule:
            dx, dy = x - cx, y - cy
            r = _m.hypot(dx, dy) or 1
            out.append((x + dx / r * 2.5, y + dy / r * 2.5))
        o.append(f'<path d="{_dd(out + [out[0]], tol=.1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(extra)
    return _C.svg_doc(w, h, "".join(o))


def box_fit(w, h, aspect, maxw=None, pad=2.):
    """centre a device of width/height `aspect` in the w x h box; returns (cx, cy, a, b) half-axes"""
    W, H = w - 2 * pad, h - 2 * pad
    if maxw:
        W = min(W, maxw)
    if W / H > aspect:
        W = H * aspect
    else:
        H = W / aspect
    return w / 2, h / 2, W / 2, H / 2


# ==== VIGNETTE KIT END ====


_n, _d, PI, TAU = C._n, C._d, C.PI, C.TAU
hatch = C.hatch_poly


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circ(cx, cy, r, n=28, bump=0., k=9, ph=0.):
    return [(cx + r * (1 + bump * math.sin(k * t + ph)) * math.cos(t),
             cy + r * (1 + bump * math.sin(k * t + ph)) * math.sin(t))
            for t in [TAU * i / n for i in range(n)]]


def hz(poly, pitch=2.):
    """horizontal hatch on the device grid"""
    return hatch(poly, 0, pitch, .25)


def vt(poly, pitch=2.):
    return hatch(poly, 90, pitch, .25)


def solid(cv, poly, outline=1.):
    cv.obj([poly], outline)
    cv.line(hatch(poly, 0, .8))


def _seg_circle(a, b, cx, cy, r):
    dx, dy = b[0] - a[0], b[1] - a[1]
    fx, fy = a[0] - cx, a[1] - cy
    A = dx * dx + dy * dy
    B = 2 * (fx * dx + fy * dy)
    Cc = fx * fx + fy * fy - r * r
    disc = B * B - 4 * A * Cc
    if A < 1e-9 or disc <= 0:
        return None
    s = math.sqrt(disc)
    return (-B - s) / (2 * A), (-B + s) / (2 * A), dx, dy


def _cut(segs, cx, cy, r):
    """remove the parts of 2-point segments inside circle (cx, cy, r)"""
    out = []
    for (a, b) in segs:
        q = _seg_circle(a, b, cx, cy, r)
        if q is None:
            out.append([a, b])
            continue
        t0, t1, dx, dy = q
        if t0 > 0:
            t = min(1, t0)
            out.append([a, (a[0] + dx * t, a[1] + dy * t)])
        if t1 < 1:
            t = max(0, t1)
            out.append([(a[0] + dx * t, a[1] + dy * t), b])
    return [p for p in out if math.hypot(p[1][0] - p[0][0], p[1][1] - p[0][1]) > .6]


def _keep_in(segs, cx, cy, r):
    """keep only the parts of segments inside circle"""
    out = []
    for (a, b) in segs:
        q = _seg_circle(a, b, cx, cy, r)
        if q is None:
            continue
        t0, t1, dx, dy = q
        t0, t1 = max(0, t0), min(1, t1)
        if t1 - t0 > 1e-3:
            out.append([(a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)])
    return out


# ----------------------------------------------------------------------------------------------
# stroke lettering (roman capitals as paths; no <text>)
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_G = {
    "A": (.72, [[(0, 1), (.36, 0), (.72, 1)], [(.15, .64), (.57, .64)]]),
    "B": (.6, [[(0, 0), (0, 1), (.38, 1)] + _arc(.38, .76, .22, .24, 90, -90, 6) + [(0, .52)],
               [(0, 0), (.33, 0)] + _arc(.33, .26, .2, .26, -90, 90, 6)[1:] + [(0, .52)]]),
    "C": (.66, [_arc(.36, .5, .34, .5, -45, -315, 12)]),
    "D": (.68, [[(0, 0), (0, 1), (.3, 1)] + _arc(.3, .5, .36, .5, 90, -90, 10) + [(0, 0)]]),
    "E": (.56, [[(.54, 0), (0, 0), (0, 1), (.54, 1)], [(0, .5), (.42, .5)]]),
    "F": (.54, [[(.54, 0), (0, 0), (0, 1)], [(0, .5), (.42, .5)]]),
    "G": (.7, [_arc(.36, .5, .34, .5, -45, -315, 12) + [(.7, .58), (.42, .58)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    "I": (.08, [[(.04, 0), (.04, 1)]]),
    "J": (.46, [[(.44, 0), (.44, .74)] + _arc(.22, .74, .22, .26, 0, 180, 6)[1:]]),
    "K": (.62, [[(0, 0), (0, 1)], [(.6, 0), (0, .6)], [(.2, .45), (.62, 1)]]),
    "L": (.52, [[(0, 0), (0, 1), (.52, 1)]]),
    "M": (.84, [[(0, 1), (0, 0), (.42, .8), (.84, 0), (.84, 1)]]),
    "N": (.68, [[(0, 1), (0, 0), (.68, 1), (.68, 0)]]),
    "O": (.76, [_arc(.38, .5, .38, .5, 0, 360, 16)]),
    "P": (.58, [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)]]),
    "Q": (.76, [_arc(.38, .5, .38, .5, 0, 360, 16), [(.45, .7), (.78, 1.04)]]),
    "R": (.62, [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)],
                [(.28, .54), (.62, 1)]]),
    "S": (.56, [_arc(.28, .25, .26, .25, -20, -270, 7) + _arc(.28, .75, .28, .25, -90, 160, 7)[1:]]),
    "T": (.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "U": (.66, [[(0, 0), (0, .66)] + _arc(.33, .66, .33, .34, 180, 0, 8)[1:] + [(.66, 0)]]),
    "V": (.7, [[(0, 0), (.35, 1), (.7, 0)]]),
    "W": (.96, [[(0, 0), (.24, 1), (.48, .2), (.72, 1), (.96, 0)]]),
    "X": (.64, [[(0, 0), (.64, 1)], [(.64, 0), (0, 1)]]),
    "Y": (.66, [[(0, 0), (.33, .5), (.66, 0)], [(.33, .5), (.33, 1)]]),
    "Z": (.6, [[(0, 0), (.6, 0), (0, 1), (.6, 1)]]),
    "0": (.54, [_arc(.27, .5, .27, .5, 0, 360, 14)]),
    "1": (.36, [[(.04, .2), (.26, 0), (.26, 1)], [(.04, 1), (.48, 1)]]),
    "2": (.54, [_arc(.27, .27, .26, .27, -170, 10, 6) + [(0, 1), (.54, 1)]]),
    "3": (.52, [_arc(.25, .25, .25, .25, -160, 90, 6), _arc(.25, .74, .27, .26, -90, 160, 6)]),
    "4": (.58, [[(.42, 1), (.42, 0), (0, .7), (.58, .7)]]),
    "5": (.54, [[(.5, 0), (.08, 0), (.04, .44)] + _arc(.26, .7, .28, .3, -120, 150, 8)]),
    "6": (.56, [[(.46, .02), (.2, .2), (.02, .65)] + _arc(.28, .7, .26, .3, 180, 540, 12)]),
    "7": (.54, [[(0, 0), (.54, 0), (.2, 1)]]),
    "8": (.54, [_arc(.27, .25, .22, .25, 90, 450, 10), _arc(.27, .74, .27, .26, -90, 270, 12)]),
    "9": (.56, [_arc(.28, .3, .26, .3, 0, 360, 12) + [(.54, .35), (.36, .8), (.1, .98)]]),
    "-": (.4, [[(.04, .55), (.36, .55)]]),
    ".": (.2, [[(.1, .92), (.1, .96)]]),
    "·": (.36, [[(.18, .4), (.26, .51), (.18, .62), (.1, .51), (.18, .4), (.18, .62)]]),
}


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def tree(cv, cx, cy, r, seed):
    rng = random.Random(seed)
    blobs = []
    for i in range(5):
        a = rng.uniform(0, TAU)
        d = r * rng.uniform(.15, .45)
        blobs.append((cx + d * math.cos(a), cy + d * math.sin(a) * .8, r * rng.uniform(.5, .66)))
    blobs.sort(key=lambda b: b[1])
    tr = rect(cx - r * .08, cy, cx + r * .08, cy + r * 1.1)
    cv.obj([tr], 1.)
    cv.hair(vt(tr, 1.5))
    for bx, by, br in blobs:
        poly = circ(bx, by, br, 30, .07, 11, rng.uniform(0, 6))
        cv.obj([poly], 1.)
        cv.hair(_cut(hatch(poly, 45, 3., 0), bx - br * .35, by - br * .35, br * .45))
        cv.hair(_cut(hatch(poly, 45, 3., 1.5), bx - br * .25, by - br * .25, br * .95))
        cv.hair(_cut(hatch(poly, -45, 3., .75), bx - br * .15, by - br * .15, br * .98))
        for j in range(7):
            t = PI + .3 + j * .35
            px, py = bx + br * .78 * math.cos(t), by + br * .78 * math.sin(t)
            cv.hair([(px, py), (px + br * .14 * math.cos(t + 1.9), py + br * .14 * math.sin(t + 1.9))])


def capitol(cv, cx, G, S, detail):
    """Oregon State Capitol on ground line G, wing span S."""
    wh = .13 * S
    for side in (-1, 1):
        x0, x1 = (cx - S / 2, cx - .16 * S) if side < 0 else (cx + .16 * S, cx + S / 2)
        face = rect(x0, G - wh, x1, G)
        cv.obj([face], 1.)
        cv.hair(hz(face, 3.))
        if side > 0:
            ret = rect(x1 - .03 * S, G - wh, x1, G)
            cv.obj([ret], 1.)
            cv.hair(hz(ret, 1.5))
        n = max(3, int((x1 - x0) / (S * .035)))
        for row in (.3, .68):
            for i in range(n):
                wx = x0 + (x1 - x0) * (i + .5) / n
                if side > 0 and wx > x1 - .035 * S:
                    continue
                cv.heavy([(wx, G - wh * (row + .14)), (wx, G - wh * (row - .14))])
        cv.line([(x0, G - wh + 1.2), (x1, G - wh + 1.2)])
    bw, bh = .36 * S, .27 * S
    bx0, bx1, by0 = cx - bw / 2, cx + bw / 2, G - bh
    blk = rect(bx0, by0, bx1, G)
    cv.obj([blk], 1.)
    cv.hair(hz(rect(bx0, by0, bx1, by0 + bh * .14), 1.5))
    rec = rect(cx - bw * .3, by0 + bh * .18, cx + bw * .3, G)
    cv.obj([rec], 1.)
    cv.hair(vt(rec, 1.5))
    if detail:
        cv.hair(hz(rec, 3.))
    for i in range(5):
        px = cx - bw * .3 + bw * .6 * (i + .5) / 5
        cv.obj([rect(px - .8, by0 + bh * .18, px + .8, G)], .5)
    pl = rect(bx0, by0 + bh * .14, cx - bw * .3, G)
    pr = rect(cx + bw * .3, by0 + bh * .14, bx1, G)
    cv.obj([pl], 1.)
    cv.hair(vt(pl, 3.))
    cv.obj([pr], 1.)
    cv.hair(vt(pr, 1.5))
    cv.heavy([(bx0 - 1, by0), (bx1 + 1, by0)])
    r = .085 * S
    dh = .2 * S
    dy0, dy1 = by0 - dh, by0 - S * .025
    base = rect(cx - r * 1.35, dy1, cx + r * 1.35, by0)
    cv.obj([base], 1.)
    cv.hair(hz(base, 3.))
    cv.hair(_keep_in(hz(base, 1.5), cx + r * 2.6, by0, r * 2))
    drum = rect(cx - r, dy0, cx + r, dy1)
    cv.obj([drum], 1.)
    nf = 22 if detail else 12
    for i in range(1, nf):
        th = -PI / 2 + PI * i / nf
        fx = cx + r * math.sin(th)
        (cv.line if math.sin(th) > .35 else cv.hair)([(fx, dy0 + 2), (fx, dy1)])
    cv.hair(hz(rect(cx + r * .45, dy0, cx + r, dy1), 2.))
    ring = rect(cx - r * 1.1, dy0 - S * .018, cx + r * 1.1, dy0 + 1)
    cv.obj([ring], 1.)
    cv.hair(_keep_in(hz(ring, 1.5), cx + r * 1.7, dy0, r * 1.2))
    lan = rect(cx - r * .55, dy0 - S * .05, cx + r * .55, dy0 - S * .018)
    cv.obj([lan], 1.)
    cv.hair(vt(lan, 2.))
    cv.obj([rect(cx - r * .22, dy0 - S * .065, cx + r * .22, dy0 - S * .05)], 1.)
    # the gilded Pioneer: axe on his shoulder, cloak
    u = S * .0019
    top = dy0 - S * .065
    fig = [(-6, 0), (-5, -14), (-7, -30), (-6, -46), (-9, -60), (-6, -76), (0, -82), (6, -76), (9, -60),
           (8, -46), (6, -30), (5, -14), (7, 0), (2, 0), (1, -28), (-1, -28), (-2, 0)]
    solid(cv, [(cx + px * u * 1.2, top + py * u) for px, py in fig], .5)
    solid(cv, circ(cx, top - 88 * u, 6.5 * u, 12), .5)
    cv.line([(cx - 4 * u, top - 66 * u), (cx - 20 * u, top - 104 * u)])
    solid(cv, [(cx - 20 * u, top - 104 * u), (cx - 27 * u, top - 99 * u), (cx - 22 * u, top - 93 * u)], .5)
    # steps
    sw = bw * .7
    for k in range(4 if detail else 2):
        yy = G + k * S * .012
        st = rect(cx - sw / 2 - k * S * .02, yy, cx + sw / 2 + k * S * .02, yy + S * .012)
        cv.obj([st], .5)
        if k % 2:
            cv.hair(hz(st, 3.))
    # the two marble pylon sculptures
    for side in (-1, 1):
        sx = cx + side * (sw / 2 + S * .04)
        blkp = rect(sx - S * .03, G - S * .055, sx + S * .03, G + S * .02)
        cv.obj([blkp], 1.)
        cv.hair(hatch(blkp, 45 if side > 0 else 90, 2. if side > 0 else 3., .25))
        cv.obj([rect(sx - S * .034, G - S * .062, sx + S * .034, G - S * .055)], 1.)


def flag(cv, x, y, fw, fh, phase=0.):
    pole_h = fh * 4.2
    cv.obj([rect(x - .7, y, x + .7, y + pole_h)], .5)
    cv.obj([circ(x, y - .6, 1.6, 8)], .5)

    def P(u, v):
        return (x + 1 + u * fw, y + 2 + v * fh + fh * .09 * math.sin(u * 5.2 + phase) * u)
    N = 14
    cv.obj([[P(i / N, 0) for i in range(N + 1)] + [P(1 - i / N, 1) for i in range(N + 1)]], 1.)
    for s in range(0, 7, 2):
        for q in (.25, .7):
            v = (s + q) / 7 + .02
            u0 = .42 if s < 4 else 0
            cv.line([P(u0 + (1 - u0) * i / N, v) for i in range(N + 1)])
    can = [P(i / 6 * .42, 0) for i in range(7)] + [P(.42 - i / 6 * .42, 4 / 7) for i in range(7)]
    cv.obj([can], .5)
    cv.hair(hatch(can, 45, 1.5))
    cv.hair(hatch(can, -45, 3.))


def drop_box(cv, x, y, s, egg=True):
    """county ballot drop box standing at (x, y), height s; a ballot half posted, its X made of
    crossed drumsticks."""
    w = s * .62
    for lg in (rect(x - w * .38, y - s * .1, x - w * .3, y), rect(x + w * .3, y - s * .1, x + w * .38, y)):
        solid(cv, lg, .5)
    body = rect(x - w / 2, y - s * .92, x + w / 2, y - s * .1)
    cv.obj([body], 1.)
    cv.hair(hatch(body, 45, 2.))
    cv.hair(_keep_in(hatch(body, -45, 3.), x + w, y - s * .5, w * .9))
    lid = [(x - w / 2 - 1.5, y - s * .92), (x + w / 2 + 1.5, y - s * .92), (x + w / 2 - 1, y - s), (x - w / 2 + 1, y - s)]
    cv.obj([lid], 1.)
    cv.hair(hz(lid, 1.5))
    pc = rect(x - w * .3, y - s * .6, x + w * .3, y - s * .3)
    cv.obj([pc], .5)
    for k in range(3):
        yy = y - s * .55 + k * s * .09
        cv.hair([(x - w * .22, yy), (x + w * .22, yy)])
    solid(cv, rect(x - w * .34, y - s * .84, x + w * .34, y - s * .78), .5)
    if egg:
        a = math.radians(-8)
        bw_, bh_ = w * .62, s * .5
        ox, oy = x - w * .02, y - s * .81

        def R(px, py):
            return (ox + px * math.cos(a) - py * math.sin(a), oy + px * math.sin(a) + py * math.cos(a))
        cv.obj([[R(-bw_ / 2, 0), R(bw_ / 2, 0), R(bw_ / 2, -bh_), R(-bw_ / 2, -bh_)]], 1.)
        cv.hair([R(-bw_ * .38, -bh_ * .82), R(bw_ * .38, -bh_ * .82)])
        cv.hair([R(-bw_ * .38, -bh_ * .7), R(bw_ * .1, -bh_ * .7)])
        for sx in (-1, 1):
            p0 = R(-bw_ * .05 - sx * bw_ * .3, -bh_ * .1)
            p1 = R(-bw_ * .05 + sx * bw_ * .22, -bh_ * .58)
            cv.line([p0, p1])
            solid(cv, circ(p1[0], p1[1], .9, 6), .5)


def heron(cx_, by, k, f, seed=0):
    """A great blue heron's neck rising out of the acanthus like a scroll stem, ending in the head:
    black crest plumes, eye, dagger bill; streaked throat in bulino. f = -1 faces left, +1 right.
    Base at (cx_, by); k = scale (1 ~ 60 px tall)."""
    cv = C.Canvas()

    def bez(p0, p1, p2, p3, n=24):
        out = []
        for i in range(n + 1):
            t = i / n
            a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
            out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
        return out
    P = lambda x, y: (cx_ + f * x * k, by + y * k)
    pts = bez(P(0, 0), P(26, -6), P(-6, -40), P(14, -56))
    n = len(pts)
    wl = [k * (7.5 - 4.2 * i / (n - 1)) for i in range(n)]
    R = C._Rib(pts, wl, wl)
    cv.obj([R.outline()], 1.)
    side = 1 if f > 0 else -1     # the throat (front) edge
    cv.hair(C._fill_lines(R, -side * .98, side * .2, 2., 0., 1., 4))
    cv.hair(C._fill_lines(R, side * .35, side * .98, 3., 0., 1., 2))
    C._shadow(cv, R, -side, k * 2.2, .05, .9)
    # streaked throat: short bulino flecks down the front of the neck
    for i in range(2, n - 2):
        a = R.at(i / (n - 1), side * .7)
        b = R.at((i + 1.6) / (n - 1), side * .3)
        (cv.line if i % 2 else cv.hair)([a, b])
    # head
    hx, hy = P(17, -58)
    head = [(hx + 6.2 * k * math.cos(t), hy + 4.4 * k * math.sin(t)) for t in [TAU * i / 20 for i in range(20)]]
    # bill
    bill = [P(19, -61), P(42, -55), P(19, -55.5)]
    cv.obj([bill], 1.)
    cv.hair([P(21, -58), P(40, -55.3)])
    cv.obj([head], 1.)
    cv.hair(_keep_in(hatch(head, 0, 1.5, .25), hx - f * 4 * k, hy + 5 * k, 5 * k))
    # black crown stripe and the trailing plumes
    crown = [P(10, -60), P(16, -63.2), P(22, -61.5), P(16, -60.5)]
    solid(cv, crown, .5)
    for dy, L in ((0, 16), (2, 13)):
        cv.heavy(bez(P(12, -61 + dy), P(4, -62 + dy), P(-2, -64 + dy), P(-2 - L * .3, -68 + dy * .5), 8))
    # eye
    ex, ey = P(19.5, -59.5)
    cv.obj([circ(ex, ey, 1.3 * k, 8)], .5)
    cv.line(hatch(circ(ex, ey, .8 * k, 6), 0, .8))
    # one finger of acanthus wrapping the base of the neck, so it grows from the leafwork
    C.acanthus_frond(*P(0, 4), -90 + f * 60, 26 * k, 3, 34, seed=seed, cv=cv)
    return cv.svg()


def scene(x, y, W, H, clip_d, seed, detail=True, uid="cv"):
    """everything inside the cartouche field (bbox x, y, W, H; clipped to clip_d)"""
    cv = C.Canvas()
    cx = x + W / 2
    G = y + H * (.7 if detail else .76)
    S = min(W * .9, (G - y - H * .07) / .74)
    # sky: a glory of rays from behind the drum, alternate wedges ruled
    sky = rect(x - 2, y - 2, x + W + 2, G + 1)
    cv.obj([sky], 0)
    gx, gy = cx, G - .4 * S
    nr = 40 if detail else 24
    R = max(W, H) * 1.6
    for i in range(nr):
        a0 = PI * i / nr - .01 - PI
        a1 = PI * (i + 1) / nr + .01 - PI
        aa = (a0 + a1) / 2
        rr0 = S * .16
        if i % 2:
            # a lit ray: burin lines fanning out of the glory, swelling as they leave the drum
            for f in (.28, .5, .72):
                at = a0 + (a1 - a0) * f
                cv.hair([(gx + rr0 * 1.3 * math.cos(at), gy + rr0 * 1.3 * math.sin(at)),
                         (gx + R * math.cos(at), gy + R * math.sin(at))])
        else:
            cv.line([(gx + rr0 * math.cos(aa), gy + rr0 * math.sin(aa)), (gx + R * math.cos(aa), gy + R * math.sin(aa))])
    # a band of cloud low on the horizon, lit from above
    rng_ = random.Random(seed)
    for k in range(5):
        ccx = x + W * (k + .5) / 5 + rng_.uniform(-6, 6)
        ccy = gy - S * .02 + rng_.uniform(-3, 3)
        cw_, ch_ = W * .14, S * .045
        cl = [(ccx + cw_ * math.cos(t) * (1 + .15 * math.sin(5 * t)), ccy - ch_ * abs(math.sin(t)) ** .7 * (1 + .25 * math.sin(7 * t + k)))
              for t in [PI * j / 18 for j in range(19)]]
        cv.obj([cl], .5)
        # the puff modelled in contour lines that echo its crown, closing up toward the shaded base
        for q in (.25, .45, .62, .76, .88):
            cv.hair([(ccx + (px_ - ccx) * (1 - .35 * q), ccy - (ccy - py_) * (1 - q)) for px_, py_ in cl[2:-2]])
    # stratus wisps between the cloud band and the far range: tapering strokes broken into drifts
    rw_ = random.Random(seed + 11)
    yy_ = gy - S * .01
    while yy_ < gy + S * .09:
        xx_ = x + rw_.uniform(-4, 4)
        while xx_ < x + W:
            L_ = rw_.uniform(10, 30)
            cv.hair([(xx_, yy_), (xx_ + L_ * .5, yy_ - .4), (xx_ + L_, yy_)])
            xx_ += L_ + rw_.uniform(2, 6)
        yy_ += 2.5
    # the far Cascades on the horizon under the glory, then the West Hills in fir
    far = [(x - 2, G + 1)] + [(x - 2 + (W + 4) * i / 40,
                               gy + S * .02 + S * .05 * abs(math.sin(i * .9 + seed % 5)) * (1 - .5 * math.sin(i * .37)))
                              for i in range(41)] + [(x + W + 2, G + 1)]
    cv.obj([far], .5)
    # the distant range: ridges and gullies cut in short slanting strokes, thinning with distance
    rr_ = random.Random(seed + 3)
    yy_ = gy + S * .07
    while yy_ < G - 2:
        xx_ = x + rr_.uniform(0, 4)
        while xx_ < x + W:
            L_ = rr_.uniform(2.5, 5.)
            cv.hair([(xx_, yy_), (xx_ + L_ * .7, yy_ + L_ * .35)])
            xx_ += rr_.uniform(5, 9)
        yy_ += 3.
    hills = [(x - 2, G + 1)] + [(x - 2 + (W + 4) * i / 30,
                                 G - H * (.06 + .025 * math.sin(i * .7 + seed % 7) + .015 * math.sin(i * 1.9)))
                                for i in range(31)] + [(x + W + 2, G + 1)]
    cv.obj([hills], .5)
    for i in range(int(W / 3.2)):
        fx_ = x + i * 3.2 + (i * 7 % 3) * .5
        top_ = G - H * (.06 + .025 * math.sin((fx_ - x + 2) / (W + 4) * 30 * .7 + seed % 7)) + 1.5
        ht_ = 3.5 + (i * 5 % 4)
        cv.hair([(fx_ - ht_ * .3, top_ + ht_), (fx_, top_), (fx_ + ht_ * .3, top_ + ht_)])
    cv.hair(hatch(hills, 45, 3.))
    # the mall
    lawn = rect(x - 2, G, x + W + 2, y + H + 2)
    cv.obj([lawn], 0)
    # mown stripes receding to the Capitol steps, and grass flicked in along each stripe's edge
    vx_, vy_ = cx, G - S * .3
    for j in range(-14, 15):
        bx_ = cx + j * W * .09
        t0 = (G - vy_) / (y + H + 2 - vy_)
        cv.hair([(vx_ + (bx_ - vx_) * t0, G), (bx_, y + H + 2)])
    yy = G + 2
    k = 0
    while yy < y + H:
        f = (yy - G) / max(1., H * .3)
        step = 2. + 2.5 * f
        xx = x + (k % 2) * step * .5
        while xx < x + W:
            cv.hair([(xx, yy), (xx + .6 + f, yy - 1.2 - f * 1.5)])
            xx += step * 2.2
        yy += step
        k += 1
    walk = [(cx - S * .13, G), (cx + S * .13, G), (cx + W * .33, y + H + 2), (cx - W * .33, y + H + 2)]
    cv.obj([walk], .5)
    cv.hair(hz(walk, 3.))
    for k in (-1, 1):
        for f in (.3, .65):
            cv.hair([(cx + k * S * .13 * f, G), (cx + k * W * .33 * f, y + H + 2)])
    if detail:
        flag(cv, cx - S * .33, G - S * .36, S * .15, S * .085, seed % 5)
    capitol(cv, cx, G, S, detail)
    tr = S * .1
    for side in (-1, 1):
        for k, (fx, fy, sc) in enumerate(((.62, .0, 1.), (.78, .08, 1.3), (.92, .2, 1.7))):
            if not detail and k == 0:
                continue
            tree(cv, cx + side * W * fx * .5, G + H * fy - tr * sc * .3, tr * sc, seed * 7 + k * 3 + side)
    if S * .2 >= 13:
        drop_box(cv, cx + W * .27, min(y + H * .95, G + (y + H - G) * .8), max(S * .2, 16))
    cid = C._uid("civ", uid, x, y, W, H)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ----------------------------------------------------------------------------------------------
# layouts (the house layouts, adapted: the field engraved whole, banner and tablet lettered)
# ----------------------------------------------------------------------------------------------


def _shade(cv, poly, cxs, cys, r, ang=45., pitch=1.5, cross=False):
    """model a cast form in burin tone: lit from the upper left, the lines swelling into the shadow
    side and crossed where it is deepest"""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    a_, b_ = max(1., (max(xs) - min(xs)) / 2), max(1., (max(ys) - min(ys)) / 2)
    tone_hatch(cv, poly, lit(mx, my, a_, b_ * 1.6, .04, .95), ang, 1.5, .62 if cross else None)


def pioneer(cv, cx, fy, hs):
    """The gilded Oregon Pioneer, feet on (cx, fy), hs tall: bearded, bareheaded, the axe over his
    shoulder and the blanket-cloak hanging from it; lit from the left, the right side worked in
    swelling hatches that close up into the shadow."""
    u = hs / 99.

    def Y(py):
        # long legs (half his height), a smaller head: eight heads tall
        if py > -38:
            return py * 46 / 38
        if py > -68:
            return py - 8
        return -76 + (py + 68) * .82

    def P(pts, soft=False):
        q = [(cx + px * u * (.9 if py < -68 else 1.), fy + Y(py) * u) for px, py in pts]
        for _ in range(2 if soft else 0):
            # Chaikin: the cast form, not a cut-out
            q = [pt for i in range(len(q)) for pt in
                 (((3 * q[i][0] + q[(i + 1) % len(q)][0]) / 4, (3 * q[i][1] + q[(i + 1) % len(q)][1]) / 4),
                  ((q[i][0] + 3 * q[(i + 1) % len(q)][0]) / 4, (q[i][1] + 3 * q[(i + 1) % len(q)][1]) / 4))]
        return q
    # the cloak behind, hanging from the left shoulder down to the knee, in heavy folds
    cloak = P([(-10, -66), (-17, -61), (-22, -40), (-23, -14), (-18, -9), (-14, -12), (-11, -30)], True)
    cv.obj([cloak], 1.)
    for i in range(5):
        t = i / 4
        cv.hair(P([(-12 - 9 * t, -60 + 4 * t), (-14 - 8 * t, -40), (-15 - 7 * t, -14 + 2 * t)]))
    _shade(cv, cloak, cx - 8 * u, fy + Y(-30) * u, 13 * u, 60, 1.5)
    # legs in buckskin leggings and boots
    for sd in (-1, 1):
        leg = P([(sd * 2, -38), (sd * 10, -38), (sd * 9, -6), (sd * 10.5, 0), (sd * 2.5, 0), (sd * 3, -6)], True)
        cv.obj([leg], 1.)
        boot = P([(sd * 2.5, -9), (sd * 9.3, -9), (sd * 11, 0), (sd * 2.5, 0)])
        cv.obj([boot], 1.)
        if sd > 0:
            _shade(cv, leg, cx + 10 * u, fy + Y(-20) * u, 8 * u, 45, 1.5, True)
        else:
            cv.hair(P([(-8, -36), (-8.5, -12)]))
        cv.hair(_keep_in(hatch(boot, 0, 1.5), cx + sd * 9 * u, fy + Y(-4) * u, 6 * u))
        for j in range(6):   # fringe down the outer seam
            yy = -36 + j * 4.5
            cv.hair(P([(sd * (10 - j * .15), yy), (sd * (12 - j * .15), yy + 2)]))
    # the tunic, belted, with a fringed hem
    tun = P([(-12, -66), (12, -66), (13.5, -40), (12, -30), (-12, -30), (-13.5, -40)], True)
    cv.obj([tun], 1.)
    _shade(cv, tun, cx + 15 * u, fy + Y(-48) * u, 14 * u, 50, 1.5, True)
    cv.line(P([(-13.5, -42), (13.5, -42)]))
    cv.line(P([(-13.3, -40), (13.3, -40)]))
    cv.obj([P([(-2, -43), (2, -43), (2, -39), (-2, -39)])], .5)
    for j in range(13):
        xx = -11.5 + j * 1.9
        cv.hair(P([(xx, -30), (xx + .3, -26.5)]))
    cv.hair(P([(0, -64), (0, -44)]))
    for j in range(4):
        cv.hair(P([(-1.5, -61 + j * 4), (1.5, -61 + j * 4)]))
    # the right arm hanging, hand by the thigh
    arm = P([(10.5, -65), (15.5, -62), (17.5, -46), (17, -36), (13, -34), (12.5, -44), (11.5, -55)], True)
    cv.obj([arm], 1.)
    _shade(cv, arm, cx + 18 * u, fy + Y(-50) * u, 7 * u, 40, 1.5, True)
    cv.obj([P([(13, -36), (17, -36.5), (17, -31.5), (14.5, -30), (12.6, -32)])], .5)
    # the axe: helve from the left hand over the shoulder, the bit behind the head
    cv.obj([P([(-17.5, -46), (-15, -45), (-4.5, -95), (-7, -96)])], .5)
    cv.hair(P([(-16.2, -46), (-5.7, -95)]))
    bit = P([(-8.5, -92), (-3, -94), (2, -102), (3.5, -91), (-1, -88), (-7.2, -88)])
    cv.obj([bit], 1.)
    cv.hair(_keep_in(hatch(bit, 80, 1.5), cx - 1 * u, fy + Y(-90) * u, 4 * u))
    cv.line(P([(2, -102), (3.5, -91)]))
    # the left arm raised to grip the helve
    larm = P([(-10.5, -65), (-15.5, -62), (-18.5, -50), (-15.5, -46), (-13, -52), (-11, -58)], True)
    cv.obj([larm], 1.)
    cv.obj([P([(-18.8, -50), (-14.8, -49), (-14.6, -44.5), (-18.3, -44.5)])], .5)
    cv.hair(P([(-12, -62), (-16, -51)]))
    # neck, head, the full beard and the hair blown back
    cv.obj([P([(-3, -68), (3, -68), (3, -64), (-3, -64)])], .5)
    hair_ = P([(-6, -78), (-5, -84), (0, -86.5), (5, -84), (6.5, -78), (5.5, -74), (-5.5, -74)], True)
    cv.obj([hair_], 1.)
    for j in range(6):
        cv.hair(P([(-5 + j * 2, -85 + abs(j - 2.5) * .6), (-5.5 + j * 2.2, -78)]))
    face = P([(-4.6, -80), (4.6, -80), (4.8, -74), (3.5, -70), (0, -69), (-3.5, -70), (-4.8, -74)], True)
    cv.obj([face], 1.)
    cv.hair(_keep_in(hatch(face, 45, 1.5), cx + 4.5 * u, fy + Y(-76) * u, 3.4 * u))
    cv.hair(P([(-3, -77), (-1, -77.4)]))
    cv.hair(P([(1, -77.4), (3, -77)]))
    cv.hair(P([(0, -77), (-.6, -74.5), (.6, -74.3)]))
    beard = P([(-4.8, -74), (-3, -71.5), (0, -72), (3, -71.5), (4.8, -74), (4.2, -68), (1.5, -63.5), (0, -62.5), (-1.5, -63.5),
               (-4.2, -68)], True)
    cv.obj([beard], 1.)
    for j in range(7):
        xx = -3.6 + j * 1.2
        cv.hair(P([(xx, -71.5), (xx * .7, -64.5)]))


def pioneer_scene(x, y, W, H, seed, detail=True):
    """the arched front's field: the gilded Pioneer on the Capitol lantern, in a glory, over a sea of
    cloud with the Cascades standing out of it"""
    cv = C.Canvas()
    cx = x + W / 2
    sky = rect(x - 2, y - 2, x + W + 2, y + H + 2)
    cv.obj([sky], 0)
    ly = y + H * .8                     # top of the lantern cornice, where he stands
    hs = (ly - y) * .86
    gx, gy = cx, ly - hs * .55
    nr = 44 if detail else 28
    R = max(W, H) * 1.5
    R0 = max(W, H) * .62

    def sky_t(px, py):
        # light breaking from behind him into a dark sky: alternate wedges of the glory held light
        r = math.hypot(px - gx, py - gy) / R0
        wedge = int((math.atan2(py - gy, px - gx) + PI) / TAU * nr) % 2
        return .1 + .95 * min(1., r) ** 1.3 - (.38 if wedge else 0.) * min(1., r * 1.6)
    tone_hatch(cv, sky, sky_t, 0., 1.5, .78, 90.)
    # the sea of cloud at his feet, its billows modelled in contour lines; the Cascades stand out of it
    rng = random.Random(seed)
    hz_ = ly - H * .1
    for pk, (fx_, hh_, ww_) in enumerate(((.13, .17, .2), (.87, .11, .15), (.66, .06, .1))):
        px_ = x + W * fx_
        top_ = hz_ - H * hh_
        mt = [(px_ - W * ww_, hz_ + 4), (px_ - W * ww_ * .3, top_ + H * hh_ * .45), (px_ - W * .012, top_ + 1),
              (px_ + W * .012, top_), (px_ + W * ww_ * .35, top_ + H * hh_ * .5), (px_ + W * ww_, hz_ + 4)]
        cv.obj([mt], .5)
        cv.hair(_keep_in(hatch(mt, 50, 1.5), px_ + W * ww_ * .45, hz_, W * ww_ * .75))
        for q in range(4):
            yy = top_ + H * hh_ * (.25 + q * .16)
            cv.hair([(px_ - W * .012 - (yy - top_) * .5, yy), (px_ - W * .03 - (yy - top_) * .2, yy + 2)])
    by_ = hz_
    row = 0
    while by_ < y + H + 4:
        xx = x - 6 - (row % 2) * 9
        while xx < x + W + 6:
            bw = rng.uniform(12, 30) * (1 + row * .2)
            bh = bw * rng.uniform(.22, .36)
            nb = rng.randint(2, 4)
            bumps = [(rng.uniform(.15, .85), rng.uniform(.5, 1.), rng.uniform(.12, .25)) for _ in range(nb)]
            cl = []
            for j in range(19):
                t = j / 18
                hv = max(bv * math.sqrt(max(0., 1 - ((t - bc) / bs) ** 2)) for bc, bv, bs in bumps)
                hv = max(hv, math.sin(PI * t) * .45)
                cl.append((xx + bw * t, by_ - bh * hv))
            cv.obj([cl + [(xx, by_ + 3), (xx + bw, by_ + 3)][::-1]], .5)
            for q in (.45, .75):
                cv.hair([(xx + bw / 2 + (px - xx - bw / 2) * (1 - .3 * q), by_ - (by_ - py) * (1 - q) + q * 1.5)
                         for px, py in cl[3:-3]])
            xx += bw * rng.uniform(.6, .95)
        by_ += 5 + row * 2.5 + rng.uniform(0, 2)
        row += 1
    # the lantern: fluted, a cornice and a ring of cresting under his feet
    lw = W * .3
    lan = rect(cx - lw / 2, ly, cx + lw / 2, y + H + 3)
    cv.obj([lan], 1.)
    n = 14
    for i in range(1, n):
        th = -PI / 2 + PI * i / n
        fx_ = cx + lw / 2 * math.sin(th)
        (cv.line if math.sin(th) > .4 else cv.hair)([(fx_, ly + 5), (fx_, y + H + 3)])
    cv.hair(_keep_in(hatch(lan, 0, 1.5), cx + lw * .62, y + H, lw * .4))
    cor = rect(cx - lw / 2 - 4, ly, cx + lw / 2 + 4, ly + 4.5)
    cv.obj([cor], 1.)
    cv.hair(hatch(rect(cx - lw / 2 - 4, ly + 2.5, cx + lw / 2 + 4, ly + 4.5), 0, 1.5))
    for i in range(int(lw / 4)):
        bx_ = cx - lw / 2 + 2 + i * 4
        cv.obj([[(bx_ - 1.2, ly), (bx_, ly - 2.4), (bx_ + 1.2, ly)]], .5)
    pioneer(cv, cx, ly - .5, hs)
    return cv.svg()

def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 17
    uid = f"cv{int(w)}x{int(h)}"
    tall = h > 260
    acs = min(34., max(22., h * .16))
    cx, cy, a, b = box_fit(w, h - acs * .45, 1.0 if tall else 1.5, pad=3)
    cy = 3 + b
    clean = shape_pts(cx, cy, a, b, "arch", 180)
    sil = ragged(clean, max(2.5, b * .05), seed, cut=lambda x, y: y < cy + b * .35)
    x0, y0 = cx - a, cy - b
    if tall:
        d = f"M{_n(x0)},{_n(y0)}h{_n(2 * a)}v{_n(2 * b)}h{_n(-2 * a)}z"
        body = scene(x0, y0, 2 * a, 2 * b, d, seed, True, "tall")
    else:
        body = pioneer_scene(x0, y0, 2 * a, 2 * b, seed, h > 110)
    # the ruled arch: a 1.5 px line and a fine outer line over the head of the arch, stopping where
    # the cloud breaks out at the foot
    top = [p for p in clean if p[1] < cy + b * .3]
    top.sort(key=lambda p: (_m.atan2(p[1] - cy, p[0] - cx) - _PI / 2) % _TAU)
    out = [(cx + (x - cx) * (1 + 2.5 / a), cy + (y - cy) * (1 + 2.5 / b)) for x, y in top]
    ex = (f'<path d="{_dd(top, tol=.1)}" fill="none" stroke="#000" stroke-width="1.5"/>'
          f'<path d="{_dd(out, tol=.1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    ex += arms_somaster(cx, h - acs / 2 - 1, acs, seed % 5)
    return vignette(w, h, uid, sil, body, None, ex)
