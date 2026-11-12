"""delights-09 "Today's long read": Walter Kirn, LOST IN THE MERITOCRACY (The Atlantic, 2005), the
brilliant student who games school without learning much.
The cartouche holds a Collegiate Gothic gate tower (Kirn's Princeton) at dusk, its clock at the
hour of the morning edition, and before it a clipped hedge maze in deep perspective, newly laid
out each day from the date: the student lost in the meritocracy. A dropped mortarboard lies on a
maze path. The ribbon is lettered LOST IN THE MERITOCRACY in drawn strokes, the pedestal tablet
THE ATLANTIC . MMV. Easter egg: the tower's shield over the gate carries a "P" -- Princeton's,
and Parker's."""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d = C._n, C._d
TAU = math.tau
H = C.hatch_poly


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .5 - 18.2 / 24
    return (days / 29.530588) % 1.


def _lancet(x, y0, w, h):
    """A pointed (lancet) window, bottom-left x, sill y0, w wide, h tall."""
    r = w * .8
    spring = y0 - h + w * .75
    pts = [(x, y0), (x, spring)]
    cx1, cx2 = x + r, x + w - r
    # left arc centred on (x + r, spring) up to the apex
    ax = x + w / 2
    a_end = math.acos((ax - cx1) / r) if abs((ax - cx1) / r) <= 1 else math.pi / 2
    for i in range(1, 7):
        a = math.pi - (math.pi - a_end) * i / 6
        pts.append((cx1 + r * math.cos(a), spring - r * math.sin(a)))
    for i in range(5, -1, -1):
        a = math.pi - (math.pi - a_end) * i / 6
        pts.append((cx2 - r * math.cos(a), spring - r * math.sin(a)))
    pts.append((x + w, y0))
    return pts


# ------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------

def _sky(cv, fx, fy, fw, hy, date, rng, stars=True):
    b1, b2 = fy + (hy - fy) * .34, fy + (hy - fy) * .7
    for y_a, y_b, p in ((fy - 2, b1, 1.5), (b1, b2, 2.), (b2, hy + 1, 3.)):
        r = _rect(fx - 2, y_a, fw + 4, y_b - y_a)
        cv.obj([r], 0)
        cv.hair(H(r, 0, p, .25))
    ph = _moon_phase(date)
    mr = max(3.5, (hy - fy) * .07)
    mx, my = fx + fw * .79, fy + (hy - fy) * .3
    disc = C._ell_pts(mx, my, mr, mr, 32)
    cv.obj([disc], .5)
    ts = [math.pi * i / 16 for i in range(17)]
    side = -1 if ph < .5 else 1
    dark = [(mx + side * mr * math.sin(t), my - mr * math.cos(t)) for t in ts] + \
           [(mx - side * mr * math.cos(TAU * ph) * math.sin(t), my - mr * math.cos(t)) for t in ts[::-1]]
    if abs(C._area(dark)) > 1:
        cv.obj([dark], 0)
        cv.hair(H(dark, 0, 1.5, .25))
    # a halo of short rays round the moon
    for k in range(4):
        ca = rng.uniform(0, TAU)
        cr_ = mr * rng.uniform(.12, .22)
        rr = mr * rng.uniform(.2, .6)
        cv.obj([C._ell_pts(mx + rr * math.cos(ca), my + rr * math.sin(ca), cr_, cr_, 10)], .5)
    for i in range(24):
        a = TAU * i / 24
        r0, r1 = mr * 1.35, mr * (1.7 if i % 2 else 2.1)
        w_ = .07
        cv.obj([[(mx + r0 * math.cos(a - w_), my + r0 * math.sin(a - w_)), (mx + r1 * math.cos(a), my + r1 * math.sin(a)),
                 (mx + r0 * math.cos(a + w_), my + r0 * math.sin(a + w_))]], 0)
    if stars:
        for _ in range(int(fw * (hy - fy) / 520)):
            sx, sy = fx + rng.uniform(.04, .96) * fw, fy + rng.uniform(.05, .55) * (hy - fy)
            if math.hypot(sx - mx, sy - my) < mr * 2.4:
                continue
            s = rng.uniform(.8, 1.6)
            cv.obj([[(sx, sy - s * 1.6), (sx + s * .45, sy), (sx, sy + s * 1.6), (sx - s * .45, sy)]], 0)
            cv.obj([[(sx - s * 1.6, sy), (sx, sy - s * .45), (sx + s * 1.6, sy), (sx, sy + s * .45)]], 0)


