"""garden-06 (Mushroom forecast) plate.

Today's mushroom is the matsutake: white, a thick shaggy ring on the stem, in sandy soil under
lodgepole pine in the Cascades, with two weeks of rain on the way; golden chanterelles do well too.
The vignette: a mature matsutake and its buttons pushing out of cracked sand under two lodgepole
pines, a golden chanterelle beside them, Mt. Hood behind a band of rain clouds. The crest is a
matsutake rising out of an acanthus calyx, the banner reads MATSUTAKE, the pedestal tablet reads
PRO AMORE FUNGORUM. Easter egg: Parker's dog has left a paw print in the sand by the mushrooms.
"""
import sys
import math
import random
import engraving_codex as C

PI, TAU = math.pi, 2 * math.pi
_n, _d, _E = C._n, C._d, C._ell_pts
CR = ' shape-rendering="crispEdges"'


# ----------------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------------

def ell(cx, cy, rx, ry, n=40):
    return _E(cx, cy, rx, ry, n)[:-1]


def scale_about(poly, ox, oy, k):
    return [(ox + (x - ox) * k, oy + (y - oy) * k) for x, y in poly]


def bezq(p0, p1, p2, n=12):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


# ----------------------------------------------------------------------------------------------
# path lettering (no <text>)
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GL = {
    "A": (.72, [[(0, 1), (.36, 0), (.72, 1)], [(.15, .64), (.57, .64)]]),
    "C": (.68, [_arc(.36, .5, .34, .5, -40, -320, 14)]),
    "E": (.56, [[(.56, 0), (0, 0), (0, 1), (.56, 1)], [(0, .5), (.44, .5)]]),
    "F": (.54, [[(.54, 0), (0, 0), (0, 1)], [(0, .5), (.42, .5)]]),
    "G": (.72, [_arc(.37, .5, .35, .5, -40, -320, 14) + [(.72, .58), (.42, .58)]]),
    "K": (.64, [[(0, 0), (0, 1)], [(.62, 0), (0, .62)], [(.2, .44), (.64, 1)]]),
    "M": (.84, [[(0, 1), (0, 0), (.42, .72), (.84, 0), (.84, 1)]]),
    "N": (.7, [[(0, 1), (0, 0), (.7, 1), (.7, 0)]]),
    "O": (.78, [_arc(.39, .5, .39, .5, 0, 360, 18)]),
    "P": (.6, [[(0, 1), (0, 0), (.36, 0)] + _arc(.34, .27, .26, .27, -90, 90, 8) + [(0, .54)]]),
    "R": (.64, [[(0, 1), (0, 0), (.36, 0)] + _arc(.34, .27, .26, .27, -90, 90, 8) + [(0, .54)], [(.3, .54), (.64, 1)]]),
    "S": (.62, [[(.6, .14), (.48, .03), (.3, 0), (.12, .05), (.04, .2), (.12, .38), (.32, .48), (.52, .58), (.62, .76),
                 (.56, .93), (.38, 1), (.18, .98), (.02, .86)]]),
    "T": (.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "U": (.68, [[(0, 0), (0, .68)] + _arc(.34, .66, .34, .34, 180, 0, 10)[1:] + [(.68, 0)]]),
    " ": (.4, []),
}


def lettering(text, x, y, size, ycurve=None, track=.28):
    """Polylines for text with cap height `size`, left at x, cap top at y (+ ycurve(x))."""
    out = []
    cx = x
    for ch in text:
        adv, strokes = GL[ch]
        dy = ycurve(cx + adv * size / 2) if ycurve else 0
        for s in strokes:
            out.append([(cx + px * size, y + dy + py * size) for px, py in s])
        cx += (adv + track) * size
    return out, cx - x - track * size


def text_width(text, size, track=.28):
    return sum((GL[c][0] + track) * size for c in text) - track * size


def pd(pls, tol=.1):
    return "".join(_d(p, tol=tol) for p in pls if len(p) > 1)


# ----------------------------------------------------------------------------------------------
# the subject: mushrooms and their forest
# ----------------------------------------------------------------------------------------------

def matsutake(cv, cx, gy, R, rng, stage=1.):
    """A matsutake standing on ground line gy, cap radius R. stage 1 mature (domed cap, gills
    showing under an in-rolled lip), stage < .5 a button (round cap clamped to the stem)."""
    mature = stage > .5
    hw = R * (.25 if mature else .32)
    sh = R * (1.15 if mature else .35)
    yt = gy - sh
    lean = R * .06 * rng.uniform(-1, 1)
    Hc = R * (.68 if mature else .9)
    e = R * .17

    def sx(u, v):  # u 0 base .. 1 top, v -1..1 across
        w = hw * (1.08 - .12 * u + .12 * math.sin(PI * min(1, u * 1.6)) * (1 - u))
        return cx + lean * u + v * w, gy + 2 - (sh + 2 + e) * u
    left = [sx(i / 16, -1) for i in range(17)]
    right = [sx(i / 16, 1) for i in range(17)]
    cv.obj([left + right[::-1]], 1.)
    for v in (-.55, -.15, .2, .45, .62, .76, .86, .94):
        cv.hair([sx(i / 14, v) for i in range(15)])
    cv.heavy([sx(i / 14, .98) for i in range(15)])
    for k in range(int(sh / 3.2)):
        u = rng.uniform(.05, .7)
        v = rng.uniform(-.7, .6)
        px, py = sx(u, v)
        s = R * .05
        cv.hair([(px - s, py - s * .7), (px, py), (px + s * .9, py - s * .6)])
    if mature:
        ru0, ru1 = .62, .86
        top = [sx(ru1, -1.25 + 2.5 * i / 10) for i in range(11)]
        bot = []
        for i in range(13):
            v = 1 - 2 * i / 12
            x, y = sx(ru0, v * 1.3)
            bot.append((x, y + (2.2 if i % 2 else -.6) * R / 40))
        cv.obj([top + bot], 1.)
        for i in range(1, 12):
            v = -1.2 + 2.4 * i / 12
            a, b = sx(ru1 - .02, v), sx(ru0 + .02, v * 1.05)
            (cv.line if v > .55 else cv.hair)([a, b])
        cv.heavy([(x, y + .8) for x, y in bot[:7]])
    ccx = cx + lean
    if mature:
        disk = ell(ccx, yt, R * .9, e, 48)
        cv.obj([disk], 1.)
        n = int(PI * R * .9 / 1.6)
        for i in range(1, n):
            th = PI * i / n
            p = (ccx + R * .9 * math.cos(th), yt + e * math.sin(th))
            q = (ccx + hw * .9 * math.cos(th), yt - e * .1)
            cv.hair([q, p])
        cv.line([(ccx + R * .9 * math.cos(PI * i / 20), yt + e * .35 * math.sin(PI * i / 20)) for i in range(21)])
    prof = [(ccx + R * t, yt - Hc * (1 - t * t) ** .55) for t in [-1 + 2 * i / 40 for i in range(41)]]
    lipy = e * (.35 if mature else .9)
    lip = [(ccx + R * math.cos(th), yt + lipy * math.sin(th)) for th in [PI * i / 24 for i in range(25)]]
    dome = prof + lip[1:-1]
    cv.obj([dome], 1.)
    ox, oy = ccx - R * .32, yt - Hc * .72
    k = .9
    while k > .18:
        ring = scale_about(dome, ox, oy, k)
        cv.hair(ring + [ring[0]])
        k -= .085 if k > .5 else .11
    rside = [p for p in prof if p[0] > ccx + R * .05] + [p for p in lip[1:-1] if p[0] > ccx + R * .05]
    if len(rside) > 3:
        cv.hair(C.hatch_poly(rside, 45, 3., .3))
        low = [p for p in rside if p[1] > yt - Hc * .45]
        if len(low) > 3:
            cv.hair(C.hatch_poly(low, -45, 3., 1.2))
    cv.heavy(lip)
    cv.hair([(x, y - 1.6) for x, y in lip[2:-2]])
    for j in range(3):
        cv.line([(ccx + (R - .3 - j * .8) * math.cos(th), yt + lipy * math.sin(th) - .2 - j * .7)
                 for th in [PI * i / 24 for i in range(0, 9)]])
    for k in range(int(R * 1.6)):
        t = rng.uniform(-.82, .82)
        f = rng.uniform(.2, .8) ** .8
        px = ccx + R * t * .96
        py = yt - Hc * f * (1 - t * t) ** .55
        s = R * (.035 + .05 * f)
        ang = math.atan2(py - (yt + R * .6), px - ccx)
        ux, uy = math.cos(ang), math.sin(ang)
        a = (px + ux * s - uy * s * .7, py + uy * s + ux * s * .7)
        b = (px + ux * s + uy * s * .7, py + uy * s - ux * s * .7)
        (cv.line if f > .75 and rng.random() < .5 else cv.hair)([a, (px, py), b])
    return (ccx, yt - Hc)


def chanterelle(cv, cx, gy, s, rng):
    """A golden chanterelle: a trumpet with a wavy rim and forked false gills running down the
    stem; its top a shallow funnel."""
    yr = gy - s * 1.25
    ry = s * .28
    ph = rng.uniform(0, TAU)

    def rim(th):
        w = 1 + .07 * math.sin(5 * th + ph) + .04 * math.sin(9 * th + ph * 2)
        return (cx + s * w * math.cos(th), yr + ry * w * math.sin(th) + s * .04 * math.sin(4 * th + ph))
    lb = bezq(rim(PI), (cx - s * .2, yr + s * .25), (cx - s * .17, gy + 1), 14)
    rb = bezq(rim(0), (cx + s * .2, yr + s * .25), (cx + s * .17, gy + 1), 14)
    front = [rim(PI * i / 30) for i in range(31)]
    body = front + lb[1:] + rb[::-1][:-1]
    cv.obj([body], 1.)
    for i in range(1, 15):
        th = PI * i / 15
        p0 = rim(th)
        tgt = (cx + (p0[0] - cx) * .18, gy - s * .35)
        mid = (cx + (p0[0] - cx) * .45, yr + s * .4)
        curve = bezq(p0, mid, tgt, 10)
        (cv.line if p0[0] > cx + s * .45 else cv.hair)(curve)
        if i % 2 and .3 < th < PI - .3:
            q0 = rim(th + PI / 30)
            cv.hair(bezq(q0, ((q0[0] + mid[0]) / 2, (q0[1] + mid[1]) / 2 + 2), curve[4], 6))
    cv.heavy(rb)
    top = [rim(TAU * i / 48) for i in range(48)]
    cv.obj([top], 1.)
    for k in (.86, .7, .54, .38, .22):
        ring = [(cx + (x - cx) * k, yr + s * .05 * (1 - k) + (y - yr) * k) for x, y in top]
        cv.hair(ring + [ring[0]])
    inner = [(cx + (x - cx) * .9, yr + (y - yr) * .9) for x, y in top if y < yr + ry * .2]
    if len(inner) > 3:
        cv.hair(C.hatch_poly(inner, 0, 1.5, .25))
    cv.heavy(front)


def pine_trunk(cv, x, y0, y1, w0, w1, rng):
    """A lodgepole pine trunk in platy bark, lit from the left."""
    cv.obj([[(x - w1 / 2, y0), (x - w0 / 2, y1), (x + w0 / 2, y1), (x + w1 / 2, y0)]], 1.)
    H = y1 - y0

    def at(u, v):
        w = w1 + (w0 - w1) * u
        return (x + v * w / 2, y0 + H * u)
    for v in (-.6, -.2, .25, .5, .68, .82, .92):
        cv.hair([at(u / 20, v + .03 * math.sin(u * 1.7)) for u in range(21)])
    for d in (.97, .88):
        cv.line([at(u / 20, d) for u in range(21)])
    yy = y0 + 3
    while yy < y1 - 2:
        u = (yy - y0) / H
        a, b = rng.uniform(-.9, -.2), rng.uniform(.1, .8)
        cv.hair([at(u, a), at(u + 1 / H, b)])
        yy += rng.uniform(3, 6)


def fir(cv, x, y0, y1, wmax, rng):
    """A true fir: a straight dark trunk carrying tiers of drooping boughs, each bough shaded dark
    beneath with a needle fringe, lit along its top; upper tiers lap over lower ones."""
    H = y1 - y0
    cv.obj([[(x - 1.5, y0 + H * .05), (x - 2.5, y1), (x + 2.5, y1), (x + 1.5, y0 + H * .05)]], 1.)
    cv.line(C.hatch_poly([(x - 1.5, y0), (x - 2.5, y1), (x + 2.5, y1), (x + 1.5, y0)], 90, 1.5))
    n = max(4, int(H / 13))
    for k in range(n):
        f = k / (n - 1)                      # 0 bottom .. 1 top
        yk = y1 - H * .12 - (H * .86) * f
        wk = wmax * (1 - f) ** .9 * .5 + 3
        dk = min(16., H * .09) * (1.1 - .5 * f)
        for side in (-1, 1):
            tip = (x + side * wk, yk + dk * .9)
            topc = bezq((x, yk - dk * .25), (x + side * wk * .55, yk - dk * .2), tip, 10)
            m = max(4, int(wk / 3))
            fringe = []
            for i in range(m + 1):
                t = i / m
                bx = x + side * wk * (1 - t)
                by = yk + dk * .9 * (1 - t) + dk * .55 * math.sin(PI * t) ** .5
                fringe.append((bx, by + (2.2 if i % 2 else 0)))
            poly = topc + fringe[1:]
            cv.obj([poly], 1.)
            cv.hair(C.hatch_poly(poly, 0, 1.5, .25))
            cv.line(C.hatch_poly([p for p in poly if p[1] > yk + dk * .25] or poly, 0, 2., 0))
            for i in range(1, m, 1):
                t = i / m
                p0 = (x + side * wk * (1 - t) * .95, yk + dk * .9 * (1 - t) - dk * .15)
                cv.hair([p0, (p0[0] - side * 2, p0[1] + dk * .45)])
            cv.heavy(fringe)
    cv.obj([[(x - 1.2, y0 - 2), (x, y0 - 8), (x + 1.2, y0 - 2), (x, y0 + 6)]], 1.)


def needle_tuft(cv, x, y, ang, L, n=9):
    for i in range(n):
        a = ang + (i - (n - 1) / 2) * .17
        cv.hair([(x, y), (x + L * math.cos(a), y + L * math.sin(a))])


def branch(cv, x, y, ang, L, rng, droop=.25):
    pts = bezq((x, y), (x + L * .5 * math.cos(ang), y + L * .5 * math.sin(ang) - L * .1),
               (x + L * math.cos(ang + droop), y + L * math.sin(ang + droop)), 10)
    cv.line(pts)
    for i in range(3, 11, 2):
        px, py = pts[i]
        for sgn in (-1, 1):
            needle_tuft(cv, px, py, ang + droop * i / 10 + sgn * .9 - PI / 2 * .3, L * .16, 7)
    needle_tuft(cv, pts[-1][0], pts[-1][1], ang + droop, L * .22, 11)


def cloud(cv, x0, x1, base, h, rng):
    n = max(3, int((x1 - x0) / (h * .55)))
    cs = [(x0 + (x1 - x0) * (i + .5) / n + rng.uniform(-3, 3), h * rng.uniform(.4, .95)) for i in range(n)]
    cs = [(c, min(r, (c - x0) * .9, (x1 - c) * .9)) for c, r in cs]

    def top(x):
        m = 0
        for c, r in cs:
            if abs(x - c) < r:
                m = max(m, math.sqrt(r * r - (x - c) ** 2))
        return base - m
    k = int(x1 - x0)
    pts = [(x0 + (x1 - x0) * i / k, top(x0 + (x1 - x0) * i / k)) for i in range(k + 1)]
    poly = pts + [(x, base + 2 - 3 * abs(math.sin(x * .09))) for x in [x1 - (x1 - x0) * i / 30 for i in range(31)]]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly([(x, max(y, base - h * .35)) for x, y in pts] + [(x1, base + 2), (x0, base + 2)], 0, 1.5, .25))
    lowb = [(x, base + 2 - 3 * abs(math.sin(x * .09))) for x in [x0 + (x1 - x0) * i / 30 for i in range(31)]]
    cv.line(C.hatch_poly([(x, max(y, base - h * .1)) for x, y in pts] + lowb[::-1], 0, 2., 0))
    for c, r in cs:
        for f in (.82, .64):
            cv.hair(_E(c + r * .1, base - r * .1, r * f, r * f * .9, 14, PI * 1.2, PI * 2.05))
    return poly


