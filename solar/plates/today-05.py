"""today-05: Tickets and deadlines ("Mark the calendar").

The plate is a winter night at the Moda Center end of the calendar: inside the carved cartouche a
calendar leaf with the next deadline's date ringed in pen, an ADMIT ONE ticket tucked under it,
and a basketball (Ducks vs. Beavers, Blazers vs. Warriors) in front. Behind them are U-cut firs
from Christmas Mountain and a ZooLights string swagged across a ruled, starry sky. The ribbon reads
MARK THE CALENDAR and the pedestal tablet TICKETS AND DEADLINES. Easter egg: the ticket stub's
seat is row "P", engraved as Parker's monogram in a beaded roundel.
The ringed date follows ctx["date"]: it is the next deadline on the page, so it changes as they pass.
"""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
_n = C._n

# ----------------------------------------------------------------------------------------------
# a small engraved stroke alphabet (cap height 6 units, y down)
# ----------------------------------------------------------------------------------------------
_O = [(2 + 2 * math.cos(t * PI / 8), 3 + 3 * math.sin(t * PI / 8)) for t in range(17)]
_FONT = {
    "A": (4, [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]]),
    "B": (4, [[(0, 0), (0, 6), (3, 6), (4, 5.1), (4, 3.9), (3, 3), (0, 3)], [(0, 0), (2.7, 0), (3.6, .8), (3.6, 2.2), (2.7, 3)]]),
    "C": (4, [[(4, 1), (3, 0), (1, 0), (0, 1.3), (0, 4.7), (1, 6), (3, 6), (4, 5)]]),
    "D": (4, [[(0, 0), (0, 6), (2.3, 6), (4, 4.5), (4, 1.5), (2.3, 0), (0, 0)]]),
    "E": (3.6, [[(3.6, 0), (0, 0), (0, 6), (3.6, 6)], [(0, 3), (2.8, 3)]]),
    "H": (4, [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]]),
    "I": (0, [[(0, 0), (0, 6)]]),
    "K": (4, [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.4, 2.5), (4, 6)]]),
    "L": (3.4, [[(0, 0), (0, 6), (3.4, 6)]]),
    "M": (5, [[(0, 6), (0, 0), (2.5, 4.2), (5, 0), (5, 6)]]),
    "N": (4, [[(0, 6), (0, 0), (4, 6), (4, 0)]]),
    "O": (4, [_O]),
    "P": (4, [[(0, 6), (0, 0), (3, 0), (4, .9), (4, 2.1), (3, 3), (0, 3)]]),
    "R": (4, [[(0, 6), (0, 0), (3, 0), (4, .9), (4, 2.1), (3, 3), (0, 3)], [(2, 3), (4, 6)]]),
    "S": (4, [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 2.9), (3, 3.1), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]]),
    "T": (4, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
    "U": (4, [[(0, 0), (0, 4.8), (1, 6), (3, 6), (4, 4.8), (4, 0)]]),
    "V": (4, [[(0, 0), (2, 6), (4, 0)]]),
    "W": (5.4, [[(0, 0), (1.3, 6), (2.7, 1.5), (4.1, 6), (5.4, 0)]]),
    "Y": (4, [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]]),
    "F": (3.6, [[(3.6, 0), (0, 0), (0, 6)], [(0, 3), (2.8, 3)]]),
    "G": (4, [[(4, 1), (3, 0), (1, 0), (0, 1.3), (0, 4.7), (1, 6), (3, 6), (4, 5), (4, 3.4), (2.3, 3.4)]]),
    "J": (3.4, [[(3.4, 0), (3.4, 4.8), (2.4, 6), (1, 6), (0, 5)]]),
    "0": (3.6, [[(1.8 + 1.8 * math.cos(t * PI / 8), 3 + 3 * math.sin(t * PI / 8)) for t in range(17)]]),
    "1": (2.4, [[(.2, 1.2), (1.6, 0), (1.6, 6)], [(.2, 6), (2.4, 6)]]),
    "2": (3.6, [[(0, 1.2), (1, 0), (2.6, 0), (3.6, 1), (3.6, 2.2), (0, 6), (3.6, 6)]]),
    "3": (3.6, [[(0, .8), (1, 0), (2.6, 0), (3.5, .9), (3.5, 2), (2.6, 2.9), (1.4, 2.9)], [(2.6, 2.9), (3.6, 3.9), (3.6, 5.1), (2.6, 6), (1, 6), (0, 5.2)]]),
    "4": (3.8, [[(2.9, 6), (2.9, 0), (0, 4.3), (3.8, 4.3)]]),
    "5": (3.6, [[(3.4, 0), (.3, 0), (0, 2.8), (1, 2.4), (2.6, 2.4), (3.6, 3.4), (3.6, 5), (2.6, 6), (1, 6), (0, 5.2)]]),
    "6": (3.6, [[(3.3, .6), (2.4, 0), (1.2, 0), (0, 1.4), (0, 4.8), (1, 6), (2.6, 6), (3.6, 5), (3.6, 3.7), (2.6, 2.7), (1, 2.7), (0, 3.6)]]),
    "7": (3.6, [[(0, 0), (3.6, 0), (1.2, 6)]]),
    "8": (3.6, [[(1.8, 2.9), (.5, 2.2), (.4, .9), (1.2, 0), (2.4, 0), (3.2, .9), (3.1, 2.2), (1.8, 2.9), (.3, 3.8), (0, 5), (1, 6), (2.6, 6), (3.6, 5), (3.3, 3.8), (1.8, 2.9)]]),
    "9": (3.6, [[(3.6, 2.4), (2.6, 3.3), (1, 3.3), (0, 2.3), (0, 1), (1, 0), (2.6, 0), (3.6, 1.2), (3.6, 4.6), (2.4, 6), (1.2, 6), (.3, 5.4)]]),
    "·": (1, [[(.3, 2.8), (.7, 3.2)], [(.7, 2.8), (.3, 3.2)]]),
}


