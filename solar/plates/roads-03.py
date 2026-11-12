"""roads-03 "Mt. Hood today": Mount Hood reflected in Trillium Lake, engraved inside the house
acanthus frame. The ribbon is lettered MT HOOD in drawn strokes; the pedestal tablet carries the
week's falling freezing level as an engraved profile. Easter egg: Parker's dog sits on the lake
shore looking up at the mountain."""
import sys
import math
import random
import re
import engraving_codex as C

n = C._n
_DEF_FRZ = [11.1, 9.3, 5.4, 5.1, 5.1, 3.1, 2.9]
_DOG = ("M.6,0C-.4,-1.6 -.2,-4 1.4,-5.2C2.6,-6 3.6,-6.6 4.3,-7.7L4.6,-9.5C4.8,-10.5 5.9,-10.9 6.7,-10.5"
        "L7.3,-9.7L8.9,-9.3C9.6,-9.1 9.6,-8.2 8.9,-8L7.4,-7.6C6.9,-6.6 6.9,-5.3 7,-4.3L7.2,-.4L7.8,0"
        "H5.9L5.8,-3.2L4.4,-1.6L4.6,-.4L5.2,0Z")


# ---------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------

def D(pts, close=False):
    return C._d(pts, close, .15)


def path(d, fill="none", sw=None, extra=""):
    if not d:
        return ""
    s = f' stroke="#000" stroke-width="{sw}"' if sw else ' stroke="none"'
    return f'<path d="{d}" fill="{fill}"{s}{extra}/>'


def lines_d(segs):
    return "".join(D(s) for s in segs if len(s) > 1)


def clip_x(segs, x0, x1):
    out = []
    for (ax, ay), (bx, by) in segs:
        if ax > bx:
            ax, ay, bx, by = bx, by, ax, ay
        if bx < x0 or ax > x1:
            continue
        def at(x):
            return (x, ay + (by - ay) * (x - ax) / (bx - ax)) if bx != ax else (x, ay)
        p = (ax, ay) if ax >= x0 else at(x0)
        q = (bx, by) if bx <= x1 else at(x1)
        if math.hypot(q[0] - p[0], q[1] - p[1]) > .6:
            out.append([p, q])
    return out


def dashes(segs, rng, on=(4, 14), off=(1.2, 4)):
    """Break straight segments into dashes (water shimmer)."""
    out = []
    for (ax, ay), (bx, by) in segs:
        L = math.hypot(bx - ax, by - ay)
        t = rng.uniform(0, off[1])
        while t < L:
            l = rng.uniform(*on)
            t1 = min(L, t + l)
            if t1 - t > .8:
                out.append([(ax + (bx - ax) * t / L, ay + (by - ay) * t / L),
                            (ax + (bx - ax) * t1 / L, ay + (by - ay) * t1 / L)])
            t = t1 + rng.uniform(*off)
    return out


def bbox_of(d):
    """Bounding box of an absolute-M / relative-l path from C._d."""
    xs, ys = [], []
    for sub in re.findall(r"M([-\d.]+),([-\d.]+)l([^Mz]*)", d):
        x, y = float(sub[0]), float(sub[1])
        xs.append(x), ys.append(y)
        nums = [float(v) for v in re.findall(r"-?\d*\.?\d+", sub[2])]
        for i in range(0, len(nums) - 1, 2):
            x += nums[i]
            y += nums[i + 1]
            xs.append(x), ys.append(y)
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def freeze_levels(ctx):
    s = (ctx or {}).get("sample") or ""
    v = [float(m) for m in re.findall(r"freezes at ([\d.]+)k", s)]
    return v if len(v) >= 3 else _DEF_FRZ


# ---------------------------------------------------------------------------------------------
# the vignette: Mount Hood over Trillium Lake
# ---------------------------------------------------------------------------------------------

# Hood seen from the south-west: (x, height) with x in -1..1 of the half-base, summit at (0, 1).
_PROFILE = [(-1., 0), (-.86, .05), (-.7, .13), (-.55, .24), (-.42, .37), (-.32, .5), (-.25, .58),
            (-.2, .63), (-.165, .655), (-.13, .67), (-.1, .72), (-.07, .8), (-.04, .9), (-.015, .97),
            (0, 1.), (.025, .975), (.05, .93), (.075, .885), (.1, .87), (.125, .85), (.15, .8),
            (.2, .72), (.27, .62), (.36, .5), (.47, .37), (.6, .25), (.75, .14), (.88, .06), (1., 0)]
