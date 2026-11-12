"""sports-05 Formula 1, merged into The scoreboard (edition plan: small tailpiece, a banner).

The tailpiece is a knitted supporters' scarf laid across in a long wave on a transparent ground:
Timbers green and gold in blocks with the Vikings' stripe between, every stitch cut as a small V
whose weight carries the colour and the shading where the drape turns, fringed and knotted at both
ends. Easter egg (the plan's): a chequered flag on a drumstick staff tucked in at the right. At
taller sizes the Las Vegas Strip at night with the silver car sits in a ruled arch over the scarf."""
import sys
import math
import random
import re
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

from engraving_codex import Canvas, _d, _n, _ell_pts, hatch_poly, _clip, _uid

PI = math.pi
TAU = 2 * PI


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------

def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _scan(poly, angle, pitch, phase=0.):
    return hatch_poly(poly, angle, pitch, phase)


def _keep(lines, fn, step=1.):
    """Cut straight hatch lines into runs where fn(x, y) is true."""
    out = []
    for a, b in lines:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        cur = []
        for i in range(n + 1):
            t = i / n
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if fn(*p):
                cur.append(p)
            else:
                if len(cur) > 1:
                    out.append([cur[0], cur[-1]])
                cur = []
        if len(cur) > 1:
            out.append([cur[0], cur[-1]])
    return out


def _sp_tone(cv, poly, tone, angle=0., layers=None):
    """Bulino tone: fn tone(x, y) in [0, 1] -> lines laid in up to four layers."""
    layers = layers or [(angle, 3., 0., .1, .5), (angle, 3., 1.5, .35, .5),
                        (angle, 3., 0., .58, 1.), (angle, 3., 1.5, .74, 1.), (angle, 1.5, 0., .9, 1.5)]
    for ang, pitch, ph, thr, wt in layers:
        ls = _keep(_scan(poly, ang, pitch, ph), lambda x, y, t=thr: tone(x, y) > t)
        if wt >= 1.5:
            cv.heavy(ls)
        elif wt >= 1:
            cv.line(ls)
        else:
            cv.hair(ls)


def _grow(poly, d):
    """Offset a simple polygon outward by d (vertex normals)."""
    n = len(poly)
    a = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1 if a > 0 else -1
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        nx = ny = 0.
        for (ax, ay), (bx, by) in ((p0, p1), (p1, p2)):
            l = math.hypot(bx - ax, by - ay) or 1
            nx += (by - ay) / l
            ny += -(bx - ax) / l
        l = math.hypot(nx, ny) or 1
        k = min(2.5, 2 / max(.4, l))
        out.append((p1[0] + sgn * nx / l * d * k, p1[1] + sgn * ny / l * d * k))
    return out


