"""Parker's arms, Somaster: *Or, a castle between five fleurs-de-lis sable*.

The full achievement, engraved in the manner of a 19th-century armorial bookplate:

- **Shield.** A heater with an engraved edge: a strong outer line that thickens into a shadow on the
  sinister side and base, a white fillet, and a fine inner line. The field is Or after Petra Sancta,
  an even field of fine dots. No hatching crosses the field, so the tincture stays unambiguous.
- **Castle, sable.** Two crenellated towers and a crenellated curtain wall in coursed masonry: every
  stone is cut in white line, with a broken bond. The towers carry cruciform arrow loops and a lit
  dexter face, and the gate is arched in voussoirs with a riveted portcullis.
- **Fleurs-de-lis, sable.** Three in chief and one on each flank. Each is cut with a white vein in the
  centre petal, a modelling line along each side petal and a banded collar.
- **Helm.** A barred helm in profile, turned to dexter, with a grille of bars, a pivot boss, a riveted
  gorget, and steel modelled by contour lines that swell into the shadow.
- **Torse and crest.** A torse of six twists, Or and sable, with a tower sable issuing from it (the
  castle's own tower). There is no motto.
- **Mantling.** Deep layered acanthus, Or lined sable. Every frond swells from the torse, scallops into
  serrated lobes and rolls into a tight curl that shows its sable lining. Folds are modelled with
  swelling burin lines that run dark into the turn, and the lobes are veined. A punched matte ground
  sits behind the leafwork so the relief glows out of the dark.

Under about 100 px of width the helm, crest and mantling are dropped and the shield alone fills the
box, with the masonry and fleur detail thinned so it still reads.

Shared by the Morning Edition (cover emblem, dedication cartouche, end page), the plate studios and
the Evening Edition:

    arms(w, h, seed=0) -> str        SVG child markup for a w x h box (no <svg>, no transforms)
    arms_svg(w, h, seed=0) -> str    the same wrapped in a full <svg>

The output is deterministic. The only ids are the Or dot pattern and the matte pattern, prefixed
`smst-` and keyed by size and seed, so two arms on one page never collide. Strokes are 0.5, 1 or
1.5 px; swelling lines are drawn as filled lenses. White lines in black are at least 1 px. There is no
<text>, no mask, no filter and no transform.
"""
import math
import random

# design space of the full achievement; the shield is x 30..94, y 58..148
DW, DH = 124., 155.
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

    def __init__(self, w, h, box=(0., 0., DW, DH)):
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

# unit space: height 2 (y -1 top .. +1 foot), width about 1.9
_PETAL_C = [(0, -1), (.09, -.9), (.19, -.74), (.26, -.55), (.27, -.36), (.21, -.18), (.12, -.07),
            (-.12, -.07), (-.21, -.18), (-.27, -.36), (-.26, -.55), (-.19, -.74), (-.09, -.9)]
_BAND = [(-.38, -.1), (.38, -.1), (.42, -.05), (.42, .08), (.38, .13), (-.38, .13), (-.42, .08), (-.42, -.05)]
_FOOT = [(-.13, .13), (.13, .13), (.1, .3), (.04, .5), (0, .62), (-.04, .5), (-.1, .3)]


def _side_petal(sg):
    """The right (sg 1) or left (sg -1) petal: up and out from the band, rolling over into a hooked tip."""
    out = [(.13, -.1), (.17, -.32), (.27, -.54), (.43, -.7), (.62, -.74), (.79, -.66), (.9, -.48), (.93, -.26),
           (.88, -.04), (.78, .14), (.66, .26), (.56, .3), (.5, .24), (.54, .16), (.6, .06), (.62, -.08),
           (.58, -.22), (.5, -.3), (.42, -.28), (.36, -.2), (.32, -.1)]
    return [(sg * x, y) for x, y in out]


def _foot_curl(sg):
    out = [(.1, .13), (.22, .18), (.32, .27), (.37, .4), (.33, .5), (.25, .5), (.24, .43), (.28, .4),
           (.25, .32), (.16, .27), (.07, .26)]
    return [(sg * x, y) for x, y in out]


