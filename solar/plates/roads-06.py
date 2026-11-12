"""roads-06 Earthquakes this week, merged into Hazards: fires and quakes (edition plan: small tailpiece, banner).

The tailpiece is a seismogram strip unrolling between two recording drums, standing free on a
transparent ground. The trace is the ridge: it climbs to a peak where a fire lookout stands on its
braced timber tower, the mountain under it worked in burin tone and the dawn sky over it in broken
strokes, with minute ticks along the strip's foot. Easter egg (the plan's): before the ridge the
trace swings, long-short, long-short, a bar of swing rhythm. At taller sizes Mount Rainier with the
strata cut away beneath it sits in a ruled oval over the strip."""
import sys
import math
import random
import datetime
import engraving_codex as C

# ==== VIGNETTE KIT BEGIN (batch 6) ====
# Shared by the batch-6 plates: a free-standing engraved vignette on a transparent ground (no
# black field, no generic scrollwork; the frame's engraved ground shows through). The scene is clipped to a shaped silhouette (oval, roundel,
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
    """assemble: the scene clipped to the silhouette (outside it the plate is transparent, so the
    frame's own engraved ground shows through and the vignette dissolves into it), a fine double
    rule round it if asked (rule = the clean silhouette), then any over-laid ornament"""
    o = []
    if sil:
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