def text_lines(s, x, y, cap, track=1.6):
    """Polylines for string s, left-aligned at x, cap top at y, cap height `cap` px."""
    k = cap / 6.
    out = []
    cx = x
    for ch in s:
        if ch == " ":
            cx += 3 * k
            continue
        wd, strokes = _FONT[ch]
        for st in strokes:
            out.append([(cx + px * k, y + py * k) for px, py in st])
        cx += (wd + track) * k
    return out, cx - x - track * k


def text_width(s, cap, track=1.6):
    return text_lines(s, 0, 0, cap, track)[1]


def text_on_curve(s, centre, cap, track=1.8):
    """Letters set along a polyline (its middle), each letter rotated to the local tangent."""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    total = text_width(s, cap, track)
    k = cap / 6.
    s0 = L[-1] / 2 - total / 2
    out = []
    pos = s0
    for ch in s:
        if ch == " ":
            pos += 3 * k
            continue
        wd, strokes = _FONT[ch]
        mid = pos + wd * k / 2
        j = max(1, min(len(L) - 1, next((i for i in range(len(L)) if L[i] >= mid), len(L) - 1)))
        t = (mid - L[j - 1]) / ((L[j] - L[j - 1]) or 1)
        px = centre[j - 1][0] + (centre[j][0] - centre[j - 1][0]) * t
        py = centre[j - 1][1] + (centre[j][1] - centre[j - 1][1]) * t
        a = math.atan2(centre[j][1] - centre[j - 1][1], centre[j][0] - centre[j - 1][0])
        ca, sa = math.cos(a), math.sin(a)
        for st in strokes:
            pl = []
            for ux, uy in st:
                lx, ly = (ux - wd / 2) * k, (uy - 3) * k
                pl.append((px + lx * ca - ly * sa, py + lx * sa + ly * ca))
            out.append(pl)
        pos += (wd + track) * k
    return out


# ----------------------------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------------------------

