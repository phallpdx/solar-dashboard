"""Coast ("Beach getaway") plate: a winter storm on the north Oregon coast, engraved in the house
Codex style. Inside the carved cartouche: Haystack Rock and the Needles, a southbound gray whale
lifting its flukes, a plunging breaker whose lip rolls into a volute eye, storm clouds and a low
sun, and a stippled beach. Easter egg: a trail of Parker's dog's paw prints across the sand (and
at larger sizes a great blue heron from Sauvie Island wading at the tide line)."""
import sys
import math
import random
import engraving_codex as C

_n, _d = C._n, C._d
TAU = math.tau


# ------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------

def _cr(pts, n=6, closed=False):
    """Catmull-Rom through pts."""
    P = list(pts)
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(P[-2])
    return out


def _clip_half(poly, nx, ny, c):
    """Keep the part of poly with nx*x + ny*y <= c (Sutherland-Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da, db = nx * a[0] + ny * a[1] - c, nx * b[0] + ny * b[1] - c
        if da <= 0:
            out.append(a)
        if (da < 0) != (db < 0):
            t = da / (da - db)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _wavy(x0, x1, y, amp, per, ph, step=2.):
    n = max(2, int((x1 - x0) / step))
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin((x0 + (x1 - x0) * i / n) / per * TAU + ph)) for i in range(n + 1)]


def _pip(x, y, poly):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def _inside(pl, poly):
    """Split a polyline into the runs whose points lie inside poly."""
    out, cur = [], []
    for p in pl:
        if _pip(p[0], p[1], poly):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _dots(pts, r=.05):
    """Tiny round-capped strokes that render as dots."""
    return [[(x, y), (x + r, y)] for x, y in pts]


# ------------------------------------------------------------------------------------------
# the subjects
# ------------------------------------------------------------------------------------------

def _sky(cv, X, Y, W, hy, beams):
    """Ruled sky (pitch 1.5 high up, 2 lower), with storm-light beams left white where they fall
    from the cloud base to the sea. beams: (ox, oy, [(a0, a1) angle ranges in radians])."""
    ox, oy, wedges = beams
    cv.obj([], 0)
    y = Y + .25
    out = []
    while y < hy:
        f = (y - Y) / max(1, hy - Y)
        cuts = []
        if y > oy:
            for a0, a1 in wedges:
                xa = ox + (y - oy) / math.tan(a0)
                xb = ox + (y - oy) / math.tan(a1)
                cuts.append((min(xa, xb), max(xa, xb)))
        cuts.sort()
        x = X
        for c0, c1 in cuts:
            if c0 > x + 1:
                out.append([(x, y), (c0, y)])
            x = max(x, c1)
        if X + W > x + 1:
            out.append([(x, y), (X + W, y)])
        y += 1.5 if f < .3 else 2.
    cv.hair(out)


def _cloud(cv, cx, cy, w, h, rng, dark=1.):
    """A cumulus storm cloud as a pile of billows, back rows first: each billow outlined, ruled
    light (pitch 3) on its lit upper left, dark (pitch 1.5) on its lower right, the pile cut flat
    and dark along the base."""
    rows = 3 if h > 14 else 2
    bil = []
    for r in range(rows):
        f = r / max(1, rows - 1)
        n = 2 + r + (1 if w > 60 else 0)
        rw = w * (.55 + .45 * f)
        for i in range(n):
            u = (i + .5) / n
            x = cx - rw / 2 + rw * u + (rng.random() - .5) * rw / n * .3
            rr = rw / n * (.62 + .2 * rng.random())
            y = cy - h * (.62 - .42 * f) - (math.sin(math.pi * u) * h * .12 if r == 0 else 0)
            bil.append((x, y, rr, min(rr * .78, h * .42)))
    for x, y, rx, ry in bil:
        e = C._ell_pts(x, y, rx, ry, 28)
        e = _clip_half(e, 0, 1, cy)
        if len(e) < 3:
            continue
        cv.obj([e], .5)
        lit = _clip_half(e, 1, 1, x + y + rx * .1)
        sh = _clip_half(e, -1, -1, -(x + y + rx * .1))
        cv.hair(C.hatch_poly(lit, 0, 3, .25))
        if len(sh) > 2:
            cv.hair(C.hatch_poly(sh, 0, 1.5, .25))
            cv.hair(C.hatch_poly(_clip_half(sh, -1, -1, -(x + y + rx * .7)), 45, 3, .25))
    base = [(cx - w * .5 + w * i / 20, cy - 1.2 - .6 * math.sin(i * 1.7)) for i in range(21)]
    cv.obj([], 0)
    cv.line(base)


def _rock(cv, cx, by, H, W):
    """Haystack Rock and the Needles, base centre (cx, by)."""
    prof = [(-.5, 0), (-.47, -.1), (-.45, -.25), (-.42, -.42), (-.37, -.6), (-.3, -.76), (-.2, -.9), (-.08, -.98),
            (.04, -1.), (.14, -.97), (.24, -.88), (.31, -.76), (.36, -.6), (.4, -.42), (.43, -.26), (.47, -.12), (.52, 0)]
    poly = [(cx + x * W, by + y * H) for x, y in prof]
    poly = _cr(poly, 3)
    # the needles behind/right of it
    nd = []
    for off, hh, ww in ((.62, .44, .1), (.78, .28, .07)):
        x = cx + off * W
        nd.append([(x - ww * W, by), (x - ww * W * .55, by - hh * H * .6), (x - ww * W * .15, by - hh * H),
                   (x + ww * W * .3, by - hh * H * .93), (x + ww * W * .7, by - hh * H * .4), (x + ww * W, by)])
    cv.obj(nd, 1.)
    for p in nd:
        cv.hair(C.hatch_poly(p, 90, 1.5, .25))
    cv.obj([poly], 1.)
    top_i = min(range(len(poly)), key=lambda i: poly[i][1])
    left = poly[:top_i + 1]
    right = poly[top_i:][::-1]

    def edge(pl, v):
        yy = by - v * H
        for i in range(len(pl) - 1):
            (x0, y0), (x1, y1) = pl[i], pl[i + 1]
            if (y0 - yy) * (y1 - yy) <= 0 and y0 != y1:
                return x0 + (x1 - x0) * (yy - y0) / (y1 - y0)
        return pl[-1][0]
    ns = max(6, int(W / 2.))
    for k in range(1, ns):
        s = (k / ns) ** .75
        pl = []
        for j in range(31):
            v = .985 * j / 30
            xl, xr = edge(left, v), edge(right, v)
            pl.append((xl + (xr - xl) * s, by - v * H))
        if s < .3 and k % 2:
            pl = pl[:14]
        cv.hair(pl)
    shade = _clip_half(poly, -1, 0, -(cx + W * .12))
    if len(shade) > 2:
        cv.hair(C.hatch_poly(shade, 30, 3, .25))
    deep = _clip_half(poly, -1, 0, -(cx + W * .3))
    if len(deep) > 2:
        cv.hair(C.hatch_poly(deep, -30, 3, .25))
    # the vegetated cap: stipple across the summit
    rng = random.Random(7)
    dots = []
    for _ in range(int(W * 1.4)):
        x = cx - W * .25 + W * .5 * rng.random()
        v = .82 + .17 * rng.random() * (1 - abs(x - cx - W * .03) / (W * .3))
        y = by - v * H
        xl, xr = edge(left, v), edge(right, v)
        if xl + 1 < x < xr - 1:
            dots.append((x, y))
    cv.line(_dots(dots))
    # surf breaking white round its foot: a heavy wash line and spray
    wash = [(cx - W * .56 + W * 1.12 * i / 30, by - 1 - 1.2 * abs(math.sin(i * 1.3))) for i in range(31)]
    cv.obj([], 0)
    cv.line(wash)
    return poly


def _gulls(cv, pts, s):
    cv.obj([], 0)
    for x, y in pts:
        cv.line(_cr([(x - s, y - s * .2), (x - s * .5, y - s * .6), (x, y)], 3))
        cv.line(_cr([(x, y), (x + s * .5, y - s * .6), (x + s, y - s * .2)], 3))


def _fluke(cv, fx, fy, L, big):
    """A gray whale's flukes rising from the sea at (fx, fy), height L."""
    U = [(-.12, .04), (-.1, -.25), (-.08, -.48), (-.18, -.64), (-.4, -.78), (-.64, -.9), (-.84, -1.02),
         (-.72, -1.04), (-.5, -1.), (-.3, -.92), (-.12, -.86), (0, -.77),
         (.12, -.87), (.32, -.95), (.54, -1.03), (.76, -1.09), (.87, -1.06), (.7, -.94), (.46, -.8),
         (.22, -.66), (.08, -.48), (.1, -.25), (.12, .04)]
    pts = _cr([(fx + x * L, fy + y * L) for x, y in U], 5, True)
    cv.obj([pts], 1.)
    # contour lines running up the stalk and fanning into each lobe
    for k in range(-7, 8):
        s = k / 7.
        pl = []
        for j in range(21):
            t = j / 20
            yy = fy + .02 * L - t * .8 * L
            g = max(0., (t - .55) / .45)
            spread = .095 + .75 * g ** 1.3
            pl.append((fx + s * L * spread, yy - abs(s) * .25 * L * g + (s * .05 * L * g if s > 0 else 0)))
        cv.hair(pl if k >= -3 else pl[9:])
    # deep shadow down the right side of the stalk and under the right lobe
    st = [(fx + .01 * L, fy + .04 * L), (fx + .13 * L, fy + .04 * L), (fx + .11 * L, fy - .25 * L),
          (fx + .1 * L, fy - .5 * L), (fx + .02 * L, fy - .5 * L)]
    cv.hair(C.hatch_poly(st, 90, 1.5, .25))
    lob = [(fx + .08 * L, fy - .48 * L), (fx + .46 * L, fy - .8 * L), (fx + .7 * L, fy - .94 * L),
           (fx + .87 * L, fy - 1.06 * L), (fx + .5 * L, fy - .88 * L), (fx + .12 * L, fy - .6 * L)]
    cv.hair(C.hatch_poly(lob, -45, 2, .25))
    rng = random.Random(3)
    for _ in range(10 if big else 5):
        x = fx + (rng.random() - .5) * .9 * L
        y = fy - (.8 + rng.random() * .12) * L - abs(x - fx) * .2
        r = .02 * L + .4
        cv.hair(C._ell_pts(x, y, r, r, 8))
    # water streaming off the trailing edge
    cv.obj([], 0)
    for k in range(-6, 7):
        if abs(k) < 1:
            continue
        x = fx + k * .12 * L
        ytop = fy - (.98 + abs(k) * .01) * L + .08 * L
        for j in range(2 if big else 1):
            y = ytop + j * .2 * L + (abs(k) % 2) * .07 * L
            if y < fy - .05 * L:
                cv.line([(x, y), (x, y + .03 * L)])
    for side in (-1, 1):
        for j in range(3):
            r = .2 * L + j * .12 * L
            cv.hair([(fx + side * r * math.cos(a), fy + .04 * L - .07 * L * math.sin(a)) for a in [k * .3 for k in range(6)]])


