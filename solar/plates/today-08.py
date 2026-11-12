"""today-08 "Seven days out": the week's solar forecast.

Subject: Parker's ground-mounted solar array on Sauvie Island under a big sun (today, ~70 kWh, the
sunniest day), with the week's rain (Fri to Sun) sweeping in from the right as heavy cumulus and
slanting showers; Mt. Hood on the horizon, the Multnomah Channel in front. The pedestal tablet
carries seven roundels, one per day, each engraved with its weather and a sun whose size follows
that day's expected kWh. The crest is a sun grown out of acanthus fingers.
Easter egg: a great blue heron standing in the reeds of the channel bank (the short band hides a
tiny one beside the panels)."""
import sys
import math
import random
import re
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_n = C._n

# fallback week (the page on 2026-11-11): (day, condition, kWh)
_WEEK = [("Today", "Cloudy", 70), ("Thu", "Cloudy", 53), ("Fri", "Showers", 9), ("Sat", "Drizzle", 12),
         ("Sun", "Rain", 22), ("Mon", "Drizzle", 63), ("Tue", "Drizzle", 33)]


def _week(ctx):
    s = (ctx or {}).get("sample", "") or ""
    got = re.findall(r"(Today|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+-?\d+\S*\s+-?\d+\S*\s+([A-Za-z ]+?)\s*\S\s*\d+% rain\s*~(\d+) kWh", s)
    wk = [(d, c.strip(), int(k)) for d, c, k in got][:7]
    if len(wk) < 7:
        names = [d for d, _, _ in wk]
        for d, c, k in _WEEK:
            if len(wk) >= 7:
                break
            if d not in names:
                wk.append((d, c, k))
    return wk[:7]


def _circ(cx, cy, r, n=40, a0=0., a1=TAU):
    return C._ell_pts(cx, cy, r, r, n, a0, a1)


def _ell(cx, cy, rx, ry, n=40, a0=0., a1=TAU):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def _hrule(poly, pitch, phase=0.):
    return C.hatch_poly(poly, 0, pitch, phase)


