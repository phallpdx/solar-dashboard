"""civics-01 "Who speaks for you": the U.S. Capitol, seat of Oregon's delegation, engraved in the
house Codex style. The dome rises on its peristyle over the Senate and House wings, the Senate
flag flying; the Reflecting Pool holds the dome's image; behind it all, Mt. Hood (Parker's egg:
Oregon's mountain standing behind the people who speak for him), and at the pool's edge a Sauvie
Island heron on tall plates. Short: a scroll frieze round an oval Capitol medallion. Medium: a
cartouche with volutes flowing to both ends. Tall: crest, cartouche between volute pairs, ribbon
banner, pedestal."""
import sys
import math
import random
import engraving_codex as C

_n, _d = C._n, C._d


# ----------------------------------------------------------------------------------------------
# small drawing helpers
# ----------------------------------------------------------------------------------------------

def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def black(cv, poly):
    """A solid black mass of 1 px lines laid 0.8 px apart."""
    cv.line(C.hatch_poly(poly, 0, .8))


def hlines(x0, x1, y0, y1, pitch, phase=0.):
    out = []
    y = y0 + phase
    while y <= y1 + 1e-6:
        out.append([(x0, y), (x1, y)])
        y += pitch
    return out


def ell(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def _sky(cv, X, Y, W, H, yb):
    cv.obj([R(X - 2, Y - 2, X + W + 2, yb + 1)], 0)
    split = Y + (yb - Y) * .42
    # 1.5 px hair rules high up (deep sky), every other one lower down (paler toward the horizon)
    y = Y - 2
    k = 0
    while y < yb:
        if y < split or k % 2 == 0:
            cv.hair([(X - 2, y), (X + W + 2, y)])
        y += 1.5
        k += 1


def _hood(cv, cx, yb, u, rng, X, W):
    """Mt. Hood, behind and left of the dome: a white snow cone with gullies and a shaded east
    face standing over dark forested foothills."""
    px, py = cx - .62 * u, yb - .8 * u
    L = [(cx - 1.7 * u, yb), (cx - 1.4 * u, yb - .12 * u), (cx - 1.1 * u, yb - .3 * u), (cx - .9 * u, yb - .5 * u),
         (cx - .76 * u, yb - .66 * u), (cx - .68 * u, yb - .75 * u), (cx - .645 * u, yb - .79 * u), (px, py),
         (cx - .6 * u, yb - .785 * u), (cx - .57 * u, yb - .77 * u), (cx - .5 * u, yb - .7 * u),
         (cx - .38 * u, yb - .55 * u), (cx - .2 * u, yb - .38 * u), (cx + .05 * u, yb - .2 * u), (cx + .4 * u, yb)]
    cv.obj([L], 1.)
    # the whole cone ruled dark (rock and timber), the east face crossed
    cv.hair(C.hatch_poly(L, 75, 1.5))
    cv.hair(C.hatch_poly([(px, py)] + [p for p in L if p[0] > px] + [(px - .05 * u, yb)], -30, 2, .5))

    def ridge_y(x):
        for (ax, ay), (bx, by) in zip(L, L[1:]):
            if ax <= x <= bx:
                return ay + (by - ay) * (x - ax) / (bx - ax)
        return yb
    # the snowfield: summit down to a ragged snow line, white, laid over the rock
    n = 30
    x0, x1 = cx - 1.02 * u, cx - .2 * u
    sl = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        tip = .1 * u if i % 4 == 2 else (.045 * u if i % 4 in (1, 3) else 0)
        y = yb - .4 * u + tip + .02 * u * math.sin(i * 1.7)
        sl.append((x, max(y, ridge_y(x) + .3)))
    snow = [p for p in L if x0 < p[0] < x1] 
    snow = [(x0, ridge_y(x0))] + snow + [(x1, ridge_y(x1))] + sl[::-1]
    cv.obj([snow], .5)
    # gullies fanning from the summit, close-set on the east (shade) side
    ng = max(9, int(u * .42 / 4))
    for i in range(-ng, int(ng * 1.4)):
        t = i / ng
        pts = []
        for j in range(16):
            s = j / 15
            x = px + t * s * .42 * u + math.sin(s * 6 + i * 1.7) * .008 * u
            y = py + .015 * u + s * .42 * u
            if y > ridge_y(x) + .8:
                pts.append((x, y))
        if len(pts) > 1:
            cv.hair(pts)
    cv.hair(C.hatch_poly([(px, py + 1), (cx - .38 * u, yb - .55 * u), (cx - .3 * u, yb - .38 * u), (px + .12 * u, yb - .38 * u)], -60, 2))
    # dark timber line along the foot
    cv.line(C.hatch_poly([(cx - 1.7 * u, yb), (cx - 1.3 * u, yb - .1 * u), (cx - .9 * u, yb - .13 * u), (cx - .4 * u, yb - .1 * u), (cx + .4 * u, yb)], 90, 2))


def _hills(cv, cx, yb, u, X, W):
    """Low Coast-Range hills to the right, ruled."""
    pts = [(cx + .3 * u, yb)]
    for i in range(31):
        x = cx + .3 * u + (X + W + 4 - cx - .3 * u) * i / 30
        pts.append((x, yb - .13 * u - .05 * u * math.sin(i * .45) - .03 * u * math.sin(i * 1.3)))
    pts.append((X + W + 4, yb))
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, 20, 2))
    cv.hair(C.hatch_poly(pts, -40, 3))


