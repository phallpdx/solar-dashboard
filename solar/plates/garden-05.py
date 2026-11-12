"""garden-05 "What is blooming": Common selfheal and Common sneezeweed, seen flowering nearby.

The plate is a bed of the two natives engraved inside the house acanthus frame: sneezeweed
(Helenium autumnale) with its globe disc and drooping three-toothed rays, selfheal (Prunella
vulgaris) with its square stem and its stacked, hairy bract-tiers sprouting hooded flowers, on the
garden soil under a ruled sky, the Sauvie Island cottonwoods and Mt. Hood behind. The main volutes
of the frame do not end in a drilled eye: they curl into sneezeweed heads.
Easter egg: a dog's paw print pressed into the garden soil (and, on tall plates, Mt. Hood).
"""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import (Canvas, _Rib, _ell_pts, _euler, _n, _d, _dp, hatch_poly, pat, _fill_lines,
                             _shadow, _smooth, _uid, _volute, volute_spine, cartouche, egg_and_dart,
                             knurled_bar, bead_moulding, dark_ground, fill_scrolls, scroll_band, palmette,
                             ribbon_banner, pedestal, svg_doc, _CR)

PI = math.pi
TAU = 2 * PI


# ----------------------------------------------------------------------------------------------
# small geometry
# ----------------------------------------------------------------------------------------------

def _poly_rib(pts, wfun):
    n = len(pts) - 1
    W = [max(.3, wfun(i / n)) for i in range(n + 1)]
    return _Rib(pts, W, W)


def _clip_g(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ----------------------------------------------------------------------------------------------
# leaves and stems
# ----------------------------------------------------------------------------------------------

def leaf(cv, x, y, ang, L, W, bend=.3, teeth=0, shade=-1, rng=None):
    """A lanceolate leaf from (x, y) heading ang (radians): midrib, paired veins, the shaded half
    lined along its form with a black under-edge, the lit half veined only; optional toothed edge."""
    n = max(14, int(L / 1.5))
    pts = _euler(x, y, ang, L, lambda u: bend / L * (1 + u), n)

    def wf(u):
        base = W * (u ** .55) * (1 - u) ** .75 * 1.55
        if teeth and .15 < u < .9:
            v = (u * teeth) % 1.
            base *= .82 + .18 * v
        return base + .25
    R = _poly_rib(pts, wf)
    cv.obj([R.outline()], 1.)
    cv.line(R.contour(0, .02, .9))
    cv.hair(_fill_lines(R, .1 * shade, .97 * shade, 1.5, .04, .96, 3))
    _shadow(cv, R, shade, min(2.4, W * .28), .1, .85)
    nv = max(3, int(L / 7))
    for k in range(nv):
        u = .1 + .75 * (k + .5) / nv
        for s in (1, -1):
            if R.width(u + .1, s) > 2.2:
                cv.hair([R.at(u, 0), R.at(u + .06, .5 * s), R.at(u + .12, .85 * s)])
    return R


def stem(cv, pts, w0, w1, wing=False):
    """A stem along pts tapering w0 -> w1 (half widths): a round-carved highlight and a shaded side;
    wing=True adds the sneezeweed's decurrent wing as a second edge line."""
    R = _poly_rib(pts, lambda u: w0 + (w1 - w0) * u)
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(-.45, 0, 1))
    if w0 > 1.6:
        cv.hair(R.contour(-.8, 0, 1))
    if wing:
        cv.hair(R.contour(.55, 0, 1))
    return R


# ----------------------------------------------------------------------------------------------
# common sneezeweed: Helenium autumnale
# ----------------------------------------------------------------------------------------------

_LIGHT = (-.52, -.62, .58)


def sneezeweed(cv, cx, cy, R, face=.45, droop=.55, seed=0, n=None):
    """A sneezeweed head centred on its globe at (cx, cy), ray length about R. face 1 is a head seen
    from the front (rays all round), lower values see it from the side with the rays swept down."""
    rng = random.Random(seed)
    n = n or (13 if R > 9 else 10)
    Rg = R * (.46 if face < .8 else .42)
    rays = []
    for i in range(n):
        a = TAU * (i + rng.uniform(-.18, .18)) / n + .2
        ca, sa = math.cos(a), math.sin(a)
        bx, by = cx + Rg * .8 * ca, cy + Rg * .8 * sa * face + Rg * .25 * (1 - face)
        dx, dy = ca, sa * face + droop
        ang = math.atan2(dy, dx)
        ln = R * (1.02 - .3 * max(0., sa) * (1 - face)) * rng.uniform(.9, 1.05)
        sgn = 1 if ca >= 0 else -1
        rays.append((sa, bx, by, ang, ln, sgn * droop * .9 * rng.uniform(.7, 1.2)))
    rays.sort(key=lambda r: r[0])           # back rays first, front rays on top
    for sa, bx, by, ang, ln, bend in rays:
        _ray(cv, bx, by, ang, ln, R, bend, back=sa < -.2 and face < .8)
    _globe(cv, cx, cy, Rg, face)


