"""river-02 'The Columbia, by the numbers' (edition plan: headpiece, about 10%, a banner of river waves).

A ruled banner of the Columbia off Sauvie Island: swells in swelling burin lines, the Washington
shore of firs, a dawn sky in broken strokes, and a bulk carrier lying to her mooring dolphins with
hawsers out whenever the page says a ship is across the way (otherwise empty dolphins and a gull).
The frame is the river's own: reeds and cattails rise over both ends of the banner and Parker's great
blue heron stands in them. Easter egg (the plan's): the St. Johns Bridge far upstream."""
import sys
import math
import random
import re
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


TAU = 2 * math.pi
_K = 2 ** (-1 / 2.6)


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _wave_row(x0, x1, y, amp, per, ph, step=2.):
    pts = []
    x = x0
    while x <= x1 + step:
        xx = min(x, x1)
        pts.append((xx, y + amp * math.sin(TAU * xx / per + ph) + amp * .4 * math.sin(TAU * xx / (per * .37) + ph * 1.7)))
        if xx >= x1:
            break
        x += step
    return pts


def _split(pl, rng, dash=(10, 40), gap=(1.6, 3.4)):
    """Break a polyline into dashes (by arc length)."""
    out, cur, acc = [], [pl[0]], 0.
    target = rng.uniform(*dash)
    gapping = False
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        acc += L
        if not gapping:
            cur.append(b)
            if acc >= target:
                if len(cur) > 1:
                    out.append(cur)
                gapping, acc, target = True, 0., rng.uniform(*gap)
        else:
            if acc >= target:
                cur = [b]
                gapping, acc, target = False, 0., rng.uniform(*dash)
    if not gapping and len(cur) > 1:
        out.append(cur)
    return out


# ---------------------------------------------------------------- stroke digits (no <text>)
_DIG = {
    "0": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)]],
    "1": [[(.5, 0), (.5, 2)], [(.15, .35), (.5, 0)]],
    "2": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (1, 2)]],
    "3": [[(0, 0), (1, 0), (1, 2), (0, 2)], [(.2, 1), (1, 1)]],
    "4": [[(0, 0), (0, 1), (1, 1)], [(1, 0), (1, 2)]],
    "5": [[(1, 0), (0, 0), (0, 1), (1, 1), (1, 2), (0, 2)]],
    "6": [[(1, 0), (0, 0), (0, 2), (1, 2), (1, 1), (0, 1)]],
    "7": [[(0, 0), (1, 0), (.4, 2)]],
    "8": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)], [(0, 1), (1, 1)]],
    "9": [[(1, 1), (0, 1), (0, 0), (1, 0), (1, 2), (0, 2)]],
}


