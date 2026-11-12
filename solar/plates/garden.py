"""Garden and wildlife plate: a November morning on Sauvie Island, engraved in the cartouche of the
house frame. A hazel branch with next year's catkins arches in from the left with a chickadee on it;
chanterelles and a sword fern push up from the wet bank; a great blue heron stands in the slough;
Douglas firs and Mt. Hood on the horizon, the moon in today's phase. Easter egg: a dog's paw print
pressed into the soil beside the chanterelles."""
import sys
import math
import random
import datetime
import engraving_codex as C

TAU = math.tau
_n, _d = C._n, C._d


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def ell(cx, cy, rx, ry, n=40, a0=0., a1=TAU):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def normals(P):
    out = []
    for i in range(len(P)):
        a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.
        out.append((-dy / L, dx / L))
    return out


class Rib:
    """A ribbon along a centre line with a half width per point. side(f) is the line at fraction f
    of the half width (-1 left .. +1 right of the direction of travel)."""

    def __init__(self, P, hw):
        self.P = P
        self.N = normals(P)
        self.hw = hw if isinstance(hw, list) else [hw] * len(P)

    def side(self, f, i0=0, i1=None):
        i1 = len(self.P) if i1 is None else i1
        return [(p[0] + n[0] * h * f, p[1] + n[1] * h * f) for p, n, h in
                zip(self.P[i0:i1], self.N[i0:i1], self.hw[i0:i1])]

    def poly(self):
        return self.side(-1) + self.side(1)[::-1]

    def bulino(self, cv, f0, f1, pitch=1.6, i0=0, i1=None):
        """Form lines along the ribbon between fractions f0..f1, spaced ~pitch px at the widest."""
        wmax = max(self.hw) or 1
        k = max(1, int(abs(f1 - f0) * wmax / pitch))
        for j in range(k + 1):
            f = f0 + (f1 - f0) * j / k
            cv.hair(self.side(f, i0, i1))


def taper(n, w0, w1, pw=1.):
    return [w0 + (w1 - w0) * (i / (n - 1)) ** pw for i in range(n)]


