"""coast-05 'Coast happenings': Haystack Rock at Cannon Beach, engraved in the house Codex style.

Vignette: the Pacific at Cannon Beach at low sun. Haystack Rock and the Needles stand in a
ruled sea, gulls (the bird walks) wheel over a ruled sky, a small holiday star hangs over the
rock (Haystack Holidays), a great blue heron stands in the wet sand and driftwood lies on the
stippled beach. Easter egg: a trail of dog paw prints running along the sand toward the heron.
The ribbon carries "CANNON BEACH" in drawn capitals; the pedestal tablet carries a Vitruvian
wave (the "running dog") border.
"""
import sys
import math
import random
import engraving_codex as C

CR = ' shape-rendering="crispEdges"'


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dpl(pts, close=False):
    if len(pts) < 2:
        return ""
    o = "M" + f(pts[0][0]) + "," + f(pts[0][1])
    px, py = pts[0]
    for x, y in pts[1:]:
        o += "l" + f(x - px) + "," + f(y - py)
        px, py = x, y
    return o + ("z" if close else "")


def pip(x, y, poly):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def runs(y, x0, x1, test, step=.5, minlen=.8):
    """Horizontal runs at row y where test(x) holds."""
    out = []
    a = None
    x = x0
    while x <= x1:
        ok = test(x)
        if ok and a is None:
            a = x
        elif not ok and a is not None:
            if x - a >= minlen:
                out.append((a, x))
            a = None
        x += step
    if a is not None and x1 - a >= minlen:
        out.append((a, x1))
    return out


def hpath(segs):
    return "".join(f"M{f(a)},{f(y)}h{f(b - a)}" for y, a, b in segs)


def P(d, w=.5, crisp=False, fill="none"):
    if not d:
        return ""
    return f'<path d="{d}" fill="{fill}" stroke="#000" stroke-width="{f(w)}"{CR if crisp else ""}/>'


def F(d, fill="#fff", rule=""):
    if not d:
        return ""
    r = f' fill-rule="{rule}"' if rule else ""
    return f'<path d="{d}" fill="{fill}" stroke="none"{r}/>'


def row05(y):
    return math.floor(y * 2) / 2 + .25


def row1(y):
    return round(y * 2) / 2


# ------------------------------------------------------------------------------------------
# the vignette: Haystack Rock at Cannon Beach
# ------------------------------------------------------------------------------------------

HAY = [(0, 0), (.02, .2), (.045, .45), (.07, .66), (.1, .8), (.14, .89), (.2, .95), (.28, .99), (.36, 1.0),
       (.44, .985), (.5, .96), (.55, .93), (.6, .88), (.64, .8), (.67, .72), (.71, .66), (.76, .62), (.8, .58),
       (.84, .5), (.88, .38), (.92, .25), (.96, .12), (1, 0)]


