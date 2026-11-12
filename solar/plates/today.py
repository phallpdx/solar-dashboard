"""Today (the front page: weather, calendar, what to plan for).

Plate: the morning over Sauvie Island. Inside the cartouche the sun breaks under a bank of cloud
beside Mt. Hood, the Columbia runs below it with the sun's glitter on the water, a great blue heron
stands in the shallows and a barn sits on the island bank. The two great flanking volutes curl
into the day's sun (left) and tonight's moon (right, its phase from the date), so the scroll itself
carries the day from sunrise to the Blazers game at night. Tall plates letter the banner
CARPE DIEM and the pedestal tablet with the date in Roman numerals.
Easter egg: the barn's weathervane is a tiny Blazers pinwheel (tonight: Blazers vs. Thunder).
"""
import sys
import math
import random
import datetime
import engraving_codex as C
import engraving_morning as M

TAU = math.pi * 2
_n = C._n
_d = C._d


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def _poly_clip_x(pl, x0, x1):
    return [p for p in pl if x0 <= p[0] <= x1]


def _hrows(poly, pitch, phase=0., inset=0.):
    return C.hatch_poly(poly, 0, pitch, phase, inset)


def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date)
    except Exception:
        d = datetime.date(2026, 11, 11)
    return M._moon_phase(d)


