"""Around Portland plate: the St. Johns Bridge seen from Cathedral Park (its gothic towers and
lancet arcade, cables and suspenders over the Willamette) with Mt. Hood behind and the West Hills;
in the foreground a bottle of New Deal's green-walnut Nocino stands on the river wall with two green
walnuts (the page's "New to try" and the St. Johns liquor store). Walnut sprigs hang either side of
the cartouche. Framed in the house acanthus; banner lettered AROUND PORTLAND, pedestal tablet
lettered with the page's four rooms. Easter egg: Parker's dog sits in Cathedral Park under the
arches, watching the river."""
import sys
import math
import random
import engraving_codex as C

_n, _d, PI, TAU = C._n, C._d, C.PI, C.TAU
hatch = C.hatch_poly


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def ell(cx, cy, rx, ry, n=28, a0=0., a1=TAU):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n)]


def hz(poly, pitch=2.):
    return hatch(poly, 0, pitch, .25)


def vt(poly, pitch=2.):
    return hatch(poly, 90, pitch, .25)


def solid(cv, poly, outline=1.):
    cv.obj([poly], outline)
    cv.line(hatch(poly, 0, .8))


def lancet(x0, x1, yb, spring, n=6):
    """a pointed (gothic) arch opening: jambs from yb up to `spring`, two arcs meeting at the apex"""
    w = x1 - x0
    r = w * .85
    pts = [(x0, yb), (x0, spring)]
    # left arc: centre at (x0 + r, spring)
    a_end = math.acos((r - w / 2) / r)
    for i in range(1, n + 1):
        a = PI - a_end * i / n
        pts.append((x0 + r + r * math.cos(a), spring - r * math.sin(a)))
    for i in range(n - 1, -1, -1):
        a = a_end * i / n
        pts.append((x1 - r + r * math.cos(a), spring - r * math.sin(a)))
    pts.append((x1, yb))
    return pts


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
# the scene: St. Johns Bridge from Cathedral Park
# ----------------------------------------------------------------------------------------------

def walnut(cv, cx, cy, r, ang=0.):
    """a green walnut: round husk, lit upper left, shaded to a crescent, with a tiny stalk scar"""
    poly = ell(cx, cy, r, r * .94, 26)
    cv.obj([poly], 1.)
    cv.hair(hatch(poly, 35, 3.))
    shade = [(cx + r * math.cos(t), cy + r * .94 * math.sin(t)) for t in [-.6 + 2.6 * i / 14 for i in range(15)]]
    shade += [(cx + r * .55 * math.cos(t) + r * .22, cy + r * .5 * math.sin(t) + r * .18)
              for t in [2. - 2.6 * i / 14 for i in range(15)]]
    cv.hair(hatch(shade, -55, 1.5))
    cv.hair([(cx + r * .62 * math.cos(t), cy + r * .58 * math.sin(t)) for t in [3.6 + .9 * i / 6 for i in range(7)]])
    s = (cx + r * .2 * math.cos(ang - PI / 2), cy - r * .92)
    cv.line([s, (s[0] + r * .15, s[1] - r * .35)])


def leaflet(cv, x, y, ang, L, wd, side=1):
    """one pinnate walnut leaflet from (x, y) along ang: pointed oval, midrib, shaded half with
    veins, lit half clean"""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)
    n = 12
    top = [P(L * i / n, wd * math.sin(PI * i / n) ** .8 * (1 - .25 * i / n)) for i in range(n + 1)]
    bot = [P(L * i / n, -wd * math.sin(PI * i / n) ** .8 * (1 - .25 * i / n)) for i in range(n, 0, -1)]
    poly = top + bot
    cv.obj([poly], 1.)
    half = top + [P(L, 0), P(0, 0)]
    cv.hair(hatch(half, math.degrees(ang) + 60 * side, 1.5))
    cv.line([P(0, 0), P(L * .95, 0)])
    for i in range(2, n - 1, 2):
        u = L * i / n
        cv.hair([P(u, 0), P(u + wd * .9, -wd * .7 * math.sin(PI * i / n))])


