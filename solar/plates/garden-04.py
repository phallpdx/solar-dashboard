"""garden-04 "Sow and plant": garlic going in now (rows 18 in apart, cloves 3 in apart, soil 53F at
2 in, a few dry days from Wed). The plate engraves the garlic bed itself: a cartouche holds a
perspective of mounded rows of young garlic running back to the cottonwood line and Mt. Hood under
a dry low sun, cut away in front to show the cloves planted point-up in the soil with a soil
thermometer at 2 in; whole garlic bulbs flank it, their strap leaves sweeping out as the acanthus.
Easter egg: a trail of dog paw prints across the bed."""
import sys
import math
import random
import zlib
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_n = C._n
_d = C._d
_ell = C._ell_pts


def _cid(*a):
    return "g4" + format(zlib.crc32(repr(a).encode()) & 0xffffff, "x")


def _clip_d(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _seed(ctx):
    return zlib.crc32(((ctx or {}).get("date", "") + "garlic").encode()) & 0xfffff


# ----------------------------------------------------------------------------------------------
# the garlic bulb, engraved
# ----------------------------------------------------------------------------------------------

class Bulb:
    """Onion-pointed garlic bulb, centre (cx, cy), half-width a, half-height b.
    pt(phi, lam): phi 0 (neck) .. pi (base), lam -1..1 across (sin of the longitude)."""

    def __init__(self, cx, cy, a, b):
        self.cx, self.cy, self.a, self.b = cx, cy, a, b

    def hw(self, phi):
        s = math.sin(phi)
        if phi < PI / 2:
            return self.a * s ** 1.9
        return self.a * s ** .75

    def y(self, phi):
        c = math.cos(phi)
        return self.cy - self.b * c if c > 0 else self.cy - self.b * .78 * c

    def pt(self, phi, lam):
        # clove bulges: each of the 7 segments swells a little between its grooves
        th = math.asin(max(-1., min(1., lam)))
        f = 1 + .045 * abs(math.sin((th + PI / 2) * 7 / 2))
        return (self.cx + self.hw(phi) * lam * f, self.y(phi))

    def outline(self, n=80):
        R = [self.pt(PI * i / n, 1) for i in range(n + 1)]
        L = [self.pt(PI * i / n, -1) for i in range(n + 1)]
        return R + L[::-1][1:-1]

    def meridian(self, th, dth, p0=.03, p1=.985, minsp=1.5):
        """Line at longitude th, kept where it lies at least minsp from a neighbour dth away."""
        segs, cur = [], []
        lam = math.sin(th)
        k = abs(math.cos(th)) * dth
        for i in range(81):
            phi = PI * (p0 + (p1 - p0) * i / 80)
            if self.hw(phi) * k >= minsp:
                cur.append(self.pt(phi, lam))
            else:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
        if len(cur) > 1:
            segs.append(cur)
        return segs


def garlic_bulb(cv, cx, cy, a, b, seed=0, roots=True, neck=True, leaves=None, light=-1):
    """A whole garlic bulb into cv: cloves as carved segments shaded along their form, papery
    skin, a ruff of roots, the neck. leaves: list of (ang_deg, length, bend, curl) fingers from the
    neck top (drawn behind the bulb). light -1: light from the left."""
    rng = random.Random(seed)
    B = Bulb(cx, cy, a, b)
    top = (cx, cy - b)
    nh = b * .55
    # leaves first (behind), springing from the neck top
    if neck:
        ntop = (cx, cy - b - nh)
        for ang, ln, bend, curl in (leaves or []):
            C._finger(cv, ntop[0] + math.cos(math.radians(ang)) * 1.5, ntop[1] + 2, math.radians(ang), ln,
                      ln * .085, bend, curl, 1.)
        nw0, nw1 = a * .2, a * .1
        neckp = [(cx - nw0, cy - b + 3), (cx - nw1, cy - b - nh), (cx + nw1, cy - b - nh), (cx + nw0, cy - b + 3)]
        cv.obj([neckp], 1.)
        for f in (.25, .5, .75):
            cv.hair([(cx + nw0 * f * -light * -1, cy - b + 2), (cx + nw1 * f * -light * -1, cy - b - nh + 1)])
        cv.hair(C.hatch_poly(neckp, 90, 1.5, cx + nw0 * .3))
        # a wrapped collar where the neck meets the bulb
        cv.line([(cx - nw0 * 1.3, cy - b + 4), (cx, cy - b + 5.2), (cx + nw0 * 1.3, cy - b + 4)])
        cv.hair([(cx - nw0 * .9, cy - b - nh * .45), (cx + nw0 * .9, cy - b - nh * .4)])
    if roots:
        bx, by = cx, B.y(PI) - .5
        cv.obj([], 0)
        nr = int(9 + a * .35)
        for i in range(nr):
            t = (i + .5) / nr - .5
            ln = b * rng.uniform(.35, .6) * (1 - abs(t) * .6)
            ang = PI / 2 + t * 2.4
            pts = []
            x, y = bx + t * a * .5, by
            aa = ang
            for k in range(10):
                aa += rng.uniform(-.25, .25)
                x += math.cos(aa) * ln / 10
                y += math.sin(aa) * ln / 10
                pts.append((x, y))
            cv.hair([(bx + t * a * .5, by)] + pts)
    ol = B.outline()
    cv.obj([ol], 1.)
    # cloves: boundaries at fixed longitudes, each clove bulging; shading on its shadow side
    ncl = 7
    bounds = [-PI / 2 + PI * i / ncl for i in range(ncl + 1)]
    for th in bounds[1:-1]:
        for s in B.meridian(th, .25, .04, .975, .8):
            cv.heavy(s)
        for s in B.meridian(th + .05 * -light, .25, .12, .9, 1.2):
            cv.line(s)
    dth = .055
    for k in range(ncl):
        t0, t1 = bounds[k], bounds[k + 1]
        mid = (t0 + t1) / 2
        # how much of the clove is in shadow: more toward the shadow side of the bulb
        sh = .38 + .45 * (math.sin(mid) * -light + 1) / 2
        th = t1 - dth * .5 if light < 0 else t0 + dth * .5
        stop = t1 - (t1 - t0) * sh if light < 0 else t0 + (t1 - t0) * sh
        j = 0
        while (th > stop) if light < 0 else (th < stop):
            p0 = .08 + .05 * (j % 2)
            for s in B.meridian(th, dth, p0, .95 - .04 * (j % 3), 1.5):
                cv.hair(s)
            th += dth * light
            j += 1
        # a highlight-side hairline that runs only part way
        hl = t0 + (t1 - t0) * .25 if light < 0 else t1 - (t1 - t0) * .25
        for s in B.meridian(hl, .4, .3, .7, 1.):
            cv.hair(s)
    # cross contours (latitudes) on the shadow flank and the underside: crosshatch
    for i in range(1, 28):
        phi = PI * (.35 + .62 * i / 28)
        hw = B.hw(phi)
        yy = B.y(phi)
        lam0 = .1 if phi > PI * .72 else .38
        line = []
        for q in range(15):
            lam = (lam0 + (.98 - lam0) * q / 14) * -light
            line.append((cx + hw * lam, yy + hw * .16 * math.cos(math.asin(min(1, abs(lam))))))
        if i % 2 == 0 or phi > PI * .8:
            cv.hair(line)
    # black core shadow hugging the shadow edge
    shp = [B.pt(PI * (.3 + .66 * i / 40), -light * (.9 - .06 * math.sin(PI * i / 40))) for i in range(41)]
    shp += [B.pt(PI * (.3 + .66 * i / 40), -light * 1.0) for i in range(40, -1, -1)]
    cv.obj([shp], 0)
    cv.line(C.hatch_poly(shp, 80, 1.))
    # basal plate
    bp = _ell(cx, B.y(PI) - 1.2, a * .22, 1.6, 16)[:-1]
    cv.obj([bp], 1.)
    cv.line(C.hatch_poly(bp, 0, 1.))
    # papery skin: a few torn flakes
    for i in range(3):
        phi = PI * rng.uniform(.25, .55)
        lam = rng.uniform(-.85, -.4) * -light * -1
        p = B.pt(phi, lam)
        cv.hair([p, (p[0] + rng.uniform(-3, 3), p[1] + rng.uniform(4, 8))])
    return B


# ----------------------------------------------------------------------------------------------
# small subjects
# ----------------------------------------------------------------------------------------------

def clove(cv, cx, cy, s, tilt=0., rng=None):
    """A planted clove, point up, base at (cx, cy), s tall, with a root tuft."""
    rng = rng or random.Random(0)
    ca, sa = math.cos(tilt), math.sin(tilt)

    def P(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    w = s * .36
    pts = []
    for i in range(25):
        t = i / 24
        pts.append(P(w * math.sin(PI * t) ** .8 * (1 - .35 * t) * (1 if True else 0), -s * t))
    right = pts
    left = [P(-w * .75 * math.sin(PI * t) ** .9 * (1 - .4 * t), -s * t) for t in [i / 24 for i in range(25)]]
    poly = right + left[::-1][1:-1]
    for i in range(5):
        t = (i + .5) / 5 - .5
        x0, y0 = P(t * w * .8, 0)
        cv.hair([(x0, y0), (x0 + t * 4 + rng.uniform(-1, 1), y0 + s * rng.uniform(.25, .4))])
    cv.obj([poly], 1.)
    # back seam and shading on the right flank
    cv.hair([P(w * .1, -s * .05), P(w * .15, -s * .5), P(0, -s * .98)])
    for f in (.95, .8, .65, .5):
        cv.hair([P(w * f * math.sin(PI * t) ** .8 * (1 - .35 * t), -s * t) for t in [.08 + .8 * i / 12 for i in range(13)]])
    cv.line([P(-w * .4, -s * .02), P(w * .5, -s * .02)])


def sprout(cv, x, y, hgt, wt=1., rng=None):
    """A young garlic shoot: two or three strap leaves fanning from the soil."""
    rng = rng or random.Random(0)
    n = 3 if hgt > 6 else 2
    for i in range(n):
        t = (i - (n - 1) / 2)
        ang = -PI / 2 + t * .38 + rng.uniform(-.08, .08)
        ln = hgt * (1 - .2 * abs(t))
        k = t * .9 / max(ln, 1)
        pts = C._euler(x, y, ang, ln, lambda u, k=k: k * (.3 + u), 8)
        if hgt > 9:
            w0 = max(.9, hgt * .06)
            R = C._Rib(pts, [w0 * (1 - j / 8) + .2 for j in range(9)], [w0 * (1 - j / 8) + .2 for j in range(9)])
            cv.obj([R.outline()], .5)
            cv.hair(R.contour(-.3 if t >= 0 else .3, 0, .85))
        else:
            (cv.line if wt >= 1 else cv.hair)(pts)


def paw(x, y, s, ang):
    """A dog's paw print (filled black): pad and four toes."""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)
    o = [_d([P(*q) for q in _ell(0, .35 * s, .55 * s, .42 * s, 14)], True, 0)]
    for tx, ty in ((-.62, -.35), (-.22, -.72), (.22, -.72), (.62, -.35)):
        o.append(_d([P(*q) for q in _ell(tx * s, ty * s, .2 * s, .26 * s, 10)], True, 0))
    return "".join(o)


def soil_thermometer(cv, x, y_surf, depth, r, temp_f=53):
    """Dial soil thermometer: dial r above the soil on a short stem, probe down to `depth`."""
    dy = y_surf - r * 2.6
    cv.obj([[(x - .9, dy + r), (x + .9, dy + r), (x + .9, y_surf + depth), (x, y_surf + depth + 2.5),
             (x - .9, y_surf + depth)]], 1.)
    disc = _ell(x, dy, r, r, 32)[:-1]
    cv.obj([_ell(x + .8, dy + .8, r + 1.4, r + 1.4, 32)[:-1]], 0)
    cv.line(C.hatch_poly(_ell(x + .8, dy + .8, r + 1.4, r + 1.4, 32)[:-1], 45, 1.))
    cv.obj([disc], 1.5)
    # ticks 0..120 F over 270 degrees
    for i in range(13):
        a = math.radians(135 + 270 * i / 12)
        r0 = r * (.62 if i % 3 == 0 else .74)
        cv.hair([(x + r0 * math.cos(a), dy + r0 * math.sin(a)), (x + r * .86 * math.cos(a), dy + r * .86 * math.sin(a))])
    a = math.radians(135 + 270 * temp_f / 120)
    cv.line([(x - r * .18 * math.cos(a), dy - r * .18 * math.sin(a)), (x + r * .66 * math.cos(a), dy + r * .66 * math.sin(a))])
    cv.line(_ell(x, dy, .6, .6, 6))


def mt_hood(cv, cx, base, hgt, wid):
    """Mt. Hood: snow on the summit, the lit west face ruled lightly, the east face dark."""
    pk = (cx, base - hgt)
    L = [(cx - wid / 2, base), (cx - wid * .2, base - hgt * .55), (cx - wid * .08, base - hgt * .86), pk]
    R = [pk, (cx + wid * .06, base - hgt * .9), (cx + wid * .14, base - hgt * .7), (cx + wid * .3, base - hgt * .35),
         (cx + wid / 2, base)]
    poly = L + R[1:]
    cv.obj([poly], .5)
    east = [pk] + R[1:] + [(cx + wid * .02, base), (cx - wid * .02, base - hgt * .5)]
    cv.hair(C.hatch_poly(east, 70, 1.5))
    west = L + [(cx - wid * .02, base - hgt * .5), (cx + wid * .02, base)]
    cv.hair(C.hatch_poly(west, -15, 3, inset=.5))
    # glacier ribs on the snow
    for f in (-.12, -.04, .05):
        cv.hair([(cx + wid * f * .3, base - hgt * .92), (cx + wid * f, base - hgt * .55)])


# ----------------------------------------------------------------------------------------------
# the scene in the cartouche field
# ----------------------------------------------------------------------------------------------

def garden_scene(fx, fy, fw, fh, clip_d, seed=0, big=False):
    """The garlic bed: sky with a low dry sun, Mt. Hood, cottonwood line, mounded rows of shoots in
    perspective, a cut-away soil section with cloves planted point-up and a soil thermometer."""
    rng = random.Random(seed)
    cv = C.Canvas()
    cx = fx + fw / 2
    hy = fy + fh * (.36 if not big else .34)          # horizon
    ys = fy + fh * (.66 if not big else .64)          # front cut of the bed
    yb = fy + fh + 2
    # sky: ruled, closing up toward the horizon
    cv.obj([], 0)
    y = fy - 1
    while y < hy:
        cv.hair([(fx - 3, y), (fx + fw + 3, y)])
        y += 2. if y < fy + (hy - fy) * .55 else 1.5
    # sun, low on the right: halo with rays, disc ruled on its lower half
    sr = min(fw, fh) * .055 + 2
    sx = fx + fw * (.72 + .08 * rng.random())
    sy = fy + (hy - fy) * .42
    halo = _ell(sx, sy, sr * 2., sr * 2., 40)[:-1]
    cv.obj([halo], 0)
    for i in range(32):
        a = TAU * i / 32
        r1 = sr * (2. if i % 2 else 1.6)
        cv.hair([(sx + sr * 1.25 * math.cos(a), sy + sr * 1.25 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    disc = _ell(sx, sy, sr, sr, 32)[:-1]
    cv.obj([disc], 1.)
    cv.hair([q for q in C.hatch_poly(disc, 0, 2., sy) if q[0][1] > sy - sr * .3])
    # Mt. Hood on the horizon, left of centre
    mt_hood(cv, fx + fw * .3, hy - 3, fh * .2, fw * .3)
    # cottonwood line along the horizon (Sauvie Island)
    tl = [(fx - 4, hy + 1)]
    x = fx - 4
    while x < fx + fw + 4:
        bw = rng.uniform(4, 9)
        th = rng.uniform(3, 7.5)
        for k in range(1, 6):
            tl.append((x + bw * k / 5, hy - th * math.sin(PI * k / 5) ** .6 - 1.5))
        x += bw
    tl += [(fx + fw + 4, hy + 1.5)]
    cv.obj([tl], .5)
    cv.hair(C.hatch_poly(tl, 90, 1.5))
    cv.line([(fx - 4, hy + 1), (fx + fw + 4, hy + 1)])
    # the bed: furrow floor ruled across, closing up into the distance
    vx, vy = cx + fw * .04, hy - fh * .02
    cv.obj([[(fx - 4, hy + 1.5), (fx + fw + 4, hy + 1.5), (fx + fw + 4, ys), (fx - 4, ys)]], 0)
    lines = []
    z = 1.
    while True:
        y = vy + (ys - vy) / z
        if y < hy + 2:
            break
        lines.append(y)
        z += .14
    y = lines[-1] if lines else ys
    k = 0
    for yy in lines:
        cv.hair([(fx - 4, yy), (fx + fw + 4, yy)])
    yy = (lines[-1] if lines else ys) - 1.5
    while yy > hy + 1.5:
        cv.hair([(fx - 4, yy), (fx + fw + 4, yy)])
        yy -= 1.5
    # mounded rows, back to front so the near mounds overlap; each one a white crown, ruled shadow flank
    sp = fw * .2
    rows = [cx + sp * (i - 2.5) + fw * .02 for i in range(6)]
    mw = sp * .3
    zmax = (ys - vy) / max(1., (hy + 3 - vy))
    order = sorted(rows, key=lambda r: -abs(r - vx))
    plants = []
    for xb in order:
        def at(zz, off):
            return (vx + (xb + off - vx) / zz, vy + (ys - vy) / zz)
        zs = [1 + (zmax * .5 - 1) * (i / 30) ** 1.5 for i in range(31)]
        L = [at(zz, -mw) for zz in zs]
        Rr = [at(zz, mw) for zz in zs]
        crest = [at(zz, 0) for zz in zs]
        # mound rises a little above the floor line
        Lr = [(p[0], p[1] - 2.2 / zz) for p, zz in zip(crest, zs)]
        mound = L + Lr[::-1]
        mound2 = Rr + Lr[::-1]
        cv.obj([], 0)
        cv.hair(L)
        cv.line(Rr)
        cv.hair(Lr)
        # shadow flank on the side away from the light (light from the upper left)
        dark_side = 1
        for f in (.2, .35, .5, .65, .8, .92):
            seg = []
            for zz in zs:
                p = at(zz, mw * f * dark_side)
                c = at(zz, 0)
                q = (p[0], p[1] - 2.2 / zz * (1 - f))
                if mw * (1 - f) / zz < .7 and f < .9:
                    break
                seg.append(q)
            if len(seg) > 1:
                cv.hair(seg)
        # light flank: a few cross strokes (clods)
        zz = 1.
        while zz < zmax * .7:
            p = at(zz, -mw * .7)
            q = at(zz, -mw * .2)
            cv.hair([(p[0], p[1] - .3 / zz), (q[0], q[1] - 1.6 / zz)])
            zz *= 1.12
        # plants along the crest, 18 in rows / about 6 in apart along the row
        zz = 1.08 + rng.random() * .1
        while zz < zmax * .62:
            c = at(zz, 0)
            plants.append((zz, c[0], c[1] - 2.2 / zz, rng.randrange(1 << 20)))
            zz += .32 * zz ** .9
    plants.sort(key=lambda p: -p[0])
    for zz, px, py, s in plants:
        hgt = fh * .1 / zz
        if hgt < 2.2:
            continue
        sprout(cv, px, py, hgt, 1. if hgt > 4 else .5, random.Random(s))
    # the cut-away: the soil section in front
    cv.obj([], 0)
    # strata: wavy hairlines, denser deeper
    y = ys + 3
    i = 0
    while y < yb + 2:
        pts = [(fx - 4 + fw * j / 40 * 1.05, y + .8 * math.sin(j * .9 + i * 1.7) + .5 * math.sin(j * 2.3 + i)) for j in range(41)]
        cv.hair(pts)
        y += 3. if y < ys + (yb - ys) * .4 else 2.
        i += 1
    # pebbles
    for k in range(int(fw / 14)):
        px = fx + rng.uniform(.03, .97) * fw
        py = ys + rng.uniform(.25, .95) * (yb - ys)
        r = rng.uniform(1.2, 2.6)
        pb = _ell(px, py, r * 1.3, r, 12)[:-1]
        cv.obj([pb], .5)
        cv.hair([q for q in C.hatch_poly(pb, 0, 1.5) if q[0][1] > py])
    # cloves at 2 in deep, 3 in apart, the near row; each sending a pale shoot to the surface
    depth = (yb - ys) * .5
    cs = (yb - ys) * .32
    step = fw * .135
    x = cx - step * 3
    j = 0
    while x <= cx + step * 3 + 1:
        if abs(x - (cx - step * 2)) > 1:
            base = ys + depth + cs * .5
            tilt = (rng.random() - .5) * .25
            clove(cv, x, base, cs, tilt, random.Random(j + seed))
            # shoot from the tip up through the soil and out
            tip = (x + math.sin(tilt) * cs, base - cs * math.cos(tilt))
            cv.obj([[(tip[0] - .8, tip[1]), (tip[0] - .6, ys), (tip[0] + .6, ys), (tip[0] + .8, tip[1])]], .5)
            sprout(cv, tip[0], ys, fh * .085, 1., random.Random(seed + j * 7))
        j += 1
        x += step
    # soil thermometer at 2 in, where the second clove would go
    tx = cx - step * 2
    soil_thermometer(cv, tx, ys, depth, max(4.5, fh * .045))
    # the cut edge of the bed
    cv.obj([], 0)
    cv.heavy([(fx - 4, ys), (fx + fw + 4, ys)])
    body = [C.dark_ground((fx - 4, ys, fw + 8, yb - ys + 6), "S"), cv.svg()]
    # Easter egg: a dog's paw prints trotting across the near furrow
    pp = []
    ty = ys - (ys - hy) * .1
    for i in range(4):
        z = 1.05 + i * .09
        px = fx + fw * (.2 + .18 * i) + (2 if i % 2 else -2)
        py = vy + (ys - vy) / z - (1.2 if i % 2 else 2.6)
        pp.append(paw(px, py, max(2.2, fh * .026) / z, .5 + .1 * i))
    body.append(f'<path d="{"".join(pp)}" fill="#000" stroke="none"/>')
    return _clip_d(_cid("scene", fx, fy, fw, fh), clip_d, "".join(body))


def _field(cx, cy, w, h):
    """The cartouche's field: its superellipse (same maths as C.cartouche)."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b


# ----------------------------------------------------------------------------------------------
# layouts
# ----------------------------------------------------------------------------------------------

def _flank_bulb(cv, x, ybot, a, side, seed, reach):
    """A garlic bulb standing at a plate end, leaves sweeping inward (side -1 left end) as acanthus."""
    b = a * .92
    cy = ybot - b * .78
    L = [(-28, 1.0, .9, 4.6), (-56, 1.15, .6, 5.), (-96, .8, -.3, -4.2), (-142, .6, -1.0, -4.4)]
    if side > 0:
        L = [(180 - g, l, -bb, -c) for g, l, bb, c in L]
    leaves = [(g, reach * l, bb, c) for g, l, bb, c in L]
    garlic_bulb(cv, x, cy, a, b, seed, True, True, leaves, -1)
    # loose cloves broken off at its foot
    rng = random.Random(seed)
    for k, (dx, tl) in enumerate(((-side * 1.15, -side * .5), (-side * 1.55, -side * .9))):
        clove(cv, x + dx * a, ybot + a * .25, a * (.6 - .1 * k), tl, rng)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .4, gh * 1.45)
    cx, cy = w / 2, (gy0 + gy1) / 2
    ba = min(gh * .22, 40.)
    bx = ba + 6
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    for side in (-1, 1):
        occ.append(("c", w / 2 + side * (w / 2 - bx), gy1 - ba * 1.2, ba * 1.3))
    room = (w - cw) / 2 - 2 * bx
    r = min(gh * .4, room * .5)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r * .95)
        vy = gy0 + gh * .44
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .055), rmax=r * .75,
                   max_n=11, edge=.7, cv=cv)
    cv.extend(main)
    figs = C.Canvas()
    for side in (-1, 1):
        _flank_bulb(figs, w / 2 + side * (w / 2 - bx), gy1 - ba * .38, ba, side, seed + side, gh * .48)
    cv.extend(figs)
    o.append(C._clip(_cid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, gh + 4)
    o.append(garden_scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.2, 150)
    o.append(C._clip(_cid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    # inside: a garlic bulb lying on the ruled sky over its bed, cloves either side
    fi = _ell(cx, cy, rx - 2.5, ry - 2.5, 64)[:-1]
    cv = C.Canvas()
    cv.obj([], 0)
    y = cy - ry
    while y < cy + ry:
        cv.hair([(cx - rx, y), (cx + rx, y)])
        y += 2. if y < cy + ry * .35 else 1.5
    a = min(ry * .48, 20)
    gy = cy + ry * .5
    cv.obj([], 0)
    cv.heavy([(cx - rx, gy), (cx + rx, gy)])
    for side in (-1, 1):
        for k in (1, 2):
            x = cx + side * (a * 1.5 + k * rx * .2)
            if abs(x - cx) < rx * .85:
                clove(cv, x, gy + .5, a * .9, side * .15, random.Random(k + side))
    garlic_bulb(cv, cx, gy - a * 1.08 * .78, a, a * 1.08, seed, True, True,
                [(-128, a * 1.5, -.9, -4.4), (-52, a * 1.5, .9, 4.4), (-160, a * 1.3, -.6, -4.), (-20, a * 1.3, .6, 4.)], -1)
    body = C.dark_ground((cx - rx, gy, 2 * rx, ry * 2), "S") + cv.svg()
    o.append(_clip_d(_cid("bm", w, h), _d(fi, True, 0), body))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 2.5, ry - 2.5, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
    return "".join(o)


def _layout_tall(w, h, seed):
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
    cw, ch = pw * .5, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    ba = min(pw * .075, ph * .1)
    ybulb = py0 + ph - ped_h * .3 + 2 - ba * .45
    for side in (-1, 1):
        occ.append(("c", cx + side * (cw / 2 + ba * 1.6), ybulb - ba, ba * 1.5))
    r2 = min(pw * .13, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    r1 = min(pw * .12, ph * .17)
    for side in (-1, 1):
        vx = w / 2 + side * (pw / 2 - r1 * 1.1)
        vy = py0 + ph * .62
        C._pair_unit(main, vx, vy, r1, -side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    figs = C.Canvas()
    for side in (-1, 1):
        _flank_bulb(figs, cx + side * (cw / 2 + ba * 1.6), ybulb, ba, side, seed + side, ph * .33)
    cv.extend(figs)
    o.append(C._clip(_cid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _field(cx, cy, cw, ch)
    o.append(garden_scene(cx - a, cy - b, 2 * a, 2 * b, inner, seed, True))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 56), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, face = C.ribbon_banner(cx, cy + ch * .47, cw * 1.3, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # ribbon face lettered with a running row of garlic cloves instead of words
    bc = C.Canvas()
    nn = 9
    for i in range(nn):
        p = face[int(len(face) * (i + 1) / (nn + 1))]
        clove(bc, p[0], p[1] + bh * .32, bh * .62, 0, random.Random(i))
    o.append(bc.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # tablet: a garlic braid lying along it, on a stipple ground
    o.append(C.dark_ground((tx + 2, ty + 2, tw - 3, th - 3), "S"))
    tc = C.Canvas()
    k = int(tw / (th * 1.5))
    for i in range(k):
        bx = tx + tw * (i + .5) / k
        garlic_bulb(tc, bx, ty + th * .55, th * .36, th * .33, i, False, False, None, -1)
    tc.obj([], 0)
    o.append(tc.svg())
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(_cid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = _seed(ctx)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