def _fleur(M, cx, cy, s):
    """One fleur-de-lis s design units tall at (cx, cy). Returns (black d, white-lens d, white-line d)."""
    S = s / 2
    T = lambda pts: [(cx + x * S, cy + y * S) for x, y in pts]
    parts = [_PETAL_C, _BAND, _FOOT, _side_petal(1), _side_petal(-1), _foot_curl(1), _foot_curl(-1)]
    blk = "".join(_poly(M, T(p)) for p in parts)
    px = S * M.k                                  # px per unit
    wl, wln = "", ""
    lw = 1 / M.k                                  # 1 px in design units
    if px >= 7:
        # centre vein: a white lens down the centre petal
        wl += _poly(M, _lens(T([(0, -.84), (0, -.6), (0, -.38), (0, -.2)]), .75 * lw, .55))
        # the collar: white lines along the band's top and foot
        wln += f"M{M.p(*T([(-.4, -.1)])[0])}L{M.p(*T([(.4, -.1)])[0])}"
        if px >= 11:
            wln += f"M{M.p(*T([(-.4, .13)])[0])}L{M.p(*T([(.4, .13)])[0])}"
        # a modelling line along each side petal, swelling at the shoulder
        for sg in (1, -1):
            sp = [(sg * x, y) for x, y in ((.26, -.22), (.33, -.44), (.47, -.58), (.64, -.6), (.77, -.5), (.8, -.3),
                                          (.76, -.08), (.66, .12))]
            wl += _poly(M, _lens(T(_resample(sp, 12)), .7 * lw, .6))
        if px >= 13:
            # the lit edge of the centre petal and the foot curls
            for sg in (1, -1):
                sp = [(sg * x, y) for x, y in ((.07, -.86), (.15, -.72), (.19, -.52), (.18, -.32))]
                wl += _poly(M, _lens(T(_resample(sp, 8)), .55 * lw, .6))
            for sg in (1, -1):
                sp = [(sg * x, y) for x, y in ((.12, .22), (.26, .27), (.36, .38))]
                wl += _poly(M, _lens(T(_resample(sp, 6)), .55 * lw, .6))
    return blk, wl, wln


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
# mantling: acanthus, Or lined sable
# ------------------------------------------------------------------------------------------------

def _spine(p0, p1, p2, p3, curl, n=40, turns=17):
    """A cubic sweep ending in a tightening logarithmic curl (turn sign curl)."""
    pts = _bez(p0, p1, p2, p3, n)
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    a = math.atan2(by - ay, bx - ax)
    step = math.hypot(bx - ax, by - ay) * 1.1
    x, y = bx, by
    for i in range(turns):
        a += curl * (.24 + i * .04)
        step *= .86
        x, y = x + math.cos(a) * step, y + math.sin(a) * step
        pts.append((x, y))
    return pts


