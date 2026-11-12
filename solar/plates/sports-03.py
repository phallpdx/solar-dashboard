"""sports-03 - Portland State Vikings (Big Sky). Last game L 60-79 at Seattle U; tonight at
Colorado State Rams. The plate is the matchup: a bearded Viking (left) and a Colorado ram (right)
grow out of the acanthus and face each other across a cartouche in which a basketball drops
toward the hoop over a hardwood floor. Both horns are the volutes. Easter egg: a pair of crossed
drumsticks lies on the court by the baseline (and a tiny 'P' rivet on the Viking's helmet band)."""
import sys
import math
import random
import engraving_codex as C

PI = math.pi
_n = C._n


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def _cr(ctrl, k=8, closed=False):
    """Catmull-Rom through control points -> dense polyline."""
    P = list(ctrl)
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(P[-2])
    return out


def _xf(pts, x, y, s, f):
    return [(x + f * u * s, y + v * s) for u, v in pts]


def _ell(cx, cy, rx, ry, n=40, a0=0., a1=2 * PI):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def _ribbon(pts, w0, w1, pw=1.):
    """A tapering ribbon along pts -> _Rib (half widths w0 at start to w1 at end)."""
    n = len(pts)
    W = [w0 + (w1 - w0) * (i / (n - 1)) ** pw for i in range(n)]
    return C._Rib(pts, W, W)


def _horn(cv, pts, w0, w1, ridge=3.2, dark_side=1):
    """An annulated horn along pts: outline, transverse growth ridges, form lines, an under-shadow."""
    R = _ribbon(pts, w0, w1, .9)
    cv.obj([R.outline()], 1.)
    L = R.L
    u = .02
    k = 0
    while u < .97:
        w = R.width(u, 1)
        if w > 1.6:
            q = [R.at(u + .006 * math.sin(k), s) for s in (-.98, -.5, 0, .5, .98)]
            q = [(q[i][0] + (.5 if i == 2 else 0) * w * .06, q[i][1]) for i in range(5)]
            (cv.line if k % 3 == 0 else cv.hair)(q)
        step = max(1.6, ridge * (w / max(w0, 1)) ** .6)
        u += step / L
        k += 1
    cv.hair(C._fill_lines(R, .15 * dark_side, .98 * dark_side, 2., .02, .97, 3))
    C._shadow(cv, R, dark_side, min(3., w0 * .35), .03, .9)
    return R


def _strands(cv, A, B, n, wig=1.2, ph=0., heavy_every=0):
    """n wavy bulino strands running between two edge curves A and B (same length)."""
    m = len(A)
    for k in range(1, n):
        f = k / n
        pl = []
        for i in range(m):
            t = i / (m - 1)
            x = A[i][0] + (B[i][0] - A[i][0]) * f
            y = A[i][1] + (B[i][1] - A[i][1]) * f
            dx, dy = B[i][0] - A[i][0], B[i][1] - A[i][1]
            d = math.hypot(dx, dy) or 1
            o = wig * math.sin(t * 9 + k * 1.7 + ph) * math.sin(PI * t)
            pl.append((x + dx / d * o, y + dy / d * o))
        (cv.line if heavy_every and k % heavy_every == 0 else cv.hair)(pl)


# ----------------------------------------------------------------------------------------------
# the Viking: bearded head in a horned helmet, the horn rolling into a volute
# ----------------------------------------------------------------------------------------------

