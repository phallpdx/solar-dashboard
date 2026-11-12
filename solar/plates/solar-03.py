"""solar-03 "This billing cycle" (PGE bill cycle): last bill $17.22 against $461.68 a year ago,
because the panels on the roof now carry the house. The plate engraves that: a low November sun
over Sauvie Island raking Parker's roof array, the old glass-domed PGE meter on its post in the
foreground (its dials parked near zero), Mt. Hood on the horizon as the Easter egg, all inside the
house Codex scroll frame. Tall plates carry the year of bills cut into the pedestal tablet."""
import sys
import math
import random
import engraving_codex as C

_n, _d = C._n, C._d
TAU = math.tau


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _quad(A, B, Cc, D, s, t):
    """bilinear point on quad A(0,0) B(1,0) C(1,1) D(0,1)."""
    return _lerp(_lerp(A, B, s), _lerp(D, Cc, s), t)


def _sub(A, B, Cc, D, s0, s1, t0, t1):
    return [_quad(A, B, Cc, D, s0, t0), _quad(A, B, Cc, D, s1, t0), _quad(A, B, Cc, D, s1, t1), _quad(A, B, Cc, D, s0, t1)]


def _circle(cx, cy, r, n=40, a0=0., a1=TAU):
    return C._ell_pts(cx, cy, r, r, n, a0, a1)


def _arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


# ----------------------------------------------------------------------------------------------
# the subject
# ----------------------------------------------------------------------------------------------

def _sun(cv, sx, sy, r, R, nray=28, rot=0.):
    """A glory: white wedges (each with its own radial hairline) cut out of the sky hatch, round
    a white disc modelled with light horizontal rules and a dark rim on the lower right."""
    for i in range(nray):
        a = rot + TAU * i / nray
        long = i % 2 == 0
        rr = R * (1. if long else .68)
        hw = math.radians(2.4 if long else 1.6)
        wedge = [(sx + r * 1.1 * math.cos(a - hw * 2.2), sy + r * 1.1 * math.sin(a - hw * 2.2)),
                 (sx + rr * math.cos(a - hw), sy + rr * math.sin(a - hw)),
                 (sx + rr * math.cos(a + hw), sy + rr * math.sin(a + hw)),
                 (sx + r * 1.1 * math.cos(a + hw * 2.2), sy + r * 1.1 * math.sin(a + hw * 2.2))]
        cv.obj([wedge], 0)
        cv.hair([(sx + r * 1.2 * math.cos(a), sy + r * 1.2 * math.sin(a)), (sx + rr * .97 * math.cos(a), sy + rr * .97 * math.sin(a))])
    halo = _circle(sx, sy, r * 1.22, 48)
    cv.obj([halo], 0)
    cv.hair(_circle(sx, sy, r * 1.14, 48) + [_circle(sx, sy, r * 1.14, 48)[0]])
    disc = _circle(sx, sy, r, 48)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 3, sy + .5))
    # shadowed crescent lower right: closer rules
    cres = _arc(sx, sy, r, r, -.3, 1.9) + _arc(sx + r * .22, sy + r * .1, r * .86, r * .9, 1.9, -.3)[::1][::-1][::-1]
    cres = _arc(sx, sy, r, r, -.3, 1.9) + _arc(sx + r * .2, sy + r * .1, r * .84, r * .86, 1.9, -.3)
    cv.hair(C.hatch_poly(cres, 0, 1.5, sy))