def _drum_and_dome(cv, cx, yb, u):
    big = u > 70
    # drum base (the octagonal attic over the old building)
    b0 = R(cx - .27 * u, yb - .37 * u, cx + .27 * u, yb - .29 * u)
    cv.obj([b0], 1.)
    cv.hair(hlines(cx - .27 * u, cx + .27 * u, yb - .37 * u + 1.5, yb - .29 * u, 2))
    cv.hair(C.hatch_poly(R(cx + .1 * u, yb - .37 * u, cx + .27 * u, yb - .29 * u), 90, 1.5))
    # peristyle: recessed wall in deep cylindrical shade, columns standing in front
    r = .235 * u
    y0, y1 = yb - .55 * u, yb - .37 * u
    wall = R(cx - r, y0, cx + r, y1)
    cv.obj([wall], 1.)
    black(cv, R(cx - r, y0 + 1, cx + r, y1))
    ncol = max(10, min(26, int(2 * math.pi * r / 3.4) // 2 * 2))
    cols = []
    for i in range(ncol):
        th = math.pi * (i + .5) / (ncol / 2)
        if th >= math.pi:
            break
        x = cx - r * math.cos(th)
        cw = min(max(.9, r * .085 * math.sin(th)), 2 * math.pi * r / ncol * .45 * math.sin(th) + .3)
        cols.append((x, cw))
    for x, cw in cols:
        cv.obj([R(x - cw / 2, y0 + 1.5, x + cw / 2, y1)], .5 if cw > 1.6 else 0)
        if x > cx + r * .15 and cw > 1.4:
            cv.hair([(x + cw * .15, y0 + 1.5), (x + cw * .15, y1)])
    # entablature + balustrade over the columns
    ent = R(cx - r - .01 * u, y0 - .045 * u, cx + r + .01 * u, y0 + 1.5)
    cv.obj([ent], 1.)
    cv.hair(hlines(cx - r, cx + r, y0 - .045 * u + 1.5, y0 + 1, 2))
    # attic with windows
    a = .2 * u
    ay0 = yb - .66 * u
    att = R(cx - a, ay0, cx + a, y0 - .045 * u)
    cv.obj([att], 1.)
    for i in range(1, 12):
        th = math.pi * i / 12
        x = cx - a * math.cos(th)
        cv.line([(x, ay0 + .025 * u), (x, y0 - .07 * u)]) if big else cv.hair([(x, ay0 + 1.5), (x, y0 - .055 * u)])
    cv.hair(C.hatch_poly(R(cx + a * .45, ay0, cx + a, y0 - .045 * u), 90, 1.5, .5))
    # dome
    rx, ry = .2 * u, .25 * u
    dy = ay0
    outline = ell(cx, dy, rx, ry, math.pi, 2 * math.pi, 40)
    dome = outline + [(cx + rx, dy + 1), (cx - rx, dy + 1)]
    cv.obj([dome], 1.)

    def meridian(sx, t0=.0, t1=.92):
        return [(cx + rx * sx * math.cos(math.pi / 2 * t), dy - ry * math.sin(math.pi / 2 * t)) for t in
                [t0 + (t1 - t0) * j / 14 for j in range(15)]]
    # ribs everywhere, every 1/6 of the half-width
    for k in range(-5, 6):
        cv.hair(meridian(k / 6., 0, .9))
    # shading on the right: meridians spaced 1.5 px apart in projection at the base
    s = 0.
    while True:
        s += 1.5 / rx
        if s >= 1:
            break
        if s > .25:
            cv.hair(meridian(s, 0, .55 + .35 * s))
    # the turned-under limb, black
    black(cv, [(cx + rx * math.cos(math.pi / 2 * t), dy - ry * math.sin(math.pi / 2 * t)) for t in [j / 12 for j in range(13)]]
          + [(cx + rx * .9 * math.cos(math.pi / 2 * t), dy - ry * .97 * math.sin(math.pi / 2 * t)) for t in [1 - j / 12 for j in range(13)]])
    # two bands of dome windows
    for f in (.2, .45):
        yy = dy - ry * f
        w2 = rx * math.sqrt(1 - f * f)
        cv.hair([(cx - w2 * .98, yy), (cx + w2 * .98, yy)])
    # lantern, cap, Statue of Freedom
    lw = .05 * u
    ly0, ly1 = dy - ry - .07 * u, dy - ry + .015 * u
    cv.obj([R(cx - lw, ly0, cx + lw, ly1)], 1.)
    for i in range(-2, 3):
        cv.hair([(cx + i * lw * .45, ly0 + 1), (cx + i * lw * .45, ly1 - 1)])
    black(cv, R(cx + lw * .3, ly0 + 1, cx + lw, ly1 - .5))
    cap = ell(cx, ly0, lw * 1.05, .035 * u, math.pi, 2 * math.pi, 14)
    cv.obj([cap + [(cx + lw * 1.05, ly0 + .5), (cx - lw * 1.05, ly0 + .5)]], 1.)
    cv.hair(C.hatch_poly(cap, 90, 1.5, cx % 1.5))
    sy = ly0 - .035 * u
    cv.line([(cx, sy), (cx, sy - .055 * u)])
    cv.heavy([(cx, sy - .03 * u), (cx, sy - .05 * u)])


def _wings(cv, cx, yb, u, X, W):
    """Connecting wings and the Senate (north, right as seen from the west) and House pavilions."""
    big = u > 70
    pc = max(3., round(u * .045 * 2) / 2)
    for side in (-1, 1):
        # connecting block
        x0, x1 = cx + side * .3 * u, cx + side * .98 * u
        if side < 0:
            x0, x1 = x1, x0
        top = yb - .2 * u
        blk = R(x0, top, x1, yb)
        cv.obj([blk], 1.)
        # cornice band, balustrade
        cv.hair(hlines(x0, x1, top + 1, top + .03 * u, 1.5))
        # colonnade on the piano nobile, ground storey rusticated
        cy0, cy1 = top + .035 * u + 1, yb - .085 * u
        x = x0 + pc / 2
        while x < x1 - 1:
            cv.line([(x, cy0), (x, cy1)])
            if big:
                cv.hair([(x + pc * .45, cy0), (x + pc * .45, cy1)])
            x += pc
        cv.hair(hlines(x0, x1, cy1 + 1, yb - .5, 2, .5))
        if big:
            x = x0 + pc
            while x < x1 - 1:
                cv.hair([(x, cy1 + 1.5), (x, cy1 + 3)])
                x += pc
    for side in (-1, 1):
        # end pavilion with its own pediment
        x0, x1 = cx + side * .95 * u, cx + side * 1.5 * u
        if side < 0:
            x0, x1 = x1, x0
        top = yb - .23 * u
        pm = (x0 + x1) / 2
        pav = R(x0, top, x1, yb)
        ped = [(x0 + .03 * u, top), (pm, top - .07 * u), (x1 - .03 * u, top)]
        cv.obj([pav, ped], 1.)
        tym = [(x0 + .07 * u, top - .5), (pm, top - .055 * u), (x1 - .07 * u, top - .5)]
        cv.hair(C.hatch_poly(tym, 0, 1.5))
        cv.hair(hlines(x0, x1, top + 1, top + .03 * u, 1.5))
        cy0, cy1 = top + .035 * u + 1, yb - .085 * u
        x = x0 + .04 * u
        n = 0
        while x < x1 - .04 * u:
            cv.obj([R(x - pc * .32, cy0, x + pc * .32, cy1)], 0)
            black(cv, R(x + pc * .32, cy0, min(x1 - .04 * u, x + pc - pc * .32), cy1))
            x += pc
            n += 1
        cv.hair(hlines(x0, x1, cy1 + 1, yb - .5, 2, .5))
        if side > 0:
            # the Senate flag
            fx, fy = pm, top - .07 * u
            fh = max(4.5, .07 * u)
            cv.line([(fx, fy), (fx, fy - fh * 2.2)])
            fl = [(fx, fy - fh * 2.2), (fx + fh * 1.6, fy - fh * 2.1), (fx + fh * 1.6, fy - fh * 1.1), (fx, fy - fh * 1.2)]
            cv.obj([fl], .5)
            cv.line(C.hatch_poly(fl, 3, 2 if fh > 6 else 1.6))
            black(cv, [(fx, fy - fh * 2.2), (fx + fh * .7, fy - fh * 2.16), (fx + fh * .7, fy - fh * 1.66), (fx, fy - fh * 1.7)])


def _portico(cv, cx, yb, u):
    big = u > 70
    w = .3 * u
    top = yb - .3 * u
    body = R(cx - w, top, cx + w, yb)
    ped = [(cx - w - .02 * u, top), (cx, top - .1 * u), (cx + w + .02 * u, top)]
    cv.obj([body, ped], 1.)
    tym = [(cx - w + .03 * u, top - .6), (cx, top - .08 * u), (cx + w - .03 * u, top - .6)]
    cv.hair(C.hatch_poly(tym, 0, 1.5))
    if big:
        cv.line(C.hatch_poly([(cx - w * .25, top - 1), (cx, top - .06 * u), (cx + w * .25, top - 1)], 90, 2))
    cv.hair(hlines(cx - w, cx + w, top + 1, top + .035 * u, 1.5))
    n = 8
    pc = (2 * w - .04 * u) / n
    cy0, cy1 = top + .04 * u + 1, yb - .06 * u
    for i in range(n):
        x = cx - w + .02 * u + pc * (i + .5)
        cw = pc * .52
        black(cv, R(x + cw / 2, cy0, x + pc - cw / 2, cy1))
        if big:
            cv.hair([(x + cw * .2, cy0 + 1), (x + cw * .2, cy1 - 1)])
    # steps
    st = [(cx - w * .8, yb - .06 * u), (cx + w * .8, yb - .06 * u), (cx + w * 1.15, yb + .05 * u), (cx - w * 1.15, yb + .05 * u)]
    cv.obj([st], 1.)
    cv.hair(hlines(cx - w * 1.2, cx + w * 1.2, yb - .06 * u + 1.5, yb + .05 * u, 1.5))
    cv.hair(C.hatch_poly(st, 0, 1.5) and [])


def _trees(cv, cx, yb, u, rng, X, W):
    """Dark clumps of trees at both ends of the grounds."""
    for side in (-1, 1):
        for k in range(3):
            tx = cx + side * (1.25 + .28 * k + rng.uniform(-.05, .05)) * u
            r = (.09 + .02 * rng.random()) * u
            ty = yb - r * .9
            blobs = []
            for j in range(5):
                a = math.pi * (j / 4)
                bx, by = tx + r * .7 * math.cos(math.pi + a), ty - r * .5 * math.sin(a) + r * .2
                blobs.append(ell(bx, by, r * .55, r * .5, 0, 2 * math.pi, 16)[:-1])
            cv.obj(blobs, .5)
            for b in blobs:
                cv.hair(C.hatch_poly(b, 70, 1.5, rng.random()))
            body = ell(tx, ty + r * .2, r, r * .75, 0, 2 * math.pi, 20)[:-1]
            cv.obj([body], 1.)
            cv.hair(C.hatch_poly(body, 70, 1.5))
            cv.line(C.hatch_poly([(tx, ty), (tx + r, ty + r * .2), (tx + r * .6, ty + r * .9), (tx - r * .2, ty + r * .95)], -20, 2))


def _pool(cv, cx, yb, u, rng, X, W, Y1):
    """The terrace and the Reflecting Pool, holding the dome's image."""
    t1 = yb + .06 * u
    cv.obj([R(X - 2, yb, X + W + 2, Y1 + 2)], 1.)
    # lawn / terrace: close rules
    cv.hair(hlines(X - 2, X + W + 2, yb + 1.5, t1, 1.5))
    cv.line([(X - 2, t1 + .5), (X + W + 2, t1 + .5)])
    # water: broken rules, the dome's reflection laid darker
    y = t1 + 2.5
    row = 0
    while y < Y1 + 2:
        x = X - 2 - rng.uniform(0, 6)
        dd = (y - t1) / max(1., Y1 - t1)
        while x < X + W + 2:
            seg = rng.uniform(6, 22)
            cv.hair([(x, y), (x + seg, y)])
            x += seg + rng.uniform(1.5, 3.5)
        # reflection: the drum and dome, inverted, broken by ripples, the shade side heavier
        d = (y - t1) / u
        half = 0.
        if d < .25:
            half = .3 * u
        elif d < .36:
            half = .235 * u
        elif d < .62:
            q = (d - .36) / .26
            half = .2 * u * (1 - q * q) ** .5
        if half > 1.5:
            xx = cx - half + rng.uniform(0, 1.5)
            while xx < cx + half:
                seg = min(cx + half - xx, rng.uniform(3, 9))
                cv.hair([(xx, y), (xx + seg, y)])
                if xx > cx - half * .1 and u > 90:
                    cv.hair([(xx + .5, y + 1), (xx + seg - .5, y + 1)])
                xx += seg + rng.uniform(1.2, 2.2)
        y += 2
        row += 1


def _heron(cv, x, y, s):
    """A small great blue heron wading at the pool edge."""
    body = ell(x, y - s * .55, s * .32, s * .16, 0, 2 * math.pi, 18)[:-1]
    body = [(px + (py - (y - s * .55)) * .6, py) for px, py in body]
    cv.obj([body], .5)
    cv.hair(C.hatch_poly(body, 30, 1.5))
    neck = [(x - s * .2, y - s * .62), (x - s * .3, y - s * .85), (x - s * .2, y - s * 1.0), (x - s * .28, y - s * 1.12)]
    cv.line(neck)
    cv.line([(x - s * .28, y - s * 1.12), (x - s * .55, y - s * 1.08)])
    cv.hair([(x - s * .25, y - s * 1.14), (x - s * .05, y - s * 1.2)])
    cv.hair([(x + s * .02, y - s * .42), (x, y)])
    cv.hair([(x + s * .1, y - s * .42), (x + s * .14, y)])


def eagle_crest(cx, by, S, seed=0):
    """A bald eagle rising from the cartouche's crown, its spread wings grown as fans of acanthus
    fingers (carved in the same relief as the scrolls), white head turned to the right."""
    cv = C.Canvas()
    rng = random.Random(seed)
    PI = math.pi
    sy = by - S * .27
    # wings: fans of swept fingers, the primaries longest and highest
    for side in (-1, 1):
        for j in range(5, 0, -1):
            sp = j / 5.4
            a = -PI / 2 + side * (.35 + sp * 1.05)
            ln = S * (1.1 - .32 * abs(sp - .35)) * rng.uniform(.96, 1.03)
            b = side * (.35 + .45 * sp)
            C._finger(cv, cx + side * S * .08, sy, a, ln, ln * .13, b, b * 6.)
    # tail fan, hanging behind the body
    for k in (-1, 0, 1):
        C._finger(cv, cx + k * S * .03, by - S * .1, PI / 2 + k * .3, S * .3, S * .06, k * .2 + .01, k * 2. + .5)
    # body: a teardrop covered in rows of scalloped feathers
    body = [(cx + S * .17 * math.sin(t) * (1 - .25 * math.cos(t)), sy - S * .1 + S * .32 * (1 - math.cos(t)) / 2 * 1.0)
            for t in [2 * PI * i / 40 for i in range(40)]]
    body = [(x, y) for x, y in body]
    cv.obj([body], 1.)
    row = 0
    y = sy - S * .05
    while y < sy + S * .2:
        half = S * .15 * (1 - ((y - sy - S * .06) / (S * .17)) ** 2) ** .5 if abs(y - sy - S * .06) < S * .17 else 0
        n = max(2, int(2 * half / max(3., S * .06)))
        for i in range(n):
            x0 = cx - half + (i + (row % 2) * .5) * 2 * half / n
            q = [(x0 + S * .03 * (1 - math.cos(PI * t / 6)) , y + S * .022 * math.sin(PI * t / 6)) for t in range(7)]
            q = [(qx, qy) for qx, qy in q if qx < cx + half]
            if len(q) > 1:
                cv.hair(q)
        y += max(2., S * .04)
        row += 1
    cv.hair(C.hatch_poly([(cx + S * .02, sy - S * .1), (cx + S * .17, sy), (cx + S * .12, sy + S * .2), (cx + S * .02, sy + S * .22)], 80, 1.5))
    # head: a white bald-eagle head in profile, flat brow, heavy hooked beak, turned right
    hx, hy, hr = cx - S * .01, sy - S * .27, S * .14

    def H(pts):
        return [(hx + px * hr, hy + py * hr) for px, py in pts]
    head = H([(-.9, 1.9), (-1.0, 1.1), (-1.08, .35), (-.98, -.25), (-.72, -.66), (-.3, -.9), (.2, -.92), (.6, -.77),
              (.88, -.6), (.95, .2), (.65, .5), (.38, .82), (.3, 1.25), (.42, 1.9), (.1, 2.12), (-.35, 2.05), (-.65, 1.98)])
    cv.obj([head], 1.)
    rng2 = random.Random(seed + 5)
    for row in range(7):
        yy = -.35 + row * .32
        for k in range(3):
            x0 = -.95 + k * .38 + (row % 2) * .19 + rng2.uniform(-.05, .05)
            if x0 < .3 - (row > 3) * .1:
                cv.hair(H([(x0, yy), (x0 + .14, yy + .1), (x0 + .3, yy + .12)]))
    beak = H([(.75, -.64), (1.2, -.7), (1.62, -.6), (1.95, -.32), (2.12, .05), (2.06, .48), (1.9, .27), (1.7, .14),
              (1.3, .2), (.85, .32)])
    cv.obj([beak], 1.)
    cv.hair(C.hatch_poly(H([(.95, -.05), (1.75, -.12), (1.7, .14), (1.3, .2), (.85, .32)]), 10, 1.5))
    cv.hair(C.hatch_poly(H([(1.5, -.6), (1.95, -.32), (2.1, .05), (1.75, -.12)]), 60, 1.5))
    black(cv, H([(1.82, -.12), (2.1, .0), (2.06, .48), (1.9, .27), (1.72, .14)]))
    cv.line(H([(.97, -.68), (.94, -.2), (.97, .3)]))
    cv.line(H([(.9, .02), (1.3, -.06), (1.78, -.12)]))
    ey = H([(.36, -.38)])[0]
    eye = [(ey[0] + max(1.2, hr * .16) * math.cos(t), ey[1] + max(1., hr * .13) * math.sin(t)) for t in [2 * PI * i / 12 for i in range(12)]]
    cv.obj([eye], 1.)
    black(cv, eye)
    cv.heavy(H([(-.05, -.55), (.35, -.68), (.8, -.6)]))
    cv.hair(H([(.1, -.15), (.5, -.12)]))
    # talons gripping the moulding
    for side in (-1, 1):
        fx = cx + side * S * .07
        for k in (-1, 0, 1):
            cv.line([(fx, by - S * .05), (fx + k * S * .03, by + 1), (fx + k * S * .035 + side * .8, by + 2.5)])
    return cv.svg()


def scene(X, Y, W, H, clip_d, seed=0, cid="cv1"):
    """The engraved Capitol view filling the bbox X,Y,W,H, clipped to path clip_d."""
    rng = random.Random(seed)
    cx = X + W / 2
    yb = Y + H * .7
    u = min(H * .67, W * .6)
    cv = C.Canvas()
    _sky(cv, X, Y, W, H, yb)
    _hood(cv, cx, yb, u, rng, X, W)
    _hills(cv, cx, yb, u, X, W)
    _drum_and_dome(cv, cx, yb, u)
    _wings(cv, cx, yb, u, X, W)
    _portico(cv, cx, yb, u)
    _pool(cv, cx, yb, u, rng, X, W, Y + H)
    if u > 90:
        _heron(cv, cx + .5 * u, yb + .06 * u + min(H * .2, .26 * u), .2 * u)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ----------------------------------------------------------------------------------------------
# lettering, drawn as strokes (no <text>)
# ----------------------------------------------------------------------------------------------

def _o(w):
    return [[(w / 2 + w / 2 * math.cos(a), .5 + .5 * math.sin(a)) for a in [2 * math.pi * i / 20 for i in range(21)]]]


_FONT = {
    "W": (.86, [[(0, 0), (.2, 1), (.43, .25), (.66, 1), (.86, 0)]]),
    "E": (.5, [[(.5, 0), (0, 0), (0, 1), (.5, 1)], [(0, .5), (.4, .5)]]),
    "T": (.6, [[(0, 0), (.6, 0)], [(.3, 0), (.3, 1)]]),
    "H": (.6, [[(0, 0), (0, 1)], [(.6, 0), (.6, 1)], [(0, .5), (.6, .5)]]),
    "P": (.52, [[(0, 1), (0, 0), (.36, 0), (.5, .1), (.52, .25), (.5, .4), (.36, .5), (0, .5)]]),
    "O": (.72, _o(.72)),
    "L": (.48, [[(0, 0), (0, 1), (.48, 1)]]),
    "V": (.66, [[(0, 0), (.33, 1), (.66, 0)]]),
    "X": (.6, [[(0, 0), (.6, 1)], [(.6, 0), (0, 1)]]),
    "U": (.6, [[(0, 0), (0, .68), (.08, .9), (.3, 1), (.52, .9), (.6, .68), (.6, 0)]]),
    "I": (0., [[(0, 0), (0, 1)]]),
    "·": (.12, [[(.06, .45), (.06, .55)]]),
}


def letter_width(txt, hgt, track=.28):
    return sum((_FONT[c][0] + track) * hgt if c in _FONT else .5 * hgt for c in txt) - track * hgt


def letters_along(pts, txt, hgt, track=.28):
    """Strokes for txt centred on polyline pts (letters upright to its local tangent)."""
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seg)

    def at(s):
        s = min(max(s, 0), total - 1e-6)
        for (a, b), L in zip(zip(pts, pts[1:]), seg):
            if s <= L:
                t = s / L if L else 0
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
            s -= L
        return pts[-1], 0.
    s = (total - letter_width(txt, hgt, track)) / 2
    out = []
    for c in txt:
        if c not in _FONT:
            s += .5 * hgt
            continue
        cw, strokes = _FONT[c]
        (mx, my), ang = at(s + cw * hgt / 2)
        ca, sa = math.cos(ang), math.sin(ang)
        for st in strokes:
            q = []
            for lx, ly in st:
                dx, dy = (lx - cw / 2) * hgt, (ly - .5) * hgt
                q.append((mx + dx * ca - dy * sa, my + dx * sa + dy * ca))
            out.append(q)
            if c in "O·":
                continue
            for (lx, ly), (nx, ny) in ((st[0], st[1]), (st[-1], st[-2])):
                if ly not in (0, 1):
                    continue
                sr = .13
                if abs(nx - lx) < abs(ny - ly) * .8:
                    tick = [(lx - sr, ly), (lx + sr, ly)]
                elif abs(ny - ly) < .01:
                    tick = [(lx, ly), (lx, ly + (.16 if ly == 0 else -.16))]
                else:
                    tick = [(lx - sr, ly), (lx + sr, ly)]
                q = []
                for tx, ty in tick:
                    dx, dy = (tx - cw / 2) * hgt, (ty - .5) * hgt
                    q.append((mx + dx * ca - dy * sa, my + dx * sa + dy * ca))
                out.append(q)
        s += (cw + track) * hgt
    return out


def _strokes_svg(strokes, w):
    return f'<path d="{"".join(_d(q, tol=0) for q in strokes)}" fill="none" stroke="#000" stroke-width="{w}"/>'


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, re-cut so the scene fills the whole field, never white)
# ----------------------------------------------------------------------------------------------

