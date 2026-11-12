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


# ==============================================================================================
# KING-TIER KIT (batch 7). Fine English scroll as on the GRS vise, the Hunt panels and the
# presentation Colt: dozens of small true spirals grown from one stem and branching on in a
# continuous rhythm, every leaf cut with fine parallel shading on its shadow side and a bright
# edge; the ground between punched to a dark matte; every panel framed in gold-line borders and
# beading; the page's subject set in an inlaid, bead-ringed portrait medallion.
#   kk_defs()                         the matte and bead patterns (put once in the body)
#   kk_matte(d)                       punched matte ground filling path d
#   kk_field(cv, box, obst, roots, seed, rmin, rmax)   the scroll field (see its doc)
#   kk_frame(x, y, w, h, ...)         gold-line + beaded border round a panel; corner rosettes
#   kk_medallion(cx, cy, rx, ry)      bead-ringed inlay setting -> (svg_under, svg_over, clip d)
#   kk_plate(w, h, scene, egg, seed)  the whole plate at any size (band / cartouche / tall)
# ==============================================================================================
import math as _m
import random as _r
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _PI


def _kn(x):
    return _C._n(x)


# ---- matte, beads -----------------------------------------------------------------------------

def kk_defs():
    rng = _r.Random(11)
    cells = set()
    while len(cells) < 8:
        cells.add((rng.randrange(6), rng.randrange(6)))
    punch = "".join(f"M{x},{y}h1v1h-1z" for x, y in sorted(cells))
    return ('<defs><pattern id="kkM" width="6" height="6" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h6v6h-6z" fill="#000"/><path d="{punch}" fill="#fff"/></pattern></defs>')


def kk_matte(d):
    return f'<path d="{d}" fill="url(#kkM)" stroke="none"/>'


def kk_rect_d(x, y, w, h):
    return f"M{_kn(x)},{_kn(y)}h{_kn(w)}v{_kn(h)}h{_kn(-w)}z"


def _kk_ell_d(cx, cy, rx, ry, n=72):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n)[:-1], True, .1)


def kk_beads(pts, r=1.5):
    """Beads (white, .5 outlined, a black shadow speck lower right) centred on pts. 2 elements."""
    rr = _kn(r)
    a = "".join(f"M{_kn(x - r)},{_kn(y)}a{rr},{rr} 0 1,0 {_kn(2 * r)},0a{rr},{rr} 0 1,0 {_kn(-2 * r)},0z" for x, y in pts)
    s = max(.5, round(r * .7 * 2) / 2)
    b = "".join(f"M{_kn(x + r * .25)},{_kn(y + r * .2)}h{_kn(s)}v{_kn(s)}h{_kn(-s)}z" for x, y in pts)
    return (f'<path d="{a}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{b}" fill="#000" stroke="none"/>')


def _kk_along(poly, pitch, closed=True):
    """Points spaced `pitch` apart along a polyline."""
    P = poly + [poly[0]] if closed else poly
    out = []
    carry = 0.
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        L = _m.hypot(bx - ax, by - ay)
        t = carry
        while t < L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L))
            t += pitch
        carry = t - L
    return out


# ---- the scroll field -----------------------------------------------------------------------

