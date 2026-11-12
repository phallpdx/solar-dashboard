"""delights-03 -- Poem of the day, Veterans Day: John McCrae, "In Flanders Fields" (1915).

The plate is the field itself: a dawn sky ruled in bulino with larks still singing, rows of white
crosses running back to a shattered tree line, poppies blowing in the foreground, their leaves cut
as acanthus fingers. The frame is the house Codex scrollwork; poppies grow out of the leafage, the
crest is the torch thrown "from failing hands" with a flame of curling fingers, the ribbon reads
IN FLANDERS FIELDS and the pedestal tablet LEST WE FORGET.
Easter egg: a tiny WWI side drum with crossed drumsticks lies in the grass at the foot of the field.
"""
import sys
import math
import random
import engraving_codex as C
import engraving_morning as M

_n, _d = C._n, C._d
TAU = math.tau

# ----------------------------------------------------------------------------------------------
# lettering (house stroke glyphs + an S of our own)
# ----------------------------------------------------------------------------------------------
_G = dict(M._G)
_G["S"] = (5, [("s", [(4.5, 1.1), (3.2, 0), (1.5, .1), (.6, 1.3), (.9, 2.9), (2.6, 3.9), (4.1, 4.8),
                      (4.6, 6.3), (3.7, 7.7), (2, 8), (.3, 7)])])


def _glyphs(ch):
    adv, strokes = _G.get(ch, _G[" "])
    return adv, [M._spline(p, False, 4) if k == "s" else list(p) for k, p in strokes]


def _text_width(s, track):
    return sum(_G.get(c, _G[" "])[0] + track for c in s) - track


def text_on_curve(s, centre, cap, track=1.3):
    """Glyph polylines centred along a polyline `centre` (the letters' mid-height line)."""
    k = cap / 8.
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.dist(centre[i], centre[i - 1]))
    tot = L[-1]

    def at(sv):
        sv = min(max(sv, 0), tot)
        j = 1
        while j < len(L) - 1 and L[j] < sv:
            j += 1
        a, b = centre[j - 1], centre[j]
        f = (sv - L[j - 1]) / max(1e-6, L[j] - L[j - 1])
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, ang

    width = _text_width(s, track) * k
    s0 = tot / 2 - width / 2
    out = []
    cx = 0.
    for c in s:
        adv, polys = _glyphs(c)
        mx, my, ang = at(s0 + (cx + adv / 2) * k)
        ca, sa = math.cos(ang), math.sin(ang)
        for p in polys:
            q = []
            for px, py in p:
                lx, ly = (px - adv / 2) * k, (py - 4) * k
                q.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            out.append(q)
        cx += adv + track
    return out


def _stroke(polys, w=1.):
    d = "".join(_d(p, tol=0) for p in polys)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w)}"/>'


# ----------------------------------------------------------------------------------------------
# small engraved motifs, all drawn into a Canvas
# ----------------------------------------------------------------------------------------------

def _black(cv, poly):
    """A solid black shape: outline plus 1 px lines 0.8 px apart."""
    cv.obj([poly], 1.)
    cv.line(C.hatch_poly(poly, 0, .8))


def _disc(cv, x, y, r):
    cv.obj([C._ell_pts(x, y, r + .5, r + .5, 14)[:-1]], 0)
    q = r
    while q > .3:
        cv.line(C._ell_pts(x, y, q, q, max(8, int(q * 6))))
        q -= .8
    cv.line([(x - .3, y), (x + .3, y)])


def _rot(pts, x, y, a, s=1., fx=1.):
    ca, sa = math.cos(a), math.sin(a)
    return [(x + (px * fx * ca - py * sa) * s, y + (px * fx * sa + py * ca) * s) for px, py in pts]


