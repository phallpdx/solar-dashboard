"""local-03 "Big events in town" / Big nights out.

The vignette is Portland's big night: the 75-foot Pioneer Courthouse Square tree lit under a
ruled night sky, its star throwing white rays, fireworks bursting, a basketball rising as the moon
(the Civil War game at the Moda Center), the Oregon Convention Center's twin glass spires on the
left (Kumoricon, table tennis), the Moda Center drum on the right, downtown towers between, the
crowd in the brick square below. Easter egg: Parker's dog sits in the crowd looking up at the
tree, and a tiny "P" is cut into the brick at his feet.
"""
import sys
import math
import random
import re
import engraving_codex as C

_n, _d = C._n, C._d
TAU = math.tau

# extra patterns: polished stipple for leaf bodies (no blank white), page-matching back hatch
_XDEFS = ('<defs>'
          '<pattern id="l3s" width="20" height="20" patternUnits="userSpaceOnUse">'
          '<rect x="4" y="4" width="2" height="2" fill="#000"/>'
          '</pattern>'
          '<pattern id="l3t" width="5" height="5" patternUnits="userSpaceOnUse">'
          '<rect x="1" y="1" width=".5" height=".5" fill="#000"/>'
          '</pattern>'
          '<pattern id="l3p" width="4" height="4" patternUnits="userSpaceOnUse">'
          '<path d="M0,0L4,4M-2,2L2,6M2,-2L6,2" stroke="#000" stroke-width=".5"/></pattern>'
          '</defs>')


_SID = [0]


def _stipple(svg):
    """Lay a sparse polished stipple over every white body so no blank white survives (canvas
    paths are drawn at scale(.25), so they take the 4x tile). The shape is defined once and used
    twice, white then dots: no tile background, so no seams."""
    def sub(m):
        _SID[0] += 1
        pid = f"l3w{_SID[0]}"
        attrs = m.group(1)
        dots = "url(#l3s)" if "scale(.25)" in attrs else "url(#l3t)"
        return (f'<defs><path id="{pid}"{attrs[5:]}/></defs><use href="#{pid}" fill="#fff" stroke="none"/>'
                f'<use href="#{pid}" fill="{dots}" stroke="none"/>')
    return re.sub(r'(<path[^>]*?) ?fill="#fff" stroke="none"/>', sub, svg)


