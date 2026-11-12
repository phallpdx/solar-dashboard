"""almanac-02 "This day in history": the Codex frame around a history frontispiece.

The page is a chronicle of today's date: what happened around here (Washington admitted as a
state, 1889), what happened elsewhere (Columbia, Gemini, Leibniz), how much of the year is gone.
So the cartouche holds an open chronicle with the day's story rising out of it: the local
mountain (Rainier when the page says Washington, Hood otherwise) over the river, a launch climbing
on its smoke column when the page has a space mission, the moon in tonight's phase. The ribbon
carries today's date in engraved Roman capitals; the pedestal tablet is the year itself, a ruled
bar cut dark for the days already behind you, with the month ticks and the solstice marked.
Hourglass finial on the crest. Easter egg: a Sauvie Island heron fishing in the river reeds.
"""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
CR = ' shape-rendering="crispEdges"'
PI = math.pi


# ------------------------------------------------------------------------------------------------
# page reading
# ------------------------------------------------------------------------------------------------

def _facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    low = s.lower()
    try:
        day = datetime.date.fromisoformat((ctx or {}).get("date", "")[:10])
    except Exception:
        day = datetime.date(2026, 11, 11)
    local = s.split("Elsewhere")[0] if "Elsewhere" in s else s
    ll = local.lower()
    if "washington" in ll or "seattle" in ll or "rainier" in ll:
        peak = "rainier"
    else:
        peak = "hood"
    space = any(k in low for k in ("nasa", "shuttle", "gemini", "apollo", "rocket", "launch", "sputnik",
                                   "spacecraft", "orbit", "satellite", "space"))
    return dict(day=day, peak=peak, space=space, seed=day.toordinal())


def _moon_age(day):
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    t = datetime.datetime(day.year, day.month, day.day, 20)
    return ((t - ref).total_seconds() / 86400.) % 29.530588


# ------------------------------------------------------------------------------------------------
# small drawing helpers
# ------------------------------------------------------------------------------------------------

def _rows(x0, x1, y0, y1, pitch=2., phase=.25):
    """Horizontal device-aligned hairlines (y = k*pitch + phase) as path data."""
    o = []
    y = math.ceil((y0 - phase) / pitch) * pitch + phase
    while y < y1:
        o.append(f"M{_n(x0)},{_n(y)}H{_n(x1)}")
        y += pitch
    return "".join(o)


def _poly_d(polys):
    return "".join(_d(p, tol=0) for p in polys)


def _hrows_in(poly, pitch, phase=.25, dash=None, rng=None):
    """Horizontal hatch inside a polygon, optionally broken into dashes (water)."""
    out = []
    for seg in C.hatch_poly(poly, 0, pitch, phase):
        (ax, ay), (bx, by) = seg
        if ax > bx:
            ax, bx = bx, ax
        y = math.floor(ay * 2) / 2 + .25
        if dash and rng:
            x = ax
            while x < bx:
                L = rng.uniform(*dash)
                out.append([(x, y), (min(bx, x + L), y)])
                x += L + rng.uniform(1.5, 4)
        else:
            out.append([(ax, y), (bx, y)])
    return out


# ------------------------------------------------------------------------------------------------
# the vignette: a chronicle opened on today, the day's story rising from it
# ------------------------------------------------------------------------------------------------