def _dashes(pl, on, off):
    out, cur, acc, state = [], [pl[0]], 0., True
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        pos = 0.
        while pos < L - 1e-9:
            lim = (on if state else off) - acc
            take = min(lim, L - pos)
            pos += take
            acc += take
            p = (a[0] + (b[0] - a[0]) * pos / L, a[1] + (b[1] - a[1]) * pos / L)
            if state:
                cur.append(p)
            if acc >= (on if state else off) - 1e-9:
                if state and len(cur) > 1:
                    out.append(cur)
                state = not state
                acc = 0.
                cur = [p]
    if state and len(cur) > 1:
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------------
# lettering in paths (house glyphs, extended)
# ------------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GLYPH = {
    "0": (.56, [_arc(.28, .5, .26, .5, 0, 360, 20)]),
    "1": (.42, [[(.06, .2), (.24, 0), (.24, 1)], [(.04, 1), (.44, 1)]]),
    "2": (.56, [_arc(.27, .27, .24, .25, 195, 380, 7) + [(.04, 1), (.54, 1)]]),
    "3": (.54, [_arc(.26, .25, .23, .25, 205, 450, 8), _arc(.26, .73, .27, .27, 270, 520, 8)]),
    "4": (.56, [[(.42, 1), (.42, 0), (.02, .72), (.56, .72)]]),
    "5": (.54, [[(.5, 0), (.1, 0), (.06, .44)] + _arc(.26, .7, .27, .3, 225, 500, 9)[1:]]),
    "6": (.56, [_arc(.28, .7, .26, .3, 0, 360, 14), [(.03, .68), (.12, .25), (.26, .04), (.46, 0)]]),
    "7": (.54, [[(.02, 0), (.54, 0), (.2, 1)]]),
    "8": (.54, [_arc(.27, .24, .21, .24, 0, 360, 12), _arc(.27, .73, .26, .27, 0, 360, 14)]),
    "9": (.56, [_arc(.28, .3, .26, .3, 0, 360, 14), [(.53, .32), (.44, .75), (.3, .96), (.1, 1)]]),
    "-": (.42, [[(.05, .56), (.37, .56)]]),
    ".": (.2, [_arc(.1, .92, .06, .06, 0, 360, 6)]),
    "W": (.84, [[(0, 0), (.2, 1), (.42, .2), (.64, 1), (.84, 0)]]),
    "L": (.5, [[(.08, 0), (.08, 1), (.5, 1)]]),
    "B": (.54, [[(.08, .48)] + _arc(.32, .74, .2, .26, -90, 90, 6) + [(.08, 1), (.08, 0)] + _arc(.3, .24, .17, .24, -90, 90, 6) + [(.08, .48)]]),
    "A": (.66, [[(0, 1), (.33, 0), (.66, 1)], [(.13, .64), (.53, .64)]]),
    "Z": (.56, [[(.04, 0), (.54, 0), (.02, 1), (.54, 1)]]),
    "E": (.5, [[(.48, 0), (.08, 0), (.08, 1), (.5, 1)], [(.08, .5), (.4, .5)]]),
    "F": (.48, [[(.48, 0), (.08, 0), (.08, 1)], [(.08, .5), (.4, .5)]]),
    "R": (.56, [[(.08, 1), (.08, 0)] + _arc(.3, .25, .22, .25, -90, 90, 6) + [(.08, .5)], [(.28, .5), (.56, 1)]]),
    "S": (.52, [_arc(.27, .26, .23, .25, -20, -270, 8) + _arc(.27, .74, .25, .26, -90, 160, 8)[1:]]),
    "I": (.2, [[(.1, 0), (.1, 1)]]),
    "J": (.44, [[(.38, 0), (.38, .7)] + _arc(.2, .7, .18, .3, 0, 160, 6)[1:]]),
    "P": (.54, [[(.08, 1), (.08, 0)] + _arc(.3, .26, .22, .26, -90, 90, 6) + [(.08, .52)]]),
    "C": (.6, [_arc(.32, .5, .3, .5, -40, -320, 14)]),
    "G": (.62, [_arc(.32, .5, .3, .5, -40, -320, 14), [(.34, .56), (.6, .56), (.6, .92)]]),
    "Q": (.7, [_arc(.35, .5, .33, .5, 0, 360, 20), [(.42, .72), (.7, 1.04)]]),
    "T": (.56, [[(0, 0), (.56, 0)], [(.28, 0), (.28, 1)]]),
    "Y": (.6, [[(0, 0), (.3, .5), (.6, 0)], [(.3, .5), (.3, 1)]]),
    "V": (.62, [[(0, 0), (.31, 1), (.62, 0)]]),
    "X": (.58, [[(0, 0), (.58, 1)], [(.58, 0), (0, 1)]]),
    "O": (.7, [_arc(.35, .5, .33, .5, 0, 360, 20)]),
    "K": (.56, [[(.08, 0), (.08, 1)], [(.54, 0), (.08, .58)], [(.24, .44), (.56, 1)]]),
    "H": (.6, [[(.06, 0), (.06, 1)], [(.54, 0), (.54, 1)], [(.06, .5), (.54, .5)]]),
    "D": (.6, [[(.08, 0), (.08, 1), (.26, 1)] + _arc(.26, .5, .3, .5, 90, -90, 10)[1:] + [(.08, 0)]]),
    "N": (.6, [[(.06, 1), (.06, 0), (.54, 1), (.54, 0)]]),
    "U": (.6, [[(.06, 0), (.06, .66)] + _arc(.3, .66, .24, .34, 180, 0, 8)[1:] + [(.54, 0)]]),
    "M": (.74, [[(.04, 1), (.06, 0), (.37, .8), (.68, 0), (.7, 1)]]),
    "*": (.5, [[(.25, .2), (.25, .8)], [(.04, .35), (.46, .65)], [(.04, .65), (.46, .35)]]),
    " ": (.3, []),
}


def text_width(s, size, track=.18):
    return sum((GLYPH.get(ch, GLYPH[" "])[0] + track) * size for ch in s) - track * size


def letter(s, size, place, track=.18):
    out = []
    x = 0.
    for ch in s:
        gw, strokes = GLYPH.get(ch, GLYPH[" "])
        for st in strokes:
            out.append([place(x + px * size, py * size) for px, py in st])
        x += (gw + track) * size
    return out