def _ray(cv, x, y, ang, L, R, bend, back=False):
    pts = _euler(x, y, ang, L, lambda u: bend / L * 2 * u, 12)
    Rb = _poly_rib(pts, lambda u: R * (.07 + .17 * u ** .8))
    m = Rb.n
    left = [Rb.at(i / (m - 1), 1) for i in range(m - 1)]
    right = [Rb.at(i / (m - 1), -1) for i in range(m - 1)]
    tip = [Rb.at(.97, .98), Rb.at(.9, .45), Rb.at(1.0, .2), Rb.at(1.04, 0), Rb.at(1.0, -.2),
           Rb.at(.9, -.45), Rb.at(.97, -.98)]
    # extrapolate the tip forward a little
    ex, ey = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
    el = math.hypot(ex, ey) or 1
    tip = [(px + ex / el * (1.5 if k in (3,) else .8 if k in (2, 4) else 0), py + ey / el * (1.5 if k in (3,) else .8 if k in (2, 4) else 0))
           for k, (px, py) in enumerate(tip)]
    cv.obj([left + tip + right[::-1]], 1.)
    if back:
        cv.hair(_fill_lines(Rb, -.92, .92, 1.5, .02, .9, 3))
    else:
        cv.hair(Rb.contour(.42, .06, .86))
        cv.hair(Rb.contour(-.42, .06, .86))
        cv.hair(_fill_lines(Rb, -.15, -.95, 1.5, .0, .88, 2))
        _shadow(cv, Rb, -1, min(1.6, R * .06), .0, .7)
    # the base, darkened where it tucks under the globe
    for u in (.05, .14, .23):
        cv.hair([Rb.at(u, -.9), Rb.at(u + .02, .9)])


def _globe(cv, cx, cy, Rg, face):
    """The globular disc: phyllotactic florets as dots whose weight follows the light."""
    circ = _ell_pts(cx, cy, Rg, Rg, max(20, int(Rg * 3)))[:-1]
    cv.obj([circ], 1.)
    tau = (1 - face) * 1.0 + .25
    ct, st = math.cos(tau), math.sin(tau)
    lx, ly, lz = _LIGHT
    sp = 2.1 if Rg > 8 else 1.9
    N = int(2.2 * PI * Rg * Rg / (sp * sp))
    for i in range(N):
        t = (i + .5) / N
        cz = 1 - t * 1.6
        sz = math.sqrt(max(0., 1 - cz * cz))
        ph = i * 2.399963
        x, y, z = sz * math.cos(ph), sz * math.sin(ph), cz
        y, z = y * ct - z * st, y * st + z * ct
        if z < .12:
            continue
        b = x * lx + y * ly + z * lz
        px, py = cx + Rg * x, cy + Rg * y
        if math.hypot(px - cx, py - cy) > Rg - 1.1:
            continue
        seg = [(px - .25, py), (px + .25, py)]
        if b > .72:
            if i % 2:
                cv.hair(seg)
        elif b > .3:
            cv.hair(seg)
        elif b > -.05:
            cv.line(seg)
        else:
            cv.heavy(seg)
    # the turned-away limb: a black crescent lower right, built of 1 px arcs
    for k, q in enumerate((.75, 1.65, 2.5)):
        if Rg - q < 2:
            break
        span = .9 - .25 * k
        cv.line(_ell_pts(cx, cy, Rg - q, Rg - q, 24, PI * (.25 - span / 2), PI * (.25 + span / 2) + .6))
    # the tuft of the pole, upper left
    cv.hair(_ell_pts(cx - Rg * .28, cy - Rg * .3, Rg * .18, Rg * .12, 10))


