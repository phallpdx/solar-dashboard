"""sports-05 (Formula 1, race-weekend watch): the Las Vegas Grand Prix at night.

The page's next race is Las Vegas under the lights (Sat Nov 21) and Antonelli leads the championship
in the silver Mercedes. So the house frame carries:
Short   : a frieze of volutes flowing out of a medallion in which the silver car streaks past a
          chequered kerb under a ruled night sky.
Medium  : a carved cartouche holding the Strip at night (the Sphere, the Luxor beam, the Stratosphere,
          lit towers) with the silver car flat-out along the barrier; the big volutes roll into racing
          wheels.
Tall    : the same night scene in a large cartouche; a crest of crossed chequered flags; ribbon banner
          lettered (in paths) with the next race and date from the page; pedestal tablet with the
          championship leader and his points.
Easter egg: the chequered flags' staffs are Parker's drumsticks (bead tips, tapered shoulders); in the
          short band a tiny pair of crossed sticks sits under the medallion.
"""
import sys
import math
import random
import re
import datetime
import engraving_codex as C
from engraving_codex import Canvas, _d, _n, _ell_pts, hatch_poly, _clip, _uid

PI = math.pi
TAU = 2 * PI


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------

def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def hatch_d(poly, angle, pitch, phase=0., inset=0.):
    return "".join(_d(p, tol=0) for p in hatch_poly(poly, angle, pitch, phase, inset))


def _scan(poly, angle, pitch, phase=0.):
    return hatch_poly(poly, angle, pitch, phase)


def _keep(lines, fn, step=1.):
    """Cut straight hatch lines into runs where fn(x, y) is true."""
    out = []
    for a, b in lines:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        cur = []
        for i in range(n + 1):
            t = i / n
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if fn(*p):
                cur.append(p)
            else:
                if len(cur) > 1:
                    out.append([cur[0], cur[-1]])
                cur = []
        if len(cur) > 1:
            out.append([cur[0], cur[-1]])
    return out


def tone_hatch(cv, poly, tone, angle=0., layers=None):
    """Bulino tone: fn tone(x, y) in [0, 1] -> lines laid in up to four layers."""
    layers = layers or [(angle, 3., 0., .1, .5), (angle, 3., 1.5, .35, .5),
                        (angle, 3., 0., .58, 1.), (angle, 3., 1.5, .74, 1.), (angle, 1.5, 0., .9, 1.5)]
    for ang, pitch, ph, thr, wt in layers:
        ls = _keep(_scan(poly, ang, pitch, ph), lambda x, y, t=thr: tone(x, y) > t)
        if wt >= 1.5:
            cv.heavy(ls)
        elif wt >= 1:
            cv.line(ls)
        else:
            cv.hair(ls)


def _grow(poly, d):
    """Offset a simple polygon outward by d (vertex normals)."""
    n = len(poly)
    a = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1 if a > 0 else -1
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        nx = ny = 0.
        for (ax, ay), (bx, by) in ((p0, p1), (p1, p2)):
            l = math.hypot(bx - ax, by - ay) or 1
            nx += (by - ay) / l
            ny += -(bx - ax) / l
        l = math.hypot(nx, ny) or 1
        k = min(2.5, 2 / max(.4, l))
        out.append((p1[0] + sgn * nx / l * d * k, p1[1] + sgn * ny / l * d * k))
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


