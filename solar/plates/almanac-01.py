"""almanac-01 "Days to celebrate" (USA + Thailand holidays): Loy Krathong night.

A banana-leaf krathong with candle and incense floats on the river under the full moon, lesser
krathongs and sky lanterns drifting behind, a temple on the far bank. The US holidays ride the
architecture: Veterans Day stars on the ribbon banner, a Thanksgiving wheat garland round a
pumpkin in the pedestal tablet. Easter egg: a Sauvie Island great blue heron in the reeds.
"""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
_n, _d, _ell = C._n, C._d, C._ell_pts


# ----------------------------------------------------------------------------------------------
# small geometry
# ----------------------------------------------------------------------------------------------

def _seed(ctx):
    return sum((i + 1) * ord(c) for i, c in enumerate((ctx or {}).get("date", "")))


def _leaf(B, T, wid, bend=0., base=.45, n=24):
    """Pointed leaf / petal from base B to tip T; returns (poly, at(u, s))."""
    bx, by = B
    dx, dy = T[0] - bx, T[1] - by
    L = math.hypot(dx, dy) or 1.
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    b0 = math.asin(min(.99, base)) / PI

    def at(u, s):
        w = wid * math.sin(PI * (b0 + (1 - b0) * u)) ** .8
        off = bend * L * u * u
        return (bx + dx * u + nx * (s * w + off), by + dy * u + ny * (s * w + off))
    left = [at(i / n, 1) for i in range(n + 1)]
    right = [at(i / n, -1) for i in range(n, -1, -1)]
    return left + right[1:], at


def _leaf_lines(at, s_list, u0=0., u1=.97, n=14):
    return [[at(u0 + (u1 - u0) * i / n, s) for i in range(n + 1)] for s in s_list]


def _star(cx, cy, r, k=.42, pts=5, rot=-PI / 2):
    return [(cx + (r if i % 2 == 0 else r * k) * math.cos(rot + PI * i / pts),
             cy + (r if i % 2 == 0 else r * k) * math.sin(rot + PI * i / pts)) for i in range(2 * pts)]


def _wave(x0, x1, y, amp, per, ph, step=3.):
    n = max(2, int((x1 - x0) / step))
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin((x0 + (x1 - x0) * i / n) / per + ph)) for i in range(n + 1)]


def _cut(pl, keep):
    """Split polyline where keep(x, y) is False."""
    out, cur = [], []
    for p in pl:
        if keep(*p):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _densify(pl, step=1.5):
    out = [pl[0]]
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / step))
        out += [(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) for i in range(1, k + 1)]
    return out


# ----------------------------------------------------------------------------------------------
# the scene pieces (all draw into a Canvas)
# ----------------------------------------------------------------------------------------------

def _sky(cv, x, y, w, hy, moon, rng):
    """Ruled night sky, dark above, opening into a halo round the moon."""
    mx, my, mr = moon
    cv.obj([[(x, y), (x + w, y), (x + w, hy), (x, hy)]], 0)
    lines = []
    yy = y + .5
    while yy < hy:
        t = (yy - y) / max(1., hy - y)
        pitch = 1.5 if t < .45 else (2. if t < .8 else 3.)
        row = _densify([(x, yy), (x + w, yy)], 2.)

        def keep(px, py, yy=yy, pitch=pitch):
            d = math.hypot(px - mx, py - my)
            if d < mr * 1.12:
                return False
            if d < mr * 1.55:          # halo: every other line only
                return int((yy - y) / 1.5) % 2 == 0
            return True
        lines += _cut(row, keep)
        yy += pitch
    cv.hair(lines)
    # halo rings
    cv.hair([_ell(mx, my, mr * 1.25, mr * 1.25, 60), ])


