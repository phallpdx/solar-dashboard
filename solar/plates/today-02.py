"""today-02 -- Alfred's briefing + "Your weather station says" (Bear Den, Sauvie Island).

Subject: Parker's own backyard weather station on the bank of the Multnomah Channel on the
pick-of-the-week dry, sunny day: a cup anemometer and wind vane (pointing into today's north
wind), a little solar panel and an empty rain gauge (0.00 in), a sun-glory sky, Mt. Hood on the
horizon, cottonwoods, the channel, and the weekend's rain already marching in from the west.
Easter eggs: the vane's compass cross is a pair of crossed drumsticks; a Sauvie Island heron
fishes the shallows; on tall plates the pedestal tablet carries a bar of swing eighths.
"""
import sys
import math
import random
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
PI = math.pi


def _hy(y):
    """snap a horizontal .5 hairline to the device grid"""
    return round((y - .25) * 2) / 2 + .25


def _hlines(poly, pitch, phase=0.):
    """horizontal hairlines on the device grid, clipped to poly"""
    return C.hatch_poly(poly, 0, pitch, phase + .25)


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _cart_box(cx, cy, cw, chh):
    bw = max(5., min(cw, chh) * .07)
    a, b = cw / 2 - bw * 1.6, chh / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


# ------------------------------------------------------------------------------------------------
# the vignette
# ------------------------------------------------------------------------------------------------

