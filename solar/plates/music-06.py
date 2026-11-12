"""music-06 "Live music ahead": a concert stage engraved inside the house Codex frame.

The page lists the coming shows (Bonobo at the Roseland, Thundercat at the Crystal Ballroom,
Neurosis, feeble little horse), so the vignette is the stage on the night: swagged curtains, a
lighting truss throwing three beams, amp stacks, a drum kit, a six-string bass (Thundercat) on its
stand, a microphone, and the crowd's heads and raised hands in silhouette at the foot.
Easter eggs: the kick-drum head carries Parker's "P" monogram, a pair of crossed drumsticks lean on
the kit, and the pedestal tablet / ribbon carry a bar of swing ride rhythm on a staff.
"""
import sys
import math
import random
import engraving_codex as C

_n, _d, _ell, _uid, _clip = C._n, C._d, C._ell_pts, C._uid, C._clip
pat = C.pat
PI, TAU = math.pi, 2 * math.pi


# ------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------

def _cr(pts, k=6):
    """Closed Catmull-Rom smoothing."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    return out


def _xf(pts, ox, oy, s, ang=0., sx=1.):
    c, si = math.cos(ang), math.sin(ang)
    return [(ox + (x * sx * c - y * si) * s, oy + (x * sx * si + y * c) * s) for x, y in pts]


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (x1 - x0) * (y - y0) / (y1 - y0):
            c = not c
    return c


def _hatch_where(poly, angle, pitch, keep, step=1.):
    """hatch_poly lines, kept only where keep(x, y) is true (runs sampled every `step` px)."""
    out = []
    for (a, b) in C.hatch_poly(poly, angle, pitch):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        run = None
        for i in range(n + 1):
            t = i / n
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if keep(*p):
                if run is None:
                    run = [p, p]
                else:
                    run[1] = p
            elif run is not None:
                if math.hypot(run[1][0] - run[0][0], run[1][1] - run[0][1]) > .8:
                    out.append(run)
                run = None
        if run is not None and math.hypot(run[1][0] - run[0][0], run[1][1] - run[0][1]) > .8:
            out.append(run)
    return out


def _run_keep(seg, keep, step=1.):
    (a, b) = seg
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L / step))
    out, run = [], None
    for i in range(n + 1):
        t = i / n
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if keep(*p):
            run = [p, p] if run is None else [run[0], p]
        elif run is not None:
            out.append(run)
            run = None
    if run is not None:
        out.append(run)
    return [r for r in out if math.hypot(r[1][0] - r[0][0], r[1][1] - r[0][1]) > .8]


def _solid(cv, poly):
    """Solid black inside poly, as overlapping 1.5 px rules (clipped by the Canvas like any line)."""
    cv.heavy(C.hatch_poly(poly, 0, 1.))


def _tone_lines(x0, x1, y0f, y1f, dark, vertical=True):
    """Lines across a form shaded by dark(u) (u 0..1 across): pitch 1.5 / 2 / 3 by tone, none in
    the highlight. y0f(x), y1f(x) give each line's ends (for vertical lines)."""
    out = []
    x = x0 + .75
    while x < x1:
        u = (x - x0) / max(1e-6, x1 - x0)
        d = dark(u)
        p = 1.5 if d > .66 else 2. if d > .4 else 3.
        if d > .14:
            a, b = y0f(x), y1f(x)
            if b - a > .8:
                out.append([(x, a), (x, b)] if vertical else [(a, x), (b, x)])
        x += p
    return out


def _cyl(u, light=.3):
    """Shading across a cylinder: light near `light`, dark at the shadow edge."""
    return min(1., abs(u - light) * 1.9 + (.25 if u > light else 0.))


# ------------------------------------------------------------------------------------------
# the stage
# ------------------------------------------------------------------------------------------

_BASS = [(0.09, -0.30), (0.15, -0.40), (0.22, -0.52), (0.29, -0.49), (0.33, -0.32), (0.33, -0.12),
         (0.31, 0.02), (0.38, 0.18), (0.43, 0.36), (0.40, 0.53), (0.25, 0.63), (0.0, 0.66), (-0.25, 0.62),
         (-0.41, 0.50), (-0.45, 0.30), (-0.40, 0.10), (-0.35, -0.03), (-0.37, -0.25), (-0.39, -0.47),
         (-0.35, -0.67), (-0.27, -0.63), (-0.19, -0.46), (-0.09, -0.30)]


