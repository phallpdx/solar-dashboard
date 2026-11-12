"""today-01 "Good morning" plate: a cloudy November dawn over the Multnomah Channel at Sauvie
Island, Mt. Hood on the horizon, a great blue heron in the low-tide shallows, the island barn with
its flag up for Veterans Day, all inside the house acanthus frame. A rising sun crowns the plate;
the pedestal tablet carries a band of stars for Veterans Day. Easter egg: Parker's dog sits on the
bank watching the heron (and a tiny crossed pair of drumsticks lean on the barn door)."""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, pat, _n, _d, _ell_pts, _Rib, _clip, _uid

TAU = math.tau


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _rot(pts, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def _xf(pts, ox, oy, s, flip=1):
    return [(ox + flip * x * s, oy + y * s) for x, y in pts]


def _solid(cv, poly, pitch=.8, ang=0):
    cv.line(hatch_poly(poly, ang, pitch))


def _cloud_poly(x0, x1, base, puffs, sag=1.5):
    """Upper envelope of puffs [(cx, r)] sitting on a slightly sagging base line."""
    top = []
    x = x0
    while x <= x1 + .01:
        best = base
        for cx, r in puffs:
            dx = x - cx
            if abs(dx) < r:
                yy = base - r * .55 - math.sqrt(r * r - dx * dx) * .75
                best = min(best, yy)
        top.append((x, best))
        x += 1.
    bot = [(x, base + sag * math.sin(math.pi * (x - x0) / max(1, x1 - x0))) for x, _ in top[::-1]]
    return top + bot


def _wavy(x0, x1, y, amp, per, ph, rng, gap_p=.12, gmin=2, gmax=6, avoid=()):
    """A water line from x0 to x1 broken into runs (sparkle gaps)."""
    out, cur = [], []
    x = x0
    while x <= x1:
        yy = y + amp * math.sin((x / per + ph) * TAU)
        blocked = any(a <= x <= b for a, b in avoid)
        if blocked:
            if len(cur) > 1:
                out.append(cur)
            cur = []
            x += 1
            continue
        cur.append((x, yy))
        if rng.random() < gap_p / 3:
            if len(cur) > 1:
                out.append(cur)
            cur = []
            x += rng.uniform(gmin, gmax)
            continue
        x += 1.5
    if len(cur) > 1:
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------------
# figures
# ------------------------------------------------------------------------------------------------

def _heron(cv, fx, fy, s, rng, detail=1.):
    """Great blue heron standing, facing left, feet at (fx, fy), about s px tall."""
    P = lambda pts: _xf(pts, fx, fy, s)
    lw = max(.5, s * .006)
    # legs (behind body), in the water
    for dx in (0., .07):
        cv.obj([P([(dx - .008, -.03), (dx + .02, -.5), (dx + .036, -.5), (dx + .008, -.03)])], .5)
        cv.line(P([(dx, -.03), (dx + .016, -.27), (dx + .03, -.5)]))
        cv.heavy(P([(dx + .012, -.25), (dx + .02, -.27)]))
    # tail plumes hanging back
    tail = P([(.16, -.47), (.33, -.36), (.31, -.33), (.27, -.35), (.25, -.31), (.12, -.43)])
    cv.obj([tail], 1.)
    cv.hair(hatch_poly(tail, 40, 1.5))
    # body: tilted teardrop
    bc = (fx + .05 * s, fy - .56 * s)
    body = []
    for i in range(40):
        t = TAU * i / 40
        rx = .2 * s * (1 + .18 * math.cos(t))
        body.append((bc[0] + rx * math.cos(t), bc[1] + .085 * s * math.sin(t)))
    body = _rot(body, bc[0], bc[1], math.radians(26))
    cv.obj([body], 1.)
    # feather contour lines following the body (bulino), dense on the belly
    for k in range(1, 8):
        f = 1 - k * .11
        ring = []
        for i in range(0, 41):
            t = math.pi * .05 + math.pi * .9 * i / 40
            rx = .2 * s * f * (1 + .18 * math.cos(t))
            ring.append((bc[0] + rx * math.cos(t), bc[1] + .085 * s * f * math.sin(t) + .012 * s * (1 - f)))
        cv.hair(_rot(ring, bc[0], bc[1], math.radians(26)))
    # the wing: dark folded wing over the back with primaries
    wing = []
    for i in range(30):
        t = math.pi + math.pi * i / 29
        wing.append((bc[0] + .03 * s + .19 * s * math.cos(t), bc[1] - .005 * s + .06 * s * math.sin(t)))
    wing += [(bc[0] + .26 * s, bc[1] + .04 * s), (bc[0] + .2 * s, bc[1] + .045 * s), (bc[0] - .12 * s, bc[1] + .02 * s)]
    wing = _rot(wing, bc[0], bc[1], math.radians(26))
    cv.obj([wing], 1.)
    cv.hair(hatch_poly(wing, 22, 1.5))
    cv.hair(hatch_poly(wing, -30, 3))
    for k in range(4):   # primary tips
        a = bc[0] + (.08 + k * .045) * s
        cv.line(_rot([(a, bc[1] + .0 * s), (a + .07 * s, bc[1] + .045 * s)], bc[0], bc[1], math.radians(26)))
    # neck: an S rib
    neck = [(-.08, -.6), (-.12, -.66), (-.1, -.72), (-.04, -.77), (-.03, -.82), (-.07, -.87), (-.1, -.92), (-.09, -.96)]
    pts = []
    for i in range(len(neck) - 1):
        for j in range(5):
            t = j / 5
            pts.append((neck[i][0] + (neck[i + 1][0] - neck[i][0]) * t, neck[i][1] + (neck[i + 1][1] - neck[i][1]) * t))
    pts.append(neck[-1])
    pts = P(pts)
    nn = len(pts)
    wl = [s * (.06 - .03 * i / nn) for i in range(nn)]
    R = _Rib(pts, wl, wl)
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(.55, 0., 1.))
    cv.hair(R.contour(.8, 0., 1.))
    cv.line(R.contour(-.5, .05, .95))          # the dark stripe down the front of the neck
    cv.hair(R.contour(-.75, 0., 1.))
    # breast plumes hanging from the neck base
    for k in range(7):
        x0 = fx + (-.17 + k * .02) * s
        cv.hair([(x0, fy - .62 * s), (x0 - .01 * s, fy - (.5 - .01 * k) * s)])
    # head and bill
    hx, hy = fx - .09 * s, fy - .965 * s
    head = _ell_pts(hx, hy, .05 * s, .032 * s, 24)[:-1]
    bill = [(hx - .03 * s, hy - .012 * s), (hx - .25 * s, hy + .022 * s), (hx - .03 * s, hy + .016 * s)]
    cv.obj([bill], 1.)
    cv.hair([(hx - .03 * s, hy + .004 * s), (hx - .22 * s, hy + .02 * s)])
    cv.obj([head], 1.)
    cv.hair(hatch_poly(head, 0, 1.5))
    crest = [(hx - .01 * s, hy - .02 * s), (hx + .16 * s, hy - .035 * s), (hx + .17 * s, hy - .025 * s), (hx + .02 * s, hy - .004 * s)]
    cv.obj([crest], 0)
    _solid(cv, crest, .8, -5)
    eye = _ell_pts(hx - .015 * s, hy - .002 * s, max(1., .009 * s), max(1., .009 * s), 10)[:-1]
    cv.obj([eye], 0)
    cv.line(_ell_pts(hx - .015 * s, hy - .002 * s, max(.5, .005 * s), max(.5, .005 * s), 8))


