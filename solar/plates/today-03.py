"""today-03 "Weather at home - Your weather station says": Parker's own weather station at Bear Den
on Sauvie Island the morning after the storm. A carved cartouche holds the scene: the storm
(0.87 in) moving off east still trailing rain, a pale low sun (70 W/m2) through the wet air, the
station mast with its cup anemometer, a north-pointing vane, a louvred instrument screen, a little
solar panel and the rain gauge, standing in soaked pasture by the Multnomah Channel.
Easter egg: a great blue heron fishing in the reeds of the channel edge, Mt. Hood on the skyline."""
import sys
import math
import random
import engraving_codex as C

TAU = 2 * math.pi


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _rot(pts, cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def _cloud(x0, x1, base, bumps):
    """Bumpy cumulus outline: bumps = [(cx, r)] sitting on base. Returns (poly, top_fn)."""
    def top(x):
        y = base
        for bx, r in bumps:
            dx = x - bx
            if abs(dx) < r:
                y = min(y, base - r * .35 - math.sqrt(r * r - dx * dx) * 1.05)
        return y
    n = max(8, int((x1 - x0) / 1.5))
    pts = [(x0 + (x1 - x0) * i / n, top(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]
    pts = [p for p in pts if p[1] < base - .3] or pts
    return [(pts[0][0], base)] + pts + [(pts[-1][0], base)], top


def _wavy_lines(poly, pitch, amp, freq, phase, rng, broken=0.):
    """Horizontal lines clipped to poly, with a gentle wave; optionally broken into dashes."""
    out = []
    for seg in C.hatch_poly(poly, 0, pitch, phase):
        (a, y), (b, _) = seg
        if b - a < 1:
            continue
        n = max(2, int((b - a) / 3))
        pts = [(a + (b - a) * i / n, y + amp * math.sin((a + (b - a) * i / n) * freq + y * .7)) for i in range(n + 1)]
        if broken:
            cur = []
            for p in pts:
                cur.append(p)
                if len(cur) > 2 and rng.random() < broken:
                    out.append(cur)
                    cur = []
            if len(cur) > 1:
                out.append(cur)
        else:
            out.append(pts)
    return out


# ------------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------------

def _scene(X, Y, W, H, seed, detail=1.):
    """Draw the station scene into the box (X, Y, W, H). Returns (canvas_svg, black_svg)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    blk = []                                     # solid black accents, drawn on top
    u = lambda t: X + W * t
    v = lambda t: Y + H * t
    s = min(W, H * 1.6) / 200.                   # figure scale
    hz = v(.60)                                  # horizon (far bank)

    # --- sky: ruled, darker up top where the storm still sits -----------------------------------
    sky = _rect(X - 2, Y - 2, X + W + 2, hz + 1)
    cv.obj([sky], 0)
    cv.hair(C.hatch_poly(sky, 0, 2, .5))
    # rain sweeping off to the east under the storm
    rain = []
    for i in range(int(W * .42 / 2.2)):
        x = u(.58) + i * 2.2 + rng.uniform(-.4, .4)
        y0 = v(.36) + rng.uniform(0, H * .05)
        y = y0
        while y < hz - 2:
            L = rng.uniform(3, 7)
            rain.append([(x, y), (x - L * .35, min(hz - 1, y + L))])
            x -= (L + 2) * .35
            y += L + 2
    cv.hair(rain)

    # --- the low sun through wet air ------------------------------------------------------------
    sx, sy, sr = u(.27), v(.36), 9 * s
    halo = C._ell_pts(sx, sy, sr * 1.9, sr * 1.9, 48)
    cv.obj([halo], 0)
    cv.hair(C.hatch_poly(halo, 0, 3, 0))
    rays = []
    for i in range(28):
        a = TAU * i / 28
        r1 = sr * (2.0 if i % 2 else 2.5) + (rng.uniform(0, 3) * s)
        rays.append([(sx + sr * 1.3 * math.cos(a), sy + sr * 1.3 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    cv.hair(rays)
    disc = C._ell_pts(sx, sy, sr, sr, 40)
    cv.obj([disc], 1.)
    cv.hair([seg for seg in C.hatch_poly(disc, 0, 3, 1) if seg[0][1] > sy - sr * .2])
    cv.hair(C._ell_pts(sx, sy, sr * 1.3, sr * 1.3, 40) + [C._ell_pts(sx, sy, sr * 1.3, sr * 1.3, 40)[0]])

    # --- clouds: the storm bank moving off east, a few rags in the west -------------------------
    def billow(bx, by, r, base, dark):
        poly = [(x, min(y, base)) for x, y in C._ell_pts(bx, by, r, r * .9, 36)]
        cv.obj([poly], 1.)
        # crescent of contour lines on the shadow side (light comes from the low sun, upper left)
        arcs = []
        j = 1
        while r - j * 1.5 > 1.5:
            rr = r - j * 1.5
            spread = (1.45 if dark else 1.15) - j * (.16 if dark else .22)
            if spread <= .1:
                break
            c0 = .85
            seg = [(bx + rr * math.cos(c0 + spread * (i / 10 * 2 - 1)), by + rr * .9 * math.sin(c0 + spread * (i / 10 * 2 - 1)))
                   for i in range(11)]
            seg = [q for q in seg if q[1] < base - .6]
            if len(seg) > 1:
                arcs.append(seg)
            j += 1
        cv.hair(arcs)
        lit = [sg for sg in C.hatch_poly(poly, 0, 3, 1.0)]
        cv.hair(lit)
        if dark:
            cv.hair([sg for sg in C.hatch_poly(poly, 0, 3, 2.5) if sg[0][1] > by + r * .1])

    def cloud(x0, x1, base, rmin, rmax, dark):
        mid, half = (x0 + x1) / 2, (x1 - x0) / 2
        back, front = [], []
        x = x0 + rmin
        while x < x1 - rmin * .6:
            q = 1 - ((x - mid) / half) ** 2
            r = rmin + (rmax - rmin) * q * rng.uniform(.75, 1.)
            back.append((x, base - r * .55 - rmax * .55 * q, r))
            x += r * rng.uniform(.8, 1.05)
        x = x0 + rmin * .8
        while x < x1 - rmin * .5:
            r = rmin * rng.uniform(.7, 1.05)
            front.append((x, base - r * .45, r))
            x += r * rng.uniform(1.1, 1.5)
        for bx, by, r in sorted(back, key=lambda t: t[1]):
            billow(bx, by, r, base, dark)
        for bx, by, r in front:
            billow(bx, by, r, base, dark)
        if dark:  # flat shadowed base of the storm
            belly = _rect(x0 + rmin * .4, base - 3 * s, x1 - rmin * .4, base)
            cv.obj([belly], .5)
            cv.hair(C.hatch_poly(belly, 0, 1.5, 0))
            cv.hair(C.hatch_poly(belly, 60, 3, 0))

    cloud(u(.5), u(1.12), v(.36), 7 * s, 15 * s, True)
    cloud(u(-.06), u(.16), v(.26), 4 * s, 7 * s, False)
    cloud(u(.32), u(.50), v(.20), 3.5 * s, 6 * s, False)

    # --- Mt. Hood on the skyline (egg) ---------------------------------------------------------
    mx, mh = u(.43), 22 * s
    mtn = [(mx - 40 * s, hz + 1), (mx - 16 * s, hz - mh * .55), (mx - 5 * s, hz - mh * .93), (mx, hz - mh),
           (mx + 4 * s, hz - mh * .9), (mx + 18 * s, hz - mh * .5), (mx + 44 * s, hz + 1)]
    cv.obj([mtn], 1.)
    sun_side = [(mx, hz - mh), (mx - 2 * s, hz - mh * .6), (mx + 3 * s, hz - mh * .35), (mx + 1 * s, hz + 1),
                (mx + 44 * s, hz + 1), (mx + 18 * s, hz - mh * .5), (mx + 4 * s, hz - mh * .9)]
    cv.hair(C.hatch_poly(sun_side, 60, 1.5, 0))
    snow_line = []
    for i in range(9):
        t = i / 8
        xx = mx - 14 * s + 30 * s * t
        snow_line.append((xx, hz - mh * .55 + 2.5 * s * math.sin(t * 11)))
    lower = [(mx - 40 * s, hz + 1)] + snow_line + [(mx + 44 * s, hz + 1)]
    cv.hair(C.hatch_poly(lower, 0, 1.5, .5))
    # far hills (Tualatin / West Hills) low and long
    hills = [(X - 2, hz + 1)] + [(u(i / 40), hz - (4 + 3 * math.sin(i * .5) + 2 * math.sin(i * 1.7)) * s) for i in range(41)] + [(X + W + 2, hz + 1)]
    hills = [(x, y) for x, y in hills]
    cv.obj([hills[:15] + [(u(.34), hz + 1)]], 1.)
    cv.hair(C.hatch_poly(hills[:15] + [(u(.34), hz + 1)], 0, 1.5, 0))
    cv.obj([[(u(.56), hz + 1)] + hills[23:]], 1.)
    cv.hair(C.hatch_poly([(u(.56), hz + 1)] + hills[23:], 0, 1.5, 0))
    # tree line on the far bank: little cottonwood crowns
    trees = []
    tx = X
    while tx < X + W:
        r = rng.uniform(2.2, 4.5) * s
        if not (u(.33) < tx < u(.55)):
            trees.append((tx, r))
        tx += r * 1.3
    for tx, r in trees:
        cr = C._ell_pts(tx, hz - r * .9, r, r * 1.2, 14)
        cv.obj([cr], .5)
        cv.hair(C.hatch_poly(cr, 75, 1.5, 0))

    # --- the Multnomah Channel ------------------------------------------------------------------
    wy0, wy1 = hz + 1, v(.70)
    water = _rect(X - 2, wy0, X + W + 2, wy1)
    cv.obj([water], 0)
    cv.hair(_wavy_lines(water, 1.5, .35, .8, 0, rng, .12))
    # glint of the sun on the water
    cv.obj([_rect(sx - 6 * s, wy0 + 1, sx + 6 * s, wy1 - 1)], 0)
    cv.hair(_wavy_lines(_rect(sx - 6 * s, wy0 + 1, sx + 6 * s, wy1 - 1), 3, .3, .9, 1, rng, .4))

    # --- pasture: soaked grass rising toward us ------------------------------------------------
    gtop = lambda x: wy1 - (2.5 + 2 * math.sin((x - X) / W * 5.0 + seed % 7)) * s
    ground = [(X - 2, Y + H + 2)] + [(u(i / 50), gtop(u(i / 50))) for i in range(51)] + [(X + W + 2, Y + H + 2)]
    cv.obj([ground], 1.)
    cv.hair(_wavy_lines(ground, 2, .5, .35, 1, rng, .08))
    # grass tufts rows, denser and longer toward the foreground
    tufts = []
    gy0 = wy1 + 2
    n_t = int(W * (Y + H - gy0) / 55)
    for _ in range(n_t):
        depth = rng.random() ** .7
        yy = gy0 + 3 + depth * (Y + H - gy0)
        x = X + rng.uniform(0, W)
        L = (2 + 7 * depth) * s * rng.uniform(.6, 1.2)
        nb = 3 + int(depth * 3)
        for kb in range(nb):
            t = kb / (nb - 1) * 2 - 1
            lean = t * L * .45 + rng.uniform(-.6, .6)
            tufts.append([(x + t * .9, yy), (x + t * .9 + lean * .35, yy - L * .55), (x + t * .9 + lean, yy - L * (1 - .3 * abs(t)))])
    cv.hair(tufts)
    # a puddle by the gauge
    pud = C._ell_pts(u(.82), v(.86), 16 * s, 3 * s, 24)
    cv.obj([pud], .5)
    cv.hair(C.hatch_poly(pud, 0, 1.5, 0))

    # --- the great blue heron in the reeds (left, channel edge) ---------------------------------
    hx, hy = u(.12), wy1 + 1 * s           # feet
    k = s * .85
    P = lambda a, b: (hx + a * k, hy + b * k)
    body = [P(-15, -15), P(-9, -20), P(-1, -25), P(5, -28), P(9, -27), P(10, -24), P(6, -19), P(-1, -16),
            P(-8, -14), P(-16, -12), P(-19, -12)]
    neck = [P(6, -27), P(9, -31), P(8, -35), P(7, -38), P(9, -42), P(13, -44), P(15, -43), P(13, -41),
            P(11, -39), P(11, -36), P(12, -31), P(10, -25)]
    legs = [[P(-1, -16), P(-2, -8), P(-1, 0)], [P(3, -18), P(4, -9), P(6, 0)]]
    cv.hair(legs)
    cv.obj([body], 1.)
    feathers = []
    for j in range(6):
        t = j / 5
        feathers.append([P(-15 + 17 * t, -13.5 - 1 * t), P(-8 + 12 * t, -18 - 4 * t), P(-2 + 8 * t, -21 - 4 * t)])
    cv.hair(feathers)
    cv.hair(C.hatch_poly(body, 25, 1.5, 0))
    cv.obj([neck], 1.)
    cv.hair([[P(8, -29), P(9.5, -33), P(9, -37)], [P(10, -26), P(11, -31), P(10.5, -35)]])  # throat plumes
    cv.line([[P(14.5, -43.5), P(24, -41)], [P(14.5, -42.3), P(23.5, -41)]])      # dagger bill
    blk.append(C._d([P(10, -44.5), P(14, -45), P(7, -46.5), P(4, -45)], True))  # crest plume
    eye = P(13, -43.7)
    blk.append(C._d(C._ell_pts(eye[0], eye[1], .7, .7, 8), True))
    # ripple rings round its legs
    cv.hair([C._ell_pts(hx + 3 * k, hy + .5, 6 * k, 1.3 * k, 20, math.pi * .1, math.pi * .9)])
    # reeds and cattails in front of and around it
    reeds = []
    for j in range(16):
        rx = hx + (j - 8) * 2.6 * k + rng.uniform(-1, 1)
        if abs(rx - hx - 2 * k) < 6 * k and j % 3:
            continue
        L = rng.uniform(14, 30) * k
        bend = rng.uniform(-5, 5) * k
        pts = [(rx + bend * (i / 6) ** 2, hy + 4 * k - L * i / 6) for i in range(7)]
        reeds.append(pts)
        if j % 4 == 1:
            tip = pts[-2]
            blk.append(C._d(C._ell_pts(tip[0] + bend * .1, tip[1], 1.1 * k, 3.2 * k, 10), True))
    cv.obj([], 0)
    cv.hair(reeds)

    # --- the weather station ------------------------------------------------------------------
    bx, by = u(.66), v(.90)          # foot of mast
    top_y = v(.21)
    pw = 1.6 * s
    mast = _rect(bx - pw, top_y, bx + pw, by)
    # guy wires
    cv.obj([], 0)
    cv.hair([[(bx, top_y + (by - top_y) * .35), (bx - 30 * s, by + 3 * s)],
             [(bx, top_y + (by - top_y) * .35), (bx + 34 * s, by + 2 * s)]])
    cv.obj([mast], 1.)
    cv.hair([[(bx + pw * .35 + i * .5, top_y + 1), (bx + pw * .35 + i * .5, by)] for i in range(2)])
    # mast bands
    cv.hair([[(bx - pw, y), (bx + pw, y)] for y in [top_y + (by - top_y) * f for f in (.3, .55, .8)]])
    # footing
    foot = _rect(bx - 6 * s, by - 2 * s, bx + 6 * s, by + 2.5 * s)
    cv.obj([foot], 1.)
    cv.hair(C.hatch_poly(foot, 0, 1.5, 0))

    # crossarm
    ay = top_y + 9 * s
    arm = _rect(bx - 24 * s, ay - 1 * s, bx + 24 * s, ay + 1 * s)
    cv.obj([arm], 1.)
    cv.hair(C.hatch_poly(arm, 0, 1.5, .5))
    # wind vane on the left end: pointing NORTH into today's 9 mph north wind (left = north)
    vx, vy = bx - 22 * s, ay - 1 * s
    cv.obj([_rect(vx - .6 * s, vy - 7 * s, vx + .6 * s, vy)], .5)
    vane_y = vy - 7 * s
    shaft = _rect(vx - 12 * s, vane_y - .5 * s, vx + 12 * s, vane_y + .5 * s)
    cv.obj([shaft], .5)
    head = [(vx - 16 * s, vane_y), (vx - 10 * s, vane_y - 3.5 * s), (vx - 11 * s, vane_y), (vx - 10 * s, vane_y + 3.5 * s)]
    blk.append(C._d(head, True))
    tail = [(vx + 7 * s, vane_y), (vx + 15 * s, vane_y - 6 * s), (vx + 17 * s, vane_y - 6 * s), (vx + 15 * s, vane_y),
            (vx + 17 * s, vane_y + 3 * s), (vx + 15 * s, vane_y + 3 * s)]
    cv.obj([tail], 1.)
    cv.hair(C.hatch_poly(tail, 90, 1.5, 0))
    # N letter drawn as strokes on a tiny arm under the vane
    nx, ny = vx, vy - 3 * s
    cv.obj([], 0)
    cv.line([[(nx - 6 * s, ny + 2 * s), (nx - 6 * s, ny - 2 * s), (nx - 3.5 * s, ny + 2 * s), (nx - 3.5 * s, ny - 2 * s)]])
    # anemometer on the right end: hub + three cups
    axx, axy = bx + 20 * s, ay - 1 * s
    cv.obj([_rect(axx - .6 * s, axy - 6 * s, axx + .6 * s, axy)], .5)
    hub_y = axy - 6 * s
    for j in range(3):
        a = TAU * j / 3 + .5 + (seed % 10) * .1
        ex, ey = axx + 10 * s * math.cos(a), hub_y + 3 * s * math.sin(a)
        cv.obj([], 0)
        cv.line([[(axx, hub_y), (ex, ey)]])
        facing = math.sin(a) > 0
        cup = C._ell_pts(ex, ey, 3.4 * s, 3 * s, 16, -math.pi / 2, math.pi / 2) if math.cos(a + .6) > 0 else \
            C._ell_pts(ex, ey, 3.4 * s, 3 * s, 16, math.pi / 2, 1.5 * math.pi)
        cv.obj([cup], 1.)
        if facing:
            blk.append(C._d(cup, True))
        else:
            cv.hair(C.hatch_poly(cup, 90, 1.5, 0))
    hub = C._ell_pts(axx, hub_y, 1.6 * s, 1.2 * s, 10)
    blk.append(C._d(hub, True))

    # instrument screen (Stevenson box) with louvres and a pitched roof
    sx0, sy0, sw_, sh_ = bx + pw, top_y + (by - top_y) * .42, 15 * s, 14 * s
    box = _rect(sx0, sy0, sx0 + sw_, sy0 + sh_)
    cv.obj([box], 1.)
    lv = []
    yy = sy0 + 1.5
    while yy < sy0 + sh_ - .8:
        lv.append([(sx0 + .8, yy), (sx0 + sw_ - .8, yy + .9)])
        yy += 1.5
    cv.hair(lv)
    cv.hair([[(sx0 + sw_ * .5, sy0), (sx0 + sw_ * .5, sy0 + sh_)]])
    roof = [(sx0 - 1.5 * s, sy0), (sx0 + sw_ * .5, sy0 - 4 * s), (sx0 + sw_ + 1.5 * s, sy0)]
    cv.obj([roof], 1.)
    cv.hair(C.hatch_poly(roof, 0, 1.5, 0))
    # a stand leg under it
    cv.obj([_rect(sx0 + sw_ * .5 - .6, sy0 + sh_, sx0 + sw_ * .5 + .6, sy0 + sh_ + 3 * s)], .5)

    # small solar panel on the left of the mast, tilted south (toward us) - dark glass, light grid
    py0 = top_y + (by - top_y) * .5
    sp = [(bx - pw - 15 * s, py0 + 2 * s), (bx - pw - 2 * s, py0 - 3 * s), (bx - pw - 2 * s, py0 + 6 * s), (bx - pw - 15 * s, py0 + 11 * s)]
    cv.obj([], 0)
    cv.line([[(bx - pw - 8 * s, py0 + 4 * s), (bx - pw, py0 + 4 * s)]])
    cv.obj([sp], 1.)
    cv.hair(C.hatch_poly(sp, 0, 1.5, 0))
    cv.hair(C.hatch_poly(sp, 90, 1.5, .75))
    cv.line([[(bx - pw - 15 * s + 13 * s * t, py0 + 2 * s - 5 * s * t), (bx - pw - 15 * s + 13 * s * t, py0 + 11 * s - 5 * s * t)] for t in (1 / 3, 2 / 3)])
    cv.line([[(bx - pw - 15 * s, py0 + 6.5 * s), (bx - pw - 2 * s, py0 + 1.5 * s)]])

    # rain gauge on its own post to the right: the cylinder that measured 0.87 in
    gx, gy = u(.84), v(.80)
    cv.obj([_rect(gx - 1.2 * s, gy, gx + 1.2 * s, v(.88))], 1.)
    cv.hair(C.hatch_poly(_rect(gx - 1.2 * s, gy, gx + 1.2 * s, v(.88)), 90, 1.5, 0))
    cyl = [(gx - 4 * s, gy - 20 * s)] + C._ell_pts(gx, gy - 20 * s, 4 * s, 1.3 * s, 12, math.pi, 0)[:0] + \
        [(gx + 4 * s, gy - 20 * s), (gx + 4 * s, gy)] + C._ell_pts(gx, gy, 4 * s, 1.3 * s, 12, 0, math.pi) + [(gx - 4 * s, gy)]
    cv.obj([cyl], 1.)
    cv.hair([[(gx + i * 1.5, gy - 19 * s), (gx + i * 1.5, gy + .8 * s)] for i in range(0, int(4 * s / 1.5) + 1)])
    # graduations up the left side (the "0.87" storm mark heavier)
    cv.hair([[(gx - 4 * s, gy - 3 * s - i * 2), (gx - 2.5 * s, gy - 3 * s - i * 2)] for i in range(int(14 * s / 2))])
    rim = C._ell_pts(gx, gy - 20 * s, 4.6 * s, 1.5 * s, 16)
    cv.obj([rim], 1.)
    blk.append(C._d(C._ell_pts(gx, gy - 20 * s, 3.4 * s, .9 * s, 14), True))
    # drops still falling from the vane & a few drips off the gauge rim
    cv.obj([], 0)
    drops = []
    for j in range(5):
        dx = gx + rng.uniform(-5, 5) * s
        dy = gy - rng.uniform(26, 40) * s
        drops.append(C._d([(dx, dy - 2 * s), (dx + .9 * s, dy + .5 * s), (dx, dy + 1.4 * s), (dx - .9 * s, dy + .5 * s)], True))
    blk.extend(drops)

    return cv.svg(), "".join(f'<path d="{d}" fill="#000" stroke="none"/>' for d in blk)


def _field_vignette(field_pts, seed, uid):
    """Fill the whole cartouche field (no white) with the scene, clipped to the field outline."""
    xs = [p[0] for p in field_pts]
    ys = [p[1] for p in field_pts]
    X, Y, W, H = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    body, blk = _scene(X, Y, W, H, seed)
    d = C._d(field_pts, True, 0)
    return (f'<clipPath id="{uid}"><path d="{d}"/></clipPath>'
            f'<g clip-path="url(#{uid})"><path d="{d}" fill="#fff" stroke="none"/>{body}{blk}</g>')


# ------------------------------------------------------------------------------------------------
# layouts
# ------------------------------------------------------------------------------------------------

def _medium(w, h, seed):
    """House medium layout, but with a wider cartouche for the landscape and the whole field engraved."""
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .5, gh * 1.9)
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
    o.append(C._clip(C._uid("m3", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(_field_vignette(C._superellipse(cx, cy, a + .5, b + .5), seed, C._uid("v3", w, h, seed)))
    # re-lay the bead row over the scene edge so the carving reads on top
    bp = C._superellipse(cx, cy, a - 3.2, b - 3.2)
    o.append(f'<path d="{C._d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#fff" stroke-width="2.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')
    o.append(f'<path d="{C._d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return C.svg_doc(w, h, "".join(o))


def _amounts(ctx):
    """Storm / week / month rain from the page text (fallbacks keep it drawable)."""
    import re
    t = (ctx or {}).get("sample", "") or ""
    def num(label, dflt):
        m = re.search(label + r"\s*([0-9]+(?:\.[0-9]+)?)\s*in", t)
        return float(m.group(1)) if m else dflt
    return num("This storm", .87), num("This month", 1.31), num("Since your gauge started", 4.24)


def _gauge_tablet(tx, ty, tw, th, storm, month):
    """Inside the pedestal tablet: an engraved rain-gauge scale 0-2 in, the storm's rain cut solid,
    the month's total ruled, every tenth ticked, every half inch a long tick."""
    cv = C.Canvas()
    x0, x1 = tx + 6, tx + tw - 6
    ym = ty + th / 2
    bh = max(3., th * .32)
    full = 2.0
    X = lambda v: x0 + (x1 - x0) * min(v, full) / full
    back = C._rect(tx + 1, ty + 1, tx + tw - 1, ty + th - 1) if hasattr(C, "_rect") else _rect(tx + 1, ty + 1, tx + tw - 1, ty + th - 1)
    cv.obj([back], 0)
    cv.hair(C.hatch_poly(back, 0, 2, .5))
    tube = _rect(x0, ym - bh / 2, x1, ym + bh / 2)
    cv.obj([tube], 1.)
    cv.hair(C.hatch_poly(_rect(x0, ym - bh / 2, X(month), ym + bh / 2), 90, 1.5, 0))
    ticks = []
    for i in range(int(full * 10) + 1):
        xx = X(i / 10)
        L = th * (.42 if i % 5 == 0 else .26)
        ticks.append([(xx, ym - bh / 2 - .3), (xx, ym - bh / 2 - L * .45)])
        ticks.append([(xx, ym + bh / 2 + .3), (xx, ym + bh / 2 + L * .45)])
    cv.line(ticks)
    out = cv.svg()
    out += f'<path d="{C._d(_rect(x0, ym - bh / 2, X(storm), ym + bh / 2), True, 0)}" fill="#000" stroke="none"/>'
    # a raindrop marks the storm's level
    dx, dy = X(storm), ym - bh / 2 - th * .22
    out += f'<path d="{C._d([(dx, dy - 3.2), (dx + 1.8, dy + .6), (dx, dy + 2), (dx - 1.8, dy + .6)], True, 0)}" fill="#000" stroke="none"/>'
    return out


def _banner_face(centre, hh):
    """Engrave the ribbon face (no lettering): light ruling and a rain hyetograph trace."""
    top = [(x, y - hh / 2 + .8) for x, y in centre]
    bot = [(x, y + hh / 2 - .8) for x, y in centre]
    face = top + bot[::-1]
    cv = C.Canvas()
    cv.obj([], 0)
    cv.hair(C.hatch_poly(face, 0, 2, .3))
    # the storm's hour-by-hour rain, drawn as a stepped trace along the ribbon
    rng = random.Random(87)
    trace = []
    n = len(centre)
    for i in range(n):
        x, y = centre[i]
        t = i / (n - 1)
        amp = math.exp(-((t - .45) / .18) ** 2) * hh * .32
        trace.append((x, y + hh * .22 - amp - rng.uniform(0, .6)))
    cv.line(trace)
    return cv.svg()


def _tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h + ped_h * .3
    o.append(C.dark_ground((0, 0, w, h), "L"))
    o.append(f'<path d="M{C._n(px0 - 3.5)},{C._n(py0 - 3.5)}h{C._n(pw + 7)}v{C._n(ph + 7)}h{C._n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{C._n(px0 - 1.5)},{C._n(py0 - 1.5)}h{C._n(pw + 3)}v{C._n(ph + 3)}h{C._n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .6
    cx, cy = w / 2, py0 + ph * .45
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
                   max_n=5, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t3", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_field_vignette(C._superellipse(cx, cy, a + .5, b + .5), seed, C._uid("tv3", w, h, seed)))
    bp = C._superellipse(cx, cy, a - 3.2, b - 3.2)
    o.append(f'<path d="{C._d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#fff" stroke-width="2.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')
    o.append(f'<path d="{C._d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_face(centre, bh))
    py = h - ped_h
    psvg, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(psvg)
    storm, month, _ = _amounts(ctx)
    o.append(_gauge_tablet(tx + 2, ty + 2, tw - 3, th - 3, storm, month))
    return C.svg_doc(w, h, "".join(o))


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    if 110 <= h <= 260:
        return _medium(w, h, seed)
    if h > 260:
        return _tall(w, h, seed, ctx)
    uid = C._uid("v3x", w, h, seed)

    def fill(ix, iy, iw, ih):
        cx, cy = ix + iw / 2, iy + ih / 2
        if h < 110:            # medallion: rect inscribed in ellipse (rx-5)*.7071
            rx, ry = iw / 2 / .7071 + 5, ih / 2 / .7071 + 5
            pts = C._ell_pts(cx, cy, rx - 1.5, ry - 1.5, 64)
        else:                  # tall cartouche: rect = (a-6)*2^(-1/2.6)
            kk = 2 ** (-1 / 2.6)
            a, b = iw / 2 / kk + 6, ih / 2 / kk + 6
            pts = C._superellipse(cx, cy, a + .5, b + .5)
        return _field_vignette(pts, seed, uid)
    return C.frame_plate(w, h, seed, fill, density=.8 if h > 260 else 1.)