def ext_at(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    if len(xs) < 2:
        return None
    return min(xs), max(xs)


def engrave_rock(poly, by, top, rng, fine=1.):
    """Basalt carved as facets: the rock is cut into a jittered grid of planes in its own (u, t)
    coordinates; each plane is hatched by its tone (lit from the left, darkening to the right),
    seams are cut in 1 px and the shadow-side rim in 1.5 px. Returns (white_fill_d, svg)."""
    H = by - top

    def at(u, t):
        t = min(t, .985)
        y = by - t * H
        e = ext_at(poly, y)
        if not e:
            return None
        l, r = e
        if 0 < u < 1:
            u = min(.99, max(.01, u + .06 * math.sin(t * 5.5 + u * 9)))
        return (l + u * (r - l), y)
    ncol = max(3, int(7 * fine))
    us = [0.] + sorted(rng.uniform(.1, .9) for _ in range(ncol - 1)) + [1.]
    half, one, seams = [], [], []
    for i in range(len(us) - 1):
        nrow = rng.randint(2, 4)
        ts = [0.] + sorted(rng.uniform(.12, .85) for _ in range(nrow - 1)) + [1.]
        for j in range(len(ts) - 1):
            u0, u1, t0, t1 = us[i], us[i + 1], ts[j], ts[j + 1]
            ed = []
            for k in range(7):
                ed.append(at(u0 + (u1 - u0) * k / 6, t0))
            for k in range(7):
                ed.append(at(u1, t0 + (t1 - t0) * k / 6))
            for k in range(7):
                ed.append(at(u1 - (u1 - u0) * k / 6, t1))
            for k in range(7):
                ed.append(at(u0, t1 - (t1 - t0) * k / 6))
            ed = [q for q in ed if q]
            if len(ed) < 4:
                continue
            um = (u0 + u1) / 2
            tone = um * 3.2 + rng.uniform(-.7, .7) + (.4 if t0 < .1 else 0)
            if tone < .8:
                half += C.hatch_poly(ed, 60, 3, rng.uniform(0, 3))
                half += C.hatch_poly(ed, 0, 3, rng.uniform(0, 3))
            elif tone < 1.6:
                half += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
            elif tone < 2.4:
                one += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
            else:
                one += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
                half += C.hatch_poly(ed, -30, 3, rng.uniform(0, 3))
            if t1 < 1:
                seams.append([q for q in (at(u0 + (u1 - u0) * k / 6, t1) for k in range(7)) if q])
        seams.append([q for q in (at(us[i + 1], k / 12 * .97) for k in range(13)) if q])
    o = [P("".join(dpl(p) for p in half), .5), P("".join(dpl(p) for p in one), 1),
         P("".join(dpl(p) for p in seams if p and len(p) > 1), 1)]
    n = len(poly)
    peak = min(range(n), key=lambda i: poly[i][1])
    o.append(P(dpl(poly[peak:]), 1.5))
    o.append(P(dpl(poly[:peak + 1]), 1))
    return dpl(poly, True), "".join(o)


def heron(x, y, s, flip=False):
    """A great blue heron standing at (x, y) = feet, s = height: body tilted, S-neck, dagger bill,
    black crest plume, dark wing coverts in bulino."""
    sx = -1 if flip else 1

    def T(px, py):
        return (x + sx * px * s, y - py * s)
    out = [(-.36, .32), (-.28, .41), (-.12, .53), (.04, .6), (.13, .63), (.15, .7), (.1, .78), (.09, .86),
           (.13, .92), (.2, .95), (.25, .955), (.46, .925), (.25, .92), (.21, .9), (.17, .86), (.17, .8),
           (.22, .72), (.23, .63), (.2, .54), (.13, .45), (0, .4), (-.18, .36)]
    sil = [T(*q) for q in out]
    o = [F(dpl(sil, True)), P(dpl(sil, True), 1)]
    # wing: closed, dark, feathered in bulino
    wing = [T(-.34, .33), T(-.2, .44), T(0, .54), T(.12, .58), T(.12, .5), T(0, .44), T(-.2, .37)]
    o.append(F(dpl(wing, True), C.pat("M")) + P(dpl(wing, True), 1))
    fl = [[T(.1 - k * .06, .52 - k * .03), T(-.25 - k * .02, .37 - k * .005)] for k in range(4)]
    o.append(P("".join(dpl(p) for p in fl), .5))
    # neck streaks and breast plumes
    o.append(P(dpl([T(.155, .62), T(.13, .72), T(.12, .8)]) + dpl([T(.16, .52), T(.1, .44)]) + dpl([T(.12, .5), T(.06, .43)]), .5))
    o.append(F(dpl([T(.15, .935), T(-.02, .95), T(.15, .92)], True), "#000"))
    o.append(P(dpl([T(.25, .938), T(.46, .925)]), .5))
    eye = T(.2, .935)
    o.append(F(f"M{f(eye[0] - .7)},{f(eye[1])}a.7,.7 0 1,0 1.4,0a.7,.7 0 1,0 -1.4,0z", "#000"))
    legs = [[T(.02, .42), T(.01, .2), T(0, 0)], [T(.07, .43), T(.08, .21), T(.1, 0)],
            [T(-.06, 0), T(.05, 0)], [T(.05, 0), T(.17, 0)]]
    o.append(P("".join(dpl(p) for p in legs), 1))
    return "".join(o)


def paw(x, y, s, ang):
    """One dog paw print (pad + four toes) as closed paths, centred (x, y)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def T(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    o = ""
    for (px, py, rx, ry) in [(0, .35, .55, .42), (-.55, -.3, .2, .27), (-.2, -.62, .2, .27), (.2, -.62, .2, .27), (.55, -.3, .2, .27)]:
        o += dpl([T(px + rx * math.cos(t * math.pi / 6), py + ry * math.sin(t * math.pi / 6)) for t in range(12)], True)
    return o


def vignette(x0, y0, W, H, clip_d, cid, seed=0, mode="tall"):
    """Fill the whole box (clipped to clip_d) with the Cannon Beach scene."""
    rng = random.Random(seed * 31 + 7)
    o = []
    x1, y1 = x0 + W, y0 + H
    band = mode == "band"
    hz = y0 + H * (.6 if band else .56)
    shore = y0 + H * (1.1 if band else .74)
    sx, sy, sr = x0 + W * .22, hz - H * .015, H * (.13 if band else .1)
    rbw = W * (.3 if band else .36)
    rbh = min(H * (.5 if band else .42), (hz - y0) * .82, rbw * .72)
    rbx = x0 + W * (.46 if band else .42)
    rock = [(rbx + u * rbw, hz + 1.5 - t * rbh) for u, t in
            [(u + rng.uniform(-.006, .006) * (0 < u < 1), t * rng.uniform(.98, 1.02) if 0 < t < 1 else t) for u, t in HAY]]
    needles = []
    nx = rbx + rbw * 1.08
    for (dx, wv, hv) in ((0, .09, .34), (.13, .06, .22), (.23, .045, .12)):
        bx = nx + rbw * dx
        bw_, bh_ = rbw * wv, rbh * hv
        needles.append([(bx, hz + 1), (bx + bw_ * .15, hz - bh_ * .6), (bx + bw_ * .38, hz - bh_), (bx + bw_ * .6, hz - bh_ * .92),
                        (bx + bw_ * .8, hz - bh_ * .45), (bx + bw_, hz + 1)])
    head = [(x0 - 2, hz + .5), (x0 - 2, hz - H * .15)]
    for i in range(1, 25):
        t = i / 24
        head.append((x0 - 2 + W * .3 * t, hz - H * .15 * (1 - t ** 1.6) - (math.sin(i * 2.3) * .9 + .9) * (1 - t)))
    head.append((x0 + W * .3, hz + .5))
    head = [(x0 + x1 - hx_, hy_) for hx_, hy_ in head]  # Tillamook Head lies north: right

    # ---- sky: ruled at pitch 2, doubled to pitch 1 in the deep upper sky; light cloud banks
    #      (pitch 3) with scalloped rims; rays of the sun thin the lines out to pitch 4.
    rays = 18

    def in_ray(x, y):
        a = math.atan2(y - sy, x - sx)
        return (int((a + math.pi) / (2 * math.pi) * rays * 2) % 2) == 0

    clouds = []
    for i in range(3):
        cx_ = x0 + W * (.12 + .33 * i + rng.uniform(-.05, .05))
        cy_ = y0 + (hz - y0) * rng.uniform(.3, .5)
        cw_ = W * rng.uniform(.18, .26)
        ch_ = (hz - y0) * rng.uniform(.07, .1)
        top_ = [(cx_ - cw_ / 2 + cw_ * t, cy_ - ch_ * (math.sin(math.pi * t) ** .7) * (.7 + .3 * abs(math.sin(t * math.pi * 4 + i))))
                for t in [k / 24 for k in range(25)]]
        bot_ = [(cx_ + cw_ / 2 - cw_ * t, cy_ + ch_ * .25 * math.sin(math.pi * t)) for t in [k / 12 for k in range(1, 12)]]
        clouds.append(top_ + bot_)
    sky = []
    y = row05(y0) - .5
    k = 0
    deep = y0 + (hz - y0) * .42
    while y < hz:
        incl = [c for c in clouds if min(q[1] for q in c) - 1 < y < max(q[1] for q in c) + 1]

        def tst(x, y=y, k=k):
            if (x - sx) ** 2 + (y - sy) ** 2 < (sr * 1.25) ** 2:
                return False
            if pip(x, y, head):
                return False
            for c in incl:
                if pip(x, y, c):
                    return k % 3 == 0
            if k % 2 == 1 and in_ray(x, y) and math.hypot(x - sx, y - sy) < W * .55:
                return False
            return True
        for a, b in runs(y, x0 - 1, x1 + 1, tst):
            sky.append((y, a, b))
        if y < deep:
            yy = y + 1
            frac = max(0., (yy - y0) / (deep - y0) - .55) / .45

            def t2(x, yy=yy):
                if (x - sx) ** 2 + (yy - sy) ** 2 < (sr * 2.2) ** 2:
                    return False
                for c in incl:
                    if pip(x, yy, c):
                        return False
                return True
            for a, b in runs(yy, x0 - 1, x1 + 1, t2):
                # break the doubled rule into dashes as it fades toward the horizon
                x = a
                while x < b:
                    L = rng.uniform(4, 30) * (1 - frac * .7)
                    if b - x > 1.5:
                        sky.append((yy, x, min(b, x + L)))
                    x += L + rng.uniform(1, 2 + 10 * frac)
        y += 2
        k += 1
    o.append(P(hpath(sky), .5, True))
    o.append(P(''.join(dpl(c[:25]) for c in clouds), .5))
    sun = []
    y = row05(sy - sr)
    while y < hz:
        dd = sr * sr - (y - sy) ** 2
        if dd > 0:
            hw = math.sqrt(dd)
            sun.append((y, sx - hw, sx + hw))
        y += 3
    o.append(P(hpath(sun), .5, True))
    o.append(P(dpl([(sx + sr * math.cos(t), sy + sr * math.sin(t)) for t in [math.pi + math.pi * i / 30 for i in range(31)]]), 1))
    # headland: a forested dark mass, 1 px rules at pitch 2
    hd = []
    y = row1(hz - H * .2)
    while y < hz:
        for a, b in runs(y, x1 - W * .32, x1 + 2, lambda x, y=y: pip(x, y, head)):
            hd.append((y, a, b))
        y += 2
    o.append(P(hpath(hd), 1, True))
    o.append(P(dpl(head[1:-1]), 1))
    trees = []
    for i in range(2, 22, 2):
        px, py = head[i]
        trees.append([(px - 1, py + .5), (px, py - 2.2), (px + 1, py + .5)])
    o.append(P("".join(dpl(p) for p in trees), .5))
    # ---- sea
    sea_half, sea_one = [], []
    y = row05(hz) + .5
    while y < shore:
        d = (y - hz) / max(1, shore - hz)
        pitch = 1.5 if d < .35 else 2
        x = x0 - 1
        while x < x1 + 1:
            L = rng.uniform(3, 10 + 25 * d)
            gap = rng.uniform(.8, 2.2 + 1.5 * d)
            if abs(x - sx) < sr * (1 - d * .3):
                L *= .4
                gap *= 2.2
            seg = (y, x, min(x + L, x1 + 1))
            refl = rbx + rbw * .05 < x < rbx + rbw * .9 and d < .5
            (sea_one if (refl and rng.random() < .8) or rng.random() < .07 else sea_half).append(seg)
            x += L + gap
        y += pitch
    sea_one = [(row1(yy), a, b) for yy, a, b in sea_one]
    o.append(P(hpath(sea_half), .5, True))
    o.append(P(hpath(sea_one), 1, True))
    o.append(P(f"M{f(x0 - 1)},{f(row1(hz))}h{f(W + 2)}", 1, True))
    # ---- rocks
    for nd in needles:
        dn, sv = engrave_rock(nd, hz + 1, min(p[1] for p in nd), rng, fine=.3)
        o.append(F(dn) + sv)
    rd, rs = engrave_rock(rock, hz + 1.5, min(p[1] for p in rock), rng)
    o.append(F(rd) + rs)
    tick = []
    for i in range(7):
        px = rbx + rbw * (.28 + i * .04)
        topy = min((p[1] for p in rock if abs(p[0] - px) < rbw * .05), default=hz)
        tick.append(f"M{f(px)},{f(topy - .3)}v-1.6")
    o.append(P("".join(tick), 1))
    fx0, fx1 = rbx - rbw * .08, nx + rbw * .3
    foam = [(fx0, hz + 1.5)]
    n = 30
    for i in range(n + 1):
        t = i / n
        foam.append((fx0 + (fx1 - fx0) * t, hz + 2.5 + math.sin(t * math.pi) * 2.5 + (math.sin(i * 1.9) * .8)))
    for i in range(n, -1, -1):
        foam.append((fx0 + (fx1 - fx0) * i / n, hz + 1.5))
    o.append(F(dpl(foam, True)))
    curls = []
    for i in range(int((fx1 - fx0) / 5)):
        cx_ = fx0 + 3 + i * 5 + rng.uniform(-1, 1)
        cy_ = hz + 3 + rng.uniform(-.5, .8)
        curls.append([(cx_ - 2, cy_ + .8), (cx_ - .5, cy_ - .6), (cx_ + 1, cy_ - .2), (cx_ + .6, cy_ + .6)])
    o.append(P("".join(dpl(p) for p in curls), .5))
    if not band:
        stx, sty = rbx + rbw * .42, y0 + (hz - rbh - y0) * .45 + H * .02
        sr2 = H * .035
        star = []
        for i in range(16):
            a = -math.pi / 2 + i * math.pi / 8
            rr = sr2 * (1 if i % 4 == 0 else (.45 if i % 2 == 0 else .25))
            star.append((stx + rr * math.cos(a), sty + rr * math.sin(a)))
        R = sr2 * 1.3
        o.append(F(f"M{f(stx - R)},{f(sty)}a{f(R)},{f(R)} 0 1,0 {f(2 * R)},0a{f(R)},{f(R)} 0 1,0 {f(-2 * R)},0z"))
        o.append(F(dpl(star, True)) + P(dpl(star, True), .5))
        o.append(F(f"M{f(stx - .8)},{f(sty)}a.8,.8 0 1,0 1.6,0a.8,.8 0 1,0 -1.6,0z", "#000"))
    gulls = []
    for i in range(4 if band else 7):
        gx = x0 + W * rng.uniform(.08, .95)
        gy = y0 + (hz - y0) * rng.uniform(.12, .7)
        if math.hypot(gx - sx, gy - sy) < sr * 1.6 or (rbx - 4 < gx < rbx + rbw + 4 and gy > hz - rbh - 4):
            continue
        s = rng.uniform(2.2, 3.6) * (H / 140 if not band else .7)
        s = max(2., min(4.5, s))
        gulls.append([(gx - s, gy - s * .2), (gx - s * .45, gy - s * .55), (gx, gy), (gx + s * .45, gy - s * .55), (gx + s, gy - s * .2)])
    if gulls:
        o.append(P("".join(dpl(g) for g in gulls), 1))
    if not band:
        wet = []
        y = row05(shore)
        while y < y1 + 1:
            x = x0 - 1
            while x < x1 + 1:
                L = rng.uniform(10, 40)
                wet.append((y, x, x + L))
                x += L + rng.uniform(1.5, 4)
            y += 2
        edge = [(x0 - 2, shore - 2)]
        for i in range(41):
            t = i / 40
            edge.append((x0 - 2 + (W + 4) * t, shore + 1.5 + math.sin(t * 19 + seed) * 1.6 + math.sin(t * 7) * 1.2))
        edge.append((x1 + 2, shore - 2))
        dry_top = [(x0 + W * t, shore + H * .07 + math.sin(t * 5.2 + 1) * H * .03 + t * H * .04) for t in [i / 30 for i in range(31)]]
        dry = [(x0 - 2, dry_top[0][1])] + dry_top + [(x1 + 2, dry_top[-1][1]), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]
        o.append(F(f"M{f(x0 - 2)},{f(shore - 2)}H{f(x1 + 2)}V{f(y1 + 2)}H{f(x0 - 2)}z"))
        o.append(P(hpath(wet), .5, True))
        o.append(F(dpl(edge, True)) + P(dpl(edge[1:-1]), .5))
        o.append(F(dpl(dry, True), C.pat("S")) + P(dpl(dry_top), 1))
        hh = H * .3
        hx, hy = x0 + W * .82, shore + H * .055
        o.append(heron(hx, hy, hh, flip=True))
        o.append(P(f"M{f(hx - 4)},{f(row05(hy + 1.5))}h9M{f(hx - 2)},{f(row05(hy + 3.5))}h5", .5, True))
        lx, ly, lw, lh = x0 + W * .04, y1 - H * .085, W * .3, H * .055
        logp = [(lx + lw * t, ly - lh * .5 + math.sin(t * 3) * lh * .12) for t in [i / 16 for i in range(17)]]
        logp += [(lx + lw * t, ly + lh * .5 + math.sin(t * 3) * lh * .12) for t in [i / 16 for i in range(16, -1, -1)]]
        o.append(F(dpl(logp, True)) + P(dpl(logp, True), 1))
        grain = []
        for j in range(1, int(lh / 1.6)):
            v = -.5 + j * 1.6 / lh
            grain.append([(lx + lw * t + 2, ly + lh * v + math.sin(t * 3) * lh * .12 + math.sin(t * 25 + j) * .35)
                          for t in [i / 30 for i in range(30)] if t < .97])
        o.append(P("".join(dpl(g) for g in grain[len(grain) // 2:]), 1))
        o.append(P("".join(dpl(g) for g in grain[:len(grain) // 2]), .5))
        ex, ey = lx + lw, ly + math.sin(3) * lh * .12
        el = lambda rx, ry: f"M{f(ex - rx)},{f(ey)}a{f(rx)},{f(ry)} 0 1,0 {f(2 * rx)},0a{f(rx)},{f(ry)} 0 1,0 {f(-2 * rx)},0z"
        o.append(F(el(lh * .22, lh * .5)) + P(el(lh * .22, lh * .5) + el(lh * .1, lh * .25), .5))
        # EASTER EGG: a dog's paw-print trail across the sand toward the heron
        pr = ""
        ps = max(2.2, H * .014)
        for i in range(9):
            t = i / 8
            px = x0 + W * (.3 + .44 * t)
            py = shore + H * (.085 - .02 * t) + (ps * 1.3 if i % 2 else -ps * 1.3)
            pr += paw(px, py, ps, math.pi / 2 - .12)
        o.append(F(pr) + P(pr, .5))
        gr = []
        for side in (0, 1):
            bx = x0 + (W * .02 if side == 0 else W * .96)
            for i in range(7):
                a = -math.pi / 2 + (i - 3) * .22
                L = H * rng.uniform(.06, .11)
                gr.append([(bx + i * 1.2, y1 + 1), (bx + i * 1.2 + math.cos(a) * L * .5 + 1, y1 + 1 + math.sin(a) * L * .55),
                           (bx + i * 1.2 + math.cos(a) * L + (i - 3) * .9, y1 + 1 + math.sin(a) * L)])
        o.append(P("".join(dpl(g) for g in gr), 1))
    body = "".join(o)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------
# drawn lettering for the ribbon
# ------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


GLYPHS = {
    "C": (.62, [_arc(.33, .5, .31, .5, -.28 * math.pi, -1.72 * math.pi, 14)]),
    "A": (.7, [[(0, 1), (.35, 0), (.7, 1)], [(.14, .64), (.56, .64)]]),
    "N": (.66, [[(0, 1), (0, 0), (.66, 1), (.66, 0)]]),
    "O": (.7, [_arc(.35, .5, .35, .5, 0, 2 * math.pi, 18)]),
    "B": (.58, [[(0, 0), (0, 1)], [(0, 0), (.36, 0)] + _arc(.36, .24, .2, .24, -math.pi / 2, math.pi / 2, 6) + [(0, .48)],
                [(0, .48), (.38, .48)] + _arc(.38, .74, .22, .26, -math.pi / 2, math.pi / 2, 6) + [(0, 1)]]),
    "E": (.56, [[(.56, 0), (0, 0), (0, 1), (.56, 1)], [(0, .5), (.44, .5)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    " ": (.45, []),
}


def letter_along(centre, text, cap):
    """Stroke the text centred along the polyline centre, caps `cap` px tall."""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.dist(centre[i - 1], centre[i]))
    tot = L[-1]
    track = .32
    widths = [GLYPHS[c][0] * cap for c in text]
    tw = sum(widths) + track * cap * (len(text) - 1)
    s = (tot - tw) / 2

    def at(sv):
        sv = max(0, min(tot - 1e-6, sv))
        for i in range(1, len(L)):
            if L[i] >= sv:
                t = (sv - L[i - 1]) / max(1e-9, L[i] - L[i - 1])
                p0, p1 = centre[i - 1], centre[i]
                a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
                return p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, a
        return centre[-1][0], centre[-1][1], 0
    out = []
    for c, wv in zip(text, widths):
        for stroke in GLYPHS[c][1]:
            pts = []
            for gx, gy in stroke:
                px, py, a = at(s + gx * cap)
                dy = (gy - .5) * cap
                pts.append((px - math.sin(a) * dy, py + math.cos(a) * dy))
            out.append(pts)
        s += wv + track * cap
    return "".join(dpl(p) for p in out)


def running_dog(tx, ty, tw, th):
    """A Vitruvian wave ('running dog') across the tablet on a light ruled ground."""
    o = [F(f"M{f(tx + 2)},{f(ty + 2)}h{f(tw - 3)}v{f(th - 3)}h{f(-(tw - 3))}z", C.pat("L"))]
    h = th - 4
    per = max(8., h * 1.7)
    n = max(1, int((tw - 6) / per))
    per = (tw - 6) / n
    base = ty + 2 + h * .92
    pts = []
    for i in range(n):
        x = tx + 3 + i * per
        r = h * .34
        cx, cy = x + per * .55, ty + 2 + h * .45
        seg = [(x, base), (x + per * .25, base - h * .1)]
        for j in range(19):
            t = j / 18
            a = math.pi * .95 - t * math.pi * 2.1
            rr = r * (1 - .62 * t)
            seg.append((cx + rr * math.cos(a) * 1.05, cy - rr * math.sin(a)))
        pts.append(seg)
    o.append(P("".join(dpl(p) for p in pts), 1))
    o.append(P(f"M{f(tx + 3)},{f(base + .5)}h{f(tw - 6)}", 1))
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts (adapted from the house frame so the vignette fills the whole carved field)
# ------------------------------------------------------------------------------------------

def _field(cx, cy, w, h, inset=4.5):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return dpl(C._superellipse(cx, cy, a - inset, b - inset), True), (cx - a, cy - b, 2 * a, 2 * b)


def _redots(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    bp = C._superellipse(cx, cy, a - 4.5, b - 4.5)
    return P(dpl(bp + [bp[0]]), 1)


def layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = [F(f"M0,0h{f(w)}v{f(h)}h{f(-w)}z", C.pat("D"))]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{f(px0 - 3.5)},{f(py0 - 3.5)}h{f(pw + 7)}v{f(ph + 7)}h{f(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{f(px0 - 1.5)},{f(py0 - 1.5)}h{f(pw + 3)}v{f(ph + 3)}h{f(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = (pw * .5, ph * .64) if h >= 400 else (pw * .56, ph * .72)
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .04), rmax=r1 * .9,
                   max_n=int(14 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    clip_d, (fx, fy, fw, fh) = _field(cx, cy, cw, ch)
    o.append(vignette(fx, fy, fw, fh, clip_d, C._uid("v", w, h, seed), seed, "tall"))
    o.append(_redots(cx, cy, cw, ch))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, max(11, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(P(letter_along(centre, "CANNON BEACH", bh * .56), 1))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(running_dog(tx, ty, tw, th))
    fy2 = py + ped_h
    fh2 = h - fy2
    if fh2 > 14:
        o.append(C.dark_ground((w * .06, fy2, w * .88, fh2 - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy2, w * .88, fh2 - 2,
                         C.scroll_band(w * .06, fy2, w * .88, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy2 + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{f(w * .06)},{f(h - 1.5)}h{f(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.7)
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .07), rmax=r * .8,
                   max_n=int(14 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    clip_d, (fx, fy, fw, fh) = _field(cx, cy, cw, gh + 4)
    o.append(vignette(fx, fy, fw, fh, clip_d, C._uid("v", w, h, seed), seed, "tall"))
    o.append(_redots(cx, cy, cw, gh + 4))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.2, 150)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    ell = C._ell_pts(cx, cy, rx - 3, ry - 3, 64)
    o.append(vignette(cx - rx, cy - ry, 2 * rx, 2 * ry, dpl(ell, True), C._uid("v", w, h, seed), seed, "band"))
    o.append(f'<path d="M0,{f(h - .5)}h{f(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5
    if h < 110:
        body = layout_band(w, h, seed)
    elif h <= 260:
        body = layout_medium(w, h, seed)
    else:
        body = layout_tall(w, h, seed, .8 if h < 440 else 1.)
    return C.svg_doc(w, h, body)
