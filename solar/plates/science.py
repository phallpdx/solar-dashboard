"""Science plate: the lead story is NASA's LISA and gravitational waves.

The cartouche holds an engraved scene of spacetime: a ruled 'rubber sheet' in perspective, pulled
down into two wells by an orbiting pair of black holes, with the two-armed spiral of gravitational
waves running out across it; above, a ruled night sky with LISA's three spacecraft and their laser
triangle trailing a hatched Earth. Tall plates add a chirp waveform cut into the pedestal tablet and
a rippling ribbon. Easter egg: a small constellation in the sky traces a 'P'."""
import sys
import math
import random
import engraving_codex as C

_n, _d, pat = C._n, C._d, C.pat
TAU = math.tau


# ------------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------------

def _path(pls, w=.5, color="#000", tol=.15, extra=""):
    d = "".join(_d(p, tol=tol) for p in pls if len(p) > 1)
    if not d:
        return ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{_n(w)}"{extra}/>'


def _fill(polys, fill="#fff", stroke="none", w=0):
    d = "".join(_d(p, True, 0) for p in polys if len(p) > 2)
    s = f' stroke="{stroke}" stroke-width="{_n(w)}"' if stroke != "none" else ' stroke="none"'
    return f'<path d="{d}" fill="{fill}"{s}/>' if d else ""


def _split(pts, keep):
    """Split a polyline into runs where keep(point index) is true."""
    out, cur = [], []
    for i, p in enumerate(pts):
        if keep(i):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _star(x, y, r):
    """A four-point engraver's star."""
    k = r * .28
    return [(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)]


# ------------------------------------------------------------------------------------------------
# the scene: spacetime sheet, binary black holes, LISA, Earth
# ------------------------------------------------------------------------------------------------

