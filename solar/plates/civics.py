"""Civics plate: the Oregon State Capitol (marble drum, the gilded Pioneer on top) under a glory of
rays, the Stars and Stripes on the mall, a county ballot drop box in the foreground with a ballot
going in, marked with an X of crossed drumsticks (Parker's Easter egg). Framed in the house
acanthus; banner lettered WE THE PEOPLE, pedestal tablet lettered with Parker's districts."""
import sys
import math
import random
import re
import engraving_codex as C

_n, _d, PI, TAU = C._n, C._d, C.PI, C.TAU
hatch = C.hatch_poly


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circ(cx, cy, r, n=28, bump=0., k=9, ph=0.):
    return [(cx + r * (1 + bump * math.sin(k * t + ph)) * math.cos(t),
             cy + r * (1 + bump * math.sin(k * t + ph)) * math.sin(t))
            for t in [TAU * i / n for i in range(n)]]


def hz(poly, pitch=2.):
    """horizontal hatch on the device grid"""
    return hatch(poly, 0, pitch, .25)


def vt(poly, pitch=2.):
    return hatch(poly, 90, pitch, .25)


def solid(cv, poly, outline=1.):
    cv.obj([poly], outline)
    cv.line(hatch(poly, 0, .8))


def _seg_circle(a, b, cx, cy, r):
    dx, dy = b[0] - a[0], b[1] - a[1]
    fx, fy = a[0] - cx, a[1] - cy
    A = dx * dx + dy * dy
    B = 2 * (fx * dx + fy * dy)
    Cc = fx * fx + fy * fy - r * r
    disc = B * B - 4 * A * Cc
    if A < 1e-9 or disc <= 0:
        return None
    s = math.sqrt(disc)
    return (-B - s) / (2 * A), (-B + s) / (2 * A), dx, dy


def _cut(segs, cx, cy, r):
    """remove the parts of 2-point segments inside circle (cx, cy, r)"""
    out = []
    for (a, b) in segs:
        q = _seg_circle(a, b, cx, cy, r)
        if q is None:
            out.append([a, b])
            continue
        t0, t1, dx, dy = q
        if t0 > 0:
            t = min(1, t0)
            out.append([a, (a[0] + dx * t, a[1] + dy * t)])
        if t1 < 1:
            t = max(0, t1)
            out.append([(a[0] + dx * t, a[1] + dy * t), b])
    return [p for p in out if math.hypot(p[1][0] - p[0][0], p[1][1] - p[0][1]) > .6]


def _keep_in(segs, cx, cy, r):
    """keep only the parts of segments inside circle"""
    out = []
    for (a, b) in segs:
        q = _seg_circle(a, b, cx, cy, r)
        if q is None:
            continue
        t0, t1, dx, dy = q
        t0, t1 = max(0, t0), min(1, t1)
        if t1 - t0 > 1e-3:
            out.append([(a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)])
    return out


