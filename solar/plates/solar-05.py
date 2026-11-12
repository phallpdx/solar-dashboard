"""solar-05 "A month of solar": Parker's 24.6 kW barn roof on Sauvie Island under a low November
sun whose rays are the last thirty days (a long ray for a good day, a stub for a low one), Mt. Hood
and the Columbia beyond, all set in the house acanthus frame. The ribbon carries the month's kWh,
the pedestal tablet a thirty-day calendar of suns and clouds. Easter egg: Parker's dog asleep,
curled at the barn door."""
import sys
import math
import random
import re
import datetime
import engraving_codex as C

_n, _d = C._n, C._d
PI = math.pi
CR = ' shape-rendering="crispEdges"'
MON = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


# ------------------------------------------------------------------------------------------------
# page facts: the thirty days, which were low, the month's total
# ------------------------------------------------------------------------------------------------

def _facts(ctx):
    ctx = ctx or {}
    try:
        end = datetime.date.fromisoformat(ctx.get("date", "")[:10])
    except ValueError:
        end = datetime.date(2026, 11, 11)
    days = [end - datetime.timedelta(days=29 - i) for i in range(30)]
    s = ctx.get("sample", "") or ""
    low = set()
    m = re.search(r"Low days:\s*([^.]*)", s)
    if m:
        for mm, dd in re.findall(r"([A-Z][a-z]{2})\s+(\d{1,2})", m.group(1)):
            if mm in MON:
                for d in days:
                    if d.month == MON[mm] and d.day == int(dd):
                        low.add(d)
    else:
        rng = random.Random(end.toordinal())
        low = {d for d in days if rng.random() < .25}
    k = re.search(r"Past (\d+) days:\s*([\d,]+)\s*kWh", s)
    label = f"{k.group(2)} KWH IN {k.group(1)} DAYS" if k else "A MONTH OF SUN"
    return days, [d in low for d in days], label


# ------------------------------------------------------------------------------------------------
# a small engraved roman for the ribbon (strokes on a 4 x 6 grid)
# ------------------------------------------------------------------------------------------------