def _bass(cv, x, y, s, ang):
    """Six-string bass standing on its stand: body centre (x, y), body length s, tilted ang."""
    T = lambda pts: _xf(pts, x, y, s, ang)
    # stand: two splayed legs behind the body and a cradle
    cv.obj([T([(-.42, .55), (-.36, .55), (-.6, 1.0), (-.66, 1.0)]), T([(.36, .55), (.42, .55), (.66, 1.0), (.6, 1.0)])], .5)
    cv.line([T([(-.63, 1.0), (-.39, .55)]), T([(.63, 1.0), (.39, .55)])])
    # neck and headstock
    nk = T([(-.07, -.3), (.07, -.3), (.055, -1.75), (-.055, -1.75)])
    hd = T(_cr([(-.06, -1.74), (.06, -1.74), (.13, -1.95), (.12, -2.18), (.0, -2.24), (-.12, -2.2), (-.1, -1.95)], 4))
    cv.obj([hd], 1.)
    cv.hair(_hatch_where(hd, math.degrees(ang) + 90, 1.5, lambda px, py: True))
    for j in range(3):
        for sd in (-1, 1):
            px, py = T([(sd * .14, -1.9 - j * .1)])[0]
            pg = _ell(px, py, s * .028, s * .028, 10)
            cv.obj([pg], 1.)
    cv.obj([nk], 1.)
    # rosewood board with grain, fret wires and inlay dots
    for k in range(-2, 3):
        cv.hair([T([(k * .022, -.32), (k * .02, -1.73)])])
    for f in range(1, 22):
        yy = -1.75 + 1.43 * (1 - 2 ** (-f / 12)) * 1.9
        if yy > -.33:
            break
        cv.line([T([(-.06, yy), (.06, yy)])])
    # body
    body = T(_cr(_BASS, 6))
    cv.obj([body], 1.5)
    bev = T(_cr([(px * .9, py * .9 + .01) for px, py in _BASS], 6))
    cv.hair([bev + [bev[0]]])
    # body shading: dark on the side away from the light, wood figure on the face
    keep = lambda px, py: (((px - x) * math.cos(ang) + (py - y) * math.sin(ang)) / s > .05) or \
        not _inside(bev, px, py)
    cv.hair(_hatch_where(body, math.degrees(ang) + 80, 2., keep))
    keep2 = lambda px, py: (((px - x) * math.cos(ang) + (py - y) * math.sin(ang)) / s > .22)
    cv.hair(_hatch_where(body, math.degrees(ang) - 10, 2., keep2))
    # flame figure: wavy lines across the lit half
    for k in range(7):
        yy = -.15 + k * .1
        pl = [(xx, yy + .025 * math.sin(xx * 23 + k)) for xx in [-.36 + i * .03 for i in range(14)]]
        pl = [p for p in pl if _inside(_BASS, p[0] * 1.12, p[1] * 1.08)]
        if len(pl) > 1:
            cv.hair([T(pl)])
    # pickguard, pickups, bridge, knobs
    pg = T(_cr([(-.08, -.3), (.08, -.3), (.24, -.42), (.27, -.2), (.2, .08), (.05, .2), (-.18, .18),
                (-.27, -.02), (-.3, -.3), (-.24, -.5), (-.14, -.42)], 4))
    cv.obj([pg], 1.)
    cv.hair(_hatch_where(pg, math.degrees(ang) + 45, 3., lambda px, py: True))
    for py0 in (-.12, .12):
        pu = T([(-.17, py0 - .045), (.17, py0 - .045), (.17, py0 + .045), (-.17, py0 + .045)])
        cv.obj([pu], 1.)
        _solid(cv, pu)
    br = T([(-.15, .32), (.15, .32), (.15, .41), (-.15, .41)])
    cv.obj([br], 1.)
    cv.hair(_hatch_where(br, math.degrees(ang), 1.5, lambda px, py: True))
    for kx, ky in ((.24, .3), (.3, .42), (.18, .5)):
        px, py = T([(kx, ky)])[0]
        kn = _ell(px, py, s * .035, s * .035, 12)
        cv.obj([kn], 1.)
        cv.hair(C.hatch_poly(kn, 90, 1.5))
    # six strings, nut to bridge
    for k in range(6):
        u = (k - 2.5) / 2.5
        cv.hair([T([(u * .045, -1.75), (u * .12, .36)])])


