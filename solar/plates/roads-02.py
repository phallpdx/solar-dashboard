"""roads-02 "Road cams and slowdowns": a flagger stop on an Oregon two-lane.

The vignette is today's TripCheck list made into one scene: a two-lane highway winding up from the
foreground into the fir-dark Coast Range (OR-127 at Old Cornelius Pass), cones down the centre
line, a flagger in hard hat and striped vest holding up the STOP/SLOW paddle, a TripCheck road
camera on its pole watching from the left shoulder, a diamond FLAGGER AHEAD sign, and a pickup
stopped in the near lane. The two great volutes either side of the cartouche curl into camera
lenses; the ribbon reads PREPARE TO SLOW and the pedestal tablet lists today's routes.
Easter egg: Parker's dog riding in the pickup bed, ears up, looking back over the tailgate."""
import sys
import math
import random
import engraving_codex as C
import engraving_morning as EM

_n, _d, _ell = C._n, C._d, C._ell_pts
PI = math.pi
TAU = 2 * PI

# ------------------------------------------------------------------------------------------------
# lettering: the house stroke font, plus the letters it lacks
# ------------------------------------------------------------------------------------------------
_G = dict(EM._G)
_G["S"] = (5, [("s", [(4.4, 1.1), (3, 0), (1.4, .1), (.5, 1.2), (.8, 2.9), (2.5, 3.9), (4.2, 5),
                      (4.5, 6.8), (3.5, 7.9), (1.7, 8), (.3, 6.9)])])
_G["U"] = (5.6, [("s", [(.9, 0), (.9, 5.4), (1.6, 7.5), (2.8, 8), (4, 7.5), (4.7, 5.4), (4.7, 0)]),
                 ("l", [(0, 0), (1.8, 0)]), ("l", [(3.8, 0), (5.6, 0)])])
_G["K"] = (5.4, [("l", [(.9, 0), (.9, 8)]), ("l", [(4.8, 0), (.9, 4.4)]), ("l", [(2.2, 3), (5, 8)]),
                 ("l", [(0, 0), (1.8, 0)]), ("l", [(0, 8), (1.8, 8)])])
_G["B"] = (5.2, [("l", [(0, 0), (1, 0), (1, 8), (0, 8)]),
                 ("s", [(1, 0), (3.3, 0), (4.3, 1), (4.3, 2.8), (3.2, 3.8), (1, 3.8)]),
                 ("s", [(1, 3.8), (3.5, 3.8), (4.7, 5), (4.7, 6.8), (3.5, 8), (1, 8)])])


def _glyphs(ch):
    adv, strokes = _G.get(ch, _G[" "])
    return adv, [EM._spline(p, False, 4) if k == "s" else list(p) for k, p in strokes]


def text_lines(s, cx, cy, hgt, track=1.3, path=None):
    """Glyph polylines centred on (cx, cy), cap height hgt. path(x) -> y offset lets the line arch."""
    k = hgt / 8
    width = (sum(_G.get(c, _G[" "])[0] + track for c in s) - track) * k
    x = cx - width / 2
    out = []
    for c in s:
        adv, polys = _glyphs(c)
        for p in polys:
            out.append([(x + px * k, cy - hgt / 2 + py * k + (path(x + px * k) if path else 0)) for px, py in p])
        x += (adv + track) * k
    return out, width


def _sw(w):
    return f'fill="none" stroke="#000" stroke-width="{w}"'


# ------------------------------------------------------------------------------------------------
# small drawing helpers (canvas)
# ------------------------------------------------------------------------------------------------

def solid(cv, poly, angle=0.):
    """Black mass: 1 px lines 0.8 px apart, clipped to poly."""
    cv.line(C.hatch_poly(poly, angle, .8))


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def fir(cv, x, yb, hgt, rng, dark=1.):
    """A Douglas fir standing on (x, yb), hgt tall: drooping tiers, lit left, shaded right."""
    n = max(3, int(hgt / 7))
    wid = hgt * .36
    trunk = rect(x - hgt * .025, yb - hgt * .12, hgt * .05, hgt * .12)
    cv.obj([trunk], .5)
    solid(cv, trunk)
    for i in range(n):
        f = i / n
        ty = yb - hgt * (.1 + .9 * (1 - f) ** .95) if i else yb - hgt
        by = yb - hgt * (.1 + .9 * (1 - (i + 1.25) / n) ** .95) if i < n - 1 else yb - hgt * .08
        top = yb - hgt + hgt * .9 * (f ** 1.05)
        ww = wid * (.25 + .75 * (i + 1) / n) * rng.uniform(.9, 1.08)
        y0 = top if i else yb - hgt
        y1 = min(yb - hgt * .06, y0 + hgt * (1.6 / n) + hgt * .05)
        droop = (y1 - y0) * .25
        poly = [(x, y0), (x + ww * .55, y1 - droop * .6), (x + ww, y1 + droop * .2), (x + ww * .6, y1 - droop * .1),
                (x + ww * .2, y1 + droop * .1), (x - ww * .2, y1 + droop * .1), (x - ww * .6, y1 - droop * .1),
                (x - ww, y1 + droop * .2), (x - ww * .55, y1 - droop * .6)]
        cv.obj([poly], .5)
        right = [(x, y0), (x + ww * 1.2, y1 + droop), (x + ww * 1.2, y1 + droop * 2), (x, y1 + droop * 2)]
        cv.hair(C.hatch_poly(_isect_box(poly, right), 75, 1.5 if dark > .5 else 2))
        cv.hair(C.hatch_poly(poly, -20, 3, rng.random() * 3))
    return


def _isect_box(poly, box):
    """Crude clip: keep poly points on the box's x side (box is to the right of x0)."""
    x0 = box[0][0]
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[0] >= x0, b[0] >= x0
        if ina:
            out.append(a)
        if ina != inb:
            t = (x0 - a[0]) / (b[0] - a[0])
            out.append((x0, a[1] + (b[1] - a[1]) * t))
    return out if len(out) > 2 else [(x0, 0), (x0 + .1, 0), (x0, .1)]


# ------------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------------