def _kk_leaf(cv, x, y, ang, L, W, c, teeth=2, seed=0):
    """A small acanthus leaf: rolled tip, forward rounded teeth on its outer edge, a vein, fine
    parallel cuts on its shadow side (+c, the side it curls toward), a bright outer edge."""
    n = max(8, int(L / 1.1))
    pts = _C._euler(x, y, ang, L, lambda u: c * (.5 + 3.4 * _C._smooth(.55, 1., u) ** 2) / L * 1.6, n)
    ph = (seed * .41) % 1.

    def prof(u, t, amp):
        w = W * (u ** .5) * ((1 - u) ** .75) / .41 + .3
        if t and .3 < u < .97:
            v = ((u - .3) / .67 * t + ph * .3) % 1.
            w *= 1 - amp * (1 - v) ** 2
        return w
    wo = [prof(i / n, teeth, .36) for i in range(n + 1)]
    wi = [prof(i / n, 0, 0) * .85 for i in range(n + 1)]
    R = _C._Rib(pts, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    # burin cuts: curved strokes that leave the light half and sweep forward over the shadow
    # half to the edge, following the leaf's own curve; longer (darker) toward the root
    Lr = R.L
    du = 1.5 / Lr
    cuts = []
    u = .05
    while u < .9:
        s0 = -.5 * c * (1 - u) ** .6
        cuts.append([R.at(u, s0), R.at(u + .08, .93 * c)])
        u += du
    out = []
    for k, q in enumerate(cuts):
        out.extend(q if k % 2 == 0 else q[::-1])
    if out:
        cv.hair(out)
    if W > 2.6:
        cv.line(R.inset(c, lambda u: .5 if .12 < u < .88 else None, .05, .95))
    return R


class _KKSpiral:
    __slots__ = ("cx", "cy", "r", "w", "par", "kids", "pts", "S", "deg")

    def __init__(self, cx, cy, r):
        self.cx, self.cy, self.r = cx, cy, r
        self.w = 1
        self.par = None
        self.kids = []
        self.pts = None


def _kk_spiral_pts(cx, cy, R, th0, w, turns=1.45, end=.15):
    T = _TAU * turns
    b = -_m.log(end) / T
    n = max(24, int(R * T * .35))
    return [(cx + R * _m.exp(-b * T * i / n) * _m.cos(th0 + w * T * i / n),
             cy + R * _m.exp(-b * T * i / n) * _m.sin(th0 + w * T * i / n)) for i in range(n + 1)]


def _kk_bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _kk_resample(pts, step=1.5):
    out = [pts[0]]
    acc = 0.
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = _m.hypot(bx - ax, by - ay)
        if L == 0:
            continue
        t = step - acc
        while t <= L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L))
            t += step
        acc = (acc + L) % step
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def kk_field(cv, box, obst, roots, seed=0, rmin=6., rmax=16., grid=None, leafy=1., inside=None):
    """Fill box (x, y, w, h) with fine scroll. obst: shapes kept clear, ('e', cx, cy, rx, ry)
    ellipses, ('r', x0, y0, x1, y1) rects and ('c', cx, cy, r) circles. roots: [(x, y, ang_degrees)] stem sources: every
    spiral is joined, by a stem branching tangentially off its neighbour, back to a root, so the
    whole field flows from them. inside(x, y) -> bool optionally limits the field to a shape.
    Spirals are packed largest-first (radius rmax down to rmin) and painted from the twigs back
    to the root, so each parent stem lies over the branches it throws."""
    x, y, w, h = box
    rng = _r.Random(seed)
    grid = grid or max(3., min(4.5, rmin * .36))
    nx, ny = max(2, int(w / grid)), max(2, int(h / grid))
    gx = w / nx
    gy = h / ny
    D = []
    for j in range(ny):
        py = y + (j + .5) * gy
        for i in range(nx):
            px = x + (i + .5) * gx
            d = min(px - x, x + w - px, py - y, y + h - py) + rmin * .35
            if inside is not None and not inside(px, py):
                d = -1.
            for o in obst:
                if o[0] == "c":
                    continue
                if o[0] == "e":
                    _, ox, oy, rx, ry = o
                    q = _m.hypot((px - ox) / rx, (py - oy) / ry)
                    dd = (q - 1) * min(rx, ry)
                else:
                    _, x0, y0, x1, y1 = o
                    ddx = max(x0 - px, 0., px - x1)
                    ddy = max(y0 - py, 0., py - y1)
                    dd = _m.hypot(ddx, ddy) if (ddx or ddy) else -1.
                if dd < d:
                    d = dd
            D.append(d)

    def stamp(cx, cy, r, reach):
        i0, i1 = max(0, int((cx - reach - x) / gx)), min(nx - 1, int((cx + reach - x) / gx))
        j0, j1 = max(0, int((cy - reach - y) / gy)), min(ny - 1, int((cy + reach - y) / gy))
        for jj in range(j0, j1 + 1):
            qy = y + (jj + .5) * gy
            base = jj * nx
            for ii in range(i0, i1 + 1):
                dd = _m.hypot(x + (ii + .5) * gx - cx, qy - cy) - r
                if dd < D[base + ii]:
                    D[base + ii] = dd
    for o in obst:
        if o[0] == "c":
            stamp(o[1], o[2], o[3], o[3] + rmax + 2)
    sp = []
    while len(sp) < 400:
        m = max(D)
        if m < rmin:
            break
        k = D.index(m)
        i, j = k % nx, k // nx
        px, py = x + (i + .5) * gx, y + (j + .5) * gy
        r = min(rmax, m) * rng.uniform(.86, 1.)
        r = max(r, rmin)
        s = _KKSpiral(px + rng.uniform(-.4, .4) * gx, py + rng.uniform(-.4, .4) * gy, r)
        sp.append(s)
        reach = r + rmax + 2
        i0, i1 = max(0, int((px - reach - x) / gx)), min(nx - 1, int((px + reach - x) / gx))
        j0, j1 = max(0, int((py - reach - y) / gy)), min(ny - 1, int((py + reach - y) / gy))
        for jj in range(j0, j1 + 1):
            qy = y + (jj + .5) * gy
            base = jj * nx
            for ii in range(i0, i1 + 1):
                qx = x + (ii + .5) * gx
                dd = _m.hypot(qx - s.cx, qy - s.cy) - r * .97
                if dd < D[base + ii]:
                    D[base + ii] = dd
    if not sp:
        return
    # the tree: Prim from the roots
    done = []
    todo = list(sp)
    rootn = []
    for (rx_, ry_, ra) in roots:
        rn = _KKSpiral(rx_, ry_, 0.)
        rn.pts = None
        rn.deg = ra
        rootn.append(rn)

    def gap(a, b):
        return _m.hypot(a.cx - b.cx, a.cy - b.cy) - a.r - b.r
    best = {}
    for s in todo:
        bd, bp = 1e9, None
        for rn in rootn:
            dd = _m.hypot(s.cx - rn.cx, s.cy - rn.cy) - s.r
            if dd < bd:
                bd, bp = dd, rn
        best[id(s)] = (bd, bp)
    order = []
    while todo:
        s = min(todo, key=lambda q: best[id(q)][0])
        todo.remove(s)
        s.par = best[id(s)][1]
        s.par.kids.append(s)
        order.append(s)
        for q in todo:
            dd = gap(q, s) * 1.0
            if dd < best[id(q)][0]:
                best[id(q)] = (dd, s)
    # geometry, from the roots outward: winding alternates (S-rhythm), the stem leaves its parent
    # running forward and arrives tangentially at the child's outer turn
    for s in order:
        p = s.par
        dx, dy = s.cx - p.cx, s.cy - p.cy
        dl = _m.hypot(dx, dy) or 1.
        ux, uy = dx / dl, dy / dl                 # parent -> child
        if p.pts is None:                         # a root
            pa = _m.radians(p.deg)
            P0, t0 = (p.cx, p.cy), (_m.cos(pa), _m.sin(pa))
            # wind so that arriving along t0 the curl turns away from the root's line
            cr = t0[0] * uy - t0[1] * ux
            s.w = 1 if cr >= 0 else -1
            if rng.random() < .25:
                s.w = -s.w
        else:
            s.w = -p.w if rng.random() < .82 else p.w
            # the branch point: on the parent's outer turn, nearest the child, heading toward it
            pts = p.pts
            lim = max(3, int(len(pts) * .5))
            bi, bv = 1, 1e9
            for i in range(1, lim):
                qx, qy = pts[i]
                tx, ty = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
                tl = _m.hypot(tx, ty) or 1.
                dd = _m.hypot(qx - s.cx, qy - s.cy)
                fw = (tx * (s.cx - qx) + ty * (s.cy - qy)) / tl / max(dd, 1.)
                v = dd - fw * s.r * 1.2
                if v < bv:
                    bv, bi = v, i
            P0 = pts[bi]
            tx, ty = pts[bi + 1][0] - pts[bi - 1][0], pts[bi + 1][1] - pts[bi - 1][1]
            tl = _m.hypot(tx, ty) or 1.
            t0 = (tx / tl, ty / tl)
            # if the parent runs away from the child here, wind the child to suit the turn
            cr = t0[0] * (s.cy - P0[1]) - t0[1] * (s.cx - P0[0])
            s.w = 1 if cr >= 0 else -1
            if rng.random() < .2:
                s.w = -s.w
        # the child's start point: where its tangent runs away from P0
        ddx, ddy = s.cx - P0[0], s.cy - P0[1]
        dl = _m.hypot(ddx, ddy) or 1.
        dx_, dy_ = -ddx / dl, -ddy / dl           # child -> P0
        R = s.r * .86
        if s.w > 0:
            nvx, nvy = -dy_, dx_
        else:
            nvx, nvy = dy_, -dx_
        # rotate the start a little forward so the stem wraps into the curl
        th0 = _m.atan2(nvy, nvx) - s.w * .35
        spi = _kk_spiral_pts(s.cx, s.cy, R, th0, s.w, rng.uniform(1.3, 1.6))
        S0 = spi[0]
        st = (spi[1][0] - S0[0], spi[1][1] - S0[1])
        sl = _m.hypot(*st) or 1.
        st = (st[0] / sl, st[1] / sl)
        L = _m.hypot(S0[0] - P0[0], S0[1] - P0[1])
        k = max(2., L * .42)
        stem = _kk_bez(P0, (P0[0] + t0[0] * k, P0[1] + t0[1] * k), (S0[0] - st[0] * k, S0[1] - st[1] * k), S0,
                    max(4, int(L / 2)))
        s.pts = _kk_resample(stem[:-1] + spi, 1.4)
        s.S = len(_kk_resample(stem[:-1], 1.4)) if len(stem) > 1 else 0
    # paint: twigs first, root last
    for s in order[::-1]:
        _kk_scroll(cv, s, rng, leafy)