def _breaker(cv, cx, cy, R, sea_y, x_left, rng, big):
    """A plunging breaker travelling right: its back rises from the left, the lip throws forward and
    rolls into a tight volute eye over a dark barrel. Returns the eye (x, y, r)."""
    KD = .2
    th0, th1 = math.pi * .8, math.pi + 1.62 * math.pi
    T = R * .42

    def ro(t):
        return R * math.exp(-KD * (t - th0))

    def thick(t):
        return T * max(0.03, (1 - (t - th0) / (th1 - th0))) ** .85

    def P(t, r):
        return (cx + r * math.cos(t), cy + r * math.sin(t))
    N = 80
    ts = [th0 + (th1 - th0) * i / N for i in range(N + 1)]
    outer = [P(t, ro(t)) for t in ts]
    inner = [P(t, ro(t) - thick(t)) for t in ts]
    tip = inner[-1]
    # the water mass: the back rising from the left, the face falling to the lip's landing, the
    # white water spreading to the right where the lip has crashed
    face = _cr([inner[0], (cx - R * .66, cy + R * .45), (cx - R * .45, cy + R * .85), (cx - R * .2, sea_y)], 8)
    back = _cr([(x_left - R, sea_y - R * .05), (x_left + (outer[0][0] - x_left) * .5, cy + R * .75),
                (outer[0][0] - R * .1, outer[0][1] + R * .12), outer[0]], 8)
    body = back + [inner[0]] + face[1:] + [(cx - R * .2, sea_y + R * .5), (x_left - R, sea_y + R * .5)]
    cv.obj([body], 1.)
    # swell contours: rules that ride up the back and the face, conforming to the wave's height
    xs0 = min(p[0] for p in body)
    xs1 = max(p[0] for p in body)

    def top(x):
        ys = []
        n = len(body)
        for i in range(n):
            (x0, y0), (x1, y1) = body[i], body[(i + 1) % n]
            if (x0 - x) * (x1 - x) <= 0 and x0 != x1:
                ys.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
        return min(ys) if ys else sea_y
    tops = [(x, top(x)) for x in [xs0 + i * 1.5 for i in range(int((xs1 - xs0) / 1.5) + 1)]]
    hmax = max(sea_y - t for _, t in tops)
    nl = int(hmax / 2)
    for j in range(1, nl):
        f = j / nl
        need = 1.5 if j % 2 else (.75 if j % 4 else 0.)
        runs, cur = [], []
        for x, t in tops:
            if sea_y - t > 1 and (sea_y - t) / nl >= need:
                cur.append((x, sea_y - f * (sea_y - t) + .25))
            else:
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
        if len(cur) > 1:
            runs.append(cur)
        for r_ in runs:
            cv.hair(_inside(r_, body))
    # barrel: the dark tube inside the curl, open to the flat water ahead
    barrel = inner + [(tip[0] + R * .25, cy + R * .7), (tip[0] + R * .3, sea_y)] + face[::-1]
    cv.obj([barrel], 0)
    for j in range(int(R * 1.05 / 1.5)):
        r = R * .12 + j * 1.5
        cv.hair(_inside([P(t, r) for t in [-.4 + i * .05 for i in range(int(6.8 / .05))]], barrel))
    cv.hair(C.hatch_poly(barrel, 60, 3, .25))
    # white water where the lip lands: a scalloped foam heap, stippled
    fx0, fx1 = tip[0] - R * .3, tip[0] + R * 1.5
    soup = []
    nb_ = 9
    for b_ in range(nb_):
        u0 = b_ / nb_
        bx = fx0 + (fx1 - fx0) * (u0 + .5 / nb_)
        hgt = R * .3 * math.sin(math.pi * (u0 + .5 / nb_)) ** .6 * (1 - .4 * u0)
        br = (fx1 - fx0) / nb_ / 2
        for kk in range(4 if b_ < nb_ - 1 else 5):
            a = math.pi + math.pi * kk / 4
            soup.append((bx + br * math.cos(a), sea_y - hgt + br * .9 * math.sin(a)))
    soup = [(fx0, sea_y)] + soup
    cv.obj([soup + [(fx1, sea_y + 1), (fx0, sea_y + 1)]], 0)
    sp = []
    for _ in range(int(R * 5)):
        x = fx0 + rng.random() * (fx1 - fx0)
        i = min(len(soup) - 1, max(0, int((x - fx0) / (fx1 - fx0) * (len(soup) - 1))))
        y = soup[i][1] + 2 + rng.random() * (sea_y - soup[i][1])
        sp.append((x, y))
    cv.line(_dots(sp))
    cv.hair(soup)
    cv.hair([[(fx0 + (fx1 - fx0) * (.1 + .8 * rng.random()), sea_y - j * 2 - .75)] for j in range(0)])
    # the curling lip: a tapering band, lined along its length, dark toward the inside
    band = outer + inner[::-1]
    cv.obj([band], 0)
    cv.line(outer[1:])
    cv.line(inner[6:])
    nb = max(4, int(T / 1.5))
    for i in range(1, nb):
        f = i / nb
        pl = [P(t, ro(t) - thick(t) * f) for t in ts if thick(t) * (1 - f) > .6]
        if f > .3:
            cv.hair(pl)
        else:
            cv.hair(pl[:max(2, int(len(pl) * f * 2.2))])
    # foam claws along the lip: acanthus fingers curling forward (the house leaf becomes spume)
    # foam claws: fingers that reach forward off the lip and curl over (Hokusai's claws)
    claws = []
    nc = 7 if big else 5
    for i in range(nc):
        t = math.pi + .3 + i * 1.35 / nc
        L = R * (.3 - .12 * i / nc)
        x, y = P(t, ro(t) - .5)
        hd = t - .25
        pl = [(x, y)]
        m = 16
        for j in range(m):
            hd += (j / m) ** 1.6 * .55
            x += L / m * math.cos(hd)
            y += L / m * math.sin(hd)
            pl.append((x, y))
        claws.append(pl)
    shapes = []
    for pl in claws:
        # a tapering white finger around the centre line
        l_, r_ = [], []
        for j in range(1, len(pl)):
            (x0, y0), (x1, y1) = pl[j - 1], pl[j]
            a = math.atan2(y1 - y0, x1 - x0)
            wdt = R * .055 * (1 - j / len(pl)) + .3
            l_.append((x1 - math.sin(a) * wdt, y1 + math.cos(a) * wdt))
            r_.append((x1 + math.sin(a) * wdt, y1 - math.cos(a) * wdt))
        shapes.append([pl[0]] + l_ + r_[::-1])
    cv.obj(shapes, 1.)
    for pl in claws:
        cv.hair([(x + .6, y + .6) for x, y in pl[2:-3]])
    sp = []
    for _ in range(int(R * 2)):
        t = math.pi + .2 + rng.random() * 1.8
        sp.append(P(t, ro(t) + 1.5 + rng.random() ** 2 * R * .35))
    cv.obj([], 0)
    cv.line(_dots(sp))
    return (cx + R * .05, cy + R * .1, max(1.2, R * .2))


