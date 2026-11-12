"""solar-06 "Good solar news": Parker's panel-roofed barn on Sauvie Island under a rayed sun,
Mt. Hood on the horizon, carved into the house acanthus frame.
Easter eggs: his dog sitting by the barn door; crossed drumsticks as the barn's weathervane."""
import sys
import math
import random
import engraving_codex as C

TAU = math.tau
_n, _d = C._n, C._d


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def _clip_convex(poly, clip):
    """Sutherland-Hodgman: poly clipped by a convex polygon (either winding)."""
    s = 1 if C._area(clip) > 0 else -1
    out = list(poly)
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inp, out = out, []
        if not inp:
            break

        def side(p):
            return s * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]))

        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _quad_pt(q, u, v):
    """Bilinear point in quad q = (p00, p10, p11, p01)."""
    return _lerp(_lerp(q[0], q[1], u), _lerp(q[3], q[2], u), v)


def _solid(cv, poly, w=1.5):
    """Fill a polygon black with overlapping rules (stays inside the canvas clipping)."""
    if w >= 1.5:
        cv.heavy(C.hatch_poly(poly, 0, 1., .5))
    else:
        cv.line(C.hatch_poly(poly, 0, 1., .5))


def _arc(cx, cy, r, a0, a1, n=None):
    n = n or max(4, int(abs(a1 - a0) * r / 2))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


# ----------------------------------------------------------------------------------------------
# the vignette: sun, Mt. Hood, Sauvie Island cottonwoods, the river, the barn with its panels
# ----------------------------------------------------------------------------------------------

def _sun(cv, sx, sy, r, rot):
    face = r >= 11
    nr = 16
    for i in range(nr):
        a = rot + TAU * i / nr
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa, ca
        if i % 2 == 0:
            # pointed ray, split down its axis: one half white, one half cut in bulino
            L, hw = r * 1.95, r * .2
            s0 = (sx + ca * r * .9, sy + sa * r * .9)
            s1 = (sx + ca * L, sy + sa * L)
            pl = (s0[0] + nx * hw, s0[1] + ny * hw)
            pr = (s0[0] - nx * hw, s0[1] - ny * hw)
            cv.obj([[pl, s1, pr]], 1.)
            cv.hair(C.hatch_poly([s0, s1, pr], math.degrees(a), 1.5, .3))
            cv.hair([s0, s1])
        else:
            # flame ray
            L, hw = r * 1.6, r * .16
            pts_l, pts_r, sp = [], [], []
            m = 14
            for k in range(m + 1):
                t = k / m
                d = r * .9 + (L - r * .9) * t
                wob = math.sin(t * TAU * 1.25) * r * .1 * (0.4 + t)
                cx, cy = sx + ca * d + nx * wob, sy + sa * d + ny * wob
                ww = hw * (1 - t) ** .8
                pts_l.append((cx + nx * ww, cy + ny * ww))
                pts_r.append((cx - nx * ww, cy - ny * ww))
                sp.append((cx, cy))
            cv.obj([pts_l + pts_r[::-1]], 1.)
            cv.hair(C.hatch_poly(sp + pts_r[::-1], math.degrees(a) + 90, 1.5, .2))
    disc = C._ell_pts(sx, sy, r, r, 48)
    cv.obj([disc], 1.5)
    cv.hair(C._ell_pts(sx, sy, r * .84, r * .84, 40))
    for k in range(5 if r > 9 else 3):
        rr = r * (.88 + .025 * k) if r > 9 else r * (.88 + .04 * k)
        cv.hair(_arc(sx, sy, rr, -.2 - .1 * k, 1.9 + .1 * k))
    lim = r * .78
    for k in range(int(lim / 1.5)):
        rr = lim - k * 1.5
        span = .9 * (rr / lim) ** 2.2
        if span > .08:
            cv.hair(_arc(sx, sy, rr, .85 - span, .85 + span))
    if face:
        e = r * .3
        for s in (-1, 1):
            ex, ey = sx + s * e, sy - r * .12
            cv.line(_arc(ex, ey, r * .13, math.pi * 1.1, math.pi * 1.9, 6))
            cv.line([(ex - r * .06, ey + r * .03), (ex + r * .06, ey + r * .03)])
            cv.hair(_arc(ex, ey - r * .02, r * .2, math.pi * 1.15, math.pi * 1.85, 6))
        cv.line([(sx, sy - r * .1), (sx - r * .06, sy + r * .14), (sx + r * .04, sy + r * .17)])
        cv.line(_arc(sx, sy + r * .05, r * .32, .55, math.pi - .55, 8))
        for s in (-1, 1):
            cv.hair(_arc(sx + s * r * .36, sy + r * .2, r * .12, 0, TAU, 8))


