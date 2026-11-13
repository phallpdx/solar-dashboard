"""world-01 "Over in Bangkok": khao soi on a Lanna silver tray, in a Himmapan-forest gap frieze.

The vignette (edition plan: a 22% oval set in a gap frieze): a deep bowl of khao soi steams on a
khan tok pedestal tray with repoussé lotus petals, its little dishes of pickled greens, shallots,
chilli paste and lime round it, a china spoon on the rim and a heap of crisp noodles on the curry.
Bowl, tray and foot are modelled in contour cuts that swell with the shade (curve_tone); the oval
ground is level burin cuts, darkest behind the steam, which is left white.
The frieze either side: kan khot coils sheathed in kranok flames grow out from behind the oval, and
the gaps are packed with kranok sam tua sprigs, small coils and lotus buds (plate is transparent
outside the oval and the ornament, so the frame ground shows through).
Easter egg: a kinnari, swan below and woman above in a chada crown, kneels in the right-hand forest
beating a klong drum, her wings and tail cut as the same kranok flames so she hides among them."""
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


_n = C._n


# ----------------------------------------------------------------------------------- helpers
# ----------------------------------------------------------------------------------- clouds
# ----------------------------------------------------------------------------------- prang
# ----------------------------------------------------------------------------------- bank, palms
# ----------------------------------------------------------------------------------- boat
# ----------------------------------------------------------------------------------- the scene

def _chaikin(q, k=2):
    for _ in range(k):
        q = [pt for i in range(len(q)) for pt in
             (((3 * q[i][0] + q[(i + 1) % len(q)][0]) / 4, (3 * q[i][1] + q[(i + 1) % len(q)][1]) / 4),
              ((q[i][0] + 3 * q[(i + 1) % len(q)][0]) / 4, (q[i][1] + 3 * q[(i + 1) % len(q)][1]) / 4))]
    return q


def curve_tone(cv, pl, tf, lo=.14, step=1.):
    """burin tone laid along a curve: the cut swells from nothing through 0.5 and 1 px to 1.5 px
    as tf(x, y) deepens, so a family of contour curves models the form it wraps"""
    pts = []
    for i in range(1, len(pl)):
        (ax, ay), (bx, by) = pl[i - 1], pl[i]
        n = max(1, int(_m.hypot(bx - ax, by - ay) / step))
        pts += [(ax + (bx - ax) * j / n, ay + (by - ay) * j / n) for j in range(n)]
    pts.append(pl[-1])
    cur, cw = [], None
    for x, y in pts:
        t = tf(x, y)
        wv = 0 if t < lo else (.5 if t < lo + .28 else (1. if t < lo + .58 else 1.5))
        if wv != cw:
            if cw and len(cur) > 1:
                {.5: cv.hair, 1.: cv.line, 1.5: cv.heavy}[cw](cur)
            cur = [cur[-1]] if (cur and wv and cw) else []
            cw = wv
        cur.append((x, y))
    if cw and len(cur) > 1:
        {.5: cv.hair, 1.: cv.line, 1.5: cv.heavy}[cw](cur)


def _flame_line(x, y, ang, L, curl, n=12):
    pts, a = [], ang
    for i in range(n + 1):
        t = i / n
        pts.append((x, y))
        a += curl * (.02 + 2.2 * t ** 4) / n * 6
        x += _m.cos(a) * L / n
        y += _m.sin(a) * L / n
    return pts


def flame(cv, x, y, ang, L, curl=1., wd=None, shade=True):
    """one kranok flame: a blade that swells off its base, runs straight, then flicks over into a
    hooked tip; the Thai double line cut inside it and its hollow side darkened"""
    wd = wd or L * .17
    P = _flame_line(x, y, ang, L, curl)
    n = len(P) - 1
    ws = [max(.3, wd * (1 - t) ** 1.5 * (1 + 2.5 * t)) for t in [i / n for i in range(n + 1)]]
    sg = 1 if curl > 0 else -1
    wl = [v * (1. if sg > 0 else .62) for v in ws]
    wr = [v * (.62 if sg > 0 else 1.) for v in ws]
    R = _Rib(P, wl, wr)
    cv.obj([R.outline()], .5)
    if L > 5:
        cv.hair(R.contour(.5 * sg, .06, .82, .9))
    if shade and L > 8:
        for k in range(2):
            u0 = .1 + k * .1
            cv.hair(R.contour(-.3 * sg - k * .3 * sg, u0, u0 + .32 - k * .1, 1.))
    return P[-1]


