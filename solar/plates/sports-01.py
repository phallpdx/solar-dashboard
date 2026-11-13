"""sports-01 (Portland Trail Blazers): the plate is the game.

Short   : a frieze of volutes flowing out of a medallion holding an engraved basketball, a pair of
          crossed drumsticks behind it (the Easter egg: Parker drums).
Medium  : a carved cartouche framing an evening court: the ball dropping through the net, Mt. Hood
          beyond, the rising moon (phase from the date); volutes flow to both ends.
Tall    : the full scene in a large cartouche between mirrored volutes whose lower eyes curl round
          basketballs; a ribbon banner lettered (in paths) with the last result parsed from the
          page; a pedestal whose tablet carries the season record; scroll frieze below.
Easter egg: crossed drumsticks (a tiny pair lies on the court beside the key).
"""
import sys
import math
import random
import re
import datetime
import engraving_codex as C
from engraving_codex import Canvas, _d, _n, _ell_pts, hatch_poly, _CR, _clip, _uid

PI = math.pi
TAU = 2 * PI


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------

def _norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.
    return tuple(c / l for c in v)


def _rot(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)

    def f(p):
        x, y, z = p
        y, z = y * cx - z * sx, y * sx + z * cx
        x, z = x * cy + z * sy, -x * sy + z * cy
        x, y = x * cz - y * sz, x * sz + y * cz
        return (x, y, z)
    return f


def _runs(pts, keep):
    out, cur = [], []
    for p, k in zip(pts, keep):
        if k and p is not None:
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def _offset(pl, d):
    out = []
    n = len(pl)
    for i in range(n):
        a, b = pl[max(0, i - 1)], pl[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        out.append((pl[i][0] - ty / l * d, pl[i][1] + tx / l * d))
    return out


def _dashes(pl, on, off):
    out, cur, acc, state = [], [pl[0]], 0., True
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        pos = 0.
        while pos < L - 1e-9:
            lim = (on if state else off) - acc
            take = min(lim, L - pos)
            pos += take
            acc += take
            p = (a[0] + (b[0] - a[0]) * pos / L, a[1] + (b[1] - a[1]) * pos / L)
            if state:
                cur.append(p)
            if acc >= (on if state else off) - 1e-9:
                if state and len(cur) > 1:
                    out.append(cur)
                state = not state
                acc = 0.
                cur = [p]
    if state and len(cur) > 1:
        out.append(cur)
    return out


def hatch_d(poly, angle, pitch, phase=0., inset=0.):
    return "".join(_d(p, tol=0) for p in hatch_poly(poly, angle, pitch, phase, inset))


# ------------------------------------------------------------------------------------------------
# the basketball: a sphere modelled in bulino, pebbled, with raised seams
# ------------------------------------------------------------------------------------------------

LIGHT = _norm((-.55, -.65, .55))


def ball(cv, cx, cy, r, spin=0., light=LIGHT, outline=1.):
    disc = _ell_pts(cx, cy, r, r, max(24, int(r * 3)))[:-1]
    cv.obj([disc], outline)
    pitch = 2.
    sets = [(_rot(.45, 0., -.5), .6, 0), (_rot(.2, 1.35, .3), .1, 1), (_rot(1.2, .5, 1.0), -.32, 2)]
    for fr, thr, kind in sets:
        if r < 6 and kind == 2:
            continue
        nlat = max(3, int(2 * r / pitch))
        for k in range(1, nlat):
            t = -1 + 2 * k / nlat
            rr = math.sqrt(1 - t * t)
            m = max(16, int(rr * r * 1.6))
            pts, keep = [], []
            for i in range(m + 1):
                th = TAU * i / m
                p = fr((rr * math.cos(th), t, rr * math.sin(th)))
                if p[2] <= 0:
                    pts.append(None)
                    keep.append(False)
                    continue
                b = p[0] * light[0] + p[1] * light[1] + p[2] * light[2]
                rim = kind == 0 and p[2] < .16 and b < -.15
                pts.append((cx + p[0] * r, cy + p[1] * r))
                keep.append(b < thr and not rim)
            cv.hair(_runs(pts, keep))
    rng = random.Random(int(cx * 7 + cy * 13 + r))
    dots = []
    for _ in range(int(r * r * .3)):
        a = rng.random() * TAU
        q = math.sqrt(rng.random()) * r * .93
        x, y = math.cos(a) * q / r, math.sin(a) * q / r
        z = math.sqrt(max(0., 1 - x * x - y * y))
        b = x * light[0] + y * light[1] + z * light[2]
        if .55 < b < .88:
            px, py = cx + x * r, cy + y * r
            dots.append([(px, py), (px + .35, py + .2)])
    cv.hair(dots)
    # seams: equator, a meridian, and the two curved side seams
    sf = _rot(.32, .22 + spin * .3, -.28)
    m = max(40, int(r * 5))
    sw = max(.8, min(1.5, r * .06))
    for kind in range(4):
        pts = []
        for i in range(m + 1):
            th = TAU * i / m
            if kind == 0:
                p = (math.cos(th), 0., math.sin(th))
            elif kind == 1:
                p = (0., math.cos(th), math.sin(th))
            else:
                s = .68 if kind == 2 else -.68
                rr = math.sqrt(1 - s * s)
                p = (s, rr * math.cos(th), rr * math.sin(th))
            pts.append(sf(p))
        scr = [(cx + p[0] * r, cy + p[1] * r) for p in pts]
        for run in _runs(scr, [p[2] > .05 for p in pts]):
            if len(run) < 3:
                continue
            a, b = _offset(run, sw), _offset(run, -sw)
            cv.obj([a + b[::-1]], 0)
            if r < 12:
                cv.line(run)
            else:
                cv.heavy(run)
    cv.obj([], 0)
    cv.line([(cx + (r - .7) * math.cos(-.2 + 1.9 * i / 29), cy + (r - .7) * math.sin(-.2 + 1.9 * i / 29)) for i in range(30)])


def drumstick(cv, x0, y0, x1, y1, w):
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    sh = []
    for i in range(13):
        u = i / 12 * .84
        hw = w / 2 * (1. if u < .5 else 1 - .62 * (u - .5) / .34)
        sh.append((u * L, hw))
    left = [(x0 + ux * s + nx * hw, y0 + uy * s + ny * hw) for s, hw in sh]
    right = [(x0 + ux * s - nx * hw, y0 + uy * s - ny * hw) for s, hw in sh]
    cv.obj([left + right[::-1]], 1.)
    for f in (-.45, .15):
        cv.hair([(x0 + ux * s + nx * hw * f, y0 + uy * s + ny * hw * f) for s, hw in sh])
    if w > 2.5:
        cv.hair([(x0 + ux * s - nx * hw * .75, y0 + uy * s - ny * hw * .75) for s, hw in sh])
    tcx, tcy = x0 + ux * L * .91, y0 + uy * L * .91
    tl, tw = L * .085, w * .4
    tip = [(tcx + ux * tl * math.cos(t) + nx * tw * math.sin(t), tcy + uy * tl * math.cos(t) + ny * tw * math.sin(t))
           for t in [TAU * i / 16 for i in range(16)]]
    cv.obj([tip], 1.)


def crossed_sticks(cv, cx, cy, size, ang=0.):
    for s in (-1, 1):
        a = ang + s * .62 - PI / 2
        dx, dy = math.cos(a) * size / 2, math.sin(a) * size / 2
        drumstick(cv, cx - dx, cy - dy, cx + dx, cy + dy, max(2.2, size * .09))


# ------------------------------------------------------------------------------------------------
# lettering in paths
# ------------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GLYPH = {
    "0": (.56, [_arc(.28, .5, .26, .5, 0, 360, 20)]),
    "1": (.42, [[(.06, .2), (.24, 0), (.24, 1)], [(.04, 1), (.44, 1)]]),
    "2": (.56, [_arc(.27, .27, .24, .25, 195, 380, 7) + [(.04, 1), (.54, 1)]]),
    "3": (.54, [_arc(.26, .25, .23, .25, 205, 450, 8), _arc(.26, .73, .27, .27, 270, 520, 8)]),
    "4": (.56, [[(.42, 1), (.42, 0), (.02, .72), (.56, .72)]]),
    "5": (.54, [[(.5, 0), (.1, 0), (.06, .44)] + _arc(.26, .7, .27, .3, 225, 500, 9)[1:]]),
    "6": (.56, [_arc(.28, .7, .26, .3, 0, 360, 14), [(.03, .68), (.12, .25), (.26, .04), (.46, 0)]]),
    "7": (.54, [[(.02, 0), (.54, 0), (.2, 1)]]),
    "8": (.54, [_arc(.27, .24, .21, .24, 0, 360, 12), _arc(.27, .73, .26, .27, 0, 360, 14)]),
    "9": (.56, [_arc(.28, .3, .26, .3, 0, 360, 14), [(.53, .32), (.44, .75), (.3, .96), (.1, 1)]]),
    "-": (.42, [[(.05, .56), (.37, .56)]]),
    "W": (.84, [[(0, 0), (.2, 1), (.42, .2), (.64, 1), (.84, 0)]]),
    "L": (.5, [[(.08, 0), (.08, 1), (.5, 1)]]),
    "B": (.54, [[(.08, .48)] + _arc(.32, .74, .2, .26, -90, 90, 6) + [(.08, 1), (.08, 0)] + _arc(.3, .24, .17, .24, -90, 90, 6) + [(.08, .48)]]),
    "A": (.66, [[(0, 1), (.33, 0), (.66, 1)], [(.13, .64), (.53, .64)]]),
    "Z": (.56, [[(.04, 0), (.54, 0), (.02, 1), (.54, 1)]]),
    "E": (.5, [[(.48, 0), (.08, 0), (.08, 1), (.5, 1)], [(.08, .5), (.4, .5)]]),
    "R": (.56, [[(.08, 1), (.08, 0)] + _arc(.3, .25, .22, .25, -90, 90, 6) + [(.08, .5)], [(.28, .5), (.56, 1)]]),
    "S": (.52, [_arc(.27, .26, .23, .25, -20, -270, 8) + _arc(.27, .74, .25, .26, -90, 160, 8)[1:]]),
    "I": (.2, [[(.1, 0), (.1, 1)]]),
    "P": (.54, [[(.08, 1), (.08, 0)] + _arc(.3, .26, .22, .26, -90, 90, 6) + [(.08, .52)]]),
    "C": (.6, [_arc(.32, .5, .3, .5, -40, -320, 14)]),
    "T": (.56, [[(0, 0), (.56, 0)], [(.28, 0), (.28, 1)]]),
    "Y": (.6, [[(0, 0), (.3, .5), (.6, 0)], [(.3, .5), (.3, 1)]]),
    "O": (.7, [_arc(.35, .5, .33, .5, 0, 360, 20)]),
    "K": (.56, [[(.08, 0), (.08, 1)], [(.54, 0), (.08, .58)], [(.24, .44), (.56, 1)]]),
    "H": (.6, [[(.06, 0), (.06, 1)], [(.54, 0), (.54, 1)], [(.06, .5), (.54, .5)]]),
    "D": (.6, [[(.08, 0), (.08, 1), (.26, 1)] + _arc(.26, .5, .3, .5, 90, -90, 10)[1:] + [(.08, 0)]]),
    "N": (.6, [[(.06, 1), (.06, 0), (.54, 1), (.54, 0)]]),
    "U": (.6, [[(.06, 0), (.06, .66)] + _arc(.3, .66, .24, .34, 180, 0, 8)[1:] + [(.54, 0)]]),
    "M": (.74, [[(.04, 1), (.06, 0), (.37, .8), (.68, 0), (.7, 1)]]),
    " ": (.3, []),
}


def text_width(s, size, track=.18):
    return sum((GLYPH.get(ch, GLYPH[" "])[0] + track) * size for ch in s) - track * size


def letter(s, size, place, track=.18):
    out = []
    x = 0.
    for ch in s:
        gw, strokes = GLYPH.get(ch, GLYPH[" "])
        for st in strokes:
            out.append([place(x + px * size, py * size) for px, py in st])
        x += (gw + track) * size
    return out


def lettering_svg(lines, sw=1., halo=3.):
    d = "".join(_d(pl, tol=.05) for pl in lines)
    return (f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_n(halo)}"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(sw)}"/>')


def along(centre, size, s, track=.18):
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    start = (S[-1] - text_width(s, size, track)) / 2

    def place(x, y):
        t = start + x
        k = 1
        while k < len(S) - 1 and S[k] < t:
            k += 1
        a, b = centre[k - 1], centre[k]
        f = (t - S[k - 1]) / ((S[k] - S[k - 1]) or 1)
        px, py = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        yy = y - size / 2
        return (px - math.sin(ang) * yy, py + math.cos(ang) * yy)
    return place


# ------------------------------------------------------------------------------------------------
# page content
# ------------------------------------------------------------------------------------------------

def _facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    res = re.search(r"Last game\s+([WL])\s+(\d+)\D{1,3}(\d+)", s)
    rec = re.search(r"Blazers\s+(\d+)\s*[-–]\s*(\d+)", s)
    result = f"{res.group(1)} {res.group(2)}-{res.group(3)}" if res else "RIP CITY"
    record = f"BLAZERS {rec.group(1)}-{rec.group(2)}" if rec else "RIP CITY"
    return result, record


