"""solar-02 "When the sun pays for chores": the noon sun riding its 10 am - 1 pm arc over Parker's
panel array on Sauvie Island, Mt. Hood on the horizon; the acanthus curls round the three chores the
sun pays for (an EV charge-plug face, a washer porthole, a stack of dishes) and a clock with the
10-1 window lit. Easter egg: the panel rack stands on crossed drumsticks."""
import sys
import math
import random
import engraving_codex as C

PI, TAU = math.pi, 2 * math.pi
E = C._ell_pts
_n = C._n


def circ(cx, cy, r, n=None):
    return E(cx, cy, r, r, n or max(14, int(r * 2.2)))[:-1]


def ring(cx, cy, r, n=None):
    c = circ(cx, cy, r, n)
    return c + [c[0]]


# ------------------------------------------------------------------ emblems grown in the volute eyes

def plug(cv, cx, cy, R):
    """EV charge-plug face (J1772): a turned collar round a dark face with five sockets."""
    tab = [(cx - R * .24, cy - R * .9), (cx + R * .24, cy - R * .9), (cx + R * .17, cy - R * 1.22), (cx - R * .17, cy - R * 1.22)]
    cv.obj([tab], 1.)
    cv.hair(C.hatch_poly(tab, 0, 1.5))
    cv.obj([circ(cx, cy, R)], 1.)
    cv.hair([ring(cx, cy, R - 1.3)])
    cv.hair(C.hatch_poly(circ(cx, cy, R - 1.6), 90, 2))
    rr = R * .74
    face = circ(cx, cy, rr)
    cv.obj([face], 1.5)
    cv.hair(C.hatch_poly(face, 45, 1.5))
    cv.hair(C.hatch_poly(face, -45, 2))
    for (ux, uy, ur) in ((-.38, -.24, .22), (.38, -.24, .22), (0, .42, .22), (-.52, .26, .12), (.52, .26, .12)):
        px, py, pr = cx + ux * rr, cy + uy * rr, max(1.1, ur * rr)
        cv.obj([circ(px, py, pr, 12)], 1.)
        if pr > 1.8:
            cv.line(ring(px + .3, py + .3, pr * .45, 10))


def porthole(cv, cx, cy, R):
    """Washer door: chrome bezel with a hinge, the drum glass dark with tumbling laundry."""
    hinge = [(cx - R * 1.14, cy - R * .32), (cx - R * .8, cy - R * .32), (cx - R * .8, cy + R * .32), (cx - R * 1.14, cy + R * .32)]
    cv.obj([hinge], 1.)
    cv.hair(C.hatch_poly(hinge, 0, 1.5))
    cv.obj([circ(cx, cy, R)], 1.)
    for f in (.9, .8):
        cv.hair([ring(cx, cy, R * f)])
    g = circ(cx, cy, R * .7)
    cv.obj([g], 1.5)
    cv.hair(C.hatch_poly(g, 0, 1.5))
    for k in range(3):
        a0 = k * TAU / 3 + .4
        pts = []
        for i in range(14):
            t = i / 13
            rr = R * (.62 - .4 * t)
            a = a0 + t * 2.4
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        cv.heavy(pts)
    glare = E(cx - R * .1, cy - R * .1, R * .52, R * .52, 16, PI * 1.05, PI * 1.45) + \
        E(cx - R * .02, cy - R * .02, R * .44, R * .44, 16, PI * 1.45, PI * 1.05)
    cv.obj([glare], 0)


def dishes(cv, cx, cy, R):
    """A stack of clean dinner plates on a dark ground."""
    bg = circ(cx, cy, R)
    cv.obj([bg], 1.)
    cv.hair(C.hatch_poly(bg, 0, 1.5))
    cv.hair(C.hatch_poly(bg, 90, 3))
    rx, ry = R * .8, R * .3
    for k in range(4):
        py = cy + R * .4 - k * R * .2
        under = E(cx, py + 1.8, rx, ry, 30)[:-1]
        cv.obj([under], 1.)
        cv.heavy(E(cx, py + 1.8, rx - .3, ry - .3, 20, .3, PI - .3))
        top = E(cx, py, rx, ry, 30)[:-1]
        cv.obj([top], 1.)
        cv.hair([E(cx, py, rx * .68, ry * .64, 28)])
        if k == 3:
            cv.hair(C.hatch_poly(E(cx, py + ry * .12, rx * .62, ry * .5, 24)[:-1], 0, 2))
        else:
            cv.hair(E(cx, py, rx * .84, ry * .82, 16, PI * .1, PI * .9))


