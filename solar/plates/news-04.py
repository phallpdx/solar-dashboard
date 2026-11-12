"""news-04 "Consumer reviews" (hands-on A/V reviews: Sony headphones, Acoustic Energy speakers,
the TEAC headphone amp with its 'Godzilla' volume knob). The plate engraves the listening bench:
a pair of over-ear headphones under an arch of five review stars, set on an engine-turned field of
sound rings; taller plates add the amp with VU meters and its big knurled knob, a pair of
bookshelf speakers on a wood-grained shelf, a starred ribbon banner and a pedestal tablet carrying
a frequency-response curve. Easter egg: Parker's 'P' monogram on the headband plaque (and, on tall
plates, a beamed pair of swing eighth notes at the end of the response curve)."""
import sys
import math
import random
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
TAU = math.tau


# ------------------------------------------------------------------------------------------------
# small engraved parts (all draw into a Canvas)
# ------------------------------------------------------------------------------------------------

def _solid(cv, poly):
    """A black mass: 1 px lines 0.8 px apart."""
    cv.line(C.hatch_poly(poly, 0, .8))
    cv.line([poly + [poly[0]]])


def _rings(cv, cx, cy, r0, r1, pitch=3., sq=1.):
    cv.obj([], 0)
    r = r0
    while r <= r1:
        n = max(24, int(r * .9))
        cv.hair([_ell(cx, cy, r, r * sq, n) + [_ell(cx, cy, r, r * sq, n)[0]]])
        r += pitch


def _star(cv, x, y, r, rot=-90.):
    """A faceted, cut star: ten facets, the lee side of each point cut black."""
    pts = []
    for i in range(10):
        a = math.radians(rot + 36 * i)
        rr = r if i % 2 == 0 else r * .43
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    cv.obj([pts], 1. if r > 3.5 else .5)
    for i in range(0, 10, 2):
        tri = [(x, y), pts[i], pts[(i + 1) % 10]]
        cv.line(C.hatch_poly(tri, 0, .8))
        cv.line([tri + [tri[0]]])


def _glyph_p(cv, x, y, hgt):
    """A small engraved 'P' (stem + bowl), hgt px tall, centred on x, y."""
    a = hgt / 2
    sx = x - a * .35
    stem = [(sx, y + a), (sx, y - a)]
    bowl = [(sx, y - a)] + [(sx + a * .35 + a * .42 * math.cos(t), y - a * .45 + a * .55 * math.sin(t))
                            for t in [-math.pi / 2 + math.pi * i / 10 for i in range(11)]] + [(sx, y + a * .1)]
    cv.line([stem, bowl])
    cv.hair([[(sx - a * .3, y + a), (sx + a * .3, y + a)]])


def _superell(cx, cy, a, b, e=2.4, n=48):
    return C._superellipse(cx, cy, a, b, e, n)


