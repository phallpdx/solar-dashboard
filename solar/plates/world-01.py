"""world-01 "Over in Bangkok": a cloudy monsoon morning over Wat Arun on the Chao Phraya.

The vignette (every size): the great prang of Wat Arun and its satellites on the far bank under
billowing, rain-heavy cumulus (51% rain), the river ruled in broken lines with the prang's
reflection, and a floating-market sampan whose vendor in a ngob hat serves a bowl of noodles
("a-roi", delicious, the page's phrase). Easter egg: the chopsticks crossed over the bowl are a pair
of drumsticks with bead tips.
Frame: house Codex acanthus (engraving_codex); the tall plate's pedestal tablet is cut in niello
with interlocking Thai kranok flames, and the ribbon carries "AROI" in engraved capitals.
"""
import sys
import math
import random
import engraving_codex as C
import engraving_thai as T

_n = C._n


# ----------------------------------------------------------------------------------- helpers
def _scan(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    xs.sort()
    return [(xs[j], xs[j + 1]) for j in range(0, len(xs) - 1, 2)]


def _cut(segs, holes):
    """Subtract x-intervals (holes) from segments."""
    for a, b in holes:
        out = []
        for s0, s1 in segs:
            if b <= s0 or a >= s1:
                out.append((s0, s1))
            else:
                if a > s0:
                    out.append((s0, a))
                if b < s1:
                    out.append((b, s1))
        segs = out
    return [(a, b) for a, b in segs if b - a > .8]


def _black(cv, poly):
    """A solid black mass from 1 px rules .8 apart."""
    cv.line(C.hatch_poly(poly, 0, .8))


def _arc(cx, cy, rx, ry, a0, a1, n=16):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


# ----------------------------------------------------------------------------------- clouds
def _cloud_spec(rng, cx, base, cw, ch):
    """Cumulus heap: a row of billows along the base, a second row riding on the middle ones, and
    small top curls; listed back (top) to front (bottom)."""
    k = max(3, int(cw / (ch * .55)))
    row = []
    for i in range(k):
        t = (i + .5) / k
        r = ch * (.3 + .32 * math.sin(math.pi * t) ** 1.2) * rng.uniform(.85, 1.08)
        row.append((cx - cw / 2 + cw * t + rng.uniform(-1.5, 1.5), base - r * .55, r))
    upper = []
    for lx, ly, r in row[1:-1]:
        r2 = r * rng.uniform(.62, .8)
        upper.append((lx + rng.uniform(-.3, .3) * r, ly - r * .78, r2))
    top = []
    for lx, ly, r in upper[len(upper) // 3: max(len(upper) // 3 + 1, 2 * len(upper) // 3)]:
        top.append((lx + rng.uniform(-.2, .2) * r, ly - r * .7, r * .62))
    return top + upper + row


def _cloud(cv, lobes, base, big):
    """Each billow is its own carved object, so the nearer ones cut the lines of those behind; each
    is shaded with arcs following its rim, dense in the shadow at lower right and thinning out
    toward the lit upper left; a flat, ruled base shadow closes the heap."""
    for lx, ly, r in lobes:
        circ = [(px, min(py, base)) for px, py in C._ell_pts(lx, ly, r, r, max(14, int(r * 2)))[:-1]]
        cv.obj([circ], 1. if (big and r > 9) else .5)
        k = 1
        while True:
            rr = r - k * 1.5
            span = math.radians(115 - k * 16)
            if rr < 1.5 or span <= .2:
                break
            arc = [p for p in _arc(lx, ly, rr, rr, math.radians(55) - span, math.radians(55) + span,
                                   max(6, int(rr * span))) if p[1] < base - .5]
            if len(arc) > 1:
                cv.hair(arc)
            k += 1
        # a light open ruling across the shadowed lower half (grey monsoon cloud)
        y = ly - r * .7
        while y < min(base, ly + r):
            for a, b in _scan(circ, y):
                cv.hair([(a + (b - a) * (.5 if y < ly - r * .2 else .18), y), (b, y)])
            y += 3.
    x0 = min(lx - r for lx, ly, r in lobes[-max(1, len(lobes) // 2):]) + 2
    x1 = max(lx + r for lx, ly, r in lobes[-max(1, len(lobes) // 2):]) - 2
    bh = max(2., min(r for _, _, r in lobes) * .45)
    band = [(x0, base - bh * .3), (x0 + bh * 2, base - bh), (x1 - bh * 2, base - bh), (x1, base - bh * .3),
            (x1 - bh, base + .8), (x0 + bh, base + .8)]
    cv.obj([band], 0)
    cv.hair(C.hatch_poly(band, 0, 1.5))
    cv.hair([(x0 + bh, base + .8), (x1 - bh, base + .8)])


# ----------------------------------------------------------------------------------- prang
def _prang(cv, cx, by, H):
    """Khmer prang of Wat Arun, base centre (cx, by), H px tall. Light from the left."""
    s = H / 52.

    def P(x, y):
        return (cx + x * s, by + y * s)
    terr = ((16, -4, 0), (13.4, -8, -4), (11, -12, -8), (9, -15.5, -12))
    if s > 1.5:
        terr = ((16, -3, 0), (14.6, -5.6, -3), (13, -8.2, -5.6), (11.6, -10.8, -8.2), (10.2, -13.2, -10.8), (8.8, -15.5, -13.2))
    for j, (hw, y0, y1) in enumerate(terr):
        poly = [P(-hw, y1), P(-hw + .8, y0), P(hw - .8, y0), P(hw, y1)]
        cv.obj([poly], 1. if s > 1.4 else .5)
        cv.hair(C.hatch_poly([P(hw * .3, y1), P(hw * .3, y0), P(hw - .8, y0), P(hw, y1)], 90, 1.5))
        cv.hair([P(-hw + .8, y0 + 1), P(hw - .8, y0 + 1)])
        if s * 4 > 6:   # balusters
            k = -hw + 1.4
            while k < hw * .3:
                cv.hair([P(k, y0 + 1), P(k, y1 - .4)])
                k += 3 / s
        if j < len(terr) - 1:
            _black(cv, [P(-1.4, y1), P(-1.4, y0 + 1), P(1.4, y0 + 1), P(1.4, y1)])
    y_f, y_n = -15.5, -42.

    def hw(y):
        t = (y_f - y) / (y_f - y_n)
        return 1.3 + 6.4 * math.cos(t * math.pi / 2) ** .75 + 1.2 * math.sin(t * math.pi) * (1 - t)
    ys = [y_f + (y_n - y_f) * i / 24 for i in range(25)]
    body = [P(-hw(y), y) for y in ys] + [P(hw(y), y) for y in ys[::-1]]
    cv.obj([body], 1.)
    nt = 8 if s < 1.6 else 11
    for i in range(nt):
        ya = y_f + (y_n - y_f) * i / nt
        yb = y_f + (y_n - y_f) * (i + 1) / nt
        wa = hw(ya)
        cv.line([P(wa * q / 6, ya - .35 * (1 - (q / 6) ** 2)) for q in range(-6, 7)])
        ym = (ya + yb) / 2
        wm = hw(ym)
        x = -wm * .55
        while x < wm:
            f = (x / wm + 1) / 2
            cv.hair([P(x, ya - .25), P(x, yb + .25)])
            x += (3. if f < .55 else (2. if f < .8 else 1.5)) / s
        if i < nt - 1 and i % 2 == 1:
            nw = max(.6, wm * .18)
            _black(cv, [P(-nw, yb + .3), P(-nw, ym), P(0, ym - (yb - ya) * .45 - .4), P(nw, ym), P(nw, yb + .3)])
    bulb = [P(-1.9, -42), P(-2.3, -43.6), P(-1.2, -45.2), P(0, -45.9), P(1.2, -45.2), P(2.3, -43.6), P(1.9, -42)]
    cv.obj([bulb], .5)
    _black(cv, bulb)
    cv.line([P(0, -45.8), P(0, -51.5)])
    cv.hair([P(-1.4, -49.6), P(-1.2, -48.2), P(0, -47.8), P(1.2, -48.2), P(1.4, -49.6)])
    cv.hair([P(-1.1, -46.6), P(1.1, -46.6)])


# ----------------------------------------------------------------------------------- bank, palms
def _palm(cv, x, y, h, lean, rng):
    top = (x + lean * h * .3, y - h)
    cv.line([(x + lean * h * .3 * (i / 8) ** 1.6, y - h * i / 8) for i in range(9)])
    for k in range(7):
        a = math.radians(-170 + k * 27 + rng.uniform(-6, 6))
        L = h * rng.uniform(.32, .45)
        pts = [(top[0] + math.cos(a) * L * i / 6, top[1] + math.sin(a) * L * i / 6 + L * .55 * (i / 6) ** 2)
               for i in range(7)]
        cv.line(pts)
        for i in range(2, 6):
            px, py = pts[i]
            cv.hair([(px, py), (px + math.cos(a + 1.2) * 1.6, py + 2.2)])


def _bank(cv, x, w, hz, hb, rng, cx, gap):
    pts = [(x - 2, hz + .5)]
    xx = x - 2
    while xx < x + w + 2:
        pts.append((xx, hz - hb * (.55 + .45 * abs(math.sin(xx * .09 + 1.3))) * rng.uniform(.85, 1.)))
        xx += 3
    pts.append((x + w + 2, hz + .5))
    cv.obj([pts], .5)
    cv.hair(C.hatch_poly(pts, 45, 2))
    cv.hair(C.hatch_poly(pts, -45, 2))
    wy = hz - max(3., hb * .55)
    wall = [(cx - gap, hz + .3), (cx - gap, wy), (cx + gap, wy), (cx + gap, hz + .3)]
    cv.obj([wall], .5)
    cv.hair([(cx - gap, wy + 1.2), (cx + gap, wy + 1.2)])
    k = cx - gap + 1.5
    while k < cx + gap:
        cv.hair([(k, wy + 1.8), (k, hz)])
        k += 3
    for px in (x + w * .06, x + w * .16, x + w * .86, x + w * .95):
        _palm(cv, px, hz - 1, hb * rng.uniform(2.2, 2.9), rng.choice((-1, 1)) * .5, rng)


# ----------------------------------------------------------------------------------- boat
def _sampan(cv, bx, by, L, rng, egg=True):
    """Floating-market sampan heading left, vendor in a ngob hat at the stern, a basket of mangoes
    and a pot amidships, a steaming bowl at the prow with crossed drumsticks over it (the egg)."""
    s = L / 60.

    def P(x, y):
        return (bx + x * s, by + y * s)
    hull = [P(-30, -7), P(-27, -3), P(-22, 0), P(-10, 1.6), P(12, 1.6), P(24, 0), P(29, -3), P(31, -6.5),
            P(26, -4.4), P(12, -3.6), P(-12, -3.6), P(-24, -4)]
    for i in range(4):
        cv.hair([P(30 + i * 3, 1.5 + i * 1.6), P(46 + i * 7, .5 + i * 2.4)])
        cv.hair([P(-30 - i * 2, -2 + i * 1.8), P(-38 - i * 6, -1 + i * 2.6)])
    vx = 18
    body = [P(vx - 4.5, -3.6), P(vx - 3.8, -10), P(vx - 1, -13), P(vx + 2, -13), P(vx + 4.2, -10), P(vx + 5, -3.6)]
    cv.obj([body], .5)
    cv.hair(C.hatch_poly(body, 70, 1.5))
    cv.hair(C.hatch_poly(body, -20, 2))
    head = C._ell_pts(bx + (vx + .5) * s, by - 14.6 * s, 1.9 * s, 1.9 * s, 12)[:-1]
    cv.obj([head], .5)
    cv.hair(C.hatch_poly(head, 90, 1.5))
    hat = [P(vx - 8, -15.2), P(vx + .5, -20.5), P(vx + 9, -15.2), P(vx + .5, -14.4)]
    cv.obj([hat], 1.)
    for q in range(-7, 9, 2):
        cv.hair([P(vx + .5, -20.2), P(vx + .5 + q, -15)])
    cv.hair(C.hatch_poly([P(vx + .5, -20.5), P(vx + 9, -15.2), P(vx + .5, -14.4)], 0, 1.5))
    cv.line([P(vx - 3, -9), P(vx + 13, 8)])
    blade = [P(vx + 11, 5.6), P(vx + 15.5, 10.4), P(vx + 14.2, 11.8), P(vx + 9.6, 7.2)]
    cv.obj([blade], .5)
    _black(cv, blade)
    for mx, my in ((-3, -8.6), (3, -8.6), (0, -10), (-1.6, -11.4), (1.6, -11.4)):
        m = C._ell_pts(bx + mx * s, by + my * s, 1.8 * s, 1.3 * s, 10)[:-1]
        cv.obj([m], .5)
        cv.hair(C.hatch_poly(m, 30, 1.5)[-2:])
    bk = [P(-4.5, -3.6), P(-5.5, -8), P(5.5, -8), P(4.5, -3.6)]
    cv.obj([bk], .5)
    cv.hair(C.hatch_poly(bk, 60, 1.5))
    cv.hair(C.hatch_poly(bk, -60, 3))
    pot = C._ell_pts(bx + 9 * s, by - 6 * s, 2.6 * s, 2.6 * s, 14)[:-1]
    cv.obj([pot], .5)
    cv.hair(C.hatch_poly(pot, 0, 1.5))
    bwx = -15
    for q in (-1.5, 1.5):     # steam
        cv.hair([P(bwx + q + .8 * math.sin(k * 1.4), -7.4 - k * 1.3) for k in range(6)])
    if egg:
        for sgn in (-1, 1):
            a, b = P(bwx - 4.5 * sgn, -13.5), P(bwx + 2.5 * sgn, -5)
            cv.line([a, b])
            tip = C._ell_pts(a[0], a[1], max(.9, .7 * s), max(.9, .7 * s), 8)[:-1]
            cv.obj([tip], 0)
            _black(cv, tip)
    bowl = [P(bwx - 4.5, -6), P(bwx - 3, -3.8), P(bwx + 3, -3.8), P(bwx + 4.5, -6)]
    cv.obj([bowl], .5)
    cv.hair(C.hatch_poly(bowl, 0, 1.5)[1:])
    cv.obj([hull], 1.)
    _black(cv, [P(-27, -3), P(-22, 0), P(-10, 1.6), P(12, 1.6), P(24, 0), P(29, -3), P(26, -1.2), P(12, -1.4),
                P(-12, -1.4), P(-24, -1.6)])
    cv.hair(C.hatch_poly([P(-24, -4), P(-12, -3.6), P(12, -3.6), P(26, -4.4), P(29, -3), P(26, -1.2), P(12, -1.4),
                          P(-12, -1.4), P(-24, -1.6)], 0, 1.5))
    cv.line([P(-29, -6.4), P(-24, -3.9), P(-12, -3.4), P(12, -3.4), P(26, -4.2), P(31, -6.4)])


# ----------------------------------------------------------------------------------- the scene
def scene(x, y, w, h, seed=0, egg=True):
    """Wat Arun under monsoon cloud, filling x..x+w, y..y+h completely (clip it to its field)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    hz = y + h * (.66 if h < w * .9 else .6)
    cx = x + w / 2
    Hm = min((hz - y) * .93, w * .55 / .62)
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, hz + 1), (x - 2, hz + 1)]
    specs = []
    sky_h = hz - y
    far_base = hz - sky_h * .12
    xx = x - 6
    while xx < x + w + 6:
        cw = rng.uniform(.18, .26) * w
        specs.append((xx + cw / 2, far_base, cw, sky_h * .14, False))
        xx += cw * .8
    for side in (-1, 1):
        cw = w * rng.uniform(.34, .4)
        specs.append((cx + side * (w * .32 + rng.uniform(-4, 4)), y + sky_h * rng.uniform(.5, .58), cw, sky_h * .3, True))
    for side in (-1, 1):
        cw = w * rng.uniform(.3, .36)
        specs.append((cx + side * w * .14 + rng.uniform(-6, 6), y + sky_h * .16, cw, sky_h * .22, True))
    clouds = [(c, _cloud_spec(rng, *c[:4])) for c in specs]
    cv.obj([sky], 0)
    yy = y - 1
    while yy < hz:
        cv.hair([(x - 2, yy), (x + w + 2, yy)])
        yy += 2. if (yy - y) < sky_h * .62 else 3.
    for (ccx, base, cw, ch, big), lobes in clouds:
        if big and base > y + sky_h * .4:
            x0 = ccx - cw * .32
            while x0 < ccx + cw * .3:
                yy = base + rng.uniform(0, 3)
                while yy < hz:
                    ln = rng.uniform(3, 7)
                    cv.hair([(x0 + (yy - base) * .22, yy), (x0 + (min(hz, yy + ln) - base) * .22, min(hz, yy + ln))])
                    yy += ln + rng.uniform(2, 4)
                x0 += 3.
    for c, lobes in sorted(clouds, key=lambda t: (t[0][4], -t[0][1])):
        _cloud(cv, lobes, c[1], c[4])
    _bank(cv, x, w, hz, max(3., sky_h * .09), rng, cx, Hm * .5)
    for side in (-1, 1):
        _prang(cv, cx + side * Hm * .52, hz - .5, Hm * .5)
    if w > Hm * 2.4:
        for side in (-1, 1):
            _prang(cv, cx + side * Hm * 1.0, hz, Hm * .36)
    _prang(cv, cx, hz, Hm)
    water = [(x - 2, hz), (x + w + 2, hz), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([water], 1.)
    yy = hz + 1.5
    while yy < y + h + 2:
        t = (yy - hz) / max(1., y + h - hz)
        rw = Hm * .3 * (1 - t * .8)
        xx = x - 2 + rng.uniform(0, 3)
        while xx < x + w + 2:
            ln = rng.uniform(5, 18) * (1 + t)
            e = min(x + w + 2, xx + ln)
            if abs((xx + e) / 2 - cx) < rw:
                cv.line([(xx, yy), (e, yy)])
            else:
                cv.hair([(xx, yy), (e, yy)])
            xx = e + rng.uniform(1.2, 3.)
        yy += 3. if t < .3 else (2. if t < .7 else 1.5)
    L = min(w * .36, (y + h - hz) * 2.6)
    _sampan(cv, x + w * .27, hz + (y + h - hz) * .62, L, rng, egg)
    return cv.svg()


# ----------------------------------------------------------------------------------- lettering
_GLYPH = {   # single-stroke capitals in a 0..1 box (y down)
    "A": [[(0, 1), (.5, 0), (1, 1)], [(.22, .62), (.78, .62)]],
    "R": [[(0, 1), (0, 0), (.62, 0), (.85, .1), (.85, .4), (.62, .5), (0, .5)], [(.5, .5), (.95, 1)]],
    "O": [[(.5, 0), (.85, .12), (1, .5), (.85, .88), (.5, 1), (.15, .88), (0, .5), (.15, .12), (.5, 0)]],
    "I": [[(.5, 0), (.5, 1)], [(.25, 0), (.75, 0)], [(.25, 1), (.75, 1)]],
}


def _letters(text, cx, cy, ht, gap=.45):
    ws = [.7 if c == "I" else 1. for c in text]
    tot = sum(ws) * ht * .72 + gap * ht * (len(text) - 1)
    x = cx - tot / 2
    d = ""
    for c, wf in zip(text, ws):
        gw = wf * ht * .72
        for stroke in _GLYPH[c]:
            d += C._d([(x + px * gw, cy - ht / 2 + py * ht) for px, py in stroke], tol=0)
        x += gw + gap * ht
    return d


# ----------------------------------------------------------------------------------- niello tablet
def _kranok_tablet(tx, ty, tw, th):
    o = [f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-tw + 2)}z" fill="#000"/>']
    k = (th - 3) / 14.
    U = 23 * k
    n = int((tw - 4) / U)
    x0 = tx + (tw - n * U) / 2
    top, bot = ty + 1.8, ty + th - 1.8
    for i in range(n):
        u = x0 + i * U
        if i < n / 2:
            o.append(T._kranok(T._mat(u + 1, bot, 0, k, k), lw=.5) + T._kranok(T._mat(u + 1 + 20.5 * k, top, 0, -k, -k), lw=.5))
        else:
            o.append(T._kranok(T._mat(u + U - 1, bot, 0, -k, k), lw=.5) + T._kranok(T._mat(u + U - 1 - 20.5 * k, top, 0, k, -k), lw=.5))
    return "".join(o)


# ----------------------------------------------------------------------------------- kranok crest
def _kranok_crest(cx, cy, size, up=True):
    """A Thai crest growing from the cartouche: a pair of kranok flames curling outward from a
    lozenge bud, and a tall centre flame (kranok plew), white with engraved son lines."""
    k = size / 20.
    sd = -1 if up else 1
    o = ""
    for side in (-1, 1):
        o += T._kranok(T._mat(cx + side * 1.5 * k, cy, 0, side * k, -sd * k), "#fff", 1, lw=.5)
    # centre flame: a tall teardrop with a flicked tip
    fl = [(cx, cy - sd * size * 1.05)]
    pts = []
    for i in range(13):
        t = i / 12
        wdt = size * .22 * math.sin(math.pi * t) ** .8 * (1 - .4 * t)
        pts.append((cx + wdt, cy + sd * (- size * 1.05 * t)))
    poly = [(cx, cy)] + pts + [(cx - (px - cx), py) for px, py in pts[::-1]]
    o += f'<path d="{C._d(poly, True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>'
    inner = [(cx + (px - cx) * .45, cy + (py - cy) * .9) for px, py in pts]
    o += f'<path d="{C._d([(cx, cy - sd * 2)] + inner[2:], tol=0)}{C._d([(cx, cy - sd * 2)] + [(cx - (px - cx), py) for px, py in inner[2:]], tol=0)}" fill="none" stroke="#000" stroke-width=".5"/>'
    bud = C._ell_pts(cx, cy, size * .2, size * .14, 16)[:-1]
    o += f'<path d="{C._d(bud, True, 0)}" fill="#000" stroke="#000" stroke-width=".5"/>'
    o += f'<path d="{C._d(C._ell_pts(cx, cy, size * .07, size * .05, 10)[:-1], True, 0)}" fill="#fff"/>'
    return o


# ----------------------------------------------------------------------------------- layouts
def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    rx = min(w * .2, gh * 2.1)
    o.append(C._clip(C._uid("wb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, rx * 2.15, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    ry = gh / 2 - .5
    o.append(C._medallion(cx, cy, rx, ry))
    fd = C._d(C._ell_pts(cx, cy, rx - 3.5, ry - 3.5, 64), True)
    o.append(_field_clip(C._uid("wbf", w, h, seed), fd, scene(cx - rx, cy - ry, rx * 2, ry * 2, seed)))
    o.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _medium(w, h, seed):
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
    o.append(C._clip(C._uid("wm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    o.append(c)
    o.append(_field_clip(C._uid("wmf", w, h, seed), fd, scene(cx - a, cy - b, 2 * a, 2 * b, seed)))
    ks = min(18., gh * .12)
    o.append(_kranok_crest(cx, cy - b - bw * .2, ks, True))
    o.append(_kranok_crest(cx, cy + b + bw * .2, ks * .85, False))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed):
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
    cw, ch = pw * .5, ph * .62
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
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("wt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(c)
    o.append(_field_clip(C._uid("wtf", w, h, seed), fd, scene(cx - a, cy - b, 2 * a, 2 * b, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.3, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    mid = centre[len(centre) // 2]
    lh = bh * .6
    o.append(f'<path d="{_letters("AROI", mid[0], mid[1] + lh * .06, lh, .6)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    # the low-tone grave over the O (a-ROI): a short falling stroke
    gx = mid[0] + lh * (.72 * .5 + .6 * .5 + .36) - lh * .1
    o.append(f'<path d="M{_n(gx - lh * .22)},{_n(mid[1] - lh * .95)}l{_n(lh * .3)},{_n(lh * .22)}" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_kranok_tablet(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("wf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
