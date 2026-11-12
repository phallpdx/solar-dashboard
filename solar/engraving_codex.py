"""engraving_codex.py: the house style for the Morning Edition's engraved plates.

Modelled on The Engraver's Codex (Sam Alfano): deep-relief acanthus scrollwork. Volutes of a
round-carved stem wind into tight curls; fronds of slender swept fingers spring from them, each
finger shaded with lines that run along its form (dense and dark on the inside of its curve, a
black shadow where it turns under, a white highlight on its outer edge) and rolling into a curl at
its tip. A cut-away ruled ground sits behind so the relief stands up. Ribbon banners, knurled bars,
beaded mouldings, egg-and-dart and a pedestal complete the vocabulary.

Pure standard library, deterministic. All coordinates are plate px (CSS px).

HOW IT PAINTS. Engraved motifs are drawn into a Canvas: each motif is an object (a white shape
with an outline) carrying hatch lines. When the canvas is emitted, every line is clipped against
the shapes of the objects painted above it (a 1 px occlusion raster), so the whole scroll layer
comes out as ONE white path plus ONE path per stroke weight, with correct overlaps. That keeps a
full plate far under 600 elements and, with integer-tenth coordinates, near 100 KB.
Every public motif function takes cv=None: pass a Canvas to draw into it (returns ""), or omit it
to get a self-contained SVG fragment.

E-ink rules (Kindle PW11, DPR 2; eink-guide.md 1-2) are built in: strokes are 0.5, 1 or 1.5 CSS px;
colours are #000/#fff only (grounds are hatch patterns of whole device pixels); curved hatching
keeps >= 1 px clear gap (it is laid coarse-to-fine and a line is dropped where it would crowd
under its pitch); black masses are built from 1 px lines laid 0.8 px apart (solid).

PUBLIC API
  svg_doc(w, h, body)                         complete <svg> with the shared <defs>
  codex_defs()                                the <defs> (ground / knurl patterns) alone
  pat(key)                                    fill="url(#...)" for a pattern: G M L S X D V K
  Canvas()                                    occlusion-aware accumulator (see above)
  dark_ground(shape, tone="G")                cut-away ground behind the relief
  hatch_poly(poly, angle, pitch, phase)       straight hatch clipped to a polygon -> polylines
  hatch_d(...)                                the same as path data
  acanthus_finger(x, y, ang, length, ...)     one swept, shaded finger with a rolled tip
  acanthus_frond(x, y, ang, length, n, ...)   a fan of fingers from one root (an acanthus leaf)
  acanthus_leaf(...)                          alias of acanthus_frond
  acanthus_scroll(cx, cy, r, a0, turns, flip, seed, tail, tail_bend, ...)   a full volute
  volute_spine(...), scroll_root(...)         its centre line / where its stem starts
  running_scroll(x0, y0, ang, length, breadth, seed, mirror, ...)  a rinceau along a line
  scroll_band(x, y, w, h, seed, center_gap=0) a frieze filling w x h exactly
  scroll_column(x, y, w, h, seed, upward, mirror)
  fill_scrolls(x, y, w, h, occupied, seed, ...) grow volutes into whatever ground is left
  palmette(cx, cy, size, up=True, seed)       a symmetric anthemion of curling fingers
  cartouche(cx, cy, w, h, seed)               -> (svg, inner_rect, inner_path_d)
  ribbon_banner(cx, cy, w, h, arch, seed)     -> (svg, face_centre_points)
  knurled_bar(x, y, w, h)
  bead_moulding(x, y, w, r)
  egg_and_dart(x, y, w, h)
  pedestal(x, y, w, h, seed)                  -> (svg, tablet_rect)
  frame_plate(w, h, seed, fill_fn)            complete <svg> filling any w x h
"""
import math
import random
import zlib

PI = math.pi
TAU = 2 * PI

# ----------------------------------------------------------------------------------------------
# numbers and path data
# ----------------------------------------------------------------------------------------------


def _f(t):
    """An integer count of tenths as the shortest decimal string."""
    neg = t < 0
    t = abs(t)
    a, b = divmod(t, 10)
    s = (str(a) if a else "") + ("." + str(b) if b else "")
    return ("-" if neg else "") + (s or "0")


def _n(x):
    return _f(int(round(x * 10)))


def _dp(pts, tol):
    """Douglas-Peucker simplification (iterative)."""
    n = len(pts)
    if n < 3 or tol <= 0:
        return list(pts)
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        best, bi = -1., -1
        for i in range(a + 1, b):
            px, py = pts[i]
            d = abs((px - ax) * dy - (py - ay) * dx) / L if L > 1e-6 else math.hypot(px - ax, py - ay)
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack.append((a, bi))
            stack.append((bi, b))
    return [p for p, k in zip(pts, keep) if k]


def _d(pts, close=False, tol=.22):
    """Path data in plain CSS px: absolute M, relative l (tenths, drift-free)."""
    if len(pts) < 2:
        return ""
    if tol:
        pts = _dp(pts, tol)
    X = [int(round(p[0] * 10)) for p in pts]
    Y = [int(round(p[1] * 10)) for p in pts]
    out = ["M", _f(X[0]), ",", _f(Y[0]), "l"]
    first = True
    for i in range(1, len(X)):
        dx, dy = X[i] - X[i - 1], Y[i] - Y[i - 1]
        if dx == 0 and dy == 0:
            continue
        sx, sy = _f(dx), _f(dy)
        if not first and sx[0] != "-":
            out.append(" ")
        out.append(sx)
        if sy[0] != "-":
            out.append(",")
        out.append(sy)
        first = False
    if first:
        return ""
    if close:
        out.append("z")
    return "".join(out)


_Q = 4          # canvas path units per CSS px (quarter px = half a device pixel)
_QT = ' transform="scale(.25)"'


class _Pen:
    """Path data in integer quarter-px (for a transform="scale(.25)" path), every subpath after the
    first starting with a relative m: about a third shorter than decimal absolute data."""

    def __init__(self):
        self.o = []
        self.cur = None

    def add(self, pts, close=False, tol=.22):
        if len(pts) < 2:
            return
        if tol:
            pts = _dp(pts, tol)
        X = [int(round(p[0] * _Q)) for p in pts]
        Y = [int(round(p[1] * _Q)) for p in pts]
        o = self.o
        if self.cur is None:
            o.append(f"M{X[0]} {Y[0]}")
        else:
            dx, dy = X[0] - self.cur[0], Y[0] - self.cur[1]
            o.append(f"m{dx}{'' if dy < 0 else ' '}{dy}")
        seg = []
        for i in range(1, len(X)):
            dx, dy = X[i] - X[i - 1], Y[i] - Y[i - 1]
            if dx or dy:
                seg.append(f"{dx}{'' if dy < 0 else ' '}{dy}")
        if not seg:
            seg = ["0 0"]
        o.append("l" + " ".join(seg).replace(" -", "-"))
        if close:
            o.append("z")
            self.cur = (X[0], Y[0])
        else:
            self.cur = (X[-1], Y[-1])

    def d(self):
        return "".join(self.o)


def _ell_pts(cx, cy, rx, ry, n=48, a0=0., a1=TAU):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def _smooth(e0, e1, x):
    if x <= e0:
        return 0.
    if x >= e1:
        return 1.
    t = (x - e0) / (e1 - e0)
    return t * t * (3 - 2 * t)


def _area(p):
    n = len(p)
    return sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1] for i in range(n)) / 2