def paw_print(cv, x, y, s):
    """Parker's dog was here: one paw pressed into the sand."""
    pad = [(x - s * .55, y + s * .35), (x - s * .3, y - s * .1), (x, y - s * .25), (x + s * .3, y - s * .1),
           (x + s * .55, y + s * .35), (x + s * .3, y + s * .55), (x, y + s * .45), (x - s * .3, y + s * .55)]
    toes = [ell(x + dx * s, y + dy * s, s * .2, s * .26, 12) for dx, dy in ((-.62, -.55), (-.22, -.9), (.22, -.9), (.62, -.55))]
    for p in [pad] + toes:
        cv.obj([p], 1.)
        cv.line(C.hatch_poly(p, 0, 1.5, .25))


def pine_cone(cv, x, y, s, ang=-.3):
    ca, sa = math.cos(ang), math.sin(ang)
    poly = [(x + ca * px - sa * py, y + sa * px + ca * py) for px, py in ell(0, 0, s, s * .5, 24)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 45 + math.degrees(ang), 2.))
    cv.hair(C.hatch_poly(poly, -45 + math.degrees(ang), 2.5))
    for i in range(-3, 4):
        px = i * s * .26
        cv.line([(x + ca * (px - s * .1) - sa * s * .45, y + sa * (px - s * .1) + ca * s * .45),
                 (x + ca * (px + s * .1) - sa * s * .45, y + sa * (px + s * .1) + ca * s * .45)])