def _kk_scroll(cv, s, rng, leafy):
    pts = s.pts
    n = len(pts)
    if n < 4:
        return
    iS = min(s.S, n - 3)
    R = s.r * .8
    w0 = max(1., min(3.2, R * .2))
    W = []
    for i in range(n):
        if i < iS:
            f = i / max(1, iS)
            W.append(w0 * (.55 + .45 * f))
        else:
            f = (i - iS) / max(1, n - 1 - iS)
            W.append(max(.45, w0 * (1 - .78 * f)))
    Rb = _C._Rib(pts, W, W)
    ins = s.w                                      # the spiral turns toward +normal when w > 0? test
    # normal side toward the centre at the spiral's start
    m = min(n - 2, iS + 2)
    q = Rb.at(m / (n - 1), 1.)
    ins = 1 if _m.hypot(q[0] - s.cx, q[1] - s.cy) < _m.hypot(pts[m][0] - s.cx, pts[m][1] - s.cy) else -1
    Ltot = Rb.L

    def tang(i):
        i = min(n - 2, max(1, i))
        a, b = pts[i - 1], pts[i + 1]
        return _m.atan2(b[1] - a[1], b[0] - a[0])
    # leaves on the outer side of the curl, nearer the root on top: laid from the eye back
    spots = []
    i = iS + 1
    lim = iS + int((n - iS) * .62)
    while i < lim:
        px, py = pts[i]
        rad = _m.hypot(px - s.cx, py - s.cy)
        ll = (s.r * 1.1 - rad * .2) * .9 * rng.uniform(.85, 1.1) * leafy ** .3
        ll = min(ll, s.r * 1.05)
        if ll < 3.2:
            break
        spots.append((i, ll, rad))
        i += max(2, int(ll * .62 / 1.4))
    # leaves along the connecting stem, alternating, springing forward
    st = []
    if iS > 6 and leafy > .3:
        j = 3
        side = 1
        while j < iS - 2:
            st.append((j, side))
            side = -side
            j += max(5, int(11 / 1.4))
    for (i, ll, rad) in spots[::-1]:
        b = Rb.at(i / (n - 1), -ins * .6)
        _kk_leaf(cv, b[0], b[1], tang(i) - ins * rng.uniform(.32, .5), ll, ll * .32, ins, 2 if ll > 6 else 1,
              rng.randrange(97))
    for (j, side) in st:
        b = Rb.at(j / (n - 1), side * .6)
        ll = min(9., s.r * .7) * rng.uniform(.8, 1.)
        if ll > 3:
            _kk_leaf(cv, b[0], b[1], tang(j) + side * .7, ll, ll * .3, -side, 1, rng.randrange(97))
    # the stem: a bright cut edge outside, a shadow line inside
    cv.obj([Rb.outline()], .5)
    if w0 > 1.2:
        cv.hair(Rb.contour(.3 * ins, 0., 1., minw=1.25))
    # one leaf rolling in toward the eye
    i = iS + int((n - iS) * .55)
    if i < n - 2 and s.r > 7:
        b = Rb.at(i / (n - 1), ins * .5)
        ll = s.r * .42
        _kk_leaf(cv, b[0], b[1], tang(i) + ins * .35, ll, ll * .28, ins, 1, rng.randrange(97))
    ex, ey = pts[-1]
    rr = max(.9, W[-1] * 1.3)
    cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)


# ---- frames, medallion --------------------------------------------------------------------