def clock(cv, cx, cy, R):
    """A clock face whose 10-1 sector is lit with rays: the best hours to run the loads."""
    cv.obj([circ(cx, cy, R)], 1.)
    cv.hair([ring(cx, cy, R * .9)])
    face = circ(cx, cy, R * .84)
    cv.hair(C.hatch_poly(face, 0, 1.5))
    a10, a13 = -PI / 2 - PI / 3, -PI / 2 + PI / 6
    sec = [(cx, cy)] + [(cx + R * .84 * math.cos(a10 + (a13 - a10) * i / 12),
                         cy + R * .84 * math.sin(a10 + (a13 - a10) * i / 12)) for i in range(13)]
    cv.obj([sec], .5)
    for i in range(1, 9):
        a = a10 + (a13 - a10) * i / 9
        cv.hair([(cx + R * .25 * math.cos(a), cy + R * .25 * math.sin(a)), (cx + R * .8 * math.cos(a), cy + R * .8 * math.sin(a))])
    cv.obj([], 0)
    for i in range(12):
        a = TAU * i / 12
        r0 = R * (.64 if i % 3 == 0 else .72)
        (cv.heavy if i % 3 == 0 else cv.line)([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                                               (cx + R * .84 * math.cos(a), cy + R * .84 * math.sin(a))])
    ah = -PI / 2 - PI / 3
    cv.heavy([(cx, cy), (cx + R * .45 * math.cos(ah), cy + R * .45 * math.sin(ah))])
    cv.line([(cx, cy), (cx, cy - R * .7)])
    cv.obj([circ(cx, cy, 1.4, 8)], 1.)


EMBLEMS = {"plug": plug, "porthole": porthole, "dishes": dishes, "clock": clock}


def evolute(cv, cx, cy, r, a0, turns, flip, rng, tail, tb, stem, fronds, emblem):
    """A house volute whose curl opens round an emblem instead of a drilled eye."""
    if not emblem:
        C._volute(cv, cx, cy, r, a0, turns, flip, rng, tail, tb, stem, fronds)
        return
    C._volute(cv, cx, cy, r, a0, turns + .15, flip, rng, tail, tb, stem, fronds, inner=False, end=.5)
    EMBLEMS[emblem](cv, cx, cy, r * .45)


def rinceau(x0, y0, ang, length, breadth, seed, mirror, emblems, r_scale=1., turns=1.35, cv=None):
    """engraving_codex.running_scroll, with emblem curls."""
    rng = random.Random(seed)
    th = math.radians(ang)
    dx, dy = math.cos(th), math.sin(th)
    nx, ny = (dy, -dx) if mirror else (-dy, dx)
    r = breadth * .4 * r_scale
    n = max(1, int(round(length / (r * 2.35))))
    P = length / n
    r = min(r, P * .46)
    units = []
    for i in range(n):
        down = i % 2 == 0
        off = (.12 if down else -.12) * breadth
        along = P * (i + .62)
        a0, flip = (-90, False) if down else (90, True)
        if mirror:
            a0, flip = -a0, not flip
        tb = .9 if down else -.9
        units.append((x0 + dx * along + nx * off, y0 + dy * along + ny * off, a0 + ang, flip, tb,
                      rng.randrange(1 << 20), emblems[i] if i < len(emblems) else None))
    for cx, cy, a0, flip, tb, sd, em in units[::-1]:
        evolute(cv, cx, cy, r, a0, turns, flip, random.Random(sd), (P * .55) / r, tb, r * .15,
                3 if r > 22 else 2, em)