def ridge_y(ridge, x):
    for (ax, ay), (bx, by) in zip(ridge, ridge[1:]):
        if ax <= x <= bx:
            return ay + (by - ay) * (x - ax) / ((bx - ax) or 1)
    return ridge[-1][1]


def scene(X, Y, W, H, seed, detail=1.):
    """The vignette into the box (X, Y, W, H): an SVG fragment (the caller clips it)."""
    rng = random.Random(seed)
    o = [C.dark_ground((X - 2, Y - 2, W + 4, H + 4), "L")]
    yh = Y + H * .56
    back = C.Canvas()
    back.obj([], 0)
    for (a, b, cb) in ((X - 4, X + W * .46, Y + H * .26), (X + W * .7, X + W + 4, Y + H * .2)):
        xx = a
        while xx < b:
            yy = cb + rng.uniform(0, 6)
            while yy < yh:
                ln = rng.uniform(5, 10)
                back.hair([(xx + (yy - cb) * .27, yy), (xx + (yy + ln - cb) * .27, yy + ln)])
                yy += ln + rng.uniform(3, 7)
            xx += 3
    # Mt. Hood
    px, py = X + W * .6, Y + H * .16
    mL, mR = X + W * .12, X + W * 1.05
    ridge = [(mL, yh), (X + W * .3, yh - H * .1), (X + W * .42, yh - H * .2), (X + W * .5, py + H * .14),
             (X + W * .56, py + H * .03), (px, py), (X + W * .63, py + H * .04), (X + W * .7, py + H * .13),
             (X + W * .8, yh - H * .2), (X + W * .92, yh - H * .1), (mR, yh)]
    mtn = ridge + [(mR, yh + 6), (mL, yh + 6)]
    back.obj([mtn], 1.)
    back.hair(C.hatch_poly(mtn, 0, 2., .25))
    back.hair(C.hatch_poly([p for p in mtn if p[0] >= px - 1] + [(px, yh + 6)], 45, 3.))
    snowline = []
    for i in range(15):
        t = i / 14
        x = X + W * (.47 + .26 * t)
        cy = py + H * (.17 + .12 * math.sin(PI * t) ** .5) * (1 - abs(t - .5) * .7)
        ry_ = ridge_y(ridge, x)
        snowline.append((x, max(cy + (H * .05 if i % 2 else 0), ry_ + 1.5)))
    top = [p for p in ridge if snowline[0][0] <= p[0] <= snowline[-1][0]]
    snow = top + snowline[::-1]
    back.obj([snow], .5)
    back.hair(C.hatch_poly([p for p in snow if p[0] >= px - .5] + [(px, snowline[7][1])], 45, 2.))
    for i in range(15):
        bx, by = snowline[i]
        sxp = px + (bx - px) * .45
        syp = py + abs(sxp - px) * (H * .14) / (W * .06) * .55 + 1.5
        if syp < by - 3:
            g = bezq((sxp, syp), ((sxp + bx) / 2 + (1.5 if i % 2 else -1.5), (syp + by) / 2), (bx, by), 8)
            (back.line if bx > px and i % 2 else back.hair)(g)
    cloud(back, X - 6, X + W * .46, Y + H * .26, H * .2, rng)
    cloud(back, X + W * .7, X + W + 6, Y + H * .2, H * .17, rng)
    fx = X - 4
    fpts = [(X - 4, yh + H * .07)]
    while fx < X + W + 4:
        hh = H * rng.uniform(.05, .11)
        fpts += [(fx, yh + H * .02), (fx + 2.5, yh + H * .02 - hh), (fx + 5, yh + H * .02)]
        fx += rng.uniform(4, 7)
    fpts.append((X + W + 4, yh + H * .07))
    back.obj([fpts], .5)
    back.line(C.hatch_poly(fpts, 0, 2., 0))
    o.append(back.svg())
    # sandy soil: stipple
    gy0 = yh + H * .06
    soil = [(X - 4 + (W + 8) * i / 30, gy0 + H * .025 * math.sin(i * .9 + seed)) for i in range(31)]
    soil += [(X + W + 4, Y + H + 4), (X - 4, Y + H + 4)]
    o.append(f'<path d="{_d(soil, True, 0)}" fill="{C.pat("S")}" stroke="none"/>')
    fr = C.Canvas()
    fr.obj([], 0)
    fr.line(soil[:31])
    for i in range(int(18 * detail)):
        sx_, sy_ = rng.uniform(X, X + W), rng.uniform(gy0 + 4, Y + H)
        ln = rng.uniform(6, 16)
        fr.hair(bezq((sx_, sy_), (sx_ + ln / 2, sy_ - 1.5), (sx_ + ln, sy_), 6))
    for i in range(int(16 * detail)):
        sx_, sy_ = rng.uniform(X, X + W), rng.uniform(gy0 + 6, Y + H)
        a = rng.uniform(-.6, .6)
        ln = rng.uniform(6, 11)
        for dd in (-1, 1):
            fr.line([(sx_, sy_), (sx_ + ln * math.cos(a + dd * .12), sy_ + ln * math.sin(a + dd * .12))])
    R1 = min(W * .21, H * .28)
    gm = Y + H * .88
    fir(fr, X + W * .07, Y + H * .02, gy0 + H * .05, W * .3, rng)
    fir(fr, X + W * .95, Y + H * .1, gy0 + H * .04, W * .24, rng)
    for (sx_, sw_) in ((X + W * .42 + R1 * .5, R1 * .8), (X + W * .63 + R1 * .35, R1 * .55)):
        shp = ell(sx_, gm + 1, sw_, R1 * .1, 24)
        fr.obj([shp], 0)
        fr.line(C.hatch_poly(shp, 0, 2., 0))
    pine_cone(fr, X + W * .34, Y + H * .955, W * .04)
    paw_print(fr, X + W * .6, Y + H * .94, W * .036)
    chanterelle(fr, X + W * .8, Y + H * .86, R1 * .48, rng)
    matsutake(fr, X + W * .24, Y + H * .9, R1 * .42, rng, .3)
    matsutake(fr, X + W * .63, gm - 3, R1 * .7, rng, 1.)
    matsutake(fr, X + W * .42, gm, R1, rng, 1.)
    bx, by = X + W * .24, Y + H * .9
    for a in (.2, .9, 2.4, 3.0):
        fr.line([(bx + R1 * .42 * math.cos(a), by + 1 + R1 * .1 * math.sin(a)),
                 (bx + R1 * .7 * math.cos(a), by + 2 + R1 * .18 * math.sin(a))])
    o.append(fr.svg())
    return "".join(o)


