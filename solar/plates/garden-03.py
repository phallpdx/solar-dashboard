"""garden-03 "Feathered neighbors": the rare-bird page.

The plate engraves the morning's headline: a Bonaparte's Gull (confirmed at Frenchman's Bar) beating
over the Columbia, Mt. Hood on the horizon, a Great Egret standing at the water's edge in the reeds,
Cackling Geese going over in a V. In the tall plate two great blue herons grow out of the
acanthus on either side of the cartouche (their necks rise from fronds, carved in the same relief),
an engraved quill lies along the ribbon banner, and the pedestal tablet carries a frieze of the
week's waterbirds (teal, cackling goose) on rippled water.
Easter egg: a trail of dog paw prints crossing the mud at the egret's feet (Parker's dog came down
to the river too).
"""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_n = C._n
_d = C._d


# ----------------------------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------------------------

def _cr(pts, closed=False, k=6):
    """Catmull-Rom through pts, k samples per span."""
    n = len(pts)
    if n < 3:
        return list(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[i + 1]
        p3 = pts[(i + 2) % n] if closed else pts[min(n - 1, i + 2)]
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def _map(pts, ox, oy, s, flip=False):
    f = -1 if flip else 1
    return [(ox + f * x * s, oy + y * s) for x, y in pts]


def _rib(pts, w0, w1, wr=None):
    n = len(pts)
    W = [w0 + (w1 - w0) * i / (n - 1) for i in range(n)]
    return C._Rib(pts, W, wr if wr is not None else W)


def _wave_rows(x0, x1, y0, y1, pitch, rng, dash=(8, 26), gap=(2, 5), lane=None, sway=0.):
    """Broken horizontal hairlines (water / mud), optional white glint lane (centre x, half width)."""
    out = []
    y = y0
    row = 0
    while y <= y1:
        x = x0 - rng.uniform(0, 10)
        while x < x1:
            ln = rng.uniform(*dash)
            seg = []
            for j in range(int(ln / 3) + 2):
                xx = x + min(ln, j * 3)
                seg.append((xx, y + sway * math.sin(xx * .11 + row)))
            if lane:
                lx, lw = lane
                lw2 = lw * (.4 + .6 * (y - y0) / max(1, y1 - y0))
                if abs(x + ln / 2 - lx) < lw2:
                    seg = []
            if seg:
                out.append(seg)
            x += ln + rng.uniform(*gap)
        y += pitch
        row += 1
    return out


def _solid(cv, poly, angle=0.):
    """A black mass of 1 px lines 1 px apart, clipped to poly."""
    cv.line(C.hatch_poly(poly, angle, 1.))


# ----------------------------------------------------------------------------------------------
# the birds
# ----------------------------------------------------------------------------------------------

def gull(cv, ox, oy, span, flip=False, phase=0.):
    """Bonaparte's Gull in winter dress, flying left (unless flip), wings up on the stroke.
    span = wingspan in px; (ox, oy) the middle of the body."""
    s = span / 70.
    M = lambda p: _map(p, ox, oy, s, flip)
    lift = phase
    # far wing (behind the body), raised high
    far = _cr([(1, -2), (3, -12), (6 + lift, -24), (9 + lift, -33), (13 + lift, -29), (13, -20), (12, -9), (9, -2)], True, 5)
    farp = M(far)
    cv.obj([farp], .5)
    cv.hair(C.hatch_poly(farp, 60 if not flip else 120, 2.))
    tipf = M(_cr([(5.6 + lift, -26), (9 + lift, -33), (13 + lift, -29), (11.8, -25)], True, 4))
    _solid(cv, tipf, 45)
    # tail and body
    tail = M([(10, -2.2), (19.5, -1.4), (20.4, 1.2), (19, 3.4), (10, 3)])
    cv.obj([tail], .5)
    cv.hair(C.hatch_poly(tail, 0, 3.))
    body = M(_cr([(-12.5, -1.6), (-8, -3.9), (0, -4.3), (8, -3.3), (13, -1), (12, 2.4), (5, 4.3), (-4, 4.4), (-10.5, 2.6)], True, 5))
    cv.obj([body], 1.)
    belly = [(-8, 3.2), (0, 3.6), (8, 2.6)]
    R = _rib(M(_cr(belly, False, 6)), .1, .1)
    for k in range(1, 3):
        cv.hair([(p[0], p[1] - k * 1.5) for p in M(_cr([(-7.5, 3.2), (0, 3.4), (7.5, 2.4)], False, 6))][1:-1])
    cv.hair([q for q in M(_cr([(-9, 2.6), (-2, 3.9), (9, 2.4)], False, 6))])
    # head
    head = M(_cr([(-11, -2.5), (-13.8, -5.4), (-17.5, -6.2), (-20.6, -4.6), (-20.8, -2.2), (-18.6, -.4), (-14, .4), (-10.5, 1)], True, 5))
    cv.obj([head], 1.)
    bill = M([(-20.4, -3.6), (-25.6, -2.9), (-20.6, -2.2)])
    cv.obj([bill], .5)
    _solid(cv, bill, 0)
    ear = M([(-15.2, -3.6)])[0]
    cv.obj([C._ell_pts(ear[0], ear[1], 1.4 * s, 1.1 * s, 10)[:-1]], 0)
    _solid(cv, C._ell_pts(ear[0], ear[1], 1.4 * s, 1.1 * s, 10)[:-1])
    eye = M([(-18.2, -4.2)])[0]
    cv.line(C._ell_pts(eye[0], eye[1], .45 * s + .2, .45 * s + .2, 8))
    # near wing, raised, the leading edge toward us; pale grey mantle in light hatch, black trailing tips
    near = _cr([(-5, -1.5), (-8, -10), (-12 - lift, -20), (-17 - lift, -31), (-20 - lift, -36), (-15.5 - lift, -33),
                (-9 - lift, -26), (-1, -18), (4, -9), (5.5, -2.5)], True, 5)
    nearp = M(near)
    cv.obj([nearp], 1.)
    # secondaries: feather lines from the leading edge back to the trailing edge
    lead = _cr([(-5, -1.5), (-8, -10), (-12 - lift, -20), (-17 - lift, -31), (-20 - lift, -36)], False, 8)
    trail = _cr([(5.5, -2.5), (4, -9), (-1, -18), (-9 - lift, -26), (-15.5 - lift, -33), (-20 - lift, -36)], False, 8)
    nf = 15
    for i in range(1, nf):
        u = i / nf
        a = lead[int(u * (len(lead) - 1))]
        b = trail[int(u * (len(trail) - 1))]
        m = (a[0] + (b[0] - a[0]) * .35, a[1] + (b[1] - a[1]) * .35)
        cv.hair(M([m, b]))
    # mantle shading: lines along the wing, from the root
    for f in (.55, .7, .82, .92):
        pl = [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f) for a, b in
              zip(lead[:int(len(lead) * .78)], trail[:int(len(lead) * .78)])]
        cv.hair(M(pl))
    # the black wing-tip with its white leading wedge (a Bonaparte's mark)
    tip = M(_cr([(-11 - lift, -27.5), (-15.5 - lift, -33), (-20 - lift, -36), (-18.6 - lift, -32.4), (-15 - lift, -29.5)], True, 4))
    _solid(cv, tip, 45)
    cv.obj([M([(-6, -1), (-1, -.4), (3, -1.2), (-2, -3)])], 0)
    cv.hair(M([(-7, -.8), (-1, .3), (4, -.6)]))


