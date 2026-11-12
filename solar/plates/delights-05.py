"""delights-05 "Old Portland - The city as it was" (Library of Congress, 1899: the Oregonian Building).

The plate engraves the 1892 Oregonian Building as it stood in 1899: its nine-storey Romanesque
block and the corner clock tower with its belvedere and steep pyramid roof, a single-truck
streetcar on the cobbles, neighbouring blocks, and a ruled 1899 sky, all set in the house
cartouche between acanthus volutes. Short plates carry the tower's clock dial as the medallion;
tall plates add a lettered ribbon ("THE CITY AS IT WAS") and a lettered pedestal tablet.
Easter egg: a Sauvie Island heron flies over the tower (tall/medium), and a tiny "P" maker's mark
sits on the clock dial (short). The clock's time and the clouds change with the date.
"""
import sys
import math
import random
import engraving_codex as C

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


def _word_w(s, track=1.6):
    return sum(_G[c][0] + track for c in s) - track


def letter_line(s, cx, cy, size, track=1.6):
    """Polylines of s centred at (cx, cy), cap height `size` px."""
    k = size / 6.
    x = cx - _word_w(s, track) * k / 2
    out = []
    for c in s:
        gw, strokes = _G[c]
        for st in strokes:
            out.append([(x + px * k, cy - size / 2 + py * k) for px, py in st])
        x += (gw + track) * k
    return out


def letter_arc(s, centre, size, track=1.6):
    """Letters set along a polyline (the ribbon's face centre), centred on it."""
    L = [0.]
    for (ax, ay), (bx, by) in zip(centre, centre[1:]):
        L.append(L[-1] + math.hypot(bx - ax, by - ay))
    k = size / 6.
    tot = _word_w(s, track) * k
    s0 = L[-1] / 2 - tot / 2

    def at(u):
        u = max(0, min(L[-1] - 1e-6, u))
        for i in range(len(L) - 1):
            if L[i + 1] >= u:
                t = (u - L[i]) / max(1e-6, L[i + 1] - L[i])
                (ax, ay), (bx, by) = centre[i], centre[i + 1]
                return ax + (bx - ax) * t, ay + (by - ay) * t, math.atan2(by - ay, bx - ax)
        return centre[-1][0], centre[-1][1], 0.

    out = []
    u = s0
    for c in s:
        gw, strokes = _G[c]
        mx, my, a = at(u + gw * k / 2)
        ca, sa = math.cos(a), math.sin(a)
        for st in strokes:
            pts = []
            for px, py in st:
                lx, ly = (px - gw / 2) * k, (py - 3) * k
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            out.append(pts)
        u += (gw + track) * k
    return out


def _pl_d(pls):
    return "".join(_d(p, tol=0) for p in pls if len(p) > 1)


# ------------------------------------------------------------------------------------------------
# the subject: the Oregonian Building, 1899
# ------------------------------------------------------------------------------------------------

def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _hlines(x0, x1, y0, y1, pitch):
    """Horizontal crisp rules on the half-px grid between y0 and y1."""
    out = []
    y = math.floor(y0 * 2) / 2 + .25
    while y < y1:
        out.append(f"M{_n(x0)},{_n(y)}H{_n(x1)}")
        y += pitch
    return "".join(out)


def heron(cx, cy, s, flip=False):
    """A great blue heron in flight, as a black silhouette path: neck folded, legs trailing."""
    f = -1 if flip else 1
    body = [(0, 0), (3, -.6), (5.5, -.4), (6.8, .2), (7.2, 1.0), (6.4, 1.5), (5.4, 1.2), (6.6, 1.9), (8.6, 2.0),
            (8.6, 2.4), (6.2, 2.5), (4.8, 1.9), (3.6, 2.3), (1.0, 1.8), (-3.5, 1.5), (-7, 1.7), (-7, 1.3), (-3.5, .9), (-.6, .7)]
    wing = [(1.2, -.2), (-1.4, -4.4), (-3.6, -7.2), (-2.4, -7.0), (1.4, -3.6), (3.6, -.4)]
    wing2 = [(.4, 1.0), (2.6, 3.4), (3.0, 4.6), (1.8, 4.0), (-.6, 1.6)]
    P = lambda pts: [(cx + f * x * s, cy + y * s) for x, y in pts]
    return _d(P(body), True, 0) + _d(P(wing), True, 0) + _d(P(wing2), True, 0)