# ------------------------------------------------------------------------------------------------
# lettering in paths (house glyphs, extended)
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
    ".": (.2, [_arc(.1, .92, .06, .06, 0, 360, 6)]),
    "W": (.84, [[(0, 0), (.2, 1), (.42, .2), (.64, 1), (.84, 0)]]),
    "L": (.5, [[(.08, 0), (.08, 1), (.5, 1)]]),
    "B": (.54, [[(.08, .48)] + _arc(.32, .74, .2, .26, -90, 90, 6) + [(.08, 1), (.08, 0)] + _arc(.3, .24, .17, .24, -90, 90, 6) + [(.08, .48)]]),
    "A": (.66, [[(0, 1), (.33, 0), (.66, 1)], [(.13, .64), (.53, .64)]]),
    "Z": (.56, [[(.04, 0), (.54, 0), (.02, 1), (.54, 1)]]),
    "E": (.5, [[(.48, 0), (.08, 0), (.08, 1), (.5, 1)], [(.08, .5), (.4, .5)]]),
    "F": (.48, [[(.48, 0), (.08, 0), (.08, 1)], [(.08, .5), (.4, .5)]]),
    "R": (.56, [[(.08, 1), (.08, 0)] + _arc(.3, .25, .22, .25, -90, 90, 6) + [(.08, .5)], [(.28, .5), (.56, 1)]]),
    "S": (.52, [_arc(.27, .26, .23, .25, -20, -270, 8) + _arc(.27, .74, .25, .26, -90, 160, 8)[1:]]),
    "I": (.2, [[(.1, 0), (.1, 1)]]),
    "J": (.44, [[(.38, 0), (.38, .7)] + _arc(.2, .7, .18, .3, 0, 160, 6)[1:]]),
    "P": (.54, [[(.08, 1), (.08, 0)] + _arc(.3, .26, .22, .26, -90, 90, 6) + [(.08, .52)]]),
    "C": (.6, [_arc(.32, .5, .3, .5, -40, -320, 14)]),
    "G": (.62, [_arc(.32, .5, .3, .5, -40, -320, 14), [(.34, .56), (.6, .56), (.6, .92)]]),
    "Q": (.7, [_arc(.35, .5, .33, .5, 0, 360, 20), [(.42, .72), (.7, 1.04)]]),
    "T": (.56, [[(0, 0), (.56, 0)], [(.28, 0), (.28, 1)]]),
    "Y": (.6, [[(0, 0), (.3, .5), (.6, 0)], [(.3, .5), (.3, 1)]]),
    "V": (.62, [[(0, 0), (.31, 1), (.62, 0)]]),
    "X": (.58, [[(0, 0), (.58, 1)], [(.58, 0), (0, 1)]]),
    "O": (.7, [_arc(.35, .5, .33, .5, 0, 360, 20)]),
    "K": (.56, [[(.08, 0), (.08, 1)], [(.54, 0), (.08, .58)], [(.24, .44), (.56, 1)]]),
    "H": (.6, [[(.06, 0), (.06, 1)], [(.54, 0), (.54, 1)], [(.06, .5), (.54, .5)]]),
    "D": (.6, [[(.08, 0), (.08, 1), (.26, 1)] + _arc(.26, .5, .3, .5, 90, -90, 10)[1:] + [(.08, 0)]]),
    "N": (.6, [[(.06, 1), (.06, 0), (.54, 1), (.54, 0)]]),
    "U": (.6, [[(.06, 0), (.06, .66)] + _arc(.3, .66, .24, .34, 180, 0, 8)[1:] + [(.54, 0)]]),
    "M": (.74, [[(.04, 1), (.06, 0), (.37, .8), (.68, 0), (.7, 1)]]),
    "*": (.5, [[(.25, .2), (.25, .8)], [(.04, .35), (.46, .65)], [(.04, .65), (.46, .35)]]),
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
    return (f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_n(halo)}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(sw)}" stroke-linecap="round" stroke-linejoin="round"/>')


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

NUMBERS = {"ANTONELLI": "12", "RUSSELL": "63", "HAMILTON": "44", "LECLERC": "16", "VERSTAPPEN": "3",
           "NORRIS": "1", "PIASTRI": "81", "ALONSO": "14", "SAINZ": "55", "ALBON": "23"}
TEAMS = r"(Mercedes|Ferrari|Red Bull|McLaren|Aston Martin|Alpine|Williams|Haas|Sauber|Audi|Racing Bulls|Cadillac|RB)"


def _facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    race, when = "GRAND PRIX", ""
    m = re.search(r"([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)?) Grand Prix\s+[^,]+,\s*[^\n]*?\s(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*([A-Z][a-z]{2}) (\d+)", s)
    if m:
        race = (m.group(1) + " GRAND PRIX").upper()
        when = f"{m.group(2).upper()} {m.group(3)}"
    leader, pts, num = "", "", ""
    m = re.search(r"1\.\s+([A-Z][\w .'-]+?)\s+" + TEAMS + r"\s+(\d+)", s)
    if m:
        leader = m.group(1).split()[-1].upper()
        pts = m.group(3)
        num = NUMBERS.get(leader, "")
    return race, when, leader, pts, num


def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date)
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .76
    return (days / 29.530588) % 1.


# ------------------------------------------------------------------------------------------------
# figures: wheel, the F1 car, chequered flag on a drumstick staff
# ------------------------------------------------------------------------------------------------