def _moon_phase(ctx):
    try:
        d = datetime.date.fromisoformat((ctx or {}).get("date", "")[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    return ((d - datetime.date(2000, 1, 6)).days % 29.530588) / 29.530588


# ------------------------------------------------------------------------------------------------
# the vignette: an evening court under Mt. Hood, the ball dropping through the net
# ------------------------------------------------------------------------------------------------

def _moon(cv, mx, my, mr, phase):
    cv.obj([_ell_pts(mx, my, mr + 2.5, mr + 2.5, 32)[:-1]], 0)
    cv.obj([_ell_pts(mx, my, mr, mr, 32)[:-1]], 1.)
    k = math.cos(phase * TAU)
    waxing = phase < .5
    sgn = -1 if waxing else 1
    limb = [(mx + sgn * mr * math.cos(t), my + mr * math.sin(t)) for t in [-PI / 2 + PI * i / 30 for i in range(31)]]
    term = [(mx - sgn * k * mr * math.cos(t), my + mr * math.sin(t)) for t in [PI / 2 - PI * i / 30 for i in range(31)]]
    if k > -.97:
        cv.hair(hatch_poly(limb + term, 0, 1.5))
    # maria
    cv.hair([[(mx - mr * .35, my - mr * .2), (mx - mr * .05, my - mr * .28)],
             [(mx + mr * .15, my + mr * .3), (mx + mr * .42, my + mr * .18)]])


def court_scene(X, Y, W, H, phase=.3, seed=0, eggs=True):
    cv = Canvas()
    rng = random.Random(seed)
    cx = X + W / 2
    yh = Y + H * .6
    bot = Y + H + 2
    # sky, ruled
    cv.obj([[(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, yh + 1), (X - 2, yh + 1)]], 0)
    _mx, _my, _mr = X + W * .84, Y + H * .19, max(4., min(W, H) * .065)
    _sk, _ = st_sky(X - 2, Y - 2, X + W + 2, yh + 1, seed + 5, avoid=lambda x, y: math.hypot(x - _mx, y - _my) < _mr + 4,
                    top_dark=.35)
    cv.hair(_sk)
    # stars: tiny crosses in the upper sky (white knock-outs)
    for _ in range(int(W * H / 2500)):
        sx, sy = X + rng.uniform(.05, .95) * W, Y + rng.uniform(.04, .3) * H
        cv.obj([_ell_pts(sx, sy, 1.3, 1.3, 8)[:-1]], 0)
    _moon(cv, X + W * .84, Y + H * .19, max(4., min(W, H) * .065), phase)
    # Mt. Hood, left of the backboard: a sharp summit, broad shoulders, snowfields on top
    hx = X + W * .2
    pk = Y + H * .2
    bw = W * .56

    def prof(u):
        d = abs(u - .5) * 2
        s = d ** .75 * .55 + d ** 2.2 * .45
        if u > .5:
            s -= .06 * math.exp(-((d - .45) / .12) ** 2)
        else:
            s -= .05 * math.exp(-((d - .55) / .1) ** 2)
        return pk + (yh - pk) * s + math.sin(u * 41) * .5 * (1 - d)
    ridge = [(hx - bw / 2 + bw * i / 60, prof(i / 60)) for i in range(61)]
    mtn = ridge + [(hx - bw / 2, yh + 1)]
    cv.obj([mtn], 1.)
    snow = lambda x: pk + (yh - pk) * (.5 + .08 * math.sin(x * .5) + .05 * math.sin(x * 1.3))
    # snow: the right flank in shadow, sparse fall lines; the lit left flank white with gullies
    for j in range(1, 24):
        u = .5 + j / 24 * .48
        x0 = hx - bw / 2 + bw * u
        y0 = prof(u) + .8
        y1 = snow(x0) + 3
        if y1 > y0 + 1:
            pts = [(x0 + (y - y0) * .22 + math.sin(y * .4 + j) * .5, y) for y in [y0 + (y1 - y0) * t / 8 for t in range(9)]]
            cv.hair(pts if j % 2 or j < 8 else pts[:4])
    for j in range(3, 22, 3):
        u = .5 - j / 24 * .48
        x0 = hx - bw / 2 + bw * u
        y0 = prof(u) + 2
        cv.hair([(x0, y0), (x0 - 1.5, y0 + (snow(x0) - y0) * .6)])
    # rock and timber below the snow: dense, cross-hatched on the shadow side
    rock = [(x, max(y, snow(x))) for x, y in ridge] + [(hx - bw / 2, yh + 1)]
    cv.hair(hatch_poly(rock, 70, 2))
    rs = [(x, max(y, snow(x) + 3)) for x, y in ridge if x > hx - 2] + [(hx + bw / 2, yh + 1), (hx, yh + 1)]
    cv.hair(hatch_poly(rs, -20, 3))
    # firs along the horizon
    fh = H * .075
    fir = [(X - 2, yh + 1)]
    x = X - 2
    while x < X + W + 2:
        b = yh - fh * (.42 + .22 * math.sin(x * .045 + 1))
        t = rng.uniform(.45, 1.)
        fir += [(x + .4, b), (x + 1.8, b - fh * .65 * t), (x + 3.2, b)]
        x += 3.2
    fir += [(X + W + 2, yh + 1)]
    cv.obj([fir], .5)
    cv.hair(hatch_poly(fir, 90, 1.5))
    # the court: planks converging, grain, joints
    floor = [(X - 2, yh), (X + W + 2, yh), (X + W + 2, bot), (X - 2, bot)]
    cv.obj([floor], 1.)
    vy = yh - H * 1.1
    tt = (yh - vy) / (bot - vy)
    step = max(6., W * .04)
    K = int(W / step / tt) + 2
    seams = []
    for k in range(-K, K + 1):
        xb = cx + k * step
        seams.append([(cx + (xb - cx) * tt, yh), (xb, bot)])
    cv.hair(seams)
    for k in range(-K, K):
        for f in (.5,):
            xb = cx + (k + f) * step
            y0 = yh
            segs = []
            while y0 < bot:
                y1 = min(bot, y0 + rng.uniform(H * .06, H * .16))
                if rng.random() < .55:
                    a, b = (y0 + 1 - vy) / (bot - vy), (y1 - 1 - vy) / (bot - vy)
                    segs.append([(cx + (xb - cx) * a, y0 + 1), (cx + (xb - cx) * b, y1 - 1)])
                y0 = y1
            cv.hair(segs)
        yy = yh + rng.uniform(.05, .6) * (bot - yh)
        while yy < bot:
            a = (yy - vy) / (bot - vy)
            cv.hair([(cx + k * step * a, yy), (cx + (k + 1) * step * a, yy)])
            yy += H * rng.uniform(.18, .4)
    # floor shading: lighter in the middle, darker toward the edges and the viewer
    vign = []
    for side in (-1, 1):
        edge = [(cx + side * W * .32, yh), (cx + side * (W / 2 + 3), yh), (cx + side * (W / 2 + 3), bot), (cx + side * W * .2, bot)]
        vign += hatch_poly(edge, side * 30 + 90, 3)
    cv.hair(vign)
    # the key, painted (cross-hatched) and outlined
    lt, lb = W * .2, W * .3
    ly1 = yh + (bot - yh) * .66
    key = [(cx - lt / 2, yh + 2), (cx + lt / 2, yh + 2), (cx + lb / 2, ly1), (cx - lb / 2, ly1)]
    cv.obj([key], 1.5)
    cv.hair(hatch_poly(key, 0, 2, .5))
    cv.hair(hatch_poly(key, 90, 3))
    fr = lb / 2
    ring = _ell_pts(cx, ly1, fr, fr * .26, 48)
    cv.obj([], 0)
    cv.line([p for p in ring if p[1] >= ly1 - .1])
    cv.hair(_dashes([p for p in ring if p[1] <= ly1 + .1], 2.5, 2))
    cv.obj([[(X - 2, yh), (X + W + 2, yh), (X + W + 2, yh + 2.5), (X - 2, yh + 2.5)]], 0)
    cv.heavy([(X - 2, yh + 1.2), (X + W + 2, yh + 1.2)])
    # goal: pole and pad
    bbw, bbh = W * .42, W * .25
    bbx, bby = cx - bbw / 2, Y + H * .08
    pw = max(3., W * .03)
    pole = [(cx - pw / 2, bby + bbh), (cx + pw / 2, bby + bbh), (cx + pw / 2, yh - 1), (cx - pw / 2, yh - 1)]
    cv.obj([pole], 1.)
    cv.line([(cx + pw / 2 - 1.2, bby + bbh), (cx + pw / 2 - 1.2, yh - 1)])
    cv.hair([(cx + pw * .05, bby + bbh), (cx + pw * .05, yh - 1)])
    padh = H * .08
    pad = [(cx - pw * 1.4, yh - padh), (cx + pw * 1.4, yh - padh), (cx + pw * 1.7, yh + 2), (cx - pw * 1.7, yh + 2)]
    cv.obj([pad], 1.)
    cv.hair([p for p in hatch_poly(pad, 90, 1.5) if p[0][0] > cx])
    cv.hair([[(cx - pw * 1.45, yh - padh + 2.5), (cx + pw * 1.45, yh - padh + 2.5)]])
    # backboard
    bb = [(bbx, bby), (bbx + bbw, bby), (bbx + bbw, bby + bbh), (bbx, bby + bbh)]
    cv.obj([bb], 1.5)
    fi = max(2., bbw * .03)
    inner = [(bbx + fi, bby + fi), (bbx + bbw - fi, bby + fi), (bbx + bbw - fi, bby + bbh - fi), (bbx + fi, bby + bbh - fi)]
    cv.line([inner + [inner[0]]])
    cv.hair(hatch_poly([(bbx + bbw - fi, bby + fi), (bbx + bbw, bby), (bbx + bbw, bby + bbh), (bbx + bbw - fi, bby + bbh - fi)], 90, 1.5, .2))
    cv.hair(hatch_poly([(bbx + fi, bby + bbh - fi), (bbx + bbw - fi, bby + bbh - fi), (bbx + bbw, bby + bbh), (bbx, bby + bbh)], 0, 1.5, .2))
    # glass: the sky through it, broken by two raking glints
    out = []
    y = bby + fi + 1.
    while y < bby + bbh - fi:
        x0, x1 = bbx + fi + .5, bbx + bbw - fi - .5
        cuts = sorted((c0 + (y - bby) * .7, c0 + (y - bby) * .7 + wd) for c0, wd in ((bbx + bbw * .12, bbw * .13), (bbx + bbw * .32, bbw * .045)))
        cur = x0
        for a, b in cuts:
            if a > cur:
                out.append([(cur, y), (min(a, x1), y)])
            cur = max(cur, b)
        if cur < x1:
            out.append([(cur, y), (x1, y)])
        y += 2.
    cv.hair([o for o in out if o[1][0] - o[0][0] > .8])
    sq_w, sq_h = bbw * .36, bbh * .4
    sqx, sqy = cx - sq_w / 2, bby + bbh - fi - sq_h - bbh * .04
    cv.obj([[(sqx - 1.2, sqy - 1.2), (sqx + sq_w + 1.2, sqy - 1.2), (sqx + sq_w + 1.2, sqy + sq_h), (sqx - 1.2, sqy + sq_h)]], 0)
    cv.heavy([[(sqx, sqy + sq_h), (sqx, sqy), (sqx + sq_w, sqy), (sqx + sq_w, sqy + sq_h)]])
    cv.hair(hatch_poly([(sqx + 1.5, sqy + 1.6), (sqx + sq_w - 1.5, sqy + 1.6), (sqx + sq_w - 1.5, sqy + sq_h), (sqx + 1.5, sqy + sq_h)], 0, 2, 1.))
    # rim and bracket
    rx = bbw * .3
    ry = rx * .3
    rcx, rcy = cx, bby + bbh + ry * .25
    brk = [(cx - rx * .26, bby + bbh - fi - 2), (cx + rx * .26, bby + bbh - fi - 2), (cx + rx * .16, rcy - ry + 1), (cx - rx * .16, rcy - ry + 1)]
    cv.obj([brk], 1.)
    cv.hair([p for p in hatch_poly(brk, 90, 1.5) if p[0][0] > cx])
    cv.obj([], 0)
    cv.heavy(_ell_pts(rcx, rcy, rx, ry, 48)[24:])
    nb = rx * 1.3
    m = 12
    rb = rx * .6

    def strands(front):
        res = []
        for i in range(m):
            a = TAU * (i + .5) / m
            if (math.sin(a) > 0) != front:
                continue
            for dirn in (-1, 1):
                pl = []
                for t in range(9):
                    u = t / 8
                    rr = rx + (rb - rx) * u ** .9
                    aa = TAU * (i + .5 + dirn * u * 1.1) / m
                    pl.append((rcx + rr * math.cos(aa), rcy + nb * u + ry * (1 - .4 * u) * math.sin(aa)))
                res.append(pl)
        return res
    cv.hair(strands(False))
    # the ball, dropping through
    brr = rx * .8
    bcx, bcy = rcx + rx * .05, rcy + brr * .3
    ball(cv, bcx, bcy, brr, spin=.3)
    cv.obj([], 0)
    cv.line(strands(True))
    loops = []
    for j in (.5, 1.):
        rr = rx + (rb - rx) * j ** .9
        loops.append([(rcx + rr * math.cos(a), rcy + nb * j + ry * (1 - .4 * j) * math.sin(a)) for a in [PI * i / 20 for i in range(21)]])
    cv.hair(loops)
    to = _ell_pts(rcx, rcy, rx + 1.4, ry + 1.4, 48)[:25]
    ti = _ell_pts(rcx, rcy, rx - 1.4, max(1., ry - 1.), 48)[:25]
    cv.obj([to + ti[::-1]], 1.)
    cv.line(_ell_pts(rcx, rcy + .9, rx, ry, 48)[3:22])
    # the arc of the shot, in fine dashes, from the left
    arc = []
    x0 = X + W * .04
    for i in range(40):
        u = i / 39
        arc.append((x0 + (bcx - brr * .6 - x0) * u, yh - H * .08 - (yh - H * .08 - (Y + H * .04)) * math.sin(PI * u * .78) ** 1.2 + u * (bcy - brr - yh + H * .08) * .0))
    arc = [p for p in arc if not (bbx - 3 < p[0] < bbx + bbw + 3 and p[1] < bby + bbh + 3)]
    if len(arc) > 2:
        cv.obj([], 0)
        cv.line(_dashes(arc, 2.5, 3.))
    # Easter egg: crossed drumsticks on the court beside the key
    if eggs:
        crossed_sticks(cv, cx + lb * .82, yh + (bot - yh) * .52, max(14., W * .15), ang=1.2)
    return cv.svg()


def medallion_scene(cx, cy, rx, ry):
    cv = Canvas()
    field = _ell_pts(cx, cy, rx, ry, 64)[:-1]
    cv.obj([field], 0)
    # the Moda Center floor: maple boards in perspective-free parquet, grain and staggered joints
    rng = random.Random(int(cx * 7 + cy))
    y = cy - ry - .25
    k = 0
    while y < cy + ry + 2:
        cv.line([(cx - rx - 2, y), (cx + rx + 2, y)])
        x = cx - rx - rng.uniform(0, 30)
        while x < cx + rx:
            x += rng.uniform(22, 40)
            cv.line([(x, y), (x, y + 4.5)])
            g = y + rng.choice((1.5, 3.))
            cv.hair([(x + 2, g), (x + rng.uniform(8, 18), g)])
        y += 4.5
        k += 1
    for sd in (-1, 1):
        cv.hair(_ell_pts(cx + sd * rx * 1.25, cy, rx * .75, ry * 1.2, 40, math.pi / 2, 3 * math.pi / 2) if sd > 0
                else _ell_pts(cx + sd * rx * 1.25, cy, rx * .75, ry * 1.2, 40, -math.pi / 2, math.pi / 2))
    rr = min(rx, ry)
    crossed_sticks(cv, cx, cy, rr * 2.1, ang=0.)
    ball(cv, cx, cy, rr * .68, spin=.2)
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts (adapted from the house frame so the whole field is engraved)
# ------------------------------------------------------------------------------------------------

def _pair_unit(cv, cx, cy, r, side, rng, a_out=0., turns=1.4, tail=.9, up=True, fronds=3, ball_eye=False):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    C._volute(cv, cx, cy, r, a0, turns, flip, rng, tail, -.5 if up else .5, r * .15, fronds)
    if ball_eye:
        ball(cv, cx, cy, r * .19, spin=side * .5)


def _field_fill(cx, cy, w, h, inner_d, scene, uid):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    body = scene(cx - a, cy - b, 2 * a, 2 * b)
    return (f'<clipPath id="{uid}"><path d="{inner_d}"/></clipPath><g clip-path="url(#{uid})">{body}</g>'
            f'<path d="{inner_d}" fill="none" stroke="#000" stroke-width="1"/>')


def layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    gap = min(gh * 1.5, 110)
    o.append(_clip(_uid("sb", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    uid = _uid("sm", w, h, seed)
    ell = _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(f'<clipPath id="{uid}"><path d="{ell}"/></clipPath><g clip-path="url(#{uid})">'
             + medallion_scene(cx, cy, rx - 2, ry - 2) + "</g>")
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0 - 1, w, gh + 2), "G"))
    cw = min(w * .42, gh * 1.5)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = Canvas(), Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True, ball_eye=r > 38)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("mm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    ph = _moon_phase(ctx)
    o.append(_field_fill(cx, cy, cw, ch, inner_d,
                         lambda X, Y, W, H: court_scene(X, Y, W, H, ph, seed, eggs=H > 110), _uid("mf", w, h, seed)))
    o.append(C.egg_and_dart(0, 0, w, em))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    result, record = _facts(ctx)
    em = min(12., 6 + h * .02)
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    px0, py0 = 0., em + 1
    pw = w
    ph = h - py0 - ped_h - frieze + ped_h * .3
    o.append(C.dark_ground((0, py0 - 1, w, h - py0 + 1), "G"))
    cw, ch = pw * .5, ph * .66
    cx, cy = w / 2, py0 + ph * .47
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = Canvas(), Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True, ball_eye=True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        _pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("tt", w, h, seed), px0, py0, pw, ph, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    phs = _moon_phase(ctx)
    o.append(_field_fill(cx, cy, cw, ch, inner_d,
                         lambda X, Y, W, H: court_scene(X, Y, W, H, phs, seed), _uid("tf", w, h, seed)))
    o.append(C.egg_and_dart(0, 0, w, em))
    # crest: a palmette carrying a ball finial, breaking up through the top moulding
    psz = min(ch * .16 + 8, 50)
    pal_y = cy - ch / 2 + 6
    o.append(C.palmette(cx, pal_y, psz, True, rng.randrange(1 << 20)))
    fr = max(5., psz * .2)
    fy_ = max(fr + 1.5, pal_y - psz * 1.0 - fr * .3)
    fcv = Canvas()
    ball(fcv, cx, fy_, fr, spin=.1)
    o.append(fcv.svg())
    # ribbon banner with the last result
    bh = min(18., max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    R = C._Rib(centre, [bh / 2] * len(centre), [bh / 2] * len(centre))
    face = [R.at(i / 40, .62) for i in range(41)] + [R.at(i / 40, -.62) for i in range(40, -1, -1)]
    o.append(f'<path d="{hatch_d(face, 0, 3, .5)}" stroke="#000" stroke-width=".5"/>')
    sz = bh * .5
    o.append(lettering_svg(letter(result, sz, along(centre, sz, result)), 1.5 if bh >= 15 else 1., 4.))
    # pedestal with the season record in the tablet
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    tab = [(tx + 3, ty + 3), (tx + tw - 1, ty + 3), (tx + tw - 1, ty + th - 1), (tx + 3, ty + th - 1)]
    o.append(f'<path d="{hatch_d(tab, 0, 2, .5)}" stroke="#000" stroke-width=".5"/>')
    sz = min(th * .56, 13)
    x0 = tx + (tw - text_width(record, sz)) / 2
    y0 = ty + (th - sz) / 2 + 1
    o.append(lettering_svg(letter(record, sz, lambda x, y: (x0 + x, y0 + y)), 1.5 if sz > 10 else 1., 4.5))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(_clip(_uid("tb", w, h, seed), 0, fy, w, fh - 2,
                       C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _player(cv, x, y, s, rng, light=True):
    """A small player cut in silhouette: feet at (x, y), s tall, with a cast shadow on the boards."""
    sh = C._ell_pts(x + s * .18, y + s * .03, s * .32, s * .06, 14)[:-1]
    cv.obj([sh], 0)
    cv.hair(C.hatch_poly(sh, 0, 1.))
    lean = rng.uniform(-.12, .12) * s
    st = rng.uniform(.12, .22) * s
    hip = (x + lean * .4, y - s * .48)
    cv.line([(x - st, y), (hip[0] - s * .04, hip[1])])
    cv.line([(x + st, y - s * .02), (hip[0] + s * .04, hip[1])])
    tor = [(hip[0] - s * .12, hip[1] + s * .06), (hip[0] + s * .12, hip[1] + s * .06),
           (hip[0] + s * .13 + lean * .3, hip[1] - s * .34), (hip[0] - s * .13 + lean * .3, hip[1] - s * .34)]
    cv.obj([tor], .5 if light else 1.)
    if not light:
        cv.hair(C.hatch_poly(tor, 70, 1.))
    sx, sy = hip[0] + lean * .3, hip[1] - s * .32
    ar = rng.uniform(-1, 1)
    cv.line([(sx - s * .12, sy), (sx - s * .26, sy + s * (.18 + ar * .12))])
    cv.line([(sx + s * .12, sy), (sx + s * .27, sy + s * (.16 - ar * .14))])
    hd = C._ell_pts(sx, sy - s * .09, s * .075, s * .085, 10)[:-1]
    cv.obj([hd], 1.)
    cv.hair(C.hatch_poly(hd, 45, 1.))


def arena_scene(X, Y, W, H, seed, result):
    """Tonight's matchup at the Moda Center, seen from the upper bowl: the roof's dark dome lit
    round the jumbotron (POR v OKC), the rim of lamps, the tiers of the crowd as pale heads on a
    dark stand with a drummer among them, the fascia, and the court below - boards laid in
    perspective, the painted keys, the players and the pinwheel at centre court."""
    rng = random.Random(seed)
    cv = C.Canvas()
    cx = X + W / 2
    q = max(1., H / 175.) ** .8
    r0, r1 = Y + H * .34, Y + H * .38          # roof rim, fascia foot
    t1 = Y + H * .62                           # crowd foot
    c0 = Y + H * .66                           # far sideline
    # roof: tone deepens toward the rim and the walls, pale round the hung screen
    roof = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, r0), (X - 2, r0)]
    cv.obj([roof], 0)
    cv.hair(C.hatch_poly(roof, 0, 1.6 * q))
    cv.hair(C.hatch_poly([(X - 2, Y + H * .18), (X + W + 2, Y + H * .18), (X + W + 2, r0), (X - 2, r0)], 0, 1.6 * q, .8))
    for k in range(-9, 10):
        bx = cx + k * W * .085
        cv.line([(cx + k * W * .02, Y - 2), (bx, r0)])
    for gk, gp in ((1., 2.4), (.72, 3.2), (.45, 4.5)):
        glow = C._ell_pts(cx, Y + H * .15, W * .28 * gk, H * .21 * gk, 40)[:-1]
        cv.obj([glow], 0)
        cv.hair(C.hatch_poly(glow, 0, gp * q))
    for k in range(-3, 4):
        cv.hair([(cx + k * W * .02, Y + H * .0), (cx + k * W * .085 * .55, Y + H * .3)])
    # rim of lamps and the fascia
    cv.heavy([(X - 2, r0), (X + W + 2, r0)])
    k = 0
    xx = X + 3
    while xx < X + W:
        lp = C._ell_pts(xx, r0 - 1.6, 1.3, 1.3, 8)[:-1]
        cv.obj([lp], .5)
        xx += 9 * q
    fas = [(X - 2, r0 + .8), (X + W + 2, r0 + .8), (X + W + 2, r1), (X - 2, r1)]
    cv.obj([fas], 1.)
    for i in range(int(W / 5)):
        x0 = X + i * 5
        cv.hair([(x0, r0 + 1.6), (x0 + 2.4, r0 + 1.6)])
    # the stands: a dark ground, the heads pale against it
    st = [(X - 2, r1), (X + W + 2, r1), (X + W + 2, t1), (X - 2, t1)]
    cv.obj([st], 0)
    cv.hair(C.hatch_poly(st, 0, 1.25 * q))
    cv.hair(C.hatch_poly([(X - 2, r1), (X + W + 2, r1), (X + W + 2, r1 + (t1 - r1) * .45), (X - 2, r1 + (t1 - r1) * .45)], 90, 1.4 * q))
    for sd in (-1, 1):                         # the aisles
        ax = cx + sd * W * .28
        cv.obj([[(ax - 2, r1), (ax + 2, r1), (ax + sd * 3 + 3, t1), (ax + sd * 3 - 3, t1)]], .5)
        for j in range(6):
            yy = r1 + (t1 - r1) * (j + .5) / 6
            cv.hair([(ax - 2.5, yy), (ax + 2.5, yy)])
    row, yy = 0, r1 + 2.2
    drummer = None
    while yy < t1 - 1:
        hr = (.85 + (yy - r1) / (t1 - r1) * 1.0) * q
        xx = X - 2 + (row % 2) * hr + rng.uniform(0, 1)
        while xx < X + W + 2:
            if min(abs(xx - (cx - W * .28)), abs(xx - (cx + W * .28))) > 3 + hr:
                if rng.random() < .9:
                    cv.obj([C._ell_pts(xx, yy, hr, hr * 1.1, 8)[:-1]], .5)
            xx += hr * 2.5 + rng.uniform(0, .9)
        if row == 3:
            drummer = (cx + W * .17, yy, hr)
        yy += hr * 2.7
        row += 1
    if drummer:                                # the egg: a drummer among them, sticks up
        dx, dy, hr = drummer
        d = hr * 2.2
        cv.obj([C._ell_pts(dx, dy - d * 1.3, hr * 1.2, hr * 1.2, 10)[:-1]], 1.)
        cv.obj([[(dx - d * .5, dy - d * .8), (dx + d * .5, dy - d * .8), (dx + d * .45, dy + d * .6), (dx - d * .45, dy + d * .6)]], 1.)
        body = [(dx - d * .7, dy + d * .1), (dx + d * .7, dy + d * .1), (dx + d * .7, dy + d * .7), (dx - d * .7, dy + d * .7)]
        cv.obj([body], 1.)
        cv.hair(C.hatch_poly(body, 60, 1.5))
        cv.obj([C._ell_pts(dx, dy + d * .1, d * .7, d * .25, 14)[:-1]], 1.)
        cv.line([(dx - d * .4, dy - d * .6), (dx - d * 1.1, dy - d * 1.4)])
        cv.line([(dx + d * .4, dy - d * .6), (dx + d * .9, dy - d * 1.6)])
    # the dasher boards
    db = [(X - 2, t1), (X + W + 2, t1), (X + W + 2, c0), (X - 2, c0)]
    cv.obj([db], 1.)
    cv.hair(C.hatch_poly(db, 0, 1. * q))
    # the court: boards laid across, closer and wider toward us, the joints staggered
    bot = Y + H + 2
    court = [(X - 2, c0), (X + W + 2, c0), (X + W + 2, bot), (X - 2, bot)]
    cv.obj([court], 1.)
    yy, g = c0 + 1.2 * q, 1.2 * q
    while yy < bot:
        cv.hair([(X - 2, yy), (X + W + 2, yy)])
        sc = g / 1.2 / q
        xx = X + rng.uniform(0, 30) * sc
        while xx < X + W:
            cv.hair([(xx, yy), (xx, min(bot, yy + g))])
            xx += rng.uniform(26, 44) * sc
        yy += g
        g = min(3.4 * q, g * 1.1)
    # the painted keys at either end, foreshortened, with the free-throw arcs
    for sd in (-1, 1):
        kx = cx + sd * W * .44
        key = [(kx - W * .09, c0 + 1), (kx + W * .09, c0 + 1), (kx + W * .13, bot), (kx - W * .13, bot)]
        cv.obj([key], 1.)
        cv.hair(C.hatch_poly(key, 0, 1.5 * q))
        fy = c0 + (bot - c0) * .62
        arc = [(kx + W * .12 * math.cos(t), fy + (bot - c0) * .16 * math.sin(t)) for t in [math.pi * (j / 16) for j in range(17)]]
        cv.line(arc)
    cv.line([(X - 2, c0 + 1), (X + W + 2, c0 + 1)])
    cv.line([(cx, c0 + 1), (cx, bot)])
    mid = c0 + (bot - c0) * .5
    cr = C._ell_pts(cx, mid, W * .1, (bot - c0) * .2, 48)
    cv.obj([cr[:-1]], 1.)
    # the pinwheel at centre court
    pr = min(W * .08, (bot - c0) * .17)
    for k in range(4):
        a0 = k * math.pi / 2 + .3
        blade = [(cx, mid)] + [(cx + pr * math.cos(a0 + t) * (1 if t < .9 else .6), mid + pr * .55 * math.sin(a0 + t) * (1 if t < .9 else .6)) for t in [j / 8 * 1.2 for j in range(9)]]
        cv.obj([blade], .5)
        if k % 2 == 0:
            cv.hair(C.hatch_poly(blade, 30, 1.))
    # the players, two at the jump, the rest spread, one side in white and one in black
    ps = (bot - c0) * .6
    for (fx, fy, lt) in ((-.05, .6, True), (.05, .58, False), (-.2, .82, False), (.24, .78, True), (-.33, .45, True), (.34, .4, False)):
        _player(cv, cx + fx * W, c0 + (bot - c0) * fy, ps * (.75 + fy * .35), rng, lt)
    # the jumbotron, hung from the crown, its own light on the cables
    jw, jh = W * .28, H * .14
    jx, jy = cx - jw / 2, Y + H * .1
    for sd in (-1, 1):
        cv.obj([], 0)
        cv.line([(cx + sd * jw * .3, Y - 2), (cx + sd * jw * .3, jy)])
    box = [(jx, jy), (jx + jw, jy), (jx + jw, jy + jh), (jx, jy + jh)]
    cv.obj([box], 1.5)
    scr = [(jx + 2.5, jy + 2.5), (jx + jw - 2.5, jy + 2.5), (jx + jw - 2.5, jy + jh - 2.5), (jx + 2.5, jy + jh - 2.5)]
    cv.obj([scr], .5)
    skirt = [(jx, jy + jh), (jx + jw, jy + jh), (jx + jw * .9, jy + jh * 1.4), (jx + jw * .1, jy + jh * 1.4)]
    cv.obj([skirt], 1.)
    cv.hair(C.hatch_poly(skirt, 0, 1.2))
    cv.hair(C.hatch_poly([(jx + jw * .62, jy + jh), (jx + jw, jy + jh), (jx + jw * .9, jy + jh * 1.4), (jx + jw * .58, jy + jh * 1.4)], 90, 1.2))
    for i in range(1, 4):
        lx = jx + jw * (.1 + .8 * i / 4)
        cv.obj([C._ell_pts(lx, jy + jh * 1.2, 1.1, 1.1, 8)[:-1]], .5)
    o = [cv.svg()]
    th = jh * .38
    o.append(st_letter("POR  v  OKC", th, cx=cx, cy=jy + jh / 2, sw=1., fit=jw * .8))
    return "".join(o)


def hoop_frame(cx, cy, rx, ry, fld, mode):
    """The frame is the game's own: a hoop on its stanchion standing either side of the arena,
    nets hanging, and the ball come to rest at the foot of the left one."""
    if mode == "band":
        return ""
    xs = [p[0] for p in fld]
    room = min(xs) - 4
    if room < 40:
        return ""
    cv = C.Canvas()
    foot = cy + ry - 2
    s = min(ry * 1.3, room * 1.6, 140.)
    for sd in (-1, 1):
        bx = cx + sd * (rx + room * .5)
        base = [(bx - s * .12, foot), (bx + s * .12, foot), (bx + s * .09, foot - s * .14), (bx - s * .09, foot - s * .14)]
        cv.obj([base], 1.)
        cv.hair(C.hatch_poly(base, 0, 1.2))
        cv.hair(C.hatch_poly([(bx + sd * .0, foot), (bx + sd * s * .12, foot), (bx + sd * s * .09, foot - s * .14), (bx, foot - s * .14)], 90, 1.4))
        top = foot - s * .78
        pole = [(bx - s * .025, foot - s * .14), (bx - s * .025, top), (bx - sd * s * .16 - s * .02, top - s * .06),
                (bx - sd * s * .16 + s * .02, top - s * .1), (bx + s * .025, top - s * .03), (bx + s * .025, foot - s * .14)]
        cv.obj([pole], 1.)
        cv.hair(C.hatch_poly(pole, 90, 1.2))
        # the backboard, faced square to us, then rim and net
        kx = bx - sd * s * .18
        bw, bh = s * .34, s * .22
        bb = [(kx - bw / 2, top - s * .2), (kx + bw / 2, top - s * .2), (kx + bw / 2, top - s * .2 + bh), (kx - bw / 2, top - s * .2 + bh)]
        cv.obj([bb], 1.5)
        cv.hair(C.hatch_poly([(kx + bw * .2, top - s * .2), (kx + bw / 2, top - s * .2), (kx + bw / 2, top - s * .2 + bh), (kx + bw * .2, top - s * .2 + bh)], 0, 2.))
        sq = [(kx - bw * .17, top - s * .2 + bh * .4), (kx + bw * .17, top - s * .2 + bh * .4), (kx + bw * .17, top - s * .2 + bh * .9), (kx - bw * .17, top - s * .2 + bh * .9)]
        cv.line(sq + [sq[0]])
        ry_ = top - s * .2 + bh * .92
        rr = bw * .22
        net_t, net_b = ry_, ry_ + s * .2
        for j in range(7):
            u = j / 6
            xt = kx - rr + 2 * rr * u
            xb = kx - rr * .55 + 2 * rr * .55 * u
            cv.hair([(xt, net_t), ((xt + xb) / 2 + rr * .12, (net_t + net_b) / 2), (xb, net_b)])
            cv.hair([(xt, net_t), ((xt + xb) / 2 - rr * .12, (net_t + net_b) / 2), (xb, net_b)])
        for j in range(1, 4):
            yy = net_t + (net_b - net_t) * j / 4
            ww = rr * (1 - .45 * j / 4)
            cv.hair([(kx - ww, yy), (kx + ww, yy)])
        cv.heavy(C._ell_pts(kx, ry_, rr, rr * .3, 24))
    br = s * .085
    bx = cx - rx - room * .5 + s * .22
    sh = C._ell_pts(bx + br * .4, foot - br * .05, br * 1.2, br * .25, 18)[:-1]
    cv.obj([sh], 0)
    cv.hair(C.hatch_poly(sh, 0, 1.))
    ball(cv, bx, foot - br, br)
    return cv.svg()


def arena_arch(cx, cy, rx, ry):
    """The Moda Center's own outline: a low dome over straight walls."""
    top, foot = cy - ry, cy + ry
    spring = top + ry * .62
    pts = [(cx - rx, foot), (cx - rx, spring)]
    for i in range(1, 48):
        t = math.pi - math.pi * i / 48
        pts.append((cx + rx * math.cos(t), spring - (spring - top) * math.sin(t)))
    pts += [(cx + rx, spring), (cx + rx, foot)]
    for i in range(1, 24):
        pts.append((cx + rx - 2 * rx * i / 24, foot))
    return pts


# ==== STUDIO FRAME (batch 2) ====================================================================
# King-tier frame, copied into this plate so it can be cut to the page (house rule: the shared
# modules stay untouched). Fine English scroll as on the GRS vise and Ken Hunt's panels: dozens of
# small logarithmic spirals grown from one stem, each branching into the next and carrying its own
# shaded leaves, packed over a punched matte ground; white "gold-line" wire borders and beading
# frame every panel; the subject sits in an inlaid medallion ringed with beads.
import math as _m
import random as _rnd
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _m.pi
_sm = _C._smooth


def _st_mat_tile():
    """An 8 px matte tile: black punched with 1 px white dots set evenly (blue noise)."""
    rng = _rnd.Random(91)
    pts = []
    tries = 0
    while len(pts) < 13 and tries < 4000:
        tries += 1
        p = (rng.randrange(16) * .5, rng.randrange(16) * .5)
        ok = True
        for q in pts:
            dx = min(abs(p[0] - q[0]), 8 - abs(p[0] - q[0]))
            dy = min(abs(p[1] - q[1]), 8 - abs(p[1] - q[1]))
            if dx * dx + dy * dy < 3.6:
                ok = False
                break
        if ok:
            pts.append(p)
    return "".join(f"M{_C._n(x)},{_C._n(y)}h1v1h-1z" for x, y in pts)


_ST_DEFS = ('<defs><pattern id="s2m" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h8v8h-8z" fill="#000"/><path d="{_st_mat_tile()}" fill="#fff"/></pattern>'
            '<pattern id="s2o" width="2" height="2" patternUnits="userSpaceOnUse"><path d="M0,0h.5v.5h-.5zM1,1h.5v.5h-.5z" fill="#000"/></pattern></defs>')


def st_matte(d):
    """The punched matte ground over path data d."""
    return f'<path d="{d}" fill="url(#s2m)" stroke="none"/>'


def st_rect_d(x, y, w, h):
    return f"M{_C._n(x)},{_C._n(y)}h{_C._n(w)}v{_C._n(h)}h{_C._n(-w)}z"


# ---------------------------------------------------------------------------------------------
# the fine scroll: spirals, leaves, growth from one stem
# ---------------------------------------------------------------------------------------------

def _spiral(px, py, head, R, s, turns):
    """A log spiral leaving (px, py) heading `head`, first radius R, turning toward side s
    (+1 = the +normal side), winding `turns` into an eye at .13 R. -> (pts, centre, radii)."""
    th = _TAU * turns
    b = _m.log(1 / .13) / th
    a0 = _m.atan2(s * R, -b * R)
    rot = head - a0
    cr, sr = _m.cos(rot), _m.sin(rot)
    pts, rad = [], []
    t = 0.
    while True:
        r = R * _m.exp(-b * t)
        lx, ly = r * _m.cos(t) - R, s * r * _m.sin(t)
        pts.append((px + lx * cr - ly * sr, py + lx * sr + ly * cr))
        rad.append(r)
        if t >= th:
            break
        t = min(th, t + max(.05, 1.4 / r))
    return pts, (px - R * cr, py - R * sr), rad


def _tangent(pts, i):
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    return _m.atan2(b[1] - a[1], b[0] - a[0])


class _Grid:
    def __init__(self, cell=24.):
        self.c = cell
        self.g = {}
        self.maxr = 0.

    def add(self, x, y, r, oid):
        self.g.setdefault((int(x // self.c), int(y // self.c)), []).append((x, y, r, oid))
        self.maxr = max(self.maxr, r)

    def clear(self, x, y, r, slack, ignore):
        reach = r + self.maxr
        c = self.c
        for i in range(int((x - reach) // c), int((x + reach) // c) + 1):
            for j in range(int((y - reach) // c), int((y + reach) // c) + 1):
                for qx, qy, qr, oid in self.g.get((i, j), ()):
                    if oid != ignore and (qx - x) ** 2 + (qy - y) ** 2 < ((r + qr) * slack) ** 2:
                        return False
        return True


def st_sweep(x, y, ang, L, k0, k1=None, n=None):
    """A sweeping stem: from (x, y) heading ang (radians), L long, curvature k0 -> k1 (1/px)."""
    k1 = k0 if k1 is None else k1
    return _C._euler(x, y, ang, L, lambda u: k0 + (k1 - k0) * u, n or max(8, int(L / 2)))


class ScrollField:
    """Grows fine scroll over a region. inside(x, y) says where scroll may grow. Scrolls branch
    from stems and from one another, each sized to the room it finds, until the field is packed."""

    def __init__(self, inside, rmin=7., rmax=30., seed=0, slack=.88):
        self.inside = inside
        self.rmin, self.rmax = rmin, rmax
        self.rng = _rnd.Random(seed)
        self.grid = _Grid(20.)
        self.slack = slack
        self.items = []
        self.queue = []

    def _ok(self, c, R, parent):
        if not self.inside(c[0], c[1]):
            return False
        if parent is not None and self.items[parent][1] == "scroll":
            pc, pR = self.items[parent][2][1], self.items[parent][2][4]
            if (pc[0] - c[0]) ** 2 + (pc[1] - c[1]) ** 2 < ((pR + R) * .78) ** 2:
                return False
        for k in range(8):
            a = k * _TAU / 8
            if not self.inside(c[0] + R * .55 * _m.cos(a), c[1] + R * .55 * _m.sin(a)):
                return False
        return self.grid.clear(c[0], c[1], R, self.slack, parent)

    def stem(self, pts, w0=2.2, w1=1.2, leaves=True, gen=0):
        """A sweeping lead, the source the scrolls grow from (points run from the root out)."""
        oid = len(self.items)
        for p in pts[::2]:
            self.grid.add(p[0], p[1], 2.5, oid)
        self.items.append((gen, "stem", (pts, w0, w1, leaves)))
        self.queue.append((gen, oid, "stem", pts, 0, None))
        return oid

    def scroll(self, px, py, head, R, s, gen=0, parent=None, turns=None, force=False):
        turns = turns or self.rng.uniform(1.25, 1.55)
        pts, c, rad = _spiral(px, py, head, R, s, turns)
        if not force and not self._ok(c, R, parent):
            return False
        oid = len(self.items)
        self.grid.add(c[0], c[1], R, oid)
        self.items.append((gen, "scroll", (pts, c, rad, s, R)))
        self.queue.append((gen, oid, "scroll", pts, s, (c, R)))
        return True

    def grow(self, max_items=300):
        rng = self.rng
        qi = 0
        while qi < len(self.queue) and len(self.items) < max_items:
            gen, oid, kind, pts, s, info = self.queue[qi]
            qi += 1
            n = len(pts)
            cand = []
            if kind == "scroll":
                c, R = info
                for f in (.03, .14, .27, .4, .52):
                    i = int(f * (n - 1))
                    q = pts[i]
                    tau = _tangent(pts, i)
                    rh = _m.hypot(q[0] - c[0], q[1] - c[1])
                    cand.append((q, tau, -s, self.rmax))
                    cand.append((q, tau + _PI, s, self.rmax * .8))
            else:
                for i in range(3, n - 2, 4):
                    q = pts[i]
                    tau = _tangent(pts, i)
                    for sd in (1, -1):
                        cand.append((q, tau + sd * .15, -sd, self.rmax))
                        cand.append((q, tau + _PI - sd * .2, sd, self.rmax * .7))
                rng.shuffle(cand)
            for q, head, cs, top in cand:
                Rc = min(self.rmax, top)
                while Rc >= self.rmin:
                    if self.scroll(q[0], q[1], head + cs * rng.uniform(-.05, .2), Rc, cs, gen + 1, oid):
                        break
                    Rc *= .82
        return self

    def _branch_to(self, oid, cx, cy, R):
        """A scroll centred at (cx, cy) whose stem leads in from the nearest coil of item oid,
        joining it tangentially, so every scroll grows out of another."""
        it = self.items[oid]
        pts = it[2][0]
        if it[1] == "scroll":
            pc, pR, rad = it[2][1], it[2][4], it[2][2]
            idx = [i for i in range(0, len(pts), 2) if rad[i] > pR * .45 and
                   (pts[i][0] - pc[0]) * (cx - pts[i][0]) + (pts[i][1] - pc[1]) * (cy - pts[i][1]) > 0] or list(range(0, len(pts) // 3))
        else:
            idx = list(range(0, len(pts), 2))
        bi = min(idx, key=lambda i: (pts[i][0] - cx) ** 2 + (pts[i][1] - cy) ** 2)
        q = pts[bi]
        tau = _tangent(pts, bi)
        ua = _m.atan2(q[1] - cy, q[0] - cx)
        S = (cx + R * _m.cos(ua), cy + R * _m.sin(ua))
        hx, hy = _m.cos(tau), _m.sin(tau)
        if hx * (S[0] - q[0]) + hy * (S[1] - q[1]) < 0:
            hx, hy = -hx, -hy
        turns = self.rng.uniform(1.25, 1.55)
        th = _TAU * turns
        bb = _m.log(1 / .13) / th
        best = None
        for sg in (1, -1):
            tx = -bb * _m.cos(ua) - sg * _m.sin(ua)
            ty = -bb * _m.sin(ua) + sg * _m.cos(ua)
            dot = tx * hx + ty * hy
            if best is None or dot > best[0]:
                best = (dot, sg, tx, ty)
        _, sg, tx, ty = best
        tl = _m.hypot(tx, ty)
        tx, ty = tx / tl, ty / tl
        L = _m.hypot(S[0] - q[0], S[1] - q[1])
        lead = []
        if L > 1.5:
            k = L * .45 + 2
            p1 = (q[0] + hx * k, q[1] + hy * k)
            p2 = (S[0] - tx * k, S[1] - ty * k)
            m = max(3, int(L / 1.5))
            for i in range(m):
                t = i / m
                a, b_, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
                lead.append((a * q[0] + b_ * p1[0] + c * p2[0] + d * S[0], a * q[1] + b_ * p1[1] + c * p2[1] + d * S[1]))
        sp, rad = [], []
        t = 0.
        while True:
            r = R * _m.exp(-bb * t)
            ph = ua + sg * t
            sp.append((cx + r * _m.cos(ph), cy + r * _m.sin(ph)))
            rad.append(r)
            if t >= th:
                break
            t = min(th, t + max(.05, 1.4 / r))
        allp = lead + sp
        allr = [R] * len(lead) + rad
        noid = len(self.items)
        self.grid.add(cx, cy, R, noid)
        self.items.append((it[0] + 1, "scroll", (allp, (cx, cy), allr, sg, R)))
        return True

    def fill(self, x, y, w, h, step=5., max_items=320):
        """Pack the field: find the widest free spot, branch a scroll into it from the nearest
        scroll's outer coil, repeat until no gap of about rmin is left."""
        rng = self.rng
        P = []
        nx, ny = max(2, int(w / step)), max(2, int(h / step))
        for j in range(ny):
            for i in range(nx):
                px, py = x + (i + .5) * w / nx, y + (j + .5) * h / ny
                if self.inside(px, py):
                    P.append([px, py, 1e9, None])
        if not P:
            return self
        cell = {}
        for k, p in enumerate(P):
            cell.setdefault((int(p[0] // 30), int(p[1] // 30)), []).append(k)

        def upd(oid, cx, cy, R, reach=None):
            reach = R + (reach or self.rmax * 3)
            for i in range(int((cx - reach) // 30), int((cx + reach) // 30) + 1):
                for j in range(int((cy - reach) // 30), int((cy + reach) // 30) + 1):
                    for k in cell.get((i, j), ()):
                        p = P[k]
                        d = _m.hypot(p[0] - cx, p[1] - cy) - R
                        if d < p[2]:
                            p[2], p[3] = d, oid
        obs = []
        for oid, it in enumerate(self.items):
            if it[1] == "scroll":
                obs.append((it[2][1][0], it[2][1][1], it[2][4], oid))
            else:
                obs.extend((q[0], q[1], 2.5, oid) for q in it[2][0][::5])
        for p in P:
            for ox, oy, orr, oid in obs:
                d = _m.hypot(p[0] - ox, p[1] - oy) - orr
                if d < p[2]:
                    p[2], p[3] = d, oid
        import heapq
        hp = [(-p[2], k) for k, p in enumerate(P)]
        heapq.heapify(hp)
        while len(self.items) < max_items and hp:
            nd, k = heapq.heappop(hp)
            best = P[k]
            if -nd != best[2]:
                heapq.heappush(hp, (-best[2], k))
                continue
            if best[2] < self.rmin * 1.15:
                break
            px, py, D, oid = best
            if oid is None:
                continue
            R = min(self.rmax, D * .97) * rng.uniform(.9, 1.)
            self._branch_to(oid, px, py, R)
            upd(len(self.items) - 1, px, py, R)
            for kk in cell.get((int(px // 30), int(py // 30)), ()):
                heapq.heappush(hp, (-P[kk][2], kk))
        return self

    def draw(self, cv, egg=None, egg_gen=2):
        """Paint the branches first so each parent lies over its children. egg(cv, x, y, r) is
        cut into the eye of one scroll of generation egg_gen (the first big enough)."""
        rng = _rnd.Random(7)
        order = sorted(range(len(self.items)), key=lambda k: -self.items[k][0])
        egg_done = egg is None
        for k in order:
            gen, kind, data = self.items[k]
            if kind == "stem":
                pts, w0, w1, lv = data
                _draw_stem(cv, pts, w0, w1, rng, lv)
                continue
            pts, c, rad, s, R = data
            use = None
            if not egg_done and gen >= egg_gen and R > 14:
                use, egg_done = egg, True
            _draw_scroll(cv, pts, c, rad, s, R, rng, use)


def _leaf(cv, x, y, ang, L, W, bend, curl, rng, lobes=None):
    """A fine-scroll leaf: a curved blade scalloped on its outer edge and turning over at the tip,
    fine parallel cuts on its shadow side, a bright cut edge, a centre vein."""
    n = max(8, int(L / 1.2))
    sp = _C._euler(x, y, ang, L, lambda u: (bend + curl * _sm(.55, 1., u) ** 2 * 3.2) / L, n)
    c = 1 if bend >= 0 else -1
    nl = lobes or (3 if L > 14 else 2)
    ph = rng.uniform(0, .3)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        pr = min(1., u / .22) ** .6 * (1 - u) ** .7 * 1.35
        v = (u * nl + ph) % 1.
        wo.append(W * pr * (.6 + .4 * _m.sin(_PI * v) ** .6) + .3)
        wi.append(W * pr * .85 + .3)
    R = _C._Rib(sp, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    cv.hair(_C._fill_lines(R, .22 * c, .92 * c, 1.5, .06, .9, 2))
    if W > 2.4:
        cv.hair(R.contour(-.05 * c, .12, .72))
    for j in range(nl):
        u = (j - ph) / nl
        if .18 < u < .85 and R.width(u, -c) > 1.8:
            cv.hair([R.at(u, -.95 * c), R.at(u + .05, -.4 * c)])
    return R


def _draw_stem(cv, pts, w0, w1, rng, leaves):
    n = len(pts)
    W = [w0 + (w1 - w0) * i / max(1, n - 1) for i in range(n)]
    R = _C._Rib(pts, W, W)
    if leaves:
        L = R.L
        u = .06
        sd = 1
        while u < .94:
            i = int(u * (n - 1))
            q = R.at(u, sd * .8)
            ll = rng.uniform(9, 13)
            _leaf(cv, q[0], q[1], _tangent(pts, i) + sd * .55, ll, ll * .22, -sd * .5, sd * 2.2, rng)
            sd = -sd
            u += rng.uniform(13, 18) / L
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(-.4, 0., 1.))
    cv.hair(R.contour(-.8, 0., 1.))


def _draw_scroll(cv, pts, c, rad, s, R, rng, egg=None):
    n = len(pts)
    hw0 = max(1., min(3.2, R * .13))
    W = [max(.6, hw0 * (rad[i] / R) ** .55) for i in range(n)]
    Rb = _C._Rib(pts, W, W)
    # where the coil proper starts (after any lead-in)
    k0 = 0
    while k0 < n - 1 and rad[k0 + 1] >= R - 1e-6:
        k0 += 1
    span = n - 1 - k0
    nlv = 1 if R < 10 else (2 if R < 16 else 3)
    fs = (.03, .2, .36)[:nlv]
    for j, f in enumerate(fs[::-1]):
        i = k0 + int(f * span)
        q = Rb.at(i / (n - 1), -s)
        ll = rad[i] * rng.uniform(.8, .95)
        _leaf(cv, q[0], q[1], _tangent(pts, i) - s * .55, ll, ll * .25, s * .9, -s * rng.uniform(1.2, 1.8), rng)
    if k0 > 6:
        i = k0 // 2
        q = Rb.at(i / (n - 1), s)
        ll = min(R * .7, 12.)
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .6, ll, ll * .24, -s * .7, s * 1.6, rng)
    cv.obj([Rb.outline()], .5)
    cv.hair(Rb.contour(.5 * s, 0., .92))
    if hw0 > 1.8:
        cv.hair(Rb.contour(.82 * s, 0., .8))
        cv.hair(Rb.contour(-.55 * s, .0, .35))
    if R > 15:
        i = k0 + int(.55 * span)
        q = Rb.at(i / (n - 1), s)
        ll = rad[i] * .95
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .35, ll, ll * .2, s * 1.6, s * .3, rng, 2)
    ex, ey = pts[-1]
    if egg:
        egg(cv, ex, ey, max(5., R * .4))
    else:
        rr = max(1.1, W[-1] * 1.4)
        cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)
        cv.line(_C._ell_pts(ex, ey, .3, .3, 4))


# ---------------------------------------------------------------------------------------------
# borders, beading, medallion, arms
# ---------------------------------------------------------------------------------------------

def st_wire(d):
    """A gold-line (wire inlay) border along path d: white wire, black, white wire on a black bed."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="5"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="3"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>')


def st_beads(d, pitch=3.5, r=1.):
    """A row of white beads on a black fillet along path d."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_C._n(2 * r + 2)}"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_C._n(2 * r)}" stroke-linecap="round" '
            f'stroke-dasharray="0 {_C._n(pitch)}"/>')


def st_ell_d(cx, cy, rx, ry, n=96):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n), True, .1)


def st_poly_d(poly):
    return _C._d(list(poly), True, .1)


def st_medallion(cx, cy, rx, ry):
    """An inlaid portrait medallion: wire, a ring of beads, wire. -> (svg, field polygon)."""
    o = [f'<path d="{st_ell_d(cx, cy, rx + 7, ry + 7)}" fill="#000" stroke="none"/>',
         st_wire(st_ell_d(cx, cy, rx + 5.5, ry + 5.5)),
         st_beads(st_ell_d(cx, cy, rx + 1.5, ry + 1.5, 180), 3.5, 1.),
         f'<path d="{st_ell_d(cx, cy, rx - .5, ry - .5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), _C._ell_pts(cx, cy, rx - 1.2, ry - 1.2, 120)[:-1]


def st_arch(cx, top, bot, half, n=48):
    """An arched (round-headed) panel polygon: the binding's central panel."""
    r = half
    pts = [(cx - half, bot)]
    for i in range(n + 1):
        a = _PI + _PI * i / n
        pts.append((cx + r * _m.cos(a), top + r + r * _m.sin(a)))
    pts.append((cx + half, bot))
    return pts


def st_arch_medallion(cx, top, bot, half):
    o = [f'<path d="{st_poly_d(st_arch(cx, top - 7, bot + 7, half + 7))}" fill="#000" stroke="none"/>',
         st_wire(st_poly_d(st_arch(cx, top - 5.5, bot + 5.5, half + 5.5))),
         st_beads(st_poly_d(st_arch(cx, top - 1.5, bot + 1.5, half + 1.5, 96)), 3.5, 1.),
         f'<path d="{st_poly_d(st_arch(cx, top + .5, bot - .5, half - .5))}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_arch(cx, top + 1.2, bot - 1.2, half - 1.2, 72)


def st_shape_pts(shape, cx, cy, rx, ry, g=0., n=120, ph=0.):
    """The outline of a shaped panel grown outward by g: oval, roundel, arch or irregular."""
    if shape == "arch":
        return st_arch(cx, cy - ry - g, cy + ry + g, rx + g, max(24, n // 2))
    if shape == "roundel":
        rx = ry = min(rx, ry)
    pts = []
    for i in range(n):
        t = _TAU * i / n
        k = 1.
        if shape == "irregular":
            k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
        pts.append((cx + (rx * k + g) * _m.cos(t), cy + (ry * k + g) * _m.sin(t)))
    return pts


def st_shape_in(shape, x, y, cx, cy, rx, ry, g=0., ph=0.):
    if shape == "arch":
        if y >= cy - ry + rx:
            return abs(x - cx) < rx + g and y < cy + ry + g
        return _m.hypot(x - cx, y - (cy - ry + rx)) < rx + g
    if shape == "roundel":
        rx = ry = min(rx, ry)
    t = _m.atan2((y - cy) / max(ry, 1), (x - cx) / max(rx, 1))
    k = 1.
    if shape == "irregular":
        k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
    return ((x - cx) / (rx * k + g)) ** 2 + ((y - cy) / (ry * k + g)) ** 2 < 1


def st_shaped_medallion(shape, cx, cy, rx, ry, ph=0.):
    """A shaped inlaid panel: black bed, wire, beads, white fillet. -> (svg, field polygon)."""
    if shape == "oval":
        return st_medallion(cx, cy, rx, ry)
    P = lambda g, n=120: st_poly_d(st_shape_pts(shape, cx, cy, rx, ry, g, n, ph))
    o = [f'<path d="{P(7)}" fill="#000" stroke="none"/>', st_wire(P(5.5)), st_beads(P(1.5, 180), 3.5, 1.),
         f'<path d="{P(-.5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_shape_pts(shape, cx, cy, rx, ry, -1.2, 120, ph)


def st_dedication(cx, foot, hh):
    """The small Somaster dedication cartouche at a front vignette's foot (about 30 px)."""
    return st_arms(cx, foot - hh / 2, hh * .5, hh * .5, mantling=True)


def st_device(w, h, seed, hk):
    """A marginal device (a 40-60 px roundel): the subject in a beaded roundel, the corners of
    the block cut away to the matte with a leaf in each spandrel."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    cx, cy = w / 2, h / 2
    r = min(w, h) / 2 - (4.5 if min(w, h) < 64 else 7.5)
    cv = StCanvas()
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * (w / 2 - 3), cy + sy * (h / 2 - 3)
            a = _m.atan2(cy - py, cx - px)
            if _m.hypot(px - cx, py - cy) > r + 9:
                L = max(4., (_m.hypot(px - cx, py - cy) - r - 6) * 1.1)
                _leaf(cv, px, py, a, L, L * .42, .5 * sx * sy, .35, _rnd.Random(seed + sx * 3 + sy))
    o.append(cv.svg())
    o.append(st_wire(st_rect_d(1.5, 1.5, w - 3, h - 3)))
    o.append(f'<path d="{st_ell_d(cx, cy, r + 3.5, r + 3.5)}" fill="#000"/>'
             f'<path d="{st_ell_d(cx, cy, r + 2, r + 2)}" fill="none" stroke="#fff" stroke-width="1" stroke-dasharray="1 1.5"/>'
             f'<path d="{st_ell_d(cx, cy, r - .2, r - .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    fld = _C._ell_pts(cx, cy, r - .9, r - .9, 72)[:-1]
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2d{w}x{h}v", fld, hk["field"](fld, "device") + st_rim(fld, 2.5)))
    return "".join(o)


def st_clip_poly(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{_C._d(list(poly), True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_clip_rect(cid, x, y, w, h, body):
    return f'<clipPath id="{cid}"><path d="{st_rect_d(x, y, w, h)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_sun(cv, cx, cy, r, rays=16):
    disc = _C._ell_pts(cx, cy, r, r, 28)[:-1]
    for k in range(rays):
        a = k * _TAU / rays
        ln = r * (1.9 if k % 2 == 0 else 1.5)
        w = _PI / rays * .7
        tri = [(cx + r * .9 * _m.cos(a - w), cy + r * .9 * _m.sin(a - w)), (cx + ln * _m.cos(a), cy + ln * _m.sin(a)),
               (cx + r * .9 * _m.cos(a + w), cy + r * .9 * _m.sin(a + w))]
        cv.obj([tri], .5)
        cv.hair([(cx + r * _m.cos(a + w * .4), cy + r * _m.sin(a + w * .4)), (cx + ln * .9 * _m.cos(a), cy + ln * .9 * _m.sin(a))])
    cv.obj([disc], .5)
    cv.hair([p for p in _C.hatch_poly(disc, 45, 1.5) if p[0][0] + p[0][1] > cx + cy - r * .3])


def _stick(cv, x0, y0, x1, y1, w):
    a = _m.atan2(y1 - y0, x1 - x0)
    n = 16
    pts = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    W = [w * (1 - .55 * _sm(.6, .95, i / n)) for i in range(n + 1)]
    R = _C._Rib(pts, W, W)
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(.6, .02, .93))
    tx, ty = x1 + _m.cos(a) * w * .5, y1 + _m.sin(a) * w * .5
    cv.obj([_C._ell_pts(tx, ty, w * 1.1, w * .8, 12)[:-1]], .5)


def st_crossed_sticks(cv, cx, cy, L, w=1.3, ang=0.):
    """Parker's crossed drumsticks, bead tips up."""
    for sd in (-1, 1):
        a = ang - _PI / 2 + sd * .62
        dx, dy = _m.cos(a) * L / 2, _m.sin(a) * L / 2
        _stick(cv, cx - dx, cy - dy, cx + dx, cy + dy, w)


_FLEUR = [(0, -1), (.13, -.72), (.16, -.42), (.1, -.15), (.24, -.2), (.42, -.42), (.62, -.48), (.78, -.38),
          (.8, -.18), (.68, -.02), (.54, .04), (.62, -.12), (.6, -.26), (.48, -.26), (.34, -.08), (.22, .1),
          (.36, .1), (.36, .22), (.14, .22), (.2, .5), (.38, .72), (.2, .7), (.08, .54), (0, .62)]


def _fleur(cx, cy, s):
    """A fleur-de-lis about 2s tall, as one closed polygon."""
    right = [(cx + x * s, cy + y * s) for x, y in _FLEUR]
    left = [(cx - x * s, cy + y * s) for x, y in _FLEUR[::-1]][1:-1]
    return right + left


def _heater(cx, top, w, h, n=24):
    """A heater shield outline: straight chief, sides curving to the point."""
    pts = [(cx - w / 2, top), (cx + w / 2, top)]
    for i in range(n + 1):
        t = i / n
        pts.append((cx + w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    for i in range(n, -1, -1):
        t = i / n
        pts.append((cx - w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    return pts


def st_arms(cx, cy, rx, ry, mantling=True):
    """Parker's arms, Somaster: Or, a castle between five fleurs-de-lis sable. A heater shield,
    Or as an even field of fine dots (Petra Sancta), the charges sable cut in solid black with
    white mortar lines; acanthus mantling springs from behind the shield's top corners."""
    o = []
    sh = min(ry * 2, rx * 2.3)
    sw = sh * .84
    top = cy - sh / 2
    shield = _heater(cx, top, sw, sh)
    if mantling:
        cv = _C.Canvas()
        rng = _rnd.Random(5)
        for sd in (-1, 1):
            for k, (a, L) in enumerate(((-.3, .9), (.25, .8), (.85, .7), (1.35, .55))):
                ang = (_PI / 2 - (a + 1.2)) if sd > 0 else (_PI / 2 + (a + 1.2))
                x0, y0 = cx + sd * sw * .42, top + sh * .1 + k * sh * .12
                _leaf(cv, x0, y0, -ang + _PI if False else (a * sd + (0 if sd > 0 else _PI)), sh * L * .55, sh * L * .12,
                      sd * .8, -sd * 2., rng, 3)
        o.append(cv.svg())
    d = st_poly_d(shield)
    o.append(f'<path d="{d}" fill="#000" stroke="#000" stroke-width="3"/>')
    o.append(f'<path d="{d}" fill="#fff" stroke="#fff" stroke-width="1"/>')
    o.append(f'<path d="{d}" fill="url(#s2o)" stroke="#000" stroke-width=".5"/>')
    blk = []
    s = sh * .085
    for fx, fy in ((-.26, .14), (0, .14), (.26, .14), (-.36, .55), (.36, .55)):
        blk.append(_fleur(cx + fx * sw, top + fy * sh + s * .1, s))
    # the castle: two towers and a curtain wall, crenellated, an arched gate with a portcullis
    cw, chh = sw * .46, sh * .3
    bx0, by1 = cx - cw / 2, top + sh * .72
    tw, th = cw * .24, chh * 1.3
    mer = tw / 5
    for tx in (bx0, bx0 + cw - tw):
        ty = by1 - th
        pts = [(tx, by1), (tx, ty)]
        for k in range(5):
            x = tx + k * mer
            if k % 2 == 0:
                pts += [(x, ty - mer), (x + mer, ty - mer)]
            else:
                pts += [(x, ty), (x + mer, ty)]
        pts += [(tx + tw, ty), (tx + tw, by1)]
        blk.append(pts)
    wy = by1 - chh * .72
    wx0, wx1 = bx0 + tw - .2, bx0 + cw - tw + .2
    nm = max(3, int((wx1 - wx0) / mer))
    mm = (wx1 - wx0) / nm
    pts = [(wx0, by1), (wx0, wy)]
    for k in range(nm):
        x = wx0 + k * mm
        if k % 2 == 1:
            pts += [(x, wy - mer * .9), (x + mm, wy - mer * .9)]
        else:
            pts += [(x, wy), (x + mm, wy)]
    pts += [(wx1, wy), (wx1, by1)]
    blk.append(pts)
    o.append(f'<path d="{"".join(st_poly_d(p) for p in blk)}" fill="#000" stroke="none"/>')
    # white work in the sable: mortar courses, tower windows, the gate and its portcullis
    lines = []
    for k in range(1, 6):
        y = by1 - k * chh * .2
        lines.append([(bx0 + 1, y), (bx0 + tw - 1, y)])
        lines.append([(bx0 + cw - tw + 1, y), (bx0 + cw - 1, y)])
        if y > wy + 1:
            lines.append([(wx0 + 1, y), (wx1 - 1, y)])
    gw, gh = cw * .2, chh * .55
    gate = [(cx - gw / 2, by1)] + [(cx - gw / 2 * _m.cos(t * _PI / 12), by1 - gh * .6 - gw / 2 * _m.sin(t * _PI / 12)) for t in range(13)] + [(cx + gw / 2, by1)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in lines)}" stroke="#fff" stroke-width="1" fill="none"/>')
    o.append(f'<path d="{st_poly_d(gate)}" fill="#fff" stroke="none"/>')
    pc = [[(cx + gw * (k / 4 - .5) * .8, by1 - gh * .95), (cx + gw * (k / 4 - .5) * .8, by1)] for k in range(5)]
    pc += [[(cx - gw * .45, by1 - gh * .3 * k), (cx + gw * .45, by1 - gh * .3 * k)] for k in (1, 2)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in pc)}" stroke="#000" stroke-width=".5" fill="none"/>')
    for tx in (bx0 + tw / 2, bx0 + cw - tw / 2):
        o.append(f'<path d="M{_C._n(tx)},{_C._n(by1 - th * .75)}v{_C._n(th * .22)}" stroke="#fff" stroke-width="1"/>')
    return "".join(o)


def st_sky(x0, y0, x1, y1, seed, avoid=None, clouds=None, top_dark=.32, pitch=(2., 2., 3., 3.)):
    """A Dore sky, not a ruled one: long lines that swell over billowing cloud banks (lit tops
    left white, undersides shaded), dark and cross-cut at the zenith, opening toward the horizon.
    Returns (hair polylines, line polylines). avoid(x, y) breaks the lines (moon, towers)."""
    rng = _rnd.Random(seed)
    W, H = x1 - x0, y1 - y0
    if clouds is None:
        clouds = []
        n = max(2, int(W / 80) + 1)
        for i in range(n):
            cx = x0 + W * (i + rng.uniform(.2, .8)) / n
            cy = y0 + H * rng.uniform(.3, .75)
            clouds.append((cx, cy, W / n * rng.uniform(.45, .7), H * rng.uniform(.09, .16)))
    hair, heavy = [], []

    def cloud_at(x, y):
        for cx, cy, rx, ry in clouds:
            dx = (x - cx) / rx
            if abs(dx) < 1:
                top = cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))
                bot = cy + ry * .35 * (1 - dx * dx) ** .5
                if top <= y <= bot:
                    return (y - top) / max(.5, bot - top)
        return None
    y = y0 + .75
    while y < y1:
        f = (y - y0) / max(1., H)
        p = pitch[min(len(pitch) - 1, int(f * len(pitch)))]
        run = []
        x = x0
        while x <= x1 + 3:
            yy = y
            for ccx, ccy, crx, cry in clouds:
                dx = (x - ccx) / (crx * 1.5)
                if abs(dx) < 1 and y > ccy:
                    yy += cry * .22 * (1 - dx * dx) ** 2 * max(0., 1 - (y - ccy) / (cry * 3))
            cf = cloud_at(x, yy)
            lit = cf is not None and cf < .55
            if lit or (avoid and avoid(x, yy)):
                if len(run) > 1:
                    hair.append(run)
                run = []
            else:
                run.append((x, yy))
            x += 3.
        if len(run) > 1:
            hair.append(run)
        y += p
    # cloud edges: billowed tops, shaded bellies
    for cx, cy, rx, ry in clouds:
        top = []
        for i in range(41):
            dx = -1 + 2 * i / 40
            top.append((cx + dx * rx, cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))))
        hair.append(top)
        for k in range(1, 4):
            arc = []
            for i in range(31):
                dx = -.85 + 1.7 * i / 30
                arc.append((cx + dx * rx * (1 - .12 * k), cy - ry * (1 - dx * dx) ** .5 * (.55 - .14 * k) + ry * .1 * k))
            hair.append(arc)
    # the zenith: cross-cut so the sky deepens upward
    zt = y0 + H * top_dark
    for ln in _C.hatch_poly([(x0, y0), (x1, y0), (x1, zt), (x0, zt)], 30, 3.):
        if avoid:
            a_, b_ = ln
            seg, cur = [], []
            for i in range(int(_m.dist(a_, b_) / 2) + 2):
                t = i / max(1, int(_m.dist(a_, b_) / 2) + 1)
                q = (a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t)
                if avoid(*q):
                    if len(cur) > 1:
                        hair.append(cur)
                    cur = []
                else:
                    cur.append(q)
            if len(cur) > 1:
                hair.append(cur)
        else:
            hair.append(ln)
    return hair, heavy


def st_rim(fld, depth=12., uid="r"):
    """Light emerging from dark: concentric cuts round the inside of a medallion field, close and
    heavy at the rim, thinning inward, so the subject glows out of a dark surround."""
    cx = sum(p[0] for p in fld) / len(fld)
    cy = sum(p[1] for p in fld) / len(fld)
    size = min(max(abs(p[0] - cx) for p in fld), max(abs(p[1] - cy) for p in fld))
    o1, o5 = [], []
    d = .75
    while d < depth:
        k = 1 - d / size
        ring = [(cx + (p[0] - cx) * k, cy + (p[1] - cy) * k) for p in fld]
        (o1 if d < depth * .35 else o5).append(_C._d(ring + [ring[0]], tol=.2))
        d += 2. if d < depth * .35 else 1.5 + (d / depth) * 1.5
    return (f'<path d="{"".join(o1)}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="{"".join(o5)}" fill="none" stroke="#000" stroke-width=".5"/>')


# ---------------------------------------------------------------------------------------------
# Easter eggs cut into a scroll's eye: egg(cv, x, y, r) draws inside a disc of radius r
# ---------------------------------------------------------------------------------------------

def _egg_disc(cv, x, y, r):
    cv.obj([_C._ell_pts(x, y, r, r, 28)[:-1]], 1.)
    cv.hair(_C._ell_pts(x, y, r - 1.2, r - 1.2, 28))


def egg_sticks(cv, x, y, r):
    """Parker's crossed drumsticks."""
    _egg_disc(cv, x, y, r)
    st_crossed_sticks(cv, x, y + r * .05, r * 1.45, max(.6, r * .09))


def egg_P(cv, x, y, r):
    """A "P" monogram, cut as a stem and a bowl with a flourish."""
    _egg_disc(cv, x, y, r)
    h = r * 1.1
    cv.line([(x - h * .22, y + h * .5), (x - h * .22, y - h * .5)])
    bowl = [(x - h * .22, y - h * .5)] + [(x - h * .05 + h * .3 * _m.sin(t * _PI / 10), y - h * .25 - h * .25 * _m.cos(t * _PI / 10)) for t in range(11)] + [(x - h * .22, y)]
    cv.line(bowl)
    cv.hair([(x - h * .45, y + h * .5), (x + h * .05, y + h * .5)])
    cv.hair([(x - h * .22, y + h * .5), (x - h * .5, y + h * .62), (x - h * .62, y + h * .45)])


def egg_note(cv, x, y, r):
    """A swing eighth-note pair (jazz)."""
    _egg_disc(cv, x, y, r)
    s = r * .32
    for dx in (-1, 1):
        hx, hy = x + dx * s * 1.1 - s * .4, y + s * 1.1
        cv.obj([_C._ell_pts(hx, hy, s * .55, s * .38, 12)[:-1]], .5)
        cv.line(_C._ell_pts(hx, hy, s * .3, s * .15, 8))
        cv.line([(hx + s * .5, hy), (hx + s * .5, y - s * 1.5)])
    cv.heavy([(x - s * .6 + s * .1, y - s * 1.5), (x + s * 1.6 + s * .1, y - s * 1.5)])


def egg_cymbal(cv, x, y, r):
    """A tiny ride cymbal on its stand, lathe rings and a bell."""
    _egg_disc(cv, x, y, r)
    cy = y - r * .15
    cv.obj([_C._ell_pts(x, cy, r * .8, r * .22, 24)[:-1]], .5)
    for k in (1, 2, 3):
        cv.hair(_C._ell_pts(x, cy, r * .8 * k / 4, r * .22 * k / 4, 20))
    cv.obj([_C._ell_pts(x, cy - r * .08, r * .16, r * .1, 10)[:-1]], .5)
    cv.line([(x, cy + r * .2), (x, y + r * .7)])
    cv.hair([(x, y + r * .55), (x - r * .35, y + r * .78)])
    cv.hair([(x, y + r * .55), (x + r * .35, y + r * .78)])


def egg_hood(cv, x, y, r):
    """Mt. Hood: the snow cone, its glaciers and a timber line."""
    _egg_disc(cv, x, y, r)
    pk = [(x - r * .82, y + r * .45), (x - r * .1, y - r * .55), (x + r * .05, y - r * .6), (x + r * .82, y + r * .45)]
    cv.obj([pk], .5)
    cv.hair([(x - r * .02, y - r * .5), (x - r * .25, y + r * .05)])
    cv.hair([(x + r * .05, y - r * .5), (x + r * .3, y + r * .1)])
    cv.hair(_C.hatch_poly([(x + r * .05, y - r * .58), (x + r * .82, y + r * .45), (x + r * .25, y + r * .45)], 60, 1.5))
    for k in range(7):
        tx = x - r * .7 + k * r * .23
        cv.line([(tx, y + r * .62), (tx, y + r * .38)])


def egg_pinwheel(cv, x, y, r):
    """The Blazers pinwheel: five pairs of swept bars turning about a hub."""
    _egg_disc(cv, x, y, r)
    for k in range(5):
        a = k * _TAU / 5 - _PI / 2
        for off in (-.12, .12):
            p0 = (x + r * .18 * _m.cos(a + off), y + r * .18 * _m.sin(a + off))
            p1 = (x + r * .78 * _m.cos(a + off + .35), y + r * .78 * _m.sin(a + off + .35))
            cv.line([p0, p1])


def egg_heron(cv, x, y, r):
    """A Sauvie Island heron's head and S neck, crest plume and dagger bill."""
    _egg_disc(cv, x, y, r)
    neck = [(x - r * .1, y + r * .8), (x - r * .35, y + r * .3), (x - r * .05, y - r * .05), (x - r * .25, y - r * .4)]
    cv.line(neck)
    cv.line([(x - r * .05 + r * .15, y + r * .8), (x - r * .2 + r * .12, y + r * .3), (x + r * .12, y - r * .02), (x - r * .1, y - r * .35)])
    hd = _C._ell_pts(x - r * .2, y - r * .45, r * .16, r * .11, 12)[:-1]
    cv.obj([hd], .5)
    cv.line([(x - r * .05, y - r * .48), (x + r * .65, y - r * .38)])
    cv.hair([(x - r * .32, y - r * .5), (x - r * .7, y - r * .55)])


def egg_dog(cv, x, y, r):
    """Parker's dog, head on its paws, curled asleep in the eye of the scroll."""
    _egg_disc(cv, x, y, r)
    body = _C._ell_pts(x + r * .05, y + r * .15, r * .72, r * .42, 24)[:-1]
    cv.obj([body], .5)
    cv.hair(_C._fill_lines(_C._Rib([(x - r * .6, y + r * .15), (x + r * .7, y + r * .15)], [r * .38, r * .38], [r * .38, r * .38]), -.3, -.95, 1.5, .1, .9, 2))
    head = _C._ell_pts(x - r * .38, y - r * .05, r * .26, r * .2, 16)[:-1]
    cv.obj([head], .5)
    cv.obj([[(x - r * .48, y - r * .2), (x - r * .3, y - r * .45), (x - r * .22, y - r * .16)]], .5)
    cv.line(_C._ell_pts(x - r * .6, y - r * .02, .5, .5, 4))
    cv.hair([(x - r * .45, y - r * .06), (x - r * .36, y - r * .04)])
    cv.hair([(x + r * .7, y + r * .1), (x + r * .55, y + r * .45), (x + r * .1, y + r * .52)])


def egg_kranok(cv, x, y, r):
    """A Thai kranok flame: three flame tongues curling up out of a lotus calyx."""
    _egg_disc(cv, x, y, r)
    for sd, L, a in ((0, 1., -_PI / 2), (-1, .7, -_PI / 2 - .55), (1, .7, -_PI / 2 + .55)):
        bx = x + sd * r * .12
        rib = _C._euler(bx, y + r * .5, a, r * L, lambda u, s_=sd or 1: s_ * 2.2 * _sm(.5, 1, u) / (r * L), 12)
        W = [r * .16 * (1 - i / 12) ** .7 + .3 for i in range(13)]
        R = _C._Rib(rib, W, W)
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.4, .05, .85))
    cv.obj([_C._ell_pts(x, y + r * .55, r * .3, r * .14, 14)[:-1]], .5)


def egg_panel(cv, x, y, r):
    """A solar panel on its rack: a grid of cells, one ray of sun."""
    _egg_disc(cv, x, y, r)
    q = [(x - r * .7, y + r * .2), (x + r * .45, y + r * .2), (x + r * .7, y - r * .35), (x - r * .45, y - r * .35)]
    cv.obj([q], .5)
    for k in range(1, 4):
        t = k / 4
        cv.hair([(q[0][0] + (q[1][0] - q[0][0]) * t, q[0][1]), (q[3][0] + (q[2][0] - q[3][0]) * t, q[3][1])])
    cv.hair([((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2), ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)])
    cv.line([(x - r * .1, y + r * .2), (x - r * .1, y + r * .65)])
    cv.line([(x - r * .4, y + r * .65), (x + r * .25, y + r * .65)])


# ---------------------------------------------------------------------------------------------
# lettering: engraved Roman capitals as strokes (no <text>)
# ---------------------------------------------------------------------------------------------

_OV = [(.5 + .5 * _m.cos(_TAU * i / 20 - _PI / 2), .5 + .5 * _m.sin(_TAU * i / 20 - _PI / 2)) for i in range(21)]
_GL = {
    "A": ([[(0, 1), (.5, 0), (1, 1)], [(.22, .62), (.78, .62)]], .85),
    "B": ([[(0, 0), (0, 1), (.7, 1), (.9, .85), (.9, .65), (.7, .5), (0, .5)], [(0, 0), (.62, 0), (.82, .12), (.82, .38), (.62, .5)]], .75),
    "C": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .85)]], .8),
    "D": ([[(0, 0), (0, 1), (.55, 1), (.92, .72), (.92, .28), (.55, 0), (0, 0)]], .8),
    "E": ([[(.85, 0), (0, 0), (0, 1), (.85, 1)], [(0, .5), (.65, .5)]], .7),
    "F": ([[(.85, 0), (0, 0), (0, 1)], [(0, .5), (.65, .5)]], .65),
    "G": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .8), (.95, .55), (.55, .55)]], .82),
    "H": ([[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .5), (1, .5)]], .8),
    "I": ([[(.5, 0), (.5, 1)]], .3),
    "J": ([[(.8, 0), (.8, .78), (.6, 1), (.2, 1), (0, .8)]], .6),
    "K": ([[(0, 0), (0, 1)], [(.9, 0), (0, .62)], [(.3, .42), (.95, 1)]], .78),
    "L": ([[(0, 0), (0, 1), (.85, 1)]], .65),
    "M": ([[(0, 1), (0, 0), (.5, .65), (1, 0), (1, 1)]], 1.),
    "N": ([[(0, 1), (0, 0), (1, 1), (1, 0)]], .82),
    "O": ([_OV], .9),
    "P": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)]], .72),
    "Q": ([_OV, [(.6, .72), (1, 1.06)]], .9),
    "R": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)], [(.45, .5), (.95, 1)]], .76),
    "S": ([[(.9, .12), (.7, 0), (.25, 0), (.05, .15), (.05, .35), (.25, .47), (.75, .53), (.95, .66), (.95, .85), (.75, 1), (.25, 1), (.05, .88)]], .7),
    "T": ([[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]], .78),
    "U": ([[(0, 0), (0, .75), (.25, 1), (.75, 1), (1, .75), (1, 0)]], .8),
    "V": ([[(0, 0), (.5, 1), (1, 0)]], .82),
    "W": ([[(0, 0), (.25, 1), (.5, .35), (.75, 1), (1, 0)]], 1.1),
    "X": ([[(0, 0), (1, 1)], [(1, 0), (0, 1)]], .8),
    "Y": ([[(0, 0), (.5, .5), (1, 0)], [(.5, .5), (.5, 1)]], .8),
    "Z": ([[(0, 0), (1, 0), (0, 1), (1, 1)]], .76),
    "0": ([[(.5 + .45 * _m.cos(_TAU * i / 20), .5 + .5 * _m.sin(_TAU * i / 20)) for i in range(21)]], .65),
    "1": ([[(.25, .2), (.55, 0), (.55, 1)], [(.25, 1), (.85, 1)]], .55),
    "2": ([[(.05, .2), (.25, 0), (.75, 0), (.95, .2), (.95, .4), (0, 1), (1, 1)]], .65),
    "3": ([[(.05, .1), (.3, 0), (.75, 0), (.95, .2), (.9, .4), (.5, .5), (.9, .6), (.95, .8), (.75, 1), (.3, 1), (.05, .9)]], .65),
    "4": ([[(.75, 1), (.75, 0), (0, .7), (1, .7)]], .65),
    "5": ([[(.9, 0), (.15, 0), (.05, .45), (.6, .4), (.95, .6), (.95, .8), (.7, 1), (.25, 1), (.05, .9)]], .65),
    "6": ([[(.85, .05), (.5, 0), (.15, .2), (.05, .6), (.15, .9), (.5, 1), (.85, .9), (.95, .7), (.8, .5), (.45, .45), (.1, .6)]], .65),
    "7": ([[(0, 0), (1, 0), (.35, 1)]], .62),
    "8": ([[(.5, .5), (.15, .38), (.1, .15), (.3, 0), (.7, 0), (.9, .15), (.85, .38), (.5, .5), (.1, .65), (.05, .85), (.3, 1), (.7, 1), (.95, .85), (.9, .65), (.5, .5)]], .65),
    "9": ([[(.9, .4), (.55, .55), (.15, .45), (.05, .25), (.2, .05), (.55, 0), (.9, .2), (.95, .5), (.8, .85), (.45, 1), (.15, .95)]], .65),
    "-": ([[(.1, .55), (.9, .55)]], .5),
    "·": ([[(.45, .5), (.55, .5)]], .35),
    ".": ([[(.45, .95), (.55, .95)]], .3),
    ",": ([[(.5, .9), (.35, 1.15)]], .3),
    ":": ([[(.5, .3), (.5, .32)], [(.5, .9), (.5, .92)]], .3),
    "'": ([[(.5, 0), (.4, .25)]], .25),
    "/": ([[(1, 0), (0, 1)]], .55),
    "&": ([[(1, 1), (.2, .35), (.25, .08), (.5, 0), (.7, .1), (.7, .3), (.1, .7), (.15, .95), (.5, 1), (.85, .7)]], .8),
    "°": ([[(.3 + .2 * _m.cos(_TAU * i / 10), .15 + .15 * _m.sin(_TAU * i / 10)) for i in range(11)]], .45),
    "%": ([[(1, 0), (0, 1)], [(.2 + .15 * _m.cos(_TAU * i / 10), .18 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)],
           [(.8 + .15 * _m.cos(_TAU * i / 10), .82 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)]], .75),
    " ": ([], .45),
}


