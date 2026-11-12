"""delights-04 "Good news / Faith in humanity": US Highway 101 turned 100 (finished 11 Nov 1926)
and a woman was pulled from the high surf at Secret Beach on the south Oregon coast.

The plate: the Oregon coast cut in bulino inside the house cartouche. Highway 101 runs along
a forested headland and leaps a gorge on a McCullough concrete arch; Secret Beach's sea stacks
and natural arch stand in the swell; a life ring floats by a swimmer's raised arm; and the
foreground breaker curls over into an acanthus volute whose foam spray is acanthus fingers (the
sea grown into the ornament). A US 101 shield crowns the cartouche; the tall plate letters the
banner HIGHWAY 101 and the pedestal tablet 1926 - 2026.
Easter egg: a tiny great blue heron (Sauvie Island) standing on top of the tallest sea stack.
"""
import sys
import math
import random
import engraving_codex as C

PI, TAU = math.pi, 2 * math.pi
_n, _d = C._n, C._d


# ----------------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------------

def _runs(y, x0, x1, keep, step=1.):
    """Horizontal runs at y between x0..x1 where keep(x) is true."""
    out, a, b = [], None, None
    x = x0
    while x <= x1:
        if keep(x):
            if a is None:
                a = x
            b = x
        else:
            if a is not None and b - a > .5:
                out.append([(a, y), (b, y)])
            a = None
        x += step
    if a is not None and b - a > .5:
        out.append([(a, y), (b, y)])
    return out


def _clip_y(segs, ylo, yhi):
    out = []
    for (ax, ay), (bx, by) in segs:
        if ay > by:
            ax, ay, bx, by = bx, by, ax, ay
        if by < ylo or ay > yhi:
            continue
        if by - ay < 1e-6:
            out.append([(ax, ay), (bx, by)])
            continue
        t0 = max(0., (ylo - ay) / (by - ay))
        t1 = min(1., (yhi - ay) / (by - ay))
        if t1 > t0:
            out.append([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)])
    return out


def _clip_x(segs, xlo, xhi):
    out = []
    for (ax, ay), (bx, by) in segs:
        if ax > bx:
            ax, ay, bx, by = bx, by, ax, ay
        if bx < xlo or ax > xhi:
            continue
        if bx - ax < 1e-6:
            out.append([(ax, ay), (bx, by)])
            continue
        t0 = max(0., (xlo - ax) / (bx - ax))
        t1 = min(1., (xhi - ax) / (bx - ax))
        if t1 > t0:
            out.append([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)])
    return out


def _poly_y(prof, x):
    """y of a left-to-right profile polyline at x."""
    for i in range(len(prof) - 1):
        (ax, ay), (bx, by) = prof[i], prof[i + 1]
        if ax <= x <= bx and bx > ax:
            return ay + (by - ay) * (x - ax) / (bx - ax)
    return None