def kk_frame(x, y, w, h, bead=1.5, rosette=True):
    """A panel's border drawn just outside x..x+w, y..y+h: a gold wire (white 1.5 line in fine
    black rules), a bead row, a black fillet; corner rosettes. Returns (svg, outer margin)."""
    o = []
    m1 = 1.
    # the gold wire
    o.append(f'<path d="{kk_rect_d(x - 3, y - 3, w + 6, h + 6)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{kk_rect_d(x - 1.25, y - 1.25, w + 2.5, h + 2.5)}" fill="none" stroke="#000" stroke-width=".5"/>')
    # bead row in a white channel outside
    g = 3 + bead + 1.5
    o.append(f'<path d="{kk_rect_d(x - g - bead - 1.5, y - g - bead - 1.5, w + 2 * (g + bead + 1.5), h + 2 * (g + bead + 1.5))}'
             f'{kk_rect_d(x - 3.5, y - 3.5, w + 7, h + 7)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    pts = _kk_along([(x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)], bead * 2 + 1)
    o.append(kk_beads(pts, bead))
    e = g + bead + 1.5
    o.append(f'<path d="{kk_rect_d(x - e, y - e, w + 2 * e, h + 2 * e)}" fill="none" stroke="#000" stroke-width="1"/>')
    if rosette:
        for cx, cy in ((x - g, y - g), (x + w + g, y - g), (x + w + g, y + h + g), (x - g, y + h + g)):
            o.append(kk_rosette(cx, cy, bead * 2.6))
    return "".join(o), e


def kk_rosette(cx, cy, r):
    pet = []
    for i in range(8):
        a = i * _PI / 4
        pet.append([(cx + r * .3 * _m.cos(a - .5), cy + r * .3 * _m.sin(a - .5)),
                    (cx + r * _m.cos(a), cy + r * _m.sin(a)),
                    (cx + r * .3 * _m.cos(a + .5), cy + r * .3 * _m.sin(a + .5))])
    d = "".join(_C._d(p, True, 0) for p in pet)
    return (f'<path d="{_kk_ell_d(cx, cy, r + 1, r + 1, 24)}" fill="#000" stroke="none"/>'
            f'<path d="{d}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="{_kk_ell_d(cx, cy, r * .28, r * .28, 10)}" fill="#fff" stroke="#000" stroke-width=".5"/>')


def kk_medallion(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval scene: a black fillet, a bead ring, a gold wire and a fine
    rule. Returns (svg_over, clip_d of the scene, outer rx, outer ry)."""
    o = []
    g = 2.5
    a1, b1 = rx + g + bead, ry + g + bead
    outer = (rx + g + 2 * bead + 3.5, ry + g + 2 * bead + 3.5)
    o.append(f'<path d="{_kk_ell_d(cx, cy, outer[0], outer[1])}{_kk_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + g - .25, ry + g - .25)}" fill="none" stroke="#000" stroke-width=".5"/>')
    per = _C._ell_pts(cx, cy, a1, b1, 180)[:-1]
    o.append(kk_beads(_kk_along(per, bead * 2 + 1.1), bead))
    o.append(f'<path d="{_kk_ell_d(cx, cy, a1 + bead + 1, b1 + bead + 1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, outer[0] - .5, outer[1] - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), _kk_ell_d(cx, cy, rx + .5, ry + .5), outer[0], outer[1]


def kk_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
# ---- a leaner emitter: half-px path units, coarser simplification --------------------------

def _kk_pd(pen):
    o = pen.o
    out = []
    prev_m = False
    for t in o:
        if t[0] == "l" and prev_m:
            t = t[1:]
            out.append(t if t[0] == "-" else " " + t)
        else:
            out.append(t)
        prev_m = t[0] == "m"
    return "".join(out)


def _kk_zig(lines):
    """Join a sweep of hatch segments into boustrophedon polylines (the joins run along the
    region's edges, where an outline or vein is drawn anyway): about half the path data."""
    out = []
    cur = None
    flip = False
    last_v = None
    for a, b in lines:
        if flip:
            a, b = b, a
        if cur is not None and _m.hypot(a[0] - cur[-1][0], a[1] - cur[-1][1]) < 3.2:
            cur += [a, b]
        else:
            if cur:
                out.append(cur)
            cur = [a, b]
        flip = not flip
    if cur:
        out.append(cur)
    return out


def kk_svg(cv, q=2, tol_fill=.55, tol_line=.42):
    """Canvas.svg with path data in 1/q px (q=2: one device pixel) and slightly coarser
    simplification: the same occlusion, about 30 % fewer bytes."""
    if not cv.objs:
        return ""
    xs = [p[0] for o in cv.objs for poly in o[0] for p in poly] or [0.]
    ys = [p[1] for o in cv.objs for poly in o[0] for p in poly] or [0.]
    x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
    W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
    mask = [bytearray(W) for _ in range(H)]
    out = {.5: [], 1.: [], 1.5: []}
    for polys, ow, strokes in reversed(cv.objs):
        for w, lines in strokes.items():
            for pl in lines:
                _C._clip_runs(pl, mask, x0, y0, W, H, out[w])
        if ow:
            for poly in polys:
                _C._clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
        for poly in polys:
            _C._fill_mask(poly, mask, x0, y0, W, H)
    oq = _C._Q
    _C._Q = q
    try:
        T = f' transform="scale({_kn(1. / q) if q != 2 else ".5"})"'
        res = []
        pen = _C._Pen()
        for polys, _, _ in cv.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path{T} d="{_kk_pd(pen)}" fill="#fff" stroke="none"/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _C._Pen()
                for pl in out[w]:
                    pen.add(pl, False, tol_line if w < 1 else tol_line + .05)
                res.append(f'<path{T} d="{_kk_pd(pen)}" fill="none" stroke="#000" stroke-width="{_kn(w * q)}"/>')
    finally:
        _C._Q = oq
    return "".join(res)


# ---- shaped panels, offsets, bead rows ------------------------------------------------------

def kk_shape(kind, x, y, w, h, c=20.):
    """A panel outline (clockwise on screen): 'rect', 'cut' (cut corners c), 'arch' (an
    elliptical arch of rise c on a rectangle), 'oval'."""
    if kind == "cut":
        return [(x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c), (x + w - c, y + h),
                (x + c, y + h), (x, y + h - c), (x, y + c)]
    if kind == "arch":
        n = 28
        top = [(x + w / 2 - w / 2 * _m.cos(_PI * i / n), y + c - c * _m.sin(_PI * i / n)) for i in range(n + 1)]
        return top + [(x + w, y + h), (x, y + h)]
    if kind == "oval":
        return _C._ell_pts(x + w / 2, y + h / 2, w / 2, h / 2, 72)[:-1]
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def kk_offset(poly, d):
    """Offset a convex clockwise-on-screen polygon outward by d (inward if d < 0), mitred."""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1])
        e2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = _m.hypot(*e1) or 1.
        l2 = _m.hypot(*e2) or 1.
        n1 = (e1[1] / l1, -e1[0] / l1)            # outward for clockwise-on-screen
        n2 = (e2[1] / l2, -e2[0] / l2)
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        bl = _m.hypot(bx, by) or 1.
        cs = max(.35, (bx * n1[0] + by * n1[1]) / bl)
        out.append((p1[0] + bx / bl * d / cs, p1[1] + by / bl * d / cs))
    return out


class kk_inside:
    """Point-in-polygon test with the crossings of each scan row cached."""

    def __init__(self, poly):
        self.p = poly
        self.rows = {}

    def __call__(self, px, py):
        xs = self.rows.get(py)
        if xs is None:
            xs = []
            P = self.p
            n = len(P)
            for i in range(n):
                (ax, ay), (bx, by) = P[i], P[(i + 1) % n]
                if (ay > py) != (by > py):
                    xs.append(ax + (bx - ax) * (py - ay) / (by - ay))
            xs.sort()
            self.rows[py] = xs
        k = 0
        for x in xs:
            if x > px:
                break
            k += 1
        return k % 2 == 1


def _kk_pd_poly(poly, close=True):
    return _C._d(poly, close, .1)


def kk_bead_row(d, r=1.5, closed=True):
    """A row of beads along any path d: a black channel, white beads with round caps on a dash
    pattern, and a black speck in each bead's shadow. 3 elements, whatever the length."""
    p = r * 2 + 1.
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_kn(2 * r + 2)}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_kn(2 * r)}" stroke-dasharray="0 {_kn(p)}" stroke-linecap="round"/>'
            f'<path d="{d}" transform="translate(.5,.5)" fill="none" stroke="#000" stroke-width="1" stroke-dasharray="0 {_kn(p)}" stroke-linecap="round"/>')


def kk_border(poly, bead=1.5):
    """Gold-line border round a panel whose clockwise outline is poly: from the panel out, a 1 px
    rule, a bright gap, a fine rule, a bead row, a 1 px rule. Returns (svg, total width)."""
    o = []
    g1 = kk_offset(poly, .5)
    g2 = kk_offset(poly, 2.75)
    gb = kk_offset(poly, 4. + bead)
    ge = kk_offset(poly, 5.5 + 2 * bead)
    o.append(f'<path d="{_kk_pd_poly(ge)}{_kk_pd_poly(poly[::-1])}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_pd_poly(g1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_kk_pd_poly(g2)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_kk_pd_poly(gb), bead))
    o.append(f'<path d="{_kk_pd_poly(ge)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), 5.5 + 2 * bead + .5


def kk_ring(cx, cy, rx, ry, bead=1.5):
    """The inlay setting round an oval: a 1.5 rule, a gold gap, a fine rule, a bead ring, a rule.
    Returns (svg, outer rx, outer ry)."""
    o = []
    e = 5.5 + 2 * bead
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + e, ry + e)}{_kk_ell_d(cx, cy, rx, ry)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + .75, ry + .75)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + 2.75, ry + 2.75)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(kk_bead_row(_kk_ell_d(cx, cy, rx + 4 + bead, ry + 4 + bead), bead))
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + e - .5, ry + e - .5)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o), rx + e, ry + e


# ---- Easter eggs: small figures cut white out of the matte --------------------------------

def _kk_U(cx, cy, r, pts):
    return [(cx + px * r, cy + py * r) for px, py in pts]


def _kk_cut(cv, poly, ang=45., pitch=1.5):
    cv.hair(_kk_zig(_C.hatch_poly(poly, ang, pitch)))


def _kk_wline(cv, pts, hw):
    """A white line hw px each side of pts, cut out of the matte."""
    pts = _kk_resample(pts, 1.5) if len(pts) > 1 else pts
    if len(pts) < 2:
        return
    R = _C._Rib(pts, [hw] * len(pts), [hw] * len(pts))
    cv.obj([R.outline()], 0)