def hclip(poly, nx, ny, c):
    """Clip polygon to the half plane nx*x + ny*y <= c."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da, db = nx * a[0] + ny * a[1] - c, nx * b[0] + ny * b[1] - c
        if da <= 0:
            out.append(a)
        if (da <= 0) != (db <= 0):
            t = da / (da - db)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def hatch(cv, poly, ang, pitch, phase=0.):
    if len(poly) > 2:
        cv.hair(C.hatch_poly(poly, ang, pitch, phase))


def hlines(cv, poly, pitch=2., y_from=None, gaps=None, rng=None):
    """Horizontal hatch on the device grid (centres at k*.5+.25) clipped to poly, optionally broken."""
    ys = [p[1] for p in poly]
    y = math.floor(min(ys)) + .25
    out = []
    for seg in C.hatch_poly(poly, 0, pitch, .25):
        (x0, y0), (x1, _) = seg
        x0, x1 = min(x0, x1), max(x0, x1)
        if gaps and rng:
            x = x0
            while x < x1:
                L = rng.uniform(*gaps[0])
                out.append([(x, y0), (min(x1, x + L), y0)])
                x += L + rng.uniform(*gaps[1])
        else:
            out.append([(x0, y0), (x1, y0)])
    cv.hair(out)


# ----------------------------------------------------------------------------------------------
# the subjects
# ----------------------------------------------------------------------------------------------

def moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .26
    return (days / 29.530589) % 1.


def moon(cv, blk, cx, cy, r, phase):
    disc = ell(cx, cy, r, r, 36)
    cv.obj([disc], 1.)
    # the shadowed part: between the limb and the terminator ellipse
    k = math.cos(phase * TAU)              # 1 new .. -1 full
    waxing = phase < .5
    s = 1 if waxing else -1                 # lit side +x when waxing
    limb = [(cx - s * r * math.sin(t), cy - r * math.cos(t)) for t in [i * math.pi / 24 for i in range(25)]]
    term = [(cx + s * r * k * math.sin(t), cy + r * math.cos(t)) for t in [i * math.pi / 24 for i in range(25)]]
    shadow = limb + term
    hatch(cv, shadow, 45, 1.5)
    hatch(cv, shadow, -45, 3)
    # maria on the lit side
    cv.hair([ell(cx + r * .25, cy - r * .2, r * .22, r * .16, 12), ell(cx - r * .1, cy + r * .3, r * .18, r * .12, 12)])


def mt_hood(cv, mx, base, mh):
    pk = (mx, base - mh)
    L = [(mx - mh * 1.9, base), (mx - mh * 1.1, base - mh * .32), (mx - mh * .55, base - mh * .62),
         (mx - mh * .2, base - mh * .9), pk]
    R = [pk, (mx + mh * .12, base - mh * .93), (mx + mh * .35, base - mh * .7), (mx + mh * .8, base - mh * .42),
         (mx + mh * 1.3, base - mh * .18), (mx + mh * 2.0, base)]
    poly = L + R[1:]
    cv.obj([poly], .5)
    snow_y = base - mh * .5
    low = hclip(poly, 0, -1, -snow_y)
    hatch(cv, low, 45, 2)
    # shadowed east face of the snowfield
    east = hclip(hclip(poly, 0, 1, snow_y), -1, 0, -(mx + 1))
    hatch(cv, east, -45, 2)
    # gullies running down from the summit
    rng = random.Random(7)
    for i in range(7):
        t = (i + .5) / 7
        x0 = mx + (t - .5) * mh * .5
        y0 = base - mh * (.92 - abs(t - .5) * .3)
        x1 = mx + (t - .5) * mh * 1.9
        cv.hair([(x0, y0), ((x0 + x1) / 2 + rng.uniform(-1, 1), (y0 + snow_y) / 2), (x1, snow_y + rng.uniform(-1, 2))])


def fir(cv, x, base, h, rng, w=None):
    w = w or h * .36
    tiers = max(4, int(h / 5))
    left, right = [], []
    for i in range(tiers + 1):
        t = i / tiers
        y = base - h * .1 - (h * .9) * t
        hw = w / 2 * (1 - t) ** .95
        left.append((x - hw * rng.uniform(.95, 1.05), y))
        left.append((x - hw * .55, y - h * .9 / tiers * .45))
        right.append((x + hw * rng.uniform(.95, 1.05), y))
        right.append((x + hw * .55, y - h * .9 / tiers * .45))
    trunk = [(x - h * .03, base), (x - h * .03, base - h * .12), (x + h * .03, base - h * .12), (x + h * .03, base)]
    poly = left + [(x, base - h)] + right[::-1]
    cv.obj([trunk], .5)
    cv.obj([poly], .5)
    hatch(cv, poly, 45, 1.5)
    hatch(cv, hclip(poly, -1, 0, -(x - w * .1)), -45, 3)


def fern(cv, x, y, length, ang, curl, rng, flip=1):
    """Sword fern frond: a rachis arching from (x, y), alternating shaded pinnae."""
    P = []
    a = math.radians(ang)
    px, py = x, y
    n = 30
    for i in range(n + 1):
        P.append((px, py))
        t = i / n
        a += curl * flip * (.4 + t) / n
        px += math.cos(a) * length / n
        py += math.sin(a) * length / n
    for i in range(2, n - 1, 2):
        t = i / n
        bx, by = P[i]
        dx, dy = P[i + 1][0] - P[i - 1][0], P[i + 1][1] - P[i - 1][1]
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        pl = length * .2 * (1 - t) ** .7 + 1.5
        for s in (-1, 1):
            nx, ny = -uy * s, ux * s
            tipx, tipy = bx + nx * pl + ux * pl * .45, by + ny * pl + uy * pl * .45
            wv = pl * .2
            leaf = [(bx - ux * wv, by - uy * wv), (bx + nx * pl * .5 - ux * wv * .3 + ux * pl * .15, by + ny * pl * .5 - uy * wv * .3 + uy * pl * .15),
                    (tipx, tipy),
                    (bx + nx * pl * .5 + ux * wv * 1.8 + ux * pl * .2, by + ny * pl * .5 + uy * wv * 1.8 + uy * pl * .2),
                    (bx + ux * wv * 1.6, by + uy * wv * 1.6)]
            cv.obj([leaf], .5)
            cv.hair([(bx + ux * wv * .3, by + uy * wv * .3), tipx_mid(bx, by, tipx, tipy)])
            if s > 0:
                hatch(cv, leaf, 45, 1.5)
    R = Rib(P, taper(len(P), 1.1, .3))
    cv.obj([R.poly()], .5)


def tipx_mid(bx, by, tx, ty):
    return (bx + (tx - bx) * .85, by + (ty - by) * .85)


def chanterelle(cv, blk, x, y, s, lean=0., rng=None, light=-1):
    """A golden chanterelle s px tall standing at (x, y): a stem flaring into a wavy, rolled-edge
    funnel cap, forking false gills running down the stem, shaded away from the light."""
    rng = rng or random.Random(1)
    rcx, rcy = x + lean * s, y - .78 * s
    rx, ry = .46 * s, .17 * s
    wav = [rng.uniform(0, TAU) for _ in range(4)]

    def rim(t, sc=1.):
        k = 1 + .06 * math.sin(4 * t + wav[0]) + .03 * math.sin(7 * t + wav[1])
        return (rcx + rx * sc * k * math.cos(t),
                rcy + ry * sc * k * math.sin(t) + .03 * s * sc * math.sin(5 * t + wav[2]))

    front = [rim(i * math.pi / 40) for i in range(41)]
    Lp, Rp = rim(math.pi), rim(0)
    sw = .075 * s
    sx = x + lean * s * .25
    left = bez(Lp, (rcx - rx * .45, rcy + .16 * s), (sx - sw * 1.1, y - .42 * s), (x - sw * 1.2, y), 16)
    right = bez((x + sw * 1.2, y), (sx + sw * 1.1, y - .42 * s), (rcx + rx * .45, rcy + .16 * s), Rp, 16)
    base = [(x + sw * 1.2 * math.cos(math.pi - a), y + sw * .5 * math.sin(a)) for a in [i * math.pi / 8 for i in range(1, 8)]]
    body = left + base + right + front
    cv.obj([body], 1.)
    # false gills: blunt ridges forking from the rim and running down into the stem
    ng = max(10, int(s * .55))
    for i in range(1, ng):
        t = i * math.pi / ng
        p = rim(t)
        f = math.cos(t)
        q = (sx + f * sw * .9, y - (.36 + .1 * (1 - abs(f)) + .05 * math.sin(i * 2.3)) * s)
        m = (p[0] * .5 + q[0] * .5 + f * s * .05, p[1] * .35 + q[1] * .65)
        g = bez(p, m, (q[0] * .7 + m[0] * .3, q[1] * .7 + m[1] * .3), q, 10)
        cv.hair(g)
        if i % 2 == 0 and s > 18:
            p2 = rim(t + math.pi / ng * .5)
            cv.hair(bez(p2, (p2[0] * .7 + m[0] * .3, p2[1] * .7 + m[1] * .3), m, m, 6))
    # shadow: doubled gills on the far flank, a black crescent tucked under the rim
    for i in range(ng):
        t = (i + .5) * math.pi / ng
        f = math.cos(t)
        if f * light > -.15:
            continue
        p = rim(t)
        if i % 2:
            continue
        q = (sx + f * sw * .9, y - (.4 + .1 * (1 - abs(f))) * s)
        m = (p[0] * .5 + q[0] * .5 + f * s * .05, p[1] * .35 + q[1] * .65)
        cv.hair(bez(p, m, (q[0] * .7 + m[0] * .3, q[1] * .7 + m[1] * .3), q, 10))
    under = [rim(t) for t in [i * math.pi / 20 for i in range(0, 9)]] if light < 0 else \
            [rim(t) for t in [i * math.pi / 20 for i in range(12, 21)]]
    under2 = [(px + (rcx - px) * .08, py + .05 * s) for px, py in under[::-1]]
    blk.append(under + under2)
    for f in (.3, .55, .8):
        cv.hair(bez((x - light * sw * f, y - .02 * s), (sx - light * sw * f, y - .2 * s),
                    (sx - light * sw * f * 1.1, y - .32 * s), (sx - light * sw * f * 1.4, y - .42 * s), 8))
    hatch(cv, hclip(hclip(body, 0, -1, -(y - .3 * s)), light, 0, light * (x + light * sw * .2)), 45, 2)
    # cap: rolled edge, sunken centre shaded on its near wall
    cap = [rim(i * TAU / 72) for i in range(72)]
    cv.obj([cap], 1.)
    cv.hair([rim(i * TAU / 72, .9) for i in range(37)])          # rolled rim, back half
    for sc in (.72, .55, .38):
        cv.hair([rim(math.pi + i * math.pi / 24, sc) for i in range(25)])
    inner = [rim(i * TAU / 48, .72) for i in range(48)]
    hatch(cv, hclip(inner, 0, -1, -(rcy - ry * .15)), 45, 1.5)
    hatch(cv, hclip(inner, -light, 0, -light * rcx), -45, 3)
    # light radial streaks on the far wall
    for i in range(5):
        t = math.pi + (i + 1) * math.pi / 6
        a, b2 = rim(t, .72), rim(t, .95)
        cv.hair([a, b2])


def heron(cv, blk, x, y, H, flip=-1):
    """Great blue heron at rest, standing at (x, y) feet, H px tall, facing left (flip -1)."""
    def T(u, v):
        return (x - flip * -1 * u * H if False else x + u * H * -flip * -1, y - v * H)

    def P(u, v):
        return (x + u * H * (-flip), y - v * H) if flip > 0 else (x + u * H, y - v * H)

    # legs
    for (u0, u1) in ((.0, .05), (.11, .08)):
        cv.obj([], 0)
        cv.line([P(u0, 0), P((u0 + u1) / 2 - .01, .2), P(u1, .38)])
        cv.hair([P(u0 - .06, 0), P(u0, 0), P(u0 + .05, .005)])
    body = [P(-.06, .70), P(.10, .68), P(.24, .60), P(.36, .47), P(.30, .43), P(.18, .40), P(.04, .37),
            P(-.08, .42), P(-.13, .52), P(-.12, .63)]
    body = smooth_closed(body, 4)
    neck_c = [P(-.06, .62), P(-.16, .68), P(-.17, .76), P(-.08, .82), P(-.05, .88), P(-.10, .94)]
    neck_c = catmull(neck_c, 6)
    neck = Rib(neck_c, taper(len(neck_c), .075 * H, .035 * H))
    cv.obj([neck.poly()], 1.)
    neck.bulino(cv, .35, 1., 1.5)
    # neck streak (black dashes down the front)
    for i in range(4, len(neck_c) - 6, 5):
        p, nn = neck_c[i], neck.N[i]
        hw = neck.hw[i]
        cv.line([(p[0] - nn[0] * hw * .5, p[1] - nn[1] * hw * .5), (neck_c[i + 1][0] - nn[0] * hw * .5, neck_c[i + 1][1] - nn[1] * hw * .5)])
    cv.obj([body], 1.)
    hatch(cv, hclip(body, 0, -1, -(y - .6 * H)), 30, 2)
    lower = hclip(body, 0, -1, -(y - .47 * H))
    hatch(cv, lower, 120, 3)
    # wing coverts: scalloped rows
    for r in range(3):
        row = []
        for i in range(6):
            u = .2 - i * .045 + r * .03
            v = .58 - r * .06 - i * .006
            row.append([P(u, v), P(u - .022, v - .03), P(u - .045, v)])
        cv.hair(row)
    # plumes over the tail and the breast
    for i in range(7):
        cv.hair([P(.22 + i * .02, .46), P(.38 + i * .012, .36 - i * .01)])
    for i in range(6):
        cv.hair([P(-.12 + i * .012, .58), P(-.14 + i * .016, .38 - i * .012)])
    # head and bill
    hx, hy = neck_c[-1]
    head = ell(hx, hy, .055 * H, .042 * H, 20)
    cv.obj([head], 1.)
    tip = P(-.36, .915)
    bill = [P(-.13, .935), tip, P(-.13, .905)]
    cv.obj([bill], .5)
    cv.hair([P(-.13, .92), P(-.33, .916)])
    hatch(cv, bill, 45, 1.5)
    hatch(cv, hclip(head, 0, -1, -(hy + .01 * H)), 45, 2)
    # black crown stripe and plume
    blk.append([P(-.08, .955), P(.0, .975), P(.09, .965), P(.0, .955), P(-.05, .945)])
    blk.append(ell(*P(-.085, .93), .009 * H, .009 * H, 8))
    return P


def catmull(pts, n=6):
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(pts[-1])
    return out


def smooth_closed(pts, n=5):
    m = len(pts)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    return out


def catkin(cv, x, y, L, sway, rng):
    """A hazel catkin: a slender pendulous tassel of scales, curving as it hangs."""
    P = bez((x, y), (x + sway * .2, y + L * .35), (x + sway * 1.3, y + L * .6), (x + sway * .9, y + L), 16)
    hw = taper(len(P), max(.6, L * .03), max(1.1, min(2., L * .06)), .5)
    hw[-1] *= .5
    R = Rib(P, hw)
    cv.obj([R.poly()], .5)
    for i in range(2, len(P) - 1, 2):
        p, nn = P[i], R.N[i]
        h = R.hw[i]
        q = P[i + 1]
        cv.hair([(p[0] - nn[0] * h, p[1] - nn[1] * h), (q[0], q[1]), (p[0] + nn[0] * h, p[1] + nn[1] * h)])
    cv.hair(R.side(.55, 3))


def hazel_leaf(cv, x, y, L, ang, rng):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    pts = []
    for i in range(25):
        t = i / 24 * math.pi
        r = math.sin(t) ** .8 * (1 - .25 * (i / 24)) * L * .38
        tooth = .06 * L * (i % 2)
        u = (1 - math.cos(t)) / 2 * L
        pts.append((x + ux * u + nx * (r + tooth * .5), y + uy * u + ny * (r + tooth * .5)))
    for i in range(24, -1, -1):
        t = i / 24 * math.pi
        r = math.sin(t) ** .8 * (1 - .25 * (i / 24)) * L * .38
        tooth = .06 * L * (i % 2)
        u = (1 - math.cos(t)) / 2 * L
        pts.append((x + ux * u - nx * (r + tooth * .5), y + uy * u - ny * (r + tooth * .5)))
    cv.obj([pts], .5)
    cv.line([(x, y), (x + ux * L, y + uy * L)])
    for i in range(1, 6):
        u = L * i / 6.5
        for s in (-1, 1):
            cv.hair([(x + ux * u, y + uy * u), (x + ux * (u + L * .16) + nx * s * L * .3, y + uy * (u + L * .16) + ny * s * L * .3)])
    hatch(cv, hclip(pts, -nx, -ny, -(nx * x + ny * y)), 45, 2)


def chickadee(cv, blk, x, y, s, face=1):
    """Black-capped chickadee perched at (x, y) (feet), s px tall, facing +x if face=1."""
    def P(u, v):
        return (x + face * u * s, y - v * s)
    tail = [P(-.25, .35), P(-.75, .05), P(-.68, -.02), P(-.18, .25)]
    cv.obj([tail], .5)
    hatch(cv, tail, 45, 1.5)
    body = smooth_closed([P(-.32, .45), P(-.05, .75), P(.25, .72), P(.38, .5), P(.25, .18), P(-.05, .12)], 5)
    cv.obj([body], 1.)
    belly = hclip(body, 0, -1, -(y - .38 * s))
    hatch(cv, belly, -45, 3)
    wing = smooth_closed([P(-.30, .48), P(-.02, .62), P(.18, .52), P(.02, .34), P(-.4, .3)], 4)
    cv.obj([wing], .5)
    hatch(cv, wing, 45, 1.5)
    cv.hair([[P(-.28, .42), P(.1, .5)], [P(-.32, .37), P(.05, .43)]])
    head = ell(*P(.32, .8), .24 * s, .23 * s, 24)
    cv.obj([head], 1.)
    # black cap and bib
    hx, hy = P(.32, .8)
    blk.append([P(.12, .82), P(.18, .98), P(.38, 1.03), P(.56, .9), P(.5, .82), P(.3, .86)])
    blk.append([P(.4, .66), P(.52, .74), P(.48, .6), P(.36, .55)])
    blk.append(ell(*P(.42, .84), .035 * s, .035 * s, 6))
    cv.obj([[P(.54, .82), P(.72, .78), P(.54, .74)]], .5)
    cv.line([P(-.02, .14), P(.0, -.02)])
    cv.line([P(.12, .14), P(.14, -.02)])


def paw(blk, x, y, s):
    """A dog's paw print pressed into the soil."""
    blk.append(smooth_closed([(x - s * .45, y + s * .1), (x, y - s * .25), (x + s * .45, y + s * .1), (x, y + s * .45)], 4))
    for dx, dy in ((-.62, -.42), (-.22, -.78), (.22, -.78), (.62, -.42)):
        blk.append(ell(x + dx * s, y + dy * s, s * .17, s * .22, 10))


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def scene(fx, fy, fw, fh, clip_d, cid, date, seed, mode="full"):
    """Engrave the Sauvie Island morning into the box, clipped to clip_d."""
    rng = random.Random(seed)
    cv = C.Canvas()
    blk = []
    S = min(fh, fw * .55)                 # subject scale
    wide = mode == "full" and fw > fh * 2.1
    hor = fy + fh * (.5 if mode == "full" else .55)
    # sky: horizontal rules, closer overhead
    sky = [(fx, fy), (fx + fw, fy), (fx + fw, hor + 2), (fx, hor + 2)]
    cv.obj([sky], 0)
    band = [(fx, fy), (fx + fw, fy), (fx + fw, fy + (hor - fy) * .45), (fx, fy + (hor - fy) * .45)]
    hlines(cv, band, 1.5)
    hlines(cv, [(fx, fy + (hor - fy) * .45), (fx + fw, fy + (hor - fy) * .45), (fx + fw, hor + 2), (fx, hor + 2)], 2)
    # moon, today's phase
    if mode == "full":
        mr = max(4.5, S * .07)
        mxm = fx + fw * (.2 if wide else .66)
        moon(cv, blk, mxm, fy + (hor - fy) * (.45 if wide else .38), mr, moon_phase(date))
        # a skein of geese crossing
        gx, gy = mxm + fw * (.12 if wide else .16), fy + (hor - fy) * .3
        for i in range(5):
            bx, by = gx - i * S * .045, gy + abs(i - 1.5) * S * .025
            cv.obj([], 0)
            cv.line([(bx - S * .018, by - S * .008), (bx, by), (bx + S * .018, by - S * .008)])
    # Mt. Hood far east
    mh = (hor - fy) * .55
    mt_hood(cv, fx + fw * (.56 if mode == "full" else .7), hor, mh)
    # far bank of the island: low fields and a fir line
    bank = [(fx, hor - 2), (fx + fw, hor - 1), (fx + fw, hor + 3), (fx, hor + 3)]
    cv.obj([bank], .5)
    hatch(cv, bank, 45, 1.5)
    tx = fx - 2
    mxc = fx + fw * (.56 if mode == "full" else .7)
    trees = []
    while tx < fx + fw + 4:
        gapm = abs(tx - mxc) < mh * (1.05 if mode == "full" else .9)
        th = (rng.uniform(.05, .08) if gapm else (.08 + .1 * (.5 + .5 * math.sin(tx * .09 + seed))) * rng.uniform(.75, 1.25)) * S
        trees.append((tx, th))
        tx += th * rng.uniform(.2, .32) * (1.6 if gapm else 1)
    trees.sort(key=lambda t: -t[1])
    for tx, th in trees:
        fir(cv, tx, hor + 1, th, rng)
    # slough water from the horizon to the foreground
    water = [(fx, hor + 2), (fx + fw, hor + 2), (fx + fw, fy + fh), (fx, fy + fh)]
    cv.obj([water], 0)
    hlines(cv, water, 2, gaps=((14, 60), (1.5, 3.5)), rng=rng)
    near = [(fx, hor + (fy + fh - hor) * .7), (fx + fw, hor + (fy + fh - hor) * .7), (fx + fw, fy + fh), (fx, fy + fh)]
    hatch(cv, near, 45, 3)
    if mode == "full":
        # cattails along the far edge of the slough
        for i in range(14):
            cx_ = fx + fw * (.66 + i * .022) + rng.uniform(-2, 2)
            ch = S * rng.uniform(.1, .2)
            cv.obj([], 0)
            cv.hair([(cx_, hor + 6), (cx_ + rng.uniform(-1, 1), hor + 6 - ch)])
            if i % 3 == 0:
                cv.obj([ell(cx_, hor + 6 - ch * .85, 1.1, ch * .14, 10)], .5)
                hatch(cv, ell(cx_, hor + 6 - ch * .85, 1.1, ch * .14, 10), 45, 1.5)
        # heron
        hH = S * (.74 if wide else .62)
        hx, hy = fx + fw * (.79 if wide else .8), hor + (fy + fh - hor) * (.8 if wide else .72)
        # reflection
        cv.obj([], 0)
        for i in range(6):
            yy = math.floor(hy + 2 + i * 2) + .25
            cv.hair([(hx - hH * .05 + rng.uniform(-1, 1), yy), (hx + hH * .18 + rng.uniform(-1, 1), yy)])
        heron(cv, blk, hx, hy, hH)
        # rushes in front of his legs
        for i in range(7):
            rx_ = hx + (i - 3) * S * .05 + rng.uniform(-1, 1)
            cv.obj([], 0)
            cv.hair(bez((rx_, hy + 3), (rx_, hy - S * .06), (rx_ + 2, hy - S * .1), (rx_ + 4 * (1 if i % 2 else -1), hy - S * .14), 6))
    # foreground bank, rising from the left
    gb = fy + fh
    bank_top = []
    nb = 30
    for i in range(nb + 1):
        t = i / nb
        if wide:
            xx = fx + fw * .6 * t
            lift = fh * .2 * (1 - t ** 3)
        elif mode == "full":
            xx = fx + fw * .68 * t
            lift = fh * .34 * (1 - t ** 2)
        else:
            xx = fx + fw * t
            lift = fh * .3 * (1 - .5 * abs(2 * t - 1) ** 2)
        bank_top.append((xx, gb - lift - 1.5 * math.sin(t * 17 + seed % 5)))
    ex = fx + fw * (.66 if wide else .74)
    if mode == "full":
        bank_top.append((ex, gb + 2))
    fg = bank_top + [(fx + fw if mode != "full" else ex, gb + 4), (fx, gb + 4)]
    cv.obj([fg], 1.)
    # soil: contour strata following the bank, cross-hatched in the shadow
    for k in range(1, 30):
        off = k * 2.
        line = [(p[0], p[1] + off + .6 * math.sin(p[0] * .15 + k)) for p in bank_top]
        cv.hair([q for q in line if q[1] < gb + 2])
    hatch(cv, hclip(fg, 0, -1, -(gb - fh * .14)), 45, 3)
    # grass tufts along the bank edge
    for i in range(0, len(bank_top) - 1):
        bx, by = bank_top[i]
        for j in range(3):
            hgt = S * rng.uniform(.04, .09)
            lean = rng.uniform(-.6, .6)
            cv.hair(bez((bx + j * 1.5, by + 1), (bx + j * 1.5, by - hgt * .5), (bx + j * 1.5 + lean * hgt * .3, by - hgt * .8),
                        (bx + j * 1.5 + lean * hgt, by - hgt), 5))
    # chanterelle cluster, a sword fern behind it
    if mode == "full":
        if wide:
            S = fh * 1.05
            mx, my = fx + fw * .33, gb - fh * .2
        else:
            mx, my = fx + fw * .30, gb - fh * .14
        fern(cv, mx - S * .05, my - S * .02, S * .55, -105, 1.4, rng, 1)
        fern(cv, mx + S * .04, my, S * .45, -70, -1.1, rng, 1)
        fallen = [(mx + S * .35, my + S * .02, S * .14, -20), (mx - S * .42, my + S * .06, S * .12, 200)]
        for lx, ly, ll, la in fallen:
            hazel_leaf(cv, lx, ly, ll, la, rng)
        chanterelle(cv, blk, mx - S * .14, my + S * .03, S * .36, -.12, random.Random(seed + 1))
        chanterelle(cv, blk, mx + S * .12, my + S * .05, S * .3, .15, random.Random(seed + 2))
        chanterelle(cv, blk, mx, my + S * .09, S * .46, .02, random.Random(seed + 3))
        chanterelle(cv, blk, mx + S * .25, my + S * .1, S * .16, .1, random.Random(seed + 4))
        # Easter egg: Parker's dog was here
        paw(blk, mx + S * .52, my + S * .12, S * .045)
        paw(blk, mx + S * .62, my + S * .07, S * .045)
        # the hazel branch, catkins already formed for spring
    if mode == "full" and not wide:
        bx0, by0 = fx - 4, fy + fh * .34
        P = bez((bx0, by0), (fx + fw * .12, fy + fh * .2), (fx + fw * .28, fy + fh * .2), (fx + fw * .44, fy + fh * .3), 30)
        br = Rib(P, taper(len(P), S * .03, S * .009))
        twig = bez(P[12], (P[12][0] + S * .04, P[12][1] - S * .08), (P[12][0] + S * .1, P[12][1] - S * .1),
                   (P[12][0] + S * .17, P[12][1] - S * .12), 12)
        tw = Rib(twig, taper(len(twig), S * .012, S * .005))
        cv.obj([tw.poly()], .5)
        tw.bulino(cv, .2, 1, 1.5)
        cv.obj([br.poly()], 1.)
        br.bulino(cv, .0, 1., 1.5)
        for i in range(3, len(P) - 2, 4):
            p, nn = P[i], br.N[i]
            cv.hair([(p[0] + nn[0] * br.hw[i] * -.7, p[1] + nn[1] * br.hw[i] * -.7), (P[i + 1][0], P[i + 1][1])])
        for i in (5, 9, 16, 23, 28):
            for j in range(1 + (i % 2)):
                catkin(cv, P[i][0] + j * 2.5, P[i][1] + br.hw[i] * .5, S * rng.uniform(.14, .2),
                       S * rng.uniform(-.04, .04) + (j - 1) * S * .025, rng)
        for j in range(2):
            catkin(cv, twig[-1][0] + j * 1.8, twig[-1][1], S * .15, 3 + j * 3, rng)
        hazel_leaf(cv, P[-1][0], P[-1][1], S * .15, 55, rng)
        hazel_leaf(cv, twig[6][0], twig[6][1], S * .12, -100, rng)
        chickadee(cv, blk, P[19][0], P[19][1] - br.hw[19] * .5, S * .15, 1)
    if mode != "full":
        mx, my = fx + fw * .36, gb - fh * .1
        fern(cv, mx - S * .1, my, S * .5, -110, 1.3, rng, 1)
        chanterelle(cv, blk, mx - S * .18, my + S * .02, S * .42, -.12, random.Random(seed + 1))
        chanterelle(cv, blk, mx + S * .16, my + S * .05, S * .36, .14, random.Random(seed + 2))
        chanterelle(cv, blk, mx, my + S * .08, S * .55, .02, random.Random(seed + 3))
        paw(blk, mx + S * .52, my + S * .02, S * .06)
    body = cv.svg()
    bd = "".join(_d(p, True, .15) for p in blk)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">'
            f'{body}<path d="{bd}" fill="#000" stroke="none"/></g>')


