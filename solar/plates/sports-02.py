"""sports-02 (Portland Timbers): a carved acanthus frame round a cartouche in which a ball, struck
from the left, bulges the top corner of a goal net set before a stand of Douglas firs. Two cut log
slabs (Timber Joey's slab for every goal; their number follows the last score) lie in the
foreground, and a tiny Timbers Army snare with crossed drumsticks hides in the grass (Parker's egg).
The two main volutes of the frame wind into small footballs instead of plain black eyes."""
import sys
import math
import random
import re
import zlib
import engraving_codex as C

_n, _d, pat = C._n, C._d, C.pat
PI = math.pi


def _uid(*a):
    return "spt" + format(zlib.crc32(repr(a).encode()) & 0xffffff, "x")


def _ell(cx, cy, rx, ry, n=48, a0=0., a1=2 * PI):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def _P(d, fill="none", sw=None, extra=""):
    s = f' stroke="#000" stroke-width="{_n(sw)}"' if sw else ' stroke="none"'
    return f'<path d="{d}" fill="{fill}"{s}{extra}/>'


def _lines(pls, tol=0.):
    return "".join(_d(p, tol=tol) for p in pls if len(p) > 1)


# ------------------------------------------------------------------------------------------------
# the football: a truncated icosahedron in orthographic projection, shaded as a sphere
# ------------------------------------------------------------------------------------------------

_PHI = (1 + 5 ** .5) / 2
_ICO = []
for _a in (-1, 1):
    for _b in (-_PHI, _PHI):
        _ICO += [(0, _a, _b), (_a, _b, 0), (_b, 0, _a)]


def _norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def _nbrs(i):
    v = _ICO[i]
    return [j for j, u in enumerate(_ICO) if j != i and abs(sum((a - b) ** 2 for a, b in zip(u, v)) - 4) < 1e-6]


def _rot(v, rx, ry, rz):
    x, y, z = v
    c, s = math.cos(rx), math.sin(rx)
    y, z = y * c - z * s, y * s + z * c
    c, s = math.cos(ry), math.sin(ry)
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(rz), math.sin(rz)
    x, y = x * c - y * s, x * s + y * c
    return (x, y, z)


def _slerp(a, b, t):
    return _norm(tuple(p + (q - p) * t for p, q in zip(a, b)))


def football(cx, cy, r, rot=(.4, .3, .2), shade=True):
    """A shaded football: white sphere, black pentagons, seams, and a hatched shadow crescent
    lower right with a black core and a reflected-light rim. 4-5 elements."""
    def pv(i, j):
        v, u = _ICO[i], _ICO[j]
        return _norm(tuple(a + (b - a) / 3 for a, b in zip(v, u)))

    def proj(p):
        q = _rot(p, *rot)
        return (cx + q[0] * r, cy - q[1] * r, q[2])

    pents, seams = [], []
    for i in range(12):
        nb = _nbrs(i)
        # order the neighbours around the vertex
        v = _ICO[i]
        ref = _norm(_ICO[nb[0]])
        e1 = _norm(tuple(a - sum(x * y for x, y in zip(ref, v)) / 5.236 * b for a, b in zip(ref, v)))
        vn = _norm(v)
        e2 = (vn[1] * e1[2] - vn[2] * e1[1], vn[2] * e1[0] - vn[0] * e1[2], vn[0] * e1[1] - vn[1] * e1[0])
        nb.sort(key=lambda j: math.atan2(sum(a * b for a, b in zip(_ICO[j], e2)), sum(a * b for a, b in zip(_ICO[j], e1))))
        ring = [pv(i, j) for j in nb]
        pts3 = []
        for k in range(5):
            a, b = ring[k], ring[(k + 1) % 5]
            pts3 += [_slerp(a, b, t / 4) for t in range(4)]
        P = [proj(p) for p in pts3]
        if min(p[2] for p in P) > -.05:
            pents.append([(p[0], p[1]) for p in P])
        elif max(p[2] for p in P) > 0:
            # partly round the limb: keep only the front part
            pents.append([(p[0], p[1]) if p[2] > 0 else
                          (cx + (p[0] - cx) / max(1e-6, math.hypot(p[0] - cx, p[1] - cy)) * r,
                           cy + (p[1] - cy) / max(1e-6, math.hypot(p[0] - cx, p[1] - cy)) * r) for p in P])
        for j in nb:
            if j > i:
                a, b = pv(i, j), pv(j, i)
                seg = [proj(_slerp(a, b, t / 6)) for t in range(7)]
                vis = [(p[0], p[1]) for p in seg if p[2] > 0]
                if len(vis) > 1:
                    seams.append(vis)
    # the hexagon seams also run between pentagon vertices of neighbouring pentagons (already
    # covered above), plus the pentagon outlines themselves.
    circ = _ell(cx, cy, r, r, 56)
    o = [_P(_d(circ, True, .1), "#fff", 1.)]
    o.append(_P("".join(_d(p, True, .15) for p in pents), "#000"))
    o.append(_P(_lines(seams, .15), sw=.5))
    if shade:
        # shadow crescent, lower right: hatched, then a black core under the limb
        n = 40
        outer = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in
                 [-.55 + (PI + .2) * k / n for k in range(n + 1)]]
        inner = [(cx + r * .42 + r * .62 * math.cos(t), cy + r * .3 + r * .62 * math.sin(t)) for t in
                 [-.55 + PI + .2 - (PI + .2) * k / n for k in range(n + 1)]]
        cres = outer + inner
        hl = C.hatch_poly(cres, -35, 1.5 if r < 14 else 2.)
        o.append(_P(_lines(hl), sw=.5))
        core = [(cx + (r - .4) * math.cos(t), cy + (r - .4) * math.sin(t)) for t in [.0 + 1.9 * k / 20 for k in range(21)]]
        core += [(cx + (r - r * .13) * math.cos(t), cy + (r - r * .13) * math.sin(t)) for t in [1.9 - 1.9 * k / 20 for k in range(21)]]
        o.append(_P(_d(core, True, .1), "#000"))
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# scene pieces
# ------------------------------------------------------------------------------------------------