def poppy(cv, x, y, r, tilt=0., rng=None, squash=.8):
    """A field poppy, face a little turned to us: four broad crinkled petals overlapping into a
    round cup, dark (red reads dark in an engraving) with fan-hatching running out from the heart
    and cross-hatching deep in the cup, a white turned rim; a black blotch at the heart, a ring of
    stamens and a white seed-pod with its rayed crown."""
    rng = rng or random.Random(0)
    ca, sa = math.cos(tilt), math.sin(tilt)

    def T(px, py):
        py *= squash
        return (x + (px * ca - py * sa) * r, y + (px * sa + py * ca) * r)

    ph = rng.random() * 6
    order = ((-math.pi * .75, 1.0), (-math.pi * .25, 1.0), (math.pi * .75, .97), (math.pi * .25, .97))
    for k, (a, rad) in enumerate(order):
        half = math.pi * .36
        n = 26 if r > 9 else 14
        edge = []
        for i in range(n + 1):
            t = i / n
            aa = a - half + 2 * half * t
            sh = math.sin(math.pi * t) ** .28
            rr = rad * sh * (1 + .05 * math.sin(t * 19 + ph + k) + .03 * math.sin(t * 41 + k))
            edge.append((math.cos(aa) * rr, math.sin(aa) * rr))
        pts = [T(0, 0)] + [T(*p) for p in edge]
        cv.obj([pts], 1.)
        # fan hatching: lines from the heart toward the rim, stopping short (the white turned rim)
        m = 22 if r > 9 else 14 if r > 5 else 8
        for i in range(1, m):
            t = i / m
            aa = a - half + 2 * half * t
            sh = math.sin(math.pi * t) ** .28
            stop = (.8 if i % 2 else .9) * sh * rad
            cv.hair([T(math.cos(aa) * .3, math.sin(aa) * .3), T(math.cos(aa) * stop, math.sin(aa) * stop)])
        # cross-hatched cup: arcs round the heart
        for rr in ((.42, .5, .58, .66) if r > 9 else (.45, .6) if r > 5 else ()):
            arc = [T(math.cos(a - half * .8 + 1.6 * half * j / 12) * rr, math.sin(a - half * .8 + 1.6 * half * j / 12) * rr)
                   for j in range(13)]
            cv.hair(arc)
        # a crease down the middle of the petal
        if r > 5:
          cv.line([T(math.cos(a) * .3, math.sin(a) * .3), T(math.cos(a + .08) * .75, math.sin(a + .08) * .75)])
        # shadow cast by the next petal along its leading edge
        if r > 5:
          cv.line([T(math.cos(a - half + .12) * .32, math.sin(a - half + .12) * .32),
                 T(math.cos(a - half + .2) * .7, math.sin(a - half + .2) * .7)])
    # black blotch at the heart
    hx, hy = T(0, 0)
    br = r * .36
    cv.obj([C._ell_pts(hx, hy, br, br * squash, 18)[:-1]], 0)
    q = br
    while q > .3:
        cv.line(C._ell_pts(hx, hy, q, q * squash, max(8, int(q * 5))))
        q -= .8
    # stamens round the pod
    if r > 6:
        for i in range(12):
            aa = TAU * i / 12 + ph
            cv.hair([T(math.cos(aa) * .2, math.sin(aa) * .2), T(math.cos(aa) * .34, math.sin(aa) * .34)])
    # seed pod with rayed crown
    pr = r * .16
    pod = C._ell_pts(hx, hy, pr, pr * squash, 14)[:-1]
    cv.obj([pod], 1.)
    if r > 7:
        for i in range(8):
            aa = TAU * i / 8 + ph
            cv.hair([(hx, hy), (hx + math.cos(aa) * pr * .85, hy + math.sin(aa) * pr * .85 * squash)])


def poppy_bud(cv, x, y, r, ang):
    """A hairy, nodding bud on its hook."""
    pts = _rot(C._ell_pts(0, 0, 1, .62, 16)[:-1], x, y, ang, r)
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, math.degrees(ang) + 70, 1.5))
    for i in range(6):
        a = ang + math.pi * (.3 + .4 * i / 5)
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * .62
        cv.hair([(px, py), (px + math.cos(a) * 1.4, py + math.sin(a) * 1.4)])