def st_text_w(text, h, track=.32):
    t = [ch if ch in _GL else " " for ch in text.upper()]
    return sum(_GL[ch][1] * h * .78 for ch in t) + track * h * max(0, len(t) - 1)


def st_letter(text, h, centre=None, cx=0., cy=0., track=.32, sw=None, fit=None):
    """Monoline engraved capitals h tall, centred on (cx, cy) or along the polyline `centre`.
    fit shrinks the lettering to that width. -> svg path."""
    t = [ch if ch in _GL else " " for ch in text.upper()]
    if fit:
        tw = st_text_w(text, h, track)
        if tw > fit:
            h *= fit / tw
    tw = st_text_w(text, h, track)
    if centre:
        acc = [0.]
        for i in range(1, len(centre)):
            acc.append(acc[-1] + _m.dist(centre[i], centre[i - 1]))
        tot = acc[-1]

        def at(sv):
            sv = max(0., min(tot, sv))
            for i in range(1, len(acc)):
                if acc[i] >= sv:
                    f = (sv - acc[i - 1]) / max(1e-6, acc[i] - acc[i - 1])
                    p0, p1 = centre[i - 1], centre[i]
                    return p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, _m.atan2(p1[1] - p0[1], p1[0] - p0[0])
            return centre[-1][0], centre[-1][1], 0.
        pos = (tot - tw) / 2
    else:
        pos = -tw / 2
    d = []
    for ch in t:
        strokes, wf = _GL[ch]
        gw = wf * h * .78
        if centre:
            mx, my, a = at(pos + gw / 2)
        else:
            mx, my, a = cx + pos + gw / 2, cy, 0.
        ca, sa = _m.cos(a), _m.sin(a)
        for st in strokes:
            pts = []
            for gx, gy in st:
                lx, ly = (gx - .5) * gw, (gy - .5) * h
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            d.append(_C._d(pts, tol=.05))
        pos += gw + track * h
    w = sw or (1. if h >= 7 else .5)
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width="{_C._n(w)}"/>'