def oregonian(fx, fy, fw, fh, seed=0, egg=True):
    """The vignette box (fx, fy, fw, fh): sky, neighbours, the Oregonian Building and its tower,
    cobbled street and a streetcar. Returns an SVG fragment (callers clip it to the field)."""
    rng = random.Random(seed)
    o = []
    G = fy + fh * (.83 if fh > 120 else .87)                     # street line under the building
    top = fy + max(2., fh * .02)
    U = (G - top) / 100.                   # 100 units from street to the finial
    X0 = fx + fw * .5 + 4 * U              # tower axis
    X = lambda u: X0 + u * U
    Y = lambda v: G - v * U

    # sky: ruled, closer at the zenith (pitch 1.5 -> 2 -> 3), crisp horizontal rules
    sky = _hlines(fx, fx + fw, fy, fy + fh * .3, 1.5) + _hlines(fx, fx + fw, fy + fh * .3, fy + fh * .58, 2) \
        + _hlines(fx, fx + fw, fy + fh * .58, G, 3)
    o.append(f'<path d="{sky}" stroke="#000" stroke-width=".5"{CR}/>')

    cv = C.Canvas()
    black = []

    # clouds: soft white banks cut out of the ruled sky, shaded underneath
    for i in range(3):
        cxl = fx + fw * (.12 + .38 * i + rng.uniform(-.05, .05))
        cyl = fy + fh * rng.uniform(.18, .34)
        rw = fw * rng.uniform(.10, .16)
        rh = max(4., fh * .035)
        # billowed top: a row of bumps of varying size over a flat, slightly sagging base
        nb = 4 + rng.randrange(2)
        xs = [cxl - rw + 2 * rw * k / nb for k in range(nb + 1)]
        pts = [(cxl + rw, cyl + rh * .6)]
        pts += [(cxl + rw - 2 * rw * k / 10, cyl + rh * (.6 + .25 * math.sin(PI * k / 10))) for k in range(1, 10)]
        pts.append((cxl - rw, cyl + rh * .6))
        bumps = []
        for k in range(nb):
            m_ = (xs[k] + xs[k + 1]) / 2
            rr = rw / nb * rng.uniform(1.25, 1.6) * (1.25 if 0 < k < nb - 1 else 1)
            bumps.append((m_, cyl + rh * .6 - rr * .15, rr))
        for j in range(41):
            x_ = cxl - rw + 2 * rw * j / 40
            yt = cyl + rh * .6
            for (bx, by, br) in bumps:
                if abs(x_ - bx) < br:
                    yt = min(yt, by - math.sqrt(br * br - (x_ - bx) ** 2) * .95)
            pts.append((x_, yt))
        cv.obj([pts], .5)
        for f in (.82, .64, .46):
            q = [(cxl + (x_ - cxl) * f, cyl + (y_ - cyl) * f + rh * (1 - f) * .9) for x_, y_ in pts]
            cv.hair([[p_ for p_ in q if p_[1] > cyl - rh * .2]])
        cv.hair([l for l in C.hatch_poly(pts, 0, 2, .25) if l[0][1] > cyl + rh * .35])

    if egg:   # Easter egg: a Sauvie Island heron crossing the sky, over the tower's left shoulder
        o_heron = heron(X(-30), Y(86), U * .7)
    else:
        o_heron = ""

    # neighbouring blocks, lower, stepping off to both edges of the field
    def block(x0, x1, hgt, tone, roof_v=0., side=None):
        y0 = G - hgt
        poly = _rect(x0, y0, x1, G + 1)
        cv.obj([poly], 1.)
        if tone == "dark":
            cv.hair(C.hatch_poly(poly, 45, 2))
            cv.hair(C.hatch_poly(poly, -45, 3))
        else:
            cv.hair(C.hatch_poly(poly, 90, 2))
        # cornice
        cv.obj([_rect(x0 - 1, y0 - 1.5, x1 + 1, y0 + 1)], .5)
        cv.hair([[(x0 - 1, y0), (x1 + 1, y0)]])
        # windows
        fl = max(5., 6 * U)
        ww = max(1.5, 2.2 * U)
        nx = max(1, int((x1 - x0 - 2) / (ww * 2.3)))
        sp = (x1 - x0) / nx
        yy = y0 + fl * .6
        while yy + fl * .5 < G - fl * .5:
            for k in range(nx):
                wx = x0 + sp * (k + .5) - ww / 2
                if tone == "dark":
                    cv.obj([_rect(wx, yy, wx + ww, yy + fl * .5)], .5)
                else:
                    black.append(_rect(wx, yy, wx + ww, yy + fl * .5))
            yy += fl

    lx = X(-38)
    x = lx
    while x > fx - 4:
        bw_ = rng.uniform(14, 24) * U
        block(x - bw_, x, rng.uniform(22, 34) * U * (1 if x > fx + fw * .15 else .85), "light")
        x -= bw_
    x = X(34)
    while x < fx + fw + 4:
        bw_ = rng.uniform(14, 22) * U
        block(x, x + bw_, rng.uniform(18, 28) * U, "dark")
        x += bw_

    # --- the main block: front face (lit) from u=-38..-6, side face receding u=10..34
    BT = 52
    side = [(X(10), Y(BT)), (X(34), Y(BT - 4)), (X(34), Y(-1)), (X(10), Y(-1))]
    cv.obj([side], 1.)
    cv.hair(C.hatch_poly(side, 90, 1.5))
    cv.hair(C.hatch_poly(side, 0, 3, .25))
    # side windows: grey slits catching the sky
    for fl_ in range(9):
        v = 6 + fl_ * 5.2
        for k in range(5):
            u0, u1 = 12 + k * 4.6, 13.6 + k * 4.6
            dv = lambda u: (u - 10) / 24 * 4 * (v / BT)
            q = [(X(u0), Y(v + 3.2 - dv(u0))), (X(u1), Y(v + 3.2 - dv(u1))), (X(u1), Y(v - dv(u1))), (X(u0), Y(v - dv(u0)))]
            cv.obj([q], .5)
    # side cornice, foreshortened
    sc = [(X(10), Y(BT + 2.5)), (X(34), Y(BT - 2)), (X(34.5), Y(BT - 4.2)), (X(10), Y(BT - .6))]
    cv.obj([sc], 1.)
    cv.hair(C.hatch_poly(sc, 90, 1.5))

    front = _rect(X(-38), Y(BT), X(-6), Y(-1))
    cv.obj([front], 1.)
    # ashlar coursing: light horizontal rules, closer in the rusticated base
    cv.hair([[(X(-38), Y(v)), (X(-6), Y(v))] for v in [i * 1.6 for i in range(1, 7)]])
    cv.hair([[(X(-38), Y(v)), (X(-6), Y(v))] for v in [12 + i * 3 for i in range(14)]])
    # string courses and cornice
    for v in (10, 15.5, 47):
        cv.obj([_rect(X(-39), Y(v + .9), X(-5), Y(v - .5))], 1.)
    cn = _rect(X(-40), Y(BT + 2.5), X(-5), Y(BT - .6))
    cv.obj([cn], 1.)
    cv.hair(C.hatch_poly(cn, 0, 1.5, .25))
    cv.hair([[(X(-40) + k * U * 1.4, Y(BT - .6)), (X(-40) + k * U * 1.4, Y(BT - 1.9))] for k in range(25)])
    # ground floor: four great Romanesque arches, dark recesses with a keystone highlight
    for k in range(4):
        ax0, ax1 = X(-37 + k * 7.6), X(-37 + k * 7.6 + 5.6)
        arch = [(ax0, Y(0)), (ax0, Y(5.5))] + _oval((ax0 + ax1) / 2, Y(5.5), (ax1 - ax0) / 2, 2.8 * U, PI, TAU, 10)[1:] + [(ax1, Y(0))]
        black.append(arch)
        cv.obj([_oval((ax0 + ax1) / 2, Y(5.5), (ax1 - ax0) / 2 + 1.2 * U, 4 * U, PI, TAU, 10) + [(ax1 + 1.2 * U, Y(5.4)), (ax0 - 1.2 * U, Y(5.4))]], .5)
        cv.hair(C.hatch_poly(_oval((ax0 + ax1) / 2, Y(5.5), (ax1 - ax0) / 2 + 1.2 * U, 4 * U, PI, TAU, 10), 90, 1.5))
    # upper floors: paired windows in five bays, arched in arcades every third storey
    for fl_ in range(7):
        v = 17 + fl_ * 4.3
        for b in range(5):
            for p in range(2):
                u0 = -36.6 + b * 6.2 + p * 2.6
                wq = _rect(X(u0), Y(v + 2.8), X(u0 + 1.8), Y(v))
                if fl_ in (2, 5):
                    wq = [(X(u0), Y(v))] + [(X(u0), Y(v + 2.6))] + _oval(X(u0 + .9), Y(v + 2.6), .9 * U, .9 * U, PI, TAU, 6)[1:] + [(X(u0 + 1.8), Y(v))]
                black.append(wq)
        cv.hair([[(X(-38), Y(v - .5)), (X(-6), Y(v - .5))]])
    # attic: a row of small round-arched lights
    for k in range(12):
        u0 = -37 + k * 2.6
        black.append([(X(u0), Y(48.4))] + [(X(u0), Y(49.6))] + _oval(X(u0 + .6), Y(49.6), .6 * U, .6 * U, PI, TAU, 5)[1:] + [(X(u0 + 1.2), Y(48.4))])
    # pilasters between bays
    for b in range(6):
        u = -37.4 + b * 6.2 - .5
        cv.hair([[(X(u), Y(16)), (X(u), Y(46))], [(X(u + .7), Y(16)), (X(u + .7), Y(46))]])

    # --- the corner tower: front u=-6..6, shaded side u=6..10
    def tower_stage(v0, v1, front_hatch=None):
        f_ = _rect(X(-6), Y(v1), X(6), Y(v0))
        s_ = [(X(6), Y(v1)), (X(10), Y(v1 - .6)), (X(10), Y(v0 - .6)), (X(6), Y(v0))]
        cv.obj([s_], 1.)
        cv.hair(C.hatch_poly(s_, 90, 1.5))
        cv.hair(C.hatch_poly(s_, 45, 3))
        cv.obj([f_], 1.)
        if front_hatch:
            cv.hair(front_hatch(f_))
        return f_

    def belt(v, d=1.):
        q = [(X(-7), Y(v + d)), (X(7), Y(v + d)), (X(11), Y(v + d - .6)), (X(11), Y(v - .6)), (X(7), Y(v)), (X(-7), Y(v))]
        cv.obj([q], 1.)
        cv.hair(C.hatch_poly([(X(7), Y(v + d)), (X(11), Y(v + d - .6)), (X(11), Y(v - .6)), (X(7), Y(v))], 90, 1.5))

    tower_stage(-1, 62, lambda f_: [[(X(-6), Y(v)), (X(6), Y(v))] for v in [i * 3 + 1.6 for i in range(20)]]
                 + [[(x_, Y(-1)), (x_, Y(62))] for x_ in (X(3.5), X(4.5), X(5.3))])
    # tower entrance arch and stacked windows
    black.append([(X(-2.6), Y(0)), (X(-2.6), Y(6))] + _oval(X(0), Y(6), 2.6 * U, 2.6 * U, PI, TAU, 10)[1:] + [(X(2.6), Y(0))])
    for i in range(10):
        v = 17 + i * 4.3
        if v > 58:
            break
        black.append(_rect(X(-2.8), Y(v + 2.8), X(-.6), Y(v)))
        black.append(_rect(X(.6), Y(v + 2.8), X(2.8), Y(v)))
    belt(62)
    # clock stage
    tower_stage(63, 73, lambda f_: C.hatch_poly(f_, 90, 3))
    cx, cy, cr = X(0), Y(68), 4.3 * U
    ring = _oval(cx, cy, cr + .9 * U, cr + .9 * U, n=28)
    cv.obj([ring], 1.)
    cv.hair(C.hatch_poly(ring, 45, 1.5))
    dial = _oval(cx, cy, cr, cr, n=28)
    cv.obj([dial], 1.)
    cv.hair([[(cx + cr * .78 * math.cos(TAU * i / 12), cy + cr * .78 * math.sin(TAU * i / 12)),
              (cx + cr * .98 * math.cos(TAU * i / 12), cy + cr * .98 * math.sin(TAU * i / 12))] for i in range(12)])
    hh, mm = 6 + seed % 4, (seed * 7) % 60
    ah, am = TAU * ((hh % 12) + mm / 60) / 12 - PI / 2, TAU * mm / 60 - PI / 2
    cv.line([[(cx, cy), (cx + cr * .5 * math.cos(ah), cy + cr * .5 * math.sin(ah))]])
    cv.hair([[(cx, cy), (cx + cr * .82 * math.cos(am), cy + cr * .82 * math.sin(am))]])
    # side clock, foreshortened
    sdial = _oval(X(8), Y(68.2), 1.3 * U, cr, n=20)
    cv.obj([sdial], .5)
    belt(73, 1.5)
    # belvedere: open arcade, black voids between colonnettes
    tower_stage(74.5, 81, lambda f_: C.hatch_poly(f_, 90, 3))
    for k in range(3):
        u0 = -5 + k * 3.6
        black.append([(X(u0), Y(75)), (X(u0), Y(79))] + _oval(X(u0 + 1.3), Y(79), 1.3 * U, 1.2 * U, PI, TAU, 8)[1:] + [(X(u0 + 2.6), Y(75))])
    cv.hair([[(X(-6), Y(75.8)), (X(6), Y(75.8))]])
    belt(81, 1.4)
    # pyramid roof with corner pinnacles, slate courses on the lit face, shadow on the other
    apex = (X(1.2), Y(95))
    rf = [(X(-6.6), Y(82.4)), (X(6.6), Y(82.4)), apex]
    rs = [(X(6.6), Y(82.4)), (X(10.6), Y(81.8)), apex]
    cv.obj([rs], 1.)
    cv.hair(C.hatch_poly(rs, 90, 1.5))
    cv.hair(C.hatch_poly(rs, 30, 2))
    cv.obj([rf], 1.)
    cv.hair(C.hatch_poly(rf, 0, 2, .25))
    cv.hair(C.hatch_poly(rf, 70, 3))
    for u in (-6.6, 6.6, 10.6):
        pin = [(X(u - .7), Y(82.4)), (X(u + .7), Y(82.4)), (X(u), Y(87.5))]
        cv.obj([pin], .5)
        cv.hair(C.hatch_poly(pin, 90, 1.5))
    # finial and flagstaff
    cv.obj([_rect(apex[0] - .6, Y(99.5), apex[0] + .6, apex[1] + 1)], .5)
    cv.line([[(apex[0], apex[1]), (apex[0], Y(100))]])
    cv.obj([[(apex[0], Y(99.6)), (apex[0] + 5.5 * U, Y(98.4)), (apex[0], Y(97.2))]], .5)

    # overhead trolley wire across the street
    tw = Y(16)
    sky_cv = cv
    # --- the street
    st = C.Canvas()
    street = _rect(fx - 2, G - .5, fx + fw + 2, fy + fh + 2)
    st.obj([street], 1.)
    yy, pitch = G + 1.5, 1.5
    rows = []
    while yy < fy + fh + 2:
        rows.append(yy)
        yy += pitch
        pitch = 1.5 if yy < G + fh * .06 else (2 if yy < G + fh * .11 else 3)
    st.hair([[(fx - 2, y_), (fx + fw + 2, y_)] for y_ in rows])
    # cobble joints, wider apart toward the viewer
    for a_, b_ in zip(rows, rows[1:]):
        if b_ - a_ >= 2:
            g = (b_ - a_) * 2.2
            off = g / 2 if int(a_) % 2 else 0
            xx = fx + off
            js = []
            while xx < fx + fw:
                js.append([(xx, a_), (xx, b_)])
                xx += g
            st.hair(js)
    # rails converging toward the building's corner
    # sidewalk kerb
    st.line([[(fx - 2, G + .5), (fx + fw + 2, G + .5)]])

    # streetcar: single truck, clerestory roof, trolley pole up to the wire
    sx0, sx1 = X(13), X(41)
    sb = G + fh * .085
    stp = sb - 11 * U
    tw = stp - 7 * U
    for ry in (sb + 3.6 * U, sb + 4.6 * U):
        st.line([[(fx - 2, ry), (fx + fw + 2, ry)]])
    body = _rect(sx0, stp, sx1, sb)
    roof = [(sx0 - 1.2 * U, stp), (sx1 + 1.2 * U, stp), (sx1, stp - 1.6 * U), (sx0, stp - 1.6 * U)]
    clere = _rect(sx0 + 4 * U, stp - 3 * U, sx1 - 4 * U, stp - 1.5 * U)
    pole_top = (sx0 + (sx1 - sx0) * .2, tw)
    st.obj([], 0)
    st.hair([[(fx - 2, tw), (fx + fw + 2, tw)]])
    st.line([[(sx0 + (sx1 - sx0) * .75, stp - 3 * U), pole_top]])
    st.obj([clere], .5)
    st.hair(C.hatch_poly(clere, 90, 1.5))
    st.obj([roof], 1.)
    st.hair(C.hatch_poly(roof, 0, 1.5, .25))
    st.obj([body], 1.)
    lower = _rect(sx0, sb - 4.2 * U, sx1, sb)
    st.hair(C.hatch_poly(lower, 90, 1.5))
    st.hair(C.hatch_poly(lower, 0, 3, .25))
    st.line([[(sx0, sb - 4.2 * U), (sx1, sb - 4.2 * U)]])
    win = []
    for k in range(7):
        wx = sx0 + 1.6 * U + k * 3.6 * U
        win.append(_rect(wx, stp + 1.4 * U, wx + 2.4 * U, sb - 5.4 * U))
    # fenders and wheels
    whe = []
    for wx in (sx0 + 6 * U, sx1 - 6 * U):
        whe.append(_oval(wx, sb + 1.6 * U, 2 * U, 2 * U, n=16))
    # lamp post at the kerb
    lpx = X(-22)
    st.obj([_rect(lpx - .5, G - 14 * U, lpx + .5, G + 1)], 0)
    st.line([[(lpx, G + 1.5), (lpx, G - 13 * U)]])
    lamp = _oval(lpx, G - 14.5 * U, 1.3 * U, 1.6 * U, n=12)
    st.obj([lamp], .5)
    st.hair(C.hatch_poly(lamp, 0, 1.5, .25))

    o.append(cv.svg())
    if black:
        o.append(f'<path d="{"".join(_d(p, True, 0) for p in black)}" fill="#000" stroke="none"/>')
    if o_heron:
        o.append(f'<path d="{o_heron}" fill="#000" stroke="none"/>')
    o.append(st.svg())
    o.append(f'<path d="{"".join(_d(p, True, 0) for p in win + whe)}" fill="#000" stroke="none"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# the clock dial (short plates' medallion)
