"""The sky (nearby): tonight's sunset over the Coast Range and the Columbia, the young moon
(its phase from ctx["date"]), Leonid meteors, an airliner with its contrail, and a heron on the
Sauvie Island bank. Easter egg: a tiny constellation of stars joined in the shape of a "P".
The house frame (engraving_codex.frame_plate) carries the scrollwork; the vignette fills the
whole carved field edge to edge (no blank paper)."""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d = C._n, C._d
K26 = 2 ** (-1 / 2.6)


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _thick(pts, w0, w1):
    """A tapered stroke as a closed polygon around polyline pts, width w0 -> w1."""
    n = len(pts)
    L, R = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        w = (w0 + (w1 - w0) * i / max(n - 1, 1)) / 2
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    return L + R[::-1]


def _bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def _star(cx, cy, r, ri=None, n=4, rot=0.):
    ri = ri or r * .3
    pts = []
    for i in range(2 * n):
        a = rot + math.pi * i / n
        rr = r if i % 2 == 0 else ri
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _hlines(x0, x1, y, rng, dash=(6, 30), gap=(1.5, 4)):
    """A broken horizontal line from x0 to x1 (engraved water)."""
    out = []
    x = x0 + rng.uniform(-6, 0)
    while x < x1:
        L = rng.uniform(*dash)
        a, b = max(x, x0), min(x + L, x1)
        if b - a > 1:
            out.append([(a, y), (b, y)])
        x += L + rng.uniform(*gap)
    return out


