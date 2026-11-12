"""Parker's arms, Somaster: *Or, a castle between five fleurs-de-lis sable*.

Engraved in heraldic hatching after Petra Sancta: Or as an even field of fine dots and sable as solid
black, with the masonry and window slits cut in white line. The shield is a heater with a castle of
two crenellated towers, a crenellated curtain wall and an arched gate with its portcullis. There are
three fleurs-de-lis in chief and one on each flank. Acanthus mantling, Or lined sable, falls from the
shield's top corners.

Shared by the Morning Edition (cover emblem, dedication cartouche, end page), the plate studios and
the Evening Edition:

    arms(w, h, seed=0) -> str        SVG child markup for a w x h box (no <svg>, no transforms)
    arms_svg(w, h, seed=0) -> str    the same wrapped in a full <svg>

The output is deterministic. The only ids are the dot pattern, prefixed `smst-` and keyed by size and
seed, so two different arms on one page never collide. Strokes are 0.5, 1 or 1.5 px. Dots and white
lines are at least 1 px for e-ink. The arms have no <text>, masks or filters.
"""
import math
import random

DW, DH = 120., 140.          # design space; the shield is x 25..95, y 16..118


def _f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class _Map:
    """Design units -> output px: a uniform scale k, centred in the w x h box."""

    def __init__(self, w, h):
        self.k = min(w / DW, h / DH)
        self.ox = (w - DW * self.k) / 2
        self.oy = (h - DH * self.k) / 2

    def p(self, x, y):
        return f"{_f(self.ox + x * self.k)},{_f(self.oy + y * self.k)}"

    def xy(self, x, y):
        return self.ox + x * self.k, self.oy + y * self.k


def _bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def _poly(M, pts, close=True):
    return "M" + "L".join(M.p(x, y) for x, y in pts) + ("Z" if close else "")


# ------------------------------------------------------------------------------------------------
# the shield
# ------------------------------------------------------------------------------------------------

SX0, SX1, SY0, SY1 = 25., 95., 16., 118.


def _shield_pts(inset=0.):
    x0, x1, y0 = SX0 + inset, SX1 - inset, SY0 + inset
    cx, yb = (SX0 + SX1) / 2, SY1 - inset * 1.4
    side = 60.
    right = _bez((x1, side), (x1, 90 - inset * .3), (cx + 15, 106 - inset * .5), (cx, yb), 18)
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    return [(x0, y0), (x1, y0)] + right + left[1:] + [(x0, side)]


# ------------------------------------------------------------------------------------------------
# charges (sable)
# ------------------------------------------------------------------------------------------------

# a fleur-de-lis in unit space: height 2 (y -1 top .. +1 foot), width about 1.8
_FLEUR = [
    # centre petal
    [(0, -1), (.18, -.8), (.3, -.55), (.26, -.3), (.15, -.06), (-.15, -.06), (-.26, -.3), (-.3, -.55), (-.18, -.8)],
    # band
    [(-.36, -.04), (.36, -.04), (.36, .12), (-.36, .12)],
    # foot, a pointed stub with a small flared base
    [(-.1, .12), (.1, .12), (.16, .5), (.3, .62), (0, .58), (-.3, .62), (-.16, .5)],
]


def _side_petal(sg):
    """The right (sg 1) or left (sg -1) petal: up and out from the band, curling down to a knob."""
    out = [(.12, -.04), (.2, -.32), (.36, -.54), (.6, -.6), (.84, -.5), (.95, -.26), (.9, -.02), (.76, .1),
           (.6, .06), (.56, -.08), (.66, -.12), (.72, -.22), (.64, -.32), (.5, -.3), (.4, -.16), (.34, .06)]
    return [(sg * x, y) for x, y in out]