def _kick(cv, cx, cy, R, rng, mono=True):
    """Bass drum, front head facing us, with Parker's P on it."""
    rim = _ell(cx, cy, R, R, 64)
    cv.obj([rim], 1.5)
    hoop_in = _ell(cx, cy, R * .86, R * .86, 64)
    # hoop: knurled wood ring
    ring = lambda px, py: (px - cx) ** 2 + (py - cy) ** 2 > (R * .86) ** 2
    cv.hair(_hatch_where(rim, 60, 1.5, ring))
    cv.line([hoop_in + [hoop_in[0]]])
    # lugs round the hoop
    for i in range(10):
        a = TAU * (i + .5) / 10
        c, s = math.cos(a), math.sin(a)
        lug = [(cx + c * R * .8 - s * R * .05, cy + s * R * .8 + c * R * .05),
               (cx + c * R * 1.04 - s * R * .05, cy + s * R * 1.04 + c * R * .05),
               (cx + c * R * 1.04 + s * R * .05, cy + s * R * 1.04 - c * R * .05),
               (cx + c * R * .8 + s * R * .05, cy + s * R * .8 - c * R * .05)]
        cv.obj([lug], 1.)
        cv.hair([[lug[0], lug[1]]])
    # head: shaded crescent on the lower right (the drum is lit from upper left)
    head = _ell(cx, cy, R * .84, R * .84, 56)
    cv.obj([head], .5)
    ox, oy = cx - R * .2, cy - R * .2
    keep = lambda px, py: (px - ox) ** 2 + (py - oy) ** 2 > (R * .78) ** 2
    cv.hair(_hatch_where(head, 45, 2., keep))
    keep = lambda px, py: (px - ox) ** 2 + (py - oy) ** 2 > (R * .9) ** 2
    cv.hair(_hatch_where(head, -45, 2., keep))
    # the coated head's light grain, everywhere but inside the monogram ring
    mr = R * .62 * .62 if mono else 0.
    cv.hair(_hatch_where(head, 0, 3., lambda px, py: (px - cx) ** 2 + (py - cy) ** 2 > (mr + 1.5) ** 2))
    if mono:
        cv.hair(_hatch_where(head, 45, 3., lambda px, py: (px - cx) ** 2 + (py - cy) ** 2 < (mr - 1) ** 2))
    if mono:
        _monogram(cv, cx, cy, R * .62)


def _monogram(cv, cx, cy, s):
    """An engraved Roman P with a swash tail, in a beaded ring."""
    ring = _ell(cx, cy, s * .62, s * .62, 48)
    cv.line([ring + [ring[0]]])
    for i in range(24):
        a = TAU * i / 24
        cv.line([[(cx + math.cos(a) * s * .7, cy + math.sin(a) * s * .7),
                  (cx + math.cos(a) * s * .72, cy + math.sin(a) * s * .72)]])
    h = s * .8
    x0 = cx - h * .26
    stem = [(x0 - h * .07, cy - h * .5), (x0 + h * .07, cy - h * .5), (x0 + h * .06, cy + h * .44),
            (x0 - h * .06, cy + h * .44)]
    _solid(cv, stem)
    cv.line([[(x0 - h * .16, cy - h * .5), (x0 + h * .12, cy - h * .5)],
             [(x0 - h * .16, cy + h * .45), (x0 + h * .16, cy + h * .45)]])
    bx, by = x0 + h * .1, cy - h * .2
    outer = [(x0, cy - h * .5)] + [(bx + h * .3 * math.cos(a), by + h * .3 * math.sin(a))
                                   for a in [-PI / 2 + PI * i / 16 for i in range(17)]] + [(x0, cy + h * .1)]
    inner = [(bx + h * .16 * math.cos(a), by + h * .19 * math.sin(a)) for a in [PI / 2 - PI * i / 16 for i in range(17)]]
    bowl = outer + [(x0 + h * .06, cy + h * .1 - h * .01)] + inner + [(x0 + h * .06, cy - h * .39)]
    _solid(cv, bowl)
    # swash curling out of the stem foot into a little volute
    sw = [(x0 + h * .06 + h * .5 * t, cy + h * .44 - h * .14 * math.sin(PI * t)) for t in [i / 10 for i in range(11)]]
    ex, ey = sw[-1]
    sw += [(ex + h * .07 * math.cos(a) * (1 - (a + PI / 2) / 9), ey - h * .07 + h * .07 * math.sin(a) * (1 - (a + PI / 2) / 9))
           for a in [PI / 2 - i * .5 for i in range(1, 13)]]
    cv.line([sw])