# ---------------------------------------------------------------- the scene
def _ship(cv, sx, ys, L, hh, compact):
    bx = sx + L
    # bow wave and wake foam
    foam = [(bx - L * .08, ys + .5), (bx + L * .015, ys - hh * .15), (bx + L * .05, ys + hh * .35), (bx - L * .1, ys + hh * .45)]
    hull = [(sx, ys - hh), (sx + L * .03, ys - hh * .02), (sx + L * .045, ys), (bx - L * .04, ys), (bx, ys - hh * 1.25),
            (bx - L * .06, ys - hh * 1.25), (bx - L * .07, ys - hh * 1.0), (sx + L * .02, ys - hh)]
    cv.obj([hull], 1)
    # the hull in burin tone: dark below the boot-top, the flare catching light under the deck
    tone_hatch(cv, hull, lambda x, y: .35 + .55 * (y - (ys - hh)) / hh, 0., 1.5, .78, 70.)
    cv.line([(sx + L * .03, ys - hh * .55), (bx - L * .03, ys - hh * .55)])
    # hatch covers along the deck, cranes between them
    nh = 5
    hy0 = ys - hh
    for i in range(nh):
        x0 = sx + L * (.24 + i * .135)
        cov = [(x0, hy0), (x0 + L * .09, hy0), (x0 + L * .085, hy0 - hh * .45), (x0 + L * .005, hy0 - hh * .45)]
        cv.obj([cov], .5)
        cv.hair(C.hatch_poly(cov, 90, 1.5))
    for i in range(4):
        x0 = sx + L * (.355 + i * .135)
        post = _rect(x0 - .9, hy0 - hh * 1.6, 1.8, hh * 1.6)
        cv.obj([post], .5)
        cv.heavy([(x0, hy0 - hh * 1.5), (x0 - L * .075, hy0 - hh * 2.6)])
        cv.hair([(x0, hy0 - hh * 2.1), (x0 - L * .075, hy0 - hh * 2.6)])
        cv.line([(x0, hy0), (x0, hy0 - hh * 2.2)])
    # forecastle mast
    cv.obj([], 0)
    cv.line([(bx - L * .05, ys - hh * 1.25), (bx - L * .05, ys - hh * 2.4)])
    # accommodation block aft, bridge wings, funnel
    ax0, ax1 = sx + L * .035, sx + L * .17
    tiers = 4
    th = hh * .62
    for k in range(tiers):
        inset = L * .006 * k
        blk = _rect(ax0 + inset, hy0 - th * (k + 1), ax1 - ax0 - inset * 2, th)
        cv.obj([blk], .5)
        cv.hair(C.hatch_poly(blk, 90, 3, .5))
        # windows
        n = int((ax1 - ax0 - inset * 2) / 2.6)
        wy = hy0 - th * (k + .5)
        cv.line([[(ax0 + inset + 1.5 + j * 2.6, wy - .3), (ax0 + inset + 2.6 + j * 2.6, wy - .3)] for j in range(n)])
    wing = _rect(ax0 - L * .02, hy0 - th * tiers - 1.6, ax1 - ax0 + L * .04, 1.6)
    cv.obj([wing], .5)
    fx = ax0 + (ax1 - ax0) * .22
    fun = [(fx, hy0 - th * tiers - 1.6), (fx + L * .05, hy0 - th * tiers - 1.6), (fx + L * .045, hy0 - th * tiers - hh * 1.6),
           (fx + L * .003, hy0 - th * tiers - hh * 1.6)]
    cv.obj([fun], .5)
    cv.hair(C.hatch_poly(fun, 90, 1.5))
    band = [(fx + L * .003, hy0 - th * tiers - hh * 1.6), (fx + L * .045, hy0 - th * tiers - hh * 1.6),
            (fx + L * .046, hy0 - th * tiers - hh * 1.25), (fx + L * .002, hy0 - th * tiers - hh * 1.25)]
    cv.heavy(C.hatch_poly(band, 0, 1.2))
    if not compact:
        # radar mast, and a thread of smoke trailing aft
        mx = ax0 + (ax1 - ax0) * .7
        cv.obj([], 0)
        cv.line([(mx, hy0 - th * tiers - 1.6), (mx, hy0 - th * tiers - hh * 2.1)])
        cv.hair([(mx - 2, hy0 - th * tiers - hh * 1.8), (mx + 2, hy0 - th * tiers - hh * 1.8)])
    cv.obj([foam], 0)
    cv.hair([[(bx - L * .06 + i * 1.5, ys + .8 + i * .5), (bx + L * .04 - i * .8, ys + .8 + i * .9)] for i in range(3)])


