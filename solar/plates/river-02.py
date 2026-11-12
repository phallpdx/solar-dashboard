"""river-02 "The Columbia, by the numbers": the river at Sauvie Island this morning.
A USGS staff gauge on a creosoted pile reads the day's level (ctx sample, default 4.7 ft) with the
tide's wet band on the wood; a grain ship runs up the channel under Mt. Hood; the Washington shore
of firs; reeds of the island bank. The house Codex frame carries it. Easter egg: Parker's Sauvie
Island heron standing on top of the gauge pile."""
import sys
import math
import random
import re
import engraving_codex as C

TAU = 2 * math.pi
_K = 2 ** (-1 / 2.6)


def _level(ctx):
    m = re.search(r"at ([0-9]+(?:\.[0-9])?) ft at Vancouver", (ctx or {}).get("sample", "") or "")
    try:
        return float(m.group(1)) if m else 4.7
    except ValueError:
        return 4.7


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _wave_row(x0, x1, y, amp, per, ph, step=2.):
    pts = []
    x = x0
    while x <= x1 + step:
        xx = min(x, x1)
        pts.append((xx, y + amp * math.sin(TAU * xx / per + ph) + amp * .4 * math.sin(TAU * xx / (per * .37) + ph * 1.7)))
        if xx >= x1:
            break
        x += step
    return pts


def _split(pl, rng, dash=(10, 40), gap=(1.6, 3.4)):
    """Break a polyline into dashes (by arc length)."""
    out, cur, acc = [], [pl[0]], 0.
    target = rng.uniform(*dash)
    gapping = False
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        acc += L
        if not gapping:
            cur.append(b)
            if acc >= target:
                if len(cur) > 1:
                    out.append(cur)
                gapping, acc, target = True, 0., rng.uniform(*gap)
        else:
            if acc >= target:
                cur = [b]
                gapping, acc, target = False, 0., rng.uniform(*dash)
    if not gapping and len(cur) > 1:
        out.append(cur)
    return out


# ---------------------------------------------------------------- stroke digits (no <text>)
_DIG = {
    "0": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)]],
    "1": [[(.5, 0), (.5, 2)], [(.15, .35), (.5, 0)]],
    "2": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (1, 2)]],
    "3": [[(0, 0), (1, 0), (1, 2), (0, 2)], [(.2, 1), (1, 1)]],
    "4": [[(0, 0), (0, 1), (1, 1)], [(1, 0), (1, 2)]],
    "5": [[(1, 0), (0, 0), (0, 1), (1, 1), (1, 2), (0, 2)]],
    "6": [[(1, 0), (0, 0), (0, 2), (1, 2), (1, 1), (0, 1)]],
    "7": [[(0, 0), (1, 0), (.4, 2)]],
    "8": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)], [(0, 1), (1, 1)]],
    "9": [[(1, 1), (0, 1), (0, 0), (1, 0), (1, 2), (0, 2)]],
}


def _digit(ch, x, y, hgt):
    s = hgt / 2
    return [[(x + px * s * .85, y + py * s) for px, py in st] for st in _DIG[ch]]


