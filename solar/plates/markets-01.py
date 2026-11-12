"""markets-01 -- North American Helium.
The Stewart Valley helium purification plant on the Saskatchewan prairie: distillation columns,
cold box, liquefier bullet tanks and flare stack under a big ruled sky, a helium balloon rising on
its tether from the wellhead, a radiant helium atom (2p 2n, two orbits) for a sun, a prairie grain
elevator on the horizon. The pedestal tablet carries the spot-price line nearly tripling since
March; the ribbon reads HELIUM. Easter egg: Parker's dog sits at the wellhead watching the balloon.
"""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, _n, _d, _ell_pts, pat, dark_ground

PI = math.pi
TAU = 2 * PI


# ------------------------------------------------------------------ small geometry helpers
def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def clip_outside(segs, cx, cy, r):
    """Keep the parts of 2-point segments lying outside circle (cx, cy, r)."""
    out = []
    for (x0, y0), (x1, y1) in segs:
        dx, dy = x1 - x0, y1 - y0
        a = dx * dx + dy * dy
        b = 2 * (dx * (x0 - cx) + dy * (y0 - cy))
        c = (x0 - cx) ** 2 + (y0 - cy) ** 2 - r * r
        disc = b * b - 4 * a * c
        if a == 0 or disc <= 0:
            out.append([(x0, y0), (x1, y1)])
            continue
        s = math.sqrt(disc)
        t0, t1 = (-b - s) / (2 * a), (-b + s) / (2 * a)
        for u0, u1 in ((0, min(1, t0)), (max(0, t1), 1)):
            if u1 - u0 > .02:
                out.append([(x0 + dx * u0, y0 + dy * u0), (x0 + dx * u1, y0 + dy * u1)])
    return out


def clip_inside(segs, cx, cy, r):
    out = []
    for (x0, y0), (x1, y1) in segs:
        dx, dy = x1 - x0, y1 - y0
        a = dx * dx + dy * dy
        b = 2 * (dx * (x0 - cx) + dy * (y0 - cy))
        c = (x0 - cx) ** 2 + (y0 - cy) ** 2 - r * r
        disc = b * b - 4 * a * c
        if a == 0 or disc <= 0:
            continue
        s = math.sqrt(disc)
        u0, u1 = max(0, (-b - s) / (2 * a)), min(1, (-b + s) / (2 * a))
        if u1 - u0 > .02:
            out.append([(x0 + dx * u0, y0 + dy * u0), (x0 + dx * u1, y0 + dy * u1)])
    return out


def shade_round(cv, poly, cx, cy, r, solid=True):
    """Bulino shading of a rounded body lit from the upper left: three layers whose terminators
    are circles offset toward the light, darkest crescent at the lower right."""
    lx, ly = cx - r * .42, cy - r * .48
    cv.hair(clip_outside(hatch_poly(poly, 32, 3, 1.3), lx, ly, r * .2))
    cv.hair(clip_outside(hatch_poly(poly, 32, 3, .3), lx, ly, r * .55))
    cv.hair(clip_outside(hatch_poly(poly, -40, 2, 1.), lx, ly, r * .95))
    if solid:
        cv.line(clip_outside(hatch_poly(poly, 32, 1.5, .6), lx, ly, r * 1.28))


def cylinder(cv, x0, x1, y0, y1, rings=(), cap=True):
    """Upright shaded cylinder with a domed head; rings are platform fractions."""
    w = x1 - x0
    head = [(x0 + w / 2 + w / 2 * math.cos(a), y0 + w * .35 * math.sin(a)) for a in [PI + PI * i / 12 for i in range(13)]]
    body = head + [(x1, y1), (x0, y1)]
    cv.obj([body], 1.)
    # vertical rules: none in the highlight, closing up toward the shadow side
    u = .32
    while u < .99:
        x = x0 + w * u
        cv.hair([(x, y0 + 1), (x, y1)])
        u += (2. if u < .5 else 1.5) / max(w, 1)
    cv.heavy([(x1 - .9, y0), (x1 - .9, y1)])
    cv.heavy([(x1 - 2.1, y0 + 1), (x1 - 2.1, y1)])
    cv.hair([(x0 + w * .15, y0 + 2), (x0 + w * .15, y1)])
    for f in rings:
        y = y0 + (y1 - y0) * f
        cv.line([(x0 - 1.5, y), (x1 + 1.5, y)])
        cv.hair([(x0 - 1.5, y + 1.5), (x1 + 1.5, y + 1.5)])
    return body


