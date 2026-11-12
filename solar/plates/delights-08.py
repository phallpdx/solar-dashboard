"""delights-08 "Books picked for you": today's pick is Dan Simmons' THE TERROR.
The cartouche holds HMS Terror locked in Arctic pack ice under the aurora (moon phase from the
date); the ribbon is lettered THE TERROR in drawn strokes; the pedestal's tablet is a carved
bookshelf of spines. Easter egg: Parker's dog, curled asleep on the nearest floe (the real
Terror/Erebus expedition sailed with a dog, Neptune)."""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d = C._n, C._d
TAU = math.tau


# ------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------

def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _half(poly, nx, ny, c):
    """Clip a polygon to the half-plane nx*x + ny*y <= c (Sutherland-Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = nx * p[0] + ny * p[1] - c, nx * q[0] + ny * q[1] - c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def _rot(poly, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in poly]


def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .5 - 18.2 / 24
    return (days / 29.530588) % 1.


# ------------------------------------------------------------------------------------------
# the scene: HMS Terror beset in the pack, aurora overhead
# ------------------------------------------------------------------------------------------

def _shaded_block(cv, poly, light_ang, rng, pitch_lit=3., outline=.5):
    """An ice block: white, lit half lightly ruled, shadow half densely hatched."""
    cv.obj([poly], outline)
    cx, cy = _centroid(poly)
    a = light_ang + rng.uniform(-.3, .3)
    nx, ny = math.cos(a), math.sin(a)
    c = nx * cx + ny * cy + rng.uniform(-1, 1)
    lit = _half(poly, -nx, -ny, -c)
    dark = _half(poly, nx, ny, c)
    if len(lit) > 2:
        cv.hair(C.hatch_poly(lit, 0, pitch_lit, .5))
    if len(dark) > 2:
        cv.obj([dark], 0)
        cv.hair(C.hatch_poly(dark, 62, 1.5, .3))
        cv.hair(C.hatch_poly(dark, 0, 3, 1.))


def _berg(cv, x0, x1, base, top, rng):
    n = max(4, int((x1 - x0) / 5))
    ip = rng.randint(1, n - 2)
    prof = []
    for i in range(n + 1):
        t = i / n
        hump = 1 - abs(i - ip) / max(ip, n - ip)
        y = base - (base - top) * (.25 + .75 * hump ** .7) * rng.uniform(.85, 1.)
        prof.append((x0 + (x1 - x0) * t, y))
    prof[0] = (x0, base)
    prof[-1] = (x1, base)
    poly = prof + [(x1, base + 1), (x0, base + 1)]
    cv.obj([poly], .5)
    cv.hair([[(x, base - 1.5), (x, y + 2)] for x, y in prof[1:-1] if x < prof[ip][0] and base - y > 5][::2])
    px, py = prof[ip]
    shadow = [(px, py)] + prof[ip + 1:] + [(x1, base + 1), (px + (x1 - px) * .25, base + 1)]
    cv.obj([shadow], 0)
    cv.hair(C.hatch_poly(shadow, 0, 1.5, .25))
    cv.hair(C.hatch_poly(shadow, 70, 2, .5))


def _ship(cv, sx, wl, L, top_lim, rng, detail=1.):
    hh = L * .17
    x0, x1 = sx - L / 2, sx + L / 2

    def sheer(t):
        return wl - hh * (1.08 - .16 * math.sin(math.pi * t) + .1 * t)

    deck = [(x0 + L * t / 30, sheer(t / 30)) for t in range(31)]
    H = min(L * .95, wl - hh - top_lim)
    masts = [(.2, .93), (.5, 1.), (.78, .8)]
    # rigging (behind everything else on the ship)
    cv.obj([], 0)
    bs_tip = (x0 - L * .24, sheer(0) - L * .09)
    tops = []
    for t, f in masts:
        mx = x0 + L * t
        tops.append((mx, sheer(t) - H * f))
    cv.hair([bs_tip, (tops[0][0], tops[0][1] + H * .12)])
    cv.hair([(bs_tip[0] + L * .06, bs_tip[1] + 2), (tops[0][0], tops[0][1] + H * .38)])
    cv.hair([(x0 - L * .1, sheer(0) - L * .045), (tops[0][0], tops[0][1] + H * .58)])
    cv.hair([tops[0], (tops[1][0], tops[1][1] + H * .3)])
    cv.hair([tops[1], (tops[2][0], tops[2][1] + H * .25)])
    cv.hair([tops[2], (x1 + L * .02, sheer(1) - hh * .2)])
    for (t, f), (mx, my) in zip(masts, tops):
        dy = sheer(t)
        for k, side in enumerate((-1, 1)):
            for j in range(3 if detail > .6 else 1):
                sx0 = mx + side * (L * .025 + j * L * .02)
                cv.hair([(mx, dy - H * f * .55), (sx0 + side * L * .02, dy - .5)])
        if detail > .6:  # ratlines
            for j in range(4):
                yy = dy - H * f * (.12 + .1 * j)
                cv.hair([(mx - L * .03 * (1 - j * .2), yy), (mx + L * .03 * (1 - j * .2), yy)])
    # masts and yards
    cv.obj([], 0)
    for (t, f), (mx, my) in zip(masts, tops):
        dy = sheer(t)
        cv.heavy([(mx, dy), (mx, dy - H * f * .55)])
        cv.line([(mx, dy - H * f * .5), (mx, my)])
        for fy, fl in ((.36, .3), (.6, .23), (.82, .15)):
            yy = dy - H * f * fy
            hl = L * fl * f * .5
            cv.line([(mx - hl, yy + .6), (mx, yy), (mx + hl, yy + .6)])
        # topmast doubling: a little black cap
        cv.heavy([(mx - 1.5, dy - H * f * .55), (mx + 1.5, dy - H * f * .55)])
    # furled sails (white rolls under each yard)
    for (t, f), (mx, my) in zip(masts, tops):
        dy = sheer(t)
        for fy, fl in ((.36, .3), (.6, .23), (.82, .15)):
            yy = dy - H * f * fy
            hl = L * fl * f * .5 * .86
            rh = max(1.2, L * .012)
            roll = [(mx + hl * math.cos(a), yy + 1 + rh * .9 + rh * math.sin(a)) for a in [TAU * i / 18 for i in range(18)]]
            cv.obj([roll], .5)
            if detail > .6:
                for g in range(-2, 3):
                    gx = mx + hl * g / 3
                    cv.hair([(gx - .6, yy + 1), (gx + .6, yy + 1 + rh * 1.8)])
            cv.hair([(mx - hl * .9, yy + 1 + rh * 1.6), (mx + hl * .9, yy + 1 + rh * 1.6)])
    # ensign at the mizzen peak: a small dark flag lifting in the wind
    fx, fyy = tops[2]
    flag = [(fx, fyy), (fx + L * .07, fyy + L * .006), (fx + L * .065, fyy + L * .035), (fx, fyy + L * .04)]
    cv.obj([flag], .5)
    cv.hair(C.hatch_poly(flag, 0, 1.5, .2))
    cv.hair(C.hatch_poly(flag, 90, 1.5, .2))
    # bowsprit and jib-boom
    cv.obj([], 0)
    cv.heavy([(x0 + L * .04, sheer(0) - hh * .1), (x0 - L * .1, sheer(0) - L * .045)])
    cv.line([(x0 - L * .1, sheer(0) - L * .045), bs_tip])
    # hull
    hull = (deck + [(x1 + hh * .05, sheer(1) + hh * .2), (x1 - hh * .3, wl + hh * .45)] +
            [(x0 + hh * 1.0, wl + hh * .45), (x0 + hh * .35, wl + hh * .05), (x0 + hh * .05, wl - hh * .5)])
    hull = [(x0 - hh * .12, sheer(0) - hh * .08)] + hull
    cv.obj([hull], 1.)
    cv.hair(C.hatch_poly(hull, 0, 1.5, .1))
    cv.hair(C.hatch_poly(hull, 72, 1.5, .3))
    cv.hair(C.hatch_poly(hull, -60, 3, .3))
    # the white band (Terror's strake) with black ports
    up = [(x0 + L * t / 30 + hh * .25, sheer(t / 30) + hh * .3) for t in range(31)]
    lo = [(x + 0, y + max(1.6, hh * .2)) for x, y in up][::-1]
    band = [p for p in up if p[0] < x1 - hh * .2] + [p for p in lo if p[0] < x1 - hh * .2]
    cv.obj([band], .5)
    if detail > .4:
        np_ = max(4, int(L / 14))
        for i in range(np_):
            t = .12 + .76 * i / (np_ - 1)
            px = x0 + L * t
            py = sheer(t) + hh * .3 + max(1.6, hh * .2) / 2
            cv.heavy([(px - .4, py), (px + .4, py)])
    # bulwark rail and stern quarter windows
    cv.obj([], 0)
    cv.hair([(x, y + 1.2) for x, y in deck])
    for i in range(3):
        wx = x1 - hh * (.35 + .3 * i)
        cv.hair([(wx, sheer(1) + hh * .62), (wx, sheer(1) + hh * .85)])
    # ice rime along the rail: little white teeth cut into the dark planking
    if detail > .6:
        for i in range(int(L / 4)):
            t = (i + .5) / int(L / 4)
            px, py = x0 + L * t, sheer(t) + hh * .66
            cv.obj([[(px - .7, py), (px + .7, py), (px, py + rng.uniform(1.5, 3))]], 0)
    return hh


def _pack(cv, fx, fw, y0, y1, rng, hull_span=None, small=False):
    """Irregular floes from y0 to y1 in perspective: thin far rows, deep near rows, dark leads."""
    rows = []
    y = y0
    while y < y1 + 4:
        depth = 2.5 + (y - y0) * .2
        rows.append((y, depth))
        y += depth * rng.uniform(.9, 1.4)
    for y, depth in rows:
        x = fx - rng.uniform(4, 30)
        while x < fx + fw + 4:
            wdt = depth * rng.uniform(2.2, 8.)
            gap = depth * (rng.uniform(.2, .6) if rng.random() < .75 else rng.uniform(1., 2.2))
            face = depth * rng.uniform(.35, .6)
            yy = y + rng.uniform(-.3, .3) * depth
            n = 7
            top = []
            for i in range(n):
                a = math.pi + math.pi * i / (n - 1)
                top.append((x + wdt / 2 + wdt / 2 * math.cos(a) * rng.uniform(.85, 1.05),
                            yy + depth * .35 + depth * .35 * math.sin(a) * rng.uniform(.7, 1.1)))
            front = [(x + wdt / 2 + wdt / 2 * math.cos(a) * rng.uniform(.9, 1.), yy + depth * .35 + depth * .3 * math.sin(a))
                     for a in [math.pi * i / (n - 1) for i in range(n)]][::-1]
            front = front[::-1]
            front = [(x + wdt - 0., yy + depth * .35)] + [(px, py) for px, py in sorted(front, key=lambda p: -p[0])][1:-1] + [(x, yy + depth * .35)]
            top_poly = top + front[::-1][1:-1][::-1] if False else top + [p for p in front[1:-1]]
            body = top_poly + []
            low = [(px, py + face) for px, py in front]
            slab = top + low
            cv.obj([slab], .5)
            cv.hair(C.hatch_poly(top_poly, 0, 3, 1.25))
            fr = front + low[::-1]
            cv.obj([fr], 0)
            cv.hair(C.hatch_poly(fr, 0, 1.5, .25))
            if depth > 6:
                cv.hair(C.hatch_poly(fr, 75, 2, .5))
            if depth > 9 and rng.random() < .5:  # a crack across the floe
                cx = x + wdt * rng.uniform(.3, .7)
                cv.hair([(cx, yy + depth * .1), (cx + depth * .3, yy + depth * .35), (cx - depth * .1, yy + depth * .62)])
            x += wdt + gap
    return rows


def _pressure_ridge(cv, x0, x1, wl, hh, rng):
    x = x0
    while x < x1:
        s = hh * rng.uniform(.45, .95)
        cx, cy = x + s * .5, wl + hh * rng.uniform(.3, .7)
        poly = _rot([(cx - s * .55, cy - s * .35), (cx + s * .5, cy - s * .45), (cx + s * .6, cy + s * .4),
                     (cx - s * .5, cy + s * .45)], cx, cy, rng.uniform(-.7, .7))
        _shaded_block(cv, poly, math.pi * .15, rng)
        x += s * rng.uniform(.45, .75)


def _dog(cv, cx, cy, s):
    """Parker's dog, curled nose-to-tail asleep on the ice."""
    sh = C._ell_pts(cx + s * .8, cy + s * 3.3, s * 8, s * 1.5, 24)
    cv.obj([sh], 0)
    cv.hair(C.hatch_poly(sh, 0, 1.5, .1))
    cv.hair(C.hatch_poly(sh, 90, 1.5, .1))
    body = C._ell_pts(cx, cy, s * 6.4, s * 3.8, 40)
    cv.obj([body], 1.)
    # coat: fur strokes following the curl, a dark shaded underside
    for r in (.35, .55, .75, .92):
        arc = [(cx + s * 6.4 * r * math.cos(a), cy + s * 3.8 * r * math.sin(a))
               for a in [math.radians(v) for v in range(-40, 210, 10)]]
        cv.hair(arc)
    cv.hair(C.hatch_poly(_half(body, 0, -1, -(cy + s * .6)), 25, 1.5, .2))
    cv.hair(C.hatch_poly(_half(body, 0, -1, -(cy + s * 2.0)), -40, 1.5, .2))
    for i in range(14):  # fuzzy back
        a = math.radians(190 + i * 11)
        px, py = cx + s * 6.4 * math.cos(a), cy + s * 3.8 * math.sin(a)
        cv.hair([(px, py), (px + s * .5 * math.cos(a - .5), py + s * .5 * math.sin(a - .5))])
    # tail: a dark plume wrapping round the front
    tail = [(cx + s * 5.6, cy - s * .2), (cx + s * 5.4, cy + s * 2.0), (cx + s * 3, cy + s * 3.4),
            (cx - s * 1., cy + s * 3.7), (cx - s * 4.2, cy + s * 3.1)]
    tail2 = [(x - s * .2, y - s * 1.5) for x, y in tail[::-1]]
    tp = tail + tail2
    cv.obj([tp], .5)
    cv.hair(C.hatch_poly(tp, 70, 1.5, .2))
    cv.hair(C.hatch_poly(tp, -20, 2, .2))
    # head resting on the tail, nose to the left
    hx, hy = cx - s * 4.4, cy + s * .2
    head = [(hx + s * 2.4 * math.cos(a), hy + s * 2.0 * math.sin(a)) for a in [TAU * i / 24 for i in range(24)]]
    muzzle = [(hx - s * 2.0, hy + s * .1), (hx - s * 4.2, hy + s * .8), (hx - s * 4.3, hy + s * 1.7),
              (hx - s * 1.2, hy + s * 2.0)]
    cv.obj([muzzle], 1.)
    cv.obj([head], 1.)
    cv.hair([(hx - s * 1.6, hy + s * .5), (hx - s * .8, hy + s * .8), (hx - s * .1, hy + s * .6)])  # closed eye
    cv.obj([C._ell_pts(hx - s * 4.1, hy + s * 1.15, s * .55, s * .45, 10)], 1.5)  # nose
    cv.hair([(hx - s * 3.9, hy + s * 1.7), (hx - s * 2.6, hy + s * 1.8)])
    ear = [(hx - s * .2, hy - s * 1.9), (hx + s * 2.3, hy - s * 1.4), (hx + s * 2.0, hy + s * 1.6),
           (hx + s * .8, hy + s * 1.0)]
    cv.obj([ear], 1.)
    cv.hair(C.hatch_poly(ear, 0, 1.5, 0))
    cv.hair(C.hatch_poly(ear, 90, 1.5, .2))