# ----------------------------------------------------------------------------------------------
# the canvas: objects in paint order, lines clipped by everything painted above them
# ----------------------------------------------------------------------------------------------

class Canvas:
    """Engraved objects in paint order. cv.obj(polys, outline) starts an object (white shapes,
    outlined at `outline` px, 0 for none); cv.hair(pl) / cv.line(pl) / cv.heavy(pl) add 0.5, 1 and
    1.5 px lines to it (pl: a list of points, or a list of such lists). cv.svg() emits one white
    path and one path per stroke weight, each line clipped where later objects cover it."""

    def __init__(self):
        self.objs = []

    def obj(self, polys=(), outline=1.):
        o = ([p for p in polys if len(p) > 2], outline, {.5: [], 1.: [], 1.5: []})
        self.objs.append(o)
        return o

    def _add(self, w, pl):
        if not pl:
            return
        if not self.objs:
            self.obj()
        if isinstance(pl[0][0], (int, float)):
            if len(pl) > 1:
                self.objs[-1][2][w].append(pl)
        else:
            self.objs[-1][2][w].extend(q for q in pl if len(q) > 1)

    def hair(self, pl):
        self._add(.5, pl)

    def line(self, pl):
        self._add(1., pl)

    def heavy(self, pl):
        self._add(1.5, pl)

    def extend(self, other):
        self.objs.extend(other.objs)

    def svg(self):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for w, lines in strokes.items():
                for pl in lines:
                    _clip_runs(pl, mask, x0, y0, W, H, out[w])
            if ow:
                for poly in polys:
                    _clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                _fill_mask(poly, mask, x0, y0, W, H)
        T = _QT
        res = []
        pen = _Pen()
        for polys, _, _ in self.objs:
            for poly in polys:
                pen.add(poly if _area(poly) >= 0 else poly[::-1], True, .5)
        if pen.o:
            res.append(f'<path{T} d="{pen.d()}" fill="#fff" stroke="none"/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _Pen()
                for pl in out[w]:
                    pen.add(pl, False, .4 if w < 1 else .45)
                res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_n(w * _Q)}"/>')
        return "".join(res)


def _fill_mask(poly, mask, x0, y0, W, H):
    n = len(poly)
    ys = [p[1] for p in poly]
    r0 = max(0, int(math.floor(min(ys) - y0)))
    r1 = min(H - 1, int(math.ceil(max(ys) - y0)))
    edges = []
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        if ay != by:
            if ay > by:
                ax, ay, bx, by = bx, by, ax, ay
            edges.append((ay - y0, by - y0, ax - x0, (bx - ax) / (by - ay)))
    one = b"\x01" * W
    for r in range(r0, r1 + 1):
        yc = r + .5
        xs = [ex + (yc - ey0) * sl for ey0, ey1, ex, sl in edges if ey0 <= yc < ey1]
        if len(xs) < 2:
            continue
        xs.sort()
        row = mask[r]
        for j in range(0, len(xs) - 1, 2):
            a = max(0, int(math.ceil(xs[j] - .5)))
            b = min(W, int(math.floor(xs[j + 1] + .5)))
            if b > a:
                row[a:b] = one[:b - a]


def _clip_runs(pl, mask, x0, y0, W, H, out):
    """Split polyline pl into the runs not covered by mask (resampled to 1 px for the test)."""
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L = math.hypot(dx, dy)
        if L > 1.:
            k = int(L)
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


def _own(cv):
    return (Canvas(), True) if cv is None else (cv, False)


# ----------------------------------------------------------------------------------------------
# patterns (grounds, knurls) and the document wrapper
# ----------------------------------------------------------------------------------------------

_CR = ' shape-rendering="crispEdges"'


def _diag(s, back=False):
    if back:
        return f"M0,0L{s},{s}M{-s / 2},{s / 2}L{s / 2},{s * 1.5}M{s / 2},{-s / 2}L{s * 1.5},{s / 2}"
    return f"M0,{s}L{s},0M{-s / 2},{s / 2}L{s / 2},{-s / 2}M{s / 2},{s * 1.5}L{s * 1.5},{s / 2}"


_PATS = {
    "G": (1.5, 1.5, f'<path d="M0,.75H1.5" stroke="#000" stroke-width="1"{_CR}/>'),   # deep ruled ground, 67 %
    "M": (2, 2, f'<path d="M0,1H2" stroke="#000" stroke-width="1"{_CR}/>'),           # mid ruled, 50 %
    "L": (3, 3, f'<path d="M0,1.25H3" stroke="#000" stroke-width=".5"{_CR}/>'),       # light ruled, 17 %
    "S": (2, 2, '<rect width="1" height="1" fill="#000"/><rect x="1" y="1" width=".5" height=".5" fill="#000"/>'),
    "X": (3, 3, f'<path d="{_diag(3)}{_diag(3, True)}" stroke="#000" stroke-width=".5"/>'),
    "D": (3, 3, f'<path d="{_diag(3)}" stroke="#000" stroke-width=".5"/>'),
    "V": (3, 3, f'<path d="M1.25,0V3" stroke="#000" stroke-width=".5"{_CR}/>'),
    "K": (3, 3, f'<path d="{_diag(3)}" stroke="#000" stroke-width="1"/>'),
}
_PID = "cdx"


def pat(k):
    """fill= value for a house pattern: G deep ruled ground, M mid ruled, L light ruled, S stipple,
    X cross-hatch, D 45-degree hatch, V vertical rules, K knurl."""
    return f"url(#{_PID}{k})"


def codex_defs():
    return "<defs>" + "".join(
        f'<pattern id="{_PID}{k}" width="{w}" height="{h}" patternUnits="userSpaceOnUse">{c}</pattern>'
        for k, (w, h, c) in sorted(_PATS.items())) + "</defs>"