def _moon(cv, mx, my, mr, rng):
    disc = _ell(mx, my, mr, mr, 64)[:-1]
    cv.obj([disc], 1.)
    # sphere modelling: light ruling over the face, a dense crescent on the lower right limb
    cv.hair(C.hatch_poly(disc, 0, 3, .7, inset=.6))
    crescent = _ell(mx, my, mr - .6, mr - .6, 40, -.4, PI * .9) + _ell(mx - mr * .16, my - mr * .16, mr * .98, mr * .98, 40, PI * .9, -.4)[::1]
    cv.hair(C.hatch_poly(crescent, 0, 1.5, 0))
    # maria
    for (fx, fy, ax, ay) in ((-.3, -.25, .32, .22), (.2, -.32, .2, .15), (.05, .15, .3, .2), (-.35, .3, .15, .12)):
        mp = _ell(mx + fx * mr, my + fy * mr, ax * mr, ay * mr, 18)[:-1]
        cv.hair(C.hatch_poly(mp, 0, 1.5, .75))


def _sparkle(cv, cx, cy, r):
    cv.obj([_star(cx, cy, r, .22, 4, 0)], .5)


def _lantern(cv, cx, cy, s):
    """Khom loi: a paper sky lantern, glowing, with ribs and a flame at the mouth."""
    top = [(cx - s * .5, cy - s * .55)] + _ell(cx, cy - s * .55, s * .5, s * .32, 12, PI, 2 * PI) + [(cx + s * .5, cy - s * .55)]
    body = top + [(cx + s * .34, cy + s * .55), (cx - s * .34, cy + s * .55)]
    cv.obj([body], .5)
    for f in (-.55, -.18, .18, .55):
        cv.hair([(cx + f * s * .5, cy - s * .75 + abs(f) * s * .12), (cx + f * s * .34, cy + s * .5)])
    cv.line([(cx - s * .36, cy + s * .55), (cx + s * .36, cy + s * .55)])
    cv.obj([_ell(cx, cy + s * .66, s * .1, s * .14, 8)[:-1]], 0)
    cv.line([(cx, cy + s * .6), (cx, cy + s * .72)])


def _far_bank(cv, x, w, hy, s, rng, temple_x):
    """Treeline and a chedi on the far bank, cut dark."""
    pts = [(x - 2, hy + 1)]
    xx = x - 2
    while xx < x + w + 2:
        h = s * (6 + 5 * abs(math.sin(xx * .07)) + 3 * rng.random())
        pts.append((xx, hy - h))
        xx += 2.5 + rng.random() * 2
    pts.append((x + w + 2, hy + 1))
    # chedi silhouette (bell on a stepped base with a ringed spire) with two smaller ones
    ch = []
    for k, (tx, sc) in enumerate(((temple_x, 1.), (temple_x - 22 * s, .55), (temple_x + 21 * s, .6))):
        H = 40 * s * sc
        b = 9 * s * sc
        poly = [(tx - b * 1.5, hy), (tx - b * 1.5, hy - H * .1), (tx - b * 1.2, hy - H * .1), (tx - b * 1.2, hy - H * .18)]
        poly += _ell(tx, hy - H * .18, b, H * .26, 16, PI, 1.5 * PI)
        poly += [(tx - b * .25, hy - H * .5), (tx - b * .12, hy - H * .7), (tx, hy - H), (tx + b * .12, hy - H * .7), (tx + b * .25, hy - H * .5)]
        poly += _ell(tx, hy - H * .18, b, H * .26, 16, 1.5 * PI, 2 * PI)
        poly += [(tx + b * 1.2, hy - H * .18), (tx + b * 1.2, hy - H * .1), (tx + b * 1.5, hy - H * .1), (tx + b * 1.5, hy)]
        ch.append(poly)
    cv.obj([pts], .5)
    cv.hair(C.hatch_poly(pts, 0, 1.5, 0))
    cv.hair(C.hatch_poly(pts, 50, 2, 0))
    for poly in ch:
        cv.obj([poly], 1.)
        cv.hair(C.hatch_poly(poly, 90, 1.5, 0))
        tx = sum(p[0] for p in poly) / len(poly)
        top = min(p[1] for p in poly)
        for f in (.62, .7, .78):     # spire rings, white
            yy = hy - (hy - top) * f
            cv.obj([[(tx - 1.6 * s, yy), (tx + 1.6 * s, yy), (tx + 1.3 * s, yy + 1), (tx - 1.3 * s, yy + 1)]], 0)


