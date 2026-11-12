"""The master page frame, after Ken C. Hunt: a band of bas-relief acanthus on a cut-away ruled ground down both
sides and across the top and foot, with Parker's own figures carved where the bands meet (his dog, crossed
drumsticks, a Sauvie heron, Mt Hood) and the section's motif carved in a cartouche at the middle of the foot.

Every leaf is modelled: a white blade cut with a 1 px edge, its shadow half ruled with bulino lines that follow
the leaf (contour lines 1.5 px apart), a dark trough along the midrib, hair veins on the lit half running out to
each lobe point. Stems are round-carved ribbons, lit on one edge, ruled on the other; every curl ends in a
drilled eye. Pure standard library; deterministic; e-ink rules (eink-guide 1-2) built in."""
import math
import re
import random

TAU = 2 * math.pi
W, H = 618, 714


def _n(x):
    s = f"{x:.1f}"
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return "0" if s in ("-0", "") else s


def _d(pts, close=False):
    if len(pts) < 2:
        return ""
    o = [f"M{_n(pts[0][0])},{_n(pts[0][1])}"]
    lx, ly = pts[0]
    for x, y in pts[1:]:
        if abs(x - lx) < .05 and abs(y - ly) < .05:
            continue
        o.append(f"L{_n(x)},{_n(y)}")
        lx, ly = x, y
    return "".join(o) + ("Z" if close else "")


def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def resample(pts, step=.8):
    """Even arc-length spacing, so widths and hatch read by distance, not by parameter."""
    S = [0.]
    for i in range(1, len(pts)):
        S.append(S[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    L = S[-1]
    n = max(4, int(L / step))
    out, j = [], 0
    for k in range(n + 1):
        s = L * k / n
        while j < len(S) - 2 and S[j + 1] < s:
            j += 1
        f = 0 if S[j + 1] == S[j] else (s - S[j]) / (S[j + 1] - S[j])
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f))
    return out, L


def normals(pts):
    out = []
    for i in range(len(pts)):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        out.append((-dy / m, dx / m))
    return out


def spiral(cx, cy, r0, a0, turns, flip=False, end=.16, n=None):
    th = TAU * turns
    b = -math.log(end) / th
    sg = -1 if flip else 1
    n = n or max(30, int(r0 * th * .9))
    return [(cx + r0 * math.exp(-b * th * i / n) * math.cos(a0 + sg * th * i / n),
             cy + r0 * math.exp(-b * th * i / n) * math.sin(a0 + sg * th * i / n)) for i in range(n + 1)]


class Ink:
    """Painter's-order list of elements; strokes packed per object."""

    def __init__(self):
        self.out = []

    def blade(self, d, sw=1):
        self.out.append(f'<path d="{d}" fill="#fff" stroke="#000" stroke-width="{sw}"/>')

    def lines(self, d, sw=.5):
        if d:
            self.out.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="{sw}"/>')

    def fill(self, d, c="#000"):
        if d:
            self.out.append(f'<path d="{d}" fill="{c}"/>')

    def svg(self):
        return "".join(self.out)


def _lobe(u, lobes, phase=0.):
    """Acanthus lobe: the edge swells slowly and snaps back at a point that leans toward the tip."""
    f = (u * lobes + phase) % 1.
    return .5 + .5 * f ** 1.8


def leaf(ink, spine, wmax, lobes=4, shade=1, hook=0., phase=0., dark=1., veins=True, taper=.75):
    """One modelled acanthus leaf along `spine` (base to tip). shade = +1/-1 picks the normal side
    that lies in shadow (ruled); the other side is lit (white, hair veins to each lobe point)."""
    pts, L = resample(spine, .7)
    N = normals(pts)
    n = len(pts)
    # width profile: grows from a narrow sheath, fullest about a third along, drawn to a point
    def wid(u):
        return wmax * (math.sin(math.pi * min(1, u ** taper)) ** .8) * (.35 + .65 * min(1, u * 4))
    lit = -shade
    E = {1: [], -1: []}
    for i in range(n):
        u = i / (n - 1)
        for s in (1, -1):
            m = _lobe(u, lobes, phase + (0 if s == lit else .5)) if u > .08 else 1
            if s != lit:
                m = .78 + .22 * m      # the shadow side rolls under: shallower lobes
            w = wid(u) * m
            E[s].append((pts[i][0] + N[i][0] * s * w, pts[i][1] + N[i][1] * s * w))
    outline = E[1] + E[-1][::-1]
    ink.blade(_d(outline, True), 1)
    # bulino on the shadow half: contour lines following the leaf, 1.5 px apart, out to near the edge
    hd = []
    for k in range(1, 12):
        off = 1.5 * k - .25
        run = []
        for i in range(n):
            u = i / (n - 1)
            m = (.78 + .22 * _lobe(u, lobes, phase + (0 if shade == lit else .5))) if u > .08 else 1
            edge = wid(u) * m
            # tone: dark through the base and trough, lifting toward the turned tip
            reach = edge - 1.1 - (.0 if dark > 1 else .25 * edge * max(0, u - .55) / .45)
            if off <= reach and u < .97:
                run.append((pts[i][0] + N[i][0] * shade * off, pts[i][1] + N[i][1] * shade * off))
            else:
                if len(run) > 2:
                    hd.append(_d(run))
                run = []
        if len(run) > 2:
            hd.append(_d(run))
    ink.lines("".join(hd), .5)
    # the trough: a 1 px cut along the midrib on the shadow side
    i0, i1 = int(.06 * n), int(.82 * n)
    ink.lines(_d([(pts[i][0] + N[i][0] * shade * .5, pts[i][1] + N[i][1] * shade * .5) for i in range(i0, i1)]), 1)
    if veins:   # lit half: a hair vein from the midrib out toward each lobe point, and the turned-edge line
        vd = []
        for j in range(lobes):
            u = (j + 1 - phase) / lobes - .04
            if not .15 < u < .9:
                continue
            i = int(u * (n - 1))
            ib = max(0, i - int(.12 * n))
            w = wid(u) * .78
            a = (pts[ib][0] + N[ib][0] * lit * .8, pts[ib][1] + N[ib][1] * lit * .8)
            b = (pts[i][0] + N[i][0] * lit * w, pts[i][1] + N[i][1] * lit * w)
            vd.append(_d([a, ((a[0] + b[0]) / 2 + N[i][0] * lit * .6, (a[1] + b[1]) / 2 + N[i][1] * lit * .6), b]))
        ink.lines("".join(vd), .5)


def ribbon(ink, pts0, w0, w1, shade=1, eye=True):
    """A round-carved stem along pts0, tapering w0 -> w1, lit on one edge and ruled on the other,
    ending (optionally) in a drilled eye."""
    pts, L = resample(pts0, .7)
    N = normals(pts)
    n = len(pts)
    ws = [w0 + (w1 - w0) * (i / (n - 1)) for i in range(n)]
    A = [(pts[i][0] + N[i][0] * ws[i] / 2, pts[i][1] + N[i][1] * ws[i] / 2) for i in range(n)]
    B = [(pts[i][0] - N[i][0] * ws[i] / 2, pts[i][1] - N[i][1] * ws[i] / 2) for i in range(n)]
    ink.blade(_d(A + B[::-1], True), 1)
    # shading: a contour line inside the shadow edge where the stem is wide enough
    sd = []
    run = []
    for i in range(n):
        if ws[i] >= 2.6:
            run.append((pts[i][0] + N[i][0] * shade * (ws[i] / 2 - 1), pts[i][1] + N[i][1] * shade * (ws[i] / 2 - 1)))
        elif len(run) > 2:
            sd.append(_d(run)); run = []
    if len(run) > 2:
        sd.append(_d(run))
    ink.lines("".join(sd), 1)
    if eye:
        ex, ey = pts[-1]
        r = max(1.3, w1 * .7)
        ink.out.append(f'<circle cx="{_n(ex)}" cy="{_n(ey)}" r="{_n(r + .9)}" fill="#fff" stroke="#000" stroke-width="1"/>'
                       f'<circle cx="{_n(ex)}" cy="{_n(ey)}" r="{_n(r * .55)}" fill="#000"/>')


# ------------------------------------------------------------------------------------------------
# one unit of the running scroll
# ------------------------------------------------------------------------------------------------

def unit(B, P, seed, s=1.):
    """One unit of an upward-flowing rinceau in a box 0..B x 0..P: the stem enters at the foot centre
    and leaves at the head centre, bulging to the left; a volute curls into the right-hand bay,
    sheathed by a big wrapping leaf; a second leaf flows up the stem's outer side, a third tucks
    under the curl. s scales the drawing (strokes stay on the e-ink grid)."""
    rng = random.Random(seed)
    ink = Ink()
    cx = B / 2
    bul = B * .26
    stem = bez((cx, P + .5), (cx - bul * 1.6, P * .72), (cx - bul * 1.6, P * .3), (cx, -.5), 30)
    node = stem[int(len(stem) * .42)]
    # volute in the right-hand bay
    vr = B * .27
    vc = (cx + B * .17, P * .44 + rng.uniform(-1, 1) * s)
    a0 = math.atan2(node[1] - vc[1], node[0] - vc[0])
    sp = spiral(vc[0], vc[1], vr, a0 + .35, 1.25 + rng.uniform(0, .15), flip=False, end=.17)
    branch = bez(node, (node[0] + 2 * s, node[1] + 3 * s), (sp[0][0] - 2 * s, sp[0][1] + 3 * s), sp[0], 10)[:-1] + sp
    # leaf 3 (deepest): tucked under the curl, hanging toward the foot on the right
    l3 = bez((vc[0] - vr * .2, vc[1] + vr * .8), (vc[0] + vr * .6, vc[1] + vr * 1.6), (B - 2 * s, P * .86), (B - 4 * s, P + 3 * s), 20)
    leaf(ink, l3, 7.5 * s, 3, shade=-1, phase=rng.random() * .3)
    # leaf 5: from low on the stem, down and out across the foot of the unit toward the band edge
    q0 = stem[int(len(stem) * .3)]
    l5 = bez(q0, (q0[0] - 3 * s, q0[1] + 6 * s), (1 * s, P * .9), (cx + 2 * s, P + 4 * s), 20)
    leaf(ink, l5, 6.5 * s, 3, shade=-1, phase=rng.random() * .3)
    # the stem
    ribbon(ink, stem, 3.4 * s, 3.0 * s, shade=-1, eye=False)
    # leaf 2: flowing up the stem's outer side to the band edge, its tip flicking in
    p0 = stem[int(len(stem) * .5)]
    l2 = bez(p0, (p0[0] - 6 * s, p0[1] - 6 * s), (1.5 * s, P * .14), (cx - 4 * s, -2 * s), 24)
    leaf(ink, l2, 9 * s, 5, shade=1, phase=rng.random() * .3)
    # the volute's stem
    ribbon(ink, branch, 3.0 * s, 1.4 * s, shade=1)
    # leaf 1: the big blade wrapping the outside of the curl, from the node round under it
    wr = vr * 1.32
    arc = [(vc[0] + wr * math.cos(a0 + .1 - t * 2.1), vc[1] + wr * math.sin(a0 + .1 - t * 2.1)) for t in [i / 24 for i in range(25)]]
    arc = [node] + arc[2:]
    leaf(ink, arc, 10.5 * s, 5, shade=-1, phase=rng.random() * .3, dark=1.2)
    # a small leaf in the curl's eye side: fills the gap between coil and band edge, head of the unit
    l4 = bez((vc[0] + vr * .3, vc[1] - vr * .95), (vc[0] + vr * .9, vc[1] - vr * 1.4), (B - 1, P * .12), (B - 6 * s, -1 * s), 16)
    leaf(ink, l4, 6.5 * s, 3, shade=1, phase=rng.random() * .3)
    return ink.svg()


