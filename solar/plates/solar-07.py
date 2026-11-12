"""solar-07 "Spots on the sun": the sun itself, engraved as the day's HMI intensitygram.

A limb-darkened solar disc, granulated, carrying today's sunspot groups (count scaled from the
page's sunspot number), streamers of the corona and a flaring prominence loop at the limb, all on
a cut-away ground inside the house cartouche. The ribbon and the pedestal tablet carry the day's
numbers in engraved path lettering. Easter egg: one sunspot group is Parker's dog's paw print.
"""
import sys
import math
import random
import re
import engraving_codex as C
import engraving_morning as EM

_n, _d, TAU, PI = C._n, C._d, C.TAU, C.PI

# ------------------------------------------------------------------------------------------------
# lettering: the morning stroke font plus the letters it lacks
# ------------------------------------------------------------------------------------------------
_G = dict(EM._G)
_G["S"] = (4.8, [("s", [(4.4, 1.0), (3.2, .05), (1.4, .1), (.5, 1.3), (.9, 2.9), (2.4, 3.7), (4.0, 4.6), (4.4, 6.3),
                       (3.5, 7.8), (1.5, 7.95), (.3, 6.9)])])
_G["U"] = (5.6, [("s", [(.9, 0), (.9, 5.4), (1.5, 7.4), (2.8, 8), (4.1, 7.4), (4.7, 5.4), (4.7, 0)]),
                 ("l", [(0, 0), (1.8, 0)]), ("l", [(3.8, 0), (5.6, 0)])])
_G["B"] = (5.2, [("l", [(0, 0), (3.1, 0)]), ("l", [(0, 8), (3.3, 8)]), ("l", [(.9, 0), (.9, 8)]),
                 ("s", [(3.1, 0), (4.3, .7), (4.3, 3.0), (3.0, 3.9), (.9, 3.9)]),
                 ("s", [(.9, 3.9), (3.4, 3.9), (4.7, 5.0), (4.6, 7.2), (3.3, 8)])])
_G["Y"] = (5.4, [("l", [(.3, 0), (2.7, 4.2), (5.1, 0)]), ("l", [(2.7, 4.2), (2.7, 8)]), ("l", [(1.6, 8), (3.8, 8)]),
                 ("l", [(-.4, 0), (1.3, 0)]), ("l", [(4.1, 0), (5.8, 0)])])
_G["K"] = (5.4, [("l", [(.9, 0), (.9, 8)]), ("l", [(4.8, 0), (.9, 5)]), ("l", [(2.2, 3.5), (5, 8)]),
                 ("l", [(0, 0), (1.8, 0)]), ("l", [(0, 8), (1.8, 8)])])


def _glyph(ch):
    adv, strokes = _G.get(ch, _G[" "])
    return adv, [EM._spline(p, False, 4) if k == "s" else list(p)
                 for k, p in strokes]


def _text_width(s, h, track=1.3):
    return (sum(_G.get(c, _G[" "])[0] + track for c in s) - track) * h / 8


def _text_on(s, path_fn, x_mid, h, track=1.3):
    """Glyph polylines centred at x_mid; path_fn(x) -> baseline-centre y and slope (rad)."""
    k = h / 8
    wd = _text_width(s, h, track)
    cx = x_mid - wd / 2
    out = []
    for c in s:
        adv, polys = _glyph(c)
        gx = cx + adv * k / 2
        gy, a = path_fn(gx)
        ca, sa = math.cos(a), math.sin(a)
        for p in polys:
            q = []
            for px, py in p:
                lx, ly = (px - adv / 2) * k, (py - 4) * k
                q.append((gx + lx * ca - ly * sa, gy + lx * sa + ly * ca))
            out.append(q)
        cx += (adv + track) * k
    return out


def _stroke(polys, sw):
    d = "".join(_d(p, tol=.1) for p in polys if len(p) > 1)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{sw}"/>' if d else ""


# ------------------------------------------------------------------------------------------------
# the day's numbers
# ------------------------------------------------------------------------------------------------

def _data(ctx):
    s = (ctx or {}).get("sample", "") or ""

    def num(pat, dflt):
        m = re.search(pat, s, re.I)
        try:
            return int(m.group(1)) if m else dflt
        except ValueError:
            return dflt
    d = {"spots": num(r"(\d+)\s+sunspots", 93), "avg": num(r"average of\s+(\d+)", 62),
         "flux": num(r"flux\s+(\d+)", 132), "flares": num(r"(\d+)\s+[A-Z]-class", 15)}
    m = re.search(r"for\s+([A-Z][a-z]{2})[a-z]*\s+(\d+)", s)
    d["day"] = (m.group(1).upper() + " " + m.group(2)) if m else ""
    m = re.search(r"\d+\s+([A-Z])-class", s)
    d["cls"] = m.group(1) if m else "C"
    return d


