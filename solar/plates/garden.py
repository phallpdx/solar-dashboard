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

def _crown(cv, rng, cx, cy, rx, ry, q, tone=1.):
    """One rounded crown of the hedge, cut in the burin manner: the outline broken into leaf
    clusters, small leaf flicks laid thicker on the shadow side (light from the upper left), and
    a ruled shade under the right-hand belly."""
    pts = []
    n = max(18, int((rx + ry) * .5))
    for i in range(n):
        a = TAU * i / n
        k = 1 + .09 * math.sin(a * 7 + rx) + .05 * math.sin(a * 13 + ry)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    cv.obj([pts], .5)
    sh = [(cx + rx * .2 + (x - cx) * .78, cy + ry * .22 + (y - cy) * .78) for x, y in pts]
    hatch(cv, sh, 35, 2.4 * q / tone)
    hatch(cv, [(cx + rx * .32 + (x - cx) * .5, cy + ry * .38 + (y - cy) * .5) for x, y in pts], -40, 2.4 * q)
    m = int(rx * ry / (14. * q * q))
    for _ in range(m):
        a = rng.uniform(0, TAU)
        r = math.sqrt(rng.random())
        x, y = cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)
        lit = (x - cx) / rx * -.6 + (y - cy) / ry * -.8
        if lit > .45 and rng.random() < .75:
            continue
        L = rng.uniform(1.2, 2.2) * q
        b = rng.uniform(-.8, .8) + (.4 if x > cx else -.4)
        cv.hair([(x - L * math.cos(b), y - L * math.sin(b) * .5), (x, y + L * .35), (x + L * math.cos(b), y - L * math.sin(b) * .5)])


def _stool(cv, rng, bx, by, H, S):
    """A coppiced hazel stool: a fan of straight rods from one knuckled base, forked toward the
    tips and hung with this year's catkins; two late yellow leaves cling on."""
    tips = []
    nrod = 6
    for i in range(nrod):
        u = (i - (nrod - 1) / 2) / ((nrod - 1) / 2)
        a = -math.pi / 2 + u * .38 + rng.uniform(-.05, .05)
        L = H * rng.uniform(.78, 1.) * (1 - .12 * abs(u))
        x0 = bx + u * S * .03
        bend = u * .55 + rng.uniform(-.1, .1)
        P = []
        for j in range(21):
            t = j / 20
            aa = a + bend * t * t
            P.append((x0 + L * t * math.cos(a) + L * .35 * t * t * (math.cos(aa) - math.cos(a)), by + L * t * math.sin(a) + L * .35 * t * t * (math.sin(aa) - math.sin(a))))
        R = Rib(P, taper(len(P), max(1.2, S * .014), .45, .8))
        cv.obj([R.poly()], .5)
        cv.hair(R.side(.45))
        for j in range(3, 17, 4):
            cv.hair([R.side(.6)[j], R.side(.95)[j]])
        tips.append((P, a, L))
        fk = int(len(P) * rng.uniform(.55, .7))
        fa = a + bend * .5 + rng.choice((-1, 1)) * rng.uniform(.35, .55)
        F = [(P[fk][0] + math.cos(fa) * L * .22 * t, P[fk][1] + math.sin(fa) * L * .22 * t) for t in [j / 8 for j in range(9)]]
        cv.obj([], 0)
        cv.hair(F)
        for (x, y) in (F[-1], P[-1]):
            for k in range(rng.choice((1, 2, 2))):
                catkin(cv, x + k * 1.6 - .8, y + 1, S * rng.uniform(.05, .075), rng.uniform(-1.5, 2), rng)
    base = ell(bx, by, S * .07, S * .025, 20)
    cv.obj([base], 1.)
    hatch(cv, base, 20, 1.5)
    for P, a, L in tips[1::3]:
        hazel_leaf(cv, P[12][0], P[12][1], S * .085, math.degrees(a) + 70, rng)
    return tips


def hedge_scene(fx, fy, fw, fh, clip_d, cid, date, seed):
    """The food-forest hedge, close to: elder, serviceberry and dogwood crowns massed behind, three
    coppiced hazel stools in front, their bare rods hung with November's catkins, a chickadee on a
    rod, the leaf litter at the foot, and the dog's paw print pressed into the soil."""
    rng = random.Random(seed)
    cv = C.Canvas()
    blk = []
    S = min(fh, fw * .5)
    q = max(1., fh / 210.) ** .7
    gb = fy + fh * .86                    # the soil line
    # the sky, pale and lightly ruled where it shows between the crowns
    sky = [(fx, fy), (fx + fw, fy), (fx + fw, gb), (fx, gb)]
    cv.obj([sky], 0)
    hatch(cv, sky, 0, 3.2 * q)
    # back crowns, then front crowns, down to the soil
    rows = ((.2, .17, .9), (.42, .19, 1.1), (.62, .2, 1.3))
    for yf, rf, tone in rows:
        x = fx - fw * .02
        while x < fx + fw * 1.02:
            rx = fh * rf * rng.uniform(.85, 1.25)
            ry = rx * rng.uniform(.62, .8)
            _crown(cv, rng, x + rx * .8, fy + fh * yf + rng.uniform(-.05, .05) * fh, rx, ry, q, tone)
            x += rx * rng.uniform(1.25, 1.6)
    # soil and leaf litter
    soil = [(fx - 2, gb), (fx + fw + 2, gb), (fx + fw + 2, fy + fh + 2), (fx - 2, fy + fh + 2)]
    cv.obj([soil], 1.)
    hatch(cv, soil, 0, 1.6 * q)
    for _ in range(int(fw / 7)):
        x, y = fx + rng.uniform(0, fw), gb + rng.uniform(1, fh * .12)
        lf = ell(x, y, rng.uniform(1.8, 3.2), rng.uniform(.9, 1.5), 10)[:-1]
        cv.obj([lf], .5)
    # the three hazel stools
    tips = []
    for xf, hf in ((.2, .72), (.52, .82), (.82, .7)):
        tips += _stool(cv, rng, fx + fw * xf, gb + 1, fh * hf, S)
    # a chickadee on a rod of the middle stool
    P, a, L = tips[9]
    chickadee(cv, blk, P[11][0] + 1, P[11][1], S * .11, 1)
    # Easter egg: the dog's paw print in the soil at the right
    paw(blk, fx + fw * .66, gb + fh * .07, S * .035)
    paw(blk, fx + fw * .7, gb + fh * .1, S * .035)
    body = cv.svg()
    bd = "".join(_d(p, True, .15) for p in blk)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">'
            f'{body}<path d="{bd}" fill="#000" stroke="none"/></g>')


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
    _mr = max(4.5, S * .07)
    _mx = fx + fw * (.2 if wide else .66)
    _my = fy + (hor - fy) * (.45 if wide else .38)
    _sk, _ = st_sky(fx, fy, fx + fw, hor + 2, seed + 3,
                    avoid=(lambda x, y: math.hypot(x - _mx, y - _my) < _mr + 4) if mode == "full" else None, top_dark=.25)
    cv.hair(_sk)
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


def _catkin(cv, x, y, L, ang, rng):
    """A hazel catkin: a pendulous tassel of overlapping scales on a curving thread."""
    pts = []
    a = ang
    px, py = x, y
    n = max(5, int(L / 1.6))
    for j in range(n + 1):
        pts.append((px, py))
        a += rng.uniform(-.05, .09)
        px += math.cos(a) * L / n
        py += math.sin(a) * L / n
    for j, (qx, qy) in enumerate(pts[1:], 1):
        t = j / n
        r = max(.9, L * .09 * math.sin(math.pi * min(1, .25 + t)) )
        cv.obj([[(qx + r * math.cos(k * math.tau / 10), qy + r * .75 * math.sin(k * math.tau / 10)) for k in range(10)]], .5)
        if j % 2:
            cv.hair([(qx + r * .1, qy - r * .2), (qx + r * .7, qy + r * .3)])


def _hazel(fld, seed):
    """The food-forest hedge: bare hazel twigs reaching in over the scene from both sides, hung
    with this month's catkins, and the hedge's low, dark mass across the near corners."""
    xs = [q[0] for q in fld]
    ys = [q[1] for q in fld]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W, H = x1 - x0, y1 - y0
    rng = random.Random(seed + 41)
    cv = C.Canvas()
    for sd in (-1, 1):
        sx = x0 + W * .06 if sd > 0 else x1 - W * .06
        sy = y0 + H * .02
        a = (0 if sd > 0 else math.pi) + sd * .2
        L = W * .15
        pts = [(sx, sy)]
        for j in range(24):
            a += sd * .012
            pts.append((pts[-1][0] + math.cos(a) * L / 24, pts[-1][1] + math.sin(a) * L / 24))
        wd = lambda t: max(.7, 3.2 * (1 - t))
        Lft = [(p[0], p[1] - wd(k / 24)) for k, p in enumerate(pts)]
        Rgt = [(p[0], p[1] + wd(k / 24)) for k, p in enumerate(pts)]
        cv.obj([Lft + Rgt[::-1]], 1.)
        cv.hair([(p[0], p[1] + wd(k / 24) * .4) for k, p in enumerate(pts)][:-2])
        for k in (7, 14, 21):
            bx, by = pts[k]
            ba = a + sd * rng.uniform(.5, .9)
            tw = [(bx, by), (bx + math.cos(ba) * L * .14, by + math.sin(ba) * L * .14)]
            cv.obj([], 0)
            cv.line(tw)
            for q in (pts[k], tw[1], ((bx + tw[1][0]) / 2, (by + tw[1][1]) / 2)):
                for m in range(rng.choice((1, 2))):
                    _catkin(cv, q[0] + m * 2.5, q[1] + 1, min(18., H * rng.uniform(.08, .12)), math.pi / 2 + sd * rng.uniform(.0, .3), rng)
    return cv.svg()


