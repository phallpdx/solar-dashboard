"""solar-04 "The grid this hour" (BPA, 88% carbon-free, hydro 75%).
Subject: Bonneville Dam spilling the Columbia under Mt. Hood, a lattice transmission tower carrying
the hydro power away, two gorge wind turbines (the 1%). The pedestal tablet engraves today's grid mix
as one banded bar (hydro / nuclear / gas / wind+solar), the ribbon reads 88% CARBON-FREE.
Easter egg: a Sauvie Island heron fishing the tailwater shallows, with a tiny P monogram on its bank stone."""
import sys
import math
import random
import engraving_codex as C

_n, _d = C._n, C._d


# ---------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------

def _wavy(segs, rng, amp=.6, wl=9., gap=.12, minlen=3.):
    """Turn straight hatch segments into broken, gently waving water lines."""
    out = []
    for (x0, y0), (x1, y1) in segs:
        L = x1 - x0
        if L < 1:
            continue
        x = x0
        while x < x1:
            run = rng.uniform(6, 26)
            xe = min(x1, x + run)
            if xe - x >= minlen or (x == x0 and xe == x1):
                n = max(2, int((xe - x) / 2) + 1)
                ph = rng.uniform(0, 6.3)
                out.append([(x + (xe - x) * i / (n - 1),
                             y0 + amp * math.sin((x + (xe - x) * i / (n - 1)) / wl * 6.283 + ph)) for i in range(n)])
            x = xe + (rng.uniform(1.5, 5) if rng.random() < gap * 3 else 1.2)
    return out


def _poly_clip_x(poly):
    return poly


def _sun(cv, cx, cy, r, x0, y0, x1, y1):
    disc = C._ell_pts(cx, cy, r, r, 40)
    for i in range(28):
        a = C.TAU * i / 28
        r1 = r * (1.9 if i % 2 else 2.6)
        p0 = (cx + r * 1.25 * math.cos(a), cy + r * 1.25 * math.sin(a))
        p1 = (cx + r1 * math.cos(a), cy + r1 * math.sin(a))
        p1 = (min(max(p1[0], x0), x1), min(max(p1[1], y0), y1))
        cv.hair([p0, p1])
    cv.obj([C._ell_pts(cx, cy, r * 1.18, r * 1.18, 40)], 0)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 3, .5, .3))
    # shading on the lower right of the disc
    cv.hair(C.hatch_poly(C._ell_pts(cx + r * .35, cy + r * .35, r * .7, r * .7, 30), 0, 3, 2., .3))


def _tower(cv, xc, yb, yt, wb, ext_left, wires_to_x, sag):
    """Lattice transmission tower; legs flare from top to base, two crossarms with insulators."""
    wt = wb * .22
    cv.obj([], 0)
    lv = 9
    pts = []
    for i in range(lv + 1):
        t = i / lv
        y = yt + (yb - yt) * t
        hw = wt / 2 + (wb - wt) / 2 * t ** 1.6
        pts.append((y, hw))
    L = [(xc - hw, y) for y, hw in pts]
    R = [(xc + hw, y) for y, hw in pts]
    cv.heavy(L)
    cv.heavy(R)
    for i in range(lv):
        cv.hair([L[i], R[i + 1]])
        cv.hair([R[i], L[i + 1]])
        cv.line([L[i + 1], R[i + 1]])
    # peak
    peak = (xc, yt - wb * .35)
    cv.line([L[0], peak, R[0]])
    tips = []
    for k, (ya, span) in enumerate(((yt + (yb - yt) * .1, wb * 1.15), (yt + (yb - yt) * .26, wb * 1.45))):
        a0, a1 = (xc - span, ya), (xc + span * .7, ya)
        cv.line([a0, a1])
        cv.hair([a0, (xc - wt * .8, ya - wb * .18)])
        cv.hair([a1, (xc + wt * .8, ya - wb * .14)])
        cv.hair([a0, (xc - wt / 2, ya + wb * .2)])
        cv.hair([a1, (xc + wt / 2, ya + wb * .2)])
        for x in (a0[0] + 1.5, a1[0] - 1.5):
            cv.line([(x, ya), (x, ya + 4)])
            for j in range(3):
                cv.hair([(x - 1.2, ya + 1 + j * 1.3), (x + 1.2, ya + 1 + j * 1.3)])
            tips.append((x, ya + 4))
    # wires: catenaries leaving to the left edge (to the city) and out the right
    for x, y in tips:
        if x < xc:
            n = 24
            pl = []
            for i in range(n + 1):
                t = i / n
                px = x + (wires_to_x - x) * t
                py = y + sag * 4 * t * (1 - t) + (t * sag * .35)
                pl.append((px, py))
            cv.line(pl)
        else:
            cv.line([(x, y), (x + ext_left, y + sag * .3)])