def _clipg(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------------
# engraved motifs (all into a Canvas)
# ------------------------------------------------------------------------------------------------

def _cloud(cv, cx, cy, s, rng, rain_to=None, dark=1.):
    """A cumulus bank: two tiers of overlapping puffs, each ruled across in fine lines with a thin
    lit crescent at upper left and its underside cut dark; a flat shadowed base; optional
    slanting rain falling to y=rain_to."""
    puffs = []
    k = rng.randint(5, 7)
    for i in range(k):
        t = i / (k - 1) - .5
        r = s * (.26 + .2 * (1 - abs(t) * 1.6) * rng.uniform(.75, 1.2))
        puffs.append((cx + t * s * 1.75 + rng.uniform(-.07, .07) * s, cy - r * .6 + rng.uniform(-.04, .04) * s, r))
    for i in range(rng.randint(2, 3)):
        t = (i + .5) / 3 - .5
        r = s * rng.uniform(.3, .42)
        puffs.append((cx + t * s * 1.1 + rng.uniform(-.1, .1) * s, cy - s * rng.uniform(.5, .7), r))
    order = sorted(puffs, key=lambda p: p[1] - p[2] * .2)
    if rain_to:
        cv.obj([], 0)
        x0, x1 = cx - s * .85, cx + s * .8
        x = x0
        j = 0
        while x < x1:
            y = cy + 2 + (j * 7 % 5)
            while y < rain_to:
                L = 4 + (j * 13 % 7)
                cv.hair([(x, y), (x - L * .28, min(rain_to, y + L))])
                y += L + 2.5 + (j * 5 % 3)
            x += 2.4
            j += 1
    for (px, py, r) in order:
        p = _circ(px, py, r, 36)
        cv.obj([p], .5 if r < 6 else 1.)
        lit_c = (px - r * .16, py - r * .16, r * .86)
        for l in _hrule(p, 2, (px * 3) % 2):
            (ax, y), (bx, _) = l
            # cut the lit crescent out of the ruling
            dy = y - lit_c[1]
            if abs(dy) < lit_c[2] and y < py:
                hw = math.sqrt(lit_c[2] ** 2 - dy * dy)
                ox = math.sqrt(max(0., r * r - (y - py) ** 2))
                a = lit_c[0] - hw
                if a > ax + .5:
                    cv.hair([(ax, y), (min(a, bx), y)])
                cv.hair([(max(ax, a + min(3., ox * .25)), y), (bx, y)])
            else:
                cv.hair(l)
        lo = [(px + r * math.cos(a), py + r * math.sin(a)) for a in [(-.1 + 1.2 * i / 20) * PI for i in range(21)]]
        inner = [(px - r * .12 + r * .92 * math.cos(a), py - r * .3 + r * .92 * math.sin(a)) for a in [(1.1 - 1.2 * i / 20) * PI for i in range(21)]]
        cv.obj([lo + inner], 0)
        cv.line(_hrule(lo + inner, 2, (px * 3) % 2))
    base = [(cx - s * 1.05, cy - 2), (cx + s * 1.05, cy - 2), (cx + s * .9, cy + 2.5), (cx - s * .95, cy + 2.5)]
    cv.obj([base], 0)
    cv.line(_hrule(base, 1.5, .25))


def _sun(cv, cx, cy, r, glory, sky_top, rays=72):
    """A rayed sun: a glory of alternating long and short rays cut through the sky ruling, a disc
    engraved in concentric rings with a dark limb."""
    g = _circ(cx, cy, glory, 72)
    cv.obj([g], 0)
    for i in range(rays):
        a = TAU * (i + .5) / rays
        L = glory * (1. if i % 2 == 0 else .72) * (1 if i % 4 else 1.0)
        r0 = r * 1.18
        cv.hair([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + L * math.cos(a), cy + L * math.sin(a))])
        if i % 2 == 0:
            r1 = r * 1.18
            cv.hair([(cx + r1 * math.cos(a + .012), cy + r1 * math.sin(a + .012)),
                     (cx + L * .7 * math.cos(a + .012), cy + L * .7 * math.sin(a + .012))])
    disc = _circ(cx, cy, r, 48)
    cv.obj([disc], 1.5)
    rr = r - 2.
    while rr > 1.5:
        cv.hair(_circ(cx, cy, rr, max(10, int(rr * 2))))
        rr -= 2.
    # dark limb lower right
    lim = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [(-.1 + .75 * i / 16) * PI for i in range(17)]]
    cv.line([(cx + (r - 1.2) * math.cos(a), cy + (r - 1.2) * math.sin(a)) for a in [(-.05 + .65 * i / 14) * PI for i in range(15)]])


def _hood(cv, cx, base, s, glory_disc=None):
    """Mt. Hood: snowfield above a ragged line, the east face ruled, ridges falling away."""
    pk = [(-58, 0), (-40, -10), (-28, -20), (-14, -29), (-5, -36), (0, -40), (5, -35), (14, -28), (28, -18), (44, -8), (62, 0)]
    P = [(cx + x * s, base + y * s) for x, y in pk]
    cv.obj([P], 1.)
    snowline = [(-26, -17), (-21, -20), (-18, -16), (-14, -21), (-10, -17), (-6, -23), (-2, -19), (2, -25), (6, -20), (10, -24), (14, -19), (19, -22), (24, -16)]
    S = [(cx + x * s, base + y * s) for x, y in snowline]
    cv.hair(S)
    low = S + [(cx + 62 * s, base), (cx - 58 * s, base)]
    cv.hair(_hrule(low, 1.5, .25))
    face = [(cx, base - 40 * s), (cx + 5 * s, base - 35 * s), (cx + 14 * s, base - 28 * s), (cx + 28 * s, base - 18 * s),
            (cx + 24 * s, base - 16 * s), (cx + 10 * s, base - 24 * s), (cx + 2 * s, base - 25 * s)]
    cv.hair(C.hatch_poly(face, 70, 2))
    for k in range(9):
        cv.hair([(cx - (1 + k * 1.9) * s, base - (38.5 - k * 1.6) * s), (cx - (4 + k * 2.9) * s, base - (24 - k * .6) * s)])
    for k in range(5):
        cv.hair([(cx - (2 + k * 4) * s, base - (36 - k * 3.5) * s), (cx - (6 + k * 5) * s, base - (26 - k * 2) * s)])
        cv.hair([(cx + (3 + k * 3) * s, base - (36 - k * 3) * s), (cx + (6 + k * 4) * s, base - (27 - k * 2.4) * s)])