def _hood(cv, cx, base, w, h):
    """Mt. Hood, small on the horizon: concave flanks flaring from a sharp summit, the lit west
    flank white with glacier gullies, the east flank in shadow, timber at the foot."""
    prof = [(-.5, 0), (-.32, .1), (-.2, .28), (-.11, .52), (-.05, .78), (-.01, .95), (.02, 1.),
            (.05, .9), (.08, .8), (.12, .64), (.2, .4), (.32, .16), (.5, 0)]
    sh = [(cx + w * u, base - h * v) for u, v in prof]
    cv.obj([sh], 1.)
    pk = sh[6]
    ridge = [pk, (cx + w * .015, base - h * .7), (cx + w * .05, base - h * .4), (cx + w * .07, base - h * .12), (cx + w * .08, base)]
    flank = ridge + sh[12:6:-1]
    cv.hair(C.hatch_poly(flank, 0, 1.5))
    cv.hair(C.hatch_poly(flank, 65, 3))
    cv.line(ridge)
    # glacier gullies down the lit flank
    for f in (.12, .22, .34, .48):
        t0 = (cx - w * (.02 + f * .45), base - h * (.92 - f * 1.1))
        cv.hair([t0, (t0[0] - w * .03, t0[1] + h * .18), (t0[0] - w * .035, t0[1] + h * .3)])
    # snowline and timber at the foot
    foot = [(cx - w * .5, base), (cx - w * .3, base - h * .1), (cx - w * .15, base - h * .2),
            (cx + w * .2, base - h * .16), (cx + w * .35, base - h * .08), (cx + w * .5, base)]
    cv.obj([foot], .5)
    cv.hair(C.hatch_poly(foot, 0, 1.5))
    cv.hair(C.hatch_poly(foot, 90, 2))


def _meter(cv, mx, my, r, post_bottom, date_seed):
    """The PGE watt-hour meter on a cedar post: glass dome with highlights, face with three
    register dials, the spinning disc seen edge-on through the window."""
    pw = r * .55
    post = [(mx - pw / 2, my), (mx + pw / 2, my), (mx + pw / 2, post_bottom + 2), (mx - pw / 2, post_bottom + 2)]
    cv.obj([post], 1.)
    # wood grain, shadow side darker
    for i in range(1, 6):
        x = mx - pw / 2 + pw * i / 6
        pts = [(x + .6 * math.sin((y - my) / 7. + i), y) for y in range(int(my), int(post_bottom) + 3, 3)]
        (cv.line if i >= 4 else cv.hair)(pts)
    cv.hair(C.hatch_poly([(mx + pw * .18, my), (mx + pw / 2, my), (mx + pw / 2, post_bottom + 2), (mx + pw * .18, post_bottom + 2)], 0, 2))
    # cast-iron socket base on the post
    base = [(mx - r * .7, my + r * .55), (mx + r * .7, my + r * .55), (mx + r * .5, my + r * 1.1), (mx - r * .5, my + r * 1.1)]
    cv.obj([base], 1.)
    cv.hair(C.hatch_poly(base, 0, 1.5))
    cv.line(C.hatch_poly([(mx + r * .2, my + r * .55), (mx + r * .7, my + r * .55), (mx + r * .5, my + r * 1.1), (mx + r * .15, my + r * 1.1)], 90, 1.5))
    # collar ring (black) and dome
    cy = my - r * .25
    ring = _circle(mx, cy, r * 1.12, 48)
    cv.obj([ring], 1.)
    cv.line(C.hatch_poly(ring, 90, .8))
    dome = _circle(mx, cy, r, 48)
    cv.obj([dome], 1.)
    # face plate
    face = _circle(mx, cy, r * .8, 40)
    cv.obj([face], .5)
    cv.hair(C.hatch_poly(face, 0, 2.5, cy))
    # three register dials across the top of the face
    rng = random.Random(date_seed)
    for k in (-1, 0, 1):
        dx, dy, dr = mx + k * r * .42, cy - r * .3, r * .19
        dial = _circle(dx, dy, dr, 20)
        cv.obj([dial], .5)
        for t in range(10):
            a = TAU * t / 10 - math.pi / 2
            cv.hair([(dx + dr * .72 * math.cos(a), dy + dr * .72 * math.sin(a)), (dx + dr * math.cos(a), dy + dr * math.sin(a))])
        a = -math.pi / 2 + TAU * (rng.random() * .15 if k else .05 + rng.random() * .1)
        cv.line([(dx, dy), (dx + dr * .8 * math.cos(a), dy + dr * .8 * math.sin(a))])
    # the disc window: a slot with the disc edge-on, its black index mark
    sw, shh = r * .55, r * .13
    slot = [(mx - sw, cy + r * .2 - shh), (mx + sw, cy + r * .2 - shh), (mx + sw, cy + r * .2 + shh), (mx - sw, cy + r * .2 + shh)]
    cv.obj([slot], .5)
    cv.line(C.hatch_poly(slot, 0, .8))
    disk = C._ell_pts(mx, cy + r * .2, sw * .9, shh * .45, 30)
    cv.obj([disk], 0)
    cv.hair(disk + [disk[0]])
    cv.line([(mx + sw * .3, cy + r * .2 - shh * .4), (mx + sw * .3, cy + r * .2 + shh * .4)])
    # the maker's mark on the face: a 'P' (Parker's monogram, the second Easter egg)
    ph = r * .26
    px0, py0 = mx - ph * .25, cy + r * .4
    bowl = [(px0, py0)] + _arc(px0, py0 + ph * .27, ph * .32, ph * .27, -math.pi / 2, math.pi / 2, 10) + [(px0, py0 + ph * .54)]
    cv.line([(px0, py0), (px0, py0 + ph)])
    cv.line(bowl)
    for j in range(0):
        y = cy + r * (.46 + .08 * j)
        hw = r * (.5 - .1 * j)
        cv.hair([(mx - hw, y), (mx + hw, y)])
    # glass: curved reflections; shadow side of the dome hatched in arcs
    for f in (.9, .94):
        cv.hair(_arc(mx, cy, r * f, r * f, -.15, 1.35, 18))
    cv.line(_arc(mx, cy, r * .97, r * .97, .1, 1.2, 14))
    cv.hair(_arc(mx, cy, r * .86, r * .86, 3.6, 4.4, 10))