def headphones(cv, cx, cy, s, stars=True, plaque=True):
    """Over-ear headphones about s wide (and as tall), centred on cx, cy, lit from upper left."""
    hy = cy - .03 * s
    R, Ry, bt = .36 * s, .40 * s, .065 * s
    # padding under the headband, quilted
    pad_o = [(cx + R * math.cos(t), hy + Ry * math.sin(t)) for t in [math.pi + .35 + (math.pi - .7) * i / 40 for i in range(41)]]
    pad_i = [(cx + (R - .05 * s) * math.cos(t), hy + (Ry - .05 * s) * math.sin(t)) for t in [math.pi + .45 + (math.pi - .9) * i / 40 for i in range(41)]]
    pad = pad_o + pad_i[::-1]
    cv.obj([pad], 1.)
    k = 0
    for i in range(1, 40):
        t = math.pi + .4 + (math.pi - .8) * i / 40
        p0 = (cx + (R - .048 * s) * math.cos(t), hy + (Ry - .048 * s) * math.sin(t))
        p1 = (cx + R * math.cos(t), hy + Ry * math.sin(t))
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) > 1:
            cv.hair([p0, p1])
    cv.hair(C.hatch_poly(pad, 0, 1.5))
    # headband: outer shell, contour lines bunched toward its under edge, black under-shadow
    ts = [math.pi + math.pi * i / 60 for i in range(61)]
    outer = [(cx + (R + bt) * math.cos(t), hy + (Ry + bt) * math.sin(t)) for t in ts]
    inner = [(cx + R * math.cos(t), hy + Ry * math.sin(t)) for t in ts]
    cv.obj([outer + inner[::-1]], 1.)
    for f in (.12, .26, .42, .62):
        cv.hair([[(cx + (R + bt * f) * math.cos(t), hy + (Ry + bt * f) * math.sin(t)) for t in ts]])
    for f in (.0, .06):
        cv.line([[(cx + (R + bt * f + .4) * math.cos(t), hy + (Ry + bt * f + .4) * math.sin(t)) for t in ts]])
    # plaque with the monogram
    if plaque:
        py = hy - Ry - bt / 2
        pr = max(3.5, .07 * s)
        pl = _ell(cx, py, pr * 1.4, pr, 24)
        cv.obj([pl], 1.)
        cv.hair([_ell(cx, py, pr * 1.4 - 1.2, pr - 1.2, 24) + [_ell(cx, py, pr * 1.4 - 1.2, pr - 1.2, 24)[0]]])
        _glyph_p(cv, cx, py, pr * 1.15)
    cups = []
    for side in (-1, 1):
        bx = cx + side * (R + bt / 2)
        # yoke: slider rising out of the band end, a fork round the cup
        yk = [(bx - .022 * s, hy - .02 * s), (bx + .022 * s, hy - .02 * s), (bx + .022 * s, hy + .14 * s), (bx - .022 * s, hy + .14 * s)]
        cv.obj([yk], 1.)
        cv.hair(C.hatch_poly(yk, 90, 1.5))
        cv.line([[(bx + side * .022 * s - side * .8, hy - .02 * s), (bx + side * .022 * s - side * .8, hy + .14 * s)]])
        ccy = hy + .33 * s
        cups.append((bx, ccy))
    for side, (bx, ccy) in zip((-1, 1), cups):
        # cushion (leatherette, dark) on the inner side
        cu = _superell(bx - side * .055 * s, ccy, .075 * s, .205 * s, 2.6)
        cv.obj([cu], 1.)
        cv.hair(C.hatch_poly(cu, 0, 1.5))
        cv.hair(C.hatch_poly(cu, 90, 3., .5))
        for f in (.82,):
            cv.line([_superell(bx - side * .055 * s, ccy, .075 * s * f, .205 * s * f, 2.6) + [cu[0]][:0]])
        # shell: white on the lit side, hatched and cut black on the lee side
        sh = _superell(bx + side * .02 * s, ccy, .085 * s, .215 * s, 2.4)
        cv.obj([sh], 1.5)
        lx = bx + side * .02 * s
        for f, w in ((.78, 'h'), (.56, 'h'), (.34, 'h')):
            ring = _superell(lx - .015 * s * (1 - f), ccy - .02 * s * (1 - f), .085 * s * f, .215 * s * f, 2.4)
            cv.hair([ring + [ring[0]]])
        # lee (right/lower) side hatched
        lee = [p for p in C.hatch_poly(sh, 90, 1.5) if p[0][0] > lx + .015 * s]
        cv.hair(lee)
        sh2 = [p for p in C.hatch_poly(sh, 30, 2.) if (p[0][0] + p[1][0]) / 2 > lx + .035 * s]
        cv.hair(sh2)
        # black crescent along the lower right edge
        cr = [p for p in sh if p[0] > lx + .05 * s or p[1] > ccy + .17 * s]
        if len(cr) > 2:
            cv.heavy([cr])
        # hinge pin
        pin = _ell(bx, hy + .14 * s, max(1.5, .018 * s), max(1.5, .018 * s), 12)
        cv.obj([pin], 1.)
    if stars:
        r = .05 * s
        for i in range(5):
            a = math.radians(-150 + 30 * i)
            _star(cv, cx + .2 * s * math.cos(a), hy + .36 * s + .2 * s * math.sin(a), r)
    return (cx - .5 * s, hy - Ry - bt, cx + .5 * s, hy + .55 * s)


