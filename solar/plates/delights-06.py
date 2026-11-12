"""delights-06 "Live from Portland - A Portland show, recorded live" (Internet Archive, Live Music Archive).

The plate engraves a Portland club stage on show night: a draped proscenium with tasselled
curtains and a fringed valance, hanging spot cans throwing ruled beams onto the backline (amp
stacks, a drum kit with ride cymbal and hi-hat), the singer's vintage mic front and centre, the
plank stage lip, and the crowd in silhouette with a taper's mic stand rising out of it (the
Live Music Archive is built by tapers). Short plates carry a reel of recording tape as the
medallion. Easter egg: Parker's crossed drumsticks on the kick-drum head (and on the reel hub).
The set list varies by date: which beams are lit and how many hands are up.
"""
import sys
import math
import random
import engraving_codex as C

PI, TAU = math.pi, 2 * math.pi
CR = ' shape-rendering="crispEdges"'

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



_G.update({
    "V": (4, [[(0, 0), (2, 6), (4, 0)]]),
    "F": (3.6, [[(3.6, 0), (0, 0), (0, 6)], [(0, 3), (2.8, 3)]]),
    "K": (4, [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.4, 2.6), (4, 6)]]),
})


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _blk(polys):
    return "".join(_d(p, True, 0) for p in polys if len(p) > 2)


