"""Parker's arms, Somaster: *Or, a castle between five fleurs-de-lis sable*.

The full achievement, engraved in the manner of a Victorian armorial bookplate:

- **Shield.** A heater with an engraved edge: a fine outer line that thickens into a shadow on the
  sinister side and base, a white fillet, and a fine inner line. The field is Or after Petra Sancta, a
  light stipple of single device pixels, so the sable charges stand hard against it.
- **Castle, sable.** Two crenellated towers and a crenellated curtain wall in coursed masonry: every
  stone is cut in white line, with a broken bond. The towers carry arrow loops and a lit dexter face,
  and the gate is arched in voussoirs with a riveted portcullis.
- **Fleurs-de-lis, sable.** Three in chief and one on each flank. Each has a tall pointed centre petal,
  side petals curling out and down, a banded collar and three short feet, with one white vein. Under
  about 24 px tall the side petals close and the feet merge, so the three lobes stay crisp.
- **Helm.** A close helmet in profile, facing dexter: the helm of an untitled gentleman. It has a rounded
  dome with a low comb, contour cuts that swell toward the back and leave the brow and crown lit, a
  beaked visor with two sights and a row of breaths, the visor's edge sweeping back to its pivot, and a
  bevor curving down to the throat. A short gorget of two riveted lames sits on the chief.
- **Torse and crest.** A cord of six crisp twists, Or (stippled) and sable, across the crown, with a
  squat tower sable issuing from it, crenellated like the castle's towers. No motto.
- **Mantling.** Long acanthus ribbons, Or lined sable, flowing from under the torse, sweeping down and
  out and rolling back into volutes, with open air between them. The Or is modelled in parallel cuts
  that close up and swell into the shadowed side and into the troughs between lobes. The sable lining
  shows only where a ribbon turns over: a deep fold as it leaves the torse, a flap on its edge and the
  inside of each roll.

Under about 100 px of width the helm, crest and mantling are dropped and the shield alone fills the
box, with the masonry and fleur detail thinned so it still reads.

Shared by the Morning Edition (cover emblem, dedication cartouche, end page), the plate studios and
the Evening Edition:

    arms(w, h, seed=0) -> str        SVG child markup for a w x h box (no <svg>, no transforms)
    arms_svg(w, h, seed=0) -> str    the same wrapped in a full <svg>

The output is deterministic. The only id is the Or stipple pattern, `smst-or-{w}x{h}-{seed}`, so two
arms on one page never collide. Strokes are 0.5, 1 or 1.5 px; swelling lines are drawn as filled
lenses. White lines in black are at least 1 px. There is no <text>, no mask, no filter and no
transform.
"""
import math
import random

# design units: the shield is x 30..94, y 58..148; FULL_BOX adds the helm, crest and mantling
SX0, SX1, SY0, SY1 = 30., 94., 58., 148.
CX = (SX0 + SX1) / 2
SIDE = 102.                      # where the heater's straight sides start to curve in
# the box used when only the shield is drawn
SHIELD_BOX = (SX0 - 2.5, SY0 - 2.5, SX1 - SX0 + 5, SY1 - SY0 + 5)


def _f(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class _Map:
    """Design units -> output px: a uniform scale k, a design box centred in the w x h box."""

    def __init__(self, w, h, box):
        bx, by, bw, bh = box
        self.k = min(w / bw, h / bh)
        self.ox = (w - bw * self.k) / 2 - bx * self.k
        self.oy = (h - bh * self.k) / 2 - by * self.k

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
    if len(pts) < 2:
        return ""
    return "M" + "L".join(M.p(x, y) for x, y in pts) + ("Z" if close else "")


def _normals(pts):
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        out.append((-dy / L, dx / L))
    return out


def _lens(pts, hw, power=.7):
    """A burin cut along a polyline: a filled lens of half-width hw (design units) that swells from a
    point to hw and tapers back to a point."""
    n = len(pts)
    if n < 2:
        return []
    nr = _normals(pts)
    a, b = [], []
    for i, ((x, y), (nx, ny)) in enumerate(zip(pts, nr)):
        u = i / (n - 1)
        r = hw * math.sin(math.pi * u) ** power
        a.append((x + nx * r, y + ny * r))
        b.append((x - nx * r, y - ny * r))
    return a + b[::-1]


def _resample(pts, n):
    """n+1 points evenly spaced along a polyline."""
    d = [0.]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(bx - ax, by - ay))
    L = d[-1] or 1
    out, j = [], 0
    for i in range(n + 1):
        t = L * i / n
        while j < len(d) - 2 and d[j + 1] < t:
            j += 1
        seg = (d[j + 1] - d[j]) or 1
        u = (t - d[j]) / seg
        (ax, ay), (bx, by) = pts[j], pts[j + 1]
        out.append((ax + (bx - ax) * u, ay + (by - ay) * u))
    return out


# ------------------------------------------------------------------------------------------------
# the shield
# ------------------------------------------------------------------------------------------------

def _shield_pts(inset=0., dx=0., dy=0.):
    x0, x1, y0 = SX0 + inset, SX1 - inset, SY0 + inset
    yb = SY1 - inset * 1.5
    right = _bez((x1, SIDE), (x1, 124 - inset * .3), (CX + 17, 140 - inset * .6), (CX, yb), 22)
    left = [(2 * CX - x, y) for x, y in reversed(right)]
    pts = [(x0, y0), (x1, y0)] + right + left[1:] + [(x0, SIDE)]
    return [(x + dx, y + dy) for x, y in pts]