def viking_head(cv, x, y, s, f=1):
    """Head centred near (x, y), about 1.3*s tall, looking toward +x when f=1, -x when f=-1."""
    T = lambda pts: _xf(pts, x, y, s, f)
    # long hair falling behind
    hairA = T(_cr([(-.20, -.05), (-.34, .12), (-.40, .34), (-.36, .56), (-.44, .72)], 5))
    hairB = T(_cr([(.02, .05), (-.08, .22), (-.12, .40), (-.16, .56), (-.26, .70)], 5))
    cv.obj([hairA + hairB[::-1]], 1.)
    _strands(cv, hairA, hairB, 9, 1.4, 1.1, 3)
    # face
    face = T(_cr([(-.26, -.04), (.40, -.06), (.47, .00), (.44, .07), (.49, .15), (.56, .25),
                  (.50, .29), (.44, .30), (.30, .40), (.02, .40), (-.20, .24)], 4, True))
    cv.obj([face], 1.)
    cheek = T(_cr([(-.24, .00), (.20, .02), (.27, .14), (.20, .28), (-.02, .38), (-.20, .22)], 4, True))
    cv.hair(C.hatch_poly(cheek, 75 * f, 2, 1.1))

    sock = T(_cr([(.28, .03), (.42, .02), (.44, .08), (.34, .11), (.27, .08)], 4, True))
    cv.obj([sock], 0)
    cv.line(C.hatch_poly(sock, 0, 1, .2))
    eye = T(_cr([(.31, .07), (.36, .055), (.41, .07), (.36, .085)], 4, True))
    cv.obj([eye], .5)
    cv.heavy([T([(.355, .062)])[0], T([(.37, .075)])[0]])
    cv.heavy(T(_cr([(.26, .035), (.34, .02), (.45, .04)], 4)))          # brow
    cv.line(T(_cr([(.46, .10), (.50, .17), (.55, .245)], 4)))            # nose ridge
    cv.line(T(_cr([(.50, .265), (.47, .245), (.45, .26)], 3)))           # nostril
    cv.hair(T(_cr([(.30, .14), (.38, .20), (.41, .27)], 4)))             # cheek line
    ear = T(_cr([(.02, .10), (.07, .07), (.10, .13), (.07, .21), (.03, .22)], 4))
    cv.line(ear)
    # beard: flowing, the strands are its modelling
    bA = T(_cr([(.48, .30), (.54, .40), (.50, .54), (.40, .70), (.24, .86), (.14, .94)], 6))
    bB = T(_cr([(.04, .22), (.00, .38), (.02, .52), (.06, .66), (.08, .80), (.14, .94)], 6))
    cv.obj([bA + bB[::-1]], 1.)
    _strands(cv, bA, bB, 13, 1.8, 0., 4)
    cv.line(C.hatch_poly(T(_cr([(.06, .30), (.18, .44), (.10, .70), (.04, .50)], 4, True)), 80, 2., .3))
    for (u, v, a, ln, cu) in ((.14, .92, 110, .34, 4.6), (.30, .80, 70, .26, -4.2)):
        p0 = T([(u, v)])[0]
        aa = math.degrees(math.atan2(math.sin(math.radians(a)), f * math.cos(math.radians(a))))
        C._finger(cv, p0[0], p0[1], math.radians(aa), s * ln, s * ln * .14, .6 * (1 if cu > 0 else -1) * f, cu * f)
    # moustache sweeping back over the beard
    for side, tip in ((1, (.30, .44)), (-1, (.10, .36))):
        mA = T(_cr([(.46, .29), (.40, .34), (.32, .38), tip], 4))
        mB = T(_cr([(.47, .31), (.42, .38), (.34, .43), tip], 4))
        if side < 0:
            mA = T(_cr([(.44, .29), (.30, .31), (.18, .30), tip], 4))
            mB = T(_cr([(.45, .31), (.32, .35), (.20, .36), tip], 4))
        cv.obj([mA + mB[::-1]], 1.)
        _strands(cv, mA, mB, 4, .5, 2.)
    # helmet: a ruled steel dome, banded and riveted, a nasal guard
    dome = T(_ell(.08, -.06, .42, .44, 40, PI, 2 * PI))
    cv.obj([dome], 1.)
    for k in range(1, 9):
        rx = .42 * (1 - k / 9.)
        arc = T(_ell(.08 + .10 * k / 9, -.06, rx, .44, 24, PI, 2 * PI))
        (cv.line if k in (3, 6) else cv.hair)(arc)
    shade = T(_ell(.08, -.06, .42, .44, 30, PI, 1.45 * PI) + [(.08, -.06)])
    cv.hair(C.hatch_poly(shade, 25 * f, 2, .3))
    band = T([(-.36, -.10), (.52, -.10), (.52, -.02), (-.36, -.02)])
    cv.obj([band], 1.)
    cv.hair(C.hatch_poly(band, 0, 1.5, .4))
    for k in range(7):
        u = -.30 + k * .13
        c = T([(u, -.06)])[0]
        cv.obj([_ell(c[0], c[1], s * .022, s * .022, 10)], 1.)
    nasal = T([(.40, -.11), (.47, -.11), (.50, .12), (.45, .13)])
    cv.obj([nasal], 1.)
    cv.hair(C.hatch_poly(nasal, 90, 1.5, .3))
    # the horn: springs from the helmet side, sweeps back and up, the tip rolling into a small volute
    Lh = .62
    pts = C._euler(-.16, -.30, math.radians(-160), Lh,
                   lambda u: (1.5 + 9. * C._smooth(.55, 1., u) ** 2) / Lh, 60)
    pts = T(pts)
    _horn(cv, pts, s * .095, s * .012, 3.0, 1)


