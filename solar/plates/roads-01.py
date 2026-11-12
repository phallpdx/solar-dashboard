"""roads-01 "Drive times": the road out of Sauvie Island over the St. Johns Bridge.

The vignette is the drive itself: the St. Johns Bridge (gothic towers, suspension cables, cars on
the deck) over the Willamette, Mt. Hood standing between its towers, Forest Park dark on the west
bank, and in front a road climbing the near bank past a four-armed fingerpost (school, Lake Oswego,
St. Johns, the beach). The big volutes either side wind into spoked wheels. Easter egg: a Sauvie
Island heron standing in the shallows under the bridge."""
import sys
import math
import random
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
PI = math.pi


# ------------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------------

class Ink:
    """Layered output: each layer() call starts a stack of white fill / pattern fill / strokes."""

    def __init__(self):
        self.o = []

    def fill(self, d, fill="#fff", stroke=None, sw=1., rule=None):
        if not d:
            return
        s = f' stroke="#000" stroke-width="{_n(sw)}"' if stroke else ' stroke="none"'
        r = ' fill-rule="evenodd"' if rule else ""
        self.o.append(f'<path d="{d}" fill="{fill}"{s}{r}/>')

    def lines(self, d, sw=.5, crisp=False):
        if not d:
            return
        c = ' shape-rendering="crispEdges"' if crisp else ""
        self.o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(sw)}"{c}/>')

    def svg(self):
        return "".join(self.o)


def P(pts, close=False, tol=.15):
    return _d(pts, close, tol)


def PL(pls, tol=.15):
    return "".join(_d(p, False, tol) for p in pls if len(p) > 1)


def hatch(poly, ang, pitch, phase=0., inset=0.):
    return "".join(_d(p, tol=0) for p in C.hatch_poly(poly, ang, pitch, phase, inset))


def lerp(a, b, t):
    return a + (b - a) * t


def wavy_lines(poly, pitch, rng, amp=.0, gap=(4, 10), seg=(10, 30), ang=0.):
    """Horizontal water lines clipped to poly, broken into dashes with short gaps."""
    out = []
    for (p, q) in C.hatch_poly(poly, ang, pitch):
        x0, y0 = p
        x1, y1 = q
        L = math.hypot(x1 - x0, y1 - y0)
        t = rng.uniform(0, 4)
        while t < L:
            l = rng.uniform(*seg)
            a, b = t / L, min(L, t + l) / L
            out.append([(lerp(x0, x1, a), lerp(y0, y1, a)), (lerp(x0, x1, b), lerp(y0, y1, b))])
            t += l + rng.uniform(*gap)
    return out


def _scallops(poly, pitch, r):
    """Rows of little arches (tree canopy, as engravers cut woodland) clipped to poly."""
    out = []
    for (p, q) in C.hatch_poly(poly, 0, pitch, .5):
        x0, x1 = min(p[0], q[0]), max(p[0], q[0])
        y = p[1]
        n = int((x1 - x0) / (2 * r))
        if n < 1:
            continue
        pts = []
        off = (y * 1.7) % (2 * r)
        for j in range(n * 4 + 1):
            t = j / 4
            x = x0 + t * 2 * r
            if x > x1:
                break
            pts.append((x, y - r * .9 * abs(math.sin(PI * t))))
        out.append(pts)
    return out


# ------------------------------------------------------------------------------------------------
# the scene: St. Johns Bridge, Mt. Hood, the road and the fingerpost
# ------------------------------------------------------------------------------------------------

