"""garden-04 "Sow and plant", merged into Walk the land (edition plan: vignette, about 18%, an oval).

An oval vignette of the prairie edge: oatgrass and camas in the lit foreground, a brush pile of crossed
limbs at the wood's edge (it smokes only when the page says burning is OK), the fence line running
back, Douglas fir and Garry oak massed in burin tone behind, cumulus over them. The top of the oval is
ruled; its foot frays out, and grass grows up over it out of the ground beyond. Easter egg (the
plan's): a kestrel on a fence post."""
import sys
import math
import random
import re
import zlib
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


PI = math.pi
TAU = 2 * PI
_n = C._n
_d = C._d
_ell = C._ell_pts


def _seed(ctx):
    return zlib.crc32(((ctx or {}).get("date", "") + "garlic").encode()) & 0xfffff


# ----------------------------------------------------------------------------------------------
# the garlic bulb, engraved
# ----------------------------------------------------------------------------------------------

class Bulb:
    """Onion-pointed garlic bulb, centre (cx, cy), half-width a, half-height b.
    pt(phi, lam): phi 0 (neck) .. pi (base), lam -1..1 across (sin of the longitude)."""

    def __init__(self, cx, cy, a, b):
        self.cx, self.cy, self.a, self.b = cx, cy, a, b

    def hw(self, phi):
        s = math.sin(phi)
        if phi < PI / 2:
            return self.a * s ** 1.9
        return self.a * s ** .75

    def y(self, phi):
        c = math.cos(phi)
        return self.cy - self.b * c if c > 0 else self.cy - self.b * .78 * c

    def pt(self, phi, lam):
        # clove bulges: each of the 7 segments swells a little between its grooves
        th = math.asin(max(-1., min(1., lam)))
        f = 1 + .045 * abs(math.sin((th + PI / 2) * 7 / 2))
        return (self.cx + self.hw(phi) * lam * f, self.y(phi))

    def outline(self, n=80):
        R = [self.pt(PI * i / n, 1) for i in range(n + 1)]
        L = [self.pt(PI * i / n, -1) for i in range(n + 1)]
        return R + L[::-1][1:-1]

    def meridian(self, th, dth, p0=.03, p1=.985, minsp=1.5):
        """Line at longitude th, kept where it lies at least minsp from a neighbour dth away."""
        segs, cur = [], []
        lam = math.sin(th)
        k = abs(math.cos(th)) * dth
        for i in range(81):
            phi = PI * (p0 + (p1 - p0) * i / 80)
            if self.hw(phi) * k >= minsp:
                cur.append(self.pt(phi, lam))
            else:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
        if len(cur) > 1:
            segs.append(cur)
        return segs


# ----------------------------------------------------------------------------------------------
# small subjects
# ----------------------------------------------------------------------------------------------

def clove(cv, cx, cy, s, tilt=0., rng=None):
    """A planted clove, point up, base at (cx, cy), s tall, with a root tuft."""
    rng = rng or random.Random(0)
    ca, sa = math.cos(tilt), math.sin(tilt)

    def P(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    w = s * .36
    pts = []
    for i in range(25):
        t = i / 24
        pts.append(P(w * math.sin(PI * t) ** .8 * (1 - .35 * t) * (1 if True else 0), -s * t))
    right = pts
    left = [P(-w * .75 * math.sin(PI * t) ** .9 * (1 - .4 * t), -s * t) for t in [i / 24 for i in range(25)]]
    poly = right + left[::-1][1:-1]
    for i in range(5):
        t = (i + .5) / 5 - .5
        x0, y0 = P(t * w * .8, 0)
        cv.hair([(x0, y0), (x0 + t * 4 + rng.uniform(-1, 1), y0 + s * rng.uniform(.25, .4))])
    cv.obj([poly], 1.)
    # back seam and shading on the right flank
    cv.hair([P(w * .1, -s * .05), P(w * .15, -s * .5), P(0, -s * .98)])
    for f in (.95, .8, .65, .5):
        cv.hair([P(w * f * math.sin(PI * t) ** .8 * (1 - .35 * t), -s * t) for t in [.08 + .8 * i / 12 for i in range(13)]])
    cv.line([P(-w * .4, -s * .02), P(w * .5, -s * .02)])


def paw(x, y, s, ang):
    """A dog's paw print (filled black): pad and four toes."""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)
    o = [_d([P(*q) for q in _ell(0, .35 * s, .55 * s, .42 * s, 14)], True, 0)]
    for tx, ty in ((-.62, -.35), (-.22, -.72), (.22, -.72), (.62, -.35)):
        o.append(_d([P(*q) for q in _ell(tx * s, ty * s, .2 * s, .26 * s, 10)], True, 0))
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# the scene in the cartouche field
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
# layouts
# ----------------------------------------------------------------------------------------------