# ----------------------------------------------------------------------------------------------
# layouts (house frame, with a wider cartouche so the scene has room)
# ----------------------------------------------------------------------------------------------

def _field(cx, cy, w, h, inset=5.5):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    pts = C._superellipse(cx, cy, a - inset, b - inset)
    return pts, (cx - a, cy - b, 2 * a, 2 * b)


def layout_band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.6, 190)
    o.append(C._clip(C._uid("gb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip = ell(cx, cy, rx - 4.5, ry - 4.5, 64)
    o.append(scene(cx - rx, cy - ry, 2 * rx, 2 * ry, _d(clip, True, 0), C._uid("gs", w, h, seed), date, seed, "mini"))
    o.append(f'<path d="{_d(ell(cx, cy, rx - 4.5, ry - 4.5, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .56, gh * 3.0)
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
    o.append(C._clip(C._uid("gm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    pts, (fx, fy, fw, fh) = _field(cx, cy, cw, ch)
    o.append(scene(fx, fy, fw, fh, _d(pts, True, 0), C._uid("gsm", w, h, seed), date, seed))
    o.append(f'<path d="{_d(pts, True, .1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, date):
    rng = random.Random(seed)
    o = []
    density = .8
    ped_h = min(max(h * .17, 48), 86.)
    frieze = 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .62, ph * .66
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .15, ph * .22)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .45)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .19)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .45)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("gt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    pts, (fx, fy, fw, fh) = _field(cx, cy, cw, ch)
    o.append(scene(fx, fy, fw, fh, _d(pts, True, 0), C._uid("gst", w, h, seed), date, seed))
    o.append(f'<path d="{_d(pts, True, .1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, face = C.ribbon_banner(cx, cy + ch * .5, cw * 1.15, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    if face and len(face) > 2:
        fr = Rib(list(face), bh * .36)
        o.append(C.dark_ground(fr.poly(), "L"))
    py = h - ped_h
    p, (tx, ty, tw_, th_) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(C.dark_ground((tx + 1.5, ty + 1.5, tw_ - 3, th_ - 3), "M"))
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 11
    if h < 110:
        body = layout_band(w, h, seed, date)
    elif h <= 260:
        body = layout_medium(w, h, seed, date)
    else:
        body = layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