def _tom(cv, cx, cy, rx, hgt, ang=0.):
    """A rack tom: elliptical top head with hoop, shaded shell below."""
    ry = rx * .35
    top = _ell(cx, cy, rx, ry, 40)
    shell = [(cx - rx, cy)] + [(cx + rx * math.cos(a), cy + hgt + ry * math.sin(a)) for a in [PI - PI * i / 20 for i in range(21)][::-1]][::-1]
    shell = [(cx - rx, cy), (cx - rx, cy + hgt)] + [(cx - rx * math.cos(PI * i / 20), cy + hgt + ry * math.sin(PI * i / 20)) for i in range(21)] + [(cx + rx, cy)]
    cv.obj([shell], 1.)
    cv.hair(_tone_lines(cx - rx, cx + rx, lambda x: cy, lambda x: cy + hgt + ry * math.sqrt(max(0, 1 - ((x - cx) / rx) ** 2)) - .5,
                        lambda u: _cyl(u, .3)))
    cv.obj([top], 1.)
    cv.hair([_ell(cx, cy, rx * .86, ry * .8, 32)])
    for i in range(6):
        a = PI * (i + .5) / 6
        px = cx - rx * math.cos(a)
        cv.line([[(px, cy + ry * math.sin(a)), (px, cy + ry * math.sin(a) + hgt * .45)]])


def _cymbal(cv, cx, cy, r, tilt=.22, stand_to=None):
    if stand_to is not None:
        cv.obj([_rect(cx - .9, cy, cx + .9, stand_to)], .5)
        cv.line([[(cx - .9, cy), (cx - .9, stand_to)], [(cx + .9, cy), (cx + .9, stand_to)]])
        for sd in (-1, 1):
            cv.line([[(cx, stand_to - r * .5), (cx + sd * r * .6, stand_to)]])
    ry = r * tilt
    disc = _ell(cx, cy, r, ry, 48)
    cv.obj([disc], 1.)
    # lathe grooves: tight concentric ellipses, darker toward the rim on the far side
    k = .95
    while k > .2:
        e = _ell(cx, cy - ry * .1 * (1 - k), r * k, ry * k, 40)
        cv.hair([e + [e[0]]])
        k -= .085 if k > .6 else .12
    bell = _ell(cx, cy - ry * .25, r * .16, ry * .5, 20)
    cv.obj([bell], 1.)
    cv.hair(C.hatch_poly(bell, 90, 1.5))
    cv.line(C.hatch_poly([p for p in disc if p[1] > cy], 0, 2.))


def _amp(cv, x0, y0, x1, y1, rng):
    """A stack: head with knobs on a 2x2 speaker cabinet, tolex ruled, grille cross-hatched."""
    W, H = x1 - x0, y1 - y0
    hy = y0 + H * .2
    head = _rect(x0 + W * .03, y0, x1 - W * .03, hy)
    cv.obj([head], 1.)
    cv.hair(_tone_lines(x0, x1, lambda x: y0 + .6, lambda x: hy - .6, lambda u: .45))
    pnl = _rect(x0 + W * .12, y0 + H * .05, x1 - W * .12, hy - H * .05)
    cv.obj([pnl], 1.)
    for i in range(5):
        kx = x0 + W * (.22 + .14 * i)
        kn = _ell(kx, (y0 + hy) / 2, H * .022, H * .022, 10)
        cv.obj([kn], .5)
        _solid(cv, kn)
    cab = _rect(x0, hy, x1, y1)
    cv.obj([cab], 1.5)
    cv.hair(_tone_lines(x0, x1, lambda x: hy + .7, lambda x: y1 - .7, lambda u: _cyl(u, .25)))
    g = _rect(x0 + W * .08, hy + H * .05, x1 - W * .08, y1 - H * .05)
    cv.obj([g], 1.)
    cv.hair(C.hatch_poly(g, 45, 2.) + C.hatch_poly(g, -45, 2.))
    gw, gh = W * .84, (y1 - hy) - H * .1
    r = min(gw, gh) * .23
    for i in range(2):
        for j in range(2):
            sx = x0 + W * .08 + gw * (.27 + .46 * i)
            sy = hy + H * .05 + gh * (.27 + .46 * j)
            cone = _ell(sx, sy, r, r, 32)
            cv.obj([cone], 1.)
            for k in (.82, .62):
                e = _ell(sx, sy, r * k, r * k, 28)
                cv.hair([e + [e[0]]])
            keep = lambda px, py, sx=sx, sy=sy: (px - sx + r * .25) ** 2 + (py - sy + r * .25) ** 2 > (r * .8) ** 2
            cv.hair(_hatch_where(cone, 45, 2., keep))
            cap = _ell(sx, sy, r * .26, r * .26, 14)
            cv.obj([cap], .5)
            _solid(cv, cap)


