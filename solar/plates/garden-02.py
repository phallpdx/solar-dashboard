"""garden-02: "Burn day check" (brush pile, Sauvie Island burn line, wind).

The vignette: a brush pile burning in a ploughed field on the island, its flames cut as Thai kranok
flames whose tips roll into acanthus curls, the smoke leaning off with the day's wind and winding
into a volute, a windsock on the left reading the gusts, Mt. Hood on the far horizon. Easter eggs:
two of the sticks in the pile are drumsticks crossed (bead tips), and a dog's paw print is pressed
into the soil. If the page says it is NOT ok to burn, the pile is unlit and the smoke is gone.
"""
import sys
import math
import random
import re
import engraving_codex as C

PI = math.pi
_n, _d = C._n, C._d


# ------------------------------------------------------------------------------------------------
# reading the page
# ------------------------------------------------------------------------------------------------

def _facts(ctx):
    s = ((ctx or {}).get("sample") or "").lower()
    m = re.search(r"gusts?\s*(\d+)\s*mph", s) or re.search(r"(\d+)\s*mph", s)
    wind = float(m.group(1)) if m else 10.
    ok = not re.search(r"no[\s-]burn|not ok|do not burn|burn ban|closed", s)
    if "ok to burn" in s:
        ok = True
    return wind, ok


# ------------------------------------------------------------------------------------------------
# engraved parts of the vignette (all into one Canvas cv)
# ------------------------------------------------------------------------------------------------

def _rib_from(pts, wfun):
    W = [wfun(i / (len(pts) - 1)) for i in range(len(pts))]
    return C._Rib(pts, W, W)


def _tongue(cv, x, y, ang, length, width, wave, flick, dark=1.):
    """One licking tongue of flame: sinuous, widest low down, drawn to a needle point that flicks
    over (kranok). Shaded along its form, dark on the inside of its last turn."""
    n = max(24, int(length / 1.1))
    sg = 1 if flick >= 0 else -1

    def k(u):
        return (wave * math.cos(u * 2.4 * PI) * 2.2 + flick * C._smooth(.7, 1., u) ** 2 * 3.2) / length

    pts = C._euler(x, y, ang, length, k, n)
    W = [width * (2.0 * (i / n) ** .35 * (1 - i / n) ** 1.25) + .35 for i in range(n + 1)]
    R = C._Rib(pts, W, W)
    cv.obj([R.outline()], 1.)
    cv.hair(C._fill_lines(R, .08 * sg, .96 * sg, 1.5, .02, .99, 4))
    cv.hair(C._fill_lines(R, -.3 * sg, -.9 * sg, 2., .1, .9, 2))
    C._shadow(cv, R, sg, min(3.2, width * .45) * dark, .1, .92)
    return R


def _flame(cv, x, y, length, width, lean, curl, seed):
    """A kranok flame: a tall tongue with smaller licks springing from its flanks."""
    rng = random.Random(seed)
    sg = 1 if curl >= 0 else -1
    a = -PI / 2 + lean * .6
    # flank licks first (under the main tongue)
    subs = []
    for j, u in enumerate((.18, .38)):
        side = -sg if j == 0 else sg
        px = x + math.cos(a) * length * u + side * width * .5
        py = y + math.sin(a) * length * u
        subs.append((px, py, a + side * rng.uniform(.35, .55), length * (.55 - .15 * j) * rng.uniform(.9, 1.1),
                     width * .55, -side * .25, side * rng.uniform(1.2, 1.8)))
    for sb in subs:
        _tongue(cv, *sb)
    _tongue(cv, x, y, a, length, width, -sg * .55 * rng.uniform(.8, 1.2), sg * curl, 1.)


def _puff(cv, cx, cy, r, rng):
    """One billow of smoke: a lobed round, ruled light above and cut into a dark crescent below."""
    nb = 5
    ph = rng.random() * PI
    poly = []
    for i in range(48):
        t = 2 * PI * i / 48
        bump = 1 + .1 * abs(math.sin(nb * t / 2 + ph))
        poly.append((cx + r * bump * math.cos(t), cy + r * .82 * bump * math.sin(t)))
    cv.obj([poly], 1.)
    # contour arcs following the round, thickening into the shadowed underside
    q = r - 1.6
    k = 0
    while q > r * .3:
        span = .55 + .45 * (k / 6)
        a0, a1 = PI * (.05 - span * .2), PI * (.95 + span * .2)
        cv.hair(C._ell_pts(cx + (r - q) * .25, cy + (r - q) * .35, q, q * .8, max(10, int(q)), a0 - .3, a1))
        q -= 1.5 if k < 3 else 2.
        k += 1
    cv.hair(C.hatch_poly(poly, 35, 3))
    cv.line(C._ell_pts(cx + r * .05, cy + r * .1, r * .85, r * .62, 24, .2, 2.4))