def svg_doc(w, h, body, cls="codex"):
    """A complete plate: width/height/viewBox w x h, the shared defs, then body."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="korn {cls}" width="{_n(w)}" height="{_n(h)}" '
            f'viewBox="0 0 {_n(w)} {_n(h)}" fill="none" stroke="#000" stroke-width=".5" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + codex_defs() + body + "</svg>")


def dark_ground(shape, tone="G"):
    """The cut-away background behind the relief: shape is (x, y, w, h), a point list or path d.
    tone: G deep ruled (default), M mid ruled, S stipple, X cross-hatch. 1 element."""
    if isinstance(shape, tuple) and len(shape) == 4:
        x, y, w, h = shape
        d = f"M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z"
    elif isinstance(shape, list):
        d = _d(shape, True, 0)
    else:
        d = shape
    return f'<path d="{d}" fill="{pat(tone)}" stroke="none"/>'


def _clip(cid, x, y, w, h, body):
    return (f'<clipPath id="{cid}"><path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g>')


def _uid(*a):
    return "cdc" + format(zlib.crc32(repr(a).encode()) & 0xffffff, "x")


# ----------------------------------------------------------------------------------------------
# hatch helpers
# ----------------------------------------------------------------------------------------------

def hatch_poly(poly, angle=45., pitch=2., phase=0., inset=0.):
    """Straight parallel lines at `angle` degrees, `pitch` px apart (use 1.5, 2 or 3), clipped to
    a closed polygon (even-odd). Returns a list of 2-point polylines (feed cv.hair)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    proj = [(px * vx + py * vy, px * ux + py * uy) for px, py in poly]
    lo = min(p[0] for p in proj)
    hi = max(p[0] for p in proj)
    out = []
    n = len(proj)
    v = math.ceil((lo - phase) / pitch) * pitch + phase
    while v <= hi:
        xs = []
        for i in range(n):
            (a0, b0), (a1, b1) = proj[i], proj[(i + 1) % n]
            if (a0 <= v < a1) or (a1 <= v < a0):
                xs.append(b0 + (b1 - b0) * (v - a0) / (a1 - a0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            s0, s1 = xs[j] + inset, xs[j + 1] - inset
            if s1 - s0 > .6:
                out.append([(v * vx + s0 * ux, v * vy + s0 * uy), (v * vx + s1 * ux, v * vy + s1 * uy)])
        v += pitch
    return out


def hatch_d(poly, angle=45., pitch=2., phase=0., inset=0.):
    """hatch_poly as path data (stroke it at .5)."""
    return "".join(_d(p, tol=0) for p in hatch_poly(poly, angle, pitch, phase, inset))


# ----------------------------------------------------------------------------------------------
# ribbons: a centre line with a half-width each side; lines laid in its (u, s) coordinates
# ----------------------------------------------------------------------------------------------

class _Rib:
    """Centre line pts with half-widths wl (+normal side) and wr (-normal side).
    at(u, s): u in [0, 1] along, s in [-1, 1] across (+1 = the +normal edge)."""

    def __init__(self, pts, wl, wr):
        self.P = pts
        n = self.n = len(pts)
        N = []
        for i in range(n):
            a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            tl = math.hypot(tx, ty) or 1
            N.append((-ty / tl, tx / tl))
        self.N = N
        self.wl, self.wr = wl, wr
        L = 0.
        for i in range(1, n):
            L += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        self.L = L or 1.

    def _ix(self, u):
        f = min(max(u, 0.), 1.) * (self.n - 1)
        i = min(int(f), self.n - 2)
        return i, f - i

    def at(self, u, s):
        i, r = self._ix(u)
        P, N = self.P, self.N
        px = P[i][0] + (P[i + 1][0] - P[i][0]) * r
        py = P[i][1] + (P[i + 1][1] - P[i][1]) * r
        nx = N[i][0] + (N[i + 1][0] - N[i][0]) * r
        ny = N[i][1] + (N[i + 1][1] - N[i][1]) * r
        W = self.wl if s >= 0 else self.wr
        w = W[i] + (W[i + 1] - W[i]) * r
        return (px + nx * s * w, py + ny * s * w)

    def width(self, u, side):
        i, r = self._ix(u)
        W = self.wl if side > 0 else self.wr
        return W[i] + (W[i + 1] - W[i]) * r

    def outline(self):
        n = self.n
        L = [self.at(i / (n - 1), 1.) for i in range(n)]
        R = [self.at(i / (n - 1), -1.) for i in range(n)]
        return _dp(L + R[::-1], .15)

    def contour(self, s, u0, u1, minw=0., step=None):
        """Polylines at constant s from u0 to u1, broken where the half-width is under minw."""
        if step is None:
            step = 1.2 / self.L
        segs, cur = [], []
        u = u0
        side = 1 if s >= 0 else -1
        while u <= u1 + 1e-9:
            if self.width(u, side) >= minw:
                cur.append(self.at(u, s))
            else:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            u += step
        if len(cur) > 1:
            segs.append(cur)
        return segs

    def inset(self, side, d, u0, u1, step=None):
        """Polylines d(u) px inside the `side` edge (d returns None where there is no line)."""
        if step is None:
            step = 1.2 / self.L
        segs, cur = [], []
        u = u0
        while u <= u1 + 1e-9:
            dd = d(u)
            w = self.width(u, side)
            if dd is not None and w > dd + .3:
                cur.append(self.at(u, side * (1 - dd / w)))
            else:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            u += step
        if len(cur) > 1:
            segs.append(cur)
        return segs


def _fill_lines(R, s0, s1, pitch=2., u0=0., u1=1., depth=4):
    """Lines along the form between s0 and s1 on R, added coarse-to-fine: a line whose neighbours
    lie a fraction g of the half-width away is kept only where half-width * g >= pitch, so the
    hatching thins gracefully toward tips and never crowds under its pitch."""
    span = abs(s1 - s0)
    out = []
    for dpt in range(1, depth + 1):
        g = span / 2 ** dpt
        for k in range(1, 2 ** dpt, 2):
            s = s0 + (s1 - s0) * k / 2 ** dpt
            out.extend(R.contour(s, u0, u1, minw=pitch / g))
    return out


def _shadow(cv, R, side, T, u0, u1):
    """A black shadow band along the `side` edge, up to T px deep at mid-span, built of 1 px lines
    0.8 px apart (solid on the panel), tapering at both ends."""
    def depth(u):
        if u <= u0 or u >= u1:
            return 0.
        return T * math.sin(PI * (u - u0) / (u1 - u0)) ** .8

    if T < .6:
        return
    # a 1.5 px line hugging the edge, then 1 px lines 1 px apart: solid, in few strokes
    cv.heavy(R.inset(side, lambda u: .75 if depth(u) >= .6 else None, u0, u1))
    d = 2.
    while d < T + .3:
        cv.line(R.inset(side, lambda u, dd=d: dd if depth(u) >= dd - .2 else None, u0, u1))
        d += .9


def _euler(x, y, ang, L, kfun, n):
    """A curve of length L from (x, y) heading ang (radians) with curvature kfun(u)."""
    ds = L / n
    pts = [(x, y)]
    a = ang
    for i in range(n):
        a += kfun((i + .5) / n) * ds
        x += math.cos(a) * ds
        y += math.sin(a) * ds
        pts.append((x, y))
    return pts


# ----------------------------------------------------------------------------------------------
# the swept finger and the frond: the Codex's acanthus
# ----------------------------------------------------------------------------------------------

_GN = sum(_smooth(.6, 1., (i + .5) / 50) ** 2 for i in range(50)) / 50


def _finger_geom(x, y, ang, length, width, bend, curl):
    n = max(18, int(length / 1.2))

    def k(u):
        return (bend + curl * _smooth(.6, 1., u) ** 2 / _GN) / length

    pts = _euler(x, y, ang, length, k, n)
    W = [width * 2.2 * (i / n) ** .45 * (1 - i / n) ** .9 * (1 - .4 * _smooth(.55, 1, i / n)) + .45
         for i in range(n + 1)]
    return pts, W


def _finger(cv, x, y, ang, length, width, bend, curl, dark=1., teeth=None):
    """One swept finger into cv (ang in radians): its outer edge cut into forward-pointing lobes."""
    pts, W = _finger_geom(x, y, ang, length, width, bend, curl)
    c = 1 if (bend + curl) >= 0 else -1
    n = len(W) - 1
    if teeth is None:
        teeth = max(0, min(4, int(length / 22)))
    ph = (x * 7.31 + y * 3.17) % 1. * .5
    Wv = []
    cuts = []
    for i in range(n + 1):
        u = i / n
        if teeth and .12 < u < .8:
            v = ((u - .12) / .68 * teeth + ph) % 1.
            Wv.append(W[i] * (.62 + .38 * v ** 1.4))
        else:
            Wv.append(W[i])
    if teeth:
        for j in range(1, teeth + 1):
            u = .12 + (j - ph) / teeth * .68
            if .14 < u < .78:
                cuts.append(u)
    R = _Rib(pts, W if c > 0 else Wv, Wv if c > 0 else W)
    cv.obj([R.outline()], 1.)
    cv.hair(_fill_lines(R, .04 * c, .98 * c, 1.5, .02, .995, 4))
    cv.hair(_fill_lines(R, -.02 * c, -.6 * c, 2., .04, .93, 2))
    _shadow(cv, R, c, min(3.2, max(W) * .5) * dark, .06, .88)
    L = R.L
    for u in cuts:
        cv.heavy([R.at(u + .004, -.98 * c), R.at(u + .03, -.55 * c), R.at(u + .07, -.25 * c)])
    u = .04
    while u < .3:
        if R.width(u, c) > 3:
            cv.hair([R.at(u, .1 * c), R.at(u + 2.5 / L, .9 * c)])
        u += 2.2 / L
    return R


def acanthus_finger(x, y, ang, length, width=None, bend=.9, curl=4.5, dark=1., cv=None):
    """One slender swept blade from (x, y) heading `ang` degrees, curving `bend` radians and
    rolling into a curl of `curl` radians at its tip (negative mirrors). Shaded along its form:
    dense and dark on the inside of the curve with a black under-shadow, a white highlight on the
    outside."""
    cv, own = _own(cv)
    _finger(cv, x, y, math.radians(ang), length, width or length * .1, bend, curl, dark)
    return cv.svg() if own else ""


def _frond(cv, x, y, ang, length, n=3, spread=.5, bend=.9, curl=4.5, width=None, rng=None, dark=1.):
    rng = rng or random.Random(0)
    width = width or length * .17
    sg = 1 if bend >= 0 else -1
    for i in sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2)):
        off = i - (n - 1) / 2
        _finger(cv, x, y, ang + off * spread, length * (1 - .18 * abs(off)) * rng.uniform(.93, 1.04),
                width * (1 - .12 * abs(off)), bend * (1 + .3 * off * sg) * rng.uniform(.9, 1.1),
                curl * rng.uniform(.85, 1.1), dark)