def egret(cv, fx, fy, H, flip=False, seed=0):
    """A Great Egret standing at the water's edge facing left (unless flip), feet at (fx, fy),
    H tall to the crown. Drawn white, shaded in bulino along its plumage."""
    s = H / 100.
    M = lambda p: _map(p, fx, fy, s, flip)
    rng = random.Random(seed)
    # legs (black), slightly apart; toes
    legs = [M([(1, -50), (0, -26), (-1.5, 0)]), M([(5, -50), (6, -26), (7, -1)])]
    cv.obj([], 0)
    for L in legs:
        cv.heavy(L)
    cv.line(M([(-1.5, 0), (-7, .8)]) + [])
    cv.line(M([(-1.5, 0), (2, 1.2)]))
    cv.line(M([(7, -1), (12, .2)]))
    cv.line(M([(7, -1), (3.5, .6)]))
    # trailing plumes (aigrettes) over the tail
    for k in range(6):
        cv.hair(M(_cr([(6 + k, -62), (18 + k * .6, -56 + k * .5), (28 + k * .8, -47 + k * .7), (33 + k, -40 + k)], False, 5)))
    # body
    bodyc = [(-12, -66), (-6, -71.5), (4, -72), (14, -67), (24, -58), (31, -48.5), (25, -49.5), (14, -51.5),
             (3, -52), (-6, -55), (-11, -60)]
    body = M(_cr(bodyc, True, 5))
    cv.obj([body], 1.)
    # belly shading: lines following the underside, close at the bottom, opening upward
    under = _cr([(-11, -59), (-5, -54.5), (4, -53), (14, -53), (24, -51)], False, 6)
    for k, off in enumerate((0, 1.5, 3, 4.5, 6.5, 9)):
        pl = [(x, y - off) for x, y in under]
        pl = pl[int(k * 1.2):len(pl) - k]
        if len(pl) > 1:
            cv.hair(M(pl))
    # wing fold line and scapular feathers
    cv.hair(M(_cr([(-4, -64), (6, -63), (16, -59), (25, -52)], False, 6)))
    for i in range(7):
        x = -2 + i * 4
        cv.hair(M([(x, -63.5 + i * .6), (x + 4.5, -59.5 + i * .8)]))
    # neck: the S of an egret
    neck = _cr([(-8, -68), (-13, -75), (-12.5, -83), (-6, -89), (-5, -95), (-9, -99), (-14, -100)], False, 6)
    Rn = C._Rib(M(neck), [3.0 * s - (1.0 * s) * i / (len(neck) - 1) for i in range(len(neck))],
                [3.0 * s - (1.0 * s) * i / (len(neck) - 1) for i in range(len(neck))])
    cv.obj([Rn.outline()], 1.)
    sd = -1 if flip else 1
    for sv in (.35, .6, .82):
        cv.hair(Rn.contour(-sv * sd, .02, .9))
    cv.hair(Rn.contour(.6 * sd, .25, .55))
    # head and bill (yellow, in light hatch), eye, lore
    head = M(_cr([(-10, -97), (-12.5, -101.4), (-17, -102), (-20, -99.6), (-17, -97.4), (-13, -96.6)], True, 5))
    cv.obj([head], 1.)
    bill = M([(-19.6, -101), (-38, -98.6), (-19.8, -98.2)])
    cv.obj([bill], .5)
    cv.hair(C.hatch_poly(bill, 45 if not flip else 135, 1.5))
    e = M([(-16, -100)])[0]
    cv.line(C._ell_pts(e[0], e[1], .9, .9, 8))
    cv.line(M([(-17.2, -100.2), (-19.6, -99.8)]))
    # chest plumes hanging from the lower neck
    for k in range(5):
        cv.hair(M([(-12 + k * .8, -73 + k), (-14 + k * .6, -66 + k * .8)]))