def kk_egg(kind, cx, cy, r):
    """A small engraved figure filling a disc of radius r (white relief, fine shadow cuts)."""
    cv = _C.Canvas()
    E = lambda pts: _kk_U(cx, cy, r, pts)
    if kind == "drumsticks" or kind == "arms":
        if kind == "arms":
            # a sun behind: a disc and rays
            rays = []
            for i in range(16):
                a = i * _TAU / 16
                r0, r1 = .42, (.92 if i % 2 == 0 else .72)
                rays.append(E([(r0 * _m.cos(a - .08), r0 * _m.sin(a - .08)), (r1 * _m.cos(a), r1 * _m.sin(a)),
                               (r0 * _m.cos(a + .08), r0 * _m.sin(a + .08))]))
            cv.obj(rays, .5)
            for p in rays[::2]:
                cv.hair([p[1], ((p[0][0] + p[2][0]) / 2, (p[0][1] + p[2][1]) / 2)])
            disc = _C._ell_pts(cx, cy, r * .4, r * .4, 28)[:-1]
            cv.obj([disc], 1.)
            cv.hair(_C._ell_pts(cx, cy, r * .3, r * .3, 22))
            cut = [p for p in disc if p[0] - cx + p[1] - cy > -r * .1]
            _kk_cut(cv, _C._ell_pts(cx + r * .08, cy + r * .08, r * .3, r * .3, 18)[:-1], -45, 1.5)
        for sg in (-1, 1):
            a = _m.radians(45 if sg > 0 else 135)
            ux, uy = _m.cos(a), _m.sin(a)
            vx, vy = -uy, ux
            L0, L1 = -.95, .95
            tw = lambda t: .035 + .06 * (t - L0) / (L1 - L0)
            pts = [(cx + r * (t * ux + tw(t) * vx), cy + r * (t * uy + tw(t) * vy)) for t in (L0, 0, L1)]
            pts += [(cx + r * (t * ux - tw(t) * vx), cy + r * (t * uy - tw(t) * vy)) for t in (L1, 0, L0)]
            cv.obj([pts], .5)
            cv.hair([(cx + r * (t * ux - tw(t) * .4 * vx), cy + r * (t * uy - tw(t) * .4 * vy)) for t in (L0 + .1, L1 - .1)])
            tip = (cx + r * L0 * ux, cy + r * L0 * uy)
            cv.obj([_C._ell_pts(tip[0], tip[1], r * .07, r * .07, 10)[:-1]], .5)
    elif kind == "cymbal":
        e = _C._ell_pts(cx, cy - r * .2, r * .9, r * .28, 40)[:-1]
        cv.obj([E([(-.05, .05), (.05, .05), (.05, .95), (-.05, .95)])], .5)
        cv.obj([e], .5)
        for k in (.25, .45, .65, .85):
            cv.hair(_C._ell_pts(cx, cy - r * .2, r * .9 * k, r * .28 * k, 28, 0, _PI))
        _kk_cut(cv, [p for p in e if p[1] > cy - r * .2], 60, 1.5)
        cv.obj([_C._ell_pts(cx, cy - r * .25, r * .14, r * .07, 12)[:-1]], .5)
    elif kind == "note":
        # two swung eighth notes, beamed: white heads cut with a shadow crescent, white stems
        for dx, dy in ((-.45, .5), (.35, .38)):
            hd = _C._ell_pts(cx + dx * r, cy + dy * r, r * .26, r * .17, 18)[:-1]
            hd = [(cx + dx * r + (px - cx - dx * r) * .94 - (py - cy - dy * r) * .35, cy + dy * r + (py - cy - dy * r) + (px - cx - dx * r) * .25) for px, py in hd]
            cv.obj([hd], .5)
            _kk_cut(cv, [p for p in hd if p[1] > cy + dy * r - r * .02], 60, 1.5)
            _kk_wline(cv, E([(dx + .22, dy - .05), (dx + .22, -.62 - (dy - .5) * .3)]), r * .045)
        beam = E([(-.25, -.66), (.6, -.82), (.6, -.64), (-.25, -.48)])
        cv.obj([beam], .5)
        _kk_cut(cv, beam, -10, 1.5)
        for k in range(3):
            _kk_wline(cv, E([(-.85 + k * .55, .88), (-.6 + k * .55, .88)]), .5)
    elif kind == "P":
        stem = E([(-.45, -.8), (-.12, -.8), (-.12, .8), (-.45, .8)])
        bowl = [(cx - r * .14 + r * .5 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .42 * _m.sin(t))
                for t in [(-_PI / 2) + _PI * i / 20 for i in range(21)]]
        inner = [(cx - r * .14 + r * .28 * _m.cos(t) * (1 if _m.cos(t) > 0 else .4), cy - r * .36 + r * .2 * _m.sin(t))
                 for t in [(-_PI / 2) + _PI * i / 16 for i in range(17)]]
        cv.obj([bowl + inner[::-1]], 1.)
        _kk_cut(cv, bowl + inner[::-1], -45, 1.5)
        cv.obj([stem], 1.)
        _kk_cut(cv, E([(-.25, -.8), (-.12, -.8), (-.12, .8), (-.25, .8)]), 90, 1.5)
        cv.obj([E([(-.62, .62), (.05, .62), (.05, .8), (-.62, .8)]), E([(-.62, -.8), (-.05, -.8), (-.05, -.66), (-.62, -.66)])], .5)
    elif kind == "bridge":
        for tx in (-.45, .45):
            cv.obj([E([(tx - .09, .85), (tx - .05, -.75), (tx, -.92), (tx + .05, -.75), (tx + .09, .85)])], .5)
            cv.hair([(cx + (tx + .03) * r, cy - r * .7), (cx + (tx + .05) * r, cy + r * .8)])
            cv.hair(E([(tx - .05, -.35), (tx + .05, -.35)]))
        deck = E([(-1, .3), (1, .3), (1, .4), (-1, .4)])
        cv.obj([deck], .5)
        main = [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)) for t in [-.45 + .9 * i / 20 for i in range(21)]]
        _kk_wline(cv, main, .7)
        for sg in (-1, 1):
            _kk_wline(cv, [(cx + sg * r * (.45 + .53 * k / 8), cy - r * .72 + r * 1.02 * (k / 8) ** 1.6) for k in range(9)], .7)
        for k in range(1, 9):
            t = -.45 + .9 * k / 9
            _kk_wline(cv, [(cx + r * t, cy - r * .72 + r * 1.0 * (1 - (t / .45) ** 2)), (cx + r * t, cy + r * .3)], .5)
    elif kind == "hood":
        m = E([(-1, .7), (-.55, .1), (-.2, -.55), (0, -.8), (.15, -.62), (.5, -.05), (1, .7)])
        cv.obj([m], .5)
        _kk_cut(cv, E([(0, -.8), (.15, -.62), (.5, -.05), (1, .7), (.1, .7)]), -60, 1.5)
        snow = E([(-.35, -.3), (-.2, -.55), (0, -.8), (.15, -.62), (.3, -.35), (.15, -.42), (.02, -.25), (-.12, -.4)])
        cv.obj([snow], .5)
        for k in range(5):
            t = -.3 + k * .15
            cv.hair(E([(0, -.75), (t * .6, -.35)]))
    elif kind == "heron":
        # a great blue heron standing in the shallows, facing left: S-curved neck, dagger bill,
        # a plume off the crown, long legs, the back feathers cut in fine lines
        body = E([(-.25, -.05), (.05, -.22), (.4, -.18), (.62, .02), (.72, .22), (.45, .18), (.1, .2), (-.18, .12)])
        cv.obj([body], .5)
        _kk_cut(cv, E([(.05, -.05), (.4, -.1), (.62, .02), (.72, .22), (.45, .18), (.1, .2)]), 20, 1.5)
        _kk_wline(cv, E([(-.12, -.08), (-.3, -.3), (-.22, -.5), (-.08, -.62), (-.2, -.78)]), r * .05)
        cv.obj([E([(-.28, -.84), (-.12, -.8), (-.1, -.74), (-.24, -.72)])], .5)
        _kk_wline(cv, E([(-.25, -.79), (-.72, -.72)]), r * .03)
        _kk_wline(cv, E([(-.12, -.83), (.12, -.88)]), r * .015)
        _kk_wline(cv, E([(.15, .18), (.1, .55), (.12, .9)]), r * .025)
        _kk_wline(cv, E([(.3, .18), (.32, .55), (.4, .9)]), r * .025)
        for k in range(5):
            _kk_wline(cv, E([(-.85 + k * .1, .93 + (k % 2) * .03), (-.55 + k * .3, .93)]), .5)
    elif kind == "kranok":
        # a Thai kranok flame: a tall leaf rising, its back serrated into flame tongues, the tip
        # hooking over, a smaller flame nested inside it and a curl at its foot
        _kk_leaf(cv, cx - r * .25, cy + r * .9, -_PI / 2 + .25, r * 1.85, r * .5, -1, 4, 3)
        _kk_leaf(cv, cx - r * .1, cy + r * .7, -_PI / 2 + .35, r * 1.1, r * .3, -1, 2, 5)
        _kk_wline(cv, [(cx - r * .25 + r * .4 * _m.cos(t), cy + r * .62 + r * .3 * _m.sin(t)) for t in [_PI * (.1 + 1.4 * k / 12) for k in range(13)]], .6)
    elif kind == "elephant":
        b = E([(-.75, .1), (-.6, -.35), (-.1, -.5), (.3, -.45), (.55, -.6), (.8, -.4), (.85, 0), (.78, .4),
               (.7, .65), (.62, .3), (.55, .15), (.45, .7), (.3, .7), (.28, .25), (-.35, .25), (-.38, .7),
               (-.55, .7), (-.58, .2)])
        cv.obj([b], .5)
        _kk_cut(cv, E([(-.75, .1), (-.35, .25), (.28, .25), (.55, .15), (.5, -.1), (-.6, -.1)]), 20, 1.5)
        cv.hair(E([(.35, -.4), (.42, -.05), (.25, .05)]))
        cv.obj([E([(-.3, -.48), (.1, -.48), (.05, -.1), (-.25, -.1)])], .5)
        for k in range(4):
            cv.hair(E([(-.27 + k * .1, -.45), (-.25 + k * .1, -.13)]))
    elif kind == "panel":
        fr = E([(-.85, -.2), (.55, -.75), (.85, .2), (-.55, .75)])
        cv.obj([fr], 1.)
        _kk_cut(cv, fr, -22, 1.5)
        for k in (1, 2, 3):
            t = k / 4
            a = (-.85 + 1.4 * t, -.2 - .55 * t)
            b = (-.55 + 1.4 * t, .75 - .55 * t)
            cv.line(E([a, b]))
        cv.line(E([(-.7, .275), (.7, -.275)]))
        cv.line(E([(0, .4), (0, .95)]))
    elif kind == "pinwheel":
        for i in range(5):
            a0 = i * _TAU / 5
            arm = [(cx + r * .92 * t * _m.cos(a0 + 1.4 * t), cy + r * .92 * t * _m.sin(a0 + 1.4 * t)) for t in [k / 12 for k in range(13)]]
            arm2 = [(cx + r * .92 * t * _m.cos(a0 + .5 + 1.4 * t), cy + r * .92 * t * _m.sin(a0 + .5 + 1.4 * t)) for t in [k / 12 for k in range(12, -1, -1)]]
            poly = arm + arm2
            cv.obj([poly], .5)
            if i % 2 == 0:
                _kk_cut(cv, poly, a0 * 57 + 30, 1.5)
    elif kind == "paw":
        cv.obj([_C._ell_pts(cx, cy + r * .3, r * .38, r * .32, 20)[:-1]], .5)
        _kk_cut(cv, _C._ell_pts(cx + r * .05, cy + r * .35, r * .3, r * .24, 16)[:-1], -45, 1.5)
        for a in (-2.4, -1.85, -1.3, -.75):
            px, py = cx + r * .62 * _m.cos(a), cy + r * .1 + r * .62 * _m.sin(a)
            cv.obj([_C._ell_pts(px, py, r * .15, r * .19, 12)[:-1]], .5)
    elif kind == "fleur":
        mid = E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4), (-.1, .25), (-.22, -.2), (-.2, -.62)])
        cv.obj([mid], .5)
        _kk_cut(cv, E([(0, -.98), (.2, -.62), (.22, -.2), (.1, .25), (0, .4)]), 70, 1.5)
        cv.hair(E([(0, -.85), (0, .3)]))
        for sg in (-1, 1):
            pet = E([(sg * .12, .2), (sg * .45, -.25), (sg * .8, -.42), (sg * .95, -.2), (sg * .78, -.05),
                     (sg * .62, -.18), (sg * .45, .05), (sg * .3, .38)])
            cv.obj([pet], .5)
            _kk_cut(cv, pet, -sg * 50, 1.5)
            cv.obj([_C._ell_pts(cx + sg * r * .82, cy - r * .28, r * .1, r * .1, 10)[:-1]], .5)
        band = E([(-.42, .32), (.42, .32), (.42, .5), (-.42, .5)])
        cv.obj([band], .5)
        _kk_cut(cv, band, 90, 1.5)
        cv.obj([E([(-.15, .5), (.15, .5), (.1, .95), (0, .82), (-.1, .95)])], .5)
    else:   # "dog": a retriever's head in profile, looking left
        head = E([(.55, .9), (.35, .25), (.1, .05), (-.15, .05), (-.55, .12), (-.82, .05), (-.88, -.12),
                  (-.7, -.22), (-.35, -.3), (-.1, -.55), (.2, -.62), (.45, -.5), (.62, -.2), (.75, .35), (.9, .9)])
        cv.obj([head], .5)
        _kk_cut(cv, E([(.35, .25), (.62, -.2), (.75, .35), (.9, .9), (.55, .9)]), 75, 1.5)
        ear = E([(.15, -.55), (.42, -.48), (.5, -.1), (.42, .35), (.3, .4), (.22, .0)])
        cv.obj([ear], .5)
        _kk_cut(cv, ear, 80, 1.5)
        cv.obj([_C._ell_pts(cx - r * .86, cy - r * .1, r * .07, r * .07, 8)[:-1]], 1.)
        cv.line(_C._ell_pts(cx - r * .12, cy - r * .3, r * .05, r * .05, 8))
        cv.hair(E([(-.82, .05), (-.5, .1)]))
    return cv.svg()