def _smoke(cv, x, y, height, size, lean, seed):
    """A column of billows rising from (x, y), leaning downwind and swelling; the last one rolls
    into an acanthus curl."""
    rng = random.Random(seed)
    pts = []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        pts.append((x + (lean + .4) * height * 1.3 * t ** 1.2 + rng.uniform(-1, 1) * size * .3,
                    y - height * t * (1 - .25 * t), size * (.6 + 1.1 * t)))
    for px, py, r in pts[::-1]:
        _puff(cv, px, py, r, rng)
    # the top billow curls over like a scroll: a spiral cut into it with a drilled eye
    ex, ey, er = pts[-1]
    sp = C.volute_spine(ex, ey, er * .75, 200, 1.3, False, end=.18)
    cv.line(sp)
    cv.heavy(sp[len(sp) * 2 // 3:])
    cv.line([C._ell_pts(sp[-1][0], sp[-1][1], 1.2, 1.2, 8), C._ell_pts(sp[-1][0], sp[-1][1], .5, .5, 6)])


def _stick(cv, x0, y0, x1, y1, w0, w1, knot=True):
    """A cut branch: a tapered round stick, bark lines along it, a dark underside, a cut end ring."""
    L = math.hypot(x1 - x0, y1 - y0)
    pts = [(x0 + (x1 - x0) * i / 12, y0 + (y1 - y0) * i / 12) for i in range(13)]
    R = _rib_from(pts, lambda u: w0 + (w1 - w0) * u)
    cv.obj([R.outline()], 1.)
    cv.hair(C._fill_lines(R, -.15, -.95, 1.5, 0, 1, 3))
    cv.hair(R.contour(.45, .05, .95))
    if w0 > 1.6:
        C._shadow(cv, R, -1, w0 * .6, 0, 1)
    ang = math.atan2(y1 - y0, x1 - x0)
    # cut end: an ellipse with growth rings
    e = C._ell_pts(x0, y0, w0 * .45, w0, 14)
    rot = [(x0 + (px - x0) * math.cos(ang) - (py - y0) * math.sin(ang),
            y0 + (px - x0) * math.sin(ang) + (py - y0) * math.cos(ang)) for px, py in e[:-1]]
    cv.obj([rot], 1.)
    if w0 > 2:
        cv.hair([(px * .5 + x0 * .5, py * .5 + y0 * .5) for px, py in rot + rot[:1]])
    if knot and L > 30:
        u = .55
        kx, ky = R.at(u, .9)
        tw = ang - .9
        cv.line([(kx, ky), (kx + math.cos(tw) * w0 * 2.2, ky + math.sin(tw) * w0 * 2.2)])
    return R


def _drumstick(cv, x0, y0, x1, y1, w):
    """A drumstick: a turned shaft tapering to a bead tip at (x1, y1)."""
    pts = [(x0 + (x1 - x0) * i / 20, y0 + (y1 - y0) * i / 20) for i in range(21)]
    R = _rib_from(pts, lambda u: w * (1 - .62 * C._smooth(.55, .96, u)))
    cv.obj([R.outline()], 1.)
    cv.hair(C._fill_lines(R, -.2, -.95, 1.5, 0, 1, 3))
    cv.hair(R.contour(.5, .02, .98))
    C._shadow(cv, R, -1, w * .5, 0, .95)
    L = R.L
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 + ux * w * .8, y1 + uy * w * .8
    bead = C._ell_pts(bx, by, w * 1.05, w * 1.05, 18)[:-1]
    cv.obj([bead], 1.)
    cv.line(C._ell_pts(bx + uy * w * .45 + ux * .4, by - ux * w * .45 + uy * .4, w * .45, w * .45, 10, .3, 2.6))
    # butt end ring
    cv.line([R.at(.02, 1), R.at(.02, -1)])


def _windsock(cv, px, top, foot, wind, sg=1):
    """A pole with a striped windsock streaming downwind; it droops in light air."""
    pole = [(px - 1.2, top - 2), (px + 1.2, top - 2), (px + 1.6, foot), (px - 1.6, foot)]
    cv.obj([pole], 1.)
    cv.hair([(px + .6, top), (px + .8, foot)])
    cv.obj([C._ell_pts(px, top - 3, 2.2, 2.2, 10)[:-1]], 1.)
    lift = min(1., wind / 22.)
    L = (foot - top) * .55
    droop = (1 - lift) * 1.3 + .12
    pts = C._euler(px + 1.2, top + 2, sg * 0 + droop * .25, L, lambda u: droop * 1.1 / L, 20)
    if sg < 0:
        pts = [(2 * px - x, y) for x, y in pts]
    R = _rib_from(pts, lambda u: 5.2 * (1 - .5 * u) + .4)
    cv.obj([R.outline()], 1.)
    # five stripes, alternately dark-hatched and lightly ruled
    for j in range(5):
        u0, u1 = j / 5, (j + 1) / 5
        band = [R.at(u0, 1), R.at(u1, 1), R.at(u1, -1), R.at(u0, -1)]
        if j % 2 == 0:
            cv.hair(C.hatch_poly(band, 90 + math.degrees(math.atan2(pts[-1][1] - pts[0][1], pts[-1][0] - pts[0][0])), 1.5, .3))
        cv.line([R.at(u1, 1), R.at(u1, -1)])
    C._shadow(cv, R, -1, 1.8, 0, 1)
    # the mouth ring
    cv.line([R.at(0, 1), R.at(0, -1)])


def _paw(cx, cy, s):
    """A dog's paw print: four toe pads and a heel pad (black)."""
    d = _d(C._ell_pts(cx, cy + s * .35, s * .55, s * .42, 14), True, 0)
    for a, r in ((-2.25, .95), (-1.75, 1.05), (-1.39, 1.05), (-.89, .95)):
        d += _d(C._ell_pts(cx + math.cos(a) * s * r, cy + math.sin(a) * s * r * .85, s * .2, s * .27, 10), True, 0)
    return d


def _mt_hood(cv, cx, base, h, w):
    """Mt. Hood: a sharp, slightly lopsided cone with a snow cap, ridges and a hatched lower flank."""
    peak = (cx + w * .04, base - h)
    left = [(cx - w * .5, base), (cx - w * .3, base - h * .32), (cx - w * .14, base - h * .62),
            (cx - w * .05, base - h * .86), peak, (cx + w * .1, base - h * .82), (cx + w * .2, base - h * .58),
            (cx + w * .34, base - h * .3), (cx + w * .5, base)]
    cv.obj([left], .5)
    snow = base - h * .55
    flank = [p for p in left if p[1] > snow - 1] + [(cx - w * .5, base)]
    lo = [(cx - w * .5, base), (cx - w * .19, snow + 3), (cx - w * .1, snow + 1), (cx, snow + 5),
          (cx + w * .1, snow), (cx + w * .2, snow + 4), (cx + w * .5, base)]
    cv.hair(C.hatch_poly(lo, 0, 1.5))
    # shadowed right face of the snow
    rf = [peak, (cx + w * .1, base - h * .82), (cx + w * .2, base - h * .58), (cx + w * .1, snow), (cx + w * .02, snow + 2)]
    cv.hair(C.hatch_poly(rf, 70, 1.5))
    for dx in (-.08, .0, .07):
        cv.hair([peak, (cx + w * dx, snow + 3)])


# ------------------------------------------------------------------------------------------------
# the vignette: fills the field (bx, by, bw, bh) completely, no bare white
# ------------------------------------------------------------------------------------------------

def scene(bx, by, bw, bh, ctx, seed=0, mini=False):
    wind, ok = _facts(ctx)
    lean = min(1., wind / 25.) * .55
    rng = random.Random(seed)
    cv = C.Canvas()
    x1, y1 = bx + bw, by + bh
    tall = bh > bw * .85
    hz = by + bh * (.6 if mini else (.56 if tall else .5))        # horizon
    # sky: graded ruled lines, denser toward the top
    sky = []
    y = by
    while y < hz + 1:
        sky.append([(bx - 2, y), (x1 + 2, y)])
        f = (y - by) / max(1., hz - by)
        y += 1.5 if f < .35 else (2. if f < .75 else 3.)
    cv.obj([], 0)
    cv.hair(sky)
    if not mini:
        # Mt. Hood far off on the horizon, to the left of the fire
        _mt_hood(cv, bx + bw * .8, hz + 1, bh * .2, bw * .42)
    # the far tree line along the slough (dark, vertical rules over a ragged crown)
    crown = [(bx - 2, hz + 3)]
    k = 0
    while crown[-1][0] < x1 + 2:
        k += 1
        xx = bx - 2 + k * 3
        crown.append((xx, hz - (2.5 + 2.2 * abs(math.sin(k * 1.7 + seed)) + 1.4 * math.sin(k * .45)) * (bh / 120)))
    trees = crown + [(x1 + 2, hz + 5), (bx - 2, hz + 5)]
    cv.obj([trees], .5)
    cv.hair(C.hatch_poly(trees, 90, 1.5))
    # the field: furrows running to a vanishing point, cross-ruled darker toward the viewer
    field = [(bx - 2, hz + 4), (x1 + 2, hz + 4), (x1 + 2, y1 + 2), (bx - 2, y1 + 2)]
    cv.obj([field], .5)
    # ploughed furrows: wavy rows opening toward the viewer, each a ridge line over finer ruling
    yy = hz + 6
    gap = 2.5
    j = 0
    while yy < y1 + 4:
        f = (yy - hz) / max(1., y1 - hz)
        row = [(bx - 2 + t * (bw + 4) / 40, yy + math.sin(t * .55 + j * 1.3) * (.4 + 1.6 * f)) for t in range(41)]
        cv.line(row) if j % 2 == 0 else cv.hair(row)
        cv.hair([(px, py + gap * .5) for px, py in row])
        yy += gap
        gap = min(5., gap * 1.12)
        j += 1
    cv.hair(C.hatch_poly(field, 90, 3))
    # the pile
    pcx = bx + bw * (.47 if not mini else .5)
    pbase = y1 - bh * (.1 if mini else (.2 if tall else .12))
    pw = bw * (.62 if mini else (.7 if tall else .6))
    ph = bh * .26 if mini else (bw * .25 if tall else min(bh * .2, bw * .2))
    smoke_h = (hz - by) + bh * .12
    if ok and not mini:
        s0 = pbase - ph * 2.0
        _smoke(cv, pcx + pw * .02, s0, (s0 - by) * .75, min(bh, bw) * .085, lean, seed)
    if not mini:
        _windsock(cv, bx + bw * .1, hz - bh * .2, pbase + bh * .02, wind)
    mound = C._ell_pts(pcx, pbase, pw / 2, ph, 40, PI, 2 * PI)[:-1] + [(pcx + pw / 2, pbase + 2), (pcx - pw / 2, pbase + 2)]
    cv.obj([mound], 1.)
    cv.line(C.hatch_poly(mound, 0, 1.5))
    cv.hair(C.hatch_poly(mound, 60, 3))
    # back sticks, then flames, then front sticks
    sr = random.Random(seed * 13 + 5)
    sticks = []
    ns = 16 if not mini else 9
    for i in range(ns):
        t = (i + sr.uniform(.2, .8)) / ns
        side = -1 if t < .5 else 1
        x0 = pcx - pw * .5 + pw * t                      # butt end out on the flank
        yb = pbase - sr.uniform(0, ph * .35)
        tip_x = pcx + (x0 - pcx) * sr.uniform(-.1, .35)   # leaning in toward the crown
        tip_y = pbase - ph * sr.uniform(.75, 1.25)
        sticks.append((x0, yb, tip_x, tip_y,
                       sr.uniform(1.4, 2.6) * (min(bh, bw) / 140 if not mini else .7) + .6, .9))
    for s in sticks[::2]:
        _stick(cv, *s)
    if ok:
        fr = random.Random(seed * 7 + 1)
        nf = 7 if not mini else 3
        # the dark outer flame: a ragged silhouette ruled near-black, so the white tongues blaze
        top = []
        m = 90
        for j in range(m + 1):
            t = j / m
            xx = pcx - pw * .46 + pw * .92 * t
            env = math.sin(PI * t) ** .7
            spike = .5 + .5 * abs(math.sin(t * PI * 5.5 + seed)) ** 3
            hh = ph * (.6 + (2.45 if not mini else 2.1) * env * spike)
            top.append((xx + lean * hh * .35, pbase - hh))
        glow = top + [(pcx + pw * .46, pbase - ph * .3), (pcx - pw * .46, pbase - ph * .3)]
        cv.obj([glow], 1.)
        cv.line(C.hatch_poly(glow, 0, 1.5))
        cv.hair(C.hatch_poly(glow, 75 + lean * 20, 2))
        order = sorted(range(nf), key=lambda i: -abs(i - (nf - 1) / 2))
        for i in order:
            off = (i - (nf - 1) / 2) / max(1, (nf - 1) / 2)
            Lf = ph * (2.2 if not mini else 2.0) * (1 - .35 * abs(off)) * fr.uniform(.88, 1.05)
            _flame(cv, pcx + off * pw * .3, pbase - ph * (.75 - .3 * abs(off)), Lf, Lf * .14,
                   lean + off * .3, (1 if off >= 0 else -1) * fr.uniform(1.8, 2.6), seed + i)
    for s in sticks[1::2]:
        _stick(cv, *s)
    # Easter egg: a pair of drumsticks crossed in front of the pile
    dw = max(1.7, min(bh, bw) * .014) if not mini else 1.3
    if mini:
        dl, dcx, dcy, sp = pw * .4, pcx, pbase - ph * .1, .22
    else:
        dl, dcx, dcy, sp = min(bw, bh) * .3, bx + bw * .27, y1 - bh * .1, .5
    for sgn in (-1, 1):
        ca, sa = math.cos(sp) * dl / 2, math.sin(sp) * dl / 2
        _drumstick(cv, dcx - sgn * ca, dcy + sa, dcx + sgn * ca, dcy - sa, dw)
    o = [cv.svg()]
    if not mini:
        # a dog's paw print, then another, pressed into the soil in the foreground
        s = max(2.2, bh * .022)
        px, py = bx + bw * .72, y1 - bh * .1
        paws = _paw(px, py, s) + _paw(px + s * 3.2, py - s * 2.6, s * .92)
        o.append(f'<path d="{paws}" fill="#000" stroke="#fff" stroke-width=".5"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# layouts (house frame, with the vignette clipped to the whole field)
# ------------------------------------------------------------------------------------------------

def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _cartouche_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("gb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(_field_clip(C._uid("gbf", w, h, seed), fd, scene(cx - rx, cy - ry, 2 * rx, 2 * ry, ctx, seed, True)))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2.5, ry - 2.5, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
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
    o.append(C._clip(C._uid("gm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _cartouche_field(cx, cy, cw, ch)
    o.append(_field_clip(C._uid("gmf", w, h, seed), inner, scene(fx, fy, fw, fh, ctx, seed)))
    o.append(_ring(cx, cy, cw, ch))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _ring(cx, cy, w, h):
    """Re-cut the cartouche's inner edge and its bead row over the vignette."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    bp = C._superellipse(cx, cy, a - 3.2, b - 3.2)
    inner = C._superellipse(cx, cy, a, b)
    return (f'<path d="{_d(inner + [inner[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1"/>')


def _letters(word, x, y, h, track=.28):
    """Roman capitals as single-stroke polylines (B U R N D A Y and space), cap height h."""
    w = h * .62
    G = {
        "B": [[(0, 0), (0, 1)], [(0, 0), (.6, 0), (.82, .1), (.82, .38), (.6, .48), (0, .48)],
              [(.6, .48), (.9, .58), (.9, .9), (.66, 1), (0, 1)]],
        "U": [[(0, 0), (0, .72), (.2, .97), (.45, 1.), (.7, .97), (.9, .72), (.9, 0)]],
        "R": [[(0, 1), (0, 0), (.62, 0), (.85, .12), (.85, .38), (.62, .5), (0, .5)], [(.45, .5), (.92, 1)]],
        "N": [[(0, 1), (0, 0), (.9, 1), (.9, 0)]],
        "D": [[(0, 0), (0, 1), (.5, 1), (.85, .8), (.95, .5), (.85, .2), (.5, 0), (0, 0)]],
        "A": [[(0, 1), (.47, 0), (.94, 1)], [(.18, .62), (.76, .62)]],
        "Y": [[(0, 0), (.47, .5), (.94, 0)], [(.47, .5), (.47, 1)]],
        " ": [],
    }
    out = []
    cx = x
    for ch in word:
        for pl in G[ch]:
            out.append([(cx + px * w, y + py * h) for px, py in pl])
        cx += w * (.95 if ch != " " else .6) + w * track
    return out, cx - x - w * track


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
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
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("gt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _cartouche_field(cx, cy, cw, ch)
    o.append(_field_clip(C._uid("gtf", w, h, seed), inner, scene(fx, fy, fw, fh, ctx, seed)))
    o.append(_ring(cx, cy, cw, ch))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 56), True, rng.randrange(1 << 20)))
    bh_ = min(16, ph * .05)
    bsvg, cen = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # the banner face: fine ruling along it, so no bare white
    lines = "".join(_d([(px, py + off) for px, py in cen[1:-1]], tol=.1) for off in (-3., -1.5, 0., 1.5, 3.))
    o.append(f'<path d="{lines}" fill="none" stroke="#000" stroke-width=".5"/>')
    py = h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: stippled, lettered BURN DAY in cut capitals
    o.append(f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{C.pat("L")}" stroke="none"/>')
    lh = min(th - 4, 18)
    pls, lw = _letters("BURN DAY", 0, 0, lh)
    ox, oy = tx + (tw - lw) / 2, ty + (th - lh) / 2
    d = "".join(_d([(ox + px, oy + py) for px, py in pl], tol=0) for pl in pls)
    o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="1.5"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) % 997
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
