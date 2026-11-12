"""garden-05 "What is blooming" -- merged into Walk the land (edition plan, Garden and wildlife).

The planned art is an oval vignette of about 18% of the sheet: the prairie edge of the land.
Tall prairie grass, a split-rail fence running off along the edge with a kestrel on a post,
the cottonwoods of the island and Mt. Hood behind, and the yard-debris brush pile, which smokes
only when the page says it is OK to burn. Sneezeweed and selfheal, the natives seen flowering
this month, stand in the near grass.
Easter egg: the kestrel on the fence post (from the page text), with a dog's paw print in the
bare earth by the brush pile.
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


def kk_rect_d(x, y, w, h):
    return f"M{_kn(x)},{_kn(y)}h{_kn(w)}v{_kn(h)}h{_kn(-w)}z"


def _kk_ell_d(cx, cy, rx, ry, n=72):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n)[:-1], True, .1)


def kk_beads(pts, r=1.5):
    """Beads (white, .5 outlined, a black shadow speck lower right) centred on pts. 2 elements."""
    rr = _kn(r)
    a = "".join(f"M{_kn(x - r)},{_kn(y)}a{rr},{rr} 0 1,0 {_kn(2 * r)},0a{rr},{rr} 0 1,0 {_kn(-2 * r)},0z" for x, y in pts)
    s = max(.5, round(r * .7 * 2) / 2)
    b = "".join(f"M{_kn(x + r * .25)},{_kn(y + r * .2)}h{_kn(s)}v{_kn(s)}h{_kn(-s)}z" for x, y in pts)
    return (f'<path d="{a}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{b}" fill="#000" stroke="none"/>')


def _kk_along(poly, pitch, closed=True):
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

def _kk_leaf(cv, x, y, ang, L, W, c, teeth=2, seed=0):
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


class _KKSpiral:
    __slots__ = ("cx", "cy", "r", "w", "par", "kids", "pts", "S", "deg")

    def __init__(self, cx, cy, r):
        self.cx, self.cy, self.r = cx, cy, r
        self.w = 1
        self.par = None
        self.kids = []
        self.pts = None


def _kk_spiral_pts(cx, cy, R, th0, w, turns=1.45, end=.15):
    T = _TAU * turns
    b = -_m.log(end) / T
    n = max(24, int(R * T * .35))
    return [(cx + R * _m.exp(-b * T * i / n) * _m.cos(th0 + w * T * i / n),
             cy + R * _m.exp(-b * T * i / n) * _m.sin(th0 + w * T * i / n)) for i in range(n + 1)]


def _kk_bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _kk_resample(pts, step=1.5):
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
        s = _KKSpiral(px + rng.uniform(-.4, .4) * gx, py + rng.uniform(-.4, .4) * gy, r)
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
        rn = _KKSpiral(rx_, ry_, 0.)
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
        spi = _kk_spiral_pts(s.cx, s.cy, R, th0, s.w, rng.uniform(1.3, 1.6))
        S0 = spi[0]
        st = (spi[1][0] - S0[0], spi[1][1] - S0[1])
        sl = _m.hypot(*st) or 1.
        st = (st[0] / sl, st[1] / sl)
        L = _m.hypot(S0[0] - P0[0], S0[1] - P0[1])
        k = max(2., L * .42)
        stem = _kk_bez(P0, (P0[0] + t0[0] * k, P0[1] + t0[1] * k), (S0[0] - st[0] * k, S0[1] - st[1] * k), S0,
                    max(4, int(L / 2)))
        s.pts = _kk_resample(stem[:-1] + spi, 1.4)
        s.S = len(_kk_resample(stem[:-1], 1.4)) if len(stem) > 1 else 0
    # paint: twigs first, root last
    for s in order[::-1]:
        _kk_scroll(cv, s, rng, leafy)


def _kk_scroll(cv, s, rng, leafy):
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
        _kk_leaf(cv, b[0], b[1], tang(i) - ins * rng.uniform(.32, .5), ll, ll * .32, ins, 2 if ll > 6 else 1,
              rng.randrange(97))
    for (j, side) in st:
        b = Rb.at(j / (n - 1), side * .6)
        ll = min(9., s.r * .7) * rng.uniform(.8, 1.)
        if ll > 3:
            _kk_leaf(cv, b[0], b[1], tang(j) + side * .7, ll, ll * .3, -side, 1, rng.randrange(97))
    # the stem: a bright cut edge outside, a shadow line inside
    cv.obj([Rb.outline()], .5)
    if w0 > 1.2:
        cv.hair(Rb.contour(.3 * ins, 0., 1., minw=1.25))
    # one leaf rolling in toward the eye
    i = iS + int((n - iS) * .55)
    if i < n - 2 and s.r > 7:
        b = Rb.at(i / (n - 1), ins * .5)
        ll = s.r * .42
        _kk_leaf(cv, b[0], b[1], tang(i) + ins * .35, ll, ll * .28, ins, 1, rng.randrange(97))
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
    o.append(f'<path d="{kk_rect_d(x - 3, y - 3, w + 6, h + 6)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{kk_rect_d(x - 1.25, y - 1.25, w + 2.5, h + 2.5)}" fill="none" stroke="#000" stroke-width=".5"/>')
    # bead row in a white channel outside
    g = 3 + bead + 1.5
    o.append(f'<path d="{kk_rect_d(x - g - bead - 1.5, y - g - bead - 1.5, w + 2 * (g + bead + 1.5), h + 2 * (g + bead + 1.5))}'
             f'{kk_rect_d(x - 3.5, y - 3.5, w + 7, h + 7)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    pts = _kk_along([(x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)], bead * 2 + 1)
    o.append(kk_beads(pts, bead))
    e = g + bead + 1.5
    o.append(f'<path d="{kk_rect_d(x - e, y - e, w + 2 * e, h + 2 * e)}" fill="none" stroke="#000" stroke-width="1"/>')
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
    return (f'<path d="{_kk_ell_d(cx, cy, r + 1, r + 1, 24)}" fill="#000" stroke="none"/>'
            f'<path d="{d}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{_kk_ell_d(cx, cy, r * .28, r * .28, 10)}" fill="#fff" stroke="#000" stroke-width=".5"/>')


def kk_medallion(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval scene: a black fillet, a bead ring, a gold wire and a fine
    rule. Returns (svg_over, clip_d of the scene, outer rx, outer ry)."""
    o = []
    g = 2.5
    a1, b1 = rx + g + bead, ry + g + bead
    outer = (rx + g + 2 * bead + 3.5, ry + g + 2 * bead + 3.5)
    o.append(f'<path d="{_kk_ell_d(cx, cy, outer[0], outer[1])}{_kk_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + g - .25, ry + g - .25)}" fill="none" stroke="#000" stroke-width=".5"/>')
    per = _C._ell_pts(cx, cy, a1, b1, 180)[:-1]
    o.append(kk_beads(_kk_along(per, bead * 2 + 1.1), bead))
    o.append(f'<path d="{_kk_ell_d(cx, cy, a1 + bead + 1, b1 + bead + 1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, outer[0] - .5, outer[1] - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), _kk_ell_d(cx, cy, rx + .5, ry + .5), outer[0], outer[1]


def kk_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
# ---- a leaner emitter: half-px path units, coarser simplification --------------------------

def _kk_pd(pen):
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


def _kk_zig(lines):
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
            res.append(f'<path{T} d="{_kk_pd(pen)}" fill="#fff" stroke="none"/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _C._Pen()
                for pl in out[w]:
                    pen.add(pl, False, tol_line if w < 1 else tol_line + .05)
                res.append(f'<path{T} d="{_kk_pd(pen)}" fill="none" stroke="#000" stroke-width="{_kn(w * q)}"/>')
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


def _kk_pd_poly(poly, close=True):
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
    o.append(f'<path d="{_kk_pd_poly(ge)}{_kk_pd_poly(poly[::-1])}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_pd_poly(g1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_kk_pd_poly(g2)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_kk_pd_poly(gb), bead))
    o.append(f'<path d="{_kk_pd_poly(ge)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), 5.5 + 2 * bead + .5


def kk_ring(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval: a 1.5 rule, a gold gap, a fine rule, a bead ring, a rule.
    Returns (svg, outer rx, outer ry)."""
    o = []
    e = 5.5 + 2 * bead
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + e, ry + e)}{_kk_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + 2.75, ry + 2.75)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_kk_ell_d(cx, cy, rx + 4 + bead, ry + 4 + bead), bead))
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + e - .5, ry + e - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), rx + e, ry + e


# ---- Easter eggs: small figures cut white out of the matte --------------------------------

def _kk_U(cx, cy, r, pts):
    return [(cx + px * r, cy + py * r) for px, py in pts]


def _kk_cut(cv, poly, ang=45., pitch=1.5):
    cv.hair(_kk_zig(_C.hatch_poly(poly, ang, pitch)))


def _kk_wline(cv, pts, hw):
    """A white line hw px each side of pts, cut out of the matte."""
    pts = _kk_resample(pts, 1.5) if len(pts) > 1 else pts
    if len(pts) < 2:
        return
    R = _C._Rib(pts, [hw] * len(pts), [hw] * len(pts))
    cv.obj([R.outline()], 0)


def kk_egg(kind, cx, cy, r):
    """A small engraved figure filling a disc of radius r (white relief, fine shadow cuts)."""
    cv = _C.Canvas()
    E = lambda pts: _kk_U(cx, cy, r, pts)
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
            _kk_cut(cv, _C._ell_pts(cx + r * .08, cy + r * .08, r * .3, r * .3, 18)[:-1], -45, 1.5)
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
        _kk_cut(cv, [p for p in e if p[1] > cy - r * .2], 60, 1.5)
        cv.obj([_C._ell_pts(cx, cy - r * .25, r * .14, r * .07, 12)[:-1]], .5)
    elif kind == "castle":
        # the Somaster castle: two crenellated towers, a crenellated curtain wall between, an
        # arched gate with its portcullis
        def cren(x0, x1, ytop, yb, n):
            pts = [(x0, yb), (x0, ytop)]
            wd = (x1 - x0) / (2 * n - 1)
            for k in range(2 * n - 1):
                xa, xb = x0 + k * wd, x0 + (k + 1) * wd
                if k % 2 == 0:
                    pts += [(xa, ytop), (xb, ytop)]
                else:
                    pts += [(xa, ytop + .14), (xb, ytop + .14)]
            return pts + [(x1, ytop), (x1, yb)]
        wall = E(cren(-.5, .5, -.25, .8, 4))
        cv.obj([wall], .5)
        _kk_cut(cv, E([(.15, -.1), (.5, -.1), (.5, .8), (.15, .8)]), 90, 1.5)
        for tx in (-.78, .44):
            tw_ = E(cren(tx, tx + .34, -.85, .8, 2))
            cv.obj([tw_], .5)
            _kk_cut(cv, E([(tx + .2, -.7), (tx + .34, -.7), (tx + .34, .8), (tx + .2, .8)]), 90, 1.5)
            cv.obj([E([(tx + .13, -.5), (tx + .21, -.5), (tx + .21, -.3), (tx + .13, -.3)])], .5)
        gate = [(cx + r * .2 * _m.cos(t), cy + r * .32 + r * .26 * _m.sin(t)) for t in [_PI + _PI * k / 10 for k in range(11)]]
        gate = [(cx + r * .2, cy + r * .8)] + gate[::-1] + [(cx - r * .2, cy + r * .8)]
        cv.obj([gate], .5)
        for k in (-.1, 0, .1):
            cv.hair(E([(k, .1), (k, .8)]))
        for k in (.3, .48, .66):
            cv.hair(E([(-.19, k), (.19, k)]))
        for k in range(4):
            cv.hair(E([(-.48 + k * .03, .05 + k * .2), (.13, .05 + k * .2)]))
    elif kind == "drum":
        # a toddler's snare: a short cylinder, its rims and zigzag cords, two sticks crossed on it
        top = _C._ell_pts(cx, cy - r * .3, r * .72, r * .25, 32)[:-1]
        side = _C._ell_pts(cx, cy - r * .3, r * .72, r * .25, 16, 0, _PI) + _C._ell_pts(cx, cy + r * .45, r * .72, r * .25, 16, _PI, 0)
        cv.obj([side], .5)
        _kk_cut(cv, [p for p in side if p[0] > cx + r * .25], 90, 1.5)
        cv.obj([top], .5)
        cv.hair(_C._ell_pts(cx, cy - r * .3, r * .55, r * .17, 28))
        zz = [(cx + r * .72 * _m.cos(t), cy + (.45 if k % 2 else -.15) * r + r * .25 * _m.sin(t)) for k, t in enumerate([_PI * (1 - j / 8) for j in range(9)])]
        cv.line(zz)
        cv.line(_C._ell_pts(cx, cy + r * .45, r * .72, r * .25, 16, 0, _PI))
        for sg in (-1, 1):
            _kk_wline(cv, E([(sg * .1, -.45), (sg * .85, -.95)]), r * .05)
    elif kind == "cymbalP":
        e = _C._ell_pts(cx, cy - r * .2, r * .9, r * .32, 40)[:-1]
        cv.obj([E([(-.05, .05), (.05, .05), (.05, .95), (-.05, .95)])], .5)
        cv.obj([e], .5)
        for k in (.3, .55, .8):
            cv.hair(_C._ell_pts(cx, cy - r * .2, r * .9 * k, r * .32 * k, 28, 0, _PI))
        _kk_cut(cv, [p for p in e if p[1] > cy - r * .12], 60, 1.5)
        cv.obj([_C._ell_pts(cx, cy - r * .25, r * .12, r * .06, 12)[:-1]], .5)
        # the P engraved in the bow of the cymbal
        cv.line(E([(.42, -.05), (.42, -.4), (.6, -.4), (.66, -.32), (.6, -.24), (.42, -.24)]))
    elif kind == "note":
        # two swung eighth notes, beamed: white heads cut with a shadow crescent, white stems
        for dx, dy in ((-.45, .5), (.35, .38)):
            hd = _C._ell_pts(cx + dx * r, cy + dy * r, r * .26, r * .17, 18)[:-1]
            hd = [(cx + dx * r + (px - cx - dx * r) * .94 - (py - cy - dy * r) * .35, cy + dy * r + (py - cy - dy * r) + (px - cx - dx * r) * .25) for px, py in hd]
            cv.obj([hd], .5)
            _kk_cut(cv, [p for p in hd if p[1] > cy + dy * r - r * .02], 60, 1.5)
            _kk_wline(cv, E([(dx + .22, dy - .05), (dx + .22, -.62 - (dy - .5) * .3)]), r * .045)
        beam = E([(-.25, -.66), (.6, -.82), (.6, -.64), (-.25, -.48)])
        cv.obj([beam], .5)
        _kk_cut(cv, beam, -10, 1.5)
        for k in range(3):
            _kk_wline(cv, E([(-.85 + k * .55, .88), (-.6 + k * .55, .88)]), .5)
    elif kind == "P":
        stem = E([(-.45, -.8), (-.12, -.8), (-.12, .8), (-.45, .8)])
        bowl = [(cx - r * .14 + r * .5 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .42 * _m.sin(t))
                for t in [(-_PI / 2) + _PI * i / 20 for i in range(21)]]
        inner = [(cx - r * .14 + r * .28 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .2 * _m.sin(t))
                 for t in [(-_PI / 2) + _PI * i / 16 for i in range(17)]]
        cv.obj([bowl + inner[::-1]], 1.)
        _kk_cut(cv, bowl + inner[::-1], -45, 1.5)
        cv.obj([stem], 1.)
        _kk_cut(cv, E([(-.25, -.8), (-.12, -.8), (-.12, .8), (-.25, .8)]), 90, 1.5)
        cv.obj([E([(-.62, .62), (.05, .62), (.05, .8), (-.62, .8)]), E([(-.62, -.8), (-.05, -.8), (-.05, -.66), (-.62, -.66)])], .5)
    elif kind == "bridge":
        for tx in (-.45, .45):
            cv.obj([E([(tx - .09, .85), (tx - .05, -.75), (tx, -.92), (tx + .05, -.75), (tx + .09, .85)])], .5)
            cv.hair([(cx + (tx + .03) * r, cy - r * .7), (cx + (tx + .05) * r, cy + r * .8)])
            cv.hair(E([(tx - .05, -.35), (tx + .05, -.35)]))
        deck = E([(-1, .3), (1, .3), (1, .4), (-1, .4)])
        cv.obj([deck], .5)
        main = [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)) for t in [-.45 + .9 * i / 20 for i in range(21)]]
        _kk_wline(cv, main, .7)
        for sg in (-1, 1):
            _kk_wline(cv, [(cx + sg * r * (.45 + .53 * k / 8), cy - r * .72 + r * 1.02 * (k / 8) ** 1.6) for k in range(9)], .7)
        for k in range(1, 9):
            t = -.45 + .9 * k / 9
            _kk_wline(cv, [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)), (cx + r * t, cy + r * .3)], .5)
    elif kind == "hood":
        m = E([(-1, .7), (-.55, .1), (-.2, -.55), (0, -.8), (.15, -.62), (.5, -.05), (1, .7)])
        cv.obj([m], .5)
        _kk_cut(cv, E([(0, -.8), (.15, -.62), (.5, -.05), (1, .7), (.1, .7)]), -60, 1.5)
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
        _kk_cut(cv, E([(.05, -.05), (.4, -.1), (.62, .02), (.72, .22), (.45, .18), (.1, .2)]), 20, 1.5)
        _kk_wline(cv, E([(-.12, -.08), (-.3, -.3), (-.22, -.5), (-.08, -.62), (-.2, -.78)]), r * .05)
        cv.obj([E([(-.28, -.84), (-.12, -.8), (-.1, -.74), (-.24, -.72)])], .5)
        _kk_wline(cv, E([(-.25, -.79), (-.72, -.72)]), r * .03)
        _kk_wline(cv, E([(-.12, -.83), (.12, -.88)]), r * .015)
        _kk_wline(cv, E([(.15, .18), (.1, .55), (.12, .9)]), r * .025)
        _kk_wline(cv, E([(.3, .18), (.32, .55), (.4, .9)]), r * .025)
        for k in range(5):
            _kk_wline(cv, E([(-.85 + k * .1, .93 + (k % 2) * .03), (-.55 + k * .3, .93)]), .5)
    elif kind == "kranok":
        # a Thai kranok flame: a tall leaf rising, its back serrated into flame tongues, the tip
        # hooking over, a smaller flame nested inside it and a curl at its foot
        _kk_leaf(cv, cx - r * .25, cy + r * .9, -_PI / 2 + .25, r * 1.85, r * .5, -1, 4, 3)
        _kk_leaf(cv, cx - r * .1, cy + r * .7, -_PI / 2 + .35, r * 1.1, r * .3, -1, 2, 5)
        _kk_wline(cv, [(cx - r * .25 + r * .4 * _m.cos(t), cy + r * .62 + r * .3 * _m.sin(t)) for t in [_PI * (.1 + 1.4 * k / 12) for k in range(13)]], .6)
    elif kind == "elephant":
        # a caparisoned Lanna elephant walking left: domed head, ear, a trunk curling down and
        # out, a tusk, pillar legs, a patterned saddle cloth over the back
        for lx in (-.42, -.18, .3, .52):
            leg = E([(lx - .1, .15), (lx + .1, .15), (lx + .11, .82), (lx - .11, .82)])
            cv.obj([leg], .5)
            _kk_cut(cv, E([(lx + .02, .2), (lx + .1, .2), (lx + .11, .8), (lx + .02, .8)]), 90, 1.5)
        body = _C._ell_pts(cx + r * .08, cy - r * .02, r * .62, r * .4, 30)[:-1]
        cv.obj([body], .5)
        _kk_cut(cv, [p for p in body if p[1] > cy + r * .08], 10, 1.5)
        head = _C._ell_pts(cx - r * .55, cy - r * .2, r * .3, r * .32, 20)[:-1]
        cv.obj([head], .5)
        trunk = [(cx - r * (.75 + .12 * _m.sin(t * 2.2)), cy - r * .05 + r * .8 * t) for t in [k / 10 for k in range(11)]]
        trunk += [(cx - r * (.95 - .1 * k / 4), cy + r * (.75 - .08 * k)) for k in range(5)]
        _kk_wline(cv, trunk, r * .07)
        _kk_wline(cv, E([(-.62, .05), (-.8, .18), (-.9, .15)]), r * .03)
        ear = E([(-.5, -.42), (-.22, -.38), (-.18, -.05), (-.3, .12), (-.45, -.05)])
        cv.obj([ear], .5)
        _kk_cut(cv, ear, 70, 1.5)
        cloth = E([(-.12, -.42), (.5, -.42), (.55, .05), (.2, .18), (-.08, .05)])
        cv.obj([cloth], .5)
        for k in range(3):
            cv.hair(E([(-.08 + k * .02, -.3 + k * .12), (.52 - k * .01, -.3 + k * .12)]))
        _kk_cut(cv, E([(-.1, .0), (.53, .0), (.2, .15), (-.08, .05)]), 45, 1.5)
        cv.obj([_C._ell_pts(cx - r * .62, cy - r * .26, r * .04, r * .04, 6)[:-1]], .5)
    elif kind == "panel":
        fr = E([(-.85, -.2), (.55, -.75), (.85, .2), (-.55, .75)])
        cv.obj([fr], 1.)
        _kk_cut(cv, fr, -22, 1.5)
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
                _kk_cut(cv, poly, a0 * 57 + 30, 1.5)
    elif kind == "paw":
        cv.obj([_C._ell_pts(cx, cy + r * .3, r * .38, r * .32, 20)[:-1]], .5)
        _kk_cut(cv, _C._ell_pts(cx + r * .05, cy + r * .35, r * .3, r * .24, 16)[:-1], -45, 1.5)
        for a in (-2.4, -1.85, -1.3, -.75):
            px, py = cx + r * .62 * _m.cos(a), cy + r * .1 + r * .62 * _m.sin(a)
            cv.obj([_C._ell_pts(px, py, r * .15, r * .19, 12)[:-1]], .5)
    elif kind == "fleur":
        mid = E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4), (-.1, .25), (-.22, -.2), (-.2, -.62)])
        cv.obj([mid], .5)
        _kk_cut(cv, E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4)]), 70, 1.5)
        cv.hair(E([(0, -.85), (0, .3)]))
        for sg in (-1, 1):
            pet = E([(sg * .12, .2), (sg * .45, -.25), (sg * .8, -.42), (sg * .95, -.2), (sg * .78, -.05),
                     (sg * .62, -.18), (sg * .45, .05), (sg * .3, .38)])
            cv.obj([pet], .5)
            _kk_cut(cv, pet, -sg * 50, 1.5)
            cv.obj([_C._ell_pts(cx + sg * r * .82, cy - r * .28, r * .1, r * .1, 10)[:-1]], .5)
        band = E([(-.42, .32), (.42, .32), (.42, .5), (-.42, .5)])
        cv.obj([band], .5)
        _kk_cut(cv, band, 90, 1.5)
        cv.obj([E([(-.15, .5), (.15, .5), (.1, .95), (0, .82), (-.1, .95)])], .5)
    else:   # "dog": a retriever's head in profile, looking left
        head = E([(.55, .9), (.35, .25), (.1, .05), (-.15, .05), (-.55, .12), (-.82, .05), (-.88, -.12),
                  (-.7, -.22), (-.35, -.3), (-.1, -.55), (.2, -.62), (.45, -.5), (.62, -.2), (.75, .35), (.9, .9)])
        cv.obj([head], .5)
        _kk_cut(cv, E([(.35, .25), (.62, -.2), (.75, .35), (.9, .9), (.55, .9)]), 75, 1.5)
        ear = E([(.15, -.55), (.42, -.48), (.5, -.1), (.42, .35), (.3, .4), (.22, .0)])
        cv.obj([ear], .5)
        _kk_cut(cv, ear, 80, 1.5)
        cv.obj([_C._ell_pts(cx - r * .86, cy - r * .1, r * .07, r * .07, 8)[:-1]], 1.)
        cv.line(_C._ell_pts(cx - r * .12, cy - r * .3, r * .05, r * .05, 8))
        cv.hair(E([(-.82, .05), (-.5, .1)]))
    return cv.svg()


def kk_roundel(cx, cy, r, kind, bead=1.2):
    """An egg in a small bead-ringed roundel on the matte."""
    ring, ox, oy = kk_ring(cx, cy, r, r, bead)
    return (f'<path d="{_kk_ell_d(cx, cy, r + .5, r + .5, 40)}" fill="url(#kkM)" stroke="none"/>'
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

def kk_med_poly(shape, cx, cy, rx, ry, seed=0):
    """The medallion's outline (clockwise on screen) in the box cx +- rx, cy +- ry:
    'oval', 'roundel' (a circle), 'arch' (an arched top on straight sides), 'banner' (a bowed
    ribbon with swallowtail notches), 'lunette' (a half oval on its flat side) or 'irregular'
    (a silhouette that swells up into a peak top-left, like a pine over a hummock)."""
    if shape == "roundel":
        r = min(rx, ry)
        return _C._ell_pts(cx, cy, r, r, 72)[:-1]
    if shape == "arch":
        return kk_shape("arch", cx - rx, cy - ry, 2 * rx, 2 * ry, min(rx * .55, ry * .7))
    if shape == "lunette":
        n = 40
        return [(cx - rx * _m.cos(_PI * i / n), cy + ry - 2 * ry * _m.sin(_PI * i / n)) for i in range(n + 1)]
    if shape == "banner":
        bow = ry * .3
        n = 24
        nt = min(ry * .9, rx * .14)
        us = [-1 + 2. * i / n for i in range(n + 1)]
        top = [(cx + rx * u, cy - ry + bow * u * u) for u in us]
        bot = [(cx + rx * u, cy + ry - bow + bow * u * u) for u in us[::-1]]
        return top + [(cx + rx - nt, cy + bow * .5)] + bot + [(cx - rx + nt, cy + bow * .5)]
    if shape == "irregular":
        pts = []
        n = 90
        rng = _r.Random(seed * 3 + 11)
        ph = rng.uniform(0, _TAU)
        for i in range(n):
            a = _TAU * i / n
            k = 1 + .05 * _m.sin(5 * a + ph) + .03 * _m.sin(9 * a + 2 * ph)
            da = (a - 3.92 + _PI) % _TAU - _PI          # the peak, up and to the left (the pine)
            k += .42 * _m.exp(-(da / .3) ** 2)
            pts.append((cx + rx * .9 * k * _m.cos(a), cy + ry * .78 * k * _m.sin(a) + ry * .12))
        return pts
    return _C._ell_pts(cx, cy, rx, ry, 72)[:-1]


def _kk_setting(shape, poly, cx, cy, rx, ry, bead):
    """The medallion's setting: the bead ring for an oval, the gold-line border otherwise.
    Returns (svg, width)."""
    if shape == "oval":
        s, ox, oy = kk_ring(cx, cy, rx, ry, bead)
        return s, ox - rx
    return kk_border(poly, bead)


def kk_plate(w, h, scene, egg="dog", seed=0, arms=False, egg2=None, dens=1., limit=188000,
             shape="oval", form="plate", flank=None):
    """The whole plate, edge to edge. The page's planned form (edition plan 1.6) and shape steer
    the composition; its size picks the layout:
      h < 110   form 'headpiece': a bead row and gold line, the matte carrying fine scroll that
                flows out both ways from the medallion, an egg roundel.
                form 'tailpiece' / 'marginal': a pointed cul-de-lampe silhouette (or, in a squarish
                box, a roundel) set in a gold-line border on a stippled frame ground, the scroll
                inside it flowing from the medallion; the egg lives in the scene.
      110-260   a cut-cornered panel in a gold-line, beaded border; spandrels of scroll and
                rosettes outside it; the medallion at the centre, the scroll flowing from its foot;
                on section fronts the dedication cartouche (arms) at the medallion's foot.
      > 260     an arched panel: a great copperplate scene in the medallion; under it a roundel
                (the arms on fronts, else the egg); flank roundels either side if asked; a bordered
                frieze at the foot with scroll flowing both ways from a palmette.
    The medallion takes `shape` (see kk_med_poly). scene(x, y, w, h, mode) -> svg filling that
    rect (it is clipped to the medallion); mode is 'band', 'medium' or 'tall'."""
    rng = _r.Random(seed)
    o = [kk_defs()]
    deferred = []

    def run_field(box, obst, roots, rmin, rmax, inside=None, poly=None, sd=0, area=None, cut=None):
        d = (_kk_pd_poly(poly) if poly else kk_rect_d(*box)) + (_kk_pd_poly(cut) if cut else "")
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
        (field bytes ~ 20 * area / rmin^1.2, measured)."""
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

    def medallion(cx, cy, rx, ry, mode, bead):
        """Paint the medallion: white base, the scene clipped to the shape, the setting."""
        poly = kk_med_poly(shape, cx, cy, rx, ry, seed)
        o.append(f'<path d="{_kk_pd_poly(kk_offset(poly, 1.))}" fill="#fff" stroke="none"/>')
        o.append(kk_clip(_C._uid("kks", w, h, seed, mode), _kk_pd_poly(poly), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, mode)))
        s, e = _kk_setting(shape, poly, cx, cy, rx, ry, bead)
        o.append(s)
        return poly, e

    def keep_clear(cx, cy, rx, ry, pad):
        """inside() test that keeps the scroll off the medallion and its setting."""
        q = kk_inside(kk_offset(kk_med_poly(shape, cx, cy, rx, ry, seed), pad))
        return lambda px, py: not q(px, py)

    if h < 110 and form in ("tailpiece", "marginal"):
        o.append(_C.dark_ground((0, 0, w, h), "S"))
        o.append(f'<path d="M0,.5H{_kn(w)}M0,{_kn(h - .5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        cx, cy = w / 2, h / 2
        if w < h * 2.6:
            # a marginal device: the roundel alone in a beaded square with rosettes at the corners
            r = min(w, h) / 2 - 9
            sq = kk_shape("rect", 3, 3, w - 6, h - 6)
            o.append(kk_matte(_kk_pd_poly(sq)))
            for (qx, qy) in ((7, 7), (w - 7, 7), (w - 7, h - 7), (7, h - 7)):
                o.append(kk_rosette(qx, qy, 3.))
            medallion(cx, cy, r, r, "band", 1.)
            return finish()
        # the cul-de-lampe: a pointed lozenge with swelling, curved sides
        a, b = w / 2 - 4, h / 2 - 4
        sil = []
        for i in range(96):
            t = _TAU * i / 96
            c_, s_ = _m.cos(t), _m.sin(t)
            sil.append((cx + a * _m.copysign(abs(c_) ** .75, c_),
                        cy + b * _m.copysign(abs(s_) ** 1.25, s_) * (1 - .25 * abs(c_) ** 3)))
        border, bw = kk_border(sil, 1.)
        ry = h / 2 - 10.5          # the medallion's setting rides over the silhouette's border
        rx = ry if shape == "roundel" else min(w * (.3 if shape == "banner" else .2), max(ry * (2.6 if shape == "banner" else 1.7), 26))
        ins = kk_inside(sil)
        clear = keep_clear(cx, cy, rx, ry, 8.)
        run_field((0, 0, w, h), [], [(cx - rx - 7, cy, 180), (cx + rx + 7, cy, 0)], max(3.6, h * .07), max(8, h * .26),
                  lambda px, py: ins(px, py) and clear(px, py), sil, 1,
                  area=.62 * w * h - _PI * (rx + 8) * (ry + 8))
        o.append(border)
        medallion(cx, cy, rx, ry, "band", 1.)
        return finish()

    if h < 110:
        top = 8.
        gy, gh = top, h - top - 3
        cx, cy = w / 2, gy + gh / 2
        ry = gh / 2 - 7.5
        if shape == "banner":
            rx = w * .36
        elif shape == "roundel":
            rx = ry
        else:
            rx = min(w * .17, max(ry * 2.2, 26))
        er = min(gh / 2 - 7, 17)
        ex = w * (.08 if seed % 2 else .92) if shape == "banner" else w * (.13 if seed % 2 else .87)
        obst = [("c", ex, cy, er + 7)] if egg else []
        if shape == "oval":
            obst.append(("e", cx, cy, rx + 9, ry + 9))
        clear = keep_clear(cx, cy, rx, ry, 9.)
        run_field((0, gy, w, gh), obst, [(cx - rx - 8, cy, 180), (cx + rx + 8, cy, 0)],
                  max(4.5, gh * .1), max(9, gh * .33), clear, sd=1,
                  area=w * gh - 3.4 * (rx + 9) * (ry + 9) - (_PI * (er + 7) ** 2 if egg else 0))
        medallion(cx, cy, rx, ry, "band", 1.)
        if egg:
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
        outer = kk_inside(kk_offset(poly, 9.))
        run_field((0, 0, w, h), [], [(0, 0, 45), (w, 0, 135), (w, h, -135), (0, h, -45)], 4.5, 10.,
                  lambda px, py: not outer(px, py), sd=2, cut=kk_offset(poly, 4.))
        cx, cy = w / 2, h / 2
        ry = (h - 2 * m) / 2 - 12
        ar = min(15., h * .075) if arms else 0
        if arms:                       # room for the dedication cartouche at the foot
            ry -= ar + 3
            cy -= ar + 3
        rx = ry if shape == "roundel" else min(w * (.27 if shape in ("banner", "lunette") else .2), ry * (1.6 if shape in ("banner", "lunette") else 1.25))
        if shape == "irregular":
            rx = min(w * .22, ry * 1.4)
        er = min(15., h * .1)
        ex = cx + (rx + 30 + er) * (-1 if seed % 2 else 1)
        obst = [("c", ex, cy, er + 8)] if egg else []
        if arms:
            obst.append(("c", cx, cy + ry + 6 + ar, ar + 8))
        border, bw = kk_border(poly)
        for q in _kk_along(poly, 3.):
            obst.append(("c", q[0], q[1], 3.))
        pin = kk_inside(poly)
        clear = keep_clear(cx, cy, rx, ry, 10.)
        run_field((m, m, w - 2 * m, h - 2 * m), obst,
                  [(cx - rx * .55, cy + ry + 8, 160), (cx + rx * .55, cy + ry + 8, 20), (cx, cy - ry - 9, 0 if seed % 2 else 180)],
                  max(6, h * .045), max(13, h * .14), lambda px, py: pin(px, py) and clear(px, py), poly, 3,
                  area=(w - 2 * m) * (h - 2 * m) - 2 * c * c - 3.4 * (rx + 10) * (ry + 10) - _PI * (er + 8) ** 2)
        o.append(border)
        for (qx, qy) in ((m * .6 + c * .3, m * .6 + c * .3), (w - m * .6 - c * .3, m * .6 + c * .3),
                         (w - m * .6 - c * .3, h - m * .6 - c * .3), (m * .6 + c * .3, h - m * .6 - c * .3)):
            o.append(kk_rosette(qx, qy, 3.6))
        medallion(cx, cy, rx, ry, "medium", 1.5)
        if egg:
            rr, _ = kk_roundel(ex, cy, er, egg, 1.)
            o.append(rr)
        if arms:
            rr, _ = kk_roundel(cx, cy + ry + 6 + ar, ar, "arms", 1.)
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
    rx = ry if shape == "roundel" else min((w - 2 * m) * (.36 if flank else .4), ry * 1.45)
    cy = m + rise * .5 + ry + 18
    ey = min(cy + ry + 14 + rr_ + 6, yb - rr_ - 10)
    obst = [("c", cx, ey, rr_ + 10)]
    fr = 0
    if flank:
        fr = min(20., ((w - 2 * m) / 2 - rx - 18) / 2 - 2)
        fx = (cx - rx - 12 - fr, cx + rx + 12 + fr)
        for x_ in fx:
            obst.append(("c", x_, cy + ry * .35, fr + 8))
    for q in _kk_along(poly, 3.):
        obst.append(("c", q[0], q[1], 3.))
    roots = [(cx - rr_ - 10, ey, 180), (cx + rr_ + 10, ey, 0), (cx, cy - ry - 10, 0 if seed % 2 else 180)]
    pin = kk_inside(poly)
    clear = keep_clear(cx, cy, rx, ry, 10.)
    run_field((m, m, w - 2 * m, ph), obst, roots, max(9, h * .019), max(19, h * .048),
              lambda px, py: pin(px, py) and clear(px, py), poly, 5,
              area=(w - 2 * m) * ph - 3.4 * (rx + 10) * (ry + 10) - _PI * (rr_ + 10) ** 2 - .43 * rise * (w - 2 * m))
    o.append(border)
    medallion(cx, cy, rx, ry, "tall", 1.5)
    if arms or egg:
        rr, _ = kk_roundel(cx, ey, rr_, "arms" if arms else egg, 1.2)
        o.append(rr)
    if flank:
        for x_, kind in zip(fx, flank):
            rr, _ = kk_roundel(x_, cy + ry * .35, fr, kind, 1.)
            o.append(rr)
    # the frieze
    fy = yb + 8
    fp = kk_shape("rect", m + 6, fy + 4, w - 2 * m - 12, h - fy - 8)
    fb, _ = kk_border(fp, 1.2)
    pr = (h - fy - 8) / 2 - 1
    pcx, pcy = w / 2, fy + 4 + (h - fy - 8) / 2
    o.append(kk_matte(kk_rect_d(0, yb + 4, w, h - yb - 4)))
    run_field((m + 6, fy + 4, w - 2 * m - 12, h - fy - 8), [("c", pcx, pcy, pr * 1.05)] + ([("c", w * .2, pcy, pr * .8)] if egg2 else []),
              [(pcx - pr, pcy, 180), (pcx + pr, pcy, 0)], max(5.5, pr * .42), pr * 1.05, sd=7)
    o.append(fb)
    o.append(kk_egg(egg2 or "fleur", pcx, pcy, pr * .95))
    return finish()


# ---- the vignette kit: a free-standing engraved scene on a light ground -----------------------
# (art direction of Nov 12: the subject is the composition; no black field, no generic scroll; the
# frame, where there is one, is built from the page's own motifs; at most a quarter of the plate dark)


def vg_defs():
    """No ground of our own: outside the vignette's cut the plate is transparent, so the frame
    designer's light engraved ground shows through and the scene dissolves into it."""
    return ""


def vg_ragged(poly, amp=3., seed=0, step=1.6):
    """The vignette's dissolving edge: the outline pulled in by an irregular amount, slow swells
    and quick jags, so the lines of the scene stop raggedly as in Bewick's tailpieces."""
    rng = _r.Random(seed * 13 + 5)
    pts = _kk_resample(list(poly) + [poly[0]], step)[:-1]
    n = len(pts)
    ph = [rng.uniform(0, _TAU) for _ in range(3)]
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    out = []
    for i, (x, y) in enumerate(pts):
        t = _TAU * i / n
        d = amp * (.55 + .25 * _m.sin(3 * t + ph[0]) + .2 * _m.sin(7 * t + ph[1]))
        d += amp * .55 * rng.random() ** 2 * (1 if i % 2 else .4)
        dx, dy = cx - x, cy - y
        L = _m.hypot(dx, dy) or 1.
        out.append((x + dx / L * d, y + dy / L * d))
    return out


def vg_rule(poly, double=True):
    """A plate-mark: a 1 px rule round the shape and a fine rule just outside it."""
    s = f'<path d="{_kk_pd_poly(poly)}" fill="none" stroke="#000" stroke-width="1"/>'
    if double:
        s += f'<path d="{_kk_pd_poly(kk_offset(poly, 2.5))}" fill="none" stroke="#000" stroke-width=".5"/>'
    return s


def vg_leaf(cv, x, y, ang, L, W, bend=.25, shade=1, veins=True):
    """A leaf from its base (x, y) along ang: two swelling edges meeting at the tip, the midrib
    cut, the shadow half modelled in fine cuts that follow the leaf's turn."""
    ux, uy = _m.cos(ang), _m.sin(ang)
    vx, vy = -uy, ux
    n = 10
    L_, R_ = [], []
    for i in range(n + 1):
        t = i / n
        c = bend * L * t * t
        wd = W * _m.sin(_PI * t ** .8) * (1 - .15 * t)
        mx, my = x + ux * L * t + vx * c, y + uy * L * t + vy * c
        L_.append((mx + vx * wd, my + vy * wd))
        R_.append((mx - vx * wd, my - vy * wd))
    poly = L_ + R_[::-1]
    cv.obj([poly], .5)
    mid = [(x + ux * L * t + vx * bend * L * t * t, y + uy * L * t + vy * bend * L * t * t) for t in [i / 8 for i in range(9)]]
    half = (L_ if shade > 0 else R_) + mid[::-1]
    cv.hair(_kk_zig(_C.hatch_poly(half, _m.degrees(ang) + 65 * shade, 1.5)))
    cv.hair(mid[:-1])
    if veins and L > 14:
        for k in range(2, 7, 2):
            p = mid[k]
            q = (L_ if shade < 0 else R_)[min(n, k + 2)]
            cv.hair([p, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)])
    return poly


def vg_reed(cv, x, base, hgt, lean, rng, cattail=True):
    """A reed: a tapering stalk leaning off true, two blade leaves with a twist, and on most a
    cattail head, its shadow side cross-cut."""
    top = (x + lean * hgt, base - hgt)
    mid = (x + lean * hgt * .45, base - hgt * .55)
    pts = _kk_bez((x, base), mid, mid, top, 10)
    R = _C._Rib(pts, [max(.6, hgt * .012 * (1 - i / 10) + .5) for i in range(11)], [max(.6, hgt * .012 * (1 - i / 10) + .5) for i in range(11)])
    cv.obj([R.outline()], .5)
    for sg in (-1, 1):
        a = -_PI / 2 + sg * rng.uniform(.25, .55) + lean
        vg_leaf(cv, x + sg * .5, base - hgt * rng.uniform(.05, .2), a, hgt * rng.uniform(.5, .8), max(1., hgt * .018), -sg * .55, sg, False)
    if cattail:
        hx, hy = pts[7]
        hh = max(4., hgt * .16)
        head = _C._ell_pts(hx, hy, max(1.4, hgt * .028), hh / 2, 16)[:-1]
        cv.obj([head], .5)
        cv.line(_C.hatch_poly([p for p in head if p[0] >= hx - .3], 0, 1.5))
        cv.hair(_C.hatch_poly(head, 35, 2))


def vg_ribbon(cv, x0, x1, yc, hgt, bow=.3, tails=True, seed=0):
    """A ribbon banner: a bowed face from x0 to x1 (centre line yc, depth hgt), its ends turning
    back behind it in folds that are cut dark, with swallowtail ends. Returns the face polygon
    (for the content) after drawing the tails and the fold shadows."""
    n = 28
    us = [-1 + 2. * i / n for i in range(n + 1)]
    cx, rx = (x0 + x1) / 2, (x1 - x0) / 2
    b = hgt * bow
    top = [(cx + rx * u, yc - hgt / 2 + b * u * u) for u in us]
    bot = [(cx + rx * u, yc + hgt / 2 + b * u * u) for u in us[::-1]]
    face = top + bot
    if tails:
        d = hgt * .32
        for sg in (-1, 1):
            ex, ey = cx + sg * rx, yc + b
            tail = [(ex - sg * hgt * .5, ey - hgt / 2 + d), (ex + sg * hgt * 1.5, ey - hgt / 2 + d),
                    (ex + sg * hgt * 1.08, ey + d), (ex + sg * hgt * 1.5, ey + hgt / 2 + d),
                    (ex - sg * hgt * .5, ey + hgt / 2 + d)]
            cv.obj([tail], 1.)
            cv.hair(_kk_zig(_C.hatch_poly(tail, 0, 1.5)))
            cv.hair(_C.hatch_poly([(ex, ey - hgt / 2 + d), (ex + sg * hgt * .45, ey - hgt / 2 + d), (ex + sg * hgt * .3, ey + hgt / 2 + d), (ex, ey + hgt / 2 + d)], 90, 2.))
            fold = [(ex, ey - hgt / 2 + d), (ex, ey + hgt / 2), (ex - sg * hgt * .38, ey + hgt / 2 + d)]
            cv.obj([fold], .5)
            cv.line(_C.hatch_poly(fold, 90 - 30 * sg, 1.5))
    cv.obj([face], 1.)
    # the face turns: shade near each end following the bow
    for sg in (-1, 1):
        sh = [p for p in top if sg * (p[0] - cx) > rx * .82] + [p for p in bot if sg * (p[0] - cx) > rx * .82]
        if len(sh) > 2:
            cv.hair(_C.hatch_poly(sh, 90, 1.5))
    return face


def vg_cartouche(cx, cy, r):
    """The Somaster dedication cartouche, a placeholder until the arms are cut: a small beaded
    oval holding crossed drumsticks over a sun, a scrolled leaf either side."""
    cv = _C.Canvas()
    for sg in (-1, 1):
        vg_leaf(cv, cx + sg * r * .9, cy + r * .25, (_PI if sg < 0 else 0) - sg * .3, r * 2.2, r * .42, -sg * .4, sg)
        vg_leaf(cv, cx + sg * r * .8, cy - r * .25, (_PI if sg < 0 else 0) + sg * .5, r * 1.7, r * .34, sg * .45, -sg)
    s = kk_svg(cv)
    rr, _ = kk_roundel(cx, cy, r, "arms", 1.)
    return s + rr


def vg_plate(w, h, scene, shape="oval", form="vignette", frame=None, arms=False, seed=0,
             ragged=True, amp=None, pad=None, aspect=None, limit=192000):
    """A plate in the planned form, transparent outside its cut: the scene, shaped
    (kk_med_poly) and either dissolving at a ragged edge or set in a plate-mark; the page's own
    frame (frame(box, poly, w, h, mode) -> svg) round it; on section fronts the dedication
    cartouche at the foot. scene(x, y, w, h, mode) -> svg filling that rect."""
    o = [kk_defs(), vg_defs()]
    m = 4.
    res = 0.
    if arms and h >= 110:
        res = min(40., h * .16)
    ar = aspect or {"oval": 1.7, "roundel": 1., "arch": 1.25, "banner": 4.2, "lunette": 2.1, "irregular": 1.55}.get(shape, 1.6)
    pd = 8. if pad is None else pad
    aw, ah = w - 2 * m - 2 * pd, h - 2 * m - 2 * pd - res
    if form == "headpiece":
        bw, bh = aw, ah
    else:
        bw = min(aw, ah * ar)
        bh = min(ah, bw / ar)
        if shape == "roundel":
            bw = bh = min(aw, ah)
    cx, cy = w / 2, m + pd + ah / 2
    rx, ry = bw / 2, bh / 2
    mode = "band" if bh < 80 else ("medium" if bh <= 230 else "tall")
    poly = kk_med_poly(shape, cx, cy, rx, ry, seed)
    cp = vg_ragged(poly, amp if amp is not None else max(3., min(9., bh * .05)), seed) if ragged else poly
    o.append(f'<path d="{_kk_pd_poly(cp)}" fill="#fff" stroke="none"/>')
    o.append(kk_clip(_C._uid("vgs", w, h, seed), _kk_pd_poly(cp), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, mode)))
    if not ragged:
        o.append(vg_rule(poly))
    if frame:
        o.append(frame((cx - rx, cy - ry, 2 * rx, 2 * ry), poly, w, h, mode))
    if res:
        r = res * .38
        o.append(vg_cartouche(cx, h - m - res / 2 - 1, r))
    return _C.svg_doc(w, h, "".join(o))


def vg_wheat(cv, pts, ear=.42, k=1.):
    """A wheat stalk along pts (base first): the straw, and on its last part the ear, kernels set
    in pairs and each shaded on its lower side, long awns combed back from them."""
    R = _C._Rib(pts, [max(.5, .9 * k)] * len(pts), [max(.5, .9 * k)] * len(pts))
    cv.obj([R.outline()], .5)
    n = len(pts)
    i0 = int(n * (1 - ear))
    for i in range(i0, n - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        a = _m.atan2(y1 - y0, x1 - x0)
        for sg in (-1, 1):
            ka = a + sg * .55
            L = 4.2 * k * (1 - .35 * (i - i0) / max(1, n - i0))
            vg_leaf(cv, x0, y0, ka, L, 1.3 * k, 0, -sg, False)
            tx, ty = x0 + _m.cos(ka) * L, y0 + _m.sin(ka) * L
            cv.hair([(tx, ty), (tx + _m.cos(a + sg * .25) * L * 1.4, ty + _m.sin(a + sg * .25) * L * 1.4)])


def vg_wreath(cv, cx, cy, r, kind="wheat", seed=0, k=1.):
    """A wreath round a roundel, two branches rising from a bow at the foot to meet at the top:
    'wheat' (ears on curving straws) or 'fir' (Douglas-fir sprigs with a cone or two)."""
    rng = _r.Random(seed)
    for sg in (-1, 1):
        n = 7
        for j in range(n):
            a0 = _PI / 2 + sg * (.25 + j * (2.5 / n))
            a1 = a0 + sg * .55
            pts = [(cx + (r + 1.5 + 2 * _m.sin(_PI * t)) * _m.cos(a0 + (a1 - a0) * t), cy + (r + 1.5 + 2 * _m.sin(_PI * t)) * _m.sin(a0 + (a1 - a0) * t)) for t in [i / 8 for i in range(9)]]
            if kind == "wheat":
                vg_wheat(cv, pts, .55, k)
            else:
                px, py = pts[4]
                for q in range(5):
                    t = q / 4
                    x_, y_ = pts[int(t * 8)]
                    aa = a0 + (a1 - a0) * t
                    for s2 in (-1, 1):
                        cv.hair([(x_, y_), (x_ + _m.cos(aa + sg * _PI / 2 + s2 * .9) * 4 * k, y_ + _m.sin(aa + sg * _PI / 2 + s2 * .9) * 4 * k)])
                Rb = _C._Rib(pts, [.7] * 9, [.7] * 9)
                cv.obj([Rb.outline()], .5)
                if j % 3 == 1:
                    cone = _C._ell_pts(px, py, 2.2 * k, 3.4 * k, 12)[:-1]
                    cv.obj([cone], .5)
                    cv.line(_C.hatch_poly(cone, 0, 1.5))
    # the bow
    for sg in (-1, 1):
        loop = [(cx, cy + r + 3), (cx + sg * 5 * k, cy + r - 1), (cx + sg * 7 * k, cy + r + 3), (cx + sg * 4 * k, cy + r + 5)]
        cv.obj([loop], .5)
        cv.hair(_C.hatch_poly(loop, 60 * sg, 1.5))
        tail = [(cx, cy + r + 4), (cx + sg * 3 * k, cy + r + 11 * k), (cx + sg * 5 * k, cy + r + 10 * k), (cx + sg * 1.5, cy + r + 4)]
        cv.obj([tail], .5)
        cv.hair(_C.hatch_poly(tail, 90, 1.5))
    cv.obj([_C._ell_pts(cx, cy + r + 3.5, 2 * k, 1.7 * k, 10)[:-1]], .5)


def vg_bough(cv, pts, k=1., seed=0, twigs=True):
    """A Douglas-fir bough along pts (base first): a tapering limb, side twigs thrown forward,
    and every part clothed in needles combed forward, light above and cut heavier beneath, so the
    bough has a lit top and a shadowed belly."""
    rng = _r.Random(seed)
    pts = _kk_resample(pts, 1.5)
    n = len(pts)
    wl = [max(.6, 2.4 * k * (1 - i / n)) for i in range(n)]
    R = _C._Rib(pts, wl, wl)

    def needles(P, L0, dens=1.6):
        m = len(P)
        up, dn = [], []
        acc = 0.
        for i in range(1, m):
            (x0, y0), (x1, y1) = P[i - 1], P[i]
            seg = _m.hypot(x1 - x0, y1 - y0)
            acc += seg
            if acc < dens:
                continue
            acc = 0.
            a = _m.atan2(y1 - y0, x1 - x0)
            t = i / m
            L = L0 * (1 - .45 * t) * rng.uniform(.8, 1.1)
            for sg, bag in ((-1, up), (1, dn)):
                b = a + sg * rng.uniform(.75, 1.05)
                bag.append([(x1, y1), (x1 + _m.cos(b) * L, y1 + _m.sin(b) * L)])
        cv.hair(up)
        cv.line(dn[::2])
        cv.hair(dn[1::2])

    if twigs:
        for i in range(6, n - 6, max(6, int(10 / k))):
            (x0, y0), (x1, y1) = pts[i - 1], pts[i]
            a = _m.atan2(y1 - y0, x1 - x0)
            sg = 1 if (i // 7) % 2 else -1
            L = 14 * k * (1 - .5 * i / n) * rng.uniform(.8, 1.2)
            b = a + sg * .6
            tw = [(x1 + _m.cos(b) * L * u + _m.cos(a) * L * .3 * u * u, y1 + _m.sin(b) * L * u + _m.sin(a) * L * .3 * u * u) for u in [j / 8 for j in range(9)]]
            cv.obj([], 0)
            cv.line(tw)
            needles(tw, 5. * k)
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(.5, 0, 1))
    needles(pts, 6.5 * k, 1.3)


def vg_rope(cv, pts, r=3., closed=False):
    """A laid rope along pts: strands twisting across it, each a lozenge lit on its upper edge
    and cut in fine lines on its lower, the lay running at a steady pitch."""
    P = _kk_resample(list(pts) + ([pts[0]] if closed else []), 1.)
    n = len(P)
    step = max(2, int(r * 1.3))
    for i in range(0, n - step - 1, step):
        (x0, y0), (x1, y1) = P[i], P[min(n - 1, i + step)]
        a = _m.atan2(y1 - y0, x1 - x0)
        nx, ny = -_m.sin(a), _m.cos(a)
        ux, uy = _m.cos(a), _m.sin(a)
        L = r * 1.3
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        q = [(c[0] - nx * r - ux * L * .9, c[1] - ny * r - uy * L * .9), (c[0] - nx * r + ux * L * .1, c[1] - ny * r + uy * L * .1),
             (c[0] + nx * r + ux * L * .9, c[1] + ny * r + uy * L * .9), (c[0] + nx * r - ux * L * .1, c[1] + ny * r - uy * L * .1)]
        cv.obj([q], .5)
        cv.hair([((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2), ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2)])
        cv.hair([(q[2][0] - ux * .8, q[2][1] - uy * .8), (q[3][0] + ux * .3, q[3][1] + uy * .3)])


def vg_coil(cv, cx, cy, r):
    """A coil of rope lying flat: turns of laid rope round a dark centre."""
    rr = r
    while rr > 3:
        vg_rope(cv, _C._ell_pts(cx, cy, rr, rr * .45, max(16, int(rr * 3))), 2.2, True)
        rr -= 4.6
    cv.obj([_C._ell_pts(cx, cy, max(1.5, rr), max(1., rr * .45), 10)[:-1]], .5)


# ---- the plate ------------------------------------------------------------------------------

# Edition plan: vignette, about 18% of the sheet, an oval.
FORM = {"form": "vignette", "share": .18, "shape": "oval", "egg": "a kestrel on a fence post"}


def _kestrel(cv, x, y, s):
    """An American kestrel perched upright on (x, y), facing left: the moustache stripes, the
    long barred tail, the folded wings."""
    P = lambda u, v: (x + u * s, y - v * s)
    tail = [P(.02, .45), P(.14, .45), P(.16, -.08), P(.0, -.08)]
    cv.obj([tail], .5)
    for k in range(4):
        cv.hair([P(.01, .32 - k * .1), P(.15, .32 - k * .1)])
    body = [P(-.12, .9), P(.06, 1.0), P(.2, .82), P(.22, .5), P(.12, .38), P(-.06, .4), P(-.16, .62)]
    cv.obj([body], 1.)
    wing = [P(.04, .88), P(.22, .8), P(.2, .4), P(.08, .3)]
    cv.obj([wing], .5)
    cv.hair(C.hatch_poly(wing, 75, 1.5))
    head = C._ell_pts(*P(-.04, 1.08), s * .14, s * .13, 14)[:-1]
    cv.obj([head], 1.)
    cv.line([P(-.1, 1.06), P(-.12, .96)])           # the moustache stripe
    cv.line([P(.06, 1.08), P(.06, .98)])
    cv.heavy([P(-.07, 1.11), P(-.06, 1.12)])
    cv.line([P(-.18, 1.07), P(-.24, 1.03)])          # beak
    cv.hair([P(-.02, .4), P(-.02, .34)])


def _brush_pile(cv, cx, by, w, h, rng):
    """The heap of yard debris: a mound of crossing limbs and twigs, dark in its hollows."""
    mound = [(cx - w / 2 + w * i / 20, by - h * math.sin(math.pi * i / 20) ** .8 * (1 + .12 * math.sin(i * 1.9))) for i in range(21)]
    cv.obj([mound], 0)
    cv.hair(C.hatch_poly(mound, 0, 1.5))
    cv.hair(C.hatch_poly(mound, 60, 2))
    for i in range(int(w / 2.2)):
        a = rng.uniform(-.7, .7) + (math.pi if rng.random() < .5 else 0)
        L = rng.uniform(.25, .6) * w
        px = cx + rng.uniform(-.38, .38) * w
        top = by - h * math.sin(math.pi * (px - cx + w / 2) / w) ** .8
        py = rng.uniform(top + 1, by)
        x0, y0 = px - L / 2 * math.cos(a), py - L / 2 * math.sin(a) * .5
        x1, y1 = px + L / 2 * math.cos(a), py + L / 2 * math.sin(a) * .5
        rib = C._Rib([(x0, y0), (x1, y1)], [.9, .5], [.9, .5])
        cv.obj([rib.outline()], .5)
        if i % 3 == 0:
            cv.line([(x0 + 2, y0 + 1), (x0 - 1, y0 - 2.5)])


def _smoke(cv, x, y, hgt, rng):
    """A thin column of smoke leaning off on the breeze: wisps of fine line that part and drift."""
    n = 16
    spine = [(x + hgt * (.35 * (t ** 1.6) + .05 * math.sin(t * 7)), y - hgt * t) for t in [i / n for i in range(n + 1)]]
    wl = [1. + hgt * .07 * (i / n) ** 1.2 for i in range(n + 1)]
    R = C._Rib(spine, wl, wl)
    cv.obj([R.outline()], 0)
    for k in (-.85, -.45, -.1, .25, .6, .9):
        cv.hair(R.contour(k, .03 + .1 * abs(k), 1))
    cv.line(R.contour(.9, .05, .6))


def prairie_scene(X, Y, W, H, mode, seed, burn_ok):
    rng = random.Random(seed)
    cv = C.Canvas()
    band = mode == "band"
    hz = Y + H * (.5 if band else .52)
    kk_sky(cv, X, Y, W, hz + 2, seed, 0 if band else 1)
    if not band:
        mh = H * .3
        mt_hood(cv, X + W * .62, hz - H * .03, mh * 2.3, mh)
    treeline(cv, X - 2, X + W + 2, hz - H * .1, hz + 1, seed + 3)
    # the prairie: a white field cut in tall grass, denser and taller toward us
    fld = [(X - 2, hz), (X + W + 2, hz), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([fld], 0)
    y, row = hz + 2, 0
    while y < Y + H + 2:
        f = (y - hz) / max(1., Y + H - hz)
        x = X - 2 + rng.uniform(0, 2)
        blades = []
        while x < X + W + 2:
            hh = (1.5 + 9 * f * f) * rng.uniform(.6, 1.2) * (H / 120 if not band else .5)
            lean = rng.uniform(-.5, .9) * hh * .5
            blades.append([(x, y), (x + lean * .4, y - hh * .6), (x + lean, y - hh)])
            x += rng.uniform(2., 3.5) / (.6 + f)
        (cv.line if f > .7 and row % 2 else cv.hair)(blades)
        y += (2. + 3. * (1 - f)) * max(1., H / 160)
        row += 1
    # the fence: posts in perspective along the edge, two rails
    fy0, fy1 = hz + H * .05, Y + H * (.82 if not band else .9)
    xa, xb = X + W * .02, X + W * (.55 if not band else .5)
    posts = []
    for i in range(6):
        t = i / 5
        px = xb + (xa - xb) * t ** .9
        py = fy0 + (fy1 - fy0) * t ** 1.4
        ph = H * (.06 + .2 * t ** 1.3)
        pw = max(1.2, ph * .12)
        posts.append((px, py, ph, pw))
    for k in (.35, .7):
        cv.obj([], 0)
        rail = [(p[0], p[1] - p[2] * k) for p in posts]
        rib = C._Rib(rail, [max(.5, p[3] * .35) for p in posts], [max(.5, p[3] * .35) for p in posts])
        cv.obj([rib.outline()], .5)
        cv.hair(rib.contour(.4, 0, 1))
    for px, py, ph, pw in posts:
        post = [(px - pw, py), (px - pw * .9, py - ph), (px + pw * .9, py - ph), (px + pw, py)]
        cv.obj([post], .5)
        cv.hair(C.hatch_poly([(px, py), (px, py - ph), (px + pw * .9, py - ph), (px + pw, py)], 90, 1.5))
    # Easter egg: the kestrel on the nearest-but-one post
    kp = posts[-2]
    _kestrel(cv, kp[0], kp[1] - kp[2], max(7., H * (.16 if not band else .3)))
    # the brush pile, smoking only on a burn day
    bx, bw = X + W * (.74 if not band else .76), W * (.3 if not band else .3)
    bby = Y + H * (.84 if not band else .9)
    bh = H * (.17 if not band else .26)
    if burn_ok:
        for k in range(2 if band else 3):
            _smoke(cv, bx - bw * .1 + k * bw * .12, bby - bh * .8, H * (.55 if not band else .5) * (1 - .2 * k), rng)
    _brush_pile(cv, bx, bby, bw, bh, rng)
    out = cv.svg()
    if not band:
        out += paw_print(bx - bw * .62, bby + H * .05, max(4., H * .04))
        # the natives in flower this month, in the near grass at the left
    return out


def _meadow_frame(box, poly, w, h, mode, seed):
    """The vignette's frame grows from the land itself: at either side of the oval's foot a clump
    of prairie grass and the month's natives, sneezeweed on the left, selfheal on the right,
    standing over the dissolving edge and running out in single blades."""
    bx, by, bw, bh = box
    rng = random.Random(seed + 9)
    cv = C.Canvas()
    gy = by + bh * .97
    for sg in (-1, 1):
        cx = bx + bw / 2 + sg * bw * .42
        reach = min(w / 2 - 6, bw * .5 + bh * .9) - bw * .42
        n = max(8, int(reach / 3.5))
        for i in range(n):
            t = i / n
            x = cx + sg * reach * t * rng.uniform(.6, 1.) - sg * bw * .08
            hg = bh * (.62 - .5 * t) * rng.uniform(.5, 1.05)
            a = -math.pi / 2 + sg * rng.uniform(.0, .45) * (1 if i % 2 else -.5)
            vg_leaf(cv, x, gy, a, hg, max(.9, hg * .025), sg * rng.uniform(.1, .5), sg, False)
    k = bh / 120.
    if mode != "band":
        sneezeweed(cv, bx + bw * .06, by + bh * .55, bh * .1, .5, .55, seed + 3)
        stem(cv, [(bx + bw * .07 + i * .2, gy - (gy - by - bh * .62) * i / 10) for i in range(11)], max(1., bh * .011), .8, True)
        selfheal(cv, bx + bw * .95, gy, bh * .5, seed + 17, -.05)
    return kk_svg(cv)


def plate(w, h, ctx):
    """Walk the land: the prairie edge with the brush pile (smoking only when it is OK to burn),
    the fence and its kestrel, the cottonwoods and Mt. Hood, in an oval vignette that dissolves
    at its edge, grass and the month's natives growing up over it. Easter egg: the kestrel on
    the post, and a dog's paw print in the bare earth."""
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    txt = (ctx.get("sample") or "").lower()
    burn_ok = not any(k in txt for k in ("no burn", "not ok to burn", "burning is not", "burn ban"))

    def sc(x, y, ww, hh, mode):
        return prairie_scene(x - 2, y - 2, ww + 4, hh + 4, mode, seed, burn_ok)
    return vg_plate(w, h, sc, shape="oval", form="vignette", seed=seed, frame=lambda *a: _meadow_frame(*a, seed))
