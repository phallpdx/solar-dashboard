"""Science-01 plate: 'This morning in science' (LISA, and three stories on how life began:
a metabolic spark, the RNA world, the lipid bubble).

The cartouche holds the primordial pool: a storm sky over a smoking volcano, a lightning spark
striking warm water and ringing it with ripples, and riding the water a great protocell, its
lipid bilayer drawn bead by bead, an RNA stem-loop coiled inside, small vesicles budding nearby.
Tall plates add a crest of a cell-sphere, a helix cut into the pedestal tablet and gravitational
ripple rules on the banner. Easter egg: one of the floating 'vesicles' is a tiny ride cymbal."""
import sys
import math
import random
import engraving_codex as C

_n, _d, pat = C._n, C._d, C.pat
TAU = math.tau


def _path(pls, w=.5, tol=.15):
    d = "".join(_d(p, tol=tol) for p in pls if len(p) > 1)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w)}"/>' if d else ""


def _circ(cx, cy, r, n=None):
    n = n or max(8, int(r * 2.2))
    return C._ell_pts(cx, cy, r, r, n)[:-1]


def _blob(cx, cy, puffs):
    """Union outline of circles (a cloud / smoke puff) sampled by angle from a centre."""
    pts = []
    for i in range(72):
        a = TAU * i / 72
        ux, uy = math.cos(a), math.sin(a)
        best = 0.
        for (px, py, r) in puffs:
            dx, dy = px - cx, py - cy
            b = dx * ux + dy * uy
            c = dx * dx + dy * dy - r * r
            disc = b * b - c
            if disc >= 0:
                best = max(best, b + math.sqrt(disc))
        pts.append((cx + ux * best, cy + uy * best))
    return pts


def _bolt(x0, y0, x1, y1, rng, w0=3.2, k=6):
    """A jagged lightning bolt from (x0,y0) to (x1,y1): polygon tapering to a point."""
    pts = [(x0, y0)]
    for i in range(1, k):
        t = i / k
        j = (rng.uniform(.5, 1.) * (1 if i % 2 else -1)) * (x1 - x0 + 14) * .18
        pts.append((x0 + (x1 - x0) * t + j, y0 + (y1 - y0) * t))
    pts.append((x1, y1))
    L, R = [], []
    for i, (px, py) in enumerate(pts):
        wv = w0 * (1 - i / len(pts)) + .3
        L.append((px - wv, py))
        R.append((px + wv, py))
    return L + R[::-1], pts


