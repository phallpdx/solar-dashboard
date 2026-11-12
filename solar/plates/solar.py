"""Solar ("Sun and power") plate: the sun, spotted with today's sunspots, rising over Parker's
Sauvie Island roof with its panel array, Mt. Hood on the horizon, all cut in the house Codex style.
The two main volutes of the frame wind into small suns. Easter egg: his dog sitting in the field."""
import sys
import math
import random
import zlib
import engraving_codex as C

PI = math.pi
_n = C._n
_d = C._d


def _seed(ctx):
    return zlib.crc32(((ctx or {}).get("date", "") + "solar").encode()) & 0xffff


def _poly_rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _quad(q, u, v):
    """bilinear point in quad q = [tl, tr, br, bl]"""
    top = _lerp(q[0], q[1], u)
    bot = _lerp(q[3], q[2], u)
    return _lerp(top, bot, v)


def _clip_path(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def _taper(cv, pts, w0, side=1, shade=3, outline=.5):
    """A tapered ribbon along centre line pts (width w0 at the root, a point at the tip), white
    with lines running along it on one side."""
    n = len(pts)
    L = []
    R = []
    nrm = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nrm.append((-dy / d, dx / d))
    for i, (p, nn) in enumerate(zip(pts, nrm)):
        ww = w0 * (1 - i / (n - 1)) ** .9 / 2
        L.append((p[0] + nn[0] * ww, p[1] + nn[1] * ww))
        R.append((p[0] - nn[0] * ww, p[1] - nn[1] * ww))
    cv.obj([L + R[::-1]], outline)
    for k in range(1, shade + 1):
        f = side * k / (shade + 1)
        line = []
        for i, (p, nn) in enumerate(zip(pts, nrm)):
            ww = w0 * (1 - i / (n - 1)) ** .9 / 2
            if i < n - 2:
                line.append((p[0] + nn[0] * ww * f, p[1] + nn[1] * ww * f))
        cv.hair(line[: max(2, int(len(line) * (1 - .25 * k / shade)))])


def _sun(cv, cx, cy, r, rng, ray_out, spots=True):
    """Engraved sun: a glory of fine radiating hairlines, alternating straight hatched wedges and
    flame rays, a white disc with limb shading and today's sunspots."""
    n = 16
    # glory: fine radiating hairlines filling the halo
    cv.obj([C._ell_pts(cx, cy, ray_out * .93, ray_out * .93, 48)[:-1]], 0)
    m = int(max(60, r * 9))
    for i in range(m):
        a = TAU_ * i / m
        L = ray_out * (.93 if i % 3 == 0 else (.82 if i % 3 == 1 else .7))
        cv.hair([(cx + r * 1.08 * math.cos(a), cy + r * 1.08 * math.sin(a)), (cx + L * math.cos(a), cy + L * math.sin(a))])
    for i in range(2 * n):
        a = -PI / 2 + TAU_ * i / (2 * n)
        big = i % 2 == 0
        L = ray_out * ((1.12 if i % 4 == 0 else .98) if big else .7)
        hw = TAU_ / (2 * n) * (.62 if big else .42)
        p0 = (cx + r * 1.02 * math.cos(a - hw), cy + r * 1.02 * math.sin(a - hw))
        p1 = (cx + r * 1.02 * math.cos(a + hw), cy + r * 1.02 * math.sin(a + hw))
        tip = (cx + L * math.cos(a), cy + L * math.sin(a))
        mid = (cx + r * 1.02 * math.cos(a), cy + r * 1.02 * math.sin(a))
        cv.obj([[p0, tip, p1]], .5)
        # the shaded flank: lines converging on the tip; the lit flank stays white
        kk = 5 if big else 3
        for k in range(1, kk + 1):
            q0 = _lerp(mid, p1, k / (kk + 1.))
            cv.hair([q0, _lerp(q0, tip, .97 - .5 / kk * k)])
        cv.line([mid, _lerp(mid, tip, .9)] if big else [mid, _lerp(mid, tip, .6)])
    # disc: fine concentric bulino rings, closer toward the limb, heavier on the lower right
    disc = C._ell_pts(cx, cy, r, r, 56)[:-1]
    cv.obj([disc], 1.)
    yy = cy - r + 1.5
    while yy < cy + r - .5:
        dy = yy - cy
        hw = math.sqrt(max(0., r * r - dy * dy)) - .8
        # the upper-left is the hot side: lines there start late, leaving it brighter
        lit = max(0., (-(dy) / r) * .7 + .25)
        x0 = cx - hw + 2 * hw * lit * .55
        if cx + hw - x0 > 1.5:
            cv.hair([(x0, yy), (cx + hw, yy)])
        yy += 2. if dy > 0 else 3.
    for f in (.95, .9, .85, .8):
        cv.hair(C._ell_pts(cx, cy, r * f, r * f, 40, -.1, PI * .62))
    # sunspots: umbra (solid) with a ruled penumbra, grouped like an active region
    if spots:
        groups = [(rng.uniform(-.5, .3), rng.uniform(-.45, -.1)), (rng.uniform(-.2, .45), rng.uniform(.1, .4))]
        for gx, gy in groups:
            for j in range(rng.randint(2, 3)):
                sx = cx + r * (gx + j * .17 * rng.uniform(.8, 1.2))
                sy = cy + r * (gy + rng.uniform(-.06, .06))
                s = max(.6, r * rng.uniform(.035, .07) * (1.3 if j == 0 else .9))
                cv.obj([C._ell_pts(sx, sy, s + 1.3, s + 1.1, 14)[:-1]], .5)
                q = s
                while q > .2:
                    cv.line(C._ell_pts(sx, sy, q, q * .85, 10))
                    q -= .7
                cv.line([(sx - .3, sy), (sx + .3, sy)])


TAU_ = 2 * PI


def _mt_hood(cv, x, base, s):
    """Mt. Hood: the summit horn, a long west shoulder, a steep east face in shadow, glaciers cut
    by dark ridges, a forested foot."""
    H = s * .6
    prof = [(-.95, 0), (-.7, .1), (-.5, .22), (-.32, .38), (-.18, .58), (-.08, .8), (-.03, .93), (.02, 1.),
            (.06, .96), (.1, .9), (.16, .78), (.26, .58), (.4, .38), (.58, .2), (.8, .08), (1.0, 0)]
    P = [(x + px * s * .6, base - py * H) for px, py in prof]
    cv.obj([P], .5)
    pk = P[7]
    # east (right) face in shadow: lines parallel to the slope, dense
    east = P[7:] + [(x + .02 * s * .6, base)]
    cv.hair(C.hatch_poly(east, 0, 1.5, phase=.75))
    cv.hair(C.hatch_poly(east, -60, 3))
    # west face: light ruling low down, snow white above
    west = P[:8] + [(x + .02 * s * .6, base)]
    cv.hair(C.hatch_poly(west, 40, 3))
    snow = [(px, py) for px, py in west]
    # glaciers: short broken gully strokes on the snowfields, a dark shadow line under the horn
    rng = random.Random(int(x * 7 + s))
    for j in range(int(s * .5)):
        t = rng.uniform(-.8, .15)
        hy = rng.uniform(.25, .75)
        gx = x + t * s * .6 * (1 - hy * .7)
        gy = base - H * hy
        cv.hair([(gx, gy), (gx + s * .015, gy + H * .07)])
    cv.line([P[6], P[5], P[4]])
    # snowline: white above, so cover lower west ruling with a dark-ish band of forest
    foot = [(x - .95 * s * .6, base + 1)]
    k = 0
    xx = x - .95 * s * .6
    while xx < x + s * .6:
        foot.append((xx, base - H * (.16 + .06 * math.sin(k * 1.7)) * (1 - abs(xx - x) / (s * .6))))
        xx += 2.5
        k += 1
    foot.append((x + s * .6, base + 1))
    cv.obj([foot], .5)
    cv.line(C.hatch_poly(foot, 0, 1.5))


def _treeline(cv, x0, x1, y, hgt, rng):
    """A dark band of firs and cottonwoods along the far bank."""
    pts = [(x0, y + 2)]
    x = x0
    while x < x1:
        if rng.random() < .6:
            w = rng.uniform(2, 3.2)
            hh = hgt * rng.uniform(.6, 1.)
            pts += [(x + w * .5, y - hh), (x + w, y - hgt * .3)]
        else:
            w = rng.uniform(4, 7)
            hh = hgt * rng.uniform(.5, .75)
            pts += [(x + w * .2, y - hh * .9), (x + w * .5, y - hh), (x + w * .8, y - hh * .85), (x + w, y - hgt * .3)]
        x += w
    pts.append((x1, y + 2))
    cv.obj([pts], .5)
    cv.line(C.hatch_poly(pts, 0, 1.5))


def _house(cv, x0, x1, eave, ground, ridge_h, rng, sun_x):
    """A long farmhouse seen from the south: a hipped roof covered with a panel array, board-and-
    batten wall, windows and a door."""
    W = x1 - x0
    ridge = eave - ridge_h
    inset = ridge_h * .9
    over = W * .03
    roof = [(x0 + inset, ridge), (x1 - inset, ridge), (x1 + over, eave), (x0 - over, eave)]
    # wall
    wall = _poly_rect(x0, eave, x1, ground)
    cv.obj([wall], 1.)
    x = x0 + 1.5
    while x < x1 - .5:
        cv.hair([(x, eave + 1), (x, ground)])
        x += 3
    # deep eave shadow
    for k in range(3):
        cv.line([(x0, eave + .8 + k * .8), (x1, eave + .8 + k * .8)])
    # windows and door
    nwin = max(2, int(W / 26))
    wh = (ground - eave) * .45
    for i in range(nwin):
        cxw = x0 + W * (i + .5) / nwin
        if i == nwin // 2:
            dw = max(4, W * .05)
            door = _poly_rect(cxw - dw / 2, ground - (ground - eave) * .72, cxw + dw / 2, ground)
            cv.obj([door], 1.)
            cv.line(C.hatch_poly(door, 90, 1.5))
            continue
        ww = max(4, W * .06)
        win = _poly_rect(cxw - ww / 2, eave + (ground - eave) * .3, cxw + ww / 2, eave + (ground - eave) * .3 + wh)
        cv.obj([win], 1.)
        cv.line(C.hatch_poly(win, 0, 1.5))
        cv.hair([((win[0][0] + win[1][0]) / 2, win[0][1]), ((win[0][0] + win[1][0]) / 2, win[2][1])])
    # roof
    cv.obj([roof], 1.)
    # hip ends shaded
    for side in (0, 1):
        tri = ([roof[0], roof[3], (roof[0][0], eave)] if side == 0 else [roof[1], roof[2], (roof[1][0], eave)])
        cv.hair(C.hatch_poly(tri, 0, 2 if side == 0 else 1.5))
    # panel array on the main plane
    q = [(roof[0][0] + 1.5, ridge + 1.5), (roof[1][0] - 1.5, ridge + 1.5),
         (roof[1][0] + (roof[2][0] - roof[1][0]) * .85, eave - 2), (roof[0][0] + (roof[3][0] - roof[0][0]) * .85, eave - 2)]
    rows = 2 if ridge_h < 22 else 3
    top_w = q[1][0] - q[0][0]
    cols = max(4, int(top_w / max(7., ridge_h * .5)))
    gap = .9
    glint_u = (sun_x - q[0][0]) / max(1., top_w)
    for i in range(rows):
        for j in range(cols):
            u0, u1 = j / cols, (j + 1) / cols
            v0, v1 = i / rows, (i + 1) / rows
            p = [_quad(q, u0, v0), _quad(q, u1, v0), _quad(q, u1, v1), _quad(q, u0, v1)]
            # shrink for frame gap
            cxp = sum(t[0] for t in p) / 4
            cyp = sum(t[1] for t in p) / 4
            pp = [(cxp + (t[0] - cxp) * (1 - gap * 2 / max(4, abs(p[1][0] - p[0][0]))),
                   cyp + (t[1] - cyp) * (1 - gap * 2 / max(4, abs(p[3][1] - p[0][1])))) for t in p]
            cv.obj([pp], .5)
            # dark glass: dense lines down the slope, a white glint where the sun strikes
            hl = C.hatch_poly(pp, 0, 1.5)
            gl = abs((u0 + u1) / 2 - glint_u - (v0 - .5) * .25)
            if gl < .12:
                hl = hl[::2]
            cv.line(hl)
            # cell divisions (hair) along the slope
            cv.hair([_lerp(pp[0], pp[1], .5), _lerp(pp[3], pp[2], .5)])
    # ridge cap
    cv.heavy([roof[0], roof[1]])
    # chimney / vent pipe
    return roof


def _dog(cv, x, y, s, flip=False):
    """Tiny sitting dog silhouette (Parker's), facing the house; feet at (x, y), height ~ s."""
    f = -1 if flip else 1
    P = [(-.30, 0), (-.34, -.18), (-.30, -.42), (-.18, -.62), (-.08, -.72), (.02, -.80), (.04, -.95),
         (.12, -1.0), (.16, -.97), (.22, -.93), (.38, -.90), (.40, -.84), (.24, -.78), (.16, -.70),
         (.12, -.45), (.14, -.2), (.18, -.05), (.20, 0), (.06, 0), (.0, -.18), (-.08, -.05), (-.14, 0)]
    pts = [(x + f * px * s, y + py * s) for px, py in P]
    cv.obj([pts], .5)
    cv.line(C.hatch_poly(pts, 90, 1.) )
    # ear and tail
    cv.line([(x + f * .06 * s, y - .93 * s), (x - f * .02 * s, y - .78 * s)])
    cv.line([(x - f * .3 * s, y - .06 * s), (x - f * .5 * s, y - .02 * s), (x - f * .58 * s, y - .12 * s)])


def scene(field, fx, fy, fw, fh, seed, cid):
    """Draw the vignette into the whole field (polygon `field`, bbox fx, fy, fw, fh)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    hz = fy + fh * .64
    # sky: horizontal ruling, open near the sun
    sky = _poly_rect(fx - 2, fy - 2, fx + fw + 2, hz + 2)
    sun_x, sun_y = fx + fw * .47, fy + fh * .36
    r = min(fw, fh) * .15
    cv.obj([sky], 0)
    y = fy - 1
    i = 0
    while y < hz + 2:
        dy = y - sun_y
        # break each line around the sun's glow
        g = r * 2.1
        if abs(dy) < g:
            hw = math.sqrt(g * g - dy * dy)
            cv.hair([(fx - 2, y), (sun_x - hw, y)])
            cv.hair([(sun_x + hw, y), (fx + fw + 2, y)])
        else:
            cv.hair([(fx - 2, y), (fx + fw + 2, y)])
        # double the ruling toward the zenith for a darker sky
        if y < sun_y - r * 1.4 and (y - fy) < fh * .2:
            cv.hair([(fx - 2, y + 1), (fx + fw + 2, y + 1)])
        y += 2 if (y - fy) > fh * .2 else 3
        i += 1
    # clouds: two long lenticular bands cut white with a hatched underside
    for cxl, cyl, lw in ((fx + fw * .16, fy + fh * .2, fw * .22), (fx + fw * .82, fy + fh * .28, fw * .2)):
        top = [(cxl - lw / 2 + lw * t, cyl - math.sin(PI * t) * fh * .05 - abs(math.sin(PI * t * 3)) * fh * .015) for t in [k / 20 for k in range(21)]]
        bot = [(cxl + lw / 2 - lw * t, cyl + math.sin(PI * t) * fh * .015) for t in [k / 20 for k in range(21)]]
        cl = top + bot
        cv.obj([cl], .5)
        cv.hair(C.hatch_poly(cl, 0, 1.5, phase=.5))
    _sun(cv, sun_x, sun_y, r, rng, r * 2.3, spots=True)
    # Mt. Hood on the horizon, left
    _mt_hood(cv, fx + fw * .17, hz, min(fw * .4, fh * .62))
    _treeline(cv, fx - 2, fx + fw + 2, hz, fh * .05, rng)
    # foreground field: ruled ground opening toward the viewer, rows of stubble, a lane to the door
    gnd = _poly_rect(fx - 2, hz, fx + fw + 2, fy + fh + 2)
    cv.obj([gnd], 0)
    yy = hz + 1.5
    st = 1.5
    while yy < fy + fh + 2:
        cv.hair([(fx - 2 + t * (fw + 4) / 30, yy + .25 * math.sin(t * 1.3 + yy)) for t in range(31)])
        yy += st
        st = min(2, st + .1)
    for k in range(int(fw / 2.2)):
        tx = fx + rng.uniform(0, fw)
        ty = hz + fh * rng.uniform(.15, .36)
        sz = .6 + (ty - hz) / fh * 5
        cv.hair([(tx - sz * .4, ty - sz), (tx, ty), (tx + sz * .1, ty - sz * 1.2)])
        cv.hair([(tx + sz * .2, ty), (tx + sz * .5, ty - sz * .8)])
    # the house
    hx0, hx1 = fx + fw * .40, fx + fw * .92
    u = min(fh, fw * .66)
    eave = hz - u * .02
    ground = hz + u * .13
    ridge_h = u * .19
    _house(cv, hx0, hx1, eave, ground, ridge_h, rng, sun_x)
    # Easter egg: the dog in the field, watching the sun come up
    _dog(cv, fx + fw * .30, ground + u * .07, max(7., u * .13))
    return _clip_path(cid, _d(field, True, 0), cv.svg())


# ----------------------------------------------------------------------------------------------
# small suns in the eyes of the main volutes ("the scroll winds into the sun")
# ----------------------------------------------------------------------------------------------

def _eye_sun(cx, cy, r):
    cv = C.Canvas()
    cv.obj([C._ell_pts(cx, cy, r * 2.1, r * 2.1, 24)[:-1]], 0)
    for i in range(12):
        a = TAU_ * i / 12
        L = r * (2.05 if i % 2 == 0 else 1.6)
        w = .32
        cv.obj([[(cx + r * 1.05 * math.cos(a - w), cy + r * 1.05 * math.sin(a - w)),
                 (cx + L * math.cos(a), cy + L * math.sin(a)),
                 (cx + r * 1.05 * math.cos(a + w), cy + r * 1.05 * math.sin(a + w))]], .5)
        cv.hair([(cx + r * 1.1 * math.cos(a + .1), cy + r * 1.1 * math.sin(a + .1)),
                 (cx + L * .9 * math.cos(a + .02), cy + L * .9 * math.sin(a + .02))])
    cv.obj([C._ell_pts(cx, cy, r, r, 24)[:-1]], 1.)
    cv.hair(C._ell_pts(cx, cy, r * .65, r * .65, 20, .3, 2.9))
    cv.line(C._ell_pts(cx, cy, .6, .6, 8))
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts
# ----------------------------------------------------------------------------------------------

def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.9)
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
        a0, flip = (90, True) if side < 0 else (90, False)
        sp = C.volute_spine(vx, vy, r, a0, 1.4, flip, .9, -.5, .13)
        eyes.append(sp[-1])
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    body = cv.svg() + "".join(_eye_sun(ex, ey, max(3., r * .1)) for ex, ey in eyes)
    o.append(C._clip(C._uid("sm", w, h, seed), 0, gy0, w, gh, body))
    c, rect, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_from_rect(rect, "se", seed, w, h))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return C.svg_doc(w, h, "".join(o))


def _field_from_rect(rect, kind, seed, w, h):
    ix, iy, iw, ih = rect
    cx, cy = ix + iw / 2, iy + ih / 2
    if kind == "se":
        k = 2 ** (-1 / 2.6)
        a, b = iw / 2 / k + 6, ih / 2 / k + 6
        field = C._superellipse(cx, cy, a + .4, b + .4)
    else:
        rx, ry = iw / 2 / .7071 + 5, ih / 2 / .7071 + 5
        a, b = rx - 2, ry - 2
        field = C._ell_pts(cx, cy, a, b, 64)[:-1]
    return scene(field, cx - a, cy - b, 2 * a, 2 * b, seed, C._uid("sf", w, h, seed, kind))


def _p_monogram(cx, cy, hgt):
    """A small engraved 'P' (Parker's): heavy stem with serifs, a bowl, drawn as strokes."""
    cv = C.Canvas()
    w = hgt * .6
    x0 = cx - w * .4
    top, bot = cy - hgt / 2, cy + hgt / 2
    cv.obj([_poly_rect(x0 - 2, top - 1.5, x0 + w + 1.5, bot + 1.5)], 0)
    cv.heavy([(x0, top), (x0, bot)])
    cv.line([(x0 + 1, top), (x0 + 1, bot)])
    cv.line([(x0 - 1.5, bot), (x0 + 2.5, bot)])
    cv.line([(x0 - 1.5, top), (x0, top)])
    bowl = [(x0, top)] + [(x0 + w * .45 + w * .45 * math.sin(t * PI), top + hgt * .27 - hgt * .27 * math.cos(t * PI))
                          for t in [k / 12 for k in range(13)]] + [(x0, top + hgt * .54)]
    cv.heavy(bowl[1:-1])
    cv.hair([(x0 + w * .45 + w * .3 * math.sin(t * PI), top + hgt * .27 - (hgt * .27 - 1.2) * math.cos(t * PI)) for t in [k / 10 for k in range(11)]])
    cv.line([bowl[0], bowl[1]])
    cv.line([bowl[-2], bowl[-1]])
    return cv.svg()


def _banner_face(centre, bh):
    """Rule the banner's face (parallel hairlines that follow its arch) and set Parker's P in it."""
    o = []
    d = ""
    for off in (-.42, -.21, 0., .21, .42):
        pts = [(x, y + off * bh) for x, y in centre]
        mid = len(pts) // 2
        gap = max(3, int(len(pts) * .06))
        d += _d(pts[:mid - gap]) + _d(pts[mid + gap:])
    o.append(f'<path d="{d}" stroke="#000" stroke-width=".5"/>')
    cx, cy = centre[len(centre) // 2]
    o.append(_p_monogram(cx, cy, bh * .62))
    return "".join(o)


def _tablet(tx, ty, tw, th, seed):
    """The pedestal tablet engraved with today's sun curve: output from dawn to dusk as a hatched
    bell, the best hours (10 am to 1 pm) cross-hatched, hour ticks along the base, ruled sky."""
    cv = C.Canvas()
    x0, x1 = tx + 3, tx + tw - 2
    y1 = ty + th - 2.5
    y0 = ty + 3
    cv.obj([_poly_rect(tx + 2, ty + 2, tx + tw - 1, ty + th - 1)], 0)
    yy = y0
    while yy < y1:
        cv.hair([(x0, yy), (x1, yy)])
        yy += 3
    # bell from 7 am to 5 pm (November), peak at noon
    def f(hh):
        return max(0., math.cos((hh - 12) / 5.2 * PI / 2)) ** 1.6
    pts = []
    for k in range(81):
        hh = 7 + 10 * k / 80
        pts.append((x0 + (x1 - x0) * (hh - 6) / 12, y1 - (y1 - y0 - 1) * f(hh)))
    bell = pts + [(pts[-1][0], y1), (pts[0][0], y1)]
    cv.obj([bell], 1.)
    cv.line(C.hatch_poly(bell, 90, 2))
    best = [p for p in pts if x0 + (x1 - x0) * 4 / 12 <= p[0] <= x0 + (x1 - x0) * 7 / 12]
    bp = best + [(best[-1][0], y1), (best[0][0], y1)]
    cv.obj([bp], .5)
    cv.heavy(C.hatch_poly(bp, 90, 1.5))
    # sun riding the peak
    sx, sy = x0 + (x1 - x0) * .5, y0 + 1
    cv.obj([C._ell_pts(sx, sy + 1.5, 2.4, 2.4, 12)[:-1]], 1.)
    for k in range(13):
        hx = x0 + (x1 - x0) * k / 12
        cv.line([(hx, y1), (hx, y1 - (2.5 if k % 3 == 0 else 1.2))])
    cv.line([(x0, y1), (x1, y1)])
    return cv.svg()


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    em = 9.
    o.append(C.egg_and_dart(0, 0, w, em))
    px0, py0 = 0., em + 1
    pw = w
    ph = h - py0 - ped_h + ped_h * .3
    o.append(C.dark_ground((0, py0, w, h - py0), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        a0, flip = (90 + 10, True) if side < 0 else (90 - 10, False)
        eyes.append((C.volute_spine(vx, vy, r1, a0, 1.45, flip, .8, -.5, .13)[-1], r1))
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        a0, flip = (-90 - (-10), False) if side < 0 else (-90 + (-10), True)
        eyes.append((C.volute_spine(vx, vy, r2, a0, 1.4, flip, .8, .5, .13)[-1], r2))
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    body = cv.svg() + "".join(_eye_sun(ex, ey, max(3., rr * .09)) for (ex, ey), rr in eyes)
    o.append(C._clip(C._uid("st", w, h, seed), px0, py0, pw, ph, body))
    c, rect, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_from_rect(rect, "se", seed, w, h))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2, 56), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_face(centre, bh))
    py = h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, seed))
    return C.svg_doc(w, h, "".join(o))


def plate(w, h, ctx):
    seed = _seed(ctx)
    if 110 <= h <= 260:
        return _layout_medium(w, h, seed)
    if h > 260:
        return _layout_tall(w, h, seed)
    return C.frame_plate(w, h, seed, lambda x, y, ww, hh: _field_from_rect((x, y, ww, hh), "el", seed, w, h))