# ------------------------------------------------------------------ the scene
DOG = [(0., .14), (.08, .08), (.16, .06), (.22, 0.), (.3, -.02), (.37, .12), (.38, .25), (.5, .45),
       (.68, .66), (.76, .86), (.86, .9), (.97, .76), (1.0, .8), (.92, .96), (.78, 1.), (.38, 1.),
       (.36, .9), (.3, .9), (.28, 1.), (.1, 1.), (.12, .96), (.2, .94), (.21, .6), (.17, .42),
       (.13, .28), (.06, .21)]


def scene(X, Y, W, H, seed=0):
    """The helium plant on the prairie, filling the box X,Y,W,H (caller clips it)."""
    cv = Canvas()
    rng = random.Random(seed)
    S = min(W, H)
    tiny = S < 60
    hz = Y + H * (.66 if tiny else .64)
    # sky: ruled, darkest at the zenith
    kk_sky(cv, X - 2, Y - 2, W + 4, hz + 1, seed, 0 if tiny else 1)
    # radiant helium atom in the upper right, standing for the sun
    ax, ay = X + W * .7, Y + H * (.2 if not tiny else .28)
    ar = S * (.12 if not tiny else .2)
    disc = _ell_pts(ax, ay, ar * 1.25, ar * 1.25, 48)
    cv.obj([disc], 0)
    for k in range(1, 40):
        rr = k * 3.
        if rr > ar * 1.25:
            break
        cv.hair([_ell_pts(ax, ay, rr, rr, 36) + [_ell_pts(ax, ay, rr, rr, 36)[0]]])
    for i in range(24):
        a = TAU * i / 24 + .1
        r1 = ar * (1.5 if i % 2 else 1.85)
        (cv.line if i % 2 == 0 else cv.hair)([(ax + ar * 1.3 * math.cos(a), ay + ar * 1.3 * math.sin(a)), (ax + r1 * math.cos(a), ay + r1 * math.sin(a))])
    if not tiny:
        for tilt in (.55, -.55):
            ca, sa = math.cos(tilt), math.sin(tilt)
            orb = [(ax + ar * math.cos(t) * ca - ar * .38 * math.sin(t) * sa,
                    ay + ar * math.cos(t) * sa + ar * .38 * math.sin(t) * ca) for t in [TAU * i / 48 for i in range(49)]]
            cv.obj([], 0)
            cv.line(orb)
            t = 1.1 if tilt > 0 else 4.0
            ex = ax + ar * math.cos(t) * ca - ar * .38 * math.sin(t) * sa
            ey = ay + ar * math.cos(t) * sa + ar * .38 * math.sin(t) * ca
            e = _ell_pts(ex, ey, 2.2, 2.2, 12)
            cv.obj([e], 1.5)
            cv.heavy([(ex - 1, ey), (ex + 1, ey)])
    nr = max(1.8, ar * .14)
    for i, (dx, dy) in enumerate(((-.8, -.6), (.8, -.6), (-.8, .7), (.8, .7))):
        px, py = ax + dx * nr, ay + dy * nr
        p = _ell_pts(px, py, nr, nr, 16)
        cv.obj([p], 1.)
        if i % 2 == 0:
            cv.line(hatch_poly(p, 0, 1.2))
        else:
            cv.hair(clip_outside(hatch_poly(p, 45, 1.5), px - nr * .4, py - nr * .4, nr * .6))

    # distant swell of prairie, a grain elevator and a shelterbelt on it
    hills = [(X - 2, hz + 1)] + [(X + W * t / 30, hz - S * (.03 + .025 * math.sin(t / 30 * 9 + seed % 7) + .02 * math.sin(t / 30 * 23)))
                                for t in range(31)] + [(X + W + 2, hz + 1)]
    cv.obj([hills], .5)
    cv.hair(hatch_poly(hills, 0, 1.5, .4))
    if not tiny:
        ex, eh, ew = X + W * .1, H * .2, W * .07
        eb = hz + 1
        tower = [(ex, eb), (ex, eb - eh), (ex + ew / 2, eb - eh - ew * .45), (ex + ew, eb - eh), (ex + ew, eb)]
        cv.obj([tower], 1.)
        for k in range(1, 7):
            yy = eb - eh * k / 7
            cv.hair([(ex, yy), (ex + ew * .55, yy)])
        cv.line(hatch_poly(tower, 90, 1.5, .2, .1)[int(len(hatch_poly(tower, 90, 1.5)) * .55):])
        cup = rect(ex + ew * .3, eb - eh - ew * .7, ew * .4, ew * .3)
        cv.obj([cup + [], [(ex + ew * .25, eb - eh - ew * .7), (ex + ew / 2, eb - eh - ew * .95), (ex + ew * .75, eb - eh - ew * .7)]], 1.)
        cv.hair(hatch_poly(cup, 90, 1.5))
        annex = rect(ex + ew, eb - eh * .45, ew * .8, eh * .45)
        cv.obj([annex], 1.)
        cv.hair(hatch_poly(annex, 0, 2))
        # shelterbelt of poplars
        for i in range(9):
            tx = X + W * (.22 + i * .028)
            tr = S * (.022 + .008 * ((i * 7 + seed) % 3))
            blob = _ell_pts(tx, hz - tr * .9, tr, tr * 1.1, 14)
            cv.obj([blob], .5)
            cv.hair(clip_outside(hatch_poly(blob, 70, 1.5), tx - tr * .5, hz - tr * 1.4, tr * .6))

    # the field: dark distant band, then furrows running to the vanishing point
    field = [(X - 2, hz), (X + W + 2, hz), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([field], 1.)
    yy = hz + 1.5
    while yy < hz + H * .07:
        cv.hair([(X - 2, yy), (X + W + 2, yy)])
        yy += 1.5
    vx = X + W * .52
    y0 = hz + H * .07
    cv.line([(X - 2, y0), (X + W + 2, y0)])
    for k in range(-26, 27):
        bx = vx + k * W * .055
        f0 = 0.
        p0 = (vx + (bx - vx) * f0, y0)
        cv.hair([(vx + (bx - vx) * .0 + k * W * .012, y0), (bx, Y + H + 2)])
    # stubble ticks between the furrows
    for j in range(5):
        yt = y0 + (Y + H - y0) * (j + .5) / 5
        cv.hair([(X - 2, yt), (X + W + 2, yt)])

    # the plant
    gb = hz + H * .05
    px = X + W * .5
    cw_, cb = W * .2, H * .17
    cold = rect(px, gb - cb, cw_, cb)
    cv.obj([cold], 1.)
    cv.hair(hatch_poly(cold, 90, 2, .5))
    cv.line(hatch_poly(rect(px + cw_ * .7, gb - cb, cw_ * .3, cb), 90, 1.5, .3))
    if not tiny:
        for k in range(1, 3):
            cv.line([(px, gb - cb * k / 3), (px + cw_, gb - cb * k / 3)])
        door = rect(px + cw_ * .12, gb - cb * .35, cw_ * .16, cb * .35)
        cv.obj([door], 1.)
        cv.line(hatch_poly(door, 0, 1.2))
    roof = [(px - 2, gb - cb), (px + cw_ / 2, gb - cb - cb * .25), (px + cw_ + 2, gb - cb)]
    cv.obj([roof], 1.)
    cv.hair(hatch_poly(roof, 0, 1.5))
    # distillation columns
    cols = [(px + cw_ * .05, W * .055, H * .44), (px + cw_ * .45, W * .045, H * .34), (px - W * .07, W * .04, H * .27)]
    for i, (cx0, cwid, ch_) in enumerate(cols):
        cylinder(cv, cx0, cx0 + cwid, gb - ch_, gb - cb * (.0 if i == 2 else .6), (.18, .45, .7) if not tiny else ())
        if not tiny:
            lad = cx0 + cwid + 1.5
            cv.obj([], 0)
            cv.hair([(lad, gb - ch_ + 4), (lad, gb - cb * .6)])
            cv.hair([(lad + 2, gb - ch_ + 4), (lad + 2, gb - cb * .6)])
    # pipe rack
    if not tiny:
        rx0, rx1, ry = px - W * .1, px + cw_ + W * .2, gb - cb * .42
        for k in range(5):
            xx = rx0 + (rx1 - rx0) * k / 4
            cv.obj([], 0)
            cv.line([(xx, ry), (xx, gb)])
        pipe = [(rx0, ry - 2.5), (rx1, ry - 2.5), (rx1, ry), (rx0, ry)]
        cv.obj([pipe], 1.)
        cv.hair([(rx0, ry - .9), (rx1, ry - .9)])
    # liquefier bullet tanks
    for k in range(2 if not tiny else 1):
        tx0 = px + cw_ + W * .03
        tl = W * .22
        th = H * .055 + 1
        ty = gb - th * (1.15 * k + 1) - 1
        bullet = ([(tx0 + th / 2 + th / 2 * math.cos(a), ty + th / 2 + th / 2 * math.sin(a)) for a in [PI / 2 + PI * i / 10 for i in range(11)]]
                  + [(tx0 + tl - th / 2 + th / 2 * math.cos(a), ty + th / 2 + th / 2 * math.sin(a)) for a in [-PI / 2 + PI * i / 10 for i in range(11)]])
        cv.obj([bullet], 1.)
        yy = ty + th * .45
        while yy < ty + th:
            cv.hair([(tx0, yy), (tx0 + tl, yy)])
            yy += 1.5
        cv.line([(tx0 + th * .4, ty + th - .8), (tx0 + tl - th * .4, ty + th - .8)])
        for sx in (.25, .75):
            leg = rect(tx0 + tl * sx - 1.5, ty + th - .5, 3, th * .15 + 1)
            cv.obj([leg], .5)
    # flare stack with its flame
    fx = X + W * .92
    ftop = hz - H * .3
    cv.obj([rect(fx - 1.2, ftop, 2.4, gb - ftop)], 1.)
    cv.hair([(fx, ftop), (fx, gb)])
    if not tiny:
        for k in range(1, 6):
            yy = ftop + (gb - ftop) * k / 6
            cv.hair([(fx - 4, yy + 5), (fx, yy)])
            cv.hair([(fx + 4, yy + 5), (fx, yy)])
        def flame(k, lean):
            pts = []
            for i in range(25):
                t = TAU * i / 24
                yy = -math.cos(t)
                hgt = (1 - yy) / 2
                x = math.sin(t) * S * .028 * k * (1 - hgt) ** .7 * (1 + hgt * 1.5) + lean * S * .03 * hgt ** 2
                pts.append((fx + x, ftop - 1 - S * .11 * k * hgt))
            return pts
        f1 = flame(1., -1)
        cv.obj([f1], 1.)
        cv.hair(clip_outside(hatch_poly(f1, 75, 1.5), fx - S * .005, ftop - S * .035, S * .022))
        f2 = flame(.5, -.6)
        cv.obj([f2], .5)

    # wellhead "christmas tree" in the foreground, the balloon tethered to it, and the dog
    wx, wb = X + W * .3, hz + H * .24
    wh = H * .12
    if not tiny:
        pad = rect(wx - S * .07, wb - 2, S * .14, 4)
        cv.obj([pad], 1.)
        cv.hair(hatch_poly(pad, 0, 1.5))
        stem = rect(wx - 2.5, wb - wh, 5, wh)
        cv.obj([stem], 1.)
        cv.line([(wx + 1.5, wb - wh), (wx + 1.5, wb)])
        for f in (.25, .6):
            yv = wb - wh * f
            arm = rect(wx - S * .05, yv - 2, S * .1, 4)
            cv.obj([arm], 1.)
            cv.hair(hatch_poly(arm, 0, 1.5))
            for sx in (-1, 1):
                wv = _ell_pts(wx + sx * S * .05, yv, 1.6, 3.6, 12)
                cv.obj([wv], 1.)
        cap = _ell_pts(wx, wb - wh - 2, 4.5, 2.2, 14)
        cv.obj([cap], 1.)
        cv.hair(hatch_poly(cap, 0, 1.5))
        # the dog, sitting by the wellhead, looking up at the balloon
        ds = max(10., S * .12)
        dx0, dy0 = wx + S * .075, wb - ds
        dogp = [(dx0 + u * ds, dy0 + v * ds) for u, v in DOG]
        cv.obj([dogp], 1.)
        cv.hair(hatch_poly(dogp, 70, 1.5))
        cv.hair(hatch_poly(dogp, -20, 3.))
    # the balloon
    bx, by = X + W * .3, Y + H * (.24 if not tiny else .3)
    br = S * (.12 if not tiny else .16)
    tie = (bx + br * .05, by + br * 1.18)
    string = [(tie[0] + math.sin(t * 9) * S * .012 * t, tie[1] + (wb - wh - 4 - tie[1]) * t) for t in [i / 30 for i in range(31)]]
    if not tiny:
        cv.obj([], 0)
        cv.line(string)
    ball = [(bx + br * math.cos(a) * (1 - .1 * max(0, math.sin(a))), by + br * math.sin(a) * (1.08 if math.sin(a) > 0 else 1)) for a in [TAU * i / 48 for i in range(48)]]
    knot = [(tie[0] - 2, tie[1] + 1.5), (tie[0], tie[1] - 2), (tie[0] + 2, tie[1] + 1.5)]
    cv.obj([ball, knot], 1.)
    shade_round(cv, ball, bx, by, br)
    cv.hair([_ell_pts(bx, by, br * f, br, 30, -PI / 2, PI / 2) for f in (.35, .75)])
    cv.obj([_ell_pts(bx - br * .45, by - br * .45, br * .13, br * .2, 12)], 0)
    if not tiny:
        # a P monogram reflected in the balloon's highlight band
        pass
    return cv.svg()


def vignette_clipped(cid, X, Y, W, H, clip_d, seed):
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{scene(X, Y, W, H, seed)}</g>')


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
        o.append(f'<path d="{_ell_d(cx, cy, rx + 1, ry + 1)}" fill="#fff" stroke="none"/>')
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
        o.append(f'<path d="{_ell_d(cx, cy, rx + 1, ry + 1)}" fill="#fff" stroke="none"/>')
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
    o.append(f'<path d="{_ell_d(cx, cy, rx + 1, ry + 1)}" fill="#fff" stroke="none"/>')
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
    """North American Helium: the Stewart Valley purification plant on the prairie, a helium
    balloon rising from the wellhead and a radiant helium atom for a sun, in the inlaid
    medallion; the dog at the wellhead and a "P" monogram roundel in the scroll (the eggs)."""
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)

    def sc(x, y, ww, hh, mode):
        X, Y, W, H = x - 2, y - 2, ww + 4, hh + 4
        return vignette_clipped("mk%d" % int(hh * 10), X, Y, W, H, _rect_d(X, Y, W, H), seed)
    return kk_plate(w, h, sc, egg="P", seed=seed)