def _roof(cv, A, B, Cc, D, gable, wallh, nx=5, ny=2):
    """Parker's south roof: shingle courses, then the array, then the shaded gable end and walls."""
    # walls under the eave
    front = [A, B, (B[0], B[1] + wallh), (A[0], A[1] + wallh)]
    cv.obj([front], 1.)
    for i in range(int((B[0] - A[0]) / 3)):
        x = A[0] + 1.5 + 3 * i
        cv.hair([(x, A[1] + 1), (x, A[1] + wallh)])
    # window in the front wall, dark
    wx0 = A[0] + (B[0] - A[0]) * .14
    win = [(wx0, A[1] + wallh * .3), (wx0 + wallh * .5, A[1] + wallh * .3), (wx0 + wallh * .5, A[1] + wallh * .8), (wx0, A[1] + wallh * .8)]
    cv.obj([win], 1.)
    cv.line(C.hatch_poly(win, 90, 1.5))
    G, Gb = gable
    side = [B, G, (G[0], G[1] + wallh), (B[0], B[1] + wallh)]
    cv.obj([side], 1.)
    cv.hair(C.hatch_poly(side, 0, 1.5))
    cv.hair(C.hatch_poly(side, 90, 2))
    tri = [B, Cc, G]
    cv.obj([tri], 1.)
    cv.hair(C.hatch_poly(tri, 0, 1.5))
    cv.hair(C.hatch_poly(tri, 70, 3))
    # chimney on the ridge
    chx = _lerp(D, Cc, .2)
    ch = [(chx[0] - 3, chx[1] + 2), (chx[0] + 3, chx[1] + 2), (chx[0] + 3, chx[1] - 9), (chx[0] - 3, chx[1] - 9)]
    # roof plane with shingle courses
    roof = [A, B, Cc, D]
    cv.obj([roof], 1.)
    rows = max(5, int(abs(A[1] - D[1]) / 2))
    for j in range(1, rows):
        t = j / rows
        cv.hair([_quad(A, B, Cc, D, 0, t), _quad(A, B, Cc, D, 1, t)])
        for k in range(1, 24):
            s = (k + (.5 if j % 2 else 0)) / 24
            cv.hair([_quad(A, B, Cc, D, s, t), _quad(A, B, Cc, D, s, t - .6 / rows)])
    cv.obj([ch], 1.)
    cv.hair(C.hatch_poly(ch, 0, 1.5))
    cv.heavy([D, Cc])
    # eave fascia shadow
    cv.obj([[A, B, (B[0], B[1] + 2.4), (A[0], A[1] + 2.4)]], .5)
    cv.line([(A[0], A[1] + 1.6), (B[0], B[1] + 1.6)])
    # the array
    s0, s1, t0, t1 = .07, .93, .1, .9
    gx, gy = .012, .04
    for i in range(nx):
        for j in range(ny):
            ps0 = s0 + (s1 - s0) * i / nx + gx
            ps1 = s0 + (s1 - s0) * (i + 1) / nx - gx
            pt0 = t0 + (t1 - t0) * j / ny + gy
            pt1 = t0 + (t1 - t0) * (j + 1) / ny - gy
            pan = _sub(A, B, Cc, D, ps0, ps1, pt0, pt1)
            cv.obj([pan], 1.)
            ci, cj = 3, 4
            for a in range(ci):
                for b in range(cj):
                    u0 = ps0 + (ps1 - ps0) * (a + .1) / ci
                    u1 = ps0 + (ps1 - ps0) * (a + .9) / ci
                    v0 = pt0 + (pt1 - pt0) * (b + .12) / cj
                    v1 = pt0 + (pt1 - pt0) * (b + .88) / cj
                    cell = _sub(A, B, Cc, D, u0, u1, v0, v1)
                    # the sun's glint runs as a light diagonal across the array
                    g = (i * ci + a) / (nx * ci) - (1 - (j * cj + b) / (ny * cj)) * .35
                    lit = abs(g - .38) < .07
                    if lit:
                        cv.hair(C.hatch_poly(cell, 0, 3, .3))
                    else:
                        cv.line(C.hatch_poly(cell, 0, 2, .3))
                        cv.hair(C.hatch_poly(cell, 75, 2))


