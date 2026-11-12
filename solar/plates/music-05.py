"""music-05 "Where the jazz is" (Jazz in Portland): an engraved tenor saxophone standing in a
spotlight before a ruled stage curtain, notes rising from its engraved bell, inside the house
acanthus frame. Tall plates add a Hammond B3 (Mel Brown's organ group heads the listing), a
lettered ribbon and a piano-keyboard pedestal tablet.
Easter egg: Parker's crossed drumsticks and a tiny ride cymbal, tucked behind the sax."""
import sys
import math
import random
import engraving_codex as C

_n, _d, _Rib, _ell = C._n, C._d, C._Rib, C._ell_pts
PI = math.pi


# ----------------------------------------------------------------------------------------------
# small geometry
# ----------------------------------------------------------------------------------------------

def _resample(pts, ws, step):
    """Even spacing along a polyline (with per-point half widths)."""
    L = [0.]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    n = max(4, int(L[-1] / step))
    out, ow = [], []
    j = 0
    for k in range(n + 1):
        s = L[-1] * k / n
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        seg = (L[j + 1] - L[j]) or 1
        t = (s - L[j]) / seg
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
        ow.append(ws[j] + (ws[j + 1] - ws[j]) * t)
    return out, ow


def _bez(p0, p1, p2, p3, n=16):
    return [((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0],
             (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1])
            for t in [i / n for i in range(n + 1)]]


def _solid(cv, poly, ang=0.):
    """A black mass: white object filled with 1 px lines 1 px apart."""
    cv.obj([poly], 1.)
    cv.line(C.hatch_poly(poly, ang, 1.))


