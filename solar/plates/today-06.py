"""today-06 "Your yard vs. the forecast": Parker's own backyard weather station on Sauvie Island,
engraved against the forecast. A forecast rain-cloud and a warmer-than-forecast sun hang over the
river cottonwoods and Mt. Hood; below, the station mast (anemometer, a heron weathervane, the
solar panel that feeds it, a louvred Stevenson screen) rises out of acanthus, and the rain gauge
that "catches 28% more" stands in the furrows. Tall plates add a pedestal whose tablet carries the
yard-vs-forecast thermograph (parsed from the page text) and a ribbon with the same two traces.
Easter egg: the weathervane is a Sauvie Island heron (with a tiny solar panel on the mast)."""
import sys
import math
import random
import re
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
hatch = C.hatch_poly


# ----------------------------------------------------------------------------------------------
# small engraving helpers
# ----------------------------------------------------------------------------------------------

def solid(cv, poly, outline=1.):
    """A black mass: white shape, then 1 px lines .8 apart."""
    cv.obj([poly], outline)
    cv.line(hatch(poly, 0, .8))


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def cyl_lines(x0, x1, y0, y1, n, light=.3):
    """Vertical shading lines on a cylinder x0..x1: none on the lit left part, closing up to the
    right like cos(theta)."""
    out = []
    w = x1 - x0
    for i in range(n):
        t = light + (1 - light) * (1 - math.cos(PI2 * (i + .5) / n)) if False else None
    k = 0
    x = x0 + w * light
    while x < x1 - .4:
        out.append([(x, y0), (x, y1)])
        u = (x - x0) / w
        step = max(1.5, 3.2 - 2.2 * (u - light) / (1 - light))
        x += step
        k += 1
    return out


PI2 = math.pi * 2


def _cloud_poly(cx, by, w, h, rng):
    """Cumulus outline: a flat-ish base at by, puffs above. Returns (poly, circles)."""
    circ = []
    n = 6
    for i in range(n):
        t = (i + .5) / n
        r = h * (.40 + .36 * math.sin(math.pi * t)) * rng.uniform(.88, 1.08)
        circ.append((cx - w / 2 + w * t, by - r * .55, r))
    top = []
    N = 70
    x0, x1 = cx - w / 2 - h * .25, cx + w / 2 + h * .25
    for i in range(N + 1):
        x = x0 + (x1 - x0) * i / N
        best = by
        for (ccx, ccy, r) in circ:
            dx = x - ccx
            if abs(dx) < r:
                y = ccy - math.sqrt(r * r - dx * dx)
                best = min(best, y)
        top.append((x, best))
    # trim the ends to the base
    top = [p for p in top if p[1] < by - .3]
    base = [(top[-1][0], by), (top[0][0], by)]
    for k in range(9):
        t = k / 8
        pass
    bottom = []
    for k in range(13):
        t = k / 12
        x = top[-1][0] + (top[0][0] - top[-1][0]) * t
        bottom.append((x, by + h * .1 * math.sin(math.pi * t * 3) ** 2))
    return top + bottom, circ


def cloud(cv, cx, by, w, h, rng):
    poly, circ = _cloud_poly(cx, by, w, h, rng)
    cv.obj([poly], 1.)
    top = [p for p in poly if p[1] < by - .3]
    # contour lines following the puffs: a white crown, closing up into a dark belly
    d, k = 2.2, 0
    while True:
        seg, segs = [], []
        for (x, y) in top:
            yy = y + d
            if yy < by - .4:
                seg.append((x, yy))
            elif len(seg) > 1:
                segs.append(seg)
                seg = []
        if len(seg) > 1:
            segs.append(seg)
        if not segs:
            break
        (cv.line if d > h * .62 else cv.hair)(segs)
        d += max(1.5, 3.2 - k * .35)
        k += 1
    # each puff's lower rim, where it overlaps the one behind
    for (ccx, ccy, r) in circ:
        arc = [(ccx + r * math.cos(a), ccy + r * math.sin(a)) for a in
               [.25 + 2.4 * i / 16 for i in range(17)]]
        arc = [p for p in arc if p[1] < by - 1]
        if len(arc) > 1:
            cv.line(arc)
    return poly