# ------------------------------------------------------------------------------------------------
# fleur-de-lis (sable, cut in white line)
# ------------------------------------------------------------------------------------------------

# unit space: height 2 (y -1 tip .. about +.45 feet), width about 1.75
_PETAL_C = [(0, -1), (.07, -.9), (.15, -.76), (.22, -.58), (.25, -.4), (.23, -.24), (.16, -.12), (.1, -.06),
            (-.1, -.06), (-.16, -.12), (-.23, -.24), (-.25, -.4), (-.22, -.58), (-.15, -.76), (-.07, -.9)]
_BAND = [(-.34, -.07), (.34, -.07), (.38, -.03), (.38, .07), (.34, .11), (-.34, .11), (-.38, .07), (-.38, -.03)]
_FOOT_C = [(-.09, .1), (.09, .1), (.07, .26), (0, .42), (-.07, .26)]


def _side_petal(sg):
    """The right (sg 1) or left (sg -1) petal: up and out from the collar, falling and curling in at the tip."""
    out = [(.11, -.08), (.19, -.27), (.32, -.44), (.49, -.54), (.67, -.53), (.81, -.42), (.88, -.25), (.87, -.06),
           (.8, .1), (.69, .22), (.58, .28), (.51, .26), (.52, .19), (.57, .12), (.61, .03), (.62, -.08),
           (.58, -.18), (.51, -.24), (.43, -.23), (.35, -.17), (.29, -.1), (.26, -.07)]
    return [(sg * x, y) for x, y in out]


def _side_foot(sg):
    out = [(.12, .1), (.29, .1), (.35, .19), (.39, .33), (.32, .36), (.25, .25), (.15, .18)]
    return [(sg * x, y) for x, y in out]


def _side_petal_small(sg):
    """The side petal simplified for small sizes: a full lobe with its tip closed, no hook to fill in."""
    out = [(.11, -.08), (.2, -.3), (.34, -.48), (.52, -.57), (.7, -.55), (.84, -.43), (.9, -.24), (.86, -.04),
           (.76, .13), (.62, .26), (.5, .26), (.52, .14), (.56, .02), (.52, -.12), (.42, -.18), (.32, -.12),
           (.26, -.07)]
    return [(sg * x, y) for x, y in out]


_FEET_SMALL = [(-.36, .1), (.36, .1), (.34, .26), (.2, .2), (.06, .3), (0, .42), (-.06, .3), (-.2, .2), (-.34, .26)]


def _fleur(M, cx, cy, s):
    """A fleur-de-lis s design units tall at (cx, cy): solid sable, one white vein. Returns (black d, white d).
    Under about 24 px tall the silhouette is simplified so its three lobes stay crisp."""
    S = s / 2
    T = lambda pts: [(cx + x * S, cy + y * S) for x, y in pts]
    if S * M.k < 12:
        parts = [_PETAL_C, _BAND, _FEET_SMALL, _side_petal_small(1), _side_petal_small(-1)]
    else:
        parts = [_PETAL_C, _BAND, _FOOT_C, _side_petal(1), _side_petal(-1), _side_foot(1), _side_foot(-1)]
    blk = "".join(_poly(M, T(_spline(p, 3) if len(p) > 8 else p)) for p in parts)
    wl = ""
    if S * M.k >= 9:
        wl = _poly(M, _lens(T(_resample([(0, -.84), (0, -.5), (0, -.16)], 10)), .5 / M.k, .6))
    return blk, wl


# ------------------------------------------------------------------------------------------------
# the castle (sable, coursed masonry in white line)
# ------------------------------------------------------------------------------------------------

def _loop(M, sx, sy, sh, sw):
    """An arrow loop: a narrow slit with a round oillet at its foot, cut white."""
    r = sw * .5
    top = [(sx - r * math.cos(math.pi * i / 6), sy + r - r * math.sin(math.pi * i / 6)) for i in range(7)]
    d = _poly(M, top + [(sx + r, sy + sh), (sx - r, sy + sh)])
    if M.k >= 1.:
        ro = max(sw * .95, 1.25 / M.k)
        d += _poly(M, [(sx + ro * math.cos(math.pi * i / 6), sy + sh + ro * math.sin(math.pi * i / 6)) for i in range(12)])
    return d