def heron_head(cv, root, head, side, H, seed=0):
    """A great blue heron's neck and head carved into the scroll: the neck rises from root (x, y)
    in an S to the head at head (x, y), the bill pointing toward -side (inward). H ~ neck length."""
    rng = random.Random(seed)
    rx, ry = root
    hx, hy = head
    dx, dy = hx - rx, hy - ry
    # control points: out, then back in, like a heron's retracted S
    ctrl = [(rx, ry), (rx + dx * .1 + side * H * .14, ry + dy * .3), (rx + dx * .25 + side * H * .06, ry + dy * .6),
            (rx + dx * .7 - side * H * .02, ry + dy * .82), (hx + side * H * .06, hy + H * .03), (hx, hy)]
    sp = _cr(ctrl, False, 8)
    n = len(sp)
    w0, w1 = H * .07, H * .04
    W = [w0 + (w1 - w0) * (i / (n - 1)) ** .8 for i in range(n)]
    R = C._Rib(sp, W, W)
    cv.obj([R.outline()], 1.)
    # which side of the rib faces the throat (inward)?
    i = n // 2
    a, b = sp[i - 1], sp[i + 1]
    nx, ny = -(b[1] - a[1]), b[0] - a[0]
    inward = 1 if nx * (-side) > 0 else -1
    # back of the neck: dense contour bulino into a black shadow; front: streaked white
    lines = C._fill_lines(R, -.05 * inward, -.98 * inward, 1.5, .02, .97, 3)
    cv.hair(lines)
    C._shadow(cv, R, -inward, min(3., w0 * .35), .05, .9)
    # throat streaks: short dark dashes down the front of the neck
    u = .12
    while u < .85:
        cv.line([R.at(u, .55 * inward), R.at(u + 3. / R.L, .3 * inward)])
        cv.hair([R.at(u + 1.5 / R.L, .85 * inward), R.at(u + 4.5 / R.L, .7 * inward)])
        u += 6.5 / R.L
    # the head, carved in the round: local (u forward, v down) in units of hl, forward = -side
    hl = H * .25
    d = -side
    L = lambda pts: [(hx + d * u * hl, hy + v * hl) for u, v in pts]
    # crest plumes trailing back (black), behind the head
    for pl in ([(-.25, -.24), (-.8, -.2), (-1.3, -.06), (-.8, -.1), (-.3, -.1)],
               [(-.3, -.1), (-.9, .02), (-1.15, .13), (-.8, .06), (-.3, .02)]):
        p = L(_cr(pl, True, 4))
        cv.obj([p], .5)
        _solid(cv, p, 45)
    head = L(_cr([(-.45, .25), (-.55, .02), (-.4, -.22), (-.05, -.32), (.3, -.24), (.55, -.1), (.55, .12),
                  (.25, .3), (-.1, .36)], True, 5))
    cv.obj([head], 1.)
    # black brow stripe from the eye back to the plume
    brow = L(_cr([(.3, -.2), (.05, -.27), (-.3, -.24), (-.45, -.12), (-.2, -.15), (.05, -.16), (.3, -.13)], True, 4))
    cv.obj([brow], 0)
    _solid(cv, brow, 45)
    # cheek and throat bulino, following the head
    for k in range(4):
        v = .02 + k * .07
        cv.hair(L([(.42, v - .02), (.1, v + .03), (-.3, v + .02)]))
    # the dagger bill
    bill = L([(.5, -.12), (2.0, .03), (.5, .14)])
    cv.obj([bill], 1.)
    cv.hair(C.hatch_poly(L([(.5, -.12), (2.0, .03), (.5, .02)]), 45, 1.5))
    cv.line(L([(.52, .02), (1.7, .03)]))
    # the eye: a ring with a black pupil
    ex, ey = L([(.22, -.07)])[0]
    cv.obj([C._ell_pts(ex, ey, max(1.6, hl * .09), max(1.6, hl * .09), 12)[:-1]], 1.)
    cv.line(C._ell_pts(ex, ey, .6, .6, 6))