def _water(cv, x, w, hy, y1, moon, glows, rng):
    mx, my, mr = moon
    cv.obj([[(x, hy), (x + w, hy), (x + w, y1), (x, y1)]], 0)
    lines, heavy = [], []
    yy = hy + 1.
    k = 0
    while yy < y1:
        t = (yy - hy) / max(1., y1 - hy)
        amp = .25 + .9 * t
        per = 4 + 8 * t
        row = _wave(x - 2, x + w + 2, yy, amp, per, rng.uniform(0, 6), 2.)
        col = mr * (.7 + .9 * t)

        def keep(px, py, t=t, col=col):
            dx = abs(px - mx)
            if dx < col:        # the moon's road: broken into glitter
                return rng.random() < .45 + .5 * (dx / col) ** 2
            for gx, gy, gr in glows:
                if abs(px - gx) < gr * (1 - abs(py - gy) / (gr * 3)) and py > gy - 1:
                    return rng.random() < .4
            return rng.random() > .04
        segs = _cut(row, keep)
        (heavy if (t > .55 and k % 3 == 0) else lines).extend(segs)
        yy += 2. if t < .5 else (1.5 if k % 2 else 2.)
        k += 1
    cv.hair(lines)
    cv.line(heavy)


def _reeds(cv, bx, by, s, side, rng, n=7):
    """A clump of reeds and cattails (side +1 leans right)."""
    for i in range(n):
        x0 = bx + side * (i - n / 2) * 3.2 * s + rng.uniform(-1, 1) * s
        H = s * rng.uniform(26, 48)
        lean = side * rng.uniform(.05, .35)
        T = (x0 + lean * H, by - H)
        poly, at = _leaf((x0, by + 2), T, 1.5 * s + .6, bend=side * rng.uniform(-.08, .12), base=.9)
        cv.obj([poly], .5)
        cv.hair(_leaf_lines(at, (-.3,), 0, .9))
        if i % 3 == 1:
            hx, hy = at(.8, 0)
            head = _ell(hx, hy, 1.7 * s + .5, 5 * s, 14)[:-1]
            cv.obj([head], .5)
            cv.hair(C.hatch_poly(head, 0, 1.5, 0))
            cv.hair(C.hatch_poly(head, 70, 1.5, 0))
            cv.hair([at(.75, 0), (T[0] + lean * 5 * s, T[1] - 4 * s)])


def _cr(pts, closed=False, k=6):
    """Catmull-Rom through pts."""
    P = list(pts)
    n = len(P)
    out = []
    rng_ = range(n) if closed else range(n - 1)
    for i in rng_:
        p0 = P[(i - 1) % n] if closed or i > 0 else P[0]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed or i + 2 < n else P[-1]
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


# great blue heron, standing, facing +x; y up, height 1
_H_BODY = [(.165, .948), (.13, .957), (.095, .958), (.06, .945), (.04, .915), (.03, .87), (.035, .82), (.05, .77),
           (.04, .72), (.0, .675), (-.08, .63), (-.18, .58), (-.27, .53), (-.33, .485), (-.36, .462),
           (-.3, .462), (-.2, .47), (-.1, .48), (-.01, .5), (.06, .54), (.1, .59), (.105, .65), (.09, .7),
           (.085, .76), (.08, .81), (.085, .86), (.105, .9), (.135, .924), (.165, .932)]
_H_BEAK = (.325, .938)
_H_WING = [(-.355, .468), (-.27, .52), (-.16, .575), (-.05, .62), (.03, .64), (.075, .6), (.06, .55),
           (-.02, .51), (-.12, .49), (-.24, .474)]