def hedge_shape(cx, cy, rx, ry):
    """The vignette's silhouette is the food-forest hedge: a skyline of rounded crowns (hazel,
    elder, serviceberry) along the top, falling to either side, a soft ground curve at the foot."""
    pts = []
    rng = random.Random(int(rx * 7 + ry))
    n = 11
    xs = [cx - rx * .92 + 2 * rx * .92 * k / n for k in range(n + 1)]
    for k in range(n):
        x0, x1 = xs[k], xs[k + 1]
        top = cy - ry * (.86 + .14 * rng.random()) * (1 - .35 * abs((x0 + x1) / 2 - cx) / rx)
        for j in range(9):
            t = j / 8
            pts.append((x0 + (x1 - x0) * t, top - ry * .07 * math.sin(math.pi * t)))
    for j in range(1, 9):
        t = j / 8
        pts.append((cx + rx * (.92 + .08 * math.sin(math.pi * t)), pts[-1][1] + (cy + ry * .6 - pts[-1][1]) * t * .5))
    for j in range(25):
        a = j / 24 * math.pi
        pts.append((cx + rx * math.cos(a), cy + ry * .55 + ry * .45 * math.sin(a)))
    for j in range(1, 9):
        t = 1 - j / 8
        pts.append((cx - rx * (.92 + .08 * math.sin(math.pi * t)), cy - ry * .2 + ry * .7 * (1 - t)))
    return pts


# ==== STUDIO FRAME (batch 2) ====================================================================
# King-tier frame, copied into this plate so it can be cut to the page (house rule: the shared
# modules stay untouched). Fine English scroll as on the GRS vise and Ken Hunt's panels: dozens of
# small logarithmic spirals grown from one stem, each branching into the next and carrying its own
# shaded leaves, packed over a punched matte ground; white "gold-line" wire borders and beading
# frame every panel; the subject sits in an inlaid medallion ringed with beads.
import math as _m
import random as _rnd
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _m.pi
_sm = _C._smooth


def _st_mat_tile():
    """An 8 px matte tile: black punched with 1 px white dots set evenly (blue noise)."""
    rng = _rnd.Random(91)
    pts = []
    tries = 0
    while len(pts) < 13 and tries < 4000:
        tries += 1
        p = (rng.randrange(16) * .5, rng.randrange(16) * .5)
        ok = True
        for q in pts:
            dx = min(abs(p[0] - q[0]), 8 - abs(p[0] - q[0]))
            dy = min(abs(p[1] - q[1]), 8 - abs(p[1] - q[1]))
            if dx * dx + dy * dy < 3.6:
                ok = False
                break
        if ok:
            pts.append(p)
    return "".join(f"M{_C._n(x)},{_C._n(y)}h1v1h-1z" for x, y in pts)


_ST_DEFS = ('<defs><pattern id="s2m" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h8v8h-8z" fill="#000"/><path d="{_st_mat_tile()}" fill="#fff"/></pattern>'
            '<pattern id="s2o" width="2" height="2" patternUnits="userSpaceOnUse"><path d="M0,0h.5v.5h-.5zM1,1h.5v.5h-.5z" fill="#000"/></pattern></defs>')


def st_matte(d):
    """The punched matte ground over path data d."""
    return f'<path d="{d}" fill="url(#s2m)" stroke="none"/>'


def st_rect_d(x, y, w, h):
    return f"M{_C._n(x)},{_C._n(y)}h{_C._n(w)}v{_C._n(h)}h{_C._n(-w)}z"


# ---------------------------------------------------------------------------------------------
# the fine scroll: spirals, leaves, growth from one stem
# ---------------------------------------------------------------------------------------------

def _spiral(px, py, head, R, s, turns):
    """A log spiral leaving (px, py) heading `head`, first radius R, turning toward side s
    (+1 = the +normal side), winding `turns` into an eye at .13 R. -> (pts, centre, radii)."""
    th = _TAU * turns
    b = _m.log(1 / .13) / th
    a0 = _m.atan2(s * R, -b * R)
    rot = head - a0
    cr, sr = _m.cos(rot), _m.sin(rot)
    pts, rad = [], []
    t = 0.
    while True:
        r = R * _m.exp(-b * t)
        lx, ly = r * _m.cos(t) - R, s * r * _m.sin(t)
        pts.append((px + lx * cr - ly * sr, py + lx * sr + ly * cr))
        rad.append(r)
        if t >= th:
            break
        t = min(th, t + max(.05, 1.4 / r))
    return pts, (px - R * cr, py - R * sr), rad


def _tangent(pts, i):
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    return _m.atan2(b[1] - a[1], b[0] - a[0])