def wheel(cv, cx, cy, r, rot=0., outline=1.):
    """Racing wheel in profile: grooved black rubber, a white sidewall band, spoked rim, hub nut."""
    disc = _ell_pts(cx, cy, r, r, max(24, int(r * 2.5)))[:-1]
    cv.obj([disc], outline)
    rr = r * .56
    k = r - .8
    ring = []
    while k > rr:
        if not (r * .8 < k < r * .8 + 1.2):
            ring.append(_ell_pts(cx, cy, k, k, max(20, int(k * 2.2))))
        k -= 1.5
    cv.heavy(ring)
    # rim
    rim = _ell_pts(cx, cy, rr, rr, max(20, int(rr * 2.5)))[:-1]
    cv.obj([rim], 1.)
    tone_hatch(cv, rim, lambda x, y: .2 + .9 * ((x - cx) * .5 + (y - cy) * .8) / rr, 30.)
    sp = []
    for i in range(10):
        a = rot + TAU * i / 10
        sp.append([(cx + rr * .3 * math.cos(a), cy + rr * .3 * math.sin(a)),
                   (cx + rr * .95 * math.cos(a + .12), cy + rr * .95 * math.sin(a + .12))])
    cv.line(sp) if rr > 8 else cv.hair(sp)
    hub = _ell_pts(cx, cy, max(1.5, rr * .3), max(1.5, rr * .3), 16)[:-1]
    cv.obj([hub], 1.)
    if rr > 6:
        cv.hair(hatch_poly(hub, 45, 1.5))
        cv.obj([_ell_pts(cx - rr * .08, cy - rr * .08, max(1., rr * .1), max(1., rr * .1), 10)[:-1]], 0)


BODY = [(.045, .03), (.04, .085), (.12, .10), (.26, .125), (.37, .175), (.43, .19),
        (.455, .19), (.47, .135), (.55, .126), (.62, .11), (.70, .095), (.80, .08),
        (.90, .066), (.975, .052), (.99, .044), (.94, .036), (.80, .04), (.68, .044),
        (.62, .03)]