def _panels(cv, x0, x1, yh, y_gnd, rows, seed):
    """Rows of tilted panels on posts receding to the horizon (yh); y_gnd: where the nearest row
    stands. Glass ruled dark in diagonal bulino with a sky-glint left bright, cell rules, white
    aluminium frames, a cast shadow on the grass."""
    cx = (x0 + x1) / 2
    Hc = 3.
    Zn = 6.
    F = (y_gnd - yh) / Hc * Zn

    def pr(X, Y, Z):
        return (cx + X * F / Z, yh + (Hc - Y) * F / Z)
    half = (x1 - x0) / 2 * Zn / F
    Zs = [Zn + 3.4 * i for i in range(rows)][::-1]
    for Z in Zs:
        npan = max(3, int(round(half * 2 / 1.15)))
        pw = half * 2 / npan
        sh = [pr(-half - .2, 0, Z - .1), pr(half + .4, 0, Z - .1), pr(half + .7, 0, Z - .75), pr(-half + .1, 0, Z - .75)]
        cv.obj([sh], 0)
        cv.line(_hrule(sh, 1.5, .25))
        for i in range(npan):
            X0 = -half + i * pw + .03
            X1 = X0 + pw - .06
            q = [pr(X0, 1.9, Z + 1.1), pr(X1, 1.9, Z + 1.1), pr(X1, .55, Z), pr(X0, .55, Z)]
            cv.obj([], 0)
            for X in (X0 + .12, X1 - .12):
                cv.line([pr(X, .55, Z), pr(X, 0, Z)])
                cv.hair([pr(X, 1.9, Z + 1.1), pr(X, 0, Z + 1.1)])
            cv.obj([q], 1.)
            ang = math.degrees(math.atan2(q[1][1] - q[0][1], q[1][0] - q[0][0]))
            gl0 = .55 + .25 * ((i * 37 + seed) % 7) / 7
            for l in C.hatch_poly(q, 62 + ang, 1.5, (i * .5) % 1.5, .5):
                (ax, ay), (bx, by) = l
                # glint: a bright diagonal band across the glass
                u = (ax - q[3][0]) / max(1., q[2][0] - q[3][0])
                if abs(u - gl0) < .07:
                    continue
                cv.hair(l)
            for k in (1, 2, 3, 4, 5):
                t = k / 6
                a = (q[0][0] + (q[1][0] - q[0][0]) * t, q[0][1] + (q[1][1] - q[0][1]) * t)
                b = (q[3][0] + (q[2][0] - q[3][0]) * t, q[3][1] + (q[2][1] - q[3][1]) * t)
                cv.hair([a, b])
            for t in (1 / 3, 2 / 3):
                m0 = (q[0][0] + (q[3][0] - q[0][0]) * t, q[0][1] + (q[3][1] - q[0][1]) * t)
                m1 = (q[1][0] + (q[2][0] - q[1][0]) * t, q[1][1] + (q[2][1] - q[1][1]) * t)
                cv.hair([m0, m1])
            cv.line([q[3], q[2]])
            cv.line([q[0], q[1]])
    return pr(half, 0, Zn)


