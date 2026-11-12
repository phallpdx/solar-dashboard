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


def clip_in(pl, poly, step=2.4):
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
    ph = moon_phase(date)
    _mr = max(4., min(W, H) * .045)
    _mx, _my = X + W * .62, Y + H * .1
    _sh, _sl = st_sky(X - 2, Y - 2, X + W + 2, Y + hz * H + 1, seed + 11, top_dark=.42,
                      avoid=(lambda x, y: math.hypot(x - _mx, y - _my) < _mr * 1.8) if (lvl and .1 < ph < .9) else None)
    sky.hair(_sh)
    sky.line(_sl)
    if lvl:
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
    # the crest itself: close lines running round under the curl so the lip is modelled, not blank
    for j in range(11):
        for r in clip_in(offset(B[int(len(B) * .2):], -(1.6 + j * (2. if j < 5 else 2.6))), body):
            wv.hair(r)
    wv.line(B)
    # the barrel: black, with the falling curtain at its mouth
    tipx, tipy = B[-1]
    barrel = U + spline([U[-1], P(face[1][0], face[1][1]), P(face[2][0] - .01, face[2][1]),
                         P(face[3][0] - .02, face[3][1] - .01)], 6)[1:] + [P(.36 if lvl else .37, .58 if lvl else .6), P(.35, .5 if lvl else .54)]
    wv.obj([barrel], 1.)
    # graded, not a void: dense at the back of the tube, opening toward the curtain
    hatch(wv, barrel, 30, 1.5)
    hatch(wv, barrel, -60, 2)
    _bx = sum(q[0] for q in U) / len(U)
    _deep = [q for q in barrel if q[0] > _bx - W * .02]
    if len(_deep) > 2:
        hatch(wv, _deep, 75, 2, w=1.)
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
            # a spume volute: the lip curls back on itself in a tight scroll, like the frame's own
            L0 = H * (.05 + .025 * rng.random()) * (1.1 if lvl == 2 else 1)
            cx_, cy_ = B[i][0] + math.cos(ta - 1.9) * L0 * .55, B[i][1] + math.sin(ta - 1.9) * L0 * .55
            sp = []
            for j in range(40):
                u = j / 39
                rr = L0 * .55 * math.exp(-2.1 * u)
                th = ta + 1.25 + u * TAU * 1.15
                sp.append((cx_ + rr * math.cos(th), cy_ + rr * math.sin(th)))
            wv.obj([], 0)
            wv.line(sp)
            wv.hair([(q[0] + .9 * math.cos(ta - 1.6), q[1] + .9 * math.sin(ta - 1.6)) for q in sp[:24]])
            wv.obj([ell(sp[-1][0], sp[-1][1], .9, .9, 6)[:-1]], .5)
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
        # Easter egg: the Blazers pinwheel on the deck
        pc = R(-.2, .0)
        pr = s * .06
        pw = []
        for k in range(4):
            a0 = ang + k * math.pi / 2
            pw.append([pc, (pc[0] + pr * math.cos(a0), pc[1] + pr * math.sin(a0)), (pc[0] + pr * .7 * math.cos(a0 + 1.), pc[1] + pr * .7 * math.sin(a0 + 1.))])
        o.append(f'<path d="{solid(pw)}" fill="#000"/>')
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
    _nk = ribbon(neck, k * .034, k * .024)
    cv.obj([_nk], 1.)
    hatch(cv, _nk, 80, 3)
    for j in range(7):
        q = neck[int(j * (len(neck) - 1) / 7)]
        cv.hair([(q[0] - k * .02, q[1]), (q[0] - k * .005, q[1] + 1.2)])
    # head, black crown stripe and plume, dagger bill
    hd = ell(*Pt(-.12, .915), k * .04, k * .03, 14)[:-1]
    cv.obj([hd], 1.)
    hatch(cv, hd, 0, 3)
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


def _field(fld, mode, seed, ctx, period):
    xs = [q[0] for q in fld]
    ys = [q[1] for q in fld]
    X, Y = min(xs), min(ys)
    return scene(X, Y, max(xs) - X, max(ys) - Y, seed, {"band": 0}.get(mode, 1),
                 ctx.get("date", ""), period)


def kelp_frame(cx, cy, rx, ry, fld, mode, seed):
    """The frame is the cove's own: bull kelp rising out of the wash at both lower corners of the
    vignette, stipes curving up its sides to their floats, the blades streaming off them."""
    if ry < 30:
        return ""
    rng = random.Random(seed)
    cv = C.Canvas()
    for sd in (-1, 1):
        for k in range(2):
            bx = cx + sd * rx * (.78 + .1 * k)
            by = cy + ry * (.98 - .05 * k)
            L = ry * (1.1 - .3 * k)
            pts = [(bx, by)]
            a = -math.pi / 2 - sd * .25
            for j in range(20):
                a += sd * (.06 + .03 * math.sin(j * .4))
                pts.append((pts[-1][0] + math.cos(a) * L / 20, pts[-1][1] + math.sin(a) * L / 20))
            st = ribbon(pts, 1.3, .6)
            cv.obj([st], 1.)
            fx, fy = pts[-1]
            fr = max(2.2, L * .05)
            fl = ell(fx, fy, fr, fr * 1.15, 18)[:-1]
            cv.obj([fl], 1.)
            cv.hair(C.hatch_poly(fl, 45, 1.5))
            for m in range(3):
                ba = a + sd * (1.3 + m * .45)
                bl = [(fx, fy)]
                for j in range(16):
                    ba += sd * .03 + .22 * math.sin(j * .8 + m * 1.7) * .4
                    bl.append((bl[-1][0] + math.cos(ba) * L * .035, bl[-1][1] + math.sin(ba) * L * .035))
                blade = ribbon(bl, 2.4, .4)
                cv.obj([blade], .5)
                cv.hair(C.hatch_poly(blade, 70 * sd, 1.5, m * .3))
    return cv.svg()


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
    o = [f'<path d="{st_rect_d(0, 0, w, h)}" fill="#fff"/>']
    if hk.get("under"):
        o.append(hk["under"](cx, cy, rx, ry, fld, mode))
    o.append(st_clip_poly(f"s2v{w}x{h}", fld, hk["field"](fld, mode)))
    o.append(st_dissolve(fld, seed, hk.get("dissolve", min(7., 3 + min(w, h) * .025))))
    if hk.get("frame"):
        o.append(hk["frame"](cx, cy, rx, ry, fld, mode))
    if hk.get("dedication") and h >= 110:
        dh = min(30., h * .16)
        o.append(f'<path d="{st_ell_d(cx, h - dh / 2 - 1.5, dh * .62, dh * .55)}" fill="#fff"/>')
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
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    name, tablet, period = facts(ctx)
    hk = dict(vignette=True, pad=3., max_aspect=2.3, frame=lambda cx, cy, rx, ry, fld, mode: kelp_frame(cx, cy, rx, ry, fld, mode, seed),
              field=lambda fld, mode: _field(fld, mode, seed, ctx, period), egg=egg_pinwheel, shape="oval", aspect=1.9, cw=.27,
              rmin=12., rmax=34., frieze=False, motto=name, tablet_lines=[tablet, "CLATSOP SPIT BUOY"] if tablet != "CLATSOP SPIT" else [tablet])
    return st_plate(w, h, seed, hk)