def f1_car(cv, x0, yg, L, number="", streaks=True, sparks=True, X=None, W=None):
    """2026 car in profile, nose to the right. x0: tail end, yg: ground line, L: overall length."""
    def P(u, v):
        return (x0 + u * L, yg - v * L)

    def poly(pts):
        return [P(u, v) for u, v in pts]

    # shadow pool under the car
    sh = [P(.06 + .9 * i / 30, .004 - .018 * math.sin(PI * i / 30)) for i in range(31)]
    sh += [P(.96 - .9 * i / 30, -.012 - .006 * math.sin(PI * i / 30)) for i in range(31)]
    cv.obj([sh], 0)
    cv.heavy(_scan(sh, 0, 1.5, .2))
    # streaks of light trailing behind
    if streaks:
        rng = random.Random(int(L * 7))
        left = (X if X is not None else x0 - L) - 2
        for i in range(9):
            v = .02 + .02 * i + rng.uniform(-.005, .005)
            if v > .2:
                break
            ln = rng.uniform(.35, .9) * (x0 - left + L * .1)
            yy = yg - v * L
            st = [(x0 + L * .06, yy - .4), (x0 + L * .06 - ln, yy), (x0 + L * .06, yy + .4)]
            cv.obj([st], 0)
    # a white contour separating the car from the night
    halo_d = max(1.2, L * .007)
    cv.obj([_grow(poly([(.0, .07), (.085, .07), (.10, .215), (.005, .225)]), halo_d),
            _grow(poly(BODY), halo_d), _grow(poly([(.90, .012), (1.0, .012), (1.0, .05), (.93, .062), (.90, .045)]), halo_d)]
           + [_ell_pts(*P(u, v), wr_ + halo_d, wr_ + halo_d, 32)[:-1] for u, v, wr_ in ((.135, .072, L * .072), (.80, .068, L * .0684))], 0)
    # rear wing: endplate and two elements
    rw = poly([(.0, .07), (.085, .07), (.10, .215), (.005, .225)])
    cv.obj([rw], 1.)
    tone_hatch(cv, rw, lambda x, y: 1.05 - .3 * (yg - y) / (L * .22) - (.5 if x > x0 + L * .075 else 0), 0)
    cv.heavy([[P(-.005, .225), P(.11, .218)], [P(.0, .195), P(.10, .19)]])
    cv.line([[P(.04, .07), P(.06, .03)], [P(.07, .07), P(.09, .03)]])
    # body: engine cover, airbox, cockpit, nose
    body = poly(BODY)
    cv.obj([body], 1.5)
    top = lambda u: .19 if .37 < u < .46 else None

    def btone(x, y):
        u = (x - x0) / L
        v = (yg - y) / L
        # silhouette top at u (approx), relative depth below it
        if u < .37:
            t = .085 + (u - .04) / .33 * .09
        elif u < .47:
            t = .19
        else:
            t = .135 - (u - .47) / .52 * .09
        rel = (t - v) / max(.03, t - .03)
        dark = .22 + .8 * max(0., rel) ** 1.3
        if v < .052 and u < .66:
            dark += .55               # black floor and lower sidepod
        if .62 < u < .99 and v < .06:
            dark += .15
        return dark
    tone_hatch(cv, body, btone, 0)
    # the long white highlight running along the shoulder
    hl = poly([(.10, .093), (.26, .113), (.37, .16), (.37, .15), (.26, .104), (.10, .087)])
    cv.obj([hl], 0)
    hl2 = poly([(.48, .124), (.62, .104), (.80, .074), (.94, .058), (.94, .054), (.80, .068), (.62, .097), (.48, .117)])
    cv.obj([hl2], 0)
    # sidepod inlet and panel lines
    cv.line([[P(.40, .13), P(.45, .118), P(.47, .085), P(.43, .07)]])
    cv.hair([[P(.12, .06), P(.40, .072)], [P(.30, .095), P(.30, .05)]])
    # airbox mouth (black)
    mouth = poly([(.43, .19), (.455, .19), (.452, .165), (.432, .168)])
    cv.obj([mouth], 1.)
    cv.heavy(_scan(mouth, 90, 1.5))
    # number roundel on the engine cover
    if number:
        rcx, rcy = P(.24, .088)
        rr = L * .026
        if rr > 3:
            rd = _ell_pts(rcx, rcy, rr, rr, 24)[:-1]
            cv.obj([rd], 1.)
            sz = rr * 1.15
            tw = text_width(number, sz, .1)
            cv.line(letter(number, sz, lambda x, y: (rcx - tw / 2 + x, rcy - sz / 2 + y), .1))
    # driver: helmet with a black visor, inside the halo
    hx, hy = P(.495, .15)
    hr = L * .022
    helm = _ell_pts(hx, hy, hr, hr * .95, 20)[:-1]
    cv.obj([helm], 1.)
    tone_hatch(cv, helm, lambda x, y: .3 + .8 * ((x - hx) * -.3 + (y - hy)) / hr, 0)
    vis = [(hx + hr * .25, hy - hr * .35), (hx + hr * 1.0, hy - hr * .25), (hx + hr * .9, hy + hr * .15), (hx + hr * .3, hy + hr * .05)]
    cv.obj([vis], 0)
    cv.heavy(_scan(vis, 0, 1.5))
    # halo hoop
    cv.heavy([[P(.47, .137), P(.52, .175), P(.58, .17), P(.615, .112)]])
    cv.line([[P(.52, .175), P(.535, .135)]])
    # front wing: endplate, flaps
    fw = poly([(.90, .012), (1.0, .012), (1.0, .05), (.93, .062), (.90, .045)])
    cv.obj([fw], 1.)
    tone_hatch(cv, fw, lambda x, y: .7 + .4 * (y - (yg - .05 * L)) / (.04 * L), 0)
    cv.line([[P(.905, .03), P(.995, .036)], [P(.91, .045), P(.99, .046)]])
    # bargeboards/floor edge
    cv.heavy([[P(.33, .025), P(.66, .025)]])
    # wheels
    wr = L * .072
    wheel(cv, *P(.135, .072), wr, .3)
    wheel(cv, *P(.80, .068), wr * .95, .9)
    # sparks off the plank
    if sparks:
        rng = random.Random(int(L * 13))
        for i in range(7):
            sx, sy = P(.62 - .03 * i, .012)
            ln = L * rng.uniform(.08, .2)
            a = rng.uniform(-.12, .1)
            sp = [(sx, sy - .5), (sx - ln * math.cos(a), sy - ln * math.sin(a)), (sx, sy + .5)]
            cv.obj([sp], 0)


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