def along(centre, size, s, track=.18):
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    start = (S[-1] - text_width(s, size, track)) / 2

    def place(x, y):
        t = start + x
        k = 1
        while k < len(S) - 1 and S[k] < t:
            k += 1
        a, b = centre[k - 1], centre[k]
        f = (t - S[k - 1]) / ((S[k] - S[k - 1]) or 1)
        px, py = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        yy = y - size / 2
        return (px - math.sin(ang) * yy, py + math.cos(ang) * yy)
    return place


# ------------------------------------------------------------------------------------------------
# page content
# ------------------------------------------------------------------------------------------------

NUMBERS = {"ANTONELLI": "12", "RUSSELL": "63", "HAMILTON": "44", "LECLERC": "16", "VERSTAPPEN": "3",
           "NORRIS": "1", "PIASTRI": "81", "ALONSO": "14", "SAINZ": "55", "ALBON": "23"}
TEAMS = r"(Mercedes|Ferrari|Red Bull|McLaren|Aston Martin|Alpine|Williams|Haas|Sauber|Audi|Racing Bulls|Cadillac|RB)"


def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date)
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .76
    return (days / 29.530588) % 1.


# ------------------------------------------------------------------------------------------------
# figures: wheel, the F1 car, chequered flag on a drumstick staff
# ------------------------------------------------------------------------------------------------

def wheel(cv, cx, cy, r, rot=0., outline=1.):
    """Racing wheel in profile: grooved black rubber, a white sidewall band, spoked rim, hub nut."""
    disc = _ell_pts(cx, cy, r, r, max(24, int(r * 2.5)))[:-1]
    cv.obj([disc], outline)
    rr = r * .56
    k = r - .8
    ring = []
    while k > rr:
        if not (r * .8 < k < r * .8 + 1.2):
            ring.append(_ell_pts(cx, cy, k, k, max(20, int(k * 2.2))))
        k -= 1.5
    cv.heavy(ring)
    # rim
    rim = _ell_pts(cx, cy, rr, rr, max(20, int(rr * 2.5)))[:-1]
    cv.obj([rim], 1.)
    _sp_tone(cv, rim, lambda x, y: .2 + .9 * ((x - cx) * .5 + (y - cy) * .8) / rr, 30.)
    sp = []
    for i in range(10):
        a = rot + TAU * i / 10
        sp.append([(cx + rr * .3 * math.cos(a), cy + rr * .3 * math.sin(a)),
                   (cx + rr * .95 * math.cos(a + .12), cy + rr * .95 * math.sin(a + .12))])
    cv.line(sp) if rr > 8 else cv.hair(sp)
    hub = _ell_pts(cx, cy, max(1.5, rr * .3), max(1.5, rr * .3), 16)[:-1]
    cv.obj([hub], 1.)
    if rr > 6:
        cv.hair(hatch_poly(hub, 45, 1.5))
        cv.obj([_ell_pts(cx - rr * .08, cy - rr * .08, max(1., rr * .1), max(1., rr * .1), 10)[:-1]], 0)


BODY = [(.045, .03), (.04, .085), (.12, .10), (.26, .125), (.37, .175), (.43, .19),
        (.455, .19), (.47, .135), (.55, .126), (.62, .11), (.70, .095), (.80, .08),
        (.90, .066), (.975, .052), (.99, .044), (.94, .036), (.80, .04), (.68, .044),
        (.62, .03)]