def _dog(cv, fx, fy, s, facing=-1):
    """Parker's dog, sitting on the bank watching the heron, about s px tall; fur in bulino ruling,
    a floppy black ear, a white eye."""
    T = lambda pts: [(fx - facing * x * s, fy + y * s) for x, y in pts]
    body = T([(.22, 0), (.25, -.2), (.2, -.42), (.1, -.6), (.07, -.8), (.0, -.9), (-.1, -.89), (-.2, -.83),
              (-.29, -.79), (-.3, -.74), (-.22, -.7), (-.12, -.68), (-.12, -.5), (-.1, -.25), (-.1, 0),
              (-.03, 0), (-.02, -.25), (.04, -.15), (.08, 0)])
    tail = T([(.2, -.03), (.36, -.06), (.42, -.02), (.38, .0), (.2, .0)])
    cv.obj([tail], 1.)
    cv.hair(hatch_poly(tail, 80, 1.5))
    cv.obj([body], 1.)
    cv.hair(hatch_poly(body, 75, 1.5))
    cv.hair(hatch_poly(T([(.25, -.05), (.22, -.4), (.1, -.6), (.12, -.2), (.2, -.02)]), -20, 1.5))
    ear = T([(.03, -.85), (.08, -.66), (.02, -.62), (-.03, -.8)])
    cv.obj([ear], 1.)
    _solid(cv, ear)
    nose = T([(-.3, -.77), (-.27, -.75), (-.3, -.73)])
    cv.obj([nose], 1.)
    _solid(cv, nose, .6)
    ex, ey = T([(-.12, -.8)])[0]
    cv.obj([_ell_pts(ex, ey, 1.2, 1.2, 8)[:-1]], 1.)
    cv.line([(ex - .2, ey), (ex + .2, ey)])
    cv.line(T([(-.1, -.5), (-.1, -.02)]))