def walnut_sprig(cv, x, y, ang, L, side=1, nuts=2, seed=0):
    """a hanging walnut branch: a curved stalk with paired leaflets, a terminal leaflet and green nuts"""
    rng = random.Random(seed)
    pts = []
    for i in range(21):
        t = i / 20
        a = ang + side * .5 * t
        if i == 0:
            pts.append((x, y))
        else:
            px, py = pts[-1]
            pts.append((px + L / 20 * math.cos(a), py + L / 20 * math.sin(a)))
    lw = L * .11
    for k, i in enumerate((5, 9, 13, 17)):
        px, py = pts[i]
        a = math.atan2(pts[i + 1][1] - py, pts[i + 1][0] - px)
        for s in (-1, 1):
            leaflet(cv, px, py, a + s * (.95 + rng.uniform(-.1, .1)), L * (.3 + .03 * k), lw, s)
    px, py = pts[-1]
    a = math.atan2(py - pts[-2][1], px - pts[-2][0])
    leaflet(cv, px, py, a, L * .36, lw, 1)
    band = [(p[0] + 1.2 * math.sin(math.atan2(1, 1)), p[1] - 1.2 * math.cos(math.atan2(1, 1))) for p in pts]
    cv.obj([pts + band[::-1]], 0)
    cv.heavy(pts)
    nr = L * .1
    for j in range(nuts):
        p = pts[3 + 4 * j]
        walnut(cv, p[0] + side * nr * (.9 + .6 * j), p[1] + nr * (1.4 + .3 * j), nr)


def tiny_dog(cv, x, y, s, face=1):
    """Parker's dog, sitting, feet at (x, y), s px tall, facing +x (face=1) or -x: a solid silhouette
    with a white ear line and collar."""
    U = [(0, 0), (-.05, -.18), (.0, -.36), (.12, -.52), (.3, -.63), (.4, -.72), (.42, -.86), (.47, -.96),
         (.5, -1.02), (.53, -.95), (.6, -.94), (.7, -.9), (.8, -.84), (.82, -.8), (.74, -.76), (.62, -.74),
         (.58, -.66), (.56, -.5), (.58, -.3), (.6, -.05), (.64, 0), (.5, 0), (.49, -.22), (.44, -.3),
         (.38, -.12), (.42, 0)]
    poly = [(x + face * u * s, y + v * s) for u, v in U]
    solid(cv, poly, 1.)
    tail = [(x + face * u * s, y + v * s) for u, v in ((-.02, -.08), (-.18, -.1), (-.28, -.2), (-.26, -.3))]
    cv.obj([], 0)
    cv.line(tail)