# ----------------------------------------------------------------------------------------------
# stroke lettering (roman capitals as paths; no <text>)
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_G = {
    "A": (.72, [[(0, 1), (.36, 0), (.72, 1)], [(.15, .64), (.57, .64)]]),
    "B": (.6, [[(0, 0), (0, 1), (.38, 1)] + _arc(.38, .76, .22, .24, 90, -90, 6) + [(0, .52)],
               [(0, 0), (.33, 0)] + _arc(.33, .26, .2, .26, -90, 90, 6)[1:] + [(0, .52)]]),
    "C": (.66, [_arc(.36, .5, .34, .5, -45, -315, 12)]),
    "D": (.68, [[(0, 0), (0, 1), (.3, 1)] + _arc(.3, .5, .36, .5, 90, -90, 10) + [(0, 0)]]),
    "E": (.56, [[(.54, 0), (0, 0), (0, 1), (.54, 1)], [(0, .5), (.42, .5)]]),
    "F": (.54, [[(.54, 0), (0, 0), (0, 1)], [(0, .5), (.42, .5)]]),
    "G": (.7, [_arc(.36, .5, .34, .5, -45, -315, 12) + [(.7, .58), (.42, .58)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    "I": (.08, [[(.04, 0), (.04, 1)]]),
    "J": (.46, [[(.44, 0), (.44, .74)] + _arc(.22, .74, .22, .26, 0, 180, 6)[1:]]),
    "K": (.62, [[(0, 0), (0, 1)], [(.6, 0), (0, .6)], [(.2, .45), (.62, 1)]]),
    "L": (.52, [[(0, 0), (0, 1), (.52, 1)]]),
    "M": (.84, [[(0, 1), (0, 0), (.42, .8), (.84, 0), (.84, 1)]]),
    "N": (.68, [[(0, 1), (0, 0), (.68, 1), (.68, 0)]]),
    "O": (.76, [_arc(.38, .5, .38, .5, 0, 360, 16)]),
    "P": (.58, [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)]]),
    "Q": (.76, [_arc(.38, .5, .38, .5, 0, 360, 16), [(.45, .7), (.78, 1.04)]]),
    "R": (.62, [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)],
                [(.28, .54), (.62, 1)]]),
    "S": (.56, [_arc(.28, .25, .26, .25, -20, -270, 7) + _arc(.28, .75, .28, .25, -90, 160, 7)[1:]]),
    "T": (.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "U": (.66, [[(0, 0), (0, .66)] + _arc(.33, .66, .33, .34, 180, 0, 8)[1:] + [(.66, 0)]]),
    "V": (.7, [[(0, 0), (.35, 1), (.7, 0)]]),
    "W": (.96, [[(0, 0), (.24, 1), (.48, .2), (.72, 1), (.96, 0)]]),
    "X": (.64, [[(0, 0), (.64, 1)], [(.64, 0), (0, 1)]]),
    "Y": (.66, [[(0, 0), (.33, .5), (.66, 0)], [(.33, .5), (.33, 1)]]),
    "Z": (.6, [[(0, 0), (.6, 0), (0, 1), (.6, 1)]]),
    "0": (.54, [_arc(.27, .5, .27, .5, 0, 360, 14)]),
    "1": (.36, [[(.04, .2), (.26, 0), (.26, 1)], [(.04, 1), (.48, 1)]]),
    "2": (.54, [_arc(.27, .27, .26, .27, -170, 10, 6) + [(0, 1), (.54, 1)]]),
    "3": (.52, [_arc(.25, .25, .25, .25, -160, 90, 6), _arc(.25, .74, .27, .26, -90, 160, 6)]),
    "4": (.58, [[(.42, 1), (.42, 0), (0, .7), (.58, .7)]]),
    "5": (.54, [[(.5, 0), (.08, 0), (.04, .44)] + _arc(.26, .7, .28, .3, -120, 150, 8)]),
    "6": (.56, [[(.46, .02), (.2, .2), (.02, .65)] + _arc(.28, .7, .26, .3, 180, 540, 12)]),
    "7": (.54, [[(0, 0), (.54, 0), (.2, 1)]]),
    "8": (.54, [_arc(.27, .25, .22, .25, 90, 450, 10), _arc(.27, .74, .27, .26, -90, 270, 12)]),
    "9": (.56, [_arc(.28, .3, .26, .3, 0, 360, 12) + [(.54, .35), (.36, .8), (.1, .98)]]),
    "-": (.4, [[(.04, .55), (.36, .55)]]),
    ".": (.2, [[(.1, .92), (.1, .96)]]),
    "·": (.36, [[(.18, .4), (.26, .51), (.18, .62), (.1, .51), (.18, .4), (.18, .62)]]),
}


def text_width(s, cap):
    return sum((_G.get(ch, (.5, []))[0] + .32) * cap if ch != " " else .5 * cap for ch in s) - .32 * cap