def _barn(cv, bx, by, s, rng):
    """Gambrel-roofed island barn, base centre (bx, by), s px tall, boarded walls, a flag on a pole."""
    w = s * 1.15
    wall = [(bx - w / 2, by), (bx - w / 2, by - s * .5), (bx + w / 2, by - s * .5), (bx + w / 2, by)]
    roof = [(bx - w / 2 - s * .05, by - s * .5), (bx - w * .36, by - s * .82), (bx, by - s), (bx + w * .36, by - s * .82),
            (bx + w / 2 + s * .05, by - s * .5)]
    cv.obj([wall], 1.)
    cv.hair(hatch_poly(wall, 90, 1.5))           # board siding
    cv.obj([roof], 1.)
    cv.hair(hatch_poly(roof, 0, 1.5))
    cv.hair(hatch_poly(roof, 60, 3))
    door = [(bx - s * .17, by), (bx - s * .17, by - s * .34), (bx + s * .17, by - s * .34), (bx + s * .17, by)]
    cv.obj([door], 1.)
    cv.hair(hatch_poly(door, 90, 3))
    cv.line([door[0], door[2]])
    cv.line([door[1], door[3]])
    loft = [(bx - s * .08, by - s * .58), (bx - s * .08, by - s * .72), (bx + s * .08, by - s * .72), (bx + s * .08, by - s * .58)]
    cv.obj([loft], 1.)
    _solid(cv, loft)
    # crossed drumsticks leaning on the wall (Easter egg)
    if s > 30:
        sx = bx + w * .34
        cv.line([(sx - s * .08, by), (sx + s * .06, by - s * .3)])
        cv.line([(sx + s * .08, by), (sx - s * .06, by - s * .3)])
        for q in ((sx + s * .06, by - s * .3), (sx - s * .06, by - s * .3)):
            cv.obj([_ell_pts(q[0], q[1], 1.2, 1.2, 8)[:-1]], 1.)
    # flag pole and flag, waving right
    px = bx - w / 2 - s * .35
    top = by - s * 1.55
    cv.obj([[(px - .7, by), (px - .7, top), (px + .7, top), (px + .7, by)]], .5)
    cv.line([(px, by), (px, top)])
    cv.obj([_ell_pts(px, top - 1, 1.3, 1.3, 8)[:-1]], 1.)
    fw, fh = s * .62, s * .38
    def fp(u, v):
        return (px + .8 + u * fw, top + 1 + v * fh + math.sin(u * 5.5) * fh * .12 * u)
    outline = [fp(i / 20, 0) for i in range(21)] + [fp(1 - i / 20, 1) for i in range(21)]
    cv.obj([outline], 1.)
    for k in range(7):   # seven red stripes as dense ruling
        v0, v1 = (2 * k) / 13, (2 * k + 1) / 13
        for vv in (v0 + (v1 - v0) * .25, v0 + (v1 - v0) * .75) if fh > 20 else ((v0 + v1) / 2,):
            cv.hair([fp(i / 20, vv) for i in range(21)] if k < 4 and False else [fp(i / 20, vv) for i in range(21)])
    canton = [fp(i / 20 * .42, 0) for i in range(9)] + [fp(.42 - i / 20 * .42, 7 / 13) for i in range(9)]
    cv.obj([canton], .5)
    cv.hair(hatch_poly(canton, 45, 1.5))
    cv.hair(hatch_poly(canton, -45, 1.5))