def stem(cv, pts, w=1.):
    R = C._Rib(pts, [w] * len(pts), [w] * len(pts))
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(-.4, 0, 1))
    for i in range(2, len(pts) - 1, 3):
        a, b = pts[i - 1], pts[i + 1]
        t = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (-1, 1):
            nx, ny = -math.sin(t) * s, math.cos(t) * s
            cv.hair([(pts[i][0] + nx * w, pts[i][1] + ny * w),
                     (pts[i][0] + nx * (w + 1.6) + math.cos(t) * 1, pts[i][1] + ny * (w + 1.6) + math.sin(t) * 1)])


def poppy_plant(cv, x, y, h, lean, r, rng, leaves=True, bud=True):
    """Stem from the ground at (x, y) rising h, leaning `lean` radians, flower of radius r on top."""
    n = 16
    pts = C._euler(x, y, -math.pi / 2 + lean * .3, h, lambda u: lean * 1.4 / h, n)
    if leaves:
        for k, s in ((0, -1), (1, 1)):
            j = 3 + k * 2
            a, b = pts[j - 1], pts[j + 1]
            t = math.atan2(b[1] - a[1], b[0] - a[0])
            C._finger(cv, pts[j][0], pts[j][1], t + s * .55, h * .5, h * .065, s * .7, s * 3.6, .9,
                      teeth=3)
    if bud:
        j = 6
        a, b = pts[j - 1], pts[j + 1]
        t = math.atan2(b[1] - a[1], b[0] - a[0])
        sg = 1 if lean <= 0 else -1
        bp = C._euler(pts[j][0], pts[j][1], t + sg * .6, h * .35, lambda u: -sg * 6. / h * (1 + 2 * u), 8)
        stem(cv, bp, .7)
        e = bp[-1]
        ea = math.atan2(bp[-1][1] - bp[-2][1], bp[-1][0] - bp[-2][0])
        poppy_bud(cv, e[0] + math.cos(ea) * r * .3, e[1] + math.sin(ea) * r * .3, r * .32, ea)
    stem(cv, pts, max(.7, r * .06))
    e = pts[-1]
    poppy(cv, e[0], e[1] - r * .55, r, lean * .4, rng)


def cross(cv, x, y, s):
    """A white wooden grave cross, base at (x, y), height s, its right face and top in shade."""
    t = max(1., s * .13)
    arm = s * .3
    ay = y - s * .72
    if s < 9:
        cv.obj([], 0)
        cv.line([(x, y), (x, y - s)])
        cv.line([(x - arm, ay), (x + arm, ay)])
        return
    d = t * .55
    face = [(x - t / 2, y), (x - t / 2, ay + t / 2), (x - arm, ay + t / 2), (x - arm, ay - t / 2),
            (x - t / 2, ay - t / 2), (x - t / 2, y - s), (x + t / 2, y - s), (x + t / 2, ay - t / 2),
            (x + arm, ay - t / 2), (x + arm, ay + t / 2), (x + t / 2, ay + t / 2), (x + t / 2, y)]
    side1 = [(x + t / 2, y), (x + t / 2, ay + t / 2), (x + t / 2 + d, ay + t / 2 - d * .5), (x + t / 2 + d, y - d * .4)]
    side2 = [(x + arm, ay - t / 2), (x + arm + d, ay - t / 2 - d * .5), (x + arm + d, ay + t / 2 - d * .5), (x + arm, ay + t / 2)]
    side3 = [(x + t / 2, y - s), (x + t / 2 + d, y - s - d * .5), (x + t / 2 + d, ay - t / 2 - d * .5), (x + t / 2, ay - t / 2)]
    # its shadow cast on the grass
    sh = [(x - t / 2, y), (x + t / 2 + d, y - d * .4), (x + s * .55, y + s * .05), (x + s * .5, y + s * .1)]
    cv.obj([sh], 0)
    cv.hair(C.hatch_poly(sh, 0, 1.5))
    for sd in (side1, side2, side3):
        cv.obj([sd], 1.)
        cv.hair(C.hatch_poly(sd, 90, 1.5))
    cv.obj([face], 1.)
    cv.hair([(x + t * .15, y - s * .05), (x + t * .15, ay + t)])
    if s > 18:
        cv.hair([(x + t * .15, ay - t), (x + t * .15, y - s + t * .4)])
        cv.hair([(x - arm + t * .3, ay + t * .2), (x - t, ay + t * .2)])
        cv.hair([(x + t, ay + t * .2), (x + arm - t * .2, ay + t * .2)])
        cv.line([(x - t * .2, ay), (x + t * .2, ay)])   # nail head on the joint