_O = [(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]
_P = [(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]
GLYPH = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 4), (3.2, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.5), (2.2, 3.5)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 0), (1, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.8)], [(1.4, 2.6), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2.5, 4.5), (5, 0), (5, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [_O],
    "P": [_P],
    "R": [_P, [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1.2, 6), (2.5, 2), (3.8, 6), (5, 0)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "0": [_O],
    "1": [[(.6, 1.2), (2, 0), (2, 6)], [(.8, 6), (3.2, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1.5, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "5": [[(4, 0), (.4, 0), (0, 3), (3, 2.6), (4, 3.6), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "6": [[(3.5, 0), (1.5, 0), (0, 2), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (.5, 3)]],
    "7": [[(0, 0), (4, 0), (1.5, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3)]],
    "9": [[(3.5, 3), (1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 4), (2.5, 6), (.5, 6)]],
    ",": [[(.6, 5.4), (.6, 6.2), (0, 7.2)]],
}


def _adv(ch):
    if ch == " ":
        return 3.2
    if ch == ",":
        return 1.8
    g = GLYPH.get(ch)
    if not g:
        return 3.2
    return max(p[0] for s in g for p in s) + 1.7


def _letter_along(text, centre, cap):
    """Stroke text centred along a polyline; returns polylines."""
    s = cap / 6.
    L = [0.]
    for a, b in zip(centre, centre[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = sum(_adv(c) for c in text) * s - 1.7 * s
    u = (L[-1] - tot) / 2

    def at(t):
        t = min(max(t, 0), L[-1] - 1e-6)
        i = max(0, min(len(L) - 2, next((k for k in range(len(L) - 1) if L[k + 1] >= t), len(L) - 2)))
        f = (t - L[i]) / max(1e-6, L[i + 1] - L[i])
        a, b = centre[i], centre[i + 1]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, ang

    out = []
    for ch in text:
        g = GLYPH.get(ch)
        if g:
            w = max(p[0] for st in g for p in st) * s
            px, py, ang = at(u + w / 2)
            ca, sa = math.cos(ang), math.sin(ang)
            for st in g:
                out.append([(px + (gx * s - w / 2) * ca - (gy * s - cap / 2) * sa,
                             py + (gx * s - w / 2) * sa + (gy * s - cap / 2) * ca) for gx, gy in st])
        u += _adv(ch) * s
    return out


# ------------------------------------------------------------------------------------------------
# geometry helpers
# ------------------------------------------------------------------------------------------------

def _circ(cx, cy, r, n=40, a0=0., a1=2 * PI):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _bil(q, u, v):
    """Bilinear point in quad q = (p00 eave-left, p01 ridge-left, p11 ridge-right, p10 eave-right)."""
    a, b, c, d = q
    x = (1 - u) * ((1 - v) * a[0] + v * b[0]) + u * ((1 - v) * d[0] + v * c[0])
    y = (1 - u) * ((1 - v) * a[1] + v * b[1]) + u * ((1 - v) * d[1] + v * c[1])
    return x, y


def _cloud(cx, base, w, h, rng):
    """A cumulus: (outline, bump list)."""
    n = max(3, int(w / (h * .7)))
    bumps = []
    for i in range(n):
        t = (i + .5) / n
        r = h * (.42 + .5 * math.sin(PI * t)) * rng.uniform(.85, 1.1)
        bumps.append((cx - w / 2 + w * t, base - r * .55, r))
    pts = []
    m = 60
    x0, x1 = cx - w / 2 - h * .25, cx + w / 2 + h * .25
    for i in range(m + 1):
        x = x0 + (x1 - x0) * i / m
        y = base
        for bx, by, r in bumps:
            if abs(x - bx) < r:
                y = min(y, by - math.sqrt(r * r - (x - bx) ** 2))
        pts.append((x, min(y, base - .5)))
    pts += [(x1 - h * .3, base + h * .06), (x0 + h * .3, base + h * .06)]
    return pts, bumps


def _sky(bx, by, bw, bh, yh, sx, sy, rg):
    """Crisp ruled sky: 1 px lines high and far from the sun, 0.5 px near it, none in its glow."""
    heavy, light = [], []
    y = math.floor(by)
    top_dark = by + (yh - by) * .42
    while y < yh + 2:
        yc = y
        dy = yc - sy
        segs = [(bx - 2, bx + bw + 2)]

        def cut(segs, r):
            if abs(dy) >= r:
                return segs, []
            hw = math.sqrt(r * r - dy * dy)
            a, b = sx - hw, sx + hw
            out, inside = [], []
            for s0, s1 in segs:
                if s1 <= a or s0 >= b:
                    out.append((s0, s1))
                else:
                    if s0 < a:
                        out.append((s0, a))
                    if s1 > b:
                        out.append((b, s1))
                    inside.append((max(s0, a), min(s1, b)))
            return out, inside

        outer, mid = cut(segs, rg * 1.9)
        for s0, s1 in outer:
            (heavy if yc < top_dark else light).append((yc, s0, s1))
        for s0, s1 in mid:
            light.append((yc, s0, s1))
        y += 2
    dh = "".join(f"M{_n(a)},{_n(yc + .5)}H{_n(b)}" for yc, a, b in heavy if b - a > .5)
    dl = "".join(f"M{_n(a)},{_n(yc + .25)}H{_n(b)}" for yc, a, b in light if b - a > .5)
    o = ""
    if dh:
        o += f'<path d="{dh}" stroke="#000" stroke-width="1"{CR}/>'
    if dl:
        o += f'<path d="{dl}" stroke="#000" stroke-width=".5"{CR}/>'
    return o


# ------------------------------------------------------------------------------------------------
# the vignette: barn roof of panels, low November sun of thirty rays, Mt. Hood, the Columbia
# ------------------------------------------------------------------------------------------------

def _dog(cv, x, y, s):
    """Parker's dog, asleep, curled nose to tail (facing left)."""
    body = C._ell_pts(x, y - 3.2 * s, 7 * s, 3.6 * s, 30)
    cv.obj([body], .5)
    for k in (.72, .45):
        cv.hair(C._ell_pts(x + .6 * s, y - 3.0 * s, 7 * s * k, 3.6 * s * k, 20, PI * 1.05, PI * 1.95))
    for i in range(7):
        a = PI * (1.1 + .8 * i / 6)
        r1, r2 = .55, .95
        cv.hair([(x + 7 * s * r1 * math.cos(a), y - 3.2 * s + 3.6 * s * r1 * math.sin(a)),
                 (x + 7 * s * r2 * math.cos(a + .08), y - 3.2 * s + 3.6 * s * r2 * math.sin(a + .08))])
    cv.hair(C.hatch_poly(C._ell_pts(x, y - 2.2 * s, 6.4 * s, 2.4 * s, 20)[:-1], 0, 1.5, .25))
    # tail wrapping the front
    tail = [(x + 6.5 * s - 9 * s * t, y - .4 * s - 1.4 * s * math.sin(PI * t)) for t in [i / 10 for i in range(11)]]
    cv.line(tail)
    # head tucked on the tail, ear flopped
    hx, hy = x - 5.2 * s, y - 2.4 * s
    head = C._ell_pts(hx, hy, 2.9 * s, 2.3 * s, 20)
    cv.obj([head], .5)
    cv.hair(C.hatch_poly(head[:-1], 45, 1.5))
    ear = [(hx + .2 * s, hy - 2 * s), (hx + 2.6 * s, hy - 1.2 * s), (hx + 1.8 * s, hy + 1.2 * s)]
    cv.obj([ear], .5)
    cv.line([(hx + .8 * s, hy - 1.2 * s), (hx + 1.9 * s, hy + .6 * s)])
    cv.heavy([(hx - 2.7 * s, hy + .2 * s), (hx - 2.4 * s, hy + .5 * s)])  # nose


def _scene(bx, by, bw, bh, clip_d, facts, seed, uid):
    days, low, _ = facts
    rng = random.Random(seed)
    S = max(.2, min(bw, bh) / 200.)
    small = S < .45
    yh = by + bh * .55
    R = max(4., 18 * S)
    sx, sy = bx + bw * .34, yh - R * 1.15 - 4 * S
    rg = R * (2.7 if not small else 2.4)
    o = [f'<clipPath id="{uid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{uid})">',
         f'<path d="M{_n(bx - 2)},{_n(by - 2)}h{_n(bw + 4)}v{_n(bh + 4)}h{_n(-bw - 4)}z" fill="#fff" stroke="none"/>',
         _sky(bx, by, bw, bh, yh, sx, sy, rg)]
    cv = C.Canvas()

    # sun: glow, thirty rays (one a day: long for a good day, a stub for a low one)
    n = len(days)
    a0, a1 = math.radians(186), math.radians(354)
    star = []
    da = (a1 - a0) / (n - 1)
    for i in range(n):
        rr = (rg * .98 if not low[i] else R * 1.25 + (rg - R * 1.25) * .32 + 2 * (1.6 * S + 1) + 2) + 1.5
        a = a0 + da * i
        for t in (-.5, -.2, .2, .5):
            r2 = rr if abs(t) < .3 else (rr + R * 1.6) / 2 if not low[i] else rr
            star.append((sx + r2 * math.cos(a + t * da), sy + r2 * math.sin(a + t * da)))
    star += [(sx + R * 1.3 * math.cos(a), sy + R * 1.3 * math.sin(a)) for a in [a1 + .5 * da + k * .2 for k in range(int((2 * PI - (a1 - a0) - da) / .2) + 1)]]
    cv.obj([star], 0)
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        ca, sa = math.cos(a), math.sin(a)
        if low[i]:
            r1 = R * 1.25 + (rg - R * 1.25) * .32
            cv.hair([(sx + R * 1.2 * ca, sy + R * 1.2 * sa), (sx + r1 * ca, sy + r1 * sa)])
            if not small:  # a little cloud-puff at the end of a low day's ray
                cv.obj([_circ(sx + (r1 + 1.6 * S + 1) * ca, sy + (r1 + 1.6 * S + 1) * sa, 1.2 + 1.1 * S, 10)[:-1]], .5)
                cv.obj([], 0)
        else:
            r1 = rg * .96
            wdg = .045 if not small else .03
            tri = [(sx + R * 1.18 * math.cos(a - wdg), sy + R * 1.18 * math.sin(a - wdg)),
                   (sx + r1 * ca, sy + r1 * sa),
                   (sx + R * 1.18 * math.cos(a + wdg), sy + R * 1.18 * math.sin(a + wdg))]
            cv.line([(sx + R * 1.18 * ca, sy + R * 1.18 * sa), (sx + r1 * ca, sy + r1 * sa)])
            if not small:
                cv.hair(tri)
        if i < n - 1 and not small:  # short flame between rays
            b = a + (a1 - a0) / (n - 1) / 2
            r2 = R * (1.55 if i % 2 else 1.8)
            cv.hair([(sx + R * 1.2 * math.cos(b), sy + R * 1.2 * math.sin(b)), (sx + r2 * math.cos(b), sy + r2 * math.sin(b))])
    disc = _circ(sx, sy, R, 48)[:-1]
    cv.obj([disc], 1.5 if not small else 1.)
    for k in range(1, 5):
        rr = R - 1.5 - 2 * (k - 1)
        if rr > R * .55:
            cv.hair(_circ(sx, sy, rr, 40, PI * .1, PI * .9 if k > 2 else PI * 1.9))
    cv.hair(C.hatch_poly(_circ(sx, sy, R * .62, 30)[:-1], 0, 3, .25))

    # clouds of the low days
    if not small:
        for (cxf, cyf, wf) in ((.06, .30, .34), (.86, .40, .30)):
            pts, bumps = _cloud(bx + bw * cxf, by + (yh - by) * cyf + 10 * S, bw * wf, 15 * S, rng)
            cv.obj([pts], .5)
            base = by + (yh - by) * cyf + 10 * S
            for bxx, byy, r in bumps:
                cv.hair(C._ell_pts(bxx + r * .1, byy + r * .1, r * .75, r * .75, 20, PI * .05, PI * .75))
            under = [(p[0], max(p[1], base - 6 * S)) for p in pts[:61]] + [pts[-2], pts[-1]]
            cv.hair(C.hatch_poly(under, 0, 2, .25))
            cv.hair(C.hatch_poly(pts, 0, 3, 1.25))
            cv.hair(C.hatch_poly(under, 45, 3))

    # Mt. Hood
    mx, mtop = bx + bw * .77, yh - bh * .27
    hw = bw * .27
    mpts = [(mx - hw, yh + 4), (mx - hw * .55, yh - (yh - mtop) * .35), (mx - hw * .22, yh - (yh - mtop) * .78),
            (mx - hw * .05, mtop + 1), (mx + hw * .02, mtop), (mx + hw * .07, mtop + 1.5 * S),
            (mx + hw * .25, yh - (yh - mtop) * .74), (mx + hw * .6, yh - (yh - mtop) * .3), (mx + hw, yh + 4)]
    cv.obj([mpts], .5)
    snow = mtop + (yh - mtop) * .5
    # shaded east face
    east = [(mx + hw * .02, mtop), (mx + hw * .07, mtop + 1.5 * S), (mx + hw * .25, yh - (yh - mtop) * .74),
            (mx + hw * .6, yh - (yh - mtop) * .3), (mx + hw, yh + 4), (mx + hw * .1, yh + 4)]
    cv.hair(C.hatch_poly(east, 45, 2))
    if not small:
        cv.hair(C.hatch_poly(east, -45, 3))
    # gullies down the snow on the lit face
    cv.hair(C.hatch_poly([(mx - hw * .55, yh - (yh - mtop) * .35), (mx - hw * .22, yh - (yh - mtop) * .78),
                           (mx - hw * .05, mtop + 1), (mx + hw * .02, mtop), (mx + hw * .02, yh), (mx - hw * .55, yh)], -60, 3))
    for k in range(11):
        t = (k + .5) / 11
        x0 = mx - hw * .04 + hw * .1 * t
        x1 = mx - hw * (.62 - .7 * t)
        cv.hair([(x0, mtop + 2 * S), (x0 + (x1 - x0) * .4 + rng.uniform(-1, 1) * S, mtop + (snow - mtop) * .55),
                 (x1, snow + rng.uniform(-2, 2) * S)])
    # forested flanks below the snow line
    flank = [(mx - hw, yh + 4), (mx - hw * .55, yh - (yh - mtop) * .35)]
    jag = []
    for k in range(13):
        t = k / 12
        jag.append((mx - hw * .55 + hw * 1.15 * t, snow + (yh - snow) * .25 * math.sin(t * 9) ** 2 + (3 * S if k % 2 else -2 * S)))
    flank = [(mx - hw, yh + 4)] + [p for p in jag] + [(mx + hw, yh + 4)]
    cv.hair(C.hatch_poly(flank, -30, 3))

    # treeline of cottonwoods and firs along the far bank
    tl = []
    x = bx - 4
    while x < bx + bw + 6:
        if rng.random() < .3:
            hgt = rng.uniform(8, 14) * S
            tl += [(x, yh), (x + 2.5 * S, yh - hgt), (x + 5 * S, yh)]
            x += 5 * S
        else:
            r = rng.uniform(3.5, 7) * S
            tl += [(x + r - r * math.cos(PI * t / 8), yh - r * .9 * math.sin(PI * t / 8) - 2 * S) for t in range(9)]
            x += 2 * r * .85
    tree = [(bx - 4, yh + 6 * S)] + tl + [(bx + bw + 6, yh + 6 * S)]
    cv.obj([tree], .5)
    cv.hair(C.hatch_poly(tree, 45, 2))
    cv.hair(C.hatch_poly(tree, -45, 3))

    # the Columbia, with the sun's road laid on it
    ry0, ry1 = yh + 6 * S, yh + 18 * S
    river = [(bx - 4, ry0), (bx + bw + 4, ry0), (bx + bw + 4, ry1), (bx - 4, ry1)]
    cv.obj([river], 0)
    yy = math.floor(ry0) + 1
    while yy < ry1:
        x = bx - 4
        while x < bx + bw + 4:
            near = abs(x - sx) < R * (.8 + 1.5 * (yy - ry0) / max(1, ry1 - ry0))
            seg = rng.uniform(2, 5) * S + (1 if near else rng.uniform(14, 40) * S)
            gap = rng.uniform(1.5, 2.5) * (2.2 if near else 1) * max(S, .5)
            cv.hair([(x, yy + .25), (x + seg, yy + .25)])
            x += seg + gap
        yy += 2
    cv.line([(bx - 4, ry0), (bx + bw + 4, ry0)])

    # Sauvie Island fields: distant ruled, then furrows running to the sun
    ft = ry1
    bot = by + bh + 2
    field = [(bx - 4, ft), (bx + bw + 4, ft), (bx + bw + 4, bot), (bx - 4, bot)]
    cv.obj([field], .5)
    step = max(4., 10 * S)
    t0 = 3.2 / step
    yf = yh + (bot - yh) * t0
    if yf > ft:
        cv.hair(C.hatch_poly([(bx - 4, ft), (bx + bw + 4, ft), (bx + bw + 4, yf), (bx - 4, yf)], 0, 2, .25))
    span = bw * 3
    k = 0
    xb = sx - span / 2
    while xb < sx + span / 2:
        p0 = (sx + (xb - sx) * t0, max(yf, ft))
        t1 = (max(yf, ft) - yh) / (bot - yh)
        p0 = (sx + (xb - sx) * t1, yh + (bot - yh) * t1)
        (cv.line if k % 2 == 0 else cv.hair)([p0, (xb, bot)])
        xb += step
        k += 1

    # the barn and its 24.6 kW roof
    x0, x1, xg0 = bx + bw * .47, bx + bw * 1.04, bx + bw * .33
    xa = bx + bw * .40
    yg, ye, yr = yh + bh * .31, yh + bh * .11, yh - bh * .11
    yg2, ye2, yr2 = yg - bh * .03, ye - bh * .01, yr + bh * .02
    gable = [(xg0, yg - bh * .015), (xg0, ye + bh * .01), (xa, yr), (x0, ye), (x0, yg)]
    wall = [(x0, ye), (x1, ye2), (x1, yg2), (x0, yg)]
    roof = [(x0, ye), (xa, yr), (x1, yr2), (x1, ye2)]
    # cast shadow on the field to the right/front
    shadow = [(xg0 - 2 * S, yg - bh * .01), (x0, yg), (x1, yg2), (x1, yg2 + 9 * S), (x0 + 6 * S, yg + 9 * S), (xg0 + 4 * S, yg + 5 * S)]
    cv.obj([shadow], 0)
    cv.hair(C.hatch_poly(shadow, 45, 1.5))
    # gable end, in shade: vertical boards and cross-hatch
    cv.obj([gable], 1.)
    cv.hair(C.hatch_poly(gable, 90, 2))
    cv.hair(C.hatch_poly(gable, -45, 3))
    if not small:
        hl = [(xg0 + (x0 - xg0) * .3, ye - bh * .05), (xg0 + (x0 - xg0) * .7, ye - bh * .055),
              (xg0 + (x0 - xg0) * .7, ye + bh * .03), (xg0 + (x0 - xg0) * .3, ye + bh * .032)]
        cv.obj([hl], 1.)
        cv.hair([hl[0], hl[2]])
        cv.hair([hl[1], hl[3]])
        cv.hair(C.hatch_poly(hl, 0, 3, .25))
    # long wall, lit: board and batten with the eave's shadow
    cv.obj([wall], 1.)
    nb = int((x1 - x0) / 3)
    for i in range(1, nb):
        t = i / nb
        cv.hair([_bil((wall[0], wall[0], wall[1], wall[1]), t, 0), _bil((wall[3], wall[3], wall[2], wall[2]), t, 0)])
    eav = [wall[0], wall[1], (x1, ye2 + bh * .035), (x0, ye + bh * .04)]
    cv.hair(C.hatch_poly(eav, 45, 1.5))
    # sliding doors and windows
    if not small:
        def wq(u0, u1, v0, v1):
            return [_bil((wall[0], wall[3], wall[2], wall[1]), u, v) for u, v in ((u0, v0), (u0, v1), (u1, v1), (u1, v0))]
        door = wq(.14, .34, .3, 1.)
        cv.obj([door], 1.)
        mid = [_bil((door[0], door[1], door[2], door[3]), .5, 0), _bil((door[0], door[1], door[2], door[3]), .5, 1)]
        for a, b in ((door[0], door[2]), (door[1], door[3])):
            cv.line([a, b])
        cv.hair(mid)
        cv.hair(C.hatch_poly(door, 90, 3))
        for u in (.48, .64, .80):
            win = wq(u, u + .07, .32, .58)
            cv.obj([win], 1.)
            cv.hair(C.hatch_poly(win, 0, 1.5, .25))
    # roof, with the array
    cv.obj([roof], 1.)
    for i in range(1, 60):
        cv.hair([_bil(roof, i / 60, 0), _bil(roof, i / 60, .06)])
    cols = max(6, int((x1 - x0) / (13 * S)))
    rows = 3 if not small else 2
    for r in range(rows):
        for c in range(cols):
            u0 = .03 + .95 * c / cols
            u1 = u0 + .95 / cols - .012
            v0 = .09 + .84 * r / rows
            v1 = v0 + .84 / rows - .03
            pq = [_bil(roof, u0, v0), _bil(roof, u0, v1), _bil(roof, u1, v1), _bil(roof, u1, v0)]
            cv.obj([pq], .5)
            glint = abs((u0 + u1) / 2 - .1 - .08 * r) < .09
            if not glint:
                cv.hair(C.hatch_poly(pq, 45, 1.5 if not small else 2))
            else:
                cv.hair(C.hatch_poly(pq, 45, 3))
            if not small:
                cv.hair([_bil(roof, (u0 + u1) / 2, v0), _bil(roof, (u0 + u1) / 2, v1)])
    cv.heavy([gable[2], gable[3]])
    cv.heavy([(x0, ye), (x1, ye2)])
    cv.line([(xa, yr), (x1, yr2)])

    # Parker's dog, asleep at the barn door
    if not small:
        _dog(cv, x0 + (x1 - x0) * .20, yg + 2 * S, max(1., S * 1.35))
    o.append(cv.svg())
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# the calendar tablet: thirty days as suns and clouds
# ------------------------------------------------------------------------------------------------

def _calendar(tx, ty, tw, th, facts):
    days, low, _ = facts
    cv = C.Canvas()
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z" fill="{C.pat("L")}" stroke="none"/>']
    n = len(days)
    cw = (tw - 6) / n
    r = min(cw * .36, th * .3)
    cy = ty + th / 2 + .5
    for i, (d, lo) in enumerate(zip(days, low)):
        cx = tx + 3 + cw * (i + .5)
        if lo:
            pts, bumps = _cloud(cx, cy + r * .55, r * 2.0, r * 1.25, random.Random(i))
            cv.obj([pts], .5)
            cv.hair(C.hatch_poly([(p[0], max(p[1], cy)) for p in pts], 0, 1.5, .25))
        else:
            cv.obj([_circ(cx, cy, r * .55, 16)[:-1]], 1.)
            for k in range(8):
                a = PI * k / 4
                cv.hair([(cx + r * .75 * math.cos(a), cy + r * .75 * math.sin(a)), (cx + r * 1.15 * math.cos(a), cy + r * 1.15 * math.sin(a))])
        if d.day == 1 and i:
            xs = cx - cw / 2
            cv.obj([], 0)
            cv.line([(xs, ty + 2), (xs, ty + th - 1)])
    o.append(cv.svg())
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# layouts (from the house frame_plate, with the field filled, no blank paper, page-specific parts)
# ------------------------------------------------------------------------------------------------

def _crest_sun(cx, cy, r):
    """A rayed sun set into the crest's calyx: flame rays alternating with straight ones."""
    cv = C.Canvas()
    cv.obj([_circ(cx, cy, r * 1.9, 40)[:-1]], 0)
    for k in range(24):
        a = 2 * PI * k / 24
        r2 = r * (1.85 if k % 2 == 0 else 1.45)
        if k % 2 == 0:
            cv.line([(cx + r * 1.1 * math.cos(a), cy + r * 1.1 * math.sin(a)), (cx + r2 * math.cos(a), cy + r2 * math.sin(a))])
        else:
            cv.hair([(cx + r * 1.1 * math.cos(a + .05 * math.sin(t * 9)) * (1 + t * .0), cy + r * (1.1 + t * .35) * math.sin(a + .05 * math.sin(t * 9))) for t in []] or
                    [(cx + r * (1.1 + .35 * t) * math.cos(a + .06 * math.sin(t * 6)), cy + r * (1.1 + .35 * t) * math.sin(a + .06 * math.sin(t * 6))) for t in [i / 6 for i in range(7)]])
    cv.obj([_circ(cx, cy, r, 32)[:-1]], 1.)
    cv.hair(_circ(cx, cy, r - 2, 28))
    cv.hair(C.hatch_poly(_circ(cx, cy, r - 2.5, 24)[:-1], 0, 2, .25))
    return cv.svg()


def _cart_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _short(w, h, seed, facts):
    o = [C.dark_ground((0, 0, w, h), "L")]
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("sb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(_scene(cx - rx, cy - ry - 1, 2 * rx, 2 * ry + 4, fd, facts, seed, C._uid("sv", w, h)))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def _medium(w, h, seed, facts, density=1.):
    rng = random.Random(seed)
    o = [C.dark_ground((0, 0, w, h), "L")]
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
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _cart_field(cx, cy, cw, gh + 4)
    o.append(_scene(fx, fy, fw, fh, fd, facts, seed, C._uid("mv", w, h)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed, facts, density=1.):
    rng = random.Random(seed)
    o = [C.dark_ground((0, 0, w, h), "L")]
    o.append(C.bead_moulding(0, 3, w, 1.5))
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .68
    cx, cy = w / 2, py0 + ph * .47
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .145, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _cart_field(cx, cy, cw, ch)
    o.append(_scene(fx, fy, fw, fh, fd, facts, seed, C._uid("tv", w, h)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    o.append(_crest_sun(cx, cy - ch / 2 + 2, min(11., ch * .045 + 3)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    letters = _letter_along(facts[2], centre, min(8., bh * .52))
    o.append(f'<path d="{"".join(_d(p, tol=0) for p in letters)}" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_calendar(tx, ty, tw, th, facts))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    facts = _facts(ctx)
    if h < 110:
        body = _short(w, h, seed, facts)
    elif h <= 260:
        body = _medium(w, h, seed, facts)
    else:
        body = _tall(w, h, seed, facts)
    return C.svg_doc(w, h, body)
