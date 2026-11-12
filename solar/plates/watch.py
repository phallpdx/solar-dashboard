"""On screen (watch): the picture palace.

A carved acanthus frame (house style, engraving_codex) round a picture palace seen from the back
row: a swagged valance and two tied-back curtains with deep folds, the projector's beam fanning over
the audience to a screen showing tonight's classic -- a moonlit old house on a hill (Psycho) with a
heron crossing the moon. Easter egg: in the front row, Parker, his little one and his dog watching.
The pedestal tablet carries a strip of film whose frames are a Muybridge sequence of the dog running.
Short plates: a filmstrip moulding over a scroll frieze round a carved film reel.
"""
import sys
import math
import random
import engraving_codex as C

_d, _n, _ell = C._d, C._n, C._ell_pts
PI, TAU = math.pi, 2 * math.pi
CR = ' shape-rendering="crispEdges"'


def _poly_path(polys, **kw):
    if str(kw.get("fill", "")).startswith("url(") and "_p" not in kw:
        kw2 = dict(kw); kw2["fill"] = "#fff"; kw2["stroke"] = "none"; kw2.pop("stroke_width", None)
        return _poly_path(polys, **kw2) + _poly_path(polys, **dict(kw, _p=1))
    kw.pop("_p", None)
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<path d="{"".join(_d(p, True, 0) for p in polys)}" {attrs}/>'


def _lerp(a, b, t):
    return a + (b - a) * t


def _moon_age(date):
    try:
        y, m, d = (int(v) for v in date[:10].split("-"))
    except Exception:
        return 10.
    # days since a known new moon (2000-01-06), modulo the synodic month
    import datetime
    days = (datetime.date(y, m, d) - datetime.date(2000, 1, 6)).days
    return days % 29.530588


# ----------------------------------------------------------------------------------------------
# motifs
# ----------------------------------------------------------------------------------------------

def _dog_head(cx, cy, s, flip=False):
    """3/4 view from behind: round skull, two pricked ears, a snout turned to one side."""
    P = [(-.7, 1.25), (-.92, .45), (-1.0, -.2), (-.86, -.72), (-.8, -1.65), (-.38, -1.0), (.08, -1.05),
         (.42, -1.8), (.66, -.85), (.9, -.48), (1.62, -.3), (1.82, -.02), (1.6, .3), (.98, .45), (.8, 1.25)]
    k = -1 if flip else 1
    return [(cx + k * x * s, cy + y * s) for x, y in P]


def _running_dog(x, y, s, pose):
    """Tiny side silhouette (s = body height); two Muybridge poses: 0 stretched, 1 gathered."""
    if pose == 0:
        P = [(0, .1), (.3, -.05), (.62, -.08), (.78, -.3), (.86, -.5), (1.02, -.42), (1.2, -.3), (1.15, -.2),
             (.95, -.18), (.9, .05), (1.25, .45), (1.15, .5), (.8, .2), (.45, .22), (.1, .45), (-.25, .62),
             (-.3, .52), (-.02, .3), (-.15, .12), (-.45, -.05), (-.45, -.12)]
    else:
        P = [(0, .05), (.3, -.1), (.62, -.12), (.76, -.35), (.86, -.55), (1.0, -.47), (1.16, -.35), (1.1, -.25),
             (.93, -.22), (.85, .1), (.62, .55), (.52, .52), (.6, .18), (.35, .25), (.32, .6), (.2, .58),
             (.12, .22), (-.12, .1), (-.4, -.15), (-.38, -.2)]
    return [(x + px * s * 1.6, y + py * s * 1.6) for px, py in P]


def _heron(cx, cy, s):
    """A great blue heron in flight: neck folded, legs trailing, broad wings."""
    P = [(-1.9, .05), (-1.2, -.05), (-.7, -.1), (-.4, -.9), (.1, -1.3), (.35, -1.1), (.05, -.6), (.2, -.2),
         (.55, -.3), (.75, -.5), (.95, -.55), (1.5, -.5), (.95, -.4), (.7, -.15), (.4, .1), (.15, .55),
         (-.25, .9), (-.15, .25), (-.7, .15), (-1.9, .15)]
    return [(cx + x * s, cy + y * s) for x, y in P]