def kk_roundel(cx, cy, r, kind, bead=1.2):
    """An egg in a small bead-ringed roundel on the matte."""
    ring, ox, oy = kk_ring(cx, cy, r, r, bead)
    return (f'<path d="{_kk_ell_d(cx, cy, r + .5, r + .5, 40)}" fill="url(#kkM)" stroke="none"/>'
            + kk_egg(kind, cx, cy, r * .86) + ring), ox


# ---- skies: burin lines that darken upward, broken by modelled cloud banks --------------------

def kk_cloud(cv, x0, x1, yb, hgt, rng):
    """A cumulus bank: a white heaped top, dark rounded underside cut in lines that follow it."""
    n = max(3, int((x1 - x0) / (hgt * .8)))
    bumps = []
    for i in range(n):
        t = (i + .5) / n
        r = hgt * (.35 + .55 * _m.sin(_PI * t) ** .7) * rng.uniform(.8, 1.1)
        bumps.append((x0 + (x1 - x0) * t, yb - r * .7, r))
    top = []
    N = int((x1 - x0) / 1.5) + 2
    for k in range(N + 1):
        x = x0 + (x1 - x0) * k / N
        y = yb
        for bx, by, br in bumps:
            dx = x - bx
            if abs(dx) < br:
                y = min(y, by - _m.sqrt(br * br - dx * dx))
        top.append((x, min(y, yb - .5)))
    bot = [(x1 - (x1 - x0) * k / 16, yb + hgt * .08 * _m.sin(_PI * k / 16)) for k in range(17)]
    cv.obj([top + bot], .5)
    # undersides: lines following the base, stacked up into the cloud, dense low and fading
    for j, d in enumerate([1., 2.5, 4., 5.5, 7.5, 10., 13.]):
        if d > hgt * .9:
            break
        cv.line([(x, max(y, yb - d)) for (x, y) in top if y < yb - d]) if j < 2 else cv.hair(
            [(x, max(y + d * .25, yb - d)) for (x, y) in top if y < yb - d - 1])
    # the heaped tops: a contour inside each bump on its shadow side
    for bx, by, br in bumps:
        if br > 4:
            cv.hair([(bx + br * .85 * _m.cos(a), by + br * .85 * _m.sin(a)) for a in [_PI * (.1 + .6 * i / 10) for i in range(11)]])


