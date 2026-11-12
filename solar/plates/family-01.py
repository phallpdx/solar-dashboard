"""family-01 "Little adventures" (play ideas: blanket fort story time, pinecone bird feeder,
worm hunt, nature treasure bag). Master plate.

Vignette: a blanket fort draped over two chairs under a night window (moon phase of the day),
a flashlight beam glowing in the doorway with two small stockinged feet sticking out, a stack
of story books, a braided rug. Pinecone bird feeders with chickadees hang into the scrollwork;
the tall plate's tablet carries the nature treasure list (pinecone, red leaf, smooth rock,
stick) and its banner is lettered with the page title.
Easter egg: Parker's dog asleep, curled nose to tail, beside the fort (paw prints in the
short band; a "P" on the top book's label).
"""
import sys
import math
import random
import datetime
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_n = C._n
_d = C._d
hatch = C.hatch_poly


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def ell(cx, cy, rx, ry, n=32, a0=0., a1=TAU, rot=0.):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n + 1 if a1 - a0 < TAU - 1e-6 else n):
        t = a0 + (a1 - a0) * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def xf(pts, ox, oy, s, ang=0., mx=1):
    """local (x right, y down) -> plate, scale s, rotate ang (rad), mirror mx=-1."""
    c, sn = math.cos(ang), math.sin(ang)
    return [(ox + (p[0] * mx * c - p[1] * sn) * s, oy + (p[0] * mx * sn + p[1] * c) * s) for p in pts]


def lerp(a, b, t):
    return a + (b - a) * t


def clip_poly_y(poly, ylo, yhi):
    """Clip polygon to ylo <= y <= yhi (Sutherland-Hodgman, two passes)."""
    def cut(P, keep, isect):
        out = []
        n = len(P)
        for i in range(n):
            a, b = P[i], P[(i + 1) % n]
            ka, kb = keep(a), keep(b)
            if ka:
                out.append(a)
            if ka != kb:
                out.append(isect(a, b))
        return out

    def iy(yv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1]) / ((b[1] - a[1]) or 1e-9), yv)
    P = cut(poly, lambda p: p[1] >= ylo, iy(ylo))
    if len(P) > 2:
        P = cut(P, lambda p: p[1] <= yhi, iy(yhi))
    return P