def f1_car(cv, x0, yg, L, number="", streaks=True, sparks=True, X=None, W=None):
    """2026 car in profile, nose to the right. x0: tail end, yg: ground line, L: overall length."""
    def P(u, v):
        return (x0 + u * L, yg - v * L)

    def poly(pts):
        return [P(u, v) for u, v in pts]

    # shadow pool under the car
    sh = [P(.06 + .9 * i / 30, .004 - .018 * math.sin(PI * i / 30)) for i in range(31)]
    sh += [P(.96 - .9 * i / 30, -.012 - .006 * math.sin(PI * i / 30)) for i in range(31)]
    cv.obj([sh], 0)
    cv.heavy(_scan(sh, 0, 1.5, .2))
    # streaks of light trailing behind
    if streaks:
        rng = random.Random(int(L * 7))
        left = (X if X is not None else x0 - L) - 2
        for i in range(9):
            v = .02 + .02 * i + rng.uniform(-.005, .005)
            if v > .2:
                break
            ln = rng.uniform(.35, .9) * (x0 - left + L * .1)
            yy = yg - v * L
            st = [(x0 + L * .06, yy - .4), (x0 + L * .06 - ln, yy), (x0 + L * .06, yy + .4)]
            cv.obj([st], 0)
    # a white contour separating the car from the night
    halo_d = max(1.2, L * .007)
    cv.obj([_grow(poly([(.0, .07), (.085, .07), (.10, .215), (.005, .225)]), halo_d),
            _grow(poly(BODY), halo_d), _grow(poly([(.90, .012), (1.0, .012), (1.0, .05), (.93, .062), (.90, .045)]), halo_d)]
           + [_ell_pts(*P(u, v), wr_ + halo_d, wr_ + halo_d, 32)[:-1] for u, v, wr_ in ((.135, .072, L * .072), (.80, .068, L * .0684))], 0)
    # rear wing: endplate and two elements
    rw = poly([(.0, .07), (.085, .07), (.10, .215), (.005, .225)])
    cv.obj([rw], 1.)
    _sp_tone(cv, rw, lambda x, y: 1.05 - .3 * (yg - y) / (L * .22) - (.5 if x > x0 + L * .075 else 0), 0)
    cv.heavy([[P(-.005, .225), P(.11, .218)], [P(.0, .195), P(.10, .19)]])
    cv.line([[P(.04, .07), P(.06, .03)], [P(.07, .07), P(.09, .03)]])
    # body: engine cover, airbox, cockpit, nose
    body = poly(BODY)
    cv.obj([body], 1.5)
    top = lambda u: .19 if .37 < u < .46 else None

    def btone(x, y):
        u = (x - x0) / L
        v = (yg - y) / L
        # silhouette top at u (approx), relative depth below it
        if u < .37:
            t = .085 + (u - .04) / .33 * .09
        elif u < .47:
            t = .19
        else:
            t = .135 - (u - .47) / .52 * .09
        rel = (t - v) / max(.03, t - .03)
        dark = .22 + .8 * max(0., rel) ** 1.3
        if v < .052 and u < .66:
            dark += .55               # black floor and lower sidepod
        if .62 < u < .99 and v < .06:
            dark += .15
        return dark
    _sp_tone(cv, body, btone, 0)
    # the long white highlight running along the shoulder
    hl = poly([(.10, .093), (.26, .113), (.37, .16), (.37, .15), (.26, .104), (.10, .087)])
    cv.obj([hl], 0)
    hl2 = poly([(.48, .124), (.62, .104), (.80, .074), (.94, .058), (.94, .054), (.80, .068), (.62, .097), (.48, .117)])
    cv.obj([hl2], 0)
    # sidepod inlet and panel lines
    cv.line([[P(.40, .13), P(.45, .118), P(.47, .085), P(.43, .07)]])
    cv.hair([[P(.12, .06), P(.40, .072)], [P(.30, .095), P(.30, .05)]])
    # airbox mouth (black)
    mouth = poly([(.43, .19), (.455, .19), (.452, .165), (.432, .168)])
    cv.obj([mouth], 1.)
    cv.heavy(_scan(mouth, 90, 1.5))
    # number roundel on the engine cover
    if number:
        rcx, rcy = P(.24, .088)
        rr = L * .026
        if rr > 3:
            rd = _ell_pts(rcx, rcy, rr, rr, 24)[:-1]
            cv.obj([rd], 1.)
            sz = rr * 1.15
            tw = text_width(number, sz, .1)
            cv.line(letter(number, sz, lambda x, y: (rcx - tw / 2 + x, rcy - sz / 2 + y), .1))
    # driver: helmet with a black visor, inside the halo
    hx, hy = P(.495, .15)
    hr = L * .022
    helm = _ell_pts(hx, hy, hr, hr * .95, 20)[:-1]
    cv.obj([helm], 1.)
    _sp_tone(cv, helm, lambda x, y: .3 + .8 * ((x - hx) * -.3 + (y - hy)) / hr, 0)
    vis = [(hx + hr * .25, hy - hr * .35), (hx + hr * 1.0, hy - hr * .25), (hx + hr * .9, hy + hr * .15), (hx + hr * .3, hy + hr * .05)]
    cv.obj([vis], 0)
    cv.heavy(_scan(vis, 0, 1.5))
    # halo hoop
    cv.heavy([[P(.47, .137), P(.52, .175), P(.58, .17), P(.615, .112)]])
    cv.line([[P(.52, .175), P(.535, .135)]])
    # front wing: endplate, flaps
    fw = poly([(.90, .012), (1.0, .012), (1.0, .05), (.93, .062), (.90, .045)])
    cv.obj([fw], 1.)
    _sp_tone(cv, fw, lambda x, y: .7 + .4 * (y - (yg - .05 * L)) / (.04 * L), 0)
    cv.line([[P(.905, .03), P(.995, .036)], [P(.91, .045), P(.99, .046)]])
    # bargeboards/floor edge
    cv.heavy([[P(.33, .025), P(.66, .025)]])
    # wheels
    wr = L * .072
    wheel(cv, *P(.135, .072), wr, .3)
    wheel(cv, *P(.80, .068), wr * .95, .9)
    # sparks off the plank
    if sparks:
        rng = random.Random(int(L * 13))
        for i in range(7):
            sx, sy = P(.62 - .03 * i, .012)
            ln = L * rng.uniform(.08, .2)
            a = rng.uniform(-.12, .1)
            sp = [(sx, sy - .5), (sx - ln * math.cos(a), sy - ln * math.sin(a)), (sx, sy + .5)]
            cv.obj([sp], 0)