def _stick(x0, y0, x1, y1, w0, w1):
    """A tapered stick (drumstick, stand leg) as a polygon from width w0 to w1, with a bead tip."""
    a = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(a), math.cos(a)
    return [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
            (x1 + math.cos(a) * w1 * 1.2, y1 + math.sin(a) * w1 * 1.2),
            (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]


def _rings(cx, cy, rx, ry, r0, r1, pitch, a0=0., a1=TAU, n=40):
    out = []
    r = r1
    while r > r0:
        k = r / r1
        out.append(_oval(cx, cy, rx * k, ry * k, a0, a1, n))
        r -= pitch
    return out


# ------------------------------------------------------------------------------------------------
# the subject: a Portland club stage, show night
# ------------------------------------------------------------------------------------------------

def stage(fx, fy, fw, fh, seed=0, egg=True):
    rng = random.Random(seed)
    o = []
    S = min(fh / 100., fw / 140.)                   # one unit
    cx = fx + fw / 2
    yF = fy + fh * .70                              # back edge of the stage floor
    yL = fy + fh * .82                              # stage lip
    yV = fy + fh * .11                              # valance bottom

    # backdrop: a heavy black drape behind the band, in deep vertical folds (bulino rules that
    # crowd together in the troughs and part on the crests)
    lines = []
    x = fx - 2.
    while x < fx + fw + 2:
        lines.append(f"M{_n(x)},{_n(fy - 2)}V{_n(yF + 1)}")
        ph = math.sin((x - fx) / (fw / 9.) * PI)
        x += 1.5 if ph < .35 else 3.
    o.append(f'<path d="{"".join(lines)}" stroke="#000" stroke-width=".5"{CR}/>')
    dk = []
    for k in range(10):
        xk = fx + fw / 9. * (k - .5) * 1. + fw / 18.
        dk.append(_rect(xk - .6 * S, fy - 2, xk + .6 * S, yF + 1))
    o.append(f'<path d="{_blk(dk)}" fill="#000"/>')

    cv = C.Canvas()
    black = []

    # light beams from the spot cans, ruled light, cut out of the backdrop
    cans = [(-.36, rng.random() < .8), (-.15, True), (.15, True), (.36, rng.random() < .8)]
    for u, lit in cans:
        if not lit:
            continue
        sx, sy = cx + u * fw, yV + 3 * S
        tx = cx + u * fw * .25 + rng.uniform(-8, 8) * S
        beam = [(sx - 2.5 * S, sy), (sx + 2.5 * S, sy), (tx + 15 * S, yF + 6 * S), (tx - 15 * S, yF + 6 * S)]
        cv.obj([beam], 0)
        cv.hair(C.hatch_poly(beam, 0, 3, .25))

    # stage floor: planks converging on the band, ruled for depth
    floor = [(fx - 2, yF), (fx + fw + 2, yF), (fx + fw + 2, yL), (fx - 2, yL)]
    cv.obj([floor], 1.)
    vx, vy = cx, yF - (yL - yF) * 2.2
    planks = []
    for i in range(-14, 15):
        bx = cx + i * fw / 18
        t0 = (yF - vy) / (yL - vy)
        planks.append([(vx + (bx - vx) * t0, yF), (bx, yL)])
    cv.hair(planks)
    cv.hair(C.hatch_poly(floor, 0, 2, .25))
    # stage lip: a black fascia with a white nosing
    black.append(_rect(fx - 2, yL, fx + fw + 2, yL + 2.6 * S))

    # amp stacks either side of the kit
    def amp(ax, w_, h_):
        cab = _rect(ax - w_ / 2, yF + 2 * S - h_, ax + w_ / 2, yF + 2 * S)
        cv.obj([cab], 1.)
        g = _rect(ax - w_ / 2 + 2 * S, yF + 2 * S - h_ + 2 * S, ax + w_ / 2 - 2 * S, yF)
        cv.obj([g], .5)
        cv.hair(C.hatch_poly(g, 45, 2))
        cv.hair(C.hatch_poly(g, -45, 2))
        cv.line([[(ax - w_ / 2, yF + 2 * S - h_ / 2), (ax + w_ / 2, yF + 2 * S - h_ / 2)]])
        hy = yF + 2 * S - h_
        head = _rect(ax - w_ / 2, hy - h_ * .3, ax + w_ / 2, hy)
        cv.obj([head], 1.)
        cv.hair(C.hatch_poly(head, 0, 1.5, .25))
        panel = _rect(ax - w_ * .42, hy - h_ * .2, ax + w_ * .42, hy - h_ * .08)
        black.append(panel)
        for k in range(6):
            kx = ax - w_ * .36 + k * w_ * .144
            black.append(_oval(kx, hy - h_ * .26, max(.8, 1.1 * S), max(.8, 1.1 * S), n=8))
    aw, ah = fw * .16, fh * .26
    amp(cx - fw * .31, aw, ah)
    amp(cx + fw * .31, aw, ah)

    # an electric guitar on its stand, leaning, in front of the left stack
    def guitar(gx, gy, sc, lean):
        ca, sa = math.cos(lean), math.sin(lean)
        T = lambda pts: [(gx + x_ * ca - y_ * sa, gy + x_ * sa + y_ * ca) for x_, y_ in pts]
        body = []
        bouts = ((0., .38 * sc, 1.0 * sc, .86 * sc), (-.06 * sc, -.5 * sc, .78 * sc, .62 * sc))

        def inside(px, py):
            return any(((px - ex) / rx) ** 2 + ((py - ey) / ry) ** 2 <= 1 for ex, ey, rx, ry in bouts)
        for i in range(48):                     # ray-cast the union of two bouts: a waisted body
            t = TAU * i / 48
            r = 2.2 * sc
            while r > .05 * sc and not inside(r * math.cos(t), r * math.sin(t)):
                r -= .03 * sc
            body.append((r * math.cos(t), r * math.sin(t)))
        neck = T(_rect(-sc * .1, -sc * 3.5, sc * .1, -sc * .8))
        hs = T([(-sc * .13, -sc * 3.5), (sc * .13, -sc * 3.5), (sc * .2, -sc * 4.3), (-sc * .08, -sc * 4.2)])
        stand = [[(gx - sc * .9, yF + 2 * S), (gx, gy + sc * .6), (gx + sc * .9, yF + 2 * S)]]
        cv.obj([], 0)
        cv.line(stand)
        cv.obj([T(body)], 1.)
        bp = T(body)
        cv.hair([l for l in C.hatch_poly(bp, 45 + math.degrees(lean), 1.5)])
        cv.hair(C.hatch_poly(bp, -45 + math.degrees(lean), 3))
        guard = T([(x_ * .55 + sc * .12, y_ * .55 + sc * .12) for x_, y_ in body])
        cv.obj([guard], .5)
        cv.hair([q for q in [T([(-sc * .3, sc * .55), (sc * .3, sc * .55)])]])
        cv.obj([neck], .5)
        cv.hair(C.hatch_poly(neck, 90 + math.degrees(lean), 1.5))
        frets = [T([(-sc * .1, -sc * 3.5 + k * sc * .22), (sc * .1, -sc * 3.5 + k * sc * .22)]) for k in range(12)]
        cv.hair(frets)
        cv.obj([hs], .5)
        cv.hair(C.hatch_poly(hs, 0, 1.5))
        for py_ in (-sc * .35, sc * .05):
            black.append(T(_rect(-sc * .26, py_, sc * .26, py_ + sc * .14)))
        black.append(T(_rect(-sc * .3, sc * .5, sc * .3, sc * .6)))
        for k in range(3):
            black.append(T(_oval(sc * .5, sc * .45 + k * sc * .22, sc * .07, sc * .07, n=6)))
    guitar(cx - fw * .21, yF - fh * .06, fh * .07, -.22)

    # --- drum kit, centred behind the mic
    R = fh * .14                                    # kick drum radius
    ky = yF + 3 * S - R
    kx = cx + 3 * S
    # hi-hat (left) and ride cymbal (right) on their stands
    hhx, hhy = kx - R * 1.75, ky - R * 1.15
    rdx, rdy = kx + R * 1.9, ky - R * 1.35
    cv.obj([], 0)
    cv.line([[(hhx, hhy), (hhx, yF + 2 * S)], [(hhx - 4 * S, yF + 2 * S), (hhx, yF - 3 * S), (hhx + 4 * S, yF + 2 * S)]])
    cv.line([[(rdx, rdy), (rdx - 2 * S, yF + 2 * S)], [(rdx - 6 * S, yF + 2 * S), (rdx - 2 * S, yF - 3 * S), (rdx + 3 * S, yF + 2 * S)]])
    # toms
    for tx_, ty_, tr in ((kx - R * .45, ky - R * 1.08, R * .36), (kx + R * .5, ky - R * 1.12, R * .4)):
        body = _rect(tx_ - tr, ty_, tx_ + tr, ty_ + tr * .9) + []
        shell = [(tx_ - tr, ty_)] + _oval(tx_, ty_ + tr * .9, tr, tr * .28, 0, PI, 12)[::-1][::-1][::-1] + [(tx_ + tr, ty_)]
        shell = [(tx_ - tr, ty_), (tx_ + tr, ty_)] + _oval(tx_, ty_ + tr * .9, tr, tr * .28, 0, PI, 14)
        cv.obj([shell], 1.)
        cv.hair([l for l in C.hatch_poly(shell, 90, 1.5) if l[0][0] > tx_ + tr * .25 or l[0][0] < tx_ - tr * .8])
        cv.hair([l for l in C.hatch_poly(shell, 90, 3) if tx_ - tr * .8 <= l[0][0] <= tx_ + tr * .25])
        top = _oval(tx_, ty_, tr, tr * .28, n=24)
        cv.obj([top], 1.)
        cv.hair([_oval(tx_, ty_, tr * .8, tr * .2, PI * .9, PI * 1.9, 10)])
    # floor tom, right
    ftx, fty, ftr = kx + R * 1.35, yF - R * .95, R * .42
    shell = [(ftx - ftr, fty), (ftx + ftr, fty)] + _oval(ftx, fty + R * .85, ftr, ftr * .28, 0, PI, 14)
    cv.obj([shell], 1.)
    cv.hair(C.hatch_poly(shell, 90, 1.5))
    cv.obj([_oval(ftx, fty, ftr, ftr * .28, n=24)], 1.)
    # kick drum: shell ring, lugs, resonant head
    ring = _oval(kx, ky, R, R, n=64)
    cv.obj([ring], 1.5)
    cv.hair([q for q in _rings(kx, ky, R, R, R * .88, R - .8, 1.5)])
    lugs = []
    for i in range(10):
        a = TAU * (i + .5) / 10
        lugs.append([(kx + R * .9 * math.cos(a), ky + R * .9 * math.sin(a)), (kx + R * 1.06 * math.cos(a), ky + R * 1.06 * math.sin(a))])
    cv.heavy(lugs)
    head = _oval(kx, ky, R * .86, R * .86, n=56)
    cv.obj([head], 1.)
    # the head is lit from the left beam: light ruling, darker toward the right edge
    cv.hair(C.hatch_poly(head, 0, 3, .25))
    cv.hair([l for l in C.hatch_poly(head, 0, 3, 1.75) if max(p[0] for p in l) > kx + R * .35])
    cv.hair([_oval(kx, ky, R * .78, R * .78, -PI * .4, PI * .45, 18)])
    if egg:
        # Easter egg: Parker's crossed drumsticks on the kick head
        L = R * .62
        for s_ in (-1, 1):
            st = _stick(kx - s_ * L * .7, ky + L * .7, kx + s_ * L * .7, ky - L * .7, max(1.6, 2.2 * S), max(1, 1.2 * S))
            cv.obj([st], 1.)
    # cymbals, in front of the stands, lathe-turned
    for (yx, yy, yr, two) in ((hhx, hhy, R * .62, True), (rdx, rdy, R * .95, False)):
        for dy in ((0., 1.6 * S) if two else (0.,)):
            cym = _oval(yx, yy + dy, yr, max(1.8, yr * .16), n=36)
            cv.obj([cym], 1.)
            cv.hair([l for l in C.hatch_poly(cym, 0, 1.5) if l[0][1] > yy + dy])
            cv.hair([[(yx - yr * k, yy + dy), (yx + yr * k, yy + dy)] for k in (.55, .3)])
            black.append(_oval(yx, yy + dy - .4 * S, yr * .14, max(1.1, yr * .1), n=10))

    # --- the singer's mic: a vintage chromed capsule on a tall stand, front and centre
    mx, my = cx - fw * .07, fy + fh * .44
    mh, mw = fh * .17, fh * .1
    cv.obj([], 0)
    st = _stick(mx, yL - 1, mx, my + mh * .6, max(1.4, 1.8 * S), max(1.2, 1.4 * S))
    cv.obj([st], 1.)
    base = [(mx - 9 * S, yL + 1), (mx - 1 * S, yL - 6 * S), (mx + 1 * S, yL - 6 * S), (mx + 9 * S, yL + 1)]
    cv.obj([base], 1.)
    cv.hair(C.hatch_poly(base, 0, 1.5))
    yoke = _rect(mx - mw * .62, my + mh * .2, mx + mw * .62, my + mh * .62)
    cv.obj([[(mx - mw * .62, my + mh * .2), (mx - mw * .5, my + mh * .2), (mx - mw * .5, my + mh * .5),
             (mx + mw * .5, my + mh * .5), (mx + mw * .5, my + mh * .2), (mx + mw * .62, my + mh * .2),
             (mx + mw * .62, my + mh * .62), (mx - mw * .62, my + mh * .62)]], 1.)
    cv.hair(C.hatch_poly(yoke, 0, 1.5))
    caps = []
    n = 28
    for i in range(n + 1):          # rounded-shield capsule, wide at the shoulders
        t = i / n
        y_ = my - mh * .5 + mh * t
        wd = mw * .5 * (.55 + .45 * math.sin(PI * min(1, t * 1.25)) ** .5)
        caps.append((mx + wd, y_))
    caps = caps + [(2 * mx - x_, y_) for x_, y_ in caps[::-1]]
    cv.obj([caps], 1.)
    # grille: horizontal chrome bars, black slots between; centre rib, shaded right side
    for y_ in [my - mh * .42 + k * max(1.5, mh * .055) for k in range(30)]:
        if y_ > my + mh * .44:
            break
        cv.line([[(mx - mw * .5, y_), (mx + mw * .5, y_)]])
    cv.obj([_rect(mx - mw * .06, my - mh * .5, mx + mw * .06, my + mh * .5)], .5)
    cv.hair([[(mx - mw * .02, my - mh * .48), (mx - mw * .02, my + mh * .48)]])
    cv.obj([caps[:n + 1] + [(mx + mw * .3, my + mh * .5), (mx + mw * .3, my - mh * .5)]], 0)
    for y_ in [my - mh * .42 + k * max(1.5, mh * .055) for k in range(30)]:
        if y_ > my + mh * .44:
            break
        cv.heavy([[(mx + mw * .3, y_), (mx + mw * .5, y_)]])
    cv.obj([], 0)
    cv.line([caps + [caps[0]]])

    # --- curtains: gathered, tied back, deep folds
    def curtain(side):
        e = fx - 3 if side < 0 else fx + fw + 3
        tie = fy + fh * .52
        wt, wk, wb = fw * .17, fw * .045, fw * .12

        def inner(y_):
            if y_ < tie:
                t = max(0., (y_ - fy) / (tie - fy))
                ww = wt + (wk - wt) * (t ** 1.5)
            else:
                t = min(1., (y_ - tie) / (fy + fh - tie))
                ww = wk + (wb - wk) * (1 - (1 - t) ** 2)
            return e - side * ww
        ys = [fy - 3 + (fh + 6) * i / 60 for i in range(61)]
        poly = [(e, ys[0])] + [(inner(y_), y_) for y_ in ys] + [(e, ys[-1])]
        cv.obj([poly], 1.)
        NF = 7
        lines = []
        for j in range(NF * 5):
            t = (j + .5) / (NF * 5)
            ph = (t * NF) % 1
            if ph < .28:
                continue                     # highlight crest of the fold
            lines.append([(e + (inner(y_) - e) * t, y_) for y_ in ys])
            if ph > .7:
                lines.append([(e + (inner(y_) - e) * (t + .5 / (NF * 5)), y_) for y_ in ys])
        cv.hair(lines)
        # tie-back cord and tassel
        tx_ = inner(tie)
        band = [(e, tie - 2.2 * S), (tx_ - side * 1.5 * S, tie - 2.2 * S), (tx_ - side * 1.5 * S, tie + 2.2 * S), (e, tie + 2.2 * S)]
        cv.obj([band], 1.)
        cv.hair(C.hatch_poly(band, 60 * side, 1.5))
        tas = [(tx_ - side * 1 * S, tie), (tx_ - side * 4 * S, tie + 6 * S), (tx_ + side * 2 * S, tie + 6 * S)]
        cv.obj([tas], 1.)
        cv.hair(C.hatch_poly(tas, 90, 1.5))
    curtain(-1)
    curtain(1)

    # --- valance: swagged, scalloped, fringed, with the spot cans hanging under it
    cv.obj([], 0)
    for u, lit in cans:
        sx = cx + u * fw
        can = [(sx - 3 * S, yV - 1), (sx + 3 * S, yV - 1), (sx + 3.6 * S, yV + 5 * S), (sx - 3.6 * S, yV + 5 * S)]
        cv.obj([can], 1.)
        cv.hair(C.hatch_poly(can, 90, 1.5))
        if lit:
            black.append(_oval(sx, yV + 5 * S, 3.4 * S, 1.2 * S, n=12))
    nsw = 5
    sw = (fw + 6) / nsw
    edge = []
    for i in range(nsw * 16 + 1):
        x_ = fx - 3 + (fw + 6) * i / (nsw * 16)
        t = ((x_ - fx + 3) / sw) % 1
        edge.append((x_, yV - 3 * S + 6 * S * math.sin(PI * t)))
    val = [(fx - 3, fy - 3), (fx + fw + 3, fy - 3)] + edge[::-1]
    cv.obj([val], 1.)
    sw_lines = []
    for k in range(1, 6):
        q = []
        for x_, y_ in edge:
            t = ((x_ - fx + 3) / sw) % 1
            q.append((x_, y_ - k * 1.6 * S * (.4 + .6 * math.sin(PI * t))))
        sw_lines.append(q)
    cv.hair(sw_lines)
    cv.hair([l for l in C.hatch_poly(val, 0, 1.5) if l[0][1] < yV - 7 * S])
    cv.hair([[(x_, y_), (x_, y_ + 2.4 * S)] for x_, y_ in edge[::2]])
    o.append(cv.svg())

    # --- the crowd in silhouette, hands up, and the taper's stand rising out of it
    crowd_y = yL + fh * .045
    rimw = []
    hd = []
    for row, (dy, rs) in enumerate(((0., 1.), (5.5, 1.15))):
        xx = fx - 4 + rng.uniform(0, 6) * S
        while xx < fx + fw + 6:
            r = rng.uniform(3.2, 4.4) * S * rs
            yy = crowd_y + dy * S + rng.uniform(-1.5, 2.5) * S
            hd.append(_oval(xx, yy, r * .82, r, n=14))
            hd.append(_oval(xx, yy + r * 2.0, r * 2.0, r * 1.25, n=18))
            if row == 0:
                rimw.append(_oval(xx - r * .1, yy - r * .1, r * .62, r * .82, PI * 1.05, PI * 1.6, 6))
                if rng.random() < .3:
                    side = rng.choice((-1, 1))
                    ax_ = xx + side * r * 1.4
                    hand_y = yy - rng.uniform(8, 13) * S
                    hd.append(_stick(ax_, yy + r * 1.2, ax_ + side * 2 * S, hand_y, 2.2 * S, 1.6 * S))
                    hd.append(_oval(ax_ + side * 2 * S, hand_y - .8 * S, 1.4 * S, 1.8 * S, n=8))
                    rimw.append([(ax_ - 1.0 * S, yy), (ax_ + side * 2 * S - 1.0 * S, hand_y + 1 * S)])
            xx += r * rng.uniform(1.8, 2.5)
    hd.append(_rect(fx - 4, crowd_y + 9 * S, fx + fw + 4, fy + fh + 4))
    tx_ = cx + fw * .235
    top_ = fy + fh * .36
    hd.append(_rect(tx_ - .8, top_, tx_ + .8, crowd_y + 4 * S))
    hd.append(_rect(tx_ - 11 * S, top_ - .8, tx_ + 11 * S, top_ + .8))
    for s_ in (-1, 1):   # a pair of pencil condensers in ORTF, the taper's signature
        hd.append(_stick(tx_ + s_ * 10 * S, top_ + 1, tx_ + s_ * 4 * S, top_ - 12 * S, 2.6 * S, 2.2 * S))
        hd.append(_rect(tx_ + s_ * 10 * S - 1.2 * S, top_ - 2, tx_ + s_ * 10 * S + 1.2 * S, top_ + 2))
    o.append(f'<path d="{_blk(black)}{_blk(hd)}" fill="#000" stroke="none"/>')
    # rim light from the stage on the front row; the dark house behind them ruled, never solid
    o.append(f'<path d="{"".join(_d(p, False, .2) for p in rimw)}" stroke="#fff" stroke-width=".5" fill="none"/>')
    floor_d = _rect(fx - 4, crowd_y + 14 * S, fx + fw + 4, fy + fh + 4)
    o.append(f'<path d="{C.hatch_d(floor_d, 0, 3, 1.25)}" stroke="#fff" stroke-width=".5"{CR}/>')
    # the room behind them is not empty paper: rim light on shoulders
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# a reel of tape (short plates' medallion)
# ------------------------------------------------------------------------------------------------

def reel_medallion(cx, cy, rx, ry, seed=0):
    o = []
    outer = _oval(cx, cy, rx + 1, ry + 1, n=64)
    o.append(f'<path d="{_d(outer, True, 0)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_d(outer, True, 0)}{_d(_oval(cx, cy, rx - 2, ry - 2, n=64)[::-1], True, 0)}" fill="#000" fill-rule="evenodd"/>')
    r = ry - 3.5
    # the wound tape pack behind the flange: tight concentric turns
    pack = _rings(cx, cy, r, r, r * .35, r, 1.5, n=48)
    o.append(f'<path d="{"".join(_d(p, True, .2) for p in pack)}" stroke="#000" stroke-width=".5" fill="none"/>')
    # the flange outside the reel, out to the oval edge: light ruling
    if rx - 2 > r + 2:
        ring = _d(_oval(cx, cy, rx - 2, ry - 2, n=64), True, 0) + _d(_oval(cx, cy, r, r, n=48)[::-1], True, 0)
        o.append(f'<path d="{ring}" fill="{C.pat("M")}" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(_oval(cx, cy, r, r, n=48), True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    # three spokes of the reel flange
    cv = C.Canvas()
    rot = (seed % 12) * TAU / 36
    for k in range(3):
        a = rot + TAU * k / 3
        sp = []
        for i in range(9):
            t = a - .32 + .64 * i / 8
            sp.append((cx + r * .96 * math.cos(t), cy + r * .96 * math.sin(t)))
        for i in range(9):
            t = a + .6 - 1.2 * i / 8
            sp.append((cx + r * .36 * math.cos(t), cy + r * .36 * math.sin(t)))
        cv.obj([sp], 1.)
        cv.hair(C.hatch_poly(sp, 0, 3, .25))
        cv.hair([l for l in C.hatch_poly(sp, 0, 3, 1.75)
                 if math.cos(math.atan2(l[0][1] - cy, l[0][0] - cx) - a - .25) < .97])
    rim_o, rim_i = _oval(cx, cy, r, r, n=56), _oval(cx, cy, r * .93, r * .93, n=56)
    cv.obj([], 0)
    cv.line([rim_o + [rim_o[0]], rim_i + [rim_i[0]]])
    hub = _oval(cx, cy, r * .36, r * .36, n=32)
    cv.obj([hub], 1.)
    cv.hair(_rings(cx, cy, r * .36, r * .36, r * .22, r * .34, 1.5, n=24))
    cv.obj([_oval(cx, cy, r * .22, r * .22, n=24)], .5)
    cv.hair(C.hatch_poly(_oval(cx, cy, r * .22, r * .22, n=24), 0, 3, .25))
    o.append(cv.svg())
    # Easter egg: crossed drumsticks on the hub label
    L = r * .2
    st = [_stick(cx - L, cy + L, cx + L, cy - L, 1.4, .9), _stick(cx + L, cy + L, cx - L, cy - L, 1.4, .9)]
    o.append(f'<path d="{_blk(st)}" fill="#000"/>')
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
    gap = min(gh * 1.25, 100)
    o.append(C._clip(C._uid("b6", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .85, r_scale=1.15 * max(1., 62. / gh))))
    o.append(reel_medallion(w / 2, top + gh / 2, gap / 2, gh / 2 - 1, seed))
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
    cw = min(w * .46, gh * 1.75)
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
    o.append(C._clip(C._uid("m6", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_box(cx, cy, cw, gh + 4)
    o.append(_field_clip(C._uid("mv6", w, h, seed), inner, stage(fx, fy, fw, fh, seed, egg=True)))
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
    cw, ch = pw * .6, ph * .72
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
    r1 = min(pw * .16, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .45)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .45)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .035), rmax=r1 * .9,
                   max_n=13, edge=.5, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t6", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_box(cx, cy, cw, ch)
    o.append(_field_clip(C._uid("tv6", w, h, seed), inner, stage(fx, fy, fw, fh, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 60), True, rng.randrange(1 << 20)))
    bh = min(17, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .48, cw * 1.3, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(f'<path d="{_pl_d(letter_arc("LIVE FROM PORTLAND", centre, bh * .48, 2.0))}" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    words = "LIVE MUSIC ARCHIVE * TAPED IN PORTLAND"
    size = min(th * .56, 10)
    ww = _word_w(words, 2.2) * size / 6
    if ww > tw - 14:
        words = "LIVE MUSIC ARCHIVE"
        ww = _word_w(words, 2.2) * size / 6
    o.append(f'<path d="{_d(_rect(tx + 2.5, ty + 2.5, tx + tw - 1, ty + th - 1), True, 0)}" fill="{C.pat("L")}" stroke="none"/>')
    o.append(f'<path d="{_d(_rect(tx + tw / 2 - ww / 2 - 4, ty + 2.5, tx + tw / 2 + ww / 2 + 4, ty + th - 1), True, 0)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_pl_d(letter_line(words, tx + tw / 2 + .5, ty + th / 2 + .8, size, 2.2))}" stroke="#000" stroke-width="1"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f6", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.25, r_scale=1.15, n=2)))
        o.append(reel_medallion(w / 2, fy + fh / 2 - 1, fh * .62, fh / 2 - 2, seed))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 6
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
