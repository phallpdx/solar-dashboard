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
    soil_top = y + h * (.82 if mode == "full" else .76)
    skc = Canvas()
    kk_sky(skc, x, y, w, soil_top + 2, seed, 1 if mode == "full" else 0)
    o.append(skc.svg())
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


# ==============================================================================================
# KING-TIER KIT (batch 7). Fine English scroll as on the GRS vise, the Hunt panels and the
# presentation Colt: dozens of small true spirals grown from one stem and branching on in a
# continuous rhythm, every leaf cut with fine parallel shading on its shadow side and a bright
# edge; the ground between punched to a dark matte; every panel framed in gold-line borders and
# beading; the page's subject set in an inlaid, bead-ringed portrait medallion.
#   kk_defs()                         the matte and bead patterns (put once in the body)
#   kk_matte(d)                       punched matte ground filling path d
#   kk_field(cv, box, obst, roots, seed, rmin, rmax)   the scroll field (see its doc)
#   kk_frame(x, y, w, h, ...)         gold-line + beaded border round a panel; corner rosettes
#   kk_medallion(cx, cy, rx, ry)      bead-ringed inlay setting -> (svg_under, svg_over, clip d)
#   kk_plate(w, h, scene, egg, seed)  the whole plate at any size (band / cartouche / tall)
# ==============================================================================================
import math as _m
import random as _r
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _PI


def _kn(x):
    return _C._n(x)


# ---- matte, beads -----------------------------------------------------------------------------

def kk_defs():
    rng = _r.Random(11)
    cells = set()
    while len(cells) < 8:
        cells.add((rng.randrange(6), rng.randrange(6)))
    punch = "".join(f"M{x},{y}h1v1h-1z" for x, y in sorted(cells))
    return ('<defs><pattern id="kkM" width="6" height="6" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h6v6h-6z" fill="#000"/><path d="{punch}" fill="#fff"/></pattern></defs>')


def kk_matte(d):
    return f'<path d="{d}" fill="url(#kkM)" stroke="none"/>'


def _rect_d(x, y, w, h):
    return f"M{_kn(x)},{_kn(y)}h{_kn(w)}v{_kn(h)}h{_kn(-w)}z"


def _ell_d(cx, cy, rx, ry, n=72):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n)[:-1], True, .1)


def kk_beads(pts, r=1.5):
    """Beads (white, .5 outlined, a black shadow speck lower right) centred on pts. 2 elements."""
    rr = _kn(r)
    a = "".join(f"M{_kn(x - r)},{_kn(y)}a{rr},{rr} 0 1,0 {_kn(2 * r)},0a{rr},{rr} 0 1,0 {_kn(-2 * r)},0z" for x, y in pts)
    s = max(.5, round(r * .7 * 2) / 2)
    b = "".join(f"M{_kn(x + r * .25)},{_kn(y + r * .2)}h{_kn(s)}v{_kn(s)}h{_kn(-s)}z" for x, y in pts)
    return (f'<path d="{a}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{b}" fill="#000" stroke="none"/>')


def _along(poly, pitch, closed=True):
    """Points spaced `pitch` apart along a polyline."""
    P = poly + [poly[0]] if closed else poly
    out = []
    carry = 0.
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        L = _m.hypot(bx - ax, by - ay)
        t = carry
        while t < L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L))
            t += pitch
        carry = t - L
    return out


# ---- the scroll field -----------------------------------------------------------------------