def _hood(cv, cx, base, H, rng):
    """Mt. Hood: a sharp summit, glaciers, the east face shaded."""
    L = [(cx - H * 1.9, base), (cx - H * 1.2, base - H * .3), (cx - H * .7, base - H * .55), (cx - H * .35, base - H * .78),
         (cx - H * .12, base - H * .93), (cx, base - H), (cx + H * .08, base - H * .92), (cx + H * .28, base - H * .8),
         (cx + H * .45, base - H * .62), (cx + H * .7, base - H * .5), (cx + H * 1.3, base - H * .25), (cx + H * 2., base)]
    cv.obj([L], 1.)
    # snowline: ragged; below it forested slopes dense
    sl = []
    for i in range(25):
        u = i / 24
        x = cx - H * 1.25 + u * H * 2.3
        y = base - H * (.32 + .1 * math.sin(u * 9 + 1) + .06 * rng.random())
        sl.append((x, y))
    low = [(cx - H * 1.9, base)] + sl + [(cx + H * 2., base)]
    lowp = [p for p in low]
    cv.obj([lowp], 0)
    cv.hair(hatch_poly(lowp, 0, 1.5))
    cv.hair(hatch_poly(lowp, 70, 3))
    cv.hair(L)
    # shaded east face: diagonal hatch from summit
    east = [(cx, base - H), (cx + H * .08, base - H * .92), (cx + H * .28, base - H * .8), (cx + H * .45, base - H * .62),
            (cx + H * .7, base - H * .5), (cx + H * .9, base - H * .42), (cx + H * .1, base - H * .45)]
    cv.hair(hatch_poly(east, 65, 2))
    # glaciers / couloirs on the lit face
    for k in range(6):
        a = cx - H * (.05 + k * .13)
        cv.hair([(cx - H * .02 * k, base - H * (.97 - .05 * k)), (a - H * .05, base - H * (.55 - .02 * k))])
    cv.hair(hatch_poly([(cx, base - H), (cx - H * .7, base - H * .55), (cx - H * .9, base - H * .45), (cx - H * .2, base - H * .5)], 0, 3))


def _treeline(cv, x0, x1, hz, th, rng):
    """Far shore: a row of firs and cottonwoods sitting on the horizon."""
    top = []
    x = x0
    while x <= x1:
        kind = rng.random()
        if kind < .6:   # fir: a spire
            hh = th * rng.uniform(.6, 1.)
            ww = hh * .35
            top += [(x, hz - hh * .25), (x + ww / 2, hz - hh), (x + ww, hz - hh * .25)]
            x += ww * rng.uniform(.6, .9)
        else:           # round cottonwood
            r = th * rng.uniform(.3, .5)
            for i in range(7):
                a = math.pi + math.pi * i / 6
                top.append((x + r + r * math.cos(a), hz - th * .25 - r * .8 + r * .8 * math.sin(a) * 1.2))
            x += 2 * r
    top = [(x0, hz)] + [(min(max(p[0], x0), x1), p[1]) for p in top] + [(x1, hz), (x1, hz + 2), (x0, hz + 2)]
    cv.obj([top], .5)
    cv.hair(hatch_poly(top, 0, 1.5))
    cv.hair(hatch_poly(top, 70, 2))
    cv.line([(x0, hz + 1), (x1, hz + 1)])


# ------------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------------