def kk_sky(cv, X, Y, W, yb, seed=0, clouds=2):
    """Sky from Y down to the horizon yb: 1 px rules at a 2 px pitch high up (dark), thinning to
    0.5 px at 2 then 3 px toward the horizon (light), with tapered 1 px bulino streaks swelling
    out of the mid sky, and cloud banks laid over it. Lines on the device grid (k/2 + 1/4)."""
    rng = _r.Random(seed * 17 + 3)
    cv.obj([[(X, Y), (X + W, Y), (X + W, yb), (X, yb)]], 0)
    H = yb - Y
    y = _m.floor(Y * 2) / 2 + .25
    while y < yb:
        f = (y - Y) / max(1., H)
        if f < .22:
            cv.line([(X, y + .25), (X + W, y + .25)])
            y += 2.
            continue
        cv.hair([(X, y), (X + W, y)])
        if f < .6 and rng.random() < .55:
            x = X + rng.uniform(-.2, 1.) * W
            L = rng.uniform(.15, .45) * W * (.6 - f) / .38
            cv.line([(x, y + .25), (x + L, y + .25)])
        y += 1.5 if f < .5 else (2. if f < .78 else 3.)
    for k in range(clouds):
        cw = W * rng.uniform(.28, .42)
        x0 = X + W * (.05 + .62 * (k / max(1, clouds - 1) if clouds > 1 else .3)) + rng.uniform(-8, 8)
        cb = Y + H * rng.uniform(.38, .62)
        kk_cloud(cv, x0, x0 + cw, cb, min(H * .2, cw * .25), rng)


# ---- the plate ------------------------------------------------------------------------------

