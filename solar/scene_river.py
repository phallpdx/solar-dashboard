"""Engraved scene: the Columbia River at Sauvie Island (Kindle Evening Edition).

    scene(w, h, seed=0, variant="dusk", moon_phase=0.5, **kw) -> str

Returns SVG child markup only (no outer <svg>, no frame) that fills a w x h box edge to edge;
the caller clips it into an oval or rectangular cartouche and thresholds it to 1-bit at 2x.

Subject: a great blue heron in the shallows, a container ship mid-river, Mt Hood on the horizon,
Douglas firs on the near bank, cattails drawn leaf by leaf, stones, a driftwood log, a jumping
fish ring, a pair of crossed drumsticks lying on the bank, the moon at its phase (0 new, 0.5 full,
lit on the right while waxing) and its shimmer path. Variants: "dusk" (low moon, lighter sky),
"night" (stars, high moon), "goodnight" (night plus a dog curled asleep on the bank).

Method (Victorian wood/steel engraving): every region has a tone field modelled by the moon; the
tone is cut in layers by _engrave: a first course of long lines that wander together and swell
with the tone, then crossed courses in the darks; faint tone breaks into tapering dashes. Clouds
are a density field lit on the rims facing the moon. Darks keep drawn detail in white line (grass
on the bank, stars). Figures (heron, dog, ship, leaves, stones) are paper-white knock-outs with
their own contour work. Stroke widths are multiples of 0.5 px, minimum line and gap 0.5 px;
no transforms, filters, masks or gradients. Deterministic for a seed. Standard library only.
"""
import math
import random

__all__ = ["scene"]


# ------------------------------------------------------------------ numbers and noise
def _n(v):
    s = "%.1f" % v
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return "0" if s in ("-0", "-", "") else s