def sun(cv, cx, cy, r, nray=20):
    star = []
    for i in range(nray * 2):
        a = math.pi * i / nray - math.pi / 2
        rr = r * (2.05 if i % 4 == 0 else 1.75 if i % 2 == 0 else 1.18)
        star.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    cv.obj([star], .5)
    disc = _ell(cx, cy, r, r, 40)[:-1]
    cv.obj([disc], 1.)
    # concentric engraved rings, closer toward the lower right limb
    for f in (.82, .64, .46):
        cv.hair(_ell(cx, cy, r * f, r * f, 32))
    cv.hair(hatch(_ell(cx + r * .35, cy + r * .35, r * .9, r * .9, 30)[:-1], -45, 1.5))
    cv.line([p for p in _ell(cx, cy, r - 1.2, r - 1.2, 30, .1, 1.6)])


def heron(cv, x, y, s, facing=1):
    """A heron weathervane figure standing on a rod at (x, y), about 10 s long. Black silhouette."""
    f = facing
    P = lambda a, b: (x + f * a * s, y - b * s)
    body = [P(-4.5, 4.2), P(-2, 5.6), P(1, 5.8), P(2.6, 5.2), P(3.4, 6.6), P(3.0, 8.6), P(3.6, 10.2),
            P(4.6, 10.6), P(8.6, 10.0), P(4.8, 9.7), P(4.1, 9.0), P(4.3, 7.0), P(3.9, 5.0), P(2.6, 3.9),
            P(.6, 3.3), P(-2, 3.4), P(-5.2, 3.0)]
    solid(cv, body, .5)
    cv.line([P(.2, 3.4), P(-.2, 0)])
    cv.line([P(1.2, 3.4), P(1.6, 0)])


def anemometer(cv, x, y, s):
    """Three-cup anemometer whose hub sits at (x, y)."""
    cv.obj([rect(x - .6 * s, y - 1 * s, 1.2 * s, 4 * s)], .5)
    for sd in (-1, 1):
        cv.line([(x, y), (x + sd * 7 * s, y - .6 * s)])
    cv.line([(x, y), (x + 2.2 * s, y + 1.6 * s)])
    # left cup: opening toward us (black mouth, white rim)
    lx, ly = x - 7 * s, y - .6 * s
    cv.obj([_ell(lx - 1.6 * s, ly, 2.4 * s, 2.0 * s, 20)[:-1]], 1.)
    solid(cv, _ell(lx - 1.6 * s, ly, 1.5 * s, 1.25 * s, 18)[:-1], 0)
    # right cup: seen from the back, a shaded bowl
    rx, ry = x + 7 * s, y - .6 * s
    bowl = [(rx + 2.6 * s * math.cos(a), ry + 2.1 * s * math.sin(a)) for a in
            [-math.pi / 2 + math.pi * i / 14 for i in range(15)]]
    bowl = [(rx, ry - 2.1 * s)] + bowl
    cv.obj([bowl], 1.)
    cv.hair(hatch(bowl, 90, 1.5))
    # front cup, foreshortened
    fx, fy = x + 2.2 * s, y + 1.6 * s
    cv.obj([_ell(fx, fy + 1.2 * s, 1.8 * s, 1.5 * s, 16)[:-1]], 1.)
    cv.line(hatch(_ell(fx + .4 * s, fy + 1.5 * s, 1.1 * s, 1.0 * s, 12)[:-1], 0, .8))
    cv.obj([_ell(x, y, 1.2 * s, .9 * s, 12)[:-1]], 1.)


