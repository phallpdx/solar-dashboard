"""music-04 'New music out' (edition plan: headpiece, about 8%, a row of record spines).

The headpiece stands free on a transparent ground, its frame made of the page's own motif: two open
reels of tape, their flanges modelled in burin tone and the wound pack showing dark through the
windows, with the tape running reel to reel over and under a crate of new LPs. In the crate the
spines pack upright, light and dark, with lettered index cards standing proud, one record pulled up
out of a sleeve engraved with a swallow over village roofs (Shygirl's Swallow!, Steven Wilson's
Requiem for a Village), and the grained crate front with its hand-hole below. Easter egg (the
plan's): a box-set spine lettered SOMASTER. At taller sizes the LP rising like a sun over the
village sits in a ruled roundel above the reels."""
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


_n, _d, _CR = C._n, C._d, C._CR
PI, TAU = math.pi, 2 * math.pi


# ------------------------------------------------------------------------------------------
# small geometry
# ------------------------------------------------------------------------------------------

def _circ(cx, cy, r, n=None):
    n = n or max(24, int(r * 1.2))
    return C._ell_pts(cx, cy, r, r, n)[:-1]


def _arc(cx, cy, r, a0, a1):
    n = max(3, int(abs(a1 - a0) * r / 2.5))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _rot(pts, cx, cy, s, ang, flip=False):
    c, si = math.cos(ang), math.sin(ang)
    out = []
    for x, y in pts:
        if flip:
            x = -x
        out.append((cx + s * (x * c - y * si), cy + s * (x * si + y * c)))
    return out


def _seed(ctx):
    return sum(map(ord, (ctx or {}).get("date", "") + "music-04"))


# ------------------------------------------------------------------------------------------
# the subject
# ------------------------------------------------------------------------------------------