def fill_scrolls(x, y, w, h, occupied, seed, rmin, rmax, max_n, edge, emblems, cv):
    """engraving_codex.fill_scrolls, the largest fillers curling round emblems."""
    rng = random.Random(seed)
    grid = 5.
    nx, ny = max(2, int(w / grid)), max(2, int(h / grid))
    pts = [(x + (i + .5) * w / nx, y + (j + .5) * h / ny) for j in range(ny) for i in range(nx)]
    near = [None] * len(pts)
    dist = []
    for k, (px, py) in enumerate(pts):
        best = 1e9
        for sh in occupied:
            d = C._shape_dist(px, py, sh)
            if d < best:
                best, near[k] = d, sh
        dist.append(min(best, min(px - x, x + w - px, py - y, y + h - py) / edge))
    made = []
    for it in range(max_n):
        k = max(range(len(pts)), key=dist.__getitem__)
        free = dist[k]
        if free < rmin * 1.1:
            break
        px, py = pts[k]
        r = min(rmax, free / 1.1) * rng.uniform(.92, 1.)
        sh = near[k]
        if sh is not None:
            if sh[0] == "c":
                bx, by = sh[1], sh[2]
            else:
                bx, by = min(max(px, sh[1]), sh[3]), min(max(py, sh[2]), sh[4])
            beta = math.degrees(math.atan2(by - py, bx - px))
            gap = max(0., C._shape_dist(px, py, sh) - r * .9)
        else:
            beta, gap = rng.uniform(0, 360), 0.
        flip = rng.random() < .5
        a0 = beta - 90 if flip else beta + 90
        made.append([r, px, py, a0, flip, min(1.4, (gap + r * .35) / r), rng.randrange(1 << 20), None])
        newc = ("c", px, py, r * 1.08)
        occupied.append(newc)
        for j, (qx, qy) in enumerate(pts):
            d = math.hypot(qx - px, qy - py) - r * 1.08
            if d < dist[j]:
                dist[j], near[j] = d, newc
    inside = [m for m in made if x + m[0] * .6 < m[1] < x + w - m[0] * .6 and y + m[0] * .6 < m[2] < y + h - m[0] * .6]
    for m, em in zip(sorted(inside, key=lambda m: -m[0]), emblems):
        if m[0] >= 18:
            m[7] = em
    for r, px, py, a0, flip, tail, sd, em in sorted(made, key=lambda m: m[0]):
        evolute(cv, px, py, r, a0, 1.35, flip, random.Random(sd), tail, .6 if flip else -.6, r * .15, 2, em)


# ------------------------------------------------------------------ the vignette

