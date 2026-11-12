"""doodles-01 "Daylight / The light is leaving" plate.

Subject: dusk over Sauvie Island. The sun sinks into the Coast Range at the far end of the year's
dotted arc of daylight (the page's curve, June high point to "you are here"), shafts of light
fanning up through a ruled evening sky, a new moon (tonight) cross-hatched dark beside the
evening star, the Multnomah Channel catching a glitter path, a cottonwood bank, and a great blue
heron standing in the shallows (the Easter egg). The pedestal tablet carries the year's daylight
curve engraved with today's sun on it; the ribbon carries the moon's phases with the new moon at
its centre.
"""
import sys
import math
import random
import datetime
import re
import engraving_codex as C

_n, _d, PI, TAU = C._n, C._d, C.PI, C.TAU


def _doy(ctx):
    try:
        return datetime.date.fromisoformat((ctx or {}).get("date", "")[:10]).timetuple().tm_yday
    except Exception:
        return 316


def _daylen(doy):
    return 12.2 + 3.52 * math.sin(TAU * (doy - 80) / 365.)


def _inside(poly, px, py):
    c = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > py) != (by > py) and px < ax + (bx - ax) * (py - ay) / (by - ay):
            c = not c
    return c


def _circle(cx, cy, r, n=32, a0=0., a1=TAU):
    return C._ell_pts(cx, cy, r, r, n, a0, a1)


def _field(cx, cy, w, h):
    """bounding box of engraving_codex.cartouche's inner field"""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, cx + a, cy + b


# ----------------------------------------------------------------------------------------------
# the heron (Easter egg): silhouette standing in the shallows, facing right
# ----------------------------------------------------------------------------------------------

def _heron(cv, x, y, s, rng):
    """Feet at (x, y), about s tall."""
    def P(u, v):
        return (x + u * s, y + v * s)
    body = [P(-.30, -.50), P(-.22, -.60), P(-.05, -.66), P(.10, -.66), P(.17, -.62), P(.14, -.55),
            P(.02, -.48), P(-.12, -.45), P(-.26, -.44), P(-.38, -.40)]
    # neck: S-curve ribbon
    spine = []
    for i in range(13):
        t = i / 12
        u = .12 + .06 * math.sin(t * PI * 1.3) - .02 * t
        v = -.62 - .36 * t
        spine.append((u, v))
    lw = .028
    left = [P(u - lw, v) for u, v in spine]
    right = [P(u + lw * .8, v) for u, v in spine]
    neck = left + right[::-1]
    head = [P(.10, -.98), P(.14, -1.02), P(.19, -1.01), P(.40, -.985), P(.19, -.965), P(.13, -.955)]
    plume = [P(.11, -1.0), P(-.04, -.985), P(.10, -.99)]
    for poly in (body, neck, head, plume):
        cv.obj([poly], 1.)
        cv.line(C.hatch_poly(poly, 0, .8))
    cv.obj([], 0)
    cv.line([[P(-.02, -.47), P(-.03, -.04)], [P(.03, -.47), P(.06, -.2), P(.04, -.02)]])
    cv.hair([[P(-.03, -.04), P(-.10, 0)], [P(-.03, -.04), P(.04, 0)], [P(.04, -.02), P(.12, .01)]])
    # ripple rings at the feet
    for k in (1, 2):
        cv.hair(C._ell_pts(x, y + .01 * s, .09 * s * k, .018 * s * k, 24, PI * .05, PI * .95))


# ----------------------------------------------------------------------------------------------
# the dusk scene, fills (x, y, w, h); clipped by the caller
# ----------------------------------------------------------------------------------------------