def acanthus_frond(x, y, ang, length, n=3, spread=28., bend=.9, curl=4.5, seed=0, width=None, cv=None):
    """An acanthus leaf as the Codex cuts it: n swept fingers fanning `spread` degrees from one root
    at (x, y) heading `ang` degrees, the middle one longest, every tip rolling the same way."""
    cv, own = _own(cv)
    _frond(cv, x, y, math.radians(ang), length, n, math.radians(spread), bend, curl, width, random.Random(seed))
    return cv.svg() if own else ""


acanthus_leaf = acanthus_frond


# ----------------------------------------------------------------------------------------------
# the volute
# ----------------------------------------------------------------------------------------------

def volute_spine(cx, cy, r, a0=180., turns=1.5, flip=False, tail=0., tail_bend=0., end=.13):
    """Centre line of a volute: a logarithmic spiral round (cx, cy) from radius r at angle a0
    (degrees, screen coordinates) winding `turns` times in to r*end; clockwise on screen unless
    flip. tail > 0 prepends a lead-in stem tail*r px long running back from the spiral's start
    along its tangent and curving by tail_bend radians. Points run from the root to the eye."""
    th = TAU * turns
    b = -math.log(end) / th
    sg = -1 if flip else 1
    n = max(40, int(r * th * .5))
    sp = []
    for i in range(n + 1):
        t = th * i / n
        rr = r * math.exp(-b * t)
        ph = math.radians(a0) + sg * t
        sp.append((cx + rr * math.cos(ph), cy + rr * math.sin(ph)))
    if tail > 0:
        L = tail * r
        dx, dy = sp[0][0] - sp[1][0], sp[0][1] - sp[1][1]
        back = _euler(sp[0][0], sp[0][1], math.atan2(dy, dx), L,
                      lambda u: sg * tail_bend * (1 - u) * 2 / L, max(8, int(L / 2)))
        sp = back[::-1][:-1] + sp
    return sp


def scroll_root(cx, cy, r, a0=180., turns=1.5, flip=False, tail=0., tail_bend=0.):
    """Where a volute's stem starts, and its heading there in degrees."""
    p = volute_spine(cx, cy, r, a0, turns, flip, tail, tail_bend)
    return p[0], math.degrees(math.atan2(p[1][1] - p[0][1], p[1][0] - p[0][0]))


def _lobe(v):
    vv = v ** .75
    bump = math.sin(PI * vv) ** .5
    f = bump * (.85 + .15 * ((3 * vv) % 1.) ** 2) if vv > .35 else bump
    return .3 + .74 * f


def _volute(cv, cx, cy, r, a0, turns, flip, rng, tail=0., tail_bend=0., stem=None, fronds=3,
            inner=True, leaf_scale=1., end=.13, blade=.3, frond_from=0.):
    pts = volute_spine(cx, cy, r, a0, turns, flip, tail, tail_bend, end)
    n = len(pts)
    i = n // 2
    a, b = pts[i - 1], pts[i + 1]
    ins = 1 if (-(b[1] - a[1])) * (cx - pts[i][0]) + (b[0] - a[0]) * (cy - pts[i][1]) > 0 else -1
    S = [0.]
    for k in range(1, n):
        S.append(S[-1] + math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]))
    tot = S[-1]
    W0 = stem or r * .15
    lob_len = .62 * r
    ph0 = rng.random() * .4
    ws, wb = [], []
    for k in range(n):
        u = S[k] / tot
        w = W0 * (1 - .6 * u ** 1.3) * (.15 + .85 * _smooth(0, .12, u))
        env = blade * r * _smooth(0, .18, u) * (1 - _smooth(.3, .72, u))
        ws.append(w)
        wb.append(max(w, env * _lobe((S[k] / lob_len + ph0) % 1.)))
    R = _Rib(pts, ws if ins > 0 else wb, wb if ins > 0 else ws)
    c = ins
    L = R.L
    # the body: a round-carved stem (inside of the curl) and a lobed blade outside it
    cv.obj([R.outline()], 1.)
    for s in (.3, .55, .75, .88):
        cv.hair(R.contour(s * c, 0., 1., minw=1.3 / max(.08, (1 - s) * .55)))
    _shadow(cv, R, c, W0 * .4, .0, 1.)
    for k, sv in enumerate((.1, .2, .3, .42)):
        cv.hair(R.contour(-sv * c, .03, .72 - .05 * k, minw=5 + 3 * k))
    lobes = tot / lob_len
    u = .02
    while u < .75:
        if R.width(u, -c) > 2.2:
            v = (u * lobes + ph0) % 1.
            reach = .95 - .6 * v if v <= .92 else .25
            cv.hair([R.at(u, -.02 * c), R.at(u + 2.4 / L, -reach * c)])
        u += 3. / L
    for j in range(int(lobes) + 2):
        un = (j - ph0) / lobes
        if .04 < un < .75 and R.width(un, -c) > 5:
            lu = 1 / lobes
            cv.heavy([R.at(un - lu * .02, -.98 * c), R.at(un + lu * .06, -.7 * c), R.at(un + lu * .12, -.42 * c)])
    # fronds springing from the outside, laid from the eye back so those nearer the root lie on top
    sg = ins
    spots = []
    u0 = .04 + frond_from * (tail * r) / tot
    u = u0
    while u < u0 + .56 and len(spots) < fronds:
        k = min(n - 2, int(u * (n - 1)))
        a, b = pts[max(0, k - 1)], pts[k + 1]
        ta = math.atan2(b[1] - a[1], b[0] - a[0])
        base = R.at(u, -ins * .5)
        rad = math.hypot(base[0] - cx, base[1] - cy)
        ll = min(r * 2.1, max(r * .85, rad * 1.9)) * leaf_scale * rng.uniform(.9, 1.06)
        spots.append((base, ta, ll, rad))
        u += ll * .45 / tot
    fr = []
    for base, ta, ll, rad in spots:
        sub = Canvas()
        _frond(sub, base[0], base[1], ta - sg * rng.uniform(.15, .3), ll, 3 if r > 30 else 2, .38,
               sg * (ll / max(rad, 1) * .6 + .25), -sg * rng.uniform(3.8, 5.), None, rng)
        fr.append(sub)
    for sub in fr[::-1]:
        cv.extend(sub)
    if inner:
        u = .55
        k = int(u * (n - 1))
        a, b = pts[k - 1], pts[k + 1]
        ta = math.atan2(b[1] - a[1], b[0] - a[0])
        base = R.at(u, ins * .4)
        ll = r * .85 * leaf_scale
        _finger(cv, base[0], base[1], ta + ins * .15, ll, ll * .14, ins * 1.6, ins * 4.5, 1.2)
    # the drilled eye
    ex, ey = pts[-1]
    rr = max(1.5, ws[-1] * .75)
    cv.obj([_ell_pts(ex, ey, rr + 1.2, rr + 1.2, 16)[:-1]], 0)
    q = rr - .4
    while q > .3:
        cv.line(_ell_pts(ex, ey, q, q, max(8, int(q * 6))))
        q -= .8
    cv.line([(ex - .3, ey), (ex + .3, ey)])