# ------------------------------------------------------------------------------------------------
# the sun
# ------------------------------------------------------------------------------------------------

def _circ(cx, cy, r, n=None, a0=0., a1=TAU):
    n = n or max(16, int(r * .9))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + (0 if a1 - a0 >= TAU - 1e-9 else 1))]


def _spot(cv, black, cx, cy, R, sx, sy, size, rng, paw=False):
    """A sunspot at (sx, sy) on the disc: umbra black, penumbra white with radial filaments,
    foreshortened toward the limb."""
    dx, dy = sx - cx, sy - cy
    rho = min(.97, math.hypot(dx, dy) / R)
    mu = math.sqrt(1 - rho * rho)
    th = math.atan2(dy, dx)
    ct, st = math.cos(th), math.sin(th)

    def P(u, v):          # u radial, v tangential, before foreshortening
        u *= max(.3, mu)
        return (sx + u * ct - v * st, sy + u * st + v * ct)
    rp = size
    ru = size * (.42 if not paw else .5)
    wob = [1 + .12 * math.sin(3 * t + rng.random() * 6) for t in [TAU * i / 28 for i in range(28)]]
    pen = [P(rp * wob[i] * math.cos(TAU * i / 28), rp * wob[i] * math.sin(TAU * i / 28)) for i in range(28)]
    cv.obj([pen], .5 if size < 4 else 1.)
    nf = max(10, int(size * 5))
    for i in range(nf):
        a = TAU * (i + rng.random() * .5) / nf
        r0 = ru * .9
        r1 = rp * wob[int(a / TAU * 28) % 28] * (.8 + .18 * rng.random())
        cv.hair([P(r0 * math.cos(a), r0 * math.sin(a)), P(r1 * math.cos(a), r1 * math.sin(a))])
    um = [P(ru * (1 + .1 * math.sin(2 * TAU * i / 18 + 1)) * math.cos(TAU * i / 18),
            ru * (1 + .1 * math.sin(2 * TAU * i / 18 + 1)) * math.sin(TAU * i / 18)) for i in range(18)]
    black.append(um)


