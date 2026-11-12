"""sports-04 (Portland Pilots, University of Portland men's basketball): the Bluff at night.

The Pilots play on the bluff above the Willamette, a mile upriver from the St. Johns Bridge, and a
"pilot" steers a river boat. So the house frame carries:
Short   : a frieze of volutes flowing out of a medallion holding a ship's helm whose hub is a basketball.
Medium  : a carved cartouche framing the St. Johns Bridge (Gothic towers, cables, Cathedral Park
          arches) with a basketball rising like the moon over Forest Park behind it, the river below;
          the big volutes curl round ship's helms.
Tall    : the same scene in a large cartouche; ribbon banner lettered (in paths) with the last result
          parsed from the page; pedestal tablet with the Pilots' record; a helm finial crowns the crest.
Easter egg: a great blue heron from Sauvie Island (just downriver of the bridge) wading in the shallows
          (in the short band, perched in the medallion's lower rim).
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
    rec = re.search(r"Pilots\s+(\d+)\s*[-–]\s*(\d+)", s)
    result = f"{res.group(1)} {res.group(2)}-{res.group(3)}" if res else "GO PILOTS"
    record = f"PILOTS {rec.group(1)}-{rec.group(2)}" if rec else "PILOTS"
    return result, record


def _poly_rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ------------------------------------------------------------------------------------------------
# the ship's helm (the Pilot's wheel), hub a basketball
# ------------------------------------------------------------------------------------------------

def helm(cv, cx, cy, r, rot=0., hub_ball=True):
    n = 8
    ro, ri = r * .74, r * .6
    kw = max(1.2, r * .055)
    # spokes with turned handles past the rim
    for i in range(n):
        a = rot + TAU * i / n
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa, ca
        r0, r1 = r * .2, r * .98
        prof = [(r0, kw * 1.1), (ri, kw), (ro, kw), (r * .8, kw * .8), (r * .84, kw * 1.5), (r * .9, kw * 1.25),
                (r * .95, kw * 1.4), (r1, kw * .6)]
        left = [(cx + ca * s + nx * w, cy + sa * s + ny * w) for s, w in prof]
        right = [(cx + ca * s - nx * w, cy + sa * s - ny * w) for s, w in prof]
        cv.obj([left + right[::-1]], 1.)
        cv.hair([(cx + ca * s - nx * w * .45, cy + sa * s - ny * w * .45) for s, w in prof])
    # rim: an annulus, ruled dark on its shadow half
    out = _ell_pts(cx, cy, ro, ro, 64)[:-1]
    inn = _ell_pts(cx, cy, ri, ri, 64)[:-1]
    cv.obj([out + [out[0]] + inn[::-1] + [inn[-1]]], 1.)
    lines = []
    m = 64
    for k in range(1, 4):
        rr = ri + (ro - ri) * k / 4
        pts = [(cx + rr * math.cos(TAU * i / m), cy + rr * math.sin(TAU * i / m)) for i in range(m + 1)]
        keep = [math.cos(TAU * i / m - .8) > (-.2 if k == 2 else .25) for i in range(m + 1)]
        lines += _runs(pts, keep)
    cv.hair(lines)
    cv.line(_ell_pts(cx, cy, ri, ri, 64))
    # hub
    hr = r * .26
    if hub_ball:
        cv.obj([_ell_pts(cx, cy, hr + 1.5, hr + 1.5, 32)[:-1]], 1.)
        ball(cv, cx, cy, hr, spin=.4)
    else:
        hub = _ell_pts(cx, cy, hr, hr, 32)[:-1]
        cv.obj([hub], 1.)
        cv.hair(hatch_poly(hub, 45, 1.5))


# ------------------------------------------------------------------------------------------------
# the heron (Easter egg): drawn as a black silhouette with a white halo
# ------------------------------------------------------------------------------------------------

def heron_svg(x, y, s, flip=False):
    """Standing great blue heron, feet at (x, y), s = height in px."""
    k = s / 30.
    f = -1 if flip else 1
    P = lambda px, py: (x + f * px * k, y - py * k)
    body = [P(-1, 13), P(3, 16.5), P(6, 17.5), P(7.5, 18.5), P(7.2, 21), P(6.4, 24.5), P(7, 27.5), P(9, 29),
            P(11, 28.6), P(15.5, 28.2), P(11, 27.6), P(9.5, 27), P(8.6, 24.5), P(9.4, 21), P(9.2, 18), P(7.5, 15),
            P(3, 12), P(-4, 11), P(-8, 12.5)]
    legs = [[P(1.5, 12.5), P(1, 6), P(.5, 0)], [P(3, 12.5), P(4, 6), P(3.5, 0)],
            [P(.5, 0), P(-2, 0)], [P(.5, 0), P(2.5, 0)], [P(3.5, 0), P(6, 0)]]
    plume = [P(8, 28.5), P(4, 30), P(1, 30.5)]
    bd = _d(body + [body[0]], True, 0)
    ld = "".join(_d(l, tol=0) for l in legs) + _d(plume, tol=0)
    return (f'<path d="{bd}" fill="#fff" stroke="#fff" stroke-width="3"/><path d="{ld}" stroke="#fff" stroke-width="3" fill="none"/>'
            f'<path d="{bd}" fill="#000"/><path d="{ld}" stroke="#000" stroke-width="{_n(max(.5, min(1., s * .03)))}" fill="none"/>'
            f'<path d="{_d([P(8.2, 28), P(9.6, 28.3)], tol=0)}" stroke="#fff" stroke-width=".5"/>')


# ------------------------------------------------------------------------------------------------
# the vignette: the St. Johns Bridge at night, a basketball rising over Forest Park
# ------------------------------------------------------------------------------------------------

def bridge_scene(X, Y, W, H, seed=0, eggs=True):
    cv = Canvas()
    rng = random.Random(seed)
    cx = X + W / 2
    yw = Y + H * .7          # waterline
    yd = Y + H * .5          # deck
    bot = Y + H + 2
    # sky, ruled; slightly closer near the top
    cv.obj([_poly_rect(X - 2, Y - 2, X + W + 2, yw + 1)], 0)
    y = Y - 1.
    while y < yw + 1:
        cv.hair([(X - 2, y), (X + W + 2, y)])
        y += 2.
    # the ball rising like the moon, with a glory of rays
    br = min(W * .15, H * .19)
    bx, by = cx + W * .02, Y + H * .27
    gr = br * 1.75
    glory = _ell_pts(bx, by, gr, gr, 64)[:-1]
    cv.obj([glory], 0)
    rays = []
    nr = 56
    for i in range(nr):
        a = TAU * i / nr
        r1 = gr * (1. if i % 2 else .82)
        rays.append([(bx + br * 1.12 * math.cos(a), by + br * 1.12 * math.sin(a)), (bx + r1 * math.cos(a), by + r1 * math.sin(a))])
    cv.hair(rays)
    rings = []
    for rr in (br * 1.3, br * 1.5):
        rings.append(_ell_pts(bx, by, rr, rr, 64))
    cv.hair(_dashes(rings[0], 1.5, 2.) + _dashes(rings[1], 1., 3.))
    ball(cv, bx, by, br, spin=.3)
    # stars: tiny white knock-outs
    for _ in range(int(W * H / 1800)):
        sx, sy = X + rng.uniform(.03, .97) * W, Y + rng.uniform(.03, .35) * H
        if math.hypot(sx - bx, sy - by) > gr + 3:
            cv.obj([_ell_pts(sx, sy, 1.2, 1.2, 8)[:-1]], 0)
    # Forest Park ridge behind, dark, a fringe of firs
    def ridge(x):
        u = (x - X) / W
        return Y + H * (.44 + .06 * math.sin(u * 5.3 + .4) + .025 * math.sin(u * 13 + 1.) - .05 * (1 - u))
    hill = [(X - 2, yw + 1)]
    x = X - 2
    while x < X + W + 2:
        b = ridge(x)
        t = rng.uniform(.4, 1.)
        hill += [(x + .3, b), (x + 1.5, b - H * .03 * t), (x + 2.7, b)]
        x += 2.7
    hill += [(X + W + 2, yw + 1)]
    cv.obj([hill], .5)
    cv.hair(hatch_poly(hill, 90, 1.5))
    cv.hair(hatch_poly(hill, 0, 2, .5))
    # lights of houses along the far shore: tiny knock-outs
    for _ in range(int(W / 14)):
        lx = X + rng.uniform(.02, .98) * W
        ly = yw - rng.uniform(.01, .05) * H
        cv.obj([_poly_rect(lx, ly, lx + 1.4, ly + 1.2)], 0)
    # river: wavy lines, broken by the ball's reflection
    cv.obj([_poly_rect(X - 2, yw, X + W + 2, bot)], 0)
    y = yw + 1.
    j = 0
    while y < bot:
        segs = []
        x = X - 2
        while x < X + W + 2:
            L = rng.uniform(8, 30)
            pts = [(x + t, y + .5 * math.sin((x + t) * .35 + j)) for t in range(0, int(L) + 1, 2)]
            refl = abs(x + L / 2 - bx) < br * (.9 - .3 * (y - yw) / H) and rng.random() < .55
            if not refl and len(pts) > 1:
                segs.append(pts)
            x += L + rng.uniform(.8, 1.6)
        cv.hair(segs)
        y += 1.5
        j += 1
    # glints in the reflection
    gl = []
    for i in range(int(H * .12)):
        gy = yw + 2 + i * 2.
        if gy > bot:
            break
        w_ = br * (.5 + rng.random() * .4)
        gl.append([(bx - w_ * rng.random(), gy), (bx - w_ * rng.random() + 3, gy)])
    # banks: left (Linnton side) low, right (Cathedral Park) with the Gothic arches
    lb = [(X - 2, yw - H * .02), (X + W * .1, yw - H * .015), (X + W * .16, yw + H * .02), (X + W * .2, yw + H * .06),
          (X - 2, yw + H * .06)]
    cv.obj([lb], 1.)
    cv.hair(hatch_poly(lb, 30, 2))
    rbx = X + W * .78
    rb = [(rbx, yw + H * .06), (rbx + W * .05, yw + H * .01), (rbx + W * .1, yw - H * .03), (X + W + 2, yw - H * .03),
          (X + W + 2, yw + H * .06)]
    cv.obj([rb], 1.)
    cv.hair(hatch_poly(rb, -30, 2))
    # towers positions
    t1, t2 = cx - W * .3, cx + W * .3
    yt = Y + H * .07
    tw = max(9., W * .07)
    span = t2 - t1
    sag_bot = yd - H * .025
    # main cable (catenary-ish parabola) and suspenders
    def cab(x):
        u = (x - t1) / span
        return yt + 3 + (sag_bot - yt - 3) * (1 - (2 * u - 1) ** 2)
    def back(x, side):
        if side < 0:
            u = (t1 - x) / (t1 - X + 2)
            return yt + 3 + (yd - yt - 5) * u ** 1.2
        u = (x - t2) / (X + W + 2 - t2)
        return yt + 3 + (yd - yt - 5) * u ** 1.2
    cv.obj([], 0)
    sus = []
    x = t1 + 4
    while x < t2 - 3:
        sus.append([(x, cab(x)), (x, yd)])
        x += 3.
    for side, x0, x1 in ((-1, X - 2, t1 - 3), (1, t2 + 3, X + W + 2)):
        x = x0 + 1
        while x < x1:
            sus.append([(x, back(x, side)), (x, yd)])
            x += 3.
    cv.hair(sus)
    # the deck: a lattice truss, dark underside
    dh = max(4., H * .04)
    deck = _poly_rect(X - 2, yd, X + W + 2, yd + dh)
    cv.obj([deck], 1.)
    tr = []
    x = X - 2
    k = 0
    while x < X + W + 2:
        tr.append([(x, yd + dh - .7), (x + dh * .8, yd + 1.2)] if k % 2 else [(x, yd + 1.2), (x + dh * .8, yd + dh - .7)])
        x += dh * .8
        k += 1
    cv.hair(tr)
    cv.hair([(X - 2, yd + 1.2), (X + W + 2, yd + 1.2)])
    cv.obj([_poly_rect(X - 2, yd + dh, X + W + 2, yd + dh + 1.5)], 0)
    cv.heavy([(X - 2, yd + dh + .7), (X + W + 2, yd + dh + .7)])
    # Cathedral Park: pointed concrete arches carrying the east approach down to the bank
    ax0 = t2 + tw * 1.1
    aw = max(12., W * .06)
    d0 = yd + dh + 1.5
    x = ax0
    while x < X + W + 2:
        pw_ = aw * .2
        base = yw - H * .03
        pier = _poly_rect(x, d0, x + pw_, base + 1)
        cv.obj([pier], 1.)
        cv.hair(hatch_poly(pier, 90, 1.5))
        g = base - d0
        spring, apex = d0 + g * .62, d0 + g * .14
        ow = aw - pw_
        curve = [(x + pw_ + ow * u, spring - (spring - apex) * (1 - abs(2 * u - 1)) ** .5) for u in [i / 16 for i in range(17)]]
        spand = [(x + pw_, d0), (x + aw, d0)] + curve[::-1]
        cv.obj([spand], 1.)
        cv.hair(hatch_poly(spand, 0, 2))
        cv.hair(hatch_poly(spand, 90, 3))
        x += aw
    # piers in the water under the towers
    for tx in (t1, t2):
        pr = _poly_rect(tx - tw * .65, yd + dh + 1.5, tx + tw * .65, yw + H * .05)
        cv.obj([pr], 1.)
        cv.hair(hatch_poly(pr, 90, 2))
        cv.hair(hatch_poly(_poly_rect(tx + tw * .2, yd + dh + 1.5, tx + tw * .65, yw + H * .05), 0, 1.5))
        cv.obj([_poly_rect(tx - tw * .8, yw - 1, tx + tw * .8, yw + 2)], 1.)
    # towers: two legs, a stacked pair of Gothic arches, a pointed cap
    for tx in (t1, t2):
        lw = tw * .28
        ya = yt + tw * .9
        for sx in (-1, 1):
            x0 = tx + sx * tw / 2
            leg = [(x0, yd + dh + 1.5), (x0, ya), (x0 - sx * lw, ya), (x0 - sx * lw * .9, yd + dh + 1.5)]
            cv.obj([leg], 1.)
            cv.hair(hatch_poly(leg, 90, 3 if sx < 0 else 1.5, .3))
            if sx > 0:
                cv.hair(hatch_poly(leg, 0, 3))
        # cap with pointed spire and an arch under it
        cap = [(tx - tw / 2 - 1, ya + 1), (tx - tw / 2 - 1, yt), (tx - tw * .3, yt - tw * .2), (tx, yt - tw * .75),
               (tx + tw * .3, yt - tw * .2), (tx + tw / 2 + 1, yt), (tx + tw / 2 + 1, ya + 1)]
        arch = [(tx + tw / 2 - lw, ya + 1)] + [(tx + (tw / 2 - lw) * math.cos(PI * i / 10),
                                                  ya + 1 - tw * .45 * math.sin(PI * i / 10) ** .7 - (tw * .12 if i == 5 else 0)) for i in range(11)]
        cv.obj([cap[:-1] + arch], 1.)
        cv.hair(hatch_poly(cap, 90, 1.5, .5))
        cv.hair(hatch_poly([(tx, yt - tw * .75), (tx + tw / 2 + 1, yt), (tx + tw / 2 + 1, ya + 1), (tx, ya + 1)], 0, 2))
        # finials at the corners
        for sx in (-1, 1):
            fx = tx + sx * (tw / 2 + .5)
            cv.obj([[(fx - 1.2, yt + 1), (fx, yt - tw * .45), (fx + 1.2, yt + 1)]], .5)
        # mid strut with a pointed arch beneath
        ym = (ya + yd) / 2
        sh = tw * .25
        strut = [(tx - tw / 2 + lw * .95, ym - sh / 2), (tx + tw / 2 - lw * .95, ym - sh / 2), (tx + tw / 2 - lw * .95, ym + sh / 2)] + \
                [(tx + (tw / 2 - lw * .95) * math.cos(PI * i / 8), ym + sh / 2 + sh * 1.4 * (1 - math.sin(PI * i / 8) ** .5)) for i in range(9)]
        cv.obj([strut], 1.)
        cv.hair(hatch_poly(strut, 0, 1.5))
    # main cables over the towers
    cv.obj([], 0)
    main = [(t1 + span * i / 60, cab(t1 + span * i / 60)) for i in range(61)]
    lback = [(X - 2 + (t1 - X + 2) * i / 30, back(X - 2 + (t1 - X + 2) * i / 30, -1)) for i in range(31)]
    rback = [(t2 + (X + W + 2 - t2) * i / 30, back(t2 + (X + W + 2 - t2) * i / 30, 1)) for i in range(31)]
    for pl in (main, lback, rback):
        cv.obj([_offset(pl, 1.4) + _offset(pl, -1.4)[::-1]], 0)
        cv.heavy(pl)
    # a river tug pushing upstream: the pilot's boat
    tl = max(18., W * .13)
    tx0, ty0 = cx + W * .12, yw + H * .17
    th_ = tl * .16
    hull = [(tx0, ty0), (tx0 + tl, ty0), (tx0 + tl * 1.08, ty0 - th_ * .9), (tx0 + tl * .98, ty0 - th_), (tx0 - tl * .02, ty0 - th_)]
    cv.obj([hull], 1.)
    cv.hair(hatch_poly(hull, 0, 1.5))
    cab = _poly_rect(tx0 + tl * .18, ty0 - th_ - tl * .14, tx0 + tl * .62, ty0 - th_)
    cv.obj([cab], 1.)
    cv.hair(hatch_poly(cab, 90, 3))
    pil = _poly_rect(tx0 + tl * .3, ty0 - th_ - tl * .27, tx0 + tl * .55, ty0 - th_ - tl * .14)
    cv.obj([pil], 1.)
    cv.obj([_poly_rect(tx0 + tl * .33, ty0 - th_ - tl * .24, tx0 + tl * .52, ty0 - th_ - tl * .19)], 0)
    cv.hair(hatch_poly(_poly_rect(tx0 + tl * .33, ty0 - th_ - tl * .24, tx0 + tl * .52, ty0 - th_ - tl * .19), 0, 1.5))
    stk = _poly_rect(tx0 + tl * .66, ty0 - th_ - tl * .2, tx0 + tl * .72, ty0 - th_)
    cv.obj([stk], 1.)
    cv.hair(hatch_poly(stk, 0, 1.5))
    # wake: white-broken lines trailing behind
    cv.obj([], 0)
    cv.hair([[(tx0 - 1 - k * 3, ty0 + .5 + k * .6), (tx0 - 5 - k * 5, ty0 + .5 + k * .6)] for k in range(4)])
    cv.obj([[(tx0 - tl * .5, ty0 + .3), (tx0 + tl * 1.1, ty0 + .3), (tx0 + tl * 1.1, ty0 + 1.6), (tx0 - tl * .5, ty0 + 1.6)]], 0)
    cv.hair([(tx0 - tl * .45, ty0 + 1.2), (tx0 + tl * 1.05, ty0 + 1.2)])
    # the heron, wading off the Linnton bank
    out = cv.svg()
    if eggs:
        out += heron_svg(X + W * .2, yw + H * .12, max(12., H * .12), flip=False)
    return out


def medallion_scene(cx, cy, rx, ry):
    cv = Canvas()
    field = _ell_pts(cx, cy, rx, ry, 64)[:-1]
    cv.obj([field], 0)
    cv.hair(hatch_poly(field, 0, 2))
    rr = min(rx, ry)
    helm(cv, cx, cy, rr * 1.02, rot=PI / 8)
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# layouts (adapted from the house frame so the whole field is engraved)
# ------------------------------------------------------------------------------------------------

def _pair_unit(cv, cx, cy, r, side, rng, a_out=0., turns=1.4, tail=.9, up=True, fronds=3, helm_eye=False):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    C._volute(cv, cx, cy, r, a0, turns, flip, rng, tail, -.5 if up else .5, r * .15, fronds)
    if helm_eye:
        helm(cv, cx, cy, r * .3, rot=side * .3, hub_ball=True)


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
    o.append(_clip(_uid("pb", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    uid = _uid("pm", w, h, seed)
    ell = _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(f'<clipPath id="{uid}"><path d="{ell}"/></clipPath><g clip-path="url(#{uid})">'
             + medallion_scene(cx, cy, rx - 2, ry - 2) + "</g>")
    # the heron perched on the medallion's rim, lower left
    hs = max(10., gh * .3)
    o.append(heron_svg(cx - rx * .62, cy + ry * .72, hs, flip=True))
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
    cw = min(w * .44, gh * 1.6)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = Canvas(), Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True, helm_eye=r > 36)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("pmm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_fill(cx, cy, cw, ch, inner_d,
                         lambda X, Y, W, H: bridge_scene(X, Y, W, H, seed, eggs=H > 70), _uid("pmf", w, h, seed)))
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
    cw, ch = pw * .52, ph * .68
    cx, cy = w / 2, py0 + ph * .47
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = Canvas(), Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True, helm_eye=True)
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
    o.append(_clip(_uid("ptt", w, h, seed), px0, py0, pw, ph, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_fill(cx, cy, cw, ch, inner_d,
                         lambda X, Y, W, H: bridge_scene(X, Y, W, H, seed), _uid("ptf", w, h, seed)))
    o.append(C.egg_and_dart(0, 0, w, em))
    # crest: a palmette carrying a helm finial, breaking up through the top moulding
    psz = min(ch * .16 + 8, 50)
    pal_y = cy - ch / 2 + 6
    o.append(C.palmette(cx, pal_y, psz, True, rng.randrange(1 << 20)))
    fr = max(7., psz * .32)
    fy_ = max(fr + 1., pal_y - psz * 1.0 - fr * .1)
    fcv = Canvas()
    helm(fcv, cx, fy_, fr, rot=PI / 8)
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
        o.append(_clip(_uid("ptb", w, h, seed), 0, fy, w, fh - 2,
                       C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) % 997 + 41
    if h < 110:
        body = layout_band(w, h, seed)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx)
    else:
        body = layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