def _offset(pl, d):
    """Polyline pl offset by d px along its left normal."""
    out = []
    n = len(pl)
    for i in range(n):
        a, b = pl[max(0, i - 1)], pl[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        out.append((pl[i][0] - ty / L * d, pl[i][1] + tx / L * d))
    return out


# ----------------------------------------------------------------------------------------------
# a single-stroke engraver's alphabet (grid 0..4 wide, 0..6 tall, y down) for path lettering
# ----------------------------------------------------------------------------------------------

_GLYPH = {
    "0": [[(2, 0), (.6, .8), (0, 3), (.6, 5.2), (2, 6), (3.4, 5.2), (4, 3), (3.4, .8), (2, 0)]],
    "1": [[(1, 1.2), (2.4, 0), (2.4, 6)], [(1, 6), (3.8, 6)]],
    "2": [[(.2, 1.3), (1, .2), (2.4, 0), (3.6, .8), (3.7, 2.2), (2.6, 3.6), (0, 6), (4, 6)]],
    "6": [[(3.5, .6), (2.2, 0), (.8, .7), (.1, 2.6), (.2, 4.6), (1, 5.8), (2.4, 6), (3.6, 5.2), (3.8, 4), (3, 3), (1.8, 2.8), (.4, 3.6)]],
    "9": [[(3.6, 2.4), (2.6, 3.2), (1.2, 3.1), (.3, 2.2), (.4, .9), (1.6, 0), (2.9, .2), (3.8, 1.4), (3.8, 3.6), (3.1, 5.4), (1.8, 6), (.6, 5.4)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "G": [[(3.8, 1), (2.6, 0), (1.2, .2), (.2, 1.6), (0, 3), (.3, 4.6), (1.4, 5.9), (2.8, 6), (4, 5), (4, 3.4), (2.4, 3.4)]],
    "W": [[(0, 0), (1, 6), (2, 2), (3, 6), (4, 0)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "U": [[(0, 0), (0, 4.4), (.8, 5.7), (2, 6), (3.2, 5.7), (4, 4.4), (4, 0)]],
    "S": [[(3.7, .9), (2.6, 0), (1.2, .1), (.3, 1), (.5, 2.3), (2, 3), (3.5, 3.7), (3.8, 5), (2.8, 5.9), (1.2, 6), (.2, 5.1)]],
    "-": [[(.6, 3.2), (3.4, 3.2)]],
    " ": [],
}


def _letter_along(text, centre, size, gap=1.25):
    """Lettering laid along a centre polyline (left to right), letters `size` px tall."""
    s = size / 6
    adv = [(4 + gap) * s if ch != " " else 3 * s for ch in text]
    total = sum(adv) - gap * s
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    mid = S[-1] / 2

    def at(d):
        for i in range(1, len(S)):
            if S[i] >= d:
                t = (d - S[i - 1]) / ((S[i] - S[i - 1]) or 1)
                a, b = centre[i - 1], centre[i]
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
        a, b = centre[-2], centre[-1]
        return b, math.atan2(b[1] - a[1], b[0] - a[0])

    out = []
    d = mid - total / 2
    for ch, ad in zip(text, adv):
        (px, py), ang = at(d + 2 * s)
        ca, sa = math.cos(ang), math.sin(ang)
        for stroke in _GLYPH.get(ch, []):
            out.append([(px + ((gx - 2) * s) * ca - ((gy - 3) * s) * sa, py + ((gx - 2) * s) * sa + ((gy - 3) * s) * ca)
                        for gx, gy in stroke])
        d += ad
    return out


def _letters(text, cx, cy, size, gap=1.25):
    s = size / 6
    w = sum((4 + gap) * s if ch != " " else 3 * s for ch in text)
    return _letter_along(text, [(cx - w, cy), (cx + w, cy)], size, gap)


def _stroke_path(pls, w):
    return (f'<path d="{"".join(_d(p, tol=0) for p in pls)}" fill="none" stroke="#000" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# ----------------------------------------------------------------------------------------------
# the US 101 route shield (drawn, never lettered)
# ----------------------------------------------------------------------------------------------

def _shield_pts(cx, cy, s):
    """US route shield outline, s = half width."""
    pts = [(-1, -.86), (-.62, -.86), (-.5, -1.0), (.5, -1.0), (.62, -.86), (1, -.86)]
    right = []
    for i in range(1, 14):
        t = i / 14
        right.append((1 + .06 * math.sin(PI * t) - t ** 2.4, -.86 + t * 1.98))
    pts += right + [(0, 1.12)] + [(-x, y) for x, y in right[::-1]]
    return [(cx + x * s, cy + y * s) for x, y in pts]


def shield_101(cx, cy, s):
    o = []
    outer = _shield_pts(cx, cy, s)
    inner = _shield_pts(cx, cy + s * .03, s * .8)
    o.append(f'<path d="{_d(outer, True, 0)}" fill="#fff" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_d(outer, True, 0)}{_d(inner[::-1], True, 0)}" fill="{C.pat("K")}" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(inner, True, 0)}" fill="{C.pat("L")}" stroke="#000" stroke-width="1"/>')
    o.append(_stroke_path(_letters("US", cx, cy - s * .43, s * .34, 1.8), 1))
    o.append(_stroke_path(_letters("101", cx, cy + s * .2, s * .6, 1.1), 1.5))
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# figures
# ----------------------------------------------------------------------------------------------

def _conifer(cv, x, base, hgt):
    """A small black fir: dense 1 px strokes fanned from the apex."""
    w = hgt * .36
    k = max(3, int(w * 2.2))
    cv.line([[(x, base - hgt), (x - w + 2 * w * i / k, base)] for i in range(k + 1)])
    cv.line([(x, base - hgt - .8), (x, base + 1)])


def _heron(cv, x, y, s):
    """Great blue heron standing, feet at (x, y), s ~ height px. The Easter egg."""
    P = lambda a, b: (x + a * s, y + b * s)
    body = [P(-.3, -.32), P(-.12, -.5), P(.1, -.55), P(.24, -.48), P(.12, -.38), P(-.1, -.34)]
    cv.obj([body], 1.)
    cv.hair([P(-.08, -.46), P(.14, -.48)])
    cv.heavy([P(.18, -.52), P(.26, -.68), P(.17, -.8), P(.22, -.94), P(.3, -.96)])   # S-neck
    cv.line([P(.3, -.96), P(.55, -.92)])                                               # dagger bill
    cv.hair([P(.2, -.97), P(.04, -.92)])                                               # plume
    cv.line([P(-.02, -.36), P(-.04, 0)])
    cv.line([P(.06, -.37), P(.09, 0)])


def _life_ring(cv, cx, cy, rx):
    ry = rx * .45
    cv.obj([C._ell_pts(cx, cy, rx, ry, 28)], 1.)
    hole = C._ell_pts(cx, cy, rx * .48, ry * .42, 18)
    cv.line(hole + [hole[0]])
    cv.hair(C.hatch_poly(hole, 0, 1.5))
    for a0 in (.35, 1.95, 3.5, 5.1):  # the four bands, cut solid
        f = 0.
        while f < .45:
            a = a0 + f
            cv.line([(cx + rx * .52 * math.cos(a), cy + ry * .46 * math.sin(a)), (cx + rx * .96 * math.cos(a), cy + ry * .94 * math.sin(a))])
            f += .07
    for a in (0.9, 2.6, 4.2, 5.8):  # grab line
        cv.hair([(cx + rx * math.cos(a), cy + ry * math.sin(a)),
                 (cx + rx * 1.14 * math.cos(a + .25), cy + ry * 1.3 * math.sin(a + .25)),
                 (cx + rx * math.cos(a + .5), cy + ry * math.sin(a + .5))])


def _swimmer(cv, x, y, s):
    """A head and one arm raised out of the water, reaching for the ring."""
    head = C._ell_pts(x, y - s * .3, s * .3, s * .32, 14)
    cv.obj([head], 1.)
    cv.line(_clip_y(C.hatch_poly(head, 0, 1.), y - s * .7, y - s * .36))  # wet hair
    cv.heavy([(x - s * .2, y - s * .05), (x - s * .5, y - s * .7), (x - s * .6, y - s * 1.25)])
    cv.line([(x - s * .6, y - s * 1.25), (x - s * .75, y - s * 1.35)])
    for r in (s * .6, s * 1.):
        cv.line(C._ell_pts(x, y, r, r * .3, 18, PI * .05, PI * .95))


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            c = not c
    return c


def _clip_in(pls, poly, step=1.2):
    """Keep only the parts of polylines inside poly."""
    out = []
    for pl in pls:
        run = []
        for i in range(len(pl)):
            pts = [pl[i]]
            if i + 1 < len(pl):
                (ax, ay), (bx, by) = pl[i], pl[i + 1]
                k = int(math.hypot(bx - ax, by - ay) / step)
                pts += [(ax + (bx - ax) * j / (k + 1), ay + (by - ay) * j / (k + 1)) for j in range(1, k + 1)]
            for p in pts:
                if _inside(poly, p[0], p[1]):
                    run.append(p)
                else:
                    if len(run) > 1:
                        out.append(run)
                    run = []
        if len(run) > 1:
            out.append(run)
    return out


def _wave(cv, cx, cy, r, sea_y, X0, X1, Ybot, rng, claws=5, tb=1.0):
    """A breaker rolling in from the left and curling over to the right into a volute with a
    drilled eye, carved like an acanthus stem: lines along its form, packed and black on the
    hollow side, white on the lit back; its lip breaks into curling acanthus claws of foam."""
    tail = 2.4
    sp = C.volute_spine(cx, cy, r, 195, 1.3, False, tail, tb, .12)
    n = len(sp)
    S = [0.]
    for k in range(1, n):
        S.append(S[-1] + math.hypot(sp[k][0] - sp[k - 1][0], sp[k][1] - sp[k - 1][1]))
    tot = S[-1]
    u_sp = (tail * r) / tot
    Wd = [max(.8, r * .5 * (1 - S[k] / tot) ** .85 * (.04 + .96 * C._smooth(0, 1, S[k] / tot / u_sp))) for k in range(n)]
    i = n - n // 4
    a, b = sp[i - 1], sp[i + 1]
    ins = 1 if (-(b[1] - a[1])) * (cx - sp[i][0]) + (b[0] - a[0]) * (cy - sp[i][1]) > 0 else -1
    R = C._Rib(sp, Wd, Wd)
    # the water body: under the back of the wave and the falling lip, down to the foot
    ks = [k for k in range(n) if S[k] / tot <= u_sp + (1 - u_sp) * .42]
    back = [R.at(k / (n - 1), -ins) for k in ks]
    lip = back[-1]
    sea_y = back[0][1]
    body = [(X0, Ybot), (X0, back[0][1] + 1.5)] + back + [(lip[0] + r * .3, lip[1] + r * .2), (X1, lip[1] + r * .4), (X1, Ybot), (X0, Ybot)]
    cv.obj([body], 0)
    swell = [(X0, back[0][1] + 1.5)] + back
    lines = []
    d, k = 1.2, 0
    while d < (Ybot - cy) + r * 2:
        lines.append([(x, y + d) for x, y in swell])
        k += 1
        d += 1.5 if k < 10 else 2
    cv.hair(_clip_in(lines, body))
    cv.hair(_clip_y(C.hatch_poly(body, -35, 2), cy + r * .9, Ybot + 2))
    # the hollow inside the curl: dark, cross-cut
    hol = C._ell_pts(cx + r * .05, cy + r * .2, r * .62, r * .5, 30)
    cv.obj([hol], 0)
    cv.line(C.hatch_poly(hol, 0, 1.5))
    cv.hair(C.hatch_poly(hol, 70, 2))
    # the curling crest itself
    c = ins
    cv.obj([R.outline()], 1.)
    cv.hair(C._fill_lines(R, .04 * c, .98 * c, 1.5, .0, 1., 4))
    cv.hair(C._fill_lines(R, -.15 * c, -.65 * c, 2.5, .05, .9, 2))
    C._shadow(cv, R, c, r * .12, .1, .97)
    ex, ey = sp[-1]
    cv.obj([C._ell_pts(ex, ey, 2.4, 2.4, 14)], 0)
    q = 1.8
    while q > .3:
        cv.line(C._ell_pts(ex, ey, q, q, 10))
        q -= .8
    # foam claws along the lip, each a small acanthus finger reaching forward and rolling under
    for j in range(claws):
        u = u_sp + (1 - u_sp) * (.03 + .4 * j / max(1, claws - 1))
        kk = max(1, min(n - 2, next(k for k in range(n) if S[k] / tot >= u)))
        a, b = sp[kk - 1], sp[kk + 1]
        ta = math.atan2(b[1] - a[1], b[0] - a[0])
        p = R.at(kk / (n - 1), -ins * .6)
        L = r * (.5 + .3 * math.sin(PI * j / max(1, claws - 1))) * rng.uniform(.9, 1.1)
        C._finger(cv, p[0], p[1], ta - ins * .5, L, L * .17, ins * 1.1, ins * 3.2, .8)
    return sp


# ----------------------------------------------------------------------------------------------
# the vignette: Highway 101 above Secret Beach at dawn
# ----------------------------------------------------------------------------------------------

def _stack(cv, rr, xc, wb, wt, top, base, arch=None):
    """A sea stack: a tapering, weathered column of basalt with a rounded, grassy crown."""
    n = 12
    L, Rr = [], []
    for i in range(n + 1):
        t = i / n
        half = wb / 2 * (1 - t) ** .7 + wt / 2 * (1 - (1 - t) ** .7)
        wob = rr.uniform(-.6, .6) + .9 * math.sin(t * 9 + xc)
        L.append((xc - half + wob, base - (base - top) * t))
        Rr.append((xc + half + wob * .7, base - (base - top) * t))
    crown = [(xc - wt / 2 + wt * u / 8, top - wt * .22 * math.sin(PI * u / 8) ** .6 - rr.uniform(0, 1.2)) for u in range(1, 8)]
    poly = L + crown + Rr[::-1]
    if arch:
        hx0, hx1, htop = arch
        poly += [(hx0 + (hx1 - hx0) * (.5 + .5 * math.cos(PI * u / 16)), base - (base - htop) * math.sin(PI * u / 16) ** .7) for u in range(17)]
    cv.obj([poly], 1.)
    x0, x1 = xc - wb / 2, xc + wb / 2
    cv.hair(C.hatch_poly(poly, 84, 2.))
    cv.line(_clip_x(C.hatch_poly(poly, 0, 1.5), x0 - 3, xc - wb * .1))       # shadow side, away from the sun
    cv.hair(_clip_x(C.hatch_poly(poly, 30, 2), x0 - 3, xc + wb * .15))
    cv.hair(crown)
    cv.hair(_clip_in([[(x0 - 2, top + (base - top) * f + rr.uniform(-1, 1)), (x1 + 2, top + (base - top) * f + rr.uniform(-1, 1))]
                      for f in (.25, .45, .62, .8)], poly))
    for k in range(3):  # surf breaking at the foot
        cv.line([(x0 - 3 - k * 2 + u, base + 1 + k * 1.6 - .8 * math.sin(u * .9)) for u in range(0, int(wb + 6 + k * 4), 2)])
    return crown


def _cloud(cv, ccx, ccy, cw, ch, rng):
    """A cumulus bank: white puffs over ruled sky, a contour on the lit top, hatched underside."""
    bumps = [(ccx + cw * rng.uniform(-.38, .38), ch * rng.uniform(.5, 1.)) for _ in range(4)]
    bumps.append((ccx, ch))
    top = []
    for u in range(25):
        x = ccx - cw / 2 + cw * u / 24
        hgt = max(b * max(0., 1 - ((x - bx) / (cw * .22)) ** 2) ** .5 for bx, b in bumps)
        hgt = max(hgt, ch * .18 * math.sin(PI * u / 24))
        top.append((x, ccy - hgt))
    cl = top + [(ccx + cw / 2, ccy + ch * .12), (ccx - cw / 2, ccy + ch * .12)]
    cv.obj([cl], 0)
    cv.line(top)
    cv.hair(_offset(top, -1.2))
    cv.hair(C.hatch_poly(cl, 0, 3, .4))
    cv.hair(_clip_y(C.hatch_poly(cl, 0, 3, 1.9), ccy - ch * .3, ccy + ch))
    cv.hair(_clip_y(C.hatch_poly(cl, -30, 2), ccy - ch * .05, ccy + ch))


def coast_scene(X, Y, W, H, seed=0, detail=1.):
    """The Oregon coast at dawn inside the box (X, Y, W, H); returns SVG (clip it to the field)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    hz = Y + H * .44
    sx, sy = X + W * (.9 + .02 * rng.random()), hz - H * .04
    sr = min(W, H) * .085

    # sky: ruled, dense at the zenith, the light rays opening from the sun
    sky = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, hz + 1), (X - 2, hz + 1)]
    cv.obj([sky], 0)
    nr = 30

    def dark_ray(x, y):
        a = math.atan2(y - sy, x - sx)
        return (a / PI * nr) % 2. >= 1.

    y, i = Y - 1, 0
    while y < hz:
        t = (y - Y) / (hz - Y)
        if t < .25 or i % 2 == 0:
            cv.hair([(X - 2, y), (X + W + 2, y)])
        else:
            cv.hair(_runs(y, X - 2, X + W + 2, lambda x, yy=y: dark_ray(x, yy)))
        y += 1.5
        i += 1
    for j in range(2):
        _cloud(cv, X + W * (.42 + .36 * j + rng.uniform(-.03, .03)), Y + H * (.17 + .07 * j), W * (.28 - .06 * j), H * .09, rng)
    for j in range(4):  # gulls
        gx = X + W * rng.uniform(.4, .9)
        gy = Y + H * rng.uniform(.25, .36)
        g = 1.8 + rng.random() * 1.4
        cv.line([(gx - g, gy - g * .2), (gx - g * .45, gy - g * .55), (gx, gy)])
        cv.line([(gx, gy), (gx + g * .45, gy - g * .55), (gx + g, gy - g * .2)])

    # the sun, half risen
    disc = C._ell_pts(sx, sy, sr, sr, 40, PI, TAU)
    cv.obj([disc], 1.5)
    cv.hair(C.hatch_poly(disc, 0, 3, 1.75))
    cv.hair(C._ell_pts(sx, sy, sr * 1.3, sr * 1.3, 40, PI, TAU))

    # the far headland across the water
    fx0 = X + W * .74
    far = [(fx0, hz)] + [(fx0 + (X + W + 4 - fx0) * (i / 16),
                          hz - H * .06 * math.sin(PI * min(1, i / 16 * 1.3) * .5) ** 1.4 - H * .01 * math.sin(i / 16 * 9))
                         for i in range(1, 17)] + [(X + W + 4, hz + 1)]
    cv.obj([far], .5)
    cv.hair(C.hatch_poly(far, 0, 1.5))

    # the sea: ruled water, tight at the horizon, opening toward us, broken by the sun's glitter
    sea = [(X - 2, hz), (X + W + 2, hz), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([sea], 0)
    cv.line([(X - 2, hz), (X + W + 2, hz)])
    y, k = hz + 1.5, 0
    while y < Y + H + 2:
        t = (y - hz) / (Y + H - hz)
        amp = .3 + 1.1 * t
        per = 9 + 16 * t
        ph = rng.random() * TAU
        glit = sr * (.8 + 2.2 * t)
        seg, segs = [], []
        xx = X - 2
        while xx <= X + W + 2:
            p = (xx, y + amp * math.sin(xx / per * TAU + ph))
            if abs(xx - sx) < glit and ((xx * .37 + k * 1.7) % 4.) < 1.6:
                if len(seg) > 1:
                    segs.append(seg)
                seg = []
            else:
                seg.append(p)
            xx += 1.5
        if len(seg) > 1:
            segs.append(seg)
        cv.hair(segs)
        y += 1.5 if t < .35 else 2.
        k += 1

    # Secret Beach: sea stacks and the natural arch standing in the swell
    base = hz + H * .13
    T1 = _stack(cv, rng, X + W * .58, W * .085, W * .05, hz - H * .2, base)
    _stack(cv, rng, X + W * .655, W * .06, W * .04, hz - H * .085, base + 1)
    _stack(cv, rng, X + W * .5, W * .045, W * .03, hz - H * .03, base - H * .02)
    _stack(cv, rng, X + W * .8, W * .16, W * .12, hz - H * .1, base + H * .025, (X + W * .765, X + W * .835, hz + H * .005))
    tyy = min(p[1] for p in T1) + 1.
    _heron(cv, X + W * .59, tyy, max(9., H * .07))            # Easter egg: Parker's heron
    _conifer(cv, X + W * .567, tyy + 1.5, H * .04)

    # the near headland: firs on the ridge, a gorge, Highway 101 benched into the cliff
    hx1 = X + W * .52
    g0, g1 = X + W * .17, X + W * .25
    ridge = []
    for i in range(41):
        t = i / 40
        xx = X - 3 + (hx1 + 3 - X) * t
        yy = Y + H * (.27 + .02 * math.sin(t * 7 + 1)) + (hz + H * .02 - Y - H * .27) * max(0, (t - .55) / .45) ** 1.5
        ridge.append((xx, yy))
    shore = lambda x: hz + H * (.27 - .2 * max(0., (x - X) / (hx1 - X)) ** 1.3)
    sh_pts = [(X - 3 + (hx1 + 6 - X) * u / 20, shore(X - 3 + (hx1 + 6 - X) * u / 20)) for u in range(21)]
    gtop = _poly_y(ridge, g0) + H * .045
    gorge = [(g0 - 1, gtop - H * .02), (g1 + 1, gtop - H * .02), (g1 + 4, shore(g1)), (g0 - 4, shore(g0))]
    cv.obj([gorge], 0)
    cv.line(C.hatch_poly(gorge, 0, 1.5))
    cv.hair(C.hatch_poly(gorge, 90, 2))
    gx = (g0 + g1) / 2
    cv.hair([[(gx - 1.2 + j * .8, gtop + H * .1), (gx - 1.5 + j * 1., shore(gx))] for j in range(4)])
    left_poly = [p for p in ridge if p[0] <= g0] + [(g0, gtop)] + [p for p in sh_pts if p[0] <= g0][::-1]
    right_poly = ([(g1, gtop)] + [p for p in ridge if p[0] >= g1] + [(hx1 + 6, shore(hx1 + 6))] +
                  [p for p in sh_pts if p[0] >= g1][::-1])
    for poly in (left_poly, right_poly):
        cv.obj([poly], 1.)
        top_y = min(p[1] for p in poly)
        cv.hair(C.hatch_poly(poly, 78, 2))
        cv.hair(_clip_y(C.hatch_poly(poly, -15, 2), top_y + H * .09, hz + H))
        cv.line(_clip_y(C.hatch_poly(poly, 0, 1.5), top_y + H * .18, hz + H))
        xs = [p[0] for p in poly]
        for j in range(4):
            yy = ridge[0][1] + H * (.08 + .045 * j)
            cv.line(_clip_x([[(min(xs), yy + rng.uniform(-1, 1)), (max(xs), yy + rng.uniform(-1.5, 1.5))]], min(xs) + 2, max(xs) - 4))
    # surf along the foot of the cliffs
    for kk in range(3):
        cv.line([(x, y + 1.2 + kk * 1.7 + .6 * math.sin(x * .8 + kk)) for x, y in sh_pts])
    xx = X - 1
    while xx < hx1 - W * .02:
        if not (g0 - 3 < xx < g1 + 3):
            ry = _poly_y(ridge, xx)
            if ry is not None:
                _conifer(cv, xx, ry + 2, H * rng.uniform(.05, .08) * (1 if xx < hx1 - W * .12 else .7))
        xx += 3. + rng.random() * 1.5

    def _ry(x):
        return (_poly_y(ridge, x) or hz) + H * .055

    def road_y(x):
        if g0 - 4 <= x <= g1 + 4:
            a, b = _ry(g0 - 4), _ry(g1 + 4)
            return a + (b - a) * (x - g0 + 4) / (g1 - g0 + 8)
        return _ry(x)

    rp = []
    xx = X - 3
    while xx <= hx1 - W * .04:
        rp.append((xx, road_y(xx)))
        xx += 1.5
    Rd = C._Rib(rp, [2.] * len(rp), [2.] * len(rp))
    cv.obj([Rd.outline()], 1.)
    for c in Rd.contour(0, 0, 1):
        cv.hair([c[j:j + 3] for j in range(0, len(c) - 2, 5)])
    cv.hair(Rd.contour(-.75, 0, 1))
    # the concrete deck arch over the gorge (Conde McCullough's coast bridges)
    ax0, ax1 = g0 - 4, g1 + 4
    span = ax1 - ax0
    by0, by1 = road_y(ax0), road_y(ax1)
    rise = min(H * .1, span * .55)
    deck = [(ax0 + span * u / 24, by0 + 2. + (by1 - by0) * u / 24) for u in range(25)]
    arc = [(ax0 + span * u / 24, by0 + 4 + rise - rise * math.sin(PI * u / 24) ** .7 + (by1 - by0) * u / 24) for u in range(25)]
    cv.obj([[(p[0], p[1] - 4.4) for p in deck] + arc[::-1]], 1.)
    cv.heavy(arc)
    cv.line([(p[0], p[1] + 1.2) for p in arc])
    cv.heavy(deck)
    cv.hair([(p[0], p[1] - 4.4) for p in deck])
    for u in range(1, 24):
        if u % 2 == 0:
            cv.hair([(deck[u][0], deck[u][1] + .6), (arc[u][0], arc[u][1] - .6)])
        cv.hair([(deck[u][0], deck[u][1] - 4.4), (deck[u][0], deck[u][1] - 2.4)])

    # the breaker, curling over into a volute and breaking into acanthus foam
    r = min(W, H) * .15
    _wave(cv, X + W * .74, Y + H * .73, r, Y + H * .93, X - 3, X + W + 3, Y + H + 3,
          random.Random(seed + 7), 5 if detail >= 1 else 4)
    # the rescue, riding the swell: a life ring tossed beside a raised arm
    lr_x, lr_y = X + W * .16, Y + H * .84
    _life_ring(cv, lr_x, lr_y, max(6.5, W * .045))
    _swimmer(cv, lr_x + W * .09, lr_y + 1, max(5., H * .045))

    return cv.svg()


def mini_coast(X, Y, W, H, seed=0):
    """The medallion scene for the short band: dawn sun, sea stack with the heron, ruled sea."""
    cv = C.Canvas()
    hz = Y + H * .58
    sx, sy, sr = X + W * .64, hz, H * .2
    cv.obj([[(X - 4, Y - 4), (X + W + 4, Y - 4), (X + W + 4, hz), (X - 4, hz)]], 0)
    y = Y - 4
    while y < hz:
        cv.hair([(X - 4, y), (X + W + 4, y)])
        y += 1.5 if (y - Y) < (hz - Y) * .5 else 2
    disc = C._ell_pts(sx, sy, sr, sr, 30, PI, TAU)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 3, 1.75))
    cv.obj([[(X - 4, hz), (X + W + 4, hz), (X + W + 4, Y + H + 4), (X - 4, Y + H + 4)]], 0)
    cv.line([(X - 4, hz), (X + W + 4, hz)])
    y = hz + 1.5
    while y < Y + H + 4:
        cv.hair([(xx, y + .5 * math.sin(xx * .5 + y)) for xx in range(int(X - 4), int(X + W + 5), 2)])
        y += 2
    poly = [(X + W * .2, hz + 3), (X + W * .22, hz - H * .3), (X + W * .27, hz - H * .4), (X + W * .33, hz - H * .37), (X + W * .36, hz + 3)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 80, 1.5))
    cv.line(_clip_x(C.hatch_poly(poly, 0, 1.5), 0, X + W * .27))
    _heron(cv, X + W * .29, hz - H * .39, H * .22)
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts (the house frame, refitted for this page)
# ----------------------------------------------------------------------------------------------

def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def _cartouche_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a + .6, b + .6)


def _layout_band(w, h, seed):
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
    fld = C._ell_pts(cx, cy, rx - 1.6, ry - 1.6, 64)
    X, Y, W, H = _bbox(fld)
    o.append(_field_clip(C._uid("bf", w, h, seed), _d(fld, True, 0), mini_coast(X, Y, W, H, seed)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.5)
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
                   max_n=int(9 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fld = _cartouche_field(cx, cy, cw, gh + 4)
    X, Y, W, H = _bbox(fld)
    o.append(_field_clip(C._uid("mf", w, h, seed), _d(fld, True, 0), coast_scene(X, Y, W, H, seed, 1 if h > 150 else .5)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    if h >= 150:  # the US 101 shield hangs at the head of the cartouche
        s = min(13., gh * .065)
        o.append(shield_101(cx, gy0 + s * 1.05, s))
    return "".join(o)


def _layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="{C.pat("L")}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .54, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .16, ph * .23)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .19)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(7 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fld = _cartouche_field(cx, cy, cw, ch)
    X, Y, W, H = _bbox(fld)
    o.append(_field_clip(C._uid("tf", w, h, seed), _d(fld, True, 0), coast_scene(X, Y, W, H, seed, 1.)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    s = min(15., ch * .06)
    o.append(shield_101(cx, cy - ch / 2 + s * .2, s))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_stroke_path(_letter_along("HIGHWAY 101", centre, bh * .52, 1.6), 1))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 3)},{_n(ty + 3)}h{_n(tw - 5)}v{_n(th - 5)}h{_n(-tw + 5)}z" fill="{C.pat("L")}" stroke="none"/>')
    o.append(_stroke_path(_letters("1926 - 2026", w / 2, ty + th / 2 + .5, min(th * .5, 11), 1.8), 1.5))
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
    seed = sum(map(ord, ctx.get("date", ""))) + 404
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
