"""Doodles ("By the numbers"): little charts drawn from Parker's roof, sky, shelf and calendar.

The plate engraves those charts as one scene inside the house Codex frame: looking west from
Sauvie Island at sunset, today's daylight arc is drawn across the sky as a beaded chart line (June's
longer arc dotted above it), the sun half-set behind the West Hills where today's arc lands, the
Multnomah Channel below; on the sill in front stand the rain jar (graduated, filled to this month's
total, a pointer at "usual by now") and the bookshelf, with the moon in today's phase. The pedestal
tablet carries the year's daylight curve with a "you are here" mark.
Easter egg: a pair of crossed drumsticks lying on the sill like doodling pencils.
"""
import sys
import math
import re
import random
import datetime

import engraving_codex as C

PI, TAU = math.pi, 2 * math.pi
LAT = 45.68  # Sauvie Island
_n, _d = C._n, C._d


# ----------------------------------------------------------------------------------------------
# today's numbers
# ----------------------------------------------------------------------------------------------

def _facts(ctx):
    try:
        day = datetime.date.fromisoformat((ctx or {}).get("date", "")[:10])
    except Exception:
        day = datetime.date(2026, 11, 11)
    doy = day.timetuple().tm_yday

    def daylen(n):
        dec = math.radians(23.44 * math.sin(TAU * (284 + n) / 365))
        c = -math.tan(math.radians(LAT)) * math.tan(dec) + math.sin(math.radians(-.83)) / (
            math.cos(math.radians(LAT)) * math.cos(dec))
        return 2 * math.degrees(math.acos(max(-1, min(1, c)))) / 15, math.degrees(dec)

    hrs, dec = daylen(doy)
    curve = [daylen(n)[0] for n in range(1, 366, 4)]
    moon_age = ((day - datetime.date(2000, 1, 6)).days - .76) % 29.530588
    sample = (ctx or {}).get("sample", "") or ""
    m = re.search(r"([0-9]+\.[0-9]+)\s*in in the jar", sample)
    rng = random.Random(day.toordinal())
    rain = float(m.group(1)) if m else round(min(5.4, .15 * day.day * rng.uniform(.4, 1.6)), 2)
    m = re.search(r"usual by now\s*([0-9.]+)", sample) or re.search(r"behind the ([0-9.]+) in", sample)
    usual = float(m.group(1)) if m else round(5.6 * day.day / 30, 1)
    return dict(hrs=hrs, noon=90 - LAT + dec, doy=doy, curve=curve, moon=moon_age / 29.530588,
                rain=rain, usual=usual, seed=day.toordinal())


# ----------------------------------------------------------------------------------------------
# small geometry
# ----------------------------------------------------------------------------------------------

