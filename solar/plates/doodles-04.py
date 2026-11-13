"""doodles-04 "Your bookshelf", merged into Books (edition plan: headpiece, about 8%, a book spine row).

The headpiece is a run of books standing free on a transparent ground: spines modelled round with
head and tail bands, raised cords and title labels, one leaning, stacks lying flat at each end as
bookends with their page blocks ruled, and the shelf's moulded edge beneath in burin tone. Easter
egg (the plan's): a calf spine lettered SOMASTER. At taller sizes the reader's desk at candle-light
(the open book with a drop-cap P and a tiny Mt. Hood plate, Tchaikovsky's spider) stands in a
ruled ogee niche above the shelf."""
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


_n, _d = C._n, C._d
PI = math.pi


def _lerp(p, q, f):
    return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)


# ------------------------------------------------------------------ pieces of the scene

def _spine(cv, x, yb, sw, sh, tilt, rng, tone):
    """A book standing on its tail at (x, yb), width sw, height sh, leaning by tilt (rad, + to the right
    about its lower right corner when tilt > 0 else lower left)."""
    ca, sa = math.cos(tilt), math.sin(tilt)
    px = x + sw if tilt > 0 else x

    def P(u, v):  # u across 0..1, v up 0..1
        lx, ly = x + u * sw - px, -v * sh
        return (px + lx * ca - ly * sa, yb + lx * sa + ly * ca)
    poly = [P(0, 0), P(1, 0), P(1, 1), P(0, 1)]
    cv.obj([poly], 1.)
    # rounded spine: dense rules at both edges, a highlight just left of centre
    us = []
    u = .5 / sw
    while u < 1:
        us.append(u)
        if u < .22:
            step = 1.5
        elif u < .42:
            step = 3. if tone < 2 else 2.
        elif u < .58:
            step = 4.5 if tone == 0 else 2.
        elif u < .75:
            step = 2.
        else:
            step = 1.5
        u += step / sw
    for u in us:
        if tone == 0 and .44 < u < .56:
            continue
        cv.hair([P(u, .02), P(u, .98)])
    # head and tail bands, and raised cords
    for v in (.08, .11, .89, .92):
        cv.line([P(0, v), P(1, v)])
    if sh > 18 and rng.random() < .7:
        for v in (.3, .55):
            cv.hair([P(0, v), P(1, v)])
            cv.hair([P(0, v + .025), P(1, v + .025)])
    if tone == 2:  # dark morocco: cross rules
        v = .13
        while v < .87:
            cv.hair([P(0, v), P(1, v)])
            v += 2. / sh
    if sw > 6 and sh > 16 and rng.random() < .6:  # title label
        lab = [P(.18, .64), P(.82, .64), P(.82, .78), P(.18, .78)]
        cv.obj([lab], .5)
        cv.hair([P(.3, .71), P(.7, .71)])
    return poly


def _shelf_row(cv, x0, x1, yb, rh, rng, lean_ok=True, tones=(0, 0, 1, 1, 2)):
    x = x0 + rng.uniform(-3, 0)
    while x < x1:
        sw = rng.choice((4.5, 5.5, 6., 7., 8., 9.5))
        sh = rh * rng.uniform(.62, .92)
        tone = rng.choice(tones)
        if lean_ok and rng.random() < .07 and x + sw * 2 < x1:
            _spine(cv, x, yb, sw, sh * .95, .32, rng, tone)
            x += sw + sh * .95 * math.sin(.32) + .5
            continue
        _spine(cv, x, yb, sw, sh, 0., rng, tone)
        x += sw + rng.choice((0., 0., .5, 1.))


def _board(cv, x0, x1, y, t=4.):
    poly = [(x0, y), (x1, y), (x1, y + t), (x0, y + t)]
    cv.obj([poly], 1.)
    cv.hair([(x0, y + 1.5), (x1, y + 1.5)])
    cv.hair([(x0, y + 3), (x1, y + 3)])
    cv.heavy([(x0, y + t + .7), (x1, y + t + .7)])


