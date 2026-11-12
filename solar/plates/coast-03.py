"""coast-03 "This week at the coast" (Warrenton tides, storm, 24 ft surf, sneaker waves).
A storm-coast vignette engraved in the house scroll frame: a towering breaker whose crest breaks
into acanthus foam-fingers, rain squalls and a lightning stroke under rolling nimbus, the
Cape Disappointment light on its headland, and the ribs of the wreck of the Peter Iredale on the
Fort Stevens sand. Easter egg: a Sauvie Island heron standing on the wreck's bow stem.
The top moulding is a Vitruvian running-wave (the classical sea ornament) in place of egg-and-dart."""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
_n = C._n


# ------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------

def _poly_d(p):
    return C._d(p, True, .1)


def _dots(pts, w=1.):
    """Round-capped zero-length strokes: engraved stipple dots, one element."""
    if not pts:
        return ""
    d = "".join(f"M{_n(x)},{_n(y)}h0" for x, y in pts)
    return f'<path d="{d}" stroke="#000" stroke-width="{_n(w)}" stroke-linecap="round" fill="none"/>'


def _wave_line(x0, x1, y, amp, freq, ph, step=2.):
    pts = []
    x = x0
    while x <= x1 + .01:
        pts.append((x, y + amp * math.sin(x * freq + ph) + amp * .35 * math.sin(x * freq * 2.3 + ph * 1.7)))
        x += step
    return pts


def _broken(pl, rng, keep=.82, seg=(6, 26)):
    """Break a polyline into dashes with gaps (glints on the water)."""
    out, cur = [], []
    budget = rng.uniform(*seg)
    on = True
    for i in range(1, len(pl)):
        d = math.hypot(pl[i][0] - pl[i - 1][0], pl[i][1] - pl[i - 1][1])
        if on:
            if not cur:
                cur = [pl[i - 1]]
            cur.append(pl[i])
        budget -= d
        if budget <= 0:
            if on and len(cur) > 1:
                out.append(cur)
            cur = []
            on = (not on) if on else True
            budget = rng.uniform(*seg) if on else rng.uniform(1.5, 5) * (1 - keep) * 5
    if on and len(cur) > 1:
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------
# the storm-coast scene, drawn into a box and clipped to the field outline
# ------------------------------------------------------------------------------------------

def _puffs(X, Y, W, H, hy, rng):
    """Billows of the storm: (cx, cy, rx, ry) in paint order (far/high first)."""
    P = []

    def bank(x0, x1, yc, rmin, rmax, rows, dy):
        for row in range(rows):
            x = x0 + rng.uniform(-.3, .3) * rmax
            while x < x1:
                r = rng.uniform(rmin, rmax)
                P.append((x + r, yc + row * dy + rng.uniform(-.3, .3) * r, r * 1.25, r * .85))
                x += r * rng.uniform(1.2, 1.6)
    bank(X - 10, X + W + 10, hy - H * .05, _S[0] * .025, _S[0] * .05, 1, 0)
    bank(X + W * .4, X + W + 10, Y + H * .1, _S[0] * .06, _S[0] * .1, 2, _S[0] * .08)
    bank(X - 10, X + W * .55, Y + H * .05, _S[0] * .07, _S[0] * .12, 2, _S[0] * .1)
    return P