def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.3, 190)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    f = C._d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(scene(cx - rx + 2, cy - ry + 2, 2 * rx - 4, 2 * ry - 4, f, seed, C._uid("sb", w, h)))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2.2, ry - 2.2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _cart_bbox(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.75)
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
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bx, by, bw_, bh = _cart_bbox(cx, cy, cw, ch)
    o.append(scene(bx, by, bw_, bh, field, seed, C._uid("sm", w, h)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = 0.
    top_free = 12.
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    fh_ = h - py0 - 1
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    o.append(f'<path d="M.5,{_n(py0 - 3.5)}h{_n(w - 1)}v{_n(fh_ + 4)}h{_n(-w + 1)}z" fill="{C.pat("M")}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(fh_ + 1.5)}h{_n(-pw - 3)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(C.dark_ground((px0, py0, pw, fh_ - 1), "G"))
    cw, ch = pw * .5, ph * .62
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .16, ph * .25)
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(11, ph * .04), rmax=r1 * .9,
                   max_n=10, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0, pw, ph, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bx, by, bw_, bh = _cart_bbox(cx, cy, cw, ch)
    o.append(scene(bx, by, bw_, bh, field, seed, C._uid("st", w, h)))
    rng.randrange(1 << 20)
    o.append(eagle_crest(cx, cy - ch / 2 + 17, min(ch * .26 + top_free, 92), seed))
    bh_ = min(17, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.3, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_strokes_svg(letters_along([(px_, py_ + bh_ * .0) for px_, py_ in centre], "WE THE PEOPLE", bh_ * .52), 1))
    p, (tx, ty, tw, th) = C.pedestal(0, h - ped_h, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    tab = R(tx + 3, ty + 3, tx + tw - 1, ty + th - 1)
    o.append(f'<path d="{"".join(_d(q, tol=0) for q in C.hatch_poly(tab, 0, 2, .5))}" stroke="#000" stroke-width=".5"/>')
    lh = min(th * .62, 12)
    my = ty + th / 2 + 1
    o.append(_strokes_svg(letters_along([(tx, my), (tx + tw, my)], "VOX · POPULI", lh, .4), 1.5))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
