"""news-01 "Portland news": the city's own front page, engraved.

The cartouche holds downtown Portland seen across the Willamette at dawn on Veterans Day: the
KOIN tower spire, Big Pink and the Wells Fargo slab against Mt. Hood, the Hawthorne Bridge's lift
towers in the river, and four Oregon Air National Guard jets in a finger-four flyover laying
contrails across a ruled sky (today's story). A ribbon banner reads PORTLAND NEWS and the
pedestal tablet SIX NEWSROOMS, in drawn path lettering. The moon phase follows ctx["date"].
Easter egg: a great blue heron from Sauvie Island standing on a piling in the river.
"""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, _n, _d, _ell_pts, _superellipse

PI = math.pi

# ---------------------------------------------------------------------------------------------
# stroke lettering (drawn, never <text>): 4 x 6 cell
# ---------------------------------------------------------------------------------------------
_GLYPH = {
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "W": [[(0, 0), (1, 6), (2, 2.5), (3, 6), (4, 0)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "M": [[(0, 6), (0, 0), (2, 3.5), (4, 0), (4, 6)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3), (2.4, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "·": [[(1.7, 3), (2.3, 3)]],
}


def _letters(text, path_pts, size):
    """Lettering centred along a polyline (list of points); returns path d of glyph strokes."""
    seg = [0.]
    for i in range(1, len(path_pts)):
        seg.append(seg[-1] + math.hypot(path_pts[i][0] - path_pts[i - 1][0], path_pts[i][1] - path_pts[i - 1][1]))
    L = seg[-1]
    s = size / 6.
    adv = 5.6 * s
    tot = adv * len(text) - 1.6 * s
    u0 = (L - tot) / 2

    def at(u):
        u = min(max(u, 0), L)
        for i in range(1, len(seg)):
            if seg[i] >= u:
                t = (u - seg[i - 1]) / max(1e-6, seg[i] - seg[i - 1])
                p, q = path_pts[i - 1], path_pts[i]
                return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, math.atan2(q[1] - p[1], q[0] - p[0]))
        return (*path_pts[-1], 0.)
    out = []
    for k, ch in enumerate(text):
        g = _GLYPH.get(ch)
        if not g:
            continue
        mx, my, ang = at(u0 + k * adv + 2 * s)
        ca, sa = math.cos(ang), math.sin(ang)
        for stroke in g:
            pts = []
            for gx, gy in stroke:
                lx, ly = (gx - 2) * s, (gy - 3) * s
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            out.append(_d(pts, tol=0))
    return "".join(out)


# ---------------------------------------------------------------------------------------------
# the vignette: downtown Portland across the Willamette, Mt. Hood, the Veterans Day flyover
# ---------------------------------------------------------------------------------------------

def _moon_phase(date):
    try:
        y, m, d = (int(v) for v in date.split("-"))
    except Exception:
        return .5
    # days since a known new moon (2000-01-06)
    a = (14 - m) // 12
    yy, mm = y + 4800 - a, m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    return ((jdn - 2451550.1) / 29.530588) % 1.


def _jet(x, y, s, ang):
    """A small swept-wing fighter seen from below, nose along ang; returns polygon."""
    pts = [(1.0, 0), (.55, .08), (.15, .1), (-.1, .62), (-.32, .62), (-.22, .12), (-.55, .1), (-.7, .32),
           (-.82, .32), (-.78, 0)]
    full = pts + [(px, -py) for px, py in reversed(pts[1:-1])]
    ca, sa = math.cos(ang), math.sin(ang)
    return [(x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s) for px, py in full]


def scene(cx, cy, a, b, seed, date, cid, full=True):
    """Everything inside the cartouche field (superellipse a x b at cx, cy)."""
    rng = random.Random(seed)
    field = _superellipse(cx, cy, a, b)
    X0, Y0, W, H = cx - a, cy - b, 2 * a, 2 * b

    def P(u, v):
        return (X0 + u * W, Y0 + v * H)
    horizon = .66
    hy = Y0 + horizon * H
    sky = Canvas()
    # sky: ruled, denser toward the horizon (pitch 3 above, 2 below)
    sky_poly = [P(-.02, -.02), P(1.02, -.02), P(1.02, horizon + .02), P(-.02, horizon + .02)]
    sky.obj([sky_poly], 0)
    mid = Y0 + H * .34
    for yy in [Y0 + 1 + 3 * i for i in range(int((mid - Y0) / 3) + 1)]:
        sky.hair([(X0 - 2, yy), (X0 + W + 2, yy)])
    yy = mid + 2
    while yy < hy + 2:
        sky.hair([(X0 - 2, yy), (X0 + W + 2, yy)])
        yy += 2
    # moon (phase by date), top right
    ph = _moon_phase(date)
    mr = max(3.5, min(W, H) * .06)
    mx, my = P(.86, .16)
    disc = _ell_pts(mx, my, mr, mr, 32)
    sky.obj([disc], .5)
    sky.hair(hatch_poly(disc, 0, 3, 1.))
    side = 1 if ph < .5 else -1
    kk = math.cos(2 * PI * ph)
    dark = [(mx - side * mr * math.cos(t), my + mr * math.sin(t)) for t in [-PI / 2 + PI * i / 24 for i in range(25)]]
    dark += [(mx + side * kk * mr * math.cos(t), my + mr * math.sin(t)) for t in [PI / 2 - PI * i / 24 for i in range(25)]]
    if abs(C._area(dark)) > 1:
        sky.obj([dark], 0)
        sky.hair(hatch_poly(dark, 0, 1.5))
        sky.hair(hatch_poly(dark, 60, 3))
    # maria: a few stipple dots on the lit face
    for (du, dv, dr) in ((-.3, -.2, .22), (.25, .1, .18), (-.05, .35, .14)):
        sky.hair(hatch_poly(_ell_pts(mx + du * mr, my + dv * mr, dr * mr, dr * mr * .8, 10), 30, 1.5))
    # clouds: low banks with shaded undersides
    for (cu, cv_, cw, chh) in ((.62, .44, .34, .07), (.08, .52, .3, .06), (.4, .3, .22, .045)):
        ccx, ccy = P(cu, cv_)
        rw, rh = cw * W / 2, chh * H
        pts = []
        n = 40
        for i in range(n + 1):
            t = PI * i / n
            bump = 1 + .22 * abs(math.sin(t * 5 + cu * 7))
            pts.append((ccx - rw * math.cos(t), ccy - rh * math.sin(t) * bump))
        pts.append((ccx + rw * .9, ccy + rh * .25))
        pts.append((ccx - rw * .9, ccy + rh * .25))
        sky.obj([pts], .5)
        under = [(px, py + rh * .55) for px, py in pts[:n + 1]]
        band = pts[:n + 1] + under[::-1]
        sky.hair(hatch_poly(pts, 0, 3, 1.5, .8))
        sky.hair(hatch_poly([(px, max(py, ccy - rh * .1)) for px, py in pts], 0, 3, 0, .4))
        sky.hair(hatch_poly([(px, max(py, ccy + rh * .05)) for px, py in pts], 25, 3, 0, .4))
    # contrails from the formation, trailing back to the left edge
    jets = []
    js = max(3.5, min(W, H) * .045)
    lead = P(.42, .13)
    ang = math.radians(-14)
    form = [(0, 0), (-2.1, -1.5), (-2.1, 1.6), (-4.2, 3.1)]   # finger-four, in jet lengths
    ca, sa = math.cos(ang), math.sin(ang)
    for fx, fy in form:
        jx = lead[0] + (fx * ca - fy * sa) * js
        jy = lead[1] + (fx * sa + fy * ca) * js
        jets.append((jx, jy))
        tail_x = X0 - 4
        L = (jx - js * .8 - tail_x) / ca
        tx, ty = jx - js * .8 * ca, jy - js * .8 * sa
        ex, ey = tx - L * ca, ty - L * sa
        wdt = 1.1
        nx, ny = -sa, ca
        trail = [(tx + nx * .4, ty + ny * .4), (ex + nx * wdt * 2.2, ey + ny * wdt * 2.2),
                 (ex - nx * wdt * 2.2, ey - ny * wdt * 2.2), (tx - nx * .4, ty - ny * .4)]
        sky.obj([trail], 0)
        sky.hair([[(tx, ty), (ex + nx * wdt * 1.6, ey + ny * wdt * 1.6)]])
    body = sky.svg()
    jet_d = "".join(_d(_jet(jx, jy, js, ang), True, 0) for jx, jy in jets)
    body += f'<path d="{jet_d}" fill="#000" stroke="none"/>'

    cv = Canvas()
    # Mt. Hood, east, behind the city
    hx, hpk = P(.72, .38)
    base_l, base_r = X0 + W * .32, X0 + W * 1.12
    mtn = [(base_l, hy + 1)]
    prof = [(0, 0), (.12, -.08), (.24, -.2), (.33, -.38), (.4, -.58), (.45, -.76), (.49, -.92), (.52, -1),
            (.54, -.97), (.565, -.9), (.6, -.78), (.66, -.6), (.74, -.42), (.84, -.25), (.93, -.12), (1, -.04)]
    mh = hy - hpk
    for t, z in prof:
        mtn.append((base_l + (base_r - base_l) * t + rng.uniform(-.4, .4), hy + z * mh))
    mtn.append((base_r, hy + 1))
    cv.obj([mtn], 1.)
    peak_x = base_l + (base_r - base_l) * .52
    # shadow side (east/right of the ridge line) hatched dark; lit side light contour lines
    shadow = [(peak_x, hpk)] + [p for p in mtn if p[0] > peak_x and p[1] < hy] + [(base_r, hy + 1),
                                                                                   (peak_x + mh * .25, hy + 1)]
    ridge = [(peak_x, hpk), (peak_x - mh * .05, hpk + mh * .3), (peak_x + mh * .12, hpk + mh * .6),
             (peak_x + mh * .25, hy + 1)]
    shadow = [(peak_x, hpk)] + [p for p in mtn if p[0] > peak_x and p[1] < hy] + [(base_r, hy + 1)] + ridge[::-1]
    cv.hair(hatch_poly(shadow, 60, 1.5))
    cv.hair(hatch_poly(shadow, -30, 3))
    lit = [p for p in mtn if p[0] <= peak_x] + ridge[1:] + [(base_l, hy + 1)]
    cv.hair(hatch_poly(lit, -62, 3))
    # snow line: below it the forested slopes are ruled dark
    snow = hpk + mh * .55
    forest = [(base_l - 2, snow), (base_r + 2, snow), (base_r + 2, hy + 2), (base_l - 2, hy + 2)]
    cv.obj([], 0)
    ftop = []
    for i in range(41):
        xx = base_l + (base_r - base_l) * i / 40
        ftop.append((xx, snow + mh * (.05 + .08 * abs(math.sin(i * 1.7))) + mh * .2 * abs(i / 40 - .52)))
    fpoly = ftop + [(base_r, hy + 1), (base_l, hy + 1)]
    # keep the forest inside the mountain silhouette: rule horizontal lines clipped to both
    for ln in hatch_poly(fpoly, 0, 1.5):
        cv.hair(ln)
    # west hills: low dark ridge on the left behind the city
    hills = [(X0 - 2, hy + 1)]
    for i in range(31):
        u = i / 30 * .5
        hills.append((X0 + W * u, hy - H * (.08 + .03 * math.sin(i * .9) + .02 * math.sin(i * 2.3)) * (1 - u * .9)))
    hills.append((X0 + W * .5, hy + 1))
    cv.obj([hills], .5)
    cv.hair(hatch_poly(hills, 0, 1.5))
    cv.hair(hatch_poly(hills, 70, 3))

    # the skyline: (u centre, width, height as fraction of H above horizon, kind)
    towers = [(.06, .07, .12, "b"), (.12, .06, .17, "b"), (.18, .05, .22, "b"), (.235, .06, .3, "koin"),
              (.3, .065, .2, "b"), (.36, .07, .37, "wells"), (.43, .08, .33, "pink"), (.5, .05, .2, "b"),
              (.555, .07, .15, "b"), (.62, .06, .11, "b"), (.68, .08, .08, "b"), (.77, .1, .06, "b"),
              (.88, .1, .05, "b"), (.97, .1, .04, "b")]
    order = sorted(range(len(towers)), key=lambda i: -towers[i][2])
    for i in order[::-1][::-1]:
        pass
    # draw tall ones first (behind), short ones in front
    for i in sorted(range(len(towers)), key=lambda i: -towers[i][2]):
        u, tw, th, kind = towers[i]
        x0, x1 = X0 + W * (u - tw / 2), X0 + W * (u + tw / 2)
        top = hy - H * th
        lit_w = (x1 - x0) * .42
        if kind == "koin":
            spire = top - H * .09
            poly = [(x0, hy + 1), (x0, top), ((x0 + x1) / 2, spire), (x1, top), (x1, hy + 1)]
            cv.obj([poly], 1.)
            cv.hair(hatch_poly([(x0, top), (x0 + lit_w, top), (x0 + lit_w, hy), (x0, hy)], 0, 2))
            cv.hair(hatch_poly([(x0 + lit_w, top), (x1, top), (x1, hy), (x0 + lit_w, hy)], 90, 1.5))
            cv.hair(hatch_poly([(x0 + lit_w, top), (x1, top), (x1, hy), (x0 + lit_w, hy)], 0, 3))
            roof_d = [((x0 + x1) / 2, spire), (x1, top), (x0 + lit_w, top)]
            cv.hair(hatch_poly(roof_d, 30, 1.5))
            cv.hair(hatch_poly([((x0 + x1) / 2, spire), (x0 + lit_w, top), (x0, top)], -60, 3))
            cv.hair([((x0 + x1) / 2, spire), ((x0 + x1) / 2, spire - H * .03)])
            cv.line([(x0 + lit_w, top), (x0 + lit_w, hy)])
        elif kind == "pink":
            ch_ = (x1 - x0) * .18
            poly = [(x0, hy + 1), (x0, top + ch_), (x0 + ch_, top), (x1 - ch_, top), (x1, top + ch_), (x1, hy + 1)]
            cv.obj([poly], 1.)
            m_ = x0 + (x1 - x0) * .5
            cv.hair(hatch_poly([(x0, top + ch_), (m_, top), (m_, hy), (x0, hy)], 90, 3))
            cv.hair(hatch_poly([(m_, top), (x1, top + ch_), (x1, hy), (m_, hy)], 90, 1.5))
            cv.hair(hatch_poly([(m_, top), (x1, top + ch_), (x1, hy), (m_, hy)], 0, 2))
            cv.line([(m_, top), (m_, hy)])
        elif kind == "wells":
            poly = [(x0, hy + 1), (x0, top), (x1, top), (x1, hy + 1)]
            cv.obj([poly], 1.)
            cv.hair(hatch_poly([(x0, top + 3), (x0 + lit_w, top + 3), (x0 + lit_w, hy), (x0, hy)], 0, 2))
            cv.hair(hatch_poly([(x0 + lit_w, top), (x1, top), (x1, hy), (x0 + lit_w, hy)], 90, 1.5))
            cv.hair(hatch_poly([(x0 + lit_w, top), (x1, top), (x1, hy), (x0 + lit_w, hy)], 0, 1.5))
            cv.line([(x0, top + 2.5), (x1, top + 2.5)])
            cv.hair([((x0 + x1) / 2, top), ((x0 + x1) / 2, top - H * .04)])
        else:
            poly = [(x0, hy + 1), (x0, top), (x1, top), (x1, hy + 1)]
            cv.obj([poly], .5 if th < .1 else 1.)
            cv.hair(hatch_poly([(x0, top), (x0 + lit_w, top), (x0 + lit_w, hy), (x0, hy)], 0, 3 if th > .1 else 2))
            cv.hair(hatch_poly([(x0 + lit_w, top), (x1, top), (x1, hy), (x0 + lit_w, hy)], 90, 1.5))
            if th > .1:
                cv.hair(hatch_poly([(x0 + lit_w, top), (x1, top), (x1, hy), (x0 + lit_w, hy)], 0, 3))
                cv.hair([(x0 + lit_w, top), (x0 + lit_w, hy)])
    # the river: ruled water, broken reflections under the towers
    river = [P(-.02, horizon), P(1.02, horizon), P(1.02, 1.02), P(-.02, 1.02)]
    cv.obj([river], 0)
    yy = hy + 1.5
    k = 0
    while yy < Y0 + H + 2:
        depth = (yy - hy) / max(1., Y0 + H - hy)
        x = X0 - 2
        while x < X0 + W + 2:
            seg = rng.uniform(6, 22) * (1 + depth)
            gap = rng.uniform(1.5, 4) * (1.2 - depth)
            cv.hair([(x, yy), (min(x + seg, X0 + W + 2), yy)])
            x += seg + gap
        yy += 2 if depth < .5 else 1.5
        k += 1
    # reflections: dark vertical streaks under the tall towers
    for u, tw, th, kind in towers:
        if th < .15:
            continue
        rx0 = X0 + W * (u + tw * .05)
        rx1 = X0 + W * (u + tw / 2)
        refl = [(rx0, hy + 1), (rx1, hy + 1), (rx1 - 1, hy + H * th * .55), (rx0 + 1, hy + H * th * .5)]
        cv.hair(hatch_poly(refl, 90, 1.5))
    # the seawall in the foreground (Tom McCall Waterfront), dark rubble and a rail
    wall_y = Y0 + H * .9
    wall = [P(-.02, .9), P(1.02, .88), P(1.02, 1.02), P(-.02, 1.02)]
    if full:
        # the Hawthorne Bridge: a Pratt-truss deck on piers, two lift towers standing on it
        dy = hy + H * .11
        tdh = max(4., H * .05)
        wl = dy + H * .07                       # pier foot / waterline under the bridge
        for tu in (.24, .5, .76):
            tx = X0 + W * tu
            pw_ = max(3.5, W * .02)
            pier = [(tx - pw_, dy + 1.5), (tx + pw_, dy + 1.5), (tx + pw_ * 1.15, wl), (tx - pw_ * 1.15, wl)]
            cv.obj([pier], 1.)
            cv.hair(hatch_poly(pier, 0, 1.5))
            cv.hair(hatch_poly([(tx, dy + 1.5), (tx + pw_, dy + 1.5), (tx + pw_ * 1.15, wl), (tx, wl)], 90, 1.5))
            refl = [(tx - pw_ * 1.1, wl), (tx + pw_ * 1.1, wl), (tx + pw_ * .6, wl + H * .05), (tx - pw_ * .6, wl + H * .05)]
            cv.obj([refl], 0)
            cv.hair(hatch_poly(refl, 0, 1.5))
        # truss band
        band = [(X0 - 2, dy - tdh), (X0 + W + 2, dy - tdh), (X0 + W + 2, dy + 1.5), (X0 - 2, dy + 1.5)]
        cv.obj([band], 0)
        cv.line([(X0 - 2, dy - tdh), (X0 + W + 2, dy - tdh)])
        cv.heavy([(X0 - 2, dy + .5), (X0 + W + 2, dy + .5)])
        step = tdh * .9
        x = X0 - 2
        k = 0
        while x < X0 + W + 2:
            cv.hair([(x, dy - tdh), (x, dy)])
            cv.hair([(x, dy - tdh), (x + step, dy)] if k % 2 else [(x, dy), (x + step, dy - tdh)])
            x += step
            k += 1
        # lift towers on the middle span, with counterweights
        for tu in (.39, .61):
            tx = X0 + W * tu
            tw_ = max(4., W * .028)
            tt = dy - tdh - H * .15
            for sx in (-1, 1):
                leg = [(tx + sx * tw_ / 2 - .9, dy), (tx + sx * tw_ / 2 - .9, tt), (tx + sx * tw_ / 2 + .9, tt), (tx + sx * tw_ / 2 + .9, dy)]
                cv.obj([leg], .5)
                cv.hair(hatch_poly(leg, 90, 1.))
            cv.obj([], 0)
            yy = tt + 2
            while yy < dy - tdh - 1:
                cv.hair([(tx - tw_ / 2, yy), (tx + tw_ / 2, yy + 3)])
                cv.hair([(tx + tw_ / 2, yy), (tx - tw_ / 2, yy + 3)])
                yy += 3
            cw_ = [(tx - tw_ / 2 + 1, tt + 3), (tx + tw_ / 2 - 1, tt + 3), (tx + tw_ / 2 - 1, tt + 3 + H * .035), (tx - tw_ / 2 + 1, tt + 3 + H * .035)]
            cv.obj([cw_], .5)
            cv.hair(hatch_poly(cw_, 0, 1.))
            cap = [(tx - tw_ * .75, tt + .5), (tx - tw_ * .55, tt - tw_ * .5), (tx + tw_ * .55, tt - tw_ * .5), (tx + tw_ * .75, tt + .5)]
            cv.obj([cap], 1.)
            cv.hair(hatch_poly(cap, 0, 1.5))
            cv.hair([(tx, tt - tw_ * .5), (tx, tt - tw_ * .5 - H * .025)])
    # seawall
    cv.obj([wall], 1.)
    cv.hair(hatch_poly(wall, 0, 1.5, .3))
    cv.hair(hatch_poly(wall, 75, 3))
    cv.hair([P(-.02, .905), P(1.02, .885)])
    # Easter egg: a great blue heron (Sauvie Island) on a piling by the seawall
    s = max(.55, min(W, H) / 150.)
    hux, huy = X0 + W * .87, Y0 + H * .885
    pil = [(hux - 2.2 * s, huy + H * .2), (hux - 2.2 * s, huy - 4 * s), (hux + 2.2 * s, huy - 4.6 * s), (hux + 2.2 * s, huy + H * .2)]
    cv.obj([pil], 1.)
    cv.hair(hatch_poly(pil, 90, 1.5))
    cv.hair(hatch_poly(pil, 20, 3))
    top = huy - 4.4 * s

    def Hp(x, y):
        return (hux + x * s, top - y * s)
    legs = [[Hp(-1, 0), Hp(-1.4, 9)], [Hp(1, 0), Hp(.2, 9)]]
    for lg in legs:
        cv.hair(lg)
    body_pts = [Hp(-1.8, 9), Hp(-4.5, 11.5), Hp(-5.5, 14.5), Hp(-4, 17), Hp(-1, 17.5), Hp(2.2, 15.5),
                Hp(5.5, 10.5), Hp(7.5, 8.6), Hp(3.5, 9.4), Hp(.5, 8.6)]
    cv.obj([body_pts], 1.)
    cv.hair(hatch_poly(body_pts, -35, 1.5))
    cv.hair([Hp(-4.2, 13.5), Hp(1, 12.6), Hp(5.5, 10)])
    neck = [Hp(-4, 16.5), Hp(-5.8, 19.5), Hp(-5, 22.5), Hp(-3.2, 24.6), Hp(-3.8, 26.5)]
    cv.heavy(neck)
    head = _ell_pts(*Hp(-4.1, 27), 1.6 * s, 1.1 * s, 12)
    cv.obj([head], 1.)
    cv.hair(hatch_poly(head, 0, 1.))
    cv.line([Hp(-5.5, 27.2), Hp(-10.5, 26)])
    cv.hair([Hp(-3, 27.8), Hp(1.5, 29)])
    body += cv.svg()
    fd = _d(field, True, 0)
    return (f'<clipPath id="{cid}"><path d="{fd}"/></clipPath>'
            f'<g clip-path="url(#{cid})"><path d="{fd}" fill="#fff" stroke="none"/>{body}</g>')


# ---------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex so the field fills completely and the banner is lettered)
# ---------------------------------------------------------------------------------------------

def _medallion_scene(cx, cy, rx, ry, seed, date, cid):
    """Oval medallion with a small newspaper-and-skyline vignette (short band)."""
    o = [C._medallion(cx, cy, rx, ry)]
    a, b = rx - 2.2, ry - 2.2
    # an ellipse field: reuse scene by passing a superellipse close to the oval
    o.append(scene(cx, cy, a, b, seed, date, cid, full=False).replace(
        _d(_superellipse(cx, cy, a, b), True, 0), _d(_ell_pts(cx, cy, a, b, 64), True, 0)))
    return "".join(o)


def _layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.4, 170)
    o.append(C._clip(C._uid("nb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(_medallion_scene(cx, cy, rx, ry, seed, date, C._uid("nbs", w, h, seed)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    return cw / 2 - bw * 1.6, ch / 2 - bw * 1.6


def _banner(cx, cy, w, h, seed, text):
    svg, centre = C.ribbon_banner(cx, cy, w, h, .04, seed)
    d = _letters(text, centre, min(h * .5, 9))
    return svg + f'<path d="{d}" fill="none" stroke="#000" stroke-width="1" stroke-linecap="square"/>'


def _layout_medium(w, h, seed, date, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.7)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("nm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, gh + 4)
    o.append(scene(cx, cy, a - 5.5, b - 5.5, seed, date, C._uid("nms", w, h, seed), full=gh > 120))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, date, density=1.):
    rng = random.Random(seed)
    o = [C.dark_ground((0, 0, w, h), "L")]
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
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
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
    o.append(C._clip(C._uid("nt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, ch)
    o.append(scene(cx, cy, a - 5.5, b - 5.5, seed, date, C._uid("nts", w, h, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = max(12., min(18, ph * .055))
    o.append(_banner(cx, cy + ch * .47, cw * 1.4, bh, rng.randrange(1 << 20), "PORTLAND NEWS"))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 3)},{_n(ty + 3)}h{_n(tw - 5)}v{_n(th - 5)}h{_n(-tw + 5)}z" fill="{C.pat("L")}" stroke="none"/>')
    tl = [(tx + 4, ty + th / 2 + .5), (tx + tw - 2, ty + th / 2 + .5)]
    o.append(f'<path d="{_letters("SIX NEWSROOMS · ONE CITY", tl, min(th * .55, 9))}" fill="none" stroke="#000" stroke-width="1"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("nf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 7
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date, .9)
    else:
        body = _layout_tall(w, h, seed, date, .85 if h >= 440 else 1.)
    return C.svg_doc(w, h, body)
