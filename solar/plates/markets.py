"""Money and markets: a helium balloon (North American Helium) lifts off over a street of Portland
houses (real estate) with Mt. Hood behind, inside the house Codex frame; the pedestal tablet
carries an engraved candlestick tape that climbs like today's S&P, and a ribbon carries the ticker
line. Easter egg: a great blue heron from Sauvie Island flying past Mt. Hood (tall/medium) and a
tiny 'P' pennant on the balloon's basket."""
import sys
import math
import random
import engraving_codex as C

_n, _d, pat = C._n, C._d, C.pat
TAU = math.tau


# ---------------------------------------------------------------------------------------------
# small drawing helpers (painter's order: white shape, hatch inside it, outline)
# ---------------------------------------------------------------------------------------------

def _poly_d(p):
    return _d(p + [p[0]], True, 0)


def _lines_d(pls, tol=0):
    return "".join(_d(pl, tol=tol) for pl in pls if len(pl) > 1)


def _shape(o, poly, hatches=(), outline=1., fill="#fff"):
    """hatches: list of (angle, pitch, phase, weight)."""
    o.append(f'<path d="{_poly_d(poly)}" fill="{fill}" stroke="none"/>')
    for ang, pitch, ph, wt in hatches:
        ls = C.hatch_poly(poly, ang, pitch, ph)
        if ls:
            o.append(f'<path d="{_lines_d(ls)}" stroke="#000" stroke-width="{wt}"/>')
    if outline:
        o.append(f'<path d="{_poly_d(poly)}" fill="none" stroke="#000" stroke-width="{outline}"/>')


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (x1 - x0) * (y - y0) / (y1 - y0):
            c = not c
    return c


def _filter_lines(lines, keep, step=.8):
    """Break straight 2-point lines into runs where keep(x, y) holds."""
    out = []
    for (x0, y0), (x1, y1) in lines:
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        cur = []
        for i in range(n + 1):
            t = i / n
            p = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if keep(*p):
                cur.append(p)
            else:
                if len(cur) > 1:
                    out.append([cur[0], cur[-1]])
                cur = []
        if len(cur) > 1:
            out.append([cur[0], cur[-1]])
    return out


def _seed(ctx):
    return sum(map(ord, (ctx or {}).get("date", ""))) + 7


# ---------------------------------------------------------------------------------------------
# the vignette: helium balloon over Portland houses, Mt. Hood behind
# ---------------------------------------------------------------------------------------------

