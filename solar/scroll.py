"""Fine-scroll engine: composes American/English fine scroll into any region.

Every call composes a fresh scroll system for its exact size and seed: spiral backbones that branch off a
running stem and tuck into tight curls, acanthus leaves that sprout from the backbones and are shaded with
fine cuts along their curves, and a ground cut away dark with a fine irregular stipple so the scroll stands
in relief. Fields are bounded by double inlay lines. Nothing here repeats a unit or tiles.

Public API (all sizes CSS px; strokes are 0.5 / 1 / 1.5 only; no transforms, text, masks or filters):

    cv = Canvas(w, h)                      # collects paths; cv.svg() -> complete <svg>
    strip(cv, run, seed, ...)              # running scroll along a Run (straight or curved centreline)
    band_rect(cv, x, y, w, h, ins, seed)   # scroll band round a rectangle, corners turned by volutes
    corner(cv, x, y, s, quad, seed)        # a corner volute group in an s x s square
    ring(cv, cx, cy, rx, ry, band, seed)   # oval ring of scroll (for a cartouche round a scene)
    fill_rect(cv, x, y, w, h, seed)        # a whole field of interlocking scroll rows (for the ground)
    fleuron / shell / rosette              # centre motifs
    inlay(cv, x, y, w, h)                  # double inlay line round a field

Pure standard library, deterministic for (args, seed).
"""
import math
import random
import zlib

TAU = math.pi * 2


# ---------------------------------------------------------------- output

def _f(x):
    s = "%.1f" % x
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return "0" if s in ("", "-", "-0") else s


def _pts(pts):
    """Absolute first point, then relative lineto deltas computed on the rounded grid (no drift)."""
    q = [(round(x * 10), round(y * 10)) for x, y in pts]
    out = [_j(q[0][0] / 10, q[0][1] / 10)]
    rel = []
    px, py = q[0]
    for x, y in q[1:]:
        if x == px and y == py:
            continue
        rel.append(_j((x - px) / 10, (y - py) / 10))
        px, py = x, y
    if rel:
        out.append("l" + _cat(rel))
    return "".join(out)


def _j(a, b):
    a, b = _f(a), _f(b)
    return a + ("" if b.startswith("-") else " ") + b


def _cat(items):
    o = items[0]
    for it in items[1:]:
        o += it if it.startswith("-") or (it.startswith(".") and "." in o.rsplit(" ", 1)[-1].rsplit("-", 1)[-1]) else " " + it
    return o


STYLE = {
    "K": 'fill="#000"',
    "W": 'fill="#fff"',
    "WO": 'fill="#fff" stroke="#000" stroke-width=".5" stroke-linejoin="round"',
    "G": 'fill="#fff" fill-rule="evenodd"',
    "C05": 'fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round"',
    "C1": 'fill="none" stroke="#000" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"',
    "C15": 'fill="none" stroke="#000" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"',
    "S1": 'fill="none" stroke="#fff" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"',
    "S15": 'fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"',
    "D": 'fill="none" stroke="#fff" stroke-width=".5" stroke-linecap="round"',
    "R05": 'fill="none" stroke="#000" stroke-width=".5" shape-rendering="crispEdges"',
    "R1": 'fill="none" stroke="#000" stroke-width="1" shape-rendering="crispEdges"',
}


def _css(attrs):
    out = []
    for a in attrs.split('" '):
        k, v = a.split('="')
        out.append("%s:%s" % (k, v.strip('"')))
    return ";".join(out)


