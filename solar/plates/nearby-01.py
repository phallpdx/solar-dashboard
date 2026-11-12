"""nearby-01 : Tomorrow's sunset.
House Codex frame (engraving_codex) round a bespoke vignette: the sun going down in the west over
the Tualatin hills, seen from Sauvie Island across the Multnomah Channel, under a full deck of high
cirrus (today's 100 % high cloud) with sun rays breaking through the gaps; the glitter path on the
water, cattails on the near bank.  Easter egg: Parker's dog sitting on the bank watching the sunset,
a rim of last light on its back; a great blue heron fishing in the shallows on the tall plates."""
import sys
import math
import random
import engraving_codex as C

K = 2 ** (-1 / 2.6)


# ------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------

def _dense(pl, step=1.):
    out = [pl[0]]
    for q in pl[1:]:
        p = out[-1]
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        n = max(1, int(L / step))
        for j in range(1, n + 1):
            out.append((p[0] + (q[0] - p[0]) * j / n, p[1] + (q[1] - p[1]) * j / n))
    return out


def _runs(pts, key):
    """Split a dense polyline into runs of equal key(pt); returns [(key, run)]."""
    res = []
    cur, run = None, []
    for p in pts:
        k = key(p)
        if k != cur:
            if run and cur is not None and len(run) > 1:
                res.append((cur, run))
            run = [run[-1]] if run else []
            cur = k
        run.append(p)
    if run and cur is not None and len(run) > 1:
        res.append((cur, run))
    return res


def _poly_d(pts):
    return C._d(pts, True, .15)


def _shape(ox, oy, s, pts, flip=False):
    return [(ox + (-x if flip else x) * s, oy + y * s) for x, y in pts]


# a sitting dog, side view, facing +x, feet at y=0, ear tip at y=-1
DOG = [(0.00, 0.00), (-0.20, -0.01), (-0.30, -0.05), (-0.26, -0.08), (-0.12, -0.06), (-0.03, -0.10),
       (-0.02, -0.24), (0.03, -0.38), (0.10, -0.50), (0.17, -0.62), (0.22, -0.72), (0.24, -0.82),
       (0.27, -0.92), (0.29, -1.00), (0.35, -0.95), (0.37, -0.89), (0.44, -0.88), (0.52, -0.85),
       (0.62, -0.82), (0.65, -0.79), (0.63, -0.75), (0.52, -0.73), (0.45, -0.70), (0.41, -0.62),
       (0.41, -0.50), (0.42, -0.30), (0.42, -0.05), (0.50, -0.03), (0.52, 0.00)]
DOG_RIM = [(0.0, -0.18), (0.04, -0.37), (0.11, -0.50), (0.18, -0.62), (0.23, -0.73), (0.25, -0.83)]

# a great blue heron standing, facing -x, feet at y=0, crown at about y=-1
HERON = [(0.30, -0.47), (0.16, -0.57), (0.02, -0.62), (-0.06, -0.63), (-0.10, -0.70), (-0.05, -0.80),
         (-0.06, -0.89), (-0.10, -0.96), (-0.04, -1.00), (0.04, -0.99), (-0.03, -0.96), (-0.13, -0.95),
         (-0.40, -0.93), (-0.14, -0.91), (-0.13, -0.86), (-0.14, -0.81), (-0.19, -0.73),
         (-0.18, -0.62), (-0.12, -0.51), (0.02, -0.45), (0.16, -0.44)]


# ------------------------------------------------------------------------------------------
# the vignette
# ------------------------------------------------------------------------------------------