_n = C._n


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _hscan(poly, y):
    """x-intervals of a closed polygon on the horizontal line y (even-odd)."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    xs.sort()
    return [(xs[j], xs[j + 1]) for j in range(0, len(xs) - 1, 2)]


def _inside(poly, x, y):
    return any(a <= x <= b for a, b in _hscan(poly, y))


def _keep(pl, pred):
    """Split a polyline into the runs whose points satisfy pred."""
    out, cur = [], []
    for p in pl:
        if pred(p):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _between(up, lo, t):
    return [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(up, lo)]


def _resample(pl, n):
    L = [0.]
    for i in range(1, len(pl)):
        L.append(L[-1] + math.hypot(pl[i][0] - pl[i - 1][0], pl[i][1] - pl[i - 1][1]))
    tot = L[-1] or 1.
    out, j = [], 0
    for k in range(n + 1):
        d = tot * k / n
        while j < len(pl) - 2 and L[j + 1] < d:
            j += 1
        seg = (L[j + 1] - L[j]) or 1.
        t = min(1., max(0., (d - L[j]) / seg))
        out.append((pl[j][0] + (pl[j + 1][0] - pl[j][0]) * t, pl[j][1] + (pl[j + 1][1] - pl[j][1]) * t))
    return out


def prof_at_x(prof, x):
    for i in range(len(prof) - 1):
        if prof[i][0] <= x <= prof[i + 1][0]:
            t = (x - prof[i][0]) / max(1e-6, prof[i + 1][0] - prof[i][0])
            return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * t
    return prof[-1][1]


def _moon_age(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .5
    return (days % 29.530588) / 29.530588      # 0 new, .5 full


def _seed(ctx):
    return sum(map(ord, (ctx or {}).get("date", "2026-11-11"))) * 7 + (ctx or {}).get("sheet", 0)


# ------------------------------------------------------------------------------------------------
# the vignette: Rainier over a cut-away section of the shaking earth
# ------------------------------------------------------------------------------------------------

def scene(field, ctx, detail=1.0, ground=True):
    """Fill the closed polygon `field` completely. detail ~ .4 (band medallion) .. 1 (tall)."""
    rng = random.Random(_seed(ctx))
    X0 = min(p[0] for p in field); X1 = max(p[0] for p in field)
    Y0 = min(p[1] for p in field); Y1 = max(p[1] for p in field)
    W, H = X1 - X0, Y1 - Y0
    cv = C.Canvas()

    y_base = Y0 + H * (.60 if ground else .80)        # foot of the mountain (hidden by hills)
    y_g = Y0 + H * (.66 if ground else .86)           # the ground surface / top of the section
    m_h = H * (.40 if ground else .52)
    m_x0, m_x1 = X0 - W * .12, X1 + W * .08
    sx = m_x0 + (m_x1 - m_x0) * .56                   # summit

    # ---- sky: ruled horizontal lines, close at the zenith, opening toward the horizon
    cv.obj([field], 0)
    y = Y0 + .75
    sky = []
    while y < y_g + 2:
        for a, b in _hscan(field, y):
            sky.append([(a, y), (b, y)])
        t = (y - Y0) / max(1., y_g - Y0)
        y += 2. if t < .9 else 3.
    cv.hair(sky)

    # ---- moon, phase by date (upper left)
    age = _moon_age((ctx or {}).get("date", ""))
    mr = max(4., H * .055)
    mx, my = X0 + W * .2, Y0 + H * .16 + mr * .6
    if _inside(field, mx - mr - 2, my) and _inside(field, mx, my - mr - 2):
        disc = C._ell_pts(mx, my, mr, mr, 40)[:-1]
        cv.obj([disc], .5)
        # the dark limb: a terminator ellipse, ruled close
        k = math.cos(age * 2 * math.pi)
        sg = 1 if age < .5 else -1           # waxing: dark on the left
        dark = []
        for i in range(41):
            v = -1 + 2 * i / 40
            dark.append((mx - sg * mr * math.sqrt(max(0, 1 - v * v)), my + mr * v))
        for i in range(41):
            v = 1 - 2 * i / 40
            dark.append((mx + sg * mr * k * math.sqrt(max(0, 1 - v * v)), my + mr * v))
        cv.hair(C.hatch_poly(dark, 0, 1.5, .3))
        for (u, v, rr) in ((-.3, -.2, .22), (.25, .3, .16), (.1, -.45, .12), (-.1, .45, .1)):
            cv.hair([C._ell_pts(mx + u * mr, my + v * mr, rr * mr, rr * mr, 10)])

    # ---- the mountain: Rainier's broad dome, Liberty Cap, Point Success, Little Tahoma
    prof = []
    NP = 90
    for i in range(NP + 1):
        u = i / NP
        d = (u - .5) / .5
        ad = abs(d)
        v = min(1., ((1 - ad) / .8) ** 1.7)
        if ad < .2:
            v = 1 - .05 * (d / .2) ** 2
        v += .045 * math.exp(-((d + .19) / .035) ** 2)            # Liberty Cap
        v += .07 * math.exp(-((d - .37) / .03) ** 2)              # Little Tahoma
        v += .012 * math.sin(u * 61 + 1.3) * (1 - ad) + rng.uniform(-.004, .004)
        prof.append((m_x0 + (m_x1 - m_x0) * u, y_base - m_h * max(0., v if 0 < i < NP else 0.)))
    peak = min(prof, key=lambda p: p[1])
    sx = (m_x0 + m_x1) / 2 + (m_x1 - m_x0) * .02
    peak = (sx, prof_at_x(prof, sx))

    def prof_at(x):
        for i in range(len(prof) - 1):
            if prof[i][0] <= x <= prof[i + 1][0]:
                t = (x - prof[i][0]) / max(1e-6, prof[i + 1][0] - prof[i][0])
                return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * t
        return y_base

    mountain = prof + [(m_x1, y_base + 4), (m_x0, y_base + 4)]

    # ---- lenticular cloud cap over the summit (Rainier's signature)
    if detail > .5:
        lw, lh = W * .36, max(4., H * .05)
        lx, ly = sx - W * .01, peak[1] - lh * 1.05
        for k2, (dx, dy, s) in enumerate(((W * .02, -lh * .95, .6), (0, 0, 1.0))):
            top = [(lx + dx + lw * s * (i / 30 - .5), ly + dy - lh * s * .55 * math.sin(math.pi * i / 30) ** .7) for i in range(31)]
            bot = [(lx + dx + lw * s * (.5 - i / 30), ly + dy + lh * s * .45 * math.sin(math.pi * (1 - i / 30)) ** .7) for i in range(31)]
            lens = top + bot[1:-1]
            cv.obj([lens], .5)
            for t in (.3, .6):
                cv.hair([_between(top, bot[::-1][1:] + [top[-1]], t)])
            cv.hair(C.hatch_poly([(p[0], ly + dy + .6) for p in top] + bot[1:-1], 0, 1.5))

    cv.obj([mountain], 1.)
    NR = 26
    ridge_spec = [(.30, .12), (.36, .22), (.42, .32), (.48, .42), (.54, .53), (.60, .64), (.66, .75), (.73, .86)]
    ridges = []
    for tu, bu in ridge_spec:
        tx = m_x0 + (m_x1 - m_x0) * tu
        ty = prof_at(tx) + 1.2
        bx = m_x0 + (m_x1 - m_x0) * bu
        pts = []
        for i in range(NR + 1):
            t = i / NR
            x = tx + (bx - tx) * (t ** .85)
            yy = ty + (y_base + 3 - ty) * t
            x += math.sin(t * 9 + tu * 23) * W * .005 * t
            pts.append((x, yy))
        ridges.append(pts)
    # the flanks' outer boundaries, resampled to the ridges' point count
    lf = _resample([p for p in prof if p[0] <= ridges[0][0][0]][::-1] + [(m_x0, y_base + 3)], NR)
    rf = _resample([p for p in prof if p[0] >= ridges[-1][0][0]] + [(m_x1, y_base + 3)], NR)
    bands = [(lf, ridges[0])] + [(ridges[i], ridges[i + 1]) for i in range(len(ridges) - 1)] + [(ridges[-1], rf)]
    hair, line = [], []
    for fi, (A, B) in enumerate(bands):
        shade = A[0][0] > sx + W * .01 or fi == len(bands) - 1
        poly = A + B[::-1]
        # flow lines down the glacier, laid coarse-to-fine so they never crowd at the summit
        pitch = 2.0 if shade else 4.0
        for d in range(1, 6):
            for k in range(1, 2 ** d, 2):
                f = k / 2 ** d
                pl = _between(A, B, f)
                keep = [p for j, p in enumerate(pl) if math.hypot(A[j][0] - B[j][0], A[j][1] - B[j][1]) / 2 ** d >= pitch]
                if len(keep) > 1:
                    hair.append(keep)
        if shade:
            if fi >= len(bands) - 4:
                hair += C.hatch_poly(poly, 32, 3, fi * .7)
            if fi >= len(bands) - 2:
                hair += C.hatch_poly(poly, -62, 3, fi * .4)
        elif detail > .55:
            # crevasses: short arcs across the flow, thickest where the ice steepens
            for j in range(3, NR - 4, 2):
                wj = math.hypot(A[j][0] - B[j][0], A[j][1] - B[j][1])
                if wj < 6:
                    continue
                for _ in range(1 + int(wj / 9)):
                    f0 = rng.uniform(.12, .75)
                    p0 = _between([A[j]], [B[j]], f0)[0]
                    p1 = _between([A[j]], [B[j]], min(.92, f0 + rng.uniform(.12, .22)))[0]
                    m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 1.0)
                    hair.append([p0, m, p1])
    # rock cleavers: each ridge a dark rib, its shadow side wider below
    for i, R in enumerate(ridges):
        lit = R[0][0] < sx
        wid = [(.6 + W * (.012 if lit else .006) * (j / NR) ** .7) for j in range(NR + 1)]
        rib = R + [(p[0] + w, p[1] + .2) for p, w in zip(R, wid)][::-1]
        hair.extend(C.hatch_poly(rib, -60, 1.5, .2))
        hair.extend(C.hatch_poly(rib, 30, 1.5, .5))
        line.append(R[:int(NR * .75)])
    cv.hair(hair)
    cv.line(line)
    cv.line([p for p in prof if abs(p[0] - sx) < W * .25])

    # ---- foothills: far ridge (ruled), near ridge (forested, dark)
    def ridge_poly(yb, amp, freq, ph, trees, bottom):
        pts = []
        x = X0 - 2
        while x <= X1 + 2:
            yy = yb + amp * math.sin(x / W * freq + ph) + amp * .5 * math.sin(x / W * freq * 2.7 + ph * 2)
            pts.append((x, yy))
            if trees:
                pts.append((x + 1.2, yy - trees * (0.6 + .4 * rng.random())))
                x += 2.6
            else:
                x += 3
        return pts + [(X1 + 2, bottom), (X0 - 2, bottom)]

    far = ridge_poly(y_base - H * .055, H * .02, 9, rng.uniform(0, 6), 0, y_g + 3)
    cv.obj([far], .5)
    cv.hair(C.hatch_poly(far, 0, 1.5, .5))
    near = ridge_poly(y_base + H * .005, H * .025, 6, rng.uniform(0, 6), 3.2 if detail > .5 else 1.5, y_g + 3)
    cv.obj([near], 1.)
    cv.hair(C.hatch_poly(near, 84, 1.5, .2))
    cv.hair(C.hatch_poly(near, 15, 3, .4))

    if ground:
        _section(cv, field, X0, X1, Y0, Y1, W, H, y_g, sx, rng, detail)
    else:
        # meadow foreground with a seismogram scratched across it
        fg = [(X0 - 2, y_g)] + [(X1 + 2, y_g), (X1 + 2, Y1 + 2), (X0 - 2, Y1 + 2)]
        cv.obj([fg], 1.)
        cv.hair(C.hatch_poly(fg, 0, 2, .3))
        tr = _trace(X0, X1, (y_g + Y1) / 2, (Y1 - y_g) * .32, rng, 1.6)
        cv.obj([[(X0 - 2, (y_g + Y1) / 2 - (Y1 - y_g) * .38), (X1 + 2, (y_g + Y1) / 2 - (Y1 - y_g) * .38),
                 (X1 + 2, (y_g + Y1) / 2 + (Y1 - y_g) * .38), (X0 - 2, (y_g + Y1) / 2 + (Y1 - y_g) * .38)]], .5)
        cv.line(tr)

    cid = C._uid("rn", round(X0, 1), round(Y0, 1), round(W, 1), round(H, 1), detail)
    return (f'<clipPath id="{cid}"><path d="{C._d(field, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


def _trace(x0, x1, yc, amp, rng, step=1.2, bursts=None):
    """A seismogram: quiet microseism with a few decaying bursts."""
    n = int((x1 - x0) / step)
    if bursts is None:
        bursts = [(rng.uniform(.08, .92), rng.uniform(.35, 1.0)) for _ in range(5)]
    pts = []
    for i in range(n + 1):
        t = i / n
        a = .08 + .05 * rng.random()
        for c, m in bursts:
            d = t - c
            if d >= 0:
                a += m * math.exp(-d * 60) * (1 if d < .004 else .9)
        sgn = 1 if i % 2 else -1
        pts.append((x0 + (x1 - x0) * t, yc + sgn * amp * min(1., a) * (.6 + .4 * rng.random())))
    return pts


def _section(cv, field, X0, X1, Y0, Y1, W, H, y_g, sx, rng, detail):
    """The earth cut away below the surface: folded strata, a fault, seismic rings, a fossil egg."""
    fx_top, fx_bot = sx + W * .17, sx - W * .02          # fault trace, surface to depth
    throw = max(2., H * .018)

    def fault_x(y):
        t = (y - y_g) / max(1., Y1 - y_g)
        return fx_top + (fx_bot - fx_top) * t + math.sin(t * 17) * 1.2

    depth = Y1 - y_g
    nlay = 5 if detail > .6 else 3
    bounds = []
    for k in range(nlay + 1):
        d0 = depth * k / nlay
        pts = []
        x = X0 - 3
        ph = rng.uniform(0, 6)
        while x <= X1 + 3:
            if k == 0:
                yy = y_g + .8 * math.sin(x * .4 + ph) * (1 if rng.random() > .5 else .4)
            else:
                yy = y_g + d0 + depth * .05 * math.sin((x - X0) / W * 5.5 + k * .9) - depth * .04 * (1 - ((x - sx) / W) ** 2 * 4)
                if x > fault_x(yy):
                    yy += throw
            pts.append((x, yy))
            x += 2.
        if k == nlay:
            pts = [(p[0], Y1 + 3) for p in pts]
        bounds.append(pts)
    surf = bounds[0]
    earth = surf + [(X1 + 3, Y1 + 3), (X0 - 3, Y1 + 3)]
    cv.obj([earth], 1.)
    styles = ["contour2", "pebble", "contour3x", "contour2d", "dark"]
    for k in range(nlay):
        up, lo = bounds[k], bounds[k + 1]
        th = sum(b[1] - a[1] for a, b in zip(up, lo)) / len(up)
        st = styles[k % len(styles)] if detail > .6 else ["contour2", "contour3x", "dark"][k]
        poly = up + lo[::-1]
        if st.startswith("contour"):
            pitch = 2. if "2" in st else 3.
            m = max(1, int(th / pitch))
            for j in range(1, m):
                cv.hair(_between(up, lo, j / m))
            if st.endswith("x"):
                cv.hair(C.hatch_poly(poly, 60, 3, .4))
            if st.endswith("d"):
                cv.hair(C.hatch_poly(poly, -35, 3, .4))
        elif st == "pebble":
            m = max(1, int(th / 3))
            for j in range(1, m):
                cv.hair(_between(up, lo, j / m))
        else:
            cv.hair(C.hatch_poly(poly, 0, 1.5, .2))
            cv.hair(C.hatch_poly(poly, 70, 3, .4))
        cv.line(lo)
    # pebbles in the conglomerate bed (white stones with a shaded underside)
    if detail > .6:
        up, lo = bounds[1], bounds[2]
        for _ in range(int(30 * detail)):
            i = rng.randrange(len(up))
            yy = up[i][1] + (lo[i][1] - up[i][1]) * rng.uniform(.25, .75)
            r = rng.uniform(1.3, 2.6)
            cv.obj([C._ell_pts(up[i][0], yy, r * 1.4, r, 12)[:-1]], .5)
            cv.hair([C._ell_pts(up[i][0] + .3, yy + .4, r * 1.0, r * .55, 10, .3, 2.8)])

    # the fault: a black, jagged break through every bed
    fl = []
    y = y_g - 1
    while y <= Y1 + 3:
        fl.append((fault_x(y) + rng.uniform(-.6, .6), y))
        y += 2.5
    cv.obj([], 0)
    cv.heavy(fl)
    # surface scarp
    cv.line([(fx_top - 3, y_g - .5), (fx_top, y_g - 1.5), (fx_top + 2, y_g + throw * .6)])

    # hypocentre under the mountain, rings of waves through the rock
    hx, hy = sx + W * .05, y_g + depth * .72
    rings = []
    rmax = max(W * .42, depth * 1.05)
    r = 4.
    k = 0
    while r < rmax:
        arc = C._ell_pts(hx, hy, r, r * .82, max(24, int(r * 1.6)))
        top_y = lambda p: p[1] > y_g + 2.5 and Y0 < p[1]
        segs = _keep(arc, top_y)
        rings.append((r, segs))
        r += 4.5 + k * 1.3
        k += 1
    for r, segs in rings:
        for s in segs:
            # a white wave front cut through the beds, ruled on its inner edge
            band = []
            for p in s:
                band.append(p)
            inner = [(hx + (p[0] - hx) * (r - 1.6) / r, hy + (p[1] - hy) * (r - 1.6) / r) for p in s]
            cv.obj([band + inner[::-1]], 0)
            cv.line(s)
            cv.hair(inner)
    # focus: a black star
    star = []
    for i in range(16):
        a = math.pi * 2 * i / 16
        rr = 3.6 if i % 2 == 0 else 1.3
        star.append((hx + rr * math.cos(a), hy + rr * math.sin(a)))
    cv.obj([star], 1.)
    cv.line(C.hatch_poly(star, 0, .8))
    # Easter egg: crossed drumsticks fossilised in the second bed, left of the mountain
    if detail > .6:
        ex = X0 + W * .3
        up, lo = bounds[-2], bounds[-1]
        i = min(range(len(up)), key=lambda j: abs(up[j][0] - ex))
        ey = up[i][1] + min(9., (Y1 - up[i][1]) * .35)
        L = max(16., min(24., W * .08))
        for a in (math.radians(-22), math.radians(180 + 22)):
            ux, uy = math.cos(a), math.sin(a)
            vx, vy = -uy, ux
            bx, by = ex - ux * L / 2, ey - uy * L / 2
            pts_l, pts_r = [], []
            for j in range(11):
                t = j / 10
                w = 1.5 - .7 * t ** 1.5
                px, py = bx + ux * L * t, by + uy * L * t
                pts_l.append((px + vx * w, py + vy * w))
                pts_r.append((px - vx * w, py - vy * w))
            stick = pts_l + pts_r[::-1]
            cv.obj([stick], .5)
            cv.hair([[(bx + ux * L * t - vx * .5, by + uy * L * t - vy * .5) for t in (0, .85)]])
            tx, ty = bx + ux * (L + 1.2), by + uy * (L + 1.2)
            tip = C._ell_pts(tx, ty, 1.6, 1.1, 10)[:-1]
            tip = [(tx + (p[0] - tx) * ux - (p[1] - ty) * uy, ty + (p[0] - tx) * uy + (p[1] - ty) * ux) for p in tip]
            cv.obj([tip], .5)

    # epicentre tremor ticks on the surface above it
    ex = hx
    for j in (-1, 1):
        for q in range(3):
            d = 4 + q * 3
            cv.hair([(ex + j * d, y_g - 1.5 - q * .2), (ex + j * (d + 1.2), y_g - 3.5 + (q % 2)), (ex + j * (d + 2.2), y_g - 1.2)])


# ------------------------------------------------------------------------------------------------
# frames
# ------------------------------------------------------------------------------------------------

_K = 2 ** (-1 / 2.6)


def _drum(cv, x, cy, r, hh):
    """a recording drum seen end-on at the strip's end: the cylinder modelled, the end cap ringed"""
    body = [(x - r, cy - hh), (x + r, cy - hh), (x + r, cy + hh), (x - r, cy + hh)]
    cv.obj([body], 1.)
    tone_hatch(cv, body, lambda px, py: .1 + .85 * ((px - (x - r)) / (2 * r)) ** 1.4, 90., 1.5, .7, 0.)
    for sd in (-1, 1):
        cap = _ell(x, cy + sd * hh, r, r * .32, 20)[:-1]
        cv.obj([cap], 1.)
        cv.hair(_ell(x, cy + sd * hh, r * .55, r * .18, 16))
        cv.obj([_ell(x, cy + sd * hh, r * .16, r * .06, 8)[:-1]], .5)