def scene(x, y, w, h, clip_d, seed=0, detail=1.):
    """The page's subject inside the box, clipped to clip_d. Fills every pixel with engraving."""
    rng = random.Random(seed)
    cv = Canvas()
    hz = y + h * (.6 if h > 60 else .62)
    box = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    # sky: ruled, darkest at the top
    cv.obj([], 0)
    bands = [(y - 2, y + h * .14, 1.5), (y + h * .14, y + h * .34, 2.), (y + h * .34, hz + 1, 3.)]
    for a, b, p in bands:
        cv.hair(hatch_poly([(x - 2, a), (x + w + 2, a), (x + w + 2, b), (x - 2, b)], 0, p, a % p))
    # the sun, low and veiled, golden light breaking through in rays
    sx, sy = x + w * .6, hz - h * .17
    sr = max(5., min(w, h) * .085)
    nr = 15
    for i in range(nr):
        if i % 2:
            continue
        a0 = math.pi + math.pi * (i + .1) / nr
        a1 = math.pi + math.pi * (i + .9) / nr
        R = max(w, h) * 1.2
        wedge = [(sx + sr * 1.15 * math.cos(a0), sy + sr * 1.15 * math.sin(a0)), (sx + R * math.cos(a0), sy + R * math.sin(a0)),
                 (sx + R * math.cos(a1), sy + R * math.sin(a1)), (sx + sr * 1.15 * math.cos(a1), sy + sr * 1.15 * math.sin(a1))]
        cv.obj([wedge], 0)
        am = (a0 + a1) / 2
        for f in (-.28, 0., .28):
            aa = am + f * (a1 - a0)
            cv.hair([(sx + sr * 1.4 * math.cos(aa), sy + sr * 1.4 * math.sin(aa)), (sx + R * math.cos(aa), sy + R * math.sin(aa))])
        cv.hair(hatch_poly(wedge, 0, 3, 1.5))
    disc = _ell_pts(sx, sy, sr, sr, 40)[:-1]
    cv.obj([disc], 1.)
    cv.hair(hatch_poly(disc, 0, 3, .5))
    cv.hair(_ell_pts(sx, sy, sr * 1.15, sr * 1.15, 40))
    # cloud banks, far to near
    clouds = []
    rows = [(.2, .5, 1.0), (.36, .7, .9), (.5, .55, .75)] if h > 90 else [(.32, .6, .8)]
    sun_gap = (sx - sr * 2.2, sx + sr * 2.2)
    for row, (vv, cover, sc) in enumerate(rows):
        base = y + h * vv
        xx = x - w * .1 + rng.uniform(0, w * .15)
        while xx < x + w:
            cw = w * rng.uniform(.18, .34) * sc
            if rng.random() < cover and not (row == len(rows) - 1 and xx < sun_gap[1] and xx + cw > sun_gap[0]):
                r0 = max(4., h * .09 * sc)
                puffs = []
                px = xx
                while px < xx + cw:
                    r = r0 * rng.uniform(.6, 1.15)
                    puffs.append((px + r * .6, r))
                    px += r * rng.uniform(.8, 1.2)
                clouds.append((base, xx, px + r0 * .3, puffs))
            xx += cw * rng.uniform(.9, 1.3)
    for base, cx0, cx1, puffs in clouds:
        poly = _cloud_poly(min(c - r for c, r in puffs) + .5, max(c + r for c, r in puffs) - .5, base, puffs)
        cv.obj([poly], .5)
        # light upper ruling, inset to keep a lit rim
        cv.hair(hatch_poly(poly, 0, 3, 1., inset=2.))
        # dark underside
        under = [(cx0, base - (puffs[0][1] * .5)), (cx1, base - (puffs[-1][1] * .5)), (cx1, base + 3), (cx0, base + 3)]
        rm = max(r for _, r in puffs)
        cv.hair([ln for ln in hatch_poly(poly, 0, 3, 2.5, inset=1.) if ln[0][1] > base - rm * .7])
        cv.hair([ln for ln in hatch_poly(poly, 0, 1.5, 1.75, inset=.5) if ln[0][1] > base - rm * .3])
        # puff rims: a contour just inside each puff's lit top
        for pcx, r in puffs:
            if r > 4:
                pcy = base - r * .55
                arc = [(pcx + r * .8 * math.cos(t), pcy - r * .75 * .8 * math.sin(t))
                       for t in [math.radians(a) for a in range(150, 25, -10)]]
                cv.hair([q for q in arc if q[1] < base - 1])
    # Mt. Hood, beyond the channel
    if h > 70:
        _hood(cv, x + w * .74, hz + 1, h * .26, rng)
    # far shore trees
    _treeline(cv, x - 2, x + w + 2, hz + 1, max(4., h * .1), rng)
    # water
    wy0 = hz + 3
    water = [(x - 2, wy0), (x + w + 2, wy0), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([water], 0)
    hx = x + w * .25
    yy = wy0 + 1
    k = 0
    while yy < y + h + 2:
        depth = (yy - wy0) / max(1., y + h - wy0)
        pitch = 2. if depth < .5 else 1.5
        avoid = []
        if yy < wy0 + h * .18:   # the sun's broken reflection
            half = sr * (1.1 - depth)
            avoid = [(sx - half, sx + half)] if k % 2 == 0 else []
        segs = _wavy(x - 2, x + w + 2, yy, .35, 14, rng.random(), rng, .12 + .1 * (1 - depth), avoid=avoid)
        if avoid:
            # short dashes in the reflection column
            dx = sx - avoid[0][0]
            q = sx - dx
            while q < sx + dx:
                L = rng.uniform(1.5, 4)
                segs.append([(q, yy), (q + L, yy)])
                q += L + rng.uniform(1.5, 3)
        cv.hair(segs)
        yy += pitch
        k += 1
    # foreground: the island bank at low tide, mud flats stippled, grass tufts
    by = y + h * .86
    bank = [(x - 2, y + h + 2)]
    for i in range(41):
        u = i / 40
        bank.append((x - 2 + u * (w + 4), by - h * (.05 * math.sin(u * 3.2 + .4) + .04 * (u > .55) * math.sin((u - .55) * 7)) - h * .03 * (u > .6)))
    bank.append((x + w + 2, y + h + 2))
    cv.obj([bank], 1.)
    cv.hair(hatch_poly(bank, 12, 2))
    cv.hair(hatch_poly(bank, -20, 3))
    # mud flat at the water's edge
    for i in range(int(w * .5 * detail)):
        u = rng.random()
        px = x + u * w
        bt = by - h * (.05 * math.sin(u * 3.2 + .4)) + rng.uniform(-1, 1)
        cv.line([(px, bt - 2 + rng.uniform(-1, 1)), (px + rng.uniform(1.5, 3), bt - 2)])
    # grass tufts along the bank's crest
    for i in range(int(w / 3)):
        u = rng.random()
        px = x + u * w
        idx = min(40, int(u * 40 + .5))
        bt = bank[1 + idx][1]
        for j in range(3):
            L = h * rng.uniform(.03, .07)
            a = -math.pi / 2 + rng.uniform(-.5, .5)
            cv.hair([(px + j, bt + 1), (px + j + L * math.cos(a), bt + 1 + L * math.sin(a))])
    # barn with the flag (Veterans Day), dog on the bank
    if h > 70:
        bx = x + w * .84
        bb = bank[1 + int(.84 * 40)][1] + h * .02
        _barn(cv, bx, bb, h * .16, rng)
        _dog(cv, x + w * .6, bank[1 + int(.6 * 40)][1] + h * .02, h * .16, -1)
    # the heron in the shallows, its reflection broken in the water
    if h > 45:
        hs = h * (.52 if h > 120 else .6)
        hy = hz + h * .14
        # reflection
        refl = []
        for k in range(int(hs * .25)):
            ry = hy + 2 + k * 1.5
            L = hs * .12 * (1 - k / (hs * .25))
            refl.append([(hx - L * .5 + rng.uniform(-1, 1), ry), (hx + L * .5 + rng.uniform(-1, 1), ry)])
        cv.line(refl)
        _heron(cv, hx, hy, hs, rng, detail)
        # ripples round the legs
        for k in range(3):
            r = hs * (.04 + .03 * k)
            cv.hair(_ell_pts(hx + hs * .04, hy, r * 2, r * .4, 24)[3:22])
    cid = _uid("v", x, y, w, h, seed)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ------------------------------------------------------------------------------------------------
# bespoke furniture: the sun crest, the star tablet, the toned banner
# ------------------------------------------------------------------------------------------------

def _sun_crest(cx, cy, r, seed):
    """The rising sun above the cartouche: a half disc with alternating long/short rays, palmette
    fingers springing either side."""
    cv = Canvas()
    for side in (-1, 1):
        C.acanthus_frond(cx + side * r * .7, cy + r * .05, 90 - side * 90 - side * 12, r * 1.9, 3, 30, bend=-side * .9, cv=cv, seed=seed + side)
    rays = []
    for i in range(17):
        a = math.pi + math.pi * (i + .5) / 17
        L = r * (1.75 if i % 2 == 0 else 1.35)
        wd = .07
        rays.append([(cx + r * .9 * math.cos(a - wd), cy + r * .9 * math.sin(a - wd)), (cx + L * math.cos(a), cy + L * math.sin(a)),
                     (cx + r * .9 * math.cos(a + wd), cy + r * .9 * math.sin(a + wd))])
    cv.obj(rays, 1.)
    for ry in rays:
        cv.hair([ry[0], ry[1]])
        cv.hair(hatch_poly(ry, 0, 1.5))
    disc = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in [math.pi + math.pi * i / 30 for i in range(31)]]
    cv.obj([disc], 1.)
    cv.hair(_ell_pts(cx, cy, r * .78, r * .78, 30)[15:31])
    cv.hair(hatch_poly(disc, 0, 2, .5, inset=1.5))
    # a face: two closed eyes and a smile, engraved
    for sx in (-1, 1):
        cv.line([(cx + sx * r * .42 - r * .1, cy - r * .42), (cx + sx * r * .42, cy - r * .36), (cx + sx * r * .42 + r * .1, cy - r * .42)])
    cv.line([(cx - r * .25, cy - r * .16), (cx, cy - r * .08), (cx + r * .25, cy - r * .16)])
    return cv.svg()