def _hood(cv, px, py, base_y, half, rng):
    """Mt. Hood: snow peak, shadowed east face, timbered foot."""
    pts = [(px - half, base_y)]
    for t in (.25, .45, .62, .78, .9):
        pts.append((px - half * (1 - t), base_y - (base_y - py) * (t ** 1.6) + rng.uniform(-.5, .5)))
    pts.append((px, py))
    for t in (.9, .75, .55, .35, .15):
        pts.append((px + half * 1.1 * (1 - t), base_y - (base_y - py) * (t ** 1.5) + rng.uniform(-.5, .5)))
    pts.append((px + half * 1.1, base_y))
    cv.obj([pts], 1.)
    hgt = base_y - py
    sh = ([(px, py)] + [p for p in pts if p[0] > px] +
          [(px + half * .5, base_y), (px + half * .15, py + hgt * .6), (px + half * .2, py + hgt * .35)])
    cv.hair(C.hatch_poly(sh, 60, 1.5))
    for k, dx in enumerate((-.55, -.3, -.08, .25, .5)):
        x1 = px + half * dx
        cv.hair([(px + dx * 1.5, py + 1.5), (px + half * dx * .5, py + hgt * .45), (x1, py + hgt * (.62 + .05 * k))])
    snow = [(px - half, base_y - hgt * .22)]
    for i in range(1, 12):
        x = px - half + 2.1 * half * i / 12
        snow.append((x, base_y - hgt * (.22 + .1 * math.sin(i * 1.7))))
    foot = snow + [(px + half * 1.1, base_y), (px - half, base_y)]
    cv.hair(C.hatch_poly(foot, 0, 1.5))


def _trees(cv, x0, x1, base, ht, rng):
    """The Sauvie Island cottonwood line on the far bank."""
    pts = [(x0, base)]
    x = x0
    while x < x1:
        if rng.random() < .3:      # a fir spire
            w = ht * rng.uniform(.5, .7)
            top = base - ht * rng.uniform(1.1, 1.5)
            pts += [(x, base - ht * .35), (x + w * .5, top), (x + w, base - ht * .35)]
            x += w * .9
            continue
        w = rng.uniform(ht * .8, ht * 1.8)
        top = base - ht * rng.uniform(.5, 1.)
        for i in range(9):
            t = i / 8
            pts.append((x + w * t, top + (base - top) * (1 - math.sin(math.pi * t) ** .7) * .6
                        + rng.uniform(-.4, .4)))
        x += w * .8
    pts.append((x1, base))
    cv.obj([pts], .5)
    cv.hair(C.hatch_poly(pts, 90, 1.5))
    cv.hair(C.hatch_poly(pts, 0, 2.))


def _river(cv, x0, x1, y0, y1, glint_x, rng):
    poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    cv.obj([poly], 0)
    y = y0 + 1
    while y < y1:
        x = x0
        while x < x1:
            L = rng.uniform(4, 14)
            gap = rng.uniform(.8, 2.5)
            if abs(x - glint_x) < (y - y0) * 2 + 3:
                gap += 2.5
                L *= .5
            cv.hair([(x, y), (min(x1, x + L), y)])
            x += L + gap
        y += 1.5