def amplifier(cv, x, y, w, h):
    """The headphone amp: brushed face, two VU meters, a big knurled volume knob, feet."""
    box = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([box], 1.5)
    cv.hair(C.hatch_poly(box, 0, 2.))
    top = [(x - 2, y - 3), (x + w + 2, y - 3), (x + w, y), (x, y)]
    cv.obj([top], 1.)
    cv.hair(C.hatch_poly(top, 0, 1.5))
    for fx in (x + w * .1, x + w * .9 - 6):
        ft = [(fx, y + h), (fx + 6, y + h), (fx + 5, y + h + 2.5), (fx + 1, y + h + 2.5)]
        cv.obj([ft], 1.)
        cv.line(C.hatch_poly(ft, 0, .8))
    # VU meters
    mh = h * .5
    mw = min(mh * 1.5, w * .2)
    for i in range(2):
        mx = x + w * .07 + i * (mw + 4)
        my = y + (h - mh) / 2
        fr = [(mx, my), (mx + mw, my), (mx + mw, my + mh), (mx, my + mh)]
        cv.obj([fr], 1.5)
        acx, acy = mx + mw / 2, my + mh * 1.05
        rr = mh * .75
        cv.hair([[(acx + rr * math.cos(t), acy + rr * math.sin(t)) for t in [math.radians(-140 + 100 * j / 20) for j in range(21)]]])
        for j in range(7):
            t = math.radians(-140 + 100 * j / 6)
            cv.hair([(acx + rr * math.cos(t), acy + rr * math.sin(t)), (acx + (rr + 2) * math.cos(t), acy + (rr + 2) * math.sin(t))])
        red = [(acx + (rr - .2) * math.cos(t), acy + (rr - .2) * math.sin(t)) for t in [math.radians(-65 + 25 * j / 6) for j in range(7)]]
        cv.line([red])
        t = math.radians(-112 + 30 * i)
        cv.line([(acx, acy - 1), (acx + rr * 1.05 * math.cos(t), acy + rr * 1.05 * math.sin(t))])
        sh = [(mx, my + mh * .78), (mx + mw, my + mh * .78), (mx + mw, my + mh), (mx, my + mh)]
        cv.hair(C.hatch_poly(sh, 0, 1.5))
    # headphone jack and small toggles
    jx = x + w * .07 + 2 * (mw + 4) + 6
    jr = max(2.5, h * .1)
    jk = _ell(jx, y + h * .5, jr, jr, 16)
    cv.obj([jk], 1.)
    _solid(cv, _ell(jx, y + h * .5, jr * .45, jr * .45, 10))
    # the big knob
    kr = h * .42
    kx, ky = x + w * .78, y + h * .52
    collar = _ell(kx, ky, kr + 2.5, kr + 2.5, 48)
    cv.obj([collar], 1.)
    for j in range(36):
        t = TAU * j / 36
        cv.hair([(kx + (kr + .5) * math.cos(t), ky + (kr + .5) * math.sin(t)), (kx + (kr + 2.5) * math.cos(t), ky + (kr + 2.5) * math.sin(t))])
    kn = _ell(kx, ky, kr, kr, 48)
    cv.obj([kn], 1.5)
    for j in range(48):
        t = TAU * j / 48
        cv.hair([(kx + kr * .78 * math.cos(t), ky + kr * .78 * math.sin(t)), (kx + kr * math.cos(t), ky + kr * math.sin(t))])
    face = _ell(kx, ky, kr * .72, kr * .72, 36)
    cv.obj([face], 1.)
    rr = kr * .72 - 1.5
    while rr > 1.5:
        cv.hair([_ell(kx, ky, rr, rr, 30) + [_ell(kx, ky, rr, rr, 30)[0]]])
        rr -= 3.
    lee = [(kx + kr * .72 * math.cos(t), ky + kr * .72 * math.sin(t)) for t in [math.radians(-20 + 130 * j / 20) for j in range(21)]]
    cv.heavy([lee])
    t = math.radians(-60)
    cv.heavy([(kx + kr * .2 * math.cos(t), ky + kr * .2 * math.sin(t)), (kx + kr * .66 * math.cos(t), ky + kr * .66 * math.sin(t))])