def drumstick(cv, x0, y0, x1, y1, w):
    """A hickory drumstick from butt (x0, y0) to bead tip (x1, y1), grain along it."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    sides = []
    for s in (1, -1):
        side = []
        for i in range(11):
            t = i / 10 * .9
            hw = w / 2 * (1 if t < .55 else 1 - .62 * (t - .55) / .35)
            side.append((x0 + ux * L * t + nx * s * hw, y0 + uy * L * t + ny * s * hw))
        sides.append(side)
    cv.obj([sides[0] + sides[1][::-1]], 1.)
    cv.hair([(x0 + ux + nx * w * .1, y0 + uy + ny * w * .1), (x0 + ux * L * .8, y0 + uy * L * .8)])
    cv.line([(p[0] - nx * .4, p[1] - ny * .4) for p in sides[1]])
    bx, by = x0 + ux * L * .95, y0 + uy * L * .95
    cv.obj([E(bx, by, w * .62, w * .62, 12)[:-1]], 1.)


def car(cv, x, y, w):
    """A small hatchback EV in profile, facing left; (x, y) is the left end of its ground line."""
    h = w * .42

    def P(u, v):
        return (x + u * w, y - h + v * h)
    body = [P(0, .78), P(.01, .52), P(.1, .42), P(.3, .36), P(.43, .08), P(.72, .05), P(.9, .34), P(.99, .44), P(1, .78)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly([P(0, .6), P(1, .6), P(1, .78), P(0, .78)], 0, 1.5))
    cv.hair(C.hatch_poly([P(.1, .44), P(.98, .46), P(.99, .6), P(.01, .6)], 0, 3))
    win = [P(.45, .14), P(.7, .12), P(.84, .36), P(.37, .38)]
    cv.obj([win], 1.)
    cv.hair(C.hatch_poly(win, 60, 1.5))
    cv.line([P(.6, .13), P(.6, .37)])
    for u in (.2, .8):
        wx, wy = P(u, .8)
        rr = h * .2
        cv.obj([circ(wx, wy, rr)], 1.5)
        q = rr - 1.
        while q > rr * .45:
            cv.line(ring(wx, wy, q))
            q -= .9
        cv.obj([circ(wx, wy, rr * .35, 10)], 1.)
    return P(1, .5)


def scene(x, y, w, h, seed, rich):
    """Sky, sun on its 10-1 arc, Mt. Hood, the Columbia, the field and the panel array."""
    cv = C.Canvas()
    rng = random.Random(seed)
    hy = y + h * (.58 if rich else .6)
    sky = [(x, y), (x + w, y), (x + w, hy + 2), (x, hy + 2)]
    cv.obj([sky], 0)
    yy = y + 1
    while yy < hy + 2:
        f = (yy - y) / (hy - y)
        (cv.line if f < .25 else cv.hair)([(x, yy), (x + w, yy)])
        yy += 2.
    # the sun's path: dotted from sunrise to sunset, carved solid across 10 am - 1 pm
    t0, t1 = 7.3, 16.7
    pk = h * (.4 if rich else .38)
    ax0, ax1 = x + w * .03, x + w * .97

    def at(t):
        p = (t - t0) / (t1 - t0)
        return (ax0 + (ax1 - ax0) * p, hy - pk * math.sin(PI * p))
    band = [at(t0 + (t1 - t0) * i / 60) for i in range(61)]
    cv.obj([[(px, py - 1.6) for px, py in band] + [(px, py + 1.6) for px, py in band][::-1]], 0)
    for i in range(0, 60, 2):
        cv.line([band[i], band[i + 1]])
    seg = [at(10 + 3 * i / 20) for i in range(21)]
    cv.obj([[(px, py - 2.2) for px, py in seg] + [(px, py + 2.2) for px, py in seg][::-1]], 1.)
    cv.line(seg)
    for t in (10, 13):
        px, py = at(t)
        cv.obj([circ(px, py, 3.2, 12)], 1.)
        cv.line(ring(px, py, 1.4, 8))
    # the sun at its noon height
    sx, sy = at(11.9)
    rs = min(w, h) * (.1 if rich else .13)
    nr = 24
    for i in range(nr):
        a = TAU * (i + .5) / nr
        lim = (hy - sy - 2) / math.sin(a) if math.sin(a) > .05 else 1e9
        if i % 2:
            r1 = min(rs * 2.25, lim)
            bw = .13
            p0 = (sx + rs * 1.12 * math.cos(a - bw), sy + rs * 1.12 * math.sin(a - bw))
            p1 = (sx + r1 * math.cos(a), sy + r1 * math.sin(a))
            p2 = (sx + rs * 1.12 * math.cos(a + bw), sy + rs * 1.12 * math.sin(a + bw))
            cv.obj([[p0, p1, p2]], .5)
            pm = (sx + rs * 1.12 * math.cos(a), sy + rs * 1.12 * math.sin(a))
            cv.hair(C.hatch_poly([pm, p1, p2], math.degrees(a) + 8, 1.5))
            cv.hair([pm, p1])
        else:
            r1 = min(rs * 1.75, lim)
            cv.obj([], 0)
            cv.line([(sx + rs * 1.2 * math.cos(a), sy + rs * 1.2 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    cv.obj([circ(sx, sy, rs * 1.08, 40)], .5)
    disc = circ(sx, sy, rs, 40)
    cv.obj([disc], 1.5)
    cres = E(sx, sy, rs - .6, rs - .6, 30, -.35, PI * .85) + E(sx - rs * .22, sy - rs * .22, rs * .9, rs * .9, 30, -.35, PI * .85)[::-1]
    cv.hair(C.hatch_poly(disc, 0, 3, 1.))
    cv.hair(C.hatch_poly(cres, 0, 3, 2.5))
    cv.hair([E(sx, sy, rs * .8, rs * .8, 30, PI * 1.1, PI * 1.6)])
    cv.obj([circ(sx, sy, 1.5, 8)], 1.)
    # Mt. Hood, far off to the east
    mx = x + w * .8
    mh = h * (.24 if rich else .19)
    mw = w * (.38 if rich else .3)
    mtn = [(mx - mw / 2, hy + 1), (mx - mw * .18, hy - mh * .62), (mx - mw * .05, hy - mh * .93), (mx + mw * .02, hy - mh),
           (mx + mw * .1, hy - mh * .86), (mx + mw * .24, hy - mh * .55), (mx + mw / 2, hy + 1)]
    cv.obj([mtn], .5)
    cv.hair(C.hatch_poly(mtn, 0, 1.5))
    shade = [(mx + mw * .02, hy - mh), (mx + mw * .1, hy - mh * .86), (mx + mw * .24, hy - mh * .55), (mx + mw / 2, hy + 1), (mx + mw * .05, hy + 1)]
    cv.hair(C.hatch_poly(shade, 70, 2))
    snow = [(mx - mw * .18, hy - mh * .62), (mx - mw * .05, hy - mh * .93), (mx + mw * .02, hy - mh), (mx + mw * .1, hy - mh * .86),
            (mx + mw * .2, hy - mh * .62), (mx + mw * .12, hy - mh * .52), (mx + mw * .06, hy - mh * .64), (mx - mw * .02, hy - mh * .5),
            (mx - mw * .1, hy - mh * .6)]
    cv.obj([snow], 0)
    for k in (-.1, -.03, .05, .12):
        cv.hair([(mx + mw * k * .3, hy - mh * .95), (mx + mw * k, hy - mh * .6)])
    cv.hair(C.hatch_poly([(mx + mw * .02, hy - mh), (mx + mw * .1, hy - mh * .86), (mx + mw * .2, hy - mh * .62),
                          (mx + mw * .12, hy - mh * .52), (mx + mw * .04, hy - mh * .8)], 70, 3))
    # the far bank: low hills either side of the mountain
    hills = [(x, hy + 1)]
    for i in range(41):
        px = x + w * i / 40
        dm = abs(px - mx) / (mw * .5)
        hh = h * (.03 + .02 * math.sin(i / 40 * 9 + seed % 7) + .012 * math.sin(i / 40 * 23))
        if dm < 1:
            hh *= dm ** 2
        hills.append((px, hy - hh))
    hills.append((x + w, hy + 1))
    cv.obj([hills], .5)
    cv.hair(C.hatch_poly(hills, 0, 1.5))
    cv.hair(C.hatch_poly(hills, 90, 3))
    # the Columbia: broken water lines
    wy0, wy1 = hy + .5, hy + h * .07
    cv.obj([[(x, wy0), (x + w, wy0), (x + w, wy1), (x, wy1)]], 0)
    yy = wy0 + 1
    while yy < wy1:
        xx = x + rng.uniform(0, 6)
        while xx < x + w:
            L = rng.uniform(5, 18)
            cv.hair([(xx, yy), (min(x + w, xx + L), yy)])
            xx += L + rng.uniform(1.5, 3)
        yy += 1.5
    # the island field: rows converging on the horizon
    cv.obj([[(x, wy1), (x + w, wy1), (x + w, y + h), (x, y + h)]], 1.)
    yy = wy1 + 1.5
    while yy < y + h:
        cv.hair([(x, yy), (x + w, yy)])
        yy += 2. if yy < wy1 + h * .1 else 3.
    vx = x + w * .5
    for i in range(-16, 17):
        cv.hair([(vx + i * w * .025, wy1 + h * .08), (vx + i * w * .1, y + h)])
    # the array, standing on crossed drumsticks
    ac = x + w * (.33 if rich else .5)
    aw = w * (.56 if rich else .5)
    fy = y + h * .74
    ah = h * .2
    sk = aw * .06
    BL, BR = (ac - aw / 2, fy), (ac + aw / 2, fy)
    TL, TR = (ac - aw * .45, fy - ah), (ac + aw * .45, fy - ah)
    shadow = [(BL[0] + aw * .06, fy + 1), (BR[0] - aw * .02, fy + 1), (BR[0] - aw * .1, fy + h * .16), (BL[0] + aw * .14, fy + h * .16)]
    cv.obj([shadow], 0)
    cv.hair(C.hatch_poly(shadow, 0, 1.5))
    cv.hair(C.hatch_poly(shadow, 60, 2))
    gy = y + h * .93
    sw = max(2.6, h * .034)
    p1x, p2x = BL[0] + aw * .1, BR[0] - aw * .1
    for px in (p1x, p2x):
        post = [(px - 1.2, fy), (px + 1.2, fy), (px + 1.2, gy), (px - 1.2, gy)]
        cv.obj([post], 1.)
        cv.hair([(px + .3, fy), (px + .3, gy)])
    # the Easter egg: the X-brace is a pair of crossed drumsticks, beads down
    drumstick(cv, p1x + 2, fy + 1, p2x - 3, gy - sw * .4, sw)
    drumstick(cv, p2x - 2, fy + 1, p1x + 3, gy - sw * .4, sw)
    rail = [(BL[0] + 2, fy), (BR[0] - 2, fy), (BR[0] - 2, fy + 2.5), (BL[0] + 2, fy + 2.5)]
    cv.obj([rail], 1.)
    cv.line([(BL[0] + 2, fy + 1.8), (BR[0] - 2, fy + 1.8)])

    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    def quad(u, v):
        return lerp(lerp(BL, BR, u), lerp(TL, TR, u), v)
    cv.obj([[BL, BR, TR, TL]], 1.5)
    cols = 6 if rich else max(4, int(aw / 24))
    rows = 2
    g = .012
    for i in range(cols):
        for j in range(rows):
            u0, u1 = i / cols + g, (i + 1) / cols - g
            v0, v1 = j / rows + g * 3, (j + 1) / rows - g * 3
            cell = [quad(u0, v0), quad(u1, v0), quad(u1, v1), quad(u0, v1)]
            glint = (i - j) in (cols // 2 - 1, cols // 2)
            cv.hair(C.hatch_poly(cell, -78, 1.5, inset=.4))
            if not glint:
                cv.hair(C.hatch_poly(cell, 12, 2, inset=.4))
            for t in (.33, .66):
                cv.hair([lerp(cell[0], cell[1], t), lerp(cell[3], cell[2], t)])
    if rich:
        plug_at = car(cv, x + w * .64, y + h * .9, w * .3)
        st = (BR[0] - 3, fy + 2)
        pts = []
        for i in range(41):
            t = i / 40
            px = st[0] + (plug_at[0] - st[0]) * t
            py = st[1] + (plug_at[1] - st[1]) * t + h * .05 * math.sin(PI * t)
            pts.append((px, py))
        cv.obj([], 0)
        cv.heavy(pts)
    return cv.svg()


def clipped(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------ layouts

def band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.1, 180)
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    cv = C.Canvas()
    half = (w - gap * .82) / 2
    rs = 1.15 * max(1., 62. / gh)
    rinceau(cx + gap * .41, cy, 0, half, gh, seed, False, ["porthole", "clock"], rs, cv=cv)
    rinceau(cx - gap * .41, cy, 180, half, gh, seed + 1, True, ["plug", "dishes"], rs, cv=cv)
    o.append(C._clip(C._uid("sb", w, h, seed), 0, top, w, gh, cv.svg()))
    o.append(C._medallion(cx, cy, rx, ry))
    fd = C._d(E(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(clipped(C._uid("sv", w, h), fd, scene(cx - rx, cy - ry, 2 * rx, 2 * ry, seed, False)))
    o.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _pair(cv, cx, cy, r, side, rng, a_out, turns, tail, up, em):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    evolute(cv, cx, cy, r, a0, turns, flip, rng, tail, -.5 if up else .5, r * .15, 3, em)


def field_of(rect):
    """The cartouche field's bounding box from its clear rect."""
    ix, iy, iw, ih = rect
    k = 2 ** (-1 / 2.6)
    a, b = iw / 2 / k + 6, ih / 2 / k + 6
    cx, cy = ix + iw / 2, iy + ih / 2
    return cx - a, cy - b, 2 * a, 2 * b