def _fleur(M, cx, cy, s):
    """One fleur-de-lis s design units tall at (cx, cy): solid sable, and a white vein if it is big."""
    parts = _FLEUR + [_side_petal(1), _side_petal(-1)]
    d = "".join(_poly(M, [(cx + x * s / 2, cy + y * s / 2) for x, y in pt]) for pt in parts)
    o = f'<path d="{d}" fill="#000"/>'
    if s * M.k >= 22:   # the centre vein, cut in white
        o += (f'<path d="M{M.p(cx, cy - s * .38)}L{M.p(cx, cy - s * .1)}" stroke="#fff" stroke-width="1" '
              f'fill="none" stroke-linecap="round"/>')
    return o


def _castle(M):
    """Two crenellated towers, a crenellated curtain wall and an arched gate with a portcullis."""
    base = 98.
    lt, rt = (41.5, 53.), (67., 78.5)           # tower x spans
    ty, wy = 50., 67.                         # tower and wall tops (below the merlons)
    mh = 4.5                                  # merlon height

    def merlons(x0, x1, top, n):
        """n merlons across x0..x1 with n-1 crenels between them."""
        u = (x1 - x0) / (2 * n - 1)
        return [(x0 + 2 * j * u, x0 + (2 * j + 1) * u, top - mh) for j in range(n)]

    body = []
    body.append([(lt[0], ty), (lt[1], ty), (lt[1], base), (lt[0], base)])
    body.append([(rt[0], ty), (rt[1], ty), (rt[1], base), (rt[0], base)])
    body.append([(lt[1] - .5, wy), (rt[0] + .5, wy), (rt[0] + .5, base), (lt[1] - .5, base)])
    for x0, x1, top in merlons(lt[0], lt[1], ty, 3) + merlons(rt[0], rt[1], ty, 3):
        body.append([(x0, top), (x1, top), (x1, top + mh + .2), (x0, top + mh + .2)])
    for x0, x1, top in merlons(lt[1] + 1.5, rt[0] - 1.5, wy, 4):
        body.append([(x0, top), (x1, top), (x1, top + mh + .2), (x0, top + mh + .2)])
    # the gate: an arched opening, cut out of the wall by drawing it after in Or
    gx0, gx1, gy = 55.5, 64.5, 82.
    gr = (gx1 - gx0) / 2
    arch = [(gx0, base), (gx0, gy)] + [(60 - gr * math.cos(math.pi * i / 12), gy - gr * math.sin(math.pi * i / 12))
                                       for i in range(1, 12)] + [(gx1, gy), (gx1, base)]
    o = [f'<path d="{"".join(_poly(M, b) for b in body)}" fill="#000"/>']
    # masonry courses in white line, broken at the slits and gate
    w1 = 1
    cut = []
    for y in (57., 64., 71., 78., 85., 92.):  # courses
        for x0, x1 in (lt, rt):
            if y > ty + 1:
                cut.append((x0 + 1.2, y, x1 - 1.2, y))
        if y > wy + 2:
            cut.append((lt[1] + 1.2, y, gx0 - 1.6, y))
            cut.append((gx1 + 1.6, y, rt[0] - 1.2, y))
    # tower slits: on the courses' gaps
    slits = []
    for x0, x1 in (lt, rt):
        c = (x0 + x1) / 2
        slits += [(c, 59., 4.2), (c, 80., 4.2)]
    d = ""
    for x0, y, x1, _ in cut:
        # leave room for the slits
        segs = [(x0, x1)]
        for sx, sy, sh in slits:
            if sy - .5 <= y <= sy + sh + .5 and x0 < sx < x1:
                segs = [(a, min(b, sx - 2.2)) for a, b in segs] + [(max(a, sx + 2.2), b) for a, b in segs]
        for a, b in segs:
            if b - a > 1.2:
                d += f"M{M.p(a, y)}H{_f(M.xy(b, y)[0])}"
    if d:
        o.append(f'<path d="{d}" stroke="#fff" stroke-width="{w1}" fill="none" stroke-linecap="butt"/>')
    sd = ""
    for sx, sy, sh in slits:
        sw = 1.8
        sd += _poly(M, [(sx - sw / 2, sy + sh)] + [(sx - sw / 2 * math.cos(math.pi * i / 6), sy + sw / 2 - sw / 2 * math.sin(math.pi * i / 6))
                                                   for i in range(7)] + [(sx + sw / 2, sy + sh)])
    o.append(f'<path d="{sd}" fill="#fff"/>')
    return o, arch, (gx0, gx1, gy - gr, base)