def _hall(cv, x0, x1, base, wall_h, roof_h, rng, flip, blacks, detail=1.):
    """A lower Collegiate Gothic wing: slate roof, gabled dormers, a row of lancets, ivy."""
    top = base - wall_h
    # roof (a long slope seen in front), slates ruled at 45 deg with coursing
    roof = [(x0, top), (x0 + roof_h * .6, top - roof_h), (x1 - roof_h * .6, top - roof_h), (x1, top)]
    cv.obj([roof], 1.)
    cv.hair(H(roof, 0, 2, .25))
    cv.hair(H(roof, 45 if flip else -45, 3, .5))
    # chimneys
    for t in (.22, .78):
        cx = x0 + (x1 - x0) * t
        ch = _rect(cx - 2.5, top - roof_h - 5, 5, 6)
        cv.obj([ch], .5)
        cv.hair(H(_rect(cx, top - roof_h - 5, 2.5, 6), 90, 1.5, .25))
        cv.obj([_rect(cx - 3.5, top - roof_h - 6.5, 7, 1.5)], .5)
    # wall in ashlar: horizontal coursing, staggered joints
    wall = _rect(x0, top, x1 - x0, wall_h)
    cv.obj([wall], 1.)
    cv.hair(H(wall, 0, 3, .25))
    y = top + 1.5
    k = 0
    while y < base - 1 and detail:
        off = 4 if k % 2 else 0
        cv.hair([[(xx, y), (xx, y + 3)] for xx in [x0 + off + 8 * i + .25 for i in range(int((x1 - x0) / 8) + 1)] if xx < x1])
        y += 3
        k += 1
    # dormers breaking the roof
    n = max(2, int((x1 - x0) / 34))
    for i in range(n):
        cx = x0 + (x1 - x0) * (i + .5) / n
        dw = min(12., (x1 - x0) / n * .45)
        dh = roof_h * .9
        g = [(cx - dw / 2, top), (cx - dw / 2, top - dh * .55), (cx, top - dh - 3), (cx + dw / 2, top - dh * .55), (cx + dw / 2, top)]
        cv.obj([g], 1.)
        cv.hair(H(g, 0, 3, .25))
        win = _lancet(cx - dw * .22, top - 1.5, dw * .44, dh * .6)
        blacks.append(win)
    # lancet windows in pairs
    m = max(3, int((x1 - x0) / 15))
    ww = min(5., (x1 - x0) / m * .3)
    for i in range(m):
        cx = x0 + (x1 - x0) * (i + .5) / m
        for dx in (-ww * .65, ww * .65):
            win = _lancet(cx + dx - ww / 2, base - wall_h * .22, ww, wall_h * .55)
            blacks.append(win)
        # a buttress between bays
        if i:
            bx = x0 + (x1 - x0) * i / m
            b = [(bx - 1.5, base), (bx - 1.5, top + wall_h * .25), (bx, top + wall_h * .12), (bx + 1.5, top + wall_h * .25), (bx + 1.5, base)]
            cv.obj([b], .5)
            cv.hair(H(b, 90, 1.5, .25))
    # ivy climbing from the foot of the wall
    ivy_pts = []
    for _ in range(int((x1 - x0) * wall_h / 160 * detail)):
        px = x0 + rng.random() * (x1 - x0)
        py = base - (rng.random() ** 1.8) * wall_h * .85
        ivy_pts.append((px, py))
    for px, py in ivy_pts:
        s = rng.uniform(1.2, 2.2)
        a = rng.uniform(0, TAU)
        leaf = [(px + s * math.cos(a + k * TAU / 3), py + s * math.sin(a + k * TAU / 3)) for k in range(3)]
        cv.obj([leaf], .5)
        cv.hair(H(leaf, 90, 1.5, .25))


