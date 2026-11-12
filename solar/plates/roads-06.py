"""roads-06 -- "Earthquakes this week" (USGS rumbles within 190 miles; small quakes under Mount Rainier).

The plate: Mount Rainier, glaciated and ridged, wearing a lenticular cloud cap, rising out of
forested foothills; under the ground the earth is cut away in section -- folded strata broken by a
fault, with seismic rings radiating from a hypocentre beneath the mountain. The ribbon banner carries
this week's seismogram; the pedestal tablet is a helicorder strip with one spike per quake.
Easter egg: a pair of crossed drumsticks buried in the strata like a fossil (a drum roll is a rumble).
"""
import sys
import math
import random
import datetime
import engraving_codex as C

_n = C._n


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _hscan(poly, y):
    """x-intervals of a closed polygon on the horizontal line y (even-odd)."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    xs.sort()
    return [(xs[j], xs[j + 1]) for j in range(0, len(xs) - 1, 2)]


def _inside(poly, x, y):
    return any(a <= x <= b for a, b in _hscan(poly, y))


def _keep(pl, pred):
    """Split a polyline into the runs whose points satisfy pred."""
    out, cur = [], []
    for p in pl:
        if pred(p):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _between(up, lo, t):
    return [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(up, lo)]


def _resample(pl, n):
    L = [0.]
    for i in range(1, len(pl)):
        L.append(L[-1] + math.hypot(pl[i][0] - pl[i - 1][0], pl[i][1] - pl[i - 1][1]))
    tot = L[-1] or 1.
    out, j = [], 0
    for k in range(n + 1):
        d = tot * k / n
        while j < len(pl) - 2 and L[j + 1] < d:
            j += 1
        seg = (L[j + 1] - L[j]) or 1.
        t = min(1., max(0., (d - L[j]) / seg))
        out.append((pl[j][0] + (pl[j + 1][0] - pl[j][0]) * t, pl[j][1] + (pl[j + 1][1] - pl[j][1]) * t))
    return out


def prof_at_x(prof, x):
    for i in range(len(prof) - 1):
        if prof[i][0] <= x <= prof[i + 1][0]:
            t = (x - prof[i][0]) / max(1e-6, prof[i + 1][0] - prof[i][0])
            return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * t
    return prof[-1][1]


def _moon_age(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .5
    return (days % 29.530588) / 29.530588      # 0 new, .5 full


def _seed(ctx):
    return sum(map(ord, (ctx or {}).get("date", "2026-11-11"))) * 7 + (ctx or {}).get("sheet", 0)


# ------------------------------------------------------------------------------------------------
# the vignette: Rainier over a cut-away section of the shaking earth
# ------------------------------------------------------------------------------------------------

def scene(field, ctx, detail=1.0, ground=True):
    """Fill the closed polygon `field` completely. detail ~ .4 (band medallion) .. 1 (tall)."""
    rng = random.Random(_seed(ctx))
    X0 = min(p[0] for p in field); X1 = max(p[0] for p in field)
    Y0 = min(p[1] for p in field); Y1 = max(p[1] for p in field)
    W, H = X1 - X0, Y1 - Y0
    cv = C.Canvas()

    y_base = Y0 + H * (.60 if ground else .80)        # foot of the mountain (hidden by hills)
    y_g = Y0 + H * (.66 if ground else .86)           # the ground surface / top of the section
    m_h = H * (.40 if ground else .52)
    m_x0, m_x1 = X0 - W * .12, X1 + W * .08
    sx = m_x0 + (m_x1 - m_x0) * .56                   # summit

    # ---- sky: ruled horizontal lines, close at the zenith, opening toward the horizon
    cv.obj([field], 0)
    y = Y0 + .75
    sky = []
    while y < y_g + 2:
        for a, b in _hscan(field, y):
            sky.append([(a, y), (b, y)])
        t = (y - Y0) / max(1., y_g - Y0)
        y += 2. if t < .9 else 3.
    cv.hair(sky)

    # ---- moon, phase by date (upper left)
    age = _moon_age((ctx or {}).get("date", ""))
    mr = max(4., H * .055)
    mx, my = X0 + W * .2, Y0 + H * .16 + mr * .6
    if _inside(field, mx - mr - 2, my) and _inside(field, mx, my - mr - 2):
        disc = C._ell_pts(mx, my, mr, mr, 40)[:-1]
        cv.obj([disc], .5)
        # the dark limb: a terminator ellipse, ruled close
        k = math.cos(age * 2 * math.pi)
        sg = 1 if age < .5 else -1           # waxing: dark on the left
        dark = []
        for i in range(41):
            v = -1 + 2 * i / 40
            dark.append((mx - sg * mr * math.sqrt(max(0, 1 - v * v)), my + mr * v))
        for i in range(41):
            v = 1 - 2 * i / 40
            dark.append((mx + sg * mr * k * math.sqrt(max(0, 1 - v * v)), my + mr * v))
        cv.hair(C.hatch_poly(dark, 0, 1.5, .3))
        for (u, v, rr) in ((-.3, -.2, .22), (.25, .3, .16), (.1, -.45, .12), (-.1, .45, .1)):
            cv.hair([C._ell_pts(mx + u * mr, my + v * mr, rr * mr, rr * mr, 10)])

    # ---- the mountain: Rainier's broad dome, Liberty Cap, Point Success, Little Tahoma
    prof = []
    NP = 90
    for i in range(NP + 1):
        u = i / NP
        d = (u - .5) / .5
        ad = abs(d)
        v = min(1., ((1 - ad) / .8) ** 1.7)
        if ad < .2:
            v = 1 - .05 * (d / .2) ** 2
        v += .045 * math.exp(-((d + .19) / .035) ** 2)            # Liberty Cap
        v += .07 * math.exp(-((d - .37) / .03) ** 2)              # Little Tahoma
        v += .012 * math.sin(u * 61 + 1.3) * (1 - ad) + rng.uniform(-.004, .004)
        prof.append((m_x0 + (m_x1 - m_x0) * u, y_base - m_h * max(0., v if 0 < i < NP else 0.)))
    peak = min(prof, key=lambda p: p[1])
    sx = (m_x0 + m_x1) / 2 + (m_x1 - m_x0) * .02
    peak = (sx, prof_at_x(prof, sx))

    def prof_at(x):
        for i in range(len(prof) - 1):
            if prof[i][0] <= x <= prof[i + 1][0]:
                t = (x - prof[i][0]) / max(1e-6, prof[i + 1][0] - prof[i][0])
                return prof[i][1] + (prof[i + 1][1] - prof[i][1]) * t
        return y_base

    mountain = prof + [(m_x1, y_base + 4), (m_x0, y_base + 4)]

    # ---- lenticular cloud cap over the summit (Rainier's signature)
    if detail > .5:
        lw, lh = W * .36, max(4., H * .05)
        lx, ly = sx - W * .01, peak[1] - lh * 1.05
        for k2, (dx, dy, s) in enumerate(((W * .02, -lh * .95, .6), (0, 0, 1.0))):
            top = [(lx + dx + lw * s * (i / 30 - .5), ly + dy - lh * s * .55 * math.sin(math.pi * i / 30) ** .7) for i in range(31)]
            bot = [(lx + dx + lw * s * (.5 - i / 30), ly + dy + lh * s * .45 * math.sin(math.pi * (1 - i / 30)) ** .7) for i in range(31)]
            lens = top + bot[1:-1]
            cv.obj([lens], .5)
            for t in (.3, .6):
                cv.hair([_between(top, bot[::-1][1:] + [top[-1]], t)])
            cv.hair(C.hatch_poly([(p[0], ly + dy + .6) for p in top] + bot[1:-1], 0, 1.5))

    cv.obj([mountain], 1.)
    NR = 26
    ridge_spec = [(.30, .12), (.36, .22), (.42, .32), (.48, .42), (.54, .53), (.60, .64), (.66, .75), (.73, .86)]
    ridges = []
    for tu, bu in ridge_spec:
        tx = m_x0 + (m_x1 - m_x0) * tu
        ty = prof_at(tx) + 1.2
        bx = m_x0 + (m_x1 - m_x0) * bu
        pts = []
        for i in range(NR + 1):
            t = i / NR
            x = tx + (bx - tx) * (t ** .85)
            yy = ty + (y_base + 3 - ty) * t
            x += math.sin(t * 9 + tu * 23) * W * .005 * t
            pts.append((x, yy))
        ridges.append(pts)
    # the flanks' outer boundaries, resampled to the ridges' point count
    lf = _resample([p for p in prof if p[0] <= ridges[0][0][0]][::-1] + [(m_x0, y_base + 3)], NR)
    rf = _resample([p for p in prof if p[0] >= ridges[-1][0][0]] + [(m_x1, y_base + 3)], NR)
    bands = [(lf, ridges[0])] + [(ridges[i], ridges[i + 1]) for i in range(len(ridges) - 1)] + [(ridges[-1], rf)]
    hair, line = [], []
    for fi, (A, B) in enumerate(bands):
        shade = A[0][0] > sx + W * .01 or fi == len(bands) - 1
        poly = A + B[::-1]
        # flow lines down the glacier, laid coarse-to-fine so they never crowd at the summit
        pitch = 2.0 if shade else 4.0
        for d in range(1, 6):
            for k in range(1, 2 ** d, 2):
                f = k / 2 ** d
                pl = _between(A, B, f)
                keep = [p for j, p in enumerate(pl) if math.hypot(A[j][0] - B[j][0], A[j][1] - B[j][1]) / 2 ** d >= pitch]
                if len(keep) > 1:
                    hair.append(keep)
        if shade:
            if fi >= len(bands) - 4:
                hair += C.hatch_poly(poly, 32, 3, fi * .7)
            if fi >= len(bands) - 2:
                hair += C.hatch_poly(poly, -62, 3, fi * .4)
        elif detail > .55:
            # crevasses: short arcs across the flow, thickest where the ice steepens
            for j in range(3, NR - 4, 2):
                wj = math.hypot(A[j][0] - B[j][0], A[j][1] - B[j][1])
                if wj < 6:
                    continue
                for _ in range(1 + int(wj / 9)):
                    f0 = rng.uniform(.12, .75)
                    p0 = _between([A[j]], [B[j]], f0)[0]
                    p1 = _between([A[j]], [B[j]], min(.92, f0 + rng.uniform(.12, .22)))[0]
                    m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 1.0)
                    hair.append([p0, m, p1])
    # rock cleavers: each ridge a dark rib, its shadow side wider below
    for i, R in enumerate(ridges):
        lit = R[0][0] < sx
        wid = [(.6 + W * (.012 if lit else .006) * (j / NR) ** .7) for j in range(NR + 1)]
        rib = R + [(p[0] + w, p[1] + .2) for p, w in zip(R, wid)][::-1]
        hair.extend(C.hatch_poly(rib, -60, 1.5, .2))
        hair.extend(C.hatch_poly(rib, 30, 1.5, .5))
        line.append(R[:int(NR * .75)])
    cv.hair(hair)
    cv.line(line)
    cv.line([p for p in prof if abs(p[0] - sx) < W * .25])

    # ---- foothills: far ridge (ruled), near ridge (forested, dark)
    def ridge_poly(yb, amp, freq, ph, trees, bottom):
        pts = []
        x = X0 - 2
        while x <= X1 + 2:
            yy = yb + amp * math.sin(x / W * freq + ph) + amp * .5 * math.sin(x / W * freq * 2.7 + ph * 2)
            pts.append((x, yy))
            if trees:
                pts.append((x + 1.2, yy - trees * (0.6 + .4 * rng.random())))
                x += 2.6
            else:
                x += 3
        return pts + [(X1 + 2, bottom), (X0 - 2, bottom)]

    far = ridge_poly(y_base - H * .055, H * .02, 9, rng.uniform(0, 6), 0, y_g + 3)
    cv.obj([far], .5)
    cv.hair(C.hatch_poly(far, 0, 1.5, .5))
    near = ridge_poly(y_base + H * .005, H * .025, 6, rng.uniform(0, 6), 3.2 if detail > .5 else 1.5, y_g + 3)
    cv.obj([near], 1.)
    cv.hair(C.hatch_poly(near, 84, 1.5, .2))
    cv.hair(C.hatch_poly(near, 15, 3, .4))

    if ground:
        _section(cv, field, X0, X1, Y0, Y1, W, H, y_g, sx, rng, detail)
    else:
        # meadow foreground with a seismogram scratched across it
        fg = [(X0 - 2, y_g)] + [(X1 + 2, y_g), (X1 + 2, Y1 + 2), (X0 - 2, Y1 + 2)]
        cv.obj([fg], 1.)
        cv.hair(C.hatch_poly(fg, 0, 2, .3))
        tr = _trace(X0, X1, (y_g + Y1) / 2, (Y1 - y_g) * .32, rng, 1.6)
        cv.obj([[(X0 - 2, (y_g + Y1) / 2 - (Y1 - y_g) * .38), (X1 + 2, (y_g + Y1) / 2 - (Y1 - y_g) * .38),
                 (X1 + 2, (y_g + Y1) / 2 + (Y1 - y_g) * .38), (X0 - 2, (y_g + Y1) / 2 + (Y1 - y_g) * .38)]], .5)
        cv.line(tr)

    cid = C._uid("rn", round(X0, 1), round(Y0, 1), round(W, 1), round(H, 1), detail)
    return (f'<clipPath id="{cid}"><path d="{C._d(field, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


def _trace(x0, x1, yc, amp, rng, step=1.2, bursts=None):
    """A seismogram: quiet microseism with a few decaying bursts."""
    n = int((x1 - x0) / step)
    if bursts is None:
        bursts = [(rng.uniform(.08, .92), rng.uniform(.35, 1.0)) for _ in range(5)]
    pts = []
    for i in range(n + 1):
        t = i / n
        a = .08 + .05 * rng.random()
        for c, m in bursts:
            d = t - c
            if d >= 0:
                a += m * math.exp(-d * 60) * (1 if d < .004 else .9)
        sgn = 1 if i % 2 else -1
        pts.append((x0 + (x1 - x0) * t, yc + sgn * amp * min(1., a) * (.6 + .4 * rng.random())))
    return pts


def _section(cv, field, X0, X1, Y0, Y1, W, H, y_g, sx, rng, detail):
    """The earth cut away below the surface: folded strata, a fault, seismic rings, a fossil egg."""
    fx_top, fx_bot = sx + W * .17, sx - W * .02          # fault trace, surface to depth
    throw = max(2., H * .018)

    def fault_x(y):
        t = (y - y_g) / max(1., Y1 - y_g)
        return fx_top + (fx_bot - fx_top) * t + math.sin(t * 17) * 1.2

    depth = Y1 - y_g
    nlay = 5 if detail > .6 else 3
    bounds = []
    for k in range(nlay + 1):
        d0 = depth * k / nlay
        pts = []
        x = X0 - 3
        ph = rng.uniform(0, 6)
        while x <= X1 + 3:
            if k == 0:
                yy = y_g + .8 * math.sin(x * .4 + ph) * (1 if rng.random() > .5 else .4)
            else:
                yy = y_g + d0 + depth * .05 * math.sin((x - X0) / W * 5.5 + k * .9) - depth * .04 * (1 - ((x - sx) / W) ** 2 * 4)
                if x > fault_x(yy):
                    yy += throw
            pts.append((x, yy))
            x += 2.
        if k == nlay:
            pts = [(p[0], Y1 + 3) for p in pts]
        bounds.append(pts)
    surf = bounds[0]
    earth = surf + [(X1 + 3, Y1 + 3), (X0 - 3, Y1 + 3)]
    cv.obj([earth], 1.)
    styles = ["contour2", "pebble", "contour3x", "contour2d", "dark"]
    for k in range(nlay):
        up, lo = bounds[k], bounds[k + 1]
        th = sum(b[1] - a[1] for a, b in zip(up, lo)) / len(up)
        st = styles[k % len(styles)] if detail > .6 else ["contour2", "contour3x", "dark"][k]
        poly = up + lo[::-1]
        if st.startswith("contour"):
            pitch = 2. if "2" in st else 3.
            m = max(1, int(th / pitch))
            for j in range(1, m):
                cv.hair(_between(up, lo, j / m))
            if st.endswith("x"):
                cv.hair(C.hatch_poly(poly, 60, 3, .4))
            if st.endswith("d"):
                cv.hair(C.hatch_poly(poly, -35, 3, .4))
        elif st == "pebble":
            m = max(1, int(th / 3))
            for j in range(1, m):
                cv.hair(_between(up, lo, j / m))
        else:
            cv.hair(C.hatch_poly(poly, 0, 1.5, .2))
            cv.hair(C.hatch_poly(poly, 70, 3, .4))
        cv.line(lo)
    # pebbles in the conglomerate bed (white stones with a shaded underside)
    if detail > .6:
        up, lo = bounds[1], bounds[2]
        for _ in range(int(30 * detail)):
            i = rng.randrange(len(up))
            yy = up[i][1] + (lo[i][1] - up[i][1]) * rng.uniform(.25, .75)
            r = rng.uniform(1.3, 2.6)
            cv.obj([C._ell_pts(up[i][0], yy, r * 1.4, r, 12)[:-1]], .5)
            cv.hair([C._ell_pts(up[i][0] + .3, yy + .4, r * 1.0, r * .55, 10, .3, 2.8)])

    # the fault: a black, jagged break through every bed
    fl = []
    y = y_g - 1
    while y <= Y1 + 3:
        fl.append((fault_x(y) + rng.uniform(-.6, .6), y))
        y += 2.5
    cv.obj([], 0)
    cv.heavy(fl)
    # surface scarp
    cv.line([(fx_top - 3, y_g - .5), (fx_top, y_g - 1.5), (fx_top + 2, y_g + throw * .6)])

    # hypocentre under the mountain, rings of waves through the rock
    hx, hy = sx + W * .05, y_g + depth * .72
    rings = []
    rmax = max(W * .42, depth * 1.05)
    r = 4.
    k = 0
    while r < rmax:
        arc = C._ell_pts(hx, hy, r, r * .82, max(24, int(r * 1.6)))
        top_y = lambda p: p[1] > y_g + 2.5 and Y0 < p[1]
        segs = _keep(arc, top_y)
        rings.append((r, segs))
        r += 4.5 + k * 1.3
        k += 1
    for r, segs in rings:
        for s in segs:
            # a white wave front cut through the beds, ruled on its inner edge
            band = []
            for p in s:
                band.append(p)
            inner = [(hx + (p[0] - hx) * (r - 1.6) / r, hy + (p[1] - hy) * (r - 1.6) / r) for p in s]
            cv.obj([band + inner[::-1]], 0)
            cv.line(s)
            cv.hair(inner)
    # focus: a black star
    star = []
    for i in range(16):
        a = math.pi * 2 * i / 16
        rr = 3.6 if i % 2 == 0 else 1.3
        star.append((hx + rr * math.cos(a), hy + rr * math.sin(a)))
    cv.obj([star], 1.)
    cv.line(C.hatch_poly(star, 0, .8))
    # Easter egg: crossed drumsticks fossilised in the second bed, left of the mountain
    if detail > .6:
        ex = X0 + W * .3
        up, lo = bounds[-2], bounds[-1]
        i = min(range(len(up)), key=lambda j: abs(up[j][0] - ex))
        ey = up[i][1] + min(9., (Y1 - up[i][1]) * .35)
        L = max(16., min(24., W * .08))
        for a in (math.radians(-22), math.radians(180 + 22)):
            ux, uy = math.cos(a), math.sin(a)
            vx, vy = -uy, ux
            bx, by = ex - ux * L / 2, ey - uy * L / 2
            pts_l, pts_r = [], []
            for j in range(11):
                t = j / 10
                w = 1.5 - .7 * t ** 1.5
                px, py = bx + ux * L * t, by + uy * L * t
                pts_l.append((px + vx * w, py + vy * w))
                pts_r.append((px - vx * w, py - vy * w))
            stick = pts_l + pts_r[::-1]
            cv.obj([stick], .5)
            cv.hair([[(bx + ux * L * t - vx * .5, by + uy * L * t - vy * .5) for t in (0, .85)]])
            tx, ty = bx + ux * (L + 1.2), by + uy * (L + 1.2)
            tip = C._ell_pts(tx, ty, 1.6, 1.1, 10)[:-1]
            tip = [(tx + (p[0] - tx) * ux - (p[1] - ty) * uy, ty + (p[0] - tx) * uy + (p[1] - ty) * ux) for p in tip]
            cv.obj([tip], .5)

    # epicentre tremor ticks on the surface above it
    ex = hx
    for j in (-1, 1):
        for q in range(3):
            d = 4 + q * 3
            cv.hair([(ex + j * d, y_g - 1.5 - q * .2), (ex + j * (d + 1.2), y_g - 3.5 + (q % 2)), (ex + j * (d + 2.2), y_g - 1.2)])


# ------------------------------------------------------------------------------------------------
# frames
# ------------------------------------------------------------------------------------------------

_K = 2 ** (-1 / 2.6)


def _field_from_rect_cartouche(ix, iy, iw, ih):
    a, b = iw / 2 / _K + 6, ih / 2 / _K + 6
    return C._superellipse(ix + iw / 2, iy + ih / 2, a + .3, b + .3, 2.6, 140)


def _seismo_on_ribbon(centre, h, rng):
    """This week's seismogram engraved on the ribbon's face (follows its arch)."""
    pts = []
    n = len(centre)
    dense = []
    for i in range(n - 1):
        for j in range(8):
            t = j / 8
            dense.append((centre[i][0] + (centre[i + 1][0] - centre[i][0]) * t,
                          centre[i][1] + (centre[i + 1][1] - centre[i][1]) * t))
    dense.append(centre[-1])
    x0, x1 = dense[0][0], dense[-1][0]
    tr = _trace(x0 + 4, x1 - 4, 0, h * .33, rng, 1.1,
                bursts=[(.16, .55), (.31, .9), (.47, .5), (.63, 1.0), (.82, .6)])
    out = []
    for (x, dy) in tr:
        k = min(range(len(dense)), key=lambda j: abs(dense[j][0] - x)) if False else None
        # centre y by interpolation
        f = (x - x0) / max(1, x1 - x0) * (len(dense) - 1)
        i = min(int(f), len(dense) - 2)
        cy = dense[i][1] + (dense[i + 1][1] - dense[i][1]) * (f - i)
        out.append((x, cy + dy))
    base = [(p[0], p[1]) for p in dense[2:-2]]
    return (f'<path d="{C._d(base, tol=.2)}" stroke="#000" stroke-width=".5"/>'
            f'<path d="{C._d(out, tol=.15)}" stroke="#000" stroke-width="1"/>')


def _helicorder(tx, ty, tw, th, rng):
    """The pedestal tablet as a helicorder strip: ruled rows, one spike per quake this week (33)."""
    o = []
    x0, x1 = tx + 4, tx + tw - 3
    y0, y1 = ty + 3, ty + th - 1.5
    rows = "".join(f"M{_n(x0)},{_n(y)}H{_n(x1)}" for y in [y0 + (y1 - y0) * k / 4 for k in range(1, 4)] if y1 - y0 > 6)
    if rows:
        o.append(f'<path d="{rows}" stroke="#000" stroke-width=".5"/>')
    mid = (y0 + y1) / 2
    d = []
    q = 33
    for i in range(q):
        x = x0 + 6 + (x1 - x0 - 12) * (i + rng.uniform(-.3, .3)) / (q - 1)
        m = rng.choice([.25, .3, .35, .4, .5, .6]) if i % 7 else rng.choice([.8, .95, 1.0])
        a = (y1 - y0) / 2 * m
        d.append(f"M{_n(x - 1.6)},{_n(mid)}L{_n(x - .8)},{_n(mid - a)}L{_n(x)},{_n(mid + a * .8)}L{_n(x + .8)},{_n(mid - a * .45)}L{_n(x + 1.6)},{_n(mid)}")
    o.append(f'<path d="M{_n(x0)},{_n(mid)}H{_n(x1)}{"".join(d)}" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def _layout_tall(w, h, ctx, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # light ruled ground under the free tips so no paper shows
    o.append(C.dark_ground((0, 0, w, py0 - 3), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .52, ph * .74
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=8, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("rt", w, h, seed), px0, 0, pw, ph + top_free, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    field = C._superellipse(cx, cy, cw / 2 - bw * 1.6 + .3, ch / 2 - bw * 1.6 + .3, 2.6, 160)
    o.append(scene(field, ctx, 1.0, True))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = max(11., min(16, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_seismo_on_ribbon(centre, bh, random.Random(seed + 3)))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py + 3, w, ped_h - 3), "G"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_helicorder(tx, ty, tw, th, random.Random(seed + 9)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("rf", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return C.svg_doc(w, h, "".join(o))


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = _seed(ctx)
    if h > 260:
        return _layout_tall(w, h, ctx, seed)
    if h < 110:
        def fill(ix, iy, iw, ih):
            rx, ry = iw / 2 / .7071 + 5 - 3.2, ih / 2 / .7071 + 5 - 3.2
            field = C._ell_pts(ix + iw / 2, iy + ih / 2, rx, ry, 90)[:-1]
            return scene(field, ctx, .4, False)
        return C.frame_plate(w, h, seed, fill)

    def fill(ix, iy, iw, ih):
        return scene(_field_from_rect_cartouche(ix, iy, iw, ih), ctx, .8 if h > 170 else .55, h > 150)
    return C.frame_plate(w, h, seed, fill)