def _heron(cv, fx, fy, H, face=1):
    """Great blue heron standing in the shallows of Sauvie Island. fx, fy: feet; H: height."""
    P = lambda p: (fx + face * p[0] * H, fy - p[1] * H)
    # legs, backward-bending, with the toes spread on the shallows
    cv.obj([], 0)
    for dx, kx in ((-.02, -.035), (.035, .045)):
        cv.line([P((dx, .5)), P((dx + kx, .25)), P((dx + kx * .4, .0))])
        cv.hair([P((dx + kx * .4, .0)), P((dx + kx * .4 + .07, -.005))])
        cv.hair([P((dx + kx * .4, .0)), P((dx + kx * .4 - .05, -.004))])
    cv.obj([_ell(*P((.0, .48)), H * .05, H * .02, 12)[:-1]], 0)
    body = [P(p) for p in _cr(_H_BODY, False, 5)] + [P(_H_BEAK)]
    cv.obj([body], 1.)
    # belly and flank: fine contour lines following the body underside
    for k in range(5):
        f = k / 5
        cv.hair([P(p) for p in _cr([(-.3 + .05 * f, .47 + .012 * k), (-.18, .48 + .014 * k), (-.06, .495 + .018 * k),
                                    (.03, .52 + .02 * k), (.08, .565 + .02 * k)], False, 4)])
    # neck: streaked front, shaded back of the neck
    for i in range(10):
        v = .6 + i * .03
        x0 = .08 + .012 * math.sin(i * 1.3)
        cv.hair([P((x0, v)), P((x0 - .015, v + .018))])
    back = [P(p) for p in _cr([(.04, .915), (.03, .87), (.035, .82), (.05, .77), (.04, .72), (.0, .675),
                               (.025, .67), (.065, .72), (.062, .78), (.05, .83), (.052, .88), (.07, .92)], False, 4)]
    cv.hair(C.hatch_poly(back, 80 * face, 1.5, 0))
    wing = [P(p) for p in _cr(_H_WING, True, 5)]
    cv.obj([wing], 1.)
    cv.hair(C.hatch_poly(wing, -24 * face, 1.5, 0))
    prim = [P(p) for p in _cr([(-.355, .468), (-.27, .52), (-.16, .56), (-.2, .5), (-.28, .478)], True, 4)]
    cv.hair(C.hatch_poly(prim, 40 * face, 1.5, .7))
    for k in range(4):     # covert feather edges
        cv.hair([P(p) for p in _cr([(-.05 - .05 * k, .6 - .02 * k), (-.02 - .05 * k, .56 - .02 * k), (.02 - .04 * k, .54 - .01 * k)], False, 4)])
    # head: black crown stripe and trailing plume, eye, bill
    stripe = [P(p) for p in _cr([(.13, .957), (.095, .962), (.05, .95), (-.03, .925), (-.09, .905), (-.02, .93),
                                 (.05, .935), (.1, .945), (.13, .95)], False, 4)]
    cv.obj([stripe], .5)
    cv.hair(C.hatch_poly(stripe, 0, 1., 0))
    cv.line([P((.05, .95)), P((-.09, .905))])
    ex, ey = P((.118, .942))
    cv.obj([_ell(ex, ey, 1.2, 1.2, 8)[:-1]], .5)
    cv.line([(ex - .3, ey), (ex + .3, ey)])
    cv.hair([P((.16, .94)), P((.32, .938))])
    cv.hair(C.hatch_poly([P((.165, .948)), P(_H_BEAK), P((.165, .932))], 0, 1.5, .5))
    # chest plumes
    for i in range(4):
        cv.hair([P((.1, .66 - i * .015)), P((.09 + i * .008, .58 - i * .02))])