# ---------------------------------------------------------------------------------------------
# a small engraved Roman capital alphabet, drawn as strokes on a 4 x 6 grid (y down)
# ---------------------------------------------------------------------------------------------
def _ARC(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_G = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "B": [[(0, 0), (0, 6)], [(0, 0), (2.4, 0)] + _ARC(2.4, 1.5, 1.4, 1.5, -90, 90) + [(0, 3)],
          [(0, 3), (2.6, 3)] + _ARC(2.6, 4.5, 1.4, 1.5, -90, 90) + [(0, 6)]],
    "C": [_ARC(2.2, 3, 2.2, 3, -50, -310, 14)],
    "D": [[(0, 0), (0, 6)], [(0, 0), (1.6, 0)] + _ARC(1.6, 3, 2.4, 3, -90, 90, 12) + [(0, 6)]],
    "E": [[(3.6, 0), (0, 0), (0, 6), (3.6, 6)], [(0, 3), (2.6, 3)]],
    "F": [[(3.6, 0), (0, 0), (0, 6)], [(0, 3), (2.6, 3)]],
    "G": [_ARC(2.2, 3, 2.2, 3, -50, -330, 14) + [(4.2, 3.6), (2.4, 3.6)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 0), (1, 6)]],
    "J": [[(3, 0), (3, 4.4)] + _ARC(1.6, 4.4, 1.4, 1.6, 0, 160, 6)],
    "K": [[(0, 0), (0, 6)], [(3.8, 0), (0, 3.6)], [(1.3, 2.4), (4, 6)]],
    "L": [[(0, 0), (0, 6), (3.4, 6)]],
    "M": [[(0, 6), (0.3, 0), (2.4, 6), (4.5, 0), (4.8, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [_ARC(2.3, 3, 2.3, 3, 0, 360, 18)],
    "P": [[(0, 6), (0, 0), (2.4, 0)] + _ARC(2.4, 1.6, 1.5, 1.6, -90, 90) + [(0, 3.2)]],
    "R": [[(0, 6), (0, 0), (2.4, 0)] + _ARC(2.4, 1.6, 1.5, 1.6, -90, 90) + [(0, 3.2)], [(1.8, 3.2), (4, 6)]],
    "S": [_ARC(2, 1.5, 1.9, 1.5, -20, -270, 8) + _ARC(2, 4.5, 1.9, 1.5, -90, 160, 9)],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 4)] + _ARC(2, 4, 2, 2, 180, 0, 10) + [(4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1.2, 6), (2.4, 0), (3.6, 6), (4.8, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "·": [[(.6, 2.6), (1.2, 3), (.6, 3.4), (0, 3), (.6, 2.6)]],
}
_ADV = {"I": 2.2, "M": 6.2, "W": 6.2, " ": 4.2, "·": 3.0}


def _text_width(s):
    return sum(_ADV.get(ch, 5.6) for ch in s) - 1.4


def _letter(ch, x, y, k, rot=0., ox=0., oy=0.):
    """Glyph strokes scaled by k (glyph height 6k), top-left at (x, y), rotated by rot about (ox, oy)."""
    out = []
    c, s = math.cos(rot), math.sin(rot)
    for st in _G.get(ch, []):
        pts = []
        for gx, gy in st:
            px, py = x + gx * k - ox, y + gy * k - oy
            pts.append((ox + px * c - py * s, oy + px * s + py * c))
        out.append(pts)
    return out


def letter_line(s, cx, cy, height, width_max=None):
    k = height / 6.
    tw = _text_width(s) * k
    if width_max and tw > width_max:
        k *= width_max / tw
        tw = width_max
    x = cx - tw / 2
    out = []
    for ch in s:
        out += _letter(ch, x, cy - 3 * k, k)
        x += _ADV.get(ch, 5.6) * k
    return out


def letter_curve(s, centre, height):
    """Letter s along a centre polyline (the ribbon face), each glyph turned to the local tangent."""
    L = [0.]
    for a, b in zip(centre, centre[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = L[-1]
    k = height / 6.
    tw = _text_width(s) * k
    if tw > tot * .86:
        k *= tot * .86 / tw
        tw = tot * .86

    def at(d):
        for i in range(1, len(L)):
            if L[i] >= d:
                t = (d - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                a, b = centre[i - 1], centre[i]
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, math.atan2(b[1] - a[1], b[0] - a[0])
        a, b = centre[-2], centre[-1]
        return b[0], b[1], math.atan2(b[1] - a[1], b[0] - a[0])
    d = (tot - tw) / 2
    out = []
    for ch in s:
        adv = _ADV.get(ch, 5.6) * k
        gx, gy, ang = at(d + (adv - 1.4 * k) / 2)
        out += _letter(ch, gx - (adv - 1.4 * k) / 2, gy - 3 * k, k, ang, gx, gy)
        d += adv
    return out


def _roman(n):
    out = ""
    for v, r in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                 (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += r
            n -= v
    return out


_MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _date_line(ctx):
    try:
        y, m, d = (int(v) for v in ctx.get("date", "")[:10].split("-"))
        return f"PORTLAND · {_roman(d)} {_MON[m - 1]} · {_roman(y)}"
    except Exception:
        return "PORTLAND · OREGON"


# ---------------------------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------------------------
def _clip_x(pls, xmin=-1e9, xmax=1e9):
    out = []
    for pl in pls:
        (x0, y0), (x1, y1) = pl[0], pl[-1]
        if x0 > x1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        if x1 < xmin or x0 > xmax:
            continue

        def at(x):
            return (x, y0 + (y1 - y0) * (x - x0) / (x1 - x0)) if x1 != x0 else (x, y0)
        a = (x0, y0) if x0 >= xmin else at(xmin)
        b = (x1, y1) if x1 <= xmax else at(xmax)
        out.append([a, b])
    return out


def _clip_y(pls, ymin=-1e9, ymax=1e9):
    sw = [[(p[1], p[0]) for p in (pl[0], pl[-1])] for pl in pls]
    return [[(p[1], p[0]) for p in pl] for pl in _clip_x(sw, ymin, ymax)]


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _circle(cx, cy, r, n=None):
    n = n or max(10, int(r * 3))
    return C._ell_pts(cx, cy, r, r, n)


def _star(cx, cy, R, r, n=5, rot=-90):
    return [(cx + (R if i % 2 == 0 else r) * math.cos(math.radians(rot + 180 * i / n)),
             cy + (R if i % 2 == 0 else r) * math.sin(math.radians(rot + 180 * i / n))) for i in range(2 * n)]


def _spike(cx, cy, ang, r0, r1, wdt):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    return [(cx + ux * r0 - uy * wdt, cy + uy * r0 + ux * wdt), (cx + ux * r1, cy + uy * r1),
            (cx + ux * r0 + uy * wdt, cy + uy * r0 - ux * wdt)]


# ---------------------------------------------------------------------------------------------
# the bespoke vignette
# ---------------------------------------------------------------------------------------------
def night_scene(uid, clip_d, bx, by, bw, bh, seed=0, small=False, ext=0.):
    """Pioneer Courthouse Square on a big night, drawn to cover the box (bx, by, bw, bh) and
    clipped to clip_d."""
    rng = random.Random(seed)
    S = bh

    def U(u):
        return bx + bw * u

    def V(v):
        return by + bh * v
    cx = bx + bw / 2
    o = []
    # --- sky: ruled night, darkest overhead, cloud banks easing to the city glow on the horizon
    hz = V(.70)

    def bank(v0, amp, ph):
        return [(bx - 2 + (bw + 4) * i / 40, V(v0) + bh * amp * (math.sin(i * .55 + ph) * .6 + math.sin(i * 1.3 + ph * 2) * .4))
                for i in range(41)]
    b1 = bank(.50, .035, seed % 7)
    b2 = bank(.63, .02, seed % 5 + 1)
    top = [(bx - 2, by - 2), (bx + bw + 2, by - 2)]
    o.append(f'<path d="{_d(top + b1[::-1], True, 0)}" fill="{C.pat("G")}" stroke="none"/>')
    o.append(f'<path d="{_d(b1 + b2[::-1], True, 0)}" fill="{C.pat("M")}" stroke="none"/>')
    o.append(f'<path d="{_d(b2 + [(bx + bw + 2, hz + 4), (bx - 2, hz + 4)], True, 0)}" fill="{C.pat("L")}" stroke="none"/>')

    cv = C.Canvas()
    # stars: tiny white sparkles in the dark band
    for i in range(18 if not small else 7):
        sx, sy = U(rng.uniform(.03, .97)), V(rng.uniform(.03, .36))
        r = rng.choice((1.1, 1.4, 1.8)) * (1 if not small else .8)
        cv.obj([_star(sx, sy, r * 1.6, r * .45, 4, rng.uniform(-10, 10))], 0)
    # fireworks: white spikes with beads, on the dark sky
    bursts = [(.83, .19, .17), (.13, .09, .1)] if not small else [(.82, .2, .17)]
    for (u, v, rr) in bursts:
        fx, fy, R = U(u), V(v), S * rr
        n = 22 if not small else 14
        for i in range(n):
            a = 360 * i / n + rng.uniform(-4, 4)
            r1 = R * rng.uniform(.75, 1.)
            cv.obj([_spike(fx, fy, a, R * .18, r1, max(.9, R * .05))], 0)
            if not small:
                ea = math.radians(a)
                cv.obj([_circle(fx + math.cos(ea) * (r1 + 2.2), fy + math.sin(ea) * (r1 + 2.2), 1.0, 8)], 0)
        cv.obj([_circle(fx, fy, max(1.2, R * .12), 12)], .5)
    # basketball moon
    mx, my, mr = U(.31), V(.15), S * (.065 if not small else .1)
    ball = _circle(mx, my, mr, 40)
    cv.obj([ball], 1.)
    cv.hair(C.hatch_poly(ball, -45, 1.5))
    lit = _circle(mx - mr * .3, my - mr * .3, mr * .72, 30)
    cv.obj([lit], 0)
    cv.hair(C.hatch_poly(lit, -45, 3))
    seams = [[(mx - mr, my), (mx + mr, my)], [(mx, my - mr), (mx, my + mr)],
             [(mx - mr * .62 + mr * .25 * math.sin(t * math.pi / 12), my - mr * .78 + mr * 1.56 * t / 12) for t in range(13)],
             [(mx + mr * .62 - mr * .25 * math.sin(t * math.pi / 12), my - mr * .78 + mr * 1.56 * t / 12) for t in range(13)]]
    cv.obj([], 0)
    cv.line(seams)

    # --- skyline (back to front)
    base = V(.80)
    towers = [(.30, .50, .05), (.36, .40, .07), (.42, .30, .06), (.56, .34, .07), (.62, .26, .06), (.69, .44, .06)]
    for u, v, wu in sorted(towers, key=lambda t: t[1]):
        x0, x1, y0 = U(u), U(u + wu), V(v)
        poly = [(x0, base), (x0, y0), (x1, y0), (x1, base)]
        if u == .42:      # Wells Fargo: a pointed crown
            poly = [(x0, base), (x0, y0 + 6), ((x0 + x1) / 2, y0 - bh * .04), (x1, y0 + 6), (x1, base)]
        if u == .62:      # Big Pink: notched top
            poly = [(x0, base), (x0, y0), (x0 + (x1 - x0) * .3, y0 - 3), (x1, y0 - 3), (x1, base)]
        cv.obj([poly], .5)
        cv.line(C.hatch_poly(poly, 90, 1.5))
        if not small:
            for wy in range(int(y0 + 5), int(base - 3), 5):
                for wx in range(int(x0 + 3), int(x1 - 2), 4):
                    if rng.random() < .55:
                        cv.obj([_rect(wx, wy, 1.6, 2)], 0)
    # Oregon Convention Center: the long hall and its two glass spires
    hx0, hx1 = U(-.02), U(.30)
    hall = [(hx0, base), (hx0, V(.62)), (U(.04), V(.60)), (U(.26), V(.60)), (hx1, V(.63)), (hx1, base)]
    cv.obj([hall], 1.)
    cv.hair(C.hatch_poly(hall, 0, 2))
    if not small:
        for k in range(int(hx0) + 3, int(hx1) - 2, 5):
            cv.obj([_rect(k, V(.66), 2.2, bh * .06)], .5)
    for su, sv in ((.085, .17), (.205, .17)):
        sx, sw = U(su), max(5, bw * .05)
        tip = (sx + sw / 2, V(sv))
        mid = sx + sw / 2
        left = [(sx, V(.61)), (sx + sw * .18, V(.46)), tip, (mid, V(.61))]
        right = [(mid, V(.61)), tip, (sx + sw * .82, V(.46)), (sx + sw, V(.61))]
        cv.obj([left], 1.)
        cv.hair(C.hatch_poly(left, 90, 3))
        cv.hair(_clip_x([[(sx, y), (mid, y)] for y in [V(.2) + i * 4 for i in range(int((V(.6) - V(.2)) / 4))]],
                        sx + 1, mid))
        cv.obj([right], 1.)
        cv.line(C.hatch_poly(right, 90, 1.5))
        cv.heavy([[tip, (mid, V(.61))]])
    # Moda Center: drum and dome on the right
    m0, m1 = U(.72), U(1.04)
    mt = V(.58)
    dome = [(m0 + (m1 - m0) * i / 20, mt - bh * .09 * math.sin(math.pi * i / 20)) for i in range(21)]
    drum = [(m0, base)] + dome + [(m1, base)]
    cv.obj([drum], 1.)
    for j in range(1, 6):
        f = j / 6
        cv.hair([[(m0 + (m1 - m0) * i / 20, mt - bh * .09 * f * math.sin(math.pi * i / 20)) for i in range(21)]])
    cv.hair([[(m0 + (m1 - m0) * i / 12, mt - bh * .09 * math.sin(math.pi * i / 12)),
              (m0 + (m1 - m0) * (.5 + (i / 12 - .5) * .9), mt + 2)] for i in range(13)])
    body = [(m0, mt + 3), (m1, mt + 3), (m1, base), (m0, base)]
    cv.line(C.hatch_poly(body, 90, 1.5))
    cv.heavy([[(m0, mt + 3), (m1, mt + 3)]])
    if not small:
        for k in range(int(m0) + 4, int(min(m1, bx + bw)) - 2, 6):
            cv.obj([_rect(k, mt + 6, 2.4, bh * .07)], .5)

    # --- the plaza: brick courses in perspective
    pz = [(bx - 2, base), (bx + bw + 2, base), (bx + bw + 2, by + bh + ext + 2), (bx - 2, by + bh + ext + 2)]
    cv.obj([pz], 1.)
    rows = []
    y = base
    step = 1.6
    while y < by + bh + ext + 2:
        rows.append(y)
        y += step
        step *= 1.22
    cv.hair([[(bx - 2, yy), (bx + bw + 2, yy)] for yy in rows])
    vx, vy = cx, base - bh * .12
    for i, yy in enumerate(rows[:-1]):
        y2 = rows[i + 1]
        pitch = (y2 - yy) * 2.2
        off = pitch / 2 if i % 2 else 0
        xx = bx - pitch + off
        segs = []
        while xx < bx + bw + pitch:
            segs.append([(xx, yy + .3), (vx + (xx - vx) * (y2 - vy) / (yy - vy), y2 - .3)])
            xx += pitch
        cv.hair(segs)

    # --- the tree
    tb = V(.86)
    ttop = V(.10)
    th = tb - ttop
    tiers = 5 if not small else 4
    tw_half = th * .36
    tree_objs = []
    for i in range(tiers):
        f0 = i / tiers
        t_top = ttop + th * max(0, f0 - .13)
        t_bot = ttop + th * (i + 1) / tiers
        hw = tw_half * (.28 + .72 * (i + 1) / tiers)
        nsc = 4 + i * 2
        edge = []
        for k in range(nsc + 1):
            xk = cx + hw - 2 * hw * k / nsc
            edge.append((xk, t_bot - th * .02))
            if k < nsc:
                edge.append((xk - hw / nsc, t_bot + th * .035))
        poly = [(cx, t_top), (cx + hw * .55, t_top + (t_bot - t_top) * .5)] + edge + [(cx - hw * .55, t_top + (t_bot - t_top) * .5)]
        tree_objs.append((poly, t_top, t_bot, hw))
    for i, (poly, t_top, t_bot, hw) in reversed(list(enumerate(tree_objs))):
        cv.obj([poly], 1.)
        cv.hair(_clip_x(C.hatch_poly(poly, 62, 3), cx - hw * .55))
        cv.hair(_clip_x(C.hatch_poly(poly, -62, 3, 1.5), cx - hw * .05))
        cv.line(_clip_x(C.hatch_poly(poly, -62, 3), cx + hw * .35))
        if not small:
            # needles: fine ticks combed up from every drooping bough tip and down each flank
            ticks = []
            for (ax, ay), (bx_, by_) in zip(poly, poly[1:] + poly[:1]):
                L = math.hypot(bx_ - ax, by_ - ay)
                for j in range(int(L / 1.8)):
                    t = (j + .5) * 1.8 / L
                    px_, py_ = ax + (bx_ - ax) * t, ay + (by_ - ay) * t
                    dx_, dy_ = cx - px_, (t_top - py_) * .5
                    dl = math.hypot(dx_, dy_) or 1
                    ticks.append([(px_, py_), (px_ + dx_ / dl * 2.6, py_ + dy_ / dl * 2.6)])
            cv.hair(ticks)
        if i > 0:
            sh_y = tree_objs[i - 1][2]
            cv.line(_clip_y(_clip_x(C.hatch_poly(poly, 0, 1.5), cx - hw * .9, cx + hw * .9), sh_y - 1, sh_y + th * .045))
        if not small:
            gy = t_top + (t_bot - t_top) * .62
            ghw = hw * .62
            sw = [(cx - ghw + 2 * ghw * k / 16, gy - (t_bot - t_top) * .18 * (k / 16) + (t_bot - t_top) * .12 * math.sin(math.pi * k / 16)) for k in range(17)]
            cv.obj([sw + [(p[0], p[1] + 2.2) for p in sw[::-1]]], .5)
            cv.hair([[(p[0], p[1] + 1.1) for p in sw]])
    # lights
    for i in range(46 if not small else 12):
        k = rng.randrange(len(tree_objs))
        poly, t_top, t_bot, hw = tree_objs[k]
        fy = rng.uniform(.3, .9)
        yy = t_top + (t_bot - t_top) * fy
        half = hw * (.25 + .7 * fy)
        xx = cx + rng.uniform(-half, half) * .9
        r = rng.choice((1.3, 1.6, 2.0)) * (1 if not small else .8)
        if r > 1.9 and not small:
            cv.obj([_star(xx, yy, r * 2.4, r * .3, 4, 45)], 0)
        cv.obj([_circle(xx, yy, r, 10)], .5)
    # star with rays
    sx, sy = cx, ttop - th * .015
    sr = th * .07
    for i in range(16):
        L = sr * (3.2 if i % 2 == 0 else 2.1)
        cv.obj([_spike(sx, sy, 360 * i / 16 + 11.25, sr * .6, L, max(.6, sr * .07))], 0)
    st = _star(sx, sy, sr, sr * .42, 5)
    cv.obj([st], 1.)
    cv.hair([[(sx, sy), p] for p in st])
    for i in range(0, 10, 2):
        cv.hair(C.hatch_poly([(sx, sy), st[i], st[(i + 1) % 10]], 90 + 36 * i, 1.5))

    # --- the crowd, in silhouette, the dog among them
    blacks = []
    dogx = cx + bw * .07
    for row, (crowd_y, sc) in enumerate(((V(.875), .75), (V(.92), 1.))):
        xx = bx - 4 + row * bh * .02
        while xx < bx + bw + 6:
            hr = bh * rng.uniform(.018, .024) * sc * (1 if not small else 1.4)
            if row == 1 and abs(xx - dogx) < bh * .05 and not small:
                xx += bh * .07
                continue
            hy = crowd_y + rng.uniform(-1.5, 1.5)
            blacks.append(C._ell_pts(xx, hy, hr * .9, hr, 14))
            blacks.append([(xx - hr * 2.1, by + bh + ext + 3), (xx - hr * 1.9, hy + hr * 1.7), (xx - hr * 1.2, hy + hr * 1.25),
                           (xx - hr * .4, hy + hr * .8), (xx + hr * .4, hy + hr * .8), (xx + hr * 1.2, hy + hr * 1.25),
                           (xx + hr * 1.9, hy + hr * 1.7), (xx + hr * 2.1, by + bh + ext + 3)])
            if rng.random() < .3:      # a beanie with a bobble
                blacks.append(C._ell_pts(xx, hy - hr * .55, hr * 1.0, hr * .7, 12, math.pi, TAU))
                blacks.append(_circle(xx, hy - hr * 1.35, hr * .32, 8))
            if rng.random() < .15 and not small:    # a phone held up
                px_, py_ = xx + hr * 1.3, hy - hr * 2.4
                blacks.append([(xx + hr * .9, hy + hr), (px_ - .6, py_ + 2), (px_ + .6, py_ + 2), (xx + hr * 1.6, hy + hr)])
                blacks.append(_rect(px_ - 1.4, py_ - 2.4, 2.8, 4.2))
            xx += hr * rng.uniform(2.2, 2.9)
    o.append(cv.svg())
    o.append(f'<path d="{"".join(_d(p, True, .1) for p in blacks)}" fill="#000" stroke="none"/>')
    if not small:
        dv = C.Canvas()
        # the dog: sitting, seen from behind, ears up, looking up at the tree
        k = bh * .0042
        dx, dy = dogx, V(.985)
        dog = [(-7, 0), (-4.2, 0), (-4.2, -7), (-2.5, -3.5), (1, -.8), (3, 0), (9, 0), (9.2, -3), (7.5, -8),
               (3.5, -12.5), (-.5, -15.5), (-.8, -18.5), (-.2, -24), (-2.4, -21.6), (-4, -22.8), (-6.2, -22),
               (-9.6, -20.6), (-9.8, -19), (-5.4, -17.6), (-5.6, -13), (-6, -8), (-6.6, -3)]
        dog = [(dx + px * k, dy + py * k) for px, py in dog]
        dv.obj([dog], 1.)
        dv.hair(_clip_x(C.hatch_poly(dog, 70, 1.5), dx + k))
        dv.hair(_clip_y(C.hatch_poly(dog, -20, 3), dy - 15 * k))
        dv.line([[(dx + (9 + 3 * math.sin(t / 6 * 3.6)) * k, dy + (-2 - 7 * t / 6) * k) for t in range(7)]])
        pk = max(.35, bh * .0024)
        dv.obj([], 0)
        dv.line(_letter("P", dx - 14 * k, dy - 6.5 * pk, pk))
        o.append(dv.svg())
    body = "".join(o)
    return f'<clipPath id="{uid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{uid})">{body}</g>'


# ---------------------------------------------------------------------------------------------
# layouts (adapted from the house layouts so every field is engraved edge to edge)
# ---------------------------------------------------------------------------------------------
def _field_ab(w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 120)
    o.append(_stipple(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                              C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh)))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(night_scene(C._uid("bs", w, h, seed), clip, cx - rx, cy - ry, 2 * rx, 2 * ry, seed, small=True))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2.2, ry - 2.2, 64), True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.5)
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
                   max_n=9, edge=.7, cv=cv)
    cv.extend(main)
    o.append(_stipple(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg())))
    c, _, field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fa, fb = _field_ab(cw, gh + 4)
    o.append(night_scene(C._uid("ms", w, h, seed), field, cx - fa, cy - fb, 2 * fa, 2 * fb, seed, small=gh < 120))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    # the page's own back-hatching behind everything, so the crest rises from the page
    o.append(f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="url(#l3p)" stroke="none"/>')
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z'
             f'M{_n(px0)},{_n(py0)}v{_n(ph)}h{_n(pw)}v{_n(-ph)}z" fill="{C.pat("D")}" fill-rule="evenodd" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .52, ph * .64
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=8, edge=.6, cv=cv)
    cv.extend(main)
    o.append(_stipple(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg())))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fa, fb = _field_ab(cw, ch)
    pal_seed, rib_seed = rng.randrange(1 << 20), rng.randrange(1 << 20)
    bh_ = min(17, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh_, .04, rib_seed)
    rib_top = min(abs(p[0] - cx) < fa * .6 and p[1] or 1e9 for p in centre) - bh_ / 2 - 2
    sb = min(cy + fb, rib_top) - (cy - fb)
    o.append(night_scene(C._uid("ts", w, h, seed), field, cx - fa, cy - fb, 2 * fa, sb, seed, ext=cy + fb - (cy - fb + sb)))
    o.append(_stipple(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, pal_seed)))
    o.append(bsvg)
    letters = letter_curve("BIG NIGHTS OUT", centre, bh_ * .5)
    o.append(f'<path d="{"".join(_d(p, tol=0) for p in letters)}" fill="none" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, tth) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # letter the tablet, with a fine ruled field round the words
    o.append(f'<path d="M{_n(tx + 3)},{_n(ty + 3)}h{_n(tw - 5)}v{_n(tth - 5)}h{_n(-(tw - 5))}z" fill="{C.pat("L")}" stroke="none"/>')
    line = _date_line(ctx or {})
    lh = tth * .55
    lw = min(tw - 16, _text_width(line) * lh / 6)
    o.append(f'<path d="M{_n(tx + tw / 2 - lw / 2 - 4)},{_n(ty + 3.5)}h{_n(lw + 8)}v{_n(tth - 6)}h{_n(-(lw + 8))}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{"".join(_d(q, tol=0) for q in letter_line(line, tx + tw / 2 + 1, ty + tth / 2 + 1, lh, tw - 16))}" fill="none" stroke="#000" stroke-width="1"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(f'<path d="M{_n(w * .06)},{_n(fy)}h{_n(w * .88)}v{_n(fh - 2)}h{_n(-w * .88)}z" fill="#fff" stroke="none"/>')
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(_stipple(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                                  C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                                r_scale=1.15, n=2))))
        o.append(_stipple(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20))))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    _SID[0] = 0
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, _XDEFS + body)