def _mountain(o, X, Y, W, H, k):
    peak = (X + W * .6, Y + H * .17)
    base_y = Y + H * .6
    L, R = X + W * .14, X + W * 1.06
    rng = random.Random(3)
    left = [(L, base_y)]
    for i in range(1, 12):
        t = i / 12
        x = L + (peak[0] - L) * t
        y = base_y + (peak[1] - base_y) * (t ** 1.35) + rng.uniform(-1, 1) * H * .006
        left.append((x, y))
    right = []
    for i in range(1, 12):
        t = i / 12
        x = peak[0] + (R - peak[0]) * t
        y = peak[1] + (base_y - peak[1]) * (t ** .75) + rng.uniform(-1, 1) * H * .006
        right.append((x, y))
    mtn = left + [peak] + right + [(R, base_y)]
    # shadow side (right of a ridge line falling from the peak) dark, sunlit left side light
    _shape(o, mtn, [], 0, pat("M"))
    o.append(f'<path d="{_lines_d(C.hatch_poly(mtn, -62, 3))}" stroke="#000" stroke-width=".5"/>')
    ridge = [peak, (peak[0] + W * .02, peak[1] + H * .1), (peak[0] - W * .01, peak[1] + H * .22),
             (peak[0] + W * .03, base_y)]
    shade = ridge + [(R, base_y)] + right[::-1]
    o.append(f'<path d="{_lines_d(C.hatch_poly(shade, 60, 1.5))}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_lines_d(C.hatch_poly(shade, -20, 3))}" stroke="#000" stroke-width=".5"/>')
    # snowcap: jagged lower edge, white with couloir lines and a ruled shadow side
    sy = peak[1] + (base_y - peak[1]) * .5

    def edge_x(poly_side, y):
        for (x0, y0), (x1, y1) in zip(poly_side, poly_side[1:]):
            if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
                return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
        return poly_side[-1][0]
    lpts = [p for p in left if p[1] <= sy + 1] + [peak]
    rpts = [peak] + [p for p in right if p[1] <= sy + 1]
    xl = edge_x(left + [peak], sy)
    xr = edge_x([peak] + right, sy)
    jag = []
    n = 14
    for i in range(n + 1):
        t = i / n
        x = xr + (xl - xr) * t
        d = (H * random.Random(i * 7 + 1).uniform(.025, .075) if i % 2 else -H * .012) * (1 - abs(t - .5) * 1.2)
        jag.append((x, sy + d))
    snow = [(xl, sy)] + [p for p in lpts if p[1] < sy] + rpts[1:] + [p for p in [(xr, sy)]] + jag[1:-1]
    snow = [p for p in snow]
    o.append(f'<path d="{_poly_d(snow)}" fill="#fff" stroke="none"/>')
    sh = ([peak, (peak[0] + W * .02, peak[1] + H * .1), (peak[0] - W * .005, sy + H * .04)]
          + sorted([p for p in jag if p[0] > peak[0]], key=lambda p: p[0]) + [p for p in rpts if p[1] < sy][::-1])
    shp = [p for p in sh]
    o.append(f'<path d="{_lines_d(C.hatch_poly(shp, 58, 2))}" stroke="#000" stroke-width=".5"/>')
    # couloirs on the lit side: fine lines running down the fall line
    cl = []
    for i in range(1, 6):
        x0 = peak[0] - (peak[0] - xl) * i / 6
        y0 = peak[1] + (sy - peak[1]) * (i / 6) * .55
        cl.append([(x0, y0), (x0 - W * .006, y0 + (sy - y0) * .5), (x0 + W * .003, sy + H * .02 * (i % 2))])
    o.append(f'<path d="{_lines_d(cl, .2)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_d(lpts + rpts[1:], tol=0)}" stroke="#000" stroke-width="1"/>')
    return base_y


def _treeline(o, X, Y, W, H, y0, k, rng):
    pts = [(X - 2, y0 + H * .1)]
    x = X - 2
    while x < X + W + 4:
        th = H * rng.uniform(.035, .075)
        tw = max(3., W * rng.uniform(.018, .03))
        base = y0 + H * .03 + rng.uniform(-1, 1) * H * .01
        pts += [(x, base), (x + tw / 2, base - th), (x + tw, base)]
        x += tw * rng.uniform(.6, .9)
    pts += [(X + W + 4, y0 + H * .1)]
    o.append(f'<path d="{_poly_d(pts)}" fill="{pat("G")}" stroke="none"/>')
    o.append(f'<path d="{_d(pts[1:-1], tol=0)}" stroke="#000" stroke-width=".5"/>')


