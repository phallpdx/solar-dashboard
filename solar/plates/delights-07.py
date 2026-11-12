"""delights-07 "Table talk" -- the dinner question: "If our house could talk, what would it say about us?"

The plate engraves the house itself at supper time: a Sauvie Island farmhouse under a ruled night
sky, its two windows lit like eyes and its open door glowing like a mouth, so the house is caught
mid-sentence; chimney smoke curls up into an acanthus-like volute (the house's speech). Douglas
firs, a split-rail fence and ruled island fields round it out; on tall plates Mt. Hood stands
behind and a heron wades the ditch. The moon's phase follows ctx["date"].
Easter egg: Parker's dog curled asleep on the porch step, and a tiny "P" cut in the gable vent.

Frame: the house style (engraving_codex); layouts are copied here so the vignette fills the whole
cartouche field (no white).
"""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, _n, _d, _ell_pts, _clip, _uid

PI = math.pi
TAU = 2 * PI


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def spiral(cx, cy, r0, r1, a0, turns, n=60, sgn=1):
    pts = []
    for i in range(n + 1):
        t = i / n
        r = r0 + (r1 - r0) * t
        a = a0 + sgn * TAU * turns * t
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def solid(cv, poly, pitch=.8):
    """A black mass: 1 px lines laid tight."""
    cv.line(hatch_poly(poly, 0, pitch))



# ------------------------------------------------------------------------------------------
# engraved lettering (stroke capitals on a 4 x 6 grid; drawn as paths, never <text>)
# ------------------------------------------------------------------------------------------
_O = [(2 + 2 * math.cos(a), 3 + 3 * math.sin(a)) for a in (TAU * i / 20 for i in range(21))]
_FONT = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5.1), (4, 3.9), (3, 3), (0, 3)], [(0, 0), (2.8, 0), (3.7, .8), (3.7, 2.2), (2.8, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.4, 6), (4, 4.4), (4, 1.6), (2.4, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.4, 2.5), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "O": [_O],
    "R": [[(0, 6), (0, 0), (3, 0), (4, .8), (4, 2.2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, .8), (3, 0), (1, 0), (0, .8), (0, 2.2), (1, 3), (3, 3), (4, 3.8), (4, 5.2), (3, 6), (1, 6), (0, 5.2)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 4.5), (.6, 5.6), (2, 6), (3.4, 5.6), (4, 4.5), (4, 0)]],
}


def letter_strokes(text, x, y, size, track=1.9):
    """Polylines for `text` with its top-left at (x, y), cap height `size`."""
    k = size / 6
    out = []
    cx = x
    for ch in text:
        if ch == " ":
            cx += k * 4
            continue
        for st in _FONT.get(ch, []):
            out.append([(cx + px * k, y + py * k) for px, py in st])
        cx += k * (4 + track)
    return out


def text_width(text, size, track=1.9):
    k = size / 6
    return sum(k * 4 if c == " " else k * (4 + track) for c in text) - k * track