def _clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def _smooth(e0, e1, x):
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    t = _clamp((x - e0) / float(e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _hash(i, j, s):
    h = (i * 374761393 + j * 668265263 + s * 974711 + 12345) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _vn(x, y, s):
    """Smooth value noise in 0..1."""
    xi, yi = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - xi, y - yi
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a, b = _hash(xi, yi, s), _hash(xi + 1, yi, s)
    c, d = _hash(xi, yi + 1, s), _hash(xi + 1, yi + 1, s)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def _cr(P, n=6):
    """Catmull-Rom curve through the points P."""
    out = []
    m = len(P)
    for i in range(m - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(m - 1, i + 2)]
        for k in range(n):
            t = k / float(n)
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                       + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(tuple(P[-1]))
    return out


def _resample(pts, m):
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    tot = L[-1] or 1.0
    out, j = [], 0
    for k in range(m):
        d = tot * k / float(m - 1)
        while j < len(pts) - 2 and L[j + 1] < d:
            j += 1
        seg = (L[j + 1] - L[j]) or 1.0
        t = _clamp((d - L[j]) / seg, 0.0, 1.0)
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    return out


def _inside(poly, x, y):
    c, j = False, len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def _sweep(cen, wf):
    """Left and right edges of a stroke of full width wf(t) along the centre line cen."""
    L, R = [], []
    n = len(cen)
    for i, (x, y) in enumerate(cen):
        xa, ya = cen[max(0, i - 1)]
        xb, yb = cen[min(n - 1, i + 1)]
        dl = math.hypot(xb - xa, yb - ya) or 1.0
        nx, ny = -(yb - ya) / dl, (xb - xa) / dl
        hw = wf(i / (n - 1.0)) * 0.5
        L.append((x + nx * hw, y + ny * hw))
        R.append((x - nx * hw, y - ny * hw))
    return L, R


def _interp(tab, x):
    """Piecewise-linear lookup in [(x, y), ...] sorted by x."""
    if x <= tab[0][0]:
        return tab[0][1]
    for i in range(1, len(tab)):
        if x <= tab[i][0]:
            x0, y0 = tab[i - 1]
            x1, y1 = tab[i]
            return y0 + (y1 - y0) * (x - x0) / float((x1 - x0) or 1.0)
    return tab[-1][1]


# ------------------------------------------------------------------ the burin
class _B(dict):
    def __missing__(self, k):
        v = self[k] = []
        return v


class _Ink(object):
    def __init__(self):
        self.out = []
        self.b = _B()
        self.dots = []
        self.box = (1e9, 1e9)

    def seg(self, w, x0, y0, x1, y1):
        bx, by = self.box
        if (x0 < 0 and x1 < 0) or (x0 > bx and x1 > bx) or (y0 > by and y1 > by) or (y0 < 0 and y1 < 0):
            return
        if x0 > bx or x1 > bx or x0 < 0 or x1 < 0:
            if abs(x1 - x0) > 0.01:
                sl = (y1 - y0) / (x1 - x0)
                if x0 > bx:
                    x0, y0 = bx, y0 + sl * (bx - x0)
                if x1 > bx:
                    x1, y1 = bx, y1 + sl * (bx - x1)
                if x0 < 0:
                    x0, y0 = 0.0, y0 - sl * x0
                if x1 < 0:
                    x1, y1 = 0.0, y1 - sl * x1
        if abs(y1 - y0) < 0.05:
            if abs(x1 - x0) < 0.05:
                return
            self.b[w].append("M%s %sh%s" % (_n(x0), _n(y0), _n(x1 - x0)))
        elif abs(x1 - x0) < 0.05:
            self.b[w].append("M%s %sv%s" % (_n(x0), _n(y0), _n(y1 - y0)))
        else:
            self.b[w].append("M%s %sl%s %s" % (_n(x0), _n(y0), _n(x1 - x0), _n(y1 - y0)))

    @staticmethod
    def _d(pts, close=False):
        px, py = round(pts[0][0], 1), round(pts[0][1], 1)
        d = ["M%s %sl" % (_n(px), _n(py))]
        parts = []
        for x, y in pts[1:]:
            dx, dy = round(x - px, 1), round(y - py, 1)
            if dx == 0 and dy == 0:
                continue
            parts.append("%s %s" % (_n(dx), _n(dy)))
            px, py = round(px + dx, 1), round(py + dy, 1)
        if not parts:
            return ""
        return d[0] + " ".join(parts) + ("z" if close else "")

    def poly(self, w, pts, close=False):
        d = self._d(pts, close)
        if d:
            self.b[w].append(d)

    def swell(self, pts, fn):
        """A stroke whose weight swells along its length: fn(t) -> wanted width, cut in .5/1/1.5."""
        n = len(pts)
        if n < 2:
            return
        ws = []
        for i in range(n - 1):
            k = int(round(fn((i + 0.5) / (n - 1)) * 2))
            ws.append(_clamp(k, 1, 3) * 0.5)
        i = 0
        while i < n - 1:
            j = i
            while j + 1 < n - 1 and ws[j + 1] == ws[i]:
                j += 1
            self.poly(ws[i], pts[i:j + 2])
            i = j + 1

    def ticks(self, w, segs):
        """Many short strokes as one chained sub-path."""
        out, px, py = [], None, None
        for x0, y0, x1, y1 in segs:
            x0, y0, x1, y1 = round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)
            if x0 == x1 and y0 == y1:
                continue
            if px is None:
                out.append("M%s %s" % (_n(x0), _n(y0)))
            else:
                out.append("m%s %s" % (_n(x0 - px), _n(y0 - py)))
            out.append("l%s %s" % (_n(x1 - x0), _n(y1 - y0)))
            px, py = x1, y1
        if out:
            self.b[w].append("".join(out))

    def raw(self, w, d):
        self.b[w].append(d)

    def dot(self, x, y):
        self.dots.append("M%s %sh.1" % (_n(x), _n(y)))

    def flush(self):
        for w in sorted(self.b):
            if self.b[w]:
                self.out.append('<path stroke-width="%s" d="%s"/>' % (_n(w), "".join(self.b[w])))
        self.b = _B()
        if self.dots:
            self.out.append('<path stroke-width="1" stroke-linecap="round" d="%s"/>' % "".join(self.dots))
            self.dots = []

    def white(self, w, d, cap=False):
        """White-line work: a stroke cut out of the tone already laid down."""
        self.flush()
        if d:
            self.out.append('<path stroke="#fff" stroke-width="%s"%s d="%s"/>'
                            % (_n(w), ' stroke-linecap="round"' if cap else "", d))

    def mask(self, pts, w=None):
        """Paper-white shape under a foreground figure, optionally with its outline."""
        self.flush()
        d = self._d(pts, True)
        if d:
            st = 'stroke="none"' if w is None else 'stroke-width="%s"' % _n(w)
            self.out.append('<path fill="#fff" %s d="%s"/>' % (st, d))


def _q(t, pitch, i, x, seed):
    """Tone 0..1 at a ruling pitch -> line weight 0, .5, 1 or 1.5, dithered line to line."""
    ideal = t * pitch * 2.0
    thr = (i * 0.618034 + 0.3 * _vn(x / 31.0, i * 0.61, seed + 7)) % 1.0
    k = int(ideal + thr * 0.9 + 0.05)
    return _clamp(k, 0, 3) * 0.5


def _runs(ws):
    """[(i0, i1, w)] from a list of sampled weights, single-sample flickers removed."""
    n = len(ws)
    for i in range(1, n - 1):
        if ws[i] != ws[i - 1] and ws[i] != ws[i + 1]:
            ws[i] = ws[i - 1]
    out, i = [], 0
    while i < n:
        j = i
        while j + 1 < n and ws[j + 1] == ws[i]:
            j += 1
        if ws[i] > 0:
            out.append((i, j + 1, ws[i]))
        i = j + 1
    return out


def _rule_h(ink, lines, x0, x1, tfn, seed, step=3.0):
    """Horizontal ruling. lines = [(y, pitch)]; tfn(x, y) -> tone 0..1 (or < 0 for no line)."""
    n = max(1, int(math.ceil((x1 - x0) / step)))
    for i, (y, pitch) in enumerate(lines):
        ws = []
        for k in range(n):
            x = x0 + (k + 0.5) * step
            t = tfn(x, y)
            ws.append(0 if t <= 0 else _q(t, pitch, i, x, seed))
        last = {}
        for a, b, wd in _runs(ws):
            xa, xb = x0 + a * step, min(x1, x0 + b * step)
            yy = y + (0.5 if wd == 1.0 else 0.3)
            if wd in last:
                ink.b[wd].append("m%s 0h%s" % (_n(xa - last[wd]), _n(xb - xa)))
            else:
                ink.b[wd].append("M%s %sh%s" % (_n(xa), _n(yy), _n(xb - xa)))
            last[wd] = xb


class _Grid(object):
    """A tone function sampled once on a grid, so several layers of line can read it cheaply."""

    def __init__(self, fn, x0, y0, x1, y1, cell=2.0):
        self.x0, self.y0, self.c = x0, y0, cell
        self.nx = int((x1 - x0) / cell) + 2
        self.ny = int((y1 - y0) / cell) + 2
        self.g = [[fn(x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell) for i in range(self.nx)] for j in range(self.ny)]

    def __call__(self, x, y):
        i = int((x - self.x0) / self.c)
        j = int((y - self.y0) / self.c)
        if i < 0 or j < 0 or i >= self.nx or j >= self.ny:
            return -1
        return self.g[j][i]


def _bgrid(fn, x0, y0, x1, y1, cell):
    """Sample fn on a grid once; return a fast bilinear lookup."""
    nx = int((x1 - x0) / cell) + 3
    ny = int((y1 - y0) / cell) + 3
    g = [[fn(x0 + i * cell, y0 + j * cell) for i in range(nx)] for j in range(ny)]

    def f(x, y):
        fx = (x - x0) / cell
        fy = (y - y0) / cell
        fx = 0.0 if fx < 0 else (nx - 1.001 if fx > nx - 1.001 else fx)
        fy = 0.0 if fy < 0 else (ny - 1.001 if fy > ny - 1.001 else fy)
        i = int(fx)
        j = int(fy)
        a = fx - i
        b = fy - j
        r0 = g[j]
        r1 = g[j + 1]
        return (r0[i] * (1 - a) + r0[i + 1] * a) * (1 - b) + (r1[i] * (1 - a) + r1[i + 1] * a) * b
    return f


def _engrave(ink, box, grid, layers, seed, inside=None):
    """Lay tone the way a burin does: a first course of long, slightly wandering lines whose weight
    swells with the tone, then further courses crossing it where the tone deepens. Each layer is a
    dict: ang (deg), pitch (px or fn(v)), lo (tone where it starts), gain (half-px per unit tone),
    cap (max half-px), A / lam (wander amplitude and length), warp(s, v) (optional form-following)."""
    x0, y0, x1, y1 = box
    ds = 2.0
    for li, ly in enumerate(layers):
        a = math.radians(ly["ang"])
        ca, sa = math.cos(a), math.sin(a)
        cs = [(x * ca + y * sa, -x * sa + y * ca) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        smin, smax = min(c[0] for c in cs), max(c[0] for c in cs)
        vmin, vmax = min(c[1] for c in cs), max(c[1] for c in cs)
        A, lam, warp = ly.get("A", 0.0), ly.get("lam", 60.0), ly.get("warp")
        pitch, lo, gain = ly["pitch"], ly["lo"], ly["gain"]
        n = int((smax - smin) / ds) + 1
        v = vmin - A - ly.get("pad", 0.0) + 0.3
        i = 0
        lr = random.Random("eng:%s:%s" % (seed, li))
        cell = ly.get("cell", 8.0)
        while v < vmax + A + ly.get("pad", 0.0):
            pv = pitch(v) if callable(pitch) else pitch
            cap = ly.get("cap", int(2 * pv - 1))
            pts = []
            for k in range(n + 1):
                sx = smin + k * ds
                vv = v
                if A:
                    vv += A * (2 * _vn(sx / lam, v / (6.0 * pv) + li * 7.3, seed + li) - 1)
                if warp:
                    vv += warp(sx, v)
                pts.append((sx * ca - vv * sa, sx * sa + vv * ca))
            us, outs = [], []
            nz = [lr.random() for _ in range(32)]
            off = lr.randrange(32)
            for k in range(n):
                xm, ym = (pts[k][0] + pts[k + 1][0]) * 0.5, (pts[k][1] + pts[k + 1][1]) * 0.5
                if xm < x0 - 1 or xm > x1 + 1 or ym < y0 - 1 or ym > y1 + 1:
                    us.append(0)
                    outs.append(False)
                    continue
                if inside is not None and not inside(xm, ym):
                    us.append(0)
                    outs.append(True)
                    continue
                outs.append(False)
                t = grid(xm, ym)
                wpx = (t - lo) * gain * pv / 3.0
                if t <= 0 or wpx <= 0.03:
                    us.append(0)
                    continue
                r = 0.55 * nz[(int(k * ds / cell) + off) % 32] + 0.9 * _vn((smin + k * ds) / 14.0, v / 5.0, seed + 31 + li) - 0.225
                xq = wpx / 0.47
                kq = int(xq)
                if kq == 0:
                    kq = 1 if r < xq ** 1.2 else 0
                elif xq - kq > 0.62 and r < (xq - kq - 0.62) * 2.6:
                    kq += 1
                us.append(min(cap, kq))
            for i0, i1, kq in _runs(us):
                run = pts[i0:i1 + 1]
                if inside is not None:
                    # find the true edge of the form at either end
                    for end, kk, dk in ((0, i0, -1), (-1, i1 - 1, 1)):
                        if 0 <= kk + dk < n and outs[kk + dk]:
                            ax, ay = (pts[kk + dk][0] + pts[kk + dk + 1][0]) * 0.5, (pts[kk + dk][1] + pts[kk + dk + 1][1]) * 0.5
                            bx, by = (pts[kk][0] + pts[kk + 1][0]) * 0.5, (pts[kk][1] + pts[kk + 1][1]) * 0.5
                            for _ in range(4):
                                mx_, my_ = (ax + bx) * 0.5, (ay + by) * 0.5
                                if inside(mx_, my_):
                                    bx, by = mx_, my_
                                else:
                                    ax, ay = mx_, my_
                            run[end] = (bx, by)
                if len(run) > 3:
                    if not A and not warp:
                        run = [run[0], run[-1]]
                    else:
                        st = 4 if lam >= 40 else 3
                        run = [run[0]] + run[st:-2:st] + [run[-1]]
                ink.poly(kq * 0.5, run)
            v += pv
            i += 1


def _hatch(ink, poly, ang, pitch, w, wfn=None, off=0.0, step=2.5):
    """Parallel hatch at angle ang (degrees) clipped to a polygon. wfn(x, y) -> weight or 0."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    R = [(x * ca + y * sa, -x * sa + y * ca) for x, y in poly]
    ys = [p[1] for p in R]
    y = math.floor(min(ys) / pitch) * pitch + off + pitch * 0.5
    ymax = max(ys)
    m = len(R)
    while y < ymax:
        xs = []
        for i in range(m):
            xa, ya = R[i]
            xb, yb = R[(i + 1) % m]
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(xa + (xb - xa) * (y - ya) / (yb - ya))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            u0, u1 = xs[j], xs[j + 1]
            if u1 - u0 < 0.8:
                continue
            if wfn is None:
                ink.seg(w, u0 * ca - y * sa, u0 * sa + y * ca, u1 * ca - y * sa, u1 * sa + y * ca)
            else:
                n = max(1, int(round((u1 - u0) / step)))
                st = (u1 - u0) / n
                ws = []
                for k in range(n):
                    u = u0 + (k + 0.5) * st
                    ws.append(wfn(u * ca - y * sa, u * sa + y * ca))
                for i0, i1, wd in _runs(ws):
                    ua, ub = u0 + i0 * st, u0 + i1 * st
                    ink.seg(wd, ua * ca - y * sa, ua * sa + y * ca, ub * ca - y * sa, ub * sa + y * ca)
        y += pitch


# ------------------------------------------------------------------ the scene
_HOOD = [(-1.0, 0.0), (-0.88, 0.03), (-0.76, 0.07), (-0.64, 0.12), (-0.52, 0.19), (-0.42, 0.27), (-0.34, 0.34),
         (-0.28, 0.37), (-0.22, 0.42), (-0.16, 0.55), (-0.11, 0.7), (-0.07, 0.83), (-0.035, 0.93), (-0.012, 0.985),
         (0.0, 1.0), (0.012, 0.955), (0.026, 0.93), (0.04, 0.955), (0.055, 0.905), (0.085, 0.85), (0.112, 0.83),
         (0.135, 0.74), (0.16, 0.685), (0.185, 0.71), (0.205, 0.665), (0.24, 0.57), (0.272, 0.545), (0.31, 0.44),
         (0.36, 0.4), (0.42, 0.3), (0.5, 0.24), (0.6, 0.15), (0.74, 0.08), (0.88, 0.03), (1.0, 0.0)]


class _Scene(object):
    def __init__(self, w, h, seed, variant, phase):
        self.w, self.h = float(w), float(h)
        try:
            self.seed = int(seed) % 100000
        except (TypeError, ValueError):
            self.seed = sum(ord(c) for c in str(seed)) % 100000
        self.rng = random.Random("river:%s" % self.seed)
        self.var = variant if variant in ("dusk", "night", "goodnight") else "dusk"
        self.night = self.var != "dusk"
        self.phase = float(phase) % 1.0
        self.ink = _Ink()
        self.ink.box = (float(w), float(h) + 1.0)
        W, H = self.w, self.h
        a = H / W
        self.tall = tall = _clamp((a - 0.19) / 0.55, 0.0, 1.0)
        self.hz = hz = round(H * (0.50 + 0.06 * tall))
        self.bh = _clamp(0.11 * H, 7.0, 34.0)                  # near bank depth
        # moon
        self.illum = (1 - math.cos(2 * math.pi * self.phase)) / 2.0
        self.sun = (not self.night) and self.illum < 0.06      # a new moon at dusk: the sun sets instead
        self.mr = r = _clamp(0.17 * hz, 5.0, 26.0)
        self.mx = round(W * 0.405)
        if self.night:
            my = hz * (0.44 - 0.12 * tall)
        else:
            my = hz - r * (1.0 if self.sun else 2.5)
        self.my = round(_clamp(my, r + 3.0, hz - r * 0.2))
        # Mt Hood
        self.hx = W * 0.715
        self.mw = _clamp(W * (0.2 + 0.05 * tall), 36.0, 160.0)
        self.mh = min(0.46 * self.mw, hz * (0.46 - 0.1 * tall))
        self.tl = hz - _clamp(0.035 * hz, 2.0, 5.0)            # top of the far tree line
        # ship
        self.sl = min(_clamp(0.19 * W, 40.0, 110.0), 2.0 * hz)
        self.ssc = self.sl / 100.0
        self.sx0 = W * 0.535 - self.sl * 0.5
        self.swl = hz + max(3.0, 0.07 * (H - hz))
        # heron
        self.hh = min(H * (0.60 - 0.24 * tall), 0.5 * W)
        self.hsc = self.hh / 94.0
        self.hfx = W * 0.235
        self.hfy = H - self.bh - max(3.0, 0.035 * H)
        self.firs = []
        rr = random.Random("ridge:%s" % self.seed)
        self.ridges = [u + rr.uniform(-0.025, 0.025) for u in (-0.74, -0.5, -0.31, -0.15, 0.02, 0.17, 0.33, 0.55, 0.8)]
        self.shore_init()
        # the ring where a fish has jumped
        self.fishR = _clamp(0.04 * W, 7.0, 22.0) if (H - self.bh - hz) > 26 else 0.0
        self.fishx = W * (0.33 if self.var == "goodnight" else 0.75)
        self.fishy = hz + (0.36 if self.var == "goodnight" else 0.52) * (H - self.bh - hz)
        # clouds
        self.clouds = []
        nc = (2 + int(hz / 45.0)) if not self.night else int(hz / 85.0)
        for i in range(nc):
            cy = hz * (0.12 + 0.62 * (i + self.rng.random() * 0.7) / max(1, nc))
            L = W * self.rng.uniform(0.16, 0.34)
            cx = W * self.rng.uniform(0.05, 0.95)
            ry = _clamp(hz * self.rng.uniform(0.035, 0.07), 2.5, 11.0)
            if abs(cy - self.my) < self.mr + ry + 2 and abs(cx - self.mx) < L * 0.5 + self.mr + 6:
                cx = (cx + W * 0.45) % W
            blobs = []
            nb = 5
            for j in range(nb):
                u = (j + 0.5) / nb - 0.5
                blobs.append((cx + u * L + self.rng.uniform(-6, 6), cy + self.rng.uniform(-0.3, 0.3) * ry,
                              L / nb * self.rng.uniform(0.9, 1.5), ry * (1.0 - 1.1 * abs(u)) * self.rng.uniform(0.8, 1.2)))
            self.clouds.append(blobs)
        self.clouds = []
        # mountain facets: (u0, u1, tone)
        fr = random.Random("hood:%s" % self.seed)
        cuts = [-1.0, -0.66, -0.43, -0.27, -0.13, 0.02, 0.2, 0.37, 0.58, 1.0]
        tones = [0.45, 0.24, 0.5, 0.2, 0.1, 0.78, 0.55, 0.85, 0.62]
        self.facets = []
        for i in range(len(tones)):
            j0 = fr.uniform(-0.03, 0.03) if 0 < i else 0
            self.facets.append((cuts[i] + j0, cuts[i + 1], _clamp(tones[i] + fr.uniform(-0.06, 0.06), 0.06, 0.9)))

    # ---- geometry lookups
    def hood(self, x):
        """Skyline y of Mt Hood at x (or None outside the mountain): long north shoulder to the left."""
        u = (x - self.hx) / self.mw
        if u < 0:
            u /= 1.6
        if u <= -1 or u >= 1:
            return None
        e = _interp(_HOOD, u)
        e += 0.05 * (_vn(x / 4.0, 3.3, self.seed) - 0.5) * min(1.0, 5 * (1 - e)) * min(1.0, e * 6)
        return self.tl - e * self.mh

    def shore_init(self):
        """The far shore as a skyline table: alders and cottonwoods built of leafy clumps, firs as spires."""
        rng = random.Random("shore:%s" % self.seed)
        W, hz = self.w, self.hz
        self.th = th = _clamp(0.085 * hz, 4.5, 14.0)
        k = th / 9.0
        y0 = hz + 0.5
        cw = sorted([W * rng.uniform(0.03, 0.1), W * rng.uniform(0.3, 0.36), W * rng.uniform(0.44, 0.49),
                     W * rng.uniform(0.6, 0.66)])
        n = int(W) + 4
        tp = [y0 - 1.0] * n
        trunks = []

        def clump(cx, cy, r):
            for xi in range(max(0, int(cx - r)), min(n, int(cx + r) + 2)):
                d = xi - cx
                if abs(d) < r:
                    yy = cy - math.sqrt(r * r - d * d)
                    if yy < tp[xi]:
                        tp[xi] = yy

        x = -6.0
        while x < W + 6:
            if cw and x >= cw[0]:
                cw.pop(0)
                wd, hg = rng.uniform(10, 14) * k, th * rng.uniform(1.45, 1.9)
                for j in range(7):
                    f = j / 6.0
                    clump(x + wd * (0.5 + rng.uniform(-0.32, 0.32) * (1 - 0.5 * f)), y0 - hg * (0.35 + 0.5 * f),
                          rng.uniform(2.2, 3.6) * k * (1 - 0.3 * f))
                trunks.append((x + wd * 0.5, y0, hg * 0.4))
            elif rng.random() < 0.4:
                wd, hg = rng.uniform(3.5, 5.5) * k, th * rng.uniform(0.75, 1.6)
                cx = x + wd / 2.0
                for xi in range(max(0, int(x)), min(n, int(x + wd) + 2)):
                    d = abs(xi - cx) / (wd / 2.0)
                    if d < 1:
                        tp[xi] = min(tp[xi], y0 - hg * (1 - d) ** 1.2)
            else:
                wd, hg = rng.uniform(7, 12) * k, th * rng.uniform(0.5, 0.9)
                for j in range(rng.randint(3, 5)):
                    clump(x + wd * rng.uniform(0.15, 0.85), y0 - hg * rng.uniform(0.35, 0.72), rng.uniform(2.0, 3.4) * k)
            x += wd * rng.uniform(0.55, 0.9)
        self.tp, self.trunks = tp, trunks

    def shore_top(self, x):
        return self.tp[int(_clamp(x, 0, len(self.tp) - 1))]

    def hills(self, x):
        """Skyline y of the distant foothills."""
        n = _vn(x / 46.0, 0.5, self.seed + 3) * 0.7 + _vn(x / 13.0, 1.5, self.seed + 4) * 0.3
        return self.tl - self.mh * (0.07 + 0.2 * n)

    def skyline(self, x):
        y = self.hills(x)
        m = self.hood(x)
        return y if m is None else min(y, m)

    def cloud(self, x, y):
        best, rel = 0.0, 0.0
        for blobs in self.clouds:
            for cx, cy, rx, ry in blobs:
                dx = (x - cx) / rx
                if dx < -1 or dx > 1:
                    continue
                dy = y - cy
                e = ry if dy < 0 else ry * 0.4
                v = 1 - dx * dx - (dy / e) ** 2
                if v > best:
                    best, rel = v, dy / ry
        return best, rel

    def moon_lit(self, x, y):
        """Inside the disc: True on the lit part."""
        if self.sun:
            return True
        dy = y - self.my
        c = math.sqrt(max(0.0, self.mr * self.mr - dy * dy))
        k = math.cos(2 * math.pi * self.phase)
        if self.phase <= 0.5:
            return (x - self.mx) > k * c
        return (x - self.mx) < -k * c

    # ---- sky
    def cloud_init(self):
        """Banks of soft lobes with flat bases; the moon lights the rims that face it."""
        rng = random.Random("cloud:%s" % self.seed)
        W, hz = self.w, self.hz
        nb = (2 if self.night else 3) + int(W * hz / 45000.0)
        blobs = []
        for b in range(nb):
            R = _clamp(hz * rng.uniform(0.07, 0.13), 4.0, 24.0)
            ln = W * rng.uniform(0.22, 0.5)
            bx = W * rng.uniform(0.0, 1.0)
            by = hz * (0.14 + 0.62 * (b + rng.random() * 0.8) / nb)
            if abs(by - R * 0.5 - self.my) < R + self.mr * 1.3 and abs(bx - self.mx) < ln * 0.5 + self.mr * 1.5:
                bx += (ln * 0.5 + self.mr * 2.5) * (1 if bx >= self.mx else -1)
            n = max(3, int(ln / (R * 1.1)))
            for i in range(n):
                f = (i + 0.5) / n
                r = R * (0.45 + 0.6 * math.sin(math.pi * f)) * rng.uniform(0.75, 1.15)
                blobs.append((bx - ln / 2.0 + ln * f + rng.uniform(-0.3, 0.3) * R, by - r * rng.uniform(0.3, 0.8), r * 1.5, r, by))

        def c(x, y):
            v = 0.0
            for cx, cy, rx, ry, base in blobs:
                dx = (x - cx) / rx
                if -2.2 < dx < 2.2:
                    dy = (y - cy) / ry
                    if -2.2 < dy < 2.2:
                        g = math.exp(-dx * dx - dy * dy)
                        if y > base:
                            g *= max(0.0, 1 - (y - base) / (ry * 0.35))
                        v += g
            return v
        self.cg = _bgrid(c, 0, 0, W, hz, 3.0)

    def sky_tone(self, x, y):
        hz = self.hz
        if y > self.sk[int(_clamp(x, 0, len(self.sk) - 1))]:
            return 0.62 if self.night else 0.4
        v = _clamp(y / float(hz), 0.0, 1.0)
        e = (x / self.w - 0.5) * 2
        if self.night:
            nt = 0.8 - 0.4 * v ** 1.3 + 0.08 * e * e
        else:
            nt = 0.56 - 0.46 * v ** 1.1 + 0.05 * e * e
        mx, my, r = self.mx, self.my, self.mr
        dx, dy = x - mx, y - my
        d = math.sqrt(dx * dx + dy * dy) + 1e-6
        s_ = max(self.illum, 1.0 if self.sun else 0.0)
        g = math.exp(-d * d / (2 * (3.0 * r) ** 2))
        nt -= (0.55 if self.night else 0.3) * g * (0.3 + 0.7 * s_)
        nt = max(nt, 0.04)
        c0 = self.cg(x, y)
        cc = _clamp(c0 * 1.5, 0.0, 1.0)
        if cc <= 0.01:
            return nt
        lit = _clamp(0.42 + 2.4 * (c0 - self.cg(x + 7 * (mx - x) / d, y + 7 * (my - y) / d)), 0.0, 1.0)
        lit *= _clamp(1.3 - d / (0.8 * self.w), 0.0, 1.0) * (0.45 + 0.55 * s_)
        if self.night:
            ct = 0.1 + 0.68 * (1 - lit)
        else:
            ct = 0.03 + 0.5 * (1 - lit)
        return nt * (1 - cc) + ct * cc

    def sky(self):
        ink, W, seed = self.ink, self.w, self.seed
        sk = self.sk
        self.cloud_init()
        g = _bgrid(self.sky_tone, 0, 0, W, self.hz + 1, 3.0)
        ha = self.hoodonly
        _engrave(ink, (0, 0, W, self.hz), g,
                 [dict(ang=-1.5, pitch=1.5, lo=0.0, gain=3.0, A=2.6, lam=75.0, pad=12.0),
                  dict(ang=-32, pitch=2.0, lo=0.42, gain=3.6, A=1.5, lam=40.0),
                  dict(ang=58, pitch=2.0, lo=0.66, gain=4.8, cap=1, A=1.5, lam=33.0)], seed,
                 inside=lambda x, y: y < ha[int(_clamp(x, 0, len(ha) - 1))] - 0.3)
        self.sky_lines = [(yy, 2.0) for yy in range(2, int(self.tl), 2)]
        # the moon: only the lit part is paper; the dark part is left to the sky, with a ghost of a limb
        r, mx, my = self.mr, self.mx, self.my
        ink.flush()
        full = self.sun or self.illum >= 0.97
        k = math.cos(2 * math.pi * self.phase)
        sg = 1 if self.phase <= 0.5 else -1
        if full:
            ink.out.append('<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke-width=".5"/>' % (_n(mx), _n(my), _n(r)))
        elif self.illum > 0.03:
            limb, term = [], []
            for j in range(0, 33):
                th_ = -math.pi / 2 + math.pi * j / 32.0
                c, sn = math.cos(th_), math.sin(th_)
                limb.append((mx + sg * r * c, my + r * sn))
                term.append((mx + sg * k * r * c, my + r * sn))
            ink.mask(limb + term[::-1])
            ink.poly(0.5, limb)
        ink.out.append('<circle cx="%s" cy="%s" r="%s" stroke-width=".5" stroke-dasharray=".5 2.5"/>' % (_n(mx), _n(my), _n(r)))
        if (full or self.illum > 0.1) and not self.sun and r >= 5:
            for cx, cy, rr in ((-0.34, -0.3, 0.3), (0.02, -0.46, 0.2), (0.3, -0.12, 0.17), (0.2, 0.2, 0.24), (-0.3, 0.3, 0.12),
                               (0.08, 0.56, 0.1), (0.52, 0.3, 0.12), (0.5, -0.38, 0.1)):
                yy = -rr
                while yy <= rr:
                    hw = math.sqrt(max(0, rr * rr - yy * yy)) * r * (0.55 + 0.7 * _hash(int(yy * 40), int(cx * 50), seed))
                    px, py = mx + (cx + 0.08 * (_hash(int(yy * 40), 7, seed) - 0.5)) * r, my + (cy + yy) * r
                    xa, xb = px - hw, px + hw
                    if not full:
                        cc = math.sqrt(max(0.0, r * r - (py - my) ** 2))
                        if sg > 0:
                            xa = max(xa, mx + k * cc + 1.0)
                        else:
                            xb = min(xb, mx - k * cc - 1.0)
                    lim = math.sqrt(max(0.0, r * r - (py - my) ** 2)) - 1.0
                    xa, xb = max(xa, mx - lim), min(xb, mx + lim)
                    if xb - xa > 1.0:
                        ink.seg(0.5, xa, py, xb, py)
                    yy += 1.5 / r

    def cloud_lines(self):
        """Clouds modelled as billows: arcs that follow each rounded form, heaviest on the side
        and underside turned from the moon, the lit edge left as bare paper."""
        ink = self.ink
        for blobs in self.clouds:
            for cx, cy, rx, ry in blobs:
                if ry < 2.2:
                    continue
                aw = 1 if cx >= self.mx else -1
                f = 0.3
                j = 0
                while f <= 1.0:
                    pts, ws = [], []
                    for q in range(0, 16):
                        th_ = math.radians(-50 + 165 * q / 15.0)
                        c, sn = math.cos(th_), math.sin(th_)
                        px = cx + aw * f * rx * c
                        py = cy + f * ry * sn * (1.0 if sn < 0 else 0.42)
                        if py > self.sk[int(_clamp(px, 0, len(self.sk) - 1))] - 1.5:
                            continue
                        pts.append((px, py))
                    if len(pts) > 2:
                        ff = f
                        ink.swell(pts, lambda t: (0.3 + 0.9 * ff) * (0.45 + 0.9 * math.sin(math.pi * min(1.0, 0.15 + t))))
                    f += max(0.12, 1.5 / ry) * (1.0 if j % 2 else 1.25)
                    j += 1

    def stars(self):
        if not self.night:
            return
        rng = random.Random("stars:%s" % self.seed)
        n = int(self.w * self.hz / 1100.0) + 6
        small, big, core = [], [], []
        for i in range(n):
            x = rng.uniform(3, self.w - 3)
            y = rng.uniform(2, self.hz)
            if y > self.sk[int(x)] - 5 or y > self.shore_top(x) - 5:
                continue
            if math.hypot(x - self.mx, y - self.my) < self.mr * 1.8:
                continue
            if self.cg(x, y) > 0.2:
                continue
            x, y = round(x * 2) / 2.0, round(y * 2) / 2.0
            if rng.random() < 0.28:
                L = rng.choice((3.0, 3.5, 4.5))
                big.append("M%s %sh%sM%s %sv%s" % (_n(x - L), _n(y), _n(2 * L), _n(x), _n(y - L), _n(2 * L)))
                core.append("M%s %sh.1" % (_n(x), _n(y)))
            else:
                small.append("M%s %sh.1" % (_n(x), _n(y)))
        self.ink.white(1.5, "".join(small), True)
        self.ink.white(0.5, "".join(big))
        self.ink.white(2, "".join(core), True)

    # ---- Mt Hood: fan contour lines falling from the summit, facets by tone
    def mountain(self):
        ink, seed = self.ink, self.seed
        hx, mw, mh, base = self.hx, self.mw, self.mh, self.tl
        top = base - mh
        ay = top - 0.22 * mh
        span = base - ay
        sb = 2.0
        ridges = self.ridges

        def shade(u):
            prev, nxt = -1.0, 1.0
            for r in ridges:
                if r <= u:
                    prev = r
                else:
                    nxt = r
                    break
            du = (u - prev) / max(0.02, nxt - prev)
            return 1 - _smooth(0.1, 0.62, du)

        def timber(x):
            return 0.2 + 0.1 * (_vn(x / 11.0, 0.3, seed + 6) - 0.5)

        def tone(x, y, u):
            d = (base - y) / mh
            n1 = _vn(x / 8.0, y / 5.0, seed + 5)
            sh = shade(u + 0.04 * (n1 - 0.5))
            face = 0.2 if u > 0.03 else 0.0
            snow = 0.4 + 0.18 * (n1 - 0.5) + (0.06 if u > 0 else 0.0)
            tb = timber(x)
            if d < tb:
                return 0.55 + 0.4 * _vn(x / 3.0, y / 2.0, seed + 8)
            if d < snow:
                k = (d - tb) / max(0.01, snow - tb)
                return (0.42 + 0.34 * sh + face) * (1 - 0.4 * k)
            return _clamp(0.85 * sh + face * 0.7, 0.0, 1.0)

        def gx(bx, tt):
            return hx + (bx - hx) * tt ** 1.45

        xl, xr = hx - 1.6 * mw, hx + mw
        N = int((xr - xl) / sb)
        n = max(3, int(span / 3.0))
        for k in range(1, N):
            bx = xl + k * sb
            u = (bx - hx) / (mw * 1.6 if bx < hx else mw)
            lev, kk = 0, k
            while kk % 2 == 0 and lev < 5:
                kk //= 2
                lev += 1
            pts = [(gx(bx, j / float(n)), ay + span * j / float(n)) for j in range(n + 1)]
            ws = []
            for j in range(n):
                tm = (j + 0.5) / n
                x, y = gx(bx, tm), ay + span * tm
                m = self.hood(x)
                sp = sb * tm ** 1.45 * (2 ** lev)
                if m is None or y < m + 1.0 or sp < 1.0:
                    ws.append(0)
                    continue
                while sp >= 2.0:
                    sp /= 2.0
                ws.append(min(_q(tone(x, y, u) * 1.15, sp, k, y, seed), 0.5 if sp < 1.5 else 1.0))
            for i0, i1, wd in _runs(ws):
                ink.poly(wd, pts[i0:i1 + 1])
        def tone_xy(x, y):
            m = self.hood(x)
            if m is None or y < m:
                return -1
            tt = (y - ay) / span
            bxr = (x - hx) / max(0.02, tt ** 1.45)
            return tone(x, y, _clamp(bxr / (mw * 1.6 if bxr < 0 else mw), -1.0, 1.0))

        g = _Grid(tone_xy, xl, top, xr, base, 2.0)
        _engrave(ink, (xl, top, xr, base), g,
                 [dict(ang=33, pitch=1.5, lo=0.5, gain=5.0, cap=1, A=0.6, lam=20.0),
                  dict(ang=-12, pitch=1.5, lo=0.72, gain=7.0, cap=1, A=0.5, lam=20.0)], seed + 400,
                 inside=lambda x, y: y > self.hoodarr[int(_clamp(x, 0, len(self.hoodarr) - 1))] + 1.0)
        # the rock ribs (cleavers) between the glaciers, swelling as they fall
        for r in ridges:
            bx = hx + r * (mw * 1.6 if r < 0 else mw)
            pts = []
            for j in range(n + 1):
                tt = j / float(n)
                x, y = gx(bx, tt), ay + span * tt
                m = self.hood(x)
                if m is None or y < m + 0.5 or (base - y) / mh < timber(x) + 0.05:
                    continue
                pts.append((x + 1.6 * (_vn(y / 4.0, r * 9.0, seed + 12) - 0.5), y))
            if len(pts) > 2:
                ink.swell(pts, lambda t: 0.5 + 1.1 * math.sin(math.pi * min(1.0, t * 1.15)))
        # timberline: a ragged row of small firs
        tk = []
        x = xl + 2
        while x < xr - 2:
            m = self.hood(x)
            yt = base - timber(x) * mh
            if m is not None and yt > m + 2.5:
                tk.append((x, yt + 1.5, x, yt - 1.2 - 2.4 * _hash(int(x * 3), 5, seed)))
            x += 2.5
        ink.ticks(1.0, tk)
        # skyline: hairline on the lit side, heavier on the shadow side; foothill crest
        lit, shd = [], []
        x = xl
        while x <= xr:
            m = self.hood(x)
            if m is not None and m < self.hills(x) + 0.5:
                (lit if x <= hx + 1.0 else shd).append((x, m))
            x += 1.5
        if len(lit) > 1:
            ink.poly(0.5, lit)
        if len(shd) > 1:
            ink.swell(shd, lambda t: 1.1 - 0.5 * t)
        run, x = [], 0.0
        while x <= self.w + 8:
            m = self.hood(x)
            hy = self.hills(x)
            if m is None or hy < m:
                run.append((x, hy))
            else:
                if len(run) > 1:
                    ink.poly(0.5, run)
                run = []
            x += 8.0
        if len(run) > 1:
            ink.poly(0.5, run)

    def treeline(self):
        """The far shore: leafy crowns lit from the moon side, worked with short upright strokes
        and crossed in the shadows."""
        ink, hz, th, seed, W = self.ink, self.hz, self.th, self.seed, self.w
        tp = self.tp
        prof = [(float(i), tp[i]) for i in range(0, int(W) + 2)]
        ink.mask([(-1, hz + 1)] + prof + [(W + 1, hz + 1)])

        def tone(x, y):
            t0 = self.shore_top(x)
            if y < t0:
                return -1
            dep = min(1.0, (y - t0) / (0.8 * th))
            lit = 1.0 if self.shore_top(x + 1.6) < t0 - 0.25 else 0.0
            return _clamp(0.5 + 0.42 * dep * dep - 0.3 * lit * (1 - dep) + 0.2 * (_vn(x / 4.0, y / 3.0, seed + 23) - 0.5), 0.04, 1.0)

        ytop = hz - 2.2 * th
        g = _Grid(tone, 0, ytop, W, hz + 1, 1.0)
        _engrave(ink, (0, ytop, W, hz + 0.5), g,
                 [dict(ang=84, pitch=1.5, lo=0.0, gain=3.2, A=0.5, lam=5.0),
                  dict(ang=0, pitch=1.5, lo=0.55, gain=6.0, A=0.3, lam=9.0),
                  dict(ang=40, pitch=1.5, lo=0.85, gain=8.0, cap=1)], seed + 300,
                 inside=lambda x, y: y > tp[int(_clamp(x, 0, len(tp) - 1))] + 0.4)
        # crown edges on the shadow side
        run = []
        for i in range(1, len(prof) - 1):
            if True:
                run.append(prof[i])
            else:
                if len(run) > 1:
                    ink.poly(0.5, run)
                run = []
        if len(run) > 1:
            ink.poly(0.5, run)
        for cx, y0, hg in self.trunks:
            ink.white(0.5, "M%s %sl%s %s" % (_n(cx), _n(y0), _n(0.6), _n(-hg)))
        ink.seg(1.0, 0, hz + 0.5, W, hz + 0.5)

    # ---- water
    def water_tone(self, x, y):
        seed, hz, H = self.seed, self.hz, self.h
        d = (y - hz) / float(H - hz)
        t = (0.5 + 0.22 * d) if self.night else (0.3 + 0.3 * d)
        # ripples: long flat lozenges of tone
        t += 0.2 * (_vn(x / (30.0 + 44 * d), y / 2.2, seed + 11) - 0.5)
        dy = y - hz
        # mountain and hill reflections
        m = self.skyline(x)
        depth = (hz - m) * 0.85
        if dy < depth:
            t += 0.2 * (1 - dy / max(1.0, depth)) + 0.06
        # far shore reflection: the crowns upside down, broken by the ripple
        rh = (hz - self.shore_top(x + 5.0 * (_vn(y / 1.6, 0.9, seed + 18) - 0.5))) * 0.95 + 1.0
        if dy < rh:
            t += 0.36 * (1 - 0.5 * dy / rh)
        else:
            t += 0.14 * math.exp(-(dy - rh) / 2.5)
        if dy < 2.2:
            t *= 0.25
        # ship
        sx0, sl, wl = self.sx0, self.sl, self.swl
        rag = 9.0 * (_vn(y / 1.7, 0.4, seed + 14) - 0.5) * (1 + 3 * d)
        if sx0 - 3 < x + rag < sx0 + sl + 2:
            sd = y - wl
            if -1.0 < sd < 2.8:
                t = 0.0
            elif sd >= 2.8:
                dep = 0.3 * sl
                br = _vn(x / 6.0, y / 1.3, seed + 13)
                if sd < dep and br > 0.75 * sd / dep:
                    t += 0.4 * (1 - sd / dep) ** 0.7
        # firs
        for fx, ty, hw, by in self.firs:
            fd = abs(x + rag - fx) / (hw * 1.1)
            if fd < 1 and y < by + 4:
                t += 0.26 * (1 - fd * fd) * (0.4 + 0.6 * _vn(x / 7.0, y / 1.4, seed + 16))
        # heron
        hd = y - self.hfy
        if 0 < hd < self.hh * 0.42 and abs(x - self.hfx + 3 * self.hsc) < self.hh * (0.16 - 0.25 * hd / self.hh):
            if _vn(x / 5.0, y / 1.5, seed + 15) > 0.35:
                t += 0.3
        # pale shallows round the heron's legs
        ex = (x - self.hfx) / (self.hh * 0.33)
        ey = (y - self.hfy - 1) / max(3.0, self.hh * 0.07)
        e2 = ex * ex + ey * ey
        if e2 < 1:
            t = t * (0.3 + 0.7 * e2) + 0.2 * math.cos(math.sqrt(e2) * 12.5) * (1 - e2)
        if self.fishR:
            fx_ = (x - self.fishx) / (self.fishR * 1.5)
            fy_ = (y - self.fishy) / (self.fishR * 0.48)
            er = math.sqrt(fx_ * fx_ + fy_ * fy_)
            if er < 1:
                t = t * (0.55 + 0.45 * er) + 0.3 * math.cos(er * 15.0) * (1 - er)
        # moon shimmer: broken glitter widening toward the viewer
        s = max(self.illum, 1.0 if self.sun else 0.0)
        if s > 0.04:
            half = self.mr * 0.75 + dy * 0.2
            ax = abs(x - self.mx - 3.0 * (_vn(y / 3.0, 0.2, seed + 17) - 0.5))
            if ax < half * 1.6 and y > hz + 2:
                core = 1 - _smooth(half * 0.15, half * 1.6, ax)
                g = _vn(x / (5.0 + 9 * d), y / 1.3, seed + 19)
                if g < 0.28 + 0.5 * core * (0.4 + 0.6 * s):
                    t *= 1 - core * (0.6 + 0.4 * s)
                else:
                    t += 0.12 * core
        return _clamp(t, 0.03, 1.0)

    def water(self):
        hz, H, W = self.hz, self.h, self.w
        g = _Grid(self.water_tone, 0, hz, W, H, 2.0)

        def pitch(v):
            return round((1.5 + 1.3 * _clamp((v - hz) / (H - hz), 0, 1)) * 2) / 2.0

        _engrave(self.ink, (0, hz + 1.2, W, H), g,
                 [dict(ang=0, pitch=pitch, lo=0.0, gain=3.0, A=0.7, lam=40.0),
                  dict(ang=88, pitch=1.5, lo=0.66, gain=6.5, A=0.6, lam=12.0),
                  dict(ang=-24, pitch=2.0, lo=0.9, gain=8.0, cap=1)], self.seed + 100)

    # ---- container ship, bow to the left
    def ripples(self):
        """Drawn wavelets that grow toward the viewer, and the ring of a jumping fish."""
        ink, W, H, hz = self.ink, self.w, self.h, self.hz
        rng = random.Random("rip:%s" % self.seed)
        wb = H - self.bh * 0.7
        n = int(W * (wb - hz) / 1500.0) + 3
        for i in range(n):
            d = rng.uniform(0.2, 1.0)
            y = hz + (wb - hz) * d
            x = rng.uniform(0, W)
            if abs(x - self.mx) < self.mr + (y - hz) * 0.25 or abs(x - self.hfx) < self.hh * 0.3:
                continue
            ln = (4 + 11 * d) * rng.uniform(0.6, 1.2)
            ink.raw(1.0 if d > 0.55 else 0.5, "M%s %sq%s %s %s 0" % (_n(x), _n(y), _n(ln / 2), _n(-(0.8 + 1.6 * d)), _n(ln)))
            if d > 0.5:
                ink.raw(0.5, "M%s %sq%s %s %s 0" % (_n(x + ln * 0.3), _n(y + 2.5), _n(ln / 3), _n(-(0.6 + d)), _n(ln * 0.66)))
        R = self.fishR
        if R:
            cx, cy = self.fishx, self.fishy
            for k, w0 in ((0.45, 0.5), (1.0, 1.0), (1.5, 0.5)):
                rx, ry = R * k, R * k * 0.32
                ink.raw(w0, "M%s %sa%s %s 0 0 0 %s 0" % (_n(cx - rx), _n(cy), _n(rx), _n(ry), _n(2 * rx)))
                if k < 1.2:
                    ink.raw(0.5, "M%s %sa%s %s 0 0 1 %s 0" % (_n(cx - rx), _n(cy), _n(rx), _n(ry), _n(2 * rx)))
            if R >= 9:
                fy = cy - R * 0.95
                body = _cr([(cx - R * 0.5, fy + R * 0.2), (cx - R * 0.2, fy - R * 0.16), (cx + R * 0.16, fy - R * 0.16),
                            (cx + R * 0.46, fy + R * 0.2)], 4)
                ink.swell(body, lambda t: 0.4 + 1.3 * math.sin(math.pi * (0.15 + 0.85 * t)))
                tx, ty = body[0]
                ink.ticks(0.5, [(tx, ty, tx - R * 0.2, ty - R * 0.02), (tx, ty, tx - R * 0.1, ty + R * 0.22)])
                ink.dot(cx + R * 0.1, cy - R * 0.35)
                ink.dot(cx - R * 0.3, cy - R * 0.5)
                ink.dot(cx + R * 0.5, cy - R * 0.45)

    def ship(self):
        ink, sc, x0, wl = self.ink, self.ssc, self.sx0, self.swl
        rng = random.Random("ship:%s" % self.seed)

        def P(u, v):
            return (x0 + u * sc, wl - v * sc)

        hull = [P(0, 10.5), P(7, 0), P(97.5, 0), P(100, 7), P(100, 10), P(72, 10), P(72, 9.3), P(11, 9.3), P(11, 10.5)]
        bays = []
        u = 13.5
        while u < 66:
            bays.append((u, 8.2, rng.choice((2, 3, 3, 4, 4))))
            u += 9.3
        th = 3.5
        sil = [P(0, 10.5), P(7, 0), P(97.5, 0), P(100, 7), P(100, 10), P(91, 10), P(91, 25), P(86, 25), P(86, 31),
               P(73, 31), P(73, 10)]
        for bu, bw, nt in reversed(bays):
            sil += [P(bu + bw, 9.3), P(bu + bw, 9.3 + nt * th), P(bu, 9.3 + nt * th), P(bu, 9.3)]
        sil += [P(11, 9.3), P(11, 10.5)]
        ink.mask(sil)
        # hull: close ruling, cross-hatched toward the stern, a light sheer strake under the rail
        _hatch(ink, hull, 0, 1.5, 1.0, off=0.2)
        if sc * 10 > 6:
            _hatch(ink, hull, 62, 3.0, 0.5)
        ink.poly(1.0, hull, True)
        a_, b_ = P(9, 7.4), P(99.4, 7.4)
        ink.white(0.5, "M%s %sL%s %s" % (_n(a_[0]), _n(a_[1]), _n(b_[0]), _n(b_[1])))
        a_, b_ = P(5.5, 0.2), P(98, 0.2)
        ink.white(1, "M%s %sL%s %s" % (_n(a_[0]), _n(a_[1] + 1.0), _n(b_[0]), _n(b_[1] + 1.0)))
        # containers
        for bu, bw, nt in bays:
            for k in range(nt):
                box = [P(bu, 9.3 + k * th), P(bu + bw, 9.3 + k * th), P(bu + bw, 9.3 + (k + 1) * th), P(bu, 9.3 + (k + 1) * th)]
                tn = rng.random()
                if tn < 0.3:
                    _hatch(ink, box, 90, 2.0, 1.0)
                elif tn < 0.6:
                    _hatch(ink, box, 90, 2.0, 0.5)
                elif tn < 0.8:
                    _hatch(ink, box, 0, 1.5, 0.5)
                ink.poly(0.5, box, True)
        # deckhouse, bridge wings, funnel, masts
        house = [P(74, 10), P(85, 10), P(85, 27.5), P(74, 27.5)]
        ink.poly(1.0 if sc > 0.7 else 0.5, house, True)
        if self.night:
            _hatch(ink, house, 90, 1.5, 1.0)
        else:
            _hatch(ink, [P(81.5, 10), P(85, 10), P(85, 27.5), P(81.5, 27.5)], 90, 1.5, 0.5)
        wins = []
        v = 13.0
        while v < 27:
            xa, ya = P(75, v)
            if sc > 0.55:
                wins.append("M%s %sh%s" % (_n(xa), _n(ya), _n(6 * sc)))
            v += 3.6
        if wins:
            ink.flush()
            if self.night:
                a_, b_ = P(73.6, 29.5), P(85.4, 29.5)
                wins.append("M%s %sh%s" % (_n(a_[0]), _n(a_[1]), _n(b_[0] - a_[0])))
                ink.out.append('<path stroke="#fff" stroke-width="1" stroke-dasharray="1.5 1" d="%s"/>' % "".join(wins))
            else:
                ink.out.append('<path stroke-width=".5" stroke-dasharray="1 1" d="%s"/>' % "".join(wins))
        ink.poly(1.0, [P(72.5, 28), P(86.5, 28), P(86.5, 31), P(72.5, 31)], True)
        ink.seg(0.5, P(73.5, 29.5)[0], P(73.5, 29.5)[1], P(85.5, 29.5)[0], P(85.5, 29.5)[1])
        fun = [P(87, 10), P(91, 10), P(91, 25), P(87, 25)]
        _hatch(ink, fun, 90, 1.5, 1.0)
        ink.poly(0.5, fun, True)
        ink.seg(0.5, P(79.5, 31)[0], P(79.5, 31)[1], P(79.5, 41)[0], P(79.5, 41)[1])
        ink.seg(0.5, P(77.5, 37)[0], P(77.5, 37)[1], P(81.5, 37)[0], P(81.5, 37)[1])
        ink.seg(0.5, P(5.5, 10.5)[0], P(5.5, 10.5)[1], P(5.5, 21)[0], P(5.5, 21)[1])
        ink.seg(0.5, P(5.5, 21)[0], P(5.5, 21)[1], P(11, 12)[0], P(11, 12)[1])
        if self.night:                                           # masthead and stern lights
            ink.flush()
            ink.out.append('<path stroke="#fff" stroke-width="1.5" stroke-linecap="round" d="M%s %sh.1M%s %sh.1"/>'
                           % (_n(P(79.5, 42)[0]), _n(P(79.5, 42)[1]), _n(P(5.5, 22)[0]), _n(P(5.5, 22)[1])))

    # ---- Douglas firs: herringbone hatching, drooping boughs
    def place_firs(self):
        W = self.w
        specs = [(0.9, 0.93, 0.085), (0.962, 0.56, 0.032)] if W >= 400 else [(0.82, 0.74, 0.08)]
        if W >= 300:
            specs.append((0.828, 0.4, 0.028))
        self.firs = []
        for fx, fh, wl in specs:
            x = W * fx
            by = self.bank_top(x) + 3.0
            Hh = min(by * fh, by - 4.0)
            self.firs.append((x, by - Hh, min(0.2 * Hh, wl * W + 2.0), by))

    def fir(self, fx, ty, hw, by, k):
        """A Douglas fir, bough by bough: each tier droops from the trunk, lifts at the tip, and
        carries its needles underneath, heaviest in the shadow next to the trunk."""
        ink = self.ink
        rng = random.Random("fir:%s:%s" % (self.seed, k))
        Hh = by - ty
        dt0 = _clamp(Hh * 0.042, 3.5, 11.0)
        tiers = []
        y = ty + dt0 * 0.6
        while y < by - Hh * 0.08:
            f = ((y - ty) / Hh) ** 0.8
            dt = dt0 * (0.55 + 0.75 * f)
            tiers.append((y, f, dt))
            y += dt
        if not tiers:
            return
        sil = {-1: [(fx, ty - 1.5)], 1: [(fx, ty - 1.5)]}
        boughs = []
        for y, f, dt in tiers:
            for sg in (-1, 1):
                ln = hw * f * rng.uniform(0.7, 1.08) + 1.5
                dr = ln * rng.uniform(0.28, 0.44)
                yy = y + (0 if sg < 0 else dt * 0.45)
                boughs.append((yy, sg, ln, dr, dt))
                sil[sg].append((fx + sg * ln * 0.3, yy - 1.0))
                sil[sg].append((fx + sg * (ln + 1.0), yy + dr - 0.14 * ln - 1.0))
                sil[sg].append((fx + sg * ln * 0.72, yy + dr * 0.6 + dt * 0.85))
        ybot = tiers[-1][0] + tiers[-1][2]
        ink.mask(sil[-1] + [(fx - 2, ybot), (fx - 2, by + 2), (fx + 2, by + 2), (fx + 2, ybot)] + sil[1][::-1])
        ink.seg(1.0, fx, ty - 1.5, fx, ty + Hh * 0.4)
        ink.seg(1.5, fx, ty + Hh * 0.4, fx, by + 2)
        if hw > 12:
            ink.seg(0.5, fx + 2, ty + Hh * 0.55, fx + 2, by + 2)
            ink.seg(1.0, fx - 1.5, ybot - 2, fx - 3.5, by + 2)

        def by_(y0, ln, dr, s_):
            return y0 + dr * s_ ** 1.5 - 0.14 * ln * _smooth(0.7, 1.0, s_)

        wc10, wc05 = [], []
        for yy, sg, ln, dr, dt in boughs:
            heavy, light, cross = [], [], []
            x = 0.8 + rng.uniform(0, 1.0)
            while x < ln:
                s_ = x / ln
                yb = by_(yy, ln, dr, s_)
                L = dt * (1.45 - 0.85 * s_) * rng.uniform(0.7, 1.1) + 1.0
                seg = (fx + sg * x, yb, fx + sg * (x + 0.22 * L), yb + L)
                if s_ < (0.45 if sg < 0 else 0.7):
                    heavy.append(seg)
                    cross.append((fx + sg * (x + 0.8), yb + 0.8, fx + sg * (x - 0.25 * L), yb + L * 0.8))
                else:
                    light.append(seg)
                x += 1.5
            ink.ticks(1.0, heavy)
            ink.ticks(0.5, cross)
            ink.ticks(1.0 if sg > 0 else 0.5, light)
            n = max(2, int(ln / 4.0))
            pts = [(fx + sg * ln * i / float(n), by_(yy, ln, dr, i / float(n))) for i in range(n + 1)]
            ink.swell(pts, lambda t: 1.2 - 0.7 * t)
            # needle clusters cut out of the dark in white line where the moon catches the bough
            if ln > 5:
                nl = _clamp(dt * 0.5, 2.0, 5.0)
                m = max(2, int(ln / 3.4))
                for q in range(m):
                    f = 0.2 + 0.8 * (q + rng.uniform(0.2, 0.8)) / m
                    bx_, by__ = fx + sg * ln * f, by_(yy, ln, dr, f) + 1.5
                    a0 = math.atan2(0.75, sg)
                    for kk, da in enumerate((0.0, 0.55, -0.55)):
                        if sg > 0 and (kk or q % 2):
                            continue
                        a = a0 + da * sg + rng.uniform(-0.15, 0.15)
                        l2 = nl * rng.uniform(0.7, 1.1) * (1.0 if kk == 0 else 0.75)
                        (wc10 if sg < 0 and kk == 0 and f > 0.45 else wc05).append(
                            "M%s %sL%s %s" % (_n(bx_), _n(by__), _n(bx_ + math.cos(a) * l2), _n(by__ + math.sin(a) * l2)))
        ink.white(1, "".join(wc10))
        ink.white(0.5, "".join(wc05))

    # ---- the heron (unit box: 94 tall, facing right)
    def heron(self):
        ink, sc = self.ink, self.hsc
        fx, fy = self.hfx, self.hfy
        big = self.hh >= 95
        cn = 4 if big else 3
        m = 18 if big else 14

        def P(u, v):
            return (fx + (u - 30) * sc, fy - (94 - v) * sc)

        def PP(pts):
            return [P(u, v) for u, v in pts]

        # legs behind the body
        lw = 1.5 if self.hh >= 70 else 1.0
        rear = _cr(PP([(25.5, 64), (27.6, 74), (28.2, 81), (26.6, 88), (26.2, 94)]), 4)
        front = _cr(PP([(31.5, 63), (32.4, 73), (33.2, 80.5), (32, 88), (31.8, 94)]), 4)
        lgw = max(2.4, 2.2 * sc)
        for cen in (rear, front):
            Lp, Rp = _sweep(cen, lambda t: lgw * (1.3 - 0.4 * t))
            ink.mask(Lp + Rp[::-1], 0.5)
            ink.poly(1.0, Lp)
        if big:
            for u, v in ((28.2, 81), (33.2, 80.5)):
                x, y = P(u, v)
                ink.poly(1.0, [(x - 0.8, y - 1.2), (x + 1.0, y), (x - 0.6, y + 1.3)])
        # thigh feathers
        for i in range(4):
            a, b = P(24.5 + i * 2.6, 62), P(25.6 + i * 2.2, 69.5 - (i % 2) * 1.5)
            ink.seg(0.5, a[0], a[1], b[0], b[1])
        # rings where the legs enter the water, and the broken leg reflection
        for u, rr in ((26.2, 4.2), (31.8, 5.2)):
            x, y = P(u, 94)
            r1 = max(3.0, rr * sc)
            ink.raw(0.5, "M%s %sa%s %s 0 0 0 %s 0" % (_n(x - r1), _n(y + 0.5), _n(r1), _n(max(1.0, r1 * 0.3)), _n(2 * r1)))
            if big:
                r2 = r1 * 1.9
                ink.raw(0.5, "M%s %sa%s %s 0 0 0 %s 0" % (_n(x - r2), _n(y + 1.5), _n(r2), _n(r2 * 0.28), _n(r2 * 1.5)))
        # body
        back = _resample(_cr(PP([(41, 45.5), (36, 42.6), (28, 42), (19.5, 45), (11.5, 52), (5.5, 61), (1, 70)]), cn), m)
        belly = _resample(_cr(PP([(41, 45.5), (43.4, 50), (42.4, 56), (37.5, 62), (29, 65.2), (19, 66.2), (9, 67.4), (1, 70)]), cn), m)
        ink.mask(back + belly[::-1])
        thick = 21 * sc
        J = max(3, int(thick / 1.75))
        for j in range(J):
            s = (j + 1.0) / (J + 1)
            if s < 0.16:
                continue
            i0 = int(round((0.07 + 0.3 * abs(s - 0.5)) * (m - 1)))
            i1 = m - 1 - (j % 3)
            pts = [(back[i][0] + (belly[i][0] - back[i][0]) * s, back[i][1] + (belly[i][1] - back[i][1]) * s)
                   for i in range(i0, i1 + 1)]
            if s < 0.42:
                # lit back: fine line, broken into feather lengths
                step = 5
                for a in range(0, len(pts) - 1, step):
                    ink.poly(0.5, pts[a:a + step])
            elif s < 0.7:
                ink.poly(1.0 if (j % 2 == 0 or not big) else 0.5, pts)
            else:
                ink.poly(1.5 if big and s > 0.8 else 1.0, pts)
        # wing edge and scapular scallops
        wing = [(back[i][0] + (belly[i][0] - back[i][0]) * 0.45, back[i][1] + (belly[i][1] - back[i][1]) * 0.45)
                for i in range(3, m - 2)]
        if big:
            for a in range(1, len(wing) - 2, 2):
                x, y = wing[a]
                ink.raw(0.5, "M%s %sq%s %s %s %s" % (_n(x), _n(y - 2.2 * sc), _n(-2.4 * sc), _n(1.6 * sc), _n(-1.0 * sc), _n(4.6 * sc)))
        ink.swell(back, lambda t: 0.55 + 0.6 * t)
        ink.swell(belly, lambda t: 0.6 + 0.95 * math.sin(math.pi * t))
        # breast plumes
        for i, (u0, v0, u1, v1) in enumerate(((40.5, 48, 39.6, 62.5), (42, 50, 41.6, 65), (38.6, 50, 37.4, 61), (43, 53, 43.4, 62))):
            if i < 3 or big:
                a, b = P(u0, v0), P(u1, v1)
                ink.raw(0.5, "M%s %sq%s %s %s %s" % (_n(a[0]), _n(a[1]), _n(1.6 * sc), _n((b[1] - a[1]) * 0.5), _n(b[0] - a[0]), _n(b[1] - a[1])))
        # neck: an S swept from breast to head
        cen = _resample(_cr(PP([(40, 48), (42.6, 42), (42, 35.5), (38, 29.5), (35.2, 23.5), (35.8, 17.5), (39, 12.8), (43.4, 9.6)]), cn), 20)
        wtab = [(0, 7.2), (0.15, 5.4), (0.4, 3.9), (0.7, 3.3), (0.9, 3.4), (1.0, 4.2)]
        L, R = [], []
        for i, (x, y) in enumerate(cen):
            xa, ya = cen[max(0, i - 1)]
            xb, yb = cen[min(len(cen) - 1, i + 1)]
            dl = math.hypot(xb - xa, yb - ya) or 1.0
            nx, ny = -(yb - ya) / dl, (xb - xa) / dl
            hw = max(0.9, _interp(wtab, i / 19.0) * sc * 0.5)
            L.append((x + nx * hw, y + ny * hw))
            R.append((x - nx * hw, y - ny * hw))
        ink.mask(L + R[::-1])
        ink.poly(1.0, L[1:])
        ink.poly(0.5 if not big else 1.0, R[1:])
        if 3.4 * sc >= 3.0:
            # throat streaks down the front of the neck
            for a in range(2, 17, 3):
                p, q = cen[a], cen[a + 2]
                ink.seg(0.5, p[0], p[1], q[0], q[1])
        # head, bill, eye, crown and plume
        head = _cr(PP([(41.6, 9.6), (42.6, 6.6), (45.6, 5.2), (48.6, 6.0), (50.4, 7.6)]), 4)
        tip = P(67.5, 10.9)
        jaw = _cr(PP([(50.6, 10.6), (47.6, 11.9), (44.4, 12.6), (42, 11.6)]), 4)
        ink.mask(head + [tip] + jaw)
        ink.poly(1.0, head + [tip])
        ink.poly(0.5, [tip] + jaw)
        g0, g1 = P(49.4, 8.9), P(64, 10.5)
        ink.seg(1.0 if big else 0.5, g0[0], g0[1], g1[0], g1[1])
        ex, ey = P(47.2, 8.1)
        ink.dot(ex, ey)
        crown = _cr(PP([(47.6, 6.2), (44.6, 5.9), (41.4, 7.4), (37, 10.6), (33.4, 14.6), (31.2, 18.6)]), 5)
        n3 = len(crown) // 3
        ink.poly(1.5, crown[:n3 + 1])
        ink.poly(1.0, crown[n3:2 * n3 + 1])
        ink.poly(0.5, crown[2 * n3:])
        if big:
            ink.poly(0.5, _cr(PP([(41, 8.4), (36.4, 12.6), (34, 17.5)]), 5))

    # ---- near bank, reeds, drumsticks
    def bank_top(self, x):
        W, H, bh = self.w, self.h, self.bh
        y = H - bh * (0.62 + 0.5 * _vn(x / 37.0, 0.3, self.seed + 41))
        y -= bh * 1.1 * _smooth(W * 0.8, W * 0.94, x)             # the fir bank rises at the right
        y -= bh * 0.5 * _smooth(W * 0.16, W * 0.02, x)            # and a little under the reeds
        if self.var == "goodnight":
            d = abs(x - self.dogx) / (self.dogw * 0.6)
            if d < 1.5:
                y = min(y, self.dogy - 3.0 + 9.0 * _smooth(0.95, 1.5, d))
        return y

    def bank(self):
        """The near bank drawn as ground: contour strokes that follow its swell, a grassy lip,
        stones, a driftwood log, and the drumsticks lying among them."""
        ink, W, H, seed, bh = self.ink, self.w, self.h, self.seed, self.bh
        rng = random.Random("bank:%s" % seed)
        bt = self.bank_top
        top = []
        x = 0.0
        while x < W:
            top.append((x, bt(x)))
            x += 6.0
        top.append((W, bt(W)))
        ink.mask([(-2, top[0][1])] + top + [(W + 2, top[-1][1]), (W + 2, H + 3), (-2, H + 3)])
        mean = sum(p[1] for p in top) / len(top)
        bta = self.bta

        def tb(x, y):
            dd = y - bta[int(_clamp(x, 0, len(bta) - 1))]
            if dd < 0:
                return -1
            t = 0.3 + 0.55 * _smooth(0.0, 7.0, dd) + 0.5 * (_vn(x / 21.0, y / 6.0, seed + 43) - 0.45)
            return _clamp(t, 0.12, 1.0)

        ymin = min(p[1] for p in top) - 1
        g = _Grid(tb, 0, ymin, W, H + 1, 2.0)
        _engrave(ink, (0, ymin, W, H + 1), g,
                 [dict(ang=0, pitch=1.5, lo=0.0, gain=3.0, A=0.6, lam=25.0, pad=bh * 2.5,
                       warp=lambda sx, v: (bta[int(_clamp(sx, 0, len(bta) - 1))] - mean) * _clamp(1 - (v - mean) / (3.0 * bh), 0.25, 1.0)),
                  dict(ang=-34, pitch=1.5, lo=0.5, gain=5.5, A=0.6, lam=18.0),
                  dict(ang=52, pitch=1.5, lo=0.78, gain=8.0, cap=1, A=0.5, lam=18.0)], seed + 200,
                 inside=lambda x, y: y > bta[int(_clamp(x, 0, len(bta) - 1))] + 0.6)
        ink.swell(top, lambda t: 0.75 + 0.9 * _vn(t * 23.0, 0.5, seed + 44))
        dogz = (self.dogx, self.dogw * 0.62) if self.var == "goodnight" else (-999.0, 0.0)

        def clear(x, r=0.0):
            return abs(x - dogz[0]) > dogz[1] + r

        # driftwood: a bleached log with a snag, lying along the lip
        dl = _clamp(0.12 * W, 28.0, 76.0)
        dx0 = W * 0.305
        th0 = _clamp(bh * 0.4, 4.0, 8.0)
        ylog = min(bt(dx0 + dl * i / 6.0) for i in range(7)) - th0 * 0.15
        cen = [(dx0 + dl * i / 8.0, ylog + 2.2 * i / 8.0 + 1.0 * math.sin(i * 0.8)) for i in range(9)]
        Lp, Rp = _sweep(cen, lambda t: th0 * (1 - 0.55 * t))
        ink.mask(Lp + Rp[::-1])
        ink.poly(0.5, Rp)
        ink.swell(Lp, lambda t: 1.6 - 0.8 * t)
        ink.poly(0.5, [(x, y + 0.6) for x, y in cen[1:6]])
        ink.poly(0.5, [(x, y - th0 * 0.2) for x, y in cen[3:8]])
        ex, ey = cen[0]
        ink.raw(1.0, "M%s %sa%s %s 0 1 0 0 %s" % (_n(ex), _n(ey - th0 / 2), _n(th0 * 0.28), _n(th0 / 2), _n(th0)))
        sx_, sy_ = Rp[5]
        ink.swell([(sx_, sy_), (sx_ + th0 * 0.5, sy_ - th0 * 1.0), (sx_ + th0 * 0.4, sy_ - th0 * 1.9)], lambda t: 1.6 - 1.1 * t)
        ink.seg(0.5, sx_ + th0 * 0.5, sy_ - th0 * 1.0, sx_ + th0 * 1.3, sy_ - th0 * 1.5)
        self.log = (dx0, dx0 + dl)
        # stones
        ns = 5 + int(W / 80.0)
        for i in range(ns):
            x = rng.uniform(4, W - 4)
            rx = _clamp(bh * rng.uniform(0.18, 0.42), 2.5, 9.0)
            if not clear(x, rx + 3) or (dx0 - rx - 2 < x < dx0 + dl + rx + 2) or abs(x - W * 0.175) < 16 + rx:
                continue
            ry = rx * rng.uniform(0.5, 0.7)
            y = bt(x) + rng.uniform(0.2, 0.75) * max(2.0, (H - bt(x)) - ry - 1)
            ink.flush()
            ink.out.append('<path fill="#fff" stroke-width=".5" d="M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 %s 0z"/>'
                           % (_n(x - rx), _n(y), _n(rx), _n(ry), _n(2 * rx), _n(rx), _n(ry), _n(-2 * rx)))
            ink.raw(1.5, "M%s %sa%s %s 0 0 0 %s %s" % (_n(x - rx * 0.5), _n(y + ry * 0.87), _n(rx), _n(ry),
                                                       _n(rx * 1.5), _n(-ry * 0.87)))
            if rx > 4:
                ink.raw(0.5, "M%s %sq%s %s %s %s" % (_n(x + rx * 0.05), _n(y + ry * 0.5), _n(rx * 0.4), _n(-ry * 0.05),
                                                     _n(rx * 0.5), _n(-ry * 0.5)))
                ink.raw(0.5, "M%s %sq%s %s %s %s" % (_n(x - rx * 0.5), _n(y - ry * 0.35), _n(rx * 0.3), _n(-ry * 0.4),
                                                     _n(rx * 0.7), _n(-ry * 0.3)))
        # grass: every blade drawn, white-line where it crosses the dark ground, black against the water
        x = rng.uniform(1, 6)
        while x < W:
            if clear(x, 2) and not (dx0 - 2 < x < dx0 + dl + 2):
                root = bt(x) + rng.uniform(1.5, 0.75 * max(3.0, H - bt(x)))
                g_ = rng.uniform(5.0, 11.0) * (1.0 + 0.6 * self.tall)
                nb = rng.randint(4, 7)
                wl, bl = [], []
                for j in range(nb):
                    fan = (j - (nb - 1) / 2.0) / nb
                    hgt = g_ * rng.uniform(0.55, 1.0)
                    xa, ya = x + fan * 2.0, root
                    xb, yb = xa + fan * hgt * 1.2 + rng.uniform(-1, 1), root - hgt
                    lip = bt((xa + xb) / 2.0)
                    if yb >= lip:
                        wl.append((xa, ya, xb, yb))
                    else:
                        f = (ya - lip) / max(0.1, ya - yb)
                        xm, ym = xa + (xb - xa) * f, lip
                        if f > 0.05:
                            wl.append((xa, ya, xm, ym))
                        bl.append((xm, ym, xb, yb))
                ink.flush()
                d = "".join("M%s %sL%s %s" % (_n(a), _n(b), _n(c), _n(e)) for a, b, c, e in wl)
                ink.white(1, d)
                ink.ticks(0.5, bl[::2])
                ink.ticks(1.0, bl[1::2])
            x += rng.uniform(5.0, 13.0)
        # low broad leaves on the bank, light against the dark
        nl = 3 + int(W / 70.0)
        for i in range(nl):
            x = rng.uniform(6, W - 6)
            if not clear(x, 8) or (dx0 - 8 < x < dx0 + dl + 8) or abs(x - W * 0.175) < 18:
                continue
            y = bt(x) + rng.uniform(0.35, 0.8) * max(3.0, H - bt(x))
            for j in range(rng.randint(3, 5)):
                a = math.radians(rng.uniform(-160, -20))
                ln = rng.uniform(5.0, 9.0) * (1 + 0.4 * self.tall)
                self.leaf(x, y, x + math.cos(a) * ln * 0.5, y + math.sin(a) * ln * 0.7 - 1, x + math.cos(a) * ln,
                          y + math.sin(a) * ln * 0.75, _clamp(ln * 0.38, 2.0, 3.5), j % 2 == 0)
        # the drumsticks: two crossed sticks with acorn tips
        L = _clamp(0.03 * H + 13.0, 15.0, 20.0)
        cx = W * 0.175
        cy = min(bt(cx) + max(5.0, 0.45 * (H - bt(cx))), H - 4.5)
        ca, sa = math.cos(math.radians(24)), math.sin(math.radians(24))
        sticks = []
        for sg in (-1, 1):
            xa, ya = cx - sg * L * 0.5 * ca, cy + L * 0.5 * sa
            xb, yb = cx + sg * L * 0.5 * ca, cy - L * 0.5 * sa
            nx, ny = sa * 1.9, sg * ca * 1.9
            ex_, ey_ = (xb - xa) / L * 2.2, (yb - ya) / L * 2.2
            ink.mask([(xa - ex_ + nx, ya - ey_ + ny), (xb + ex_ + nx, yb + ey_ + ny), (xb + ex_ - nx, yb + ey_ - ny),
                      (xa - ex_ - nx, ya - ey_ - ny)])
            sticks.append((xa, ya, xb, yb))
        for xa, ya, xb, yb in sticks:
            mx_, my_ = xa + (xb - xa) * 0.6, ya + (yb - ya) * 0.6
            nx_, ny_ = xa + (xb - xa) * 0.88, ya + (yb - ya) * 0.88
            ink.seg(1.5, xa, ya, mx_, my_)
            ink.seg(1.0, mx_, my_, nx_, ny_)
            ink.flush()
            ink.out.append('<circle cx="%s" cy="%s" r="1.6" fill="#000" stroke="#fff" stroke-width=".5"/>'
                           % (_n(xa + (xb - xa) * 0.97), _n(ya + (yb - ya) * 0.97)))

    def leaf(self, x0, y0, cx, cy, x1, y1, wmax, dark):
        """One leaf: a tapering blade from (x0, y0) bending through (cx, cy) to its tip, paper-white
        with midrib; its shadowed half (or the whole of a leaf in shade) is lined."""
        ink = self.ink
        n = max(6, int((abs(x1 - x0) + abs(y1 - y0)) / 5.0) + 4)
        cen = []
        for i in range(n + 1):
            t = i / float(n)
            a, b, c = (1 - t) * (1 - t), 2 * t * (1 - t), t * t
            cen.append((a * x0 + b * cx + c * x1, a * y0 + b * cy + c * y1))

        def wf(t):
            return max(0.4, wmax * (1 - t ** 2.4) * (0.55 + 0.45 * min(1.0, t * 4.0)))

        L, R = _sweep(cen, wf)
        ink.mask(L + R[::-1], 0.5)
        if wmax >= 1.8:
            ink.poly(0.5, cen[:-1])
            for fr in ((0.5,) if not dark else (0.5, -0.5)):
                pts = [(cen[i][0] + (L[i][0] - cen[i][0]) * fr, cen[i][1] + (L[i][1] - cen[i][1]) * fr) for i in range(1, n - 1)]
                ink.poly(0.5, pts)
            if wmax >= 3.2:
                ink.poly(1.0, L[:n - 1])
        elif dark:
            ink.poly(1.0, cen)
        return cen

    def reeds(self):
        """Cattails and reeds, leaf by leaf; the tall clump at the left frames the scene."""
        ink, W, H = self.ink, self.w, self.h
        rng = random.Random("reeds:%s" % self.seed)
        top = _clamp(H * (0.62 - 0.27 * self.tall), 28.0, 190.0)   # tallest blade
        wm = _clamp(top * 0.034, 1.8, 5.0)

        def clump(x0, x1, n, hgt, heads, wmax):
            items = []
            for i in range(n):
                x = rng.uniform(x0, x1)
                items.append((rng.uniform(0.42, 1.0) * hgt, x, i))
            items.sort(reverse=True)
            for g, x, i in items:
                y = self.bank_top(x) + 4
                lean = rng.uniform(-0.3, 0.36) * g
                if i < heads and g > 16:
                    # a cattail: straight stalk, velvet head, spike
                    lean *= 0.3
                    xt, yt = x + lean, y - g
                    self.leaf(x, y, x + lean * 0.4, y - g * 0.5, xt, yt, max(1.0, wmax * 0.35), True)
                    Lh = _clamp(g * 0.13, 5.0, 13.0)
                    hw = _clamp(wmax * 0.55, 1.2, 2.6)
                    hx0, hy0 = x + lean * 0.8, y - g * 0.8
                    hx1, hy1 = hx0 + lean * 0.14, hy0 - Lh
                    Lp, Rp = _sweep([(hx0, hy0), ((hx0 + hx1) / 2, (hy0 + hy1) / 2), (hx1, hy1)], lambda t: 2 * hw)
                    ink.mask(Lp + Rp[::-1], 0.5)
                    for fr in (-0.55, 0.0, 0.55):
                        ink.seg(1.0 if fr >= 0 else 0.5, hx0 + fr * hw, hy0 - 0.5, hx1 + fr * hw, hy1 + 0.5)
                    ink.seg(0.5, hx1, hy1, hx1 + lean * 0.05, hy1 - Lh * 0.6)
                else:
                    droop = rng.random() < 0.3
                    if droop:
                        # a blade that has folded over
                        sg = 1 if lean >= 0 else -1
                        self.leaf(x, y, x + lean * 0.5, y - g * 1.15, x + lean + sg * g * 0.3, y - g * 0.62,
                                  wmax * rng.uniform(0.7, 1.0), rng.random() < 0.5)
                    else:
                        self.leaf(x, y, x + lean * 0.12, y - g * 0.62, x + lean, y - g, wmax * rng.uniform(0.6, 1.0),
                                  rng.random() < 0.45)

        clump(-2, W * 0.135, 12 + int(W / 40), top, 4, wm)
        if self.var != "goodnight":
            clump(W * 0.46, W * 0.52, 6, top * 0.36, 1, max(1.6, wm * 0.6))
        clump(W * 0.765, W * 0.815, 5, top * 0.32, 1, max(1.6, wm * 0.6))

    # ---- the dog, curled asleep (unit box 112 x 50, nose to the right)
    def dog_place(self):
        W, H = self.w, self.h
        self.dogw = min(_clamp(0.31 * W, 78.0, 176.0), 1.3 * H)
        self.dogx = W * (0.585 if W >= 400 else 0.52)
        self.dogy = H - max(3.0, self.bh * 0.4)                    # ground line under the dog

    def dog(self):
        """A medium mixed-breed dog curled asleep (unit box 140 x 64): head in profile at the right,
        chin on the forepaws, folded ear, closed eye; the back arcs over ribcage and haunch to the
        tail, which wraps along the front with its tip tucked by the nose. Moon-lit rim along the
        back; fur in short strokes that follow the body, black in the lights, white in the darks."""
        ink, seed = self.ink, self.seed
        rng = random.Random("dog:%s" % seed)
        sc = self.dogw / 140.0
        x0, y0 = self.dogx - self.dogw * 0.5, self.dogy

        def P(u, v):
            return (x0 + u * sc, y0 - (64 - v) * sc)

        def PP(pts):
            return [P(u, v) for u, v in pts]

        cn = 6 if sc > 0.7 else 4
        backK = [(8, 57), (5, 46), (8, 34), (18, 22), (34, 13), (52, 8.5), (70, 8), (84, 11.5), (92, 17.5), (95.5, 23)]
        skullK = [(95.5, 23), (99, 21.4), (104, 22.2), (108, 24.8), (110.2, 28.8)]
        muzK = [(110.2, 28.8), (114, 30), (121, 32.2), (128, 35), (131.8, 37.4), (132.6, 40.2), (131, 43.6), (128, 47.4)]
        pawK = [(128, 47.4), (133, 50.4), (137.6, 53.6), (138.8, 57.6), (136.4, 61.2), (131, 63), (122, 64)]
        underK = [(122, 64), (90, 64.4), (50, 64.4), (22, 63.6), (11, 61), (8, 57)]
        backU, skullU, muzU, pawU, underU = _cr(backK, cn), _cr(skullK, cn), _cr(muzK, cn), _cr(pawK, cn), _cr(underK, 3)
        outU = backU + skullU[1:] + muzU[1:] + pawU[1:] + underU[1:]
        earU = _cr([(93.6, 24.6), (98, 23.2), (102.8, 23), (104.6, 27.6), (102, 36), (98.6, 46), (95, 39), (92.6, 31), (93.6, 24.6)], cn)
        haunchK = [(20, 59), (14, 46.5), (18, 32.5), (30, 24.5), (44, 25.5), (54, 33.5), (57, 45), (52, 57)]
        haunchU = _cr(haunchK, cn)
        headU = [(92, 25), (99, 21.4), (104, 22.2), (108, 24.8), (110.2, 28.8), (121, 32.2), (131.8, 37.4), (132.6, 40.2),
                 (128, 47.4), (120, 50.4), (108, 52.6), (98, 52.2), (92.6, 45), (90.6, 34)]
        tailtab = [(8, 53), (22, 58), (44, 60.4), (66, 60.4), (86, 59.6), (104, 59), (120, 58), (129, 56.4)]
        backtab = [(5, 46), (8, 34), (18, 22), (34, 13), (52, 8.5), (70, 8), (84, 11.5), (92, 17.5), (96, 23)]
        headtop = [(92, 25), (99, 21.4), (104, 22.2), (108, 24.8), (110.2, 28.8), (121, 32.2), (131.8, 37.4)]
        # cast shadow on the ground, falling away from the moon
        for k, (a, b, wd) in enumerate(((2, 150, 1.5), (14, 148, 1.0), (34, 138, 0.5))):
            ink.seg(wd, x0 + a * sc, y0 + 1.2 + 2.5 * k, x0 + b * sc, y0 + 1.2 + 2.5 * k)
        ink.mask(PP(outU))
        # ---- the coat
        gs = 1.8 / sc
        coat = {0.5: [], 1.0: [], 1.5: []}
        cuts = []
        v, row = 5.0, 0
        while v < 64:
            u = 4.0 + (row % 2) * gs * 0.5
            while u < 136:
                uu, vv = u + rng.uniform(-0.3, 0.3) * gs, v + rng.uniform(-0.3, 0.3) * gs
                u += gs
                if not _inside(outU, uu, vv) or _inside(earU, uu, vv):
                    continue
                tt = _interp(tailtab, uu)
                if vv > tt + 0.8 and uu < 130:
                    ang = math.atan2(_interp(tailtab, uu + 4) - _interp(tailtab, uu - 4), 8.0) + 0.35
                    shade = (0.08 + 0.42 * (vv - tt) / max(1.0, 64.5 - tt)) * (0.4 if uu > 100 else 1.0)
                elif uu > 100 and vv > 53.0:
                    continue                                           # forepaws: drawn, not furred
                elif _inside(headU, uu, vv):
                    ang = 0.38 + 0.5 * _smooth(36, 48, vv)
                    dtop = vv - _interp(headtop, uu)
                    shade = 0.03 + 0.34 * _smooth(10.0, 20.0, dtop)
                    if uu < 100:
                        shade += 0.1                                   # behind the ear, into the ruff
                    if abs(uu - 110) < 6.5 and abs(vv - 31.5) < 4.5:
                        shade = 0.0
                    if uu > 116 and dtop < 7:
                        shade = 0.0                                    # the lit top of the muzzle
                elif _inside(haunchU, uu, vv):
                    dx, dy = uu - 36.0, vv - 42.0
                    f = math.hypot(dx / 21.0, dy / 17.0)
                    ang = math.atan2(dx / 441.0, -dy / 289.0)
                    shade = 0.04 + 0.78 * _smooth(0.5, 1.05, f) * (0.2 if (dy < -1 and dx < 9) else 1.0)
                else:
                    dx, dy = uu - 52.0, vv - 62.0
                    yb = _interp(backtab, uu)
                    db = (vv - yb) / max(1.0, 60 - yb)
                    ang = math.atan2(dx / 2400.0, -dy / 2900.0) + 0.35 * _smooth(0.3, 0.9, db)
                    shade = 0.0 if db < 0.11 else 0.06 + 0.72 * _smooth(0.16, 0.9, db)
                    if 56 < uu < 84 and vv > 40:
                        shade += 0.16                                  # the hollow under the ribs
                    if uu > 84:
                        shade = shade * 0.7 + (0.25 if vv > 44 else 0.0)
                    if vv > tt - 5:
                        shade += 0.14                                  # shadow thrown on the tail
                    if 54 < uu < 82 and 0.25 < db < 0.75:
                        shade += 0.14 * math.sin((uu - 54) * 1.05)     # the ribs, felt under the coat
                if rng.random() > min(0.97, shade * 1.3):
                    continue
                wd = 0.5 if shade < 0.45 else (1.0 if shade < 0.85 or sc < 0.7 else 1.5)
                a = ang + rng.uniform(-0.22, 0.22)
                ln = (3.0 + 2.4 * rng.random()) * 0.5
                px, py = P(uu, vv)
                ca_, sa_ = math.cos(a) * ln, math.sin(a) * ln
                coat[wd].append((px - ca_, py - sa_, px + ca_, py + sa_))
                if shade > 0.6 and rng.random() < 0.45:
                    cuts.append("M%s %sL%s %s" % (_n(px - ca_ + 1.2 * sa_ / ln), _n(py - sa_ - 1.2 * ca_ / ln),
                                                  _n(px + ca_ * 0.8 + 1.2 * sa_ / ln), _n(py + sa_ * 0.8 - 1.2 * ca_ / ln)))
            v += gs * 0.85
            row += 1
        for wd in (0.5, 1.0, 1.5):
            ink.ticks(wd, coat[wd])
        ink.white(0.5, "".join(cuts))
        # ---- the masses
        # spine, glimpsed as a broken ridge under the lit rim
        sp = []
        u = 14.0
        while u < 88:
            sp.append(P(u, _interp(backtab, u) + 3.4) + P(u + 3.2, _interp(backtab, u + 3.2) + 3.4))
            u += 5.2
        ink.ticks(0.5, sp)
        ink.swell(PP(haunchU), lambda t: 0.5 + 1.1 * _smooth(0.35, 0.8, t))
        hp = _cr(PP([(52, 57), (62, 53), (74, 53.6), (82, 57.8)]), cn)
        ink.swell(hp, lambda t: 1.0 - 0.4 * t)
        ink.ticks(0.5, [P(u_, 54.4) + P(u_ + 0.9, 57.6) for u_ in (75.5, 78.5, 81.0)])
        ink.swell(_cr(PP([(81, 47), (78.4, 35), (82, 23.5), (90, 17.5)]), cn), lambda t: 1.1 - 0.6 * t)
        ink.poly(0.5, _cr(PP([(82, 50), (92, 52.4), (103, 53.6)]), cn))
        tail = _cr(PP(tailtab), cn)
        ink.swell(tail, lambda t: 1.0 + 0.4 * math.sin(math.pi * t))
        ink.poly(1.0, _cr(PP([(129, 56.4), (132.6, 58.6), (131, 62.8)]), 3))
        # collar
        for du in (0.0, 3.4):
            ink.poly(1.0, _cr(PP([(91.4 - du, 17.6), (88.2 - du, 29), (89.2 - du, 41), (93 - du, 51)]), 3))
        # ---- the head
        ear = PP(earU)
        ink.mask(ear)
        tipx, tipy = 98.6, 45.4
        for i in range(9):
            f = i / 8.0
            a_ = (94.0 + 9.8 * f, 27.6 + 1.4 * f - 2.0 * math.sin(math.pi * f) * 0.3)
            mid = (a_[0] * 0.5 + tipx * 0.5 + (f - 0.5) * 4.4, a_[1] * 0.5 + tipy * 0.5)
            end = (a_[0] * 0.1 + tipx * 0.9 + (f - 0.5) * 1.4, a_[1] * 0.1 + tipy * 0.9)
            ln_ = _cr(PP([a_, mid, end]), 4)
            if f > 0.8:
                ink.poly(0.5, ln_[:-1])
            else:
                ink.swell(ln_, lambda t: 1.0 if t < 0.8 else 0.5)
        ink.swell(ear, lambda t: 0.7 + 0.8 * math.sin(math.pi * t))
        ink.swell(_cr(PP([(106.6, 30.6), (109.6, 33.8), (114, 32.2)]), 5), lambda t: 0.6 + 1.1 * math.sin(math.pi * t))
        ink.ticks(0.5, [P(108.4, 33.4) + P(107.6, 35.4), P(110.6, 34) + P(110.6, 36), P(112.6, 33.2) + P(113.4, 35)])
        ink.poly(0.5, _cr(PP([(106, 27.4), (109.6, 26.2), (113.2, 27.8)]), 4))
        ink.poly(0.5, _cr(PP([(131, 43.6), (125, 44.4), (118, 43.4), (113.6, 40.8)]), 4))
        ink.poly(0.5, _cr(PP([(113.6, 40.8), (110, 44.2), (106, 46.8)]), 4))
        ink.swell(_cr(PP([(128, 47.4), (118, 49.8), (106, 51.8), (98, 51.2)]), 4), lambda t: 1.0 - 0.5 * t)
        for u_, v_ in ((122, 39.4), (125, 41), (120.6, 41.6), (127.4, 39.2)):
            px, py = P(u_, v_)
            ink.dot(px, py)
        # forepaws under the chin
        ink.poly(0.5, _cr(PP([(110, 53), (124, 55.4), (137.4, 56.4)]), 4))
        ink.ticks(0.5, [P(u_, 51.6) + P(u_ + 0.8, 54.6) for u_ in (132.4, 134.8, 136.8)]
                  + [P(u_ - 1, 57.4) + P(u_ - 0.2, 60.2) for u_ in (133.4, 135.6, 137.4)])
        # outline: hairline along the moonlit back, heavy underneath
        ink.swell(PP(backU), lambda t: 1.1 - 0.6 * math.sin(math.pi * min(1.0, t * 1.2)))
        ink.poly(1.0, PP(skullU))
        ink.poly(1.0, PP(muzU))
        ink.poly(1.0, PP(pawU))
        ink.poly(1.5, PP(underU))
        nx, ny = P(131.0, 38.9)
        ink.flush()
        ink.out.append('<circle cx="%s" cy="%s" r="%s" fill="#000" stroke="none"/>' % (_n(nx), _n(ny), _n(_clamp(2.5 * sc, 1.3, 3.0))))

    # ---- assemble
    def render(self):
        ink = self.ink
        if self.var == "goodnight":
            self.dog_place()
        self.place_firs()
        nW = int(self.w) + 3
        self.hoodarr, self.sk, self.bta, self.hoodonly = [], [], [], []
        for i in range(nW):
            m = self.hood(float(i))
            hl = self.hills(float(i))
            self.hoodarr.append(hl if m is None else min(hl, m))
            self.hoodonly.append(self.hz + 2.0 if m is None else m)
            self.sk.append(hl)
            self.bta.append(self.bank_top(float(i)))
        self.sky()
        self.stars()
        self.mountain()
        self.treeline()
        self.water()
        self.ripples()
        self.ship()
        for k in (2, 1, 0):
            if k < len(self.firs):
                fx, ty, hw, by = self.firs[k]
                self.fir(fx, ty, hw, by, k)
        self.heron()
        self.bank()
        self.reeds()
        if self.var == "goodnight":
            self.dog()
        ink.flush()
        return '<g fill="none" stroke="#000">' + "".join(ink.out) + "</g>"



def scene(w, h, seed=0, variant="dusk", moon_phase=0.5, **kw):
    """Engraved Columbia River scene as SVG child markup filling a w x h box edge to edge."""
    w = max(60.0, float(w))
    h = max(40.0, float(h))
    if moon_phase is None:
        moon_phase = 0.5
    return _Scene(w, h, seed, variant, moon_phase).render()