def _moon_age(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (datetime.datetime(d.year, d.month, d.day, 2) - datetime.datetime(2000, 1, 6, 18, 14)).total_seconds() / 86400
    return days % 29.530588


# ------------------------------------------------------------------------------------------------
# the vignette
# ------------------------------------------------------------------------------------------------

def _scene(field, X0, Y0, W, H, mode, ctx):
    """Engrave the evening sky into the field polygon (bbox X0,Y0,W,H). Returns SVG fragment
    (clipped to the field by the caller)."""
    date = (ctx or {}).get("date", "2026-11-11")
    rng = random.Random("sky" + date + mode)
    cv = C.Canvas()
    black = []          # solid silhouettes painted after the canvas
    whites = []         # small white highlights on the silhouettes
    small = mode == "band"
    hz = Y0 + H * (.6 if small else .6)          # horizon (top of the water)
    sun_x = X0 + W * (.5 if small else .44)
    R = min(W * .14, H * .19) if not small else H * .2

    # --- sky: ruled, darkest at the zenith, opening to the glow at the horizon --------------
    cv.obj([], 0)
    span = hz - Y0
    y = Y0 + .75
    while y < hz + 2:
        t = (y - Y0) / span
        if t < .3:
            cv.line([(X0 - 2, y), (X0 + W + 2, y)]); p = 2.
        elif t < .55:
            cv.hair([(X0 - 2, y), (X0 + W + 2, y)]); p = 1.5
        elif t < .8:
            cv.hair([(X0 - 2, y), (X0 + W + 2, y)]); p = 2.
        else:
            # glow: lines break away round the sun
            cv.hair([(X0 - 2, y), (X0 + W + 2, y)])
            p = 3.
        y += p
    # deep night corners: a crossing diagonal hatch in the upper sky
    top = [(X0 - 2, Y0 - 2), (X0 + W + 2, Y0 - 2), (X0 + W + 2, Y0 + span * .22), (X0 - 2, Y0 + span * .22)]
    cv.hair(C.hatch_poly(top, 60, 3))

    # --- rays of the setting sun -------------------------------------------------------------
    nr = 29 if not small else 13
    for i in range(nr):
        a = math.pi + math.pi * (i + .5) / nr
        if abs(math.sin(a)) < .12:
            continue
        r0 = R * 1.18
        r1 = R * (3.4 if i % 2 else 2.4) * (1 if not small else .8)
        hw = .03 if i % 2 else .05
        wedge = [(sun_x + r0 * math.cos(a - hw), hz + r0 * math.sin(a - hw)),
                 (sun_x + r1 * math.cos(a), hz + r1 * math.sin(a)),
                 (sun_x + r0 * math.cos(a + hw), hz + r0 * math.sin(a + hw))]
        cv.obj([wedge], .5)

    # --- (cloud banks tried and dropped: they read as bars across the rays) --------------------------------------------
    if False:
        for k in range(2):
            cy = Y0 + span * (.36 + .2 * k) + rng.uniform(-4, 4)
            cl = W * rng.uniform(.34, .5)
            cx = X0 + W * (.22 + .56 * ((k + rng.random() * .5) % 1.))
            th = 1.4 + .8 * rng.random()
            up = [(cx - cl / 2 + cl * i / 30, cy - th * math.sin(math.pi * i / 30) ** .7) for i in range(31)]
            dn = [(cx + cl / 2 - cl * i / 30, cy + th * .6 * math.sin(math.pi * i / 30)) for i in range(31)]
            poly = up + dn
            cv.obj([poly], .5)
            cv.heavy([(x, yy + .5) for x, yy in dn[4:-4]])
            # curled end
            ex = cx + cl / 2 * (1 if k % 2 else -1)
            sp = [(ex + math.cos(t) * th * (1 - t / 9) * (1 if k % 2 else -1), cy - th * .3 + math.sin(t) * th * (1 - t / 9))
                  for t in [i * .35 for i in range(18)]]
            cv.line(sp)

    # --- stars, and the "P" constellation (Easter egg) ---------------------------------------
    stars = []
    tries = 0
    nst = 18 if not small else 6
    while len(stars) < nst and tries < 400:
        tries += 1
        sx = X0 + W * rng.uniform(.06, .94)
        sy = Y0 + span * rng.uniform(.04, .5 if not small else .4)
        if math.hypot(sx - sun_x, sy - hz) < R * 3.6:
            continue
        if any(math.hypot(sx - a, sy - b) < 14 for a, b, _ in stars):
            continue
        stars.append((sx, sy, rng.choice((3., 3.6, 4.4, 5.4))))
    pcon = []
    if not small:
        px, py = X0 + W * .2, Y0 + span * .2
        s = max(6., min(W, H) * .036)
        pcon = [(px, py + 3.2 * s), (px, py + 1.6 * s), (px, py), (px + 1.3 * s, py + .1 * s),
                (px + 1.7 * s, py + .85 * s), (px + 1.2 * s, py + 1.55 * s)]
        stars = [st for st in stars if math.hypot(st[0] - px - s, st[1] - py - 1.6 * s) > 4 * s]
        for a, b in zip(pcon, pcon[1:] + [pcon[1]]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            m = int(L / 3)
            for j in range(1, m):
                if j % 2:
                    t0, t1 = j / m, (j + .6) / m
                    cv.obj([], 0)
                    cv.hair([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                             (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)])
    for sx, sy, r in stars:
        cv.obj([_star(sx, sy, r, r * .34, 4, rng.uniform(-.15, .15))], .5)
    for i, (sx, sy) in enumerate(pcon):
        cv.obj([_star(sx, sy, 3.6 if i in (0, 2, 4) else 2.8, 1., 4, .1)], .5)

    # --- Leonid meteors, from the radiant in the east (upper left of the plate) --------------
    nm = 3 if not small else 1
    for i in range(nm):
        hx = X0 + W * (.58 + .12 * i + rng.uniform(-.03, .03)) if not small else X0 + W * .72
        hy = Y0 + span * (.12 + .15 * i + rng.uniform(0, .05)) if not small else Y0 + span * .22
        L = (W * .17 if not small else W * .22) * (1 - .2 * i)
        a = math.radians(205 + rng.uniform(-5, 5))
        tx, ty = hx + L * math.cos(a), hy + L * math.sin(a)
        nx, ny = -math.sin(a), math.cos(a)
        wh = 1.6
        cv.obj([[(tx, ty), (hx + nx * wh, hy + ny * wh), (hx - nx * wh, hy - ny * wh)]], .5)
        cv.obj([_star(hx, hy, 3.6, 1.2, 4, .4)], .5)

    # --- the young moon (phase from the date) -------------------------------------------------
    age = _moon_age(date)
    mr = max(5., min(W, H) * .052) if not small else max(4., H * .1)
    mx, my = X0 + W * (.8 if not small else .2), Y0 + span * (.36 if not small else .3)
    disc = C._ell_pts(mx, my, mr, mr, 40)
    cv.obj([disc], .5)
    cv.line(C.hatch_poly(disc, 0, 1.5, .25))
    th = 2 * math.pi * age / 29.530588
    k = math.cos(th)
    waxing = age < 14.765
    k = min(k, .4)                      # always leave a readable sliver
    sgn = 1 if waxing else -1
    lit = []
    for i in range(25):
        yy = -1 + 2 * i / 24
        lit.append((mx + sgn * mr * math.sqrt(max(0, 1 - yy * yy)), my + mr * yy))
    for i in range(25):
        yy = 1 - 2 * i / 24
        lit.append((mx + sgn * k * mr * math.sqrt(max(0, 1 - yy * yy)), my + mr * yy))
    cv.obj([lit], 1.)
    cv.hair([[(x, yy) for x, yy in lit[:25]]])

    # --- an airliner and its contrail (planes overhead) -----------------------------------------
    if not small:
        ax, ay = X0 + W * .66, Y0 + span * .62
        ps = max(7., min(W, H) * .045)
        ca = math.radians(-12)
        cl = W * .4
        ux, uy = math.cos(ca), math.sin(ca)
        nx, ny = -uy, ux
        for off in (-1.6, 1.6):
            tr = [(ax - ux * ps + nx * off - ux * cl * t, ay - uy * ps + ny * off - uy * cl * t) for t in (0, 1)]
            trail = _thick(tr, 2.2, 5.5)
            cv.obj([trail], .5)
            cv.hair([[(x + nx * 0, y) for x, y in tr]])

        def P(u, v):
            return (ax + ux * u * ps + nx * v * ps, ay + uy * u * ps + ny * v * ps)
        fus = [P(1.1, 0), P(.9, -.12), P(-1, -.1), P(-1.1, 0), P(-1, .1), P(.9, .12)]
        wing = [P(.25, 0), P(-.25, -1.05), P(-.42, -1.05), P(-.15, 0), P(-.42, 1.05), P(-.25, 1.05)]
        tail = [P(-.8, 0), P(-1.05, -.4), P(-1.13, -.4), P(-1.05, 0), P(-1.13, .4), P(-1.05, .4)]
        black += [fus, wing, tail]

    # --- the Coast Range ------------------------------------------------------------------------
    rid = []
    nn = 60
    ph = rng.uniform(0, 6)
    for i in range(nn + 1):
        x = X0 - 2 + (W + 4) * i / nn
        t = i / nn
        hgt = H * (.05 + .03 * math.sin(t * 9 + ph) + .02 * math.sin(t * 23 + ph * 2)) * (1.25 - .5 * abs(t - .5))
        if small:
            hgt *= .7
        rid.append((x, hz - max(2, hgt)))
    hills = rid + [(X0 + W + 2, hz + 1), (X0 - 2, hz + 1)]
    # sun first, then the hills cover its foot
    sun = C._ell_pts(sun_x, hz, R, R, 56)
    # insert the sun before the hills in paint order: build its own object now
    cv.obj([sun], 1.5)
    for f in (.84, .66, .48):
        ring = C._ell_pts(sun_x, hz, R * f, R * f, 48)
        cv.hair([ring + [ring[0]]])
    cv.hair(C.hatch_poly(C._ell_pts(sun_x, hz, R * .3, R * .3, 24), 0, 1.5))
    cv.obj([hills], 1.)
    cv.hair(C.hatch_poly(hills, 0, 1.5, .25))
    cv.hair(C.hatch_poly(hills, 70, 3))
    # nearer ridge, a little lower and darker
    rid2 = [(x, y + (H * .03 if not small else H * .02) + 2 * math.sin(i * .7)) for i, (x, y) in enumerate(rid[::-1])]
    rid2 = [(X0 - 2 + (W + 4) * i / nn, hz - H * (.025 + .02 * math.sin(i / nn * 14 + ph * 3)) * (1 if not small else .6))
            for i in range(nn + 1)]
    h2 = rid2 + [(X0 + W + 2, hz + 1), (X0 - 2, hz + 1)]
    cv.obj([h2], .5)
    cv.line(C.hatch_poly(h2, 0, 2, .5))

    # --- the river: broken water lines, the sun's glitter path down the middle ------------------
    water = [(X0 - 2, hz), (X0 + W + 2, hz), (X0 + W + 2, Y0 + H + 2), (X0 - 2, Y0 + H + 2)]
    cv.obj([water], 0)
    y = hz + 1.5
    wr = random.Random("water" + date)
    while y < Y0 + H + 2:
        t = (y - hz) / (Y0 + H - hz + 1)
        gw = R * (.55 + 1.3 * t)
        p = 2. if t < .5 else 1.5
        for seg in _hlines(X0 - 2, sun_x - gw, y, wr, (8, 40), (1.5, 3.5)):
            cv.hair(seg)
        for seg in _hlines(sun_x + gw, X0 + W + 2, y, wr, (8, 40), (1.5, 3.5)):
            cv.hair(seg)
        # glitter: short dashes, sparse
        if True:
            for seg in _hlines(sun_x - gw, sun_x + gw, y, wr, (2, 7), (2, 4.5)):
                cv.hair(seg)
        y += p

    # --- Sauvie Island bank, reeds and a heron (on medium/tall) ---------------------------------
    if not small:
        by = Y0 + H * .86
        bank = [(X0 - 2, Y0 + H + 2)]
        for i in range(31):
            t = i / 30
            bank.append((X0 - 2 + W * .42 * t, by + H * .06 * t * t - 1.5 * math.sin(t * 11)))
        bank += [(X0 + W * .42, Y0 + H + 2)]
        cv.obj([bank], 1.)
        cv.line(C.hatch_poly(bank, 0, 1.5))
        bank2 = [(X0 + W + 2, Y0 + H + 2)]
        for i in range(31):
            t = i / 30
            bank2.append((X0 + W + 2 - W * .3 * t, by + H * .03 + H * .07 * t * t - 1.2 * math.sin(t * 9)))
        bank2 += [(X0 + W * .7, Y0 + H + 2)]
        cv.obj([bank2], 1.)
        cv.line(C.hatch_poly(bank2, 0, 1.5))
        # reeds and cattails
        rr = random.Random("reeds" + date)
        for x0, x1, base in ((X0 + W * .02, X0 + W * .36, by), (X0 + W * .76, X0 + W * .98, by + H * .04)):
            x = x0
            while x < x1:
                hgt = H * rr.uniform(.05, .13)
                lean = rr.uniform(-.25, .25)
                stem = [(x, base + 2), (x + lean * hgt * .5, base - hgt * .5), (x + lean * hgt, base - hgt)]
                black.append(_thick(stem, 1.3, .5))
                if rr.random() < .35:
                    tx, ty = stem[-1]
                    black.append(C._ell_pts(tx, ty + 3, 1.4, 3.2, 12))
                x += rr.uniform(3, 7)
        # the heron, standing in the shallows at the left: S-neck, dagger bill, long legs
        hs = H * .3
        fx, fy = X0 + W * .25, by + 1
        def Q(u, v):
            return (fx + u * hs, fy - v * hs)
        tilt = .5
        body = [Q(-.06 + .25 * math.cos(t) * math.cos(tilt) - .085 * math.sin(t) * math.sin(tilt),
                  .55 + .25 * math.cos(t) * math.sin(tilt) + .085 * math.sin(t) * math.cos(tilt))
                for t in [i * math.pi / 18 for i in range(36)]]
        neck = _bez(Q(.14, .63), Q(.26, .7), Q(.0, .8), Q(.12, .92), 20)
        black.append(body)
        black.append(_thick(neck, hs * .07, hs * .04))
        black.append(C._ell_pts(*Q(.135, .93), hs * .04, hs * .028, 16))
        black.append(_thick([Q(.165, .935), Q(.33, .9)], hs * .026, .5))          # bill
        black.append(_thick([Q(.11, .945), Q(-.02, .97), Q(-.1, .945)], 1.1, .5))  # crest plume
        black.append(_thick([Q(-.27, .44), Q(-.36, .38)], hs * .04, .8))           # tail
        black.append(_thick([Q(-.03, .48), Q(-.04, .26), Q(-.05, 0)], 1.4, 1.))    # legs
        black.append(_thick([Q(.03, .5), Q(.06, .25), Q(.08, .01)], 1.4, 1.))
        black.append(_thick([Q(.02, .66), Q(-.06, .58), Q(-.04, .5)], 2.2, .6))    # breast plumes
        whites.append(_thick([Q(-.24, .47), Q(-.05, .55), Q(.14, .6)], .5, 1.4))  # wing highlight
        whites.append(_thick([Q(-.2, .5), Q(.0, .57)], .4, 1.))
        whites.append(_thick(neck[4:16], .6, .4))
        whites.append(C._ell_pts(*Q(.145, .935), .8, .8, 8))
        # reflection of the heron: broken lines below
        for j in range(5):
            yy = fy + 3 + j * 2.5
            cv.obj([], 0)
            cv.line([(fx - hs * .05 - j * .5, yy), (fx + hs * .08, yy)])

    out = [cv.svg()]
    if black:
        out.append(f'<path d="{"".join(_d(p, True, .15) for p in black)}" fill="#000" stroke="none"/>')
    if whites:
        out.append(f'<path d="{"".join(_d(p, True, .15) for p in whites)}" fill="#fff" stroke="none"/>')
    return "".join(out)


def _wrap(field, X0, Y0, W, H, mode, ctx, cid):
    return (f'<clipPath id="{cid}"><path d="{_d(field, True, .1)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{_scene(field, X0, Y0, W, H, mode, ctx)}</g>')


def _moon_phase_glyph(cx, cy, r, f, waxing, black, whites, rings):
    """A moon at illuminated fraction f: black disc, white lit part."""
    black.append(C._ell_pts(cx, cy, r, r, 20))
    k = 1 - 2 * f
    sg = 1 if waxing else -1
    if f > .02:
        lit = [(cx + sg * r * .82 * math.sqrt(max(0, 1 - ((i / 10 - 1)) ** 2)), cy + r * .82 * (i / 10 - 1)) for i in range(21)]
        lit += [(cx + sg * k * r * .82 * math.sqrt(max(0, 1 - ((1 - i / 10)) ** 2)), cy + r * .82 * (1 - i / 10)) for i in range(21)]
        whites.append(lit)
    rings.append(C._ell_pts(cx, cy, r + 1.2, r + 1.2, 24))


def _banner_extra(centre, h, date):
    """Engrave the ribbon face: the month of moons, today's ringed, on a ruled face."""
    n = len(centre) - 1
    hl = []
    for off in (-h * .22, 0, h * .22):
        hl.append([(x, y + off) for x, y in centre[2:-2]])
    black, whites, rings = [], [], []
    age = _moon_age(date)
    m = 9
    L = centre[-1][0] - centre[0][0]
    bodies = []
    for j in range(m):
        t = (j + .5) / m
        i = int(t * n)
        cx, cy = centre[i]
        a = age + (j - m // 2) * 29.53 / m
        a %= 29.53
        f = (1 - math.cos(2 * math.pi * a / 29.53)) / 2
        r = h * .3
        bodies.append(C._ell_pts(cx, cy, r + 2.2, r + 2.2, 20))
        _moon_phase_glyph(cx, cy, r, f, a < 14.765, black, whites, rings if j == m // 2 else [])
    # ruled face behind the moons, clipped round them by a white backing
    o = [f'<path d="{"".join(_d(p, tol=.2) for p in hl)}" stroke="#000" stroke-width=".5" fill="none"/>',
         f'<path d="{"".join(_d(p, True, .15) for p in bodies)}" fill="#fff" stroke="none"/>',
         f'<path d="{"".join(_d(p, True, .15) for p in black)}" fill="#000" stroke="none"/>',
         f'<path d="{"".join(_d(p, True, .15) for p in whites)}" fill="#fff" stroke="none"/>']
    if rings:
        o.append(f'<path d="{"".join(_d(p + [p[0]], tol=.15) for p in rings)}" stroke="#000" stroke-width=".5" fill="none"/>')
    return "".join(o)


def _tablet_extra(tx, ty, tw, th, date):
    """Engrave the sunk tablet: the Leonids streaming from their radiant over a ruled night."""
    rng = random.Random("tab" + date)
    x0, y0, x1, y1 = tx + 2.5, ty + 2.5, tx + tw - 1, ty + th - 1
    cv = C.Canvas()
    cv.obj([], 0)
    y = y0 + .75
    while y < y1:
        cv.line([(x0, y), (x1, y)])
        y += 2.
    rx, ry = x0 + (x1 - x0) * .5, y0 + (y1 - y0) * .5
    for i in range(22):
        a = 2 * math.pi * i / 22 + rng.uniform(-.08, .08)
        r0 = (y1 - y0) * rng.uniform(.25, .45)
        L = (x1 - x0) * rng.uniform(.06, .2)
        cx, cy = rx + math.cos(a) * r0 * 2.6, ry + math.sin(a) * r0
        hx, hy = rx + math.cos(a) * (r0 * 2.6 + L), ry + math.sin(a) * (r0 + L * .38)
        if not (x0 + 3 < hx < x1 - 3 and y0 + 3 < hy < y1 - 3):
            continue
        ang = math.atan2(hy - cy, hx - cx)
        nx, ny = -math.sin(ang), math.cos(ang)
        cv.obj([[(cx, cy), (hx + nx * 1.1, hy + ny * 1.1), (hx - nx * 1.1, hy - ny * 1.1)]], .5)
    for i in range(14):
        sx, sy = rng.uniform(x0 + 4, x1 - 4), rng.uniform(y0 + 3, y1 - 3)
        cv.obj([_star(sx, sy, rng.choice((1.8, 2.4, 3.)), .6, 4, 0)], .5)
    cv.obj([_star(rx, ry, 4.5, 1.3, 4, 0), ], .5)
    cv.obj([_star(rx, ry, 3.2, 1., 4, math.pi / 4)], .5)
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 7
    cid = "skyv%dx%d" % (w, h)

    def fill(x, y, fw, fh):
        cx, cy = x + fw / 2, y + fh / 2
        if h < 110:
            rx, ry = fw / 2 / .7071 + 1, fh / 2 / .7071 + 1
            field = C._ell_pts(cx, cy, rx, ry, 64)
            mode = "band"
        else:
            a, b = fw / 2 / K26 + 6, fh / 2 / K26 + 6
            field = C._superellipse(cx, cy, a + .5, b + .5)
            rx, ry = a, b
            mode = "tall" if h > 260 else "medium"
        return _wrap(field, cx - rx, cy - ry, 2 * rx, 2 * ry, mode, ctx, cid)

    orig_banner, orig_ped = C.ribbon_banner, C.pedestal

    def banner(cx, cy, bw, bh, arch=.06, seed=0):
        svg, centre = orig_banner(cx, cy, bw, bh, arch, seed)
        return svg + _banner_extra(centre, bh, date), centre

    def ped(x, y, pw, ph, seed=0):
        svg, tab = orig_ped(x, y, pw, ph, seed)
        return svg + _tablet_extra(*tab, date), tab

    C.ribbon_banner, C.pedestal = banner, ped
    try:
        return C.frame_plate(w, h, seed, fill, density=.9 if h > 260 else 1.)
    finally:
        C.ribbon_banner, C.pedestal = orig_banner, orig_ped
