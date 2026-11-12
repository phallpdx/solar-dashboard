"""Engraved vignettes for the Kindle Evening Edition: a jazz drum kit and a Thai lotus pond.

scene(w, h, seed=0, variant="jazz") -> SVG child markup (no outer <svg>, no frame) that fills a
w x h box edge to edge with engraved tone; the caller clips it into its cartouche.

Both plates are built the way scene_city.py builds its plates, so that they read as one hand: a
tone field (0 paper .. 1 black) is cut in layers by families of lines whose weight swells and
breaks with the tone, and the drawn subjects stand luminous on it, with white-line detail cut
back into the darks.  Output is meant to be thresholded to 1-bit at 2x: black strokes are 0.5 /
1 / 1.5 px, white-line strokes any multiple of 0.5, hatch pitch >= 1.5, coordinates to one
decimal; clip-paths only (no transforms, filters, masks, gradients or text).

Standard library only; imports nothing from the rest of the package.
"""
import math
import random

PI = math.pi


# ---------------------------------------------------------------- number / path helpers
def _n(v):
    s = "%.1f" % v
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return "0" if s in ("-0", "") else s


def _pl(pts, close=False):
    """Absolute move, then relative lines between rounded points (compact)."""
    r = [(int(round(x * 10)), int(round(y * 10))) for x, y in pts]
    out = ["M%s %s" % (_n(r[0][0] / 10.0), _n(r[0][1] / 10.0))]
    rel = []
    for (ax, ay), (bx, by) in zip(r, r[1:]):
        if (ax, ay) != (bx, by):
            dx, dy = _n((bx - ax) / 10.0), _n((by - ay) / 10.0)
            rel.append(dx + ("" if dy.startswith("-") else " ") + dy)
    if rel:
        out.append("l" + " ".join(rel).replace(" -", "-"))
    elif not close:
        out.append("h0")
    return "".join(out) + ("z" if close else "")


def _q(a, b, c, n=8, t0=0.0, t1=1.0):
    out = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / float(n)
        u = 1 - t
        out.append((u * u * a[0] + 2 * u * t * b[0] + t * t * c[0],
                    u * u * a[1] + 2 * u * t * b[1] + t * t * c[1]))
    return out