def _castle(M, OR):
    k = M.k
    base = 128.
    lt, rt = (42.5, 53.5), (70.5, 81.5)       # tower x spans
    ty, wy = 92., 106.                        # tower and wall tops (below the merlons)
    mh = 4.6                                  # merlon height
    gx0, gx1, gy = 57.5, 66.5, 117.           # the gate: jambs and springing line
    gr = (gx1 - gx0) / 2
    o = []

    def merlons(x0, x1, top, n):
        u = (x1 - x0) / (2 * n - 1)
        return [(x0 + 2 * j * u, x0 + (2 * j + 1) * u, top - mh) for j in range(n)]

    body = [
        [(lt[0], ty), (lt[1], ty), (lt[1], base), (lt[0], base)],
        [(rt[0], ty), (rt[1], ty), (rt[1], base), (rt[0], base)],
        [(lt[1] - .5, wy), (rt[0] + .5, wy), (rt[0] + .5, base), (lt[1] - .5, base)],
        # string course: a slight projecting plinth under each tower
        [(lt[0] - .8, base - 2.4), (lt[1] + .2, base - 2.4), (lt[1] + .2, base), (lt[0] - .8, base)],
        [(rt[0] - .2, base - 2.4), (rt[1] + .8, base - 2.4), (rt[1] + .8, base), (rt[0] - .2, base)],
        # corbelled parapets: the towers' tops oversail by a little
        [(lt[0] - .8, ty - .2), (lt[1] + .8, ty - .2), (lt[1] + .8, ty + 1.8), (lt[0] - .8, ty + 1.8)],
        [(rt[0] - .8, ty - .2), (rt[1] + .8, ty - .2), (rt[1] + .8, ty + 1.8), (rt[0] - .8, ty + 1.8)],
    ]
    mer = merlons(lt[0] - .8, lt[1] + .8, ty, 3) + merlons(rt[0] - .8, rt[1] + .8, ty, 3) + \
        merlons(lt[1] + 1.2, rt[0] - 1.2, wy, 4)
    for x0, x1, top in mer:
        body.append([(x0, top), (x1, top), (x1, top + mh + .3), (x0, top + mh + .3)])
    o.append(f'<path d="{"".join(_poly(M, b) for b in body)}" fill="#000"/>')

    # arrow loops: cruciform slits, cut white
    loops = []
    for x0, x1 in (lt, rt):
        c = (x0 + x1) / 2
        loops += [(c, 98.5, 6.), (c, 113., 6.)]
    if k < 1.:
        loops = [(c, y + 1, hh - 2) for c, y, hh in loops]
    sw = max(1.1 / k, .9)
    ld = "".join(_loop(M, sx, sy, sh, sw) for sx, sy, sh in loops)
    # masonry: coursed stones in white line, each course broken by staggered vertical joints
    course = 3.4 if k >= 1.2 else 4.6
    hz, vt = "", ""

    def blocked(x, y):
        for sx, sy, sh in loops:
            if abs(x - sx) < 2.4 and sy - 1. <= y <= sy + sh + 1.:
                return True
        return gx0 - 1.6 < x < gx1 + 1.6 and y > gy - gr - 2.6

    def run(x0, x1, y):
        """A horizontal course line from x0 to x1, broken where a loop or the gate sits."""
        nonlocal hz
        xs = [x0]
        x = x0
        step = .25
        segs, cur = [], None
        while x <= x1 + 1e-6:
            b = blocked(x, y)
            if not b and cur is None:
                cur = x
            if b and cur is not None:
                segs.append((cur, x - step))
                cur = None
            x += step
        if cur is not None:
            segs.append((cur, x1))
        for a, b in segs:
            if b - a > .9:
                hz += f"M{M.p(a, y)}H{_f(M.xy(b, y)[0])}"
        return xs

    pieces = [(lt[0] + .3, lt[1] - .3, ty + 2.6), (rt[0] + .3, rt[1] - .3, ty + 2.6),
              (lt[1] + .3, rt[0] - .3, wy + 1.4)]
    for x0, x1, top in pieces:
        y, row = top + course, 0
        while y < base - 2.6:
            run(x0, x1, y)
            if k >= 1.:
                # vertical joints for the stones of the course above this line
                stone = 4.4 if k >= 1.6 else 5.4
                off = (row % 2) * stone / 2
                x = x0 + off + stone * .6
                while x < x1 - .8:
                    yy0, yy1 = y - course + .5, y - .5
                    if yy0 < top - .2:
                        yy0 = top
                    if not blocked(x, (yy0 + yy1) / 2) and not blocked(x, yy0) and not blocked(x, yy1):
                        vt += f"M{M.p(x, yy0)}V{_f(M.xy(x, yy1)[1])}"
                    x += stone
            y += course
            row += 1
    # the plinth's top edge and the parapet's corbel line, lit
    for x0, x1 in (lt, rt):
        hz += f"M{M.p(x0 - .4, base - 2.4 + .6 / k)}H{_f(M.xy(x1 + .4, 0)[0])}"
    o.append(f'<path d="{hz}{vt}" stroke="#fff" stroke-width="1" fill="none" stroke-linecap="butt"/>')
    o.append(f'<path d="{ld}" fill="#fff"/>')

    # shaded towers: the dexter face of each tower is lit, so a few white lines model it
    if k >= 1.2:
        sh = ""
        for x0, x1 in (lt, rt):
            for i, f in enumerate((1.0, 2.6) if k >= 2 else (1.1,)):
                x = x0 + f * (1.6 / k) + .2
                y0, y1 = ty + 2.4, base - 3.
                sh += _poly(M, _lens(_resample([(x, y0), (x, y1)], 14), .5 / k * (1 - i * .3), .4))
        o.append(f'<path d="{sh}" fill="#fff"/>')

    # the gate: an arch of voussoirs opening onto the Or field, closed by a riveted portcullis
    arch = [(gx0, base), (gx0, gy)] + [(CX - gr * math.cos(math.pi * i / 16), gy - gr * math.sin(math.pi * i / 16))
                                       for i in range(1, 16)] + [(gx1, gy), (gx1, base)]
    o.append(f'<path d="{_poly(M, arch)}" fill="{OR}"/>')
    pd = ""
    bar = 1.5 if k >= 2 else 1
    x = gx0 + 1.6
    xs = []
    while x < gx1 - .9:
        xs.append(x)
        # vertical bars end in spikes at the foot
        top = gy - math.sqrt(max(0, gr * gr - (x - CX) ** 2)) + .4
        pd += f"M{M.p(x, top)}V{_f(M.xy(x, base - 1.6)[1])}"
        x += 2.2 if k >= 1.6 else 2.6
    ys = [y for y in (gy - gr + 3.2, gy + .2, gy + 3.6, gy + 7.) if y < base - 2.]
    for y in ys:
        pd += f"M{M.p(gx0, y)}H{_f(M.xy(gx1, y)[0])}"
    o.append(f'<path d="{pd}" stroke="#000" stroke-width="{bar}" fill="none"/>')
    spikes = "".join(_poly(M, [(x - .7, base - 1.8), (x + .7, base - 1.8), (x, base - .2)]) for x in xs)
    o.append(f'<path d="{spikes}" fill="#000"/>')
    if k >= 2:
        rv = ""
        for x in xs:
            for y in ys:
                rv += f'M{_f(M.xy(x, y)[0] - .5)},{_f(M.xy(x, y)[1])}h1'
        o.append(f'<path d="{rv}" stroke="#fff" stroke-width="1" fill="none"/>')
    # voussoirs: the arch ring outlined in white, with radial joints
    if k >= 1.:
        rr = gr + 1.9
        ring = [(CX - (gr + .9) * math.cos(math.pi * i / 16), gy - (gr + .9) * math.sin(math.pi * i / 16)) for i in range(17)]
        vd = _poly(M, [(gx0 - .9, gy + 2)] + ring + [(gx1 + .9, gy + 2)], False)
        for i in range(1, 8):
            a = math.pi * i / 8
            vd += (f"M{M.p(CX - (gr + .2) * math.cos(a), gy - (gr + .2) * math.sin(a))}"
                   f"L{M.p(CX - rr * math.cos(a), gy - rr * math.sin(a))}")
        o.append(f'<path d="{vd}" stroke="#fff" stroke-width="1" fill="none"/>')
    # a black line round the gate so the dots meet a clean edge
    o.append(f'<path d="{_poly(M, arch, False)}" stroke="#000" stroke-width="1" fill="none"/>')
    return o