def _star(cx, cy, r):
    return [(cx + (r if i % 2 == 0 else r * .42) * math.cos(-math.pi / 2 + math.pi * i / 5),
             cy + (r if i % 2 == 0 else r * .42) * math.sin(-math.pi / 2 + math.pi * i / 5)) for i in range(10)]


def _star_tablet(tx, ty, tw, th):
    """Veterans Day: thirteen white stars on a ruled ground across the tablet."""
    o = [f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-tw + 2)}z" fill="{pat("G")}" stroke="none"/>']
    n = 13
    r = min(th * .36, tw / n * .36)
    d = "".join(_d(_star(tx + tw * (i + .5) / n, ty + th / 2 + r * .1, r), True, 0) for i in range(n))
    o.append(f'<path d="{d}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    # laurel ticks between stars
    t = "".join(f"M{_n(tx + tw * i / n)},{_n(ty + th * .3)}v{_n(th * .4)}" for i in range(1, n))
    o.append(f'<path d="{t}" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def _banner_face(cx, cy, w, h, arch, centre):
    top = [(px, py - h / 2 + 1.2) for px, py in centre]
    bot = [(px, py + h / 2 - 1.2) for px, py in centre[::-1]]
    face = f'<path d="{_d(top + bot, True, 0)}" fill="{pat("L")}" stroke="none"/>'
    # a row of small stars along the face for the day
    n = 9
    stars = ""
    r = h * .22
    for i in range(n):
        p = centre[int((i + .5) / n * (len(centre) - 1))]
        stars += _d(_star(p[0], p[1], r), True, 0)
    return face + f'<path d="{stars}" fill="#fff" stroke="#000" stroke-width=".5"/>'


# ------------------------------------------------------------------------------------------------
# layouts (from the house frame_plate, adapted: no bare paper, the vignette fills the whole field)
# ------------------------------------------------------------------------------------------------

def _medallion_scene(cx, cy, rx, ry, seed):
    outer = _ell_pts(cx, cy, rx + 1, ry + 1, 64)
    ring = _d(outer, True) + _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    field = _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o = [f'<path d="{_d(outer, True)}" fill="#fff" stroke="none"/>']
    o.append(scene(cx - rx, cy - ry, rx * 2, ry * 2, field, seed, .6))
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 3.5, ry - 3.5, 64), True)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    return "".join(o)


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(f'<path d="M0,0h{_n(w)}v{_n(top)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>')
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    gap = min(gh * 2.2, 150)
    o.append(_clip(_uid("b", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    o.append(_medallion_scene(w / 2, top + gh / 2, gap / 2, gh / 2 - 1, seed))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = [f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>']
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.7)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = Canvas(), Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    fx0, fx1, fy0, fy1 = _bbox(field)
    o.append(c)
    o.append(scene(fx0, fy0, fx1 - fx0, fy1 - fy0, field, seed, .8))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _bbox(d):
    import re
    # field path is "M x,y l dx,dy ..." in tenths-free numbers; walk it
    nums = re.findall(r"-?\d*\.?\d+", d)
    vals = [float(v) for v in nums]
    x, y = vals[0], vals[1]
    xs, ys = [x], [y]
    for i in range(2, len(vals) - 1, 2):
        x += vals[i]
        y += vals[i + 1]
        xs.append(x)
        ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


def _layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = [f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>']
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .7
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = Canvas(), Canvas()
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
    o.append(_clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    fx0, fx1, fy0, fy1 = _bbox(field)
    o.append(c)
    o.append(scene(fx0, fy0, fx1 - fx0, fy1 - fy0, field, seed, 1.))
    sr = min(ch * .1 + top_free * .5, 34)
    o.append(_sun_crest(cx, cy - ch / 2 + 5, sr, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bw = cw * 1.4
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, bw, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_face(cx, cy + ch * .47, bw, bh, .04, centre))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_star_tablet(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(_clip(_uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                       C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed, .9)
    else:
        body = _layout_tall(w, h, seed, .85)
    return C.svg_doc(w, h, body)