def scene(X0, Y0, W, H, seed=0, detail=2):
    """The vignette filling the rect X0,Y0,W,H (the caller clips it to its field).
    detail 0: tiny medallion (sky, Hood, bridge, water); 1: + bank and road; 2: everything."""
    rng = random.Random(seed)
    k = Ink()
    X1, Y1 = X0 + W, Y0 + H
    Yh = Y0 + H * (.64 if detail else .70)    # waterline
    Yd = Y0 + H * (.52 if detail else .56)    # bridge deck
    Yt = Y0 + H * (.10 if detail else .12)    # tower tops (under the spires)
    xt = (X0 + W * .29, X0 + W * .71)

    # sky: ruled, closer near the top (an engraved dawn), lighter toward the horizon
    sky = []
    y = Y0 + .75
    while y < Yh:
        sky.append(f"M{_n(X0)},{_n(y)}h{_n(W)}")
        y += 2. if y < Y0 + H * .2 else 3.
    k.lines("".join(sky), .5, True)

    # morning sun low behind Hood's right shoulder: rays as gaps -> ray lines
    sx, sy, sr = X0 + W * .62, Y0 + H * .33, H * .07
    rays = []
    for i in range(28):
        a = PI + PI * (i + .5) / 28
        r1 = sr * (2.6 if i % 2 else 3.6)
        rays.append([(sx + sr * 1.25 * math.cos(a), sy + sr * 1.25 * math.sin(a)),
                     (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    k.fill(P(_ell(sx, sy, sr * 1.15, sr * 1.15, 32), True))
    k.lines(PL(rays), .5)
    k.fill(P(_ell(sx, sy, sr, sr, 32), True), "#fff", True, .5)
    k.lines(hatch(_ell(sx, sy, sr, sr, 32), 0, 3, .4, .3), .5)

    # gulls wheeling over the river
    if detail:
        gulls = []
        for gx, gy, gs in ((.12, .17, 1.), (.17, .22, .8), (.84, .2, .9), (.4, .14, .7)):
            x0, y0, sz = X0 + W * gx, Y0 + H * gy, max(2.2, H * .022) * gs
            gulls.append([(x0 - sz, y0 - sz * .2), (x0 - sz * .45, y0 - sz * .55), (x0, y0),
                          (x0 + sz * .45, y0 - sz * .55), (x0 + sz, y0 - sz * .2)])
        k.fill("".join(P([(px, py - .9) for px, py in g] + [(px, py + .3) for px, py in g[::-1]], True, 0) for g in gulls), "#fff")
        k.lines(PL(gulls), 1.)

    # Mt. Hood, standing between the towers
    mx, mw = X0 + W * .5, W * (.62 if detail else .74)
    mh = min(H * (.47 if detail else .46), W * .3)
    base = Yh + 1
    prof = [(0, 0), (.08, .05), (.16, .14), (.25, .27), (.33, .42), (.39, .57), (.43, .70), (.465, .83),
            (.49, .96), (.505, 1.0), (.52, .965), (.54, .93), (.555, .90), (.58, .82), (.62, .70),
            (.67, .56), (.74, .40), (.82, .25), (.91, .12), (1, .03)]
    mt = [(mx - mw / 2 + u * mw, base - v * mh) for u, v in prof]
    k.fill(P(mt + [(mx + mw / 2, base + 2), (mx - mw / 2, base + 2)], True), "#fff", True, 1.)
    peak = mt[9]
    # fall lines: fanning down from the summit ridge; close and doubled on the shadow (east) face,
    # broken into dashes on the lit snow so it sparkles
    rprof, lprof = mt[9:], mt[:10][::-1]

    def along(pl, t):
        S = [0.]
        for q0, q1 in zip(pl, pl[1:]):
            S.append(S[-1] + math.hypot(q1[0] - q0[0], q1[1] - q0[1]))
        s_ = t * S[-1]
        for i in range(1, len(S)):
            if S[i] >= s_:
                f = (s_ - S[i - 1]) / max(1e-6, S[i] - S[i - 1])
                return (lerp(pl[i - 1][0], pl[i][0], f), lerp(pl[i - 1][1], pl[i][1], f))
        return pl[-1]
    shadow, lit = [], []
    nsh = 30 if detail else 16
    for i in range(nsh):
        t = (i + .5) / nsh
        top = along(rprof, t * .97)
        foot = (lerp(mx + mw * .05, mx + mw * .5, t), base)
        mid = (lerp(top[0], foot[0], .5) - mw * .015 * (1 - t), lerp(top[1], foot[1], .5))
        shadow.append([top, mid, foot])
    nl = 16 if detail else 8
    for i in range(nl):
        t = (i + .6) / nl
        top = along(lprof, t * .95)
        top = (top[0] + 1.2, top[1] + 1.5)
        foot = (lerp(mx + mw * .0, mx - mw * .5, t), base)
        segs, u = [], rng.uniform(0, .08)
        while u < 1:
            v = min(1, u + rng.uniform(.1, .22))
            segs.append([(lerp(top[0], foot[0], u), lerp(top[1], foot[1], u)),
                         (lerp(top[0], foot[0], v), lerp(top[1], foot[1], v))])
            u = v + rng.uniform(.04, .09)
        lit.extend(segs)
    k.lines(PL(shadow), .5)
    # cross-shading low on the shadow face for depth
    low = [(mx + mw * .08, base - mh * .45), (mx + mw * .5, base), (mx + mw * .1, base)]
    k.lines(hatch(low, -20, 2, .4), .5)
    k.lines(PL(lit), .5)
    # a whisper of horizontal ruling over the lower snow so no field is left bare
    snow = [(mx - mw * .5, base), peak, (mx + mw * .06, base)]
    k.lines(hatch(snow, 0, 3, 1.1), .5)
    # a jagged snowline, dark timber below
    sn = []
    for i in range(41):
        u = i / 40
        v = .34 + .06 * math.sin(u * 23 + seed) + .05 * ((i * 7) % 3 - 1)
        sn.append((mx - mw * .40 + u * mw * .80, base - v * mh * (1 - abs(u - .5) * 1.25)))
    forest = sn + [(mx + mw / 2, base + 1), (mx - mw / 2, base + 1)]
    k.fill(P(forest, True), C.pat("M"), False)
    k.lines(P(sn), .5)
    k.lines(PL(_scallops(forest, 3, 1.4)), .5)

    # Forest Park: the dark wooded ridge on the west bank, canopy cut in scallops
    fp = [(X0 - 2, Y0 + H * .30)]
    for i in range(1, 31):
        u = i / 30
        yy = lerp(Y0 + H * .30, Yh - 1, u ** 1.5) - 1.8 * abs(math.sin(i * 1.7 + seed))
        fp.append((X0 + W * .40 * u, yy))
    fp += [(X0 + W * .40, Yh + 1), (X0 - 2, Yh + 1)]
    k.fill(P(fp, True), C.pat("M"), False)
    k.lines(P(fp[:31]), 1.)
    k.lines(PL(_scallops(fp, 3, 1.5)), .5)
    # east bank: low and lightly ruled, the St. Johns roofs
    eb = [(X0 + W * .66, Yh + 1), (X0 + W * .76, Yh - H * .04), (X0 + W * .9, Yh - H * .07), (X1 + 2, Yh - H * .1),
          (X1 + 2, Yh + 1)]
    k.fill(P(eb, True), C.pat("D"), True, .5)
    roofs = []
    for i in range(7):
        bx = X0 + W * (.78 + .035 * i)
        by = lerp(Yh - H * .045, Yh - H * .095, i / 6)
        roofs.append([(bx, by + 3), (bx, by), (bx + 2, by - 2), (bx + 4, by), (bx + 4, by + 3)])
    if detail:
        k.fill("".join(P(r, True) for r in roofs), "#fff", True, .5)

    # the river
    riv = [(X0 - 2, Yh), (X1 + 2, Yh), (X1 + 2, Y1 + 2), (X0 - 2, Y1 + 2)]
    k.fill(P(riv, True))
    k.lines(PL(wavy_lines(riv, 2, rng, gap=(2, 5), seg=(8, 26))), .5)
    k.lines(f"M{_n(X0)},{_n(Yh)}h{_n(W)}", 1.)
    # tower reflections
    refl = []
    for x in xt:
        yy = Yh + 2
        while yy < Yh + H * .2:
            wdt = W * .025 * (1 - (yy - Yh) / (H * .25))
            refl.append([(x - wdt, yy), (x + wdt * rng.uniform(.4, 1), yy)])
            yy += 2
    k.lines(PL(refl), 1.)

    # ---- the bridge
    deck_h = max(2.5, H * .03)
    # side and main cables, suspenders
    att = Yt + H * .03
    def main_y(x):
        m = (xt[0] + xt[1]) / 2
        hw = (xt[1] - xt[0]) / 2
        return lerp(Yd - 1.5, att, ((x - m) / hw) ** 2)

    def side_y(x, s):
        xa = xt[0] if s < 0 else xt[1]
        xe = xa + s * (xt[1] - xt[0]) * .55
        u = (x - xa) / (xe - xa)
        return lerp(att, Yd - 1.5, u ** .75)
    cab, sus = [], []
    cab.append([(x, main_y(x)) for x in [lerp(xt[0], xt[1], i / 40) for i in range(41)]])
    for s in (-1, 1):
        xa = xt[0] if s < 0 else xt[1]
        xe = xa + s * (xt[1] - xt[0]) * .55
        cab.append([(lerp(xa, xe, i / 20), side_y(lerp(xa, xe, i / 20), s)) for i in range(21)])
        x = xa + s * 3
        while (x - xe) * s < 0:
            sus.append([(x, side_y(x, s)), (x, Yd)])
            x += s * 3
    x = xt[0] + 3
    while x < xt[1] - 2:
        sus.append([(x, main_y(x)), (x, Yd)])
        x += 3
    k.lines(PL(sus), .5)
    k.lines(PL(cab), 1.)
    # deck: a truss band running bank to bank, piers on the approaches
    deck = [(X0 - 2, Yd), (X1 + 2, Yd), (X1 + 2, Yd + deck_h), (X0 - 2, Yd + deck_h)]
    k.fill(P(deck, True), "#fff", True, 1.)
    zz = [(X0 + i * 2.5, Yd + (deck_h if i % 2 else 0)) for i in range(int(W / 2.5) + 2)]
    k.lines(P(zz, tol=0), .5)
    k.lines(f"M{_n(X0)},{_n(Yd + deck_h + .6)}h{_n(W)}", 1., True)
    piers = []
    for s in (-1, 1):
        for j in range(1, 4):
            px = (xt[0] if s < 0 else xt[1]) + s * (xt[1] - xt[0]) * (.18 * j + .12)
            if X0 < px < X1:
                piers.append([(px - 1.5, Yd + deck_h + 1), (px + 1.5, Yd + deck_h + 1), (px + 2, Yh), (px - 2, Yh)])
    if piers:
        k.fill("".join(P(p, True) for p in piers), "#fff", True, .5)
        k.lines("".join(hatch(p, 90, 1.5, .2) for p in piers), .5)
    # cars crossing (black, as engravers cut them)
    cars = []
    for cx0, dirn in ((xt[0] + (xt[1] - xt[0]) * .3, 1), (xt[0] + (xt[1] - xt[0]) * .66, -1), (X0 + W * .86, 1)):
        s = max(.7, H / 130)
        cars.append([(cx0 - 4 * s, Yd - .3), (cx0 - 4 * s, Yd - 1.6 * s), (cx0 - 1.8 * s * dirn, Yd - 1.8 * s),
                     (cx0 - 1 * s * dirn, Yd - 3 * s), (cx0 + 1.6 * s * dirn, Yd - 3 * s), (cx0 + 2.6 * s * dirn, Yd - 1.8 * s),
                     (cx0 + 4 * s, Yd - 1.5 * s), (cx0 + 4 * s, Yd - .3)])
    k.fill("".join(P(c, True, 0) for c in cars), "#000")
    # the two gothic towers
    for i, x in enumerate(xt):
        hb, ht = W * .03, W * .019
        top = Yt
        tw = [(x - ht, top), (x + ht, top), (x + hb, Yh + 1), (x - hb, Yh + 1)]
        spire = [(x - ht - .6, top + .5), (x - ht * .55, top - H * .04), (x, top - H * .085), (x + ht * .55, top - H * .04),
                 (x + ht + .6, top + .5)]
        k.fill(P(tw, True) + P(spire, True), "#fff", True, 1.)
        # shadow on the right face, darker below the deck
        rt = [(x + ht * .25, top), (x + ht, top), (x + hb, Yh + 1), (x + hb * .25, Yh + 1)]
        k.lines(hatch(rt, 90, 1.5, .4), .5)
        k.lines(hatch([(x + ht * .5 * .1, spire[2][1] + 2), (x + ht + .6, top + .5), (x, top + .5)], 90, 1.5, .4), .5)
        # finials
        fin = [[(x - ht - .6, top + .5), (x - ht - .6, top - H * .03)], [(x + ht + .6, top + .5), (x + ht + .6, top - H * .03)],
               [(x, spire[2][1]), (x, spire[2][1] - H * .025)]]
        k.lines(PL(fin), 1.)
        # gothic lancets above the deck, the great pointed arch below
        win = []
        n_l = 3 if H > 90 else 2
        span = (Yd - 2) - (top + H * .05)
        for j in range(n_l):
            y0 = top + H * .05 + span * j / n_l
            y1 = y0 + span / n_l - 2.2
            ww = lerp(ht, hb, (y1 - top) / (Yh - top)) * .42
            win.append(_lancet(x, y0, y1, ww))
        aw = lerp(ht, hb, .9) * .55
        win.append(_lancet(x, Yd + deck_h + 2.5, Yh + 1.2, aw))
        k.fill("".join(P(p, True, 0) for p in win), "#000")
        # tower bands (string courses)
        bands = []
        for j in range(n_l + 1):
            yy = top + H * .05 + span * j / n_l - 1.2
            wv = lerp(ht, hb, (yy - top) / (Yh - top))
            bands.append([(x - wv, yy), (x + wv, yy)])
        k.lines(PL(bands), 1., True)

    if detail >= 1:
        _foreground(k, X0, Y0, W, H, Yh, rng, detail)
    return k.svg()


def _lancet(x, y0, y1, hw):
    """A black equilateral pointed (gothic) opening, apex y0, sill y1, half-width hw."""
    ys = y0 + 1.732 * hw
    pts = [(x - hw, y1)]
    for i in range(9):
        a = PI - (PI / 3) * i / 8
        pts.append((x + hw + 2 * hw * math.cos(a), ys - 2 * hw * math.sin(a)))
    right = [(2 * x - px, py) for px, py in pts[::-1]]
    return pts + right[1:]


def _foreground(k, X0, Y0, W, H, Yh, rng, detail):
    X1, Y1 = X0 + W, Y0 + H

    def X(u):
        return X0 + W * u

    def Y(v):
        return Y0 + H * v
    # west spit (left): reeds and the heron
    lb_top = [(X(-.02), Y(.70)), (X(.06), Y(.72)), (X(.14), Y(.755)), (X(.22), Y(.785)), (X(.30), Y(.81)),
              (X(.36), Y(.86)), (X(.40), Y(.95)), (X(.42), Y(1.02))]
    lbank = lb_top + [(X(-.02), Y(1.02))]
    # east bank (right) rising toward the bridge with the road on it
    rb_top = []
    for i in range(41):
        u = i / 40
        rb_top.append((lerp(X(.44), X1 + 2, u), lerp(Y(1.02), Y(.68), 1 - (1 - u) ** 1.8) - .7 * math.sin(i * 1.9)))
    rbank = rb_top + [(X1 + 2, Y(1.02))]
    for bank, top, ang in ((lbank, lb_top, 8), (rbank, rb_top, -12)):
        k.fill(P(bank, True), C.pat("M"), False)
        k.lines(hatch(bank, ang + 60, 3, .3), .5)
        k.lines(hatch(bank, ang + 70, 3, .2, 0) if False else "", .5)
        tufts = []
        for (x, y) in top[1:-1]:
            tufts.append([(x - 1.2, y + 3), (x - .3, y - 1.5), (x + .3, y + 3)])
        k.lines(PL(tufts), .5)
        k.lines(P(top), 1.)
        k.lines(P([(x, y + 1.6) for x, y in top]), 1.)

    # the road: wide at the foot, climbing the east bank to the bridge
    def edge(t, side):
        xb = X(.56 if side < 0 else .90)
        xv = X(.865 if side < 0 else .895)
        x = lerp(xb, xv, t ** .8) - W * .07 * math.sin(t * PI) * (1 - t)
        y = lerp(Y(1.02), Y(.70), 1 - (1 - t) ** 1.6)
        return (x, y)
    L = [edge(i / 30, -1) for i in range(31)]
    R = [edge(i / 30, 1) for i in range(31)]
    road = L + R[::-1]
    k.fill(P(road, True), "#fff", False)
    k.lines(hatch(road, 0, 3, .6), .5)
    k.lines(P(L) + P(R), 1.)
    dash = []
    for i in range(0, 28, 3):
        a = ((L[i][0] + R[i][0]) / 2, (L[i][1] + R[i][1]) / 2)
        j = i + 1
        b = ((L[j][0] + R[j][0]) / 2, (L[j][1] + R[j][1]) / 2)
        dash.append([a, b])
    k.lines(PL(dash), 1.5 if detail >= 2 else 1.)
    k.lines(P([(x - 1.3, y) for x, y in L[:22]]), 1.)
    # a little car climbing toward the bridge
    if detail >= 2:
        t = .55
        ca, cb = edge(t, -1), edge(t, 1)
        ccx, ccy, s = (ca[0] + cb[0]) / 2, (ca[1] + cb[1]) / 2, max(.9, H / 120)
        car = [(ccx - 5 * s, ccy), (ccx - 5 * s, ccy - 2.2 * s), (ccx - 2.5 * s, ccy - 2.6 * s), (ccx - 1.2 * s, ccy - 4.4 * s),
               (ccx + 2.4 * s, ccy - 4.4 * s), (ccx + 3.6 * s, ccy - 2.6 * s), (ccx + 5 * s, ccy - 2.2 * s), (ccx + 5 * s, ccy)]
        k.fill(P(car, True, 0), "#000")
        k.fill(P([(ccx - .8 * s, ccy - 3.9 * s), (ccx + 2.1 * s, ccy - 3.9 * s), (ccx + 2.9 * s, ccy - 2.7 * s), (ccx - .8 * s, ccy - 2.7 * s)], True, 0), "#fff")
        k.fill(P(_ell(ccx - 3 * s, ccy, 1.3 * s, 1.3 * s, 10), True, 0) + P(_ell(ccx + 3 * s, ccy, 1.3 * s, 1.3 * s, 10), True, 0), "#fff", True, 1.)

    if detail < 2:
        return
    # the fingerpost: four arms for the four drives (school, Lake Oswego, St. Johns, the beach)
    px, py0 = X(.585), Y(.97)
    ph = H * .34
    top = py0 - ph
    post = [(px - 1.6, py0), (px - 1.3, top), (px + 1.3, top), (px + 1.6, py0)]
    k.fill(P(post, True) + P([(px - 1.9, top + .4), (px, top - 2.6), (px + 1.9, top + .4)], True), "#fff", True, 1.)
    k.lines(P([(px + .6, top + 1), (px + .8, py0)]), 1.)
    arms = []
    hh = max(2.2, H * .021)
    for j, (dirn, tilt, ln) in enumerate(((-1, -.10, .13), (1, .08, .115), (-1, .05, .10), (1, -.07, .125))):
        ay = top + 3.5 + j * (2 * hh + 1.6)
        L0 = H * ln
        x0, x1 = px + dirn * 1.3, px + dirn * L0
        sl = tilt * L0
        arms.append([(x0, ay - hh), (x1, ay - hh + sl), (x1 + dirn * hh * 1.2, ay + sl), (x1, ay + hh + sl), (x0, ay + hh)])
    k.fill("".join(P(a, True, 0) for a in arms), "#fff", True, 1.)
    k.fill("".join(P([a[4], a[3], a[2], (a[3][0], a[3][1] - 1.4), (a[4][0], a[4][1] - 1.4)], True, 0) for a in arms), "#000")
    rule = []
    for a in arms:
        (x0, y0), (x1, y1) = a[0], a[1]
        (x3, y3), (x4, y4) = a[3], a[4]
        for f in (.33, .66):
            rule.append([(lerp(x0, x4, f) + (1 if x1 > x0 else -1) * 1.5, lerp(y0, y4, f)), (lerp(x1, x3, f), lerp(y1, y3, f))])
        rule.append([(x4, y4 - .6), (x3, y3 - .6)])
    k.lines(PL(rule), .5)
    k.fill(P([(px - 3.5, py0 - 1), (px + 3.5, py0 - 1), (px + 4.5, py0 + 2), (px - 4.5, py0 + 2)], True), "#000")

    # Easter egg: a Sauvie Island great blue heron on the spit, among reeds
    hx, hy, hs = X(.25), Y(.795), H * .27
    reeds = []
    for i in range(14):
        rx = X(.04 + .024 * i) + rng.uniform(-1, 1)
        if abs(rx - hx) < hs * .7:
            continue
        ry = lerp(Y(.72), Y(.83), (rx - X0) / (W * .36))
        rh = hs * rng.uniform(.35, .75)
        bend = rng.uniform(-.3, .3) * rh
        reeds.append([(rx, ry + 2), (rx + bend * .3, ry - rh * .5), (rx + bend, ry - rh)])
    k.lines(PL(reeds), .5)
    _heron(k, hx, hy, hs)


def _heron(k, x, y, s):
    """A great blue heron standing at (x, y) (feet), s tall, facing left: hunched blue-grey body,
    S-curved neck, black crest plume, dagger bill, long legs."""
    def p(u, v):
        return (x + u * s, y - v * s)
    # legs first
    k.lines(PL([[p(.03, .47), p(.01, .22), p(.0, .01)], [p(.09, .47), p(.11, .22), p(.14, .01)]]), .5 if s < 40 else 1.)
    k.lines(PL([[p(-.08, 0), p(.06, .01)], [p(.08, 0), p(.22, .01)]]), .5)
    body = [p(-.10, .63), p(-.02, .71), p(.14, .70), p(.27, .62), p(.40, .44), p(.33, .45), p(.18, .48), p(.04, .48), p(-.07, .54)]
    k.fill(P(body, True, 0), "#fff", True, 1.)
    k.lines(hatch(body, -30, 1.5, .3, .4), .5)
    wing = [p(.0, .66), p(.14, .68), p(.25, .61), p(.38, .45), p(.2, .53), p(.05, .57)]
    k.fill(P(wing, True, 0), "#000")
    # neck as a tapered filled band
    c = [p(-.08, .62), p(-.15, .68), p(-.16, .75), p(-.10, .82), p(-.11, .89), p(-.17, .935)]
    wd = [.045, .04, .035, .03, .028, .03]
    l, r = [], []
    for i, (cx, cy) in enumerate(c):
        a0 = c[max(0, i - 1)]
        a1 = c[min(len(c) - 1, i + 1)]
        dx, dy = a1[0] - a0[0], a1[1] - a0[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * wd[i] * s / 2, dx / L * wd[i] * s / 2
        l.append((cx + nx, cy + ny))
        r.append((cx - nx, cy - ny))
    neck = l + r[::-1]
    k.fill(P(neck, True, 0), "#fff", True, .5)
    k.lines(P([(px + .4, py) for px, py in r[1:4]], tol=0), 1.)
    head = _ell(x - .185 * s, y - .945 * s, .045 * s, .03 * s, 14)
    k.fill(P(head, True, 0), "#fff", True, .5)
    k.fill(P([p(-.21, .955), p(-.46, .935), p(-.21, .925)], True, 0), "#000")
    k.fill(P([p(-.17, .975), p(-.02, 1.0), p(-.05, .985), p(-.15, .955)], True, 0), "#000")
    k.fill(P(_ell(x - .2 * s, y - .948 * s, .7, .7, 6), True, 0), "#000")


# ------------------------------------------------------------------------------------------------
# wheels: the main volutes wind into spoked wheels
# ------------------------------------------------------------------------------------------------

def wheel(cx, cy, r):
    k = Ink()
    k.fill(P(_ell(cx, cy, r + 1, r + 1, 40), True), "#000")
    k.fill(P(_ell(cx, cy, r - .8, r - .8, 40), True), "#fff")
    k.lines(P(_ell(cx, cy, r - 2, r - 2, 36) + [_ell(cx, cy, r - 2, r - 2, 36)[0]]), .5)
    sp = []
    for i in range(12):
        a = 2 * PI * i / 12
        sp.append([(cx + r * .25 * math.cos(a), cy + r * .25 * math.sin(a)),
                   (cx + (r - 2) * math.cos(a + .12), cy + (r - 2) * math.sin(a + .12))])
    k.lines(PL(sp), .5 if r < 12 else 1.)
    k.fill(P(_ell(cx, cy, r * .28, r * .28, 20), True), "#fff", True, 1.)
    k.fill(P(_ell(cx, cy, r * .12, r * .12, 12), True), "#000")
    # shade the lower right inside of the rim
    k.lines(P(_ell(cx + .5, cy + .5, r - 1.3, r - 1.3, 24, -.3, 1.9)), 1.)
    return k.svg()


# ------------------------------------------------------------------------------------------------
# lettering drawn as paths
# ------------------------------------------------------------------------------------------------

_FONT = {
    "D": (4.2, [[(0, 0), (0, 6)], [(0, 0), (2, 0), (3.5, .8), (4.1, 3), (3.5, 5.2), (2, 6), (0, 6)]]),
    "R": (4, [[(0, 6), (0, 0), (2.6, 0), (3.6, .6), (3.9, 1.6), (3.6, 2.6), (2.6, 3.1), (0, 3.1)], [(2.1, 3.1), (4, 6)]]),
    "I": (1, [[(.5, 0), (.5, 6)]]),
    "V": (4.4, [[(0, 0), (2.2, 6), (4.4, 0)]]),
    "E": (3.6, [[(3.6, 0), (0, 0), (0, 6), (3.6, 6)], [(0, 3), (2.8, 3)]]),
    "T": (4, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
    "M": (5, [[(0, 6), (0, 0), (2.5, 4.2), (5, 0), (5, 6)]]),
    "S": (3.8, [[(3.6, .8), (2.8, 0), (1, 0), (.2, .8), (.2, 2.2), (1, 3), (2.8, 3), (3.7, 3.8), (3.7, 5.2), (2.9, 6), (1, 6), (.1, 5.2)]]),
    " ": (2.4, []),
}


def letter_along(text, centre, size):
    """Stroke letters `size` px tall centred along the polyline `centre`."""
    sc = size / 6
    widths = [_FONT[c][0] * sc for c in text]
    gap = 1.6 * sc
    total = sum(widths) + gap * (len(text) - 1)
    S = [0.]
    for a, b in zip(centre, centre[1:]):
        S.append(S[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

    def at(s):
        for i in range(1, len(S)):
            if S[i] >= s:
                t = (s - S[i - 1]) / max(1e-6, S[i] - S[i - 1])
                a, b = centre[i - 1], centre[i]
                return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), math.atan2(b[1] - a[1], b[0] - a[0]))
        a, b = centre[-2], centre[-1]
        return (b[0], b[1], math.atan2(b[1] - a[1], b[0] - a[0]))
    s = (S[-1] - total) / 2
    out = []
    for c, wdt in zip(text, widths):
        ox, oy, ang = at(s + wdt / 2)
        ca, sa = math.cos(ang), math.sin(ang)
        for stroke in _FONT[c][1]:
            pts = []
            for u, v in stroke:
                lx, ly = u * sc - wdt / 2, v * sc - size / 2
                pts.append((ox + lx * ca - ly * sa, oy + lx * sa + ly * ca))
            out.append(pts)
        s += wdt + gap
    return out


# ------------------------------------------------------------------------------------------------
# layouts (house frame, with the field filled edge to edge)
# ------------------------------------------------------------------------------------------------

def _clip_path(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.3, 150)
    o.append(C._clip("rb%d" % h, 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 3.8, ry - 3.8
    field = _ell(cx, cy, fx, fy, 64)
    o.append(_clip_path("rbf%d" % h, P(field, True, 0), scene(cx - fx, cy - fy, 2 * fx, 2 * fy, seed, 0)))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .47, gh * 1.75)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
        sp = C.volute_spine(vx, vy, r, 90 if side < 0 else 90, 1.4, side < 0, .9, -.5)
        eyes.append(sp[-1])
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip("rm%d" % h, 0, gy0, w, gh, cv.svg()))
    for ex, ey in eyes:
        o.append(wheel(ex, ey, max(5., r * .2)))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    xs = [float(v) for v in []]
    a = cw / 2
    b = (gh + 4) / 2
    o.append(_clip_path("rmf%d" % h, inner, scene(cx - a, cy - b, cw, gh + 4, seed, 2 if h >= 150 else 1)))
    # re-cut the inner bead edge over the scene
    bw = max(5., min(cw, gh + 4) * .07)
    ia, ib = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    sp = C._superellipse(cx, cy, ia, ib)
    o.append(f'<path d="{_d(sp + [sp[0]], tol=.1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.dark_ground((0, 0, w, py0), "L"))
    o.append(C.bead_moulding(0, 2.5, w, 1., fillet=False))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
        a0, flip = (100, True) if side < 0 else (80, False)
        eyes.append((C.volute_spine(vx, vy, r1, a0, 1.45, flip, .8, -.5)[-1], r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip("rt%d" % h, px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    for (ex, ey), rr in eyes:
        o.append(wheel(ex, ey, max(6., rr * .2)))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_clip_path("rtf%d" % h, inner, scene(cx - cw / 2, cy - ch / 2, cw, ch, seed, 2)))
    bw = max(5., min(cw, ch) * .07)
    sp = C._superellipse(cx, cy, cw / 2 - bw * 1.6, ch / 2 - bw * 1.6)
    o.append(f'<path d="{_d(sp + [sp[0]], tol=.1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(19, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(f'<path d="{PL(letter_along("DRIVE TIMES", centre, bh * .56), 0)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, ped_h), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet_map(tx, ty, tw, th, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip("rf%d" % h, w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _tablet_map(tx, ty, tw, th, seed):
    """The pedestal's tablet engraved as a route map: home on Sauvie Island, four roads out."""
    k = Ink()
    x0, y0, x1, y1 = tx + 2.5, ty + 2.5, tx + tw - 1, ty + th - 1
    k.lines(hatch([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0, 2, .3), .5)
    # the river as a white band crossing the tablet
    rv = [(x0 + (x1 - x0) * u, lerp(y0, y1, .3 + .35 * u) + 2 * math.sin(u * 9)) for u in [i / 30 for i in range(31)]]
    k.lines(P(rv), 1.5)
    home = (x0 + (x1 - x0) * .5, lerp(y0, y1, .55))
    dests = [(x0 + (x1 - x0) * .1, y0 + (y1 - y0) * .25), (x0 + (x1 - x0) * .88, y0 + (y1 - y0) * .78),
             (x0 + (x1 - x0) * .7, y0 + (y1 - y0) * .2), (x0 + (x1 - x0) * .2, y0 + (y1 - y0) * .8)]
    roads = []
    for i, (dx, dy) in enumerate(dests):
        pts = []
        for j in range(21):
            u = j / 20
            pts.append((lerp(home[0], dx, u), lerp(home[1], dy, u) + (3 if i % 2 else -3) * math.sin(u * PI)))
        roads.append(pts)
    k.lines(PL(roads), 1.)
    k.fill("".join(P(_ell(dx, dy, 1.8, 1.8, 10), True, 0) for dx, dy in dests), "#000")
    k.fill(P(_ell(home[0], home[1], 2.5, 2.5, 12), True, 0), "#fff", True, 1.)
    return k.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 41
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