def stevenson(cv, cx, top, s):
    """A louvred Stevenson screen, centre cx, roof ridge at top."""
    bw, bh = 15 * s, 12 * s
    dep = 4 * s
    ry = top + 4 * s
    # side face (perspective) to the right
    side = [(cx + bw / 2, ry + 1.6 * s), (cx + bw / 2 + dep, ry), (cx + bw / 2 + dep, ry + bh - 1.4 * s),
            (cx + bw / 2, ry + bh + 1.6 * s)]
    cv.obj([side], 1.)
    cv.hair(hatch(side, 0, 1.5))
    cv.line(hatch(side, 60, 3))
    front = rect(cx - bw / 2, ry + 1.6 * s, bw, bh)
    cv.obj([front], 1.)
    # louvres: each a 1 px slat edge with a hair shadow under it
    y = ry + 1.6 * s + 2
    while y < ry + 1.6 * s + bh - 1.5:
        cv.line([(cx - bw / 2 + 1.2, y), (cx + bw / 2 - 1.2, y)])
        cv.hair([(cx - bw / 2 + 1.2, y + 1.5), (cx + bw / 2 - 1.2, y + 1.5)])
        y += 3.2 if s < 1.4 else 3.6
    cv.line([(cx, ry + 1.6 * s), (cx, ry + 1.6 * s + bh)])
    # gabled roof with a shadowed eave
    roof = [(cx - bw / 2 - 2 * s, ry + 2.2 * s), (cx - bw / 4, top), (cx + bw / 2 + dep * .6, top - .4 * s),
            (cx + bw / 2 + dep + 1.6 * s, ry + .6 * s), (cx + bw / 2 + 1 * s, ry + 2.4 * s)]
    cv.obj([roof], 1.)
    cv.hair(hatch(roof, -20, 1.5))
    cv.line([(cx - bw / 2 - 1.6 * s, ry + 2.9 * s), (cx + bw / 2 + 1 * s, ry + 3.0 * s)])
    # legs
    for lx in (cx - bw / 2 + 1.5 * s, cx + bw / 2 - 1.5 * s):
        cv.obj([rect(lx - .6 * s, ry + 1.6 * s + bh, 1.2 * s, 3.2 * s)], .5)


def solar_panel(cv, x, y, s):
    """A small tilted panel clamped to the mast at (x, y), facing south-left."""
    p = [(x - 1 * s, y), (x - 9 * s, y + 2.4 * s), (x - 8.4 * s, y + 8 * s), (x - .6 * s, y + 5.2 * s)]
    cv.obj([p], 1.)
    cv.line(hatch(p, 15, 1.5))
    # cell grid: white rules through the dark glass
    cv.obj([], 0)
    for t in (1 / 3, 2 / 3):
        a = (p[0][0] + (p[1][0] - p[0][0]) * t, p[0][1] + (p[1][1] - p[0][1]) * t)
        b = (p[3][0] + (p[2][0] - p[3][0]) * t, p[3][1] + (p[2][1] - p[3][1]) * t)
        cv.obj([[(a[0] - .4, a[1]), (a[0] + .4, a[1]), (b[0] + .4, b[1]), (b[0] - .4, b[1])]], 0)
    a = ((p[0][0] + p[3][0]) / 2, (p[0][1] + p[3][1]) / 2)
    b = ((p[1][0] + p[2][0]) / 2, (p[1][1] + p[2][1]) / 2)
    cv.obj([[(a[0], a[1] - .4), (b[0], b[1] - .4), (b[0], b[1] + .4), (a[0], a[1] + .4)]], 0)
    cv.obj([], 0)
    cv.line([(x - 1 * s, y + 2.6 * s), (x, y + 2.6 * s)])