def acanthus_scroll(cx, cy, r, a0=180., turns=1.5, flip=False, seed=0, tail=0., tail_bend=0.,
                    stem=None, fronds=3, inner=True, leaf_scale=1., end=.13, blade=.3, cv=None):
    """A volute of shaded acanthus round (cx, cy): a round-carved stem (white highlight outside,
    black shadow inside) with a lobed blade, winding `turns` times from radius r at angle a0
    (degrees) into a tight curl that ends in a drilled black eye; fronds of swept fingers spring
    from its outside and roll their tips outward, and one finger rolls into the eye.
    tail adds a lead-in stem (tail*r px) curving by tail_bend radians, so volutes can grow from a
    root or from one another; flip mirrors the winding; seed varies the leafage."""
    cv, own = _own(cv)
    _volute(cv, cx, cy, r, a0, turns, flip, random.Random(seed), tail, tail_bend, stem, fronds, inner,
            leaf_scale, end, blade)
    return cv.svg() if own else ""


# ----------------------------------------------------------------------------------------------
# palmette
# ----------------------------------------------------------------------------------------------

def palmette(cx, cy, size, up=True, seed=0, n=2, cv=None):
    """A symmetric anthemion rising (or hanging) from (cx, cy), about `size` tall: n pairs of
    swept fingers curling outward and a tall centre pair, on a small ribbed calyx."""
    cv, own = _own(cv)
    rng = random.Random(seed)
    base = -PI / 2 if up else PI / 2
    sd = 1 if up else -1
    for j in range(n, 0, -1):
        for side in (-1, 1):
            sp = j / (n + .4)
            a = base + side * sp * 1.25 * sd
            ln = size * (1.05 - .28 * sp) * rng.uniform(.95, 1.03)
            b = side * (.5 + .6 * sp) * sd
            _finger(cv, cx + side * size * .05, cy, a, ln, ln * .12, b, b * 5.5)
    for side in (-1, 1):
        _finger(cv, cx + side * .5, cy, base - side * .05 * sd, size * 1.12, size * .1,
                side * .12 * sd, side * 3.6 * sd)
    r = size * .13
    cv.obj([_ell_pts(cx, cy, r * 1.6, r, 28)[:-1]], 1.)
    cv.hair(hatch_poly(_ell_pts(cx, cy + r * .3 * sd, r * 1.4, r * .55, 20)[:-1], 0, 1.5))
    return cv.svg() if own else ""


# ----------------------------------------------------------------------------------------------
# architectural members
# ----------------------------------------------------------------------------------------------

def knurled_bar(x, y, w, h):
    """A turned rod with rounded ends: a white highlight along the top, diagonal knurling, a black
    underside. h about 5-12 px. 4 elements."""
    r = h / 2
    body = (f"M{_n(x + r)},{_n(y)}h{_n(w - 2 * r)}a{_n(r)},{_n(r)} 0 0,1 0,{_n(h)}"
            f"h{_n(-(w - 2 * r))}a{_n(r)},{_n(r)} 0 0,1 0,{_n(-h)}z")
    k = f"M{_n(x + r * .6)},{_n(y + h * .36)}h{_n(w - r * 1.2)}v{_n(h * .4)}h{_n(-(w - r * 1.2))}z"
    sh = (f"M{_n(x + r * .5)},{_n(y + h * .76)}h{_n(w - r)}"
          f"a{_n(r)},{_n(r * .3)} 0 0,1 {_n(-r * .5)},{_n(h * .24 - .5)}h{_n(-(w - 2 * r))}"
          f"a{_n(r)},{_n(r * .3)} 0 0,1 {_n(-r * .5)},{_n(-(h * .24 - .5))}z")
    return (f'<path d="{body}" fill="#fff" stroke="#000" stroke-width="1"/>'
            f'<path d="{k}" fill="{pat("K")}" stroke="none"/>'
            f'<path d="{sh}" fill="#000" stroke="none"/>'
            f'<path d="M{_n(x + r)},{_n(y + h * .2)}h{_n(w - 2 * r)}" stroke="#000" stroke-width=".5"/>')


def bead_moulding(x, y, w, r=2.5, fillet=True):
    """A row of round beads (radius r) centred on y from x to x+w, fillet rules above and below;
    each bead white with a black crescent lower right. One pattern tile: 3-4 elements."""
    r = max(1., round(r * 2) / 2)
    pitch = 2 * r + 1
    th = 2 * r + 1
    rr, r2 = _n(r), _n(2 * r)
    cx, cy = pitch / 2, th / 2
    p0 = (cx + r * math.cos(-.35), cy + r * math.sin(-.35))
    p1 = (cx + r * math.cos(2.0), cy + r * math.sin(2.0))
    k = r * .55
    pid = f"{_PID}B{int(r * 10)}"
    tile = (f'<path d="M{_n(cx - r)},{_n(cy)}a{rr},{rr} 0 1,0 {r2},0a{rr},{rr} 0 1,0 -{r2},0z" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="M{_n(p0[0])},{_n(p0[1])}A{rr},{rr} 0 0,1 {_n(p1[0])},{_n(p1[1])}'
            f'A{_n(k * 1.6)},{_n(k * 1.3)} 0 0,0 {_n(p0[0])},{_n(p0[1])}z" fill="#000"/>')
    o = (f'<defs><pattern id="{pid}" x="{_n(x)}" y="{_n(y - th / 2)}" width="{_n(pitch)}" height="{_n(th)}" '
         f'patternUnits="userSpaceOnUse">{tile}</pattern></defs>'
         f'<path d="M{_n(x)},{_n(y - th / 2)}h{_n(w)}v{_n(th)}h{_n(-w)}z" fill="url(#{pid})" stroke="none"/>')
    if fillet:
        o += (f'<path d="M{_n(x)},{_n(y - r - 1.5)}h{_n(w)}M{_n(x)},{_n(y + r + 1.5)}h{_n(w)}" '
              f'stroke="#000" stroke-width="1"{_CR}/>')
    return o