def _along(P, s, off):
    acc = 0.
    for i in range(1, len(P)):
        L = math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1])
        if acc + L >= s or i == len(P) - 1:
            t = (s - acc) / L if L else 0
            x = P[i - 1][0] + (P[i][0] - P[i - 1][0]) * t
            y = P[i - 1][1] + (P[i][1] - P[i - 1][1]) * t
            nx, ny = -(P[i][1] - P[i - 1][1]) / L, (P[i][0] - P[i - 1][0]) / L
            return (x + nx * off, y + ny * off)
        acc += L
    return P[-1]


def _plen(P):
    return sum(math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]) for i in range(1, len(P)))


def letter(s, x, y, cap, path_pts=None):
    """Polylines for string s, cap height `cap`, from x with the cap top at y. path_pts: a centre
    polyline; x is then arc length along it and y the offset across it."""
    out = []
    cur = x
    for ch in s.upper():
        if ch == " ":
            cur += .5 * cap
            continue
        gw, strokes = _G.get(ch, _G["·"])
        for st in strokes:
            pts = [(cur + px * cap, y + py * cap) for px, py in st]
            if path_pts:
                pts = [_along(path_pts, px, py) for px, py in pts]
            out.append(pts)
        cur += (gw + .32) * cap
    return out


def serif_lines(lines, cap):
    out = []
    k = cap * .14
    for pl in lines:
        for a, b in ((pl[0], pl[1]), (pl[-1], pl[-2])):
            if abs(a[0] - b[0]) < .25 * abs(a[1] - b[1]):
                out.append([(a[0] - k, a[1]), (a[0] + k, a[1])])
    return out


def lettering_svg(lines, w=1.):
    d = "".join(_d(p, tol=.05) for p in lines)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w)}"/>'


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def tree(cv, cx, cy, r, seed):
    rng = random.Random(seed)
    blobs = []
    for i in range(5):
        a = rng.uniform(0, TAU)
        d = r * rng.uniform(.15, .45)
        blobs.append((cx + d * math.cos(a), cy + d * math.sin(a) * .8, r * rng.uniform(.5, .66)))
    blobs.sort(key=lambda b: b[1])
    tr = rect(cx - r * .08, cy, cx + r * .08, cy + r * 1.1)
    cv.obj([tr], 1.)
    cv.hair(vt(tr, 1.5))
    for bx, by, br in blobs:
        poly = circ(bx, by, br, 30, .07, 11, rng.uniform(0, 6))
        cv.obj([poly], 1.)
        cv.hair(_cut(hatch(poly, 45, 3., 0), bx - br * .35, by - br * .35, br * .45))
        cv.hair(_cut(hatch(poly, 45, 3., 1.5), bx - br * .25, by - br * .25, br * .95))
        cv.hair(_cut(hatch(poly, -45, 3., .75), bx - br * .15, by - br * .15, br * .98))
        for j in range(7):
            t = PI + .3 + j * .35
            px, py = bx + br * .78 * math.cos(t), by + br * .78 * math.sin(t)
            cv.hair([(px, py), (px + br * .14 * math.cos(t + 1.9), py + br * .14 * math.sin(t + 1.9))])