def _sky(cv, X, Y, W, H, hy, rng, puffs):
    """The storm sky engraved the old way: one field of horizontal lines whose weight carries
    the tone; billows are modelled by thickening the lines in their shadowed bellies and cutting
    them away along their sunlit crowns, so the clouds have no outlines at all."""
    def val(x, y):
        t = (y - Y) / max(1., hy - Y)
        v = .55 - .25 * t
        for cx, cy, rx, ry in puffs:
            dx, dy = (x - cx) / rx, (y - cy) / ry
            q = dx * dx + dy * dy
            if q < 1:
                s = dy * .8 + dx * .45
                v = min(1., max(.3, .5 + .6 * s + .2 * q * (dy > 0)))
                if q > .62 and s < -.05:
                    v = 0.
                elif s < -.55:
                    v = .1
        return v

    cv.obj([], 0)
    hair, line, heavy = [], [], []
    y = Y - 6
    while y < hy - .4:
        x = X - 8
        cur, cls = [], None
        while x <= X + W + 8:
            v = val(x, y)
            c = 0 if v < .2 else (1 if v < .6 else (2 if v < .85 else 3))
            if c != cls:
                if cls and len(cur) > 1:
                    (hair, line, heavy)[cls - 1].append(cur)
                cur = [(x, y)] if c else []
                cls = c
            elif c:
                if len(cur) == 1:
                    cur.append((x, y))
                else:
                    cur[-1] = (x, y)
            x += 1.
        if cls and len(cur) > 1:
            (hair, line, heavy)[cls - 1].append(cur)
        y += 1.5
    cv.hair(hair)
    cv.line(line)
    cv.heavy(heavy)
    # rain squalls slanting out of the nimbus
    for (rx, rw) in ((X + W * .42, W * .2), (X + W * .78, W * .1)):
        poly = [(rx, Y + H * .3), (rx + rw, Y + H * .3), (rx + rw - H * .2, hy), (rx - H * .2, hy)]
        cv.hair(C.hatch_poly(poly, 75, 3, rng.random() * 3))


def _bolt(cv, x, y0, y1, rng):
    """A forked lightning stroke, cut white with a black edge so it burns out of the ruled sky."""
    h = y1 - y0
    n = 6
    pts = [(x, y0)]
    xx = x
    for i in range(1, n + 1):
        xx += (h * .13 if i % 2 else -h * .08) + rng.uniform(-.03, .03) * h
        pts.append((xx, y0 + h * i / n + rng.uniform(-.04, .04) * h * (i < n)))
    w0 = max(1.6, h * .07)
    L = [(px - w0 * (1 - .85 * i / n), py) for i, (px, py) in enumerate(pts)]
    R = [(px + w0 * (1 - .85 * i / n) * .7, py) for i, (px, py) in enumerate(pts)]
    cv.obj([L + R[::-1]], 1.)
    # forks
    for j, sgn in ((2, -1), (4, 1)):
        bx, by = pts[j]
        fl = [(bx, by), (bx + sgn * h * .1, by + h * .1), (bx + sgn * h * .06, by + h * .17), (bx + sgn * h * .13, by + h * .26)]
        cv.obj([[(px - .9 * (1 - k / 3), py) for k, (px, py) in enumerate(fl)] + [(px + .9 * (1 - k / 3), py) for k, (px, py) in enumerate(fl)][::-1]], .5)


def _headland(cv, X, Y, W, H, hy, rng):
    """Cape Disappointment: a wooded bluff on the right with the lighthouse and its beams."""
    x0 = X + W * .72
    top = []
    for i in range(25):
        t = i / 24
        xx = x0 + (X + W + 8 - x0) * t
        yy = hy - _S[0] * (.03 + .13 * C._smooth(0, .55, t)) - math.sin(t * 31) * _S[0] * .012 * (t > .3)
        top.append((xx, yy))
    poly = [(x0 - 6, hy + 1)] + top + [(X + W + 8, hy + 1)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 0, 1.5, .3))
    cv.hair(C.hatch_poly(poly, 60, 3, .5, 1.5))
    # spruce along the ridge: fine vertical ticks
    for i in range(4, 25):
        px, py = top[i]
        hgt = _S[0] * .02 + 1
        cv.line([(px, py + 1), (px, py - hgt)])
    # the lighthouse on the bluff's shoulder
    lx, ly = top[9][0], top[9][1] + 1
    th = _S[0] * .13
    tw = max(2.2, th * .2)
    tower = [(lx - tw, ly), (lx - tw * .7, ly - th), (lx + tw * .7, ly - th), (lx + tw, ly)]
    # beams first (behind the tower)
    cv.obj([], 0)
    for a in (-.12, .1):
        for s in (-1, 1):
            ang = PI if s < 0 else 0
            ang += a
            L = W * .16
            cv.hair([(lx + s * tw, ly - th - 2), (lx + s * tw + math.cos(ang) * L * s * s, ly - th - 2 + math.sin(ang) * L)])
    cv.obj([tower], 1.)
    band = [(lx - tw * .87, ly - th * .42), (lx - tw * .8, ly - th * .62), (lx + tw * .8, ly - th * .62), (lx + tw * .87, ly - th * .42)]
    cv.line(C.hatch_poly(band, 0, 1., .2))
    cv.hair([(lx + tw * .35, ly - 1), (lx + tw * .25, ly - th + 1)])
    lamp = [(lx - tw * .6, ly - th), (lx - tw * .6, ly - th - tw * 1.1), (lx, ly - th - tw * 1.8), (lx + tw * .6, ly - th - tw * 1.1), (lx + tw * .6, ly - th)]
    cv.obj([lamp], 1.)
    cv.hair(C.hatch_poly(lamp, 0, 1.5, .5))
    return poly