def rain_gauge(cv, cx, base, s, w=None, h=None):
    w = w or 9 * s
    h = h or 24 * s
    x0, x1 = cx - w / 2, cx + w / 2
    top = base - h
    er = w * .18
    body = [(x0, top)] + [(x1, top)] + [(cx + w / 2 * math.cos(a), base + er * math.sin(a))
                                       for a in [math.pi * i / 16 for i in range(17)]]
    # shadow cast on the ground to the right
    sh = _ell(cx + w * .55, base + er * .5, w * .85, er * 1.1, 20)[:-1]
    solid(cv, sh, 0)
    cv.obj([body], 1.)
    cv.hair(cyl_lines(x0, x1, top + er, base + er * .7, 0, .42))
    cv.line([[(x1 - 1.2, top + er), (x1 - 1.2, base + er * .6)]])
    # collar where the funnel meets the tube
    col = top + h * .22
    cv.line([(x0, col)] + [(cx + w / 2 * math.cos(a), col + er * .8 * math.sin(a))
                           for a in [math.pi - math.pi * i / 12 for i in range(13)]])
    # graduations on the lit side
    y = col + 2.5
    k = 0
    while y < base - 1.5:
        L = w * (.34 if k % 5 == 0 else .18)
        cv.hair([(x0 + w * .1, y), (x0 + w * .1 + L, y)])
        y += max(1.5, 1.6 * s)
        k += 1
    # funnel mouth: white rim, black throat
    rim = _ell(cx, top, w / 2 + .6, er + .6, 24)[:-1]
    cv.obj([rim], 1.)
    solid(cv, _ell(cx, top + .3, w / 2 - 1.2, er * .6, 20)[:-1], 0)


def treeline(cv, X, W, hz, s, rng):
    pts = [(X - 4, hz + 1)]
    x = X - 4
    while x < X + W + 4:
        r = rng.uniform(2.5, 5.5) * s
        for i in range(7):
            a = math.pi + math.pi * i / 6
            pts.append((x + r + r * math.cos(a), hz - r * .9 - r * .6 * math.sin(-a) + rng.uniform(-.3, .3)))
        x += r * 1.7
    pts.append((X + W + 4, hz + 1))
    cv.obj([pts], .5)
    cv.hair(hatch(pts, 90, 1.5))
    cv.hair(hatch(pts, 0, 2, .5))
    return pts