def capitol(cv, cx, G, S, detail):
    """Oregon State Capitol on ground line G, wing span S."""
    wh = .13 * S
    for side in (-1, 1):
        x0, x1 = (cx - S / 2, cx - .16 * S) if side < 0 else (cx + .16 * S, cx + S / 2)
        face = rect(x0, G - wh, x1, G)
        cv.obj([face], 1.)
        cv.hair(hz(face, 3.))
        if side > 0:
            ret = rect(x1 - .03 * S, G - wh, x1, G)
            cv.obj([ret], 1.)
            cv.hair(hz(ret, 1.5))
        n = max(3, int((x1 - x0) / (S * .035)))
        for row in (.3, .68):
            for i in range(n):
                wx = x0 + (x1 - x0) * (i + .5) / n
                if side > 0 and wx > x1 - .035 * S:
                    continue
                cv.heavy([(wx, G - wh * (row + .14)), (wx, G - wh * (row - .14))])
        cv.line([(x0, G - wh + 1.2), (x1, G - wh + 1.2)])
    bw, bh = .36 * S, .27 * S
    bx0, bx1, by0 = cx - bw / 2, cx + bw / 2, G - bh
    blk = rect(bx0, by0, bx1, G)
    cv.obj([blk], 1.)
    cv.hair(hz(rect(bx0, by0, bx1, by0 + bh * .14), 1.5))
    rec = rect(cx - bw * .3, by0 + bh * .18, cx + bw * .3, G)
    cv.obj([rec], 1.)
    cv.hair(vt(rec, 1.5))
    if detail:
        cv.hair(hz(rec, 3.))
    for i in range(5):
        px = cx - bw * .3 + bw * .6 * (i + .5) / 5
        cv.obj([rect(px - .8, by0 + bh * .18, px + .8, G)], .5)
    pl = rect(bx0, by0 + bh * .14, cx - bw * .3, G)
    pr = rect(cx + bw * .3, by0 + bh * .14, bx1, G)
    cv.obj([pl], 1.)
    cv.hair(vt(pl, 3.))
    cv.obj([pr], 1.)
    cv.hair(vt(pr, 1.5))
    cv.heavy([(bx0 - 1, by0), (bx1 + 1, by0)])
    r = .085 * S
    dh = .2 * S
    dy0, dy1 = by0 - dh, by0 - S * .025
    base = rect(cx - r * 1.35, dy1, cx + r * 1.35, by0)
    cv.obj([base], 1.)
    cv.hair(hz(base, 3.))
    cv.hair(_keep_in(hz(base, 1.5), cx + r * 2.6, by0, r * 2))
    drum = rect(cx - r, dy0, cx + r, dy1)
    cv.obj([drum], 1.)
    nf = 22 if detail else 12
    for i in range(1, nf):
        th = -PI / 2 + PI * i / nf
        fx = cx + r * math.sin(th)
        (cv.line if math.sin(th) > .35 else cv.hair)([(fx, dy0 + 2), (fx, dy1)])
    cv.hair(hz(rect(cx + r * .45, dy0, cx + r, dy1), 2.))
    ring = rect(cx - r * 1.1, dy0 - S * .018, cx + r * 1.1, dy0 + 1)
    cv.obj([ring], 1.)
    cv.hair(_keep_in(hz(ring, 1.5), cx + r * 1.7, dy0, r * 1.2))
    lan = rect(cx - r * .55, dy0 - S * .05, cx + r * .55, dy0 - S * .018)
    cv.obj([lan], 1.)
    cv.hair(vt(lan, 2.))
    cv.obj([rect(cx - r * .22, dy0 - S * .065, cx + r * .22, dy0 - S * .05)], 1.)
    # the gilded Pioneer: axe on his shoulder, cloak
    u = S * .0019
    top = dy0 - S * .065
    fig = [(-6, 0), (-5, -14), (-7, -30), (-6, -46), (-9, -60), (-6, -76), (0, -82), (6, -76), (9, -60),
           (8, -46), (6, -30), (5, -14), (7, 0), (2, 0), (1, -28), (-1, -28), (-2, 0)]
    solid(cv, [(cx + px * u * 1.2, top + py * u) for px, py in fig], .5)
    solid(cv, circ(cx, top - 88 * u, 6.5 * u, 12), .5)
    cv.line([(cx - 4 * u, top - 66 * u), (cx - 20 * u, top - 104 * u)])
    solid(cv, [(cx - 20 * u, top - 104 * u), (cx - 27 * u, top - 99 * u), (cx - 22 * u, top - 93 * u)], .5)
    # steps
    sw = bw * .7
    for k in range(4 if detail else 2):
        yy = G + k * S * .012
        st = rect(cx - sw / 2 - k * S * .02, yy, cx + sw / 2 + k * S * .02, yy + S * .012)
        cv.obj([st], .5)
        if k % 2:
            cv.hair(hz(st, 3.))
    # the two marble pylon sculptures
    for side in (-1, 1):
        sx = cx + side * (sw / 2 + S * .04)
        blkp = rect(sx - S * .03, G - S * .055, sx + S * .03, G + S * .02)
        cv.obj([blkp], 1.)
        cv.hair(hatch(blkp, 45 if side > 0 else 90, 2. if side > 0 else 3., .25))
        cv.obj([rect(sx - S * .034, G - S * .062, sx + S * .034, G - S * .055)], 1.)