def _tower(cv, cx, base, tw, top, rng, blacks, date, detail=1.):
    """The gate tower: buttressed, crenellated, corner pinnacles, belfry lancets, clock, a black
    pointed gate arch with the P shield above it."""
    th = base - top
    x0, x1 = cx - tw / 2, cx + tw / 2
    side_w = tw * .16
    # shadowed side face to the right (perspective)
    side = [(x1, top + 2), (x1 + side_w, top), (x1 + side_w, base - 1), (x1, base)]
    cv.obj([side], 1.)
    cv.hair(H(side, 90, 1.5, .25))
    cv.hair(H(side, 45, 3, .5))
    body = _rect(x0, top + 2, tw, th - 2)
    cv.obj([body], 1.)
    cv.hair(H(body, 0, 3, .25))
    y = top + 3.5
    k = 0
    while y < base - 1 and detail:
        off = 3.5 if k % 2 else 0
        cv.hair([[(xx, y), (xx, y + 3)] for xx in [x0 + off + 7 * i + .25 for i in range(int(tw / 7) + 1)] if x0 < xx < x1])
        y += 3
        k += 1
    # string courses
    for t in (.3, .58):
        yy = top + th * t
        sc = _rect(x0 - 1.5, yy, tw + 3 + side_w, 2.5)
        cv.obj([sc], .5)
        cv.hair(H(_rect(x0 - 1.5, yy + 1.5, tw + 3 + side_w, 1), 0, 1.5, .25))
    # crenellation + pinnacles
    mw = tw / 9
    cren = []
    for i in range(9):
        if i % 2 == 0:
            cren.append(_rect(x0 + i * mw, top - mw * 1.1, mw, mw * 1.1 + 2.5))
    for m in cren:
        cv.obj([m], 1.)
        cv.hair(H(_rect(m[0][0] + m[1][0] - m[0][0] - 1.5, m[0][1], 1.5, m[2][1] - m[0][1]), 90, 1.5, .25) if False else [])
    parapet = _rect(x0 - 2, top - 1, tw + 4 + side_w, 4)
    cv.obj([parapet], 1.)
    cv.hair(H(parapet, 0, 1.5, .25))
    for px in (x0 - 1, x1 + side_w * .5):
        pw = tw * .13
        shaft = _rect(px - pw / 2, top - th * .14, pw, th * .14 + 4)
        cv.obj([shaft], 1.)
        cv.hair(H(_rect(px, top - th * .14, pw / 2, th * .14 + 4), 90, 1.5, .25))
        spire = [(px - pw * .65, top - th * .14), (px, top - th * .14 - pw * 3.2), (px + pw * .65, top - th * .14)]
        cv.obj([spire], 1.)
        cv.hair(H([(px, top - th * .14 - pw * 3.2), (px + pw * .65, top - th * .14), (px, top - th * .14)], 90, 1.5, .25))
        # crockets up the spire
        for j in range(1, 4):
            t = j / 4.
            yy = top - th * .14 - pw * 3.2 * t
            xx = px + pw * .65 * (1 - t)
            cv.line([(xx, yy), (xx + 1.2, yy - 1)])
            cv.line([(2 * px - xx, yy), (2 * px - xx - 1.2, yy - 1)])
    # belfry: a pair of tall louvred lancets
    bw = tw * .17
    for dx in (-bw * .7, bw * .7):
        lw = _lancet(cx + dx - bw / 2, top + th * .28, bw, th * .22)
        blacks.append(lw)
    # clock under the belfry (hands at the hour of reading, about twenty past six)
    cr = min(tw * .2, th * .085)
    ccy = top + th * .42
    face = C._ell_pts(cx, ccy, cr, cr, 40)
    cv.obj([C._ell_pts(cx, ccy, cr + 1.5, cr + 1.5, 40)], 1.)
    cv.hair(H(C._ell_pts(cx, ccy, cr + 1.5, cr + 1.5, 40), 0, 1.5, .25))
    cv.obj([face], 1.)
    cv.hair(C._ell_pts(cx, ccy, cr * .62, cr * .62, 32) + [C._ell_pts(cx, ccy, cr * .62, cr * .62, 32)[0]])
    for i in range(12):
        a = TAU * i / 12
        r0 = cr * (.72 if i % 3 == 0 else .82)
        cv.line([(cx + r0 * math.cos(a), ccy + r0 * math.sin(a)), (cx + cr * .92 * math.cos(a), ccy + cr * .92 * math.sin(a))])
    try:
        dd = datetime.date.fromisoformat(date[:10])
        mins = 15 + dd.toordinal() % 15
    except Exception:
        mins = 20
    hrs = 6 + mins / 60
    ah = TAU * hrs / 12 - math.pi / 2
    am = TAU * mins / 60 - math.pi / 2
    cv.heavy([(cx, ccy), (cx + cr * .5 * math.cos(ah), ccy + cr * .5 * math.sin(ah))])
    cv.line([(cx, ccy), (cx + cr * .8 * math.cos(am), ccy + cr * .8 * math.sin(am))])
    cv.obj([C._ell_pts(cx, ccy, 1, 1, 8)], .5)
    # oriel windows on the shaft
    for dx in (-tw * .22, tw * .22):
        blacks.append(_lancet(cx + dx - 2.2, top + th * .74, 4.4, th * .1))
    # gate: a pointed arch, black, with voussoirs
    gw = tw * .46
    gh = th * .22
    gate = _lancet(cx - gw / 2, base, gw, gh)
    vou = _lancet(cx - gw / 2 - 2.5, base, gw + 5, gh + 3)
    cv.obj([vou], 1.)
    cv.hair(H(vou, 90, 1.5, .25))
    blacks.append(gate)
    # the P shield over the gate
    sw = min(tw * .3, max(7., (th * .78 - 3.5 - th * .42 - cr - 3) / 1.15))
    sh = sw * 1.15
    sy = base - gh - 3.5 - sh
    shield = [(cx - sw / 2, sy), (cx + sw / 2, sy), (cx + sw / 2, sy + sh * .55),
              (cx + sw * .3, sy + sh * .85), (cx, sy + sh), (cx - sw * .3, sy + sh * .85), (cx - sw / 2, sy + sh * .55)]
    cv.obj([[(p[0] + (p[0] - cx) * .25, p[1] + (p[1] - sy - sh / 2) * .2) for p in shield]], 1.)
    blacks.append(shield)
    pl = [(cx - sw * .12, sy + sh * .8), (cx - sw * .12, sy + sh * .17)]
    bowl = [(cx - sw * .12, sy + sh * .17)] + [(cx + sw * .02 + sw * .17 * math.sin(math.pi * i / 10),
                                                 sy + sh * .17 + sh * .15 - sh * .15 * math.cos(math.pi * i / 10)) for i in range(11)] + \
           [(cx - sw * .12, sy + sh * .47)]
    letter = C.Canvas()
    cv.obj([[(cx - sw * .3, sy + sh * .1), (cx + sw * .35, sy + sh * .1), (cx + sw * .35, sy + sh * .52),
             (cx - sw * .3, sy + sh * .52)]] if False else [], 0)
    return pl, bowl