def _scene(x, y, w, h, seed, rich=True):
    rng = random.Random(seed)
    cv = C.Canvas()
    hz = y + h * (.60 if rich else .62)
    sx = x + w * (.70 if rich else .5)
    sr = min(w, h) * (.13 if rich else .2)
    x1, y1 = x + w, y + h
    # sky: ruled, darkening upward (1.5 / 2 / 3 px pitch)
    sky = [(x - 1, y - 1), (x1 + 1, y - 1), (x1 + 1, hz + 2), (x - 1, hz + 2)]
    cv.obj([sky], 0)
    yy = y + .5
    lines = []
    while yy < hz + 2:
        t = (yy - y) / max(1., hz - y)
        lines.append([(x - 1, yy), (x1 + 1, yy)])
        yy += 1.5 if t < .3 else (2. if t < .62 else 3.)
    cv.hair(lines)
    # shafts of light: white wedges fanning from the sun
    nr = 15 if rich else 11
    R = math.hypot(w, h)
    for i in range(nr):
        a = PI + PI * (i + .5) / nr
        half = math.radians(1.6 if i % 2 else 2.4)
        r0 = sr * 1.35
        r1 = R * (1. if i % 2 == 0 else .55) * (1 if rich else .8)
        wedge = [(sx + r0 * math.cos(a), hz + r0 * math.sin(a)),
                 (sx + r1 * math.cos(a - half), hz + r1 * math.sin(a - half)),
                 (sx + r1 * math.cos(a + half), hz + r1 * math.sin(a + half))]
        cv.obj([wedge], .5)
        if i % 2 == 0:
            m = [(sx + (r0 + 2) * math.cos(a), hz + (r0 + 2) * math.sin(a)),
                 (sx + r1 * math.cos(a), hz + r1 * math.sin(a))]
            cv.hair([m])
    # glow ring and the sun
    cv.obj([_circle(sx, hz, sr * 1.25, 48)], .5)
    cv.hair([_circle(sx, hz, sr * 1.12, 48)])
    disc = _circle(sx, hz, sr, 48)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 2, .7))
    if rich:
        # the year's arc of daylight: dotted, June high, ending in the setting sun
        ax0, apk = x + w * .04, x + w * .36
        arc = []
        for i in range(61):
            t = i / 60
            px = ax0 + (sx - ax0) * t
            k = (px - ax0) / (sx - ax0)
            hh = math.sin(PI * min(1, k / (2 * (apk - ax0) / (sx - ax0))) if k < 2 * (apk - ax0) / (sx - ax0) else PI)
            py = hz - (hz - y) * .78 * math.sin(PI * k) ** .9
            arc.append((px, py))
        arc_svg = (f'<path d="{_d(arc, tol=.2)}" fill="none" stroke="#000" stroke-width="1.5" '
                   f'stroke-dasharray="0 5" stroke-linecap="round"/>')
        # little June sun at the top of the arc
        pk = min(arc, key=lambda p: p[1])
        cv.obj([_circle(pk[0], pk[1], 5.5, 20)], 1.)
        cv.hair(C.hatch_poly(_circle(pk[0], pk[1], 5.5, 20), 0, 2, .5))
        for i in range(12):
            a = TAU * i / 12
            cv.hair([[(pk[0] + 7.5 * math.cos(a), pk[1] + 7.5 * math.sin(a)),
                      (pk[0] + (11 if i % 2 else 9) * math.cos(a), pk[1] + (11 if i % 2 else 9) * math.sin(a))]])
        # new moon tonight: dark, cross-hatched, with an earthshine rim; evening star beside it
        mx, my, mr = x + w * .12, y + h * .14, min(w, h) * .055
        moon = _circle(mx, my, mr, 36)
        cv.obj([_circle(mx, my, mr + 2.5, 36)], .5)
        cv.obj([moon], 1.)
        cv.hair(C.hatch_poly(moon, 45, 1.5) + C.hatch_poly(moon, -45, 1.5))
        cv.hair([_circle(mx, my, mr * .82, 36, -PI * .45, PI * .45)])
    else:
        arc_svg = ""
    stars = [(x + w * .22, y + h * .07, 4.5), (x + w * .5, y + h * .05, 3), (x + w * .9, y + h * .1, 3.5),
             (x + w * .3, y + h * .26, 2.5)] if rich else [(x + w * .15, y + h * .2, 3), (x + w * .85, y + h * .16, 3)]
    for (ax, ay, r) in stars:
        st = []
        for i in range(8):
            a = PI / 4 * i - PI / 2
            rr = r if i % 2 == 0 else r * .3
            st.append((ax + rr * math.cos(a), ay + rr * math.sin(a)))
        cv.obj([st], .5)
    # distant Coast Range, sun sinking behind it
    pts = []
    n = 60
    for i in range(n + 1):
        t = i / n
        px = x - 1 + (w + 2) * t
        v = (.035 + .025 * math.sin(t * 9 + seed % 7) + .018 * math.sin(t * 23 + 1) + .01 * math.sin(t * 51))
        v *= h * (1 if rich else .7)
        # a saddle where the sun sets
        v *= .55 + .45 * min(1, abs(px - sx) / (sr * 2.2))
        pts.append((px, hz - v))
    hills = pts + [(x1 + 1, hz + 3), (x - 1, hz + 3)]
    cv.obj([hills], 1.)
    cv.hair(C.hatch_poly(hills, 0, 1.5, .25))
    # ridge highlights: a second range nearer, darker
    pts2 = []
    for i in range(n + 1):
        t = i / n
        px = x - 1 + (w + 2) * t
        v = (.012 + .012 * math.sin(t * 13 + 2) + .006 * math.sin(t * 37)) * h
        pts2.append((px, hz + 2 - v))
    near = pts2 + [(x1 + 1, hz + 5), (x - 1, hz + 5)]
    cv.obj([near], 1.)
    cv.hair(C.hatch_poly(near, 0, 1.5, .5) + C.hatch_poly(near, 60, 2))
    # the channel: broken water lines, a glitter path under the sun
    wy0 = hz + 4
    water = [(x - 1, wy0), (x1 + 1, wy0), (x1 + 1, y1 + 1), (x - 1, y1 + 1)]
    cv.obj([water], 0)
    wl = []
    yy = wy0 + 1.5
    while yy < y1 + 1:
        t = (yy - wy0) / max(1., y1 - wy0)
        col = sr * (.9 + 2.2 * t)
        px = x - 1
        while px < x1 + 1:
            near_col = abs(px - sx) < col
            seg = rng.uniform(2, 5) if near_col else rng.uniform(14, 60)
            gap = rng.uniform(2.5, 4.5) if near_col else rng.uniform(1.5, 3.5)
            if near_col and rng.random() < .25:
                gap += 3
            wl.append([(px, yy), (min(px + seg, x1 + 1), yy)])
            px += seg + gap
        yy += 2. if t < .5 else 1.5
    cv.hair(wl)
    if rich:
        # Sauvie Island bank: cottonwoods on the left, low grass bank right
        bx1 = x + w * .34
        tops = []
        k = 9
        prev = None
        for i in range(k + 1):
            t = i / k
            px = x - 1 + (bx1 - x + 1) * t
            crown = (.24 - .15 * t ** 1.4) * h + 4 * math.sin(i * 2.1)
            cur = (px, hz + 6 - crown)
            if prev:
                (ax, ay), (bx, by) = prev, cur
                bulge = (bx - ax) * .42
                for j in range(1, 11):
                    u = j / 10
                    tops.append((ax + (bx - ax) * u, ay + (by - ay) * u - bulge * math.sin(PI * u)))
            else:
                tops.append(cur)
            prev = cur
        tops.append((bx1 + 8, hz + h * .06))
        bank = tops + [(bx1 + 30, hz + h * .14), (x + w * .4, y + h * .86), (x - 1, y + h * .9)]
        cv.obj([bank], 1.)
        cv.hair(C.hatch_poly(bank, 0, 1.5) + C.hatch_poly(bank, 70, 2))
        # crown texture: little leaf-tufts in the treeline
        tufts = []
        for i in range(70):
            tx = x + rng.uniform(0, bx1 - x - 6)
            ty = hz + rng.uniform(-.17, .05) * h
            if not _inside(bank, tx, ty - 2):
                continue
            tufts.append(C._ell_pts(tx, ty, 3, 1.6, 8, PI, TAU))
        cv.line(tufts)
        # foreground shore at the bottom
        shore = [(x - 1, y + h * .9)]
        for i in range(21):
            t = i / 20
            shore.append((x - 1 + (w + 2) * t, y + h * (.93 + .025 * math.sin(t * 11 + 1)) + (6 if t > .5 else 0) * (t - .5)))
        shore += [(x1 + 1, y1 + 1), (x - 1, y1 + 1)]
        cv.obj([shore], 1.)
        cv.hair(C.hatch_poly(shore, -20, 1.5) + C.hatch_poly(shore, 30, 2))
        # reeds
        reeds = []
        for i in range(16):
            rx = x + w * (.36 + .06 * (i % 8)) + rng.uniform(-4, 4) + (w * .35 if i >= 8 else 0)
            if rx > x1 - 4:
                continue
            base = y + h * .94
            ln = rng.uniform(.05, .10) * h
            bend = rng.uniform(-6, 6)
            reeds.append([(rx, base), (rx + bend * .3, base - ln * .5), (rx + bend, base - ln)])
        cv.line(reeds)
        _heron(cv, x + w * .53, y + h * .80, h * .25, rng)
    else:
        _heron(cv, x + w * .3, y + h * .86, h * .34, rng)
    return arc_svg, cv.svg()