def sneezeweed_bud(cv, cx, cy, r):
    circ = _ell_pts(cx, cy, r, r, 18)[:-1]
    cv.obj([circ], 1.)
    for k in range(-2, 3):
        cv.hair([(cx + k * r * .35, cy - r * .9 + abs(k) * r * .2), (cx + k * r * .45, cy + r * .9 - abs(k) * r * .2)])
    cv.line(_ell_pts(cx, cy, r - .75, r - .75, 14, .2, 1.9))
    for s in (-1, 1):
        cv.obj([[(cx + s * r * .2, cy + r * .6), (cx + s * r * 1.3, cy + r * 1.1), (cx + s * r * .5, cy + r * 1.3)]], 1.)
        cv.hair([(cx + s * r * .4, cy + r * .9), (cx + s * r * .9, cy + r * 1.15)])


# ----------------------------------------------------------------------------------------------
# common selfheal: Prunella vulgaris
# ----------------------------------------------------------------------------------------------

def selfheal(cv, x, y, H, seed=0, lean=0.):
    """A selfheal plant rising from (x, y) to about y - H: a square stem with opposite veined
    leaves, a sessile leaf pair under the spike, and the spike itself: stacked hairy bract-tiers
    with hooded two-lipped flowers springing from them."""
    rng = random.Random(seed)
    hs = H * .36
    ws = hs * .56
    sh = H - hs
    pts = _euler(x, y, -PI / 2 + lean, sh, lambda u: -lean * 1.6 / sh, 16)
    sx, sy = pts[-1]
    lw = max(1., H * .016)
    for fu, sc in ((.32, 1.), (.66, .82)):
        px, py = pts[int(fu * 16)]
        for s in (-1, 1):
            leaf(cv, px, py, -PI / 2 + s * 1.05 + lean, H * .3 * sc, H * .07 * sc, -s * .35, 0, s, rng)
    stem(cv, pts, lw * 1.2, lw * .9)
    for s in (-1, 1):
        leaf(cv, sx + s * 1, sy + 1, -PI / 2 + s * 1.35, H * .16, H * .045, -s * .5, 0, s, rng)
    _spike(cv, sx, sy, ws, hs, lean, rng)