def flag(cv, x, y, fw, fh, phase=0.):
    pole_h = fh * 4.2
    cv.obj([rect(x - .7, y, x + .7, y + pole_h)], .5)
    cv.obj([circ(x, y - .6, 1.6, 8)], .5)

    def P(u, v):
        return (x + 1 + u * fw, y + 2 + v * fh + fh * .09 * math.sin(u * 5.2 + phase) * u)
    N = 14
    cv.obj([[P(i / N, 0) for i in range(N + 1)] + [P(1 - i / N, 1) for i in range(N + 1)]], 1.)
    for s in range(0, 7, 2):
        for q in (.25, .7):
            v = (s + q) / 7 + .02
            u0 = .42 if s < 4 else 0
            cv.line([P(u0 + (1 - u0) * i / N, v) for i in range(N + 1)])
    can = [P(i / 6 * .42, 0) for i in range(7)] + [P(.42 - i / 6 * .42, 4 / 7) for i in range(7)]
    cv.obj([can], .5)
    cv.hair(hatch(can, 45, 1.5))
    cv.hair(hatch(can, -45, 3.))


def drop_box(cv, x, y, s, egg=True):
    """county ballot drop box standing at (x, y), height s; a ballot half posted, its X made of
    crossed drumsticks."""
    w = s * .62
    for lg in (rect(x - w * .38, y - s * .1, x - w * .3, y), rect(x + w * .3, y - s * .1, x + w * .38, y)):
        solid(cv, lg, .5)
    body = rect(x - w / 2, y - s * .92, x + w / 2, y - s * .1)
    cv.obj([body], 1.)
    cv.hair(hatch(body, 45, 2.))
    cv.hair(_keep_in(hatch(body, -45, 3.), x + w, y - s * .5, w * .9))
    lid = [(x - w / 2 - 1.5, y - s * .92), (x + w / 2 + 1.5, y - s * .92), (x + w / 2 - 1, y - s), (x - w / 2 + 1, y - s)]
    cv.obj([lid], 1.)
    cv.hair(hz(lid, 1.5))
    pc = rect(x - w * .3, y - s * .6, x + w * .3, y - s * .3)
    cv.obj([pc], .5)
    for k in range(3):
        yy = y - s * .55 + k * s * .09
        cv.hair([(x - w * .22, yy), (x + w * .22, yy)])
    solid(cv, rect(x - w * .34, y - s * .84, x + w * .34, y - s * .78), .5)
    if egg:
        a = math.radians(-8)
        bw_, bh_ = w * .62, s * .5
        ox, oy = x - w * .02, y - s * .81

        def R(px, py):
            return (ox + px * math.cos(a) - py * math.sin(a), oy + px * math.sin(a) + py * math.cos(a))
        cv.obj([[R(-bw_ / 2, 0), R(bw_ / 2, 0), R(bw_ / 2, -bh_), R(-bw_ / 2, -bh_)]], 1.)
        cv.hair([R(-bw_ * .38, -bh_ * .82), R(bw_ * .38, -bh_ * .82)])
        cv.hair([R(-bw_ * .38, -bh_ * .7), R(bw_ * .1, -bh_ * .7)])
        for sx in (-1, 1):
            p0 = R(-bw_ * .05 - sx * bw_ * .3, -bh_ * .1)
            p1 = R(-bw_ * .05 + sx * bw_ * .22, -bh_ * .58)
            cv.line([p0, p1])
            solid(cv, circ(p1[0], p1[1], .9, 6), .5)