def _mic(cv, x, ybase, ytop, s):
    """Microphone on a boom stand."""
    cv.obj([_rect(x - .8, ytop, x + .8, ybase)], .5)
    cv.line([[(x - .8, ytop), (x - .8, ybase)], [(x + .8, ytop), (x + .8, ybase)]])
    for sd in (-1, 1):
        cv.line([[(x, ybase - s * .5), (x + sd * s * .9, ybase)]])
    bx, by = x + s * 1.3, ytop - s * .7
    cv.line([[(x, ytop), (bx, by)]])
    a = math.atan2(by - ytop, bx - x)
    grill = _ell(bx + math.cos(a) * s * .3, by + math.sin(a) * s * .3, s * .32, s * .32, 20)
    cv.obj([grill], 1.)
    cv.hair(C.hatch_poly(grill, 45, 1.5) + C.hatch_poly(grill, -45, 1.5))


def _sticks(cv, cx, cy, L, a1=-.95, a2=-2.2):
    """Crossed drumsticks with turned tips."""
    for a in (a1, a2):
        c, s = math.cos(a), math.sin(a)
        p0 = (cx - c * L * .5, cy - s * L * .5)
        p1 = (cx + c * L * .5, cy + s * L * .5)
        w0, w1 = L * .045, L * .026
        nx, ny = -s, c
        stick = [(p0[0] + nx * w0, p0[1] + ny * w0), (p1[0] + nx * w1, p1[1] + ny * w1),
                 (p1[0] - nx * w1, p1[1] - ny * w1), (p0[0] - nx * w0, p0[1] - ny * w0)]
        cv.obj([stick], 1.)
        cv.hair([[(p0[0] - nx * w0 * k, p0[1] - ny * w0 * k), (p1[0] - nx * w1 * k, p1[1] - ny * w1 * k)] for k in (.25, .5, .72)])
        tip = _ell(p1[0] + c * L * .03, p1[1] + s * L * .03, L * .035, L * .022, 12)
        tip = [(p1[0] + c * L * .03 + (px - p1[0] - c * L * .03) * c - (py - p1[1] - s * L * .03) * s,
                p1[1] + s * L * .03 + (px - p1[0] - c * L * .03) * s + (py - p1[1] - s * L * .03) * c) for px, py in tip]
        cv.obj([tip], 1.)
        cv.hair(C.hatch_poly(tip, math.degrees(a) + 90, 1.5))


def _curtain(cv, x0, x1, y0, y1, side, rng):
    """Side drape: folds as dense/sparse vertical rules, gathered to a tie-back."""
    W = x1 - x0
    ty = y0 + (y1 - y0) * .62
    def edge(y):
        # inner edge swings toward the tie-back then flares out at the floor
        t = (y - y0) / (y1 - y0)
        pinch = .55 * math.exp(-((t - .62) / .16) ** 2)
        return W * (1 - pinch)
    poly = []
    n = 24
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        poly.append((x0 + edge(y) if side < 0 else x1 - edge(y), y))
    if side < 0:
        poly = [(x0 - 2, y0), ] + poly + [(x0 - 2, y1)]
    else:
        poly = [(x1 + 2, y0)] + poly + [(x1 + 2, y1)]
    cv.obj([poly], 1.5)
    nf = max(3, int(W / 9))
    lines = []
    for k in range(int(W / 1.5)):
        u = k / (W / 1.5)
        ph = (u * nf) % 1
        d = .5 + .5 * math.cos(ph * TAU)
        if d < .3 and k % 2:
            continue
        if d < .55 and k % 3 == 1:
            continue
        pl = []
        for i in range(n + 1):
            y = y0 + (y1 - y0) * i / n
            e = edge(y)
            xx = x0 + u * e if side < 0 else x1 - u * e
            pl.append((xx, y))
        lines.append(pl)
    cv.hair(lines)
    # tie-back cord with tassel
    tx = x0 + edge(ty) * .5 if side < 0 else x1 - edge(ty) * .5
    cv.heavy([[(tx - edge(ty) * .6, ty - 2), (tx + edge(ty) * .6, ty + 2)]])
    tas = [(tx, ty), (tx + 3, ty + 9), (tx - 3, ty + 9)]
    cv.obj([tas], 1.)
    cv.hair([[(tx + i * .9, ty + 2), (tx + i * 1.2, ty + 9)] for i in (-2, -1, 0, 1, 2)])