def lark(cv, x, y, s, a, flap):
    """A lark on the wing: dark body, wings raised (flap 0..1), forked-free short tail."""
    up = .5 + .9 * flap
    body = [(-1.1, 0), (-.5, -.22), (.3, -.25), (.9, -.12), (1.25, 0), (.9, .14), (.2, .22), (-.6, .16)]
    wl = [(-.15, -.1), (-.55, -.5 * up), (-1.0, -1.05 * up), (-.55, -.9 * up), (.25, -.15)]
    wr = [(.05, -.1), (.35, -.65 * up), (.15, -1.25 * up), (.55, -.85 * up), (.5, -.12)]
    tail = [(-1.0, -.05), (-1.6, -.25), (-1.65, .12), (-1.0, .1)]
    for p in (wl, tail, body, wr):
        _black(cv, _rot(p, x, y, a, s))


def side_drum(cv, x, y, s):
    """Easter egg: a WWI side drum with rope tensioning and two crossed sticks, s px wide."""
    w, h = s, s * .62
    sticks = []
    for sg in (-1, 1):
        x0, y0 = x - sg * w * .7, y - h * 1.05
        x1, y1 = x + sg * w * .55, y + h * .25
        sticks.append([(x0, y0), (x1, y1)])
    shell = [(x - w / 2, y - h / 2)] + C._ell_pts(x, y + h / 2, w / 2, h * .22, 16, 0, math.pi) + [(x + w / 2, y - h / 2)]
    shell = [(x - w / 2, y - h / 2), (x - w / 2, y + h / 2)] + C._ell_pts(x, y + h / 2, w / 2, h * .22, 16, math.pi, 0)[::-1][::-1][1:-1] + [(x + w / 2, y + h / 2), (x + w / 2, y - h / 2)]
    shell = [(x - w / 2, y - h / 2)] + [(x + w / 2 * math.cos(math.pi - math.pi * i / 16), y + h / 2 + h * .22 * math.sin(math.pi - math.pi * i / 16)) for i in range(17)] + [(x + w / 2, y - h / 2)]
    cv.obj([shell], 1.)
    zig = []
    for i in range(7):
        zig.append((x - w / 2 + w * i / 6, y - h * .4 if i % 2 == 0 else y + h * .45))
    cv.hair(zig)
    cv.hair(C.hatch_poly([(x + w * .2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x + w * .2, y + h * .6)], 90, 1.5))
    for yy in (y - h * .42, y + h * .5):
        cv.line([(x - w / 2, yy), (x + w / 2, yy)])
    head = C._ell_pts(x, y - h / 2, w / 2, h * .22, 18)[:-1]
    cv.obj([head], 1.)
    for st in sticks:
        R = C._Rib(st, [.8, .5], [.8, .5])
        cv.obj([R.outline()], .5)
        cv.hair([st[0], st[1]])
        cv.line([st[1], st[1]])


# ----------------------------------------------------------------------------------------------
# the scene: Flanders field at dawn, filling any field polygon
# ----------------------------------------------------------------------------------------------