def kestrel(cv, x, y, s, f=1):
    """an American kestrel perched upright, feet at (x, y), s tall, facing f (+1 right)"""
    def P(u, v):
        return (x + f * u * s, y - v * s)
    tail = [P(-.08, .02), P(.04, .02), P(.02, -.3), P(-.06, -.3)]
    cv.obj([tail], .5)
    cv.hair([P(-.06, -.24), P(.02, -.24)])
    body = [P(-.12, .05), P(-.16, .3), P(-.12, .55), P(.0, .7), P(.12, .62), P(.15, .4), P(.1, .15), P(.0, .02)]
    cv.obj([body], 1.)
    wing = [P(-.14, .55), P(-.16, .3), P(-.1, .0), P(-.02, .1), P(-.04, .45)]
    cv.obj([wing], .5)
    cv.hair(_keep_disc(_C.hatch_poly(wing, 30, 1.5), x - f * .12 * s, y - .25 * s, s * .2))
    for k in range(4):   # spotted breast
        cv.hair([P(.05 + .02 * (k % 2), .45 - k * .08), P(.07 + .02 * (k % 2), .43 - k * .08)])
    head = _ell(x + f * .04 * s, y - .76 * s, .1 * s, .1 * s, 12)[:-1]
    cv.obj([head], 1.)
    cv.hair([P(.0, .72), P(.02, .64)])          # the moustache stripe
    cv.obj([[P(.13, .78), P(.19, .75), P(.13, .72)]], .5)
    cv.line([P(.07, .79), P(.08, .79)])


