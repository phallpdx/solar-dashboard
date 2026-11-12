"""Sports plate: the Blazers. A ball dropping through an outdoor hoop on a Portland court under
Mt. Hood, set in the house acanthus frame. The banner reads RIP CITY; the pedestal tablet carries
F1 chequered ribbons running out from a small basketball medallion, and behind that ball, the
Easter egg: Parker's crossed drumsticks."""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_n, _d, _ell = C._n, C._d, C._ell_pts
hp = C.hatch_poly


def _circle(cx, cy, r, n=40):
    return _ell(cx, cy, r, r, n)[:-1]


# ----------------------------------------------------------------------------------------------
# the basketball, in engraved relief
# ----------------------------------------------------------------------------------------------

def ball(cv, cx, cy, r, rot=-.5, light=True):
    disc = _circle(cx, cy, r, max(24, int(r * 3)))
    cv.obj([disc], 1.5 if r > 6 else 1.)
    big = r > 9
    # body tone: 45-degree bulino over the whole ball
    cv.hair(hp(disc, 45, 2 if big else 1.5, .25))
    # core shadow: a crescent lower right, cross-hatched, a darker core inside it
    a0, a1 = -PI / 4 - .3, 3 * PI / 4 + .3
    def arc(ccx, ccy, rr, rev=False):
        pts = [(ccx + rr * math.cos(a0 + (a1 - a0) * i / 28), ccy + rr * math.sin(a0 + (a1 - a0) * i / 28)) for i in range(29)]
        return pts[::-1] if rev else pts
    off = r * .26
    crescent = arc(cx, cy, r) + arc(cx - off, cy - off, r * .97, True)
    cv.hair(hp(crescent, -45, 2 if big else 1.5, .5))
    if big:
        core = arc(cx, cy, r)[5:24] + arc(cx + r * .02, cy + r * .02, r * .86, True)[5:24]
        cv.line(hp(core, 45, 2, .5))
    if light:
        cv.obj([_ell(cx - r * .4, cy - r * .42, r * .26, r * .17, 16)[:-1]], 0)
        cv.obj([], 0)
    # seams, in the ball's own frame (rotated by rot): a meridian, an equator, two side arcs
    c, s = math.cos(rot), math.sin(rot)
    T = lambda u, v: (cx + r * (u * c - v * s), cy + r * (u * s + v * c))
    inside = lambda u, v: u * u + v * v <= .995
    N = 36
    seams = []
    seams.append([T(.10 * (1 - v * v), v) for v in [-1 + 2 * i / N for i in range(N + 1)]])
    seams.append([T(u, -.16 * (1 - u * u)) for u in [-1 + 2 * i / N for i in range(N + 1)]])
    for sg in (-1, 1):
        R2, ox = 1.0, sg * 1.42
        pts = []
        for i in range(N + 1):
            t = -1.2 + 2.4 * i / N
            u, v = ox - sg * R2 * math.cos(t), R2 * math.sin(t)
            if inside(u, v):
                pts.append(T(u, v))
        seams.append(pts)
    if big:
        cv.heavy(seams)
    else:
        cv.line(seams)


# ----------------------------------------------------------------------------------------------
# the scene: hoop on a Portland court under Mt. Hood
# ----------------------------------------------------------------------------------------------