def _mountain(cv, F, x0, x1, base, top, kind, rng):
    w = x1 - x0
    px = x0 + w * (.46 if kind == "rainier" else .5)
    pts = []
    n = 48
    for i in range(n + 1):
        t = i / n
        x = x0 + w * t
        u = (x - px) / (w * .5)
        if kind == "rainier":   # broad glaciated dome with a flat summit and a shoulder
            hgt = max(0., 1 - abs(u) ** 1.5) ** 1.15
            hgt = min(hgt, .93 + .04 * math.cos(u * 9))
            if u > 0:
                hgt = max(hgt - .06 * math.exp(-((u - .35) / .12) ** 2), 0)
        else:                   # Hood: a sharp horn
            hgt = max(0., 1 - abs(u)) ** 1.3 * (1 - .12 * max(0., .25 - abs(u)) * 4) ** 0 
        hgt *= 1 + .02 * math.sin(t * 37 + rng.random())
        pts.append((x, base - (base - top) * hgt))
    poly = pts + [(x1, base + 2), (x0, base + 2)]
    cv.obj([poly], 1.)
    H = base - top
    # lit face first over the whole mass: light snowfield ruling
    cv.hair(C.hatch_poly(poly, -30, 3))
    # shadow face: right of a ridge line wandering down from the summit, deep bulino
    ridge = [(px + H * .05 * math.sin(k * .9) + k * H * .03, top + 1.5 + k * H / 10) for k in range(11)]
    rpts = [p for p in pts if p[0] > ridge[0][0] + .5]
    shadow = ridge + [(x1, base + 2)] + rpts[::-1]
    cv.hair(C.hatch_poly(shadow, 45, 1.5))
    cv.hair(C.hatch_poly(shadow, -45, 3))
    # glaciers: broken crevasse strokes radiating down the fall line from under the summit
    for k in range(9):
        ang = math.radians(98 + k * 5.5)
        L = H * rng.uniform(.35, .7)
        sx0, sy0 = px - 1 - k * .4, top + H * .1 + k * .6
        d = rng.uniform(1, 3)
        while d < L:
            seg = rng.uniform(2, 5)
            p0 = (sx0 + math.cos(ang) * d, sy0 + math.sin(ang) * d)
            p1 = (sx0 + math.cos(ang) * (d + seg), sy0 + math.sin(ang) * (d + seg))
            (cv.line if rng.random() < .35 else cv.hair)([p0, p1])
            d += seg + rng.uniform(1.5, 4)
    cv.heavy(ridge[:7])
    # forest skirt: firs of varied height on a dark base
    fy = base - H * .14
    trees = []
    x = x0 + rng.uniform(0, 2)
    while x < x1:
        th_ = rng.uniform(.5, 1.) * H * .16
        tw_ = th_ * .32
        ty_ = fy + rng.uniform(-2, 3)
        trees.append((x, ty_, th_, tw_))
        x += tw_ * rng.uniform(.9, 1.4)
    skirt = [(x0, base + 2)] + [(t[0], t[1]) for t in trees] + [(x1, base + 2)]
    cv.obj([skirt], 0)
    cv.hair(C.hatch_poly(skirt, 90, 1.5))
    cv.hair(C.hatch_poly(skirt, 0, 1.5, .25))
    for (tx, ty_, th_, tw_) in sorted(trees, key=lambda t: t[1]):
        fir = [(tx, ty_ - th_)]
        for k in range(1, 4):
            yk = ty_ - th_ + th_ * k / 3
            fir.append((tx + tw_ * k / 3 * 1.1, yk))
            if k < 3:
                fir.append((tx + tw_ * k / 3 * .45, yk))
        fir = fir + [(2 * tx - q[0], q[1]) for q in fir[:0:-1]]
        cv.obj([fir + [(tx + tw_ * .2, ty_ + 3), (tx - tw_ * .2, ty_ + 3)]], .5)
        cv.hair(C.hatch_poly(fir, 90, 1.5, .25 + (tx % 1.5) * 0))
    return poly