def chequered_flag(cv, bx, by, tx, ty, fw, fh, side, w_staff, nc=6, nr=4, phase=0.):
    """A drumstick staff from butt (bx, by) to tip (tx, ty); a waving chequered flag hung from
    just under the tip, flying outward to `side` (-1 left, +1 right)."""
    drumstick(cv, bx, by, tx, ty, w_staff)
    L = math.hypot(tx - bx, ty - by)
    ux, uy = (tx - bx) / L, (ty - by) / L
    ax, ay = bx + ux * L * .8, by + uy * L * .8      # top of the hoist
    # flag frame: along = horizontal-ish outward, down = back along the staff
    dx, dy = -ux, -uy

    def F(u, v):
        wave = math.sin(u * PI * 1.6 + phase) * fh * .14 * u
        sag = u * u * fh * .18
        return (ax + side * u * fw + dx * (v * fh + wave + sag) * .98,
                ay + dy * (v * fh) + wave + sag)

    outline = [F(i / 20, 0) for i in range(21)] + [F(1, j / 6) for j in range(1, 7)] + \
              [F(1 - i / 20, 1) for i in range(1, 21)] + [F(0, 1 - j / 6) for j in range(1, 6)]
    cv.obj([outline], 1.)
    for i in range(nc):
        for j in range(nr):
            cell = [F(i / nc, j / nr), F((i + 1) / nc, j / nr), F((i + 1) / nc, (j + 1) / nr), F(i / nc, (j + 1) / nr)]
            shade = math.cos((i + .5) / nc * PI * 1.6 + phase)       # fold shading
            if (i + j) % 2 == 0:
                cv.heavy(_scan(cell, 0, 1.5, .3))
            elif shade < -.2:
                cv.hair(_scan(cell, 0, 2.))
            elif shade < .4:
                cv.hair(_scan(cell, 0, 3.))
    # re-draw staff tip over the hoist so the flag hangs behind the bead
    tcx, tcy = bx + ux * L * .91, by + uy * L * .91
    tip = [(tcx + ux * L * .085 * math.cos(t) - uy * w_staff * .4 * math.sin(t),
            tcy + uy * L * .085 * math.cos(t) + ux * w_staff * .4 * math.sin(t)) for t in [TAU * i / 16 for i in range(16)]]
    cv.obj([tip], 1.)


def crossed_flags(cv, cx, cy, size):
    for s in (-1, 1):
        a = -PI / 2 + s * .5
        L = size
        bx, by = cx - math.cos(a) * L * .45, cy - math.sin(a) * L * .45
        tx, ty = cx + math.cos(a) * L * .55, cy + math.sin(a) * L * .55
        chequered_flag(cv, bx, by, tx, ty, size * .62, size * .42, s, max(2.2, size * .07), phase=s * .7)


def crossed_sticks(cv, cx, cy, size, ang=0.):
    for s in (-1, 1):
        a = ang + s * .62 - PI / 2
        dx, dy = math.cos(a) * size / 2, math.sin(a) * size / 2
        drumstick(cv, cx - dx, cy - dy, cx + dx, cy + dy, max(2.2, size * .09))


# ------------------------------------------------------------------------------------------------
# the Strip at night
# ------------------------------------------------------------------------------------------------