# ------------------------------------------------------------------------------------------------
# mantling: long acanthus ribbons, Or lined sable
# ------------------------------------------------------------------------------------------------

def _spine(p0, p1, p2, p3, curl, R0, turn=8.4):
    """A cubic sweep ending in a logarithmic volute of starting radius R0 (turn sign curl).
    Returns (points, index where the volute starts, radius at each point)."""
    pts = _bez(p0, p1, p2, p3, 40)
    rad = [None] * len(pts)
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    a0 = math.atan2(by - ay, bx - ax)
    # centre of the volute: to the curl side of the end point
    nx, ny = -math.sin(a0) * curl, math.cos(a0) * curl
    cx, cy = bx + nx * R0, by + ny * R0
    phi0 = math.atan2(by - cy, bx - cx)
    b = math.log(4.5) / turn
    m = int(turn / .16)
    for i in range(1, m + 1):
        th = turn * i / m
        r = R0 * math.exp(-b * th)
        ph = phi0 + curl * th
        pts.append((cx + r * math.cos(ph), cy + r * math.sin(ph)))
        rad.append(r)
    return pts, 41, rad


def _plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _ribbon(sp, wmax, lobes, curl, k, fold=True):
    """One mantling ribbon: a broad acanthus leaf that sweeps out and rolls into a volute. Returns
    polygons by role: face (Or), lining (sable, only where it turns over: a flap on the outer edge and
    the inside of the roll), lines (burin shading), hi (white cuts on the sable)."""
    lw = 1 / k
    spine, jv, rad = sp
    n = len(spine)
    nr = _normals(spine)
    s = -curl                     # +s: the lobed outer edge, lit; -s: the inner edge, toward the roll
    W, O, I, bumps = [], [], [], []
    for i, ((x, y), (nx, ny)) in enumerate(zip(spine, nr)):
        if i < jv:
            v = i / (jv - 1)
            wv = wmax * (.4 + .6 * math.sin(math.pi * min(1, v * 1.6) * .5) ** 1.2) * (1 - .42 * v ** 2)
            ph = (v * lobes) % 1
            ph = ph ** 1.2
            bump = (1 - abs(2 * ph - 1)) ** 2.2 if v > .1 else 0
        else:
            wv = min(wmax * .58, .62 * rad[i]) + .4 * lw
            bump = 0
        W.append(wv)
        bumps.append(bump)
        wo = wv * (.44 + .28 * bump)
        wi = wv * .46
        O.append((x + s * nx * wo, y + s * ny * wo))
        I.append((x - s * nx * wi, y - s * ny * wi))
    face = [O + I[::-1]]
    lining, hi, lines = [], [], []
    # inside the roll the lining shows: a sable strip on the inner side of the volute, and the eye
    rb = [(spine[i][0] - s * nr[i][0] * W[i] * .46 * (1 - 2 * min(1, (i - jv + 1) / 30) * .8),
           spine[i][1] - s * nr[i][1] * W[i] * .46 * (1 - 2 * min(1, (i - jv + 1) / 30) * .8)) for i in range(jv - 1, n)]
    lining.append(I[jv - 1:] + rb[::-1])
    ex, ey = spine[-1]
    er = max(1.1 * lw, rad[-1] * .5)
    lining.append([(ex + er * math.cos(t * math.pi / 6), ey + er * math.sin(t * math.pi / 6)) for t in range(12)])
    # a flap: the outer edge turns over for a stretch and shows its lining
    if fold:
        a, b = int(jv * .46), int(jv * .66)
        fo, fi = [], []
        for i in range(a, b + 1):
            t = (i - a) / (b - a)
            (x, y), (nx, ny) = spine[i], nr[i]
            d = W[i] * .36 * math.sin(math.pi * t ** .8) ** .9
            fo.append(O[i])
            fi.append((O[i][0] - s * nx * d, O[i][1] - s * ny * d))
        lining.append(fo + fi[::-1])
        mid = [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2) for p, q in zip(fo, fi)][2:-2]
        if len(mid) > 3 and W[(a + b) // 2] * .36 * k > 3.5:
            hi.append(_lens(mid, .5 * lw, .6))
    # Or modelled in fine parallel cuts along the ribbon: close and swelling on the inner, shadowed
    # side, thinning out toward the lit lobed edge, and carried on round the roll
    nl = max(3, min(14, int(wmax * .7 * k / 2.6)))
    for q in range(nl):
        f = -.43 + q * (.68 / nl)
        hw = (.55 - .33 * q / (nl - 1)) * lw
        start = int(jv * (.04 + .1 * q / nl))
        end = min(n - 8, jv + int(40 * (1 - q / nl)))
        pts = []
        for i in range(start, end):
            pts.append((spine[i][0] + s * nr[i][0] * W[i] * f, spine[i][1] + s * nr[i][1] * W[i] * f))
        if len(pts) > 3:
            # break the lighter cuts at each lobe so they rise and fall with the leaf
            if q >= nl // 2:
                L = max(1, int(lobes))
                for j in range(L + 1):
                    a = max(0, int((j + .15) / lobes * jv) - start)
                    b = min(len(pts), int((j + .9) / lobes * jv) - start)
                    if b - a > 3:
                        lines.append(_lens(pts[a:b], hw, .7))
            else:
                lines.append(_lens(pts, hw, .6))
    # the troughs: the bays between lobes fall into shadow, cut in from the edge
    for j in range(1, max(1, int(lobes)) + 1):
        ib = int(min(jv - 2, j / lobes * jv))
        if ib < jv * .15 or ib >= jv - 2:
            continue
        for di, fl, hw in ((-1, .5, .45), (0, .62, .55), (1, .5, .45)):
            i = max(0, min(jv - 1, ib + di * max(1, int(.012 * jv))))
            p0 = O[i]
            p1 = (spine[i][0] + (O[i][0] - spine[i][0]) * (1 - fl * 2), spine[i][1] + (O[i][1] - spine[i][1]) * (1 - fl * 2))
            lines.append(_lens([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1], hw * lw, .6))
    # a deeper fold where the ribbon leaves the torse: its inner edge turns over, sable
    if fold:
        a, b = 0, int(jv * .22)
        fo, fi = [], []
        for i in range(a, b + 1):
            t = (i - a) / (b - a)
            (x, y), (nx, ny) = spine[i], nr[i]
            d = W[i] * .42 * math.sin(math.pi * (.15 + .85 * t)) ** .8
            fo.append(I[i])
            fi.append((I[i][0] + s * nx * d, I[i][1] + s * ny * d))
        lining.append(fo + fi[::-1])
        mid = [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2) for p, q in zip(fo, fi)][1:-2]
        if len(mid) > 3 and k >= 1.:
            hi.append(_lens(mid, .5 * lw, .6))
    # a vein from the midrib into each lobe point
    L = max(1, int(lobes))
    for j in range(L):
        lo, hi_ = int(j / lobes * jv), int((j + 1) / lobes * jv)
        if hi_ - lo < 2:
            continue
        best = max(range(lo, hi_), key=lambda q: bumps[q])
        if bumps[best] < .5:
            continue
        p0 = spine[max(0, best - int(.07 * jv))]
        p2 = O[best]
        lines.append(_lens([p0, ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2), (p0[0] + (p2[0] - p0[0]) * .82, p0[1] + (p2[1] - p0[1]) * .82)],
                           .5 * lw, .6))
    return {"face": face, "lines": lines, "lining": lining, "hi": hi}