def scene(x0, y0, W, H, seed=0, detail=2):
    """The flagger stop, filling x0..x0+W, y0..y0+H completely (no blank paper). Returns
    (canvas_svg, extra_svg) - the extra is drawn on top (the paddle)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    top = []
    yh = y0 + H * (.40 if detail else .44)
    yb = y0 + H
    side = 1   # the road bends away to the right in the distance

    def road_y(t):
        return yh + 1.5 + (yb - yh + 2) * t

    def road_hw(t):
        return W * (.006 + .40 * max(0., t) ** 1.1)

    def road_x(t):
        return x0 + W * (.40 + side * .2 * max(0., 1 - t) ** 2.2)

    def at(t, s):
        return (road_x(t) + s * road_hw(t), road_y(t))

    # sky: ruled, denser toward the zenith; clouds
    sky = rect(x0 - 2, y0 - 2, W + 4, yh - y0 + 6)
    cv.obj([sky], 0)
    _sh, _sl = st_sky(x0 - 2, y0 - 2, x0 + W + 2, yh + 4, seed + 13, clouds=[], top_dark=.4)
    cv.hair(_sh)
    cv.line(_sl)
    if detail:
        for k in range(2 + (detail > 1)):
            cx = x0 + W * (.18 + .62 * k / 2 + rng.uniform(-.06, .06))
            cy = y0 + (yh - y0) * rng.uniform(.3, .6)
            cw, ch = W * rng.uniform(.13, .2), (yh - y0) * .11
            pts = []
            for i in range(25):
                a = PI + PI * i / 24
                bump = 1 + .22 * abs(math.sin(a * 3 + k))
                pts.append((cx + cw * math.cos(a), cy + ch * bump * math.sin(a) * 1.6))
            pts += [(cx + cw * .9, cy + ch * .35), (cx - cw * .9, cy + ch * .35)]
            cv.obj([pts], .5)
            cv.hair(C.hatch_poly(pts, 0, 3, 1.5))
            under = [(cx - cw * .85, cy), (cx + cw * .85, cy), (cx + cw * .9, cy + ch * .35), (cx - cw * .9, cy + ch * .35)]
            cv.hair(C.hatch_poly(under, 0, 1.5, .75))

    # Coast Range: far ridge, light, with a fringe of firs on its crest
    ridge = [(x0 - 2, yh + 2)]
    for i in range(41):
        u = i / 40
        ridge.append((x0 + W * u, yh - H * (.09 + .05 * math.sin(u * 5.3 + seed % 5) + .03 * math.sin(u * 13.1))))
    ridge += [(x0 + W + 2, yh + 2)]
    cv.obj([ridge], .5)
    cv.hair(C.hatch_poly(ridge, 0, 1.5, .5))
    if detail:
        for i in range(1, 40, 2 if detail > 1 else 3):
            px, py = ridge[i + 1]
            hh = H * .025 * rng.uniform(.7, 1.2)
            cv.hair([(px - hh * .3, py + .5), (px, py - hh), (px + hh * .3, py + .5)])

    # near hills, left high, right lower; firs on them (back to front)
    for sgn, hgt, ph in ((1, .14, 1.3), (-1, .2, .2)):
        pts = []
        for i in range(31):
            u = i / 30
            xx = x0 + W * (.5 + sgn * .5 * u) if sgn > 0 else x0 + W * (.5 - .5 * u)
            yy = yh + 2 - H * hgt * (u ** .7) * (1 + .15 * math.sin(u * 9 + ph))
            pts.append((xx, yy))
        pts += [(pts[-1][0] + sgn * 2, yh + H * .08), (x0 + W * .5, yh + H * .08)]
        cv.obj([pts], .5)
        cv.hair(C.hatch_poly(pts, 0, 1.5, .75))
        cv.hair(C.hatch_poly(pts, 60 * sgn, 2))
        cv.hair(C.hatch_poly(pts, -60 * sgn, 3))
        if detail:
            nf = 11 if detail > 1 else 6
            for j in range(nf):
                u = (j + .5 + rng.uniform(-.25, .25)) / nf
                if sgn > 0 and u < .3:
                    continue
                k = min(29, int(u * 30))
                fx, fy = pts[k]
                fir(cv, fx, fy + H * .04, H * (.1 + .08 * u) * rng.uniform(.8, 1.15), rng)

    # fields between hills and road: ruled, with rows of grass ticks in perspective
    field = [(x0 - 2, yh + H * .04), (x0 + W + 2, yh + H * .04), (x0 + W + 2, yb + 2), (x0 - 2, yb + 2)]
    cv.obj([field], 0)
    vx, vy = road_x(0), yh + 1
    nr = 70 if detail else 36
    for k in range(-nr, nr + 1):
        bx = road_x(1) + k * W * 2.4 / (2 * nr)
        f = .06 if k % 8 == 0 else (.18 if k % 4 == 0 else (.36 if k % 2 == 0 else .6))
        cv.hair([(vx + (bx - vx) * f, vy + (yb + 2 - vy) * f), (bx, yb + 2)])
    t = .05
    while t < 1.05:
        yy = road_y(t)
        cv.hair([(x0 - 2, yy), (x0 + W + 2, yy)])
        t += .06 + .12 * t
    if detail:
        t = .1
        while t < 1.0:
            yy = road_y(t)
            g = 1 + 5 * t
            sp = 2 + 3.5 * t
            xx = x0 + rng.uniform(0, sp)
            while xx < x0 + W:
                cv.hair([(xx, yy), (xx + g * .25, yy - g)])
                xx += sp * rng.uniform(.7, 1.3)
            t += .04 + .05 * t

    # the road: dark ruled asphalt between white edge lines, dashed centre line
    N = 40
    L = [at(i / N, -1) for i in range(N + 1)]
    R = [at(i / N, 1) for i in range(N + 1)]
    road = L + R[::-1]
    cv.obj([road], 1.)
    cv.hair(C.hatch_poly(road, 0, 1.5, .25))
    # gravel shoulders
    for s0, s1 in ((-1.18, -1.), (1., 1.18)):
        sh = [at(i / N, s0) for i in range(N + 1)] + [at(i / N, s1) for i in range(N, -1, -1)]
        cv.obj([sh], .5)
        if detail:
            t = .08
            while t < 1:
                for k in range(3):
                    px, py = at(t, s0 + (s1 - s0) * rng.random())
                    cv.hair([(px, py), (px + .5, py)])
                t += .015
        cv.hair(C.hatch_poly(sh, 0, 3, 1))
    for s0, s1 in ((-.95, -.9), (.9, .95)):
        strip = [at(i / N, s0) for i in range(N + 1)] + [at(i / N, s1) for i in range(N, -1, -1)]
        cv.obj([strip], 0)
    # centre dashes in perspective
    t = .06
    while t < 1.05:
        dt = .028 + .09 * t
        t1 = min(1.02, t + dt * .45)
        hw = .022
        dash = [at(t, -hw), at(t1, -hw), at(t1, hw), at(t, hw)]
        if road_hw(t) * hw * 2 > .6:
            cv.obj([dash], .5)
        t += dt

    # TripCheck camera on its pole, left shoulder, looking down the road
    if detail:
        cp = at(.42, -1.45)
        ph = H * .42
        pw = max(1.2, W * .008)
        pole = rect(cp[0] - pw / 2, cp[1] - ph, pw, ph)
        cv.obj([pole], .5)
        solid(cv, pole, 90)
        arm_y = cp[1] - ph + H * .02
        al = W * .07
        arm = rect(cp[0], arm_y, al, pw * .7)
        cv.obj([arm], .5)
        solid(cv, arm)
        # housing: a hooded box with lens
        hx, hy = cp[0] + al, arm_y + pw
        bw, bh = W * .055, H * .03
        box = [(hx - bw * .2, hy), (hx + bw, hy + bh * .2), (hx + bw, hy + bh * 1.1), (hx - bw * .2, hy + bh)]
        hood = [(hx - bw * .3, hy - bh * .25), (hx + bw * 1.15, hy - bh * .05), (hx + bw * 1.15, hy + bh * .25), (hx - bw * .3, hy + bh * .05)]
        cv.obj([box], 1.)
        cv.hair(C.hatch_poly(box, 15, 1.5))
        cv.obj([hood], 1.)
        cv.hair(C.hatch_poly(hood, 8, 3, 1))
        lr = bh * .42
        lx, ly = hx + bw + lr * .3, hy + bh * .65
        cv.obj([_ell(lx, ly, lr * .6, lr, 16)[:-1]], 1.)
        solid(cv, _ell(lx, ly, lr * .35, lr * .7, 12)[:-1])
        # solar panel on top of the pole (a nod to his panels)
        sp = [(cp[0] - W * .03, cp[1] - ph - H * .035), (cp[0] + W * .025, cp[1] - ph - H * .05),
              (cp[0] + W * .025, cp[1] - ph - H * .025), (cp[0] - W * .03, cp[1] - ph - H * .01)]
        cv.obj([sp], 1.)
        cv.hair(C.hatch_poly(sp, 90, 1.5))
        cv.hair(C.hatch_poly(sp, -15, 3))
        stub = rect(cp[0] - .5, cp[1] - ph - H * .015, 1, H * .015)
        cv.obj([stub], .5)

    # diamond FLAGGER AHEAD sign, left
    if detail:
        sx, sy = at(.6, -1.12)
        ss = W * .085
        post = rect(sx - .8, sy - ss * 1.6, 1.6, ss * 1.6)
        cv.obj([post], .5)
        solid(cv, post, 90)
        cy_ = sy - ss * 1.6 - ss * .55
        dia = [(sx, cy_ - ss * .62), (sx + ss * .62, cy_), (sx, cy_ + ss * .62), (sx - ss * .62, cy_)]
        cv.obj([dia], 1.5)
        inner = [(sx, cy_ - ss * .5), (sx + ss * .5, cy_), (sx, cy_ + ss * .5), (sx - ss * .5, cy_)]
        cv.obj([inner], .5)
        cv.hair(C.hatch_poly(inner, 45, 3))
        # pictogram flagger
        k = ss * .5
        cv.obj([_ell(sx - k * .05, cy_ - k * .48, k * .1, k * .1, 10)[:-1]], 0)
        solid(cv, _ell(sx - k * .05, cy_ - k * .48, k * .1, k * .1, 10)[:-1])
        body = [(sx - k * .17, cy_ - k * .35), (sx + k * .1, cy_ - k * .35), (sx + k * .08, cy_ + k * .05),
                (sx + k * .16, cy_ + k * .5), (sx + k * .04, cy_ + k * .5), (sx - k * .04, cy_ + k * .15),
                (sx - k * .12, cy_ + k * .5), (sx - k * .24, cy_ + k * .5), (sx - k * .14, cy_ + k * .05)]
        cv.obj([body], 0)
        solid(cv, body)
        cv.line([(sx + k * .08, cy_ - k * .28), (sx + k * .32, cy_ - k * .12)])
        cv.line([(sx + k * .32, cy_ - k * .12), (sx + k * .32, cy_ - k * .55)])
        fl = [(sx + k * .32, cy_ - k * .55), (sx + k * .5, cy_ - k * .5), (sx + k * .32, cy_ - k * .4)]
        cv.obj([fl], 0)
        solid(cv, fl)

    # cones down the centre line, closing the far lane
    nc = 6 if detail > 1 else (4 if detail else 3)
    for j in range(nc):
        t = .28 + .4 * j / max(1, nc - 1)
        px, py = at(t, .04)
        ch = max(2.5, road_hw(t) * .3)
        cw = ch * .32
        cone = [(px - cw * .25, py - ch), (px + cw * .25, py - ch), (px + cw, py - ch * .12), (px - cw, py - ch * .12)]
        base = rect(px - cw * 1.35, py - ch * .14, cw * 2.7, ch * .14)
        cv.obj([base], .5)
        solid(cv, base)
        cv.obj([cone], .5 if ch < 6 else 1.)
        cv.line(C.hatch_poly(cone, 0, 1.5 if ch > 6 else 1.6))
        if ch > 4:
            band = [(px - cw * .5, py - ch * .7), (px + cw * .5, py - ch * .7), (px + cw * .66, py - ch * .5), (px - cw * .66, py - ch * .5)]
            cv.obj([band], .5)
            cv.hair(C.hatch_poly(band, 90, 3))

    # the flagger, right shoulder, facing us, paddle up
    fx, fy = x0 + W * (.75 if detail else .72), y0 + H * (.74 if detail else .8)
    s = H * (.3 if detail else .4)
    _flagger(cv, top, fx, fy, s, detail)

    # the pickup stopped in the near lane, dog in the bed (Easter egg)
    if detail:
        px, py = at(.88, .48)
        tw = road_hw(.88) * .8
        _pickup(cv, px, py, tw, rng, detail)
    return cv.svg(), "".join(top)


def _flagger(cv, top, x, y, s, detail):
    """A flagger standing on (x, y), s tall, facing the viewer, holding the paddle up in his right hand."""
    hw = s * .14
    # legs (work trousers, dark) and boots
    for sg in (-1, 1):
        leg = [(x + sg * hw * .12, y - s * .47), (x + sg * hw * .95, y - s * .47), (x + sg * hw * .9, y - s * .05),
               (x + sg * hw * .25, y - s * .05)]
        cv.obj([leg], 1.)
        cv.hair(C.hatch_poly(leg, 90, 1.5, .75))
        if sg > 0:
            cv.hair(C.hatch_poly(leg, 90, 1.5, 0))
        boot = [(x + sg * hw * .2, y - s * .07), (x + sg * hw * .95, y - s * .07), (x + sg * hw * 1.2, y), (x + sg * hw * .15, y)]
        cv.obj([boot], .5)
        solid(cv, boot)
    # left arm hanging, glove
    arm = [(x - hw * 1.05, y - s * .78), (x - hw * .78, y - s * .78), (x - hw * 1.05, y - s * .45), (x - hw * 1.4, y - s * .46)]
    cv.obj([arm], 1.)
    cv.hair(C.hatch_poly(arm, 70, 1.5))
    # torso: shirt, then the vest with reflective bands
    torso = [(x - hw * 1.05, y - s * .8), (x + hw * 1.05, y - s * .8), (x + hw * .98, y - s * .45), (x - hw * .98, y - s * .45)]
    cv.obj([torso], 1.)
    cv.hair(C.hatch_poly(torso, 45, 1.5))
    cv.hair(C.hatch_poly(torso, -45, 3))
    if s > 30:
        for yy in (.55, .64):
            band = [(x - hw * 1.02, y - s * yy - s * .025), (x + hw * 1.02, y - s * yy - s * .025),
                    (x + hw * 1.0, y - s * yy + s * .02), (x - hw * 1.0, y - s * yy + s * .02)]
            cv.obj([band], .5)
            cv.hair([[(px, py - .1), (px, py + .1)] for px, py in band[:1]])
        for sg in (-1, 1):
            strap = [(x + sg * hw * .3, y - s * .8), (x + sg * hw * .6, y - s * .8), (x + sg * hw * .55, y - s * .6),
                     (x + sg * hw * .3, y - s * .6)]
            cv.obj([strap], .5)
        zipl = [(x, y - s * .78), (x, y - s * .46)]
        cv.line(zipl)
    # head, face shaded on its right
    hr = s * .065
    hy = y - s * .87
    head = _ell(x, hy, hr * .85, hr, 20)[:-1]
    cv.obj([head], 1.)
    cv.hair(C.hatch_poly([(x + hr * .2, hy - hr), (x + hr, hy - hr), (x + hr, hy + hr), (x + hr * .2, hy + hr)], 90, 1.5))
    if s > 30:
        cv.hair([(x - hr * .35, hy - hr * .05), (x - hr * .15, hy - hr * .05)])
        cv.hair([(x + hr * .15, hy - hr * .05), (x + hr * .35, hy - hr * .05)])
        cv.hair([(x - hr * .2, hy + hr * .45), (x + hr * .2, hy + hr * .45)])
    # hard hat: dome, brim, ridge
    dome = [(x - hr * 1.0, hy - hr * .3)] + [(x + hr * 1.0 * math.cos(a), hy - hr * .3 - hr * .95 * math.sin(a))
                                             for a in [PI - PI * i / 16 for i in range(17)]]
    brim = [(x - hr * 1.35, hy - hr * .38), (x + hr * 1.35, hy - hr * .38), (x + hr * 1.25, hy - hr * .18), (x - hr * 1.25, hy - hr * .18)]
    cv.obj([dome], 1.)
    cv.hair(C.hatch_poly([(x + hr * .3, hy - hr * 1.3), (x + hr * 1.1, hy - hr * 1.3), (x + hr * 1.1, hy - hr * .3), (x + hr * .3, hy - hr * .3)], 60, 1.5))
    cv.hair([(x, hy - hr * 1.25), (x, hy - hr * .35)])
    cv.obj([brim], 1.)
    solid(cv, brim[:2] + [(x + hr * 1.25, hy - hr * .25), (x - hr * 1.25, hy - hr * .25)])
    # right arm raised, holding the paddle staff
    sx = x + hw * 1.5
    arm2 = [(x + hw * .8, y - s * .79), (x + hw * 1.05, y - s * .8), (sx + hw * .25, y - s * .66), (sx - hw * .05, y - s * .6)]
    cv.obj([arm2], 1.)
    cv.hair(C.hatch_poly(arm2, 20, 1.5))
    staff_top = y - s * 1.08
    staff = rect(sx - .6, staff_top, 1.2, s * .78)
    cv.obj([staff], .5)
    solid(cv, staff, 90)
    glove = _ell(sx, y - s * .63, hw * .32, hw * .3, 12)[:-1]
    cv.obj([glove], 1.)
    cv.hair(C.hatch_poly(glove, 45, 1.5))
    # the paddle: black octagon with white border, drawn on top
    pr = s * .13
    pcx, pcy = sx, staff_top - pr * .85
    octo = [(pcx + pr * math.cos(PI / 8 + i * PI / 4), pcy + pr * math.sin(PI / 8 + i * PI / 4)) for i in range(8)]
    octi = [(pcx + pr * .8 * math.cos(PI / 8 + i * PI / 4), pcy + pr * .8 * math.sin(PI / 8 + i * PI / 4)) for i in range(8)]
    top.append(f'<path d="{_d(octo, True, 0)}" fill="#000" stroke="#000" stroke-width=".5"/>')
    top.append(f'<path d="{_d(octi, True, 0)}" fill="none" stroke="#fff" stroke-width="{1 if pr > 6 else .5}"/>')
    if pr > 9:
        polys, _ = text_lines("SLOW", pcx, pcy, pr * .52, 1.1)
        top.append(f'<path d="{"".join(_d(p, tol=0) for p in polys)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    elif pr > 4:
        top.append(f'<path d="M{_n(pcx - pr * .45)},{_n(pcy)}h{_n(pr * .9)}" stroke="#fff" stroke-width="1"/>')


def _pickup(cv, x, y, w, rng, detail):
    """A pickup seen from behind, centred on x with its wheels on y, w wide; the dog rides in the bed."""
    h = w * .78
    # tyres
    for sg in (-1, 1):
        ty = rect(x + sg * w * .42 - w * .09, y - h * .2, w * .18, h * .2)
        cv.obj([ty], 1.)
        solid(cv, ty)
    # cab (seen over the bed): roof and rear window
    cab = [(x - w * .38, y - h * .62), (x - w * .32, y - h * .98), (x + w * .32, y - h * .98), (x + w * .38, y - h * .62)]
    cv.obj([cab], 1.)
    cv.hair(C.hatch_poly(cab, 0, 3, 1))
    win = [(x - w * .3, y - h * .66), (x - w * .26, y - h * .9), (x + w * .26, y - h * .9), (x + w * .3, y - h * .66)]
    cv.obj([win], 1.)
    cv.line(C.hatch_poly(win, 0, 1.5, .5))
    cv.hair(C.hatch_poly(win, 60, 3))
    # bed sides and tailgate
    bed = [(x - w * .5, y - h * .62), (x + w * .5, y - h * .62), (x + w * .5, y - h * .18), (x - w * .5, y - h * .18)]
    cv.obj([bed], 1.5)
    cv.hair(C.hatch_poly(bed, 0, 2, 1))
    gate = [(x - w * .42, y - h * .58), (x + w * .42, y - h * .58), (x + w * .42, y - h * .3), (x - w * .42, y - h * .3)]
    cv.obj([gate], 1.)
    cv.hair(C.hatch_poly(gate, 0, 3, 1.5))
    cv.hair(C.hatch_poly([(x - w * .42, y - h * .38), (x + w * .42, y - h * .38), (x + w * .42, y - h * .3), (x - w * .42, y - h * .3)], 0, 1.5, .25))
    handle = rect(x - w * .08, y - h * .52, w * .16, h * .05)
    cv.obj([handle], .5)
    solid(cv, handle)
    # the dog: head and ears above the tailgate, looking back at us
    dx, dy = x + w * .1, y - h * .74
    r = w * .13
    for sg in (-1, 1):
        ear = [(dx + sg * r * .5, dy - r * .75), (dx + sg * r * 1.25, dy - r * .55), (dx + sg * r * 1.15, dy + r * .45),
               (dx + sg * r * .75, dy + r * .1)]
        cv.obj([ear], 1.)
        cv.line(C.hatch_poly(ear, 80 * sg, 1.5))
    head = _ell(dx, dy, r * .82, r, 24)[:-1]
    cv.obj([head], 1.)
    cv.hair(C.hatch_poly([(dx + r * .3, dy - r), (dx + r, dy - r), (dx + r, dy + r), (dx + r * .3, dy + r)], 80, 1.5))
    cv.hair([[(dx - r * .5 + k * r * .25, dy - r * .7), (dx - r * .45 + k * r * .25, dy - r * .4)] for k in range(4)])
    muz = _ell(dx, dy + r * .45, r * .42, r * .32, 16)[:-1]
    cv.obj([muz], .5)
    nose = _ell(dx, dy + r * .3, r * .16, r * .11, 10)[:-1]
    cv.obj([nose], 0)
    solid(cv, nose)
    for sg in (-1, 1):
        e = _ell(dx + sg * r * .35, dy - r * .1, r * .1, r * .12, 8)[:-1]
        cv.obj([e], 0)
        solid(cv, e)
    cv.hair([(dx, dy + r * .42), (dx, dy + r * .6), (dx - r * .15, dy + r * .68)])
    cv.hair([(dx, dy + r * .6), (dx + r * .15, dy + r * .68)])
    # tail lights and bumper
    for sg in (-1, 1):
        tl = rect(x + sg * w * .47 - w * .03, y - h * .58, w * .06, h * .18)
        cv.obj([tl], .5)
        solid(cv, tl)
    bump = rect(x - w * .52, y - h * .28, w * 1.04, h * .1)
    cv.obj([bump], 1.)
    cv.hair(C.hatch_poly(bump, 0, 1.5, .5))
    cv.hair([(x - w * .5, y - h * .26), (x + w * .5, y - h * .26)])
    plate_ = rect(x - w * .1, y - h * .28 - h * .02, w * .2, h * .1)
    cv.obj([plate_], .5)
    cv.hair(C.hatch_poly(plate_, 90, 1.5))
    # shadow under it
    sh = rect(x - w * .55, y - h * .05, w * 1.1, h * .07)
    cv.obj([sh], 0)
    solid(cv, sh)


def vignette(clip_d, box, cid, seed, detail):
    """The scene clipped to a field outline (path d)."""
    x, y, w, h = box
    a, b = scene(x - 1, y - 1, w + 2, h + 2, seed, detail)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{a}{b}</g>'


# ------------------------------------------------------------------------------------------------
# figural: volutes whose eyes become TripCheck camera lenses
# ------------------------------------------------------------------------------------------------

def lens(cx, cy, r):
    """A camera lens: a knurled barrel ring, black glass, a white glint."""
    o = [f'<path d="{_d(_ell(cx, cy, r, r, 32)[:-1], True, 0)}" fill="#fff" stroke="#000" stroke-width="1.5"/>']
    o.append(f'<path d="{_d(_ell(cx, cy, r * .78, r * .78, 28)[:-1], True, 0)}" fill="#000"/>')
    ticks = "".join(_d([(cx + r * .82 * math.cos(a), cy + r * .82 * math.sin(a)), (cx + r * .97 * math.cos(a), cy + r * .97 * math.sin(a))], tol=0)
                    for a in [TAU * i / 28 for i in range(28)])
    o.append(f'<path d="{ticks}" {_sw(.5)}/>')
    o.append(f'<path d="{_d(_ell(cx, cy, r * .5, r * .5, 24)[:-1], True, 0)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    g = [(cx - r * .45 + r * .3 * math.cos(a), cy - r * .3 + r * .2 * math.sin(a)) for a in [TAU * i / 12 for i in range(12)]]
    o.append(f'<path d="{_d(g, True, 0)}" fill="#fff"/>')
    o.append(f'<path d="{_d(_ell(cx + r * .3, cy + r * .28, r * .07, r * .07, 8)[:-1], True, 0)}" fill="#fff"/>')
    return "".join(o)


def _pair_eye(cx, cy, r, side, a_out, turns, tail, up):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    pts = C.volute_spine(cx, cy, r, a0, turns, flip, tail, -.5 if up else .5, .13)
    return pts[-1]


# ------------------------------------------------------------------------------------------------
# layouts (house layouts, adapted: no blank paper anywhere, lettering, lenses, our vignette)
# ------------------------------------------------------------------------------------------------

def _letter(polys, w=.5, color="#000"):
    return f'<path d="{"".join(_d(p, tol=.1) for p in polys)}" fill="none" stroke="{color}" stroke-width="{w}"/>'


def _ribbon(cx, cy, w, h, seed, words):
    svg, centre = C.ribbon_banner(cx, cy, w, h, .04, seed)
    xs = [p[0] for p in centre]
    ys = [p[1] for p in centre]

    def arch(x):
        if x <= xs[0]:
            return ys[0] - cy
        for i in range(1, len(xs)):
            if x <= xs[i]:
                f = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
                return ys[i - 1] + (ys[i] - ys[i - 1]) * f - cy
        return ys[-1] - cy
    face = xs[-1] - xs[0]
    hgt = min(h * .5, face / (len(words) * .9))
    polys, tw = text_lines(words, cx, cy, hgt, 1.6, arch)
    if tw > face * .9:
        hgt *= face * .9 / tw
        polys, tw = text_lines(words, cx, cy, hgt, 1.6, arch)
    return svg + _letter(polys, 1. if hgt > 7 else .5)


def _routes(ctx):
    s = (ctx or {}).get("sample", "") or ""
    import re
    found = []
    for m in re.finditer(r"\b(OR|US|I)-(\d{1,3})\b", s):
        r = f"{m.group(1)} {m.group(2)}"
        if r not in found:
            found.append(r)
    for r in ["OR 127", "US 26", "US 101", "US 30"]:
        if len(found) >= 4:
            break
        if r not in found:
            found.append(r)
    return found


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top - 1, w, gh + 3), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _ell(cx, cy, rx - 4.5, ry - 4.5, 64)[:-1]
    o.append(vignette(_d(field, True, 0), (cx - rx, cy - ry, 2 * rx, 2 * ry), C._uid("bv", w, h, seed), seed, 0))
    o.append(f'<path d="{_d(field, True, 0)}" {_sw(1)}/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
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
    cw = min(w * .44, gh * 1.6)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        eyes.append(_pair_eye(vx, vy, r, side, 0, 1.4, .9, True))
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .07), rmax=r * .8,
                   max_n=9, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    for ex, ey in eyes:
        o.append(lens(ex, ey, max(4., r * .13)))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(vignette(inner, (cx - cw / 2, cy - gh / 2 - 2, cw, gh + 4), C._uid("mv", w, h, seed), seed, 1 if h < 170 else 2))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_m = 8.
    px0, py0 = 4., top_m + 3
    pw = w - 8
    ph = h - py0 - ped_h - frieze + ped_h * .3
    # behind everything below the panel: a stippled ground so no paper shows round the pedestal
    o.append(C.dark_ground((0, py0 + ph - 4, w, h - (py0 + ph - 4)), "S"))
    o.append(C.bead_moulding(0, 4, w, 2))
    o.append(f'<path d="M{_n(px0 - 2.5)},{_n(py0 - 2.5)}h{_n(pw + 5)}v{_n(ph + 5)}h{_n(-pw - 5)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1)},{_n(py0 - 1)}h{_n(pw + 2)}v{_n(ph + 2)}h{_n(-pw - 2)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        eyes.append((_pair_eye(vx, vy, r1, side, 10, 1.45, .8, True), r1))
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
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0, pw, ph, cv.svg()))
    for (ex, ey), rr in eyes:
        o.append(lens(ex, ey, max(5., rr * .14)))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(vignette(inner, (cx - cw / 2, cy - ch / 2, cw, ch), C._uid("tv", w, h, seed), seed, 2))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2, 56), True, rng.randrange(1 << 20)))
    o.append(_ribbon(cx, cy + ch * .47, cw * 1.4, min(17, ph * .05), rng.randrange(1 << 20), "PREPARE TO SLOW"))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    polys, tw_ = text_lines(" · ".join(_routes(ctx)), tx + tw / 2 + 1, ty + th / 2 + 1, min(th * .62, 13), 1.6)
    # rule the tablet's ends; paper stays only behind the lettering
    for ex0, ex1 in ((tx + 3, tx + tw / 2 - tw_ / 2 - 8), (tx + tw / 2 + tw_ / 2 + 9, tx + tw - 1)):
        if ex1 - ex0 > 4:
            o.append(f'<path d="M{_n(ex0)},{_n(ty + 3)}h{_n(ex1 - ex0)}v{_n(th - 4)}h{_n(ex0 - ex1)}z" fill="{C.pat("L")}"/>')
            o.append(f'<path d="M{_n(ex0 - 5)},{_n(ty + th / 2 + 1)}l1.5,-1.5 1.5,1.5 -1.5,1.5z" fill="#000"/>' if ex0 > tx + tw / 2 else
                     f'<path d="M{_n(ex1 + 2)},{_n(ty + th / 2 + 1)}l1.5,-1.5 1.5,1.5 -1.5,1.5z" fill="#000"/>')
    o.append(_letter(polys, 1. if th > 14 else .5))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _milestone(fld, seed):
    """The marginal device: a stone milestone at the roadside, round-headed, cut SAUVIE 0 MI,
    its shadow side hatched, grass at its foot, the road running off behind it."""
    xs = [q[0] for q in fld]
    ys = [q[1] for q in fld]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    r = (max(xs) - min(xs)) / 2
    d = _d(fld, True, 0)
    o = [f'<path d="{d}" fill="url(#s2o)"/>']
    cv = C.Canvas()
    gy = cy + r * .5
    cv.obj([[(cx - r - 2, gy), (cx + r + 2, gy), (cx + r + 2, cy + r + 2), (cx - r - 2, cy + r + 2)]], 0)
    cv.hair(C.hatch_poly([(cx - r - 2, gy), (cx + r + 2, gy), (cx + r + 2, cy + r + 2), (cx - r - 2, cy + r + 2)], 0, 2))
    cv.obj([[(cx + r * .1, gy), (cx + r * .3, gy), (cx + r * 1.2, cy + r + 2), (cx - r * .5, cy + r + 2)]], .5)
    pw, ph = r * .62, r * 1.05
    top = gy - ph
    post = [(cx - pw / 2, gy + 1)] + [(cx + pw / 2 * math.cos(PI + PI * i / 16), top + pw / 2 + pw / 2 * math.sin(PI + PI * i / 16)) for i in range(17)] + [(cx + pw / 2, gy + 1)]
    cv.obj([post], 1.)
    side = [(cx + pw * .3, gy + 1), (cx + pw * .3, top + pw * .3), (cx + pw / 2, top + pw / 2), (cx + pw / 2, gy + 1)]
    cv.hair(C.hatch_poly(side, 90, 1.5))
    rng = random.Random(seed)
    cv.obj([], 0)
    cv.hair([[(cx + dx, gy + 1.5), (cx + dx + rng.uniform(-.8, .8), gy - rng.uniform(1.5, 3.5))] for dx in [-pw * .8 + i * 1.6 for i in range(int(pw * 1.6 / 1.6) + 1)]])
    o.append(cv.svg())
    th = max(3., pw * .22)
    o.append(st_letter("SAUVIE", th, cx=cx, cy=top + pw * .62, track=.15, sw=.5, fit=pw * .9))
    o.append(st_letter("0 MI", th * 1.25, cx=cx, cy=top + pw * .62 + th * 1.9, track=.2, sw=.5))
    return "".join(o)


def _field(fld, mode, seed):
    if mode == "device":
        return _milestone(fld, seed)
    xs = [q[0] for q in fld]
    ys = [q[1] for q in fld]
    x, y = min(xs), min(ys)
    a, b = scene(x - 1, y - 1, max(xs) - x + 2, max(ys) - y + 2, seed, {"band": 0, "medium": 1}.get(mode, 2))
    return a + b


# ==== STUDIO FRAME (batch 2) ====================================================================
# King-tier frame, copied into this plate so it can be cut to the page (house rule: the shared
# modules stay untouched). Fine English scroll as on the GRS vise and Ken Hunt's panels: dozens of
# small logarithmic spirals grown from one stem, each branching into the next and carrying its own
# shaded leaves, packed over a punched matte ground; white "gold-line" wire borders and beading
# frame every panel; the subject sits in an inlaid medallion ringed with beads.
import math as _m
import random as _rnd
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _m.pi
_sm = _C._smooth


def _st_mat_tile():
    """An 8 px matte tile: black punched with 1 px white dots set evenly (blue noise)."""
    rng = _rnd.Random(91)
    pts = []
    tries = 0
    while len(pts) < 13 and tries < 4000:
        tries += 1
        p = (rng.randrange(16) * .5, rng.randrange(16) * .5)
        ok = True
        for q in pts:
            dx = min(abs(p[0] - q[0]), 8 - abs(p[0] - q[0]))
            dy = min(abs(p[1] - q[1]), 8 - abs(p[1] - q[1]))
            if dx * dx + dy * dy < 3.6:
                ok = False
                break
        if ok:
            pts.append(p)
    return "".join(f"M{_C._n(x)},{_C._n(y)}h1v1h-1z" for x, y in pts)


_ST_DEFS = ('<defs><pattern id="s2m" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h8v8h-8z" fill="#000"/><path d="{_st_mat_tile()}" fill="#fff"/></pattern>'
            '<pattern id="s2o" width="2" height="2" patternUnits="userSpaceOnUse"><path d="M0,0h.5v.5h-.5zM1,1h.5v.5h-.5z" fill="#000"/></pattern></defs>')


def st_matte(d):
    """The punched matte ground over path data d."""
    return f'<path d="{d}" fill="url(#s2m)" stroke="none"/>'


def st_rect_d(x, y, w, h):
    return f"M{_C._n(x)},{_C._n(y)}h{_C._n(w)}v{_C._n(h)}h{_C._n(-w)}z"


# ---------------------------------------------------------------------------------------------
# the fine scroll: spirals, leaves, growth from one stem
# ---------------------------------------------------------------------------------------------

def _spiral(px, py, head, R, s, turns):
    """A log spiral leaving (px, py) heading `head`, first radius R, turning toward side s
    (+1 = the +normal side), winding `turns` into an eye at .13 R. -> (pts, centre, radii)."""
    th = _TAU * turns
    b = _m.log(1 / .13) / th
    a0 = _m.atan2(s * R, -b * R)
    rot = head - a0
    cr, sr = _m.cos(rot), _m.sin(rot)
    pts, rad = [], []
    t = 0.
    while True:
        r = R * _m.exp(-b * t)
        lx, ly = r * _m.cos(t) - R, s * r * _m.sin(t)
        pts.append((px + lx * cr - ly * sr, py + lx * sr + ly * cr))
        rad.append(r)
        if t >= th:
            break
        t = min(th, t + max(.05, 1.4 / r))
    return pts, (px - R * cr, py - R * sr), rad


def _tangent(pts, i):
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    return _m.atan2(b[1] - a[1], b[0] - a[0])


class _Grid:
    def __init__(self, cell=24.):
        self.c = cell
        self.g = {}
        self.maxr = 0.

    def add(self, x, y, r, oid):
        self.g.setdefault((int(x // self.c), int(y // self.c)), []).append((x, y, r, oid))
        self.maxr = max(self.maxr, r)

    def clear(self, x, y, r, slack, ignore):
        reach = r + self.maxr
        c = self.c
        for i in range(int((x - reach) // c), int((x + reach) // c) + 1):
            for j in range(int((y - reach) // c), int((y + reach) // c) + 1):
                for qx, qy, qr, oid in self.g.get((i, j), ()):
                    if oid != ignore and (qx - x) ** 2 + (qy - y) ** 2 < ((r + qr) * slack) ** 2:
                        return False
        return True


def st_sweep(x, y, ang, L, k0, k1=None, n=None):
    """A sweeping stem: from (x, y) heading ang (radians), L long, curvature k0 -> k1 (1/px)."""
    k1 = k0 if k1 is None else k1
    return _C._euler(x, y, ang, L, lambda u: k0 + (k1 - k0) * u, n or max(8, int(L / 2)))


class ScrollField:
    """Grows fine scroll over a region. inside(x, y) says where scroll may grow. Scrolls branch
    from stems and from one another, each sized to the room it finds, until the field is packed."""

    def __init__(self, inside, rmin=7., rmax=30., seed=0, slack=.88):
        self.inside = inside
        self.rmin, self.rmax = rmin, rmax
        self.rng = _rnd.Random(seed)
        self.grid = _Grid(20.)
        self.slack = slack
        self.items = []
        self.queue = []

    def _ok(self, c, R, parent):
        if not self.inside(c[0], c[1]):
            return False
        if parent is not None and self.items[parent][1] == "scroll":
            pc, pR = self.items[parent][2][1], self.items[parent][2][4]
            if (pc[0] - c[0]) ** 2 + (pc[1] - c[1]) ** 2 < ((pR + R) * .78) ** 2:
                return False
        for k in range(8):
            a = k * _TAU / 8
            if not self.inside(c[0] + R * .55 * _m.cos(a), c[1] + R * .55 * _m.sin(a)):
                return False
        return self.grid.clear(c[0], c[1], R, self.slack, parent)

    def stem(self, pts, w0=2.2, w1=1.2, leaves=True, gen=0):
        """A sweeping lead, the source the scrolls grow from (points run from the root out)."""
        oid = len(self.items)
        for p in pts[::2]:
            self.grid.add(p[0], p[1], 2.5, oid)
        self.items.append((gen, "stem", (pts, w0, w1, leaves)))
        self.queue.append((gen, oid, "stem", pts, 0, None))
        return oid

    def scroll(self, px, py, head, R, s, gen=0, parent=None, turns=None, force=False):
        turns = turns or self.rng.uniform(1.25, 1.55)
        pts, c, rad = _spiral(px, py, head, R, s, turns)
        if not force and not self._ok(c, R, parent):
            return False
        oid = len(self.items)
        self.grid.add(c[0], c[1], R, oid)
        self.items.append((gen, "scroll", (pts, c, rad, s, R)))
        self.queue.append((gen, oid, "scroll", pts, s, (c, R)))
        return True

    def grow(self, max_items=300):
        rng = self.rng
        qi = 0
        while qi < len(self.queue) and len(self.items) < max_items:
            gen, oid, kind, pts, s, info = self.queue[qi]
            qi += 1
            n = len(pts)
            cand = []
            if kind == "scroll":
                c, R = info
                for f in (.03, .14, .27, .4, .52):
                    i = int(f * (n - 1))
                    q = pts[i]
                    tau = _tangent(pts, i)
                    rh = _m.hypot(q[0] - c[0], q[1] - c[1])
                    cand.append((q, tau, -s, self.rmax))
                    cand.append((q, tau + _PI, s, self.rmax * .8))
            else:
                for i in range(3, n - 2, 4):
                    q = pts[i]
                    tau = _tangent(pts, i)
                    for sd in (1, -1):
                        cand.append((q, tau + sd * .15, -sd, self.rmax))
                        cand.append((q, tau + _PI - sd * .2, sd, self.rmax * .7))
                rng.shuffle(cand)
            for q, head, cs, top in cand:
                Rc = min(self.rmax, top)
                while Rc >= self.rmin:
                    if self.scroll(q[0], q[1], head + cs * rng.uniform(-.05, .2), Rc, cs, gen + 1, oid):
                        break
                    Rc *= .82
        return self

    def _branch_to(self, oid, cx, cy, R):
        """A scroll centred at (cx, cy) whose stem leads in from the nearest coil of item oid,
        joining it tangentially, so every scroll grows out of another."""
        it = self.items[oid]
        pts = it[2][0]
        if it[1] == "scroll":
            pc, pR, rad = it[2][1], it[2][4], it[2][2]
            idx = [i for i in range(0, len(pts), 2) if rad[i] > pR * .45 and
                   (pts[i][0] - pc[0]) * (cx - pts[i][0]) + (pts[i][1] - pc[1]) * (cy - pts[i][1]) > 0] or list(range(0, len(pts) // 3))
        else:
            idx = list(range(0, len(pts), 2))
        bi = min(idx, key=lambda i: (pts[i][0] - cx) ** 2 + (pts[i][1] - cy) ** 2)
        q = pts[bi]
        tau = _tangent(pts, bi)
        ua = _m.atan2(q[1] - cy, q[0] - cx)
        S = (cx + R * _m.cos(ua), cy + R * _m.sin(ua))
        hx, hy = _m.cos(tau), _m.sin(tau)
        if hx * (S[0] - q[0]) + hy * (S[1] - q[1]) < 0:
            hx, hy = -hx, -hy
        turns = self.rng.uniform(1.25, 1.55)
        th = _TAU * turns
        bb = _m.log(1 / .13) / th
        best = None
        for sg in (1, -1):
            tx = -bb * _m.cos(ua) - sg * _m.sin(ua)
            ty = -bb * _m.sin(ua) + sg * _m.cos(ua)
            dot = tx * hx + ty * hy
            if best is None or dot > best[0]:
                best = (dot, sg, tx, ty)
        _, sg, tx, ty = best
        tl = _m.hypot(tx, ty)
        tx, ty = tx / tl, ty / tl
        L = _m.hypot(S[0] - q[0], S[1] - q[1])
        lead = []
        if L > 1.5:
            k = L * .45 + 2
            p1 = (q[0] + hx * k, q[1] + hy * k)
            p2 = (S[0] - tx * k, S[1] - ty * k)
            m = max(3, int(L / 1.5))
            for i in range(m):
                t = i / m
                a, b_, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
                lead.append((a * q[0] + b_ * p1[0] + c * p2[0] + d * S[0], a * q[1] + b_ * p1[1] + c * p2[1] + d * S[1]))
        sp, rad = [], []
        t = 0.
        while True:
            r = R * _m.exp(-bb * t)
            ph = ua + sg * t
            sp.append((cx + r * _m.cos(ph), cy + r * _m.sin(ph)))
            rad.append(r)
            if t >= th:
                break
            t = min(th, t + max(.05, 1.4 / r))
        allp = lead + sp
        allr = [R] * len(lead) + rad
        noid = len(self.items)
        self.grid.add(cx, cy, R, noid)
        self.items.append((it[0] + 1, "scroll", (allp, (cx, cy), allr, sg, R)))
        return True

    def fill(self, x, y, w, h, step=5., max_items=320):
        """Pack the field: find the widest free spot, branch a scroll into it from the nearest
        scroll's outer coil, repeat until no gap of about rmin is left."""
        rng = self.rng
        P = []
        nx, ny = max(2, int(w / step)), max(2, int(h / step))
        for j in range(ny):
            for i in range(nx):
                px, py = x + (i + .5) * w / nx, y + (j + .5) * h / ny
                if self.inside(px, py):
                    P.append([px, py, 1e9, None])
        if not P:
            return self
        cell = {}
        for k, p in enumerate(P):
            cell.setdefault((int(p[0] // 30), int(p[1] // 30)), []).append(k)

        def upd(oid, cx, cy, R, reach=None):
            reach = R + (reach or self.rmax * 3)
            for i in range(int((cx - reach) // 30), int((cx + reach) // 30) + 1):
                for j in range(int((cy - reach) // 30), int((cy + reach) // 30) + 1):
                    for k in cell.get((i, j), ()):
                        p = P[k]
                        d = _m.hypot(p[0] - cx, p[1] - cy) - R
                        if d < p[2]:
                            p[2], p[3] = d, oid
        obs = []
        for oid, it in enumerate(self.items):
            if it[1] == "scroll":
                obs.append((it[2][1][0], it[2][1][1], it[2][4], oid))
            else:
                obs.extend((q[0], q[1], 2.5, oid) for q in it[2][0][::5])
        for p in P:
            for ox, oy, orr, oid in obs:
                d = _m.hypot(p[0] - ox, p[1] - oy) - orr
                if d < p[2]:
                    p[2], p[3] = d, oid
        import heapq
        hp = [(-p[2], k) for k, p in enumerate(P)]
        heapq.heapify(hp)
        while len(self.items) < max_items and hp:
            nd, k = heapq.heappop(hp)
            best = P[k]
            if -nd != best[2]:
                heapq.heappush(hp, (-best[2], k))
                continue
            if best[2] < self.rmin * 1.15:
                break
            px, py, D, oid = best
            if oid is None:
                continue
            R = min(self.rmax, D * .97) * rng.uniform(.9, 1.)
            self._branch_to(oid, px, py, R)
            upd(len(self.items) - 1, px, py, R)
            for kk in cell.get((int(px // 30), int(py // 30)), ()):
                heapq.heappush(hp, (-P[kk][2], kk))
        return self

    def draw(self, cv, egg=None, egg_gen=2):
        """Paint the branches first so each parent lies over its children. egg(cv, x, y, r) is
        cut into the eye of one scroll of generation egg_gen (the first big enough)."""
        rng = _rnd.Random(7)
        order = sorted(range(len(self.items)), key=lambda k: -self.items[k][0])
        egg_done = egg is None
        for k in order:
            gen, kind, data = self.items[k]
            if kind == "stem":
                pts, w0, w1, lv = data
                _draw_stem(cv, pts, w0, w1, rng, lv)
                continue
            pts, c, rad, s, R = data
            use = None
            if not egg_done and gen >= egg_gen and R > 14:
                use, egg_done = egg, True
            _draw_scroll(cv, pts, c, rad, s, R, rng, use)


def _leaf(cv, x, y, ang, L, W, bend, curl, rng, lobes=None):
    """A fine-scroll leaf: a curved blade scalloped on its outer edge and turning over at the tip,
    fine parallel cuts on its shadow side, a bright cut edge, a centre vein."""
    n = max(8, int(L / 1.2))
    sp = _C._euler(x, y, ang, L, lambda u: (bend + curl * _sm(.55, 1., u) ** 2 * 3.2) / L, n)
    c = 1 if bend >= 0 else -1
    nl = lobes or (3 if L > 14 else 2)
    ph = rng.uniform(0, .3)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        pr = min(1., u / .22) ** .6 * (1 - u) ** .7 * 1.35
        v = (u * nl + ph) % 1.
        wo.append(W * pr * (.6 + .4 * _m.sin(_PI * v) ** .6) + .3)
        wi.append(W * pr * .85 + .3)
    R = _C._Rib(sp, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    cv.hair(_C._fill_lines(R, .22 * c, .92 * c, 1.5, .06, .9, 2))
    if W > 2.4:
        cv.hair(R.contour(-.05 * c, .12, .72))
    for j in range(nl):
        u = (j - ph) / nl
        if .18 < u < .85 and R.width(u, -c) > 1.8:
            cv.hair([R.at(u, -.95 * c), R.at(u + .05, -.4 * c)])
    return R


def _draw_stem(cv, pts, w0, w1, rng, leaves):
    n = len(pts)
    W = [w0 + (w1 - w0) * i / max(1, n - 1) for i in range(n)]
    R = _C._Rib(pts, W, W)
    if leaves:
        L = R.L
        u = .06
        sd = 1
        while u < .94:
            i = int(u * (n - 1))
            q = R.at(u, sd * .8)
            ll = rng.uniform(9, 13)
            _leaf(cv, q[0], q[1], _tangent(pts, i) + sd * .55, ll, ll * .22, -sd * .5, sd * 2.2, rng)
            sd = -sd
            u += rng.uniform(13, 18) / L
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(-.4, 0., 1.))
    cv.hair(R.contour(-.8, 0., 1.))


def _draw_scroll(cv, pts, c, rad, s, R, rng, egg=None):
    n = len(pts)
    hw0 = max(1., min(3.2, R * .13))
    W = [max(.6, hw0 * (rad[i] / R) ** .55) for i in range(n)]
    Rb = _C._Rib(pts, W, W)
    # where the coil proper starts (after any lead-in)
    k0 = 0
    while k0 < n - 1 and rad[k0 + 1] >= R - 1e-6:
        k0 += 1
    span = n - 1 - k0
    nlv = 1 if R < 10 else (2 if R < 16 else 3)
    fs = (.03, .2, .36)[:nlv]
    for j, f in enumerate(fs[::-1]):
        i = k0 + int(f * span)
        q = Rb.at(i / (n - 1), -s)
        ll = rad[i] * rng.uniform(.8, .95)
        _leaf(cv, q[0], q[1], _tangent(pts, i) - s * .55, ll, ll * .25, s * .9, -s * rng.uniform(1.2, 1.8), rng)
    if k0 > 6:
        i = k0 // 2
        q = Rb.at(i / (n - 1), s)
        ll = min(R * .7, 12.)
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .6, ll, ll * .24, -s * .7, s * 1.6, rng)
    cv.obj([Rb.outline()], .5)
    cv.hair(Rb.contour(.5 * s, 0., .92))
    if hw0 > 1.8:
        cv.hair(Rb.contour(.82 * s, 0., .8))
        cv.hair(Rb.contour(-.55 * s, .0, .35))
    if R > 15:
        i = k0 + int(.55 * span)
        q = Rb.at(i / (n - 1), s)
        ll = rad[i] * .95
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .35, ll, ll * .2, s * 1.6, s * .3, rng, 2)
    ex, ey = pts[-1]
    if egg:
        egg(cv, ex, ey, max(5., R * .4))
    else:
        rr = max(1.1, W[-1] * 1.4)
        cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)
        cv.line(_C._ell_pts(ex, ey, .3, .3, 4))


# ---------------------------------------------------------------------------------------------
# borders, beading, medallion, arms
# ---------------------------------------------------------------------------------------------

def st_wire(d):
    """A gold-line (wire inlay) border along path d: white wire, black, white wire on a black bed."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="5"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="3"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>')


def st_beads(d, pitch=3.5, r=1.):
    """A row of white beads on a black fillet along path d."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_C._n(2 * r + 2)}"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_C._n(2 * r)}" stroke-linecap="round" '
            f'stroke-dasharray="0 {_C._n(pitch)}"/>')


def st_ell_d(cx, cy, rx, ry, n=96):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n), True, .1)


def st_poly_d(poly):
    return _C._d(list(poly), True, .1)


def st_medallion(cx, cy, rx, ry):
    """An inlaid portrait medallion: wire, a ring of beads, wire. -> (svg, field polygon)."""
    o = [f'<path d="{st_ell_d(cx, cy, rx + 7, ry + 7)}" fill="#000" stroke="none"/>',
         st_wire(st_ell_d(cx, cy, rx + 5.5, ry + 5.5)),
         st_beads(st_ell_d(cx, cy, rx + 1.5, ry + 1.5, 180), 3.5, 1.),
         f'<path d="{st_ell_d(cx, cy, rx - .5, ry - .5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), _C._ell_pts(cx, cy, rx - 1.2, ry - 1.2, 120)[:-1]


def st_arch(cx, top, bot, half, n=48):
    """An arched (round-headed) panel polygon: the binding's central panel."""
    r = half
    pts = [(cx - half, bot)]
    for i in range(n + 1):
        a = _PI + _PI * i / n
        pts.append((cx + r * _m.cos(a), top + r + r * _m.sin(a)))
    pts.append((cx + half, bot))
    return pts


def st_arch_medallion(cx, top, bot, half):
    o = [f'<path d="{st_poly_d(st_arch(cx, top - 7, bot + 7, half + 7))}" fill="#000" stroke="none"/>',
         st_wire(st_poly_d(st_arch(cx, top - 5.5, bot + 5.5, half + 5.5))),
         st_beads(st_poly_d(st_arch(cx, top - 1.5, bot + 1.5, half + 1.5, 96)), 3.5, 1.),
         f'<path d="{st_poly_d(st_arch(cx, top + .5, bot - .5, half - .5))}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_arch(cx, top + 1.2, bot - 1.2, half - 1.2, 72)


def st_shape_pts(shape, cx, cy, rx, ry, g=0., n=120, ph=0.):
    """The outline of a shaped panel grown outward by g: oval, roundel, arch or irregular."""
    if shape == "arch":
        return st_arch(cx, cy - ry - g, cy + ry + g, rx + g, max(24, n // 2))
    if shape == "roundel":
        rx = ry = min(rx, ry)
    pts = []
    for i in range(n):
        t = _TAU * i / n
        k = 1.
        if shape == "irregular":
            k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
        pts.append((cx + (rx * k + g) * _m.cos(t), cy + (ry * k + g) * _m.sin(t)))
    return pts


def st_shape_in(shape, x, y, cx, cy, rx, ry, g=0., ph=0.):
    if shape == "arch":
        if y >= cy - ry + rx:
            return abs(x - cx) < rx + g and y < cy + ry + g
        return _m.hypot(x - cx, y - (cy - ry + rx)) < rx + g
    if shape == "roundel":
        rx = ry = min(rx, ry)
    t = _m.atan2((y - cy) / max(ry, 1), (x - cx) / max(rx, 1))
    k = 1.
    if shape == "irregular":
        k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
    return ((x - cx) / (rx * k + g)) ** 2 + ((y - cy) / (ry * k + g)) ** 2 < 1


def st_shaped_medallion(shape, cx, cy, rx, ry, ph=0.):
    """A shaped inlaid panel: black bed, wire, beads, white fillet. -> (svg, field polygon)."""
    if shape == "oval":
        return st_medallion(cx, cy, rx, ry)
    P = lambda g, n=120: st_poly_d(st_shape_pts(shape, cx, cy, rx, ry, g, n, ph))
    o = [f'<path d="{P(7)}" fill="#000" stroke="none"/>', st_wire(P(5.5)), st_beads(P(1.5, 180), 3.5, 1.),
         f'<path d="{P(-.5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_shape_pts(shape, cx, cy, rx, ry, -1.2, 120, ph)


def st_dedication(cx, foot, hh):
    """The small Somaster dedication cartouche at a front vignette's foot (about 30 px)."""
    return st_arms(cx, foot - hh / 2, hh * .5, hh * .5, mantling=True)


def st_device(w, h, seed, hk):
    """A marginal device (a 40-60 px roundel): the subject in a beaded roundel, the corners of
    the block cut away to the matte with a leaf in each spandrel."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    cx, cy = w / 2, h / 2
    r = min(w, h) / 2 - (4.5 if min(w, h) < 64 else 7.5)
    cv = StCanvas()
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * (w / 2 - 3), cy + sy * (h / 2 - 3)
            a = _m.atan2(cy - py, cx - px)
            if _m.hypot(px - cx, py - cy) > r + 9:
                L = max(4., (_m.hypot(px - cx, py - cy) - r - 6) * 1.1)
                _leaf(cv, px, py, a, L, L * .42, .5 * sx * sy, .35, _rnd.Random(seed + sx * 3 + sy))
    o.append(cv.svg())
    o.append(st_wire(st_rect_d(1.5, 1.5, w - 3, h - 3)))
    o.append(f'<path d="{st_ell_d(cx, cy, r + 3.5, r + 3.5)}" fill="#000"/>'
             f'<path d="{st_ell_d(cx, cy, r + 2, r + 2)}" fill="none" stroke="#fff" stroke-width="1" stroke-dasharray="1 1.5"/>'
             f'<path d="{st_ell_d(cx, cy, r - .2, r - .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    fld = _C._ell_pts(cx, cy, r - .9, r - .9, 72)[:-1]
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2d{w}x{h}v", fld, hk["field"](fld, "device") + st_rim(fld, 2.5)))
    return "".join(o)


def st_clip_poly(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{_C._d(list(poly), True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_clip_rect(cid, x, y, w, h, body):
    return f'<clipPath id="{cid}"><path d="{st_rect_d(x, y, w, h)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_sun(cv, cx, cy, r, rays=16):
    disc = _C._ell_pts(cx, cy, r, r, 28)[:-1]
    for k in range(rays):
        a = k * _TAU / rays
        ln = r * (1.9 if k % 2 == 0 else 1.5)
        w = _PI / rays * .7
        tri = [(cx + r * .9 * _m.cos(a - w), cy + r * .9 * _m.sin(a - w)), (cx + ln * _m.cos(a), cy + ln * _m.sin(a)),
               (cx + r * .9 * _m.cos(a + w), cy + r * .9 * _m.sin(a + w))]
        cv.obj([tri], .5)
        cv.hair([(cx + r * _m.cos(a + w * .4), cy + r * _m.sin(a + w * .4)), (cx + ln * .9 * _m.cos(a), cy + ln * .9 * _m.sin(a))])
    cv.obj([disc], .5)
    cv.hair([p for p in _C.hatch_poly(disc, 45, 1.5) if p[0][0] + p[0][1] > cx + cy - r * .3])


def _stick(cv, x0, y0, x1, y1, w):
    a = _m.atan2(y1 - y0, x1 - x0)
    n = 16
    pts = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    W = [w * (1 - .55 * _sm(.6, .95, i / n)) for i in range(n + 1)]
    R = _C._Rib(pts, W, W)
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(.6, .02, .93))
    tx, ty = x1 + _m.cos(a) * w * .5, y1 + _m.sin(a) * w * .5
    cv.obj([_C._ell_pts(tx, ty, w * 1.1, w * .8, 12)[:-1]], .5)


def st_crossed_sticks(cv, cx, cy, L, w=1.3, ang=0.):
    """Parker's crossed drumsticks, bead tips up."""
    for sd in (-1, 1):
        a = ang - _PI / 2 + sd * .62
        dx, dy = _m.cos(a) * L / 2, _m.sin(a) * L / 2
        _stick(cv, cx - dx, cy - dy, cx + dx, cy + dy, w)


_FLEUR = [(0, -1), (.13, -.72), (.16, -.42), (.1, -.15), (.24, -.2), (.42, -.42), (.62, -.48), (.78, -.38),
          (.8, -.18), (.68, -.02), (.54, .04), (.62, -.12), (.6, -.26), (.48, -.26), (.34, -.08), (.22, .1),
          (.36, .1), (.36, .22), (.14, .22), (.2, .5), (.38, .72), (.2, .7), (.08, .54), (0, .62)]


def _fleur(cx, cy, s):
    """A fleur-de-lis about 2s tall, as one closed polygon."""
    right = [(cx + x * s, cy + y * s) for x, y in _FLEUR]
    left = [(cx - x * s, cy + y * s) for x, y in _FLEUR[::-1]][1:-1]
    return right + left


def _heater(cx, top, w, h, n=24):
    """A heater shield outline: straight chief, sides curving to the point."""
    pts = [(cx - w / 2, top), (cx + w / 2, top)]
    for i in range(n + 1):
        t = i / n
        pts.append((cx + w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    for i in range(n, -1, -1):
        t = i / n
        pts.append((cx - w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    return pts


def st_arms(cx, cy, rx, ry, mantling=True):
    """Parker's arms, Somaster: Or, a castle between five fleurs-de-lis sable. A heater shield,
    Or as an even field of fine dots (Petra Sancta), the charges sable cut in solid black with
    white mortar lines; acanthus mantling springs from behind the shield's top corners."""
    o = []
    sh = min(ry * 2, rx * 2.3)
    sw = sh * .84
    top = cy - sh / 2
    shield = _heater(cx, top, sw, sh)
    if mantling:
        cv = _C.Canvas()
        rng = _rnd.Random(5)
        for sd in (-1, 1):
            for k, (a, L) in enumerate(((-.3, .9), (.25, .8), (.85, .7), (1.35, .55))):
                ang = (_PI / 2 - (a + 1.2)) if sd > 0 else (_PI / 2 + (a + 1.2))
                x0, y0 = cx + sd * sw * .42, top + sh * .1 + k * sh * .12
                _leaf(cv, x0, y0, -ang + _PI if False else (a * sd + (0 if sd > 0 else _PI)), sh * L * .55, sh * L * .12,
                      sd * .8, -sd * 2., rng, 3)
        o.append(cv.svg())
    d = st_poly_d(shield)
    o.append(f'<path d="{d}" fill="#000" stroke="#000" stroke-width="3"/>')
    o.append(f'<path d="{d}" fill="#fff" stroke="#fff" stroke-width="1"/>')
    o.append(f'<path d="{d}" fill="url(#s2o)" stroke="#000" stroke-width=".5"/>')
    blk = []
    s = sh * .085
    for fx, fy in ((-.26, .14), (0, .14), (.26, .14), (-.36, .55), (.36, .55)):
        blk.append(_fleur(cx + fx * sw, top + fy * sh + s * .1, s))
    # the castle: two towers and a curtain wall, crenellated, an arched gate with a portcullis
    cw, chh = sw * .46, sh * .3
    bx0, by1 = cx - cw / 2, top + sh * .72
    tw, th = cw * .24, chh * 1.3
    mer = tw / 5
    for tx in (bx0, bx0 + cw - tw):
        ty = by1 - th
        pts = [(tx, by1), (tx, ty)]
        for k in range(5):
            x = tx + k * mer
            if k % 2 == 0:
                pts += [(x, ty - mer), (x + mer, ty - mer)]
            else:
                pts += [(x, ty), (x + mer, ty)]
        pts += [(tx + tw, ty), (tx + tw, by1)]
        blk.append(pts)
    wy = by1 - chh * .72
    wx0, wx1 = bx0 + tw - .2, bx0 + cw - tw + .2
    nm = max(3, int((wx1 - wx0) / mer))
    mm = (wx1 - wx0) / nm
    pts = [(wx0, by1), (wx0, wy)]
    for k in range(nm):
        x = wx0 + k * mm
        if k % 2 == 1:
            pts += [(x, wy - mer * .9), (x + mm, wy - mer * .9)]
        else:
            pts += [(x, wy), (x + mm, wy)]
    pts += [(wx1, wy), (wx1, by1)]
    blk.append(pts)
    o.append(f'<path d="{"".join(st_poly_d(p) for p in blk)}" fill="#000" stroke="none"/>')
    # white work in the sable: mortar courses, tower windows, the gate and its portcullis
    lines = []
    for k in range(1, 6):
        y = by1 - k * chh * .2
        lines.append([(bx0 + 1, y), (bx0 + tw - 1, y)])
        lines.append([(bx0 + cw - tw + 1, y), (bx0 + cw - 1, y)])
        if y > wy + 1:
            lines.append([(wx0 + 1, y), (wx1 - 1, y)])
    gw, gh = cw * .2, chh * .55
    gate = [(cx - gw / 2, by1)] + [(cx - gw / 2 * _m.cos(t * _PI / 12), by1 - gh * .6 - gw / 2 * _m.sin(t * _PI / 12)) for t in range(13)] + [(cx + gw / 2, by1)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in lines)}" stroke="#fff" stroke-width="1" fill="none"/>')
    o.append(f'<path d="{st_poly_d(gate)}" fill="#fff" stroke="none"/>')
    pc = [[(cx + gw * (k / 4 - .5) * .8, by1 - gh * .95), (cx + gw * (k / 4 - .5) * .8, by1)] for k in range(5)]
    pc += [[(cx - gw * .45, by1 - gh * .3 * k), (cx + gw * .45, by1 - gh * .3 * k)] for k in (1, 2)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in pc)}" stroke="#000" stroke-width=".5" fill="none"/>')
    for tx in (bx0 + tw / 2, bx0 + cw - tw / 2):
        o.append(f'<path d="M{_C._n(tx)},{_C._n(by1 - th * .75)}v{_C._n(th * .22)}" stroke="#fff" stroke-width="1"/>')
    return "".join(o)


def st_sky(x0, y0, x1, y1, seed, avoid=None, clouds=None, top_dark=.32, pitch=(2., 2., 3., 3.)):
    """A Dore sky, not a ruled one: long lines that swell over billowing cloud banks (lit tops
    left white, undersides shaded), dark and cross-cut at the zenith, opening toward the horizon.
    Returns (hair polylines, line polylines). avoid(x, y) breaks the lines (moon, towers)."""
    rng = _rnd.Random(seed)
    W, H = x1 - x0, y1 - y0
    if clouds is None:
        clouds = []
        n = max(2, int(W / 80) + 1)
        for i in range(n):
            cx = x0 + W * (i + rng.uniform(.2, .8)) / n
            cy = y0 + H * rng.uniform(.3, .75)
            clouds.append((cx, cy, W / n * rng.uniform(.45, .7), H * rng.uniform(.09, .16)))
    hair, heavy = [], []

    def cloud_at(x, y):
        for cx, cy, rx, ry in clouds:
            dx = (x - cx) / rx
            if abs(dx) < 1:
                top = cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))
                bot = cy + ry * .35 * (1 - dx * dx) ** .5
                if top <= y <= bot:
                    return (y - top) / max(.5, bot - top)
        return None
    y = y0 + .75
    while y < y1:
        f = (y - y0) / max(1., H)
        p = pitch[min(len(pitch) - 1, int(f * len(pitch)))]
        run = []
        x = x0
        while x <= x1 + 3:
            yy = y
            for ccx, ccy, crx, cry in clouds:
                dx = (x - ccx) / (crx * 1.5)
                if abs(dx) < 1 and y > ccy:
                    yy += cry * .22 * (1 - dx * dx) ** 2 * max(0., 1 - (y - ccy) / (cry * 3))
            cf = cloud_at(x, yy)
            lit = cf is not None and cf < .55
            if lit or (avoid and avoid(x, yy)):
                if len(run) > 1:
                    hair.append(run)
                run = []
            else:
                run.append((x, yy))
            x += 3.
        if len(run) > 1:
            hair.append(run)
        y += p
    # cloud edges: billowed tops, shaded bellies
    for cx, cy, rx, ry in clouds:
        top = []
        for i in range(41):
            dx = -1 + 2 * i / 40
            top.append((cx + dx * rx, cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))))
        hair.append(top)
        for k in range(1, 4):
            arc = []
            for i in range(31):
                dx = -.85 + 1.7 * i / 30
                arc.append((cx + dx * rx * (1 - .12 * k), cy - ry * (1 - dx * dx) ** .5 * (.55 - .14 * k) + ry * .1 * k))
            hair.append(arc)
    # the zenith: cross-cut so the sky deepens upward
    zt = y0 + H * top_dark
    for ln in _C.hatch_poly([(x0, y0), (x1, y0), (x1, zt), (x0, zt)], 30, 3.):
        if avoid:
            a_, b_ = ln
            seg, cur = [], []
            for i in range(int(_m.dist(a_, b_) / 2) + 2):
                t = i / max(1, int(_m.dist(a_, b_) / 2) + 1)
                q = (a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t)
                if avoid(*q):
                    if len(cur) > 1:
                        hair.append(cur)
                    cur = []
                else:
                    cur.append(q)
            if len(cur) > 1:
                hair.append(cur)
        else:
            hair.append(ln)
    return hair, heavy


def st_rim(fld, depth=12., uid="r"):
    """Light emerging from dark: concentric cuts round the inside of a medallion field, close and
    heavy at the rim, thinning inward, so the subject glows out of a dark surround."""
    cx = sum(p[0] for p in fld) / len(fld)
    cy = sum(p[1] for p in fld) / len(fld)
    size = min(max(abs(p[0] - cx) for p in fld), max(abs(p[1] - cy) for p in fld))
    o1, o5 = [], []
    d = .75
    while d < depth:
        k = 1 - d / size
        ring = [(cx + (p[0] - cx) * k, cy + (p[1] - cy) * k) for p in fld]
        (o1 if d < depth * .35 else o5).append(_C._d(ring + [ring[0]], tol=.2))
        d += 2. if d < depth * .35 else 1.5 + (d / depth) * 1.5
    return (f'<path d="{"".join(o1)}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="{"".join(o5)}" fill="none" stroke="#000" stroke-width=".5"/>')


# ---------------------------------------------------------------------------------------------
# Easter eggs cut into a scroll's eye: egg(cv, x, y, r) draws inside a disc of radius r
# ---------------------------------------------------------------------------------------------

def _egg_disc(cv, x, y, r):
    cv.obj([_C._ell_pts(x, y, r, r, 28)[:-1]], 1.)
    cv.hair(_C._ell_pts(x, y, r - 1.2, r - 1.2, 28))


def egg_sticks(cv, x, y, r):
    """Parker's crossed drumsticks."""
    _egg_disc(cv, x, y, r)
    st_crossed_sticks(cv, x, y + r * .05, r * 1.45, max(.6, r * .09))


def egg_P(cv, x, y, r):
    """A "P" monogram, cut as a stem and a bowl with a flourish."""
    _egg_disc(cv, x, y, r)
    h = r * 1.1
    cv.line([(x - h * .22, y + h * .5), (x - h * .22, y - h * .5)])
    bowl = [(x - h * .22, y - h * .5)] + [(x - h * .05 + h * .3 * _m.sin(t * _PI / 10), y - h * .25 - h * .25 * _m.cos(t * _PI / 10)) for t in range(11)] + [(x - h * .22, y)]
    cv.line(bowl)
    cv.hair([(x - h * .45, y + h * .5), (x + h * .05, y + h * .5)])
    cv.hair([(x - h * .22, y + h * .5), (x - h * .5, y + h * .62), (x - h * .62, y + h * .45)])


def egg_note(cv, x, y, r):
    """A swing eighth-note pair (jazz)."""
    _egg_disc(cv, x, y, r)
    s = r * .32
    for dx in (-1, 1):
        hx, hy = x + dx * s * 1.1 - s * .4, y + s * 1.1
        cv.obj([_C._ell_pts(hx, hy, s * .55, s * .38, 12)[:-1]], .5)
        cv.line(_C._ell_pts(hx, hy, s * .3, s * .15, 8))
        cv.line([(hx + s * .5, hy), (hx + s * .5, y - s * 1.5)])
    cv.heavy([(x - s * .6 + s * .1, y - s * 1.5), (x + s * 1.6 + s * .1, y - s * 1.5)])


def egg_cymbal(cv, x, y, r):
    """A tiny ride cymbal on its stand, lathe rings and a bell."""
    _egg_disc(cv, x, y, r)
    cy = y - r * .15
    cv.obj([_C._ell_pts(x, cy, r * .8, r * .22, 24)[:-1]], .5)
    for k in (1, 2, 3):
        cv.hair(_C._ell_pts(x, cy, r * .8 * k / 4, r * .22 * k / 4, 20))
    cv.obj([_C._ell_pts(x, cy - r * .08, r * .16, r * .1, 10)[:-1]], .5)
    cv.line([(x, cy + r * .2), (x, y + r * .7)])
    cv.hair([(x, y + r * .55), (x - r * .35, y + r * .78)])
    cv.hair([(x, y + r * .55), (x + r * .35, y + r * .78)])


def egg_hood(cv, x, y, r):
    """Mt. Hood: the snow cone, its glaciers and a timber line."""
    _egg_disc(cv, x, y, r)
    pk = [(x - r * .82, y + r * .45), (x - r * .1, y - r * .55), (x + r * .05, y - r * .6), (x + r * .82, y + r * .45)]
    cv.obj([pk], .5)
    cv.hair([(x - r * .02, y - r * .5), (x - r * .25, y + r * .05)])
    cv.hair([(x + r * .05, y - r * .5), (x + r * .3, y + r * .1)])
    cv.hair(_C.hatch_poly([(x + r * .05, y - r * .58), (x + r * .82, y + r * .45), (x + r * .25, y + r * .45)], 60, 1.5))
    for k in range(7):
        tx = x - r * .7 + k * r * .23
        cv.line([(tx, y + r * .62), (tx, y + r * .38)])


def egg_pinwheel(cv, x, y, r):
    """The Blazers pinwheel: five pairs of swept bars turning about a hub."""
    _egg_disc(cv, x, y, r)
    for k in range(5):
        a = k * _TAU / 5 - _PI / 2
        for off in (-.12, .12):
            p0 = (x + r * .18 * _m.cos(a + off), y + r * .18 * _m.sin(a + off))
            p1 = (x + r * .78 * _m.cos(a + off + .35), y + r * .78 * _m.sin(a + off + .35))
            cv.line([p0, p1])


def egg_heron(cv, x, y, r):
    """A Sauvie Island heron's head and S neck, crest plume and dagger bill."""
    _egg_disc(cv, x, y, r)
    neck = [(x - r * .1, y + r * .8), (x - r * .35, y + r * .3), (x - r * .05, y - r * .05), (x - r * .25, y - r * .4)]
    cv.line(neck)
    cv.line([(x - r * .05 + r * .15, y + r * .8), (x - r * .2 + r * .12, y + r * .3), (x + r * .12, y - r * .02), (x - r * .1, y - r * .35)])
    hd = _C._ell_pts(x - r * .2, y - r * .45, r * .16, r * .11, 12)[:-1]
    cv.obj([hd], .5)
    cv.line([(x - r * .05, y - r * .48), (x + r * .65, y - r * .38)])
    cv.hair([(x - r * .32, y - r * .5), (x - r * .7, y - r * .55)])


def egg_dog(cv, x, y, r):
    """Parker's dog, head on its paws, curled asleep in the eye of the scroll."""
    _egg_disc(cv, x, y, r)
    body = _C._ell_pts(x + r * .05, y + r * .15, r * .72, r * .42, 24)[:-1]
    cv.obj([body], .5)
    cv.hair(_C._fill_lines(_C._Rib([(x - r * .6, y + r * .15), (x + r * .7, y + r * .15)], [r * .38, r * .38], [r * .38, r * .38]), -.3, -.95, 1.5, .1, .9, 2))
    head = _C._ell_pts(x - r * .38, y - r * .05, r * .26, r * .2, 16)[:-1]
    cv.obj([head], .5)
    cv.obj([[(x - r * .48, y - r * .2), (x - r * .3, y - r * .45), (x - r * .22, y - r * .16)]], .5)
    cv.line(_C._ell_pts(x - r * .6, y - r * .02, .5, .5, 4))
    cv.hair([(x - r * .45, y - r * .06), (x - r * .36, y - r * .04)])
    cv.hair([(x + r * .7, y + r * .1), (x + r * .55, y + r * .45), (x + r * .1, y + r * .52)])


def egg_kranok(cv, x, y, r):
    """A Thai kranok flame: three flame tongues curling up out of a lotus calyx."""
    _egg_disc(cv, x, y, r)
    for sd, L, a in ((0, 1., -_PI / 2), (-1, .7, -_PI / 2 - .55), (1, .7, -_PI / 2 + .55)):
        bx = x + sd * r * .12
        rib = _C._euler(bx, y + r * .5, a, r * L, lambda u, s_=sd or 1: s_ * 2.2 * _sm(.5, 1, u) / (r * L), 12)
        W = [r * .16 * (1 - i / 12) ** .7 + .3 for i in range(13)]
        R = _C._Rib(rib, W, W)
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.4, .05, .85))
    cv.obj([_C._ell_pts(x, y + r * .55, r * .3, r * .14, 14)[:-1]], .5)


def egg_panel(cv, x, y, r):
    """A solar panel on its rack: a grid of cells, one ray of sun."""
    _egg_disc(cv, x, y, r)
    q = [(x - r * .7, y + r * .2), (x + r * .45, y + r * .2), (x + r * .7, y - r * .35), (x - r * .45, y - r * .35)]
    cv.obj([q], .5)
    for k in range(1, 4):
        t = k / 4
        cv.hair([(q[0][0] + (q[1][0] - q[0][0]) * t, q[0][1]), (q[3][0] + (q[2][0] - q[3][0]) * t, q[3][1])])
    cv.hair([((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2), ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)])
    cv.line([(x - r * .1, y + r * .2), (x - r * .1, y + r * .65)])
    cv.line([(x - r * .4, y + r * .65), (x + r * .25, y + r * .65)])


# ---------------------------------------------------------------------------------------------
# lettering: engraved Roman capitals as strokes (no <text>)
# ---------------------------------------------------------------------------------------------

_OV = [(.5 + .5 * _m.cos(_TAU * i / 20 - _PI / 2), .5 + .5 * _m.sin(_TAU * i / 20 - _PI / 2)) for i in range(21)]
_GL = {
    "A": ([[(0, 1), (.5, 0), (1, 1)], [(.22, .62), (.78, .62)]], .85),
    "B": ([[(0, 0), (0, 1), (.7, 1), (.9, .85), (.9, .65), (.7, .5), (0, .5)], [(0, 0), (.62, 0), (.82, .12), (.82, .38), (.62, .5)]], .75),
    "C": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .85)]], .8),
    "D": ([[(0, 0), (0, 1), (.55, 1), (.92, .72), (.92, .28), (.55, 0), (0, 0)]], .8),
    "E": ([[(.85, 0), (0, 0), (0, 1), (.85, 1)], [(0, .5), (.65, .5)]], .7),
    "F": ([[(.85, 0), (0, 0), (0, 1)], [(0, .5), (.65, .5)]], .65),
    "G": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .8), (.95, .55), (.55, .55)]], .82),
    "H": ([[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .5), (1, .5)]], .8),
    "I": ([[(.5, 0), (.5, 1)]], .3),
    "J": ([[(.8, 0), (.8, .78), (.6, 1), (.2, 1), (0, .8)]], .6),
    "K": ([[(0, 0), (0, 1)], [(.9, 0), (0, .62)], [(.3, .42), (.95, 1)]], .78),
    "L": ([[(0, 0), (0, 1), (.85, 1)]], .65),
    "M": ([[(0, 1), (0, 0), (.5, .65), (1, 0), (1, 1)]], 1.),
    "N": ([[(0, 1), (0, 0), (1, 1), (1, 0)]], .82),
    "O": ([_OV], .9),
    "P": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)]], .72),
    "Q": ([_OV, [(.6, .72), (1, 1.06)]], .9),
    "R": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)], [(.45, .5), (.95, 1)]], .76),
    "S": ([[(.9, .12), (.7, 0), (.25, 0), (.05, .15), (.05, .35), (.25, .47), (.75, .53), (.95, .66), (.95, .85), (.75, 1), (.25, 1), (.05, .88)]], .7),
    "T": ([[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]], .78),
    "U": ([[(0, 0), (0, .75), (.25, 1), (.75, 1), (1, .75), (1, 0)]], .8),
    "V": ([[(0, 0), (.5, 1), (1, 0)]], .82),
    "W": ([[(0, 0), (.25, 1), (.5, .35), (.75, 1), (1, 0)]], 1.1),
    "X": ([[(0, 0), (1, 1)], [(1, 0), (0, 1)]], .8),
    "Y": ([[(0, 0), (.5, .5), (1, 0)], [(.5, .5), (.5, 1)]], .8),
    "Z": ([[(0, 0), (1, 0), (0, 1), (1, 1)]], .76),
    "0": ([[(.5 + .45 * _m.cos(_TAU * i / 20), .5 + .5 * _m.sin(_TAU * i / 20)) for i in range(21)]], .65),
    "1": ([[(.25, .2), (.55, 0), (.55, 1)], [(.25, 1), (.85, 1)]], .55),
    "2": ([[(.05, .2), (.25, 0), (.75, 0), (.95, .2), (.95, .4), (0, 1), (1, 1)]], .65),
    "3": ([[(.05, .1), (.3, 0), (.75, 0), (.95, .2), (.9, .4), (.5, .5), (.9, .6), (.95, .8), (.75, 1), (.3, 1), (.05, .9)]], .65),
    "4": ([[(.75, 1), (.75, 0), (0, .7), (1, .7)]], .65),
    "5": ([[(.9, 0), (.15, 0), (.05, .45), (.6, .4), (.95, .6), (.95, .8), (.7, 1), (.25, 1), (.05, .9)]], .65),
    "6": ([[(.85, .05), (.5, 0), (.15, .2), (.05, .6), (.15, .9), (.5, 1), (.85, .9), (.95, .7), (.8, .5), (.45, .45), (.1, .6)]], .65),
    "7": ([[(0, 0), (1, 0), (.35, 1)]], .62),
    "8": ([[(.5, .5), (.15, .38), (.1, .15), (.3, 0), (.7, 0), (.9, .15), (.85, .38), (.5, .5), (.1, .65), (.05, .85), (.3, 1), (.7, 1), (.95, .85), (.9, .65), (.5, .5)]], .65),
    "9": ([[(.9, .4), (.55, .55), (.15, .45), (.05, .25), (.2, .05), (.55, 0), (.9, .2), (.95, .5), (.8, .85), (.45, 1), (.15, .95)]], .65),
    "-": ([[(.1, .55), (.9, .55)]], .5),
    "·": ([[(.45, .5), (.55, .5)]], .35),
    ".": ([[(.45, .95), (.55, .95)]], .3),
    ",": ([[(.5, .9), (.35, 1.15)]], .3),
    ":": ([[(.5, .3), (.5, .32)], [(.5, .9), (.5, .92)]], .3),
    "'": ([[(.5, 0), (.4, .25)]], .25),
    "/": ([[(1, 0), (0, 1)]], .55),
    "&": ([[(1, 1), (.2, .35), (.25, .08), (.5, 0), (.7, .1), (.7, .3), (.1, .7), (.15, .95), (.5, 1), (.85, .7)]], .8),
    "°": ([[(.3 + .2 * _m.cos(_TAU * i / 10), .15 + .15 * _m.sin(_TAU * i / 10)) for i in range(11)]], .45),
    "%": ([[(1, 0), (0, 1)], [(.2 + .15 * _m.cos(_TAU * i / 10), .18 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)],
           [(.8 + .15 * _m.cos(_TAU * i / 10), .82 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)]], .75),
    " ": ([], .45),
}