def heron(cx_, by, k, f, seed=0):
    """A great blue heron's neck rising out of the acanthus like a scroll stem, ending in the head:
    black crest plumes, eye, dagger bill; streaked throat in bulino. f = -1 faces left, +1 right.
    Base at (cx_, by); k = scale (1 ~ 60 px tall)."""
    cv = C.Canvas()

    def bez(p0, p1, p2, p3, n=24):
        out = []
        for i in range(n + 1):
            t = i / n
            a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
            out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
        return out
    P = lambda x, y: (cx_ + f * x * k, by + y * k)
    pts = bez(P(0, 0), P(26, -6), P(-6, -40), P(14, -56))
    n = len(pts)
    wl = [k * (7.5 - 4.2 * i / (n - 1)) for i in range(n)]
    R = C._Rib(pts, wl, wl)
    cv.obj([R.outline()], 1.)
    side = 1 if f > 0 else -1     # the throat (front) edge
    cv.hair(C._fill_lines(R, -side * .98, side * .2, 2., 0., 1., 4))
    cv.hair(C._fill_lines(R, side * .35, side * .98, 3., 0., 1., 2))
    C._shadow(cv, R, -side, k * 2.2, .05, .9)
    # streaked throat: short bulino flecks down the front of the neck
    for i in range(2, n - 2):
        a = R.at(i / (n - 1), side * .7)
        b = R.at((i + 1.6) / (n - 1), side * .3)
        (cv.line if i % 2 else cv.hair)([a, b])
    # head
    hx, hy = P(17, -58)
    head = [(hx + 6.2 * k * math.cos(t), hy + 4.4 * k * math.sin(t)) for t in [TAU * i / 20 for i in range(20)]]
    # bill
    bill = [P(19, -61), P(42, -55), P(19, -55.5)]
    cv.obj([bill], 1.)
    cv.hair([P(21, -58), P(40, -55.3)])
    cv.obj([head], 1.)
    cv.hair(_keep_in(hatch(head, 0, 1.5, .25), hx - f * 4 * k, hy + 5 * k, 5 * k))
    # black crown stripe and the trailing plumes
    crown = [P(10, -60), P(16, -63.2), P(22, -61.5), P(16, -60.5)]
    solid(cv, crown, .5)
    for dy, L in ((0, 16), (2, 13)):
        cv.heavy(bez(P(12, -61 + dy), P(4, -62 + dy), P(-2, -64 + dy), P(-2 - L * .3, -68 + dy * .5), 8))
    # eye
    ex, ey = P(19.5, -59.5)
    cv.obj([circ(ex, ey, 1.3 * k, 8)], .5)
    cv.line(hatch(circ(ex, ey, .8 * k, 6), 0, .8))
    # one finger of acanthus wrapping the base of the neck, so it grows from the leafwork
    C.acanthus_frond(*P(0, 4), -90 + f * 60, 26 * k, 3, 34, seed=seed, cv=cv)
    return cv.svg()