def _leaf(cv, x, y, ang, L, W, c, teeth=2, seed=0):
    """A small acanthus leaf: rolled tip, forward rounded teeth on its outer edge, a vein, fine
    parallel cuts on its shadow side (+c, the side it curls toward), a bright outer edge."""
    n = max(8, int(L / 1.1))
    pts = _C._euler(x, y, ang, L, lambda u: c * (.5 + 3.4 * _C._smooth(.55, 1., u) ** 2) / L * 1.6, n)
    ph = (seed * .41) % 1.

    def prof(u, t, amp):
        w = W * (u ** .5) * ((1 - u) ** .75) / .41 + .3
        if t and .3 < u < .97:
            v = ((u - .3) / .67 * t + ph * .3) % 1.
            w *= 1 - amp * (1 - v) ** 2
        return w
    wo = [prof(i / n, teeth, .36) for i in range(n + 1)]
    wi = [prof(i / n, 0, 0) * .85 for i in range(n + 1)]
    R = _C._Rib(pts, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    # burin cuts: curved strokes that leave the light half and sweep forward over the shadow
    # half to the edge, following the leaf's own curve; longer (darker) toward the root
    Lr = R.L
    du = 1.5 / Lr
    cuts = []
    u = .05
    while u < .9:
        s0 = -.5 * c * (1 - u) ** .6
        cuts.append([R.at(u, s0), R.at(u + .08, .93 * c)])
        u += du
    out = []
    for k, q in enumerate(cuts):
        out.extend(q if k % 2 == 0 else q[::-1])
    if out:
        cv.hair(out)
    if W > 2.6:
        cv.line(R.inset(c, lambda u: .5 if .12 < u < .88 else None, .05, .95))
    return R


class _Spiral:
    __slots__ = ("cx", "cy", "r", "w", "par", "kids", "pts", "S", "deg")

    def __init__(self, cx, cy, r):
        self.cx, self.cy, self.r = cx, cy, r
        self.w = 1
        self.par = None
        self.kids = []
        self.pts = None


def _spiral_pts(cx, cy, R, th0, w, turns=1.45, end=.15):
    T = _TAU * turns
    b = -_m.log(end) / T
    n = max(24, int(R * T * .35))
    return [(cx + R * _m.exp(-b * T * i / n) * _m.cos(th0 + w * T * i / n),
             cy + R * _m.exp(-b * T * i / n) * _m.sin(th0 + w * T * i / n)) for i in range(n + 1)]


def _bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _resample(pts, step=1.5):
    out = [pts[0]]
    acc = 0.
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = _m.hypot(bx - ax, by - ay)
        if L == 0:
            continue
        t = step - acc
        while t <= L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L))
            t += step
        acc = (acc + L) % step
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def kk_field(cv, box, obst, roots, seed=0, rmin=6., rmax=16., grid=None, leafy=1., inside=None):
    """Fill box (x, y, w, h) with fine scroll. obst: shapes kept clear, ('e', cx, cy, rx, ry)
    ellipses, ('r', x0, y0, x1, y1) rects and ('c', cx, cy, r) circles. roots: [(x, y, ang_degrees)] stem sources: every
    spiral is joined, by a stem branching tangentially off its neighbour, back to a root, so the
    whole field flows from them. inside(x, y) -> bool optionally limits the field to a shape.
    Spirals are packed largest-first (radius rmax down to rmin) and painted from the twigs back
    to the root, so each parent stem lies over the branches it throws."""
    x, y, w, h = box
    rng = _r.Random(seed)
    grid = grid or max(3., min(4.5, rmin * .36))
    nx, ny = max(2, int(w / grid)), max(2, int(h / grid))
    gx = w / nx
    gy = h / ny
    D = []
    for j in range(ny):
        py = y + (j + .5) * gy
        for i in range(nx):
            px = x + (i + .5) * gx
            d = min(px - x, x + w - px, py - y, y + h - py) + rmin * .35
            if inside is not None and not inside(px, py):
                d = -1.
            for o in obst:
                if o[0] == "c":
                    continue
                if o[0] == "e":
                    _, ox, oy, rx, ry = o
                    q = _m.hypot((px - ox) / rx, (py - oy) / ry)
                    dd = (q - 1) * min(rx, ry)
                else:
                    _, x0, y0, x1, y1 = o
                    ddx = max(x0 - px, 0., px - x1)
                    ddy = max(y0 - py, 0., py - y1)
                    dd = _m.hypot(ddx, ddy) if (ddx or ddy) else -1.
                if dd < d:
                    d = dd
            D.append(d)

    def stamp(cx, cy, r, reach):
        i0, i1 = max(0, int((cx - reach - x) / gx)), min(nx - 1, int((cx + reach - x) / gx))
        j0, j1 = max(0, int((cy - reach - y) / gy)), min(ny - 1, int((cy + reach - y) / gy))
        for jj in range(j0, j1 + 1):
            qy = y + (jj + .5) * gy
            base = jj * nx
            for ii in range(i0, i1 + 1):
                dd = _m.hypot(x + (ii + .5) * gx - cx, qy - cy) - r
                if dd < D[base + ii]:
                    D[base + ii] = dd
    for o in obst:
        if o[0] == "c":
            stamp(o[1], o[2], o[3], o[3] + rmax + 2)
    sp = []
    while len(sp) < 400:
        m = max(D)
        if m < rmin:
            break
        k = D.index(m)
        i, j = k % nx, k // nx
        px, py = x + (i + .5) * gx, y + (j + .5) * gy
        r = min(rmax, m) * rng.uniform(.86, 1.)
        r = max(r, rmin)
        s = _Spiral(px + rng.uniform(-.4, .4) * gx, py + rng.uniform(-.4, .4) * gy, r)
        sp.append(s)
        reach = r + rmax + 2
        i0, i1 = max(0, int((px - reach - x) / gx)), min(nx - 1, int((px + reach - x) / gx))
        j0, j1 = max(0, int((py - reach - y) / gy)), min(ny - 1, int((py + reach - y) / gy))
        for jj in range(j0, j1 + 1):
            qy = y + (jj + .5) * gy
            base = jj * nx
            for ii in range(i0, i1 + 1):
                qx = x + (ii + .5) * gx
                dd = _m.hypot(qx - s.cx, qy - s.cy) - r * .97
                if dd < D[base + ii]:
                    D[base + ii] = dd
    if not sp:
        return
    # the tree: Prim from the roots
    done = []
    todo = list(sp)
    rootn = []
    for (rx_, ry_, ra) in roots:
        rn = _Spiral(rx_, ry_, 0.)
        rn.pts = None
        rn.deg = ra
        rootn.append(rn)

    def gap(a, b):
        return _m.hypot(a.cx - b.cx, a.cy - b.cy) - a.r - b.r
    best = {}
    for s in todo:
        bd, bp = 1e9, None
        for rn in rootn:
            dd = _m.hypot(s.cx - rn.cx, s.cy - rn.cy) - s.r
            if dd < bd:
                bd, bp = dd, rn
        best[id(s)] = (bd, bp)
    order = []
    while todo:
        s = min(todo, key=lambda q: best[id(q)][0])
        todo.remove(s)
        s.par = best[id(s)][1]
        s.par.kids.append(s)
        order.append(s)
        for q in todo:
            dd = gap(q, s) * 1.0
            if dd < best[id(q)][0]:
                best[id(q)] = (dd, s)
    # geometry, from the roots outward: winding alternates (S-rhythm), the stem leaves its parent
    # running forward and arrives tangentially at the child's outer turn
    for s in order:
        p = s.par
        dx, dy = s.cx - p.cx, s.cy - p.cy
        dl = _m.hypot(dx, dy) or 1.
        ux, uy = dx / dl, dy / dl                 # parent -> child
        if p.pts is None:                         # a root
            pa = _m.radians(p.deg)
            P0, t0 = (p.cx, p.cy), (_m.cos(pa), _m.sin(pa))
            # wind so that arriving along t0 the curl turns away from the root's line
            cr = t0[0] * uy - t0[1] * ux
            s.w = 1 if cr >= 0 else -1
            if rng.random() < .25:
                s.w = -s.w
        else:
            s.w = -p.w if rng.random() < .82 else p.w
            # the branch point: on the parent's outer turn, nearest the child, heading toward it
            pts = p.pts
            lim = max(3, int(len(pts) * .5))
            bi, bv = 1, 1e9
            for i in range(1, lim):
                qx, qy = pts[i]
                tx, ty = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
                tl = _m.hypot(tx, ty) or 1.
                dd = _m.hypot(qx - s.cx, qy - s.cy)
                fw = (tx * (s.cx - qx) + ty * (s.cy - qy)) / tl / max(dd, 1.)
                v = dd - fw * s.r * 1.2
                if v < bv:
                    bv, bi = v, i
            P0 = pts[bi]
            tx, ty = pts[bi + 1][0] - pts[bi - 1][0], pts[bi + 1][1] - pts[bi - 1][1]
            tl = _m.hypot(tx, ty) or 1.
            t0 = (tx / tl, ty / tl)
            # if the parent runs away from the child here, wind the child to suit the turn
            cr = t0[0] * (s.cy - P0[1]) - t0[1] * (s.cx - P0[0])
            s.w = 1 if cr >= 0 else -1
            if rng.random() < .2:
                s.w = -s.w
        # the child's start point: where its tangent runs away from P0
        ddx, ddy = s.cx - P0[0], s.cy - P0[1]
        dl = _m.hypot(ddx, ddy) or 1.
        dx_, dy_ = -ddx / dl, -ddy / dl           # child -> P0
        R = s.r * .86
        if s.w > 0:
            nvx, nvy = -dy_, dx_
        else:
            nvx, nvy = dy_, -dx_
        # rotate the start a little forward so the stem wraps into the curl
        th0 = _m.atan2(nvy, nvx) - s.w * .35
        spi = _spiral_pts(s.cx, s.cy, R, th0, s.w, rng.uniform(1.3, 1.6))
        S0 = spi[0]
        st = (spi[1][0] - S0[0], spi[1][1] - S0[1])
        sl = _m.hypot(*st) or 1.
        st = (st[0] / sl, st[1] / sl)
        L = _m.hypot(S0[0] - P0[0], S0[1] - P0[1])
        k = max(2., L * .42)
        stem = _bez(P0, (P0[0] + t0[0] * k, P0[1] + t0[1] * k), (S0[0] - st[0] * k, S0[1] - st[1] * k), S0,
                    max(4, int(L / 2)))
        s.pts = _resample(stem[:-1] + spi, 1.4)
        s.S = len(_resample(stem[:-1], 1.4)) if len(stem) > 1 else 0
    # paint: twigs first, root last
    for s in order[::-1]:
        _scroll(cv, s, rng, leafy)