def _heron(cv, fx, fy, hgt):
    """A great blue heron standing on the pile, facing left; feet at (fx, fy)."""
    s = hgt
    P = lambda pts: [(fx + x * s, fy + y * s) for x, y in pts]
    legs = [P([(.03, -.36), (.0, -.12), (-.02, 0)]), P([(.07, -.36), (.08, -.14), (.06, 0)])]
    cv.obj([], 0)
    cv.line(legs)
    cv.hair([P([(-.02, 0), (-.08, .005)]), P([(.06, 0), (.12, .004)])])
    body = P([(-.11, -.52), (-.04, -.6), (.06, -.61), (.17, -.55), (.27, -.46), (.36, -.37), (.3, -.36), (.18, -.37),
              (.08, -.35), (-.02, -.37), (-.1, -.43), (-.13, -.48)])
    cv.obj([body], 1)
    wing = P([(-.04, -.56), (.06, -.6), (.17, -.55), (.27, -.46), (.35, -.375), (.2, -.39), (.06, -.42), (-.02, -.46)])
    cv.hair(C.hatch_poly(body, -28, 1.5))
    cv.hair(C.hatch_poly(wing, 30, 3))
    cv.hair([P([(.0, -.5), (.18, -.43)]), P([(.04, -.55), (.24, -.44)])])
    # breast plumes
    cv.hair([P([(-.1 + .02 * i, -.44 + .01 * i), (-.06 + .02 * i, -.36)]) for i in range(4)])
    # neck: S curve, white with a streaked front
    spine = P([(-.08, -.52), (-.15, -.6), (-.13, -.7), (-.06, -.78), (-.07, -.86), (-.1, -.9)])
    wdt = .045 * s
    l, r = [], []
    for i, (x, y) in enumerate(spine):
        a, b = spine[max(0, i - 1)], spine[min(len(spine) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        k = 1.25 if i == 0 else 1.
        l.append((x + nx * wdt * k, y + ny * wdt * k))
        r.append((x - nx * wdt * k, y - ny * wdt * k))
    neck = l + r[::-1]
    cv.obj([neck], 1)
    cv.line([r[1:-1]])
    cv.hair([[(x + (rr[0] - x) * .45, y + (rr[1] - y) * .45), (x + (rr[0] - x) * .8, y + (rr[1] - y) * .8)]
             for (x, y), rr in zip(l[1:-1], r[1:-1])])
    head = [(fx + (-.1 + .055 * math.cos(a)) * s, fy + (-.915 + .035 * math.sin(a)) * s) for a in [TAU * k / 16 for k in range(16)]]
    cv.obj([head], 1)
    cv.heavy([P([(-.08, -.94), (.05, -.935)]), P([(-.02, -.935), (.13, -.9)])])   # black crest and plume
    beak = P([(-.15, -.925), (-.38, -.9), (-.15, -.9)])
    cv.obj([beak], 1)
    cv.hair([P([(-.15, -.912), (-.36, -.901)])])
    e = P([(-.115, -.918)])[0]
    cv.heavy([[(e[0] - .4, e[1]), (e[0] + .4, e[1])]])


# ---------------------------------------------------------------- engraved roman capitals (stroke paths)
def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


_CAP = {
    "A": (1.1, [[(0, 2), (.55, 0), (1.1, 2)], [(.22, 1.3), (.88, 1.3)]]),
    "B": (.9, [[(0, 0), (0, 2)], [(0, 0), (.55, 0)] + _arc(.55, .48, .32, .48, -90, 90, 8) + [(0, .96)],
               [(0, .96), (.55, .96)] + _arc(.55, 1.48, .36, .52, -90, 90, 8) + [(0, 2)]]),
    "C": (1., [_arc(.62, 1, .6, 1, -50, -310, 16)]),
    "E": (.8, [[(.8, 0), (0, 0), (0, 2), (.8, 2)], [(0, 1), (.6, 1)]]),
    "F": (.8, [[(.8, 0), (0, 0), (0, 2)], [(0, 1), (.6, 1)]]),
    "G": (1.05, [_arc(.6, 1, .6, 1, -50, -340, 16) + [(1.08, 1.1), (.65, 1.1)]]),
    "H": (1., [[(0, 0), (0, 2)], [(1, 0), (1, 2)], [(0, 1), (1, 1)]]),
    "I": (.1, [[(.05, 0), (.05, 2)]]),
    "L": (.75, [[(0, 0), (0, 2), (.75, 2)]]),
    "M": (1.3, [[(0, 2), (.08, 0), (.65, 2), (1.22, 0), (1.3, 2)]]),
    "N": (1., [[(0, 2), (0, 0), (1, 2), (1, 0)]]),
    "O": (1.2, [_arc(.6, 1, .6, 1, 0, 360, 20)]),
    "R": (.9, [[(0, 2), (0, 0), (.5, 0)] + _arc(.5, .5, .35, .5, -90, 90, 8) + [(0, 1)], [(.4, 1), (.95, 2)]]),
    "S": (.85, [_arc(.43, .5, .4, .5, -20, -270, 10) + _arc(.43, 1.5, .42, .5, -90, 160, 10)]),
    "T": (.9, [[(0, 0), (.9, 0)], [(.45, 0), (.45, 2)]]),
    "U": (1., [[(0, 0), (0, 1.45)] + _arc(.5, 1.45, .5, .55, 180, 0, 10)[1:] + [(1, 0)]]),
    "V": (1.05, [[(0, 0), (.52, 2), (1.05, 0)]]),
    "W": (1.5, [[(0, 0), (.38, 2), (.75, .4), (1.12, 2), (1.5, 0)]]),
    ".": (.2, [[(.1, 1.85), (.1, 1.95)]]),
    "\u00b7": (.2, [[(.1, .95), (.1, 1.05)]]),
}


# ---------------------------------------------------------------- field recovery + plate
def st_johns(cv, x0, x1, deck, th):
    """the St. Johns Bridge far off: two gothic towers th tall, the cables in catenary, the deck"""
    span = x1 - x0
    t1, t2 = x0 + span * .25, x0 + span * .75
    top = deck - th
    cab = []
    for i in range(41):
        u = i / 40
        xx = x0 + span * u
        if xx < t1:
            yy = deck - (xx - x0) / (t1 - x0) * th * .95
        elif xx > t2:
            yy = deck - (x1 - xx) / (x1 - t2) * th * .95
        else:
            v = (xx - t1) / (t2 - t1)
            yy = top + th * .05 + th * .78 * (1 - (2 * v - 1) ** 2)
        cab.append((xx, yy))
    cv.obj([], 0)
    cv.line(cab)
    for xx, yy in cab[1:-1:2]:
        cv.hair([(xx, yy), (xx, deck)])
    cv.line([(x0 - span * .05, deck), (x1 + span * .05, deck)])
    for tx in (t1, t2):
        tw = max(1.6, th * .14)
        tw_ = [(tx - tw, deck + th * .35), (tx + tw, deck + th * .35), (tx + tw * .7, top + th * .1), (tx, top - th * .06),
               (tx - tw * .7, top + th * .1)]
        cv.obj([tw_], .5)
        cv.hair([(tx, top + th * .12), (tx, deck - th * .4)])
        cv.hair([(tx - tw * .5, deck - th * .55), (tx, deck - th * .75), (tx + tw * .5, deck - th * .55)])


def river_band(x, y, W, H, seed, ship=True):
    """the headpiece: a banner of the Columbia off Sauvie Island; swells in swelling burin lines, the
    Washington shore of firs, the St. Johns Bridge far upstream, and a bulk carrier at the moorings
    when one is in"""
    rng = random.Random(seed)
    cv = C.Canvas()
    cv.obj([_rect(x - 2, y - 2, W + 4, H + 4)], 0)
    hy = y + H * .38
    # sky: dawn streaks in broken strokes, closing up toward the zenith
    yy = y
    while yy < hy:
        t = (yy - y) / max(1., hy - y)
        xx = x - 2 + rng.uniform(0, 5)
        while xx < x + W:
            L = rng.uniform(8, 30)
            cv.hair([(xx, yy), (xx + L, yy)])
            xx += L + rng.uniform(1.5, 3.5 + 8 * t)
        yy += 1.5 if t < .4 else 2.
    st_johns(cv, x + W * .74, x + W * .97, hy - H * .03, H * .26)
    # the Washington shore
    shore = [(x - 2, hy + 1)]
    xx = x - 2
    while xx < x + W + 2:
        th = H * rng.uniform(.06, .14)
        wv = th * .4
        shore += [(xx, hy - 1), (xx + wv, hy - 1 - th), (xx + 2 * wv, hy - 1)]
        xx += 2 * wv * rng.uniform(.6, 1.)
    shore += [(x + W + 2, hy + 1)]
    cv.obj([shore], .5)
    cv.hair(C.hatch_poly(shore, 90, 1.5))
    cv.hair(_keep_disc(C.hatch_poly(shore, 20, 2.), x + W * .3, hy, W * .4))
    # the river: rows of swell, the crests cut heavier as they come forward
    water = _rect(x - 2, hy, W + 4, y + H - hy + 3)
    cv.obj([water], 0)
    L = min(W * .42, H * 2.2)
    sx = x + W * .14
    ys = hy + H * .22
    hh = max(3., L * .08)
    yy = hy + 1
    while yy < y + H + 2:
        t = (yy - hy) / max(1., y + H - hy)
        row = _wave_row(x - 2, x + W + 2, yy, .3 + 1.2 * t, 12 + 26 * t, rng.uniform(0, TAU))
        segs = _split(row, rng, (8 + 26 * (1 - t), 24 + 40 * (1 - t)), (1.2, 2. + 2 * t))
        (cv.line if t > .5 else cv.hair)(segs)
        yy += 1.5 if t < .3 else 2.
    if ship:
        # moored: the dolphins she lies to, hawsers out fore and aft
        for fx in (-.04, 1.06):
            px = sx + L * fx
            for k in (-1, 0, 1):
                pile = _rect(px + k * 1.6 - .7, ys - hh * 1.6 + abs(k) * .8, 1.4, hh * 1.9)
                cv.obj([pile], .5)
                cv.hair(C.hatch_poly(pile, 90, 1.5))
        cv.hair([(sx + L * .01, ys - hh * .9), (sx - L * .04, ys - hh * 1.3)])
        cv.hair([(sx + L * .99, ys - hh * 1.1), (sx + L * 1.06, ys - hh * 1.3)])
        _ship(cv, sx, ys, L, hh, False)
    else:
        for fx in (.2, .5):
            px = sx + L * fx
            for k in (-1, 0, 1):
                pile = _rect(px + k * 1.6 - .7, ys - hh * 1.6 + abs(k) * .8, 1.4, hh * 1.9)
                cv.obj([pile], .5)
                cv.hair(C.hatch_poly(pile, 90, 1.5))
        gx, gy, r = sx + L * .5, ys - hh * 2.4, hh * .9
        cv.line([(gx - r, gy + r * .1), (gx - r * .45, gy - r * .45), (gx, gy + r * .15), (gx + r * .45, gy - r * .45), (gx + r, gy + r * .1)])
    return cv.svg()


def _reedbed(cv, bx, by, wd, ht, sd, rng):
    """a clump of reeds and cattails rising from by, spread wd, leaning outward on side sd"""
    for i in range(int(wd / 2.2)):
        gx = bx + rng.uniform(-wd / 2, wd / 2)
        gh = ht * rng.uniform(.5, 1.)
        lean = sd * rng.uniform(.05, .35) + rng.uniform(-.08, .08)
        stem = [(gx + lean * gh * (t ** 1.7), by - gh * t) for t in [k / 10 for k in range(11)]]
        cv.obj([], 0)
        cv.line(stem[:6])
        cv.hair(stem[5:])
        if rng.random() < .22:
            # a cattail: the brown head modelled round, the spike above it
            hx, hy = stem[7]
            hw, hh = max(1.4, ht * .045), ht * .16
            head = _ell(hx, hy, hw, hh, 12)[:-1]
            cv.obj([head], .5)
            tone_hatch(cv, head, lit(hx, hy, hw, hh, .35, .7), 0., 1.5, .7)
            cv.line([(hx, hy - hh), stem[-1]])
        elif rng.random() < .3:
            # a reed blade folding over
            mx, my = stem[6]
            cv.hair([(mx, my), (mx + sd * ht * .12, my - ht * .05), (mx + sd * ht * .22, my + ht * .04)])


def _reedbed(cv, bx, by, wd, ht, sd, rng):
    """a clump of reeds and cattails rising from by, spread wd, leaning outward on side sd"""
    for i in range(int(wd / 2.2)):
        gx = bx + rng.uniform(-wd / 2, wd / 2)
        gh = ht * rng.uniform(.5, 1.)
        lean = sd * rng.uniform(.05, .35) + rng.uniform(-.08, .08)
        stem = [(gx + lean * gh * (t ** 1.7), by - gh * t) for t in [k / 10 for k in range(11)]]
        cv.obj([], 0)
        cv.line(stem[:6])
        cv.hair(stem[5:])
        if rng.random() < .22:
            # a cattail: the brown head modelled round, the spike above it
            hx, hy = stem[7]
            hw, hh = max(1.4, ht * .045), ht * .16
            head = _ell(hx, hy, hw, hh, 12)[:-1]
            cv.obj([head], .5)
            tone_hatch(cv, head, lit(hx, hy, hw, hh, .35, .7), 0., 1.5, .7)
            cv.line([(hx, hy - hh), stem[-1]])
        elif rng.random() < .3:
            # a reed blade folding over
            mx, my = stem[6]
            cv.hair([(mx, my), (mx + sd * ht * .12, my - ht * .05), (mx + sd * ht * .22, my + ht * .04)])


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 17 * int(ctx.get("sheet", 0) or 0)
    smp = (ctx.get("sample", "") or "")
    ship = not re.search(r"no ship", smp, re.I)
    uid = f"cb{int(w)}x{int(h)}"
    cx, cy, a, b = box_fit(w, h, 7.2 if h < 110 else 2.6, pad=2)
    a *= .86
    clean = shape_pts(cx, cy, a, b, "cushion", 200)
    body = river_band(cx - a, cy - b, 2 * a, 2 * b, seed, ship)
    rng = random.Random(seed + 4)
    cv = C.Canvas()
    for sd in (-1, 1):
        _reedbed(cv, cx + sd * a * .96, h - 1, a * .2, h * .95, sd, rng)
    _heron(cv, cx - a * 1.02, h - 2, h * .9)
    return vignette(w, h, uid, clean, body, clean, cv.svg())