def scene(x, y, W, H, clip_d, seed, detail=True, uid="cv"):
    """everything inside the cartouche field (bbox x, y, W, H; clipped to clip_d)"""
    cv = C.Canvas()
    cx = x + W / 2
    G = y + H * (.7 if detail else .76)
    S = min(W * .9, (G - y - H * .07) / .74)
    # sky: a glory of rays from behind the drum, alternate wedges ruled
    sky = rect(x - 2, y - 2, x + W + 2, G + 1)
    cv.obj([sky], 0)
    gx, gy = cx, G - .4 * S
    nr = 40 if detail else 24
    R = max(W, H) * 1.6
    for i in range(nr):
        a0 = PI * i / nr - .01 - PI
        a1 = PI * (i + 1) / nr + .01 - PI
        wedge = [(gx, gy), (gx + R * math.cos(a0), gy + R * math.sin(a0)), (gx + R * math.cos(a1), gy + R * math.sin(a1))]
        if i % 2:
            cv.hair(hz(wedge, 1.5))
        else:
            aa = (a0 + a1) / 2
            rr0 = S * .16
            cv.hair([(gx + rr0 * math.cos(aa), gy + rr0 * math.sin(aa)), (gx + R * math.cos(aa), gy + R * math.sin(aa))])
    cv.hair(hz(rect(x - 2, gy, x + W + 2, G + 1), 2.))
    # the West Hills
    hills = [(x - 2, G + 1)] + [(x - 2 + (W + 4) * i / 30,
                                 G - H * (.06 + .025 * math.sin(i * .7 + seed % 7) + .015 * math.sin(i * 1.9)))
                                for i in range(31)] + [(x + W + 2, G + 1)]
    cv.obj([hills], .5)
    cv.hair(hatch(hills, 45, 2.))
    cv.hair(hatch(hills, -45, 3.))
    # the mall
    lawn = rect(x - 2, G, x + W + 2, y + H + 2)
    cv.obj([lawn], 0)
    cv.hair(hz(lawn, 2.))
    walk = [(cx - S * .13, G), (cx + S * .13, G), (cx + W * .33, y + H + 2), (cx - W * .33, y + H + 2)]
    cv.obj([walk], .5)
    cv.hair(hz(walk, 3.))
    for k in (-1, 1):
        for f in (.3, .65):
            cv.hair([(cx + k * S * .13 * f, G), (cx + k * W * .33 * f, y + H + 2)])
    if detail:
        flag(cv, cx - S * .33, G - S * .36, S * .15, S * .085, seed % 5)
    capitol(cv, cx, G, S, detail)
    tr = S * .1
    for side in (-1, 1):
        for k, (fx, fy, sc) in enumerate(((.62, .0, 1.), (.78, .08, 1.3), (.92, .2, 1.7))):
            if not detail and k == 0:
                continue
            tree(cv, cx + side * W * fx * .5, G + H * fy - tr * sc * .3, tr * sc, seed * 7 + k * 3 + side)
    if S * .2 >= 13:
        drop_box(cv, cx + W * .27, min(y + H * .95, G + (y + H - G) * .8), max(S * .2, 16))
    cid = C._uid("civ", uid, x, y, W, H)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ----------------------------------------------------------------------------------------------
# layouts (the house layouts, adapted: the field engraved whole, banner and tablet lettered)
# ----------------------------------------------------------------------------------------------

def _field(w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


def _tablet_text(ctx):
    head = ((ctx or {}).get("sample", "") or "").split("|")[0]
    parts = []
    for pat, fmt in ((r"([A-Z][a-z]+) County", "{} COUNTY"), (r"District (\d+)", "OR-{}"),
                     (r"Senate (\d+)", "SENATE {}"), (r"House (\d+)", "HOUSE {}")):
        m = re.search(pat, head)
        if m:
            parts.append(fmt.format(m.group(1).upper()))
    return " · ".join(parts) if parts else "VOX POPULI"


def _layout_band(w, h, seed, ctx):
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
    fr = C._ell_pts(cx, cy, rx - 2, ry - 2, 64)
    o.append(scene(cx - rx, cy - ry, 2 * rx, 2 * ry, _d(fr, True, 0), seed, False, "b"))
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
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cw, gh + 4)
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed, h >= 150, "m"))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
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
    cw, ch = pw * .46, ph * .6
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    hk = min(ch / 105., 2.1)
    for side in (-1, 1):
        o.append(heron(cx + side * (cw * .5 - 2), cy + ch * .22, hk, side, seed + side))
    o.append(c)
    a, b = _field(cw, ch)
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed, True, "t"))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.5, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    cap = bh * .5
    txt = "WE THE PEOPLE"
    L = _plen(centre)
    o.append(lettering_svg(letter(txt, (L - text_width(txt, cap)) / 2, -cap / 2, cap, centre), 1.))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw_, th_) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    t2 = _tablet_text(ctx)
    cap2 = min(th_ * .52, 9.)
    while text_width(t2, cap2) > tw_ - 16 and cap2 > 4:
        cap2 -= .5
    ln = letter(t2, tx + (tw_ - text_width(t2, cap2)) / 2 + 1, ty + (th_ - cap2) / 2 + .8, cap2)
    o.append(lettering_svg(ln + serif_lines(ln, cap2), 1.))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 17
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