def drumstick(cv, x0, y0, x1, y1, w):
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    sh = []
    for i in range(13):
        u = i / 12 * .84
        hw = w / 2 * (1. if u < .5 else 1 - .62 * (u - .5) / .34)
        sh.append((u * L, hw))
    left = [(x0 + ux * s + nx * hw, y0 + uy * s + ny * hw) for s, hw in sh]
    right = [(x0 + ux * s - nx * hw, y0 + uy * s - ny * hw) for s, hw in sh]
    cv.obj([left + right[::-1]], 1.)
    for f in (-.45, .15):
        cv.hair([(x0 + ux * s + nx * hw * f, y0 + uy * s + ny * hw * f) for s, hw in sh])
    if w > 2.5:
        cv.hair([(x0 + ux * s - nx * hw * .75, y0 + uy * s - ny * hw * .75) for s, hw in sh])
    tcx, tcy = x0 + ux * L * .91, y0 + uy * L * .91
    tl, tw = L * .085, w * .4
    tip = [(tcx + ux * tl * math.cos(t) + nx * tw * math.sin(t), tcy + uy * tl * math.cos(t) + ny * tw * math.sin(t))
           for t in [TAU * i / 16 for i in range(16)]]
    cv.obj([tip], 1.)


def chequered_flag(cv, bx, by, tx, ty, fw, fh, side, w_staff, nc=6, nr=4, phase=0.):
    """A drumstick staff from butt (bx, by) to tip (tx, ty); a waving chequered flag hung from
    just under the tip, flying outward to `side` (-1 left, +1 right)."""
    drumstick(cv, bx, by, tx, ty, w_staff)
    L = math.hypot(tx - bx, ty - by)
    ux, uy = (tx - bx) / L, (ty - by) / L
    ax, ay = bx + ux * L * .8, by + uy * L * .8      # top of the hoist
    # flag frame: along = horizontal-ish outward, down = back along the staff
    dx, dy = -ux, -uy

    def F(u, v):
        wave = math.sin(u * PI * 1.6 + phase) * fh * .14 * u
        sag = u * u * fh * .18
        return (ax + side * u * fw + dx * (v * fh + wave + sag) * .98,
                ay + dy * (v * fh) + wave + sag)

    outline = [F(i / 20, 0) for i in range(21)] + [F(1, j / 6) for j in range(1, 7)] + \
              [F(1 - i / 20, 1) for i in range(1, 21)] + [F(0, 1 - j / 6) for j in range(1, 6)]
    cv.obj([outline], 1.)
    for i in range(nc):
        for j in range(nr):
            cell = [F(i / nc, j / nr), F((i + 1) / nc, j / nr), F((i + 1) / nc, (j + 1) / nr), F(i / nc, (j + 1) / nr)]
            shade = math.cos((i + .5) / nc * PI * 1.6 + phase)       # fold shading
            if (i + j) % 2 == 0:
                cv.heavy(_scan(cell, 0, 1.5, .3))
            elif shade < -.2:
                cv.hair(_scan(cell, 0, 2.))
            elif shade < .4:
                cv.hair(_scan(cell, 0, 3.))
    # re-draw staff tip over the hoist so the flag hangs behind the bead
    tcx, tcy = bx + ux * L * .91, by + uy * L * .91
    tip = [(tcx + ux * L * .085 * math.cos(t) - uy * w_staff * .4 * math.sin(t),
            tcy + uy * L * .085 * math.cos(t) + ux * w_staff * .4 * math.sin(t)) for t in [TAU * i / 16 for i in range(16)]]
    cv.obj([tip], 1.)


# ------------------------------------------------------------------------------------------------
# the Strip at night
# ------------------------------------------------------------------------------------------------