# ----------------------------------------------------------------------------------------------
# the Ram (Colorado State, tonight): long head, curled annulated horn round the ear
# ----------------------------------------------------------------------------------------------

def ram_head(cv, x, y, s, f=1):
    T = lambda pts: _xf(pts, x, y, s, f)
    # neck wool
    nA = T(_cr([(-.24, .02), (-.36, .30), (-.36, .56), (-.48, .90)], 5))
    nB = T(_cr([(.12, .38), (.04, .50), (-.04, .66), (-.02, .90)], 5))
    neck = nA + nB[::-1]
    cv.obj([neck], 1.)
    _wool(cv, neck, s)
    head = T(_cr([(-.10, -.32), (.14, -.30), (.30, -.18), (.48, .04), (.60, .24), (.66, .36),
                  (.62, .44), (.54, .48), (.44, .46), (.30, .42), (.12, .40), (-.04, .30),
                  (-.20, .10)], 4, True))
    cv.obj([head], 1.)
    # modelling: lines running down the long face, denser on the jaw
    fA = T(_cr([(.06, -.28), (.28, -.10), (.46, .10), (.58, .28), (.63, .37)], 6))
    fB = T(_cr([(-.10, .20), (.10, .34), (.28, .40), (.44, .45), (.56, .47)], 6))
    _strands(cv, fA, fB, 12, .25, 0.)
    jaw = T(_cr([(-.04, .26), (.20, .30), (.42, .38), (.52, .47), (.20, .41), (-.02, .32)], 4, True))
    cv.hair(C.hatch_poly(jaw, 35 * f, 2, .2))
    cv.line(T(_cr([(.56, .42), (.60, .45), (.64, .44)], 3)))            # mouth
    nos = T(_cr([(.57, .31), (.61, .29), (.63, .33), (.60, .35)], 4, True))
    cv.obj([nos], 1.)
    cv.line(C.hatch_poly(nos, 0, 1, .2))
    eye = T(_cr([(.20, -.06), (.27, -.09), (.32, -.05), (.26, -.02)], 4, True))
    cv.obj([eye], 1.)
    cv.line(C.hatch_poly(T(_cr([(.23, -.07), (.29, -.07), (.28, -.04), (.24, -.04)], 3, True)), 0, 1, .2))
    cv.heavy(T(_cr([(.16, -.10), (.26, -.13), (.36, -.07)], 4)))
    cv.hair(T(_cr([(.20, .00), (.30, .02), (.38, .08)], 4)))
    # the horn: big log spiral rolling back and down round the ear, the scroll of the plate
    hp = C.volute_spine(0, 0, 1, -48, 1.3, True, 0, 0, .14)
    sc = .48
    cx0, cy0 = -.15, .12
    pts = T([(cx0 + px * sc, cy0 + py * sc) for px, py in hp])
    _horn(cv, pts, s * .14, s * .022, 2.6, f)
    # a tuft of fleece over the horn's root on the poll
    rp = pts[0]
    tuft = _ell(rp[0] + f * s * .02, rp[1] + s * .02, s * .13, s * .08, 20)
    cv.obj([tuft], 1.)
    _wool(cv, tuft, s * .8)