def _fir(x, base, h, rng, wfac=.36):
    """Douglas fir: drooping tiers. Returns (outline polygon, branch-tip hatch polylines)."""
    tiers = max(4, int(h / 6))
    left, right = [], []
    top = base - h
    for k in range(tiers + 1):
        t = k / tiers
        y = top + h * t * .92
        hw = h * wfac * (t ** .95) * rng.uniform(.85, 1.1) + .6
        left.append((x - hw, y + h * .03))
        left.append((x - hw * .45, y + h * .012))
        right.append((x + hw, y + h * .03))
        right.append((x + hw * .45, y + h * .012))
    poly = [(x, top)] + right[1:] + [(x + h * .03, base), (x - h * .03, base)] + left[1:][::-1]
    return poly


def _fir_svg(x, base, h, rng, dark="G", wfac=.36):
    """A Douglas fir carved in relief: drooping tiers, each lit on the upper-left (open hatch) and
    shadowed lower-right (close hatch, black under each bough), a trunk at the foot."""
    o = []
    tiers = max(4, int(h / 9))
    top = base - h * .93
    polys, light, shade, under = [], [], [], []
    for k in range(tiers):
        t0 = k / tiers
        t1 = (k + 1) / tiers
        ya = top + (base - h * .07 - top) * max(0, t0 - .08)
        yb = top + (base - h * .07 - top) * t1
        hw = h * wfac * (t1 ** .9) * rng.uniform(.9, 1.08) + 1
        droop = (yb - ya) * .35
        L = [(x, ya), (x - hw * .55, yb - droop * .6), (x - hw, yb + droop * .3), (x - hw * .7, yb - droop * .1),
             (x - hw * .45, yb + droop * .2), (x - hw * .15, yb), (x, yb + droop * .25)]
        R = [(x + hw * .15, yb), (x + hw * .45, yb + droop * .2), (x + hw * .7, yb - droop * .1),
             (x + hw, yb + droop * .3), (x + hw * .55, yb - droop * .6)]
        poly = L + R
        polys.append(poly)
        light.append(L + [(x, ya)])
        shade.append([(x, ya)] + [(x, yb + droop * .25)] + R)
        under.append([(x - hw * .7, yb - droop * .1), (x - hw * .45, yb + droop * .2), (x - hw * .15, yb),
                      (x, yb + droop * .25), (x + hw * .15, yb), (x + hw * .45, yb + droop * .2), (x + hw * .7, yb - droop * .1)])
    trunk = [(x - h * .025, base - h * .1), (x + h * .025, base - h * .1), (x + h * .035, base), (x - h * .035, base)]
    o.append(_P(_d(trunk, True, 0), pat("G"), .5))
    for k, poly in enumerate(polys):
        o.append(_P(_d(poly, True, .1), "#fff", .5))
        o.append(_P(_lines(C.hatch_poly(light[k], 25, 3 if dark == "M" else 2)) +
                    _lines(C.hatch_poly(shade[k], -25, 1.5)), sw=.5))
        o.append(_P(_d(under[k], False, .1), sw=1.5))
    return "".join(o)