def _scene(field, seed, date, small=False):
    """Everything inside the cartouche field polygon, returned clipped to it."""
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    fx, fy, fw, fh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    rng = random.Random(seed)
    cv = C.Canvas()
    hy = fy + fh * (.6 if not small else .58)
    # sky, darkest at the zenith
    b1, b2 = fy + (hy - fy) * .38, fy + (hy - fy) * .74
    for y_a, y_b, p in ((fy - 2, b1, 1.5), (b1, b2, 2.), (b2, hy + 1, 3.)):
        r = _rect(fx - 2, y_a, fw + 4, y_b - y_a)
        cv.obj([r], 0)
        cv.hair(C.hatch_poly(r, 0, p, .25))
    # aurora curtains: ruled vertically, a bright lower hem
    for k in range(2 if not small else 1):
        ya = fy + (hy - fy) * (.2 + .2 * k) + rng.uniform(-2, 2)
        hc = (hy - fy) * (.22 - .05 * k)
        ph1, ph2 = rng.uniform(0, TAU), rng.uniform(0, TAU)
        f1 = rng.uniform(1.2, 2.2)
        N = 48
        topl, botl = [], []
        for i in range(N + 1):
            t = i / N
            x = fx + fw * (-.05 + 1.1 * t)
            yt = ya + hc * .35 * math.sin(TAU * f1 * t + ph1) + hc * .15 * math.sin(TAU * 3.3 * t + ph2)
            yb = yt + hc * (.55 + .35 * math.sin(TAU * 1.7 * t + ph2))
            topl.append((x, yt))
            botl.append((x, yb))
        cur = topl + botl[::-1]
        cv.obj([cur], 0)
        vlines = C.hatch_poly(cur, 90, 2, .25 + k)
        cv.hair([[(p[0][0], min(p[0][1], p[1][1])), (p[0][0], max(p[0][1], p[1][1]) - 1.8 - rng.random() * 2)]
                 for p in vlines if abs(p[1][1] - p[0][1]) > 3])
        cv.hair(botl)
    # moon, phase of the morning
    ph = _moon_phase(date)
    mr = max(3.5, fh * .062)
    mx, my = fx + fw * .8, fy + fh * .14
    disc = C._ell_pts(mx, my, mr, mr, 32)
    cv.obj([disc], .5)
    ts = [math.pi * i / 16 for i in range(17)]
    side = -1 if ph < .5 else 1
    dark = [(mx + side * mr * math.sin(t), my - mr * math.cos(t)) for t in ts] + \
           [(mx - side * mr * math.cos(TAU * ph) * math.sin(t), my - mr * math.cos(t)) for t in ts[::-1]]
    if abs(_area(dark)) > 1:
        cv.obj([dark], 0)
        cv.hair(C.hatch_poly(dark, 0, 1.5, .25))
    # stars cut into the sky
    for _ in range(int(fw * fh / 900) if not small else 3):
        sx, sy = fx + rng.uniform(.05, .95) * fw, fy + rng.uniform(.04, .5) * (hy - fy)
        if math.hypot(sx - mx, sy - my) < mr * 2.5:
            continue
        s = rng.uniform(.8, 1.7)
        cv.obj([[(sx, sy - s * 1.6), (sx + s * .45, sy), (sx, sy + s * 1.6), (sx - s * .45, sy)]], 0)
        cv.obj([[(sx - s * 1.6, sy), (sx, sy - s * .45), (sx + s * 1.6, sy), (sx, sy + s * .45)]], 0)
    # the ice plain to the horizon
    plain = _rect(fx - 2, hy, fw + 4, fy + fh - hy + 2)
    cv.obj([plain], 0)
    cv.hair(C.hatch_poly(plain, 0, 3, 1.))
    # bergs on the horizon
    x = fx - rng.uniform(0, 10)
    while x < fx + fw:
        bw = fw * rng.uniform(.1, .22)
        if rng.random() < .8:
            _berg(cv, x, x + bw, hy + 1, hy - fh * rng.uniform(.04, .12), rng)
        x += bw * rng.uniform(.8, 1.3)
    # the ship, beset
    L = min(fw * .74, fh * .72)
    sx = fx + fw * .5
    wl = fy + fh * (.69 if not small else .72)
    # far floes between horizon and ship
    _pack(cv, fx, fw, hy + 2, wl - L * .05, random.Random(seed + 3), small=small)
    hh = _ship(cv, sx, wl, L, fy + fh * .06, rng, 0 if small else 1)
    _pressure_ridge(cv, sx - L * .62, sx + L * .58, wl, hh, rng)
    # near floes
    rows = _pack(cv, fx, fw, wl + hh * .9, fy + fh, random.Random(seed + 7), small=small)
    if not small:
        # the dog asleep on a near floe
        s = max(1.2, fh / 120)
        dy = wl + hh * .9 + (fy + fh - wl) * .3
        _dog(cv, fx + fw * .76, dy, s)
    cid = C._uid("sc", fx, fy, fw, fh, seed)
    return (f'<clipPath id="{cid}"><path d="{_d(field, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


def _area(p):
    return C._area(p)


# ------------------------------------------------------------------------------------------
# lettering (drawn strokes, no <text>)
# ------------------------------------------------------------------------------------------

_GLYPHS = {
    "T": (.78, [[(0, 1), (1, 1)], [(.5, 1), (.5, 0)]]),
    "H": (.78, [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .52), (1, .52)]]),
    "E": (.66, [[(1, 1), (0, 1), (0, 0), (1, 0)], [(0, .52), (.8, .52)]]),
    "R": (.74, [[(0, 0), (0, 1), (.7, 1), (.95, .9), (1, .76), (.95, .62), (.7, .52), (0, .52)], [(.55, .52), (1, 0)]]),
    "O": (.9, [[(.5 + .5 * math.cos(a), .5 + .5 * math.sin(a)) for a in [TAU * i / 24 for i in range(25)]]]),
    " ": (.45, []),
}