def _house(o, x, gy, w, h, roof, rng, k, chimney=True, porch=True):
    """A Portland old house: lap-sided walls, steep gable, windows, porch."""
    wall = [(x, gy), (x, gy - h), (x + w, gy - h), (x + w, gy)]
    ry = gy - h
    rise = w * .5 * roof
    peak = (x + w / 2, ry - rise)
    # chimney behind the roof
    if chimney:
        cx = x + w * (.72 if rng.random() < .5 else .22)
        ch = [(cx, ry - rise * .2), (cx, ry - rise * .95), (cx + w * .08, ry - rise * .95), (cx + w * .08, ry - rise * .2)]
        _shape(o, ch, [(0, 1.5, 0, .5)], 1.)
    _shape(o, wall, [(0, 2 if w > 40 else 3, .5, .5)], 1.)
    # shadow side of the house (east wall in shade): vertical rules over the right fifth
    sh = [(x + w * .8, gy), (x + w * .8, gy - h), (x + w, gy - h), (x + w, gy)]
    o.append(f'<path d="{_lines_d(C.hatch_poly(sh, 90, 1.5))}" stroke="#000" stroke-width=".5"/>')
    eave = w * .08
    gable = [(x - eave, ry + 1), peak, (x + w + eave, ry + 1)]
    # roof face: shingle courses (horizontal) + a darker raking hatch on the shaded half
    _shape(o, gable, [(0, 1.5, 0, .5)], 1.5)
    right_half = [peak, (x + w + eave, ry + 1), (x + w / 2, ry + 1)]
    o.append(f'<path d="{_lines_d(C.hatch_poly(right_half, -35, 2))}" stroke="#000" stroke-width=".5"/>')
    # gable window (attic) and bargeboard
    gw = max(2., w * .1)
    gwy = ry - rise * .45
    if w > 26:
        o.append(f'<path d="{_poly_d([(peak[0] - gw / 2, gwy - gw * .7), (peak[0] + gw / 2, gwy - gw * .7), (peak[0] + gw / 2, gwy + gw * .7), (peak[0] - gw / 2, gwy + gw * .7)])}" fill="#000" stroke="#fff" stroke-width=".5"/>')
    # windows: two up, one down + door
    blacks, mullions = [], []
    ww, wh = w * .18, h * .24
    for fx, fy in ((.2, .18), (.62, .18), (.2, .58)):
        wx, wy = x + w * fx, gy - h + h * fy
        blacks.append([(wx, wy), (wx + ww, wy), (wx + ww, wy + wh), (wx, wy + wh)])
        if ww > 4:
            mullions.append([(wx + ww / 2, wy), (wx + ww / 2, wy + wh)])
            mullions.append([(wx, wy + wh / 2), (wx + ww, wy + wh / 2)])
    dx, dw = x + w * .6, w * .2
    blacks.append([(dx, gy), (dx, gy - h * .42), (dx + dw, gy - h * .42), (dx + dw, gy)])
    o.append(f'<path d="{"".join(_poly_d(b) for b in blacks)}" fill="#000" stroke="none"/>')
    if mullions:
        o.append(f'<path d="{_lines_d(mullions)}" stroke="#fff" stroke-width=".5"/>')
    if porch and w > 30:
        # porch roof and posts across the lower front
        py = gy - h * .48
        pr = [(x - 2, py + 2), (x + w * .9, py + 2), (x + w * .9 + 2, py - 2), (x - 4, py - 2)]
        _shape(o, pr, [(90, 1.5, 0, .5)], 1.)
        posts = [[(x + w * f, py + 2), (x + w * f, gy)] for f in (.04, .48, .88)]
        o.append(f'<path d="{_lines_d(posts)}" stroke="#000" stroke-width="1.5"/>')
        rail = [[(x, gy - h * .14), (x + w * .58, gy - h * .14)]]
        rail += [[(x + w * f / 10, gy - h * .14), (x + w * f / 10, gy)] for f in range(1, 6)]
        o.append(f'<path d="{_lines_d(rail)}" stroke="#000" stroke-width=".5"/>')
    return peak


def _sale_sign(o, x, gy, s):
    """A real-estate sign on a post (blank board, hatched: no lettering)."""
    post = [[(x, gy), (x, gy - s * 1.6)], [(x, gy - s * 1.5), (x + s * 1.2, gy - s * 1.5)]]
    o.append(f'<path d="{_lines_d(post)}" stroke="#000" stroke-width="1"/>')
    b = [(x + s * .15, gy - s * 1.45), (x + s * 1.15, gy - s * 1.45), (x + s * 1.15, gy - s * .8), (x + s * .15, gy - s * .8)]
    _shape(o, b, [(45, 1.5, 0, .5)], 1.)
    o.append(f'<path d="{_d([(x + s * .3, gy - s * 1.12), (x + s * 1.0, gy - s * 1.12)], tol=0)}" stroke="#fff" stroke-width="1"/>')


