"""Moon watch (nearby-02): a moonlit night over the Columbia, engraved in the house Codex style.
The moon is drawn at today's phase (from ctx["date"]); Mt. Hood stands on the horizon, the river
carries the moon's broken reflection, and on the Sauvie Island bank Parker's dog sits howling at
the moon beside a heron (the Easter eggs). Taller plates add the coming phases (First Quarter,
Full, Last Quarter, New) engraved on the pedestal tablet."""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
TAU = 2 * math.pi
SYN = 29.530588853


# ------------------------------------------------------------------------------------------------
# moon phase
# ------------------------------------------------------------------------------------------------

def _age(date):
    try:
        d = datetime.datetime.strptime((date or "")[:10], "%Y-%m-%d") + datetime.timedelta(hours=20)
    except ValueError:
        d = datetime.datetime(2026, 11, 11, 20)
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    return ((d - ref).total_seconds() / 86400.) % SYN


def _phase_polys(cx, cy, r, age, n=40, min_lit=.0):
    """(lit, dark) polygons of a moon disc at `age` days. Waxing lit on the right."""
    p = TAU * age / SYN
    k = (1 - math.cos(p)) / 2
    if min_lit and k < min_lit:
        p = math.acos(1 - 2 * min_lit) * (1 if p < math.pi else -1) % TAU
    waxing = p < math.pi
    c = math.cos(p)
    sx = 1 if waxing else -1
    ts = [-math.pi / 2 + math.pi * i / n for i in range(n + 1)]
    limb_lit = [(cx + sx * r * math.cos(t), cy + r * math.sin(t)) for t in ts]
    term = [(cx + sx * r * c * math.cos(t), cy + r * math.sin(t)) for t in ts[::-1]]
    limb_dark = [(cx - sx * r * math.cos(t), cy + r * math.sin(t)) for t in ts]
    lit = limb_lit + term
    dark = term[::-1] + limb_dark[::-1]
    return lit, dark, sx, c


def _clip_lines(lines, fn):
    """Keep only the parts of 2-point lines whose sample points satisfy fn(x, y)."""
    out = []
    for (x0, y0), (x1, y1) in lines:
        L = math.hypot(x1 - x0, y1 - y0)
        m = max(2, int(L / .8))
        run = []
        for i in range(m + 1):
            t = i / m
            q = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if fn(*q):
                run.append(q)
            else:
                if len(run) > 1:
                    out.append([run[0], run[-1]])
                run = []
        if len(run) > 1:
            out.append([run[0], run[-1]])
    return out


def _star(x, y, s):
    return [(x, y - s), (x + s * .28, y - s * .28), (x + s, y), (x + s * .28, y + s * .28),
            (x, y + s), (x - s * .28, y + s * .28), (x - s, y), (x - s * .28, y - s * .28)]


# ------------------------------------------------------------------------------------------------
# figures (black silhouettes cut into the bank)
# ------------------------------------------------------------------------------------------------

def _dog(x, y, s, face=1):
    """A sitting dog, muzzle raised to the moon. (x, y) = front paws on the ground, s = height."""
    Q = [(78, 4), (74, 12), (68, 20), (62, 28), (60, 40), (62, 52), (62, 70), (63, 92), (68, 96), (68, 100),
         (54, 100), (54, 80), (52, 72), (46, 78), (44, 90), (46, 96), (48, 100), (12, 100), (2, 99), (0, 96),
         (8, 94), (12, 88), (13, 76), (18, 64), (26, 52), (36, 38), (44, 28), (46, 22), (40, 17), (44, 13),
         (50, 12), (58, 10), (64, 8), (72, 2)]
    P = [((qx - 60) / 100, (qy - 100) / 100) for qx, qy in Q]
    return [(x + face * px * s, y + py * s) for px, py in P]


def _heron(x, y, s, face=-1):
    """A great blue heron standing in the shallows, neck folded. (x, y) = feet."""
    body = [(0, -.48), (.16, -.56), (.30, -.60), (.36, -.66), (.32, -.76), (.30, -.86), (.36, -.94),
            (.44, -.97), (.62, -.92), (.46, -.90), (.40, -.86), (.42, -.76), (.46, -.64), (.42, -.52),
            (.30, -.42), (.12, -.38), (-.10, -.36), (-.30, -.28), (-.12, -.40)]
    legs = [[(.10, -.39), (.08, 0)], [(.16, -.39), (.22, 0)]]
    f = lambda q: (x + face * q[0] * s, y + q[1] * s)
    return [f(q) for q in body], [[f(q) for q in L] for L in legs]