# ---------------------------------------------------------------- the scene
def _scene(cv, X0, Y0, W, H, level, seed, compact):
    rng = random.Random(seed)
    X1, Y1 = X0 + W, Y0 + H
    hy = Y0 + H * (.52 if not compact else .5)            # horizon (far waterline)
    S = H / 100.

    # sky: ruled, denser aloft, with long dawn streaks of cloud
    sky = _rect(X0 - 2, Y0 - 2, W + 4, hy - Y0 + 4)
    cv.obj([sky], 0)
    y = Y0
    while y < hy:
        t = (y - Y0) / max(1., hy - Y0)
        cv.hair([(X0, y), (X1, y)])
        y += 1.5 if t < .35 else (2. if t < .7 else 3.)
    if not compact:
        for i in range(4):
            cx = X0 + W * (.12 + .26 * i + rng.uniform(-.05, .05))
            cy = Y0 + (hy - Y0) * rng.uniform(.18, .5)
            L, th = W * rng.uniform(.12, .2), max(3.5, H * .022)
            top = [(cx - L + 2 * L * k / 16, cy - th * math.sin(math.pi * k / 16) ** .7) for k in range(17)]
            bot = [(cx + L - 2 * L * k / 16, cy + th * .45 * math.sin(math.pi * k / 16)) for k in range(17)]
            poly = top + bot
            cv.obj([poly], .5)
            cv.hair(C.hatch_poly(poly, 0, 3, .5 + cy % 3, 1.5))
        # two gulls
        for gx, gy, gs in ((.3, .2, 1.), (.36, .26, .8)):
            x, y = X0 + W * gx, Y0 + (hy - Y0) * gy
            r = 3.2 * S * gs
            cv.obj([], 0)
            cv.line([(x - r, y + r * .1), (x - r * .45, y - r * .45), (x, y + r * .15), (x + r * .45, y - r * .45), (x + r, y + r * .1)])

    # Mt. Hood: steep summit pyramid, concave flanks, the Steel Cliff shoulder to the east
    pkx, pky = X0 + W * .45, hy - H * (.36 if not compact else .3)
    mh = hy - pky
    mw = min(W * .36, mh * 2.3)
    rm = random.Random(seed + 7)
    left, right = [], []
    for k in range(25):
        t = k / 24.
        yy = pky + mh * t
        xl = mw * (.32 * t + .68 * t ** 2.3) * (1 + .03 * math.sin(k * 2.1)) + rm.uniform(0, .8)
        xr = mw * (.3 * t + .7 * t ** 2.1) * 1.08 + mw * .1 * math.exp(-((t - .38) / .1) ** 2) + rm.uniform(0, .8)
        left.append((pkx - xl, yy))
        right.append((pkx + xr, yy))
    mtn = left[::-1] + [(pkx - .6, pky - 1.2), (pkx + .6, pky - 1.2)] + right
    base = mtn + [(pkx + mw * 1.3, hy + 2), (pkx - mw * 1.3, hy + 2)]
    cv.obj([base], 1)
    inside = lambda p: _inside(p, base)
    snow_y = lambda x: pky + mh * (.52 + .13 * math.sin((x - pkx) / mw * 9 + 1) + .07 * math.sin((x - pkx) / mw * 23)
                                   + .25 * (abs(x - pkx) / mw) ** 2)
    ridge = [(pkx + mh * .07 * t * math.sin(t * 4), pky + mh * t) for t in [k / 20 for k in range(21)]]
    east = [(pkx, pky)] + right[1:] + ridge[::-1]
    cv.hair(_clip_lines(C.hatch_poly(east, 64, 1.5), base))
    west = left + [(pkx, hy)] + ridge[::-1]
    cv.hair(C.hatch_poly(west, -14, 3., .7))
    xs = [pkx - mw * 1.3 + i * mw * 2.6 / 80 for i in range(81)]
    rock = [(x, snow_y(x)) for x in xs] + [(xs[-1], hy + 2), (xs[0], hy + 2)]
    cv.hair(_clip_lines(C.hatch_poly(rock, -30, 1.5) + C.hatch_poly(rock, 30, 3), base))
    # glaciers and couloirs: heavier lines raking down the snowfield
    for k in range(7 if not compact else 3):
        f = -.6 + 1.2 * k / (6 if not compact else 2)
        x0 = pkx + mw * f * .18
        y0 = pky + mh * (.08 + .05 * abs(f))
        pts = [(x0 + mw * f * .55 * t + 1.2 * math.sin(t * 7 + k), y0 + mh * .5 * t) for t in [j / 10 for j in range(11)]]
        pts = [p for p in pts if inside(p) and p[1] < snow_y(p[0]) + 2]
        if len(pts) > 1:
            (cv.line if f > 0 else cv.hair)(pts)
    cv.line(ridge[:13])

    # foothills, then the Washington shore of firs
    fh = [(X0 - 2, hy - H * .07)]
    for i in range(41):
        x = X0 + W * i / 40
        fh.append((x, hy - H * (.05 + .025 * math.sin(i * .5 + seed) + .015 * math.sin(i * 1.3))))
    fh += [(X1 + 2, hy - H * .05), (X1 + 2, hy + 1), (X0 - 2, hy + 1)]
    cv.obj([fh], .5)
    cv.hair(C.hatch_poly(fh, 20, 1.5))
    cv.hair(C.hatch_poly(fh, -40, 3))
    shore = [(X0 - 2, hy)]
    x = X0 - 2
    rs = random.Random(seed + 3)
    while x < X1 + 2:
        th = H * rs.uniform(.022, .05)
        wv = th * .45
        base = hy - H * .018
        shore += [(x, base), (x + wv, base - th), (x + 2 * wv, base)]
        x += 2 * wv * rs.uniform(.7, 1.0)
    shore += [(X1 + 2, hy + 1), (X0 - 2, hy + 1)]
    cv.obj([shore], .5)
    cv.line(C.hatch_poly(shore, 90, 1.5))
    cv.hair(C.hatch_poly(shore, 0, 2))

    # the river
    wy0 = hy
    water = _rect(X0 - 2, wy0, W + 4, Y1 - wy0 + 2)
    cv.obj([water], 0)
    # the ship's span (for its reflection)
    L = min(W * .5, H * 1.25)
    sx = X0 + W * (.1 if not compact else .06)
    ys = hy + H * .075
    hh = max(3., L * .075)
    rw = random.Random(seed + 11)
    y = wy0 + 1
    while y < Y1 + 2:
        t = (y - wy0) / max(1., Y1 - wy0)
        amp = .25 + 1.1 * t
        row = _wave_row(X0 - 2, X1 + 2, y, amp, 14 + 30 * t, rw.uniform(0, TAU))
        in_refl = ys - 1 < y < ys + hh * 2.6
        if in_refl:
            a = [p for p in row if p[0] < sx + L * .02]
            b = [p for p in row if sx + L * .02 <= p[0] <= sx + L * .96]
            c = [p for p in row if p[0] > sx + L * .96]
            for part in (a, c):
                if len(part) > 1:
                    cv.hair(_split(part, rw, (8 + 30 * (1 - t), 30 + 40 * (1 - t))))
            if len(b) > 1:
                cv.line(_split(b, rw, (14, 50), (.8, 1.6)))
        else:
            segs = _split(row, rw, (8 + 30 * (1 - t), 30 + 40 * (1 - t)), (1.4, 2.4 + 2 * t))
            (cv.line if t > .55 else cv.hair)(segs)
        y += 1.5 if t < .2 else (2. if t < .5 else 3.)

    # the grain ship running up the channel
    _ship(cv, sx, ys, L, hh, compact)

    # the gauge pile in the foreground
    gx = X0 + W * (.86 if not compact else .84)
    wl = hy + H * (.31 if not compact else .3)
    pw = max(5., H * .085)
    ft = H * .105
    top = wl - ft * (3.3 if not compact else 2.4)
    _pile(cv, gx, top, wl, pw, ft, level, compact)
    if not compact:
        _heron(cv, gx + pw * .1, top - pw * .1, H * .25)
    # the island bank, reeds and cattails, bottom left
    _bank(cv, X0, Y1, W, H, seed, compact)