def _in_ell(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2


# ----------------------------------------------------------------------------------------------
# the stage: curtain, spotlight, floor
# ----------------------------------------------------------------------------------------------

def _stage(cv, x, y, w, h, spot, floor_y, seed):
    """Ruled curtain whose folds are made by dropping every other line in the light; a spotlight
    ellipse `spot` (cx, cy, rx, ry) thins it to the light pitch; a ruled floor below floor_y."""
    rng = random.Random(seed)
    cv.obj([], 0)
    scx, scy, srx, sry = spot
    P = max(14., w / 9)
    ph = rng.random() * 6
    # the beam: a cone from the top centre widening to the floor
    def lit(xx, yy):
        t = (yy - y) / max(1., floor_y - y)
        half = srx * (.35 + .65 * t)
        return abs(xx - scx) / half

    i = 0
    xx = x + .75
    while xx < x + w:
        runs = {.5: [], 1.: []}
        cur, cw_ = [], None
        yy = y
        while yy <= floor_y + .01:
            fold = .5 + .5 * math.sin(2 * PI * xx / P + ph + .5 * math.sin((yy - y) / max(h, 1) * 3 + xx / P))
            L = lit(xx, yy)
            wgt = None
            if L < 1:                      # in the light: pitch 3, then 6 at the core
                if i % 2 == 0 and (L > .6 or i % 4 == 0):
                    wgt = .5
            elif fold > .6:                 # the fold in shadow: every line
                wgt = .5
            elif fold > .22:                # half-tone
                wgt = .5 if i % 2 == 0 else None
            else:                           # the lit crest of the fold
                wgt = .5 if i % 4 == 0 else None
            if wgt != cw_:
                if cw_ is not None and len(cur) > 1:
                    runs[cw_].append(cur)
                cur = [cur[-1]] if (cur and wgt is not None and cw_ is not None) else []
                cw_ = wgt
            if wgt is not None:
                cur.append((xx, yy))
            yy += 1.5
        if cw_ is not None and len(cur) > 1:
            runs[cw_].append(cur)
        cv.hair(runs[.5])
        cv.line(runs[1.])
        i += 1
        xx += 1.5
    # pelmet: a scalloped valance with a black shadow under it at the top
    vh = max(4., h * .06)
    sc = []
    nsc = max(4, int(w / max(18., vh * 3)))
    for k in range(nsc * 12 + 1):
        t = k / (nsc * 12)
        sc.append((x + w * t, y + vh * (.55 + .45 * abs(math.sin(PI * t * nsc)))))
    val = [(x - 1, y - 1), (x + w + 1, y - 1)] + sc[::-1]
    cv.obj([val], 1.)
    cv.hair(C.hatch_poly(val, 90, 3, .7))
    cv.line([(p[0], p[1] + 1.4) for p in sc])
    # floor: boards receding, lines closing up toward the back; lighter in the pool of light
    fl = [(x - 1, floor_y), (x + w + 1, floor_y), (x + w + 1, y + h + 1), (x - 1, y + h + 1)]
    cv.obj([fl], 1.)
    yy = floor_y + 1.5
    k = 0
    while yy < y + h:
        seg = []
        xx = x
        while xx <= x + w:
            lit = _in_ell(xx, yy, scx, floor_y + (y + h - floor_y) * .45, srx * 1.15, (y + h - floor_y) * .7)
            if lit > 1 or k % 2 == 0:
                seg.append((xx, yy))
            else:
                if len(seg) > 1:
                    cv.hair(seg)
                seg = []
            xx += 3
        if len(seg) > 1:
            cv.hair(seg)
        k += 1
        yy += 1.5 + (yy - floor_y) * .08
    cv.line([(x, floor_y), (x + w, floor_y)])


# ----------------------------------------------------------------------------------------------
# the tenor saxophone
# ----------------------------------------------------------------------------------------------

def _across(R, side, d, u0, u1, frac_ok=lambda f: True):
    """Polyline d px in from the `side` edge across the tube (may pass the centre line)."""
    segs, cur = [], []
    step = 1.2 / R.L
    u = u0
    while u <= u1 + 1e-9:
        wa, wb = R.width(u, side), R.width(u, -side)
        D = wa + wb
        if d < D - .8 and frac_ok(d / D):
            s = side * (1 - d / wa) if d < wa else -side * ((d - wa) / wb)
            cur.append(R.at(u, s))
        else:
            if len(cur) > 1:
                segs.append(cur)
            cur = []
        u += step
    if len(cur) > 1:
        segs.append(cur)
    return segs


def _tube(cv, R, side, u0, u1):
    """Bulino on a round tube lit from the far side: lines along the form, 1.5 px apart in the
    shadow third, 3 px through the half-tone, a clear highlight band, one reflected-light line."""
    d = 1.2
    while d < 60:
        lim = .34 if d < 1e9 else 0
        cv.hair(_across(R, side, d, u0, u1, lambda f: f < .36))
        d += 1.5
    d = 1.2
    while d < 120:
        cv.hair(_across(R, side, d, u0, u1, lambda f: .36 <= f < .6))
        d += 3.
    cv.hair(_across(R, -side, 1.3, u0, u1))


def sax(cv, x, y, H, detail=1.):
    """A tenor sax whose bbox top-left is about (x, y), height about .88*H (width ~.78*H).
    Returns (bell_centre, bell_axis_angle, foot_point)."""
    def P(u, v):
        return (x + (u + .06) * H, y + v * H)

    # crook (neck) from mouthpiece to body
    neck = _bez(P(.02, .035), P(.12, .005), P(.22, .03), P(.27, .15), 20)
    nw = [H * (.014 + .012 * i / 20) for i in range(21)]
    # body, bow, bell tube, flare
    pts = [P(.27, .15), P(.275, .4), P(.28, .70)]
    for k in range(1, 13):
        a = PI - PI * k / 12
        pts.append(P(.39 + .11 * math.cos(a), .70 + .11 * math.sin(a)))
    pts += [P(.505, .5), P(.515, .38), P(.535, .30), P(.555, .245), P(.575, .205)]
    hw = [.04, .046, .056] + [.06 + .006 * k / 12 for k in range(1, 13)] + [.072, .08, .09, .115, .15]
    pts, hw = _resample(pts, [v * H for v in hw], 1.2)
    R = _Rib(pts, hw, hw)
    ub = None   # where the bow ends (the bell side starts)
    for i, p in enumerate(pts):
        if p[0] > P(.5, 0)[0] and ub is None:
            ub = i / (len(pts) - 1)

    # mouthpiece and ligature
    mpp, mpw = _resample([P(-.05, .045), P(.025, .034)], [H * .012, H * .02], 1.)
    mp = _Rib(mpp, mpw, mpw)
    _solid(cv, mp.outline(), 30)
    npts, nww = _resample(neck, nw, 1.)
    N = _Rib(npts, nww, nww)
    cv.obj([N.outline()], 1.)
    cv.hair(C._fill_lines(N, -.15, -.98, 1.5, 0, 1, 3))
    C._shadow(cv, N, -1, max(.8, H * .007), .05, .95)
    # octave key on the crook
    if H > 70:
        a, b = N.at(.55, 1), N.at(.75, 1)
        cv.line([a, (a[0] + H * .01, a[1] - H * .02), (b[0] + H * .01, b[1] - H * .02), b])

    # the main tube
    cv.obj([R.outline()], 1.)
    # body: light from the left; contour lines heavy on the right (−side on the way down,
    # +side on the way up the bell), a highlight band left clear.
    _tube(cv, R, -1, 0, ub)
    _tube(cv, R, 1, ub, .985)
    C._shadow(cv, R, -1, max(1., H * .014), .02, ub + .02)
    C._shadow(cv, R, 1, max(1., H * .014), ub - .04, .9)
    # ribs and solder rings: body ferrule, bow guard, bell brace
    for u in (.02, ub - .26, ub - .02, .86):
        if 0 < u < 1:
            cv.line([R.at(u, -1), R.at(u, 1)])
            cv.hair([R.at(u + 1.6 / R.L, -1), R.at(u + 1.6 / R.L, 1)])
    # the bell-to-body brace
    if H > 50:
        a, b = R.at(.18, -1), R.at(ub + .12, -1)
        br = [(a[0], a[1] + H * .1), (b[0], a[1] + H * .1)]
        cv.obj([[(br[0][0], br[0][1] - H * .012), (br[1][0], br[1][1] - H * .012),
                 (br[1][0], br[1][1] + H * .012), (br[0][0], br[0][1] + H * .012)]], 1.)
        cv.hair([(br[0][0], br[0][1] + H * .005), (br[1][0], br[1][1] + H * .005)])

    # acanthus engraved on the bell (real sax bells carry exactly this)
    if H * detail > 150:
        bx, by = R.at(.9, .1)
        C.acanthus_frond(bx, by, -60, H * .085, n=3, spread=34, bend=.8, curl=4, seed=3, cv=cv)
        bx, by = R.at(.8, -.2)
        C.acanthus_frond(bx, by, -100, H * .06, n=2, spread=30, bend=-.8, curl=-4, seed=5, cv=cv)

    # key cups with pearl touches, down the front of the body and up the bell side
    keys = [(.07, .55), (.12, .6), (.17, .6), (.25, .55), (.31, .6), (.37, .6)]
    keys += [(ub + .05, -.45), (ub + .11, -.5), (ub + .17, -.5)]
    rk = max(1.4, H * .028)
    for u, s in keys:
        if u >= 1:
            continue
        kx, ky = R.at(u, s)
        cup = _ell(kx, ky, rk, rk * .9, 18)
        cv.obj([cup], 1.)
        if rk > 2.5:
            cv.hair([(p[0], p[1]) for p in _ell(kx, ky, rk * .55, rk * .5, 14)] + [_ell(kx, ky, rk * .55, rk * .5, 14)[0]])
            cv.obj([[(kx + rk * .55 * math.cos(t), ky + rk * .5 * math.sin(t)) for t in
                     [PI * (-.1 + .7 * i / 8) for i in range(9)]]], 0)
            cv.line([(kx + rk * .55 * math.cos(t) * .8, ky + rk * .5 * math.sin(t) * .8) for t in
                     [PI * (-.05 + .6 * i / 8) for i in range(9)]])
    # key rods running along the body
    if H > 60:
        cv.obj([], 0)
        cv.line(R.contour(.92, .06, .4))
        cv.hair(R.contour(.8, .06, .38))

    # bell mouth: an ellipse across the flare's end, black throat, rim highlight
    e0, e1 = R.at(1, -1), R.at(1, 1)
    bc = ((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2)
    ax = math.atan2(e1[1] - e0[1], e1[0] - e0[0])
    ra = math.hypot(e1[0] - e0[0], e1[1] - e0[1]) / 2
    rb = ra * .32
    rim = [(bc[0] + ra * math.cos(t) * math.cos(ax) - rb * math.sin(t) * math.sin(ax),
            bc[1] + ra * math.cos(t) * math.sin(ax) + rb * math.sin(t) * math.cos(ax)) for t in
           [2 * PI * i / 40 for i in range(40)]]
    cv.obj([rim], 1.5)
    th = [(bc[0] + .78 * (p[0] - bc[0]), bc[1] + .7 * (p[1] - bc[1]) + rb * .15) for p in rim]
    cv.obj([th], 0)
    cv.line(C.hatch_poly(th, math.degrees(ax), 1.))
    cv.hair([rim[k] for k in range(22, 38)])
    foot = R.at(ub - .12, 1)
    return bc, ax, foot


def drumsticks(cv, cx, cy, L, ang=50.):
    """Two crossed drumsticks (the Easter egg): tapering, with oval tips and grain."""
    for sg in (-1, 1):
        a = math.radians(90 + sg * ang / 2 + 180)
        dx, dy = math.cos(a), math.sin(a)
        p0 = (cx - dx * L / 2, cy - dy * L / 2)
        p1 = (cx + dx * L / 2, cy + dy * L / 2)
        pts, ws = _resample([p0, p1], [max(1.2, L * .032), max(.9, L * .018)], 1.)
        ws = [w if i < len(ws) - 4 else L * .012 for i, w in enumerate(ws)]
        R = _Rib(pts, ws, ws)
        cv.obj([R.outline()], 1.)
        cv.hair(C._fill_lines(R, -.3, -.98, 1.5, 0, 1, 3))
        if L > 40:
            cv.hair(R.contour(.5, .1, .7))
        cv.obj([_ell(p1[0] + dx * L * .03, p1[1] + dy * L * .03, L * .03, L * .03, 14)], 1.)
        if L > 30:
            c = (p1[0] + dx * L * .03, p1[1] + dy * L * .03)
            cv.hair([(c[0] + L * .012, c[1] - L * .018), (c[0] + L * .022, c[1] + L * .004)])


def cymbal(cv, cx, cy, r):
    """A tiny ride cymbal on its stand, lathed grooves, bell in the middle."""
    cv.obj([[(cx - .4, cy), (cx + .4, cy), (cx + .4, cy + r * 3), (cx - .4, cy + r * 3)]], .5)
    disc = _ell(cx, cy, r, r * .22, 30)
    cv.obj([disc], 1.)
    cv.hair([[(cx - r * f, cy + r * .22 * f * (-.2)), (cx + r * f, cy + r * .22 * f * (-.2))] for f in (.85, .6)])
    cv.hair(C.hatch_poly(disc, 0, 1.5, .5))
    _solid(cv, _ell(cx, cy - r * .1, r * .22, r * .12, 12))


_NOTES = []


def notes(cv, out, pts, s, seed):
    """Eighth notes and a beamed pair floating up from the bell; each wears a white halo that cuts
    the curtain behind it. Black heads/stems are appended to out (raw SVG)."""
    rng = random.Random(seed)
    for k, (nx, ny) in enumerate(pts):
        beamed = (k % 3 == 1)
        heads = [(nx, ny), (nx + s * 1.1, ny - s * .35)] if beamed else [(nx, ny)]
        top = min(h[1] for h in heads) - s * 1.5
        halo = [(nx - s * .7, ny + s * .6), (heads[-1][0] + s * .8, heads[-1][1] + s * .6),
                (heads[-1][0] + s * (1.3 if not beamed else .8), top - s * .4), (nx - s * .7 + s * .5, top - s * .4)]
        cv.obj([halo], 0)
        d = ""
        for hx, hy in heads:
            hp = [(hx + s * .42 * math.cos(t) * math.cos(-.45) - s * .3 * math.sin(t) * math.sin(-.45),
                   hy + s * .42 * math.cos(t) * math.sin(-.45) + s * .3 * math.sin(t) * math.cos(-.45))
                  for t in [2 * PI * i / 14 for i in range(14)]]
            d += _d(hp, True, 0)
        sw = 1. if s > 7 else .5
        st = "".join(f"M{_n(hx + s * .36)},{_n(hy - s * .1)}V{_n(top if not beamed else top + (hx - nx) * -.32)}"
                     for hx, hy in heads)
        if beamed:
            bm = [(nx + s * .36, top), (heads[1][0] + s * .36, top - s * .35),
                  (heads[1][0] + s * .36, top - s * .35 + s * .28), (nx + s * .36, top + s * .28)]
            d += _d(bm, True, 0)
        else:
            fx = nx + s * .36
            st += f"M{_n(fx)},{_n(top)}c{_n(s * .1)},{_n(s * .5)} {_n(s * .8)},{_n(s * .5)} {_n(s * .5)},{_n(s * 1.3)}"
        out.append(f'<path d="{d}" fill="#000" stroke="none"/>'
                   f'<path d="{st}" stroke="#000" stroke-width="{sw}"/>')


# ----------------------------------------------------------------------------------------------
# the Hammond B3 (tall plates): cabinet, two manuals, drawbars, Leslie
# ----------------------------------------------------------------------------------------------

def organ(cv, x, y, w, h):
    """B3 seen three-quarter front: lid, two manuals, drawbars, turned legs, wood grain."""
    lid = [(x, y), (x + w, y), (x + w * 1.03, y + h * .06), (x - w * .03, y + h * .06)]
    cv.obj([lid], 1.)
    cv.hair(C.hatch_poly(lid, 0, 2))
    body = [(x, y + h * .06), (x + w, y + h * .06), (x + w, y + h * .72), (x, y + h * .72)]
    cv.obj([body], 1.)
    # wood grain: wavering lines down the case, darker to the right
    k = 0
    gx = x + 1.5
    while gx < x + w - 1:
        if not (k % 2 and gx < x + w * .55):
            cv.hair([(gx, y + h * .43), (gx, y + h * .72)])
        gx += 1.5
        k += 1
    # a carved panel on the case front
    pn = [(x + w * .1, y + h * .48), (x + w * .9, y + h * .48), (x + w * .9, y + h * .66), (x + w * .1, y + h * .66)]
    cv.obj([pn], 1.)
    cv.hair(C.hatch_poly(pn, 0, 3, 1))
    cv.line([(x + w * .1 + 1.5, y + h * .66 - 1.2), (x + w * .9 - 1.2, y + h * .66 - 1.2), (x + w * .9 - 1.2, y + h * .48 + 1.5)])
    # keyboard well (black) with two manuals of white keys and black sharps
    kw = [(x + w * .06, y + h * .12), (x + w * .94, y + h * .12), (x + w * .94, y + h * .42), (x + w * .06, y + h * .42)]
    _solid(cv, kw)
    for m in range(2):
        ky = y + h * (.17 + m * .12)
        kh = h * .08
        kx0, kx1 = x + w * .09 - m * w * .0, x + w * .91
        keys = [(kx0, ky), (kx1, ky), (kx1, ky + kh), (kx0, ky + kh)]
        cv.obj([keys], .5)
        nk = int((kx1 - kx0) / 2.5)
        cv.hair([[(kx0 + (kx1 - kx0) * j / nk, ky), (kx0 + (kx1 - kx0) * j / nk, ky + kh)] for j in range(1, nk)])
        for j in range(nk):
            if j % 7 in (0, 1, 3, 4, 5):
                bx = kx0 + (kx1 - kx0) * (j + .7) / nk
                cv.obj([[(bx, ky), (bx + (kx1 - kx0) / nk * .6, ky),
                         (bx + (kx1 - kx0) / nk * .6, ky + kh * .6), (bx, ky + kh * .6)]], 0)
                cv.line([[(bx + .5, ky), (bx + .5, ky + kh * .6)]])
    # drawbars above the manuals
    for j in range(9):
        dx = x + w * (.28 + .05 * j)
        ln = h * (.012 + .03 * ((j * 5 + 3) % 7) / 7)
        cv.obj([[(dx - 1.2, y + h * .118 - ln), (dx + 1.2, y + h * .118 - ln), (dx + 1.2, y + h * .118), (dx - 1.2, y + h * .118)]], 0)
        cv.line([[(dx - .6, y + h * .118 - ln), (dx - .6, y + h * .118)], [(dx + .6, y + h * .118 - ln), (dx + .6, y + h * .118)]])
    # skirt and legs
    sk = [(x + w * .02, y + h * .72), (x + w * .98, y + h * .72), (x + w * .95, y + h * .8), (x + w * .05, y + h * .8)]
    cv.obj([sk], 1.)
    cv.hair(C.hatch_poly(sk, 0, 1.5))
    for lx in (x + w * .08, x + w * .92):
        leg = [(lx - w * .03, y + h * .8), (lx + w * .03, y + h * .8), (lx + w * .015, y + h), (lx - w * .015, y + h)]
        cv.obj([leg], 1.)
        cv.hair(C.hatch_poly(leg, 90, 1.5))
    # pedalboard
    pb = [(x + w * .15, y + h * .93), (x + w * .85, y + h * .93), (x + w * .9, y + h), (x + w * .1, y + h)]
    cv.obj([pb], 1.)
    cv.hair([[(x + w * (.15 + .05 * j), y + h * .93), (x + w * (.1 + .057 * j), y + h)] for j in range(1, 14)])


# ----------------------------------------------------------------------------------------------
# path lettering (stroked block capitals on a 4 x 6 grid)
# ----------------------------------------------------------------------------------------------

_GL = {
    "J": [[(4, 0), (4, 4.6), (2.8, 6), (1.2, 6), (0, 4.8)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2.2), (3, 3.2), (0, 3.2)]],
    "O": [[(1.2, 0), (2.8, 0), (4, 1.4), (4, 4.6), (2.8, 6), (1.2, 6), (0, 4.6), (0, 1.4), (1.2, 0)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2.2), (3, 3.2), (0, 3.2)], [(2.2, 3.2), (4, 6)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "D": [[(0, 0), (0, 6), (2.6, 6), (4, 4.6), (4, 1.4), (2.6, 0), (0, 0)]],
    " ": [],
}


def letter_along(centre, text, size, out, sw=1.):
    """Letter `text` centred along the polyline `centre`, glyphs size px tall, upright to it."""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    adv = size * .95
    tw = adv * len(text) - size * .3
    s0 = L[-1] / 2 - tw / 2
    d = ""
    for k, ch in enumerate(text):
        s = s0 + k * adv + size * .33
        j = 0
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        t = (s - L[j]) / ((L[j + 1] - L[j]) or 1)
        px = centre[j][0] + (centre[j + 1][0] - centre[j][0]) * t
        py = centre[j][1] + (centre[j + 1][1] - centre[j][1]) * t
        a = math.atan2(centre[j + 1][1] - centre[j][1], centre[j + 1][0] - centre[j][0])
        ca, sa = math.cos(a), math.sin(a)
        k6 = size / 6
        for stroke in _GL.get(ch, []):
            pts = []
            for gx, gy in stroke:
                lx, ly = (gx - 2) * k6, (gy - 3) * k6
                pts.append((px + lx * ca - ly * sa, py + lx * sa + ly * ca))
            d += _d(pts, tol=0)
    out.append(f'<path d="{d}" stroke="#000" stroke-width="{sw}" stroke-linecap="square" stroke-linejoin="miter"/>')


# ----------------------------------------------------------------------------------------------
# the vignette
# ----------------------------------------------------------------------------------------------

def trumpet_bell(cx, base_y, L):
    """A trumpet bell standing on the cartouche, mouth up, the crest's leaves sprouting from it."""
    cv = C.Canvas()
    pts, ws = [], []
    for i in range(25):
        t = i / 24
        pts.append((cx, base_y - L * t))
        ws.append(L * (.06 + .5 * t ** 3.2))
    R = _Rib(pts, ws, ws)
    cv.obj([R.outline()], 1.)
    _tube(cv, R, 1, 0, .97)
    C._shadow(cv, R, 1, max(1., L * .05), .1, .95)
    cv.line([R.at(.12, -1), R.at(.12, 1)])
    cv.hair([R.at(.16, -1), R.at(.16, 1)])
    top = R.at(1, 0)
    rim = _ell(top[0], top[1], ws[-1], ws[-1] * .22, 32)
    cv.obj([rim], 1.5)
    th = _ell(top[0], top[1] + ws[-1] * .03, ws[-1] * .78, ws[-1] * .14, 24)
    _solid(cv, th)
    return cv.svg()


def scene(x, y, w, h, seed, tall=False):
    """Everything inside the field box: stage, (organ), sticks + cymbal, sax, notes."""
    cv = C.Canvas()
    raw = []
    wide = w > h * 1.6
    H = h * (.98 if wide else .9 if tall else .84) / .88
    H = min(H, w * .95 / .8 if not tall else w * .6 / .8)
    sw_ = .8 * H
    if tall:
        sx = x + w * .07
    elif wide:
        sx = x + w * .5 - sw_ * .75
    else:
        sx = x + (w - sw_) / 2 - w * .07
    sy = y + h - .88 * H - h * (.01 if wide else .07 if tall else .04)
    floor_y = y + h * (.8 if tall else .83)
    spot = (sx + sw_ * .42, y + h * .5, max(sw_ * .62, 10), h * .58)
    _stage(cv, x - 2, y - 2, w + 4, h + 4, spot, floor_y, seed)
    if tall:
        ow = w * .42
        organ(cv, x + w * .56, floor_y - h * .42, ow, h * .42 + h * .04)
    # Easter egg: crossed sticks and a ride cymbal behind the sax
    stick_L = max(14., H * .42)
    drumsticks(cv, sx + sw_ * .1, sy + .62 * H, stick_L, 54)
    if H > 70:
        cymbal(cv, sx + sw_ * .02 - H * .03, sy + .35 * H, max(4., H * .07))
    bc, ax, foot = sax(cv, sx, sy, H, 1.)
    # notes climb from the bell up and to the right
    ns = max(4.5, min(11., H * .07))
    pts = []
    for k in range(3 if H > 60 or wide else 2):
        if wide:
            pts.append((bc[0] + ns * (1.6 + 2.3 * k), bc[1] + ns * (.9 - .5 * (k % 2) + .25 * k)))
        else:
            pts.append((bc[0] + ns * (1.1 + 1.9 * k), bc[1] - ns * (1.6 + 1.6 * k) + (ns * .6 if k == 1 else 0)))
    def inside(px, py):
        u = abs(px + ns - (x + w / 2)) / (w / 2)
        v = abs(py - ns * 1.6 - (y + h / 2)) / (h / 2)
        return u ** 2.6 + v ** 2.6 < .8 and px + ns * 1.5 < x + w and py - ns * 2 > y
    pts = [p for p in pts if inside(*p)]
    notes(cv, raw, pts, ns, seed)
    return cv.svg() + "".join(raw)


def _clipped(cid, clip_d, body):
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, copied and made bespoke: the field is engraved edge to edge)
# ----------------------------------------------------------------------------------------------

def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.1, 160)
    o.append(C._clip(C._uid("jb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = _d(_ell(cx, cy, rx - 4, ry - 4, 72), True, 0)
    o.append(_clipped(C._uid("jbf", w, h, seed), fd, scene(cx - rx + 4, cy - ry + 4, 2 * rx - 8, 2 * ry - 8, seed)))
    o.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _medium(w, h, seed):
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
                   max_n=6, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("jm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = cw / 2 - max(5., min(cw, gh + 4) * .07) * 1.6, (gh + 4) / 2 - max(5., min(cw, gh + 4) * .07) * 1.6
    o.append(_clipped(C._uid("jmf", w, h, seed), fd, scene(cx - a, cy - b, 2 * a, 2 * b, seed)))
    bp = C._superellipse(cx, cy, a - 1, b - 1)
    o.append(f'<path d="{_d(bp, True, .1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _keyboard_tablet(tx, ty, tw, th):
    """Fill the pedestal's sunk tablet with a piano keyboard (white keys, black sharps)."""
    nk = int(tw / 6.5)
    kw = tw / nk
    d = "".join(f"M{_n(tx + kw * j)},{_n(ty + 1)}V{_n(ty + th - .5)}" for j in range(1, nk))
    blk = ""
    for j in range(nk - 1):
        if (j % 7) in (0, 1, 3, 4, 5):
            bx = tx + kw * (j + .68)
            blk += f"M{_n(bx)},{_n(ty)}h{_n(kw * .64)}v{_n(th * .6)}h{_n(-kw * .64)}z"
    return (f'<path d="{d}" stroke="#000" stroke-width=".5"/>'
            f'<path d="{blk}" fill="#000" stroke="none"/>'
            f'<path d="M{_n(tx)},{_n(ty + th - 2)}h{_n(tw)}" stroke="#000" stroke-width=".5"/>')


def _tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h + ped_h * .3
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
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=4, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("jt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_clipped(C._uid("jtf", w, h, seed), fd, scene(cx - a, cy - b, 2 * a, 2 * b, seed, tall=True)))
    bp = C._superellipse(cx, cy, a - 1, b - 1)
    o.append(f'<path d="{_d(bp, True, .1)}" fill="none" stroke="#000" stroke-width="1"/>')
    psz = min(ch * .2 + top_free, 62)
    o.append(trumpet_bell(cx, cy - ch / 2 + 9, psz * .55))
    o.append(C.palmette(cx, cy - ch / 2 + 9 - psz * .53, psz * .75, True, rng.randrange(1 << 20)))
    rh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, rh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lt = []
    letter_along(centre, "JAZZ IN PORTLAND", rh * .5, lt, 1.)
    o.append("".join(lt))
    py = h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_keyboard_tablet(tx + 2, ty + 2, tw - 3, th - 3))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