GROUND = ('<pattern id="hg" width="1.5" height="1.5" patternUnits="userSpaceOnUse">'
          '<path d="M0,.75H1.5" stroke="#000" stroke-width="1" shape-rendering="crispEdges"/></pattern>')


def column(x0, y0, Bw, Hh, P, ids, flip_x=False):
    """Stack units up a column using <use>, alternating mirror so the stem weaves."""
    out = []
    n = int(math.ceil(Hh / P))
    P = Hh / n
    for i in range(n):
        y = y0 + Hh - P * (i + 1)
        mir = (i % 2 == 1) != flip_x
        tid = ids[i % len(ids)]
        if mir:
            out.append(f'<use href="#{tid}" xlink:href="#{tid}" transform="translate({_n(x0 + Bw)},{_n(y)}) scale(-1,{_n(P / UP)})"/>')
        else:
            out.append(f'<use href="#{tid}" xlink:href="#{tid}" transform="translate({_n(x0)},{_n(y)}) scale(1,{_n(P / UP)})"/>')
    return "".join(out)


UP = 60  # unit length as drawn


# ------------------------------------------------------------------------------------------------
# carved figures: white forms cut with a black edge (double stroke / outlined blades) on the ground
# ------------------------------------------------------------------------------------------------

def carve(d, w=3.2, inner=1.4):
    """A line carved in relief: a black cut either side of a white raised fillet."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w)}"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_n(inner)}"/>')


def form(d, shade_d=""):
    """A raised white form with a 1 px cut edge and its own shadow ruling."""
    return (f'<path d="{d}" fill="#fff" stroke="#000" stroke-width="1"/>'
            + (f'<path d="{shade_d}" fill="none" stroke="#000" stroke-width=".5"/>' if shade_d else ""))


def _hatch_in(poly, x0, x1, y0, y1, pitch=1.5, ang=45):
    """45-degree hatch lines inside a convex-ish polygon (scanline clip), as path d."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    # rotate polygon so hatch is horizontal, scan, rotate back
    rp = [(x * ca + y * sa, -x * sa + y * ca) for x, y in poly]
    ys = [p[1] for p in rp]
    out = []
    y = min(ys) + pitch / 2
    while y < max(ys):
        xs = []
        for i in range(len(rp)):
            (ax, ay), (bx, by) = rp[i], rp[(i + 1) % len(rp)]
            if (ay <= y < by) or (by <= y < ay):
                xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            if xs[j + 1] - xs[j] > .8:
                p, q = (xs[j] + .4, y), (xs[j + 1] - .4, y)
                out.append(_d([(p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca), (q[0] * ca - q[1] * sa, q[0] * sa + q[1] * ca)]))
        y += pitch
    return "".join(out)


def _poly(d):
    """Points of an M/L/Z path (for hatching)."""
    import re
    nums = [float(v) for v in re.findall(r"-?\d*\.?\d+", d)]
    return list(zip(nums[0::2], nums[1::2]))