def _krathong(cv, cx, cy, K, rng, small=False):
    """A banana-leaf krathong: trunk-slice base, two tiers of folded pointed leaves, a dome of
    marigolds, candle with flame, three incense sticks with smoke."""
    rx, ry = K * .5, K * .13
    base_h = K * .12
    # reflection under it: a few dark ruled strokes
    for i in range(4):
        yy = cy + base_h + 2 + i * 2.
        cv.obj([], 0)
        cv.hair([(cx - rx * (.8 - .15 * i), yy), (cx + rx * (.8 - .15 * i), yy)])
    # base drum
    side = _ell(cx, cy, rx, ry, 30, 0, PI) + _ell(cx, cy + base_h, rx, ry, 30, 0, PI)[::-1]
    side = _ell(cx, cy + base_h, rx, ry, 30, 0, PI) + _ell(cx, cy, rx, ry, 30, PI, 0)
    cv.obj([side], 1.)
    for i in range(1, 22):
        f = i / 22
        xx = cx - rx + 2 * rx * f
        yt = cy + ry * math.sqrt(max(0, 1 - ((xx - cx) / rx) ** 2))
        yb = yt + base_h
        if f < .3 or f > .78 or i % 2:
            cv.hair([(xx, yt + .3), (xx, yb - .3)])
    cv.line(_ell(cx, cy + base_h * .45, rx, ry, 30, 0, PI))

    items = []

    def tier(trx, try_, ty, n, ph, plen, pw, lift):
        for i in range(n):
            a = ph + 2 * PI * i / n
            bx, by = cx + trx * math.cos(a), ty + try_ * math.sin(a)
            tx = cx + (trx + plen * .5) * math.cos(a)
            tyy = by - plen * lift
            items.append((by, bx, (tx, tyy), a, pw))
    if small:
        tier(rx * .92, ry * .92, cy - K * .01, 7, .1, K * .34, K * .07, 1.)
        tier(rx * .6, ry * .6, cy - K * .1, 5, .35, K * .32, K * .07, 1.1)
    else:
        tier(rx * .95, ry * .95, cy, 16, .1, K * .2, K * .05, .95)
        tier(rx * .72, ry * .72, cy - K * .08, 13, .3, K * .22, K * .05, 1.)
        tier(rx * .48, ry * .48, cy - K * .16, 10, .05, K * .2, K * .048, 1.05)
    items.sort()
    for by, bx, T, a, pw in items:
        poly, at = _leaf((bx, by), T, pw, bend=0., base=.8)
        cv.obj([poly], 1. if not small else .5)
        # folded banana leaf: one half ruled dark, crease line, the other half lit
        dark_side = 1 if math.cos(a) > 0 else -1
        nl = max(2, int(pw / 1.5))
        cv.hair(_leaf_lines(at, [dark_side * (k + .5) / nl for k in range(nl)], .02, .95))
        cv.hair(_leaf_lines(at, [-dark_side * .6], .15, .75))
        cv.line(_leaf_lines(at, [0], .03, .99))
    if small:
        cv.obj([_ell(cx, cy - K * .3, K * .06, K * .1, 10)[:-1]], 0)
        cv.line([(cx, cy - K * .15), (cx, cy - K * .3)])
        return
    # marigold dome
    dome = _ell(cx, cy - K * .22, rx * .36, K * .17, 30, PI, 2 * PI) + [(cx + rx * .36, cy - K * .18), (cx - rx * .36, cy - K * .18)]
    cv.obj([dome], 1.)
    cv.hair(C.hatch_poly(dome, 0, 1.5, 0))
    for (fx, fy) in ((-.27, -.24), (.27, -.24), (-.14, -.33), (.14, -.33), (0, -.27), (-.13, -.22), (.13, -.22)):
        fx0, fy0 = cx + fx * rx * 1.05, cy + fy * K
        fr = K * .042
        fl = _ell(fx0, fy0, fr, fr * .8, 16)[:-1]
        cv.obj([fl], .5)
        for j in range(8):
            a = 2 * PI * j / 8
            cv.hair([(fx0 + fr * .3 * math.cos(a), fy0 + fr * .25 * math.sin(a)), (fx0 + fr * .9 * math.cos(a), fy0 + fr * .72 * math.sin(a))])
        cv.obj([_ell(fx0, fy0, fr * .3, fr * .25, 8)[:-1]], 0)
        cv.hair(C.hatch_poly(_ell(fx0, fy0, fr * .3, fr * .25, 8)[:-1], 45, 1.5))
    # incense: three sticks leaning right, glowing tips, smoke
    for j, ang in enumerate((-.35, -.22, -.09)):
        x0, y0 = cx + K * (.08 + .02 * j), cy - K * .3
        L = K * .42
        tip = (x0 + L * math.sin(-ang) * .6 + K * .02, y0 - L * math.cos(ang))
        cv.obj([], 0)
        cv.line([(x0, y0), tip])
        smoke = [(tip[0] + 2.2 * math.sin(i * .5 + j) * (i / 14) + i * .5, tip[1] - i * 1.6) for i in range(15)]
        cv.hair(smoke)
    # candle
    cw, chh = K * .05, K * .26
    cyt = cy - K * .36 - chh
    cand = [(cx - cw, cy - K * .3), (cx - cw, cyt), (cx + cw, cyt), (cx + cw, cy - K * .3)]
    cv.obj([cand], 1.)
    cv.hair(C.hatch_poly(cand[:2] + [(cx - cw * .2, cyt), (cx - cw * .2, cy - K * .3)], 90, 1.5, 0))
    cv.hair([(cx + cw * .3, cyt + 1), (cx + cw * .5, cyt + chh * .3)])  # wax drip
    # flame with radiant glow
    fcy = cyt - K * .07
    flame = [(cx + K * .04 * math.sin(t) * math.sin(t / 2) ** 1.3, fcy - K * .05 * math.cos(t) - K * .01 * math.cos(t) ** 2)
             for t in [2 * PI * i / 36 for i in range(36)]]
    cv.obj([flame], 1.)
    cv.obj([_ell(cx, fcy + K * .015, K * .012, K * .025, 8)[:-1]], 0)
    cv.line([(cx, fcy + K * .03), (cx, cyt)])
    return (cx, fcy, K * .1)