def paw_trail(cv, x, y, k, n=4, ang=-.35):
    """The Easter egg: a dog's paw prints walking across the mud."""
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(n):
        side = 1 if i % 2 else -1
        px = x + ca * i * 9 * k - sa * side * 2.6 * k
        py = y + sa * i * 9 * k + ca * side * 2.6 * k
        polys = [C._ell_pts(px, py, 1.7 * k, 1.4 * k, 12)[:-1]]
        for t, (u, v) in enumerate(((2.2, -1.6), (2.8, -.4), (2.8, .8), (2.2, 2.0))):
            tx = px + ca * u * k - sa * (v - .2) * k
            ty = py + sa * u * k + ca * (v - .2) * k
            polys.append(C._ell_pts(tx, ty, .65 * k, .55 * k, 8)[:-1])
        cv.obj(polys, .5)


def goose_swim(cv, x, y, s, flip=False, teal=False):
    """A cackling goose (or a blue-winged teal) swimming, waterline at y."""
    M = lambda p: _map(p, x, y, s, flip)
    if teal:
        body = M(_cr([(-6, -1), (-3, -4), (4, -4.2), (8, -2.4), (6, .2), (-5, .2)], True, 4))
        head = M(_cr([(-5, -3), (-6, -7), (-8.6, -7.6), (-10, -6), (-8, -5), (-6.5, -2.5)], True, 4))
        cv.obj([body, head], .5)
        cv.hair(C.hatch_poly(body, 0, 1.5))
        cface = M([(-8.4, -6.8), (-7.4, -7.2), (-7.4, -5.6)])
        cv.line(cface)
        cv.line(M([(-10, -6), (-11.6, -5.6)]))
        return
    body = M(_cr([(-8, -1), (-5, -5), (4, -5.6), (10, -4.4), (12, -2.4), (9, .2), (-7, .2)], True, 4))
    neck = M(_cr([(-6, -3.5), (-7.4, -9), (-7.6, -13), (-9.6, -14.4), (-11.8, -13.4), (-9.6, -12.4), (-9.2, -8.6), (-7.6, -3)], True, 4))
    cv.obj([body], .5)
    cv.hair(C.hatch_poly(body, 0, 1.5))
    cv.obj([neck], .5)
    _solid(cv, neck, 90)
    cv.obj([M(_cr([(-9.4, -12.6), (-8, -12.2), (-8.2, -10.6), (-9.2, -11.2)], True, 3))], 0)
    cv.line(M([(-11.8, -13.4), (-13.4, -13)]))
    cv.line(M([(-6, -.2), (8, -.2)]))