def _sea(cv, X, W, hy, by, glints):
    """Ruled sea: wavy rules widening toward the shore, broken into glitter under the sun."""
    cv.obj([], 0)
    y = hy + .75
    i = 0
    while y < by:
        f = (y - hy) / max(1., by - hy)
        amp = .2 + f * 1.
        per = 10 + f * 22
        pl = _wavy(X, X + W, y, amp, per, i * 1.7)
        gw = 3 + f * 18
        seg, out = [], []
        for p in pl:
            if False:
                if len(seg) > 1:
                    out.append(seg)
                seg = []
            else:
                seg.append(p)
        if len(seg) > 1:
            out.append(seg)
        cv.hair(out)
        y += 1.5 if f < .35 else 2. if f < .7 else 3.
        i += 1


def _beach(cv, X, W, by, Y1, rng):
    """Sand: a foam scallop at the tide line, ruled and stippled sand."""
    poly = [(X - 2, by)]
    for i in range(41):
        poly.append((X + W * i / 40, by + .8 * math.sin(i * .9)))
    poly += [(X + W + 2, Y1 + 2), (X - 2, Y1 + 2)]
    cv.obj([poly], 1.)
    sc = []
    for i in range(int(W / 6)):
        x = X + i * 6 + rng.random() * 2
        sc.append([(x + 2.6 * math.cos(a), by + 1.2 + 1.2 * math.sin(a)) for a in [math.pi * k / 6 for k in range(7)]])
    cv.hair(sc)
    cv.hair(C.hatch_poly([(X - 2, by + 3.5), (X + W + 2, by + 3.5), (X + W + 2, Y1 + 2), (X - 2, Y1 + 2)], 0, 2, .25))
    dots = [(X + rng.random() * W, by + 3 + rng.random() * (Y1 - by - 2)) for _ in range(int(W * (Y1 - by) / 14))]
    cv.line(_dots(dots, .05))


