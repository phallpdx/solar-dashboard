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
    cv.hair(C.hatch_poly(rect(x0 - 2, y0 - 2, W + 4, (yh - y0) * .45), 0, 1.5))
    cv.hair(C.hatch_poly(rect(x0 - 2, y0 - 2 + (yh - y0) * .45, W + 4, (yh - y0) * .55 + 6), 0, 3))
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


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