# the left side; (p0, p1, p2, p3, curl, width, lobes, fold, volute radius), back to front, mirrored
_RIBBONS = [
    ((34, 62), (20, 96), (14, 126), (38, 147), -1, 11., 4, True, 5.5),
    ((46, 26), (30, 32), (24, 42), (26, 51), 1, 8., 2, False, 4.),
    ((49, 40), (24, 56), (17, 82), (23, 96), 1, 8., 3, False, 4.),
    ((50, 34), (28, 52), (5, 84), (8, 116), -1, 15., 5, True, 8.),
    ((49, 20), (26, 16), (6, 30), (4, 58), -1, 16., 4, True, 8.5),
    ((50, 14), (34, -2), (12, -8), (5, 6), -1, 13., 3, True, 7.),
]


def _mantling(M, seed):
    rng = random.Random(seed * 7919 + 17)
    k = M.k
    o = []
    mir = lambda poly: [(2 * CX - x, y) for x, y in poly]
    ow = 1
    for p0, p1, p2, p3, cs, wd, lb, fold, R0 in _RIBBONS:
        j = lambda p: (p[0] + rng.uniform(-.8, .8), p[1] + rng.uniform(-.8, .8))
        f = _ribbon(_spine(p0, j(p1), j(p2), j(p3), cs, R0), wd, lb, cs, k, fold)
        both = lambda key: f[key] + [mir(p) for p in f[key]]
        o.append(f'<path d="{"".join(_poly(M, p) for p in both("face"))}" fill="#fff" stroke="#000" '
                 f'stroke-width="{ow}" stroke-linejoin="round"/>')
        o.append(f'<path d="{"".join(_poly(M, p) for p in both("lines"))}" fill="#000"/>')
        o.append(f'<path d="{"".join(_poly(M, p) for p in both("lining"))}" fill="#000" stroke="#000" '
                 f'stroke-width="1" stroke-linejoin="round"/>')
        if f["hi"]:
            o.append(f'<path d="{"".join(_poly(M, p) for p in both("hi"))}" fill="#fff"/>')
    return o