def spacetime_scene(x0, y0, W, H, clip_d, seed=0, mode="medium"):
    """Engraved gravitational-wave scene filling the box x0,y0,W,H, clipped to clip_d."""
    rng = random.Random(seed)
    o = []
    small = mode == "short"
    horizon = y0 + H * (.30 if mode == "tall" else .34 if mode == "medium" else .30)
    cx = x0 + W / 2

    # ---- sky: horizontal rules, tight at the zenith, opening toward the horizon ----
    sky, sky1 = [], []
    y = y0 - 2
    while y < horizon + 1:
        t = (y - y0) / max(1., horizon - y0)
        (sky1 if t < .45 else sky).append([(x0 - 4, y), (x0 + W + 4, y)])
        y += 2. if t < .45 else 1.5 if t < .75 else 2. if t < .92 else 3.
    o.append(_path(sky, .5, tol=0))
    o.append(_path(sky1, 1., tol=0))

    # ---- the sheet geometry ----
    D0, D1 = 1., 4.2
    phase = (seed % 360) / 360 * TAU                     # orbital phase changes with the date
    sep = {"tall": .55, "medium": .72, "short": .75}[mode]
    mc = (0., {"tall": 2.0, "medium": 1.75, "short": 1.8}[mode])                                      # binary centre in world (X, D)
    m = [(mc[0] + sep * math.cos(phase), mc[1] + sep * .55 * math.sin(phase)),
         (mc[0] - sep * math.cos(phase), mc[1] - sep * .55 * math.sin(phase))]
    sheet_h = y0 + H - horizon
    Xspan = W / 2
    A = sheet_h * (.30 if not small else .22)            # well depth scale (px at D=1)
    k_wave = 10.                                          # radial wavenumber of the ripples

    def dip(X, D):
        s = 0.
        for mx, md in m:
            r2 = (X - mx) ** 2 + ((D - md) * 1.5) ** 2
            s += 1 / math.sqrt(r2 + .1)
        well = s - 2 / math.sqrt(4.)                      # ~0 far away
        rx, rd = X - mc[0], (D - mc[1]) * 1.5
        r = math.hypot(rx, rd)
        th = math.atan2(rd, rx)
        env = (r / (r + .6)) * math.exp(-r / 2.4)
        ripple = .07 * math.cos(2 * th - k_wave * r + 2 * phase) * env
        return max(0., well) * .3 + ripple

    def proj(X, D):
        t = (1 / D - 1 / D1) / (1 / D0 - 1 / D1)
        sx = cx + X * Xspan / D
        sy = horizon + t * sheet_h * .98 + dip(X, D) * A / D
        return sx, sy

    def steep(X, D):
        e = .04
        return abs(dip(X + e, D) - dip(X - e, D)) + abs(dip(X, D + e) - dip(X, D - e))

    # white sheet under everything below the far edge (the far edge undulates a little)
    nx = 70
    Xmax = D1 * 1.25
    far = [proj(-Xmax + 2 * Xmax * i / nx, D1) for i in range(nx + 1)]
    sheet = far + [(x0 + W + 6, y0 + H + 6), (x0 - 6, y0 + H + 6)]
    o.append(_fill([sheet]))

    # fine rules of constant depth (the sheet's tone), major grid lines heavier
    nd_major = 9 if not small else 6
    sub = 4 if not small else 3
    hair, major, deep = [], [], []
    nsamp = 90
    for j in range(nd_major * sub + 1):
        u = j / (nd_major * sub)
        D = 1 / (1 / D0 + (1 / D1 - 1 / D0) * u)          # even spacing on screen, before the dip
        if D < D0 * .62:
            continue
        pts = [proj(-Xmax + 2 * Xmax * i / nsamp, D) for i in range(nsamp + 1)]
        if j % sub == 0:
            major.append(pts)
        else:
            hair.append(pts)
    # lines running into the distance
    nX = 22 if not small else 14
    for i in range(-nX, nX + 1):
        X = Xmax * i / nX
        pts = [proj(X, D0 * .62 + (D1 - D0 * .62) * q / 60) for q in range(61)]
        major.append(pts) if i % 2 == 0 else hair.append(pts)
        # half-lines inside the wells for shading
        if i < nX:
            Xh = Xmax * (i + .5) / nX
            ds = [D0 * .62 + (D1 - D0 * .62) * q / 80 for q in range(81)]
            ph = [proj(Xh, d) for d in ds]
            deep += _split(ph, lambda q, Xh=Xh, ds=ds: steep(Xh, ds[q]) > .035)
    # cross-hatch in the steep throat of each well
    for j in range(nd_major * sub * 2 + 1):
        u = (j + .5) / (nd_major * sub * 2)
        D = 1 / (1 / D0 + (1 / D1 - 1 / D0) * u)
        Xs = [-Xmax + 2 * Xmax * i / 140 for i in range(141)]
        pts = [proj(X, D) for X in Xs]
        deep += _split(pts, lambda q, Xs=Xs, D=D: steep(Xs[q], D) > .065)
    o.append(_path(hair + deep, .5))
    o.append(_path(major, 1. if not small else .5))

    # wave crests: the two-armed spiral, drawn as swelling lines across the sheet
    crest, crest_w = [], []
    for arm in range(2):
        pts = []
        for q in range(300):
            r = .2 + q * .014
            th = (k_wave * r - 2 * phase + arm * TAU) / 2
            X = mc[0] + r * math.cos(th)
            D = mc[1] + r * math.sin(th) / 1.5
            if D < D0 * .65 or D > D1 or abs(X) > Xmax:
                pts.append(None)
                continue
            pts.append((proj(X, D), r))
        run, rw = [], None
        for p in pts + [None]:
            wgt = None if p is None else (1.5 if p[1] < 1.3 else 1. if p[1] < 2.6 else .5)
            if small and wgt:
                wgt = min(wgt, 1.)
            if p is None or wgt != rw:
                if len(run) > 1:
                    crest_w.append((rw, run))
                run = run[-1:] if p is not None else []
            if p is not None:
                run.append(p[0])
                rw = wgt
    for wv in (.5, 1., 1.5):
        o.append(_path([r for ww, r in crest_w if ww == wv], wv))

    # the two black holes, each a black sphere ringed by a shaded accretion disc
    bodies = sorted(m, key=lambda p: p[1], reverse=True)          # far one first
    for X, D in bodies:
        sx, sy = proj(X, D)
        rb = max(3., (sheet_h * {'tall': .2, 'medium': .3, 'short': .26}[mode]) / D)
        cyb = sy - rb * .55
        rx, ry = rb * 2.3, rb * .62
        back = C._ell_pts(sx, cyb, rx, ry, 40, math.pi, TAU)
        inner_b = C._ell_pts(sx, cyb, rb * 1.25, ry * .5, 30, math.pi, TAU)
        ring_back = back + inner_b[::-1]
        o.append(_fill([ring_back], "#fff", "#000", .5))
        o.append(_path(C.hatch_poly(ring_back, 0, 1.5), .5, tol=0))
        disc = C._ell_pts(sx, cyb, rb, rb, 36)[:-1]
        o.append(_fill([disc], "#000"))
        # photon ring and a lensed glint
        o.append(_path([C._ell_pts(sx, cyb, rb * .78, rb * .78, 30, 3.5, 5.3)], .5, "#fff"))
        front = C._ell_pts(sx, cyb, rx, ry, 40, 0, math.pi)
        inner_f = C._ell_pts(sx, cyb, rb * 1.25, ry * .5, 30, 0, math.pi)
        ring_front = front + inner_f[::-1]
        o.append(_fill([ring_front], "#fff", "#000", .5))
        # shade the disc's underside: hatching thickening toward the front edge
        o.append(_path(C.hatch_poly(ring_front, 0, 1.5, .75), .5, tol=0))
        o.append(_path([C._ell_pts(sx, cyb, rx * .7, ry * .72, 30, .15, math.pi - .15)], .5))

    # ---- stars, LISA, Earth ----
    sky_h = horizon - y0
    stars = []
    srng = random.Random(seed * 13 + 5)
    for _ in range(int(W * sky_h / (260 if not small else 180))):
        sx, sy = x0 + srng.random() * W, y0 + srng.random() * (sky_h - 3)
        stars.append(C._ell_pts(sx, sy, .9, .9, 6)[:-1] if srng.random() < .8 else _star(sx, sy, 2.4))

    if not small:
        # Easter egg: a constellation tracing a 'P' (Parker), tucked toward the left of the sky
        ps = max(1., sky_h / 40)
        px, py = x0 + W * .27, y0 + sky_h * .18
        Pp = [(0, 18), (0, 9), (0, 0), (6, 0), (9.5, 4.5), (6, 9), (0, 9)]
        Pp = [(px + a * ps, py + b * ps) for a, b in Pp]
        o.append(_path([Pp], 1., "#fff", 0))
        for i, (sx, sy) in enumerate(Pp[:-1]):
            stars.append(_star(sx, sy, 2.6 * ps if i in (0, 3) else 1.9 * ps))

        # Earth: a hatched globe low in the sky, LISA's triangle trailing it
        er = max(6., sky_h * .28)
        ex, ey = x0 + W * .80, y0 + sky_h * .52
        globe = C._ell_pts(ex, ey, er, er, 40)[:-1]
        o.append(_fill([globe], "#fff", "#000", 1))
        # night side: curved hatching (lines of latitude) on the lower right
        lat = []
        for i in range(1, 12):
            yy = -er + 2 * er * i / 12
            half = math.sqrt(max(0., er * er - yy * yy))
            seg = []
            for q in range(21):
                xx = -half + 2 * half * q / 20
                if xx * .55 + yy * .35 > -er * .25:   # terminator
                    seg.append((ex + xx, ey + yy))
            if len(seg) > 1:
                lat.append(seg)
        dense = []
        for i in range(1, 24):
            yy = -er + 2 * er * i / 24
            half = math.sqrt(max(0., er * er - yy * yy))
            seg = [(ex + xx, ey + yy) for xx in [-half + 2 * half * q / 20 for q in range(21)]
                   if xx * .55 + yy * .35 > er * .35]
            if len(seg) > 1:
                dense.append(seg)
        # continents: a few stippled blobs on the lit side
        cont = []
        for c0 in range(3):
            a = srng.uniform(2.2, 4.2)
            rr = srng.uniform(.25, .55) * er
            ccx, ccy = ex + math.cos(a) * rr, ey + math.sin(a) * rr
            blob = [(ccx + er * .22 * (1 + .3 * math.sin(3 * t + c0)) * math.cos(t),
                     ccy + er * .16 * (1 + .3 * math.cos(2 * t)) * math.sin(t)) for t in [TAU * q / 16 for q in range(17)]]
            cont.append(blob)
        o.append(_path(lat, .5))
        o.append(_path(dense, 1.))

        # LISA: three spacecraft 2.5 million km apart, laser arms between them
        L = min(W * .30, sky_h * 1.1)
        tx, ty = ex - er * 1.9 - L * .55, ey - sky_h * .05
        rot = .35 + phase * .2
        tri = [(tx + L * .58 * math.cos(rot + TAU * i / 3), ty + L * .58 * .42 * math.sin(rot + TAU * i / 3)) for i in range(3)]
        o.append(_path([tri + [tri[0]]], 1., "#fff", 0))
        o.append(_path([tri + [tri[0]]], .5, "#000", 0, ' stroke-dasharray="0 3"'))
        for (sx, sy) in tri:
            craft = C._ell_pts(sx, sy, 3., 2., 12)[:-1]
            o.append(_fill([craft], "#fff", "#000", .5))
            o.append(_path([[(sx - 2.2, sy - .2), (sx + 2.2, sy - .2)], [(sx - 4.5, sy), (sx - 2.5, sy)],
                            [(sx + 2.5, sy), (sx + 4.5, sy)]], .5, tol=0))
    o.append(_fill(stars, "#fff"))

    body = "".join(o)
    cid = C._uid("sci", x0, y0, W, H, seed, mode)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------------