def _scanx(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    xs.sort()
    return xs


def scene(field, seed, egg=True, detail=1.):
    """The whole vignette for a field polygon; returns (canvas_svg, black_fill_svg) to be clipped."""
    rng = random.Random(seed)
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W, H = x1 - x0, y1 - y0
    cxm = (x0 + x1) / 2
    cv = C.Canvas()
    big = [(x0 - 4, y0 - 4), (x1 + 4, y0 - 4), (x1 + 4, y1 + 4), (x0 - 4, y1 + 4)]
    yH = y0 + H * (.4 if H > W * .8 else .48 if H > 70 else .5)
    # --- sky: bulino ruling, darker overhead, opening round the low sun
    sx, sy = cxm + W * .14, yH
    sr = min(H * .2, W * .1)
    glow = sr * 3.2
    cv.obj([], 0)
    y = y0 - 2
    i = 0
    while y < yH:
        f = (y - y0) / max(1, yH - y0)
        segs = []
        xa, xb = x0 - 4, x1 + 4
        # rays: alternate wedges round the sun keep every other line
        if y < sy:
            span = []
            xx = xa
            step = 1.
            cur = [xx, None]
            while xx <= xb:
                dx, dy = xx - sx, y - sy
                dist = math.hypot(dx, dy)
                keep = True
                if dist < glow:
                    ang = math.atan2(dy, dx)
                    ray = int((ang + math.pi) / (math.pi / 13)) % 2
                    if dist < sr * 1.25:
                        keep = (i % 2 == 0)
                    elif ray and i % 2:
                        keep = False
                if f < .35 and i % 1 == 0:
                    pass
                if keep and cur[1] is None:
                    cur = [xx, True]
                if not keep and cur[1]:
                    segs.append([(cur[0], y), (xx, y)])
                    cur = [xx, None]
                xx += step
            if cur[1]:
                segs.append([(cur[0], y), (xb, y)])
        else:
            segs.append([(xa, y), (xb, y)])
        for sgm in segs:
            if f < .4:
                cv.line(sgm) if i % 3 == 0 and f < .15 else cv.hair(sgm)
            else:
                cv.hair(sgm)
        pitch = 1.5 if f < .3 else 2. if f < .75 else 2.
        y += pitch
        i += 1
    # sun disc behind the horizon, ruled, with a 1 px rim
    disc = C._ell_pts(sx, sy, sr, sr, 40, math.pi, TAU)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 3, 1.))
    # larks
    birds = []
    for k in range(int((8 if H > 150 else 5) * detail) if H > 60 else 2):
        bx = x0 + W * (.12 + .76 * rng.random())
        by = y0 + (yH - y0) * (.18 + .5 * rng.random())
        if math.hypot(bx - sx, by - sy) < sr * 1.6:
            continue
        lark(cv, bx, by, rng.uniform(3., 4.4) * (1 if H > 60 else .75), rng.uniform(-.3, .3) * (1 if bx < cxm else -1) + (0 if bx < sx else math.pi) * 0, rng.random())
    # --- distant tree line and a shattered church
    tl = [(x0 - 4, yH + 1)]
    for t in range(0, 61):
        xx = x0 - 4 + (W + 8) * t / 60
        hh = 2.2 + 1.6 * math.sin(t * 1.7 + seed) + 1.2 * math.sin(t * .53)
        tl.append((xx, yH - max(.8, hh)))
    tl.append((x1 + 4, yH + 1))
    cv.obj([tl], .5)
    cv.hair(C.hatch_poly(tl, 90, 1.5))
    ch_x = cxm - W * .3
    if H > 60:
        spire = [(ch_x - 4, yH), (ch_x - 4, yH - 7), (ch_x - 2.5, yH - 9), (ch_x - 1.6, yH - 14), (ch_x - .8, yH - 9.5),
                 (ch_x + .6, yH - 10.5), (ch_x + 1.2, yH - 7.5), (ch_x + 4, yH - 6), (ch_x + 5, yH)]
        cv.obj([spire], 1.)
        cv.hair(C.hatch_poly(spire, 90, 1.5))
        cv.line([(ch_x - 1, yH - 5), (ch_x - 1, yH - 3)])
    # --- the ground: furrows in perspective, falling toward us
    gnd = [(x0 - 4, yH), (x1 + 4, yH), (x1 + 4, y1 + 4), (x0 - 4, y1 + 4)]
    cv.obj([gnd], 0)
    d = .8
    yy = yH + 1.
    while yy < y1 + 4:
        cv.hair([(x0 - 4, yy), (x1 + 4, yy)])
        d = min(3., 1.5 + (yy - yH) * .05)
        yy += d
    vx = cxm
    for k in range(-14, 15):
        cv.hair([(vx + k * 3, yH + 1), (vx + k * 40, y1 + 4)])
    # --- crosses, row on row, receding
    rows = 7 if H > 150 else 6 if H > 90 else 4 if H > 50 else 3
    smax = H * .26
    for rI in range(rows):
        q = .08 + .92 * ((rI + 1) / rows) ** 1.6
        by = yH + (y1 - yH) * q * (.88 if H > W * .8 else .8)
        s = min(smax, (by - yH) * .8 + 3)
        sp = max(5., s * 1.25)
        off = (rI % 2) * sp / 2 + rng.uniform(0, sp * .3)
        xx = x0 - sp + off
        xs_ = _scanx(field, by)
        small = []
        while xx < x1 + sp:
            if xs_ and xs_[0] + s * .3 < xx < xs_[-1] - s * .3:
                cross(cv, xx, by, s)
                for _ in range(2 if H > 200 else 3):
                    small.append((xx + rng.uniform(-sp * .55, sp * .55), by + rng.uniform(0, s * .22)))
            xx += sp
        # poppies blowing between the crosses, row on row
        for (px, py) in sorted(small, key=lambda p: p[1]):
            pr = s * rng.uniform(.13, .19)
            if pr >= 3.:
                cv.obj([], 0)
                cv.hair([(px, py + pr), (px + rng.uniform(-1, 1), py + pr * 3.)])
                poppy(cv, px, py, pr, rng.uniform(-.4, .4), rng)
            else:
                _disc(cv, px, py, max(.7, pr * .7))
    # --- foreground: poppies blowing at both sides, grass, and the Easter-egg drum
    rr = min(H * .13, W * .075, 20.)
    cnt = 3 if H > 90 else 2 if H > 50 else 1
    for side in (-1, 1):
        xs_ = _scanx(field, y1 - H * .2)
        edge_x = xs_[0] if side < 0 else xs_[-1]
        for k in range(cnt):
            bx = edge_x - side * (rr * (.5 + 1.25 * k) + rng.uniform(-2, 2))
            hgt = (y1 - yH) * (.62 - .1 * k) * rng.uniform(.92, 1.06) + rr * .4
            r = rr * (1 - .13 * k)
            poppy_plant(cv, bx, y1 + 4, hgt, side * (.12 + .1 * k), r, rng, leaves=(H > 50 and k < 2),
                        bud=(k == 1 and H > 70))
    # grass in the foreground middle
    gx0, gx1 = cxm - W * .25, cxm + W * .25
    cv.obj([], 0)
    for k in range(int(W * .2)):
        gx = gx0 + (gx1 - gx0) * rng.random()
        gb = y1 + 2 - rng.random() * H * .08
        gh = rng.uniform(3, 7) * (1 if H > 60 else .6)
        lean = rng.uniform(-.5, .5)
        cv.hair([(gx, gb), (gx + lean * gh * .5, gb - gh * .6), (gx + lean * gh, gb - gh)])
    if egg and H > 60:
        side_drum(cv, cxm + W * .17, y1 - min(9, H * .06), max(12., W * .05))
        _disc(cv, cxm - W * .08, y1 - H * .05, 1.6)
        _disc(cv, cxm + W * .02, y1 - H * .08, 1.3)
    return cv.svg()