def _plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _frond(spine, wmax, lobes, curl, k, w0=.32):
    """One acanthus frond along spine. Returns its primitives, each a list of polygons:
    face (Or), cuts (black burin cuts modelling the fold), lining (sable), hi (white lines on the lining)."""
    lw = 1 / k
    spine = _resample(spine, max(30, int(_plen(spine) * min(k, 2.1) / 1.9)))
    n = len(spine)
    nr = _normals(spine)
    s = -curl                  # the lobed outer edge is on the side away from the curl
    tail = .72                 # where the leaf rolls over to show its lining
    outer, inner, linb, mid, widths, bumps = [], [], [], [], [], []
    for i, ((x, y), (nx, ny)) in enumerate(zip(spine, nr)):
        u = i / (n - 1)
        if u < tail:
            v = u / tail
            wv = wmax * (w0 + (1 - w0) * math.sin(math.pi * min(1, v * 1.3) * .5) ** .9) * (1 - .3 * v * v)
            ph = (u / tail * lobes) % 1
            ph = ph ** 1.35
            tri = 1 - abs(2 * ph - 1)
            bump = tri ** 1.7
            # a small serration on the lobe's leading shoulder
            bump += .12 * math.exp(-((ph - .25) / .07) ** 2)
        else:
            wv = wmax * .4 * (1 - ((u - tail) / (1 - tail)) ** 2.2) ** .8 + .8 * lw
            bump = .2
        widths.append(wv)
        bumps.append(bump)
        wo = wv * (.5 + .5 * bump) if u < tail else wv * .5
        wi = wv * .5
        lb = wv * (.16 + .12 * math.sin(u * 9 + 1.)) if u < tail else wv * .5 + wo
        outer.append((x + s * nx * wo, y + s * ny * wo))
        inner.append((x - s * nx * wi, y - s * ny * wi))
        linb.append((x - s * nx * (wi - lb), y - s * ny * (wi - lb)))
        mid.append((x - s * nx * (wi - lb * .5), y - s * ny * (wi - lb * .5)))
    face = [outer + inner[::-1]]
    lining = [inner + linb[::-1]]
    hi = []
    jt = int(n * tail)
    seg = mid[int(n * .05):jt + 1]
    if len(seg) > 3:
        hi.append(_lens(seg, .55 * lw, .4))
    # the rolled tip: a white spiral line inside the black curl
    if k >= 1.:
        for f in (.25, -.3):
            cs = [(x - s * nx * widths[i] * f, y - s * ny * widths[i] * f)
                  for i, ((x, y), (nx, ny)) in enumerate(zip(spine, nr)) if jt - 3 <= i < n - 4]
            if len(cs) > 3 and _plen(cs) * k > 4:
                hi.append(_lens(cs, .55 * lw, .5))
    # burin cuts: from the lining out across the face, deeper in the bays and into the curl
    cuts = []
    for i in range(2, jt):
        u = i / (n - 1)
        if u < .12 and i % 2:
            continue
        (x, y), (nx, ny) = spine[i], nr[i]
        tx, ty_ = spine[min(n - 1, i + 1)][0] - spine[i - 1][0], spine[min(n - 1, i + 1)][1] - spine[i - 1][1]
        tl = math.hypot(tx, ty_) or 1
        tx, ty_ = tx / tl, ty_ / tl
        wv = widths[i]
        bx_, by_ = linb[i]
        depth = .22 + .38 * (1 - bumps[i]) + .25 * (u / tail) ** 2
        L = (wv * .5 + wv * .5 * (.5 + .5 * bumps[i])) * depth
        ex, ey = bx_ + (s * nx * .85 + tx * .5) * L, by_ + (s * ny * .85 + ty_ * .5) * L
        hw = .5 * lw if L * k > 2.5 else .4 * lw
        cuts.append([(bx_ - tx * hw, by_ - ty_ * hw), (bx_ + tx * hw, by_ + ty_ * hw), (ex, ey)])
    # a vein from the midrib into each lobe point
    for j in range(int(lobes)):
        i0 = int((j + .1) / lobes * tail * (n - 1))
        best = max(range(i0, min(jt, int((j + 1) / lobes * tail * (n - 1)) + 1)), key=lambda q: bumps[q], default=None)
        if best is None:
            continue
        a = max(0, best - int(.06 * n))
        p0 = spine[a]
        p2 = outer[best]
        p1 = ((p0[0] + p2[0]) / 2 + s * nr[best][0] * widths[best] * .08, (p0[1] + p2[1]) / 2 + s * nr[best][1] * widths[best] * .08)
        cuts.append(_lens(_bez(p0, p1, p1, (p0[0] + (p2[0] - p0[0]) * .85, p0[1] + (p2[1] - p0[1]) * .85), 8), .55 * lw, .6))
    return {"face": face, "cuts": cuts, "lining": lining, "hi": hi}


