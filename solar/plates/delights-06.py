"""delights-06 Live from Portland, merged into Live music ahead (edition plan: small tailpiece, banner).

The tailpiece is a ticket made a banner, standing free on a transparent ground: the arched face is
the ticket, edged and bending away from the light, its stub torn along a perforation and lettered
ADMIT ONE; the marquee letters LIVE TONIGHT run across it with Parker's dog looking out as the O
(the plan's Easter egg); the ends fold back behind into swallowtails modelled dark in the folds, and
a few torn stubs lie fallen beneath. At taller sizes the club stage on show night (proscenium, spot
cans, backline with the crossed drumsticks on the kick, the crowd rim-lit, a taper's ORTF stand)
sits in a ruled oval over the ticket."""
import sys
import math
import random
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


PI, TAU = math.pi, 2 * math.pi
CR = ' shape-rendering="crispEdges"'

_n, _d = C._n, C._d
PI, TAU = math.pi, 2 * math.pi
CR = ' shape-rendering="crispEdges"'


# ------------------------------------------------------------------------------------------------
# stroke lettering (drawn as paths, never <text>)
# ------------------------------------------------------------------------------------------------

def _oval(cx, cy, rx, ry, a0=0., a1=TAU, n=14):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


_G = {
    "A": (4, [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]]),
    "B": (4, [[(0, 0), (0, 6), (3, 6), (4, 5.1), (4, 3.9), (3, 3), (0, 3)], [(0, 0), (2.8, 0), (3.7, .8), (3.7, 2.2), (2.8, 3)]]),
    "C": (4, [[(4, 1), (3, 0), (1, 0), (0, 1.2), (0, 4.8), (1, 6), (3, 6), (4, 5)]]),
    "D": (4, [[(0, 0), (0, 6), (2.4, 6), (4, 4.4), (4, 1.6), (2.4, 0), (0, 0)]]),
    "E": (3.6, [[(3.6, 0), (0, 0), (0, 6), (3.6, 6)], [(0, 3), (2.8, 3)]]),
    "G": (4, [[(4, 1), (3, 0), (1, 0), (0, 1.2), (0, 4.8), (1, 6), (3, 6), (4, 5), (4, 3.4), (2.3, 3.4)]]),
    "H": (4, [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]]),
    "I": (2, [[(1, 0), (1, 6)], [(0, 0), (2, 0)], [(0, 6), (2, 6)]]),
    "L": (3.5, [[(0, 0), (0, 6), (3.5, 6)]]),
    "M": (5, [[(0, 6), (0, 0), (2.5, 4), (5, 0), (5, 6)]]),
    "N": (4, [[(0, 6), (0, 0), (4, 6), (4, 0)]]),
    "O": (4.4, [_oval(2.2, 3, 2.2, 3, n=20)]),
    "P": (4, [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]]),
    "R": (4, [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]]),
    "S": (4, [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]]),
    "T": (4, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
    "U": (4, [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]]),
    "W": (5.4, [[(0, 0), (1.3, 6), (2.7, 2), (4.1, 6), (5.4, 0)]]),
    "Y": (4, [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]]),
    "1": (3, [[(.6, 1.2), (1.8, 0), (1.8, 6)], [(.6, 6), (3, 6)]]),
    "8": (4, [_oval(2, 1.5, 1.6, 1.5, n=16), _oval(2, 4.4, 1.9, 1.6, n=16)]),
    "9": (4, [_oval(2, 2, 2, 2, n=18), [(4, 2), (4, 4.4), (3, 6), (1, 6), (0, 5)]]),
    "*": (2.4, [[(1.2, 2.2), (2.2, 3), (1.2, 3.8), (.2, 3), (1.2, 2.2)]]),
    " ": (2.6, []),
}


_G.update({
    "V": (4, [[(0, 0), (2, 6), (4, 0)]]),
    "F": (3.6, [[(3.6, 0), (0, 0), (0, 6)], [(0, 3), (2.8, 3)]]),
    "K": (4, [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.4, 2.6), (4, 6)]]),
})


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _blk(polys):
    return "".join(_d(p, True, 0) for p in polys if len(p) > 2)