def cattail(cv, x, y, hgt, lean, rng, head=True):
    """A reed blade or bulrush rising from (x, y) hgt px, leaning `lean` (px at the top)."""
    pts = _cr([(x, y), (x + lean * .15, y - hgt * .4), (x + lean * .5, y - hgt * .75), (x + lean, y - hgt)], False, 6)
    if head:
        R = _rib(pts, 1.2, .5)
        cv.obj([R.outline()], .5)
        hi = int(len(pts) * .62)
        hx0, hy0 = pts[hi]
        hx1, hy1 = pts[min(len(pts) - 1, hi + 5)]
        ang = math.atan2(hy1 - hy0, hx1 - hx0)
        L = math.hypot(hx1 - hx0, hy1 - hy0)
        cx, cy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
        hw = max(2., hgt * .035)
        poly = [(cx + math.cos(ang) * L * .5 * math.cos(t) - math.sin(ang) * hw * math.sin(t),
                 cy + math.sin(ang) * L * .5 * math.cos(t) + math.cos(ang) * hw * math.sin(t)) for t in
                [TAU * i / 16 for i in range(16)]]
        cv.obj([poly], 1.)
        _solid(cv, poly, 45)
        # a highlight hairline down the lit side stays white: cover it with a thin white sliver
        hl = [(cx + math.cos(ang) * L * .35 * math.cos(t) - math.sin(ang) * hw * .35 * math.sin(t) - math.sin(ang) * hw * .3,
               cy + math.sin(ang) * L * .35 * math.cos(t) + math.cos(ang) * hw * .35 * math.sin(t) + math.cos(ang) * hw * .3)
              for t in [TAU * i / 12 for i in range(12)]]
        cv.obj([hl], 0)
    else:
        # a leaf blade: wide at the base, twisting, shaded on one side
        sg = 1 if lean >= 0 else -1
        n = len(pts)
        W = [max(.4, 2.6 * (1 - i / (n - 1)) ** .7) for i in range(n)]
        R = C._Rib(pts, W, [w * .6 for w in W])
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(-.2 * sg, 0, .8))
        C._shadow(cv, R, -sg, 1.2, .05, .7)


# ----------------------------------------------------------------------------------------------
# the scene: river at Frenchman's Bar, Mt. Hood, the gull, the egret, the reeds
# ----------------------------------------------------------------------------------------------