def small_scene(X, Y, W, H, seed):
    """For the band's medallion: a matsutake and a chanterelle on sand, rain behind."""
    rng = random.Random(seed)
    o = [C.dark_ground((X - 2, Y - 2, W + 4, H + 4), "L")]
    gy = Y + H * .72
    o.append(f'<path d="M{_n(X - 2)},{_n(gy)}h{_n(W + 4)}v{_n(H)}h{_n(-W - 4)}z" fill="{C.pat("S")}" stroke="none"/>')
    cv = C.Canvas()
    cv.obj([], 0)
    for xx in range(int(X), int(X + W), 3):
        cv.hair([(xx, Y), (xx + 3, Y + H * .3)])
    R = min(W * .2, H * .34)
    chanterelle(cv, X + W * .72, gy + 2, R * .55, rng)
    matsutake(cv, X + W * .4, gy + 2, R, rng, 1.)
    o.append(cv.svg())
    return "".join(o)


def crest(cx, cy, size, seed):
    """A matsutake rising from an acanthus calyx."""
    cv = C.Canvas()
    rng = random.Random(seed)
    base = -PI / 2
    n = 2
    for j in range(n, 0, -1):
        for side in (-1, 1):
            sp = j / (n + .4)
            a = base + side * sp * 1.35
            ln = size * (1.0 - .25 * sp) * rng.uniform(.95, 1.03)
            b = side * (.5 + .6 * sp)
            C._finger(cv, cx + side * size * .05, cy, a, ln, ln * .12, b, b * 5.5)
    matsutake(cv, cx, cy - size * .1, size * .46, rng, 1.)
    r = size * .13
    cv.obj([ell(cx, cy, r * 1.6, r, 28)], 1.)
    cv.hair(C.hatch_poly(ell(cx, cy + r * .3, r * 1.4, r * .55, 20), 0, 1.5))
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex, every surface engraved)
# ----------------------------------------------------------------------------------------------