def _log_slab(cx, cy, rx, ry, depth, rng):
    """A cut log slab standing on edge, its sawn face toward the viewer: the bark rim runs back to
    the left (dark, furrowed in white), the face carries growth rings, a check and the pith."""
    o = []
    arc = [(cx - depth + rx * math.cos(t), cy + ry * math.sin(t)) for t in [PI / 2 + PI * k / 24 for k in range(25)]]
    body = [(cx, cy + ry)] + arc + [(cx, cy - ry)]
    o.append(_P(_d(body, True, .1), pat("G"), 1.))
    fur = []
    for k in range(1, 10):
        t = PI / 2 + PI * k / 10
        y = cy + ry * math.sin(t)
        x0 = cx - depth + rx * math.cos(t) + .8
        fur.append([(x0, y), (x0 + depth * .45, y + rng.uniform(-.7, .7)), (cx - rx * .2, y + rng.uniform(-.5, .5))])
    o.append(f'<path d="{_lines(fur, .1)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    face = _ell(cx, cy, rx, ry, 44)
    o.append(_P(_d(face, True, .1), "#fff", 1.5))
    rings = []
    n = max(4, int(rx / 1.7))
    ox, oy = rx * .14, -ry * .12
    for k in range(1, n):
        f = k / n
        rings.append([(cx + ox * (1 - f) + rx * f * math.cos(t) * (1 + .05 * math.sin(5 * t + k * 1.7)),
                       cy + oy * (1 - f) + ry * f * math.sin(t) * (1 + .05 * math.sin(5 * t + k * 1.7)))
                      for t in [2 * PI * j / 40 for j in range(41)]])
    o.append(_P(_lines(rings, .15), sw=.5))
    o.append(_P(_d([(cx + ox, cy + oy), (cx + rx * .62, cy + ry * .68)], tol=0), sw=1.))
    o.append(_P(_d(_ell(cx + ox, cy + oy, .9, .9, 8), True, 0), "#000"))
    # cast shadow on the right of the face's rim and on the grass
    o.append(_P(_d(_ell(cx, cy, rx + .7, ry + .7, 40, -.3, PI * .7), tol=.1), sw=1.5))
    return "".join(o)


def _snare(cx, cy, s):
    """Parker's egg: a little Timbers Army snare with crossed sticks. s ~ drum radius."""
    o = []
    hgt = s * .9
    top = _ell(cx, cy, s, s * .35, 28)
    body = [(cx - s, cy)] + [(cx + s * math.cos(t), cy + hgt + s * .35 * math.sin(t)) for t in
                             [PI - PI * k / 14 for k in range(15)]][::-1][::-1] + [(cx + s, cy)]
    body = [(cx - s, cy), (cx - s, cy + hgt)] + \
        [(cx + s * math.cos(t), cy + hgt + s * .35 * math.sin(t)) for t in [PI - PI * k / 14 for k in range(15)]] + \
        [(cx + s, cy)]
    o.append(_P(_d(body, True, .1), "#fff", 1.))
    o.append(_P(_lines(C.hatch_poly(body, 90, 1.5)), sw=.5))
    # tension rods
    rods = [[(cx + s * math.cos(t), cy + s * .35 * math.sin(t) + 1), (cx + s * math.cos(t), cy + hgt + s * .35 * math.sin(t) - 1)]
            for t in [PI * (k + .5) / 5 for k in range(5)]]
    o.append(_P(_lines(rods), "none", 1.))
    o.append(_P(_d(top, True, .1), "#fff", 1.))
    # sticks crossed over the head
    L = s * 2.1
    sticks = []
    for sgn in (-1, 1):
        a = -PI / 2 + sgn * .62
        x0, y0 = cx - sgn * s * .55, cy + s * .1
        sticks.append([(x0, y0), (x0 + L * math.cos(a), y0 + L * math.sin(a))])
    o.append(_P(_lines(sticks), "none", 1.5))
    for p in sticks:
        x1, y1 = p[1]
        o.append(_P(_d(_ell(x1, y1, 1.1, 1.1, 10), True, 0), "#000"))
    return "".join(o)


def _score(ctx):
    m = re.search(r"Last game\s+([WLD])\s+(\d+)\s*[–\-]\s*(\d+)", (ctx or {}).get("sample", ""))
    if not m:
        return "W", 1, 0
    return m.group(1), int(m.group(2)), int(m.group(3))


# ------------------------------------------------------------------------------------------------
# the vignette: everything drawn inside the field bbox and clipped to the field outline
# ------------------------------------------------------------------------------------------------

_FONT = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.6, 6), (4, 4.6), (4, 1.4), (2.6, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.4), (2.4, 3.4)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2, 3.5), (4, 0), (4, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1, 6), (2, 2.5), (3, 6), (4, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "1": [[(1, 1), (2, 0), (2, 6)], [(1, 6), (3, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1.5, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "5": [[(4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]],
    "6": [[(4, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "7": [[(0, 0), (4, 0), (1.5, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3)]],
    "9": [[(4, 3), (1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (0, 6)]],
    "-": [[(1, 3), (3, 3)]],
    ".": [[(1.8, 5.6), (2.2, 6)]],
    "\u00b7": [[(1.8, 2.8), (2.2, 3.2)]],
}


def lettering(s, cx, cy, size, track=1.6, path=None):
    """Engraved capitals as stroke paths, centred on (cx, cy), cap height `size`. With path (a list
    of centre points) the letters ride it (a banner). Returns polylines."""
    k = size / 6
    adv = [(5.4 if ch != " " else 3.4) * k + track for ch in s]
    tot = sum(adv) - track
    out = []
    if path:
        # arc-length parametrise the path
        L = [0.]
        for p, q in zip(path, path[1:]):
            L.append(L[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
        mid = L[-1] / 2

        def at(u):
            for i in range(1, len(L)):
                if L[i] >= u:
                    t = (u - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                    p, q = path[i - 1], path[i]
                    a = math.atan2(q[1] - p[1], q[0] - p[0])
                    return p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, a
            p, q = path[-2], path[-1]
            return q[0], q[1], math.atan2(q[1] - p[1], q[0] - p[0])
    u = -tot / 2
    for ch, ad in zip(s, adv):
        for stroke in _FONT.get(ch, []):
            pl = []
            for gx, gy in stroke:
                lx, ly = u + gx * k, (gy - 3) * k
                if path:
                    px, py, a = at(mid + lx)
                    pl.append((px - math.sin(a) * ly, py + math.cos(a) * ly))
                else:
                    pl.append((cx + lx, cy + ly))
            out.append(pl)
        u += ad
    return out


def _net(gx0, gx1, top, gy, bcx, bcy, br, pitch):
    """Diamond net lattice over the goal mouth, pushed outward round the ball (the bulge)."""
    out = []
    W, H = gx1 - gx0, gy - top
    span = W + H
    for sgn in (1, -1):
        c = -H
        while c <= W:
            pl = []
            for i in range(41):
                t = i / 40
                y = top + H * t
                x = gx0 + c + (H * t if sgn > 0 else H * (1 - t))
                if gx0 <= x <= gx1:
                    dx, dy = x - bcx, y - bcy
                    d = math.hypot(dx, dy)
                    R = br * 3.2
                    if 1e-6 < d < R:
                        push = (R - d) / R
                        f = 1 + push * push * 1.3 * br / max(d, br * .5)
                        x, y = bcx + dx * f, bcy + dy * f
                    y += H * .05 * math.sin(PI * min(1, max(0, (x - gx0) / W)))
                    pl.append((x, y))
                elif len(pl) > 1:
                    out.append(pl)
                    pl = []
                else:
                    pl = []
            if len(pl) > 1:
                out.append(pl)
            c += pitch
    return out


def vignette(bx, by, bw, bh, clip_d, ctx, seed=0, small=False):
    rng = random.Random(seed)
    res, gf, ga = _score(ctx)
    cid = _uid("v", bx, by, bw, bh, seed)
    o = [f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">']
    x1, y1 = bx + bw, by + bh
    hor = by + bh * (.58 if not small else .66)
    # sky: light ruled, deepening to mid rules at the top (a heavy Portland sky)
    o.append(_P(f"M{_n(bx)},{_n(by)}h{_n(bw)}v{_n(hor - by)}h{_n(-bw)}z", pat("L")))
    o.append(_P(f"M{_n(bx)},{_n(by)}h{_n(bw)}v{_n((hor - by) * .3)}h{_n(-bw)}z", pat("M")))
    if not small:
        # Mt Hood on the horizon, snow lit on the west face, the east flank ruled
        mx, mh = bx + bw * .73, bh * .36
        mt = [(mx - mh * 1.9, hor), (mx - mh * .4, hor - mh * .8), (mx - mh * .12, hor - mh * .97),
              (mx, hor - mh), (mx + mh * .2, hor - mh * .9), (mx + mh * 2., hor)]
        # morning rays fanning up from behind the peak
        rays = []
        for i in range(31):
            a = PI + PI * (i + .5) / 31
            r0, r1 = mh * .35, bw * 1.2
            if i % 2:
                r1 = bw * .5
            rays.append([(mx + r0 * math.cos(a), hor - mh * .7 + r0 * math.sin(a)), (mx + r1 * math.cos(a), hor - mh * .7 + r1 * math.sin(a))])
        o.append(f'<path d="{_lines(rays)}" fill="none" stroke="#fff" stroke-width="1"/>')
        o.append(_P(_d(mt, True, 0), "#fff", .5))
        flank = [(mx, hor - mh), (mx + mh * .2, hor - mh * .9), (mx + mh * 2., hor), (mx + mh * .25, hor),
                 (mx + mh * .15, hor - mh * .45), (mx - mh * .05, hor - mh * .72)]
        o.append(_P(_lines(C.hatch_poly(flank, 62, 1.5)), sw=.5))
        snow = [(mx - mh * 1.9, hor), (mx - mh * 1.1, hor - mh * .42), (mx - mh * .8, hor - mh * .5),
                (mx - mh * .6, hor - mh * .4), (mx - mh * .35, hor - mh * .58), (mx - mh * .1, hor - mh * .46),
                (mx + mh * .25, hor)]
        o.append(_P(_lines(C.hatch_poly(snow, 0, 2)), sw=.5))
        o.append(_P(_lines([[(mx - mh * .3, hor - mh * .7), (mx - mh * .55, hor - mh * .52)],
                            [(mx + mh * .02, hor - mh * .9), (mx - mh * .1, hor - mh * .62)]]), sw=.5))
        # distant fir line along the horizon
        ridge = [(bx, hor + 1)]
        x = bx
        while x < x1:
            hh = rng.uniform(.035, .075) * bh
            ridge += [(x + 1.7, hor - hh), (x + 3.4, hor - hh * .4)]
            x += rng.uniform(3.4, 5.5)
        ridge += [(x1, hor + 1)]
        o.append(_P(_d(ridge, True, 0), pat("G")) + _P(_d(ridge[1:-1], False, 0), sw=.5))
    # pitch: mowed stripes converging on a vanishing point high above the goal
    vx, vy = bx + bw / 2, hor - bh * 1.6
    for k in range(-16, 16):
        def at(kk, y):
            x0 = vx + kk * bw * .085
            return (vx + (x0 - vx) * (y - vy) / (hor - vy), y)
        poly = [at(k, hor), at(k + 1, hor), at(k + 1, y1 + 2), at(k, y1 + 2)]
        o.append(_P(_d(poly, True, 0), pat("M" if k % 2 else "D")))
    o.append(_P(f"M{_n(bx)},{_n(hor)}h{_n(bw)}", sw=1.))
    # the goal, set back on the goal line
    gw = bw * (.5 if not small else .62)
    gx0, gx1 = vx - gw / 2, vx + gw / 2
    gh = bh * (.33 if not small else .48)
    gy = hor + bh * (.07 if not small else .05)
    # chalk: goal line, six-yard box and the penalty spot, white
    box = [(gx0 - gw * .14, gy), (gx0 - gw * .22, y1 - bh * .14), (gx1 + gw * .22, y1 - bh * .14), (gx1 + gw * .14, gy)]
    chalk = [[(bx, gy), (x1, gy)], box]
    o.append(f'<path d="{_lines(chalk)}" fill="none" stroke="#fff" stroke-width="2"/>')
    dep = gh * .3
    back_top = gy - gh + dep * .15
    inset = gw * .06
    mouth = [(gx0, gy), (gx0, gy - gh), (gx1, gy - gh), (gx1, gy)]
    # the shadowed inside of the goal, then the net lattice in white
    o.append(_P(_d(mouth, True, 0), pat("G")))
    o.append(_P(_lines(C.hatch_poly([(gx0 + inset, gy - dep * .3), (gx0 + inset, back_top),
                                     (gx1 - inset, back_top), (gx1 - inset, gy - dep * .3)], 90, 3)), sw=.5))
    br = max(4.5, min(bw, bh) * (.08 if not small else .17))
    bcx = gx1 - gw * .24 if not small else vx + gw * .13
    bcy = gy - gh * .62 if not small else gy - gh * .52
    pitch = 4. if not small else 3.
    net = _net(gx0, gx1, gy - gh, gy, bcx, bcy, br, pitch)
    o.append(f'<path d="{_lines(net, .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    # stanchions and the back bar
    st = [[(gx0 + inset, gy - dep * .3), (gx0 + inset, back_top), (gx1 - inset, back_top), (gx1 - inset, gy - dep * .3)]]
    o.append(f'<path d="{_lines(st)}" fill="none" stroke="#fff" stroke-width="1.5"/>')
    # posts and crossbar: white, outlined, shadow line under the bar and right of each post
    pw = max(2., bw * .014)
    frame = [(gx0 - pw, gy + .5), (gx0 - pw, gy - gh - pw), (gx1 + pw, gy - gh - pw), (gx1 + pw, gy + .5),
             (gx1, gy + .5), (gx1, gy - gh), (gx0, gy - gh), (gx0, gy + .5)]
    o.append(_P(_d(frame, True, 0), "#fff", .5))
    o.append(f'<path d="M{_n(gx0)},{_n(gy)}V{_n(gy - gh)}H{_n(gx1)}V{_n(gy)}" fill="none" stroke="#000" stroke-width="1"/>')
    # cast shadow of the goal on the grass
    o.append(_P(_d([(gx0 - pw, gy + .8), (gx1 + pw, gy + .8), (gx1 + pw + gw * .1, gy + 3.5), (gx0 - pw + gw * .1, gy + 3.5)], True, 0), "#000"))
    if not small:
        # the ball's flight: white wake lines, edged, curling back to a strike point low left
        tr = []
        for k in (-.45, 0., .45):
            p0 = (bcx - br * 1.15, bcy + k * br)
            pts = []
            for i in range(13):
                t = i / 12
                pts.append((p0[0] - t * bw * (.3 - abs(k) * .12), p0[1] + t * t * bh * .2 + k * br * t * .6))
            tr.append(pts)
        o.append(f'<path d="{_lines(tr, .2)}" fill="none" stroke="#000" stroke-width="2"/>')
        o.append(f'<path d="{_lines(tr, .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    o.append(football(bcx, bcy, br, (.5 + seed % 7 * .2, .35, .3)))
    if not small:
        # Douglas firs framing the scene, the near ones tall and dark at the edges
        base = hor + bh * .12
        for (fx, fh, fd) in ((bx + bw * .19, bh * .44, "M"), (x1 - bw * .175, bh * .4, "M"),
                             (bx + bw * .07, bh * .7, "G"), (x1 - bw * .06, bh * .64, "G")):
            o.append(_fir_svg(fx, base + (fh - bh * .4) * .3, fh, rng, fd, .25))
        # log slabs, Timber Joey's: one for each goal of the last win
        nlog = max(1, min(4, gf)) if res == "W" else 1
        lr = bh * .12
        for k in range(nlog - 1, -1, -1):
            lx = bx + bw * .25 + k * lr * 1.25
            ly = y1 - bh * .17 + k * lr * .18
            o.append(_log_slab(lx, ly, lr * .8, lr, lr * .55, rng))
        # Parker's egg: a Timbers Army snare with crossed sticks, bottom right in the grass
        o.append(_snare(x1 - bw * .3, y1 - bh * .2, max(4.5, bh * .05)))
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# frame layouts (copied from engraving_codex and adapted so the vignette fills the whole field)
# ------------------------------------------------------------------------------------------------

def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _ball_eye(main_cv_spine_end, r):
    x, y = main_cv_spine_end
    return football(x, y, r, (.9, .4, .1))


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(_uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    # Parker's egg: crossed drumsticks behind the medallion, like swords behind a shield
    for sgn in (-1, 1):
        x0, y0, x1_, y1_ = cx - sgn * rx * 1.5, cy + ry * .98, cx + sgn * rx * 1.5, cy - ry * .98
        a = math.atan2(y1_ - y0, x1_ - x0)
        nx, ny = -math.sin(a), math.cos(a)
        wb, wt = 2.6, 1.5
        L = math.hypot(x1_ - x0, y1_ - y0)
        stick = [(x0 + nx * wb, y0 + ny * wb), (x0 + math.cos(a) * L * .92 + nx * wt, y0 + math.sin(a) * L * .92 + ny * wt),
                 (x0 + math.cos(a) * L * .92 - nx * wt, y0 + math.sin(a) * L * .92 - ny * wt), (x0 - nx * wb, y0 - ny * wb)]
        o.append(_P(_d(stick, True, 0), "#fff", 1.))
        o.append(_P(_d([(x0 + nx * wb * .2, y0 + ny * wb * .2), (x0 + math.cos(a) * L * .9, y0 + math.sin(a) * L * .9)], tol=0), sw=.5))
        o.append(_P(_d(_ell(x0 + math.cos(a) * L * .96, y0 + math.sin(a) * L * .96, 3., 2.2, 12), True, 0), "#fff", 1.))
    o.append(C._medallion(cx, cy, rx, ry))
    clip = _d(_ell(cx, cy, rx - 4, ry - 4, 64), True, 0)
    o.append(vignette(cx - rx + 4, cy - ry + 4, 2 * rx - 8, 2 * ry - 8, clip, ctx, seed, small=True))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.6)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        a0, flip = (90, True) if side < 0 else (90, False)
        C._volute(main, vx, vy, r, a0, 1.4, flip, random.Random(seed * 3 + side), .9, -.5, r * .15, 3)
        sp = C.volute_spine(vx, vy, r, a0, 1.4, flip, .9, -.5)
        eyes.append((sp[-1], r))
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    for (ex, ey), rr in eyes:
        o.append(football(ex, ey, max(4., rr * .13), (.9, .4, .1), shade=rr * .13 > 6))
    c, _, clip = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, cw, gh + 4)
    o.append(vignette(fx, fy, fw, fh, clip, ctx, seed))
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
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.insert(0, C.dark_ground((0, 0, w, py0 - 3.5), "L"))
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .62
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        a0, flip = (90 + 10, True) if side < 0 else (90 - 10, False)
        C._volute(main, vx, vy, r1, a0, 1.45, flip, random.Random(seed * 5 + side), .8, -.5, r1 * .15, 3)
        eyes.append((C.volute_spine(vx, vy, r1, a0, 1.45, flip, .8, -.5)[-1], r1))
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
    o.append(C._clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    for (ex, ey), rr in eyes:
        o.append(football(ex, ey, max(5., rr * .12), (.9, .4, .1)))
    c, _, clip = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field(cx, cy, cw, ch)
    o.append(vignette(fx, fy, fw, fh, clip, ctx, seed))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh_ = min(22, ph * .065)
    bsvg, cl = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_P(_lines(lettering("PORTLAND TIMBERS", 0, 0, bh_ * .52, bh_ * .14, cl)), sw=1.5))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py + ped_h * .3, w, h - py - ped_h * .3), "G"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    res, gf, ga = _score(ctx)
    m = re.search(r"Last game\s+[WLD]\s+\d+\s*[\u2013\-]\s*\d+\s+(at|vs\.?)\s+([A-Za-z .]+?)\s*\u00b7", ctx.get("sample", ""))
    opp = (m.group(2).upper().replace(" FC", "") if m else "")
    txt = {"W": "WON", "L": "LOST", "D": "DREW"}[res] + f" {gf}-{ga}" + (f" \u00b7 {('AT' if m.group(1) == 'at' else 'VS')} {opp}" if m else "")
    o.append(_P(f"M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z", pat("L")))
    ls = min(th * .55, 11.)
    o.append(_P(_lines(lettering(txt, tx + tw / 2, ty + th / 2, ls, ls * .3)), "none", 3.).replace('stroke="#000"', 'stroke="#fff"'))
    o.append(f'<path d="{_lines(lettering(txt, tx + tw / 2, ty + th / 2, ls, ls * .3))}" fill="none" stroke="#000" stroke-width="1.5"/>')
    fy = py + ped_h
    fh2 = h - fy
    if fh2 > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh2 - 2), "G"))
        o.append(C._clip(_uid("f", w, h, seed), w * .06, fy, w * .88, fh2 - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx, .85)
    return C.svg_doc(w, h, body)