# ------------------------------------------------------------------------------------------------
# helm, torse and crest
# ------------------------------------------------------------------------------------------------

HX, HY = 62., 16.            # helm origin: x centre, y at the top of the skull; the gorget rests on the chief at y 59

# a close helmet in profile, facing dexter: the dome, the beaked visor and the bevor, as one silhouette
SKC, SKR = (2.4, 17.2), (16., 16.6)           # the dome's centre and radii
_HELM = [(-10, 5.4), (-4.6, 2.), (2.4, .6), (9.4, 1.8), (14.6, 5.4), (17.6, 10.6), (18.6, 16.8), (18., 23.),
         (16.4, 28.4), (14.6, 32.4), (13.6, 35.4), (0, 35.8), (-11.6, 35.2), (-14.4, 33.2), (-16.8, 30.2),
         (-17.6, 27.2), (-16.6, 24.8), (-20.4, 23.6), (-25.6, 21.4), (-21.6, 17.2), (-16.6, 12.2), (-12.8, 8.2)]


def _spline(pts, m=6, closed=True):
    """A Catmull-Rom curve through pts, m points per span."""
    P = list(pts)
    n = len(P)
    out = []
    for i in range(n if closed else n - 1):
        if closed:
            p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        else:
            p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(n - 1, i + 2)]
        for j in range(m):
            t = j / m
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


def _helm(M):
    k = M.k
    lw = 1 / k
    H = lambda pts: [(HX + x, HY + y) for x, y in pts]
    o = []
    # the gorget: two short lames under the bevor, set on the chief
    lames = [(54.2, 59.6, 14.6, 17.4), (50.4, 55.2, 12.8, 15.2)]
    for y0, y1, a0, a1 in lames:
        top = [(HX + 1 + a0 * c, y0 + 1.3 * math.sqrt(max(0, 1 - c * c))) for c in [i / 12 - 1 for i in range(25)]]
        bot = [(HX + 1 + a1 * c, y1 + 1.5 * math.sqrt(max(0, 1 - c * c))) for c in [1 - i / 12 for i in range(25)]]
        o.append(f'<path d="{_poly(M, top + bot)}" fill="#fff" stroke="#000" stroke-width="1" stroke-linejoin="round"/>')
        hs = ""
        step = 2.6 / k
        x = HX + 1 - a1 + 1.
        while x < HX + 1 + a1 - .8:
            c0, c1 = (x - HX - 1) / a0, (x - HX - 1) / a1
            yt = y0 + 1.3 * math.sqrt(max(0, 1 - min(1, c0 * c0))) + .9
            yb = y1 + 1.5 * math.sqrt(max(0, 1 - c1 * c1)) - .5
            g = (x - HX - 1 + a1) / (2 * a1)
            if yb - yt > .8 and g > .3:
                hs += _poly(M, _lens([(x, yt), (x, (yt + yb) / 2), (x, yb)], (.12 + .5 * g * g) * lw, .5))
            x += step
        hs += _poly(M, _lens([(HX + 1 + a0 * c * .96, y0 + 1.3 * math.sqrt(max(0, 1 - c * c)) + .8) for c in [i / 10 - 1 for i in range(1, 20)]],
                             .5 * lw, .5))
        o.append(f'<path d="{hs}" fill="#000"/>')
        if k >= 1.2:
            rv = ""
            r = .7
            for c in (-.6, 0, .6):
                px_, py_ = M.xy(HX + 1 + a0 * c * 1.04, y0 + 1.3 * math.sqrt(1 - c * c) + 2.)
                rv += f"M{_f(px_ - r)},{_f(py_)}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0-{2 * r} 0"
            o.append(f'<path d="{rv}" fill="#000"/>')
    # the comb: a low ridge along the top of the dome
    dome = [(SKC[0] + (SKR[0] + .2) * math.cos(t), SKC[1] + (SKR[1] + .2) * math.sin(t)) for t in
            [math.radians(-148 + 128 * i / 24) for i in range(25)]]
    comb_out = [(SKC[0] + (SKR[0] + .2 + 1.7 * math.sin(math.pi * i / 24) ** .5) * math.cos(t),
                 SKC[1] + (SKR[1] + .2 + 1.7 * math.sin(math.pi * i / 24) ** .5) * math.sin(t))
                for i, t in enumerate([math.radians(-148 + 128 * i / 24) for i in range(25)])]
    comb = H(comb_out + dome[::-1])
    o.append(f'<path d="{_poly(M, comb)}" fill="#fff" stroke="#000" stroke-width="1" stroke-linejoin="round"/>')
    sk = H(_spline(_HELM, 5))
    o.append(f'<path d="{_poly(M, sk)}" fill="#fff" stroke="#000" stroke-width="1" stroke-linejoin="round"/>')
    sh = ""
    # the comb's shadow side
    sh += _poly(M, _lens(H([(SKC[0] + (SKR[0] + 1.) * math.cos(t), SKC[1] + (SKR[1] + 1.) * math.sin(t)) for t in
                            [math.radians(-110 + 85 * i / 16) for i in range(17)]]), .35 * lw, .6))
    # the dome: contour cuts following its curve, swelling toward the back and leaving the lit
    # edge on the brow and crown clear
    for d, hw in ((2.4, .35), (3.8, .45), (5.3, .55), (6.9, .6)):
        pts = [(SKC[0] + (SKR[0] - d) * math.cos(t), SKC[1] + (SKR[1] - d) * math.sin(t)) for t in
               [math.radians(-62 + 140 * i / 24) for i in range(25)]]
        sh += _poly(M, _lens(H(pts), hw * lw, 1.1))
    # the visor: the brow above the sights, then cuts along its beak, closing toward the point
    vis_top = [(-12.4, 8.8), (-16.2, 12.8), (-21., 17.6), (-24.2, 21.)]
    for f, hw in ((1.5, .45), (2.8, .38)):
        sh += _poly(M, _lens(H(_resample([(x + f * .55, y + f * .85) for x, y in vis_top], 12)), hw * lw, .7))
    for f, hw in ((.9, .55), (2., .45)):
        sh += _poly(M, _lens(H(_resample([(-23.6 + f * .3, 22.2 - f * .6), (-19.6, 22.8 - f), (-14.6, 23.4 - f), (-8, 23.6 - f * .8)], 12)),
                             hw * lw, .7))
    # the visor's edge sweeping back to its pivot, shaded beneath
    edge = H(_spline([(-11.4, 8.6), (-3.6, 9.4), (3., 12.6), (6.4, 17.6), (4.6, 22.6), (-3., 24.6), (-15.6, 24.8)], 4, False))
    under = [(x + .5, y + .7) for x, y in edge[2:-2]]
    sh += _poly(M, _lens(under, .55 * lw, .6))
    # the bevor: cuts curving down and back to the neck, heavier toward the throat
    for f, hw in ((1.2, .55), (2.6, .45), (4., .35)):
        pts = [(-15.8 + f, 25.8), (-16.6 + f, 28.4), (-15.6 + f * .9, 31.4), (-13 + f * .7, 33.8)]
        sh += _poly(M, _lens(H(_resample(pts, 10)), hw * lw, .7))
    for f, hw in ((1.6, .45), (3.2, .4)):
        pts = [(-14.8, 25.8 + f), (-6, 26.2 + f), (4, 26 + f), (12.6, 25 + f * .7)]
        sh += _poly(M, _lens(H(_resample(pts, 14)), hw * lw, .8))
    o.append(f'<path d="{sh}" fill="#000"/>')
    o.append(f'<path d="{_poly(M, edge, False)}" fill="none" stroke="#000" stroke-width="1"/>')
    # the sights: two horizontal eye-slots across the visor, cut dark
    sl = ""
    for (x0, y0), (x1, y1), hw in (((-21.2, 16.9), (-8.6, 13.6), .75), ((-19.6, 19.4), (-7.6, 16.8), .6)):
        pts = _resample([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 - .3), (x1, y1)], 10)
        sl += _poly(M, _lens(H(pts), max(hw, .75 / k), .25))
    # the breaths: a few small holes on the lower visor
    if k >= .9:
        r = max(.6 * k, .75)
        for x, y in ((-18.2, 22.), (-15.2, 22.4), (-12.2, 22.6), (-9.2, 22.6)):
            px_, py_ = M.xy(HX + x, HY + y)
            sl += f"M{_f(px_ - r)},{_f(py_)}a{_f(r)} {_f(r)} 0 1 0 {_f(2 * r)} 0a{_f(r)} {_f(r)} 0 1 0-{_f(2 * r)} 0"
    o.append(f'<path d="{sl}" fill="#000"/>')
    # the pivot: a small domed rivet where the visor turns
    bx, by = M.xy(HX + 5.8, HY + 17.6)
    r = max(1.1, 1.2 * k)
    o.append(f'<circle cx="{_f(bx)}" cy="{_f(by)}" r="{_f(r)}" fill="#000"/>')
    if r >= 2.5:
        o.append(f'<circle cx="{_f(bx - r * .3)}" cy="{_f(by - r * .3)}" r="{_f(max(.5, r * .3))}" fill="#fff"/>')
    return o