def _scroll(cv, s, rng, leafy):
    pts = s.pts
    n = len(pts)
    if n < 4:
        return
    iS = min(s.S, n - 3)
    R = s.r * .8
    w0 = max(1., min(3.2, R * .2))
    W = []
    for i in range(n):
        if i < iS:
            f = i / max(1, iS)
            W.append(w0 * (.55 + .45 * f))
        else:
            f = (i - iS) / max(1, n - 1 - iS)
            W.append(max(.45, w0 * (1 - .78 * f)))
    Rb = _C._Rib(pts, W, W)
    ins = s.w                                      # the spiral turns toward +normal when w > 0? test
    # normal side toward the centre at the spiral's start
    m = min(n - 2, iS + 2)
    q = Rb.at(m / (n - 1), 1.)
    ins = 1 if _m.hypot(q[0] - s.cx, q[1] - s.cy) < _m.hypot(pts[m][0] - s.cx, pts[m][1] - s.cy) else -1
    Ltot = Rb.L

    def tang(i):
        i = min(n - 2, max(1, i))
        a, b = pts[i - 1], pts[i + 1]
        return _m.atan2(b[1] - a[1], b[0] - a[0])
    # leaves on the outer side of the curl, nearer the root on top: laid from the eye back
    spots = []
    i = iS + 1
    lim = iS + int((n - iS) * .62)
    while i < lim:
        px, py = pts[i]
        rad = _m.hypot(px - s.cx, py - s.cy)
        ll = (s.r * 1.1 - rad * .2) * .9 * rng.uniform(.85, 1.1) * leafy ** .3
        ll = min(ll, s.r * 1.05)
        if ll < 3.2:
            break
        spots.append((i, ll, rad))
        i += max(2, int(ll * .62 / 1.4))
    # leaves along the connecting stem, alternating, springing forward
    st = []
    if iS > 6 and leafy > .3:
        j = 3
        side = 1
        while j < iS - 2:
            st.append((j, side))
            side = -side
            j += max(5, int(11 / 1.4))
    for (i, ll, rad) in spots[::-1]:
        b = Rb.at(i / (n - 1), -ins * .6)
        _leaf(cv, b[0], b[1], tang(i) - ins * rng.uniform(.32, .5), ll, ll * .32, ins, 2 if ll > 6 else 1,
              rng.randrange(97))
    for (j, side) in st:
        b = Rb.at(j / (n - 1), side * .6)
        ll = min(9., s.r * .7) * rng.uniform(.8, 1.)
        if ll > 3:
            _leaf(cv, b[0], b[1], tang(j) + side * .7, ll, ll * .3, -side, 1, rng.randrange(97))
    # the stem: a bright cut edge outside, a shadow line inside
    cv.obj([Rb.outline()], .5)
    if w0 > 1.2:
        cv.hair(Rb.contour(.3 * ins, 0., 1., minw=1.25))
    # one leaf rolling in toward the eye
    i = iS + int((n - iS) * .55)
    if i < n - 2 and s.r > 7:
        b = Rb.at(i / (n - 1), ins * .5)
        ll = s.r * .42
        _leaf(cv, b[0], b[1], tang(i) + ins * .35, ll, ll * .28, ins, 1, rng.randrange(97))
    ex, ey = pts[-1]
    rr = max(.9, W[-1] * 1.3)
    cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)


# ---- frames, medallion --------------------------------------------------------------------