# ------------------------------------------------------------------------------------------------
# mantling: acanthus fronds, Or lined sable, falling from the shield's top corners
# ------------------------------------------------------------------------------------------------

def _frond(spine, wmax, lobes, rng):
    """A ribbon along spine (list of points) that swells to wmax and tapers into a curl, its outer edge
    scalloped into acanthus lobes. Returns (outer outline, inner lining strip, lining midline)."""
    n = len(spine)
    nrm = []
    for i in range(n):
        a, b = spine[max(0, i - 1)], spine[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nrm.append((-dy / L, dx / L))
    left, right, lin, mid = [], [], [], []
    for i, ((x, y), (nx, ny)) in enumerate(zip(spine, nrm)):
        u = i / (n - 1)
        wv = wmax * math.sin(math.pi * min(1, u * 1.15)) ** .7 if u < .87 else wmax * .25 * (1 - u) / .13
        ph = u * lobes * math.pi
        sc = .55 + .45 * (1 - abs(math.sin(ph))) ** 1.6      # pointed acanthus lobes, round bays
        wo = wv * sc
        left.append((x + nx * wo, y + ny * wo))
        right.append((x - nx * wv * .55, y - ny * wv * .55))
        lin.append((x - nx * wv * .05, y - ny * wv * .05))
        mid.append((x - nx * wv * .3, y - ny * wv * .3))
    outline = left + list(reversed(right))
    lining = lin + list(reversed(right))
    # a vein from the spine to each lobe point, with a shorter one either side
    veins = []
    for j in range(1, int(lobes) + 1):
        i = int(round(j / lobes * (n - 1)))
        if 0 < i < n * .86:
            for di, f in ((0, .85), (-1, .5), (1, .5)):
                k = min(n - 1, max(0, i + di))
                x, y = spine[k]
                lx, ly = left[k]
                bx, by = spine[max(0, i - 2)]
                veins.append([(bx + (x - bx) * .3, by + (y - by) * .3), (x + (lx - x) * f, y + (ly - y) * f)])
    return outline, lining, mid, veins


def _spine(p0, p1, p2, p3, curl, n=26):
    """A cubic sweep ending in a tightening curl (turn sign curl)."""
    pts = _bez(p0, p1, p2, p3, n)
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    a = math.atan2(by - ay, bx - ax)
    step = math.hypot(bx - ax, by - ay)
    x, y = bx, by
    for i in range(10):
        a += curl * (.32 + i * .045)
        step *= .9
        x, y = x + math.cos(a) * step, y + math.sin(a) * step
        pts.append((x, y))
    return pts


def _mantling(M, seed):
    rng = random.Random(seed * 7 + 3)
    j = lambda v: v + rng.uniform(-1.2, 1.2)
    fronds = [
        # (p0, p1, p2, p3, curl sign, width, lobes): the left side; mirrored for the right
        ((30, 17), (14, 8), (2, 18), (j(6), j(34)), -1, 9., 4),
        ((26, 26), (10, 30), (3, 48), (j(9), j(66)), -1, 9.5, 5),
        ((26, 44), (12, 58), (6, 84), (j(14), j(100)), -1, 9., 5),
        ((27, 66), (16, 86), (16, 110), (j(28), j(124)), -1, 7.5, 4),
        ((46, 16), (42, 5), (30, 2), (j(20), j(9)), 1, 6.5, 3),
    ]
    outs, lins, mids, veins = [], [], [], []
    for side in (1, -1):
        for p0, p1, p2, p3, cs, wd, lb in fronds:
            m = (lambda p: p) if side == 1 else (lambda p: (DW - p[0], p[1]))
            sp = _spine(m(p0), m(p1), m(p2), m(p3), cs * side)
            # a mirrored spine flips its normal, so the right side passes a negative width
            ol, li, mi, ve = _frond(sp, wd * side, lb, rng)
            veins += ve
            outs.append(ol)
            lins.append(li)
            mids.append(mi)
    return outs, lins, mids, veins


# ------------------------------------------------------------------------------------------------
# the arms
# ------------------------------------------------------------------------------------------------

def arms(w, h, seed=0):
    """Somaster arms engraved for a w x h px box: SVG child markup, no outer <svg>, no transforms."""
    M = _Map(w, h)
    pid = f"smst-or-{int(round(w))}x{int(round(h))}-{int(seed)}"
    pitch = 2. if M.k >= .9 else 3.     # Or: 1 px dots every 2 px (3 px when small, so it stays grey)
    o = [f'<defs><pattern id="{pid}" width="{_f(pitch)}" height="{_f(pitch)}" patternUnits="userSpaceOnUse">'
         f'<rect width="{_f(pitch)}" height="{_f(pitch)}" fill="#fff"/>'
         f'<circle cx="{_f(pitch / 2)}" cy="{_f(pitch / 2)}" r=".5" fill="#000"/></pattern></defs>']
    OR = f"url(#{pid})"
    # mantling first, behind the shield
    outs, lins, mids, veins = _mantling(M, seed)
    o.append(f'<path d="{"".join(_poly(M, p) for p in outs)}" fill="{OR}" stroke="#000" stroke-width="1" stroke-linejoin="round"/>')
    o.append(f'<path d="{"".join(_poly(M, p, False) for p in veins)}" fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round"/>')
    o.append(f'<path d="{"".join(_poly(M, p) for p in lins)}" fill="#000"/>')
    o.append(f'<path d="{"".join(_poly(M, p[2:-6], False) for p in mids)}" fill="none" stroke="#fff" stroke-width="1" stroke-linecap="round"/>')
    # the shield: a black edge, a white fillet, the Or field
    sh = _shield_pts()
    o.append(f'<path d="{_poly(M, sh)}" fill="#000"/>')
    o.append(f'<path d="{_poly(M, _shield_pts(1.4 / M.k + .2))}" fill="#fff"/>')
    o.append(f'<path d="{_poly(M, _shield_pts(2.4 / M.k + .6))}" fill="{OR}"/>')
    # charges
    body, arch, (gx0, gx1, gtop, gb) = _castle(M)
    o += body
    o.append(f'<path d="{_poly(M, arch)}" fill="{OR}" stroke="#000" stroke-width="1"/>')
    # the portcullis: black grid in the gate
    pd = ""
    x = gx0 + 1.8
    while x < gx1 - .8:
        pd += f"M{M.p(x, gtop + 1)}V{_f(M.xy(x, gb)[1])}"
        x += 2.
    for y in (gtop + 5, gtop + 9.5, gtop + 14):
        pd += f"M{M.p(gx0, y)}H{_f(M.xy(gx1, y)[0])}"
    o.append(f'<path d="{pd}" stroke="#000" stroke-width="1" fill="none"/>')
    for cx, cy, s in ((40, 31, 18.5), (60, 29.5, 18.5), (80, 31, 18.5), (32.6, 80, 14), (87.4, 80, 14)):
        o.append(_fleur(M, cx, cy, s))
    # the edge: a 1.5 px black line over all
    o.append(f'<path d="{_poly(M, sh)}" fill="none" stroke="#000" stroke-width="1.5" stroke-linejoin="round"/>')
    return "".join(o)


def arms_svg(w, h, seed=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(w)}" height="{_f(h)}" viewBox="0 0 {_f(w)} {_f(h)}">'
            + arms(w, h, seed) + "</svg>")


if __name__ == "__main__":
    import sys
    w, h = (float(a) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (160, 200)
    sys.stdout.write(arms_svg(w, h))