def _valance(cv, x0, x1, y0, hh, rng):
    """Scalloped pelmet across the top with gathered folds and a fringe."""
    W = x1 - x0
    ns = max(3, int(round(W / 55)))
    sw = W / ns
    poly = [(x0 - 2, y0 - 2), (x1 + 2, y0 - 2)]
    bottom = []
    for i in range(ns * 16 + 1):
        x = x1 - W * i / (ns * 16)
        t = ((x - x0) / sw) % 1
        bottom.append((x, y0 + hh * (.62 + .38 * math.sin(PI * t))))
    poly += bottom
    cv.obj([poly], 1.5)
    lines = []
    for k in range(int(W / 1.5)):
        x = x0 + k * 1.5
        t = ((x - x0) / sw) % 1
        d = abs(math.sin(PI * t * 3))
        if d < .3 and k % 2:
            continue
        yb = y0 + hh * (.62 + .38 * math.sin(PI * t)) - 1
        lines.append([(x, y0), (x, yb)])
    cv.hair(lines)
    cv.line([[(x0, y0 + hh * .16), (x1, y0 + hh * .16)]])
    # fringe of tassel cords on each swag
    fr = []
    for p in bottom[::2]:
        fr.append([p, (p[0], p[1] + 2.5)])
    cv.line(fr)


def _truss(cv, x0, x1, y, hh, lamps):
    """Lighting truss: two chords with zig-zag lacing; the lamps hang beneath."""
    cv.obj([_rect(x0, y, x1, y + hh)], 1.)
    zz = []
    n = int((x1 - x0) / hh)
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        zz.append([(xa, y + hh if i % 2 else y), (xb, y if i % 2 else y + hh)])
    cv.hair(zz)
    cv.line([[(x0, y + hh * .5), (x1, y + hh * .5)]])
    for lx, ang in lamps:
        c, s = math.cos(ang), math.sin(ang)
        L, r0, r1 = hh * 2.4, hh * .55, hh * .85
        cx, cy = lx, y + hh + hh * .3
        can = [(cx - s * r0, cy + c * r0 * 0 - c * 0), ]
        nx, ny = -s, c
        p0 = (cx, cy)
        p1 = (cx + c * L, cy + s * L)
        can = [(p0[0] + nx * r0, p0[1] + ny * r0), (p1[0] + nx * r1, p1[1] + ny * r1),
               (p1[0] - nx * r1, p1[1] - ny * r1), (p0[0] - nx * r0, p0[1] - ny * r0)]
        cv.obj([can], 1.)
        _solid(cv, can)
        lens = [(p1[0] + nx * r1, p1[1] + ny * r1), (p1[0] + nx * r1 + c * 1.5, p1[1] + ny * r1 + s * 1.5),
                (p1[0] - nx * r1 + c * 1.5, p1[1] - ny * r1 + s * 1.5), (p1[0] - nx * r1, p1[1] - ny * r1)]
        cv.obj([lens], 1.)
        cv.line([[(cx, y + hh), (cx, cy)]])


def _crowd(x0, x1, ytop, ybot, rng):
    """Front rows in black silhouette, rimmed with white where the stage light catches them."""
    W = x1 - x0
    blk = []
    rims = []
    r = max(5., min(11., (ybot - ytop) * .32))
    for row in range(2):
        yy = ybot - r * (1.2 if row == 0 else .2) + (r * .4 if row else 0)
        x = x0 - r * rng.random() - (r * .9 if row else 0)
        while x < x1 + r:
            hr = r * (.85 + .3 * rng.random()) * (1.12 if row else 1.)
            hy = yy - hr * (1.4 + .3 * rng.random())
            head = _ell(x, hy, hr * .78, hr, 18)
            sh = [(x - hr * 1.9, ybot + 2), (x - hr * 1.7, hy + hr * 1.5), (x - hr * .5, hy + hr * .9),
                  (x + hr * .5, hy + hr * .9), (x + hr * 1.7, hy + hr * 1.5), (x + hr * 1.9, ybot + 2)]
            blk += [head, sh]
            if row == 0:
                rims.append(_ell(x, hy, hr * .78 - .9, hr - .9, 18)[13:18])
            if rng.random() < .3 and row == 0:
                sd = 1 if rng.random() < .5 else -1
                ax = x + sd * hr * 1.4
                hx, hy2 = ax + sd * hr * .8, hy - hr * 2.6
                arm = [(ax - hr * .3, hy + hr * 1.4), (hx - hr * .25, hy2), (hx + hr * .25, hy2), (ax + hr * .3, hy + hr * 1.4)]
                blk.append(arm)
                # devil horns or open hand
                if rng.random() < .5:
                    blk.append([(hx - hr * .3, hy2 + 1), (hx - hr * .28, hy2 - hr * .8), (hx - hr * .12, hy2 - hr * .8), (hx - hr * .1, hy2 + 1)])
                    blk.append([(hx + hr * .1, hy2 + 1), (hx + hr * .14, hy2 - hr * .8), (hx + hr * .3, hy2 - hr * .8), (hx + hr * .3, hy2 + 1)])
                    blk.append(_ell(hx, hy2 + hr * .1, hr * .38, hr * .3, 10))
                else:
                    blk.append(_ell(hx, hy2 - hr * .1, hr * .4, hr * .45, 10))
            x += hr * (2.3 + rng.random() * .9)
    d = "".join(_d(p, True, .3) for p in blk)
    rd = "".join(_d(p, False, .2) for p in rims)
    return (f'<path d="{d}" fill="#000" stroke="none"/>'
            f'<path d="{rd}" fill="none" stroke="#fff" stroke-width=".5"/>')