def _glow_rays(cv, cx, cy, r0, r1, n=24):
    cv.obj([], 0)
    for i in range(n):
        a = 2 * PI * (i + .5) / n
        rr = r1 * (1 if i % 2 else .7)
        cv.hair([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + rr * math.cos(a), cy + rr * math.sin(a))])


def _firework(cv, cx, cy, r, rng, n=22):
    cv.obj([_ell(cx, cy, r * .28, r * .28, 16)[:-1]], 0)
    lines = []
    for i in range(n):
        a = 2 * PI * i / n + rng.uniform(-.05, .05)
        rr = r * rng.uniform(.8, 1.)
        sag = r * .12
        pts = [(cx + rr * t * math.cos(a), cy + rr * t * math.sin(a) + sag * t * t) for t in [k / 6 for k in range(1, 7)]]
        lines.append(pts)
        ex, ey = pts[-1]
        cv.obj([_ell(ex, ey + .6, .9, .9, 6)[:-1]], 0)
        cv.line([(ex, ey + .2), (ex, ey + 1.6)])
    cv.obj([], 0)
    cv.hair(lines)
    cv.line([(cx - 1, cy), (cx + 1, cy)])


def _scene(x, y, w, h, clip_d, ctx, level):
    """The Loy Krathong night, laid out in the box x,y,w,h and clipped to clip_d.
    level: 0 medallion, 1 cartouche (medium), 2 big cartouche (tall)."""
    rng = random.Random(_seed(ctx) * 7 + level)
    cv = C.Canvas()
    s = min(w / 200., h / 170.)
    hy = y + h * (.46 if level else .5)
    mr = min(w, h) * (.15 if level else .2)
    mx, my = x + w * (.68 if level else .73), y + h * (.22 if level else .27)
    if level == 0:
        mx, my, mr = x + w * .74, y + h * .32, min(w, h) * .17
    moon = (mx, my, mr)
    _sky(cv, x - 2, y - 2, w + 4, hy, moon, rng)
    # stars
    for i in range(int(6 + 8 * s) if level else 3):
        sx, sy = x + rng.uniform(.05, .95) * w, y + rng.uniform(.04, .35) * h
        if math.hypot(sx - mx, sy - my) > mr * 1.8:
            _sparkle(cv, sx, sy, rng.uniform(1.6, 2.6) * max(.8, s))
    _moon(cv, mx, my, mr, rng)
    if level:
        # New Year's and Loy Krathong fireworks
        _firework(cv, x + w * .2, y + h * .16, w * .1, rng)
        if level == 2:
            _firework(cv, x + w * .42, y + h * .1, w * .06, rng, 16)
        # sky lanterns rising from beyond the temple
        for i in range(5 if level == 2 else 3):
            lx = x + w * (.3 + .28 * rng.random())
            ly = y + h * (.18 + .2 * rng.random())
            if math.hypot(lx - mx, ly - my) < mr * 1.7:
                continue
            _lantern(cv, lx, ly, max(5., 9 * s * (1 - (hy - ly) / h * .5)))
        _far_bank(cv, x - 2, w + 4, hy, s, rng, x + w * .47)
    glows = []
    K = min(w * .4, h * (.6 if level else .8))
    kx, ky = x + w * .54, y + h * (.8 if level else .78)
    if level:
        for fx, fy, fk in ((.36, .555, .11), (.84, .6, .12)):
            glows.append((x + w * fx, y + h * fy, K * fk * 1.2))
    glows.append((kx, ky + K * .1, K * .4))
    _water(cv, x - 2, w + 4, hy, y + h + 2, moon, glows, rng)
    if level:
        for fx, fy, fk in ((.36, .555, .11), (.84, .6, .12)):
            _krathong(cv, x + w * fx, y + h * fy, K * fk * 2.2, rng, small=True)
    if level == 2 or (level == 1 and w > 150):
        # Easter egg: Parker's Sauvie Island heron, wading in the reeds at the left
        _reeds(cv, x + w * .04, y + h + 2, s * 1.1, 1, rng, 6)
        _reeds(cv, x + w * .96, y + h + 2, s * 1.1, -1, rng, 6)
        _heron(cv, x + w * (.15 if w < h * 1.3 else .2), y + h * .97, h * .62, 1)
    else:
        # Easter egg, small: the Sauvie Island heron wading at the left
        _heron(cv, x + w * (.2 if level else .18), y + h * (.9 if level else .86), h * (.55 if level else .5), 1)
    flame = _krathong(cv, kx, ky, K, rng)
    _glow_rays(cv, flame[0], flame[1], flame[2] * .9, flame[2] * 2.3, 20 if level else 14)
    cid = C._uid("lk", x, y, w, h, level)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ----------------------------------------------------------------------------------------------