def st_text_w(text, h, track=.32):
    t = [ch if ch in _GL else " " for ch in text.upper()]
    return sum(_GL[ch][1] * h * .78 for ch in t) + track * h * max(0, len(t) - 1)


def st_letter(text, h, centre=None, cx=0., cy=0., track=.32, sw=None, fit=None):
    """Monoline engraved capitals h tall, centred on (cx, cy) or along the polyline `centre`.
    fit shrinks the lettering to that width. -> svg path."""
    t = [ch if ch in _GL else " " for ch in text.upper()]
    if fit:
        tw = st_text_w(text, h, track)
        if tw > fit:
            h *= fit / tw
    tw = st_text_w(text, h, track)
    if centre:
        acc = [0.]
        for i in range(1, len(centre)):
            acc.append(acc[-1] + _m.dist(centre[i], centre[i - 1]))
        tot = acc[-1]

        def at(sv):
            sv = max(0., min(tot, sv))
            for i in range(1, len(acc)):
                if acc[i] >= sv:
                    f = (sv - acc[i - 1]) / max(1e-6, acc[i] - acc[i - 1])
                    p0, p1 = centre[i - 1], centre[i]
                    return p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, _m.atan2(p1[1] - p0[1], p1[0] - p0[0])
            return centre[-1][0], centre[-1][1], 0.
        pos = (tot - tw) / 2
    else:
        pos = -tw / 2
    d = []
    for ch in t:
        strokes, wf = _GL[ch]
        gw = wf * h * .78
        if centre:
            mx, my, a = at(pos + gw / 2)
        else:
            mx, my, a = cx + pos + gw / 2, cy, 0.
        ca, sa = _m.cos(a), _m.sin(a)
        for st in strokes:
            pts = []
            for gx, gy in st:
                lx, ly = (gx - .5) * gw, (gy - .5) * h
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            d.append(_C._d(pts, tol=.05))
        pos += gw + track * h
    w = sw or (1. if h >= 7 else .5)
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width="{_C._n(w)}"/>'