def _smoke_and_rocket(cv, sx, ground, top, scale, rng):
    """A launch: billowing smoke column from the ground up to a shuttle stack climbing at the top."""
    H = ground - top
    rk = scale * 1.0
    ry = top + rk * 6
    # smoke billows, larger toward the ground, painted top-down so the lower ones overlap
    billows = []
    y = ry + rk * 3
    r = rk * .9
    while y < ground + r:
        billows.append((sx + rng.uniform(-.6, .6) * r * .5, y, r))
        y += r * .9
        r = min(r * 1.12, scale * 3.6)
    for bx, by, br in billows:
        circ = _ell(bx, by, br, br * .9, 26)[:-1]
        cv.obj([circ], .5)
        # shade the right / under side of each billow with fine curved lines
        for k in range(1, 4):
            f = 1 - k * .22
            arc = _ell(bx + br * (1 - f) * .7, by + br * (1 - f) * .3, br * f, br * f * .9, 24, -PI * .35, PI * .6)
            cv.hair(arc)
        cv.hair(C.hatch_poly(_ell(bx + br * .55, by + br * .35, br * .45, br * .45, 16)[:-1], 45, 1.5))
    # flame
    fl = [(sx - rk * .7, ry + rk * 1.6), (sx, ry + rk * 4.2), (sx + rk * .7, ry + rk * 1.6)]
    cv.obj([fl], .5)
    cv.hair([[(sx + dx, ry + rk * 1.7), (sx + dx * .4, ry + rk * 3.4)] for dx in (-.4 * rk, 0, .4 * rk)])
    # external tank with pointed nose, two boosters, orbiter in front
    tw = rk * .9
    tank = [(sx - tw / 2, ry + rk * 1.6), (sx - tw / 2, ry - rk * 3.4), (sx, ry - rk * 5), (sx + tw / 2, ry - rk * 3.4),
            (sx + tw / 2, ry + rk * 1.6)]
    cv.obj([tank], 1.)
    cv.hair(C.hatch_poly(tank, 90, 1.5))
    for side in (-1, 1):
        bx = sx + side * (tw / 2 + rk * .28)
        srb = [(bx - rk * .26, ry + rk * 1.9), (bx - rk * .26, ry - rk * 2.6), (bx, ry - rk * 3.3), (bx + rk * .26, ry - rk * 2.6),
               (bx + rk * .26, ry + rk * 1.9)]
        cv.obj([srb], .5)
        cv.hair([[(bx + rk * .1 * side, ry - rk * 2.5), (bx + rk * .1 * side, ry + rk * 1.8)]])
    orb = [(sx, ry - rk * 2.6), (sx + rk * .38, ry - rk * 1.9), (sx + rk * .42, ry - rk * .2), (sx + rk * 1.5, ry + rk * 1.2),
           (sx + rk * 1.5, ry + rk * 1.6), (sx - rk * 1.5, ry + rk * 1.6), (sx - rk * 1.5, ry + rk * 1.2), (sx - rk * .42, ry - rk * .2),
           (sx - rk * .38, ry - rk * 1.9)]
    cv.obj([orb], 1.)
    cv.hair(C.hatch_poly(orb, 0, 1.5, .25, .3)[len(C.hatch_poly(orb, 0, 1.5)) // 2:])
    cv.heavy([(sx - rk * .22, ry - rk * 2.05), (sx + rk * .22, ry - rk * 2.05)])
    return billows


def _moon(cv, mx, my, r, age):
    disc = _ell(mx, my, r, r, 32)[:-1]
    cv.obj([disc], 1.)
    ph = age / 29.530588
    k = math.cos(ph * 2 * PI)          # terminator ellipse x-scale
    lit_right = ph < .5
    pts_dark = []
    for i in range(33):
        t = -PI / 2 + PI * i / 32
        pts_dark.append((mx + (-1 if lit_right else 1) * r * math.cos(t), my + r * math.sin(t)))
    for i in range(33):
        t = PI / 2 - PI * i / 32
        pts_dark.append((mx + (1 if lit_right else -1) * r * k * math.cos(t), my + r * math.sin(t)))
    cv.hair(C.hatch_poly(pts_dark, 45, 1.5))
    cv.hair(C.hatch_poly(pts_dark, -45, 3))
    cv.hair(C.hatch_poly(disc, 0, 3, .25, .8))


def _heron(cv, x, y, s):
    """Easter egg: a grey heron standing in the shallows, about 7*s tall, facing left."""
    body = [(x - 1.6 * s, y - 3.6 * s), (x - .2 * s, y - 4.3 * s), (x + 1.4 * s, y - 3.9 * s), (x + 2.3 * s, y - 2.8 * s),
            (x + .8 * s, y - 2.6 * s), (x - .9 * s, y - 2.9 * s)]
    cv.obj([body], .5)
    cv.hair(C.hatch_poly(body, 30, 1.5))
    cv.line([(x - 1.4 * s, y - 3.7 * s), (x - 1.7 * s, y - 5.1 * s), (x - 1.1 * s, y - 6.2 * s), (x - 1.5 * s, y - 6.9 * s)])
    cv.heavy([(x - 1.5 * s, y - 6.9 * s), (x - 1.3 * s, y - 7. * s)])
    cv.line([(x - 1.5 * s, y - 6.9 * s), (x - 3.1 * s, y - 6.5 * s)])
    cv.hair([(x - .9 * s, y - 6.9 * s), (x + .2 * s, y - 6.6 * s)])
    cv.hair([[(x + .1 * s, y - 2.8 * s), (x, y)], [(x + .5 * s, y - 2.7 * s), (x + .9 * s, y)]])


def _book(cv, x0, x1, top, bottom, rng):
    """An open chronicle across the foreground: two curved pages of ruled 'text', a dark gutter,
    the page block's edges below."""
    cx = (x0 + x1) / 2
    w = x1 - x0
    H = bottom - top
    lift = H * .22
    n = 30

    def top_edge(t):    # t 0 outer .. 1 spine
        return top + lift * math.sin(t * PI * .5) ** 1.5 * .9 - lift * .35 * math.sin(t * PI)

    def bot_edge(t):
        return bottom - H * .28 + lift * .5 * t ** 2

    stack = [(x0 - 3, bot_edge(0) + 2), (cx, bottom), (x1 + 3, bot_edge(0) + 2), (x1 + 3, bottom + 8), (x0 - 3, bottom + 8)]
    cv.obj([[(x0 - 4, bot_edge(0) - 2), (cx, bottom + 1), (x1 + 4, bot_edge(0) - 2), (x1 + 4, bottom + 10), (x0 - 4, bottom + 10)]], 1.)
    cv.hair(C.hatch_poly([(x0 - 4, bot_edge(0) - 2), (cx, bottom + 1), (x1 + 4, bot_edge(0) - 2), (x1 + 4, bottom + 10), (x0 - 4, bottom + 10)], -45, 1.5))
    for k in range(3):
        cv.hair([(x0 - 3 + k, bot_edge(0) + k * 1.5), (cx, bottom - 1 + k * 1.5 - 4), (x1 + 3 - k, bot_edge(0) + k * 1.5)])
    for side in (-1, 1):
        ox = cx + side * w / 2
        tp = [(ox + (cx - ox) * i / n, top_edge(i / n)) for i in range(n + 1)]
        bp = [(ox + (cx - ox) * i / n, bot_edge(i / n)) for i in range(n + 1)]
        page = tp + bp[::-1]
        cv.obj([page], 1.)
        # text lines: rows that follow the page's curl, broken into words
        rows = int((bot_edge(0) - top_edge(0)) / 3)
        for r in range(1, rows):
            f = r / rows
            row = []
            for i in range(2, n - 1):
                t = i / n
                y = top_edge(t) + (bot_edge(t) - top_edge(t)) * f
                row.append((ox + (cx - ox) * t, y))
            if side == 1 and r == rows // 2 and rows >= 4:
                # Easter egg: one 'line' of the chronicle is a bar of swing (long-short pairs)
                hh = 2.2
                k0 = 1
                for pair in range(4):
                    i1, i2 = k0 + pair * 6, k0 + pair * 6 + 3
                    if i2 >= len(row):
                        break
                    tops = []
                    for ii, long_ in ((i1, True), (i2, False)):
                        hx_, hy_ = row[ii]
                        cv.heavy(_ell(hx_, hy_ + .3, .5, .35, 8))
                        cv.line([(hx_ + .9, hy_ + .3), (hx_ + .9, hy_ - hh * 1.6)])
                        tops.append((hx_ + .9, hy_ - hh * 1.6))
                        if long_:
                            cv.heavy([(hx_ + 1.9, hy_ + .2), (hx_ + 2.1, hy_ + .2)])
                    cv.heavy(tops)
                    a_, b_ = tops
                    cv.line([(b_[0] - 1.6, b_[1] + 1.3 + (a_[1] - b_[1]) * .0), (b_[0], b_[1] + 1.3)])
                continue
            j = 0
            while j < len(row) - 1:
                L = rng.randint(1, 4)
                cv.hair(row[j:j + L + 1])
                j += L + 1
        # gutter shadow: dense lines close to the spine
        gut = [(cx + side * w * .07, top_edge(.86)), (cx, top_edge(1)), (cx, bot_edge(1)), (cx + side * w * .07, bot_edge(.86))]
        cv.hair(C.hatch_poly(gut, 90, 1.5))
        # curled corner of each outer leaf
        cv.line([(ox, top_edge(0)), (ox + side * -3, top_edge(0) - 2), (ox + side * -6, top_edge(.1))])
    cv.heavy([(cx, top_edge(1)), (cx, bot_edge(1))])
    return top_edge(.5)


def vignette(field_pts, ctx, mode="tall", uid="v"):
    """Fill the whole cartouche field (a closed polygon) with the history frontispiece."""
    F = _facts(ctx)
    rng = random.Random(F["seed"])
    xs = [p[0] for p in field_pts]
    ys = [p[1] for p in field_pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    o = []
    # sky: ruled, denser toward the zenith (bulino tone by pitch 1 / 2 on the device grid)
    sky = _rows(x0, x1, y0, y1, 2, .25) + _rows(x0, x1, y0, y0 + h * .3, 2, 1.25)
    o.append(f'<path d="{sky}" stroke="#000" stroke-width=".5"{CR}/>')
    cv = C.Canvas()
    small = mode == "band"
    horizon = y0 + h * (.7 if small else .6)
    # moon in today's phase
    mr = max(3.5, min(w, h) * (.075 if not small else .13))
    mx = x0 + w * (.2 if not small else .26)
    my = y0 + h * (.2 if not small else .3)
    _moon(cv, mx, my, mr, _moon_age(F["day"]))
    # clouds: rolled banks, white tops, ruled undersides
    for (cxf, cyf, cwf) in (((.62, .22, .34), (.86, .34, .22), (.3, .4, .2)) if not small else ((.7, .3, .3),)):
        ccx, ccy, cww = x0 + w * cxf, y0 + h * cyf, w * cwf
        top_pts = []
        nb = 5
        for i in range(nb):
            bx = ccx - cww / 2 + cww * (i + .5) / nb
            br = cww / nb * (.75 + .35 * math.sin(i * 2.3 + F["seed"]))
            top_pts += _ell(bx, ccy, br, br * .7, 12, PI, 2 * PI)
        cloud = top_pts + [(ccx + cww / 2 + 2, ccy + 1), (ccx - cww / 2 - 2, ccy + 1)]
        cv.obj([cloud], .5)
        cv.hair(C.hatch_poly(cloud, 0, 1.5, .25))
        cv.obj([[(p[0], p[1] + 1.2) for p in top_pts[::1]] + [(ccx - cww / 2, ccy - 1)]], 0)
        cv.hair(C.hatch_poly([(p[0], p[1] + 1.2) for p in top_pts] + [(ccx - cww / 2, ccy - 1)], 0, 3, 1.75))
    # far range: dark cross-hatched foothills along the horizon
    far = [(x0, horizon + 1)] + [(x0 + w * i / 40, horizon - h * (.05 + .03 * math.sin(i * .7 + rng.random()) + .02 * math.sin(i * 2.1)))
                                 for i in range(41)] + [(x1, horizon + 1)]
    cv.obj([far], .5)
    cv.hair(C.hatch_poly(far, 45, 2))
    cv.hair(C.hatch_poly(far, -45, 3))
    # the mountain
    mx0, mx1 = x0 + w * (.06 if not small else .2), x0 + w * (.7 if not small else .8)
    _mountain(cv, None, mx0, mx1, horizon, y0 + h * (.18 if not small else .22), F["peak"], rng)
    # river: broken water ruling, reflection-dark band under the mountain
    wb = y1 if small else horizon + h * .16
    water = [(x0, horizon + .5), (x1, horizon + .5), (x1, wb), (x0, wb)]
    cv.obj([water], 0)
    cv.hair(_hrows_in(water, 2, .25, (8, 30), rng))
    cv.hair(_hrows_in([(x0, horizon + .5), (x1, horizon + .5), (x1, horizon + (wb - horizon) * .3), (x0, horizon + (wb - horizon) * .3)], 2, 1.25, (6, 22), rng))
    for k in range(int((mx1 - mx0) / 2.5)):
        rx_ = mx0 + w * .05 + k * 2.5
        if rx_ > mx1 - w * .05:
            break
        y = horizon + 1.5
        while y < wb - 1:
            L = rng.uniform(1.5, 5)
            cv.hair([(rx_, y), (rx_, min(wb - 1, y + L))])
            y += L + rng.uniform(1.5, 4)
    # launch
    if F["space"]:
        _smoke_and_rocket(cv, x0 + w * (.82 if not small else .78), horizon + 1, y0 + h * .1,
                          max(2.2, min(w, h) * (.028 if not small else .05)), rng)
    if small:
        _book(cv, x0 + w * .3, x1 - w * .3, y0 + h * .74, y1 - h * .05, rng)
    else:
        # reeds and the heron (Easter egg) at the near bank
        hx = x0 + w * .22
        for k in range(9):
            bx = hx - 6 + k * 1.6 + rng.uniform(-.4, .4)
            cv.hair([(bx, wb), (bx + rng.uniform(-1.5, 1.5), wb - rng.uniform(4, 9))])
        _book(cv, x0 + w * .1, x1 - w * .1, wb - h * .02, y1 - h * .02, rng)
    o.append(cv.svg())
    clip = f'<clipPath id="{uid}"><path d="{_d(field_pts, True, 0)}"/></clipPath>'
    return clip + f'<g clip-path="url(#{uid})">' + "".join(o) + "</g>"


# ------------------------------------------------------------------------------------------------
# lettering: Roman capitals as engraved strokes
# ------------------------------------------------------------------------------------------------

def _roman(n):
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    s = ""
    for v, t in vals:
        while n >= v:
            s += t
            n -= v
    return s


_GLYPH = {   # strokes in a unit box (x right, y down); (advance, [(weight, polyline)])
    "I": (.42, [(1.5, [(.21, 0), (.21, 1)]), (.5, [(0, 0), (.42, 0)]), (.5, [(0, 1), (.42, 1)])]),
    "V": (.8, [(1.5, [(.05, 0), (.4, 1)]), (.5, [(.4, 1), (.75, 0)]), (.5, [(-.08, 0), (.2, 0)]), (.5, [(.62, 0), (.88, 0)])]),
    "X": (.8, [(1.5, [(.08, 0), (.72, 1)]), (.5, [(.72, 0), (.08, 1)]), (.5, [(-.05, 0), (.25, 0)]), (.5, [(.58, 0), (.85, 0)]),
               (.5, [(-.05, 1), (.25, 1)]), (.5, [(.58, 1), (.85, 1)])]),
    "L": (.62, [(1.5, [(.15, 0), (.15, 1)]), (.5, [(-.02, 0), (.34, 0)]), (.5, [(-.02, 1), (.62, 1), (.62, .78)])]),
    "C": (.78, [(1.5, [(.72, .12)] + [(.42 - .38 * math.sin(t * PI / 10), .5 - .5 * math.cos(t * PI / 10)) for t in range(11)][1:]
                + [(.72, .88)])]),
    "D": (.82, [(.5, [(.08, 0), (.08, 1)]), (1.5, [(.08, 0)] + [(.4 + .36 * math.sin(t * PI / 10), .5 - .5 * math.cos(t * PI / 10)) for t in range(11)]
                + [(.08, 1)])]),
    "M": (1.05, [(.5, [(.08, 1), (.12, 0)]), (1.5, [(.12, 0), (.52, 1)]), (.5, [(.52, 1), (.9, 0)]), (1.5, [(.9, 0), (.95, 1)]),
                 (.5, [(-.05, 1), (.25, 1)]), (.5, [(.8, 1), (1.1, 1)])]),
    ".": (.5, [(1.5, [(.22, .45), (.28, .55)]), (1.5, [(.28, .45), (.22, .55)])]),
    " ": (.4, []),
}


def _letter_along(centre, text, hgt, track=.18):
    """Lay text along a polyline (the ribbon's face centre). Returns {weight: [polylines]}."""
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    total_adv = sum(_GLYPH[c][0] + track for c in text) - track
    L = total_adv * hgt
    s = (S[-1] - L) / 2
    out = {.5: [], 1.: [], 1.5: []}

    def at(sv):
        sv = min(max(sv, 0), S[-1])
        for i in range(1, len(S)):
            if S[i] >= sv:
                f = (sv - S[i - 1]) / max(1e-6, S[i] - S[i - 1])
                ax, ay = centre[i - 1]
                bx, by = centre[i]
                ang = math.atan2(by - ay, bx - ax)
                return ax + (bx - ax) * f, ay + (by - ay) * f, ang
        return centre[-1][0], centre[-1][1], 0.

    for ch in text:
        adv, strokes = _GLYPH[ch]
        for wgt, pl in strokes:
            q = []
            for gx, gy in pl:
                px, py, a = at(s + gx * hgt)
                dy = (gy - .5) * hgt
                q.append((px - math.sin(a) * dy, py + math.cos(a) * dy))
            out[wgt].append(q)
        s += (adv + track) * hgt
    return out


def _strokes_svg(st, scale_ok=True):
    o = []
    for wgt, pls in st.items():
        if pls:
            o.append(f'<path d="{"".join(_d(p, tol=0) for p in pls)}" stroke="#000" stroke-width="{_n(wgt)}" fill="none"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# hourglass finial and the year tablet
# ------------------------------------------------------------------------------------------------

def _hourglass(cx, base, hgt, frac):
    """A turned hourglass standing on base, hgt tall; sand fallen in proportion to the year gone."""
    cv = C.Canvas()
    w = hgt * .5
    cap = hgt * .1
    # glass bulbs
    n = 24
    right = []
    for i in range(n + 1):
        t = i / n
        y = base - cap - (hgt - 2 * cap) * t
        u = abs(t - .5) * 2
        right.append((cx + w * .42 * (.12 + .88 * math.sin(u * PI / 2) ** .7), y))
    glass = right + [(2 * cx - p[0], p[1]) for p in right[::-1]]
    # posts behind
    for side in (-1, 1):
        px = cx + side * w * .46
        post = [(px - 1.2, base - cap), (px + 1.2, base - cap), (px + 1.2, base - hgt + cap), (px - 1.2, base - hgt + cap)]
        cv.obj([post], .5)
        cv.hair(C.hatch_poly(post, 90, 1.5))
    cv.obj([glass], 1.)
    cv.hair(C.hatch_poly(glass, 90, 3))
    cv.hair(C.hatch_poly([p for p in glass if p[0] > cx + w * .12] or glass, 90, 3, 1.5))
    # sand: lower bulb filled by frac, upper by 1-frac
    mid = base - hgt / 2
    lo = [p for p in glass if p[1] > mid]
    lo_h = (hgt / 2 - cap) * (.25 + .7 * frac)
    sand_lo = [p for p in lo if p[1] > base - cap - lo_h]
    if len(sand_lo) > 2:
        sand_lo = [(cx - w * .1, base - cap - lo_h - 2)] + sand_lo + [(cx + w * .1, base - cap - lo_h - 2)]
        cv.hair(C.hatch_poly(sand_lo, 45, 1.5))
        cv.hair(C.hatch_poly(sand_lo, -45, 3))
    up = [p for p in glass if p[1] < mid]
    up_h = (hgt / 2 - cap) * (.7 * (1 - frac))
    sand_up = [p for p in up if p[1] > mid - up_h - 1]
    if len(sand_up) > 2:
        cv.hair(C.hatch_poly(sand_up, 45, 1.5))
    cv.line([(cx, mid), (cx, base - cap - lo_h)])
    # caps
    for yc, sgn in ((base - cap / 2, 1), (base - hgt + cap / 2, -1)):
        capr = [(cx - w * .58, yc - cap / 2), (cx + w * .58, yc - cap / 2), (cx + w * .58, yc + cap / 2), (cx - w * .58, yc + cap / 2)]
        cv.obj([capr], 1.)
        cv.hair(C.hatch_poly(capr, 0, 1.5, .25))
    return cv.svg()


def _year_tablet(tx, ty, tw, th, day):
    """The pedestal's tablet as the year: dark cut for the days behind, ruled light ahead,
    month ticks, today's mark, a little sun at the winter solstice."""
    y0 = datetime.date(day.year, 1, 1)
    ylen = (datetime.date(day.year + 1, 1, 1) - y0).days
    f = ((day - y0).days + 1) / ylen
    o = []
    x = tx + 2
    W = tw - 4
    gone = f'M{_n(x)},{_n(ty + 2)}h{_n(W * f)}v{_n(th - 4)}h{_n(-W * f)}z'
    ahead = f'M{_n(x + W * f)},{_n(ty + 2)}h{_n(W * (1 - f))}v{_n(th - 4)}h{_n(-W * (1 - f))}z'
    o.append(f'<path d="{ahead}" fill="{C.pat("L")}" stroke="none"/>')
    o.append(f'<path d="{gone}" fill="{C.pat("X")}" stroke="none"/>')
    o.append(f'<path d="{gone}" fill="{C.pat("D")}" stroke="none"/>')
    ticks = []
    for m in range(1, 13):
        tf = (datetime.date(day.year, m, 1) - y0).days / ylen
        xx = round((x + W * tf) * 2) / 2
        ticks.append(f"M{_n(xx)},{_n(ty + 1)}v{_n(th - 2)}")
    o.append(f'<path d="{"".join(ticks)}" stroke="#000" stroke-width="1"{CR}/>')
    # today: a pointer
    tx_ = x + W * f
    o.append(f'<path d="M{_n(tx_ - 2.5)},{_n(ty)}h5l-2.5,{_n(th * .45)}zM{_n(tx_ - 2.5)},{_n(ty + th)}h5l-2.5,{_n(-th * .45)}z" fill="#000" stroke="none"/>')
    # winter solstice: a small sun
    sf = (datetime.date(day.year, 12, 21) - y0).days / ylen
    sx, sy = x + W * sf, ty + th / 2
    r = max(1.5, th * .18)
    rays = "".join(f"M{_n(sx + r * 1.4 * math.cos(a))},{_n(sy + r * 1.4 * math.sin(a))}L{_n(sx + r * 2.3 * math.cos(a))},{_n(sy + r * 2.3 * math.sin(a))}"
                   for a in [i * PI / 4 for i in range(8)])
    o.append(f'<path d="{_d(_ell(sx, sy, r * 1.1, r * 1.1, 14), True, 0)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{rays}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_d(_ell(sx, sy, r * .45, r * .45, 8), True, 0)}" fill="#000"/>')
    return "".join(o), f


# ------------------------------------------------------------------------------------------------
# layouts (house frame, re-cut so the vignette fills the whole field and nothing is left white)
# ------------------------------------------------------------------------------------------------

def _field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return C._superellipse(cx, cy, a + .5, b + .5)


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.1, 150)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _ell(cx, cy, rx - 2.2, ry - 2.2, 64)[:-1]
    o.append(vignette(field, ctx, "band", C._uid("vb", w, h)))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx):
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .07), rmax=r * .8,
                   max_n=11, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(vignette(_field(cx, cy, cw, gh + 4), ctx, "medium", C._uid("vm", w, h)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
    F = _facts(ctx)
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .07, 30.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="{C.pat("D")}" stroke="none"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((0, 0, w, py0 - 3.5), "L"))
    o.append(f'<path d="M0,{_n(py0 - 3.5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw = pw * (.52 if ph < 300 else .5)
    ch = ph * (.74 if ph < 300 else .64)
    cx, cy = w / 2, py0 + ph * .47
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(11, ph * .04), rmax=r1 * .9,
                   max_n=10, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(vignette(_field(cx, cy, cw, ch), ctx, "tall", C._uid("vt", w, h)))
    # crest: a palmette with the hourglass of the year standing in it
    pal = min(ch * .2 + top_free, 62)
    o.append(C.palmette(cx, cy - ch / 2 + 7, pal, True, rng.randrange(1 << 20)))
    y0 = datetime.date(F["day"].year, 1, 1)
    frac = ((F["day"] - y0).days + 1) / ((datetime.date(F["day"].year + 1, 1, 1) - y0).days)
    hg = min(pal * .9, cy - ch / 2 + 4)
    o.append(_hourglass(cx, cy - ch / 2 + 4, hg, frac))
    # the ribbon with today's date in Roman capitals
    bh = max(11., min(16, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    d = F["day"]
    txt = f"{_roman(d.month)} . {_roman(d.day)} . {_roman(d.year)}"
    o.append(_strokes_svg(_letter_along(centre, txt, bh * .52)))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py + 3, w, ped_h - 3), "M"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    tab, _ = _year_tablet(tx, ty, tw, th, F["day"])
    o.append(tab)
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