def _house(x0, yb, u):
    """The old house on the hill, in silhouette: returns (black polys, lit-window rects)."""
    R = lambda a, b, c, d: [(x0 + a * u, yb + b * u), (x0 + c * u, yb + b * u), (x0 + c * u, yb + d * u), (x0 + a * u, yb + d * u)]
    T = lambda pts: [(x0 + a * u, yb + b * u) for a, b in pts]
    black = [R(0, 0, 6, -4.2),
             T([(-.4, -4.1), (6.4, -4.1), (5.7, -5.9), (.3, -5.9)]),
             R(5.9, 0, 8.6, -6.6),
             T([(5.6, -6.5), (8.9, -6.5), (7.25, -9.6)]),
             R(1.1, -5.8, 1.7, -6.9),
             R(-1.8, 0, 0, -2.2), T([(-2.1, -2.1), (.2, -2.1), (.2, -2.9)]),
             R(2.6, -5.8, 3.6, -7.0), T([(2.4, -6.9), (3.8, -6.9), (3.1, -7.7)])]
    win = [R(.7, -2.9, 1.4, -1.6), R(2.6, -2.9, 3.3, -1.6), R(4.5, -2.9, 5.2, -1.6), R(6.9, -5.3, 7.7, -3.9)]
    lit = [R(6.9, -5.3, 7.7, -3.9)]
    return black, win, lit