# the left side; (p0, p1, p2, p3, curl, width, lobes), drawn back to front and mirrored for the right.
# The first six are the main falls, top to bottom; the rest are smaller leaves laid over them.
_FRONDS = [
    ((52, 27), (44, 13), (28, 3), (13, 8), -1, 12., 4),
    ((51, 30), (36, 21), (13, 22), (5, 40), -1, 13., 5),
    ((50, 35), (33, 40), (12, 48), (5, 70), -1, 13., 5),
    ((41, 50), (23, 62), (7, 82), (6, 103), -1, 12.5, 5),
    ((33, 76), (14, 92), (4, 114), (11, 132), -1, 12., 5),
    ((31, 104), (19, 120), (16, 140), (32, 150), -1, 10., 4),
    ((50, 31), (40, 31), (30, 36), (24, 48), 1, 8., 3),
    ((34, 56), (24, 64), (18, 76), (20, 88), 1, 8., 3),
    ((32, 88), (23, 98), (20, 110), (23, 121), 1, 7.5, 3),
    ((50, 28), (46, 20), (40, 15), (33, 16), 1, 6., 2),
]


def _mantling(M, seed, OR):
    rng = random.Random(seed * 7919 + 17)
    k = M.k
    o = []
    mir = lambda poly: [(DW - x, y) for x, y in poly]
    sx, sy = 1.3 / k + .5, 1.5 / k + .6          # cast shadow offset: light from dexter chief
    spines = []
    for p0, p1, p2, p3, cs, wd, lb in _FRONDS:
        j = lambda p: (p[0] + rng.uniform(-1., 1.), p[1] + rng.uniform(-1., 1.))
        spines.append(_spine(p0, j(p1), j(p2), j(p3), cs))
    # the cut-away ground: punched matte between each pair of neighbouring falls
    gd = []
    for a, b in zip(spines[:5], spines[1:6]):
        gd.append(a[:44] + b[:44][::-1])
    gd.append(spines[5][:44] + [(40, 140), (34, 112)])
    gd.append([(53, 29), (50, 36), (41, 50), (33, 58), (54, 60), (54, 36)])
    gd += [mir(p) for p in gd]
    o.append(f'<path d="{"".join(_poly(M, p) for p in gd)}" fill="url(#{M.mat})"/>')
    for sp, (p0, p1, p2, p3, cs, wd, lb) in zip(spines, _FRONDS):
        f = _frond(sp, wd, lb + (2 if lb >= 4 else 1), cs, k)
        both = lambda key: f[key] + [mir(p) for p in f[key]]
        shadow = [[(x + sx, y + sy) for x, y in p] for p in both("face")]
        o.append(f'<path d="{"".join(_poly(M, p) for p in shadow)}" fill="url(#{M.mat})"/>')
        o.append(f'<path d="{"".join(_poly(M, p) for p in both("face"))}" fill="{OR}" stroke="#000" '
                 f'stroke-width="1" stroke-linejoin="round"/>')
        o.append(f'<path d="{"".join(_poly(M, p) for p in both("cuts"))}" fill="#000"/>')
        o.append(f'<path d="{"".join(_poly(M, p) for p in both("lining"))}" fill="#000" stroke="#000" '
                 f'stroke-width="1" stroke-linejoin="round"/>')
        o.append(f'<path d="{"".join(_poly(M, p) for p in both("hi"))}" fill="#fff"/>')
    return o


# ------------------------------------------------------------------------------------------------
# helm, torse and crest
# ------------------------------------------------------------------------------------------------

HX, HY = 62., 21.5          # helm origin: x centre, y just above the crown

_HELM = [(0, 3), (6, 3.6), (10.5, 5.6), (14.2, 9.6), (16, 15.4), (15.4, 21.4), (12.6, 25.6), (11.4, 28.4),
         (13.6, 31.2), (17.4, 34.6), (19, 38.2), (10, 38.8), (0, 38.9), (-10, 38.7), (-17, 38.1), (-15.2, 34.6),
         (-11.6, 31.4), (-10.4, 29.6), (-13, 28.2), (-16.4, 25.6), (-18, 21), (-17.8, 16), (-15.8, 11.4),
         (-11.4, 7.2), (-6, 4.2)]
