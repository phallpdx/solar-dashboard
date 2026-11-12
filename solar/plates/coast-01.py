"""coast-01 (Surf report: "Should you paddle out?") - the master plate.

The subject is the morning's call on the north Oregon coast: a big W groundswell wall breaking
left under Tillamook Head, its lip throwing over into a black barrel and shattering into acanthus
claws, a surfer drawing a line down the face, Terrible Tilly (Tillamook Rock light) on the horizon,
and the wet cobblestones of Seaside Cove in the foreground. Today's best break is lettered on the
ribbon and the Clatsop Spit buoy reading on the pedestal tablet. The top moulding is a Vitruvian
wave scroll (running dog) instead of the house egg-and-dart.
Easter egg: a great blue heron from Sauvie Island standing on the cobbles, fishing the wash.
"""
import sys
import math
import random
import re
import datetime
import engraving_codex as C
import engraving_morning as M

_n, _d, pat = C._n, C._d, C.pat
PI, TAU = math.pi, 2 * math.pi


# ----------------------------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------------------------

def spline(pts, n=8):
    """Catmull-Rom through pts."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def resample(pl, step=1.):
    out = [pl[0]]
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / step))
        for i in range(1, k + 1):
            out.append((a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k))
    return out


def clip_in(pl, poly, step=1.4):
    """Runs of polyline pl that lie inside poly."""
    runs, cur = [], []
    for p in resample(pl, step):
        if inside(p, poly):
            cur.append(p)
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
    if len(cur) > 1:
        runs.append(cur)
    return runs


def shift(pl, dx, dy):
    return [(x + dx, y + dy) for x, y in pl]


def offset(pl, d):
    """Offset an open polyline by d along its left normal."""
    out = []
    n = len(pl)
    for i in range(n):
        a, b = pl[max(0, i - 1)], pl[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        out.append((pl[i][0] - ty / L * d, pl[i][1] + tx / L * d))
    return out


def ribbon(pl, w0, w1):
    """Closed outline of a tapering band along pl, half-width w0 -> w1."""
    n = len(pl)
    L, R = [], []
    for i in range(n):
        a, b = pl[max(0, i - 1)], pl[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        w = w0 + (w1 - w0) * i / (n - 1)
        L.append((pl[i][0] - ty / l * w, pl[i][1] + tx / l * w))
        R.append((pl[i][0] + ty / l * w, pl[i][1] - tx / l * w))
    return L + R[::-1]


def ell(cx, cy, rx, ry, n=24, a0=0., a1=TAU, rot=0.):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def solid(polys):
    return "".join(_d(p, True, .1) for p in polys if len(p) > 2)


# ----------------------------------------------------------------------------------------------
# engraved lettering (stroke capitals from engraving_morning, plus the letters this page needs)
# ----------------------------------------------------------------------------------------------

G = dict(M._G)
G.update({
    "S": (5, [("s", [(4.4, 1.2), (3, 0), (1.3, .2), (.5, 1.8), (1.5, 3.4), (3.4, 4.3), (4.6, 5.9), (3.9, 7.6),
                     (2.1, 8), (.3, 6.8)])]),
    "U": (5.6, [("l", [(0, 0), (1.8, 0)]), ("l", [(3.8, 0), (5.6, 0)]),
                ("s", [(.9, 0), (.9, 5.4), (1.6, 7.4), (2.8, 8), (4, 7.4), (4.7, 5.4), (4.7, 0)])]),
    "B": (5.2, [("l", [(0, 0), (1, 0), (1, 8), (0, 8)]),
                ("s", [(1, 0), (3.2, .1), (4.3, 1.1), (4.2, 2.9), (3, 3.8), (1, 3.9)]),
                ("s", [(1, 3.9), (3.4, 4), (4.8, 5.3), (4.5, 7.1), (3.2, 8), (1, 8)])]),
    "K": (5.4, [("l", [(1, 0), (1, 8)]), ("l", [(4.8, 0), (1, 4.8)]), ("l", [(2.4, 3.2), (4.9, 8)]),
                ("l", [(0, 0), (2, 0)]), ("l", [(0, 8), (2, 8)]), ("l", [(3.9, 0), (5.6, 0)]), ("l", [(4, 8), (5.8, 8)])]),
    "Y": (5.4, [("l", [(.3, 0), (2.7, 4.2), (5.1, 0)]), ("l", [(2.7, 4.2), (2.7, 8)]), ("l", [(1.6, 8), (3.8, 8)]),
                ("l", [(-.4, 0), (1.2, 0)]), ("l", [(4.2, 0), (5.8, 0)])]),
    "J": (4.4, [("s", [(3.3, 0), (3.3, 5.8), (2.6, 7.6), (1.4, 8), (.3, 7)]), ("l", [(2.2, 0), (4.4, 0)])]),
})


def glyphs(s):
    out, x = [], 0.
    for ch in s:
        adv, strokes = G.get(ch, G[" "])
        for kind, pts in strokes:
            q = M._spline(pts, False, 4) if kind == "s" else list(pts)
            out.append([(x + px, py) for px, py in q])
        x += adv + 1.25
    return out, x - 1.25


def text_flat(s, cx, cy, h):
    gl, wd = glyphs(s)
    k = h / 8
    return [[(cx + (px - wd / 2) * k, cy + (py - 4) * k) for px, py in g] for g in gl], wd * k


def text_on(s, centre, h):
    """Letters set along a curve (list of points), centred, tops toward -normal (up)."""
    gl, wd = glyphs(s)
    k = h / 8
    S = [0.]
    for a, b in zip(centre, centre[1:]):
        S.append(S[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = S[-1]
    s0 = tot / 2 - wd * k / 2

    def at(sv):
        sv = min(max(sv, 0), tot - 1e-6)
        i = max(0, min(len(S) - 2, next(j for j in range(len(S) - 1) if S[j + 1] >= sv)))
        t = (sv - S[i]) / ((S[i + 1] - S[i]) or 1)
        a, b = centre[i], centre[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    out = []
    for g in gl:
        q = []
        for px, py in g:
            (x, y), (tx, ty) = at(s0 + px * k)
            yy = (py - 4) * k
            q.append((x - ty * yy, y + tx * yy))
        out.append(q)
    return out, wd * k


# ----------------------------------------------------------------------------------------------
# page facts from today's text
# ----------------------------------------------------------------------------------------------

def facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    best = re.search(r"Best bet[^:]*:\s*([A-Z][A-Za-z .'/]+?),", s)
    buoy = re.search(r"Buoy waves\s*([\d.]+)\s*ft\s*\S\s*(\d+)\s*s\s*\S\s*([NSEW]{1,3})", s, re.I)
    water = re.search(r"Water\s*(\d+)\s*°", s, re.I)
    name = (best.group(1).strip() if best else "Seaside Cove").upper()
    name = "".join(c for c in name if c in G)
    tab = []
    if buoy:
        tab.append(f"{buoy.group(1)} FT · {buoy.group(2)} S · {buoy.group(3).upper()}")
    if water:
        tab.append(f"WATER {water.group(1)}°")
    tablet = "  ·  ".join(tab) or "CLATSOP SPIT"
    tablet = "".join(c for c in tablet if c in G)
    period = int(buoy.group(2)) if buoy else 12
    return name, tablet, period


def moon_phase(date):
    try:
        d = datetime.datetime.fromisoformat(date[:10]) + datetime.timedelta(hours=16)
    except Exception:
        d = datetime.datetime(2026, 11, 11, 16)
    days = (d - datetime.datetime(2000, 1, 6, 18, 14)).total_seconds() / 86400
    return (days / 29.530588) % 1.


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def hatch(cv, poly, ang, pitch, phase=0., w=.5):
    ls = C.hatch_poly(poly, ang, pitch, phase)
    (cv.hair if w == .5 else cv.line)(ls)


def scene(X, Y, W, H, seed, lvl, date="", period=12):
    """Engraved coast inside the box (it is clipped by the caller to its field). lvl 0 tiny,
    1 medium, 2 tall. Returns svg fragment."""
    rng = random.Random(seed)
    P = lambda u, v: (X + u * W, Y + v * H)
    Ps = lambda pts: [P(u, v) for u, v in pts]
    hz = .40 if lvl else .46
    o = []

    # ---- sky ------------------------------------------------------------------------------
    sky = C.Canvas()
    sk = Ps([(-.02, -.02), (1.02, -.02), (1.02, hz + .01), (-.02, hz + .01)])
    sky.obj([sk], 0)
    yb = Y + hz * H
    y = Y - 1
    while y < yb:
        f = (y - Y) / (hz * H)
        y += 1.5 if f < .25 else 2 if f < .6 else 3
        sky.hair([(X - 2, y), (X + W + 2, y)])
    # clouds: white cumulus banks, shaded underneath
    if lvl:
        for cu, cvv, cw in ((.16, .2, .24), (.8, .27, .28), (.42, .09, .2)):
            if lvl < 2 and cvv < .1:
                continue
            cx, cy, ww = X + cu * W, Y + cvv * H, cw * W
            crng = random.Random(seed + int(cu * 100))
            k = 5
            rads = [ww / k * crng.uniform(.6, 1.) * (1.4 - .8 * abs(i - (k - 1) / 2) / k) for i in range(k)]
            top = [(cx - ww / 2, cy)]
            for i in range(k):
                bx = cx - ww / 2 + ww * (i + .5) / k
                r = rads[i]
                top += ell(bx, cy - r * .35, r, r * .8, 10, PI * 1.05, PI * 1.95)
            top += [(cx + ww / 2, cy)]
            sky.obj([top], 1.)
            for i in range(k):
                bx = cx - ww / 2 + ww * (i + .5) / k
                r = rads[i]
                for q in (.25, .45):
                    sky.hair(clip_in(ell(bx + r * .1, cy - r * .35 + r * q * .4, r * (1 - q), r * .8 * (1 - q), 10, PI * .1, PI * .9), top))
            for ln in C.hatch_poly(top, 0, 2, .5):
                for rr in clip_in(ln, [(cx - ww, cy - ww * .04), (cx + ww, cy - ww * .04), (cx + ww, cy + 2), (cx - ww, cy + 2)]):
                    sky.hair(rr)
        # gulls
        for gx, gy, gs in ((.3, .12, 1.), (.36, .16, .8), (.27, .19, .7)):
            x0, y0 = P(gx, gy)
            g = max(2., W * .018) * gs
            sky.line([(x0 - g, y0 - g * .2), (x0 - g * .5, y0 - g * .45), (x0, y0), (x0 + g * .5, y0 - g * .45), (x0 + g, y0 - g * .2)])
    # moon by date
    ph = moon_phase(date)
    if lvl and .1 < ph < .9:
        mr = max(4., min(W, H) * .045)
        mx, my = X + W * .62, Y + H * .1
        disc = ell(mx, my, mr, mr, 28)
        sky.obj([disc[:-1]], 1.)
        # dark part: limb on the dark side + the terminator
        sg = 1 if ph < .5 else -1
        kc = math.cos(TAU * ph) * sg
        shade = [(mx - sg * mr * math.cos(a), my + mr * math.sin(a)) for a in [-PI / 2 + PI * i / 24 for i in range(25)]]
        shade += [(mx + sg * mr * kc * math.cos(a), my + mr * math.sin(a)) for a in [PI / 2 - PI * i / 24 for i in range(25)]]
        if abs(ph - .5) > .03:
            hatch(sky, shade, 0, 1.5)
            hatch(sky, shade, 90, 3)
    o.append(sky.svg())

    # ---- headland, the rock, the sea ---------------------------------------------------------
    cv = C.Canvas()
    # Tillamook Head, left, with a spruce ridge
    ridge = [(-.03, .12), (.05, .10), (.12, .12), (.2, .17), (.27, .23), (.33, .30), (.37, .35), (.40, hz)]
    if not lvl:
        ridge = [(-.03, .26), (.1, .25), (.2, .3), (.3, .38), (.36, hz)]
    rp = spline(Ps(ridge), 10)
    top = []
    tree = max(2.5, H * .03)
    for i, (x, y) in enumerate(rp):
        top.append((x, y))
        if lvl and i % 3 == 1 and y < Y + H * (hz - .05):
            s = tree * rng.uniform(.7, 1.15)
            top += [(x + s * .3, y - s * .4), (x + s * .15, y - s * .4), (x + s * .4, y - s * .9),
                    (x + s * .25, y - s * .9), (x + s * .5, y - s * 1.5), (x + s * .75, y - s * .9),
                    (x + s * .6, y - s * .9), (x + s * .85, y - s * .4), (x + s * .7, y - s * .4), (x + s, y)]
    head = top + [P(.42, hz + .005), P(-.03, hz + .005)]
    cv.obj([head], 1.)
    hatch(cv, head, 45, 2)
    lower = [P(-.03, .22), P(.2, .26), P(.42, hz + .01), P(-.03, hz + .01)] if lvl else [P(-.03, .33), P(.36, hz + .01), P(-.03, hz + .01)]
    for ln in C.hatch_poly(head, -45, 2):
        for r in clip_in(ln, lower):
            cv.hair(r)
    # cliff face where the head drops to the sea
    for i in range(6):
        x0 = X + W * (.33 + .012 * i)
        cv.hair(clip_in([(x0, Y + H * (hz - .12)), (x0 + 1, Y + H * hz)], head))
    # Tillamook Rock with its lighthouse (Terrible Tilly)
    if lvl:
        rx, ry = X + W * .9, Y + H * hz
        rw, rh = W * .055, H * .03
        rock = [(rx - rw / 2, ry), (rx - rw * .35, ry - rh * .6), (rx - rw * .1, ry - rh), (rx + rw * .2, ry - rh * .9),
                (rx + rw * .45, ry - rh * .3), (rx + rw / 2, ry)]
        cv.obj([rock], 1.)
        hatch(cv, rock, 50, 1.5)
        bw_, bh_ = rw * .35, rh * .55
        house = [(rx - bw_ / 2, ry - rh * .9), (rx + bw_ / 2, ry - rh * .9), (rx + bw_ / 2, ry - rh * .9 - bh_), (rx - bw_ / 2, ry - rh * .9 - bh_)]
        cv.obj([house], .5)
        hatch(cv, house, 90, 1.5)
        th = rh * 1.3
        tower = [(rx - 1.2, ry - rh * .9 - bh_), (rx + 1.2, ry - rh * .9 - bh_), (rx + .9, ry - rh * .9 - bh_ - th), (rx - .9, ry - rh * .9 - bh_ - th)]
        cv.obj([tower], .5)
        cv.line([(rx, ry - rh * .9 - bh_ - th - 2.2), (rx, ry - rh * .9 - bh_ - th)])
    # the sea: broken ruled lines, closer at the horizon
    sea = Ps([(-.03, hz), (1.03, hz), (1.03, 1.03), (-.03, 1.03)])
    cv.obj([sea], 0)
    cv.line([P(-.03, hz), P(1.03, hz)])
    y = Y + hz * H + 1.5
    while y < Y + H + 2:
        f = (y - Y - hz * H) / (H * (1 - hz))
        x = X - 2 - rng.uniform(0, 6)
        while x < X + W + 2:
            L = rng.uniform(10, 40) * (1 + f)
            cv.hair([(x, y), (x + L, y + rng.uniform(-.2, .2))])
            x += L + rng.uniform(1.5, 3.5)
        y += 1.5 if f < .2 else 2
    # distant swell lines: the period sets their spacing
    nsw = 3 if lvl else 1
    for k in range(nsw):
        v = hz + .035 + k * (.04 + .002 * period)
        amp = H * (.006 + .004 * k)
        crest = [(X - 2 + W * t / 60, Y + v * H - amp * math.sin(t / 60 * TAU * 2.2 + k)) for t in range(61)]
        band = crest + [(X + W + 2, Y + v * H + amp * 4), (X - 2, Y + v * H + amp * 4)]
        cv.obj([crest + [(X + W + 2, Y + v * H + amp * 3), (X - 2, Y + v * H + amp * 3)]], 0)
        cv.line(crest)
        for j in range(1, 4):
            cv.hair(shift(crest, 0, j * 1.5 + .5))
    o.append(cv.svg())

    # ---- the breaker ---------------------------------------------------------------------------
    wv = C.Canvas()
    if lvl:
        back = [(1.04, .53), (.94, .5), (.84, .43), (.73, .31), (.62, .23), (.52, .2), (.43, .22), (.36, .28),
                (.32, .36), (.32, .44), (.36, .47), (.40, .45)]
        under = [(.40, .45), (.42, .39), (.46, .33), (.52, .30), (.57, .31)]
        face = [(.57, .31), (.59, .40), (.56, .50), (.49, .58), (.38, .64), (.24, .68), (.1, .71), (-.04, .72)]
    else:
        back = [(1.04, .62), (.9, .55), (.78, .44), (.66, .33), (.55, .27), (.45, .27), (.37, .32), (.33, .40),
                (.33, .48), (.37, .51), (.41, .49)]
        under = [(.41, .49), (.44, .42), (.49, .37), (.56, .36)]
        face = [(.56, .36), (.58, .46), (.53, .56), (.44, .63), (.3, .69), (.12, .73), (-.04, .75)]
    B = spline(Ps(back), 8)
    U = spline(Ps(under), 6)
    F = spline(Ps(face), 8)
    body = B + U[1:] + F[1:] + [P(-.04, .86), P(1.04, .86)]
    wv.obj([body], 1.)
    # face: lines that follow the face, tight by the barrel and opening toward the shoulder
    d = 1.6
    k = 0
    while d < W * .7:
        ln = offset(F, -d)
        for r in clip_in(ln, body):
            wv.hair(r)
        k += 1
        d += 1.6 if k < 6 else 2 if k < 12 else 3
    # back: lines following the crest
    for j in range(1, 30):
        ln = offset(B[:int(len(B) * .55)], 2 + j * (1.8 if j < 4 else 3))
        for r in clip_in(ln, body):
            wv.hair(r)
    # lip roll: lines under the crest round the lip
    for j in range(1, 9):
        ln = offset(B[int(len(B) * .3):], -(j * 1.6 if j < 5 else 6.4 + (j - 4) * 2.2))
        for r in clip_in(ln, body):
            wv.hair(r)
    wv.line(B)
    # the barrel: black, with the falling curtain at its mouth
    tipx, tipy = B[-1]
    barrel = U + spline([U[-1], P(face[1][0], face[1][1]), P(face[2][0] - .01, face[2][1]),
                         P(face[3][0] - .02, face[3][1] - .01)], 6)[1:] + [P(.36 if lvl else .37, .58 if lvl else .6), P(.35, .5 if lvl else .54)]
    wv.obj([barrel], 1.)
    hatch(wv, barrel, 30, 1.5, w=1.)
    hatch(wv, barrel, -60, 1.5, w=1.)
    curtain = [P(.34, .46 if lvl else .5), P(.37, .47 if lvl else .51), P(.385, .6 if lvl else .62), P(.35, .64 if lvl else .66),
               P(.32, .62 if lvl else .64), P(.325, .52 if lvl else .55)]
    wv.obj([curtain], .5)
    for i in range(5):
        xx = X + W * (.326 + .011 * i)
        wv.hair(clip_in([(xx, Y + H * .44), (xx + 1, Y + H * .7)], curtain))
    # spray claws on the lip: acanthus fingers that curl back (the scroll becomes the wave)
    if lvl:
        nB = len(B)
        i0, i1 = int(nB * .42), int(nB * .9)
        step = max(1, int((i1 - i0) / (6 if lvl == 2 else 4)))
        for i in range(i0, i1, step):
            a, b = B[i - 1], B[i + 1]
            ta = math.atan2(b[1] - a[1], b[0] - a[0])
            ln = H * (.06 + .03 * rng.random()) * (1.1 if lvl == 2 else 1)
            C.acanthus_frond(B[i][0], B[i][1], math.degrees(ta - 1.1), ln, 2, 30, -.5, -4.2, rng.randrange(999),
                             ln * .2, cv=wv)
        # spray: little drops off the lip
        for j in range(16):
            u = rng.uniform(.3, .6)
            v = rng.uniform(.12, .24)
            x, y = P(u, v)
            if not inside((x, y), body):
                wv.obj([ell(x, y, .9, .9, 6)[:-1]], .5)
    o.append(wv.svg())

    # the surfer, carved black down the face
    if lvl:
        s = H * .075
        sx, sy = P(.66, .5)
        ang = .35
        ca, sa = math.cos(ang), math.sin(ang)
        R = lambda x, y: (sx + (x * ca - y * sa) * s, sy + (x * sa + y * ca) * s)
        board = [R(-.75, .02), R(-.4, -.06), R(.55, -.06), R(.8, .0), R(.55, .07), R(-.4, .07)]
        bodyp = [R(-.2, -.05), R(-.32, -.38), R(-.12, -.5), R(-.05, -.75), R(.1, -.95), R(.22, -.86),
                 R(.12, -.62), R(.4, -.62), R(.62, -.48), R(.58, -.44), R(.33, -.52), R(.18, -.45), R(.26, -.22),
                 R(.32, -.05), R(.2, -.05), R(.08, -.3), R(-.05, -.32), R(-.05, -.05)]
        head = ell(*R(.2, -1.08), s * .1, s * .1, 10)
        arm = [R(-.12, -.62), R(-.45, -.72), R(-.62, -.62), R(-.6, -.58), R(-.42, -.66), R(-.1, -.56)]
        o.append(f'<path d="{solid([bodyp, head, arm])}" fill="#000" stroke="#000" stroke-width=".5"/>')
        o.append(f'<path d="{_d(board, True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{_d([R(-.5, .0), R(.6, .0)], False, 0)}" stroke="#000" stroke-width=".5"/>')
        # wake off the board
        wk = C.Canvas()
        wk.obj([], 0)
        for j in range(3):
            wk.hair([R(.6, .1 + j * .1), R(1.1 + j * .3, .25 + j * .2), R(1.6 + j * .4, .5 + j * .25)])
        o.append(wk.svg())

    # ---- foreground: whitewater and the cobbles of the cove ------------------------------------
    fg = C.Canvas()
    wy = .74 if lvl else .78
    foam = [P(-.03, wy + .04)]
    for i in range(25):
        u = -.03 + 1.06 * i / 24
        foam.append(P(u, wy + .015 * math.sin(i * 1.7 + seed) - .01 * (i % 2)))
    foam += [P(1.03, wy + .04), P(1.03, 1.03), P(-.03, 1.03)]
    fg.obj([foam], 1.)
    for j in range(1, 9):
        yy = Y + H * wy + j * (1.6 if j < 3 else 2.5)
        x = X - 3
        while x < X + W + 3:
            L = rng.uniform(4, 12)
            fg.hair([(x, yy), (x + L * .5, yy - .6), (x + L, yy)])
            x += L + 2
    if lvl:
        # the cobble beach: dark wet ground, then the stones
        cy0 = wy + .08
        gnd = Ps([(-.03, cy0), (.2, cy0 - .012), (.5, cy0 + .005), (.8, cy0 - .01), (1.03, cy0), (1.03, 1.03), (-.03, 1.03)])
        fg.obj([gnd], 1.)
        hatch(fg, gnd, 35, 1.5)
        hatch(fg, gnd, -35, 2)
        stones = []
        v = cy0 + .02
        row = 0
        while v < 1.06:
            u = -.04 + rng.uniform(0, .04) + (row % 2) * .02
            sz = (.025 + .045 * (v - cy0) / (1 - cy0)) * (1 if lvl == 2 else 1.1)
            while u < 1.04:
                rxs = W * sz * rng.uniform(.75, 1.15)
                rys = rxs * rng.uniform(.45, .62)
                stones.append((P(u, v), rxs, rys, rng.uniform(-.25, .25)))
                u += sz * 2 * rng.uniform(.9, 1.1) * (W and 1)
            v += (sz * W * .55) / H
            row += 1
        stones.sort(key=lambda s: s[0][1])
        for (cx, cy), rxs, rys, rot in stones:
            e = ell(cx, cy, rxs, rys, 22, 0, TAU, rot)[:-1]
            fg.obj([e], 1.)
            # form shading: crescents toward the lower right, highlight upper left
            for q in (.15, .32, .5, .66, .8):
                a = ell(cx - rxs * q * .35, cy - rys * q * .45, rxs * (1 - q * .35), rys * (1 - q * .45), 16, -.2, PI * .85, rot)
                fg.hair(a)
            if rxs > 6:
                fg.hair(ell(cx - rxs * .35, cy - rys * .35, rxs * .25, rys * .2, 8, PI * 1.1, PI * 1.6, rot))
    o.append(fg.svg())

    # ---- the heron (Easter egg) ------------------------------------------------------------------
    if lvl:
        o.append(heron(X + W * (.16 if lvl == 2 else .14), Y + H * (.93 if lvl == 2 else .95),
                       H * (.36 if lvl == 2 else .36)))
    return "".join(o)


def heron(x, y, h):
    """A great blue heron standing in the wash, looking left, feet at (x, y), h tall."""
    cv = C.Canvas()
    k = h
    Pt = lambda u, v: (x + u * k, y - v * k)
    cv.obj([], 0)
    # long legs with a backward knee, toes spread
    cv.line([Pt(.06, .47), Pt(.05, .24), Pt(.0, 0)])
    cv.line([Pt(.1, .47), Pt(.11, .24), Pt(.12, 0)])
    for fx in (.0, .12):
        cv.hair([Pt(fx - .06, -.005), Pt(fx + .05, .005)])
        cv.hair([Pt(fx, 0), Pt(fx - .04, -.02)])
    # tail plumes behind
    for j in range(4):
        cv.hair([Pt(.18, .5 + j * .012), Pt(.3 + j * .015, .41 + j * .01)])
    # body: tilted oval, dark slate, the wing folded over it
    body = ell(*Pt(.08, .56), k * .17, k * .075, 26, 0, TAU, .5)[:-1]
    cv.obj([body], 1.)
    hatch(cv, body, 25, 1.5)
    hatch(cv, body, -40, 2)
    wing = spline([Pt(-.02, .63), Pt(.1, .62), Pt(.22, .5), Pt(.28, .43), Pt(.16, .48), Pt(.04, .55), Pt(-.02, .63)], 4)
    cv.obj([wing], .5)
    for j in range(6):
        cv.hair(clip_in(spline([Pt(-.02, .62 - j * .012), Pt(.12, .6 - j * .018), Pt(.3, .42)], 6), wing))
    # neck: a long thin S, white with a streaked foreneck
    neck = spline([Pt(-.06, .6), Pt(-.09, .7), Pt(-.03, .78), Pt(-.06, .86), Pt(-.11, .9)], 6)
    cv.obj([ribbon(neck, k * .034, k * .024)], 1.)
    for j in range(7):
        q = neck[int(j * (len(neck) - 1) / 7)]
        cv.hair([(q[0] - k * .02, q[1]), (q[0] - k * .005, q[1] + 1.2)])
    # head, black crown stripe and plume, dagger bill
    hd = ell(*Pt(-.12, .915), k * .04, k * .03, 14)[:-1]
    cv.obj([hd], 1.)
    cv.heavy([Pt(-.15, .935), Pt(-.09, .94), Pt(-.04, .935)])
    cv.line([Pt(-.06, .935), Pt(.06, .9)])
    beak = [Pt(-.155, .925), Pt(-.33, .9), Pt(-.155, .9)]
    cv.obj([beak], 1.)
    cv.hair([Pt(-.16, .912), Pt(-.3, .9)])
    cv.line([Pt(-.13, .918), Pt(-.125, .918)])
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# the running-dog wave moulding (replaces the house egg-and-dart on this page)
# ----------------------------------------------------------------------------------------------

def wave_moulding(x, y, w, hb, seed=0):
    P_ = round(hb * 1.6 * 2) / 2
    base = hb - 1.5
    cx, cy, r = P_ * .6, hb * .44, hb * .34
    prof = spline([(0, base - hb * .04), (P_ * .2, base - hb * .1), (P_ * .34, cy + r * .9), (cx - r, cy)], 6)
    arc = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in [PI + PI * 1.0 * i / 16 for i in range(17)]]
    arc2 = [(cx + r * (1 - .25 * i / 10) * math.cos(t), cy + r * (1 - .25 * i / 10) * math.sin(t))
            for i, t in enumerate([TAU + PI * .5 * i / 10 for i in range(11)])]
    tail = spline([arc2[-1], (cx + r * .2, cy + r * 1.05), (P_ * .9, base - hb * .02), (P_, base - hb * .06)], 6)
    poly = prof + arc + arc2 + tail[1:] + [(P_, hb), (0, hb)]
    spiral = [(cx + r * (.7 - .55 * i / 30) * math.cos(t), cy + r * (.7 - .55 * i / 30) * math.sin(t))
              for i, t in enumerate([PI * .5 + TAU * 1.1 * i / 30 for i in range(31)])]
    pid = f"cstWv{int(hb * 10)}"
    tile = (f'<path d="{_d(poly, True, .05)}" fill="#fff" stroke="none"/>'
            f'<path d="{C.hatch_d(poly, 0, 1.5, .25)}{C.hatch_d(poly, 60, 2)}" stroke="#000" stroke-width=".5"/>'
            f'<path d="{_d(prof + arc + arc2 + tail[1:], False, .05)}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="{_d(spiral, False, .05)}" fill="none" stroke="#fff" stroke-width="2"/>'
            f'<path d="{_d(ell(spiral[-1][0], spiral[-1][1], .9, .9, 8), True, 0)}" fill="#000"/>')
    # sky above the waves: light ruled, so no blank paper
    sky = "".join(f"M0,{_n(yy)}h{_n(P_)}" for yy in [i * 2 + 1.5 for i in range(int(hb / 2) + 1)])
    tile = f'<path d="{sky}" stroke="#000" stroke-width=".5"/>' + tile
    return (f'<defs><pattern id="{pid}" x="{_n(x)}" y="{_n(y)}" width="{_n(P_)}" height="{_n(hb)}" '
            f'patternUnits="userSpaceOnUse">{tile}</pattern></defs>'
            f'<path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(hb)}h{_n(-w)}z" fill="url(#{pid})" stroke="none"/>'
            f'<path d="M{_n(x)},{_n(y + hb - .5)}h{_n(w)}M{_n(x)},{_n(y + .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')


# ----------------------------------------------------------------------------------------------
# layouts (from the house frame_plate, re-cut for this page)
# ----------------------------------------------------------------------------------------------

def clip_d(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def field_ring(cx, cy, a, b):
    """Re-cut the cartouche's bead row over the engraved field: a white fillet with black beads."""
    bp = C._superellipse(cx, cy, a - 3.2, b - 3.2)
    d = _d(bp + [bp[0]], tol=.15)
    return (f'<path d="{d}" fill="none" stroke="#fff" stroke-width="4"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')