# frame pieces with the white spots engraved
# ------------------------------------------------------------------------------------------------

def chirp_tablet(tx, ty, tw, th):
    """The pedestal tablet cut with the GW150914-style chirp: a wave tightening and swelling to the
    merger, then ringing down."""
    o = [f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-(tw - 2))}z" fill="{pat("L")}" stroke="none"/>']
    cy = ty + th / 2
    amp = th * .36
    pts = []
    n = 900
    tm = .82
    for i in range(n + 1):
        t = i / n
        if t < tm:
            tau = (tm - t) + .004
            f = 14 * tau ** (-3 / 8)
            ph = -2 * math.pi * (8 / 5) * 14 * tau ** (5 / 8) * 2.2
            a = amp * min(1., (.08 / tau) ** .25) * min(1., t * 8)
        else:
            dt = t - tm
            ph = 2 * math.pi * 140 * dt
            a = amp * math.exp(-dt * 40)
        pts.append((tx + 4 + (tw - 8) * t, cy - a * math.cos(ph)))
    o.append(f'<path d="M{_n(tx + 4)},{_n(cy)}h{_n(tw - 8)}" stroke="#000" stroke-width=".5" stroke-dasharray="1 2"/>')
    o.append(_path([pts], 1., tol=.12))
    return "".join(o)