def scene(x0, y0, W, H, field_d, seed=0, mode="medium"):
    rng = random.Random(seed * 31 + 7)
    cv = C.Canvas()
    x1, y1 = x0 + W, y0 + H
    yh = y0 + H * (.52 if mode != "short" else .55)       # horizon
    # ---- storm sky: ruled, darkest at the top
    cv.obj([], 0)
    y = y0 - 1
    while y < yh + 1:
        cv.hair([(x0 - 2, y), (x1 + 2, y)])
        f = (y - y0) / max(1, yh - y0)
        y += 1.5 if f < .45 else 2. if f < .8 else 3.
    # ---- volcano at the left, low hills at the right
    vx = x0 + W * .24
    vh = H * .3
    cw_ = W * .035
    prof = []
    for j in range(13):
        t = j / 12
        prof.append((vx - cw_ - (W * .16) * t ** 1.6, yh - vh + vh * t))
    cone = [(x0 - 4, yh + 1)] + prof[::-1] + [(vx - cw_ * .4, yh - vh - 1.5), (vx + cw_ * .3, yh - vh + 1.5)]
    cone += [(vx + cw_ + (W * .16) * (j / 12) ** 1.6, yh - vh + vh * j / 12) for j in range(13)] + [(x0 - 4, yh + 1)]
    cv.obj([cone], 1.)
    cv.hair(C.hatch_poly(cone, 0, 1.5))
    right = [(vx, yh - vh)] + [(vx + cw_ + (W * .16) * (j / 12) ** 1.6, yh - vh + vh * j / 12) for j in range(13)] + [(vx + W * .02, yh + 1)]
    cv.hair(C.hatch_poly(right, 70, 2))
    for k in range(5):                                     # gullies down the flank
        u = (k + .5) / 5
        cv.hair([(vx - cw_ + 2 * cw_ * u + (W * .16) * (t / 6) ** 1.6 * (2 * u - 1), yh - vh + vh * t / 6) for t in range(1, 7)])
    hills = [(x1 - W * .32, yh + 1)] + [(x1 - W * .32 + W * .34 * t / 20,
             yh - H * (.07 + .04 * math.sin(t * .7)) * math.sin(math.pi * t / 20) ** .5) for t in range(21)] + [(x1 + 3, yh + 1)]
    cv.obj([hills], 1.)
    cv.hair(C.hatch_poly(hills, 90, 2))
    # smoke from the crater: one billowing column leaning away from the storm
    puffs = []
    for i in range(5 if mode != "short" else 4):
        r = H * (.035 + .02 * i)
        puffs.append((vx + i * i * W * .006 - W * .01, yh - vh - r * .6 - i * H * .055, r))
    sp = _blob(vx, yh - vh - H * .12, puffs)
    cv.obj([sp], 1.)
    cv.hair(C.hatch_poly(sp, 0, 2, phase=.5))
    for (px, py, r) in puffs:
        arc = [(px + r * math.cos(a), py + r * math.sin(a)) for a in [TAU * (.08 + .32 * j / 10) for j in range(11)]]
        cv.line(arc)
        cv.hair([(px + r * .7 * math.cos(a), py + r * .7 * math.sin(a)) for a in [TAU * (.12 + .25 * j / 10) for j in range(11)]])
    # ---- storm clouds across the top
    ncl = 3 if mode != "short" else 2
    for k in range(ncl):
        cx = x0 + W * (.32 + .36 * k / max(1, ncl - 1)) + rng.uniform(-6, 6)
        cy = y0 + H * .13
        R = H * (.1 if mode != "short" else .12)
        puffs = [(cx + R * u, cy + R * v, R * s) for (u, v, s) in
                 ((-1.4, .4, .7), (-.6, -.2, 1.), (.4, -.35, 1.1), (1.3, .25, .8), (0, .45, .8))]
        cl = _blob(cx, cy + R * .1, puffs)
        cv.obj([cl], 1.)
        under = [(q[0], max(q[1], cy + R * .1)) for q in cl]
        cv.hair(C.hatch_poly(under, 0, 1.5, phase=.25))
        cv.hair(C.hatch_poly(cl, -20, 3, phase=.5))
        for (px, py, r) in puffs[1:4]:
            cv.hair([(px + r * .8 * math.cos(a), py + r * .8 * math.sin(a)) for a in [math.pi * (1.1 + .7 * j / 8) for j in range(9)]])
    # ---- the warm pool
    water = [(x0 - 4, yh), (x1 + 4, yh), (x1 + 4, y1 + 4), (x0 - 4, y1 + 4)]
    cv.obj([water], .5)
    sxp = x0 + W * .36                                     # strike point
    y = yh + 1.5
    i = 0
    while y < y1 + 2:
        f = (y - yh) / max(1, y1 - yh)
        pts = [(x, y + .5 * math.sin(x * .21 + i * 1.3)) for x in [x0 - 3 + j * 3 for j in range(int(W / 3) + 3)]]
        cv.hair(pts)
        y += 2. if f < .6 else 1.5
        i += 1
    # ripple rings around the strike
    for j in range(4):
        rx, ry = 5 + j * W * .04, 1.4 + j * H * .028
        cv.line(C._ell_pts(sxp, yh + 3 + j * .8, rx, ry, 40))
    # lightning
    bpoly, cl_ = _bolt(sxp - W * .07, y0 + H * .2, sxp, yh + 2, rng, w0=max(2.2, H * .022))
    cv.obj([bpoly], 1.)
    br = [cl_[2], (cl_[2][0] - W * .06, cl_[2][1] + H * .1), (cl_[2][0] - W * .05, cl_[2][1] + H * .16)]
    cv.heavy(br)
    # spark rays at the strike
    for k in range(14):
        a = math.pi + math.pi * (k + .5) / 14
        r0, r1 = 4, (H * .09 if k % 2 else H * .14)
        cv.hair([(sxp + r0 * math.cos(a) * 1.6, yh + 2 + r0 * math.sin(a)), (sxp + r1 * math.cos(a) * 1.6, yh + 2 + r1 * math.sin(a))])
    # ---- the protocell
    R = min(H * (.3 if mode != "short" else .31), W * .2)
    ccx, ccy = x0 + W * .64, yh + R * (.15 if mode != "short" else -.05)
    # its shadow / reflection on the water
    refl = C._ell_pts(ccx + R * .15, ccy + R * .95, R * 1.05, R * .22, 40)[:-1]
    cv.obj([refl], 0)
    cv.line(C.hatch_poly(refl, 0, 1.5))
    _protocell(cv, ccx, ccy, R, rng)
    # vesicles budding off
    for (u, v, s) in ((-1.3, -.95, .17), (1.35, -.75, .16), (1.25, .55, .12)):
        _vesicle(cv, ccx + R * u, ccy + R * v, R * s)
    # Easter egg: a tiny ride cymbal floating among the vesicles
    _cymbal(cv, x0 + W * .48, yh + H * .12, max(6., R * .26))
    body = cv.svg()
    cid = C._uid("sc", x0, y0, W, H, seed)
    return f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _protocell(cv, cx, cy, R, rng):
    disc = _circ(cx, cy, R + 1.6, 96)
    cv.obj([disc], 1.)
    # lipid bilayer: two rings of heads with tails pointing into the membrane
    n = int(TAU * R / 3.0)
    for i in range(n):
        a = TAU * i / n
        c, s = math.cos(a), math.sin(a)
        cv.hair([(cx + c * (R - .9), cy + s * (R - .9)), (cx + c * (R - 3.2), cy + s * (R - 3.2))])
    n2 = int(TAU * (R - 6) / 3.0)
    for i in range(n2):
        a = TAU * (i + .5) / n2
        c, s = math.cos(a), math.sin(a)
        cv.hair([(cx + c * (R - 5.1), cy + s * (R - 5.1)), (cx + c * (R - 3.4), cy + s * (R - 3.4))])
    # interior: light ruled cytoplasm with a dark crescent of shade bottom-right
    inner = _circ(cx, cy, R - 7, 80)
    cv.hair(C.hatch_poly(inner, 30, 2))
    # small molecules of the metabolic cycle drifting in the cytoplasm: benzene-like rings
    for (u, v, sz) in ((-.5, -.25, .11), (-.42, .32, .09), (.42, -.3, .1), (.36, .38, .08), (-.08, -.55, .07)):
        mx, my, mr = cx + R * u, cy + R * v, max(2.4, R * sz)
        hexa = [(mx + mr * math.cos(TAU * k / 6 + .5), my + mr * math.sin(TAU * k / 6 + .5)) for k in range(6)]
        cv.obj([hexa], 1.)
        cv.hair([hexa[0], hexa[1]]); cv.hair([hexa[2], hexa[3]]); cv.hair([hexa[4], hexa[5]])
        q = [(hexa[k][0] * .75 + mx * .25, hexa[k][1] * .75 + my * .25) for k in range(6)]
        cv.hair([q[0], q[1]]); cv.hair([q[2], q[3]]); cv.hair([q[4], q[5]])
        cv.line([hexa[1], (hexa[1][0] + (hexa[1][0] - mx) * .6, hexa[1][1] + (hexa[1][1] - my) * .6)])
    sh = [(cx + (R - 7) * math.cos(a), cy + (R - 7) * math.sin(a)) for a in [-.6 + 3.0 * j / 30 for j in range(31)]]
    sh += [(cx + R * .25 + (R - 9) * math.cos(a) * .9, cy + R * .2 + (R - 9) * math.sin(a) * .85)
           for a in [2.4 - 3.0 * j / 30 for j in range(31)]]
    cv.hair(C.hatch_poly(sh, -60, 1.5))
    # outer membrane shading: lower-right half of the bilayer band darkened
    band = [(cx + (R + 1.6) * math.cos(a), cy + (R + 1.6) * math.sin(a)) for a in [-.3 + 2.4 * j / 30 for j in range(31)]]
    band += [(cx + (R - 6) * math.cos(a), cy + (R - 6) * math.sin(a)) for a in [2.1 - 2.4 * j / 30 for j in range(31)]]
    cv.hair(C.hatch_poly(band, 45, 1.5))
    # membrane head rings drawn last so they read as beads
    for rr, nn, off in ((R, n, 0.), (R - 6, n2, .5)):
        for i in range(nn):
            a = TAU * (i + off) / nn
            p = _circ(cx + rr * math.cos(a), cy + rr * math.sin(a), 1.15, 7)
            cv.obj([p], .5)
            if math.cos(a - .8) > .3:
                cv.hair([p[0], p[3]])
    # RNA stem-loop coiled inside
    _rna(cv, cx - R * .02, cy + R * .02, R * .78, rng)
    # highlight edge (top-left) left clean; a glint
    g = (cx - R * .45, cy - R * .45)
    cv.line([(g[0] - 2.5, g[1]), (g[0] + 2.5, g[1])])
    cv.line([(g[0], g[1] - 2.5), (g[0], g[1] + 2.5)])