def vegas_scene(X, Y, W, H, seed=0, number="", date="", detail=True):
    cv = Canvas()
    rng = random.Random(seed)
    yh = Y + H * (.6 if detail else .5)      # horizon / foot of the barrier fence
    yg = Y + H * (.87 if detail else .9)     # ground line under the car
    # night sky: dense bulino at the zenith opening to a glow above the Strip
    sky = _rect(X - 2, Y - 2, X + W + 2, yh + 1)
    cv.obj([sky], 0)
    y = Y - 1.
    while y < yh + 1:
        f = (y - Y) / max(1, yh - Y)
        if f < .3:
            cv.line([(X - 2, y), (X + W + 2, y)])
            y += 2.
        else:
            cv.hair([(X - 2, y), (X + W + 2, y)])
            y += 1.5 if f < .55 else (2. if f < .82 else 3.)
    # stars
    for _ in range(int(W * (yh - Y) / 900)):
        sx, sy = X + rng.uniform(.03, .97) * W, Y + rng.uniform(.03, .5) * (yh - Y)
        s = rng.choice((1.1, 1.4, 1.8))
        cv.obj([[(sx, sy - s), (sx + s * .35, sy), (sx, sy + s), (sx - s * .35, sy)]], 0)
        cv.obj([[(sx - s, sy), (sx, sy - s * .35), (sx + s, sy), (sx, sy + s * .35)]], 0)
    if detail:
        # the moon, in today's phase
        ph = _moon_phase(date)
        mr = max(5., min(W, H) * .055)
        mx, my = X + W * .6, Y + H * .07 + mr
        disc = _ell_pts(mx, my, mr, mr, 40)[:-1]
        cv.obj([disc], .5)
        k = math.cos(ph * TAU)        # terminator ellipse x-scale
        waxing = ph < .5

        def lit(x, y):
            dx, dy = (x - mx) / mr, (y - my) / mr
            if dx * dx + dy * dy > 1:
                return False
            xt = k * math.sqrt(max(0., 1 - dy * dy))
            return dx > xt if waxing else dx < -xt
        cv.hair(_keep(_scan(disc, 0, 1.5), lambda x, y: not lit(x, y)))
        cv.hair(_keep(_scan(disc, 0, 3., 1.), lit))
        for (cx_, cy_, cr) in ((.3, -.2, .18), (-.25, .3, .14), (.1, .4, .1)):
            c = (mx + cx_ * mr, my + cy_ * mr)
            if lit(*c):
                cv.hair([_ell_pts(c[0], c[1], cr * mr, cr * mr, 10)])
        # the Luxor beam
        lx = X + W * .3
        beam = [(lx - .8, yh - H * .17), (lx - 3.5, Y - 2), (lx + 3.5, Y - 2), (lx + .8, yh - H * .17)]
        cv.obj([beam], 0)
        cv.hair([[(lx, yh - H * .17), (lx, Y - 2)]])
    # towers of the Strip: lit window grids, shadowed flanks
    towers = []
    xs = X - 4
    while xs < X + W:
        tw = rng.uniform(.06, .11) * W
        th = rng.uniform(.18, .38) * (yh - Y) * (1.25 if detail else 1.)
        towers.append((xs, tw, th, rng.random()))
        xs += tw * rng.uniform(.75, 1.05)
    for xs, tw, th, kind in towers:
        top = yh - th
        shape = [(xs, yh + 1), (xs, top + 4), (xs + tw * .2, top + 4), (xs + tw * .2, top), (xs + tw * .8, top),
                 (xs + tw * .8, top + 4), (xs + tw, top + 4), (xs + tw, yh + 1)] if kind < .5 else \
            [(xs, yh + 1), (xs, top + tw * .25), (xs + tw * .5, top), (xs + tw, top + tw * .25), (xs + tw, yh + 1)]
        cv.obj([shape], .5)
        cv.hair(_scan(shape, 90, 3., .5) + _scan(shape, 0, 3., .5))
        shade = [(xs + tw * .62, yh + 1), (xs + tw * .62, top), (xs + tw, top), (xs + tw, yh + 1)]
        cv.hair(_scan(shade, 90, 1.5, 0.))
    if detail:
        # the Stratosphere, far left
        sx = X + W * .12
        stop = Y + H * .2
        shaft = [(sx - 2.5, yh + 1), (sx - 1.5, stop + 12), (sx + 1.5, stop + 12), (sx + 2.5, yh + 1)]
        cv.obj([shaft], .5)
        cv.hair(_scan(shaft, 90, 1.5, .4))
        pod = [(sx - 9, stop + 12), (sx - 7, stop + 6), (sx + 7, stop + 6), (sx + 9, stop + 12), (sx + 5, stop + 15), (sx - 5, stop + 15)]
        cv.obj([pod], 1.)
        cv.hair(_scan(pod, 0, 1.5) )
        cv.obj([[(sx - 6, stop + 9), (sx + 6, stop + 9), (sx + 6, stop + 10.2), (sx - 6, stop + 10.2)]], 0)
        cv.line([[(sx, stop + 6), (sx, stop - 10)]])
        # the Luxor pyramid
        lx = X + W * .3
        pw = W * .12
        pyr = [(lx - pw, yh + 1), (lx, yh - H * .17), (lx + pw, yh + 1)]
        cv.obj([pyr], 1.)
        cv.hair(_scan([(lx - pw, yh + 1), (lx, yh - H * .17), (lx, yh + 1)], 60, 3.))
        cv.hair(_scan([(lx, yh + 1), (lx, yh - H * .17), (lx + pw, yh + 1)], -60, 1.5))
        # the Sphere
        sr = min(W * .14, H * .16)
        scx, scy = X + W * .74, yh - sr * .8
        sp = _ell_pts(scx, scy, sr, sr, 64)[:-1]
        cv.obj([sp], 1.)
        grid = []
        for i in range(1, 8):
            lat = -PI / 2 + PI * i / 8
            yy = scy + sr * math.sin(lat)
            hw = sr * math.cos(lat)
            grid.append(_dashes([(scx - hw, yy), (scx + hw, yy)], 1., 1.5))
        for i in range(1, 8):
            lo = -PI / 2 + PI * i / 8
            grid.append(_dashes([(scx + sr * math.sin(lo) * math.cos(t), scy + sr * math.sin(t))
                                 for t in [-PI / 2 + PI * j / 24 for j in range(25)]], 1., 1.5))
        for g in grid:
            cv.hair(g)
        # the LED skin: a fine dotted screen
        for ln in _scan(sp, 0, 3., 1.5):
            cv.hair(_dashes(ln, .8, 2.2))
        cv.hair(_keep(_scan(sp, 45, 2.), lambda x, y: (x - scx + sr * .35) ** 2 + (y - scy + sr * .35) ** 2 > (sr * 1.05) ** 2))
        cv.hair(_keep(_scan(sp, -45, 2.), lambda x, y: (x - scx + sr * .4) ** 2 + (y - scy + sr * .4) ** 2 > (sr * 1.35) ** 2))
    # catch fence and barrier wall
    fy1 = yh + H * (.05 if detail else .06)
    fence = _rect(X - 2, yh, X + W + 2, fy1)
    cv.obj([fence], 0)
    cv.hair(_scan(fence, 60, 3.) + _scan(fence, -60, 3.))
    cv.line([[(X - 2, yh), (X + W + 2, yh)]])
    posts = []
    px = X - 2
    while px < X + W + 2:
        posts.append([(px, yh - 3), (px, fy1)])
        px += 22
    cv.line(posts)
    wy1 = fy1 + H * .05
    wall = _rect(X - 2, fy1, X + W + 2, wy1)
    cv.obj([wall], 1.)
    cv.hair(_scan(wall, 0, 2., .5))
    panels = []
    px = X + 8
    while px < X + W + 2:
        panels.append([(px, fy1), (px, wy1)])
        px += 36
    cv.line(panels)
    # track: ruled asphalt, darker near the barrier
    trk = _rect(X - 2, wy1, X + W + 2, Y + H + 2)
    cv.obj([trk], 1.)
    y = wy1 + 1.5
    while y < Y + H + 2:
        cv.line([(X - 2, y), (X + W + 2, y)])
        y += 2.
    # chequered kerb in the foreground
    ky0 = Y + H * (.9 if detail else .93)
    kerb = []
    k = 0
    bx = X - 6
    while bx < X + W + 4:
        cell = [(bx, Y + H + 2), (bx + 4, ky0), (bx + 4 + 12, ky0), (bx + 12, Y + H + 2)]
        cv.obj([cell], .5)
        if k % 2 == 0:
            cv.heavy(_scan(cell, 0, 1.5, .2))
        else:
            cv.hair(_scan(cell, 0, 3.))
        bx += 12
        k += 1
    # the car, flat out
    L = min(W * (1.02 if detail else .92), H * (2.6 if detail else 3.4))
    f1_car(cv, X + W * .5 - L * .48, yg, L, number, True, detail, X, W)
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts
# ------------------------------------------------------------------------------------------------