def stage(X, Y, W, H, seed=0, crowd=True, fine=1.):
    """The whole concert vignette in the box X, Y, W, H (clip it to the field outside)."""
    rng = random.Random(seed)
    o = []
    # dark hall behind
    o.append(C.dark_ground((X - 2, Y - 2, W + 4, H + 4), "G"))
    vh = H * .085
    cwid = W * .12
    yf = Y + H * .62          # back edge of the stage floor
    yfront = Y + H * .86      # stage lip
    ty = Y + vh * 1.1
    th = max(4., H * .022)
    lamps = [(X + W * .3, 1.95), (X + W * .5, PI / 2), (X + W * .7, 1.19)]
    # light beams (white with a fine rule, so they glow against the hall)
    beams = []
    cx = X + W * .5
    targets = [(cx - W * .1, W * .16), (cx, W * .2), (cx + W * .15, W * .17)]
    for (lx, a), (tx, tw) in zip(lamps, targets):
        ly = ty + th * 2.6
        beams.append([(lx - 2, ly), (lx + 2, ly), (tx + tw / 2, yfront), (tx - tw / 2, yfront)])
    bd = "".join(_d(b, True, 0) for b in beams)
    o.append(f'<path d="{bd}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{bd}" fill="{pat("L")}" stroke="none"/>')
    cv = C.Canvas()
    # stage floor: boards running to a vanishing point, lit pools where the beams land
    floor = [(X - 2, yf), (X + W + 2, yf), (X + W + 2, yfront), (X - 2, yfront)]
    cv.obj([floor], 1.)
    vx, vy = cx, yf - H * .9
    bl = []
    for i in range(-30, 31):
        xb = cx + i * W / 22
        t0 = 0.
        p0 = (vx + (xb - vx) * ((yf - vy) / (yfront - vy)), yf)
        bl.append([p0, (xb, yfront)])
    cv.line(bl)
    pools = [((tx), (yf + yfront) / 2 + H * .04, tw * .62) for tx, tw in targets]
    def dark_floor(px, py):
        for (qx, qy, qr) in pools:
            if ((px - qx) / qr) ** 2 + ((py - qy) / (qr * .28)) ** 2 < 1:
                return False
        return True
    cv.hair(C.hatch_poly(floor, 0, 3.))
    cv.hair([r for seg in C.hatch_poly(floor, 0, 3., 1.5) for r in _run_keep(seg, dark_floor)])
    # stage lip moulding
    lip = _rect(X - 2, yfront, X + W + 2, yfront + H * .03)
    cv.obj([lip], 1.)
    cv.hair(C.hatch_poly(lip, 0, 1.5))
    # amp stacks
    aw = W * .19
    ah = H * .36
    _amp(cv, X + cwid * .55, yf + H * .04 - ah, X + cwid * .55 + aw, yf + H * .04, rng)
    _amp(cv, X + W - cwid * .55 - aw, yf + H * .04 - ah, X + W - cwid * .55, yf + H * .04, rng)
    # drum kit
    R = min(W * .15, H * .14)
    kx, ky = cx - W * .04, yf + H * .03 - R
    _cymbal(cv, kx - R * 1.75, ky - R * 1.25, R * .72, .24, yf + H * .05)
    _cymbal(cv, kx + R * 1.8, ky - R * 1.0, R * .85, .2, yf + H * .06)   # the ride
    _tom(cv, kx - R * .55, ky - R * 1.15, R * .45, R * .38)
    _tom(cv, kx + R * .55, ky - R * 1.1, R * .5, R * .42)
    _kick(cv, kx, ky, R, rng)
    _sticks(cv, kx - R * 1.2, ky + R * .7, R * 1.25)
    # mic at the front
    _mic(cv, cx - W * .26, yfront - H * .02, yf - H * .1, W * .025)
    # Thundercat's six-string on its stand
    bs = H * .19
    _bass(cv, cx + W * .21, yfront - H * .02 - bs * 1.0, bs, .16)
    # curtains and pelmet frame it all
    _curtain(cv, X - 2, X + cwid, Y + vh * .5, yfront + 1, -1, rng)
    _curtain(cv, X + W - cwid, X + W + 2, Y + vh * .5, yfront + 1, 1, rng)
    _truss(cv, X + cwid * .6, X + W - cwid * .6, ty, th, lamps)
    _valance(cv, X - 2, X + W + 2, Y - 2, vh, rng)
    o.append(cv.svg())
    if crowd:
        o.append(_crowd(X - 4, X + W + 4, Y + H * .8, Y + H + 2, rng))
    return "".join(o)