def kk_frame(x, y, w, h, bead=1.5, rosette=True):
    """A panel's border drawn just outside x..x+w, y..y+h: a gold wire (white 1.5 line in fine
    black rules), a bead row, a black fillet; corner rosettes. Returns (svg, outer margin)."""
    o = []
    m1 = 1.
    # the gold wire
    o.append(f'<path d="{_rect_d(x - 3, y - 3, w + 6, h + 6)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_rect_d(x - 1.25, y - 1.25, w + 2.5, h + 2.5)}" fill="none" stroke="#000" stroke-width=".5"/>')
    # bead row in a white channel outside
    g = 3 + bead + 1.5
    o.append(f'<path d="{_rect_d(x - g - bead - 1.5, y - g - bead - 1.5, w + 2 * (g + bead + 1.5), h + 2 * (g + bead + 1.5))}'
             f'{_rect_d(x - 3.5, y - 3.5, w + 7, h + 7)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    pts = _along([(x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)], bead * 2 + 1)
    o.append(kk_beads(pts, bead))
    e = g + bead + 1.5
    o.append(f'<path d="{_rect_d(x - e, y - e, w + 2 * e, h + 2 * e)}" fill="none" stroke="#000" stroke-width="1"/>')
    if rosette:
        for cx, cy in ((x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)):
            o.append(kk_rosette(cx, cy, bead * 2.6))
    return "".join(o), e


def kk_rosette(cx, cy, r):
    pet = []
    for i in range(8):
        a = i * _PI / 4
        pet.append([(cx + r * .3 * _m.cos(a - .5), cy + r * .3 * _m.sin(a - .5)),
                    (cx + r * _m.cos(a), cy + r * _m.sin(a)),
                    (cx + r * .3 * _m.cos(a + .5), cy + r * .3 * _m.sin(a + .5))])
    d = "".join(_C._d(p, True, 0) for p in pet)
    return (f'<path d="{_ell_d(cx, cy, r + 1, r + 1, 24)}" fill="#000" stroke="none"/>'
            f'<path d="{d}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{_ell_d(cx, cy, r * .28, r * .28, 10)}" fill="#fff" stroke="#000" stroke-width=".5"/>')


def kk_medallion(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval scene: a black fillet, a bead ring, a gold wire and a fine
    rule. Returns (svg_over, clip_d of the scene, outer rx, outer ry)."""
    o = []
    g = 2.5
    a1, b1 = rx + g + bead, ry + g + bead
    outer = (rx + g + 2 * bead + 3.5, ry + g + 2 * bead + 3.5)
    o.append(f'<path d="{_ell_d(cx, cy, outer[0], outer[1])}{_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + g - .25, ry + g - .25)}" fill="none" stroke="#000" stroke-width=".5"/>')
    per = _C._ell_pts(cx, cy, a1, b1, 180)[:-1]
    o.append(kk_beads(_along(per, bead * 2 + 1.1), bead))
    o.append(f'<path d="{_ell_d(cx, cy, a1 + bead + 1, b1 + bead + 1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_ell_d(cx, cy, outer[0] - .5, outer[1] - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), _ell_d(cx, cy, rx + .5, ry + .5), outer[0], outer[1]


def kk_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
# ---- a leaner emitter: half-px path units, coarser simplification --------------------------

def _pd(pen):
    o = pen.o
    out = []
    prev_m = False
    for t in o:
        if t[0] == "l" and prev_m:
            t = t[1:]
            out.append(t if t[0] == "-" else " " + t)
        else:
            out.append(t)
        prev_m = t[0] == "m"
    return "".join(out)


def _zig(lines):
    """Join a sweep of hatch segments into boustrophedon polylines (the joins run along the
    region's edges, where an outline or vein is drawn anyway): about half the path data."""
    out = []
    cur = None
    flip = False
    last_v = None
    for a, b in lines:
        if flip:
            a, b = b, a
        if cur is not None and _m.hypot(a[0] - cur[-1][0], a[1] - cur[-1][1]) < 3.2:
            cur += [a, b]
        else:
            if cur:
                out.append(cur)
            cur = [a, b]
        flip = not flip
    if cur:
        out.append(cur)
    return out


def kk_svg(cv, q=2, tol_fill=.55, tol_line=.42):
    """Canvas.svg with path data in 1/q px (q=2: one device pixel) and slightly coarser
    simplification: the same occlusion, about 30 % fewer bytes."""
    if not cv.objs:
        return ""
    xs = [p[0] for o in cv.objs for poly in o[0] for p in poly] or [0.]
    ys = [p[1] for o in cv.objs for poly in o[0] for p in poly] or [0.]
    x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
    W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
    mask = [bytearray(W) for _ in range(H)]
    out = {.5: [], 1.: [], 1.5: []}
    for polys, ow, strokes in reversed(cv.objs):
        for w, lines in strokes.items():
            for pl in lines:
                _C._clip_runs(pl, mask, x0, y0, W, H, out[w])
        if ow:
            for poly in polys:
                _C._clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
        for poly in polys:
            _C._fill_mask(poly, mask, x0, y0, W, H)
    oq = _C._Q
    _C._Q = q
    try:
        T = f' transform="scale({_kn(1. / q) if q != 2 else ".5"})"'
        res = []
        pen = _C._Pen()
        for polys, _, _ in cv.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path{T} d="{_pd(pen)}" fill="#fff" stroke="none"/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _C._Pen()
                for pl in out[w]:
                    pen.add(pl, False, tol_line if w < 1 else tol_line + .05)
                res.append(f'<path{T} d="{_pd(pen)}" fill="none" stroke="#000" stroke-width="{_kn(w * q)}"/>')
    finally:
        _C._Q = oq
    return "".join(res)


# ---- shaped panels, offsets, bead rows ------------------------------------------------------

def kk_shape(kind, x, y, w, h, c=20.):
    """A panel outline (clockwise on screen): 'rect', 'cut' (cut corners c), 'arch' (an
    elliptical arch of rise c on a rectangle), 'oval'."""
    if kind == "cut":
        return [(x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c), (x + w - c, y + h),
                (x + c, y + h), (x, y + h - c), (x, y + c)]
    if kind == "arch":
        n = 28
        top = [(x + w / 2 - w / 2 * _m.cos(_PI * i / n), y + c - c * _m.sin(_PI * i / n)) for i in range(n + 1)]
        return top + [(x + w, y + h), (x, y + h)]
    if kind == "oval":
        return _C._ell_pts(x + w / 2, y + h / 2, w / 2, h / 2, 72)[:-1]
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def kk_offset(poly, d):
    """Offset a convex clockwise-on-screen polygon outward by d (inward if d < 0), mitred."""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1])
        e2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = _m.hypot(*e1) or 1.
        l2 = _m.hypot(*e2) or 1.
        n1 = (e1[1] / l1, -e1[0] / l1)            # outward for clockwise-on-screen
        n2 = (e2[1] / l2, -e2[0] / l2)
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        bl = _m.hypot(bx, by) or 1.
        cs = max(.35, (bx * n1[0] + by * n1[1]) / bl)
        out.append((p1[0] + bx / bl * d / cs, p1[1] + by / bl * d / cs))
    return out


class kk_inside:
    """Point-in-polygon test with the crossings of each scan row cached."""

    def __init__(self, poly):
        self.p = poly
        self.rows = {}

    def __call__(self, px, py):
        xs = self.rows.get(py)
        if xs is None:
            xs = []
            P = self.p
            n = len(P)
            for i in range(n):
                (ax, ay), (bx, by) = P[i], P[(i + 1) % n]
                if (ay > py) != (by > py):
                    xs.append(ax + (bx - ax) * (py - ay) / (by - ay))
            xs.sort()
            self.rows[py] = xs
        k = 0
        for x in xs:
            if x > px:
                break
            k += 1
        return k % 2 == 1


def _pd_poly(poly, close=True):
    return _C._d(poly, close, .1)


def kk_bead_row(d, r=1.5, closed=True):
    """A row of beads along any path d: a black channel, white beads with round caps on a dash
    pattern, and a black speck in each bead's shadow. 3 elements, whatever the length."""
    p = r * 2 + 1.
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_kn(2 * r + 2)}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_kn(2 * r)}" stroke-dasharray="0 {_kn(p)}" stroke-linecap="round"/>'
            f'<path d="{d}" transform="translate(.5,.5)" fill="none" stroke="#000" stroke-width="1" stroke-dasharray="0 {_kn(p)}" stroke-linecap="round"/>')