def st_tablet_text(tx, ty, tw, th, lines):
    """Lines of lettering in a tablet, over a dotted Or ground cut back behind each line."""
    o = [f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>']
    n = len(lines)
    lh = min(th / (n * 1.6 + .4), 11.)
    for i, ln in enumerate(lines):
        cy = ty + th * (i + .5) / n
        w = min(tw - 8, st_text_w(ln, lh) + lh * 1.4)
        o.append(f'<path d="{st_rect_d(tx + (tw - w) / 2, cy - lh * .85, w, lh * 1.7)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
        o.append(st_letter(ln, lh, cx=tx + tw / 2, cy=cy, fit=tw - 12))
    return "".join(o)


def st_doc(w, h, body):
    return _C.svg_doc(w, h, _ST_DEFS + body)
# ==== END STUDIO FRAME ==========================================================================
# ==== STUDIO LAYOUTS ============================================================================


def _in_ell(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1


def st_border(w, h, inset=3.):
    """The plate's own gold-line border and an inner row of beads, all four edges."""
    return (st_wire(st_rect_d(inset, inset, w - 2 * inset, h - 2 * inset))
            + st_beads(st_rect_d(inset + 4.5, inset + 4.5, w - 2 * inset - 9, h - 2 * inset - 9), 3.5, 1.))


def _st_clip_runs(pl, mask, x0, y0, W, H, out, step=1.5):
    """_clip_runs at a 1.5 px test step (lines are cut cleanly enough; half the work)."""
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L = _m.hypot(dx, dy)
        if L > step:
            k = int(L / step)
            for j in range(1, k + 1):
                t = j / (k + 1)
                pts.append((px + dx * t, py + dy * t))
        pts.append(q)
        px, py = q
    run = []
    for (x, y) in pts:
        xi, yi = int(x - x0), int(y - y0)
        if 0 <= xi < W and 0 <= yi < H and mask[yi][xi]:
            if len(run) > 1:
                out.append(run)
            run = []
        else:
            run.append((x, y))
    if len(run) > 1:
        out.append(run)


class StCanvas(_C.Canvas):
    """The house Canvas, emitting with a slightly coarser simplification for the fine cuts so a
    packed field of scroll stays inside the byte budget (the eye cannot see 0.15 px)."""

    def svg(self, tol_fill=.95, tol_hair=.65, tol_line=.55):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for wd, lines in strokes.items():
                for pl in lines:
                    _st_clip_runs(pl, mask, x0, y0, W, H, out[wd])
            if ow:
                for poly in polys:
                    _st_clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                _C._fill_mask(poly, mask, x0, y0, W, H)
        res = []
        pen = _C._Pen()
        for polys, _, _ in self.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="#fff" stroke="none"/>')
        for wd in (.5, 1., 1.5):
            if out[wd]:
                pen = _C._Pen()
                for pl in out[wd]:
                    if len(pl) > 2 or _m.dist(pl[0], pl[-1]) > .6:
                        pen.add(pl, False, tol_hair if wd < 1 else tol_line)
                res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_C._n(wd * 4)}"/>')
        return "".join(res)


def _scroll_layer(field, uid, x, y, w, h, egg=None, egg_gen=2):
    cv = StCanvas()
    field.draw(cv, egg, egg_gen)
    return st_clip_rect(uid, x, y, w, h, cv.svg())


def st_band(w, h, seed, hk):
    """h < 110: a carved band. An inlaid medallion holds the subject; from it a stem runs to
    either edge, the fine scroll branching off it to fill the band."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2 + hk.get("dx", 0.), h / 2
    ry = max(4., h / 2 - 8.5) if h >= 40 else max(4., h / 2 - 7.2)
    rx = min(w * .2, max(ry * 1.5, ry * hk.get("aspect", 1.7)))
    if h < 40:
        ins = 5.
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 2 < y < fy1 + 2 and not _in_ell(x, y, cx, cy, rx + 12, ry + 12)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(3.5 if h < 40 else 4.5, gh * .12), rmax=max(4.6, gh * .32), seed=seed, slack=.9)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        L = (w / 2 - rx - 14) * 1.05
        x0 = cx + sd * (rx + 9)
        a = 0. if sd > 0 else _PI
        pts = []
        n = int(L / 2)
        for i in range(n + 1):
            u = i / n
            pts.append((x0 + sd * L * u, cy + gh * .18 * _m.sin(u * _TAU * (L / (gh * 2.2)) + (0 if sd > 0 else 1.3))))
        F.stem(pts, 1.6, 1.0, leaves=False)
    F.grow(8)
    F.fill(fx0 - 4, fy0 - 2, fx1 - fx0 + 8, fy1 - fy0 + 4, 3., hk.get("max_items", 160))
    o.append(_scroll_layer(F, f"s2b{w}x{h}", 0, 0, w, h, hk.get("egg"), 1))
    o.append(st_border(w, h, 1.5 if h < 40 else 3.))
    m, fld = st_medallion(cx, cy, rx, ry)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2b{w}x{h}v", fld, hk["field"](fld, "band") + st_rim(fld, hk.get("rim", 5.))))
    return "".join(o)


def st_medium(w, h, seed, hk):
    """110-260: the medallion between two panels of fine scroll, each grown from a stem that
    sweeps out of the medallion's foot; gold-line border and beading round the plate."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2, h / 2
    shape = hk.get("shape", "oval")
    ded = 15. if hk.get("dedication") else 0.
    ry = h / 2 - ins - 6
    rx = min(w * hk.get("cw", .21), ry * hk.get("aspect", 1.45))
    if shape == "roundel":
        rx = ry
    if shape == "arch":
        rx = min(rx, ry * 1.1)
    ph = (seed % 97) * .07
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 3 < y < fy1 + 3 and not st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph) and not (ded and abs(x - cx) < 34 and y > h - ins - 2 * ded - 6)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(6., gh * .055), rmax=min(26., gh * .2), seed=seed, slack=.88)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        a0 = _PI / 2 + sd * .25 * _PI
        x0, y0 = cx + (rx + 10) * _m.cos(_PI / 2 - sd * .9), cy + (ry + 10) * _m.sin(_PI / 2 - sd * .9)
        head = 0. if sd > 0 else _PI
        L = (w / 2 - rx - 20)
        k = -sd * .9 / L
        F.stem(st_sweep(x0, y0, head + sd * .35, L * 1.05, k * 1.5, -k * 1.2), 2., 1.1)
        x1, y1 = cx + (rx + 10) * _m.cos(-_PI / 2 + sd * .9), cy + (ry + 10) * _m.sin(-_PI / 2 + sd * .9)
        F.stem(st_sweep(x1, y1, head - sd * .35, L * .8, -k * 1.5, k), 1.8, 1.)
    F.grow(10)
    F.fill(fx0 - 4, fy0 - 3, fx1 - fx0 + 8, fy1 - fy0 + 6, 4., hk.get("max_items", 260))
    o.append(_scroll_layer(F, f"s2m{w}x{h}", 0, 0, w, h, hk.get("egg"), 2))
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2m{w}x{h}v", fld, hk["field"](fld, "medium") + st_rim(fld, hk.get("rim", 9.))))
    if ded:
        o.append(st_dedication(cx, h - 3, 2 * ded))
    if hk.get("crest"):
        o.append(hk["crest"](cx, cy - ry - 2, min(14., ins + 4), "medium"))
    return "".join(o)


