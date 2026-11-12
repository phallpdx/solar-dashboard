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
    cv.obj([], 0)
    y = Y - 1
    while y < hz:
        f = (y - Y) / max(1, hz - Y)
        cv.hair([(X - 2, y), (X + W + 2, y)])
        y += 1.5 if f < .3 else (2. if f < .75 else 3.)
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
        cv.heavy(hatch_poly(dogp, 60, 1.2))
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


# ------------------------------------------------------------------ lettering + tablet
STROKES = {
    "H": [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .5), (1, .5)]],
    "E": [[(1, 0), (0, 0), (0, 1), (1, 1)], [(0, .5), (.75, .5)]],
    "L": [[(0, 0), (0, 1), (1, 1)]],
    "I": [[(.5, 0), (.5, 1)]],
    "U": [[(0, 0), (0, .75), (.25, 1), (.75, 1), (1, .75), (1, 0)]],
    "M": [[(0, 1), (0, 0), (.5, .6), (1, 0), (1, 1)]],
}


def letter_along(centre, word, h):
    """Block capitals drawn as 1 px paths, spaced along the banner's centre line."""
    n = len(centre)
    L = [0.]
    for i in range(1, n):
        L.append(L[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    tot = L[-1]
    lw, gap = h * .62, h * .55
    span = len(word) * lw + (len(word) - 1) * gap
    s0 = (tot - span) / 2

    def at(s):
        for i in range(1, n):
            if L[i] >= s:
                f = (s - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                return (centre[i - 1][0] + (centre[i][0] - centre[i - 1][0]) * f,
                        centre[i - 1][1] + (centre[i][1] - centre[i - 1][1]) * f)
        return centre[-1]
    d = []
    for k, ch in enumerate(word):
        sx = s0 + k * (lw + gap)
        for st in STROKES[ch]:
            pts = []
            for u, v in st:
                px, py = at(sx + u * lw)
                pts.append((px, py - h / 2 + v * h))
            d.append(_d(pts, tol=0))
    return f'<path d="{"".join(d)}" stroke="#000" stroke-width="1.5" fill="none" stroke-linecap="square"/>'


def tablet_chart(tx, ty, tw, th, seed):
    """The sunk tablet: ruled, with the helium spot price climbing to nearly 3x since March."""
    o = []
    x0, y0, w, h = tx + 3, ty + 3, tw - 5, th - 5
    o.append(f'<path d="{"".join(_d(p, tol=0) for p in hatch_poly(rect(x0, y0, w, h), 0, 2, .5))}" stroke="#000" stroke-width=".5"/>')
    rng = random.Random(seed)
    m = 18
    bw_ = (w - 22) / m
    bars, tops = [], []
    for k in range(m):
        f = k / (m - 1)
        v = (1 + 2 * f ** 1.6) / 3 * (1 + (rng.random() - .5) * .08)
        bh = (h - 2) * min(1., v)
        bx = x0 + 4 + k * bw_
        bars.append(rect(bx, y0 + h - bh, bw_ * .6, bh))
        tops.append((bx + bw_ * .3, y0 + h - bh - 1.5))
    o.append(f'<path d="{"".join(_d(b, True, 0) for b in bars)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{"".join(_d(p, tol=0) for b in bars for p in hatch_poly(b, 90, 1.5, .3))}" stroke="#000" stroke-width=".5"/>')
    ex, ey = x0 + w - 3, y0 + 1.5
    o.append(f'<path d="M{_n(ex)},{_n(ey)}l-6,-2.5v5z" fill="#000" stroke="none"/>')
    return "".join(o)


# ------------------------------------------------------------------ layouts (copied from the house frame)
def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("hb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip_d = _d(_ell_pts(cx, cy, rx - 3.5, ry - 3.5, 64), True)
    o.append(vignette_clipped(C._uid("hbv", w, h, seed), cx - rx, cy - ry, 2 * rx, 2 * ry, clip_d, seed))
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _cart_field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .4, gh * 1.45)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("hm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c.split('<path d="', 2)[0] + '<path d="' + c.split('<path d="', 2)[1])
    o.append(vignette_clipped(C._uid("hmv", w, h, seed), *_cart_field(cx, cy, cw, gh + 4), inner, seed))
    o.append('<path d="' + c.split('<path d="', 2)[2])
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _banner(cx, cy, w, h, arch, seed):
    svg, centre = C.ribbon_banner(cx, cy, w, h, arch, seed)
    return svg + letter_along(centre, "HELIUM", h * .5)


def _layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # light ruled sky behind the breaking-out crest so no bare paper shows
    o.append(dark_ground((0, 0, w, h), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
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
    o.append(C._clip(C._uid("ht", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    parts = c.split('<path d="', 2)
    o.append(parts[0] + '<path d="' + parts[1])
    o.append(vignette_clipped(C._uid("htv", w, h, seed), *_cart_field(cx, cy, cw, ch), inner, seed))
    o.append('<path d="' + parts[2])
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    o.append(_banner(cx, cy + ch * .47, cw * 1.4, min(16, ph * .05), .04, rng.randrange(1 << 20)))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(tablet_chart(tx, ty, tw, th, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("hf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed, .9)
    else:
        body = _layout_tall(w, h, seed, .8 if h > 470 else 1.)
    return C.svg_doc(w, h, body)