def _heron(cv, x, y, s, mirror=False):
    """A great blue heron standing, feet at (x, y), about 30*s tall, facing left (mirror: right)."""
    m = -1 if mirror else 1

    def P(pts):
        return [(x + m * px * s, y + py * s) for px, py in pts]
    body = P([(-4, -16), (-1, -19), (4, -19.5), (9, -17.5), (13, -14), (12, -12.5), (6, -12.5), (0, -13), (-3.5, -14.2)])
    neck = P([(-3, -17), (-5, -20), (-4.8, -23.5), (-2.5, -26), (-3, -29), (-5.5, -30.5), (-7.5, -30), (-6.6, -28.4),
              (-5.2, -27.4), (-4.6, -25.8), (-6.8, -23), (-7, -19.5), (-4.6, -15.6)])
    head = P([(-5, -30.8), (-7.8, -31), (-14.5, -29.6), (-8, -29.2), (-6.4, -28.4)])
    cv.obj([], 0)
    cv.line(P([(1.5, -13), (1.2, -6.5), (1.6, 0)]))
    cv.line(P([(4, -13), (4.2, -6.5), (5.4, 0)]))
    cv.hair(P([(1.6, 0), (-1.4, .2)]))
    cv.hair(P([(5.4, 0), (8.4, .3)]))
    cv.obj([body], 1.)
    for k in range(5):
        t = k / 4
        cv.hair(P([(-1 + t * 7, -18.6 + t * .2), (5 + t * 7, -13.2 + t * .6)]))
    cv.hair(P([(0, -14.5), (6, -13.6), (11.5, -13)]))
    cv.obj([neck], 1.)
    cv.hair(P([(-4.4, -22), (-5.8, -21)]))
    cv.hair(P([(-4.6, -19.4), (-6, -18.6)]))
    cv.obj([head], 1.)
    cv.line(P([(-5.8, -31.4), (-3, -31.6), (1, -30.4)]))  # crest plume
    cv.hair(P([(-8, -29.9), (-14, -29.6)]))


def _reeds(cv, x0, x1, y, h, seed):
    rng = random.Random(seed)
    cv.obj([], 0)
    x = x0
    while x < x1:
        hh = h * rng.uniform(.45, 1.)
        lean = rng.uniform(-.25, .25) * hh
        cv.hair([(x, y), (x + lean * .4, y - hh * .5), (x + lean, y - hh)])
        if rng.random() < .25:
            tx, ty = x + lean, y - hh
            cv.line([(tx, ty), (tx + lean * .05, ty - 3.5)])
        x += rng.uniform(1.4, 2.6)