def st_pedestal(x, y, w, h, seed, hk, uid):
    """The base: knurled cornice, a frieze panel (gold-line border, fine scroll from the centre
    out) round a sunk tablet, a second knurled bar, beading. -> svg"""
    o = []
    kb = 6.
    o.append(_C.knurled_bar(x, y, w, kb))
    py0, py1 = y + kb + 1, y + h - kb - 5
    ph = py1 - py0
    tw, th = min(w * .5, 300.), ph - 10
    tx, ty = x + (w - tw) / 2, py0 + 5
    o.append(st_matte(st_rect_d(x, py0, w, ph)))

    def inside(px, py):
        return x + 6 < px < x + w - 6 and py0 + 2 < py < py1 - 2 and not (tx - 8 < px < tx + tw + 8)
    F = ScrollField(inside, rmin=max(4.5, ph * .16), rmax=ph * .4, seed=seed + 11, slack=.9)
    for sd in (-1, 1):
        xs = tx - 6 if sd < 0 else tx + tw + 6
        L = (w - tw) / 2 - 14
        pts = [(xs + sd * L * i / 30, py0 + ph / 2 + ph * .15 * _m.sin(i / 30 * _TAU * (L / (ph * 2)))) for i in range(31)]
        F.stem(pts, 1.4, .9, leaves=False)
    F.grow(6)
    F.fill(x + 6, py0 + 2, w - 12, ph - 4, 3., 120)
    o.append(_scroll_layer(F, uid + "p", x, py0, w, ph))
    o.append(st_wire(st_rect_d(x + 2.5, py0 + 1.5, w - 5, ph - 3)))
    o.append(f'<path d="{st_rect_d(tx - 3, ty - 3, tw + 6, th + 6)}" fill="#000"/>')
    o.append(st_beads(st_rect_d(tx - 1.5, ty - 1.5, tw + 3, th + 3), 3.5, 1.))
    o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="#fff" stroke="none"/>')
    if hk.get("tablet"):
        o.append(hk["tablet"](tx, ty, tw, th))
    elif hk.get("tablet_lines"):
        o.append(st_tablet_text(tx, ty, tw, th, hk["tablet_lines"]))
    else:
        o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>')
    o.append(_C.knurled_bar(x + 4, py1, w - 8, kb))
    o.append(st_beads(f"M{_C._n(x + 3)},{_C._n(y + h - 2.5)}h{_C._n(w - 6)}", 3.5, 1.))
    return "".join(o)