class _Grid:
    def __init__(self, cell=24.):
        self.c = cell
        self.g = {}
        self.maxr = 0.

    def add(self, x, y, r, oid):
        self.g.setdefault((int(x // self.c), int(y // self.c)), []).append((x, y, r, oid))
        self.maxr = max(self.maxr, r)

    def clear(self, x, y, r, slack, ignore):
        reach = r + self.maxr
        c = self.c
        for i in range(int((x - reach) // c), int((x + reach) // c) + 1):
            for j in range(int((y - reach) // c), int((y + reach) // c) + 1):
                for qx, qy, qr, oid in self.g.get((i, j), ()):
                    if oid != ignore and (qx - x) ** 2 + (qy - y) ** 2 < ((r + qr) * slack) ** 2:
                        return False
        return True


def st_sweep(x, y, ang, L, k0, k1=None, n=None):
    """A sweeping stem: from (x, y) heading ang (radians), L long, curvature k0 -> k1 (1/px)."""
    k1 = k0 if k1 is None else k1
    return _C._euler(x, y, ang, L, lambda u: k0 + (k1 - k0) * u, n or max(8, int(L / 2)))


class ScrollField:
    """Grows fine scroll over a region. inside(x, y) says where scroll may grow. Scrolls branch
    from stems and from one another, each sized to the room it finds, until the field is packed."""

    def __init__(self, inside, rmin=7., rmax=30., seed=0, slack=.88):
        self.inside = inside
        self.rmin, self.rmax = rmin, rmax
        self.rng = _rnd.Random(seed)
        self.grid = _Grid(20.)
        self.slack = slack
        self.items = []
        self.queue = []

    def _ok(self, c, R, parent):
        if not self.inside(c[0], c[1]):
            return False
        if parent is not None and self.items[parent][1] == "scroll":
            pc, pR = self.items[parent][2][1], self.items[parent][2][4]
            if (pc[0] - c[0]) ** 2 + (pc[1] - c[1]) ** 2 < ((pR + R) * .78) ** 2:
                return False
        for k in range(8):
            a = k * _TAU / 8
            if not self.inside(c[0] + R * .55 * _m.cos(a), c[1] + R * .55 * _m.sin(a)):
                return False
        return self.grid.clear(c[0], c[1], R, self.slack, parent)

    def stem(self, pts, w0=2.2, w1=1.2, leaves=True, gen=0):
        """A sweeping lead, the source the scrolls grow from (points run from the root out)."""
        oid = len(self.items)
        for p in pts[::2]:
            self.grid.add(p[0], p[1], 2.5, oid)
        self.items.append((gen, "stem", (pts, w0, w1, leaves)))
        self.queue.append((gen, oid, "stem", pts, 0, None))
        return oid

    def scroll(self, px, py, head, R, s, gen=0, parent=None, turns=None, force=False):
        turns = turns or self.rng.uniform(1.25, 1.55)
        pts, c, rad = _spiral(px, py, head, R, s, turns)
        if not force and not self._ok(c, R, parent):
            return False
        oid = len(self.items)
        self.grid.add(c[0], c[1], R, oid)
        self.items.append((gen, "scroll", (pts, c, rad, s, R)))
        self.queue.append((gen, oid, "scroll", pts, s, (c, R)))
        return True

    def grow(self, max_items=300):
        rng = self.rng
        qi = 0
        while qi < len(self.queue) and len(self.items) < max_items:
            gen, oid, kind, pts, s, info = self.queue[qi]
            qi += 1
            n = len(pts)
            cand = []
            if kind == "scroll":
                c, R = info
                for f in (.03, .14, .27, .4, .52):
                    i = int(f * (n - 1))
                    q = pts[i]
                    tau = _tangent(pts, i)
                    rh = _m.hypot(q[0] - c[0], q[1] - c[1])
                    cand.append((q, tau, -s, self.rmax))
                    cand.append((q, tau + _PI, s, self.rmax * .8))
            else:
                for i in range(3, n - 2, 4):
                    q = pts[i]
                    tau = _tangent(pts, i)
                    for sd in (1, -1):
                        cand.append((q, tau + sd * .15, -sd, self.rmax))
                        cand.append((q, tau + _PI - sd * .2, sd, self.rmax * .7))
                rng.shuffle(cand)
            for q, head, cs, top in cand:
                Rc = min(self.rmax, top)
                while Rc >= self.rmin:
                    if self.scroll(q[0], q[1], head + cs * rng.uniform(-.05, .2), Rc, cs, gen + 1, oid):
                        break
                    Rc *= .82
        return self

    def _branch_to(self, oid, cx, cy, R):
        """A scroll centred at (cx, cy) whose stem leads in from the nearest coil of item oid,
        joining it tangentially, so every scroll grows out of another."""
        it = self.items[oid]
        pts = it[2][0]
        if it[1] == "scroll":
            pc, pR, rad = it[2][1], it[2][4], it[2][2]
            idx = [i for i in range(0, len(pts), 2) if rad[i] > pR * .45 and
                   (pts[i][0] - pc[0]) * (cx - pts[i][0]) + (pts[i][1] - pc[1]) * (cy - pts[i][1]) > 0] or list(range(0, len(pts) // 3))
        else:
            idx = list(range(0, len(pts), 2))
        bi = min(idx, key=lambda i: (pts[i][0] - cx) ** 2 + (pts[i][1] - cy) ** 2)
        q = pts[bi]
        tau = _tangent(pts, bi)
        ua = _m.atan2(q[1] - cy, q[0] - cx)
        S = (cx + R * _m.cos(ua), cy + R * _m.sin(ua))
        hx, hy = _m.cos(tau), _m.sin(tau)
        if hx * (S[0] - q[0]) + hy * (S[1] - q[1]) < 0:
            hx, hy = -hx, -hy
        turns = self.rng.uniform(1.25, 1.55)
        th = _TAU * turns
        bb = _m.log(1 / .13) / th
        best = None
        for sg in (1, -1):
            tx = -bb * _m.cos(ua) - sg * _m.sin(ua)
            ty = -bb * _m.sin(ua) + sg * _m.cos(ua)
            dot = tx * hx + ty * hy
            if best is None or dot > best[0]:
                best = (dot, sg, tx, ty)
        _, sg, tx, ty = best
        tl = _m.hypot(tx, ty)
        tx, ty = tx / tl, ty / tl
        L = _m.hypot(S[0] - q[0], S[1] - q[1])
        lead = []
        if L > 1.5:
            k = L * .45 + 2
            p1 = (q[0] + hx * k, q[1] + hy * k)
            p2 = (S[0] - tx * k, S[1] - ty * k)
            m = max(3, int(L / 1.5))
            for i in range(m):
                t = i / m
                a, b_, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
                lead.append((a * q[0] + b_ * p1[0] + c * p2[0] + d * S[0], a * q[1] + b_ * p1[1] + c * p2[1] + d * S[1]))
        sp, rad = [], []
        t = 0.
        while True:
            r = R * _m.exp(-bb * t)
            ph = ua + sg * t
            sp.append((cx + r * _m.cos(ph), cy + r * _m.sin(ph)))
            rad.append(r)
            if t >= th:
                break
            t = min(th, t + max(.05, 1.4 / r))
        allp = lead + sp
        allr = [R] * len(lead) + rad
        noid = len(self.items)
        self.grid.add(cx, cy, R, noid)
        self.items.append((it[0] + 1, "scroll", (allp, (cx, cy), allr, sg, R)))
        return True

    def fill(self, x, y, w, h, step=5., max_items=320):
        """Pack the field: find the widest free spot, branch a scroll into it from the nearest
        scroll's outer coil, repeat until no gap of about rmin is left."""
        rng = self.rng
        P = []
        nx, ny = max(2, int(w / step)), max(2, int(h / step))
        for j in range(ny):
            for i in range(nx):
                px, py = x + (i + .5) * w / nx, y + (j + .5) * h / ny
                if self.inside(px, py):
                    P.append([px, py, 1e9, None])
        if not P:
            return self
        cell = {}
        for k, p in enumerate(P):
            cell.setdefault((int(p[0] // 30), int(p[1] // 30)), []).append(k)

        def upd(oid, cx, cy, R, reach=None):
            reach = R + (reach or self.rmax * 3)
            for i in range(int((cx - reach) // 30), int((cx + reach) // 30) + 1):
                for j in range(int((cy - reach) // 30), int((cy + reach) // 30) + 1):
                    for k in cell.get((i, j), ()):
                        p = P[k]
                        d = _m.hypot(p[0] - cx, p[1] - cy) - R
                        if d < p[2]:
                            p[2], p[3] = d, oid
        obs = []
        for oid, it in enumerate(self.items):
            if it[1] == "scroll":
                obs.append((it[2][1][0], it[2][1][1], it[2][4], oid))
            else:
                obs.extend((q[0], q[1], 2.5, oid) for q in it[2][0][::5])
        for p in P:
            for ox, oy, orr, oid in obs:
                d = _m.hypot(p[0] - ox, p[1] - oy) - orr
                if d < p[2]:
                    p[2], p[3] = d, oid
        import heapq
        hp = [(-p[2], k) for k, p in enumerate(P)]
        heapq.heapify(hp)
        while len(self.items) < max_items and hp:
            nd, k = heapq.heappop(hp)
            best = P[k]
            if -nd != best[2]:
                heapq.heappush(hp, (-best[2], k))
                continue
            if best[2] < self.rmin * 1.15:
                break
            px, py, D, oid = best
            if oid is None:
                continue
            R = min(self.rmax, D * .97) * rng.uniform(.9, 1.)
            self._branch_to(oid, px, py, R)
            upd(len(self.items) - 1, px, py, R)
            for kk in cell.get((int(px // 30), int(py // 30)), ()):
                heapq.heappush(hp, (-P[kk][2], kk))
        return self

    def draw(self, cv, egg=None, egg_gen=2):
        """Paint the branches first so each parent lies over its children. egg(cv, x, y, r) is
        cut into the eye of one scroll of generation egg_gen (the first big enough)."""
        rng = _rnd.Random(7)
        order = sorted(range(len(self.items)), key=lambda k: -self.items[k][0])
        egg_done = egg is None
        for k in order:
            gen, kind, data = self.items[k]
            if kind == "stem":
                pts, w0, w1, lv = data
                _draw_stem(cv, pts, w0, w1, rng, lv)
                continue
            pts, c, rad, s, R = data
            use = None
            if not egg_done and gen >= egg_gen and R > 14:
                use, egg_done = egg, True
            _draw_scroll(cv, pts, c, rad, s, R, rng, use)


def _leaf(cv, x, y, ang, L, W, bend, curl, rng, lobes=None):
    """A fine-scroll leaf: a curved blade scalloped on its outer edge and turning over at the tip,
    fine parallel cuts on its shadow side, a bright cut edge, a centre vein."""
    n = max(8, int(L / 1.2))
    sp = _C._euler(x, y, ang, L, lambda u: (bend + curl * _sm(.55, 1., u) ** 2 * 3.2) / L, n)
    c = 1 if bend >= 0 else -1
    nl = lobes or (3 if L > 14 else 2)
    ph = rng.uniform(0, .3)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        pr = min(1., u / .22) ** .6 * (1 - u) ** .7 * 1.35
        v = (u * nl + ph) % 1.
        wo.append(W * pr * (.6 + .4 * _m.sin(_PI * v) ** .6) + .3)
        wi.append(W * pr * .85 + .3)
    R = _C._Rib(sp, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    cv.hair(_C._fill_lines(R, .22 * c, .92 * c, 1.5, .06, .9, 2))
    if W > 2.4:
        cv.hair(R.contour(-.05 * c, .12, .72))
    for j in range(nl):
        u = (j - ph) / nl
        if .18 < u < .85 and R.width(u, -c) > 1.8:
            cv.hair([R.at(u, -.95 * c), R.at(u + .05, -.4 * c)])
    return R


def _draw_stem(cv, pts, w0, w1, rng, leaves):
    n = len(pts)
    W = [w0 + (w1 - w0) * i / max(1, n - 1) for i in range(n)]
    R = _C._Rib(pts, W, W)
    if leaves:
        L = R.L
        u = .06
        sd = 1
        while u < .94:
            i = int(u * (n - 1))
            q = R.at(u, sd * .8)
            ll = rng.uniform(9, 13)
            _leaf(cv, q[0], q[1], _tangent(pts, i) + sd * .55, ll, ll * .22, -sd * .5, sd * 2.2, rng)
            sd = -sd
            u += rng.uniform(13, 18) / L
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(-.4, 0., 1.))
    cv.hair(R.contour(-.8, 0., 1.))


def _draw_scroll(cv, pts, c, rad, s, R, rng, egg=None):
    n = len(pts)
    hw0 = max(1., min(3.2, R * .13))
    W = [max(.6, hw0 * (rad[i] / R) ** .55) for i in range(n)]
    Rb = _C._Rib(pts, W, W)
    # where the coil proper starts (after any lead-in)
    k0 = 0
    while k0 < n - 1 and rad[k0 + 1] >= R - 1e-6:
        k0 += 1
    span = n - 1 - k0
    nlv = 1 if R < 10 else (2 if R < 16 else 3)
    fs = (.03, .2, .36)[:nlv]
    for j, f in enumerate(fs[::-1]):
        i = k0 + int(f * span)
        q = Rb.at(i / (n - 1), -s)
        ll = rad[i] * rng.uniform(.8, .95)
        _leaf(cv, q[0], q[1], _tangent(pts, i) - s * .55, ll, ll * .25, s * .9, -s * rng.uniform(1.2, 1.8), rng)
    if k0 > 6:
        i = k0 // 2
        q = Rb.at(i / (n - 1), s)
        ll = min(R * .7, 12.)
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .6, ll, ll * .24, -s * .7, s * 1.6, rng)
    cv.obj([Rb.outline()], .5)
    cv.hair(Rb.contour(.5 * s, 0., .92))
    if hw0 > 1.8:
        cv.hair(Rb.contour(.82 * s, 0., .8))
        cv.hair(Rb.contour(-.55 * s, .0, .35))
    if R > 15:
        i = k0 + int(.55 * span)
        q = Rb.at(i / (n - 1), s)
        ll = rad[i] * .95
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .35, ll, ll * .2, s * 1.6, s * .3, rng, 2)
    ex, ey = pts[-1]
    if egg:
        egg(cv, ex, ey, max(5., R * .4))
    else:
        rr = max(1.1, W[-1] * 1.4)
        cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)
        cv.line(_C._ell_pts(ex, ey, .3, .3, 4))


# ---------------------------------------------------------------------------------------------
# borders, beading, medallion, arms
# ---------------------------------------------------------------------------------------------

def st_wire(d):
    """A gold-line (wire inlay) border along path d: white wire, black, white wire on a black bed."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="5"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="3"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>')


def st_beads(d, pitch=3.5, r=1.):
    """A row of white beads on a black fillet along path d."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_C._n(2 * r + 2)}"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_C._n(2 * r)}" stroke-linecap="round" '
            f'stroke-dasharray="0 {_C._n(pitch)}"/>')


def st_ell_d(cx, cy, rx, ry, n=96):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n), True, .1)


def st_poly_d(poly):
    return _C._d(list(poly), True, .1)


def st_medallion(cx, cy, rx, ry):
    """An inlaid portrait medallion: wire, a ring of beads, wire. -> (svg, field polygon)."""
    o = [f'<path d="{st_ell_d(cx, cy, rx + 7, ry + 7)}" fill="#000" stroke="none"/>',
         st_wire(st_ell_d(cx, cy, rx + 5.5, ry + 5.5)),
         st_beads(st_ell_d(cx, cy, rx + 1.5, ry + 1.5, 180), 3.5, 1.),
         f'<path d="{st_ell_d(cx, cy, rx - .5, ry - .5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), _C._ell_pts(cx, cy, rx - 1.2, ry - 1.2, 120)[:-1]


def st_arch(cx, top, bot, half, n=48):
    """An arched (round-headed) panel polygon: the binding's central panel."""
    r = half
    pts = [(cx - half, bot)]
    for i in range(n + 1):
        a = _PI + _PI * i / n
        pts.append((cx + r * _m.cos(a), top + r + r * _m.sin(a)))
    pts.append((cx + half, bot))
    return pts


def st_arch_medallion(cx, top, bot, half):
    o = [f'<path d="{st_poly_d(st_arch(cx, top - 7, bot + 7, half + 7))}" fill="#000" stroke="none"/>',
         st_wire(st_poly_d(st_arch(cx, top - 5.5, bot + 5.5, half + 5.5))),
         st_beads(st_poly_d(st_arch(cx, top - 1.5, bot + 1.5, half + 1.5, 96)), 3.5, 1.),
         f'<path d="{st_poly_d(st_arch(cx, top + .5, bot - .5, half - .5))}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_arch(cx, top + 1.2, bot - 1.2, half - 1.2, 72)


def st_shape_pts(shape, cx, cy, rx, ry, g=0., n=120, ph=0.):
    """The outline of a shaped panel grown outward by g: oval, roundel, arch or irregular."""
    if shape == "arch":
        return st_arch(cx, cy - ry - g, cy + ry + g, rx + g, max(24, n // 2))
    if shape == "roundel":
        rx = ry = min(rx, ry)
    pts = []
    for i in range(n):
        t = _TAU * i / n
        k = 1.
        if shape == "irregular":
            k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
        pts.append((cx + (rx * k + g) * _m.cos(t), cy + (ry * k + g) * _m.sin(t)))
    return pts


def st_shape_in(shape, x, y, cx, cy, rx, ry, g=0., ph=0.):
    if shape == "arch":
        if y >= cy - ry + rx:
            return abs(x - cx) < rx + g and y < cy + ry + g
        return _m.hypot(x - cx, y - (cy - ry + rx)) < rx + g
    if shape == "roundel":
        rx = ry = min(rx, ry)
    t = _m.atan2((y - cy) / max(ry, 1), (x - cx) / max(rx, 1))
    k = 1.
    if shape == "irregular":
        k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
    return ((x - cx) / (rx * k + g)) ** 2 + ((y - cy) / (ry * k + g)) ** 2 < 1


def st_shaped_medallion(shape, cx, cy, rx, ry, ph=0.):
    """A shaped inlaid panel: black bed, wire, beads, white fillet. -> (svg, field polygon)."""
    if shape == "oval":
        return st_medallion(cx, cy, rx, ry)
    P = lambda g, n=120: st_poly_d(st_shape_pts(shape, cx, cy, rx, ry, g, n, ph))
    o = [f'<path d="{P(7)}" fill="#000" stroke="none"/>', st_wire(P(5.5)), st_beads(P(1.5, 180), 3.5, 1.),
         f'<path d="{P(-.5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_shape_pts(shape, cx, cy, rx, ry, -1.2, 120, ph)


def st_dedication(cx, foot, hh):
    """The small Somaster dedication cartouche at a front vignette's foot (about 30 px)."""
    return st_arms(cx, foot - hh / 2, hh * .5, hh * .5, mantling=True)


def st_device(w, h, seed, hk):
    """A marginal device (a 40-60 px roundel): the subject in a beaded roundel, the corners of
    the block cut away to the matte with a leaf in each spandrel."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    cx, cy = w / 2, h / 2
    r = min(w, h) / 2 - (4.5 if min(w, h) < 64 else 7.5)
    cv = StCanvas()
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * (w / 2 - 3), cy + sy * (h / 2 - 3)
            a = _m.atan2(cy - py, cx - px)
            if _m.hypot(px - cx, py - cy) > r + 9:
                L = max(4., (_m.hypot(px - cx, py - cy) - r - 6) * 1.1)
                _leaf(cv, px, py, a, L, L * .42, .5 * sx * sy, .35, _rnd.Random(seed + sx * 3 + sy))
    o.append(cv.svg())
    o.append(st_wire(st_rect_d(1.5, 1.5, w - 3, h - 3)))
    o.append(f'<path d="{st_ell_d(cx, cy, r + 3.5, r + 3.5)}" fill="#000"/>'
             f'<path d="{st_ell_d(cx, cy, r + 2, r + 2)}" fill="none" stroke="#fff" stroke-width="1" stroke-dasharray="1 1.5"/>'
             f'<path d="{st_ell_d(cx, cy, r - .2, r - .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    fld = _C._ell_pts(cx, cy, r - .9, r - .9, 72)[:-1]
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2d{w}x{h}v", fld, hk["field"](fld, "device") + st_rim(fld, 2.5)))
    return "".join(o)


def st_clip_poly(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{_C._d(list(poly), True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_clip_rect(cid, x, y, w, h, body):
    return f'<clipPath id="{cid}"><path d="{st_rect_d(x, y, w, h)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_sun(cv, cx, cy, r, rays=16):
    disc = _C._ell_pts(cx, cy, r, r, 28)[:-1]
    for k in range(rays):
        a = k * _TAU / rays
        ln = r * (1.9 if k % 2 == 0 else 1.5)
        w = _PI / rays * .7
        tri = [(cx + r * .9 * _m.cos(a - w), cy + r * .9 * _m.sin(a - w)), (cx + ln * _m.cos(a), cy + ln * _m.sin(a)),
               (cx + r * .9 * _m.cos(a + w), cy + r * .9 * _m.sin(a + w))]
        cv.obj([tri], .5)
        cv.hair([(cx + r * _m.cos(a + w * .4), cy + r * _m.sin(a + w * .4)), (cx + ln * .9 * _m.cos(a), cy + ln * .9 * _m.sin(a))])
    cv.obj([disc], .5)
    cv.hair([p for p in _C.hatch_poly(disc, 45, 1.5) if p[0][0] + p[0][1] > cx + cy - r * .3])


def _stick(cv, x0, y0, x1, y1, w):
    a = _m.atan2(y1 - y0, x1 - x0)
    n = 16
    pts = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    W = [w * (1 - .55 * _sm(.6, .95, i / n)) for i in range(n + 1)]
    R = _C._Rib(pts, W, W)
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(.6, .02, .93))
    tx, ty = x1 + _m.cos(a) * w * .5, y1 + _m.sin(a) * w * .5
    cv.obj([_C._ell_pts(tx, ty, w * 1.1, w * .8, 12)[:-1]], .5)


def st_crossed_sticks(cv, cx, cy, L, w=1.3, ang=0.):
    """Parker's crossed drumsticks, bead tips up."""
    for sd in (-1, 1):
        a = ang - _PI / 2 + sd * .62
        dx, dy = _m.cos(a) * L / 2, _m.sin(a) * L / 2
        _stick(cv, cx - dx, cy - dy, cx + dx, cy + dy, w)


_FLEUR = [(0, -1), (.13, -.72), (.16, -.42), (.1, -.15), (.24, -.2), (.42, -.42), (.62, -.48), (.78, -.38),
          (.8, -.18), (.68, -.02), (.54, .04), (.62, -.12), (.6, -.26), (.48, -.26), (.34, -.08), (.22, .1),
          (.36, .1), (.36, .22), (.14, .22), (.2, .5), (.38, .72), (.2, .7), (.08, .54), (0, .62)]


def _fleur(cx, cy, s):
    """A fleur-de-lis about 2s tall, as one closed polygon."""
    right = [(cx + x * s, cy + y * s) for x, y in _FLEUR]
    left = [(cx - x * s, cy + y * s) for x, y in _FLEUR[::-1]][1:-1]
    return right + left


def _heater(cx, top, w, h, n=24):
    """A heater shield outline: straight chief, sides curving to the point."""
    pts = [(cx - w / 2, top), (cx + w / 2, top)]
    for i in range(n + 1):
        t = i / n
        pts.append((cx + w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    for i in range(n, -1, -1):
        t = i / n
        pts.append((cx - w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    return pts


def st_arms(cx, cy, rx, ry, mantling=True):
    """Parker's arms, Somaster: Or, a castle between five fleurs-de-lis sable. A heater shield,
    Or as an even field of fine dots (Petra Sancta), the charges sable cut in solid black with
    white mortar lines; acanthus mantling springs from behind the shield's top corners."""
    o = []
    sh = min(ry * 2, rx * 2.3)
    sw = sh * .84
    top = cy - sh / 2
    shield = _heater(cx, top, sw, sh)
    if mantling:
        cv = _C.Canvas()
        rng = _rnd.Random(5)
        for sd in (-1, 1):
            for k, (a, L) in enumerate(((-.3, .9), (.25, .8), (.85, .7), (1.35, .55))):
                ang = (_PI / 2 - (a + 1.2)) if sd > 0 else (_PI / 2 + (a + 1.2))
                x0, y0 = cx + sd * sw * .42, top + sh * .1 + k * sh * .12
                _leaf(cv, x0, y0, -ang + _PI if False else (a * sd + (0 if sd > 0 else _PI)), sh * L * .55, sh * L * .12,
                      sd * .8, -sd * 2., rng, 3)
        o.append(cv.svg())
    d = st_poly_d(shield)
    o.append(f'<path d="{d}" fill="#000" stroke="#000" stroke-width="3"/>')
    o.append(f'<path d="{d}" fill="#fff" stroke="#fff" stroke-width="1"/>')
    o.append(f'<path d="{d}" fill="url(#s2o)" stroke="#000" stroke-width=".5"/>')
    blk = []
    s = sh * .085
    for fx, fy in ((-.26, .14), (0, .14), (.26, .14), (-.36, .55), (.36, .55)):
        blk.append(_fleur(cx + fx * sw, top + fy * sh + s * .1, s))
    # the castle: two towers and a curtain wall, crenellated, an arched gate with a portcullis
    cw, chh = sw * .46, sh * .3
    bx0, by1 = cx - cw / 2, top + sh * .72
    tw, th = cw * .24, chh * 1.3
    mer = tw / 5
    for tx in (bx0, bx0 + cw - tw):
        ty = by1 - th
        pts = [(tx, by1), (tx, ty)]
        for k in range(5):
            x = tx + k * mer
            if k % 2 == 0:
                pts += [(x, ty - mer), (x + mer, ty - mer)]
            else:
                pts += [(x, ty), (x + mer, ty)]
        pts += [(tx + tw, ty), (tx + tw, by1)]
        blk.append(pts)
    wy = by1 - chh * .72
    wx0, wx1 = bx0 + tw - .2, bx0 + cw - tw + .2
    nm = max(3, int((wx1 - wx0) / mer))
    mm = (wx1 - wx0) / nm
    pts = [(wx0, by1), (wx0, wy)]
    for k in range(nm):
        x = wx0 + k * mm
        if k % 2 == 1:
            pts += [(x, wy - mer * .9), (x + mm, wy - mer * .9)]
        else:
            pts += [(x, wy), (x + mm, wy)]
    pts += [(wx1, wy), (wx1, by1)]
    blk.append(pts)
    o.append(f'<path d="{"".join(st_poly_d(p) for p in blk)}" fill="#000" stroke="none"/>')
    # white work in the sable: mortar courses, tower windows, the gate and its portcullis
    lines = []
    for k in range(1, 6):
        y = by1 - k * chh * .2
        lines.append([(bx0 + 1, y), (bx0 + tw - 1, y)])
        lines.append([(bx0 + cw - tw + 1, y), (bx0 + cw - 1, y)])
        if y > wy + 1:
            lines.append([(wx0 + 1, y), (wx1 - 1, y)])
    gw, gh = cw * .2, chh * .55
    gate = [(cx - gw / 2, by1)] + [(cx - gw / 2 * _m.cos(t * _PI / 12), by1 - gh * .6 - gw / 2 * _m.sin(t * _PI / 12)) for t in range(13)] + [(cx + gw / 2, by1)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in lines)}" stroke="#fff" stroke-width="1" fill="none"/>')
    o.append(f'<path d="{st_poly_d(gate)}" fill="#fff" stroke="none"/>')
    pc = [[(cx + gw * (k / 4 - .5) * .8, by1 - gh * .95), (cx + gw * (k / 4 - .5) * .8, by1)] for k in range(5)]
    pc += [[(cx - gw * .45, by1 - gh * .3 * k), (cx + gw * .45, by1 - gh * .3 * k)] for k in (1, 2)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in pc)}" stroke="#000" stroke-width=".5" fill="none"/>')
    for tx in (bx0 + tw / 2, bx0 + cw - tw / 2):
        o.append(f'<path d="M{_C._n(tx)},{_C._n(by1 - th * .75)}v{_C._n(th * .22)}" stroke="#fff" stroke-width="1"/>')
    return "".join(o)


def st_sky(x0, y0, x1, y1, seed, avoid=None, clouds=None, top_dark=.32, pitch=(2., 2., 3., 3.)):
    """A Dore sky, not a ruled one: long lines that swell over billowing cloud banks (lit tops
    left white, undersides shaded), dark and cross-cut at the zenith, opening toward the horizon.
    Returns (hair polylines, line polylines). avoid(x, y) breaks the lines (moon, towers)."""
    rng = _rnd.Random(seed)
    W, H = x1 - x0, y1 - y0
    if clouds is None:
        clouds = []
        n = max(2, int(W / 80) + 1)
        for i in range(n):
            cx = x0 + W * (i + rng.uniform(.2, .8)) / n
            cy = y0 + H * rng.uniform(.3, .75)
            clouds.append((cx, cy, W / n * rng.uniform(.45, .7), H * rng.uniform(.09, .16)))
    hair, heavy = [], []

    def cloud_at(x, y):
        for cx, cy, rx, ry in clouds:
            dx = (x - cx) / rx
            if abs(dx) < 1:
                top = cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))
                bot = cy + ry * .35 * (1 - dx * dx) ** .5
                if top <= y <= bot:
                    return (y - top) / max(.5, bot - top)
        return None
    y = y0 + .75
    while y < y1:
        f = (y - y0) / max(1., H)
        p = pitch[min(len(pitch) - 1, int(f * len(pitch)))]
        run = []
        x = x0
        while x <= x1 + 3:
            yy = y
            for ccx, ccy, crx, cry in clouds:
                dx = (x - ccx) / (crx * 1.5)
                if abs(dx) < 1 and y > ccy:
                    yy += cry * .22 * (1 - dx * dx) ** 2 * max(0., 1 - (y - ccy) / (cry * 3))
            cf = cloud_at(x, yy)
            lit = cf is not None and cf < .55
            if lit or (avoid and avoid(x, yy)):
                if len(run) > 1:
                    hair.append(run)
                run = []
            else:
                run.append((x, yy))
            x += 3.
        if len(run) > 1:
            hair.append(run)
        y += p
    # cloud edges: billowed tops, shaded bellies
    for cx, cy, rx, ry in clouds:
        top = []
        for i in range(41):
            dx = -1 + 2 * i / 40
            top.append((cx + dx * rx, cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))))
        hair.append(top)
        for k in range(1, 4):
            arc = []
            for i in range(31):
                dx = -.85 + 1.7 * i / 30
                arc.append((cx + dx * rx * (1 - .12 * k), cy - ry * (1 - dx * dx) ** .5 * (.55 - .14 * k) + ry * .1 * k))
            hair.append(arc)
    # the zenith: cross-cut so the sky deepens upward
    zt = y0 + H * top_dark
    for ln in _C.hatch_poly([(x0, y0), (x1, y0), (x1, zt), (x0, zt)], 30, 3.):
        if avoid:
            a_, b_ = ln
            seg, cur = [], []
            for i in range(int(_m.dist(a_, b_) / 2) + 2):
                t = i / max(1, int(_m.dist(a_, b_) / 2) + 1)
                q = (a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t)
                if avoid(*q):
                    if len(cur) > 1:
                        hair.append(cur)
                    cur = []
                else:
                    cur.append(q)
            if len(cur) > 1:
                hair.append(cur)
        else:
            hair.append(ln)
    return hair, heavy


def st_rim(fld, depth=12., uid="r"):
    """Light emerging from dark: concentric cuts round the inside of a medallion field, close and
    heavy at the rim, thinning inward, so the subject glows out of a dark surround."""
    cx = sum(p[0] for p in fld) / len(fld)
    cy = sum(p[1] for p in fld) / len(fld)
    size = min(max(abs(p[0] - cx) for p in fld), max(abs(p[1] - cy) for p in fld))
    o1, o5 = [], []
    d = .75
    while d < depth:
        k = 1 - d / size
        ring = [(cx + (p[0] - cx) * k, cy + (p[1] - cy) * k) for p in fld]
        (o1 if d < depth * .35 else o5).append(_C._d(ring + [ring[0]], tol=.2))
        d += 2. if d < depth * .35 else 1.5 + (d / depth) * 1.5
    return (f'<path d="{"".join(o1)}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="{"".join(o5)}" fill="none" stroke="#000" stroke-width=".5"/>')


# ---------------------------------------------------------------------------------------------
# Easter eggs cut into a scroll's eye: egg(cv, x, y, r) draws inside a disc of radius r
# ---------------------------------------------------------------------------------------------

def _egg_disc(cv, x, y, r):
    cv.obj([_C._ell_pts(x, y, r, r, 28)[:-1]], 1.)
    cv.hair(_C._ell_pts(x, y, r - 1.2, r - 1.2, 28))


def egg_sticks(cv, x, y, r):
    """Parker's crossed drumsticks."""
    _egg_disc(cv, x, y, r)
    st_crossed_sticks(cv, x, y + r * .05, r * 1.45, max(.6, r * .09))


def egg_P(cv, x, y, r):
    """A "P" monogram, cut as a stem and a bowl with a flourish."""
    _egg_disc(cv, x, y, r)
    h = r * 1.1
    cv.line([(x - h * .22, y + h * .5), (x - h * .22, y - h * .5)])
    bowl = [(x - h * .22, y - h * .5)] + [(x - h * .05 + h * .3 * _m.sin(t * _PI / 10), y - h * .25 - h * .25 * _m.cos(t * _PI / 10)) for t in range(11)] + [(x - h * .22, y)]
    cv.line(bowl)
    cv.hair([(x - h * .45, y + h * .5), (x + h * .05, y + h * .5)])
    cv.hair([(x - h * .22, y + h * .5), (x - h * .5, y + h * .62), (x - h * .62, y + h * .45)])


def egg_note(cv, x, y, r):
    """A swing eighth-note pair (jazz)."""
    _egg_disc(cv, x, y, r)
    s = r * .32
    for dx in (-1, 1):
        hx, hy = x + dx * s * 1.1 - s * .4, y + s * 1.1
        cv.obj([_C._ell_pts(hx, hy, s * .55, s * .38, 12)[:-1]], .5)
        cv.line(_C._ell_pts(hx, hy, s * .3, s * .15, 8))
        cv.line([(hx + s * .5, hy), (hx + s * .5, y - s * 1.5)])
    cv.heavy([(x - s * .6 + s * .1, y - s * 1.5), (x + s * 1.6 + s * .1, y - s * 1.5)])


def egg_cymbal(cv, x, y, r):
    """A tiny ride cymbal on its stand, lathe rings and a bell."""
    _egg_disc(cv, x, y, r)
    cy = y - r * .15
    cv.obj([_C._ell_pts(x, cy, r * .8, r * .22, 24)[:-1]], .5)
    for k in (1, 2, 3):
        cv.hair(_C._ell_pts(x, cy, r * .8 * k / 4, r * .22 * k / 4, 20))
    cv.obj([_C._ell_pts(x, cy - r * .08, r * .16, r * .1, 10)[:-1]], .5)
    cv.line([(x, cy + r * .2), (x, y + r * .7)])
    cv.hair([(x, y + r * .55), (x - r * .35, y + r * .78)])
    cv.hair([(x, y + r * .55), (x + r * .35, y + r * .78)])


def egg_hood(cv, x, y, r):
    """Mt. Hood: the snow cone, its glaciers and a timber line."""
    _egg_disc(cv, x, y, r)
    pk = [(x - r * .82, y + r * .45), (x - r * .1, y - r * .55), (x + r * .05, y - r * .6), (x + r * .82, y + r * .45)]
    cv.obj([pk], .5)
    cv.hair([(x - r * .02, y - r * .5), (x - r * .25, y + r * .05)])
    cv.hair([(x + r * .05, y - r * .5), (x + r * .3, y + r * .1)])
    cv.hair(_C.hatch_poly([(x + r * .05, y - r * .58), (x + r * .82, y + r * .45), (x + r * .25, y + r * .45)], 60, 1.5))
    for k in range(7):
        tx = x - r * .7 + k * r * .23
        cv.line([(tx, y + r * .62), (tx, y + r * .38)])


def egg_pinwheel(cv, x, y, r):
    """The Blazers pinwheel: five pairs of swept bars turning about a hub."""
    _egg_disc(cv, x, y, r)
    for k in range(5):
        a = k * _TAU / 5 - _PI / 2
        for off in (-.12, .12):
            p0 = (x + r * .18 * _m.cos(a + off), y + r * .18 * _m.sin(a + off))
            p1 = (x + r * .78 * _m.cos(a + off + .35), y + r * .78 * _m.sin(a + off + .35))
            cv.line([p0, p1])


def egg_heron(cv, x, y, r):
    """A Sauvie Island heron's head and S neck, crest plume and dagger bill."""
    _egg_disc(cv, x, y, r)
    neck = [(x - r * .1, y + r * .8), (x - r * .35, y + r * .3), (x - r * .05, y - r * .05), (x - r * .25, y - r * .4)]
    cv.line(neck)
    cv.line([(x - r * .05 + r * .15, y + r * .8), (x - r * .2 + r * .12, y + r * .3), (x + r * .12, y - r * .02), (x - r * .1, y - r * .35)])
    hd = _C._ell_pts(x - r * .2, y - r * .45, r * .16, r * .11, 12)[:-1]
    cv.obj([hd], .5)
    cv.line([(x - r * .05, y - r * .48), (x + r * .65, y - r * .38)])
    cv.hair([(x - r * .32, y - r * .5), (x - r * .7, y - r * .55)])


def egg_dog(cv, x, y, r):
    """Parker's dog, head on its paws, curled asleep in the eye of the scroll."""
    _egg_disc(cv, x, y, r)
    body = _C._ell_pts(x + r * .05, y + r * .15, r * .72, r * .42, 24)[:-1]
    cv.obj([body], .5)
    cv.hair(_C._fill_lines(_C._Rib([(x - r * .6, y + r * .15), (x + r * .7, y + r * .15)], [r * .38, r * .38], [r * .38, r * .38]), -.3, -.95, 1.5, .1, .9, 2))
    head = _C._ell_pts(x - r * .38, y - r * .05, r * .26, r * .2, 16)[:-1]
    cv.obj([head], .5)
    cv.obj([[(x - r * .48, y - r * .2), (x - r * .3, y - r * .45), (x - r * .22, y - r * .16)]], .5)
    cv.line(_C._ell_pts(x - r * .6, y - r * .02, .5, .5, 4))
    cv.hair([(x - r * .45, y - r * .06), (x - r * .36, y - r * .04)])
    cv.hair([(x + r * .7, y + r * .1), (x + r * .55, y + r * .45), (x + r * .1, y + r * .52)])


def egg_kranok(cv, x, y, r):
    """A Thai kranok flame: three flame tongues curling up out of a lotus calyx."""
    _egg_disc(cv, x, y, r)
    for sd, L, a in ((0, 1., -_PI / 2), (-1, .7, -_PI / 2 - .55), (1, .7, -_PI / 2 + .55)):
        bx = x + sd * r * .12
        rib = _C._euler(bx, y + r * .5, a, r * L, lambda u, s_=sd or 1: s_ * 2.2 * _sm(.5, 1, u) / (r * L), 12)
        W = [r * .16 * (1 - i / 12) ** .7 + .3 for i in range(13)]
        R = _C._Rib(rib, W, W)
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.4, .05, .85))
    cv.obj([_C._ell_pts(x, y + r * .55, r * .3, r * .14, 14)[:-1]], .5)


def egg_panel(cv, x, y, r):
    """A solar panel on its rack: a grid of cells, one ray of sun."""
    _egg_disc(cv, x, y, r)
    q = [(x - r * .7, y + r * .2), (x + r * .45, y + r * .2), (x + r * .7, y - r * .35), (x - r * .45, y - r * .35)]
    cv.obj([q], .5)
    for k in range(1, 4):
        t = k / 4
        cv.hair([(q[0][0] + (q[1][0] - q[0][0]) * t, q[0][1]), (q[3][0] + (q[2][0] - q[3][0]) * t, q[3][1])])
    cv.hair([((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2), ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)])
    cv.line([(x - r * .1, y + r * .2), (x - r * .1, y + r * .65)])
    cv.line([(x - r * .4, y + r * .65), (x + r * .25, y + r * .65)])


# ---------------------------------------------------------------------------------------------
# lettering: engraved Roman capitals as strokes (no <text>)
# ---------------------------------------------------------------------------------------------

_OV = [(.5 + .5 * _m.cos(_TAU * i / 20 - _PI / 2), .5 + .5 * _m.sin(_TAU * i / 20 - _PI / 2)) for i in range(21)]
_GL = {
    "A": ([[(0, 1), (.5, 0), (1, 1)], [(.22, .62), (.78, .62)]], .85),
    "B": ([[(0, 0), (0, 1), (.7, 1), (.9, .85), (.9, .65), (.7, .5), (0, .5)], [(0, 0), (.62, 0), (.82, .12), (.82, .38), (.62, .5)]], .75),
    "C": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .85)]], .8),
    "D": ([[(0, 0), (0, 1), (.55, 1), (.92, .72), (.92, .28), (.55, 0), (0, 0)]], .8),
    "E": ([[(.85, 0), (0, 0), (0, 1), (.85, 1)], [(0, .5), (.65, .5)]], .7),
    "F": ([[(.85, 0), (0, 0), (0, 1)], [(0, .5), (.65, .5)]], .65),
    "G": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .8), (.95, .55), (.55, .55)]], .82),
    "H": ([[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .5), (1, .5)]], .8),
    "I": ([[(.5, 0), (.5, 1)]], .3),
    "J": ([[(.8, 0), (.8, .78), (.6, 1), (.2, 1), (0, .8)]], .6),
    "K": ([[(0, 0), (0, 1)], [(.9, 0), (0, .62)], [(.3, .42), (.95, 1)]], .78),
    "L": ([[(0, 0), (0, 1), (.85, 1)]], .65),
    "M": ([[(0, 1), (0, 0), (.5, .65), (1, 0), (1, 1)]], 1.),
    "N": ([[(0, 1), (0, 0), (1, 1), (1, 0)]], .82),
    "O": ([_OV], .9),
    "P": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)]], .72),
    "Q": ([_OV, [(.6, .72), (1, 1.06)]], .9),
    "R": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)], [(.45, .5), (.95, 1)]], .76),
    "S": ([[(.9, .12), (.7, 0), (.25, 0), (.05, .15), (.05, .35), (.25, .47), (.75, .53), (.95, .66), (.95, .85), (.75, 1), (.25, 1), (.05, .88)]], .7),
    "T": ([[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]], .78),
    "U": ([[(0, 0), (0, .75), (.25, 1), (.75, 1), (1, .75), (1, 0)]], .8),
    "V": ([[(0, 0), (.5, 1), (1, 0)]], .82),
    "W": ([[(0, 0), (.25, 1), (.5, .35), (.75, 1), (1, 0)]], 1.1),
    "X": ([[(0, 0), (1, 1)], [(1, 0), (0, 1)]], .8),
    "Y": ([[(0, 0), (.5, .5), (1, 0)], [(.5, .5), (.5, 1)]], .8),
    "Z": ([[(0, 0), (1, 0), (0, 1), (1, 1)]], .76),
    "0": ([[(.5 + .45 * _m.cos(_TAU * i / 20), .5 + .5 * _m.sin(_TAU * i / 20)) for i in range(21)]], .65),
    "1": ([[(.25, .2), (.55, 0), (.55, 1)], [(.25, 1), (.85, 1)]], .55),
    "2": ([[(.05, .2), (.25, 0), (.75, 0), (.95, .2), (.95, .4), (0, 1), (1, 1)]], .65),
    "3": ([[(.05, .1), (.3, 0), (.75, 0), (.95, .2), (.9, .4), (.5, .5), (.9, .6), (.95, .8), (.75, 1), (.3, 1), (.05, .9)]], .65),
    "4": ([[(.75, 1), (.75, 0), (0, .7), (1, .7)]], .65),
    "5": ([[(.9, 0), (.15, 0), (.05, .45), (.6, .4), (.95, .6), (.95, .8), (.7, 1), (.25, 1), (.05, .9)]], .65),
    "6": ([[(.85, .05), (.5, 0), (.15, .2), (.05, .6), (.15, .9), (.5, 1), (.85, .9), (.95, .7), (.8, .5), (.45, .45), (.1, .6)]], .65),
    "7": ([[(0, 0), (1, 0), (.35, 1)]], .62),
    "8": ([[(.5, .5), (.15, .38), (.1, .15), (.3, 0), (.7, 0), (.9, .15), (.85, .38), (.5, .5), (.1, .65), (.05, .85), (.3, 1), (.7, 1), (.95, .85), (.9, .65), (.5, .5)]], .65),
    "9": ([[(.9, .4), (.55, .55), (.15, .45), (.05, .25), (.2, .05), (.55, 0), (.9, .2), (.95, .5), (.8, .85), (.45, 1), (.15, .95)]], .65),
    "-": ([[(.1, .55), (.9, .55)]], .5),
    "·": ([[(.45, .5), (.55, .5)]], .35),
    ".": ([[(.45, .95), (.55, .95)]], .3),
    ",": ([[(.5, .9), (.35, 1.15)]], .3),
    ":": ([[(.5, .3), (.5, .32)], [(.5, .9), (.5, .92)]], .3),
    "'": ([[(.5, 0), (.4, .25)]], .25),
    "/": ([[(1, 0), (0, 1)]], .55),
    "&": ([[(1, 1), (.2, .35), (.25, .08), (.5, 0), (.7, .1), (.7, .3), (.1, .7), (.15, .95), (.5, 1), (.85, .7)]], .8),
    "°": ([[(.3 + .2 * _m.cos(_TAU * i / 10), .15 + .15 * _m.sin(_TAU * i / 10)) for i in range(11)]], .45),
    "%": ([[(1, 0), (0, 1)], [(.2 + .15 * _m.cos(_TAU * i / 10), .18 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)],
           [(.8 + .15 * _m.cos(_TAU * i / 10), .82 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)]], .75),
    " ": ([], .45),
}