def _sunburst(cv, cx, cy, box, n=36):
    """Alternating dark and light rays from (cx, cy) filling box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    R = math.hypot(max(cx - x0, x1 - cx), max(cy - y0, y1 - cy)) + 4
    cv.obj([[(x0 - 2, y0 - 2), (x1 + 2, y0 - 2), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]], 0)
    for i in range(n):
        a0, a1 = TAU * i / n, TAU * (i + 1) / n
        am = (a0 + a1) / 2
        wedge = [(cx, cy)] + _arc(cx, cy, R, a0, a1)
        if i % 2:
            cv.hair(C.hatch_poly(wedge, math.degrees(am), 1.5))
        else:
            cv.hair(C.hatch_poly(wedge, math.degrees(am), 3., inset=1.))


def _village(cv, x0, x1, base, gh, seed):
    """A dark skyline: rolling ground, cottages and a church with a steeple (Requiem for a Village)."""
    rng = random.Random(seed)
    W = x1 - x0
    pts = [(x0 - 2, base + 4)]
    x = x0 - 2
    steeple_at = x0 + W * rng.uniform(.2, .32)
    done = False
    while x < x1 + 2:
        if not done and x > steeple_at:
            # the church: nave, tower, spire
            nw, nh = gh * .9, gh * .55
            pts += [(x, base - gh * .25), (x, base - gh * .25 - nh), (x + nw * .5, base - gh * .25 - nh * 1.5),
                    (x + nw, base - gh * .25 - nh)]
            tx = x + nw
            pts += [(tx, base - gh * 1.4), (tx + gh * .18, base - gh * 2.6), (tx + gh * .36, base - gh * 1.4),
                    (tx + gh * .36, base - gh * .25)]
            x = tx + gh * .36 + 2
            done = True
            continue
        hw = rng.uniform(.5, .9) * gh
        hh = rng.uniform(.35, .6) * gh
        gy = base - gh * (.12 + .14 * math.sin((x - x0) / W * 5.3 + seed % 7))
        pts += [(x, gy), (x, gy - hh), (x + hw / 2, gy - hh - hw * .45), (x + hw, gy - hh), (x + hw, gy)]
        x += hw + rng.uniform(1.5, gh * .5)
    pts += [(x1 + 2, base + 4)]
    pts += [(x1 + 2, base + gh * 3), (x0 - 2, base + gh * 3)]
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, 0, 1.5))
    cv.hair(C.hatch_poly(pts, 90, 3))
    cv.hair(C.hatch_poly([(x0 - 2, base + 1), (x1 + 2, base + 1), (x1 + 2, base + gh * 3), (x0 - 2, base + gh * 3)], 90, 3))


_SW_R = [(0, -1.0), (.09, -.9), (.12, -.62), (.5, -.66), (.92, -.56), (1.3, -.3), (.88, -.4), (.5, -.33),
         (.15, -.2), (.13, .1), (.42, .8), (.09, .32), (0, .27)]
_SWALLOW = _SW_R + [(-x, y) for x, y in _SW_R[::-1][1:-1]]


def _swallow(cv, cx, cy, s, ang):
    """A barn swallow seen from above, wings swept, tail forked."""
    p = _rot(_SWALLOW, cx, cy, s, ang)
    cv.obj([p], 1.)
    for side in (-1, 1):
        wing = _rot([(side * .12, -.62), (side * .5, -.66), (side * .92, -.56), (side * 1.3, -.3),
                     (side * .88, -.4), (side * .5, -.33), (side * .15, -.2)], cx, cy, s, ang)
        cv.hair(C.hatch_poly(wing, math.degrees(ang) - side * 12, 1.5))
        cv.hair(C.hatch_poly(wing, math.degrees(ang) + 90 - side * 30, 3))
        for k in range(4):     # primaries
            f = .35 + k * .2
            cv.hair(_rot([(side * f, -.62 + .02 * k), (side * (f + .25), -.42 + .03 * k)], cx, cy, s, ang))
    body = _rot([(0, -1.0), (.12, -.62), (.15, -.2), (.13, .1), (0, .27), (-.13, .1), (-.15, -.2), (-.12, -.62)], cx, cy, s, ang)
    cv.line(C.hatch_poly(body, math.degrees(ang) + 90, 1.5))
    for side in (-1, 1):
        tail = _rot([(side * .13, .1), (side * .42, .8), (side * .09, .32)], cx, cy, s, ang)
        cv.hair(C.hatch_poly(tail, math.degrees(ang) + 90 - side * 20, 1.5))
    throat = _rot([(-.07, -.78), (.07, -.78), (.09, -.55), (-.09, -.55)], cx, cy, s, ang)
    cv.obj([throat], 0)
    cv.hair(C.hatch_poly(throat, math.degrees(ang), 3))


def _sleeve(cv, cx, cy, S, ang, seed):
    half = S / 2
    sq = lambda k: _rot([(-k, -k), (k, -k), (k, k), (-k, k)], cx, cy, 1, ang)
    cv.obj([sq(half)], 1.5)
    inner = sq(half - 4)
    cv.hair(C.hatch_poly(sq(half), math.degrees(ang) + 90, 3))       # card grain on the border
    cv.obj([inner], 1.)
    cv.hair(C.hatch_poly(inner, math.degrees(ang) + 45, 2))
    cv.hair(C.hatch_poly(inner, math.degrees(ang) - 45, 3))
    # a pale moon behind the bird
    mx, my = _rot([(-.17 * S, -.05 * S)], cx, cy, 1, ang)[0]
    m = _circ(mx, my, S * .24)
    cv.obj([m], .5)
    cv.hair(C.hatch_poly(m, math.degrees(ang), 3))
    bx, by = _rot([(-.18 * S, .02 * S)], cx, cy, 1, ang)[0]
    _swallow(cv, bx, by, S * .34, ang - .45)


def _p_monogram(cx, cy, r):
    """A script 'P' (polylines in a radius-r box)."""
    stem = [(cx - .2 * r, cy - .55 * r), (cx - .22 * r, cy + .2 * r), (cx - .3 * r, cy + .6 * r),
            (cx - .5 * r, cy + .7 * r)]
    bowl = [(cx - .55 * r, cy - .35 * r)] + [
        (cx + .05 * r + .38 * r * math.cos(t), cy - .25 * r + .32 * r * math.sin(t))
        for t in [-PI * .95 + PI * 1.95 * i / 16 for i in range(17)]]
    return [stem, bowl]


def _record(cv, cx, cy, R, seed):
    disc = _circ(cx, cy, R, 96)
    cv.obj([disc], 1.5)
    rl = R * .34
    rng = random.Random(seed)
    gaps = sorted(rng.uniform(.45, .92) for _ in range(4))
    hi = (-2.25, .9)            # the two sheen wedges
    k = 0
    r = rl + 3
    while r < R - 1.5:
        f = (r - rl) / (R - rl)
        if any(abs(f - g) < .015 for g in gaps):
            cv.line(_arc(cx, cy, r, 0, TAU))      # the band between tracks
            r += 2
            continue
        if k % 2 == 0:
            cv.hair(_arc(cx, cy, r, 0, TAU))
        else:
            hw = .2 + .12 * math.sin(f * PI)
            segs = [(hi[0] + hw, hi[1] - hw), (hi[1] + hw, hi[0] + TAU - hw)]
            for a0, a1 in segs:
                cv.hair(_arc(cx, cy, r, a0, a1))
        k += 1
        r += 1.5
    cv.line(_arc(cx, cy, R - 1.5, 0, TAU))
    # dead wax and the label
    cv.obj([_circ(cx, cy, rl + 2)], .5)
    cv.hair([_arc(cx, cy, rl + 1, 0, TAU)])
    lab = _circ(cx, cy, rl)
    cv.obj([lab], 1.)
    rr = rl * .72
    q = rl - 1.5
    while q > rr:
        cv.hair(_arc(cx, cy, q, 0, TAU))
        q -= 3
    cv.line(_arc(cx, cy, rr, 0, TAU))
    cv.hair(C.hatch_poly(_circ(cx, cy, rr - 1), 0, 3))
    if rl > 9:
        cv.obj([], 0)
        cv.heavy(_p_monogram(cx + rl * .05, cy, rr * .82))
    cv.obj([_circ(cx, cy, max(1.2, rl * .1), 12)], 1.5)
    cv.heavy([_arc(cx, cy, max(.5, rl * .05), 0, TAU)])


def vignette_art(x, y, w, h, field_poly, seed, kind):
    """kind 'disc': record only (medallion); 'full': sleeve + record over the village."""
    cv = C.Canvas()
    xs = [p[0] for p in field_poly]
    ys = [p[1] for p in field_poly]
    box = (min(xs), min(ys), max(xs), max(ys))
    fx0, fy0, fx1, fy1 = box
    fw, fh = fx1 - fx0, fy1 - fy0
    if kind == "disc":
        R = min(fw, fh) / 2 - 5
        cx, cy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        _sunburst(cv, cx, cy, box, 28)
        _record(cv, cx, cy, R, seed)
        return cv.svg()
    R = min(fh * .36, fw * .3)
    cx = fx0 + fw * .62
    cy = fy0 + fh * .47
    _sunburst(cv, cx, cy, box, 40)
    _village(cv, fx0, fx1, fy0 + fh * .9, max(8., fh * .085), seed)
    S = R * 2.05
    sx, sy = cx - R * 1.05, cy - R * .05
    _sleeve(cv, sx, sy, S, -.12, seed)
    _record(cv, cx, cy, R, seed)
    return cv.svg()


# ------------------------------------------------------------------------------------------
# Parker's drumsticks, crossed behind the cartouche
# ------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------
# banner lettering: a bar of swing rhythm; tablet: a sound wave
# ------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------
# layouts (copied from engraving_codex and made bespoke)
# ------------------------------------------------------------------------------------------

def record_band(x, y, W, H, seed):
    """the headpiece: a crate of LPs seen from the front, spines packed upright, one record pulled up
    out of its sleeve, and among the spines a box set lettered SOMASTER"""
    rng = random.Random(seed)
    cv = C.Canvas()
    ctop = y + H * .72                     # the crate's front board
    rh = ctop - y - H * .02
    xx = x + 1
    sp = []
    while xx < x + W - 3:
        sw = rng.choice((1.5, 2., 2., 2.5, 3.))
        sp.append((xx, sw, rh * rng.uniform(.9, 1.)))
        xx += sw
    # pick the pulled record and the box set
    ip = int(len(sp) * (.3 + .1 * rng.random()))
    ib = int(len(sp) * (.66 + .1 * rng.random()))
    bw = max(7., min(12., H * .16))
    for i, (sx, sw, sh) in enumerate(sp):
        if i == ib:
            continue
        top = ctop - sh
        poly = [(sx, ctop + 2), (sx + sw, ctop + 2), (sx + sw, top), (sx, top)]
        cv.obj([poly], .5)
        if sw >= 2.5 and i % 2:
            cv.hair(C.hatch_poly(poly, 0, 1.5))
        elif i % 3 == 0:
            cv.hair([(sx + sw / 2, top + 1), (sx + sw / 2, ctop)])
        if sw >= 2 and i % 5 == 1:
            cv.hair([(sx + .5, top + sh * .3), (sx + sw - .5, top + sh * .3)])
    # index cards between the sections, their tabs standing proud, lettered
    tabs = []
    for k, frac in enumerate((.12, .5, .85)):
        j = int(len(sp) * frac)
        if j in (ip, ib) or j >= len(sp):
            continue
        tx = sp[j][0]
        tw = max(7., rh * .22)
        top = ctop - rh * 1.08
        card = [(tx, ctop), (tx, top + 2), (tx + 1, top), (tx + tw - 1, top), (tx + tw, top + 2), (tx + tw, top + rh * .2),
                (tx + 2, top + rh * .2), (tx + 2, ctop)]
        cv.obj([card], .5)
        cv.hair([(tx + 1, top + rh * .2 + 1), (tx + 1, ctop)])
        tabs.append((tx + tw / 2 + 1, top + rh * .1, "AJS"[k], tw))
    # the pulled record: the sleeve stands up out of the row, the disc half out of it, grooved
    sx, sw, sh = sp[ip]
    S = min(rh * .78, H * .6)
    sl = [(sx - S * .1, ctop), (sx + S * .9, ctop), (sx + S * .9, ctop - S), (sx - S * .1, ctop - S)]
    R = S * .46
    dcx, dcy = sx + S * .4, ctop - S + R * .1
    disc = C._ell_pts(dcx, dcy, R, R, 48)[:-1]
    cv.obj([disc], 1.)
    k = .9
    while k > .38:
        cv.hair(C._ell_pts(dcx, dcy, R * k, R * k, 40))
        k -= .07
    cv.obj([C._ell_pts(dcx, dcy, R * .3, R * .3, 20)[:-1]], .5)
    cv.hair(C.hatch_poly(C._ell_pts(dcx + R * .08, dcy + R * .08, R * .2, R * .2, 14)[:-1], 45, 1.5))
    cv.obj([C._ell_pts(dcx, dcy, R * .04 + .6, R * .04 + .6, 8)[:-1]], .5)
    cv.line([(dcx + R * .55 * math.cos(a), dcy + R * .55 * math.sin(a)) for a in [-.9 + i * .1 for i in range(9)]])
    cv.obj([sl], 1.)
    # the sleeve's art: a swallow over the village roofs
    cv.hair(C.hatch_poly(sl, 0, 2.))
    sb = [(sx + S * .1, ctop - S * .55), (sx + S * .3, ctop - S * .7), (sx + S * .4, ctop - S * .6), (sx + S * .55, ctop - S * .78),
          (sx + S * .5, ctop - S * .58), (sx + S * .7, ctop - S * .5), (sx + S * .4, ctop - S * .5)]
    cv.obj([sb], .5)
    for j in range(4):
        rx = sx + S * (.0 + j * .22)
        roof = [(rx, ctop - S * .08), (rx + S * .1, ctop - S * .24), (rx + S * .2, ctop - S * .08)]
        cv.obj([roof + [(rx + S * .2, ctop - 1), (rx, ctop - 1)]], .5)
        cv.hair(C.hatch_poly(roof + [(rx + S * .2, ctop - 1), (rx, ctop - 1)], 60, 1.5))
    # the box set
    sx, sw, sh = sp[ib]
    bt = ctop - rh * 1.02
    box = [(sx, ctop + 2), (sx + bw, ctop + 2), (sx + bw, bt), (sx, bt)]
    cv.obj([box], 1.)
    for u in (.08, .16, .84, .92):
        cv.hair([(sx + bw * u, bt + 1), (sx + bw * u, ctop)])
    lab = [(sx + bw * .22, ctop - rh * .08), (sx + bw * .78, ctop - rh * .08), (sx + bw * .78, bt + rh * .08), (sx + bw * .22, bt + rh * .08)]
    cv.obj([lab], .5)
    # the crate: slatted, grained, with a hand-hole and corner irons
    front = [(x, ctop), (x + W, ctop), (x + W, y + H), (x, y + H)]
    cv.obj([front], 1.)
    for j in range(int((y + H + 3 - ctop) / 1.5)):
        yy = ctop + 1.5 + j * 1.5
        cv.hair([(x - 3 + i * 4, yy + .5 * math.sin(i * .4 + j * 1.7)) for i in range(int(W / 4) + 3)])
    hx = x + W * .5
    hole = C._ell_pts(hx, ctop + (y + H - ctop) * .5, min(16., W * .05), max(1.5, (y + H - ctop) * .2), 20)[:-1]
    cv.obj([hole], 1.)
    cv.hair(C.hatch_poly(hole, 0, 1.5))
    cv.hair(C.hatch_poly(hole, 90, 1.5))
    cv.line(C._ell_pts(hx, ctop + (y + H - ctop) * .5 + .8, min(16., W * .05) - 1, max(.6, (y + H - ctop) * .2 - 1), 20))
    lt = "".join(motto([(tx - tw * .4, ty), (tx + tw * .4, ty)], ch, rh * .16, .5, None, .9) for tx, ty, ch, tw in tabs)
    return cv.svg() + lt + motto([(sx + bw / 2, ctop - rh * .1), (sx + bw / 2, bt + rh * .1)], "SOMASTER", bw * .62, .5, None, .98)


def tape_reel(cv, cx, cy, r, ph=0.):
    """an open reel of tape: the flange in burin tone, three windows showing the wound pack, the hub"""
    disc = _ell(cx, cy, r, r, 40)[:-1]
    cv.obj([disc], 1.)
    tone_hatch(cv, disc, lit(cx, cy, r, r, .1, .8), 30., 1.5, .7)
    pack = _ell(cx, cy, r * .78, r * .78, 36)[:-1]
    cv.hair(pack + [pack[0]])
    for i in range(3):
        a = ph + _TAU * i / 3
        win = []
        for j in range(9):
            t = a - .55 + 1.1 * j / 8
            win.append((cx + r * .72 * _m.cos(t), cy + r * .72 * _m.sin(t)))
        for j in range(9):
            t = a + .4 - .8 * j / 8
            win.append((cx + r * .3 * _m.cos(t), cy + r * .3 * _m.sin(t)))
        cv.obj([win], 1.)
        k = .66
        while k > .34:   # the wound tape seen through the window: close dark turns
            cv.line([(cx + r * k * _m.cos(t), cy + r * k * _m.sin(t)) for t in [a - .5 + j * .1 for j in range(11)]])
            k -= .045
    hub = _ell(cx, cy, r * .2, r * .2, 16)[:-1]
    cv.obj([hub], 1.)
    for i in range(3):
        a = ph + _TAU * i / 3 + _PI / 3
        cv.line([(cx + r * .08 * _m.cos(a), cy + r * .08 * _m.sin(a)), (cx + r * .19 * _m.cos(a), cy + r * .19 * _m.sin(a))])


def tape_headpiece(w, h, seed):
    """the headpiece: a crate of new LPs between two open reels, the tape running from reel to reel
    over and under the crate as its frame"""
    r = h * .46
    Wd = min(w - 4, h * 9.5)
    lx, rx = w / 2 - Wd / 2 + r + 1, w / 2 + Wd / 2 - r - 1
    cy = h / 2
    cv = Canvas()
    # the tape: a ribbon off the top of the left reel, over the crate, down round the right reel,
    # and back underneath, its face catching the light
    def run(y0, y1, sag):
        return [(lx + (rx - lx) * i / 30, y0 + (y1 - y0) * i / 30 + sag * _m.sin(_PI * i / 30)) for i in range(31)]
    for pts in (run(cy - r * .98, cy - r * .98, -h * .04), run(cy + r * .98, cy + r * .98, h * .04)):
        R = _Rib(pts, [1.4] * len(pts), [1.4] * len(pts))
        cv.obj([R.outline()], .5)
    tape_reel(cv, lx, cy, r, .2)
    tape_reel(cv, rx, cy, r, 1.1)
    crate = record_band(0, 0, rx - lx - 2 * r - 10, h * .82, seed)
    return (cv.svg() + f'<svg x="{_nn(lx + r + 5)}" y="{_nn(h * .09)}" width="{_nn(rx - lx - 2 * r - 10)}" '
            f'height="{_nn(h * .82)}" overflow="visible">{crate}</svg>')


def plate(w, h, ctx):
    seed = _seed(ctx)
    uid = f"nm{int(w)}x{int(h)}"
    if h <= 110:
        return vignette(w, h, uid, None, "", None, tape_headpiece(w, h, seed))
    # taller: the LP rising like a sun over the village, in a roundel, the reels and crate beneath
    hp = min(70., h * .32)
    cx, cy, a, b = box_fit(w, h - hp, 1.0, pad=3)
    cy = 3 + b
    clean = shape_pts(cx, cy, a, b, "round", 160)
    body = vignette_art(0, 0, 0, 0, clean, seed, "full")
    foot = f'<svg x="0" y="{_nn(h - hp)}" width="{_nn(w)}" height="{_nn(hp)}" overflow="visible">{tape_headpiece(w, hp, seed)}</svg>'
    return vignette(w, h, uid, clean, body, clean, foot)
