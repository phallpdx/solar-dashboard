"""nearby-03 : Sky events ahead (meteor showers, space-station passes, asteroids, a cloudy night).
House Codex frame round a bespoke night-sky vignette over Sauvie Island: Leonid meteors streaking
out of the sickle of Leo, today's thin crescent moon (phase from ctx date) with earthshine, the
space station crossing on a dotted track, a small passing asteroid, the cloud deck that clouds us
out tonight, Mt. Hood snow-lit on the horizon, the cottonwood shore and the Multnomah Channel.
The pedestal tablet is an engraved calendar of the next four meteor-shower peaks (burst size by
rate); the ribbon carries a row of stars.
Easter egg: two of the "meteors" are a pair of crossed drumsticks with bead tips, streaking
across the upper sky."""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d, pat = C._n, C._d, C.pat
K = 2 ** (-1 / 2.6)
TAU = math.tau


# ------------------------------------------------------------------------------------------
# small geometry
# ------------------------------------------------------------------------------------------

def _ell(cx, cy, rx, ry, n=32, a0=0., a1=TAU):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + (0 if a1 - a0 >= TAU - 1e-9 else 1))]


def _star(x, y, r, rot=0.):
    pts = []
    for i in range(8):
        a = rot + math.pi * i / 4
        rr = r if i % 2 == 0 else r * .32
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return pts


def _moon_frac(date):
    try:
        d = datetime.date.fromisoformat(date)
    except Exception:
        d = datetime.date(2026, 11, 11)
    jd = d.toordinal() + 1721424.5 + .25          # ~ 6 pm local, roughly
    p = ((jd - 2451550.26) / 29.530588853) % 1.
    return p, (1 - math.cos(TAU * p)) / 2


def _hrows(top, bot, x0, x1, pitch, phase, keep, step=1.):
    """Horizontal hatch rows inside the shape bounded by top(x) .. bot(x); keep(x, y, frac) picks
    which samples carry a line.  Returns polylines."""
    out = []
    ymin = min(top(x0 + (x1 - x0) * i / 40) for i in range(41))
    ymax = max(bot(x0 + (x1 - x0) * i / 40) for i in range(41))
    y = ymin + phase
    while y < ymax:
        run = []
        x = x0
        while x <= x1:
            t, b = top(x), bot(x)
            ok = t < y < b and keep(x, y, (y - t) / max(.1, b - t))
            if ok:
                run.append((x, y))
            elif run:
                if len(run) > 1:
                    out.append([run[0], run[-1]])
                run = []
            x += step
        if len(run) > 1:
            out.append([run[0], run[-1]])
        y += pitch
    return out


# ------------------------------------------------------------------------------------------
# sky motifs
# ------------------------------------------------------------------------------------------

def _meteor(cv, hx, hy, ang, L, r):
    """A tapered meteor streak, head at (hx, hy) travelling along ang (radians)."""
    c, s = math.cos(ang), math.sin(ang)
    nx, ny = -s, c
    tx, ty = hx - c * L, hy - s * L
    left, right = [], []
    for i in range(13):
        t = i / 12
        px, py = tx + c * L * t, ty + s * L * t
        wv = r * t ** 1.7
        left.append((px + nx * wv, py + ny * wv))
        right.append((px - nx * wv, py - ny * wv))
    head = [(hx + r * math.cos(ang + math.pi / 2 - math.pi * k / 8), hy + r * math.sin(ang + math.pi / 2 - math.pi * k / 8))
            for k in range(1, 8)]
    poly = left + head + right[::-1]
    cv.obj([poly], .5)
    # bulino along the shaded underside, fading to the tail
    for f in (.45, .72):
        cv.hair([(tx + c * L * t - nx * r * f * t ** 1.7, ty + s * L * t - ny * r * f * t ** 1.7)
                 for t in [.35 + .65 * k / 10 for k in range(11)]])
    cv.hair([(hx - c * r * .2 + nx * r * .3, hy - s * r * .2 + ny * r * .3), (hx + c * r * .5, hy + s * r * .5)])