def mt_hood(cv, x, hz, s):
    peak = (x, hz - 17 * s)
    m = [(x - 22 * s, hz), (x - 9 * s, hz - 8 * s), (x - 3.5 * s, hz - 14 * s), peak, (x + 4 * s, hz - 13 * s),
         (x + 11 * s, hz - 7 * s), (x + 24 * s, hz)]
    cv.obj([m], .5)
    snow = [(x - 7 * s, hz - 10 * s), (x - 3.5 * s, hz - 14 * s), peak, (x + 4 * s, hz - 13 * s), (x + 8 * s, hz - 9 * s),
            (x + 5 * s, hz - 10 * s), (x + 3 * s, hz - 8.5 * s), (x + .5 * s, hz - 11 * s), (x - 2 * s, hz - 8.5 * s),
            (x - 4.5 * s, hz - 10.5 * s)]
    lower = [p for p in m]
    # shaded east flank darker, west flank light ruled; the snowcap stays carved white
    east = [peak, (x + 24 * s, hz), (x + 1 * s, hz)]
    cv.hair(hatch(lower, 0, 2))
    cv.hair(hatch(east, 60, 1.5))
    cv.obj([snow], 0)
    for k in range(3):
        cv.hair([(x + (k - 1) * 2.2 * s, hz - (12.5 - abs(k - 1)) * s), (x + (k - 1) * 3.6 * s, hz - 9 * s)])


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def scene(X, Y, W, H, seed, level=2):
    """Engraved yard-vs-forecast vignette filling the box (callers clip it to the field)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    s = max(.45, min(H / 100., W / 115.))
    hz = Y + H * (.64 if level else .7)
    # sky: ruled, darker aloft
    sky = rect(X - 3, Y - 3, W + 6, hz - Y + 4)
    cv.obj([sky], 0)
    yy = Y - 3
    cv.hair([[(X - 3, y), (X + W + 3, y)] for y in [Y - 3 + 1.5 * k for k in range(int((hz - Y + 4) / 1.5) + 1)]
             if y < Y + (hz - Y) * .35])
    y = Y + (hz - Y) * .35
    tog = 0
    while y <= hz + 1:
        cv.hair([(X - 3, y), (X + W + 3, y)])
        y += 2 if y < Y + (hz - Y) * .7 else 3
    if level == 0:
        ccx, cby = X + W * .5, Y + H * .4
        cloud(cv, ccx, cby, W * .52, H * .3, rng)
        cv.obj([], 0)
        ground = rect(X - 3, hz, W + 6, Y + H - hz + 3)
        cv.obj([ground], .5)
        y, p = hz + 1.5, 1.5
        while y < Y + H + 3:
            cv.hair([(X - 3, y), (X + W + 3, y)])
            p = min(3, p + .25)
            y += p
        cv.obj([], 0)
        for i in range(-3, 4):
            x = ccx + i * W * .075
            cv.line([[(x + 1.2 * (k + .5) * .3 - k * 0, cby + 4 + k * 4.5), (x - 1.0 - k * .3, cby + 7 + k * 4.5)]
                     for k in range(int((Y + H - cby) / 4.5)) if (k + i) % 2 == 0][:3])
        rain_gauge(cv, ccx + W * .02, hz + (Y + H - hz) * .45, s, W * .09, H * .32)
        return cv.svg()

    # sun (warmer than forecast) peeping round the cloud, upper right
    sun(cv, X + W * .52, Y + H * .2, H * .075)
    # Mt. Hood far off, and the cottonwoods along the channel
    mt_hood(cv, X + W * .5, hz - 1, s * .9)
    treeline(cv, X, W, hz + .5, s * .8, rng)
    # forecast cloud, its rain slanting across the fields
    ccx, cby = X + W * .3, Y + H * .36
    cl = cloud(cv, ccx, cby, W * .38, H * .16, rng)
    # ground: perspective furrows over ruled tilth
    ground = rect(X - 3, hz + 1, W + 6, Y + H - hz + 3)
    cv.obj([ground], .5)
    y, p = hz + 2.5, 1.5
    while y < hz + (Y + H - hz) * .3:
        cv.hair([(X - 3, y), (X + W + 3, y)])
        p = min(3, p * 1.18)
        y += p
    vx, vy = X + W * .4, hz - H * .35
    t0 = (hz + 1 - vy) / (Y + H + 3 - vy)
    for i in range(-20, 30):
        bx = vx + i * W * .036
        (cv.line if i % 2 else cv.hair)([(vx + (bx - vx) * t0, hz + 1), (bx, Y + H + 3)])
    # grass and stubble along the furrows nearer the eye
    for j in range(60):
        gx0 = X + rng.uniform(0, W)
        gy0 = hz + (Y + H - hz) * rng.uniform(.35, 1.)
        hh = (1.5 + 2.5 * (gy0 - hz) / (Y + H - hz)) * s
        for k in (-1, 0, 1):
            cv.hair([(gx0, gy0), (gx0 + k * hh * .45, gy0 - hh)])
    # rain
    cv.obj([], 0)
    span = W * .34
    k = 0
    for i in range(16):
        x = ccx - span / 2 + span * i / 15
        y0 = cby + 2 + (i % 3) * 2.5
        pts = []
        y = y0
        while y < hz + (Y + H - hz) * .5:
            pts.append([(x - (y - y0) * .28, y), (x - (y + 3.5 * s - y0) * .28, y + 3.5 * s)])
            y += 7.5 * s
        cv.line(pts)
    # the rain gauge in the furrows, catching it
    gx = X + W * .36
    gbase = Y + H * .9
    rain_gauge(cv, gx, gbase, s)
    # the station mast rising out of acanthus
    s0 = s
    s = s * 1.3
    mx = X + W * .72
    mbase = Y + H * .93
    mtop = Y + H * .14
    mast = rect(mx - 1.3 * s, mtop, 2.6 * s, mbase - mtop)
    cv.obj([mast], 1.)
    cv.hair([(mx + .2 * s, mtop + 2), (mx + .2 * s, mbase)])
    cv.line([(mx + .8 * s, mtop + 2), (mx + .8 * s, mbase)])
    # cross arm with the heron vane
    ay = mtop + 15 * s
    arm = rect(mx - 1, ay - .7 * s, 15 * s, 1.4 * s)
    cv.obj([arm], .5)
    cv.line([(mx, ay + .5 * s), (mx + 15 * s, ay + .5 * s)])
    vx2 = mx + 13 * s
    cv.obj([rect(vx2 - .5 * s, ay - 4 * s, 1 * s, 4 * s)], .5)
    rod = [(vx2 - 10 * s, ay - 4.4 * s), (vx2 + 6 * s, ay - 4.4 * s)]
    cv.line(rod)
    arrow = [(vx2 + 8 * s, ay - 4.4 * s), (vx2 + 5 * s, ay - 6 * s), (vx2 + 5.6 * s, ay - 4.4 * s),
             (vx2 + 5 * s, ay - 2.8 * s)]
    solid(cv, arrow, .5)
    heron(cv, vx2 - 4 * s, ay - 4.4 * s, s * .8, 1)
    # solar panel (Parker's) feeding the station
    solar_panel(cv, mx - 1.3 * s, ay + 3 * s, s)
    anemometer(cv, mx, mtop, s)
    # Stevenson screen on the mast
    stevenson(cv, mx, Y + H * .44, s * .9)
    # acanthus springing from the foot of the mast
    s = s0
    L = H * .25
    C.acanthus_frond(mx - 1, mbase + 1, -150, L, 3, 24, -.8, -4.2, rng.randrange(1 << 20), cv=cv)
    C.acanthus_frond(mx + 1, mbase + 1, -30, L * .95, 3, 24, .8, 4.2, rng.randrange(1 << 20), cv=cv)
    C.acanthus_finger(mx, mbase + 2, -95, L * .7, cv=cv, bend=-.3, curl=-3.5)
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# yard vs forecast data (parsed from the page; falls back to the sample day)
# ----------------------------------------------------------------------------------------------

def temps(ctx):
    txt = (ctx or {}).get("sample", "") or ""
    yard = [(int(a), int(b)) for a, b in re.findall(r"(\d+)\D{0,3}/\s*(\d+)\D{0,3}\s*forecast", txt)]
    fc = [(int(a), int(b)) for a, b in re.findall(r"forecast\s*(\d+)\D{0,3}/\s*(\d+)", txt)]
    if len(yard) < 1 or len(fc) < 1:
        yard, fc = [(67, 52), (61, 50), (54, 49)], [(65, 51), (60, 48), (53, 48)]
    n = min(len(yard), len(fc), 3)
    if n < 3:
        yard = (yard + [(61, 50), (54, 49)])[:3]
        fc = (fc + [(60, 48), (53, 48)])[:3]
    return yard[:3], fc[:3]


def _trace(days, x, y, w, h, lo, hi, n=90):
    """Diurnal curve through the daily (high, low) pairs: low at dawn, high mid-afternoon."""
    pts = []
    for i in range(n + 1):
        t = i / n * len(days)
        d = min(int(t), len(days) - 1)
        f = t - d
        H, L = days[d]
        Ln = days[min(d + 1, len(days) - 1)][1]
        if f < .25:
            v = L + (H - L) * 0 if False else L
            v = L
            v = L + 0 * f
            # night: easing from previous evening down to the low
            v = L + (H - L) * .0
        if f < .6:
            v = L + (H - L) * (1 - math.cos(math.pi * max(0, f - .22) / .38)) / 2 if f > .22 else L
        else:
            v = Ln + (H - Ln) * (1 + math.cos(math.pi * (f - .6) / .62)) / 2
        pts.append((x + w * i / n, y + h - (v - lo) / (hi - lo) * h))
    return pts


def thermograph(x, y, w, h, ctx, frame=True):
    yard, fc = temps(ctx)
    vals = [v for d in yard + fc for v in d]
    lo, hi = min(vals) - 2, max(vals) + 2
    o = []
    if frame:
        o.append(f'<path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("L")}" stroke="none"/>')
        g = "".join(f"M{_n(x + w * k / 3)},{_n(y + 1)}v{_n(h - 2)}" for k in (1, 2))
        g += "".join(f"M{_n(x + w * k / 12)},{_n(y + h - 2.5)}v2.5" for k in range(1, 12))
        o.append(f'<path d="{g}" stroke="#000" stroke-width=".5"/>')
    py0, ph = y + h * .08, h * .8
    f = _trace(fc, x + 2, py0, w - 4, ph, lo, hi)
    yv = _trace(yard, x + 2, py0, w - 4, ph, lo, hi)
    o.append(f'<path d="{_d(f, tol=.2)}" stroke="#000" stroke-width="1" stroke-dasharray="3 2.5" fill="none"/>')
    o.append(f'<path d="{_d(yv, tol=.2)}" stroke="#000" stroke-width="1.5" fill="none"/>')
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# layouts (from the house codex, with the field engraved edge to edge)
# ----------------------------------------------------------------------------------------------

def _field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return a, b


def _clipped(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def framed_scene(cx, cy, a, b, cid, seed, level=2, shrink=4.6):
    poly = C._superellipse(cx, cy, a - shrink, b - shrink)
    d = _d(poly, True, .1)
    return _clipped(cid, d, scene(cx - a, cy - b, 2 * a, 2 * b, seed, level))


def layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.8, 130)
    o.append(C._clip(C._uid("b6", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    poly = _ell(cx, cy, rx - 2.2, ry - 2.2, 64)[:-1]
    o.append(_clipped(C._uid("bs6", w, h), _d(poly, True, .1),
                      scene(cx - rx, cy - ry, 2 * rx, 2 * ry, seed, 0 if gh < 70 else 1)))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 2.2, ry - 2.2, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.55)
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .07), rmax=r * .8,
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m6", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, ch)
    o.append(framed_scene(cx, cy, a, b, C._uid("ms6", w, h), seed, 2 if gh > 80 else 1))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # light-ruled paper behind the crest so nothing is bare
    o.append(C.dark_ground((0, 0, w, top_free + 2), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
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
    o.append(C._clip(C._uid("t6", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, ch)
    o.append(framed_scene(cx, cy, a, b, C._uid("ts6", w, h), seed, 2))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # the two traces woven along the ribbon face
    yard, fc = temps(ctx)
    n = len(centre)
    sw = [(p[0], p[1] - bh * .18 * math.sin(i / (n - 1) * math.pi * 6)) for i, p in enumerate(centre)]
    sf = [(p[0], p[1] + bh * .18 * math.sin(i / (n - 1) * math.pi * 6)) for i, p in enumerate(centre)]
    o.append(f'<path d="{_d(sw[1:-1], tol=0)}" stroke="#000" stroke-width="1" fill="none"/>'
             f'<path d="{_d(sf[1:-1], tol=0)}" stroke="#000" stroke-width="1" stroke-dasharray="2.5 2" fill="none"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py + 3, w, ped_h - 3), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(thermograph(tx + 3, ty + 3, tw - 5, th - 5, ctx))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh), "L"))
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f6", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", "") + "today-06"))
    if h < 110:
        body = layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx)
    else:
        body = layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