def scene(x, y, w, h, seed=0, mode="tall"):
    """The whole engraved view filling x..x+w, y..y+h (caller clips it)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    band = mode == "band"
    hy = y + h * (.6 if band else .56)            # horizon (far shore waterline)
    # sky: ruled, darkening upward (engraver's sky), lines a fixed 2 px apart, weight by height
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, hy + 1), (x - 2, hy + 1)]
    cv.obj([sky], 0)
    yy = y - 1.75
    while yy < hy:
        t = (yy - y) / max(1., hy - y)
        if t < .38:
            cv.line([(x - 2, yy), (x + w + 2, yy)]) if t < .14 else cv.hair([(x - 2, yy), (x + w + 2, yy)])
            yy += 2 if t < .14 else 1.5
        else:
            cv.hair([(x - 2, yy), (x + w + 2, yy)])
            yy += 2 if t < .7 else 3
    # clouds, lit from the low winter sun
    if not band:
        for (cx, cy, cw) in ((x + w * .78, y + h * .14, w * .26), (x + w * .14, y + h * .46, w * .22)):
            pts = []
            lobes = [(cx - cw * .38, cw * .12), (cx - cw * .16, cw * .19), (cx + cw * .08, cw * .23),
                     (cx + cw * .3, cw * .15)]
            for i in range(41):
                px = cx - cw * .5 + cw * i / 40
                top = max([math.sqrt(max(0, r * r - (px - lx) ** 2)) for lx, r in lobes] + [0])
                pts.append((px, cy - top * .8))
            base = [(cx + cw * .5, cy + 1), (cx - cw * .5, cy + 1)]
            poly = pts + base
            cv.obj([poly], .5)
            for k in range(1, 4):
                cv.hair([(cx - cw * (.44 - k * .05), cy - k * 1.5), (cx + cw * (.44 - k * .06), cy - k * 1.5)])
    # Mt. Hood on the horizon
    mx, mw, mh = x + w * (.68 if not band else .7), w * (.36 if not band else .5), h * (.27 if not band else .3)
    prof = [(-1, 0), (-.82, .1), (-.66, .2), (-.5, .33), (-.36, .47), (-.24, .62), (-.13, .78), (-.06, .9), (0, 1),
            (.05, .95), (.1, .87), (.17, .78), (.25, .67), (.34, .55), (.46, .41), (.6, .27), (.76, .15), (.9, .07), (1, 0)]
    MP = lambda p: [(mx + u * mw / 2, hy - v * mh) for u, v in p]
    mt = MP(prof)
    cv.obj([mt], .5)
    cv.hair(C.hatch_poly(mt, 0, 2., .25))
    snow = MP([(-.36, .47), (-.24, .62), (-.13, .78), (-.06, .9), (0, 1), (.05, .95), (.1, .87), (.17, .78), (.25, .67),
               (.34, .55), (.3, .5), (.25, .56), (.2, .46), (.15, .55), (.1, .4), (.05, .5), (0, .36), (-.05, .5), (-.1, .42),
               (-.16, .55), (-.22, .47), (-.28, .52)])
    cv.obj([snow], 0)
    # shadow flank (sun low in the south-east, behind and to the right: west face in shade)
    shade = MP([(0, 1), (-.06, .9), (-.13, .78), (-.24, .62), (-.36, .47), (-.5, .33), (-.66, .2), (-.82, .1), (-1, 0),
                (-.3, 0), (-.18, .2), (-.12, .38), (-.07, .55), (-.03, .75)])
    cv.obj([shade], 0)
    cv.hair(C.hatch_poly(shade, 45, 2.))
    for g in ((.02, .92, .06, .55), (.12, .8, .2, .5), (.2, .7, .3, .48), (-.04, .88, -.02, .6)):
        cv.hair(MP([(g[0], g[1]), ((g[0] + g[2]) / 2 + .01, (g[1] + g[3]) / 2), (g[2], g[3])]))
    # far shore: Douglas firs along the Washington bank
    top = []
    xx = x - 2
    while xx < x + w + 2:
        th = rng.uniform(.03, .065) * h if not band else rng.uniform(.04, .08) * h
        tw = rng.uniform(3, 6)
        top += [(xx, hy - th * .25), (xx + tw * .5, hy - th), (xx + tw, hy - th * .3)]
        xx += tw
    shore = top + [(x + w + 2, hy + 1.5), (x - 2, hy + 1.5)]
    cv.obj([shore], .5)
    cv.line(C.hatch_poly(shore, 0, 1.5))
    # the river, its glint lane under the light
    wy1 = y + h + 2
    water = [(x - 2, hy + 1.5), (x + w + 2, hy + 1.5), (x + w + 2, wy1), (x - 2, wy1)]
    cv.obj([water], 0)
    cv.hair(_wave_rows(x - 2, x + w + 2, hy + 2.75, hy + 6, 1.5, rng, (10, 40), (1, 3)))
    cv.hair(_wave_rows(x - 2, x + w + 2, hy + 8, wy1, 2, rng, (6, 22), (2, 6), lane=(x + w * .43, w * .07)))
    # Mt. Hood's reflection, broken
    for k in range(5):
        ry = hy + 4 + k * 3
        half = mw * (.18 - k * .03)
        if half > 2:
            cv.hair([(mx - half, ry), (mx + half * .4, ry)])
    # Cackling Geese in a V, far off
    if not band:
        gx, gy = x + w * .5, y + h * .12
        for i in range(-3, 5):
            k = abs(i)
            step = min(w * .022, h * .04)
            bx, by = gx + i * step * 1.4 + (k * step * 1.3 if i < 0 else 0), gy + k * step * .9
            bs = max(1.5, min(h * .008, step * .4))
            cv.obj([], 0)
            cv.line([(bx - bs * 1.6, by - bs * .6), (bx - bs * .6, by - bs * .1), (bx, by + bs * .3),
                     (bx + bs * .6, by - bs * .1), (bx + bs * 1.6, by - bs * .7)])
    # the gull: the morning's rare bird
    if band:
        gull(cv, x + w * .4, y + h * .5, min(w * .5, h * .95), phase=rng.uniform(-1, 1))
    elif mode == "med":
        gull(cv, x + w * .3, y + h * .36, min(w * .34, h * .62), phase=rng.uniform(-1, 1))
    else:
        gull(cv, x + w * .33, y + h * .33, min(w * .38, h * .5), phase=rng.uniform(-1, 1))
    # foreground mud bank (Frenchman's Bar is a sand-and-mud bar)
    if not band or h > 44:
        mt0 = y + h * (.8 if not band else .86)
        mud_top = [(x - 2 + w * i / 30, mt0 + h * .04 * math.sin(i / 30 * 5.2 + .6) - (h * .05) * (i / 30) ** 2)
                   for i in range(31)]
        mud = [(x - 2, mt0)] + mud_top + [(x + w + 2, y + h + 2), (x - 2, y + h + 2)]
        cv.obj([mud], 1.)
        # contour hatching along the bank, dense at the lip
        for k in range(1, 40):
            off = 1.5 * k if k < 6 else 9 + (k - 6) * 2
            pl = [(px, py + off) for px, py in mud_top]
            if pl[0][1] > y + h + 2:
                break
            cv.hair(pl)
        # the egg: a dog's paw prints in the mud
        k = max(1., min(1.6, h / 180))
        paw_trail(cv, x + w * (.42 if not band else .12), y + h * (.92 if not band else .95), k,
                  4 if not band else 3, -.12)
    # the egret, and the reeds it stands in
    if not band:
        EH = h * (.6 if mode == "tall" else .62)
        ex, ey = x + w * (.7 if mode == "tall" else .7), y + h * .88
        # ripples round its feet
        cv.obj([], 0)
        egret(cv, ex, ey, EH, seed=seed)
        cv.obj([], 0)
        for r in (1, 1.6, 2.3):
            cv.hair(C._ell_pts(ex + EH * .02, ey + 1, EH * .07 * r, EH * .012 * r, 20, .15, PI - .15))
        # reeds: a stand at the left edge, a few at the right, cattails among them
        for cx0, n, hmax, lean_dir in ((x + w * .1, 9 if mode == "tall" else 6, .55, 1), (x + w * .9, 6, .45, -1)):
            for i in range(n):
                rx = cx0 + lean_dir * i * w * .012 + rng.uniform(-2, 2)
                hg = h * hmax * rng.uniform(.55, 1.)
                lean = lean_dir * rng.uniform(-.05, .25) * hg
                cattail(cv, rx, y + h + 2, hg, lean, rng, head=(i % 3 == 1))
    return cv.svg()


def scene_clipped(cid, clip_d, x, y, w, h, seed, mode):
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{scene(x, y, w, h, seed, mode)}</g>')


# ----------------------------------------------------------------------------------------------
# banner quill and tablet frieze
# ----------------------------------------------------------------------------------------------

def quill(cv, centre, h):
    """An engraved feather lying along the banner face's centre line: shaft, barbs, notches."""
    n = len(centre)
    pts = centre[int(n * .1):int(n * .9) + 1]
    m = len(pts)
    W = [h * .34 * math.sin(PI * min(1, (i / (m - 1)) * 1.15)) ** .6 + .3 for i in range(m)]
    R = C._Rib(pts, W, W)
    cv.obj([R.outline()], .5)
    u = .01
    i = 0
    while u < .97:
        for sgn in (1, -1):
            if R.width(u, sgn) > 1.2:
                cv.hair([R.at(u, .05 * sgn), R.at(u + 3. / R.L, .97 * sgn)])
        u += 1.5 / R.L
        i += 1
    cv.line([R.at(u0, 0) for u0 in [k / 60 for k in range(61)]])
    for nu in (.3, .52, .74):
        cv.obj([[R.at(nu, .98), R.at(nu + 4 / R.L, .2), R.at(nu + 6 / R.L, .98)]], 0)