def st_text_w(text, h, track=.32):
    t = [ch if ch in _GL else " " for ch in text.upper()]
    return sum(_GL[ch][1] * h * .78 for ch in t) + track * h * max(0, len(t) - 1)


def st_letter(text, h, centre=None, cx=0., cy=0., track=.32, sw=None, fit=None):
    """Monoline engraved capitals h tall, centred on (cx, cy) or along the polyline `centre`.
    fit shrinks the lettering to that width. -> svg path."""
    t = [ch if ch in _GL else " " for ch in text.upper()]
    if fit:
        tw = st_text_w(text, h, track)
        if tw > fit:
            h *= fit / tw
    tw = st_text_w(text, h, track)
    if centre:
        acc = [0.]
        for i in range(1, len(centre)):
            acc.append(acc[-1] + _m.dist(centre[i], centre[i - 1]))
        tot = acc[-1]

        def at(sv):
            sv = max(0., min(tot, sv))
            for i in range(1, len(acc)):
                if acc[i] >= sv:
                    f = (sv - acc[i - 1]) / max(1e-6, acc[i] - acc[i - 1])
                    p0, p1 = centre[i - 1], centre[i]
                    return p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, _m.atan2(p1[1] - p0[1], p1[0] - p0[0])
            return centre[-1][0], centre[-1][1], 0.
        pos = (tot - tw) / 2
    else:
        pos = -tw / 2
    d = []
    for ch in t:
        strokes, wf = _GL[ch]
        gw = wf * h * .78
        if centre:
            mx, my, a = at(pos + gw / 2)
        else:
            mx, my, a = cx + pos + gw / 2, cy, 0.
        ca, sa = _m.cos(a), _m.sin(a)
        for st in strokes:
            pts = []
            for gx, gy in st:
                lx, ly = (gx - .5) * gw, (gy - .5) * h
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            d.append(_C._d(pts, tol=.05))
        pos += gw + track * h
    w = sw or (1. if h >= 7 else .5)
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width="{_C._n(w)}"/>'