def st_tablet_text(tx, ty, tw, th, lines):
    """Lines of lettering in a tablet, over a dotted Or ground cut back behind each line."""
    o = [f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>']
    n = len(lines)
    lh = min(th / (n * 1.6 + .4), 11.)
    for i, ln in enumerate(lines):
        cy = ty + th * (i + .5) / n
        w = min(tw - 8, st_text_w(ln, lh) + lh * 1.4)
        o.append(f'<path d="{st_rect_d(tx + (tw - w) / 2, cy - lh * .85, w, lh * 1.7)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
        o.append(st_letter(ln, lh, cx=tx + tw / 2, cy=cy, fit=tw - 12))
    return "".join(o)


def st_doc(w, h, body):
    return _C.svg_doc(w, h, _ST_DEFS + body)
# ==== END STUDIO FRAME ==========================================================================
# ==== STUDIO LAYOUTS ============================================================================


def _in_ell(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1


def st_border(w, h, inset=3.):
    """The plate's own gold-line border and an inner row of beads, all four edges."""
    return (st_wire(st_rect_d(inset, inset, w - 2 * inset, h - 2 * inset))
            + st_beads(st_rect_d(inset + 4.5, inset + 4.5, w - 2 * inset - 9, h - 2 * inset - 9), 3.5, 1.))


def _st_clip_runs(pl, mask, x0, y0, W, H, out, step=1.5):
    """_clip_runs at a 1.5 px test step (lines are cut cleanly enough; half the work)."""
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L = _m.hypot(dx, dy)
        if L > step:
            k = int(L / step)
            for j in range(1, k + 1):
                t = j / (k + 1)
                pts.append((px + dx * t, py + dy * t))
        pts.append(q)
        px, py = q
    run = []
    for (x, y) in pts:
        xi, yi = int(x - x0), int(y - y0)
        if 0 <= xi < W and 0 <= yi < H and mask[yi][xi]:
            if len(run) > 1:
                out.append(run)
            run = []
        else:
            run.append((x, y))
    if len(run) > 1:
        out.append(run)


class StCanvas(_C.Canvas):
    """The house Canvas, emitting with a slightly coarser simplification for the fine cuts so a
    packed field of scroll stays inside the byte budget (the eye cannot see 0.15 px)."""

    def svg(self, tol_fill=.95, tol_hair=.65, tol_line=.55):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for wd, lines in strokes.items():
                for pl in lines:
                    _st_clip_runs(pl, mask, x0, y0, W, H, out[wd])
            if ow:
                for poly in polys:
                    _st_clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                _C._fill_mask(poly, mask, x0, y0, W, H)
        res = []
        pen = _C._Pen()
        for polys, _, _ in self.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="#fff" stroke="none"/>')
        for wd in (.5, 1., 1.5):
            if out[wd]:
                pen = _C._Pen()
                for pl in out[wd]:
                    if len(pl) > 2 or _m.dist(pl[0], pl[-1]) > .6:
                        pen.add(pl, False, tol_hair if wd < 1 else tol_line)
                res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_C._n(wd * 4)}"/>')
        return "".join(res)


def _scroll_layer(field, uid, x, y, w, h, egg=None, egg_gen=2):
    cv = StCanvas()
    field.draw(cv, egg, egg_gen)
    return st_clip_rect(uid, x, y, w, h, cv.svg())


def st_band(w, h, seed, hk):
    """h < 110: a carved band. An inlaid medallion holds the subject; from it a stem runs to
    either edge, the fine scroll branching off it to fill the band."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2 + hk.get("dx", 0.), h / 2
    ry = max(4., h / 2 - 8.5) if h >= 40 else max(4., h / 2 - 7.2)
    rx = min(w * .2, max(ry * 1.5, ry * hk.get("aspect", 1.7)))
    if h < 40:
        ins = 5.
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 2 < y < fy1 + 2 and not _in_ell(x, y, cx, cy, rx + 12, ry + 12)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(3.5 if h < 40 else 4.5, gh * .12), rmax=max(4.6, gh * .32), seed=seed, slack=.9)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        L = (w / 2 - rx - 14) * 1.05
        x0 = cx + sd * (rx + 9)
        a = 0. if sd > 0 else _PI
        pts = []
        n = int(L / 2)
        for i in range(n + 1):
            u = i / n
            pts.append((x0 + sd * L * u, cy + gh * .18 * _m.sin(u * _TAU * (L / (gh * 2.2)) + (0 if sd > 0 else 1.3))))
        F.stem(pts, 1.6, 1.0, leaves=False)
    F.grow(8)
    F.fill(fx0 - 4, fy0 - 2, fx1 - fx0 + 8, fy1 - fy0 + 4, 3., hk.get("max_items", 160))
    o.append(_scroll_layer(F, f"s2b{w}x{h}", 0, 0, w, h, hk.get("egg"), 1))
    o.append(st_border(w, h, 1.5 if h < 40 else 3.))
    m, fld = st_medallion(cx, cy, rx, ry)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2b{w}x{h}v", fld, hk["field"](fld, "band") + st_rim(fld, hk.get("rim", 5.))))
    return "".join(o)


def st_medium(w, h, seed, hk):
    """110-260: the medallion between two panels of fine scroll, each grown from a stem that
    sweeps out of the medallion's foot; gold-line border and beading round the plate."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2, h / 2
    shape = hk.get("shape", "oval")
    ded = 15. if hk.get("dedication") else 0.
    ry = h / 2 - ins - 6
    rx = min(w * hk.get("cw", .21), ry * hk.get("aspect", 1.45))
    if shape == "roundel":
        rx = ry
    if shape == "arch":
        rx = min(rx, ry * 1.1)
    ph = (seed % 97) * .07
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 3 < y < fy1 + 3 and not st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph) and not (ded and abs(x - cx) < 34 and y > h - ins - 2 * ded - 6)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(6., gh * .055), rmax=min(26., gh * .2), seed=seed, slack=.88)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        a0 = _PI / 2 + sd * .25 * _PI
        x0, y0 = cx + (rx + 10) * _m.cos(_PI / 2 - sd * .9), cy + (ry + 10) * _m.sin(_PI / 2 - sd * .9)
        head = 0. if sd > 0 else _PI
        L = (w / 2 - rx - 20)
        k = -sd * .9 / L
        F.stem(st_sweep(x0, y0, head + sd * .35, L * 1.05, k * 1.5, -k * 1.2), 2., 1.1)
        x1, y1 = cx + (rx + 10) * _m.cos(-_PI / 2 + sd * .9), cy + (ry + 10) * _m.sin(-_PI / 2 + sd * .9)
        F.stem(st_sweep(x1, y1, head - sd * .35, L * .8, -k * 1.5, k), 1.8, 1.)
    F.grow(10)
    F.fill(fx0 - 4, fy0 - 3, fx1 - fx0 + 8, fy1 - fy0 + 6, 4., hk.get("max_items", 260))
    o.append(_scroll_layer(F, f"s2m{w}x{h}", 0, 0, w, h, hk.get("egg"), 2))
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2m{w}x{h}v", fld, hk["field"](fld, "medium") + st_rim(fld, hk.get("rim", 9.))))
    if ded:
        o.append(st_dedication(cx, h - 3, 2 * ded))
    if hk.get("crest"):
        o.append(hk["crest"](cx, cy - ry - 2, min(14., ins + 4), "medium"))
    return "".join(o)