def _sea(cv, X, Y, W, H, hy, by, rng):
    cv.obj([[(X - 8, hy), (X + W + 8, hy), (X + W + 8, by + 8), (X - 8, by + 8)]], 0)
    y = hy + .8
    i = 0
    while y < by + 6:
        t = (y - hy) / max(1, by - hy)
        amp = .3 + t * 1.6
        pl = _wave_line(X - 8, X + W + 8, y, amp, .09 + .1 * (1 - t), rng.random() * 6, 2. if t > .2 else 3.)
        pieces = _broken(pl, rng, .8, (10 + 30 * (1 - t), 40 + 60 * (1 - t)))
        if t > .55 and i % 3 == 0:
            cv.line(pieces)
        else:
            cv.hair(pieces)
        y += 1.5 + 1.5 * t
        i += 1
    cv.heavy([(X - 8, hy), (X + W + 8, hy)])


def _bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def _breaker(cv, bx, y0, hh, rng, foam=True, ww=None):
    """A plunging breaker in the Hokusai manner, breaking to the right. The long back climbs to
    the crest; the lip throws forward over a black hollow; the concave face runs down and forward
    into the trough. Every water line runs from the trough up over the crest and round the lip,
    sparse and broken on the back (light), crowding to dense on the face and under the curl.
    The crest tears into acanthus foam-claws curling with the wave."""
    R = hh * .32
    ex = 1.25
    cx, cy = bx + hh * 1.0, y0 - hh + R
    ri = R * .42
    tip_th = PI * .3
    rootx = cx - ri * ex
    fbx = cx + R * ex * 1.8

    def line(t, th_end=None, arc_n=36):
        r = R - t * (R - ri)
        b0 = (bx + (fbx - bx) * t, y0)
        lx = cx - r * ex
        c1 = (b0[0] + (lx - b0[0]) * .6 * (1 - t) + (-R * 1.7) * t, y0 - hh * .04 * (1 - t) - R * .15 * t)
        c2 = (lx - hh * .12 * (1 - t) + R * 1.1 * t, cy + (y0 - cy) * .38 * (1 - t) + R * .75 * t)
        back = _bez(b0, c1, c2, (lx, cy), 18)
        th1 = tip_th - t * .35 if th_end is None else th_end
        arc = []
        for i in range(1, arc_n + 1):
            th = PI + (th1 + PI) * i / 36
            rr = r * (1 - .32 * (i / 36) ** 2 * (1 - t * .5))
            arc.append((cx + rr * ex * math.cos(th), cy + rr * math.sin(th)))
        return back + arc

    outer = line(0.)
    full_inner = line(1.)
    inner_arc = full_inner[18:]
    face = full_inner[:19][::-1]              # root -> down and forward to the trough
    tip = outer[-1]
    k = next((i for i, p in enumerate(face) if p[0] >= tip[0] + R * .2), len(face) - 1)
    tube = [inner_arc[-1], tip, face[k]] + face[:k][::-1] + inner_arc[:-1]
    cv.obj([tube], 0)
    cv.line(C.hatch_poly(tube, 70, 1.5, .3))
    cv.hair(C.hatch_poly(tube, -15, 2, .3))
    for i in range(5):
        f = (i + .5) / 5
        p0 = (tip[0] - R * .35 * (1 - f), tip[1] - R * .1 * (1 - f))
        p1 = (p0[0] + R * .12, face[k][1] - (face[k][1] - p0[1]) * .25)
        cv.hair([p0, p1])
    body = outer + [tip] + full_inner[::-1] + [(fbx + 2, y0 + 3), (bx - 4, y0 + 3)]
    cv.obj([body], 1.)
    m = max(8, int((R - ri) / 1.4))
    for j in range(1, m):
        t = j / m
        pl = line(t, tip_th - t * .35 - .05)
        if t < .45:
            pl = _broken(pl, rng, .7, (6 + 20 * t, 18 + 30 * t))
        (cv.line if t > .72 else cv.hair)(pl)
        # extra lines between, running from the trough only as high as the spread allows
        t2 = (j + .5) / m
        pl2 = line(t2, arc_n=0)[:int(18 * (.55 + .3 * t2))]
        if t2 < .45:
            pl2 = _broken(pl2, rng, .7, (6, 20))
        (cv.line if t2 > .8 else cv.hair)(pl2)
    pl0 = line(.5 / m, arc_n=0)[:11]
    cv.hair(_broken(pl0, rng, .7, (6, 20)))
    # foam claws along the crest and lip: a row of long claws, small ones tucked between
    if foam:
        nf = max(5, int(hh / 9))
        for row, (L0, off) in enumerate(((hh * .13, 0.), (hh * .07, .5))):
            for i in range(nf):
                f = .06 + .86 * (i + off) / nf
                idx = min(18 + int(f * 36), len(outer) - 2)
                p, q = outer[idx], outer[idx + 1]
                tang = math.atan2(q[1] - p[1], q[0] - p[0])
                ln = L0 * rng.uniform(.8, 1.2) * (1.15 - .45 * f)
                C._finger(cv, p[0], p[1], tang - (1.2 if row == 0 else .75), ln, ln * (.13 if row == 0 else .11), 1.2, 5.5, 1.)
    return outer, (cx, cy, R)