def film_reel(cx, cy, R, cv=None):
    """A carved film reel: wound film round the rim, six cut-outs with bevels, hub."""
    o = []
    rim = _ell(cx, cy, R, R, 72)
    o.append(_poly_path([rim], fill="#fff", stroke="#000", stroke_width="1.5"))
    # the wound film: concentric hairlines, tight
    rr = []
    r = R - 1.5
    while r > R * .78:
        q = _ell(cx, cy, r, r, 72)
        rr.append(_d(q + [q[0]], tol=.15))
        r -= 1.5
    o.append(f'<path d="{"".join(rr)}" stroke="#000" stroke-width=".5" fill="none"/>')
    q = _ell(cx, cy, R * .76, R * .76, 72)
    o.append(f'<path d="{_d(q + [q[0]], tol=.15)}" stroke="#000" stroke-width="1" fill="none"/>')
    # the flange face: shaded lower right with 45 deg hatch for volume
    face = [(cx + R * .74 * math.cos(a), cy + R * .74 * math.sin(a)) for a in [(-PI / 4) + PI * i / 30 for i in range(31)]]
    o.append(f'<path d="{C.hatch_d(face, 45, 2)}" stroke="#000" stroke-width=".5" fill="none"/>')
    holes, bev = [], []
    for i in range(6):
        a = TAU * i / 6 - PI / 2
        hx, hy = cx + R * .47 * math.cos(a), cy + R * .47 * math.sin(a)
        hr = R * .2
        holes.append(_ell(hx, hy, hr, hr, 28))
        arc = _ell(hx, hy, hr + 1.2, hr + 1.2, 18, PI * .75, PI * 1.75)
        bev.append(_d(arc, tol=.1))
    o.append(_poly_path(holes, fill="#000", stroke="none"))
    o.append(f'<path d="{"".join(bev)}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(_poly_path([_ell(cx, cy, R * .16, R * .16, 24)], fill="#000", stroke="none"))
    o.append(_poly_path([_ell(cx, cy, R * .07, R * .07, 12)], fill="#fff", stroke="none"))
    return "".join(o)


def filmstrip(x, y, w, h, frames=True, seed=0):
    """A strip of 35 mm film: black base, sprocket holes top and bottom, frames between."""
    o = [f'<path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="#000" stroke="none"/>']
    if not frames:
        hp = 4.
        holes = []
        k = x + 1.5
        while k + 2 < x + w:
            holes.append([(k, y + h / 2 - 1), (k + 2, y + h / 2 - 1), (k + 2, y + h / 2 + 1), (k, y + h / 2 + 1)])
            k += hp
        o.append(_poly_path(holes, fill="#fff", stroke="none"))
        return "".join(o)
    band = max(2.5, h * .2)
    hs = max(1., band - 1.5)
    hp = hs * 2 + .5
    holes = []
    for yy in (y + (band - hs) / 2, y + h - band + (band - hs) / 2):
        k = x + 1
        while k + hs < x + w - .5:
            holes.append([(k, yy), (k + hs * 1.1, yy), (k + hs * 1.1, yy + hs), (k, yy + hs)])
            k += hp
    o.append(_poly_path(holes, fill="#fff", stroke="none"))
    fh = h - 2 * band
    fw = fh * 1.35
    n = max(1, int((w - 2) / (fw + 1.5)))
    fw = (w - 2 - 1.5 * (n - 1)) / n
    cells, dogs = [], []
    for i in range(n):
        fx = x + 1 + i * (fw + 1.5)
        cells.append([(fx, y + band), (fx + fw, y + band), (fx + fw, y + band + fh), (fx, y + band + fh)])
        s = fh * .32
        dx = fx + fw * (.25 + .5 * ((i % 5) / 5.))
        dogs.append(_running_dog(dx, y + band + fh * .5, s, i % 2))
    o.append(_poly_path(cells, fill=C.pat("L"), stroke="#fff", stroke_width=".5"))
    # the ground line in each frame
    gl = "".join(f"M{_n(c[0][0] + 1)},{_n(c[2][1] - fh * .14)}h{_n(fw - 2)}" for c in cells)
    o.append(f'<path d="{gl}" stroke="#000" stroke-width=".5"/>')
    o.append(_poly_path(dogs, fill="#000", stroke="none"))
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# the picture palace vignette
# ----------------------------------------------------------------------------------------------

def _curtain(cv, x_edge, top, tie_y, bot, w_top, w_tie, w_bot, side, folds=5):
    """A drape hanging from `top`, gathered at a tieback, flaring to `bot`. side +1: hangs from the
    left edge (inner edge to the right); -1 the mirror."""
    N = 60

    def width(t):  # t 0 top .. 1 bottom
        tt = (tie_y - top) / (bot - top)
        if t <= tt:
            u = t / tt
            return _lerp(w_top, w_tie, (1 - math.cos(PI * u)) / 2)
        u = (t - tt) / (1 - tt)
        return _lerp(w_tie, w_bot, math.sin(PI / 2 * u) ** .8)

    def pt(f, t):
        yy = _lerp(top, bot, t)
        ww = width(t)
        wav = .6 * math.sin(f * folds * TAU + t * 3) * (1 - abs(f - .5))
        return (x_edge + side * (f * ww + wav), yy)

    outline = [pt(0, i / N) for i in range(N + 1)] + [pt(1, 1 - i / N) for i in range(N + 1)]
    outline[0] = (x_edge - side * 2, top)
    outline[N] = (x_edge - side * 2, bot)
    cv.obj([outline], 1.)
    # fold lines, spaced 1.6 px at the tieback; extra lines fill in above and below it
    w_min = min(w_tie, w_top, w_bot)
    base = 1.6 / w_min
    tt = (tie_y - top) / (bot - top)
    f = base
    k = 0
    while f < .999:
        tone = .5 - .5 * math.cos(f * folds * TAU)
        if tone > .35 or k % 2 == 0:
            pl = [pt(f, i / N) for i in range(N + 1)]
            if tone > .82:
                cv.line(pl)
            else:
                cv.hair(pl)
        # upper and lower in-betweens where the drape is wide
        g = f + base / 2
        tone2 = .5 - .5 * math.cos(g * folds * TAU)
        if tone2 > .45:
            cv.hair([pt(g, i / N) for i in range(0, int(N * tt * .7) + 1)])
            cv.hair([pt(g, i / N) for i in range(int(N * (tt + (1 - tt) * .4)), N + 1)])
        f += base
        k += 1
    # the gathered tieback: a band with cross shading and a tassel
    ty = tie_y
    band = [pt(0, tt - .025), pt(1, tt - .025), pt(1, tt + .025), pt(0, tt + .025)]
    cv.obj([band], 1.)
    cv.hair(C.hatch_poly(band, 45 * side, 1.5))
    tx, _ = pt(1, tt)
    tass = [(tx + side * 1, ty)] + [(tx + side * (1 + 3.2 * math.sin(PI * i / 10)), ty + 2 + 9 * i / 10) for i in range(11)]
    cv.obj([tass], 1.)
    cv.hair([[(tx + side * (1 + 3.2 * math.sin(PI * j / 6) * .8), ty + 5), (tx + side * (1 + 3.2 * math.sin(PI * j / 6) * .8), ty + 11)] for j in range(1, 6)])


def _valance(cv, x, y, w, h, n=5):
    """A swagged pelmet: n swags hanging across the top, folds following the sag."""
    sag = h * .55
    lower = []
    for i in range(n * 16 + 1):
        u = i / (n * 16)
        k = (u * n) % 1
        lower.append((x + w * u, y + h - sag + sag * math.sin(PI * k)))
    poly = [(x - 1, y - 1), (x + w + 1, y - 1)] + lower[::-1]
    cv.obj([poly], 1.)
    ls = []
    for j in range(1, 9):
        s = j / 9.
        for i in range(n):
            pl = []
            for q in range(17):
                k = q / 16
                xx = x + w * (i + k) / n
                yy = y + (h - sag) * s ** .7 + sag * s * math.sin(PI * k)
                pl.append((xx, yy))
            ls.append(pl)
    cv.hair(ls)
    # shadow under each swag's lower edge
    for d in (1., 1.9):
        sh = []
        for i in range(n):
            sh.append([(x + w * (i + q / 16) / n, y + h - sag + (sag - d) * math.sin(PI * q / 16) - d * .2)
                       for q in range(2, 15)])
        cv.line(sh)
    # rosettes at the swag joins
    for i in range(n + 1):
        xx = x + w * i / n
        r = max(2., h * .18)
        disc = _ell(xx, y + h - sag + r * .2, r, r, 18)
        cv.obj([disc], 1.)
        cv.hair(C.hatch_poly(disc, 45, 1.5, inset=0))


def theatre(x, y, w, h, clip_d, ctx, seed=0):
    """The picture palace, filling the box (x, y, w, h), clipped to clip_d."""
    rng = random.Random(seed)
    o = [C.dark_ground((x - 2, y - 2, w + 4, h + 4), "G")]
    S = min(w, h)
    # screen
    sx0, sx1 = x + w * .21, x + w * .79
    sy0, sy1 = y + h * .17, y + h * .58
    sw, sh = sx1 - sx0, sy1 - sy0
    # beam from behind the audience to the screen foot
    ox, oy = x + w * .5, y + h * 1.08
    beam = [(ox - 3, oy), (sx0 - 2, sy1 + 1), (sx1 + 2, sy1 + 1), (ox + 3, oy)]
    o.append(_poly_path([beam], fill=C.pat("L"), stroke="none"))
    rays = []
    for i in range(15):
        t = (i + .5) / 15
        rays.append(_d([(ox, oy), (_lerp(sx0, sx1, t), sy1 + 1)], tol=0))
    o.append(f'<path d="{"".join(rays)}" stroke="#000" stroke-width=".5"/>')
    # screen surround: black, then sky
    o.append(_poly_path([[(sx0 - 3, sy0 - 3), (sx1 + 3, sy0 - 3), (sx1 + 3, sy1 + 3), (sx0 - 3, sy1 + 3)]], fill="#000"))
    scr = [(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)]
    o.append(_poly_path([scr], fill=C.pat("L"), stroke="#fff", stroke_width="1"))
    o.append(_poly_path([[(sx0, sy0), (sx1, sy0), (sx1, sy0 + sh * .3), (sx0, sy0 + sh * .3)]], fill=C.pat("M")))
    # moon with the date's phase, and the heron crossing it
    mr = sh * .19
    mx, my = sx0 + sw * .72, sy0 + sh * .3
    disc = _ell(mx, my, mr, mr, 40)
    o.append(_poly_path([_ell(mx, my, mr + 2, mr + 2, 40)], fill="#000"))
    o.append(_poly_path([disc], fill="#fff", stroke="#000", stroke_width=".5"))
    age = _moon_age(ctx.get("date", ""))
    ph = (1 - math.cos(TAU * age / 29.53)) / 2  # illuminated fraction
    waxing = age < 14.77
    term = 1 - 2 * ph  # terminator ellipse x-scale
    dark = []
    for i in range(41):
        a = -PI / 2 + PI * i / 40
        dark.append((mx + (-1 if waxing else 1) * mr * math.cos(a), my + mr * math.sin(a)))
    for i in range(41):
        a = PI / 2 - PI * i / 40
        dark.append((mx + (-1 if waxing else 1) * mr * term * math.cos(a), my + mr * math.sin(a)))
    if ph < .97:
        o.append(f'<path d="{C.hatch_d(dark, 45, 1.5)}" stroke="#000" stroke-width=".5"/>')
    # craters
    cr = "".join(_d(_ell(mx + mr * a, my + mr * b, mr * c, mr * c, 10), True, 0) for a, b, c in ((-.3, -.25, .18), (.25, .2, .14), (.1, -.45, .09)))
    o.append(f'<path d="{cr}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(_poly_path([_heron(mx - mr * .1, my + mr * .05, mr * .5)], fill="#000"))
    # the hill and the old house
    crest_x = sx0 + sw * .3
    hill = [(sx0, sy1), (sx0, sy0 + sh * .72)]
    for i in range(25):
        u = i / 24
        xx = _lerp(sx0, sx1, u)
        yy = sy0 + sh * (.6 + .34 * (u - .3) ** 2 * (1 if u > .3 else 2.2)) - sh * .02 * math.sin(u * 19)
        hill.append((xx, yy))
    hill.append((sx1, sy1))
    o.append(_poly_path([hill], fill=C.pat("X"), stroke="#000", stroke_width="1"))
    u = sw * .3 / 11
    hb = sy0 + sh * .6 + 1
    blk, win, lit = _house(crest_x - 4 * u, hb, u)
    o.append(_poly_path(blk, fill="#000"))
    o.append(_poly_path([q for q in win if q not in lit], fill=C.pat("M")))
    o.append(_poly_path(lit, fill="#fff"))
    # a stair down the hill and the long low motel at its foot
    stair = "".join(_d([(crest_x + 2 * u + k * u * .7, hb + k * u * .55), (crest_x + 2 * u + k * u * .7 + u * .45, hb + k * u * .55)], tol=0) for k in range(1, 7))
    o.append(f'<path d="{stair}" stroke="#fff" stroke-width=".5"/>')
    my0 = sy1 - sh * .06
    motel = [(sx0 + sw * .52, my0), (sx1 - sw * .04, my0), (sx1 - sw * .04, my0 - sh * .09), (sx0 + sw * .52, my0 - sh * .09)]
    roof = [(sx0 + sw * .5, my0 - sh * .09), (sx1 - sw * .02, my0 - sh * .09), (sx1 - sw * .06, my0 - sh * .13), (sx0 + sw * .54, my0 - sh * .13)]
    o.append(_poly_path([motel, roof], fill="#000"))
    doors = []
    for k in range(7):
        dx = _lerp(sx0 + sw * .55, sx1 - sw * .09, k / 6)
        doors.append([(dx, my0 - sh * .065), (dx + max(1.5, sw * .018), my0 - sh * .065), (dx + max(1.5, sw * .018), my0 - sh * .02), (dx, my0 - sh * .02)])
    o.append(_poly_path(doors[1::2], fill="#fff"))
    o.append(_poly_path(doors[0::2], fill=C.pat("M")))
    # a scratch of film grain / vignette on the screen corners
    vg = []
    for cxs, cys, a in ((sx0, sy0, 45), (sx1, sy0, -45), (sx0, sy1, -45), (sx1, sy1, 45)):
        tri = [(cxs, cys), (cxs + (sw * .14 if cxs == sx0 else -sw * .14), cys), (cxs, cys + (sh * .2 if cys == sy0 else -sh * .2))]
        vg.append(C.hatch_d(tri, a, 1.5))
    o.append(f'<path d="{"".join(vg)}" stroke="#000" stroke-width=".5"/>')

    # proscenium: curtains and valance (engraved relief on a canvas)
    cv = C.Canvas()
    top = y + h * .1
    tie = y + h * .52
    bot = y + h * .74
    for side, xe in ((1, x - 1), (-1, x + w + 1)):
        _curtain(cv, xe, top - 2, tie, bot, w * .3, w * .1, w * .2, side, folds=5 if w > 150 else 4)
    _valance(cv, x - 2, y - 2, w + 4, h * .14 + 2, n=5 if w > 160 else 4)
    o.append(cv.svg())
    # stage lip with footlights under the screen
    ly = y + h * .64
    o.append(_poly_path([[(x + w * .17, ly), (x + w * .83, ly), (x + w * .86, ly + 4), (x + w * .14, ly + 4)]], fill="#000"))
    o.append(f'<path d="M{_n(x + w * .17)},{_n(ly + .5)}h{_n(w * .66)}" stroke="#fff" stroke-width=".5" stroke-dasharray="1.5 2.5"/>')

    # the audience, seen from behind, rim-lit by the beam
    def row(yh, r, n, x0, x1, specials):
        heads, rims, seats, outl = [], [], [], []
        xs = [_lerp(x0, x1, (i + .5) / n) for i in range(n)]
        for i, hx in enumerate(xs):
            hx += rng.uniform(-r * .25, r * .25)
            kind = specials.get(i, "adult")
            if kind == "dog":
                p = _dog_head(hx, yh + r * .05, r * .92, flip=hx > ox)
                heads.append(p)
                top_a = 0
                rims.append(_d(p[3:10], tol=.1))
                outl.append(_d(p[1:13], tol=.1))
                continue
            rr = r * (.7 if kind == "kid" else 1)
            hy = yh + (r - rr) * 1.6
            heads.append(_ell(hx, hy, rr, rr * 1.12, 28))
            heads.append([(hx - rr * 1.9, hy + rr * 2.6), (hx - rr * 1.7, hy + rr * 1.4), (hx - rr * .5, hy + rr * .9),
                          (hx + rr * .5, hy + rr * .9), (hx + rr * 1.7, hy + rr * 1.4), (hx + rr * 1.9, hy + rr * 2.6)])
            # rim light on the side facing the beam's centre, on the crown
            a0 = -PI * .85 if hx > ox else -PI * .55
            rims.append(_d(_ell(hx, hy, rr - .8, rr * 1.12 - .8, 14, a0, a0 + PI * .4), tol=.1))
            outl.append(_d(_ell(hx, hy, rr + .25, rr * 1.12 + .25, 24, PI * 1.02, PI * 1.98), tol=.1))
            outl.append(_d([(hx - rr * 1.7, hy + rr * 1.4), (hx - rr * .5, hy + rr * .9)], tol=0) + _d([(hx + rr * .5, hy + rr * .9), (hx + rr * 1.7, hy + rr * 1.4)], tol=0))
            if kind == "hat":
                heads.append([(hx - rr * 1.5, hy - rr * .5), (hx + rr * 1.5, hy - rr * .5), (hx + rr * .8, hy - rr * .8),
                              (hx + rr * .7, hy - rr * 1.7), (hx - rr * .7, hy - rr * 1.7), (hx - rr * .8, hy - rr * .8)])
        out = _poly_path(heads, fill="#000")
        out += f'<path d="{"".join(rims)}" stroke="#fff" stroke-width="1" fill="none"/>'
        out += f'<path d="{"".join(outl)}" stroke="#fff" stroke-width=".5" fill="none"/>'
        return out

    rb = max(h * .045, 5.)
    nb = max(5, int(w / (rb * 3.2)))
    o.append(row(y + h * .755, rb, nb, x + w * .02, x + w * .98, {1: "hat", nb - 2: "hat"}))
    # back of the seats in front of the front row: carved velvet tops
    rf = max(h * .066, 7.5)
    nf = max(4, int(w / (rf * 3.4)))
    mid = nf // 2
    egg = {mid - 1: "adult", mid: "kid", mid + 1: "dog"} if (seed % 2 == 0) else {mid - 1: "dog", mid: "kid", mid + 1: "adult"}
    o.append(row(y + h * .855, rf, nf, x - w * .02, x + w * 1.02, egg))
    seat_y = y + h * .95
    seats = [(x - 2, y + h + 4)]
    for i in range(nf * 2 + 1):
        u = i / (nf * 2)
        seats.append((x - 2 + (w + 4) * u, seat_y - (rf * .45 if i % 2 else 0)))
    seats.append((x + w + 2, y + h + 4))
    o.append(_poly_path([seats], fill="#000"))
    o.append(f'<path d="{_d(seats[1:-1], tol=0)}" stroke="#fff" stroke-width=".5"/>')
    cid = C._uid("thr", x, y, w, h)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">' + "".join(o) + "</g>"


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, made bespoke: no blank paper anywhere, film details)
# ----------------------------------------------------------------------------------------------

def _paper(w, h):
    return f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("L")}" stroke="none"/>'