def kranok3(cv, x, y, ang, L, sg):
    """kranok sam tua: three flames from one sheath, the big one between two little ones"""
    flame(cv, x, y, ang - sg * .55, L * .55, sg * 1.1, shade=False)
    flame(cv, x, y, ang + sg * .5, L * .5, sg * .9, shade=False)
    flame(cv, x, y, ang, L, sg * 1.2)
    kab = _chaikin([(x - _m.cos(ang) * L * .12 + _m.sin(ang) * L * .12, y - _m.sin(ang) * L * .12 - _m.cos(ang) * L * .12),
                    (x + _m.cos(ang) * L * .14, y + _m.sin(ang) * L * .14),
                    (x - _m.cos(ang) * L * .12 - _m.sin(ang) * L * .12, y - _m.sin(ang) * L * .12 + _m.cos(ang) * L * .12)], 1)
    cv.obj([kab + [(x - _m.cos(ang) * L * .2, y - _m.sin(ang) * L * .2)]], .5)


class _Occ:
    """a coarse occupancy grid of discs, for packing the frieze"""

    def __init__(self, c=4.):
        self.c, self.g = c, {}

    def add(self, x, y, r):
        c = self.c
        for i in range(int((x - r) // c), int((x + r) // c) + 1):
            for j in range(int((y - r) // c), int((y + r) // c) + 1):
                self.g.setdefault((i, j), []).append((x, y, r))

    def free(self, x, y, r):
        c = self.c
        for i in range(int((x - r) // c) - 1, int((x + r) // c) + 2):
            for j in range(int((y - r) // c) - 1, int((y + r) // c) + 2):
                for a, b, q in self.g.get((i, j), ()):
                    if (x - a) ** 2 + (y - b) ** 2 < (r + q) ** 2:
                        return False
        return True

    def path(self, P, r):
        for i in range(0, len(P), 2):
            self.add(P[i][0], P[i][1], r)


def kan_khot(cv, occ, x, y, R, th, sg, turns=1.4, tl=.13):
    """a curling stem (kan khot) sheathed in kranok flames: it reaches in from angle th, winds in
    `turns` times, and ends in a three-flame bud at its eye"""
    n = int(34 * turns)
    a0 = th + sg * tl * turns * _TAU
    sp = []
    for i in range(-int(n * tl), n + 1):
        t = i / n
        a = a0 + sg * t * turns * _TAU
        rr = R * (1 - .8 * t ** .8) if t >= 0 else R * (1 - 2.2 * t)
        sp.append((x + rr * _m.cos(a), y + rr * _m.sin(a)))
    m = len(sp)
    sw = max(1.1, R * .05)
    ws = [sw * (1.3 - .7 * i / m) for i in range(m)]
    # the sheath: flames off the outer side of the coil, swept back against its growth
    L0 = R * .7
    for i in range(3, int(m * .8), 3):
        (ax, ay), (bx, by) = sp[i - 1], sp[i]
        tx, ty = bx - ax, by - ay
        tn = _m.hypot(tx, ty) or 1
        tx, ty = tx / tn, ty / tn
        ox, oy = bx - x, by - y
        on = _m.hypot(ox, oy) or 1
        ox, oy = ox / on, oy / on
        dx, dy = ox * .75 - tx * .66, oy * .75 - ty * .66
        cr = 1.15 if (ox * -ty - oy * -tx) > 0 else -1.15
        t = i / m
        L = L0 * (1 - .7 * t) * (.8 + .4 * (_hash(i, int(x)) % 97) / 97)
        bx_, by_ = bx + ox * sw * .5, by + oy * sw * .5
        ang = _m.atan2(dy, dx)
        flame(cv, bx_, by_, ang, L, cr)
        occ.path(_flame_line(bx_, by_, ang, L, cr, 6), L * .18 + 1.5)
    R_ = _Rib(sp, ws, ws)
    cv.obj([R_.outline()], .5)
    cv.hair(R_.contour(.0, .02, .92, 1.))
    occ.path(sp, sw + 2)
    ex, ey = sp[-1]
    ta = _m.atan2(sp[-1][1] - sp[-2][1], sp[-1][0] - sp[-2][0])
    kranok3(cv, ex, ey, ta + sg * 1.2, R * .45, sg)
    occ.add(x, y, R * .35)


def lai_panel(cv, x0, x1, y0, y1, sd, seed, hide, oval):
    """one wing of the gap frieze: two great kan khot coils reaching out from behind the oval, the
    gaps packed with kranok sprigs and lotus buds; `hide` is the kinnari's clearing"""
    occ = _Occ(4.)
    W, H = x1 - x0, y1 - y0
    ocx, ocy, oa, ob = oval
    inside = lambda x, y, r: ((x - ocx) / (oa + r)) ** 2 + ((y - ocy) / (ob + r)) ** 2 < 1
    if hide:
        occ.add(*hide)
    inner = x1 if sd < 0 else x0
    R = min(W * .26, H * .25)
    if hide:
        coils = [(inner + sd * W * .26, y0 + H * .27, R * .85, 1), (inner + sd * W * .3, y0 + H * .8, R * .6, -1)]
    else:
        coils = [(inner + sd * W * .34, y0 + H * .29, R, 1), (inner + sd * W * .7, y0 + H * .73, R * .92, -1)]
    for k, (cx, cy, r, s) in enumerate(coils):
        sg = -s * sd
        th = (0 if sd < 0 else _PI) + s * sd * .5 * (1 if sd < 0 else -1)
        th = _m.atan2((ocy - cy) * .35, (inner + sd * -6) - cx)
        kan_khot(cv, occ, cx, cy, r, th, sg)
    rng = random.Random(seed)
    for tries in range(700):        # gaps: the biggest kranok sprig that fits
        f = 1 - tries / 760
        L = rng.uniform(.5, 1.) * f * .3 * H + 4
        x = rng.uniform(x0 + 1, x1 - 1)
        y = rng.uniform(y0 + 1, y1 - 1)
        r = L * .42
        if inside(x, y, -r) or not occ.free(x, y, r):
            continue
        ang = _m.atan2(y - (y0 + H / 2), (x - inner)) + rng.uniform(-.7, .7)
        bx, by = x - _m.cos(ang) * L * .45, y - _m.sin(ang) * L * .45
        if L > 16 and rng.random() < .45:
            kan_khot(cv, occ, x, y, L * .4, ang + _PI, rng.choice((-1, 1)), 1.1, .1)
        elif L > 9:
            kranok3(cv, bx, by, ang, L, rng.choice((-1, 1)))
        else:
            flame(cv, bx, by, ang, L, rng.choice((-1.2, 1.2)))
        occ.add(x, y, r)
    for tries in range(220):
        r = rng.uniform(1.8, 3.2)
        x, y = rng.uniform(x0 + 3, x1 - 3), rng.uniform(y0 + 3, y1 - 3)
        if inside(x, y, 0) or not occ.free(x, y, r + .8):
            continue
        bud = _chaikin([(x, y - r * 1.5), (x + r, y), (x, y + r * .9), (x - r, y)], 2)
        cv.obj([bud], .5)
        cv.hair([(x, y + r * .8), (x, y - r * .6)])
        occ.add(x, y, r + .5)


def kinnari(cv, x, y, s, sd=-1):
    """a kinnari, woman above and swan below, in a tiered chada crown, kneeling at a klong drum;
    her wings and tail are kranok flames like the forest's, so she hides in it. Faces sd (-1 left)"""
    X = lambda u: x + sd * -u * s     # u > 0 runs away from the way she faces
    Y = lambda v: y - v * s
    # tail plumes and the raised wings first, so the body lies over their roots
    for i in range(4):
        flame(cv, X(.3), Y(.22), (_PI if sd > 0 else 0) + sd * (.15 - i * .32) * -1 - (0 if sd > 0 else 0), s * (.42 - i * .04), -sd * 1.1, s * .07)
    for i in range(5):
        a = -_PI / 2 + sd * -(.25 + i * .22)
        flame(cv, X(.1), Y(.58), a, s * (.5 - i * .05), sd * 1.2, s * .075)
    # the swan body, lit from the upper left
    body = _chaikin([(X(-.12), Y(.3)), (X(.05), Y(.42)), (X(.28), Y(.36)), (X(.38), Y(.24)), (X(.22), Y(.1)), (X(-.04), Y(.12))], 3)
    cv.obj([body], 1.)
    tone_hatch(cv, body, lit(X(.12), Y(.26), s * .25, s * .15, .14, .75), 15., 1.5, .75)
    for k in range(5):      # feather scales
        u, v = .02 + k * .06, .22 + .02 * (k % 2)
        cv.hair(_garc(X(u), Y(v), s * .03, s * .025, 0, _PI, 5))
    # bird legs folded under, the feet on the ground line
    for u in (.06, .18):
        cv.line([(X(u), Y(.12)), (X(u - .05), Y(.05)), (X(u + .02), Y(.0)), (X(u - .06), Y(.0))])
    # the torso, slender and leaning to the drum: shoulders, a narrow waist, a sash, a collar
    tor = _chaikin([(X(-.08), Y(.36)), (X(.1), Y(.37)), (X(.05), Y(.47)), (X(.06), Y(.55)), (X(.08), Y(.62)),
                    (X(-.07), Y(.64)), (X(-.05), Y(.55)), (X(-.03), Y(.47))], 3)
    cv.obj([tor], 1.)
    tone_hatch(cv, tor, lit(X(-.01), Y(.52), s * .07, s * .14, -.05, .75), 75., 1.5, None)
    cv.obj([_chaikin([(X(-.09), Y(.43)), (X(.07), Y(.44)), (X(.08), Y(.4)), (X(-.09), Y(.39))], 1)], .5)
    cv.obj([_garc(X(.0), Y(.62), s * .075, s * .045, 0, _PI, 8)], .5)
    cv.hair(_garc(X(.0), Y(.62), s * .05, s * .025, 0, _PI, 6))
    # the head in profile, the crown rising in tiers to its spire, flame ear-pieces
    hx, hy = X(.0), Y(.7)
    head = _chaikin([(hx + sd * s * .045, hy + s * .02), (hx + sd * s * .05, hy - s * .03), (hx, hy - s * .065),
                     (hx - sd * s * .05, hy - s * .02), (hx - sd * s * .02, hy + s * .065), (hx + sd * s * .02, hy + s * .06)], 2)
    cv.obj([head], 1.)
    cv.hair([(hx + sd * s * .03, hy - s * .01), (hx + sd * s * .045, hy - s * .012)])
    for k in range(5):
        wk = s * (.055 - k * .009)
        yk = hy - s * (.05 + k * .05)
        cv.obj([[(hx - wk, yk), (hx + wk, yk), (hx + wk * .82, yk - s * .05), (hx - wk * .82, yk - s * .05)]], .5)
        cv.hair([(hx - wk * .7, yk - s * .025), (hx + wk * .7, yk - s * .025)])
    cv.obj([[(hx - s * .012, hy - s * .3), (hx + s * .012, hy - s * .3), (hx, hy - s * .42)]], .5)
    flame(cv, hx - sd * s * .03, hy - s * .02, _PI / 2 + sd * -.4, s * .12, sd * -1.3, s * .025, False)
    # the klong drum before her, a barrel on its side, laced heads; her arms out, sticks raised
    dx, dy = X(-.26), Y(.24)
    dr = s * .11
    drum = _chaikin([(dx - s * .1, dy - dr), (dx + s * .1, dy - dr), (dx + s * .12, dy), (dx + s * .1, dy + dr),
                     (dx - s * .1, dy + dr), (dx - s * .12, dy)], 2)
    cv.obj([drum], 1.)
    for k in range(9):
        t = -.9 + 1.8 * k / 8
        curve_tone(cv, [(dx - s * .1 * _m.sqrt(1 - .5 * t * t), dy + dr * t), (dx + s * .1 * _m.sqrt(1 - .5 * t * t), dy + dr * t)],
                   lambda px, py: .2 + .6 * max(0., (py - dy) / dr) + .1 * (px - dx) / (s * .1))
    for e in (-1, 1):       # the two heads, and the lacing zig-zagging between them
        cv.obj([_ell(dx + e * s * .105, dy, s * .03, dr * .95, 14)[:-1]], 1.)
    zz = [(dx + s * .085 * (1 if k % 2 else -1), dy - dr * .85 + dr * 1.7 * k / 7) for k in range(8)]
    cv.hair(zz)
    for y_, x_ in ((.62, .06), (.6, -.05)):
        arm = [(X(x_), Y(y_ - .02)), (X(x_ - .1), Y(.46)), (X(-.2), Y(.42 + (.04 if x_ > 0 else 0)))]
        Ra = _Rib(arm, [s * .022, s * .019, s * .014], [s * .022, s * .019, s * .014])
        cv.obj([Ra.outline()], .5)
    cv.line([(X(-.2), Y(.46)), (X(-.27), Y(.4))])
    cv.line([(X(-.2), Y(.42)), (X(-.3), Y(.5))])


def khao_soi(cv, cx, cy, a, b):
    """the field: a bowl of khao soi steaming on a Lanna silver pedestal tray (khan tok), with its
    little dishes, modelled in contour cuts out of a dark ground"""
    ty = cy + b * .32
    ta, tb = a * .78, b * .26
    L = lambda px, py, c0, w0: max(0., min(1., (px - c0) / w0 * .5 + .5))
    # the pedestal: a waisted foot under the tray, its flutes catching the light
    fy0, fy1 = ty + tb * .7, cy + b * .86
    for k in range(16):
        v = k / 15
        y_ = fy0 + (fy1 - fy0) * v
        hw = ta * (.36 + .2 * (1 - v) ** 3 + .14 * v ** 2)
        curve_tone(cv, [(cx - hw * _m.cos(t), y_ + tb * .22 * hw / ta * _m.sin(t)) for t in [_PI * j / 30 for j in range(31)]],
                   lambda px, py, hw=hw: .2 + .7 * L(px, py, cx - hw * .2, hw * 2) ** 1.4)
    foot = [(cx - ta * .5, fy0 - 2)] + [(cx - ta * .5 * _m.cos(t), fy1 + tb * .3 * _m.sin(t)) for t in [_PI * j / 20 for j in range(21)]] + [(cx + ta * .5, fy0 - 2)]
    cv.obj([], 0)
    cv.line(foot[1:-1])
    # the tray: a plain well inside a rim of repoussé lotus petals
    tray = _ell(cx, ty, ta, tb, 72)[:-1]
    cv.obj([tray + []], 1.)
    rim = [(cx + ta * 1.0 * _m.cos(t), ty + tb * 1.0 * _m.sin(t) + tb * .28) for t in [_PI * j / 36 for j in range(37)]]
    cv.line(rim)
    for i in range(36):
        t = _TAU * i / 36 + .08
        if _m.sin(t) < -.2:
            continue
        p = [(cx + ta * (.78 + .22 * _m.sin(_PI * j / 6)) * _m.cos(t + (j / 6 - .5) * .17),
              ty + tb * (.78 + .22 * _m.sin(_PI * j / 6)) * _m.sin(t + (j / 6 - .5) * .17)) for j in range(7)]
        cv.hair(p)
        curve_tone(cv, [(cx + ta * .8 * _m.cos(t + .05), ty + tb * .8 * _m.sin(t + .05)), (cx + ta * .97 * _m.cos(t + .05), ty + tb * .97 * _m.sin(t + .05))],
                   lambda px, py: .3 + .5 * L(px, py, cx, ta))
    for k in range(5):      # the rim's front, its thickness cut in tone
        q = k / 4
        curve_tone(cv, [(cx + ta * _m.cos(t), ty + tb * _m.sin(t) + tb * .28 * q) for t in [_PI * j / 36 for j in range(37)]],
                   lambda px, py: .15 + .75 * L(px, py, cx - ta * .3, ta * 1.6) ** 1.3)
    cv.hair(_ell(cx, ty, ta * .77, tb * .77, 56))
    for k in range(9):      # the well: the light falls across it, shadowed under the far rim
        v = -.7 + 1.4 * k / 8
        hw = ta * .74 * _m.sqrt(1 - v * v)
        curve_tone(cv, [(cx - hw, ty + tb * .74 * v), (cx + hw, ty + tb * .74 * v)],
                   lambda px, py: .55 - .6 * (py - ty) / tb + .2 * (px - cx) / ta)
    # the little dishes: pickled greens, shallots, a wedge of lime, chilli paste
    for dx_, dy_, kind in ((-.62, .05, "g"), (-.36, .45, "s"), (.62, .1, "c"), (.4, .45, "l")):
        px, py = cx + ta * dx_, ty + tb * dy_
        r = a * .085
        cv.obj([_ell(px, py + r * .25, r, r * .45, 20)[:-1]], 1.)
        for k in range(4):
            v = k / 3
            curve_tone(cv, [(px - r * _m.cos(t) * (1 - .2 * v), py + r * .25 + r * .45 * _m.sin(t) * (1 - .2 * v) + r * .3 * v) for t in [_PI * j / 12 for j in range(13)]],
                       lambda qx, qy: .25 + .6 * L(qx, qy, px, r * 2))
        cv.obj([_ell(px, py, r, r * .38, 20)[:-1]], 1.)
        if kind == "l":
            w_ = [(px - r * .7, py), (px + r * .6, py - r * .1), (px - r * .1, py - r * .65)]
            cv.obj([w_], 1.)
            for k in range(3):
                cv.hair([(px - r * .1, py - r * .55), (px - r * .55 + k * r * .5, py - r * .05)])
        else:
            rng = random.Random(len(kind) * 7 + int(px))
            for k in range(7 if kind != "c" else 0):
                ex, ey = px + rng.uniform(-.6, .6) * r, py + rng.uniform(-.35, .05) * r
                cv.obj([_ell(ex, ey, r * .22, r * .14, 8)[:-1]], .5)
                if kind == "g":
                    cv.hair([(ex - r * .15, ey), (ex + r * .15, ey - .3)])
            if kind == "c":
                cv.obj([_ell(px, py + .3, r * .78, r * .26, 18)[:-1]], 0)
                tone_hatch(cv, _ell(px, py + .3, r * .78, r * .26, 18)[:-1], lambda qx, qy: .7, 0., 1.5, None)
    # the bowl: a deep bowl, its pattern band, modelled in cuts that wrap it
    ba, bh = a * .3, b * .5
    bty = ty - tb * .1 - bh       # its rim
    rb = bh * .19
    def bw(v):
        return ba * (1 - .55 * v ** 2.2)
    out = [(cx + bw(v), bty + bh * v) for v in [k / 20 for k in range(21)]] + \
          [(cx - bw(v), bty + bh * v) for v in [k / 20 for k in range(20, -1, -1)]]
    cv.obj([out + [(cx - ba, bty - 1)]], 1.)
    for k in range(1, 15):
        v = k / 15
        hw = bw(v)
        curve_tone(cv, [(cx - hw * _m.cos(t), bty + bh * v + rb * hw / ba * _m.sin(t)) for t in [_PI * j / 24 for j in range(25)]],
                   lambda px, py, v=v, hw=hw: .05 + .9 * L(px, py, cx - hw * .15, hw * 2) ** 1.6 + .25 * v)
    for q in (.16, .3):
        cv.line([(cx - bw(q) * _m.cos(t), bty + bh * q + rb * bw(q) / ba * _m.sin(t)) for t in [_PI * j / 24 for j in range(25)]])
    for j in range(9):      # the band: little flames between its lines
        t = _PI * (j + .5) / 9
        px = cx - bw(.23) * _m.cos(t)
        py = bty + bh * .23 + rb * _m.sin(t)
        if .25 < t < _PI - .25:
            cv.hair([(px - 1.2, py + 1.5), (px, py - 1.6), (px + .6, py + .2)])
    cv.obj([_ell(cx, bty, ba, rb, 40)[:-1]], 1.)
    soup = _ell(cx, bty + rb * .12, ba * .9, rb * .78, 36)[:-1]
    cv.obj([soup], .5)
    for k in range(5):
        v = -.6 + 1.2 * k / 4
        hw = ba * .88 * _m.sqrt(1 - v * v)
        curve_tone(cv, [(cx - hw, bty + rb * .12 + rb * .74 * v), (cx + hw, bty + rb * .12 + rb * .74 * v)],
                   lambda px, py: .55 + .25 * (px - cx) / ba)
    for k, (ox, oy) in enumerate(((-.5, .2), (.55, -.1), (.3, .35), (-.2, -.3))):     # beads of chilli oil
        cv.obj([_ell(cx + ba * ox, bty + rb * oy, 1.4, .8, 8)[:-1]], .5)
    # the crisp noodle nest, a tangle heaped on the curry, and a sprig of coriander
    rng = random.Random(11)
    nx, ny, nr = cx - ba * .08, bty - rb * .4, ba * .45
    nest = _chaikin([(nx - nr, ny + rb * .2), (nx - nr * .6, ny - rb * 1.3), (nx, ny - rb * 1.9), (nx + nr * .6, ny - rb * 1.4), (nx + nr, ny + rb * .2)], 2)
    cv.obj([nest], .5)
    for i in range(5):       # loops of fried noodle trailing across the heap, darker underneath
        v = .15 + i * .2
        yb = ny - rb * 1.6 * (1 - v)
        hw = nr * (.35 + .6 * v)
        P = [(nx - hw + 2 * hw * t + 1.3 * _m.cos(t * 26 + i), yb + 1.1 * _m.sin(t * 26 + i) + rb * .3 * _m.sin(_PI * t) * -0.3)
             for t in [j / 60 for j in range(61)]]
        curve_tone(cv, P, lambda px, py, v=v: .2 + .45 * v + .25 * (px - nx) / nr)
    for k in range(3):
        flame(cv, nx + nr * .55, ny - rb * 1.2, -_PI / 2 + .5 + k * .45, ba * .22, 1.2, None, False)
    # a china spoon resting on the rim
    sx, sy = cx + ba * .6, bty - rb * .3
    sp = _chaikin([(sx - ba * .25, sy + rb * .5), (sx + ba * .15, sy - rb * .4), (sx + ba * .65, sy - rb * 2.4), (sx + ba * .72, sy - rb * 2.2),
                   (sx + ba * .25, sy - rb * .2), (sx - ba * .05, sy + rb * 1.0)], 2)
    cv.obj([sp], 1.)
    cv.hair([(sx - ba * .1, sy + rb * .4), (sx + ba * .4, sy - rb * 1.0)])
    # steam: wisps cut white out of the ground above the bowl
    for k, (ox, ph) in enumerate(((-.35, 0.), (.0, 1.7), (.3, 3.1))):
        x0_, y0_ = cx + ba * ox, bty - rb * 2.2
        Ls = b * (.45 + .1 * k)
        P = [(x0_ + ba * .12 * _m.sin(ph + t * 5.) * (1 + t), y0_ - Ls * t) for t in [j / 20 for j in range(21)]]
        ws = [.4 + 2.2 * _m.sin(_PI * j / 20) * (1 - j / 26) for j in range(21)]
        cv.obj([_Rib(P, ws, ws).outline()], 0)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 1
    uid = f"bk{int(w)}x{int(h)}"
    cx, cy, a, b = box_fit(w, h, 1.6, w * .48, 3)
    clean = shape_pts(cx, cy, a, b, "oval", 160)
    # the field: the bowl lit out of a ground of close level cuts, darkest behind the steam
    cv = Canvas()
    cv.obj([clean], 0)
    bty = cy - b * .2
    tone_hatch(cv, clean, lambda x, y: .74 - .45 * max(0., (y - bty) / b) - .06 * (x - cx) / a, 0., 1.5, .8, 90.)
    khao_soi(cv, cx, cy, a, b)
    body = cv.svg()
    # the Himmapan gap frieze either side, the kinnari drumming hidden in its right wing
    extra = ""
    gw = cx - a - 6
    if gw > 40:
        fr = Canvas()
        ks = min(h * .62, gw * 1.1)
        kx, ky = cx + a + 6 + gw * .62, h * .5 + ks * .42
        ov = (cx, cy, a + 3, b + 3)
        lai_panel(fr, 2, cx - a + 8, 3, h - 3, -1, seed, None, ov)
        lai_panel(fr, cx + a - 8, w - 2, 3, h - 3, 1, seed + 1, (kx - ks * .05, ky - ks * .5, ks * .34), ov)
        kinnari(fr, kx, ky, ks, -1)
        extra = fr.svg()
    # the frieze lies behind the oval: its stems run in under the rule
    s = vignette(w, h, uid, clean, body, clean)
    i = s.index(">", s.index("<svg")) + 1
    return s[:i] + extra + s[i:]