def _turbine(cv, x, yb, hgt, ang):
    cv.obj([], 0)
    hub = (x, yb - hgt)
    cv.line([(x - .6, yb), (x - .3, hub[1])])
    cv.line([(x + .6, yb), (x + .3, hub[1])])
    for k in range(3):
        a = ang + k * C.TAU / 3
        tip = (hub[0] + hgt * .62 * math.cos(a), hub[1] + hgt * .62 * math.sin(a))
        mid = (hub[0] + hgt * .25 * math.cos(a + .12), hub[1] + hgt * .25 * math.sin(a + .12))
        cv.line([hub, mid, tip])
    cv.obj([C._ell_pts(hub[0], hub[1], 1.1, 1.1, 8)], 1.)


def _heron(cv, x, y, s, rng):
    """Great blue heron standing, facing left, about 1.0*s tall; (x, y) = feet on the water."""
    body = [(x + s * (.05 + .22 * math.cos(a)), y - s * (.52 + .11 * math.sin(a) - .08 * math.cos(a))) for a in
            [C.TAU * i / 30 for i in range(30)]]
    # tail plumes drooping right
    tail = [(x + s * .2, y - s * .5), (x + s * .38, y - s * .36), (x + s * .3, y - s * .4), (x + s * .2, y - s * .44)]
    # legs
    cv.obj([], 0)
    cv.line([(x - s * .02, y - s * .44), (x - s * .04, y)])
    cv.line([(x + s * .06, y - s * .44), (x + s * .07, y - s * .02)])
    cv.obj([body, tail], 1.)
    cv.hair(C.hatch_poly(body, 25, 1.5, 0, .4))
    cv.hair(C.hatch_poly(tail, -30, 1.5, 0, .2))
    # wing edge
    cv.line([(x - s * .12, y - s * .6), (x + s * .1, y - s * .55), (x + s * .3, y - s * .42)])
    # S neck (a ribbon) + head
    neck = []
    for i in range(14):
        t = i / 13
        nx = x - s * .14 - s * .1 * math.sin(t * 3.4)
        ny = y - s * .58 - s * .36 * t
        neck.append((nx, ny))
    lw = [s * .045] * 14
    lpts = [(p[0] - w, p[1]) for p, w in zip(neck, lw)]
    rpts = [(p[0] + w, p[1]) for p, w in zip(neck, lw)]
    hx, hy = neck[-1]
    head = C._ell_pts(hx - s * .02, hy - s * .02, s * .07, s * .05, 16)
    cv.obj([lpts + rpts[::-1], head], 1.)
    cv.hair([(p[0] + .3, p[1]) for p in neck])
    # crest plume and beak
    cv.line([(hx + s * .03, hy - s * .04), (hx + s * .2, hy - s * .02)])
    beak = [(hx - s * .06, hy - s * .03), (hx - s * .3, hy + s * .01), (hx - s * .06, hy + s * .02)]
    cv.obj([beak], 1.)
    cv.obj([C._ell_pts(hx - s * .03, hy - s * .02, .8, .8, 6)], 1.)
    # reflection ripples
    for i in range(4):
        w = s * (.18 + .08 * i)
        cv.hair([(x - w + .03 * s, y + 1.5 + i * 2), (x + w * .8, y + 1.5 + i * 2)])