def scene(x, y, w, h, clip_d, seed=0):
    rng = random.Random(seed)
    cv = C.Canvas()
    hz = y + h * .60                     # horizon
    X = lambda f: x + w * f
    Y = lambda f: y + h * f
    # sky: ruled, closer near the zenith, with sun rays (gaps) from behind the mountain
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, hz + 1), (x - 2, hz + 1)]
    cv.obj([], 0)
    top = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, Y(.22)), (x - 2, Y(.22))]
    low = [(x - 2, Y(.22)), (x + w + 2, Y(.22)), (x + w + 2, hz + 1), (x - 2, hz + 1)]
    cv.line(hp(top, 0, 2, .5))
    cv.hair(hp(low, 0, 2, .25))
    # clouds: white lenses with a dark underside
    for (fx, fy, fr) in ((.13, .17, .11), (.86, .1, .09), (.62, .27, .07)):
        ccx, ccy, rw = X(fx), Y(fy), w * fr
        cl = []
        for i in range(25):
            a = PI + PI * i / 24
            bump = 1 + .18 * math.sin(i * 1.3 + seed)
            cl.append((ccx + rw * math.cos(a), ccy + rw * .42 * bump * math.sin(a)))
        cl += [(ccx + rw * .8, ccy + rw * .08), (ccx - rw * .8, ccy + rw * .08)]
        cv.obj([cl], .5)
        cv.hair(hp([(ccx - rw, ccy - rw * .1), (ccx + rw, ccy - rw * .1), (ccx + rw * .8, ccy + rw * .08), (ccx - rw * .8, ccy + rw * .08)], 0, 1.5, .25))
    # Mt. Hood: left of centre, white snowfield, shaded slopes
    px, pk = X(.27), Y(.20)
    L0, R0 = X(-.12), X(.72)
    ridge = [(L0, hz)]
    for i in range(1, 30):
        t = i / 30
        xx = L0 + (px - L0) * t
        yy = hz - (hz - pk) * (t ** 1.7) + rng.uniform(-.6, .6)
        ridge.append((xx, yy))
    ridge.append((px, pk))
    for i in range(1, 30):
        t = i / 30
        xx = px + (R0 - px) * t
        yy = pk + (hz - pk) * (t ** .62) + rng.uniform(-.6, .6)
        ridge.append((xx, yy))
    ridge.append((R0, hz))
    cv.obj([ridge + [(R0, hz + 1), (L0, hz + 1)]], 1.)
    # sunlit (left) face: light diagonal; shadow (right) face: dense
    snowline = lambda xx: pk + (hz - pk) * (.42 + .1 * math.sin((xx - px) * .21))
    lface = [p for p in ridge if p[0] <= px] + [(px, hz), (L0, hz)]
    rface = [(px, pk)] + [p for p in ridge if p[0] > px] + [(px, hz)]
    # lower slopes (below snowline): forest tone
    cv.hair(hp(ridge + [(R0, hz + 1), (L0, hz + 1)], 75, 3, .25))
    cv.hair(hp(rface, -60, 2, .5))
    lower = [(L0, hz)] + [(xx, max(snowline(xx), next(p[1] for p in ridge if p[0] >= xx)))
                          for xx in [L0 + (R0 - L0) * i / 60 for i in range(61)]] + [(R0, hz)]
    cv.hair(hp(lower, 60, 2, .25))
    # snow: crevasse gullies running down from the peak, shadow side hatched
    snow_r = [(px, pk)] + [p for p in ridge if px < p[0] and p[1] < snowline(p[0])] + [(px + w * .02, snowline(px))]
    if len(snow_r) > 2:
        cv.hair(hp(snow_r + [(px, snowline(px))], -60, 2, .5))
    for k in range(-3, 5):
        g = []
        x0 = px + k * w * .025
        for i in range(12):
            t = i / 11
            gx = x0 + k * w * .03 * t + math.sin(t * 5 + k) * 1.2
            gy = pk + (hz - pk) * (.05 + abs(k) * .03) + t * (hz - pk) * .35
            ry = next((p[1] for p in ridge if p[0] >= gx), hz)
            if gy > ry + 1.5:
                g.append((gx, gy))
        if len(g) > 1:
            cv.hair(g)
    # snowline: a dark, ragged edge where the forest meets the snow
    sl = []
    for i in range(61):
        xx = L0 + (R0 - L0) * i / 60
        ry = next(p[1] for p in ridge if p[0] >= xx)
        yy = snowline(xx) + rng.uniform(-1, 1.5)
        if yy > ry + 1:
            sl.append((xx, yy))
        elif len(sl) > 1:
            cv.line(sl)
            sl = []
    if len(sl) > 1:
        cv.line(sl)
    # fir line along the horizon, black with white tips of light
    firs = []
    xx = x - 4
    while xx < x + w + 4:
        fh = h * rng.uniform(.035, .075)
        fw = fh * .45
        firs.append([(xx - fw, hz + 1), (xx, hz - fh), (xx + fw, hz + 1)])
        xx += fw * rng.uniform(.9, 1.4)
    cv.obj([[(x - 4, hz - 1), (x + w + 4, hz - 1), (x + w + 4, hz + 2.5), (x - 4, hz + 2.5)]] + firs, 0)
    for f in firs:
        cv.hair(hp(f, 0, 1.5, .25 + (hz % 1)))
        cv.line(hp(f, 90, 1.5))
    # the court: planks in perspective to a vanishing point, boards and nail rows
    vx, vy = X(.5), hz - h * .25
    floor = [(x - 4, hz + 2), (x + w + 4, hz + 2), (x + w + 4, y + h + 4), (x - 4, y + h + 4)]
    cv.obj([floor], 1.)
    k = -24
    while k <= 24:
        fx = X(.5) + k * w * .055
        bx = vx + (fx - vx) * ((y + h + 4 - vy) / (hz + 2 - vy))
        cv.hair([(vx + (fx - vx) * ((hz + 2 - vy) / (hz + 2 - vy)), hz + 2), (bx, y + h + 4)])
        k += .25
    # grain / board ends: horizontal rows spaced in perspective
    rows = []
    d = 1.
    yy = hz + 2
    while yy < y + h + 4:
        rows.append(yy)
        d *= 1.22
        yy += d
    # staggered board ends between the planks
    for i in range(1, len(rows)):
        y0_, y1_ = rows[i - 1], rows[i]
        f0 = (y0_ - vy) / (y + h + 4 - vy)
        kk = -96 + (i % 3)
        while kk <= 96:
            fx = X(.5) + kk * w * .01375
            xa = vx + (fx - vx) * ((y0_ - vy) / (hz + 2 - vy))
            sp = w * .01375 * ((y0_ - vy) / (hz + 2 - vy))
            if x - 4 < xa < x + w + 4 and y1_ - y0_ > 2.5:
                cv.hair([(xa, y0_ + .25), (xa + sp, y0_ + .25)])
            kk += 3
    # painted lane (the key) and free-throw circle: hatched darker
    cx_ = X(.69)
    t = lambda f: hz + 2 + (y + h + 4 - hz - 2) * f
    def pv(xb, f):
        yy_ = t(f)
        return (vx + (xb - vx) * ((yy_ - vy) / (y + h + 4 - vy)), yy_)
    lane = [pv(cx_ - w * .12, .05), pv(cx_ + w * .12, .05), pv(cx_ + w * .24, 1.), pv(cx_ - w * .24, 1.)]
    cv.obj([lane], 1.5)
    cv.hair(hp(lane, 45, 3))
    cv.hair(hp(lane, -45, 3))
    ftc = [((pv(cx_ + w * .2 * math.cos(a), .62))[0], t(.62) + (y + h - t(.62)) * .25 * math.sin(a)) for a in [PI * i / 24 for i in range(25)]]
    cv.line(ftc)
    # long shadow of the pole across the boards
    # the pole, its arm, the backboard, rim and net
    polex, pole_w = X(.91), max(3., w * .03)
    pole_top = Y(.21)
    pole = [(polex - pole_w / 2, pole_top), (polex + pole_w / 2, pole_top), (polex + pole_w / 2, Y(.93)), (polex - pole_w / 2, Y(.93))]
    sh = [(polex - pole_w / 2, Y(.93)), (polex + pole_w / 2, Y(.93)), (X(.40), Y(1.04)), (X(.34), Y(1.04))]
    cv.obj([sh], 0)
    cv.line(hp(sh, 0, 1.5, .5))
    cv.obj([pole], 1.)
    cv.line(hp([(polex + pole_w * .05, pole_top), (polex + pole_w / 2, pole_top), (polex + pole_w / 2, Y(.93)), (polex + pole_w * .05, Y(.93))], 90, 1.5, .5))
    bw_, bh_ = w * .34, w * .22
    bcx = X(.69)
    btop = Y(.15)
    arm = [(bcx + bw_ * .3, btop + bh_ * .42), (polex, pole_top + 3), (polex, pole_top + 7), (bcx + bw_ * .3, btop + bh_ * .62)]
    cv.obj([arm], 1.)
    cv.line(hp(arm, 0, 1.5, .25))
    board = [(bcx - bw_ / 2, btop), (bcx + bw_ / 2, btop), (bcx + bw_ / 2, btop + bh_), (bcx - bw_ / 2, btop + bh_)]
    cv.obj([board], 1.5)
    # board face: vertical glass streaks, a carved frame and the inner shooter's square
    inb = [(bcx - bw_ / 2 + 2.5, btop + 2.5), (bcx + bw_ / 2 - 2.5, btop + 2.5), (bcx + bw_ / 2 - 2.5, btop + bh_ - 2.5), (bcx - bw_ / 2 + 2.5, btop + bh_ - 2.5)]
    cv.line([inb[0], inb[1], inb[2], inb[3], inb[0]])
    cv.hair(hp(inb, 90, 3, .25))
    sq = [(bcx - bw_ * .17, btop + bh_ * .42), (bcx + bw_ * .17, btop + bh_ * .42), (bcx + bw_ * .17, btop + bh_ - 3.5), (bcx - bw_ * .17, btop + bh_ - 3.5)]
    cv.obj([sq], 1.5)
    cv.hair(hp(sq, 45, 2))
    # Blazers pinwheel above the square: five and five swept bars
    pcx, pcy, pr = bcx, btop + bh_ * .22, bh_ * .14
    for s in (-1, 1):
        for i in range(5):
            off_ = (i - 2) * pr * .32
            bar = []
            for j in range(9):
                tt = j / 8
                bar.append((pcx + s * (pr * .15 + tt * pr * 1.6) , pcy + off_ * (1 - .5 * tt) - s * tt * pr * .25))
            cv.line(bar)
    # rim and net
    rimx, rimy = bcx, btop + bh_ + 2
    rr = bw_ * .23
    rim = _ell(rimx, rimy + rr * .3, rr, rr * .3, 40)
    cv.obj([], 0)
    nb = max(5, int(rr / 2.2))
    depth = rr * 1.25
    strands = []
    for i in range(nb + 1):
        a = PI * i / nb
        tx0 = rimx - rr * math.cos(a)
        ty0 = rimy + rr * .3 + rr * .3 * math.sin(a)
        for s in (-1, 1):
            st = []
            for j in range(7):
                f = j / 6
                ww = rr * (1 - .38 * f)
                ang = a + s * f * PI / nb * 3
                st.append((rimx - ww * math.cos(ang), rimy + rr * .3 + rr * .3 * (1 - .4 * f) * math.sin(ang) + depth * f))
            strands.append(st)
    cv.hair(strands)
    cv.hair([[(rimx - rr * (1 - .38 * f) * math.cos(PI * i / 30), rimy + rr * .3 + rr * .3 * (1 - .4 * f) * math.sin(PI * i / 30) + depth * f)
             for i in range(31)] for f in (.5, 1.)])
    cv.obj([], 0)
    cv.heavy(rim)
    cv.line([(rimx - rr * .2, rimy + rr * .2), (rimx - rr * .2, btop + bh_), (rimx + rr * .2, btop + bh_), (rimx + rr * .2, rimy + rr * .2)])
    # the ball, dropping toward the rim along a dotted arc
    br = max(5., w * .078)
    bx, by = X(.47), Y(.27)
    arc = []
    for i in range(40):
        tt = i / 39
        ax = X(.04) + (bx - X(.04)) * tt
        ay = Y(.64) - (Y(.64) - by) * (1 - (1 - tt) ** 2) - h * .05 * math.sin(PI * tt) * 0
        arc.append((ax, ay))
    for i in range(0, 34, 3):
        seg = arc[i:i + 2]
        cv.obj([], 0)
        cv.heavy(seg)
    for s in (-1, 1):
        cv.line([(bx - br * 1.7, by + s * br * .55 + br * .4), (bx - br * 1.15, by + s * br * .45 + br * .2)])
    cv.line([(bx - br * 2.1, by + br * .2), (bx - br * 1.25, by)])
    ball(cv, bx, by, br, -.6)
    # Easter egg: Parker's drumsticks left crossed on the boards
    sx_, sy_ = X(.2), Y(.86)
    L = w * .16
    for sgn in (-1, 1):
        a = sgn * .35
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2 * .5
        p0, p1 = (sx_ - dx, sy_ - dy), (sx_ + dx, sy_ + dy)
        if sgn > 0:
            p0, p1 = p1, p0
        nx, ny = -math.sin(a) * 1.2, math.cos(a) * 1.2
        st = [(p0[0] + nx, p0[1] + ny), (p1[0] + nx * .5, p1[1] + ny * .5), (p1[0] - nx * .5, p1[1] - ny * .5), (p0[0] - nx, p0[1] - ny)]
        cv.obj([st], 1.)
        cv.hair([(p0[0] - nx * .4, p0[1] - ny * .4), (p1[0] - nx * .2, p1[1] - ny * .2)])
        cv.obj([_ell(p1[0], p1[1], 1.6, 1.3, 10)[:-1]], 1.)
    body = cv.svg()
    cid = C._uid("sc", x, y, w, h, seed)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g>')