def kk_plate(w, h, scene, egg="dog", seed=0, arms=False, egg2=None, dens=1., limit=188000):
    """The whole plate, edge to edge, by height:
      h < 110   band: a bead row and gold line hang under the text; the matte carries fine scroll
                flowing out both ways from an oval medallion (the scene); an egg roundel.
      110-260   a cut-cornered panel in a gold-line, beaded border; spandrels of scroll and
                rosettes outside it; the medallion at the centre, scroll flowing from its foot.
      > 260     an arched panel: a great oval copperplate scene; under it a roundel (the arms
                placeholder on fronts, else the egg); spandrels; a bordered frieze at the foot
                with scroll flowing both ways from a palmette.
    scene(x, y, w, h, mode) -> svg filling that rect (it is clipped to the oval)."""
    rng = _r.Random(seed)
    o = [kk_defs()]
    field = _C.Canvas()

    deferred = []

    def run_field(box, obst, roots, rmin, rmax, inside=None, poly=None, sd=0, area=None, cut=None):
        d = (_kk_pd_poly(poly) if poly else kk_rect_d(*box)) + (_kk_pd_poly(cut) if cut else "")
        o.append(kk_matte(d))
        if area is not None:
            deferred.append((len(o), box, obst, roots, rmin, rmax, inside, d, sd, area))
            o.append("")
            return
        cv = _C.Canvas()
        kk_field(cv, box, obst, roots, seed * 7 + sd, rmin * dens, rmax * dens, inside=inside)
        o.append(kk_clip(_C._uid("kkf", w, h, seed, sd), d, kk_svg(cv)))

    def finish():
        """The main field is grown last, its scroll size set so the plate lands under budget
        (field bytes ~ 19 * area / rmin^1.2, measured)."""
        for (k, box, obst, roots, rmin, rmax, inside, d, sd, area) in deferred:
            used = sum(len(t) for t in o) + 1800
            room = max(30000., limit - used)
            need = (20. * area / room) ** (1 / 1.2)
            f = max(dens, need / rmin)
            for tries in range(3):
                cv = _C.Canvas()
                kk_field(cv, box, obst, roots, seed * 7 + sd, rmin * f, rmax * f, inside=inside)
                o[k] = kk_clip(_C._uid("kkf", w, h, seed, sd), d, kk_svg(cv))
                over = used + len(o[k]) - limit - 6000
                if over <= 0:
                    break
                f *= (1 + over / len(o[k])) ** .85
        return _C.svg_doc(w, h, "".join(o))

    if h < 110:
        top = 8.
        gy, gh = top, h - top - 3
        cx, cy = w / 2, gy + gh / 2
        ry = gh / 2 - 7.5
        rx = min(w * .17, max(ry * 2.2, 26))
        obst = [("e", cx, cy, rx + 9, ry + 9)]
        er = min(gh / 2 - 7, 17)
        ex = w * (.13 if seed % 2 else .87)
        obst.append(("c", ex, cy, er + 7))
        run_field((0, gy, w, gh), obst, [(cx - rx - 8, cy, 180), (cx + rx + 8, cy, 0)],
                  max(4.5, gh * .1), max(9, gh * .33), sd=1, area=w * gh - _PI * (rx + 9) * (ry + 9) - _PI * (er + 7) ** 2)
        o.append(f'<path d="{_kk_ell_d(cx, cy, rx + 1, ry + 1)}" fill="#fff" stroke="none"/>')
        o.append(kk_clip(_C._uid("kks", w, h, seed), _kk_ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "band")))
        ring, _, _ = kk_ring(cx, cy, rx, ry, 1.)
        o.append(ring)
        rr, _ = kk_roundel(ex, cy, er, egg, 1.)
        o.append(rr)
        o.append(f'<path d="M0,1.5H{_kn(w)}M0,{_kn(top - .5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(kk_bead_row(f"M0,{_kn(top / 2 + .25)}H{_kn(w)}", 1., False))
        o.append(f'<path d="M0,{_kn(h - 1.5)}H{_kn(w)}" stroke="#000" stroke-width="1"{_C._CR}/>')
        o.append(f'<path d="M0,{_kn(h - 2.75)}H{_kn(w)}" stroke="#000" stroke-width=".5"{_C._CR}/>')
        return finish()

    if h <= 260:
        m = 10.
        c = min(30., h * .17)
        poly = kk_shape("cut", m, m, w - 2 * m, h - 2 * m, c)
        # the spandrels and margins: matte with small scroll
        outer = kk_inside(kk_offset(poly, 9.))
        run_field((0, 0, w, h), [], [(0, 0, 45), (w, 0, 135), (w, h, -135), (0, h, -45)], 4.5, 10.,
                  lambda px, py: not outer(px, py), sd=2, cut=kk_offset(poly, 4.))
        cx, cy = w / 2, h / 2
        ry = (h - 2 * m) / 2 - 12
        rx = min(w * .2, ry * 1.25)
        er = min(15., h * .1)
        ex = cx + (rx + 30 + er) * (-1 if seed % 2 else 1)
        obst = [("e", cx, cy, rx + 10, ry + 10), ("c", ex, cy, er + 8)]
        border, bw = kk_border(poly)
        for q in _kk_along(poly, 3.):
            obst.append(("c", q[0], q[1], 3.))
        run_field((m, m, w - 2 * m, h - 2 * m), obst,
                  [(cx - rx * .55, cy + ry + 8, 160), (cx + rx * .55, cy + ry + 8, 20), (cx, cy - ry - 9, 0 if seed % 2 else 180)],
                  max(6, h * .045), max(13, h * .14), kk_inside(poly), poly, 3,
                  area=(w - 2 * m) * (h - 2 * m) - 2 * c * c - _PI * (rx + 10) * (ry + 10) - _PI * (er + 8) ** 2)
        o.append(border)
        for p in (poly[0], poly[2], poly[4], poly[6]):
            pass
        for (qx, qy) in ((m * .6 + c * .3, m * .6 + c * .3), (w - m * .6 - c * .3, m * .6 + c * .3),
                         (w - m * .6 - c * .3, h - m * .6 - c * .3), (m * .6 + c * .3, h - m * .6 - c * .3)):
            o.append(kk_rosette(qx, qy, 3.6))
        o.append(f'<path d="{_kk_ell_d(cx, cy, rx + 1, ry + 1)}" fill="#fff" stroke="none"/>')
        o.append(kk_clip(_C._uid("kks", w, h, seed), _kk_ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "medium")))
        ring, _, _ = kk_ring(cx, cy, rx, ry, 1.5)
        o.append(ring)
        rr, _ = kk_roundel(ex, cy, er, egg, 1.)
        o.append(rr)
        return finish()

    # tall
    m = 10.
    fh = min(max(h * .12, 34), 60)
    yb = h - fh - 12
    rise = min(70., (yb - m) * .16)
    poly = kk_shape("arch", m, m, w - 2 * m, yb - m, rise)
    outer = kk_inside(kk_offset(poly, 9.))
    run_field((0, 0, w, yb + 6), [], [(0, 0, 45), (w, 0, 135)], 10., 22.,
              lambda px, py: not outer(px, py) and py < m + rise + 4, sd=4, cut=kk_offset(poly, 4.))
    border, bw = kk_border(poly)
    cx = w / 2
    ph = yb - m
    rr_ = min(24., ph * .07)
    ry = min(ph * .4, 175, (ph - rise * .5 - 18 - 2 * rr_ - 44) / 2)
    rx = min((w - 2 * m) * .4, ry * 1.45)
    cy = m + rise * .5 + ry + 18
    ey = min(cy + ry + 14 + rr_ + 6, yb - rr_ - 10)
    obst = [("e", cx, cy, rx + 10, ry + 10), ("c", cx, ey, rr_ + 10)]
    for q in _kk_along(poly, 3.):
        obst.append(("c", q[0], q[1], 3.))
    roots = [(cx - rr_ - 10, ey, 180), (cx + rr_ + 10, ey, 0), (cx, cy - ry - 10, 0 if seed % 2 else 180)]
    run_field((m, m, w - 2 * m, ph), obst, roots, max(9, h * .019), max(19, h * .048), kk_inside(poly), poly, 5,
              area=(w - 2 * m) * ph - _PI * (rx + 10) * (ry + 10) - _PI * (rr_ + 10) ** 2 - .43 * rise * (w - 2 * m))
    o.append(border)
    o.append(f'<path d="{_kk_ell_d(cx, cy, rx + 1, ry + 1)}" fill="#fff" stroke="none"/>')
    o.append(kk_clip(_C._uid("kks", w, h, seed), _kk_ell_d(cx, cy, rx, ry), scene(cx - rx, cy - ry, 2 * rx, 2 * ry, "tall")))
    ring, _, _ = kk_ring(cx, cy, rx, ry, 1.5)
    o.append(ring)
    rr, _ = kk_roundel(cx, ey, rr_, "arms" if arms else egg, 1.2)
    o.append(rr)
    # the frieze
    fy = yb + 8
    fp = kk_shape("rect", m + 6, fy + 4, w - 2 * m - 12, h - fy - 8)
    fb, _ = kk_border(fp, 1.2)
    pr = (h - fy - 8) / 2 - 1
    pcx, pcy = w / 2, fy + 4 + (h - fy - 8) / 2
    o.append(kk_matte(kk_rect_d(0, yb + 4, w, h - yb - 4)))
    run_field((m + 6, fy + 4, w - 2 * m - 12, h - fy - 8), [("c", pcx, pcy, pr * 1.05)] + ([("c", w * .2, pcy, pr * .8)] if egg2 else []),
              [(pcx - pr, pcy, 180), (pcx + pr, pcy, 0)], max(5.5, pr * .42), pr * 1.05, sd=7)
    o.append(fb)
    o.append(kk_egg(egg2 or "fleur", pcx, pcy, pr * .95))
    return finish()


# ---- the plate ------------------------------------------------------------------------------

def plate(w, h, ctx):
    """Where the jazz is: the tenor under the spotlight before the curtain (the B3 organ on tall
    plates), in the inlaid medallion; crossed drumsticks and a ride cymbal behind the sax and a
    swing-note roundel in the scroll (the Easter eggs)."""
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)

    def sc(x, y, ww, hh, mode):
        X, Y, W, H = x - 2, y - 2, ww + 4, hh + 4
        return _clipped("mu%d" % int(hh * 10), kk_rect_d(X, Y, W, H), scene(X, Y, W, H, seed, mode == "tall"))
    return kk_plate(w, h, sc, egg="note", seed=seed)