# ------------------------------------------------------------------------------------------
# the frame (house layouts, adapted so no blank paper survives)
# ------------------------------------------------------------------------------------------

def _field_vignette(cx, cy, cw, ch, inner_d, seed, uid, crowd=True):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    body = stage(cx - a, cy - b, 2 * a, 2 * b, seed, crowd)
    return f'<clipPath id="{uid}"><path d="{inner_d}"/></clipPath><g clip-path="url(#{uid})">{body}</g>'


def _staff(cv, pts, gap, notes=True, seed=0, lines=True):
    """Five staff lines following centre polyline pts, with a bar of swung ride rhythm."""
    def at(u, off):
        n = len(pts) - 1
        f = u * n
        i = min(n - 1, int(f))
        t = f - i
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        return (x0 + dx * t - dy / L * off, y0 + dy * t + dx / L * off)
    for k in ((-2, -1, 0, 1, 2) if lines else ()):
        cv.hair([[at(i / 60, k * gap) for i in range(61)]])
    if not notes:
        return
    # ding . ding-a ding . ding-a : quarter, swung pair (beamed, triplet feel), repeated, bar lines
    seq = [(.06, 'bar'), (.13, 'q', 1), (.22, 'e', 0), (.28, 'e', 1), (.37, 'q', 1), (.46, 'e', 0), (.52, 'e', 1),
           (.6, 'bar'), (.67, 'q', 1), (.76, 'e', 0), (.82, 'e', 1), (.9, 'q', 1), (.96, 'bar')]
    prev = None
    for item in seq:
        u = item[0]
        if item[1] == 'bar':
            cv.line([[at(u, -2 * gap), at(u, 2 * gap)]])
            continue
        ln = item[2]
        hx, hy = at(u, -ln * gap * .5 + gap * .5)
        head = [(hx + gap * .62 * math.cos(a) * math.cos(-.4) - gap * .44 * math.sin(a) * math.sin(-.4),
                 hy + gap * .62 * math.cos(a) * math.sin(-.4) + gap * .44 * math.sin(a) * math.cos(-.4)) for a in [TAU * i / 12 for i in range(12)]]
        cv.obj([head], .5)
        _solid(cv, head)
        top = at(u + .011, -(3.2 if lines else 2.6) * gap)
        sx = (hx + gap * .55, hy)
        cv.line([[sx, (sx[0], top[1])]])
        if item[1] == 'e':
            if prev is not None:
                cv.heavy([[prev, (sx[0], top[1])]])
                prev = None
            else:
                prev = (sx[0], top[1])


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(_clip(_uid("b", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    # inside the medallion: the kick drum with the P, drumsticks crossed behind it
    uid = _uid("bm", w, h, seed)
    cv = C.Canvas()
    R = ry - 6
    _sticks(cv, cx, cy + 2, rx * 1.75, -.62, -PI + .62)
    _kick(cv, cx, cy, R, random.Random(seed), True)
    inner = _ell(cx, cy, rx - 2.2, ry - 2.2, 64)
    o.append(f'<clipPath id="{uid}"><path d="{_d(inner, True, 0)}"/></clipPath><g clip-path="url(#{uid})">'
             f'{C.dark_ground((cx - rx, cy - ry, 2 * rx, 2 * ry), "M")}{cv.svg()}</g>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
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
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_vignette(cx, cy, cw, gh + 4, inner_d, seed, _uid("mv", w, h, seed), gh > 130))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # a light ruled tint over all the paper the frame leaves (no blank white anywhere)
    o.append(f'<path d="M0,{_n(top_free * .35)}h{_n(w)}V{_n(h)}H0z" fill="{pat("L")}" stroke="none"/>')
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .52, ph * .66
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
    o.append(_clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_vignette(cx, cy, cw, ch, inner_d, seed, _uid("tv", w, h, seed), True))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    sc = C.Canvas()
    _staff(sc, centre, bh * .13, True, lines=False)
    o.append(sc.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, tth) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet carries a bar of swing ride rhythm, engraved
    tc = C.Canvas()
    _staff(tc, [(tx + 6, ty + tth / 2), (tx + tw - 6, ty + tth / 2)], min(2.5, tth * .14), True)
    o.append(tc.svg())
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(_clip(_uid("f", w, h, seed), 0, fy, w, fh - 2,
                       C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