def _drumstick(cv, hx, hy, ang, L, r):
    """Easter egg: a drumstick flying like a meteor (bead tip leading)."""
    c, s = math.cos(ang), math.sin(ang)
    nx, ny = -s, c
    bx, by = hx - c * L, hy - s * L
    side = []
    for i in range(11):
        t = i / 10
        wv = r * (.55 if t < .62 else .55 - .32 * (t - .62) / .38)
        side.append((bx + c * L * t * .9, by + s * L * t * .9, wv))
    lft = [(x + nx * w, y + ny * w) for x, y, w in side]
    rgt = [(x - nx * w, y - ny * w) for x, y, w in side]
    butt = [(bx - c * r * .5 * math.sin(math.pi * k / 6) + nx * r * .55 * math.cos(math.pi * k / 6),
             by - s * r * .5 * math.sin(math.pi * k / 6) + ny * r * .55 * math.cos(math.pi * k / 6)) for k in range(1, 6)]
    cv.obj([lft + rgt[::-1] + butt[::-1]], .5)
    for f in (-.25, -.42):
        cv.hair([(x + nx * w * f * 1.6, y + ny * w * f * 1.6) for x, y, w in side[1:-1]])
    ex, ey = hx - c * r * .35, hy - s * r * .35
    bead = [(ex + c * r * .75 * math.cos(t) - nx * r * .5 * math.sin(t), ey + s * r * .75 * math.cos(t) - ny * r * .5 * math.sin(t))
            for t in [TAU * k / 16 for k in range(16)]]
    cv.obj([bead], .5)
    cv.hair([(ex - nx * r * .25 + c * r * .4 * math.cos(t), ey - ny * r * .25 + s * r * .4 * math.cos(t)) for t in (1.2, 2.2)])
    return [(bx - c * (6 + k * 5), by - s * (6 + k * 5)) for k in range(3)]


def _moon(cv, cx, cy, r, phase, frac):
    disc = _ell(cx, cy, r, r, 40)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 30, 1.5))
    waxing = phase < .5
    sg = 1 if waxing else -1
    f = max(frac, .17)                      # 4 % is a hair; engrave it legibly
    limb = [(cx + sg * r * math.cos(t), cy + r * math.sin(t)) for t in [-math.pi / 2 + math.pi * k / 24 for k in range(25)]]
    term = [(cx + sg * r * (1 - 2 * f) * math.cos(t), cy + r * math.sin(t)) for t in [math.pi / 2 - math.pi * k / 24 for k in range(25)]]
    cv.obj([limb + term], 1.)
    if f > .02:
        mid = [(cx + sg * r * (1 - f) * math.cos(t), cy + r * .92 * math.sin(t)) for t in [-1.2 + 2.4 * k / 16 for k in range(17)]]
        cv.hair(mid)


def _iss(cv, x, y, s):
    cv.obj([[(x - s * .9, y - s * .08), (x + s * .9, y - s * .08), (x + s * .9, y + s * .08), (x - s * .9, y + s * .08)]], .5)
    for sx in (-.75, -.45, .45, .75):
        for sy in (-1, 1):
            px, py = x + sx * s, y + sy * s * .42
            p = [(px - s * .12, py - s * .3), (px + s * .12, py - s * .3), (px + s * .12, py + s * .3), (px - s * .12, py + s * .3)]
            cv.obj([p], .5)
            cv.hair(C.hatch_poly(p, 90, 1.5))
    m = [(x - s * .2, y - s * .2), (x + s * .2, y - s * .2), (x + s * .2, y + s * .2), (x - s * .2, y + s * .2)]
    cv.obj([m], .5)
    cv.hair(C.hatch_poly(m, 0, 1.5))


def _rock(cv, x, y, r, rng):
    pts = [(x + r * (1 + .22 * math.sin(3 * a + 1) + .1 * rng.random()) * math.cos(a) * 1.25,
            y + r * (1 + .22 * math.sin(3 * a + 1) + .1 * rng.random()) * math.sin(a))
           for a in [TAU * k / 18 for k in range(18)]]
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, 20, 1.5, 0, r * .25))
    for k in range(3):
        a = rng.random() * TAU
        cr = _ell(x + r * .45 * math.cos(a), y + r * .4 * math.sin(a), r * .22, r * .16, 10)
        cv.obj([cr], .5)