def _whitecaps(cv, X, Y, W, H, hy, rng, small):
    """Wind-torn crests across the sea: white caps with a dark trough line under each."""
    n = 9 if not small else 5
    for i in range(n):
        t = rng.random() ** .7
        y = hy + 3 + (H * .3) * t
        x = X + W * (.3 + .68 * rng.random())
        s = 4 + 12 * t
        cap = [(x - s, y), (x - s * .4, y - s * .28), (x + s * .1, y - s * .42), (x + s * .5, y - s * .3), (x + s * .3, y - s * .12), (x + s, y)]
        cv.obj([cap], .5)
        cv.heavy([(x - s * 1.2, y + .8), (x + s * 1.1, y + .8)])
        cv.hair([(x - s * .2, y - s * .3), (x + s * .35, y - s * .1)])


def _spray(X, Y, W, H, cx, cy, r, rng, n):
    pts = []
    for _ in range(n):
        a = rng.uniform(-PI, 0.2)
        d = r * rng.random() ** .6
        pts.append((cx + math.cos(a) * d * 1.3, cy + math.sin(a) * d))
    return pts


def _beach(X, Y, W, H, rng, y0f=.86):
    y0 = Y + H * y0f
    top = []
    for i in range(41):
        t = i / 40
        xx = X - 8 + (W + 16) * t
        top.append((xx, y0 - H * .11 * C._smooth(.25, 1, t) + math.sin(t * 19) * 1.2))
    poly = [(X - 8, Y + H + 8)] + top + [(X + W + 8, Y + H + 8)]
    return poly, top