def _vignette(x, y, w, h, clip_d, seed, rich=True):
    arc, body = _scene(x, y, w, h, seed, rich)
    cid = C._uid("dl", x, y, w, h, seed)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}{arc}</g>')


# ----------------------------------------------------------------------------------------------
# pedestal tablet: the year's daylight curve; banner: the moon's phases
# ----------------------------------------------------------------------------------------------

def _tablet(tx, ty, tw, th, doy):
    o = []
    ix, iy, iw, ih = tx + 3, ty + 3, tw - 5, th - 5
    o.append(f'<path d="M{_n(ix)},{_n(iy)}h{_n(iw)}v{_n(ih)}h{_n(-iw)}z" fill="{C.pat("L")}" stroke="none"/>')
    base = iy + ih - 1
    top = iy + 2
    lo, hi = 8.68, 15.72
    pts = []
    for i in range(73):
        d = 1 + 364 * i / 72
        v = (_daylen(d) - lo) / (hi - lo)
        pts.append((ix + iw * i / 72, base - (base - top) * (.15 + .85 * v)))
    area = pts + [(ix + iw, base), (ix, base)]
    o.append(f'<path d="{_d(area, True, .2)}" fill="{C.pat("X")}" stroke="none"/>')
    o.append(f'<path d="{_d(pts, tol=.2)}" stroke="#000" stroke-width="1.5"/>')
    ticks = "".join(f"M{_n(ix + iw * (m + .5) / 12)},{_n(base)}v-2" for m in range(12))
    o.append(f'<path d="{ticks}" stroke="#000" stroke-width=".5"/>')
    px = ix + iw * (doy - 1) / 364
    v = (_daylen(doy) - lo) / (hi - lo)
    py = base - (base - top) * (.15 + .85 * v)
    r = max(2.5, min(4.5, ih * .25))
    o.append(f'<path d="{_d(_circle(px, py, r + 1.5, 20), True, .1)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_d(_circle(px, py, r, 20), True, .1)}" fill="#000" stroke="none"/>')
    rays = "".join(f"M{_n(px + (r + 2) * math.cos(a))},{_n(py + (r + 2) * math.sin(a))}"
                   f"L{_n(px + (r + 4) * math.cos(a))},{_n(py + (r + 4) * math.sin(a))}"
                   for a in [TAU * i / 8 for i in range(8)])
    o.append(f'<path d="{rays}" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def _moon_phase(cx, cy, r, ph):
    """ph in [0,1): 0 new (dark), .5 full. Returns path d of the DARK part."""
    lit = (1 - math.cos(TAU * ph)) / 2          # 0..1
    k = 1 - 2 * lit                               # terminator x-scale
    waxing = ph < .5
    sgn = -1 if waxing else 1                      # dark side: left when waxing
    arc = [(cx + sgn * r * math.sin(t), cy - r * math.cos(t)) for t in [PI * i / 20 for i in range(21)]]
    term = [(cx - sgn * k * r * math.sin(t), cy - r * math.cos(t)) for t in [PI * i / 20 for i in range(20, -1, -1)]]
    return _d(arc + term, True, .1)


def _banner_moons(centre, bh):
    o, dark = [], []
    n = 9
    r = max(2.5, bh * .26)
    L = len(centre) - 1
    for i in range(n):
        j = int(round(L * (.12 + .76 * i / (n - 1))))
        cx, cy = centre[j]
        ph = ((i - n // 2) / (n - 1)) * .9 % 1.
        o.append(_d(_circle(cx, cy, r, 20), True, .1))
        if abs(ph) < 1e-6:
            dark.append(_d(_circle(cx, cy, r, 20), True, .1))
        else:
            dark.append(_moon_phase(cx, cy, r, ph))
    return (f'<path d="{"".join(o)}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{"".join(dark)}" fill="#000" stroke="none"/>')


# ----------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex so the vignette fills the whole cartouche field)
# ----------------------------------------------------------------------------------------------

def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    ell = C._ell_pts(cx, cy, rx - 3, ry - 3, 64)
    o.append(_vignette(cx - rx, cy - ry, 2 * rx, 2 * ry, _d(ell, True, 0), seed, rich=False))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 3, ry - 3, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _medium(w, h, seed, doy):
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
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bx0, by0, bx1, by1 = _field(cx, cy, cw, gh + 4)
    o.append(_vignette(bx0, by0, bx1 - bx0, by1 - by0, inner, seed, rich=gh > 120))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed, doy, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # light-ruled field round the panel and under the pedestal: no blank paper anywhere
    o.append(f'<path d="M0,{_n(top_free * .35)}h{_n(w)}V{_n(h)}H0z" fill="{C.pat("L")}" stroke="none"/>')
    o.append(C.bead_moulding(0, 2.5, w, 1.2))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .48, ph * .6
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
    bx0, by0, bx1, by1 = _field(cx, cy, cw, ch)
    o.append(_vignette(bx0, by0, bx1 - bx0, by1 - by0, inner, seed, rich=True))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_moons(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, doy))
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
    seed = sum(map(ord, ctx.get("date", ""))) + 11
    doy = _doy(ctx)
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed, doy)
    else:
        body = _tall(w, h, seed, doy)
    return C.svg_doc(w, h, body)