def _ell(cx, cy, rx, ry, a0=0.0, a1=2 * PI, rot=0.0, n=None):
    if n is None:
        n = int(max(6, min(40, (rx + ry) * abs(a1 - a0) / 7.0)))
    cr, sr = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / float(n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out


def _E(cx, cy, rx, ry, rot=0.0):
    """Closed ellipse as two arc commands (rot in degrees is the arc's own axis rotation)."""
    rx, ry = max(0.1, round(rx, 1)), max(0.1, round(ry, 1))
    a = math.radians(rot)
    dx, dy = rx * math.cos(a), rx * math.sin(a)
    return "M%s %sa%s %s %s 1 0 %s %sa%s %s %s 1 0 %s %sz" % (
        _n(cx - dx), _n(cy - dy), _n(rx), _n(ry), _n(rot), _n(2 * dx), _n(2 * dy),
        _n(rx), _n(ry), _n(rot), _n(-2 * dx), _n(-2 * dy))


def _arc(cx, cy, rx, ry, a0, a1, rot=0.0):
    """Elliptical arc from angle a0 to a1 (radians, y down) as one A command."""
    rr = math.radians(rot)
    cr, sr = math.cos(rr), math.sin(rr)

    def P(a):
        x, y = rx * math.cos(a), ry * math.sin(a)
        return (cx + x * cr - y * sr, cy + x * sr + y * cr)
    a, b = P(a0), P(a1)
    return "M%s %sA%s %s %s %d %d %s %s" % (_n(a[0]), _n(a[1]), _n(rx), _n(ry), _n(rot),
                                             1 if abs(a1 - a0) > PI else 0, 1 if a1 > a0 else 0,
                                             _n(b[0]), _n(b[1]))


def _qd(a, b, c, t0=0.0, t1=1.0):
    """Quadratic curve (optionally the sub-span t0..t1) as one Q command."""
    if t0 != 0.0 or t1 != 1.0:
        def at(t):
            u = 1 - t
            return (u * u * a[0] + 2 * u * t * b[0] + t * t * c[0], u * u * a[1] + 2 * u * t * b[1] + t * t * c[1])

        def lerp(p, q, t):
            return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        m = lerp(lerp(a, b, t0), lerp(b, c, t0), t1)
        a, b, c = at(t0), m, at(t1)
    return "M%s %sQ%s %s %s %s" % (_n(a[0]), _n(a[1]), _n(b[0]), _n(b[1]), _n(c[0]), _n(c[1]))


def _soft(ys, w, cx, cy, rx, ry, rng, jit=8.0):
    """Horizontal ruling that stops raggedly short of an ellipse: a soft-edged pool of light."""
    seg = []
    for y in ys:
        k = 1 - ((y - cy) / ry) ** 2
        if k <= 0:
            seg.append("M0 %sh%s" % (_n(y), _n(w)))
            continue
        half = rx * math.sqrt(k)
        xl = cx - half - rng.uniform(-jit, jit)
        xr = cx + half + rng.uniform(-jit, jit)
        if xl > 2:
            seg.append("M0 %sh%s" % (_n(y), _n(xl)))
        if xr < w - 2:
            seg.append("M%s %sh%s" % (_n(xr), _n(y), _n(w - xr)))
    return "".join(seg)


def _snap(v, p=0.5):
    return round(v / p) * p


def _hat(box, pitch, ang=0.0, off=0.0):
    """Parallel lines at `ang` degrees covering box, on a global grid of `pitch`."""
    x0, y0, x1, y1 = box
    if x1 - x0 < 0.5 or y1 - y0 < 0.5:
        return ""
    if ang in (0, 90):                       # whole-pixel extents: these ends are clipped or butt
        x0, y0, x1, y1 = math.floor(x0), math.floor(y0), math.ceil(x1), math.ceil(y1)
    if ang == 0:
        y = math.ceil(y0 / pitch) * pitch + off
        seg = []
        while y <= y1:
            seg.append("M%s %sh%s" % (_n(x0), _n(y), _n(x1 - x0)))
            y += pitch
        return "".join(seg)
    if ang == 90:
        x = math.ceil(x0 / pitch) * pitch + off
        seg = []
        while x <= x1:
            seg.append("M%s %sv%s" % (_n(x), _n(y0), _n(y1 - y0)))
            x += pitch
        return "".join(seg)
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cs = [x * nx + y * ny for x in (x0, x1) for y in (y0, y1)]
    c = math.floor(min(cs) / pitch) * pitch + off
    seg = []
    while c <= max(cs):
        px, py = c * nx, c * ny
        t0, t1 = -1e9, 1e9
        for p, d, lo, hi in ((px, dx, x0, x1), (py, dy, y0, y1)):
            ta, tb = (lo - p) / d, (hi - p) / d
            t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
        if t1 - t0 > 1.0:
            ax, ay = round(px + t0 * dx, 1), round(py + t0 * dy, 1)
            bx, by = round(px + t1 * dx, 1), round(py + t1 * dy, 1)
            dy_ = _n(by - ay)
            seg.append("M%s %sl%s%s%s" % (_n(ax), _n(ay), _n(bx - ax), "" if dy_[0] == "-" else " ", dy_))
        c += pitch
    return "".join(seg)


def _fade(box, pitch, ang, tone, rng, step=5.0):
    """Hatching with no edge: each line is broken into strokes that thin out and stop as
    tone(x, y) (0..1) falls away."""
    x0, y0, x1, y1 = box
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cs = [x * nx + y * ny for x in (x0, x1) for y in (y0, y1)]
    c = math.floor(min(cs) / pitch) * pitch
    out = []
    while c <= max(cs):
        px, py = c * nx, c * ny
        t0, t1 = -1e9, 1e9
        for p_, d_, lo, hi in ((px, dx, x0, x1), (py, dy, y0, y1)):
            if abs(d_) < 1e-9:
                if p_ < lo or p_ > hi:
                    t0, t1 = 1.0, 0.0
                continue
            ta, tb = (lo - p_) / d_, (hi - p_) / d_
            t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
        t = t0
        run = None
        while t < t1:
            te = min(t1, t + step * rng.uniform(0.6, 1.4))
            tm = (t + te) / 2
            if tone(px + tm * dx, py + tm * dy) > rng.random():
                run = (run[0] if run else t, te)
            elif run:
                out.append(run)
                run = None
            t = te
        if run:
            out.append(run)
        for ra, rb in out:
            pass
        if out:
            yield_ = "".join("M%s %sL%s %s" % (_n(px + ra * dx), _n(py + ra * dy), _n(px + rb * dx), _n(py + rb * dy))
                             for ra, rb in out)
            _fade.acc.append(yield_)
            out = []
        c += pitch
    r = "".join(_fade.acc)
    _fade.acc = []
    return r


_fade.acc = []


def _ezone(cx, cy, rx, ry, soft=0.5):
    """Tone that is 0 inside an ellipse and rises to 1 over `soft` radii beyond it."""
    def f(x, y):
        d = math.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
        return max(0.0, min(1.0, (d - 1.0) / soft))
    return f


def _R(x0, y0, x1, y1):
    return "M%s %sH%sV%sH%sz" % (_n(x0), _n(y0), _n(x1), _n(y1), _n(x0))


def _bbox(pts, pad=0.0):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ---------------------------------------------------------------- the burin (tone cut in layers)
# These helpers follow scene_city.py so that all the plates read as one hand: a tone field
# (0 paper .. 1 black) is cut by families of lines whose weight swells and breaks with it.

def _f(v):
    s = '%.1f' % v
    if s.endswith('.0'):
        s = s[:-2]
    if s in ('-0', ''):
        return '0'
    if s.startswith('0.'):
        s = s[1:]
    elif s.startswith('-0.'):
        s = '-' + s[2:]
    return s


def _r(v):
    return round(v * 10) / 10.0


def _j(a, b):
    sb = _f(b)
    return _f(a) + ('' if sb[0] == '-' else ' ') + sb


def _cl(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


class _P(object):
    """Path data accumulator: runs in relative steps, rounded cumulatively so nothing drifts."""

    tol = 0.22

    def __init__(self):
        self.d = []
        self.x = self.y = None

    def run(self, pts, close=False):
        q = [pts[0]]
        a = 0
        n = len(pts)
        while a < n - 1:
            b = a + 1
            while b + 1 < n:
                ax, ay = pts[a]
                cx, cy = pts[b + 1]
                L = math.hypot(cx - ax, cy - ay) + 1e-9
                ok = True
                for m in range(a + 1, b + 1):
                    if abs((pts[m][0] - ax) * (cy - ay) - (pts[m][1] - ay) * (cx - ax)) / L > self.tol:
                        ok = False
                        break
                if not ok:
                    break
                b += 1
            q.append(pts[b])
            a = b
        x0, y0 = _r(q[0][0]), _r(q[0][1])
        if self.x is None or close:
            s = 'M' + _j(x0, y0)
        else:
            s = 'm' + _j(_r(x0 - self.x), _r(y0 - self.y))
        px, py = x0, y0
        if len(q) == 1:
            s += 'h0'
        for x, y in q[1:]:
            dx, dy = _r(x - px), _r(y - py)
            if dx == 0 and dy == 0:
                continue
            if dy == 0:
                s += 'h' + _f(dx)
            elif dx == 0:
                s += 'v' + _f(dy)
            else:
                s += 'l' + _j(dx, dy)
            px, py = _r(px + dx), _r(py + dy)
        if close:
            s += 'z'
            self.x = self.y = None
        else:
            self.x, self.y = px, py
        self.d.append(s)

    def dot(self, x, y):
        self.run([(x, y)])

    def s(self):
        return ''.join(self.d)


def _stroke(d, w):
    return '<path d="%s" stroke-width="%s"/>' % (d, _f(w)) if d else ''


def _hl(x0, x1, y, step=3.0):
    n = max(1, int(math.ceil((x1 - x0) / step)))
    return [(x0 + (x1 - x0) * i / n, y) for i in range(n + 1)]


def _vl(x, y0, y1, step=2.0):
    n = max(1, int(math.ceil((y1 - y0) / step)))
    return [(x, y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def _hfam(x0, x1, y0, y1, pitch, step=3.0):
    out = []
    y = y0
    while y <= y1:
        out.append(_hl(x0, x1, y, step))
        y += pitch
    return out


def _vfam(x0, x1, y0, y1, pitch, step=2.0):
    out = []
    x = x0
    while x <= x1:
        out.append(_vl(x, y0, y1, step))
        x += pitch
    return out


def _dfam(box, ang, pitch, step=2.0):
    """Parallel straight lines at angle ang (degrees) covering box, perpendicular pitch."""
    x0, y0, x1, y1 = box
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cs = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    on = [c[0] * nx + c[1] * ny for c in cs]
    ot = [c[0] * dx + c[1] * dy for c in cs]
    out = []
    o = math.floor(min(on) / pitch) * pitch + pitch / 2.0
    while o < max(on):
        pts = []
        t = min(ot)
        while t <= max(ot) + step:
            x, y = o * nx + t * dx, o * ny + t * dy
            if x0 - step <= x <= x1 + step and y0 - step <= y <= y1 + step:
                pts.append((x, y))
            t += step
        if len(pts) > 1:
            out.append(pts)
        o += pitch
    return out


def _bis(a, b, tone):
    """a is inked, b is not: the last inked point toward b."""
    for _ in range(5):
        m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        if tone(m[0], m[1]) > 0:
            a = m
        else:
            b = m
    return a


def _rule(lines, tone, pitch, rng, cap=None, lo=0.4, cell=7.0, soft=False, dith=True):
    """The burin: each line is cut at 0.5 / 1 / 1.5 px according to tone (0 paper .. 1 black) or
    lifted where the tone runs out (broken dashes in faint tone, exact edges where tone is 0)."""
    if cap is None:
        cap = min(1.5, math.floor((pitch - 0.5) * 2) / 2.0)
    acc = {0.5: _P(), 1.0: _P(), 1.5: _P()}
    for pts in lines:
        n = len(pts)
        if n < 2:
            continue
        nz = [rng.random() for _ in range(32)]
        off = rng.randrange(32)
        ts, qs, dist = [], [], 0.0
        for i, (x, y) in enumerate(pts):
            if i:
                dist += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
            t = tone(x, y)
            ts.append(t)
            w = t * pitch
            if soft:        # weight tapers and the line breaks progressively: no hard step
                r = nz[(int(dist / cell) + off) % 32]
                r2 = r if dith else 0.5
                if w >= 1.4:
                    q = 1.5
                elif w >= 1.2:
                    q = 1.5 if r2 < (w - 1.2) / 0.2 else 1.0
                elif w >= 0.9:
                    q = 1.0
                elif w >= 0.68:
                    q = 1.0 if r2 < (w - 0.68) / 0.22 else 0.5
                elif w >= 0.45:
                    q = 0.5
                elif w > 0.03 and r < (w / 0.45) ** 1.2:
                    q = 0.5
                else:
                    q = 0.0
            elif w >= 1.25:
                q = 1.5
            elif w >= 0.75:
                q = 1.0
            elif w >= lo:
                q = 0.5
            elif w > 0.03 and nz[(int(dist / cell) + off) % 32] < (w / lo) ** 1.5:
                q = 0.5
            else:
                q = 0.0
            qs.append(min(q, cap))
        run, rq = [], 0.0
        for i in range(n):
            q = qs[i]
            if i == 0:
                if q:
                    run, rq = [pts[0]], q
                continue
            if q == rq:
                if q:
                    run.append(pts[i])
                continue
            a, b = pts[i - 1], pts[i]
            if rq and q:
                m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                run.append(m)
                acc[rq].run(run)
                run = [m, b]
            elif rq:
                if ts[i] <= 0:
                    e = _bis(a, b, tone)
                    if e != a:
                        run.append(e)
                if len(run) > 1:
                    acc[rq].run(run)
                run = []
            else:
                if ts[i - 1] <= 0:
                    s0 = _bis(b, a, tone)
                    run = [s0, b] if s0 != b else [b]
                else:
                    run = [b]
            rq = q
        if rq and len(run) > 1:
            acc[rq].run(run)
    return ''.join(_stroke(acc[w].s(), w) for w in (0.5, 1.0, 1.5))


def _grid(fn, x0, y0, x1, y1, cell):
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


def _wfam(x0, x1, y0, y1, pitch, step=3.0, a1=2.5, l1=70.0, a2=1.2, l2=29.0):
    """Near-horizontal lines that undulate together, as a hand lays a tint."""
    out = []
    y = y0
    n = int((x1 - x0) / step) + 1
    while y <= y1:
        out.append([(x0 + i * step, y + a1 * math.sin((x0 + i * step) / l1 + y / 23.0) + a2 * math.sin((x0 + i * step) / l2 - y / 11.0))
                    for i in range(n + 1)])
        y += pitch
    return out


def _bend(lines, amp=1.5, wl=40.0):
    return [[(x, y + amp * math.sin(x / wl + y / (wl * 1.3))) for x, y in ln] for ln in lines]


def _adw(i, p, t, pm=1.5, gap=0.5):
    """Weight for line i of a family whose spacing p changes along it (lines converging to a
    vanishing point, rings closing up at a silhouette): where the lines crowd, every second or
    fourth one carries the tone and the rest are lifted, so the gap never closes."""
    for k in (1, 2, 4):
        if p * k >= pm:
            if i % k:
                return 0.0
            e = p * k
            return min(t * e, e - gap)
    return 0.0


def _knots(kn, v):
    for (a, ta), (b, tb) in zip(kn, kn[1:]):
        if v <= b:
            return ta + (tb - ta) * (v - a) / (b - a)
    return kn[-1][1]


class _C:
    """Canvas: ordered paths; consecutive strokes of the same weight and clip are merged."""

    def __init__(self, pre):
        self.o, self.pre, self.k, self.cur = [], pre, 0, {}

    def flush(self):
        for (w, cl), ds in self.cur.items():
            sw = _n(w)
            a = ' clip-path="url(#%s)"' % cl if cl else ""
            sw = "" if w == 0.5 else ' stroke-width="%s"' % sw          # .5 is the group default
            self.o.append('<path%s%s d="%s"/>' % (sw, a, "".join(ds)))
        self.cur = {}

    def d(self, d, w=0.5, clip=None):
        # black strokes never hide one another, so everything between two white shapes is
        # pooled by (weight, clip) into a single path
        if d:
            self.cur.setdefault((w, clip), []).append(d)

    def line(self, pts, w=0.5, close=False, clip=None):
        if len(pts) > 1:
            self.d(_pl(pts, close), w, clip)

    def mask(self, d):
        self.flush()
        self.o.append('<path fill="#fff" stroke="none" d="%s"/>' % d)

    def ink(self, d):
        self.flush()
        self.o.append('<path fill="#000" stroke="none" d="%s"/>' % d)

    def white(self, d, clip=None, w=0.5):
        """White-line work cut into a dark passage."""
        self.flush()
        self.o.append('<path stroke="#fff" stroke-width="%s"%s d="%s"/>' % (_n(_snap(w)), ' clip-path="url(#%s)"' % clip if clip else "", d))

    def raw(self, markup):
        self.flush()
        self.o.append(markup)

    def clip(self, d, eo=False):
        self.k += 1
        cid = "%s%d" % (self.pre, self.k)
        self.o.append('<clipPath id="%s"><path %sd="%s"/></clipPath>'
                      % (cid, 'clip-rule="evenodd" ' if eo else "", d))
        return cid

    def open(self, cid):
        self.flush()
        self.o.append('<g clip-path="url(#%s)">' % cid)

    def close(self):
        self.flush()
        self.o.append("</g>")

    def dots(self, pts, w=1.0):
        self.d("".join("M%s %sh0" % (_n(x), _n(y)) for x, y in pts), w)

    def shape(self, pts, w=1.0):
        """Paper-white silhouette with an outline: occludes what lies behind."""
        d = pts if isinstance(pts, str) else _pl(pts, True)
        self.flush()
        self.o.append('<path fill="#fff"%s d="%s"/>' % ({0.5: "", 1.0: ' stroke-width="1"', 1.5: ' stroke-width="1.5"'}[w], d))
        return d


# ====================================================================== JAZZ
def _lug(C, x, b0, b1, ww):
    """Cast lug: a slim bevelled casing, lit on its face, a shadow down one flank, one screw."""
    ww = min(ww, 2.0)
    C.shape([(x - ww, b0 + 1), (x - ww + 1, b0), (x + ww - 1, b0), (x + ww, b0 + 1), (x + ww, b1 - 1),
             (x + ww - 1, b1), (x - ww + 1, b1), (x - ww, b1 - 1)], 0.5)
    C.d("M%s %sV%s" % (_n(x + ww), _n(b0 + 1), _n(b1 - 1)), 1.0)
    C.dots([(x, (b0 + b1) / 2.0)], 1.0)


def _drum(C, cx, ty, rx, ry, dep, nl=5, light=-0.5, snare=False):
    """Upright drum seen from slightly above: head ellipse, shell with vertical contour ruling
    that packs toward the turning edges, ring cross-hatch in the shadow, hoops, lugs and rods."""
    cx = _snap(cx)
    sil = _ell(cx, ty, rx, ry, PI, 2 * PI) + _ell(cx, ty + dep, rx, ry, 0, PI)
    C.mask(_pl(sil, True))
    # the shell is turned with rings that run round it, parallel to the hoops: open on the band
    # of light, swelling to near black on the far flank, with a breath of reflected light at the edge
    rg = random.Random(int(cx * 7 + ty * 13 + rx))

    def tn(th):
        d_ = th - light
        if d_ < 0:
            return 0.6 * _cl((-d_ - 0.2) / 0.9) ** 1.2
        return 0.97 * _cl((d_ - 0.2) / 1.15) ** 0.9 - 0.3 * _cl((th - 1.22) / 0.3)

    def tone(x, y):
        th = math.asin(_cl((x - cx) / rx, -1.0, 1.0))
        t = tn(th)
        return _cl(t * (0.82 + 0.36 * (y - ty - ry * math.cos(th)) / dep))
    na = max(14, int(rx * 1.3))
    ths = [-PI / 2 + 0.04 + (PI - 0.08) * i / float(na) for i in range(na + 1)]
    rings = []
    yy = 3.5
    while yy < dep - 2.4:
        rings.append([(cx + rx * math.sin(t_), ty + yy + ry * math.cos(t_)) for t_ in ths])
        yy += 2.0
    C.raw(_rule(rings, tone, 2.0, rg, soft=True))
    gen = []
    x = 0.0
    while x < rx - 1.5:                                  # a few generators cross the rings in the dark
        th = math.asin(x / rx)
        if tn(th) > 0.5:
            y0 = ty + ry * math.cos(th)
            gen.append([(cx + x, y0 + 2.5 + q_ * (dep - 4.5) / 4.0) for q_ in range(5)])
        x += 2.5
    C.raw(_rule(gen, lambda x_, y_: _cl((tone(x_, y_) - 0.5) * 1.2), 2.5, rg, cap=0.5, soft=True))
    # lugs and tension rods
    lw = max(1.0, rx * 0.06)
    if rx < 18 and nl > 4:
        nl = 4
    for i in range(nl):
        th = -1.2 + 2.4 * i / max(1, nl - 1)
        x = cx + rx * math.sin(th)
        yb = ty + ry * math.cos(th)
        ww = max(1.0, lw * math.cos(th) + 0.5)
        C.d("M%s %sv%s" % (_n(x), _n(yb + 2), _n(dep - 3)), 0.5)
        b0, b1 = yb + dep * 0.34, yb + dep * 0.66
        if rx >= 18 and ww >= 1.5:
            _lug(C, x, b0, b1, ww)
        else:
            C.d(_R(x - ww, b0, x + ww, b1), 1.0 if ww < 1.6 else 0.5)
        if rx >= 18:
            C.d("M%s %sh%s" % (_n(x - ww), _n(yb + 2.5), _n(2 * ww)), 1.0)
            C.d("M%s %sh%s" % (_n(x - ww), _n(yb + dep - 1.5), _n(2 * ww)), 1.0)
    if nl and rx >= 14:                              # maker's badge and air vent between the lugs
        byy = ty + ry + dep * 0.5
        C.mask(_E(cx, byy, max(2.5, rx * 0.1), max(2.0, min(dep * 0.16, rx * 0.08))))
        C.d(_E(cx, byy, max(2.5, rx * 0.1), max(2.0, min(dep * 0.16, rx * 0.08))), 0.5)
        C.dots([(cx, byy)], 1.0)
    if snare:                                        # strainer and the ends of the snare wires
        th = 0.48
        x = cx + rx * math.sin(th)
        yb = ty + ry * math.cos(th)
        C.mask(_R(x - 2, yb + dep * 0.35, x + 2, yb + dep - 1))
        C.d(_R(x - 2, yb + dep * 0.35, x + 2, yb + dep - 1), 0.5)
        C.d("M%s %sl2.5 -%s" % (_n(x + 2), _n(yb + dep * 0.5), _n(dep * 0.35)), 1.0)
        C.d("".join("M%s %sv2.5" % (_n(cx + rx * math.sin(a)), _n(ty + dep + ry * math.cos(a) + 0.5))
                    for a in [-0.3 + 0.6 * i / 9.0 for i in range(10)]), 0.5)
    # hoops
    C.d(_arc(cx, ty + dep, rx, ry, 0, PI), 1.0)
    C.d(_arc(cx, ty + dep - 2, rx, ry, 0, PI), 0.5)
    C.d(_arc(cx, ty + 2, rx, ry, 0, PI), 0.5)
    C.d(_E(cx, ty, rx, ry), 1.0)
    if ry > 3.5:
        C.d(_E(cx, ty, rx - 1.5, ry - 1), 0.5)
        cid = C.clip(_E(cx, ty, rx - 1.5, ry - 1))
        C.d(_hat((cx - rx, ty - ry, cx + rx, ty - ry * 0.25), 2.0), 0.5, cid)
        C.d(_hat((cx + rx * 0.45, ty - ry, cx + rx, ty + ry), 2.0, 60), 0.5, cid)


def _stand(C, x, ytop, fy, s, spread=0.62, w2=True):
    """Cymbal / snare stand: telescoping tube with collars and a braced tripod."""
    x = _snap(x)
    hub = fy - 0.85 * s
    low = fy - 0.38 * s
    feet = [(x - spread * s, fy + 0.03 * s), (x + spread * s * 0.92, fy + 0.02 * s),
            (x + 0.14 * s, fy + 0.2 * s)]
    C.white("".join(_pl([(x, hub), (fx, ffy)]) + _pl([(x, low), ((x + fx) / 2, (hub + ffy) / 2)]) for fx, ffy in feet), None, 3.0)
    for fx, ffy in feet:
        C.line([(x, hub), (fx, ffy)], 1.0)
        C.line([(x + (1 if fx > x else -1) * 1.0, hub + 1.5), (fx + 0.5, ffy - 1.5)], 0.5)
        C.line([(x, low), ((x + fx) / 2, (hub + ffy) / 2)], 0.5)
        C.d("M%s %sh%s" % (_n(fx - 1.5), _n(ffy), _n(3)), 1.5)
    if w2:
        C.mask(_R(x - 2.5, ytop, x + 2.5, low))
        mid = hub - (hub - ytop) * 0.45
        C.d("M%s %sV%s" % (_n(x - 1.5), _n(mid), _n(low)), 0.5)
        C.d("M%s %sV%s" % (_n(x + 1.5), _n(mid), _n(low)), 1.0)
        C.d("M%s %sV%s" % (_n(x - 0.5), _n(ytop), _n(mid)), 0.5)
        C.d("M%s %sV%s" % (_n(x + 0.5), _n(ytop), _n(mid)), 0.5)
        for yy in (mid, hub):
            C.d(_R(x - 2.5, yy - 2, x + 2.5, yy + 2), 0.5)
            C.d("M%s %sh2.5" % (_n(x + 2.5), _n(yy)), 1.0)
    else:
        C.d("M%s %sV%s" % (_n(x), _n(ytop), _n(low)), 1.0)


def _cymbal(C, cx, cy, rx, ry, rot=0.0, bell=True):
    """Cymbal as a foreshortened disc with lathe rings, a sheen of radial ruling and a bell."""
    rr = math.radians(rot)
    if not bell:                                   # the under cymbal of the hi-hat: only its edge shows
        C.mask(_E(cx, cy, rx, ry, rot))
        C.d(_E(cx, cy, rx, ry, rot), 1.0)
        C.d(_arc(cx, cy - 1.5, rx * 0.96, ry, 0.15, PI - 0.15), 0.5)
        return
    C.mask(_E(cx, cy + 1, rx, ry, rot))
    C.d(_E(cx, cy + 1, rx, ry, rot), 0.5)
    C.mask(_E(cx, cy, rx, ry, rot))
    # sheen: two opposed wedges of fine ruling, as light rakes across the lathing
    for a0, a1, pit, wd in ((0.2, 1.05, 1.5, 0.5), (PI + 0.25, PI + 1.0, 2.0, 0.5))[:2 if rx > 24 else 1]:
        wedge = [(cx, cy)] + _ell(cx, cy, rx, ry, a0, a1, rr, 6)
        wid = C.clip(_pl(wedge, True))
        C.d(_hat(_bbox(wedge), pit, _snap(math.degrees((a0 + a1) / 2) * 0.4 + rot + 80, 5)), wd, wid)
    k = 0.3
    dk = max(1.5 / max(ry, 0.1), 0.13)
    while k < 0.97:
        C.d(_E(cx, cy, rx * k, ry * k, rot), 0.5)
        k += dk
    C.d(_E(cx, cy, rx, ry, rot), 1.0)
    nh = int(max(10, min(46, rx * ry / 9.0)))        # hammer marks, strewn in a sunflower spiral
    hm = []
    for i in range(nh):
        a, r = i * 2.4, 0.3 + 0.62 * math.sqrt((i + 0.5) / nh)
        hx_, hy_ = rx * r * math.cos(a), ry * r * math.sin(a)
        hm.append((cx + hx_ * math.cos(rr) - hy_ * math.sin(rr), cy + hx_ * math.sin(rr) + hy_ * math.cos(rr)))
    C.dots(hm[::2], 1.0)
    C.dots(hm[1::2], 0.5)
    if bell:
        bx, by = rx * 0.2, max(1.5, ry * 0.2)
        dome = _ell(cx, cy, bx, by + max(2.0, rx * 0.09), PI, 2 * PI, rr, 6)
        C.mask(_pl(dome, True))
        C.mask(_E(cx, cy, bx, by, rot))
        C.line(dome, 1.0)
        C.d(_arc(cx, cy, bx, by, 0, PI, rot), 0.5)
        C.line(_ell(cx, cy, bx * 0.6, by + max(2.0, rx * 0.09) * 0.55, PI * 1.5, 2 * PI, rr, 4), 0.5)


def _monogram(C, x, y, hh):
    """Slab-serif P, ruled dark, drawn as a path."""
    def P(u, v):
        return (x + (u - 0.36) * hh, y + (v - 0.5) * hh)
    outer = [P(0, 0), P(0.4, 0)] + [P(0.4 + 0.34 * math.cos(a), 0.28 + 0.28 * math.sin(a))
                                    for a in [-PI / 2 + PI * i / 10.0 for i in range(11)]]
    outer += [P(0.35, 0.56), P(0.35, 0.9), P(0.47, 0.9), P(0.47, 1), P(0, 1), P(0, 0.9), P(0.12, 0.9),
              P(0.12, 0.1), P(0, 0.1)]
    inner = [P(0.35, 0.11), P(0.4, 0.11)] + [P(0.4 + 0.13 * math.cos(a), 0.28 + 0.17 * math.sin(a))
                                            for a in [-PI / 2 + PI * i / 8.0 for i in range(9)]]
    inner += [P(0.35, 0.45)]
    d = _pl(outer, True) + _pl(inner, True)
    C.mask(_pl(outer, True))
    cid = C.clip(d, True)
    C.d(_hat(_bbox(outer), 1.5), 1.0, cid)
    C.d(d, 1.0 if hh > 26 else 0.5)


def _bass_drum(C, cx, cy, R, fy):
    """Bass drum facing the room, turned a little: front head, shell rings, lugs, spurs."""
    rx, ry = R * 0.93, R
    dx, dy = R * 0.5, R * 0.07
    bx, by = cx + dx, cy - dy
    ph = math.atan2(ry * dx, rx * dy)                # tangent point angle (near the bottom)
    # spurs
    C.white("".join(_pl([(cx + dx * 0.6 + sgn * R * 0.62, cy + R * 0.62), (cx + dx * 0.6 + sgn * R * 1.0, fy + R * 0.06)]) for sgn in (-1, 1)), None, 3.0)
    for sgn in (-1, 1):
        C.line([(cx + dx * 0.6 + sgn * R * 0.62, cy + R * 0.62), (cx + dx * 0.6 + sgn * R * 1.0, fy + R * 0.06)], 1.0)
        C.d("M%s %sh3" % (_n(cx + dx * 0.6 + sgn * R * 1.0 - 1.5), _n(fy + R * 0.06)), 1.5)
    sil = _ell(bx, by, rx, ry, ph - PI, ph) + _ell(cx, cy, rx, ry, ph, ph + PI)
    C.mask(_pl(sil, True))
    # shell: rings parallel to the hoops, cut by the tone round the cylinder: lit on top with a band
    # of highlight, sinking to black underneath; where the rings close up at the silhouette the
    # dark is carried by lines along the shell instead
    rg = random.Random(int(cx * 5 + cy * 11))

    def tb(a):
        if a < -1.2:
            return 0.34 * _cl((-1.2 - a) / 0.4)
        return 0.97 * _cl((a + 0.8) / 1.45) ** 0.9

    n = max(4, int(dx / 1.5))
    sp = dx / float(n)
    aa = [ph - PI + 0.03 + (PI - 0.06) * q_ / 44.0 for q_ in range(45)]
    for i in range(1, n):
        f_ = i / float(n)
        ex, ey = cx + dx * f_, cy - dy * f_

        def tw(x, y, ex=ex, ey=ey, i=i):
            a = math.atan2((y - ey) / ry, (x - ex) / rx)
            nx_, ny_ = ry * math.cos(a), rx * math.sin(a)
            p = sp * abs(nx_ - ny_ * dy / dx) / (math.hypot(nx_, ny_) or 1.0)
            return _adw(i, p, tb(a))
        C.raw(_rule([[(ex + rx * math.cos(a), ey + ry * math.sin(a)) for a in aa]], tw, 1.0, rg, cap=1.5, soft=True))
    gen = []
    a = 0.55
    while a < ph - 0.02:
        gen.append([(cx + dx * q_ / 6.0 + rx * math.cos(a), cy - dy * q_ / 6.0 + ry * math.sin(a)) for q_ in range(7)])
        a += 2.0 / R
    C.raw(_rule(gen, lambda x, y: _cl((math.atan2((y - cy) / ry, (x - cx - dx * 0.5) / rx) - 0.5) / 0.7) * 0.95,
                2.0, rg, soft=True))
    C.d(_arc(bx, by, rx, ry, ph - PI, ph), 1.0)
    C.d(_arc(bx - 2, by + 0.3, rx, ry, ph - PI + 0.1, ph - 0.1), 0.5)
    # lugs + tension rods along the shell
    for a in ((-1.25, -0.8, -0.35, 0.1, 0.55, 1.0) if R > 32 else (-1.1, -0.4, 0.3, 1.0)):
        ca, sa = math.cos(a), math.sin(a)
        p0 = (cx + rx * ca, cy + ry * sa)
        p1 = (bx + rx * ca, by + ry * sa)
        nx, ny = ca * 1.5, sa * 1.5
        C.line([p0, p1], 1.0)
        m0 = (p0[0] + dx * 0.36, p0[1] - dy * 0.36)
        m1 = (p0[0] + dx * 0.64, p0[1] - dy * 0.64)
        lug = [(m0[0] - nx, m0[1] - ny), (m0[0] + nx * 1.3, m0[1] + ny * 1.3),
               (m1[0] + nx * 1.3, m1[1] + ny * 1.3), (m1[0] - nx, m1[1] - ny)]
        if a < 0.4:                                      # the lugs underneath are lost in the shadow
            C.mask(_pl(lug, True))
            C.line(lug, 0.5, True)
            C.line([lug[1], lug[2]], 1.0)
        for q in (p0, p1):
            C.line([(q[0] - nx * 0.4, q[1] - ny * 0.4), (q[0] + nx * 1.6, q[1] + ny * 1.6)], 1.5)
    a = -0.57
    bq = (cx + rx * math.cos(a) + dx * 0.5, cy + ry * math.sin(a) - dy * 0.5)
    C.mask(_E(bq[0], bq[1], max(2.5, R * 0.075), max(2.0, R * 0.055), -30))
    C.d(_E(bq[0], bq[1], max(2.5, R * 0.075), max(2.0, R * 0.055), -30), 0.5)
    C.dots([bq], 1.0)
    # front hoop and head
    C.mask(_E(cx, cy, rx, ry))
    C.d(_E(cx, cy, rx, ry), 1.5)
    hw = max(2.5, R * 0.075)
    C.d(_E(cx, cy, rx - hw * 0.5, ry - hw * 0.5), 0.5)
    C.d(_E(cx, cy, rx - hw, ry - hw), 1.0)
    hx, hy = rx - hw - 0.5, ry - hw - 0.5
    r2_ = hx * 0.56
    head = C.clip(_E(cx, cy, hx, hy))
    box = (cx - rx, cy - ry, cx + rx, cy + ry)
    # the head: rings that follow its roundness, open where the lamp strikes it and swelling
    # into the lower flank, with the hoop's shadow lying inside the rim on the lit side
    def th_(x, y):
        u, v = (x - cx) / hx, (y - cy) / hy
        r_ = math.hypot(u, v)
        t = 0.05 + 0.62 * _cl((u * 0.55 + v * 0.8 + 0.25) / 1.1) ** 1.3
        t += 0.5 * _cl((r_ - 0.86) / 0.14) * _cl(-(u * 0.6 + v * 0.8) + 0.2)
        return _cl(t)
    hr = []
    k_ = 1.5
    while k_ < hx - r2_ + 3:
        hr.append([(cx + (hx - k_) * math.cos(a), cy + (hy - k_) * math.sin(a))
                   for a in [2 * PI * q_ / 72.0 for q_ in range(73)]])
        k_ += 2.5
    C.open(head)
    C.raw(_rule(hr, th_, 2.5, rg, soft=True))
    C.close()
    # monogram roundel
    r2 = hx * 0.56
    C.mask(_E(cx, cy, r2, r2 * hy / hx))
    C.d(_E(cx, cy, r2, r2 * hy / hx), 1.0)
    C.d(_E(cx, cy, r2 - 2, (r2 - 2) * hy / hx), 0.5)
    if r2 > 14:
        rc = C.clip(_E(cx, cy, r2 - 2, (r2 - 2) * hy / hx) + _E(cx, cy, r2 - 5, (r2 - 5) * hy / hx), True)
        C.d(_hat((cx - r2, cy - r2, cx + r2, cy + r2), 2.0, 90), 0.5, rc)
        C.d(_E(cx, cy, r2 - 5, (r2 - 5) * hy / hx), 0.5)
    _monogram(C, cx, cy, r2 * 1.12 if r2 > 14 else r2 * 1.3)
    # claws on the front hoop
    for a in ((-1.25, -0.8, -0.35, 0.1, 0.55, 1.0, 1.6, 2.2, 2.75, 3.3, 3.85, 4.45) if R > 32 else
              (-1.1, -0.4, 0.3, 1.0, 1.75, 2.5, 3.25, 4.0)):
        ca, sa = math.cos(a), math.sin(a)
        C.line([(cx + (rx - hw) * ca, cy + (ry - hw) * sa), (cx + (rx + 1) * ca, cy + (ry + 1) * sa)], 1.5)


def _bass(C, bx, by, H, lean, fy, lside=1):
    """Upright bass in three-quarter view, leaning; cross-contours follow the arched belly."""
    L = H / 1.9
    ax, ay = math.sin(lean), -math.cos(lean)
    px, py = math.cos(lean), math.sin(lean)
    prof = [(0, 0.0), (0.03, 0.2), (0.1, 0.275), (0.24, 0.3), (0.38, 0.25), (0.5, 0.175), (0.58, 0.185),
            (0.7, 0.23), (0.8, 0.215), (0.9, 0.14), (0.97, 0.06), (1.0, 0.035)]

    def hw0(t):
        t = max(0.0, min(1.0, t))
        for (t0, v0), (t1, v1) in zip(prof, prof[1:]):
            if t <= t1:
                return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        return prof[-1][1]

    def hw(t):
        if t < 0.03:
            return hw0(t)
        return sum(hw0(t + d_) for d_ in (-0.05, -0.025, 0, 0.025, 0.05)) / 5.0

    def pt(t, u, ox=0.0, oy=0.0):
        return (bx + (ax * t + px * u) * L + ox, by + (ay * t + py * u) * L + oy)

    nt = 26 if L > 80 else 18
    ts = [i / float(nt) for i in range(nt + 1)]
    C.line([pt(-0.1, 0), pt(0, 0)], 1.0)
    C.d("M%s %sh3" % (_n(pt(-0.1, 0)[0] - 1.5), _n(pt(-0.1, 0)[1])), 1.5)
    sd = -1 if lside > 0 else 1                             # the side turned from the lamp
    rx_, ry_ = 0.075 * L * sd, -0.012 * L                  # rib offset (back plate)
    rg = random.Random(int(bx * 3 + H * 7))
    back = [pt(t, hw(t), rx_, ry_) for t in ts] + [pt(t, -hw(t), rx_, ry_) for t in ts[::-1]]
    d = C.shape(back, 1.0)
    cid = C.clip(d)
    bb = _bbox(back)
    ribs = []
    for q_ in range(int(2.0 * L / 2.0)):                    # the rib: short strokes across it, round the bouts
        t_ = 0.01 + q_ * 2.0 / L / 2.0 * 1.0
        if t_ > 0.99:
            break
        ribs.append("M%s %sL%s %s" % (_n(pt(t_, sd * hw(t_))[0]), _n(pt(t_, sd * hw(t_))[1]),
                                      _n(pt(t_, sd * hw(t_), rx_, ry_)[0]), _n(pt(t_, sd * hw(t_), rx_, ry_)[1])))
    C.d(_hat(bb, 2.0, 0), 1.0, cid)
    C.d("".join(ribs[::2]), 1.0, cid)
    top = [pt(t, hw(t)) for t in ts] + [pt(t, -hw(t)) for t in ts[::-1]]
    d = C.shape(top, 1.0)
    C.line([pt(t, hw(t) * 0.94) for t in ts[1:-2:2]] + [pt(t, -hw(t) * 0.94) for t in ts[-3:0:-2]], 0.5, True)
    if L > 80:
        C.line([pt(t, hw(t) * 0.9) for t in ts[1:-2:2]] + [pt(t, -hw(t) * 0.9) for t in ts[-3:0:-2]], 0.5, True)
    # the belly is modelled as a rounded form: a lit edge, a band of bare paper where the arching
    # catches the lamp, then cross-contours that swell and close toward the far flank, crossed by
    # lines down the length in the deep shadow; a little reflected light comes back at the rim
    kn = [(-1.0, 0.36), (-0.84, 0.1), (-0.58, 0.0), (-0.32, 0.03), (0.08, 0.34), (0.48, 0.74), (0.8, 0.98), (1.0, 0.7)]

    def bt(x, y):
        rx0, ry0 = (x - bx) / L, (y - by) / L
        t_ = rx0 * ax + ry0 * ay
        u_ = rx0 * px + ry0 * py
        v = _cl(u_ / max(0.03, hw(t_)) * sd, -1.0, 1.0)
        return _cl(_knots(kn, v) + 0.22 * _cl((0.14 - t_) / 0.14) + 0.1 * _cl((t_ - 0.86) / 0.14))
    tb_ = _bbox(top, 2.0)
    bg = _grid(bt, tb_[0], tb_[1], tb_[2], tb_[3], 2.0)
    bc = C.clip(d)
    cont = []
    t = -0.01
    while t < 1.06:
        w_ = max(0.06, hw(min(1.0, max(0.0, t)))) * 1.04
        cont.append([pt(t - 0.045 * (1 - c_ * c_), c_ * w_) for c_ in [-1 + q_ / 9.0 for q_ in range(19)]])
        t += 2.0 / L
    C.open(bc)
    C.raw(_rule(cont, bg, 2.0, rg, soft=True))
    nl_ = max(4, int(0.3 * L / 1.5))
    for q_ in range(1, nl_):
        c_ = sd * q_ / float(nl_)

        def tw(x, y, q_=q_):
            rx0, ry0 = (x - bx) / L, (y - by) / L
            return _adw(q_, hw(rx0 * ax + ry0 * ay) * L / nl_, _cl((bg(x, y) - 0.55) * 1.6), 2.0)
        C.raw(_rule([[pt(t_, c_ * hw(t_)) for t_ in ts[1:-1]]], tw, 1.0, rg, cap=1.0, soft=True))
    C.close()
    C.white(_pl([pt(t_, sd * hw(t_) * 0.9) for t_ in ts[2:-2]]), bc, 0.5)       # purfling, white in the dark
    # f-holes
    for sg in (-1, 1):
        f = [pt(0.39 + 0.22 * i / 10.0, sg * (0.118 + 0.024 * math.sin(i / 10.0 * 2 * PI))) for i in range(11)]
        C.white(_pl(f), None, 3.0)
        C.line(f, 1.5 if L > 90 else 1.0)
        e0, e1 = pt(0.385, sg * 0.126), pt(0.615, sg * 0.11)
        C.white("M%s %sh0M%s %sh0" % (_n(e0[0]), _n(e0[1]), _n(e1[0]), _n(e1[1])), None, 4.0 if L > 90 else 3.0)
        C.dots([e0], 3.0 if L > 90 else 2.0)                                    # the eyes of the f
        C.dots([e1], 2.5 if L > 90 else 1.5)
        C.line([pt(0.5, sg * 0.105), pt(0.5, sg * 0.132)], 0.5)                 # the nick
    # tailpiece
    tp = [pt(0.06, -0.022), pt(0.06, 0.022), pt(0.33, 0.045), pt(0.33, -0.045)]
    C.shape(tp, 1.0)
    for u in (-0.018, 0.0, 0.018):
        C.line([pt(0.08, u * 0.6), pt(0.32, u * 1.6)], 1.0)
    C.line([pt(0.0, 0), pt(0.06, 0)], 1.0)
    C.line([pt(0.47, -0.075), pt(0.47, 0.075)], 1.5)
    C.line([pt(0.45, -0.07), pt(0.47, -0.075)], 0.5)
    C.line([pt(0.45, 0.07), pt(0.47, 0.075)], 0.5)
    # neck, fingerboard, strings
    fb = [pt(0.6, -0.042), pt(0.6, 0.042), pt(1.62, 0.024), pt(1.62, -0.024)]
    C.white(_pl(fb, True), None, 4.0)                       # a rim of light keeps the neck off the dark
    C.shape(fb, 1.0)
    for u in (-0.02, 0.0, 0.02):
        C.line([pt(0.62, u), pt(1.61, u * 0.55)], 0.5)
    C.line([pt(0.61, 0.042 * sd), pt(1.61, 0.024 * sd)], 1.5)
    C.line([pt(1.0, 0.035, 2, 0), pt(1.6, 0.024, 2, 0)], 0.5)
    for u0, u1 in ((-0.03, -0.05), (-0.01, -0.017), (0.01, 0.017), (0.03, 0.05)):
        C.line([pt(0.33, u0), pt(0.47, u1), pt(0.6, u1 * 0.72)], 0.5)
    # pegbox and scroll
    pb = [pt(1.62, -0.028), pt(1.62, 0.028), pt(1.77, 0.03), pt(1.77, -0.03)]
    C.white(_pl(pb, True) + "".join(_pl([pt(tt_, sg_ * 0.03), pt(tt_, sg_ * 0.078)]) for tt_, sg_ in ((1.65, 1), (1.69, -1), (1.73, 1), (1.76, -1))), None, 4.0)
    C.shape(pb, 1.0)
    C.line([pt(1.64, 0), pt(1.76, 0)], 1.0)
    for i, tt in enumerate((1.65, 1.69, 1.73, 1.76)):
        sg = -1 if i % 2 else 1
        C.line([pt(tt, sg * 0.03), pt(tt, sg * 0.075)], 1.0)
        C.line([pt(tt - 0.012, sg * 0.075), pt(tt + 0.012, sg * 0.075)], 1.5)
    sc = pt(1.81, 0.012)
    C.mask(_E(sc[0], sc[1], 0.05 * L + 2, 0.05 * L + 2))
    sp = []
    for i in range(22):
        a = i / 21.0 * 3.4 * PI + math.atan2(ay, ax) + PI
        r = 0.05 * L * (1 - i / 24.0)
        sp.append((sc[0] + r * math.cos(a), sc[1] + r * math.sin(a)))
    C.line(sp, 1.0)


def _stool(C, x, fy, s):
    """Drummer's throne: round padded seat with a button, on a braced tripod."""
    x = _snap(x)
    ty = fy - 1.5 * s
    C.white("".join(_pl([(x, fy - 0.75 * s), (fx, ffy)]) for fx, ffy in ((x - 0.5 * s, fy + 0.02 * s), (x + 0.5 * s, fy + 0.02 * s), (x + 0.1 * s, fy + 0.18 * s))), None, 3.5)
    for fx, ffy, wd in ((x - 0.5 * s, fy + 0.02 * s, 0.5), (x + 0.5 * s, fy + 0.02 * s, 1.0), (x + 0.1 * s, fy + 0.18 * s, 1.0)):
        C.line([(x, fy - 0.75 * s), (fx, ffy)], 1.0)
        C.line([(x + (1.5 if fx > x else -1.5), fy - 0.75 * s + 1), (fx + 1, ffy - 1.5)], wd)
        C.line([(x, fy - 0.38 * s), ((x + fx) / 2, (fy - 0.75 * s + ffy) / 2)], 0.5)
        C.d("M%s %sh3" % (_n(fx - 1.5), _n(ffy)), 1.5)
    C.mask(_R(x - 2, ty, x + 2, fy - 0.38 * s))
    C.d("M%s %sV%s" % (_n(x - 1.5), _n(ty), _n(fy - 0.38 * s)), 0.5)
    C.d("M%s %sV%s" % (_n(x + 1.5), _n(ty), _n(fy - 0.38 * s)), 1.0)
    C.d(_R(x - 2.5, fy - 0.75 * s - 2, x + 2.5, fy - 0.75 * s + 2), 0.5)
    rx, ry, dep = 0.44 * s, 0.13 * s, max(4.0, 0.17 * s)
    _drum(C, x, ty, rx, ry, dep, nl=0)
    C.d(_arc(x, ty + dep * 0.5, rx, ry, 0.15, PI - 0.15), 0.5)           # piping
    C.d(_arc(x, ty, rx * 0.5, ry * 0.5, 0.3, 2.6), 0.5)                   # the dip of the cushion
    C.dots([(x, ty)], 1.5)


def _mic(C, x, fy, s):
    """Ribbon microphone in a yoke on a weighted round-base stand."""
    x = _snap(x)
    top = fy - 3.3 * s
    mw, mh = max(3.5, 0.17 * s), max(10.0, 0.62 * s)
    brx, bry = 0.42 * s, 0.12 * s
    by = fy + 0.05 * s
    # base: a low dome with a rim
    C.mask(_E(x, by + 2, brx, bry))
    C.d(_arc(x, by + 2.5, brx, bry, 0, PI), 1.0)
    C.mask(_E(x, by, brx, bry))
    C.d(_E(x, by, brx, bry), 1.0)
    C.d(_arc(x, by - 0.5, brx * 0.72, bry * 0.7, PI * 0.9, PI * 2.1), 0.5)
    C.d(_arc(x, by - 1.5, brx * 0.3, bry * 0.5, PI, 2 * PI), 0.5)
    cid = C.clip(_E(x, by, brx, bry))
    C.d(_hat((x + brx * 0.2, by - bry, x + brx, by + bry), 1.5), 0.5, cid)
    C.d(_hat((x + brx * 0.55, by - bry, x + brx, by + bry), 1.5), 1.0, cid)
    # tube with clutch
    cl = fy - 1.75 * s
    C.mask(_R(x - 2, top + mh, x + 2, by - bry * 0.4))
    C.d("M%s %sV%s" % (_n(x - 1.5), _n(cl), _n(by - bry * 0.5)), 0.5)
    C.d("M%s %sV%s" % (_n(x + 1.5), _n(cl), _n(by - bry * 0.5)), 1.0)
    C.d("M%s %sV%s" % (_n(x - 0.5), _n(top + mh + 0.14 * s), _n(cl)), 0.5)
    C.d("M%s %sV%s" % (_n(x + 0.5), _n(top + mh + 0.14 * s), _n(cl)), 0.5)
    C.d(_R(x - 2.5, cl - 2.5, x + 2.5, cl + 2.5), 0.5)
    C.d("M%s %sh3.5" % (_n(x + 2.5), _n(cl)), 1.5)
    # yoke
    yk = top + mh + 0.14 * s
    pv = top + mh * 0.55
    C.d("M%s %sV%sQ%s %s %s %sQ%s %s %s %sV%s" % (_n(x - mw - 2.5), _n(pv), _n(yk - 3), _n(x - mw - 2.5), _n(yk), _n(x), _n(yk),
                                                  _n(x + mw + 2.5), _n(yk), _n(x + mw + 2.5), _n(yk - 3), _n(pv)), 1.0)
    C.dots([(x - mw - 2.5, pv), (x + mw + 2.5, pv)], 1.5)
    # body: capsule with slotted grille, centre band and collar
    r = mw
    d = "M%s %sQ%s %s %s %sQ%s %s %s %sV%sQ%s %s %s %sQ%s %s %s %sz" % (
        _n(x - mw), _n(top + r), _n(x - mw), _n(top), _n(x), _n(top), _n(x + mw), _n(top), _n(x + mw), _n(top + r),
        _n(top + mh - r * 0.6), _n(x + mw), _n(top + mh), _n(x), _n(top + mh), _n(x - mw), _n(top + mh), _n(x - mw), _n(top + mh - r * 0.6))
    C.shape(d, 1.0)
    cid = C.clip(d)
    g1 = top + mh * 0.66
    C.d(_hat((x - mw, top + 1.5, x + mw, g1), 2.0), 0.5, cid)
    C.d(_hat((x + mw * 0.25, top + 1.5, x + mw, g1), 2.0), 1.0, cid)
    C.mask(_R(x - 1, top + 1.5, x + 1, g1))
    C.d("M%s %sV%sM%s %sV%s" % (_n(x - 1), _n(top + 2), _n(g1), _n(x + 1), _n(top + 2), _n(g1)), 0.5)
    C.d("M%s %sh%s" % (_n(x - mw), _n(g1), _n(2 * mw)), 1.0)
    C.d("M%s %sh%s" % (_n(x - mw), _n(g1 + 2), _n(2 * mw)), 0.5)
    C.d(_R(x - mw * 0.5, g1 + 3.5, x + mw * 0.5, top + mh - 2.5), 0.5)


def _amp(C, x, fy, s):
    """Small tweed combo amplifier, seen from a little above and to the left."""
    wd, ht, dx, dy = 1.7 * s, 1.35 * s, 0.32 * s, 0.22 * s
    x0, x1, y0, y1 = x - wd / 2, x + wd / 2, fy - ht, fy + 0.08 * s
    side = [(x1, y0), (x1 + dx, y0 - dy), (x1 + dx, y1 - dy), (x1, y1)]
    d = C.shape(side, 1.0)
    cid = C.clip(d)
    C.d(_hat(_bbox(side), 1.5, 90), 1.0, cid)
    C.d(_hat(_bbox(side), 2.0, 0), 0.5, cid)
    topf = [(x0, y0), (x0 + dx, y0 - dy), (x1 + dx, y0 - dy), (x1, y0)]
    d = C.shape(topf, 1.0)
    cid = C.clip(d)
    C.d(_hat(_bbox(topf), 2.0, 0), 0.5, cid)
    C.line([(x0 + wd * 0.3 + dx * 0.5, y0 - dy * 0.5 - 2), (x0 + wd * 0.42 + dx * 0.5, y0 - dy * 0.5 - 4),
            (x0 + wd * 0.62 + dx * 0.5, y0 - dy * 0.5 - 4), (x0 + wd * 0.74 + dx * 0.5, y0 - dy * 0.5 - 2)], 1.5)
    C.shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 1.0)
    m = max(2.5, 0.1 * s)
    pan = y0 + m + max(4.0, 0.2 * s)
    g = [(x0 + m, pan + 1.5), (x1 - m, pan + 1.5), (x1 - m, y1 - m), (x0 + m, y1 - m)]
    d = _pl(g, True)
    C.d(d, 1.0)
    cid = C.clip(d)
    C.d(_hat(_bbox(g), 2.0, 45), 0.5, cid)
    C.d(_hat(_bbox(g), 2.0, -45), 0.5, cid)
    sp = C.clip(_E(x, (pan + y1) / 2 + 1, wd * 0.3, wd * 0.3))
    C.open(cid)
    C.d(_hat(_bbox(g), 2.0, 0), 0.5, sp)
    C.close()
    C.line([(x0 + m, y0 + m), (x1 - m, y0 + m), (x1 - m, pan), (x0 + m, pan)], 0.5, True)
    kn = int(max(3, wd / 9))
    C.dots([(x0 + m + (wd - 2 * m) * (i + 0.5) / kn, (y0 + m + pan) / 2) for i in range(kn)], 1.5)


def _curtain(C, x0, x1, y1, rng, lit, w, lx=None):
    """Velvet in heavy hanging folds, cut as a tone field.  The first family of lines runs across
    the cloth and bows over every fold as a contour would (upward above the eye, flattening
    toward the floor), swelling into the valleys and lifting to bare paper on the crests; in the
    shadowed flanks a second family falls with the cloth, and a diagonal third closes the deepest
    valleys.  The hem hangs in scallops over a gap of shadow."""
    if lx is None:
        lx = (x0 + x1) / 2.0
    fw0 = _cl(w * 0.105, 30.0, 60.0)
    edges = [x0 - 8.0]
    rgs = []
    while edges[-1] < x1 + 8:
        edges.append(edges[-1] + fw0 * rng.uniform(0.72, 1.32))
        rgs.append(rng.uniform(0.4, 0.6))
    nf = len(rgs)
    phs = [rng.uniform(0, 6.28) for _ in range(nf)]

    def sway(x, y):
        return 3.5 * math.sin(y / 47.0 + x / 130.0) + 1.5 * math.sin(y / 19.0 - x / 60.0)

    def fold(x, y):
        xs = x - sway(x, y)
        i = 0
        while i < nf - 1 and xs >= edges[i + 1]:
            i += 1
        fwd = edges[i + 1] - edges[i]
        u = _cl((xs - edges[i]) / fwd)
        rg = rgs[i] + 0.06 * math.sin(y / 33.0 + phs[i])
        if u < rg:
            return 1 - u / rg, -1, i, fwd
        return (u - rg) / (1 - rg), 1, i, fwd

    def ct(x, y):
        v, side, i, fwd = fold(x, y)
        b = 1 - 0.96 * lit(x, y)
        if side * (1 if edges[i] + fwd * 0.5 < lx else -1) < 0:
            s_ = _cl((v - 0.08) / 0.7) ** 0.8                      # the flank turned from the lamp
        else:
            s_ = 0.9 * _cl((v - 0.24) / 0.76) ** 1.9               # the lit flank: dark only in the valley
        s_ *= 0.86 + 0.14 * math.sin(y / 29.0 + phs[i] * 2)
        return _cl(s_ * (0.5 + 0.5 * b) + (0.08 + 0.42 * b) * _cl(v * 4.0 - 0.3))
    g = _grid(ct, x0, 0, x1, y1, 2.0)
    ye = y1 * 0.92                                                # eye level

    def bump(x, y):
        v, side, i, fwd = fold(x, y)
        return math.cos(v * PI / 2) ** 0.8 * fwd

    hem = []
    x = x0
    while x <= x1:
        hem.append((x, y1 - 5.5 + 0.075 * bump(x, y1 - 4)))
        x += 2.0
    hem.append((x1, hem[-1][1]))
    cl_ = C.clip(_pl([(x0, 0), (x1, 0)] + hem[::-1], True))
    C.ink(_pl(hem + [(x1, y1), (x0, y1)], True))                 # the gap of shadow under the hem
    fam = []
    y = 1.5
    while y < y1 + 8:
        k_ = 0.2 * _cl((ye - y) / ye, -0.4, 1.0)
        ln = []
        x = x0
        while x <= x1 + 1.9:
            ln.append((x, y - k_ * bump(x, y)))
            x += 2.0
        fam.append(ln)
        y += 2.5
    C.open(cl_)
    C.raw(_rule(fam, g, 2.5, rng, soft=True))
    fam2 = []
    xs = x0 - 6.0
    while xs < x1 + 6:
        fam2.append([(xs + sway(xs, yy_), yy_) for yy_ in [q_ * 3.0 for q_ in range(int(y1 / 3.0) + 2)]])
        xs += 2.5
    C.raw(_rule(fam2, lambda x, y: _cl((g(x, y) - 0.56) * 2.1), 2.5, rng, cap=1.0, soft=True))
    C.raw(_rule(_bend(_dfam((x0, 0, x1, y1), 58, 2.5, 3.0), 1.5, 30.0), lambda x, y: _cl((g(x, y) - 0.82) * 4.5), 2.5, rng, cap=0.5, soft=True))
    C.close()
    C.d(_pl(hem), 1.0)


def _bricks(C, x0, x1, y1, rng, lit):
    """Brick wall in the half-dark: the faces are a cut tone, brick by brick; the mortar is white
    line with a dark arris under it."""
    bh, bw = 8.0, 24.0
    C.mask(_R(x0, 0, x1, y1))
    var = {}

    def bt(x, y):
        r = int(y // bh)
        c = int((x - (bw / 2 if r % 2 else 0)) // bw)
        k = (r, c)
        if k not in var:
            var[k] = rng.uniform(-0.14, 0.18)
        return _cl(0.26 + 0.66 * (1 - lit(x, y)) + var[k])
    C.raw(_rule(_hfam(x0, x1, 1.0, y1, 2.0, 3.0), bt, 2.0, rng, soft=True))
    C.raw(_rule(_dfam((x0, 0, x1, y1), 50 if x0 < 1 else -50, 2.5, 3.0), lambda x, y: _cl((bt(x, y) - 0.6) * 2.6), 2.5, rng, soft=True))
    mo, ar = [], []
    r = 0
    y = 0.0
    while y < y1:
        mo.append("M%s %sh%s" % (_n(x0), _n(y), _n(x1 - x0)))
        ar.append("M%s %sh%s" % (_n(x0), _n(y + 1), _n(x1 - x0)))
        xx = math.floor(x0 / bw) * bw + (bw / 2 if r % 2 else 0) - bw
        while xx < x1:
            if x0 < xx < x1:
                mo.append("M%s %sV%s" % (_n(xx), _n(y), _n(min(y1, y + bh))))
                ar.append("M%s %sV%s" % (_n(xx + 1), _n(y + 1.5), _n(min(y1, y + bh - 1))))
            xx += bw
        y += bh
        r += 1
    C.white("".join(mo), None, 1.5)
    C.d("".join(ar), 0.5)



def _poster(C, cx, cy, pw, ph):
    """Framed club bill: a record, and bars of lettering too small to read."""
    x0, y0, x1, y1 = _snap(cx - pw / 2), _snap(cy - ph / 2), _snap(cx + pw / 2), _snap(cy + ph / 2)
    C.mask(_R(x0 - 1, y0 - 1, x1 + 3, y1 + 3))
    C.d("M%s %sV%sH%s" % (_n(x1 + 1.5), _n(y0 + 3), _n(y1 + 1.5), _n(x0 + 3)), 1.5)      # cast shadow
    C.d(_R(x0, y0, x1, y1), 1.0)
    C.d(_R(x0 + 2.5, y0 + 2.5, x1 - 2.5, y1 - 2.5), 0.5)
    C.d("M%s %sL%s %sL%s %s" % (_n(x0 + 4), _n(y0), _n(cx), _n(y0 - 6), _n(x1 - 4), _n(y0)), 0.5)
    C.dots([(cx, y0 - 6)], 1.5)
    r = min(pw * 0.3, ph * 0.24)
    ry_ = y0 + 5 + r
    k = r
    while k > r * 0.42:
        C.d(_E(cx, ry_, k, k), 1.0 if k == r else 0.5)
        k -= 1.5
    C.d(_E(cx, ry_, r * 0.36, r * 0.36), 1.0)
    C.dots([(cx, ry_)], 1.5)
    C.d(_arc(cx, ry_, r * 0.8, r * 0.8, -1.2, -0.4) + _arc(cx, ry_, r * 0.8, r * 0.8, 1.9, 2.7), 1.0)
    yy = ry_ + r + 4
    for i, (f, wd) in enumerate(((0.8, 1.5), (0.55, 1.0), (0.7, 0.5), (0.4, 0.5))):
        if yy < y1 - 4:
            C.d("M%s %sh%s" % (_n(cx - (pw - 9) * f / 2), _n(yy), _n((pw - 9) * f)), wd)
        yy += 3.5 if i else 4.0


def _window(C, cx, cy, ww, wh):
    """Small sash window on the night: glazing bars, a crescent moon, glints on the panes."""
    x0, y0, x1, y1 = _snap(cx - ww / 2), _snap(cy - wh / 2), _snap(cx + ww / 2), _snap(cy + wh / 2)
    C.mask(_R(x0 - 2, y0 - 2, x1 + 2, y1 + 4))
    C.d(_R(x0, y0, x1, y1), 1.0)
    C.d(_R(x0 + 2.5, y0 + 2.5, x1 - 2.5, y1 - 2.5), 0.5)
    cid = C.clip(_R(x0 + 2.5, y0 + 2.5, x1 - 2.5, y1 - 2.5))
    C.d(_hat((x0, y0, x1, y1), 2.0, 45), 0.5, cid)
    C.d(_hat((x0, (y0 + y1) / 2, x1, y1), 2.0, -45), 0.5, cid)
    mx, my, mr = cx + ww * 0.2, y0 + wh * 0.26, max(2.5, ww * 0.12)
    C.mask(_E(mx, my, mr + 1, mr + 1))
    C.d(_arc(mx, my, mr, mr, -1.9, 1.3), 1.0)
    C.d(_arc(mx - mr * 0.45, my - mr * 0.2, mr * 0.85, mr * 0.85, -1.2, 0.9), 0.5)
    C.mask(_R(cx - 1, y0 + 2.5, cx + 1, y1 - 2.5) + _R(x0 + 2.5, cy - 1, x1 - 2.5, cy + 1))
    C.d("M%s %sV%sM%s %sV%s" % (_n(cx - 1), _n(y0 + 2.5), _n(y1 - 2.5), _n(cx + 1), _n(y0 + 2.5), _n(y1 - 2.5)), 0.5)
    C.d("M%s %sH%sM%s %sH%s" % (_n(x0 + 2.5), _n(cy - 1), _n(x1 - 2.5), _n(x0 + 2.5), _n(cy + 1), _n(x1 - 2.5)), 0.5)
    C.d("M%s %sH%s" % (_n(x0 - 2), _n(y1 + 1.5), _n(x1 + 2)), 1.5)
    C.d("M%s %sH%s" % (_n(x0), _n(y1 + 3.5), _n(x1 + 1)), 0.5)


def _jazz(C, w, h, rng):
    wide = w / float(h)
    fy0 = _snap(h * (0.64 if wide < 3.2 else 0.62))          # wall meets floor
    fy = fy0 + (h - fy0) * 0.42                               # line the kit stands on
    s = min((fy - 3) / 3.75, w * 0.56 / 6.6)
    ox = w * (0.47 if wide >= 2.6 else 0.48 if wide > 1.2 else 0.5)
    lightx = ox

    # ---- back wall: brick at the ends, velvet curtain across the rest
    lod = 1
    pl = pr_ = 0.0
    if wide >= 2.6:
        pl = pr_ = _snap(w * 0.13, 12)
    elif w >= 300 and ox - 3.5 * s > 60:
        pl = _snap(min(ox - 3.9 * s, w * 0.17), 12)
    lrx, lry, lyc = max(w * 0.27, 4.0 * s), fy0 * 0.9, fy0 * 0.85

    def lit(x, y):
        return math.exp(-1.25 * (((x - lightx) / lrx) ** 2 + ((y - lyc) / lry) ** 2))
    if pl:
        _bricks(C, 0, pl, fy0, rng, lit)
        if pl >= 56 and fy0 >= 60:
            pw = min(pl - 20, 46.0, fy0 * 0.42)
            _poster(C, pl * 0.5 - 2, fy0 * (0.36 if fy0 > 120 else 0.44), pw, pw * 1.36)
    if pr_:
        _bricks(C, w - pr_, w, fy0, rng, lit)
        ww_ = min(pr_ - 26, 44.0, fy0 * 0.45)
        _window(C, w - pr_ * 0.5 + 3, fy0 * 0.42, ww_, ww_ * 1.3)
    C.mask(_R(pl, 0, w - pr_, fy0))
    _curtain(C, pl, w - pr_, fy0, rng, lit, w, lightx)
    for xx, sg in (((pl, -1),) if pl else ()) + (((w - pr_, 1),) if pr_ else ()):
        C.d("M%s 0V%s" % (_n(xx), _n(fy0)), 1.5)                # leading edge and its shadow on the brick
        C.d("M%s 0V%s" % (_n(xx + sg * 2.5), _n(fy0)), 1.0)
        C.d("M%s 0V%s" % (_n(xx + sg * 5), _n(fy0)), 0.5)
    # valance with fringe and tassels, and the lamp, on tall plates
    top_free = fy - 3.75 * s
    if top_free > 34:
        vh = min(26.0, top_free * 0.42)
        vw = w - pl - pr_
        nsw = max(2, int(round(vw / 95.0)))
        sw_ = vw / float(nsw)
        pts = [(pl, 0)]
        for i in range(nsw):
            pts += _q((pl + i * sw_, vh * 0.55), (pl + (i + 0.5) * sw_, vh * 1.5), (pl + (i + 1) * sw_, vh * 0.55), 10)
        pts += [(w - pr_, 0)]
        d = C.shape(pts, 1.0)
        cid = C.clip(d)
        for i in range(nsw):
            xa, xb = pl + i * sw_, pl + (i + 1) * sw_
            nj = int(vh / 2.5)
            for j in range(1, nj):
                f = j / float(nj)
                a_, b_, c_ = (xa, vh * 0.55 * f), ((xa + xb) / 2, vh * 1.5 * f + 2), (xb, vh * 0.55 * f)
                C.d(_qd(a_, b_, c_), 0.5, cid)
                if j % 2 == 0:
                    C.d(_qd(a_, b_, c_, 0.5, 0.92), 1.0, cid)           # each fold swells into its shadow
            a_, b_, c_ = (xa, vh * 0.55 - 2.5), ((xa + xb) / 2, vh * 1.5 - 2.5), (xb, vh * 0.55 - 2.5)
            C.d(_qd(a_, b_, c_), 1.0, cid)                              # braid
            fr = _q((xa, vh * 0.55), ((xa + xb) / 2, vh * 1.5), (xb, vh * 0.55), int(sw_ / 4.0))
            C.d("".join("M%s %sv%s" % (_n(px_), _n(py_), _n(3.5 + (k_ % 2))) for k_, (px_, py_) in enumerate(fr[1:-1])), 0.5)
        C.open(cid)                                                     # the valance sinks into the dark with the room
        vb = (pl, 0, w - pr_, vh * 1.5 + 2)
        C.raw(_rule(_bend(_dfam(vb, 40, 2.0, 3.0), 1.0, 25.0), lambda x, y: _cl(0.15 + 0.8 * (1 - lit(x, y * 2 + fy0 * 0.3))), 2.0, rng, soft=True))
        C.raw(_rule(_dfam(vb, -40, 2.5, 3.0), lambda x, y: _cl(0.9 * (1 - lit(x, y * 2 + fy0 * 0.3)) - 0.45) * 2, 2.5, rng, soft=True))
        C.close()
        for i in range(nsw + 1):                                        # tassels at the swag heads
            tx, ty_ = min(max(pl + i * sw_, pl + 3), w - pr_ - 3), vh * 0.55
            C.mask(_E(tx, ty_ + 3.5, 4.0, 4.0) + "M%s %sh7l1.5 8.5h-10z" % (_n(tx - 3.5), _n(ty_ + 5)))
            C.d("M%s 0V%s" % (_n(tx), _n(ty_ + 2)), 1.5)
            C.d(_E(tx, ty_ + 3.5, 2.5, 2.5), 1.0)
            C.d("".join("M%s %sl%s 6.5" % (_n(tx + q_ * 0.5), _n(ty_ + 6), _n(q_ * 0.6)) for q_ in (-3, -1.5, 0, 1.5, 3)), 0.5)
            C.d("M%s %sh5" % (_n(tx - 2.5), _n(ty_ + 6.5)), 1.0)
        ly = vh + (top_free - vh) * 0.45
        lx = _snap(ox + 0.3 * s)
        lr = max(7.0, min(0.5 * s, (top_free - vh) * 0.45))
        C.white("M%s %sV%s" % (_n(lx), _n(vh), _n(ly - lr * 0.7)), None, 3.0)
        C.d("M%s 0V%s" % (_n(lx), _n(ly - lr * 0.7)), 1.0)
        shade = [(lx - lr * 0.22, ly - lr * 0.7), (lx + lr * 0.22, ly - lr * 0.7), (lx + lr, ly), (lx - lr, ly)]
        C.shape(shade, 1.0)
        for q_ in range(-4, 5):                                         # flutes of the enamel shade
            C.line([(lx + lr * 0.22 * q_ / 4.5, ly - lr * 0.7 + 1), (lx + lr * q_ / 4.5, ly)], 1.0 if q_ > 1 else 0.5)
        C.mask(_E(lx, ly, lr, lr * 0.2))
        C.d(_E(lx, ly, lr, lr * 0.2), 1.0)
        C.d(_arc(lx, ly + lr * 0.12, lr * 0.3, lr * 0.25, 0, PI), 0.5)
        for a in (-0.5, -0.25, 0.25, 0.5):                              # a few rays, dotted
            C.dots([(lx + math.sin(a) * rr_, ly + lr * 0.3 + math.cos(a) * rr_)
                    for rr_ in [lr * 0.5 + 4.0 * i for i in range(int(min(10, (top_free - ly) / 5)))]], 0.5)

    shl = []

    def shadow(cx, cy, rx, ry):
        shl.append((cx, cy, rx * 1.15, max(2.0, ry) * 1.5))

    def X(u):
        return ox + u * s

    def Y(v):
        return fy - v * s

    # ---- place the supporting cast by the room that is left
    left_free, right_free = X(-3.4), w - X(3.4)
    Hb = max(min(6.6 * s, (fy0 + 4) * 0.98), 5.0 * s)
    Lb = Hb / 1.9
    items = []
    bass_side = 1
    if wide >= 2.6:
        bass_side = -1
    if bass_side > 0:
        bxp = min(X(3.5) + Lb * 0.42, w - Lb * 0.2) if right_free > Lb * 0.3 else w - Lb * 0.12
        right_free = w - (bxp + Lb * 0.45)
    else:
        bxp = X(-3.5) - Lb * 0.45
        left_free = bxp - Lb * 0.75
    lcur, rcur = (bxp - Lb * 0.7 if bass_side < 0 else X(-3.5)), (bxp + Lb * 0.55 if bass_side > 0 else X(3.5))
    order = [("mic", 1.15 * s), ("stool", 0.92 * s), ("amp", 2.6 * s)]
    lcur = min(lcur, X(-3.45))
    lmin, rmax = 2.0, w - 2.0
    side = 1 if bass_side < 0 else -1
    for name, need in order:
        for sd in (side, -side):
            if sd > 0 and rmax - rcur >= need * 0.95:
                items.append((name, rcur + need * 0.5))
                rcur += need
                break
            if sd < 0 and lcur - lmin >= need * 0.95:
                items.append((name, lcur - need * 0.5))
                lcur -= need
                break
        side = -side

    # shadows first
    shadow(X(0.25), Y(-0.1), 2.9 * s, 0.3 * s)
    shadow(X(1.9), Y(0.0), 0.9 * s, 0.1 * s)
    shadow(X(-1.6), Y(-0.02), 0.8 * s, 0.08 * s)
    shadow(bxp + 0.14 * Lb, fy0 + 6, Lb * 0.42, max(3.0, (h - fy0) * 0.06))
    shadow(X(-2.6), Y(-0.03), 0.75 * s, 0.07 * s)
    shadow(X(2.75), Y(-0.03), 0.7 * s, 0.07 * s)
    for name, xx in items:
        if name == "amp":
            shadow(xx + 0.3 * s, fy + 0.08 * s, 1.1 * s, 0.09 * s)
        elif name == "mic":
            shadow(xx + 0.2 * s, fy + 0.18 * s, 0.55 * s, 0.06 * s)
        else:
            shadow(xx + 0.1 * s, fy + 0.08 * s, 0.6 * s, 0.07 * s)

    # ---- floor: a tone field cut in layers (undulating tint, then lines down the boards, then a
    # diagonal family in the deepest shadow); the pool of light and every cast shadow live in the field
    C.mask("M0 %sH%sV%sH0z" % (_n(fy0), _n(w), _n(h + 1)))
    pcx, pcy = lightx - 0.2 * s, fy + 0.3 * s
    prx, pry = max(3.9 * s, w * 0.3), max(5.0, (h - fy0) * 0.55)

    def ft(x, y):
        d_ = math.sqrt(((x - pcx) / prx) ** 2 + ((y - pcy) / pry) ** 2)
        t = 0.04 + 0.92 * _cl((d_ - 0.62) / 1.25) ** 1.4
        for cx_, cy_, rx_, ry_ in shl:
            k_ = ((x - cx_) / rx_) ** 2 + ((y - cy_) / ry_) ** 2
            if k_ < 1:
                e_ = 1 - k_
                t += (0.96 - t) * min(1.0, e_ * e_ * 3.2)
        return t
    fg = _grid(ft, 0, fy0, w, h + 2, 2.0)
    C.d("M0 %sH%s" % (_n(fy0), _n(w)), 1.5)
    C.d("M0 %sH%s" % (_n(fy0 + 2), _n(w)), 0.5)
    frect = "M0 %sH%sV%sH0z" % (_n(fy0 + 2), _n(w), _n(h + 1))
    vpx, vpy = w * 0.5, fy0 - (h - fy0) * 1.1
    fl = C.clip(frect)

    def bx_(xb, y):
        return vpx + (xb - vpx) * (y - vpy) / (h - vpy)
    # every line runs down the boards toward the vanishing point; the tone of the pool and of the
    # cast shadows is carried by their weight alone, and where they crowd toward the wall every
    # other one is lifted.  Each fourteenth line is a seam between boards and never breaks.
    pb, nseam = 2.0, 14
    r0 = (fy0 + 2 - vpy) / (h - vpy)
    i0 = int(math.floor((vpx - (vpx + 3) / r0) / pb / nseam)) * nseam
    i1 = int(math.ceil((vpx + (w - vpx + 3) / r0) / pb))
    pms = [1.5 + 0.7 * rng.random() for _ in range(i1 - i0 + 1)]
    ys = [fy0 + 2 + q_ * 3.0 for q_ in range(int((h - fy0) / 3.0) + 1)]

    def fw_(x, y):
        k_ = (y - vpy) / (h - vpy)
        i = int(round((vpx + (x - vpx) / k_) / pb))
        w_ = _adw(i, pb * k_, fg(x, y) * 0.88, pms[((i - i0) // 4) % len(pms)], 0.5 + 0.5 * _cl(abs(x - vpx) / (y - vpy) * 2.5 - 0.25))
        if i % nseam == 0 and w_ < 0.5:
            return 0.5
        return w_
    fam = []
    jn = []
    for i in range(i0, i1 + 1):
        ln = [(bx_(i * pb, y_), y_) for y_ in ys]
        ln = [q_ for q_ in ln if -3 < q_[0] < w + 3]
        if len(ln) > 1:
            fam.append(ln)
        if i % nseam == 0:                                                   # one butt joint to a board
            yj = fy0 + 5 + (h - fy0 - 6) * rng.random() ** 1.4
            jn.append("M%s %sH%s" % (_n(bx_(i * pb, yj)), _n(yj), _n(bx_((i + nseam) * pb, yj))))
    C.open(fl)
    C.raw(_rule(fam, fw_, 1.0, rng, cap=1.5, soft=True, dith=False))
    C.close()
    C.d("".join(jn), 0.5, fl)

    # ---- upright bass, leaning into the corner
    _bass(C, bxp, fy0 + 3 - 0.1 * Lb * 0, Hb, 0.2 * bass_side * -1 if bass_side > 0 else 0.2, fy0 + 3, 1 if lightx > bxp else -1)
    for name, xx in items:
        if name == "amp":
            _amp(C, xx - 0.15 * s, fy - 0.05 * s, s)
        elif name == "mic":
            _mic(C, xx, fy + 0.1 * s, s)
        elif name == "stool":
            _stool(C, xx, fy, s)

    # ---- the kit, back to front
    # ride on its stand (behind the floor tom)
    _stand(C, X(2.7), Y(2.85), fy - 0.05 * s, s)
    C.white(_pl([(X(2.7), Y(2.75)), (X(2.05), Y(3.02))]), None, 3.5)
    C.line([(X(2.7), Y(2.75)), (X(2.05), Y(3.02))], 1.5)
    C.line([(X(2.05), Y(3.02)), (X(2.0), Y(3.2))], 1.0)
    _cymbal(C, X(1.95), Y(3.12), 0.9 * s, 0.3 * s, -9)
    C.d("M%s %sv-3" % (_n(X(1.95)), _n(Y(3.12) - max(2.0, 0.08 * s) - 1)), 1.0)
    # hi-hat
    hx_ = _snap(X(-2.75))
    _stand(C, hx_, Y(2.0), fy - 0.02 * s, s, 0.55)
    C.line([(hx_ + 0.1 * s, fy + 0.2 * s), (hx_ + 0.5 * s, fy + 0.3 * s), (hx_ + 0.55 * s, fy + 0.22 * s),
            (hx_ + 0.16 * s, fy + 0.1 * s)], 1.0, True)
    _cymbal(C, hx_, Y(2.03), 0.62 * s, 0.13 * s, 0, bell=False)
    _cymbal(C, hx_, Y(2.03) - max(2.5, 0.07 * s), 0.62 * s, 0.14 * s, 0)
    C.d("M%s %sv%s" % (_n(hx_), _n(Y(2.03) - max(2.5, 0.07 * s) - max(2.0, 0.056 * s) - 1), _n(-max(5.0, 0.3 * s))), 1.0)
    C.d("M%s %sh3" % (_n(hx_ - 1.5), _n(Y(2.03) - max(2.5, 0.07 * s) - max(2.0, 0.056 * s) - 3)), 1.5)
    # floor tom on three legs
    ftx, fty, frx = X(1.85), Y(1.72), 0.7 * s
    C.white("".join(_pl([(ftx + lx_ * frx, fty + 0.5 * s), (ftx + lx_ * frx * 1.08, fy + ly_ * s)]) for lx_, ly_ in ((-0.92, 0.0), (0.92, 0.0), (0.2, 0.2))), None, 3.0)
    for lx_, ly_ in ((-0.92, 0.0), (0.92, 0.0), (0.2, 0.2)):
        C.line([(ftx + lx_ * frx, fty + 0.5 * s), (ftx + lx_ * frx * 1.08, fy + ly_ * s)], 1.0)
        C.d("M%s %sh3" % (_n(ftx + lx_ * frx * 1.08 - 1.5), _n(fy + ly_ * s)), 1.5)
    _drum(C, ftx, fty, frx, 0.2 * s, 1.08 * s, nl=6)
    # rack tom on its post
    C.line([(X(-0.05), Y(2.0)), (X(-0.05), Y(2.3))], 1.5)
    _drum(C, X(-0.1), Y(2.86), 0.5 * s, 0.15 * s, 0.6 * s, nl=6)
    # bass drum
    _bass_drum(C, X(-0.1), Y(1.06), s, fy)
    # snare on its stand, in front and to the left
    sx, sy, srx = X(-1.62), Y(1.6), 0.62 * s
    _stand(C, sx, sy + 0.42 * s, fy + 0.08 * s, s, 0.5)
    C.line([(sx - srx * 0.8, sy + 0.42 * s + 0.2 * s), (sx, sy + 0.62 * s + 0.2 * s), (sx + srx * 0.8, sy + 0.42 * s + 0.2 * s)], 1.0)
    _drum(C, sx, sy, srx, 0.2 * s, 0.4 * s, nl=6, snare=True)
    # sticks and brushes resting on the head
    def stick(x0, y0, x1, y1, wd):
        dx_, dy_ = x1 - x0, y1 - y0
        ln = math.hypot(dx_, dy_) or 1
        nx_, ny_ = -dy_ / ln * wd, dx_ / ln * wd
        pts = [(x0 + nx_, y0 + ny_), (x1 - dx_ * 0.2 + nx_, y1 - dy_ * 0.2 + ny_), (x1 + nx_ * 0.4, y1 + ny_ * 0.4),
               (x1 - nx_ * 0.4, y1 - ny_ * 0.4), (x1 - dx_ * 0.2 - nx_, y1 - dy_ * 0.2 - ny_), (x0 - nx_, y0 - ny_)]
        C.line([(x0 + 1, y0 + 2.5), (x1 + 1, y1 + 2.5)], 0.5)      # cast shadow on the head
        C.shape(pts, 0.5)
        C.line([pts[4], pts[5]], 1.0)
        C.d(_E(x1, y1, max(1.0, wd * 0.9), max(1.0, wd * 0.9)), 1.0)
    swd = max(1.0, 0.028 * s)
    stick(sx + srx * 1.05, sy + 0.1 * s, sx - srx * 0.75, sy - 0.11 * s, swd)
    stick(sx + srx * 1.1, sy - 0.02 * s, sx - srx * 0.6, sy - 0.02 * s, swd)
    # the pair of brushes: one across the snare, its mate on the floor tom
    def brush(x0, y0, x1, y1, ln):
        dx_, dy_ = x1 - x0, y1 - y0
        L_ = math.hypot(dx_, dy_) or 1.0
        ux, uy = dx_ / L_, dy_ / L_
        C.line([(x0, y0 + 2), (x1, y1 + 2)], 0.5)                           # shadow on the head
        C.line([(x0, y0), (x1, y1)], 1.5)
        C.line([(x0 + ux * 2, y0 + uy * 2 - 1.5), (x1, y1 - 1.5)], 0.5)
        C.d(_E(x0 - ux * 2, y0 - uy * 2, 1.5, 1.5), 0.5)                    # pull ring
        C.line([(x1 - uy * 1.5, y1 + ux * 1.5), (x1 + uy * 1.5, y1 - ux * 1.5)], 1.0)
        for i in range(9):
            a = math.atan2(uy, ux) + (i - 4) * 0.085
            C.line([(x1, y1), (x1 + ln * math.cos(a), y1 + ln * math.sin(a) * 0.55)], 0.5)
    brush(sx - srx * 1.12, sy + 0.16 * s, sx - srx * 0.2, sy + 0.05 * s, srx * 0.62)
    brush(ftx + frx * 1.15, fty + 0.02 * s, ftx + frx * 0.2, fty - 0.02 * s, frx * 0.6)


# ====================================================================== LOTUS
def _chaikin(pts, n=2, closed=True):
    for _ in range(n):
        out = []
        m = len(pts)
        for i in range(m if closed else m - 1):
            a, b = pts[i], pts[(i + 1) % m]
            out.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            out.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        pts = out if closed else [pts[0]] + out + [pts[-1]]
    return pts


def _curl(C, x, y, r, ang, flip=1):
    """One cloud-curl of the Lanna ground: a coiled head with a flame tail, lit from the upper
    left; laid like scales so that no bare ground is left between them."""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa * flip, ca * flip

    def at(a):
        return (x + r * math.cos(a), y + r * math.sin(a))
    p1, p2 = at(ang + 1.9), at(ang - 1.9)
    tip = (x + ca * 2.0 * r - px * 0.95 * r, y + sa * 2.0 * r - py * 0.95 * r)
    c1 = (x + ca * 1.7 * r + px * 0.95 * r, y + sa * 1.7 * r + py * 0.95 * r)
    c2 = (x + ca * 1.25 * r - px * 0.35 * r, y + sa * 1.25 * r - py * 0.35 * r)
    if flip < 0:
        p1, p2 = p2, p1
    C.shape("M%s %sQ%s %s %s %sA%s %s 0 0 %d %s %sQ%s %s %s %sz" % (
        _n(tip[0]), _n(tip[1]), _n(c1[0]), _n(c1[1]), _n(p1[0]), _n(p1[1]), _n(r), _n(r), 1 if flip > 0 else 0,
        _n(p2[0]), _n(p2[1]), _n(c2[0]), _n(c2[1]), _n(tip[0]), _n(tip[1])), 0.5)
    sp = []
    for i in range(11):
        t = i / 10.0
        a = ang + PI + flip * (0.6 + t * 2.9 * PI)
        rr = r * 0.72 * (1 - 0.82 * t)
        sp.append((x + rr * math.cos(a) + ca * r * 0.1 * (1 - t), y + rr * math.sin(a) + sa * r * 0.1 * (1 - t)))
    C.line(sp, 0.5)
    C.d(_arc(x, y, r - 1.5, r - 1.5, 0.2, 1.9), 1.0)                   # swell on the shadow side
    k = 3.0
    while k < r * 0.55:                                                 # and hatching that follows the coil
        C.d(_arc(x, y, r - k, r - k, 0.35 + k * 0.05, 1.75 - k * 0.05), 0.5)
        k += 1.5
    C.d(_qd(c1, ((c1[0] + tip[0]) / 2 + ca * r * 0.1, (c1[1] + tip[1]) / 2 + sa * r * 0.1), tip, 0.0, 0.8), 0.5)
    C.d(_qd(((p2[0] + x) / 2 + ca * r * 0.5, (p2[1] + y) / 2 + sa * r * 0.5), c2, tip, 0.0, 0.75), 0.5)


def _wat(C, cx, by, W):
    """Temple front: three telescoped gables with bai raka, chofa and hang hong, a columned
    porch with door and windows, and naga balustrades down the steps."""
    pb = 0.08 * W
    yb0 = by - pb
    yE = yb0 - 0.26 * W
    apex0 = yE - 0.8 * W
    cw = max(1.5, 0.022 * W)
    # porch wall, door and windows
    x0, x1 = cx - 0.4 * W, cx + 0.4 * W
    C.mask(_R(x0, yE - 1, x1, yb0))
    rg = random.Random(int(cx * 3 + W * 5))
    # lime-washed wall: a light tint that deepens on the side away from the moon
    C.open(C.clip(_R(x0, yE, x1, yb0)))
    C.raw(_rule(_wfam(x0, x1, yE + 1, yb0, 2.0, 3.0, 0.6, 31.0, 0.3, 13.0),
                lambda x, y: 0.1 + 0.34 * _cl((x - x0) / (x1 - x0)) ** 1.5 + 0.25 * _cl(1 - (y - yE) / (0.16 * W)), 2.0, rg, soft=True))
    C.close()
    cols = [cx - 0.38 * W, cx - 0.14 * W, cx + 0.14 * W, cx + 0.38 * W]
    for k, (xa, xb) in enumerate(zip(cols, cols[1:])):
        mx = (xa + xb) / 2
        ow = (0.07 if k == 1 else 0.045) * W
        oy = yE + (0.07 if k == 1 else 0.1) * W
        ob = yb0 if k == 1 else yb0 - 0.07 * W
        d = "M%s %sL%s %sL%s %sL%s %sL%s %sz" % (_n(mx - ow), _n(ob), _n(mx - ow), _n(oy), _n(mx), _n(oy - ow * 1.2),
                                                 _n(mx + ow), _n(oy), _n(mx + ow), _n(ob))
        cid = C.clip(d)
        C.d(_hat((mx - ow, oy - ow * 1.2, mx + ow, ob), 1.5, 90), 1.0, cid)
        C.d(_hat((mx - ow, oy - ow * 1.2, mx + ow, (oy + ob) / 2), 2.0), 0.5, cid)
        C.d(d, 1.0)
        C.line([(mx - ow - 2, oy), (mx, oy - ow * 1.2 - 3), (mx + ow + 2, oy)], 0.5)
        C.d("M%s %sH%s" % (_n(xa + cw + 1), _n(yb0 - 0.06 * W), _n(xb - cw - 1)), 0.5)       # dado
        if k == 1:                                           # panelled double doors, white line in the dark
            wl = "M%s %sV%s" % (_n(_snap(mx)), _n(oy - ow * 0.9), _n(ob))
            for sg in (-1, 1):
                xm = mx + sg * ow * 0.5
                for ya_, yb_ in ((oy + 1.5, oy + (ob - oy) * 0.42), (oy + (ob - oy) * 0.5, ob - 2.5)):
                    wl += _R(xm - ow * 0.3, ya_, xm + ow * 0.3, yb_)
            C.white(wl, cid, 0.5)
            C.dots([(mx - 1.5, (oy + ob) / 2 + 1), (mx + 1.5, (oy + ob) / 2 + 1)], 1.0)
        else:                                                # windows: a mullion and bars; carved panels beside and below
            C.white("M%s %sV%sM%s %sH%s" % (_n(_snap(mx)), _n(oy - ow * 0.9), _n(ob), _n(mx - ow), _n((oy + ob) / 2), _n(mx + ow)), cid, 0.5)
            C.d(_R(mx - ow - 1.5, ob + 1.5, mx + ow + 1.5, yb0 - 0.06 * W - 1.5), 0.5)
            pw_ = ((xb - xa) / 2 - ow - cw) / 2.0
            if pw_ > 3.5:
                for sg in (-1, 1):
                    qx_, qy_ = mx + sg * (ow + pw_ + 0.5), (oy + ob) / 2
                    ph_ = min(pw_ * 1.7, (ob - oy) * 0.4)
                    C.line([(qx_, qy_ - ph_), (qx_ + pw_ * 0.62, qy_), (qx_, qy_ + ph_), (qx_ - pw_ * 0.62, qy_)], 0.5, True)
                    C.dots([(qx_, qy_)], 1.0)
    for xx in cols:
        xx = _snap(xx)
        C.mask(_R(xx - cw, yE, xx + cw, yb0))
        C.d("M%s %sV%s" % (_n(xx - cw), _n(yE + 3), _n(yb0)), 0.5)
        C.d("M%s %sV%s" % (_n(xx + cw), _n(yE + 3), _n(yb0)), 1.0)
        C.line([(xx - cw - 2, yE + 0.5), (xx - cw, yE + 3.5), (xx + cw, yE + 3.5), (xx + cw + 2, yE + 0.5)], 0.5)
        C.d("M%s %sh%s" % (_n(xx - cw - 1), _n(yb0 - 1.5), _n(2 * cw + 2)), 1.0)
    # the eaves throw their shadow down the head of the wall and across the capitals
    C.d(_hat((x0, yE + 0.5, x1, yE + max(3.0, 0.035 * W)), 1.5), 1.0)
    esh = []
    for q_ in range(int((x1 - x0) / 2.0)):
        xx = x0 + 1 + q_ * 2.0
        esh.append("M%s %sv%s" % (_n(xx), _n(yE + max(3.0, 0.035 * W)), _n(max(2.0, 0.03 * W) * (0.7 + 0.5 * rg.random()))))
    C.d("".join(esh), 0.5)
    # platform, steps and nagas
    C.mask(_R(cx - 0.47 * W, yb0, cx + 0.47 * W, by))
    C.d("M%s %sH%s" % (_n(cx - 0.47 * W), _n(yb0), _n(cx + 0.47 * W)), 1.0)
    C.d("M%s %sH%s" % (_n(cx - 0.47 * W), _n(yb0 + pb * 0.45), _n(cx + 0.47 * W)), 0.5)
    C.d(_hat((cx - 0.47 * W, yb0 + pb * 0.45, cx + 0.47 * W, by), 3.0, 90), 0.5)
    C.d(_hat((cx + 0.2 * W, yb0 + 1.5, cx + 0.47 * W, by), 1.5), 0.5)
    sw0, sw1 = 0.075 * W, 0.13 * W
    C.mask(_pl([(cx - sw0, yb0 - 1), (cx + sw0, yb0 - 1), (cx + sw1 + 3, by + 1), (cx - sw1 - 3, by + 1)], True))
    for q in range(5):
        f = q / 4.0
        C.d("M%s %sh%s" % (_n(cx - sw0 - (sw1 - sw0) * f), _n(yb0 + pb * f), _n(2 * (sw0 + (sw1 - sw0) * f))), 1.0 if q % 2 else 0.5)
    for sg in (-1, 1):
        a, b, c = (cx + sg * sw0, yb0 - 0.03 * W), (cx + sg * (sw0 + 0.04 * W), yb0 + pb * 0.6), (cx + sg * (sw1 + 0.05 * W), by - 1.5)
        C.d(_qd(a, b, c), 1.5)
        C.d(_qd((a[0], a[1] - 2), (b[0] + sg * 1.5, b[1] - 2), (c[0], c[1] - 2.5)), 0.5)
        hd = (c[0] + sg * 0.035 * W, c[1] - 0.085 * W)
        C.d(_qd(c, (c[0] + sg * 0.06 * W, c[1]), hd), 1.5)
        C.line([hd, (hd[0] - sg * 0.02 * W, hd[1] - 0.045 * W)], 1.0)
        C.line([(hd[0] + sg * 0.01 * W, hd[1] + 0.02 * W), (hd[0] + sg * 0.035 * W, hd[1] - 0.015 * W)], 1.0)
        C.line([hd, (hd[0] + sg * 0.03 * W, hd[1] + 0.012 * W)], 0.5)
    # side wings: low hipped roofs on their own columns
    for sg in (-1, 1):
        xa, xb = cx + sg * 0.47 * W, cx + sg * 0.79 * W
        lo_, hi_ = min(xa, xb), max(xa, xb)
        C.mask(_R(lo_, yE + 0.07 * W, hi_, by))
        C.open(C.clip(_R(lo_, yE + 0.09 * W, hi_, yb0)))
        C.raw(_rule(_wfam(lo_, hi_, yE + 0.09 * W + 1, yb0, 2.0, 3.0, 0.6, 31.0, 0.3, 13.0),
                    lambda x, y: (0.14 if sg < 0 else 0.4) + 0.5 * _cl(1 - (y - yE - 0.09 * W) / (0.07 * W)), 2.0, rg, soft=True))
        C.close()
        C.d("M%s %sH%s" % (_n(lo_), _n(yb0), _n(hi_)), 1.0)
        C.d(_hat((lo_, yb0 + 1.5, hi_, by), 3.0, 90), 0.5)
        C.d("M%s %sH%s" % (_n(lo_), _n(yb0 + pb * 0.45), _n(hi_)), 0.5)
        for q, f in enumerate((0.28, 0.66)):
            mx = xa + (xb - xa) * f
            ow, oy, ob = 0.035 * W, yE + 0.15 * W, yb0 - 0.05 * W
            d = "M%s %sL%s %sL%s %sL%s %sL%s %sz" % (_n(mx - ow), _n(ob), _n(mx - ow), _n(oy), _n(mx), _n(oy - ow * 1.2),
                                                     _n(mx + ow), _n(oy), _n(mx + ow), _n(ob))
            C.d(_hat((mx - ow, oy - ow * 1.2, mx + ow, ob), 1.5, 90), 1.0, C.clip(d))
            C.d(d, 1.0)
            C.line([(mx - ow - 1.5, oy), (mx, oy - ow * 1.2 - 2.5), (mx + ow + 1.5, oy)], 0.5)
        for f in (0.47, 0.97):
            xx = _snap(xa + (xb - xa) * f)
            C.d("M%s %sV%s" % (_n(xx - cw * 0.8), _n(yE + 0.09 * W), _n(yb0)), 0.5)
            C.d("M%s %sV%s" % (_n(xx + cw * 0.8), _n(yE + 0.09 * W), _n(yb0)), 1.0)
        A, B = (cx + sg * 0.44 * W, yE + 0.09 * W), (cx + sg * 0.46 * W, yE - 0.045 * W)
        Cc, D = (cx + sg * 0.69 * W, yE - 0.045 * W), (cx + sg * 0.84 * W, yE + 0.09 * W)
        rf = [A, B, Cc] + _q(Cc, (Cc[0] + sg * 0.05 * W, yE + 0.06 * W), D, 5)[1:]
        d = C.shape(rf, 1.0)
        rc = C.clip(d)
        C.d(_hat(_bbox(rf), 2.5, 90), 0.5, rc)
        C.d(_hat((min(A[0], D[0]), yE + 0.02 * W, max(A[0], D[0]), yE + 0.09 * W), 2.0), 0.5, rc)
        C.d(_hat(_bbox(rf), 2.0, 60 * sg), 0.5, rc) if sg > 0 else None
        C.d("M%s %sH%s" % (_n(B[0]), _n(B[1]), _n(Cc[0])), 1.5)
        C.d("".join("M%s %sl%s -2.5" % (_n(B[0] + (Cc[0] - B[0]) * q_ / 9.0), _n(B[1] - 0.5), _n(sg * 1.5)) for q_ in range(1, 10)), 0.5)
        C.d(_qd(D, (D[0] + sg * 0.04 * W, D[1] + 0.005 * W), (D[0] + sg * 0.05 * W, D[1] - 0.045 * W)), 1.5)
        C.d("M%s %sH%s" % (_n(A[0]), _n(A[1] + 1.5), _n(D[0])), 0.5)
    # the gables, widest and lowest first
    tiers = [(0.22, 0.0, 0.42), (0.34, 0.2, 0.2), (0.46, 0.4, 0.0)]
    for j in (2, 1, 0):
        hw, da, de = tiers[j]
        hw *= W
        ya, ye = apex0 + da * W, yE - de * W
        sides = []
        for sg in (-1, 1):
            sides.append(((cx, ya), (cx + sg * hw * 0.42, ya + (ye - ya) * 0.62), (cx + sg * hw, ye)))
        L_, R_ = sides
        d = "M%s %sQ%s %s %s %sH%sQ%s %s %s %sz" % (_n(cx), _n(ya), _n(L_[1][0]), _n(L_[1][1]), _n(L_[2][0]), _n(ye),
                                                   _n(R_[2][0]), _n(R_[1][0]), _n(R_[1][1]), _n(cx), _n(ya))
        C.shape(d, 0.5)
        cid = C.clip(d)
        nf = int(2 * hw / 3.0)
        t0 = 0.0 if j == 0 else tiers[j - 1][0] * W / hw * 0.8
        fan = []
        for q in range(nf + 1):
            xx = cx - hw + 2 * hw * q / float(nf)
            if abs(xx - cx) / hw >= t0 - 0.05:
                fan.append("M%s %sL%s %s" % (_n(cx), _n(ya), _n(xx), _n(ye)))
        C.d("".join(fan[::2]), 0.5, cid)
        C.d("".join(fan[1::2][len(fan) // 4:]), 0.5, cid)
        C.d("".join(fan[::2][-(len(fan) // 6 + 1):]), 1.0, cid)                      # the flank away from the light
        if j:
            yu = yE - tiers[j - 1][2] * W
            C.d(_hat((cx - hw, yu, cx + hw, yu + max(3.0, 0.03 * W)), 1.5), 1.0, cid)  # shadow of the tier above
        for sg, sd in ((-1, L_), (1, R_)):
            C.d(_qd(sd[0], sd[1], sd[2], t0, 1.0), 1.0)
            C.d(_qd((sd[0][0], sd[0][1] + 4), (sd[1][0] - sg * 1.5, sd[1][1] + 3), (sd[2][0] - sg * 6, sd[2][1]), t0, 1.0), 0.5, cid)
            pts = _q(sd[0], sd[1], sd[2], max(4, int(hw * (1 - t0) * 1.4 / 3.5)), max(t0, 0.07), 0.97)
            C.d("".join("M%s %sl%s -2.5" % (_n(px_), _n(py_), _n(sg * 2.0)) for px_, py_ in pts), 0.5)   # bai raka
            e = sd[2]
            C.d(_qd(e, (e[0] + sg * 0.05 * W, e[1] + 0.005 * W), (e[0] + sg * 0.06 * W, e[1] - 0.05 * W)), 1.5)   # hang hong
            C.d(_qd((e[0] + sg * 0.06 * W, e[1] - 0.05 * W), (e[0] + sg * 0.062 * W, e[1] - 0.08 * W), (e[0] + sg * 0.04 * W, e[1] - 0.085 * W)), 0.5)
        C.d("M%s %sH%s" % (_n(cx - hw), _n(ye), _n(cx + hw)), 1.0)
        C.d("M%s %sH%s" % (_n(cx - hw + 3), _n(ye - 2.5), _n(cx + hw - 3)), 0.5, cid)
    # pediment medallion and curls
    my = yE - 0.42 * W - 0.1 * W
    mr = max(2.5, 0.045 * W)
    C.mask(_E(cx, my, mr + 1, mr + 1))
    C.d(_E(cx, my, mr, mr), 1.0)
    C.d(_E(cx, my, mr * 0.5, mr * 0.5), 0.5)
    C.dots([(cx, my)], 1.0)
    if W > 70:
        for sg in (-1, 1):
            _curl(C, cx + sg * 0.085 * W, my + 0.035 * W, mr * 0.8, PI / 2 - sg * 1.1, sg)
    # chofa: the horned finial, swelling from the ridge to a hair at the tip
    a, b, c = (cx, apex0 + 1), (cx - 0.045 * W, apex0 - 0.07 * W), (cx + 0.012 * W, apex0 - 0.115 * W)
    C.d(_qd(a, b, c, 0, 0.5), 1.5)
    C.d(_qd(a, b, c, 0.5, 1), 1.0)
    C.d(_qd(c, (cx + 0.04 * W, apex0 - 0.15 * W), (cx - 0.012 * W, apex0 - 0.175 * W)), 0.5)
    C.line([(cx - 0.02 * W, apex0 - 0.055 * W), (cx - 0.05 * W, apex0 - 0.045 * W)], 0.5)


def _elephant(C, x0, gy, H):
    """Royal elephant in profile, in Lanna regalia.  Domed head, fan ear with folds, trunk curled
    round a lotus, rounded belly, column legs with toenails.  The form is turned with contour
    strokes that ring the barrel and the legs and swell as they pass into shadow."""
    def P(u, v):
        return (x0 + u * H, gy - v * H)
    big = H > 44
    px = 1.0 / H
    for leg in ([(0.2, 0.42), (0.21, 0.02), (0.37, 0.02), (0.36, 0.2), (0.38, 0.42)],
                [(0.8, 0.45), (0.84, 0.03), (1.0, 0.03), (0.97, 0.25), (0.96, 0.45)]):      # far legs, in shadow
        lp = [P(*q) for q in leg]
        d = C.shape(lp, 0.5)
        lc = C.clip(d)
        ua, ub = leg[0][0] - 0.02, leg[-1][0] + 0.06
        v = 0.0
        while v < 0.5:                                                   # hoops ring the far legs, deep in shadow
            a, b, c = P(ua, v + 0.035), P((ua + ub) / 2, v - 0.06), P(ub, v + 0.035)
            C.d(_qd(a, b, c), 1.0, lc)
            C.d(_qd(a, b, c, 0.0, 0.4), 1.5, lc)
            v += 2.0 * px
    body = [(0.03, 0.78), (0.0, 0.66), (0.01, 0.5), (0.04, 0.36), (0.03, 0.2), (0.05, 0.05), (0.04, 0.0), (0.25, 0.0),
            (0.24, 0.12), (0.27, 0.3), (0.36, 0.36), (0.5, 0.33), (0.62, 0.36), (0.68, 0.3), (0.67, 0.1), (0.66, 0.0),
            (0.87, 0.0), (0.86, 0.15), (0.87, 0.38), (0.9, 0.5), (0.96, 0.55), (1.03, 0.6), (1.09, 0.72), (1.11, 0.86),
            (1.08, 0.99), (0.99, 1.07), (0.88, 1.06), (0.78, 0.97), (0.66, 1.0), (0.45, 1.03), (0.25, 0.99), (0.1, 0.9)]
    d = C.shape(_chaikin([P(*q) for q in body], 2 if big else 1), 1.0)
    cid = C.clip(d)
    # rings round the barrel
    u = 0.03
    k = 0
    st = (2.0 if big else 2.5) * px
    while u < 0.76:
        a, b, c = P(u + 0.03, 1.05), P(u - 0.1, 0.66), P(u + 0.04, 0.3)
        rump = u < 0.15
        if rump or k % 2:
            C.d(_qd(a, b, c, 0.06, 0.42), 0.5, cid)
        C.d(_qd(a, b, c, 0.42, 0.7), 1.0 if rump else 0.5, cid)
        C.d(_qd(a, b, c, 0.7, 1.0), 1.5 if rump else 1.0, cid)
        if 0.3 < u < 0.66 and k % 2 == 0:
            C.d(_qd(a, b, c, 0.86, 1.0), 1.5, cid)                       # the belly, deepest
        u += st
        k += 1
    u = 0.76
    while u < 0.92:                                                      # shoulder
        a, b, c = P(u, 0.97), P(u + 0.07, 0.7), P(u - 0.01, 0.42)
        C.d(_qd(a, b, c, 0.25, 0.7), 0.5, cid)
        C.d(_qd(a, b, c, 0.7, 1.0), 1.0, cid)
        u += st * 1.25
    for ua, ub in ((0.02, 0.27), (0.65, 0.89)):                          # legs: hoops round the columns
        v = 0.03
        while v < 0.4:
            a, b, c = P(ua, v + 0.035), P((ua + ub) / 2, v - 0.065), P(ub, v + 0.035)
            C.d(_qd(a, b, c, 0.0, 0.2), 1.5, cid)                        # the shadow side of the column
            C.d(_qd(a, b, c, 0.2, 0.44), 1.0, cid)
            C.d(_qd(a, b, c, 0.44, 0.7 if int(v * H) % 2 else 0.86), 0.5, cid)
            C.d(_qd(a, b, c, 0.95, 1.0), 0.5, cid)
            v += st
        for f in (0.22, 0.5, 0.78):                                       # toenails
            xx = P(ua + (ub - ua) * f, 0)[0]
            rr = max(1.5, 0.028 * H)
            C.mask(_arc(xx, gy, rr, rr * 1.3, PI, 2 * PI) + "z")
            C.d(_arc(xx, gy, rr, rr * 1.3, PI, 2 * PI), 1.0)
        for v, wd in ((0.1, 1.0), (0.135, 0.5)):                          # anklets
            C.mask(_pl([P(ua + 0.015, v + 0.012), P(ub - 0.01, v + 0.012), P(ub - 0.01, v - 0.03), P(ua + 0.015, v - 0.03)], True))
        C.d(_qd(P(ua + 0.01, 0.115), P((ua + ub) / 2, 0.085), P(ub - 0.005, 0.115)), 1.0)
        C.d(_qd(P(ua + 0.01, 0.085), P((ua + ub) / 2, 0.055), P(ub - 0.005, 0.085)), 1.0)
        C.dots([P(ua + (ub - ua) * f, 0.085 - 0.012 * math.sin(PI * f)) for f in (0.2, 0.4, 0.6, 0.8)], 1.0)
    v = 0.62                                                             # head: hoops over the dome and cheek
    while v < 1.08:
        a, b, c = P(0.84, v + 0.02), P(1.0, v - 0.05), P(1.13, v + 0.01)
        C.d(_qd(a, b, c), 1.0 if v < 0.72 else 0.5, cid)
        v += st * (1.0 if v < 0.75 else 1.5)
    # crupper and collar
    for a, b, c in ((P(0.28, 0.76), P(0.13, 0.7), P(0.0, 0.76)), (P(0.79, 0.99), P(0.84, 0.72), P(0.92, 0.5))):
        C.white(_qd(a, b, c), cid, max(2.5, 0.05 * H))
        C.d(_qd((a[0], a[1] - 0.02 * H), (b[0], b[1] - 0.02 * H), (c[0], c[1] - 0.02 * H)), 1.0, cid)
        C.d(_qd((a[0], a[1] + 0.02 * H), (b[0], b[1] + 0.02 * H), (c[0], c[1] + 0.02 * H)), 0.5, cid)
        C.dots(_q(a, b, c, 6)[1:-1], 1.5 if big else 1.0)
    # caparison, in bands, with medallion, diaper and tassels
    cl = [P(0.27, 1.0), P(0.45, 1.04), P(0.69, 1.005), P(0.71, 0.56)]
    for q in range(8):
        cl.append(P(0.71 - 0.44 * (q + 0.5) / 8.0, 0.49 if q % 2 == 0 else 0.55))
    cl.append(P(0.27, 0.56))
    d = C.shape(cl, 1.0)
    cc = C.clip(d)
    for ins, wd in ((0.025, 0.5), (0.05, 1.0), (0.065, 0.5)):
        C.line([P(0.27 + ins, 1.0 - ins * 0.7), P(0.45, 1.04 - ins), P(0.69 - ins, 1.005 - ins), P(0.71 - ins, 0.56 + ins), P(0.27 + ins, 0.56 + ins)], wd, True)
    C.dots([P(0.27 + 0.0375, 0.6 + 0.045 * i) for i in range(9)] + [P(0.71 - 0.0375, 0.6 + 0.045 * i) for i in range(9)]
           + [P(0.33 + 0.045 * i, 0.5975) for i in range(8)], 1.0)
    mc = P(0.49, 0.79)
    mr = 0.085 * H
    C.d(_E(mc[0], mc[1], mr, mr), 1.0)
    C.d(_E(mc[0], mc[1], mr * 0.78, mr * 0.78), 0.5)
    C.d(_E(mc[0], mc[1], mr * 0.3, mr * 0.3), 1.0)
    for i in range(8):                                                   # lotus rosette
        a = i * PI / 4
        t = (mc[0] + mr * 0.74 * math.cos(a), mc[1] + mr * 0.74 * math.sin(a))
        e1 = (mc[0] + mr * 0.5 * math.cos(a - 0.4), mc[1] + mr * 0.5 * math.sin(a - 0.4))
        e2 = (mc[0] + mr * 0.5 * math.cos(a + 0.4), mc[1] + mr * 0.5 * math.sin(a + 0.4))
        b0 = (mc[0] + mr * 0.3 * math.cos(a), mc[1] + mr * 0.3 * math.sin(a))
        C.d(_qd(b0, e1, t) + _qd(b0, e2, t), 0.5)
    if big:
        dd = []
        for i in range(8):
            for j in range(8):
                q = P(0.355 + 0.04 * i + (0.02 if j % 2 else 0), 0.645 + 0.04 * j)
                if math.hypot(q[0] - mc[0], q[1] - mc[1]) > mr * 1.2 and q[0] < P(0.63, 0)[0] and q[1] > P(0, 0.93)[1]:
                    dd.append(q)
        C.dots(dd, 1.0)
    C.d(_hat((x0 + 0.58 * H, gy - 1.05 * H, x0 + 0.72 * H, gy - 0.5 * H), 2.0, 60), 0.5, cc)   # the cloth turns from the light
    C.d(_hat((x0 + 0.27 * H, gy - 0.6 * H, x0 + 0.72 * H, gy - 0.48 * H), 1.5), 0.5, cc)
    for q in range(8):                                                   # tassels on the points
        if q % 2 == 0:
            t = P(0.71 - 0.44 * (q + 0.5) / 8.0, 0.49)
            C.d("M%s %sv%s" % (_n(t[0]), _n(t[1]), _n(0.035 * H)), 1.0)
            C.d(_E(t[0], t[1] + 0.05 * H, max(1.0, 0.014 * H), max(1.5, 0.022 * H)), 0.5)
    # tail
    C.white(_qd(P(0.03, 0.78), P(-0.06, 0.62), P(-0.035, 0.36)), None, 3.0)
    C.d(_qd(P(0.03, 0.78), P(-0.06, 0.62), P(-0.035, 0.36)), 1.5)
    C.line([P(-0.065, 0.28), P(-0.035, 0.36), P(-0.005, 0.27)], 0.5)
    C.line([P(-0.035, 0.36), P(-0.035, 0.25)], 1.0)
    # ear: a fan with a scalloped hem, folded from the hinge
    ear = _chaikin([P(0.85, 0.98), P(0.74, 1.05), P(0.63, 0.96), P(0.575, 0.78), P(0.61, 0.6), P(0.7, 0.49), P(0.8, 0.52),
                    P(0.865, 0.64), P(0.885, 0.8)], 2)
    d = C.shape(ear, 1.0)
    ce = C.clip(d)
    hn = P(0.86, 0.87)
    for q in range(9):
        f = q / 8.0
        e = P(0.74 - 0.15 * math.sin(PI * f) - 0.04 * f, 1.03 - 0.53 * f)
        m = ((hn[0] + e[0]) / 2 + 0.03 * H * (f - 0.5), (hn[1] + e[1]) / 2 + 0.03 * H)
        C.d(_qd(hn, m, e, 0.12, 0.96), 0.5, ce)
        if q % 2 == 0 or f > 0.6:
            C.d(_qd(hn, m, e, 0.4, 0.8), 1.0, ce)                        # each fold swells in its hollow
    C.d(_hat((x0 + 0.58 * H, gy - 0.66 * H, x0 + 0.9 * H, gy - 0.48 * H), 1.5, 30), 0.5, ce)
    C.d(_qd(P(0.6, 0.78), P(0.62, 0.6), P(0.72, 0.52)), 0.5, ce)
    # headdress: band, net and jewels
    C.white(_qd(P(0.89, 1.06), P(1.02, 1.05), P(1.105, 0.9)), cid, max(2.5, 0.045 * H))
    C.d(_qd(P(0.89, 1.045), P(1.01, 1.03), P(1.09, 0.895)), 1.0)
    C.d(_qd(P(0.895, 1.015), P(1.0, 1.0), P(1.07, 0.89)), 0.5)
    C.dots(_q(P(0.89, 1.03), P(1.005, 1.015), P(1.08, 0.892), 5)[1:-1], 1.0)
    jw = P(1.085, 0.86)
    C.mask(_E(jw[0], jw[1], max(1.5, 0.022 * H), max(2.0, 0.035 * H)))
    C.d(_E(jw[0], jw[1], max(1.5, 0.022 * H), max(2.0, 0.035 * H)), 0.5)
    C.dots([jw], 1.0)
    # eye
    e0, e1 = P(0.975, 0.835), P(1.04, 0.84)
    C.mask("M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(e0[0]), _n(e0[1]), _n(P(1.005, 0.875)[0]), _n(P(1.005, 0.875)[1]), _n(e1[0]), _n(e1[1]),
                                                _n(P(1.01, 0.81)[0]), _n(P(1.01, 0.81)[1]), _n(e0[0]), _n(e0[1])))
    C.d(_qd(e0, P(1.005, 0.875), e1), 1.0)
    C.d(_qd(e0, P(1.01, 0.81), e1), 0.5)
    C.dots([P(1.01, 0.84)], 1.5)
    C.d(_qd(P(0.965, 0.8), P(1.005, 0.775), P(1.045, 0.8)), 0.5)
    # trunk: a tapering ribbon, ringed, its tip curled round a lotus bud
    cl_ = _chaikin([P(1.05, 0.76), P(1.14, 0.6), P(1.175, 0.42), P(1.155, 0.26), P(1.2, 0.14), P(1.3, 0.115), P(1.375, 0.2),
                    P(1.36, 0.31)], 3 if big else 2, False)
    le, ri = [], []
    n = len(cl_)
    for i, (qx, qy) in enumerate(cl_):
        a, b = cl_[max(0, i - 1)], cl_[min(n - 1, i + 1)]
        dx_, dy_ = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx_, dy_) or 1.0
        hw = H * (0.095 - 0.062 * (i / (n - 1.0)) ** 0.8)
        le.append((qx - dy_ / ln * hw, qy + dx_ / ln * hw))
        ri.append((qx + dy_ / ln * hw, qy - dx_ / ln * hw))
    tip = cl_[-1]
    _petal(C, tip[0], tip[1] + 0.02 * H, 0.25, 0.2 * H, 0.045 * H, 1, 0.5)
    _petal(C, tip[0], tip[1] + 0.02 * H, 0.05, 0.17 * H, 0.03 * H, 1, 0.5)
    tc = C.clip(C.shape(le + ri[::-1], 1.0))
    seglen = 1.0 * H / n
    stp = max(1, int(round(2.0 / max(seglen, 0.1))))
    for i in range(1, n - 1, stp):
        m = ((le[i][0] + ri[i][0]) / 2, (le[i][1] + ri[i][1]) / 2)
        bow = (cl_[min(n - 1, i + 1)][0] - cl_[i - 1][0], cl_[min(n - 1, i + 1)][1] - cl_[i - 1][1])
        bl = math.hypot(*bow) or 1.0
        hw_ = H * (0.095 - 0.062 * (i / (n - 1.0)) ** 0.8)
        mm = (m[0] + bow[0] / bl * hw_ * 1.5, m[1] + bow[1] / bl * hw_ * 1.5)
        C.d(_qd(le[i], mm, ri[i], 0.0, 0.2), 1.5, tc)                   # rings round the trunk, heavy on its shadow side
        C.d(_qd(le[i], mm, ri[i], 0.2, 0.48), 1.0, tc)
        C.d(_qd(le[i], mm, ri[i], 0.48, 0.74 if (i // stp) % 2 else 0.9), 0.5, tc)
    # tusk with gold bands
    t0, t1 = P(1.02, 0.6), P(1.3, 0.56)
    C.shape("M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(t0[0]), _n(t0[1]), _n(P(1.15, 0.4)[0]), _n(P(1.15, 0.4)[1]), _n(t1[0]), _n(t1[1]),
                                                 _n(P(1.15, 0.5)[0]), _n(P(1.15, 0.5)[1]), _n(P(1.045, 0.67)[0]), _n(P(1.045, 0.67)[1])), 0.5)
    C.d(_qd(t0, P(1.15, 0.4), t1, 0.08, 0.85), 1.0)
    for f in (0.3, 0.42):
        a = _q(t0, P(1.15, 0.4), t1, 1, f, f)[0]
        b = _q(P(1.045, 0.67), P(1.15, 0.5), t1, 1, f, f)[0]
        C.line([a, b], 1.0)


def _hero(C, x, y, s, flip=1):
    """A great kranok: coiled head with a crest of flames streaming from it, each flame veined
    and shaded, and smaller counter-flames beneath."""
    def flame(bx, by, ang, L, sh=1):
        dx, dy = math.cos(ang), -math.sin(ang)
        qx, qy = -dy * sh, dx * sh
        wd = 0.2 * L

        def T(a, b):
            return (x + flip * (bx + dx * a * L + qx * b * wd), y + (by + dy * a * L + qy * b * wd))
        tip = T(1.0, -1.1)
        b0, b1 = T(0, 1), T(0, -1)
        c0, c1 = T(0.55, 1.55), T(0.5, -0.9)
        C.shape("M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(b0[0]), _n(b0[1]), _n(c0[0]), _n(c0[1]), _n(tip[0]), _n(tip[1]),
                                                     _n(c1[0]), _n(c1[1]), _n(b1[0]), _n(b1[1])), 0.5)
        C.d(_qd(b0, c0, tip, 0.12, 0.88), 1.0)
        C.d(_qd(T(0, 0), T(0.5, 0.25), tip, 0.08, 0.92), 0.5)
        for k_ in range(int(max(1, wd / 1.6))):
            off = 0.5 + 0.9 * (k_ + 0.5) / max(1, wd / 1.6)
            C.d(_qd(T(0.04, off * 0.7), T(0.52, off + 0.25), tip, 0.1, 0.72 - 0.12 * k_), 0.5)
    for j in (2, 1, 0):
        flame(s * (0.7 + 0.95 * j), s * 0.62, math.radians(-28 - 9 * j), s * (1.5 - 0.25 * j), -1)
    n = 6
    for i in range(n - 1, -1, -1):
        flame(s * (0.35 + 0.72 * i), s * (0.42 - 0.04 * i), math.radians(78 - 11 * i), s * (2.9 - 0.33 * i))
    C.mask(_E(x, y, s * 1.06, s * 1.06))
    sp, sp2 = [], []
    for i in range(34):
        t = i / 33.0
        a = PI * 0.5 + (0.4 + t * 2.4 * 2 * PI) * 1
        r = s * (1 - 0.86 * t)
        sp.append((x + flip * r * math.cos(a), y + r * math.sin(a)))
        if t < 0.8:
            sp2.append((x + flip * (r - 2.0) * math.cos(a), y + (r - 2.0) * math.sin(a)))
    C.line(sp, 1.0)
    C.line(sp2, 0.5)
    k = 4.0
    while k < s * 0.5:
        C.d(_arc(x, y, s - k, s - k, 0.3 if flip > 0 else PI - 1.8, 1.8 if flip > 0 else PI - 0.3), 0.5)
        k += 1.5
    C.dots([(x + flip * s * 0.02, y - s * 0.02)], 1.5)


def _lfr(x, y, ang):
    dx, dy = math.sin(ang), -math.cos(ang)
    return lambda a, b: (x + dx * a - dy * b, y + dy * a + dx * b)


def _lens(C, a, b, wd, vein=True):
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * wd * 2, dx / ln * wd * 2
    d = "M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(a[0]), _n(a[1]), _n(mx + nx), _n(my + ny), _n(b[0]), _n(b[1]),
                                             _n(mx - nx), _n(my - ny), _n(a[0]), _n(a[1]))
    if vein is None:
        return d
    C.shape(d, 0.5)
    if vein:
        C.d(_qd(a, (mx + nx * 0.15, my + ny * 0.15), b, 0.1, 0.85), 0.5)


def _heart(C, T, a0, l, drip=True):
    """Bodhi / taro leaf: heart-shaped, notched at the stalk, drawn out to a drip tip, veined."""
    half = _q(T(a0, 0), T(a0 - 0.14 * l, 0.42 * l), T(a0 + 0.36 * l, 0.44 * l), 3)
    half += _q(T(a0 + 0.36 * l, 0.44 * l), T(a0 + 0.7 * l, 0.42 * l), T(a0 + (0.86 if drip else 0.95) * l, 0.07 * l if drip else 0.0), 4)[1:]
    oth = _q(T(a0, 0), T(a0 - 0.14 * l, -0.42 * l), T(a0 + 0.36 * l, -0.44 * l), 3)
    oth += _q(T(a0 + 0.36 * l, -0.44 * l), T(a0 + 0.7 * l, -0.42 * l), T(a0 + (0.86 if drip else 0.95) * l, -0.07 * l if drip else 0.0), 4)[1:]
    tip = [T(a0 + 1.2 * l, 0.05 * l)] if drip else []
    C.shape(half + tip + oth[::-1], 0.5)
    C.line([T(a0, 0), T(a0 + (1.1 if drip else 0.9) * l, 0)], 0.5)
    for f, r in ((0.12, 0.3), (0.34, 0.27), (0.56, 0.2)):
        for sg in (-1, 1):
            C.line([T(a0 + f * l, 0), T(a0 + (f + 0.17) * l, sg * r * l)], 0.5)


def _spray(C, x, y, L, rng, n=6):
    """One plant of the Himmapan wood, white on the dark: bodhi leaves, a fern, broad blades,
    a leafy shoot or a great taro leaf, by turns of the dice."""
    kind = rng.randrange(5)
    j = rng.uniform(-0.2, 0.2)
    if kind == 0:                                           # bodhi: heart leaves with drip tips
        for a in ((-0.85, 0.75) if rng.random() < 0.5 else (-1.0, 0.0, 0.95)):
            T = _lfr(x, y, a + j)
            l = L * rng.uniform(0.5, 0.62)
            C.white(_pl([T(0, 0), T(0.32 * L, 0)]), None, 1.0)
            _heart(C, T, 0.3 * L, l)
    elif kind == 1:                                         # fern: fronds of paired leaflets
        for a, sg in ((-0.55, -1), (0.6, 1)):
            T = _lfr(x, y, a + j)
            l = L * rng.uniform(0.95, 1.2)
            sp = [T(l * f, sg * 0.22 * l * f * f) for f in [q_ / 7.0 for q_ in range(8)]]
            C.white(_pl(sp), None, 1.0)
            ds = []
            for q_ in range(1, 7):
                p = sp[q_]
                ll = l * 0.3 * (1 - q_ / 8.5)
                for s2 in (-1, 1):
                    e = T(l * q_ / 7.0 + ll * 0.45, sg * 0.22 * l * (q_ / 7.0) ** 2 + s2 * ll)
                    ds.append(_lens(C, p, e, max(1.0, ll * 0.2), None))
            ds.append(_lens(C, sp[-2], sp[-1], max(1.0, l * 0.035), None))
            C.shape("".join(ds), 0.5)
    elif kind == 2:                                         # three broad blades with ribbed sides
        for a in (-0.75, 0.05, 0.8):
            T = _lfr(x, y, a + j + rng.uniform(-0.12, 0.12))
            l = L * rng.uniform(0.8, 1.1) * (1.0 if a else 1.12)
            wd = max(2.0, l * 0.17)
            _lens(C, T(0, 0), T(l, 0.12 * l * (1 if a > 0 else -1)), wd)
            for f in (0.3, 0.45, 0.6):
                for sg in (-1, 1):
                    C.line([T(l * f, 0.12 * l * f * (1 if a > 0 else -1)), T(l * (f + 0.12), sg * wd * 0.62 + 0.12 * l * f * (1 if a > 0 else -1))], 0.5)
    elif kind == 3:                                         # a shoot with alternate leaves
        sg = 1 if rng.random() < 0.5 else -1
        T = _lfr(x, y, j + sg * 0.25)
        l = L * rng.uniform(1.0, 1.25)
        sp = [T(l * f, -sg * 0.2 * l * f * f) for f in [q_ / 6.0 for q_ in range(7)]]
        C.white(_pl(sp), None, 1.0)
        for q_ in range(1, 6):
            s2 = 1 if q_ % 2 else -1
            p = sp[q_]
            _lens(C, p, T(l * (q_ / 6.0 + 0.2), -sg * 0.2 * l * (q_ / 6.0) ** 2 + s2 * 0.3 * l * (1 - q_ / 12.0)), max(1.5, l * 0.07))
        _lens(C, sp[-2], T(l * 1.12, -sg * 0.27 * l), max(1.5, l * 0.06))
    else:                                                   # one great taro leaf on its stalk
        T = _lfr(x, y, j * 2.5)
        C.white(_pl([T(0, 0), T(0.3 * L, 0)]), None, 1.0)
        _heart(C, T, 0.25 * L, L * 0.9, False)


def _rosette(C, x, y, r):
    for i in range(5):
        a = i * 2 * PI / 5 - PI / 2
        C.mask(_E(x + r * 0.62 * math.cos(a), y + r * 0.62 * math.sin(a), r * 0.48, r * 0.48))
        C.d(_E(x + r * 0.62 * math.cos(a), y + r * 0.62 * math.sin(a), r * 0.48, r * 0.48), 0.5)
    C.mask(_E(x, y, r * 0.34, r * 0.34))
    C.d(_E(x, y, r * 0.34, r * 0.34), 0.5)
    C.dots([(x, y)], 1.0)


def _bird(C, x, y, L, flip=1):
    """Long-tailed bird perched in the leaves."""
    f = flip
    for k, (dxl, dyl) in enumerate(((-1.5, 0.75), (-1.25, 1.05), (-0.95, 1.25))):          # tail plumes
        t = (x + f * dxl * L, y + dyl * L)
        C.shape("M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(x - f * 0.3 * L), _n(y + 0.1 * L), _n(x + f * (dxl * 0.5) * L), _n(y + (dyl * 0.25) * L),
                                                     _n(t[0]), _n(t[1]), _n(x + f * (dxl * 0.5 + 0.12) * L), _n(y + (dyl * 0.6) * L),
                                                     _n(x - f * 0.2 * L), _n(y + 0.22 * L)), 0.5)
        C.d(_qd((x - f * 0.28 * L, y + 0.15 * L), (x + f * (dxl * 0.5 + 0.05) * L, y + dyl * 0.42 * L), t, 0.1, 0.9), 0.5)
    C.mask(_E(x, y, 0.5 * L, 0.3 * L, -25 * f))
    C.d(_E(x, y, 0.5 * L, 0.3 * L, -25 * f), 1.0)
    for k in range(3):                                                                    # wing coverts
        C.d(_qd((x - f * (0.3 - 0.12 * k) * L, y - (0.02 + 0.03 * k) * L), (x - f * (0.05 - 0.1 * k) * L, y + (0.2 - 0.02 * k) * L),
                (x + f * (0.2 + 0.05 * k) * L, y + (0.0 - 0.05 * k) * L)), 0.5)
    hx, hy = x + f * 0.46 * L, y - 0.3 * L
    C.mask(_E(hx, hy, 0.2 * L, 0.2 * L))
    C.d(_E(hx, hy, 0.2 * L, 0.2 * L), 1.0)
    C.shape([(hx + f * 0.17 * L, hy - 0.06 * L), (hx + f * 0.42 * L, hy + 0.02 * L), (hx + f * 0.17 * L, hy + 0.08 * L)], 0.5)
    C.dots([(hx + f * 0.05 * L, hy - 0.03 * L)], 1.0)
    C.line([(hx - f * 0.05 * L, hy - 0.19 * L), (hx - f * 0.16 * L, hy - 0.42 * L)], 0.5)   # crest
    C.line([(hx, hy - 0.2 * L), (hx - f * 0.04 * L, hy - 0.45 * L)], 0.5)
    C.line([(x + f * 0.05 * L, y + 0.28 * L), (x + f * 0.05 * L, y + 0.45 * L)], 1.0)       # legs
    C.line([(x - f * 0.08 * L, y + 0.27 * L), (x - f * 0.08 * L, y + 0.45 * L)], 1.0)


def _dog(C, x, y, hh, flip=1):
    """A small dog sitting at the water's edge, looking toward the temple."""
    pts = [(0.0, 0.78), (0.1, 0.87), (0.2, 0.96), (0.27, 1.08), (0.36, 0.98), (0.44, 0.86), (0.47, 0.68), (0.63, 0.42),
           (0.7, 0.14), (0.86, 0.1), (0.97, 0.3), (0.9, 0.36), (0.83, 0.2), (0.74, 0.02), (0.4, 0.0), (0.4, 0.1), (0.35, 0.2),
           (0.31, 0.0), (0.16, 0.0), (0.2, 0.1), (0.22, 0.45), (0.18, 0.62), (0.08, 0.68)]
    P = [(x + flip * (u - 0.45) * hh, y - v * hh) for u, v in pts]
    C.shape(_chaikin(P, 1), 1.0)

    def Q(u, v):
        return (x + flip * (u - 0.45) * hh, y - v * hh)
    C.dots([Q(0.17, 0.86)], 1.0)
    C.dots([Q(0.015, 0.79)], 1.5)
    C.line([Q(0.2, 0.66), Q(0.44, 0.72)], 1.0)                                              # collar
    C.line([Q(0.3, 0.86), Q(0.29, 1.02)], 0.5)
    C.d(_qd(Q(0.45, 0.5), Q(0.56, 0.3), Q(0.52, 0.08)), 0.5)                                # haunch
    for v in (0.2, 0.3, 0.4):
        C.line([Q(0.56 + 0.1 * (0.45 - v), v), Q(0.66 + 0.06 * (0.45 - v), v - 0.02)], 0.5)


def _pod(C, x, yb, sz, rng):
    """Lotus seed pod on its stalk."""
    lean = rng.uniform(-0.2, 0.2)
    top = (x + lean * sz, yb - sz * rng.uniform(1.1, 1.6))
    C.white(_qd((x + 0.5, yb), (x + 0.5, yb - sz * 0.8), (top[0] + 0.5, top[1])), None, 3.5)
    C.d(_qd((x, yb), (x, yb - sz * 0.8), top), 1.0)
    C.d(_qd((x + 1.5, yb), (x + 1.5, yb - sz * 0.8), (top[0] + 1.5, top[1])), 0.5)
    rx, ry, hh = sz * 0.36, sz * 0.13, sz * 0.4
    cy = top[1] - hh
    C.shape("M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(top[0] - rx), _n(cy), _n(top[0] - rx * 0.8), _n(top[1] - hh * 0.2), _n(top[0]), _n(top[1]),
                                                 _n(top[0] + rx * 0.8), _n(top[1] - hh * 0.2), _n(top[0] + rx), _n(cy)), 0.5)
    for q in range(-3, 4):
        f = q / 3.5
        C.d(_qd((top[0] + rx * f, cy + ry * math.sqrt(1 - f * f)), (top[0] + rx * 0.75 * f, top[1] - hh * 0.25), top, 0, 0.85),
            1.0 if q > 1 else 0.5)
    C.mask(_E(top[0], cy, rx, ry))
    C.d(_E(top[0], cy, rx, ry), 1.0)
    C.dots([(top[0] + rx * 0.55 * math.cos(a), cy + ry * 0.55 * math.sin(a)) for a in [i * PI / 3 for i in range(6)]] + [(top[0], cy)],
           1.5 if sz > 20 else 1.0)


def _leaf(C, x, yb, sz, rng):
    """A lotus leaf held above the water: tilted dish with radial veins and a shaded near lip."""
    lean = rng.uniform(-0.3, 0.3)
    c = (x + lean * sz, yb - sz * rng.uniform(0.9, 1.4))
    C.white(_qd((x, yb), (x, yb - sz * 0.7), c), None, 3.5)
    C.d(_qd((x, yb), (x, yb - sz * 0.7), c), 1.5)
    rot = rng.uniform(-18, 18)
    rr = math.radians(rot)
    rx, ry = sz * 0.85, sz * 0.34
    C.mask(_E(c[0], c[1] + 2.5, rx, ry, rot))
    C.d(_arc(c[0], c[1] + 2.5, rx, ry, 0.15, PI - 0.15, rot), 1.0)
    C.mask(_E(c[0], c[1], rx, ry, rot))
    C.d(_E(c[0], c[1], rx, ry, rot), 1.0)
    hub = (c[0] + rx * 0.08, c[1] - ry * 0.12)
    for i in range(14):
        a = i * 2 * PI / 14 + 0.2
        e = (c[0] + rx * math.cos(a) * math.cos(rr) - ry * math.sin(a) * math.sin(rr),
             c[1] + rx * math.cos(a) * math.sin(rr) + ry * math.sin(a) * math.cos(rr))
        C.line([hub, (hub[0] + (e[0] - hub[0]) * 0.93, hub[1] + (e[1] - hub[1]) * 0.93)], 0.5)
        if 0.1 < a < PI:                                       # near lip in shade: short strokes from the rim
            for f in (0.3, 0.62):
                a2 = a + f * 2 * PI / 14
                e2 = (c[0] + rx * math.cos(a2) * math.cos(rr) - ry * math.sin(a2) * math.sin(rr),
                      c[1] + rx * math.cos(a2) * math.sin(rr) + ry * math.sin(a2) * math.cos(rr))
                C.line([e2, (hub[0] + (e2[0] - hub[0]) * 0.6, hub[1] + (e2[1] - hub[1]) * 0.6)], 1.0 if f < 0.5 else 0.5)
    C.d(_E(hub[0], hub[1], max(1.5, rx * 0.07), max(1.0, ry * 0.07), rot), 0.5)


def _fish(C, x, y, L, flip):
    f = flip
    C.d(_arc(x, y + 1, L * 0.75, max(1.5, L * 0.16), PI * 1.1, PI * 1.9), 0.5)          # ring it rises in
    C.shape("M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(x - f * L * 0.5), _n(y), _n(x), _n(y - L * 0.26), _n(x + f * L * 0.45), _n(y),
                                                 _n(x), _n(y + L * 0.2), _n(x - f * L * 0.5), _n(y)), 0.5)
    C.d(_qd((x - f * L * 0.5, y), (x, y - L * 0.26), (x + f * L * 0.45, y), 0.1, 0.9), 1.0)
    C.line([(x - f * L * 0.72, y - L * 0.17), (x - f * L * 0.5, y), (x - f * L * 0.72, y + L * 0.15)], 1.0)
    C.line([(x - f * L * 0.66, y - L * 0.06), (x - f * L * 0.52, y), (x - f * L * 0.66, y + L * 0.05)], 0.5)
    C.dots([(x + f * L * 0.3, y - L * 0.03)], 1.0)
    for q in (-0.1, 0.06, 0.2):
        C.d(_qd((x + f * L * q, y - L * 0.09), (x + f * L * (q - 0.06), y), (x + f * L * q, y + L * 0.07)), 0.5)


def _dragonfly(C, x, y, L, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    for off, wl, rot in ((0.08, 0.62, 62), (0.08, 0.62, -62), (-0.06, 0.55, 110), (-0.06, 0.55, -110)):
        a = ang + math.radians(rot)
        wx, wy = x + ca * L * off + math.cos(a) * L * wl * 0.5, y + sa * L * off + math.sin(a) * L * wl * 0.5
        C.mask(_E(wx, wy, L * wl * 0.5, max(1.0, L * 0.1), math.degrees(a)))
        C.d(_E(wx, wy, L * wl * 0.5, max(1.0, L * 0.1), math.degrees(a)), 0.5)
        C.line([(x + ca * L * off, y + sa * L * off), (wx + math.cos(a) * L * wl * 0.4, wy + math.sin(a) * L * wl * 0.4)], 0.5)
    C.line([(x + ca * L * 0.22, y + sa * L * 0.22), (x - ca * L * 0.15, y - sa * L * 0.15)], 1.5)
    C.line([(x - ca * L * 0.15, y - sa * L * 0.15), (x - ca * L * 0.85, y - sa * L * 0.85)], 1.0)
    C.dots([(x + ca * L * 0.3, y + sa * L * 0.3)], 1.5)


def _chedi(C, cx, by, H):
    """Bell-shaped chedi with a ringed spire, modelled by horizontal contour ruling."""
    def hw(f):
        if f < 0.1:
            return 0.36
        if f < 0.18:
            return 0.3
        if f < 0.24:
            return 0.25
        if f < 0.52:
            g = (f - 0.24) / 0.28
            return 0.05 + 0.18 * math.sqrt(max(0.0, 1 - g ** 2.2))
        if f < 0.57:
            return 0.07
        return 0.05 * (1 - (f - 0.57) / 0.43) + 0.004
    fs = [i / 36.0 for i in range(37)]
    out = [(cx - hw(f) * H, by - f * H) for f in fs] + [(cx + hw(f) * H, by - f * H) for f in fs[::-1]]
    C.shape(out, 1.0)
    y = by - 1.5
    while y > by - H * 0.98:
        f = (by - y) / H
        ww = hw(f) * H
        if f > 0.57:                                    # the spire, ring upon ring
            C.d("M%s %sh%s" % (_n(cx - ww - 1), _n(y), _n(2 * ww + 2)), 1.0 if int(y / 2) % 2 else 0.5)
        elif ww > 1.2:
            g = (f - 0.24) / 0.28
            bow = 2.0 * (1 - g) if 0 < g < 1 else 0.0       # contours sag round the bell
            C.d("M%s %sq%s %s %s 0" % (_n(cx - ww * 0.6), _n(y), _n(ww * 0.4), _n(bow), _n(ww * 0.8)), 0.5)
            C.d("M%s %sq%s %s %s 0" % (_n(cx + ww * 0.2), _n(y + bow * 0.5), _n(ww * 0.4), _n(bow * 0.4), _n(ww * 0.78)), 1.0)
        y -= 2.0
    for f in (0.1, 0.18, 0.24, 0.52, 0.57):                 # mouldings
        C.d("M%s %sh%s" % (_n(cx - hw(f - 0.01) * H - 1), _n(by - f * H), _n(2 * hw(f - 0.01) * H + 2)), 1.0)
    nw = 0.05 * H
    if nw > 2:                                              # niche
        d = "M%s %sV%sL%s %sL%s %sV%sz" % (_n(cx - nw), _n(by - 0.1 * H), _n(by - 0.19 * H), _n(cx), _n(by - 0.23 * H),
                                           _n(cx + nw), _n(by - 0.19 * H), _n(by - 0.1 * H))
        C.mask(d)
        C.d(d, 0.5)
        C.d(_hat((cx - nw, by - 0.23 * H, cx + nw, by - 0.1 * H), 1.5, 90), 1.0, C.clip(d))


def _palm(C, x, by, H, rng):
    top = (x + rng.uniform(-0.12, 0.12) * H, by - H)
    cm = (x + (top[0] - x) * 0.2, by - H * 0.6)
    C.d(_qd((x, by), cm, top), 1.5)
    C.d(_qd((x + 1.5, by), (cm[0] + 1.5, cm[1]), (top[0] + 1.5, top[1])), 0.5)
    for i in range(7):
        a = -PI * 0.5 + (i - 3) * 0.55 + rng.uniform(-0.1, 0.1)
        L = H * rng.uniform(0.3, 0.42)
        tip = (top[0] + L * math.cos(a) * 1.1, top[1] + L * math.sin(a) * 0.6 + L * 0.45)
        ctl = (top[0] + L * math.cos(a) * 0.7, top[1] + L * math.sin(a) * 0.9)
        C.d(_qd(top, ctl, tip), 1.0)
        C.d(_qd((top[0], top[1] + 1.5), (ctl[0], ctl[1] + 2), (tip[0] - 1, tip[1] + 1)), 0.5)


def _petal(C, bx, by, ang, L, wd, shade=1, w=1.0, curl=0.0):
    ax, ay = math.sin(ang), -math.cos(ang)
    px, py = math.cos(ang), math.sin(ang)
    tip = (bx + ax * L + px * curl * L, by + ay * L + py * curl * L)

    def ctl(u):
        return (bx + ax * 0.45 * L + px * wd * 1.7 * u, by + ay * 0.45 * L + py * wd * 1.7 * u)
    b = (bx, by)
    c0, c1 = ctl(-1), ctl(1)
    C.shape("M%s %sQ%s %s %s %sQ%s %s %s %sz" % (_n(bx), _n(by), _n(c0[0]), _n(c0[1]), _n(tip[0]), _n(tip[1]),
                                                 _n(c1[0]), _n(c1[1]), _n(bx), _n(by)), 0.5)
    if w > 0.5:                                   # the outline swells along the shadow side
        C.d(_qd(b, c1 if shade > 0 else c0, tip, 0.12, 0.86), 1.0)
    m = int(wd * 2 * 0.85 / 1.5)
    for k in range(m):
        u = -0.85 + 1.7 * (k + 0.5) / m
        dark = u * shade > 0
        t1 = 0.93 - 0.3 * abs(u) if dark else 0.3 + 0.12 * (k % 2)
        C.d(_qd(b, ctl(u), tip, 0.12, t1), 0.5)
    if L > 18:                                    # the turned edge on the shadow side
        C.d(_qd(b, ctl(0.95 * shade), tip, 0.25, 0.85), 0.5)
    return tip


def _bloom(C, bx, by, L, rng, open_=1.0):
    sh = 1
    wd = 0.2 * L
    w = 1.0 if L > 17 else 0.5
    for a in (1.45, -1.45):
        _petal(C, bx + math.copysign(0.1 * L, a), by, a * open_ + rng.uniform(-0.08, 0.08), L * 0.85, wd * 0.8, sh, w, 0.1 * (1 if a > 0 else -1))
    _petal(C, bx, by - 0.05 * L, rng.uniform(-0.05, 0.05), L * 1.02, wd, sh, w)
    for a in (0.45, -0.45, 0.92, -0.92):
        _petal(C, bx + a * 0.08 * L, by, a * open_ + rng.uniform(-0.05, 0.05), L * (1.0 - 0.06 * abs(a)), wd, sh, w)
    for a in (0.6, -0.6):
        _petal(C, bx + a * 0.2 * L, by + 0.06 * L, a * open_ * 0.9, L * 0.72, wd * 1.1, sh, w)
    _petal(C, bx, by + 0.1 * L, 0.02, L * 0.7, wd * 1.25, sh, w)


def _pad(C, cx, cy, rx, rng, paw=False):
    """Floating lotus pad: notched disc in perspective, ruled, with radial veins."""
    ry = rx * 0.3
    a0 = rng.uniform(0.3, 2.6)
    ctr = (cx + rx * 0.12 * math.cos(a0), cy + ry * 0.12 * math.sin(a0))
    C.d(_arc(cx + 0.5, cy + 2, rx, ry, 0.1, PI - 0.1), 1.5)
    C.d(_arc(cx + 1, cy + 4.5, rx * 0.94, ry, 0.5, PI - 0.5), 0.5)
    C.shape(_arc(cx, cy, rx, ry, a0 + 0.13, a0 + 2 * PI - 0.13) + "L%s %sz" % (_n(ctr[0]), _n(ctr[1])), 1.0)
    cid = C.clip(_arc(cx, cy, rx * 0.9, ry * 0.86, a0 + 0.16, a0 + 2 * PI - 0.16) + "L%s %sz" % (_n(ctr[0]), _n(ctr[1])))
    for k_ in range(1, int(ry * 0.84 / 1.5) + 1):               # contours ring the pad instead of ruling it
        f_ = k_ * 1.5 / ry
        C.d(_arc(cx, cy, rx * f_, ry * f_, a0 + 0.3, a0 + 2 * PI - 0.3), 1.0 if k_ % 3 == 0 else 0.5, cid)
    C.d(_hat((cx + rx * 0.2, cy - ry, cx + rx, cy + ry), 2.0, 60), 0.5, cid)
    nv = 11 if rx > 20 else 8
    for i in range(nv):
        a = a0 + 0.35 + (2 * PI - 0.7) * i / (nv - 1.0)
        C.line([ctr, (cx + rx * 0.86 * math.cos(a), cy + ry * 0.84 * math.sin(a))], 1.0)
    if paw:
        qx, qy = cx - rx * 0.4, cy + ry * 0.28
        C.mask(_E(qx, qy - 1, 5.5, 4.2))
        C.ink(_E(qx, qy, 2.0, 1.5))
        for ddx, ddy in ((-2.6, -1.6), (-1.0, -2.8), (1.0, -2.8), (2.6, -1.6)):
            C.ink(_E(qx + ddx, qy + ddy, 0.8, 0.7))


def _lotus(C, w, h, rng):
    """Moonlit temple pond in the manner of Lanna silver: no bare ground anywhere.  The sky is a
    field of flame-clouds in three scales under a cut night tint; a dark Himmapan wood (white-line
    leaves, a bird, a small dog) closes the far bank; elephant and temple are the two heroes."""
    wide = w / float(h)
    hz = _snap(h * (0.6 if wide > 3.5 else 0.52 if wide > 1.6 else 0.46))
    W = min(w * 0.25, (hz - 2) / 1.31)
    scx = w * (0.68 if wide > 1.2 else 0.64)
    apex = hz - 1.14 * W
    He = min(hz * 0.72, w * 0.21)
    ex0 = w * (0.07 if wide < 3 else 0.12)
    gy = hz + max(3.0, (h - hz) * 0.1)
    mx, my = min(scx - W * 0.95, max(ex0 + He * 1.5, w * 0.4)), hz * 0.27
    mr = max(5.0, min(hz * 0.12, 19.0))

    def night(x, y):
        d = math.sqrt(((x - mx) / (w * 0.5)) ** 2 + ((y - my) / (hz * 1.3)) ** 2)
        return _cl(0.06 + 0.52 * d ** 0.9)

    # ---- sky: matte ground, then cloud-curls small and middling, then the night cut over them
    C.d(_hat((0, 0, w, hz), 1.5), 1.0)
    cell = max(13.0, min(hz * 0.14, 19.0))
    rows = int(hz / (cell * 0.7)) + 2
    for r_ in range(rows):
        y = (r_ - 0.1) * cell * 0.7
        for c_ in range(int(w / cell) + 3):
            x = (c_ - 1 + (0.5 if r_ % 2 else 0.0)) * cell + rng.uniform(-0.14, 0.14) * cell
            yy = y + rng.uniform(-0.12, 0.12) * cell
            rr = cell * rng.uniform(0.42, 0.54)
            fl = 1 if rng.random() < 0.5 else -1
            ang = (-0.45 if r_ % 2 == 0 else PI + 0.45) + rng.uniform(-0.5, 0.5)
            if yy - rr > hz:
                continue
            if yy > apex + abs(x - scx) / (0.46 * W) * 0.8 * W + rr * 1.5 and abs(x - scx) < 0.4 * W:
                continue                                    # hidden behind the gables
            _curl(C, x, yy, rr, ang, fl)
    for i in range(int(w * hz / 5200.0) + 2):               # the middle scale, strewn over the small
        x, yy = rng.uniform(0, w), rng.uniform(0.04, 0.8) * hz
        if abs(x - scx) < 0.5 * W and yy > apex - cell:
            continue
        _curl(C, x, yy, cell * rng.uniform(0.85, 1.15), rng.choice((-0.5, PI + 0.5)) + rng.uniform(-0.4, 0.4), rng.choice((-1, 1)))
    ng = _grid(night, 0, 0, w, hz, 6.0)
    C.raw(_rule(_bend(_dfam((0, 0, w, hz), 32, 2.0, 3.0), 1.5, 40.0), ng, 2.0, rng, soft=True))
    C.raw(_rule(_bend(_dfam((0, 0, w, hz), -40, 3.0, 3.0), 1.5, 33.0), lambda x, y: _cl((ng(x, y) - 0.42) * 1.6), 3.0, rng, cap=0.5, soft=True))
    # moon in a ring of small flames
    for i in range(16):
        a = i * PI / 8
        C.mask(_pl([(mx + mr * 1.05 * math.cos(a - 0.14), my + mr * 1.05 * math.sin(a - 0.14)),
                    (mx + mr * (1.55 if i % 2 else 1.3) * math.cos(a + 0.1), my + mr * (1.55 if i % 2 else 1.3) * math.sin(a + 0.1)),
                    (mx + mr * 1.05 * math.cos(a + 0.14), my + mr * 1.05 * math.sin(a + 0.14))], True))
    C.mask(_E(mx, my, mr + 1.5, mr + 1.5))
    C.d(_E(mx, my, mr, mr), 1.0)
    C.d(_arc(mx, my, mr - 2, mr - 2, 0.2, 1.7), 0.5)
    C.d(_arc(mx, my, mr - 4, mr - 4, 0.5, 1.4), 0.5)
    # the great flame-scrolls
    hs = max(6.0, min(hz * 0.085, 15.0))
    heroes = [(ex0 + He * 0.45, hz * 0.1, 1), (min(w - hs * 1.5, scx + W * 0.95), hz * 0.2, -1)]
    if wide > 2.2:
        heroes.append(((mx + scx) / 2 + W * 0.1, hz * 0.14, 1))
    for hx_, hy_, fl in heroes:
        _hero(C, hx_, hy_ + hs * 0.6, hs, fl)

    # ---- the Himmapan wood along the far bank and up both sides: white-line leaves on the dark
    ph1 = rng.uniform(0, 6)

    def hb(x):
        e = math.exp(-(x / (0.12 * w)) ** 2) + math.exp(-((w - x) / (0.12 * w)) ** 2)
        return hz * (0.17 + 0.34 * e + 0.03 * math.sin(x / 19.0 + ph1))
    tl = [(0, hz + 1)]
    x = 0.0
    while x <= w + 4:
        tl.append((x, hz - hb(x)))
        x += 4.0
    tl.append((w, hz + 1))
    d = _pl(tl, True)
    C.mask(d)
    cid = C.clip(d)
    C.d(_hat((0, hz * 0.3, w, hz + 1), 1.5), 1.0, cid)
    C.d(_hat((0, hz * 0.3, w, hz + 1), 2.0, 60), 0.5, cid)
    C.d(_hat((0, hz * 0.3, w, hz + 1), 2.0, -60), 0.5, cid)
    Lf = max(8.0, min(hz * 0.11, 16.0))
    sprays = []
    x = -2.0
    while x < w + 4:
        top = hb(x)
        yy = hz - top + Lf * 0.3
        while yy < hz - 1:
            sprays.append((yy + rng.uniform(-2, 2), x + rng.uniform(-3, 3)))
            yy += Lf * 1.05
        x += Lf * 1.35
    bird = (w * 0.03 + Lf, hz - hb(w * 0.04) * 0.5)
    dogx = min(w - 14.0, scx + W * 0.84 + (w - scx - W * 0.84) * 0.45)
    dh = max(9.0, min(hz * 0.12, 17.0))
    k = 0
    for yy, x in sorted(sprays):
        if math.hypot(x - bird[0], yy - bird[1]) < Lf * 1.3:
            continue
        if abs(x - dogx) < dh * 0.6 and yy > hz - dh * 1.2:
            continue
        if k % 7 == 3:
            _rosette(C, x, yy - Lf * 0.3, max(2.5, Lf * 0.36))
        else:
            _spray(C, x, yy, Lf * rng.uniform(0.8, 1.15), rng, rng.choice((5, 6, 7)))
        k += 1
    _bird(C, bird[0], bird[1], Lf * 1.1, 1)
    _dog(C, dogx, hz + 1, dh, -1)
    _spray(C, dogx + dh * 0.55, hz + 1, Lf * 0.8, rng, 5)
    # chedi and temple
    chedis = []
    chx = scx - W * 1.2
    if chx - W * 0.26 > ex0 + He * 1.42:
        chedis.append((chx, W * 0.74))
    if wide > 2.4 and scx + W * 1.25 < w - W * 0.3:
        chedis.append((scx + W * 1.22, W * 0.6))
    for cx_, ch_ in chedis:
        _chedi(C, cx_, hz, ch_)
    _wat(C, scx, hz, W)

    # ---- water: a tone field cut in ripples; the moon's path is left as paper
    C.mask("M0 %sH%sV%sH0z" % (_n(hz), _n(w), _n(h + 1)))
    C.d("M0 %sH%s" % (_n(hz), _n(w)), 1.0)
    dw = float(h - hz)
    rdep = min(dw * 0.6, W * 0.9)

    def wt(x, y):
        dep = (y - hz) / dw
        e = abs(x - w * 0.5) / (w * 0.5)
        t = 0.3 + 0.22 * e * e + 0.2 * dep
        t += 0.45 * math.exp(-(y - hz) / (hb(x) * 0.55 + 1))                    # the wood, mirrored
        r = (y - hz) / rdep
        if r < 1 and abs(x - scx) < W * 0.82 * (1 - 0.3 * r):
            t += 0.38 * (1 - r) * (0.6 + 0.4 * math.sin(y * 1.9))               # the temple, mirrored
        for cx_, ch_ in chedis:
            r = (y - hz) / (ch_ * 0.8)
            if r < 1 and abs(x - cx_) < ch_ * 0.26 * (1 - 0.6 * r):
                t += 0.3 * (1 - r)
        k = ((x - ex0 - He * 0.6) / (He * 0.75)) ** 2 + ((y - gy) / max(4.0, He * 0.42)) ** 2
        if k < 1:
            t += 0.45 * (1 - k)                                                 # under the elephant
        g = math.exp(-((x - mx) / (mr * 0.9 + dw * 0.16 * dep)) ** 2)
        t -= 0.75 * g * (0.55 + 0.45 * math.sin(y * 2.3 + x * 0.21))            # moon glitter
        return _cl(t, 0.0, 0.97)
    wg = _grid(wt, 0, hz, w, h + 2, 2.5)
    C.raw(_rule(_wfam(0, w, hz + 1.5, h + 2, 2.0, 4.0, 0.9, 26.0, 0.5, 11.0), wg, 2.0, rng, soft=True))
    C.raw(_rule(_wfam(0, w, hz + 2.75, h + 2, 2.5, 4.0, 1.4, 41.0, 0.7, 17.0), lambda x, y: _cl((wg(x, y) - 0.5) * 2.0), 2.5, rng, soft=True))
    C.raw(_rule(_bend(_dfam((0, hz, w, h + 1), -24, 2.5, 3.0), 1.5, 30.0), lambda x, y: _cl((wg(x, y) - 0.78) * 3.5), 2.5, rng, soft=True))
    gl = []
    for i in range(int(dw * 0.5)):                                              # glints, white line
        yy = hz + 2 + dw * rng.random() ** 1.3
        xx = mx + rng.gauss(0, 1) * (mr * 1.2 + dw * 0.22 * (yy - hz) / dw)
        ln = rng.uniform(3, 9) * (0.6 + 1.5 * (yy - hz) / dw)
        gl.append("M%s %sq%s -1 %s 0" % (_n(xx - ln / 2), _n(yy), _n(ln / 2), _n(ln)))
    C.white("".join(gl), None, 1.0)

    # ---- the elephant, standing in the shallows
    for u in (0.14, 0.3, 0.77, 0.92):
        C.mask(_E(ex0 + u * He, gy, He * 0.17, max(1.5, He * 0.04)))
        C.d(_E(ex0 + u * He, gy, He * 0.17, max(1.5, He * 0.04)), 0.5)
        C.white(_arc(ex0 + u * He, gy + 1, He * 0.26, max(2.5, He * 0.07), 0.2, PI - 0.2), None, 1.0)
    _elephant(C, ex0, gy, He)

    # ---- foreground: pads, leaves, pods, buds and blooms, far to near; fish beneath, dragonflies above
    fg0 = hz + dw * 0.3
    L0 = max(13.0, min(h * 0.17, w * 0.1, 46.0))
    for i in range(int(w / 150) + 1):
        fl = 1 if rng.random() < 0.5 else -1
        _fish(C, w * rng.uniform(0.35, 0.95), hz + dw * rng.uniform(0.2, 0.5), max(9.0, L0 * rng.uniform(0.4, 0.6)), fl)
    things = []
    npad = max(5, int(w / 48.0))
    for i in range(npad):
        px_ = w * (i + 0.5) / npad + rng.uniform(-0.4, 0.4) * w / npad
        f = rng.random()
        py_ = fg0 + (h - fg0) * (0.02 + 0.94 * f)
        things.append((py_, "pad", px_, max(9.0, L0 * (0.5 + 0.75 * f)) * (1.2 if h < 140 else 1.0)))
    nfl = max(2, min(5, int(round(w / 125.0))))
    for i in range(nfl):
        fx = w * (0.06 + 0.88 * (i + 0.5) / nfl) + rng.uniform(-0.12, 0.12) * w / nfl
        f = rng.random()
        things.append((fg0 + (h - fg0) * (0.35 + 0.6 * f), "bloom", fx, L0 * (0.8 + 0.4 * f)))
        things.append((fg0 + (h - fg0) * (0.15 + 0.6 * rng.random()), "bud", fx + rng.choice((-1, 1)) * L0 * rng.uniform(1.2, 2.0), L0 * 0.7))
        kind = ("leaf", "pod")[i % 2]
        things.append((fg0 + (h - fg0) * (0.2 + 0.75 * rng.random()), kind, fx + rng.choice((-1, 1)) * L0 * rng.uniform(2.0, 3.0),
                       L0 * (0.75 if kind == "leaf" else 0.6)))
    # nothing may stand in front of the elephant's legs, nor crowd the temple door
    keep = []
    for yb, kind, x_, sz in things:
        if kind != "pad":
            reach = sz * (2.75 if kind == "bloom" else 2.3)
            if ex0 - sz < x_ < ex0 + He * 1.45 + sz and yb - reach < gy + 3:
                yb = gy + 4 + reach
                if yb > h - 3:
                    x_ = ex0 + He * 1.5 + sz + rng.uniform(0, 0.2) * w
                    yb = fg0 + (h - fg0) * rng.uniform(0.4, 0.95)
        elif ex0 - sz < x_ < ex0 + He * 1.4 + sz and yb - sz * 0.3 < gy + 4:
            yb = gy + 5 + sz * 0.3
        keep.append((min(yb, h + sz * 0.2), kind, x_, sz))
    things = keep
    pads = [t for t in things if t[1] == "pad"]
    pawpad = max(pads, key=lambda t: t[3] - abs(t[2] - w * 0.5) * 0.1 - abs(t[0] - (fg0 + (h - fg0) * 0.55)) * 0.2)
    for t in sorted(things):
        yb, kind, x_, sz = t
        if kind == "pad":
            _pad(C, x_, yb, sz, rng, paw=(t is pawpad))
            continue
        # concentric ripples where the stem leaves the water: white rings in the dark, black in the light
        C.white(_E(x_, yb, sz * 0.84, sz * 0.25) + _E(x_, yb, sz * 0.62, sz * 0.18) + _E(x_, yb, sz * 0.38, sz * 0.11), None, 1.0)
        C.d(_arc(x_, yb, sz * 0.84, sz * 0.25, 0.2, PI - 0.2), 0.5)
        C.d(_arc(x_, yb, sz * 0.62, sz * 0.18, 0.2, PI - 0.2), 1.0)
        C.d(_arc(x_, yb, sz * 0.38, sz * 0.11, 0.1, PI - 0.1), 1.0)
        if kind in ("bloom", "leaf"):                       # the flower's light lies broken on the water
            C.white("".join("M%s %sq%s 1.5 %s 0" % (_n(x_ - sz * ww_ + sz * 0.1 * (q_ % 2)), _n(yb + sz * 0.3 + 2.5 * q_), _n(sz * ww_), _n(sz * ww_ * 2))
                            for q_, ww_ in enumerate((0.42, 0.5, 0.4, 0.26, 0.14)) if yb + sz * 0.3 + 2.5 * q_ < h), None, 1.0)
        if kind == "bloom":
            sh = min(sz * rng.uniform(1.0, 1.5), yb - sz * 1.15 - 2)
            sh = max(sh, sz * 0.25)
            top = (x_ + rng.uniform(-0.3, 0.3) * sz, yb - sh)
            cm = (x_ + (top[0] - x_) * 0.1, yb - sh * 0.6)
            C.white(_qd((x_ + 0.5, yb), (cm[0] + 0.5, cm[1]), (top[0] + 0.5, top[1])), None, 4.0)
            C.d(_qd((x_, yb), cm, top), 1.5)
            C.d(_qd((x_ + 2, yb), (cm[0] + 2, cm[1]), (top[0] + 2, top[1])), 0.5)
            _bloom(C, top[0], top[1], sz, rng)
        elif kind == "leaf":
            _leaf(C, x_, yb, sz, rng)
        elif kind == "pod":
            _pod(C, x_, yb, sz, rng)
        else:
            sh = min(sz * rng.uniform(1.2, 1.9), yb - sz - 2)
            sh = max(sh, sz * 0.3)
            lean = rng.uniform(-0.25, 0.25)
            top = (x_ + lean * sz * 1.5, yb - sh)
            C.white(_qd((x_ + 0.5, yb), (x_ + 0.5, yb - sh * 0.7), (top[0] + 0.5, top[1])), None, 3.5)
            C.d(_qd((x_, yb), (x_, yb - sh * 0.7), top), 1.0)
            C.d(_qd((x_ + 1.5, yb), (x_ + 1.5, yb - sh * 0.7), (top[0] + 1.5, top[1])), 0.5)
            _petal(C, top[0], top[1], lean, sz, sz * 0.2, 1, 1.0)
            _petal(C, top[0], top[1], lean, sz * 0.8, sz * 0.1, 1, 0.5)
            C.line([(top[0] - sz * 0.12, top[1]), (top[0], top[1] + sz * 0.08), (top[0] + sz * 0.12, top[1])], 1.0)
    for i in range(int(w / 190) + 1):
        _dragonfly(C, w * rng.uniform(0.3, 0.95), hz + dw * rng.uniform(0.06, 0.3), max(8.0, L0 * 0.45), rng.uniform(-0.6, 0.6) + (PI if i % 2 else 0))


# ====================================================================== API
def scene(w, h, seed=0, variant="jazz", **kw):
    """SVG child markup filling a w x h box edge to edge.  variant: "jazz" or "lotus"."""
    w, h = float(w), float(h)
    v = "lotus" if str(variant).lower().startswith("l") else "jazz"
    rng = random.Random(int(seed) * 7919 + (17 if v == "jazz" else 43))
    C = _C("sm%s%d_%d_%d_" % (v[0], int(seed), int(w), int(h)))
    (_jazz if v == "jazz" else _lotus)(C, w, h, rng)
    C.flush()
    cid = C.pre + "0"
    return ('<clipPath id="%s"><path d="M0 0H%sV%sH0z"/></clipPath>'
            '<g clip-path="url(#%s)" fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round">%s</g>'
            % (cid, _n(w), _n(h), cid, "".join(C.o)))