def _vignette(cv, X, Y, W, H, seed, level=2, wk=None):
    """The scene in the box X,Y,W,H (drawn a little past it; the caller clips to the field)."""
    rng = random.Random(seed)
    yh = Y + H * (.6 if level else .62)
    sun_k = max(.55, min(1.15, (wk[0][2] if wk else 70) / 62.))
    sr = min(W, H) * .085 * sun_k * (1.25 if level == 0 else 1)
    sx, sy = X + W * .3, Y + H * (.28 if level else .3)
    # sky ruling: darker aloft
    sky = [(X - 4, Y - 4), (X + W + 4, Y - 4), (X + W + 4, yh + 1), (X - 4, yh + 1)]
    cv.obj([sky], 0)
    for l in _hrule(sky, 2, .5):
        yy = l[0][1]
        t = (yy - Y) / max(1, yh - Y)
        if t < .32:
            cv.line(l)
        else:
            cv.hair(l)
    # the sun
    _sun(cv, sx, sy, sr, sr * (2.6 if level else 2.2), Y)
    # weather from the right: Fri-Sun rain
    if level >= 1:
        n_cl = 3 if level == 2 else 2
        for i in range(n_cl):
            cs = min(W * (.17 if level == 2 else .2), H * .23) * (1 - .15 * i) * rng.uniform(.9, 1.05)
            ccx = X + W * (.88 - .26 * i) + rng.uniform(-.03, .03) * W
            ccy = Y + H * (.2 + .09 * (i % 2)) + rng.uniform(-.02, .02) * H
            _cloud(cv, ccx, ccy, cs, rng, rain_to=yh + 2 if i < n_cl - 1 or level == 1 else None)
        # a small fair-weather cloud drifting across the sun's glory
        _cloud(cv, sx - sr * 1.4, sy + sr * 1.9, min(W * .07, H * .07), rng)
    else:
        _cloud(cv, X + W * .8, Y + H * .4, W * .12, rng, rain_to=yh + 2)
    # Mt. Hood and distant ridges
    hs = H * (.0042 if level == 2 else .0036) * (1 if level else .8)
    if level >= 1:
        ridge = [(X - 4, yh)] + [(X + W * t / 30, yh - H * (.025 + .018 * math.sin(t / 30 * 9 + seed % 7) + .01 * math.sin(t * 1.3))) for t in range(31)] + [(X + W + 4, yh), (X + W + 4, yh + 2), (X - 4, yh + 2)]
        cv.obj([ridge], .5)
        cv.hair(C.hatch_poly(ridge, 0, 1.5, .25))
        _hood(cv, X + W * .66, yh - H * .02, hs * 1.0 * H / 100 * 1.6 if False else W * .0042 * (1.2 if level == 2 else 1))
        # Douglas firs on the far bank
        cv.obj([], 0)
    # the field
    gnd = [(X - 4, yh), (X + W + 4, yh), (X + W + 4, Y + H + 4), (X - 4, Y + H + 4)]
    cv.obj([gnd], .5)
    yw = Y + H * (.86 if level == 2 else .9)
    ys = []
    z = 1.
    while True:
        yy = yh + (yw - yh) * (1 / z) ** -1 * 0 + (yh - yh)
        break
    yy = yh + 1.2
    p = 1.5
    while yy < yw:
        cv.hair([(X - 4, yy), (X + W + 4, yy)])
        yy += p
        p = min(3.2, p * 1.12)
    # furrows converging on the vanishing point
    vp = (X + W * .5, yh - H * .1)
    for k in range(-18, 19):
        bx = X + W * .5 + k * W * .07
        t0 = .06
        a = (vp[0] + (bx - vp[0]) * t0 * 1.6, vp[1] + (yw - vp[1]) * t0 * 1.6)
        if a[1] < yh + 1:
            f = (yh + 1 - vp[1]) / (yw - vp[1])
            a = (vp[0] + (bx - vp[0]) * f, yh + 1)
        cv.hair([a, (bx, yw)])
    # the array
    rows = 3 if level == 2 else (2 if level == 1 else 1)
    _panels(cv, X + W * (.04 if level else .1), X + W * (.74 if level else .9), yh, yw - H * (.03 if level else .02), rows, seed)
    # the channel in front
    wat = [(X - 4, yw), (X + W + 4, yw), (X + W + 4, Y + H + 4), (X - 4, Y + H + 4)]
    cv.obj([wat], .5)
    yy = yw + 1.5
    j = 0
    while yy < Y + H + 4:
        x = X - 4 + (j * 3.7) % 9
        while x < X + W + 4:
            L = 5 + (j * 7 + int(x)) % 9
            near_sun = abs(x - sx) < sr * 1.2
            if near_sun:
                cv.line([(x, yy), (x + L * .6, yy)])
            else:
                cv.hair([(x, yy), (x + L, yy)])
            x += L + (1.5 if near_sun else 2.2)
        yy += 1.5 if yy < yw + 4 else 2
        j += 1
    # Easter egg: the heron in the reeds
    hx = X + W * (.86 if level else .14)
    if level >= 1:
        _reeds(cv, X + W * .7, X + W + 4, yw + 1.5, H * .07, seed)
        _heron(cv, hx, yw + 1.2, H * (.0068 if level == 2 else .006), mirror=False)
        _reeds(cv, hx + W * .04, hx + W * .12, yw + 2.5, H * .05, seed + 1)
    else:
        _heron(cv, X + W * .1, yh + (yw - yh) * .9, H * .005, mirror=True)


def _field_poly(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a, b), (cx - a, cy - b, 2 * a, 2 * b)


# ------------------------------------------------------------------------------------------------
# the seven-day tablet and the ribbon
# ------------------------------------------------------------------------------------------------