def _trees(x0, x1, ybase, hmax, rng):
    """A ragged cottonwood line along the bank, as one silhouette top edge."""
    pts = []
    x = x0
    while x < x1:
        w = rng.uniform(5, 11) * hmax / 14
        hh = hmax * rng.uniform(.45, 1.)
        for i in range(7):
            t = i / 6
            pts.append((x + w * t, ybase - hh * math.sin(math.pi * t) ** .6 - rng.uniform(0, hmax * .08)))
        x += w * .8
    return pts


# ------------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------------

def _scene(x, y, w, h, ctx, clip_d, cid, compact=False):
    """Night over the Columbia, filling the box x, y, w, h (clipped to clip_d). No white left:
    sky ruled and cross-hatched, stars and the moon knocked out of it, water ruled."""
    date = (ctx or {}).get("date", "")
    rng = random.Random(date + "moon")
    age = _age(date)
    cv = C.Canvas()
    box = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    hor = y + h * (.66 if compact else .64)
    # moon
    r = min(h * (.24 if compact else .2), w * .14)
    mx, my = x + w * (.70 if compact else .68), y + h * (.30 if compact else .27)
    if compact:
        r = min(h * .25, w * .11)
        my = y + h * .36
    halo = r * 1.75
    # sky: horizontal rules; cross rules thicken toward the zenith, thinning in the halo
    cv.obj([box], 0)
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, hor + 1), (x - 2, hor + 1)]
    cv.hair(C.hatch_poly(sky, 0, 2 if not compact else 1.5, .5))
    up = y + (hor - y) * .55
    cross = C.hatch_poly(sky, 70, 2, .3)
    cv.hair(_clip_lines(cross, lambda px, py: py < up + 6 * math.sin(px * .07) and math.hypot(px - mx, py - my) > halo * 1.25))
    cross2 = C.hatch_poly(sky, -70, 3, .3)
    cv.hair(_clip_lines(cross2, lambda px, py: py < y + (hor - y) * .28 and math.hypot(px - mx, py - my) > halo * 1.5))
    # stars (white knocked out of the ruling)
    stars = []
    n = int(w * (hor - y) / (170 if not compact else 120))
    for _ in range(n * 3):
        if len(stars) >= n:
            break
        sx_, sy_ = rng.uniform(x + 3, x + w - 3), rng.uniform(y + 3, hor - 8)
        if math.hypot(sx_ - mx, sy_ - my) < halo + 4:
            continue
        if any(math.hypot(sx_ - a, sy_ - b) < 9 for a, b, _ in stars):
            continue
        s = rng.choice((1.4, 1.6, 2., 2.2, 2.8, 3.4)) if not compact else rng.choice((1.3, 1.6, 2., 2.6))
        stars.append((sx_, sy_, s))
    # the Pleiades, high in the November evening east
    px_, py_ = x + w * .2, y + (hor - y) * .25
    if all(math.hypot(px_ - mx, py_ - my) > halo + 10 for _ in (0,)):
        for dx, dy in ((0, 0), (4, -1.5), (6.5, 1.5), (3, 3.5), (8.5, -.5), (1.5, -3.6)):
            stars.append((px_ + dx * (.8 if compact else 1.2), py_ + dy * (.8 if compact else 1.2), 1.2))
    for sx_, sy_, s in stars:
        cv.obj([_star(sx_, sy_, s)], 0)
        if s > 2.5:
            cv.obj([[(sx_ - .5, sy_ - s * 1.9), (sx_ + .5, sy_ - s * 1.9), (sx_ + .5, sy_ + s * 1.9), (sx_ - .5, sy_ + s * 1.9)]], 0)
    # halo: rings of light round the moon (concentric hairlines open the ruling)
    for k_ in (1.18, 1.42):
        cv.obj([_ell(mx, my, r * k_ + 1, r * k_ + 1, 48)], 0)
        cv.hair(C.hatch_poly(_ell(mx, my, r * k_ + 1, r * k_ + 1, 48), 0, 3 if k_ < 1.3 else 2, 1))
    # the moon
    lit, dark, sx, c = _phase_polys(mx, my, r, age, 48, min_lit=.16)
    disc = _ell(mx, my, r, r, 60)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(dark, 0, 1.5, .75))
    cv.hair(C.hatch_poly(dark, 62, 2))
    # maria on the earthlit side, cross-ruled darker
    for (u, v, a, b) in ((-.35, -.35, .32, .24), (.05, -.15, .26, .3), (-.2, .3, .3, .2), (.35, .25, .2, .18)):
        m = _ell(mx + u * r, my + v * r, a * r, b * r, 18)
        cv.hair(_clip_lines(C.hatch_poly(m, 50, 2), lambda px, py: (px - mx) * sx < r * c - 1.5))
    # the lit crescent: limb highlight, shading lines laid parallel to the terminator
    cv.obj([lit], 0)
    p_ = TAU * age / SYN
    for f in (.15, .35, .55):
        ts = [-math.pi / 2 + math.pi * i / 30 for i in range(31)]
        cc = max(-1., min(1., c * (1 - f) + f))
        pl = [(mx + sx * r * (c + (1 - c) * f * .5) * math.cos(t) * (1 if c >= 0 else 1), my + r * math.sin(t) * (1 - f * .25)) for t in ts]
        cv.hair([q for q in pl if math.hypot(q[0] - mx, q[1] - my) < r - .8])
    # craters on the lit limb
    for t in (-.8, -.2, .5, 1.0):
        qx, qy = mx + sx * r * .82 * math.cos(t), my + r * .82 * math.sin(t)
        cv.hair([_ell(qx, qy, r * .07 + .6, r * .07 + .6, 8)[i] for i in range(5)])
    cv.obj([], 0)
    cv.line(disc + [disc[0]])
    # Mt. Hood on the horizon
    hx = x + w * (.32 if not compact else .3)
    hh = min(h * .36, (hor - y) * .58, w * .23)
    hw = hh * 1.8
    prof = [(hx - hw, hor + 1), (hx - hw * .55, hor - hh * .25), (hx - hw * .3, hor - hh * .5),
            (hx - hw * .12, hor - hh * .82), (hx - hw * .04, hor - hh * .97), (hx, hor - hh),
            (hx + hw * .03, hor - hh * .93), (hx + hw * .07, hor - hh * .95), (hx + hw * .18, hor - hh * .72),
            (hx + hw * .4, hor - hh * .45), (hx + hw * .62, hor - hh * .2), (hx + hw, hor + 1)]
    cv.obj([prof], .5 if compact else 1.)
    snow = hor - hh * .45
    # shadow (left) flank, away from the moon
    shade = [(hx, hor - hh), (hx - hw * .04, hor - hh * .97), (hx - hw * .12, hor - hh * .82),
             (hx - hw * .3, hor - hh * .5), (hx - hw * .55, hor - hh * .25), (hx - hw, hor + 1), (hx - hw * .1, hor + 1)]
    cv.hair(C.hatch_poly(shade, 62, 1.5 if not compact else 2))
    # gullies down the snow, lit side
    for i, f in enumerate((.12, .26, .4, .55)):
        gx = hx + hw * f * .55
        cv.hair([(hx + hw * .01 * i, hor - hh * (.93 - .05 * i)), (gx, hor - hh * .55 + rng.uniform(-2, 2)),
                 (gx + hw * .05, snow + rng.uniform(0, 4))])
    # snow: sparse rules following the slope, so no bare paper
    cv.hair(_clip_lines(C.hatch_poly(prof, 0, 3, .5), lambda px, py: py < snow + 2 and px > hx - hw * .05))
    # timber below the snowline: dense horizontal rules ragged at the top
    for ln in C.hatch_poly(prof, 0, 1.5):
        yy = ln[0][1]
        if yy > snow + rng.uniform(-3, 3):
            cv.hair(ln)
    # foothills, dark
    hills = [(x - 2, hor + 1)]
    for i in range(41):
        t = i / 40
        hills.append((x + w * t, hor - h * .045 * (1 + math.sin(t * 9.1 + 1.3)) * (1.2 - t * .5) - h * .01 * math.sin(t * 31)))
    hills += [(x + w + 2, hor + 2), (x + w + 2, hor + 3), (x - 2, hor + 3)]
    cv.obj([hills], .5)
    cv.hair(C.hatch_poly(hills, 0, 1.5))
    cv.hair(C.hatch_poly(hills, 50, 2))
    # the river: rules, broken into a column of white glitter under the moon
    water = [(x - 2, hor + 2.5), (x + w + 2, hor + 2.5), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([water], 0)
    yy = hor + 4
    i = 0
    while yy < y + h + 2:
        depth = (yy - hor) / max(1., (y + h - hor))
        half = r * (.18 + depth * .55)
        segs = [(x - 2, mx - half - rng.uniform(0, 4))]
        xx = mx - half
        while xx < mx + half:
            gap = rng.uniform(1., 3.) * (1 - abs(xx - mx) / half * .6)
            seg = rng.uniform(1.5, 5) * (.6 + abs(xx - mx) / half)
            segs.append((xx + gap, xx + gap + seg))
            xx += gap + seg
        segs.append((mx + half + rng.uniform(0, 4), x + w + 2))
        pitch = 1.5 if depth < .35 else 2
        for a, b in segs:
            if b - a > .6:
                cv.hair([(a, yy), (b, yy)])
        if i % 3 == 2:   # a second, offset rule darkens the water away from the glitter
            cv.hair([(x - 2, yy + .75), (mx - half * 1.3, yy + .75)])
            cv.hair([(mx + half * 1.3, yy + .75), (x + w + 2, yy + .75)])
        yy += pitch
        i += 1
    body = cv.svg()
    # the Sauvie Island bank in the foreground, black, with cottonwoods, the dog and the heron
    by = y + h * (.86 if not compact else .88)
    bank = [(x - 2, y + h + 2), (x - 2, by - h * .02)]
    bx1 = x + w * (.42 if not compact else .4)
    for i in range(13):
        t = i / 12
        bank.append((x + (bx1 - x) * t, by + (y + h - by) * (t ** 2) * .9 - h * .012 * math.sin(t * 7)))
    bank.append((bx1 + 6, y + h + 2))
    blk = [_d(bank, True, .2)]
    def bank_y(px):
        t = (px - x) / (bx1 - x)
        return by + (y + h - by) * (t ** 2) * .9 - h * .012 * math.sin(t * 7)
    reeds = []
    for i in range(int(w * .3 / 3)):
        rx_ = x + w * .02 + i * 3 + rng.uniform(-1, 1)
        if abs(rx_ - (x + w * (.31 if not compact else .22))) < h * .1:
            continue
        rh = h * rng.uniform(.03, .08)
        lean = rng.uniform(-.25, .35) * rh
        reeds.append([(rx_, bank_y(rx_) + 1), (rx_ + lean * .4, bank_y(rx_) - rh * .6), (rx_ + lean, bank_y(rx_) - rh)])
    ds = h * (.15 if not compact else .22)
    dxp = x + w * (.31 if not compact else .22)
    dog = _dog(dxp, bank_y(dxp) + 1, ds, 1)
    blk.append(_d(dog, True, .1))
    hs = h * (.17 if not compact else .2)
    hb, legs = _heron(x + w * (.54 if not compact else .46), by + h * .045, hs, -1)
    blk.append(_d(hb, True, .1))
    o = [f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">', body,
         f'<path d="{"".join(blk)}" fill="#000" stroke="none" fill-rule="nonzero"/>',
         f'<path d="{"".join(_d(L, tol=0) for L in legs)}" stroke="#000" stroke-width="1"/>',
         f'<path d="{"".join(_d(L, tol=.1) for L in reeds)}" stroke="#000" stroke-width="1"/>']
    # the dog's moonlit outline and the heron's ripples
    o.append(f'<path d="{_d(dog[25:] + dog[:1], tol=.1)}" stroke="#fff" stroke-width=".5"/>')
    rip = "".join(_d([(hb[0][0] - hs * .3 + i * hs * .05, by + h * .05 + i * 1.5), (hb[0][0] + hs * .3 - i * hs * .05, by + h * .05 + i * 1.5)], tol=0) for i in range(2))
    o.append(f'<path d="{rip}" stroke="#fff" stroke-width=".5"/>')
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# little phase discs (for the pedestal tablet)
# ------------------------------------------------------------------------------------------------

def _phase_disc(cx, cy, r, age):
    cv = C.Canvas()
    lit, dark, sx, c = _phase_polys(cx, cy, r, age, 24)
    disc = _ell(cx, cy, r, r, 32)
    cv.obj([disc], 1.)
    k = (1 - math.cos(TAU * age / SYN)) / 2
    if k < .98:
        cv.hair(C.hatch_poly(dark, 45, 1.5))
        cv.hair(C.hatch_poly(dark, -45, 2))
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts (house layouts, re-cut so the scene fills the whole field)
# ------------------------------------------------------------------------------------------------

def _band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    mw = min(w * .36, max(150., gh * 2.6))
    o.append(C._clip(C._uid("nb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, mw * .86, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = mw / 2, gh / 2 - .5
    ring = _d(_ell(cx, cy, rx, ry, 80), True) + _d(_ell(cx, cy, rx - 3, ry - 3, 80)[::-1], True)
    o.append(f'<path d="{_d(_ell(cx, cy, rx, ry, 80), True)}" fill="#fff" stroke="none"/>')
    inner = _ell(cx, cy, rx - 3.5, ry - 3.5, 80)
    o.append(_scene(cx - rx, cy - ry, rx * 2, ry * 2, ctx, _d(inner, True), C._uid("ns", w, h, seed), True))
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 1.5, ry - 1.5, 80), True)}" fill="none" stroke="#fff" stroke-width=".5" stroke-dasharray="0 3" stroke-linecap="round"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _field(cx, cy, cw, ch, seed):
    """The cartouche and the superellipse just inside its bead row."""
    c, rect, _ = C.cartouche(cx, cy, cw, ch, seed)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return c, (cx - a, cy - b, 2 * a, 2 * b), _d(C._superellipse(cx, cy, a - 5.5, b - 5.5), True, .1)


def _medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.75)
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
    o.append(C._clip(C._uid("nm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (fx, fy, fw, fh), clip = _field(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_scene(fx, fy, fw, fh, ctx, clip, C._uid("nms", w, h, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed, ctx, density=.8):
    rng = random.Random(seed)
    age = _age((ctx or {}).get("date", ""))
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("nt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (fx, fy, fw, fh), clip = _field(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_scene(fx, fy, fw, fh, ctx, clip, C._uid("nts", w, h, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, cen = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # the ribbon's face: light rules, with a line of stars and moons engraved along it
    face = [(px, py - bh / 2 + 2.2) for px, py in cen[2:-2]] + [(px, py + bh / 2 - 2.2) for px, py in cen[2:-2]][::-1]
    o.append(f'<path d="{C.hatch_d(face, 0, 2, .5)}" stroke="#000" stroke-width=".5"/>')
    marks = []
    m = 9
    for i in range(m):
        j = int(round(4 + (len(cen) - 9) * i / (m - 1)))
        qx, qy = cen[j]
        if i % 2:
            marks.append(_d(_star(qx, qy, bh * .26), True))
        else:
            o.append(_phase_disc(qx, qy, bh * .24, SYN * (.12 + .76 * i / (m - 1))))
    o.append(f'<path d="{"".join(marks)}" fill="#000" stroke="none"/>')
    py = h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the coming phases engraved on the tablet: first quarter, full, last quarter, new
    o.append(f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{C.pat("M")}" stroke="none"/>')
    rr = min(th * .36, 9)
    for i, a in enumerate((SYN * .25, SYN * .5, SYN * .75, 0.)):
        qx = tx + tw * (i + .5) / 4
        o.append(_phase_disc(qx, ty + th / 2 + .5, rr, a))
    for i in range(1, 4):
        qx = tx + tw * i / 4
        o.append(f'<path d="{_d(_star(qx, ty + th / 2 + .5, 2.2), True)}" fill="#000" stroke="none"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _band(w, h, seed, ctx)
    elif h <= 260:
        body = _medium(w, h, seed, ctx)
    else:
        body = _tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