def rot(pts, cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def rotl(pls, cx, cy, ang):
    return [rot(p, cx, cy, ang) for p in pls]


def inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            c = not c
    return c


def clip_to(pl, poly):
    """Keep the runs of polyline pl inside poly (resampled at 1 px)."""
    pts = [pl[0]]
    for q in pl[1:]:
        p = pts[-1]
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        k = max(1, int(d))
        for j in range(1, k + 1):
            pts.append((p[0] + (q[0] - p[0]) * j / k, p[1] + (q[1] - p[1]) * j / k))
    out, run = [], []
    for p in pts:
        if inside(poly, *p):
            run.append(p)
        else:
            if len(run) > 1:
                out.append(run)
            run = []
    if len(run) > 1:
        out.append(run)
    return out


def circ(cx, cy, r, n=None, a0=0., a1=2 * PI):
    n = n or max(12, int(r * 1.6))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def bands(poly, angle, pitch, keep):
    """Straight hatch in poly; keep(x, y, i) decides each line by its midpoint and index."""
    out = []
    for i, l in enumerate(C.hatch_poly(poly, angle, pitch)):
        mx, my = (l[0][0] + l[1][0]) / 2, (l[0][1] + l[1][1]) / 2
        if keep(mx, my, i):
            out.append(l)
    return out


# ----------------------------------------------------------------------------------------------
# today's date to ring: the next deadline on the page
# ----------------------------------------------------------------------------------------------
_DEADLINES = [(11, 19), (11, 20), (11, 21), (11, 27), (12, 1), (12, 3), (12, 5), (12, 6), (12, 10)]
_MON = {11: "NOV", 12: "DEC", 1: "JAN"}


def next_deadline(ctx):
    d = (ctx or {}).get("date", "") or ""
    try:
        m, day = int(d[5:7]), int(d[8:10])
    except ValueError:
        m, day = 11, 11
    for mm, dd in _DEADLINES:
        if (mm, dd) >= (m, day) and m >= 10:
            return mm, dd
    return _DEADLINES[-1]


# ----------------------------------------------------------------------------------------------
# the vignette's parts, drawn into a Canvas
# ----------------------------------------------------------------------------------------------

def star(cv, x, y, r):
    p = []
    for i in range(8):
        a = PI / 4 * i - PI / 2
        rr = r if i % 2 == 0 else r * .3
        p.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    cv.obj([p], 0)


def sky(cv, field, top, bot, seed):
    """Night sky: 1 px rules at 2 px near the top (50 %), thinning to 0.5 px rules toward the horizon."""
    cv.obj([field], 0)
    h = bot - top

    def dark(x, y, i):
        return (y - top) / h < .42

    cv.line(bands(field, 0, 2, dark))
    cv.hair(bands(field, 0, 2, lambda x, y, i: not dark(x, y, i) and ((y - top) / h < .75 or i % 3 != 2)))


def string_lights(cv, x0, x1, y, sag, n, S, rng):
    """A ZooLights swag: a wire sagging between two points, bulbs hanging from it."""
    wire = [(x0 + (x1 - x0) * i / 40, y + sag * math.sin(PI * i / 40)) for i in range(41)]
    cv.obj([], 0)
    cv.line(wire)
    for k in range(n):
        t = (k + .5) / n
        bx = x0 + (x1 - x0) * t
        by = y + sag * math.sin(PI * t)
        r = 1.5 * S + .6
        bulb = [(bx + r * .8 * math.cos(a), by + 2 * S + r * 1.25 + r * 1.25 * math.sin(a)) for a in [2 * PI * i / 14 for i in range(14)]]
        # glow: a white halo with short rays
        halo = circ(bx, by + 2 * S + r * 1.25, r * 2.2, 18)[:-1]
        cv.obj([halo], 0)
        for j in range(8):
            a = 2 * PI * j / 8 + .2
            cv.hair([(bx + r * 1.7 * math.cos(a), by + 2 * S + r * 1.25 + r * 1.9 * math.sin(a)),
                     (bx + r * 2.5 * math.cos(a), by + 2 * S + r * 1.25 + r * 2.6 * math.sin(a))])
        cv.obj([bulb], .5)
        cv.hair(C.hatch_poly(bulb, 45, 1.5) if k % 2 else [])
        cv.obj([[(bx - r * .55, by), (bx + r * .55, by), (bx + r * .55, by + 2 * S), (bx - r * .55, by + 2 * S)]], .5)
        cv.line([(bx, by), (bx, by + 2 * S)])


def fir(cv, x, base, hgt, S, rng, tiers=5):
    """A U-cut Douglas fir: tiers of drooping, toothed boughs, each shaded dark on the right and
    under its own lip, the trunk below."""
    wmax = hgt * .38
    tw = max(1.5, hgt * .035)
    trunk = [(x - tw, base - hgt * .1), (x + tw, base - hgt * .1), (x + tw * 1.3, base), (x - tw * 1.3, base)]
    cv.obj([trunk], 1)
    cv.line(C.hatch_poly(trunk, 90, 1.5))
    for t in range(tiers):
        f0 = t / tiers
        f1 = (t + 1.35) / tiers
        ytop = base - hgt + hgt * .9 * f0
        ybot = min(base - hgt * .1, base - hgt + hgt * .9 * f1)
        half = wmax * (.18 + .82 * (t + 1) / tiers)
        teeth = max(4, int(2 * half / (3.2 * S + 1.5)))
        sag = (ybot - ytop) * .1
        poly = [(x, ytop), (x + half * .55, ybot - sag * 1.6), (x + half, ybot - sag * .4)]
        for i in range(1, teeth):
            u = 1 - 2 * i / teeth
            px = x + half * u
            py = ybot - sag * (1 - abs(u)) * .3 + (2.6 * S if i % 2 else 0)
            poly.append((px, py))
        poly += [(x - half, ybot - sag * .4), (x - half * .55, ybot - sag * 1.6)]
        cv.obj([poly], 1)
        # body: 1 px rules at 45 (dark), crossed on the shadow side, a pale lit edge on the left
        dark = [(x - half * .45, ytop - 2), (x + half + 2, ytop - 2), (x + half + 2, ybot + 6 * S), (x - half * .45, ybot + 6 * S)]
        cv.line(clip_to_many(C.hatch_poly(dark, 45, 2), poly))
        cv.hair(clip_to_many(C.hatch_poly([(x + half * .1, ytop - 2), (x + half + 2, ytop - 2), (x + half + 2, ybot + 6 * S), (x + half * .1, ybot + 6 * S)], -45, 3), poly))
        lit = [(x - half - 2, ytop - 2), (x - half * .45, ytop - 2), (x - half * .45, ybot + 6 * S), (x - half - 2, ybot + 6 * S)]
        cv.hair(clip_to_many(C.hatch_poly(lit, 45, 3), poly))
        # needle sprays: short white-edged ticks along the lower edge
        for i in range(1, teeth):
            u = 1 - 2 * i / teeth
            px = x + half * u
            cv.hair([(px, ybot - 1 + (2.6 * S if i % 2 else 0)), (px - 1.2 * S, ybot - 4 * S)])
    # the star on the top
    star(cv, x, base - hgt - 1.5 * S, 3.2 * S + 1)
    cv.line(clip_to_many([[(x - 4 * S, base - hgt - 1.5 * S), (x + 4 * S, base - hgt - 1.5 * S)],
                          [(x, base - hgt - 5 * S), (x, base - hgt + 2 * S)]], circ(x, base - hgt - 1.5 * S, 6 * S)))


def clip_to_many(pls, poly):
    out = []
    for pl in pls:
        out.extend(clip_to(pl, poly))
    return out


def ground(cv, field, gy, cx, a, S):
    """Snow-dusted ground in ruled perspective, a light row of drifts along its top."""
    top = [(cx - a - 10 + i * (2 * a + 20) / 30, gy + 2.5 * S * math.sin(i * 1.3) + 1.5 * S * math.sin(i * .55)) for i in range(31)]
    poly = top + [(cx + a + 10, gy + 400), (cx - a - 10, gy + 400)]
    cv.obj([poly], 1)
    lines = C.hatch_poly(poly, 0, 2)
    keep = []
    for i, l in enumerate(lines):
        y = l[0][1]
        d = y - gy
        if d < 5 * S:
            if i % 2 == 0:
                keep.append(l)
        elif d < 12 * S or i % 2 == 0:
            keep.append(l)
    cv.hair(clip_to_many(keep, field))


def calendar(cv, cx, cy, W, H, ang, mon, day, S):
    """A torn-off calendar leaf: a dark header with binder rings, the month, the date in big
    shaded numerals ringed in pen, the page lightly ruled with a turned-up corner."""
    x0, y0 = cx - W / 2, cy - H / 2
    hd = H * .22
    sh = rot([(x0 + 3 * S, y0 + 4 * S), (x0 + W + 4 * S, y0 + 4 * S), (x0 + W + 4 * S, y0 + H + 4 * S), (x0 + 3 * S, y0 + H + 4 * S)], cx, cy, ang)
    cv.obj([sh], 0)
    cv.line(C.hatch_poly(sh, 45, 1.5))
    cr = W * .16
    page = [(x0, y0), (x0 + W, y0), (x0 + W, y0 + H - cr), (x0 + W - cr, y0 + H), (x0, y0 + H)]
    P = rot(page, cx, cy, ang)
    cv.obj([P], 1)
    # paper tone: light 45-degree rules, a clean highlight band on the left
    body = rot([(x0 + W * .1, y0 + hd), (x0 + W, y0 + hd), (x0 + W, y0 + H - cr), (x0 + W - cr, y0 + H), (x0 + W * .1, y0 + H)], cx, cy, ang)
    cv.hair(C.hatch_poly(body, 45 + math.degrees(ang), 3))
    shade = rot([(x0 + W * .8, y0 + hd), (x0 + W, y0 + hd), (x0 + W, y0 + H - cr), (x0 + W * .8, y0 + H)], cx, cy, ang)
    cv.hair(C.hatch_poly(shade, -45 + math.degrees(ang), 3))
    # the header band, nearly black, ruled 1 px at 1.5
    hb = rot([(x0, y0), (x0 + W, y0), (x0 + W, y0 + hd), (x0, y0 + hd)], cx, cy, ang)
    cv.line(C.hatch_poly(hb, math.degrees(ang), 1.5))
    cv.line([rot([(x0, y0 + hd + 1.5), (x0 + W, y0 + hd + 1.5)], cx, cy, ang)])
    # binder rings riding on the header
    for f in (.25, .75):
        rx, ry = x0 + W * f, y0 + hd * .35
        hole = rot(circ(rx, ry + hd * .2, 2 * S + .6, 12)[:-1], cx, cy, ang)
        cv.obj([hole], 1)
        ring = rot([(rx - 1.6 * S, ry + hd * .2), (rx - 1.6 * S, ry - hd * .55), (rx + 1.6 * S, ry - hd * .55), (rx + 1.6 * S, ry + hd * .2)], cx, cy, ang)
        cv.obj([ring], 1)
        cv.hair(C.hatch_poly(ring, 90 + math.degrees(ang), 1.5) [len(C.hatch_poly(ring, 90 + math.degrees(ang), 1.5)) // 2:])
    # month name: white field cut into the header so it reads
    mcap = hd * .42
    mw = text_width(mon, mcap)
    lab = rot([(cx - mw / 2 - 3, y0 + hd * .5 - mcap / 2 - 2), (cx + mw / 2 + 3, y0 + hd * .5 - mcap / 2 - 2),
               (cx + mw / 2 + 3, y0 + hd * .5 + mcap / 2 + 2), (cx - mw / 2 - 3, y0 + hd * .5 + mcap / 2 + 2)], cx, cy, ang)
    cv.obj([lab], .5)
    cv.line(rotl(text_lines(mon, cx - mw / 2, y0 + hd * .5 - mcap / 2, mcap)[0], cx, cy, ang))
    # weekday rules (a tiny week grid under the header)
    for j in range(7):
        gx = x0 + W * (.12 + .76 * j / 6)
        cv.line(rotl([[(gx - .6, y0 + hd + 4 * S), (gx + .6, y0 + hd + 4 * S)]], cx, cy, ang))
    # the date: big numerals, each stroke heavy with a fine shading line beside it
    ds = str(day)
    cap = H * .42
    dw = text_width(ds, cap, 1.2)
    dx, dy = cx - dw / 2, y0 + hd + (H - hd) * .5 - cap / 2 + 1
    tl, _ = text_lines(ds, dx, dy, cap, 1.2)
    clear = []
    for pl in tl:
        R = rot(pl, cx, cy, ang)
        clear.append(R)
    # a white bed under the numerals so the paper rules part round them
    for pl in clear:
        for i in range(len(pl) - 1):
            (ax, ay), (bx, by) = pl[i], pl[i + 1]
            L = math.hypot(bx - ax, by - ay) or 1
            nx, ny = -(by - ay) / L * 2.1, (bx - ax) / L * 2.1
            cv.obj([[(ax + nx - (bx - ax) / L * 1.5, ay + ny - (by - ay) / L * 1.5), (bx + nx + (bx - ax) / L * 1.5, by + ny + (by - ay) / L * 1.5),
                     (bx - nx + (bx - ax) / L * 1.5, by - ny + (by - ay) / L * 1.5), (ax - nx - (bx - ax) / L * 1.5, ay - ny - (by - ay) / L * 1.5)]], 0)
    cv.obj([], 0)
    for pl in clear:
        cv.heavy(pl)
        cv.heavy([(x + .9, y + .3) for x, y in pl])
        cv.hair([(x + 2.2, y + .7) for x, y in pl])
    # ringed in pen: a loose double loop that overshoots its start
    rcx, rcy = cx, dy + cap / 2
    ra, rb = dw / 2 + 6 * S, cap / 2 + 4.5 * S
    loop = [(rcx + ra * (1 + .04 * t) * math.cos(-2.2 + t), rcy + rb * (1 - .03 * t) * math.sin(-2.2 + t)) for t in [i * 2 * PI * 1.12 / 60 for i in range(61)]]
    cv.line(rot(loop, cx, cy, ang))
    # the turned-up corner
    cor = rot([(x0 + W, y0 + H - cr), (x0 + W - cr, y0 + H), (x0 + W - cr * 1.1, y0 + H - cr * 1.1)], cx, cy, ang)
    cv.obj([cor], 1)
    cv.hair(C.hatch_poly(cor, math.degrees(ang) - 45, 1.5))
    return P


def ticket(cv, cx, cy, W, H, ang, S, mon, day):
    """ADMIT ONE: a ticket with bitten corners and a perforated stub; the stub's seat letter is a
    beaded "P" roundel (Parker's monogram, the Easter egg)."""
    x0, y0 = cx - W / 2, cy - H / 2
    sx = x0 + W * .72
    nr = H * .12
    sh = rot([(x0 + 3 * S, y0 + 3.5 * S), (x0 + W + 3 * S, y0 + 3.5 * S), (x0 + W + 3 * S, y0 + H + 3.5 * S), (x0 + 3 * S, y0 + H + 3.5 * S)], cx, cy, ang)
    cv.obj([sh], 0)
    cv.line(C.hatch_poly(sh, 45, 1.5))
    out = []
    cr = H * .14
    # outline: corners bitten as quarter circles, notches at the perforation top and bottom
    out += [(x0 + cr * (1 - math.cos(a)), y0 + cr * (1 - math.sin(a))) for a in [PI / 2 * (1 - i / 6) for i in range(7)]][::-1][::-1]
    out = [(x0 + cr * math.sin(PI / 2 * i / 6), y0 + cr * math.cos(PI / 2 * i / 6)) for i in range(7)]
    out += [(sx + nr * math.cos(PI - PI * i / 8), y0 + nr * math.sin(PI - PI * i / 8)) for i in range(9)]
    out += [(x0 + W - cr * math.cos(PI / 2 * i / 6), y0 + cr * math.sin(PI / 2 * i / 6)) for i in range(7)]
    out += [(x0 + W - cr * math.sin(PI / 2 * i / 6), y0 + H - cr * math.cos(PI / 2 * i / 6)) for i in range(7)]
    out += [(sx + nr * math.cos(PI * i / 8), y0 + H - nr * math.sin(PI * i / 8)) for i in range(9)]
    out += [(x0 + cr * math.cos(PI / 2 * i / 6), y0 + H - cr * math.sin(PI / 2 * i / 6)) for i in range(7)]
    T = rot(out, cx, cy, ang)
    cv.obj([T], 1)
    deg = math.degrees(ang)
    # face: fine 45 rules; stub: vertical rules (a different paper tone)
    face = rot([(x0 + 3, y0 + 3), (sx - 2, y0 + 3), (sx - 2, y0 + H - 3), (x0 + 3, y0 + H - 3)], cx, cy, ang)
    stub = rot([(sx + 2, y0 + 3), (x0 + W - 3, y0 + 3), (x0 + W - 3, y0 + H - 3), (sx + 2, y0 + H - 3)], cx, cy, ang)
    cv.hair(C.hatch_poly(face, deg + 45, 3))
    cv.hair(C.hatch_poly(stub, deg - 45, 3))
    # inner border rules
    m = 2.2 * S + 1
    cv.hair([rot([(x0 + m, y0 + m), (sx - m, y0 + m), (sx - m, y0 + H - m), (x0 + m, y0 + H - m), (x0 + m, y0 + m)], cx, cy, ang)])
    # perforation
    k = int((H - 2 * nr) / 2.5)
    for i in range(k):
        yy = y0 + nr + 1 + i * (H - 2 * nr - 2) / max(1, k - 1)
        cv.line([rot([(sx, yy - .5), (sx, yy + .5)], cx, cy, ang)])
    # lettering on a clear bed
    cap = H * .2
    for s, yy, c in (("ADMIT", y0 + H * .2, cap), ("ONE", y0 + H * .2 + cap * 1.55, cap)):
        tw = text_width(s, c)
        fx = x0 + (sx - x0) / 2 - tw / 2
        bed = rot([(fx - 2, yy - 1.6), (fx + tw + 2, yy - 1.6), (fx + tw + 2, yy + c + 1.6), (fx - 2, yy + c + 1.6)], cx, cy, ang)
        cv.obj([bed], 0)
        cv.heavy(rotl(text_lines(s, fx, yy, c)[0], cx, cy, ang))
    # small print: the date line as dashes
    for j in range(2):
        yy = y0 + H * .8 + j * 2
        cv.hair([rot([(x0 + W * .1, yy), (sx - W * .1, yy)], cx, cy, ang)])
    # the stub: "P" roundel (egg)
    rx, ry = (sx + x0 + W) / 2, cy
    rr = min((x0 + W - sx) * .36, H * .3)
    disc = rot(circ(rx, ry, rr, 24)[:-1], cx, cy, ang)
    cv.obj([disc], 1)
    for i in range(14):
        a = 2 * PI * i / 14
        cv.line([rot([(rx + (rr - 1.6) * math.cos(a), ry + (rr - 1.6) * math.sin(a))] * 2, cx, cy, ang)[0],
                 rot([(rx + (rr - 1.6) * math.cos(a) + .4, ry + (rr - 1.6) * math.sin(a))], cx, cy, ang)[0]])
    pc = rr * 1.0
    cv.heavy(rotl(text_lines("P", rx - pc * 4 / 12, ry - pc / 2, pc)[0], cx, cy, ang))
    return T


def basketball(cv, bx, by, r, S, ang=.35):
    """The ball: lit from the upper left, seams cut as grooves, the shadow side laid in curved
    lines that follow its round, a cast shadow on the ground."""
    shadow = [(bx + r * .2 + r * 1.05 * math.cos(a), by + r * .92 + r * .22 * math.sin(a)) for a in [2 * PI * i / 30 for i in range(30)]]
    cv.obj([shadow], 0)
    cv.line(C.hatch_poly(shadow, 0, 1.5))
    disc = circ(bx, by, r, 48)[:-1]
    cv.obj([disc], 1.5)
    # shading: arcs of circles centred up-left, dense toward the lower right
    lx, ly = bx - r * .45, by - r * .5
    for k in range(40):
        rr = r * .55 + k * 1.5
        if rr > r * 2:
            break
        f = (rr - r * .55) / (r * 1.4)
        if f < .25 and k % 2:
            continue
        arc = circ(lx, ly, rr, int(rr * 1.2) + 8)
        for pl in clip_to(arc, circ(bx, by, r - .8, 40)[:-1]):
            if f > .55:
                cv.line(pl)
            else:
                cv.hair(pl)
    # seams (with a fine groove line beside each)
    ca, sa = math.cos(ang), math.sin(ang)

    def tr(u, v):
        return (bx + (u * ca - v * sa) * r, by + (u * sa + v * ca) * r)

    seams = [
        [tr(math.cos(t), .0) for t in []],
        [tr(-1 + 2 * i / 30, .05 * math.sin(PI * i / 30)) for i in range(31)],
        [tr(.04 * math.sin(PI * i / 30), -1 + 2 * i / 30) for i in range(31)],
        [tr(-.62 + .3 * math.sin(PI * i / 30), -.8 + 1.6 * i / 30) for i in range(31)],
        [tr(.62 - .3 * math.sin(PI * i / 30), -.8 + 1.6 * i / 30) for i in range(31)],
    ]
    disc_in = circ(bx, by, r - .3, 48)[:-1]
    for s in seams:
        if len(s) < 2:
            continue
        for pl in clip_to(s, disc_in):
            # a white groove bed so the shading parts round each seam
            pass
    cv.obj([], 0)
    for s in seams:
        if len(s) < 2:
            continue
        for pl in clip_to(s, disc_in):
            cv.heavy(pl)
    # pebble grain on the lit side: tiny dots
    rng = random.Random(7)
    for i in range(int(r * r * .12)):
        a = rng.uniform(0, 2 * PI)
        d = r * math.sqrt(rng.random()) * .9
        px, py = bx + d * math.cos(a), by + d * math.sin(a)
        if math.hypot(px - lx, py - ly) < r * .9:
            cv.hair([(px, py), (px + .5, py)])
    return disc


def vignette(cx, cy, a, b, ctx, mode="full"):
    """The scene inside a superellipse field of half-sizes a, b centred at (cx, cy)."""
    field = C._superellipse(cx, cy, a + 1.5, b + 1.5)
    rng = random.Random(sum(map(ord, (ctx or {}).get("date", ""))))
    mon_n, day = next_deadline(ctx)
    mon = _MON[mon_n]
    cv = C.Canvas()
    S = max(.55, min(a / 100., b / 70.))
    top, bot = cy - b, cy + b
    sky(cv, field, top, bot, rng)
    if mode == "small":
        # the medallion: ticket alone on the night sky with a few stars
        for i in range(5):
            star(cv, cx + a * (-.75 + .375 * i), cy - b * (.55 if i % 2 else .7), 1.8)
        ticket(cv, cx, cy + b * .08, min(a * 1.5, b * 3.6), min(b * 1.15, a * .65), -.06, .6, mon, day)
        return cv.svg(), field
    # stars, seeded by date
    for i in range(int(10 * S) + 6):
        sx_ = cx + a * rng.uniform(-.9, .9)
        sy_ = top + b * rng.uniform(.12, .55)
        if C._superellipse and inside(field, sx_, sy_):
            star(cv, sx_, sy_, rng.uniform(2.6, 4.2) * max(.8, S))
    gy = cy + b * .42
    # ZooLights swags
    string_lights(cv, cx - a * 1.05, cx + a * .02, top + b * .28, b * .18, 7, S, rng)
    string_lights(cv, cx - a * .02, cx + a * 1.05, top + b * .26, b * .2, 7, S, rng)
    # firs from Christmas Mountain, behind
    if b > 40:
        fir(cv, cx - a * .74, gy + 3 * S, b * 1.0, S, rng, 5)
        fir(cv, cx - a * .5, gy + 4 * S, b * .62, S, rng, 4)
        fir(cv, cx + a * .78, gy + 3 * S, b * .9, S, rng, 5)
    ground(cv, field, gy, cx, a, S)
    # the still life
    Wc, Hc = 64 * S, 78 * S
    calendar(cv, cx - a * .06, cy - b * .02, Wc, Hc, -.07, mon, day, S)
    ticket(cv, cx + a * .44, cy + b * .5, 86 * S, 34 * S, .16, S, mon, day)
    basketball(cv, cx - a * .43, cy + b * .55, 22 * S, S)
    return cv.svg(), field


def _clip_poly(cid, poly, body):
    return (f'<clipPath id="{cid}"><path d="{C._d(poly, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g>')


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, adapted: field filled edge to edge, banner and tablet lettered)
# ----------------------------------------------------------------------------------------------

def _field_of(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


def layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("b5", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    body, field = vignette(cx, cy, rx - 4.5, ry - 4.5, ctx, "small")
    fe = C._ell_pts(cx, cy, rx - 4, ry - 4, 64)[:-1]
    o.append(_clip_poly(C._uid("b5v", w, h), fe, body))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _cartouche_scene(o, cx, cy, cw, ch, seed, ctx, w, h, tag):
    c, _, _ = C.cartouche(cx, cy, cw, ch, seed)
    o.append(c)
    a, b = _field_of(cx, cy, cw, ch)
    body, field = vignette(cx, cy, a, b, ctx, "full" if b > 30 else "small")
    o.append(_clip_poly(C._uid(tag, w, h), C._superellipse(cx, cy, a, b), body))
    return a, b


def layout_medium(w, h, seed, ctx, density=1.):
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .065), rmax=r * .8,
                   max_n=int(11 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m5", w, h, seed), 0, gy0, w, gh, cv.svg()))
    _cartouche_scene(o, cx, cy, cw, gh + 4, rng.randrange(1 << 20), ctx, w, h, "m5v")
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    # the strip under the text: a bead row hung from the content, a light ruled ground below it,
    # the crest and volute tips break up through it
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    if py0 - 3.5 - 7 > 1:
        o.append(C.dark_ground((0, 7, w, py0 - 3.5 - 7), "L"))
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(11, ph * .04), rmax=r1 * .9,
                   max_n=int(8 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t5", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    _cartouche_scene(o, cx, cy, cw, ch, rng.randrange(1 << 20), ctx, w, h, "t5v")
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 56), True, rng.randrange(1 << 20)))
    bh = min(16, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(f'<path d="{"".join(C._d(p, tol=0) for p in text_on_curve("MARK THE CALENDAR", centre, bh * .46))}" stroke="#000" stroke-width="1" fill="none"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py + 3, w, ped_h - 6), "G"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # tablet: a light ruled ground lettered in the house capitals
    cap = min(th * .55, 9)
    s = "TICKETS · AND · DEADLINES"
    tl, tw2 = text_lines(s, 0, 0, cap, 2.2)
    fx, fy = tx + tw / 2 - tw2 / 2, ty + th / 2 - cap / 2 + .5
    o.append(f'<path d="M{_n(tx + 3)},{_n(ty + 3)}h{_n(tw - 5)}v{_n(th - 5)}h{_n(-tw + 5)}z" fill="{C.pat("L")}" stroke="none"/>')
    o.append(f'<path d="M{_n(fx - 4)},{_n(fy - 2)}h{_n(tw2 + 8)}v{_n(cap + 4)}h{_n(-tw2 - 8)}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{"".join(C._d([(fx + x, fy + y) for x, y in pl], tol=0) for pl in tl)}" stroke="#000" stroke-width="1" fill="none"/>')
    fy2 = py + ped_h
    fh = h - fy2
    if fh > 14:
        o.append(C.dark_ground((0, fy2, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f5", w, h, seed), 0, fy2, w, fh - 2,
                         C.scroll_band(0, fy2, w, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy2 + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    if h < 110:
        body = layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx)
    else:
        body = layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