def letter_on_curve(text, centre, size, track=2.):
    """Lettering centred along a polyline (the ribbon face): each glyph placed upright on it."""
    L = [0.]
    for a, b in zip(centre, centre[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = L[-1]
    tw = text_width(text, size, track)
    k = size / 6
    s = (tot - tw) / 2
    out = []

    def at(u):
        for i in range(1, len(L)):
            if L[i] >= u:
                t = (u - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
                a, b = centre[i - 1], centre[i]
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, math.atan2(b[1] - a[1], b[0] - a[0])
        a, b = centre[-2], centre[-1]
        return b[0], b[1], math.atan2(b[1] - a[1], b[0] - a[0])
    for ch in text:
        if ch == " ":
            s += k * 4
            continue
        px, py, ang = at(s + k * 2)
        c, si = math.cos(ang), math.sin(ang)
        for st in _FONT.get(ch, []):
            out.append([(px + (gx - 2) * k * c - (gy - 3) * k * si, py + (gx - 2) * k * si + (gy - 3) * k * c)
                        for gx, gy in st])
        s += k * (4 + track)
    return out

# ------------------------------------------------------------------------------------------
# scene parts
# ------------------------------------------------------------------------------------------

def _fir(cv, x, base, h, w, rng, tiers=5):
    """An engraved Douglas fir: stacked drooping tiers, needles hatched, dark under each tier."""
    tw = max(1.2, w * .08)
    tr = rect(x - tw / 2, base - h * .2, tw, h * .2)
    cv.obj([tr], 1.)
    solid(cv, tr)
    for i in range(tiers):
        f = i / tiers
        ty = base - h * .12 - (h * .86) * f
        th = h * .86 / tiers * 1.6
        hw = w / 2 * (1 - f * .8)
        top = (x + rng.uniform(-.4, .4), ty - th)
        poly = [top, (x + hw * .55, ty - th * .45), (x + hw, ty + th * .05), (x + hw * .55, ty - th * .08),
                (x + hw * .3, ty + th * .02), (x, ty - th * .06), (x - hw * .3, ty + th * .02),
                (x - hw * .55, ty - th * .08), (x - hw, ty + th * .05), (x - hw * .55, ty - th * .45)]
        cv.obj([poly], .5)
        cv.hair(hatch_poly(poly, 62, 1.5))
        under = [(x - hw, ty + th * .05), (x - hw * .5, ty - th * .3), (x + hw * .5, ty - th * .3),
                 (x + hw, ty + th * .05), (x + hw * .55, ty - th * .08), (x, ty - th * .06),
                 (x - hw * .55, ty - th * .08)]
        cv.line(hatch_poly(under, 0, 1.5))
        # right half in shadow
        half = [top, (x + hw * .55, ty - th * .45), (x + hw, ty + th * .05), (x, ty)]
        cv.hair(hatch_poly(half, -62, 1.5))


def _moon(cv, cx, cy, r, phase):
    disc = _ell_pts(cx, cy, r, r, 40)[:-1]
    cv.obj([disc], 1.)
    k = math.cos(phase * TAU)              # 1 new .. -1 full
    sd = -1 if phase < .5 else 1           # dark limb side
    limb = [(cx + sd * r * math.cos(a), cy + r * math.sin(a)) for a in (-PI / 2 + PI * i / 24 for i in range(25))]
    term = [(cx - sd * r * k * math.cos(a), cy + r * math.sin(a)) for a in (PI / 2 - PI * i / 24 for i in range(25))]
    cv.hair(hatch_poly(disc, 0, 3, .5))
    if k > -.9:
        cv.hair(hatch_poly(limb + term, 0, 3, 2))
    for dx, dy, rr in ((.3, -.2, .18), (-.25, .3, .14), (.05, .5, .1)):
        cv.hair([_ell_pts(cx + dx * r, cy + dy * r, rr * r, rr * r, 12)])


def _house(cv, cx, base, W, detail):
    """The farmhouse, gable end on, W wide. Returns anchor points."""
    bw, bh = W, W * .58
    x0, x1 = cx - bw / 2, cx + bw / 2
    wall_top = base - bh
    ridge = wall_top - W * .42
    ov = W * .07
    # chimney first (behind the roof)
    chx, chw = cx + W * .2, W * .09
    cht = ridge - W * .02
    ch_base = ridge + (wall_top - ridge) * .5
    chim = rect(chx, cht, chw, ch_base - cht)
    cv.obj([chim], 1.)
    cv.hair(hatch_poly(chim, 0, 1.5))
    cv.hair(hatch_poly(rect(chx + chw * .55, cht, chw * .45, ch_base - cht), 90, 1.5))
    cap = rect(chx - chw * .15, cht - max(1.6, chw * .3), chw * 1.3, max(1.6, chw * .3))
    cv.obj([cap], 1.)
    solid(cv, cap)
    # clapboard walls
    walls = rect(x0, wall_top, bw, bh)
    cv.obj([walls], 1.)
    cv.hair(hatch_poly(walls, 0, 2. if W > 70 else 1.5))
    flank = rect(x1 - bw * .08, wall_top, bw * .08, bh)
    cv.obj([flank], .5)
    cv.hair(hatch_poly(flank, 90, 1.5))
    cv.hair(hatch_poly(flank, 0, 1.5))
    # gable: board-and-batten, round vent with a "P"
    gable = [(x0, wall_top), (cx, ridge + W * .05), (x1, wall_top)]
    cv.obj([gable], .5)
    cv.hair(hatch_poly(gable, 90, 1.5))
    vr = W * .07
    vy = wall_top - (wall_top - ridge) * .4
    vent = _ell_pts(cx, vy, vr, vr, 24)[:-1]
    cv.obj([vent], 1.)
    if vr > 3.4:
        p = [(cx - vr * .3, vy + vr * .6), (cx - vr * .3, vy - vr * .6), (cx + vr * .1, vy - vr * .6),
             (cx + vr * .4, vy - vr * .32), (cx + vr * .1, vy - vr * .02), (cx - vr * .3, vy - vr * .02)]
        cv.line(p)
    else:
        cv.hair([(cx - vr, vy), (cx + vr, vy)])
        cv.hair([(cx, vy - vr), (cx, vy + vr)])
    # roof slopes: shingle courses, right slope in shadow
    rl = [(x0 - ov, wall_top + ov * .55), (cx, ridge), (cx, ridge + W * .06), (x0 + ov * .2, wall_top + ov * .1)]
    rr = [(cx, ridge), (x1 + ov, wall_top + ov * .55), (x1 - ov * .2, wall_top + ov * .1), (cx, ridge + W * .06)]
    for poly, dark in ((rl, False), (rr, True)):
        cv.obj([poly], 1.)
        cv.hair(hatch_poly(poly, 0, 1.5))
        if dark:
            cv.line(hatch_poly(poly, -38, 2))
    cv.heavy([(x0 - ov, wall_top + ov * .55), (cx, ridge), (x1 + ov, wall_top + ov * .55)])
    # windows: two lit eyes with shutters and flower boxes
    ww, wh = bw * .16, bh * .34
    for sx in (-1, 1):
        wx = cx + sx * bw * .3 - ww / 2
        wy = wall_top + bh * .14
        cv.obj([rect(wx - 1.2, wy - 1.2, ww + 2.4, wh + 2.4)], 1.)
        cv.obj([rect(wx, wy, ww, wh)], 1.)
        cv.line([(wx + ww / 2, wy), (wx + ww / 2, wy + wh)])
        cv.line([(wx, wy + wh / 2), (wx + ww, wy + wh / 2)])
        for s2 in (-1, 1):
            sh = rect(wx - 1.2 - ww * .42 if s2 < 0 else wx + ww + 1.2, wy - 1.2, ww * .42, wh + 2.4)
            cv.obj([sh], .5)
            cv.hair(hatch_poly(sh, 0, 1.5))
            cv.hair(hatch_poly(sh, 90, 1.5))
        box = rect(wx - 1.5, wy + wh + 1.2, ww + 3, max(2.2, wh * .3))
        cv.obj([box], 1.)
        cv.hair(hatch_poly(box, 90, 1.5))
        if detail:
            for k in range(4):
                cv.hair([_ell_pts(wx + ww * (k + .5) / 4, wy + wh + .6, 1.1, 1.1, 8)])
    # the glowing door (the mouth): open leaf dark, a lamplit table seen inside
    dw, dh = bw * .2, bh * .52
    dx, dy = cx - dw / 2, base - dh
    cv.obj([rect(dx - 1.5, dy - 1.5, dw + 3, dh + 1.5)], 1.)
    cv.obj([rect(dx, dy, dw, dh)], 1.)
    leaf = rect(dx, dy, dw * .3, dh)
    cv.obj([leaf], .5)
    solid(cv, leaf, 1.)
    # inside: a hanging lamp over the supper table
    lx = dx + dw * .65
    cv.hair([(lx, dy), (lx, dy + dh * .2)])
    lamp = [(lx - dw * .16, dy + dh * .32), (lx, dy + dh * .2), (lx + dw * .16, dy + dh * .32)]
    cv.obj([lamp], 1.)
    solid(cv, lamp, 1.)
    table = rect(dx + dw * .32, dy + dh * .58, dw * .66, max(1.2, dh * .06))
    cv.obj([table], 1.)
    solid(cv, table, 1.)
    for tx in (dx + dw * .4, dx + dw * .9):
        cv.line([(tx, dy + dh * .62), (tx, dy + dh * .9)])
    # floor boards
    cv.hair(hatch_poly(rect(dx + dw * .3, dy + dh * .9, dw * .7, dh * .1), 0, 1.5))
    # porch step
    step = rect(dx - dw * .7, base - 2.4, dw * 2.4, 2.4)
    cv.obj([step], 1.)
    cv.hair(hatch_poly(step, 0, 1.5))
    return dict(chim=(chx + chw / 2, cht - max(1.6, chw * .3)), door=(dx, dy, dw, dh))


def _dog(cv, x, y, s):
    """Parker's dog curled asleep: round body, tucked tail, head on paws, one ear up."""
    body = _ell_pts(x, y - s * .36, s * .6, s * .36, 24)[:-1]
    cv.obj([body], 1.)
    cv.hair([spiral(x + s * .02, y - s * .38, s * .1, s * .4, 0, .75, 18)])
    fur = [(x - s * .2, y - s * .3), (x + s * .55, y - s * .3), (x + s * .5, y - s * .05), (x - s * .1, y - s * .02)]
    cv.hair(hatch_poly(fur, 20, 1.5))
    head = _ell_pts(x - s * .56, y - s * .24, s * .26, s * .21, 16)[:-1]
    cv.obj([head], 1.)
    ear = [(x - s * .66, y - s * .38), (x - s * .55, y - s * .66), (x - s * .44, y - s * .38)]
    cv.obj([ear], .5)
    solid(cv, ear, 1.)
    cv.hair([(x - s * .74, y - s * .26), (x - s * .62, y - s * .25)])


def _smoke(cv, x, y, ex, ey, r, flip):
    """Chimney smoke rising from (x, y), drifting to (ex, ey) and curling there into a volute of
    radius r: the house's speech."""
    n = 36
    H = math.hypot(ex - x, ey - y)
    pts = []
    for i in range(n + 1):
        t = i / n
        u = t * t * (3 - 2 * t)
        wob = math.sin(t * 6.) * H * .04 * t
        pts.append((x + (ex - x) * (t * .35 + u * .65) + wob, y + (ey - y) * (1 - (1 - t) ** 2)))
    spi = spiral(ex + flip * r, ey, r, r * .1, 0 if flip < 0 else PI, 1.25, 40, flip)
    centre = pts + spi[1:]
    L = len(centre)
    left, right = [], []
    for i in range(L):
        a, b = centre[max(0, i - 1)], centre[min(L - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        t = i / (L - 1)
        w = r * (.15 + .5 * math.sin(min(1., t * 1.5) * PI * .85)) * (1 - t * .75)
        left.append((centre[i][0] + nx * w, centre[i][1] + ny * w))
        right.append((centre[i][0] - nx * w, centre[i][1] - ny * w))
    cv.obj([left + right[::-1]], .5)
    cut = int(L * .94)
    for f in (-.5, 0., .5):
        line = [(l[0] * (1 - f) / 2 + r_[0] * (1 + f) / 2, l[1] * (1 - f) / 2 + r_[1] * (1 + f) / 2)
                for l, r_ in zip(left[:cut], right[:cut])]
        cv.hair([line])
    cv.line([right[:cut]])
    er = max(1.2, r * .18)
    eye = _ell_pts(spi[-1][0], spi[-1][1], er, er, 10)[:-1]
    cv.obj([eye], 0)
    solid(cv, eye, .8)


def _heron(cv, x, y, s):
    """A great blue heron standing in the ditch."""
    body = [(x - s * .3, y - s * .55), (x + s * .05, y - s * .7), (x + s * .3, y - s * .6),
            (x + s * .5, y - s * .38), (x + s * .1, y - s * .42)]
    cv.obj([body], 1.)
    cv.hair(hatch_poly(body, 20, 1.5))
    cv.heavy([(x - s * .25, y - s * .6), (x - s * .38, y - s * .8), (x - s * .27, y - s * .98), (x - s * .36, y - s * 1.06)])
    head = _ell_pts(x - s * .39, y - s * 1.07, s * .06, s * .05, 10)[:-1]
    cv.obj([head], 1.)
    cv.line([(x - s * .44, y - s * 1.07), (x - s * .7, y - s * 1.03)])
    cv.hair([(x - s * .38, y - s * 1.11), (x - s * .2, y - s * 1.16)])
    for lx in (x, x + s * .07):
        cv.line([(lx, y - s * .44), (lx, y)])
    for i in range(3):
        cv.hair([(x - s * .5 + i * s * .12, y + 1.5 + i * .3), (x + s * .4 - i * s * .1, y + 1.5 + i * .3)])


# ------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------

def scene(field_pts, seed, date):
    rng = random.Random(seed)
    xs = [p[0] for p in field_pts]
    ys = [p[1] for p in field_pts]
    fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
    W, H = fx1 - fx0, fy1 - fy0
    cx = (fx0 + fx1) / 2
    tall = H > 140
    detail = H > 60
    cv = Canvas()
    # night sky, ruled; closer at the zenith
    cv.obj([field_pts], 0)
    horizon = fy0 + H * (.62 if tall else .66)
    cv.hair(hatch_poly(rect(fx0 - 2, fy0 - 2, W + 4, horizon - fy0 + 3), 0, 1.5))
    cv.hair(hatch_poly(rect(fx0 - 2, fy0 - 2, W + 4, H * .2 + 2), 0, 3, .75))
    # moon from the date, a few stars
    try:
        y_, m_, d_ = (int(v) for v in date.split("-"))
        days = (y_ - 2000) * 365.25 + (m_ - 1) * 30.6 + d_ - 6.1
        phase = (days / 29.53) % 1
    except Exception:
        phase = .3
    mr = max(4.5, H * .075)
    mx, my = fx0 + W * (.66 if not tall else .72), fy0 + H * (.2 if not tall else .14)
    _moon(cv, mx, my, mr, phase)
    for i in range(int(W * H / 700) + 4):
        sx, sy = fx0 + W * rng.uniform(.08, .92), fy0 + H * rng.uniform(.07, .45)
        if math.hypot(sx - mx, sy - my) < mr * 2.2 or abs(sx - cx) < W * .22:
            continue
        r = rng.choice((1., 1.2, 1.5))
        cv.obj([_ell_pts(sx, sy, r, r, 8)[:-1]], 0)
        cv.hair([(sx - r * 1.8, sy), (sx + r * 1.8, sy)])
        cv.hair([(sx, sy - r * 1.8), (sx, sy + r * 1.8)])
    # Mt. Hood (tall)
    if tall:
        hx, hb, hh = fx0 + W * .74, horizon + 1, H * .3
        mtn = [(hx - W * .36, hb), (hx - W * .12, hb - hh * .55), (hx - W * .03, hb - hh * .92), (hx, hb - hh),
               (hx + W * .05, hb - hh * .86), (hx + W * .16, hb - hh * .5), (hx + W * .4, hb)]
        cv.obj([mtn], 1.)
        cv.hair(hatch_poly(mtn, 0, 1.5))
        cv.hair(hatch_poly([(hx, hb - hh), (hx + W * .05, hb - hh * .86), (hx + W * .16, hb - hh * .5),
                            (hx + W * .4, hb), (hx + W * .06, hb)], 60, 1.5))
        snow = [(hx - W * .03, hb - hh * .92), (hx, hb - hh), (hx + W * .05, hb - hh * .86), (hx + W * .07, hb - hh * .7),
                (hx + W * .03, hb - hh * .74), (hx + W * .01, hb - hh * .64), (hx - W * .02, hb - hh * .76),
                (hx - W * .07, hb - hh * .7)]
        cv.obj([snow], .5)
        cv.hair(hatch_poly(snow, 100, 3))
        cv.hair([(hx + W * .01, hb - hh * .95), (hx + W * .02, hb - hh * .75)])
    # far hills
    hills = [(fx0 - 2, horizon + 2)]
    for i in range(41):
        t = i / 40
        hills.append((fx0 + W * t, horizon - H * (.035 + .03 * math.sin(t * 9 + seed % 7) + .02 * math.sin(t * 23))))
    hills += [(fx1 + 2, horizon + 2), (fx1 + 2, fy1 + 2), (fx0 - 2, fy1 + 2)]
    cv.obj([hills], 1.)
    cv.hair(hatch_poly(hills, 0, 1.5))
    cv.hair(hatch_poly(hills, 75, 3))
    # fields: ruled ground and furrows converging on the house
    ground = [(fx0 - 2, horizon + H * .02), (fx1 + 2, horizon + H * .02), (fx1 + 2, fy1 + 2), (fx0 - 2, fy1 + 2)]
    cv.obj([ground], .5)
    cv.hair(hatch_poly(ground, 0, 2))
    vpx, vpy = cx, horizon - H * .1
    y0_ = horizon + H * .06
    for i in range(-16, 17):
        if abs(i) < 2:
            continue
        x = cx + i * W * .055
        t0 = (y0_ - vpy) / (fy1 + 2 - vpy)
        cv.hair([(vpx + (x - vpx) * t0, y0_), (x, fy1 + 2)])
    # firs flanking the house
    hs = min(W * (.46 if tall else .33), H * (.5 if tall else .56))
    base = horizon + H * (.13 if tall else .16)
    firs = ((-1, 1.02, 1.3), (-1, .74, .95), (1, 1.0, 1.15), (1, .74, .8))
    if not tall and W > hs * 3.2:
        firs = ((-1, 1.5, .8), (1, 1.42, .9)) + firs
    for sx, k, hk in firs:
        if not detail and k < .8:
            continue
        _fir(cv, cx + sx * hs * k, base - H * .015, hs * hk, hs * .4 * hk ** .5, rng, 5 if tall else 4)
    # the house
    g = _house(cv, cx, base, hs, detail)
    dx, dy, dw, dh = g["door"]
    # the path, lightly stippled
    path = [(dx - dw * .1, base), (dx + dw * 1.1, base), (cx + W * .13, fy1 + 2), (cx - W * .13, fy1 + 2)]
    cv.obj([path], .5)
    cv.hair(hatch_poly(path, 0, 3))
    for i in range(int(W * .5)):
        px, py = rng.uniform(cx - W * .11, cx + W * .11), rng.uniform(base + 3, fy1)
        cv.hair([(px, py), (px + .5, py)])
    # the Easter egg: Parker's dog asleep on the step
    _dog(cv, dx - dw * .62, base - .3, max(6., hs * .16))
    # split-rail fence across the foreground, open at the path
    fy = base + (fy1 - base) * .5
    ph = max(5., H * .08)
    rh = max(1.6, ph * .15)
    for side in (-1, 1):
        xa, xb = (cx + W * .14, fx1 + 4) if side > 0 else (fx0 - 4, cx - W * .14)
        for ry in (.22, .6):
            rail = rect(xa, fy - ph + ph * ry, xb - xa, rh)
            cv.obj([rail], .5)
            cv.hair([(xa, fy - ph + ph * ry + rh * .65), (xb, fy - ph + ph * ry + rh * .65)])
        n = max(2, int((xb - xa) / max(14., W * .09)))
        for j in range(n + 1):
            p = xa + (xb - xa) * j / n
            if side > 0 and j == 0 or side < 0 and j == n:
                p -= side * 0
            post = rect(p - 1.4, fy - ph * 1.12, 2.8, ph * 1.12)
            cv.obj([post], .5)
            cv.hair([(p + .6, fy - ph * 1.08), (p + .6, fy)])
    # chimney smoke curling into speech
    chx, chy = g["chim"]
    room = chy - fy0
    sr = max(4., min(room * .3, W * .07))
    _smoke(cv, chx, chy - .5, cx - W * (.16 if tall else .17), fy0 + max(sr * 1.25, room * .3), sr, -1)
    return cv


# ------------------------------------------------------------------------------------------
# layouts (from engraving_codex, the vignette filling the whole field)
# ------------------------------------------------------------------------------------------

def _vignette(field_pts, cid, seed, date):
    cv = scene(field_pts, seed, date)
    d = _d(field_pts, True, 0)
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{cv.svg()}</g>'


def _cart_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - .3, b - .3)


def _stroke_path(pls, wgt):
    return f'<path d="{"".join(_d(p, tol=0) for p in pls)}" fill="none" stroke="#000" stroke-width="{wgt}"/>'


def _layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(max(gh * 1.9, 96), 150)
    o.append(_clip(_uid("b", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx + 1, ry + 1, 64), True)}" fill="#fff" stroke="none"/>')
    ring = _d(_ell_pts(cx, cy, rx + 1, ry + 1, 64), True) + _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    field = _ell_pts(cx, cy, rx - 2.5, ry - 2.5, 64)[:-1]
    o.append(_vignette(field, _uid("bv", w, h, seed), seed, date))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
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
    cw = min(w * .44, gh * 1.95)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = Canvas(), Canvas()
    for side in (-1, 1):
        vx, vy = cx + side * (cw / 2 + r), gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(_vignette(_cart_field(cx, cy, cw, gh + 4), _uid("mv", w, h, seed), seed, date))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h + ped_h * .3
    em = min(10., top_free * .5)
    o.append(C.dark_ground((0, 0, w, top_free), "L"))
    o.append(C.egg_and_dart(0, 0, w, em))
    o.append(C.dark_ground((0, h - ped_h, w, ped_h), "M"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = Canvas(), Canvas()
    r1 = min(pw * .16, ph * .25)
    for side in (-1, 1):
        vx, vy = cx + side * (cw * .5 + r1 * .55), py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .21)
    for side in (-1, 1):
        vx, vy = cx + side * (cw * .5 + r2 * .55), py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_vignette(_cart_field(cx, cy, cw, ch), _uid("tv", w, h, seed), seed, date))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh_ = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.3, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    cl = [(q[0], q[1] + bh_ * .52) for q in centre]
    k0 = int(len(cl) * .3)
    o.append(f'<path d="{_d(cl[k0:len(cl) - k0], tol=0)}" fill="none" stroke="#fff" stroke-width="{_n(bh_ * .62)}"/>')
    o.append(_stroke_path(letter_on_curve("TABLE TALK", cl, bh_ * .5), 1.5))
    p, (tx, ty, tw, th) = C.pedestal(0, h - ped_h, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z" fill="{C.pat("L")}" stroke="none"/>')
    msg = "IF OUR HOUSE COULD TALK"
    sz = min(th * .55, 9.)
    mw = text_width(msg, sz) + 12
    o.append(f'<path d="M{_n(w / 2 - mw / 2)},{_n(ty + th / 2 - sz / 2 - 2.5)}h{_n(mw)}v{_n(sz + 5)}h{_n(-mw)}z" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(_stroke_path(letter_strokes(msg, tx + (tw - text_width(msg, sz)) / 2, ty + th / 2 - sz / 2, sz), 1.5))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 7
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date)
    else:
        body = _layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