def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _rot(pts, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def _runs(x0, x1, y, keep, step=.8):
    """Horizontal line at y from x0 to x1, kept where keep(x, y)."""
    out, cur = [], None
    x = x0
    while x <= x1 + 1e-6:
        if keep(x, y):
            if cur is None:
                cur = [x, x]
            cur[1] = x
        elif cur is not None:
            if cur[1] - cur[0] > .7:
                out.append([(cur[0], y), (cur[1], y)])
            cur = None
        x += step
    if cur is not None and cur[1] - cur[0] > .7:
        out.append([(cur[0], y), (cur[1], y)])
    return out


def _cyl_lines(x0, x1, y0, y1, n, side_bias=0.):
    """Vertical lines across x0..x1, crowding toward both edges like a cylinder's shading."""
    out = []
    cx, r = (x0 + x1) / 2, (x1 - x0) / 2
    for i in range(1, n):
        t = -PI / 2 + PI * i / n
        s = math.sin(t)
        if s < side_bias:
            continue
        x = cx + r * s
        out.append([(x, y0), (x, y1)])
    return out


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def _scene(X, Y, W, H, F, detail=2):
    """Engrave the sunset chart scene filling X..X+W, Y..Y+H. detail 0 mini, 1 no sill, 2 full."""
    cv = C.Canvas()
    rng = random.Random(F["seed"])
    cx = X + W / 2
    fore = detail >= 2
    hor = Y + H * (.58 if fore else .66)                 # water line
    ridge_y = hor - H * (.06 if fore else .08)
    # the chart: today's arc and June's
    span = W * .47
    rx_t = span * (.35 + .65 * F["hrs"] / 15.8)
    rx_j = span
    top_room = hor - Y - H * .1
    ry_t = top_room * (.3 + .7 * F["noon"] / 68.)
    ry_j = top_room
    sun_r = max(3.5, min(W, H) * (.1 if detail else .14))
    sx, sy = cx + rx_t, ridge_y + sun_r * .1
    if sx + sun_r * 1.2 > X + W * .88:
        sx = X + W * .88 - sun_r * 1.2

    # sky: ruled, closer toward the zenith, cut away in a halo and alternate rays round the sun
    cv.obj([_rect(X - 2, Y - 2, W + 4, hor - Y + 4)], 0)
    nray = 22
    ray_len = [min(W, H) * (.62 if k % 2 else .42) for k in range(nray)]

    def sky_keep(x, y):
        dx, dy = x - sx, y - sy
        dist = math.hypot(dx, dy)
        if dist < sun_r * 1.35:
            return False
        a = math.atan2(dy, dx) % TAU
        k = int(a / TAU * nray * 2)
        if k % 2 == 0 and dist < ray_len[(k // 2) % nray] * (1 - .25 * abs(math.sin(a))):
            return False
        return True

    y = Y - 1
    while y < hor:
        t = (y - Y) / max(1, hor - Y)
        cv.hair(_runs(X - 2, X + W + 2, y, sky_keep, .7))
        y += 1.5 if t < .3 else (2. if t < .7 else 3.)
    # a few dark cloud bars low in the sky (doubled lines)
    if detail:
        for k in range(3):
            cy_ = Y + (hor - Y) * (.42 + .14 * k)
            x0 = X + W * rng.uniform(.02, .2) + k * W * .08
            x1 = x0 + W * rng.uniform(.25, .38)
            ln = []
            for j in range(3):
                yy = cy_ + j * 1.5 + .75
                a = x0 + j * 3 + rng.uniform(0, 3)
                b = x1 - j * 4 - rng.uniform(0, 3)
                if b - a > 4:
                    ln += _runs(a, b, yy, lambda x, y_: math.hypot(x - sx, y_ - sy) > sun_r * 1.6)
            cv.hair(ln)

    # the moon in today's phase, upper left
    if detail:
        mr = max(4., min(W, H) * .045)
        mx, my = X + W * .2, Y + H * .16
        cv.obj([C._ell_pts(mx, my, mr + 1.2, mr + 1.2, 32)[:-1]], 0)
        cv.obj([C._ell_pts(mx, my, mr, mr, 32)[:-1]], 1.)
        ph = F["moon"]
        k = math.cos(TAU * ph)  # 1 new, -1 full
        lit_right = ph < .5
        dark = []
        for j in range(int(2 * mr / 1.5) + 1):
            yy = my - mr + .75 + j * 1.5
            if abs(yy - my) >= mr:
                continue
            hw = math.sqrt(mr * mr - (yy - my) ** 2)
            term = mx + hw * k * (1 if lit_right else -1)
            if lit_right:
                a, b = mx - hw, term
            else:
                a, b = term, mx + hw
            if b - a > .6:
                dark.append([(a, yy), (b, yy)])
        cv.hair(dark)
        for (ax, ay, ar) in ((.3, -.25, .18), (-.2, .3, .12), (.25, .35, .1)):
            cv.hair([C._ell_pts(mx + ax * mr, my + ay * mr, ar * mr, ar * mr, 10)])

    # June's arc, dotted, and today's arc, beaded at each hour of daylight
    if detail:
        dots = []
        for i in range(0, 61):
            a = PI + PI * i / 60
            if i % 2 == 0:
                p = (cx + rx_j * math.cos(a), hor + ry_j * math.sin(a))
                q = (cx + rx_j * math.cos(a + PI / 150), hor + ry_j * math.sin(a + PI / 150))
                dots.append([p, q])
        cv.obj([], 0)
        cv.line(dots)
    arc = [(cx + rx_t * math.cos(PI + PI * i / 80), hor + ry_t * math.sin(PI + PI * i / 80)) for i in range(81)]
    cv.obj([], 0)
    cv.line(arc)
    nb = max(2, int(round(F["hrs"])))
    for i in range(1, nb):
        a = PI + PI * i / nb
        bx, by = cx + rx_t * math.cos(a), hor + ry_t * math.sin(a)
        br = 1.6 if detail else 1.1
        cv.obj([C._ell_pts(bx, by, br, br, 12)[:-1]], 1.)
        if i * 2 == nb:  # noon bead: black
            cv.heavy([C._ell_pts(bx, by, br * .4, br * .4, 8)])
    # the sun: ringed disc
    cv.obj([C._ell_pts(sx, sy, sun_r, sun_r, 40)[:-1]], 1.5)
    rings = [C._ell_pts(sx, sy, rr, rr, 40) for rr in [sun_r - 2 * j for j in range(1, 40)] if rr > 1.2]
    cv.hair(rings)
    cv.hair(C.hatch_poly(C._ell_pts(sx, sy, sun_r - .5, sun_r - .5, 30, 0, PI)[:-1] + [(sx - sun_r, sy)], 0, 1.5))

    # far ridge: the Tualatin Mountains
    def ridge(x, far=True):
        t = (x - X) / W
        if far:
            return ridge_y - H * (.045 * math.sin(t * 5.1 + 1.3) + .025 * math.sin(t * 13 + .4) + .05)
        return hor - H * (.03 + .07 * max(0, math.sin(t * 3.4 - .9)) + .012 * math.sin(t * 23))

    xs = [X - 2 + (W + 4) * i / 70 for i in range(71)]
    far = [(x, ridge(x)) for x in xs] + [(X + W + 2, hor + 1), (X - 2, hor + 1)]
    cv.obj([far], .5)
    ln = []
    y = min(p[1] for p in far[:-2]) - 1
    while y < hor + 1:
        ln += _runs(X - 2, X + W + 2, y, lambda x, y_: y_ > ridge(x) + .4, .7)
        y += 1.5
    cv.hair(ln)
    cv.hair(C.hatch_poly(far, 30, 3))
    # near ridge with firs, left and right shoulders
    near = [(x, ridge(x, False)) for x in xs] + [(X + W + 2, hor + 1), (X - 2, hor + 1)]
    cv.obj([near], .5)
    cv.hair(C.hatch_poly(near, 0, 1.5, .5))
    cv.hair(C.hatch_poly(near, -50, 2))
    if detail:
        firs = []
        fx = X + 2
        while fx < X + W:
            base = ridge(fx, False) + 1
            fh = H * rng.uniform(.03, .065)
            if fh > 3 and abs(fx - sx) > sun_r * 1.4:
                fw = fh * .32
                pts = [(fx, base - fh)]
                for j in range(1, 5):
                    yy = base - fh + fh * j / 4.5
                    pts += [(fx + fw * j / 4, yy - fh * .06), (fx + fw * j / 6, yy)]
                pts += [(fx + fw, base), (fx - fw, base)]
                for j in range(4, 0, -1):
                    yy = base - fh + fh * j / 4.5
                    pts += [(fx - fw * j / 6, yy), (fx - fw * j / 4, yy - fh * .06)]
                firs.append(pts)
            fx += rng.uniform(3.5, 9) * (1 if detail > 1 else 1.4)
        cv.obj(firs, .5)
        for f in firs:
            cv.hair(C.hatch_poly(f, 0, 1.5))
            cv.hair(C.hatch_poly(f, 70, 1.5))

    # the channel: broken water lines, a white path of light under the sun
    wbot = Y + H + 2
    cv.obj([_rect(X - 2, hor, W + 4, wbot - hor)], 1.)
    wl = []
    y = hor + 1.5
    j = 0
    while y < wbot:
        t = (y - hor) / max(1., (Y + H) - hor)
        pathw = sun_r * (.55 + .5 * t) * (1 - .35 * (j % 2))
        x = X - 2 + rng.uniform(0, 6)
        while x < X + W + 2:
            L = rng.uniform(14, 40) * (1 + t)
            a, b = x, min(x + L, X + W + 2)
            if a < sx + pathw and b > sx - pathw:
                # in the sun's path: short glints
                g = sx - pathw + rng.uniform(0, pathw * .6)
                while g < sx + pathw:
                    gl = rng.uniform(1.5, 4.5)
                    if rng.random() < .78:
                        wl.append([(max(a, g), y), (min(b, g + gl), y)])
                    g += gl + rng.uniform(1.5, 4)
                if a < sx - pathw:
                    wl.append([(a, y), (sx - pathw, y)])
                if b > sx + pathw:
                    wl.append([(sx + pathw, y), (b, y)])
            else:
                wl.append([(a, y), (b, y)])
            x = b + rng.uniform(1.2, 2.2)
        y += 1.5 if t > .6 else 2.
        j += 1
    cv.hair(wl)

    if fore:
        _sill(cv, X, Y, W, H, F, rng, sx)
    return cv


def _book_spine(cv, pts, ang, i, tone):
    """A book's spine (polygon pts, its long axis at ang degrees): rounded with lines along it,
    raised bands, a sunk label."""
    cv.obj([pts], 1.)
    (ax, ay), (bx, by), (qx, qy), (dx, dy) = pts
    L = math.hypot(bx - ax, by - ay)
    T = math.hypot(dx - ax, dy - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    vx, vy = (dx - ax) / T, (dy - ay) / T

    def P(u, v):
        return (ax + ux * u + vx * v, ay + uy * u + vy * v)

    # rounding: lines along, crowding to the shadow side; tone sets how dark the cloth is
    n = max(3, int(T / (1.5 if tone else 2)))
    for j in range(1, n):
        t = j / n
        if tone == 0 and .15 < t < .55:
            continue
        if tone == 1 and t < .3 and j % 2:
            continue
        cv.hair([P(1, T * t), P(L - 1, T * t)])
    if tone == 2:
        cv.hair(C.hatch_poly(pts, ang + 60, 2, .5, .5))
    # bands
    for f in (.07, .11, .89, .93):
        cv.line([P(L * f, .6), P(L * f, T - .6)])
    # label with two lines of "lettering"
    lw, lh = L * .3, T * .52
    lab = [P((L - lw) / 2, (T - lh) / 2), P((L + lw) / 2, (T - lh) / 2), P((L + lw) / 2, (T + lh) / 2), P((L - lw) / 2, (T + lh) / 2)]
    cv.obj([lab], 1.)
    if lh > 5:
        for k, t in enumerate((.35, .68)):
            cv.line([P((L - lw) / 2 + 2 + k, (T - lh) / 2 + lh * t), P((L + lw) / 2 - 2 - (i % 3), (T - lh) / 2 + lh * t)])
    else:
        cv.hair([P((L - lw) / 2 + 1.5, T / 2), P((L + lw) / 2 - 1.5, T / 2)])


def _sill(cv, X, Y, W, H, F, rng, sx):
    """Foreground: the window sill with the books, the rain jar and the crossed drumsticks."""
    top = Y + H * .8
    sill = [(X - 2, top), (X + W + 2, top), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([sill], 1.)
    gr = []
    edge = top + H * .075
    y = top + 1.5
    k = 0
    while y < edge:
        gr.append([(x, y + .5 * math.sin(x * .07 + k * 1.7) + .35 * math.sin(x * .19 + k)) for x in
                   [X - 2 + (W + 4) * i / 60 for i in range(61)]])
        y += 1.5 if y > edge - 5 else 2.
        k += 1
    cv.hair(gr)
    front = [(X - 2, edge), (X + W + 2, edge), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([front], 1.)
    cv.line(C.hatch_poly(front, 0, 1.5, .4))
    cv.hair(C.hatch_poly(front, 60, 2))

    s = H / 230.
    base = top + H * .04

    # the bookshelf: a lying stack, three volumes standing on it, one leaning
    bx = X + W * .08
    stack = [(W * .3, H * .05, 0, 1), (W * .27, H * .055, 4, 0), (W * .31, H * .045, -2, 2), (W * .25, H * .05, 5, 1)]
    yb = base
    for i, (bw, bh, off, tone) in enumerate(stack):
        x0, y0 = bx + off * s, yb - bh
        _book_spine(cv, _rect(x0, y0, bw, bh), 0, i, tone)
        yb = y0
    x = bx + W * .03
    for i, (hh, ww, tone) in enumerate([(H * .21, W * .04, 0), (H * .25, W * .048, 2), (H * .22, W * .042, 1)]):
        pts = [(x, yb), (x, yb - hh), (x + ww, yb - hh), (x + ww, yb)]
        _book_spine(cv, pts, -90, i + 1, tone)
        x += ww + .3
    hh, ww, a = H * .23, W * .04, .38
    lean = _rot([(x, yb), (x, yb - hh), (x + ww, yb - hh), (x + ww, yb)], x + ww, yb, a)
    _book_spine(cv, lean, -90 + math.degrees(a), 4, 1)

    # the rain jar: clear glass, so the channel shows through; water to this month's total
    jw, jh = W * .15, H * .4
    jx = X + W * .57 - jw / 2
    jb = base + H * .012
    jt = jb - jh
    full_in = 3.0
    q0 = jb - 3 * s
    qh = jh - 12 * s
    lvl = q0 - qh * min(F["rain"], full_in) / full_in
    usual_y = q0 - qh * min(F["usual"], full_in) / full_in
    # glass walls only (no white fill): the scene behind reads through
    cv.obj([], 0)
    cv.line([(jx, jt + 4 * s), (jx, jb - 2 * s), (jx + 2, jb), (jx + jw - 2, jb), (jx + jw, jb - 2 * s), (jx + jw, jt + 4 * s)])
    cv.hair([(jx + 1.5, jt + 5 * s), (jx + 1.5, lvl)])
    cv.hair([(jx + jw - 1.5, jt + 5 * s), (jx + jw - 1.5, lvl)])
    # a bright reflection stripe: a white sliver down the glass
    rx0 = jx + jw * .2
    refl = [(rx0, jt + 7 * s), (rx0 + jw * .1, jt + 7 * s), (rx0 + jw * .1, lvl - 2), (rx0, lvl - 2)]
    cv.obj([refl], 0)
    # water: an occluding body, ruled with cylinder shading and a highlight
    water = [(jx, lvl), (jx + jw, lvl), (jx + jw, jb - 2 * s), (jx + jw - 2, jb), (jx + 2, jb), (jx, jb - 2 * s)]
    cv.obj([water], 1.)
    cv.hair(C.hatch_poly(water, 0, 1.5, .25, .3))
    cv.hair([l for l in _cyl_lines(jx, jx + jw, lvl + 1, jb - 1, 16) if not (jx + jw * .16 < l[0][0] < jx + jw * .34)])
    cv.line([(jx + .5, lvl - 1.2), (jx + 2, lvl), (jx + jw - 2, lvl), (jx + jw - .5, lvl - 1.2)])
    ell = C._ell_pts(jx + jw / 2, lvl, jw / 2 - .5, 1.6 + s, 24)[:-1]
    cv.obj([ell], .5)
    cv.hair(C.hatch_poly(ell, 0, 1.5))
    # graduations: quarter, half and inch ticks with dot numerals (one dot per inch)
    ticks, dots = [], []
    for q in range(0, int(full_in * 4) + 1):
        yy = q0 - qh * q / (full_in * 4)
        L = jw * (.36 if q % 4 == 0 else (.22 if q % 2 == 0 else .12))
        ticks.append([(jx + jw - 1, yy), (jx + jw - 1 - L, yy)])
        if q % 4 == 0 and q:
            for d in range(q // 4):
                ex = jx + jw - 3 - L - 2.2 * d
                dots.append(C._ell_pts(ex, yy, .5, .5, 6))
    cv.obj([], 0)
    cv.line(ticks)
    cv.heavy(dots)
    # "usual by now": a pointer outside the glass
    pw_ = 4 + 2 * s
    cv.obj([[(jx + jw + 1.5, usual_y), (jx + jw + 1.5 + pw_ * 1.6, usual_y - pw_ * .7), (jx + jw + 1.5 + pw_ * 1.6, usual_y + pw_ * .7)]], 1.)
    cv.hair(C.hatch_poly([(jx + jw + 1.5, usual_y), (jx + jw + 1.5 + pw_ * 1.6, usual_y - pw_ * .7), (jx + jw + 1.5 + pw_ * 1.6, usual_y + pw_ * .7)], 0, 1.5))
    # funnel and lip
    fun = [(jx - 3, jt), (jx + jw + 3, jt), (jx + jw, jt + 5 * s), (jx, jt + 5 * s)]
    cv.obj([fun], 1.)
    cv.hair(C.hatch_poly(fun, 0, 1.5, .5))
    lip = C._ell_pts(jx + jw / 2, jt, jw / 2 + 3, 2.2 * s + 1, 28)[:-1]
    cv.obj([lip], 1.)
    cv.line(C.hatch_poly(C._ell_pts(jx + jw / 2, jt + .4, jw / 2 + 1, 1.2 * s + .5, 20)[:-1], 0, 1.5))
    # cast shadow on the sill
    sh = [(jx + jw, jb - 1), (jx + jw * 1.9, jb - 1), (jx + jw * 1.7, jb + 2.5), (jx + jw, jb + 2.5)]
    cv.obj([sh], 0)
    cv.line(C.hatch_poly(sh, 0, 1.5))

    # Easter egg: Parker's crossed drumsticks lying on the sill in front, like two doodling pencils
    mx, my = X + W * .44, base + H * .02
    ln = W * .34
    for a in (.16, -.13):
        ca, sa = math.cos(a), math.sin(a)
        x0, y0 = mx - ca * ln / 2, my - sa * ln / 2
        x1, y1 = mx + ca * ln / 2, my + sa * ln / 2
        if a < 0:
            x0, y0, x1, y1 = x1, y1, x0, y0
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        if ny < 0:
            nx, ny = -nx, -ny
        w0, w1 = 2.2 + 1.3 * s, 1. + .5 * s
        e = L * .8

        def at(u, v):
            wd = w0 + (w1 - w0) * max(0, (u - L * .45) / (e - L * .45))
            return (x0 + ux * u + nx * v * wd, y0 + uy * u + ny * v * wd)

        us = [L * i / 24 * .93 for i in range(25)]
        rod = [at(u, -1) for u in us] + [at(u, 1) for u in us[::-1]]
        tr = 1.4 + .6 * s
        tip = _rot(C._ell_pts(x0 + ux * (L * .93 + tr), y0 + uy * (L * .93 + tr), tr * 1.4, tr, 14)[:-1],
                   x0 + ux * (L * .93 + tr), y0 + uy * (L * .93 + tr), math.atan2(dy, dx))
        cv.obj([rod, tip], 1.)
        cv.hair([[at(u, .3) for u in us[1:-1]], [at(u, .65) for u in us[1:-1]]])
        cv.line([at(u, .9) for u in us[1:-1]])
        cv.hair(C.hatch_poly(tip, 0, 1.5, .25)[1:])
        cv.line([at(L * .05, -1), at(L * .05, 1)])


def _field(F, cx, cy, w, h, detail):
    """The cartouche's whole field, engraved and clipped to its outline."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    cv = _scene(cx - a, cy - b, 2 * a, 2 * b, F, detail)
    pts = C._superellipse(cx, cy, a + .3, b + .3)
    cid = C._uid("dd", cx, cy, w, h)
    return (f'<clipPath id="{cid}"><path d="{_d(pts, True, .1)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ----------------------------------------------------------------------------------------------
# pedestal tablet: the year's daylight curve; ribbon face shading
# ----------------------------------------------------------------------------------------------

def _tablet(F, tx, ty, tw, th):
    cv = C.Canvas()
    x0, y0, w, h = tx + 2, ty + 2, tw - 3, th - 3
    cv.obj([_rect(x0, y0, w, h)], 0)
    cv.hair(C.hatch_poly(_rect(x0, y0, w, h), 0, 3, .75))
    vals = F["curve"]
    lo, hi = min(vals) - .4, max(vals) + .2
    pts = [(x0 + 3 + (w - 6) * i / (len(vals) - 1), y0 + h - 2 - (h - 4) * (v - lo) / (hi - lo)) for i, v in enumerate(vals)]
    area = pts + [(pts[-1][0], y0 + h), (pts[0][0], y0 + h)]
    cv.obj([area], 0)
    cv.hair(C.hatch_poly(area, 45, 1.5))
    cv.hair(C.hatch_poly(area, -45, 3))
    cv.obj([], 0)
    cv.heavy(pts)
    # month ticks
    cv.line([[(x0 + 3 + (w - 6) * m / 12, y0 + h - 2), (x0 + 3 + (w - 6) * m / 12, y0 + h)] for m in range(13)])
    i = (F["doy"] - 1) / 365
    px = x0 + 3 + (w - 6) * i
    v = vals[min(len(vals) - 1, int(i * (len(vals) - 1) + .5))]
    py = y0 + h - 2 - (h - 4) * (v - lo) / (hi - lo)
    r = max(2.2, h * .16)
    cv.obj([C._ell_pts(px, py, r + 1.2, r + 1.2, 18)[:-1]], 1.)
    cv.heavy([C._ell_pts(px, py, r * .45, r * .45, 10)])
    return cv.svg()


def _ribbon_face(centre, h):
    R = C._Rib(centre, [h / 2] * len(centre), [h / 2] * len(centre))
    cv = C.Canvas()
    cv.obj([], 0)
    for s in (.48, .26, -.3, -.42, -.54):
        cv.hair(R.contour(s, .02, .98))
    # a row of tiny raindrops along the face: the month's rainy days
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts (copies of the house layouts, with the field engraved edge to edge)
# ----------------------------------------------------------------------------------------------

def _band(w, h, seed, F):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    a, b = rx - 4.5, ry - 4.5
    cv = _scene(cx - a, cy - b, 2 * a, 2 * b, F, 0)
    cid = C._uid("bm", w, h, seed)
    o.append(f'<clipPath id="{cid}"><path d="{_d(C._ell_pts(cx, cy, a, b, 64), True)}"/></clipPath>'
             f'<g clip-path="url(#{cid})">{cv.svg()}</g>')
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, a, b, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _medium(w, h, seed, F):
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
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field(F, cx, cy, cw, gh + 4, 2 if gh > 150 else 1))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed, F):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    # light ruled paper under everything that is not panel, pedestal or frieze
    o.append(C.dark_ground((0, 0, w, h), "L"))
    o.append(C.bead_moulding(0, 2.5, w, 1., False))
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .62
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
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
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field(F, cx, cy, cw, ch, 2))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    o.append(_sun_boss(cx, cy - ch / 2 + 2, min(13., ch * .055)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_ribbon_face(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(F, tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _sun_boss(x, y, r):
    """A small rayed sun carved where the crest springs from the cartouche."""
    cv = C.Canvas()
    rays = []
    for i in range(16):
        a = TAU * i / 16
        R = r * (1.75 if i % 2 else 1.4)
        b = .2 if i % 2 else .26
        rays.append([(x + r * .8 * math.cos(a - b), y + r * .8 * math.sin(a - b)), (x + R * math.cos(a), y + R * math.sin(a)),
                     (x + r * .8 * math.cos(a + b), y + r * .8 * math.sin(a + b))])
    cv.obj(rays, 1.)
    for i, rp in enumerate(rays):
        cv.hair(C.hatch_poly(rp, 360 * i / 16 + 90, 1.5) if i % 2 else [[rp[0], rp[1]]])
    disc = C._ell_pts(x, y, r, r, 36)[:-1]
    cv.obj([disc], 1.5)
    cv.hair([C._ell_pts(x, y, rr, rr, 30) for rr in (r - 2.5, r - 4.5) if rr > 1])
    cv.hair(C.hatch_poly(C._ell_pts(x, y, max(1, r - 5.5), max(1, r - 5.5), 24)[:-1], 0, 1.5))
    cv.heavy([C._ell_pts(x, y, 1, 1, 8)])
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    F = _facts(ctx)
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _band(w, h, seed, F)
    elif h <= 260:
        body = _medium(w, h, seed, F)
    else:
        body = _tall(w, h, seed, F)
    return C.svg_doc(w, h, body)
