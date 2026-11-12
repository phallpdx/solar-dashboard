"""Colophon plate for the Morning Edition's last page ("That's the edition", -30-).

The edition is finished, so the subject is the press that printed it: an iron Columbian hand press,
engraved front-on in a print shop, with the day's sheets pegged up to dry and the shop clock that
strikes a new edition every hour. On the press crown, where a Columbian carries its cast eagle,
stands a great blue heron from Sauvie Island. Easter egg: a pair of crossed drumsticks lying on the
stack of freshly printed papers. The short band carries the newsroom end mark "-30-" itself.
"""
import sys
import math
import random
import engraving_codex as C
try:
    from solar.arms import arms
except ImportError:          # run from solar/ (the plate studio's own path)
    from arms import arms

PI = math.pi
_n = C._n
_d = C._d


# ----------------------------------------------------------------------------------------------
# small drawing helpers (plate px)
# ----------------------------------------------------------------------------------------------

def _slab(cv, x0, y0, x1, y1, along="v", hl=.22, outline=1., edge=True):
    """A shaded block lit from the upper left: lines along `along` ('v' vertical, 'h' horizontal),
    white highlight on the lit side, spacing closing 3 -> 2 -> 1.5 toward the dark side, black edge."""
    cv.obj([[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], outline)
    if along == "v":
        W = x1 - x0
        t = hl * W
        while t < W - .6:
            f = t / W
            cv.hair([(x0 + t, y0 + .4), (x0 + t, y1 - .4)])
            t += 3. if f < .5 else 2. if f < .8 else 1.5
        if edge and W > 3:
            cv.heavy([(x1 - .8, y0 + .4), (x1 - .8, y1 - .4)])
    else:
        H = y1 - y0
        t = hl * H
        while t < H - .6:
            f = t / H
            cv.hair([(x0 + .4, y0 + t), (x1 - .4, y0 + t)])
            t += 3. if f < .5 else 2. if f < .8 else 1.5
        if edge and H > 3:
            cv.heavy([(x0 + .4, y1 - .8), (x1 - .4, y1 - .8)])


def _member(cv, pts, wl, wr, dark=1, pitch=2., shadow=1.2):
    """A round-carved member along pts (half-widths wl on the +normal side, wr on the other):
    lines along the form dense on the dark side, a black shadow band on the dark edge."""
    n = len(pts)
    wl = wl if isinstance(wl, list) else [wl] * n
    wr = wr if isinstance(wr, list) else [wr] * n
    R = C._Rib(pts, wl, wr)
    cv.obj([R.outline()], 1.)
    wm = max(max(wl), max(wr))
    d = 1.5
    while d < wm * 1.62:
        cv.hair(R.contour(dark * (1 - d / wm), 0, 1))
        d += 1.5 if d < wm * .7 else 2. if d < wm * 1.2 else 3.
    if shadow > .5:
        cv.heavy(R.inset(dark, lambda u: .75, 0, 1))
        d = 2.
        while d < shadow + .3:
            cv.line(R.inset(dark, lambda u, dd=d: dd, 0, 1))
            d += .9
    return R


def _sphere(cv, cx, cy, r):
    """A shaded ball: concentric crescent lines toward the lower right, a white glint upper left."""
    cv.obj([C._ell_pts(cx, cy, r, r, max(16, int(r * 6)))], 1.)
    k = 1
    while True:
        off = k * 1.6
        rr = r - off * .55
        if rr < 1.2:
            break
        # offset circles clipped to the ball: arcs on the shadow side
        ox, oy = cx - off * .55, cy - off * .55
        arc = []
        for i in range(25):
            a = -PI * .15 + PI * 1.3 * i / 24
            px, py = ox + rr * math.cos(a), oy + rr * math.sin(a)
            if math.hypot(px - cx, py - cy) < r - .4:
                arc.append((px, py))
        if len(arc) > 1:
            cv.hair(arc)
        k += 1
    cv.line(C._ell_pts(cx, cy, r - .8, r - .8, 24, -PI * .1, PI * .65))


def _text_lines(cv, x0, y0, x1, y1, seed, cols=2, head=True):
    """Tiny printed matter: a headline rule and justified columns of type lines."""
    rng = random.Random(seed)
    y = y0
    if head and y1 - y0 > 6:
        cv.line([(x0, y + .5), (x1, y + .5)])
        y += 2.5
    gw = (x1 - x0 - (cols - 1) * 1.5) / cols
    for c in range(cols):
        cx0 = x0 + c * (gw + 1.5)
        yy = y
        while yy < y1 - .2:
            ln = gw if rng.random() > .15 else gw * rng.uniform(.4, .8)
            cv.hair([(cx0, yy), (cx0 + ln, yy)])
            yy += 1.5


# ----------------------------------------------------------------------------------------------
# the heron (Sauvie Island great blue heron, standing, facing left)
# ----------------------------------------------------------------------------------------------

def _spline(cps, n=8):
    """Catmull-Rom through control points, n samples per span."""
    out = []
    P = [cps[0]] + list(cps) + [cps[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(cps[-1])
    return out


def _heron(cv, S):
    """A great blue heron standing, facing -x in its own units (about 37 tall)."""
    p, u = S.p, S.u
    # legs: long, the joint bending backward, scaled shins, splayed toes
    cv.obj([], 0)
    for (fx, kx, hx) in ((1.6, 2.4, 1.0), (-1.6, -.6, -.4)):
        cv.line([p(fx, 0), p(kx, -7.4), p(hx, -15.5)])
        for k in range(1, 6):
            y = -k * 1.25
            x = fx + (kx - fx) * (-y / 7.4)
            cv.hair([p(x - .5, y), p(x + .5, y - .2)])
        cv.hair([p(fx - 3.2, .1), p(fx, 0), p(fx + 2.4, -.1)])
        cv.hair([p(fx, 0), p(fx - 1.8, .5)])
    # tail and body: a teardrop tilted down to the tail, breast deep
    B, T = (-6., -24.5), (9.5, -14.5)
    cx, cy = (B[0] + T[0]) / 2, (B[1] + T[1]) / 2
    a = math.atan2(T[1] - B[1], T[0] - B[0])
    L, H = math.hypot(T[0] - B[0], T[1] - B[1]) / 2, 4.3
    ca, sa = math.cos(a), math.sin(a)

    def bp(x, y):
        return p(cx + x * ca - y * sa, cy + x * sa + y * ca)

    body = [bp(L * math.cos(t), H * math.sin(t) * (1 - .38 * math.cos(t)))
            for t in [TAU * i / 48 for i in range(48)]]
    cv.obj([body], 1.)
    # contour feathering along the body: dense on the belly (shadow), sparse on the back
    for f in (.92, .8, .68, .56, .44, .3, .16, .02, -.2, -.45):
        ln = []
        for i in range(25):
            t = -.85 * PI + 1.7 * PI * i / 24
            x = L * .96 * math.cos(t * .5) * (1 if True else 0)
            x = -L * .95 + 1.9 * L * i / 24
            ct = x / L
            half = H * math.sqrt(max(0., 1 - ct * ct)) * (1 - .38 * ct)
            ln.append(bp(x, f * half))
        (cv.line if f > .75 else cv.hair)(ln)
    # thigh feathers
    cv.hair([bp(2, 3.8), bp(1, 5.5)])
    # folded wing laid over the back, primaries running past the tail
    wing = [bp(-L * .75, -H * .2), bp(-L * .4, -H * 1.2), bp(L * .2, -H * 1.15), bp(L * .85, -H * .55),
            bp(L * 1.32, H * .05), bp(L * 1.1, H * .25), bp(L * .5, H * .1), bp(-L * .1, H * .15), bp(-L * .55, H * .35)]
    wing = _spline(wing + [wing[0]], 4)[:-1]
    cv.obj([wing], 1.)
    # coverts: rows of scalloped feather tips
    for row, (f0, f1, yy) in enumerate(((-.55, .35, -.5), (-.35, .65, -.05), (-.1, .9, .2))):
        x = f0 * L
        while x < f1 * L:
            q0, q1, q2 = bp(x, yy * H + .2), bp(x + 1.0, yy * H + .9), bp(x + 2.0, yy * H + .1)
            cv.hair([q0, q1, q2])
            x += 2.0
    # primaries: long dark quills
    for k in range(6):
        y0 = -.3 + k * .09
        cv.line([bp(L * .35, H * y0), bp(L * 1.25, H * (y0 * .4 + .1))])
    cv.hair(C.hatch_poly([bp(L * .3, -H * .9), bp(L * 1.3, 0), bp(L * 1.1, H * .3), bp(L * .3, H * .2)], math.degrees(a) + 90, 1.5))
    # back plumes trailing over the tail
    for k in range(4):
        cv.hair(_spline([bp(-L * .2 + k, -H * 1.0), bp(L * .5, -H * .9 + k * .3), bp(L * 1.2 + k * .5, -H * .2 + k * .4)], 5))
    # neck: an S from the breast, carrying the head high
    neck = _spline([(-5.0, -24.2), (-2.6, -27.6), (-2.9, -31.0), (-4.9, -34.2), (-5.7, -36.0)], 5)
    np_ = [p(*q) for q in neck]
    W = [u * (2.2 - 1.15 * (i / (len(np_) - 1)) ** .8) for i in range(len(np_))]
    R = C._Rib(np_, W, W)
    cv.obj([R.outline()], 1.)
    side = -S.m   # the back of the neck is shaded
    d = 1.
    while d < max(W) * 1.1:
        cv.hair(R.contour(side * (1 - d / max(W)), .02, .96))
        d += 1.5
    cv.heavy(R.inset(side, lambda q: .7, .05, .92))
    # black streaks down the foreneck
    for k in range(7):
        t = .12 + k * .11
        q0, q1 = R.at(t, -side * .55), R.at(t + .05, -side * .35)
        cv.line([q0, q1])
    # breast plumes hanging over the body
    for k in range(6):
        cv.hair(_spline([p(-5.6 + k * .5, -25.8 + k * .3), p(-7.6 + k * .45, -21.5 + k * .3), p(-7.0 + k * .5, -17.8 + k * .3)], 4))
    # head, eye, dagger bill, black crown stripe, crest plumes
    hx, hy = -6.2, -36.6
    cv.obj([C._ell_pts(*p(hx, hy), 2.2 * u, 1.55 * u, 20)], 1.)
    bill = [p(hx - 1.4, hy - 1.0), p(hx - 10.5, hy + .2), p(hx - 1.2, hy + 1.1)]
    cv.obj([bill], 1.)
    cv.hair([p(hx - 1.6, hy + .15), p(hx - 9.5, hy + .25)])
    cv.hair([p(hx - 2, hy + .7), p(hx - 7, hy + .5)])
    cv.heavy([p(hx - 1.8, hy - .9), p(hx - .2, hy - 1.45), p(hx + 1.7, hy - 1.0)])
    cv.line(_spline([p(hx + 1.0, hy - 1.0), p(hx + 4.2, hy - .4), p(hx + 7.4, hy + 1.2)], 4))
    cv.line(_spline([p(hx + 1.0, hy - .6), p(hx + 3.8, hy + .5), p(hx + 6.0, hy + 2.3)], 4))
    cv.heavy([p(hx - .7, hy - .2), p(hx - .5, hy - .2)])
    cv.hair([p(hx + .4, hy + .6), p(hx + 1.6, hy + 1.2)])


TAU = 2 * PI


class _Sc:
    def __init__(self, ox, oy, u, m=1):
        self.ox, self.oy, self.u, self.m = ox, oy, u, m

    def p(self, x, y):
        return (self.ox + self.m * x * self.u, self.oy + y * self.u)

    def sub(self, x, y, k=1., m=1):
        return _Sc(self.ox + self.m * x * self.u, self.oy + y * self.u, self.u * k, self.m * m)


# ----------------------------------------------------------------------------------------------
# the Columbian hand press, front elevation; origin at the centre of its foot, units S.u
# ----------------------------------------------------------------------------------------------

def _press(cv, S, seed):
    p, u = S.p, S.u
    rng = random.Random(seed)

    # outboard rail leg and rounce (behind the rails)
    _member(cv, [p(60, 0), p(60, -31)], 1.6 * u, 1.6 * u, 1, 2., 1.)
    _slab(cv, *p(57, -2), *p(63, 0), "h", .3)

    # cheeks: two waisted iron columns, lit from the left
    for sx in (-1, 1):
        pts = [p(sx * (29 - 3 * t ** 1.5) + 0, -5 - 68 * t) for t in [i / 24 for i in range(25)]]
        w = [u * (4.8 - 2.0 * math.sin(PI * min(1, t * 1.15)) + .6 * t) for t in [i / 24 for i in range(25)]]
        R = _member(cv, pts, w, w, 1, 1.5, 2.2 * u)
        cv.hair(R.contour(-.55, .08, .92))
        cv.line(R.contour(-.72, .08, .92))
        # bolt heads down the face
        for t in (.18, .5, .82):
            bx, by = R.at(t, -.2)
            cv.obj([C._ell_pts(bx, by, .9 * u, .9 * u, 10)], 1.)
            cv.line([(bx + .2 * u, by - .5 * u), (bx + .5 * u, by + .3 * u)])

    # cross sill and scroll feet
    _slab(cv, *p(-36, -9), *p(36, -4.5), "h", .2)
    for sx in (-1, 1):
        foot = [p(sx * 26, -4.5), p(sx * 40, -4.5), p(sx * 44, -1.5), p(sx * 44, 0), p(sx * 22, 0), p(sx * 24, -2.5)]
        if sx > 0:
            foot = foot[::-1]
        cv.obj([foot], 1.)
        cv.hair(C.hatch_poly(foot, 0, 1.5 if sx > 0 else 2.))
        cv.heavy([p(sx * 22, -.6), p(sx * 44, -.6)])
        _sphere(cv, *p(sx * 42.5, -4.8), 1.9 * u)

    # platen and the piston above it
    _slab(cv, *p(-3, -66), *p(3, -50), "v", .25)
    for yy in (-62, -56):
        _slab(cv, *p(-4.5, yy), *p(4.5, yy + 2.2), "v", .2)
    _slab(cv, *p(-16, -50), *p(16, -45.5), "h", .2)
    # the forme and frisket sheet under the platen (a white page with its print showing through)
    _slab(cv, *p(-20, -45.5), *p(20, -42), "v", .9, 1., False)

    # bed / ribs running through, coffin on top
    _slab(cv, *p(-50, -36.5), *p(64, -31.5), "h", .18)
    _slab(cv, *p(-22, -42), *p(48, -36.5), "h", .3)
    # the inked forme: tiny type rows on the coffin
    for k in range(3):
        y0 = -41.2 + k * 1.6
        cv.hair([p(24, y0), p(46, y0)])
    # rounce: a spoked crank wheel on the rail end
    rx, ry = p(55, -26)
    rr = 5.2 * u
    cv.obj([C._ell_pts(rx, ry, rr, rr, 28)], 1.)
    cv.obj([C._ell_pts(rx, ry, rr - 1.4 * u, rr - 1.4 * u, 28)], 1.)
    cv.hair(C.hatch_poly(C._ell_pts(rx, ry, rr - 1.4 * u, rr - 1.4 * u, 28), 0, 2.))
    for k in range(4):
        a = PI / 4 + k * PI / 2 + .2
        cv.obj([], 0)
        cv.heavy([(rx, ry), (rx + (rr - .6) * math.cos(a), ry + (rr - .6) * math.sin(a))])
    cv.line(C._ell_pts(rx, ry, rr - .7 * u, rr - .7 * u, 28, 0, PI))
    _sphere(cv, rx, ry, 1.2 * u)
    _member(cv, [p(55, -26), p(61, -23), p(64, -19)], .9 * u, .9 * u, 1, 2., 0)

    # crown: an arched head with a carved panel
    crown = [p(-33, -70), p(33, -70), p(33, -76)] + \
        [p(33 * math.cos(PI * i / 20), -76 - 6 * math.sin(PI * i / 20)) for i in range(1, 20)] + [p(-33, -76)]
    cv.obj([crown], 1.)
    cv.hair(C.hatch_poly(crown, 0, 2.))
    pan = [p(-24, -72)] + [p(24 * math.cos(PI * i / 16), -74.5 - 4 * math.sin(PI * i / 16)) for i in range(17)] + [p(24, -72)]
    pan = [p(-24, -72), p(24, -72)] + [p(24 * math.cos(PI * i / 16), -74.5 - 4 * math.sin(PI * i / 16)) for i in range(17)]
    cv.obj([pan], 1.)
    cv.hair(C.hatch_poly(pan, 0, 1.5))
    # bosses on the carved panel
    for bx in (-14, 0, 14):
        _sphere(cv, *p(bx, -74.6), (2.2 if bx else 2.8) * u)
    cv.heavy([p(-33, -70.6), p(33, -70.6)])
    # the lever beam with counterweights
    beam = [p(-46 + 92 * t, -82 - 6 * math.sin(PI * t)) for t in [i / 24 for i in range(25)]]
    _member(cv, beam, 1.5 * u, 1.5 * u, -1 if False else 1, 1.5, 1.)
    for sx in (-1, 1):
        _member(cv, [p(sx * 30, -78), p(sx * 34, -84)], 1.2 * u, 1.2 * u, 1, 2., 0)
        _sphere(cv, *p(sx * 46, -84), 4.2 * u)
    # finial: a small acanthus crest on the crown
    _slab(cv, *p(-5, -91), *p(5, -88), "v", .2)
    C.palmette(*p(0, -90), 9 * u, True, seed, 2, cv=cv)

    # bar handle sweeping out to the right, wooden grip
    bar = [p(29 + 30 * t, -60 + 8 * t * t) for t in [i / 16 for i in range(17)]]
    _member(cv, bar, 1.2 * u, 1.2 * u, 1, 1.5, .8)
    grip = [p(59 + 9 * t, -52 + 4.5 * t) for t in [i / 10 for i in range(11)]]
    gw = [u * (1.5 + 1.0 * math.sin(PI * i / 10)) for i in range(11)]
    R = _member(cv, grip, gw, gw, 1, 1.5, .8)
    for t in (.2, .5, .8):  # wood grain flecks
        cv.hair([R.at(t, -.4), R.at(t + .1, -.25)])



def _paper_stack(cv, S, seed, sticks=True):
    """Freshly printed newspapers in a stack, with the crossed drumsticks lying on top."""
    p, u = S.p, S.u
    rng = random.Random(seed)
    # stack body (folded papers seen edge-on), each fold a line
    side = [p(-12, 0), p(12, 0), p(12.5, -11), p(-11.5, -11.5)]
    cv.obj([side], 1.)
    y = -.8
    while y > -11:
        j = rng.uniform(-.3, .3)
        cv.hair([p(-12 + j, y), p(12.2 + j, y - .15)])
        y -= 1.5 / u * 1.0
    cv.heavy([p(12, 0), p(12.5, -11)])
    # top sheet in slight perspective with the masthead and columns
    top = [p(-11.5, -11.5), p(12.5, -11), p(10, -16), p(-9.5, -16.5)]
    cv.obj([top], 1.)
    tx0, ty0 = p(-8.2, -15.7)
    tx1, ty1 = p(9, -11.8)
    _text_lines(cv, tx0, ty0, tx1, ty1, seed, 3)
    if sticks:
        # Easter egg: Parker's crossed drumsticks lying on the papers
        for a, b in (((-10, -12.8), (9, -17.6)), ((-9, -17.4), (10.5, -12.3))):
            pts = [p(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in [i / 10 for i in range(11)]]
            w = [u * (.35 + .55 * min(1, i / 6)) for i in range(11)]
            _member(cv, pts, w, w, 1, 1.5, 0)
            cv.obj([C._ell_pts(*pts[0], .55 * u, .45 * u, 10)], 1.)


def _clock(cv, cx, cy, r, hour):
    """The shop clock: a moulded ring, minute ticks, roman-ish hour bars, hands at `hour`."""
    cv.obj([C._ell_pts(cx, cy, r + 1.5, r + 1.5, 40)], 1.)
    ring = C._ell_pts(cx, cy, r + 1.5, r + 1.5, 40)
    cv.hair([C._ell_pts(cx, cy, r + .6, r + .6, 40, PI * .1, PI * 1.1)])
    cv.heavy(C._ell_pts(cx, cy, r + .5, r + .5, 40, -PI * .4, PI * .6))
    cv.line(C._ell_pts(cx, cy, r - .4, r - .4, 40))
    cv.hair(C.hatch_poly(C._ell_pts(cx, cy, r - 2.8, r - 2.8, 32), 0, 3., 1.))
    for k in range(60):
        a = TAU * k / 60
        r0 = r - (2.4 if k % 5 == 0 else 1.2)
        (cv.line if k % 5 == 0 else cv.hair)([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                                              (cx + (r - .6) * math.cos(a), cy + (r - .6) * math.sin(a))])
    ah = -PI / 2 + TAU * (hour % 12) / 12
    am = -PI / 2
    cv.heavy([(cx, cy), (cx + r * .5 * math.cos(ah), cy + r * .5 * math.sin(ah))])
    cv.line([(cx, cy), (cx + r * .78 * math.cos(am), cy + r * .78 * math.sin(am))])
    cv.line(C._ell_pts(cx, cy, .6, .6, 8))
    # pendulum box hint below
    return ring


def _sheets(cv, x0, x1, y, sag, k, seed, hw, hh):
    """A drying line between x0 and x1 at y with k pegged sheets hanging from it."""
    rng = random.Random(seed)
    line = [(x0 + (x1 - x0) * t, y + sag * math.sin(PI * t)) for t in [i / 20 for i in range(21)]]
    cv.obj([], 0)
    cv.line(line)
    for i in range(k):
        t = (i + .7) / (k + .4)
        sx = x0 + (x1 - x0) * t
        sy = y + sag * math.sin(PI * t)
        sk = rng.uniform(-.06, .06)
        sh = [(sx - hw / 2, sy), (sx + hw / 2, sy + sk * hw), (sx + hw / 2 + hh * .04, sy + hh), (sx - hw / 2 + hh * .02, sy + hh + sk * hw)]
        cv.obj([sh], 1.)
        _text_lines(cv, sx - hw / 2 + 1.6, sy + 2., sx + hw / 2 - 1.4, sy + hh - 1.5, seed + i, 2)
        # page curl shadow on the right edge
        cv.line([(sx + hw / 2 - .7, sy + 1), (sx + hw / 2 - .5 + hh * .04, sy + hh - 1)])
        for px in (sx - hw / 2 + 1.5, sx + hw / 2 - 1.5):
            cv.obj([[(px - .9, sy - 1.6), (px + .9, sy - 1.6), (px + .7, sy + 1.8), (px - .7, sy + 1.8)]], 1.)
            cv.hair([(px, sy - 1.4), (px, sy + 1.6)])


def _scene(fx, fy, fw, fh, field_d, seed, date, cid):
    """The print shop, filling the field box (fx, fy, fw, fh), clipped to field_d."""
    o = []
    # wall: light ruled; wainscot below a chair rail; floor
    u = min(fh * .9 / 100, fw * .94 / 196)
    floor = fy + fh * .975 if fh < 160 else fy + fh * .9
    S = _Sc(fx + fw / 2 + 4 * u, floor, u)
    wains = floor - 22 * u
    o.append(C.dark_ground((fx - 2, fy - 2, fw + 4, wains - fy + 2), "G"))
    o.append(C.dark_ground((fx - 2, wains, fw + 4, floor - wains), "V"))
    o.append(C.dark_ground((fx - 2, floor, fw + 4, fy + fh - floor + 2), "M"))
    # cast shadow of the press on the floor and wainscot, to the right
    sh = [S.p(-40, 0), S.p(70, 0), S.p(84, 6), S.p(-28, 6)]
    o.append(C.dark_ground(sh, "G"))
    cv = C.Canvas()
    cv.obj([], 0)
    cv.line([(fx - 2, wains), (fx + fw + 2, wains)])
    cv.heavy([(fx - 2, wains - 1.6), (fx + fw + 2, wains - 1.6)])
    cv.line([(fx - 2, floor), (fx + fw + 2, floor)])
    # floorboard seams fanning toward the vanishing point
    vx = S.ox
    for k in range(-9, 10):
        x0 = vx + k * 9 * u
        cv.hair([(vx + (x0 - vx) * .82, floor), (vx + (x0 - vx) * 1.35, fy + fh + 4)])
    hour = (sum(map(ord, date)) % 12) or 12
    tall = fh > 160
    # clock, upper right; drying line with today's sheets, upper left
    cr = 9.5 * u
    ccx, ccy = S.p(80, -74)
    _clock(cv, ccx, ccy, cr, hour)
    lx0, ly = S.p(-104, -88)
    _sheets(cv, lx0, S.p(-40, 0)[0], ly, 4 * u, 3, seed, 13 * u, 18 * u)
    _press(cv, S, seed)
    _paper_stack(cv, S.sub(-36, 0, .8), seed + 3)
    # a great blue heron from Sauvie Island has walked in to inspect the edition
    _heron(cv, S.sub(-72, 0, 2.15, -1))
    body = "".join(o) + cv.svg()
    return (f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>')


# ----------------------------------------------------------------------------------------------
# layouts (house frame, rebuilt so the whole cartouche field can be engraved edge to edge)
# ----------------------------------------------------------------------------------------------

def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .5, gh * 1.9)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    # Parker's arms (Somaster) either side of the press, in place of the flanking scroll pairs
    ah = gh - 6
    aw = ah * 120 / 140
    shields = []
    for k, side in enumerate((-1, 1)):
        vx = cx + side * (cw / 2 + (w / 2 - cw / 2) / 2)
        vy = gy0 + gh * .5
        shields.append(f'<g transform="translate({_n(vx - aw / 2)},{_n(vy - ah / 2)})">{arms(aw, ah, seed * 2 + k)}</g>')
        occ.append(("r", vx - aw / 2 - 2, gy0, vx + aw / 2 + 2, gy1))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("em", w, h, seed), 0, gy0, w, gh, cv.svg()))
    o += shields
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, gh + 4)
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, fd, seed, ctx.get("date", ""), C._uid("ef", w, h, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", "") + "end")) % 997
    if h < 110:
        body = C._layout_band(w, h, seed, lambda *a: "")
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = C._layout_tall(w, h, seed, lambda *a: "")
    return C.svg_doc(w, h, body)