def _sun(cx, cy, R, seed, data, corona=True, detail=1.):
    """Returns (svg) for the disc with spots, granulation, corona and a prominence."""
    rng = random.Random(seed)
    cv = C.Canvas()
    black = []
    # corona: a glory of fine rays fading into the cut-away ground, long and short in turn,
    # with a few broad helmet streamers carried out further
    if corona:
        ns = 6
        for i in range(ns):
            a = TAU * (i + .5 + (rng.random() - .5) * .4) / ns + .3
            L = R * (1.55 + .35 * rng.random())
            hw = .2 + .06 * rng.random()
            pl_, pr_ = [], []
            for j in range(17):
                t = j / 16
                rr = R + (L - R) * t
                wdt = hw * (1 - t) ** 1.6 * (.75 + .5 * math.sin(PI * min(1, t * 1.6)))
                pl_.append((cx + rr * math.cos(a - wdt), cy + rr * math.sin(a - wdt)))
                pr_.append((cx + rr * math.cos(a + wdt), cy + rr * math.sin(a + wdt)))
            cv.obj([pl_ + pr_[::-1]], 0)
            for s_ in (-.8, -.6, -.4, -.2, 0., .2, .4, .6, .8):
                q = []
                for j in range(17):
                    t = j / 16 * (1 - abs(s_) * .5)
                    rr = R + (L - R) * t
                    wdt = hw * (1 - t) ** 1.6 * (.75 + .5 * math.sin(PI * min(1, t * 1.6)))
                    q.append((cx + rr * math.cos(a + s_ * wdt), cy + rr * math.sin(a + s_ * wdt)))
                cv.hair(q)
        nr = int(R * 4.2)
        tips = []
        for i in range(nr):
            m = i % 4
            tips.append(R * (1.3 if m == 0 else (1.19 if m == 2 else 1.1 + .04 * rng.random())))
        glow = []
        for i in range(nr):
            a = TAU * i / nr
            glow.append((cx + (tips[i] + .6) * math.cos(a), cy + (tips[i] + .6) * math.sin(a)))
            a2 = TAU * (i + .5) / nr
            r2 = min(tips[i], tips[(i + 1) % nr]) * .985
            glow.append((cx + r2 * math.cos(a2), cy + r2 * math.sin(a2)))
        cv.obj([glow], 0)
        for i in range(nr):
            a = TAU * i / nr
            cv.hair([(cx + R * math.cos(a), cy + R * math.sin(a)),
                     (cx + tips[i] * math.cos(a), cy + tips[i] * math.sin(a))])
        black_bg = []
    else:
        black_bg = []
    # prominence loops (the day's flares) at the limb, upper right
    pa = -PI * .27 + (rng.random() - .5) * .3
    for k, (span, hgt) in enumerate(((.16, .34), (.11, .24), (.07, .15))):
        outer, inner = [], []
        for j in range(25):
            t = j / 24
            aa = pa + (t - .5) * 2 * span
            hh = math.sin(PI * t) ** .8
            ro = R * (1 + hgt * hh) + 1
            ri = R * (1 + (hgt - .05) * hh) - 1
            outer.append((cx + ro * math.cos(aa), cy + ro * math.sin(aa)))
            inner.append((cx + ri * math.cos(aa), cy + ri * math.sin(aa)))
        loop = outer + inner[::-1]
        cv.obj([loop], 1.)
        cv.hair([[(o[0] * .5 + i[0] * .5, o[1] * .5 + i[1] * .5) for o, i in zip(outer[2:-2], inner[2:-2])]])
        # shadow on the inside of the loop
        cv.line([[(o[0] * .25 + i[0] * .75, o[1] * .25 + i[1] * .75) for o, i in zip(outer[3:-3], inner[3:-3])]])
    # the disc
    disc = _circ(cx, cy, R, max(48, int(R * 1.4)))
    cv.obj([disc], 1.5)
    # limb darkening: rings tightening toward the edge, then a broken inner set
    d = 1.5
    k = 0
    while d < R * .42:
        ring = _circ(cx, cy, R - d, max(40, int(R * 1.3)))
        if k < 3:
            cv.line(ring + [ring[0]])
        else:
            # broken rings: granulated feel, gaps grow inward
            n = len(ring)
            gap = .12 + .5 * (d / (R * .42))
            seg = []
            for i in range(n + 1):
                p = ring[i % n]
                if (math.sin(i * .9 + k * 1.7) + 1) / 2 > gap:
                    seg.append(p)
                else:
                    if len(seg) > 1:
                        cv.hair(seg)
                    seg = []
            if len(seg) > 1:
                cv.hair(seg)
        k += 1
        d += 1.5 if k < 4 else (2 if k < 7 else 3 + (k - 7) * .9)
    # granulation: stipple dots, denser toward the limb, and a scatter of tiny open cells
    ng = int(R * R * .09 * detail)
    for i in range(ng):
        rr = R * .93 * math.sqrt(rng.random()) ** .7
        a = rng.random() * TAU
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        if rng.random() < .93:
            cv.hair([(x, y), (x + .45, y + .15)])
        else:
            c0 = rng.random() * TAU
            cv.hair(_circ(x, y, .9 + .5 * rng.random(), 6, c0, c0 + 4))
    # sunspot groups in the two activity belts
    ngroups = max(2, min(7, round(data["spots"] / 16)))
    s0 = max(2.4, R * .06)
    placed = []

    def free(x, y, r):
        return all(math.hypot(x - px, y - py) > r + pr + 2 for px, py, pr in placed)

    # Easter egg first: a paw print (pad + four toes), lower left of centre
    if R > 34:
        px, py = cx - R * .2, cy + R * .3
        ps = s0 * 1.25
        _spot(cv, black, cx, cy, R, px, py + ps * .3, ps * 1.35, rng, paw=True)
        placed.append((px, py + ps * .3, ps * 1.4))
        for j, (ox, oy) in enumerate(((-1.55, -1.25), (-.55, -2.15), (.55, -2.15), (1.55, -1.25))):
            tx, ty = px + ox * ps, py + oy * ps
            _spot(cv, black, cx, cy, R, tx, ty, ps * .62, rng)
            placed.append((tx, ty, ps * .65))
    g = 0
    tries = 0
    while g < ngroups and tries < 200:
        tries += 1
        lat = (rng.choice((-1, 1))) * (.12 + .26 * rng.random())
        lon = (rng.random() - .5) * 1.6
        x = cx + R * math.sin(lon) * math.cos(lat * PI / 2) * .95
        y = cy + R * math.sin(lat * PI / 2 * 1.4)
        if math.hypot(x - cx, y - cy) > R * .86:
            continue
        lead = s0 * (1.1 + 1.2 * rng.random())
        if not free(x, y, lead * 3.2):
            continue
        n = 2 + int(rng.random() * 4)
        tilt = -.15 * (1 if lat < 0 else -1)
        trail = []
        for j in range(n):
            sx = x - j * lead * 1.5 * math.cos(tilt) + (rng.random() - .5) * lead
            sy = y - j * lead * 1.5 * math.sin(tilt) + (rng.random() - .5) * lead * .8
            sz = lead if j == 0 else lead * (.35 + .45 * rng.random())
            if j == n - 1 and n > 2:
                sz = lead * .8
            trail.append((sx, sy, sz))
        for sx, sy, sz in trail:
            if math.hypot(sx - cx, sy - cy) < R * .9:
                _spot(cv, black, cx, cy, R, sx, sy, sz, rng)
        for sx, sy, sz in trail:
            placed.append((sx, sy, sz))
        # pores: tiny umbra dots around the group
        for j in range(3 + n):
            qx = x + (rng.random() - .7) * lead * 6
            qy = y + (rng.random() - .5) * lead * 2.5
            if math.hypot(qx - cx, qy - cy) < R * .9 and free(qx, qy, .5):
                black.append(_circ(qx, qy, .55 + .4 * rng.random(), 6))
        g += 1
    out = ""
    if black_bg:
        out += f'<path d="{"".join(_d(p, tol=0) for p in black_bg)}" stroke="#000" stroke-width=".5"/>'
    out += cv.svg()
    if black:
        out += f'<path d="{"".join(_d(p, True, .05) for p in black)}" fill="#000" stroke="none"/>'
    return out


