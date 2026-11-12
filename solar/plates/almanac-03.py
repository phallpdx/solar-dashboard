"""almanac-03 "Local history" (History near home: Pier Park, St. Johns, Cathedral Park, Sauvie Island).

The plate engraves the St. Johns Bridge (1931) over the Willamette: its two Gothic towers with
stacked lancets, the cables and suspenders, the cathedral arches of Cathedral Park under the east
approach, the Forest Park hills of firs on the west bank, Pier Park's evergreens, Mt. Hood behind,
the moon of the day. Easter egg: a great blue heron from Sauvie Island fishing in the shallows.
House frame from engraving_codex (shaded acanthus volutes on a cut-away ruled ground).
"""
import sys
import math
import random
import datetime
import engraving_codex as C
import engraving_morning as M

_n, _d, _ell = C._n, C._d, C._ell_pts
PI = math.pi


def _hy(y):
    """Snap a horizontal 0.5 px line onto the device grid (k*.5 + .25)."""
    return math.floor(y * 2) / 2 + .25


def _clipped(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _black(polys):
    d = "".join(_d(p, True, 0) for p in polys if len(p) > 2)
    return f'<path d="{d}" fill="#000" stroke="none"/>' if d else ""


def _hlines(x0, x1, y0, y1, pitch, rng=None, dash=None, gap=(2, 5)):
    """Horizontal hairlines on the device grid; with dash=(a, b) broken into dashes."""
    out = []
    y = _hy(y0)
    while y <= y1:
        if dash and rng:
            x = x0 - rng.uniform(0, dash[1])
            while x < x1:
                L = rng.uniform(*dash)
                a, b = max(x, x0), min(x + L, x1)
                if b - a > .8:
                    out.append([(a, y), (b, y)])
                x += L + rng.uniform(*gap)
        else:
            out.append([(x0, y), (x1, y)])
        y += pitch
    return out


def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    return ((d - datetime.date(2000, 1, 6)).days % 29.530588) / 29.530588


def _moon(cv, cx, cy, r, phase):
    disc = _ell(cx, cy, r, r, 28)
    cv.obj([disc], .5)
    # terminator: the unlit part gets dense hatch
    k = math.cos(phase * 2 * PI)   # 1 new .. -1 full
    waxing = phase < .5
    dark = []
    for i in range(29):
        t = -PI / 2 + PI * i / 28
        dark.append((cx + (-1 if waxing else 1) * r * math.cos(t), cy + r * math.sin(t)))
    for i in range(29):
        t = PI / 2 - PI * i / 28
        dark.append((cx + (-1 if waxing else 1) * r * k * math.cos(t) * (1 if True else 1), cy + r * math.sin(t)))
    if abs(k) < .98 or k > 0:
        cv.hair(C.hatch_poly(dark, 0, 1.5, .25))
    cv.hair(C.hatch_poly(disc, 45, 3))


def _lancet(x, y0, y1, hw):
    """Pointed (Gothic) opening: x centre, y0 apex..y1 sill, half width hw."""
    spring = y0 + hw * 1.7
    pts = [(x - hw, y1), (x + hw, y1), (x + hw, spring)]
    for i in range(1, 9):
        t = i / 9
        pts.append((x + hw * (1 - t) ** 1.25, spring - (spring - y0) * math.sin(t * PI / 2)))
    pts.append((x, y0))
    for i in range(8, 0, -1):
        t = i / 9
        pts.append((x - hw * (1 - t) ** 1.25, spring - (spring - y0) * math.sin(t * PI / 2)))
    pts.append((x - hw, spring))
    return pts


def _fir(cv, x, base, h, rng, lit=-1, dark=1):
    """A Douglas fir in layered drooping tiers, painted bottom-up so each tier overlaps the one
    below; every tier is ruled dark underneath, needle-hatched, with a white upper edge."""
    tiers = max(3, int(h / 8.5))
    w = h * .3
    top = base - h * .93
    trunk = [(x - w * .07, base - h * .12), (x + w * .07, base - h * .12), (x + w * .09, base), (x - w * .09, base)]
    cv.obj([trunk], .5)
    cv.hair(C.hatch_poly(trunk, 90, 1.5, .25))
    for i in range(tiers - 1, -1, -1):
        t0, t1 = i / tiers, (i + 1) / tiers
        ya = top + (base - h * .1 - top) * t0 * .96
        yb = top + (base - h * .1 - top) * t1
        wi = w * (.18 + .82 * t1 ** .9) * rng.uniform(.88, 1.08)
        dr = (yb - ya) * .55
        shape = [(x, ya - (yb - ya) * .15)]
        pts = []
        for k in range(1, 6):
            u = k / 5
            pts.append((x + wi * u, ya + (yb - ya) * u * .8 + dr * u ** 3))
        pts.append((x + wi * .82, yb + dr * .4))
        pts.append((x + wi * .55, yb - (yb - ya) * .1 + dr * .35))
        pts.append((x + wi * .25, yb - (yb - ya) * .05))
        shape += pts
        shape.append((x, yb - (yb - ya) * .18))
        shape += [(2 * x - px, py) for px, py in reversed(pts)]
        cv.obj([shape], .5)
        under = [(x - wi, ya + (yb - ya) * .45), (x + wi, ya + (yb - ya) * .45), (x + wi, yb + dr), (x - wi, yb + dr)]
        cv.hair(_clip_lines(C.hatch_poly(shape, 0, 1.5, .25), lambda p, y0=ya + (yb - ya) * (.45 if dark else .65): p[1] > y0))
        shade = [(x, ya)] + [(x - lit * wi * u, ya + (yb - ya) * u * .8 + dr * u ** 3) for u in (.25, .5, .75, 1.)] + [(x - lit * wi * .5, yb + dr), (x, yb)]
        cv.hair(C.hatch_poly(shade, 135 if lit < 0 else 45, 2))
        # needle strokes fanning down from the stem on the lit side
        nd = []
        for k in range(1, 5):
            u = k / 5
            px, py = x + lit * wi * u * .9, ya + (yb - ya) * u * .8 + dr * u ** 3
            nd.append([(x + lit * wi * u * .3, ya + (yb - ya) * (u * .3 + .25)), (px, py - 1)])
        cv.hair(nd)
    cv.obj([], 0)


def _clip_lines(lines, keep):
    """Keep the hatch segments whose midpoint passes keep(pt)."""
    return [l for l in lines if keep(((l[0][0] + l[-1][0]) / 2, (l[0][1] + l[-1][1]) / 2))]


# great blue heron, facing left, feet at the origin (about 44 units tall); from engraving_morning
_HERON_BODY = [
    [(-20, -40.2), (-15, -40.6), (-11.8, -41.6)],
    [(-11.8, -41.6), (-9, -42.4), (-7.4, -41.4)],
    [(-7.4, -41.4), (-3.4, -43.6), (-.6, -43.6)],
    [(-.6, -43.6), (-5, -42.2), (-6.6, -40.2), (-6.4, -37.6), (-4.6, -34.2), (-3.4, -30.6), (-1.2, -28.2),
     (4, -27.6), (10, -24.6), (16, -18.6)],
    [(16, -18.6), (8, -16.2), (2, -14.8), (-3.4, -16.2), (-6.4, -20.2), (-7.2, -24.6), (-8.6, -29.6),
     (-9.8, -34.4), (-9.6, -38.4), (-11.6, -39.6), (-20, -40.2)]]


def _heron(cv, ox, oy, s, mirror=False):
    m = lambda p: M._map(p, ox, oy, s, mirror)
    body = m(M._chunks(_HERON_BODY, 4))
    cv.obj([], 0)
    cv.line([m([(0, -14.8), (.6, -7), (-.5, 0), (-3.6, .6)]), m([(2.6, -15), (3.6, -7), (4.4, 0), (7, .4)])])
    cv.obj([body], 1.)
    wing = m(M._spline([(-5.6, -22), (-1, -27), (6, -25.6), (13.6, -19), (6, -17), (-1.6, -16.6), (-5.6, -22)], True, 4))
    cv.obj([wing], .5)
    cv.hair(C.hatch_poly(wing, 45 if not mirror else 135, 1.5))
    neck = m([(-6.2, -38), (-5, -34), (-3.6, -30.6), (-1.6, -28.4)])
    cv.hair(neck)
    cv.hair([m([(-8.6 + i * .3, -36 + i * 2.4), (-8 + i * .3, -35 + i * 2.4)]) for i in range(5)])
    cv.hair(C.hatch_poly(m([(-7.4, -41.4), (-3.4, -43.6), (-.6, -43.6), (-5, -42.2)]), 0, 1.5))
    e = m([(-9.4, -40.8)])[0]
    cv.obj([_ell(e[0], e[1], .7, .7, 8)], .5)
    cv.line(C.hatch_poly(_ell(e[0], e[1], .7, .7, 8), 0, 1))


def bridge_scene(fx, fy, fw, fh, seed, date, lod=1):
    """The St. Johns Bridge over the Willamette, filling the box (fx, fy, fw, fh) edge to edge
    (to be clipped by its field outline). lod 0 a small medallion, 1 medium, 2 tall."""
    rng = random.Random(seed)
    X = lambda t: fx + fw * t
    Y = lambda t: fy + fh * t
    x0, x1 = fx - 2, fx + fw + 2
    wl = Y(.70)
    dk = Y(.47 if lod else .44)
    dt = max(2.5, min(5., fh * .032))
    yt = Y(.13 if lod else .1)
    T1, T2 = X(.29), X(.71)
    tw = max(6., fw * .06)
    out = []

    # ---- layer A: sky, moon, Mt. Hood, far bank, water ------------------------------------------
    A = C.Canvas()
    A.obj([], 0)
    A.line(_hlines(x0, x1, fy - 2, Y(.07), 2))
    A.hair(_hlines(x0, x1, Y(.07) + .5, Y(.12), 1.5))
    A.hair(_hlines(x0, x1, Y(.12) + 1, Y(.34), 2))
    A.hair(_hlines(x0, x1, Y(.34) + 1, wl, 3))
    if lod:
        mr = max(4., min(6., fh * .035))
        _moon(A, X(.12) if lod == 1 else X(.86), Y(.16), mr, _moon_phase(date))
    # Mt. Hood between the towers: lit west face in broken snow strokes, the east face in shadow
    hx, hp, hb, hw = X(.53), Y(.27 if lod else .2), Y(.66), fw * .21
    H = hb - hp
    prof_l = [(-1, 1), (-.8, .86), (-.62, .7), (-.45, .52), (-.3, .34), (-.2, .2), (-.12, .1), (-.06, .04), (-.03, .0)]
    prof_r = [(.02, .01), (.07, .07), (.1, .06), (.16, .16), (.26, .32), (.4, .5), (.58, .68), (.8, .86), (1, 1)]
    hood = [(hx + u * hw, hp + v * H + (rng.uniform(-.6, .6) if 0 < abs(u) < 1 else 0)) for u, v in prof_l + prof_r]
    A.obj([hood], .5)
    ridge = [(hx - .03 * hw, hp), (hx + .0 * hw, hp + .2 * H), (hx - .06 * hw, hp + .42 * H), (hx + .04 * hw, hp + .7 * H),
             (hx + .02 * hw, hb)]
    shade = ridge + [(hx + hw, hb)] + [(hx + u * hw, hp + v * H) for u, v in prof_r[::-1]]
    A.hair(C.hatch_poly(shade, 45, 2))
    A.hair(C.hatch_poly([p for p in shade if p[1] > hp + .55 * H] + [(hx + hw, hb)], -45, 3))
    # snow: broken strokes down the lit face following the fall line
    sn = []
    ncol = max(8, int(hw * .45 / 2.2))
    for k in range(-ncol, 1):
        u = k / (ncol + .5)
        x_top = hx + u * hw * .45
        nrow = max(4, int(H / 9))
        for j in range(nrow):
            y0 = hp + H * (abs(u) * .7 + .05 + j * .88 / nrow) + rng.uniform(-1, 1)
            y1 = y0 + H * rng.uniform(.4, .8) / nrow
            if y1 < hb - 1:
                sn.append([(x_top + (y0 - hp) * u * .9, y0), (x_top + (y1 - hp) * u * .9, y1)])
    A.hair(sn)
    # lower slopes: forested, ruled dark
    low = [(hx - hw, hb), (hx - hw * .7, hp + .78 * H), (hx - hw * .3, hp + .84 * H), (hx + hw * .2, hp + .8 * H),
           (hx + hw * .7, hp + .82 * H), (hx + hw, hb)]
    A.obj([low], 0)
    A.hair(C.hatch_poly(low, 0, 1.5, .25))
    # far bank: a long low treeline of firs
    fb = [(x0, wl + 1)]
    xx = x0
    while xx < x1:
        top = Y(.64) + rng.uniform(-1.5, 1.5)
        fb += [(xx, top + 2), (xx + 1.6, top - rng.uniform(1, 3.5)), (xx + 3.2, top + 2)]
        xx += 3.2
    fb += [(x1, wl + 1)]
    A.obj([fb], .5)
    A.hair(C.hatch_poly(fb, 0, 1.5, .25))
    # water: dense near the far bank, opening toward us; broken bulino strokes
    A.obj([], 0)
    A.hair(_hlines(x0, x1, wl + 1, Y(.8), 1.5, rng, (8, 26), (1.5, 3)))
    A.hair(_hlines(x0, x1, Y(.8) + .5, Y(.9), 2, rng, (5, 18), (2, 5)))
    A.line(_hlines(x0, x1, Y(.9) + .5, fy + fh + 2, 3, rng, (5, 22), (2, 5)))
    for tx in (T1, T2):   # reflections of the towers, broken into dashes
        y = _hy(Y(.76))
        i = 0
        while y < Y(.97):
            j = rng.uniform(-1.2, 1.2)
            A.line([(tx - tw * .4 + j, y), (tx + tw * .4 + j, y)])
            y += 2 if i % 3 else 3
            i += 1
    out.append(A.svg())

    # ---- layer B: east approach with the cathedral arches, deck, towers ------------------------
    B = C.Canvas()
    blk = []
    # west bank: Forest Park hillside rising to the left edge
    hill = [(x0, Y(.34 if lod else .3))]
    for i in range(1, 13):
        t = i / 12
        hill.append((X(-.01 + .25 * t), Y(.34 + .40 * t ** 1.4) + rng.uniform(-1, 1)))
    hill += [(X(.26), Y(.76)), (x0, Y(.80))]
    # cathedral arches under the east approach (right), standing on the St. Johns bank
    ae0, ae1 = X(.79), x1 + 4
    land_e = Y(.73)
    if lod:
        bank = [(X(.76), land_e + 1), (X(.8), wl - 1), (x1 + 2, wl - 3), (x1 + 2, land_e + 6)]
        B.obj([bank], .5)
        B.hair(C.hatch_poly(bank, 0, 1.5, .25))
    via = [(ae0, dk + dt), (ae1, dk + dt), (ae1, land_e), (ae0, land_e)]
    B.obj([via], 1.)
    B.hair(C.hatch_poly(via, 90, 3, .25))
    na = 3 if lod else 2
    span = (ae1 - ae0) / na
    for i in range(na):
        ax = ae0 + span * (i + .5)
        hwid = span * .32
        op = _lancet(ax, dk + dt + (land_e - dk) * .12, land_e, hwid)
        blk.append(op)
        if lod:
            B.line([(ax - hwid - 1.5, land_e), (ax - hwid - 1.5, dk + dt + 2)])
    # deck with its stiffening truss, from the hill to the right edge
    deck = [(x0, dk), (x1, dk), (x1, dk + dt), (x0, dk + dt)]
    B.obj([deck], 1.)
    zz = []
    xx = x0
    up = True
    while xx < x1:
        zz.append((xx, dk + dt - .5 if up else dk + .5))
        xx += dt * .9
        up = not up
    B.hair(zz)
    B.obj([], 0)
    B.line([(x0, dk + dt + .8), (x1, dk + dt + .8)])
    # the towers: tapered Gothic piers with stacked lancets and spired tops
    tops = []
    for tx in (T1, T2):
        pier = [(tx - tw * .75, Y(.69)), (tx + tw * .75, Y(.69)), (tx + tw * .7, Y(.76)), (tx - tw * .7, Y(.76))]
        B.obj([pier], 1.)
        B.hair(C.hatch_poly(pier, 0, 1.5, .25))
        hb, ht = tw / 2, tw * .36
        sp = tw * (1.1 if lod else .8)
        tower = [(tx - hb, Y(.70)), (tx + hb, Y(.70)), (tx + ht, yt),
                 (tx + ht * .96, yt - sp * .25), (tx + ht * .55, yt - sp), (tx + ht * .18, yt - sp * .25),
                 (tx, yt - sp * .45),
                 (tx - ht * .18, yt - sp * .25), (tx - ht * .55, yt - sp), (tx - ht * .96, yt - sp * .25), (tx - ht, yt)]
        B.obj([tower], 1.)
        half = [(tx + hb * .25, Y(.70)), (tx + hb, Y(.70)), (tx + ht, yt), (tx + ht * .55, yt - sp), (tx + ht * .2, yt)]
        B.hair(C.hatch_poly(half, 90, 1.5, .25))
        B.hair(C.hatch_poly(tower, 90, 3, 1.25))
        # the crown band and the cable saddles
        B.line([(tx - ht, yt + 1.5), (tx + ht, yt + 1.5)])
        # lancets between the legs: three stacked above the deck, one tall below
        w_at = lambda y: hb + (ht - hb) * (Y(.70) - y) / (Y(.70) - yt)
        ya, yb = yt + 4, dk - 2
        n_up = 3 if lod else 2
        seg = (yb - ya) / n_up
        for k in range(n_up):
            y0, y1 = ya + seg * k + .8, ya + seg * (k + 1) - .8
            hwl = w_at(y1) * .4
            if y1 - y0 > hwl * 2.2:
                blk.append(_lancet(tx, y0, y1, hwl))
        y0, y1 = dk + dt + 2, Y(.66)
        if y1 - y0 > 6:
            blk.append(_lancet(tx, y0, y1, w_at(y1) * .42))
        tops.append((tx, yt + 1))
    out.append(B.svg())
    out.append(_black(blk))

    # ---- layer C: cables, suspenders, the west hill of firs, foreground, the heron --------------
    Cv = C.Canvas()
    Cv.obj([], 0)
    (ax_, ay_), (bx_, by_) = tops
    sag = dk - 1.5 - ay_

    def main(x):
        t = (x - ax_) / (bx_ - ax_)
        return ay_ + sag * 4 * t * (1 - t)

    cab = [(ax_ + (bx_ - ax_) * i / 40, main(ax_ + (bx_ - ax_) * i / 40)) for i in range(41)]
    Cv.heavy(cab)
    sus = []
    xx = ax_ + 3
    while xx < bx_ - 2:
        y = main(xx)
        if dk - y > 1.5:
            sus.append([(xx, y + 1), (xx, dk)])
        xx += 4
    # side spans: down to the anchorages at the ends
    for (sx, sy), ex in (((ax_, ay_), X(.02)), ((bx_, by_), X(.98))):
        ey = dk - .5

        def side(x, sx=sx, sy=sy, ex=ex, ey=ey):
            t = (x - sx) / (ex - sx)
            return sy + (ey - sy) * t ** 1.35

        Cv.heavy([(sx + (ex - sx) * i / 24, side(sx + (ex - sx) * i / 24)) for i in range(25)])
        xx = sx + (3 if ex > sx else -3)
        while (xx < ex - 2) if ex > sx else (xx > ex + 2):
            y = side(xx)
            if dk - y > 1.5:
                sus.append([(xx, y + 1), (xx, dk)])
            xx += 4 if ex > sx else -4
    Cv.hair(sus)
    # the west hill: Forest Park firs climbing to the left edge
    Cv.obj([hill], .5)
    Cv.hair(C.hatch_poly(hill, 0, 1.5, .25))
    Cv.hair(C.hatch_poly(hill, 45, 3))
    firs = []
    nf = 11 if lod else 6
    for i in range(nf):
        t = (i + rng.uniform(0, .5)) / nf
        x = X(-.02 + .27 * t)
        base = Y(.36 + .40 * t ** 1.4) + 4
        firs.append((base, x, fh * rng.uniform(.22, .3) * (1.15 - t * .45)))
        if lod and i % 2 == 0:
            firs.append((base + fh * .06, x + fw * .03, fh * rng.uniform(.18, .24) * (1.15 - t * .4)))
    for base, x, hh in sorted(firs):
        _fir(Cv, x, base, hh, rng)
    # Pier Park's evergreens framing the right foreground
    if lod:
        for x, hh in ((X(.93), fh * .4), (X(1.0), fh * .66)):
            _fir(Cv, x, fy + fh + 1, hh, rng, lit=1)
    # foreground shoal with reeds and the heron (Sauvie Island) fishing at its edge
    hb = Y(.9)
    shoal = [(x0, Y(.80))] + [(X(.36 * i / 12), Y(.83) + (i / 12) ** 2.2 * fh * .2 + rng.uniform(-.8, .8)) for i in range(13)] \
        + [(X(.4), fy + fh + 2), (x0, fy + fh + 2)]
    Cv.obj([shoal], .5)
    Cv.hair(C.hatch_poly(shoal, 0, 1.5, .25))
    Cv.hair(C.hatch_poly(shoal, -45, 3))
    reeds = []
    for i in range(12 if lod else 5):
        rx = X(.01 + (.11 if lod else .08) * i / (11 if lod else 4)) + rng.uniform(-1.5, 1.5)
        ry = Y(.83) + 3 + rng.uniform(0, 3)
        rh = fh * rng.uniform(.12, .24)
        bend = rng.uniform(-4, 4)
        reeds.append([(rx, ry), (rx + bend * .25, ry - rh * .5), (rx + bend, ry - rh)])
    Cv.line(reeds)
    for r in reeds[::3]:   # cattail heads
        tx_, ty_ = r[1]
        Cv.obj([_ell(tx_, ty_, 1.1, 2.6, 10)], .5)
        Cv.line(C.hatch_poly(_ell(tx_, ty_, 1.1, 2.6, 10), 0, 1))
    _heron(Cv, X(.22 if lod else .2), hb, fh * (.27 if lod else .34) / 44)
    out.append(Cv.svg())
    return "".join(out)


def _sprig_cone(cv, x, y, L, ang=90., flip=1):
    """A Douglas-fir sprig hanging from (x, y) heading ang degrees: a twig of white needles and a
    cone of overlapping scales with the three-pronged bracts poking out (Pier Park's evergreens)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy * flip, ux * flip
    P = lambda s, t: (x + ux * s + vx * t, y + uy * s + vy * t)
    # twig with needles
    cv.obj([], 0)
    twig = [P(L * .5 * i / 6, L * .05 * math.sin(i / 6 * PI)) for i in range(7)]
    needles = []
    for i in range(1, 9):
        s0 = L * .5 * i / 9
        for side in (-1, 1):
            nl = L * .2 * (1 - i / 14)
            b0 = P(s0, 0)
            tip = P(s0 + nl * .55, side * nl)
            mid = P(s0 + nl * .3, side * nl * .55)
            nn = math.hypot(tip[0] - b0[0], tip[1] - b0[1]) or 1
            px_, py_ = -(tip[1] - b0[1]) / nn * 1.3, (tip[0] - b0[0]) / nn * 1.3
            needles.append([b0, (mid[0] + px_, mid[1] + py_), tip, (mid[0] - px_, mid[1] - py_)])
    cv.obj(needles, .5)
    cv.hair([[n_[0], n_[2]] for n_ in needles])
    cv.obj([], 0)
    cv.line(twig)
    # the cone hangs from the twig's middle
    cs = L * .22
    cx_, cy_ = P(cs, 0)
    cl, cw_ = L * .62, L * .17
    c_ang = a + flip * .5
    cu, cvv = (math.cos(c_ang), math.sin(c_ang)), (-math.sin(c_ang), math.cos(c_ang))
    Q = lambda s, t: (cx_ + cu[0] * s + cvv[0] * t, cy_ + cu[1] * s + cvv[1] * t)
    body = []
    for i in range(25):
        t = PI * i / 24
        body.append(Q(cl * .5 - cl * .5 * math.cos(t), cw_ * math.sin(t) * (1 - .25 * (1 - math.cos(t)) / 2)))
    for i in range(25):
        t = PI * i / 24
        body.append(Q(cl * .5 + cl * .5 * math.cos(t), -cw_ * math.sin(t) * (1 - .25 * (1 + math.cos(t)) / 2)))
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly(body, math.degrees(c_ang), 1.5))
    # scales: rounded tongues whose free edges point to the tip, painted tip-first so each row
    # laps over the bases of the row below; each with a three-pronged bract
    rows = 7
    step = cl / (rows + .6)
    for r in range(rows - 1, -1, -1):
        s0 = step * (r + 1.1)
        k = math.sin(PI * min(.97, max(.06, (s0 - step * .3) / cl))) ** .7
        hwid = cw_ * k * .42
        cols = (-1, 0, 1) if r % 2 == 0 else (-.5, .5)
        for j in cols:
            t0 = j * cw_ * k * .62
            if abs(t0) + hwid * .6 > cw_ * k:
                continue
            sc = [Q(s0 - step * 1.1, t0 - hwid), Q(s0 - step * 1.1, t0 + hwid)]
            for q in range(9):
                th = PI * q / 8
                sc.append(Q(s0 + step * .55 * math.sin(th), t0 + hwid * math.cos(th)))
            cv.obj([sc], 1.)
            # shade the scale's far side and under its lip
            sh = [Q(s0 - step * 1.1, t0 + hwid * .1), Q(s0 - step * 1.1, t0 + hwid)] + \
                [Q(s0 + step * .55 * math.sin(PI * q / 8), t0 + hwid * math.cos(PI * q / 8)) for q in range(5)]
            cv.hair(C.hatch_poly(sh, math.degrees(c_ang) + 90, 1.5))
            # bract: three prongs from the lip
            lip = Q(s0 + step * .5, t0)
            cv.hair([[Q(s0 + step * .1, t0), Q(s0 + step * 1.0, t0)],
                     [Q(s0 + step * .3, t0), Q(s0 + step * .85, t0 - hwid * .35)],
                     [Q(s0 + step * .3, t0), Q(s0 + step * .85, t0 + hwid * .35)]])
            del lip
    cv.obj([], 0)


# ------------------------------------------------------------------------------------------------
# layouts (the house compositions, with the cartouche field engraved full)
# ------------------------------------------------------------------------------------------------

def _cart_geom(w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


def _layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.6, 170)
    o.append(C._clip(C._uid("b3", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .86, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    ia, ib = rx - 3.5, ry - 3.5
    field = _d(_ell(cx, cy, ia, ib, 64), True, 0)
    o.append(_clipped(C._uid("bf3", w, h, seed), field, bridge_scene(cx - ia, cy - ib, 2 * ia, 2 * ib, seed, date, 0)))
    o.append(f'<path d="{_d(_ell(cx, cy, ia, ib, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .5, gh * 1.9)
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
    o.append(C._clip(C._uid("m3", w, h, seed), 0, gy0, w, gh, cv.svg()))
    cn = C.Canvas()
    L = min(54., gh * .3)
    for side in (-1, 1):
        _sprig_cone(cn, cx + side * (cw / 2 + r * 1.62), gy0 + 1, L, 90 + side * 8, side)
    o.append(cn.svg())
    ch = gh + 4
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_geom(cw, ch)
    o.append(_clipped(C._uid("mf3", w, h, seed), field, bridge_scene(cx - a, cy - b, 2 * a, 2 * b, seed, date, 1)))
    o.append(f'<path d="{field}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


_EXTRA = {
    "S": (4.8, [("s", [(4.4, 1.1), (3, 0), (1.3, .2), (.5, 1.6), (1.2, 3.2), (2.6, 4), (4, 4.9), (4.5, 6.4), (3.6, 7.8), (1.8, 8), (.3, 6.9)])]),
    "J": (4.2, [("l", [(1.4, 0), (4.2, 0)]), ("s", [(3.2, 0), (3.2, 5.8), (2.6, 7.6), (1.4, 8), (.2, 7)])]),
    "K": (5.2, [("l", [(0, 0), (2, 0)]), ("l", [(0, 8), (2, 8)]), ("l", [(1, 0), (1, 8)]),
                ("l", [(4.8, .2), (1, 4.8)]), ("l", [(2.2, 3.5), (5, 8)])]),
}


def _letters(s, cx, y, cap, warp=None, track=1.4):
    """Path-drawn capitals centred on cx, top at y, cap height cap. warp(x) -> dy bends the line."""
    k = cap / 8
    G = dict(M._G)
    G.update(_EXTRA)
    width = sum(G.get(c, G[" "])[0] + track for c in s) - track
    x = cx - width * k / 2
    out = []
    for ch in s:
        adv, strokes = G.get(ch, G[" "])
        for kind, pts in strokes:
            pl = M._spline(pts, False, 4) if kind == "s" else list(pts)
            if kind == "p":
                pl = list(pts)
            q = [(x + px * k, y + py * k) for px, py in pl]
            if warp:
                q = [(qx, qy + warp(qx)) for qx, qy in q]
            out.append(q)
        x += (adv + track) * k
    return out


def _layout_tall(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.dark_ground((0, 0, w, py0 - 3.5), "L"))
    o.append(C.bead_moulding(0, 2.5, w, 1.5))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .62
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .45)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .45)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=5, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t3", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_geom(cw, ch)
    o.append(_clipped(C._uid("tf3", w, h, seed), field, bridge_scene(cx - a, cy - b, 2 * a, 2 * b, seed, date, 2)))
    o.append(f'<path d="{field}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bw_ = cw * 1.4
    arch = .04
    by = cy + ch * .47
    bsvg, _ = C.ribbon_banner(cx, by, bw_, bh, arch, rng.randrange(1 << 20))
    o.append(bsvg)
    fw_ = bw_ * .7
    warp = lambda x: -arch * bw_ * math.sin(PI * min(1, max(0, (x - (cx - fw_ / 2)) / fw_)))
    lt = _letters("ST. JOHNS · MCMXXXI", cx, by - bh * .3, bh * .6, warp)
    o.append(f'<path d="{"".join(_d(p, False, .1) for p in lt)}" fill="none" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, ped_h), "M"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 3)},{_n(ty + 3)}h{_n(tw - 5)}v{_n(th - 5)}h{_n(-tw + 5)}z" fill="{C.pat("L")}" stroke="none"/>')
    cap = min(th * .55, 11)
    lt = _letters("PIER PARK · CATHEDRAL PARK", tx + tw / 2, ty + (th - cap) / 2 + .5, cap)
    pad = cap * .35
    lw = max(q[0] for p_ in lt for q in p_) - min(q[0] for p_ in lt for q in p_)
    o.append(f'<path d="M{_n(tx + tw / 2 - lw / 2 - pad)},{_n(ty + (th - cap) / 2 - pad)}h{_n(lw + 2 * pad)}v{_n(cap + 2 * pad)}h{_n(-lw - 2 * pad)}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{"".join(_d(p, False, .1) for p in lt)}" fill="none" stroke="#000" stroke-width="1"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f3", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) * 7 + 3
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date)
    else:
        body = _layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
