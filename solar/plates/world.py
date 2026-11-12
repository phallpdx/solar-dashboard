"""World / Thailand plate: "Over in Bangkok" -- cloudy, rain about, and today's phrase aroi, "delicious".
The vignette is a Bangkok floating market under monsoon cloud: a Thai ubosot with chofa and bai raka
gables and a bell chedi on the far bank, coconut palms, a rain squall slanting out of the clouds, and
on the klong a noodle vendor's sampan with its steaming pot (aroi!) and a fruit boat poled by a woman
in a ngob hat. Easter egg: a small white elephant on the far bank, and a "P" on the noodle pot.
House frame (engraving_codex) re-laid so the vignette fills the whole cartouche field, with kranok
flames worked into the corner of each volute group."""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import _n, _d, Canvas, hatch_poly

TAU = 2 * math.pi


# ------------------------------------------------------------------------------------ geometry
def _pip(x, y, poly):
    ins = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            ins = not ins
        j = i
    return ins


def _clip_in(lines, poly, keep=True):
    """Split polylines into the parts inside (keep=True) or outside poly, 1px resampling."""
    out = []
    for pl in lines:
        pts = [pl[0]]
        for a, b in zip(pl, pl[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            k = max(1, int(L))
            for j in range(1, k + 1):
                pts.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
        run = []
        for p in pts:
            if _pip(p[0], p[1], poly) == keep:
                run.append(p)
            else:
                if len(run) > 1:
                    out.append(run)
                run = []
        if len(run) > 1:
            out.append(run)
    return out


def _arc(cx, cy, rx, ry, a0, a1, n=None):
    n = n or max(4, int(abs(a1 - a0) * max(rx, ry) / 2) + 2)
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _bez(p0, p1, p2, p3, n=10):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def _cpath(d, x0, y0, s, flip=False):
    """Flatten an M/C/L/Z path (absolute) into a point list, scaled by s about the origin, placed at x0,y0."""
    import re
    tok = re.findall(r"[MCLZ]|-?\d*\.?\d+", d)
    pts, cur, i, cmd = [], (0, 0), 0, None
    nums = []

    def P(a, b):
        return (x0 + (-a if flip else a) * s, y0 + b * s)
    while i < len(tok):
        t = tok[i]
        if t in "MCLZ":
            cmd = t
            i += 1
            continue
        if cmd == "M":
            cur = (float(tok[i]), float(tok[i + 1]))
            pts.append(P(*cur))
            i += 2
            cmd = "L"
        elif cmd == "L":
            cur = (float(tok[i]), float(tok[i + 1]))
            pts.append(P(*cur))
            i += 2
        elif cmd == "C":
            c1 = (float(tok[i]), float(tok[i + 1]))
            c2 = (float(tok[i + 2]), float(tok[i + 3]))
            e = (float(tok[i + 4]), float(tok[i + 5]))
            pts.extend(P(*q) for q in _bez(cur, c1, c2, e, 8)[1:])
            cur = e
            i += 6
        else:
            i += 1
    return pts


def _blk(polys):
    return "".join(_d(p, True, .15) for p in polys if len(p) > 2)


def _hrules(poly, pitch, phase=0., y0=-1e9, y1=1e9, dash=None, rnd=None):
    """Horizontal hairlines clipped to poly and to the band y0..y1, optionally broken into dashes."""
    out = []
    for seg in hatch_poly(poly, 0, pitch, phase):
        (ax, ay), (bx, by) = seg
        if not (y0 <= ay <= y1):
            continue
        if dash and rnd:
            x = ax + rnd.uniform(0, dash[1])
            while x < bx:
                e = min(bx, x + rnd.uniform(*dash))
                if e - x > .8:
                    out.append([(x, ay), (e, ay)])
                x = e + rnd.uniform(1.2, 3.)
        else:
            out.append(seg)
    return out


# ------------------------------------------------------------------------------------ motifs
def _cloud(cv, cx, by, wd, ht, rnd, dark=False):
    """A cumulus bank built of billows, back row then front row, each a white dome with a flat base,
    outlined, with a crescent of concentric contour lines on its shadowed lower right and a ruled
    underside; a rain cloud gets closer lines and a darker belly."""
    nb = max(2, int(round(wd / (ht * .72))))
    rows = []
    for i in range(nb):
        t = (i + .5) / nb
        prof = .55 + .45 * math.sin(math.pi * t)
        r = ht * .62 * prof * rnd.uniform(.88, 1.08)
        rows.append((cx - wd / 2 + wd * t + rnd.uniform(-.12, .12) * wd / nb, by - r * .62, r))
    for i in range(nb - 1):
        x = (rows[i][0] + rows[i + 1][0]) / 2 + rnd.uniform(-2, 2)
        r = min(rows[i][2], rows[i + 1][2]) * rnd.uniform(.62, .74)
        rows.append((x, by - r * .32, r))
    lo = []
    pitch = 1.5 if dark else 2.
    for bx, bcy, r in rows:
        ring = [(bx + r * math.cos(a), min(by, bcy + r * math.sin(a))) for a in [TAU * k / 40 for k in range(40)]]
        cv.obj([ring], 1.)
        arcs = []
        rr = r - pitch
        while rr > r * .22:
            f = 1 - (r - rr) / (r * .78)
            sp = math.pi * (.78 if dark else .62) * f ** .7
            arcs.append(_arc(bx, bcy, rr, rr, math.radians(25) - sp, math.radians(25) + sp))
            rr -= pitch
        cv.hair(_clip_in(arcs, ring))
        cv.hair(_hrules(ring, 1.5, .25, by - r * (.55 if dark else .3), by + 1))
        if dark:
            cv.hair(_hrules(ring, 3, 1., bcy - r, by))
        lo.append(ring)
    return lo


def _rain(cv, x0, x1, y0, y1, rnd, slant=.35):
    cv.obj([], 0)
    lines = []
    x = x0
    while x < x1:
        y = y0 + rnd.uniform(0, 4)
        while y < y1:
            L = rnd.uniform(3, 7)
            e = min(y1, y + L)
            lines.append([(x - (y - y0) * slant, y), (x - (e - y0) * slant, e)])
            y = e + rnd.uniform(2, 4.5)
        x += rnd.choice((2.5, 3, 3.5))
    cv.hair(lines)


def _treeline(cv, x0, x1, yb, ht, rnd):
    top = []
    x = x0
    while x <= x1:
        top.append((x, yb - ht * (.45 + .35 * abs(math.sin(x * .21)) + .2 * rnd.random())))
        x += 2.5
    poly = top + [(x1, yb), (x0, yb)]
    cv.obj([poly], .5)
    cv.hair(hatch_poly(poly, 0, 1.5, .3))
    cv.hair(hatch_poly(poly, 70, 3))
    return poly


def _palm(cv, x, yb, ht, lean, rnd):
    """Coconut palm: a curved ringed trunk and drooping feathered fronds."""
    tx, ty = x + lean * ht, yb - ht
    trunk = _bez((x, yb), (x + lean * ht * .1, yb - ht * .5), (tx - lean * ht * .2, ty + ht * .2), (tx, ty), 16)
    w0 = max(1.2, ht * .045)
    L = [(p[0] - w0 * (1 - .4 * i / 16), p[1]) for i, p in enumerate(trunk)]
    R = [(p[0] + w0 * (1 - .4 * i / 16), p[1]) for i, p in enumerate(trunk)]
    poly = L + R[::-1]
    cv.obj([poly], 1.)
    cv.hair([[L[i], R[i]] for i in range(1, 16, 1)])
    cv.hair(_clip_in([[(p[0] + w0 * .3, p[1]), (p[0] + w0, p[1])] for p in trunk], poly))
    for k in range(7):
        a = math.radians(-170 + k * 27 + rnd.uniform(-6, 6))
        fl = ht * rnd.uniform(.38, .5)
        droop = .9 if abs(math.cos(a)) > .5 else .4
        ex, ey = tx + fl * math.cos(a), ty + fl * math.sin(a) * .5 + fl * droop * .6
        mid = (tx + fl * .55 * math.cos(a), ty + fl * .55 * math.sin(a) - fl * .15)
        rib = _bez((tx, ty), mid, mid, (ex, ey), 10)
        cv.line(rib)
        leaf = []
        for i in range(2, 10):
            px, py = rib[i]
            qx, qy = rib[i + 1]
            dx, dy = qx - px, qy - py
            l = math.hypot(dx, dy) or 1
            nx, ny = -dy / l, dx / l
            sz = fl * .16 * (1 - i / 12)
            for sgn in (1, -1):
                leaf.append([(px, py), (px + (nx * sgn + dx / l * .6) * sz + 0, py + (ny * sgn + dy / l * .6) * sz + sz * .5)])
        cv.hair(leaf)


def _chedi(cv, blk, cx, yb, ht):
    """Bell-shaped chedi: three base tiers, the bell, a harmika, a ringed spire and pinnacle."""
    s = ht / 100.
    y = yb
    for hw, th in ((22, 5), (18, 5), (14.5, 5)):
        p = [(cx - hw * s, y), (cx - hw * s, y - th * s), (cx + hw * s, y - th * s), (cx + hw * s, y)]
        cv.obj([p], 1.)
        cv.hair(hatch_poly(p, 90, 1.5) and [q for q in hatch_poly(p, 90, 1.5) if q[0][0] > cx + hw * s * .35])
        cv.hair([[(cx - hw * s, y - th * s * .45), (cx + hw * s, y - th * s * .45)]])
        y -= th * s
    by = y
    bh = 30 * s
    bell = []
    for i in range(25):
        t = i / 24
        yy = by - bh * t
        hw = 13.5 * s * (1 - t ** 2.4) ** .55 + 3 * s * t
        bell.append((cx - hw, yy))
    bell = bell + [(2 * cx - p[0], p[1]) for p in bell[::-1]]
    cv.obj([bell], 1.)
    cv.hair([q for q in hatch_poly(bell, 90, 1.5) if q[0][0] > cx + 3 * s])
    cv.hair([q for q in hatch_poly(bell, 90, 3) if cx - 4 * s < q[0][0] <= cx + 3 * s])
    cv.hair([_arc(cx, by - bh * f, 13.5 * s * (1 - f ** 2.4) ** .55 + 3 * s * f, 1.2 * s, 0, math.pi) for f in (.15, .5)])
    y = by - bh
    hp = [(cx - 6 * s, y), (cx - 6 * s, y - 5 * s), (cx + 6 * s, y - 5 * s), (cx + 6 * s, y)]
    cv.obj([hp], 1.)
    cv.hair([q for q in hatch_poly(hp, 90, 1.5) if q[0][0] > cx])
    y -= 5 * s
    sh = 42 * s
    sp = [(cx - 4.5 * s, y), (cx - .6 * s, y - sh), (cx + .6 * s, y - sh), (cx + 4.5 * s, y)]
    cv.obj([sp], 1.)
    cv.hair([q for q in hatch_poly(sp, 90, 1.5) if q[0][0] > cx + .3])
    rings = []
    k = 0
    yy = y - 2.4 * s
    while yy > y - sh * .7:
        hw = 4.5 * s * (1 - (y - yy) / sh)
        rings.append([(cx - hw, yy), (cx + hw, yy + .4)])
        yy -= 2.4 * s
        k += 1
    cv.hair(rings)
    blk.append(_arc(cx, y - sh * .78, 1.3 * s, 2.2 * s, 0, TAU, 12))
    cv.obj([], 0)
    cv.hair([[(cx, y - sh), (cx, y - sh - 9 * s)]])


def _ubosot(cv, blk, cx, yb, wd, rnd):
    """Front elevation of a Thai ordination hall: platform, colonnade, two tiers of shoulder roofs and
    the steep main gable with bai raka teeth, a chofa horn at the apex and hang hong at the eaves; the
    gable face (na ban) cut away dark around a carved white deity-wheel."""
    s = wd / 100.
    # platform
    y = yb
    pl = [(cx - 50 * s, y), (cx - 47 * s, y - 6 * s), (cx + 47 * s, y - 6 * s), (cx + 50 * s, y)]
    cv.obj([pl], 1.)
    cv.hair(hatch_poly(pl, 0, 1.5, .5))
    cv.hair([[(cx + k * 6 * s, y - 6 * s), (cx + k * 6 * s, y)] for k in range(-7, 8)])
    y -= 6 * s
    # colonnade
    wh = 24 * s
    wall = [(cx - 40 * s, y), (cx - 40 * s, y - wh), (cx + 40 * s, y - wh), (cx + 40 * s, y)]
    cv.obj([wall], 1.)
    cv.hair(hatch_poly(wall, 90, 1.5))
    cols = []
    for k in range(-3, 4):
        x = cx + k * 12.5 * s
        c = [(x - 2.3 * s, y), (x - 2.3 * s, y - wh), (x + 2.3 * s, y - wh), (x + 2.3 * s, y)]
        cols.append(c)
    cv.obj(cols, 1.)
    for c in cols:
        x0 = c[0][0]
        cv.hair([[(x0 + 3 * s, c[0][1]), (x0 + 3 * s, c[1][1])], [(x0 + 3.9 * s, c[0][1]), (x0 + 3.9 * s, c[1][1])]])
        cv.hair([[(x0 - .8 * s, c[1][1] + 2.5 * s), (x0 + 5.4 * s, c[1][1] + 2.5 * s)]])
        # lotus capital
        cv.hair(_arc(x0 + 2.3 * s, c[1][1] + 1.2 * s, 3 * s, 1.6 * s, 0, math.pi))
    for k in (-1, 0, 1):
        x = cx + (k * 12.5 + 6.25 * (1 if k >= 0 else -1)) * s if k else cx + 6.25 * s
    for k in (-2, -1, 0, 1):   # doors / windows between columns: black arched openings
        x = cx + (k + .5) * 12.5 * s
        top = y - wh * (.75 if k in (-1, 0) else .62)
        blk.append([(x - 3.4 * s, y - 1)] + _arc(x, top + 3.4 * s, 3.4 * s, 4 * s, math.pi, TAU, 10) + [(x + 3.4 * s, y - 1)])
    y -= wh
    # lower shoulder roof (tier 1), then upper shoulder (tier 2)
    eave1 = y + 2 * s
    for (ow, iw, yb1, yt1) in ((50, 30, eave1, y - 9 * s), (38, 24, y - 7 * s, y - 17 * s)):
        for sg in (-1, 1):
            p = [(cx + sg * ow * s, yb1), (cx + sg * iw * s, yt1), (cx + sg * (iw - 4) * s, yt1), (cx + sg * (iw - 4) * s, yb1)]
            cv.obj([p], 1.)
            # tile courses parallel to the slope, a white border at the edge
            ang = math.degrees(math.atan2(yt1 - yb1, sg * (iw - ow) * s))
            cv.hair(hatch_poly(p, ang, 2, inset=0) if sg > 0 else hatch_poly(p, ang, 3))
            cv.line([(cx + sg * (ow - 2.2) * s, yb1 - .6 * s), (cx + sg * (iw - .4) * s, yt1 + .4 * s)])
            # hang hong: an upturned curl at the eave end
            hx, hy = cx + sg * ow * s, yb1
            cv.line(_bez((hx, hy), (hx + sg * 2.5 * s, hy + .5 * s), (hx + sg * 3.5 * s, hy - 1.5 * s), (hx + sg * 2.6 * s, hy - 3.6 * s), 8))
        eave = [(cx - (ow - 1) * s, yb1), (cx + (ow - 1) * s, yb1)]
        cv.obj([], 0)
        cv.line(eave)
    # main gable
    gw, gb, ga = 27 * s, y - 15 * s, y - 52 * s
    roof = [(cx - gw - 5 * s, gb + 3 * s), (cx, ga - 3 * s), (cx + gw + 5 * s, gb + 3 * s)]
    face = [(cx - gw, gb), (cx, ga), (cx + gw, gb)]
    # bai raka teeth along both rakes
    teeth = []
    for sg in (-1, 1):
        p0 = (cx + sg * (gw + 5 * s), gb + 3 * s)
        p1 = (cx, ga - 3 * s)
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
        nx, ny = -uy * sg * -1, ux * sg * -1
        if ny > 0:
            nx, ny = -nx, -ny
        k = 3 * s
        t = k
        while t < L - 6 * s:
            bx, by = p0[0] + ux * t, p0[1] + uy * t
            teeth.append([(bx - ux * 1.3 * s, by - uy * 1.3 * s), (bx + nx * 3 * s + ux * 1.2 * s, by + ny * 3 * s + uy * 1.2 * s),
                          (bx + ux * 1.3 * s, by + uy * 1.3 * s)])
            t += 3.4 * s
    cv.obj(teeth, .5)
    cv.hair([[q[0], q[1]] for q in teeth])
    cv.obj([roof + [(cx + gw, gb), (cx, ga), (cx - gw, gb)]], 1.)
    cv.hair(_clip_in([[(cx - gw - 5 * s + f * s, gb + 3 * s), (cx, ga - 3 * s + f * s)] for f in (1.6, 3.2)], roof))
    cv.hair(_clip_in([[(cx + gw + 5 * s - f * s, gb + 3 * s), (cx, ga - 3 * s + f * s)] for f in (1.6, 3.2)], roof))
    # na ban: dark cut-away ground round a white wheel with rays
    cv.obj([face], 1.)
    cv.hair(hatch_poly(face, 0, 1.5, .4))
    wy = gb - (gb - ga) * .34
    wr = gw * .3
    disc = _arc(cx, wy, wr, wr, 0, TAU, 28)
    cv.obj([disc], 1.)
    cv.hair([[(cx + wr * .35 * math.cos(a), wy + wr * .35 * math.sin(a)), (cx + wr * .9 * math.cos(a), wy + wr * .9 * math.sin(a))]
             for a in [TAU * i / 16 for i in range(16)]])
    cv.hair(_arc(cx, wy, wr * .35, wr * .35, 0, TAU, 12))
    # kranok flames rising either side of the wheel
    for sg in (-1, 1):
        fx = cx + sg * wr * 1.55
        fl = [(fx - 2.2 * s, gb - .5), (fx - sg * 1.5 * s, gb - 6 * s), (fx + sg * 2 * s, gb - 9 * s),
              (fx + sg * .5 * s, gb - 5.5 * s), (fx + 2.2 * s, gb - .5)]
        cv.obj([fl], .5)
        cv.hair([[(fx, gb - 1), (fx + sg * 1.2 * s, gb - 6.5 * s)]])
    # tympanum beam
    beam = [(cx - gw - 2 * s, gb), (cx - gw - 2 * s, gb + 3.5 * s), (cx + gw + 2 * s, gb + 3.5 * s), (cx + gw + 2 * s, gb)]
    cv.obj([beam], 1.)
    cv.hair(hatch_poly(beam, 0, 1.5, .5))
    # chofa: a slender hooked horn (the garuda's beak) at the apex
    ax, ay = cx, ga - 3 * s
    horn = _bez((ax - 1.2 * s, ay + 1), (ax - 1.5 * s, ay - 7 * s), (ax + 3 * s, ay - 11 * s), (ax + 4.5 * s, ay - 8.5 * s), 10)
    horn2 = _bez((ax + 4.5 * s, ay - 8.5 * s), (ax + 2 * s, ay - 9 * s), (ax + 1 * s, ay - 5 * s), (ax + 1.2 * s, ay + 1), 10)
    blk.append(horn + horn2[1:])
    return ga - 12 * s


def _sampan(cv, blk, wht, x, y, ln, rnd, kind, egg=False):
    """A flat sampan (ruea pai) with a seated vendor in a ngob hat. kind 'noodle': a steaming pot and
    stacked bowls; kind 'fruit': heaped fruit and a pole."""
    s = ln / 70.
    hull = ([(x - 35 * s, y - 7 * s)] + _bez((x - 35 * s, y - 7 * s), (x - 30 * s, y + 1 * s), (x - 15 * s, y + 2.6 * s), (x, y + 2.6 * s), 8)[1:]
            + _bez((x, y + 2.6 * s), (x + 15 * s, y + 2.6 * s), (x + 30 * s, y + 1 * s), (x + 35 * s, y - 6 * s), 8)[1:]
            + _bez((x + 35 * s, y - 6 * s), (x + 20 * s, y - 2.6 * s), (x - 20 * s, y - 2.6 * s), (x - 35 * s, y - 7 * s), 8)[1:])
    # wake lines under the hull (white paper cut through the water)
    cv.obj([[(x - 32 * s, y + 1 * s), (x + 32 * s, y + 1 * s), (x + 34 * s, y + 5 * s), (x - 34 * s, y + 5 * s)]], 0)
    cv.hair([[(x - 30 * s + rnd.uniform(-2, 2), y + 4.6 * s), (x - 6 * s, y + 4.6 * s)], [(x + 4 * s, y + 4.6 * s), (x + 28 * s, y + 4.6 * s)]])
    # vendor
    vx = x + (16 if kind == "noodle" else -14) * s
    body = [(vx - 4.2 * s, y - 2.5 * s), (vx - 3.2 * s, y - 10 * s), (vx + 3.2 * s, y - 10 * s), (vx + 4.6 * s, y - 2.5 * s)]
    cv.obj([body], 1.)
    cv.hair(hatch_poly(body, 75, 1.5))
    hat = [(vx - 10 * s, y - 10.5 * s), (vx, y - 16.5 * s), (vx + 10 * s, y - 10.5 * s), (vx, y - 9.6 * s)]
    cv.obj([hat], 1.)
    cv.hair([[(vx, y - 16.5 * s), (vx + 10 * s * f, y - 10.5 * s + .9 * s * (1 - abs(f)))] for f in (-.75, -.45, -.15, .15, .45, .75)])
    cv.hair(_clip_in(hatch_poly(hat, 20, 1.5), [(vx, y - 16.5 * s), (vx + 10 * s, y - 10.5 * s), (vx, y - 9.6 * s)]))
    blk.append([(vx - 7 * s, y - 10.2 * s), (vx + 7 * s, y - 10.2 * s), (vx + 3 * s, y - 8.4 * s), (vx - 3 * s, y - 8.4 * s)])
    if kind == "noodle":
        # paddle
        cv.obj([], 0)
        cv.line([(vx + 3 * s, y - 7 * s), (vx + 17 * s, y + 6 * s)])
        blk.append(_arc(vx + 18 * s, y + 7 * s, 1.6 * s, 3 * s, 0, TAU, 10))
        # pot over a brazier, lid knob, steam
        px = x - 6 * s
        pot = [(px - 7 * s, y - 3 * s), (px - 7.5 * s, y - 12 * s), (px + 7.5 * s, y - 12 * s), (px + 7 * s, y - 3 * s)]
        cv.obj([pot], 1.)
        cv.hair([q for q in hatch_poly(pot, 90, 1.5) if q[0][0] > px + 2 * s])
        cv.hair([q for q in hatch_poly(pot, 90, 3) if px - 3 * s < q[0][0] <= px + 2 * s])
        cv.line([(px - 7.6 * s, y - 9.5 * s), (px + 7.6 * s, y - 9.5 * s)])
        lid = _arc(px, y - 12 * s, 7.8 * s, 2.6 * s, math.pi, TAU, 14)
        cv.obj([lid], 1.)
        cv.hair([q for q in hatch_poly(lid, 0, 1.5) if q[0][0] > px])
        blk.append(_arc(px, y - 15 * s, 1.2 * s, 1 * s, 0, TAU, 8))
        if egg:   # a tiny engraved "P" on the pot's belly
            cv.obj([], 0)
            cv.line([(px - 1.5 * s, y - 4 * s), (px - 1.5 * s, y - 8.6 * s)] + _arc(px - .4 * s, y - 7.5 * s, 1.6 * s, 1.1 * s, -math.pi / 2, math.pi / 2, 6)[1:] + [(px - 1.5 * s, y - 6.4 * s)])
        cv.obj([], 0)
        for k, dx in enumerate((-3, 0, 3)):
            st = []
            for i in range(14):
                t = i / 13
                st.append((px + dx * s + math.sin(t * 7 + k) * 1.6 * s * (.4 + t), y - 16 * s - t * 15 * s))
            cv.hair(st)
        # stacked bowls
        for j in range(3):
            bx = x - 22 * s + j * 5.4 * s
            bowl = _arc(bx, y - 4 * s, 2.6 * s, 2.4 * s, 0, math.pi, 8)[::-1] + [(bx + 2.6 * s, y - 4 * s)]
            bowl = [(bx - 2.6 * s, y - 4 * s)] + _arc(bx, y - 4 * s, 2.6 * s, 2.2 * s, math.pi, 0, 8)[::-1][::-1]
            b = [(bx - 2.8 * s, y - 5 * s), (bx + 2.8 * s, y - 5 * s), (bx + 1.4 * s, y - 2.6 * s), (bx - 1.4 * s, y - 2.6 * s)]
            cv.obj([b], 1.)
            cv.hair([q for q in hatch_poly(b, 90, 1.5) if q[0][0] > bx])
    else:
        # pole
        cv.obj([], 0)
        cv.line([(vx - 2 * s, y - 8 * s), (vx - 12 * s, y + 7 * s)])
        cv.line([(vx + 1 * s, y - 8 * s), (vx + 9 * s, y - 34 * s)])
        # heaped fruit: mangosteen, rambutan, mango
        fr = []
        for j in range(11):
            fx = x + (2 + (j % 6) * 4.4 + (2.2 if j >= 6 else 0)) * s
            fy = y - (4.6 if j < 6 else 8.4) * s
            r = (2.3 if j % 3 else 2.7) * s
            fr.append((fx, fy, r))
        for fx, fy, r in fr:
            c = _arc(fx, fy, r, r, 0, TAU, 12)
            cv.obj([c], 1.)
            cv.hair(_clip_in([_arc(fx, fy, r * .6, r * .6, -.3, 2.2, 6)], c))
            cv.hair([q for q in hatch_poly(c, 60, 1.5) if (q[0][0] + q[1][0]) / 2 > fx])
        bk = [(x + 25 * s, y - 2.5 * s), (x + 24.5 * s, y - 8 * s), (x + 33 * s, y - 8.5 * s), (x + 32 * s, y - 3 * s)]
        cv.obj([bk], 1.)
        cv.hair(hatch_poly(bk, 45, 1.5) + hatch_poly(bk, -45, 3))
    blk.append(hull)
    # white strakes cut through the black hull: the gunwale and two planks
    for f, (u0, u1) in ((0, (.04, .96)), (1, (.12, .88)), (2, (.25, .75))):
        pts = []
        for i in range(13):
            u = u0 + (u1 - u0) * i / 12
            xx = x - 35 * s + 70 * s * u
            top = y - 2.6 * s - 4 * s * (2 * u - 1) ** 4 if u < .5 else y - 2.6 * s - 3.4 * s * (2 * u - 1) ** 4
            pts.append((xx, top + (1.1 + f * 1.4) * s))
        wht.append(pts)


def _longtail(cv, blk, x, y, ln, rnd):
    s = ln / 44.
    hull = [(x - 22 * s, y - 7 * s)] + _bez((x - 22 * s, y - 7 * s), (x - 18 * s, y), (x - 5 * s, y + 1.4 * s), (x + 14 * s, y + .6 * s), 8)[1:] + [(x + 16 * s, y - 1.6 * s), (x - 10 * s, y - 2 * s)]
    cv.obj([], 0)
    cv.line([(x + 14 * s, y - 3 * s), (x + 28 * s, y + 2 * s)])
    cv.hair([[(x + 27 * s + rnd.uniform(-1, 3), y + rnd.uniform(-1, 2)), (x + 31 * s + rnd.uniform(0, 4), y + rnd.uniform(-3, 1))] for _ in range(6)])
    blk.append(hull)
    for dx in (-9, -4, 1):
        blk.append(_arc(x + dx * s, y - 3.6 * s, 1 * s, 1 * s, 0, TAU, 8))
    blk.append(_arc(x + 12 * s, y - 6 * s, 1 * s, 1.2 * s, 0, TAU, 8))
    blk.append([(x + 11 * s, y - 5 * s), (x + 13 * s, y - 5 * s), (x + 13.4 * s, y - 2 * s), (x + 10.6 * s, y - 2 * s)])


_ELE = ("M37,14C42,13.6 46,16 49,18.6C58,14 72,13 82,18C89,22 93,32 92,44C92,52 91,62 91,70L81,70C81,64 80.6,59 80,55"
        "C74,56.6 64,57 59,56C58.6,61 58.6,66 58.6,70L47,70C47,64 46,56 45,50C43,49 41,48 39.6,46.6"
        "C37.6,47.6 36.4,50 36.4,54C36.6,58 37.6,61 36,64C34.4,66.4 31,66 30.6,63.4C30.4,62 31.6,61 32.6,61.6"
        "C33.4,59 32.6,55 31.6,51C30.2,45 28.8,38 29.2,31C29.6,25 31,17.6 37,14Z")
_EAR = "M41,22C50,21 54,30 51,40C49,45 44,45 42.4,41C41.8,37 43,33 42,28C41.6,26 41,24 41,22Z"


def _elephant(cv, blk, x, yb, ht):
    s = ht / 57.
    body = _cpath(_ELE, x - 60 * s, yb - 70 * s, s)
    cv.obj([body], 1.)
    cv.hair([q for q in hatch_poly(body, 90, 1.5) if q[0][0] > x + 12 * s])
    cv.hair(_clip_in(hatch_poly(body, 0, 1.5), [(x - 70, yb - 16 * s), (x + 70, yb - 16 * s), (x + 70, yb + 5), (x - 70, yb + 5)]))
    ear = _cpath(_EAR, x - 60 * s, yb - 70 * s, s)
    cv.obj([ear], .5)
    cv.hair(hatch_poly(ear, 90, 1.5))
    # a tasselled howdah cloth
    cl = [(x - 8 * s, yb - 52 * s), (x + 22 * s, yb - 52 * s), (x + 22 * s, yb - 34 * s), (x - 8 * s, yb - 34 * s)]
    cv.obj([cl], .5)
    cv.hair(hatch_poly(cl, 45, 3))
    blk.append(_arc(x - 20 * s, yb - 50 * s, 1.5 * s, 1.5 * s, 0, TAU, 8))


def _kranok(cv, x, y, ang, L, sg=1, wd=None):
    """A Thai kranok flame: a swelling blade on a curved spine whose tip flicks over into a curl,
    a lobed outer edge (the flame's teeth), contour lines dense on the inner side and a black eye
    at the root. ang: heading in degrees (-90 = up); sg: which way the tip flicks."""
    wd = wd or L * .3
    n = 26
    sp = []
    a = math.radians(ang)
    px, py = x, y
    for i in range(n + 1):
        u = i / n
        sp.append((px, py))
        a += sg * (.02 + .16 * u ** 2.2)
        px += math.cos(a) * L / n
        py += math.sin(a) * L / n
    def norm(i):
        a_, b_ = sp[max(0, i - 1)], sp[min(n, i + 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        l = math.hypot(dx, dy) or 1
        return -dy / l, dx / l
    def half(u):
        return wd * .5 * math.sin(math.pi * min(1, u * 1.05) ** .8) * (1 - .25 * u)
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        nx, ny = norm(i)
        hw = half(u)
        tooth = 1 + .22 * max(0, math.sin(u * math.pi * 4.5)) * (u > .15)
        outer.append((sp[i][0] + nx * hw * tooth * -sg, sp[i][1] + ny * hw * tooth * -sg))
        inner.append((sp[i][0] - nx * hw * -sg, sp[i][1] - ny * hw * -sg))
    poly = outer + inner[::-1]
    cv.obj([poly], 1.)
    # contour lines on the inner (shadow) half, closer toward the edge
    ls = []
    for f in (.25, .45, .62, .76, .88):
        pl = []
        for i in range(2, n - 1):
            u = i / n
            nx, ny = norm(i)
            hw = half(u)
            pl.append((sp[i][0] - nx * hw * f * -sg, sp[i][1] - ny * hw * f * -sg))
        ls.append(pl)
    cv.hair(ls)
    cv.hair([[(sp[i][0], sp[i][1]), outer[i]] for i in range(4, n - 3, 3)])
    cv.line(sp[1:n - 1])
    # the niello half: the inner side cut solid black, a white vein left along the spine
    blk = []
    for i in range(1, n):
        nx, ny = norm(i)
        hw = half(i / n)
        blk.append((sp[i][0] - nx * hw * .3 * -sg, sp[i][1] - ny * hw * .3 * -sg))
    return blk + [p for p in inner[1:n][::-1]]


# ------------------------------------------------------------------------------------ the scene
def _scene(field, X, Y, W, H, seed, small=False):
    """Paint the floating market into the field polygon (bbox X, Y, W, H). Returns SVG."""
    rnd = random.Random(seed)
    cv = Canvas()
    blk, wht = [], []
    tall = W / H < 1.25
    yh = Y + H * (.62 if small else (.6 if tall else .6))
    # sky: ruled, closer toward the zenith
    cv.obj([], 0)
    ytop = Y + H * (.14 if tall else .2)
    cv.hair(_hrules(field, 2, 0., ytop, yh))
    cv.hair(_hrules(field, 1.5, 0., -1e9, ytop - .5))
    sky = yh - Y
    if small:
        _cloud(cv, X + W * .3, Y + H * .36, W * .4, H * .16, rnd)
        _cloud(cv, X + W * .76, Y + H * .3, W * .34, H * .15, rnd, dark=True)
    else:
        # the squall on the right, falling from a dark cloud; fair-weather billows to the left
        rx0 = X + W * (.66 if not tall else .6)
        cby = Y + sky * (.36 if not tall else .4)
        _rain(cv, rx0, X + W * 1.02, cby, yh, rnd)
        _cloud(cv, X + W * .82, cby, W * (.4 if not tall else .5), sky * .3, rnd, dark=True)
        _cloud(cv, X + W * .3, Y + sky * (.33 if not tall else .3), W * (.5 if not tall else .6), sky * .32, rnd)
        if tall:
            _cloud(cv, X + W * .42, Y + sky * .62, W * .4, sky * .18, rnd)
        else:
            _cloud(cv, X + W * .5, Y + sky * .64, W * .26, sky * .2, rnd)
    # far bank
    _treeline(cv, X - 5, X + W + 5, yh, H * .07, rnd)
    hall_w = min(W * .42, H * .62) if not tall else W * .5
    hx = X + W * (.6 if not tall else .58)
    if not small:
        _chedi(cv, blk, X + W * (.2 if not tall else .17), yh + 1, sky * (.78 if not tall else .7))
        _palm(cv, X + W * .06, yh + 2, sky * .74, .2, rnd)
        _palm(cv, X + W * .95, yh + 2, sky * .66, -.24, rnd)
        _palm(cv, X + W * .34, yh + 1, sky * .44, -.1, rnd)
        _elephant(cv, blk, hx + hall_w * .5 + W * .045, yh + 1.5, H * .11)
    _ubosot(cv, blk, hx, yh + 1, hall_w, rnd)
    # bank edge and the klong
    water = [(X - 5, yh + 1), (X + W + 5, yh + 1), (X + W + 5, Y + H + 5), (X - 5, Y + H + 5)]
    wd = Y + H - yh
    cv.obj([water], 0)
    cv.line([(X - 5, yh + 1), (X + W + 5, yh + 1)])
    cv.hair(_hrules(water, 3, 0, yh + 2, yh + wd * .4, (5, 16), rnd))
    cv.hair(_hrules(water, 2, 0, yh + wd * .4, Y + H + 5, (6, 20), rnd))
    refl = []
    for (rx, rw, rl) in ((hx, hall_w * .36, wd * .55), (X + W * .2, W * .05, wd * .45)):
        yy = yh + 3
        while yy < yh + rl:
            hw = rw * (1 - (yy - yh) / rl) * rnd.uniform(.7, 1)
            refl.append([(rx - hw, yy), (rx + hw * rnd.uniform(-.2, .1), yy)])
            refl.append([(rx + hw * rnd.uniform(.1, .3), yy), (rx + hw, yy)])
            yy += 2
    cv.line(refl)
    if not small:
        bl = W * (.42 if not tall else .5)
        _longtail(cv, blk, X + W * .42, yh + wd * .24, bl * .32, rnd)
        _sampan(cv, blk, wht, X + W * .3, yh + wd * .6, bl, rnd, "fruit")
        _sampan(cv, blk, wht, X + W * .7, yh + wd * .8, bl * 1.02, rnd, "noodle", egg=True)
    out = cv.svg() + f'<path d="{_blk(blk)}" fill="#000" stroke="none"/>'
    if wht:
        out += f'<path d="{"".join(_d(q, False, .15) for q in wht)}" fill="none" stroke="#fff" stroke-width=".5"/>'
    return out


def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------ layouts
def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("wb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 4, ry - 4
    field = C._ell_pts(cx, cy, fx, fy, 64)
    o.append(_field_clip(C._uid("wbf", w, h, seed), _d(field, True, 0),
                         _scene(field, cx - fx, cy - fy, 2 * fx, 2 * fy, seed, small=True)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _cart_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a + .5, b + .5), (cx - a, cy - b, 2 * a, 2 * b)


def _layout_medium(w, h, seed):
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
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("wm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    kv = Canvas()
    kb = []
    for side in (-1, 1):
        for (fy, fa, fl, fs) in ((cy - gh * .04, -72, gh * .4, 1), (cy + gh * .04, 72, gh * .36, -1)):
            ang = fa if side > 0 else 180 - fa
            kb.append(_kranok(kv, cx + side * cw * .5, fy, ang, fl, side * fs))
    o.append(C._clip(C._uid("wmk", w, h, seed), 0, gy0, w, gh, kv.svg() + f'<path d="{_blk(kb)}" fill="#000"/>'))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    field, (X, Y, W, H) = _cart_field(cx, cy, cw, gh + 4)
    o.append(_field_clip(C._uid("wmf", w, h, seed), _d(field, True, 0), _scene(field, X, Y, W, H, seed)))
    o.append(C.bead_moulding(cx - cw * .5 + 8, 0, 0, 1) if False else "")
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tablet(tx, ty, tw, th, seed):
    """Fill the pedestal's sunk tablet: a running row of lotus petals, cut-away ground between."""
    cv = Canvas()
    box = [(tx + 2, ty + 2), (tx + tw - 1, ty + 2), (tx + tw - 1, ty + th - 1), (tx + 2, ty + th - 1)]
    cv.obj([], 0)
    cv.hair(hatch_poly(box, 0, 1.5, .3))
    n = max(5, int(tw / (th * .9)))
    pw = (tw - 6) / n
    for i in range(n):
        px = tx + 3 + pw * (i + .5)
        pet = _bez((px, ty + th - 3), (px - pw * .55, ty + th * .6), (px - pw * .2, ty + th * .3), (px, ty + 4), 8) + \
            _bez((px, ty + 4), (px + pw * .2, ty + th * .3), (px + pw * .55, ty + th * .6), (px, ty + th - 3), 8)[1:]
        cv.obj([pet], 1.)
        cv.hair(_clip_in([[(px, ty + th - 3), (px, ty + 6)]], pet))
        cv.hair([q for q in hatch_poly(pet, 90, 1.5) if q[0][0] > px + .8])
    return cv.svg()


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
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
                   max_n=5, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("wt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    field, (X, Y, W, H) = _cart_field(cx, cy, cw, ch)
    o.append(_field_clip(C._uid("wtf", w, h, seed), _d(field, True, 0), _scene(field, X, Y, W, H, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(15, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .5, cw * 1.25, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_aroi(centre, bh))
    py = h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, seed))
    return "".join(o)


# Today's phrase, lettered on the ribbon in Thai: aroi, "delicious". Glyphs as unit strokes
# (x 0..1, y 0..1 down), each a list of polylines plus head loops (cx, cy, r).
def _g_oang():
    return ([[(.2, .13), (.45, .0), (.8, .03), (.95, .3), (.95, .95), (.5, 1.), (.08, .95), (.05, .5)]], [(.2, .27, .13)])


def _g_ro():
    return ([[(.16, .22), (.1, .06), (.3, 0.), (.85, .02), (.93, .3), (.93, .74), (.76, .98), (.42, 1.), (.26, .96)]], [(.27, .82, .13)])


def _g_yo():
    return ([[(.15, .28), (.08, .6), (.1, .97), (.5, 1.), (.88, .96), (.93, .55), (.93, 0.)], [(.1, .78), (.3, .96)]], [(.16, .15, .12)])


def _aroi(centre, bh):
    n = len(centre) - 1
    gh = bh * .56
    gw = gh * .78
    adv = gw * 1.35
    glyphs = [_g_oang(), _g_ro(), _g_oang(), _g_yo()]
    tot = adv * len(glyphs) - (adv - gw)
    mid = centre[n // 2]
    lines, loops = [], []

    def at(x):          # the ribbon's centre line height at x
        for a, b in zip(centre, centre[1:]):
            if a[0] <= x <= b[0]:
                return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0] or 1)
        return mid[1]
    x0 = mid[0] - tot / 2
    for i, (pls, lps) in enumerate(glyphs):
        gx = x0 + i * adv
        gy = at(gx + gw / 2) - gh * .38
        for pl in pls:
            lines.append([(gx + u * gw, gy + v * gh) for u, v in pl])
        for u, v, r in lps:
            loops.append(_arc(gx + u * gw, gy + v * gh, r * gw, r * gw, 0, TAU, 10))
        if i == 1:      # mai ek, the low-tone mark, over the ro
            lines.append([(gx + gw * .92, gy - gh * .55), (gx + gw * .92, gy - gh * .2)])
    # flourishes either side: a lozenge and dashes running out along the ribbon
    for sg in (-1, 1):
        ex = mid[0] + sg * (tot / 2 + gw * .9)
        ey = at(ex)
        loops.append([(ex - 1.6, ey), (ex, ey - 1.6), (ex + 1.6, ey), (ex, ey + 1.6)])
        k = 0
        x = ex + sg * 4
        while abs(x - mid[0]) < (centre[-1][0] - centre[0][0]) / 2 - 6 and k < 12:
            L = 3.5 - k * .15
            lines.append([(x, at(x)), (x + sg * L, at(x + sg * L))])
            x += sg * (L + 2.2)
            k += 1
    d = "".join(_d(q, False, .1) for q in lines)
    dl = "".join(_d(q, True, .1) for q in loops)
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="{dl}" fill="#fff" stroke="#000" stroke-width="1"/>')


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) * 7 + int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