CSS = {k: _css(v) for k, v in STYLE.items()}


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.ops = []
        self.slot = None  # (x, y, w, h) of the white text slot, recorded on the <svg> as data-slot
        self.clip = None  # optional path d: everything is clipped to it (keeps outside transparent)
        self.top = []     # ops drawn last, over everything (slot white, inlay rules)

    def add(self, key, d):
        if not d:
            return
        if self.ops and self.ops[-1][0] == key:
            self.ops[-1][1].append(d)
        else:
            self.ops.append((key, [d]))

    def over(self, key, d):
        """Add to the top layer, drawn after everything else."""
        if self.top and self.top[-1][0] == key:
            self.top[-1][1].append(d)
        else:
            self.top.append((key, [d]))

    def poly(self, key, pts, close=True):
        if len(pts) > 1:
            self.add(key, "M" + _pts(pts) + ("Z" if close else ""))

    def line(self, key, pts):
        self.poly(key, pts, close=False)

    def circle(self, key, cx, cy, r):
        self.add(key, "M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 %s 0" % (
            _f(cx - r), _f(cy), _f(r), _f(r), _f(2 * r), _f(r), _f(r), _f(-2 * r)))

    def dot(self, x, y):
        if self.ops and self.ops[-1][0] == "D":
            self.ops[-1][1].append((x, y))
        else:
            self.ops.append(("D", [(x, y)]))

    @staticmethod
    def _dots(ds):
        q = sorted((round(y * 2) / 2 // 3, round(x * 10), round(y * 10)) for x, y in ds)
        out = []
        px = py = None
        for _, x, y in q:
            if px is None:
                out.append("M" + _j(x / 10, y / 10) + "h0")
            else:
                out.append("m" + _j((x - px) / 10, (y - py) / 10) + "h0")
            px, py = x, y
        return "".join(out)

    def body(self):
        ops = self.ops + self.top
        used = sorted({k for k, _ in ops})
        css = "".join(".%s{%s}" % (k.lower(), CSS[k]) for k in used)
        body = "".join('<path class="%s" d="%s"/>' % (k.lower(), self._dots(ds) if k == "D" else "".join(ds)) for k, ds in ops)
        if self.clip:
            cid = "c%x" % (zlib.crc32(self.clip.encode()) & 0xffffff)
            body = '<clipPath id="%s"><path d="%s"/></clipPath><g clip-path="url(#%s)">%s</g>' % (cid, self.clip, cid, body)
        return "<style>%s</style>" % css + body

    def svg(self):
        slot = ' data-slot="%s"' % " ".join(_f(v) for v in self.slot) if self.slot else ""
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s"%s>%s</svg>'
                % (_f(self.w), _f(self.h), _f(self.w), _f(self.h), slot, self.body()))


def rng_for(*parts):
    return random.Random(zlib.crc32(repr(parts).encode()))


# ---------------------------------------------------------------- geometry

def _norm(x, y):
    d = math.hypot(x, y) or 1.0
    return x / d, y / d


def _normals(pts):
    n = len(pts)
    out = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tx, ty = _norm(b[0] - a[0], b[1] - a[1])
        out.append((-ty, tx))
    return out


def _arclen(pts):
    s = [0.0]
    for i in range(1, len(pts)):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    return s


def _at(pts, s, t):
    """Point and unit tangent at arclength fraction t of polyline pts with cumulative lengths s."""
    L = s[-1] * min(max(t, 0.0), 1.0)
    for i in range(1, len(pts)):
        if s[i] >= L:
            seg = s[i] - s[i - 1] or 1.0
            k = (L - s[i - 1]) / seg
            x = pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k
            y = pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k
            return (x, y), _norm(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
    return pts[-1], _norm(pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])


def _resample(pts, step):
    s = _arclen(pts)
    n = max(2, int(s[-1] / step) + 1)
    return [_at(pts, s, i / (n - 1))[0] for i in range(n)]


def _bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t * t
        d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _spiral(cx, cy, r0, a0, turns, decay, dirn, n=None):
    """Log spiral from radius r0 at angle a0, winding `turns` in direction dirn (+1 ccw on screen = -y up)."""
    n = n or max(12, int(28 * turns * max(1.0, r0 / 4)))
    out = []
    for i in range(n + 1):
        t = i / n
        th = a0 + dirn * TAU * turns * t
        r = r0 * (decay ** t)
        out.append((cx + r * math.cos(th), cy - r * math.sin(th)))
    return out


def _ribbon(pts, hw):
    """Polygon of a centreline with half-widths hw (list or callable of t)."""
    nm = _normals(pts)
    n = len(pts)
    L, R = [], []
    for i, (p, q) in enumerate(zip(pts, nm)):
        h = hw(i / (n - 1)) if callable(hw) else hw[i]
        L.append((p[0] + q[0] * h, p[1] + q[1] * h))
        R.append((p[0] - q[0] * h, p[1] - q[1] * h))
    return L + R[::-1], L, R


# ---------------------------------------------------------------- the elements

def backbone(cv, pts, w0=1.6, w1=0.6, key="W"):
    """A scroll backbone: bright tapering band (no outline: it lies on the dark ground)."""
    pts = _resample(pts, 1.3)
    if key == "W":
        # drawn as white strokes: 1.5 px for the thick run, then 1 px into the curl
        n = len(pts)
        if w0 >= 1.25 and w1 < 1.25:
            k = max(2, int(n * min(1.0, (w0 - 1.25) / max(0.01, w0 - w1) + 0.15)))
            cv.line("S15", pts[:k + 1])
            cv.line("S1", pts[k:])
        else:
            cv.line("S15" if w0 >= 1.25 else "S1", pts)
        return
    poly, L, R = _ribbon(pts, lambda t: (w0 + (w1 - w0) * t) / 2)
    cv.poly(key, poly)


def finger(cv, spine, width, shade=1, cuts=2, step=0.9, blunt=0.0, teeth=None, cover=0.4):
    """An acanthus blade along `spine`: the edge on the `shade` side (+1 left of travel, -1 right) is the
    smooth shadow edge, the other edge is serrated into small forward-pointing teeth.  Fine cuts run
    along the blade at 1 px pitch from the shadow edge, the outer ones running out sooner, so tone grades
    from dark at the shadow edge to a bright toothed edge and tip.  A notch cut runs in from each tooth."""
    spine = _resample(spine, max(step, min(1.6, width * 0.3)))
    n = len(spine)
    if n < 3:
        return
    nm = _normals(spine)
    hw = width / 2
    Ltot = _arclen(spine)[-1]
    if teeth is None:
        teeth = max(0, int(Ltot / 3.6)) if width >= 2.2 else 0
    sg = 1 if shade > 0 else -1

    def env(t):
        if t < 0.3:
            e = math.sin(math.pi / 2 * t / 0.3) ** 0.65
        else:
            e = math.cos(math.pi / 2 * (t - 0.3) / 0.7) ** (0.85 - 0.45 * blunt)
        return max(0.0, e)

    def saw(t):
        if not teeth or t < 0.1 or t > 0.92:
            return 1.0
        q = (t * teeth) % 1.0
        return 0.6 + 0.4 * (q ** 1.3)

    S, T = [], []  # shadow edge, toothed edge
    for i, (p, q) in enumerate(zip(spine, nm)):
        t = i / (n - 1)
        h = hw * env(t)
        S.append((p[0] + sg * q[0] * h, p[1] + sg * q[1] * h))
        h2 = h * saw(t)
        T.append((p[0] - sg * q[0] * h2, p[1] - sg * q[1] * h2))
    cv.poly("WO", S + T[::-1][1:-1])
    # cuts from the shadow edge inward at 1 px pitch
    if cuts:
        c = 1
        while True:
            d = c * 1.5 - 0.5
            if d > width * cover:
                break
            stop = (0.92 - 0.55 * d / max(width, 1.0)) * (1.0 if cuts > 1 else 0.8)
            seg = []
            for i in range(n):
                t = i / (n - 1)
                full = 2 * hw * env(t) * (0.5 + 0.5 * saw(t))
                if 0.04 < t < stop and full - d > 0.8:
                    h = hw * env(t)
                    off = h - d  # signed offset from spine toward shadow side
                    seg.append((spine[i][0] + sg * nm[i][0] * off, spine[i][1] + sg * nm[i][1] * off))
                elif seg:
                    break
            if len(seg) > 2:
                cv.line("C05", seg)
            c += 1
    # notch cuts from the toothed edge
    if teeth:
        prevq = 0
        for i in range(1, n):
            t = i / (n - 1)
            q = (t * teeth) % 1.0
            if q < prevq and 0.12 < t < 0.88:
                e = T[i]
                m = spine[min(n - 1, i + 1)]
                cv.line("C05", [e, (e[0] + (m[0] - e[0]) * 0.3, e[1] + (m[1] - e[1]) * 0.3)])
            prevq = q


def leaf(cv, spine, width, lobes=3, shade=1, rng=None, cuts=1.0, step=0.9, side=None):
    """An acanthus leaf along `spine`: a main lobe plus `lobes` side fingers springing from it and sweeping
    the same way, each overlapping the one before, each pointed and shaded along its length.  `side` puts
    the side fingers to the left (+1) or right (-1) of travel; default both sides alternately."""
    rng = rng or random.Random(0)
    sp = _resample(spine, step)
    n = len(sp)
    if n < 4:
        return
    s = _arclen(sp)
    Ltot = s[-1]
    finger(cv, sp, width, shade=shade, cuts=2 if width > 3 else 1, step=step)
    nm = _normals(sp)
    for j in range(lobes):
        t = 0.22 + 0.5 * (j + rng.uniform(-0.1, 0.1)) / max(1, lobes)
        sd = side if side else (1 if j % 2 == 0 else -1)
        (bx, by), (tx, ty) = _at(sp, s, t)
        nx, ny = -ty, tx
        ln = Ltot * (0.55 - 0.3 * j / max(1, lobes)) * rng.uniform(0.85, 1.1)
        sp_ang = rng.uniform(0.45, 0.75)
        # the finger leaves the main lobe splayed out, then bends back to run with the leaf
        pts = []
        for q in range(10):
            u = q / 9
            a = sp_ang * (1 - u) ** 1.3
            dx = tx * math.cos(a) + sd * nx * math.sin(a)
            dy = ty * math.cos(a) + sd * ny * math.sin(a)
            if pts:
                px, py = pts[-1]
            else:
                px, py = bx + sd * nx * width * 0.15, by + sd * ny * width * 0.15
                pts.append((px, py))
                continue
            pts.append((px + dx * ln / 9, py + dy * ln / 9))
        finger(cv, pts, width * rng.uniform(0.5, 0.65), shade=-sd if shade == 0 else shade, cuts=1, step=step)


def bud(cv, x, y, r):
    if r <= 0.8:
        cv.line("S15", [(x, y), (x + 0.01, y)])
        return
    cv.circle("W", x, y, r)
    cv.circle("C05", x, y, r)
    if r > 1.1:
        cv.circle("K", x + r * 0.25, y + r * 0.25, r * 0.38)


class Occ:
    """Coarse occupancy raster (cell px) of a lane in local coords, filled by scanline."""

    def __init__(self, x0, y0, x1, y1, cell=0.75):
        self.x0, self.y0, self.c = x0, y0, cell
        self.nx = int((x1 - x0) / cell) + 1
        self.ny = int((y1 - y0) / cell) + 1
        self.g = [bytearray(self.nx) for _ in range(self.ny)]

    def fill(self, pts, grow=0.0):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        c = self.c
        j0 = max(0, int((min(ys) - grow - self.y0) / c))
        j1 = min(self.ny - 1, int((max(ys) + grow - self.y0) / c) + 1)
        n = len(pts)
        g = int(grow / c + 0.5)
        for j in range(j0, j1 + 1):
            y = self.y0 + (j + 0.5) * c
            xs = []
            for i in range(n):
                (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
                if (ya > y) != (yb > y):
                    xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                i0 = max(0, int((a - self.x0) / c) - g)
                i1 = min(self.nx - 1, int((b - self.x0) / c) + g)
                row = self.g[j]
                for i in range(i0, i1 + 1):
                    row[i] = 1

    def free(self, x, y, r):
        c = self.c
        i0, i1 = int((x - r - self.x0) / c), int((x + r - self.x0) / c)
        j0, j1 = int((y - r - self.y0) / c), int((y + r - self.y0) / c)
        if i0 < 0 or j0 < 0 or i1 >= self.nx or j1 >= self.ny:
            return False
        for j in range(j0, j1 + 1):
            if any(self.g[j][i0:i1 + 1]):
                return False
        return True


class Mapped:
    """A canvas proxy that maps every point through f(x, y) -> (X, Y) (a rigid motion or a run's bend)."""

    def __init__(self, cv, f, occ=None):
        self.cv, self.f, self.occ = cv, f, occ

    def poly(self, key, pts, close=True):
        if self.occ is not None and key in ("WO", "W") and close:
            self.occ.fill(pts)
        elif self.occ is not None and key in ("S1", "S15") and len(pts) > 1:
            self.occ.fill(_ribbon(pts, [0.75 if key == "S15" else 0.5] * len(pts))[0])
        self.cv.poly(key, [self.f(x, y) for x, y in pts], close)

    def line(self, key, pts):
        self.poly(key, pts, close=False)

    def circle(self, key, x, y, r):
        if self.occ is not None and key == "W":
            self.occ.fill([(x + r * math.cos(a / 8 * TAU), y + r * math.sin(a / 8 * TAU)) for a in range(8)])
        X, Y = self.f(x, y)
        self.cv.circle(key, X, Y, r)

    def dot(self, x, y):
        self.cv.dot(*self.f(x, y))

    def add(self, key, d):
        self.cv.add(key, d)


class Scroll:
    """One spiral scroll in a y-down frame: centre, outer radius, winding dirn (+1 clockwise on screen),
    start angle a0 (screen angle, radians, y down) where its stem joins."""

    def __init__(self, cx, cy, r, dirn, a0, turns=1.5, decay=0.18):
        self.cx, self.cy, self.r, self.dirn, self.a0 = cx, cy, r, dirn, a0
        self.turns, self.decay = turns, decay

    def point(self, f, rscale=1.0):
        th = self.a0 + self.dirn * TAU * f
        r = self.rad(f) * rscale
        return (self.cx + r * math.cos(th), self.cy + r * math.sin(th))

    def rad(self, f):
        """Radius at turn-fraction f: nearly round through the first turn, tightening into the eye."""
        u = min(max(f / self.turns, 0.0), 1.0)
        return self.r * (1.0 - (1.0 - self.decay) * u ** 1.5)

    def tangent_at(self, f):
        a, b = self.point(f - 0.01), self.point(f + 0.01)
        return _norm(b[0] - a[0], b[1] - a[1])

    def start(self):
        return self.point(0)

    def tangent(self):
        return self.tangent_at(0)

    def arc(self, f0, f1, rscale=1.0, n=None):
        n = n or max(8, int(abs(f1 - f0) * 5.0 * max(self.r, 2.0)))
        return [self.point(f0 + (f1 - f0) * i / n, rscale) for i in range(n + 1)]

    def pts(self):
        return self.arc(0, self.turns)


def wrap_leaf(cv, sc, R, f0, f1, rng, lobes=None, cuts=True):
    """The scroll's big acanthus leaf, wrapped round the outside of its backbone from turn-fraction f0 to
    f1: inner edge riding the backbone, outer edge scalloped into pointed lobes out to radius R, the tip
    curling off the circle.  Shaded with concentric bulino cuts that follow the curl, darkest next to the
    backbone and running out before the lit outer edge; each lobe divided by a notch cut."""
    lobes = lobes or max(2, int((f1 - f0) * 6.5))
    n = max(16, int((f1 - f0) * 90 * max(1.0, R / 6)))
    ph = rng.uniform(0.0, 0.2)
    inner, outer = [], []
    rad = []
    for i in range(n + 1):
        t = i / n
        f = f0 + (f1 - f0) * t
        th = sc.a0 + sc.dirn * TAU * f
        rb = sc.r * (sc.decay ** (f / sc.turns)) + 0.55
        q = (t * lobes + ph) % 1.0
        lob = 0.5 + 0.5 * (math.sin(math.pi / 2 * min(1.0, q / 0.85)) ** 1.4 if q < 0.85 else 1 - (q - 0.85) / 0.15 * 0.85)
        grow = min(1.0, t / 0.18) ** 0.7
        tip = 1.0 if t < 0.8 else max(0.0, 1 - (t - 0.8) / 0.2) ** 0.6
        ro = rb + (R - rb) * grow * tip * lob
        if t > 0.85:  # tip curls outward beyond the backbone
            ro += (R - rb) * 0.25 * (t - 0.85) / 0.15
        inner.append((sc.cx + rb * math.cos(th), sc.cy + rb * math.sin(th)))
        tho = th - sc.dirn * 0.45 * (ro - rb) / max(R, 1.0) * (0.3 + q)
        outer.append((sc.cx + ro * math.cos(tho), sc.cy + ro * math.sin(tho)))
        rad.append((th, rb, ro, q))
    cv.poly("WO", inner + outer[::-1])
    if not cuts:
        return
    # concentric cuts (pitch 1.0 from the backbone), each running out earlier: dark in, bright out
    k = 1
    while True:
        d = k * 1.05
        seg = []
        stop = 0.9 - 0.22 * k + rng.uniform(-0.05, 0.05)
        if stop < 0.2:
            break
        for i, (th, rb, ro, q) in enumerate(rad):
            t = i / n
            if ro - rb > d + 0.7 and 0.04 < t < stop:
                seg.append((sc.cx + (rb + d) * math.cos(th), sc.cy + (rb + d) * math.sin(th)))
            elif seg:
                if len(seg) > 2:
                    cv.line("C05", seg)
                seg = []
        if len(seg) > 2:
            cv.line("C05", seg)
        k += 1
        if k > 4:
            break
    # notch cuts between lobes
    for i, (th, rb, ro, q) in enumerate(rad):
        if 0 < i < n and rad[i - 1][3] > q and 0.1 < i / n < 0.9:
            a = (sc.cx + ro * math.cos(th), sc.cy + ro * math.sin(th))
            m = rb + (ro - rb) * 0.35
            cv.line("C05", [a, (sc.cx + m * math.cos(th + sc.dirn * 0.12), sc.cy + m * math.sin(th + sc.dirn * 0.12))])


def curl_fill(cv, sc, wmax=1.5):
    """The leaf rolled up inside the scroll: fills the gap between the outer turn and the next one in,
    tapering at both ends, with one cut following the curl near its outer (shadow) edge."""
    fa, fb = 0.12, sc.turns - 1.0 - 0.05
    if fb <= fa + 0.1:
        return
    n = max(8, int((fb - fa) * 4.5 * sc.r))
    outer, inner, cut = [], [], []
    for i in range(n + 1):
        t = i / n
        f = fa + (fb - fa) * t
        th = sc.a0 + sc.dirn * TAU * f
        ro = sc.rad(f) - wmax * 0.5 - 0.35
        ri = sc.rad(f + 1) + 0.75
        mid = (ro + ri) / 2
        k = min(1.0, t / 0.2, (1 - t) / 0.25) ** 0.6
        a, b = mid + (ro - mid) * k, mid + (ri - mid) * k
        outer.append((sc.cx + a * math.cos(th), sc.cy + a * math.sin(th)))
        inner.append((sc.cx + b * math.cos(th), sc.cy + b * math.sin(th)))
        if a - b > 2.2 and 0.1 < t < 0.8:
            c = a - 1.0
            cut.append((sc.cx + c * math.cos(th), sc.cy + c * math.sin(th)))
    cv.poly("WO", outer + inner[::-1])
    if len(cut) > 2:
        cv.line("C05", cut)


def inner_leaf(cv, sc, wmax, rng, fs=0.03, fe=None):
    """The scroll's acanthus leaf: springs from outside the backbone just before the fork, turns over
    across it and rolls into the scroll, filling the gap between the outer turn and the next one in, its
    inner edge cut into forward-pointing lobes, its tip curling short of the eye.  Shaded by cuts that
    follow the curl along the backbone side (into the shadow), so the lit inner lobes stay bright."""
    fe = fe if fe is not None else min(sc.turns - 0.55, rng.uniform(0.85, 1.0))
    n = max(10, int((fe - fs) * 4.5 * sc.r))
    lob = max(2, int((fe - fs) * rng.uniform(3.2, 4.2)))
    ph = rng.uniform(0, 0.3)
    outer, inner, rows = [], [], []
    for i in range(n + 1):
        t = i / n
        f = fs + (fe - fs) * t
        th = sc.a0 + sc.dirn * TAU * f
        rad = sc.rad(max(f, 0.0))
        nxt = sc.rad(max(f, 0.0) + 1)
        if f < 0.04:  # outside, turning over the backbone
            k = (0.04 - f) / (0.04 - fs)
            ro = rad + wmax * 0.5 + sc.r * 0.38 * math.sin(math.pi * min(1.0, k * 1.1)) ** 0.8
        else:
            ro = rad - wmax * 0.5 - 0.25
        ri0 = nxt + 0.7
        env = min(1.0, (1 - t) / 0.3) ** 0.7 if t > 0.7 else 1.0
        q = (t * lob + ph) % 1.0
        saw = 0.7 + 0.3 * q ** 1.2 if 0.1 < t < 0.95 else 1.0
        env *= min(1.0, t / 0.12) ** 0.6
        ri = ro - (ro - ri0) * env * saw
        if f < 0.04:
            ri = max(ri0, rad - sc.r * 0.25 * (1 - (0.04 - f) / (0.04 - fs)))
        outer.append((sc.cx + ro * math.cos(th), sc.cy + ro * math.sin(th)))
        inner.append((sc.cx + ri * math.cos(th), sc.cy + ri * math.sin(th)))
        rows.append((th, ro, ri, q, t))
    cv.poly("WO", outer + inner[::-1])
    # cuts following the curl from the backbone side
    for c in (1, 2):
        d = c * 1.5 - 0.5
        seg = []
        stop = 0.8 - 0.25 * c
        for th, ro, ri, q, t in rows:
            if 0.12 < t < stop and ro - ri > d + 1.2:
                rr = ro - d
                seg.append((sc.cx + rr * math.cos(th), sc.cy + rr * math.sin(th)))
            elif seg:
                break
        if len(seg) > 2:
            cv.line("C05", seg)
    # lobe notches
    for i in range(1, len(rows)):
        th, ro, ri, q, t = rows[i]
        if q < rows[i - 1][3] and 0.12 < t < 0.9 and ro - ri > 1.6:
            m = ri + (ro - ri) * 0.45
            cv.line("C05", [(sc.cx + ri * math.cos(th), sc.cy + ri * math.sin(th)),
                            (sc.cx + m * math.cos(th - sc.dirn * 0.15), sc.cy + m * math.sin(th - sc.dirn * 0.15))])


def draw_scroll(cv, sc, rng, wmax=1.5, R=None):
    """A scroll: backbone, the acanthus leaf rolled into it, the bud at its eye."""
    backbone(cv, sc.pts(), w0=wmax, w1=0.5)
    if sc.r >= 2.4:
        inner_leaf(cv, sc, wmax, rng)
    e = sc.point(sc.turns)
    bud(cv, e[0], e[1], max(0.6, sc.r * 0.12))


class Run:
    """A band region: a centreline polyline (traversed clockwise on screen for frames) and a width H.
    p(u, v): u along the centreline, v across it, +v toward the outer side (left of travel)."""

    def __init__(self, pts, H):
        self.c = _resample(pts, 0.5)
        self.s = _arclen(self.c)
        self.L = self.s[-1]
        self.H = H
        n = len(self.c)
        self.nm = []
        for i in range(n):
            a = self.c[max(i - 1, 0)]
            b = self.c[min(i + 1, n - 1)]
            tx, ty = _norm(b[0] - a[0], b[1] - a[1])
            self.nm.append((ty, -tx))

    def p(self, u, v):
        t = min(max(u / self.L if self.L else 0.0, 0.0), 1.0)
        i = t * (len(self.c) - 1)
        i0 = int(i)
        i1 = min(i0 + 1, len(self.c) - 1)
        k = i - i0
        x = self.c[i0][0] + (self.c[i1][0] - self.c[i0][0]) * k
        y = self.c[i0][1] + (self.c[i1][1] - self.c[i0][1]) * k
        nx = self.nm[i0][0] + (self.nm[i1][0] - self.nm[i0][0]) * k
        ny = self.nm[i0][1] + (self.nm[i1][1] - self.nm[i0][1]) * k
        if u < 0 or u > self.L:  # straight continuation past the ends
            e = u if u < 0 else u - self.L
            x, y = x - ny * e, y + nx * e
        return (x + nx * v, y + ny * v)


def _ground_in_run(cv, run, u0, u1, v0, v1, rng, density=1.1):
    """Cut-away ground in a run: black, with a fine irregular stipple of 1-device-px pricks."""
    m = Mapped(cv, lambda x, y: run.p(x, y))
    m.poly("K", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    n = int((u1 - u0) * (v1 - v0) * density)
    for _ in range(n):
        m.dot(rng.uniform(u0 + 0.3, u1 - 0.3), rng.uniform(v0 + 0.4, v1 - 0.4))


# ---------------------------------------------------------------- lanes (a band of scroll in local coords)

def lane(cv, L, H, rng, start_side=1, wmax=None, rmin=0.44, rmax=0.56, lead=None):
    """Compose fine scroll in the lane x in [0, L], y in [-H/2, H/2] (y down) of canvas-like `cv`.

    A running stem dips alternately to each side; at each turn a scroll forks off and tucks into a tight
    curl; big acanthus leaves sweep back from each fork over the trough; small flame leaves and secondary
    curls fill what room is left.  Radii, spacing, winding and leaf shapes vary with the seed, so no two
    stretches are alike.
    """
    if L < H * 0.8:
        return []
    wmax = wmax or (1.5 if H >= 12 else 1.0)
    plan = []
    side = start_side
    x = 0.0
    while True:
        r = H * (rmin + (rmax - rmin) * rng.random() ** 0.8)
        if plan and rng.random() < 0.3:
            r = H * rng.uniform(rmin * 0.6, rmin * 0.85)  # a small scroll between big ones
        m = max(0.5, H * 0.05)
        cy = side * (H / 2 - r - m) * -1  # side +1 -> scroll sits toward -y (outer), its fork below it
        if not plan:
            x = r + H * rng.uniform(0.10, 0.25)
        else:
            px, py, pr, _ = plan[-1]
            need = (r + pr) * rng.uniform(0.95, 1.1)
            dy = abs(cy - py)
            x = px + math.sqrt(max(need * need - dy * dy, (0.95 * (r + pr)) ** 2))
        if x + r > L - H * 0.05:
            break
        plan.append((x, cy, r, side))
        side = -side
    if not plan:
        return []
    slack = L - (plan[-1][0] + plan[-1][2]) - H * 0.05
    if len(plan) > 1 and slack > 0:
        plan = [(x + slack * (0.1 + 0.85 * i / (len(plan) - 1)), cy, r, sd) for i, (x, cy, r, sd) in enumerate(plan)]
    scrolls = []
    for x, cy, r, side in plan:
        # side +1 (outer, -y): starts at its bottom (angle +90deg, y down) heading +x, winds counter-clockwise
        rb = r * rng.uniform(0.86, 0.94)
        if side > 0:
            sc = Scroll(x, cy, rb, -1, math.pi / 2, rng.uniform(1.55, 1.8), rng.uniform(0.16, 0.22))
        else:
            sc = Scroll(x, cy, rb, 1, -math.pi / 2, rng.uniform(1.55, 1.8), rng.uniform(0.16, 0.22))
        sc.R = r
        scrolls.append(sc)
    # the running stem
    stems = []
    if lead is not None:
        stems.append((lead[0], lead[1], scrolls[0]))
    else:
        s0 = scrolls[0]
        p3 = s0.start()
        stems.append(((0.0, p3[1] * 0.3), (1.0, 0.0), s0))
    for a, b in zip(scrolls, scrolls[1:]):
        stems.append((a.start(), a.tangent(), b))
    stem_pts = []
    for p0, t0, b in stems:
        p3, t3 = b.start(), b.tangent()
        d = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
        k = d * 0.45
        pts = _bez(p0, (p0[0] + t0[0] * k, p0[1] + t0[1] * k), (p3[0] - t3[0] * k, p3[1] - t3[1] * k), p3, 20)
        stem_pts.append(pts)
    # trailing stem out to the end of the lane, ending in a small curl
    last = scrolls[-1]
    hb = H / 2 - 0.6
    # the trough behind each fork: a sweeping leaf, or a secondary scroll branching off with its own leaf
    secondary = []
    for i, sc in enumerate(scrolls):
        if sc.R < 2.2:
            continue
        sx, sy = sc.start()
        up = -1 if sc.cy > sy else 1  # direction from the fork away from its own scroll
        room = H / 2 - up * sy - 0.6  # free depth toward the far edge
        prevx = scrolls[i - 1].cx + scrolls[i - 1].r if i else 0.0
        span = sx - prevx
        if room > H * 0.3 and span > H * 0.35 and rng.random() < 0.55 and H >= 8:
            r2 = min(room * 0.48, span * 0.42) * rng.uniform(0.85, 1.0)
            cx2 = sx - span * rng.uniform(0.35, 0.5)
            cy2 = sy + up * (room - r2 - 0.2)
            # branch: leaves the fork backward and curls the opposite way to its parent
            d2 = -sc.dirn
            a2 = math.atan2(sy - cy2, sx - cx2)
            sc2 = Scroll(cx2, cy2, r2, d2, a2, rng.uniform(1.2, 1.5), rng.uniform(0.15, 0.25))
            secondary.append(sc2)
            leaf(cv, _bez((sx, sy), (sx - span * 0.3, sy + up * room * 0.1), (cx2 + r2 * 1.4, cy2 - up * r2 * 0.6),
                          (cx2 + r2 * 0.2, cy2 - up * r2 * 0.95), 12),
                 width=r2 * 0.9, lobes=2, shade=up, rng=rng, side=-up)
            continue
        ln = sc.R * rng.uniform(1.35, 1.8)
        bend = rng.uniform(0.9, 1.5)
        pts = []
        for j in range(15):
            t = j / 14
            ang = math.pi + up * (0.35 + bend * t * t)
            pts.append((sx + math.cos(ang) * ln * t, sy + math.sin(ang) * ln * t * 0.85))
        dev = max(abs(py - sy) for _, py in pts) or 1.0
        f = min(1.0, max(0.3, room - sc.R * 0.3) / dev)
        pts = [(px, sy + (py - sy) * f) for px, py in pts]
        leaf(cv, pts, width=sc.R * rng.uniform(1.1, 1.3), lobes=2, shade=-up, rng=rng, side=up)
    for pts in stem_pts:
        backbone(cv, pts, w0=wmax, w1=wmax)
    # stem leaves: from each fork a long acanthus blade hugs the stem on the side away from its scroll,
    # toothed edge out, running toward the next scroll; a shorter one answers it from the far end
    pairs = []
    if lead is None:
        pairs = [(None, scrolls[0])]
    pairs += list(zip(scrolls, scrolls[1:]))
    for (a_, b_), pts in zip(pairs, stem_pts):
        if len(pts) < 8 or H < 6:
            continue
        nm = _normals(pts)
        for which, sc, t0, t1 in (("a", a_, 0.04, rng.uniform(0.55, 0.7)), ("b", b_, rng.uniform(0.5, 0.62), 0.96)):
            if sc is None:
                continue
            i0, i1 = int(t0 * (len(pts) - 1)), int(t1 * (len(pts) - 1))
            seg = pts[i0:i1 + 1]
            if len(seg) < 4:
                continue
            mx, my = seg[len(seg) // 2]
            k = len(seg) // 2 + i0
            # side away from this scroll's centre
            sd = 1 if (nm[k][0] * (mx - sc.cx) + nm[k][1] * (my - sc.cy)) > 0 else -1
            room = H * rng.uniform(0.36, 0.46)
            off = []
            for j, (px, py) in enumerate(seg):
                q = nm[i0 + j]
                tt = j / (len(seg) - 1)
                o = (wmax * 0.5 + room * 0.42 * math.sin(math.pi * min(1.0, tt * 1.15)) ** 0.7)
                off.append((px + sd * q[0] * o, py + sd * q[1] * o))
            if which == "b":
                off = off[::-1]
            off = [(px, max(-hb + 0.4, min(hb - 0.4, py))) for px, py in off]
            finger(cv, off, room, shade=sd if which == "a" else -sd, cuts=2, cover=0.62)
    for sc in secondary:
        draw_scroll(cv, sc, rng, wmax=wmax * 0.8, R=sc.r * 1.5)
    for sc in scrolls:
        draw_scroll(cv, sc, rng, wmax=wmax, R=sc.R)
    _fill_gaps(cv, L, H, rng, scrolls + secondary)
    return scrolls


def _fill_gaps(cv, L, H, rng, scrolls):
    """Fill the ground left between scrolls with small curled leaves and tendril curls, each springing
    toward the nearest scroll's flow, so no pocket of bare ground is larger than a leaf."""
    occ = getattr(cv, "occ", None)
    if occ is None:
        return
    hb = H / 2
    pts = []
    step = 1.2
    y = -hb + step * 0.6
    while y < hb:
        x = step * rng.uniform(0.3, 0.8)
        while x < L:
            pts.append((x + rng.uniform(-0.4, 0.4) * step, y + rng.uniform(-0.3, 0.3) * step))
            x += step
        y += step * 0.8
    rng.shuffle(pts)
    for x, y in pts:
        rr = 1.6
        if not (-hb + rr < y < hb - rr) or not occ.free(x, y, rr):
            continue
        # grow to the room available
        while rr < H * 0.3 and occ.free(x, y, rr + 0.5):
            rr += 0.5
        near = min(scrolls, key=lambda s: math.hypot(s.cx - x, s.cy - y)) if scrolls else None
        if near is not None:
            ang = math.atan2(y - near.cy, x - near.cx) + near.dirn * math.pi / 2
        else:
            ang = rng.uniform(0, TAU)
        ln = rr * 2.0
        if rr >= 2.2 and rng.random() < 0.45:
            # a tendril curl with its leaf
            d = rng.choice((-1, 1))
            sc = Scroll(x, y, rr * 0.55, d, ang + math.pi, rng.uniform(1.2, 1.5), 0.25)
            draw_scroll(cv, sc, rng, wmax=0.9, R=rr * 0.95)
        else:
            bend = rng.uniform(-0.9, 0.9)
            sp = []
            for q in range(9):
                t = q / 8
                a = ang + bend * t
                sp.append((x - math.cos(ang) * ln * 0.5 + math.cos(a) * ln * t, y - math.sin(ang) * ln * 0.5 + math.sin(a) * ln * t))
            finger(cv, sp, rr * 1.15, shade=1 if bend > 0 else -1, cuts=1, cover=0.4)


def _run_map(run, flip=False, u0=0.0):
    def f(x, y):
        u = u0 + x
        if flip:
            u = run.L - u
        return run.p(u, -y)
    return f


DENSITY = 2.0  # white pricks per CSS px^2 of visible ground (0.5 px pricks: a fine dark matte, ~60 % ink)


def _base(cv):
    while isinstance(cv, Mapped):
        cv = cv.cv
    return cv


def strip(cv, run, seed, u0=0.0, u1=None, flip=False, start_side=1, ground=True, density=None, **kw):
    """Running fine scroll along `run` between u0 and u1, flowing in +u (or from the far end if flip).

    ground: True lays the black ground and stipples it; "dots" stipples only (the black is already
    laid); False draws scroll only.  The stipple goes only where the ground shows between the scrolls,
    and sits beneath them."""
    rng = rng_for("strip", seed)
    density = DENSITY if density is None else density
    u1 = run.L if u1 is None else u1
    H = run.H
    L = u1 - u0
    f = _run_map(run, flip, u0)
    occ = Occ(-2, -H / 2, L + 2, H / 2, cell=0.5)
    m = Mapped(cv, f, occ)
    base = _base(cv)
    if ground is True:
        m.poly("K", [(0, -H / 2), (L, -H / 2), (L, H / 2), (0, H / 2)])
        occ.g = [bytearray(occ.nx) for _ in range(occ.ny)]
    idx = len(base.ops)
    out = lane(m, L, H, rng, start_side, **kw)
    if ground:
        dots = []
        for _ in range(int(L * H * density)):
            x, y = rng.uniform(0.25, L - 0.25), rng.uniform(-H / 2 + 0.3, H / 2 - 0.3)
            i, j = int((x + 2) / occ.c), int((y + H / 2) / occ.c)
            if 0 <= j < occ.ny and 0 <= i < occ.nx and occ.g[j][i]:
                continue
            dots.append(f(x, y))
        base.ops.insert(idx, ("D", dots))
    return out


# ---------------------------------------------------------------- motifs

def fleuron(cv, x, y, s, up=(0, -1), rng=None):
    """Acanthus fleuron (anthemion) rising in direction `up`, base at (x, y), height s: a tall central
    leaf flanked by two turned-over leaves and a pair of tight volutes at the foot."""
    rng = rng or random.Random(1)
    ux, uy = up
    rx, ry = -uy, ux  # right

    def P(a, b):  # a along up, b to the right
        return (x + ux * a + rx * b, y + uy * a + ry * b)

    for sgn in (-1, 1):
        # foot volute
        cx, cy = P(s * 0.16, sgn * s * 0.30)
        r = s * 0.17
        pts = []
        for j in range(40):
            t = j / 39
            th = -sgn * TAU * 1.35 * t
            rr = r * (0.22 ** t)
            a, b = s * 0.16 - rr * math.sin(th + 0.0), sgn * s * 0.30 + rr * math.cos(th) * -sgn
            pts.append(P(a, b))
        backbone(cv, pts, 1.4 if s > 14 else 1.0, 0.5)
        # side leaf curling outward
        sp = [P(s * (0.18 + 0.55 * t), sgn * s * (0.08 + 0.32 * math.sin(t * 2.4))) for t in [k / 12 for k in range(13)]]
        leaf(cv, sp, width=s * 0.24, lobes=3, shade=sgn, rng=rng)
    # central leaf
    sp = [P(s * 0.08 + s * 0.88 * t, s * 0.03 * math.sin(t * 3)) for t in [k / 14 for k in range(15)]]
    leaf(cv, sp, width=s * 0.28, lobes=4, shade=1, rng=rng)
    bx, by = P(s * 0.06, 0)
    bud(cv, bx, by, max(0.9, s * 0.07))


def shell(cv, x, y, s, up=(0, -1)):
    """Scallop shell, hinge at (x, y), opening toward `up`, radius s: ribs as bright flutes, cut furrows."""
    ux, uy = up
    rx, ry = -uy, ux
    n = 9 if s > 8 else 7
    outline = []
    for i in range(n * 6 + 1):
        a = math.pi * (i / (n * 6))
        bump = 1.0 + 0.07 * abs(math.sin(a * n))
        outline.append((x + (rx * math.cos(a) + ux * math.sin(a)) * s * bump,
                        y + (ry * math.cos(a) + uy * math.sin(a)) * s * bump))
    cv.poly("W", [(x, y)] + outline)
    cv.poly("C05", [(x, y)] + outline)
    for i in range(1, n):
        a = math.pi * i / n
        e = (x + (rx * math.cos(a) + ux * math.sin(a)) * s * 0.98, y + (ry * math.cos(a) + uy * math.sin(a)) * s * 0.98)
        m = (x + (rx * math.cos(a) + ux * math.sin(a)) * s * 0.18, y + (ry * math.cos(a) + uy * math.sin(a)) * s * 0.18)
        cv.line("C05", [m, e])
        # furrow shading on the shadow side of each rib
        a2 = a + math.pi / n * 0.32
        e2 = (x + (rx * math.cos(a2) + ux * math.sin(a2)) * s * 0.9, y + (ry * math.cos(a2) + uy * math.sin(a2)) * s * 0.9)
        m2 = (x + (rx * math.cos(a2) + ux * math.sin(a2)) * s * 0.5, y + (ry * math.cos(a2) + uy * math.sin(a2)) * s * 0.5)
        if s > 6:
            cv.line("C05", [m2, e2])
    bud(cv, x, y, max(0.8, s * 0.14))


def rosette(cv, x, y, r, petals=8, rng=None):
    """Rosette boss: lobed petals radiating, each with a vein and a shaded flank, pearl at the heart."""
    rng = rng or random.Random(2)
    for i in range(petals):
        a = TAU * i / petals + 0.2
        sp = [(x + math.cos(a + 0.25 * t) * r * (0.2 + 0.8 * t), y + math.sin(a + 0.25 * t) * r * (0.2 + 0.8 * t))
              for t in [k / 8 for k in range(9)]]
        leaf(cv, sp, width=r * 0.55, lobes=2, shade=1, rng=rng, cuts=0.8)
    bud(cv, x, y, r * 0.24)


# ---------------------------------------------------------------- frames

def inlay(cv, x, y, w, h, outer=True):
    """Crisp double inlay line round a field: 1 px rule, white channel, 0.5 px rule."""
    if outer:
        cv.add("R1", "M%s %sH%sV%sH%sZ" % (_f(x + 0.5), _f(y + 0.5), _f(x + w - 0.5), _f(y + h - 0.5), _f(x + 0.5)))
        cv.add("R05", "M%s %sH%sV%sH%sZ" % (_f(x + 2.25), _f(y + 2.25), _f(x + w - 2.25), _f(y + h - 2.25), _f(x + 2.25)))
    else:
        cv.add("R05", "M%s %sH%sV%sH%sZ" % (_f(x + 0.25), _f(y + 0.25), _f(x + w - 0.25), _f(y + h - 0.25), _f(x + 0.25)))
        cv.add("R1", "M%s %sH%sV%sH%sZ" % (_f(x + 2), _f(y + 2), _f(x + w - 2), _f(y + h - 2), _f(x + 2)))


def volute(cv, cx, cy, R, dirn, a0, rng, wmax=1.2, turns=None):
    """A free-standing scroll of footprint radius R, its stem joining at screen angle a0."""
    rb = R * rng.uniform(0.6, 0.68)
    sc = Scroll(cx, cy, rb, dirn, a0, turns or rng.uniform(1.4, 1.7), rng.uniform(0.13, 0.2))
    draw_scroll(cv, sc, rng, wmax=wmax, R=R)
    return sc


def _stipple_rect(cv, x0, y0, x1, y1, rng, density=1.1):
    n = int(max(0.0, x1 - x0) * max(0.0, y1 - y0) * density)
    for _ in range(n):
        cv.dot(rng.uniform(x0 + 0.3, x1 - 0.3), rng.uniform(y0 + 0.3, y1 - 0.3))


def _rect_d(x0, y0, x1, y1):
    return "M%s %sH%sV%sH%sZ" % (_f(x0), _f(y0), _f(x1), _f(y1), _f(x0))


def corner(cv, x, y, s, quad, seed, rng=None):
    """Corner piece in the s x s lane square at (x, y): a volute turning the corner, its blade leaf
    sweeping round, and a bud pointing out along the diagonal.  quad: 'tl', 'tr', 'br', 'bl'."""
    rng = rng or rng_for("corner", seed, quad)
    sx = 1 if quad in ("tl", "bl") else -1
    sy = 1 if quad in ("tl", "tr") else -1
    ox = x if sx > 0 else x + s
    oy = y if sy > 0 else y + s
    m = Mapped(cv, lambda a, b: (ox + sx * a, oy + sy * b))
    # the scroll sits in the square; its stem arrives from the inner side (along +a then +b)
    if s >= 5:
        sc = Scroll(s * 0.52, s * 0.52, s * 0.3, 1, math.pi * 0.75, 1.55, 0.16)
        if s >= 9:
            finger(m, [(s * 0.46 - s * 0.36 * t, s * 0.46 - s * 0.36 * t + s * 0.08 * math.sin(t * 3)) for t in
                       [k / 10 for k in range(11)]], s * 0.32, shade=1, cuts=2)
        draw_scroll(m, sc, rng, wmax=1.2 if s >= 9 else 0.9, R=s * 0.46)
        bud(m, s * 0.12, s * 0.12, max(0.6, s * 0.07))


def _lane_rects(x, y, w, h, ins, o=1.5, i=2.0):
    t, r, b, l = ins
    return {
        "top": (x + l, y + o, x + w - r, y + t - i),
        "right": (x + w - r + i, y + t, x + w - o, y + h - b),
        "bottom": (x + l, y + h - b + i, x + w - r, y + h - o),
        "left": (x + o, y + t, x + l - i, y + h - b),
    }


def band_rect(cv, x, y, w, h, ins, seed, centre=("fleuron", None, "shell", None), corners=True,
              density=1.1, ends=None, slot=True, open_sides=()):
    """A fine-scroll band round the rectangle (x, y, w, h), ins = (t, r, b, l) band widths.

    Band anatomy, outside in: 0.5 px rule, 1 px bright inlay, the stippled ground with its scroll, 1 px
    bright inlay, 1 px rule against the white slot.  Each side is composed afresh from its centre motif
    out to the corners (balanced, never mirror-copied); each corner is turned by a volute.
    centre: motif per side (top, right, bottom, left): 'fleuron', 'shell', 'rosette' or None.
    ends: None, or a kind ('scroll' | 'point' | 'roll') to replace the left and right sides with shaped
    scrolled ends (the outline leaves the rectangle; outside stays transparent).
    open_sides: sides with no band ('top'/'bottom'); those get small scrolled terminals instead.
    """
    t, r, b, l = ins
    density = DENSITY if density is None else density
    if slot and hasattr(cv, "slot"):
        cv.slot = (x + l, y + t, w - l - r, h - t - b)
    if ends:
        _band_with_ends(cv, x, y, w, h, ins, seed, centre, density, ends)
        return
    # ground and the outer rule as one black frame
    cv.add("K", _rect_d(x, y, x + w, y + h))
    top = getattr(cv, "over", cv.add)
    if hasattr(cv, "clip") and cv.clip is None:
        cv.clip = _rect_d(x, y, x + w, y + h)
    if slot:
        top("W", _rect_d(x + l, y + t, x + w - r, y + h - b))
    rng = rng_for("band", seed)
    o, i = (1.5 if min(ins) >= 12 else 0.5), 2.0
    lanes = _lane_rects(x, y, w, h, ins, o, i)
    # stipple the corners (the lanes stipple their own visible ground)
    for cx0, cy0, cx1, cy1 in ((x + o, y + o, x + l - i, y + t - i), (x + w - r + i, y + o, x + w - o, y + t - i),
                               (x + w - r + i, y + h - b + i, x + w - o, y + h - o), (x + o, y + h - b + i, x + l - i, y + h - o)):
        _stipple_rect(cv, cx0, cy0, cx1, cy1, rng, density)
    # scroll in each lane, flowing out from the centre motif to the corners
    runs = {
        "top": lambda X0, Y0, X1, Y1: [(X0, (Y0 + Y1) / 2), (X1, (Y0 + Y1) / 2)],
        "right": lambda X0, Y0, X1, Y1: [((X0 + X1) / 2, Y0), ((X0 + X1) / 2, Y1)],
        "bottom": lambda X0, Y0, X1, Y1: [(X1, (Y0 + Y1) / 2), (X0, (Y0 + Y1) / 2)],
        "left": lambda X0, Y0, X1, Y1: [((X0 + X1) / 2, Y1), ((X0 + X1) / 2, Y0)],
    }
    for k, name in enumerate(("top", "right", "bottom", "left")):
        x0, y0, x1, y1 = lanes[name]
        H = (y1 - y0) if name in ("top", "bottom") else (x1 - x0)
        if H < 2.5:
            continue
        run = Run(runs[name](x0, y0, x1, y1), H)
        _compose_side(cv, run, (seed, name), centre[k] if k < len(centre) else None, k)
    # inlay: bright channels and rules
    top("R05", _rect_d(x + 0.25, y + 0.25, x + w - 0.25, y + h - 0.25))
    if o > 1:
        top("S1", _rect_d(x + 1, y + 1, x + w - 1, y + h - 1))
    top("S1", _rect_d(x + l - 1.5, y + t - 1.5, x + w - r + 1.5, y + h - b + 1.5))
    top("R1", _rect_d(x + l - 0.5, y + t - 0.5, x + w - r + 0.5, y + h - b + 0.5))
    if corners:
        for quad, (cx0, cy0, cx1, cy1) in (("tl", (x + o, y + o, x + l - i, y + t - i)),
                                           ("tr", (x + w - r + i, y + o, x + w - o, y + t - i)),
                                           ("br", (x + w - r + i, y + h - b + i, x + w - o, y + h - o)),
                                           ("bl", (x + o, y + h - b + i, x + l - i, y + h - o))):
            s = min(cx1 - cx0, cy1 - cy0)
            if s >= 3:
                corner(cv, cx0 + (cx1 - cx0 - s) / 2, cy0 + (cy1 - cy0 - s) / 2, s, quad, seed)


def _compose_side(cv, run, seed, motif, k, density=None):
    rng = rng_for("side", seed)
    density = DENSITY if density is None else density
    L, H = run.L, run.H
    msz = H * 1.3 if motif and L > 5 * H else 0
    if not msz:
        strip(cv, run, seed, 0, L, ground="dots", start_side=1 if k % 2 == 0 else -1, density=density)
        return
    half = (L - msz) / 2
    strip(cv, run, (seed, "a"), 0, half, flip=True, ground="dots", start_side=1, density=density)
    strip(cv, run, (seed, "b"), 0, half, flip=False, ground="dots", start_side=-1, density=density)
    m = Mapped(cv, lambda u, v: run.p(u, v))
    for _ in range(int(msz * H * density)):
        m.dot(rng.uniform(half + 0.2, half + msz - 0.2), rng.uniform(-H / 2 + 0.3, H / 2 - 0.3))
    cx, cy = run.p(L / 2, 0)
    ox, oy = run.p(L / 2, -H / 2)  # inner edge of the lane
    ux, uy = _norm(ox - cx, oy - cy)
    if motif == "fleuron":
        fleuron(cv, ox - ux * 0.3, oy - uy * 0.3, H * 1.0, up=(-ux, -uy), rng=rng)
    elif motif == "shell":
        shell(cv, ox - ux * 0.3, oy - uy * 0.3, H * 0.92, up=(-ux, -uy))
    elif motif == "rosette":
        rosette(cv, cx, cy, H * 0.48, rng=rng)


def _inside(poly, x, y, margin=0.0):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    if c and margin:
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy or 1.0
            k = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
            if math.hypot(x - x1 - k * dx, y - y1 - k * dy) < margin:
                return False
    return c


def _band_with_ends(cv, x, y, w, h, ins, seed, centre, density, kind):
    """Plaque with shaped scrolled ends: top and bottom bands of scroll, and at each end a scrolled
    cartouche end whose outline leaves the rectangle (kind 'scroll': twin volutes meeting in a bud;
    'point': a pointed ogee end with one big volute; 'roll': a rolled ribbon end)."""
    t, r, b, l = ins
    rng = rng_for("ends", seed)
    o, i = 1.5, 2.0
    # outline of the whole plaque: straight top/bottom, shaped ends inside the end widths
    def end_outline(left):
        e = l if left else r
        X = x if left else x + w
        sg = 1 if left else -1
        pts = []
        n = 24
        for j in range(n + 1):
            q = j / n
            yy = y + h * q
            d = abs(q - 0.5) * 2  # 1 at top/bottom, 0 at middle
            if kind == "point":
                xx = X + sg * e * (0.85 * d ** 1.6)
            elif kind == "roll":
                xx = X + sg * e * (0.25 + 0.15 * math.cos(q * TAU))
            else:  # scroll: concave notch between two lobes
                xx = X + sg * e * (0.05 + 0.55 * (1 - math.sin(math.pi * q) ** 2) * 0 + 0.45 * math.sin(math.pi * d) ** 1.2 * (1 - d * 0.3))
            pts.append((xx, yy))
        return pts
    Lp = end_outline(True)
    Rp = end_outline(False)
    outline = [(x + l, y)] + [(px, py) for px, py in Lp[::-1]][::-1][:0] + []
    outline = [(x + l, y), (x + w - r, y)] + Rp + [(x + w - r, y + h), (x + l, y + h)] + Lp[::-1]
    cv.poly("K", outline)
    cv.poly("C05", outline)
    # stipple, only inside the outline
    n = int((l + r) * h * density)
    for _ in range(n):
        px = rng.uniform(0, l + r)
        px = x + px if px < l else x + w - (px - l)
        py = rng.uniform(y + o, y + h - o)
        if _inside(outline, px, py, 0.8):
            cv.dot(px, py)
    cv.add("W", _rect_d(x + l, y + t, x + w - r, y + h - b))
    # top and bottom lanes
    for k, name in ((0, "top"), (2, "bottom")):
        if name == "top":
            y0, y1 = y + o, y + t - i
            pts = [(x + l, (y0 + y1) / 2), (x + w - r, (y0 + y1) / 2)]
        else:
            y0, y1 = y + h - b + i, y + h - o
            pts = [(x + w - r, (y0 + y1) / 2), (x + l, (y0 + y1) / 2)]
        H = y1 - y0
        if H >= 2.5:
            _compose_side(cv, Run(pts, H), (seed, name), centre[k] if k < len(centre) else None, k)
    # the ends: volutes
    for left in (True, False):
        e = l if left else r
        sg = 1 if left else -1
        X = x if left else x + w
        Xin = x + l if left else x + w - r
        R = min(h * 0.25, e * 0.42)
        if kind == "point":
            volute(cv, X + sg * e * 0.55, y + h / 2, min(h * 0.3, e * 0.42), sg, math.pi / 2, rng)
        elif kind == "roll":
            for q, d in ((0.3, 1), (0.7, -1)):
                volute(cv, X + sg * e * 0.5, y + h * q, R, d * sg, -math.pi / 2 * d, rng)
        else:
            for q, d in ((0.28, 1), (0.72, -1)):
                volute(cv, X + sg * e * 0.52, y + h * q, R, -d * sg, (math.pi if left else 0.0), rng)
            bud(cv, X + sg * e * 0.2, y + h / 2, max(0.7, h * 0.05))
    # inlay: bright line inside the outline and round the slot, and the slot rule
    inl = []
    for px, py in outline:
        inl.append((px, py))
    cv.add("S1", _rect_d(x + l - 1.5, y + t - 1.5, x + w - r + 1.5, y + h - b + 1.5))
    cv.add("R1", _rect_d(x + l - 0.5, y + t - 0.5, x + w - r + 0.5, y + h - b + 0.5))
    cv.line("S1", [(x + l * 0.6, y + 1), (x + w - r * 0.6, y + 1)])
    cv.line("S1", [(x + l * 0.6, y + h - 1), (x + w - r * 0.6, y + h - 1)])


def ring(cv, cx, cy, rx, ry, band, seed, density=1.1):
    """An oval ring of scroll (centreline ellipse rx, ry), for a cartouche round a scene."""
    n = 240
    pts = [(cx + rx * math.cos(-math.pi / 2 + TAU * i / n), cy + ry * math.sin(-math.pi / 2 + TAU * i / n)) for i in range(n + 1)]
    run = Run(pts, band)
    rng = rng_for("ring", seed)
    _ground_in_run(cv, run, 0, run.L, -band / 2, band / 2, rng, density)
    inner = Run(pts, band - 5.5)
    strip(cv, inner, (seed, "ring-a"), 0, run.L / 2, flip=True, ground=False)
    strip(cv, inner, (seed, "ring-b"), 0, run.L / 2, ground=False, start_side=-1)
    for off in (band / 2 - 0.5, -band / 2 + 0.5):
        cv.poly("C1", Run(pts, 0).map([(u, off) for u in [run.L * i / 240 for i in range(241)]]), close=False)


def fill_rect(cv, x, y, w, h, seed, row=None, density=1.1):
    """Fill a whole rectangle with rows of fine scroll (for grounds). Rows interlock by alternating flow."""
    row = row or min(h, 22.0)
    n = max(1, int(round(h / row)))
    rh = h / n
    for i in range(n):
        yy = y + rh * (i + 0.5)
        run = Run([(x, yy), (x + w, yy)], rh)
        strip(cv, run, (seed, "row", i), flip=bool(i % 2), start_side=1 if i % 2 else -1, density=density)