_GRILLE = [(-16.6, 12.6), (-13, 11.4), (-10, 12), (-8.8, 15.6), (-8.6, 20), (-9.2, 24), (-10.8, 26.4),
           (-14.2, 26.8), (-16.6, 25), (-17.6, 21), (-17.4, 16)]


def _spline(pts, m=6, closed=True):
    """A Catmull-Rom curve through pts, m points per span."""
    P = list(pts)
    n = len(P)
    out = []
    rng_ = range(n) if closed else range(n - 1)
    for i in rng_:
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        if not closed:
            p0, p3 = P[max(0, i - 1)], P[min(n - 1, i + 2)]
        for j in range(m):
            t = j / m
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    return out


def _helm(M):
    k = M.k
    lw = 1 / k
    H = lambda pts: [(HX + x, HY + y) for x, y in pts]
    o = []
    out = H(_spline(_HELM, 5))
    o.append(f'<path d="{_poly(M, out)}" fill="#fff"/>')
    # steel: meridian cuts round the skull, swelling and closing up into the shadowed back; a few
    # fine ones on the lit cheek in front of the pivot
    sh = ""
    cx_, cy_ = -1.5, 17.
    for a, hw, t0, t1 in ((17., .75, -1.25, 1.2), (15.6, .7, -1.35, 1.25), (14., .62, -1.4, 1.3), (12.2, .55, -1.45, 1.3),
                          (10.2, .45, -1.45, 1.3), (8., .35, -1.45, 1.3), (5.6, .28, -1.4, 1.25),
                          (-4.4, .25, -1.2, 1.1), (-6.2, .3, -1.15, 1.05)):
        pts = []
        for i in range(25):
            t = t0 + (t1 - t0) * i / 24
            pts.append((HX + cx_ + a * math.cos(t), HY + cy_ + 13. * math.sin(t)))
        pts = [p for p in pts if p[1] < HY + 28.6]
        sh += _poly(M, _lens(pts, hw * lw, .6))
    # the gorget: lames lit from above, shaded beneath
    for y0, hw in ((31.4, .6), (32.2, .4), (34.5, .6), (35.3, .4)):
        pts = [(HX + x, HY + y0 + .004 * (x - 2) ** 2 * .3) for x in range(-12, 17, 2)]
        sh += _poly(M, _lens(pts, hw * lw, .5))
    o.append(f'<path d="{sh}" fill="#000"/>')
    lame = H([(-12, 30.6), (-4, 30.2), (6, 29.8), (13.4, 29.6)])
    lame2 = H([(-13.6, 33.6), (-4, 33.6), (8, 33.6), (16.4, 33.6)])
    o.append(f'<path d="{_poly(M, lame, False)}{_poly(M, lame2, False)}" '
             f'stroke="#000" stroke-width="1" fill="none"/>')
    # the grille: a dark mouth crossed by bars that follow the face
    gr = H(_spline(_GRILLE, 4))
    o.append(f'<path d="{_poly(M, gr)}" fill="#000"/>')
    bars = ""
    nb = 3 if k < 2 else 4
    for i in range(nb):
        f = (i + .8) / (nb + .6)
        pts = []
        for j in range(13):
            yy = 12.4 + j * (25.8 - 12.4) / 12
            q = ((yy - 19) / 7) ** 2
            xf, xb = -17.6 + 1.4 * q, -8.6 - .8 * q
            pts.append((HX + xf + (xb - xf) * f, HY + yy))
        bars += _poly(M, pts, False)
    o.append(f'<path d="{bars}" stroke="#fff" stroke-width="1" fill="none"/>')
    o.append(f'<path d="{_poly(M, gr)}" stroke="#000" stroke-width="1" fill="none" stroke-linejoin="round"/>')
    # the pivot boss: a rosette on the cheek
    bx, by = M.xy(HX - 1.5, HY + 17.)
    r = 2.5 * k
    boss = f'<circle cx="{_f(bx)}" cy="{_f(by)}" r="{_f(r)}" fill="#fff" stroke="#000" stroke-width="1"/>'
    if r >= 4:
        petals = ""
        for i in range(8):
            a = i * math.pi / 4
            petals += f"M{_f(bx + math.cos(a) * r * .35)},{_f(by + math.sin(a) * r * .35)}L{_f(bx + math.cos(a) * r * .8)},{_f(by + math.sin(a) * r * .8)}"
        boss += f'<path d="{petals}" stroke="#000" stroke-width=".5" fill="none"/>'
    boss += f'<circle cx="{_f(bx)}" cy="{_f(by)}" r="{_f(max(.75, r * .3))}" fill="#000"/>'
    o.append(boss)
    rv = ""
    if k >= 1.2:
        for x in range(-10, 16, 4):
            px_, py_ = M.xy(HX + x, HY + 32.)
            rv += f"M{_f(px_ - .75)},{_f(py_)}a.75 .75 0 1 0 1.5 0a.75 .75 0 1 0-1.5 0"
        o.append(f'<path d="{rv}" fill="#000"/>')
    o.append(f'<path d="{_poly(M, out)}" fill="none" stroke="#000" stroke-width="1" stroke-linejoin="round"/>')
    return o