# ------------------------------------------------------------------------------------------------

def clock_medallion(cx, cy, rx, ry, seed=0):
    o = []
    outer = _oval(cx, cy, rx + 1, ry + 1, n=64)
    o.append(f'<path d="{_d(outer, True, 0)}" fill="#fff" stroke="none"/>')
    ring = _d(outer, True, 0) + _d(_oval(cx, cy, rx - 2, ry - 2, n=64)[::-1], True, 0)
    o.append(f'<path d="{ring}" fill="#000" fill-rule="evenodd"/>')
    # chapter ring with hour bars, minute dots
    r1x, r1y = rx - 3.5, ry - 3.5
    r2x, r2y = rx - 3.5 - min(6, ry * .32), ry - 3.5 - min(6, ry * .32)
    o.append(f'<path d="{_d(_oval(cx, cy, r1x, r1y, n=64), True, 0)}{_d(_oval(cx, cy, r2x, r2y, n=64), True, 0)}" stroke="#000" stroke-width=".5"/>')
    bars = []
    for i in range(12):
        a = TAU * i / 12
        c, s = math.cos(a), math.sin(a)
        for dk in ((-.035, .035) if i % 3 else (-.06, 0, .06)):
            bars.append([(cx + r1x * .97 * math.cos(a + dk), cy + r1y * .97 * math.sin(a + dk)),
                         (cx + r2x * 1.03 * math.cos(a + dk), cy + r2y * 1.03 * math.sin(a + dk))])
    o.append(f'<path d="{_pl_d(bars)}" stroke="#000" stroke-width="{1 if ry > 20 else .5}"/>')
    # dial centre: guilloche-free light ruling, a black boss
    inner = _oval(cx, cy, r2x - 1, r2y - 1, n=48)
    o.append(f'<path d="{C.hatch_d(inner, 0, 2, .25)}" stroke="#000" stroke-width=".5"{CR}/>')
    # the tiny maker's "P" (Easter egg) above the centre
    P = letter_line("P", cx, cy - r2y * .45, max(3, r2y * .28))
    o.append(f'<path d="{_d(_oval(cx, cy - r2y * .45, r2y * .26, r2y * .26, n=16), True, 0)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_pl_d(P)}" stroke="#000" stroke-width=".5"/>')
    hh, mm = 6 + seed % 4, (seed * 7) % 60
    ah, am = TAU * ((hh % 12) + mm / 60) / 12 - PI / 2, TAU * mm / 60 - PI / 2
    hand = lambda a, L, wdt: [(cx + L * math.cos(a) * r2x / r2y, cy + L * math.sin(a)),
                              (cx + wdt * math.cos(a + PI / 2), cy + wdt * math.sin(a + PI / 2)),
                              (cx - L * .18 * math.cos(a), cy - L * .18 * math.sin(a)),
                              (cx - wdt * math.cos(a + PI / 2), cy - wdt * math.sin(a + PI / 2))]
    o.append(f'<path d="{_d(hand(ah, r2y * .6, 1.4), True, 0)}{_d(hand(am, r2y * .9, 1.0), True, 0)}'
             f'{_d(_oval(cx, cy, 1.6, 1.6, n=10), True, 0)}" fill="#000"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# layouts (house layouts, re-cut for this page: no blank white anywhere)
# ------------------------------------------------------------------------------------------------

def _bg(w, h):
    return C.dark_ground((0, 0, w, h), "D")


def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _field_box(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _layout_band(w, h, seed):
    o = [_bg(w, h)]
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.6, 120)
    o.append(C._clip(C._uid("b5", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    o.append(clock_medallion(w / 2, top + gh / 2, gap / 2, gh / 2 - 1, seed))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = [_bg(w, h)]
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.6)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m5", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_box(cx, cy, cw, gh + 4)
    o.append(_field_clip(C._uid("mv5", w, h, seed), inner, oregonian(fx, fy, fw, fh, seed, egg=gh > 140)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = [_bg(w, h)]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .66
    cx, cy = w / 2, py0 + ph * .44
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .035), rmax=r1 * .9,
                   max_n=13, edge=.5, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t5", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_box(cx, cy, cw, ch)
    o.append(_field_clip(C._uid("tv5", w, h, seed), inner, oregonian(fx, fy, fw, fh, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 60), True, rng.randrange(1 << 20)))
    bh = min(17, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(f'<path d="{_pl_d(letter_arc("THE CITY AS IT WAS", centre, bh * .48, 2.0))}" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: lettered, ends filled with a light rule so no paper shows
    words = "OREGONIAN * PORTLAND * 1899"
    size = min(th * .56, 10)
    ww = _word_w(words, 2.2) * size / 6
    o.append(f'<path d="{_d(_rect(tx + 2.5, ty + 2.5, tx + tw - 1, ty + th - 1), True, 0)}" fill="{C.pat("L")}" stroke="none"/>')
    o.append(f'<path d="{_d(_rect(tx + tw / 2 - ww / 2 - 4, ty + 2.5, tx + tw / 2 + ww / 2 + 4, ty + th - 1), True, 0)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_pl_d(letter_line(words, tx + tw / 2 + .5, ty + th / 2 + .8, size, 2.2))}" stroke="#000" stroke-width="1"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f5", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