def speaker(cv, x, y, w, h, side):
    """A bookshelf speaker: grained cabinet, woofer with surround and dust cap, dome tweeter."""
    box = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([box], 1.5)
    # wood grain, wavy vertical bulino
    rng = random.Random(int(x * 13 + y))
    gx = x + 1.5
    while gx < x + w - 1:
        ph = rng.uniform(0, 6)
        amp = rng.uniform(.3, 1.)
        cv.hair([[(gx + amp * math.sin(ph + yy * .09) + .6 * math.sin(yy * .31 + ph), yy) for yy in [y + h * j / 40 for j in range(41)]]])
        gx += 2.
    # cabinet side in shadow
    lee = [(x + w, y), (x + w + w * .12, y - 2), (x + w + w * .12, y + h - 2), (x + w, y + h)] if side > 0 else \
          [(x, y), (x - w * .12, y - 2), (x - w * .12, y + h - 2), (x, y + h)]
    cv.obj([lee], 1.)
    cv.line(C.hatch_poly(lee, 0, .8 if side > 0 else 1.5))
    wr = w * .36
    wx, wy = x + w / 2, y + h * .66
    sur = _ell(wx, wy, wr, wr, 48)
    cv.obj([sur], 1.5)
    cv.hair(C.hatch_poly(sur, 45, 1.5))
    cone = _ell(wx, wy, wr * .8, wr * .8, 40)
    cv.obj([cone], 1.)
    for j in range(24):
        t = TAU * j / 24
        cv.hair([(wx + wr * .3 * math.cos(t), wy + wr * .3 * math.sin(t)), (wx + wr * .8 * math.cos(t), wy + wr * .8 * math.sin(t))])
    cap = _ell(wx, wy, wr * .3, wr * .3, 24)
    cv.obj([cap], 1.)
    cv.hair([_ell(wx + 1, wy + 1, wr * .18, wr * .18, 16) + [_ell(wx + 1, wy + 1, wr * .18, wr * .18, 16)[0]]])
    cv.line([[(wx + wr * .3 * math.cos(t), wy + wr * .3 * math.sin(t)) for t in [j / 10 * 1.6 for j in range(11)]]])
    tx, ty = x + w / 2, y + h * .2
    tr = w * .16
    ring = _ell(tx, ty, tr, tr, 32)
    cv.obj([ring], 1.)
    cv.hair(C.hatch_poly(ring, -45, 1.5))
    dome = _ell(tx, ty, tr * .55, tr * .55, 24)
    cv.obj([dome], 1.)
    cv.line([[(tx + tr * .55 * math.cos(t), ty + tr * .55 * math.sin(t)) for t in [-.3 + j / 10 * 2. for j in range(11)]]])


def shelf(cv, x, y, w, h):
    """A wood shelf: a lit top edge and a grained front with knots."""
    top = [(x, y), (x + w, y), (x + w, y + 3), (x, y + 3)]
    cv.obj([top], 1.)
    fr = [(x, y + 3), (x + w, y + 3), (x + w, y + h), (x, y + h)]
    cv.obj([fr], 1.)
    rng = random.Random(int(w * 7 + h))
    knots = [(x + w * rng.uniform(.15, .85), y + 3 + (h - 3) * rng.uniform(.35, .65)) for _ in range(2)]
    yy = y + 4.5
    while yy < y + h - .8:
        pts = []
        for j in range(81):
            xx = x + w * j / 80
            dy = .5 * math.sin(xx * .05 + yy)
            for kx, ky in knots:
                d = math.hypot((xx - kx) / 2.4, yy - ky)
                dy += 3.5 * (yy - ky) / (d * d + 6.) * 2.
            pts.append((xx, yy + dy))
        cv.hair([pts])
        yy += 1.5
    for kx, ky in knots:
        cv.line([_ell(kx, ky, 2.5, 1.2, 12) + [_ell(kx, ky, 2.5, 1.2, 12)[0]]])
    cv.line(C.hatch_poly([(x, y + h - 2.5), (x + w, y + h - 2.5), (x + w, y + h), (x, y + h)], 0, .8))


