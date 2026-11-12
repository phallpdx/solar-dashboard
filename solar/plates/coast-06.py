"""coast-06 'Whale watch': the first southbound gray whales passing Cape Lookout, early winter.

The vignette is an engraved seascape cut into the house cartouche: the long forested headland of
Cape Lookout reaching out to sea from the right, a gray whale surfacing in the foreground heading
south (left) with its heart-shaped blow, a second whale throwing its flukes up as it sounds, the
sea ruled in perspective. The tall plate's tablet carries the migration itself: a procession of
gray whales on the swell. Easter egg: Parker's dog sits at the very tip of the cape, watching.
"""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
_n = C._n
_d = C._d


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def _pip(x, y, poly):
    ins = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            ins = not ins
        j = i
    return ins


def _clip_pl(pl, poly, step=.7):
    """Clip a polyline to a polygon by dense sampling; returns list of polylines."""
    pts = []
    for (x0, y0), (x1, y1) in zip(pl, pl[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L / step))
        for i in range(k):
            t = i / k
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    pts.append(pl[-1])
    out, cur = [], []
    for p in pts:
        if _pip(p[0], p[1], poly):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _clip_many(pls, poly):
    o = []
    for pl in pls:
        o.extend(_clip_pl(pl, poly))
    return o


def _dash(pl, on, off, phase=0.):
    """Break a polyline into dashes (for broken water lines)."""
    out, cur, s = [], [], -phase
    for (x0, y0), (x1, y1) in zip(pl, pl[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L / .6))
        for i in range(k):
            t = i / k
            p = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            m = s % (on + off)
            if m < on:
                cur.append(p)
            elif cur:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
            s += L / k
    if len(cur) > 1:
        out.append(cur)
    return out


# ----------------------------------------------------------------------------------------------
# the seascape vignette
# ----------------------------------------------------------------------------------------------

def _whale_back(cv, solids, x0, x1, wl, hb, rng, blow=True):
    """A gray whale surfacing, head to the left (southbound): the blunt mottled head lifting out of
    the water with mouth line and eye, the blowholes and their V blow, the long back with its low
    hump and the knuckled ridge running back into the sea."""
    L = x1 - x0
    n = 80
    top = []
    for i in range(n + 1):
        u = i / n
        if u < .3:      # the sloping wedge of the head up to the blowholes
            y = hb * (.18 + .7 * (u / .3) ** .85)
        elif u < .4:    # the slight dip behind the blowholes
            y = hb * (.88 - .06 * math.sin(PI * (u - .3) / .1))
        else:
            y = hb * (.88 + .1 * math.sin(PI * min(1., (u - .4) / .3) * .5) - 1.0 * ((u - .4) / .6) ** 2.2 * .98)
        if .6 < u < .76:
            y += hb * .06 * math.sin(PI * (u - .6) / .16)           # the hump
        if u > .78:
            y += hb * .04 * abs(math.sin((u - .78) * 70))           # knuckles
        top.append((x0 + L * u, wl - y))
    # blunt rostrum: round the front
    front = [(x0 - hb * .06 * math.sin(PI * t), wl - hb * .18 * t) for t in [k / 8 for k in range(9)]]
    body = front + top[1:] + [(x1 + 1, wl + 1), (x0, wl + 1)]
    cv.obj([body], 1.)
    # contour hatching: a white highlight along the crown, lines follow the back, close below
    lines = []
    off = 2.6
    while off < hb * 1.1:
        lines.append([(x, y + off) for x, y in top])
        off += 1.5
    cv.hair(_clip_many(lines, body))
    flank = [(x, min(wl, y + hb * .3)) for x, y in top]
    cv.hair(C.hatch_poly([(x0, wl)] + flank + [(x1, wl)], 158, 2, .3))
    belly = [(x, min(wl, y + hb * .62)) for x, y in top]
    cv.hair(C.hatch_poly([(x0, wl)] + belly + [(x1, wl)], 22, 2, .7))
    cv.line(_clip_pl([(x0, wl - 1.)] + [(x0 + L, wl - 1.)], body))
    cv.heavy(_clip_pl([(x0, wl - .2), (x1, wl - .2)], body))
    # mouth line and eye
    mouth = [(x0 + L * u * .27, wl - hb * (.1 + .16 * math.sin(PI * u * .8))) for u in [k / 12 for k in range(13)]]
    cv.heavy(mouth)
    ex, ey = x0 + L * .29, wl - hb * .3
    solids.append(C._ell_pts(ex, ey, max(.8, hb * .05), max(.6, hb * .035), 10)[:-1])
    # blowholes
    bi = int(n * .3)
    bx, by = top[bi]
    for k in (-1, 1):
        cv.obj([C._ell_pts(bx + k * hb * .1, by + 1.4, hb * .08, hb * .03, 10)[:-1]], 1.)
    # barnacles and scars, clustered on the head, scattered along the back
    for i in range(int(L / 2.6)):
        u = rng.betavariate(1.2, 3.2) * .9
        tx, ty = top[int(u * n)]
        dep = rng.uniform(.1, .75) * (wl - ty)
        r = rng.uniform(.7, 1.8) * max(.7, hb / 26)
        if dep < r + 2.2 or (u < .27 and ty + dep > wl - hb * (.2 + .1 * math.sin(PI * u / .26)) - r - 1):
            continue
        cx, cy = tx + rng.uniform(-2, 2), ty + dep
        if rng.random() < .3:   # a long pale scar
            p = C._ell_pts(cx, cy, r * 2.6, r * .5, 10)[:-1]
        else:
            p = C._ell_pts(cx, cy, r * rng.uniform(1, 1.5), r, 9)[:-1]
        cv.obj([p], .5)
        if rng.random() < .4:
            solids.append(C._ell_pts(cx + .2, cy + .2, r * .4, r * .3, 7)[:-1])
    # bow wave curling off the head, wake trailing behind
    for j in range(4):
        r = hb * (.25 + .14 * j)
        cv.hair(_dash(C._ell_pts(x0 - hb * .05, wl + .5, r, r * .35, 24, PI * .5, PI * 1.1), 3, 1.1, j))
    for j in range(3):
        yy = wl + 1 + j * 1.8
        cv.hair(_dash([(x1 - L * .1, yy), (x1 + L * .3, yy + j * .4)], 3, 1.2, j))
    if blow:
        _blow(cv, bx, by + .5, hb * 1.7, rng)
    return top