# US holidays on the architecture
# ----------------------------------------------------------------------------------------------

def _lotus_crest(cx, by, S):
    """Loy Krathong's lotus as the crest: a bud of shaded pointed petals on a ribbed calyx."""
    cv = C.Canvas()
    spec = [(62, .6, .2, .1), (38, .82, .22, .06), (16, .95, .23, .03), (0, 1.05, .25, 0.)]
    for ang, ln, wd, bd in spec:
        for side in ((-1, 1) if ang else (1,)):
            a = math.radians(ang) * side
            B = (cx + side * S * .06 * (ang > 0), by)
            T = (B[0] + S * ln * math.sin(a), by - S * ln * math.cos(a))
            poly, at = _leaf(B, T, S * wd, bend=-side * bd, base=.55)
            cv.obj([poly], 1.)
            nl = max(3, int(S * wd / 1.5))
            dk = -side if ang else -1
            cv.hair(_leaf_lines(at, [dk * (k + .5) / nl for k in range(nl)], .03, .93))
            cv.hair(_leaf_lines(at, [-dk * .45, -dk * .75], .12, .8))
            cv.line(_leaf_lines(at, [0], .05, .96))
    cal = _ell(cx, by + S * .02, S * .3, S * .1, 24)[:-1]
    cv.obj([cal], 1.)
    cv.hair(C.hatch_poly(cal, 90, 1.5, 0))
    cv.obj([_ell(cx, by - S * .02, S * .22, S * .05, 18)[:-1]], 1.)
    return cv.svg()


