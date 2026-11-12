"""coast-05 Coast happenings, merged into Shellfish check (edition plan: tailpiece, about 8%).

A Bewick tailpiece: a patch of wet strand at the tide line (the last wave's lace, ripple marks lit on
the crest and hatched on the lee, shell bits) fraying out into a light stippled ground, with a
Pacific razor clam and a Dungeness crab lying on it in full relief, modelled in swelling burin tone.
Easter egg (the plan's): the crab holds Parker's crossed drumsticks up in its claws. At taller sizes
Haystack Rock and the Needles stand behind the strand."""
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


CR = ' shape-rendering="crispEdges"'


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dpl(pts, close=False):
    if len(pts) < 2:
        return ""
    o = "M" + f(pts[0][0]) + "," + f(pts[0][1])
    px, py = pts[0]
    for x, y in pts[1:]:
        o += "l" + f(x - px) + "," + f(y - py)
        px, py = x, y
    return o + ("z" if close else "")


def pip(x, y, poly):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def runs(y, x0, x1, test, step=.5, minlen=.8):
    """Horizontal runs at row y where test(x) holds."""
    out = []
    a = None
    x = x0
    while x <= x1:
        ok = test(x)
        if ok and a is None:
            a = x
        elif not ok and a is not None:
            if x - a >= minlen:
                out.append((a, x))
            a = None
        x += step
    if a is not None and x1 - a >= minlen:
        out.append((a, x1))
    return out


def hpath(segs):
    return "".join(f"M{f(a)},{f(y)}h{f(b - a)}" for y, a, b in segs)


def P(d, w=.5, crisp=False, fill="none"):
    if not d:
        return ""
    return f'<path d="{d}" fill="{fill}" stroke="#000" stroke-width="{f(w)}"{CR if crisp else ""}/>'


def F(d, fill="#fff", rule=""):
    if not d:
        return ""
    r = f' fill-rule="{rule}"' if rule else ""
    return f'<path d="{d}" fill="{fill}" stroke="none"{r}/>'


def row05(y):
    return math.floor(y * 2) / 2 + .25


def row1(y):
    return round(y * 2) / 2


# ------------------------------------------------------------------------------------------
# the vignette: Haystack Rock at Cannon Beach
# ------------------------------------------------------------------------------------------

HAY = [(0, 0), (.02, .2), (.045, .45), (.07, .66), (.1, .8), (.14, .89), (.2, .95), (.28, .99), (.36, 1.0),
       (.44, .985), (.5, .96), (.55, .93), (.6, .88), (.64, .8), (.67, .72), (.71, .66), (.76, .62), (.8, .58),
       (.84, .5), (.88, .38), (.92, .25), (.96, .12), (1, 0)]