def _rna(cv, cx, cy, L, rng):
    """A hairpin: two strands climbing side by side, paired by rungs, closing in a loop at the
    top, with single-stranded tails flaring at the foot. The whole hairpin leans and bows."""
    gap = max(4.5, L * .2)
    n = 40
    lean = .35
    spine = []
    for i in range(n + 1):
        t = i / n
        spine.append((cx + math.sin(t * 2.4) * L * .22 + (t - .5) * L * lean, cy + L * .55 - t * L * 1.05))
    def off(i, s):
        i = min(max(i, 1), n - 1)
        (ax, ay), (bx, by) = spine[i - 1], spine[i + 1]
        dx, dy = bx - ax, by - ay
        m = math.hypot(dx, dy) or 1
        px, py = spine[i]
        return (px - dy / m * s, py + dx / m * s)
    A = [off(i, gap / 2) for i in range(n + 1)]
    B = [off(i, -gap / 2) for i in range(n + 1)]
    top = spine[-1]
    (ax, ay), (bx, by) = spine[-3], spine[-1]
    hd = math.atan2(by - ay, bx - ax)
    lr = gap * .9
    lc = (top[0] + math.cos(hd) * lr * .7, top[1] + math.sin(hd) * lr * .7)
    loop = [(lc[0] + lr * math.cos(hd + math.pi / 2 - k * (TAU * .85) / 20 - .45),
             lc[1] + lr * math.sin(hd + math.pi / 2 - k * (TAU * .85) / 20 - .45)) for k in range(21)]
    rib = A + loop + B[::-1]
    # body: a white ribbon with heavy strand lines and paired rungs
    poly = [off(i, gap / 2 + 1.2) for i in range(n + 1)] + [off(i, -gap / 2 - 1.2) for i in range(n, -1, -1)]
    cv.obj([poly], 0)
    for i in range(2, n - 1, 3):
        cv.line([off(i, gap / 2 - .4), off(i, -gap / 2 + .4)])
    cv.heavy(A + loop[1:-1] + B[::-1])
    # bases on the loop
    for k in range(2, 20, 3):
        p = loop[k]
        q = (p[0] + (p[0] - lc[0]) * .45, p[1] + (p[1] - lc[1]) * .45)
        cv.line([p, q])
    # tails
    for s, sgn in ((A, -1), (B, 1)):
        p = s[0]
        tail = [(p[0] + sgn * L * .25 * math.sin(k / 8 * 1.6) , p[1] + L * .2 * k / 8) for k in range(9)]
        cv.heavy(tail)
        for k in range(2, 9, 2):
            q = tail[k]
            cv.line([q, (q[0] + sgn * 2.5, q[1] - 1)])