def _layout_band(w, h, seed, ctx):
    o = [_paper(w, h)]
    fs = 7.
    o.append(filmstrip(0, 0, w, fs, frames=False))
    top = fs + 1
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh, C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    o.append(_poly_path([_ell(cx, cy, rx - 2, ry - 2, 64)], fill=C.pat("S")))
    R = ry - 4
    o.append(film_reel(cx, cy, R))
    # film unspooling from the reel to both sides of the medallion
    for sd in (-1, 1):
        fx = cx + sd * R * .7
        fw = rx - R * .7 - 5
        if fw > 6:
            x0 = fx if sd > 0 else fx - fw
            o.append(filmstrip(x0, cy + R * .2, fw, min(8., R * .45), frames=False))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = [_paper(w, h)]
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.5)
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
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = cw / 2 - max(5., min(cw, gh + 4) * .07) * 1.6, (gh + 4) / 2 - max(5., min(cw, gh + 4) * .07) * 1.6
    o.append(theatre(cx - a, cy - b, 2 * a, 2 * b, inner, ctx, seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _banner_face(centre, hh):
    d = "".join(_d([(px, py + off) for px, py in centre[1:-1]], tol=.1) for off in (-hh * .36, 0, hh * .36))
    return f'<path d="{d}" stroke="#000" stroke-width=".5" fill="none"/>'


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = [_paper(w, h)]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 2)},{_n(py0 - 2)}h{_n(pw + 4)}v{_n(ph + 4)}h{_n(-pw - 4)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
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
                   max_n=int(9 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(theatre(cx - a, cy - b, 2 * a, 2 * b, inner, ctx, seed))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .5, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_face(centre, bh / 2))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(filmstrip(tx + 1, ty + 1, tw - 2, th - 2, frames=True, seed=seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.25,
                                       r_scale=1.15, n=2)))
        rr = min(fh * .4, 22)
        o.append(film_reel(w / 2, fy + fh / 2 - 1, rr))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