def st_tall(w, h, seed, hk):
    """> 260: the full plate. The scene in a great inlaid medallion (an arched panel on a section
    front, like the binding) over a ribbon banner and the dedication cartouche with Parker's arms
    (placeholder); fine scroll grown from a stem rising either side of the arms packs the field;
    a pedestal; under it, when tall, a frieze of the same scroll."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    ped_h = min(max(h * .13, 40), 62.)
    fz = min(max(h * .09, 30), 50.) if (h >= 440 and hk.get("frieze", True)) else 0.
    py = h - ped_h - fz - ins * (1 if fz else .6)
    shape = hk.get("shape") or ("arch" if hk.get("arch") else "oval")
    arch = shape == "arch"
    rx = w * hk.get("cw", .3)
    top = ins + 12
    bot = py - (62 if py > 300 else 46)
    ry = (bot - top) / 2
    if shape == "roundel":
        rx = ry = min(rx * 1.25, ry)
        top = bot - 2 * ry
    cx, cy = w / 2, top + ry
    ph = (seed % 97) * .07
    ay = bot + 4
    ary = min(26., (py - ay) * .4)
    arx = ary * 1.25
    aby = py - ary - 8

    def inside(x, y):
        if not (ins - 4 < x < w - ins + 4 and ins - 3 < y < py - 3):
            return False
        if st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph):
            return False
        if abs(x - cx) < rx * 1.05 + 10 and bot - 4 < y < bot + 16:
            return False
        if _in_ell(x, y, cx, aby, arx + 10, ary + 9):
            return False
        return True
    F = ScrollField(inside, rmin=hk.get("rmin", 8.), rmax=min(hk.get("rmax", 30.), w * .058), seed=seed, slack=.88)
    for sd in (-1, 1):
        x0, y0 = cx + sd * (arx + 8), aby + ary * .3
        F.stem(st_sweep(x0, y0, (0. if sd > 0 else _PI) - sd * .25, (py - ins) * .55 + w * .1,
                        -sd * .004, -sd * .022), 3., 1.6)
        F.stem(st_sweep(cx + sd * (rx * .7), ins + 4, (0. if sd > 0 else _PI) + sd * .15, w * .3, sd * .004, sd * .02), 2.6, 1.4)
    F.grow(4)
    F.fill(ins - 4, ins - 3, w - 2 * ins + 8, py - ins, 6., hk.get("max_items", 340))
    uid = f"s2t{w}x{h}"
    o.append(_scroll_layer(F, uid, 0, 0, w, py, hk.get("egg"), 2))
    if fz:
        fy0 = py + ped_h + 2
        fh = h - ins - fy0

        def inside2(x, y):
            return ins - 4 < x < w - ins + 4 and fy0 < y < fy0 + fh and abs(x - w / 2) > fh * .7
        G = ScrollField(inside2, rmin=max(4.5, fh * .15), rmax=fh * .4, seed=seed + 5, slack=.9)
        for sd in (-1, 1):
            L = w / 2 - fh * .7 - 8
            G.stem([(w / 2 + sd * (fh * .7 + L * i / 40), fy0 + fh / 2 + fh * .17 * _m.sin(i / 40 * _TAU * (L / (fh * 2.1)))) for i in range(41)],
                   1.5, 1., leaves=False)
        G.grow(6)
        G.fill(ins - 4, fy0, w - 2 * ins + 8, fh, 4., 140)
        o.append(_scroll_layer(G, uid + "f", 0, fy0, w, fh, hk.get("egg2"), 1))
        cvp = _C.Canvas()
        _C.palmette(w / 2, fy0 + 1, fh * .8, False, seed, cv=cvp)
        o.append(cvp.svg())
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(uid + "v", fld, hk["field"](fld, "tall") + st_rim(fld, hk.get("rim", 14.))))
    if hk.get("crest"):
        o.append(hk["crest"](cx, top - 3, top - 4, "tall"))
    bh = min(16., (py - bot) * .4)
    bs, centre = _C.ribbon_banner(cx, bot + 2, rx * 2.5, bh, .035, seed)
    o.append(bs)
    if hk.get("banner"):
        o.append(hk["banner"](centre, bh))
    elif hk.get("motto"):
        o.append(st_letter(hk["motto"], bh * .55, centre=centre[4:-4], fit=_m.dist(centre[4], centre[-5]) * .92))
    if hk.get("dedication"):
        o.append(st_arms(cx, aby, arx, ary))
    else:
        # not a front: a small inlaid cartouche carries the page's own device instead of the arms
        em, efl = st_medallion(cx, aby, arx * .78, ary * .78)
        o.append(em)
        o.append(f'<path d="{st_poly_d(efl)}" fill="url(#s2o)" stroke="none"/>')
        if hk.get("egg"):
            ecv = StCanvas()
            hk["egg"](ecv, cx, aby, ary * .62)
            o.append(ecv.svg())
    o.append(st_pedestal(0, py, w, ped_h, seed, hk, uid))
    return "".join(o)


def st_dissolve(poly, seed, depth=9., step=1.25):
    """Bewick's dissolving edge: white broken rings laid over the outer few px of a vignette, the
    white taking more of each ring toward the rim, so the cut lines crumble out into the paper."""
    rng = _rnd.Random(seed)
    n = int(depth / step)
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    o = []
    for k in range(n):
        f = 1 - k / n                       # 1 at the rim, toward 0 inside
        g = k * step + .4
        ring = []
        for (x, y) in poly:
            dx, dy = x - cx, y - cy
            L = _m.hypot(dx, dy) or 1
            ring.append((x - dx / L * g, y - dy / L * g))
        segs = []
        for _ in range(4):
            on = rng.uniform(1, 5) * (.3 + 1.9 * f * f)
            off = rng.uniform(3, 9) * (1.3 - f)
            segs += [on, max(.3, off)]
        da = " ".join(_C._n(v) for v in segs)
        o.append(f'<path d="{st_poly_d(ring)}" fill="none" stroke="#fff" stroke-width="{_C._n(step + .25)}" '
                 f'stroke-dasharray="{da}" stroke-dashoffset="{_C._n(rng.uniform(0, 40))}"/>')
    o.append(f'<path d="{st_poly_d(poly)}" fill="none" stroke="#fff" stroke-width="2"/>')
    return "".join(o)


def st_vignette(w, h, seed, hk):
    """The free-standing vignette: the scene itself is the plate, cut to its shape and crumbling
    out into the paper at the rim; any ornament is drawn from the subject (hk['frame'])."""
    shape = hk.get("shape", "oval")
    pad = hk.get("pad", 2.)
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - pad, h / 2 - pad
    rx = min(rx, ry * hk.get("max_aspect", 3.2))
    ph = (seed % 97) * .07
    fld = hk["shape_fn"](cx, cy, rx, ry) if hk.get("shape_fn") else st_shape_pts(shape, cx, cy, rx, ry, 0., 160, ph)
    if shape == "irregular" and not hk.get("shape_fn"):
        s = max(max(abs(q[0] - cx) / (w / 2 - pad) for q in fld), max(abs(q[1] - cy) / (h / 2 - pad) for q in fld))
        fld = [(cx + (q[0] - cx) / s, cy + (q[1] - cy) / s) for q in fld]
    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    o = [f'<path d="{st_rect_d(0, 0, w, h)}" fill="#fff"/>']
    if hk.get("under"):
        o.append(hk["under"](cx, cy, rx, ry, fld, mode))
    o.append(st_clip_poly(f"s2v{w}x{h}", fld, hk["field"](fld, mode)))
    o.append(st_dissolve(fld, seed, hk.get("dissolve", min(7., 3 + min(w, h) * .025))))
    if hk.get("frame"):
        o.append(hk["frame"](cx, cy, rx, ry, fld, mode))
    if hk.get("dedication") and h >= 110:
        dh = min(30., h * .16)
        o.append(f'<path d="{st_ell_d(cx, h - dh / 2 - 1.5, dh * .62, dh * .55)}" fill="#fff"/>')
        o.append(st_dedication(cx, h - 1.5, dh))
    return "".join(o)


def st_plate(w, h, seed, hk):
    base = _C.Canvas
    if hk.get("vignette"):
        return _st_plate(w, h, seed, hk)
    _C.Canvas = StCanvas
    try:
        return _st_plate(w, h, seed, hk)
    finally:
        _C.Canvas = base


def _st_plate(w, h, seed, hk):
    if hk.get("vignette"):
        body = st_vignette(w, h, seed, hk)
    elif h <= 72 and w <= 110 and hk.get("device", True):
        body = st_device(w, h, seed, hk)
    elif h < 110:
        body = st_band(w, h, seed, hk)
    elif h <= 260:
        body = st_medium(w, h, seed, hk)
    else:
        body = st_tall(w, h, seed, hk)
    return st_doc(w, h, body)
# ==== END STUDIO LAYOUTS ========================================================================


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    routes = _routes(ctx)
    hk = dict(field=lambda fld, mode: _field(fld, mode, seed), egg=egg_panel, shape="roundel", aspect=1.9, cw=.27,
              rmin=10., rmax=32., frieze=False, motto="PREPARE TO SLOW",
              tablet_lines=[" · ".join(routes[:2]), " · ".join(routes[2:4])] if len(routes) > 2 else [" · ".join(routes)])
    return st_plate(w, h, seed, hk)
