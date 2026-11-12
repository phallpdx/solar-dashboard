"""markets-03 -- Portland real estate.
An old Portland Craftsman house in three-quarter view: a steep front gable with shingled peak and
attic window, a deep porch on tapered columns, clapboard walls, a brick chimney, rhododendrons at the
foundation and a brick walk down the lawn. Behind it Douglas firs, Mount Hood on the right, and on the
left the Gothic towers of the St. Johns Bridge over the Willamette (the page names St. Johns).
The house sits in the codex cartouche between the big volutes; on tall plates a house key lies on
the pedestal tablet (its bow a carved volute), and the ribbon is ruled.
Easter egg: Parker's dog sits on the porch beside the steps, waiting at the door.
"""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, _n, _d, _ell_pts, pat, dark_ground

PI = math.pi


# ------------------------------------------------------------------ geometry helpers
def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def quad_lines(q, pitch_px, along=True):
    """Lines across a quad q=[p0,p1,p2,p3] (p0-p1 top edge, p3-p2 bottom edge): if along, lines run
    p0->p1 direction, spaced down the p0->p3 / p1->p2 sides; else run p0->p3 direction, spaced across."""
    p0, p1, p2, p3 = q
    if along:
        L = max(math.dist(p0, p3), math.dist(p1, p2))
        n = max(1, int(L / pitch_px))
        return [[lerp(p0, p3, i / n), lerp(p1, p2, i / n)] for i in range(1, n)]
    L = max(math.dist(p0, p1), math.dist(p3, p2))
    n = max(1, int(L / pitch_px))
    return [[lerp(p0, p1, i / n), lerp(p3, p2, i / n)] for i in range(1, n)]


def solid(cv, poly, w=1.5):
    """Black fill as tight heavy hatch (Canvas has white fills only)."""
    cv.heavy(hatch_poly(poly, 0, 1.25))


def bez(p0, p1, p2, p3, n=10):
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


_DOG_SIT = ("M.6,0C-.4,-1.6 -.2,-4 1.4,-5.2C2.6,-6 3.6,-6.6 4.3,-7.7L4.6,-9.5C4.8,-10.5 5.9,-10.9 6.7,-10.5"
            "L7.3,-9.7L8.9,-9.3C9.6,-9.1 9.6,-8.2 8.9,-8L7.4,-7.6C6.9,-6.6 6.9,-5.3 7,-4.3L7.2,-.4L7.8,0"
            "H5.9L5.8,-3.2L4.4,-1.6L4.6,-.4L5.2,0Z")


def flatten(d):
    import re
    toks = re.findall(r"[MLCHVZ]|-?\d*\.?\d+", d)
    pts, i, cmd, cur = [], 0, None, (0, 0)
    while i < len(toks):
        t = toks[i]
        if t in "MLCHVZ":
            cmd = t
            i += 1
            if cmd == "Z":
                continue
        if cmd in "ML":
            cur = (float(toks[i]), float(toks[i + 1]))
            pts.append(cur)
            i += 2
        elif cmd == "H":
            cur = (float(toks[i]), cur[1])
            pts.append(cur)
            i += 1
        elif cmd == "V":
            cur = (cur[0], float(toks[i]))
            pts.append(cur)
            i += 1
        elif cmd == "C":
            c = [(float(toks[i + k]), float(toks[i + k + 1])) for k in (0, 2, 4)]
            pts += bez(cur, c[0], c[1], c[2], 6)
            cur = c[2]
            i += 6
        else:
            i += 1
    return pts


DOG = flatten(_DOG_SIT)