def medium(w, h, seed):
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
    cv = C.Canvas()
    main = C.Canvas()
    for side, emb in ((-1, "plug"), (1, "porthole")):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True, emb)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), max(9, gh * .08), r * .8, 8, .7, ["dishes", "clock"], cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, rect, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = field_of(rect)
    o.append(clipped(C._uid("mv", w, h), fd, scene(fx, fy, fw, fh, seed, fw > 200)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def numerals(x, y, w, h):
    """'10-1' cut as strokes, centred in x..x+w, y..y+h."""
    ch = h * .66
    cw = ch * .55
    gap = cw * .4
    tot = cw * 4 + gap * 3
    x0 = x + (w - tot) / 2
    y0 = y + (h - ch) / 2
    out_h, out_l = [], []

    def one(px):
        m = px + cw / 2
        out_h.append([(m, y0), (m, y0 + ch)])
        out_l.append([(m - cw * .28, y0 + ch * .18), (m, y0)])
        out_l.append([(m - cw * .32, y0 + ch), (m + cw * .32, y0 + ch)])

    one(x0)
    zx = x0 + cw + gap + cw / 2
    out_l.append(E(zx, y0 + ch / 2, cw * .42, ch / 2, 24))
    out_h.append(E(zx, y0 + ch / 2, cw * .42, ch / 2, 12, PI * .6, PI * 1.4))
    dx = x0 + 2 * (cw + gap)
    out_h.append([(dx + cw * .1, y0 + ch / 2), (dx + cw * .9, y0 + ch / 2)])
    one(x0 + 3 * (cw + gap))
    d1 = "".join(C._d(p, tol=0) for p in out_h)
    d2 = "".join(C._d(p, tol=0) for p in out_l)
    return (f'<path d="{d1}" stroke="#000" stroke-width="1.5" fill="none"/>'
            f'<path d="{d2}" stroke="#000" stroke-width="1" fill="none"/>')


def tall(w, h, seed):
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
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .18, ph * .25)
    for side, emb in ((-1, "plug"), (1, "porthole")):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True, emb)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side, emb in ((-1, "dishes"), (1, "clock")):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        _pair(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False, emb)
        occ.append(("c", vx, vy, r2))
    fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), max(14, ph * .05), r1 * .9, 6, .6, [], cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, rect, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = field_of(rect)
    o.append(clipped(C._uid("tv", w, h), fd, scene(fx, fy, fw, fh, seed, True)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bsvg, _ = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, min(16, ph * .05), .04, rng.randrange(1 << 20))
    o.append(bsvg)
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 3)},{_n(ty + 3)}h{_n(tw - 5)}v{_n(th - 5)}h{_n(-tw + 5)}z" fill="{C.pat("L")}" stroke="none"/>')
    nb = min(th, 22)
    o.append(f'<path d="M{_n(cx - nb * 1.4)},{_n(ty + 2.5)}h{_n(nb * 2.8)}v{_n(th - 4)}h{_n(-nb * 2.8)}z" fill="#fff" stroke="none"/>')
    o.append(numerals(cx - nb * 1.4, ty + 2, nb * 2.8, th - 3))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = band(w, h, seed)
    elif h <= 260:
        body = medium(w, h, seed)
    else:
        body = tall(w, h, seed)
    return C.svg_doc(w, h, body)