def egg_and_dart(x, y, w, h):
    """An ovolo moulding in the band y..y+h: white eggs in hatched shells alternating with black
    darts, a fillet above and a bead row below. One pattern tile: about 6 elements."""
    bh = h * .72
    pitch = max(4., round(bh * 1.1 * 2) / 2)
    top = 1.
    rx, ry = pitch * .46, bh * .58
    cx = pitch / 2
    ex, ey = rx * .68, ry * .8
    hx, hy = ex * .7, ey * .8
    pid = f"{_PID}E{int(pitch * 10)}x{int(bh * 10)}"
    tile = (f'<path d="M0,0h{_n(pitch)}v{_n(bh + 1)}h{_n(-pitch)}z" fill="{pat("X")}"/>'
            f'<path d="M{_n(cx - rx)},{_n(top)}A{_n(rx)},{_n(ry)} 0 0,0 {_n(cx + rx)},{_n(top)}z" fill="#fff" stroke="#000" stroke-width=".5"/>'
            f'<path d="M{_n(cx - ex)},{_n(top)}A{_n(ex)},{_n(ey)} 0 0,0 {_n(cx + ex)},{_n(top)}z" fill="#fff" stroke="#000" stroke-width="1"/>'
            f'<path d="M{_n(cx + hx * .2)},{_n(top + 1)}A{_n(hx)},{_n(hy)} 0 0,1 {_n(cx - hx * .5)},{_n(top + hy * .9)}" stroke="#000" stroke-width=".5" fill="none"/>'
            f'<path d="M0,{_n(top)}h1.2L0,{_n(top + bh * .85)}zM{_n(pitch)},{_n(top)}h-1.2L{_n(pitch)},{_n(top + bh * .85)}z" fill="#000"/>')
    o = (f'<defs><pattern id="{pid}" x="{_n(x)}" y="{_n(y)}" width="{_n(pitch)}" height="{_n(bh + 1)}" '
         f'patternUnits="userSpaceOnUse">{tile}</pattern></defs>'
         f'<path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(bh + 1)}h{_n(-w)}z" fill="url(#{pid})" stroke="none"/>')
    o += f'<path d="M{_n(x)},{_n(y + .5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>'
    o += bead_moulding(x, y + bh + (h - bh) / 2 + .5, w, max(1., (h - bh) / 2 - 1.), fillet=False)
    return o


def pedestal(x, y, w, h, seed=0):
    """The reference's base, filling x..x+w, y..y+h: a knurled cornice; a slab whose top is lightly
    ruled in perspective and whose front face is ruled mid-tone round a sunk blank tablet (for path
    lettering) flanked by rosettes; a second knurled bar; a flared plinth over a bead row.
    Returns (svg, (tx, ty, tw, th)), the tablet."""
    o = []
    kb = max(5, min(10, h * .11))
    inset = w * .035
    o.append(knurled_bar(x, y, w, kb))
    yy = y + kb
    slab = h * .42
    top = slab * .22
    o.append(f'<path d="M{_n(x + inset)},{_n(yy)}h{_n(w - 2 * inset)}v{_n(slab)}h{_n(-(w - 2 * inset))}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="M{_n(x + inset)},{_n(yy)}h{_n(w - 2 * inset)}l{_n(-inset * .5)},{_n(top)}'
             f'h{_n(-(w - 3 * inset))}z" fill="{pat("L")}" stroke="#000" stroke-width=".5"/>')
    fy = yy + top
    fh = slab - top
    o.append(f'<path d="M{_n(x + inset * 1.5)},{_n(fy)}h{_n(w - 3 * inset)}v{_n(fh)}'
             f'h{_n(-(w - 3 * inset))}z" fill="{pat("M")}" stroke="#000" stroke-width="1"/>')
    th = fh * .6
    tw = w * .56
    tx, ty = x + (w - tw) / 2, fy + (fh - th) / 2
    o.append(f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(tx + .5)},{_n(ty + .5)}h{_n(tw - 1)}l-1.5,1.5h{_n(-(tw - 4))}v{_n(th - 4)}l-1.5,1.5z" fill="#000" stroke="none"/>')
    for sx in (-1, 1):
        rx = x + w / 2 + sx * (tw / 2 + (w - 3 * inset - tw) / 4)
        rcy = fy + fh / 2
        rr = min(fh * .32, 9)
        o.append(f'<path d="{_d(_ell_pts(rx, rcy, rr, rr, 24), True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        petals = "".join(_d([(rx, rcy), (rx + rr * .9 * math.cos(a + .25), rcy + rr * .9 * math.sin(a + .25)),
                             (rx + rr * .9 * math.cos(a - .25), rcy + rr * .9 * math.sin(a - .25))], True, 0)
                         for a in [TAU * i / 8 for i in range(8)])
        o.append(f'<path d="{petals}" fill="{pat("D")}" stroke="#000" stroke-width=".5"/>')
        o.append(f'<path d="{_d(_ell_pts(rx, rcy, rr * .25, rr * .25, 10), True, 0)}" fill="#000"/>')
    yy = fy + fh
    o.append(knurled_bar(x + inset * .4, yy, w - inset * .8, kb))
    yy += kb
    ph = y + h - yy
    if ph > 6:
        fl = [(x + inset * 1.2 - inset * 1.1 * (i / 12) ** 2.2, yy + ph * .7 * i / 12) for i in range(13)]
        fr = [(2 * x + w - p[0], p[1]) for p in fl[::-1]]
        o.append(f'<path d="{_d(fl + fr, True, 0)}" fill="{pat("V")}" stroke="none"/>')
        o.append(f'<path d="{_d(fl, tol=0)}{_d(fr, tol=0)}" stroke="#000" stroke-width="1"/>')
        o.append(bead_moulding(x + inset * .1, yy + ph * .85, w - inset * .2, max(1., ph * .12)))
    return "".join(o), (tx, ty, tw, th)


# ----------------------------------------------------------------------------------------------
# ribbon banner
# ----------------------------------------------------------------------------------------------