def _paws(cx, cy, s, n, ang=-6):
    """The dog's paw-print trail (black pads on white sand), s = print size."""
    d = []
    a = math.radians(ang)
    for i in range(n):
        x = cx + i * s * 2.6 * math.cos(a)
        y = cy + i * s * 2.6 * math.sin(a) + (s * .8 if i % 2 else 0)
        d.append(_d(C._ell_pts(x, y, s * .45, s * .36, 10), True, 0))
        for tx, ty in ((-.5, -.5), (-.18, -.8), (.18, -.8), (.5, -.5)):
            d.append(_d(C._ell_pts(x + tx * s, y + ty * s, s * .15, s * .19, 6), True, 0))
    rects = []
    for i in range(n):
        x = cx + i * s * 2.6 * math.cos(a)
        y = cy + i * s * 2.6 * math.sin(a) + (s * .8 if i % 2 else 0)
        rects.append(_d(C._ell_pts(x, y - s * .25, s * 1.0, s * .8, 12), True, 0))
    return (f'<path d="{"".join(rects)}" fill="#fff" stroke="none"/>'
            f'<path d="{"".join(d)}" fill="#000" stroke="none"/>')


def _heron(x, y, s):
    """A great blue heron wading (Sauvie Island's bird), s = height."""
    body = _cr([(x - .4 * s, y - .48 * s), (x - .1 * s, y - .62 * s), (x + .14 * s, y - .6 * s),
                (x + .18 * s, y - .5 * s), (x - .05 * s, y - .42 * s), (x - .42 * s, y - .44 * s)], 5, True)
    neck = _cr([(x + .12 * s, y - .58 * s), (x + .22 * s, y - .74 * s), (x + .1 * s, y - .86 * s),
                (x + .16 * s, y - .98 * s), (x + .26 * s, y - 1. * s)], 4)
    bill = [(x + .26 * s, y - 1. * s), (x + .5 * s, y - .95 * s)]
    plume = [(x + .16 * s, y - .99 * s), (x - .02 * s, y - .97 * s)]
    legs = [[(x - .02 * s, y - .44 * s), (x - .05 * s, y)], [(x + .05 * s, y - .44 * s), (x + .11 * s, y - .02 * s)]]
    halo = _d(C._ell_pts(x, y - .5 * s, .62 * s, .56 * s, 16), True, 0)
    return (f'<path d="{_d(body, True, .05)}" fill="#000"/>'
            f'<path d="{_d(neck, tol=.05)}" stroke="#000" stroke-width="1" fill="none"/>'
            f'<path d="{_d(bill, tol=0)}{_d(plume, tol=0)}{"".join(_d(l, tol=0) for l in legs)}" stroke="#000" stroke-width=".5" fill="none"/>')