def _vesicle(cv, cx, cy, r):
    p = _circ(cx, cy, r + 1.2, 28)
    cv.obj([p], 1.)
    cv.hair(C.hatch_poly(_circ(cx, cy, r - 1, 20), 30, 2))
    sh = [(cx + (r - .5) * math.cos(a), cy + (r - .5) * math.sin(a)) for a in [-.2 + 2.6 * j / 14 for j in range(15)]]
    cv.hair(C.hatch_poly(sh, -60, 1.5))
    n = max(6, int(TAU * r / 2.6))
    for i in range(n):
        a = TAU * i / n
        cv.hair([(cx + r * math.cos(a), cy + r * math.sin(a)), (cx + (r + 1.2) * math.cos(a), cy + (r + 1.2) * math.sin(a))])


def _cymbal(cv, cx, cy, r):
    """A ride cymbal seen at a slant: lathed bowl, a domed bell, a black edge underneath."""
    ry = r * .3
    rim = C._ell_pts(cx, cy, r, ry, 40)[:-1]
    under = C._ell_pts(cx, cy + ry * .45, r * .96, ry * .9, 40)[:-1]
    cv.obj([under], 0)
    cv.line(C.hatch_poly(under, 0, 1, phase=.2))
    cv.obj([rim], 1.)
    for f in (.82, .64, .46):
        cv.hair(C._ell_pts(cx, cy - ry * (1 - f) * .2, r * f, ry * f, 32))
    bell = C._ell_pts(cx, cy - ry * .45, r * .26, ry * .75, 20)[:-1]
    cv.obj([bell], 1.)
    cv.hair(C.hatch_poly(bell, 90, 1.5))
    cv.line([(cx, cy - ry * 1.3), (cx, cy - ry * 1.8)])