def _halo(cv, fx, fy, R, rng):
    """Candle glow: the ruled ground thins out toward the flame, and short rays burst from it."""
    disc = C._ell_pts(fx, fy, R, R, 56)
    cv.obj([disc], 0)
    y = fy - R + .75
    k = 0
    while y < fy + R:
        dy = abs(y - fy)
        half = math.sqrt(max(0., R * R - dy * dy))
        lev = (0, 2, 1, 3)[k % 4]
        r_in = R * (.42 + .14 * lev)
        if dy < r_in:
            hin = math.sqrt(r_in * r_in - dy * dy)
            cv.line([(fx - half, y), (fx - hin, y)]) if lev == 0 else cv.hair([(fx - half, y), (fx - hin, y)])
            cv.line([(fx + hin, y), (fx + half, y)]) if lev == 0 else cv.hair([(fx + hin, y), (fx + half, y)])
        else:
            (cv.line if lev == 0 else cv.hair)([(fx - half, y), (fx + half, y)])
        y += 1.5
        k += 1
    n = max(24, int(R * 1.4) // 2 * 2)
    for i in range(n):
        a = TAU * i / n + .05
        r0 = R * (.1 if i % 2 == 0 else .16)
        r1 = R * (.5 if i % 2 == 0 else rng.uniform(.26, .36))
        cv.hair([(fx + r0 * math.cos(a), fy + r0 * math.sin(a)), (fx + r1 * math.cos(a), fy + r1 * math.sin(a))])


TAU = 2 * PI


def _book(cv, cx, gy, bw, ph, rng, deco=True):
    """An open book seen from the front, gutter foot at (cx, gy), each leaf bw wide, ph tall."""
    thick = max(2.5, ph * .16)

    def top(s, t):
        return (cx + s * bw * t, gy - ph - ph * .2 * math.sin(PI * t) + ph * .08 * t + ph * .1 * (1 - t) ** 3)

    def bot(s, t):
        return (cx + s * bw * t, gy - ph * .14 * math.sin(PI * t * .9) + ph * .1 * (1 - t) ** 3 * 0)

    def blk(s, t, f=1.):
        b = bot(s, t)
        return (b[0] + s * f * 1.5, b[1] + thick * f * (.35 + .65 * t))
    T = [i / 30 for i in range(31)]
    # cover boards (dark leather), then the page blocks
    for s in (-1, 1):
        cov = [(cx, gy + 1.5)] + [(blk(s, t, 1.)[0] + s * 1.8 * t, blk(s, t, 1.)[1] + 1.8) for t in T] + \
              [(cx + s * (bw + 3.3), gy - ph * .3)] + [(cx + s * bw * .5, gy - ph * .1)]
        cov = [(cx, gy + 1.5)] + [(blk(s, t, 1.)[0] + s * 1.8 * t, blk(s, t, 1.)[1] + 1.8) for t in T] + \
              [(bot(s, 1.)[0] + s * 3.3, bot(s, 1.)[1] - 2)]
        cv.obj([cov], 1.)
        cv.hair(C.hatch_poly(cov, 0, 1.5))
        blkp = [bot(s, t) for t in T] + [blk(s, t) for t in T[::-1]]
        cv.obj([blkp], 1.)
        f = .25
        while f < 1:
            cv.hair([blk(s, t, f) for t in T[3:]])
            f += .25
    marg_t, marg_f = .1, .14
    for s in (-1, 1):
        page = [top(s, t) for t in T] + [bot(s, t) for t in T[::-1]]
        cv.obj([page], 1.)
        # gutter shadow: rules parallel to the gutter, closing up into it
        t = .006
        while t < .16:
            cv.hair([_lerp(top(s, t), bot(s, t), .02), _lerp(top(s, t), bot(s, t), .98)])
            t += (1.1 + 6 * t) / bw
        # page curl shade along the outer edge
        cv.hair([_lerp(top(s, .97), bot(s, .97), .03), _lerp(top(s, .97), bot(s, .97), .97)])
        # the text block, as words
        cap = None
        pic = None
        if deco and s < 0:
            cap = (.6, .9, marg_f, .5)        # drop cap P
        if deco and s > 0 and ph > 16:
            pic = (.26, .86, marg_f, .5)       # plate: Mt. Hood
        nl = max(4, int(ph * .78 / 1.9))
        for k in range(nl):
            f = marg_f + (1 - 2 * marg_f) * k / (nl - 1)
            t0, t1 = .17, .9
            if cap and cap[2] - .02 <= f <= cap[3] + .02:
                t1 = cap[0] - .03
            if pic and pic[2] - .02 <= f <= pic[3] + .02:
                continue
            if k == nl // 2 or k == nl - 1:
                t1 = t0 + (t1 - t0) * rng.uniform(.35, .7)
            t = t0
            while t < t1:
                L = rng.uniform(2.5, 7.5) / bw
                e = min(t1, t + L)
                if e - t > .8 / bw:
                    cv.hair([_lerp(top(s, t), bot(s, t), f), _lerp(top(s, (t + e) / 2), bot(s, (t + e) / 2), f),
                             _lerp(top(s, e), bot(s, e), f)])
                t = e + 1.3 / bw
        if cap:
            q = lambda t, f: _lerp(top(s, t), bot(s, t), f)
            box = [q(cap[0], cap[2]), q(cap[1], cap[2]), q(cap[1], cap[3]), q(cap[0], cap[3])]
            cv.obj([box], .5)
            x0, y0 = box[1][0] + .8, box[1][1] + .8
            x1, y1 = box[0][0] - .8, box[3][1] - .8
            wdt, hgt = x1 - x0, y1 - y0
            sx = x0 + wdt * .32
            cv.heavy([(sx, y0 + hgt * .08), (sx, y0 + hgt * .92)])
            cv.line([(sx - wdt * .14, y0 + hgt * .92), (sx + wdt * .16, y0 + hgt * .92)])
            bowl = [(sx - wdt * .1, y0 + hgt * .1)] + [(sx + wdt * .1 + wdt * .38 * math.sin(PI * j / 12),
                     y0 + hgt * .3 - hgt * .2 * math.cos(PI * j / 12)) for j in range(13)] + [(sx, y0 + hgt * .5)]
            cv.heavy(bowl)
            cv.hair(C.hatch_poly([(x0, y1), (x0 + wdt * .2, y1), (x0, y1 - hgt * .3)], 45, 1.5))
            cv.hair([(x1 - wdt * .3, y1 - .4), (x1 - .4, y1 - .4), (x1 - .4, y1 - hgt * .3)])
        if pic:
            q = lambda t, f: _lerp(top(s, t), bot(s, t), f)
            frame = [q(pic[0], pic[2]), q(pic[1], pic[2]), q(pic[1], pic[3]), q(pic[0], pic[3])]
            cv.obj([frame], .5)
            # sky: horizontal rules; the mountain white with a shaded flank
            cv.hair(C.hatch_poly(frame, 0, 1.5, inset=.3))
            xa, xb = frame[0][0], frame[1][0]
            ya, yb2 = (frame[0][1] + frame[1][1]) / 2, (frame[2][1] + frame[3][1]) / 2
            pw, phh = xb - xa, yb2 - ya
            peak = (xa + pw * .52, ya + phh * .18)
            mtn = [(xa + .4, yb2 - .4), (xa + pw * .3, ya + phh * .62), peak, (xa + pw * .75, ya + phh * .6), (xb - .4, yb2 - .4)]
            cv.obj([mtn], .5)
            cv.hair(C.hatch_poly([peak, (xa + pw * .75, ya + phh * .6), (xb - .4, yb2 - .4), (xa + pw * .55, yb2 - .4)], 70, 1.5))
            cv.hair([(xa + pw * .4, ya + phh * .42), (xa + pw * .47, ya + phh * .5), (xa + pw * .55, ya + phh * .4)])
    # ribbon bookmark from the gutter
    rl = ph * .9
    rib = [(cx - 1.3, gy - ph * .55), (cx + 1.3, gy - ph * .55), (cx + 2.3, gy + rl * .55), (cx + 1.6, gy + rl * .5),
           (cx + .4, gy + rl * .62), (cx + .2, gy + rl * .45), (cx - .9, gy + rl * .5)]
    cv.obj([rib], .5)
    cv.hair(C.hatch_poly(rib, 60, 1.5))
    cv.line([(cx, gy - ph * .55), (cx, gy - ph * 1.08)])


def _stack(cv, x, yb, w, rng, hs):
    """Books lying flat, spines to us (heights hs): returns top y."""
    y = yb
    for bh in hs:
        bwid = w * rng.uniform(.82, 1.)
        bx = x + (w - bwid) / 2 + rng.uniform(-2, 2)
        face = [(bx, y), (bx + bwid, y), (bx + bwid, y - bh), (bx, y - bh)]
        rnd = [(bx, y), (bx + bwid, y), (bx + bwid + 1.2, y - bh / 2), (bx + bwid, y - bh), (bx, y - bh), (bx - 1.2, y - bh / 2)]
        cv.obj([rnd], 1.)
        v = 1.
        while v < bh - .5:
            m = abs(v / bh - .38)
            if m > .1:
                cv.hair([(bx + .5, y - v), (bx + bwid - .5, y - v)])
            v += 1.5 if m > .25 else 2.
        for e in (.07, .1, .9, .93):
            cv.line([(bx + bwid * e, y), (bx + bwid * e, y - bh)])
        if rng.random() < .7:
            lab = [(bx + bwid * .4, y - bh * .25), (bx + bwid * .6, y - bh * .25), (bx + bwid * .6, y - bh * .75), (bx + bwid * .4, y - bh * .75)]
            cv.obj([lab], .5)
            cv.hair([(bx + bwid * .44, y - bh / 2), (bx + bwid * .56, y - bh / 2)])
        y -= bh
    # top cover in perspective
    top = [(bx, y), (bx + bwid, y), (bx + bwid - 2, y - 3), (bx + 2, y - 3)]
    cv.obj([top], 1.)
    cv.hair(C.hatch_poly(top, 0, 1.5))
    return y - 3


def _specs(cv, x, y, r):
    """Round reading spectacles lying on the desk (seen low, so the rims are flat ellipses)."""
    for dx in (-r * 1.25, r * 1.25):
        rim = C._ell_pts(x + dx, y, r, r * .5, 28)
        inner = C._ell_pts(x + dx, y, r - 1.2, r * .5 - 1.1, 28)
        cv.obj([rim], 1.)
        cv.line(inner + [inner[0]])
        cv.hair(C.hatch_poly(inner, -20, 1.5, phase=.3)[1::2])
    cv.line([(x - r * .3, y - r * .3), (x, y - r * .45), (x + r * .3, y - r * .3)])
    cv.line([(x - r * 2.2, y - r * .2), (x - r * 3.6, y - r * .9), (x - r * 4.3, y - r * .5)])
    cv.line([(x + r * 2.2, y - r * .2), (x + r * 3.4, y - r * 1.1), (x + r * 3.9, y - r * .7)])


def _candle(cv, x, yb, cw, ch, rng):
    """Chamberstick: dish, candle, wick; returns the flame centre."""
    dish = C._ell_pts(x, yb - 1.5, cw * 2.1, 2.6, 30)
    cv.obj([C._ell_pts(x + cw * 2.1 + 1.5, yb - 3.5, 2.6, 2.6, 16)], 1.)  # finger ring
    cv.obj([dish], 1.)
    cv.hair(C.hatch_poly(dish, 0, 1.5, phase=.5))
    cv.hair(C._ell_pts(x, yb - 2.6, cw * 1.6, 1.3, 24, PI, TAU))
    body = [(x - cw / 2, yb - 2.5), (x + cw / 2, yb - 2.5), (x + cw / 2, yb - ch), (x - cw / 2, yb - ch)]
    cv.obj([body], 1.)
    u = .5
    while u < cw:
        f = u / cw
        if f < .2 or f > .62:
            cv.hair([(x - cw / 2 + u, yb - ch + 1.5), (x - cw / 2 + u, yb - 3)])
        u += 1.5 if (f < .12 or f > .78) else 2.
    drip = [(x + cw * .15, yb - ch), (x + cw * .35, yb - ch), (x + cw * .3, yb - ch + ch * .3), (x + cw * .22, yb - ch + ch * .32)]
    cv.obj([drip], .5)
    cv.hair(C._ell_pts(x, yb - ch, cw / 2, 1.2, 16, 0, PI))
    fy = yb - ch - 2.2
    fh = max(6., cw * 1.6)
    fl = [(x + (cw * .38) * math.sin(PI * i / 16) * (1 - i / 16) ** .6 * 1.6, fy - fh * i / 16) for i in range(17)]
    fl = fl + [(2 * x - p[0], p[1]) for p in fl[::-1]]
    cv.obj([fl], 1.)
    cv.obj([C._ell_pts(x, fy - fh * .22, cw * .14, fh * .18, 12)], .5)
    cv.line([(x, yb - ch), (x, fy - fh * .1)])
    return (x, fy - fh * .4)


def _spider(fx, top_y, by, s=1.):
    """Black spider on its thread; raw svg (drawn above the canvas)."""
    o = f'<path d="M{_n(fx)},{_n(top_y)}V{_n(by - 2 * s)}" stroke="#000" stroke-width=".5"/>'
    body = _d(C._ell_pts(fx, by + 1.6 * s, 1.9 * s, 2.4 * s, 14), True, 0) + _d(C._ell_pts(fx, by - .9 * s, 1.2 * s, 1.2 * s, 10), True, 0)
    o += f'<path d="{body}" fill="#000" stroke="none"/>'
    legs = []
    for sd in (-1, 1):
        for k, (a, b) in enumerate(((-.9, -1.6), (-.35, -.6), (.25, .5), (.8, 1.4))):
            ax, ay = fx + sd * .9 * s, by - .6 * s + k * .45 * s
            kx, ky = ax + sd * 2.6 * s, ay + a * 2.2 * s - 1.2 * s
            ex, ey = kx + sd * 1.4 * s, ky + b * 1.9 * s + 2.2 * s
            legs.append(f"M{_n(ax)},{_n(ay)}L{_n(kx)},{_n(ky)}L{_n(ex)},{_n(ey)}")
    o += f'<path d="{"".join(legs)}" stroke="#000" stroke-width=".5" fill="none"/>'
    return o


def _desk_scene(cx, cy, a, b, seed, uid):
    """The whole field of a cartouche whose inner superellipse half-axes are a, b."""
    rng = random.Random(seed)
    field = C._superellipse(cx, cy, a - 4.6, b - 4.6)
    fd = _d(field, True, .1)
    x0, x1, y0, y1 = cx - a, cx + a, cy - b, cy + b
    H = 2 * b
    desk_h = min(max(H * .2, 12), 40)
    ty = y1 - desk_h                               # desk top surface (back edge)
    cv = Canvas = C.Canvas()
    # shelves behind
    rh = min(max(H * .3, 26), 46)
    yb = ty + 1
    rows = []
    while yb > y0 - rh * .3:
        rows.append(yb)
        yb -= rh + 4
    for i, yb in enumerate(rows):
        _shelf_row(cv, x0, x1, yb, rh, random.Random(seed * 31 + i))
        if i:
            pass
    # proportions of the desk group
    bw = min(a * (.44 if b < a * .75 else .56), H * .42, 92)
    ph = bw * .62
    gx = cx - a * .02
    gy = ty + desk_h * .48
    cdx = gx + bw + max(13, a * .19)
    cwid = max(4.5, bw * .15)
    srng = random.Random(seed * 7 + 1)
    hs = [srng.choice((5., 6., 7.5)) * max(1., bw / 50) for _ in range(3 if H > 90 else 2)]
    sbase = gy + desk_h * .25
    stop_y = sbase - sum(hs) - 3
    cht = min(ph * 1.25, (stop_y - y0) * .55)
    # candle glow
    flame_guess = (cdx, stop_y + 2 - cht - 2.2 - max(6., cwid * 1.6) * .4)
    R = min(cht * .95, a * .3, (gy - y0) * .7)
    _halo(cv, flame_guess[0], flame_guess[1], R, rng)
    for i, yb in enumerate(rows[1:]):
        _board(cv, x0, x1, yb)
    # desk with grain
    desk = [(x0 - 2, ty), (x1 + 2, ty), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]
    cv.obj([desk], 1.)
    k = 0
    y = ty + 1.5
    front = y1 - min(6., desk_h * .3)
    while y < front - .5:
        amp = .5 + .4 * math.sin(k * 1.7)
        cv.hair([(x, y + amp * math.sin(x * .07 + k * .9) + .4 * math.sin(x * .23 + k)) for x in range(int(x0) - 2, int(x1) + 3, 3)])
        y += 2. if (k % 5) else 1.5
        k += 1
    for kx in (cx - a * .62, cx + a * .55):
        kn = C._ell_pts(kx, ty + desk_h * .45, 4.5, 1.6, 16)
        cv.hair(kn + [kn[0]])
    cv.heavy([(x0 - 2, front), (x1 + 2, front)])
    y = front + 1.5
    while y < y1 + 2:
        cv.line([(x0 - 2, y), (x1 + 2, y)])
        y += 1.5
    # cast shadows on the desk, falling away from the candle (to the left)
    sh = [(gx - bw - 1, gy + 2), (gx + bw, gy + 2), (gx + bw - 6, gy - desk_h * .05), (gx - bw - desk_h * .6, gy - desk_h * .05)]
    cv.obj([], 0)
    cv.hair(C.hatch_poly(sh, -30, 1.5))
    # spectacles laid on the desk at the left
    _specs(cv, gx - bw - max(13, a * .16), gy + desk_h * .05, max(4.5, bw * .13))
    # the candle stands on a stack of books at the right
    sw = cwid * 4.6
    _stack(cv, cdx - sw / 2, sbase, sw, srng, hs)
    _book(cv, gx, gy, bw, ph, random.Random(seed * 13 + 5))
    fx, fy = _candle(cv, cdx, stop_y + 2, cwid, cht, rng)
    body = (f'<clipPath id="{uid}"><path d="{fd}"/></clipPath><g clip-path="url(#{uid})">'
            f'<path d="{fd}" fill="{C.pat("G")}" stroke="none"/>' + cv.svg())
    # spider dropping into the light from the shelf above
    spx = flame_guess[0] - R * .55
    spy = flame_guess[1] - R * .1
    top = max(y0, rows[1] if len(rows) > 1 else y0)
    if R > 14:
        body += _spider(spx, y0 - 2, spy, max(.7, min(1.2, R / 40)))
    body += "</g>"
    return body


# ------------------------------------------------------------------ layouts (house frames, bespoke fill)

def _flat_book(cv, x0, x1, yb, th, rng):
    """a book lying on its side, fore-edge toward us: the page block in fine rules, boards dark"""
    poly = [(x0, yb), (x1, yb), (x1, yb - th), (x0, yb - th)]
    cv.obj([poly], 1.)
    cv.line([(x0, yb - th * .18), (x1, yb - th * .18)])
    cv.line([(x0, yb - th * .82), (x1, yb - th * .82)])
    yy = yb - th * .3
    while yy > yb - th * .75:
        cv.hair([(x0 + 1, yy), (x1 - 1.2, yy)])
        yy -= 2.
    tone_hatch(cv, [(x1 - th * .35, yb), (x1, yb), (x1, yb - th), (x1 - th * .35, yb - th)], lambda x, y: .6, 90., 1.5, .7)


def shelf_row2(w, h, seed):
    """the headpiece: a run of books standing free on the light ground, spines modelled round,
    stacks lying flat at each end as bookends, the shelf's moulded edge beneath; one calf spine
    lettered SOMASTER"""
    rng = random.Random(seed)
    cv = C.Canvas()
    yb = h - 5.5
    rh = h - 10
    x0, x1 = 6., w - 6.
    # bookends: a stack lying flat at each end
    stack_w = min(70., w * .13)
    for sd in (-1, 1):
        yy = yb
        for k in range(rng.randint(3, 4)):
            th = rng.uniform(5., 8.)
            bw = stack_w * rng.uniform(.8, 1.)
            bx = x0 + rng.uniform(0, 4) if sd < 0 else x1 - bw - rng.uniform(0, 4)
            _flat_book(cv, bx, bx + bw, yy, th, rng) if sd < 0 else _flat_book(cv, bx, bx + bw, yy, th, rng)
            yy -= th + .5
            if yy < yb - rh * .9:
                break
    _shelf_row(cv, x0 + stack_w + 3, x1 - stack_w - 3, yb, rh, rng, True, (0,))
    sw = max(8., min(13., rh * .2))
    sh = rh * .97
    sx = x0 + stack_w + (x1 - x0 - 2 * stack_w) * (.58 + .1 * rng.random())
    sp = [(sx, yb), (sx + sw, yb), (sx + sw, yb - sh), (sx, yb - sh)]
    cv.obj([sp], 1.)
    tone_hatch(cv, sp, lambda x, y: abs((x - sx) / sw - .45) * 1.6 + .05, 90., 1.5, None)
    for v in (.06, .09, .91, .94):
        cv.line([(sx, yb - sh * v), (sx + sw, yb - sh * v)])
    lab = [(sx + sw * .2, yb - sh * .14), (sx + sw * .8, yb - sh * .14), (sx + sw * .8, yb - sh * .86), (sx + sw * .2, yb - sh * .86)]
    cv.obj([lab], .5)
    # the shelf edge: a moulded board, lit on the nosing, shadowed under
    board = [(0, yb), (w, yb), (w, h), (0, h)]
    cv.obj([board], 1.)
    tone_hatch(cv, board, lambda x, y: .1 + (y - yb) / (h - yb) * .6, 0., 2., None)
    return cv.svg() + motto([(sx + sw / 2, yb - sh * .16), (sx + sw / 2, yb - sh * .84)], "SOMASTER", sw * .62, .5, None, .98)


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 404
    uid = f"bk{int(w)}x{int(h)}"
    if h <= 110:
        return vignette(w, h, uid, None, "", None, shelf_row2(w, h, seed))
    # taller: the reader's desk at candle-light in an ogee-headed niche, the shelf run beneath
    sh = min(60., h * .3)
    cx, cy, a, b = box_fit(w, h - sh, 1.4, pad=3)
    cy = 3 + b
    clean = shape_pts(cx, cy, a, b, "ogee", 160)
    body = _desk_scene(cx, cy, a + 5, b + 5, seed, C._uid("bkd", w, h, seed))
    row = f'<svg x="0" y="{_nn(h - sh)}" width="{_nn(w)}" height="{_nn(sh)}" overflow="visible">{shelf_row2(w, sh, seed)}</svg>'
    return vignette(w, h, uid, clean, body, clean, row)