def _heron(o, x, y, s, flip=False):
    """A great blue heron in flight: neck tucked, legs trailing, wings up. Black silhouette."""
    f = -1 if flip else 1

    def P(px, py):
        return (x + f * px * s, y + py * s)
    body = [P(-.5, 0), P(-.2, -.12), P(.25, -.1), P(.45, -.02), P(.25, .1), P(-.3, .1)]
    neck = [P(.4, -.06), P(.55, -.2), P(.5, -.32), P(.62, -.36), P(.66, -.3), P(.6, -.22), P(.66, -.1), P(.45, .04)]
    beak = [P(.62, -.36), P(.95, -.3), P(.64, -.29)]
    wing = [P(-.15, -.08), P(-.45, -.55), P(-.1, -.95), P(.1, -.5), P(.2, -.08)]
    wing2 = [P(-.05, -.02), P(.2, -.3), P(.45, -.4), P(.25, -.02)]
    o.append(f'<path d="{"".join(_poly_d(p) for p in (body, neck, beak, wing, wing2))}" fill="#000" stroke="none"/>')
    legs = [[P(-.45, .02), P(-1.0, .1)], [P(-.45, .05), P(-1.0, .16)]]
    o.append(f'<path d="{_lines_d(legs)}" stroke="#000" stroke-width=".5"/>')
    # white feather lines in the wing so it reads as a bird, not a blot
    if s > 14:
        fl = [[P(-.1 + .05 * i, -.12), P(-.35 + .1 * i, -.65 + .05 * i)] for i in range(4)]
        o.append(f'<path d="{_lines_d(fl)}" stroke="#fff" stroke-width=".5"/>')