def kk_border(poly, bead=1.5):
    """Gold-line border round a panel whose clockwise outline is poly: from the panel out, a 1 px
    rule, a bright gap, a fine rule, a bead row, a 1 px rule. Returns (svg, total width)."""
    o = []
    g1 = kk_offset(poly, .5)
    g2 = kk_offset(poly, 2.75)
    gb = kk_offset(poly, 4. + bead)
    ge = kk_offset(poly, 5.5 + 2 * bead)
    o.append(f'<path d="{_pd_poly(ge)}{_pd_poly(poly[::-1])}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_pd_poly(g1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_pd_poly(g2)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_pd_poly(gb), bead))
    o.append(f'<path d="{_pd_poly(ge)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), 5.5 + 2 * bead + .5


def kk_ring(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval: a 1.5 rule, a gold gap, a fine rule, a bead ring, a rule.
    Returns (svg, outer rx, outer ry)."""
    o = []
    e = 5.5 + 2 * bead
    o.append(f'<path d="{_ell_d(cx, cy, rx + e, ry + e)}{_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_ell_d(cx, cy, rx + 2.75, ry + 2.75)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_ell_d(cx, cy, rx + 4 + bead, ry + 4 + bead), bead))
    o.append(f'<path d="{_ell_d(cx, cy, rx + e - .5, ry + e - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), rx + e, ry + e


# ---- Easter eggs: small figures cut white out of the matte --------------------------------

def _U(cx, cy, r, pts):
    return [(cx + px * r, cy + py * r) for px, py in pts]


def _cut(cv, poly, ang=45., pitch=1.5):
    cv.hair(_zig(_C.hatch_poly(poly, ang, pitch)))


def _wline(cv, pts, hw):
    """A white line hw px each side of pts, cut out of the matte."""
    pts = _resample(pts, 1.5) if len(pts) > 1 else pts
    if len(pts) < 2:
        return
    R = _C._Rib(pts, [hw] * len(pts), [hw] * len(pts))
    cv.obj([R.outline()], 0)


def kk_egg(kind, cx, cy, r):
    """A small engraved figure filling a disc of radius r (white relief, fine shadow cuts)."""
    cv = _C.Canvas()
    E = lambda pts: _U(cx, cy, r, pts)
    if kind == "drumsticks" or kind == "arms":
        if kind == "arms":
            # a sun behind: a disc and rays
            rays = []
            for i in range(16):
                a = i * _TAU / 16
                r0, r1 = .42, (.92 if i % 2 == 0 else .72)
                rays.append(E([(r0 * _m.cos(a - .08), r0 * _m.sin(a - .08)), (r1 * _m.cos(a), r1 * _m.sin(a)),
                               (r0 * _m.cos(a + .08), r0 * _m.sin(a + .08))]))
            cv.obj(rays, .5)
            for p in rays[::2]:
                cv.hair([p[1], ((p[0][0] + p[2][0]) / 2, (p[0][1] + p[2][1]) / 2)])
            disc = _C._ell_pts(cx, cy, r * .4, r * .4, 28)[:-1]
            cv.obj([disc], 1.)
            cv.hair(_C._ell_pts(cx, cy, r * .3, r * .3, 22))
            cut = [p for p in disc if p[0] - cx + p[1] - cy > -r * .1]
            _cut(cv, _C._ell_pts(cx + r * .08, cy + r * .08, r * .3, r * .3, 18)[:-1], -45, 1.5)
        for sg in (-1, 1):
            a = _m.radians(45 if sg > 0 else 135)
            ux, uy = _m.cos(a), _m.sin(a)
            vx, vy = -uy, ux
            L0, L1 = -.95, .95
            tw = lambda t: .035 + .06 * (t - L0) / (L1 - L0)
            pts = [(cx + r * (t * ux + tw(t) * vx), cy + r * (t * uy + tw(t) * vy)) for t in (L0, 0, L1)]
            pts += [(cx + r * (t * ux - tw(t) * vx), cy + r * (t * uy - tw(t) * vy)) for t in (L1, 0, L0)]
            cv.obj([pts], .5)
            cv.hair([(cx + r * (t * ux - tw(t) * .4 * vx), cy + r * (t * uy - tw(t) * .4 * vy)) for t in (L0 + .1, L1 - .1)])
            tip = (cx + r * L0 * ux, cy + r * L0 * uy)
            cv.obj([_C._ell_pts(tip[0], tip[1], r * .07, r * .07, 10)[:-1]], .5)
    elif kind == "cymbal":
        e = _C._ell_pts(cx, cy - r * .2, r * .9, r * .28, 40)[:-1]
        cv.obj([E([(-.05, .05), (.05, .05), (.05, .95), (-.05, .95)])], .5)
        cv.obj([e], .5)
        for k in (.25, .45, .65, .85):
            cv.hair(_C._ell_pts(cx, cy - r * .2, r * .9 * k, r * .28 * k, 28, 0, _PI))
        _cut(cv, [p for p in e if p[1] > cy - r * .2], 60, 1.5)
        cv.obj([_C._ell_pts(cx, cy - r * .25, r * .14, r * .07, 12)[:-1]], .5)
    elif kind == "note":
        for dx in (-.42, .38):
            cv.obj([_C._ell_pts(cx + dx * r - r * .05, cy + r * .5, r * .24, r * .16, 16)[:-1]], 1.)
            cv.line(_C.hatch_poly(_C._ell_pts(cx + dx * r - r * .05, cy + r * .5, r * .2, r * .12, 14)[:-1], 0, 1.))
            cv.obj([E([(dx + .15, .5), (dx + .2, .5), (dx + .2, -.6), (dx + .15, -.6)])], .5)
        cv.obj([E([(-.27, -.62), (.58, -.72), (.58, -.5), (-.27, -.4)])], .5)
        cv.line(_C.hatch_poly(E([(-.27, -.62), (.58, -.72), (.58, -.5), (-.27, -.4)]), 0, 1.))
    elif kind == "P":
        stem = E([(-.45, -.8), (-.12, -.8), (-.12, .8), (-.45, .8)])
        bowl = [(cx - r * .14 + r * .5 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .42 * _m.sin(t))
                for t in [(-_PI / 2) + _PI * i / 20 for i in range(21)]]
        inner = [(cx - r * .14 + r * .28 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .2 * _m.sin(t))
                 for t in [(-_PI / 2) + _PI * i / 16 for i in range(17)]]
        cv.obj([bowl + inner[::-1]], 1.)
        _cut(cv, bowl + inner[::-1], -45, 1.5)
        cv.obj([stem], 1.)
        _cut(cv, E([(-.25, -.8), (-.12, -.8), (-.12, .8), (-.25, .8)]), 90, 1.5)
        cv.obj([E([(-.62, .62), (.05, .62), (.05, .8), (-.62, .8)]), E([(-.62, -.8), (-.05, -.8), (-.05, -.66), (-.62, -.66)])], .5)
    elif kind == "bridge":
        for tx in (-.45, .45):
            cv.obj([E([(tx - .09, .85), (tx - .05, -.75), (tx, -.92), (tx + .05, -.75), (tx + .09, .85)])], .5)
            cv.hair([(cx + (tx + .03) * r, cy - r * .7), (cx + (tx + .05) * r, cy + r * .8)])
            cv.hair(E([(tx - .05, -.35), (tx + .05, -.35)]))
        deck = E([(-1, .3), (1, .3), (1, .4), (-1, .4)])
        cv.obj([deck], .5)
        main = [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)) for t in [-.45 + .9 * i / 20 for i in range(21)]]
        _wline(cv, main, .7)
        for sg in (-1, 1):
            _wline(cv, [(cx + sg * r * (.45 + .53 * k / 8), cy - r * .72 + r * 1.02 * (k / 8) ** 1.6) for k in range(9)], .7)
        for k in range(1, 9):
            t = -.45 + .9 * k / 9
            _wline(cv, [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)), (cx + r * t, cy + r * .3)], .5)
    elif kind == "hood":
        m = E([(-1, .7), (-.55, .1), (-.2, -.55), (0, -.8), (.15, -.62), (.5, -.05), (1, .7)])
        cv.obj([m], .5)
        _cut(cv, E([(0, -.8), (.15, -.62), (.5, -.05), (1, .7), (.1, .7)]), -60, 1.5)
        snow = E([(-.35, -.3), (-.2, -.55), (0, -.8), (.15, -.62), (.3, -.35), (.15, -.42), (.02, -.25), (-.12, -.4)])
        cv.obj([snow], .5)
        for k in range(5):
            t = -.3 + k * .15
            cv.hair(E([(0, -.75), (t * .6, -.35)]))
    elif kind == "heron":
        # a great blue heron standing in the shallows, facing left: S-curved neck, dagger bill,
        # a plume off the crown, long legs, the back feathers cut in fine lines
        body = E([(-.25, -.05), (.05, -.22), (.4, -.18), (.62, .02), (.72, .22), (.45, .18), (.1, .2), (-.18, .12)])
        cv.obj([body], .5)
        _cut(cv, E([(.05, -.05), (.4, -.1), (.62, .02), (.72, .22), (.45, .18), (.1, .2)]), 20, 1.5)
        _wline(cv, E([(-.12, -.08), (-.3, -.3), (-.22, -.5), (-.08, -.62), (-.2, -.78)]), r * .05)
        cv.obj([E([(-.28, -.84), (-.12, -.8), (-.1, -.74), (-.24, -.72)])], .5)
        _wline(cv, E([(-.25, -.79), (-.72, -.72)]), r * .03)
        _wline(cv, E([(-.12, -.83), (.12, -.88)]), r * .015)
        _wline(cv, E([(.15, .18), (.1, .55), (.12, .9)]), r * .025)
        _wline(cv, E([(.3, .18), (.32, .55), (.4, .9)]), r * .025)
        for k in range(5):
            _wline(cv, E([(-.85 + k * .1, .93 + (k % 2) * .03), (-.55 + k * .3, .93)]), .5)
    elif kind == "kranok":
        # a Thai kranok flame: a tall leaf rising, its back serrated into flame tongues, the tip
        # hooking over, a smaller flame nested inside it and a curl at its foot
        _leaf(cv, cx - r * .25, cy + r * .9, -_PI / 2 + .25, r * 1.85, r * .5, -1, 4, 3)
        _leaf(cv, cx - r * .1, cy + r * .7, -_PI / 2 + .35, r * 1.1, r * .3, -1, 2, 5)
        _wline(cv, [(cx - r * .25 + r * .4 * _m.cos(t), cy + r * .62 + r * .3 * _m.sin(t)) for t in [_PI * (.1 + 1.4 * k / 12) for k in range(13)]], .6)
    elif kind == "elephant":
        b = E([(-.75, .1), (-.6, -.35), (-.1, -.5), (.3, -.45), (.55, -.6), (.8, -.4), (.85, 0), (.78, .4),
               (.7, .65), (.62, .3), (.55, .15), (.45, .7), (.3, .7), (.28, .25), (-.35, .25), (-.38, .7),
               (-.55, .7), (-.58, .2)])
        cv.obj([b], .5)
        _cut(cv, E([(-.75, .1), (-.35, .25), (.28, .25), (.55, .15), (.5, -.1), (-.6, -.1)]), 20, 1.5)
        cv.hair(E([(.35, -.4), (.42, -.05), (.25, .05)]))
        cv.obj([E([(-.3, -.48), (.1, -.48), (.05, -.1), (-.25, -.1)])], .5)
        for k in range(4):
            cv.hair(E([(-.27 + k * .1, -.45), (-.25 + k * .1, -.13)]))
    elif kind == "panel":
        fr = E([(-.85, -.2), (.55, -.75), (.85, .2), (-.55, .75)])
        cv.obj([fr], 1.)
        _cut(cv, fr, -22, 1.5)
        for k in (1, 2, 3):
            t = k / 4
            a = (-.85 + 1.4 * t, -.2 - .55 * t)
            b = (-.55 + 1.4 * t, .75 - .55 * t)
            cv.line(E([a, b]))
        cv.line(E([(-.7, .275), (.7, -.275)]))
        cv.line(E([(0, .4), (0, .95)]))
    elif kind == "pinwheel":
        for i in range(5):
            a0 = i * _TAU / 5
            arm = [(cx + r * .92 * t * _m.cos(a0 + 1.4 * t), cy + r * .92 * t * _m.sin(a0 + 1.4 * t)) for t in [k / 12 for k in range(13)]]
            arm2 = [(cx + r * .92 * t * _m.cos(a0 + .5 + 1.4 * t), cy + r * .92 * t * _m.sin(a0 + .5 + 1.4 * t)) for t in [k / 12 for k in range(12, -1, -1)]]
            poly = arm + arm2
            cv.obj([poly], .5)
            if i % 2 == 0:
                _cut(cv, poly, a0 * 57 + 30, 1.5)
    elif kind == "paw":
        cv.obj([_C._ell_pts(cx, cy + r * .3, r * .38, r * .32, 20)[:-1]], .5)
        _cut(cv, _C._ell_pts(cx + r * .05, cy + r * .35, r * .3, r * .24, 16)[:-1], -45, 1.5)
        for a in (-2.4, -1.85, -1.3, -.75):
            px, py = cx + r * .62 * _m.cos(a), cy + r * .1 + r * .62 * _m.sin(a)
            cv.obj([_C._ell_pts(px, py, r * .15, r * .19, 12)[:-1]], .5)
    elif kind == "fleur":
        mid = E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4), (-.1, .25), (-.22, -.2), (-.2, -.62)])
        cv.obj([mid], .5)
        _cut(cv, E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4)]), 70, 1.5)
        cv.hair(E([(0, -.85), (0, .3)]))
        for sg in (-1, 1):
            pet = E([(sg * .12, .2), (sg * .45, -.25), (sg * .8, -.42), (sg * .95, -.2), (sg * .78, -.05),
                     (sg * .62, -.18), (sg * .45, .05), (sg * .3, .38)])
            cv.obj([pet], .5)
            _cut(cv, pet, -sg * 50, 1.5)
            cv.obj([_C._ell_pts(cx + sg * r * .82, cy - r * .28, r * .1, r * .1, 10)[:-1]], .5)
        band = E([(-.42, .32), (.42, .32), (.42, .5), (-.42, .5)])
        cv.obj([band], .5)
        _cut(cv, band, 90, 1.5)
        cv.obj([E([(-.15, .5), (.15, .5), (.1, .95), (0, .82), (-.1, .95)])], .5)
    else:   # "dog": a retriever's head in profile, looking left
        head = E([(.55, .9), (.35, .25), (.1, .05), (-.15, .05), (-.55, .12), (-.82, .05), (-.88, -.12),
                  (-.7, -.22), (-.35, -.3), (-.1, -.55), (.2, -.62), (.45, -.5), (.62, -.2), (.75, .35), (.9, .9)])
        cv.obj([head], .5)
        _cut(cv, E([(.35, .25), (.62, -.2), (.75, .35), (.9, .9), (.55, .9)]), 75, 1.5)
        ear = E([(.15, -.55), (.42, -.48), (.5, -.1), (.42, .35), (.3, .4), (.22, .0)])
        cv.obj([ear], .5)
        _cut(cv, ear, 80, 1.5)
        cv.obj([_C._ell_pts(cx - r * .86, cy - r * .1, r * .07, r * .07, 8)[:-1]], 1.)
        cv.line(_C._ell_pts(cx - r * .12, cy - r * .3, r * .05, r * .05, 8))
        cv.hair(E([(-.82, .05), (-.5, .1)]))
    return cv.svg()


def kk_roundel(cx, cy, r, kind, bead=1.2):
    """An egg in a small bead-ringed roundel on the matte."""
    ring, ox, oy = kk_ring(cx, cy, r, r, bead)
    return (f'<path d="{_ell_d(cx, cy, r + .5, r + .5, 40)}" fill="url(#kkM)" stroke="none"/>'
            + kk_egg(kind, cx, cy, r * .86) + ring), ox


# ---- skies: burin lines that darken upward, broken by modelled cloud banks --------------------

def kk_cloud(cv, x0, x1, yb, hgt, rng):
    """A cumulus bank: a white heaped top, dark rounded underside cut in lines that follow it."""
    n = max(3, int((x1 - x0) / (hgt * .8)))
    bumps = []
    for i in range(n):
        t = (i + .5) / n
        r = hgt * (.35 + .55 * _m.sin(_PI * t) ** .7) * rng.uniform(.8, 1.1)
        bumps.append((x0 + (x1 - x0) * t, yb - r * .7, r))
    top = []
    N = int((x1 - x0) / 1.5) + 2
    for k in range(N + 1):
        x = x0 + (x1 - x0) * k / N
        y = yb
        for bx, by, br in bumps:
            dx = x - bx
            if abs(dx) < br:
                y = min(y, by - _m.sqrt(br * br - dx * dx))
        top.append((x, min(y, yb - .5)))
    bot = [(x1 - (x1 - x0) * k / 16, yb + hgt * .08 * _m.sin(_PI * k / 16)) for k in range(17)]
    cv.obj([top + bot], .5)
    # undersides: lines following the base, stacked up into the cloud, dense low and fading
    for j, d in enumerate([1., 2.5, 4., 5.5, 7.5, 10., 13.]):
        if d > hgt * .9:
            break
        cv.line([(x, max(y, yb - d)) for (x, y) in top if y < yb - d]) if j < 2 else cv.hair(
            [(x, max(y + d * .25, yb - d)) for (x, y) in top if y < yb - d - 1])
    # the heaped tops: a contour inside each bump on its shadow side
    for bx, by, br in bumps:
        if br > 4:
            cv.hair([(bx + br * .85 * _m.cos(a), by + br * .85 * _m.sin(a)) for a in [_PI * (.1 + .6 * i / 10) for i in range(11)]])


def kk_sky(cv, X, Y, W, yb, seed=0, clouds=2):
    """Sky from Y down to the horizon yb: 1 px rules at a 2 px pitch high up (dark), thinning to
    0.5 px at 2 then 3 px toward the horizon (light), with tapered 1 px bulino streaks swelling
    out of the mid sky, and cloud banks laid over it. Lines on the device grid (k/2 + 1/4)."""
    rng = _r.Random(seed * 17 + 3)
    cv.obj([[(X, Y), (X + W, Y), (X + W, yb), (X, yb)]], 0)
    H = yb - Y
    y = _m.floor(Y * 2) / 2 + .25
    while y < yb:
        f = (y - Y) / max(1., H)
        if f < .22:
            cv.line([(X, y + .25), (X + W, y + .25)])
            y += 2.
            continue
        cv.hair([(X, y), (X + W, y)])
        if f < .6 and rng.random() < .55:
            x = X + rng.uniform(-.2, 1.) * W
            L = rng.uniform(.15, .45) * W * (.6 - f) / .38
            cv.line([(x, y + .25), (x + L, y + .25)])
        y += 1.5 if f < .5 else (2. if f < .78 else 3.)
    for k in range(clouds):
        cw = W * rng.uniform(.28, .42)
        x0 = X + W * (.05 + .62 * (k / max(1, clouds - 1) if clouds > 1 else .3)) + rng.uniform(-8, 8)
        cb = Y + H * rng.uniform(.38, .62)
        kk_cloud(cv, x0, x0 + cw, cb, min(H * .2, cw * .25), rng)


# ---- the plate ------------------------------------------------------------------------------

def kk_plate(w, h, scene, egg="dog", seed=0, arms=False, egg2=None, dens=1., limit=188000):
    """The whole plate, edge to edge, by height:
      h < 110   band: a bead row and gold line hang under the text; the matte carries fine scroll
                flowing out both ways from an oval medallion (the scene); an egg roundel.
      110-260   a cut-cornered panel in a gold-line, beaded border; spandrels of scroll and
                rosettes outside it; the medallion at the centre, scroll flowing from its foot.
      > 260     an arched panel: a great oval copperplate scene; under it a roundel (the arms
                placeholder on fronts, else the egg); spandrels; a bordered frieze at the foot
                with scroll flowing both ways from a palmette.
    scene(x, y, w, h, mode) -> svg filling that rect (it is clipped to the oval)."""
    rng = _r.Random(seed)
    o = [kk_defs()]
    field = _C.Canvas()

    deferred = []

    def run_field(box, obst, roots, rmin, rmax, inside=None, poly=None, sd=0, area=None, cut=None):
        d = (_pd_poly(poly) if poly else _rect_d(*box)) + (_pd_poly(cut) if cut else "")
        o.append(kk_matte(d))
        if area is not None:
            deferred.append((len(o), box, obst, roots, rmin, rmax, inside, d, sd, area))
            o.append("")
            return
        cv = _C.Canvas()
        kk_field(cv, box, obst, roots, seed * 7 + sd, rmin * dens, rmax * dens, inside=inside)
        o.append(kk_clip(_C._uid("kkf", w, h, seed, sd), d, kk_svg(cv)))

    def finish():
        """The main field is grown last, its scroll size set so the plate lands under budget
        (field bytes ~ 19 * area / rmin^1.2, measured)."""
        for (k, box, obst, roots, rmin, rmax, inside, d, sd, area) in deferred:
            used = sum(len(t) for t in o) + 1800
            room = max(30000., limit - used)
            need = (20. * area / room) ** (1 / 1.2)
            f = max(dens, need / rmin)
            for tries in range(3):
                cv = _C.Canvas()
                kk_field(cv, box, obst, roots, seed * 7 + sd, rmin * f, rmax * f, inside=inside)
                o[k] = kk_clip(_C._uid("kkf", w, h, seed, sd), d, kk_svg(cv))
                over = used + len(o[k]) - limit - 6000
                if over <= 0:
                    break
                f *= (1 + over / len(o[k])) ** .85
        return _C.svg_doc(w, h, "".join(o))

    if h < 110:
        top = 8.
        gy, gh = top, h - top - 3
        cx, cy = w / 2, gy + gh / 2
        ry = gh / 2 - 7.5
        rx = min(w * .17, max(ry * 2.2, 26))
        obst = [("e", cx, cy, rx + 9, ry + 9)]
        er = min(gh / 2 - 7, 17)
        ex = w * (.13 if seed % 2 else .87)
        obst.append(("c", ex, cy, er + 7))
        run_field((0, gy, w, gh), obst, [(cx - rx - 8, cy, 180), (cx + rx + 8, cy, 0)],
                  max(4.5, gh * .1), max(9, gh * .33), sd=1, area=w * gh - _PI * (rx + 9) * (ry + 9) - _PI * (er + 7) ** 2)
        o.append(kk_clip(_C._uid("kks", w, h, seed), _ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "band")))
        ring, _, _ = kk_ring(cx, cy, rx, ry, 1.)
        o.append(ring)
        rr, _ = kk_roundel(ex, cy, er, egg, 1.)
        o.append(rr)
        o.append(f'<path d="M0,1.5H{_kn(w)}M0,{_kn(top - .5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(kk_bead_row(f"M0,{_kn(top / 2 + .25)}H{_kn(w)}", 1., False))
        o.append(f'<path d="M0,{_kn(h - 1.5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(f'<path d="M0,{_kn(h - 2.75)}H{_kn(w)}" stroke="#000" stroke-width=".5"{_C._CR}/>')
        return finish()

    if h <= 260:
        m = 10.
        c = min(30., h * .17)
        poly = kk_shape("cut", m, m, w - 2 * m, h - 2 * m, c)
        # the spandrels and margins: matte with small scroll
        outer = kk_inside(kk_offset(poly, 9.))
        run_field((0, 0, w, h), [], [(0, 0, 45), (w, 0, 135), (w, h, -135), (0, h, -45)], 4.5, 10.,
                  lambda px, py: not outer(px, py), sd=2, cut=kk_offset(poly, 4.))
        cx, cy = w / 2, h / 2
        ry = (h - 2 * m) / 2 - 12
        rx = min(w * .2, ry * 1.25)
        er = min(15., h * .1)
        ex = cx + (rx + 30 + er) * (-1 if seed % 2 else 1)
        obst = [("e", cx, cy, rx + 10, ry + 10), ("c", ex, cy, er + 8)]
        border, bw = kk_border(poly)
        for q in _along(poly, 3.):
            obst.append(("c", q[0], q[1], 3.))
        run_field((m, m, w - 2 * m, h - 2 * m), obst,
                  [(cx - rx * .55, cy + ry + 8, 160), (cx + rx * .55, cy + ry + 8, 20), (cx, cy - ry - 9, 0 if seed % 2 else 180)],
                  max(6, h * .045), max(13, h * .14), kk_inside(poly), poly, 3,
                  area=(w - 2 * m) * (h - 2 * m) - 2 * c * c - _PI * (rx + 10) * (ry + 10) - _PI * (er + 8) ** 2)
        o.append(border)
        for p in (poly[0], poly[2], poly[4], poly[6]):
            pass
        for (qx, qy) in ((m * .6 + c * .3, m * .6 + c * .3), (w - m * .6 - c * .3, m * .6 + c * .3),
                         (w - m * .6 - c * .3, h - m * .6 - c * .3), (m * .6 + c * .3, h - m * .6 - c * .3)):
            o.append(kk_rosette(qx, qy, 3.6))
        o.append(kk_clip(_C._uid("kks", w, h, seed), _ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "medium")))
        ring, _, _ = kk_ring(cx, cy, rx, ry, 1.5)
        o.append(ring)
        rr, _ = kk_roundel(ex, cy, er, egg, 1.)
        o.append(rr)
        return finish()

    # tall
    m = 10.
    fh = min(max(h * .12, 34), 60)
    yb = h - fh - 12
    rise = min(70., (yb - m) * .16)
    poly = kk_shape("arch", m, m, w - 2 * m, yb - m, rise)
    outer = kk_inside(kk_offset(poly, 9.))
    run_field((0, 0, w, yb + 6), [], [(0, 0, 45), (w, 0, 135)], 10., 22.,
              lambda px, py: not outer(px, py) and py < m + rise + 4, sd=4, cut=kk_offset(poly, 4.))
    border, bw = kk_border(poly)
    cx = w / 2
    ph = yb - m
    rr_ = min(24., ph * .07)
    ry = min(ph * .4, 175, (ph - rise * .5 - 18 - 2 * rr_ - 44) / 2)
    rx = min((w - 2 * m) * .4, ry * 1.12)
    cy = m + rise * .5 + ry + 18
    ey = min(cy + ry + 14 + rr_ + 6, yb - rr_ - 10)
    obst = [("e", cx, cy, rx + 10, ry + 10), ("c", cx, ey, rr_ + 10)]
    for q in _along(poly, 3.):
        obst.append(("c", q[0], q[1], 3.))
    roots = [(cx - rr_ - 10, ey, 180), (cx + rr_ + 10, ey, 0), (cx, cy - ry - 10, 0 if seed % 2 else 180)]
    run_field((m, m, w - 2 * m, ph), obst, roots, max(9, h * .019), max(19, h * .048), kk_inside(poly), poly, 5,
              area=(w - 2 * m) * ph - _PI * (rx + 10) * (ry + 10) - _PI * (rr_ + 10) ** 2 - .43 * rise * (w - 2 * m))
    o.append(border)
    o.append(kk_clip(_C._uid("kks", w, h, seed), _ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "tall")))
    ring, _, _ = kk_ring(cx, cy, rx, ry, 1.5)
    o.append(ring)
    rr, _ = kk_roundel(cx, ey, rr_, "arms" if arms else egg, 1.2)
    o.append(rr)
    # the frieze
    fy = yb + 8
    fp = kk_shape("rect", m + 6, fy + 4, w - 2 * m - 12, h - fy - 8)
    fb, _ = kk_border(fp, 1.2)
    pr = (h - fy - 8) / 2 - 1
    pcx, pcy = w / 2, fy + 4 + (h - fy - 8) / 2
    o.append(kk_matte(_rect_d(0, yb + 4, w, h - yb - 4)))
    run_field((m + 6, fy + 4, w - 2 * m - 12, h - fy - 8), [("c", pcx, pcy, pr * 1.05)] + ([("c", w * .2, pcy, pr * .8)] if egg2 else []),
              [(pcx - pr, pcy, 180), (pcx + pr, pcy, 0)], max(5.5, pr * .42), pr * 1.05, sd=7)
    o.append(fb)
    o.append(kk_egg(egg2 or "fleur", pcx, pcy, pr * .95))
    return finish()


# ---- the plate ------------------------------------------------------------------------------

def plate(w, h, ctx):
    """What is blooming: common selfheal and common sneezeweed, a bee, the cottonwoods and Mt.
    Hood, in the inlaid medallion; a dog's paw print in the garden soil and a Sauvie Island
    heron roundel in the scroll (the Easter eggs)."""
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)

    def sc(x, y, ww, hh, mode):
        X, Y, W, H = x - 2, y - 2, ww + 4, hh + 4
        return garden(X, Y, W, H, seed, _rect_d(X, Y, W, H), "compact" if mode == "band" else "full")
    return kk_plate(w, h, sc, egg="heron", seed=seed)