def _wool(cv, poly, s):
    """Little tight curls packed into a region: the fleece."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    r = max(1.5, s * .022)
    step = r * 2.3
    j = 0
    y = min(ys) + r
    pl = []
    while y < max(ys):
        x = min(xs) + r + (j % 2) * step / 2
        while x < max(xs):
            if _inside(x, y, poly):
                a0 = (x * 1.3 + y) % 6.28
                pl.append(_ell(x, y, r, r * .85, 9, a0, a0 + 4.6))
            x += step
        y += step * .8
        j += 1
    cv.hair(pl)


def _inside(px, py, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


# ----------------------------------------------------------------------------------------------
# the vignette: the shot - a ball dropping toward the hoop over the hardwood
# ----------------------------------------------------------------------------------------------

def basketball(cv, cx, cy, r, rot=-.35):
    circ = _ell(cx, cy, r, r, 48)
    cv.obj([circ], 1.5)
    # shading: turned edge lower right, deep core shadow, highlight left
    cres = _ell(cx, cy, r, r, 30, -.35, PI * .95)
    inner = _ell(cx + r * .30, cy + r * .28 - r * .02, r * .92, r * .92, 30, -.35, PI * .95)
    def lune(off, k):
        a = _ell(cx, cy, r - .3, r - .3, 34, -.55 + .0, PI * 1.05)
        b = _ell(cx - r * off * .7, cy - r * off * .7, r * k, r * k, 34, -.55, PI * 1.05)
        return a + b[::-1]
    cv.hair(C.hatch_poly(lune(.42, 1.02), -35, 3, .4))
    cv.hair(C.hatch_poly(lune(.25, 1.0), 55, 2, .9))
    cv.line(C.hatch_poly(lune(.10, 1.0), -35, 2, 1.3))
    # pebble: stipple ticks over the body
    rng = random.Random(int(cx * 7 + cy))
    tk = []
    for _ in range(int(r * r * .5)):
        a = rng.uniform(0, 2 * PI)
        d = r * math.sqrt(rng.random()) * .92
        px, py = cx + d * math.cos(a), cy + d * math.sin(a)
        tk.append([(px, py), (px + .5, py + .3)])
    cv.hair(tk)
    # seams: great circles seen at an angle
    ca, sa = math.cos(rot), math.sin(rot)
    def R(u, v):
        return (cx + u * ca - v * sa, cy + u * sa + v * ca)
    seams = []
    seams.append([R(r * .98 * math.cos(t), r * .14 * math.sin(t)) for t in [PI * i / 30 for i in range(31)]])
    seams.append([R(r * .30 * math.sin(t), r * .98 * math.cos(t)) for t in [PI * i / 30 for i in range(31)]])
    for sd in (-1, 1):
        seams.append([R(sd * (r * .55 - r * .55 * math.sin(t) * .55) + sd * r * .1, r * .84 * math.cos(t))
                      for t in [PI * i / 30 for i in range(31)]])
    for pl in seams:
        cv.heavy(pl)


def drumsticks(cv, cx, cy, L):
    """The Easter egg: two drumsticks crossed, tips up."""
    for sd in (-1, 1):
        a = -PI / 2 + sd * .55
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        x0, y0 = cx - ux * L * .5, cy - uy * L * .5
        w0, w1 = L * .045, L * .02
        body = [(x0 + vx * w0, y0 + vy * w0), (x0 + ux * L * .85 + vx * w1, y0 + uy * L * .85 + vy * w1),
                (x0 + ux * L * .85 - vx * w1, y0 + uy * L * .85 - vy * w1), (x0 - vx * w0, y0 - vy * w0)]
        cv.obj([body], 1.)
        cv.hair(C.hatch_poly(body, math.degrees(a), 1.5, .2) [:1])
        tx, ty = x0 + ux * L * .92, y0 + uy * L * .92
        cv.obj([_ell(tx, ty, L * .045, L * .06, 10)], 1.)


def court_scene(fx, fy, fw, fh, seed=0, egg=True):
    """The shot, filling the box (fx, fy, fw, fh) with no blank ground. Returns a Canvas."""
    cv = C.Canvas()
    cx = fx + fw / 2
    floor = fy + fh * .70
    # arena: ruled dark wall, deepening toward the top corners; lamp beams down onto the court
    wall = [(fx - 2, fy - 2), (fx + fw + 2, fy - 2), (fx + fw + 2, floor), (fx - 2, floor)]
    cv.obj([wall], 0)
    cv.hair(C.hatch_poly(wall, 0, 2, .5))
    upper = [(fx - 2, fy - 2), (fx + fw + 2, fy - 2), (fx + fw + 2, fy + fh * .22), (cx, fy + fh * .34),
             (fx - 2, fy + fh * .22)]
    cv.hair(C.hatch_poly(upper, 60, 3, .3))
    cv.hair(C.hatch_poly(upper, -60, 3, 1.3))
    # crowd tiers: rows of heads as small arcs along the wall
    rows = []
    for j in range(3):
        yy = fy + fh * (.40 + j * .09)
        r = 1.4 + j * .35
        x = fx + (j % 2) * r * 1.4
        while x < fx + fw:
            rows.append(_ell(x, yy, r, r * 1.1, 8, PI, 2 * PI))
            x += r * 2.8
    cv.line(rows)
    rail = [(fx - 2, floor - fh * .05), (fx + fw + 2, floor - fh * .05), (fx + fw + 2, floor), (fx - 2, floor)]
    cv.obj([rail], 1.)
    cv.hair(C.hatch_poly(rail, 90, 2, .5))
    # hardwood floor in perspective: boards converging, grain, a white key
    fl = [(fx - 2, floor), (fx + fw + 2, floor), (fx + fw + 2, fy + fh + 2), (fx - 2, fy + fh + 2)]
    cv.obj([fl], 1.)
    vx, vy = cx + fw * .10, floor - fh * 1.4
    boards = []
    for k in range(-30, 31):
        bx = cx + k * 7.
        t0 = 0.
        a = (vx + (bx - vx) * ((floor - vy) / (fy + fh + 2 - vy)), floor)
        boards.append([a, (bx, fy + fh + 2)])
    cv.hair(boards)
    rng = random.Random(seed)
    grain = []
    y = floor + 2.
    while y < fy + fh + 2:
        x = fx + rng.uniform(0, 9)
        while x < fx + fw:
            ln = rng.uniform(4, 11)
            grain.append([(x, y), (x + ln, y)])
            x += ln + rng.uniform(3, 9)
        y += 2.
    cv.hair(grain)
    # the key: lane and arc, white lines on the wood
    hx = cx + fw * .17
    key = [(hx - fw * .14, floor + 1), (hx + fw * .14, floor + 1), (hx + fw * .22, fy + fh + 3), (hx - fw * .22, fy + fh + 3)]
    keyin = [(hx - fw * .14 + 2.5, floor + 1), (hx + fw * .14 - 2.5, floor + 1), (hx + fw * .22 - 3, fy + fh + 3),
             (hx - fw * .22 + 3, fy + fh + 3)]
    cv.obj([key], 1.)
    cv.obj([keyin], 1.)
    cv.hair(C.hatch_poly(keyin, 0, 2, .5))
    cv.hair(C.hatch_poly(keyin, 90, 3, .5))
    # ball shadow on the floor
    bsr = fh * .12
    bx, by = cx - fw * .07, fy + fh * .33
    sh = _ell(bx + fw * .02, floor + fh * .12, bsr * 1.1, bsr * .25, 20)
    cv.obj([sh], 0)
    cv.line(C.hatch_poly(sh, 0, 2, .2))
    cv.hair(C.hatch_poly(sh, 0, 2, 1.2))
    if egg:
        drumsticks(cv, fx + fw * .20, floor + fh * .16, fh * .24)
    # the stanchion and backboard (right)
    bbx, bby = hx, fy + fh * .22
    bw, bh = fw * .30, fh * .28
    post = [(fx + fw - fw * .07, bby + bh * .2), (fx + fw + 2, bby + bh * .2), (fx + fw + 2, fy + fh + 2), (fx + fw - fw * .07, fy + fh + 2)]
    cv.obj([post], 1.)
    cv.hair(C.hatch_poly(post, 90, 1.5, .3))
    cv.hair(C.hatch_poly(post, 30, 3, .3))
    arm_y = bby + bh * .45
    arm = [(bbx + bw / 2 - 2, arm_y - 3), (fx + fw - fw * .06, arm_y - 3), (fx + fw - fw * .06, arm_y + 3), (bbx + bw / 2 - 2, arm_y + 3)]
    cv.obj([arm], 1.)
    cv.hair(C.hatch_poly(arm, 0, 1.5, .4))
    brace = []
    xx = bbx + bw / 2
    while xx < fx + fw - fw * .07:
        brace.append([(xx, arm_y + 3), (xx + 4, arm_y + 10), (xx + 8, arm_y + 3)])
        xx += 8
    cv.line(brace)
    # board thickness (dark), then the glass face, then the target square
    side = [(bbx - bw / 2, bby), (bbx + bw / 2, bby), (bbx + bw / 2 + 3, bby + 3), (bbx + bw / 2 + 3, bby + bh + 3),
            (bbx - bw / 2 + 3, bby + bh + 3), (bbx - bw / 2, bby + bh)]
    cv.obj([side], 1.)
    cv.line(C.hatch_poly(side, 45, 1, .2))
    face = [(bbx - bw / 2, bby), (bbx + bw / 2, bby), (bbx + bw / 2, bby + bh), (bbx - bw / 2, bby + bh)]
    cv.obj([face], 1.5)
    cv.hair(C.hatch_poly(face, -62, 3, .4))
    gl = [(bbx - bw / 2 + 2.5, bby + 2.5), (bbx - bw / 2 + bw * .45, bby + 2.5), (bbx - bw / 2 + 2.5, bby + bh * .75)]
    cv.obj([gl], 0)               # a glint where the glass catches the light
    cv.obj([], 0)
    sq = [(bbx - bw * .17, bby + bh * .42), (bbx + bw * .17, bby + bh * .42), (bbx + bw * .17, bby + bh * .92), (bbx - bw * .17, bby + bh * .92)]
    cv.heavy([sq[0], sq[1], sq[2], sq[3], sq[0]])
    # the rim and net
    rx, ry = bw * .26, bw * .07
    rcx, rcy = bbx, bby + bh * .92 + ry + 2
    cv.obj([[(rcx - 3, bby + bh * .9), (rcx + 3, bby + bh * .9), (rcx + 3, rcy), (rcx - 3, rcy)]], 1.)
    nd = fh * .20
    top = _ell(rcx, rcy, rx, ry, 16)
    bot = _ell(rcx, rcy + nd, rx * .55, ry * .55, 16)
    mid = _ell(rcx, rcy + nd * .5, rx * .78, ry * .78, 16)
    net = []
    for i in range(16):
        net.append([top[i], mid[(i + 1) % 16], bot[i]])
        net.append([top[(i + 1) % 16], mid[i], bot[(i + 1) % 16]])
    netpoly = top[8:] + [top[0]] + bot[:9][::-1]
    cv.obj([_ell(rcx, rcy + nd * .5, rx * 1.0, nd * .55, 24)], 0)
    cv.hair(C.hatch_poly(_ell(rcx, rcy + nd * .5, rx * .9, nd * .5, 24), 0, 2, 1))
    cv.line(net)
    cv.line([bot[i] for i in range(16)] + [bot[0]])
    ring = _ell(rcx, rcy, rx + 1.2, ry + 1.2, 32)
    ringin = _ell(rcx, rcy, rx - .8, ry - .8, 32)
    cv.obj([ring], 0)
    cv.heavy(ring + [ring[0]])
    cv.heavy(ringin + [ringin[0]])
    # the shot's arc: a dotted trajectory from the left, the ball at its apex
    arc = []
    for i in range(14):
        t = i / 13.
        px = fx + fw * .02 + (bx - fx - fw * .02 - bsr * 1.2) * t
        py = floor - fh * .05 - (floor - fh * .05 - by - bsr * .3) * math.sin(t * PI / 2)
        arc.append(_ell(px, py, .9 + t * .7, .9 + t * .7, 8))
    cv.obj(arc, 1.)
    # speed lines behind the ball
    for k in (-1, 0, 1):
        cv.obj([], 0)
        cv.line([(bx - bsr * 1.15, by + k * bsr * .45), (bx - bsr * 1.9, by + k * bsr * .45 + bsr * .25)])
    basketball(cv, bx, by, bsr)
    return cv


# ----------------------------------------------------------------------------------------------
# lettering drawn as strokes (no <text>): a plain engraver's block capital on a 4 x 6 grid
# ----------------------------------------------------------------------------------------------

_FONT = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.9), (3.2, 3.9)]],
    "D": [[(0, 0), (0, 6), (2.2, 6), (4, 4.4), (4, 1.6), (2.2, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.2), (2.2, 3.2)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.8)], [(1.4, 2.6), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (2.8, 0), (3.7, .9), (3.7, 2.1), (2.8, 3)]],
    "*": [[(2, 2.2), (2, 3.8)], [(1.2, 3), (2.8, 3)]],
}


def letter_line(text, cx, cy, size, track=1.6):
    """Polylines for text centred at (cx, cy), cap height `size`."""
    k = size / 6.
    adv = (4 + track) * k
    total = len(text) * adv - track * k
    x0 = cx - total / 2
    out = []
    for i, ch in enumerate(text):
        for pl in _FONT.get(ch, []):
            out.append([(x0 + i * adv + u * k, cy - size / 2 + v * k) for u, v in pl])
    return out


def letter_curve(text, centre, size, track=1.8):
    """Letters set along a centre curve (the ribbon's face), each turned to the local tangent."""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    k = size / 6.
    adv = (4 + track) * k
    total = len(text) * adv - track * k
    s0 = L[-1] / 2 - total / 2

    def at(d):
        for i in range(1, len(L)):
            if L[i] >= d:
                t = (d - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
                p, q = centre[i - 1], centre[i]
                return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t), math.atan2(q[1] - p[1], q[0] - p[0])
        return centre[-1], 0.
    out = []
    for i, ch in enumerate(text):
        (px, py), a = at(s0 + i * adv + 2 * k)
        ca, sa = math.cos(a), math.sin(a)
        for pl in _FONT.get(ch, []):
            out.append([(px + (u - 2) * k * ca - (v - 3) * k * sa, py + (u - 2) * k * sa + (v - 3) * k * ca)
                        for u, v in pl])
    return out


# ----------------------------------------------------------------------------------------------
# layouts
# ----------------------------------------------------------------------------------------------

def _clip_d(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _field(cx, cy, cw, ch, ix, iy, iw, ih):
    """The cartouche's white field's bbox, from the inner rect cartouche() returned."""
    k = 2 ** (-1 / 2.6)
    a, b = iw / 2 / k + 6, ih / 2 / k + 6
    return cx - a, cy - b, 2 * a, 2 * b


def _band(w, h, seed):
    """Short: bead moulding, ground, a scroll frieze round a medallion with the ball in it,
    the Viking horn and ram horn flanking the medallion."""
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("s3b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    cv = C.Canvas()
    ell = _ell(cx, cy, rx - 3.5, ry - 3.5, 48)
    cv.obj([ell], 0)
    cv.hair(C.hatch_poly(ell, 0, 2, .5))
    cv.hair(C.hatch_poly(_ell(cx, cy, rx - 3.5, ry - 3.5, 30, PI, 2 * PI), 45, 3, .5))
    # tiny crossed drumsticks behind the ball - the egg
    drumsticks(cv, cx + rx * .48, cy + ry * .05, ry * 1.1)
    basketball(cv, cx - rx * .18, cy, ry * .62)
    o.append(_clip_d(C._uid("s3m", w, h), C._d(_ell(cx, cy, rx - 2.5, ry - 2.5, 64), True), cv.svg()))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
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
    cw = min(w * .40, gh * 1.45)
    cx, cy = w / 2, (gy0 + gy1) / 2
    s = min(gh * .66, 104.)
    hx = cw / 2 + s * .58
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1),
           ("c", cx - hx + s * .05, cy - s * .05, s * .52),
           ("c", cx + hx - s * .05, cy - s * .02, s * .52)]
    cv = C.Canvas()
    main = C.Canvas()
    xo = cx - hx - s * .5          # outer free span each side
    r = min(gh * .42, xo * .55)
    if r > 12:
        for side in (-1, 1):
            vx = cx + side * (hx + s * .5 + r * .9)
            vy = gy0 + gh * .5
            C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, side < 0)
            occ.append(("c", vx, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(7, gh * .055), rmax=r * .8 if r > 12 else gh * .3,
                   max_n=18, edge=.7, cv=cv)
    cv.extend(main)
    # fronds springing from behind each head, so the figures grow out of the leafwork
    leaf = C.Canvas()
    for side in (-1, 1):
        bx = cx + side * hx
        C.acanthus_frond(bx - side * s * .2, gy1 - 2, -90 - side * 35, s * .55, 3, 26, .9 * side, 4.5 * side,
                         seed + side, cv=leaf)
        C.acanthus_frond(bx - side * s * .1, gy0 + 4, 90 + side * 40, s * .42, 2, 30, -.9 * side, -4.5 * side,
                         seed + 5 + side, cv=leaf)
    cv.extend(leaf)
    figs = C.Canvas()
    viking_head(figs, cx - hx, cy - s * .12, s * .82, 1)
    ram_head(figs, cx + hx, cy - s * .06, s * .80, -1)
    cv.extend(figs)
    o.append(C._clip(C._uid("s3m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, cw, gh + 4, ix, iy, iw, ih)
    o.append(_clip_d(C._uid("s3f", w, h), field, court_scene(fx, fy, fw, fh, seed).svg()))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed):
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
    cw, ch = pw * .44, ph * .62
    cx, cy = w / 2, py0 + ph * .45
    s = min((pw - cw) / 2 * .62, ph * .34)
    hx = cw / 2 + s * .5
    hy = cy + ch * .02
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6),
           ("r", cx - hx - s * .5, hy - s * .55, cx - hx + s * .55, hy + s * .95),
           ("r", cx + hx - s * .55, hy - s * .55, cx + hx + s * .5, hy + s * .95)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .15, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .7)
        vy = py0 + ph - r1 * 1.0
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .17)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .7)
        vy = py0 + r2 * 1.0
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(9, ph * .035), rmax=r1 * .9,
                   max_n=16, edge=.6, cv=cv)
    cv.extend(main)
    leaf = C.Canvas()
    for side in (-1, 1):
        bx = cx + side * hx
        C.acanthus_frond(bx - side * s * .15, hy + s * .95, -90 - side * 30, s * .6, 3, 26, .9 * side, 4.5 * side,
                         seed + side, cv=leaf)
    cv.extend(leaf)
    figs = C.Canvas()
    viking_head(figs, cx - hx, hy - s * .1, s, 1)
    ram_head(figs, cx + hx, hy - s * .02, s * .96, -1)
    cv.extend(figs)
    o.append(C._clip(C._uid("s3t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, cw, ch, ix, iy, iw, ih)
    o.append(_clip_d(C._uid("s3tf", w, h), field, court_scene(fx, fy, fw, fh, seed).svg()))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lc = C.Canvas()
    lc.obj([], 0)
    R = C._Rib(centre, [bh / 2] * len(centre), [bh / 2] * len(centre))
    for sv in (-.55, -.3, -.05, .2, .45):
        lc.hair(R.contour(sv, .02, .98))
    lc.obj([], 0)
    lc.heavy(letter_curve("VIKINGS", [(a, b + .8) for a, b in centre], bh * .56, 2.2))
    o.append(lc.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    tc = C.Canvas()
    tab = [(tx + 2.5, ty + 2.5), (tx + tw - 1, ty + 2.5), (tx + tw - 1, ty + th - 1), (tx + 2.5, ty + th - 1)]
    tc.obj([tab], 0)
    tc.hair(C.hatch_poly(tab, 0, 2, .5))
    tc.obj([], 0)
    lh = min(th * .62, 11)
    tc.heavy(letter_line("PORTLAND STATE * BIG SKY", tx + tw / 2, ty + th / 2 + .6, lh, 1.8))
    o.append(tc.svg())
    fy2 = py + ped_h
    fh2 = h - fy2
    if fh2 > 14:
        o.append(C.dark_ground((w * .06, fy2, w * .88, fh2 - 2), "G"))
        o.append(C._clip(C._uid("s3fr", w, h, seed), w * .06, fy2, w * .88, fh2 - 2,
                         C.scroll_band(w * .06, fy2, w * .88, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy2 + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