def ripple_banner_fill(centre, h):
    """Undulating rules along the banner face (between its edge contours)."""
    lines = []
    L = len(centre)
    for s in (-.48, -.24, 0., .24, .48):
        pts = []
        for i in range(L - 1):
            for q in range(4):
                u = (i + q / 4)
                x = centre[i][0] + (centre[i + 1][0] - centre[i][0]) * q / 4
                y = centre[i][1] + (centre[i + 1][1] - centre[i][1]) * q / 4
                env = math.sin(math.pi * u / (L - 1))
                pts.append((x, y + s * h / 2 + h * .09 * env * math.sin(u * 1.2 + s * 3)))
        lines.append(pts)
    return _path(lines, .5)


def armillary(cx, cy, R, seed=0):
    """An armillary sphere on a short baluster: hatched globe inside three tilted ring bands, the
    rings' back halves passing behind the globe and their front halves before it."""
    cv = C.Canvas()
    rings = [(0., .32), (1.05, .30), (-1.05, .30)]          # (tilt, minor/major)
    bw = max(2.2, R * .12)

    def band(tilt, k, a0, a1, rr):
        ct, st = math.cos(tilt), math.sin(tilt)
        out, inn = [], []
        for i in range(25):
            t = a0 + (a1 - a0) * i / 24
            for lst, r in ((out, rr), (inn, rr - bw)):
                x, y = r * math.cos(t), r * k * math.sin(t)
                lst.append((cx + x * ct - y * st, cy + x * st + y * ct))
        return out + inn[::-1], out, inn

    # baluster and foot
    st = [(cx - R * .1, cy + R * .95), (cx - R * .16, cy + R * 1.25), (cx - R * .42, cy + R * 1.45),
          (cx + R * .42, cy + R * 1.45), (cx + R * .16, cy + R * 1.25), (cx + R * .1, cy + R * .95)]
    cv.obj([st], 1.)
    cv.hair(C.hatch_poly(st, 90, 1.5, R * .05))
    for tilt, k in rings:
        poly, o_, i_ = band(tilt, k, math.pi, TAU, R)
        cv.obj([poly], 1.)
        cv.hair(C.hatch_poly(poly, 90 + math.degrees(tilt), 1.5))
    g = C._ell_pts(cx, cy, R * .62, R * .62, 40)[:-1]
    cv.obj([g], 1.)
    # globe: latitude rules, closing up on the shadow side
    for i in range(1, 16):
        yy = -R * .62 + R * 1.24 * i / 16
        half = math.sqrt(max(0., (R * .62) ** 2 - yy * yy))
        seg = [(cx + xx, cy + yy) for xx in [-half + 2 * half * q / 16 for q in range(17)]
               if xx * .6 + yy * .4 > -R * .05]
        if len(seg) > 1:
            cv.hair(seg)
    for j in (-.35, 0., .35):
        cv.hair(C._ell_pts(cx, cy, R * .62 * abs(math.cos(j * 2.6)) + .1, R * .62, 30, -math.pi / 2, math.pi / 2)
                if j >= 0 else C._ell_pts(cx, cy, R * .62 * .55, R * .62, 30, math.pi / 2, 1.5 * math.pi))
    for tilt, k in rings:
        poly, o_, i_ = band(tilt, k, 0., math.pi, R)
        cv.obj([poly], 1.)
        cv.hair(C.hatch_poly(poly, 90 + math.degrees(tilt), 2.))
        cv.hair(o_[2:-2])
    # axis pin and finial
    cv.obj([C._ell_pts(cx, cy - R * 1.08, R * .1, R * .1, 12)[:-1]], 1.)
    cv.line([(cx, cy - R * .98), (cx, cy - R * .62)])
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts (house layouts, copied so the cartouche field and frame blanks can be engraved)
# ------------------------------------------------------------------------------------------------