def vegas_scene(X, Y, W, H, seed=0, number="", date="", detail=True):
    cv = Canvas()
    rng = random.Random(seed)
    yh = Y + H * (.6 if detail else .5)      # horizon / foot of the barrier fence
    yg = Y + H * (.87 if detail else .9)     # ground line under the car
    # night sky: dense bulino at the zenith opening to a glow above the Strip
    sky = _rect(X - 2, Y - 2, X + W + 2, yh + 1)
    cv.obj([sky], 0)
    y = Y - 1.
    while y < yh + 1:
        f = (y - Y) / max(1, yh - Y)
        if f < .3:
            cv.line([(X - 2, y), (X + W + 2, y)])
            y += 2.
        else:
            cv.hair([(X - 2, y), (X + W + 2, y)])
            y += 1.5 if f < .55 else (2. if f < .82 else 3.)
    # stars
    for _ in range(int(W * (yh - Y) / 900)):
        sx, sy = X + rng.uniform(.03, .97) * W, Y + rng.uniform(.03, .5) * (yh - Y)
        s = rng.choice((1.1, 1.4, 1.8))
        cv.obj([[(sx, sy - s), (sx + s * .35, sy), (sx, sy + s), (sx - s * .35, sy)]], 0)
        cv.obj([[(sx - s, sy), (sx, sy - s * .35), (sx + s, sy), (sx, sy + s * .35)]], 0)
    if detail:
        # the moon, in today's phase
        ph = _moon_phase(date)
        mr = max(5., min(W, H) * .055)
        mx, my = X + W * .6, Y + H * .07 + mr
        disc = _ell_pts(mx, my, mr, mr, 40)[:-1]
        cv.obj([disc], .5)
        k = math.cos(ph * TAU)        # terminator ellipse x-scale
        waxing = ph < .5

        def lit(x, y):
            dx, dy = (x - mx) / mr, (y - my) / mr
            if dx * dx + dy * dy > 1:
                return False
            xt = k * math.sqrt(max(0., 1 - dy * dy))
            return dx > xt if waxing else dx < -xt
        cv.hair(_keep(_scan(disc, 0, 1.5), lambda x, y: not lit(x, y)))
        cv.hair(_keep(_scan(disc, 0, 3., 1.), lit))
        for (cx_, cy_, cr) in ((.3, -.2, .18), (-.25, .3, .14), (.1, .4, .1)):
            c = (mx + cx_ * mr, my + cy_ * mr)
            if lit(*c):
                cv.hair([_ell_pts(c[0], c[1], cr * mr, cr * mr, 10)])
        # the Luxor beam
        lx = X + W * .3
        beam = [(lx - .8, yh - H * .17), (lx - 3.5, Y - 2), (lx + 3.5, Y - 2), (lx + .8, yh - H * .17)]
        cv.obj([beam], 0)
        cv.hair([[(lx, yh - H * .17), (lx, Y - 2)]])
    # towers of the Strip: lit window grids, shadowed flanks
    towers = []
    xs = X - 4
    while xs < X + W:
        tw = rng.uniform(.06, .11) * W
        th = rng.uniform(.18, .38) * (yh - Y) * (1.25 if detail else 1.)
        towers.append((xs, tw, th, rng.random()))
        xs += tw * rng.uniform(.75, 1.05)
    for xs, tw, th, kind in towers:
        top = yh - th
        shape = [(xs, yh + 1), (xs, top + 4), (xs + tw * .2, top + 4), (xs + tw * .2, top), (xs + tw * .8, top),
                 (xs + tw * .8, top + 4), (xs + tw, top + 4), (xs + tw, yh + 1)] if kind < .5 else \
            [(xs, yh + 1), (xs, top + tw * .25), (xs + tw * .5, top), (xs + tw, top + tw * .25), (xs + tw, yh + 1)]
        cv.obj([shape], .5)
        cv.hair(_scan(shape, 90, 3., .5) + _scan(shape, 0, 3., .5))
        shade = [(xs + tw * .62, yh + 1), (xs + tw * .62, top), (xs + tw, top), (xs + tw, yh + 1)]
        cv.hair(_scan(shade, 90, 1.5, 0.))
    if detail:
        # the Stratosphere, far left
        sx = X + W * .12
        stop = Y + H * .2
        shaft = [(sx - 2.5, yh + 1), (sx - 1.5, stop + 12), (sx + 1.5, stop + 12), (sx + 2.5, yh + 1)]
        cv.obj([shaft], .5)
        cv.hair(_scan(shaft, 90, 1.5, .4))
        pod = [(sx - 9, stop + 12), (sx - 7, stop + 6), (sx + 7, stop + 6), (sx + 9, stop + 12), (sx + 5, stop + 15), (sx - 5, stop + 15)]
        cv.obj([pod], 1.)
        cv.hair(_scan(pod, 0, 1.5) )
        cv.obj([[(sx - 6, stop + 9), (sx + 6, stop + 9), (sx + 6, stop + 10.2), (sx - 6, stop + 10.2)]], 0)
        cv.line([[(sx, stop + 6), (sx, stop - 10)]])
        # the Luxor pyramid
        lx = X + W * .3
        pw = W * .12
        pyr = [(lx - pw, yh + 1), (lx, yh - H * .17), (lx + pw, yh + 1)]
        cv.obj([pyr], 1.)
        cv.hair(_scan([(lx - pw, yh + 1), (lx, yh - H * .17), (lx, yh + 1)], 60, 3.))
        cv.hair(_scan([(lx, yh + 1), (lx, yh - H * .17), (lx + pw, yh + 1)], -60, 1.5))
        # the Sphere
        sr = min(W * .14, H * .16)
        scx, scy = X + W * .74, yh - sr * .8
        sp = _ell_pts(scx, scy, sr, sr, 64)[:-1]
        cv.obj([sp], 1.)
        grid = []
        for i in range(1, 8):
            lat = -PI / 2 + PI * i / 8
            yy = scy + sr * math.sin(lat)
            hw = sr * math.cos(lat)
            grid.append(_dashes([(scx - hw, yy), (scx + hw, yy)], 1., 1.5))
        for i in range(1, 8):
            lo = -PI / 2 + PI * i / 8
            grid.append(_dashes([(scx + sr * math.sin(lo) * math.cos(t), scy + sr * math.sin(t))
                                 for t in [-PI / 2 + PI * j / 24 for j in range(25)]], 1., 1.5))
        for g in grid:
            cv.hair(g)
        # the LED skin: a fine dotted screen
        for ln in _scan(sp, 0, 3., 1.5):
            cv.hair(_dashes(ln, .8, 2.2))
        cv.hair(_keep(_scan(sp, 45, 2.), lambda x, y: (x - scx + sr * .35) ** 2 + (y - scy + sr * .35) ** 2 > (sr * 1.05) ** 2))
        cv.hair(_keep(_scan(sp, -45, 2.), lambda x, y: (x - scx + sr * .4) ** 2 + (y - scy + sr * .4) ** 2 > (sr * 1.35) ** 2))
    # catch fence and barrier wall
    fy1 = yh + H * (.05 if detail else .06)
    fence = _rect(X - 2, yh, X + W + 2, fy1)
    cv.obj([fence], 0)
    cv.hair(_scan(fence, 60, 3.) + _scan(fence, -60, 3.))
    cv.line([[(X - 2, yh), (X + W + 2, yh)]])
    posts = []
    px = X - 2
    while px < X + W + 2:
        posts.append([(px, yh - 3), (px, fy1)])
        px += 22
    cv.line(posts)
    wy1 = fy1 + H * .05
    wall = _rect(X - 2, fy1, X + W + 2, wy1)
    cv.obj([wall], 1.)
    cv.hair(_scan(wall, 0, 2., .5))
    panels = []
    px = X + 8
    while px < X + W + 2:
        panels.append([(px, fy1), (px, wy1)])
        px += 36
    cv.line(panels)
    # track: ruled asphalt, darker near the barrier
    trk = _rect(X - 2, wy1, X + W + 2, Y + H + 2)
    cv.obj([trk], 1.)
    y = wy1 + 1.5
    while y < Y + H + 2:
        cv.line([(X - 2, y), (X + W + 2, y)])
        y += 2.
    # chequered kerb in the foreground
    ky0 = Y + H * (.9 if detail else .93)
    kerb = []
    k = 0
    bx = X - 6
    while bx < X + W + 4:
        cell = [(bx, Y + H + 2), (bx + 4, ky0), (bx + 4 + 12, ky0), (bx + 12, Y + H + 2)]
        cv.obj([cell], .5)
        if k % 2 == 0:
            cv.heavy(_scan(cell, 0, 1.5, .2))
        else:
            cv.hair(_scan(cell, 0, 3.))
        bx += 12
        k += 1
    # the car, flat out
    L = min(W * (1.02 if detail else .92), H * (2.6 if detail else 3.4))
    f1_car(cv, X + W * .5 - L * .48, yg, L, number, True, detail, X, W)
    return cv.svg()