# ridges: (profile index they start from, base x they run down to)
_RIDGES = [(0, -1.), (5, -.62), (9, -.42), (12, -.22), (14, -.02), (17, .2), (20, .4), (23, .66), (28, 1.)]


def _fir(x, y, h, rng):
    """A black fir silhouette, foot at (x, y), h tall, as a polygon."""
    tiers = max(4, int(h / 3.2))
    left, right = [], []
    for i in range(tiers + 1):
        t = i / tiers
        yy = y - h + h * t * .92
        wdt = h * (.05 + .2 * t) * rng.uniform(.85, 1.1)
        left.append((x - wdt, yy + h * .05))
        left.append((x - wdt * .45, yy + h * .02))
        right.append((x + wdt, yy + h * .05))
        right.append((x + wdt * .45, yy + h * .02))
    pts = [(x, y - h)] + right + [(x + h * .03, y), (x - h * .03, y)] + left[::-1]
    return pts


def scene(x, y, w, h, seed=0, detail=1.0, frz=None, dog=True):
    """Fill the box x,y,w,h (callers clip it) with the engraved view. detail <1 for small boxes."""
    rng = random.Random(seed * 31 + 7)
    o = []
    small = h < 70
    yh = y + h * (.62 if not small else .80)        # mountain base / far shore
    sy = y + h * (.07 if not small else .12)         # summit
    cx = x + w * .53
    hw = w * .45
    mh = min(yh - sy, hw * (.62 if not small else .5))
    sy = yh - mh
    prof = [(cx + px * hw, yh - py * mh) for px, py in _PROFILE]
    summit = prof[14]

    # sky: dense rules above, opening toward the horizon
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, yh + 1), (x - 2, yh + 1)]
    sk_hi = [s for s in C.hatch_poly(sky, 0, 1.5) if s[0][1] < y + (yh - y) * .28]
    sk_lo = [s for s in C.hatch_poly(sky, 0, 3) if s[0][1] >= y + (yh - y) * .28]
    sk_mid = [s for s in C.hatch_poly(sky, 0, 3, 1.5) if y + (yh - y) * .28 <= s[0][1] < y + (yh - y) * .55]
    o.append(path(lines_d(sk_hi + sk_lo + sk_mid), sw=.5))
    # a few drifting clouds (white, shaded bellies)
    cl = []
    cl_h = []
    if not small:
        for k in range(3):
            ccx = x + w * (.12 + .3 * k + rng.uniform(-.05, .05)) + (w * .5 if k == 1 else 0) * 0
            ccy = y + (yh - y) * rng.uniform(.18, .42)
            cw_, ch_ = w * rng.uniform(.12, .2), max(4., min(9., h * .045))
            if ccy + 1 > sy - 2 and abs(ccx - cx) < hw * (1 - (yh - ccy - 2) / mh) + cw_ / 2 + 4:
                ccy = sy - 4
                if abs(ccx - cx) < cw_ / 2 + 8 or ccy - ch_ < y + 4:
                    continue
            top = [(ccx - cw_ / 2 + cw_ * i / 16, ccy - ch_ * (.35 + .65 * math.sin(math.pi * i / 16) ** .7
                    * (.75 + .25 * math.sin(i * 1.9 + k)))) for i in range(17)]
            poly = top + [(ccx + cw_ / 2, ccy), (ccx - cw_ / 2, ccy)]
            cl.append(poly)
    if not small and h > w * .75:
        # a tall field: the morning sun stands over the shoulder, rays fanning across the sky
        sx_, sy_ = x + w * .76, y + (sy - y) * .48
        sr = w * .075
        rays = []
        for i in range(36):
            a = math.tau * i / 36
            r1 = sr * (2.4 if i % 2 else 3.6)
            rays.append([(sx_ + sr * 1.25 * math.cos(a), sy_ + sr * 1.25 * math.sin(a)),
                         (sx_ + r1 * math.cos(a), sy_ + r1 * math.sin(a))])
        o.append(path(lines_d(rays), sw=.5))
        disc = C._ell_pts(sx_, sy_, sr, sr, 40)
        o.append(path(D(disc, True), "#fff", 1))
        o.append(path(lines_d([sg for sg in C.hatch_poly(disc, 0, 3, .5, inset=.8) if sg[0][1] > sy_ - sr * .1]
                              + C.hatch_poly(C._ell_pts(sx_, sy_, sr * .55, sr * .55, 24), 0, 3, 2)), sw=.5))
        cl = [c for c in cl if abs((c[0][0] + c[-2][0]) / 2 - sx_) > sr * 2 or abs(c[-1][1] - sy_) > sr * 1.6]
    for poly in cl:
        o.append(path(D(poly, True), "#fff", .5))
        cl_h += C.hatch_poly(poly, 0, 1.5, .75, inset=1)[-2:]
        cl_h += C.hatch_poly(poly, 0, 3, 0, inset=2.5)
    o.append(path(lines_d(cl_h), sw=.5))

    # the mountain
    mpoly = prof + [(prof[-1][0], yh + 1), (prof[0][0], yh + 1)]
    o.append(path(D(mpoly, True), "#fff"))
    ridges = []
    for k, (pi, bx) in enumerate(_RIDGES):
        a = prof[pi]
        b = (cx + bx * hw, yh)
        pts = []
        m = 10
        for i in range(m + 1):
            t = i / m
            px = a[0] + (b[0] - a[0]) * t
            py = a[1] + (b[1] - a[1]) * (t ** .9)
            if 0 < i < m and 0 < k < len(_RIDGES) - 1:
                px += rng.uniform(-1, 1) * hw * .018 * math.sin(math.pi * t)
            pts.append((px, py))
        ridges.append(pts)
    hair, line, cross = [], [], []
    for k in range(len(_RIDGES) - 1):
        i0, i1 = _RIDGES[k][0], _RIDGES[k + 1][0]
        face = prof[i0:i1 + 1] + ridges[k + 1][1:] + ridges[k][::-1][1:-1]
        if len(face) < 3:
            continue
        r0, r1 = ridges[k], ridges[k + 1]
        dx = (r0[-1][0] + r1[-1][0]) / 2 - (r0[0][0] + r1[0][0]) / 2
        dy = (r0[-1][1] + r1[-1][1]) / 2 - (r0[0][1] + r1[0][1]) / 2
        ang = math.degrees(math.atan2(dy, dx))
        west = (k < 4)
        tone = [3, 2, 2, 2, 1.5, 1.5, 1.5, 2][k] if k < 8 else 2
        hair += C.hatch_poly(face, ang, tone, rng.uniform(0, tone), inset=.6)
        if not west:
            cross += C.hatch_poly(face, ang + 62, 3 if k in (5, 7) else 2, .7, inset=.6)
            # gully shadow along the ridge's lee side
        else:
            if k in (2, 3):
                cross += [s for s in C.hatch_poly(face, ang - 55, 3, .3, inset=.6)
                          if (s[0][1] + s[1][1]) / 2 > yh - mh * .35]
    o.append(path(lines_d(hair + cross), sw=.5))

    # snow and glaciers on the upper mountain (only 2 in of new snow: the permanent ice and the cap)
    snow_line = sy + mh * .42
    sn = [p for p in prof if p[1] <= snow_line + 1]
    left_i = next(i for i, p in enumerate(prof) if p[1] <= snow_line)
    right_i = max(i for i, p in enumerate(prof) if p[1] <= snow_line)
    lp, rp = prof[left_i], prof[right_i]
    bottom = []
    m = 26
    for i in range(m + 1):
        t = i / m
        bx = rp[0] + (lp[0] - rp[0]) * t
        # glacier tongues reach down the gullies between ridges
        tongue = 0.
        for (pi, rx) in _RIDGES[1:-1]:
            gx = cx + (rx + .1) * hw * .55
            tongue += math.exp(-((bx - gx) / (hw * .045)) ** 2)
        by = snow_line + mh * (.14 * tongue + .03 * math.sin(i * 2.3 + seed)) - mh * .05
        bottom.append((bx, max(by, snow_line - mh * .2)))
    snow = prof[left_i:right_i + 1] + bottom
    o.append(path(D(snow, True), "#fff", .5))
    sh = dashes(C.hatch_poly(snow, -14, 3, .5, inset=1), random.Random(seed + 4), (3, 10), (2, 5))
    shade = C.hatch_poly(snow, 105, 2, .2, inset=.8)
    snow_lit = clip_x(sh, -1e9, summit[0] - .5)
    snow_dark = clip_x(shade, summit[0] + .5, 1e9)
    snow_dark += clip_x(C.hatch_poly(snow, 160, 3, 1, inset=1.5), summit[0] + hw * .08, 1e9)
    # contour drifts across the lit snow
    snow_lit += clip_x(C.hatch_poly(snow, 78, 3, .5, inset=.8), summit[0] - hw * .07, summit[0])
    # ridges continue as rock ribs through the snow
    ribs = []
    for rpts in ridges[1:-1]:
        ribs.append([p for p in rpts if p[1] <= max(q[1] for q in bottom) + 2])
    # crater rock and rock bands: dense dark islands in the ice
    rocks = []
    for (fx, fy, s) in ((.06, .2, .05), (-.16, .32, .04), (.17, .3, .035), (-.05, .36, .03), (.1, .4, .03)):
        rx_, ry_ = cx + fx * hw, sy + fy * mh
        rr = hw * s
        poly = [(rx_ + rr * math.cos(a) * rng.uniform(.6, 1.1), ry_ + rr * .55 * math.sin(a) * rng.uniform(.6, 1.1))
                for a in [i * math.tau / 9 for i in range(9)]]
        rocks.append(poly)
    o.append(path(lines_d(snow_lit + snow_dark), sw=.5))
    o.append(path(lines_d([r for r in ribs if r and r[0][0] <= summit[0] + .1]), sw=.5))
    o.append(path(lines_d([r for r in ribs if r and r[0][0] > summit[0] + .1]), sw=1))
    o.append(path(D(prof), sw=1))

    # foothills: two forested ridges with saw-tooth tree tips
    def ridge_poly(base, amp, ph_, tooth, seed2):
        r2 = random.Random(seed2)
        pts = []
        xx = x - 3
        while xx < x + w + 4:
            yy = base - amp * (.5 + .5 * math.sin((xx - x) / w * 6.3 + ph_)) * (.7 + .3 * math.sin((xx - x) / w * 17 + ph_))
            t = tooth * r2.uniform(.6, 1.3)
            pts.append((xx, yy))
            pts.append((xx + t * .5, yy - t * 1.6))
            xx += t
        return pts + [(x + w + 4, yh + h), (x - 3, yh + h)]
    far = ridge_poly(yh + 1, mh * .12, 1.2, max(2.4, h * .018), seed + 1)
    o.append(path(D(far, True), "#fff"))
    o.append(path(lines_d(C.hatch_poly(far, 0, 2, .5, inset=.3)), sw=.5))
    o.append(path(D(far[:-2]), sw=.5))
    near = ridge_poly(yh + h * .035, mh * .1, 3.6, max(3, h * .024), seed + 2)
    o.append(path(D(near, True), "#fff"))
    o.append(path(lines_d(C.hatch_poly(near, 0, 1.5, 0, inset=.3) + C.hatch_poly(near, 70, 3, .5, inset=.3)), sw=.5))
    o.append(path(D(near[:-2]), sw=.5))

    if small:
        return "".join(o)

    # Timberline Lodge on the lower south slope (tiny: steep roof, central tower)
    lx, ly = cx + hw * .22, yh - mh * .2
    ls = max(.7, min(1.3, mh / 70))
    lodge = [(lx - 7 * ls, ly), (lx - 7 * ls, ly - 2 * ls), (lx - 3 * ls, ly - 4.6 * ls), (lx - 1.2 * ls, ly - 4.6 * ls),
             (lx, ly - 7.5 * ls), (lx + 1.2 * ls, ly - 4.6 * ls), (lx + 3 * ls, ly - 4.6 * ls), (lx + 7 * ls, ly - 2 * ls),
             (lx + 7 * ls, ly)]
    o.append(path(D(lodge, True), "#fff", .5))
    o.append(path(lines_d(C.hatch_poly(lodge[1:-1], 90, 1.5, .25)), sw=.5))
    o.append(path(D([(lx - 6.5 * ls, ly - .8 * ls), (lx + 6.5 * ls, ly - .8 * ls)])
                  + D([(lx - 6 * ls, ly - 2.2 * ls), (lx - 3 * ls, ly - 3.9 * ls)])
                  + D([(lx + 6 * ls, ly - 2.2 * ls), (lx + 3 * ls, ly - 3.9 * ls)]), sw=.5))
    o.append(path(D([(lx - 7 * ls, ly), (lx + 7 * ls, ly), (lx + 7 * ls, ly - 1.4 * ls), (lx - 7 * ls, ly - 1.4 * ls)], True), "#000"))

    # Trillium Lake: ruled water, the mountain's reflection broken into shimmer
    ly0 = yh + h * .075
    ly1 = y + h * .9
    lake = [(x - 3, ly0), (x + w + 3, ly0), (x + w + 3, ly1), (x - 3, ly1)]
    o.append(path(D(lake, True), "#fff"))
    water = C.hatch_poly(lake, 0, 3, .5)
    refl = [(px, ly0 + (yh - py) * (ly1 - ly0) / mh * .95) for px, py in prof]
    refl = refl + [(refl[-1][0], ly0), (refl[0][0], ly0)]
    rd = C.hatch_poly(refl, 0, 3, 2)
    rng2 = random.Random(seed + 9)
    o.append(path(lines_d(dashes(water, rng2, (14, 40), (1.5, 4))
                          + clip_x(dashes(rd, rng2, (10, 30), (1.2, 2.5)), summit[0] - hw * .02, 1e9)
                          + clip_x(dashes(rd, rng2, (3, 9), (2, 4)), -1e9, summit[0] - hw * .02)), sw=.5))
    # shore line and reeds
    shore = [(x - 3, ly1 + 1)] + [(x + w * i / 30, ly1 + rng.uniform(-.8, .8)) for i in range(31)] + [(x + w + 3, ly1 + 1),
                                                                                                 (x + w + 3, y + h + 3), (x - 3, y + h + 3)]
    o.append(path(D(shore, True), "#fff"))
    sl = C.hatch_poly(shore, 0, 2, 1)
    o.append(path(lines_d(sl + C.hatch_poly(shore, -40, 3, 0)), sw=.5))
    o.append(path(D(shore[:-3]), sw=1))
    reeds = []
    for i in range(int(w / 3.2)):
        rx_ = x + w * rng.random()
        if x + w * .3 < rx_ < x + w * .7 and rng.random() < .7:
            continue
        rh = rng.uniform(2, 5) * h / 120
        reeds.append([(rx_, ly1 + 1), (rx_ + rng.uniform(-1, 1), ly1 - rh)])
    o.append(path(lines_d(reeds), sw=.5))

    # framing firs, black, at both sides, standing on the shore
    trees = []
    for side in (-1, 1):
        base_x = x + (w * .03 if side < 0 else w * .97)
        for j in range(5):
            tx = base_x - side * (j * w * .045 + rng.uniform(0, w * .015))
            th = min(h * .62, (ly1 - yh) * 3.2) * (1 - .14 * j) * rng.uniform(.9, 1.05)
            trees.append(_fir(tx, ly1 + 3 + j * .5, th, rng))
    o.append(path("".join(D(t, True) for t in trees), "#000"))
    # white bark nicks so the silhouettes are not mush on e-ink
    nicks = []
    for t in trees:
        tip = t[0]
        for i in range(2, len(t) // 2 - 2, 2):
            p = t[i]
            if p[0] > tip[0]:
                nicks.append([(tip[0] + .6, p[1] - 1.2), (p[0] - 1.6, p[1] - .4)])
    o.append(path(lines_d(nicks), sw=.5, extra=' stroke="#fff"').replace('stroke="#000" ', ''))

    # Easter egg: the dog on the shore, looking at the mountain
    if dog:
        dx_, dy_ = x + w * .3, ly1 + h * .045
        s = max(.75, h / 150)
        o.append(f'<path d="{_DOG}" fill="#000" transform="translate({n(dx_)},{n(dy_)}) scale({n(s * 10) if False else round(s, 2)})"/>')
    return "".join(o)


# ---------------------------------------------------------------------------------------------
# drawn lettering (no <text>): a small stroke alphabet
# ---------------------------------------------------------------------------------------------

_GL = {
    "M": [[(0, 1), (0, 0), (.42, .62), (.84, 0), (.84, 1)]],
    "T": [[(0, 0), (.72, 0)], [(.36, 0), (.36, 1)]],
    "H": [[(0, 0), (0, 1)], [(.7, 0), (.7, 1)], [(0, .5), (.7, .5)]],
    "O": [[(.38 + .38 * math.cos(a * math.tau / 20), .5 + .5 * math.sin(a * math.tau / 20)) for a in range(21)]],
    "D": [[(0, 0), (0, 1), (.3, 1)] + [(.3 + .42 * math.cos(a), .5 + .5 * math.sin(a))
                                       for a in [math.pi / 2 - math.pi * i / 12 for i in range(13)]] + [(0, 0)]],
    " ": [],
    ".": [[(.1, .9), (.1, 1)]],
}
_ADV = {"M": 1.06, "T": .9, "H": .92, "O": .98, "D": .94, " ": .6, ".": .4}


def letter_along(text, centre, cap):
    """Stroke letters centred along a polyline (the ribbon's face centre)."""
    L = [0.]
    for a, b in zip(centre, centre[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = sum(_ADV[c] for c in text) * cap
    s0 = L[-1] / 2 - total / 2

    def at(s):
        for i in range(len(L) - 1):
            if L[i + 1] >= s:
                t = (s - L[i]) / max(1e-6, L[i + 1] - L[i])
                a, b = centre[i], centre[i + 1]
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
        return centre[-1], 0.
    out = []
    s = s0
    for c in text:
        (px, py), ang = at(s + _ADV[c] * cap / 2)
        ca, sa = math.cos(ang), math.sin(ang)
        for st in _GL[c]:
            pts = []
            for gx, gy in st:
                lx, ly = (gx - (_ADV[c] - .2) / 2) * cap, (gy - .5) * cap
                pts.append((px + lx * ca - ly * sa, py + lx * sa + ly * ca))
            out.append(pts)
        s += _ADV[c] * cap
    return out


# ---------------------------------------------------------------------------------------------
# the freezing-level tablet
# ---------------------------------------------------------------------------------------------

def tablet(tx, ty, tw, th, frz):
    """Fill the pedestal's sunk tablet: a mountain range whose peaks fall day by day with the
    freezing level, each peak capped with snow below it."""
    o = []
    x0, x1 = tx + 3, tx + tw - 3
    y0, y1 = ty + 1.5, ty + th - 1
    o.append(path(D([(tx + 1, ty + 1), (tx + tw - 1, ty + 1), (tx + tw - 1, ty + th - 1), (tx + 1, ty + th - 1)], True),
                  C.pat("X")))
    hi, lo = max(frz + [11.]), 0.
    k = len(frz)
    pts = [(x0, y1)]
    for i, v in enumerate(frz):
        cx = x0 + (x1 - x0) * (i + .5) / k
        hw = (x1 - x0) / k * .62
        pk = y1 - (y1 - y0) * (v - lo) / (hi - lo)
        pts += [(cx - hw, y1 - (y1 - pk) * .25), (cx, pk), (cx + hw, y1 - (y1 - pk) * .25)]
    pts.append((x1, y1))
    o.append(path(D(pts, True), "#fff", 1))
    o.append(path(lines_d([sg for sg in C.hatch_poly(pts, 0, 2, .5, inset=.5)
                           if (sg[0][1] > y1 - (y1 - y0) * .35)]), sw=.5))
    return "".join(o)


# ---------------------------------------------------------------------------------------------
# layouts (house frame, copied so the cartouche field, ribbon and tablet can be engraved)
# ---------------------------------------------------------------------------------------------

def _field(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("rb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = C._d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(_field(C._uid("rbf", w, h, seed), fd, scene(cx - rx, cy - ry, 2 * rx, 2 * ry, seed, dog=False)))
    o.append(path(C._d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True), sw=1))
    o.append(f'<path d="M0,{n(h - .5)}h{n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.75)
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
    o.append(C._clip(C._uid("rm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bx, by, bw, bh = bbox_of(fd)
    o.append(_field(C._uid("rmf", w, h, seed), fd, scene(bx, by, bw, bh, seed, dog=bh > 80)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{n(px0 - 3.5)},{n(py0 - 3.5)}h{n(pw + 7)}v{n(ph + 7)}h{n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{n(px0 - 1.5)},{n(py0 - 1.5)}h{n(pw + 3)}v{n(ph + 3)}h{n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .52, ph * (.7 if h < 360 else .64)
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("rt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bx, by, bw, bh = bbox_of(fd)
    o.append(_field(C._uid("rtf", w, h, seed), fd, scene(bx, by, bw, bh, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .16 + top_free, 52), True, rng.randrange(1 << 20)))
    bh_ = min(18, max(14, ph * .06))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .5, cw * 1.25, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(path(lines_d(letter_along("MT HOOD", centre, bh_ * .56)), sw=1.5, extra=' stroke-linecap="square"'))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(tablet(tx, ty, tw, th, freeze_levels(ctx)))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("rf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{n(w * .06)},{n(h - 1.5)}h{n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx, .8 if h > 440 else 1.)
    return C.svg_doc(w, h, body)