def st_pedestal(x, y, w, h, seed, hk, uid):
    """The base: knurled cornice, a frieze panel (gold-line border, fine scroll from the centre
    out) round a sunk tablet, a second knurled bar, beading. -> svg"""
    o = []
    kb = 6.
    o.append(_C.knurled_bar(x, y, w, kb))
    py0, py1 = y + kb + 1, y + h - kb - 5
    ph = py1 - py0
    tw, th = min(w * .5, 300.), ph - 10
    tx, ty = x + (w - tw) / 2, py0 + 5
    o.append(st_matte(st_rect_d(x, py0, w, ph)))

    def inside(px, py):
        return x + 6 < px < x + w - 6 and py0 + 2 < py < py1 - 2 and not (tx - 8 < px < tx + tw + 8)
    F = ScrollField(inside, rmin=max(4.5, ph * .16), rmax=ph * .4, seed=seed + 11, slack=.9)
    for sd in (-1, 1):
        xs = tx - 6 if sd < 0 else tx + tw + 6
        L = (w - tw) / 2 - 14
        pts = [(xs + sd * L * i / 30, py0 + ph / 2 + ph * .15 * _m.sin(i / 30 * _TAU * (L / (ph * 2)))) for i in range(31)]
        F.stem(pts, 1.4, .9, leaves=False)
    F.grow(6)
    F.fill(x + 6, py0 + 2, w - 12, ph - 4, 3., 120)
    o.append(_scroll_layer(F, uid + "p", x, py0, w, ph))
    o.append(st_wire(st_rect_d(x + 2.5, py0 + 1.5, w - 5, ph - 3)))
    o.append(f'<path d="{st_rect_d(tx - 3, ty - 3, tw + 6, th + 6)}" fill="#000"/>')
    o.append(st_beads(st_rect_d(tx - 1.5, ty - 1.5, tw + 3, th + 3), 3.5, 1.))
    o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="#fff" stroke="none"/>')
    if hk.get("tablet"):
        o.append(hk["tablet"](tx, ty, tw, th))
    elif hk.get("tablet_lines"):
        o.append(st_tablet_text(tx, ty, tw, th, hk["tablet_lines"]))
    else:
        o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>')
    o.append(_C.knurled_bar(x + 4, py1, w - 8, kb))
    o.append(st_beads(f"M{_C._n(x + 3)},{_C._n(y + h - 2.5)}h{_C._n(w - 6)}", 3.5, 1.))
    return "".join(o)