def _torse(M, OR):
    """A wreath of six twists, Or and sable, lying across the crown like a cord."""
    k = M.k
    half, th, n, sk = 19.5, 6.6, 6, 3.4
    yc = lambda x: HY + 1.6 + .011 * (x - HX) ** 2
    xs = [HX - half + 2 * half * i / n for i in range(n + 1)]

    def bound(i):
        """The S-curved seam between twists i-1 and i, from the top edge to the bottom."""
        x = xs[i]
        if i == 0 or i == n:
            sg = -1 if i == 0 else 1
            return [(x + sk * .5 - sk * t / 8 + sg * 1.1 * math.sin(math.pi * t / 8), yc(x) - th / 2 + th * t / 8) for t in range(9)]
        return [(x + sk * .5 - sk * t / 8 + .7 * math.sin(2 * math.pi * t / 8), yc(x) - th / 2 + th * t / 8) for t in range(9)]

    orp, sbp, lines, hl = "", "", "", ""
    for i in range(n):
        A, B = bound(i), bound(i + 1)
        top = [(A[0][0] + (B[0][0] - A[0][0]) * t / 6, 0) for t in range(7)]
        top = [(x, yc(x) - th / 2 - .55 * math.sin(math.pi * t / 6)) for t, (x, _) in enumerate(top)]
        bot = [(B[-1][0] + (A[-1][0] - B[-1][0]) * t / 6, 0) for t in range(7)]
        bot = [(x, yc(x) + th / 2 + .55 * math.sin(math.pi * t / 6)) for t, (x, _) in enumerate(bot)]
        pts = top + B[1:] + bot[1:] + A[::-1][1:-1]
        if i % 2 == 0:
            orp += _poly(M, pts)
            # the Or twist rounds into shadow along its lower seam
            for f, hw in ((.7, .5), (.86, .55)):
                lines += _poly(M, _lens([(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f) for a, b in zip(A, B)][1:-1], hw / k, .6))
        else:
            sbp += _poly(M, pts)
            hl += _poly(M, _lens([(a[0] + (b[0] - a[0]) * .3, a[1] + (b[1] - a[1]) * .3) for a, b in zip(A, B)][1:-1], .55 / k, .6))
    return [f'<path d="{orp}" fill="{OR}" stroke="#000" stroke-width="1" stroke-linejoin="round"/>',
            f'<path d="{lines}" fill="#000"/>',
            f'<path d="{sbp}" fill="#000" stroke="#000" stroke-width="1" stroke-linejoin="round"/>',
            f'<path d="{hl}" fill="#fff"/>']