def _letter_ribbon(cv, centre, text, lh):
    seg = [0.]
    for (ax, ay), (bx, by) in zip(centre, centre[1:]):
        seg.append(seg[-1] + math.hypot(bx - ax, by - ay))
    total = seg[-1]
    track = lh * .4
    widths = [_GLYPHS[c][0] * lh for c in text]
    tw = sum(widths) + track * (len(text) - 1)

    def at(s):
        s = max(0., min(total, s))
        for i in range(1, len(seg)):
            if seg[i] >= s:
                t = (s - seg[i - 1]) / max(1e-6, seg[i] - seg[i - 1])
                (ax, ay), (bx, by) = centre[i - 1], centre[i]
                L = math.hypot(bx - ax, by - ay) or 1
                return ax + (bx - ax) * t, ay + (by - ay) * t, (bx - ax) / L, (by - ay) / L
        return centre[-1][0], centre[-1][1], 1., 0.

    s0 = total / 2 - tw / 2
    cv.obj([], 0)
    for ch, wdt in zip(text, widths):
        for stroke in _GLYPHS[ch][1]:
            pl = []
            for u, v in stroke:
                x, y, tx, ty = at(s0 + u * wdt)
                nx, ny = ty, -tx
                vv = (v - .5) * lh
                pl.append((x + nx * vv, y + ny * vv))
            cv.line(pl)
        s0 += wdt + track
    # fleurons either side: diamond, dash, dot
    for side in (-1, 1):
        base = total / 2 + side * (tw / 2 + lh * .9)
        x, y, tx, ty = at(base)
        nx, ny = ty, -tx
        d = lh * .32
        cv.obj([[(x - tx * d * 1.4, y - ty * d * 1.4), (x + nx * d, y + ny * d), (x + tx * d * 1.4, y + ty * d * 1.4),
                 (x - nx * d, y - ny * d)]], .5)
        cv.hair(C.hatch_poly([(x - tx * d * 1.4, y - ty * d * 1.4), (x + nx * d, y + ny * d), (x + tx * d * 1.4, y + ty * d * 1.4),
                              (x - nx * d, y - ny * d)], 0, 1.5, .2))
        x2, y2, _, _ = at(base + side * lh * 1.1)
        x3, y3, _, _ = at(base + side * lh * 3.6)
        cv.line([(x2, y2), (x3, y3)])
        x4, y4, _, _ = at(base + side * lh * 4.3)
        cv.heavy([(x4 - .3, y4), (x4 + .3, y4)])