def _vignette(bx, by, bw, bh, clip_d, cid, seed, data, cy_frac=.5, ground="G", rscale=.43):
    cx, cy = bx + bw / 2, by + bh * cy_frac
    R = min(bw * rscale, bh * max(rscale, .44))
    body = (f'<path d="M{_n(bx - 2)},{_n(by - 2)}h{_n(bw + 4)}v{_n(bh + 4)}h{_n(-bw - 4)}z" fill="{C.pat(ground)}"/>'
            + _sun(cx, cy, R, seed, data, corona=R > 24, detail=1.))
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _sol(cx, cy, r, seed, rays=True):
    """A carved sun mask: a face in a ringed disc, its mane a fan of shaded acanthus fingers that
    grow out of the scrollwork. Returns svg."""
    rng = random.Random(seed)
    cv = C.Canvas()
    if rays:
        n = 11
        for i in range(n):
            t = i / (n - 1)
            ang = 165 + 210 * t                       # upper fan, degrees
            L = r * (1.55 + (.35 if i % 2 == 0 else 0) + .25 * math.sin(PI * t))
            sx, sy = cx + r * .8 * math.cos(math.radians(ang)), cy + r * .8 * math.sin(math.radians(ang))
            bend = (.9 if t < .5 else -.9) * (.6 + .4 * abs(t - .5) * 2)
            C.acanthus_finger(sx, sy, ang, L, width=r * (.42 if i % 2 == 0 else .32), bend=bend,
                              curl=3.5 + rng.random(), cv=cv)
        # lower flames, short and swept down, like a beard
        for i, ang in enumerate((25, 55, 90, 125, 155)):
            sx, sy = cx + r * .8 * math.cos(math.radians(ang)), cy + r * .8 * math.sin(math.radians(ang))
            C.acanthus_finger(sx, sy, ang, r * (.95 if ang == 90 else .8), width=r * .32,
                              bend=(-.8 if ang < 90 else .8), curl=3.5, cv=cv)
    # the disc: outer bead ring, sunk black fillet, the face
    ring = _circ(cx, cy, r, 64)
    cv.obj([ring], 1.)
    cv.hair(_circ(cx, cy, r * .92, 64) + [_circ(cx, cy, r * .92, 64)[0]])
    face = _circ(cx, cy, r * .8, 64)
    cv.obj([face], 1.)
    k = r * .8

    def U(pts):
        return [(cx + x * k, cy + y * k) for x, y in pts]

    def bez(p0, p1, p2, p3, n=12):
        return [((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0],
                 (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1])
                for t in [j / n for j in range(n + 1)]]
    # cheek / jaw hatching on the shadow side
    for yy in [i * 1.5 / k for i in range(-int(k * .8 / 1.5), int(k * .8 / 1.5) + 1)]:
        xo = math.sqrt(max(0, .94 - yy * yy))
        x0 = xo * (.55 + .2 * (yy * yy))
        if xo - x0 > .04:
            cv.hair(U([(x0, yy), (xo, yy)]))
    # brows
    for sg in (-1, 1):
        cv.line(U([(sg * x, y) for x, y in bez((.1, -.3), (.2, -.48), (.45, -.5), (.62, -.33))]))
        # eye: lids and a black pupil
        cv.line(U([(sg * x, y) for x, y in bez((.14, -.17), (.24, -.3), (.42, -.3), (.52, -.17))]))
        cv.hair(U([(sg * x, y) for x, y in bez((.14, -.17), (.26, -.08), (.42, -.08), (.52, -.17))]))
        cv.heavy(U([(sg * .33, -.2), (sg * .33, -.15)]))
        # cheek apple
        cv.hair(U([(sg * x, y) for x, y in bez((.48, .05), (.56, .2), (.5, .32), (.4, .38))]))
    # nose
    cv.line(U(bez((.06, -.22), (.04, -.05), (.14, .08), (.1, .14))))
    cv.hair(U(bez((-.14, .12), (-.08, .2), (.08, .2), (.14, .12))))
    cv.hair(U(bez((-.06, -.2), (-.08, -.05), (-.1, .04), (-.12, .1))))
    # mouth and smile
    cv.line(U(bez((-.32, .38), (-.12, .5), (.12, .5), (.32, .38))))
    cv.hair(U(bez((-.22, .45), (-.08, .58), (.08, .58), (.22, .45))))
    cv.hair(U(bez((-.12, .66), (-.04, .7), (.04, .7), (.12, .66))))
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts (house layouts copied and made bespoke)
# ------------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, data):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    ell = C._ell_pts(cx, cy, rx - 2, ry - 2, 64)
    o.append(_vignette(cx - rx, cy - ry, 2 * rx, 2 * ry, _d(ell, True), C._uid("bv", w, h, seed), seed, data,
                       .5, "G", .4))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, data, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .4, gh * 1.45)
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
                   max_n=int(11 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fb = _field_box(cx, cy, cw, gh + 4)
    o.append(_vignette(*fb, field, C._uid("mv", w, h, seed), seed, data, .5, "G", .38))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _field_box(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return (cx - a, cy - b, 2 * a, 2 * b)


def _layout_tall(w, h, seed, data, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(9 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fb = _field_box(cx, cy, cw, ch)
    o.append(_vignette(*fb, field, C._uid("tv", w, h, seed), seed, data, .47, "G", .37))
    rng.randrange(1 << 20)
    sr = min(ch * .1 + top_free * .3, 31)
    o.append(_sol(cx, cy - ch / 2 - sr * .15, sr, seed))
    bh = min(16, ph * .05)
    by = cy + ch * .47
    bsvg, centre = C.ribbon_banner(cx, by, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # letter the ribbon along its arch
    xs = [p[0] for p in centre]

    def along(x):
        i = max(0, min(len(centre) - 2, int((x - xs[0]) / (xs[-1] - xs[0]) * (len(centre) - 1))))
        (x0, y0), (x1, y1) = centre[i], centre[i + 1]
        t = (x - x0) / (x1 - x0) if x1 != x0 else 0
        return y0 + (y1 - y0) * t, math.atan2(y1 - y0, x1 - x0)
    words = "SPOTS ON THE SUN" + (" · " + data["day"] if data["day"] else "")
    lh = bh * .5
    while _text_width(words, lh) > (xs[-1] - xs[0]) * .9 and lh > 4:
        lh -= .5
    o.append(_stroke(_text_on(words, along, cx, lh), 1))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: today's numbers
    tline = f"SUNSPOT NUMBER {data['spots']} · AVG {data['avg']} · FLUX {data['flux']}"
    lh = min(th * .55, 10)
    while _text_width(tline, lh) > tw * .92 and lh > 4:
        lh -= .5
    o.append(_stroke(_text_on(tline, lambda x: (ty + th / 2 + .5, 0.), tx + tw / 2, lh), 1))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * (ctx.get("sheet", 0) or 0)
    data = _data(ctx)
    if h < 110:
        body = _layout_band(w, h, seed, data)
    elif h <= 260:
        body = _layout_medium(w, h, seed, data)
    else:
        body = _layout_tall(w, h, seed, data)
    # nothing stays paper-white outside the relief: a light ruled ground under everything
    under = f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("L")}"/>'
    return C.svg_doc(w, h, under + body)