def st_tablet_text(tx, ty, tw, th, lines):
    """Lines of lettering in a tablet, over a dotted Or ground cut back behind each line."""
    o = [f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>']
    n = len(lines)
    lh = min(th / (n * 1.6 + .4), 11.)
    for i, ln in enumerate(lines):
        cy = ty + th * (i + .5) / n
        w = min(tw - 8, st_text_w(ln, lh) + lh * 1.4)
        o.append(f'<path d="{st_rect_d(tx + (tw - w) / 2, cy - lh * .85, w, lh * 1.7)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
        o.append(st_letter(ln, lh, cx=tx + tw / 2, cy=cy, fit=tw - 12))
    return "".join(o)


def st_doc(w, h, body):
    return _C.svg_doc(w, h, _ST_DEFS + body)
# ==== END STUDIO FRAME ==========================================================================
# ==== STUDIO LAYOUTS ============================================================================


def _in_ell(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1


def st_border(w, h, inset=3.):
    """The plate's own gold-line border and an inner row of beads, all four edges."""
    return (st_wire(st_rect_d(inset, inset, w - 2 * inset, h - 2 * inset))
            + st_beads(st_rect_d(inset + 4.5, inset + 4.5, w - 2 * inset - 9, h - 2 * inset - 9), 3.5, 1.))


def _st_clip_runs(pl, mask, x0, y0, W, H, out, step=1.5):
    """_clip_runs at a 1.5 px test step (lines are cut cleanly enough; half the work)."""
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L = _m.hypot(dx, dy)
        if L > step:
            k = int(L / step)
            for j in range(1, k + 1):
                t = j / (k + 1)
                pts.append((px + dx * t, py + dy * t))
        pts.append(q)
        px, py = q
    run = []
    for (x, y) in pts:
        xi, yi = int(x - x0), int(y - y0)
        if 0 <= xi < W and 0 <= yi < H and mask[yi][xi]:
            if len(run) > 1:
                out.append(run)
            run = []
        else:
            run.append((x, y))
    if len(run) > 1:
        out.append(run)


class StCanvas(_C.Canvas):
    """The house Canvas, emitting with a slightly coarser simplification for the fine cuts so a
    packed field of scroll stays inside the byte budget (the eye cannot see 0.15 px)."""

    def svg(self, tol_fill=.95, tol_hair=.65, tol_line=.55):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for wd, lines in strokes.items():
                for pl in lines:
                    _st_clip_runs(pl, mask, x0, y0, W, H, out[wd])
            if ow:
                for poly in polys:
                    _st_clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                _C._fill_mask(poly, mask, x0, y0, W, H)
        res = []
        pen = _C._Pen()
        for polys, _, _ in self.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="#fff" stroke="none"/>')
        for wd in (.5, 1., 1.5):
            if out[wd]:
                pen = _C._Pen()
                for pl in out[wd]:
                    if len(pl) > 2 or _m.dist(pl[0], pl[-1]) > .6:
                        pen.add(pl, False, tol_hair if wd < 1 else tol_line)
                res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_C._n(wd * 4)}"/>')
        return "".join(res)


def _scroll_layer(field, uid, x, y, w, h, egg=None, egg_gen=2):
    cv = StCanvas()
    field.draw(cv, egg, egg_gen)
    return st_clip_rect(uid, x, y, w, h, cv.svg())


def st_band(w, h, seed, hk):
    """h < 110: a carved band. An inlaid medallion holds the subject; from it a stem runs to
    either edge, the fine scroll branching off it to fill the band."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2 + hk.get("dx", 0.), h / 2
    ry = max(4., h / 2 - 8.5) if h >= 40 else max(4., h / 2 - 7.2)
    rx = min(w * .2, max(ry * 1.5, ry * hk.get("aspect", 1.7)))
    if h < 40:
        ins = 5.
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 2 < y < fy1 + 2 and not _in_ell(x, y, cx, cy, rx + 12, ry + 12)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(3.5 if h < 40 else 4.5, gh * .12), rmax=max(4.6, gh * .32), seed=seed, slack=.9)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        L = (w / 2 - rx - 14) * 1.05
        x0 = cx + sd * (rx + 9)
        a = 0. if sd > 0 else _PI
        pts = []
        n = int(L / 2)
        for i in range(n + 1):
            u = i / n
            pts.append((x0 + sd * L * u, cy + gh * .18 * _m.sin(u * _TAU * (L / (gh * 2.2)) + (0 if sd > 0 else 1.3))))
        F.stem(pts, 1.6, 1.0, leaves=False)
    F.grow(8)
    F.fill(fx0 - 4, fy0 - 2, fx1 - fx0 + 8, fy1 - fy0 + 4, 3., hk.get("max_items", 160))
    o.append(_scroll_layer(F, f"s2b{w}x{h}", 0, 0, w, h, hk.get("egg"), 1))
    o.append(st_border(w, h, 1.5 if h < 40 else 3.))
    m, fld = st_medallion(cx, cy, rx, ry)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2b{w}x{h}v", fld, hk["field"](fld, "band") + st_rim(fld, hk.get("rim", 5.))))
    return "".join(o)


def st_medium(w, h, seed, hk):
    """110-260: the medallion between two panels of fine scroll, each grown from a stem that
    sweeps out of the medallion's foot; gold-line border and beading round the plate."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2, h / 2
    shape = hk.get("shape", "oval")
    ded = 15. if hk.get("dedication") else 0.
    ry = h / 2 - ins - 6
    rx = min(w * hk.get("cw", .21), ry * hk.get("aspect", 1.45))
    if shape == "roundel":
        rx = ry
    if shape == "arch":
        rx = min(rx, ry * 1.1)
    ph = (seed % 97) * .07
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 3 < y < fy1 + 3 and not st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph) and not (ded and abs(x - cx) < 34 and y > h - ins - 2 * ded - 6)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(6., gh * .055), rmax=min(26., gh * .2), seed=seed, slack=.88)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        a0 = _PI / 2 + sd * .25 * _PI
        x0, y0 = cx + (rx + 10) * _m.cos(_PI / 2 - sd * .9), cy + (ry + 10) * _m.sin(_PI / 2 - sd * .9)
        head = 0. if sd > 0 else _PI
        L = (w / 2 - rx - 20)
        k = -sd * .9 / L
        F.stem(st_sweep(x0, y0, head + sd * .35, L * 1.05, k * 1.5, -k * 1.2), 2., 1.1)
        x1, y1 = cx + (rx + 10) * _m.cos(-_PI / 2 + sd * .9), cy + (ry + 10) * _m.sin(-_PI / 2 + sd * .9)
        F.stem(st_sweep(x1, y1, head - sd * .35, L * .8, -k * 1.5, k), 1.8, 1.)
    F.grow(10)
    F.fill(fx0 - 4, fy0 - 3, fx1 - fx0 + 8, fy1 - fy0 + 6, 4., hk.get("max_items", 260))
    o.append(_scroll_layer(F, f"s2m{w}x{h}", 0, 0, w, h, hk.get("egg"), 2))
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2m{w}x{h}v", fld, hk["field"](fld, "medium") + st_rim(fld, hk.get("rim", 9.))))
    if ded:
        o.append(st_dedication(cx, h - 3, 2 * ded))
    if hk.get("crest"):
        o.append(hk["crest"](cx, cy - ry - 2, min(14., ins + 4), "medium"))
    return "".join(o)