# ------------------------------------------------------------------ the scene
def scene(field, seed=0, tall=False):
    """Draw the Portland house scene filling `field` (polygon). Returns svg fragment (Canvas)."""
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
    FW, FH = fx1 - fx0, fy1 - fy0
    s = min(FW / 168., FH / 108.)
    if tall:
        s = min(FW / 172., FH / 136.)
    ox = (fx0 + fx1) / 2
    oy = (fy0 + fy1) / 2 + (-8 * s if tall else -2 * s)
    rng = random.Random(seed)

    def P(x, y):
        return (ox + x * s, oy + y * s)

    def PL(pts):
        return [P(x, y) for x, y in pts]

    cv = Canvas()
    BIGL, BIGR = -400, 400
    yb = (fy1 - oy) / s + 4     # field bottom in design units
    yt = (fy0 - oy) / s - 4

    # ---- sky: bulino ruling, heavier toward the zenith, a morning sun rising behind Mount Hood
    cv.obj([field], 0)
    sky = PL([(BIGL, yt), (BIGR, yt), (BIGR, 16), (BIGL, 16)])
    cv.hair(hatch_poly(sky, 0, 2, .5))
    zen = PL([(BIGL, yt), (BIGR, yt), (BIGR, -44), (60, -48), (0, -46), (-60, -50), (BIGL, -47)])
    cv.line(hatch_poly(zen, 0, 2, .5))
    sx, sy, sr = 80, -40, 8.5
    # the glow: a lighter disc of sky with rays
    glow = _ell_pts(*P(sx, sy), 46 * s, 40 * s, 60)
    cv.obj([glow], 0)
    cv.hair(hatch_poly(glow, 0, 3, .5))
    rays = []
    for i in range(48):
        a = 2 * PI * i / 48
        r0, r1 = sr + 2.5, (44 if i % 2 else 30) + (6 if i % 4 == 1 else 0)
        rays.append([P(sx + r0 * math.cos(a), sy + r0 * math.sin(a) * .9), P(sx + r1 * math.cos(a), sy + r1 * math.sin(a) * .88)])
    cv.hair(rays)
    halo = _ell_pts(*P(sx, sy), 47 * s, 41 * s, 60)
    cv.hair([halo + [halo[0]]])
    disc = _ell_pts(*P(sx, sy), sr * s, sr * s, 40)
    cv.obj([disc], 1.)
    cv.hair(hatch_poly(disc, 0, 3, 1.))
    # long low winter clouds drifting across the glow
    for (cx, cy, cw, ch) in ((-62, -38, 44, 5), (14, -54, 52, 6), (54, -22, 30, 4)) + (((-30, -72, 50, 8), (70, -80, 40, 6)) if tall else ()):
        top = [(cx - cw / 2 + cw * i / 24, cy - ch * (.5 + .5 * abs(math.sin(i * .9 + cx))) * math.sin(PI * i / 24)) for i in range(25)]
        cl = PL(top + [(cx + cw / 2 + 3, cy + 1), (cx - cw / 2 - 3, cy + 1)])
        cv.obj([cl], .5)
        cv.hair(hatch_poly(cl, 0, 3, (cy * s) % 3))
        cv.hair(hatch_poly(PL([(cx - cw / 2 - 3, cy - ch * .3), (cx + cw / 2 + 3, cy - ch * .3), (cx + cw / 2 + 3, cy + 1), (cx - cw / 2 - 3, cy + 1)]), 0, 1.5, .75))

    # ---- Mount Hood
    HX = 20
    peak = (54 + HX, -44)
    left = [(-20 + HX, 16), (0 + HX, 6), (14 + HX, -4), (26 + HX, -16), (36 + HX, -26), (44 + HX, -34), (49 + HX, -40), peak]
    right = [(58 + HX, -41), (63 + HX, -36), (70 + HX, -28), (80 + HX, -18), (94 + HX, -6), (112 + HX, 6), (130 + HX, 16)]
    hood = PL(left + right)
    cv.obj([hood], 1.)
    snow = [(16, -6), (22, -12), (26, -10), (31, -18), (35, -15), (39, -24), (43, -20), (47, -30), (51, -24),
            (56, -31), (60, -22), (66, -27), (71, -17), (77, -20), (84, -10), (92, -12), (104, 0), (130, 16)]
    snow = [(x + HX, y) for x, y in snow]
    below = PL([(-20 + HX, 16)] + snow + [(150, 30), (-20, 30)])
    cv.hair(hatch_poly(below, 35, 2))
    cv.hair(hatch_poly(below, -35, 3))
    # east face in shadow
    east = PL([(x + HX if i else x, y) for i, (x, y) in enumerate([peak, (58, -41), (63, -36), (70, -28), (80, -18), (94, -6), (112, 6), (60, 6), (57, -20)])])
    cv.hair(hatch_poly(east, 60, 2))
    # glacier ridges on the lit snow
    for k in range(7):
        a = (peak[0] - 2 - k * 1.2, peak[1] + 3 + k * 2.2)
        b = (a[0] - 6 - k * 4, a[1] + 10 + k * 1.5)
        cv.hair([P(*a), P(*lerp(a, b, .5)), P(b[0] + 1, b[1])])
    cv.line([P(*peak), P(57 + HX, -30), P(58 + HX, -20)])
    # rock ribs on the west face
    for k in range(5):
        a = (peak[0] - 5 - k * 6, peak[1] + 8 + k * 6)
        cv.hair([P(*a), P(a[0] - 3, a[1] + 4), P(a[0] - 2, a[1] + 8)])

    # ---- Forest Park ridge (left) and the Willamette
    ridge = [(BIGL, 16)] + [(x, 2 - 3 * math.sin(x * .05) - 2 * math.sin(x * .13 + 1)) for x in range(-130, 31, 5)] + [(30, 16)]
    rp = PL(ridge)
    cv.obj([rp], .5)
    cv.hair(hatch_poly(rp, 0, 1.5))
    cv.hair(hatch_poly(rp, 70, 3))
    river = PL([(BIGL, 8), (-20, 8), (-20, 16), (BIGL, 16)])
    cv.obj([river], 0)
    for j, y in enumerate(range(9, 16)):
        x = -120 + (j * 7) % 9
        while x < -24:
            ln = 6 + (j * 5 + int(x)) % 8
            cv.hair([P(x, y), P(x + ln, y)])
            x += ln + 3

    # ---- St. Johns Bridge: two Gothic towers, cables and deck
    deck_y = 4
    towers = (-94, -70)
    cv.obj([], 0)
    cab = []
    for i in range(41):
        x = towers[0] + (towers[1] - towers[0]) * i / 40
        t = i / 40
        cab.append((x, -20 + 22 * 4 * t * (1 - t) * .8))
    for x, y in cab[2:-2:2]:
        cv.hair([P(x, y), P(x, deck_y)])
    cv.line(PL(cab))
    side_l = [(towers[0] - 30 + 30 * t, deck_y - 22 * t ** 1.6) for t in [i / 12 for i in range(13)]]
    side_r = [(towers[1] + 16 * t, -20 + 24 * t ** .7) for t in [i / 12 for i in range(13)]]
    cv.line(PL(side_l))
    cv.line(PL(side_r))
    for x, y in side_l[1:-1]:
        cv.hair([P(x, y), P(x, deck_y)])
    deck = PL([(-140, deck_y - .8), (-40, deck_y - .8), (-40, deck_y + 1.2), (-140, deck_y + 1.2)])
    cv.obj([deck], .5)
    cv.hair([P(-140, deck_y + .2), P(-40, deck_y + .2)])
    for tx in towers:
        tw = 2.4
        tp = PL([(tx - tw * 1.15, 9), (tx - tw, -16), (tx - tw * 1.1, -18), (tx - tw * .7, -19), (tx - tw * .7, -21.5),
                 (tx - tw * .3, -21.5), (tx, -25), (tx + tw * .3, -21.5), (tx + tw * .7, -21.5), (tx + tw * .7, -19),
                 (tx + tw * 1.1, -18), (tx + tw, -16), (tx + tw * 1.15, 9)])
        cv.obj([tp], .5)
        cv.hair(hatch_poly(PL([(tx, -26), (tx + tw, -18), (tx + tw, 9), (tx, 9)]), 90, 1.5))
        for (a0, a1) in ((-16, -8), (-5, 2)):
            op = PL([(tx - tw * .55, a1), (tx - tw * .55, a0 + 1.6), (tx, a0), (tx + tw * .55, a0 + 1.6), (tx + tw * .55, a1)])
            cv.obj([op], 0)
            solid(cv, op)
        # piers in the river
        pier = PL([(tx - tw * 1.3, 8), (tx + tw * 1.3, 8), (tx + tw * 1.3, 12), (tx - tw * 1.3, 12)])
        cv.obj([pier], .5)
        cv.hair(hatch_poly(pier, 90, 1.5))

    # ---- far lawn / meadow ground
    ground = PL([(BIGL, 16), (BIGR, 16), (BIGR, yb), (BIGL, yb)])
    cv.obj([ground], .5)
    cv.hair(hatch_poly(PL([(BIGL, 16), (BIGR, 16), (BIGR, 30), (BIGL, 30)]), 0, 2, .5))
    cv.hair(hatch_poly(PL([(BIGL, 30), (BIGR, 30), (BIGR, yb), (BIGL, yb)]), 0, 2, 1.))
    # grass: rows of strokes, growing toward the viewer
    r2 = random.Random(seed + 7)
    tufts = []
    gy = 20.
    while gy < yb:
        hgt = .8 + (gy - 16) * .06
        stepx = 1.6 + (gy - 16) * .05
        gx = -140 + r2.uniform(0, stepx)
        while gx < 140:
            lean = r2.uniform(-.5, .5)
            tufts.append([P(gx, gy), P(gx + lean, gy - hgt * r2.uniform(.6, 1.2))])
            gx += stepx * r2.uniform(.8, 1.6)
        gy += 1.2 + (gy - 16) * .05
    cv.hair(tufts)

    # ---- Douglas firs
    def fir(x, base, hgt, dark=True):
        wdt = hgt * .36
        tiers = 7
        pts = [(x, base - hgt)]
        R, L = [], []
        for i in range(1, tiers + 1):
            yy = base - hgt + hgt * .9 * i / tiers
            ww = wdt * (i / tiers) ** .9
            R += [(x + ww, yy), (x + ww * .42, yy - hgt * .035)]
            L += [(x - ww * .42, yy - hgt * .035), (x - ww, yy)]
        poly = [(x, base - hgt)] + R[:-1] + [(x + .7, base - hgt * .1), (x + .7, base), (x - .7, base), (x - .7, base - hgt * .1)] + L[::-1][1:]
        pp = PL(poly)
        cv.obj([pp], .5)
        cv.hair(hatch_poly(pp, 30, 1.5))
        cv.hair(hatch_poly(PL([(x, base - hgt), (x + wdt, base), (x, base)]), -50, 2))
        # light catching the branch tips on the west side
        for i in range(1, tiers + 1):
            yy = base - hgt + hgt * .9 * i / tiers
            ww = wdt * (i / tiers) ** .9
            cv.hair([P(x - ww * .9, yy - .3), P(x - ww * .35, yy - hgt * .03)])

    fir(-62, 44, 70)
    fir(-104, 40, 56)
    fir(-82, 34, 22)
    fir(70, 40, 66)
    fir(84, 36, 44)
    fir(96, 32, 30)

    # ---- the house (drawn larger, set forward on the lawn) --------------------
    base_P = P
    HK = 1.3

    def P(x, y):
        return base_P(-2 + (x + 8) * HK, 54 + (y - 46) * HK)

    def PL(pts):
        return [P(x, y) for x, y in pts]

    # side wall (in shade), receding to the right
    sw = [(-8, 8), (34, 3), (34, 42), (-8, 46)]
    swp = PL(sw)
    cv.obj([swp], 1.)
    cv.hair(quad_lines(swp, 1.5))
    cv.hair(hatch_poly(swp, 90, 3))
    # side windows
    for (a, b) in ((2, 11), (19, 27)):
        def yt_(x):
            return 8 + (3 - 8) * (x + 8) / 42
        def yb_(x):
            return 46 + (42 - 46) * (x + 8) / 42
        top = lambda x: yt_(x) + 9
        bot = lambda x: yt_(x) + 26
        win = PL([(a, top(a)), (b, top(b)), (b, bot(b)), (a, bot(a))])
        cv.obj([win], 1.)
        inner = PL([(a + 1.2, top(a) + 1.4), (b - 1.2, top(b) + 1.4), (b - 1.2, bot(b) - 1.4), (a + 1.2, bot(a) - 1.4)])
        cv.obj([inner], 0)
        solid(cv, inner)
        m = (a + b) / 2
        mid = lambda x: (top(x) + bot(x)) / 2
        cv.obj([PL([(a + 1, mid(a) - .6), (b - 1, mid(b) - .6), (b - 1, mid(b) + .6), (a + 1, mid(a) + .6)])], 0)
        cv.obj([PL([(m - .4, top(m)), (m + .4, top(m)), (m + .4, bot(m)), (m - .4, bot(m))])], 0)
        # sill
        cv.obj([PL([(a - 1.2, bot(a)), (b + 1.2, bot(b)), (b + 1.2, bot(b) + 1.4), (a - 1.2, bot(a) + 1.4)])], .5)
    # eave shadow under the side roof
    es = PL([(-8, 8), (34, 3), (34, 6), (-8, 11.5)])
    cv.obj([es], 0)
    solid(cv, es)

    # chimney (behind the roof ridge, drawn before roof so the roof clips it)
    ch = PL([(14, -38), (21, -38.6), (21, -6), (14, -6)])
    cv.obj([ch], 1.)
    cv.hair(hatch_poly(ch, 0, 2))
    bricks = []
    for j, yy in enumerate(range(-37, -6, 2)):
        for xx in ([15.6, 18.4] if j % 2 else [17, 19.8]):
            bricks.append([P(xx, yy), P(xx, yy + 2)])
    cv.hair(bricks)
    cv.hair(hatch_poly(PL([(18.5, -38.4), (21, -38.6), (21, -6), (18.5, -6)]), 90, 1.5))
    cap = PL([(13, -40.4), (22, -41), (22, -38.4), (13, -38)])
    cv.obj([cap], 1.)
    cv.hair(hatch_poly(cap, 0, 1.5))

    # side roof plane: ridge from gable peak back to the right, eave along the side wall top
    rf = PL([(-28, -26), (14, -30), (38, 4), (-6, 10)])
    cv.obj([rf], 1.)
    cv.hair(quad_lines(rf, 2.))                       # shingle courses
    cv.hair(quad_lines(rf, 3., along=False))          # down-slope shading
    cv.hair(hatch_poly(PL([(-6, 10), (38, 4), (34, -2), (-10, 4)]), 70, 1.5))  # darker near the eave
    cv.line([P(-28, -26), P(14, -30)])

    # front wall below the gable
    fw = PL([(-50, 10), (-8, 10), (-8, 46), (-50, 46)])
    cv.obj([fw], 1.)
    cv.hair(hatch_poly(fw, 0, 2, .7))                  # clapboards
    # porch shade
    shade = PL([(-50, 24), (-8, 24), (-8, 42), (-50, 42)])
    cv.hair(hatch_poly(shade, 45, 2))
    cv.hair(hatch_poly(PL([(-50, 24), (-8, 24), (-8, 28), (-50, 28)]), -45, 2))
    # front window (big Craftsman window with transom)
    win = PL([(-46, 27), (-33, 27), (-33, 40), (-46, 40)])
    cv.obj([win], 1.)
    tr = PL([(-45, 28), (-34, 28), (-34, 31), (-45, 31)])
    cv.obj([tr], 0)
    solid(cv, tr)
    for k in range(3):
        cv.obj([PL([(-42.6 + k * 3.7, 28), (-42 + k * 3.7, 28), (-42 + k * 3.7, 31), (-42.6 + k * 3.7, 31)])], 0)
    gl = PL([(-45, 32.2), (-34, 32.2), (-34, 39), (-45, 39)])
    cv.obj([gl], 0)
    solid(cv, gl)
    cv.obj([PL([(-39.9, 32), (-39.1, 32), (-39.1, 39), (-39.9, 39)])], 0)
    # door with its lights
    dr = PL([(-24, 26), (-16, 26), (-16, 42), (-24, 42)])
    cv.obj([dr], 1.)
    cv.hair(hatch_poly(dr, 90, 1.5))
    cv.obj([PL([(-23, 27.2), (-17, 27.2), (-17, 30.5), (-23, 30.5)])], .5)
    solid(cv, PL([(-22.7, 27.6), (-17.3, 27.6), (-17.3, 30.1), (-22.7, 30.1)]))
    cv.obj([PL([(-17.8, 34), (-17, 34), (-17, 35), (-17.8, 35)])], 0)

    # gable: shingled triangle with attic window, deep bargeboards
    gab = PL([(-28, -26), (-48, 10), (-10, 10)])
    cv.obj([gab], 1.)
    sh_lines = hatch_poly(gab, 0, 2)
    cv.hair(sh_lines)
    ticks = []
    for j, yy in enumerate(range(-22, 10, 2)):
        half = 20 * (yy + 26) / 36
        x = -28 - half + (1.5 if j % 2 else .4)
        while x < -28 + half:
            ticks.append([P(x, yy - 1.0), P(x, yy)])
            x += 3
    cv.hair(ticks)
    aw = PL([(-33, -8), (-23, -8), (-23, 4), (-33, 4)])
    cv.obj([aw], 1.)
    awi = PL([(-32, -7), (-24, -7), (-24, 3), (-32, 3)])
    cv.obj([awi], 0)
    solid(cv, awi)
    cv.obj([PL([(-28.4, -7), (-27.6, -7), (-27.6, 3), (-28.4, 3)]), PL([(-32, -2.4), (-24, -2.4), (-24, -1.6), (-32, -1.6)])], 0)
    # knee braces under the eaves
    for bx, d in ((-48, 1), (-10, -1)):
        br = PL([(bx, 10), (bx + d * 4, 10), (bx + d * .8, 14)])
        cv.obj([br], .5)
        cv.hair(hatch_poly(br, 0, 1.5))
    # bargeboards: thick rake trim with a black underside
    for (a, b) in (((-28, -27.4), (-52, 11)), ((-28, -27.4), (-6, 11))):
        n = (b[1] - a[1], -(b[0] - a[0]))
        L = math.hypot(*n)
        nx, ny = n[0] / L * 2.2, n[1] / L * 2.2
        if nx > 0:
            nx, ny = -nx, -ny
        bb = PL([a, b, (b[0] - nx * .2, b[1] + 2.2), (a[0], a[1] + 2.4)])
        cv.obj([bb], 1.)
        cv.hair([P(a[0], a[1] + 1.1), P(b[0], b[1] + 1.1)])
    # porch roof (a shed across the front)
    pr = PL([(-53, 20), (-5, 20), (-5, 24.5), (-53, 24.5)])
    cv.obj([pr], 1.)
    cv.hair(hatch_poly(PL([(-53, 20), (-5, 20), (-5, 22), (-53, 22)]), 0, 1.5))
    solid(cv, PL([(-53, 23), (-5, 23), (-5, 24.5), (-53, 24.5)]))
    # tapered Craftsman columns on brick piers
    for cx in (-49, -29.5, -9):
        col = PL([(cx - 1.4, 24.5), (cx + 1.4, 24.5), (cx + 2.2, 36), (cx - 2.2, 36)])
        cv.obj([col], 1.)
        cv.hair(hatch_poly(PL([(cx + .2, 24.5), (cx + 1.4, 24.5), (cx + 2.2, 36), (cx + .4, 36)]), 90, 1.5))
        pier = PL([(cx - 3, 36), (cx + 3, 36), (cx + 3, 42), (cx - 3, 42)])
        cv.obj([pier], 1.)
        cv.hair(hatch_poly(pier, 0, 1.5))
        cv.hair([[P(cx - 1, yy), P(cx - 1, yy + 1.5)] for yy in (36, 39)] + [[P(cx + 1.5, yy), P(cx + 1.5, yy + 1.5)] for yy in (37.5, 40.5)])
    # porch floor and foundation
    fl = PL([(-53, 42), (-5, 42), (-5, 44), (-53, 44)])
    cv.obj([fl], 1.)
    fd = PL([(-52, 44), (-6, 44), (-6, 47), (-52, 47)])
    cv.obj([fd], .5)
    cv.hair(hatch_poly(fd, 45, 2))
    cv.hair(hatch_poly(fd, -45, 2))
    fd2 = PL([(-8, 46), (34, 42), (34, 44.5), (-8, 48.5)])
    cv.obj([fd2], .5)
    solid(cv, fd2)
    # steps
    for k in range(3):
        st = PL([(-33 - k * 1.2, 44 + k * 2), (-25 + k * 1.2, 44 + k * 2), (-25 + k * 1.2, 46 + k * 2), (-33 - k * 1.2, 46 + k * 2)])
        cv.obj([st], 1.)
        cv.hair([P(-33 - k * 1.2, 45.4 + k * 2), P(-25 + k * 1.2, 45.4 + k * 2)])
        cv.hair(hatch_poly(PL([(-33 - k * 1.2, 45.4 + k * 2), (-25 + k * 1.2, 45.4 + k * 2), (-25 + k * 1.2, 46 + k * 2), (-33 - k * 1.2, 46 + k * 2)]), 0, 1.5))

    # rhododendrons along the foundation
    def shrub(x, y, w_, h_, sd):
        rr = random.Random(sd)
        top = []
        nb = 9
        for i in range(nb + 1):
            t = i / nb
            top.append((x - w_ / 2 + w_ * t, y - h_ * math.sin(PI * t) ** .6 - rr.uniform(0, h_ * .25)))
        bump = []
        for i in range(len(top) - 1):
            a, b = top[i], top[i + 1]
            mid = lerp(a, b, .5)
            bump += [a, (mid[0], mid[1] - 1.4)]
        poly = PL(bump + [top[-1], (x + w_ / 2, y), (x - w_ / 2, y)])
        cv.obj([poly], .5)
        cv.hair(hatch_poly(poly, 40, 1.5))
        cv.hair(hatch_poly(poly, -40, 3))
        # blossoms: tiny white rings
        for i in range(int(w_ / 3)):
            bx = x - w_ / 2 + 2 + rr.uniform(0, w_ - 4)
            by = y - rr.uniform(1.5, h_ * .7)
            ring = _ell_pts(*P(bx, by), .9 * s, .9 * s, 10)
            cv.obj([ring], .5)

    shrub(-46, 49, 13, 7, seed + 1)
    shrub(4, 49, 16, 8, seed + 2)
    shrub(26, 46, 14, 7, seed + 3)

    # brick walk from the steps down the lawn
    wk = [(-33.5, 50), (-24.5, 50), (-12, yb), (-48, yb)]
    wkp = PL(wk)
    cv.obj([wkp], 1.)
    yy, j = 51.0, 0
    rows = []
    while yy < yb:
        t = (yy - 50) / max(1, yb - 50)
        xl = -33.5 + (-48 + 33.5) * t
        xr = -24.5 + (-12 + 24.5) * t
        rows.append([P(xl, yy), P(xr, yy)])
        nb = 4
        for k in range(1, nb):
            bx = xl + (xr - xl) * (k - (.5 if j % 2 else 0)) / nb
            rows.append([P(bx, yy), P(bx, yy + 1.4 + t * 2)])
        yy += 1.4 + t * 2
        j += 1
    cv.hair(rows)
    cv.hair(hatch_poly(PL([(-24.5, 50), (-12, yb), (-20, yb), (-27.5, 50)]), 70, 3))

    # ---- Easter egg: Parker's dog sitting on the porch by the steps, looking out
    dx0, dy0, dk = -15.5, 43.9, .95
    dg = PL([(dx0 + x * dk, dy0 + y * dk) for x, y in DOG])
    halo_d = PL([(dx0 + 4 + (x - 4) * 1.22 * dk, dy0 + .6 + y * 1.12 * dk) for x, y in DOG])
    cv.obj([halo_d], 0)
    cv.obj([dg], 1.)
    solid(cv, dg)
    eye = _ell_pts(*P(dx0 + 6.7 * dk, dy0 - 8.7 * dk), .3 * s * HK, .3 * s * HK, 8)
    cv.obj([eye], 0)
    collar = PL([(dx0 + 4.3 * dk, dy0 - 7 * dk), (dx0 + 7.2 * dk, dy0 - 6.6 * dk), (dx0 + 7.2 * dk, dy0 - 6.1 * dk), (dx0 + 4.2 * dk, dy0 - 6.5 * dk)])
    cv.obj([collar], 0)

    # mailbox post at the walk with the house number plate (a tiny engraved P)
    mb = PL([(-6, 54), (-1, 54), (-1, 57.5), (-6, 57.5)])
    post = PL([(-4, 57.5), (-3, 57.5), (-3, 66), (-4, 66)])
    cv.obj([post], .5)
    cv.hair(hatch_poly(post, 90, 1.5))
    cv.obj([mb], 1.)
    cv.hair(hatch_poly(PL([(-6, 56), (-1, 56), (-1, 57.5), (-6, 57.5)]), 0, 1.5))
    cv.line([P(-1, 54.4), P(.6, 52.6), P(.6, 54)])

    return cv.svg()