def _wreck(cv, X, Y, W, H, top, rng):
    """The Peter Iredale: the iron ribs of the hull standing out of the sand, bow stem raked
    high, receding along a diagonal."""
    def sand_y(x):
        for i in range(1, len(top)):
            if top[i][0] >= x:
                a, b = top[i - 1], top[i]
                return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
        return top[-1][1]

    bxs = X + W * .66
    n = 7
    ribs = []
    for i in range(n):
        t = i / (n - 1)
        x = bxs + W * .25 * t
        y = sand_y(x) + 2 + H * .05 * (1 - t)
        sc = 1. - .55 * t
        ribs.append((x, y, sc))
    stem_tip = None
    # paint far-to-near
    for i in reversed(range(n)):
        x, y, sc = ribs[i]
        for side in (-1, 1):
            hh = _S[0] * .36 * sc * (1 if side > 0 else .82) * rng.uniform(.8, 1.)
            if i in (2, 4) and side < 0:
                hh *= .45      # broken off
            L = hh
            ang = -PI / 2 + side * .18
            k = lambda u, sd=side: -sd * 2.3 / L * C._smooth(.2, 1, u)
            pts = C._euler(x + side * W * .04 * sc, y, ang, L, k, 18)
            wd = max(1.1, 2.6 * sc)
            Rb = C._Rib(pts, [wd * (1 - .45 * j / 18) for j in range(19)], [wd * (1 - .45 * j / 18) for j in range(19)])
            cv.obj([Rb.outline()], 1.)
            cv.line(Rb.inset(side, lambda u: .9, 0., .98))
            if wd > 1.6:
                cv.hair(Rb.contour(-.2 * side, 0, .98))
        if i < n - 1:
            nx, ny, nsc = ribs[i + 1]
            for hf in (.25, .45):
                cv.hair([(x - W * .04 * sc, y - _S[0] * .36 * sc * hf), (nx - W * .04 * nsc, ny - _S[0] * .36 * nsc * hf)])
    # the bow stem: raked forward, tallest, nearest
    x, y, sc = ribs[0]
    sx, sy = x - W * .05, y + 2
    L = _S[0] * .34
    pts = C._euler(sx, sy, -PI / 2 - .3, L, lambda u: .5 / L, 24)
    wd = 3.2
    Rb = C._Rib(pts, [wd * (1 - .5 * j / 24) for j in range(25)], [wd * (1 - .5 * j / 24) for j in range(25)])
    cv.obj([Rb.outline()], 1.)
    C._shadow(cv, Rb, 1, 2.2, .0, 1.)
    cv.hair(Rb.contour(-.3, 0, 1))
    # rivet line
    cv.obj([], 0)
    stem_tip = pts[-1]
    # stringer: a bent plate running from stem to the first ribs
    pl = [Rb.at(.25, 1), (ribs[1][0], ribs[1][1] - _S[0] * .14), (ribs[3][0], ribs[3][1] - _S[0] * .1)]
    cv.heavy(pl)
    # sand piled at the foot of the wreck, and its shadow
    return stem_tip, sand_y


