"""today-07 Window shades, merged into Alfred's briefing (edition plan: small tailpiece, about 8%, an oval cameo).

An oval cameo under the signature: the ground worked dark in level burin lines that close up toward
the rim, and lit out of it Alfred's silver salver in perspective with its gadrooned rim, a swelling
coffee pot with a dark band of reflection down its side, a cup and saucer with the steam rising.
Easter egg (the plan's): a dog biscuit laid on the salver beside the cup."""
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

import engraving_morning as M
import re

_n = C._n
PI = math.pi
TAU = 2 * PI


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _lerp(a, b, t):
    return a + (b - a) * t


def _sm(t):
    t = min(max(t, 0.), 1.)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------------------------
# pieces of the scene, all drawn into one Canvas
# ---------------------------------------------------------------------------------------------

def _crescent(cx, cy, r, phi=-.5, d=.45, ri=.82, n=40):
    """A crescent moon: the disc less an offset disc toward angle phi."""
    ix, iy = cx + r * d * math.cos(phi), cy + r * d * math.sin(phi)
    rr = r * ri
    outer = [(cx + r * math.cos(phi + TAU * i / n), cy + r * math.sin(phi + TAU * i / n)) for i in range(n + 1)]
    outer = [q for q in outer if math.hypot(q[0] - ix, q[1] - iy) > rr]
    inner = [(ix + rr * math.cos(phi + TAU * i / n), iy + rr * math.sin(phi + TAU * i / n)) for i in range(n + 1)]
    inner = [q for q in inner if math.hypot(q[0] - cx, q[1] - cy) < r]
    return outer + inner[::-1]


def _disc_shade(cx, cy, r, pitch=1.5):
    """Horizontal shading across a disc, leaving a highlight upper left."""
    hx, hy, hr = cx - r * .3, cy - r * .3, r * .62
    out = []
    yy = cy - r + .25
    while yy < cy + r:
        half = math.sqrt(max(0., r * r - (yy - cy) ** 2)) - .8
        if half > .6:
            a, b = cx - half, cx + half
            dy = yy - hy
            if abs(dy) < hr:
                hh = math.sqrt(hr * hr - dy * dy)
                if hx - hh > a + .6:
                    out.append([(a, yy), (hx - hh, yy)])
                if b > hx + hh + .6:
                    out.append([(max(a, hx + hh), yy), (b, yy)])
            else:
                out.append([(a, yy), (b, yy)])
        yy += pitch
    return out


def _sky(cv, poly, pitch, phase=.25):
    cv.obj([poly], 0)
    cv.hair(C.hatch_poly(poly, 0, pitch, phase))


