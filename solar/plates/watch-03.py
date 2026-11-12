"""watch-03 plate: Kids' movie of the day, "Tuck Everlasting" (1914, Treegap wood, because it's fall).

The vignette is the heart of the story: the giant ash in the Treegap wood with the secret spring
welling up among its roots, ringed with pebbles; Winnie's toad sits by the spring; the Tucks' pond
and rowboat lie beyond under a moon of today's phase; autumn leaves fall through the scene and drift
across the acanthus ground. Tall plates letter the ribbon TUCK EVERLASTING and carve MCMXIV (1914)
into the pedestal tablet.

Easter egg: a "P" carved into the bark of the great ash, like a lover's initial cut into a tree.
"""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import Canvas, _Rib, _ell_pts, _d, _n, hatch_poly, _shadow, _fill_lines, _euler

PI = math.pi


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def runs(segs, keep, step=.7):
    """Split polylines into the runs where keep(x, y) is true."""
    out = []
    for pl in segs:
        cur = []
        straight = len(pl) == 2
        for j, ((x0, y0), (x1, y1)) in enumerate(zip(pl, pl[1:])):
            L = math.hypot(x1 - x0, y1 - y0)
            k = max(1, int(L / step))
            last = j == len(pl) - 2
            for i in range(k + (1 if last else 0)):
                t = i / k
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                if keep(x, y):
                    cur.append((x, y))
                else:
                    if len(cur) > 1:
                        out.append([cur[0], cur[-1]] if straight else cur)
                    cur = []
        if len(cur) > 1:
            out.append([cur[0], cur[-1]] if straight else cur)
    return out