def _blow(cv, x, y, H, rng):
    """The gray whale's heart-shaped V blow: two rounded plumes of mist leaning apart, stippled
    densely at their rims and streaked where the jets rise."""
    for side in (-1, 1):
        tilt = side * .42
        cxp, cyp = x + side * H * .2, y - H * .48
        rx, ry = H * .2, H * .44
        plume = []
        for i in range(28):
            a = 2 * PI * i / 28
            ex, ey = rx * math.cos(a), ry * math.sin(a)
            if ey > 0:  # narrow toward the blowhole
                ex *= 1 - .75 * (ey / ry)
            plume.append((cxp + ex * math.cos(tilt) - ey * math.sin(tilt), cyp + ex * math.sin(tilt) + ey * math.cos(tilt)))
        cv.obj([plume], 0)
        dots = []
        xs = [p[0] for p in plume]
        ys = [p[1] for p in plume]
        gy = min(ys)
        while gy < max(ys):
            gx = min(xs) + (gy * 7) % 1.7
            while gx < max(xs):
                px, py = gx + rng.uniform(-.4, .4), gy + rng.uniform(-.4, .4)
                if _pip(px, py, plume):
                    # distance to the rim ~ how dense
                    dmin = min(math.hypot(px - q[0], py - q[1]) for q in plume[::2])
                    if rng.random() < max(.12, 1 - dmin / (rx * .7)):
                        dots.append([(px, py), (px + .5, py + .15)])
                gx += 1.7
            gy += 1.7
        cv.hair(dots)
        stk = []
        for j in range(5):
            sx = x + side * j * .5
            stk.append(_dash([(sx, y), (sx + side * H * (.15 + .07 * j), y - H * (.55 + .07 * j))], 2.2, 1.2, j * .7))
        for st in stk:
            cv.hair(_clip_many(st, plume))