def _sm(pts, n=6):
    """Chaikin-smoothed closed outline from a polygon (soft carved forms from a few hand points)."""
    for _ in range(n // 2):
        q = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            q += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        pts = q
    return pts


def fig_dog():
    """Parker's dog, head in profile facing right, ears down, collar: in a 30 x 30 box."""
    head = _sm([(7, 29), (6.5, 22), (8, 15), (11, 10), (15, 7), (19.5, 6.5), (23, 8), (25, 10.5), (28.5, 12), (29, 14.5),
                (27, 16.5), (23.5, 17), (21, 18.5), (19, 21), (18, 25), (18, 29)], 6)
    ear = _sm([(13, 8.5), (10, 9.5), (8.5, 13), (8.5, 18), (10, 21), (12.5, 20.5), (14, 16.5), (14.5, 11.5)], 6)
    hd = _d(head, True)
    sh = _hatch_in(head[len(head) // 2:] + [(12, 28), (12, 20)], 0, 30, 0, 30, 1.5, 45)
    o = form(hd, sh)
    o += form(_d(ear, True), _hatch_in(ear, 0, 30, 0, 30, 1.5, -45))
    o += '<circle cx="20.3" cy="10.6" r="1.2" fill="#000"/><circle cx="20.6" cy="10.3" r=".35" fill="#fff"/>'
    o += '<ellipse cx="28" cy="13.2" rx="1.5" ry="1.1" fill="#000"/>'
    o += '<path d="M24,15.8C25.5,16.4 27,16.2 28,15.3" fill="none" stroke="#000" stroke-width=".5"/>'
    o += carve("M7.5,24.5C11,26 15,26.3 18.4,25.4", 3, 1.2) + '<circle cx="13" cy="27.2" r="1.1" fill="#fff" stroke="#000" stroke-width=".5"/>'
    return o


def fig_hood():
    """Mt Hood: the snow cone lit from the left, the right flank ruled, three firs at its foot."""
    m = [(1, 27), (8, 17), (12, 11), (14.5, 6), (15.5, 5), (17, 7.5), (19.5, 12), (23, 17), (29, 27)]
    o = form(_d(m, True), _hatch_in([(15.5, 5), (17, 7.5), (19.5, 12), (23, 17), (29, 27), (17, 27), (16, 14)], 0, 30, 0, 30, 1.5, 45))
    snow = [(9.5, 15), (12, 11), (14.5, 6), (15.5, 5), (17, 7.5), (19.5, 12), (21, 14.5), (19, 13.5), (17.5, 15.5), (16, 12.5), (14, 15.5), (12.5, 13.5)]
    o += f'<path d="{_d(snow, True)}" fill="#fff" stroke="#000" stroke-width=".5"/>'
    for fx, fh in ((5, 7), (9, 9), (25, 8)):
        tri = [(fx, 29 - fh), (fx + 2.6, 29), (fx - 2.6, 29)]
        o += f'<path d="{_d(tri, True)}" fill="#000" stroke="#000" stroke-width=".5"/>'
    o += '<path d="M1,28.5H29" stroke="#000" stroke-width="1"/>'
    return o


def fig_heron():
    """A great blue heron from Sauvie Island, standing in the shallows, facing left."""
    body = _sm([(12, 15), (16, 12.5), (21, 13), (25, 16), (27.5, 20), (24, 20.5), (19, 20), (14.5, 18.5)], 6)
    o = form(_d(body, True), _hatch_in(body[len(body) // 3:], 0, 30, 0, 30, 1.5, 45))
    o += carve("M13.5,15.5C11,13 12.5,10 12,7.5C11.6,5.6 9.8,5 8.4,5.8", 3.2, 1.4)
    o += carve("M8.6,5.8L2.2,7.6", 2.4, .8)
    o += '<circle cx="9.6" cy="5.9" r=".6" fill="#000"/><path d="M10.5,5C12,3.8 14,3.6 15.5,4.2" stroke="#000" stroke-width=".5" fill="none"/>'
    o += carve("M18.5,20V28M20.5,20L22,28", 2.2, .6)
    o += '<path d="M10,28.25H28M13,27C15,26.3 17,26.3 19,27" stroke="#000" stroke-width=".5" fill="none"/>'
    return o


def fig_drums():
    """Crossed drumsticks over a ride cymbal."""
    o = f'<ellipse cx="15" cy="17" rx="13" ry="4.6" fill="#fff" stroke="#000" stroke-width="1"/>'
    o += '<path d="M3.5,18.5C9,21.5 21,21.5 26.5,18.5M6,15.4C11,13.7 19,13.7 24,15.4" stroke="#000" stroke-width=".5" fill="none"/>'
    o += '<ellipse cx="15" cy="16.6" rx="2.6" ry="1" fill="#000"/>'
    o += carve("M5,27L24.5,4.5", 3.4, 1.6) + carve("M25,27L5.5,4.5", 3.4, 1.6)
    o += ('<ellipse cx="24.8" cy="4.2" rx="1.6" ry="1.2" fill="#fff" stroke="#000" stroke-width="1"/>'
          '<ellipse cx="5.2" cy="4.2" rx="1.6" ry="1.2" fill="#fff" stroke="#000" stroke-width="1"/>')
    return o


def roundel(cx, cy, r, fig, ink_id="hg"):
    """A turned boss: an outer bead, a cove ruled into shadow on its lower right, a ruled ground,
    and the figure carved standing up from it."""
    o = f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="#fff" stroke="#000" stroke-width="1"/>'
    # cove shading: concentric arcs on the shadow half (pitch 1.5)
    d = []
    for k in range(1, 3):
        rr = r - 1.5 * k
        a0, a1 = -.3, math.pi + .3
        pts = [(cx + rr * math.cos(a0 + (a1 - a0) * i / 24), cy + rr * math.sin(a0 + (a1 - a0) * i / 24)) for i in range(25)]
        d.append(_d(pts))
    o += f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width=".5"/>'
    ri = r - 4.5
    o += f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(ri)}" fill="url(#{ink_id})" stroke="#000" stroke-width="1"/>'
    s = (ri * 2 - 3) / 30
    o += f'<g transform="translate({_n(cx - 15 * s)},{_n(cy - 15 * s)}) scale({s:.4f})">{fig}</g>'
    return o


# ------------------------------------------------------------------------------------------------
# section motifs, carved in the cartouche at the middle of the foot (20 x 20 box)
# ------------------------------------------------------------------------------------------------

def _sun(cx=10, cy=10, r=4.2, rays=12, R=8.6):
    d = "".join(f"M{_n(cx + (r + 1.6) * math.cos(a))},{_n(cy + (r + 1.6) * math.sin(a))}L{_n(cx + R * math.cos(a))},{_n(cy + R * math.sin(a))}"
                for a in [TAU * k / rays for k in range(rays)])
    return carve(d, 2.4, .6) + f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="#fff" stroke="#000" stroke-width="1"/>' \
        + f'<path d="M{_n(cx - r * .3)},{_n(cy + r * .9)}A{_n(r * .95)},{_n(r * .95)} 0 0 0 {_n(cx + r * .9)},{_n(cy - r * .3)}" fill="none" stroke="#000" stroke-width=".5"/>'


def _m(d):
    return carve(d, 3, 1.2)


MOTIFS = {
    "today": lambda: _sun(),
    "edition": lambda: _m("M6,17V3.5H11C14,3.5 15.5,5.2 15.5,7.6C15.5,10 14,11.7 11,11.7H6"),          # P monogram
    "end": lambda: _m("M6,17V3.5H11C14,3.5 15.5,5.2 15.5,7.6C15.5,10 14,11.7 11,11.7H6") + _m("M3,18.5H17"),
    "solar": lambda: _sun(13.5, 6, 2.8, 8, 5.2) + _m("M2,18L6,10H18L14.5,18ZM4,14H16.5M9.5,10L8,18M14,10L12.5,18"),
    "music": lambda: f'<ellipse cx="10" cy="8" rx="7.5" ry="2.6" fill="#fff" stroke="#000" stroke-width="1"/>'
                     + _m("M2.5,8V15.5C2.5,17 6,18.2 10,18.2C14,18.2 17.5,17 17.5,15.5V8M5,10L8,17M11,10.5L8,17M15,10L12,17")
                     + carve("M4,1.5L10,7M16,1.5L10,7", 2.4, .8),
    "world": lambda: _m("M10,18.5C4,16 4,10 8,7C7,10 9,11 10,10C9,7 11,4 14,2C12,6 16,8 15.5,12C15.2,15.5 13,17.5 10,18.5Z"),
    "river": lambda: _m("M2,13H18L15.5,16.5H5ZM6,13V8H13V13M9,8V4.5M11,8V3.5") + carve("M1,18.5C3,17.5 5,19.5 7,18.5S11,17.5 13,18.5 17,19.5 19,18.5", 2.4, .7),
    "coast": lambda: _m("M1,17C4,17 5,9 11,8C15,7.5 17.5,10 16,13C14.8,15.5 11.5,14.5 12,12.5M1,17H19"),
    "garden": lambda: _m("M10,18.5V9M10,13C7,13 4.5,11 4.5,8C7.5,8 10,10 10,13ZM10,9C7.5,9 6.5,6 7,3C8.5,4.5 10,5 10,5C10,5 11.5,4.5 13,3C13.5,6 12.5,9 10,9Z"),
    "roads": lambda: _m("M3,18.5L8.5,2.5M17,18.5L11.5,2.5") + carve("M10,17V14.5M10,11.5V9.5M10,7V5.5", 2.4, .8),
    "family": lambda: _m("M2.5,9.5L10,3L17.5,9.5M4.5,8V18H15.5V8M8.5,18V13H11.5V18"),
    "nearby": lambda: _m("M10,1.5L12,8L18.5,10L12,12L10,18.5L8,12L1.5,10L8,8Z") + '<circle cx="10" cy="10" r="1.2" fill="#000"/>',
    "news": lambda: _m("M4,18.5C6,13 9,7 16.5,1.5C16,6 13,11 7.5,14.5M4,18.5L9.5,10"),
    "markets": lambda: _m("M2,17L7,11L10.5,13.5L17,5M13,5H17V9M2,18.5H18"),
    "civics": lambda: _m("M3,8.5H17M5,8.5V16M8.3,8.5V16M11.7,8.5V16M15,8.5V16M2.5,16.5H17.5M2,18.5H18M4,8.5C5,5 8,3 10,3S15,5 16,8.5M10,3V1"),
    "sports": lambda: f'<circle cx="10" cy="10" r="8" fill="#fff" stroke="#000" stroke-width="1.5"/>'
                      + _m("M2,10H18M10,2V18M4.5,4.5C7.5,7 7.5,13 4.5,15.5M15.5,4.5C12.5,7 12.5,13 15.5,15.5"),
    "watch": lambda: _m("M1.5,10C5,4.5 15,4.5 18.5,10C15,15.5 5,15.5 1.5,10Z") + '<circle cx="10" cy="10" r="3" fill="#000"/><circle cx="11" cy="9" r=".8" fill="#fff"/>',
    "local": lambda: _m("M1,15H19M2.5,15C5,8 15,8 17.5,15M5.5,5V15M14.5,5V15M5.5,5L4.5,3M14.5,5L15.5,3M7,15V11M10,15V9.5M13,15V11"),
    "almanac": lambda: _m("M12.5,2.5C8,3 5,6.5 5,10.5S8,18 12.5,18.5C9.5,16.5 8.5,13.5 8.5,10.5S9.5,4.5 12.5,2.5Z") + carve("M15.5,5.5L16.3,7.3L18,8L16.3,8.7L15.5,10.5L14.7,8.7L13,8L14.7,7.3Z", 1.6, .4),
    "science": lambda: f'<circle cx="10" cy="10" r="1.6" fill="#000"/>' + _m("M10,1.5C14,1.5 14,18.5 10,18.5S6,1.5 10,1.5ZM2.6,5.8C4.6,2.3 19.4,10.8 17.4,14.3S0.6,9.3 2.6,5.8ZM17.4,5.8C19.4,9.3 4.6,17.7 2.6,14.3S15.4,2.3 17.4,5.8Z"),
    "doodles": lambda: _m("M3,17L4.5,12.5L14.5,2.5L17.5,5.5L7.5,15.5ZM12.5,4.5L15.5,7.5M3,17L7.5,15.5"),
    "delights": lambda: _m("M10,1.8L12.3,7.3L18.2,7.6L13.6,11.3L15.1,17.1L10,13.8L4.9,17.1L6.4,11.3L1.8,7.6L7.7,7.3Z"),
}


def cartouche(cx, cy, w, h, motif):
    """An oval tablet with scrolled ends, a turned rim and a ruled ground, the motif carved in it."""
    rx, ry = w / 2, h / 2
    pts = []
    for i in range(96):
        a = TAU * i / 96
        c, s = math.cos(a), math.sin(a)
        e = 3.2
        x = rx * (abs(c) ** (2 / e)) * (1 if c >= 0 else -1)
        y = ry * (abs(s) ** (2 / e)) * (1 if s >= 0 else -1)
        pts.append((cx + x, cy + y))
    o = f'<path d="{_d(pts, True)}" fill="#fff" stroke="#000" stroke-width="1"/>'
    inner = [(cx + (x - cx) * (rx - 3.5) / rx, cy + (y - cy) * (ry - 3) / ry) for x, y in pts]
    o += f'<path d="{_d([(cx + (x - cx) * (rx - 1.75) / rx, cy + (y - cy) * (ry - 1.5) / ry) for x, y in pts[2:46]])}" fill="none" stroke="#000" stroke-width=".5"/>'
    o += f'<path d="{_d(inner, True)}" fill="url(#hg)" stroke="#000" stroke-width="1"/>'
    s = (h - 7) / 20
    o += f'<g transform="translate({_n(cx - 10 * s)},{_n(cy - 10 * s)}) scale({s:.4f})">{motif}</g>'
    return o


# ------------------------------------------------------------------------------------------------
# the page
# ------------------------------------------------------------------------------------------------

SIDE = 46      # body padding at the sides (CSS px)
TOPB = 26      # running head / bar inset at top and foot
CORNER_R = 21


def defs(seed=0):
    side = "".join(f'<g id="hs{k}">{unit(36, UP, seed * 10 + k)}</g>' for k in range(3))
    top = "".join(f'<g id="ht{k}">{unit(18, 34, seed * 10 + 5 + k, s=.5)}</g>' for k in range(2))
    return "<defs>" + GROUND + side + top + "</defs>"


def _col(x0, y0, length, B, ids, P, flip=False):
    """Units up a vertical band from y0+length to y0; whole units only, centred (the bosses cover the ends)."""
    n = int(length // P) + 1
    ys = y0 + (length - n * P) / 2
    o = []
    for i in range(n):
        y = ys + length - P * (i + 1) + (n * P - length) / 2 * 0
        mir = (i % 2 == 1) != flip
        t = ids[i % len(ids)]
        tr = f"translate({_n(x0 + B)},{_n(y)}) scale(-1,1)" if mir else f"translate({_n(x0)},{_n(y)})"
        o.append(f'<use href="#{t}" xlink:href="#{t}" transform="{tr}"/>')
    return "".join(o)


def _row(x0, y0, length, B, ids, P, rightward=True):
    """Units along a horizontal band: the column unit turned 90 degrees."""
    n = int(math.ceil(length / P))
    xs = x0 + (length - n * P) / 2
    o = []
    for i in range(n):
        mir = i % 2 == 1
        t = ids[i % len(ids)]
        if rightward:   # flow +x: rotate the upward unit by 90 deg clockwise
            x = xs + P * i
            tr = f"translate({_n(x)},{_n(y0 + (0 if mir else B))}) rotate(-90)" + (" scale(-1,1) translate(" + _n(-B) + ",0)" if mir else "")
            tr = f"translate({_n(x)},{_n(y0)}) rotate(90) translate(0,{_n(-P)}) " + ("scale(-1,1) translate(" + _n(-B) + ",0)" if not mir else "")
        else:
            x = xs + P * i
            tr = f"translate({_n(x + P)},{_n(y0 + B)}) rotate(-90) " + ("scale(-1,1) translate(" + _n(-B) + ",0)" if mir else "")
        o.append(f'<use href="#{t}" xlink:href="#{t}" transform="{tr}"/>')
    return "".join(o)


def page_frame(motif_key=None, seed=0, w=W, h=H):
    S, T = SIDE, TOPB
    bx0, bx1 = 4, S - 6            # side band
    by0, by1 = 4, T - 4            # top band
    o = ['<rect x="1.5" y="1.5" width="%s" height="%s" fill="none" stroke="#000" stroke-width="1"/>' % (_n(w - 3), _n(h - 3))]
    # the cut-away ground in every band
    gd = (f"M{bx0},{by0}H{w - bx0}V{h - by0}H{bx0}Z"
          f"M{bx1},{by1}V{h - by1}H{w - bx1}V{by1}Z")
    o.append(f'<path d="{gd}" fill="url(#hg)" fill-rule="evenodd"/>')
    # bands
    B = bx1 - bx0
    o.append(f'<clipPath id="hcl"><path d="{gd}" clip-rule="evenodd"/></clipPath><g clip-path="url(#hcl)">')
    o.append(_col(bx0, 30, h - 60, B, ["hs0", "hs1", "hs2"], UP))
    o.append(_col(w - bx1, 30, h - 60, B, ["hs2", "hs0", "hs1"], UP, flip=True))
    TB = by1 - by0
    o.append(_row(30, by0, w - 60, TB, ["ht0", "ht1"], 34, True))
    o.append(_row(44, h - by1, (w - 88) / 2, TB, ["ht1", "ht0"], 34, True))
    o.append(_row(w / 2, h - by1, (w - 88) / 2, TB, ["ht0", "ht1"], 34, False))
    o.append("</g>")
    # mouldings: a hair and a 1 px fillet framing the reading panel and the outer edge
    o.append(f'<path d="M{bx1 + .75},{by1 + .75}H{w - bx1 - .75}V{h - by1 - .75}H{bx1 + .75}Z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{bx1 + 2.5},{by1 + 2.5}H{w - bx1 - 2.5}V{h - by1 - 2.5}H{bx1 + 2.5}Z" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{bx0 - .75},{by0 - .75}H{w - bx0 + .75}V{h - by0 + .75}H{bx0 - .75}Z" fill="none" stroke="#000" stroke-width=".5"/>')
    # Parker's four bosses at the corners
    R = CORNER_R
    for (cx, cy), f in (((S / 2, 32), fig_dog), ((w - S / 2, 32), fig_hood), ((S / 2, h - 32), fig_heron), ((w - S / 2, h - 32), fig_drums)):
        o.append(roundel(cx, cy, R, f()))
    if motif_key and motif_key in MOTIFS:
        o.append(cartouche(w / 2, h - T / 2 - 1, 84, 24, MOTIFS[motif_key]()))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" stroke-linecap="round" stroke-linejoin="round">' + defs(seed) + "".join(o) + "</svg>")


def motif_tablet(key, w=84, h=24):
    """The section's cartouche alone (layered over the common frame)."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2}" height="{h + 2}" viewBox="{-1} {-1} {w + 2} {h + 2}" '
            f'stroke-linecap="round" stroke-linejoin="round"><defs>{GROUND}</defs>' + cartouche(w / 2, h / 2, w, h, MOTIFS[key]()) + "</svg>")


# ------------------------------------------------------------------------------------------------
# the page ground: fine, light, low-relief foliage under everything that is not text
# ------------------------------------------------------------------------------------------------

def leaf_light(ink, spine, wmax, lobes=4, shade=1, phase=0.):
    """A low-relief leaf for the ground: 0.5 px cut edge, its shadow half ruled at pitch 3 (about 17 %)."""
    pts, L = resample(spine, .8)
    N = normals(pts)
    n = len(pts)
    lit = -shade

    def wid(u):
        return wmax * (math.sin(math.pi * min(1, u ** .75)) ** .8) * (.35 + .65 * min(1, u * 4))
    E = {1: [], -1: []}
    for i in range(n):
        u = i / (n - 1)
        for s in (1, -1):
            m = _lobe(u, lobes, phase + (0 if s == lit else .5)) if u > .08 else 1
            if s != lit:
                m = .78 + .22 * m
            E[s].append((pts[i][0] + N[i][0] * s * wid(u) * m, pts[i][1] + N[i][1] * s * wid(u) * m))
    ink.out.append(f'<path d="{_d(E[1] + E[-1][::-1], True)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    hd = []
    for k in range(1, 6):
        off = 3 * k - 1.5
        run = []
        for i in range(n):
            u = i / (n - 1)
            m = (.78 + .22 * _lobe(u, lobes, phase + .5)) if u > .08 else 1
            if off <= wid(u) * m - 1.2 and u < .92:
                run.append((pts[i][0] + N[i][0] * shade * off, pts[i][1] + N[i][1] * shade * off))
            else:
                if len(run) > 2:
                    hd.append(_d(run))
                run = []
        if len(run) > 2:
            hd.append(_d(run))
    hd.append(_d([(pts[i][0] + N[i][0] * shade * .25, pts[i][1] + N[i][1] * shade * .25) for i in range(int(.06 * n), int(.8 * n))]))
    ink.lines("".join(hd), .5)


def spray(seed, R=34):
    """A curling stem with four to six leaves, in a box about 2R across centred on 0,0."""
    rng = random.Random(seed)
    ink = Ink()
    a0 = rng.uniform(0, TAU)
    flip = rng.random() < .5
    sp = spiral(0, 0, R * .55, a0, 1.1, flip=flip, end=.2)
    stem = sp
    pts, L = resample(stem, 1.)
    N = normals(pts)
    nl = rng.randint(4, 6)
    leaves = []
    for j in range(nl):
        u = .05 + .62 * j / nl + rng.uniform(-.03, .03)
        i = int(u * (len(pts) - 1))
        side = 1 if j % 2 else -1
        if j == nl - 1:
            side = 1 if not flip else -1
        bx, by = pts[i]
        tx, ty = pts[min(len(pts) - 1, i + 2)][0] - bx, pts[min(len(pts) - 1, i + 2)][1] - by
        ang = math.atan2(ty, tx) + side * rng.uniform(.5, .9) * (1 if not flip else -1)
        ll = R * rng.uniform(.6, .95) * (1 - .35 * u)
        bend = side * rng.uniform(.4, .9)
        sp2 = [(bx + math.cos(ang + bend * t * t) * ll * t, by + math.sin(ang + bend * t * t) * ll * t) for t in [k / 14 for k in range(15)]]
        leaves.append((sp2, ll * rng.uniform(.3, .38), rng.choice((3, 4, 4, 5)), -side, rng.random() * .3))
    # the stem: a 1 px line with a hair beside it, curling to an eye
    sd = _d(pts)
    ink.lines(sd, 1)
    ink.lines(_d([(p[0] + N[i][0] * 1.25, p[1] + N[i][1] * 1.25) for i, p in enumerate(pts[:-6])]), .5)
    ex, ey = pts[-1]
    ink.out.append(f'<circle cx="{_n(ex)}" cy="{_n(ey)}" r="1.4" fill="#fff" stroke="#000" stroke-width=".5"/>')
    for l in leaves[::-1]:
        leaf_light(ink, *l)
    return ink.svg()


GROUND_L = ('<pattern id="hgl" width="3" height="3" patternUnits="userSpaceOnUse">'
            '<path d="M0,1.25H3" stroke="#000" stroke-width=".5" shape-rendering="crispEdges"/></pattern>')


def page_ground(w=W, h=H, seed=0, kinds=8, R=34):
    """Foliage sprays scattered on a jittered grid over a light ruled ground: seeded, so no two sheets'
    worth repeat; a handful of drawn sprays reused at many turns and mirrors keeps the file small."""
    rng = random.Random(seed)
    defs = "".join(f'<g id="gs{k}">{spray(seed * 100 + k, R)}</g>' for k in range(kinds))
    uses = []
    step = R * 1.25
    rows = int(h / step) + 2
    cols = int(w / step) + 2
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    rng.shuffle(cells)
    for c, r in cells:
        x = (c - .5 + rng.uniform(-.35, .35) + (.5 if r % 2 else 0)) * step
        y = (r - .5 + rng.uniform(-.35, .35)) * step
        k = rng.randrange(kinds)
        rot = rng.uniform(0, 360)
        sx = -1 if rng.random() < .5 else 1
        uses.append(f'<use href="#gs{k}" xlink:href="#gs{k}" transform="translate({_n(x)},{_n(y)}) rotate({rot:.0f}) scale({sx},1)"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" stroke-linecap="round" stroke-linejoin="round"><defs>{GROUND_L}{defs}</defs>'
            f'<rect width="{w}" height="{h}" fill="url(#hgl)"/>' + "".join(uses) + "</svg>")


def ground_cell(seed, w=60, h=52):
    """One cell of the all-over rinceau: an S-stem from the lower-left corner to the upper-right, a volute
    curling off it into the upper-left bay, leaves wrapping the curl and filling the lower-right bay.
    Cells meet stem to stem at their corners, so any arrangement of variants and mirrors reads as one vine."""
    rng = random.Random(seed)
    ink = Ink()
    stem = bez((0, h), (w * .55, h * .95), (w * .45, h * .05), (w, 0), 30)
    node = stem[int(len(stem) * rng.uniform(.4, .5))]
    vc = (w * rng.uniform(.24, .3), h * rng.uniform(.28, .34))
    vr = min(w, h) * rng.uniform(.17, .2)
    a0 = math.atan2(node[1] - vc[1], node[0] - vc[0])
    sp = spiral(vc[0], vc[1], vr, a0 - .2, 1.2, flip=True, end=.2)
    branch = bez(node, (node[0] - 3, node[1] - 2), (sp[0][0] + 3, sp[0][1] + 2), sp[0], 8)[:-1] + sp
    L = []
    # lower-right bay: a long leaf from low on the stem, curling up
    q = stem[int(len(stem) * .3)]
    L.append((bez(q, (q[0] + 8, q[1] + 2), (w * .9, h * .85), (w * .95, h * .5), 18), 9, 4, 1, rng.random() * .3))
    # wrap leaf round the volute
    wr = vr * 1.45
    arc = [(vc[0] + wr * math.cos(a0 + t * 2.0), vc[1] + wr * math.sin(a0 + t * 2.0)) for t in [i / 18 for i in range(19)]]
    L.append(([node] + arc[2:], 8, 4, -1, rng.random() * .3))
    # a small leaf from high on the stem into the upper-right
    q2 = stem[int(len(stem) * .75)]
    L.append((bez(q2, (q2[0] - 2, q2[1] + 6), (w * .85, h * .3), (w * .97, h * .28), 12), 5.5, 3, 1, rng.random() * .3))
    # and one from low into the lower-left
    q3 = stem[int(len(stem) * .14)]
    L.append((bez(q3, (q3[0] - 2, q3[1] - 6), (w * .05, h * .7), (w * .04, h * .58), 12), 5.5, 3, -1, rng.random() * .3))
    for sp_, wm, lob, sh, ph in L[:2]:
        leaf_light(ink, sp_, wm, lob, sh, ph)
    ink.lines(_d(stem), 1)
    ink.lines(_d(branch), 1)
    ex, ey = branch[-1]
    ink.out.append(f'<circle cx="{_n(ex)}" cy="{_n(ey)}" r="1.5" fill="#fff" stroke="#000" stroke-width=".5"/>')
    for sp_, wm, lob, sh, ph in L[2:]:
        leaf_light(ink, sp_, wm, lob, sh, ph)
    return ink.svg()


GROUND_S = ('<pattern id="hgs" width="1.5" height="1.5" patternUnits="userSpaceOnUse">'
            '<rect width=".5" height=".5" fill="#000"/></pattern>')


def page_ground2(w=W, h=H, seed=0, kinds=6, cw=60, ch=52):
    rng = random.Random(seed)
    defs = "".join(f'<g id="gc{k}">{ground_cell(seed * 100 + k, cw, ch)}</g>' for k in range(kinds))
    uses = []
    for r in range(int(h / ch) + 2):
        for c in range(int(w / cw) + 2):
            k = rng.randrange(kinds)
            x, y = (c - .5) * cw + (r % 2) * 0, (r - .5) * ch
            if (c + r) % 2:     # mirror alternate cells: the vines zigzag into an ogee lattice
                tr = f"translate({_n(x + cw)},{_n(y)}) scale(-1,1)"
            else:
                tr = f"translate({_n(x)},{_n(y)})"
            uses.append(f'<use href="#gc{k}" xlink:href="#gc{k}" transform="{tr}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" stroke-linecap="round" stroke-linejoin="round"><defs>{GROUND_S}{defs}</defs>'
            f'<rect width="{w}" height="{h}" fill="url(#hgs)"/>' + "".join(uses) + "</svg>")


def page_ground3(w=W, h=H, seed=0, kinds=8, R=30):
    """Sprays laid along a seeded flow of two or three great curls across the sheet (Poisson-spaced),
    so the ground reads as one composed sweep of foliage, never a grid."""
    rng = random.Random(seed)
    defs = "".join(f'<g id="gs{k}">{spray(seed * 100 + k, R)}</g>' for k in range(kinds))
    vort = [(rng.uniform(.15, .85) * w, rng.uniform(.1, .9) * h, rng.choice((-1, 1)) * rng.uniform(.8, 1.2)) for _ in range(3)]

    def flow(x, y):
        vx = vy = 0.
        for cx, cy, s in vort:
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy + 900
            vx += -dy * s / d2 * 4000
            vy += dx * s / d2 * 4000
        return math.degrees(math.atan2(vy + .3, vx + 1))
    pts = []
    tries = 0
    rmin = R * 1.05
    while tries < 6000:
        tries += 1
        x, y = rng.uniform(-R, w + R), rng.uniform(-R, h + R)
        if all((x - a) ** 2 + (y - b) ** 2 > rmin * rmin for a, b in pts):
            pts.append((x, y))
    uses = []
    for x, y in pts:
        k = rng.randrange(kinds)
        uses.append(f'<use href="#gs{k}" xlink:href="#gs{k}" transform="translate({_n(x)},{_n(y)}) rotate({flow(x, y):.0f})"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" stroke-linecap="round" stroke-linejoin="round"><defs>{GROUND_S}{defs}</defs>'
            f'<rect width="{w}" height="{h}" fill="url(#hgs)"/>' + "".join(uses) + "</svg>")


def leaf_sym(seed, L=24, Wd=7.5):
    """A slender low-relief acanthus leaf, base at 0,0, pointing +x, curving and hooking its tip."""
    rng = random.Random(seed)
    bend = rng.uniform(.35, .7) * rng.choice((-1, 1))
    pts = [(L * t * math.cos(bend * t * t), L * t * math.sin(bend * t * t)) for t in [k / 16 for k in range(17)]]
    ink = Ink()
    leaf_light(ink, pts, Wd * rng.uniform(.85, 1.1), rng.choice((4, 5)), 1 if bend > 0 else -1, rng.random() * .3)
    return ink.svg()


def curl_sym(seed, r=7):
    """A small volute: a 1 px stem curling to a drilled eye, a leaf wrapped round its outside."""
    rng = random.Random(seed)
    sp = spiral(r, 0, r, math.pi, 1.3, flip=bool(rng.random() < .5), end=.2)
    lead = [(0, 0)] + sp
    ink = Ink()
    arc = [(r + r * 1.45 * math.cos(math.pi - t * 1.9 * (1 if sp[3][1] < 0 else -1)), r * 1.45 * math.sin(math.pi - t * 1.9 * (1 if sp[3][1] < 0 else -1))) for t in [k / 14 for k in range(15)]]
    ink.lines(_d(lead), 1)
    leaf_light(ink, [(0, 0)] + arc[1:], 5.5, 4, 1 if sp[3][1] > 0 else -1, rng.random() * .3)
    ex, ey = sp[-1]
    ink.out.append(f'<circle cx="{_n(ex)}" cy="{_n(ey)}" r="1.4" fill="#fff" stroke="#000" stroke-width=".5"/>')
    return ink.svg()


def page_ground4(w=W, h=H, seed=0, sep=46, step=15):
    """Long vines following a seeded flow of great curls across the sheet (evenly spaced streamlines),
    leaved alternately along their length with occasional curling volutes: one composed sweep per sheet."""
    rng = random.Random(seed)
    vort = [(rng.uniform(.1, .9) * w, rng.uniform(.1, .9) * h, rng.choice((-1, 1)) * rng.uniform(.7, 1.3)) for _ in range(3)]

    base = rng.uniform(0, TAU)

    def vel(x, y):
        vx, vy = math.cos(base) * .6, math.sin(base) * .6
        for cx, cy, s in vort:
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy + 2500
            vx += -dy * s / d2 * 700
            vy += dx * s / d2 * 700
        m = math.hypot(vx, vy) or 1
        return vx / m, vy / m
    occ = {}
    cs = sep / 2

    def free(x, y, own):
        gx, gy = int(x // cs), int(y // cs)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for (px, py, o) in occ.get((gx + i, gy + j), ()):
                    if o != own and (px - x) ** 2 + (py - y) ** 2 < (sep * .9) ** 2:
                        return False
        return True
    lines = []
    seeds_ = [(rng.uniform(-20, w + 20), rng.uniform(-20, h + 20)) for _ in range(300)]
    for lid, (sx, sy) in enumerate(seeds_):
        if not free(sx, sy, -1):
            continue
        line = [(sx, sy)]
        for direction in (1, -1):
            x, y = sx, sy
            seg = []
            for _ in range(220):
                vx, vy = vel(x, y)
                x, y = x + direction * vx * 2, y + direction * vy * 2
                if not (-30 < x < w + 30 and -30 < y < h + 30) or not free(x, y, lid):
                    break
                seg.append((x, y))
            line = (seg[::-1] + line) if direction == -1 else (line + seg)
        if len(line) < 25:
            continue
        for (x, y) in line:
            occ.setdefault((int(x // cs), int(y // cs)), []).append((x, y, lid))
        lines.append(line)
    defs = "".join(f'<g id="gl{k}">{leaf_sym(seed * 50 + k)}</g>' for k in range(6))
    defs += "".join(f'<g id="gv{k}">{curl_sym(seed * 50 + 20 + k)}</g>' for k in range(3))
    stems, leaves = [], []
    for line in lines:
        pts, L = resample(line, 1.5)
        stems.append(_d(pts[::2] + [pts[-1]]))
        N = normals(pts)
        k = 0
        i = rng.randrange(3, 8)
        while i < len(pts) - 3:
            x, y = pts[i]
            tx, ty = -N[i][1], N[i][0]
            ta = math.degrees(math.atan2(ty, tx))
            side = 1 if k % 2 else -1
            if rng.random() < .16:
                g = f"gv{rng.randrange(3)}"
                leaves.append(f'<use href="#{g}" xlink:href="#{g}" transform="translate({_n(x)},{_n(y)}) rotate({ta + side * 70:.0f}) scale(1,{side})"/>')
            else:
                g = f"gl{rng.randrange(6)}"
                leaves.append(f'<use href="#{g}" xlink:href="#{g}" transform="translate({_n(x)},{_n(y)}) rotate({ta + side * rng.uniform(28, 48):.0f}) scale(1,{side})"/>')
            k += 1
            i += int(step / 1.5 * rng.uniform(.8, 1.2))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" stroke-linecap="round" stroke-linejoin="round"><defs>{GROUND_S}{defs}</defs>'
            f'<rect width="{w}" height="{h}" fill="url(#hgs)"/>'
            f'<path d="{"".join(stems)}" fill="none" stroke="#000" stroke-width="1"/>' + "".join(leaves) + "</svg>")


# ------------------------------------------------------------------------------------------------
# the paper: a calm banknote tint, and the carved bars that sit in the gaps between blocks
# ------------------------------------------------------------------------------------------------

def paper_tint(w=W, h=H, seed=0, pitch=3.):
    """Engraved banknote paper: concentric hair arcs 3 px apart round a centre far off the sheet, so the
    lines run near 45 degrees and turn by a few degrees across the page; one path, about 17 % tone."""
    rng = random.Random(seed)
    cx = -rng.uniform(700, 1100)
    cy = h + rng.uniform(600, 1100)
    ds = [math.hypot(x - cx, y - cy) for x in (0, w) for y in (0, h)]
    r0, r1 = min(ds) - pitch, max(ds) + pitch
    out = []
    r = r0 - (r0 % pitch) + .25
    while r < r1:
        # the arc's span over the sheet: angles where the circle meets the page rectangle (sampled)
        a_lo, a_hi = None, None
        for k in range(181):
            a = -math.pi / 2 + (math.pi / 2) * k / 180       # the quarter facing the page (up and right)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if -2 <= x <= w + 2 and -2 <= y <= h + 2:
                a_lo = a if a_lo is None else a_lo
                a_hi = a
        if a_lo is not None:
            a_lo -= .01
            a_hi += .01
            x0, y0 = cx + r * math.cos(a_lo), cy + r * math.sin(a_lo)
            x1, y1 = cx + r * math.cos(a_hi), cy + r * math.sin(a_hi)
            out.append(f"M{x0:.1f},{y0:.1f}A{r:.2f},{r:.2f} 0 0 1 {x1:.1f},{y1:.1f}")
        r += pitch
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<path d="{"".join(out)}" fill="none" stroke="#000" stroke-width=".5"/></svg>')


def gap_bar(w=232, h=20, seed=0):
    """A carved bar for the gap between two blocks: a pill of cut-away ground holding a short running
    acanthus scroll that flows out from a drilled boss at the centre to both ends."""
    B = h - 4
    body = [f'<defs>{GROUND}<g id="gb0">{unit(B, 32, seed * 7 + 1, s=B / 36)}</g><g id="gb1">{unit(B, 32, seed * 7 + 2, s=B / 36)}</g>'
            f'<clipPath id="gbc"><rect x="2" y="2" width="{w - 4}" height="{B}" rx="{B / 2}"/></clipPath></defs>']
    body.append(f'<rect x="2" y="2" width="{w - 4}" height="{B}" rx="{B / 2}" fill="url(#hg)"/>')
    body.append('<g clip-path="url(#gbc)">' + _row(w / 2 + 8, 2, w / 2, B, ["gb0", "gb1"], 32, True)
                + _row(-8, 2, w / 2, B, ["gb1", "gb0"], 32, False) + "</g>")
    body.append(f'<rect x="1.5" y="1.5" width="{w - 3}" height="{B + 1}" rx="{B / 2 + .5}" fill="none" stroke="#000" stroke-width="1"/>')
    body.append(f'<circle cx="{w / 2}" cy="{h / 2}" r="{B / 2 - 1}" fill="#fff" stroke="#000" stroke-width="1"/>'
                f'<circle cx="{w / 2}" cy="{h / 2}" r="{B / 2 - 3.5}" fill="url(#hg)" stroke="#000" stroke-width=".5"/>'
                f'<circle cx="{w / 2}" cy="{h / 2}" r="1.6" fill="#fff" stroke="#000" stroke-width=".5"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" stroke-linecap="round" stroke-linejoin="round">' + "".join(body) + "</svg>")


# ================================================================================================
# KING TIER: fine interlocking scroll on a punched matte ground, gold-line wire and beading
# ================================================================================================
# A punched matte: black, struck with a 1 px white punch every 2 px (no flat black anywhere).
def _punch_tile(seed=11, size=8, n=15):
    """A matte punched ground: a black tile struck with 1 px white punches at jittered places (no grid to
    read, no flat black over 3 px), tiled at 8 px, which is too fine to read as a pattern."""
    rng = random.Random(seed)
    cells = [(x, y) for x in range(0, size, 2) for y in range(0, size, 2)]
    rng.shuffle(cells)
    d = "".join(f"M{x + rng.choice((0, .5)):g},{y + rng.choice((0, .5)):g}h1v1h-1z" for x, y in cells[:n])
    return (f'<pattern id="hp" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
            f'<rect width="{size}" height="{size}" fill="#000"/><path d="{d}" fill="#fff"/></pattern>')


PUNCH = _punch_tile()


def fine_leaf(ink, spine, wmax, lobes=3, shade=1, phase=0.):
    """A small scroll leaf: white blade with a 0.5 px cut edge, shadow side cut with 0.5 px lines
    1.5 px apart, a fine trough at the midrib. Leaves this small read as engraving, not clip art."""
    pts, L = resample(spine, 1.)
    N = normals(pts)
    n = len(pts)
    lit = -shade

    def wid(u):
        return wmax * (math.sin(math.pi * min(1, u ** .7)) ** .7) * (.4 + .6 * min(1, u * 5))
    E = {1: [], -1: []}
    for i in range(n):
        u = i / (n - 1)
        for s in (1, -1):
            m = _lobe(u, lobes, phase + (0 if s == lit else .5)) if u > .1 else 1
            if s != lit:
                m = .8 + .2 * m
            E[s].append((pts[i][0] + N[i][0] * s * wid(u) * m, pts[i][1] + N[i][1] * s * wid(u) * m))
    ink.blade(_d(E[1] + E[-1][::-1], True), .5)
    hd = []
    for k in range(1, 5 if wmax > 3.2 else 2):
        off = 1.5 * k - .5 if wmax > 3.2 else 1.
        run = []
        for i in range(n):
            u = i / (n - 1)
            if off <= wid(u) * .8 - .7 and u < .9:
                run.append((pts[i][0] + N[i][0] * shade * off, pts[i][1] + N[i][1] * shade * off))
            else:
                if len(run) > 2:
                    hd.append(_d(run))
                run = []
        if len(run) > 2:
            hd.append(_d(run))
    hd.append(_d([(p[0] + N[i][0] * shade * .3, p[1] + N[i][1] * shade * .3) for i, p in enumerate(pts) if .08 < i / (n - 1) < .8]))
    ink.lines("".join(hd), .5)


def fine_unit(B, P, seed):
    """One unit of fine running scroll, flowing up a B x P box: a slender stem weaving from foot to head,
    a true logarithmic volute curling into the bay with seven small shaded leaves sprouting along it,
    a second, smaller curl on the stem's outer side, and leaves sheathing the stem. Mirrored units
    interlock, so the scroll runs on with no gaps."""
    rng = random.Random(seed)
    ink = Ink()
    cx = B / 2
    stem = bez((cx, P + .3), (cx - B * .42, P * .7), (cx - B * .42, P * .3), (cx, -.3), 26)
    node = stem[int(len(stem) * .45)]
    vr = B * .3
    vc = (cx + B * .2, P * .45)
    a0 = math.atan2(node[1] - vc[1], node[0] - vc[0])
    sp = spiral(vc[0], vc[1], vr, a0 + .3, 1.7, flip=False, end=.12)
    branch = bez(node, (node[0] + 1.5, node[1] + 1), (sp[0][0] - 1, sp[0][1] + 1.5), sp[0], 8)[:-1] + sp
    # small outer curl on the stem side, near the head
    q = stem[int(len(stem) * .78)]
    cc = (max(1.8 + B * .12, q[0] - B * .2), q[1] + P * .04)
    sp2 = spiral(cc[0], cc[1], B * .14, math.atan2(q[1] - cc[1], q[0] - cc[0]), 1.4, flip=True, end=.15)
    tw = [q] + sp2
    # leaves sheathing the stem low down (deepest)
    for u, side, ln in ((.12, 1, .55), (.28, -1, .5), (.62, -1, .5), (.88, 1, .45)):
        p0 = stem[int(len(stem) * u)]
        p1 = stem[int(len(stem) * u) + 3]
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]) + side * .55
        L = B * ln
        sp_ = [(p0[0] + math.cos(ang + side * .9 * t * t) * L * t, p0[1] + math.sin(ang + side * .9 * t * t) * L * t) for t in [k / 10 for k in range(11)]]
        fine_leaf(ink, sp_, B * .14, 3, -side, rng.random() * .3)
    ribbon(ink, stem, 1.8, 1.5, shade=-1, eye=False)
    ribbon(ink, tw, 1.3, .8, shade=1)
    # leaves along the volute's outside, from the root toward the eye, each smaller and tighter
    pts, Lsp = resample(branch, .7)
    N = normals(pts)
    nl = 8
    for j in range(nl):
        u = .04 + .7 * j / nl
        i = int(u * (len(pts) - 1))
        x, y = pts[i]
        tx, ty = pts[i + 2][0] - x, pts[i + 2][1] - y
        ta = math.atan2(ty, tx)
        # outward = away from the volute centre
        ox, oy = x - vc[0], y - vc[1]
        side = 1 if (-ty * ox + tx * oy) < 0 else -1
        L = B * (.52 - .3 * u) * rng.uniform(.9, 1.1)
        ang = ta - side * .5
        sp_ = [(x + math.cos(ang + side * 1.1 * t * t) * L * t, y + math.sin(ang + side * 1.1 * t * t) * L * t) for t in [k / 10 for k in range(11)]]
        fine_leaf(ink, sp_, L * .32, rng.choice((2, 3)), side, rng.random() * .3)
    ribbon(ink, branch, 1.6, .7, shade=1)
    return ink.svg()


def wire(x0, y0, x1, y1):
    """A fine gold-line inlay: a 1 px white wire."""
    return f'<path d="M{_n(x0)},{_n(y0)}L{_n(x1)},{_n(y1)}" stroke="#fff" stroke-width="1" fill="none"/>'


def beads_d(x0, y0, x1, y1, r=1, pitch=3.):
    """Path data for a row of round beads (white, struck on the black) from (x0,y0) to (x1,y1)."""
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(L / pitch))
    o = []
    for k in range(n + 1):
        t = k / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        o.append(f"M{x - r:.2f},{y:.2f}a{r},{r} 0 1 0 {2 * r},0a{r},{r} 0 1 0 {-2 * r},0")
    return "".join(o)


def king_frame(motif_key=None, seed=0, w=W, h=H):
    """The master frame at king tier: each band a black field punched to a matte, a gold-line wire and a
    row of beads along both its edges, and between them fine scroll flowing continuously round the
    page; Parker's bosses at the corners ringed with beads; the section cartouche at the foot."""
    S, T = SIDE, TOPB
    bx0, bx1 = 3, S - 5            # side band 3..41
    by0, by1 = 3, T - 4            # top band 3..22
    o = [f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="none" stroke="#000" stroke-width="1"/>']
    gd = f"M{bx0},{by0}H{w - bx0}V{h - by0}H{bx0}Z" f"M{bx1},{by1}V{h - by1}H{w - bx1}V{by1}Z"
    o.append(f'<path d="{gd}" fill="url(#hp)" fill-rule="evenodd"/>')
    # edges: wire, beads, wire on the outside; beads and wire on the inside
    ow, ob, iw, ib = 1.5, 4.0, 1.5, 4.0
    # scroll field between the bead rows
    sx0, sx1 = bx0 + 6.5, bx1 - 6.5            # side scroll: 9.5..34.5 (25 px)
    sy0, sy1 = by0 + 4.5, by1 - 4.5            # top scroll: 7.5..17.5 (10 px)
    Bs, Bt = sx1 - sx0, sy1 - sy0
    o.append(f'<clipPath id="kcl"><path d="M{sx0},{sy0}H{w - sx0}V{h - sy0}H{sx0}Z M{sx1},{sy1}V{h - sy1}H{w - sx1}V{sy1}Z" clip-rule="evenodd"/></clipPath>')
    o.append('<g clip-path="url(#kcl)">')
    Ps, Pt = round(Bs * 1.5, 1), round(Bt * 2.2, 1)
    o.append(_col(sx0, sy0 + 2, h - 2 * sy0 - 4, Bs, ["ks0", "ks1", "ks2"], Ps))
    o.append(_col(w - sx1, sy0 + 2, h - 2 * sy0 - 4, Bs, ["ks2", "ks0", "ks1"], Ps, flip=True))
    o.append(_row(sx1, sy0, w - 2 * sx1, Bt, ["kt0", "kt1"], Pt, True))
    o.append(_row(sx1, h - sy1, (w - 2 * sx1) / 2, Bt, ["kt1", "kt0"], Pt, True))
    o.append(_row(w / 2, h - sy1, (w - 2 * sx1) / 2, Bt, ["kt0", "kt1"], Pt, False))
    o.append("</g>")
    # gold-line wires and beads on both edges of every band
    wd, bd = [], []
    for (a0, b0, a1, b1) in ((bx0, by0, w - bx0, h - by0), (bx1, by1, w - bx1, h - by1)):
        sg = 1 if a0 == bx0 else -1      # inward offset for the outer box, outward for the inner
        for off, kind in ((ow, "w"), (ob, "b")):
            x0, y0, x1, y1 = a0 + sg * off, b0 + sg * off, a1 - sg * off, b1 - sg * off
            if kind == "w":
                wd.append(f"M{_n(x0)},{_n(y0)}H{_n(x1)}V{_n(y1)}H{_n(x0)}Z")
            else:
                bd.append((x0, y0, x1, y1))
    o.append(f'<path d="{"".join(wd)}" fill="none" stroke="#fff" stroke-width="1"/>')
    # bead rows as pattern-filled strips (a bead every 3 px), each pattern registered on its own row
    bp = []
    for k, (x0, y0, x1, y1) in enumerate(bd):
        for j, (rx, ry, rw, rh) in enumerate(((x0, y0 - 1.5, x1 - x0, 3), (x0, y1 - 1.5, x1 - x0, 3), (x0 - 1.5, y0, 3, y1 - y0), (x1 - 1.5, y0, 3, y1 - y0))):
            pid = f"kb{k}{j}"
            bp.append(f'<pattern id="{pid}" width="3" height="3" patternUnits="userSpaceOnUse" x="{_n(rx + (0 if j < 2 else 0))}" y="{_n(ry)}">'
                      f'<circle cx="1.5" cy="1.5" r="1" fill="#fff"/></pattern>')
            o.append(f'<rect x="{_n(rx)}" y="{_n(ry)}" width="{_n(rw)}" height="{_n(rh)}" fill="url(#{pid})"/>')
    o.insert(0, "<defs>" + "".join(bp) + "</defs>")
    # the reading panel's edge: a fine black double rule on the paper side
    o.append(f'<path d="M{bx1 + .75},{by1 + .75}H{w - bx1 - .75}V{h - by1 - .75}H{bx1 + .75}Z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{bx1 + 2.25},{by1 + 2.25}H{w - bx1 - 2.25}V{h - by1 - 2.25}H{bx1 + 2.25}Z" fill="none" stroke="#000" stroke-width=".5"/>')
    R = CORNER_R
    for (cx, cy), f in (((S / 2 - 1, 30), fig_dog), ((w - S / 2 + 1, 30), fig_hood), ((S / 2 - 1, h - 30), fig_heron), ((w - S / 2 + 1, h - 30), fig_drums)):
        o.append(king_roundel(cx, cy, R, f()))
    if motif_key and motif_key in MOTIFS:
        o.append(cartouche(w / 2, h - T / 2 - 1, 84, 24, MOTIFS[motif_key]()))
    dfs = ("<defs>" + PUNCH + GROUND
           + "".join(f'<g id="ks{k}">{fine_unit(Bs, Ps, seed * 10 + k)}</g>' for k in range(3))
           + "".join(f'<g id="kt{k}">{fine_unit(Bt, Pt, seed * 10 + 5 + k)}</g>' for k in range(2)) + "</defs>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" stroke-linecap="round" stroke-linejoin="round">' + dfs + "".join(o) + "</svg>")


def king_roundel(cx, cy, r, fig):
    """A boss ringed with beads between two gold-line wires, its ground punched, the figure standing up."""
    o = f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r + .5)}" fill="#000"/>'
    o += f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r - 1)}" fill="none" stroke="#fff" stroke-width="1"/>'
    n = int(TAU * (r - 3.5) / 3)
    o += '<path d="' + "".join(f"M{cx + (r - 3.5) * math.cos(TAU * k / n) - 1:.2f},{cy + (r - 3.5) * math.sin(TAU * k / n):.2f}a1,1 0 1 0 2,0a1,1 0 1 0 -2,0" for k in range(n)) + '" fill="#fff"/>'
    o += f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r - 6)}" fill="url(#hp)" stroke="#fff" stroke-width="1"/>'
    s = (2 * (r - 6) - 3) / 30
    o += f'<g transform="translate({_n(cx - 15 * s)},{_n(cy - 15 * s)}) scale({s:.4f})">{fig}</g>'
    return o


# The cut-away ground everywhere (bands, bosses, cartouches, gap bars) is the punched matte now.
GROUND = PUNCH.replace('id="hp"', 'id="hg"')
hunt_page_frame = page_frame
page_frame = king_frame


# ================================================================================================
# FITTED FILLS: white-line Himmapan flora on black, cut to every free rectangle of a sheet
# ================================================================================================

def _f1(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _bird(x, y, s=1., flip=False):
    """A small perching bird in white line (for the flora's hidden creatures), about 12 x 9 at s=1."""
    k = -1 if flip else 1
    P = lambda px, py: f"{_f1(x + k * px * s)},{_f1(y + py * s)}"
    body = (f"M{P(0, 0)}C{P(2, -4)} {P(6, -5)} {P(8, -3)}L{P(10, -4.5)}L{P(9.5, -2.5)}C{P(9, 0)} {P(6, 2)} {P(2, 1.5)}"
            f"L{P(-3, 3)}L{P(-1, .5)}Z")
    return (f'<path d="{body}" fill="#fff"/><path d="M{P(3.5, -1)}C{P(5, -2)} {P(6.5, -1.5)} {P(7, -.5)}" stroke="#000" stroke-width=".5" fill="none"/>'
            f'<circle cx="{_f1(x + k * 7.6 * s)}" cy="{_f1(y - 3 * s)}" r=".5" fill="#000"/>'
            f'<path d="M{P(4, 1.6)}V{P(4, 4.5)[P(4, 4.5).index(",") + 1:]}M{P(5.5, 1.4)}L{P(6, 4.5)}" stroke="#fff" stroke-width="1" fill="none"/>')


def _creature(kind, x, y, box):
    """Hide one of Parker's creatures: the bird is drawn here; the dog and heron come from the frame's
    bosses (white forms that read as silhouettes on the black)."""
    if kind == "bird" or box < 30:
        s = box / 14
        return _bird(x + box * .1, y + box * .6, s, flip=bool(int(x) % 2))
    f = fig_dog() if kind == "dog" else fig_heron()
    return f'<g transform="translate({_f1(x)},{_f1(y)}) scale({box / 30:.3f})">{f}</g>'


class _Pack:
    """Circles already taken in a panel, bucketed for fast free-space tests."""

    def __init__(self, cell=12.):
        self.c, self.b = cell, {}

    def add(self, x, y, r):
        k = (int(x // self.c), int(y // self.c))
        self.b.setdefault(k, []).append((x, y, r))

    def free(self, x, y, r, gap=.6):
        cx, cy = int(x // self.c), int(y // self.c)
        rr = int((r + 16) // self.c) + 1
        for j in range(cy - rr, cy + rr + 1):
            for i in range(cx - rr, cx + rr + 1):
                for (px, py, pr) in self.b.get((i, j), ()):
                    d = r + pr + gap
                    if (x - px) ** 2 + (y - py) ** 2 < d * d:
                        return False
        return True


def _r1(v):
    t = f"{v:.1f}"
    if t in ("-0.0", "0.0"):
        return "0"
    t = t.rstrip("0").rstrip(".")
    return t.replace("0.", ".", 1) if t.startswith(("0.", "-0.")) else t


def _pts(pts):
    """A polyline in relative coordinates, rounded to .1 px (the cheapest path text)."""
    x0, y0 = round(pts[0][0], 1), round(pts[0][1], 1)
    o = [f"M{_r1(x0)},{_r1(y0)}l"]
    px, py = x0, y0
    seg = []
    for x, y in pts[1:]:
        x, y = round(x, 1), round(y, 1)
        dx, dy = _r1(x - px), _r1(y - py)
        seg.append(dx + ("," if not dy.startswith("-") else "") + dy)
        px, py = x, y
    out = o[0] + "".join((" " if k and not v.startswith("-") else "") + v for k, v in enumerate(seg))
    return out


def _kranok(x, y, a, L, Wd, curl, side):
    """A kranok flame leaf from (x, y) heading a: the spine bends by curl and hooks at the tip, the outer
    edge (side +-1) breaks into two flames. Returns (outline pts, hatch polylines, spine pts)."""
    n = 10
    sp, nr = [], []
    px, py, aa = x, y, a
    for i in range(n + 1):
        u = i / n
        sp.append((px, py))
        nr.append((-math.sin(aa), math.cos(aa)))
        aa += curl * (.6 + 2.2 * u * u) / n
        px += math.cos(aa) * L / n
        py += math.sin(aa) * L / n
    outer, inner = [], []
    for i, ((sx, sy), (nx, ny)) in enumerate(zip(sp, nr)):
        u = i / n
        wv = Wd * math.sin(math.pi * min(1., u ** .75)) * (1 - .25 * u)
        fl = 1 - .45 * abs(math.sin(u * 2.5 * math.pi)) ** 1.5 if u > .2 else 1.
        outer.append((sx + side * nx * wv * fl, sy + side * ny * wv * fl))
        inner.append((sx - side * nx * wv * .55, sy - side * ny * wv * .55))
    hatch = []
    # ribs: from the midrib out toward each flame of the outer edge, the leaf's modelling
    if Wd >= 2.:
        for i in range(2, n - 1, 2 if Wd < 4 else 1):
            (sx, sy), (ox, oy) = sp[i], outer[i]
            hatch.append([(sx + (ox - sx) * .15, sy + (oy - sy) * .15), (sx + (ox - sx) * .75 + (sp[i + 1][0] - sx) * .6, sy + (oy - sy) * .75 + (sp[i + 1][1] - sy) * .6)])
    if Wd >= 3.:
        for f in ((.45,) if Wd < 5 else (.3, .62)):
            hatch.append([(sx + side * nx * Wd * f * math.sin(math.pi * min(1., (i / n) ** .75)) * (1 - .25 * i / n),
                           sy + side * ny * Wd * f * math.sin(math.pi * min(1., (i / n) ** .75)) * (1 - .25 * i / n))
                          for i, ((sx, sy), (nx, ny)) in enumerate(zip(sp, nr)) if .15 <= i / n <= .82])
    return outer + inner[::-1], hatch, sp


def flora(w, h, seed=0, grow="l", eggs=True, as_parts=False):
    """White-line flora on black for a w x h panel, after the Thai Himmapan forest engravings: light
    forms (kranok flame leaves, lotus and peony heads, palm fronds, buds) packed edge to edge on a black
    ground, each cut with black-line detail. Stems spring from the `grow` edge (l, r, t, b: the side
    that meets a text label) and lean away from it; whatever black is left is stippled with seed dots,
    so no flat black is larger than a few px. Panel coordinates (0..w, 0..h)."""
    rng = random.Random(seed)
    P = _Pack()
    m = min(w, h)
    pad = 3.5 if m >= 24 else 1.
    inside = lambda x, y, r: pad + r <= x <= w - pad - r and pad + r <= y <= h - pad - r
    base = {"l": 0., "r": math.pi, "t": math.pi / 2, "b": -math.pi / 2}.get(grow, 0.)
    L0 = max(6., min(28., m * .5))
    stems, leaves, hatch, heads, hdet, hdark, blades, dots = [], [], [], [], [], [], [], []
    extra = []
    if eggs and w >= 60 and h >= 40 and rng.random() < .8:      # a hidden creature
        box = min(30., h - 12, w / 3)
        ex, ey = rng.uniform(pad + 2, w - box - pad - 2), rng.uniform(pad + 2, h - box - pad - 2)
        extra.append(_creature(rng.choice(("bird", "bird", "dog", "heron")) if box >= 26 else "bird", ex, ey, box))
        P.add(ex + box / 2, ey + box / 2, box * .5)

    def leaf(x, y, a, L, side):
        Wd = L * rng.uniform(.26, .34)
        ol, ha, sp = _kranok(x, y, a, L, Wd, side * rng.uniform(.5, 1.1), side)
        chk = sp[4::2]
        for (sx, sy) in chk:
            if not inside(sx, sy, .5) or not P.free(sx, sy, Wd * .5, .3):
                return False
        for (sx, sy) in chk:
            P.add(sx, sy, Wd * .55)
        leaves.append(_pts(ol) + "Z")
        hatch.extend(_pts(hh) for hh in ha if len(hh) > 1)
        return True

    def head(x, y, r):
        """A lotus (pointed petals) or a peony (round petals): white, its petals parted in black."""
        a0 = rng.uniform(0, TAU)
        if r >= 3.5 and rng.random() < .55:
            n = rng.choice((6, 7, 8))
            d = ""
            cur = None
            for k in range(n):
                a = a0 + TAU * k / n
                c, s_ = math.cos(a), math.sin(a)
                hw = math.pi / n * .95
                p0 = (round(x + math.cos(a - hw) * r * .3, 1), round(y + math.sin(a - hw) * r * .3, 1))
                p1 = (round(x + math.cos(a + hw) * r * .3, 1), round(y + math.sin(a + hw) * r * .3, 1))
                tip = (round(x + c * r, 1), round(y + s_ * r, 1))
                cl = (round(x + math.cos(a - hw * .9) * r * .78, 1), round(y + math.sin(a - hw * .9) * r * .78, 1))
                cr = (round(x + math.cos(a + hw * .9) * r * .78, 1), round(y + math.sin(a + hw * .9) * r * .78, 1))
                if cur is None:
                    d += f"M{_r1(p0[0])},{_r1(p0[1])}"
                    cur = p0
                elif (p0[0] - cur[0]) ** 2 + (p0[1] - cur[1]) ** 2 > .04:
                    d += f"l{_r1(p0[0] - cur[0])},{_r1(p0[1] - cur[1])}"
                rel = lambda q, o=None: f"{_r1(q[0] - (o or cur)[0])},{_r1(q[1] - (o or cur)[1])}"
                d += f"q{rel(cl)} {rel(tip)}q{rel(cr, tip)} {rel(p1, tip)}"
                cur = p1
                if r >= 5:
                    hdet.append(_pts([(x + c * r * .42, y + s_ * r * .42), (x + c * r * .8, y + s_ * r * .8)]))
            heads.append(d + "z")
            rc = r * .34
            hdark.append(f"M{_f1(x - rc)},{_f1(y)}a{_f1(rc)},{_f1(rc)} 0 1 0 {_f1(2 * rc)},0a{_f1(rc)},{_f1(rc)} 0 1 0 {_f1(-2 * rc)},0")
            if rc >= 1.6:
                dots.append((x, y, .8))
        else:
            n = 5 if r < 5 else 7
            pr = r * (.42 if n == 5 else .36)
            for k in range(n):
                a = a0 + TAU * k / n
                cx_, cy_ = x + math.cos(a) * (r - pr), y + math.sin(a) * (r - pr)
                heads.append(f"M{_r1(cx_ - pr)},{_r1(cy_)}a{_r1(pr)},{_r1(pr)} 0 1 0 {_r1(2 * pr)},0a{_r1(pr)},{_r1(pr)} 0 1 0 {_r1(-2 * pr)},0")
            ri = r * .42
            heads.append(f"M{_f1(x - ri)},{_f1(y)}a{_f1(ri)},{_f1(ri)} 0 1 0 {_f1(2 * ri)},0a{_f1(ri)},{_f1(ri)} 0 1 0 {_f1(-2 * ri)},0")
            if ri >= 1.8:
                rj = ri * .5
                hdet.append(f"M{_f1(x - rj)},{_f1(y)}a{_f1(rj)},{_f1(rj)} 0 1 0 {_f1(2 * rj)},0")
        P.add(x, y, r)

    def frond(x, y, a, r):
        """A palm spray: narrow white blades fanned about a."""
        n = 5 if r < 7 else 7
        for k in range(n):
            b = a + (k / (n - 1) - .5) * 1.9
            Lb = r * 2 * (1 - .25 * abs(k / (n - 1) - .5) * 2)
            bw = max(1.1, r * .16)
            bend = rng.uniform(-.25, .25)
            p = [(x, y)]
            pts_l, pts_r = [], []
            for i in range(1, 5):
                u = i / 4
                bb = b + bend * u
                cx_ = x + math.cos(bb) * Lb * u
                cy_ = y + math.sin(bb) * Lb * u
                ww = bw * math.sin(math.pi * min(1, u * 1.3)) * (1 - u * .6)
                pts_l.append((cx_ - math.sin(bb) * ww, cy_ + math.cos(bb) * ww))
                pts_r.append((cx_ + math.sin(bb) * ww, cy_ - math.cos(bb) * ww))
            blades.append(_pts(p + pts_l + pts_r[::-1]) + "Z")
        P.add(x + math.cos(a) * r, y + math.sin(a) * r, r)

    def stem(x, y, a, L):
        """A stem from the label edge: a white line that leans away and curls, leaves alternating along
        it, a head at its end."""
        pts = [(x, y)]
        curl = rng.choice((-1, 1)) * rng.uniform(.01, .035)
        step = 1.5
        for t in range(int(L / step)):
            a += curl * (1 + t * .01) + .04 * math.sin(t * .15 + seed) + rng.uniform(-.03, .03)
            nx, ny = x + math.cos(a) * step, y + math.sin(a) * step
            if not inside(nx, ny, .5) or (t > 2 and not P.free(nx + math.cos(a) * 2, ny + math.sin(a) * 2, .9, .4)):
                break
            x, y = nx, ny
            pts.append((x, y))
        if len(pts) < 6:
            return
        stems.append(_pts(pts))
        sd = rng.choice((-1, 1))
        Ls = max(5., min(L0, m * .45))
        for k in range(3, len(pts) - 2, max(3, int(Ls * .45))):
            (x0, y0), (x1, y1) = pts[k - 1], pts[k]
            ta = math.atan2(y1 - y0, x1 - x0)
            leaf(x1, y1, ta + sd * rng.uniform(.5, .9), Ls * rng.uniform(.75, 1.05), sd)
            sd = -sd
        for (sx, sy) in pts[1::2]:
            P.add(sx, sy, .9)
        ex_, ey_ = pts[-1]
        rh = max(2.5, min(L0 * .45, m * .3))
        for rr in (rh, rh * .7, rh * .5):
            cx_, cy_ = ex_ + math.cos(a) * rr, ey_ + math.sin(a) * rr
            if inside(cx_, cy_, rr) and P.free(cx_, cy_, rr, .2):
                head(cx_, cy_, rr)
                break
    # stems from the label edge
    gap = max(8., L0 * 1.3)
    if grow in "lr":
        ys = [pad + gap * .5 + k * gap for k in range(int((h - 2 * pad) / gap) + 1)]
        for y in ys:
            if y < h - pad:
                stem(pad + 1 if grow == "l" else w - pad - 1, y, base + rng.uniform(-.5, .5), w * rng.uniform(.5, 1.))
    else:
        xs = [pad + gap * .5 + k * gap for k in range(int((w - 2 * pad) / gap) + 1)]
        for x in xs:
            if x < w - pad:
                stem(x, pad + 1 if grow == "t" else h - pad - 1, base + rng.uniform(-.5, .5), h * rng.uniform(.5, 1.))
    # then pack: heads, fronds, leaves, buds, seed dots, from large to small
    for r in [rr for rr in (L0 * .55, L0 * .42, L0 * .32, 4.5, 3.4) if rr <= m * .42]:
        sp_ = r * 1.6
        cand = [(i * sp_ + rng.uniform(0, sp_), j * sp_ + rng.uniform(0, sp_)) for j in range(int(h / sp_) + 1) for i in range(int(w / sp_) + 1)]
        rng.shuffle(cand)
        for (x, y) in cand:
            if not inside(x, y, r) or not P.free(x, y, r, .3):
                continue
            q = rng.random()
            if r >= 4 and q < .3:
                head(x, y, r)
            elif r >= 4 and q < .5:
                frond(x - math.cos(base) * r, y - math.sin(base) * r, base + rng.uniform(-.7, .7), r)
            elif r >= 3:
                aa = base + rng.uniform(-1.2, 1.2)
                if not leaf(x - math.cos(aa) * r, y - math.sin(aa) * r, aa, 2 * r * 1.05, rng.choice((-1, 1))):
                    head(x, y, r * .8)
            else:
                head(x, y, r)
    # seed stipple in what black is left: enough that no flat black runs past a few px
    sp_ = 3.5
    for j in range(int(h / sp_) + 1):
        for i in range(int(w / sp_) + 1):
            x, y = i * sp_ + rng.randint(0, 1), j * sp_ + rng.randint(0, 1)
            if inside(x, y, .6) and P.free(x, y, 1.6, 0):
                dots.append((x, y, .55))
                P.add(x, y, .6)
    dd = ""
    if dots:
        ds = sorted(((round(x), round(y)) for x, y, r in dots), key=lambda d: (d[1], d[0]))
        dd = f"M{ds[0][0]},{ds[0][1]}h0" + "".join(f"m{x - px},{y - py}h0" for (px, py), (x, y) in zip(ds, ds[1:]))
    parts = {"stems": stems, "leaves": leaves, "hatch": hatch, "blades": blades, "heads": heads,
             "hdet": hdet, "hdark": hdark, "dots": [dd] if dd else []}
    if m >= 24:
        parts["wire"] = [f"M1.5,1.5h{_f1(w - 3)}v{_f1(h - 3)}h{_f1(3 - w)}z"]
    if as_parts:
        return parts, extra
    return _paint({k: v for k, v in parts.items()}, extra, [f"M0,0h{_f1(w)}v{_f1(h)}h{_f1(-w)}z"])


# how each class of fill path is painted, in order
_PAINT = (("wire", 'fill="none" stroke="#fff" stroke-width="1"'),
          ("stems", 'fill="none" stroke="#fff" stroke-width="1.5"'),
          ("leaves", 'fill="#fff" stroke="#000" stroke-width=".5"'),
          ("hatch", 'fill="none" stroke="#000" stroke-width=".5"'),
          ("blades", 'fill="#fff"'),
          ("heads", 'fill="#fff" stroke="#000" stroke-width=".5"'),
          ("hdet", 'fill="none" stroke="#000" stroke-width=".5"'),
          ("hdark", 'fill="#000"'),
          ("dots", 'fill="none" stroke="#fff" stroke-width="1"'),
          ("beads", 'fill="#fff"'),
          ("fillet", 'fill="none" stroke="#fff" stroke-width="1"'))


def _paint(parts, extra, ground):
    o = [f'<path d="{"".join(ground)}" fill="#000"/>'] if ground else []
    for k, attrs in _PAINT:
        if parts.get(k):
            o.append(f'<path d="{"".join(parts[k])}" {attrs}/>')
    return "".join(o) + "".join(extra)


_LEAD = re.compile(r"^M(-?[\d.]+),(-?[\d.]+)")


def _shift(sub, dx, dy):
    """Move one subpath (absolute moveto first, relative after) by dx, dy."""
    return _LEAD.sub(lambda m_: f"M{_r1(float(m_.group(1)) + dx)},{_r1(float(m_.group(2)) + dy)}", sub, count=1)


def moulding(w, h):
    """A strip too thin for flora: beading on black when there is room, else a black fillet with a
    gold-line wire. Returns parts (subpaths with an absolute first moveto, strip coordinates)."""
    t = min(w, h)
    horiz = w >= h
    if t >= 6:
        r = min(2., (t - 3) / 2)
        pitch = 2 * r + 1.5
        n = int(((w if horiz else h) - 2) / pitch)
        d = []
        for k in range(n):
            c = 1 + pitch / 2 + k * pitch
            x, y = (c, h / 2) if horiz else (w / 2, c)
            d.append(f"M{_r1(x - r)},{_r1(y)}a{_r1(r)},{_r1(r)} 0 1 0 {_r1(2 * r)},0a{_r1(r)},{_r1(r)} 0 1 0 {_r1(-2 * r)},0")
        return {"beads": d}
    if t >= 3:
        return {"fillet": [f"M{_r1(1 if horiz else w / 2)},{_r1(h / 2 if horiz else 1)}" + (f"h{_r1(w - 2)}" if horiz else f"v{_r1(h - 2)}")]}
    return {}


def sheet_fill(panels, strips, seed=0, w=W, h=H, ground=(), matte=(), motif=None, extra_svg=""):
    """One sheet's ornament layer, a single SVG, laid only where no panel is (edition plan 1.5 rule 8,
    1.6 leftover space): `panels` [(x, y, w, h, grow)] get a carved Himmapan frieze (the plan puts one
    in the largest gap between panels, with the page's `motif` small at its centre in a cartouche),
    `strips` [(x, y, w, h)] a bead moulding, `matte` the frame's punched ground (frame margin below the
    plate), `ground` plain black (slivers and the edges under labels). Paths are merged by kind across
    the sheet, so the element count stays small."""
    allp, extra = {}, []
    gd = []
    for k, (x, y, pw, ph, g) in enumerate(panels):
        parts, ex = flora(pw, ph, seed * 101 + k * 7 + int(x) * 3 + int(y), g, as_parts=True)
        for kk, v in parts.items():
            allp.setdefault(kk, []).extend(_shift(sub, x, y) for sub in v)
        extra += [f'<g transform="translate({_f1(x)},{_f1(y)})">{e}</g>' for e in ex]
        if motif and motif in MOTIFS and ph >= 16 and pw >= ph * 4:
            ch = ph - 4
            extra.append(cartouche(x + pw / 2, y + ph / 2, ch * 3.2, ch, MOTIFS[motif]()))
            motif = None
    for (x, y, sw, sh) in strips:
        for kk, v in moulding(sw, sh).items():
            allp.setdefault(kk, []).extend(_shift(sub, x, y) for sub in v)
    for (x, y, rw, rh) in list((p[0], p[1], p[2], p[3]) for p in panels) + list(strips) + list(ground):
        gd.append(f"M{_r1(x)},{_r1(y)}h{_r1(rw)}v{_r1(rh)}h{_r1(-rw)}z")
    mt = "".join(f"M{_r1(x)},{_r1(y)}h{_r1(rw)}v{_r1(rh)}h{_r1(-rw)}z" for (x, y, rw, rh) in matte)
    body = _paint(allp, extra, gd)
    if mt:
        body = f'<path d="{mt}" fill="url(#hg)"/>' + body
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'stroke-linecap="round" stroke-linejoin="round"><defs>{GROUND}</defs>' + body + extra_svg + "</svg>")