def _banner_stars(centre, h):
    """Veterans Day: a row of engraved stars along the ribbon face."""
    n = len(centre)
    out = []
    step = max(1, int(round(n / 11)))
    for i in range(step // 2 + 1, n - 1, step):
        cx, cy = centre[i]
        out.append(_d(_star(cx, cy, h * .3), True, 0))
    rule = _d(centre, tol=.15)
    return (f'<path d="{"".join(out)}" fill="#000" stroke="none"/>')


def _harvest(tx, ty, tw, th):
    """Thanksgiving: a wheat garland from a pumpkin across the pedestal tablet."""
    cv = C.Canvas()
    x0, y0, x1, y1 = tx + 3, ty + 2.5, tx + tw - 2, ty + th - 1.5
    cy = (y0 + y1) / 2
    hh = (y1 - y0)
    cv.obj([[(tx + 2, ty + 2), (tx + tw - 1, ty + 2), (tx + tw - 1, ty + th - 1), (tx + 2, ty + th - 1)]], 0)
    cv.hair(C.hatch_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0, 3, .5))
    cx = tx + tw / 2
    pr = hh * .55
    for side in (-1, 1):
        stem = [(cx + side * pr * 1.4, cy + hh * .05 * 0)] + [(cx + side * (pr * 1.4 + t), cy + hh * .12 * math.sin(t / 16)) for t in range(0, int(tw / 2 - pr * 1.4 - 4), 2)]
        cv.obj([], 0)
        cv.line(stem)
        L = len(stem)
        for k in range(3, L - 2, 4):
            px, py = stem[k]
            up = 1 if (k // 4) % 2 else -1
            T = (px + side * hh * .5, py + up * hh * .32)
            poly, at = _leaf((px, py), T, hh * .14, base=.7)
            cv.obj([poly], .5)
            cv.hair(_leaf_lines(at, (-.3 * up * side,), .1, .9))
            ax, ay = T
            cv.hair([(ax, ay), (ax + side * hh * .3, ay + up * hh * .06)])
    # pumpkin
    for k, (dx, rr) in enumerate(((-.5, .55), (.5, .55), (-.22, .75), (.22, .75), (0, .62))):
        e = _ell(cx + dx * pr, cy + hh * .05, pr * rr, pr * .62, 20)[:-1]
        cv.obj([e], .5)
        cv.hair(C.hatch_poly(e, 90, 1.5 if k < 2 else 3, 0))
    cv.obj([[(cx - 1, cy - pr * .5), (cx + 1, cy - pr * .5), (cx + 2.5, cy - pr * .95), (cx + 1, cy - pr * 1.0)]], .5)
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts (house frame, adapted so every field is engraved: no blank paper)
# ----------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip = _d(_ell(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(_scene(cx - rx + 2, cy - ry + 2, 2 * rx - 4, 2 * ry - 4, clip, ctx, 0))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 2.5, ry - 2.5, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.5)
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx0, fx1 = ix - iw * .2, ix + iw * 1.2
    fy0, fy1 = iy - ih * .2, iy + ih * 1.2
    o.append(_scene(fx0, fy0, fx1 - fx0, fy1 - fy0, field, ctx, 1))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # the ground runs to the plate's edges; a light ruling above the panel carries the crest
    o.append(C.dark_ground((0, 0, w, py0 + ph), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .52, ph * .66
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx0, fx1 = ix - iw * .2, ix + iw * 1.2
    fy0, fy1 = iy - ih * .2, iy + ih * 1.2
    o.append(_scene(fx0, fy0, fx1 - fx0, fy1 - fy0, field, ctx, 2))
    o.append(_lotus_crest(cx, cy - ch / 2 + 10, min(ch * .2 + top_free, 62)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_stars(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, h - py), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_harvest(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = _seed(ctx) % 100003
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