def ribbon_banner(cx, cy, w, h, arch=.06, seed=0):
    """A curling ribbon: a face h tall spanning about w, arched by arch*w (negative sags), that
    folds behind at each end into a shaded, swallow-tailed tail curling back and down. No
    lettering. Returns (svg, face_centre_points) for callers who letter it with paths."""
    cv = Canvas()
    face_w = w * .7
    n = 40
    centre = [(cx - face_w / 2 + face_w * i / n, cy - arch * w * math.sin(PI * i / n)) for i in range(n + 1)]
    R = _Rib(centre, [h / 2] * (n + 1), [h / 2] * (n + 1))
    for side in (-1, 1):
        e = centre[0] if side < 0 else centre[-1]
        e2 = centre[1] if side < 0 else centre[-2]
        ang = math.atan2(e[1] - e2[1], e[0] - e2[0])
        tl = (w - face_w) / 2 + h * .5
        sx, sy = e[0] - side * h * .5, e[1] + h * .55
        tp = _euler(sx, sy, ang + side * .2, tl, lambda u, sd=side: -sd * 2.2 * _smooth(.45, 1, u) / tl, 26)
        T = _Rib(tp, [h * .46] * len(tp), [h * .46] * len(tp))
        ol = T.outline()
        tip = tp[-1]
        a = math.atan2(tp[-1][1] - tp[-2][1], tp[-1][0] - tp[-2][0])
        notch = (tip[0] - math.cos(a) * h * .5, tip[1] - math.sin(a) * h * .5)
        k = len(ol) // 2
        ol = ol[:k] + [notch] + ol[k:]
        cv.obj([ol], 1.)
        for s in (-.72, -.42, -.14, .14, .42, .72):
            cv.hair(T.contour(s, 0., .9))
        cv.hair(hatch_poly([T.at(0, 1), T.at(0, -1), T.at(.3, -1), T.at(.3, 1)], 45 * side, 1.5))
        p0, p1 = R.at(0 if side < 0 else 1, 1), R.at(0 if side < 0 else 1, -1)
        fold = [p0, p1, T.at(0, -1), T.at(0, 1)]
        if _area(fold) * _area([p0, p1, T.at(0, 1), T.at(0, -1)]) > 0 and abs(_area(fold)) < abs(_area([p0, p1, T.at(0, 1), T.at(0, -1)])):
            fold = [p0, p1, T.at(0, 1), T.at(0, -1)]
        cv.obj([fold], 1.)
        cv.line(hatch_poly(fold, -45 * side, 1.5, inset=.3))
    cv.obj([R.outline()], 1.)
    for s in (.84, .7, -.7, -.84):
        cv.hair(R.contour(s, 0., 1.))
    _shadow(cv, R, -1, h * .14, 0., 1.)
    return cv.svg(), centre


# ----------------------------------------------------------------------------------------------
# cartouche
# ----------------------------------------------------------------------------------------------

def _superellipse(cx, cy, a, b, e=2.6, n=96):
    pts = []
    for i in range(n):
        t = TAU * i / n
        c, s = math.cos(t), math.sin(t)
        pts.append((cx + a * math.copysign(abs(c) ** (2 / e), c), cy + b * math.copysign(abs(s) ** (2 / e), s)))
    return pts


def _ring_line(cx, cy, a, b):
    p = _superellipse(cx, cy, a, b)
    return _d(p + [p[0]], tol=.15)