def _torse(M, OR):
    """Six twists, Or and sable alternately, across the crown."""
    k = M.k
    x0, x1 = HX - 13.5, HX + 13.5
    yc = lambda x: HY + 3.6 + .0045 * (x - HX) ** 2
    th = 6.
    n = 6
    orp, sbp, hl, sh_ = "", "", "", ""
    for i in range(n):
        a, b = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
        sk = 2.4
        pts = []
        # a twist: a slanted pillow, rounded top and bottom
        for j in range(9):
            t = j / 8
            x = a + (b - a) * t
            pts.append((x + sk * .5, yc(x) - th / 2 - .5 * math.sin(math.pi * t)))
        for j in range(9):
            t = 1 - j / 8
            x = a + (b - a) * t
            pts.append((x - sk * .5, yc(x) + th / 2 + .5 * math.sin(math.pi * t)))
        if i % 2 == 0:
            orp += _poly(M, pts)
            m = (a + b) / 2
            sh_ += _poly(M, _lens([(m + sk * .5 + 1.2, yc(m) - th / 2 + .5), (m + .9, yc(m) + .4), (m - sk * .5 + .6, yc(m) + th / 2 - .2)],
                                  .55 / k, .6))
        else:
            sbp += _poly(M, pts)
            m = (a + b) / 2
            hl += _poly(M, _lens([(m + sk * .4 - .2, yc(m) - th / 2 + .6), (m, yc(m)), (m - sk * .4 + .2, yc(m) + th / 2 - .6)],
                                 .5 / k, .6))
    return [f'<path d="{orp}" fill="{OR}" stroke="#000" stroke-width="1" stroke-linejoin="round"/>',
            f'<path d="{sbp}" fill="#000" stroke="#000" stroke-width="1" stroke-linejoin="round"/>',
            f'<path d="{sh_}" fill="#000"/>', f'<path d="{hl}" fill="#fff"/>']


def _crest(M):
    """A tower sable issuing from the torse, cut in coursed white line."""
    k = M.k
    cx, top, foot = HX + .5, 7.4, HY + 2.2
    x0, x1 = cx - 5.6, cx + 5.6
    mh = 3.6
    body = [[(x0, top), (x1, top), (x1 + .4, foot), (x0 - .4, foot)],
            [(x0 - .8, top - .3), (x1 + .8, top - .3), (x1 + .8, top + 1.6), (x0 - .8, top + 1.6)]]
    u = (x1 - x0 + 1.6) / 5
    for j in range(3):
        a = x0 - .8 + 2 * j * u
        body.append([(a, top - mh), (a + u, top - mh), (a + u, top), (a, top)])
    o = [f'<path d="{"".join(_poly(M, b) for b in body)}" fill="#000"/>']
    d = ""
    y = top + 3.6
    row = 0
    while y < foot - 1.2:
        if top + 2.4 < y < top + 10.4:
            d += f"M{M.p(x0 + .6, y)}H{_f(M.xy(cx - 2., y)[0])}M{M.p(cx + 2., y)}H{_f(M.xy(x1 - .6, y)[0])}"
        else:
            d += f"M{M.p(x0 + .6, y)}H{_f(M.xy(x1 - .6, y)[0])}"
        if k >= 1.2:
            st = 3.6
            x = x0 + .6 + (row % 2) * st / 2 + st * .55
            while x < x1 - .8:
                if abs(x - cx) > 1.6:
                    d += f"M{M.p(x, y - 3.1)}V{_f(M.xy(x, y - .5)[1])}"
                x += st
        y += 3.4
        row += 1
    # break the courses where the loop sits
    o.append(f'<path d="{d}" stroke="#fff" stroke-width="1" fill="none"/>')
    sw = max(1.1 / k, .9)
    o.append(f'<path d="{_loop(M, cx, top + 3.4, 5.2, sw)}" fill="#fff"/>')
    return o