def _array(cv, Q, cols, rows, glints=((.3, .08), (.46, .035))):
    """A solar array on quad Q (p00, p10, p11, p01: u along the rows, v up the slope): black
    racking, dark glass panels cut in two crossing bulino sets with cell lines, and the sun's glint
    struck across them as bright diagonal strips."""
    racking = list(Q)
    cv.obj([racking], 1.)
    _solid(cv, racking, 1.)
    ua = math.degrees(math.atan2(Q[1][1] - Q[0][1], Q[1][0] - Q[0][0]))
    va = math.degrees(math.atan2(Q[3][1] - Q[0][1], Q[3][0] - Q[0][0]))
    for i in range(cols):
        for j in range(rows):
            g = .035
            u0, u1 = i / cols + g / 2, (i + 1) / cols - g / 2
            v0, v1 = j / rows + g * 1.5, (j + 1) / rows - g * 1.5
            pq = [_quad_pt(Q, u0, v0), _quad_pt(Q, u1, v0), _quad_pt(Q, u1, v1), _quad_pt(Q, u0, v1)]
            cv.obj([pq], .5)
            cv.hair(C.hatch_poly(pq, ua, 1.5))
            cv.hair(C.hatch_poly(pq, va, 1.5, .75))
            for k in (1, 2):
                cv.hair([_lerp(pq[0], pq[1], k / 3), _lerp(pq[3], pq[2], k / 3)])
    for (t0, wdt) in glints:
        g0 = _quad_pt(Q, t0, -.2)
        g1 = _quad_pt(Q, t0 + .3, 1.2)
        nrm = (g1[1] - g0[1], -(g1[0] - g0[0]))
        L = math.hypot(*nrm)
        ww = wdt * math.hypot(Q[1][0] - Q[0][0], Q[1][1] - Q[0][1])
        nrm = (nrm[0] / L * ww, nrm[1] / L * ww)
        strip = [(g0[0] - nrm[0], g0[1] - nrm[1]), (g1[0] - nrm[0], g1[1] - nrm[1]),
                 (g1[0] + nrm[0], g1[1] + nrm[1]), (g0[0] + nrm[0], g0[1] + nrm[1])]
        gp = _clip_convex(strip, racking)
        if len(gp) > 2:
            cv.obj([gp], 0)
            cv.hair(C.hatch_poly(gp, math.degrees(math.atan2(g1[1] - g0[1], g1[0] - g0[0])), 3., .5))