def _P_stone(cv, x, y, s):
    """A little bank stone with a cut 'P' monogram (the Easter egg's signature)."""
    st = C._ell_pts(x, y, s * 1.3, s * .8, 20)
    cv.obj([st], 1.)
    cv.hair(C.hatch_poly(C._ell_pts(x + s * .5, y + s * .3, s * 1.1, s * .6, 16), -40, 1.5))
    cv.line([(x - s * .35, y + s * .5), (x - s * .35, y - s * .5), (x + s * .2, y - s * .5),
             (x + s * .35, y - s * .3), (x + s * .2, y - s * .05), (x - s * .35, y - s * .05)])


# ---------------------------------------------------------------------------------------------
# the vignette: Bonneville Dam spilling under Mt. Hood
# ---------------------------------------------------------------------------------------------

def _scene(bx, by, bw, bh, seed):
    rng = random.Random(seed)
    X = lambda u: bx + bw * u
    Y = lambda v: by + bh * v
    big = bh > 70
    huge = bh > 150
    cv = C.Canvas()
    # sky: ruled, denser high up
    sky = [(X(-.05), Y(-.05)), (X(1.05), Y(-.05)), (X(1.05), Y(.6)), (X(-.05), Y(.6))]
    cv.obj([sky], 0)
    cv.hair(C.hatch_poly([(X(-.05), Y(-.05)), (X(1.05), Y(-.05)), (X(1.05), Y(.2)), (X(-.05), Y(.2))], 0, 2, .5))
    cv.hair(C.hatch_poly([(X(-.05), Y(.2) + .5), (X(1.05), Y(.2) + .5), (X(1.05), Y(.6)), (X(-.05), Y(.6))], 0, 3, .5))
    if big:
        # morning sun over the gorge
        _sun(cv, X(.24), Y(.17), bh * .065, X(-.05), Y(-.05), X(1.05), Y(.45))
        # streaks of cloud
        for (u, v, l) in ((.55, .07, .22), (.05, .3, .16), (.72, .22, .2)):
            cl = [(X(u) + bw * l * i / 20, Y(v) - bh * .012 * math.sin(math.pi * i / 20)) for i in range(21)]
            cl2 = [(X(u) + bw * l * i / 20, Y(v) + bh * .014) for i in range(20, -1, -1)]
            cv.obj([cl + cl2], 0)
            cv.hair(cl)
            cv.hair(C.hatch_poly(cl + cl2, 0, 1.5, .25, .4))
    # Mt. Hood
    hood_pk = (X(.6), Y(.13 if big else .22))
    hood = [(X(.32), Y(.5)), (X(.43), Y(.36)), (X(.5), Y(.28)), (X(.555), Y(.18)), hood_pk,
            (X(.625), Y(.16)), (X(.66), Y(.22)), (X(.72), Y(.3)), (X(.8), Y(.38)), (X(.9), Y(.5))]
    cv.obj([hood], 1.)
    sh = [hood_pk, (X(.625), Y(.16)), (X(.66), Y(.22)), (X(.72), Y(.3)), (X(.8), Y(.38)), (X(.9), Y(.5)),
          (X(.62), Y(.5)), (X(.6), Y(.3))]
    cv.hair(C.hatch_poly(sh, 70, 1.5))
    cv.hair(C.hatch_poly(hood, -35, 3, 1.))
    if big:
        # glacier gullies and ridge lines down the lit face
        for k in range(5):
            u = .47 + k * .03
            cv.line([(X(.6 - k * .004), Y(.17 + k * .02)), (X(u), Y(.3 + k * .025)), (X(u - .03), Y(.45))])
        cv.line([hood_pk, (X(.6), Y(.3)), (X(.62), Y(.5))])
    # timber skirt: dense, crossed
    skirt = [(X(.28), Y(.5)), (X(.4), Y(.4)), (X(.5), Y(.37)), (X(.6), Y(.39)), (X(.7), Y(.36)), (X(.85), Y(.42)),
             (X(.95), Y(.5))]
    cv.obj([skirt], .5)
    cv.hair(C.hatch_poly(skirt, 0, 1.5))
    cv.hair(C.hatch_poly(skirt, 80, 2, .7))
    # gorge walls, layered basalt
    lc = [(X(-.05), Y(.12 if big else .2)), (X(.05), Y(.15)), (X(.1), Y(.22)), (X(.17), Y(.27)), (X(.22), Y(.35)),
          (X(.3), Y(.42)), (X(.36), Y(.5)), (X(.4), Y(.56)), (X(-.05), Y(.7))]
    rc = [(X(1.05), Y(.28)), (X(.97), Y(.3)), (X(.9), Y(.33)), (X(.86), Y(.4)), (X(.8), Y(.46)), (X(.76), Y(.52)),
          (X(.72), Y(.56)), (X(1.05), Y(.7))]
    if big:
        _turbine(cv, X(.93), Y(.315), bh * .11, .4 + seed % 7 * .3)
        _turbine(cv, X(.99), Y(.29), bh * .09, 1.1 + seed % 5 * .4)
    for wall, side in ((lc, -1), (rc, 1)):
        cv.obj([wall], 1.)
        cv.hair(C.hatch_poly(wall, 62 * -side + 90 * (side > 0), 2))
        cv.hair(C.hatch_poly(wall, 0, 3, 1.))
        if big:
            top = wall[:-1]
            for k in range(1, 6):
                cv.line([(p[0] + side * k * bw * .012, p[1] + k * bh * .03) for p in top[1:]])
    # dam: deck, gantry, piers, spill
    d0, d1 = X(.2), X(.86)
    yd, yp, yf = Y(.5), Y(.535), Y(.66)
    deck = [(d0, yd), (d1, yd), (d1, yp), (d0, yp)]
    cv.obj([deck], 1.)
    cv.hair(C.hatch_poly(deck, 0, 1.5, .25, .3))
    cv.line([(d0, yd - 2), (d1, yd - 2)])
    for k in range(int((d1 - d0) / 4) + 1):
        cv.hair([(d0 + k * 4, yd - 2), (d0 + k * 4, yd)])
    if big:
        gx = d0 + (d1 - d0) * (.3 + (seed % 5) * .08)
        gh = bh * .06
        g = [(gx - 6, yd - 2), (gx - 4, yd - gh), (gx + 4, yd - gh), (gx + 6, yd - 2), (gx + 4, yd - 2), (gx + 3, yd - gh + 3),
             (gx - 3, yd - gh + 3), (gx - 4, yd - 2)]
        cv.obj([g], 1.)
        cv.hair(C.hatch_poly(g, 90, 1.5))
    npier = max(5, int((d1 - d0) / 14))
    pw = (d1 - d0) / npier
    for i in range(npier + 1):
        px = d0 + i * pw
        pr = [(px - pw * .16, yp), (px + pw * .16, yp), (px + pw * .2, yf + 2), (px - pw * .2, yf + 2)]
        if i < npier:
            # spillway curtain from the gate to the stilling basin
            xa, xb = px + pw * .16, px + pw * .84
            cv.obj([[(xa, yp), (xb, yp), (xb + pw * .05, yf + 2), (xa - pw * .05, yf + 2)]], 0)
            gate_b = yp + (yf - yp) * .28
            slot = [(xa, yp), (xb, yp), (xb, gate_b), (xa, gate_b)]
            cv.line(C.hatch_poly(slot, 0, 1.5, .25))
            cv.hair(C.hatch_poly(slot, 90, 1.5, .25))
            x = xa + .8
            while x < xb - .5:
                t0 = gate_b + rng.uniform(0, 2)
                n = 8
                pl = [(x + (x - (xa + xb) / 2) * .12 * (j / n) ** 2 + rng.uniform(-.2, .2), t0 + (yf + 1 - t0) * j / n)
                      for j in range(n + 1)]
                cut = rng.randrange(2, 7)
                cv.hair(pl[:cut])
                cv.hair(pl[cut + 1:])
                x += 1.5
        cv.obj([pr], 1.)
        cv.hair(C.hatch_poly([(px, yp), (px + pw * .16, yp), (px + pw * .2, yf + 2), (px, yf + 2)], 90, 1.5, .2))
    # powerhouse on the left bank end
    if big:
        ph = [(X(.12), Y(.53)), (X(.22), Y(.53)), (X(.22), Y(.65)), (X(.12), Y(.67))]
        cv.obj([ph], 1.)
        cv.hair(C.hatch_poly(ph, 0, 2, .5))
        for k in range(4):
            wx = X(.13) + k * bw * .023
            win = [(wx, Y(.56)), (wx + bw * .012, Y(.56)), (wx + bw * .012, Y(.61)), (wx, Y(.61))]
            cv.obj([win], 1.)
            cv.line(C.hatch_poly(win, 0, 1.5, .5))
    # foam in the stilling basin
    foam = [(X(.1), Y(.64))] + [(d0 + (d1 - d0) * i / 30 + (X(.08) if False else 0), Y(.645) - bh * .012 * abs(math.sin(i * 1.7)))
                                for i in range(31)] + [(X(.9), Y(.66)), (X(.92), Y(.71)), (X(.08), Y(.71))]
    cv.obj([foam], 0)
    fx = X(.1)
    while fx < X(.9):
        fy = Y(.66) + rng.uniform(-.01, .04) * bh
        r = rng.uniform(1.2, 2.6)
        a0 = rng.uniform(0, 6.3)
        cv.hair([(fx + r * math.cos(a0 + j * .5), fy + r * .6 * math.sin(a0 + j * .5)) for j in range(9)])
        fx += rng.uniform(1.6, 3.2)
    cv.hair(_wavy(C.hatch_poly(foam, 0, 3, 1.), rng, .4, 5))
    # tailwater: the Columbia rolling toward us
    river = [(X(-.05), Y(.69)), (X(1.05), Y(.69)), (X(1.05), Y(1.05)), (X(-.05), Y(1.05))]
    cv.obj([river], 0)
    segs = C.hatch_poly(river, 0, 2, .5)
    cv.hair(_wavy(segs, rng, .5, 10))
    # sun's glitter path under the sun
    if big:
        for k in range(int(bh * .3 / 2)):
            yy = Y(.7) + k * 2 + 1
            hw = 3 + k * .45
            cx = X(.3) + k * .3
            cv.line([(cx - hw * rng.uniform(.3, 1), yy), (cx + hw * rng.uniform(.2, .8), yy)])
    # near banks
    if big:
        lb = [(X(-.05), Y(.84)), (X(.1), Y(.86)), (X(.28), Y(.92)), (X(.4), Y(1.05)), (X(-.05), Y(1.05))]
        rb = [(X(1.05), Y(.72)), (X(.95), Y(.76)), (X(.8), Y(.86)), (X(.66), Y(.96)), (X(.6), Y(1.05)), (X(1.05), Y(1.05))]
        for b, ang in ((lb, 30), (rb, -50)):
            cv.obj([b], 1.)
            cv.hair(C.hatch_poly(b, ang, 1.5))
            cv.hair(C.hatch_poly(b, 0, 3, 1.))
            for k in range(14):
                i = rng.randrange(len(b) - 2)
                t = rng.random()
                p, q = b[i], b[i + 1]
                gx, gy = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                if bx < gx < bx + bw:
                    for j in range(3):
                        cv.line([(gx, gy), (gx + (j - 1) * 1.6, gy - rng.uniform(2.5, 5))])
        # transmission tower on the near bank
        _tower(cv, X(.84), Y(.9), Y(.16 if huge else .2), bw * .085, bw * .3, X(-.05), bh * .16)
        # heron in the shallows (Easter egg), with the P stone
        _heron(cv, X(.17), Y(.84), bh * .2, rng)
        if huge:
            _P_stone(cv, X(.31), Y(.93), max(3., bh * .022))
    else:
        # small plate: a lone pylon on the right bank
        rb = [(X(1.05), Y(.78)), (X(.85), Y(.9)), (X(.75), Y(1.05)), (X(1.05), Y(1.05))]
        cv.obj([rb], 1.)
        cv.hair(C.hatch_poly(rb, -50, 1.5))
        if bh > 40:
            _tower(cv, X(.88), Y(.92), Y(.18), bw * .07, bw * .2, X(-.05), bh * .08)
    return cv.svg()


