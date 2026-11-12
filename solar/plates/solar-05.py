"""solar-05 'A month of solar' (edition plan: headpiece, about 8%, a banner).

The headpiece stands free on a transparent ground: thirty split-cedar fence posts across a strip of
tilled field, set in fives like tally marks (four upright and the fifth a brace laid across them),
one post for each of the last thirty days; a low day's post stands shorter and leans. The posts are
modelled in burin tone, each throwing its shadow toward us from a low November sun behind the middle,
the wire strung post to post, grass at their feet. Easter egg (the plan's): a dog's paw print in the
dirt. At taller sizes Parker's barn roof under the sun sits in a ruled lunette above the fence."""
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


_n, _d = C._n, C._d
PI = math.pi
CR = ' shape-rendering="crispEdges"'
MON = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


# ------------------------------------------------------------------------------------------------
# page facts: the thirty days, which were low, the month's total
# ------------------------------------------------------------------------------------------------

def _facts(ctx):
    ctx = ctx or {}
    try:
        end = datetime.date.fromisoformat(ctx.get("date", "")[:10])
    except ValueError:
        end = datetime.date(2026, 11, 11)
    days = [end - datetime.timedelta(days=29 - i) for i in range(30)]
    s = ctx.get("sample", "") or ""
    low = set()
    m = re.search(r"Low days:\s*([^.]*)", s)
    if m:
        for mm, dd in re.findall(r"([A-Z][a-z]{2})\s+(\d{1,2})", m.group(1)):
            if mm in MON:
                for d in days:
                    if d.month == MON[mm] and d.day == int(dd):
                        low.add(d)
    else:
        rng = random.Random(end.toordinal())
        low = {d for d in days if rng.random() < .25}
    k = re.search(r"Past (\d+) days:\s*([\d,]+)\s*kWh", s)
    label = f"{k.group(2)} KWH IN {k.group(1)} DAYS" if k else "A MONTH OF SUN"
    return days, [d in low for d in days], label


# ------------------------------------------------------------------------------------------------
# a small engraved roman for the ribbon (strokes on a 4 x 6 grid)
# ------------------------------------------------------------------------------------------------