def tablet_frieze(x, y, w, h, seed):
    """The sunk tablet: rippled water with the week's waterbirds, reeds at each end."""
    rng = random.Random(seed)
    cv = C.Canvas()
    cv.obj([[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]], 0)
    wl = y + h * .66
    cv.hair([[(x, yy), (x + w, yy)] for yy in [y + .25 + k * 3 for k in range(int((wl - y - 2) / 3))]])
    cv.hair(_wave_rows(x, x + w, wl + 1.25, y + h, 2, rng, (5, 14), (2, 4)))
    s = h / 18
    birds = [(x + w * .2, 0), (x + w * .36, 1), (x + w * .64, 1), (x + w * .8, 0)]
    for bx, kind in birds:
        goose_swim(cv, bx, wl, s * (1.0 if kind == 0 else 1.2), flip=bx > x + w / 2, teal=(kind == 0))
    cv.obj([], 0)
    # a tiny sun-and-wing roundel at the centre
    cx = x + w / 2
    r = h * .32
    cv.obj([C._ell_pts(cx, y + h * .45, r, r, 24)[:-1]], 1.)
    for i in range(16):
        a = TAU * i / 16
        cv.hair([(cx + r * .45 * math.cos(a), y + h * .45 + r * .45 * math.sin(a)),
                 (cx + r * .85 * math.cos(a), y + h * .45 + r * .85 * math.sin(a))])
    cv.line(C._ell_pts(cx, y + h * .45, r * .3, r * .3, 10))
    for side in (-1, 1):
        for i in range(4):
            cattail(cv, x + (4 + i * 3 if side < 0 else w - 4 - i * 3), y + h + 1, h * rng.uniform(.6, .95),
                    side * -rng.uniform(0, 3), rng, head=(i == 1))
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, adapted: the vignette fills the whole cartouche field)
# ----------------------------------------------------------------------------------------------