def st_pedestal(x, y, w, h, seed, hk, uid):
    """The base: knurled cornice, a frieze panel (gold-line border, fine scroll from the centre
    out) round a sunk tablet, a second knurled bar, beading. -> svg"""
    o = []
    kb = 6.
    o.append(_C.knurled_bar(x, y, w, kb))
    py0, py1 = y + kb + 1, y + h - kb - 5
    ph = py1 - py0
    tw, th = min(w * .5, 300.), ph - 10
    tx, ty = x + (w - tw) / 2, py0 + 5
    o.append(st_matte(st_rect_d(x, py0, w, ph)))

    def inside(px, py):
        return x + 6 < px < x + w - 6 and py0 + 2 < py < py1 - 2 and not (tx - 8 < px < tx + tw + 8)
    F = ScrollField(inside, rmin=max(4.5, ph * .16), rmax=ph * .4, seed=seed + 11, slack=.9)
    for sd in (-1, 1):
        xs = tx - 6 if sd < 0 else tx + tw + 6
        L = (w - tw) / 2 - 14
        pts = [(xs + sd * L * i / 30, py0 + ph / 2 + ph * .15 * _m.sin(i / 30 * _TAU * (L / (ph * 2)))) for i in range(31)]
        F.stem(pts, 1.4, .9, leaves=False)
    F.grow(6)
    F.fill(x + 6, py0 + 2, w - 12, ph - 4, 3., 120)
    o.append(_scroll_layer(F, uid + "p", x, py0, w, ph))
    o.append(st_wire(st_rect_d(x + 2.5, py0 + 1.5, w - 5, ph - 3)))
    o.append(f'<path d="{st_rect_d(tx - 3, ty - 3, tw + 6, th + 6)}" fill="#000"/>')
    o.append(st_beads(st_rect_d(tx - 1.5, ty - 1.5, tw + 3, th + 3), 3.5, 1.))
    o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="#fff" stroke="none"/>')
    if hk.get("tablet"):
        o.append(hk["tablet"](tx, ty, tw, th))
    elif hk.get("tablet_lines"):
        o.append(st_tablet_text(tx, ty, tw, th, hk["tablet_lines"]))
    else:
        o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>')
    o.append(_C.knurled_bar(x + 4, py1, w - 8, kb))
    o.append(st_beads(f"M{_C._n(x + 3)},{_C._n(y + h - 2.5)}h{_C._n(w - 6)}", 3.5, 1.))
    return "".join(o)