def prairie_scene(x, y, W, H, seed, smoke=False):
    """the prairie edge: oatgrass and camas in the lit foreground, a brush pile at the wood's edge
    (smoking only on a burn-OK day), the fence line, Douglas fir and Garry oak in dense hatching
    behind, a sky of cumulus, and a kestrel on a post"""
    rng = random.Random(seed)
    cv = C.Canvas()
    cv.obj([[(x - 2, y - 2), (x + W + 2, y - 2), (x + W + 2, y + H + 2), (x - 2, y + H + 2)]], 0)
    hz = y + H * .5
    # the sky: cumulus built in contour lines, the clear sky between them in fine broken strokes
    yy = y
    while yy < hz:
        xx = x - 2 + rng.uniform(0, 6)
        while xx < x + W:
            L = rng.uniform(6, 20) * (1.6 if H > 180 else 1.)
            cv.hair([(xx, yy), (xx + L, yy + rng.uniform(-.3, .3))])
            xx += L + rng.uniform(2, 5) * (1 + (yy - y) / H * 3)
        yy += 2.
    for j in range(3):
        ccx, ccy = x + W * (.15 + .35 * j + rng.uniform(-.05, .05)), y + H * rng.uniform(.12, .3)
        cw = W * rng.uniform(.16, .24)
        top = []
        for i in range(25):
            t = i / 24
            bump = max(math.sqrt(max(0., 1 - ((t - c) / sw) ** 2)) * hv for c, hv, sw in ((.3, 1., .25), (.6, .8, .22), (.8, .5, .15), (.15, .5, .14)))
            top.append((ccx - cw / 2 + cw * t, ccy - cw * .22 * bump))
        cl = top + [(ccx + cw / 2, ccy + 1), (ccx - cw / 2, ccy + 1)]
        cv.obj([cl], .5)
        for q in (.3, .55, .78):
            cv.hair([(px, ccy - (ccy - py) * (1 - q) + 1) for px, py in top[2:-2]])
    # the wood's edge: firs and oaks massed dark, a lit rim on the crowns
    trees = []
    xx = x - 6
    while xx < x + W + 6:
        if rng.random() < .65:
            th = H * rng.uniform(.16, .42)
            tw = th * .42
            trees.append(("fir", xx, th, tw))
            xx += tw * rng.uniform(.6, 1.3)
        else:
            th = H * rng.uniform(.18, .26)
            tw = th * 1.1
            trees.append(("oak", xx, th, tw))
            xx += tw * .6
    for kind, tx, th, tw in trees:
        base = hz + 2
        if kind == "fir":
            pts = [(tx, base - th)]
            n = 7
            for i in range(1, n + 1):
                t = i / n
                pts.append((tx + tw / 2 * t * 1.05, base - th + th * t - (th / n * .4 if i < n else 0)))
                if i < n:
                    pts.append((tx + tw / 2 * t * .55, base - th + th * t))
            pts = pts + [(tx - px + tx, py) for px, py in pts[::-1]][:-1]
        else:
            pts = []
            for i in range(19):
                a = math.pi + math.pi * i / 18
                r = 1 + .12 * math.sin(i * 2.1 + tx)
                pts.append((tx + tw / 2 * math.cos(a) * r, base - th * .55 + th * .45 * math.sin(a) * r))
            pts += [(tx + tw * .35, base), (tx - tw * .35, base)]
        cv.obj([pts], .5)
        tone_hatch(cv, pts, lit(tx, base - th * .5, tw * .55, th * .5, .3, .75), 80. if kind == "fir" else 30., 1.5, .7)
    # the ground plane: rough meadow receding in short flicks
    meadow = [(x - 2, hz), (x + W + 2, hz), (x + W + 2, y + H + 2), (x - 2, y + H + 2)]
    cv.obj([meadow], 0)
    cv.line([(x - 2, hz), (x + W + 2, hz)])
    yy = hz + 2
    while yy < y + H:
        k = (yy - hz) / (y + H - hz)
        xx = x + rng.uniform(0, 4)
        while xx < x + W:
            L = 1.5 + 3.5 * k
            cv.hair([(xx, yy), (xx + L * .2, yy - L)])
            xx += (3.5 - 1.5 * k + rng.uniform(0, 2)) * (1.4 if H > 180 else 1.)
        yy += (2 + 2 * k) * (1.3 if H > 180 else 1.)
    # the fence line and its posts, the kestrel on the nearest
    fy = hz + (y + H - hz) * .28
    posts = []
    for i in range(9):
        px = x + W * (.54 + i * .065)
        ph = H * (.1 + .012 * i)
        posts.append((px, ph))
    for i in range(len(posts) - 1):
        (a, ha), (b, hb) = posts[i], posts[i + 1]
        for q in (.35, .7):
            cv.hair([(a, fy - ha * q), (b, fy + (i + 1) * .9 - hb * q)])
    for i, (px, ph) in enumerate(posts):
        pb = fy + i * .9
        post = [(px - 1.3, pb), (px + 1.3, pb), (px + 1.3, pb - ph), (px - 1.3, pb - ph - .8)]
        cv.obj([post], .5)
        cv.hair([(px + .4, pb - ph + 1), (px + .4, pb - .5)])
    kp, kh = posts[1]
    kestrel(cv, kp, fy + .9 - kh - .5, H * .2, -1)
    # the brush pile at the wood's edge: a mound of crossed limbs, the gaps dark
    bx, bw, bh = x + W * .3, W * .26, H * .2
    mound = [(bx - bw / 2 + bw * i / 20, fy + 3 - bh * math.sin(math.pi * i / 20) ** .7 * (1 + .1 * math.sin(i * 1.7)))
             for i in range(21)]
    cv.obj([mound], 1.)
    cv.hair(C.hatch_poly(mound, 0, 1.5))
    cv.hair(_keep_disc(C.hatch_poly(mound, 90, 1.5), bx + bw * .2, fy, bw * .4))
    for i in range(18):
        a0 = rng.uniform(-.9, .9)
        cxl = bx + rng.uniform(-.4, .4) * bw
        cyl = fy + 2 - rng.uniform(.1, .7) * bh
        L = rng.uniform(.2, .45) * bw
        limb = [(cxl - math.cos(a0) * L / 2, cyl - math.sin(a0) * L / 2), (cxl + math.cos(a0) * L / 2, cyl + math.sin(a0) * L / 2)]
        R = _Rib(limb, [1.2, .6], [1.2, .6])
        cv.obj([R.outline()], .5)
        if rng.random() < .5:
            tx, ty = limb[1]
            cv.hair([(tx, ty), (tx + 3 * math.cos(a0 - .7), ty + 3 * math.sin(a0 - .7))])
    if smoke:
        # a burn-OK morning: smoke curls up off the pile and leans with the breeze
        for j in range(3):
            pts = []
            for i in range(30):
                t = i / 29
                pts.append((bx + bw * (-.05 + .1 * j) + t * W * .12 + math.sin(t * 7 + j) * 4 * t,
                            fy - bh * .8 - t * (fy - y) * .9))
            R = _Rib(pts, [1. + 5 * (i / 29) for i in range(30)], [1. + 5 * (i / 29) for i in range(30)])
            cv.obj([R.outline()], .5)
            cv.hair(R.contour(.3, .5, .9))
    # the lit foreground: oatgrass and camas, tall, swelling and tapering
    for i in range(int(W / 4)):
        gx = x + rng.uniform(-2, W + 2)
        gb = y + H + 2
        gh = H * rng.uniform(.12, .3)
        lean = rng.uniform(-.25, .25)
        stem = [(gx, gb), (gx + lean * gh * .5, gb - gh * .5), (gx + lean * gh, gb - gh)]
        R = _Rib(stem, [1., .6, .25], [1., .6, .25])
        cv.obj([R.outline()], .5)
        if rng.random() < .3:
            hx, hy = stem[-1]
            for k in range(4):   # a camas spike
                cv.obj([_ell(hx + (k % 2 - .5) * 2, hy + k * 2, 1.4, .9, 8)[:-1]], .5)
    return cv.svg()