# ---------------------------------------------------------------------------------------------
# path lettering for the ribbon
# ---------------------------------------------------------------------------------------------

_G = {  # 4 wide x 6 tall stroke glyphs, y down
    "8": [[(2, 0), (0.6, .6), (0.6, 2.2), (2, 3), (3.4, 2.2), (3.4, .6), (2, 0)],
          [(2, 3), (0.2, 3.8), (0.2, 5.3), (2, 6), (3.8, 5.3), (3.8, 3.8), (2, 3)]],
    "%": [[(3.8, 0), (0.2, 6)], [(1, .2), (.2, 1), (1, 1.8), (1.8, 1), (1, .2)], [(3, 4.2), (2.2, 5), (3, 5.8), (3.8, 5), (3, 4.2)]],
    "C": [[(3.8, 1), (2.8, 0), (1.2, 0), (0, 1.4), (0, 4.6), (1.2, 6), (2.8, 6), (3.8, 5)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "R": [[(0, 6), (0, 0), (2.8, 0), (3.8, .9), (3.8, 2.2), (2.8, 3), (0, 3)], [(2, 3), (4, 6)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5.1), (4, 3.9), (3, 3), (0, 3)], [(0, 0), (2.8, 0), (3.7, .8), (3.7, 2.2), (3, 3)]],
    "O": [[(2, 0), (.4, .8), (0, 3), (.4, 5.2), (2, 6), (3.6, 5.2), (4, 3), (3.6, .8), (2, 0)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "-": [[(.6, 3.2), (3.4, 3.2)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 2.9), (3, 2.9)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 2.9), (3, 2.9)]],
    " ": [],
}


def _letter_ribbon(centre, h, text):
    """Letters centred along the ribbon's centre line, as 1px strokes."""
    size = h * .52
    sc = size / 6
    adv = 5.4 * sc
    total = adv * len(text) - 1.4 * sc
    xs = [p[0] for p in centre]
    cx = (xs[0] + xs[-1]) / 2
    x = cx - total / 2
    d = []

    def yat(px):
        for (x0, y0), (x1, y1) in zip(centre, centre[1:]):
            if x0 <= px <= x1:
                return y0 + (y1 - y0) * (px - x0) / max(1e-6, x1 - x0)
        return centre[-1][1]
    for ch in text:
        ym = yat(x + 2 * sc)
        for st in _G.get(ch, []):
            d.append(_d([(x + gx * sc, ym - 3 * sc + gy * sc) for gx, gy in st], tol=0))
        x += adv
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width="1"/>'


def _mix_tablet(tx, ty, tw, th):
    """The pedestal tablet engraved with today's grid mix as one banded bar."""
    o = []
    o.append(f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-tw + 2)}z" fill="{C.pat("L")}" stroke="none"/>')
    bx, bw = tx + 8, tw - 16
    by, bh = ty + th * .25, th * .5
    parts = [(75, "G"), (13, "X"), (12, "D"), (1, "S")]
    x = bx
    tot = sum(p for p, _ in parts)
    seps = []
    for p, k in parts:
        w = max(2.5, bw * p / tot)
        o.append(f'<path d="M{_n(x)},{_n(by)}h{_n(w)}v{_n(bh)}h{_n(-w)}z" fill="#fff" stroke="none"/>')
        if k == "G":
            o.append(f'<path d="M{_n(x)},{_n(by)}h{_n(w)}v{_n(bh)}h{_n(-w)}z" fill="#000" stroke="none"/>')
            rng = random.Random(7)
            segs = C.hatch_poly([(x + 1, by + 1), (x + w - 1, by + 1), (x + w - 1, by + bh - 1), (x + 1, by + bh - 1)], 0, 2, 0)
            o.append(f'<path d="{"".join(_d(pl, tol=.2) for pl in _wavy(segs, rng, .5, 7))}" fill="none" stroke="#fff" stroke-width=".5"/>')
        else:
            o.append(f'<path d="M{_n(x)},{_n(by)}h{_n(w)}v{_n(bh)}h{_n(-w)}z" fill="{C.pat(k)}" stroke="none"/>')
        x += w
        seps.append(x)
    o.append(f'<path d="M{_n(bx)},{_n(by)}h{_n(x - bx)}v{_n(bh)}h{_n(bx - x)}z'
             + "".join(f"M{_n(s)},{_n(by)}v{_n(bh)}" for s in seps[:-1])
             + f'" fill="none" stroke="#000" stroke-width="1"/>')
    # end caps as small arrows
    o.append(f'<path d="M{_n(tx + 3)},{_n(by + bh / 2)}l3,-2.5v5zM{_n(tx + tw - 3)},{_n(by + bh / 2)}l-3,-2.5v5z" fill="#000" stroke="none"/>')
    return "".join(o)