def moon_phase(date):
    try:
        d = datetime.date.fromisoformat(str(date)[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (datetime.datetime(d.year, d.month, d.day, 12) - datetime.datetime(2000, 1, 6, 18, 14)).total_seconds() / 86400
    return (days / 29.530588) % 1.


# ----------------------------------------------------------------------------------------------
# engraved motifs (all draw into a codex Canvas: later objects cover earlier lines)
# ----------------------------------------------------------------------------------------------

def moon(cv, cx, cy, r, phase):
    disc = ell(cx, cy, r, r, 28)
    cv.obj([disc], 1.)
    waxing = phase < .5
    k = math.cos(TAU * phase)          # 1 new .. -1 full
    left, right = [], []
    n = 16
    for i in range(n + 1):
        y = -r + 2 * r * i / n
        hw = math.sqrt(max(0., r * r - y * y))
        term = hw * k
        if waxing:        # lit on the right: dark from -hw to term
            left.append((cx - hw, cy + y))
            right.append((cx + term, cy + y))
        else:             # lit on the left: dark from -term to hw
            left.append((cx - term, cy + y))
            right.append((cx + hw, cy + y))
    dark = left + right[::-1]
    if abs(C._area(dark)) > 1.:
        cv.line(hatch(dark, 0, 1.5))
    for (dx, dy, rr) in ((-.25, -.2, .22), (.2, .25, .18)):
        cv.hair(hatch(ell(cx + dx * r, cy + dy * r, rr * r, rr * r * .8, 10), 30, 1.5))


def star(cv, x, y, r):
    pts = []
    for i in range(8):
        a = PI / 4 * i - PI / 2
        rr = r if i % 2 == 0 else r * .3
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    cv.obj([pts], 0)


def pinecone(cv, x, y, L, ang=PI / 2, seed=0, seeds=True, string=0.):
    """A pinecone hanging from (x, y) along direction ang, L long. string: length of the hanging
    cord above it (drawn from (x, y) back against ang)."""
    rng = random.Random(seed)
    ca, sa = math.cos(ang), math.sin(ang)
    na, nb = -sa, ca

    def P(a, b):
        return (x + ca * a + na * b, y + sa * a + nb * b)
    if string > 0:
        cv.obj([], 0)
        cv.line([P(-string, 0), P(0, 0)])

    def hw(t):
        return L * .3 * max(0., math.sin(PI * min(1., t) ** .8)) ** .85 + L * .02
    stem = [P(-L * .06, -L * .035), P(-L * .06, L * .035), P(L * .06, L * .05), P(L * .06, -L * .05)]
    cv.obj([stem], 1.)
    cv.hair(hatch(stem, math.degrees(ang), 1.5))
    nr = max(5, int(L / 4.2))
    ns = 9
    scales = []
    for i in range(nr):
        t = .05 + .86 * i / (nr - 1)
        for j in range(ns):
            ph = (j + .5 * (i % 2)) * TAU / ns + rng.uniform(-.08, .08)
            c = math.cos(ph)
            if c < -.15:
                continue
            h_ = hw(t)
            b = h_ * math.sin(ph)
            sw = max(1.6, 2 * h_ * (PI / ns) * (.35 + .65 * max(c, 0.)) * 1.15)
            sl = L / nr * 1.9
            scales.append((-i, c, t * L, b, sw, sl, ph))
    scales.sort()          # bottom rows first, then back to front within a row
    for _, c, a, b, sw, sl, ph in scales:
        poly = [P(a - sl * .35, b - sw * .55), P(a - sl * .35, b + sw * .55), P(a + sl * .4, b + sw * .5),
                P(a + sl * .72, b + sw * .12), P(a + sl * .72, b - sw * .12), P(a + sl * .4, b - sw * .5)]
        cv.obj([poly], 1. if L > 26 else .5)
        lower = [P(a + sl * .05, b - sw * .52), P(a + sl * .05, b + sw * .52), P(a + sl * .4, b + sw * .5),
                 P(a + sl * .72, b + sw * .12), P(a + sl * .72, b - sw * .12), P(a + sl * .4, b - sw * .5)]
        pitch = 1.5 if (c < .45 or abs(math.sin(ph)) > .75) else 2.
        cv.hair(hatch(lower, math.degrees(ang) + 90 + 25 * math.sin(ph), pitch))
        if c < .5:
            cv.hair(hatch(poly, math.degrees(ang) + 20, 3))
        cv.hair([P(a - sl * .2, b), P(a + sl * .55, b)])
    if seeds:
        for _ in range(int(L * .9)):
            t = rng.uniform(.12, .9)
            b = hw(t) * rng.uniform(-.85, .85)
            p = P(t * L, b)
            q = P(t * L + .8, b + rng.uniform(-.4, .4))
            cv.obj([[p, (p[0] + .5, p[1] - .4), q, (q[0] - .5, q[1] + .4)]], 0)
            cv.heavy([p, q])


def chickadee(cv, x, y, s, facing=1, tilt=0.):
    """A black-capped chickadee perched with its feet at (x, y), about 3.2 s long."""
    def T(pts):
        return xf(pts, x, y, s, tilt, facing)
    cv.obj([], 0)
    cv.line(T([(-.05, -.15), (-.1, .08)]))
    cv.line(T([(.2, -.15), (.25, .08)]))
    cv.hair(T([(-.35, .1), (.15, .1)]))
    cv.hair(T([(.0, .1), (.45, .1)]))
    oy = -.75
    tail = T([(-.75, oy + .15), (-1.95, oy + .55), (-2.0, oy + .78), (-.7, oy + .45)])
    cv.obj([tail], 1.)
    cv.hair(T([(-.8, oy + .3), (-1.95, oy + .66)]))
    cv.hair(hatch(tail, math.degrees(tilt) + 90, 1.5))
    body = T([(px, py + oy) for px, py in ell(0, 0, 1.0, .62, 30, rot=-.3)])
    cv.obj([body], 1.)
    cv.hair(hatch(T([(-.6, oy + .15), (.9, oy - .2), (.9, oy + .6), (-.6, oy + .6)]), math.degrees(tilt) + 20, 3))
    for k in (.55, .75):
        cv.hair(T([(px, py + oy) for px, py in ell(.1, .05, .85 * k + .2, .5 * k + .1, 14, .3, 2.5, rot=-.3)]))
    wing = T([(-.6, oy - .3), (.4, oy - .38), (.3, oy + .1), (-.4, oy + .38), (-1.05, oy + .45)])
    cv.obj([wing], 1.)
    for k in range(4):
        f = .2 + k * .2
        cv.hair(T([(lerp(.3, -.4, f), oy - .32 + f * .1), (lerp(-.35, -1.0, f), oy + .45 - .05 * k)]))
    cv.hair(hatch(T([(-.6, oy - .3), (.4, oy - .38), (.35, oy - .1), (-.7, oy + .05)]), math.degrees(tilt) - 30, 1.5))
    hx, hy = .9, oy - .55
    head = T(ell(hx, hy, .5, .48, 24))
    cv.obj([head], 1.)
    cap = T(ell(hx, hy, .5, .48, 14, PI * .78, PI * 2.08) + [(hx + .3, hy - .02)])
    cv.obj([cap], 0)
    cv.heavy(hatch(cap, 0, 1.5))
    bib = T([(hx + .2, hy + .32), (hx - .12, hy + .62), (hx + .05, hy + .9), (hx + .45, hy + .25)])
    cv.obj([bib], 0)
    cv.heavy(hatch(bib, 0, 1.5))
    cv.obj([T(ell(hx + .18, hy - .08, .085, .085, 8))], 0)
    beak = T([(hx + .46, hy - .08), (hx + .8, hy + .02), (hx + .45, hy + .1)])
    cv.obj([beak], 1.)
    cv.hair(T([(hx - .3, hy + .2), (hx + .25, hy + .25)]))


def dog_curled(cv, cx, cy, rx, ry, facing=1):
    """Parker's dog asleep, curled nose to tail (the Easter egg)."""
    def T(pts):
        return [(cx + (px - cx) * facing, py) for px, py in pts]
    cv.obj([], 0)
    cv.heavy(T(ell(cx, cy + ry * .2, rx * 1.02, ry * .95, 20, .15, PI - .15)))
    body = T(ell(cx, cy, rx, ry, 40))
    cv.obj([body], 1.)
    rng = random.Random(7)
    for k, f in enumerate((.9, .76, .62, .48, .34)):
        n = int(26 * f + 8)
        for i in range(n):
            a0 = TAU * i / n + rng.uniform(-.05, .05)
            if math.sin(a0) < -.4 and k > 2:
                continue
            cv.hair(T(ell(cx, cy, rx * f, ry * f, 3, a0, a0 + TAU / n * .6)))
    cv.hair(T_h(hatch(clip_poly_y(ell(cx, cy, rx, ry, 30), cy + ry * .35, cy + ry), 0, 1.5), cx, facing))
    cv.line(T(ell(cx - rx * .35, cy - ry * .05, rx * .42, ry * .62, 14, -1.9, 1.2)))
    tail = T([(cx - rx * .95, cy + ry * .1), (cx - rx * .6, cy + ry * .95), (cx, cy + ry * 1.12),
              (cx + rx * .5, cy + ry * .95), (cx + rx * .45, cy + ry * .7), (cx, cy + ry * .78),
              (cx - rx * .55, cy + ry * .62), (cx - rx * .82, cy + ry * .05)])
    cv.obj([tail], 1.)
    for f in (.3, .55, .8):
        cv.hair(T([(cx - rx * (.95 - .1 * f), cy + ry * (.1 + .05 * f)), (cx - rx * .6, cy + ry * (.62 + .3 * f)),
                   (cx, cy + ry * (.78 + .32 * f)), (cx + rx * .45, cy + ry * (.72 + .2 * f))]))
    hx, hy = cx + rx * .55, cy + ry * .15
    hd = ell(hx, hy, rx * .36, ry * .55, 24, rot=.35)
    cv.obj([T(hd)], 1.)
    cv.hair(T_h(hatch(clip_poly_y(hd, hy + ry * .1, hy + ry), 0, 1.5), cx, facing))
    snout = [(hx - rx * .05, hy + ry * .25), (hx - rx * .38, hy + ry * .55), (hx - rx * .32, hy + ry * .78),
             (hx + rx * .1, hy + ry * .6)]
    cv.obj([T(snout)], 1.)
    cv.hair(T_h(hatch(snout, 0, 2), cx, facing))
    nose = ell(hx - rx * .35, hy + ry * .66, rx * .06, ry * .1, 8)
    cv.obj([T(nose)], 0)
    cv.heavy(T_h(hatch(nose, 0, 1.5), cx, facing))
    cv.line(T(ell(hx - rx * .08, hy + ry * .05, rx * .07, ry * .07, 6, .2, PI - .2)))
    ear = [(hx + rx * .05, hy - ry * .4), (hx + rx * .3, hy - ry * .35), (hx + rx * .32, hy + ry * .3),
           (hx + rx * .18, hy + ry * .42), (hx + rx * .05, hy + ry * .05)]
    cv.obj([T(ear)], 1.)
    cv.line(T_h(hatch(ear, 75, 1.5), cx, facing))
    for dx in (-.12, .05):
        cv.obj([T(ell(hx + rx * dx, hy + ry * .85, rx * .1, ry * .14, 10))], 1.)
        cv.hair(T([(hx + rx * (dx - .03), hy + ry * .8), (hx + rx * (dx - .03), hy + ry * .95)]))


def T_h(lines, cx, facing):
    return [[(cx + (px - cx) * facing, py) for px, py in pl] for pl in lines]


def book_stack(cv, x, base, w, rng, n=4, monogram=True):
    """Story books stacked on the floor, spines out; returns top y."""
    y = base
    bh = max(4., w * .13)
    for i in range(n):
        bw = w * rng.uniform(.82, 1.)
        ox = x + rng.uniform(-w * .06, w * .08)
        h_ = bh * rng.uniform(.85, 1.15)
        y -= h_
        sp = rect(ox, y, bw, h_)
        pages = rect(ox + bw, y + h_ * .15, w * .04, h_ * .7)
        cv.obj([pages], .5)
        cv.hair(hatch(pages, 0, 1.5))
        cv.obj([sp], 1.)
        style = i % 3
        if style == 0:
            cv.hair(hatch(sp, 90, 2))
        elif style == 1:
            cv.hair(hatch(sp, 0, 1.5))
        else:
            cv.hair(hatch(sp, 45, 2))
            cv.hair(hatch(sp, -45, 3))
        for f in (.08, .14, .86, .92):
            cv.line([(ox + bw * f, y), (ox + bw * f, y + h_)])
        lab = rect(ox + bw * .32, y + h_ * .22, bw * .36, h_ * .56)
        cv.obj([lab], .5)
        if monogram and i == n - 1:
            px, py, ph = ox + bw * .47, y + h_ * .3, h_ * .4
            cv.line([(px, py + ph), (px, py), (px + ph * .45, py), (px + ph * .6, py + ph * .15),
                     (px + ph * .6, py + ph * .35), (px + ph * .45, py + ph * .5), (px, py + ph * .5)])
        else:
            cv.hair([(ox + bw * .36, y + h_ * .5), (ox + bw * .64, y + h_ * .5)])
        cv.heavy([(ox, y + h_), (ox + bw, y + h_)])
    return y


def fort_scene(cv, X, Y, W, H, date, seed=0):
    """The blanket fort at night, filling X..X+W, Y..Y+H completely."""
    rng = random.Random(seed)
    cx = X + W / 2
    fy = Y + H * .70                       # where wall meets floor
    u = max(1., min(W, H) / 150.)          # detail scale
    # ---- wall: striped wallpaper
    wall = rect(X - 2, Y - 2, W + 4, fy - Y + 2)
    cv.obj([wall], 0)
    cv.hair(hatch(wall, 90, 2))
    sx = X + 1
    while sx < X + W:
        cv.line([(sx, Y - 2), (sx, fy)])
        sx += 9 * u
    rail = rect(X - 2, fy - H * .1, W + 4, H * .025)
    cv.obj([rail], 1.)
    cv.hair(hatch(rail, 0, 1.5))
    # ---- window with the night sky and today's moon
    wx0, wx1 = cx - W * .19, cx + W * .19
    wy0, wy1 = Y + H * .08, Y + H * .46
    ft = max(2.5, W * .02)
    frame = rect(wx0 - ft, wy0 - ft, wx1 - wx0 + 2 * ft, wy1 - wy0 + 2 * ft)
    cv.obj([frame], 1.)
    for k in (.33, .66):
        cv.hair([(wx0 - ft * (1 - k), wy0 - ft * (1 - k)), (wx1 + ft * (1 - k), wy0 - ft * (1 - k)),
                 (wx1 + ft * (1 - k), wy1 + ft * (1 - k)), (wx0 - ft * (1 - k), wy1 + ft * (1 - k)),
                 (wx0 - ft * (1 - k), wy0 - ft * (1 - k))])
    sill = rect(wx0 - ft * 2, wy1 + ft * .6, wx1 - wx0 + ft * 4, ft * 1.2)
    cv.obj([sill], 1.)
    cv.hair(hatch(sill, 0, 1.5))
    pane = rect(wx0, wy0, wx1 - wx0, wy1 - wy0)
    cv.obj([pane], 1.)
    yy = wy0 + .75
    while yy < wy1:
        t = (yy - wy0) / (wy1 - wy0)
        if t < .45:
            cv.line([(wx0, yy), (wx1, yy)])
        else:
            cv.hair([(wx0, yy), (wx1, yy)])
        yy += 1.5 if t < .8 else 2.
    hills = [(wx0, wy1)] + [(wx0 + (wx1 - wx0) * i / 24,
                             wy1 - (wy1 - wy0) * (.16 + .06 * math.sin(i * .9 + seed % 5) + .04 * math.sin(i * 2.3)))
                            for i in range(25)] + [(wx1, wy1)]
    cv.obj([hills], .5)
    cv.line(hatch(hills, 0, 1.5))
    mph = moon_phase(date)
    mr = max(4., (wx1 - wx0) * .1)
    mcx, mcy = wx1 - (wx1 - wx0) * .26, wy0 + (wy1 - wy0) * .26
    moon(cv, mcx, mcy, mr, mph)
    for i in range(7):
        sxs = wx0 + (wx1 - wx0) * rng.uniform(.06, .94)
        sys_ = wy0 + (wy1 - wy0) * rng.uniform(.06, .55)
        if math.hypot(sxs - mcx, sys_ - mcy) < mr * 2:
            continue
        star(cv, sxs, sys_, rng.uniform(1.4, 2.4) * u)
    mw = max(1.6, ft * .55)
    for m in (rect(cx - mw / 2, wy0, mw, wy1 - wy0), rect(wx0, (wy0 + wy1) / 2 - mw / 2, wx1 - wx0, mw)):
        cv.obj([m], .5)
    # curtains, tied back
    for sd in (-1, 1):
        x0 = wx0 - ft if sd < 0 else wx1 + ft
        tie = wy0 + (wy1 - wy0) * .62
        top_in, top_out = x0 - sd * (wx1 - wx0) * .2, x0 + sd * W * .07
        cur = [(top_in, wy0 - ft * 2), (top_out, wy0 - ft * 2), (x0 + sd * W * .055, tie), (x0 + sd * W * .09, fy),
               (x0, fy), (x0 + sd * W * .02, tie + 2)]
        cv.obj([cur], 1.)
        for k in range(1, 9):
            f = k / 9
            a = (lerp(top_in, top_out, f), wy0 - ft * 2)
            b = (lerp(x0 + sd * W * .02, x0 + sd * W * .055, f), tie)
            c = (lerp(x0, x0 + sd * W * .09, f), fy)
            (cv.line if k % 3 == 0 else cv.hair)([a, b, c])
        tb = ell(x0 + sd * W * .04, tie, W * .03, H * .015, 12)
        cv.obj([tb], 1.)
        cv.hair(hatch(tb, 0, 1.5))
    rod = rect(wx0 - W * .1, wy0 - ft * 2.6, wx1 - wx0 + W * .2, max(1.6, ft * .7))
    cv.obj([rod], 1.)
    for sd in (-1, 1):
        kx = cx + sd * ((wx1 - wx0) / 2 + W * .1)
        kn = ell(kx, wy0 - ft * 2.2, ft * .9, ft * .9, 12)
        cv.obj([kn], 1.)
        cv.hair(hatch(kn, 45, 1.5))
    # ---- floor: boards running toward a vanishing point
    floor = rect(X - 2, fy, W + 4, Y + H + 2 - fy)
    cv.obj([floor], 1.)
    vx, vy = cx, Y - H * .4
    for k in range(-9, 10):
        x0 = cx + k * W * .085
        t = (Y + H + 2 - vy) / (fy - vy)
        cv.line([(x0, fy), (vx + (x0 - vx) * t, Y + H + 2)])
    yy = fy + 1.5
    while yy < Y + H + 2:
        cv.hair([(X - 2, yy), (X + W + 2, yy)])
        yy += 2. if yy < fy + (Y + H - fy) * .5 else 1.5
    # braided rug in front of the door
    rcx, rcy, rrx, rry = cx, fy + (Y + H - fy) * .62, W * .3, (Y + H - fy) * .5
    rug = ell(rcx, rcy, rrx, rry, 48)
    cv.obj([rug], 1.)
    for k in range(1, 6):
        f = 1 - k / 6
        ring = ell(rcx, rcy, rrx * f, rry * f, 40)
        cv.line(ring + [ring[0]])
        n = int(60 * (f + .08)) + 6
        for i in range(n):
            a = TAU * i / n
            p = (rcx + rrx * f * math.cos(a), rcy + rry * f * math.sin(a))
            q = (rcx + rrx * (f + 1 / 6) * math.cos(a + .06), rcy + rry * (f + 1 / 6) * math.sin(a + .06))
            cv.hair([p, q])
    # ---- the chairs under the blanket
    fx0, fx1 = cx - W * .2, cx + W * .2
    ty = Y + H * .34
    pw = max(2.2, W * .014)
    for fx in (fx0, fx1):
        for dx in (-W * .045, W * .045):
            post = rect(fx + dx - pw / 2, ty - H * .07, pw, fy + H * .04 - (ty - H * .07))
            cv.obj([post], 1.)
            cv.hair([(fx + dx - pw * .15, ty - H * .07), (fx + dx - pw * .15, fy + H * .04)])
            cv.hair(hatch(rect(fx + dx + pw * .1, ty - H * .07, pw * .4, fy + H * .04 - (ty - H * .07)), 90, 1.5))
            kn = ell(fx + dx, ty - H * .075, pw * 1.05, pw * 1.05, 12)
            cv.obj([kn], 1.)
            cv.hair(hatch(clip_poly_y(kn, ty - H * .075, ty), 0, 1.5))
    # ---- the blanket: a patchwork quilt draped over both chair backs
    sag = H * .07

    def top(t):
        xt = lerp(fx0 - W * .07, fx1 + W * .07, t)
        if xt < fx0 - W * .045:
            yt = ty + (fx0 - W * .045 - xt) * 1.9
        elif xt > fx1 + W * .045:
            yt = ty + (xt - fx1 - W * .045) * 1.9
        else:
            q = (xt - fx0 + W * .045) / (fx1 - fx0 + W * .09)
            yt = ty + sag * math.sin(PI * q) ** .8
        return xt, yt

    def hem(t):
        return lerp(fx0 - W * .1, fx1 + W * .1, t), fy + H * .1 + H * .01 * math.sin(t * 19)

    nf = 5

    def Pt(t, v):
        a, b = top(t), hem(t)
        dx = v * W * .014 * math.sin(TAU * nf * t)
        return (lerp(a[0], b[0], v) + dx, lerp(a[1], b[1], v))

    def shade(t):
        return math.cos(TAU * nf * t)
    N = 60
    outline = [Pt(i / N, 0) for i in range(N + 1)] + [Pt(1 - i / N, 1) for i in range(N + 1)]
    cv.obj([outline], 1.)
    span = (fx1 - fx0) + W * .32
    nl = int(span / 1.5)
    for k in range(nl + 1):
        t = k / nl
        s = shade(t + .5 / nf / 2)
        if s > .35 and k % 2:
            continue
        if s > .75 and k % 4 >= 2:
            continue
        cv.hair([Pt(t, v / 12) for v in range(13)])
    nu, nv = 9, 5
    for i in range(nu):
        for j in range(nv):
            if (i + j) % 2:
                continue
            t0, t1 = i / nu, (i + 1) / nu
            v0, v1 = j / nv, (j + 1) / nv
            vv = v0 + .5 / (nv * 4)
            while vv < v1:
                cv.hair([Pt(t0 + (t1 - t0) * q / 6, vv) for q in range(7)])
                vv += 1 / (nv * 4) if shade((t0 + t1) / 2) > -.2 else 1 / (nv * 6)
            pc = Pt((t0 + t1) / 2, (v0 + v1) / 2)
            r = min(W * .018, H * .02)
            cv.hair([(pc[0] - r, pc[1]), (pc[0] + r, pc[1])])
            cv.hair([(pc[0], pc[1] - r), (pc[0], pc[1] + r)])
    for i in range(1, nu):
        cv.line([Pt(i / nu, v / 10) for v in range(11)])
    for j in range(1, nv):
        cv.line([Pt(t / 40, j / nv) for t in range(41)])
    for k in range(nf):
        t = (k + .5) / nf
        cv.heavy([Pt(t, v / 10) for v in range(3, 11)])
    cv.line([Pt(t / 40, .9) for t in range(41)])
    cv.heavy([Pt(t / 40, 1.) for t in range(41)])
    # ---- the doorway: flaps tied back, the inside dark, story time glowing in it
    apex = Pt(.5, .16)
    bl, br = Pt(.3, 1.), Pt(.7, 1.)

    def edge(a, b, bow):
        out = []
        for i in range(13):
            f = i / 12
            px, py = lerp(a[0], b[0], f), lerp(a[1], b[1], f)
            out.append((px + bow * math.sin(PI * f) * (1 if b[0] > a[0] else -1), py))
        return out
    le = edge(apex, bl, -W * .03)
    re = edge(apex, br, -W * .03)
    door = le + [Pt(.3 + .4 * i / 10, 1.) for i in range(1, 10)] + re[::-1]
    cv.obj([door], 1.5)
    cv.line(hatch(door, 0, 1.5))
    cv.hair(hatch(door, 70, 2))
    # the flashlight's glow on the back of the fort
    gx, gy = apex[0], lerp(apex[1], bl[1], .66)
    grx, gry = (br[0] - bl[0]) * .4, (bl[1] - apex[1]) * .36
    glow = ell(gx, gy, grx, gry, 30)
    cv.obj([glow], 0)
    for i in range(28):
        a = TAU * i / 28
        cv.hair([(gx + grx * .55 * math.cos(a), gy + gry * .55 * math.sin(a)),
                 (gx + grx * math.cos(a), gy + gry * math.sin(a))])
    ring = ell(gx, gy, grx * .78, gry * .78, 30)
    cv.hair(ring + [ring[0]])
    # her silhouette, reading: head with two little pigtails, shoulders, an open book
    hs = (bl[1] - apex[1]) * .15
    sx_, sy_ = gx - grx * .12, gy + gry * .45
    sil = [ell(sx_, sy_ - hs * 1.25, hs * .8, hs * .88, 18),
           ell(sx_ - hs * .78, sy_ - hs * 1.95, hs * .3, hs * .22, 10, rot=-.7),
           ell(sx_ + hs * .78, sy_ - hs * 1.95, hs * .3, hs * .22, 10, rot=.7),
           [(sx_ - hs * 1.5, bl[1] - .5), (sx_ - hs * 1.2, sy_ - hs * .1), (sx_ - hs * .4, sy_ - hs * .45),
            (sx_ + hs * .4, sy_ - hs * .45), (sx_ + hs * 1.2, sy_ - hs * .1), (sx_ + hs * 1.5, bl[1] - .5)]]
    for pp in sil:
        cv.obj([pp], 0)
        cv.heavy(hatch(pp, 0, 1.5))
    bkx, bky = sx_ + hs * 1.7, sy_ + hs * .1
    book = [(bkx - hs * 1.1, bky - hs * .9), (bkx, bky - hs * .5), (bkx + hs * 1.1, bky - hs * .9),
            (bkx + hs * 1.05, bky + hs * .4), (bkx, bky + hs * .7), (bkx - hs * 1.05, bky + hs * .4)]
    cv.obj([book], 1.)
    cv.line([(bkx, bky - hs * .5), (bkx, bky + hs * .7)])
    for k in range(1, 4):
        f = k / 4
        cv.hair([(bkx - hs * .9, bky - hs * .8 + hs * 1.1 * f), (bkx - hs * .15, bky - hs * .4 + hs * 1.0 * f)])
    torch = xf([(-6, -1.6), (2, -1.6), (4, -2.6), (4, 2.6), (2, 1.6), (-6, 1.6)], bl[0] + (br[0] - bl[0]) * .25,
               bl[1] - 3 * u, u * .9, -2.4)
    cv.obj([torch], 1.)
    cv.heavy(hatch(torch, 0, 1.5))
    # flap edges rolled back
    for e in (le, re):
        cv.heavy(e)
    # ---- story books stacked by the fort
    book_stack(cv, cx + W * .265, Y + H * .86, W * .13, random.Random(seed + 3), 4)
    # ---- the dog, asleep beside the fort (Easter egg)
    dog_curled(cv, cx - W * .31, Y + H * .8, W * .1, H * .075, 1)


def pinecone_scene(cv, X, Y, W, H, date, seed=0):
    """Short medallion: a pinecone feeder hanging in the window with a chickadee on it, and paw
    prints on the sill (Easter egg)."""
    sky = rect(X - 2, Y - 2, W + 4, H + 4)
    cv.obj([sky], 0)
    yy = Y - 1
    while yy < Y + H + 2:
        t = (yy - Y) / H
        cv.hair([(X - 2, yy), (X + W + 2, yy)])
        yy += 1.5 if t < .45 else 2
    mr = max(3.5, H * .1)
    moon(cv, X + W * .8, Y + H * .25, mr, moon_phase(date))
    rng = random.Random(seed)
    for _ in range(5):
        star(cv, X + W * rng.uniform(.05, .6), Y + H * rng.uniform(.08, .5), rng.uniform(1.2, 2))
    sill = rect(X - 2, Y + H * .8, W + 4, H * .3)
    cv.obj([sill], 1.)
    cv.hair(hatch(sill, 0, 1.5))
    for k in range(3):
        px, py = X + W * (.16 + k * .12), Y + H * (.9 - .04 * (k % 2))
        s = max(1., H * .032)
        cv.obj([ell(px, py, 1.6 * s, 1.3 * s, 10)], 0)
        for dx, dy in ((-1.6, -1.6), (-.55, -2.3), (.55, -2.3), (1.6, -1.6)):
            cv.obj([ell(px + dx * s, py + dy * s, .6 * s, .7 * s, 8)], 0)
    L = H * .55
    pinecone(cv, X + W * .4, Y + H * .16, L, PI / 2, seed, True, H * .2)
    chickadee(cv, X + W * .7, Y + H * .8, max(4.5, H * .13), -1, .1)


# ----------------------------------------------------------------------------------------------
# banner lettering: a small engraved Roman, drawn as strokes (no <text>)
# ----------------------------------------------------------------------------------------------

def _O():
    return [[(2 + 2 * math.cos(t * TAU / 16), 3 + 3 * math.sin(t * TAU / 16)) for t in range(17)]]


FONT = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1.5), (0, 4.5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1.5), (0, 4.5), (1, 6), (3, 6), (4, 5), (4, 3.5), (2.5, 3.5)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 0), (1, 6)]],
    "J": [[(4, 0), (4, 4.5), (3, 6), (1, 6), (0, 4.8)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.5)], [(1.3, 2.7), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2, 4), (4, 0), (4, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": _O(),
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "Q": _O() + [[(2.5, 4.5), (4, 6.3)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 4.8), (1, 6), (3, 6), (4, 4.8), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1, 6), (2, 2), (3, 6), (4, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
}


def letter_along(centre, text, cap):
    """Path data for text centred along the banner's centre line, letters cap px tall."""
    text = "".join(ch for ch in text.upper() if ch in FONT or ch == " ")
    s = cap / 6.
    adv = [2.6 * s if ch == " " else ((2 if ch == "I" else 4) + 1.6) * s for ch in text]
    total = sum(adv) - 1.6 * s
    acc = [0.]
    for i in range(1, len(centre)):
        acc.append(acc[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    L = acc[-1]
    if total > L * .9:
        k = L * .9 / total
        s *= k
        adv = [a * k for a in adv]
        total = L * .9

    def at(d):
        for i in range(1, len(acc)):
            if acc[i] >= d:
                f = (d - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
                a = math.atan2(centre[i][1] - centre[i - 1][1], centre[i][0] - centre[i - 1][0])
                return (lerp(centre[i - 1][0], centre[i][0], f), lerp(centre[i - 1][1], centre[i][1], f)), a
        return centre[-1], 0.
    d = (L - total) / 2
    out = []
    for ch, a_ in zip(text, adv):
        if ch != " ":
            gw = 2 if ch == "I" else 4
            (px, py), ang = at(d + gw * s / 2)
            for st in FONT[ch]:
                pts = xf([(p[0] - gw / 2, p[1] - 3) for p in st], px, py, s, ang)
                out.append(_d(pts, tol=0))
        d += a_
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# layouts
# ----------------------------------------------------------------------------------------------

def _clip_to(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.55, 116)
    o.append(C._clip(C._uid("fb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    cv = C.Canvas()
    pinecone_scene(cv, cx - rx, cy - ry, 2 * rx, 2 * ry, date, seed)
    o.append(_clip_to(C._uid("fbm", w, h, seed), _d(ell(cx, cy, rx - 4.3, ry - 4.3, 64), True, 0), cv.svg()))
    o.append(f'<path d="{_d(ell(cx, cy, rx - 4, ry - 4, 64), True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
    return "".join(o)


def _feeder(cv, x, y, L, seed, bird, facing=1):
    pinecone(cv, x, y + L * .45, L, PI / 2 + .05 * facing, seed, True, L * .45)
    if bird:
        chickadee(cv, x + facing * L * .04, y + L * .45 + L * .98, L * .2, facing, 0.)


def _layout_medium(w, h, seed, date, density=1.):
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
    L = min(gh * .42, 64)
    fxs = (r * .36, w - r * .36)
    for fx in fxs:
        occ.append(("c", fx, gy0 + L * .9, L * .45))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    feed = C.Canvas()
    for k, fx in enumerate(fxs):
        _feeder(feed, fx, gy0, L, seed + k, True, 1 if k == 0 else -1)
    cv.extend(feed)
    o.append(C._clip(C._uid("fm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, gh + 4) * .07)
    a, b = cw / 2 - bw * 1.6, (gh + 4) / 2 - bw * 1.6
    sc = C.Canvas()
    fort_scene(sc, cx - a, cy - b, 2 * a, 2 * b, date, seed)
    field = _d(C._superellipse(cx, cy, a - 5.5, b - 5.5), True, 0)
    o.append(_clip_to(C._uid("fmf", w, h, seed), field, sc.svg()))
    o.append(f'<path d="{field}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def treasure_tablet(x, y, w, h, seed):
    """The tablet carries the nature-treasure list in pictures: pinecone, red leaf, smooth rock,
    stick, on a cut ground with a running vine."""
    cv = C.Canvas()
    g = rect(x, y, w, h)
    cv.obj([g], 0)
    cv.hair(hatch(g, 0, 1.5))
    cy = y + h / 2
    vine = [(x + 4 + (w - 8) * i / 80, cy + h * .18 * math.sin(i / 80 * TAU * 3)) for i in range(81)]
    cv.obj([], 0)
    cv.line(vine)
    s = h * .95
    slots = [x + w * f for f in (.2, .4, .6, .8)]
    pinecone(cv, slots[0] - s * .9, cy, s * 1.8, 0, seed, False)
    lx = slots[1]
    pts = []
    for i in range(41):
        t = TAU * i / 40
        rr = s * .5 * (.55 + .45 * abs(math.cos(2.5 * t)) ** .6)
        pts.append((lx + rr * math.cos(t - PI / 2) * 1.2, cy + rr * math.sin(t - PI / 2) * .95))
    cv.obj([pts], 1.)
    cv.hair(hatch(pts, 90, 1.5))
    cv.hair(hatch(pts, 0, 3))
    for t in (-PI / 2, -PI / 2 + 1.26, -PI / 2 - 1.26, PI / 2 - .6, PI / 2 + .6):
        cv.line([(lx, cy + s * .2), (lx + s * .5 * math.cos(t), cy + s * .45 * math.sin(t))])
    cv.line([(lx, cy + s * .2), (lx + s * .1, cy + s * .55)])
    rx = slots[2]
    rock = ell(rx, cy + s * .05, s * .75, s * .42, 30)
    cv.obj([rock], 1.)
    for f in (.85, .7, .55):
        cv.hair(ell(rx + s * .08, cy + s * .1, s * .75 * f, s * .42 * f, 20, .2, PI - .2))
    cv.hair(hatch(clip_poly_y(rock, cy + s * .2, cy + s), 0, 1.5))
    sx = slots[3]
    stick = [(sx - s * .95, cy + s * .25), (sx + s * .95, cy - s * .2), (sx + s * .97, cy - s * .08), (sx - s * .93, cy + s * .37)]
    cv.obj([stick], 1.)
    cv.hair(hatch(stick, -13, 1.5))
    tw = [(sx, cy + s * .05), (sx + s * .35, cy - s * .4), (sx + s * .4, cy - s * .35), (sx + s * .1, cy + s * .02)]
    cv.obj([tw], 1.)
    cv.hair(hatch(tw, -50, 1.5))
    return cv.svg()


def _layout_tall(w, h, seed, date, title, density=1.):
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
    L = min(ph * .2, 70)
    fxs = (px0 + pw * .07, px0 + pw * .93)
    for fx in fxs:
        occ.append(("c", fx, py0 + L * 1.0, L * .5))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    feed = C.Canvas()
    for k, fx in enumerate(fxs):
        _feeder(feed, fx, py0, L, seed + k, True, 1 if k == 0 else -1)
    cv.extend(feed)
    o.append(C._clip(C._uid("ft", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    sc = C.Canvas()
    fort_scene(sc, cx - a, cy - b, 2 * a, 2 * b, date, seed)
    field = _d(C._superellipse(cx, cy, a - 5.5, b - 5.5), True, 0)
    o.append(_clip_to(C._uid("ftf", w, h, seed), field, sc.svg()))
    o.append(f'<path d="{field}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(f'<path d="{letter_along(centre, title, bh * .52)}" fill="none" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(treasure_tablet(tx + 2, ty + 2, tw - 3, th - 3, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("ff", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, str(date))) + 11
    title = ctx.get("title") or "Little adventures"
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date)
    else:
        body = _layout_tall(w, h, seed, date, title, .95)
    return C.svg_doc(w, h, body)