def _day_glyph(cv, cx, cy, r, cond, kwh):
    cv.obj([_circ(cx, cy, r, 32)], 1.)
    c = cond.lower()
    wet = any(k in c for k in ("rain", "shower", "drizzle", "storm"))
    sr = r * (.22 + .34 * max(0., min(1., kwh / 70.)))
    sx, sy = cx - r * .2, cy - r * .2
    # rays
    for i in range(12):
        a = TAU * i / 12
        cv.hair([(sx + sr * 1.3 * math.cos(a), sy + sr * 1.3 * math.sin(a)), (sx + sr * 1.75 * math.cos(a), sy + sr * 1.75 * math.sin(a))])
    cv.obj([_circ(sx, sy, sr, 18)], .5)
    cv.hair(_hrule(_circ(sx, sy, sr, 18), 1.5, .2) if sr > 2 else [])
    # cloud
    if "clear" not in c and "sun" not in c:
        cl = []
        for px, py, pr in ((-.3, .22, .3), (.05, .08, .36), (.38, .26, .26)):
            cl.append((cx + px * r, cy + py * r, pr * r))
        for px, py, pr in cl:
            q = _circ(px, py, pr, 18)
            cv.obj([q], .5)
            cv.hair([l for l in _hrule(q, 1.5, .5) if l[0][1] > py])
        if wet:
            cv.obj([], 0)
            nn = 3 if "drizzle" in c else 4
            for k in range(nn):
                x = cx - r * .4 + k * r * .8 / (nn - 1)
                cv.line([(x, cy + r * .5), (x - r * .1, cy + r * .78)])


def _tablet(tx, ty, tw, th, wk):
    o = [C.dark_ground((tx + 1.5, ty + 1.5, tw - 3, th - 3), "S")]
    cv = C.Canvas()
    n = len(wk)
    r = min(th * .78, tw / n * .38)
    step = (tw - 8) / n
    for i, (d, c, k) in enumerate(wk):
        cx = tx + 4 + step * (i + .5)
        cy = ty + th / 2
        if i:
            cv.obj([], 0)
            px = tx + 4 + step * i
            cv.line([(px - step / 2 + r + 1.5, cy), (px + step / 2 - r - 1.5, cy)])
            cv.hair([(px, cy - 2), (px + 1.6, cy), (px, cy + 2), (px - 1.6, cy), (px, cy - 2)])
        _day_glyph(cv, cx, cy, r, c, k)
    o.append(cv.svg())
    return "".join(o)


def _ribbon_fill(cx, cy, w, h, arch, centre, wk=None):
    top = [(x, y - h / 2 + 1.2) for x, y in centre]
    bot = [(x, y + h / 2 - 1.2) for x, y in centre[::-1]]
    poly = top + bot
    cv = C.Canvas()
    cv.obj([], 0)
    for l in C.hatch_poly(poly, 0, 3, .7):
        cv.hair(l)
    # the week's expected solar, engraved as a curve across the face, a pip on each day
    if wk:
        n = len(centre)
        mx = max(k for _, _, k in wk) or 1
        pts = []
        for i, (_, _, k) in enumerate(wk):
            t = .12 + .76 * i / (len(wk) - 1)
            j = t * (n - 1)
            j0 = int(j)
            f = j - j0
            x = centre[j0][0] + (centre[min(n - 1, j0 + 1)][0] - centre[j0][0]) * f
            y = centre[j0][1] + (centre[min(n - 1, j0 + 1)][1] - centre[j0][1]) * f
            pts.append((x, y + h * .26 - h * .52 * k / mx))
        sm = []
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            for q in range(8):
                u = q / 8
                e = (1 - math.cos(PI * u)) / 2
                sm.append((ax + (bx - ax) * u, ay + (by - ay) * e))
        sm.append(pts[-1])
        cv.obj([], 0)
        cv.line(sm)
        for x, y in pts:
            cv.obj([_circ(x, y, 2.1, 12)], 1.)
            cv.hair([(x - 1, y), (x + 1, y)])
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# the crest: a sun grown from acanthus
# ------------------------------------------------------------------------------------------------