def _flukes(cv, cx, wl, s, rng):
    """Flukes raised as a whale sounds: a slim tail stock and broad swept blades, dark, water
    streaming from the trailing edge, a ring of splash at the stock."""
    stock = [(cx - s * .06, wl + .5), (cx - s * .045, wl - s * .35), (cx - s * .03, wl - s * .55),
             (cx + s * .03, wl - s * .55), (cx + s * .045, wl - s * .35), (cx + s * .06, wl + .5)]
    n = 30
    lead, trail = [], []
    for i in range(n + 1):
        t = i / n
        e = (t - .5) * 2           # -1 .. 1
        ae = abs(e)
        x = cx + e * s * .5
        base = wl - s * .55 - s * .38 * ae ** 1.5        # blades sweep up and out
        lead.append((x, base + s * .2 * (1 - ae) ** .7 + s * .035))
        notch = s * .06 * max(0, 1 - ae / .07)
        trail.append((x, base - s * .02 + notch + s * .05 * math.sin(PI * ae) * ae))
    shape = trail + lead[::-1]
    cv.obj([stock], 1.)
    cv.hair(C.hatch_poly(stock, 90, 1.5))
    cv.hair(C.hatch_poly(stock, 15, 2))
    cv.obj([shape], 1.)
    cv.hair(_clip_many([[(p[0], p[1] + k) for p in trail] for k in (1.5, 3, 4.5, 6, 7.5, 9)], shape))
    cv.hair(C.hatch_poly(shape, 70, 1.5))
    drips = []
    for i in range(1, n, 2):
        x, y = lead[i]
        Ld = (wl - y) * rng.uniform(.3, .85)
        drips.append(_dash([(x, y + 1), (x + rng.uniform(-.5, .5), y + Ld)], 1.6, 1.3, rng.random() * 2))
    for d in drips:
        cv.hair(d)
    for j in range(3):
        r = s * (.12 + .1 * j)
        cv.hair(_dash(C._ell_pts(cx, wl + 1 + j * 1.2, r, r * .18, 30, 0, PI), 2, 1.3, j))


def _dog_sitting(x, y, s):
    """Tiny sitting dog in profile, facing left (out to sea), base at (x, y). Black silhouette."""
    pts = [(0, 0), (-.5, -2.5), (-.2, -5), (-1.4, -7.4), (-2.6, -7.7), (-3.4, -8.6), (-2.3, -9.0),
           (-1.3, -9.6), (-.3, -10.6), (.7, -10), (.9, -8.4), (1.5, -6), (3.0, -4.4), (4.4, -3.6),
           (5.6, -2.0), (6.6, -1.6), (7.0, -.6), (5.5, -.3), (5, 0)]
    return [(x + px * s, y + py * s) for px, py in pts]