def cartouche(cx, cy, w, h, seed=0, scrolls=False, crest=False):
    """A carved cartouche about w x h at (cx, cy): a convex moulding (contoured, with a black sunk
    fillet and a bead row) round a white field; optionally volutes breaking out at the four corners
    and a palmette crest above / pendant below.
    Returns (svg, (ix, iy, iw, ih), inner_path_d): the largest clear rectangle in the field, and
    the field's outline (use it in a clipPath to fill the whole field)."""
    rng = random.Random(seed)
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    o = []
    if scrolls:
        cv = Canvas()
        for sx in (-1, 1):
            for sy in (-1, 1):
                rr = min(w, h) * .2
                _volute(cv, cx + sx * (a + bw * .4), cy + sy * b * .55, rr, 90 * sy, 1.3, sx * sy > 0,
                        random.Random(rng.randrange(1 << 20)), fronds=2)
        o.append(cv.svg())
    outer = _superellipse(cx, cy, a + bw, b + bw)
    inner = _superellipse(cx, cy, a, b)
    o.append(f'<path d="{_d(inner, True, .1)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_d(outer, True, .1)}{_d(inner[::-1], True, .1)}" fill="#fff" stroke="#000" stroke-width="1" fill-rule="evenodd"/>')
    o.append(f'<path d="{"".join(_ring_line(cx, cy, a + bw * f, b + bw * f) for f in (.62, .74, .86))}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(_ring_line(cx, cy, a + bw * f, b + bw * f) for f in (.42,))}" fill="none" stroke="#000" stroke-width="1"/>')
    sunk = _d(_superellipse(cx, cy, a + bw * .26, b + bw * .26), True, .1) + _d(inner[::-1], True, .1)
    o.append(f'<path d="{sunk}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    bp = _superellipse(cx, cy, a - 3.2, b - 3.2)
    o.append(f'<path d="{_d(bp + [bp[0]], tol=.15)}" fill="none" stroke="#000" stroke-width="1.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')

    if crest:
        size = min(w * .2, h * .28)
        o.append(palmette(cx, cy - b - bw * .6, size, True, rng.randrange(1 << 20)))
        o.append(palmette(cx, cy + b + bw * .6, size * .7, False, rng.randrange(1 << 20)))
    k = 2 ** (-1 / 2.6)
    ia, ib = (a - 6) * k, (b - 6) * k
    return "".join(o), (cx - ia, cy - ib, 2 * ia, 2 * ib), _d(inner, True, 0)


# ----------------------------------------------------------------------------------------------
# running scrolls, bands, columns
# ----------------------------------------------------------------------------------------------

def running_scroll(x0, y0, ang, length, breadth, seed=0, mirror=False, n=None, r_scale=1., turns=1.35,
                   first_down=True, fronds=3, cv=None):
    """A rinceau: volutes rising one from another's tail along a line from (x0, y0) heading `ang`
    degrees for `length` px, in a band `breadth` px across centred on the line, curling alternately
    to either side. mirror reverses the winding (the left-hand copy of a symmetric pair).
    n units (default: as many as fit with r about breadth * .4). Units are painted far end first."""
    cv, own = _own(cv)
    rng = random.Random(seed)
    th = math.radians(ang)
    dx, dy = math.cos(th), math.sin(th)
    nx, ny = (dy, -dx) if mirror else (-dy, dx)
    r = breadth * .4 * r_scale
    if n is None:
        n = max(1, int(round(length / (r * 2.35))))
    P = length / n
    r = min(r, P * .46)
    units = []
    for i in range(n):
        down = (i % 2 == 0) == first_down
        off = (.12 if down else -.12) * breadth
        along = P * (i + .62)
        a0, flip = (-90, False) if down else (90, True)
        if mirror:
            a0, flip = -a0, not flip
        tb = .9 if down else -.9
        units.append((x0 + dx * along + nx * off, y0 + dy * along + ny * off, a0 + ang, flip, tb,
                      rng.randrange(1 << 20)))
    for cx, cy, a0, flip, tb, sd in units[::-1]:
        _volute(cv, cx, cy, r, a0, turns, flip, random.Random(sd), (P * .55) / r, tb, r * .15,
                fronds if r > 22 else min(fronds, 2))
    return cv.svg() if own else ""


def scroll_band(x, y, w, h, seed=0, center_gap=0., cv=None, r_scale=1., n=None):
    """A frieze of interlocking shaded acanthus volutes filling x..x+w, y..y+h exactly, flowing from
    the centre out to both ends (mirrored) and curling alternately up and down, with `center_gap`
    px left clear in the middle for a motif."""
    cv, own = _own(cv)
    half = (w - center_gap) / 2
    cy = y + h / 2
    running_scroll(x + w / 2 + center_gap / 2, cy, 0, half, h, seed, False, n=n, r_scale=r_scale, cv=cv)
    running_scroll(x + w / 2 - center_gap / 2, cy, 180, half, h, seed, True, n=n, r_scale=r_scale, cv=cv)
    return cv.svg() if own else ""


def scroll_column(x, y, w, h, seed=0, upward=True, mirror=False, cv=None):
    """A vertical rinceau filling x..x+w, y..y+h, flowing up (or down)."""
    if upward:
        return running_scroll(x + w / 2, y + h, -90, h, w, seed, mirror, cv=cv)
    return running_scroll(x + w / 2, y, 90, h, w, seed, mirror, cv=cv)


# ----------------------------------------------------------------------------------------------
# space filling: grow volutes into whatever ground is left
# ----------------------------------------------------------------------------------------------

def _shape_dist(px, py, sh):
    if sh[0] == "c":
        return math.hypot(px - sh[1], py - sh[2]) - sh[3]
    _, x0, y0, x1, y1 = sh
    dx = max(x0 - px, 0., px - x1)
    dy = max(y0 - py, 0., py - y1)
    if dx == 0 and dy == 0:
        return -min(px - x0, x1 - px, py - y0, y1 - py)
    return math.hypot(dx, dy)


def fill_scrolls(x, y, w, h, occupied, seed=0, rmin=10., rmax=80., max_n=12, edge=.6, grid=5.,
                 fronds=2, cv=None):
    """Grow volutes into the free ground of the box until no gap of radius about rmin is left.
    occupied: ('c', cx, cy, r) circles and ('r', x0, y0, x1, y1) rects already filled; extended in
    place. Each new volute is sized to its gap, springs by its tail from its nearest neighbour and
    winds away from it. edge < 1 lets volutes run off the box edges (clip, or let them break out).
    Volutes are painted smallest first, so they tuck under their larger neighbours."""
    cv, own = _own(cv)
    rng = random.Random(seed)
    nx, ny = max(2, int(w / grid)), max(2, int(h / grid))
    pts = [(x + (i + .5) * w / nx, y + (j + .5) * h / ny) for j in range(ny) for i in range(nx)]
    near = [None] * len(pts)
    dist = []
    for k, (px, py) in enumerate(pts):
        best = 1e9
        for sh in occupied:
            d = _shape_dist(px, py, sh)
            if d < best:
                best, near[k] = d, sh
        dist.append(min(best, min(px - x, x + w - px, py - y, y + h - py) / edge))
    made = []
    for it in range(max_n):
        k = max(range(len(pts)), key=dist.__getitem__)
        free = dist[k]
        if free < rmin * 1.1:
            break
        px, py = pts[k]
        r = min(rmax, free / 1.1) * rng.uniform(.92, 1.)
        sh = near[k]
        if sh is not None:
            if sh[0] == "c":
                bx, by = sh[1], sh[2]
            else:
                bx, by = min(max(px, sh[1]), sh[3]), min(max(py, sh[2]), sh[4])
            beta = math.degrees(math.atan2(by - py, bx - px))
            gap = max(0., _shape_dist(px, py, sh) - r * .9)
        else:
            beta, gap = rng.uniform(0, 360), 0.
        flip = rng.random() < .5
        a0 = beta - 90 if flip else beta + 90
        made.append((r, px, py, a0, flip, min(1.4, (gap + r * .35) / r), rng.randrange(1 << 20)))
        newc = ("c", px, py, r * 1.08)
        occupied.append(newc)
        for j, (qx, qy) in enumerate(pts):
            d = math.hypot(qx - px, qy - py) - r * 1.08
            if d < dist[j]:
                dist[j], near[j] = d, newc
    for r, px, py, a0, flip, tail, sd in sorted(made):
        _volute(cv, px, py, r, a0, 1.35, flip, random.Random(sd), tail, .6 if flip else -.6, r * .15, fronds)
    return cv.svg() if own else ""


def apron(x, y, w, h, seed=0, cv=None):
    """The reference's foot: a palmette hanging from the middle of the top edge and, flowing out
    from it to both ends, a pair of interlocking volutes each side, on the paper (no ground), so the
    plate finishes in scroll tips rather than a hard edge. Fills x..x+w, y..y+h."""
    cv, own = _own(cv)
    rng = random.Random(seed)
    gap = h * 1.1
    scroll_band(x, y + h * .04, w, h * .92, rng.randrange(1 << 20), gap, cv=cv, r_scale=1.15, n=2)
    palmette(x + w / 2, y + 2, h * .85, False, rng.randrange(1 << 20), cv=cv)
    return cv.svg() if own else ""


# ----------------------------------------------------------------------------------------------
# reference composition
# ----------------------------------------------------------------------------------------------

def _placeholder(x, y, w, h):
    return ""


def frame_plate(w, h, seed=0, fill_fn=None, density=1.):
    """A complete house plate filling w x h edge to edge (w 550-570, h 50-560). By height:
      h < 110  : a bead moulding hangs under the text; a cut-away ground carries a frieze of
                 interlocking volutes flowing out of a small central medallion (fill_fn fills it);
      110-260  : an egg-and-dart moulding hangs on top; ground; a carved cartouche (fill_fn) with big
                 volutes flowing out to both ends, the gaps grown full of smaller ones; knurled foot;
      > 260    : a palmette crest and volute tips rise free above a double-ruled panel; ground; a
                 large cartouche (fill_fn) between mirrored pairs of volutes, the rest grown full; a
                 ribbon banner across its foot; a pedestal; a scroll frieze below it.
    fill_fn(x, y, w, h) -> SVG fragment for the bespoke vignette. Returns the full <svg>.
    density (0-1) scales how many filler volutes grow into the ground: lower it to leave bytes for
    a heavy vignette. The frame alone is about 30-36 KB short, 44-52 KB medium, 75-112 KB tall;
    density < .9 also drops the tall plate's scroll frieze under the pedestal (about -12 KB).
    The vignette box is white; anything the vignette draws stays inside it."""
    fill_fn = fill_fn or _placeholder
    if h < 110:
        body = _layout_band(w, h, seed, fill_fn)
    elif h <= 260:
        body = _layout_medium(w, h, seed, fill_fn, density)
    else:
        body = _layout_tall(w, h, seed, fill_fn, density)
    return svg_doc(w, h, body)


def _medallion(cx, cy, rx, ry):
    ring = _d(_ell_pts(cx, cy, rx + 1, ry + 1, 64), True) + _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    return (f'<path d="{_d(_ell_pts(cx, cy, rx + 1, ry + 1, 64), True)}" fill="#fff" stroke="none"/>'
            f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>'
            f'<path d="{_d(_ell_pts(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')


def _layout_band(w, h, seed, fill_fn):
    o = []
    top = 7.
    o.append(bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(_clip(_uid("b", w, h, seed), 0, top, w, gh, scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(_medallion(cx, cy, rx, ry))
    k = .7071
    o.append(fill_fn(cx - (rx - 5) * k, cy - (ry - 5) * k, (rx - 5) * 2 * k, (ry - 5) * 2 * k))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def _pair_unit(cv, cx, cy, r, side, rng, a_out=0., turns=1.4, tail=.9, up=True, fronds=3):
    """One volute of a mirrored pair (side -1 left, +1 right) winding outward from the centre.
    up: its stem rises from below and curls over outward; else it hangs from above."""
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    _volute(cv, cx, cy, r, a0, turns, flip, rng, tail, -.5 if up else .5, r * .15, fronds)


def _layout_medium(w, h, seed, fill_fn, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .4, gh * 1.45)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                 max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), _ = cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(fill_fn(ix, iy, iw, ih))
    o.append(knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, fill_fn, density=1.):
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
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        _pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                 max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), _ = cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(fill_fn(ix, iy, iw, ih))
    o.append(palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bsvg, _ = ribbon_banner(cx, cy + ch * .47, cw * 1.4, min(16, ph * .05), .04, rng.randrange(1 << 20))
    o.append(bsvg)
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, _ = pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(_clip(_uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                       scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                   r_scale=1.15, n=2)))
        o.append(palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)