def cartouche_scene(cx, cy, cw, ch, seed, lvl, ctx, period):
    c, _, field = C.cartouche(cx, cy, cw, ch, seed)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    sc = scene(cx - a, cy - b, 2 * a, 2 * b, seed, lvl, ctx.get("date", ""), period)
    return c + clip_d(C._uid("cst", cx, cy, cw, ch), field, sc) + field_ring(cx, cy, a, b)


def layout_band(w, h, seed, ctx, period):
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
    inner = ell(cx, cy, rx - 2, ry - 2, 64)
    sc = scene(cx - rx, cy - ry, 2 * rx, 2 * ry, seed, 0, ctx.get("date", ""), period)
    o.append(clip_d(C._uid("bm", w, h), _d(inner, True, 0), sc))
    o.append(f'<path d="{_d(ell(cx, cy, rx - 2, ry - 2, 64), True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def layout_medium(w, h, seed, ctx, period):
    rng = random.Random(seed)
    o = []
    em = min(14., 8 + h * .025)
    o.append(wave_moulding(0, 0, w, em, seed))
    foot = 7.
    gy0, gy1 = em, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .48, gh * 1.75)
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
    o.append(cartouche_scene(cx, cy, cw, gh + 4, rng.randrange(1 << 20), 1, ctx, period))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, ctx, period, name, tablet):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 52), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(max(h * .05, 16), 24.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # the running-dog wave moulding along the top: the plate hangs under the text on breaking surf
    o.append(wave_moulding(0, 0, w, top_free - 4, seed))
    o.append(C.dark_ground((0, top_free - 4, w, h - top_free + 4), "M"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .7
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .16, ph * .25)
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=8, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    o.append(cartouche_scene(cx, cy, cw, ch, rng.randrange(1 << 20), 2, ctx, period))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 56), True, rng.randrange(1 << 20)))
    bh = min(17, max(13, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    letters, _ = text_on(name, centre, bh * .52)
    o.append(f'<path d="{"".join(_d(g, False, .05) for g in letters)}" fill="none" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, tht) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # letter the tablet with the buoy, rule the rest of it
    th = min(tht * .58, 8.)
    tl, twd = text_flat(tablet, tx + tw / 2, ty + tht / 2 + .5, th)
    kx0, kx1 = tx + tw / 2 - twd / 2 - 4, tx + tw / 2 + twd / 2 + 4
    rule = "".join(f"M{_n(xx)},{_n(ty + 2)}v{_n(tht - 3)}" for xx in
                   [tx + 3 + i * 2 for i in range(int((tw - 5) / 2) + 1)] if not (kx0 < xx < kx1))
    o.append(f'<path d="{rule}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{_n(kx0)},{_n(ty + 2)}v{_n(tht - 3)}M{_n(kx1)},{_n(ty + 2)}v{_n(tht - 3)}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{"".join(_d(g, False, .05) for g in tl)}" fill="none" stroke="#000" stroke-width="1"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    name, tablet, period = facts(ctx)
    if h < 110:
        body = layout_band(w, h, seed, ctx, period)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx, period)
    else:
        body = layout_tall(w, h, seed, ctx, period, name, tablet)
    return C.svg_doc(w, h, body)