# ------------------------------------------------------------------------------------------------
# small bespoke pieces for the frame
# ------------------------------------------------------------------------------------------------

def helix_tablet(tx, ty, tw, th):
    """The pedestal tablet cut with an RNA strand: a sugar-phosphate backbone wave with its bases."""
    o = [f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-(tw - 2))}z" fill="{pat("L")}" stroke="none"/>']
    cy = ty + th / 2
    a = th * .3
    n = 300
    A = [(tx + 6 + (tw - 12) * i / n, cy - a * math.sin(TAU * 6 * i / n)) for i in range(n + 1)]
    Bs = [(tx + 6 + (tw - 12) * i / n, cy + a * math.sin(TAU * 6 * i / n)) for i in range(n + 1)]
    rungs = [[(A[i][0], A[i][1]), (Bs[i][0], Bs[i][1])] for i in range(0, n + 1, 5) if abs(A[i][1] - Bs[i][1]) > 2]
    o.append(_path(rungs, .5))
    o.append(_path([A], 1.5, .1))
    o.append(_path([Bs], 1., .1))
    return "".join(o)


def ripple_banner_fill(centre, h):
    lines = []
    L = len(centre)
    for s in (-.5, -.25, 0., .25, .5):
        pts = []
        for i in range(L - 1):
            for q in range(4):
                u = i + q / 4
                x = centre[i][0] + (centre[i + 1][0] - centre[i][0]) * q / 4
                y = centre[i][1] + (centre[i + 1][1] - centre[i][1]) * q / 4
                env = math.sin(math.pi * u / (L - 1))
                pts.append((x, y + s * h / 2 + h * .08 * env * math.sin(u * 1.4 + s * 3)))
        lines.append(pts)
    return _path(lines, .5)


def cell_crest(cx, cy, R):
    """A small engraved sphere (a protocell) for the crest, bilayer beads round it."""
    cv = C.Canvas()
    _protocell(cv, cx, cy, R, random.Random(3))
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts
# ------------------------------------------------------------------------------------------------

def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.1, 170)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(scene(cx - rx, cy - ry, 2 * rx, 2 * ry, field, seed, "short"))
    o.append(f'<path d="{field}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
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
    cw = min(w * .48, gh * 1.9)
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
                   max_n=int(9 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, field, seed, "medium"))
    bp = C._superellipse(cx, cy, a - .3, b - .3)
    o.append(_path([bp + [bp[0]]], 1.))
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
    o.append(C.dark_ground((0, 0, w, py0 + 2), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .62
    cx, cy = w / 2, py0 + ph * .46
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, field, seed, "tall"))
    bp = C._superellipse(cx, cy, a - .3, b - .3)
    o.append(_path([bp + [bp[0]]], 1.))
    room = cy - ch / 2
    R = max(10., min(30., room * .3))
    fcv = C.Canvas()
    for side in (-1, 1):
        C.acanthus_frond(cx + side * R * .2, cy - ch / 2 + 6, -90 + side * 62, R * 2.4, n=3, spread=34,
                         bend=.9 * side, curl=4.5 * side, seed=seed + side, cv=fcv)
    o.append(fcv.svg())
    o.append(cell_crest(cx, cy - ch / 2 - R * 1.1 + 2, R))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(ripple_banner_fill(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, min(ped_h, h - py)), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(helix_tablet(tx + 2, ty + 2, tw - 2, th - 2))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh), "L"))
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 11 * int(ctx.get("sheet", 0) or 0) + 101
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