def seascape(cv, solids, x, y, w, h, seed, detail=1.):
    """Fill the box (x, y, w, h) completely: sky, Cape Lookout, sea, whales."""
    rng = random.Random(seed)
    hz = y + h * (.42 if h > w * .7 else .46)
    box = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    # sky: ruled, darker at the zenith (pitch 2 above, 3 toward the horizon)
    sky = [(x, y), (x + w, y), (x + w, hz), (x, hz)]
    cv.obj([sky], 0)
    yy = y + .5
    lines = []
    while yy < hz:
        pitch = 2. if yy < y + (hz - y) * .45 else 3.
        lines.append([(x, yy), (x + w, yy)])
        yy += pitch
    cv.hair(lines)
    # low winter cloud bank: lines doubled under each billow
    cl = []
    for i in range(int(w / 14) + 2):
        cx = x + i * 14 + rng.uniform(-3, 3)
        cy = y + (hz - y) * rng.uniform(.25, .4)
        r = rng.uniform(6, 10) * min(1, h / 120)
        cl.append(C._ell_pts(cx, cy, r * 1.4, r * .8, 18, 0, PI))
    cv.hair(_clip_many(cl, sky))
    # gulls
    for i in range(3 if w > 120 else 1):
        gx, gy = x + w * rng.uniform(.15, .55), y + (hz - y) * rng.uniform(.15, .55)
        g = rng.uniform(2.2, 3.5) * min(1.2, w / 150)
        cv.obj([[(gx - g, gy), (gx - g * .5, gy - g * .5), (gx, gy), (gx + g * .5, gy - g * .5), (gx + g, gy), (gx, gy + g * .25)]], 0)
        cv.line([(gx - g, gy), (gx - g * .5, gy - g * .5), (gx, gy), (gx + g * .5, gy - g * .5), (gx + g, gy)])

    # Cape Lookout: a long headland from the right, cliff at its tip
    tipx = x + w * .5
    capeH = (hz - y) * .36
    ridge = []
    n = 80
    for i in range(n + 1):
        u = i / n
        px = tipx + (x + w + 2 - tipx) * u
        # cliff rises fast at the tip, a forested spine, dropping slightly to the land
        hgt = capeH * (min(1, u / .06) ** .7) * (.78 + .22 * math.sin(PI * min(1, u * 1.4)))
        ridge.append((px, hz - hgt))
    cape = [(tipx - capeH * .15, hz + 1)] + ridge + [(x + w + 2, hz + 1)]
    cv.obj([cape], 1.)
    # forest crown: serrated spruce silhouette along the ridge
    crown = []
    for i in range(n + 1):
        px, py = ridge[i]
        tooth = (.8 + 1.4 * rng.random()) * (1 if i % 2 else -.1) * min(1.2, capeH / 22)
        crown.append((px, py - tooth))
    forest = crown + [(p[0], p[1] + capeH * .35) for p in ridge[::-1]]
    cv.obj([forest], .5)
    cv.hair(C.hatch_poly(forest, 90, 1.5))
    cv.hair(C.hatch_poly(forest, 30, 1.5))
    # cliff face below forest: vertical strata, cross-hatched on the shadowed seaward face
    face = [(p[0], p[1] + capeH * .35) for p in ridge] + [(x + w + 2, hz + 1), (tipx - capeH * .15, hz + 1)]
    cv.hair(C.hatch_poly(face, 82, 2))
    shadow = [(tipx - capeH * .15, hz + 1), ridge[0], ridge[4], (ridge[4][0] + 3, hz + 1)]
    cv.hair(C.hatch_poly(shadow, 0, 1.5))
    cv.hair(C.hatch_poly([(p[0], p[1] + capeH * .5) for p in ridge] + [(x + w + 2, hz + 1), (tipx, hz + 1)], 20, 2))
    # sea stack off the tip, surf
    sx = tipx - capeH * .5
    stack = [(sx - capeH * .12, hz + .5), (sx - capeH * .06, hz - capeH * .3), (sx + capeH * .05, hz - capeH * .34),
             (sx + capeH * .1, hz + .5)]
    cv.obj([stack], 1.)
    cv.hair(C.hatch_poly(stack, 90, 1.5))
    cv.hair(C.hatch_poly(stack, 0, 2))
    # Easter egg: the dog sitting at the tip of the cape, looking out to sea
    dx, dy = ridge[3][0] + 1.5, ridge[3][1] - 1.2
    solids.append(_dog_sitting(dx, dy, max(.42, min(.75, h / 300))))

    # sea: ruled water widening toward the foreground
    sea = [(x, hz), (x + w, hz), (x + w, y + h), (x, y + h)]
    cv.obj([sea], 0)
    wl_lines = []
    yy = hz + 1.
    i = 0
    while yy < y + h + 1:
        dep = (yy - hz) / (y + h - hz)
        amp = .2 + 1.6 * dep
        per = 8 + 26 * dep
        ph = rng.uniform(0, 6)
        pl = [(x + t, yy + amp * math.sin((x + t) / per * 2 * PI + ph)) for t in range(0, int(w) + 2, 2)]
        if dep > .25:
            wl_lines.extend(_dash(pl, per * 1.4, per * .25, rng.uniform(0, per)))
        else:
            wl_lines.append(pl)
        yy += 1.5 if dep < .15 else 2.
        i += 1
    cv.hair(wl_lines)
    # dark troughs in the foreground: short heavier strokes
    tr = []
    for j in range(int(w * h / 900 * detail)):
        tx = x + rng.uniform(0, w)
        ty = hz + (y + h - hz) * rng.uniform(.35, 1)
        L = 3 + 6 * (ty - hz) / (y + h - hz)
        tr.append([(tx, ty), (tx + L * .5, ty + .5), (tx + L, ty)])
    cv.line(tr)
    # reflection streak under the cape
    cv.hair(C.hatch_poly([(tipx, hz + 1), (x + w, hz + 1), (x + w, hz + 4 + capeH * .2), (tipx + 6, hz + 3)], 0, 1.5))

    # distant whale sounding (flukes) left of the cape, a far blow on the horizon
    fs = min(w * .2, (y + h - hz) * .6)
    _flukes(cv, x + w * .2, hz + (y + h - hz) * .3, fs, rng)
    _blow(cv, x + w * .9, hz + .5, max(3, fs * .18), rng)
    # the foreground whale, swimming south (left)
    wl = hz + (y + h - hz) * .74
    hb = min((y + h - hz) * .5, w * .17)
    _whale_back(cv, solids, x + w * .17, x + w * 1.0, wl, hb, rng)
    return box


def vignette_svg(field_d, x, y, w, h, seed, uid, detail=1.):
    cv = C.Canvas()
    solids = []
    seascape(cv, solids, x, y, w, h, seed, detail)
    body = cv.svg()
    if solids:
        body += f'<path d="{"".join(_d(p, True, 0) for p in solids)}" fill="#000" stroke="none"/>'
    return (f'<clipPath id="{uid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{uid})">{body}</g>')


# ----------------------------------------------------------------------------------------------
# migration tablet and banner face
# ----------------------------------------------------------------------------------------------