def _scene(x, y, w, h, seed=0):
    """The engraved landscape filling x..x+w, y..y+h completely (clip it to the frame)."""
    rng = random.Random(seed)
    s = max(.6, min(2.4, min(w / 165., h / 72.)))
    X = lambda u: x + u * w
    Y = lambda v: y + v * h
    tall = h > w * .7
    hy = Y(.56 if tall else .6)                 # horizon
    cv = C.Canvas()
    blacks = []                                 # solid fills painted over the canvas

    # ---- sky: light ruled with a sun glory --------------------------------------------------
    sky = _rect(x - 1, y - 1, x + w + 1, hy + 1)
    cv.obj([sky], 0)
    cv.hair(_hlines(sky, 3))
    sx, sy = X(.79), hy - (hy - y) * .42
    sr = 8.5 * s
    nr = 28
    R = math.hypot(w, h)
    for i in range(nr):
        a0 = 2 * PI * i / nr
        a1 = a0 + 2 * PI / nr * (.55 if i % 2 else .3)
        r0 = sr * 1.25
        wedge = [(sx + r0 * math.cos(a0), sy + r0 * math.sin(a0)), (sx + R * math.cos(a0), sy + R * math.sin(a0)),
                 (sx + R * math.cos(a1), sy + R * math.sin(a1)), (sx + r0 * math.cos(a1), sy + r0 * math.sin(a1))]
        cv.hair(_hlines(wedge, 3, 1.5))
    cv.hair(_hlines(_rect(x - 1, y - 1, x + w + 1, y + (hy - y) * .3), 3, 1.5))
    cv.line(_hlines(_rect(x - 1, y - 1, x + w + 1, y + (hy - y) * .1), 3))
    # a skein of geese over the island (November)
    gk = []
    for i in range(5):
        j = i - 2
        gx_, gy_ = X(.68) + j * 5.5 * s + (j % 2) * s, y + (hy - y) * .14 + abs(j) * 2 * s
        if j == 0:
            gy_ -= .8 * s
        gk.append([(gx_ - 2 * s, gy_ + .6 * s), (gx_ - .7 * s, gy_ - .5 * s), (gx_, gy_), (gx_ + .7 * s, gy_ - .5 * s), (gx_ + 2 * s, gy_ + .6 * s)])
    geese = gk

    # ---- the weekend's rain coming in from the west (left) -----------------------------------
    cl_x, cl_y = X(.05), y + (hy - y) * .34
    if s >= .62:
        rain = _rect(cl_x - 2 * s, cl_y + 4 * s, cl_x + 42 * s, hy - 2)
        cv.obj([rain], 0)
        cv.hair(C.hatch_poly(rain, 72, 3))
        puffs = [(14, -9, 8), (26, -7, 7), (4, -3, 8), (19, -2, 9), (33, -1, 7), (10, 4, 8), (26, 5, 8), (40, 4, 6)]
        for px, py, pr in puffs:
            cyc = cl_y + py * s
            p = _ell(cl_x + px * s, cyc, pr * s, pr * s * .82, 30)
            cv.obj([p], .5)
            lower = [q for q in p if q[1] > cyc - pr * s * .05]
            if len(lower) > 2:
                cv.hair(_hlines(lower, 1.5))
            cv.hair([_ell(cl_x + px * s, cyc, pr * s * .7, pr * s * .6, 20, PI * 1.05, PI * 1.6)])
        base_ = [(cl_x - 3 * s, cl_y + 8 * s), (cl_x + 47 * s, cl_y + 8 * s), (cl_x + 44 * s, cl_y + 11 * s), (cl_x, cl_y + 11 * s)]
        cv.obj([base_], .5)
        cv.line(_hlines(base_, 1.5))

    # ---- Mt. Hood ---------------------------------------------------------------------------
    mx, mh, mw = X(.34), (hy - y) * .68, w * .5
    peak = (mx, hy - mh)
    left = [(mx - mw / 2, hy + 1), (mx - mw * .36, hy - mh * .12), (mx - mw * .24, hy - mh * .3),
            (mx - mw * .15, hy - mh * .5), (mx - mw * .08, hy - mh * .75), (mx - mw * .03, hy - mh * .95)]
    right = [(mx + mw * .025, hy - mh * .97), (mx + mw * .05, hy - mh * .86), (mx + mw * .1, hy - mh * .7),
             (mx + mw * .14, hy - mh * .62), (mx + mw * .22, hy - mh * .42), (mx + mw * .34, hy - mh * .17),
             (mx + mw / 2, hy + 1)]
    hood = left + [peak] + right
    cv.obj([hood], 1.)
    snow = hy - mh * .45
    ridge = [peak, (mx + mw * .01, hy - mh * .78), (mx - mw * .03, hy - mh * .55), (mx - mw * .02, hy - mh * .3), (mx - mw * .04, hy + 1)]
    shadow = left + ridge[::-1][:-1][::-1] if False else left + [peak] + ridge[1:]
    # the shadowed west face: lines that fall with the slope, darker low
    cv.hair(C.hatch_poly(shadow, -55, 2))
    low_sh = [(px, max(py, snow)) for px, py in shadow]
    cv.hair(_hlines(low_sh, 1.5))
    # the lit east face: forest below the snow, bright snowfield with gullies above
    lit_low = [(mx - mw * .04, snow)] + [(px, max(py, snow)) for px, py in right] + [(mx - mw * .04, hy + 1)]
    cv.hair(_hlines(lit_low, 2))
    for k in range(6):
        t_ = (k + 1) / 7
        g0 = (mx + mw * .006 * k, peak[1] + mh * (.08 + .02 * k))
        g1 = (mx + mw * (.03 + .27 * t_), snow + mh * .08 * (1 - t_) - 1)
        mid = ((g0[0] + g1[0]) / 2 - mw * .02, (g0[1] + g1[1]) / 2 + mh * .03)
        cv.hair([g0, mid, g1])
        if k % 2:
            cv.hair([(mid[0] + 1.5, mid[1]), (g1[0] + 1.5, g1[1] + 1)])
    # broken snow line
    sn = []
    xx = mx - mw * .04
    while xx < mx + mw * .3:
        sn.append([(xx, snow + rng.uniform(-1.5, 1.5) * s), (xx + 3 * s, snow + rng.uniform(-3, 0) * s)])
        xx += 4.5 * s
    cv.line(sn)
    cv.line(ridge)
    cv.line([left[-1], peak, right[0], right[1], right[2]])

    # ---- cottonwoods on the far shore --------------------------------------------------------
    tl_top = []
    xx = x - 2
    while xx < x + w + 2:
        r = (2.2 + 2.6 * rng.random()) * s
        for k in range(7):
            a = PI + PI * k / 6
            tl_top.append((xx + r + r * math.cos(a), hy - 1.5 * s + r * .9 * math.sin(a)))
        xx += 2 * r * .85
    trees = tl_top + [(x + w + 2, hy + 3 * s), (x - 2, hy + 3 * s)]
    cv.obj([trees], .5)
    cv.hair(_hlines(trees, 1.5))

    # ---- the channel ------------------------------------------------------------------------
    wy0, wy1 = hy + 3 * s, Y(.76)
    water = _rect(x - 1, wy0, x + w + 1, wy1)
    cv.obj([water], 0)
    yy = _hy(wy0 + 1)
    while yy < wy1:
        t = (yy - wy0) / max(1., wy1 - wy0)
        xx = x - 1 + rng.random() * 6
        while xx < x + w:
            seg = (6 + rng.random() * 14) * (1 + t)
            gap = (1.5 + rng.random() * 3)
            if abs(xx - sx) < 9 * s * (1 + t):
                seg, gap = seg * .35, gap * 1.6
            cv.hair([(xx, yy), (min(x + w + 1, xx + seg), yy)])
            xx += seg + gap
        yy = _hy(yy + (2 if t < .5 else 1.5))

    # ---- the heron (Easter egg) wading on the left ------------------------------------------
    if s >= .62:
        hx_, hb = X(.9), wy0 + (wy1 - wy0) * .62
        k_ = s * 1.2
        body = [(hx_ - 5 * k_, hb - 9 * k_), (hx_ - 1 * k_, hb - 11.5 * k_), (hx_ + 4 * k_, hb - 10 * k_),
                (hx_ + 6 * k_, hb - 7.5 * k_), (hx_ + 2 * k_, hb - 6.5 * k_), (hx_ - 3 * k_, hb - 7 * k_)]
        neck = [(hx_ - 4 * k_, hb - 10 * k_), (hx_ - 6.5 * k_, hb - 14 * k_), (hx_ - 4.5 * k_, hb - 18 * k_),
                (hx_ - 6 * k_, hb - 21 * k_)]
        blacks.append(f'<path d="{_d(body, True, 0)}" fill="#000"/>')
        blacks.append(f'<path d="{_d(neck, tol=0)}" stroke="#000" stroke-width="1" fill="none"/>')
        blacks.append(f'<path d="{_d(_ell(hx_ - 6 * k_, hb - 21.5 * k_, 1.4 * k_, 1.1 * k_, 10), True, 0)}" fill="#000"/>')
        blacks.append(f'<path d="M{_n(hx_ - 7 * k_)},{_n(hb - 21.6 * k_)}l{_n(-5 * k_)},{_n(1.2 * k_)}'
                      f'M{_n(hx_ - 5.6 * k_)},{_n(hb - 22.3 * k_)}l{_n(3.5 * k_)},{_n(-1.4 * k_)}'
                      f'M{_n(hx_)},{_n(hb - 7 * k_)}l{_n(-.6 * k_)},{_n(7 * k_)}M{_n(hx_ + 1.5 * k_)},{_n(hb - 7 * k_)}l{_n(.8 * k_)},{_n(7 * k_)}" '
                      f'stroke="#000" stroke-width=".5" fill="none"/>')
        blacks.append(f'<path d="M{_n(hx_ - 4 * k_)},{_n(_hy(hb + 1.5 * k_))}h{_n(9 * k_)}M{_n(hx_ - 3 * k_)},{_n(_hy(hb + 3.5 * k_))}h{_n(6 * k_)}'
                      f'M{_n(hx_ - 5 * k_)},{_n(_hy(hb + 5.5 * k_))}h{_n(3 * k_)}" stroke="#000" stroke-width="1" fill="none"/>')

    # ---- the near bank, where the station stands ----------------------------------------------
    bank_top = []
    for i in range(41):
        u = i / 40
        v = .79 - .075 * math.exp(-((u - .58) / .28) ** 2) - .012 * math.sin(u * 23 + seed)
        bank_top.append((x - 2 + (w + 4) * u, Y(v)))
    bank = bank_top + [(x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([bank], 1.)
    off = 2.5
    k = 0
    while off < h:
        pitch = 3 if off < 7 * s else (2 if off < 16 * s else 1.5)
        cv.hair([[(px, py + off + .35 * math.sin(px * .21)) for px, py in bank_top]])
        off += pitch
        k += 1

    gr = random.Random(seed + 7)
    blades = []
    for px, py in bank_top[1:-1]:
        for j in range(4):
            bx = px + gr.uniform(-3, 3) * s
            L = gr.uniform(1.5, 3.2) * min(s, 1.3)
            lean = gr.uniform(-.5, .5)
            blades.append([(bx, py + 1.5), (bx + lean * L, py - L)])
    cv.hair(blades)

    # ---- the weather station ----------------------------------------------------------------
    mxs = X(.58)
    uu = (mxs - x + 2) / (w + 4)
    base = Y(.79 - .075 * math.exp(-((uu - .58) / .28) ** 2) - .012 * math.sin(uu * 23 + seed)) + 3 * s
    top = Y(.18) if tall else Y(.13)
    mr = max(1.5, 1.6 * s)
    for dx in (-9, 9, -2.5):
        leg = [(mxs, base - 9 * s), (mxs + dx * s, base + (1.5 if dx != -2.5 else 3) * s)]
        cv.heavy(leg) if dx == -2.5 else cv.line(leg)
    # rain gauge on its own post, left of the mast (empty: 0.00 in)
    gx, gw, gt = mxs - 22 * s, 4.2 * s, base - 16 * s
    cv.obj([_rect(gx - .6 * s, gt + 8 * s, gx + .6 * s, base + 1)], .5)
    can = _rect(gx - gw / 2, gt, gx + gw / 2, gt + 8.5 * s)
    cv.obj([can], 1.)
    cv.hair(C.hatch_poly(_rect(gx - gw / 2, gt, gx - gw * .1, gt + 8.5 * s), 90, 1.5))
    cv.hair(C.hatch_poly(_rect(gx + gw * .25, gt, gx + gw * .4, gt + 8.5 * s), 90, 1.5))
    funnel = [(gx - gw * .75, gt - 2.2 * s), (gx + gw * .75, gt - 2.2 * s), (gx + gw / 2, gt), (gx - gw / 2, gt)]
    cv.obj([funnel], 1.)
    cv.hair(_hlines(funnel, 1.5))
    # the mast
    mast = _rect(mxs - mr, top, mxs + mr, base - 8 * s)
    cv.obj([mast], 1.)
    cv.hair([(mxs - mr * .45, top + 2), (mxs - mr * .45, base - 8 * s)])
    cv.hair([(mxs + mr * .55, top + 2), (mxs + mr * .55, base - 8 * s)])
    # solar panel half-way up, tilted to the sun (right)
    py0 = top + (base - top) * .5
    pw, ph = 15 * s, 9 * s
    panel = [(mxs + mr, py0 - ph * .9), (mxs + mr + pw, py0 - ph * .35), (mxs + mr + pw * .92, py0 + ph * .35),
             (mxs + mr - pw * .05, py0 - ph * .15)]
    cv.obj([panel], 1.)
    cv.hair(C.hatch_poly(panel, 45, 2))
    a, b, c, d = panel
    for t in (.25, .5, .75):
        cv.line([(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (d[0] + (c[0] - d[0]) * t, d[1] + (c[1] - d[1]) * t)])
    cv.line([((a[0] + d[0]) / 2, (a[1] + d[1]) / 2), ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)])
    cv.heavy([(mxs + mr, py0 - ph * .1), (mxs + mr + pw * .5, py0 + ph * .05)])
    # crossed drumsticks = the compass cross (Easter egg)
    cy_ = top + (base - top) * .36
    L = 11.5 * s
    for sg in (-1, 1):
        a0 = math.radians(18 * sg)
        ux, uy = math.cos(a0), math.sin(a0)
        p0 = (mxs - ux * L, cy_ - uy * L)
        p1 = (mxs + ux * L, cy_ + uy * L)
        nx, ny = -uy, ux
        wb, wt = 1.3 * s, .55 * s
        stick = [(p1[0] + nx * wb, p1[1] + ny * wb), (p0[0] + nx * wt, p0[1] + ny * wt),
                 (p0[0] - nx * wt, p0[1] - ny * wt), (p1[0] - nx * wb, p1[1] - ny * wb)]
        cv.obj([stick], 1.)
        cv.hair([((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1])
        cv.obj([_ell(p0[0] - ux * 1.2 * s, p0[1] - uy * 1.2 * s, 1.5 * s, 1.1 * s, 12)], 1.)
    if s >= .7:
        nxp, nyp = mxs - L * .95 - 7 * s, cy_ - L * .31 - 2 * s
        cv.line([(nxp, nyp + 4 * s), (nxp, nyp), (nxp + 3 * s, nyp + 4 * s), (nxp + 3 * s, nyp)])
    # wind vane: arrow pointing north (left) into today's north wind, feathered tail right
    vy = top + (base - top) * .12
    va = 20 * s
    cv.obj([_rect(mxs - va, vy - .6 * s, mxs + va * .8, vy + .6 * s)], 1.)
    head = [(mxs - va - 5 * s, vy), (mxs - va + 1 * s, vy - 3 * s), (mxs - va, vy), (mxs - va + 1 * s, vy + 3 * s)]
    cv.obj([head], 1.)
    cv.hair(_hlines(head, 1.5))
    fin = [(mxs + va * .45, vy), (mxs + va * .62, vy - 6.5 * s), (mxs + va * 1.05, vy - 7.5 * s),
           (mxs + va * .95, vy - 3 * s), (mxs + va * 1.05, vy + 4.5 * s), (mxs + va * .62, vy + 3.5 * s)]
    cv.obj([fin], 1.)
    for t in range(1, 6):
        u = t / 6
        cv.hair([(mxs + va * (.5 + .5 * u), vy - (1 + 5.5 * u) * s), (mxs + va * (.45 + .2 * u), vy + .3)])
    # anemometer on top: hub, three arms, cups
    hub_y = top - 2 * s
    cv.obj([_rect(mxs - .9 * s, hub_y, mxs + .9 * s, top + 1)], 1.)
    arms = [(-11, 1.2), (11, -1.2), (3.5, 3.2)]
    for k_, (dx, dy) in enumerate(arms):
        ex, ey = mxs + dx * s, hub_y + dy * s
        cv.line([(mxs, hub_y), (ex, ey)])
        cr = 3.0 * s * (.85 if k_ == 2 else 1)
        mouth = 1 if k_ != 1 else -1
        cup = _ell(ex, ey, cr * .55, cr, 18, -PI / 2 if mouth > 0 else PI / 2, PI / 2 if mouth > 0 else 1.5 * PI)
        cv.obj([cup], 1.)
        cv.hair(_hlines(cup, 1.5))
    cv.obj([_ell(mxs, hub_y, 1.8 * s, 1.4 * s, 14)], 1.)

    # ---- the sun itself, burning through ----------------------------------------------------
    disc = _ell(sx, sy, sr, sr, 40)
    cv.obj([disc], 1.)
    cv.hair(_hlines(_ell(sx, sy, sr - 1.5, sr - 1.5, 40), 3, 1.5))
    ring = _ell(sx, sy, sr * 1.12, sr * 1.12, 40)
    gd = "".join(_d(g, tol=0) for g in geese)
    blacks.append(f'<path d="{gd}" stroke="#000" stroke-width="1" fill="none"/>')
    return cv.svg() + "".join(blacks) + f'<path d="{_d(ring, True, 0)}" stroke="#000" stroke-width=".5" fill="none"/>'


def _vignette_clipped(cid, clip_d, x, y, w, h, seed):
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{_scene(x, y, w, h, seed)}</g>')


# ------------------------------------------------------------------------------------------------
# tall plate extras
# ------------------------------------------------------------------------------------------------

def _swing_bar(tx, ty, tw, th):
    """the pedestal tablet: a light ruled ground with a bar of swing eighths on a staff (egg)"""
    o = [f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-tw + 2)}z" fill="{C.pat("L")}" stroke="none"/>']
    gap = 2.5 if th >= 16 else 2.
    sy0 = ty + th / 2 - 2 * gap
    sx0, sx1 = tx + tw * .3, tx + tw * .7
    o.append(f'<path d="M{_n(sx0 - 3)},{_n(sy0 - 4)}h{_n(sx1 - sx0 + 6)}v{_n(4 * gap + 8)}h{_n(-(sx1 - sx0 + 6))}z" fill="#fff"/>')
    staff = "".join(f"M{_n(sx0)},{_n(_hy(sy0 + i * gap))}H{_n(sx1)}" for i in range(5))
    o.append(f'<path d="{staff}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{_n(sx0)},{_n(sy0)}v{_n(4 * gap)}M{_n(sx1)},{_n(sy0)}v{_n(4 * gap)}M{_n(sx1 - 2)},{_n(sy0)}v{_n(4 * gap)}" stroke="#000" stroke-width="1"/>')
    notes, stems, beams = [], [], []
    xs = [sx0 + (sx1 - sx0) * (i + .7) / 8.6 for i in range(8)]
    pitches = [2, 3, 1.5, 2.5, 3.5, 2, 1, 1.5]
    for i, (nx, pp) in enumerate(zip(xs, pitches)):
        ny = sy0 + pp * gap
        notes.append(_d(_ell(nx, ny, 1.4, 1.0, 10), True, 0))
        stems.append(f"M{_n(nx + 1.3)},{_n(ny)}V{_n(sy0 - 3)}")
        if i % 2 == 0:
            beams.append(f"M{_n(nx + 1.3)},{_n(sy0 - 3)}H{_n(xs[i + 1] + 1.3)}")
    o.append(f'<path d="{"".join(notes)}" fill="#000"/>')
    o.append(f'<path d="{"".join(stems)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(beams)}" stroke="#000" stroke-width="1.5"/>')
    return "".join(o)


def _ribbon_face_shade(centre, h):
    o = []
    for f in (-.28, 0, .28):
        pts = [(px, py + f * h) for px, py in centre[1:-1]]
        o.append(_d(pts, tol=.2))
    return f'<path d="{"".join(o)}" stroke="#000" stroke-width=".5" fill="none"/>'


# ------------------------------------------------------------------------------------------------
# layouts (from the house library, re-proportioned around the station)
# ------------------------------------------------------------------------------------------------

def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.3, 210.)
    o.append(C._clip(C._uid("tb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .86, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    ia, ib = rx - 4.5, ry - 4.5
    clip_d = _d(_ell(cx, cy, ia, ib, 72), True, 0)
    o.append(_vignette_clipped(C._uid("tbv", w, h, seed), clip_d, cx - ia, cy - ib, 2 * ia, 2 * ib, seed))
    o.append(f'<path d="{clip_d}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 2.1)
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
    o.append(C._clip(C._uid("tm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_vignette_clipped(C._uid("tmv", w, h, seed), inner, *_cart_box(cx, cy, cw, gh + 4), seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .6
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
                   max_n=5, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("tt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_vignette_clipped(C._uid("ttv", w, h, seed), inner, *_cart_box(cx, cy, cw, ch), seed))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_ribbon_face_shade(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_swing_bar(tx + 2, ty + 2, tw - 3, th - 3))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("tf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 1102
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
