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
    y = Y - 1.
    while y < yh + 1:
        cv.hair([(X - 2, y), (X + W + 2, y)])
        y += 2.
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
    cv.hair(hatch_poly(field, 0, 2))
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


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) % 997 + 11
    if h < 110:
        body = layout_band(w, h, seed)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx)
    else:
        body = layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