def supporters_scarf(w, h, seed):
    """the tailpiece: a knitted supporters' scarf laid across in a long wave, Timbers green and gold
    in blocks with the Vikings' stripe between, every stitch a small V, the drape shaded where it
    turns, fringed at both ends; a chequered flag on a drumstick staff tucked in at the right"""
    rng = random.Random(seed)
    Wd = min(w - 4, h * 5.6)
    x0, x1 = w / 2 - Wd / 2 + h * .12, w / 2 + Wd / 2 - h * .3
    hw = h * .2
    cy = h * .48
    C_ = []
    for i in range(61):
        u = i / 60
        C_.append((x0 + (x1 - x0) * u, cy + h * .12 * _m.sin(u * _TAU * 1.15 + .6)))
    cv = Canvas()
    R = _Rib(C_, [hw] * len(C_), [hw] * len(C_))
    cv.obj([R.outline()], 1.)
    # walk along the scarf: stripe blocks, drape shading from the slope, stitches in rows
    acc = [0.]
    for i in range(1, len(C_)):
        acc.append(acc[-1] + _m.dist(C_[i - 1], C_[i]))
    L = acc[-1]
    blocks = [("dark", .14), ("light", .02), ("mid", .05), ("light", .02), ("dark", .14), ("gold", .1)] * 3
    tot = sum(b for _, b in blocks)
    bounds, s_ = [], 0.
    for kind, b in blocks:
        bounds.append((s_ / tot * L, (s_ + b) / tot * L, kind))
        s_ += b
    tone_of = {"dark": .78, "mid": .5, "gold": .2, "light": 0.}
    step = 2.4
    s = 1.
    j = 0
    while s < L - 1:
        i = next(k for k in range(1, len(acc)) if acc[k] >= s)
        t = (s - acc[i - 1]) / max(1e-6, acc[i] - acc[i - 1])
        (ax, ay), (bx, by) = C_[i - 1], C_[i]
        px, py = ax + (bx - ax) * t, ay + (by - ay) * t
        tx, ty = (bx - ax) / max(1e-6, acc[i] - acc[i - 1]), (by - ay) / max(1e-6, acc[i] - acc[i - 1])
        nx, ny = -ty, tx
        kind = next(k for a_, b_, k in bounds if a_ <= s < b_) if s < bounds[-1][1] else "dark"
        drape = .25 * ty
        v = -1 + 1.2 / hw
        while v < 1 - 1.2 / hw:
            tone = tone_of[kind] + drape + .25 * max(0., abs(v) - .7) / .3
            qx, qy = px + nx * v * hw, py + ny * v * hw
            if tone > .12:
                pl = [(qx - tx * 1. + nx * .9, qy - ty * 1. + ny * .9), (qx, qy), (qx + tx * 1. + nx * .9, qy + ty * 1. + ny * .9)]
                (cv.hair if tone < .45 else (cv.line if tone < .8 else cv.heavy))(pl)
            v += 2.2 / hw
        if kind == "light" and j % 2 == 0:
            cv.hair([(px + nx * hw * .95, py + ny * hw * .95), (px - nx * hw * .95, py - ny * hw * .95)])
        s += step
        j += 1
    # the fringe at each end, knotted in bunches
    for end, sgn in ((C_[0], -1), (C_[-1], 1)):
        (ex, ey) = end
        for k in range(9):
            v = -1 + 2 * k / 8
            fx, fy = ex, ey + v * hw * .9
            ln = h * rng.uniform(.12, .2)
            cv.obj([], 0)
            cv.line([(fx, fy), (fx + sgn * ln * .4, fy + rng.uniform(-1, 1)), (fx + sgn * ln, fy + rng.uniform(-2, 2))])
            if k % 3 == 1:
                cv.obj([_ell(fx + sgn * 1.6, fy, 1.4, 1.4, 8)[:-1]], 1.)
    svg = cv.svg()
    cvf = C.Canvas()
    fx = x1 + h * .14
    chequered_flag(cvf, fx, h * .97, fx - h * .02, h * .06, h * .42, h * .28, -1, max(1.2, h * .03), 5, 3)
    return svg + cvf.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) % 997 + 53
    uid = f"sb{int(w)}x{int(h)}"
    if h <= 110:
        return vignette(w, h, uid, None, "", None, supporters_scarf(w, h, seed))
    # taller: the Strip at night with the silver car in a ruled arch, the scarf across its foot
    sh = min(64., h * .3)
    cx, cy, a, b = box_fit(w, h - sh * .6, 1.7, pad=3)
    cy = 3 + b
    clean = shape_pts(cx, cy, a, b, "arch", 160)
    body = vegas_scene(cx - a, cy - b, 2 * a, 2 * b, seed, "", ctx.get("date", ""), True)
    foot = f'<svg x="0" y="{_nn(h - sh)}" width="{_nn(w)}" height="{_nn(sh)}" overflow="visible">{supporters_scarf(w, sh, seed)}</svg>'
    return vignette(w, h, uid, clean, body, clean, foot)