def _sun_crest(cx, cy, size, seed):
    cv = C.Canvas()
    rng = random.Random(seed)
    r = size * .3
    for side in (-1, 1):
        for j, a in enumerate((12, 38, 64)):
            ang = math.radians(-90 + side * (90 - a + 8))
            ln = size * (.62 + .16 * (j == 2)) * rng.uniform(.95, 1.04)
            b = side * .55
            C._finger(cv, cx + side * r * .6, cy, ang, ln, ln * .12, b, b * 5.5)
    for i in range(16):
        a = -PI + PI * (i + .5) / 16
        ln = r * (1.75 if i % 2 else 1.4)
        poly = [(cx + r * 1.05 * math.cos(a - .07), cy + r * 1.05 * math.sin(a - .07)),
                (cx + ln * math.cos(a), cy + ln * math.sin(a)),
                (cx + r * 1.05 * math.cos(a + .07), cy + r * 1.05 * math.sin(a + .07))]
        cv.obj([poly], .5)
        cv.hair([(cx + r * 1.1 * math.cos(a + .03), cy + r * 1.1 * math.sin(a + .03)), (cx + ln * .92 * math.cos(a), cy + ln * .92 * math.sin(a))])
    disc = _circ(cx, cy, r, 40)
    cv.obj([disc], 1.5)
    rr = r - 1.8
    while rr > 1.5:
        cv.hair(_circ(cx, cy, rr, max(10, int(rr * 2))))
        rr -= 2.
    # a calm face, eyes closed: brows, lids, nose, a slight smile
    cv.obj([], 0)
    e = r * .3
    for sd in (-1, 1):
        cv.hair([(cx + sd * e * .35, cy - e * .9), (cx + sd * e * 1.0, cy - e * 1.15), (cx + sd * e * 1.6, cy - e * .9)])
        cv.line([(cx + sd * e * .5, cy - e * .35), (cx + sd * e * .95, cy - e * .1), (cx + sd * e * 1.4, cy - e * .35)])
    cv.hair([(cx, cy - e * .6), (cx - e * .15, cy + e * .5), (cx + e * .2, cy + e * .6)])
    cv.line([(cx - e * .7, cy + e * 1.05), (cx, cy + e * 1.3), (cx + e * .7, cy + e * 1.05)])
    calyx = _ell(cx, cy + r * 1.02, r * .55, r * .22, 24)
    cv.obj([calyx], 1.)
    cv.hair(_hrule(_ell(cx, cy + r * 1.02, r * .55, r * .22, 20), 1.5, .3))
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts (adapted from the house frame_plate)
# ------------------------------------------------------------------------------------------------

def _scene(cid, cx, cy, cw, ch, seed, level, wk):
    poly, (X, Y, W, H) = _field_poly(cx, cy, cw, ch)
    cv = C.Canvas()
    _vignette(cv, X, Y, W, H, seed, level, wk)
    return _clipg(cid, C._d(poly, True, 0), cv.svg())


def _layout_band(w, h, seed, wk):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.6, 120)
    o.append(C._clip(C._uid("b8", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fld = _ell(cx, cy, rx - 4.2, ry - 4.2, 64)
    cv = C.Canvas()
    _vignette(cv, cx - rx, cy - ry, 2 * rx, 2 * ry, seed, 0, wk)
    o.append(_clipg(C._uid("b8v", w, h), C._d(fld, True, 0), cv.svg()))
    o.append(f'<path d="{C._d(fld, True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, wk):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.55)
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
                   max_n=9, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m8", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_scene(C._uid("m8v", w, h), cx, cy, cw, gh + 4, seed, 1 if gh < 170 else 2, wk))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, wk):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # the light ruled ground the crest rises through (no blank paper above the panel)
    o.append(C.dark_ground((0, 0, w, py0 - 3.5), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .52, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .145, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=8, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t8", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_scene(C._uid("t8v", w, h), cx, cy, cw, ch, seed, 2, wk))
    o.append(_sun_crest(cx, cy - ch / 2 + 6, min((cy - ch / 2 + 4) / .9, 92), rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    by = cy + ch * .47
    bsvg, centre = C.ribbon_banner(cx, by, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_ribbon_fill(cx, by, cw * 1.4, bh, .04, centre, wk))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(C.dark_ground((0, py + 2, w, ped_h - 2), "L"))
    o.append(p)
    o.append(_tablet(tx + 2, ty + 2, tw - 3, th - 3, wk))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f8", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 8
    wk = _week(ctx)
    if h < 110:
        body = _layout_band(w, h, seed, wk)
    elif h <= 260:
        body = _layout_medium(w, h, seed, wk)
    else:
        body = _layout_tall(w, h, seed, wk)
    return C.svg_doc(w, h, body)