def scene(X, Y, W, H, seed, field_d=None):
    """The coast vignette filling X..X+W, Y..Y+H, clipped to field_d. Returns svg."""
    rng = random.Random(seed)
    big = H > 90
    g = 1.25 if W / H > 1.9 else 1.
    hy = Y + H * (.52 if g == 1 else .46)
    by = Y + H * .8
    o = []
    cv = C.Canvas()
    ox, oy = X + W * .68, Y + H * .3
    wedges = [(1.72, 1.8), (1.9, 2.02), (2.15, 2.22), (1.5, 1.56)]
    _sky(cv, X, Y, W, hy, (ox, oy, wedges))
    glints = [ox + (hy - oy) / math.tan((a0 + a1) / 2) for a0, a1 in wedges[:3]]
    if big:
        _cloud(cv, X + W * .47, Y + H * .2, W * .26, H * .12, rng, .7)
    _cloud(cv, X + W * .8, Y + H * .32, W * .44, H * .24, rng)
    _cloud(cv, X + W * .2, Y + H * .27, W * .4, H * .2, rng)
    gs = max(1.8, H * .022)
    _gulls(cv, [(X + W * .55, Y + H * .33), (X + W * .59, Y + H * .29), (X + W * .51, Y + H * .27)], gs)
    _sea(cv, X, W, hy, by + 1, glints)
    _rock(cv, X + W * .74, hy + H * .18 * g, H * .4 * g, min(W * .27, H * .55 * g))
    _fluke(cv, X + W * .5, hy + H * .1 * g, H * .25 * g, big)
    R = H * .21 * g
    eye = _breaker(cv, X + W * (.25 if g == 1 else .2), hy + H * .03, R, by + 1, X, rng, big)
    _beach(cv, X, W, by + 2, Y + H, rng)
    o.append(cv.svg())
    ex, ey, er = eye
    o.append(f'<path d="{_d(C._ell_pts(ex, ey, er, er, 12), True, 0)}" fill="#000"/>')
    s = max(2.4, H * .032)
    o.append(_paws(X + W * .44, by + 2 + (Y + H - by) * .5, s, 6 if W > 140 else 4))
    if big:
        o.append(_heron(X + W * .8, by + 2 + (Y + H - by) * .45, H * .11))
    body = "".join(o)
    if field_d:
        cid = C._uid("coastf", X, Y, W, H, seed)
        body = f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
    return body