def _heron(cx, by, s):
    """A small great blue heron, standing, facing left: solid black with a white eye-stripe line."""
    # body
    body = C._ell_pts(cx + s * .5, by - s * 2.4, s * 1.25, s * .7, 16)[:-1]
    body = [(px, py - (s * .25 if px > cx + s * .9 else 0)) for px, py in body]
    neck = [(cx - s * .4, by - s * 2.6), (cx - s * .9, by - s * 3.4), (cx - s * .5, by - s * 4.1),
            (cx - s * .9, by - s * 4.8), (cx - s * .55, by - s * 5.0), (cx - s * .25, by - s * 4.75),
            (cx + s * .0, by - s * 4.0), (cx - s * .2, by - s * 3.3), (cx + s * .2, by - s * 2.6)]
    head = [(cx - s * .95, by - s * 4.75), (cx - s * 2.5, by - s * 4.6), (cx - s * .85, by - s * 4.45)]
    plume = [(cx - s * .3, by - s * 4.95), (cx + s * .9, by - s * 4.7), (cx - s * .2, by - s * 4.8)]
    tail = [(cx + s * 1.4, by - s * 2.6), (cx + s * 2.3, by - s * 1.9), (cx + s * 1.5, by - s * 2.1)]
    d = "".join(_poly_d(p) for p in (body, neck, head, plume, tail))
    legs = f"M{_n(cx + s * .3)},{_n(by - s * 1.8)}L{_n(cx + s * .15)},{_n(by)}M{_n(cx + s * .7)},{_n(by - s * 1.8)}L{_n(cx + s * .75)},{_n(by)}"
    return (f'<path d="{d}{legs}" fill="#fff" stroke="#fff" stroke-width="1.5"/>'
            f'<path d="{d}" fill="#000" stroke="#000" stroke-width=".5"/>'
            f'<path d="{legs}" stroke="#000" stroke-width="1"/>'
            f'<path d="M{_n(cx - s * .55)},{_n(by - s * 4.7)}h{_n(-s * .5)}" stroke="#fff" stroke-width=".5"/>')


_S = [100.]


def _tidepool(cv, x, y, s, rng):
    """Tidepool days: a barnacled rock at the tide line with a sea star and a clam shell on it."""
    rock = []
    for i in range(18):
        a = PI + PI * i / 17
        r = s * (1 + .12 * math.sin(i * 2.3 + 1))
        rock.append((x + r * 1.5 * math.cos(a), y + r * .75 * math.sin(a)))
    rock += [(x + s * 1.5, y + 2), (x - s * 1.5, y + 2)]
    cv.obj([rock], 1.)
    cv.hair(C.hatch_poly(rock, 40, 1.5, .2))
    sh = [(px, py + s * .35) for px, py in rock[:18]] + [(x + s * 1.6, y + 3), (x - s * 1.6, y + 3)]
    cv.line(C.hatch_poly(sh, -40, 1.5, .4))
    # the sea star
    sx, sy, r1 = x - s * .35, y - s * .5, s * .62
    star = []
    for i in range(10):
        a = -PI / 2 + PI * i / 5 + .2
        r = r1 if i % 2 == 0 else r1 * .38
        star.append((sx + r * math.cos(a) * 1.15, sy + r * math.sin(a) * .8))
    cv.obj([star], 1.)
    for i in range(0, 10, 2):
        cv.hair([(sx, sy), ((star[i][0] + sx) / 2, (star[i][1] + sy) / 2)])
        cv.line([(sx + (star[i][0] - sx) * .45, sy + (star[i][1] - sy) * .45), (sx + (star[i][0] - sx) * .7, sy + (star[i][1] - sy) * .7)])
    # a clam
    cx, cy, cr = x + s * .75, y - s * .2, s * .35
    clam = C._ell_pts(cx, cy, cr * 1.2, cr, 16, PI, 2 * PI) + [(cx + cr * 1.2, cy + 1), (cx - cr * 1.2, cy + 1)]
    cv.obj([clam], 1.)
    for k in range(-2, 3):
        cv.hair([(cx, cy + 1), (cx + k * cr * .45, cy - cr * .85)])