def sunset(X, Y, W, H, field, seed, uid):
    """Engrave the sunset scene over the box X,Y,W,H, clipped to the polygon `field`."""
    rng = random.Random(seed)
    cv = C.Canvas()
    blacks = []          # solid silhouettes (painted last)
    whites = []          # 0.5 px white rim-light strokes (on the silhouettes)
    small = H < 70
    hy = Y + H * (.6 if not small else .64)          # horizon (ridge foot / far shore)
    sx = X + W * (.55 if not small else .5)
    r = max(7., min(W, H) * (.17 if not small else .2))
    sy = hy - H * .045 - r * .3
    top = Y

    # ---- sky: rows on a 1.5 px grid; tone by height, lit sun rays and the glow
    n_rays = 21 if not small else 13

    def sky_level(p):
        x, y = p
        t = (y - top) / max(1., hy - top)
        lv = 3.2 - 2.4 * t
        dx, dy = x - sx, y - sy
        d = math.hypot(dx, dy)
        a = math.atan2(dy, dx)
        if dy < 0:
            k = int(math.floor((a + math.pi) / math.pi * n_rays * 2))
            if k % 2 == 0:
                lv -= 1.3 * min(1., (2.0 * r / max(d, 1.)) ** 1.3)
        lv -= 1.8 * max(0., 1 - d / (2.2 * r))
        return max(0, min(3, int(round(lv))))

    sky = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, hy + 1), (X - 2, hy + 1)]
    cv.obj([sky], 0)
    yk = 0
    y = Y + .75
    while y < hy + .5:
        pl = _dense([(X - 1, y), (X + W + 1, y)])
        for lv, run in _runs(pl, sky_level):
            if lv == 3:
                cv.line(run)
            elif lv == 2:
                cv.hair(run)
            elif lv == 1 and yk % 2 == 0:
                cv.hair(run)
            elif lv == 0 and yk % 4 == 0:
                cv.hair(run)
        y += 1.5
        yk += 1

    # ---- the sun: ruled disc, heavy rim
    disc = C._ell_pts(sx, sy, r, r, 56)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 3, .6, inset=1.6))
    cv.hair([(sx + (r + 2.2) * math.cos(t / 40 * math.tau), sy + (r + 2.2) * math.sin(t / 40 * math.tau)) for t in range(41)])

    # ---- banks of high cloud (100 % high cover), billowed tops, lit undersides, gaps for the rays
    rows = 3 if not small else 2
    for i in range(rows):
        cy = top + (hy - top) * ((.2 + .58 * i / max(1, rows - 1)) if not small else (.25 + .45 * i))
        x = X - rng.uniform(10, 40) - (W * .25 if i % 2 else 0)
        while x < X + W:
            L = rng.uniform(.38, .62) * W
            T = (rng.uniform(4.5, 7.) if not small else rng.uniform(2.6, 3.6)) * (1 + .35 * i / rows) * (H / 160) ** .4
            tilt = rng.uniform(-.03, .015)
            cx0 = x
            n = 60
            upper, lower = [], []
            ph = rng.uniform(0, 6)
            nb = rng.randint(4, 7)
            for j in range(n + 1):
                u = j / n
                px = cx0 + L * u
                c = cy + tilt * (px - cx0) + 1.0 * math.sin(u * 4 + ph)
                env = math.sin(math.pi * u) ** .6
                bump = .6 + .4 * abs(math.sin(u * nb * math.pi + ph))
                upper.append((px, c - T * env * bump * 1.25))
                lower.append((px, c + T * env * .45))
            poly = upper + lower[::-1]
            cv.obj([poly], 0)
            cv.line(upper[3:-3])
            cv.hair(upper)
            # contour shading following the bank: dense and dark along the top, a lit white underside
            for s_ in (.1, .2, .3, .42, .56, .7):
                cv.hair([(a_[0], a_[1] + (b_[1] - a_[1]) * s_) for a_, b_ in zip(upper[2:-2], lower[2:-2])])
            cv.hair([(a_[0], b_[1]) for a_, b_ in zip(upper[6:-6], lower[6:-6])])
            x += L + rng.uniform(.05, .22) * W

    # ---- far hills (the Tualatin ridge across the channel)
    def ridge(base, amp, freq, ph):
        return [(X - 2 + (W + 4) * j / 60,
                 base - amp * (.55 + .3 * math.sin(j / 60 * freq + ph) + .15 * math.sin(j / 60 * freq * 2.7 + ph * 2)))
                for j in range(61)]
    far = ridge(hy, H * .1, 6, rng.uniform(0, 6))
    farp = far + [(X + W + 2, hy + 1), (X - 2, hy + 1)]
    cv.obj([farp], 0)
    cv.hair(far)
    cv.hair(C.hatch_poly(farp, 0, 1.5, .3))
    near = ridge(hy, H * .05, 9, rng.uniform(0, 6))
    nearp = near + [(X + W + 2, hy + 1), (X - 2, hy + 1)]
    cv.obj([nearp], 0)
    cv.line(C.hatch_poly(nearp, 0, 1.5, .3))
    cv.hair(C.hatch_poly(nearp, 60, 1.5))
    cv.line(near)

    # ---- water: broken rules, the reflection of the ridge, the sun's glitter path
    bank = Y + H * (.84 if not small else 1.02)
    water = [(X - 2, hy), (X + W + 2, hy), (X + W + 2, bank + 6), (X - 2, bank + 6)]
    cv.obj([water], 0)
    y = hy + 1
    k = 0
    while y < bank + 6:
        t = (y - hy) / max(1., bank - hy)
        x = X - 2
        while x < X + W + 2:
            gw = abs(x - sx) / (r * (.7 + 1.6 * t))
            if t < .14:
                seg, gap, wt = rng.uniform(8, 30), rng.uniform(.8, 1.5), 1.
            elif gw < 1:
                seg, gap, wt = rng.uniform(1.5, 4), rng.uniform(2, 4), .5
            else:
                seg, gap, wt = rng.uniform(10, 40), rng.uniform(1.5, 4), .5 if t < .6 else 1.
            pl = [(x, y), (min(x + seg, X + W + 2), y)]
            (cv.line if wt == 1. else cv.hair)(pl)
            x += seg + gap
        y += 1.5 if gw >= 1 or k % 2 == 0 else 1.5
        k += 1

    # ---- near bank, cattails, the dog (and the heron when there is room)
    if not small:
        bpts = [(X - 2 + (W + 4) * j / 40, bank + 3 * math.sin(j / 40 * 9 + seed) - 4 * (1 - j / 40) ** 2 * 2)
                for j in range(41)]
        bankp = bpts + [(X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
        blacks.append(_poly_d(bankp))
        reeds = []
        for i in range(int(W / 7)):
            bx = X + rng.uniform(0, 1) * W
            if abs(bx - sx) < r * .9 or abs(bx - (X + W * .3)) < H * .09:
                continue
            ht = rng.uniform(.05, .14) * H
            lean = rng.uniform(-.25, .25)
            by = bank + 2
            tip = (bx + lean * ht, by - ht)
            reeds.append([(bx, by), ((bx + tip[0]) / 2 + lean * 2, by - ht / 2), tip])
            if rng.random() < .45 and ht > 10:
                ty = by - ht * .78
                blacks.append(_poly_d(C._ell_pts(bx + lean * ht * .78, ty, 1.3, ht * .1, 12)))
        for i in range(int(W / 3)):
            gx = X + W * i / int(W / 3) + rng.uniform(-1, 1)
            j = min(40, max(0, int((gx - X + 2) / (W + 4) * 40)))
            gy = bpts[j][1] + rng.uniform(3, 9)
            if gy < Y + H - 2:
                whites.append(C._d([(gx, gy), (gx + rng.uniform(-1.5, 1.5), gy - rng.uniform(2, 4))]))
        # the dog, sitting on the bank, watching the sun
        ds = H * .2
        dx = X + W * .3
        blacks.append(_poly_d(_shape(dx, bank + 1, ds, DOG)))
        whites.append(C._d(_shape(dx, bank + 1, ds, DOG_RIM)))
        # the heron in the shallows, right of the glitter
        hs = H * .22
        if H > 120:
            hx = X + W * .8
            hyy = bank - H * .045
            blacks.append(_poly_d(_shape(hx, hyy - hs * .03, hs, HERON)))
            reeds.append([(hx + hs * .03, hyy - hs * .44), (hx + hs * .02, hyy + 1)])
            reeds.append([(hx + hs * .09, hyy - hs * .44), (hx + hs * .12, hyy + 1)])
            whites.append(C._d(_shape(hx, hyy - hs * .03, hs, [(.28, -.48), (.15, -.56), (.02, -.61)])))
            # ripples round its legs
            for j, rr in enumerate((3, 6)):
                cv.hair([(hx + hs * .07 + rr * 1.8 * math.cos(t / 16 * math.pi), hyy + 1.5 + rr * .35 * math.sin(t / 16 * math.pi)) for t in range(17)])
        reed_d = "".join(C._d(rp) for rp in reeds)
    else:
        reed_d = ""

    out = [f'<clipPath id="{uid}"><path d="{_poly_d(field)}"/></clipPath><g clip-path="url(#{uid})">', cv.svg()]
    if blacks:
        out.append(f'<path d="{"".join(blacks)}" fill="#000" stroke="none"/>')
    if reed_d:
        out.append(f'<path d="{reed_d}" stroke="#000" stroke-width="1"/>')
    if whites:
        out.append(f'<path d="{"".join(whites)}" stroke="#fff" stroke-width=".5"/>')
    out.append('</g>')
    out.append(f'<path d="{_poly_d(field)}" stroke="#000" stroke-width="1"/>')
    return "".join(out)


# ------------------------------------------------------------------------------------------
# tall layout: the house _layout_tall, copied so the ribbon and the pedestal tablet get engraved
# ------------------------------------------------------------------------------------------

def _banner_fill(centre, bh):
    """Rule the ribbon face along its run, a white edge left top and bottom."""
    o = []
    for s_ in (-.28, -.14, 0., .14, .28):
        o.append(C._d([(x, y + s_ * bh) for x, y in centre[2:-2]]))
    return f'<path d="{"".join(o)}" stroke="#000" stroke-width=".5"/>'


def _tablet(tx, ty, tw, th, seed):
    """The sunken tablet: the sun setting across the half-hour of best colour, in seven stages,
    each disc a little lower behind a ruled horizon, on a ruled ground."""
    cv = C.Canvas()
    x0, y0, x1, y1 = tx + 2.5, ty + 2.5, tx + tw - 1, ty + th - 1
    box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    cv.obj([box], 0)
    cv.hair(C.hatch_poly(box, 0, 1.5, .4))
    hzy = y0 + (y1 - y0) * .66
    rr = (y1 - y0) * .4
    n = 7
    for i in range(n):
        cx = x0 + (x1 - x0) * (i + .5) / n
        cy = hzy - rr * (.9 - 1.5 * i / (n - 1))
        disc = C._ell_pts(cx, cy, rr, rr, 28)
        cv.obj([disc], 1.)
        cv.hair(C.hatch_poly(disc, 0, 3, .7, inset=1.2))
    sea = [(x0, hzy), (x1, hzy), (x1, y1), (x0, y1)]
    cv.obj([sea], 0)
    cv.line(C.hatch_poly(sea, 0, 1.5, .4))
    cv.line([(x0, hzy), (x1, hzy)])
    return cv.svg()


def _layout_tall(w, h, seed, fill_fn, density=1.):
    rng = random.Random(seed)
    o = []
    _n = C._n
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .48, ph * .6
    cx, cy = w / 2, py0 + ph * .45
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
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(fill_fn(ix, iy, iw, ih))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_fill(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, seed))
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


# ------------------------------------------------------------------------------------------
# plate
# ------------------------------------------------------------------------------------------

def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    uid = f"nb01c{int(w)}x{int(h)}s{ctx.get('sheet', 0) if isinstance(ctx.get('sheet', 0), int) else 0}".replace("-", "m")

    def fill(ix, iy, iw, ih):
        cx, cy = ix + iw / 2, iy + ih / 2
        if h < 110:
            # band medallion: ellipse field
            rx, ry = iw / 2 / .7071 + 5 - 4.5, ih / 2 / .7071 + 5 - 4.5
            field = C._ell_pts(cx, cy, rx, ry, 72)
        else:
            a, b = iw / 2 / K + 6, ih / 2 / K + 6
            field = C._superellipse(cx, cy, a - 5.5, b - 5.5, 2.6, 120)
        xs = [p[0] for p in field]
        ys = [p[1] for p in field]
        X0, Y0 = min(xs), min(ys)
        return sunset(X0, Y0, max(xs) - X0, max(ys) - Y0, field, seed, uid)

    if h > 260:
        return C.svg_doc(w, h, _layout_tall(w, h, seed, fill))
    return C.frame_plate(w, h, seed, fill)