def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(spacetime_scene(cx - rx, cy - ry, 2 * rx, 2 * ry, field, seed, "short"))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(9 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(spacetime_scene(cx - a, cy - b, 2 * a, 2 * b, field, seed, "medium"))
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
    # the light-ruled air the crest rises into (no bare paper)
    o.append(C.dark_ground((0, 0, w, py0 + 2), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .60
    cx, cy = w / 2, py0 + ph * .45
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
                   max_n=int(7 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(spacetime_scene(cx - a, cy - b, 2 * a, 2 * b, field, seed, "tall"))
    bp = C._superellipse(cx, cy, a - .3, b - .3)
    o.append(_path([bp + [bp[0]]], 1.))
    room = cy - ch / 2
    R = max(10., min(40., room * .36))
    fcv = C.Canvas()
    for side in (-1, 1):
        C.acanthus_frond(cx + side * R * .2, cy - ch / 2 + 6, -90 + side * 62, R * 2.1, n=3, spread=34,
                         bend=.9 * side, curl=4.5 * side, seed=seed + side, cv=fcv)
    o.append(fcv.svg())
    o.append(armillary(cx, cy - ch / 2 - R * 1.45 + 2, R, seed))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(ripple_banner_fill(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, min(ped_h, h - py)), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(chirp_tablet(tx + 2, ty + 2, tw - 2, th - 2))
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
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