def scene(X, Y, W, H, seed, small=False):
    """The storm coast filling the box X, Y, W, H (caller clips it). The layout follows the
    box's aspect: wide (band), landscape (cartouche) or portrait (tall plate)."""
    rng = random.Random(seed)
    portrait = H > W * .85
    S = min(H, W * .62)
    _S[0] = S
    hy = Y + H * (.58 if portrait else (.5 if small else .47))
    base = Y + H * (.8 if portrait else .9)
    o = []
    cv = C.Canvas()
    puffs = _puffs(X, Y, W, H, hy, rng)
    if portrait:
        # a second tier of billows lower in the tall sky
        P2 = _puffs(X, Y + (hy - Y) * .38, W, H * .55, hy, rng)
        puffs = puffs + [p for p in P2 if p[1] < hy - S * .12]
    _sky(cv, X, Y, W, H, hy, rng, puffs)
    _bolt(cv, X + W * .55, Y + (hy - Y) * .42, hy - S * .02, rng)
    _headland(cv, X, Y, W, H, hy, rng)
    bpoly, btop = _beach(X, Y, W, H, rng, .93 if portrait else .86)
    _sea(cv, X, Y, W, H, hy, max(base, Y + H * .97), rng)
    _whitecaps(cv, X, Y, W, H, hy, rng, small)
    big = W * .46 if portrait else min(H * (.68 if not small else .72), W * .4, S * .75)
    outer, (wcx, wcy, wR) = _breaker(cv, X - W * .06, base, big, rng, True)
    o.append(cv.svg())
    sp = _spray(X, Y, W, H, wcx + wR * .9, wcy - wR * .4, big * .3, rng, 80 if not small else 40)
    o.append(_dots(sp, .9))
    # the beach (stipple ground) with a lacy wash line of the sneaker wave
    o.append(f'<path d="{_poly_d(bpoly)}" fill="{C.pat("S")}" stroke="none"/>')
    cv2 = C.Canvas()
    wash = [(px, py - 1.6) for px, py in btop] + [(btop[-1][0], btop[-1][1] + 2.5)] + [(px, py + 2.5 + 1.4 * math.sin(px * .9)) for px, py in btop[::-1]]
    cv2.obj([wash], .5)
    cv2.hair([[(px, py + 1 + .6 * math.sin(px * .5)) for px, py in btop]])
    cv2.line([[(px, py + 3.6 + 1.4 * math.sin(px * .9)) for px, py in btop]])
    tip, sand_y = _wreck(cv2, X, Y, W, H, btop, rng)
    tx = X + W * (.5 if not portrait else .3)
    _tidepool(cv2, tx, sand_y(tx) + S * .1, S * .1, rng)
    o.append(cv2.svg())
    o.append(_heron(tip[0] + 1, tip[1] + .5, max(1.5, S * .03)))
    return "".join(o)


# ------------------------------------------------------------------------------------------
# frame pieces: the Vitruvian running-wave moulding (the sea's own classical ornament)
# ------------------------------------------------------------------------------------------