def field_svg(field, cid, seed, egg=True, detail=1.):
    d = _d(field, True, 0)
    body = scene(field, seed, egg, detail)
    return (f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">'
            f'<path d="{d}" fill="#fff" stroke="none"/>{body}</g>')


# ----------------------------------------------------------------------------------------------
# frame pieces adapted from the house layouts
# ----------------------------------------------------------------------------------------------

def _cart_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a, b)


def torch(cx, cy, size, seed):
    """The crest: the torch thrown 'from failing hands', its flame a palmette of curling fingers."""
    cv = C.Canvas()
    hl = size * .55
    top = cy - hl
    shaft = [(cx - size * .07, cy), (cx - size * .11, top), (cx + size * .11, top), (cx + size * .07, cy)]
    cv.obj([shaft], 1.)
    cv.hair(C.hatch_poly(shaft, 90, 1.5, 0.))
    for k in range(1, 5):
        yy = cy - hl * k / 5
        cv.line([(cx - size * .06, yy), (cx + size * .06, yy + 1.5)])
    cup = [(cx - size * .26, top - size * .14), (cx + size * .26, top - size * .14), (cx + size * .13, top + 1),
           (cx - size * .13, top + 1)]
    cv.obj([cup], 1.)
    cv.hair(C.hatch_poly(cup, 0, 1.5))
    C.palmette(cx, top - size * .14, size * .8, True, seed, 2, cv=cv)
    return cv.svg()