def _sun(cv, cx, cy, r):
    """A rising sun: white rays cut out of the sky hatch, a modelled disc."""
    n = 14
    for i in range(0, n, 2):
        a0 = PI + PI * (i + .2) / n - .02
        a1 = PI + PI * (i + .8) / n + .02
        R = r * 3.2
        wedge = [(cx + r * 1.15 * math.cos(a0), cy + r * 1.15 * math.sin(a0)),
                 (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                 (cx + R * math.cos(a1), cy + R * math.sin(a1)),
                 (cx + r * 1.15 * math.cos(a1), cy + r * 1.15 * math.sin(a1))]
        cv.obj([wedge], 0)
        if r > 6:
            am = (a0 + a1) / 2
            cv.hair([(cx + r * 1.4 * math.cos(am), cy + r * 1.4 * math.sin(am)),
                     (cx + R * .8 * math.cos(am), cy + R * .8 * math.sin(am))])
    disc = C._ell_pts(cx, cy, r, r, 40)[:-1]
    cv.obj([disc], 1.)
    if r > 5:
        cv.hair(_disc_shade(cx, cy, r, 2. if r < 9 else 1.5))
    elif r > 3:
        cv.hair([C._ell_pts(cx, cy, r * .6, r * .6, 24, -.2, 1.9)])


def _hills(cv, x0, x1, ybase, h, seed, hood=True):
    """Rolling hills across a light, Mt. Hood standing behind them."""
    rng = random.Random(seed)
    w = x1 - x0
    yb = ybase
    if hood and h > 6:
        px = x0 + w * .66
        top_y = ybase - h * 1.05
        mt = [(x0 + w * .18, yb), (px - w * .3, ybase - h * .4), (px - w * .14, ybase - h * .72),
              (px - w * .04, top_y + h * .08), (px, top_y), (px + w * .05, top_y + h * .1),
              (px + w * .16, ybase - h * .66), (px + w * .34, ybase - h * .36), (x1 + 2, ybase - h * .2), (x1 + 2, yb)]
        cv.obj([mt], .5)
        snow_y = ybase - h * .62
        cv.hair([q for q in C.hatch_poly(mt, -45, 1.5) if min(p[1] for p in q) > snow_y - .5])
        cv.hair([q for q in C.hatch_poly(mt, 0, 3, .25) if q[0][1] <= snow_y and q[0][0] > px - .2])
        for f in (-.12, -.05, .04, .11):
            cv.hair([(px + w * f * .3, top_y + h * .12), (px + w * f, snow_y + h * .06)])
    pts = [(x0, yb)]
    m = 24
    ph = rng.random() * 6
    for i in range(m + 1):
        t = i / m
        pts.append((x0 + w * t, ybase - h * (.32 + .16 * math.sin(t * 5.2 + ph) + .08 * math.sin(t * 13 + ph))))
    pts.append((x1, yb))
    cv.obj([pts], .5)
    cv.hair(C.hatch_poly(pts, 0, 1.5, .25))


def _rolled_shade(cv, x0, x1, y0, hgt):
    """A roller blind wound up at the head of the light."""
    y1 = y0 + hgt
    cv.obj([_rect(x0, y0, x1, y1)], 1.)
    yy = y0 + hgt * .5
    while yy < y1 - .8:
        cv.hair([(x0 + .5, yy), (x1 - .5, yy)])
        yy += 1.5
    if hgt > 4:
        cv.line([(x0 + .5, y1 - 1), (x1 - .5, y1 - 1)])


def _roman_shade(cv, x0, x1, y0, y1, folds):
    """A Roman shade let down: stacked pleats, each bellying out and shaded under its fold."""
    fh = (y1 - y0) / folds
    m = 20
    for j in range(folds):
        ya = y0 + j * fh
        yb = ya + fh
        bulge = min(fh * .3, 2.5)
        low = [(x0 + (x1 - x0) * i / m, yb + bulge * math.sin(PI * i / m)) for i in range(m + 1)]
        poly = [(x0, ya), (x1, ya)] + low[::-1]
        cv.obj([poly], .5)
        for f in (.45, .62, .76, .88):
            if fh * (1 - f) < .9:
                continue
            cv.hair([(x0 + (x1 - x0) * i / m, ya + (yb - ya) * f + bulge * f * f * math.sin(PI * i / m))
                     for i in range(m + 1)])
        cv.line([(p[0], p[1] - .6) for p in low])
    cv.hair([[(x0 + 1.2, y0), (x0 + 1.2, y1)], [(x1 - 1.2, y0), (x1 - 1.2, y1)]])


def _drumstick(cv, x, y, L):
    """The shade pull: a cord ending in a drumstick, bead down."""
    cord = L * .38
    cv.obj([], 0)
    cv.hair([(x, y), (x, y + cord)])
    s0 = y + cord
    s1 = y + L - L * .1
    wt, wb = max(1.1, L * .05), max(.55, L * .02)
    shaft = [(x - wt, s0), (x + wt, s0), (x + wb, s1), (x - wb, s1)]
    cv.obj([shaft], .5)
    br = max(1.2, L * .08)
    bead = C._ell_pts(x, s1 + br * .8, br * .62, br, 16)[:-1]
    cv.obj([bead], .5)
    if wt > 1.4:
        cv.hair([(x + wt * .4, s0 + .8), (x + wb * .4, s1 - .5)])


def _curtain(cv, side, xo, y0, y1, wtop, wtie, wbot, tie_t, seed):
    """A velvet curtain hanging from y0 to y1 against the outer edge xo (side -1: left curtain,
    its inner edge to the right), drawn back to a tie-back at tie_t. Folds in bulino."""
    rng = random.Random(seed)
    H = y1 - y0
    inw = -side

    def width(t):
        if t < tie_t:
            return _lerp(wtop, wtie, _sm(t / tie_t) ** .8)
        return _lerp(wtie, wbot, _sm((t - tie_t) / (1 - tie_t)))

    m = max(24, int(H / 1.5))
    k = max(3, int(round(wtop / 5.5)))
    ph = rng.random()
    amp = 1.6 if H > 20 else .8

    def at(s, t):
        y = y0 + H * t
        if t >= .999:
            y += amp * math.sin(2 * PI * (s * k + ph))
        return (xo + inw * width(t) * s, y)

    inner = [at(1, i / m) for i in range(m + 1)]
    bottom = [at(1 - i / 16, 1) for i in range(17)]
    poly = [(xo, y0)] + inner + bottom + [(xo, y1)]
    cv.obj([poly], 1.)
    N = max(4, int(wtop / 1.6))
    for i in range(1, N):
        s = i / N
        lvl = 1 if i % 4 == 0 else (2 if i % 2 == 0 else 4)
        fold_phase = (s * k + ph) % 1.
        dark = abs(fold_phase - .75) < .17
        seg, segs = [], []
        for j in range(m + 1):
            t = j / m
            gap = width(t) / N * lvl
            if gap >= 1.6 or (dark and gap >= 1.):
                seg.append(at(s, t))
            else:
                if len(seg) > 1:
                    segs.append(seg)
                seg = []
        if len(seg) > 1:
            segs.append(seg)
        (cv.line if dark and lvl <= 2 else cv.hair)(segs)
    cv.line([(p[0] + side * .8, p[1]) for p in inner[1:-1]])


def _tieback(cv, side, xo, y, wtie, h):
    """A rope tie-back with a tassel, gathering the curtain."""
    inw = -side
    x1 = xo + inw * (wtie + 1.5)
    band = [(xo, y - h * .5), (x1, y - h * .4), (x1, y + h * .4), (xo, y + h * .5)]
    cv.obj([band], 1.)
    xx = min(xo, x1)
    while xx < max(xo, x1) - .5:
        cv.hair([(xx, y - h * .45), (xx + h * .7, y + h * .45)])
        xx += 2.
    tx = x1 - inw * .5
    th = h * 2.4
    tw = h * .7
    cap = C._ell_pts(tx, y + h * .4 + tw * .5, tw * .55, tw * .55, 12)[:-1]
    skirt = [(tx - tw * .4, y + h * .4 + tw * .8), (tx + tw * .4, y + h * .4 + tw * .8),
             (tx + tw * .8, y + h * .4 + th), (tx - tw * .8, y + h * .4 + th)]
    cv.obj([skirt], .5)
    xx = tx - tw * .55
    while xx < tx + tw * .6:
        cv.hair([(xx * .6 + tx * .4, y + h * .4 + tw * .9), (xx, y + h * .4 + th - .4)])
        xx += 1.5
    cv.obj([cap], .5)


def _valance(cv, x0, x1, y0, vh, seed):
    """A swagged pelmet: festoons of draped cloth hung between tasselled jabots."""
    w = x1 - x0
    n = max(2, int(round(w / (vh * 3.2))))
    sw = w / n
    m = 16
    top = vh * .28
    for i in range(n):
        a = x0 + sw * i
        low = [(a + sw * j / m, y0 + top + (vh - top) * math.sin(PI * j / m)) for j in range(m + 1)]
        poly = [(a, y0), (a + sw, y0)] + low[::-1]
        cv.obj([poly], 1.)
        for f in (.25, .42, .56, .68, .78, .87, .94):
            if (vh - top) * .1 < .9 and f < .8:
                continue
            yy = [(a + sw * j / m, y0 + top * f + (vh - top) * f * math.sin(PI * j / m) ** (1.2 - .4 * f))
                  for j in range(m + 1)]
            (cv.line if f > .9 else cv.hair)(yy)
    cv.obj([_rect(x0 - 1, y0 - .5, x1 + 1, y0 + max(2., top * .8))], 1.)
    if top > 3:
        cv.hair([(x0, y0 + top * .45), (x1, y0 + top * .45)])
    for i in range(1, n):
        jx = x0 + sw * i
        th = vh * .9
        tw = max(1.6, vh * .16)
        cap = C._ell_pts(jx, y0 + top + tw, tw, tw, 12)[:-1]
        skirt = [(jx - tw * .6, y0 + top + tw * 1.6), (jx + tw * .6, y0 + top + tw * 1.6),
                 (jx + tw * 1.2, y0 + top + th), (jx - tw * 1.2, y0 + top + th)]
        cv.obj([skirt], .5)
        xx = jx - tw
        while xx < jx + tw:
            cv.hair([(jx + (xx - jx) * .5, y0 + top + tw * 1.8), (xx, y0 + top + th - .3)])
            xx += 1.5
        cv.obj([cap], .5)


def scene(x, y, w, h, seed=0, clip_d=None):
    """The whole curtained window filling x..x+w, y..y+h (and, if clip_d is given, the field
    that outline describes): no white left but highlights."""
    rng = random.Random(seed)
    cv = C.Canvas()
    big = h > 70
    bleed = 6 if clip_d else 0
    vh = max(6., min(h * .2, 34.))
    cw = w * (.23 if big else .19)
    sill_h = max(2.5, h * .05)
    wy0 = y + vh * .55
    wy1 = y + h - (h * .14 if big else sill_h + 1.5)
    ww = w - 2 * cw + cw * .5
    wx0 = x + (w - ww) / 2
    wx1 = wx0 + ww
    fr = max(2., min(ww, h) * .035)
    gx0, gx1, gy0, gy1 = wx0 + fr, wx1 - fr, wy0 + fr, wy1 - fr
    mx = (gx0 + gx1) / 2
    lw = (gx1 - gx0 - fr) / 2
    L0, L1 = (gx0, mx - fr / 2), (mx + fr / 2, gx1)
    lh = gy1 - gy0
    _sky(cv, _rect(L0[0], gy0, L0[1], gy1), 2)
    _sky(cv, _rect(L1[0], gy0, L1[1], gy1), 1.5)
    # the right light: moon and stars above the let-down shade
    hem = gy0 + lh * .55
    mr = max(1.8, min(lw, lh) * .1)
    mcx, mcy = L1[0] + lw * .78, hem + (gy1 - hem) * .5 + 1.5
    cv.obj([C._ell_pts(mcx, mcy, mr + .8, mr + .8, 24)[:-1]], 0)
    cres = _crescent(mcx, mcy, mr, -.6)
    cv.obj([cres], .5)
    if mr > 5:
        cv.hair(C.hatch_poly(cres, 0, 2, .25, .8))
    for sx, sy, ss in ((L1[0] + lw * .2, hem + (gy1 - hem) * .55 + 1, 1.6), (L1[0] + lw * .33, hem + (gy1 - hem) * .8, 1.1)):
        ss = max(ss, min(lw, lh) * .045)
        cv.obj([[(sx, sy - ss * 1.6), (sx + ss * .4, sy), (sx, sy + ss * 1.6), (sx - ss * .4, sy)]], 0)
        cv.obj([[(sx - ss * 1.6, sy), (sx, sy - ss * .4), (sx + ss * 1.6, sy), (sx, sy + ss * .4)]], 0)
    # the left light: the sun over the hills and Mt. Hood
    sr = max(2.5, min(lw * .2, lh * .17))
    _sun(cv, L0[0] + lw * .38, gy0 + lh * .58, sr)
    _hills(cv, L0[0], L0[1], gy1, lh * .3, rng.randrange(1 << 20), hood=lh > 18)
    _rolled_shade(cv, L0[0], L0[1], gy0, max(2.5, lh * .1))
    _roman_shade(cv, L1[0], L1[1], gy0, hem, max(2, int(round((hem - gy0) / 6.5))))
    bars = [_rect(wx0, wy0, wx1, gy0), _rect(wx0, gy1, wx1, wy1), _rect(wx0, gy0, gx0, gy1),
            _rect(gx1, gy0, wx1, gy1), _rect(mx - fr / 2, gy0, mx + fr / 2, gy1)]
    for b in bars:
        cv.obj([b], .5)
        if fr >= 3:
            cv.hair(C.hatch_poly(b, 45, 3, .5, .6))
    _drumstick(cv, (L1[0] + L1[1]) / 2, hem + 1.5, min(lh * .32, (gy1 - hem) * .85))
    sx0, sx1 = wx0 - fr * 1.6, wx1 + fr * 1.6
    cv.obj([_rect(sx0, wy1, sx1, wy1 + sill_h)], 1.)
    cv.heavy([(sx0 + 1, wy1 + sill_h - .75), (sx1 - 1, wy1 + sill_h - .75)])
    if sill_h > 3:
        cv.hair([(sx0 + 1, wy1 + 1.25), (sx1 - 1, wy1 + 1.25)])
    yb = y + h + bleed
    tie_t = .52 if big else .5
    for side in (-1, 1):
        xo = (x - bleed) if side < 0 else (x + w + bleed)
        wt = cw + bleed
        _curtain(cv, side, xo, y + vh * .5, yb, wt, wt * .5, wt * .82, tie_t, rng.randrange(1 << 20))
        _tieback(cv, side, xo, y + vh * .5 + (yb - y - vh * .5) * tie_t, wt * .5, max(2.5, h * .045))
    _valance(cv, x - bleed, x + w + bleed, y - bleed + .5, vh + bleed, rng.randrange(1 << 20))
    wall = C.dark_ground((x - 8, y - 8, w + 16, h + 16) if clip_d else (x, y, w, h), "D")
    body = wall + cv.svg()
    if clip_d:
        cid = C._uid("tw", x, y, w, h, seed)
        return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
    return C._clip(C._uid("tr", x, y, w, h, seed), x, y, w, h, body)


# ---------------------------------------------------------------------------------------------
# layouts
# ---------------------------------------------------------------------------------------------

def salver_cameo(w, h, seed):
    """the tailpiece: an oval cameo, the ground worked dark in level burin lines, and lit out of it
    Alfred's silver salver in perspective with its gadrooned rim, the coffee pot, a cup and saucer
    steaming, and a dog biscuit laid beside the cup"""
    cx, cy, a, b = box_fit(w, h, 2.6, pad=4)
    clean = shape_pts(cx, cy, a, b, "oval", 160)
    cv = Canvas()
    cv.obj([clean], 0)
    tone_hatch(cv, clean, lambda x, y: .55 + .3 * ((x - cx) / a) ** 2 + .15 * (y - cy) / b, 0., 1.5, .82, 90.)
    # the salver: an ellipse in perspective, the rim gadrooned, the well shaded on its far side
    sy = cy + b * .42
    ra, rb = a * .78, b * .38
    tray = _ell(cx, sy, ra, rb, 60)[:-1]
    cv.obj([tray], 1.)
    tone_hatch(cv, tray, lambda x, y: .05 + .45 * max(0., (sy - y) / rb) + .2 * max(0., (x - cx) / ra), 0., 1.5, None)
    well = _ell(cx, sy + rb * .06, ra * .82, rb * .72, 48)
    cv.hair(well)
    for i in range(36):
        t = _TAU * i / 36
        px, py = cx + ra * .91 * _m.cos(t), sy + rb * .91 * _m.sin(t)
        cv.hair([(px, py), (cx + ra * .99 * _m.cos(t + .04), sy + rb * .99 * _m.sin(t + .04))])
    # the coffee pot: a tall silver body, swelling, its lid and finial, spout to the left, handle right
    ph = b * 1.25
    px0, pb = cx + a * .12, sy + rb * .05
    prof = [(.22, 0), (.3, .04), (.38, .14), (.42, .3), (.38, .48), (.26, .64), (.2, .72), (.26, .76), (.22, .82), (.14, .9), (.05, .96)]
    body = [(px0 + u * ph, pb - v * ph) for u, v in prof] + [(px0 - u * ph, pb - v * ph) for u, v in prof[::-1]]
    for _ in range(2):
        body = [pt for i in range(len(body)) for pt in
                (((3 * body[i][0] + body[(i + 1) % len(body)][0]) / 4, (3 * body[i][1] + body[(i + 1) % len(body)][1]) / 4),
                 ((body[i][0] + 3 * body[(i + 1) % len(body)][0]) / 4, (body[i][1] + 3 * body[(i + 1) % len(body)][1]) / 4))]
    spout = [(px0 - .36 * ph, pb - .3 * ph), (px0 - .62 * ph, pb - .72 * ph), (px0 - .66 * ph, pb - .7 * ph), (px0 - .42 * ph, pb - .5 * ph)]
    cv.obj([spout], 1.)
    tone_hatch(cv, spout, lambda x, y: .3, 60., 1.5, None)
    handle = [(px0 + .4 * ph, pb - .2 * ph), (px0 + .62 * ph, pb - .35 * ph), (px0 + .6 * ph, pb - .66 * ph), (px0 + .36 * ph, pb - .7 * ph)]
    cv.obj([], 0)
    cv.heavy(handle)
    cv.obj([body], 1.)
    # polished silver: a dark band of reflection down the right, the window's light as a white stripe
    tone_hatch(cv, body, lambda x, y: (.85 if .12 < (x - px0) / ph < .32 else (.35 if (x - px0) / ph > -.05 else .0)), 90., 1.5, .8, 0.)
    cv.line([(px0 - ph * .3, pb - ph * .62), (px0 + ph * .3, pb - ph * .62)])
    cv.obj([_ell(px0, pb - ph * 1.02, ph * .05, ph * .05, 8)[:-1]], 1.)
    # the cup and saucer, steam rising
    ux, uy = cx - a * .38, sy + rb * .1
    sauc = _ell(ux, uy, ra * .26, rb * .3, 28)[:-1]
    cv.obj([sauc], 1.)
    cv.hair(_ell(ux, uy, ra * .17, rb * .18, 24))
    cup = [(ux - ra * .13, uy - rb * .9), (ux + ra * .13, uy - rb * .9), (ux + ra * .1, uy - rb * .05), (ux - ra * .1, uy - rb * .05)]
    cv.obj([cup], 1.)
    tone_hatch(cv, cup, lambda x, y: .1 + .7 * max(0., (x - ux) / (ra * .13)), 90., 1.5, None)
    rim = _ell(ux, uy - rb * .9, ra * .13, rb * .16, 20)[:-1]
    cv.obj([rim], 1.)
    tone_hatch(cv, rim, lambda x, y: .7, 0., 1.5, None)
    cv.line([(ux + ra * .12, uy - rb * .75), (ux + ra * .2, uy - rb * .6), (ux + ra * .11, uy - rb * .35)])
    for k in range(2):
        cv.obj([], 0)
        cv.hair([(ux - ra * .03 + k * ra * .06 + _m.sin(t * 4 + k) * ra * .03, uy - rb * 1.1 - t * b * .7) for t in [j / 8 for j in range(9)]])
    # the dog biscuit: a bone, laid on the tray in front of the cup
    bx, by, bl = cx - a * .02, sy + rb * .5, a * .3
    bone = []
    for i in range(32):
        t = _TAU * i / 32
        ex = _m.cos(t)
        lobe = 1 + .55 * max(0., abs(ex) - .6) / .4 * (1 + .6 * _m.cos(4 * t))
        bone.append((bx + bl * .5 * _m.copysign(abs(ex) ** .6, ex), by + rb * .22 * _m.sin(t) * lobe))
    cv.obj([bone], 1.)
    tone_hatch(cv, bone, lambda x, y: .1 + .5 * max(0., (y - by) / (rb * .2)), 20., 1.5, None)
    for k in range(3):
        cv.obj([_ell(bx - bl * .18 + k * bl * .18, by - rb * .02, .5, .5, 6)[:-1]], .5)
    return clean, cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    uid = f"al{int(w)}x{int(h)}"
    clean, body = salver_cameo(w, h, seed)
    return vignette(w, h, uid, clean, body, clean)