def field_of(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return (cx - a, cy - b, 2 * a, 2 * b)


def clip_d(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def banner(cx, cy, w, h, seed, text="MATSUTAKE", arch=.04):
    bsvg, centre = C.ribbon_banner(cx, cy, w, h, arch, seed)
    size = h * .52
    tw = text_width(text, size)
    if tw > w * .62:
        size *= w * .62 / tw
        tw = text_width(text, size)

    def yc(x):
        return min(centre, key=lambda p: abs(p[0] - x))[1] - cy
    pls, _ = lettering(text, cx - tw / 2, cy - size / 2, size, yc)
    return bsvg + f'<path d="{pd(pls)}" stroke="#000" stroke-width="1" fill="none"/>'


def tablet_fill(tx, ty, tw, th, text="PRO AMORE FUNGORUM"):
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z" fill="{C.pat("L")}" stroke="none"/>']
    size = min(th * .56, 9.)
    if size >= 4:
        t = text_width(text, size, .34)
        pls, _ = lettering(text, tx + (tw - t) / 2, ty + (th - size) / 2 + .5, size, None, .34)
        o.append(f'<path d="M{_n(tx + (tw - t) / 2 - 4)},{_n(ty + (th - size) / 2 - 1)}h{_n(t + 8)}v{_n(size + 3)}h{_n(-t - 8)}z" fill="#fff" stroke="none"/>')
        o.append(f'<path d="{pd(pls)}" stroke="#000" stroke-width="1" fill="none"/>')
        for sx in (-1, 1):
            x0 = tx + tw / 2 + sx * (t / 2 + 10)
            x1 = tx + tw / 2 + sx * (tw / 2 - 6)
            ym = ty + th / 2
            o.append(f'<path d="M{_n(x0)},{_n(ym)}L{_n(x1)},{_n(ym)}" stroke="#000" stroke-width="1"/>')
            for xd in (x0, x1):
                o.append(f'<path d="{_d(ell(xd, ym, 1.5, 1.5, 8), True, 0)}" fill="#000"/>')
    return "".join(o)


def layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.bead_moulding(0, 3, w, 1.5))
    o.append(C.dark_ground((0, 6.5, w, py0), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .035), rmax=r1 * .9,
                   max_n=int(14 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("gt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = field_of(cx, cy, cw, ch)
    o.append(clip_d(C._uid("gv", w, h, seed), field, scene(fx, fy, fw, fh, seed)))
    o.append(crest(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), rng.randrange(1 << 20)))
    o.append(banner(cx, cy + ch * .47, cw * 1.4, min(17, ph * .055), rng.randrange(1 << 20)))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, ped_h), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(tablet_fill(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh), "L"))
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("gf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
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
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .07), rmax=r * .8,
                   max_n=int(10 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("gm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = field_of(cx, cy, cw, gh + 4)
    o.append(clip_d(C._uid("gmv", w, h, seed), field,
                    scene(fx, fy, fw, fh, seed, .6) if fh > 70 else small_scene(fx, fy, fw, fh, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("gb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    inner = _d(ell(cx, cy, rx - 4.5, ry - 4.5, 64), True, 0)
    o.append(clip_d(C._uid("gbv", w, h, seed), inner, small_scene(cx - rx, cy - ry, 2 * rx, 2 * ry, seed)))
    o.append(f'<path d="{inner}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 6
    if h < 110:
        body = layout_band(w, h, seed)
    elif h <= 260:
        body = layout_medium(w, h, seed)
    else:
        body = layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