def _balloon(o, cx, cy, r, k, rng, pennant=True):
    """A gas balloon: striped gores shaded into a dark crescent, netting, ropes, basket."""
    # envelope: a sphere that tapers into a neck
    env = []
    for i in range(72):
        t = TAU * i / 72
        sx, sy = math.cos(t), math.sin(t)
        if sy > 0:
            sx *= 1 - .35 * sy ** 2
            sy *= 1.12
        env.append((cx + r * sx, cy + r * sy))
    neck_y = cy + r * 1.12
    o.append(f'<path d="{_poly_d(env)}" fill="#fff" stroke="none"/>')
    # gores: meridians x = cx + r*sin(phi)*cos(t) ; alternate gores dark ruled
    ng = 8
    mer = []
    for g in range(ng + 1):
        phi = -math.pi / 2 + math.pi * g / ng
        pts = []
        for j in range(41):
            t = -math.pi / 2 + math.pi * j / 40
            sx, sy = math.sin(phi) * math.cos(t), math.sin(t)
            if sy > 0:
                sx *= 1 - .35 * sy ** 2
                sy *= 1.12
            pts.append((cx + r * sx, cy + r * sy))
        mer.append(pts)
    for g in range(0, ng, 2):
        gore = mer[g] + mer[g + 1][::-1]
        ls = C.hatch_poly(gore, 90, 2 if r > 30 else 3)
        o.append(f'<path d="{_lines_d(ls)}" stroke="#000" stroke-width=".5"/>')
    for g in range(1, ng, 2):
        gore = mer[g] + mer[g + 1][::-1]
        ls = C.hatch_poly(gore, 0, 3, 1)
        o.append(f'<path d="{_lines_d(ls)}" stroke="#000" stroke-width=".5"/>')
    # form shading: everything outside a light disc toward the upper left gets cross-hatch
    lx, ly, lr = cx - r * .35, cy - r * .35, r * .82
    lr2 = r * 1.05

    def dark1(x, y):
        return math.hypot(x - lx, y - ly) > lr

    def dark2(x, y):
        return math.hypot(x - lx, y - ly) > lr2
    h1 = _filter_lines(C.hatch_poly(env, 40, 2), dark1)
    h2 = _filter_lines(C.hatch_poly(env, -35, 2, .5), dark2)
    h3 = _filter_lines(C.hatch_poly(env, 40, 2, 1), lambda x, y: math.hypot(x - lx, y - ly) > r * 1.25)
    o.append(f'<path d="{_lines_d(h1 + h2 + h3)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_lines_d(mer[1:-1], .2)}" stroke="#000" stroke-width=".5"/>')
    # netting: latitude cords
    lat = []
    for q in (-.55, -.1, .35, .72):
        pts = []
        for j in range(41):
            a = -math.pi / 2 + math.pi * j / 40
            sy = q
            w = math.sqrt(max(0, 1 - q * q))
            sx = w * math.sin(a)
            if sy > 0:
                sx *= 1 - .35 * sy ** 2
                sy *= 1.12
            pts.append((cx + r * sx, cy + r * sy))
        lat.append(pts)
    o.append(f'<path d="{_lines_d(lat, .2)}" stroke="#000" stroke-width=".5" stroke-dasharray="1.5 1"/>')
    o.append(f'<path d="{_poly_d(env)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    # a small specular glint (stays white and under 12 px)
    gl = C._ell_pts(cx - r * .45, cy - r * .5, r * .1, r * .16, 16)
    o.append(f'<path d="{_poly_d(gl)}" fill="#fff" stroke="none"/>')
    # load ring, ropes, basket
    ringy = neck_y + r * .18
    bw, bh = r * .5, r * .32
    by = neck_y + r * .55
    ropes = [[(cx + r * .62 * s, cy + r * .78), (cx + bw / 2 * s * .9, by)] for s in (-1, -.35, .35, 1)]
    ropes.append([(cx - r * .12, neck_y - 1), (cx, ringy)])
    ropes.append([(cx + r * .12, neck_y - 1), (cx, ringy)])
    o.append(f'<path d="{_lines_d(ropes)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_poly_d(C._ell_pts(cx, ringy, r * .08, r * .03, 12))}" fill="none" stroke="#000" stroke-width="1"/>')
    basket = [(cx - bw / 2, by), (cx + bw / 2, by), (cx + bw * .42, by + bh), (cx - bw * .42, by + bh)]
    _shape(o, basket, [(60, 1.5, 0, .5), (-60, 3, 0, .5)], 1.)
    rim = [(cx - bw / 2 - 1, by - 1), (cx + bw / 2 + 1, by - 1), (cx + bw / 2 + 1, by + 1.5), (cx - bw / 2 - 1, by + 1.5)]
    _shape(o, rim, [], 1., "#000")
    # sandbags
    bags = [C._ell_pts(cx + s * bw * .52, by + bh * .55, max(1.2, r * .05), max(1.6, r * .07), 10) for s in (-1, 1)]
    o.append(f'<path d="{"".join(_poly_d(b) for b in bags)}" fill="#000" stroke="none"/>')
    if pennant and r > 22:
        # a pennant on a staff from the basket, carrying an engraved P monogram (Easter egg)
        sx0, sy0 = cx + bw * .38, by
        top = (sx0 + r * .1, by - r * .62)
        o.append(f'<path d="{_d([(sx0, sy0), top], tol=0)}" stroke="#000" stroke-width="1"/>')
        L = r * .5
        pen = [top, (top[0] + L, top[1] + L * .18), (top[0], top[1] + L * .36)]
        _shape(o, pen, [(0, 1.5, 0, .5)], .5)
        # P cut white out of the ruled pennant
        px, py, ph = top[0] + L * .14, top[1] + L * .07, L * .24
        pP = [(px, py + ph), (px, py)]
        bowl = [(px, py)] + [(px + ph * .28 + ph * .28 * math.cos(a), py + ph * .28 - ph * .28 * math.sin(a))
                             for a in [math.pi / 2 - math.pi * j / 8 for j in range(9)]] + [(px, py + ph * .56)]
        o.append(f'<path d="{_d(pP, tol=0)}{_d(bowl, tol=0)}" stroke="#fff" stroke-width="1" fill="none"/>')


def _scene(X, Y, W, H, clip_d, ctx, small=False):
    rng = random.Random(_seed(ctx))
    k = min(W, H * 1.4) / 240.
    o = []
    # sky: deep ruled at the zenith easing to light ruled, then a morning glow of fine stipple
    o.append(f'<path d="M{_n(X - 2)},{_n(Y - 2)}h{_n(W + 4)}v{_n(H + 4)}h{_n(-W - 4)}z" fill="{pat("L")}" stroke="none"/>')
    o.append(f'<path d="M{_n(X - 2)},{_n(Y - 2)}h{_n(W + 4)}v{_n(H * .2 + 2)}h{_n(-W - 4)}z" fill="{pat("M")}" stroke="none"/>')
    # sun rays fanning from behind the mountain (morning)
    sx, sy = X + W * .64, Y + H * .5
    rays = []
    for i in range(29):
        a = math.pi + math.pi * (i + .5) / 29
        if i % 2:
            continue
        rays.append([(sx + math.cos(a) * H * .3, sy + math.sin(a) * H * .3),
                     (sx + math.cos(a) * W * 1.2, sy + math.sin(a) * W * 1.2)])
    o.append(f'<path d="{_lines_d(rays)}" stroke="#fff" stroke-width="1"/>')
    # clouds: a couple of soft ruled banks with scalloped tops
    for cxx, cyy, cw in ((X + W * .86, Y + H * .17, W * .28), (X + W * .08, Y + H * .52, W * .3)):
        if small:
            break
        top = []
        n = 6
        for i in range(n + 1):
            t = i / n
            top.append((cxx - cw / 2 + cw * t, cyy - (H * .025 + H * .02 * math.sin(t * math.pi)) * (1 + .5 * (i % 2))))
        cl = top + [(cxx + cw / 2, cyy + H * .02), (cxx - cw / 2, cyy + H * .02)]
        _shape(o, cl, [(0, 3, 1.5, .5)], 0)
        o.append(f'<path d="{_d(top, tol=0)}" stroke="#000" stroke-width=".5"/>')
    base_y = _mountain(o, X, Y, W, H, k)
    if not small:
        _heron(o, X + W * .86, Y + H * .3, max(8., W * .055), flip=True)
    gy = Y + H * .86
    _treeline(o, X, Y, W, H, base_y - H * .02, k, rng)
    # middle distance: a ruled field
    fld = [(X - 2, base_y + H * .06), (X + W + 2, base_y + H * .05), (X + W + 2, gy), (X - 2, gy)]
    _shape(o, fld, [(0, 2, 0, .5)], 0)
    # the street of houses, bigger to the right, the left kept for the balloon's tether
    houses = []
    if small:
        spec = [(.42, .2, .26, 1.0), (.66, .22, .32, 1.1)]
    else:
        spec = [(.4, .15, .17, 1.1), (.56, .15, .21, 1.2), (.74, .18, .19, .95), (.92, .15, .23, 1.15)]
    for fx, fw, fh, roof in spec:
        houses.append((X + W * fx, W * fw, H * fh, roof))
    for hx, hw, hh, roof in houses:
        _house(o, hx - hw / 2, gy, hw, hh, roof, rng, k, porch=not small)
    # front lawn / street
    fg = [(X - 2, gy), (X + W + 2, gy), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    o.append(f'<path d="{_poly_d(fg)}" fill="{pat("G")}" stroke="none"/>')
    o.append(f'<path d="{_d([(X - 2, gy), (X + W + 2, gy)], tol=0)}" stroke="#000" stroke-width="1"/>')
    walks = [[(hx + hw * .1, gy), (hx + hw * .1 - hw * .05, Y + H + 2)] for hx, hw, hh, roof in houses]
    o.append(f'<path d="{_lines_d(walks)}" stroke="#fff" stroke-width="1"/>')
    if not small:
        _sale_sign(o, X + W * .58, gy + H * .07, max(5., W * .035))
    # the balloon, lifting off over the left of the street
    r = min(W * .16, H * .2)
    bx, by = X + W * .22, Y + H * .27
    if small:
        r = min(W * .2, H * .26)
        bx, by = X + W * .2, Y + H * .32
    _balloon(o, bx, by, r, k, rng, pennant=not small)
    body = "".join(o)
    cid = C._uid("mk", X, Y, W, H)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ---------------------------------------------------------------------------------------------
# the tape: a climbing candlestick chart cut into the pedestal tablet, a ticker on the ribbon
# ---------------------------------------------------------------------------------------------

def _candles(tx, ty, tw, th, seed):
    rng = random.Random(seed)
    o = []
    o.append(f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z" fill="{pat("L")}" stroke="none"/>')
    n = max(8, int(tw / 15))
    step = (tw - 8) / n
    vals = [0.]
    for i in range(n):
        vals.append(vals[-1] + rng.gauss(.45, 1.))
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pad = 2

    def Y(v):
        return ty + th - pad - (v - lo) / span * (th - 2 * pad - 1)
    wicks, whites, blacks = [], [], []
    for i in range(n):
        a, b = vals[i], vals[i + 1]
        x = tx + 4 + step * (i + .5)
        top, bot = max(a, b) + rng.uniform(.2, .7), min(a, b) - rng.uniform(.2, .7)
        wicks.append([(x, max(ty + 2, Y(top))), (x, min(ty + th - 2, Y(bot)))])
        bw = max(2., step * .6)
        y0, y1 = Y(max(a, b)), Y(min(a, b))
        if y1 - y0 < 1:
            y1 = y0 + 1
        rect = [(x - bw / 2, y0), (x + bw / 2, y0), (x + bw / 2, y1), (x - bw / 2, y1)]
        (whites if b >= a else blacks).append(rect)
    o.append(f'<path d="{_lines_d(wicks)}" stroke="#000" stroke-width=".5"/>')
    if whites:
        o.append(f'<path d="{"".join(_poly_d(r) for r in whites)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    if blacks:
        o.append(f'<path d="{"".join(_poly_d(r) for r in blacks)}" fill="#000" stroke="none"/>')
    return "".join(o)


def _ribbon_face(centre, h, seed):
    R = C._Rib(centre, [h / 2] * len(centre), [h / 2] * len(centre))
    face = R.outline()
    rng = random.Random(seed)
    o = [f'<path d="{_lines_d([q for q in [R.at(i / 60, .5) for i in range(61)]] and [[R.at(i / 60, s) for i in range(61)] for s in (-.3, .1, .5)], .2)}" stroke="#000" stroke-width=".5"/>']
    # ticker: a rising zigzag across the face, with an arrowhead at its end
    pts = []
    v = -.5
    n = 26
    for i in range(n + 1):
        u = .08 + .84 * i / n
        v = max(-.55, min(.55, v + rng.uniform(-.35, .3) + .045))
        pts.append(R.at(u, -v))
    o.append(f'<path d="{_d(pts, tol=0)}" stroke="#000" stroke-width="1.5"/>')
    e, e2 = pts[-1], pts[-2]
    a = math.atan2(e[1] - e2[1], e[0] - e2[0])
    s = h * .35
    head = [(e[0] + math.cos(a) * s, e[1] + math.sin(a) * s),
            (e[0] + math.cos(a + 2.4) * s * .8, e[1] + math.sin(a + 2.4) * s * .8),
            (e[0] + math.cos(a - 2.4) * s * .8, e[1] + math.sin(a - 2.4) * s * .8)]
    o.append(f'<path d="{_poly_d(head)}" fill="#000" stroke="none"/>')
    return "".join(o)


# ---------------------------------------------------------------------------------------------
# layouts (from the house frame_plate, with the field filled edge to edge)
# ---------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    inner = C._ell_pts(cx, cy, rx - 2, ry - 2, 64)
    o.append(_scene(cx - rx, cy - ry, rx * 2, ry * 2, _d(inner, True, 0), ctx, small=True))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _field(c_svg_args):
    cx, cy, cw, ch = c_svg_args
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return (cx - a, cy - b, 2 * a, 2 * b)


def _layout_medium(w, h, seed, ctx, density=1.):
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
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    X, Y, W, H = _field((cx, cy, cw, gh + 4))
    o.append(_scene(X, Y, W, H, inner_d, ctx, small=H < 110))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx, density=1.):
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
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
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
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    X, Y, W, H = _field((cx, cy, cw, ch))
    o.append(_scene(X, Y, W, H, inner_d, ctx))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_ribbon_face(centre, bh, _seed(ctx)))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    kb = max(5, min(10, ped_h * .11))
    slab = ped_h * .42
    fy0 = py + kb + slab * .22
    fh0 = slab - slab * .22
    cy0, ch0 = fy0 + 2.5, fh0 - 5
    o.append(f'<path d="M{_n(tx)},{_n(cy0)}h{_n(tw)}v{_n(ch0)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(tx + .5)},{_n(cy0 + .5)}h{_n(tw - 1)}l-1.5,1.5h{_n(-(tw - 4))}v{_n(ch0 - 4)}l-1.5,1.5z" fill="#000" stroke="none"/>')
    o.append(_candles(tx + 1, cy0 + 1, tw - 2, ch0 - 1, _seed(ctx)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = _seed(ctx)
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