def _clip_d(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------------
# the vignettes
# ------------------------------------------------------------------------------------------------

def _vig_medallion(cx, cy, rx, ry):
    cv = C.Canvas()
    s = min(rx * 1.55, ry * 1.62)
    _rings(cv, cx, cy + s * .05, 2, max(rx, ry) + 4, 3.)
    headphones(cv, cx, cy + s * .01, s, stars=s > 50)
    return cv.svg()


def _vig_field(bx, by, bw, bh, tall):
    """Fill the whole cartouche field (box is its bounding box; the caller clips)."""
    cv = C.Canvas()
    cx = bx + bw / 2
    if tall:
        sh_h = max(14., bh * .07)
        sy = by + bh * .83
        sph = bh * .25
        spw = min(bw * .21, sph * .66)
        aw, ah = bw * .4, bh * .1
        s = min(bw * .7, bh * .5)
        hcy = sy - sph - 4 - .52 * s
        _rings(cv, cx, hcy, 2, max(bw, bh), 3.)
        cv.obj([], 0)
        cv.line(C.hatch_poly([(bx, sy + sh_h), (bx + bw, sy + sh_h), (bx + bw, by + bh), (bx, by + bh)], 0, 1.5))
        speaker(cv, bx + bw * .08 + (bw * .21 - spw) * .5, sy - sph, spw, sph, -1)
        speaker(cv, bx + bw * .92 - spw - (bw * .21 - spw) * .5, sy - sph, spw, sph, 1)
        amplifier(cv, cx - aw / 2, sy - ah - 3, aw, ah)
        shelf(cv, bx - 2, sy, bw + 4, sh_h)
        headphones(cv, cx, hcy, s)
    else:
        sh_h = max(9., bh * .1)
        sy = by + bh * .8
        ah = min(bh * .17, 22.)
        aw = bw * .62
        s = min(bw * .56, (sy - ah - by) * 1.02)
        hcy = by + (sy - ah - 4 - by) * .52
        _rings(cv, cx, hcy, 2, max(bw, bh), 3.)
        cv.obj([], 0)
        cv.line(C.hatch_poly([(bx, sy + sh_h), (bx + bw, sy + sh_h), (bx + bw, by + bh), (bx, by + bh)], 0, 1.5))
        amplifier(cv, cx - aw / 2, sy - ah - 2, aw, ah)
        shelf(cv, bx - 2, sy, bw + 4, sh_h)
        headphones(cv, cx, hcy, s)
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts (house layouts from engraving_codex, adapted so no field is left blank)
# ------------------------------------------------------------------------------------------------

def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.75, 134)
    o.append(C._clip(C._uid("b4", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _d(_ell(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(_clip_d(C._uid("bm4", w, h), field, _vig_medallion(cx, cy, rx - 2, ry - 2)))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _field(cart_svg, inner_d, cx, cy, cw, ch, tall, uid):
    # the field's bounding box from its outline
    nums = [float(v) for v in __import__("re").findall(r"-?\d+(?:\.\d+)?", inner_d)]
    return _clip_d(uid, inner_d, _vig_field(cx - cw / 2, cy - ch / 2, cw, ch, tall))


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
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m4", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(_clip_d(C._uid("mf4", w, h), inner_d, _vig_field(cx - a, cy - b, 2 * a, 2 * b, False)))
    bp = C._superellipse(cx, cy, a - 3.2, b - 3.2)
    o.append(f'<path d="{_d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _banner_stars(centre, hgt):
    cv = C.Canvas()
    n = len(centre) - 1
    for i in range(5):
        p = centre[int(n * (.3 + .1 * i))]
        _star(cv, p[0], p[1], hgt * .36)
    # light ruling across the face between the stars
    cv.obj([], 0)
    return cv.svg()


def _tablet(tx, ty, tw, th):
    """The pedestal tablet: a ruled measurement grid with a frequency-response curve (the review's
    'warm bass' hump), and at its end a beamed pair of swing eighths, Parker's jazz note."""
    cv = C.Canvas()
    x0, x1 = tx + 3, tx + tw - 3
    y0, y1 = ty + 3, ty + th - 2
    cv.obj([], 0)
    box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    cv.hair(C.hatch_poly(box, 0, 3.))
    gx = x0
    k = 0
    while gx < x1 - 26:
        cv.hair([(gx, y0), (gx, y1)])
        gx += 3. if k % 10 else 3.
        k += 1
    pts = []
    for j in range(161):
        u = j / 160
        xx = x0 + (x1 - 30 - x0) * u
        db = .55 * math.exp(-((u - .12) / .1) ** 2) - .25 * math.exp(-((u - .62) / .08) ** 2) \
            + .18 * math.sin(u * 31) * u ** 2 - .5 * max(0, u - .9) * 6
        pts.append((xx, (y0 + y1) / 2 - db * (y1 - y0) * .55))
    cv.heavy([pts])
    # swing eighths at the tablet's right end
    nx = x1 - 22
    mid = (y0 + y1) / 2
    hh = (y1 - y0)
    cv.obj([[(nx - 3, y0 - 1), (x1 + 1, y0 - 1), (x1 + 1, y1 + 1), (nx - 3, y1 + 1)]], 0)
    for i, dx in enumerate((0, 10)):
        hx, hyy = nx + dx, y1 - 2.2 - i * .8
        head = _ell(hx, hyy, 2.4, 1.6, 12)
        cv.obj([head], .5)
        cv.line(C.hatch_poly(head, 0, .8))
        cv.line([(hx + 2.2, hyy - .5), (hx + 2.2, y0 + 1)])
    for dy in (0, 1., 2.):
        cv.line([(nx + 2.2, y0 + 1 + dy), (nx + 12.2, y0 + 1 + dy)])
    return cv.svg()


def _tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .04, 18.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # light ruled ground above the panel so the crest rises out of engraved paper, not blank white
    o.append(C.dark_ground((0, 0, w, top_free), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .62
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t4", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_clip_d(C._uid("tf4", w, h), inner_d, _vig_field(cx - a, cy - b, 2 * a, 2 * b, True)))
    bp = C._superellipse(cx, cy, a - 3.2, b - 3.2)
    o.append(f'<path d="{_d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_stars(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx + 1.5, ty + 1.5, tw - 2, th - 2))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f4", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 4
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