def _lettered_banner(cx, cy, w, h, seed, words):
    svg, centre = C.ribbon_banner(cx, cy, w, h, .04, seed)
    cap = min(h * .55, 9.)
    face = [(p[0], p[1] + h * .08) for p in centre]
    return svg + _stroke(text_on_curve(words, face, cap, 1.6), 1.)


def _tablet_letters(tx, ty, tw, th, words):
    cap = min(th * .62, 10.)
    k = cap / 8.
    wid = _text_width(words, 1.8) * k
    while wid > tw * .9:
        cap *= .9
        k = cap / 8.
        wid = _text_width(words, 1.8) * k
    line = [(tx + tw / 2 - wid, ty + th / 2 + .6), (tx + tw / 2 + wid, ty + th / 2 + .6)]
    return _stroke(text_on_curve(words, line, cap, 1.8), 1.)


def _poppy_sprigs(cv, pts, rng, r):
    for (px, py, ang) in pts:
        poppy(cv, px, py, r * rng.uniform(.9, 1.05), ang, rng)


def layout_tall(w, h, seed, lite=False):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 46), 80.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .07, 30.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = (pw * .5, ph * .7) if h > 420 else (pw * .56, ph * .72)
    cx, cy = w / 2, py0 + ph * (.46 if h > 420 else .5)
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=1 if lite else 9 if h <= 400 else 4, edge=.6, cv=cv)
    cv.extend(main)
    # poppies grown out of the leafage at the outer ends of the panel
    pc = C.Canvas()
    pr = min(13., ph * .06)
    for side in (-1, 1):
        ex = cx + side * (cw * .5 + r1 * 1.55)
        poppy(pc, ex, py0 + ph * .5, pr, side * .5, rng)
    cv.extend(pc)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(field_svg(_cart_field(cx, cy, cw, ch), C._uid("v", w, h, seed), seed))
    tb = cy - ch / 2 + 6
    o.append(torch(cx, tb, min(ch * .22 + top_free, 66, (tb - 1) / 1.62), rng.randrange(1 << 20)))
    bh = min(18., ph * .065)
    o.append(_lettered_banner(cx, cy + ch * .5 - 1, cw * 1.45, bh, rng.randrange(1 << 20), "IN FLANDERS FIELDS"))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    fh_ = th / .6
    t2y, t2h = ty - fh_ * .14, fh_ * .86
    o.append(f'<path d="M{_n(tx)},{_n(t2y)}h{_n(tw)}v{_n(t2h)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>'
             f'<path d="M{_n(tx + 2)},{_n(t2y + 2)}h{_n(tw - 4)}v{_n(t2h - 4)}h{_n(-tw + 4)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(_tablet_letters(tx, t2y + 1, tw, t2h - 2, "LEST WE FORGET"))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        cvp = C.Canvas()
        poppy(cvp, w / 2, fy + fh * .45, fh * .32, 0., rng)
        o.append(cvp.svg())
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.8)
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
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(field_svg(_cart_field(cx, cy, cw, gh + 4), C._uid("mv", w, h, seed), seed, egg=gh > 90, detail=.8))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.2, 150)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    ring = _d(C._ell_pts(cx, cy, rx + 1, ry + 1, 64), True) + _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    fld = C._ell_pts(cx, cy, rx - 2, ry - 2, 64)[:-1]
    o.append(field_svg(fld, C._uid("bv", w, h, seed), seed, egg=False, detail=.5))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 1103
    if h < 110:
        body = layout_band(w, h, seed)
    elif h <= 260:
        body = layout_medium(w, h, seed)
    else:
        body = layout_tall(w, h, seed)
        if len(body) > 196 * 1024:      # stay under the 200 KB plate budget whatever the date
            body = layout_tall(w, h, seed, lite=True)
    return C.svg_doc(w, h, body)