def running_wave(x, y, w, h):
    """A band of Vitruvian scroll: white curling waves on a black ground, each eye a spiral,
    with a fillet above and a bead-like rule below."""
    o = []
    hh = h - 2.5
    P = hh * 1.9
    n = max(1, round(w / P))
    P = w / n
    yb, yt = y + 1.5 + hh, y + 1.5
    R = hh * .36
    pts = [(x - 1, yb)]
    eyes = []
    for k in range(n + 1):
        x0 = x + k * P - P * .1
        cx, cy = x0 + P * .55, yt + R + .2
        # back of the wave rising from the trough
        for i in range(1, 7):
            t = i / 7
            pts.append((x0 + (cx - R - x0) * t, yb - (yb - cy) * C._smooth(0, 1, t)))
        # over the crest and down into the curl (clockwise in y-down)
        for i in range(19):
            a = PI + PI * 1.45 * i / 18
            pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
        # the lip comes back in toward the eye
        for i in range(9):
            a = PI * 2.45 - PI * .85 * i / 8
            r = R * (.55 - .1 * i / 8)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        # the front falls to the next trough
        pts.append((cx + R * .25, cy + R * .3))
        pts.append((cx + R * .9, yb - hh * .12))
        eyes.append((cx, cy, R))
    pts.append((x + w + 1, yb))
    o.append(f'<path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="#000" stroke="none"/>')
    o.append(f'<path d="{_poly_d(pts)}" fill="#fff" stroke="none"/>')
    # modelling: two hairlines following the back of each wave
    hd = []
    for cx, cy, r in eyes:
        for f in (.78, .62):
            a0, a1 = PI * 1.05, PI * 2.2
            seg = [(cx + r * f * math.cos(a0 + (a1 - a0) * i / 12), cy + r * f * math.sin(a0 + (a1 - a0) * i / 12)) for i in range(13)]
            hd.append(C._d(seg, tol=.1))
    o.append(f'<path d="{"".join(hd)}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="M{_n(x)},{_n(y + .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts
# ------------------------------------------------------------------------------------------

def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.9, 230)
    o.append(C._clip(C._uid("cb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .86, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = C._d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True, .1)
    o.append(_field_clip(C._uid("cbf", w, h, seed), fd, scene(cx - rx, cy - ry, rx * 2, ry * 2, seed, small=True)))
    # re-cut the inner ring over the scene so the field edge is crisp
    o.append(f'<path d="{C._d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(running_wave(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .54, gh * 1.95)
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
    o.append(C._clip(C._uid("cm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(_field_clip(C._uid("cmf", w, h, seed), fd, scene(cx - a, cy - b, 2 * a, 2 * b, seed)))
    o.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall_fill(seed):
    def fill(ix, iy, iw, ih):
        k = 2 ** (-1 / 2.6)
        a, b = iw / 2 / k + 6, ih / 2 / k + 6
        cx, cy = ix + iw / 2, iy + ih / 2
        fd = C._d(C._superellipse(cx, cy, a, b), True, 0)
        return (_field_clip(C._uid("ctf", ix, iy, iw, ih, seed), fd, scene(cx - a, cy - b, 2 * a, 2 * b, seed))
                + f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')
    return fill


def _tide_ribbon(centre, bh):
    """The banner carries the week's tide: two highs and two lows a day as an engraved curve,
    water ruled below it, sky finely ruled above."""
    n = len(centre) - 1
    up, lo, curve = [], [], []
    for i in range(n + 1):
        u = i / n
        x, y = centre[i]
        yc = y + bh * .26 * math.sin(u * 4 * PI * 1.5 + .6) * (.8 + .2 * math.sin(u * 7))
        curve.append((x, yc))
    hair, vert = [], []
    for i in range(0, n + 1):
        x, y = centre[i]
        # (sampled finely below)
    d_up, d_lo = [], []
    x0, x1 = centre[0][0] + 1.5, centre[-1][0] - 1.5
    xx = x0
    def at(x):
        f = (x - centre[0][0]) / (centre[-1][0] - centre[0][0]) * n
        i = min(int(f), n - 1)
        r = f - i
        return (centre[i][1] + (centre[i + 1][1] - centre[i][1]) * r, curve[i][1] + (curve[i + 1][1] - curve[i][1]) * r)
    while xx <= x1:
        yc, yv = at(xx)
        d_lo.append(f"M{_n(xx)},{_n(yv + 1.2)}V{_n(yc + bh * .5 - 1.6)}")
        xx += 2.
    yy = -bh * .5 + 2.
    while yy < bh * .3:
        seg, cur = [], []
        xx = x0
        while xx <= x1:
            yc, yv = at(xx)
            if yc + yy < yv - 1.2:
                cur.append((xx, yc + yy))
            else:
                if len(cur) > 1:
                    seg.append(cur)
                cur = []
            xx += 2.
        if len(cur) > 1:
            seg.append(cur)
        d_up.extend(C._d(s, tol=.1) for s in seg)
        yy += 3.
    return (f'<path d="{"".join(d_lo)}{"".join(d_up)}" stroke="#000" stroke-width=".5" fill="none"/>'
            f'<path d="{C._d(curve, tol=.1)}" stroke="#000" stroke-width="1.5" fill="none"/>')


def _tall(w, h, seed, fill_fn, density=.8):
    rng = random.Random(seed)
    o = []
    o.append(C.dark_ground((0, 0, w, h), "L"))      # nothing left bare: a light ruled ground under all
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .44, ph * .58
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
    o.append(_tide_ribbon(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(running_wave(tx + 2.5, ty + 2.5, tw - 4, th - 4))
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
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed, _tall_fill(seed), .8)
    return C.svg_doc(w, h, body)