def _cloud(cv, bumps, base, sag=0.):
    x0 = min(c - r for c, r in bumps)
    x1 = max(c + r for c, r in bumps)

    def top(x):
        h = 0.
        for c, r in bumps:
            if abs(x - c) < r:
                h = max(h, math.sqrt(r * r - (x - c) ** 2))
        return base - h

    def bot(x):
        return base + sag * math.sin(math.pi * (x - x0) / (x1 - x0))

    n = int((x1 - x0) / 1.5) + 2
    tp = [(x0 + (x1 - x0) * i / n, top(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]
    bp = [(x0 + (x1 - x0) * i / n, bot(x0 + (x1 - x0) * i / n)) for i in range(n, -1, -1)]
    cv.obj([tp + bp], 1.)
    cv.hair(_hrows(top, bot, x0, x1, 2., 1., lambda x, y, f: f > .38))
    cv.hair(_hrows(top, bot, x0, x1, 2., 2., lambda x, y, f: f > .7))
    # billow edges: each bump's inner rim, lit from the upper left
    for c, r in bumps:
        arc = [(c + (r - 1.6) * math.cos(a), base - (r - 1.6) * math.sin(a)) for a in [.35 + 2.3 * k / 14 for k in range(15)]]
        arc = [p for p in arc if p[1] < top(p[0]) + 4 and p[1] > top(p[0]) + .5]
        if len(arc) > 2:
            cv.hair(arc)


def _mount(cv, cx, by, hw, hh, rng):
    """Mt. Hood: snowy, gullied left flank in moonlight, hatched right flank."""
    def prof(t):                                    # t in [-1, 1]; Hood: steep summit, broad shoulders
        u = 1 - abs(t)
        return hh * (.55 * u ** 2.4 + .45 * u ** .9)
    ridge_l = [(cx + hw * (t - 1), by - prof(t - 1) + (rng.random() - .5) * hh * .03 * (2 - t))
               for t in [k / 13 for k in range(14)]]
    ridge_r = [(cx + hw * 1.1 * t, by - prof(t) + (rng.random() - .5) * hh * .03 * (1 + t))
               for t in [k / 13 for k in range(1, 14)]]
    peak = ridge_l[-1]
    poly = [(cx - hw, by + 2)] + ridge_l + ridge_r + [(cx + hw * 1.1, by + 2)]
    cv.obj([poly], 1.)
    # shaded right flank: from a spine slightly right of the peak
    spine = [(peak[0] + hw * .12 * t + hw * .03 * math.sin(t * 9), peak[1] + (by - peak[1]) * t) for t in [k / 12 for k in range(13)]]
    sh = spine + ridge_r[::-1][:0] + [(cx + hw * 1.1, by + 2)] + ridge_r[::-1]
    sh = spine + [(cx + hw * 1.1, by + 2)] + ridge_r[::-1]
    cv.hair(C.hatch_poly(sh, 62, 1.5))
    cv.hair(C.hatch_poly(sh, -25, 3, 0, 2))
    cv.hair(spine)
    # gullies on the lit flank, running from the ridge down-left
    for k in range(7):
        t = .2 + .1 * k
        sx = peak[0] + (cx - hw - peak[0]) * t * .3 + hw * .05 * k * .4
        sy = peak[1] + (by - peak[1]) * t * .4
        g = [(sx - hw * .05 * u + math.sin(u * 5 + k) * 1.2, sy + (by - sy) * u * .8) for u in [j / 8 for j in range(9)]]
        cv.hair(g)
    # foothills below the snowline
    fh = [(cx - hw * 1.05, by + 2)] + [(cx - hw + hw * 2.2 * t, by - hh * .2 * (.5 + .5 * math.sin(t * 7 + 1)) * (1 - abs(2 * t - 1) * .5))
                                       for t in [k / 20 for k in range(21)]] + [(cx + hw * 1.2, by + 2)]
    cv.obj([fh], .5)
    cv.hair(C.hatch_poly(fh, 0, 1.5))


def _treeline(x0, x1, y, hmax, rng):
    pts = [(x0, y + 3)]
    x = x0
    while x < x1:
        if rng.random() < .25:                       # a fir
            w = 4 + rng.random() * 4
            hh = hmax * (.7 + .3 * rng.random())
            pts += [(x, y - hh * .3), (x + w / 2, y - hh), (x + w, y - hh * .3)]
            x += w
        else:                                        # a cottonwood crown
            w = 7 + rng.random() * 10
            hh = hmax * (.35 + .4 * rng.random())
            for k in range(7):
                a = math.pi - math.pi * k / 6
                pts.append((x + w / 2 + w / 2 * math.cos(a), y - hh * .4 - hh * .6 * math.sin(a) - rng.random()))
            x += w * .85
    pts.append((x1, y + 3))
    return pts


def vignette(X, Y, W, H, clip_d, ctx, small=False):
    """The night sky over Sauvie Island, filling the bbox, clipped to clip_d."""
    seed = sum(map(ord, ctx.get("date", "")))
    rng = random.Random(seed * 31 + 7)
    phase, frac = _moon_frac(ctx.get("date", ""))
    o = []
    hz = Y + H * (.74 if not small else .7)                 # horizon
    o.append(C.dark_ground((X, Y, W, hz - Y + 2), "G"))
    o.append(C.dark_ground((X, hz, W, Y + H - hz), "M"))
    S = min(W, H)
    mw_t = [(X - 5 + (W + 10) * t, Y + H * (.62 - .55 * t) + H * .04 * math.sin(t * 9 + seed)) for t in [k / 24 for k in range(25)]]
    mw_b = [(x + H * .02, y + H * (.11 + .04 * math.sin(i * .9))) for i, (x, y) in enumerate(mw_t)]
    o.append(C.dark_ground(mw_t + mw_b[::-1], "M"))
    cv = C.Canvas()
    for i in range(int(W * H / 600)):
        t = rng.random()
        j = int(t * 24)
        u = rng.random()
        px = mw_t[j][0] * (1 - u) + mw_b[j][0] * u
        py = mw_t[j][1] * (1 - u) + mw_b[j][1] * u
        if py < hz - 6:
            cv.obj([_star(px, py, .9 + rng.random() * .6, 0)], 0)
    # moon, upper left (a waning crescent before dawn shows its lit limb to the east/left)
    mr = max(5.5, S * .11)
    mx, my = X + W * .22, Y + H * .21
    # stars
    nst = int(W * H / (260 if not small else 160))
    for _ in range(min(nst, 140)):
        sx, sy = X + rng.random() * W, Y + rng.random() * (hz - Y - 4)
        if math.hypot(sx - mx, sy - my) < mr * 1.6:
            continue
        r = .9 + rng.random() ** 3 * (2.2 if not small else 1.4)
        cv.obj([_star(sx, sy, r, rng.random() * .4)], .5 if r > 1.4 else 0)
    # Leo's sickle, the Leonid radiant, upper right
    lx, ly, ls = X + W * .8, Y + H * .16, S * .0032
    sickle = [(0, 0), (-4, -6), (-2, -13), (4, -16), (9, -12), (6, 6), (24, 4), (30, 10)]
    for i, (a, b) in enumerate(sickle):
        cv.obj([_star(lx + a * ls * 10, ly + b * ls * 10, (2.6 if i in (0, 6) else 1.9) * max(.7, S / 200), .2)], .5)
    rx, ry = lx + 2 * ls * 10, ly - 6 * ls * 10
    if not small:
        for k, (ang, L, rr, dd) in enumerate(((150, .34, 2.2, .12), (170, .26, 1.8, .2), (200, .3, 2.0, .1),
                                               (128, .22, 1.6, .16), (110, .18, 1.5, .14), (215, .18, 1.4, .3))):
            a = math.radians(ang + rng.uniform(-4, 4))
            d0 = S * dd + S * .05
            hx, hy = rx + math.cos(a) * (d0 + W * L), ry + math.sin(a) * (d0 + W * L)
            _meteor(cv, hx, hy, a, W * L, rr * S / 150 + 1.)
    else:
        for ang, L in ((152, .4), (172, .3)):
            a = math.radians(ang)
            hx, hy = rx + math.cos(a) * W * (L + .1), ry + math.sin(a) * W * (L + .1)
            _meteor(cv, hx, hy, a, W * L, 1.6)
        dx, dy, dl = X + W * .4, Y + H * .42, S * .3      # Easter egg: crossed drumsticks
        _drumstick(cv, dx + dl * .35, dy - dl * .25, math.radians(-35), dl, 1.8)
        _drumstick(cv, dx - dl * .35, dy - dl * .25, math.radians(-145), dl, 1.8)
    _moon(cv, mx, my, mr, phase, frac)
    if not small:
        # Easter egg: crossed drumsticks streaking across the upper middle sky
        dx, dy, dl = X + W * .47, Y + H * .3, S * .23
        glints = []
        glints += _drumstick(cv, dx + dl * .35, dy - dl * .25, math.radians(-35), dl, max(2.6, S * .024))
        glints += _drumstick(cv, dx - dl * .35, dy - dl * .25, math.radians(-145), dl, max(2.6, S * .024))
        # the space station on its dotted track, south-west to south-east
        ix, iy = X + W * .5, Y + H * .47
        _iss(cv, ix, iy, max(4., S * .05))
        # 2026 VP8 tumbling past
        _rock(cv, X + W * .86, Y + H * .5, max(2.5, S * .028), rng)
        # the cloud deck that clouds us out tonight
        cb = hz - H * .07
        _mount(cv, X + W * .62, hz + 1, W * .3, H * .25, rng)
        _cloud(cv, [(X + W * (-.02 + .085 * k), S * (.07 + .04 * ((k * 7) % 3))) for k in range(4)], cb, 3)
        _cloud(cv, [(X + W * (.74 + .1 * k), S * (.06 + .035 * ((k * 5) % 3))) for k in range(4)], cb + H * .045, 2)
        _cloud(cv, [(X + W * (.12 + .075 * k), S * (.035 + .025 * (k % 2))) for k in range(4)], Y + H * .53, 2)
    else:
        _mount(cv, X + W * .62, hz + 1, W * .2, H * .22, rng)
    o.append(cv.svg())
    if not small:
        tr = [(ix - W * .25 + W * .5 * t, iy + H * .09 * (2 * t - 1) ** 2 - H * .02) for t in [k / 30 for k in range(31)]]
        tr = [p for p in tr if abs(p[0] - ix) > S * .04]
        o.append(f'<path d="{_d(tr)}" stroke="#fff" stroke-width="1" stroke-dasharray="1 2.5" fill="none"/>')
        ar = X + W * .86
        o.append(f'<path d="M{_n(ar - S * .035)},{_n(Y + H * .5 - 1.5)}h{_n(-S * .06)}M{_n(ar - S * .04)},{_n(Y + H * .5 + 1.5)}h{_n(-S * .04)}" stroke="#fff" stroke-width=".5" stroke-dasharray="2 1.5"/>')
        o.append("".join(f'<path d="{_d([(gx, gy), (gx + .1, gy + .1)])}" stroke="#fff" stroke-width="1"/>' for gx, gy in glints[:0]))
    # the cottonwood shore
    tl = _treeline(X - 2, X + W + 2, hz + 1, max(4., H * .07), rng)
    o.append(f'<path d="{_d(tl, True, .2)}" fill="#000" stroke="none"/>')
    # moon glade on the channel
    gl = []
    yy = hz + 5
    k = 0
    while yy < Y + H - 1:
        half = (2 + (yy - hz) * .25) * (1 + .4 * math.sin(k * 2.3))
        off = math.sin(k * 1.7) * 2
        gl.append(f"M{_n(mx + off - half)},{_n(yy)}h{_n(half * 2)}")
        if k % 2 == 0:
            for sx in (-1, 1):
                gl.append(f"M{_n(mx + sx * (half + 3 + k % 5))},{_n(yy)}h{_n(sx * (2 + k % 3))}")
        yy += 2.
        k += 1
    o.append(f'<path d="{"".join(gl)}" stroke="#fff" stroke-width="1" shape-rendering="crispEdges"/>')
    cid = C._uid("nb3", X, Y, W, H)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{"".join(o)}</g>'


# ------------------------------------------------------------------------------------------
# tablet & ribbon fills
# ------------------------------------------------------------------------------------------

_SHOWERS = [(1, 3, 80), (4, 22, 18), (5, 6, 50), (8, 12, 100), (10, 21, 20), (11, 17, 15), (12, 14, 150), (12, 22, 10)]


def _tablet(tx, ty, tw, th, ctx):
    try:
        d0 = datetime.date.fromisoformat(ctx.get("date", ""))
    except Exception:
        d0 = datetime.date(2026, 11, 11)
    ev = []
    for yr in (d0.year, d0.year + 1):
        for m, dd, z in _SHOWERS:
            dt = datetime.date(yr, m, dd)
            if dt >= d0:
                ev.append(((dt - d0).days, z))
    ev = sorted(ev)[:4]
    span = max(ev[-1][0] + 4, 30)
    x0, x1 = tx + 3, tx + tw - 3
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{pat("G")}" stroke="none"/>']
    cy = ty + th / 2 + .5
    o.append(f'<path d="M{_n(x0 + 6)},{_n(cy)}H{_n(x1 - 2)}" stroke="#fff" stroke-width="1" stroke-dasharray="1 2"/>')
    cv = C.Canvas()
    # today: a crescent at the left end
    cv.obj([_ell(x0 + 4, cy, 3.2, 3.2, 16)], .5)
    cv.hair(C.hatch_poly(_ell(x0 + 4, cy, 3.2, 3.2, 16), 30, 1.5))
    cv.obj([[(x0 + 4 + 3.2 * math.cos(t), cy + 3.2 * math.sin(t)) for t in [math.pi / 2 + math.pi * k / 10 for k in range(11)]]
            + [(x0 + 4 - 2.2 * math.cos(t), cy + 3.2 * math.sin(t)) for t in [-math.pi / 2 + math.pi * k / 10 for k in range(11)]]], .5)
    rays = []
    for days, z in ev:
        bx = x0 + 12 + (x1 - x0 - 22) * days / span
        R = min(th / 2 - 2.5, 3 + (th / 2 - 5) * math.sqrt(z / 150))
        nr = 8 + int(z / 10)
        for k in range(nr):
            a = TAU * k / nr
            rr = R * (1 if k % 2 == 0 else .62)
            rays.append(f"M{_n(bx + 2.2 * math.cos(a))},{_n(cy + 2.2 * math.sin(a))}L{_n(bx + rr * math.cos(a))},{_n(cy + rr * math.sin(a))}")
        cv.obj([_star(bx, cy, 2.6, .39)], .5)
    o.append(cv.svg())
    o.append(f'<path d="{"".join(rays)}" stroke="#fff" stroke-width="1"/>')
    return "".join(o)


def _ribbon_face(centre, h):
    n = len(centre)
    top, bot = [], []
    for i, (x, y) in enumerate(centre):
        a = centre[max(0, i - 1)]
        b = centre[min(n - 1, i + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        top.append((x + nx * (h / 2 - 2.6), y + ny * (h / 2 - 2.6)))
        bot.append((x - nx * (h / 2 - 2.6), y - ny * (h / 2 - 2.6)))
    face = top[2:-2] + bot[2:-2][::-1]
    o = [f'<path d="{_d(face, True, .1)}" fill="{pat("L")}" stroke="none"/>']
    cv = C.Canvas()
    for i in range(4, n - 3, 4):
        x, y = centre[i]
        cv.obj([_star(x, y, h * .26, .39)], .5)
    o.append(cv.svg())
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts (copied from engraving_codex and changed so the vignette fills the whole field)
# ------------------------------------------------------------------------------------------

def _field_d(ix, iy, iw, ih, pad=5.5):
    a, b = iw / 2 / K + 6, ih / 2 / K + 6
    return _d(C._superellipse(ix + iw / 2, iy + ih / 2, a - pad, b - pad), True, .1), (ix + iw / 2 - a, iy + ih / 2 - b, 2 * a, 2 * b)


def _layout_band(w, h, seed, ctx):
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
    clip = _d(_ell(cx, cy, rx - 2.2, ry - 2.2, 64), True, .1)
    o.append(vignette(cx - rx, cy - ry, 2 * rx, 2 * ry, clip, ctx, small=True))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 2, ry - 2, 64), True, .1)}" stroke="#000" stroke-width="1" fill="none"/>')
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
    cw = min(w * .44, gh * 1.7)
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
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    clip, (bx, by, bw, bh) = _field_d(ix, iy, iw, ih)
    o.append(vignette(bx, by, bw, bh, clip, ctx, small=gh < 120))
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
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .62
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
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    clip, (bx, by, bw, bh) = _field_d(ix, iy, iw, ih)
    o.append(vignette(bx, by, bw, bh, clip, ctx))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh_ = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_ribbon_face(centre, bh_))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, ctx))
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


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", "")))
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx, .8 if h > 420 else 1.)
    return C.svg_doc(w, h, body)