def hlines(poly, ys):
    """Horizontal lines at the given y values clipped to a polygon."""
    out = []
    n = len(poly)
    for y in ys:
        xs = []
        for i in range(n):
            (a0, b0), (a1, b1) = poly[i], poly[(i + 1) % n]
            if (b0 <= y < b1) or (b1 <= y < b0):
                xs.append(a0 + (a1 - a0) * (y - b0) / (b1 - b0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            if xs[j + 1] - xs[j] > .6:
                out.append([(xs[j], y), (xs[j + 1], y)])
    return out


def wobble(segs, amp, freq, ph=0.):
    return [[(x + amp * math.sin(y * freq + ph), y) for x, y in pl] for pl in segs]


def moon_phase(date):
    """0 new, .5 full."""
    try:
        y, m, d = (int(v) for v in date.split("-"))
    except Exception:
        return .5
    a = (14 - m) // 12
    yy, mm = y + 4800 - a, m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    return ((jdn - 2451550.26) / 29.530589) % 1.


# ------------------------------------------------------------------------------------------------
# path lettering (no <text>): engraved Roman capitals as strokes in a unit box
# ------------------------------------------------------------------------------------------------

def _arc_pts(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GLYPHS = {
    "T": (.7, [[(0, 0), (.7, 0)], [(.35, 0), (.35, 1)]]),
    "U": (.7, [[(0, 0), (0, .72), (.08, .93), (.22, 1), (.48, 1), (.62, .93), (.7, .72), (.7, 0)]]),
    "C": (.7, [_arc_pts(.38, .5, .36, .5, -42, -318)]),
    "K": (.66, [[(0, 0), (0, 1)], [(.64, 0), (0, .62)], [(.2, .46), (.66, 1)]]),
    "E": (.58, [[(.58, 0), (0, 0), (0, 1), (.58, 1)], [(0, .5), (.44, .5)]]),
    "V": (.72, [[(0, 0), (.36, 1), (.72, 0)]]),
    "R": (.64, [[(0, 1), (0, 0), (.38, 0), (.54, .06), (.6, .25), (.54, .43), (.38, .5), (0, .5)],
                [(.3, .5), (.64, 1)]]),
    "P": (.62, [[(0, 1), (0, 0), (.38, 0), (.54, .06), (.6, .25), (.54, .43), (.38, .5), (0, .5)]]),
    "L": (.56, [[(0, 0), (0, 1), (.56, 1)]]),
    "A": (.74, [[(0, 1), (.37, 0), (.74, 1)], [(.16, .64), (.58, .64)]]),
    "S": (.6, [[(.58, .14), (.46, .03), (.3, 0), (.13, .04), (.03, .16), (.05, .31), (.2, .43),
                (.42, .54), (.57, .67), (.6, .84), (.49, .96), (.3, 1), (.12, .96), (0, .85)]]),
    "I": (0., [[(0, 0), (0, 1)]]),
    "N": (.7, [[(0, 1), (0, 0), (.7, 1), (.7, 0)]]),
    "G": (.72, [_arc_pts(.38, .5, .36, .5, -40, -320) + [(.7, .6), (.42, .6)]]),
    "M": (.86, [[(0, 1), (0, 0), (.43, .78), (.86, 0), (.86, 1)]]),
    "X": (.7, [[(0, 0), (.7, 1)], [(.7, 0), (0, 1)]]),
    " ": (.45, []),
}


def letter_strokes(text, cx, cy, size, track=.32, centre=None):
    """Strokes for text of cap height size centred on (cx, cy), or along a centre line (a ribbon's).
    Returns (main strokes, serif strokes)."""
    adv = [GLYPHS[c][0] + track for c in text]
    total = (sum(adv) - track) * size
    main, ser = [], []
    if centre:
        L = [0.]
        for a, b in zip(centre, centre[1:]):
            L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

        def place(s):
            s = L[-1] / 2 + s
            for i in range(1, len(L)):
                if L[i] >= s:
                    t = (s - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
                    a, b = centre[i - 1], centre[i]
                    ang = math.atan2(b[1] - a[1], b[0] - a[0])
                    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, ang
            return centre[-1][0], centre[-1][1], 0.
    else:
        def place(s):
            return cx + s, cy, 0.
    x = -total / 2
    for c, a in zip(text, adv):
        gw, strokes = GLYPHS[c]
        px, py, ang = place(x + gw * size / 2)
        ca, sa = math.cos(ang), math.sin(ang)

        def tf(u, v, gw=gw, px=px, py=py, ca=ca, sa=sa):
            lx, ly = (u - gw / 2) * size, (v - .5) * size
            return (px + lx * ca - ly * sa, py + lx * sa + ly * ca)
        for st in strokes:
            main.append([tf(u, v) for u, v in st])
            for (u0, v0), (u1, v1) in ((st[0], st[1]), (st[-1], st[-2])):
                if v0 in (0, 1) and abs(u1 - u0) < .3 * abs(v1 - v0):
                    ser.append([tf(u0 - .14, v0), tf(u0 + .14, v0)])
        x += a * size
    return main, ser


def letters_svg(text, cx, cy, size, centre=None, halo=False):
    main, ser = letter_strokes(text, cx, cy, size, centre=centre)
    sw = "1.5" if size >= 7 else "1"
    h = (f'<path d="{"".join(_d(p, tol=0) for p in main + ser)}" stroke="#fff" stroke-width="4.5" fill="none"/>'
         if halo else "")
    return h + (f'<path d="{"".join(_d(p, tol=0) for p in main)}" stroke="#000" stroke-width="{sw}" fill="none"/>'
            f'<path d="{"".join(_d(p, tol=0) for p in ser)}" stroke="#000" stroke-width="1" fill="none"/>')


# ------------------------------------------------------------------------------------------------
# motifs of the story
# ------------------------------------------------------------------------------------------------

def maple_leaf(cv, x, y, s, rot):
    """A small fallen maple leaf, veined, half shaded."""
    pts = []
    lobes = ((-PI / 2, 1.), (-PI / 2 - 1.05, .86), (-PI / 2 + 1.05, .86), (-PI / 2 - 2.05, .55), (-PI / 2 + 2.05, .55))
    for i in range(64):
        t = 2 * PI * i / 64 - PI
        m = max(L * math.exp(-((math.atan2(math.sin(t - a), math.cos(t - a))) / .4) ** 2) for a, L in lobes)
        r = s * (.42 + .58 * m) * (1 + .08 * abs(math.sin(t * 11)))
        pts.append((x + r * math.cos(t + rot), y + r * math.sin(t + rot)))
    cv.obj([pts], .5 if s < 4 else 1.)
    for a, L in lobes:
        cv.hair([(x, y), (x + s * .85 * L * math.cos(a + rot), y + s * .85 * L * math.sin(a + rot))])
    sx, sy = math.cos(rot), math.sin(rot)
    cv.line(runs(hatch_poly(pts, math.degrees(rot) + 60, 1.5),
                 lambda px, py: (px - x) * sx + (py - y) * sy > s * .05))
    cv.hair(runs(hatch_poly(pts, math.degrees(rot) - 60, 2),
                 lambda px, py: (px - x) * sx + (py - y) * sy <= s * .05))
    cv.line([(x, y), (x - s * .75 * math.cos(rot - PI / 2), y - s * .75 * math.sin(rot - PI / 2)),
             (x - s * .8 * math.cos(rot - PI / 2) + s * .12 * math.cos(rot), y - s * .8 * math.sin(rot - PI / 2) + s * .12 * math.sin(rot))])


def toad(cv, x, y, L, face=1):
    """Winnie's toad squatting at (x, y) (its feet), L long, facing +x if face > 0: broad flat
    head with a bulging eye, humped warty back, folded haunch, propped front leg."""
    def T(u, v):
        return (x + face * (u - .5) * L, y - (.62 - v) * L)
    P = [(1., .4), (.96, .3), (.86, .24), (.8, .15), (.7, .13), (.62, .2), (.48, .16), (.32, .1),
         (.18, .12), (.07, .22), (0, .36), (.02, .48), (.1, .56), (.4, .6), (.7, .58), (.86, .52),
         (.95, .47)]
    body = [T(u, v) for u, v in P]
    cv.obj([body], 1.)
    cv.hair(hatch_poly(body, 30 * face, 1.5))
    cv.line(runs(hatch_poly(body, -60 * face, 1.5), lambda px, py: py > y - L * .2))
    rng = random.Random(7)
    for i in range(int(4 + L * .3)):
        u, v = rng.uniform(.12, .62), rng.uniform(.16, .4)
        cx, cy = T(u, v)
        r = max(.7, L * .03)
        cv.obj([_ell_pts(cx, cy, r, r * .8, 8)[:-1]], .5)
    th = [T(u, v) for u, v in ((.06, .5), (.1, .32), (.24, .26), (.4, .34), (.42, .5), (.34, .6), (.16, .6))]
    cv.obj([th], 1.)
    cv.hair(hatch_poly(th, -40 * face, 1.5))
    cv.heavy([T(u, v) for u, v in ((.38, .58), (.5, .62), (.3, .62))])
    fl = [T(u, v) for u, v in ((.74, .4), (.8, .4), (.82, .6), (.9, .62), (.76, .62), (.72, .46))]
    cv.obj([fl], 1.)
    cv.line(hatch_poly(fl, 0, 1.2))
    ex, ey = T(.74, .14)
    r = max(1.4, L * .09)
    cv.obj([_ell_pts(ex, ey, r * 1.15, r, 12)[:-1]], 1.)
    cv.heavy(hatch_poly(_ell_pts(ex, ey + r * .25, r * .9, r * .6, 10)[:-1], 0, 1))
    cv.line([T(1., .36), T(.84, .34), T(.7, .3)])


def heron(cv, x, y, s, face=1):
    """A great blue heron standing at (x, y) (its feet), s tall: Sauvie Island's bird."""
    def T(u, v):
        return (x + face * u * s, y - v * s)
    sil = [(.62, .86), (.44, .9), (.38, .93), (.22, .93), (.33, .89), (.33, .82), (.27, .74), (.25, .66),
           (.29, .61), (.2, .6), (.04, .56), (-.14, .42), (-.08, .405), (.08, .42), (.22, .45), (.31, .5),
           (.37, .6), (.33, .68), (.35, .76), (.41, .83), (.45, .855)]
    body = [T(u, v) for u, v in sil]
    cv.obj([body], .5)
    cv.hair(hatch_poly(body, 15 * face, 1.5))
    wing = [T(u, v) for u, v in ((.27, .6), (.04, .555), (-.13, .425), (.1, .47), (.25, .5))]
    cv.line(hatch_poly(wing, -30 * face, 1.5))
    cv.heavy([T(.36, .9), T(.24, .925)])
    cv.hair([T(.1, .43), T(.12, .2), T(.11, 0)])
    cv.hair([T(.17, .44), T(.19, .2), T(.22, 0)])
    cv.hair([T(.11, 0), T(.17, 0)])


def clump(cv, cx, cy, r, rng, big=True):
    """One mass of foliage: scalloped edge, lit upper left, dark lower right, leaf tufts."""
    nl = max(7, int(r / 2.6))
    ph = rng.uniform(0, 2 * PI)
    pts = []
    for i in range(nl * 6):
        t = 2 * PI * i / (nl * 6)
        sc = abs(math.sin(nl * t / 2 + ph))
        rr = r * (.86 + .14 * sc ** .5)
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t) * .86))
    cv.obj([pts], 1.)
    hx, hy = cx - r * .38, cy - r * .42
    ang = -35 + rng.uniform(-8, 8)
    p0 = rng.uniform(0, 3)
    cv.hair(hatch_poly(pts, ang, 3, p0))
    cv.hair(runs(hatch_poly(pts, ang, 3, p0 + 1.5), lambda x, y: math.hypot(x - hx, y - hy) > r * .62))
    cv.line(runs(hatch_poly(pts, ang + 90, 1.5), lambda x, y: math.hypot(x - hx, y - hy) > r * .95))
    cv.heavy(runs(hatch_poly(pts, ang + 90, 1.5, .75), lambda x, y: math.hypot(x - hx, y - hy) > r * 1.18))
    if big and r > 6:
        for j in range(int(r * r / 18)):
            a = rng.uniform(0, 2 * PI)
            d = r * math.sqrt(rng.uniform(.05, .72))
            px, py = cx + d * math.cos(a), cy + d * math.sin(a) * .86
            k = r * .1 + 1
            lit = math.hypot(px - hx, py - hy) < r * .7
            pl = [(px - k, py - k * .2), (px - k * .45, py + k * .35), (px + k * .2, py + k * .4), (px + k * .8, py)]
            (cv.hair if lit else cv.line)(pl)


def rib_shade(cv, R, side, dark=1., pitch_lit=3., pitch_dk=1.6, wob=0., outline=1.):
    """A carved round member: lines along its form, sparse on the lit side, dense toward `side`,
    with a black shadow on that edge."""
    cv.obj([R.outline()], outline)
    if not outline:   # open at the root: only the two flanks are cut
        cv.line(R.contour(1., 0, 1) + R.contour(-1., 0, 1))
    lit = _fill_lines(R, -.9 * side, .15 * side, pitch_lit, 0, 1, 3)
    dk = _fill_lines(R, .3 * side, .97 * side, pitch_dk, 0, 1, 4)
    if wob:
        lit = wobble(lit, wob, .45)
        dk = wobble(dk, wob, .45)
    cv.hair(lit)
    cv.hair(dk)
    T = max(R.wl + R.wr) * .38 * dark
    _shadow(cv, R, side, T, 0., 1.)


def scene(cv, X, Y, W, H, seed, date, det=1):
    """The Treegap wood: giant ash, spring among its roots, toad, pond and rowboat, moon, falling
    leaves. Fills the box X, Y, W, H with tone (no bare paper)."""
    rng = random.Random(seed)
    wide = W > H * 1.2
    hy = Y + H * .58
    gy = Y + H * (.80 if det else .84)
    tx = X + W * (.42 if wide else .45)
    Rc = min(W * (.3 if wide else .36), H * (.42 if wide else .36))
    hw = max(2.8, Rc * .16)

    sky = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, hy + 3), (X - 2, hy + 3)]
    cv.obj([sky], 0)
    ys, yv = [], Y - 1
    while yv < hy + 3:
        ys.append(yv)
        yv += 2 if yv < Y + H * .2 else (1.5 if yv < Y + H * .32 else (2 if yv < Y + H * .46 else 3))
    zen = Y + H * .2
    cv.line(hlines(sky, [v for v in ys if v < zen]))
    cv.hair(hlines(sky, [v for v in ys if v >= zen]))

    ph = moon_phase(date)
    mr = max(3.5, H * .075)
    mx = X + W * (.86 if wide else .82)
    my = Y + H * .17
    disc = _ell_pts(mx, my, mr, mr, 32)[:-1]
    cv.obj([disc], .5)
    c2 = math.cos(2 * PI * ph)

    def dark(x, y):
        u, v = (x - mx) / mr, (y - my) / mr
        q = math.sqrt(max(0., 1 - v * v))
        return not (u > q * c2 if ph < .5 else u < -q * c2)
    cv.hair(runs(hlines(disc, [my - mr + .75 + i * 1.5 for i in range(int(mr * 2 / 1.5) + 1)]), dark))
    cv.hair(runs(hlines(disc, [my - mr + 1.5 + i * 3 for i in range(int(mr * 2 / 3) + 1)]),
                 lambda x, y: not dark(x, y)))

    crowns = []
    xx = X - 6
    while xx < X + W + 6:
        cw_ = H * rng.uniform(.07, .14)
        crowns.append((xx + cw_ / 2, cw_ / 2, H * rng.uniform(.07, .15), rng.random() < .15))
        xx += cw_ * rng.uniform(.55, .8)

    def sky_line(px):
        best = H * .02
        for c, r, top, fir in crowns:
            d = abs(px - c) / r
            if d < 1:
                best = max(best, top * (1.25 * (1 - d) if fir else math.sqrt(1 - d * d)))
        return hy - best
    wood = [(X - 2, hy + 4)] + [(X - 2 + i * .8, sky_line(X - 2 + i * .8)) for i in range(int((W + 4) / .8) + 1)] + [(X + W + 2, hy + 4)]
    cv.obj([wood], .5)
    cv.line(hatch_poly(wood, 90, 1.5, .5))

    ground = [(X - 2, hy), (X + W + 2, hy), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([ground], 0)
    ys, yv = [], hy + 1
    while yv < Y + H + 2:
        ys.append(yv)
        f = (yv - hy) / (Y + H - hy)
        yv += 3 if f < .3 else (2 if f < .7 else 1.5)
    fy_ = hy + (Y + H - hy) * .62
    cv.hair(hlines(ground, [v for v in ys if v < fy_]))
    cv.line(hlines(ground, [v for v in ys if v >= fy_]))
    for i in range(int(W / 4)):
        gx = X + rng.uniform(0, W)
        g0 = hy + (Y + H - hy) * rng.uniform(.08, .7)
        gh = 1.2 + (g0 - hy) * .09
        cv.hair([[(gx - gh * .5, g0 - gh * .8), (gx - .3, g0)], [(gx + .1, g0 - gh * 1.1), (gx, g0)],
                 [(gx + gh * .55, g0 - gh * .7), (gx + .3, g0)]])

    pcx, pcy = X + W * (.79 if wide else .75), hy + (gy - hy) * .55
    prx, pry = W * (.2 if wide else .22), max(3., (gy - hy) * .32)
    pond = _ell_pts(pcx, pcy, prx, pry, 40)[:-1]
    cv.obj([pond], .5)
    cv.hair(runs(hlines(pond, [pcy - pry + .75 + i * 1.5 for i in range(int(pry * 2 / 1.5) + 1)]),
                 lambda x, y: (int(x * .5 + y * 7.3) % 7) != 0 or abs(y - pcy) > pry * .5))
    if det and prx > 18:
        bl = min(prx * .55, H * .2)
        bx, by = pcx - prx * .1, pcy + pry * .05
        hull = [(bx - bl * .5, by - bl * .1), (bx + bl * .5, by - bl * .12), (bx + bl * .38, by + bl * .08),
                (bx - bl * .36, by + bl * .08)]
        cv.obj([hull], 1.)
        cv.hair(hatch_poly(hull, 0, 1.5, .4))
        cv.line([(bx - bl * .5, by - bl * .1), (bx + bl * .5, by - bl * .12)])
        cv.line([(bx - bl * .1, by - bl * .1), (bx - bl * .55, by + bl * .25)])
        if bl > 12:
            fig = _ell_pts(bx + bl * .08, by - bl * .22, bl * .08, bl * .13, 12)[:-1]
            cv.obj([fig], .5)
            cv.line(hatch_poly(fig, 0, 1, .2))
            cv.obj([_ell_pts(bx + bl * .08, by - bl * .4, bl * .06, bl * .06, 10)[:-1]], .5)
        cv.hair([(bx - bl * .6, by + bl * .14), (bx + bl * .6, by + bl * .14)])

    if det and H * .2 >= 18:
        heron(cv, pcx - prx * .7, pcy + pry * .75, max(10., H * .2), 1)
    ccx, ccy = tx, Y + H * (.3 if wide else .27)
    nC = (16 if det else 13) + (8 if det > 1 else 0)
    cl = []
    for i in range(nC):
        a = rng.uniform(-PI, 0)
        d = math.sqrt(rng.uniform(0, 1))
        px = ccx + Rc * (1.55 if wide else 1.15) * d * math.cos(a)
        py = ccy + Rc * .55 * d * math.sin(a) + Rc * .35 * rng.uniform(-.2, 1)
        cl.append((py, px, Rc * (rng.uniform(.3, .42) if det else rng.uniform(.26, .34))))
    cl.sort()
    back, front = cl[:int(nC * .6)], cl[int(nC * .6):]
    for py, px, r in back:
        clump(cv, px, py, r, rng, det > 0)
    ttop = ccy + Rc * .35
    for sgn, ang, ln in ((-1, -2.25, .95), (1, -.85, .9), (0, -1.6, .7)):
        sx = tx + sgn * hw * .4
        pts = _euler(sx, ttop + hw, ang, Rc * ln, lambda u, s=sgn, L=Rc * ln: -s * .3 / L, 18)
        n = len(pts)
        Wd = [hw * (.75 - .5 * i / (n - 1)) for i in range(n)]
        rib_shade(cv, _Rib(pts, Wd, Wd), 1 if sgn >= 0 else -1, .8, 3, 1.6)
    n = 26
    tpts = [(tx + hw * .3 * math.sin(i / (n - 1) * 2.2), gy - (gy - ttop) * i / (n - 1)) for i in range(n)]
    Wt = [hw * (1 + 1.5 * (1 - i / (n - 1)) ** 4) for i in range(n)]
    TR = _Rib(tpts, Wt, Wt)
    rib_shade(cv, TR, 1, 1., 3, 1.6, wob=.45)
    kx, ky = TR.at(.62, .4)
    knot = _ell_pts(kx, ky, hw * .2, hw * .35, 12)[:-1]
    cv.obj([knot], 1.)
    cv.line(hatch_poly(knot, 90, .9))
    # the Easter egg: a P cut into the bark in a little blaze
    bx_, by_ = TR.at(.4, -.32)
    ps = max(3.6, hw * .75)
    cv.obj([_ell_pts(bx_, by_, ps * .48, ps * .68, 16)[:-1]], .5)
    pm, _ = letter_strokes("P", bx_, by_, ps * .8)
    cv.line(pm)
    for py, px, r in front:
        if py + r * .8 < ttop + hw * 2.5 or abs(px - tx) > hw * 3:
            clump(cv, px, py, r, rng, det > 0)

    for sgn, ang, ln in ((-1, 3.0, 4.6), (1, .14, 4.8), (-1, 2.75, 2.6), (1, .4, 2.8)):
        sx = tx + sgn * hw * .9
        sy = gy - hw * 1.1
        L = hw * ln
        pts = _euler(sx, sy, ang, L, lambda u, s=sgn, L=L: s * (1.1 * math.sin(u * 6) + .35) / L, 18)
        nn = len(pts)
        Wd = [hw * .7 * (1 - .85 * i / (nn - 1)) ** 1.2 + .5 for i in range(nn)]
        R = _Rib(pts, Wd, Wd)
        rib_shade(cv, R, 1 if R.N[0][1] > 0 else -1, 1.2, 1.5, 1.5, outline=0)

    sx, sy = tx + hw * .2, gy + max(2., hw * .35)
    srx, sry = max(5., hw * 2.1), max(1.8, hw * .55)
    pool = _ell_pts(sx, sy, srx, sry, 28)[:-1]
    npb = int(8 + srx * .9)
    for i in range(npb):
        a = 2 * PI * i / npb + .2
        pr = max(1., hw * .28) * (.8 + .4 * ((i * 37) % 5) / 4)
        px, py = sx + (srx + pr * .6) * math.cos(a), sy + (sry + pr * .5) * math.sin(a)
        peb = _ell_pts(px, py, pr * 1.25, pr * .8, 10)[:-1]
        cv.obj([peb], .5)
        cv.hair(runs(hatch_poly(peb, 0, 1.5), lambda x, y, q=py: y > q))
    cv.obj([pool], 1.)
    cv.hair(runs(hlines(pool, [sy - sry + .75 + i * 1.5 for i in range(int(sry * 2 / 1.5) + 1)]),
                 lambda x, y: math.hypot((x - sx) / srx, (y - sy) / sry) > .45))
    for f in (.22, .34):
        cv.hair(_ell_pts(sx, sy - sry * .05, srx * f, sry * f * 1.1, 16))

    tl = max(8., hw * 3.)
    toad(cv, sx - srx - tl * .45, sy + sry + tl * .45, tl, 1)

    for i in range(3 + 3 * det):
        lx = X + W * rng.uniform(.05, .95)
        ly = Y + H * rng.uniform(.05, .55)
        maple_leaf(cv, lx, ly, max(3., H * .034) * rng.uniform(.8, 1.2), rng.uniform(-1, 1))
    for i in range(2 + 2 * det):
        lx = X + W * rng.uniform(.05, .95)
        ly = gy + (Y + H - gy) * rng.uniform(.2, .9)
        if abs(lx - sx) > srx * 1.6:
            maple_leaf(cv, lx, ly, max(3., H * .036) * rng.uniform(.8, 1.1), rng.uniform(0, 2 * PI))


def scene_svg(X, Y, W, H, clip_d, seed, date, det, cid):
    cv = Canvas()
    scene(cv, X, Y, W, H, seed, date, det)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{cv.svg()}</g>'


def ground_leaves(cv, x, y, w, h, avoid, rng, n, s):
    """Autumn leaves drifting across the scroll ground (kept off the boxes in avoid)."""
    k = tries = 0
    placed = []
    while k < n and tries < n * 20:
        tries += 1
        lx, ly = x + rng.uniform(.03, .97) * w, y + rng.uniform(.15, .85) * h
        if any(a <= lx <= b and c <= ly <= d for a, c, b, d in avoid):
            continue
        if any(math.hypot(lx - a, ly - b) < s * 6 for a, b in placed):
            continue
        placed.append((lx, ly))
        maple_leaf(cv, lx, ly, s * rng.uniform(.85, 1.15), rng.uniform(-1.2, 1.2))
        k += 1


# ------------------------------------------------------------------------------------------------
# layouts (the house layouts, re-cut for this page)
# ------------------------------------------------------------------------------------------------

def _field(cx, cy, w, h):
    """The cartouche field, as C.cartouche computes it: half-axes and outline path."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b, _d(C._superellipse(cx, cy, a, b), True, 0)


def layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.3, 150)
    cvs = Canvas()
    C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh), cv=cvs)
    ground_leaves(cvs, 0, top, w, gh, [(w / 2 - gap * .6, 0, w / 2 + gap * .6, h)], random.Random(seed + 11),
                  4, max(4.5, gh * .09))
    o.append(C._clip(C._uid("wb", w, h, seed), 0, top, w, gh, cvs.svg()))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    ix, iy = rx - 2.5, ry - 2.5
    ring = _d(_ell_pts(cx, cy, ix, iy, 64), True, 0)
    o.append(scene_svg(cx - ix, cy - iy, 2 * ix, 2 * iy, ring, seed, date, 0, C._uid("wbs", w, h)))
    o.append(f'<path d="{ring}" stroke="#000" stroke-width="1" fill="none"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .4, gh * 2.0)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .065), rmax=r * .8,
                   max_n=14, edge=.7, cv=cv)
    cv.extend(main)
    lv = Canvas()
    ground_leaves(lv, 0, gy0, w, gh, [(cx - cw * .55, 0, cx + cw * .55, h)], random.Random(seed + 5), 6,
                  max(5., gh * .07))
    cv.extend(lv)
    o.append(C._clip(C._uid("wm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    a, b, fd = _field(cx, cy, cw, ch)
    o.append(c)
    o.append(scene_svg(cx - a, cy - b, 2 * a, 2 * b, fd, seed, date, 1, C._uid("wms", w, h)))
    o.append(f'<path d="{fd}" stroke="#000" stroke-width="1" fill="none"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    em = 12.
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    o.append(C.dark_ground((0, em, w, h - em), "G"))
    o.append(C.egg_and_dart(0, 0, w, em))
    px0, py0 = 6., em + 5
    pw = w - 12
    ph = h - py0 - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    lv = Canvas()
    ground_leaves(lv, px0, py0, pw, ph, [(cx - cw * .55, 0, cx + cw * .55, h)], random.Random(seed + 9), 9, 8.)
    cv.extend(lv)
    o.append(C._clip(C._uid("wt", w, h, seed), px0, py0, pw, ph, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    a, b, fd = _field(cx, cy, cw, ch)
    o.append(c)
    o.append(scene_svg(cx - a, cy - b, 2 * a, 2 * b, fd, seed, date, 2, C._uid("wts", w, h)))
    o.append(f'<path d="{fd}" stroke="#000" stroke-width="1" fill="none"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18, 52), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(letters_svg("TUCK EVERLASTING", 0, 0, bh * .5, centre=centre))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z" fill="{C.pat("L")}"/>')
    o.append(letters_svg("MCMXIV", tx + tw / 2, ty + th / 2 + .5, min(th * .66, 13), halo=True))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        fc = Canvas()
        C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2, cv=fc)
        o.append(C._clip(C._uid("wf", w, h, seed), 0, fy, w, fh - 2, fc.svg()))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 31 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = layout_band(w, h, seed, date)
    elif h <= 260:
        body = layout_medium(w, h, seed, date)
    else:
        body = layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