def _maze(seed, C_, R_):
    """A perfect maze on C_ x R_ cells (recursive backtracker); returns the set of walls as
    ('h', i, j): wall on the near side of row j spanning col i; ('v', i, j): left of col i in row j."""
    rng = random.Random(seed)
    seen = [[False] * R_ for _ in range(C_)]
    hw = {(i, j) for i in range(C_) for j in range(R_ + 1)}
    vw = {(i, j) for i in range(C_ + 1) for j in range(R_)}
    st = [(C_ // 2, 0)]
    seen[C_ // 2][0] = True
    while st:
        i, j = st[-1]
        nb = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= i + di < C_ and 0 <= j + dj < R_ and not seen[i + di][j + dj]]
        if not nb:
            st.pop()
            continue
        a, b = rng.choice(nb)
        if a != i:
            vw.discard((max(a, i), j))
        else:
            hw.discard((i, max(b, j)))
        seen[a][b] = True
        st.append((a, b))
    # entrance nearest us in the middle, the exit at the far side towards the gate
    hw.discard((C_ // 2, 0))
    hw.discard((C_ // 2, R_))
    return hw, vw


def _hedges(cv, cx, hy, ynear, wn, zf, hh, cols, rows, seed, rng, extend=0):
    """The maze in perspective. World u across (0..1 = maze width wn at z=1), d in depth (0 near,
    1 far); z = 1 + d (zf - 1). Hedge boxes painted far to near."""
    def P(u, d, top=False):
        z = 1 + d * (zf - 1)
        y = hy + (ynear - hy - (hh if top else 0)) / z
        return (cx + (u - .5) * wn / z, y)

    hw, vw = _maze(seed, cols, rows)
    t = .16 / cols                 # hedge thickness in u
    td = .16 / rows * .55          # in depth
    boxes = []
    for (i, j) in hw:
        boxes.append((i / cols - t / 2, (i + 1) / cols + t / 2, j / rows - td, j / rows + td))
    for (i, j) in vw:
        boxes.append((i / cols - t / 2, i / cols + t / 2, j / rows, (j + 1) / rows))
    boxes.sort(key=lambda b: (-(b[2] + b[3]) / 2, -abs((b[0] + b[1]) / 2 - .5)))
    for u0, u1, d0, d1 in boxes:
        if d1 < -0.2:
            continue
        um = (u0 + u1) / 2
        z0 = 1 + max(d0, -.15) * (zf - 1)
        # side face toward the centre line
        su = u0 if um > .5 else u1
        if d1 - d0 > td * 2.5:
            side = [P(su, d0), P(su, d1), P(su, d1, True), P(su, d0, True)]
            cv.obj([side], .5)
            cv.hair(H(side, 90, 2, .25))
            # sprigs along its top edge
            a, b = P(su, d0, True), P(su, d1, True)
            n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2.5)
            cv.hair([[(a[0] + (b[0] - a[0]) * k / max(1, n), a[1] + (b[1] - a[1]) * k / max(1, n)),
                      (a[0] + (b[0] - a[0]) * k / max(1, n) + rng.uniform(-.8, .8), a[1] + (b[1] - a[1]) * k / max(1, n) + 2.2)]
                     for k in range(n)])
        front = [P(u0, d0), P(u1, d0), P(u1, d0, True), P(u0, d0, True)]
        top = [P(u0, d0, True), P(u1, d0, True), P(u1, d1, True), P(u0, d1, True)]
        cv.obj([top], .5)
        cv.hair(H(top, 0, 3, 1.25))
        # leafy texture on the clipped top: short ticks
        tx0, ty0 = top[0]
        tx1, ty1 = top[2]
        nn = int(abs((top[1][0] - top[0][0]) * (top[0][1] - top[3][1])) / 9)
        cv.hair([[(px, py), (px + 1.2, py - .8)] for px, py in
                 [(rng.uniform(min(p[0] for p in top), max(p[0] for p in top)),
                   rng.uniform(min(p[1] for p in top), max(p[1] for p in top))) for _ in range(nn)]])
        cv.obj([front], 1.)
        fh = front[0][1] - front[3][1]
        cv.hair(H(front, 90, 1.5, .25))
        if fh > 7:
            cv.hair(H(front, 45, 3, .5))
        # scalloped clipped edge
        a, b = front[3], front[2]
        n = int((b[0] - a[0]) / 2)
        if n > 1:
            sc = []
            for k in range(n + 1):
                x = a[0] + (b[0] - a[0]) * k / n
                sc.append((x, a[1] + (1.2 if k % 2 else 0)))
            cv.line(sc)
    return P


def _mortarboard(cv, x, y, s, rot=-.18):
    """A graduate's cap lying on the gravel: diamond board, skull cap, tassel."""
    c, sn = math.cos(rot), math.sin(rot)

    def T(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    cap = [T(-1.3, .1), T(-1.2, .9), T(1.2, .9), T(1.3, .1)]
    cv.obj([cap], 1.)
    cv.hair(H(cap, 90, 1.5, .25))
    board = [T(-2.2, 0), T(0, -.8), T(2.2, 0), T(0, .8)]
    cv.obj([board], 1.)
    cv.hair(H([T(0, .8), T(2.2, 0), T(-2.2, 0)], 0, 1.5, .25))
    cv.hair(H([T(-2.2, 0), T(0, -.8), T(2.2, 0)], 45, 3, .5))
    btn = C._ell_pts(*T(0, 0), .22 * s, .14 * s, 10)
    cv.obj([btn], .5)
    cord = [T(0, 0), T(.9, .25), T(1.9, .45)]
    cv.line(cord)
    tas = [T(1.8, .45), T(2.15, .45), T(2.35, 1.6), T(1.6, 1.6)]
    cv.obj([tas], .5)
    cv.hair(H(tas, 90, 1.5, .25))


def _book(cv, x, y, s):
    """An open book seen from the front and a little above: curved pages, ruled text lines,
    a dark gutter, the cover's edge below."""
    def curve(sd, y0, lift, n=14):
        return [(x + sd * 2.25 * s * k / n, y0 - lift * math.sin(math.pi * .5 * (k / n) ** .7) + .15 * s * (k / n) ** 3)
                for k in range(n + 1)]
    cover = [(x - 2.45 * s, y + 1.05 * s), (x, y + 1.42 * s), (x + 2.45 * s, y + 1.05 * s),
             (x + 2.45 * s, y + 1.25 * s), (x, y + 1.62 * s), (x - 2.45 * s, y + 1.25 * s)]
    cv.obj([cover], 1.)
    cv.hair(H(cover, 0, 1.5, .25))
    for sd in (-1, 1):
        top = curve(sd, y + .12 * s, .3 * s)
        bot = curve(sd, y + 1.38 * s, .3 * s)
        page = top + bot[::-1]
        # page block edge (the stack of leaves under the top page)
        edge = [top[-1], (top[-1][0] + sd * .12 * s, top[-1][1] + .1 * s), (bot[-1][0] + sd * .12 * s, bot[-1][1] + .02 * s), bot[-1]]
        cv.obj([edge], .5)
        cv.hair(H(edge, 90, 1.5, .25))
        cv.obj([page], 1.)
        n = max(3, int(1.26 * s / 2.))
        for r in range(1, n):
            f = r / n
            row = [(a[0], a[1] + (b[1] - a[1]) * f) for a, b in zip(top, bot)]
            k0, k1 = 2, 13 if r % 4 else 9
            cv.hair(row[k0:k1])
        gut = [(x, y + .12 * s)] + [(x + sd * .35 * s, y + .12 * s - .08 * s), (x + sd * .35 * s, y + 1.38 * s - .08 * s)] + [(x, y + 1.38 * s)]
        cv.obj([gut], 0)
        cv.hair(H(gut, 90, 1.5, .25))
    cv.line([(x, y + .12 * s), (x, y + 1.4 * s)])


def _scene(field, seed, date, small=False):
    """Everything inside the cartouche field polygon, returned clipped to it."""
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    fx, fy, fw, fh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    rng = random.Random(seed)
    cv = C.Canvas()
    blacks = []
    cx = fx + fw / 2
    hy = fy + fh * .57
    _sky(cv, fx, fy, fw, hy, date, rng)
    detail = 1.
    # distant trees along the horizon: rounded masses, darkly scribbled
    ground_far = hy + fh * .02
    tw = fw * .23
    wall_h = fh * .12
    roof_h = fh * .055
    # elms behind the wings: rounded crowns rising over the roofs, scribbled dark
    for i in range(11):
        tx = fx + fw * (i + rng.uniform(-.25, .25)) / 10
        if abs(tx - cx) < tw * .7:
            continue
        tr = fh * rng.uniform(.06, .085)
        tcy = ground_far - wall_h - roof_h - tr * rng.uniform(.45, .8)
        m = 13
        crown = [(tx + tr * (.9 + .13 * abs(math.sin(m * a / 2))) * math.cos(a),
                  tcy + tr * 1.12 * (.9 + .13 * abs(math.sin(m * a / 2))) * math.sin(a))
                 for a in [TAU * k / 104 for k in range(104)]]
        cv.obj([crown], 1.)
        # shadow side (lower right) ruled dark, the rest left for the leaf clumps
        sh = [(tx + tr * 1.1 * math.cos(a), tcy + tr * 1.25 * math.sin(a)) for a in [TAU * k / 30 for k in range(30)]]
        sh = [p for p in sh if (p[0] - tx) * .6 + (p[1] - tcy) > -tr * .25] or sh
        cv.hair(H(crown, 90, 1.5, .25))
        cv.obj([[(tx - tr * .4 + tr * .48 * math.cos(a), tcy - tr * .5 + tr * .4 * math.sin(a)) for a in [TAU * k / 24 for k in range(24)]]], 0)
        # leaf clumps: rows of little scallops, as an engraver cuts foliage
        yy = tcy - tr * 1.05
        row = 0
        while yy < tcy + tr * 1.05:
            half = tr * math.sqrt(max(0., 1 - ((yy - tcy) / (tr * 1.1)) ** 2)) * .9
            xx = tx - half + (1.3 if row % 2 else 0)
            while xx < tx + half - 2:
                cv.hair([(xx + 1.3 * math.cos(math.pi + math.pi * k / 4), yy + 1.1 * math.sin(math.pi + math.pi * k / 4) + 1.1) for k in range(5)][::-1])
                xx += 2.6
            yy += 2.5
            row += 1
    # rooks wheeling round the tower
    for _ in range(7):
        bx = cx + rng.uniform(-.32, .38) * fw
        by = fy + fh * rng.uniform(.08, .3)
        if abs(bx - cx) < tw * .7:
            bx += tw * (1 if bx > cx else -1)
        bs = rng.uniform(1.6, 2.6)
        cv.obj([], 0)
        cv.line([(bx - bs, by - bs * .45), (bx - bs * .4, by - bs * .1), (bx, by + bs * .2), (bx + bs * .4, by - bs * .1), (bx + bs, by - bs * .5)])
    _hall(cv, fx - 4, cx - tw * .5, ground_far, wall_h, roof_h, rng, False, blacks, detail)
    _hall(cv, cx + tw * .66, fx + fw + 4, ground_far, wall_h, roof_h, rng, True, blacks, detail)
    ttop = fy + fh * .15
    pl, bowl = _tower(cv, cx, ground_far, tw, ttop, rng, blacks, date, detail)
    back = cv.svg()
    # lawn and the maze in front
    fc = C.Canvas()
    lawn = _rect(fx - 2, ground_far, fw + 4, fy + fh - ground_far + 2)
    fc.obj([lawn], 0)
    fc.hair(H(lawn, 0, 2, .25))
    # gravel walk from the maze exit to the gate
    zf = 3.4
    ynear = fy + fh * 1.08
    wn = fw * 1.7
    maze_far = hy + (ynear - hy) / zf
    walk = [(cx - tw * .17, ground_far), (cx + tw * .17, ground_far), (cx + fw * .045, maze_far + 2), (cx - fw * .045, maze_far + 2)]
    fc.obj([walk], .5)
    fc.hair(H(walk, 0, 3, .25))
    gravel = _rect(fx - 2, maze_far, fw + 4, fy + fh - maze_far + 2)
    fc.obj([gravel], .5)
    fc.hair(H(gravel, 0, 3, 1.25))
    for _ in range(int(fw * (fy + fh - maze_far) / 40)):
        px, py = fx + rng.random() * fw, maze_far + 1 + rng.random() * (fy + fh - maze_far)
        fc.hair([(px, py), (px + .6, py)])
    cols = 9 if not small else 7
    rows = 6 if not small else 4
    hh = fh * .11
    P = _hedges(fc, cx, hy, ynear, wn, zf, hh, cols, rows, seed, rng)
    # the cap, dropped on the path in the nearest cell left of the entrance
    mx, my = P((cols // 2 - .5) / cols, 1.5 / rows)
    front = fc.svg()
    blk = C.Canvas()
    o = [back, f'<path d="{"".join(_d(b, True, 0) for b in blacks)}" fill="#000" stroke="none"/>']
    # the P on the shield: drawn white over its black field
    o.append(f'<path d="{_d(pl, tol=0)}{_d(bowl, tol=0)}" stroke="#fff" stroke-width="1.5" fill="none"/>')
    o.append(front)
    cap = C.Canvas()
    _mortarboard(cap, mx, my - 2, max(3., fw * .028))
    o.append(cap.svg())
    cid = C._uid("lr", fx, fy, fw, fh, seed)
    return (f'<clipPath id="{cid}"><path d="{_d(field, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{"".join(o)}</g>')


def _small_scene(field, seed, date):
    """The medallion of the short band: a mortarboard on an open book, ruled ground."""
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    fx, fy, fw, fh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    cv = C.Canvas()
    bg = _rect(fx - 2, fy - 2, fw + 4, fh + 4)
    cv.obj([bg], 0)
    cv.hair(H(bg, 0, 1.5, .25))
    s = min(fw / 6, fh / 2.6)
    _book(cv, fx + fw / 2, fy + fh * .5 - s * .75, s)
    _mortarboard(cv, fx + fw / 2 + s * 1.15, fy + fh * .42 + s * .25, s * .42, -.2)
    cid = C._uid("ls", fx, fy, fw, fh, seed)
    return (f'<clipPath id="{cid}"><path d="{_d(field, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ------------------------------------------------------------------------------------------
# lettering (drawn strokes, no <text>)
# ------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


_GLYPHS = {
    "T": (.72, [[(0, 1), (1, 1)], [(.5, 1), (.5, 0)]]),
    "H": (.74, [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .52), (1, .52)]]),
    "E": (.6, [[(1, 1), (0, 1), (0, 0), (1, 0)], [(0, .52), (.8, .52)]]),
    "R": (.68, [[(0, 0), (0, 1), (.7, 1), (.95, .9), (1, .76), (.95, .62), (.7, .52), (0, .52)], [(.55, .52), (1, 0)]]),
    "O": (.86, [_arc(.5, .5, .5, .5, 0, 360, 24)]),
    "C": (.74, [_arc(.55, .5, .55, .5, -50, -310, 18)]),
    "L": (.56, [[(0, 1), (0, 0), (1, 0)]]),
    "S": (.62, [[(1, .86), (.82, 1), (.2, 1), (0, .84), (.06, .64), (.3, .54), (.75, .46), (.98, .34), (1, .16), (.8, 0), (.18, 0), (0, .14)]]),
    "I": (.12, [[(.5, 0), (.5, 1)]]),
    "N": (.74, [[(0, 0), (0, 1), (1, 0), (1, 1)]]),
    "M": (.9, [[(0, 0), (0, 1), (.5, .25), (1, 1), (1, 0)]]),
    "A": (.76, [[(0, 0), (.5, 1), (1, 0)], [(.2, .36), (.8, .36)]]),
    "Y": (.72, [[(0, 1), (.5, .5), (1, 1)], [(.5, .5), (.5, 0)]]),
    "V": (.74, [[(0, 1), (.5, 0), (1, 1)]]),
    ".": (.2, [[(.5, .42), (.5, .58)]]),
    " ": (.42, []),
}


def _letter(cv, centre, text, lh, fleurons=True, track=.36):
    seg = [0.]
    for (ax, ay), (bx, by) in zip(centre, centre[1:]):
        seg.append(seg[-1] + math.hypot(bx - ax, by - ay))
    total = seg[-1]
    tr = lh * track
    widths = [_GLYPHS[c][0] * lh for c in text]
    tw = sum(widths) + tr * (len(text) - 1)

    def at(s):
        s = max(0., min(total, s))
        for i in range(1, len(seg)):
            if seg[i] >= s:
                t = (s - seg[i - 1]) / max(1e-6, seg[i] - seg[i - 1])
                (ax, ay), (bx, by) = centre[i - 1], centre[i]
                L = math.hypot(bx - ax, by - ay) or 1
                return ax + (bx - ax) * t, ay + (by - ay) * t, (bx - ax) / L, (by - ay) / L
        return centre[-1][0], centre[-1][1], 1., 0.

    s0 = total / 2 - tw / 2
    cv.obj([], 0)
    for ch, wdt in zip(text, widths):
        for stroke in _GLYPHS[ch][1]:
            pl = []
            for u, v in stroke:
                x, y, tx, ty = at(s0 + u * wdt)
                nx, ny = ty, -tx
                vv = (v - .5) * lh
                pl.append((x + nx * vv, y + ny * vv))
            (cv.heavy if ch == "." else cv.line)(pl)
        s0 += wdt + tr
    if not fleurons:
        return
    for side in (-1, 1):
        base = total / 2 + side * (tw / 2 + lh * .9)
        x, y, tx, ty = at(base)
        nx, ny = ty, -tx
        d = lh * .32
        dia = [(x - tx * d * 1.4, y - ty * d * 1.4), (x + nx * d, y + ny * d), (x + tx * d * 1.4, y + ty * d * 1.4), (x - nx * d, y - ny * d)]
        cv.obj([dia], .5)
        cv.hair(H(dia, 0, 1.5, .25))
        x2, y2, _, _ = at(base + side * lh * 1.1)
        x3, y3, _, _ = at(base + side * lh * 2.8)
        cv.line([(x2, y2), (x3, y3)])


# ------------------------------------------------------------------------------------------
# layouts (from the house frame, so the vignette can fill the whole field)
# ------------------------------------------------------------------------------------------

def _cart_field(cx, cy, cw, ch):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - 4.4, b - 4.4)


def _layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    o.append(_small_scene(C._ell_pts(cx, cy, rx - 4.5, ry - 4.5, 64), seed, date))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, date):
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
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    field = _cart_field(cx, cy, cw, gh + 4)
    o.append(_scene(field, seed, date, small=True) if gh >= 100 else _small_scene(field, seed, date))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    em = min(10., 6 + h * .01)
    top_free = em + 2
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.egg_and_dart(0, 0, w, em))
    o.append(C.dark_ground((0, py0 + ph - 2, w, h - py0 - ph + 2), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .48, ph * .66
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
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
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_scene(_cart_field(cx, cy, cw, ch), seed, date))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 58), True, rng.randrange(1 << 20)))
    bh = min(17, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.55, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lc = C.Canvas()
    _letter(lc, centre, "LOST IN THE MERITOCRACY", bh * .5, False, .3)
    o.append(lc.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    tc = C.Canvas()
    _letter(tc, [(tx, ty + th / 2 + .5), (tx + tw, ty + th / 2 + .5)], "THE ATLANTIC . MMV", min(th * .5, 10))
    o.append(tc.svg())
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
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 9 * 131
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date)
    else:
        body = _layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