def scene(x, y, W, H, seed=0, full=True):
    """The vignette, filling the box x, y, W, H edge to edge (caller clips it to the field)."""
    cv = C.Canvas()
    S = min(W, H)
    P = lambda u, v: (x + u * W, y + v * H)
    hz = y + H * (.6 if full else .66)
    # sky: horizontal rules, closer (darker) toward the zenith
    sky = [(x - 2, y - 2), (x + W + 2, y - 2), (x + W + 2, hz + 1), (x - 2, hz + 1)]
    cv.obj([], 0)
    top = [(x - 2, y - 2), (x + W + 2, y - 2), (x + W + 2, y + H * .22), (x - 2, y + H * .22)]
    cv.hair(C.hatch_poly(top, 0, 1.5))
    cv.hair(C.hatch_poly([(x - 2, y + H * .22), (x + W + 2, y + H * .22), (x + W + 2, hz + 1), (x - 2, hz + 1)], 0, 2, .5))
    # low November sun to the south-west
    sx, sy = x + W * (.24 if full else .5), y + H * (.28 if full else .4)
    _sun(cv, sx, sy, S * (.11 if full else .14), S * (.62 if full else .75), 32 if full else 24, (seed % 7) * .03)
    if full:
        # a flight of geese in the winter sky
        for k in range(5):
            gxp, gyp = x + W * (.62 + .045 * k), y + H * (.14 + .02 * abs(k - 2))
            cv.line([(gxp - 2.4, gyp - 1.1), (gxp, gyp), (gxp + 2.4, gyp - 1.1)])
        # Mt. Hood on the eastern horizon (the Easter egg)
        _hood(cv, x + W * .5, hz, W * .46, H * .17)
    # far hills of the Tualatin range, darker
    hills = [(x - 2, hz + 1)] + [(x + W * i / 30, hz - H * (.035 + .02 * math.sin(i * .7 + seed) + .012 * math.sin(i * 1.9))) for i in range(31)] + [(x + W + 2, hz + 1)]
    if full:
        hills = [(px, py) if not (x + W * .33 < px < x + W * .67) else (px, max(py, hz - H * .02)) for px, py in hills]
    cv.obj([hills], .5)
    cv.hair(C.hatch_poly(hills, 0, 1.5, .25))
    # the island: fields in furrows running to the horizon, darker in the foreground
    ground = [(x - 2, hz), (x + W + 2, hz), (x + W + 2, y + H + 2), (x - 2, y + H + 2)]
    cv.obj([ground], 1.)
    vx = x + W * .45
    for k in range(-24, 25):
        bx = vx + k * W / 14
        cv.hair([(vx + k * W / 90, hz + 1), (bx, y + H + 2)])
    for j in range(1, 30):
        f = (j / 29) ** 1.25
        yy = hz + (y + H - hz) * f
        cv.hair([(x - 2, yy), (x + W + 2, yy)])
    if full:
        # a hedgerow along the horizon
        hedge = [(x - 2, hz + 3)] + [(x + W * i / 40, hz - 1 - 1.5 * abs(math.sin(i * 1.7))) for i in range(41)] + [(x + W + 2, hz + 3)]
        cv.obj([hedge], .5)
        cv.line(C.hatch_poly(hedge, 0, 1.))
        # the house and its roof array
        A, B = P(.02, .8), P(.56, .8)
        Dd, Cc = P(.1, .58), P(.53, .58)
        G = P(.66, .75)
        # the house's shadow thrown across the field toward us
        shd = [P(.56, .92), P(.66, .87), P(.8, .96), P(.72, 1.02), P(.5, 1.02)]
        cv.obj([], 0)
        cv.hair(C.hatch_poly(shd, 0, 1.))
        _roof(cv, A, B, Cc, Dd, (G, None), H * .13)
        # the meter on its post, foreground right
        mr = S * .15
        _meter(cv, x + W * .84, y + H * .74, mr, y + H, seed)
    else:
        # a mini array on the ground, tilted to the sun
        for k in (-1, 0, 1):
            cx0 = x + W * (.5 + .27 * k)
            A, B = (cx0 - W * .12, hz + H * .2), (cx0 + W * .12, hz + H * .2)
            Dd, Cc = (cx0 - W * .1, hz + H * .02), (cx0 + W * .1, hz + H * .02)
            pan = [A, B, Cc, Dd]
            cv.obj([pan], 1.)
            cv.line(C.hatch_poly(pan, 0, 2, .3))
            for s in (1 / 3, 2 / 3):
                cv.hair([_lerp(A, B, s), _lerp(Dd, Cc, s)])
            cv.hair([_lerp(A, Dd, .5), _lerp(B, Cc, .5)])
            cv.line([(cx0, hz + H * .2), (cx0, y + H)])
    return cv.svg()