# ----------------------------------------------------------------------------------------------
# lettering for the banner: a small engraved roman, drawn as strokes
# ----------------------------------------------------------------------------------------------

def _C_letter():
    return [[(.5 + .46 * math.cos(a), .5 + .5 * math.sin(a)) for a in [-.75 - (TAU - 1.5) * i / 20 for i in range(21)]]]


_GLYPH = {
    "R": [[(0, 1), (0, 0), (.62, 0), (.85, .1), (.88, .27), (.8, .43), (.6, .5), (0, .5)], [(.5, .5), (.95, 1)]],
    "I": [[(.5, 0), (.5, 1)]],
    "P": [[(0, 1), (0, 0), (.62, 0), (.85, .1), (.88, .27), (.8, .43), (.6, .52), (0, .52)]],
    "C": _C_letter(),
    "T": [[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]],
    "Y": [[(0, 0), (.5, .5), (1, 0)], [(.5, .5), (.5, 1)]],
}
_ADV = {"I": .55, " ": .8}


def _lettering(text, centre, H):
    """Strokes of text laid along centre (a polyline), letter height H, centred."""
    adv = [(_ADV.get(ch, 1.15)) * H * .78 for ch in text]
    total = sum(adv)
    cum = [0.]
    for i in range(1, len(centre)):
        cum.append(cum[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    L = cum[-1]

    def at(s):
        s = min(max(s, 0), L)
        for i in range(1, len(cum)):
            if cum[i] >= s:
                f = (s - cum[i - 1]) / ((cum[i] - cum[i - 1]) or 1)
                (ax, ay), (bx, by) = centre[i - 1], centre[i]
                tx, ty = bx - ax, by - ay
                tl = math.hypot(tx, ty) or 1
                return ax + tx * f, ay + ty * f, tx / tl, ty / tl
        return centre[-1][0], centre[-1][1], 1, 0

    out = []
    s = L / 2 - total / 2
    for ch, a in zip(text, adv):
        g = _GLYPH.get(ch)
        if g:
            gw = H * .62
            ox = s + (a - gw) / 2
            for stroke in g:
                pts = []
                for u, v in stroke:
                    px, py, tx, ty = at(ox + u * gw)
                    nx, ny = -ty, tx
                    off = (v - .5) * H
                    pts.append((px + nx * off, py + ny * off))
                out.append(pts)
        s += a
    return out, (L / 2 - total / 2, L / 2 + total / 2), at


def banner(cx, cy, w, h, seed):
    svg, centre = C.ribbon_banner(cx, cy, w, h, .04, seed)
    letters, (s0, s1), at = _lettering("RIP CITY", centre, h * .5)
    cv = C.Canvas()
    cv.obj([], 0)
    # face shading: contours along the ribbon, kept off the band that carries the letters
    R = C._Rib(centre, [h / 2] * len(centre), [h / 2] * len(centre))
    for s_ in (.62, -.62):
        cv.hair(R.contour(s_, 0., 1.))
    # beyond the lettering, the middle band gets fine ruled shading too
    tot = R.L
    for s_ in (.3, 0., -.3):
        cv.hair(R.contour(s_, 0., max(0., s0 - 6) / tot))
        cv.hair(R.contour(s_, min(1., (s1 + 6) / tot), 1.))
    # little lozenges flanking the words
    for s in (s0 - 3, s1 + 3):
        px, py, tx, ty = at(s)
        cv.obj([[(px - tx * 2.2, py - ty * 2.2), (px - ty * 1.6, py + tx * 1.6), (px + tx * 2.2, py + ty * 2.2), (px + ty * 1.6, py - tx * 1.6)]], 0)
        cv.heavy([(px - tx * 1.5, py - ty * 1.5), (px + tx * 1.5, py + ty * 1.5)])
    cv.line(letters)
    # thicken the main strokes (a second pass, offset half a pixel) for an engraved roman
    thick = []
    for st in letters:
        if len(st) == 2:
            thick.append([(p[0] + .45, p[1]) for p in st])
    cv.line(thick)
    return svg + cv.svg()


# ----------------------------------------------------------------------------------------------
# the pedestal tablet: chequered ribbons and the drumstick Easter egg
# ----------------------------------------------------------------------------------------------

def tablet(tx, ty, tw, th):
    cv = C.Canvas()
    cy = ty + th / 2
    rect = [(tx + 1, ty + 1), (tx + tw - 1, ty + 1), (tx + tw - 1, ty + th - 1), (tx + 1, ty + th - 1)]
    cv.obj([rect], 0)
    cv.hair(hp(rect, 0, 1.5, .25))
    br = th * .42
    # chequered flags streaming out to both ends, two rows of checks on a waving strip
    for s in (-1, 1):
        x0 = tx + tw / 2 + s * (br + 7)
        x1 = tx + tw / 2 + s * (tw / 2 - 5)
        n = int(abs(x1 - x0) / (th * .32))
        amp = th * .12
        half = th * .26
        cols = []
        for i in range(n + 1):
            f = i / n
            xx = x0 + (x1 - x0) * f
            yc = cy + amp * math.sin(f * TAU * 1.5)
            cols.append((xx, yc))
        strip = [(p[0], p[1] - half) for p in cols] + [(p[0], p[1] + half) for p in cols[::-1]]
        cv.obj([strip], 1.)
        for i in range(n):
            for row in (0, 1):
                if (i + row) % 2 == 0:
                    (ax, ay), (bx, by) = cols[i], cols[i + 1]
                    ya0 = ay - half + row * half
                    yb0 = by - half + row * half
                    q = [(ax, ya0), (bx, yb0), (bx, yb0 + half), (ax, ya0 + half)]
                    cv.line(hp(q, 90 if s > 0 else 90, 1, .5))
        # swallow tail end
        e = cols[-1]
        cv.obj([[(e[0], e[1] - half), (e[0] + s * 4, e[1] - half - 1), (e[0] + s * 2, e[1]), (e[0] + s * 4, e[1] + half + 1), (e[0], e[1] + half)]], 1.)
        cv.hair(hp([(e[0], e[1] - half), (e[0] + s * 4, e[1] - half - 1), (e[0] + s * 2, e[1]), (e[0] + s * 4, e[1] + half + 1), (e[0], e[1] + half)], 0, 1.5, .25))
    # Easter egg: crossed drumsticks behind the little ball
    mx = tx + tw / 2
    for s in (-1, 1):
        a = s * .5
        L = th * 1.15
        dx, dy = math.sin(a) * L / 2, math.cos(a) * L / 2
        p0, p1 = (mx - dx * 1.0 - s * 0, cy + dy), (mx + dx, cy - dy)
        nx, ny = math.cos(a) * .9, -math.sin(a) * .9
        stick = [(p0[0] + nx, p0[1] + ny), (p1[0] + nx * .5, p1[1] + ny * .5), (p1[0] - nx * .5, p1[1] - ny * .5), (p0[0] - nx, p0[1] - ny)]
        cv.obj([stick], 1.)
        cv.obj([_ell(p1[0], p1[1], 1.5, 1.5, 10)[:-1]], 1.)
    ball(cv, mx, cy, br, -.4, light=False)
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts (from the house library, with the vignette clipped to the whole field)
# ----------------------------------------------------------------------------------------------

def _cart_field(cw, ch):
    bw = max(5., min(cw, ch) * .07)
    return cw / 2 - bw * 1.6, ch / 2 - bw * 1.6


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
    # inside: a ball on a ruled ground, crossed drumsticks behind it
    field = _ell(cx, cy, rx - 3.5, ry - 3.5, 48)[:-1]
    cv = C.Canvas()
    cv.obj([field], 0)
    cv.hair(hp(field, 0, 1.5, .25))
    br = ry * .62
    for s in (-1, 1):
        a = s * .9
        L = br * 2.6
        dx, dy = math.sin(a) * L / 2, math.cos(a) * L / 2
        p0, p1 = (cx - dx, cy + dy), (cx + dx, cy - dy)
        nx, ny = math.cos(a) * 1.1, -math.sin(a) * 1.1
        cv.obj([[(p0[0] + nx, p0[1] + ny), (p1[0] + nx * .5, p1[1] + ny * .5), (p1[0] - nx * .5, p1[1] - ny * .5), (p0[0] - nx, p0[1] - ny)]], 1.)
        cv.obj([_ell(p1[0], p1[1], 1.8, 1.8, 10)[:-1]], 1.)
    ball(cv, cx, cy, br, -.5)
    o.append(cv.svg())
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
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
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_field(cw, ch)
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .04, 18.)
    px0, py0 = 4., top_free
    pw = w - 8
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # a light ruled ground under the crest, so the plate rises out of the page's own ruled field
    o.append(f'<path d="M0,0h{_n(w)}v{_n(py0)}h{_n(-w)}z" fill="{C.pat("D")}" stroke="none"/>')
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .50, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .145, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .04), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_field(cw, ch)
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 56), True, rng.randrange(1 << 20)))
    fcv = C.Canvas()
    ball(fcv, cx, cy - ch / 2 + 2, 10.5, -.3)
    o.append(fcv.svg())
    o.append(banner(cx, cy + ch * .47, cw * 1.35, min(22, ph * .06), rng.randrange(1 << 20)))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    # ground behind the pedestal and frieze so no paper shows round the plinth
    o.append(C.dark_ground((0, py + 4, w, h - py - 4), "G"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(tablet(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
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
