"""doodles-03 "The rain jar": Parker's rain gauge on Sauvie Island in a November squall.

Tall: a carved cartouche held by mirrored acanthus volutes; inside, storm clouds over Mt. Hood
and the cottonwood line, slanting rain, a glass gauge on a grained post holding 1.31 in (a black
pointer marks the 2.1 in Portland usually has by now), a heron in the flooded slough and, in the
mud by the post, the dog's paw prints (the Easter egg). The crest carries a raindrop finial, the
ribbon carries the five recent rainy days as five drops sized by their totals, and the pedestal
tablet is a month gauge filled to 1.31 of the usual 5.6 in.
Medium: the same scene in the cartouche between volutes. Short: a frieze round a medallion
holding the gauge in the rain."""
import sys
import math
import random
import re
import engraving_codex as C

_n = C._n
_d = C._d
PI = math.pi

# ----------------------------------------------------------------------------------------------
# data from the page (falls back to today's measured numbers)
# ----------------------------------------------------------------------------------------------


def _data(ctx):
    s = (ctx or {}).get("sample", "") or ""
    got, usual_now, usual_month = 1.31, 2.1, 5.6
    m = re.search(r"([\d.]+)\s*in in the jar", s)
    if m:
        got = float(m.group(1))
    m = re.search(r"behind the ([\d.]+) in|ahead of the ([\d.]+) in", s)
    if m:
        usual_now = float(m.group(1) or m.group(2))
    m = re.search(r"usual for \w+ ([\d.]+)", s)
    if m:
        usual_month = float(m.group(1))
    days = [float(x) for x in re.findall(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([\d.]+)", s)] or [.02, .04, .14, .48, .39]
    return got, usual_now, max(usual_month, got, usual_now), days[-6:]


# ----------------------------------------------------------------------------------------------
# small shapes
# ----------------------------------------------------------------------------------------------


def _ell(cx, cy, rx, ry, n=32, rot=0.):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        t = 2 * PI * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def _closed(p):
    return p + [p[0]]


def _drop(cx, cy, r, n=36):
    """A raindrop, tip up, about 2.9 r tall."""
    pts = []
    for i in range(n):
        t = 2 * PI * i / n
        pts.append((cx + 1.25 * r * math.sin(t) * math.sin(t / 2), cy - 1.45 * r * math.cos(t) + .35 * r))
    return pts


def _keep(lines, f):
    return [l for l in lines if f(((l[0][0] + l[-1][0]) / 2, (l[0][1] + l[-1][1]) / 2))]


def _drop_obj(cv, cx, cy, r):
    p = _drop(cx, cy, r)
    cv.obj([p], 1. if r > 2.2 else .5)
    if r > 1.6:
        cv.hair(_keep(C.hatch_poly(p, 70, 1.5), lambda m: m[0] > cx - r * .15 or m[1] > cy + r * .7))
    if r > 5:
        for k in (.72, .5):
            q = _drop(cx + r * (1 - k) * .45, cy + r * (1 - k) * .5, r * k)
            cv.hair([q[4:30]])
    return p


def _hline(poly, y):
    return C.hatch_poly(poly, 0, 1e6, y)


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------


def _cloud(cx, cy, w, h, rng):
    """Billowed top, flat-ish bottom: outline polygon and a top-envelope function."""
    k = max(4, int(w / (h * .6)))
    circles = []
    for i in range(k):
        t = (i + .5) / k
        r = h * (.3 + .45 * math.sin(PI * t) ** .8) * rng.uniform(.8, 1.12)
        circles.append((cx - w / 2 + w * t + rng.uniform(-2, 2), cy + h * .5 - r * .9, r))
    base = cy + h * .5

    def top(x):
        ys = [c[1] - math.sqrt(max(0., c[2] ** 2 - (x - c[0]) ** 2)) for c in circles if abs(x - c[0]) < c[2]]
        return min(min(ys), base - 1) if ys else None
    xs = [x for x in [cx - w / 2 - h + i * .5 for i in range(int((w + 2 * h) * 2))] if top(x) is not None]
    tp = [(x, top(x)) for x in xs]
    bt = [(x, base + .6 * math.sin(x * .3)) for x in xs[::-1]]
    return C._dp(tp, .15) + C._dp(bt, .15), circles, top


def _shade_cloud(cv, poly, circles, top, cy, h):
    """Lit rim under each billow's top, ruled tone below it, dense at the base; billow contours."""
    base = cy + h * .5
    xs0 = min(p[0] for p in poly)
    xs1 = max(p[0] for p in poly)
    lines = []
    y = base - 1.
    while y > base - h * 1.2:
        f = (base - y) / h
        rim = 3.5 + 3 * f
        seg = []
        x = xs0
        while x <= xs1:
            t = top(x)
            ok = t is not None and y > t + rim
            if ok:
                seg.append((x, y))
            elif len(seg) > 1:
                lines.append([seg[0], seg[-1]]); seg = []
            else:
                seg = []
            x += .5
        if len(seg) > 1:
            lines.append([seg[0], seg[-1]])
        y -= 1.5 if f < .3 else (2. if f < .6 else 3.)
    cv.hair(lines)
    arcs = []
    for c in circles:
        for k in (.8,):
            arcs.append([(c[0] + c[2] * k * math.cos(a), c[1] + c[2] * k * math.sin(a))
                         for a in [PI * (1.05 + .55 * i / 12) for i in range(13)]])
    cv.hair(arcs)


def _scene(ctx, field, bx, by, bw, bh, seed, detail=1.):
    """Engrave the whole field with the rain-jar scene. Returns (canvas svg, black-fill path data)."""
    got, usual_now, usual_month, days = _data(ctx)
    rng = random.Random(seed)
    cv = C.Canvas()
    blacks = []
    s = bh / 160.
    big = bh > 60
    hy = by + bh * (.6 if big else .66)      # horizon
    x0, x1 = bx - 2, bx + bw + 2

    # ---- sky: ruled, dense at the top, with slanting rain
    sky = [(x0, by - 2), (x1, by - 2), (x1, hy), (x0, hy)]
    cv.obj([sky], 0)
    y = hy - 1
    lines = []
    while y > by - 2:
        f = (hy - y) / max(1., hy - by)
        lines.append([(x0, y), (x1, y)])
        y -= 3. if f < .45 else (2. if f < .8 else 1.5)
    cv.hair(lines)
    rain = []
    n_rain = int(bw * (hy - by) / 70 * detail)
    ang = math.radians(104)
    for i in range(n_rain):
        px = rng.uniform(x0, x1 + 20)
        py = rng.uniform(by, hy + bh * .12)
        L = rng.uniform(5, 11) * max(.6, s)
        rain.append([(px, py), (px + L * math.cos(ang), py + L * math.sin(ang))])
    clouds = []
    if big:
        specs = [(bx + bw * .3, by + bh * .22, bw * .34, bh * .12), (bx + bw * .7, by + bh * .17, bw * .32, bh * .11),
                 (bx + bw * .62, by + bh * .36, bw * .36, bh * .1)]
    else:
        specs = [(bx + bw * .5, by + bh * .14, bw * .9, bh * .2)]
    for (ccx, ccy, cw, ch) in specs:
        poly, circ, top = _cloud(ccx, ccy, cw, ch, rng)
        clouds.append((poly, circ, top, ccy, ch))
    cv.hair(rain)
    for poly, circ, top, ccy, ch in clouds:
        cv.obj([poly], 1.)
        _shade_cloud(cv, poly, circ, top, ccy, ch)
        cv.hair(_keep(rain, lambda m, cy=ccy, h=ch: m[1] > cy + h * .5))

    # ---- Mt. Hood on the horizon, behind the cottonwoods
    if big:
        mx, mh, mw = bx + bw * .2, bh * .2, bw * .3
        mt = [(mx - mw / 2, hy), (mx - mw * .12, hy - mh * .78), (mx - mw * .03, hy - mh), (mx + mw * .06, hy - mh * .9),
              (mx + mw * .16, hy - mh * .7), (mx + mw / 2, hy)]
        cv.obj([mt], .5)
        shadow = [(mx - mw * .03, hy - mh), (mx + mw * .06, hy - mh * .9), (mx + mw * .16, hy - mh * .7), (mx + mw / 2, hy),
                  (mx + mw * .02, hy), (mx + mw * .01, hy - mh * .5)]
        cv.hair(C.hatch_poly(shadow, 65, 1.5))
        lower = [(mx - mw / 2, hy), (mx - mw * .3, hy - mh * .45), (mx - mw * .2, hy - mh * .36), (mx - mw * .1, hy - mh * .48),
                 (mx + mw * .05, hy - mh * .4), (mx + mw * .2, hy - mh * .5), (mx + mw / 2, hy)]
        cv.hair(C.hatch_poly(lower, 0, 2))
        for k in range(4):
            gx_ = mx - mw * .08 + k * mw * .05
            cv.hair([[(gx_, hy - mh * (.82 - k * .04)), (gx_ - mw * .03 + k * mw * .02, hy - mh * .52)]])

    # ---- cottonwood line along the horizon
    tl = []
    x = x0
    while x <= x1:
        tl.append((x, hy - bh * .03 - abs(math.sin(x * .19)) * bh * .035 - abs(math.sin(x * .053)) * bh * .03))
        x += 2
    trees = tl + [(x1, hy + 1), (x0, hy + 1)]
    cv.obj([trees], .5)
    cv.hair(C.hatch_poly(trees, 90, 1.5))
    cv.line([[(x0, hy + 1), (x1, hy + 1)]])

    # ---- flat fields, then the flooded slough
    wy = hy + bh * .1
    fields = [(x0, hy + 1), (x1, hy + 1), (x1, wy), (x0, wy)]
    cv.obj([fields], 0)
    fl, y, p = [], hy + 2.5, 1.5
    while y < wy:
        fl.append([(x0, y), (x1, y)])
        y += p
        p = min(3., p + .3)
    cv.hair(fl)
    water = [(x0, wy), (x1, wy), (x1, by + bh + 2), (x0, by + bh + 2)]
    cv.obj([water], .5)
    wl, y = [], wy + 1.5
    while y < by + bh + 2:
        f = (y - wy) / max(1., bh * .4)
        dash = 6 + 26 * f
        xx = x0 + rng.uniform(-dash, 0)
        while xx < x1:
            wl.append([(xx, y), (xx + dash, y)])
            xx += dash + rng.uniform(1.5, 3 + 4 * f)
        y += 1.5 if f < .3 else 2.
    cv.hair(wl)
    cv.hair(_keep(rain, lambda m: m[1] < wy + bh * .1))

    # ---- rain rings on the water
    for i in range(int(7 * detail) if big else 2):
        rx_ = rng.uniform(bx + bw * .05, bx + bw * .95)
        ry_ = rng.uniform(wy + 4, by + bh - 6)
        rr = (2.5 + 5 * (ry_ - wy) / max(1, bh * .4)) * max(.7, s)
        cv.obj([_ell(rx_, ry_, rr, rr * .3, 24)], .5)
        cv.hair([_closed(_ell(rx_, ry_, rr * .55, rr * .17, 16))])
        cv.hair([[(rx_ - rr * 1.5, ry_ + rr * .45), (rx_ + rr * 1.5, ry_ + rr * .45)]])

    # ---- the heron, in the slough, looking at the gauge
    if bh > 100 and bw > 140:
        _heron(cv, bx + bw * .77, wy + bh * .16, s, blacks)

    # ---- mud bank with the dog's paw prints (the Easter egg)
    gx = bx + bw * (.4 if big else .5)
    if big:
        lip = [(bx + bw * t / 20 * .64, by + bh * (.82 - .07 * math.sin(PI * t / 20) - .02 * math.sin(t * 1.3) + .12 * (t / 20) ** 3)) for t in range(21)]
        bank = [(x0, by + bh * .82)] + lip + [(bx + bw * .66, by + bh + 2), (x0, by + bh + 2)]
        cv.obj([bank], 1.)
        cv.hair(C.hatch_poly(bank, 20, 2))
        cv.hair(C.hatch_poly(bank, -25, 3, .7))
        for t in range(3, 19, 2):
            px, py = lip[t]
            for k in (-1, 0, 1):
                cv.hair([[(px + k * 1.2, py + .5), (px + k * 2.6 + rng.uniform(-1, 1), py - (3 + rng.uniform(0, 3)) * max(.7, s))]])
        for i in range(4):
            ppx = bx + bw * (.08 + .07 * i)
            ppy = by + bh * (.93 - .025 * i) + (2.5 if i % 2 else -2.5) * s
            pr = 1.9 * max(.8, s)
            blacks.append(_d(_ell(ppx, ppy, pr, pr * .85, 12), True, 0))
            for k in range(4):
                a = -PI / 2 + (k - 1.5) * .55 + .45
                blacks.append(_d(_ell(ppx + pr * 1.9 * math.cos(a), ppy + pr * 1.9 * math.sin(a), pr * .45, pr * .45, 8), True, 0))

    # ---- the gauge on its post
    _gauge(cv, gx, by, bh, hy, got, usual_now, s, blacks, short=not big)
    return cv.svg(), "".join(blacks)


def _heron(cv, hx, hy, s, blacks):
    """Great blue heron, facing left toward the gauge, feet at (hx, hy)."""
    k = 11 * s
    cv.obj([], 0)
    cv.line([[(hx - .3 * k, hy), (hx - .2 * k, hy - 2.4 * k)], [(hx + .35 * k, hy - .15 * k), (hx + .25 * k, hy - 2.4 * k)]])
    cv.hair([[(hx - .3 * k, hy + 1.5), (hx - .3 * k, hy + 1.1 * k)], [(hx + .35 * k, hy + 1.5), (hx + .35 * k, hy + 1. * k)]])
    bcx, bcy = hx + .15 * k, hy - 2.95 * k
    rot = math.radians(22)
    body = _ell(bcx, bcy, 1.5 * k, .72 * k, 40, rot)
    tail = [(bcx + 1. * k, bcy + .2 * k), (bcx + 2.1 * k, bcy + 1.05 * k), (bcx + 1.6 * k, bcy + .5 * k), (bcx + 1.25 * k, bcy + .6 * k)]
    cv.obj([tail], .5)
    cv.hair(C.hatch_poly(tail, 35, 1.5))
    # neck: S curve from the chest up to the head
    fx, fy = bcx - 1.25 * k, bcy - .45 * k
    neck = []
    for i in range(21):
        t = i / 20
        neck.append((fx - .2 * k * t + .55 * k * math.sin(t * PI * 2) * (1 - .4 * t), fy - 2.6 * k * t))
    wdt = [(.42 - .2 * i / 20) * k for i in range(21)]
    R = C._Rib(neck, wdt, wdt)
    cv.obj([R.outline()], 1.)
    for sv in (-.55, -.2):
        cv.hair(R.contour(sv, .04, .96))
    cv.hair(R.contour(.5, .3, .9))
    cv.obj([body], 1.)
    c, sn = math.cos(rot), math.sin(rot)

    def lower(m):
        dx, dy = m[0] - bcx, m[1] - bcy
        return -dx * sn + dy * c > -.1 * k
    cv.hair(C.hatch_poly(body, 22, 3))
    cv.hair(_keep(C.hatch_poly(body, 22, 3, 1.5), lower))
    for j in range(5):
        u = -.35 + j * .17
        p0 = (bcx - 1.1 * k * c - u * k * -sn, bcy - 1.1 * k * sn + u * k * c)
        cv.hair([[p0, (p0[0] + 1.3 * k * c, p0[1] + 1.3 * k * sn + .12 * k), (p0[0] + 2.4 * k * c, p0[1] + 2.4 * k * sn + .45 * k)]])
    hx2, hy2 = neck[-1]
    cv.obj([_ell(hx2 - .05 * k, hy2 - .05 * k, .45 * k, .34 * k, 20)], 1.)
    beak = [(hx2 - .35 * k, hy2 - .16 * k), (hx2 - 1.8 * k, hy2 + .12 * k), (hx2 - .35 * k, hy2 + .14 * k)]
    cv.obj([beak], 1.)
    cv.hair(C.hatch_poly(beak, 0, 1.5))
    blacks.append(_d([(hx2 - .3 * k, hy2 - .3 * k), (hx2 + .4 * k, hy2 - .42 * k), (hx2 + 1.3 * k, hy2 - .3 * k),
                      (hx2 + .35 * k, hy2 - .18 * k)], True, 0))
    blacks.append(_d(_ell(hx2 - .12 * k, hy2 - .06 * k, .09 * k, .09 * k, 8), True, 0))


def _gauge(cv, gx, by, bh, hy, got, usual_now, s, blacks, short=False):
    top_y = by + bh * (.16 if not short else .1)
    gw = max(9., 16 * s)
    glass_top = top_y + gw * .9
    glass_bot = by + bh * (.74 if not short else .9)
    pw = gw * .9
    post_x = gx + gw * .5 + pw * .55
    post = [(post_x - pw / 2, glass_top + gw * .4), (post_x + pw / 2, glass_top + gw * .2),
            (post_x + pw / 2, by + bh + 3), (post_x - pw / 2, by + bh + 3)]
    cv.obj([post], 1.)
    grain = []
    for i in range(1, 5):
        x = post_x - pw / 2 + pw * i / 5
        grain.append([(x + .6 * math.sin(y * .21 + i) + (1.2 * math.exp(-((y - glass_bot) / 6) ** 2) if i == 2 else 0), y)
                      for y in [glass_top + gw * .4 + j * 2 for j in range(int((by + bh - glass_top) / 2))]])
    cv.hair(grain)
    cv.hair(C.hatch_poly([(post_x + pw * .15, glass_top), (post_x + pw / 2, glass_top), (post_x + pw / 2, by + bh + 3),
                          (post_x + pw * .15, by + bh + 3)], 90, 1.5))
    knot_y = glass_bot + (by + bh - glass_bot) * .4
    cv.hair([_closed(_ell(post_x - pw * .1, knot_y, pw * .14, pw * .35, 14))])
    for yy in (glass_top + (glass_bot - glass_top) * .25, glass_bot - (glass_bot - glass_top) * .2):
        br = [(gx - gw * .55, yy - 1.6), (post_x + pw * .3, yy - 1.6), (post_x + pw * .3, yy + 1.6), (gx - gw * .55, yy + 1.6)]
        cv.obj([br], 1.)
        cv.hair([[(gx - gw * .55, yy), (post_x + pw * .3, yy)]])
    gl = gx - gw / 2
    gb = glass_bot - gw * .15
    cyl = [(gl, glass_top), (gl + gw, glass_top), (gl + gw, gb)] + \
          [(gx + gw / 2 * math.cos(a), gb + gw * .2 * math.sin(a)) for a in [PI * i / 10 for i in range(11)]] + [(gl, gb)]
    cv.obj([cyl], 1.)
    scale_top = glass_top + gw * .35
    span = gb - scale_top
    full = 3.
    wl = gb - span * min(got, full) / full
    water = [(gl + .5, wl), (gl + gw - .5, wl), (gl + gw - .5, glass_bot - gw * .1), (gl + .5, glass_bot - gw * .1)]
    cv.hair(C.hatch_poly(water, 0, 1.5))
    cv.hair(_keep(C.hatch_poly(water, 90, 1.5), lambda m: m[0] > gl + gw * .62))
    cv.line([[(gx + gw * .5 * math.cos(a), wl + gw * .12 * math.sin(a)) for a in [PI - PI * i / 8 for i in range(9)]]])
    cv.hair([[(gl + gw * x, glass_top + 1), (gl + gw * x, wl - 1.5)] for x in (.7, .8, .88)])
    cv.hair([[(gl + gw * .14, glass_top + 2), (gl + gw * .14, glass_bot - gw * .3)]])
    ticks = []
    for i in range(int(full * 10) + 1):
        if short and i % 5:
            continue
        y = gb - span * i / (full * 10)
        L = gw * (.42 if i % 10 == 0 else .28 if i % 5 == 0 else .16)
        ticks.append([(gl + gw * .22, y), (gl + gw * .22 + L, y)])
    cv.hair(ticks)
    fun = [(gl - gw * .35, top_y), (gl + gw * 1.35, top_y), (gl + gw, glass_top), (gl, glass_top)]
    cv.obj([fun], 1.)
    cv.hair(_keep(C.hatch_poly(fun, 75, 1.5), lambda m: m[0] > gx))
    cv.hair(_keep(C.hatch_poly(fun, 105, 3), lambda m: m[0] <= gx))
    cv.obj([_ell(gx, top_y, gw * .85 + 1, 2.4, 24)], 1.)
    blacks.append(_d(_ell(gx, top_y + .2, gw * .78, 1.3, 20), True, 0))
    uy = gb - span * min(usual_now, full) / full
    blacks.append(_d([(gl + gw + 1, uy), (gl + gw + 1 + gw * .45, uy - gw * .28), (gl + gw + 1 + gw * .45, uy + gw * .28)], True, 0))
    cv.obj([], 0)
    cv.line([[(gl + gw * .4, uy), (gl + gw - .5, uy)]])
    if not short:
        for dx, dy in ((-.2, -1.6), (.5, -2.6), (.15, -3.7)):
            _drop_obj(cv, gx + dx * gw, top_y + dy * gw * .9, max(1.4, gw * .1))


# ----------------------------------------------------------------------------------------------
# layouts (copied from the house library so the cartouche field, banner and tablet are engraved)
# ----------------------------------------------------------------------------------------------


def _clipd(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _art(art, blk):
    return art + (f'<path d="{blk}" fill="#000" stroke="none"/>' if blk else "")


def _field_art(ctx, cx, cy, cw, ch, seed, uid):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    field = C._superellipse(cx, cy, a + .5, b + .5)
    art, blk = _scene(ctx, field, cx - a, cy - b, 2 * a, 2 * b, seed)
    return _clipd(uid, _d(field, True, 0), _art(art, blk))


def _banner_face(centre, h, days):
    """Rule the ribbon face and set one drop per recent rainy day, sized by its total."""
    cv = C.Canvas()
    n = len(centre)
    R = C._Rib(centre, [h / 2] * n, [h / 2] * n)
    face = [R.at(i / 40, .62) for i in range(41)] + [R.at(1 - i / 40, -.62) for i in range(41)]
    cv.obj([face], 0)
    cv.hair([l for sv in (.48, .32, .16, 0., -.16, -.32, -.48) for l in R.contour(sv, .02, .98)])
    m = max(days) or 1
    k = len(days)
    for i, v in enumerate(days):
        u = .5 + (i - (k - 1) / 2) * .13
        px, py = R.at(u, 0)
        r = h * (.1 + .18 * math.sqrt(v / m))
        cv.obj([C._ell_pts(px, py, h * .42, h * .42, 24)], .5)
        _drop_obj(cv, px, py - r * .15, r)
    for i in range(k + 1):
        u = .5 + (i - k / 2) * .13
        if .02 < u < .98:
            px, py = R.at(u, 0)
            cv.obj([[(px - 2, py), (px, py - 1.6), (px + 2, py), (px, py + 1.6)]], .5)
    return cv.svg()


def _tablet(tx, ty, tw, th, got, usual_now, usual_month):
    """The month gauge across the pedestal tablet: a tube filled to today's total, tenth-inch
    ticks, a black pointer at what Portland usually has by now."""
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{C.pat("L")}" stroke="none"/>']
    x0, x1 = tx + 12, tx + tw - 12
    tcy = ty + th * .62
    tr = max(2.5, th * .2)
    full = usual_month
    xg = x0 + (x1 - x0) * got / full
    xu = x0 + (x1 - x0) * usual_now / full
    tube = f"M{_n(x0)},{_n(tcy - tr)}H{_n(x1)}a{_n(tr)},{_n(tr)} 0 0,1 0,{_n(2 * tr)}H{_n(x0)}a{_n(tr)},{_n(tr)} 0 0,1 0,{_n(-2 * tr)}z"
    o.append(f'<path d="{tube}" fill="{C.pat("L")}" stroke="#000" stroke-width="1"/>')
    fill = f"M{_n(x0)},{_n(tcy - tr + 1)}H{_n(xg)}V{_n(tcy + tr - 1)}H{_n(x0)}a{_n(tr - 1)},{_n(tr - 1)} 0 0,1 0,{_n(-2 * tr + 2)}z"
    o.append(f'<path d="{fill}" fill="{C.pat("X")}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{_n(x0)},{_n(tcy - tr * .45)}H{_n(x1)}" stroke="#000" stroke-width=".5"/>')
    tk = []
    i = 0
    while i <= full * 10 + 1e-6:
        x = x0 + (x1 - x0) * i / (full * 10)
        L = tr * (1.6 if i % 10 == 0 else 1.1 if i % 5 == 0 else .6)
        tk.append(f"M{_n(x)},{_n(tcy - tr - 1.2)}v{_n(-L)}")
        i += 1
    o.append(f'<path d="{"".join(tk)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{_n(xu)},{_n(tcy - tr - 1)}l{_n(-tr * .7)},{_n(-tr * 1.5)}h{_n(tr * 1.4)}z" fill="#000"/>')
    cv = C.Canvas()
    _drop_obj(cv, xg, tcy - tr * .2, tr * 1.05)
    o.append(cv.svg())
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    got, usual_now, usual_month, days = _data(ctx)
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
    cw, ch = pw * .52, ph * .66
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
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_art(ctx, cx, cy, cw, ch, seed, C._uid("v", w, h, seed)))
    psz = min(ch * .2 + top_free, 62)
    pcy = cy - ch / 2 + 7
    o.append(C.palmette(cx, pcy, psz, True, rng.randrange(1 << 20)))
    dcv = C.Canvas()
    _drop_obj(dcv, cx, pcy - psz * .48, psz * .12)
    o.append(dcv.svg())
    bh_ = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_face(centre, bh_, days))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, got, usual_now, usual_month))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        dcv = C.Canvas()
        _drop_obj(dcv, w / 2, fy + fh * .55, fh * .09)
        o.append(dcv.svg())
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
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
                   max_n=9, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_art(ctx, cx, cy, cw, gh + 4, seed, C._uid("mv", w, h, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


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
    fx, fy = rx - 2.5, ry - 2.5
    field = C._ell_pts(cx, cy, fx, fy, 64)
    art, blk = _scene(ctx, field, cx - fx, cy - fy, 2 * fx, 2 * fy, seed, .8)
    o.append(_clipd(C._uid("bv", w, h, seed), _d(field, True, 0), _art(art, blk)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