def lookout_strip(w, h, seed):
    """the tailpiece: a seismogram strip unrolling between two recording drums. The trace is the
    ridge: it climbs into a peak where a fire lookout stands on its tower, and the mountain under it is
    worked in burin tone. The minute ticks run along the strip's foot; the wiggles before the peak go
    long-short, long-short, a bar of swing."""
    rng = random.Random(seed)
    Wd = min(w - 4, h * 5.6)
    x0, x1 = w / 2 - Wd / 2, w / 2 + Wd / 2
    r = h * .1
    top, bot = h * .16, h * .86
    sx0, sx1 = x0 + 2 * r + 1, x1 - 2 * r - 1
    cv = Canvas()
    strip = [(sx0, top + 2), (sx1, top), (sx1, bot), (sx0, bot + 2)]
    cv.obj([strip], 1.)
    # the sky over the ridge: broken dawn strokes, closing up toward the strip's top edge
    yy = top + 2.5
    while yy < bot - 5:
        t = (yy - top) / (bot - top)
        xx = sx0 + rng.uniform(0, 5)
        while xx < sx1 - 1:
            L = rng.uniform(6, 18)
            cv.hair([(xx, yy), (min(sx1 - 1, xx + L), yy)])
            xx += L + rng.uniform(1.5, 3) + 10 * t
        yy += 2.
    # the paper's own ruling: faint minute lines, and the time ticks along the foot
    k = 0
    xx = sx0 + 4
    while xx < sx1 - 2:
        cv.hair([(xx, bot - 1), (xx, bot - (3.5 if k % 5 == 0 else 2))])
        xx += 4
        k += 1
    # the trace: a quiet line, then a bar of swing (pairs long-short), then the ridge climbing to the peak
    base = top + (bot - top) * .66
    px = sx0 + (sx1 - sx0) * .62
    py = top + (bot - top) * .42
    pts = []
    x = sx0 + 1
    i = 0
    while x < sx1 - 1:
        u = (x - sx0) / (sx1 - sx0)
        if u < .1:
            y = base + rng.uniform(-.4, .4)
        elif u < .34:
            beat = (x - (sx0 + (sx1 - sx0) * .1)) % 9.
            amp = (bot - top) * (.16 if beat < 6 else .08)
            y = base - amp * math.sin(beat / 6 * _PI) if beat < 6 else base - amp * math.sin((beat - 6) / 3 * _PI)
        else:
            ridge = math.exp(-((x - px) / ((sx1 - sx0) * .17)) ** 2)
            y = base - (base - py) * ridge + (.8 + .6 * ridge) * math.sin(i * 1.9) * rng.uniform(.4, 1.)
        pts.append((x, y))
        x += 1.1
        i += 1
    # the mountain under the trace, worked in tone, light from the west
    mtn = pts[int(len(pts) * .3):] + [(sx1 - 1, bot - 4), (pts[int(len(pts) * .3)][0], bot - 4)]
    tone_hatch(cv, mtn, lambda x, y: .1 + .45 * (1 if x > px else .3) + .25 * (y - py) / (bot - py), 60., 2., .8, -30.)
    cv.obj([], 0)
    cv.line(pts)
    # firs along the ridge's shoulders
    for j in range(len(pts) // 3, len(pts) - 2, 3):
        fx, fy = pts[j]
        if abs(fx - px) < (sx1 - sx0) * .05 or rng.random() < .35:
            continue
        hgt = rng.uniform(2.5, 4.5)
        cv.line([(fx - hgt * .3, fy + .5), (fx, fy - hgt), (fx + hgt * .3, fy + .5)])
    # the lookout: a glazed cab with a hipped roof and a catwalk on a braced timber tower
    tw, th_ = (bot - top) * .2, (bot - top) * .26
    ly = min(p[1] for p in pts) + .5
    legs = [(px - tw * .45, ly), (px - tw * .25, ly - th_), (px + tw * .25, ly - th_), (px + tw * .45, ly)]
    cv.obj([], 0)
    cv.line([legs[0], legs[1]])
    cv.line([legs[3], legs[2]])
    for q in (.33, .66):
        a_ = (legs[0][0] + (legs[1][0] - legs[0][0]) * q, ly - th_ * q)
        b_ = (legs[3][0] + (legs[2][0] - legs[3][0]) * q, ly - th_ * q)
        cv.hair([a_, b_])
    cv.hair([legs[0], (legs[2][0], ly - th_ * .66)])
    cv.hair([legs[3], (legs[1][0], ly - th_ * .66)])
    cab = [(px - tw * .42, ly - th_), (px + tw * .42, ly - th_), (px + tw * .42, ly - th_ - tw * .45), (px - tw * .42, ly - th_ - tw * .45)]
    cv.obj([cab], 1.)
    for q in (-.2, 0., .2):
        cv.hair([(px + tw * q, ly - th_ - 1), (px + tw * q, ly - th_ - tw * .42)])
    tone_hatch(cv, [(px + tw * .2, ly - th_), (px + tw * .42, ly - th_), (px + tw * .42, ly - th_ - tw * .45), (px + tw * .2, ly - th_ - tw * .45)],
               lambda x, y: .7, 90., 1.5, None)
    roof = [(px - tw * .55, ly - th_ - tw * .45), (px + tw * .55, ly - th_ - tw * .45), (px, ly - th_ - tw * .8)]
    cv.obj([roof], 1.)
    tone_hatch(cv, roof, lambda x, y: .2 if x < px else .75, 30., 1.5, None)
    cv.line([(px - tw * .6, ly - th_ + .5), (px + tw * .6, ly - th_ + .5)])
    # the pen at the strip's right, the drums at both ends with the paper wrapped round them
    for sd, xx in ((-1, x0 + r), (1, x1 - r)):
        _drum(cv, xx, (top + bot) / 2, r, (bot - top) / 2 + 1)
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = _seed(ctx)
    uid = f"hz{int(w)}x{int(h)}"
    if h <= 110:
        return vignette(w, h, uid, None, "", None, lookout_strip(w, h, seed))
    # taller: Rainier and the cut-away strata in a ruled oval, the seismogram strip beneath
    sh = min(64., h * .3)
    cx, cy, a, b = box_fit(w, h - sh, 1.7, pad=3)
    cy = 3 + b
    clean = shape_pts(cx, cy, a, b, "oval", 160)
    body = scene(clean, ctx, .8, True)
    foot = f'<svg x="0" y="{_nn(h - sh)}" width="{_nn(w)}" height="{_nn(sh)}" overflow="visible">{lookout_strip(w, sh, seed)}</svg>'
    return vignette(w, h, uid, clean, body, clean, foot)