def ext_at(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    if len(xs) < 2:
        return None
    return min(xs), max(xs)


def engrave_rock(poly, by, top, rng, fine=1.):
    """Basalt carved as facets: the rock is cut into a jittered grid of planes in its own (u, t)
    coordinates; each plane is hatched by its tone (lit from the left, darkening to the right),
    seams are cut in 1 px and the shadow-side rim in 1.5 px. Returns (white_fill_d, svg)."""
    H = by - top

    def at(u, t):
        t = min(t, .985)
        y = by - t * H
        e = ext_at(poly, y)
        if not e:
            return None
        l, r = e
        if 0 < u < 1:
            u = min(.99, max(.01, u + .06 * math.sin(t * 5.5 + u * 9)))
        return (l + u * (r - l), y)
    ncol = max(3, int(7 * fine))
    us = [0.] + sorted(rng.uniform(.1, .9) for _ in range(ncol - 1)) + [1.]
    half, one, seams = [], [], []
    for i in range(len(us) - 1):
        nrow = rng.randint(2, 4)
        ts = [0.] + sorted(rng.uniform(.12, .85) for _ in range(nrow - 1)) + [1.]
        for j in range(len(ts) - 1):
            u0, u1, t0, t1 = us[i], us[i + 1], ts[j], ts[j + 1]
            ed = []
            for k in range(7):
                ed.append(at(u0 + (u1 - u0) * k / 6, t0))
            for k in range(7):
                ed.append(at(u1, t0 + (t1 - t0) * k / 6))
            for k in range(7):
                ed.append(at(u1 - (u1 - u0) * k / 6, t1))
            for k in range(7):
                ed.append(at(u0, t1 - (t1 - t0) * k / 6))
            ed = [q for q in ed if q]
            if len(ed) < 4:
                continue
            um = (u0 + u1) / 2
            tone = um * 3.2 + rng.uniform(-.7, .7) + (.4 if t0 < .1 else 0)
            if tone < .8:
                half += C.hatch_poly(ed, 60, 3, rng.uniform(0, 3))
                half += C.hatch_poly(ed, 0, 3, rng.uniform(0, 3))
            elif tone < 1.6:
                half += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
            elif tone < 2.4:
                one += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
            else:
                one += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
                half += C.hatch_poly(ed, -30, 3, rng.uniform(0, 3))
            if t1 < 1:
                seams.append([q for q in (at(u0 + (u1 - u0) * k / 6, t1) for k in range(7)) if q])
        seams.append([q for q in (at(us[i + 1], k / 12 * .97) for k in range(13)) if q])
    o = [P("".join(dpl(p) for p in half), .5), P("".join(dpl(p) for p in one), 1),
         P("".join(dpl(p) for p in seams if p and len(p) > 1), 1)]
    n = len(poly)
    peak = min(range(n), key=lambda i: poly[i][1])
    o.append(P(dpl(poly[peak:]), 1.5))
    o.append(P(dpl(poly[:peak + 1]), 1))
    return dpl(poly, True), "".join(o)


def heron(x, y, s, flip=False):
    """A great blue heron standing at (x, y) = feet, s = height: body tilted, S-neck, dagger bill,
    black crest plume, dark wing coverts in bulino."""
    sx = -1 if flip else 1

    def T(px, py):
        return (x + sx * px * s, y - py * s)
    out = [(-.36, .32), (-.28, .41), (-.12, .53), (.04, .6), (.13, .63), (.15, .7), (.1, .78), (.09, .86),
           (.13, .92), (.2, .95), (.25, .955), (.46, .925), (.25, .92), (.21, .9), (.17, .86), (.17, .8),
           (.22, .72), (.23, .63), (.2, .54), (.13, .45), (0, .4), (-.18, .36)]
    sil = [T(*q) for q in out]
    o = [F(dpl(sil, True)), P(dpl(sil, True), 1)]
    # wing: closed, dark, feathered in bulino
    wing = [T(-.34, .33), T(-.2, .44), T(0, .54), T(.12, .58), T(.12, .5), T(0, .44), T(-.2, .37)]
    o.append(F(dpl(wing, True), C.pat("M")) + P(dpl(wing, True), 1))
    fl = [[T(.1 - k * .06, .52 - k * .03), T(-.25 - k * .02, .37 - k * .005)] for k in range(4)]
    o.append(P("".join(dpl(p) for p in fl), .5))
    # neck streaks and breast plumes
    o.append(P(dpl([T(.155, .62), T(.13, .72), T(.12, .8)]) + dpl([T(.16, .52), T(.1, .44)]) + dpl([T(.12, .5), T(.06, .43)]), .5))
    o.append(F(dpl([T(.15, .935), T(-.02, .95), T(.15, .92)], True), "#000"))
    o.append(P(dpl([T(.25, .938), T(.46, .925)]), .5))
    eye = T(.2, .935)
    o.append(F(f"M{f(eye[0] - .7)},{f(eye[1])}a.7,.7 0 1,0 1.4,0a.7,.7 0 1,0 -1.4,0z", "#000"))
    legs = [[T(.02, .42), T(.01, .2), T(0, 0)], [T(.07, .43), T(.08, .21), T(.1, 0)],
            [T(-.06, 0), T(.05, 0)], [T(.05, 0), T(.17, 0)]]
    o.append(P("".join(dpl(p) for p in legs), 1))
    return "".join(o)


def paw(x, y, s, ang):
    """One dog paw print (pad + four toes) as closed paths, centred (x, y)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def T(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    o = ""
    for (px, py, rx, ry) in [(0, .35, .55, .42), (-.55, -.3, .2, .27), (-.2, -.62, .2, .27), (.2, -.62, .2, .27), (.55, -.3, .2, .27)]:
        o += dpl([T(px + rx * math.cos(t * math.pi / 6), py + ry * math.sin(t * math.pi / 6)) for t in range(12)], True)
    return o


def vignette_scene(x0, y0, W, H, clip_d, seed=0, mode="tall", cid="cvs"):
    """Fill the whole box (clipped to clip_d) with the Cannon Beach scene."""
    rng = random.Random(seed * 31 + 7)
    o = []
    x1, y1 = x0 + W, y0 + H
    band = mode == "band"
    hz = y0 + H * (.6 if band else .56)
    shore = y0 + H * (1.1 if band else .74)
    sx, sy, sr = x0 + W * .22, hz - H * .015, H * (.13 if band else .1)
    rbw = W * (.3 if band else .36)
    rbh = min(H * (.5 if band else .42), (hz - y0) * .82, rbw * .72)
    rbx = x0 + W * (.46 if band else .42)
    rock = [(rbx + u * rbw, hz + 1.5 - t * rbh) for u, t in
            [(u + rng.uniform(-.006, .006) * (0 < u < 1), t * rng.uniform(.98, 1.02) if 0 < t < 1 else t) for u, t in HAY]]
    needles = []
    nx = rbx + rbw * 1.08
    for (dx, wv, hv) in ((0, .09, .34), (.13, .06, .22), (.23, .045, .12)):
        bx = nx + rbw * dx
        bw_, bh_ = rbw * wv, rbh * hv
        needles.append([(bx, hz + 1), (bx + bw_ * .15, hz - bh_ * .6), (bx + bw_ * .38, hz - bh_), (bx + bw_ * .6, hz - bh_ * .92),
                        (bx + bw_ * .8, hz - bh_ * .45), (bx + bw_, hz + 1)])
    head = [(x0 - 2, hz + .5), (x0 - 2, hz - H * .15)]
    for i in range(1, 25):
        t = i / 24
        head.append((x0 - 2 + W * .3 * t, hz - H * .15 * (1 - t ** 1.6) - (math.sin(i * 2.3) * .9 + .9) * (1 - t)))
    head.append((x0 + W * .3, hz + .5))
    head = [(x0 + x1 - hx_, hy_) for hx_, hy_ in head]  # Tillamook Head lies north: right

    # ---- sky: ruled at pitch 2, doubled to pitch 1 in the deep upper sky; light cloud banks
    #      (pitch 3) with scalloped rims; rays of the sun thin the lines out to pitch 4.
    rays = 18

    def in_ray(x, y):
        a = math.atan2(y - sy, x - sx)
        return (int((a + math.pi) / (2 * math.pi) * rays * 2) % 2) == 0

    clouds = []
    for i in range(3):
        cx_ = x0 + W * (.12 + .33 * i + rng.uniform(-.05, .05))
        cy_ = y0 + (hz - y0) * rng.uniform(.3, .5)
        cw_ = W * rng.uniform(.18, .26)
        ch_ = (hz - y0) * rng.uniform(.07, .1)
        top_ = [(cx_ - cw_ / 2 + cw_ * t, cy_ - ch_ * (math.sin(math.pi * t) ** .7) * (.7 + .3 * abs(math.sin(t * math.pi * 4 + i))))
                for t in [k / 24 for k in range(25)]]
        bot_ = [(cx_ + cw_ / 2 - cw_ * t, cy_ + ch_ * .25 * math.sin(math.pi * t)) for t in [k / 12 for k in range(1, 12)]]
        clouds.append(top_ + bot_)
    sky = []
    y = row05(y0) - .5
    k = 0
    deep = y0 + (hz - y0) * .2
    while y < hz:
        incl = [c for c in clouds if min(q[1] for q in c) - 1 < y < max(q[1] for q in c) + 1]

        def tst(x, y=y, k=k):
            if (x - sx) ** 2 + (y - sy) ** 2 < (sr * 1.25) ** 2:
                return False
            if pip(x, y, head):
                return False
            for c in incl:
                if pip(x, y, c):
                    return k % 3 == 0
            if k % 2 == 1 and in_ray(x, y) and math.hypot(x - sx, y - sy) < W * .55:
                return False
            return True
        for a, b in runs(y, x0 - 1, x1 + 1, tst):
            sky.append((y, a, b))
        if y < deep:
            yy = y + 1
            frac = max(0., (yy - y0) / (deep - y0) - .55) / .45

            def t2(x, yy=yy):
                if (x - sx) ** 2 + (yy - sy) ** 2 < (sr * 2.2) ** 2:
                    return False
                for c in incl:
                    if pip(x, yy, c):
                        return False
                return True
            for a, b in runs(yy, x0 - 1, x1 + 1, t2):
                # break the doubled rule into dashes as it fades toward the horizon
                x = a
                while x < b:
                    L = rng.uniform(4, 30) * (1 - frac * .7)
                    if b - x > 1.5:
                        sky.append((yy, x, min(b, x + L)))
                    x += L + rng.uniform(1, 2 + 10 * frac)
        y += 2
        k += 1
    o.append(P(hpath(sky), .5, True))
    o.append(P(''.join(dpl(c[:25]) for c in clouds), .5))
    sun = []
    y = row05(sy - sr)
    while y < hz:
        dd = sr * sr - (y - sy) ** 2
        if dd > 0:
            hw = math.sqrt(dd)
            sun.append((y, sx - hw, sx + hw))
        y += 3
    o.append(P(hpath(sun), .5, True))
    o.append(P(dpl([(sx + sr * math.cos(t), sy + sr * math.sin(t)) for t in [math.pi + math.pi * i / 30 for i in range(31)]]), 1))
    # headland: a forested dark mass, 1 px rules at pitch 2
    hd = []
    y = row1(hz - H * .2)
    while y < hz:
        for a, b in runs(y, x1 - W * .32, x1 + 2, lambda x, y=y: pip(x, y, head)):
            hd.append((y, a, b))
        y += 2
    o.append(P(hpath(hd), 1, True))
    o.append(P(dpl(head[1:-1]), 1))
    trees = []
    for i in range(2, 22, 2):
        px, py = head[i]
        trees.append([(px - 1, py + .5), (px, py - 2.2), (px + 1, py + .5)])
    o.append(P("".join(dpl(p) for p in trees), .5))
    # ---- sea
    sea_half, sea_one = [], []
    y = row05(hz) + .5
    while y < shore:
        d = (y - hz) / max(1, shore - hz)
        pitch = 1.5 if d < .35 else 2
        x = x0 - 1
        while x < x1 + 1:
            L = rng.uniform(3, 10 + 25 * d)
            gap = rng.uniform(.8, 2.2 + 1.5 * d)
            if abs(x - sx) < sr * (1 - d * .3):
                L *= .4
                gap *= 2.2
            seg = (y, x, min(x + L, x1 + 1))
            refl = rbx + rbw * .05 < x < rbx + rbw * .9 and d < .5
            (sea_one if (refl and rng.random() < .8) or rng.random() < .07 else sea_half).append(seg)
            x += L + gap
        y += pitch
    sea_one = [(row1(yy), a, b) for yy, a, b in sea_one]
    o.append(P(hpath(sea_half), .5, True))
    o.append(P(hpath(sea_one), 1, True))
    o.append(P(f"M{f(x0 - 1)},{f(row1(hz))}h{f(W + 2)}", 1, True))
    # ---- rocks
    for nd in needles:
        dn, sv = engrave_rock(nd, hz + 1, min(p[1] for p in nd), rng, fine=.3)
        o.append(F(dn) + sv)
    rd, rs = engrave_rock(rock, hz + 1.5, min(p[1] for p in rock), rng)
    o.append(F(rd) + rs)
    tick = []
    for i in range(7):
        px = rbx + rbw * (.28 + i * .04)
        topy = min((p[1] for p in rock if abs(p[0] - px) < rbw * .05), default=hz)
        tick.append(f"M{f(px)},{f(topy - .3)}v-1.6")
    o.append(P("".join(tick), 1))
    fx0, fx1 = rbx - rbw * .08, nx + rbw * .3
    foam = [(fx0, hz + 1.5)]
    n = 30
    for i in range(n + 1):
        t = i / n
        foam.append((fx0 + (fx1 - fx0) * t, hz + 2.5 + math.sin(t * math.pi) * 2.5 + (math.sin(i * 1.9) * .8)))
    for i in range(n, -1, -1):
        foam.append((fx0 + (fx1 - fx0) * i / n, hz + 1.5))
    o.append(F(dpl(foam, True)))
    curls = []
    for i in range(int((fx1 - fx0) / 5)):
        cx_ = fx0 + 3 + i * 5 + rng.uniform(-1, 1)
        cy_ = hz + 3 + rng.uniform(-.5, .8)
        curls.append([(cx_ - 2, cy_ + .8), (cx_ - .5, cy_ - .6), (cx_ + 1, cy_ - .2), (cx_ + .6, cy_ + .6)])
    o.append(P("".join(dpl(p) for p in curls), .5))
    if not band:
        stx, sty = rbx + rbw * .42, y0 + (hz - rbh - y0) * .45 + H * .02
        sr2 = H * .035
        star = []
        for i in range(16):
            a = -math.pi / 2 + i * math.pi / 8
            rr = sr2 * (1 if i % 4 == 0 else (.45 if i % 2 == 0 else .25))
            star.append((stx + rr * math.cos(a), sty + rr * math.sin(a)))
        R = sr2 * 1.3
        o.append(F(f"M{f(stx - R)},{f(sty)}a{f(R)},{f(R)} 0 1,0 {f(2 * R)},0a{f(R)},{f(R)} 0 1,0 {f(-2 * R)},0z"))
        o.append(F(dpl(star, True)) + P(dpl(star, True), .5))
        o.append(F(f"M{f(stx - .8)},{f(sty)}a.8,.8 0 1,0 1.6,0a.8,.8 0 1,0 -1.6,0z", "#000"))
    gulls = []
    for i in range(4 if band else 7):
        gx = x0 + W * rng.uniform(.08, .95)
        gy = y0 + (hz - y0) * rng.uniform(.12, .7)
        if math.hypot(gx - sx, gy - sy) < sr * 1.6 or (rbx - 4 < gx < rbx + rbw + 4 and gy > hz - rbh - 4):
            continue
        s = rng.uniform(2.2, 3.6) * (H / 140 if not band else .7)
        s = max(2., min(4.5, s))
        gulls.append([(gx - s, gy - s * .2), (gx - s * .45, gy - s * .55), (gx, gy), (gx + s * .45, gy - s * .55), (gx + s, gy - s * .2)])
    if gulls:
        o.append(P("".join(dpl(g) for g in gulls), 1))
    if not band:
        wet = []
        y = row05(shore)
        while y < y1 + 1:
            x = x0 - 1
            while x < x1 + 1:
                L = rng.uniform(10, 40)
                wet.append((y, x, x + L))
                x += L + rng.uniform(1.5, 4)
            y += 2
        edge = [(x0 - 2, shore - 2)]
        for i in range(41):
            t = i / 40
            edge.append((x0 - 2 + (W + 4) * t, shore + 1.5 + math.sin(t * 19 + seed) * 1.6 + math.sin(t * 7) * 1.2))
        edge.append((x1 + 2, shore - 2))
        dry_top = [(x0 + W * t, shore + H * .07 + math.sin(t * 5.2 + 1) * H * .03 + t * H * .04) for t in [i / 30 for i in range(31)]]
        dry = [(x0 - 2, dry_top[0][1])] + dry_top + [(x1 + 2, dry_top[-1][1]), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]
        o.append(F(f"M{f(x0 - 2)},{f(shore - 2)}H{f(x1 + 2)}V{f(y1 + 2)}H{f(x0 - 2)}z"))
        o.append(P(hpath(wet), .5, True))
        o.append(F(dpl(edge, True)) + P(dpl(edge[1:-1]), .5))
        o.append(F(dpl(dry, True), C.pat("S")) + P(dpl(dry_top), 1))
        hh = H * .3
        hx, hy = x0 + W * .82, shore + H * .055
        o.append(heron(hx, hy, hh, flip=True))
        o.append(P(f"M{f(hx - 4)},{f(row05(hy + 1.5))}h9M{f(hx - 2)},{f(row05(hy + 3.5))}h5", .5, True))
        lx, ly, lw, lh = x0 + W * .04, y1 - H * .085, W * .3, H * .055
        logp = [(lx + lw * t, ly - lh * .5 + math.sin(t * 3) * lh * .12) for t in [i / 16 for i in range(17)]]
        logp += [(lx + lw * t, ly + lh * .5 + math.sin(t * 3) * lh * .12) for t in [i / 16 for i in range(16, -1, -1)]]
        o.append(F(dpl(logp, True)) + P(dpl(logp, True), 1))
        grain = []
        for j in range(1, int(lh / 1.6)):
            v = -.5 + j * 1.6 / lh
            grain.append([(lx + lw * t + 2, ly + lh * v + math.sin(t * 3) * lh * .12 + math.sin(t * 25 + j) * .35)
                          for t in [i / 30 for i in range(30)] if t < .97])
        o.append(P("".join(dpl(g) for g in grain[len(grain) // 2:]), 1))
        o.append(P("".join(dpl(g) for g in grain[:len(grain) // 2]), .5))
        ex, ey = lx + lw, ly + math.sin(3) * lh * .12
        el = lambda rx, ry: f"M{f(ex - rx)},{f(ey)}a{f(rx)},{f(ry)} 0 1,0 {f(2 * rx)},0a{f(rx)},{f(ry)} 0 1,0 {f(-2 * rx)},0z"
        o.append(F(el(lh * .22, lh * .5)) + P(el(lh * .22, lh * .5) + el(lh * .1, lh * .25), .5))
        # EASTER EGG: a dog's paw-print trail across the sand toward the heron
        pr = ""
        ps = max(2.2, H * .014)
        for i in range(9):
            t = i / 8
            px = x0 + W * (.3 + .44 * t)
            py = shore + H * (.085 - .02 * t) + (ps * 1.3 if i % 2 else -ps * 1.3)
            pr += paw(px, py, ps, math.pi / 2 - .12)
        o.append(F(pr) + P(pr, .5))
        gr = []
        for side in (0, 1):
            bx = x0 + (W * .02 if side == 0 else W * .96)
            for i in range(7):
                a = -math.pi / 2 + (i - 3) * .22
                L = H * rng.uniform(.06, .11)
                gr.append([(bx + i * 1.2, y1 + 1), (bx + i * 1.2 + math.cos(a) * L * .5 + 1, y1 + 1 + math.sin(a) * L * .55),
                           (bx + i * 1.2 + math.cos(a) * L + (i - 3) * .9, y1 + 1 + math.sin(a) * L)])
        o.append(P("".join(dpl(g) for g in gr), 1))
    body = "".join(o)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------
# drawn lettering for the ribbon
# ------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


GLYPHS = {
    "C": (.62, [_arc(.33, .5, .31, .5, -.28 * math.pi, -1.72 * math.pi, 14)]),
    "A": (.7, [[(0, 1), (.35, 0), (.7, 1)], [(.14, .64), (.56, .64)]]),
    "N": (.66, [[(0, 1), (0, 0), (.66, 1), (.66, 0)]]),
    "O": (.7, [_arc(.35, .5, .35, .5, 0, 2 * math.pi, 18)]),
    "B": (.58, [[(0, 0), (0, 1)], [(0, 0), (.36, 0)] + _arc(.36, .24, .2, .24, -math.pi / 2, math.pi / 2, 6) + [(0, .48)],
                [(0, .48), (.38, .48)] + _arc(.38, .74, .22, .26, -math.pi / 2, math.pi / 2, 6) + [(0, 1)]]),
    "E": (.56, [[(.56, 0), (0, 0), (0, 1), (.56, 1)], [(0, .5), (.44, .5)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    " ": (.45, []),
}


# ------------------------------------------------------------------------------------------
# layouts (adapted from the house frame so the vignette fills the whole carved field)
# ------------------------------------------------------------------------------------------

def razor_clam(cv, x, y, L, ang):
    """a Pacific razor clam lying on the sand, L long, its siphon end at (x, y) side"""
    ca, sa = _m.cos(ang), _m.sin(ang)
    W = L * .3

    def T(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)
    sh = []
    for i in range(25):
        t = i / 24
        sh.append(T(L * t, -W / 2 * (1 - (2 * t - 1) ** 8) ** .5 * (.92 + .08 * t)))
    for i in range(25):
        t = 1 - i / 24
        sh.append(T(L * t, W / 2 * (1 - (2 * t - 1) ** 8) ** .5 * (.92 + .08 * t)))
    # the siphon pushing out of the gape, ringed
    sip = [T(-L * .02, -W * .16), T(-L * .14, -W * .14), T(-L * .18, 0), T(-L * .14, W * .14), T(-L * .02, W * .16)]
    cv.obj([sip], .5)
    for q in (.06, .1, .14):
        cv.hair([T(-L * q, -W * .15), T(-L * q, W * .15)])
    cv.obj([sh], 1.)
    tone_hatch(cv, sh, lit(*T(L * .5, -W * .1), L * .5, W * .6, .0, 1.), _m.degrees(ang) + 90, 1.5, .6)
    # the glossy periostracum: a dark band along the lower edge, a bright stripe left along the top
    for v in (.3, .36, .42):
        cv.hair([T(L * .04, W * v), T(L * .5, W * (v + .04)), T(L * .96, W * v)])
    cv.line([T(L * .08, W * .44), T(L * .5, W * .48), T(L * .92, W * .44)])
    cv.hair([T(L * .1, -W * .18), T(L * .55, -W * .22), T(L * .9, -W * .16)])


def dungeness(cv, cx, cy, s, sticks=True):
    """a Dungeness crab from above, carapace s wide, holding Parker's crossed drumsticks up in its claws"""
    a, b = s / 2, s * .34
    # walking legs first, under the shell: four a side, jointed, the tips sharp
    for sd in (-1, 1):
        for i in range(4):
            ba = -.25 + i * .32
            bx = cx + sd * a * .78 * _m.cos(ba)
            by = cy + b * .55 * _m.sin(ba) + b * .1
            l1, l2, l3 = s * .2, s * .17, s * .12
            a1 = ba + (-.3 + i * .12)
            p1 = (bx + sd * l1 * _m.cos(a1), by + l1 * _m.sin(a1) - s * .03)
            a2 = a1 + .6 + i * .08
            p2 = (p1[0] + sd * l2 * _m.cos(a2), p1[1] + l2 * _m.sin(a2))
            a3 = a2 + .5
            p3 = (p2[0] + sd * l3 * _m.cos(a3), p2[1] + l3 * _m.sin(a3))
            R = _Rib([(bx, by), p1, p2, p3], [s * .05, s * .045, s * .035, .4], [s * .05, s * .045, s * .035, .4])
            cv.obj([R.outline()], .5)
            cv.hair(R.contour(.5, 0, .9))
            cv.hair([(p1[0] - s * .01, p1[1] - s * .03), (p1[0] + s * .01, p1[1] + s * .03)])
            cv.hair([(p2[0] - s * .012, p2[1] - s * .025), (p2[0] + s * .012, p2[1] + s * .025)])
    # the claws, reaching forward and up
    tips = []
    for sd in (-1, 1):
        sx = cx + sd * a * .55
        sy = cy - b * .6
        mer = (sx + sd * s * .2, sy - s * .14)
        car = (mer[0] + sd * s * .02, mer[1] - s * .16)
        arm = _Rib([(sx, sy), mer, car], [s * .05, s * .055, s * .05], [s * .05, s * .055, s * .05])
        cv.obj([arm.outline()], .5)
        cv.hair(arm.contour(.4, 0, .9, minw=1.))
        # the hand (propodus) swelling, then the two fingers closing on a drumstick
        hx, hy = car[0] - sd * s * .04, car[1] - s * .12
        hand = [(car[0] - s * .07, car[1] + s * .02), (car[0] + s * .07, car[1] + s * .02),
                (hx + s * .065, hy), (hx + s * .03, hy - s * .07), (hx - s * .05, hy - s * .05), (hx - s * .07, hy)]
        cv.obj([hand], 1.)
        tone_hatch(cv, hand, lit(hx, hy - s * .02, s * .07, s * .07, .05, .95), 60., 1.5, .6)
        f1 = [(hx - sd * s * .02, hy - s * .06), (hx - sd * s * .09, hy - s * .15), (hx - sd * s * .05, hy - s * .07)]
        f2 = [(hx + sd * s * .03, hy - s * .07), (hx - sd * s * .04, hy - s * .17), (hx + sd * s * .0, hy - s * .07)]
        cv.obj([f1, f2], .5)
        for k in range(3):
            cv.hair([(hx - s * .05 + k * s * .04, hy - s * .02), (hx - s * .045 + k * s * .04, hy - s * .035)])
        tips.append((hx - sd * s * .055, hy - s * .13))
    # the carapace: a broad fan, toothed along the front edge, modelled toward the shadowed rear
    car_ = []
    for i in range(61):
        t = _PI + _PI * i / 60
        tooth = (1 + .045 * abs(_m.sin(t * 9))) if _m.sin(t) < -.15 else 1.
        car_.append((cx + a * _m.cos(t) * tooth, cy + b * .9 * _m.sin(t) * tooth))
    for i in range(1, 30):
        t = _PI * i / 30
        car_.append((cx - a * _m.cos(t) * (1 - .35 * _m.sin(t) ** 2), cy + b * .75 * _m.sin(t) ** .8))
    cv.obj([car_], 1.)
    tone_hatch(cv, car_, lit(cx, cy - b * .1, a, b * 1.1, .02, 1.), 18., 1.5, .62)
    for q in (.8, .6):   # the carapace's sculpture: faint rings echoing the toothed rim
        ring = [(cx + (px - cx) * q, cy + (py - cy) * q - b * (1 - q) * .1) for px, py in car_[5:56]]
        cv.hair(ring)
    # the gastric and cardiac grooves: the H on the back, and granules
    cv.hair([(cx - a * .22, cy - b * .3), (cx - a * .12, cy + b * .05), (cx - a * .2, cy + b * .45)])
    cv.hair([(cx + a * .22, cy - b * .3), (cx + a * .12, cy + b * .05), (cx + a * .2, cy + b * .45)])
    cv.hair([(cx - a * .12, cy + b * .05), (cx + a * .12, cy + b * .05)])
    cv.obj([_ell(cx - a * .1, cy - b * .78, s * .022, s * .022, 6)[:-1], _ell(cx + a * .1, cy - b * .78, s * .022, s * .022, 6)[:-1]], .5)
    if sticks:
        (lx, ly), (rx, ry) = tips
        L = s * .62
        for (tx, ty), sd in (((lx, ly), -1), ((rx, ry), 1)):
            ang = -_PI / 2 - sd * 1.0
            p0 = (tx - _m.cos(ang) * L * .08, ty - _m.sin(ang) * L * .08)
            p1 = (tx + _m.cos(ang) * L * .92, ty + _m.sin(ang) * L * .92)
            R = _Rib([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1], [s * .028, s * .025, s * .012],
                     [s * .028, s * .025, s * .012])
            cv.obj([R.outline()], .5)
            cv.hair(R.contour(.5, 0, 1))
            cv.obj([_ell(p1[0], p1[1], s * .025, s * .025, 8)[:-1]], .5)


def strand(x, y, W, H, seed, band=True, figures=True):
    """the wet sand at the tide line: lace of the last wave along the top, ripple marks, the clam
    and the crab, a few shell bits; the whole field worked, nothing left bare"""
    rng = _r.Random(seed)
    cv = Canvas()
    cv.obj([[(x - 2, y - 2), (x + W + 2, y - 2), (x + W + 2, y + H + 2), (x - 2, y + H + 2)]], 0)
    sea = y + H * (.14 if band else .3)
    # the sea: swells in burin lines, breaking into a lace of foam at the edge
    yy = y - 1
    k = 0
    while yy < sea:
        pts = [(x - 2 + i * 3, yy + .8 * _m.sin(i * .7 + k * 1.3 + seed)) for i in range(int(W / 3) + 3)]
        cv.line(pts) if (sea - yy) > H * .06 else cv.hair(pts)
        yy += 1.5 + 1.5 * (yy - y) / max(1., sea - y)
        k += 1
    lace = []
    for i in range(int(W / 2) + 3):
        lx = x - 2 + i * 2
        lace.append((lx, sea + 1.6 * _m.sin(lx * .21 + seed) + 1.2 * _m.sin(lx * .053)))
    foam = lace + [(x + W + 2, sea + 7), (x - 2, sea + 7)]
    cv.obj([foam], 0)
    cv.line(lace)
    for j in range(int(W / 5)):
        fx = x + rng.uniform(0, W)
        fy = sea + rng.uniform(2.5, 6)
        cv.obj([_ell(fx, fy, rng.uniform(.8, 1.6), .7, 6)[:-1]], .5)
    # ripple marks: sinuous ridges, each crest a lit edge with its lee side hatched into shadow
    yy = sea + 8
    k = 0
    while yy < y + H + 4:
        ph = rng.uniform(0, 6)
        amp = 1.2 + k * .15
        crest = [(x - 2 + i * 2.5, yy + amp * _m.sin(i * .19 + ph) + .6 * _m.sin(i * .53 + ph * 2)) for i in range(int(W / 2.5) + 3)]
        cv.line(crest)
        for i in range(0, len(crest) - 1, 2):
            px, py = crest[i]
            cv.hair([(px, py + 1.2), (px - .8, py + 2.6 + .3 * k)])
        yy += 5.5 + k * .8
        k += 1
    # shell bits and a sand dollar
    for j in range(int(W * H / 900) + 2):
        bx, by = x + rng.uniform(0, W), sea + 8 + rng.uniform(0, max(1., y + H - sea - 10))
        r = rng.uniform(1.2, 2.4)
        cv.obj([[(bx - r, by), (bx, by - r * .8), (bx + r, by)]], .5)
        cv.hair([(bx, by - r * .7), (bx, by)])
    if not figures:
        return cv.svg()
    s = min(H * (.62 if band else .4), W * .3)
    cyc = y + H * (.66 if band else .8)
    razor_clam(cv, x + W * .3 - s * .8, cyc - s * .05, s * 1.5, -.12)
    dungeness(cv, x + W * .64, cyc + s * .02, s * .85)
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    uid = f"co{int(w)}x{int(h)}"
    cx, cy, a, b = box_fit(w, h, 5.2 if h < 110 else 2.2, pad=2)
    # a Bewick tailpiece: a patch of wet strand whose edges fray out into the light ground, the crab
    # and the razor clam lying on it in full relief, free to break the fraying edge
    sil = ragged(shape_pts(cx, cy + b * .15, a, b * .85, "cushion", 160), max(2.5, b * .14), seed)
    x0, y0 = cx - a, cy - b
    if h < 110:
        body = strand(x0, y0, 2 * a, 2 * b, seed, True, False)
        s = 2 * b * 1.0
        fy = cy + b * .3
    else:
        d = f"M{f(x0)},{f(y0)}h{f(2 * a)}v{f(2 * b)}h{f(-2 * a)}z"
        body = (vignette_scene(x0, y0, 2 * a, 2 * b, d, seed) +
                strand(x0, y0 + 2 * b * .6, 2 * a, 2 * b * .4, seed, True, False))
        s = 2 * b * .36
        fy = cy + b * .62
    cv = Canvas()
    razor_clam(cv, cx - a * .52 - s * .6, fy - s * .02, s * 1.35, -.14)
    dungeness(cv, cx + a * .28, fy + s * .02, s * .62)
    return vignette(w, h, uid, sil, body, None, cv.svg())