_O = [(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]
_P = [(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]
GLYPH = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 4), (3.2, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.5), (2.2, 3.5)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 0), (1, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.8)], [(1.4, 2.6), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2.5, 4.5), (5, 0), (5, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [_O],
    "P": [_P],
    "R": [_P, [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1.2, 6), (2.5, 2), (3.8, 6), (5, 0)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "0": [_O],
    "1": [[(.6, 1.2), (2, 0), (2, 6)], [(.8, 6), (3.2, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1.5, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "5": [[(4, 0), (.4, 0), (0, 3), (3, 2.6), (4, 3.6), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "6": [[(3.5, 0), (1.5, 0), (0, 2), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (.5, 3)]],
    "7": [[(0, 0), (4, 0), (1.5, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3)]],
    "9": [[(3.5, 3), (1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 4), (2.5, 6), (.5, 6)]],
    ",": [[(.6, 5.4), (.6, 6.2), (0, 7.2)]],
}


# ------------------------------------------------------------------------------------------------
# geometry helpers
# ------------------------------------------------------------------------------------------------

def _circ(cx, cy, r, n=40, a0=0., a1=2 * PI):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _bil(q, u, v):
    """Bilinear point in quad q = (p00 eave-left, p01 ridge-left, p11 ridge-right, p10 eave-right)."""
    a, b, c, d = q
    x = (1 - u) * ((1 - v) * a[0] + v * b[0]) + u * ((1 - v) * d[0] + v * c[0])
    y = (1 - u) * ((1 - v) * a[1] + v * b[1]) + u * ((1 - v) * d[1] + v * c[1])
    return x, y


def _cloud(cx, base, w, h, rng):
    """A cumulus: (outline, bump list)."""
    n = max(3, int(w / (h * .7)))
    bumps = []
    for i in range(n):
        t = (i + .5) / n
        r = h * (.42 + .5 * math.sin(PI * t)) * rng.uniform(.85, 1.1)
        bumps.append((cx - w / 2 + w * t, base - r * .55, r))
    pts = []
    m = 60
    x0, x1 = cx - w / 2 - h * .25, cx + w / 2 + h * .25
    for i in range(m + 1):
        x = x0 + (x1 - x0) * i / m
        y = base
        for bx, by, r in bumps:
            if abs(x - bx) < r:
                y = min(y, by - math.sqrt(r * r - (x - bx) ** 2))
        pts.append((x, min(y, base - .5)))
    pts += [(x1 - h * .3, base + h * .06), (x0 + h * .3, base + h * .06)]
    return pts, bumps


def _sky(bx, by, bw, bh, yh, sx, sy, rg):
    """Crisp ruled sky: 1 px lines high and far from the sun, 0.5 px near it, none in its glow."""
    heavy, light = [], []
    y = math.floor(by)
    top_dark = by + (yh - by) * .42
    while y < yh + 2:
        yc = y
        dy = yc - sy
        segs = [(bx - 2, bx + bw + 2)]

        def cut(segs, r):
            if abs(dy) >= r:
                return segs, []
            hw = math.sqrt(r * r - dy * dy)
            a, b = sx - hw, sx + hw
            out, inside = [], []
            for s0, s1 in segs:
                if s1 <= a or s0 >= b:
                    out.append((s0, s1))
                else:
                    if s0 < a:
                        out.append((s0, a))
                    if s1 > b:
                        out.append((b, s1))
                    inside.append((max(s0, a), min(s1, b)))
            return out, inside

        outer, mid = cut(segs, rg * 1.9)
        for s0, s1 in outer:
            (heavy if yc < top_dark else light).append((yc, s0, s1))
        for s0, s1 in mid:
            light.append((yc, s0, s1))
        y += 2
    dh = "".join(f"M{_n(a)},{_n(yc + .5)}H{_n(b)}" for yc, a, b in heavy if b - a > .5)
    dl = "".join(f"M{_n(a)},{_n(yc + .25)}H{_n(b)}" for yc, a, b in light if b - a > .5)
    o = ""
    if dh:
        o += f'<path d="{dh}" stroke="#000" stroke-width="1"{CR}/>'
    if dl:
        o += f'<path d="{dl}" stroke="#000" stroke-width=".5"{CR}/>'
    return o


# ------------------------------------------------------------------------------------------------
# the vignette: barn roof of panels, low November sun of thirty rays, Mt. Hood, the Columbia
# ------------------------------------------------------------------------------------------------

def _dog(cv, x, y, s):
    """Parker's dog, asleep, curled nose to tail (facing left)."""
    body = C._ell_pts(x, y - 3.2 * s, 7 * s, 3.6 * s, 30)
    cv.obj([body], .5)
    for k in (.72, .45):
        cv.hair(C._ell_pts(x + .6 * s, y - 3.0 * s, 7 * s * k, 3.6 * s * k, 20, PI * 1.05, PI * 1.95))
    for i in range(7):
        a = PI * (1.1 + .8 * i / 6)
        r1, r2 = .55, .95
        cv.hair([(x + 7 * s * r1 * math.cos(a), y - 3.2 * s + 3.6 * s * r1 * math.sin(a)),
                 (x + 7 * s * r2 * math.cos(a + .08), y - 3.2 * s + 3.6 * s * r2 * math.sin(a + .08))])
    cv.hair(C.hatch_poly(C._ell_pts(x, y - 2.2 * s, 6.4 * s, 2.4 * s, 20)[:-1], 0, 1.5, .25))
    # tail wrapping the front
    tail = [(x + 6.5 * s - 9 * s * t, y - .4 * s - 1.4 * s * math.sin(PI * t)) for t in [i / 10 for i in range(11)]]
    cv.line(tail)
    # head tucked on the tail, ear flopped
    hx, hy = x - 5.2 * s, y - 2.4 * s
    head = C._ell_pts(hx, hy, 2.9 * s, 2.3 * s, 20)
    cv.obj([head], .5)
    cv.hair(C.hatch_poly(head[:-1], 45, 1.5))
    ear = [(hx + .2 * s, hy - 2 * s), (hx + 2.6 * s, hy - 1.2 * s), (hx + 1.8 * s, hy + 1.2 * s)]
    cv.obj([ear], .5)
    cv.line([(hx + .8 * s, hy - 1.2 * s), (hx + 1.9 * s, hy + .6 * s)])
    cv.heavy([(hx - 2.7 * s, hy + .2 * s), (hx - 2.4 * s, hy + .5 * s)])  # nose


def _scene(bx, by, bw, bh, clip_d, facts, seed, uid):
    days, low, _ = facts
    rng = random.Random(seed)
    S = max(.2, min(bw, bh) / 200.)
    small = S < .45
    yh = by + bh * .55
    R = max(4., 18 * S)
    sx, sy = bx + bw * .34, yh - R * 1.15 - 4 * S
    rg = R * (2.7 if not small else 2.4)
    o = [f'<clipPath id="{uid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{uid})">',
         f'<path d="M{_n(bx - 2)},{_n(by - 2)}h{_n(bw + 4)}v{_n(bh + 4)}h{_n(-bw - 4)}z" fill="#fff" stroke="none"/>',
         _sky(bx, by, bw, bh, yh, sx, sy, rg)]
    cv = C.Canvas()

    # sun: glow, thirty rays (one a day: long for a good day, a stub for a low one)
    n = len(days)
    a0, a1 = math.radians(186), math.radians(354)
    star = []
    da = (a1 - a0) / (n - 1)
    for i in range(n):
        rr = (rg * .98 if not low[i] else R * 1.25 + (rg - R * 1.25) * .32 + 2 * (1.6 * S + 1) + 2) + 1.5
        a = a0 + da * i
        for t in (-.5, -.2, .2, .5):
            r2 = rr if abs(t) < .3 else (rr + R * 1.6) / 2 if not low[i] else rr
            star.append((sx + r2 * math.cos(a + t * da), sy + r2 * math.sin(a + t * da)))
    star += [(sx + R * 1.3 * math.cos(a), sy + R * 1.3 * math.sin(a)) for a in [a1 + .5 * da + k * .2 for k in range(int((2 * PI - (a1 - a0) - da) / .2) + 1)]]
    cv.obj([star], 0)
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        ca, sa = math.cos(a), math.sin(a)
        if low[i]:
            r1 = R * 1.25 + (rg - R * 1.25) * .32
            cv.hair([(sx + R * 1.2 * ca, sy + R * 1.2 * sa), (sx + r1 * ca, sy + r1 * sa)])
            if not small:  # a little cloud-puff at the end of a low day's ray
                cv.obj([_circ(sx + (r1 + 1.6 * S + 1) * ca, sy + (r1 + 1.6 * S + 1) * sa, 1.2 + 1.1 * S, 10)[:-1]], .5)
                cv.obj([], 0)
        else:
            r1 = rg * .96
            wdg = .045 if not small else .03
            tri = [(sx + R * 1.18 * math.cos(a - wdg), sy + R * 1.18 * math.sin(a - wdg)),
                   (sx + r1 * ca, sy + r1 * sa),
                   (sx + R * 1.18 * math.cos(a + wdg), sy + R * 1.18 * math.sin(a + wdg))]
            cv.line([(sx + R * 1.18 * ca, sy + R * 1.18 * sa), (sx + r1 * ca, sy + r1 * sa)])
            if not small:
                cv.hair(tri)
        if i < n - 1 and not small:  # short flame between rays
            b = a + (a1 - a0) / (n - 1) / 2
            r2 = R * (1.55 if i % 2 else 1.8)
            cv.hair([(sx + R * 1.2 * math.cos(b), sy + R * 1.2 * math.sin(b)), (sx + r2 * math.cos(b), sy + r2 * math.sin(b))])
    disc = _circ(sx, sy, R, 48)[:-1]
    cv.obj([disc], 1.5 if not small else 1.)
    for k in range(1, 5):
        rr = R - 1.5 - 2 * (k - 1)
        if rr > R * .55:
            cv.hair(_circ(sx, sy, rr, 40, PI * .1, PI * .9 if k > 2 else PI * 1.9))
    cv.hair(C.hatch_poly(_circ(sx, sy, R * .62, 30)[:-1], 0, 3, .25))

    # clouds of the low days
    if not small:
        for (cxf, cyf, wf) in ((.06, .30, .34), (.86, .40, .30)):
            pts, bumps = _cloud(bx + bw * cxf, by + (yh - by) * cyf + 10 * S, bw * wf, 15 * S, rng)
            cv.obj([pts], .5)
            base = by + (yh - by) * cyf + 10 * S
            for bxx, byy, r in bumps:
                cv.hair(C._ell_pts(bxx + r * .1, byy + r * .1, r * .75, r * .75, 20, PI * .05, PI * .75))
            under = [(p[0], max(p[1], base - 6 * S)) for p in pts[:61]] + [pts[-2], pts[-1]]
            cv.hair(C.hatch_poly(under, 0, 2, .25))
            cv.hair(C.hatch_poly(pts, 0, 3, 1.25))
            cv.hair(C.hatch_poly(under, 45, 3))

    # Mt. Hood
    mx, mtop = bx + bw * .77, yh - bh * .27
    hw = bw * .27
    mpts = [(mx - hw, yh + 4), (mx - hw * .55, yh - (yh - mtop) * .35), (mx - hw * .22, yh - (yh - mtop) * .78),
            (mx - hw * .05, mtop + 1), (mx + hw * .02, mtop), (mx + hw * .07, mtop + 1.5 * S),
            (mx + hw * .25, yh - (yh - mtop) * .74), (mx + hw * .6, yh - (yh - mtop) * .3), (mx + hw, yh + 4)]
    cv.obj([mpts], .5)
    snow = mtop + (yh - mtop) * .5
    # shaded east face
    east = [(mx + hw * .02, mtop), (mx + hw * .07, mtop + 1.5 * S), (mx + hw * .25, yh - (yh - mtop) * .74),
            (mx + hw * .6, yh - (yh - mtop) * .3), (mx + hw, yh + 4), (mx + hw * .1, yh + 4)]
    cv.hair(C.hatch_poly(east, 45, 2))
    if not small:
        cv.hair(C.hatch_poly(east, -45, 3))
    # gullies down the snow on the lit face
    cv.hair(C.hatch_poly([(mx - hw * .55, yh - (yh - mtop) * .35), (mx - hw * .22, yh - (yh - mtop) * .78),
                           (mx - hw * .05, mtop + 1), (mx + hw * .02, mtop), (mx + hw * .02, yh), (mx - hw * .55, yh)], -60, 3))
    for k in range(11):
        t = (k + .5) / 11
        x0 = mx - hw * .04 + hw * .1 * t
        x1 = mx - hw * (.62 - .7 * t)
        cv.hair([(x0, mtop + 2 * S), (x0 + (x1 - x0) * .4 + rng.uniform(-1, 1) * S, mtop + (snow - mtop) * .55),
                 (x1, snow + rng.uniform(-2, 2) * S)])
    # forested flanks below the snow line
    flank = [(mx - hw, yh + 4), (mx - hw * .55, yh - (yh - mtop) * .35)]
    jag = []
    for k in range(13):
        t = k / 12
        jag.append((mx - hw * .55 + hw * 1.15 * t, snow + (yh - snow) * .25 * math.sin(t * 9) ** 2 + (3 * S if k % 2 else -2 * S)))
    flank = [(mx - hw, yh + 4)] + [p for p in jag] + [(mx + hw, yh + 4)]
    cv.hair(C.hatch_poly(flank, -30, 3))

    # treeline of cottonwoods and firs along the far bank
    tl = []
    x = bx - 4
    while x < bx + bw + 6:
        if rng.random() < .3:
            hgt = rng.uniform(8, 14) * S
            tl += [(x, yh), (x + 2.5 * S, yh - hgt), (x + 5 * S, yh)]
            x += 5 * S
        else:
            r = rng.uniform(3.5, 7) * S
            tl += [(x + r - r * math.cos(PI * t / 8), yh - r * .9 * math.sin(PI * t / 8) - 2 * S) for t in range(9)]
            x += 2 * r * .85
    tree = [(bx - 4, yh + 6 * S)] + tl + [(bx + bw + 6, yh + 6 * S)]
    cv.obj([tree], .5)
    cv.hair(C.hatch_poly(tree, 45, 2))
    cv.hair(C.hatch_poly(tree, -45, 3))

    # the Columbia, with the sun's road laid on it
    ry0, ry1 = yh + 6 * S, yh + 18 * S
    river = [(bx - 4, ry0), (bx + bw + 4, ry0), (bx + bw + 4, ry1), (bx - 4, ry1)]
    cv.obj([river], 0)
    yy = math.floor(ry0) + 1
    while yy < ry1:
        x = bx - 4
        while x < bx + bw + 4:
            near = abs(x - sx) < R * (.8 + 1.5 * (yy - ry0) / max(1, ry1 - ry0))
            seg = rng.uniform(2, 5) * S + (1 if near else rng.uniform(14, 40) * S)
            gap = rng.uniform(1.5, 2.5) * (2.2 if near else 1) * max(S, .5)
            cv.hair([(x, yy + .25), (x + seg, yy + .25)])
            x += seg + gap
        yy += 2
    cv.line([(bx - 4, ry0), (bx + bw + 4, ry0)])

    # Sauvie Island fields: distant ruled, then furrows running to the sun
    ft = ry1
    bot = by + bh + 2
    field = [(bx - 4, ft), (bx + bw + 4, ft), (bx + bw + 4, bot), (bx - 4, bot)]
    cv.obj([field], .5)
    step = max(4., 10 * S)
    t0 = 3.2 / step
    yf = yh + (bot - yh) * t0
    if yf > ft:
        cv.hair(C.hatch_poly([(bx - 4, ft), (bx + bw + 4, ft), (bx + bw + 4, yf), (bx - 4, yf)], 0, 2, .25))
    span = bw * 3
    k = 0
    xb = sx - span / 2
    while xb < sx + span / 2:
        p0 = (sx + (xb - sx) * t0, max(yf, ft))
        t1 = (max(yf, ft) - yh) / (bot - yh)
        p0 = (sx + (xb - sx) * t1, yh + (bot - yh) * t1)
        (cv.line if k % 2 == 0 else cv.hair)([p0, (xb, bot)])
        xb += step
        k += 1

    # the barn and its 24.6 kW roof
    x0, x1, xg0 = bx + bw * .47, bx + bw * 1.04, bx + bw * .33
    xa = bx + bw * .40
    yg, ye, yr = yh + bh * .31, yh + bh * .11, yh - bh * .11
    yg2, ye2, yr2 = yg - bh * .03, ye - bh * .01, yr + bh * .02
    gable = [(xg0, yg - bh * .015), (xg0, ye + bh * .01), (xa, yr), (x0, ye), (x0, yg)]
    wall = [(x0, ye), (x1, ye2), (x1, yg2), (x0, yg)]
    roof = [(x0, ye), (xa, yr), (x1, yr2), (x1, ye2)]
    # cast shadow on the field to the right/front
    shadow = [(xg0 - 2 * S, yg - bh * .01), (x0, yg), (x1, yg2), (x1, yg2 + 9 * S), (x0 + 6 * S, yg + 9 * S), (xg0 + 4 * S, yg + 5 * S)]
    cv.obj([shadow], 0)
    cv.hair(C.hatch_poly(shadow, 45, 1.5))
    # gable end, in shade: vertical boards and cross-hatch
    cv.obj([gable], 1.)
    cv.hair(C.hatch_poly(gable, 90, 2))
    cv.hair(C.hatch_poly(gable, -45, 3))
    if not small:
        hl = [(xg0 + (x0 - xg0) * .3, ye - bh * .05), (xg0 + (x0 - xg0) * .7, ye - bh * .055),
              (xg0 + (x0 - xg0) * .7, ye + bh * .03), (xg0 + (x0 - xg0) * .3, ye + bh * .032)]
        cv.obj([hl], 1.)
        cv.hair([hl[0], hl[2]])
        cv.hair([hl[1], hl[3]])
        cv.hair(C.hatch_poly(hl, 0, 3, .25))
    # long wall, lit: board and batten with the eave's shadow
    cv.obj([wall], 1.)
    nb = int((x1 - x0) / 3)
    for i in range(1, nb):
        t = i / nb
        cv.hair([_bil((wall[0], wall[0], wall[1], wall[1]), t, 0), _bil((wall[3], wall[3], wall[2], wall[2]), t, 0)])
    eav = [wall[0], wall[1], (x1, ye2 + bh * .035), (x0, ye + bh * .04)]
    cv.hair(C.hatch_poly(eav, 45, 1.5))
    # sliding doors and windows
    if not small:
        def wq(u0, u1, v0, v1):
            return [_bil((wall[0], wall[3], wall[2], wall[1]), u, v) for u, v in ((u0, v0), (u0, v1), (u1, v1), (u1, v0))]
        door = wq(.14, .34, .3, 1.)
        cv.obj([door], 1.)
        mid = [_bil((door[0], door[1], door[2], door[3]), .5, 0), _bil((door[0], door[1], door[2], door[3]), .5, 1)]
        for a, b in ((door[0], door[2]), (door[1], door[3])):
            cv.line([a, b])
        cv.hair(mid)
        cv.hair(C.hatch_poly(door, 90, 3))
        for u in (.48, .64, .80):
            win = wq(u, u + .07, .32, .58)
            cv.obj([win], 1.)
            cv.hair(C.hatch_poly(win, 0, 1.5, .25))
    # roof, with the array
    cv.obj([roof], 1.)
    for i in range(1, 60):
        cv.hair([_bil(roof, i / 60, 0), _bil(roof, i / 60, .06)])
    cols = max(6, int((x1 - x0) / (13 * S)))
    rows = 3 if not small else 2
    for r in range(rows):
        for c in range(cols):
            u0 = .03 + .95 * c / cols
            u1 = u0 + .95 / cols - .012
            v0 = .09 + .84 * r / rows
            v1 = v0 + .84 / rows - .03
            pq = [_bil(roof, u0, v0), _bil(roof, u0, v1), _bil(roof, u1, v1), _bil(roof, u1, v0)]
            cv.obj([pq], .5)
            glint = abs((u0 + u1) / 2 - .1 - .08 * r) < .09
            if not glint:
                cv.hair(C.hatch_poly(pq, 45, 1.5 if not small else 2))
            else:
                cv.hair(C.hatch_poly(pq, 45, 3))
            if not small:
                cv.hair([_bil(roof, (u0 + u1) / 2, v0), _bil(roof, (u0 + u1) / 2, v1)])
    cv.heavy([gable[2], gable[3]])
    cv.heavy([(x0, ye), (x1, ye2)])
    cv.line([(xa, yr), (x1, yr2)])

    # Parker's dog, asleep at the barn door
    if not small:
        _dog(cv, x0 + (x1 - x0) * .20, yg + 2 * S, max(1., S * 1.35))
    o.append(cv.svg())
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# the calendar tablet: thirty days as suns and clouds
# ------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------
# layouts (from the house frame_plate, with the field filled, no blank paper, page-specific parts)
# ------------------------------------------------------------------------------------------------

def _post(cv, x, yb, ht, wd, lean=0.):
    """a split cedar fence post, round-topped, modelled in burin tone, its grain running down"""
    poly = [(x - wd / 2, yb), (x - wd / 2 + lean, yb - ht + wd * .3), (x + lean, yb - ht), (x + wd / 2 + lean, yb - ht + wd * .3),
            (x + wd / 2, yb)]
    cv.obj([poly], 1.)
    tone_hatch(cv, poly, lambda px, py: .08 + .9 * max(0., (px - (x - wd / 2)) / wd - .25), 90., 1.5, .75, 20.)
    return poly


def tally_fence(w, h, seed, good=None):
    """the headpiece: thirty fence posts across a strip of field, set in fives like tally marks
    (four upright and the fifth a brace laid across them); a low November sun behind the middle,
    the wire strung post to post, the dirt of the field in front with a dog's paw print in it.
    good: thirty booleans, a low day's post leans and stands shorter"""
    rng = random.Random(seed)
    Wd = min(w - 4, h * 9.5)
    x0, x1 = w / 2 - Wd / 2, w / 2 + Wd / 2
    yb = h * .8
    cv = Canvas()
    # the sun behind the middle, its rays cut as long burin strokes
    sx, sy, sr = w / 2, yb - h * .1, h * .36
    for i in range(48):
        a = _PI + _PI * i / 47
        L = sr * (2.0 if i % 2 else 1.5)
        cv.obj([], 0)
        (cv.line if i % 2 else cv.hair)([(sx + sr * 1.08 * _m.cos(a), sy + sr * 1.08 * _m.sin(a)), (sx + L * _m.cos(a), sy + L * _m.sin(a))])
    disc = _ell(sx, sy, sr, sr, 40)[:-1]
    cv.obj([disc], 1.)
    tone_hatch(cv, disc, lambda x, y: .05 + .5 * max(0., (math.hypot(x - sx, y - sy) / sr) - .55), 0., 1.5, None)
    # the field: a strip of tilled dirt fraying out at each end, clods and furrows in short flicks
    ground = [(x0 + Wd * i / 60, yb - 1.5 * _m.sin(i * .7) - (h * .06 if 8 < i < 52 else 0)) for i in range(61)]
    ground += [(x1 - Wd * i / 60, h - 1 - (2.5 * abs(_m.sin(i * 1.3)) if (i < 6 or i > 54) else 0)) for i in range(61)]
    cv.obj([ground], 0)
    yy = yb - h * .04
    while yy < h - 1:
        xx = x0 + rng.uniform(0, 6)
        while xx < x1:
            L = rng.uniform(2, 6)
            cv.hair([(xx, yy), (xx + L, yy + rng.uniform(-.4, .4))])
            xx += L + rng.uniform(1.5, 4)
        yy += 2.
    # the paw print pressed in the dirt
    px, py = x0 + Wd * .78, h * .9
    pad = _ell(px, py, h * .045, h * .035, 12)[:-1]
    cv.obj([pad], .5)
    tone_hatch(cv, pad, lambda x, y: .8, 45., 1.5, .6)
    for k, (dx, dy) in enumerate(((-1.4, -1.1), (-.5, -1.6), (.5, -1.6), (1.4, -1.1))):
        toe = _ell(px + dx * h * .03, py + dy * h * .03, h * .017, h * .021, 8)[:-1]
        cv.obj([toe], .5)
        tone_hatch(cv, toe, lambda x, y: .8, 45., 1.5, None)
    # the wire, then the thirty posts in six groups of five
    good = good or [True] * 30
    n = 30
    gap = Wd * .94 / (6 * 5 + 5)
    xs = []
    x = x0 + Wd * .03
    for g in range(6):
        for k in range(4):
            xs.append(x)
            x += gap
        xs.append(None)
        x += gap * 2
    for q in (.35, .62):
        cv.obj([], 0)
        cv.hair([(x0 + Wd * .02, yb - h * .55 * q - 2), (x1 - Wd * .02, yb - h * .55 * q - 2)])
    day = 0
    for g in range(6):
        grp = xs[g * 5:g * 5 + 4]
        for k, gx in enumerate(grp):
            ok = good[day % 30]
            ht = h * (.6 if ok else .44) * rng.uniform(.94, 1.04)
            pw = max(3., h * .075)
            # the post's shadow thrown toward us by the low sun behind, then the post, grass at its foot
            sh = [(gx - pw / 2, yb + 1), (gx + pw / 2, yb + 1), (gx + pw / 2 + (gx - sx) * .05, h - 2), (gx - pw / 2 + (gx - sx) * .05, h - 2)]
            cv.obj([sh], 0)
            tone_hatch(cv, sh, lambda x, y: .75, 0., 1.5, None)
            _post(cv, gx, yb + 1, ht, pw, 0. if ok else rng.uniform(-1.5, 1.5))
            for t in range(5):
                bx_ = gx + rng.uniform(-pw, pw)
                cv.obj([], 0)
                cv.hair([(bx_, yb + 1.5), (bx_ + rng.uniform(-1.5, 1.5), yb + 1.5 - rng.uniform(2, 4.5))])
            day += 1
        # the fifth day: a brace laid across the four, like the stroke through a tally
        a_ = (grp[0] - gap * .4, yb - h * .12)
        b_ = (grp[-1] + gap * .4, yb - h * .5)
        R = _Rib([a_, ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2), b_], [1.4, 1.5, 1.3], [1.4, 1.5, 1.3])
        cv.obj([R.outline()], 1.)
        cv.hair(R.contour(.75, 0, 1))
        day += 1
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    facts = _facts(ctx)
    uid = f"ms{int(w)}x{int(h)}"
    good = [not lo for lo in facts[1]]
    if h <= 110:
        return vignette(w, h, uid, None, "", None, tally_fence(w, h, seed, good))
    # taller: the barn roof under the low sun in a ruled lunette, the tally fence beneath it
    fh = min(64., h * .3)
    cx, cy, a, b = box_fit(w, h - fh, 2.2, pad=3)
    cy = 3 + b
    clean = shape_pts(cx, cy, a, b, "lunette", 160)
    d = _dd(clean, True, .1)
    body = _scene(cx - a, cy - b, 2 * a, 2 * b, d, facts, seed, uid)
    foot = f'<svg x="0" y="{_nn(h - fh)}" width="{_nn(w)}" height="{_nn(fh)}" overflow="visible">{tally_fence(w, fh, seed, good)}</svg>'
    return vignette(w, h, uid, clean, body, clean, foot)