def scene_svg(field, cid, seed=0, tall=False):
    d = _d(field, True, 0)
    return (f'<clipPath id="{cid}"><path d="{d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{scene(field, seed, tall)}</g>')


# ------------------------------------------------------------------ house key (tall tablet)
def key_svg(x, y, w, h, seed=0):
    """A house key lying across the tablet, its bow a carved volute, on a ruled ground."""
    o = [dark_ground((x, y, w, h), "M")]
    cv = Canvas()
    cy = y + h / 2
    kh = h * .8
    bx = x + w * .2
    # bow: a ring
    ring = _ell_pts(bx, cy, kh * .55, kh * .55, 40)
    hole = _ell_pts(bx, cy, kh * .2, kh * .2, 24)
    cv.obj([ring], 1.)
    cv.hair(hatch_poly(ring, 0, 1.5))
    cv.obj([hole], 1.)
    cv.hair(hatch_poly(hole, 0, 1.5))
    # shank
    x0, x1 = bx + kh * .5, x + w * .8
    sh = [(x0, cy - kh * .12), (x1, cy - kh * .12), (x1 + kh * .15, cy), (x1, cy + kh * .12), (x0, cy + kh * .12)]
    cv.obj([sh], 1.)
    cv.hair([[(x0, cy + kh * .04), (x1, cy + kh * .04)]])
    cv.hair(hatch_poly([(x0, cy + kh * .04), (x1, cy + kh * .04), (x1, cy + kh * .12), (x0, cy + kh * .12)], 0, 1.5))
    # bit with cuts
    bit = [(x1 - kh * 1.4, cy + kh * .12)]
    cuts = [.35, .2, .45, .28, .4]
    for i, c in enumerate(cuts):
        xa = x1 - kh * 1.4 + kh * 1.3 * i / len(cuts)
        xb = x1 - kh * 1.4 + kh * 1.3 * (i + 1) / len(cuts)
        bit += [(xa, cy + kh * (.12 + c)), (xb, cy + kh * (.12 + c))]
    bit += [(x1 - kh * .1, cy + kh * .12)]
    cv.obj([bit], 1.)
    cv.hair(hatch_poly(bit, 90, 1.5))
    # collar
    col = [(x0 - 1, cy - kh * .22), (x0 + 3, cy - kh * .22), (x0 + 3, cy + kh * .22), (x0 - 1, cy + kh * .22)]
    cv.obj([col], 1.)
    cv.hair(hatch_poly(col, 90, 1.5))
    o.append(cv.svg())
    # volute growing out of the bow
    o.append(C.acanthus_scroll(bx, cy, kh * .7, a0=200, turns=1.1, seed=seed, fronds=2, leaf_scale=.6))
    return "".join(o)


# ------------------------------------------------------------------ layouts (from the codex, the field filled)
def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.0, 150)
    o.append(C._clip(C._uid("b3", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _ell_pts(cx, cy, rx - 4.3, ry - 4.3, 72)
    o.append(scene_svg(field, C._uid("bs", w, h, seed), seed))
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 4, ry - 4, 72), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _cartouche_field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - .3, b - .3)


def _layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.85)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(10 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m3", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene_svg(_cartouche_field(cx, cy, cw, gh + 4), C._uid("ms", w, h, seed), seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, density=1.):
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
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
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
                   max_n=int(8 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t3", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene_svg(_cartouche_field(cx, cy, cw, ch), C._uid("ts", w, h, seed), seed, tall=True))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # rule the ribbon face so no white field remains
    lines = []
    for f in (-.5, -.3, -.1, .1, .3, .5):
        lines.append(_d([(px, py + f * bh) for px, py in centre], tol=.2))
    o.append(f'<path d="{"".join(lines)}" stroke="#000" stroke-width=".5" fill="none"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(C._clip(C._uid("k3", w, h, seed), tx, ty, tw, th, key_svg(tx, ty, tw, th, seed)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f3", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