def bottle(cv, cx, base, hgt):
    """the Nocino: a tall shouldered bottle, dark (the walnut liqueur is near black), with a white
    window light, a lettered label carrying a walnut and a wax-sealed cork"""
    bw = hgt * .3
    sh = base - hgt * .55
    nk = base - hgt * .82
    nw = bw * .32
    top = base - hgt
    pts = [(cx - bw / 2, base), (cx - bw / 2, sh)]
    for i in range(1, 7):
        t = i / 6
        pts.append((cx - bw / 2 + (bw / 2 - nw / 2) * (1 - math.cos(t * PI / 2)), sh - (sh - nk) * math.sin(t * PI / 2)))
    pts += [(cx - nw / 2, top + hgt * .05), (cx - nw * .62, top + hgt * .03), (cx - nw * .62, top + hgt * .015)]
    right = [(2 * cx - px, py) for px, py in pts[::-1]]
    poly = pts + right
    cv.obj([poly], 1.)
    # glass: dark body, cylindrical modelling, highlight a third from the left
    body = rect(cx - bw / 2, sh + 1, cx + bw / 2, base)
    xs = []
    x = cx - bw / 2 + .5
    hl = cx - bw * .18
    while x < cx + bw / 2:
        if abs(x - hl) > bw * .07:
            xs.append(x)
        x += 1.5 if (x > cx + bw * .1 or x < cx - bw * .38) else 2.
    cv.hair([[(xx, sh - (sh - nk) * .0 + 1), (xx, base - .6)] for xx in xs])
    cv.hair(hatch(poly, 0, 1.5))
    # shoulder and neck: curved bands of hatch
    sp = [p for p in poly if p[1] <= sh + .5]
    cv.hair(hatch(sp, 70, 2.))
    # label
    ly0, ly1 = sh + hgt * .12, sh + hgt * .38
    lab = rect(cx - bw / 2 + .5, ly0, cx + bw / 2 - .5, ly1)
    cv.obj([lab], 1.)
    cv.hair(vt(rect(cx + bw * .28, ly0, cx + bw / 2, ly1), 1.5))
    cv.hair([[(cx - bw / 2 + 2, ly0 + 2), (cx + bw / 2 - 2, ly0 + 2)], [(cx - bw / 2 + 2, ly1 - 2), (cx + bw / 2 - 2, ly1 - 2)]])
    cap = (ly1 - ly0) * .2
    t = "NOCINO"
    if cap >= 3.2:
        lw_ = text_width(t, cap)
        ln = letter(t, cx - lw_ / 2, ly0 + 3.5, cap)
        cv.obj([], 0)
        cv.hair(ln)
        wr = (ly1 - ly0) * .2
        wy = ly1 - 3.5 - wr
        wp = ell(cx, wy, wr, wr * .9, 16)
        cv.obj([wp], .5)
        cv.hair(hatch(wp, 40, 1.5, 0, 0)[len(hatch(wp, 40, 1.5)) // 2:])
    # wax over the cork
    wax = rect(cx - nw * .62, top, cx + nw * .62, top + hgt * .07)
    solid(cv, wax, 1.)


def scene(x, y, W, H, clip_d, seed, detail=2, uid="cv"):
    """everything inside the cartouche field (bbox x, y, W, H; clipped to clip_d).
    detail: 0 medallion, 1 medium cartouche, 2 tall cartouche"""
    rng = random.Random(seed)
    cv = C.Canvas()
    cx = x + W / 2
    G = y + H * (.66 if detail else .7)            # waterline
    deck = y + H * (.44 if detail else .5)
    ttop = y + H * (.14 if detail else .2)
    span = W * (.21 if detail else .3)
    tl, tr_ = cx - span, cx + span

    # sky: ruled, tighter overhead, a moon by the date
    sky = rect(x - 2, y - 2, x + W + 2, G + 1)
    cv.obj([sky], 0)
    cv.hair(hz(rect(x - 2, y - 2, x + W + 2, y + H * .2), 1.5))
    cv.hair(hz(rect(x - 2, y + H * .2, x + W + 2, G + 1), 2.))
    if detail:
        # banks of cloud: white shapes, their bellies hatched
        for k in range(3 if detail == 2 else 2):
            ccx = x + W * (.18 + .32 * k + rng.uniform(-.05, .05))
            ccy = y + H * (.12 + .07 * (k % 2))
            cw = W * rng.uniform(.18, .26)
            chh = H * .045
            cl = []
            for i in range(25):
                t = PI + PI * i / 24
                bump = 1 + .25 * abs(math.sin(i * 1.3 + k))
                cl.append((ccx + cw / 2 * math.cos(t), ccy + chh * bump * math.sin(t)))
            cl.append((ccx + cw / 2, ccy + chh * .35))
            cl.append((ccx - cw / 2, ccy + chh * .35))
            cv.obj([cl], .5)
            cv.hair(hz([(px, py) for px, py in cl if py > ccy - chh * .4] + [(ccx - cw / 2, ccy + chh * .35)], 1.5))
            cv.hair(hz(cl, 3.))

    if detail == 2:
        cv.obj([], 0)
        for k in range(3):
            gx_, gy_ = x + W * (.3 + .09 * k), y + H * (.27 + .03 * (k % 2))
            g = 2.2 + k * .4
            cv.line([(gx_ - g, gy_ - g * .5), (gx_ - g * .4, gy_ - g * .6), (gx_, gy_), (gx_ + g * .4, gy_ - g * .6), (gx_ + g, gy_ - g * .5)])
    # Mt. Hood
    hp = cx + W * .08
    hb = G - H * .05
    hh = H * (.33 if detail else .3)
    hw = W * .34
    prof = [(hp - hw, hb), (hp - hw * .62, hb - hh * .32), (hp - hw * .38, hb - hh * .56), (hp - hw * .2, hb - hh * .76),
            (hp - hw * .08, hb - hh * .93), (hp, hb - hh), (hp + hw * .05, hb - hh * .94), (hp + hw * .12, hb - hh * .9),
            (hp + hw * .24, hb - hh * .72), (hp + hw * .45, hb - hh * .48), (hp + hw * .7, hb - hh * .26), (hp + hw, hb)]
    cv.obj([prof], 1.)
    snow_y = hb - hh * .5
    jag = []
    for i in range(15):
        u = -1 + 2 * i / 14
        jag.append((hp + u * hw * .62, snow_y + (H * .025) * ((i % 2) * 1.2 - .2) + abs(u) * hh * .08))
    low = jag + [(hp + hw * 1.1, hb + 1), (hp - hw * 1.1, hb + 1)]
    cv.hair(hz(low, 1.5))
    east = [(hp, hb - hh)] + [p for p in prof if p[0] > hp] + [(hp + hw * .05, hb)]
    cv.hair(hatch(east, 60, 2.))
    for k in range(5):
        u = .12 + k * .16
        cv.hair([(hp - hw * u * .3, hb - hh * (1 - u * .2)), (hp - hw * u * .9, snow_y + H * .02)])
    # the West Hills, forested: scalloped tops, cross-hatched
    hills = [(x - 2, G + 1)]
    for i in range(41):
        t = i / 40
        hx = x - 2 + (W + 4) * t
        hy = G - H * (.05 + .07 * max(0, .55 - t) + .012 * abs(math.sin(i * 1.7 + seed)))
        hills.append((hx, hy))
    hills.append((x + W + 2, G + 1))
    cv.obj([hills], .5)
    cv.hair(hatch(hills, 0, 1.5))
    ticks = []
    for p, q in zip(hills[1:-2], hills[2:-1]):
        for f in (.25, .75):
            ticks.append([(p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f + .5), (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f + 3.5)])
    cv.line(ticks)

    # the Willamette: broken water lines, open near the horizon, tighter toward us; tower reflections
    river = rect(x - 2, G, x + W + 2, y + H + 2)
    cv.obj([river], 0)
    lines = []
    yy = G + 1.5
    while yy < y + H + 2:
        pitch = 3. if yy < G + H * .12 else 2.
        xx = x - 2 + rng.uniform(0, 8)
        while xx < x + W + 2:
            L = rng.uniform(8, 34)
            lines.append([(xx, yy), (min(xx + L, x + W + 2), yy)])
            xx += L + rng.uniform(1.5, 4)
        yy += pitch
    cv.hair(lines)
    for tx in (tl, tr_):
        rf = rect(tx - W * .025, G + 1, tx + W * .025, G + H * .2)
        cv.hair(hz(rf, 3.) if False else [[(a[0], a[1] + 1.5), (b[0], b[1] + 1.5)] for a, b in hz(rf, 3.)])
    # wake of a little river boat (upstream, right)
    if detail == 2:
        bx, by = cx + W * .02, G + H * .07
        boat = [(bx - W * .04, by), (bx + W * .04, by), (bx + W * .035, by + 3), (bx - W * .035, by + 3)]
        cv.obj([boat], 1.)
        cab = rect(bx - W * .015, by - 4, bx + W * .012, by)
        cv.obj([cab], 1.)
        cv.hair(vt(cab, 1.5))
        cv.obj([], 0)
        cv.line([(bx - W * .07, by + 3.5), (bx + W * .06, by + 3.5)])

    # Cathedral Park: the left bank under the approach arcade
    bank_y = G - H * .03
    bank = [(x - 2, bank_y), (tl - W * .06, bank_y)]
    for i in range(1, 13):
        t = i / 12
        bank.append((tl - W * .06 - W * .2 * t ** 1.6 + W * .03 * math.sin(t * PI), bank_y + (y + H + 2 - bank_y) * t))
    bank.append((x - 2, y + H + 2))
    # approach: concrete arcade of lancet arches from the field edge to the left tower
    arc_top = deck + H * .035
    arc = rect(x - 2, arc_top, tl - W * .02, bank_y + 1)
    cv.obj([arc], 1.)
    cv.hair(hz(arc, 3.))
    nb = 3 if detail else 2
    bay = (tl - W * .02 - x) / nb
    for i in range(nb):
        bx0 = x + bay * i + bay * .18
        bx1 = x + bay * (i + 1) - bay * .18
        if bx1 - bx0 < 4:
            continue
        op = lancet(bx0, bx1, bank_y + 1, arc_top + (bank_y - arc_top) * .45)
        cv.obj([op], 1.)
        cv.hair(hz(op, 1.5))
        cv.hair(hatch(op, 90, 3.))
        # pier shading: the right flank of each pier in shadow
        cv.obj([], 0)
        cv.hair(vt(rect(bx1 + 1, arc_top + 2, bx1 + bay * .2, bank_y), 1.5))
    cv.obj([bank], 1.)
    cv.hair(hz(bank, 2.))
    grass = []
    for i in range(int(W * H / 260)):
        px_ = x + rng.uniform(0, W * .32)
        py_ = bank_y + 3 + rng.uniform(0, H * .4)
        grass.append([(px_, py_), (px_ + .7, py_ - 2.2)])
    cv.hair(grass)
    # the shore: the bank face dropping to the water, in shadow
    lip = bank[1:-1]
    face = lip + [(px + 3.5, py + 1.5) for px, py in lip[::-1]]
    cv.obj([face], .5)
    cv.line(hatch(face, 0, 1.5))
    # grass tufts along the bank top
    tufts = []
    gx = x
    while gx < tl - W * .1:
        hh_ = rng.uniform(1.5, 3.2)
        tufts.append([(gx, bank_y), (gx + rng.uniform(-.8, .8), bank_y - hh_)])
        gx += rng.uniform(1.6, 2.6)
    cv.obj([], 0)
    cv.hair(tufts)

    # the bridge: main cables, suspenders, gothic towers, stiffening truss
    dk0, dk1 = deck, deck + max(3., H * .03)
    cab_low = deck - H * .03

    def cable_y(px):
        if px < tl:
            return ttop + (deck - ttop) * ((tl - px) / (tl - x + 6)) ** .9 * .95 + 2
        if px > tr_:
            return ttop + (deck - ttop) * ((px - tr_) / (x + W + 6 - tr_)) ** .9 * .95 + 2
        u = (px - cx) / span
        return cab_low - (cab_low - ttop - 2) * u * u
    cab = [(px, cable_y(px)) for px in [x - 2 + (W + 4) * i / 120 for i in range(121)]]
    cv.obj([], 0)
    sus = []
    px = x + 1.
    while px < x + W:
        cy_ = cable_y(px)
        if dk0 - cy_ > 2 and abs(px - tl) > W * .03 and abs(px - tr_) > W * .03:
            sus.append([(px, cy_), (px, dk0)])
        px += 3. if detail else 4.
    cv.hair(sus)
    cv.heavy(cab)
    cv.hair([(p[0], p[1] - 1.5) for p in cab])
    for tx in (tl, tr_):
        tb = G + 2
        wb, wt = W * .05, W * .032
        tw = [(tx - wb / 2, tb), (tx - wt / 2, ttop + 2), (tx + wt / 2, ttop + 2), (tx + wb / 2, tb)]
        # spire with corner pinnacles
        sp = [(tx - wt * .55, ttop + 2), (tx, ttop - H * .07), (tx + wt * .55, ttop + 2)]
        cv.obj([sp], 1.)
        cv.hair(hatch([(tx, ttop - H * .07), (tx + wt * .55, ttop + 2), (tx, ttop + 2)], 90, 1.5))
        for s in (-1, 1):
            pn = [(tx + s * wt * .5 - 1.2, ttop + 3), (tx + s * wt * .5, ttop - H * .03), (tx + s * wt * .5 + 1.2, ttop + 3)]
            cv.obj([pn], .5)
        cv.obj([tw], 1.)
        cv.hair(vt([(tx, tb), (tx, ttop + 2), (tx + wt / 2, ttop + 2), (tx + wb / 2, tb)], 1.5))
        cv.hair(vt([(tx - wb / 2, tb), (tx - wt / 2, ttop + 2), (tx - wt * .2, ttop + 2), (tx - wb * .2, tb)], 3.))
        # stacked lancets up the tower face, the portal where the deck passes
        n_l = 3 if detail else 2
        seg = (dk0 - ttop - 6) / n_l
        for k in range(n_l):
            yb = ttop + 6 + seg * (k + 1) - seg * .18
            f = (yb - ttop) / (tb - ttop)
            hw_ = (wt + (wb - wt) * f) * .22
            win = lancet(tx - hw_, tx + hw_, yb, yb - seg * .45, 4)
            solid(cv, win, .5)
            cv.obj([], 0)
            cv.line([(tx - hw_ * 2.2, yb + 1.5), (tx + hw_ * 2.2, yb + 1.5)])
        hw_ = wb * .3
        portal = lancet(tx - hw_, tx + hw_, G, dk1 + (G - dk1) * .3, 5)
        cv.obj([portal], 1.)
        cv.hair(hz(portal, 1.5))
        # pier in the river
        pier = rect(tx - wb * .7, G - 1, tx + wb * .7, G + max(3., H * .025))
        cv.obj([pier], 1.)
        cv.hair(vt(rect(tx, G, tx + wb * .7, G + max(3., H * .025)), 1.5))
    # deck and truss
    dk = rect(x - 2, dk0, x + W + 2, dk1)
    cv.obj([dk], 1.)
    tru = []
    step = max(3., (dk1 - dk0) * 1.1)
    px = x - 2
    k = 0
    while px < x + W + 2:
        tru.append([(px, dk1 if k % 2 else dk0), (px + step, dk0 if k % 2 else dk1)])
        px += step
        k += 1
    cv.hair(tru)
    cv.obj([], 0)
    cv.heavy([(x - 2, dk1 + .5), (x + W + 2, dk1 + .5)])
    rail = []
    px = x - 2
    while px < x + W + 2:
        rail.append([(px, dk0), (px, dk0 - 1.5)])
        px += 2.
    cv.hair(rail)
    cv.hair([(x - 2, dk0 - 1.6), (x + W + 2, dk0 - 1.6)])

    # foreground: the river wall, the Nocino and two green walnuts
    if detail:
        wy = y + H * .84
        wall = [(cx + W * .1, wy), (x + W + 2, wy - H * .02), (x + W + 2, y + H + 2), (cx + W * .06, y + H + 2)]
        cv.obj([wall], 1.)
        cv.hair(hz(wall, 2.))
        joints = []
        for r_ in range(4):
            yj = wy + 3 + r_ * 6
            joints.append([(cx + W * .08, yj), (x + W + 2, yj - H * .02 * (1 - r_ * .2))])
            for c_ in range(6):
                xj = cx + W * (.14 + .07 * c_ + .035 * (r_ % 2))
                joints.append([(xj, yj), (xj, yj + 6)])
        cv.line(joints[:4])
        cv.hair(joints[4:])
        bh = H * (.34 if detail == 2 else .3)
        bxc = x + W * .8
        bottle(cv, bxc, wy - H * .012, bh)
        wr = max(3.5, H * .035)
        def wall_top(px):
            return wy + (px - (cx + W * .1)) / (x + W + 2 - cx - W * .1) * (-H * .02)
        for fx_, f_ in ((.36, 1.), (.62, .92)):
            px_ = bxc - bh * fx_
            walnut(cv, px_, wall_top(px_) - wr * f_ * .94, wr * f_)
        # Easter egg: Parker's dog sitting in Cathedral Park, watching the river
        ds = max(7., H * .065)
        tiny_dog(cv, x + W * .11, y + H * .74, ds, 1)

    cid = C._uid("loc", uid, x, y, W, H)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ----------------------------------------------------------------------------------------------
# layouts (the house layouts, adapted: the field engraved whole, banner and tablet lettered)
# ----------------------------------------------------------------------------------------------

def _field(w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


TABLET = "NEW TO TRY · OPENING · BIG EVENTS · ST. JOHNS"


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.2, 150)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fr = C._ell_pts(cx, cy, rx - 2, ry - 2, 64)
    o.append(scene(cx - rx, cy - ry, 2 * rx, 2 * ry, _d(fr, True, 0), seed, 0, "b"))
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
    cw = min(w * .46, gh * 1.7)
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
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed, 1 if h < 170 else 2, "m"))
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
    cw, ch = pw * .5, ph * .62
    cx, cy = w / 2, py0 + ph * .45
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    # walnut sprigs hanging from the cartouche shoulders, over the scrollwork
    sp = C.Canvas()
    L = min(ch * .42, 110)
    for side in (-1, 1):
        walnut_sprig(sp, cx + side * (cw * .5 - 6), cy - ch * .28, PI / 2 - side * .55, L, -side, 2, seed + side)
    o.append(C._clip(C._uid("s", w, h, seed), px0, py0, pw, ph, sp.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cw, ch)
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed, 2, "t"))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    cap = bh * .5
    txt = "AROUND PORTLAND"
    Lc = _plen(centre)
    o.append(lettering_svg(letter(txt, (Lc - text_width(txt, cap)) / 2, -cap / 2, cap, centre), 1.))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw_, th_) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    t2 = TABLET
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
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 31
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