# ------------------------------------------------------------------------------------------
# the bookshelf in the pedestal's tablet
# ------------------------------------------------------------------------------------------

def _bookshelf(tx, ty, tw, th, seed):
    rng = random.Random(seed)
    cv = C.Canvas()
    x0, y0, w, h = tx + 1.5, ty + 1.5, tw - 2, th - 2
    back = _rect(x0, y0, w, h)
    cv.obj([back], 0)
    cv.hair(C.hatch_poly(back, 0, 1.5, .25))
    shelf = y0 + h - 1.5
    x = x0 + 2
    lay_at = rng.uniform(.3, .4)
    lay_at2 = rng.uniform(.68, .78)
    while x < x0 + w - 3:
        frac = (x - x0) / w
        if abs(frac - lay_at) < .004 or abs(frac - lay_at2) < .004:
            # a little stack of books lying flat
            sw = rng.uniform(16, 22)
            yb = shelf
            for k in range(3):
                bh = rng.uniform(2.5, 3.6)
                bx = x + rng.uniform(-1, 1.5)
                b = _rect(bx, yb - bh, sw - k * 1.5, bh)
                cv.obj([b], .5)
                cv.hair([(bx + 1.5, yb - bh / 2), (bx + sw - k * 1.5 - 1.5, yb - bh / 2)] if k != 1 else
                        C.hatch_poly(b, 0, 1.5, .2))
                yb -= bh
            x += sw + 1.5
            continue
        bw = rng.choice((3., 3.5, 4., 4.5, 5., 6., 7.))
        bh = h * rng.uniform(.6, .94)
        b = _rect(x, shelf - bh, bw, bh)
        cv.obj([b], .5)
        tone = rng.random()
        if tone < .3:
            cv.hair(C.hatch_poly(b, 90, 1.5, .25))
        else:
            sh = _rect(x + bw * .62, shelf - bh, bw * .38, bh)
            cv.hair(C.hatch_poly(sh, 90, 1.5, .25))
        if bw >= 4:
            for fy in (.12, .2, .82):
                cv.hair([(x + .4, shelf - bh * (1 - fy)), (x + bw - .4, shelf - bh * (1 - fy))])
        x += bw + (.5 if rng.random() < .8 else 1.)
    cv.obj([_rect(x0, shelf, w, 1.5)], 0)
    cv.heavy([(x0, shelf + .75), (x0 + w, shelf + .75)])
    return cv.svg()