def _eye_sun(cv, x, y, r):
    """A small sun set in a volute's eye: a black ring of pointed rays round a white disc with a
    hatched lower half."""
    rays = []
    for i in range(12):
        a = TAU * i / 12
        rays += [(x + r * 1.9 * math.cos(a), y + r * 1.9 * math.sin(a)), (x + r * 1.15 * math.cos(a + TAU / 24), y + r * 1.15 * math.sin(a + TAU / 24))]
    cv.obj([rays], 1.)
    cv.line(C.hatch_poly(rays, 30, .9))
    disc = _circle(x, y, r * 1.05, 24)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(_circle(x, y, r, 24, 0, math.pi), 0, 1.5, y + .3))
    cv.line([(x - r * .45, y - r * .25), (x - r * .15, y - r * .25)])
    cv.line([(x + r * .15, y - r * .25), (x + r * .45, y - r * .25)])


def _clipped(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, re-cut so the vignette fills the whole field)
# ----------------------------------------------------------------------------------------------

def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.6, 120)
    o.append(C._clip(C._uid("sb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 4.5, ry - 4.5
    field = C._ell_pts(cx, cy, fx, fy, 64)
    o.append(_clipped(C._uid("sbf", w, h, seed), _d(field, True, 0), scene(cx - fx, cy - fy, 2 * fx, 2 * fy, seed, False)))
    o.append(f'<path d="{_d(field, True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _cart_field(cx, cy, cw, ch, seed, body_fn):
    """House cartouche whose whole field (not just its inner rect) carries the vignette."""
    c, _, _ = C.cartouche(cx, cy, cw, ch, seed)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    fa, fb = a - 5.5, b - 5.5
    field = C._superellipse(cx, cy, fa, fb)
    d = _d(field, True, .1)
    return (c + _clipped(C._uid("cf", cx, cy, cw, ch), d, body_fn(cx - fa, cy - fb, 2 * fa, 2 * fb))
            + f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>')


def _medium(w, h, seed):
    rng = random.Random(seed)
    o = []
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
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .06), rmax=r * .8,
                   max_n=16, edge=.7, cv=cv)
    cv.extend(main)
    # each great volute winds into a sun: the scroll's eye carved as a rayed disc
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        a0, fl = (90., True) if side < 0 else (90., False)
        ex, ey = C.volute_spine(vx, gy0 + gh * .5, r, a0, 1.4, fl, .9, -.5)[-1]
        _eye_sun(cv, ex, ey, max(3.2, r * .11))
    o.append(C._clip(C._uid("sm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    o.append(_cart_field(cx, cy, cw, gh + 4, rng.randrange(1 << 20), lambda X, Y, W, H: scene(X, Y, W, H, seed, gh > 90)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


# the year of bills on the page's chart, Oct..Oct (share of the $635 December peak)
_BILLS = [.13, .6, 1., .5, .55, .38, .08, .02, .02, .02, .02, .02, .03]


def _tablet_bars(x, y, w, h):
    """The pedestal tablet engraved with the year of PGE bills: ruled ground, thirteen carved
    bars (heavy winter, nothing all summer), the last one, today's, marked with a small sun."""
    cv = C.Canvas()
    box = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([box], 0)
    cv.hair(C.hatch_poly(box, 0, 2))
    n = len(_BILLS)
    bw = w / n
    base = y + h - 2.5
    for i, v in enumerate(_BILLS):
        bh = max(1.2, (h - 6) * v)
        bar = [(x + i * bw + bw * .18, base - bh), (x + (i + 1) * bw - bw * .18, base - bh),
               (x + (i + 1) * bw - bw * .18, base), (x + i * bw + bw * .18, base)]
        cv.obj([bar], 1.)
        cv.hair(C.hatch_poly(bar, 90, 1.5))
    cv.obj([], 0)
    cv.line([(x + 1, base + .5), (x + w - 1, base + .5)])
    _eye_sun(cv, x + (n - .5) * bw, base - 6, 2.2)
    return cv.svg()


def _tall(w, h, seed):
    R = C
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(R.dark_ground((0, 0, w, h), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(R.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = R.Canvas(), R.Canvas()
    r1 = min(pw * .18, ph * .25)
    eyes = []
    for side in (-1, 1):
        vx, vy = cx + side * (cw * .5 + r1 * .55), py0 + ph - r1 * 1.1
        R._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
        a0, fl = (100., True) if side < 0 else (80., False)
        eyes.append((R.volute_spine(vx, vy, r1, a0, 1.45, fl, .8, -.5)[-1], r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx, vy = cx + side * (cw * .5 + r2 * .55), py0 + r2 * 1.1
        R._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    R.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .04), rmax=r1 * .9,
                   max_n=12, edge=.6, cv=cv)
    cv.extend(main)
    for (ex, ey), rr in eyes:
        _eye_sun(cv, ex, ey, max(3.5, rr * .1))
    o.append(R._clip(R._uid("st", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    o.append(_cart_field(cx, cy, cw, ch, rng.randrange(1 << 20), lambda X, Y, W, H: scene(X, Y, W, H, seed, True)))
    o.append(R.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bsvg, face = R.ribbon_banner(cx, cy + ch * .47, cw * 1.4, min(16, ph * .05), .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # the banner's face ruled lightly, so no bare paper shows
    if len(face) > 1:
        bh = min(16, ph * .05) * .32
        o.append('<path d="' + "".join(_d([(fx, fy + k * 2.) for fx, fy in face], tol=.3) for k in range(-int(bh / 2), int(bh / 2) + 1))
                 + '" stroke="#000" stroke-width=".5"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = R.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet_bars(tx + 3, ty + 3, tw - 5, th - 5))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(R.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(R._clip(R._uid("sf", w, h, seed), 0, fy, w, fh - 2,
                         R.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(R.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", "")))
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
