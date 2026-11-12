"""civics-02 "Election coming up": an engraved Oregon vote-by-mail plate.

Subject (from the page): the next special district election (school boards, local measures), the
ballots that go out by mail, the countdown in days, the Oregon primary and general to follow.
  short  : a carved scroll frieze round a medallion holding a sealed ballot envelope.
  medium : a cartouche between big volutes; in it an Oregon ballot drop box takes a ballot under
           Mt. Hood, fields ruled in perspective, a heron crossing the sky.
  tall   : the Oregon State Capitol (fluted drum, Golden Pioneer) with Mt. Hood behind and the drop
           box in the foreground, in a scroll frame; a ribbon banner carries the election date and
           the pedestal tablet carries today's countdown ("188 DAYS"), all lettered as paths.
Easter egg: the X on the ballot is a pair of crossed drumsticks (ball tips), and a Sauvie Island
heron flies over the valley.
"""
import sys
import math
import random
import re
import engraving_codex as C

_n, _d = C._n, C._d
PI = math.pi

# ------------------------------------------------------------------------------------------------
# stroke lettering (paths only), grid 4 wide x 6 tall, y down
# ------------------------------------------------------------------------------------------------
_G = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.3), (2.3, 3.3)]],
    "I": [[(0, 0), (0, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2.5, 4), (5, 0), (5, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "W": [[(0, 0), (1.2, 6), (2.5, 2.4), (3.8, 6), (5, 0)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.5)], [(1.3, 2.7), (4, 6)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "1": [[(1, 1), (2.3, 0), (2.3, 6)], [(1, 6), (3.6, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1.5, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "5": [[(4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]],
    "6": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "7": [[(0, 0), (4, 0), (1.5, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6),
           (4, 5), (4, 4), (3, 3)]],
    "9": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (4, 3)]],
    "*": [[(1.5, 2.5), (2.5, 3.5)], [(2.5, 2.5), (1.5, 3.5)]],
}


def _gw(ch):
    if ch == " ":
        return 2.6
    if ch == "*":
        return 4.
    return max(p[0] for s in _G.get(ch, [[(0, 0), (4, 0)]]) for p in s)


def text_width(s, size):
    k = size / 6.
    return sum((_gw(c) + 2.) * k for c in s) - 2. * k


def letter_lines(s, x, y, size, along=None):
    """Polylines for string s, cap height `size`, left/top at (x, y). If along is a function
    t(px) -> (X, Y, angle) mapping a horizontal offset to a point on a curve, letters follow it."""
    k = size / 6.
    out = []
    cx = 0.
    for ch in s:
        g = _G.get(ch, [])
        gw = _gw(ch)
        for stroke in g:
            pl = []
            for gx, gy in stroke:
                lx, ly = cx + gx * k, gy * k - size / 2
                if along:
                    mid = cx + gw * k / 2
                    X, Y, a = along(mid)
                    dx = lx - mid
                    pl.append((X + dx * math.cos(a) - ly * math.sin(a), Y + dx * math.sin(a) + ly * math.cos(a)))
                else:
                    pl.append((x + lx, y + ly + size / 2))
            out.append(pl)
        cx += (gw + 2.) * k
    return out


def _polyd(pls, tol=0):
    return "".join(_d(p, tol=tol) for p in pls if len(p) > 1)


# ------------------------------------------------------------------------------------------------
# page facts (read the day's text)
# ------------------------------------------------------------------------------------------------

def _facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    m = re.search(r"(\d{1,4})\s+days", s)
    days = m.group(1) if m else ""
    m = re.search(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*,\s+([A-Z][a-z]{2})\w*\s+(\d{1,2})", s)
    date = (m.group(2).upper() + " " + m.group(3)) if m else ""
    return days, date


# ------------------------------------------------------------------------------------------------
# small geometry
# ------------------------------------------------------------------------------------------------

def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _ell(cx, cy, rx, ry, n=28, a0=0., a1=2 * PI):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + (0 if a1 - a0 >= 2 * PI - 1e-6 else 1))]


def _H(cv, poly, ang, pitch, phase=0., inset=0., w=.5):
    ls = C.hatch_poly(poly, ang, pitch, phase, inset)
    (cv.hair if w == .5 else cv.line if w == 1 else cv.heavy)(ls)


def _solid(cv, poly):
    """A black mass made of 1 px lines 0.8 apart."""
    cv.line(C.hatch_poly(poly, 0, .8, .4))


# ------------------------------------------------------------------------------------------------
# the scene pieces (all draw into a Canvas, painter's order)
# ------------------------------------------------------------------------------------------------

def _sky(cv, X, Y, W, H, hy):
    cv.obj([_rect(X - 2, Y - 2, W + 4, hy - Y + 4)], 0)
    # engraved sky: open rules above, closing toward the horizon, a few cloud banks left blank
    _H(cv, _rect(X - 2, Y - 2, W + 4, (hy - Y) * .45 + 2), 0, 3, .5)
    _H(cv, _rect(X - 2, Y + (hy - Y) * .45, W + 4, (hy - Y) * .55 + 2), 0, 2, .5)


def _clouds(cv, X, Y, W, H, hy, rng):
    for k in range(2):
        cx = X + W * (.14 + .72 * k) + rng.uniform(-4, 4)
        cy = Y + (hy - Y) * (.3 + .1 * k)
        rw = W * (.12 - .02 * k)
        rh = rw * .42
        pts = [(cx + rw, cy)]
        ph = rng.uniform(0, 1)
        for i in range(61):
            u = i / 60
            x = cx + rw - 2 * rw * u
            sc = abs(math.sin(PI * (3.5 * u + ph))) ** .5
            pts.append((x, cy - rh * math.sin(PI * u) ** .7 * (.62 + .38 * sc)))
        pts.append((cx - rw, cy))
        cv.obj([pts], .5)
        belly = [(cx - rw, cy), (cx + rw, cy), (cx + rw * .8, cy - rh * .35), (cx - rw * .8, cy - rh * .35)]
        _H(cv, belly, 0, 1.5)
        _H(cv, [(x, y) for x, y in pts], 0, 3, 1.)


def _heron(cv, x, y, s, flip=False):
    """A great blue heron in flight, Sauvie Island style: neck folded back, dagger bill, legs
    trailing straight out behind, broad arched wings on the up-stroke."""
    f = -1 if flip else 1
    P = lambda a, b: (x + f * a * s, y + b * s)
    wing = [P(-1.2, -.3), P(-.2, -2.2), P(1.2, -3.4), P(3.2, -3.9), P(5.2, -3.4), P(4.2, -2.6), P(2.8, -2.2),
            P(1.6, -1.2), P(1.4, -.4)]
    cv.obj([wing], .5)
    _H(cv, wing, 0, 1.5)
    cv.hair([P(.2, -1.6), P(1.6, -2.9), P(3.4, -3.4)])
    body = [P(-2.4, -.4), P(-.8, -1.), P(1.8, -.8), P(3.2, -.2), P(1.8, .5), P(-1.2, .5)]
    cv.obj([body], .5)
    _solid(cv, body)
    cv.heavy([P(-2.2, -.5), P(-3.3, -1.1), P(-2.9, -1.9), P(-3.6, -2.)])
    head = _ell(*P(-3.8, -2.0), .55 * s, .45 * s, 8)
    cv.obj([head], .5)
    _solid(cv, head)
    cv.line([P(-4.2, -2.0), P(-6.2, -1.8)])
    cv.line([P(3.1, -.2), P(7.2, .3)])
    cv.hair([P(3.0, .1), P(7.0, .8)])


def _hood(cv, mx, base, half, top, seed, light_left=False):
    """Mt. Hood: a steep snow cone with a lopsided summit, dark rock ribs and glaciers radiating
    down, its shaded flank hatched along the slope, and dark forested foothills below the snowline."""
    rng = random.Random(seed)
    Hh = base - top

    def wid(y, side):
        t = min(1., max(0., (y - top) / Hh))
        k = 1.0 if side > 0 else 1.12
        return half * k * (.72 * t ** .85 + .28 * t ** 2.5) + 2.6

    ys = [top + Hh * (i / 30) ** 1.2 for i in range(31)]
    right = [(mx + wid(y, 1) + (.6 * math.sin(i * 1.7) if i > 3 else 0), y) for i, y in enumerate(ys)]
    left = [(mx - wid(y, -1) - (.6 * math.sin(i * 2.3) if i > 3 else 0), y) for i, y in enumerate(ys)]
    summit = [(mx - 2.4, top + 1.5), (mx - .8, top), (mx + .8, top + .4), (mx + 2.6, top + 1.4)]
    poly = summit + right[1:] + left[1:][::-1]
    cv.obj([poly], 1.)
    # snowline, ragged, lower on the gullies
    sy = top + Hh * .58
    nz = 18
    zig = []
    for i in range(nz + 1):
        u = i / nz
        x = mx - wid(sy, -1) + (wid(sy, -1) + wid(sy, 1)) * u
        yj = sy + (Hh * .1 * (1 if i % 2 else -.35)) * (.6 + .4 * rng.random())
        zig.append((x, yj))
    zig[0] = (mx - wid(sy, -1), sy)
    zig[-1] = (mx + wid(sy, 1), sy)
    rk = [p for p in right if p[1] > sy]
    lk = [p for p in left if p[1] > sy]
    low = zig + rk + lk[::-1]
    _H(cv, low, 0, 1.5)
    _H(cv, low, 75, 3)
    # shadow flank (east): hatch along the fall line, two densities
    sgn = -1 if light_left else 1
    ridge = [(mx + .8 + sgn * (Hh * .1) * t ** 1.3 + 1.2 * math.sin(t * 11), top + .4 + (sy - top + 2) * t)
             for t in [i / 14 for i in range(15)]]
    edge = right if not light_left else left
    flank = ridge + [p for p in edge if top + 1 < p[1] <= sy + 2][::-1]
    _H(cv, flank, 90 + sgn * 22, 2)
    _H(cv, flank, 90 - sgn * 50, 3)
    cv.heavy(ridge[:10])
    # rock ribs on the lit face: wedges from near the summit down into the snow
    for k in range(6):
        f = (k + .7) / 6.5
        x0 = mx - sgn * (1.5 + f * 2.5)
        y0 = top + 2 + Hh * .05 * k
        L = (sy - y0) * (.55 + .4 * rng.random())
        dx = -sgn * wid(y0 + L, -sgn) * f * .9
        tip = (x0 + dx, y0 + L)
        w0 = .9 + .5 * rng.random()
        wedge = [(x0, y0), (x0 + dx * .5 + w0, y0 + L * .5), tip, (x0 + dx * .5 - w0 * .3, y0 + L * .5)]
        cv.obj([wedge], 0)
        cv.line([(x0, y0), (x0 + dx * .5, y0 + L * .5), tip])
        cv.hair([(x0 + 1.5 * -sgn, y0 + 3), (x0 + dx * .55 + 1.6 * -sgn, y0 + L * .55)])
    # crevasse ticks
    for k in range(10):
        y = top + Hh * (.12 + .32 * rng.random())
        x = mx - sgn * wid(y, -sgn) * rng.uniform(.2, .85)
        cv.hair([(x - 1.5, y), (x + 1.5, y + .4)])


def _trees(cv, x0, x1, y, h, rng, dark=True):
    """A treeline of firs along y: a black-shadowed band of zig-zag crowns."""
    pts = [(x0, y + h)]
    x = x0
    while x < x1:
        tw = rng.uniform(2.4, 4.)
        th = h * rng.uniform(.6, 1.)
        pts += [(x, y + h * .5), (x + tw / 2, y + h - th), (x + tw, y + h * .5)]
        x += tw * .8
    pts.append((x1, y + h))
    cv.obj([pts], .5)
    _H(cv, pts, 0, 1.5 if dark else 2)
    _H(cv, pts, 90, 2)


def _fields(cv, X, Y, W, H, hy, vx):
    """Willamette valley floor: sectors ruled to a vanishing point, alternately ploughed (furrows
    to the vanishing point) and in grass (rows closing toward the horizon), a winding river."""
    g = [(X - 2, hy), (X + W + 2, hy), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([g], 0)
    bot = Y + H + 2
    bounds = [X - W * 2.2, X - W * .6, X + W * .1, vx - W * .06, vx + W * .2, X + W * .78, X + W * 1.5, X + W * 3]
    rows = []
    yy, step = hy + 1.5, 2.
    while yy < bot:
        rows.append(yy)
        step *= 1.15
        yy += max(2., min(step, 3.))
    for i in range(len(bounds) - 1):
        b0, b1 = bounds[i], bounds[i + 1]
        sec = [(vx + (b0 - vx) * .02, hy), (vx + (b1 - vx) * .02, hy), (b1, bot), (b0, bot)]
        if i % 2:
            # ploughed: furrows to the vanishing point, about 3 px apart at the front
            n = max(2, int(abs(b1 - b0) / 3.))
            cv.hair([[(vx + (b0 + (b1 - b0) * j / n - vx) * .02, hy + .5), (b0 + (b1 - b0) * j / n, bot)] for j in range(n + 1)])
        else:
            ls = []
            for ry in rows:
                t = (ry - hy) / (bot - hy)
                xa, xb = vx + (b0 - vx) * t, vx + (b1 - vx) * t
                ls.append([(xa, ry), (xb, ry)])
            cv.hair(ls)
        cv.hair([sec[0], sec[3]])


def _river(cv, X, Y, W, H, hy):
    pts_l, pts_r = [], []
    for i in range(21):
        t = i / 20
        y = hy + 1 + (Y + H + 2 - hy) * t ** 1.4
        cx = X + W * (.12 + .1 * math.sin(t * 5.2 + .4)) - W * .1 * t
        hw = 1 + W * .07 * t ** 1.3
        pts_l.append((cx - hw, y))
        pts_r.append((cx + hw, y))
    poly = pts_l + pts_r[::-1]
    cv.obj([poly], .5)
    _H(cv, poly, 0, 3, 1.)
    cv.hair(pts_r)


def _road(cv, X, Y, W, H, hy, vx):
    p = [(vx - 1, hy + 1), (vx + 1, hy + 1), (vx + W * .16, Y + H + 2), (vx - W * .05, Y + H + 2)]
    cv.obj([p], .5)
    _H(cv, p, 90, 3)


def _dropbox(cv, bx, base, s, rng, label=True):
    """An Oregon official ballot drop box: steel cabinet on a plinth, sloped hood over the slot,
    a ballot envelope going in. s = width of the front face."""
    bh = s * 1.25           # cabinet height
    d = s * .32             # side depth (seen to the right)
    dy = d * .45
    top = base - bh - s * .18
    # cast shadow on the ground, falling right
    sh = [(bx + s, base), (bx + s + d, base - dy), (bx + s + d + s * .9, base - dy * .2), (bx + s * 1.6, base + s * .14),
          (bx, base + s * .1)]
    cv.obj([sh], 0)
    _H(cv, sh, 0, 1.5)
    _H(cv, sh, 90, 3)
    # plinth
    pl = [(bx - s * .06, base - s * .18), (bx + s * 1.06, base - s * .18), (bx + s * 1.06, base), (bx - s * .06, base)]
    pls = [(bx + s * 1.06, base - s * .18), (bx + s * 1.06 + d, base - s * .18 - dy), (bx + s * 1.06 + d, base - dy),
           (bx + s * 1.06, base)]
    cv.obj([pl], 1.)
    _H(cv, pl, 0, 2)
    cv.obj([pls], 1.)
    _solid(cv, pls)
    # side of the cabinet (in shadow)
    side = [(bx + s, top), (bx + s + d, top - dy), (bx + s + d, base - s * .18 - dy), (bx + s, base - s * .18)]
    cv.obj([side], 1.)
    _H(cv, side, 90, 1.5)
    _H(cv, side, 30, 2)
    # front face: brushed steel, vertical rules, darker toward the corner
    fr = [(bx, top), (bx + s, top), (bx + s, base - s * .18), (bx, base - s * .18)]
    cv.obj([fr], 1.)
    _H(cv, [(bx + s * .62, top), (bx + s, top), (bx + s, base - s * .18), (bx + s * .62, base - s * .18)], 90, 2, .5)
    _H(cv, [(bx + s * .82, top), (bx + s, top), (bx + s, base - s * .18), (bx + s * .82, base - s * .18)], 0, 2)
    _H(cv, [(bx, top), (bx + s * .62, top), (bx + s * .62, base - s * .18), (bx, base - s * .18)], 90, 3, .5)
    cv.hair([[(bx + 1.5, top + 1.5), (bx + 1.5, base - s * .18 - 1.5)]])
    # door seam and handle
    cv.line([(bx + s * .08, top + bh * .42), (bx + s * .92, top + bh * .42)])
    hx = bx + s * .5
    hd = [(hx - s * .09, top + bh * .48), (hx + s * .09, top + bh * .48), (hx + s * .09, top + bh * .52),
          (hx - s * .09, top + bh * .52)]
    cv.obj([hd], .5)
    _solid(cv, hd)
    # label plate on the door: a ballot box tick and VOTE lettering
    if label:
        lx, ly, lw, lh = bx + s * .14, top + bh * .58, s * .72, bh * .3
        lab = _rect(lx, ly, lw, lh)
        cv.obj([lab], 1.)
        _H(cv, lab, 0, 3, .5, inset=.3)
        size = min(lh * .42, lw / 4.4 * .9)
        tw = text_width("VOTE", size)
        if size >= 3.5:
            ll = letter_lines("VOTE", lx + (lw - tw) / 2, ly + lh * .14, size)
            cv.obj([_rect(lx + (lw - tw) / 2 - 1.5, ly + lh * .1, tw + 3, size + 2)], 0)
            cv.line(ll)
            # little star rule below
            cv.hair([(lx + 2, ly + lh * .78), (lx + lw - 2, ly + lh * .78)])
    # hood over the slot, sloping back
    hood_f = [(bx - s * .05, top - s * .02), (bx + s * 1.05, top - s * .02), (bx + s * 1.05, top + s * .05),
              (bx - s * .05, top + s * .05)]
    hr = s * .22
    hood_t = [(bx - s * .05, top - s * .02), (bx + s * 1.05, top - s * .02), (bx + s * 1.05 + d, top - s * .02 - dy - hr),
              (bx - s * .05 + d, top - s * .02 - dy - hr)]
    hood_s = [(bx + s * 1.05, top - s * .02), (bx + s * 1.05 + d, top - s * .02 - dy - hr), (bx + s * 1.05 + d, top + s * .05 - dy),
              (bx + s * 1.05, top + s * .05)]
    cv.obj([hood_t], 1.)
    _H(cv, hood_t, 0, 2)
    cv.obj([hood_s], 1.)
    _solid(cv, hood_s)
    # the slot: black mouth under the hood lip
    slot = [(bx + s * .14, top + s * .05), (bx + s * .86, top + s * .05), (bx + s * .86, top + s * .05 + max(2.2, s * .07)),
            (bx + s * .14, top + s * .05 + max(2.2, s * .07))]
    cv.obj([hood_f], 1.)
    _H(cv, hood_f, 0, 1.5)
    cv.obj([slot], 0)
    _solid(cv, slot)
    # the ballot going in (stays above the slot, tilted)
    ew, eh = s * .62, s * .42
    ex, ey = bx + s * .52, top + s * .06
    a = -.32
    ca, sa = math.cos(a), math.sin(a)
    E = lambda u, v: (ex + u * ca - v * sa, ey + u * sa + v * ca)
    env = [E(-ew / 2, 0), E(ew / 2, 0), E(ew / 2, -eh), E(-ew / 2, -eh)]
    cv.obj([env], 1.)
    _H(cv, [E(-ew / 2, 0), E(ew / 2, 0), E(ew / 2, -eh * .35), E(-ew / 2, -eh * .35)], 0, 3, inset=.4)
    cv.hair([E(-ew / 2, -eh), E(0, -eh * .45), E(ew / 2, -eh)])
    # Easter egg: the X on the ballot is a pair of crossed drumsticks with ball tips
    bxc, byc = E(-ew * .2, -eh * .55)
    k = eh * .28
    for sg in (-1, 1):
        p0 = (bxc - k, byc + sg * k)
        p1 = (bxc + k, byc - sg * k)
        cv.line([p0, p1])
        cv.obj([_ell(p1[0], p1[1], .8, .8, 8)], .5)
    # a second ballot already falling in, its edge showing in the slot
    cv.hair([(bx + s * .2, top + s * .085), (bx + s * .45, top + s * .085)])
    return top - s * .3 - dy


def _capitol(cv, cx, base, s, rng):
    """The Oregon State Capitol: marble wings, colonnaded front, a fluted cylindrical drum and
    lantern, the Golden Pioneer on top. s = width of the drum."""
    # wings
    ww = s * 3.4
    wh = s * .62
    wings = _rect(cx - ww / 2, base - wh, ww, wh)
    cv.obj([wings], 1.)
    _H(cv, wings, 0, 3, .5)
    # windows: rows of dark slits
    rows = []
    for r in range(2):
        yy = base - wh * (.78 - .4 * r)
        x = cx - ww / 2 + 4
        while x < cx + ww / 2 - 4:
            if abs(x - cx) > s * .75:
                rows.append(_rect(x, yy, 1.6, wh * .24))
            x += 4.
    cv.obj(rows, 0)
    for p in rows:
        _solid(cv, p)
    cv.line([(cx - ww / 2, base - wh + 2), (cx + ww / 2, base - wh + 2)])
    # front block with colonnade
    fw, fh = s * 1.5, s * .92
    fb = _rect(cx - fw / 2, base - fh, fw, fh)
    cv.obj([fb], 1.)
    _H(cv, _rect(cx - fw / 2, base - fh, fw, fh * .22), 0, 2)
    cols = []
    for i in range(7):
        x = cx - fw / 2 + fw * (i + .5) / 7
        cols.append(_rect(x - 1.2, base - fh * .74, 2.4, fh * .58))
    gaps = []
    for i in range(6):
        x0 = cx - fw / 2 + fw * (i + .5) / 7 + 1.2
        x1 = cx - fw / 2 + fw * (i + 1.5) / 7 - 1.2
        gaps.append(_rect(x0, base - fh * .74, x1 - x0, fh * .58))
    cv.obj(gaps, 0)
    for g in gaps:
        _H(cv, g, 0, 1.5)
        _H(cv, g, 90, 2)
    # steps
    for k in range(4):
        sy = base - fh * .16 + k * fh * .04
        cv.hair([(cx - fw / 2 - k * 2, sy), (cx + fw / 2 + k * 2, sy)])
    # drum
    dh = s * 1.05
    dt = base - fh - dh
    drum = _rect(cx - s / 2, dt, s, dh)
    cv.obj([drum], 1.)
    fl = []
    for i in range(1, 22):
        t = i / 22
        x = cx - s / 2 * math.cos(PI * t)
        fl.append([(x, dt + dh * .12), (x, dt + dh * .92)])
    cv.hair(fl)
    sh = _rect(cx + s * .18, dt, s * .32, dh)
    _H(cv, sh, 0, 2)
    cv.line([(cx - s / 2, dt + dh * .1), (cx + s / 2, dt + dh * .1)])
    cv.line([(cx - s / 2, dt + dh * .94), (cx + s / 2, dt + dh * .94)])
    # stepped cap and lantern
    cap = [(cx - s * .5, dt), (cx - s * .38, dt - s * .1), (cx + s * .38, dt - s * .1), (cx + s * .5, dt)]
    cv.obj([cap], 1.)
    _H(cv, cap, 0, 2)
    lw, lh = s * .3, s * .3
    lan = _rect(cx - lw / 2, dt - s * .1 - lh, lw, lh)
    cv.obj([lan], 1.)
    _H(cv, lan, 90, 2)
    _H(cv, _rect(cx + lw * .1, dt - s * .1 - lh, lw * .4, lh), 0, 1.5)
    # the Golden Pioneer: a striding axeman in gilt (white figure, black shading)
    py = dt - s * .1 - lh
    ph = s * .42
    fig = [(cx - ph * .12, py), (cx + ph * .14, py), (cx + ph * .12, py - ph * .55), (cx + ph * .18, py - ph * .75),
           (cx + ph * .06, py - ph * .86), (cx - ph * .1, py - ph * .76), (cx - ph * .14, py - ph * .5)]
    head = _ell(cx + ph * .02, py - ph * .93, ph * .09, ph * .09, 10)
    cv.obj([fig, head], 1.)
    _H(cv, fig, 90, 1.5, .25)
    cv.line([(cx - ph * .2, py - ph * .95), (cx + ph * .2, py - ph * .55)])  # axe handle over shoulder
    axe = [(cx - ph * .2, py - ph * .95), (cx - ph * .3, py - ph * .85), (cx - ph * .25, py - ph * 1.05)]
    cv.obj([axe], .5)
    _solid(cv, axe)
    return dt


def _scene(X, Y, W, H, mode, seed, field_d):
    """Engrave the full field (no white left). mode: 'm' medium, 't' tall, 's' short."""
    rng = random.Random(seed)
    cv = C.Canvas()
    if mode == "s":
        # a sealed ballot envelope, crossed-drumstick X, on a ruled ground
        cv.obj([_rect(X - 4, Y - 4, W + 8, H + 8)], 0)
        _H(cv, _rect(X - 4, Y - 4, W + 8, H + 8), 0, 2, .5)
        ew, eh = W * .8, H * .72
        ex, ey = X + (W - ew) / 2, Y + (H - eh) / 2
        env = _rect(ex, ey, ew, eh)
        sh = _rect(ex + 2, ey + 2, ew, eh)
        cv.obj([sh], 0)
        _solid(cv, sh)
        cv.obj([env], 1.)
        _H(cv, env, 0, 3, 1., inset=.5)
        flap = [(ex, ey), (ex + ew / 2, ey + eh * .55), (ex + ew, ey)]
        cv.obj([flap + [(ex + ew, ey)]], 1.)
        cv.hair(C.hatch_poly(flap, 45, 2))
        sr = eh * .2
        scx, scy = ex + ew / 2, ey + eh * .55
        ring = _ell(scx, scy, sr + 1.2, sr + 1.2, 18)
        cv.obj([ring], 1.)
        _solid(cv, ring)
        seal = _ell(scx, scy, sr, sr, 18)
        cv.obj([seal], .5)
        # Easter egg: the seal's X is a pair of crossed drumsticks with ball tips
        k = sr * .62
        for sg in (-1, 1):
            p1 = (scx + k, scy - sg * k)
            cv.line([(scx - k, scy + sg * k), p1])
            cv.obj([_ell(p1[0], p1[1], .9, .9, 8)], .5)
            _solid(cv, _ell(p1[0], p1[1], .9, .9, 8))
        cid = C._uid("civfield", X, Y, W, H, mode)
        return f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{cid})">{cv.svg()}</g>'
    hy = Y + H * (.6 if mode == "m" else .68)
    _sky(cv, X, Y, W, H, hy)
    _clouds(cv, X, Y, W, H, hy, rng)
    _heron(cv, X + W * (.84 if mode == "m" else .2), Y + (hy - Y) * (.2 if mode == "m" else .2),
           max(1.5, W / 70.), flip=False)
    if mode == "m":
        _hood(cv, X + W * .36, hy + 1, W * .36, Y + H * .17, seed, light_left=False)
    else:
        _hood(cv, X + W * .72, hy - H * .06, W * .34, Y + H * .3, seed, light_left=False)
    _trees(cv, X - 2, X + W + 2, hy - H * .04, H * .045, rng)
    vx = X + W * (.36 if mode == "m" else .44)
    _fields(cv, X, Y, W, H, hy, vx)
    _river(cv, X, Y, W, H, hy)
    if mode == "t":
        s = W * .25
        _capitol(cv, X + W * .42, hy + H * .03, s, rng)
        # the plaza in front
        pz = [(X - 2, hy + H * .03), (X + W + 2, hy + H * .03), (X + W + 2, hy + H * .06), (X - 2, hy + H * .06)]
        cv.obj([pz], .5)
        _H(cv, pz, 0, 3)
        _road(cv, X, Y, W, H, hy + H * .06, X + W * .42)
        _dropbox(cv, X + W * .64, Y + H * .96, W * .2, rng)
    else:
        _road(cv, X, Y, W, H, hy, vx)
        _dropbox(cv, X + W * .6, Y + H * .95, min(W * .22, H * .42), rng)
    body = cv.svg()
    cid = C._uid("civfield", X, Y, W, H, mode)
    return f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex so the cartouche field and every margin is engraved)
# ------------------------------------------------------------------------------------------------

def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b, _d(C._superellipse(cx, cy, a, b), True, 0)


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("cvb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = _d(_ell(cx, cy, rx - 4.5, ry - 4.5, 64), True, 0)
    k = .7071
    iw, ih = (rx - 4.5) * 2 * k * 1.15, (ry - 4.5) * 2 * k * 1.1
    o.append(_scene(cx - iw / 2, cy - ih / 2, iw, ih, "s", seed, fd).replace(
        "<g clip", f'<path d="{fd}" fill="{C.pat("L")}" stroke="none"/><g clip', 1))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.75)
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
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("cvm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b, fd = _field(cx, cy, cw, ch)
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, "m", seed, fd))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _banner_letters(centre, text, h):
    if not text:
        return ""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    size = min(h * .5, 9.)
    tw = text_width(text, size)
    off = (L[-1] - tw) / 2

    def along(px):
        s = off + px
        for i in range(1, len(L)):
            if L[i] >= s:
                t = (s - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                a = math.atan2(centre[i][1] - centre[i - 1][1], centre[i][0] - centre[i - 1][0])
                return (centre[i - 1][0] + (centre[i][0] - centre[i - 1][0]) * t,
                        centre[i - 1][1] + (centre[i][1] - centre[i - 1][1]) * t, a)
        return centre[-1][0], centre[-1][1], 0.

    ll = letter_lines(text, 0, 0, size, along)
    return f'<path d="{_polyd(ll)}" stroke="#000" stroke-width="1.5" fill="none"/>'


def _layout_tall(w, h, seed, ctx):
    days, date = _facts(ctx)
    rng = random.Random(seed)
    o = []
    # the whole room is cut away first: no paper shows anywhere
    o.append(C.dark_ground((0, 0, w, h), "M"))
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    em = 9.
    o.append(C.egg_and_dart(0, 0, w, em))
    px0, py0 = 6., em + 5
    pw = w - 12
    ph = h - py0 - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .7
    cx, cy = w / 2, py0 + ph * .47
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
                   max_n=5, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("cvt", w, h, seed), px0, py0, pw, ph, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b, fd = _field(cx, cy, cw, ch)
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, "t", seed, fd))
    o.append(C.palmette(cx, cy - ch / 2 + 6, min(ch * .14, 40), True, rng.randrange(1 << 20)))
    bh = min(17, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .5, cw * 1.5, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_letters(centre, ("VOTE " + date) if date else "VOTE BY MAIL", bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: ruled, lettered with today's countdown
    o.append(f'<path d="M{_n(tx + 2.5)},{_n(ty + 2.5)}h{_n(tw - 3.5)}v{_n(th - 3.5)}h{_n(-(tw - 3.5))}z" fill="{C.pat("L")}" stroke="none"/>')
    label = (days + " DAYS") if days else "OREGON VOTES"
    size = min(th * .6, 14.)
    if size >= 4:
        txw = text_width(label, size)
        lx, ly = tx + (tw - txw) / 2, ty + (th - size) / 2 + .5
        o.append(f'<path d="M{_n(lx - 3)},{_n(ly - 1.5)}h{_n(txw + 6)}v{_n(size + 3)}h{_n(-(txw + 6))}z" fill="#fff" stroke="none"/>')
        o.append(f'<path d="{_polyd(letter_lines(label, lx, ly, size))}" stroke="#000" stroke-width="1.5" fill="none"/>')
        o.append(f'<path d="{_polyd(letter_lines(label, lx + .9, ly + .9, size))}" stroke="#000" stroke-width=".5" fill="none"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("cvf", w, h, seed), 0, fy, w, fh - 2,
                         C.dark_ground((0, fy, w, fh), "G") +
                         C.scroll_band(w * .02, fy, w * .96, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