# ------------------------------------------------------------------------------------------
# layouts (copied from the house frame so the vignette can fill the whole field)
# ------------------------------------------------------------------------------------------

def _pedestal(x, y, w, h, seed=0):
    """The reference's base, filling x..x+w, y..y+h: a knurled cornice; a slab whose top is lightly
    ruled in perspective and whose front face is ruled mid-tone round a sunk blank tablet (for path
    lettering) flanked by rosettes; a second knurled bar; a flared plinth over a bead row.
    Returns (svg, (tx, ty, tw, th)), the tablet."""
    o = []
    kb = max(5, min(10, h * .11))
    inset = w * .035
    o.append(C.knurled_bar(x, y, w, kb))
    yy = y + kb
    slab = h * .5
    top = slab * .18
    o.append(f'<path d="M{_n(x + inset)},{_n(yy)}h{_n(w - 2 * inset)}v{_n(slab)}h{_n(-(w - 2 * inset))}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="M{_n(x + inset)},{_n(yy)}h{_n(w - 2 * inset)}l{_n(-inset * .5)},{_n(top)}'
             f'h{_n(-(w - 3 * inset))}z" fill="{C.pat("L")}" stroke="#000" stroke-width=".5"/>')
    fy = yy + top
    fh = slab - top
    o.append(f'<path d="M{_n(x + inset * 1.5)},{_n(fy)}h{_n(w - 3 * inset)}v{_n(fh)}'
             f'h{_n(-(w - 3 * inset))}z" fill="{C.pat("M")}" stroke="#000" stroke-width="1"/>')
    th = fh * .8
    tw = w * .66
    tx, ty = x + (w - tw) / 2, fy + (fh - th) / 2
    o.append(f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(tx + .5)},{_n(ty + .5)}h{_n(tw - 1)}l-1.5,1.5h{_n(-(tw - 4))}v{_n(th - 4)}l-1.5,1.5z" fill="#000" stroke="none"/>')
    for sx in (-1, 1):
        rx = x + w / 2 + sx * (tw / 2 + (w - 3 * inset - tw) / 4)
        rcy = fy + fh / 2
        rr = min(fh * .32, 10)
        o.append(f'<path d="{_d(C._ell_pts(rx, rcy, rr, rr, 24), True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        petals = "".join(_d([(rx, rcy), (rx + rr * .9 * math.cos(a + .25), rcy + rr * .9 * math.sin(a + .25)),
                             (rx + rr * .9 * math.cos(a - .25), rcy + rr * .9 * math.sin(a - .25))], True, 0)
                         for a in [TAU * i / 8 for i in range(8)])
        o.append(f'<path d="{petals}" fill="{C.pat("D")}" stroke="#000" stroke-width=".5"/>')
        o.append(f'<path d="{_d(C._ell_pts(rx, rcy, rr * .25, rr * .25, 10), True, 0)}" fill="#000"/>')
    yy = fy + fh
    o.append(C.knurled_bar(x + inset * .4, yy, w - inset * .8, kb))
    yy += kb
    ph = y + h - yy
    if ph > 6:
        fl = [(x + inset * 1.2 - inset * 1.1 * (i / 12) ** 2.2, yy + ph * .7 * i / 12) for i in range(13)]
        fr = [(2 * x + w - p[0], p[1]) for p in fl[::-1]]
        o.append(f'<path d="{_d(fl + fr, True, 0)}" fill="{C.pat("V")}" stroke="none"/>')
        o.append(f'<path d="{_d(fl, tol=0)}{_d(fr, tol=0)}" stroke="#000" stroke-width="1"/>')
        o.append(C.bead_moulding(x + inset * .1, yy + ph * .85, w - inset * .2, max(1., ph * .12)))
    return "".join(o), (tx, ty, tw, th)



def _cart_field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - 4.4, b - 4.4)


def _layout_band(w, h, seed, date):
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
    field = C._ell_pts(cx, cy, rx - 4.5, ry - 4.5, 64)
    o.append(_scene(field, seed, date, small=True))
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
    cw = min(w * .42, gh * 1.5)
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
    o.append(_scene(_cart_field(cx, cy, cw, gh + 4), seed, date, small=gh < 120))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    em = min(10., 6 + h * .01)
    top_free = em + 2
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # a moulding the whole plate hangs from, and a light ground under the base
    o.append(C.egg_and_dart(0, 0, w, em))
    o.append(C.dark_ground((0, py0 + ph - 2, w, h - py0 - ph + 2), "L"))
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=8, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_scene(_cart_field(cx, cy, cw, ch), seed, date))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 58), True, rng.randrange(1 << 20)))
    bh = min(17, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lc = C.Canvas()
    _letter_ribbon(lc, centre, "THE TERROR", bh * .52)
    o.append(lc.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = _pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_bookshelf(tx, ty, tw, th, seed + 11))
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
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 8 * 131
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date)
    else:
        body = _layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