def _tufts(w, h, cx, cy, a, b, seed):
    """oatgrass and camas growing up over the foot of the oval, out of the ground beyond it"""
    rng = random.Random(seed + 9)
    cv = C.Canvas()
    for sd in (-1, 1):
        bx = cx + sd * a * .78
        for i in range(16):
            gx = bx + rng.uniform(-a * .22, a * .22)
            gb = cy + b * rng.uniform(.82, 1.0)
            gh = b * rng.uniform(.35, .75)
            lean = sd * rng.uniform(0, .45) + rng.uniform(-.1, .1)
            stem = [(gx + lean * gh * (t ** 1.6), gb - gh * t) for t in [k / 8 for k in range(9)]]
            cv.obj([], 0)
            cv.line(stem[:5])
            cv.hair(stem[4:])
            if rng.random() < .35:
                hx, hy = stem[-1]
                for k in range(5):
                    cv.obj([_ell(hx + (k % 2 - .5) * 2.2, hy + k * 2.2, 1.6, 1., 8)[:-1]], .5)
            elif rng.random() < .5:
                hx, hy = stem[-1]
                for k in range(4):
                    cv.hair([(hx, hy + k * 2), (hx + sd * 2.5, hy + k * 2 - 1.5)])
    return cv.svg()


def plate(w, h, ctx):
    seed = _seed(ctx)
    uid = f"wl{int(w)}x{int(h)}"
    sample = (ctx or {}).get("sample", "")
    burn_ok = bool(re.search(r"\\bburn\\w*[^.|]{0,30}\\b(ok|open|allowed)\\b", sample, re.I))
    cx, cy, a, b = box_fit(w, h, 2.1 if h < 260 else 1.3, pad=3)
    clean = shape_pts(cx, cy, a, b, "oval", 180)
    sil = ragged(clean, max(2., b * .05), seed, cut=lambda x, y: y < cy + b * .4)
    body = prairie_scene(cx - a, cy - b, 2 * a, 2 * b, seed, burn_ok)
    top = [p for p in clean if p[1] < cy + b * .4]
    top.sort(key=lambda p: (_m.atan2(p[1] - cy, p[0] - cx) - _PI / 2) % _TAU)
    ex = f'<path d="{_dd(top, tol=.1)}" fill="none" stroke="#000" stroke-width="1.5"/>' + _tufts(w, h, cx, cy, a, b, seed)
    return vignette(w, h, uid, sil, body, None, ex)