def st_tall(w, h, seed, hk):
    """> 260: the full plate. The scene in a great inlaid medallion (an arched panel on a section
    front, like the binding) over a ribbon banner and the dedication cartouche with Parker's arms
    (placeholder); fine scroll grown from a stem rising either side of the arms packs the field;
    a pedestal; under it, when tall, a frieze of the same scroll."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    ped_h = min(max(h * .13, 40), 62.)
    fz = min(max(h * .09, 30), 50.) if (h >= 440 and hk.get("frieze", True)) else 0.
    py = h - ped_h - fz - ins * (1 if fz else .6)
    shape = hk.get("shape") or ("arch" if hk.get("arch") else "oval")
    arch = shape == "arch"
    rx = w * hk.get("cw", .3)
    top = ins + 12
    bot = py - (62 if py > 300 else 46)
    ry = (bot - top) / 2
    if shape == "roundel":
        rx = ry = min(rx * 1.25, ry)
        top = bot - 2 * ry
    cx, cy = w / 2, top + ry
    ph = (seed % 97) * .07
    ay = bot + 4
    ary = min(26., (py - ay) * .4)
    arx = ary * 1.25
    aby = py - ary - 8

    def inside(x, y):
        if not (ins - 4 < x < w - ins + 4 and ins - 3 < y < py - 3):
            return False
        if st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph):
            return False
        if abs(x - cx) < rx * 1.05 + 10 and bot - 4 < y < bot + 16:
            return False
        if _in_ell(x, y, cx, aby, arx + 10, ary + 9):
            return False
        return True
    F = ScrollField(inside, rmin=hk.get("rmin", 8.), rmax=min(hk.get("rmax", 30.), w * .058), seed=seed, slack=.88)
    for sd in (-1, 1):
        x0, y0 = cx + sd * (arx + 8), aby + ary * .3
        F.stem(st_sweep(x0, y0, (0. if sd > 0 else _PI) - sd * .25, (py - ins) * .55 + w * .1,
                        -sd * .004, -sd * .022), 3., 1.6)
        F.stem(st_sweep(cx + sd * (rx * .7), ins + 4, (0. if sd > 0 else _PI) + sd * .15, w * .3, sd * .004, sd * .02), 2.6, 1.4)
    F.grow(4)
    F.fill(ins - 4, ins - 3, w - 2 * ins + 8, py - ins, 6., hk.get("max_items", 340))
    uid = f"s2t{w}x{h}"
    o.append(_scroll_layer(F, uid, 0, 0, w, py, hk.get("egg"), 2))
    if fz:
        fy0 = py + ped_h + 2
        fh = h - ins - fy0

        def inside2(x, y):
            return ins - 4 < x < w - ins + 4 and fy0 < y < fy0 + fh and abs(x - w / 2) > fh * .7
        G = ScrollField(inside2, rmin=max(4.5, fh * .15), rmax=fh * .4, seed=seed + 5, slack=.9)
        for sd in (-1, 1):
            L = w / 2 - fh * .7 - 8
            G.stem([(w / 2 + sd * (fh * .7 + L * i / 40), fy0 + fh / 2 + fh * .17 * _m.sin(i / 40 * _TAU * (L / (fh * 2.1)))) for i in range(41)],
                   1.5, 1., leaves=False)
        G.grow(6)
        G.fill(ins - 4, fy0, w - 2 * ins + 8, fh, 4., 140)
        o.append(_scroll_layer(G, uid + "f", 0, fy0, w, fh, hk.get("egg2"), 1))
        cvp = _C.Canvas()
        _C.palmette(w / 2, fy0 + 1, fh * .8, False, seed, cv=cvp)
        o.append(cvp.svg())
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(uid + "v", fld, hk["field"](fld, "tall") + st_rim(fld, hk.get("rim", 14.))))
    if hk.get("crest"):
        o.append(hk["crest"](cx, top - 3, top - 4, "tall"))
    bh = min(16., (py - bot) * .4)
    bs, centre = _C.ribbon_banner(cx, bot + 2, rx * 2.5, bh, .035, seed)
    o.append(bs)
    if hk.get("banner"):
        o.append(hk["banner"](centre, bh))
    elif hk.get("motto"):
        o.append(st_letter(hk["motto"], bh * .55, centre=centre[4:-4], fit=_m.dist(centre[4], centre[-5]) * .92))
    if hk.get("dedication"):
        o.append(st_arms(cx, aby, arx, ary))
    else:
        # not a front: a small inlaid cartouche carries the page's own device instead of the arms
        em, efl = st_medallion(cx, aby, arx * .78, ary * .78)
        o.append(em)
        o.append(f'<path d="{st_poly_d(efl)}" fill="url(#s2o)" stroke="none"/>')
        if hk.get("egg"):
            ecv = StCanvas()
            hk["egg"](ecv, cx, aby, ary * .62)
            o.append(ecv.svg())
    o.append(st_pedestal(0, py, w, ped_h, seed, hk, uid))
    return "".join(o)


def st_dissolve(poly, seed, depth=9., step=1.25):
    """Bewick's dissolving edge: white broken rings laid over the outer few px of a vignette, the
    white taking more of each ring toward the rim, so the cut lines crumble out into the paper."""
    rng = _rnd.Random(seed)
    n = int(depth / step)
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    o = []
    for k in range(n):
        f = 1 - k / n                       # 1 at the rim, toward 0 inside
        g = k * step + .4
        ring = []
        for (x, y) in poly:
            dx, dy = x - cx, y - cy
            L = _m.hypot(dx, dy) or 1
            ring.append((x - dx / L * g, y - dy / L * g))
        segs = []
        for _ in range(4):
            on = rng.uniform(1, 5) * (.3 + 1.9 * f * f)
            off = rng.uniform(3, 9) * (1.3 - f)
            segs += [on, max(.3, off)]
        da = " ".join(_C._n(v) for v in segs)
        o.append(f'<path d="{st_poly_d(ring)}" fill="none" stroke="#fff" stroke-width="{_C._n(step + .25)}" '
                 f'stroke-dasharray="{da}" stroke-dashoffset="{_C._n(rng.uniform(0, 40))}"/>')
    o.append(f'<path d="{st_poly_d(poly)}" fill="none" stroke="#fff" stroke-width="2"/>')
    return "".join(o)


def st_ragged(poly, seed, depth=7.):
    """The vignette's dissolving rim as a cut: the outline resampled finely and bitten inward by
    layered noise and sharp nicks, so the scene's lines end raggedly in the surrounding ground
    (nothing is painted over them; outside the cut the plate stays transparent)."""
    rng = _rnd.Random(seed)
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    pts = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        L = _m.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / 1.3))
        for j in range(k):
            pts.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    m = len(pts)
    ph = [rng.uniform(0, 6.3) for _ in range(4)]
    out = []
    for i, (x, y) in enumerate(pts):
        u = i / m * _TAU
        d = depth * (.45 + .2 * _m.sin(u * 7 + ph[0]) + .15 * _m.sin(u * 19 + ph[1]) + .1 * _m.sin(u * 53 + ph[2]))
        if rng.random() < .22:
            d += depth * rng.uniform(.2, .75)
        d = max(.5, d)
        dx, dy = x - cx, y - cy
        L = _m.hypot(dx, dy) or 1
        out.append((x - dx / L * d, y - dy / L * d))
    return out


def st_vignette(w, h, seed, hk):
    """The free-standing vignette: the scene itself is the plate, cut to its shape and crumbling
    out into the paper at the rim; any ornament is drawn from the subject (hk['frame'])."""
    shape = hk.get("shape", "oval")
    pad = hk.get("pad", 2.)
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - pad, h / 2 - pad
    rx = min(rx, ry * hk.get("max_aspect", 3.2))
    ph = (seed % 97) * .07
    fld = hk["shape_fn"](cx, cy, rx, ry) if hk.get("shape_fn") else st_shape_pts(shape, cx, cy, rx, ry, 0., 160, ph)
    if shape == "irregular" and not hk.get("shape_fn"):
        s = max(max(abs(q[0] - cx) / (w / 2 - pad) for q in fld), max(abs(q[1] - cy) / (h / 2 - pad) for q in fld))
        fld = [(cx + (q[0] - cx) / s, cy + (q[1] - cy) / s) for q in fld]
    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    o = []
    if hk.get("under"):
        o.append(hk["under"](cx, cy, rx, ry, fld, mode))
    rag = st_ragged(fld, seed, hk.get("dissolve", min(7., 3 + min(w, h) * .025)))
    o.append(st_clip_poly(f"s2v{w}x{h}", rag, hk["field"](fld, mode)))
    if hk.get("frame"):
        o.append(hk["frame"](cx, cy, rx, ry, fld, mode))
    if hk.get("dedication") and h >= 110:
        dh = min(30., h * .16)
        o.append(st_dedication(cx, h - 1.5, dh))
    return "".join(o)


def st_plate(w, h, seed, hk):
    base = _C.Canvas
    if hk.get("vignette"):
        return _st_plate(w, h, seed, hk)
    _C.Canvas = StCanvas
    try:
        return _st_plate(w, h, seed, hk)
    finally:
        _C.Canvas = base


def _st_plate(w, h, seed, hk):
    if hk.get("vignette"):
        body = st_vignette(w, h, seed, hk)
    elif h <= 72 and w <= 110 and hk.get("device", True):
        body = st_device(w, h, seed, hk)
    elif h < 110:
        body = st_band(w, h, seed, hk)
    elif h <= 260:
        body = st_medium(w, h, seed, hk)
    else:
        body = st_tall(w, h, seed, hk)
    return st_doc(w, h, body)
# ==== END STUDIO LAYOUTS ========================================================================


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 23
    result, record = _facts(ctx)
    phs = _moon_phase(ctx)

    def field(fld, mode):
        xs = [p[0] for p in fld]
        ys = [p[1] for p in fld]
        X0, Y0, X1, Y1 = min(xs), min(ys), max(xs), max(ys)
        if mode == "band":
            return medallion_scene((X0 + X1) / 2, (Y0 + Y1) / 2, (X1 - X0) / 2, (Y1 - Y0) / 2)
        return arena_scene(X0, Y0, X1 - X0, Y1 - Y0, seed, result)

    hk = dict(vignette=True, pad=3., max_aspect=1.9, shape="arch", shape_fn=arena_arch, frame=hoop_frame, field=field, egg=egg_pinwheel, aspect=2., cw=.25, rmin=9., rmax=30.,
              motto=result, tablet_lines=[record, "RIP CITY"])
    return st_plate(w, h, seed, hk)
