"""coast-04 "Shellfish check" (Clamming and crabbing, ODA biotoxin status).

Engraved subject: a Dungeness crab on the open bay sand at low tide, Haystack Rock and the surf
behind it, bay clams and a razor clam at its feet, a mussel bed on a barnacled rock. The scroll
frame is the house Codex frame, re-composed for this page: a scallop shell crowns the cartouche,
the lower volutes sprout crab claws, the pedestal tablet carries a running Vitruvian wave.
Easter egg: Parker's dog has left a trail of paw prints across the wet sand to the crab.
"""
import sys
import math
import random
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
PI, TAU = math.pi, 2 * math.pi
LX, LY = -.6, -.8          # light from the upper left


# ------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------

def _scale(poly, P, k):
    return [(P[0] + (x - P[0]) * k, P[1] + (y - P[1]) * k) for x, y in poly]


def _cent(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def _rings(poly, P, k0, k1, step, back=-.15, close=True):
    """Contour copies of poly scaled about P from k0 down to k1, kept only on the shadow side
    (where the direction from P faces away from the light more than `back`)."""
    out = []
    k = k0
    while k > k1 + 1e-6:
        q = _scale(poly, P, k)
        run = []
        seq = q + [q[0]] if close else q
        for x, y in seq:
            dx, dy = x - P[0], y - P[1]
            L = math.hypot(dx, dy) or 1
            if -(dx * LX + dy * LY) / L > back:
                run.append((x, y))
            else:
                if len(run) > 1:
                    out.append(run)
                run = []
        if len(run) > 1:
            out.append(run)
        k -= step
    return out


def _body(cv, poly, P, rim_px, dense=1., outline=1., mid=True, core=.4, detail=None):
    """A convex form modelled in three layers: a dark crescent of 1 px contour lines on the shadow
    side, a band of hair contours, a white core (the highlight). rim_px ~ the shape radius."""
    R = max(rim_px, 3.)
    st = 2. / R            # 2 px between contours on the far side
    cv.obj([poly], outline)
    (cv.line if dense >= 1 else cv.hair)(_rings(poly, P, 1 - st * .5, .7, st, -.25))
    cv.obj([_scale(poly, P, .72)], 0)
    if mid:
        cv.hair(_rings(poly, P, .72 - st * .5, core + .02, st, -.05))
    q3 = _scale(poly, P, core)
    cv.obj([q3], 0)
    if detail:
        detail(cv)
    return q3


def _capsule(p0, p1, r0, r1, n=8):
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    pts = []
    for i in range(n + 1):
        t = a - PI / 2 + PI * i / n
        pts.append((p1[0] + r1 * math.cos(t), p1[1] + r1 * math.sin(t)))
    for i in range(n + 1):
        t = a + PI / 2 + PI * i / n
        pts.append((p0[0] + r0 * math.cos(t), p0[1] + r0 * math.sin(t)))
    return pts


def _limb(cv, p0, p1, r0, r1, spines=0, rng=None):
    """A jointed crustacean limb segment: hard shell, dark along its shadow side, a white glint."""
    poly = _capsule(p0, p1, r0, r1)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    nx, ny = -math.sin(a), math.cos(a)
    sd = 1 if (nx * LX + ny * LY) < 0 else -1      # +normal*sd faces the shadow
    cv.obj([poly], 1.)
    rm = max(r0, r1)
    f = 1.
    while f > -.25:
        cv.line([(p0[0] + nx * sd * f * r0, p0[1] + ny * sd * f * r0), (p1[0] + nx * sd * f * r1, p1[1] + ny * sd * f * r1)]) \
            if f > .45 else cv.hair([(p0[0] + nx * sd * f * r0, p0[1] + ny * sd * f * r0), (p1[0] + nx * sd * f * r1, p1[1] + ny * sd * f * r1)])
        f -= 2. / rm if f > .45 else 2. / rm
    # glint along the lit side
    g0 = (p0[0] - nx * sd * .45 * r0, p0[1] - ny * sd * .45 * r0)
    g1 = (p1[0] - nx * sd * .45 * r1, p1[1] - ny * sd * .45 * r1)
    cv.obj([_capsule(g0, g1, r0 * .28, r1 * .28, 4)], 0)
    # knuckle groove near the far joint
    k = .86
    cx, cy = p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k
    rr = r0 + (r1 - r0) * k
    cv.line([(cx + nx * rr * .95, cy + ny * rr * .95), (cx - nx * rr * .95, cy - ny * rr * .95)])
    if spines and rng:
        for i in range(spines):
            t = .2 + .6 * i / max(1, spines - 1)
            bx, by = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
            rr = r0 + (r1 - r0) * t
            s = -sd
            b0 = (bx + nx * s * rr * .9 - math.cos(a) * 1.2, by + ny * s * rr * .9 - math.sin(a) * 1.2)
            b1 = (bx + nx * s * rr * .9 + math.cos(a) * 1.2, by + ny * s * rr * .9 + math.sin(a) * 1.2)
            tip = (bx + nx * s * (rr + 2.2) + math.cos(a) * 1.8, by + ny * s * (rr + 2.2) + math.sin(a) * 1.8)
            cv.obj([[b0, tip, b1]], .5)


# ------------------------------------------------------------------------------------------
# the Dungeness crab (top view, front toward `rot`)
# ------------------------------------------------------------------------------------------

def _carapace(s, M):
    pts = []
    N = 140
    for i in range(N):
        th = TAU * i / N
        c, si = math.cos(th), math.sin(th)
        x, y = c, .6 * si
        if si > 0:                      # posterior narrows
            x *= 1 - .33 * si ** 1.6
            y = .52 * si
        r = 1.
        if si < -.05 and abs(c) > .2:   # anterolateral teeth, 10 a side
            u = (abs(c) - .2) / .8
            ph = (u * 9.5) % 1.
            r += .055 * (1 - abs(ph - .5) * 2) ** 1.5 * (.6 + .4 * u)
        if si < 0 and abs(c) <= .2:     # front: shallow notch with frontal teeth
            r -= .05 * (1 - abs(c) / .2)
            r += .025 * abs(math.sin(abs(c) / .2 * 2.5 * PI))
        if abs(si + .17) < .1 and abs(c) > .95:   # the big last tooth
            r += .06 * (1 - abs(si + .17) / .1)
        pts.append(M(x * r, y * r))
    return pts


def _finger_poly(cv, base, ang, L, wid, bend, teeth_side=0):
    """One pincer finger: tapering, curving by `bend` rad over its length, toothed on one edge."""
    n = 10
    cl = [base]
    a = ang
    for j in range(n):
        a += bend / n * (1.6 if j > n * .55 else .5)
        cl.append((cl[-1][0] + math.cos(a) * L / n, cl[-1][1] + math.sin(a) * L / n))
    left, right = [], []
    for j, (qx, qy) in enumerate(cl):
        j1, j2 = max(j - 1, 0), min(j + 1, n)
        tx, ty = cl[j2][0] - cl[j1][0], cl[j2][1] - cl[j1][1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        ww = wid * (1 - j / n) ** .75 + .35
        tooth = (1.1 if j % 2 else 0) if (1 < j < n - 1) else 0
        left.append((qx + nx * (ww + (tooth if teeth_side > 0 else 0)), qy + ny * (ww + (tooth if teeth_side > 0 else 0))))
        right.append((qx - nx * (ww + (tooth if teeth_side < 0 else 0)), qy - ny * (ww + (tooth if teeth_side < 0 else 0))))
    poly = left + right[::-1]
    cv.obj([poly], 1.)
    # shade along the finger on its shadow side, black tip
    R = C._Rib(cl, [wid * (1 - j / n) ** .75 + .35 for j in range(n + 1)], [wid * (1 - j / n) ** .75 + .35 for j in range(n + 1)])
    nx0, ny0 = R.N[n // 2]
    sd = 1 if (nx0 * LX + ny0 * LY) < 0 else -1
    for f in (.75, .4):
        cv.line(R.contour(sd * f, 0., .75, minw=1.4))
    cv.hair(R.contour(-sd * .3, .1, .6, minw=2.))
    tip = R.outline()
    cv.obj([[R.at(u, s) for u, s in ((.72, 1), (1, 1), (1, -1), (.72, -1))]], 0)
    cv.line([R.at(.72 + .28 * k / 6, s) for k in range(7) for s in (0,)])
    cv.heavy([[R.at(u, s) for u in (.74, .85, .97)] for s in (-.45, .45)])
    return cl[-1]


def cheliped(cv, bx, by, ang, L, side, rng=None):
    """A crab's claw arm in px: merus out from (bx, by) heading ang, carpus turning in, a swollen
    palm, a fixed finger and a moving dactyl meeting in front. side +1 right arm, -1 left."""
    w = L * .085
    a0 = ang
    m1 = (bx + math.cos(a0) * L * .38, by + math.sin(a0) * L * .38)
    _limb(cv, (bx, by), m1, w * 1.0, w * 1.15, 3, rng)
    a1 = a0 - side * 1.0
    m2 = (m1[0] + math.cos(a1) * L * .2, m1[1] + math.sin(a1) * L * .2)
    _limb(cv, m1, m2, w * 1.25, w * 1.45, 2, rng)
    a2 = a1 - side * .55
    pl = L * .42
    ca, sa = math.cos(a2), math.sin(a2)
    pc = (m2[0] + ca * pl * .42, m2[1] + sa * pl * .42)
    palm = []
    for k in range(40):
        t = TAU * k / 40
        pu = math.cos(t) * pl * .55
        pv = math.sin(t) * w * 2.1 * (1 - .25 * math.cos(t))
        palm.append((pc[0] + pu * ca - pv * sa, pc[1] + pu * sa + pv * ca))
    tipb = (pc[0] + ca * pl * .46, pc[1] + sa * pl * .46)
    off = w * 1.0
    # fixed finger on the outside, dactyl on the inside, both curving in toward each other
    _finger_poly(cv, (tipb[0] + sa * off * side, tipb[1] - ca * off * side), a2 - side * .05, L * .3, w * 1.0, -side * .9, -side)
    _finger_poly(cv, (tipb[0] - sa * off * side, tipb[1] + ca * off * side), a2 - side * .35, L * .3, w * .95, side * .45, side)
    P = (pc[0] - ca * pl * .12 + LX * w * .9, pc[1] - sa * pl * .12 + LY * w * .9)

    def det(cv):
        for k in range(8):       # two rows of granules / spines along the top of the palm
            u = -.4 + .75 * k / 7
            for v in (.62, .3):
                q = (pc[0] + u * pl * .55 * ca - v * w * 2.1 * sa * side, pc[1] + u * pl * .55 * sa + v * w * 2.1 * ca * side)
                cv.hair([q, (q[0] + .7, q[1] + .5)])
    _body(cv, palm, P, w * 2.2, detail=det)
    cv.heavy(_rings(palm, P, 1, .99, 1, .3))


def crab(cv, cx, cy, s, rot=0., seed=0, shadow=True):
    """Dungeness crab, carapace half-width s px, centred at (cx, cy), rot in radians."""
    rng = random.Random(seed)
    cr, sr = math.cos(rot), math.sin(rot)

    def M(u, v):
        return (cx + (u * cr - v * sr) * s, cy + (u * sr + v * cr) * s)

    if shadow:
        sh = [M(math.cos(t) * 1.75 + .15, math.sin(t) * .72 + .32) for t in [TAU * i / 40 for i in range(40)]]
        cv.obj([sh], 0)
        cv.line(C.hatch_poly(sh, 45, 2))
    lw = max(1.4, s * .1)
    # walking legs: 4 pairs, spread sideways, knees out, tips curving back
    for side in (-1, 1):
        for i in range(3, -1, -1):
            bu, bv = side * (.8 - .1 * i), -.08 + i * .13
            a = -.3 + i * .32
            ang0 = (a if side > 0 else PI - a)
            L1, L2, L3 = .6 - .02 * i, .34, .4
            d0 = (math.cos(ang0), math.sin(ang0))
            p1 = (bu + d0[0] * L1, bv + d0[1] * L1)
            bend = side * (.45 + .08 * i)
            ang1 = ang0 + bend
            p2 = (p1[0] + math.cos(ang1) * L2, p1[1] + math.sin(ang1) * L2)
            ang2 = ang1 + bend * .5
            p3 = (p2[0] + math.cos(ang2) * L3, p2[1] + math.sin(ang2) * L3)
            _limb(cv, M(*p3), M(*p2), lw * .3, lw * .8)
            _limb(cv, M(*p2), M(*p1), lw * .8, lw * .95)
            _limb(cv, M(bu, bv), M(*p1), lw * 1.05, lw * 1.0, 2 if i < 3 else 0, rng)
    # claws, held forward
    for side in (-1, 1):
        bx, by = M(side * .55, -.3)
        ang = math.atan2(-.75, side * .65) + rot
        cheliped(cv, bx, by, ang, s * 1.55, side, rng)
    # carapace on top
    cara = _carapace(s, M)
    P = M(-.22, -.2)

    def cdet(cv):
        gr = [M(u, v) for u, v in ((-.2, -.42), (0, -.5), (.2, -.42), (.12, -.18), (-.12, -.18))]
        cv.hair([gr + [gr[0]]])
        card = [M(u, v) for u, v in ((-.13, .03), (.13, .03), (.17, .18), (0, .3), (-.17, .18))]
        cv.hair([card + [card[0]]])
        for sd in (-1, 1):
            cv.line([M(sd * (.15 + .4 * t), -.15 + .05 * t - .25 * t * t) for t in [k / 10 for k in range(11)]])
            cv.hair([M(sd * (.5 + .25 * t), -.05 + .18 * t) for t in [k / 6 for k in range(7)]])
        for _ in range(int(s * 2.2)):
            u, v = rng.uniform(-.88, .88), rng.uniform(-.52, .45)
            if (u / .92) ** 2 + (v / .56) ** 2 < 1:
                q = M(u, v)
                cv.hair([q, (q[0] + .6, q[1] + .3)])
    _body(cv, cara, P, s * .9, core=.38, detail=cdet)
    cv.heavy(_rings(cara, P, 1, .99, 1, .2))
    for sd in (-1, 1):
        e = M(sd * .14, -.6)
        cv.obj([_ell(e[0], e[1], s * .05 + .8, s * .05 + .8, 10)[:-1]], 1.)
        cv.heavy([(e[0] - .5, e[1] + .3), (e[0] + .5, e[1] - .3)])
    return cara


# ------------------------------------------------------------------------------------------
# bivalves
# ------------------------------------------------------------------------------------------

def bay_clam(cv, cx, cy, s, rot=0., seed=0):
    """A littleneck / bay clam valve: rounded triangle, concentric ridges, radial ribs."""
    cr, sr = math.cos(rot), math.sin(rot)

    def M(u, v):
        return (cx + (u * cr - v * sr) * s, cy + (u * sr + v * cr) * s)
    shell = []
    for i in range(48):
        t = TAU * i / 48
        u, v = math.cos(t), .84 * math.sin(t)
        if v < 0:
            v -= .22 * (max(0., -math.sin(t)) ** 6)
            u *= 1 - .18 * (-math.sin(t)) ** 2
        shell.append(M(u, v + .08))
    umbo = M(-.08, -.88)
    cv.obj([[(x + 1.2, y + 1.5) for x, y in shell]], 0)
    cv.line(C.hatch_poly([(x + 1.2, y + 1.5) for x, y in shell], 45, 2))
    cv.obj([shell], 1.)
    st = 2. / s
    k = 1 - st
    while k > .12:
        q = _scale(shell, umbo, k)
        (cv.line if (k * 100) % 7 < 2.5 else cv.hair)([q[3:46]])
        k -= st * (1.4 if k < .5 else 1)
    q = _scale(shell, umbo, .55)
    # radial ribs on the lit half only
    for j in range(5, 44, 3):
        cv.hair([umbo, _scale(shell, umbo, .97)[j]])
    cv.heavy(_rings(shell, M(-.3, -.3), 1, .99, 1, .3))


def razor_clam(cv, x0, y0, L, rot=0., seed=0):
    """A Pacific razor clam lying on the sand: long glossy oblong, growth lines, siphon out."""
    cr, sr = math.cos(rot), math.sin(rot)
    W = L * .2

    def M(u, v):
        return (x0 + u * cr * L - v * sr * W, y0 + u * sr * L + v * cr * W)
    top = [M(t, -1 + .25 * (2 * t - 1) ** 6 + .05 * math.sin(t * PI)) for t in [i / 30 for i in range(31)]]
    bot = [M(t, 1 - .25 * (2 * t - 1) ** 6 + .05 * math.sin(t * PI)) for t in [i / 30 for i in range(31)]]
    shell = top + bot[::-1]
    cv.obj([[(x + 1, y + 1.4) for x, y in shell]], 0)
    cv.line(C.hatch_poly([(x + 1, y + 1.4) for x, y in shell], 45, 2))
    # siphon out of the far end
    sp = [M(1.0 + .14 * t, -.2 + .4 * math.sin(t * 2)) for t in [i / 8 for i in range(9)]]
    for q in [_capsule(sp[0], sp[-1], W * .34, W * .3, 5)]:
        cv.obj([q], 1.)
        cv.line(C.hatch_poly(q, 0, 2))
    cv.obj([shell], 1.)
    # glossy lengthwise bands, dark on the lower half
    for v in (.15, .32, .48, .63, .76, .88):
        (cv.line if v > .5 else cv.hair)([M(t, v) for t in [i / 20 for i in range(1, 20)]])
    cv.hair([M(t, -.55) for t in [i / 20 for i in range(2, 18)]])
    # concentric growth arcs from the umbo (near the front end)
    for k in range(1, 9):
        u = .18 + k * .09
        cv.hair([M(u + .04 * math.cos(a) , math.sin(a) * .95) for a in [-PI / 2 + PI * i / 10 for i in range(11)]])


def mussel(cv, x0, y0, L, rot=0.):
    """A blue mussel: long dark wedge, a sheen streak, growth ridges."""
    cr, sr = math.cos(rot), math.sin(rot)
    W = L * .26

    def M(u, v):
        return (x0 + u * cr * L - v * sr * W, y0 + u * sr * L + v * cr * W)
    up = [M(t, -(.35 + .75 * math.sin(PI * t ** .7)) * (1 - .1 * t)) for t in [i / 20 for i in range(21)]]
    lo = [M(t, (.5 + .35 * math.sin(PI * t ** .8)) * (1 - .3 * t)) for t in [i / 20 for i in range(21)]]
    shell = up + lo[::-1]
    cv.obj([shell], 1.)
    # dark shell: 1 px lines along the length every 2 px...
    lines = []
    v = -.95
    while v < .85:
        lines.append([M(t, v * (.35 + .75 * math.sin(PI * max(t, .02) ** .7)) if v < 0 else v * (.5 + .35 * math.sin(PI * t ** .8))) for t in [i / 16 for i in range(17)]])
        v += 2. / W
    cv.line(lines)
    # ...broken by a white sheen streak
    sheen = [M(t, -.25 + .12 * math.sin(PI * t)) for t in [i / 12 for i in range(2, 11)]] + \
            [M(t, -.05 + .1 * math.sin(PI * t)) for t in [i / 12 for i in range(10, 1, -1)]]
    cv.obj([sheen], 0)
    for k in range(3):
        u = .45 + .17 * k
        cv.obj([], 0)
        cv.hair([[M(u + .03 * math.cos(a), math.sin(a) * .9) for a in [-PI / 2 + PI * i / 8 for i in range(9)]]])


def scallop(cv, cx, cy, size, up=True, seed=0):
    """A rococo scallop shell (coquille), hinge at (cx, cy), fanning up (or down) about size tall."""
    sd = -1 if up else 1
    n = 13
    spread = 1.25
    R = size
    ribs = []
    edge = []
    for i in range(n + 1):
        a = -spread + 2 * spread * i / n
        ribs.append(a)
    # scalloped rim: an arc bump per rib
    for i in range(n):
        a0, a1 = ribs[i], ribs[i + 1]
        for k in range(7):
            a = a0 + (a1 - a0) * k / 6
            r = R * (1 + .06 * math.sin(PI * k / 6)) * (1 - .1 * abs(a) ** 2)
            edge.append((cx + r * math.sin(a), cy + sd * r * math.cos(a) * .92))
    hinge = [(cx + R * .16, cy + sd * R * .06), (cx - R * .16, cy + sd * R * .06)]
    shell = edge + hinge
    # ears
    for s2 in (-1, 1):
        ear = [(cx, cy - sd * R * .02), (cx + s2 * R * .34, cy - sd * R * .02), (cx + s2 * R * .3, cy + sd * R * .2), (cx + s2 * R * .1, cy + sd * R * .22)]
        cv.obj([ear], 1.)
        cv.hair(C.hatch_poly(ear, 90, 2))
    cv.obj([shell], 1.)
    # each rib: a rounded ridge, dark on its right flank, with growth ticks
    for i in range(n):
        a0, a1 = ribs[i], ribs[i + 1]
        am = (a0 + a1) / 2
        for f, w in ((.15, 1.), (.32, 1.), (.5, .5), (.68, .5)):
            a = am + (a1 - am) * f
            rr = R * (1 - .1 * abs(a) ** 2)
            pts = [(cx + rr * t * math.sin(a), cy + sd * rr * t * math.cos(a) * .92) for t in (.2, .97)]
            (cv.line if w >= 1 else cv.hair)(pts)
        a = a0
        rr = R * (1 - .1 * abs(a) ** 2)
        cv.heavy([(cx + rr * .18 * math.sin(a), cy + sd * rr * .18 * math.cos(a) * .92),
                  (cx + rr * .99 * math.sin(a), cy + sd * rr * .99 * math.cos(a) * .92)])
    for t in (.42, .62, .8):
        cv.hair([(cx + R * t * math.sin(a), cy + sd * R * t * math.cos(a) * .92 * (1 - .1 * abs(a) ** 2)) for a in [-spread + 2 * spread * i / 30 for i in range(31)]])


def paw(cv, x, y, s, rot):
    """One dog paw print pressed in the sand (dark hollows)."""
    cr, sr = math.cos(rot), math.sin(rot)

    def M(u, v):
        return (x + (u * cr - v * sr) * s, y + (u * sr + v * cr) * s)
    pad = [M(.5 * math.cos(t), .42 * math.sin(t) + .25) for t in [TAU * i / 14 for i in range(14)]]
    cv.obj([pad], .5)
    cv.line(C.hatch_poly(pad, 0, 1.5))
    for u, v in ((-.52, -.25), (-.2, -.55), (.2, -.55), (.52, -.25)):
        toe = [M(u + .17 * math.cos(t), v + .2 * math.sin(t)) for t in [TAU * i / 10 for i in range(10)]]
        cv.obj([toe], .5)
        cv.line(C.hatch_poly(toe, 0, 1.5))


# ------------------------------------------------------------------------------------------
# the scene in the cartouche
# ------------------------------------------------------------------------------------------

def scene(x, y, w, h, seed=0, mode="tall"):
    """Bay at low tide filling the box x,y,w,h (to be clipped to the cartouche field)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    small = mode == "band"
    hz = y + h * (.30 if mode == "tall" else .34)
    if small:
        hz = y + h * .32
    x1, y1 = x + w, y + h
    cv.obj([], 0)
    # sky: horizontal rules, closer toward the zenith
    yy = y + .25
    while yy < hz:
        p = 2. if (yy - y) < (hz - y) * .45 else 3.
        cv.hair([(x - 2, yy), (x1 + 2, yy)])
        yy += p
    # a few gulls
    if not small:
        for gx, gy, gs in ((.18, .1, 3.2), (.3, .16, 2.4), (.24, .2, 2)):
            px, py = x + w * gx, y + h * gy
            cv.line([(px - gs, py), (px - gs * .5, py - gs * .45), (px, py), (px + gs * .5, py - gs * .45), (px + gs, py)])
    # distant headland, left
    hl = [(x - 2, hz)] + [(x + w * t * .45, hz - h * (.05 + .045 * math.sin(t * 3.2) - .04 * t * t) ) for t in [i / 20 for i in range(21)]] + [(x + w * .5, hz)]
    cv.obj([hl], .5)
    cv.hair(C.hatch_poly(hl, 45, 2))
    cv.hair(C.hatch_poly(hl, -45, 3))
    # Haystack Rock and the Needles
    if not small:
        rx, rw, rt = x + w * .68, w * .3, hz - h * .22
        prof = []
        for i in range(25):
            t = i / 24
            a = PI * t
            px = rx - rw / 2 * math.cos(a)
            py = hz - (hz - rt) * (math.sin(a) ** .8) * (1 - .06 * math.sin(3 * a + 1) - .05 * math.sin(7 * a))
            prof.append((px, py))
        rock = prof + [(rx + rw / 2, hz + 1), (rx - rw / 2, hz + 1)]
        cv.obj([rock], 1.)
        cv.line(C.hatch_poly(rock, 45, 2))
        cv.hair(C.hatch_poly(rock, -45, 3))
        lit = [(rx - rw / 2 + 3, hz - 1)] + [(px, py + 2.5) for px, py in prof[2:11]] + [(rx - rw * .05, hz - (hz - rt) * .5), (rx - rw * .1, hz - 1)]
        cv.obj([lit], 0)
        cv.hair(C.hatch_poly(lit, 45, 3))
        cv.hair(C.hatch_poly(lit, -45, 3))
        # ledges
        for k in range(4):
            ly = rt + (hz - rt) * (.3 + .17 * k)
            cv.heavy([(rx - rw * .05 + k * 3, ly), (rx + rw * .18, ly + 2), (rx + rw * .3 - k * 2, ly + 1)])
            cv.hair([(rx - rw * .3 + k * 2, ly + 3), (rx - rw * .08, ly + 4)])
        for nx_, nh in ((rx + rw * .62, .1), (rx + rw * .78, .065), (rx - rw * .72, .05)):
            nd = [(nx_ - w * .025, hz + 1), (nx_ - w * .01, hz - h * nh), (nx_ + w * .006, hz - h * nh * 1.05), (nx_ + w * .028, hz + 1)]
            cv.obj([nd], .5)
            cv.line(C.hatch_poly(nd, 80, 2))
        # puffin-white guano cap: leave a light crown
    # sea
    sea_b = hz + h * (.17 if not small else .2)
    cv.obj([[(x - 2, hz), (x1 + 2, hz), (x1 + 2, sea_b), (x - 2, sea_b)]], 0)
    cv.line([(x - 2, hz), (x1 + 2, hz)])
    yy = hz + 1.5
    k = 0
    while yy < sea_b - 3:
        segs = []
        xx = x - 2
        while xx < x1:
            ln = rng.uniform(8, 26)
            segs.append([(xx, yy), (min(x1 + 2, xx + ln), yy)])
            xx += ln + rng.uniform(1.5, 4)
        (cv.line if k % 3 == 1 else cv.hair)(segs)
        yy += 2. if (yy - hz) < (sea_b - hz) * .5 else 1.5 + .5
        k += 1
    # breaker: dark curl under a white foam crest
    by = sea_b - 3
    crest = [(x - 2 + i * 2, by - 3 - 1.6 * math.sin(i * .9) - 1.2 * math.sin(i * .37)) for i in range(int(w / 2) + 4)]
    foam = crest + [(x1 + 4, by + 3), (x - 2, by + 3)]
    cv.obj([foam], 0)
    cv.line(crest)
    for i in range(0, len(crest) - 3, 3):
        cv.hair([crest[i], (crest[i][0] + 1.2, by + 1.8)])
    # wet sand with reflections
    sand_t = sea_b + 2
    cv.obj([[(x - 2, sea_b + 2), (x1 + 2, sea_b + 2), (x1 + 2, y1 + 2), (x - 2, y1 + 2)]], 0)
    cv.line([(x - 2, sea_b + 2.5), (x1 + 2, sea_b + 2.5)])
    yy = sand_t + 2
    wet_b = sand_t + h * .08
    while yy < wet_b:
        segs = []
        xx = x - 2
        while xx < x1:
            ln = rng.uniform(10, 40)
            segs.append([(xx, yy), (min(x1 + 2, xx + ln), yy)])
            xx += ln + rng.uniform(2, 6)
        cv.hair(segs)
        yy += 2
    if not small:
        # reflection of the rock in the wet sand
        rx = x + w * .74
        refl = [(rx - w * .1, sand_t), (rx + w * .12, sand_t), (rx + w * .05, wet_b), (rx - w * .05, wet_b)]
        cv.line(C.hatch_poly(refl, 90, 2))
    # dry sand: ripples, stipple dashes, darker toward the foreground
    yy = wet_b + 1
    r = 0
    while yy < y1 + 2:
        dens = (yy - wet_b) / max(1., y1 - wet_b)
        segs = []
        xx = x - 2 + rng.uniform(0, 3)
        while xx < x1:
            amp = 1.2
            ln = rng.uniform(4, 14)
            segs.append([(xx + j, yy + amp * math.sin((xx + j) * .07 + r * 1.3)) for j in range(0, int(ln) + 1, 2)])
            xx += ln + rng.uniform(1.5, 6 - 3.5 * dens)
        (cv.line if (r % 2 == 0 and dens > .5) else cv.hair)(segs)
        yy += 3.
        r += 1
    # show holes (clams breathing under the sand)
    for _ in range(4 if not small else 1):
        hx, hy = x + w * rng.uniform(.06, .4), wet_b + (y1 - wet_b) * rng.uniform(.15, .5)
        cv.obj([_ell(hx, hy, 2.2, 1.2, 10)[:-1]], .5)
        cv.heavy([(hx - 1, hy), (hx + 1, hy)])

    # foreground subjects
    if small:
        s = min(w * .15, h * .24)
        crab(cv, x + w * .5, y + h * .64, s, -.05, seed)
        return cv.svg()
    s = min(w * .19, h * .2)
    ccx, ccy = x + w * .52, y1 - h * (.37 if mode == "tall" else .3)
    # paw prints: the dog walked up the wet sand to have a look at the crab
    for i in range(5):
        t = i / 4
        px = x + w * (.05 + .3 * t)
        py = wet_b + (ccy - wet_b) * (.15 + .75 * t) + (3 if i % 2 else -3)
        if mode == "medium" and px < x + w * .12:
            continue
        paw(cv, px, py, max(3., s * .22), .9 + .2 * (i % 2))
    # mussel bed on a barnacled rock, right foreground
    fb = .07 if mode == "tall" else 0
    mr = [(x1 - w * .36, y1 + 2), (x1 - w * .33, y1 - h * (.1 + fb)), (x1 - w * .22, y1 - h * (.17 + fb)), (x1 - w * .08, y1 - h * (.19 + fb)), (x1 + 2, y1 - h * (.14 + fb)), (x1 + 2, y1 + 2)]
    cv.obj([mr], 1.)
    cv.line(C.hatch_poly(mr, 45, 2))
    cv.hair(C.hatch_poly(mr, -45, 3))
    for k in range(5):     # barnacles
        bx, by = x1 - w * (.1 + .04 * k), y1 - h * (.15 + fb - .006 * k) - (k % 2) * 3
        cv.obj([_ell(bx, by, 2.2, 1.6, 10)[:-1]], .5)
        cv.heavy([(bx - .6, by), (bx + .6, by)])
    ml = max(8., s * .7)
    for k, (u, v, a) in enumerate(((.24, .12, -2.3), (.17, .1, -1.9), (.1, .12, -1.5), (.2, .05, -2.7), (.06, .07, -1.2))):
        mussel(cv, x1 - w * (u + .05), y1 - h * (v + fb), ml * (1 - .07 * k), a)
    # bay clams, left foreground, and the razor clam (season closed: lying idle)
    fb = .16 if mode == "tall" else .08
    bay_clam(cv, x + w * .2, y1 - h * (fb + .02), max(5., s * .3), -.3, seed)
    bay_clam(cv, x + w * .31, y1 - h * (fb - .03), max(4.5, s * .25), .4, seed + 1)
    razor_clam(cv, x + w * .05, y1 - h * (fb + .2), max(16., s * .95), -.32, seed)
    crab(cv, ccx, ccy, s, -.08 + .04 * math.sin(seed), seed)
    return cv.svg()


# ------------------------------------------------------------------------------------------
# pedestal tablet: a running Vitruvian wave
# ------------------------------------------------------------------------------------------

def vitruvian(x, y, w, h):
    """A running Vitruvian wave: black crests rolling right into spiral eyes over a black sea
    band, on a ruled sky."""
    R = h * .4
    base = y + h - h * .12
    cy = base - R
    P = R * 3.4
    n = max(3, int(round(w / P)))
    P = w / n
    o = [f'<path d="{C.hatch_d([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], 0, 2, .25)}" stroke-width=".5"/>']
    d = []
    for k in range(-1, n + 1):
        cx = x + P * (k + .55)
        T = 2.55 * PI
        outer, inner = [], []
        for i in range(61):
            t = T * i / 60
            r = R * (1 - .72 * t / T)
            th = R * .5 * (1 - t / T) ** 1.2 + .4
            a = PI + t
            outer.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            ri = max(.3, r - th)
            inner.append((cx + ri * math.cos(a), cy + ri * math.sin(a)))
        foot = [(cx - R - P * .45, base + 1), (cx - R * 1.05, cy + R * .2)]
        poly = foot + outer + inner[::-1] + [(cx - R * .5, base + 1)]
        d.append(_d(poly, True, .1))
    d.append(f"M{_n(x - 2)},{_n(base)}h{_n(w + 4)}v{_n(h)}h{_n(-w - 4)}z")
    cid = C._uid("vw", x, y, w, h)
    o.append(f'<path d="{"".join(d)}" fill="#000" stroke="none"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts (house layouts from engraving_codex, recomposed for this page)
# ------------------------------------------------------------------------------------------

def _clip_to(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b


def _claw_volute(cv, cx, cy, r, side, up=True):
    """(unused) A crab claw growing out of a volute eye: the scroll's stem turns into the cheliped."""
    ang = (-PI / 2 - side * .5) if up else (PI / 2 + side * .5)
    p0 = (cx, cy)
    p1 = (cx + math.cos(ang) * r * .7, cy + math.sin(ang) * r * .7)
    _limb(cv, p0, p1, r * .11, r * .13, 3, random.Random(3))
    a2 = ang - side * .7
    pc = (p1[0] + math.cos(a2) * r * .3, p1[1] + math.sin(a2) * r * .3)
    ca, sa = math.cos(a2), math.sin(a2)
    palm = [(pc[0] + math.cos(t) * r * .32 * ca - math.sin(t) * r * .14 * sa,
             pc[1] + math.cos(t) * r * .32 * sa + math.sin(t) * r * .14 * ca) for t in [TAU * i / 30 for i in range(30)]]
    tip = (pc[0] + ca * r * .28, pc[1] + sa * r * .28)
    for off, bd in ((-.07, .9), (.07, -.8)):
        q = [(tip[0] - sa * off * r, tip[1] + ca * off * r)]
        a = a2
        for j in range(8):
            a += bd * .12 * side
            q.append((q[-1][0] + math.cos(a) * r * .045, q[-1][1] + math.sin(a) * r * .045))
        R = C._Rib(q, [r * .05 * (1 - j / 9) + .4 for j in range(9)], [r * .05 * (1 - j / 9) + .4 for j in range(9)])
        cv.obj([R.outline()], 1.)
        cv.hair(R.contour(.3, 0, .8))
    _body(cv, palm, (pc[0] - ca * r * .05 + LX * r * .04, pc[1] - sa * r * .05 + LY * r * .04), r * .25)


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("b4", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 3.6, ry - 3.6
    d = _d(_ell(cx, cy, fx, fy, 64), True)
    o.append(_clip_to(C._uid("bf4", w, h, seed), d, scene(cx - fx, cy - fy, 2 * fx, 2 * fy, seed, "band")))
    o.append(f'<path d="{_d(_ell(cx, cy, fx, fy, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.75)
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
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m4", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, gh + 4)
    o.append(_clip_to(C._uid("mf4", w, h, seed), inner, scene(cx - a, cy - b, 2 * a, 2 * b, seed, "medium")))
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
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .66
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .24)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(7 * density), edge=.6, cv=cv)
    cv.extend(main)
    ssz = min(ch * .17 + top_free * .8, 64)
    sy = cy - ch / 2 + ssz * .35
    for side in (-1, 1):
        C.acanthus_frond(cx + side * ssz * .3, sy - ssz * .1, -PI / 2 + side * 1.0, ssz * .95, n=3, spread=26, seed=seed + side, cv=cv)
    o.append(C._clip(C._uid("t4", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, ch)
    o.append(_clip_to(C._uid("tf4", w, h, seed), inner, scene(cx - a, cy - b, 2 * a, 2 * b, seed, "tall")))
    # scallop crest with acanthus springing from its ears
    crest = C.Canvas()
    scallop(crest, cx, sy, ssz, True, seed)
    o.append(crest.svg())
    bh = min(16, ph * .05)
    bsvg, cen = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    m = len(cen)
    rib = "".join(_d([(px, py + off) for px, py in cen[1:m - 1]], tol=.15) for off in (-bh * .2, bh * .2))
    o.append(f'<path d="{rib}" stroke="#000" stroke-width=".5"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_clip_to(C._uid("tt4", w, h, seed), f"M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z",
                      vitruvian(tx + 2, ty + 2, tw - 3, th - 3)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f4", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.4,
                                       r_scale=1.15, n=2)))
        pend = C.Canvas()
        scallop(pend, w / 2, fy + 2, fh * .78, False, seed + 7)
        o.append(pend.svg())
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 4
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