# ------------------------------------------------------------------------------------------------
# the arms
# ------------------------------------------------------------------------------------------------

def arms(w, h, seed=0):
    """Somaster arms engraved for a w x h px box: SVG child markup, no outer <svg>, no transforms."""
    full = min(w / DW, h / DH) * DW >= 100
    M = _Map(w, h) if full else _Map(w, h, SHIELD_BOX)
    k = M.k
    key = f"{int(round(w))}x{int(round(h))}-{int(seed)}"
    pid = f"smst-or-{key}"
    M.mat = f"smst-mat-{key}"
    pitch = 2. if k >= .9 else 3.     # Or: 1 px dots every 2 px (3 px when small, so it stays light)
    o = [f'<defs><pattern id="{pid}" width="{_f(pitch)}" height="{_f(pitch)}" patternUnits="userSpaceOnUse">'
         f'<rect width="{_f(pitch)}" height="{_f(pitch)}" fill="#fff"/>'
         f'<circle cx="{_f(pitch / 2)}" cy="{_f(pitch / 2)}" r=".5" fill="#000"/></pattern>'
         f'<pattern id="{M.mat}" width="3" height="3" patternUnits="userSpaceOnUse">'
         f'<rect width="3" height="3" fill="#000"/><rect x="1" y="1" width="1" height="1" fill="#fff"/></pattern></defs>']
    OR = f"url(#{pid})"
    if full:
        o += _mantling(M, seed, OR)
    # the shield: outer line swelling to a shadow on the sinister side and base, white fillet, fine line
    sh = _shield_pts()
    o.append(f'<path d="{_poly(M, sh)}" fill="#000"/>')
    sd = 3.2 / k
    o.append(f'<path d="{_poly(M, _shield_pts(1.2 / k + .25 / k, -sd * .45, -sd * .45))}" fill="#fff"/>')
    inner = _shield_pts(2.7 / k + .3 / k + sd * .4)
    o.append(f'<path d="{_poly(M, inner)}" fill="{OR}" stroke="#000" stroke-width=".5"/>')
    # charges
    o += _castle(M, OR)
    blk, wl, wln = "", "", ""
    for cx, cy, s in ((44.5, 74.5, 17.), (62, 73.5, 17.), (79.5, 74.5, 17.), (36.6, 106, 12.5), (87.4, 106, 12.5)):
        b, l1, l2 = _fleur(M, cx, cy, s)
        blk += b
        wl += l1
        wln += l2
    o.append(f'<path d="{blk}" fill="#000"/>')
    if wl:
        o.append(f'<path d="{wl}" fill="#fff"/>')
    if wln:
        o.append(f'<path d="{wln}" stroke="#fff" stroke-width="1" fill="none"/>')
    if full:
        o += _helm(M)
        o += _torse(M, OR)
        o += _crest(M)
    return "".join(o)


def arms_svg(w, h, seed=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(w)}" height="{_f(h)}" viewBox="0 0 {_f(w)} {_f(h)}">'
            + arms(w, h, seed) + "</svg>")


if __name__ == "__main__":
    import sys
    w, h = (float(a) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (160, 200)
    sys.stdout.write(arms_svg(w, h))