def _field_bbox(dpath):
    import re
    nums = re.findall(r"-?[\d.]+", dpath)
    # path is M x,y l dx,dy ... (relative); rebuild absolute points
    vals = [float(v) for v in nums]
    x, y = vals[0], vals[1]
    xs, ys = [x], [y]
    for i in range(2, len(vals) - 1, 2):
        x += vals[i]
        y += vals[i + 1]
        xs.append(x)
        ys.append(y)
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def _clip_field(cid, dpath, body):
    return f'<clipPath id="{cid}"><path d="{dpath}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ---------------------------------------------------------------------------------------------
# layouts (house layouts, with the field engraved edge to edge and the tablet/ribbon carved)
# ---------------------------------------------------------------------------------------------

def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("sb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = C._d(C._ell_pts(cx, cy, rx - 4, ry - 4, 64), True)
    o.append(_clip_field(C._uid("sbf", w, h, seed), field,
                         _scene(cx - rx + 4, cy - ry + 4, 2 * rx - 8, 2 * ry - 8, seed)))
    o.append(f'<path d="{field}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed):
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("sm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_bbox(fd)
    o.append(_clip_field(C._uid("smf", w, h, seed), fd, _scene(fx, fy, fw, fh, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.dark_ground((0, 0, w, h), "S"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="{C.pat("S")}" stroke="none"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
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
                   max_n=10, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("st", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_bbox(fd)
    o.append(_clip_field(C._uid("stf", w, h, seed), fd, _scene(fx, fy, fw, fh, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_letter_ribbon(centre, bh, "88% CARBON-FREE"))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(_pedestal_under(0, py, w, ped_h))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_mix_tablet(tx, ty, tw, th))
    fy = py + ped_h
    fhh = h - fy
    if fhh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fhh - 2), "G"))
        o.append(C._clip(C._uid("sf", w, h, seed), w * .06, fy, w * .88, fhh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fhh - 2, rng.randrange(1 << 20), fhh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fhh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _pedestal_under(x, y, w, h):
    """White underlay matching the house pedestal's silhouette, so the plate's stipple ground
    shows only outside it (its ruled patterns are transparent)."""
    kb = max(5, min(10, h * .11))
    inset = w * .035
    slab = h * .42
    yy = y + kb + slab + kb
    ph = y + h - yy
    fl = [(x + inset * 1.2 - inset * 1.1 * (i / 12) ** 2.2, yy + ph * .7 * i / 12) for i in range(13)]
    fr = [(2 * x + w - p[0], p[1]) for p in fl[::-1]]
    pts = [(x, y), (x + w, y), (x + w, y + kb), (x + w - inset, y + kb), (x + w - inset, yy)] + fr + \
          [(x + w, yy + ph * .7), (x + w, y + h), (x, y + h), (x, yy + ph * .7)] + fl[::-1] + \
          [(x + inset, yy), (x + inset, y + kb), (x, y + kb)]
    return f'<path d="{_d(pts, True, 0)}" fill="#fff" stroke="none"/>'


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 4
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