def _spike(cv, bx, by, ws, hs, lean, rng):
    ca, sa = math.cos(lean), math.sin(lean)

    def P(u, v):                  # u across (-1..1 of half width), v up (0..1 of height)
        lx, ly = u * ws / 2, -v * hs
        return (bx + lx * ca - ly * sa, by + lx * sa + ly * ca)
    # the dark core seen between the bracts
    core = [P(-.92, 0), P(-.95, .7), P(-.75, .95), P(0, 1.04), P(.75, .95), P(.95, .7), P(.92, 0)]
    cv.obj([core], 1.)
    cv.line(hatch_poly(core, 90 + math.degrees(lean), 1.5))
    cv.hair(hatch_poly(core, 45, 3))
    nt = 6
    tiers = [.07 + .86 * k / (nt - 1) * .97 for k in range(nt)]
    flowers = []
    for k, v in enumerate(tiers[1:5], 1):
        for s in (-1, 1):
            if (k + (s > 0)) % 2 == 0 or rng.random() < .5:
                flowers.append((v + .05, s, (1.0 - .1 * k) * rng.uniform(.92, 1.05)))
    # bracts from the top down, each tier overlapping the one above
    for k in range(nt - 1, -1, -1):
        v = tiers[k]
        wk = 1.02 - .2 * (k / (nt - 1)) ** 2
        th = .15
        poly = [P(-wk, v), P(-wk * .72, v + th * .55), P(-wk * .3, v + th * .66), P(-wk * .08, v + th * .7),
                P(0, v + th * 1.05), P(wk * .08, v + th * .7), P(wk * .3, v + th * .66), P(wk * .72, v + th * .55),
                P(wk, v), P(wk * .8, v - th * .42), P(wk * .4, v - th * .68), P(0, v - th * .74),
                P(-wk * .4, v - th * .68), P(-wk * .8, v - th * .42)]
        cv.obj([poly], 1.)
        low = [P(-wk * .95, v - th * .05), P(wk * .95, v - th * .05), P(wk * .78, v - th * .42),
               P(wk * .4, v - th * .66), P(0, v - th * .72), P(-wk * .4, v - th * .66), P(-wk * .78, v - th * .42)]
        cv.hair(hatch_poly(low, 90 + math.degrees(lean), 1.5))
        cv.hair(hatch_poly(poly, 45 + math.degrees(lean), 3))
        cv.line([P(-wk * .92, v - th * .3), P(-wk * .4, v - th * .56), P(0, v - th * .6),
                 P(wk * .4, v - th * .56), P(wk * .92, v - th * .3)])
        cv.hair([P(0, v + th * .9), P(0, v - th * .3)])
        # the ciliate rim
        rim = [P(-wk, v), P(-wk * .72, v + th * .55), P(-wk * .3, v + th * .66), P(-wk * .08, v + th * .7),
               P(0, v + th * 1.05), P(wk * .08, v + th * .7), P(wk * .3, v + th * .66), P(wk * .72, v + th * .55), P(wk, v)]
        for a, b in zip(rim, rim[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            m = max(1, int(L / 1.8))
            for j in range(m):
                t = (j + .5) / m
                qx, qy = a[0] + dx * t, a[1] + dy * t
                cv.hair([(qx, qy), (qx + dy / L * 1.6, qy - dx / L * 1.6)])
    # the cap of unopened buds
    cap = [P(-.55, .98), P(-.3, 1.12), P(0, 1.16), P(.3, 1.12), P(.55, .98), P(0, .9)]
    cv.obj([cap], 1.)
    cv.hair(hatch_poly(cap, 45, 1.5))
    for v, s, sc in flowers:
        _flower(cv, P(s * .8, v), s, ws * sc * .95, lean)


def _flower(cv, base, s, f, lean):
    """A hooded selfheal flower springing sideways (s = -1 left, +1 right) from a bract tier."""
    x, y = base
    up = -PI / 2 + lean
    a_tube = up + s * 1.05
    tube = _euler(x, y, a_tube, f * .5, lambda u: 0, 6)
    Rt = _poly_rib(tube, lambda u: f * (.07 + .04 * u))
    tx, ty = tube[-1]
    # lower lip: drooping, fringed
    lip = _euler(tx, ty, up + s * 2.0, f * .55, lambda u: s * 1.2 / (f * .55), 8)
    Rl = _poly_rib(lip, lambda u: f * (.06 + .2 * math.sin(PI * min(1, u * 1.1)) ** .7))
    cv.obj([Rl.outline()], 1.)
    cv.hair(Rl.contour(.4, .1, .9))
    cv.hair(Rl.contour(-.4, .1, .9))
    ex, ey = lip[-1]
    for k in (-1, 0, 1):
        cv.hair([Rl.at(.95, k * .6), (ex + k * f * .05 + (ex - lip[-2][0]) * .6, ey + (ey - lip[-2][1]) * .6)])
    cv.obj([Rt.outline()], 1.)
    cv.hair(_fill_lines(Rt, -.2, -.9, 1.5, 0, 1, 1))
    # the hood (upper lip): a helmet arching out and over
    hood = _euler(tx, ty, up + s * .25, f * 1.05, lambda u: s * 2.6 / (f * 1.05) * (.4 + u), 14)
    Rh = _poly_rib(hood, lambda u: f * (.06 + .24 * math.sin(PI * u) ** .6))
    cv.obj([Rh.outline()], 1.)
    cv.hair(_fill_lines(Rh, -s * .05, -s * .95, 1.5, 0, 1, 3))
    cv.hair(Rh.contour(s * .45, .1, .85))
    _shadow(cv, Rh, -s, min(1.8, f * .09), .05, .95)


# ----------------------------------------------------------------------------------------------
# the bee, the paw, Mt. Hood
# ----------------------------------------------------------------------------------------------

def bee(cv, cx, cy, s, ang=-.35):
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (cx + (u * ca - v * sa) * s, cy + (u * sa + v * ca) * s)
    for wv, sp in ((-1, .9), (-1, .45)):
        wing = [P(-.1 + .9 * math.cos(t) * .5 * sp + .2, -.25 + wv * (.55 + .5 * math.sin(t)) * sp)
                for t in [TAU * i / 16 for i in range(16)]]
        cv.obj([wing], .5)
        cv.hair([P(0, -.3), P(.35 * sp, -.25 - .9 * sp)])
    body = [P(.85 * math.cos(t) * .9 - .2, .45 * math.sin(t)) for t in [TAU * i / 20 for i in range(20)]]
    cv.obj([body], 1.)
    for u in (-.75, -.45, -.15):
        band = [P(u, -.42), P(u + .14, -.43), P(u + .14, .43), P(u, .42)]
        cv.line(hatch_poly(band, 90 + math.degrees(ang), 1.))
    head = [P(.85 + .28 * math.cos(t), .28 * math.sin(t)) for t in [TAU * i / 12 for i in range(12)]]
    cv.obj([head], 1.)
    cv.line(hatch_poly(head, 45, 1.5))
    cv.hair([P(1.05, -.2), P(1.35, -.6)])
    cv.hair([P(1.05, -.1), P(1.45, -.3)])


def paw_print(x, y, s):
    """A dog's paw pressed into the soil: four toe pads over a heel pad, cut white with a black rim."""
    o = []
    heel = [(x + s * .55 * math.cos(t), y + s * .1 + s * .42 * math.sin(t) * (1 if math.sin(t) > 0 else 1.2) - s * .05 * math.cos(2 * t))
            for t in [TAU * i / 20 for i in range(20)]]
    toes = [(-.62, -.42, .2, .26), (-.22, -.72, .21, .27), (.22, -.72, .21, .27), (.62, -.42, .2, .26)]
    d = _d(heel, True, 0)
    for tx, ty, rx, ry in toes:
        d += _d(_ell_pts(x + tx * s, y + ty * s, rx * s, ry * s, 12)[:-1], True, 0)
    o.append(f'<path d="{d}" fill="#fff" stroke="#000" stroke-width="1"/>')
    sh = _d(_ell_pts(x + s * .05, y + s * .2, s * .38, s * .22, 12, .3, 2.6), False, 0)
    o.append(f'<path d="{sh}" fill="none" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def mt_hood(cv, cx, by, w, h):
    """Mt. Hood from Sauvie Island: a lopsided cone, snow above a ragged line, ridges and gullies."""
    pk = (cx + w * .05, by - h)
    outline = [(cx - w / 2, by), (cx - w * .3, by - h * .32), (cx - w * .15, by - h * .62),
               (cx - w * .04, by - h * .88), pk, (cx + w * .1, by - h * .92), (cx + w * .2, by - h * .7),
               (cx + w * .32, by - h * .45), (cx + w / 2, by)]
    cv.obj([outline], 1.)
    rock = [(cx - w / 2, by), (cx - w * .36, by - h * .25), (cx - w * .25, by - h * .3), (cx - w * .18, by - h * .2),
            (cx - w * .05, by - h * .34), (cx + w * .05, by - h * .26), (cx + w * .16, by - h * .38),
            (cx + w * .27, by - h * .3), (cx + w * .36, by - h * .33), (cx + w / 2, by)]
    cv.hair(hatch_poly(rock, 45, 2))
    cv.hair(hatch_poly(rock, -45, 3))
    for k in range(-3, 4):
        x0 = pk[0] + k * w * .07
        cv.hair([(pk[0] + k * w * .02, pk[1] + h * .12 + abs(k) * h * .05), (x0, by - h * .3)])
    # shadowed east face
    east = [pk, (cx + w * .1, by - h * .92), (cx + w * .2, by - h * .7), (cx + w * .32, by - h * .45),
            (cx + w * .2, by - h * .38), (cx + w * .1, by - h * .55)]
    cv.hair(hatch_poly(east, 90, 1.5))


def treeline(cv, x0, x1, top, base, seed):
    """Cottonwood crowns along the island, dark with vertical rules."""
    rng = random.Random(seed)
    pts = [(x0, base)]
    x = x0
    while x < x1:
        r = rng.uniform(3.5, 7.)
        hh = rng.uniform(.4, 1.) * (base - top)
        for i in range(7):
            t = PI * i / 6
            pts.append((x + r - r * math.cos(t), base - hh + (1 - math.sin(t)) * r * .7 - r * .25 * math.sin(t)))
        x += r * 1.6
    pts.append((x1, base))
    pts = [(min(max(p[0], x0), x1), p[1]) for p in pts]
    cv.obj([pts], .5)
    cv.hair(hatch_poly(pts, 90, 1.5))


# ----------------------------------------------------------------------------------------------
# the vignette
# ----------------------------------------------------------------------------------------------

def garden(x, y, w, h, seed=0, clip_d=None, mode="full"):
    """The bed of selfheal and sneezeweed filling the box (clipped to clip_d), mode 'full' or
    'compact' (the small medallion of the short frieze)."""
    rng = random.Random(seed)
    o = []
    box = f"M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z"
    o.append(f'<path d="{box}" fill="{pat("L")}" stroke="none"/>')
    sky = []
    yy = math.floor(y / 3) * 3 + 2.75
    while yy < y + h * .4:
        t = (yy - y) / (h * .4)
        xx = x
        while xx < x + w:
            ln = rng.uniform(8, 40)
            if rng.random() < (1 - t) ** 1.3:
                sky.append(f"M{_n(xx)},{_n(yy)}h{_n(ln)}")
            xx += ln + rng.uniform(2, 10) * (.3 + t)
        yy += 3
    if sky:
        o.append(f'<path d="{"".join(sky)}" stroke="#000" stroke-width=".5"{_CR}/>')
    soil_top = y + h * (.82 if mode == "full" else .76)
    back = Canvas()
    if mode == "full":
        mh = h * .34
        mt_hood(back, x + w * .54, soil_top - h * .06, mh * 2.3, mh)
        treeline(back, x - 2, x + w + 2, soil_top - h * .12, soil_top + 1, seed + 3)
    o.append(back.svg())
    # soil: stippled, with a ragged top
    sp = [(x - 1, y + h + 1)]
    k = 0
    while True:
        px = x - 1 + k * 3.
        sp.append((min(px, x + w + 1), soil_top + 1.2 * math.sin(k * 1.7) + rng.uniform(-.6, .6)))
        if px >= x + w + 1:
            break
        k += 1
    sp.append((x + w + 1, y + h + 1))
    o.append(f'<path d="{_d(sp, True, 0)}" fill="{pat("S")}" stroke="none"/>')
    o.append(f'<path d="{_d(sp[1:-1], False, .3)}" fill="none" stroke="#000" stroke-width="1"/>')
    furrow = []
    for j in range(1, 4):
        yy = soil_top + j * (y + h - soil_top) / 4
        furrow.append(_d([(x, yy), (x + w * .3, yy - .8), (x + w * .7, yy + .6), (x + w, yy)], False, 0))
    o.append(f'<path d="{"".join(furrow)}" stroke="#000" stroke-width=".5" fill="none"/>')
    # the paw print
    ps = max(5., min(h * .075, 9.))
    o.append(paw_print(x + w * (.47 if mode == "full" else .5), soil_top + (y + h - soil_top) * .52 + ps * .1, ps))
    cv = Canvas()
    gy = soil_top + 1
    if mode == "full":
        # sneezeweed: three heads on winged stems, left of centre
        heads = [(x + w * .2, y + h * .5, h * .13, .5), (x + w * .38, y + h * .3, h * .17, .62),
                 (x + w * .07, y + h * .3, h * .1, .4)]
        for k, (hx, hy, R, face) in enumerate(heads):
            bx = hx + (w * .03 if k == 1 else -w * .01)
            pts = [(bx + (hx - bx) * (i / 12) ** 1.4, gy - (gy - hy - R * .3) * i / 12) for i in range(13)]
            leaf(cv, pts[5][0], pts[5][1], -PI / 2 - .95 + k * .1, h * .22, h * .04, .25, 5, 1, rng)
            leaf(cv, pts[8][0], pts[8][1], -PI / 2 + .9, h * .18, h * .035, -.3, 5, -1, rng)
            stem(cv, pts, max(1., h * .012), max(.8, h * .009), True)
        sneezeweed_bud(cv, x + w * .29, y + h * .45, h * .035)
        for k, (hx, hy, R, face) in sorted(enumerate(heads), key=lambda t: t[1][2]):
            sneezeweed(cv, hx, hy, R, face, .55, seed + k)
        # selfheal: two plants right of centre, the taller in front
        selfheal(cv, x + w * .86, gy, h * .55, seed + 11, .12)
        selfheal(cv, x + w * .68, gy, h * .72, seed + 12, -.06)
        bee(cv, x + w * .87, y + h * .2, max(3., h * .045), -.3)
    else:
        R = h * .23
        hx, hy = x + w * .3, y + h * .42
        pts = [(hx + 2, gy), (hx, hy)]
        stem(cv, [(hx + 1 - i * .1, gy - (gy - hy) * i / 8) for i in range(9)], 1., .8, True)
        leaf(cv, hx + .5, gy - (gy - hy) * .45, -PI / 2 - 1., h * .3, h * .07, .25, 4, 1, rng)
        sneezeweed(cv, hx, hy, R, .6, .5, seed)
        selfheal(cv, x + w * .7, gy, h * .82, seed + 5, 0)
    o.append(cv.svg())
    body = "".join(o)
    if clip_d:
        body = _clip_g(_uid("gv", x, y, w, h, seed), clip_d, body)
    return body


# ----------------------------------------------------------------------------------------------
# lettering: a small engraved roman in strokes
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


_G = {
    "A": (.62, [[(0, 1), (.31, 0), (.62, 1)], [(.13, .64), (.49, .64)]]),
    "B": (.54, [[(0, 0), (0, 1), (.36, 1)] + _arc(.36, .75, .18, .25, PI / 2, -PI / 2, 8) + [(0, .5)],
                [(0, 0), (.32, 0)] + _arc(.32, .25, .16, .25, -PI / 2, PI / 2, 8)]),
    "D": (.6, [[(0, 0), (0, 1), (.22, 1)] + _arc(.22, .5, .38, .5, PI / 2, -PI / 2, 14) + [(0, 0)]]),
    "E": (.48, [[(.48, 0), (0, 0), (0, 1), (.48, 1)], [(0, .5), (.38, .5)]]),
    "F": (.46, [[(.46, 0), (0, 0), (0, 1)], [(0, .5), (.36, .5)]]),
    "G": (.62, [_arc(.31, .5, .31, .5, -PI * .22, -PI * 1.95, 18) + [(.62, .62), (.36, .62)]]),
    "H": (.56, [[(0, 0), (0, 1)], [(.56, 0), (.56, 1)], [(0, .5), (.56, .5)]]),
    "I": (0., [[(0, 0), (0, 1)]]),
    "L": (.46, [[(0, 0), (0, 1), (.46, 1)]]),
    "M": (.72, [[(0, 1), (0, 0), (.36, .72), (.72, 0), (.72, 1)]]),
    "N": (.58, [[(0, 1), (0, 0), (.58, 1), (.58, 0)]]),
    "O": (.66, [_arc(.33, .5, .33, .5, 0, TAU, 22)]),
    "S": (.52, [_arc(.26, .25, .24, .25, -PI * .1, -PI * 1.5, 10) + _arc(.26, .75, .26, .25, -PI / 2, PI * .85, 10)]),
    "T": (.58, [[(0, 0), (.58, 0)], [(.29, 0), (.29, 1)]]),
    "W": (.84, [[(0, 0), (.2, 1), (.42, .25), (.64, 1), (.84, 0)]]),
    "Z": (.54, [[(0, 0), (.54, 0), (0, 1), (.54, 1)]]),
}


def _text_lines(text, cap):
    """Polylines for text with cap height `cap`, origin at its top-left; returns (lines, width)."""
    lines = []
    x = 0.
    for ch in text:
        if ch == " ":
            x += cap * .45
            continue
        if ch == "*":
            lines.append(_ell_pts(x + cap * .12, cap * .5, cap * .1, cap * .1, 8))
            x += cap * .24 + cap * .26
            continue
        gw, strokes = _G[ch]
        for st in strokes:
            lines.append([(x + px * cap, py * cap) for px, py in st])
        x += gw * cap + cap * .26
    return lines, x - cap * .26


def lettering_on(centre, text, cap, sw=1.):
    """Text riding the ribbon's centre line (upright to the local tangent)."""
    lines, tw = _text_lines(text, cap)
    xs = [p[0] for p in centre]
    cx = (xs[0] + xs[-1]) / 2
    x0 = cx - tw / 2

    def at(xq):
        for i in range(len(centre) - 1):
            if centre[i][0] <= xq <= centre[i + 1][0]:
                t = (xq - centre[i][0]) / (centre[i + 1][0] - centre[i][0])
                yy = centre[i][1] + (centre[i + 1][1] - centre[i][1]) * t
                ang = math.atan2(centre[i + 1][1] - centre[i][1], centre[i + 1][0] - centre[i][0])
                return yy, ang
        return centre[-1][1], 0.
    out = []
    for pl in lines:
        mx = x0 + sum(p[0] for p in pl) / len(pl)
        yy, ang = at(mx)
        ca, sa = math.cos(ang), math.sin(ang)
        q = []
        for px, py in pl:
            dx, dy = x0 + px - mx, py - cap / 2
            q.append((mx + dx * ca - dy * sa, yy + dx * sa + dy * ca))
        out.append(q)
    return f'<path d="{"".join(_d(p, False, 0) for p in out)}" fill="none" stroke="#000" stroke-width="{sw}"/>'


# ----------------------------------------------------------------------------------------------
# frame layouts (adapted from engraving_codex.frame_plate)
# ----------------------------------------------------------------------------------------------

def _field(cx, cy, ix, iy, iw, ih):
    k = 2 ** (-1 / 2.6)
    a, b = iw / 2 / k + 6, ih / 2 / k + 6
    return cx - a, cy - b, 2 * a, 2 * b


def _eye(cx, cy, r, side, a_out=0., turns=1.4, tail=.9, up=True):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    return volute_spine(cx, cy, r, a0, turns, flip, tail, -.5 if up else .5)[-1]


def _pair_unit(cv, cx, cy, r, side, rng, a_out=0., turns=1.4, tail=.9, up=True, fronds=3):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    _volute(cv, cx, cy, r, a0, turns, flip, rng, tail, -.5 if up else .5, r * .15, fronds)


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 130)
    o.append(C._clip(_uid("b", w, h, seed), 0, top, w, gh,
                     scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 4, ry - 4
    fd = _d(_ell_pts(cx, cy, fx, fy, 64)[:-1], True, 0)
    o.append(garden(cx - fx, cy - fy, 2 * fx, 2 * fy, seed, fd, "compact"))
    o.append(f'<path d="{_d(_ell_pts(cx, cy, fx, fy, 64), False, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = [f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>']
    em = min(12., 6 + h * .025)
    o.append(egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.8)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        ex, ey = _eye(vx, vy, r, side, 0, 1.4, .9, True)
        sneezeweed(main, ex, ey, r * .3, 1., .12, seed + 40 + side, 12)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                 max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), fd = cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, ix, iy, iw, ih)
    o.append(garden(fx, fy, fw, fh, seed, fd, "full"))
    o.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = [f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>']
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        ex, ey = _eye(vx, vy, r1, side, 10, 1.45, .8, True)
        sneezeweed(main, ex, ey, r1 * .3, 1., .12, seed + 50 + side, 13)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        _pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        ex, ey = _eye(vx, vy, r2, side, -10, 1.4, .8, False)
        sneezeweed(main, ex, ey, r2 * .28, 1., .12, seed + 60 + side, 12)
        occ.append(("c", vx, vy, r2))
    fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                 max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), fd = cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, ix, iy, iw, ih)
    o.append(garden(fx, fy, fw, fh, seed, fd, "full"))
    o.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')
    # crest: a selfheal spike rising from the palmette
    crest = Canvas()
    cs = min(ch * .2 + top_free, 62)
    palmette(cx, cy - ch / 2 + 7, cs, True, rng.randrange(1 << 20), cv=crest)
    _spike(crest, cx, cy - ch / 2 + 7 - cs * .1, cs * .26, cs * .58, 0., random.Random(seed + 7))
    o.append(crest.svg())
    bh = min(16, ph * .05)
    bsvg, centre = ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(lettering_on(centre, "SELFHEAL * SNEEZEWEED", bh * .44, 1))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: lettered, its flanks ruled
    cap = min(th * .55, 11)
    lines, lw = _text_lines("WHAT IS BLOOMING", cap)
    lx = tx + (tw - lw) / 2
    ly = ty + (th - cap) / 2 + .5
    for sx0, sx1 in ((tx + 3, lx - 6), (lx + lw + 6, tx + tw - 2)):
        if sx1 - sx0 > 4:
            o.append(f'<path d="M{_n(sx0)},{_n(ty + 3)}h{_n(sx1 - sx0)}v{_n(th - 4.5)}h{_n(sx0 - sx1)}z" fill="{pat("L")}" stroke="none"/>')
    for dx_ in (lx - 3.5, lx + lw + 3.5):
        o.append(f'<path d="{_d(_ell_pts(dx_, ty + th / 2, 1.3, 1.3, 8), True, 0)}" fill="#000"/>')
    o.append(f'<path d="{"".join(_d([(lx + px, ly + py_) for px, py_ in pl], False, 0) for pl in lines)}" '
             f'fill="none" stroke="#000" stroke-width="{1.5 if cap > 9 else 1}"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(_uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                     r_scale=1.15, n=2)))
        o.append(palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return svg_doc(w, h, body)