def st_tall(w, h, seed, hk):
    """> 260: the full plate. The scene in a great inlaid medallion (an arched panel on a section
    front, like the binding) over a ribbon banner and the dedication cartouche with Parker's arms
    (placeholder); fine scroll grown from a stem rising either side of the arms packs the field;
    a pedestal; under it, when tall, a frieze of the same scroll."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    ped_h = min(max(h * .13, 40), 62.)
    fz = min(max(h * .09, 30), 50.) if (h >= 440 and hk.get("frieze", True)) else 0.
    py = h - ped_h - fz - ins * (1 if fz else .6)
    shape = hk.get("shape") or ("arch" if hk.get("arch") else "oval")
    arch = shape == "arch"
    rx = w * hk.get("cw", .3)
    top = ins + 12
    bot = py - (62 if py > 300 else 46)
    ry = (bot - top) / 2
    if shape == "roundel":
        rx = ry = min(rx * 1.25, ry)
        top = bot - 2 * ry
    cx, cy = w / 2, top + ry
    ph = (seed % 97) * .07
    ay = bot + 4
    ary = min(26., (py - ay) * .4)
    arx = ary * 1.25
    aby = py - ary - 8

    def inside(x, y):
        if not (ins - 4 < x < w - ins + 4 and ins - 3 < y < py - 3):
            return False
        if st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph):
            return False
        if abs(x - cx) < rx * 1.05 + 10 and bot - 4 < y < bot + 16:
            return False
        if _in_ell(x, y, cx, aby, arx + 10, ary + 9):
            return False
        return True
    F = ScrollField(inside, rmin=hk.get("rmin", 8.), rmax=min(hk.get("rmax", 30.), w * .058), seed=seed, slack=.88)
    for sd in (-1, 1):
        x0, y0 = cx + sd * (arx + 8), aby + ary * .3
        F.stem(st_sweep(x0, y0, (0. if sd > 0 else _PI) - sd * .25, (py - ins) * .55 + w * .1,
                        -sd * .004, -sd * .022), 3., 1.6)
        F.stem(st_sweep(cx + sd * (rx * .7), ins + 4, (0. if sd > 0 else _PI) + sd * .15, w * .3, sd * .004, sd * .02), 2.6, 1.4)
    F.grow(4)
    F.fill(ins - 4, ins - 3, w - 2 * ins + 8, py - ins, 6., hk.get("max_items", 340))
    uid = f"s2t{w}x{h}"
    o.append(_scroll_layer(F, uid, 0, 0, w, py, hk.get("egg"), 2))
    if fz:
        fy0 = py + ped_h + 2
        fh = h - ins - fy0

        def inside2(x, y):
            return ins - 4 < x < w - ins + 4 and fy0 < y < fy0 + fh and abs(x - w / 2) > fh * .7
        G = ScrollField(inside2, rmin=max(4.5, fh * .15), rmax=fh * .4, seed=seed + 5, slack=.9)
        for sd in (-1, 1):
            L = w / 2 - fh * .7 - 8
            G.stem([(w / 2 + sd * (fh * .7 + L * i / 40), fy0 + fh / 2 + fh * .17 * _m.sin(i / 40 * _TAU * (L / (fh * 2.1)))) for i in range(41)],
                   1.5, 1., leaves=False)
        G.grow(6)
        G.fill(ins - 4, fy0, w - 2 * ins + 8, fh, 4., 140)
        o.append(_scroll_layer(G, uid + "f", 0, fy0, w, fh, hk.get("egg2"), 1))
        cvp = _C.Canvas()
        _C.palmette(w / 2, fy0 + 1, fh * .8, False, seed, cv=cvp)
        o.append(cvp.svg())
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(uid + "v", fld, hk["field"](fld, "tall") + st_rim(fld, hk.get("rim", 14.))))
    if hk.get("crest"):
        o.append(hk["crest"](cx, top - 3, top - 4, "tall"))
    bh = min(16., (py - bot) * .4)
    bs, centre = _C.ribbon_banner(cx, bot + 2, rx * 2.5, bh, .035, seed)
    o.append(bs)
    if hk.get("banner"):
        o.append(hk["banner"](centre, bh))
    elif hk.get("motto"):
        o.append(st_letter(hk["motto"], bh * .55, centre=centre[4:-4], fit=_m.dist(centre[4], centre[-5]) * .92))
    if hk.get("dedication"):
        o.append(st_arms(cx, aby, arx, ary))
    else:
        # not a front: a small inlaid cartouche carries the page's own device instead of the arms
        em, efl = st_medallion(cx, aby, arx * .78, ary * .78)
        o.append(em)
        o.append(f'<path d="{st_poly_d(efl)}" fill="url(#s2o)" stroke="none"/>')
        if hk.get("egg"):
            ecv = StCanvas()
            hk["egg"](ecv, cx, aby, ary * .62)
            o.append(ecv.svg())
    o.append(st_pedestal(0, py, w, ped_h, seed, hk, uid))
    return "".join(o)


def st_dissolve(poly, seed, depth=9., step=1.25):
    """Bewick's dissolving edge: white broken rings laid over the outer few px of a vignette, the
    white taking more of each ring toward the rim, so the cut lines crumble out into the paper."""
    rng = _rnd.Random(seed)
    n = int(depth / step)
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    o = []
    for k in range(n):
        f = 1 - k / n                       # 1 at the rim, toward 0 inside
        g = k * step + .4
        ring = []
        for (x, y) in poly:
            dx, dy = x - cx, y - cy
            L = _m.hypot(dx, dy) or 1
            ring.append((x - dx / L * g, y - dy / L * g))
        segs = []
        for _ in range(4):
            on = rng.uniform(1, 5) * (.3 + 1.9 * f * f)
            off = rng.uniform(3, 9) * (1.3 - f)
            segs += [on, max(.3, off)]
        da = " ".join(_C._n(v) for v in segs)
        o.append(f'<path d="{st_poly_d(ring)}" fill="none" stroke="#fff" stroke-width="{_C._n(step + .25)}" '
                 f'stroke-dasharray="{da}" stroke-dashoffset="{_C._n(rng.uniform(0, 40))}"/>')
    o.append(f'<path d="{st_poly_d(poly)}" fill="none" stroke="#fff" stroke-width="2"/>')
    return "".join(o)


def st_ragged(poly, seed, depth=7.):
    """The vignette's dissolving rim as a cut: the outline resampled finely and bitten inward by
    layered noise and sharp nicks, so the scene's lines end raggedly in the surrounding ground
    (nothing is painted over them; outside the cut the plate stays transparent)."""
    rng = _rnd.Random(seed)
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    pts = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        L = _m.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / 1.3))
        for j in range(k):
            pts.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    m = len(pts)
    ph = [rng.uniform(0, 6.3) for _ in range(4)]
    out = []
    for i, (x, y) in enumerate(pts):
        u = i / m * _TAU
        d = depth * (.45 + .2 * _m.sin(u * 7 + ph[0]) + .15 * _m.sin(u * 19 + ph[1]) + .1 * _m.sin(u * 53 + ph[2]))
        if rng.random() < .22:
            d += depth * rng.uniform(.2, .75)
        d = max(.5, d)
        dx, dy = x - cx, y - cy
        L = _m.hypot(dx, dy) or 1
        out.append((x - dx / L * d, y - dy / L * d))
    return out


def st_vignette(w, h, seed, hk):
    """The free-standing vignette: the scene itself is the plate, cut to its shape and crumbling
    out into the paper at the rim; any ornament is drawn from the subject (hk['frame'])."""
    shape = hk.get("shape", "oval")
    pad = hk.get("pad", 2.)
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - pad, h / 2 - pad
    rx = min(rx, ry * hk.get("max_aspect", 3.2))
    ph = (seed % 97) * .07
    fld = hk["shape_fn"](cx, cy, rx, ry) if hk.get("shape_fn") else st_shape_pts(shape, cx, cy, rx, ry, 0., 160, ph)
    if shape == "irregular" and not hk.get("shape_fn"):
        s = max(max(abs(q[0] - cx) / (w / 2 - pad) for q in fld), max(abs(q[1] - cy) / (h / 2 - pad) for q in fld))
        fld = [(cx + (q[0] - cx) / s, cy + (q[1] - cy) / s) for q in fld]
    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    o = []
    if hk.get("under"):
        o.append(hk["under"](cx, cy, rx, ry, fld, mode))
    rag = st_ragged(fld, seed, hk.get("dissolve", min(7., 3 + min(w, h) * .025)))
    o.append(st_clip_poly(f"s2v{w}x{h}", rag, hk["field"](fld, mode)))
    if hk.get("frame"):
        o.append(hk["frame"](cx, cy, rx, ry, fld, mode))
    if hk.get("dedication") and h >= 110:
        dh = min(30., h * .16)
        o.append(st_dedication(cx, h - 1.5, dh))
    return "".join(o)


def st_plate(w, h, seed, hk):
    base = _C.Canvas
    if hk.get("vignette"):
        return _st_plate(w, h, seed, hk)
    _C.Canvas = StCanvas
    try:
        return _st_plate(w, h, seed, hk)
    finally:
        _C.Canvas = base


def _st_plate(w, h, seed, hk):
    if hk.get("vignette"):
        body = st_vignette(w, h, seed, hk)
    elif h <= 72 and w <= 110 and hk.get("device", True):
        body = st_device(w, h, seed, hk)
    elif h < 110:
        body = st_band(w, h, seed, hk)
    elif h <= 260:
        body = st_medium(w, h, seed, hk)
    else:
        body = st_tall(w, h, seed, hk)
    return st_doc(w, h, body)
# ==== END STUDIO LAYOUTS ========================================================================


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 11

    def field(fld, mode):
        xs = [p[0] for p in fld]
        ys = [p[1] for p in fld]
        fx, fy = min(xs), min(ys)
        if mode == "band":
            sc = scene(fx, fy, max(xs) - fx, max(ys) - fy, _d(fld, True, 0), C._uid("gs", w, h, mode), date, seed, "mini")
        else:
            sc = hedge_scene(fx, fy, max(xs) - fx, max(ys) - fy, _d(fld, True, 0), C._uid("gs", w, h, mode), date, seed)
        return sc

    hk = dict(vignette=True, pad=3., max_aspect=2.6, shape_fn=hedge_shape,
                            shape="irregular", dedication=True, frieze=False, field=field, egg=egg_dog, aspect=2.6, cw=.26, rmin=9.5, rmax=30., motto="SAUVIE ISLAND",
              tablet_lines=["WALK THE LAND · BURN DAY · BIRDS", "SOW · BLOOMS · MUSHROOMS"])
    return st_plate(w, h, seed, hk)