def _stick(x0, y0, x1, y1, w0, w1):
    """A tapered stick (drumstick, stand leg) as a polygon from width w0 to w1, with a bead tip."""
    a = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(a), math.cos(a)
    return [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
            (x1 + math.cos(a) * w1 * 1.2, y1 + math.sin(a) * w1 * 1.2),
            (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]


def _rings(cx, cy, rx, ry, r0, r1, pitch, a0=0., a1=TAU, n=40):
    out = []
    r = r1
    while r > r0:
        k = r / r1
        out.append(_oval(cx, cy, rx * k, ry * k, a0, a1, n))
        r -= pitch
    return out


# ------------------------------------------------------------------------------------------------
# the subject: a Portland club stage, show night
# ------------------------------------------------------------------------------------------------

def stage(fx, fy, fw, fh, seed=0, egg=True):
    rng = random.Random(seed)
    o = []
    S = min(fh / 100., fw / 140.)                   # one unit
    cx = fx + fw / 2
    yF = fy + fh * .70                              # back edge of the stage floor
    yL = fy + fh * .82                              # stage lip
    yV = fy + fh * .11                              # valance bottom

    # backdrop: a heavy black drape behind the band, in deep vertical folds (bulino rules that
    # crowd together in the troughs and part on the crests)
    lines = []
    x = fx - 2.
    while x < fx + fw + 2:
        lines.append(f"M{_n(x)},{_n(fy - 2)}V{_n(yF + 1)}")
        ph = math.sin((x - fx) / (fw / 9.) * PI)
        x += 1.5 if ph < .35 else 3.
    o.append(f'<path d="{"".join(lines)}" stroke="#000" stroke-width=".5"{CR}/>')
    dk = []
    for k in range(10):
        xk = fx + fw / 9. * (k - .5) * 1. + fw / 18.
        dk.append(_rect(xk - .6 * S, fy - 2, xk + .6 * S, yF + 1))
    o.append(f'<path d="{_blk(dk)}" fill="#000"/>')

    cv = C.Canvas()
    black = []

    # light beams from the spot cans, ruled light, cut out of the backdrop
    cans = [(-.36, rng.random() < .8), (-.15, True), (.15, True), (.36, rng.random() < .8)]
    for u, lit in cans:
        if not lit:
            continue
        sx, sy = cx + u * fw, yV + 3 * S
        tx = cx + u * fw * .25 + rng.uniform(-8, 8) * S
        beam = [(sx - 2.5 * S, sy), (sx + 2.5 * S, sy), (tx + 15 * S, yF + 6 * S), (tx - 15 * S, yF + 6 * S)]
        cv.obj([beam], 0)
        cv.hair(C.hatch_poly(beam, 0, 3, .25))

    # stage floor: planks converging on the band, ruled for depth
    floor = [(fx - 2, yF), (fx + fw + 2, yF), (fx + fw + 2, yL), (fx - 2, yL)]
    cv.obj([floor], 1.)
    vx, vy = cx, yF - (yL - yF) * 2.2
    planks = []
    for i in range(-14, 15):
        bx = cx + i * fw / 18
        t0 = (yF - vy) / (yL - vy)
        planks.append([(vx + (bx - vx) * t0, yF), (bx, yL)])
    cv.hair(planks)
    cv.hair(C.hatch_poly(floor, 0, 2, .25))
    # stage lip: a black fascia with a white nosing
    black.append(_rect(fx - 2, yL, fx + fw + 2, yL + 2.6 * S))

    # amp stacks either side of the kit
    def amp(ax, w_, h_):
        cab = _rect(ax - w_ / 2, yF + 2 * S - h_, ax + w_ / 2, yF + 2 * S)
        cv.obj([cab], 1.)
        g = _rect(ax - w_ / 2 + 2 * S, yF + 2 * S - h_ + 2 * S, ax + w_ / 2 - 2 * S, yF)
        cv.obj([g], .5)
        cv.hair(C.hatch_poly(g, 45, 2))
        cv.hair(C.hatch_poly(g, -45, 2))
        cv.line([[(ax - w_ / 2, yF + 2 * S - h_ / 2), (ax + w_ / 2, yF + 2 * S - h_ / 2)]])
        hy = yF + 2 * S - h_
        head = _rect(ax - w_ / 2, hy - h_ * .3, ax + w_ / 2, hy)
        cv.obj([head], 1.)
        cv.hair(C.hatch_poly(head, 0, 1.5, .25))
        panel = _rect(ax - w_ * .42, hy - h_ * .2, ax + w_ * .42, hy - h_ * .08)
        black.append(panel)
        for k in range(6):
            kx = ax - w_ * .36 + k * w_ * .144
            black.append(_oval(kx, hy - h_ * .26, max(.8, 1.1 * S), max(.8, 1.1 * S), n=8))
    aw, ah = fw * .16, fh * .26
    amp(cx - fw * .31, aw, ah)
    amp(cx + fw * .31, aw, ah)

    # an electric guitar on its stand, leaning, in front of the left stack
    def guitar(gx, gy, sc, lean):
        ca, sa = math.cos(lean), math.sin(lean)
        T = lambda pts: [(gx + x_ * ca - y_ * sa, gy + x_ * sa + y_ * ca) for x_, y_ in pts]
        body = []
        bouts = ((0., .38 * sc, 1.0 * sc, .86 * sc), (-.06 * sc, -.5 * sc, .78 * sc, .62 * sc))

        def inside(px, py):
            return any(((px - ex) / rx) ** 2 + ((py - ey) / ry) ** 2 <= 1 for ex, ey, rx, ry in bouts)
        for i in range(48):                     # ray-cast the union of two bouts: a waisted body
            t = TAU * i / 48
            r = 2.2 * sc
            while r > .05 * sc and not inside(r * math.cos(t), r * math.sin(t)):
                r -= .03 * sc
            body.append((r * math.cos(t), r * math.sin(t)))
        neck = T(_rect(-sc * .1, -sc * 3.5, sc * .1, -sc * .8))
        hs = T([(-sc * .13, -sc * 3.5), (sc * .13, -sc * 3.5), (sc * .2, -sc * 4.3), (-sc * .08, -sc * 4.2)])
        stand = [[(gx - sc * .9, yF + 2 * S), (gx, gy + sc * .6), (gx + sc * .9, yF + 2 * S)]]
        cv.obj([], 0)
        cv.line(stand)
        cv.obj([T(body)], 1.)
        bp = T(body)
        cv.hair([l for l in C.hatch_poly(bp, 45 + math.degrees(lean), 1.5)])
        cv.hair(C.hatch_poly(bp, -45 + math.degrees(lean), 3))
        guard = T([(x_ * .55 + sc * .12, y_ * .55 + sc * .12) for x_, y_ in body])
        cv.obj([guard], .5)
        cv.hair([q for q in [T([(-sc * .3, sc * .55), (sc * .3, sc * .55)])]])
        cv.obj([neck], .5)
        cv.hair(C.hatch_poly(neck, 90 + math.degrees(lean), 1.5))
        frets = [T([(-sc * .1, -sc * 3.5 + k * sc * .22), (sc * .1, -sc * 3.5 + k * sc * .22)]) for k in range(12)]
        cv.hair(frets)
        cv.obj([hs], .5)
        cv.hair(C.hatch_poly(hs, 0, 1.5))
        for py_ in (-sc * .35, sc * .05):
            black.append(T(_rect(-sc * .26, py_, sc * .26, py_ + sc * .14)))
        black.append(T(_rect(-sc * .3, sc * .5, sc * .3, sc * .6)))
        for k in range(3):
            black.append(T(_oval(sc * .5, sc * .45 + k * sc * .22, sc * .07, sc * .07, n=6)))
    guitar(cx - fw * .21, yF - fh * .06, fh * .07, -.22)

    # --- drum kit, centred behind the mic
    R = fh * .14                                    # kick drum radius
    ky = yF + 3 * S - R
    kx = cx + 3 * S
    # hi-hat (left) and ride cymbal (right) on their stands
    hhx, hhy = kx - R * 1.75, ky - R * 1.15
    rdx, rdy = kx + R * 1.9, ky - R * 1.35
    cv.obj([], 0)
    cv.line([[(hhx, hhy), (hhx, yF + 2 * S)], [(hhx - 4 * S, yF + 2 * S), (hhx, yF - 3 * S), (hhx + 4 * S, yF + 2 * S)]])
    cv.line([[(rdx, rdy), (rdx - 2 * S, yF + 2 * S)], [(rdx - 6 * S, yF + 2 * S), (rdx - 2 * S, yF - 3 * S), (rdx + 3 * S, yF + 2 * S)]])
    # toms
    for tx_, ty_, tr in ((kx - R * .45, ky - R * 1.08, R * .36), (kx + R * .5, ky - R * 1.12, R * .4)):
        body = _rect(tx_ - tr, ty_, tx_ + tr, ty_ + tr * .9) + []
        shell = [(tx_ - tr, ty_)] + _oval(tx_, ty_ + tr * .9, tr, tr * .28, 0, PI, 12)[::-1][::-1][::-1] + [(tx_ + tr, ty_)]
        shell = [(tx_ - tr, ty_), (tx_ + tr, ty_)] + _oval(tx_, ty_ + tr * .9, tr, tr * .28, 0, PI, 14)
        cv.obj([shell], 1.)
        cv.hair([l for l in C.hatch_poly(shell, 90, 1.5) if l[0][0] > tx_ + tr * .25 or l[0][0] < tx_ - tr * .8])
        cv.hair([l for l in C.hatch_poly(shell, 90, 3) if tx_ - tr * .8 <= l[0][0] <= tx_ + tr * .25])
        top = _oval(tx_, ty_, tr, tr * .28, n=24)
        cv.obj([top], 1.)
        cv.hair([_oval(tx_, ty_, tr * .8, tr * .2, PI * .9, PI * 1.9, 10)])
    # floor tom, right
    ftx, fty, ftr = kx + R * 1.35, yF - R * .95, R * .42
    shell = [(ftx - ftr, fty), (ftx + ftr, fty)] + _oval(ftx, fty + R * .85, ftr, ftr * .28, 0, PI, 14)
    cv.obj([shell], 1.)
    cv.hair(C.hatch_poly(shell, 90, 1.5))
    cv.obj([_oval(ftx, fty, ftr, ftr * .28, n=24)], 1.)
    # kick drum: shell ring, lugs, resonant head
    ring = _oval(kx, ky, R, R, n=64)
    cv.obj([ring], 1.5)
    cv.hair([q for q in _rings(kx, ky, R, R, R * .88, R - .8, 1.5)])
    lugs = []
    for i in range(10):
        a = TAU * (i + .5) / 10
        lugs.append([(kx + R * .9 * math.cos(a), ky + R * .9 * math.sin(a)), (kx + R * 1.06 * math.cos(a), ky + R * 1.06 * math.sin(a))])
    cv.heavy(lugs)
    head = _oval(kx, ky, R * .86, R * .86, n=56)
    cv.obj([head], 1.)
    # the head is lit from the left beam: light ruling, darker toward the right edge
    cv.hair(C.hatch_poly(head, 0, 3, .25))
    cv.hair([l for l in C.hatch_poly(head, 0, 3, 1.75) if max(p[0] for p in l) > kx + R * .35])
    cv.hair([_oval(kx, ky, R * .78, R * .78, -PI * .4, PI * .45, 18)])
    if egg:
        # Easter egg: Parker's crossed drumsticks on the kick head
        L = R * .62
        for s_ in (-1, 1):
            st = _stick(kx - s_ * L * .7, ky + L * .7, kx + s_ * L * .7, ky - L * .7, max(1.6, 2.2 * S), max(1, 1.2 * S))
            cv.obj([st], 1.)
    # cymbals, in front of the stands, lathe-turned
    for (yx, yy, yr, two) in ((hhx, hhy, R * .62, True), (rdx, rdy, R * .95, False)):
        for dy in ((0., 1.6 * S) if two else (0.,)):
            cym = _oval(yx, yy + dy, yr, max(1.8, yr * .16), n=36)
            cv.obj([cym], 1.)
            cv.hair([l for l in C.hatch_poly(cym, 0, 1.5) if l[0][1] > yy + dy])
            cv.hair([[(yx - yr * k, yy + dy), (yx + yr * k, yy + dy)] for k in (.55, .3)])
            black.append(_oval(yx, yy + dy - .4 * S, yr * .14, max(1.1, yr * .1), n=10))

    # --- the singer's mic: a vintage chromed capsule on a tall stand, front and centre
    mx, my = cx - fw * .07, fy + fh * .44
    mh, mw = fh * .17, fh * .1
    cv.obj([], 0)
    st = _stick(mx, yL - 1, mx, my + mh * .6, max(1.4, 1.8 * S), max(1.2, 1.4 * S))
    cv.obj([st], 1.)
    base = [(mx - 9 * S, yL + 1), (mx - 1 * S, yL - 6 * S), (mx + 1 * S, yL - 6 * S), (mx + 9 * S, yL + 1)]
    cv.obj([base], 1.)
    cv.hair(C.hatch_poly(base, 0, 1.5))
    yoke = _rect(mx - mw * .62, my + mh * .2, mx + mw * .62, my + mh * .62)
    cv.obj([[(mx - mw * .62, my + mh * .2), (mx - mw * .5, my + mh * .2), (mx - mw * .5, my + mh * .5),
             (mx + mw * .5, my + mh * .5), (mx + mw * .5, my + mh * .2), (mx + mw * .62, my + mh * .2),
             (mx + mw * .62, my + mh * .62), (mx - mw * .62, my + mh * .62)]], 1.)
    cv.hair(C.hatch_poly(yoke, 0, 1.5))
    caps = []
    n = 28
    for i in range(n + 1):          # rounded-shield capsule, wide at the shoulders
        t = i / n
        y_ = my - mh * .5 + mh * t
        wd = mw * .5 * (.55 + .45 * math.sin(PI * min(1, t * 1.25)) ** .5)
        caps.append((mx + wd, y_))
    caps = caps + [(2 * mx - x_, y_) for x_, y_ in caps[::-1]]
    cv.obj([caps], 1.)
    # grille: horizontal chrome bars, black slots between; centre rib, shaded right side
    for y_ in [my - mh * .42 + k * max(1.5, mh * .055) for k in range(30)]:
        if y_ > my + mh * .44:
            break
        cv.line([[(mx - mw * .5, y_), (mx + mw * .5, y_)]])
    cv.obj([_rect(mx - mw * .06, my - mh * .5, mx + mw * .06, my + mh * .5)], .5)
    cv.hair([[(mx - mw * .02, my - mh * .48), (mx - mw * .02, my + mh * .48)]])
    cv.obj([caps[:n + 1] + [(mx + mw * .3, my + mh * .5), (mx + mw * .3, my - mh * .5)]], 0)
    for y_ in [my - mh * .42 + k * max(1.5, mh * .055) for k in range(30)]:
        if y_ > my + mh * .44:
            break
        cv.heavy([[(mx + mw * .3, y_), (mx + mw * .5, y_)]])
    cv.obj([], 0)
    cv.line([caps + [caps[0]]])

    # --- curtains: gathered, tied back, deep folds
    def curtain(side):
        e = fx - 3 if side < 0 else fx + fw + 3
        tie = fy + fh * .52
        wt, wk, wb = fw * .17, fw * .045, fw * .12

        def inner(y_):
            if y_ < tie:
                t = max(0., (y_ - fy) / (tie - fy))
                ww = wt + (wk - wt) * (t ** 1.5)
            else:
                t = min(1., (y_ - tie) / (fy + fh - tie))
                ww = wk + (wb - wk) * (1 - (1 - t) ** 2)
            return e - side * ww
        ys = [fy - 3 + (fh + 6) * i / 60 for i in range(61)]
        poly = [(e, ys[0])] + [(inner(y_), y_) for y_ in ys] + [(e, ys[-1])]
        cv.obj([poly], 1.)
        NF = 7
        lines = []
        for j in range(NF * 5):
            t = (j + .5) / (NF * 5)
            ph = (t * NF) % 1
            if ph < .28:
                continue                     # highlight crest of the fold
            lines.append([(e + (inner(y_) - e) * t, y_) for y_ in ys])
            if ph > .7:
                lines.append([(e + (inner(y_) - e) * (t + .5 / (NF * 5)), y_) for y_ in ys])
        cv.hair(lines)
        # tie-back cord and tassel
        tx_ = inner(tie)
        band = [(e, tie - 2.2 * S), (tx_ - side * 1.5 * S, tie - 2.2 * S), (tx_ - side * 1.5 * S, tie + 2.2 * S), (e, tie + 2.2 * S)]
        cv.obj([band], 1.)
        cv.hair(C.hatch_poly(band, 60 * side, 1.5))
        tas = [(tx_ - side * 1 * S, tie), (tx_ - side * 4 * S, tie + 6 * S), (tx_ + side * 2 * S, tie + 6 * S)]
        cv.obj([tas], 1.)
        cv.hair(C.hatch_poly(tas, 90, 1.5))
    curtain(-1)
    curtain(1)

    # --- valance: swagged, scalloped, fringed, with the spot cans hanging under it
    cv.obj([], 0)
    for u, lit in cans:
        sx = cx + u * fw
        can = [(sx - 3 * S, yV - 1), (sx + 3 * S, yV - 1), (sx + 3.6 * S, yV + 5 * S), (sx - 3.6 * S, yV + 5 * S)]
        cv.obj([can], 1.)
        cv.hair(C.hatch_poly(can, 90, 1.5))
        if lit:
            black.append(_oval(sx, yV + 5 * S, 3.4 * S, 1.2 * S, n=12))
    nsw = 5
    sw = (fw + 6) / nsw
    edge = []
    for i in range(nsw * 16 + 1):
        x_ = fx - 3 + (fw + 6) * i / (nsw * 16)
        t = ((x_ - fx + 3) / sw) % 1
        edge.append((x_, yV - 3 * S + 6 * S * math.sin(PI * t)))
    val = [(fx - 3, fy - 3), (fx + fw + 3, fy - 3)] + edge[::-1]
    cv.obj([val], 1.)
    sw_lines = []
    for k in range(1, 6):
        q = []
        for x_, y_ in edge:
            t = ((x_ - fx + 3) / sw) % 1
            q.append((x_, y_ - k * 1.6 * S * (.4 + .6 * math.sin(PI * t))))
        sw_lines.append(q)
    cv.hair(sw_lines)
    cv.hair([l for l in C.hatch_poly(val, 0, 1.5) if l[0][1] < yV - 7 * S])
    cv.hair([[(x_, y_), (x_, y_ + 2.4 * S)] for x_, y_ in edge[::2]])
    o.append(cv.svg())

    # --- the crowd in silhouette, hands up, and the taper's stand rising out of it
    crowd_y = yL + fh * .045
    rimw = []
    hd = []
    for row, (dy, rs) in enumerate(((0., 1.), (5.5, 1.15))):
        xx = fx - 4 + rng.uniform(0, 6) * S
        while xx < fx + fw + 6:
            r = rng.uniform(3.2, 4.4) * S * rs
            yy = crowd_y + dy * S + rng.uniform(-1.5, 2.5) * S
            hd.append(_oval(xx, yy, r * .82, r, n=14))
            hd.append(_oval(xx, yy + r * 2.0, r * 2.0, r * 1.25, n=18))
            # rim light from the stage on the crown and the shoulders, both rows
            rimw.append(_oval(xx - r * .1, yy - r * .1, r * .62, r * .82, PI * 1.05, PI * 1.6, 6))
            rimw.append(_oval(xx, yy + r * 2.0, r * 1.75, r * 1.0, PI * 1.08, PI * 1.42, 6))
            rimw.append(_oval(xx, yy + r * 2.0, r * 1.75, r * 1.0, PI * 1.62, PI * 1.9, 6))
            if row == 1:
                rimw.append(_oval(xx, yy + r * 2.0, r * 1.3, r * .62, PI * 1.15, PI * 1.85, 8))
            if row == 0:
                if rng.random() < .3:
                    side = rng.choice((-1, 1))
                    ax_ = xx + side * r * 1.4
                    hand_y = yy - rng.uniform(8, 13) * S
                    hd.append(_stick(ax_, yy + r * 1.2, ax_ + side * 2 * S, hand_y, 2.2 * S, 1.6 * S))
                    hd.append(_oval(ax_ + side * 2 * S, hand_y - .8 * S, 1.4 * S, 1.8 * S, n=8))
                    rimw.append([(ax_ - 1.0 * S, yy), (ax_ + side * 2 * S - 1.0 * S, hand_y + 1 * S)])
            xx += r * rng.uniform(1.8, 2.5)
    hd.append(_rect(fx - 4, crowd_y + 9 * S, fx + fw + 4, fy + fh + 4))
    tx_ = cx + fw * .235
    top_ = fy + fh * .36
    hd.append(_rect(tx_ - .8, top_, tx_ + .8, crowd_y + 4 * S))
    hd.append(_rect(tx_ - 11 * S, top_ - .8, tx_ + 11 * S, top_ + .8))
    for s_ in (-1, 1):   # a pair of pencil condensers in ORTF, the taper's signature
        hd.append(_stick(tx_ + s_ * 10 * S, top_ + 1, tx_ + s_ * 4 * S, top_ - 12 * S, 2.6 * S, 2.2 * S))
        hd.append(_rect(tx_ + s_ * 10 * S - 1.2 * S, top_ - 2, tx_ + s_ * 10 * S + 1.2 * S, top_ + 2))
    o.append(f'<path d="{_blk(black)}{_blk(hd)}" fill="#000" stroke="none"/>')
    # rim light from the stage on the front row; the dark house behind them ruled, never solid
    o.append(f'<path d="{"".join(_d(p, False, .2) for p in rimw)}" stroke="#fff" stroke-width="1" fill="none" stroke-linecap="round"/>')
    floor_d = _rect(fx - 4, crowd_y + 14 * S, fx + fw + 4, fy + fh + 4)
    o.append(f'<path d="{C.hatch_d(floor_d, 0, 3, 1.25)}" stroke="#fff" stroke-width="1"{CR}/>')
    # the room behind them is not empty paper: rim light on shoulders
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# a reel of tape (short plates' medallion)
# ------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------
# layouts (house layouts, re-cut for this page: no blank white anywhere)
# ------------------------------------------------------------------------------------------------

def ticket_ribbon(w, h, seed):
    """the tailpiece: a ticket made a banner. The face is the ticket, arched, its stub torn along a
    perforation and lettered ADMIT ONE; the marquee letters LIVE TONIGHT run across it with Parker's
    dog looking out as the O; the ends fold back behind into swallowtails, modelled dark in the folds"""
    Wd = min(w - 4, h * 5.6)
    cx, cy = w / 2, h * .46
    fw, fh = Wd * .74, h * .5
    sag = h * .1

    def F(u, v):
        return (cx + u * fw / 2, cy + v * fh / 2 - sag * (1 - u * u))
    cv = Canvas()
    # the tails behind, each end folded back and notched
    for sd in (-1, 1):
        x_in, x_out = cx + sd * fw * .38, cx + sd * Wd / 2
        dy = h * .2
        yt = cy - fh / 2 + dy
        yb = cy + fh / 2 + dy
        notch = (x_out - sd * Wd * .06, (yt + yb) / 2)
        tail = [(x_in, yt), (x_out, yt), notch, (x_out, yb), (x_in, yb)]
        cv.obj([tail], 1.)
        tone_hatch(cv, tail, lambda x, y, sd=sd: .25 + .55 * abs(x - cx) / (Wd / 2) + .25 * (y - yt) / (yb - yt), 90 + sd * 20, 1.5, .7)
        cv.line([(x_in + sd * 2, yt + 1.6), (x_out - sd * 1, yt + 1.6)])
        # the fold: a dark triangle where the tail turns under the face
        fx = cx + sd * fw / 2
        fold = [(fx, cy + fh / 2), (fx - sd * fw * .06, cy + fh / 2 + dy), (fx, cy + fh / 2 + dy)]
        fold = [F(sd, 1), (F(sd, 1)[0] - sd * fw * .07, yb), (F(sd, 1)[0], yb)]
        cv.obj([fold], 1.)
        tone_hatch(cv, fold, lambda x, y: .95, 45 * sd, 1.5, .5)
    # the face of the ticket
    face = [F(-1 + 2 * i / 40, -1) for i in range(41)] + [F(1 - 2 * i / 40, 1) for i in range(41)]
    cv.obj([face], 1.5)
    # paper bending over the arch: the edges turn away from the light
    tone_hatch(cv, face, lambda x, y: max(0., abs((y - (cy - sag * (1 - ((x - cx) / (fw / 2)) ** 2))) / (fh / 2)) - .62) * 2.2,
               0., 1.5, None)
    inner = [F(-.97 + 1.94 * i / 40, -.8) for i in range(41)] + [F(.97 - 1.94 * i / 40, .8) for i in range(41)]
    cv.hair(inner + [inner[0]])
    # the stub: a perforation, the stub's own border
    us = .62
    for i in range(int(fh / 2.2)):
        v = -.92 + 1.84 * i / max(1, int(fh / 2.2) - 1)
        x, y = F(us, v)
        cv.obj([_ell(x, y, .6, .6, 6)[:-1]], .5)
    o = [cv.svg()]
    holes = []
    cap_h = fh * .62
    line = [F(-.93 + (us - .07 + .93) * i / 20, .04) for i in range(21)]
    o.append(motto(line, "LIVE T@NIGHT", cap_h, 1.5, holes, .96))
    stub = [F(us + .04 + (.96 - us - .04) * i / 10, -.3) for i in range(11)]
    stub2 = [F(us + .04 + (.96 - us - .04) * i / 10, .35) for i in range(11)]
    o.append(motto(stub, "ADMIT", fh * .32, .5, None, .9))
    o.append(motto(stub2, "ONE", fh * .32, .5, None, .9))
    cv2 = Canvas()
    for hx, hy, cap in holes:
        fig_dogface(cv2, hx, hy, cap * .55)
    o.append(cv2.svg())
    # a scatter of torn ticket stubs fallen in front, as at the end of a night
    cv3 = Canvas()
    rng = random.Random(seed)
    for k in range(3):
        sx = cx + rng.choice((-1, 1)) * Wd * rng.uniform(.22, .44)
        sy = h * rng.uniform(.84, .92)
        a = rng.uniform(-.5, .5)
        sw_, sh_ = h * .16, h * .09
        pts = [(sx + dx * math.cos(a) - dy * math.sin(a), sy + dx * math.sin(a) + dy * math.cos(a))
               for dx, dy in ((-sw_ / 2, -sh_ / 2), (sw_ / 2, -sh_ / 2), (sw_ / 2, sh_ / 2), (-sw_ / 2, sh_ / 2))]
        cv3.obj([pts], .5)
        tone_hatch(cv3, pts, lambda x, y: .3, math.degrees(a) + 80, 1.5, None)
    o.insert(0, cv3.svg())
    return "".join(o), (cx, cy, Wd)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 6
    uid = f"lv{int(w)}x{int(h)}"
    if h <= 110:
        body, _ = ticket_ribbon(w, h, seed)
        return vignette(w, h, uid, None, "", None, body)
    # taller: the club stage on show night in an oval, the ticket banner across its foot
    bh = min(64., h * .3)
    cx, cy, a, b = box_fit(w, h - bh * .55, 1.6, pad=3)
    cy = 3 + b
    sil = ragged(shape_pts(cx, cy, a, b, "oval", 160), 3., seed)
    body = stage(cx - a, cy - b, 2 * a, 2 * b, seed, True)
    rib, _ = ticket_ribbon(w, bh, seed)
    rib = f'<svg x="0" y="{_nn(h - bh)}" width="{_nn(w)}" height="{_nn(bh)}" overflow="visible">{rib}</svg>'
    return vignette(w, h, uid, sil, body, shape_pts(cx, cy, a, b, "oval", 160), rib)