def _roman(n):
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
                 (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s
            n -= v
    return out


# ----------------------------------------------------------------------------------------------
# the scene: morning on the Columbia at Sauvie Island
# ----------------------------------------------------------------------------------------------

def _cloud(cv, xl, xr, yb, hgt, rng, dark=1.):
    """A cumulus bank: bumpy top, soft flat base; contour lines follow the bumps and crowd toward
    the base so the underside goes dark (engraved cloud)."""
    n = max(3, int((xr - xl) / (hgt * .9)))
    bumps = []
    for i in range(n):
        t = (i + .5) / n
        cx = xl + (xr - xl) * t + rng.uniform(-.15, .15) * (xr - xl) / n
        env = math.sin(math.pi * t) ** .6
        r = hgt * (.45 + .55 * env) * rng.uniform(.75, 1.0)
        bumps.append((cx, r))

    def top(x):
        best = yb
        for cx, r in bumps:
            dx = x - cx
            if abs(dx) < r:
                best = min(best, yb - math.sqrt(r * r - dx * dx) * .9)
        return best

    N = int((xr - xl) / 1.2) + 2
    xs = [xl + (xr - xl) * i / (N - 1) for i in range(N)]
    tp = [(x, top(x)) for x in xs]
    base = [(x, yb + .8 * math.sin(x * .21)) for x in xs[::-1]]
    poly = tp + base
    cv.obj([poly], 1.)
    # contour lines below the top, spacing shrinking toward the base
    ds = []
    d = 2.6
    step = 3.
    while True:
        ds.append(d)
        step = max(1.5, step * (.86 if dark > .5 else .92))
        d += step
        if d > hgt * 1.3:
            break
    for d in ds:
        seg = []
        for x, ty in tp[1:-1]:
            y = ty + d
            if y < yb - .9:
                seg.append((x, y))
            else:
                if len(seg) > 1:
                    cv.hair(seg)
                seg = []
        if len(seg) > 1:
            cv.hair(seg)
    # a black shadow line along the base
    cv.line([(x, yb - .6 + .8 * math.sin(x * .21)) for x in xs[2:-2]])
    return poly


def _hood(cv, px, py, s, ybase):
    """Mt. Hood: a snow cone, lit from the left (the sun), shaded right flank, gullies, forest skirt."""
    H = ybase - py
    L = [(px - H * 1.45, ybase), (px - H * 1.0, ybase - H * .22), (px - H * .62, ybase - H * .45),
         (px - H * .34, ybase - H * .68), (px - H * .18, ybase - H * .83), (px - H * .07, ybase - H * .94),
         (px, py)]
    R = [(px + H * .05, py + H * .03), (px + H * .12, ybase - H * .9), (px + H * .2, ybase - H * .8),
         (px + H * .28, ybase - H * .74), (px + H * .45, ybase - H * .58),
         (px + H * .8, ybase - H * .32), (px + H * 1.2, ybase - H * .12), (px + H * 1.6, ybase)]
    out = M._spline(L, False, 3) + M._spline(R, False, 3)[1:]
    poly = out + [(px + H * 1.6, ybase + 2), (px - H * 1.45, ybase + 2)]
    cv.obj([poly], 1.)
    # shaded right flank: hatch at a slope, clipped to a wedge right of the ridge line
    ridge = [(px, py), (px + H * .02, py + H * .3), (px - H * .05, ybase - H * .3), (px + H * .1, ybase)]
    wedge = ridge + [(px + H * 1.7, ybase), (px + H * 1.7, py - 2)]
    sh = [q for q in C.hatch_poly(wedge, 62, 1.5)]
    cv.hair(sh)
    # lit flank: sparse gullies running down from the summit
    rng = random.Random(7)
    for k in range(7):
        t = (k + 1) / 8
        x0 = px - H * .06 * t
        y0 = py + H * (.12 + .1 * t)
        gx = px - H * (.25 + 1.0 * t)
        g = [(x0 + (gx - x0) * u + math.sin(u * 5 + k) * .8, y0 + (ybase - H * (.18 + .1 * rng.random()) - y0) * u ** .9)
             for u in [i / 10 for i in range(11)]]
        # keep inside the cone
        g = [p for p in g if p[1] > _interp_y(out, p[0]) + 1.2]
        if len(g) > 1:
            cv.hair(g)
    # snow line: forest skirt as dense rows on the lower slopes
    sk = [(px - H * 1.5, ybase), (px - H * .9, ybase - H * .25), (px - H * .5, ybase - H * .3),
          (px, ybase - H * .36), (px + H * .5, ybase - H * .33), (px + H * 1.0, ybase - H * .2),
          (px + H * 1.65, ybase), (px + H * 1.65, ybase + 2), (px - H * 1.5, ybase + 2)]
    rows = C.hatch_poly(sk, 0, 1.5)
    cv.hair([r for r in rows])
    return poly


def _interp_y(pl, x):
    best = None
    for i in range(len(pl) - 1):
        (a, b), (c, d) = pl[i], pl[i + 1]
        if (a <= x <= c) or (c <= x <= a):
            y = b if c == a else b + (d - b) * (x - a) / (c - a)
            best = y if best is None else min(best, y)
    return best if best is not None else 1e9


def _treeline(cv, x0, x1, yh, s, rng):
    """The far shore: a ragged line of cottonwoods and firs, dark."""
    pts = []
    x = x0
    while x < x1:
        kind = rng.random()
        if kind < .35:   # fir spike
            w = 3 * s
            pts += [(x, yh - 2 * s), (x + w / 2, yh - (5.5 + 3 * rng.random()) * s), (x + w, yh - 2 * s)]
            x += w
        else:            # rounded crown
            w = (4 + 4 * rng.random()) * s
            hh = (3 + 3 * rng.random()) * s
            for i in range(7):
                t = i / 6
                pts.append((x + w * t, yh - 1.5 * s - hh * math.sin(math.pi * t) ** .7))
            x += w
    poly = pts + [(x1 + 2, yh + 1.2), (x0 - 2, yh + 1.2)]
    cv.obj([poly], 1.)
    cv.line(_hrows(poly, 1.5))
    return poly


def _heron(cv, ox, oy, s, mirror=False):
    """A great blue heron in the shallows (after the house morning plate), feathers in bulino."""
    body = M._chunks([
        [(-20, -40.2), (-15, -40.6), (-11.8, -41.6)],
        [(-11.8, -41.6), (-9, -42.4), (-7.4, -41.4)],
        [(-7.4, -41.4), (-3.4, -43.6), (-.6, -43.6)],
        [(-.6, -43.6), (-5, -42.2), (-6.6, -40.2), (-6.4, -37.6), (-4.6, -34.2), (-3.4, -30.6), (-1.2, -28.2),
         (4, -27.6), (10, -24.6), (16, -18.6)],
        [(16, -18.6), (8, -16.2), (2, -14.8), (-3.4, -16.2), (-6.4, -20.2), (-7.2, -24.6), (-8.6, -29.6),
         (-9.8, -34.4), (-9.6, -38.4), (-11.6, -39.6), (-20, -40.2)]], 4)
    body = M._map(body, ox, oy, s, mirror)
    for leg in ([(0, -14.8), (.6, -7), (-.5, 0)], [(2.6, -15), (3.6, -7), (4.4, 0)]):
        cv.obj([], 0)
        cv.line(M._map(leg, ox, oy, s, mirror))
    cv.obj([body], 1.)
    wing = M._map(M._spline([(-5.6, -22), (-1, -27), (6, -25.6), (13.6, -19), (6, -17), (-1.6, -16.6),
                             (-5.6, -22)], True, 4), ox, oy, s, mirror)
    # breast and back: fine lines along the body
    cv.hair(C.hatch_poly(body, 75 if not mirror else 105, 1.5))
    cv.obj([wing], 1.)
    cv.hair(C.hatch_poly(wing, -28 if not mirror else 208, 1.5))
    cv.hair(C.hatch_poly(wing, 20 if not mirror else 160, 3))
    plume = M._map([(-7.4, -41.4), (-3.4, -43.6), (-.6, -43.6)], ox, oy, s, mirror)
    cv.heavy(plume)
    e = M._map([(-9.6, -40.8)], ox, oy, s, mirror)[0]
    cv.line([(e[0] - .3, e[1]), (e[0] + .3, e[1])])
    # beak shadow
    cv.line(M._map([(-20, -40.2), (-15, -40.6), (-11.8, -41.6)], ox, oy, s, mirror))


def _barn(cv, x, yb, s):
    """A gambrel barn with board-and-batten walls; its weathervane is a Blazers pinwheel."""
    w, h1, h2 = 24 * s, 9 * s, 17 * s
    rf = [(x - 1 * s, yb - h1), (x + w * .12, yb - h1 - 5 * s), (x + w / 2, yb - h2), (x + w * .88, yb - h1 - 5 * s),
          (x + w + 1 * s, yb - h1)]
    wall = [(x, yb), (x, yb - h1), (x + w, yb - h1), (x + w, yb)]
    cv.obj([wall], 1.)
    cv.hair([[(x + i, yb - h1 + .5), (x + i, yb - .3)] for i in [k * 2 for k in range(1, int(w / 2))]])
    dw, dh = w * .34, h1 * .78
    door = [(x + w / 2 - dw / 2, yb), (x + w / 2 - dw / 2, yb - dh), (x + w / 2 + dw / 2, yb - dh), (x + w / 2 + dw / 2, yb)]
    cv.obj([door], 1.)
    cv.line(C.hatch_poly(door, 90, 1.5))
    cv.obj([], 0)
    cv.line([door[0], door[2]])
    cv.line([door[1], door[3]])
    roof = rf + [(x + w + 1 * s, yb - h1 + 1.2), (x - 1 * s, yb - h1 + 1.2)]
    cv.obj([roof], 1.)
    cv.hair(C.hatch_poly(roof, 0, 1.5))
    cv.hair(C.hatch_poly(roof, 70, 3))
    # loft window
    lw = [(x + w / 2 - 2 * s, yb - h1 - 1.5 * s), (x + w / 2 + 2 * s, yb - h1 - 1.5 * s),
          (x + w / 2 + 2 * s, yb - h1 - 5.5 * s), (x + w / 2 - 2 * s, yb - h1 - 5.5 * s)]
    cv.obj([lw], 1.)
    cv.line(C.hatch_poly(lw, 0, 1.))
    # weathervane: pole, arrow and a five-and-five pinwheel
    vx, vy = x + w / 2, yb - h2
    top = vy - 6 * s
    cv.obj([], 0)
    cv.line([(vx, vy), (vx, top)])
    cv.hair([(vx - 3 * s, top + 2.4 * s), (vx + 3 * s, top + 2.4 * s)])
    pr = 2.6 * s
    pc = (vx, top - pr)
    cv.obj([C._ell_pts(pc[0], pc[1], pr + .4, pr + .4, 20)[:-1]], 1.)
    for i in range(5):
        a = TAU * i / 5 - math.pi / 2
        for sg in (1, -1):
            cv.hair([(pc[0] + pr * (.15 + .75 * t) * math.cos(a + sg * (.15 + .9 * t * t)),
                      pc[1] + pr * (.15 + .75 * t) * math.sin(a + sg * (.15 + .9 * t * t))) for t in (0, .33, .66, 1)])


def scene(cv, x, y, w, h, seed, date, compact=False):
    """Draw the morning scene into cv over the box (x, y, w, h); the caller clips it."""
    rng = random.Random(seed)
    s = max(.55, min(w / 135., h / 88.))
    portrait = h > w * 1.05
    yh = y + h * (.6 if portrait else .58)          # horizon (far shore)
    yb = y + h * (.88 if portrait else .86)         # near bank top
    sx = x + w * (.34 if not compact else .4)
    sr = (min(w, h) * (.11 if not compact else .17))
    sy = yh - sr * .35 - 2 * s
    # --- sky: ruled rows broken into a sunburst ---
    cv.obj([], 0)
    nr = 18
    pitch = 2.
    yy = math.floor(y) + 1.          # whole-px rows: each hairline straddles two device rows
    row = 0
    while yy < yh + 1:
        seg = []
        xx = x
        while xx <= x + w + .01:
            dx, dy = xx - sx, yy - sy
            r = math.hypot(dx, dy)
            th = math.atan2(dy, dx)
            lit = (int(math.floor((th / math.pi) * nr + 100)) % 2 == 0)
            gap = r < sr * 1.25 + 1 or (lit and r < sr * 3.6 and row % 2 == 1)
            if gap:
                if len(seg) > 1:
                    cv.hair(seg)
                seg = []
            else:
                seg.append((xx, yy))
            xx += 1.
        if len(seg) > 1:
            cv.hair(seg)
        yy += pitch
        row += 1
    # rays between the burst sectors: fine radial lines from the rim
    rays = []
    for i in range(nr * 2):
        a = math.pi * i / nr
        if math.sin(a) > -.02:
            continue
        r0, r1 = sr * 1.35, sr * (2.6 if i % 2 else 3.3)
        rays.append([(sx + r0 * math.cos(a), sy + r0 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    cv.hair(rays)
    # --- the sun: a lined disc with a flaming rim ---
    disc = C._ell_pts(sx, sy, sr, sr, 48)[:-1]
    cv.obj([disc], 1.5)
    q = sr - 2.
    while q > 1.5:
        cv.hair(C._ell_pts(sx, sy, q, q, max(16, int(q * 4))))
        q -= 2. if q > sr * .55 else 3.
    flames = []
    for i in range(24):
        a = TAU * i / 24
        a2 = a + .13
        flames.append([(sx + (sr + 1.3) * math.cos(a), sy + (sr + 1.3) * math.sin(a)),
                       (sx + (sr + (3.2 if i % 2 else 2.2) * s) * math.cos(a2), sy + (sr + (3.2 if i % 2 else 2.2) * s) * math.sin(a2))])
    cv.obj([], 0)
    cv.line(flames)
    # --- clouds: a bank across the top, one lip drifting over the sun ---
    crng = random.Random(seed * 13 + 1)
    ch = max(9., h * .15)
    clouds = [(x - w * .05, x + w * .3, y + h * .2 + ch * .3), (x + w * .5, x + w * 1.05, y + h * .16 + ch * .4),
              ] + ([] if compact else [(sx - sr * .6, sx + sr * 3.4, sy - sr * 1.75)])
    if portrait:
        clouds.append((x + w * .05, x + w * .55, y + h * .36))
    for xl, xr, cb in clouds:
        _cloud(cv, xl, xr, cb, ch * crng.uniform(.75, 1.0), crng)
    # --- Mt. Hood beyond the river, catching the light ---
    hx = x + w * (.72 if not compact else .74)
    hpk = yh - h * (.3 if not portrait else .2)
    _hood(cv, hx, hpk, s, yh - 1)
    # --- the far shore of trees ---
    _treeline(cv, x - 2, x + w + 2, yh + 1, s, random.Random(seed + 5))
    # --- the Columbia: rippled water, glitter under the sun ---
    water = [(x - 2, yh + 1.5), (x + w + 2, yh + 1.5), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([water], 0)
    wr = random.Random(seed + 9)
    yy = math.floor(yh) + 3.
    k = 0
    while yy < y + h + 2:
        depth = (yy - yh) / max(1., (y + h - yh))
        glit = sr * (.6 + .9 * depth)
        seg = []
        xx = x - 2
        ph = wr.random() * 9
        while xx <= x + w + 2:
            dash = math.sin(xx * .35 / (1 + depth) + ph + k) > -.75
            in_glit = abs(xx - sx) < glit and (math.sin(xx * 1.7 + k * 2.3) > .25 or (abs(xx - sx) < glit * .3 and k % 2))
            if dash and not in_glit:
                seg.append((xx, yy + .35 * math.sin(xx * .5 + k)))
            else:
                if len(seg) > 1:
                    cv.hair(seg)
                seg = []
            xx += 1.
        if len(seg) > 1:
            cv.hair(seg)
        yy += 2.
        k += 1
    # glitter flecks
    gl = []
    for i in range(int(18 * s)):
        gy = yh + 3 + (y + h - yh) * wr.random() ** 1.3
        gx = sx + wr.uniform(-1, 1) * sr * (.6 + .8 * (gy - yh) / max(1, h * .4))
        gl.append([(gx - 1.6, gy), (gx + 1.6, gy)])
    cv.hair(gl)
    # --- the near bank of Sauvie Island ---
    br = random.Random(seed + 3)
    bank = []
    N = 40
    for i in range(N + 1):
        t = i / N
        bx = x - 2 + (w + 4) * t
        rise = (1 - t) ** 1.4 * h * .1 + (t ** 3) * h * .04
        bank.append((bx, yb - rise + math.sin(t * 17 + seed) * 1.2))
    bpoly = bank + [(x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([bpoly], 1.)
    cv.hair(C.hatch_poly(bpoly, 0, 3, 1.))
    meadow = []
    yy0 = yb + 3 * s
    rowk = 0
    while yy0 < y + h + 2:
        xx = x - 2 + br.uniform(0, 3)
        while xx < x + w + 2:
            ty = _interp_y(bank, xx)
            if yy0 > ty + 2.5:
                ln = (1.6 + .5 * rowk) * s * br.uniform(.7, 1.2)
                meadow.append([(xx, yy0), (xx + br.uniform(-.8, .8), yy0 - ln)])
            xx += br.uniform(1.6, 2.6) * (1 + .1 * rowk)
        yy0 += (2.2 + .6 * rowk) * s
        rowk += 1
    cv.hair(meadow)
    tufts = []
    for (bx, by) in bank[1:-1]:
        for j in range(2):
            ox = bx + br.uniform(-1.5, 1.5)
            ln = br.uniform(2.5, 5.) * s
            lean = br.uniform(-1.4, 1.4)
            tufts.append([(ox, by + 1.2), (ox + lean, by - ln)])
    cv.line(tufts)
    # reeds at the water's edge
    reeds = []
    rx0 = x + w * .62
    for i in range(int(10 * s)):
        rx = rx0 + i * 2.6 + br.uniform(-.6, .6)
        ry = _interp_y(bank, rx) + 1
        hh = br.uniform(7, 13) * s
        reeds.append([(rx, ry), (rx + .6, ry - hh * .5), (rx + 1.6 + br.uniform(-.5, 1.2), ry - hh)])
    cv.obj([], 0)
    cv.line(reeds)
    tails = []
    for i, rd in enumerate(reeds):
        if i % 3 == 1:
            tx, ty = rd[1][0] + (rd[2][0] - rd[1][0]) * .55, rd[1][1] + (rd[2][1] - rd[1][1]) * .55
            tails.append([(tx, ty - 1.6 * s), (tx + .2, ty + 1.6 * s)])
    cv.heavy(tails)
    # the barn on the bank, its weathervane a Blazers pinwheel
    bxp = x + w * (.1 if not compact else .08)
    _barn(cv, bxp, _interp_y(bank, bxp + 12 * s) + 2 * s, s * (1.0 if not compact else .7))
    # the heron in the shallows
    hxp = x + w * .58
    _heron(cv, hxp, _interp_y(bank, hxp) - 1.5 * s, s * .82, mirror=False)


def _scene_svg(cid, clip_d, bx, by, bw, bh, seed, date, compact=False):
    cv = C.Canvas()
    scene(cv, bx, by, bw, bh, seed, date, compact)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{cv.svg()}</g>'


# ----------------------------------------------------------------------------------------------
# the volute eyes: sun and moon carved into the scroll
# ----------------------------------------------------------------------------------------------

def _sun_eye(cv, cx, cy, r):
    disc = C._ell_pts(cx, cy, r, r, 40)[:-1]
    flames = []
    for i in range(16):
        a = TAU * i / 16
        L = r * (1.55 if i % 2 == 0 else 1.32)
        w = .32 if i % 2 == 0 else .24
        tip = (cx + L * math.cos(a + .18), cy + L * math.sin(a + .18))
        flames.append([(cx + r * .9 * math.cos(a - w), cy + r * .9 * math.sin(a - w)),
                       (cx + r * 1.2 * math.cos(a - w * .2), cy + r * 1.2 * math.sin(a - w * .2)), tip,
                       (cx + r * 1.15 * math.cos(a + w * .9), cy + r * 1.15 * math.sin(a + w * .9)),
                       (cx + r * .9 * math.cos(a + w), cy + r * .9 * math.sin(a + w))])
    for f in flames:
        cv.obj([f], 1.)
        cv.hair([f[0], f[2]])
    cv.obj([disc], 1.5)
    q = r - 1.8
    while q > 1.2:
        cv.hair(C._ell_pts(cx, cy, q, q, max(12, int(q * 4))))
        q -= 2.
    # a small engraved face: brows, eyes, nose, smile
    k = r / 10.
    cv.obj([C._ell_pts(cx, cy, r * .62, r * .62, 30)[:-1]], 0)
    for sg in (-1, 1):
        cv.line([(cx + sg * 4.6 * k, cy - 3.2 * k), (cx + sg * 3.0 * k, cy - 3.9 * k), (cx + sg * 1.3 * k, cy - 3.2 * k)])
        cv.heavy([(cx + sg * 3.0 * k - .4, cy - 1.8 * k), (cx + sg * 3.0 * k + .4, cy - 1.8 * k)])
    cv.line([(cx - .3 * k, cy - 2.6 * k), (cx - 1.0 * k, cy + .9 * k), (cx + .6 * k, cy + 1.2 * k)])
    cv.line([(cx - 3.0 * k, cy + 2.6 * k), (cx, cy + 3.8 * k), (cx + 3.0 * k, cy + 2.6 * k)])
    cv.hair([[(cx + sg * 5.4 * k, cy + .6 * k), (cx + sg * 4.6 * k, cy + 3.4 * k)] for sg in (-1, 1)])


def _moon_eye(cv, cx, cy, r, phase):
    """Tonight's moon in the volute's eye: the dark disc ruled, the lit limb white and contoured,
    a ring of earthshine round it."""
    disc = C._ell_pts(cx, cy, r, r, 40)[:-1]
    cv.obj([C._ell_pts(cx, cy, r + 2.6, r + 2.6, 40)[:-1]], 0)
    cv.hair(C._ell_pts(cx, cy, r + 1.6, r + 1.6, 40))
    cv.obj([disc], 1.5)
    waxing = phase < .5
    f = phase if waxing else 1 - phase           # 0 new .. .5 full
    f = min(.5, max(.12, f))
    c = math.cos(TAU * f)
    sg = 1 if waxing else -1                      # lit limb on the right when waxing
    N = 32
    term = []
    for i in range(N + 1):
        yy = -r + 2 * r * i / N
        hw = math.sqrt(max(0., r * r - yy * yy))
        term.append((cx + sg * c * hw, cy + yy))
    limb_dark = []
    for i in range(N + 1):
        yy = r - 2 * r * i / N
        hw = math.sqrt(max(0., r * r - yy * yy))
        limb_dark.append((cx - sg * hw, cy + yy))
    shadow = term + limb_dark
    cv.hair(C.hatch_poly(shadow, 0, 1.5))
    # contour lines in the lit crescent, following the limb
    for k in (.25, .5, .72):
        pl = []
        for i in range(1, N):
            yy = -r + 2 * r * i / N
            hw = math.sqrt(max(0., r * r - yy * yy))
            xl, xt = cx + sg * hw, cx + sg * c * hw
            pl.append((xt + (xl - xt) * (1 - k * .5) if False else xl - sg * (hw - c * hw) * k * .55, cy + yy))
        cv.hair(pl)
    cv.line(term)


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, with the cartouche field fully engraved and figures grown in)
# ----------------------------------------------------------------------------------------------

def _medium(w, h, seed, date, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.6)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        a0, flip = (90, True) if side < 0 else (90, False)
        C._volute(main, vx, vy, r, a0, 1.25, flip, random.Random(seed * 3 + side), .9, -.5, r * .15, 3,
                  False, 1., .42)
        eyes.append((vx, vy))
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    er = r * .27
    _sun_eye(cv, eyes[0][0], eyes[0][1], er)
    _moon_eye(cv, eyes[1][0], eyes[1][1], er * 1.05, _moon_phase(date))
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), inner_d = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(_scene_svg(C._uid("ms", w, h, seed), inner_d, cx - a, cy - b, 2 * a, 2 * b, seed, date))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _band(w, h, seed, date):
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
    ia, ib = rx - 3.5, ry - 3.5
    clip = _d(C._ell_pts(cx, cy, ia, ib, 64), True)
    o.append(_scene_svg(C._uid("bs", w, h, seed), clip, cx - ia, cy - ib, 2 * ia, 2 * ib, seed, date, True))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
    return "".join(o)


def _letter(cv, s, cx, cy, hgt, weight="line"):
    polys, wd = M._text_polys(s, cx, cy - hgt / 2, hgt, 1.5, True)
    cv.obj([], 0)
    (cv.heavy if weight == "heavy" else cv.line)(polys)


def _tall(w, h, seed, date, density=.85):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .62
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .24)
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .6)
        vy = py0 + ph - r1 * 1.15
        a0, flip = (100, True) if side < 0 else (80, False)
        C._volute(main, vx, vy, r1, a0, 1.3, flip, random.Random(seed * 5 + side), .8, -.5, r1 * .15, 3,
                  False, 1., .42)
        eyes.append((vx, vy))
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    er = r1 * .27
    _sun_eye(cv, eyes[0][0], eyes[0][1], er)
    _moon_eye(cv, eyes[1][0], eyes[1][1], er * 1.05, _moon_phase(date))
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene_svg(C._uid("ts", w, h, seed), inner_d, cx - a, cy - b, 2 * a, 2 * b, seed, date))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lv = C.Canvas()
    mid = centre[len(centre) // 2]
    _letter(lv, "CARPE DIEM", mid[0], mid[1] + .5, bh * .5)
    o.append(lv.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    try:
        d = datetime.date.fromisoformat(date)
    except Exception:
        d = datetime.date(2026, 11, 11)
    tv = C.Canvas()
    tv.obj([[(tx + 2, ty + 2), (tx + tw - 1, ty + 2), (tx + tw - 1, ty + th - 1), (tx + 2, ty + th - 1)]], 0)
    tv.hair(C.hatch_poly([(tx + 2, ty + 2), (tx + tw - 1, ty + 2), (tx + tw - 1, ty + th - 1), (tx + 2, ty + th - 1)], 0, 3))
    lh = min(th * .5, 11)
    txt = f"{_roman(d.day)} · {_roman(d.month)} · {_roman(d.year)}"
    polys, wd = M._text_polys(txt, tx + tw / 2, ty + th / 2 - lh / 2, lh, 1.6, True)
    # clear a band behind the lettering, then letter it
    tv.obj([[(tx + tw / 2 - wd / 2 - 4, ty + th / 2 - lh / 2 - 2.5), (tx + tw / 2 + wd / 2 + 4, ty + th / 2 - lh / 2 - 2.5),
             (tx + tw / 2 + wd / 2 + 4, ty + th / 2 + lh / 2 + 2.5), (tx + tw / 2 - wd / 2 - 4, ty + th / 2 + lh / 2 + 2.5)]], 0)
    tv.heavy(polys)
    o.append(tv.svg())
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date") or "2026-11-11"
    seed = sum(map(ord, date)) + 31 * int(ctx.get("sheet") or 0 if (ctx.get("sheet") or 0) >= 0 else 0)
    if h < 110:
        body = _band(w, h, seed, date)
    elif h <= 260:
        body = _medium(w, h, seed, date)
    else:
        body = _tall(w, h, seed, date, 1. if h >= 440 else .85)
    # the page's own diagonal ground, carried under the plate wherever the ornament breaks free
    base = ('<defs><pattern id="tdyD" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(-40)">'
            '<path d="M0,1.5H3" stroke="#000" stroke-width=".5"/></pattern></defs>'
            f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="url(#tdyD)" stroke="none"/>')
    return C.svg_doc(w, h, base + body)