def _barn(cv, gx0, gx1, ye, yb, dx, dy, egg_scale):
    """A gable barn in 3/4 view: the gable end faces us, the long roof slopes toward the sun (left)
    and carries Parker's array; board-and-batten walls; the dog by the door; a crossed-drumstick
    weathervane on the cupola."""
    gm = (gx0 + gx1) / 2
    gw = gx1 - gx0
    yp = ye - gw * .55
    side = [(gx0, yb), (gx0, ye), (gx0 - dx, ye - dy), (gx0 - dx, yb - dy)]
    cv.obj([side], 1.)
    cv.hair(C.hatch_poly(side, 90, 3.))
    for t in (.3, .7):
        wx = gx0 - dx * t
        wy = ye - dy * t + (yb - ye) * .25
        ww, wh = gw * .09, (yb - ye) * .32
        k = dy / dx * ww / 2
        win = [(wx - ww / 2, wy + k), (wx + ww / 2, wy - k), (wx + ww / 2, wy - k + wh), (wx - ww / 2, wy + k + wh)]
        cv.obj([win], 1.)
        _solid(cv, win, 1.)
    _solid(cv, [(gx0, ye), (gx0 - dx, ye - dy), (gx0 - dx, ye - dy + 2.5), (gx0, ye + 2.5)])
    ov = gw * .06
    E0 = (gx0 - ov, ye + ov * .5)
    R0 = (gm, yp - 1)
    D = (-dx - ov, -dy)
    roof = [E0, R0, (R0[0] + D[0], R0[1] + D[1]), (E0[0] + D[0], E0[1] + D[1])]
    cv.obj([roof], 1.)
    cv.hair(C.hatch_poly(roof, 0, 3.))
    a0 = _lerp(E0, R0, .12)
    a1 = _lerp(E0, R0, .92)
    Q = ((a0[0] + D[0] * .05, a0[1] + D[1] * .05), (a0[0] + D[0] * .95, a0[1] + D[1] * .95),
         (a1[0] + D[0] * .95, a1[1] + D[1] * .95), (a1[0] + D[0] * .05, a1[1] + D[1] * .05))
    _array(cv, Q, (6 if gw > 30 else 4), 2)
    # ridge cap
    cv.obj([[(R0[0] - .8, R0[1] - 1.2), (R0[0] + D[0] - .8, R0[1] + D[1] - 1.2),
             (R0[0] + D[0] + .6, R0[1] + D[1] + .8), (R0[0] + .6, R0[1] + .8)]], .5)
    # cupola + drumstick weathervane (Easter egg)
    cx, cy = R0[0] + D[0] * .5, R0[1] + D[1] * .5
    cs = max(3., gw * .1)
    cup = [(cx - cs / 2, cy + 1), (cx - cs / 2, cy - cs), (cx + cs / 2, cy - cs), (cx + cs / 2, cy + 1)]
    cv.obj([cup], 1.)
    cv.hair(C.hatch_poly(cup, 90, 1.5))
    cr = [(cx - cs * .8, cy - cs), (cx, cy - cs * 1.7), (cx + cs * .8, cy - cs)]
    cv.obj([cr], 1.)
    cv.hair(C.hatch_poly(cr, 30, 1.5))
    mx, my = cx, cy - cs * 1.7
    cv.line([(mx, my), (mx, my - cs * 1.2)])
    sl = cs * 1.1
    for s in (-1, 1):
        a = math.radians(-90 + s * 35)
        p0 = (mx - math.cos(a) * sl * .55, my - cs * .75 - math.sin(a) * sl * .55)
        p1 = (mx + math.cos(a) * sl * .55, my - cs * .75 + math.sin(a) * sl * .55)
        cv.line([p0, p1])
        cv.obj([C._ell_pts(p1[0], p1[1], .9, .9, 8)], 1.)
    # gable end facing us
    gable = [(gx0, yb), (gx0, ye), (gm, yp), (gx1, ye), (gx1, yb)]
    cv.obj([gable], 1.)
    cv.hair(C.hatch_poly(gable, 90, 1.5))
    cv.hair(C.hatch_poly([(gx0, ye), (gm, yp), (gx1, ye)], 0, 3.))
    for ex in (gx0, gx1):
        _solid(cv, [(ex, ye), (gm, yp), (gm, yp + 2.2), (ex, ye + 2.2)])
    for ex in (gx0 - ov * .6, gx1 + ov * .6):
        cv.obj([[(ex, ye + ov * .3), (gm, yp - 1.2), (gm, yp + .6), (ex, ye + ov * .3 + 1.8)]], .5)
    lw, lh = gw * .2, (ye - yp) * .5
    loft = [(gm - lw / 2, ye - 1), (gm - lw / 2, ye - 1 - lh), (gm + lw / 2, ye - 1 - lh), (gm + lw / 2, ye - 1)]
    cv.obj([loft], 1.)
    _solid(cv, loft, 1.)
    dw, dh = gw * .46, (yb - ye) * .7
    door = [(gm - dw / 2, yb), (gm - dw / 2, yb - dh), (gm + dw / 2, yb - dh), (gm + dw / 2, yb)]
    cv.obj([door], 1.)
    cv.hair(C.hatch_poly(door, 90, 2.))
    cv.line([door[0], door[2]])
    cv.line([door[1], door[3]])
    cv.hair([(gm, yb), (gm, yb - dh)])
    # the dog, sitting right of the door, looking up at the sun (Easter egg)
    s = egg_scale
    bx, by = gx1 - (gx1 - gm - dw / 2) * .5, yb
    dog = [(0, 0), (.2, -2.4), (.8, -4.6), (1.6, -6.4), (1.2, -7.6), (1.4, -8.8), (2.6, -9.2), (3.4, -8.4),
           (2.9, -7.6), (2.6, -6.6), (3.4, -4.4), (3.6, -1.6), (4.6, -.5), (4.4, 0)]
    ox = bx - 1.8 * s
    dog = [(ox + x * s, by + y * s) for x, y in dog]
    cv.obj([dog], .5)
    _solid(cv, dog, 1.)
    cv.line([(ox + 4.3 * s, by - .3 * s), (ox + 6 * s, by - .8 * s), (ox + 6.6 * s, by - 2.2 * s)])