# ------------------------------------------------------------------------------------------
# layouts: the house layouts, with the vignette clipped to the whole field so no white survives
# ------------------------------------------------------------------------------------------

def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _bead_ring(cx, cy, w, h):
    """Re-strike the cartouche's sunk fillet and bead row over the scene edge."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    inner = C._superellipse(cx, cy, a, b)
    sunk = _d(C._superellipse(cx, cy, a + bw * .26, b + bw * .26), True, .1) + _d(inner[::-1], True, .1)
    return (f'<path d="{sunk}" fill="#000" stroke="none" fill-rule="evenodd"/>'
            f'<path d="{_d(inner, True, .1)}" fill="none" stroke="#000" stroke-width="1"/>')


def _band(w, h, seed):
    K = C
    o = []
    top = 7.
    o.append(K.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(K.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.3, 160)
    o.append(K._clip(K._uid("b", w, h, seed), 0, top, w, gh,
                     K.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(K._medallion(cx, cy, rx, ry))
    fr = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(scene(cx - rx * .92, cy - ry, 2 * rx * .92, 2 * ry, seed, fr))
    o.append(f'<path d="{fr}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _medium(w, h, seed):
    K = C
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(K.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(K.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .48, gh * 2.4)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = K.Canvas()
    main = K.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        K._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    K.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(K._clip(K._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = K.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, cw, gh + 4)
    o.append(scene(fx, fy, fw, fh, seed, fd))
    o.append(_bead_ring(cx, cy, cw, gh + 4))
    o.append(K.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tide_tablet(tx, ty, tw, th, seed):
    """The pedestal's sunk tablet engraved with the day's tide curve (two highs, two lows) over
    hour ticks, the water under it ruled dark, a sun and moon marking day and night."""
    x0, x1 = tx + 4, tx + tw - 3
    y0, y1 = ty + 3, ty + th - 1.5
    hh = y1 - y0
    ph = (seed % 24) / 24 * TAU
    curve = [(x0 + (x1 - x0) * i / 120, y0 + hh * (.5 + .3 * math.sin(i / 120 * TAU * 1.93 + ph) + .06 * math.sin(i / 120 * TAU * .97)))
             for i in range(121)]
    o = []
    air = [(x0, y0)] + [(x1, y0)] + curve[::-1]
    o.append(f'<path d="{C.hatch_d(air, 0, 3, .25)}" stroke="#000" stroke-width=".5" fill="none" shape-rendering="crispEdges"/>')
    water = curve + [(x1, y1), (x0, y1)]
    o.append(f'<path d="{C.hatch_d(water, 0, 1.5, .25)}" stroke="#000" stroke-width=".5" fill="none" shape-rendering="crispEdges"/>')
    o.append(f'<path d="{_d(curve, tol=.1)}" stroke="#000" stroke-width="1.5" fill="none"/>')
    ticks = "".join(f"M{_n(x0 + (x1 - x0) * i / 24)},{_n(y1)}v{-2 if i % 6 else -4}" for i in range(25))
    o.append(f'<path d="{ticks}" stroke="#000" stroke-width="1" fill="none"/>')
    # highs and lows: white beads on the curve
    ext = []
    for i in range(1, 120):
        if (curve[i][1] - curve[i - 1][1]) * (curve[i + 1][1] - curve[i][1]) < 0:
            ext.append(curve[i])
    r = max(1.5, hh * .1)
    o.append(f'<path d="{"".join(_d(C._ell_pts(x, y, r, r, 10), True, 0) for x, y in ext)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _wave_ribbon(centre, h):
    """A running wave scroll along the ribbon face: crests rising from the left and curling over
    into white volute eyes, the water under them ruled dark."""
    xs = [p[0] for p in centre]
    x0, x1 = min(xs) + h * .5, max(xs) - h * .5

    def cy(x):
        for i in range(len(centre) - 1):
            if centre[i][0] <= x <= centre[i + 1][0]:
                t = (x - centre[i][0]) / max(1e-6, centre[i + 1][0] - centre[i][0])
                return centre[i][1] + (centre[i + 1][1] - centre[i][1]) * t
        return centre[-1][1]
    per = h * 1.9
    n = max(3, int((x1 - x0) / per))
    per = (x1 - x0) / n
    A = h * .5
    top, curls = [], []
    for k in range(n):
        ux = x0 + k * per
        for j in range(13):
            t = j / 12
            x = ux + per * .7 * t
            top.append((x, cy(x) + h * .3 - A * t ** 1.6))
        ex, ey = ux + per * .78, cy(ux + per * .78) + h * .3 - A * .55
        curls.append((ex, ey))
        for j in range(5):
            t = j / 4
            x = ux + per * (.7 + .3 * t)
            top.append((x, cy(x) + h * .3 - A * (1 - t) ** .7))
    bot = [(x, cy(x) + h * .4) for x in (x1, x0)]
    water = top + bot
    o = [f'<path d="{C.hatch_d(water, 0, 1.5, .25)}" stroke="#000" stroke-width=".5" fill="none"/>',
         f'<path d="{_d(top, tol=.1)}" stroke="#000" stroke-width="1" fill="none"/>']
    r = A * .3
    disc = "".join(_d(C._ell_pts(x, y, r, r, 14), True, 0) for x, y in curls)
    o.append(f'<path d="{disc}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    sp = "".join(_d([(x + r * (1 - .75 * j / 16) * math.cos(-math.pi / 2 + j * .5), y + r * (1 - .75 * j / 16) * math.sin(-math.pi / 2 + j * .5))
                     for j in range(17)], tol=.05) for x, y in curls)
    o.append(f'<path d="{sp}" stroke="#000" stroke-width="1" fill="none"/>')
    return "".join(o)


def _tall(w, h, seed):
    K = C
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
    o.append(K.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .52, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = K.Canvas()
    main = K.Canvas()
    r1 = min(pw * .16, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        K._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        K._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    K.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=5, edge=.6, cv=cv)
    cv.extend(main)
    o.append(K._clip(K._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = K.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, cw, ch)
    o.append(scene(fx, fy, fw, fh, seed, fd))
    o.append(_bead_ring(cx, cy, cw, ch))
    o.append(K.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, cen = K.ribbon_banner(cx, cy + ch * .47, cw * 1.3, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_wave_ribbon(cen, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, tab = K.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tide_tablet(*tab, seed))
    fy2 = py + ped_h
    fh2 = h - fy2
    if fh2 > 14:
        o.append(K.dark_ground((w * .06, fy2, w * .88, fh2 - 2), "G"))
        o.append(K._clip(K._uid("f", w, h, seed), w * .06, fy2, w * .88, fh2 - 2,
                         K.scroll_band(w * .06, fy2, w * .88, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(K.palmette(w / 2, fy2 + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 11
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