def _tiny_whale(cv, solids, x, y, L, rng, blow):
    """A small gray whale back on the swell, head left, with optional blow."""
    hb = L * .2
    top = []
    for i in range(21):
        u = i / 20
        top.append((x + L * u, y - hb * math.sin(PI * u) ** .7 * (1 - .4 * u)))
    body = [(x, y + .5)] + top + [(x + L, y + .5)]
    cv.obj([body], 1.)
    cv.hair(_clip_many([[(p[0], p[1] + off) for p in top] for off in (1.5, 3)], body))
    if blow:
        bx = x + L * .2
        cv.hair([[(bx, y - hb), (bx - L * .12, y - hb - L * .3)], [(bx + 1, y - hb), (bx + L * .14, y - hb - L * .3)]])
        for j in range(5):
            a = rng.uniform(0, 2 * PI)
            r = rng.uniform(0, L * .12)
            for sd in (-1, 1):
                px, py = bx + sd * L * .12 + r * math.cos(a), y - hb - L * .32 + r * math.sin(a) * .6
                cv.hair([(px, py), (px + .5, py)])


def tablet_svg(tx, ty, tw, th, seed, uid):
    rng = random.Random(seed)
    cv = C.Canvas()
    solids = []
    box = [(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th)]
    cv.obj([box], 0)
    lines = []
    yy = ty + 2
    while yy < ty + th:
        pl = [(tx + t, yy + .6 * math.sin(t / 7 + yy)) for t in range(0, int(tw) + 2, 2)]
        lines.append(pl)
        yy += 2. if yy < ty + th * .5 else 1.5
    cv.hair(lines)
    n = max(3, int(tw / 55))
    for i in range(n):
        L = th * rng.uniform(2.0, 2.6)
        x = tx + 10 + (tw - 20 - L) * (i + rng.uniform(-.15, .15)) / max(1, n - 1)
        _tiny_whale(cv, solids, x, ty + th * rng.uniform(.72, .82), L, rng, i % 2 == 0)
    # a southbound arrow of swell along the bottom
    body = cv.svg()
    return (f'<clipPath id="{uid}"><path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(2 - tw)}z"/></clipPath>'
            f'<g clip-path="url(#{uid})">{body}</g>')


def banner_face(centre, h):
    """Engrave the ribbon face: a running wave (the swell the whales ride) with stippled crests."""
    o = []
    pts = centre
    wave = []
    n = len(pts) - 1
    for i in range(n * 4 + 1):
        t = i / (n * 4)
        k = min(n - 1, int(t * n))
        f = t * n - k
        x = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f
        y = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f
        wave.append((x, y + h * .22 * math.sin(t * n * 1.6)))
    o.append(_d(wave[2:-2], tol=.1))
    for off in (-h * .3, h * .3):
        o.append(_d([(p[0], p[1] + off) for p in pts[1:-1]], tol=.1))
    return f'<path d="{"".join(o)}" fill="none" stroke="#000" stroke-width=".5"/>'


# ----------------------------------------------------------------------------------------------
# layouts (house layouts with the field filled edge to edge)
# ----------------------------------------------------------------------------------------------

def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = C._ell_pts(cx, cy, rx - 2, ry - 2, 64)[:-1]
    o.append(vignette_svg(_d(field, True, 0), cx - rx, cy - ry, 2 * rx, 2 * ry, seed, C._uid("bv", w, h, seed), .6))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
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
                   max_n=int(9 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = cw / 2, (gh + 4) / 2
    o.append(vignette_svg(field, cx - a, cy - b, 2 * a, 2 * b, seed, C._uid("mv", w, h, seed), .8))
    o.append(C.knurled_bar(0, h - foot, w, foot))
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
    # the strip above the panel is not left white: a light ruled ground the crest rises through
    o.append(C.dark_ground((0, 0, w, py0), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .48, ph * .6
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=int(9 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(vignette_svg(field, cx - cw / 2, cy - ch / 2, cw, ch, seed, C._uid("tv", w, h, seed)))
    # crest: a gray whale's flukes rising out of the cartouche, carved over a small palmette
    ps = min(ch * .2 + top_free, 62)
    o.append(C.palmette(cx, cy - ch / 2 + 7, ps * .8, True, rng.randrange(1 << 20)))
    fc = C.Canvas()
    _flukes(fc, cx, cy - ch / 2 + 6, ps * 1.5, random.Random(seed + 3))
    o.append(fc.svg())
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(banner_face(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(tablet_svg(tx + 2, ty + 2, tw - 2.5, th - 2.5, seed + 11, C._uid("tb", w, h, seed)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh), "L"))
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 606
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