def scene(cv, X, Y, W, H, seed, date):
    """The whole vignette, filling the box X..X+W, Y..Y+H (clip it to the cartouche field)."""
    rng = random.Random(seed)
    S = min(W, H * 1.5)
    hz = Y + H * (.6 if W / H > 1.6 else .58)
    sx, sy = X + W * .25, Y + H * (.3 if W / H > 1.6 else .28)
    sr = max(5., min(H * .15, W * .1))
    sky = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, hz + 2), (X - 2, hz + 2)]
    cv.obj([sky], 0)
    y = Y - 1.
    while y < hz + 2:
        cv.hair([(X - 2, y), (X + W + 2, y)])
        frac = (y - Y) / max(1., hz - Y)
        y += 1.5 if frac < .35 else (2. if frac < .75 else 3.)
    nrays = 40
    rot = (sum(map(ord, date)) % 9) * .02
    Rmax = math.hypot(W, H) * 1.2
    for i in range(nrays):
        a = rot + TAU * (i + .5) / nrays
        half = math.radians(1.6 if i % 2 else 1.0)
        r0 = sr * 2.05
        wedge = [(sx + r0 * math.cos(a - half * .6), sy + r0 * math.sin(a - half * .6)),
                 (sx + Rmax * math.cos(a - half), sy + Rmax * math.sin(a - half)),
                 (sx + Rmax * math.cos(a + half), sy + Rmax * math.sin(a + half)),
                 (sx + r0 * math.cos(a + half * .6), sy + r0 * math.sin(a + half * .6))]
        cv.obj([wedge], 0)
        cv.hair([(sx + r0 * math.cos(a), sy + r0 * math.sin(a)), (sx + Rmax * math.cos(a), sy + Rmax * math.sin(a))])
    halo = C._ell_pts(sx, sy, sr * 2.05, sr * 2.05, 48)
    cv.obj([halo], 0)
    for k in range(int(sr * 1.05 / 1.5)):
        cv.hair(_arc(sx, sy, sr + k * 1.5, 0, TAU, 40))
    _sun(cv, sx, sy, sr, rot)
    half = min(W * .2, H * .3)
    _hood(cv, X + W * .76, hz - half * .85, hz, half, rng)
    _trees(cv, X - 2, X + W + 2, hz + 1, max(4., min(H * .09, W * .045)), rng)
    rv0, rv1 = hz + 1, hz + max(4., H * .07)
    _river(cv, X - 2, X + W + 2, rv0, rv1, sx, rng)
    field = [(X - 2, rv1), (X + W + 2, rv1), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([field], .5)
    vp = (sx, rv1 - H * .05)
    for k in range(-26, 27):
        bx = sx + k * W * .055
        top = _lerp(vp, (bx, Y + H + 2), (rv1 - vp[1]) / (Y + H + 2 - vp[1]))
        cv.hair([top, (bx, Y + H + 2)])
    y = rv1 + 2
    while y < Y + H + 2:
        cv.hair([(X - 2, y), (X + W + 2, y)])
        y += 3 if y < rv1 + H * .15 else 1.5
    wide = W / H > 1.6
    gw = S * (.25 if wide else .22)
    gx0 = X + W * .56
    yb = Y + H * (.84 if wide else .79)
    ye = yb - gw * .58
    dx, dy = gw * 1.25, gw * .2
    shp = [(gx0 + gw, yb), (gx0 + gw + gw * .7, yb + gw * .18), (gx0 - dx * .2 + gw * .6, yb + gw * .2), (gx0, yb)]
    cv.obj([shp], 0)
    _solid(cv, shp, 1.)
    _barn(cv, gx0, gx0 + gw, ye, yb, dx, dy, max(.55, gw / 48))
    # a ground-mounted row of panels in the left foreground, tilted up to the sun
    if wide:
        ax0, ax1 = X + W * .1, X + W * .42
        ay0, ay1 = Y + H * .87, Y + H * .83
        hp = H * .14
    else:
        ax0, ax1 = X + W * .1, X + W * .52
        ay0, ay1 = Y + H * .96, Y + H * .92
        hp = H * .11
    Q = ((ax0, ay0), (ax1, ay1), (ax1 + W * .025, ay1 - hp * .85), (ax0 + W * .035, ay0 - hp))
    sh = [(ax0, ay0 + 1), (ax1, ay1 + 1), (ax1 + W * .05, ay1 + 1 + H * .02), (ax0 + W * .07, ay0 + 1 + H * .03)]
    cv.obj([sh], 0)
    _solid(cv, sh, 1.)
    for t in (.04, .5, .96):
        top = _quad_pt(Q, t, .9)
        bot = _lerp(_quad_pt(Q, t, 0), _quad_pt(Q, t, 0), 0)
        cv.obj([[(top[0] - .7, top[1]), (top[0] + .7, top[1]), (top[0] + .7, bot[1] + 2), (top[0] - .7, bot[1] + 2)]], .5)
    _array(cv, Q, 7, 2, ((.3, .03), (.4, .012)))


# ----------------------------------------------------------------------------------------------
# frame compositions (house layouts, re-cut so the vignette fills the whole cartouche field)
# ----------------------------------------------------------------------------------------------

def _eye(cx, cy, r, side, a_out, turns, tail, up):
    """Where a house _pair_unit volute ends in its eye (so a sun can be set in the curl)."""
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    return C.volute_spine(cx, cy, r, a0, turns, flip, tail, -.5 if up else .5)[-1]


def _field_scene(fpts, seed, date, tag):
    xs = [p[0] for p in fpts]
    ys = [p[1] for p in fpts]
    X, Y, W, H = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    cv = C.Canvas()
    scene(cv, X, Y, W, H, seed, date)
    cid = C._uid("sol", tag, X, Y, W, H)
    return (f'<clipPath id="{cid}"><path d="{_d(fpts, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


def _cartouche_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - 2, b - 2)


def _layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 150)
    o.append(C._clip(C._uid("sb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fpts = C._ell_pts(cx, cy, rx - 2, ry - 2, 64)[:-1]
    o.append(_field_scene(fpts, seed, date, "b"))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.95)
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
        eyes.append(_eye(vx, vy, r, side, 0, 1.4, .9, True))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(7, gh * .065), rmax=r * .8,
                   max_n=14, edge=.7, cv=cv)
    cv.extend(main)
    for ex, ey in eyes:
        _sun(cv, ex, ey, max(4., r * .14), .1)
    o.append(C._clip(C._uid("sm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_scene(_cartouche_field(cx, cy, cw, gh + 4), seed, date, "m"))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tablet_fill(tx, ty, tw, th, seed):
    """The pedestal's sunk tablet: ruled ground with a little sun between rows of panels."""
    cv = C.Canvas()
    poly = [(tx + 2, ty + 2), (tx + tw - 1, ty + 2), (tx + tw - 1, ty + th - 1), (tx + 2, ty + th - 1)]
    cv.obj([poly], 0)
    cv.hair(C.hatch_poly(poly, 0, 1.5))
    n = max(3, int(tw / (th * 2.2)))
    n += 1 - n % 2
    for i in range(n):
        x = tx + tw * (i + .5) / n
        y = ty + th / 2
        if i == n // 2:
            _sun(cv, x, y, th * .22, 0)
        else:
            pw, ph = th * 1.1, th * .5
            q = [(x - pw / 2, y + ph / 2), (x - pw / 2 + ph * .4, y - ph / 2), (x + pw / 2 + ph * .4, y - ph / 2), (x + pw / 2, y + ph / 2)]
            cv.obj([q], 1.)
            cv.hair(C.hatch_poly(q, 0, 1.5))
            for k in (1, 2, 3):
                cv.hair([_lerp(q[0], q[3], k / 4), _lerp(q[1], q[2], k / 4)])
    return cv.svg()


def _banner_shade(centre, bh):
    """Bulino along the banner face so no bare white is left: rules following the ribbon's arch,
    opening toward a highlight band just above the middle where the ribbon bulges."""
    lines = []
    off = -bh * .32
    while off < bh * .34:
        if not (-.1 * bh < off < .06 * bh):
            pl = []
            for i in range(1, len(centre) - 1):
                (x0, y0), (x1, y1) = centre[i - 1], centre[i + 1]
                L = math.hypot(x1 - x0, y1 - y0) or 1
                nx, ny = -(y1 - y0) / L, (x1 - x0) / L
                pl.append((centre[i][0] + nx * off, centre[i][1] + ny * off))
            lines.append(_d(pl, tol=.2))
        off += 1.5
    return f'<path d="{"".join(lines)}" fill="none" stroke="#000" stroke-width=".5"/>'


def _layout_tall(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
        eyes.append((_eye(vx, vy, r1, side, 10, 1.45, .8, True), r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
        eyes.append((_eye(vx, vy, r2, side, -10, 1.4, .8, False), r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    for (ex, ey), rr in eyes:
        _sun(cv, ex, ey, max(4., rr * .12), .1)
    o.append(C._clip(C._uid("st", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_scene(_cartouche_field(cx, cy, cw, ch), seed, date, "t"))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_shade(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet_fill(tx, ty, tw, th, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("sf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "") or ""
    seed = sum(map(ord, date)) + 6
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date)
    else:
        body = _layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