def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 130)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx + 1, ry + 1, 64), True)}" fill="#fff" stroke="none"/>')
    field = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(scene_clipped(C._uid("bs", w, h, seed), field, cx - rx, cy - ry, 2 * rx, 2 * ry, seed, "band"))
    ring = _d(C._ell_pts(cx, cy, rx + 1, ry + 1, 64), True) + _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2.5, ry - 2.5, 64), True)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed):
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
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .06), rmax=r * .8,
                   max_n=13, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    a, b = _field_ab(cw, gh + 4)
    o.append(c)
    o.append(scene_clipped(C._uid("ms", w, h, seed), field, cx - a, cy - b, 2 * a, 2 * b, seed, "med"))
    o.append(_bead_ring(cx, cy, cw, gh + 4))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _field_ab(w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


def _bead_ring(cx, cy, w, h):
    """The cartouche's bead row, redrawn over the scene so the field sits inside it."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    inner = C._superellipse(cx, cy, a, b)
    return f'<path d="{_d(inner, True, .1)}" fill="none" stroke="#000" stroke-width="1.5"/>'


def _layout_tall(w, h, seed):
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
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .16, ph * .23)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .7)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .19)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .7)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    # the herons grow out of the leafwork beside the cartouche
    herons = C.Canvas()
    NH = min(ch * .62, ph * .42)
    for side in (-1, 1):
        root = (cx + side * (cw / 2 + NH * .5), cy + NH * .55)
        head = (cx + side * (cw / 2 + NH * .5), cy - NH * .3)
        heron_head(herons, root, head, side, NH, seed + side)
        C._frond(herons, root[0] - side * 2, root[1] + 4, -PI / 2 + side * .5, NH * .42, 3, .5,
                 side * 1.1, side * 4.6, None, random.Random(seed + 11 * side))
        C._frond(herons, root[0] + side * 3, root[1] + 6, -PI / 2 - side * .1, NH * .36, 2, .6,
                 -side * 1., -side * 4.4, None, random.Random(seed + 13 * side))
        occ.append(("c", root[0], (root[1] + head[1]) / 2, NH * .32))
        occ.append(("c", head[0] - side * NH * .1, head[1], NH * .3))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(11, ph * .035), rmax=r1 * .9,
                   max_n=14, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field_ab(cw, ch)
    o.append(scene_clipped(C._uid("ts", w, h, seed), field, cx - a, cy - b, 2 * a, 2 * b, seed, "tall"))
    o.append(_bead_ring(cx, cy, cw, ch))
    o.append(herons.svg())
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    qcv = C.Canvas()
    quill(qcv, centre, bh)
    o.append(qcv.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(tablet_frieze(tx + 2, ty + 2, tw - 3, th - 3, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) * 7 + 3
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