def medallion_scene(cx, cy, rx, ry, number=""):
    return vegas_scene(cx - rx, cy - ry, 2 * rx, 2 * ry, 3, number, detail=False)


# ------------------------------------------------------------------------------------------------
# layouts
# ------------------------------------------------------------------------------------------------

def _pair_unit(cv, cx, cy, r, side, rng, a_out=0., turns=1.4, tail=.9, up=True, fronds=3, wheel_eye=False):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    C._volute(cv, cx, cy, r, a0, turns, flip, rng, tail, -.5 if up else .5, r * .15, fronds)
    if wheel_eye:
        wheel(cv, cx, cy, r * .3, side * .3)


def _field_fill(cx, cy, w, h, inner_d, scene, uid):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.4, h / 2 - bw * 1.4
    body = scene(cx - a, cy - b, 2 * a, 2 * b)
    return (f'<clipPath id="{uid}"><path d="{inner_d}"/></clipPath><g clip-path="url(#{uid})">{body}</g>'
            f'<path d="{inner_d}" fill="none" stroke="#000" stroke-width="1"/>')


def layout_band(w, h, seed, ctx):
    race, when, leader, pts, num = _facts(ctx)
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    gap = min(gh * 2.6, 170)
    o.append(_clip(_uid("fb", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .86, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    uid = _uid("fm", w, h, seed)
    ell = _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(f'<clipPath id="{uid}"><path d="{ell}"/></clipPath><g clip-path="url(#{uid})">'
             + medallion_scene(cx, cy, rx - 2, ry - 2, num) + "</g>")
    # Easter egg: Parker's crossed sticks under the medallion
    ecv = Canvas()
    crossed_sticks(ecv, cx, cy + ry - 1, max(12., gh * .32))
    o.append(ecv.svg())
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, ctx):
    race, when, leader, pts, num = _facts(ctx)
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0 - 1, w, gh + 2), "G"))
    cw = min(w * .5, gh * 1.9)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = Canvas(), Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True, wheel_eye=r > 30)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("fmm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_fill(cx, cy, cw, ch, inner_d,
                         lambda X, Y, W, H: vegas_scene(X, Y, W, H, seed, num, ctx.get("date", ""), detail=H > 95),
                         _uid("fmf", w, h, seed)))
    o.append(C.egg_and_dart(0, 0, w, em))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, ctx):
    race, when, leader, pts, num = _facts(ctx)
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .02)
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    px0, py0 = 0., em + 1
    pw = w
    ph = h - py0 - ped_h - frieze + ped_h * .3
    o.append(C.dark_ground((0, py0 - 1, w, h - py0 + 1), "G"))
    cw, ch = pw * .6, ph * .7
    cx, cy = w / 2, py0 + ph * .48
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = Canvas(), Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True, wheel_eye=True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        _pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=11, edge=.6, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("ftt", w, h, seed), px0, py0, pw, ph, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_field_fill(cx, cy, cw, ch, inner_d,
                         lambda X, Y, W, H: vegas_scene(X, Y, W, H, seed, num, ctx.get("date", "")),
                         _uid("ftf", w, h, seed)))
    o.append(C.egg_and_dart(0, 0, w, em))
    # crest: a palmette carrying crossed chequered flags on drumstick staffs
    psz = min(ch * .14 + 8, 44)
    pal_y = cy - ch / 2 + 6
    o.append(C.palmette(cx, pal_y, psz, True, rng.randrange(1 << 20)))
    fcv = Canvas()
    fs = max(26., min(84., psz * 1.9))
    crossed_flags(fcv, cx, max(fs * .5 + 2, pal_y - psz * .7), fs)
    o.append(fcv.svg())
    # ribbon banner with the next race
    bh = min(18., max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    R = C._Rib(centre, [bh / 2] * len(centre), [bh / 2] * len(centre))
    face = [R.at(i / 40, .62) for i in range(41)] + [R.at(i / 40, -.62) for i in range(40, -1, -1)]
    o.append(f'<path d="{hatch_d(face, 0, 3, .5)}" stroke="#000" stroke-width=".5"/>')
    txt = (race + ("  *  " + when if when else "")).strip()
    sz = bh * .5
    o.append(lettering_svg(letter(txt, sz, along(centre, sz, txt)), 1. if bh < 15 else 1.5, 4.))
    # pedestal with the championship leader
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    tab = [(tx + 3, ty + 3), (tx + tw - 1, ty + 3), (tx + tw - 1, ty + th - 1), (tx + 3, ty + th - 1)]
    o.append(f'<path d="{hatch_d(tab, 0, 2, .5)}" stroke="#000" stroke-width=".5"/>')
    rec = f"{leader}  {pts}" if leader else "FORMULA 1"
    sz = min(th * .56, 13)
    x0 = tx + (tw - text_width(rec, sz)) / 2
    y0 = ty + (th - sz) / 2 + 1
    o.append(lettering_svg(letter(rec, sz, lambda x, y: (x0 + x, y0 + y)), 1.5 if sz > 10 else 1., 4.5))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(_clip(_uid("ftb", w, h, seed), 0, fy, w, fh - 2,
                       C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) % 997 + 53
    if h < 110:
        body = layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx)
    else:
        body = layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