def _inside(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (x1 - x0) * (y - y0) / (y1 - y0):
            c = not c
    return c


def _clip_lines(lines, poly):
    """Keep the parts of 2-point lines inside poly (sampled)."""
    out = []
    for (a, b) in lines:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(2, int(L / 1.))
        cur = []
        for i in range(n + 1):
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            if _inside(p, poly):
                cur.append(p)
            elif cur:
                if len(cur) > 1:
                    out.append([cur[0], cur[-1]])
                cur = []
        if len(cur) > 1:
            out.append([cur[0], cur[-1]])
    return out


def _ship(cv, sx, ys, L, hh, compact):
    bx = sx + L
    # bow wave and wake foam
    foam = [(bx - L * .08, ys + .5), (bx + L * .015, ys - hh * .15), (bx + L * .05, ys + hh * .35), (bx - L * .1, ys + hh * .45)]
    hull = [(sx, ys - hh), (sx + L * .03, ys - hh * .02), (sx + L * .045, ys), (bx - L * .04, ys), (bx, ys - hh * 1.25),
            (bx - L * .06, ys - hh * 1.25), (bx - L * .07, ys - hh * 1.0), (sx + L * .02, ys - hh)]
    cv.obj([hull], 1)
    cv.heavy(C.hatch_poly(hull, 0, 1.5, .3))
    # hatch covers along the deck, cranes between them
    nh = 5
    hy0 = ys - hh
    for i in range(nh):
        x0 = sx + L * (.24 + i * .135)
        cov = [(x0, hy0), (x0 + L * .09, hy0), (x0 + L * .085, hy0 - hh * .45), (x0 + L * .005, hy0 - hh * .45)]
        cv.obj([cov], .5)
        cv.hair(C.hatch_poly(cov, 90, 1.5))
    for i in range(4):
        x0 = sx + L * (.355 + i * .135)
        post = _rect(x0 - .9, hy0 - hh * 1.6, 1.8, hh * 1.6)
        cv.obj([post], .5)
        cv.heavy([(x0, hy0 - hh * 1.5), (x0 - L * .075, hy0 - hh * 2.6)])
        cv.hair([(x0, hy0 - hh * 2.1), (x0 - L * .075, hy0 - hh * 2.6)])
        cv.line([(x0, hy0), (x0, hy0 - hh * 2.2)])
    # forecastle mast
    cv.obj([], 0)
    cv.line([(bx - L * .05, ys - hh * 1.25), (bx - L * .05, ys - hh * 2.4)])
    # accommodation block aft, bridge wings, funnel
    ax0, ax1 = sx + L * .035, sx + L * .17
    tiers = 4
    th = hh * .62
    for k in range(tiers):
        inset = L * .006 * k
        blk = _rect(ax0 + inset, hy0 - th * (k + 1), ax1 - ax0 - inset * 2, th)
        cv.obj([blk], .5)
        cv.hair(C.hatch_poly(blk, 90, 3, .5))
        # windows
        n = int((ax1 - ax0 - inset * 2) / 2.6)
        wy = hy0 - th * (k + .5)
        cv.line([[(ax0 + inset + 1.5 + j * 2.6, wy - .3), (ax0 + inset + 2.6 + j * 2.6, wy - .3)] for j in range(n)])
    wing = _rect(ax0 - L * .02, hy0 - th * tiers - 1.6, ax1 - ax0 + L * .04, 1.6)
    cv.obj([wing], .5)
    fx = ax0 + (ax1 - ax0) * .22
    fun = [(fx, hy0 - th * tiers - 1.6), (fx + L * .05, hy0 - th * tiers - 1.6), (fx + L * .045, hy0 - th * tiers - hh * 1.6),
           (fx + L * .003, hy0 - th * tiers - hh * 1.6)]
    cv.obj([fun], .5)
    cv.hair(C.hatch_poly(fun, 90, 1.5))
    band = [(fx + L * .003, hy0 - th * tiers - hh * 1.6), (fx + L * .045, hy0 - th * tiers - hh * 1.6),
            (fx + L * .046, hy0 - th * tiers - hh * 1.25), (fx + L * .002, hy0 - th * tiers - hh * 1.25)]
    cv.heavy(C.hatch_poly(band, 0, 1.2))
    if not compact:
        # radar mast, and a thread of smoke trailing aft
        mx = ax0 + (ax1 - ax0) * .7
        cv.obj([], 0)
        cv.line([(mx, hy0 - th * tiers - 1.6), (mx, hy0 - th * tiers - hh * 2.1)])
        cv.hair([(mx - 2, hy0 - th * tiers - hh * 1.8), (mx + 2, hy0 - th * tiers - hh * 1.8)])
    cv.obj([foam], 0)
    cv.hair([[(bx - L * .06 + i * 1.5, ys + .8 + i * .5), (bx + L * .04 - i * .8, ys + .8 + i * .9)] for i in range(3)])


def _pile(cv, gx, top, wl, pw, ft, level, compact):
    x0 = gx - pw / 2
    # ripples ringing the pile
    rp = []
    for i in range(3):
        rx, ry = pw * (.9 + .55 * i), 1.2 + .8 * i
        rp.append([(gx + rx * math.cos(a), wl + 1 + i * .6 + ry * math.sin(a)) for a in [math.pi * k / 18 for k in range(19)]])
    cv.obj([], 0)
    cv.hair(rp)
    pile = [(x0, top + pw * .15), (x0 + pw, top + pw * .15), (x0 + pw, wl), (x0, wl)]
    cv.obj([pile], 1)
    # cylinder: dense on the shadow side, wood grain
    for k in range(9):
        u = (k + .5) / 9
        xx = x0 + pw * u
        if u > .6:
            cv.hair([(xx, top + pw * .2), (xx, wl)])
        else:
            pts = [(xx + .35 * math.sin((yy - top) / 5 + k), yy) for yy in [top + pw * .2 + j * 3 for j in range(int((wl - top) / 3))]]
            cv.hair(_split(pts, random.Random(k), (8, 30), (1.5, 3)))
    cv.line([(x0 + pw * .82, top + pw * .2), (x0 + pw * .82, wl)])
    # the tide's wet band: the river rises and falls a foot or two with each tide
    wet = _rect(x0, wl - ft * 1.6, pw, ft * 1.6)
    cv.hair(C.hatch_poly(wet, 35, 1.5))
    # weathered top
    cap = [(gx + pw / 2 * math.cos(a), top + pw * .15 + pw * .16 * math.sin(a)) for a in [TAU * k / 24 for k in range(24)]]
    cv.obj([cap], 1)
    cv.hair([[(gx + pw / 2 * r * math.cos(a), top + pw * .15 + pw * .16 * r * math.sin(a)) for a in [TAU * k / 20 for k in range(21)]]
             for r in (.35, .7)])
    # the staff gauge: enamel plate, foot marks, tenths in E blocks, foot numerals
    bw = pw * .78
    bx = gx - bw / 2 - pw * .05
    btop = top + ft * .55
    plate = _rect(bx, btop, bw, wl - btop)
    cv.obj([plate], 1)
    f_top = level + (wl - btop) / ft
    f = math.floor(level * 5) / 5 + .2
    while f < f_top - .05:
        yy = wl - (f - level) * ft
        whole = abs(f - round(f)) < 1e-6
        half = abs(f * 2 - round(f * 2)) < 1e-6
        step = .2 if ft > 14 else .5
        if not whole and not (half and step == .5) and abs(f / step - round(f / step)) > 1e-6:
            f += .2
            continue
        if whole:
            cv.heavy([(bx, yy), (bx + bw, yy)])
            if ft > 14 and yy - ft * .38 > btop + 1:
                cv.line(_digit(str(int(round(f)) % 10), bx + bw * .55, yy - ft * .4, ft * .3))
        elif half:
            cv.heavy([(bx, yy), (bx + bw * .45, yy)])
            cv.line([(bx + .6, yy), (bx + .6, yy + ft * .2)])
        else:
            cv.line([(bx, yy), (bx + bw * .3, yy)])
        f += .2
    # the needle of today: a heavier waterline hugging the pile
    cv.obj([], 0)
    cv.heavy([(x0 - pw * .5, wl), (x0 + pw * 1.5, wl)])


def _heron(cv, fx, fy, hgt):
    """A great blue heron standing on the pile, facing left; feet at (fx, fy)."""
    s = hgt
    P = lambda pts: [(fx + x * s, fy + y * s) for x, y in pts]
    legs = [P([(.03, -.36), (.0, -.12), (-.02, 0)]), P([(.07, -.36), (.08, -.14), (.06, 0)])]
    cv.obj([], 0)
    cv.line(legs)
    cv.hair([P([(-.02, 0), (-.08, .005)]), P([(.06, 0), (.12, .004)])])
    body = P([(-.11, -.52), (-.04, -.6), (.06, -.61), (.17, -.55), (.27, -.46), (.36, -.37), (.3, -.36), (.18, -.37),
              (.08, -.35), (-.02, -.37), (-.1, -.43), (-.13, -.48)])
    cv.obj([body], 1)
    wing = P([(-.04, -.56), (.06, -.6), (.17, -.55), (.27, -.46), (.35, -.375), (.2, -.39), (.06, -.42), (-.02, -.46)])
    cv.hair(C.hatch_poly(body, -28, 1.5))
    cv.hair(C.hatch_poly(wing, 30, 3))
    cv.hair([P([(.0, -.5), (.18, -.43)]), P([(.04, -.55), (.24, -.44)])])
    # breast plumes
    cv.hair([P([(-.1 + .02 * i, -.44 + .01 * i), (-.06 + .02 * i, -.36)]) for i in range(4)])
    # neck: S curve, white with a streaked front
    spine = P([(-.08, -.52), (-.15, -.6), (-.13, -.7), (-.06, -.78), (-.07, -.86), (-.1, -.9)])
    wdt = .045 * s
    l, r = [], []
    for i, (x, y) in enumerate(spine):
        a, b = spine[max(0, i - 1)], spine[min(len(spine) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        k = 1.25 if i == 0 else 1.
        l.append((x + nx * wdt * k, y + ny * wdt * k))
        r.append((x - nx * wdt * k, y - ny * wdt * k))
    neck = l + r[::-1]
    cv.obj([neck], 1)
    cv.line([r[1:-1]])
    cv.hair([[(x + (rr[0] - x) * .45, y + (rr[1] - y) * .45), (x + (rr[0] - x) * .8, y + (rr[1] - y) * .8)]
             for (x, y), rr in zip(l[1:-1], r[1:-1])])
    head = [(fx + (-.1 + .055 * math.cos(a)) * s, fy + (-.915 + .035 * math.sin(a)) * s) for a in [TAU * k / 16 for k in range(16)]]
    cv.obj([head], 1)
    cv.heavy([P([(-.08, -.94), (.05, -.935)]), P([(-.02, -.935), (.13, -.9)])])   # black crest and plume
    beak = P([(-.15, -.925), (-.38, -.9), (-.15, -.9)])
    cv.obj([beak], 1)
    cv.hair([P([(-.15, -.912), (-.36, -.901)])])
    e = P([(-.115, -.918)])[0]
    cv.heavy([[(e[0] - .4, e[1]), (e[0] + .4, e[1])]])


def _bank(cv, X0, Y1, W, H, seed, compact):
    rng = random.Random(seed + 21)
    bh = H * (.16 if not compact else .14)
    bank = [(X0 - 2, Y1 + 2), (X0 - 2, Y1 - bh)]
    for i in range(1, 21):
        t = i / 20
        bank.append((X0 + W * .34 * t, Y1 - bh * (1 - t ** 1.6) - rng.uniform(0, 1.5)))
    bank.append((X0 + W * .34, Y1 + 2))
    cv.obj([bank], 1)
    cv.hair(C.hatch_poly(bank, 45, 1.5))
    cv.hair(C.hatch_poly(bank, -45, 3))
    # reeds and cattails rising off the bank, blades arching and folding over
    n = 26 if not compact else 12
    for i in range(n):
        t = (i + rng.uniform(0, .8)) / n
        x = X0 + W * .32 * t
        base = Y1 - bh * (1 - (t * .9) ** 1.6) + 2
        hgt = H * rng.uniform(.14, .3) * (1 - t * .45)
        bend = rng.uniform(-.5, .6)
        tip_droop = rng.random() < .35
        pts = []
        for k in range(13):
            u = k / 12
            dx = bend * hgt * .5 * u ** 2
            dy = -hgt * u
            if tip_droop and u > .7:
                dy = -hgt * .7 - hgt * .3 * math.sin((u - .7) / .3 * math.pi / 2) * .4
                dx += bend * hgt * .6 * (u - .7) + math.copysign(hgt * .25 * (u - .7), bend)
            pts.append((x + dx, base + dy))
        w = max(.9, H * .007) * (1.6 if i % 4 == 0 else 1)
        poly = [(px - w * (1 - k / 12), py) for k, (px, py) in enumerate(pts)] + \
               [(px + w * (1 - k / 12) + .2, py) for k, (px, py) in enumerate(pts)][::-1]
        cv.obj([poly], .5)
        cv.hair([pts[:10]])
        if i % 5 == 2 and not tip_droop:
            hx, hy = pts[8]
            ch = hgt * .2
            cat = [(hx - 1.7 + j % 2 * 3.4, hy - ch * (j // 2)) for j in (0, 1, 3, 2)]
            cat = [(hx - 1.2, hy), (hx + 1.2, hy), (hx + 1.3, hy - ch), (hx, hy - ch - 1.2), (hx - 1.3, hy - ch)]
            cv.obj([cat], 1)
            cv.heavy(C.hatch_poly(cat, 0, 1.5))
            cv.obj([], 0)
            cv.line([(hx, hy - ch - 1.5), (hx + bend, hy - ch - hgt * .12)])



# ---------------------------------------------------------------- engraved roman capitals (stroke paths)
def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


_CAP = {
    "A": (1.1, [[(0, 2), (.55, 0), (1.1, 2)], [(.22, 1.3), (.88, 1.3)]]),
    "B": (.9, [[(0, 0), (0, 2)], [(0, 0), (.55, 0)] + _arc(.55, .48, .32, .48, -90, 90, 8) + [(0, .96)],
               [(0, .96), (.55, .96)] + _arc(.55, 1.48, .36, .52, -90, 90, 8) + [(0, 2)]]),
    "C": (1., [_arc(.62, 1, .6, 1, -50, -310, 16)]),
    "E": (.8, [[(.8, 0), (0, 0), (0, 2), (.8, 2)], [(0, 1), (.6, 1)]]),
    "F": (.8, [[(.8, 0), (0, 0), (0, 2)], [(0, 1), (.6, 1)]]),
    "G": (1.05, [_arc(.6, 1, .6, 1, -50, -340, 16) + [(1.08, 1.1), (.65, 1.1)]]),
    "H": (1., [[(0, 0), (0, 2)], [(1, 0), (1, 2)], [(0, 1), (1, 1)]]),
    "I": (.1, [[(.05, 0), (.05, 2)]]),
    "L": (.75, [[(0, 0), (0, 2), (.75, 2)]]),
    "M": (1.3, [[(0, 2), (.08, 0), (.65, 2), (1.22, 0), (1.3, 2)]]),
    "N": (1., [[(0, 2), (0, 0), (1, 2), (1, 0)]]),
    "O": (1.2, [_arc(.6, 1, .6, 1, 0, 360, 20)]),
    "R": (.9, [[(0, 2), (0, 0), (.5, 0)] + _arc(.5, .5, .35, .5, -90, 90, 8) + [(0, 1)], [(.4, 1), (.95, 2)]]),
    "S": (.85, [_arc(.43, .5, .4, .5, -20, -270, 10) + _arc(.43, 1.5, .42, .5, -90, 160, 10)]),
    "T": (.9, [[(0, 0), (.9, 0)], [(.45, 0), (.45, 2)]]),
    "U": (1., [[(0, 0), (0, 1.45)] + _arc(.5, 1.45, .5, .55, 180, 0, 10)[1:] + [(1, 0)]]),
    "V": (1.05, [[(0, 0), (.52, 2), (1.05, 0)]]),
    "W": (1.5, [[(0, 0), (.38, 2), (.75, .4), (1.12, 2), (1.5, 0)]]),
    ".": (.2, [[(.1, 1.85), (.1, 1.95)]]),
    "\u00b7": (.2, [[(.1, .95), (.1, 1.05)]]),
}


def _letter_run(text, cx, cy, hgt, track=.42, path=None):
    """Polylines for text centred at (cx, cy), cap height hgt; optional centre line path to follow."""
    s = hgt / 2
    glyphs = []
    width = 0.
    for ch in text:
        if ch == " ":
            width += .7 * s
            glyphs.append(None)
            continue
        if ch.isdigit():
            gw, strokes = .85, _DIG[ch]
        else:
            gw, strokes = _CAP.get(ch, (.6, []))
        glyphs.append((width, gw, strokes))
        width += (gw + track) * s
    width -= track * s
    out = []
    for g in glyphs:
        if not g:
            continue
        x0, gw, strokes = g
        for st in strokes:
            pl = []
            for px, py in st:
                X = cx - width / 2 + x0 + px * s * (.85 if gw == .85 else 1)
                Y = cy - hgt / 2 + py * s
                if path:
                    Y += _path_y(path, X) - cy
                pl.append((X, Y))
            out.append(pl)
    return out, width


def _path_y(path, x):
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
    return path[0][1] if x < path[0][0] else path[-1][1]


def _tall_extras(w, h, level, rising):
    """Letter the house banner and engrave today's reading into the pedestal tablet."""
    ped_h = min(max(h * .17, 48), 86.)
    top_free = min(h * .055, 26.)
    py0 = top_free
    ph = h - top_free - ped_h + ped_h * .3
    pw = w - 12
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    bh = min(16, ph * .05)
    _, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, 0)
    cv = C.Canvas()
    cv.obj([], 0)
    letters, _ = _letter_run("THE COLUMBIA", cx, cy + ch * .47, bh * .52, .5, centre)
    cv.heavy(letters)
    _, (tx, ty, tw, th) = C.pedestal(0, h - ped_h, w, ped_h, 0)
    # the tablet: ruled ground, the reading cut in heavy capitals, a running wave either side
    tab = [(tx + 2, ty + 2), (tx + tw - .8, ty + 2), (tx + tw - .8, ty + th - .8), (tx + 2, ty + th - .8)]
    cv.obj([tab], 0)
    txt = ("VANCOUVER  %s FT  %s" % (("%.1f" % level), "RISING" if rising else "FALLING"))
    lh = min(th * .5, 9)
    letters, lw = _letter_run(txt, tx + tw / 2, ty + th / 2 + .6, lh, .5)
    cv.hair([[(x0, y), (x1, y)] for y in [ty + 3.5 + 2 * k for k in range(int((th - 4) / 2))]
             for x0, x1 in ((tx + 3, tx + tw / 2 - lw / 2 - 4), (tx + tw / 2 + lw / 2 + 4, tx + tw - 2))])
    knock = [(tx + tw / 2 - lw / 2 - 3, ty + 2.5), (tx + tw / 2 + lw / 2 + 3, ty + 2.5),
             (tx + tw / 2 + lw / 2 + 3, ty + th - 1.5), (tx + tw / 2 - lw / 2 - 3, ty + th - 1.5)]
    cv.obj([knock], .5)
    cv.heavy(letters)
    # running-dog waves on the ruled ends
    for side in (-1, 1):
        x_a = tx + 6 if side < 0 else tx + tw / 2 + lw / 2 + 7
        x_b = tx + tw / 2 - lw / 2 - 7 if side < 0 else tx + tw - 5
        P = th * 1.3
        n = int((x_b - x_a) / P)
        if n < 1:
            continue
        x_a += ((x_b - x_a) - n * P) / 2
        yb = ty + th - 3
        r0 = th * .28
        pl = []
        for i in range(n):
            ox = x_a + i * P
            ccx, ccy = ox + P * .55, ty + th * .48
            pl += [(ox + P * .05 * k / 6, yb - (yb - ccy) * (k / 6) ** 2 * 0) for k in range(1)]
            pl += [(ox + (ccx - r0 - ox) * k / 6, yb + (ccy - yb) * math.sin(k / 6 * math.pi / 2)) for k in range(7)]
            for k in range(25):
                a = math.pi + 1.4 * TAU * k / 24
                r = r0 * (1 - .7 * k / 24)
                pl.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
            spiral_end = pl[-1]
            cv.obj([], 0)
            cv.heavy([pl[-25:]])
            pl = [(ccx + r0 * .2, yb)]
        cv.line([[(x_a, yb), (x_a + n * P, yb)]])
    return cv.svg()

# ---------------------------------------------------------------- field recovery + plate
def _field_from_box(ix, iy, iw, ih, kind):
    cx, cy = ix + iw / 2, iy + ih / 2
    if kind == "band":
        rx, ry = iw / 2 / .7071 + 5, ih / 2 / .7071 + 5
        a, b = rx - 4.6, ry - 4.6
        pts = [(cx + a * math.cos(t), cy + b * math.sin(t)) for t in [TAU * k / 96 for k in range(96)]]
    else:
        a, b = (iw / 2) / _K + 6 - 4.8, (ih / 2) / _K + 6 - 4.8
        pts = C._superellipse(cx, cy, a, b)
    return cx, cy, a, b, pts


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 17 * int(ctx.get("sheet", 0) or 0)
    level = _level(ctx)
    kind = "band" if h < 110 else ("med" if h <= 260 else "tall")

    def fill(ix, iy, iw, ih):
        cx, cy, a, b, field = _field_from_box(ix, iy, iw, ih, kind)
        cv = C.Canvas()
        _scene(cv, cx - a, cy - b, 2 * a, 2 * b, level, seed, kind == "band")
        cid = C._uid("rv2", w, h, seed)
        return (f'<clipPath id="{cid}"><path d="{C._d(field, True, 0)}"/></clipPath>'
                f'<g clip-path="url(#{cid})">{cv.svg()}</g>')

    svg = C.frame_plate(w, h, seed, fill, density=.85 if kind == "tall" else 1.)
    if kind == "tall":
        smp = (ctx.get("sample", "") or "").lower()
        svg = svg[:-6] + _tall_extras(w, h, level, "falling" not in smp) + "</svg>"
    return svg
