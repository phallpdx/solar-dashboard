"""River plate: the Columbia off Sauvie Island, engraved in the house (Codex) style.

The vignette, carved into the cartouche of the house frame: a cargo ship riding the Columbia under
Mt. Hood, the Washington shore beyond, a dolphin of pilings in the foreground with a great blue
heron on it, the Sauvie Island bank with cattails, a leaping salmon (the page's fishing), and the
moon in its real phase for ctx["date"]. Easter egg: a "P" monogram on the ship's funnel.
The tall plate letters THE COLUMBIA on the banner and runs a Vitruvian wave along the pedestal.
"""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d = C._n, C._d
PI, TAU = math.pi, 2 * math.pi


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _ell(cx, cy, rx, ry, n=28, rot=0.):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        t = TAU * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def _bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def _ribbon(center, half):
    """Outline around a centre polyline with half-width half(t), t in 0..1."""
    n = len(center)
    L, R = [], []
    for i in range(n):
        a, b = center[max(0, i - 1)], center[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        w = half(i / (n - 1))
        L.append((center[i][0] + nx * w, center[i][1] + ny * w))
        R.append((center[i][0] - nx * w, center[i][1] - ny * w))
    return L + R[::-1], L, R


def _offset(center, d):
    out = []
    n = len(center)
    for i in range(n):
        a, b = center[max(0, i - 1)], center[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        out.append((center[i][0] - ty / tl * d, center[i][1] + tx / tl * d))
    return out


def _moon_phase(date):
    try:
        d = datetime.datetime.fromisoformat(str(date)[:10] + "T12:00:00")
    except Exception:
        d = datetime.datetime(2026, 11, 11, 12)
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    days = (d - ref).total_seconds() / 86400
    return (days / 29.530588853) % 1.


# ------------------------------------------------------------------------------------------------
# the vignette: the Columbia off Sauvie Island
# ------------------------------------------------------------------------------------------------

def river_scene(cx, cy, a, b, clip_pts, ctx, seed=0, uid="r"):
    """Fill the field (bbox cx +- a, cy +- b; clip_pts its outline) with the river scene."""
    rng = random.Random(seed)
    X0, Y0, W, H = cx - a, cy - b, 2 * a, 2 * b
    S = min(W, H * 1.15)
    big = min(a, b) > 50
    small = min(a, b) < 30
    X = lambda u: X0 + W * u
    Y = lambda v: Y0 + H * v
    cv = C.Canvas()
    hv = Y(.55 if not small else .52)          # horizon (far waterline)
    bot = Y0 + H + 2

    # --- sky: ruled lines, darker aloft, opening toward the horizon -----------------------------
    sky = [(X0 - 2, Y0 - 2), (X0 + W + 2, Y0 - 2), (X0 + W + 2, hv + 1), (X0 - 2, hv + 1)]
    cv.obj([sky], 0)
    y = Y0 - 1
    while y < hv:
        v = (y - Y0) / (hv - Y0)
        cv.hair([(X0 - 2, y), (X0 + W + 2, y)])
        y += 1.5 if v < .3 else (2. if v < .62 else 3.)

    # --- moon in today's phase --------------------------------------------------------------------
    f = _moon_phase((ctx or {}).get("date", ""))
    mx, my, mr = X(.8), Y(.17 if not small else .25), max(3.5, S * .055)
    disc = _ell(mx, my, mr, mr, 36)
    cv.obj([disc], 1.)
    cv.line(C.hatch_poly(disc, 0, 1.5))
    cv.hair(C.hatch_poly(disc, 90, 2))
    k = math.cos(TAU * f)
    lit_frac = (1 - k) / 2
    if lit_frac > .03:
        sgn = 1 if f < .5 else -1
        lit = [(mx + sgn * mr * math.cos(t), my + mr * math.sin(t)) for t in [PI * (i / 24 - .5) for i in range(25)]]
        lit += [(mx + sgn * k * mr * math.cos(t), my + mr * math.sin(t)) for t in [PI * (.5 - i / 24) for i in range(25)]]
        cv.obj([lit], 0)
        cv.hair(C.hatch_poly(lit, 90, 3))
    else:
        # new moon: only the earthshine rim
        cv.obj([], 0)
        cv.hair([(mx + (mr + 1.6) * math.cos(t), my + (mr + 1.6) * math.sin(t))
                 for t in [PI * (-.35 + .7 * i / 20) for i in range(21)]])
        cv.hair([(mx + (mr + 3) * math.cos(t), my + (mr + 3) * math.sin(t))
                 for t in [PI * (-.25 + .5 * i / 16) for i in range(17)]])

    # --- clouds: long scalloped banks, shaded beneath ----------------------------------------------
    if not small:
        for (u0, u1, v0, th) in ((.04, .5, .2, .07), (.5, .98, .36, .055), (.12, .4, .42, .035)):
            xa, xb, yb = X(u0), X(u1), Y(v0) + H * th
            n = 36
            top = []
            for i in range(n + 1):
                t = i / n
                env = math.sin(PI * t) ** .7
                bump = abs(math.sin(PI * t * rng.uniform(4.5, 5.2) + rng.uniform(0, .3)))
                top.append((xa + (xb - xa) * t, yb - H * th * env * (.55 + .45 * bump)))
            poly = top + [(xb, yb), (xa, yb)]
            cv.obj([poly], .5)
            low = [(xa, yb - H * th * .38), (xb, yb - H * th * .38), (xb, yb + 1), (xa, yb + 1)]
            cv.hair(C.hatch_poly(poly, 0, 2))
            cv.hair([q for q in C.hatch_poly(low, 0, 1.5, .75) if True])
            for j in range(4):
                t = rng.uniform(.15, .85)
                x = xa + (xb - xa) * t
                cv.hair(_bez((x - 6, yb - H * th * .5), (x - 2, yb - H * th * .8), (x + 2, yb - H * th * .8), (x + 6, yb - H * th * .55), 6))

    # --- Mt. Hood ---------------------------------------------------------------------------------
    pk = (X(.31), hv - min(H * .33, S * .38))
    mh = hv - pk[1]
    hw = mh * 1.45
    left = [(pk[0] - hw * t, pk[1] + mh * (t ** 1.35) + (.6 * math.sin(t * 40) if t < .25 else 0)) for t in [i / 24 for i in range(25)]]
    right = [(pk[0] + hw * 1.1 * t, pk[1] + mh * (t ** 1.25) + (.8 * math.sin(t * 33 + 1) if t < .3 else 0)) for t in [i / 24 for i in range(25)]]
    # a craggy summit
    crag = [(pk[0] - 3, pk[1] + 2.2), (pk[0] - 1.2, pk[1] + .6), (pk[0], pk[1]), (pk[0] + 1.6, pk[1] + 1.4), (pk[0] + 3.4, pk[1] + 2.4)]
    mount = left[::-1][:-3] + crag + right[3:] + [(right[-1][0], hv + 2), (left[-1][0], hv + 2)]
    cv.obj([mount], 1.)
    snow = .62                       # fraction of the height under snow
    # east face in shade: hatch following the slope
    ridge = [(pk[0] + 1.2 + mh * .12 * t + .9 * math.sin(t * 9), pk[1] + mh * snow * t) for t in [i / 16 for i in range(17)]]
    shade = ridge + [p for p in right if p[1] <= pk[1] + mh * snow][::-1]
    cv.hair(C.hatch_poly(shade, 64, 1.5))
    cv.hair(ridge)
    cv.hair(C.hatch_poly(mount, -58, 3))
    # glacier gullies on the lit face
    for j in range(5 if big else 3):
        sx = pk[0] - 2 - j * mh * .09
        sy = pk[1] + 3 + j * mh * .05
        g = [(sx - mh * .04 * t - .6 * math.sin(t * 6 + j), sy + mh * (.22 + .05 * j) * t) for t in [i / 8 for i in range(9)]]
        cv.hair(g)
    for j in range(4 if big else 2):
        sx = pk[0] + 4 + j * mh * .1
        sy = pk[1] + 4 + j * mh * .06
        cv.line([(sx + mh * .05 * t, sy + mh * .25 * t + .5 * math.sin(t * 7)) for t in [i / 8 for i in range(9)]])
    # forested lower slopes
    sl = pk[1] + mh * .8
    fo = [(p[0], max(p[1], sl + 1.5 * math.sin(p[0] * .7))) for p in mount]
    tree_line = [(x, sl + 1.2 * math.sin(x * .13) + (0 if i % 2 else 2.4 + 1.2 * math.sin(i * 1.7))) for i, x in enumerate([left[-1][0] + i * 1.3 for i in range(int((right[-1][0] - left[-1][0]) / 1.3) + 1)])]
    forest = tree_line + [(right[-1][0], hv + 2), (left[-1][0], hv + 2)]
    cv.obj([forest], 0)
    cv.line(C.hatch_poly(forest, 0, 2))
    cv.hair(tree_line)
    # low foothills right
    hills = [(X(.5) + i * 3, hv - H * .03 - H * .012 * math.sin(i * .21) - H * .008 * math.sin(i * .07)) for i in range(int(W * .52 / 3) + 2)]
    hills_poly = hills + [(X0 + W + 2, hv + 2), (X(.5), hv + 2)]
    cv.obj([hills_poly], .5)
    cv.hair(C.hatch_poly(hills_poly, 0, 1.5))

    # --- the Washington shore: a dark ribbon of firs ----------------------------------------------
    st = []
    x = X0 - 2
    i = 0
    while x < X0 + W + 2:
        h_tree = (1.8 + 1.4 * abs(math.sin(i * 1.7)) + (1.2 if i % 7 == 3 else 0)) * max(1., S / 160)
        st.append((x, hv - 1.2))
        st.append((x + 1.1, hv - 1.2 - h_tree))
        x += 2.2
        i += 1
    st.append((x, hv - 1.2))
    shore = st + [(X0 + W + 2, hv + .5), (X0 - 2, hv + .5)]
    cv.obj([shore], 0)
    cv.line(C.hatch_poly(shore, 0, 1.5))
    cv.hair(st)

    # --- the river -----------------------------------------------------------------------------
    water = [(X0 - 2, hv + .5), (X0 + W + 2, hv + .5), (X0 + W + 2, bot), (X0 - 2, bot)]
    cv.obj([water], 0)
    # ship placement (needed for the reflection)
    sx0, sx1 = X(.42), X(.94)
    L = sx1 - sx0
    hh = max(3., L / 10.5)
    yw = hv + H * (.085 if not small else .1)
    y = hv + 1.2
    row = 0
    while y < bot:
        t = (y - hv) / (bot - hv)
        amp = .15 + .55 * t
        wl = 10 + 26 * t
        x = X0 - 2 - rng.uniform(0, 10)
        pts = []
        while x < X0 + W + 2:
            seg = rng.uniform(8, 40) * (1 - .4 * t)
            gap = rng.uniform(1.2, 2.5 + 5 * t)
            xe = min(x + seg, X0 + W + 2)
            n = max(2, int((xe - x) / 2))
            pl = [(x + (xe - x) * q / n, y + amp * math.sin((x + (xe - x) * q / n) / wl * TAU + row * .22)) for q in range(n + 1)]
            refl = (yw - 1 < y < yw + hh * 3.2 and sx0 - 2 < (x + xe) / 2 < sx1)
            refl_super = (yw - 1 < y < yw + hh * 5.5 and sx1 - L * .22 < (x + xe) / 2 < sx1 - L * .02)
            if refl or refl_super:
                cv.line(pl)
            else:
                cv.hair(pl)
            x = xe + gap
        y += 1.5 if t < .12 else (2. if t < .5 else 3.)
        row += 1

    _ship(cv, sx0, sx1, yw, hh, big, small)

    # --- the pilings, with the heron -----------------------------------------------------------
    if not small:
        px = X(.3)
        pw = max(2.6, S * .022)
        base = Y(.86)
        tops = [Y(.7), Y(.645), Y(.675), Y(.72)]
        hero_top = None
        for j, ty in enumerate(tops):
            x = px + (j - 1.5) * pw * 1.05
            body = [(x, ty), (x + pw, ty), (x + pw, base), (x, base)]
            cv.obj([body], 1.)
            cv.hair(C.hatch_poly([(x + pw * .55, ty), (x + pw, ty), (x + pw, base), (x + pw * .55, base)], 90, 1.5))
            cv.hair([(x + pw * .25, ty + 2), (x + pw * .28, base - 1)])
            cv.hair([[(x + .2, ty + 1.2 + q * 1.6), (x + pw - .2, ty + 1.6 + q * 1.6)] for q in range(2)])
            top = _ell(x + pw / 2, ty, pw / 2, pw * .22, 14)
            cv.obj([top], .5)
            if j == 1:
                hero_top = (x + pw / 2, ty - pw * .1)
        cv.obj([], 0)
        for q in range(3):
            rx, ry = pw * (2.6 + q * 1.1), pw * (.35 + q * .18)
            cv.hair([(px + rx * math.cos(t), base + ry * math.sin(t)) for t in [PI * (.05 + .9 * i / 16) for i in range(17)]])
        # the wire wrap binding the dolphin
        wy = Y(.73)
        cv.obj([], 0)
        cv.heavy([(px - 2 * pw * 1.05 + .5, wy), (px + 2 * pw * 1.05 - .5, wy + .4)])
        cv.line([(px - 2 * pw * 1.05 + .5, wy + 2), (px + 2 * pw * 1.05 - .5, wy + 2.4)])
        _heron(cv, hero_top[0], hero_top[1], min(H * .36, S * .38), big)

    # --- Sauvie Island bank, cattails --------------------------------------------------------------
    if not small:
        edge = _bez((X0 - 2, Y(.72)), (X(.08), Y(.74)), (X(.2), Y(.84)), (X(.3), Y(1.03)), 20)
        bank = edge + [(X0 - 2, bot)]
        cv.obj([bank], 1.)
        cv.hair(C.hatch_poly(bank, 28, 2))
        deep = [(X0 - 2, Y(.86)), (X(.14), Y(.9)), (X(.24), bot), (X0 - 2, bot)]
        cv.hair(C.hatch_poly(deep, -40, 2))
        # grass tufts along the crest
        for i, (gx, gy) in enumerate(edge[:-3]):
            for q in range(3):
                lean = rng.uniform(-.5, .25)
                ln = rng.uniform(3, 7) * max(1., S / 170)
                cv.hair([(gx + q * 1.2, gy + 1.5), (gx + q * 1.2 + lean * ln, gy + 1.5 - ln)])
        for j, u in enumerate((.04, .08, .13, .17)):
            gx = X(u)
            gy = Y(.735 + .02 * j + (.03 if u > .15 else 0))
            hgt = H * (.17 - .02 * j)
            lean = .08 + .04 * j
            stem = [(gx, gy), (gx + hgt * lean * .5, gy - hgt * .6), (gx + hgt * lean, gy - hgt)]
            cv.obj([], 0)
            cv.line(stem)
            hx, hy = gx + hgt * lean * .72, gy - hgt * .76
            head = _ell(hx, hy, max(1.2, S * .007), hgt * .13, 12, math.atan2(-1, lean) + PI / 2)
            cv.obj([head], 1.)
            cv.line(C.hatch_poly(head, 90, .9))
            # a blade leaf
            cv.obj([], 0)
            cv.hair(_bez((gx + 1, gy), (gx + 2 + hgt * .1, gy - hgt * .3), (gx + 3 + hgt * .25, gy - hgt * .55), (gx + 2 + hgt * .45, gy - hgt * .62), 8))

    # --- a leaping salmon (fishing the Columbia) ---------------------------------------------------
    if big:
        _salmon(cv, X(.74), Y(.86), S * .2, rng)

    clip = f"{uid}c"
    return (f'<clipPath id="{clip}"><path d="{_d(clip_pts, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{clip})">{cv.svg()}</g>')


def _ship(cv, x0, x1, yw, hh, big, small):
    """A bulk carrier, bow to the left (bound downriver), riding at yw with hull height hh."""
    L = x1 - x0

    def deck(x):
        t = max(0., 1 - (x - x0) / (.13 * L))
        return yw - hh - hh * .45 * t * t

    # bow wave (behind the hull)
    wave = [(x0 - L * .07, yw + 1.2), (x0 + L * .02, yw - hh * .35), (x0 + L * .12, yw + .2), (x0 + L * .2, yw + 1.6)]
    cv.obj([_bez(wave[0], wave[1], wave[2], wave[3], 10) + [(x0 + L * .05, yw + 2.5)]], .5)
    for q in range(3):
        cv.hair(_bez((x0 - L * (.05 - q * .02), yw + 1.4 + q * .8), (x0 + L * .02, yw - hh * .1),
                     (x0 + L * .1, yw + .6), (x0 + L * .18, yw + 1.6), 8))

    stem = _bez((x0 + L * .012, yw), (x0 - L * .002, yw - hh * .6), (x0 - L * .02, yw - hh * 1.2), (x0 - L * .03, deck(x0)), 8)
    xs = [x0 + L * i / 40 for i in range(41)]
    hull = stem + [(x, deck(x)) for x in xs[1:]] + [(x1 - L * .025, yw)]
    cv.obj([hull], 1.)
    # dark hull, a white boot-top at the waterline and a white sheer strake under the deck
    dark = [(x0 + L * .0 - .5, deck(x0) + 1.2)] + [(x, deck(x) + 1.2) for x in xs[1:]] + \
           [(x1 - L * .015, yw - 1.7), (x0 + L * .01, yw - 1.7)]
    cv.line(C.hatch_poly(dark, 0, .8))
    # anchor and hawse pipe
    cv.obj([_ell(x0 + L * .035, deck(x0) + hh * .55, max(.9, hh * .13), max(.9, hh * .13), 10)], .5)
    if not small:
        cv.obj([], 0)
        cv.line([(x0 + L * .035, deck(x0) + hh * .68), (x0 + L * .037, yw - 2.2)])
    # hold hatch covers and cranes
    nh = 6 if L > 70 else 4
    hx0, hx1 = x0 + L * .14, x1 - L * .24
    cw = (hx1 - hx0) / nh
    for i in range(nh):
        a = hx0 + cw * i + cw * .1
        bb = a + cw * .78
        yd = deck(a)
        hc = max(1.4, hh * .32)
        box = [(a, yd), (bb, yd), (bb, yd - hc), (a + 1, yd - hc - .4)]
        cv.obj([box], .5)
        cv.hair(C.hatch_poly(box, 90, 1.5))
    for i in range(1, nh, 2 if nh > 4 else 1):
        if i >= nh:
            break
        pxx = hx0 + cw * i
        yd = deck(pxx)
        ph = hh * 1.9
        post = [(pxx - .8, yd), (pxx + .8, yd), (pxx + .6, yd - ph), (pxx - .6, yd - ph)]
        cv.obj([post], .5)
        cv.line([(pxx - .2, yd), (pxx - .2, yd - ph)])
        jib = (pxx - cw * .95, yd - ph * 1.55)
        cv.obj([], 0)
        cv.line([(pxx, yd - ph * .55), jib])
        cv.hair([(pxx, yd - ph), jib])
        cv.hair([jib, (jib[0] + .3, yd - hh * .6)])
    # foremast
    cv.obj([], 0)
    fm = x0 + L * .06
    cv.line([(fm, deck(fm)), (fm + .3, deck(fm) - hh * 1.5)])
    cv.hair([(fm - 2, deck(fm) - hh * 1.1), (fm + 2.2, deck(fm) - hh * 1.1)])
    cv.hair([(fm + .3, deck(fm) - hh * 1.5), (x1 - L * .14, deck(x1) - hh * 4.4)])   # stay to the bridge mast

    # the accommodation block aft, four decks, bridge wings
    sa, sb = x1 - L * .2, x1 - L * .05
    yd = deck(x1)
    dh = hh * .62
    nd = 4 if not small else 3
    for k in range(nd):
        y0 = yd - dh * k
        aa = sa + k * L * .006 - (L * .025 if k == nd - 1 else 0)
        bbx = sb - k * L * .004
        box = [(aa, y0), (bbx, y0), (bbx, y0 - dh), (aa, y0 - dh)]
        cv.obj([box], .5 if k < nd - 1 else 1.)
        cv.hair(C.hatch_poly([(bbx - L * .02, y0), (bbx, y0), (bbx, y0 - dh), (bbx - L * .02, y0 - dh)], 90, 1.5))
        cv.hair([(aa, y0 - dh + .7), (bbx, y0 - dh + .7)])
        wy = y0 - dh * .55
        x = aa + 1.6
        step = 2.4 if k == nd - 1 else 3.
        while x < bbx - L * .022:
            cv.line([(x, wy), (x + (1.4 if k == nd - 1 else .9), wy)])
            x += step
    top = yd - dh * nd
    # lifeboat on the aft quarter
    if not small:
        lb = _ell(sb - L * .01, yd - dh * 1.5, L * .022, max(1., dh * .3), 16)
        cv.obj([lb], .5)
        cv.hair(C.hatch_poly([(p[0], p[1]) for p in lb if p[1] >= yd - dh * 1.5] or lb, 0, 1.))
    # mast and radar on the wheelhouse
    mxp = sa + L * .07
    cv.obj([], 0)
    cv.line([(mxp, top), (mxp, top - hh * 1.4)])
    cv.hair([(mxp - 2.4, top - hh * .9), (mxp + 2.4, top - hh * .9)])
    cv.hair([(mxp - 1.5, top - hh * 1.25), (mxp + 1.5, top - hh * 1.25)])
    # funnel, raked aft, with the house mark
    fa, fb = sb - L * .07, sb - L * .012
    fh = hh * 1.45
    rake = fh * .25
    fun = [(fa, top + .3), (fb, top + .3), (fb + rake, top - fh), (fa + rake, top - fh)]
    cv.obj([fun], 1.)
    band = [(fa + rake * .9, top - fh * .9), (fb + rake * .9, top - fh * .9), (fb + rake, top - fh), (fa + rake, top - fh)]
    cv.line(C.hatch_poly(band, 0, .8))
    low = [(fa, top + .3), (fb, top + .3), (fb + rake * .3, top - fh * .3), (fa + rake * .3, top - fh * .3)]
    cv.hair(C.hatch_poly(low, 0, 1.5))
    cv.hair(C.hatch_poly([(fb - (fb - fa) * .3, top), (fb, top), (fb + rake * .9, top - fh * .9),
                          (fb - (fb - fa) * .3 + rake * .9, top - fh * .9)], 90, 1.5))
    # the "P" monogram on the funnel (Easter egg)
    if not small:
        pc = ((fa + fb) / 2 + rake * .6, top - fh * .6)
        ph = fh * .34
        pw = ph * .5
        P = [(pc[0] - pw * .45, pc[1] + ph / 2), (pc[0] - pw * .45, pc[1] - ph / 2), (pc[0] + pw * .15, pc[1] - ph / 2)]
        P += [(pc[0] + pw * .15 + pw * .35 * math.sin(t), pc[1] - ph / 2 + ph * .26 * (1 - math.cos(t))) for t in [PI * i / 8 for i in range(1, 9)]]
        P += [(pc[0] - pw * .45, pc[1] + ph * .02)]
        cv.obj([], 0)
        cv.line(P)
    # stern flag staff and wake
    cv.obj([], 0)
    cv.hair([(x1 - L * .005, yd), (x1 + L * .004, yd - hh * 1.1)])
    for q in range(3):
        cv.hair(_bez((x1 - L * .03, yw + .8 + q), (x1 + L * .02, yw + 1.5 + q * 1.4), (x1 + L * .05, yw + q * 1.2), (x1 + L * .09, yw + 1 + q * 1.6), 8))


_HERON = [(-.38, -.862), (-.17, -.884), (-.14, -.9), (-.1, -.915), (-.06, -.906), (-.045, -.88), (-.055, -.83),
          (-.085, -.77), (-.095, -.71), (-.075, -.655), (-.03, -.615), (.03, -.59), (.08, -.588), (.14, -.565),
          (.2, -.53), (.26, -.48), (.31, -.43), (.27, -.418), (.19, -.405), (.11, -.39), (.05, -.385),
          (.0, -.39), (-.04, -.405), (-.07, -.39), (-.075, -.43), (-.1, -.42), (-.1, -.47), (-.12, -.5),
          (-.125, -.555), (-.15, -.62), (-.162, -.7), (-.152, -.765), (-.125, -.82), (-.125, -.85),
          (-.15, -.858), (-.17, -.866)]
_WING = [(-.02, -.585), (.08, -.58), (.15, -.555), (.22, -.505), (.3, -.432), (.2, -.415), (.1, -.41), (.02, -.43), (-.03, -.5)]


def _heron(cv, fx, fy, hgt, big):
    """A great blue heron standing on (fx, fy), facing left, hgt tall."""
    s = hgt
    dy = .13
    P = lambda x, y: (fx + x * s, fy + (y + dy) * s)
    F = lambda x, y: (fx + x * s, fy + y * s)
    cv.obj([], 0)
    cv.line([P(.035, -.4), F(.04, -.16), F(-.005, 0)])
    cv.line([P(.075, -.395), F(.085, -.15), F(.06, 0)])
    cv.hair([F(-.005, 0), F(-.07, .005)])
    cv.hair([F(.06, 0), F(.0, .008)])
    cv.hair([F(.06, 0), F(.1, .006)])
    body = [P(x, y) for x, y in _HERON]
    cv.obj([body], 1.)
    wing = [P(x, y) for x, y in _WING]
    cv.hair(C.hatch_poly(wing, 22, 1.5))
    cv.hair(C.hatch_poly(wing, -50, 3 if big else 2))
    for q in range(5):
        t = q / 4
        cv.hair(_bez(P(.0 + .04 * t, -.57 + .02 * t), P(.1 + .03 * t, -.55 + .04 * t), P(.2, -.48 + .03 * t), P(.3 - .03 * t, -.43 + .01 * t), 8))
    # the shaggy breast plumes and the dark thigh
    for q in range(4):
        x = -.115 + q * .018
        cv.hair([P(x, -.56 + q * .02), P(x - .012, -.47), P(x + .005, -.41 + q * .005)])
    cv.hair(C.hatch_poly([P(.0, -.43), P(.08, -.43), P(.1, -.395), P(.0, -.39)], 70, 1.5))
    # neck: grey back of the neck, black-streaked foreneck
    cv.hair([P(-.07 + .01 * math.sin(t * 3), -.84 + .23 * t) for t in [i / 10 for i in range(11)]])
    fore = [P(-.135 - .02 * math.sin(t * 2.6), -.82 + .26 * t) for t in [i / 12 for i in range(13)]]
    cv.line([fore[i] for i in range(1, 12, 2)])
    for i in range(1, 12, 2):
        cv.line([fore[i], fore[i + 1]])
    # head: white face, black crown stripe running back into the plume, eye, bill
    cv.line([P(-.13, -.9), P(-.05, -.902)])
    cv.heavy([P(-.06, -.9), P(.08, -.885)])
    cv.hair([P(-.06, -.895), P(.06, -.872)])
    cv.hair([P(-.17, -.874), P(-.36, -.862)])
    cv.obj([_ell(*P(-.118, -.889), max(.6, s * .008), max(.6, s * .008), 6)], 1.)


def _salmon(cv, cx, cy, size, rng):
    """A salmon leaping clear, arched, nose up and to the left, with its splash."""
    arc = [(cx + size * .5 * math.cos(t), cy - size * .35 * math.sin(t) - size * .1) for t in [PI * (.15 + .7 * i / 20) for i in range(21)]]
    prof = lambda t: size * .12 * math.sin(PI * min(1, t * 1.02) ** 1.5) ** .8 + .3
    body, upper, lower = _ribbon(arc, prof)
    # tail fork at the start (lower right)
    t0 = arc[0]
    tail = [(t0[0] + size * .02, t0[1] + size * .02), (t0[0] + size * .14, t0[1] + size * .07),
            (t0[0] + size * .06, t0[1] - size * .01), (t0[0] + size * .12, t0[1] - size * .1)]
    cv.obj([tail], 1.)
    cv.hair(C.hatch_poly(tail, 70, 1.5))
    cv.obj([body], 1.)
    # dark back (outer side of the arch), silver belly, lateral line, spots
    back = upper[1:-1] + [p for p in arc[1:-1]][::-1]
    cv.hair(C.hatch_poly(back, 20, 1.5))
    cv.hair(arc[2:-3])
    for i in range(3, 17, 2):
        p = upper[i]
        q = arc[i]
        cv.line([((p[0] * 2 + q[0]) / 3, (p[1] * 2 + q[1]) / 3), ((p[0] * 2 + q[0]) / 3 + .6, (p[1] * 2 + q[1]) / 3 + .2)])
    # gill and eye
    g = arc[16]
    cv.hair([upper[16], lower[16]])
    e = arc[18]
    cv.obj([_ell(e[0], e[1] - .5, .7, .7, 6)], 1.)
    # dorsal fin
    d0 = upper[9]
    cv.obj([[d0, upper[12], (d0[0] + size * .02, d0[1] - size * .08)]], .5)
    # splash under it
    cv.obj([], 0)
    for q in range(3):
        r = size * (.18 + q * .12)
        cv.hair([(cx + size * .25 + r * math.cos(t), cy + size * .12 + r * .22 * math.sin(t)) for t in [PI * (1.05 + .9 * i / 14) for i in range(15)]])
    for q in range(7):
        a = PI * (1.1 + .8 * q / 6)
        r = size * rng.uniform(.25, .4)
        x, y = cx + size * .25 + r * math.cos(a), cy + size * .05 + r * .6 * math.sin(a)
        cv.obj([_ell(x, y, .8, .8, 6)], .5)


# ------------------------------------------------------------------------------------------------
# lettering: a small stroked roman for the banner
# ------------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_GLYPHS = {
    "T": (.72, [[(0, 0), (.72, 0)], [(.36, 0), (.36, 1)]]),
    "H": (.72, [[(.06, 0), (.06, 1)], [(.66, 0), (.66, 1)], [(.06, .5), (.66, .5)]]),
    "E": (.6, [[(.58, 0), (.06, 0), (.06, 1), (.58, 1)], [(.06, .5), (.46, .5)]]),
    "C": (.74, [_arc(.4, .5, .36, .5, -50, -310, 16)]),
    "O": (.82, [_arc(.41, .5, .37, .5, 0, 360, 22)]),
    "L": (.58, [[(.06, 0), (.06, 1), (.56, 1)]]),
    "U": (.72, [[(.06, 0), (.06, .66)] + _arc(.36, .66, .3, .34, 180, 0, 10)[1:] + [(.66, 0)]]),
    "M": (.88, [[(.04, 1), (.1, 0), (.44, .78), (.78, 0), (.84, 1)]]),
    "B": (.66, [[(.06, 0), (.06, 1)], [(.06, 0), (.38, 0)] + _arc(.38, .24, .22, .24, -90, 90, 8) + [(.06, .48)],
                [(.06, .48), (.42, .48)] + _arc(.42, .74, .24, .26, -90, 90, 8) + [(.06, 1)]]),
    "I": (.18, [[(.09, 0), (.09, 1)]]),
    "A": (.78, [[(.03, 1), (.39, 0), (.75, 1)], [(.17, .64), (.61, .64)]]),
    " ": (.5, []),
}


def _letter(text, centre, lh, track=.32):
    """Path data: text laid along the polyline centre, letter height lh, centred on it."""
    cum = [0.]
    for i in range(1, len(centre)):
        cum.append(cum[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    total = cum[-1]

    def frame(s):
        s = min(max(s, 0), total)
        i = 1
        while i < len(cum) - 1 and cum[i] < s:
            i += 1
        p, q = centre[i - 1], centre[i]
        seg = (cum[i] - cum[i - 1]) or 1
        r = (s - cum[i - 1]) / seg
        tx, ty = (q[0] - p[0]) / seg, (q[1] - p[1]) / seg
        return (p[0] + (q[0] - p[0]) * r, p[1] + (q[1] - p[1]) * r), (tx, ty), (-ty, tx)

    width = sum(_GLYPHS[c][0] * lh for c in text) + track * lh * (len(text) - 1)
    s = (total - width) / 2
    d = []
    for c in text:
        gw, strokes = _GLYPHS[c]
        for st in strokes:
            pts = []
            for gx, gy in st:
                (px, py), (tx, ty), (nx, ny) = frame(s + gx * lh)
                pts.append((px - nx * (gy - .5) * lh * -1, py - ny * (gy - .5) * lh * -1))
            d.append(_d(pts, tol=0))
        s += gw * lh + track * lh
    return "".join(d), (total - width) / 2, width


# ------------------------------------------------------------------------------------------------
# the Vitruvian wave (the river running along the pedestal's tablet)
# ------------------------------------------------------------------------------------------------

def _running_wave(x, y, w, h):
    R = h * .3
    cyy = y + h * .44
    Lu = R * 2.7
    n = max(2, int((w - R * 2) / Lu))
    x0 = x + (w - n * Lu) / 2 + R * .5
    lines = []
    fills = []
    prev_bottom = (x + 1, cyy + R)
    for i in range(n):
        c = (x0 + i * Lu + R, cyy)
        conn = _bez(prev_bottom, (prev_bottom[0] + (c[0] - R - prev_bottom[0]) * .7, prev_bottom[1]),
                    (c[0] - R, cyy + R * .5), (c[0] - R, cyy), 8)
        sp = []
        for j in range(41):
            t = j / 40
            th = PI + t * 3.4 * PI
            r = R * (1 - .82 * t)
            sp.append((c[0] + r * math.cos(th), c[1] + r * math.sin(th)))
        lines.append(conn + sp)
        # the crest under the curl, shaded
        fills.append(conn + [p for p in sp[:22]] + [(sp[21][0], y + h - 1), (prev_bottom[0], y + h - 1)])
        prev_bottom = (c[0], cyy + R)
    lines.append(_bez(prev_bottom, (prev_bottom[0] + R, prev_bottom[1]), (x + w - 2, prev_bottom[1]), (x + w - 1, prev_bottom[1]), 4))
    return lines, fills


# ------------------------------------------------------------------------------------------------
# layouts (copied from the house frame and adapted: no white anywhere, the field filled)
# ------------------------------------------------------------------------------------------------

def _band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.65, 124)
    o.append(C._clip(C._uid("rb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    o.append(river_scene(cx, cy, rx - 4, ry - 4, _ell(cx, cy, rx - 4, ry - 4, 64), ctx, seed, "rvb%d" % h))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _medium(w, h, seed, ctx):
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
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("rm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    fa, fb = a - 5.5, b - 5.5
    o.append(river_scene(cx, cy, fa, fb, C._superellipse(cx, cy, fa, fb), ctx, seed, "rvm%d" % h))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # the strip above the panel: a light ruled ground under a bead moulding, so the crest rises from it
    o.append(C.dark_ground((0, 0, w, py0), "L"))
    o.append(C.bead_moulding(0, 2.5, w, 1.5))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .24)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("rt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    fa, fb = a - 5.5, b - 5.5
    o.append(river_scene(cx, cy, fa, fb, C._superellipse(cx, cy, fa, fb), ctx, seed, "rvt%d" % h))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(17, max(11, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    d, _, _ = _letter("THE COLUMBIA", centre, bh * .52, .3)
    o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="1" stroke-linecap="square" stroke-linejoin="miter"/>')
    # pedestal on a dark ground, its tablet carrying the running wave
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py0 + ph, w, h - py0 - ph), "G"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    ix, iy, iw, ih = tx + 2.5, ty + 2.5, tw - 4, th - 4
    o.append(C.dark_ground((ix, iy, iw, ih), "L"))
    lines, fills = _running_wave(ix, iy, iw, ih)
    o.append(f'<path d="{"".join(_d(f_, True, 0) for f_ in fills)}" fill="{C.pat("M")}" stroke="none"/>')
    o.append(f'<path d="{"".join(_d(l, tol=.1) for l in lines)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("rf", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _band(w, h, seed, ctx)
    elif h <= 260:
        body = _medium(w, h, seed, ctx)
    else:
        body = _tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