def _crest(M):
    """A tower sable issuing from the torse, squat, crenellated like the castle's towers."""
    k = M.k
    cx, foot = HX, HY + 2.
    x0, x1 = cx - 8.6, cx + 8.6
    top = HY - 12.4           # the parapet; merlons rise above it
    mh = 4.6
    body = [[(x0, top), (x1, top), (x1 + .5, foot), (x0 - .5, foot)],
            [(x0 - 1., top - .4), (x1 + 1., top - .4), (x1 + 1., top + 2.), (x0 - 1., top + 2.)]]
    u = (x1 - x0 + 2.) / 5
    for j in range(3):
        a = x0 - 1. + 2 * j * u
        body.append([(a, top - mh), (a + u, top - mh), (a + u, top), (a, top)])
    o = [f'<path d="{"".join(_poly(M, b) for b in body)}" fill="#000"/>']
    d = ""
    course = 3.4 if k >= 1.2 else 4.4
    lt, lb = top + 3.6, top + 10.
    y = top + 2. + course
    row = 0
    while y < foot - 1.:
        if lt - 1 < y < lb + 2.4:
            d += f"M{M.p(x0 + .6, y)}H{_f(M.xy(cx - 2., y)[0])}M{M.p(cx + 2., y)}H{_f(M.xy(x1 - .6, y)[0])}"
        else:
            d += f"M{M.p(x0 + .6, y)}H{_f(M.xy(x1 - .6, y)[0])}"
        if k >= 1.:
            st = 4.4
            x = x0 + .6 + (row % 2) * st / 2 + st * .55
            while x < x1 - .8:
                if abs(x - cx) > 2.2 or not (lt - 1 < y < lb + 4):
                    d += f"M{M.p(x, y - course + .5)}V{_f(M.xy(x, y - .5)[1])}"
                x += st
        y += course
        row += 1
    if k >= 1.2:
        d += f"M{M.p(x0 + 1.2 / k + .1, top + 2.6)}V{_f(M.xy(0, foot - 2.)[1])}"
    o.append(f'<path d="{d}" stroke="#fff" stroke-width="1" fill="none"/>')
    sw = max(1.1 / k, .9)
    o.append(f'<path d="{_loop(M, cx, lt, lb - lt, sw)}" fill="#fff"/>')
    return o


# ------------------------------------------------------------------------------------------------
# the arms
# ------------------------------------------------------------------------------------------------

FULL_BOX = (-4., -12., 132., 163.)


def arms(w, h, seed=0):
    """Somaster arms engraved for a w x h px box: SVG child markup, no outer <svg>, no transforms."""
    bw, bh = FULL_BOX[2], FULL_BOX[3]
    full = min(w / bw, h / bh) * bw >= 100
    M = _Map(w, h, FULL_BOX if full else SHIELD_BOX)
    k = M.k
    key = f"{int(round(w))}x{int(round(h))}-{int(seed)}"
    pid = f"smst-or-{key}"
    # Or: a light stipple of single device pixels, staggered on a 3 px lattice
    o = [f'<defs><pattern id="{pid}" width="3" height="3" patternUnits="userSpaceOnUse">'
         f'<rect width="3" height="3" fill="#fff"/><rect x=".5" y=".5" width=".5" height=".5" fill="#000"/>'
         f'<rect x="2" y="2" width=".5" height=".5" fill="#000"/></pattern></defs>']
    OR = f"url(#{pid})"
    if full:
        o += _mantling(M, seed)
    # the shield: outer line swelling to a shadow on the sinister side and base, white fillet, fine line
    sh = _shield_pts()
    o.append(f'<path d="{_poly(M, sh)}" fill="#000"/>')
    sd = 3.2 / k
    d_ = sd * .45
    o.append(f'<path d="{_poly(M, _shield_pts(d_ + 1.5 / k, -d_, -d_))}" fill="#fff"/>')
    inner = _shield_pts(2.6 / k)
    o.append(f'<path d="{_poly(M, inner)}" fill="{OR}" stroke="#000" stroke-width=".5"/>')
    o += _castle(M, OR)
    blk, wl = "", ""
    for cx, cy, s in ((44.5, 75, 17.), (62, 74, 17.), (79.5, 75, 17.), (36.4, 106, 12.5), (87.6, 106, 12.5)):
        b, l1 = _fleur(M, cx, cy, s)
        blk += b
        wl += l1
    o.append(f'<path d="{blk}" fill="#000"/>')
    if wl:
        o.append(f'<path d="{wl}" fill="#fff"/>')
    if full:
        o += _helm(M)
        o += _crest(M)
        o += _torse(M, OR)
    return "".join(o)


def arms_svg(w, h, seed=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(w)}" height="{_f(h)}" viewBox="0 0 {_f(w)} {_f(h)}">'
            + arms(w, h, seed) + "</svg>")


if __name__ == "__main__":
    import sys
    w, h = (float(a) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (160, 200)
    sys.stdout.write(arms_svg(w, h))
