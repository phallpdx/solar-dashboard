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
import re
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


TOL = 0.08  # path simplification tolerance, CSS px (0.16 device px at DPR 2)


def _dp(q, tol):
    keep = [False] * len(q)
    keep[0] = keep[-1] = True
    stack = [(0, len(q) - 1)]
    while stack:
        i0, i1 = stack.pop()
        (ax, ay), (cx, cy) = q[i0], q[i1]
        dx, dy = cx - ax, cy - ay
        d = math.sqrt(dx * dx + dy * dy)
        best, bi = -1.0, -1
        for i in range(i0 + 1, i1):
            bx, by = q[i]
            e = abs((bx - ax) * dy - (by - ay) * dx) / d if d else math.hypot(bx - ax, by - ay)
            if e > best:
                best, bi = e, i
        if bi > 0 and best > tol:
            keep[bi] = True
            stack.append((i0, bi))
            stack.append((bi, i1))
    return [p for p, k in zip(q, keep) if k]


def _pts(pts, tol=TOL):
    """Absolute first point, then relative lineto deltas computed on the rounded grid (no drift)."""
    q = [(round(x * 10), round(y * 10)) for x, y in pts]
    if len(q) > 2:  # Douglas-Peucker: drop points within TOL px of the simplified path
        q = _dp(q, tol * 10)
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
    "M": 'fill="url(#mt)"',
    "W": 'fill="#fff"',
    "S05": 'fill="none" stroke="#fff" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round"',
    "G1": 'fill="#bbb"',
    "G0": 'fill="#ccc"',
    "GA": 'fill="#aaa"',
    "G2": 'fill="#888"',
    "WO": 'fill="#fff" stroke="#000" stroke-width="1" stroke-linejoin="round" paint-order="stroke"',
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
            self.add(key, "M" + _pts(pts, getattr(self, "tol", TOL)) + ("Z" if close else ""))

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

    MATTE = (29, 23)  # the stipple tile: odd sizes, random pricks; nothing in the scroll shares its period

    def _matte(self):
        """The cut-away ground: black, finely and irregularly pricked (1 device px pricks, ~2 per CSS px^2),
        as one small random tile.  At 37 x 29 px of pure noise its period cannot be seen."""
        tw, th = self.MATTE
        rng = random.Random(zlib.crc32(("matte", self.w, self.h).encode() if False else repr(("matte", self.w, self.h)).encode()))
        ds = []
        for _ in range(int(tw * th * DENSITY)):
            ds.append((rng.uniform(0, tw), rng.uniform(0, th)))
        return ('<defs><pattern id="mt" width="%d" height="%d" patternUnits="userSpaceOnUse">'
                '<path fill="#000" d="M0 0H%dV%dH0Z"/><path class="d" d="%s"/></pattern></defs>' % (tw, th, tw, th, self._dots(ds)))

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
        ops = _batch(self.ops) + self.top
        used = sorted({k for k, _ in ops} | ({"D"} if any(k == "M" for k, _ in ops) else set()))
        css = "".join(".%s{%s}" % (k.lower(), CSS[k]) for k in used)
        body = "".join('<path class="%s" d="%s"/>' % (k.lower(), self._dots(ds) if k == "D" else "".join(ds)) for k, ds in ops)
        if any(k == "M" for k, _ in ops):
            body = self._matte() + body
        if self.clip:
            cid = "c%x" % (zlib.crc32(self.clip.encode()) & 0xffffff)
            body = '<clipPath id="%s"><path clip-rule="evenodd" d="%s"/></clipPath><g clip-path="url(#%s)">%s</g>' % (cid, self.clip, cid, body)
        return "<style>%s</style>" % css + body

    def svg(self):
        slot = ' data-slot="%s"' % " ".join(_f(v) for v in self.slot) if self.slot else ""
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s"%s>%s</svg>'
                % (_f(self.w), _f(self.h), _f(self.w), _f(self.h), slot, self.body()))


_TOK = re.compile(r"[MmlhHVaZ]|-?(?:\d+\.?\d*|\.\d+)")


def _bbox(d):
    """Bounding box of one of our own path strings (M, l, h, H, V, a, Z), or None if it can't be read."""
    t = _TOK.findall(d)
    xs, ys = [], []
    x = y = 0.0
    i, cmd, n = 0, None, len(t)
    try:
        while i < n:
            if t[i].isalpha():
                cmd = t[i]
                i += 1
                if cmd == "Z":
                    continue
            if cmd == "M":
                x, y = float(t[i]), float(t[i + 1]); i += 2; cmd = "l" if False else "L_"
            elif cmd in ("l", "L_"):
                if cmd == "l":
                    x += float(t[i]); y += float(t[i + 1])
                else:
                    cmd = "l"; continue
                i += 2
            elif cmd == "h":
                x += float(t[i]); i += 1
            elif cmd == "H":
                x = float(t[i]); i += 1
            elif cmd == "V":
                y = float(t[i]); i += 1
            elif cmd == "a":
                r = float(t[i]); x += float(t[i + 5]); y += float(t[i + 6]); i += 7
                xs += [x - 2 * r, x + 2 * r]; ys += [y - 2 * r, y + 2 * r]
            else:
                return None
            xs.append(x); ys.append(y)
    except (IndexError, ValueError):
        return None
    if not xs:
        return None
    return (min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)


def _hit(a, b):
    return a is None or b is None or not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _batch(ops, depth=60):
    """Merge each path into an earlier group of its own class when nothing drawn in between overlaps it,
    so the file has far fewer <path> elements.  Painting order between overlapping shapes is kept."""
    out = []  # [key, [d...], [bbox...]]
    for key, ds in ops:
        if key in ("D", "M"):
            out.append([key, list(ds), [None]])
            continue
        for d in ds:
            bb = _bbox(d)
            tgt = None
            for g in range(len(out) - 1, max(-1, len(out) - 1 - depth), -1):
                if out[g][0] == key:
                    tgt = g
                    break
                if any(_hit(bb, o) for o in out[g][2]):
                    break
            if tgt is None:
                out.append([key, [d], [bb]])
            else:
                out[tgt][1].append(d)
                out[tgt][2].append(bb)
    return [(k, ds) for k, ds, _ in out]


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
        cv.line("S1", [(x, y), (x + 0.01, y)])
        return
    cv.circle("W", x, y, r)


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
    """One scroll in a y-down frame: footprint radius R, winding dirn (+1 clockwise on screen), start
    angle a0 (screen radians) where its stem joins.  The outer turn stays nearly round; the last part
    tightens into a small volute eye."""

    def __init__(self, cx, cy, R, dirn, a0, turns=1.35, eye=0.17):
        self.cx, self.cy, self.R, self.dirn, self.a0 = cx, cy, R, dirn, a0
        self.turns, self.eye = turns, eye
        self.r = R

    def rad(self, f):
        u = min(max(f / self.turns, 0.0), 1.0)
        return self.R * (1.0 - (1.0 - self.eye) * u ** 1.3)

    def point(self, f, rscale=1.0):
        th = self.a0 + self.dirn * TAU * f
        r = self.rad(f) * rscale
        return (self.cx + r * math.cos(th), self.cy + r * math.sin(th))

    def tangent_at(self, f):
        a, b = self.point(f - 0.005), self.point(f + 0.005)
        return _norm(b[0] - a[0], b[1] - a[1])

    def start(self):
        return self.point(0)

    def tangent(self):
        return self.tangent_at(0)

    def arc(self, f0, f1, rscale=1.0, n=None):
        n = n or max(8, int(abs(f1 - f0) * 4.5 * max(self.R, 2.0)))
        return [self.point(f0 + (f1 - f0) * i / n, rscale) for i in range(n + 1)]

    def pts(self):
        return self.arc(0, self.turns)


def lobe(cv, spine, width, shade=1, cuts=True, tip=True, teeth=0, rib=False):
    """One acanthus lobe along the polyline `spine` (base to tip): a pointed blade, widest a third of the
    way, crisp outline, bright face; fine cuts along its curve on the shadow side only (shade=+1 the left
    of travel, -1 the right), longest next to the edge; the tip turned over (a short cut back along the
    lit edge) and a vein cut from the base."""
    step = max(0.8, min(1.6, width * 0.28))
    if teeth:
        step = min(step, max(0.5, _arclen(spine)[-1] / (teeth * 5 + 4)))
    spine = _resample(spine, step)
    n = len(spine)
    if n < 4:
        return None
    nm = _normals(spine)
    hw = width / 2
    sg = 1 if shade > 0 else -1
    if teeth:
        _env0 = None

    def env(t, s):
        e = math.sin(math.pi * min(1.0, t ** 0.72)) ** 0.85 * (1.0 - 0.2 * t)
        if teeth and t > 0.3:
            # serrated outline: saw teeth raking toward the tip, offset between the two flanks
            q = ((t - 0.3) / 0.7 * teeth + (0.5 if s == sg else 0.0)) % 1.0
            e *= 1.0 - 0.3 * q
        return e * (0.82 if s == sg else 1.0)  # shadow flank a little narrower: the lobe leans to the light

    Sd, Lt = [], []
    for i, (p, q) in enumerate(zip(spine, nm)):
        t = i / (n - 1)
        a, b = hw * env(t, sg), hw * env(t, -sg)
        Sd.append((p[0] + sg * q[0] * a, p[1] + sg * q[1] * a))
        Lt.append((p[0] - sg * q[0] * b, p[1] - sg * q[1] * b))
    poly = Sd + Lt[::-1][1:-1]
    cv.poly("WO", poly)
    model = getattr(_base(cv), "model", False) and width >= 2.6
    if model:
        # silver: the face light grey with only a narrow white lit edge, darkening toward the root on the
        # shadow flank; the black cuts carry the rest of the modelling
        face_o, face_i = [], []
        for i, (p, q) in enumerate(zip(spine, nm)):
            t = i / (n - 1)
            a = hw * env(t, sg) - 0.1
            b = hw * env(t, -sg) - 0.6
            if a + b < 0.4:
                continue
            face_o.append((p[0] + sg * q[0] * a, p[1] + sg * q[1] * a))
            face_i.append((p[0] - sg * q[0] * b, p[1] - sg * q[1] * b))
        if len(face_o) > 2:
            cv.poly("G0", face_o + face_i[::-1])
        outer, inner = [], []
        for i, (p, q) in enumerate(zip(spine, nm)):
            t = i / (n - 1)
            if t > 0.6:
                break
            a = hw * env(t, sg) - 0.1
            c = 1.2 * (1.0 - t / 0.6) ** 0.8
            o = max(-hw * env(t, -sg) * 0.35, a * (1.0 - c))
            if a <= 0.2 or o >= a - 0.2:
                continue
            outer.append((p[0] + sg * q[0] * a, p[1] + sg * q[1] * a))
            inner.append((p[0] + sg * q[0] * o, p[1] + sg * q[1] * o))
        if len(outer) > 2:
            cv.poly("GA", outer + inner[::-1])
    if cuts and width >= 2.8:
        k = 1
        pitch = 1.05 if model else 1.5
        while True:
            d = k * pitch - (0.45 if model else 0.6)
            if d > hw * 0.85:
                break
            stop = (0.72 - 0.18 * k) if not model else (0.8 - 0.075 * k)
            seg = []
            for i in range(n):
                t = i / (n - 1)
                a = hw * env(t, sg)
                if 0.06 < t < stop and a - d > 0.45:
                    o = a - d
                    seg.append((spine[i][0] + sg * nm[i][0] * o, spine[i][1] + sg * nm[i][1] * o))
                elif seg:
                    break
            if len(seg) > 2:
                cv.line("C05", seg)
            k += 1
            if k > ((2 if width < 5 else 3 if width < 8 else 5) if not model else (3 if width < 5 else 5 if width < 8 else 8)):
                break
    if rib and width >= 3.0 and n >= 6:
        cv.line("C05", spine[int(n * 0.1):int(n * 0.78)])
    if tip and width >= 2.0 and n >= 6:
        j0 = int((n - 1) * 0.8)
        seg = []
        for i in range(j0, n - 1):
            t = i / (n - 1)
            b = hw * env(t, -sg) * 0.55
            seg.append((spine[i][0] - sg * nm[i][0] * b, spine[i][1] - sg * nm[i][1] * b))
        seg.append(spine[-1])
        if len(seg) > 2:
            cv.line("C05", seg)
    return poly


def _curve(base, ang, length, bend, n=10, hook=0.0):
    """A smooth curve from base heading `ang`, turning by `bend` radians over its length, the last fifth
    turning a further `hook` (the lobe's turned tip)."""
    pts = [base]
    x, y = base
    for i in range(1, n + 1):
        t = (i - 0.5) / n
        a = ang + bend * t + (hook * ((t - 0.8) / 0.2) if t > 0.8 else 0.0)
        x += math.cos(a) * length / n
        y += math.sin(a) * length / n
        pts.append((x, y))
    return pts


def fan(cv, base, ang, length, width, n, side, rng, bend=0.6, spread=0.9, order="back"):
    """An acanthus leaf as a fan of n overlapping pointed lobes springing from `base`: the first runs
    along `ang`, the others splay out to `side` (+1 clockwise on screen) and curl back toward the flow;
    each sits on the one behind it, its shadow flank toward it."""
    lobes = []
    for i in range(n):
        u = i / max(1, n - 1)
        a = ang + side * spread * u * rng.uniform(0.85, 1.1)
        ln = length * (1.0 - 0.32 * u) * rng.uniform(0.9, 1.08)
        wd = width * (1.0 - 0.25 * u) * rng.uniform(0.9, 1.1)
        b0 = (base[0] + math.cos(a) * width * 0.15, base[1] + math.sin(a) * width * 0.15)
        lobes.append((_curve(b0, a, ln, -side * bend * rng.uniform(0.8, 1.2), 10, -side * 0.5), wd))
    seq = lobes[::-1] if order == "back" else lobes
    for sp, wd in seq:
        lobe(cv, sp, wd, shade=-side)


def acanthus(cv, spine, width, side, rng, lobes=3):
    """A compound acanthus leaf along `spine`: a long main lobe, and side lobes springing from its `side`
    flank (+1 left of travel) that sweep back alongside it, each smaller toward the tip, layered behind
    the main lobe so its crisp edge reads over them."""
    sp = _resample(spine, 0.8)
    if len(sp) < 5:
        return
    s = _arclen(sp)
    Ltot = s[-1]
    nm = _normals(sp)
    side_lobes = []
    for j in range(lobes):
        t = 0.18 + 0.55 * j / max(1, lobes) + rng.uniform(-0.04, 0.04)
        (bx, by), (tx, ty) = _at(sp, s, t)
        nx, ny = -ty * side, tx * side
        a = math.atan2(ty, tx)
        out = math.atan2(ny, nx)
        # leave splayed out, then swing back to run with the leaf, tip curling out
        ang = a + (out - a) * 0.0
        spread = 0.75 - 0.15 * j
        start = math.atan2(math.sin(a) * math.cos(spread) + ny * math.sin(spread),
                           math.cos(a) * math.cos(spread) + nx * math.sin(spread))
        ln = Ltot * (0.6 - 0.12 * j) * rng.uniform(0.9, 1.1)
        turn = a - start
        turn = (turn + math.pi) % TAU - math.pi
        b0 = (bx + nx * width * 0.2, by + ny * width * 0.2)
        side_lobes.append((_curve(b0, start, ln, turn * 1.2, 10, -turn * 0.6), width * (0.72 - 0.1 * j)))
    for spn, wd in side_lobes[::-1]:
        lobe(cv, spn, wd, shade=-side)
    lobe(cv, sp, width, shade=-side)


def draw_scroll(cv, sc, rng, bw=None, R=None, inner=True, inner_w=None):
    """A scroll: a broad bright backbone ribbon with a groove cut along its inner side, winding into a
    tight volute that ends in a round button; a lobe rolled into the curl."""
    R = sc.R
    bw = bw or max(1.5, min(5.0, R * 0.5))
    pts = _resample(sc.pts(), max(0.8, R * 0.12))
    n = len(pts)
    if n < 4:
        return
    nm = _normals(pts)
    L, Rr = [], []
    for i, (p, q) in enumerate(zip(pts, nm)):
        t = i / (n - 1)
        h = bw / 2 * (1.0 - 0.55 * t)
        L.append((p[0] + q[0] * h, p[1] + q[1] * h))
        Rr.append((p[0] - q[0] * h, p[1] - q[1] * h))
    if inner and R >= 3.5:
        # two lobes rolled into the curl, the second lying over the first
        iw = inner_w or R * 0.8
        lobe(cv, sc.arc(0.04, 0.78, rscale=0.6), iw, shade=sc.dirn)
        if R >= 6.5:
            lobe(cv, sc.arc(0.5, 1.02, rscale=0.6), iw * 0.55, shade=sc.dirn)
    cv.poly("WO", L + Rr[::-1])
    if getattr(_base(cv), "model", False) and bw >= 2.0:
        # the ribbon turned toward the centre falls into shadow: pale grey on that half, deepening near the eye
        sh_o, sh_i = [], []
        for i, (p, q) in enumerate(zip(pts, nm)):
            t = i / (n - 1)
            h = bw / 2 * (1.0 - 0.55 * t)
            if h < 0.6:
                continue
            cx, cy = sc.cx - p[0], sc.cy - p[1]
            sd = 1 if q[0] * cx + q[1] * cy > 0 else -1
            o1, o2 = sd * (h - 0.1), -sd * (h - 0.55)
            sh_o.append((p[0] + q[0] * o1, p[1] + q[1] * o1))
            sh_i.append((p[0] + q[0] * o2, p[1] + q[1] * o2))
        if len(sh_o) > 2:
            cv.poly("G0", sh_o + sh_i[::-1])
    # groove cut along the inner side of the ribbon (toward the centre: the shadow)
    if bw >= 2.0:
        gi = []
        for i, (p, q) in enumerate(zip(pts, nm)):
            t = i / (n - 1)
            if 0.04 < t < 0.8:
                h = bw / 2 * (1.0 - 0.55 * t)
                # which normal side faces the centre?
                cx, cy = sc.cx - p[0], sc.cy - p[1]
                s = 1 if q[0] * cx + q[1] * cy > 0 else -1
                o = s * max(0.0, h - 0.75)
                gi.append((p[0] + q[0] * o, p[1] + q[1] * o))
        if len(gi) > 2:
            cv.line("C05", gi)
    e = pts[-1]
    rb = max(0.75, sc.rad(sc.turns) * 0.95)
    if rb <= 0.8:
        cv.line("S15", [e, (e[0] + 0.01, e[1])])
    else:
        cv.circle("W", e[0], e[1], rb)


def _scroll_from(p, tdir, centre, R, rng, turns=None):
    """A scroll of radius R centred at `centre` whose stem arrives at p heading tdir: start angle from the
    centre toward p, winding chosen so it carries on the way the stem was going."""
    a0 = math.atan2(p[1] - centre[1], p[0] - centre[0])
    best = None
    for d in (1, -1):
        sc = Scroll(centre[0], centre[1], R, d, a0, turns or rng.uniform(1.25, 1.5), rng.uniform(0.14, 0.2))
        tx, ty = sc.tangent()
        score = tx * tdir[0] + ty * tdir[1]
        if best is None or score > best[0]:
            best = (score, sc)
    return best[1]


def _stem(cv, p0, t0, p3, t3, w, k=0.42):
    d = math.hypot(p3[0] - p0[0], p3[1] - p0[1]) * k
    pts = _bez(p0, (p0[0] + t0[0] * d, p0[1] + t0[1] * d), (p3[0] - t3[0] * d, p3[1] - t3[1] * d), p3, 16)
    pts = _resample(pts, 1.0)
    poly, _, _ = _ribbon(pts, [w / 2] * len(pts))
    cv.poly("W", poly)
    return pts


def lane(cv, L, H, rng, start_side=1, **kw):
    """Compose fine scroll in the lane x in [0, L], y in [-H/2, H/2] (y down).

    Big scrolls dominate, alternating side and size; between each pair the stem crosses the lane, and the
    two pockets it leaves are filled one with a subordinate scroll (2-3x smaller, branching off the stem and
    winding against its neighbours) and one with an acanthus fan; leftover ground gets single lobes."""
    hb = H / 2 - 0.4
    if L < H * 0.7:
        # too short for a run: one scroll and a fan
        R = min(hb, L / 2 - 0.3)
        sc = Scroll(L / 2, 0, R, 1 if start_side > 0 else -1, math.pi / 2, 1.35, 0.17)
        draw_scroll(cv, sc, rng)
        return [sc]
    bigs = []
    side = start_side
    k = 0
    x = 0.0
    while True:
        # a dominant scroll every third place, the two between it smaller and unequal (no two alike)
        Rb = H * (0.49, 0.31, 0.39)[k % 3] * rng.uniform(0.95, 1.03)
        Rb = min(Rb, hb)
        cy = -side * (hb - Rb)
        if not bigs:
            x = Rb + H * rng.uniform(0.04, 0.2)
        else:
            px, pcy, pR, ps = bigs[-1]
            x = px + pR + Rb + H * (rng.uniform(0.5, 0.75) if (k - 1) % 3 == 0 else rng.uniform(0.26, 0.4))
        if x + Rb > L - 0.3:
            break
        bigs.append((x, cy, Rb, side))
        side = -side
        k += 1
    if not bigs:
        R = min(hb, L / 2 - 0.3)
        sc = Scroll(L / 2, 0, R, 1, math.pi / 2, 1.35, 0.17)
        draw_scroll(cv, sc, rng)
        return [sc]
    slack = L - 0.3 - (bigs[-1][0] + bigs[-1][2])
    if slack > 0 and len(bigs) > 1:
        bigs = [(x + slack * (i / (len(bigs) - 1)) * 0.95, cy, R, s) for i, (x, cy, R, s) in enumerate(bigs)]
    elif slack > 0:
        bigs = [(x + slack / 2, cy, R, s) for x, cy, R, s in bigs]
    scrolls = []
    for x, cy, R, s in bigs:
        # top scroll (s=+1): starts at its bottom heading +x -> winds counter-clockwise on screen (dirn -1)
        if s > 0:
            sc = Scroll(x, cy, R, -1, math.pi / 2, rng.uniform(1.15, 1.32), rng.uniform(0.16, 0.22))
        else:
            sc = Scroll(x, cy, R, 1, -math.pi / 2, rng.uniform(1.15, 1.32), rng.uniform(0.16, 0.22))
        scrolls.append(sc)
    sw = max(1.2, min(2.4, H * 0.1))
    subs, fans, stems = [], [], []
    # lead-in from the lane start
    s0 = scrolls[0]
    p3 = s0.start()
    stems.append(((0.0, p3[1] * 0.5), (1.0, 0.0), p3, s0.tangent()))
    for i, (a, b) in enumerate(zip(scrolls, scrolls[1:])):
        stems.append((a.start(), a.tangent(), b.start(), b.tangent()))
    # tail-out past the last scroll
    sl = scrolls[-1]
    p0 = sl.start()
    if L - p0[0] > H * 0.25:
        stems.append((p0, sl.tangent(), (L, p0[1] * 0.4), (1.0, 0.0)))
    drawn = []
    for j, (p0, t0, p3, t3) in enumerate(stems):
        pts = _bez(p0, (p0[0] + t0[0] * 4, p0[1] + t0[1] * 4), (p3[0] - t3[0] * 4, p3[1] - t3[1] * 4), p3, 16)
        drawn.append(pts)
    # pockets between consecutive bigs
    for i, (a, b) in enumerate(zip(scrolls, scrolls[1:])):
        pts = drawn[i + 1]
        gx0, gx1 = a.cx + a.R, b.cx - b.R
        gap = gx1 - gx0
        if gap < 1.5:
            continue
        top_first = (i + (1 if rng.random() < 0.25 else 0)) % 2 == 0
        # the two pockets: near a on the side away from a's start, and near b on the side away from b's start
        pa = (gx0 + gap * 0.35, -math.copysign(hb * 0.55, a.start()[1] - a.cy))
        pb = (gx1 - gap * 0.35, -math.copysign(hb * 0.55, b.start()[1] - b.cy))
        for which, pc in ((0, pa), (1, pb)):
            if (which == 0) == top_first:
                rs = max(1.6, min(gap * 0.5, hb * 0.55) * rng.uniform(0.82, 0.98))
                cx = max(gx0 + rs * 0.6, min(gx1 - rs * 0.6, pc[0]))
                cy = math.copysign(hb - rs, pc[1])
                # branch point on the stem nearest that pocket
                bi = min(range(len(pts)), key=lambda q: math.hypot(pts[q][0] - cx, pts[q][1] - cy))
                bp = pts[bi]
                tdir = _norm(cx - bp[0], cy - bp[1])
                sc2 = _scroll_from((cx + (bp[0] - cx) * 0.0, cy), (0, 0), (cx, cy), rs, rng)
                # start of the sub scroll faces the stem
                a0 = math.atan2(bp[1] - cy, bp[0] - cx)
                d = -a.dirn if which == 0 else -b.dirn
                sc2 = Scroll(cx, cy, rs, d, a0, rng.uniform(1.2, 1.45), rng.uniform(0.16, 0.22))
                subs.append((bp, _norm(pts[min(bi + 1, len(pts) - 1)][0] - pts[max(bi - 1, 0)][0],
                                       pts[min(bi + 1, len(pts) - 1)][1] - pts[max(bi - 1, 0)][1]), sc2))
            else:
                bi = min(range(len(pts)), key=lambda q: math.hypot(pts[q][0] - pc[0], pts[q][1] - pc[1]))
                bp = pts[bi]
                ang = math.atan2(pc[1] - bp[1], pc[0] - bp[0])
                dist = math.hypot(pc[0] - bp[0], pc[1] - bp[1])
                fans.append((bp, ang, max(3.0, min(H * 0.95, dist * 2.6)), (which, i)))
    # draw: fans (behind), stems, sub scrolls, big scrolls; lobes fill what is left
    for bp, ang, ln, key in fans:
        sd = 1 if rng.random() < 0.5 else -1
        spn = _curve(bp, ang - sd * 0.5, ln, sd * 1.3, 14, sd * 0.6)
        spn = [(x, max(-hb + 0.6, min(hb - 0.6, y))) for x, y in spn]
        acanthus(cv, spn, max(2.2, ln * 0.3), -sd, rng, lobes=3 if ln > 8 else 2)
    anchors = []
    for p0, t0, p3, t3 in stems:
        sp_ = _stem(cv, p0, t0, p3, t3, sw)
        for q in range(1, len(sp_) - 1, 2):
            tx, ty = _norm(sp_[q + 1][0] - sp_[q - 1][0], sp_[q + 1][1] - sp_[q - 1][1])
            anchors.append((sp_[q][0], sp_[q][1], tx, ty))
    base = _base(cv)
    i_scroll = len(base.ops)
    for bp, tdir, sc2 in subs:
        p3 = sc2.start()
        t3 = sc2.tangent()
        dd = math.hypot(p3[0] - bp[0], p3[1] - bp[1])
        if tdir[0] * (p3[0] - bp[0]) + tdir[1] * (p3[1] - bp[1]) < 0:
            tdir = (-tdir[0], -tdir[1])
        if dd > 0.5:
            _stem(cv, bp, tdir, p3, t3, sw * 0.8, k=0.5)
        draw_scroll(cv, sc2, rng, bw=max(1.2, sw * 0.9))
    for sc in scrolls:
        # a fan where the stem meets the scroll, its lobes riding the outer turn
        if sc.R > 3.5:
            st = sc.start()
            t = sc.tangent()
            ang = math.atan2(-t[1], -t[0])
            side = -sc.dirn
            fan(cv, st, ang + side * 0.25, sc.R * 1.35, sc.R * 0.5, 3, side, rng, bend=1.0, spread=0.6, order="front")
        draw_scroll(cv, sc, rng)
    for sc in scrolls + [s_ for _, _, s_ in subs]:
        for f in (0.15, 0.3, 0.45, 0.6, 0.75):
            p = sc.point(f)
            t = sc.tangent_at(f)
            anchors.append((p[0], p[1], t[0], t[1]))
    i_fill = len(base.ops)
    _fill_gaps(cv, L, H, rng, scrolls + [s_ for _, _, s_ in subs], anchors)
    # the pocket leaves sit behind the scrolls, so every scroll keeps its crisp edge
    chunk = base.ops[i_fill:]
    del base.ops[i_fill:]
    base.ops[i_scroll:i_scroll] = chunk
    return scrolls


def _dt(occ):
    """Chamfer distance (in px) from every free cell to the nearest occupied cell or lane edge."""
    nx, ny, c = occ.nx, occ.ny, occ.c
    INF = 1e9
    d = [[0.0 if occ.g[j][i] or j in (0, ny - 1) else INF for i in range(nx)] for j in range(ny)]
    a, b = c, c * 1.4142
    for j in range(1, ny):
        row, up = d[j], d[j - 1]
        for i in range(nx):
            v = row[i]
            if v:
                v = min(v, up[i] + a, (up[i - 1] + b) if i else INF, (up[i + 1] + b) if i + 1 < nx else INF,
                        (row[i - 1] + a) if i else INF)
                row[i] = v
    for j in range(ny - 2, -1, -1):
        row, dn = d[j], d[j + 1]
        for i in range(nx - 1, -1, -1):
            v = row[i]
            if v:
                v = min(v, dn[i] + a, (dn[i - 1] + b) if i else INF, (dn[i + 1] + b) if i + 1 < nx else INF,
                        (row[i + 1] + a) if i + 1 < nx else INF)
                row[i] = v
    return d


def _fill_gaps(cv, L, H, rng, scrolls, anchors=()):
    """Grow leaves into the ground left between the scrolls: find the open pockets (a distance transform
    of what is drawn), and into each send an acanthus leaf from the nearest stem or scroll, sized to the
    pocket and sweeping with the flow, so the dark shows only as narrow channels between leaves."""
    occ = getattr(cv, "occ", None)
    if occ is None:
        return
    gmin = getattr(_base(cv), "gap_min", 1.4)
    d = _dt(occ)
    c = occ.c
    cells = []
    for j in range(occ.ny):
        for i in range(occ.nx):
            v = d[j][i]
            if gmin <= v < 1e8:
                cells.append((v, occ.x0 + (i + 0.5) * c, occ.y0 + (j + 0.5) * c))
    cells.sort(reverse=True)
    chosen = []
    for v, x, y in cells:
        if not (0.5 < x < L - 0.5):
            continue
        if any(math.hypot(x - X, y - Y) < (v + V) * 1.0 for V, X, Y in chosen):
            continue
        chosen.append((v, x, y))
    hb = H / 2 - 0.5
    for v, x, y in chosen:
        best = None
        for ax, ay, tx, ty in anchors:
            dd = math.hypot(ax - x, ay - y)
            if best is None or dd < best[0]:
                best = (dd, ax, ay, tx, ty)
        sd = rng.choice((-1, 1))
        if best and best[0] < v * 3.2 + 2:
            dd, ax, ay, tx, ty = best
            ang = math.atan2(y - ay, x - ax)
            # sweep with the stem: lean the leaf toward the stem's direction of travel
            flow = math.atan2(ty, tx)
            dl = (flow - ang + math.pi) % TAU - math.pi
            sd = 1 if dl > 0 else -1
            ln = dd + v * 1.8
            spn = _curve((ax, ay), ang - sd * 0.35, ln, sd * 1.0, 12, sd * 0.6)
        else:
            near = min(scrolls, key=lambda s_: math.hypot(s_.cx - x, s_.cy - y) - s_.R) if scrolls else None
            ang = (math.atan2(y - near.cy, x - near.cx) + near.dirn * math.pi / 2) if near else 0.0
            ln = v * 2.6
            spn = _curve((x - math.cos(ang) * ln * 0.5, y - math.sin(ang) * ln * 0.5), ang - sd * 0.3, ln, sd * 0.7, 10, sd * 0.5)
        spn = [(px, max(-hb, min(hb, py))) for px, py in spn]
        if v >= 2.6:
            acanthus(cv, spn, v * 2.1, -sd, rng, lobes=1 if v < 3.2 else 2 if v < 4.5 else 3)
        else:
            lobe(cv, spn, v * 2.25, shade=-sd)


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


def _ground_in_run(cv, run, u0, u1, v0, v1, rng, density=2.0):
    """Cut-away ground in a run: black, with a fine irregular stipple of 1-device-px pricks."""
    m = Mapped(cv, lambda x, y: run.p(x, y))
    m.poly("M", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    n = 0
    for _ in range(n):
        m.dot(rng.uniform(u0 + 0.3, u1 - 0.3), rng.uniform(v0 + 0.4, v1 - 0.4))


# ---------------------------------------------------------------- lanes (a band of scroll in local coords)

def _run_map(run, flip=False, u0=0.0):
    def f(x, y):
        u = u0 + x
        if flip:
            u = run.L - u
        return run.p(u, -y)
    return f


DENSITY = 2.3  # white pricks per CSS px^2 of visible ground (0.5 px pricks: a fine dark matte, ~60 % ink)


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
    if run.H < 6.5:
        density *= 1.5  # the wiry vine leaves more ground showing: open the matte up to hold the tone
    u1 = run.L if u1 is None else u1
    H = run.H
    L = u1 - u0
    f = _run_map(run, flip, u0)
    occ = Occ(-2, -H / 2, L + 2, H / 2, cell=0.5)
    m = Mapped(cv, f, occ)
    base = _base(cv)
    if ground is True:
        m.poly("M", [(0, -H / 2), (L, -H / 2), (L, H / 2), (0, H / 2)])
        occ.g = [bytearray(occ.nx) for _ in range(occ.ny)]
    out = lane(m, L, H, rng, start_side, **kw)
    return out


# ---------------------------------------------------------------- motifs

def fleuron(cv, x, y, s, up=(0, -1), rng=None):
    """Acanthus fleuron rising in direction `up`, base at (x, y), height s: a tall pointed central lobe over
    two compound acanthus leaves that rise and turn over outward, a pair of volutes curling out at the foot
    and a collar bud binding them."""
    rng = rng or random.Random(1)
    ux, uy = up
    rx, ry = -uy, ux
    au = math.atan2(uy, ux)

    def P(a, b):
        return (x + ux * a + rx * b, y + uy * a + ry * b)

    for sg in (-1, 1):  # calyx: two short lobes turning down and out at the foot
        lobe(cv, _curve(P(s * 0.08, sg * s * 0.04), au + sg * 1.9, s * 0.34, sg * 0.5, 8, sg * 0.4), s * 0.16, shade=-sg)
    for sg in (-1, 1):
        spn = _curve(P(s * 0.1, sg * s * 0.05), au + sg * 0.22, s * 0.7, sg * 1.25, 12, sg * 0.9)
        acanthus(cv, spn, s * 0.22, sg, rng, lobes=2)
    lobe(cv, _curve(P(s * 0.08, 0), au, s * 0.9, 0.0, 12), s * 0.3, shade=1)
    cv.line("C05", [P(s * (0.14 + 0.5 * t), 0) for t in (0, 0.5, 1)])
    bud(cv, *P(s * 0.06, 0), max(0.9, s * 0.07))


def shell(cv, x, y, s, up=(0, -1), rng=None):
    """Acanthus palmette (shell), hinge at (x, y), opening toward `up`, radius s: pointed lobes fanning
    out, the outer ones behind, each shaded on the side away from the centre line."""
    ux, uy = up
    au = math.atan2(uy, ux)
    n = 7 if s > 8 else 5
    order = sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2))
    for i in order:
        u = i / (n - 1) - 0.5
        a = au + u * 2.6
        b0 = (x + math.cos(a) * s * 0.12, y + math.sin(a) * s * 0.12)
        ln = s * (0.95 - 0.25 * abs(u) * 2)
        lobe(cv, _curve(b0, a, ln, -u * 0.6, 10, -u * 0.8), s * (0.42 - 0.12 * abs(u) * 2),
             shade=1 if u > 0 else -1)
    bud(cv, x, y, max(0.8, s * 0.14))


def rosette(cv, x, y, r, petals=8, rng=None):
    """Rosette boss: two rings of pointed acanthus petals, swirling, a pearl at the heart."""
    for k, (rr, w, off) in enumerate(((r, 0.62, 0.0), (r * 0.62, 0.5, 0.5))):
        for i in range(petals):
            a = TAU * (i + off) / petals + 0.2
            b0 = (x + math.cos(a) * r * 0.12, y + math.sin(a) * r * 0.12)
            lobe(cv, _curve(b0, a, rr * 0.9, 0.45, 8, 0.4), rr * w, shade=1)
    bud(cv, x, y, max(0.8, r * 0.22))


def inlay(cv, x, y, w, h, outer=True):
    """Crisp double inlay line round a field: 1 px rule, white channel, 0.5 px rule."""
    if outer:
        cv.add("R1", "M%s %sH%sV%sH%sZ" % (_f(x + 0.5), _f(y + 0.5), _f(x + w - 0.5), _f(y + h - 0.5), _f(x + 0.5)))
        cv.add("R05", "M%s %sH%sV%sH%sZ" % (_f(x + 2.25), _f(y + 2.25), _f(x + w - 2.25), _f(y + h - 2.25), _f(x + 2.25)))
    else:
        cv.add("R05", "M%s %sH%sV%sH%sZ" % (_f(x + 0.25), _f(y + 0.25), _f(x + w - 0.25), _f(y + h - 0.25), _f(x + 0.25)))
        cv.add("R1", "M%s %sH%sV%sH%sZ" % (_f(x + 2), _f(y + 2), _f(x + w - 2), _f(y + h - 2), _f(x + 2)))


def volute(cv, cx, cy, R, dirn, a0, rng, wmax=None, turns=None):
    """A free-standing scroll of footprint radius R, its stem joining at screen angle a0."""
    sc = Scroll(cx, cy, R, dirn, a0, turns or rng.uniform(1.3, 1.5), rng.uniform(0.14, 0.19))
    draw_scroll(cv, sc, rng)
    return sc


def _stipple_rect(cv, x0, y0, x1, y1, rng, density=2.0):
    return  # the matte pattern under the band does this now
    n = int(max(0.0, x1 - x0) * max(0.0, y1 - y0) * density)
    for _ in range(n):
        cv.dot(rng.uniform(x0 + 0.3, x1 - 0.3), rng.uniform(y0 + 0.3, y1 - 0.3))


def _rect_d(x0, y0, x1, y1):
    return "M%s %sH%sV%sH%sZ" % (_f(x0), _f(y0), _f(x1), _f(y1), _f(x0))


def corner(cv, x, y, s, quad, seed, rng=None):
    """Corner piece in the s x s square at (x, y): a dominant volute turning the corner with an acanthus
    fan springing from its foot toward the outer corner.  quad: 'tl', 'tr', 'br', 'bl'."""
    rng = rng or rng_for("corner", seed, quad)
    sx = 1 if quad in ("tl", "bl") else -1
    sy = 1 if quad in ("tl", "tr") else -1
    ox = x if sx > 0 else x + s
    oy = y if sy > 0 else y + s
    m = Mapped(cv, lambda a, b: (ox + sx * a, oy + sy * b))
    if s < 5:
        return
    fan(m, (s * 0.62, s * 0.62), math.radians(225), s * 0.62, s * 0.3, 3, 1, rng, bend=0.8, spread=0.7)
    sc = Scroll(s * 0.58, s * 0.58, s * 0.38, 1, math.radians(200), 1.4, 0.16)
    draw_scroll(m, sc, rng)


def _lane_rects(x, y, w, h, ins, o=1.5, i=2.0):
    t, r, b, l = ins
    return {
        "top": (x + l, y + o, x + w - r, y + t - i),
        "right": (x + w - r + i, y + t, x + w - o, y + h - b),
        "bottom": (x + l, y + h - b + i, x + w - r, y + h - o),
        "left": (x + o, y + t, x + l - i, y + h - b),
    }


def band_rect(cv, x, y, w, h, ins, seed, centre=("fleuron", None, "shell", None), corners=True,
              density=None, ends=None, slot=True, open_sides=(), lit=False, raised=False, motif_min=5.0):
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
        _band_with_ends(cv, x, y, w, h, ins, seed, centre, density, ends, lit=lit, motif_min=motif_min)
        return
    if open_sides and hasattr(cv, "clip"):
        cy0 = y + (t if "top" in open_sides else 0)
        cy1 = y + h - (b if "bottom" in open_sides else 0)
        cv.clip = _rect_d(x, cy0, x + w, cy1)
        _terminals(cv, x, y, w, h, ins, open_sides, seed)
    # ground and the outer rule as one black frame
    cv.add("M", _rect_d(x, y, x + w, y + h))
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
        _compose_side(cv, run, (seed, name), centre[k] if k < len(centre) else None, k, density=density,
                      motif_min=motif_min)
    # inlay: bright channels and rules
    top("R05", _rect_d(x + 0.25, y + 0.25, x + w - 0.25, y + h - 0.25))
    if o > 1:
        top("S1", _rect_d(x + 1, y + 1, x + w - 1, y + h - 1))
    top("S1", _rect_d(x + l - 1.5, y + t - 1.5, x + w - r + 1.5, y + h - b + 1.5))
    top("R05", _rect_d(x + l - 0.25, y + t - 0.25, x + w - r + 0.25, y + h - b + 0.25))
    if corners:
        for quad, (cx0, cy0, cx1, cy1) in (("tl", (x + o, y + o, x + l - i, y + t - i)),
                                           ("tr", (x + w - r + i, y + o, x + w - o, y + t - i)),
                                           ("br", (x + w - r + i, y + h - b + i, x + w - o, y + h - o)),
                                           ("bl", (x + o, y + h - b + i, x + l - i, y + h - o))):
            s = min(cx1 - cx0, cy1 - cy0)
            if s >= 3:
                corner(cv, cx0 + (cx1 - cx0 - s) / 2, cy0 + (cy1 - cy0 - s) / 2, s, quad, seed)


def _compose_side(cv, run, seed, motif, k, density=None, motif_min=5.0):
    rng = rng_for("side", seed)
    density = DENSITY if density is None else density
    L, H = run.L, run.H
    msz = H * 1.3 if motif and L > motif_min * H else 0
    if not msz:
        strip(cv, run, seed, 0, L, ground="dots", start_side=1 if k % 2 == 0 else -1, density=density)
        return
    half = (L - msz) / 2
    strip(cv, run, (seed, "a"), 0, half, flip=True, ground="dots", start_side=1, density=density)
    strip(cv, run, (seed, "b"), 0, half, flip=False, ground="dots", start_side=-1, density=density)
    m = Mapped(cv, lambda u, v: run.p(u, v))

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


def _terminals(cv, x, y, w, h, ins, open_sides, seed):
    """Where a panel runs on past the sheet edge: the side lanes end in small scrolled terminals."""
    t, r, b, l = ins
    rng = rng_for("term", seed)
    for side in open_sides:
        yy = y + t + 4.5 if side == "top" else y + h - b - 4.5
        for xx, lw, d in ((x + l / 2, l, 1), (x + w - r / 2, r, -1)):
            if lw >= 4:
                rr = lw * 0.42
                dirn = d if side == "top" else -d
                volute(cv, xx, yy, rr, dirn, -math.pi / 2 if side == "top" else math.pi / 2, rng, wmax=1.0)


def _band_with_ends(cv, x, y, w, h, ins, seed, centre, density, kind, lit=False, motif_min=5.0):
    """Plaque with shaped scrolled ends: top and bottom bands of scroll, and at each end a scrolled
    cartouche end whose outline leaves the rectangle (kind 'scroll': twin volutes meeting in a bud;
    'point': a pointed ogee end with one big volute; 'roll': a rolled ribbon end)."""
    t, r, b, l = ins
    rng = rng_for("ends", seed)
    o, i = (1.5 if min(t, b) >= 10 else 0.5), 2.0
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
            elif kind == "tail":
                xx = X + sg * e * 0.55 * (1 - d) ** 1.2
            else:  # scroll: concave notch between two lobes
                xx = X + sg * e * (0.05 + 0.55 * (1 - math.sin(math.pi * q) ** 2) * 0 + 0.45 * math.sin(math.pi * d) ** 1.2 * (1 - d * 0.3))
            pts.append((xx, yy))
        return pts
    Lp = end_outline(True)
    Rp = end_outline(False)
    outline = [(x + l, y)] + [(px, py) for px, py in Lp[::-1]][::-1][:0] + []
    outline = [(x + l, y), (x + w - r, y)] + Rp + [(x + w - r, y + h), (x + l, y + h)] + Lp[::-1]
    cv.poly("M", outline)
    cv.poly("C05", outline)
    if hasattr(cv, "clip") and cv.clip is None:
        cv.clip = "M" + _pts(outline) + "Z"
    # stipple, only inside the outline
    n = 0
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
            _compose_side(cv, Run(pts, H), (seed, name), centre[k] if k < len(centre) else None, k,
                          motif_min=motif_min)
    # the ends: volutes
    for left in (True, False):
        e = l if left else r
        sg = 1 if left else -1
        X = x if left else x + w
        Xin = x + l if left else x + w - r
        R = min(h * 0.25, e * 0.42)
        if kind == "point":
            volute(cv, X + sg * e * 0.55, y + h / 2, min(h * 0.3, e * 0.42), sg, math.pi / 2, rng)
            if lit:
                bud(cv, X + sg * e * 0.16, y + h / 2, 1.1)
        elif kind == "tail":
            for q, d in ((0.3, 1), (0.7, -1)):
                volute(cv, X + sg * e * 0.62, y + h * q, min(h * 0.24, e * 0.36), -d * sg, (math.pi if left else 0.0), rng)
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
    top = getattr(cv, "over", cv.add)
    top("W", _rect_d(x + l, y + t, x + w - r, y + h - b))
    top("S1", _rect_d(x + l - 1.5, y + t - 1.5, x + w - r + 1.5, y + h - b + 1.5))
    top("R05", _rect_d(x + l - 0.25, y + t - 0.25, x + w - r + 0.25, y + h - b + 0.25))
    if lit:
        top("R05", _rect_d(x + l - 2.75, y + t - 2.75, x + w - r + 2.75, y + h - b + 2.75))
    cv.line("S1", [(x + l * 0.6, y + 1), (x + w - r * 0.6, y + 1)])
    cv.line("S1", [(x + l * 0.6, y + h - 1), (x + w - r * 0.6, y + h - 1)])


def ring(cv, cx, cy, rx, ry, band, seed, density=2.0):
    """An oval ring of scroll (centreline ellipse rx, ry), for a cartouche round a scene."""
    n = 240
    pts = [(cx + rx * math.cos(-math.pi / 2 + TAU * i / n), cy + ry * math.sin(-math.pi / 2 + TAU * i / n)) for i in range(n + 1)]
    run = Run(pts, band)
    rng = rng_for("ring", seed)
    outer = [run.p(run.L * i / n, band / 2) for i in range(n + 1)]
    inner_ = [run.p(run.L * i / n, -band / 2) for i in range(n + 1)]
    cv.add("M", "M" + _pts(outer) + "ZM" + _pts(inner_[::-1]) + "Z")
    inner = Run(pts, band - 5.5)
    strip(cv, inner, (seed, "ring-a"), 0, run.L / 2, flip=True, ground="dots", density=density)
    strip(cv, inner, (seed, "ring-b"), 0, run.L / 2, ground="dots", start_side=-1, density=density)
    for off, key in ((band / 2 - 0.5, "C1"), (band / 2 - 2.0, "S1"), (-band / 2 + 2.0, "S1"), (-band / 2 + 0.5, "C1")):
        cv.poly(key, [run.p(run.L * i / 240, off) for i in range(241)], close=False)


def fill_rect(cv, x, y, w, h, seed, row=None, density=2.0):
    """Fill a whole rectangle with rows of fine scroll (for grounds). Rows interlock by alternating flow."""
    row = row or min(h, 22.0)
    n = max(1, int(round(h / row)))
    rh = h / n
    for i in range(n):
        yy = y + rh * (i + 0.5)
        run = Run([(x, yy), (x + w, yy)], rh)
        strip(cv, run, (seed, "row", i), flip=bool(i % 2), start_side=1 if i % 2 else -1, density=density)
    return cv


# ---------------------------------------------------------------- plaques with scrolled ears (small frames)

def _ear_outline(kind, e, h, n=28):
    """Outline of one ear in local coords: u from 0 (the slot side) to e (the tip), v in [-h/2, h/2]."""
    pts = []
    for j in range(n + 1):
        q = j / n
        v = -h / 2 + h * q
        d = abs(q - 0.5) * 2  # 1 at top and bottom, 0 at the middle
        if kind == "point":      # ogee point
            u = e * (1.0 - 0.78 * d ** 1.35)
        elif kind == "tail":     # swallow-tail: notched in the middle
            u = e * (0.55 + 0.45 * d ** 0.7)
        elif kind == "scroll":   # twin lobes with a waist
            u = e * (0.72 + 0.28 * math.sin(math.pi * d) ** 0.8 - 0.25 * d ** 6)
        elif kind == "round":    # half round cap
            u = e * math.sqrt(max(0.0, 1 - d * d)) * 0.95 + e * 0.05
        else:                    # 'roll': rounded tab with a shallow notch
            u = e * (0.86 + 0.14 * math.cos(q * TAU * 2) * 0.4 - 0.5 * d ** 4)
        pts.append((max(0.0, u), v))
    return [(0.0, h / 2)] + pts[::-1] + [(0.0, -h / 2)]


def ear(cv, e, h, rng, kind="roll", lit=False):
    """Compose the scroll cluster in one ear (local coords, u outward from the slot, v down): a dominant
    volute, a subordinate scroll 2-3x smaller winding against it, an acanthus leaf springing from the
    volute's foot back toward the slot, and leaves grown into what ground is left."""
    hb = h / 2
    occ = Occ(-1, -hb, e + 1, hb, cell=0.5)
    m = Mapped(cv.cv, cv.f, occ) if isinstance(cv, Mapped) else Mapped(cv, lambda u, v: (u, v), occ)
    outline = _ear_outline(kind, e, h)
    # cells outside the ear count as occupied so leaves stay inside
    for j in range(occ.ny):
        y = occ.y0 + (j + 0.5) * occ.c
        for i in range(occ.nx):
            x = occ.x0 + (i + 0.5) * occ.c
            if not _inside(outline, x, y, 0.9):
                occ.g[j][i] = 1
    anchors = []
    scrolls = []
    # a tall ear (the banner's tails) carries two clusters, mirrored; a short one carries one
    if h > 2.1 * e:
        halves = [(-h / 4, h / 4, 1), (h / 4, h / 4, -1)]
    else:
        halves = [(0.0, hb, rng.choice((-1, 1)))]
    for v0, hh, up in halves:
        R = min(e * 0.4, hh * 0.82)
        cu = e * (0.48 if len(halves) == 1 else 0.56)
        cv_ = v0 + up * min(hh * 0.12, max(0.0, hh - R - 0.6))
        big = Scroll(cu, cv_, R, 1 if up > 0 else -1, math.atan2(hh, -e) if up > 0 else math.atan2(-hh, -e),
                     rng.uniform(1.15, 1.3), 0.18)
        r2 = R * rng.uniform(0.38, 0.48)
        su, sv = min(e - r2 - 0.8, cu + R * 0.55), v0 - up * (hh - r2 - 0.8)
        small = Scroll(su, sv, r2, -big.dirn, math.atan2(cv_ - sv, cu - su), rng.uniform(1.1, 1.3), 0.22)
        p3, t3 = big.start(), big.tangent()
        sp = _stem(m, (0.0, v0 - up * hh * 0.25), (1.0, up * 0.3), p3, t3, max(1.2, R * 0.28))
        for q in range(1, len(sp) - 1):
            tx, ty = _norm(sp[q + 1][0] - sp[q - 1][0], sp[q + 1][1] - sp[q - 1][1])
            anchors.append((sp[q][0], sp[q][1], tx, ty))
        bi = len(sp) // 2
        _stem(m, sp[bi], _norm(sp[bi + 1][0] - sp[bi - 1][0], sp[bi + 1][1] - sp[bi - 1][1]), small.start(),
              small.tangent(), max(1.0, r2 * 0.4), k=0.5)
        if hh * 2 >= 14:
            acanthus(m, _curve(sp[1], math.atan2(up * 1.0, 0.3), min(hh * 0.9, e * 0.9), -up * 1.6, 12, -up * 0.5),
                     max(2.2, R * 0.55), up, rng, lobes=2)
        scrolls += [small, big]
    base = _base(cv)
    i0 = len(base.ops)
    for sc in scrolls:
        draw_scroll(m, sc, rng)
    for sc in scrolls:
        for f in (0.1, 0.3, 0.5, 0.7):
            p = sc.point(f)
            t = sc.tangent_at(f)
            anchors.append((p[0], p[1], t[0], t[1]))
    i1 = len(base.ops)
    _fill_gaps(m, e, h, rng, scrolls, anchors)
    chunk = base.ops[i1:]
    del base.ops[i1:]
    base.ops[i0:i0] = chunk
    if lit:
        bud(m, e * 0.9, 0.0, 1.2)
    return outline


def plaque(cv, x, y, w, h, ears, t, seed, kind="roll", lit=False, centre=None):
    """A small frame whose scroll lives in its ears: left and right ears of width ears = (el, er) hold the
    composed scroll clusters; the long edges are crisp double inlay lines of width t (no thin scroll band).
    The slot between is white.  Outside the outline stays transparent."""
    el, er = ears
    kl, kr = (kind, kind) if isinstance(kind, str) else kind
    rng = rng_for("plaque", seed)
    # outline of the whole plaque, clockwise from top-left of the body
    L = [(x + el - u, y + h / 2 + v) for u, v in _ear_outline(kl, el, h)]
    Rr = [(x + w - er + u, y + h / 2 + v) for u, v in _ear_outline(kr, er, h)]
    outline = [(x + el, y), (x + w - er, y)] + Rr[::-1] + [(x + w - er, y + h), (x + el, y + h)] + L
    # Rr runs from (0, +h/2) to (0, -h/2) in local order: reversed gives top to bottom on the right
    if hasattr(cv, "clip") and cv.clip is None:
        cv.clip = "M" + _pts(outline) + "Z"
    cv.poly("M", outline)
    for side, e, kind in ((-1, el, kl), (1, er, kr)):
        X = x + el if side < 0 else x + w - er
        f = (lambda u, v, X=X, s=side: (X + s * u, y + h / 2 + v))
        ear(Mapped(cv, f), e, h, rng_for("ear", seed, side), kind=kind, lit=lit)
    top = getattr(cv, "over", cv.add)
    cv.slot = (x + el, y + t, w - el - er, h - 2 * t)
    if t >= 10:
        # a wide plaque (the banner): head and foot carry true scroll lanes between the ears
        o, i_ = 1.5, 2.0
        for k, name in ((0, "top"), (2, "bottom")):
            if name == "top":
                y0, y1 = y + o, y + t - i_
                pts = [(x + el, (y0 + y1) / 2), (x + w - er, (y0 + y1) / 2)]
            else:
                y0, y1 = y + h - t + i_, y + h - o
                pts = [(x + w - er, (y0 + y1) / 2), (x + el, (y0 + y1) / 2)]
            _compose_side(cv, Run(pts, y1 - y0), (seed, name), (centre or (None,) * 4)[k], k, motif_min=6)
        top("W", _rect_d(x + el, y + t, x + w - er, y + h - t))
        top("R05", "M%s %sH%s" % (_f(x + el), _f(y + t - i_ + 0.25), _f(x + w - er)) +
            "M%s %sH%s" % (_f(x + el), _f(y + h - t + i_ - 0.25), _f(x + w - er)))
    else:
        # long edges: no thin scroll, just a double inlay (black edge, white fillet, black slot rule)
        top("W", _rect_d(x + el, y, x + w - er, y + h))
    top("C1", "M" + _pts(_inset(outline, 0.5)) + "Z")
    top("S1", "M" + _pts(_inset(outline, 1.75)) + "Z")
    top("S1", _rect_d(x + el - 1.5, y + t - 1.5, x + w - er + 1.5, y + h - t + 1.5))
    top("R05", _rect_d(x + el - 0.25, y + t - 0.25, x + w - er + 0.25, y + h - t + 0.25))
    if lit:
        top("R05", _rect_d(x + el - 2.75, y + t - 2.75, x + w - er + 2.75, y + h - t + 2.75))
    return outline


def _inset(poly, d):
    """Offset a closed polygon inward by d (simple vertex-normal offset; fine for these smooth outlines)."""
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    out = []
    for i in range(n):
        ax, ay = poly[i - 1]
        bx, by = poly[i]
        cx, cy = poly[(i + 1) % n]
        t1 = _norm(bx - ax, by - ay)
        t2 = _norm(cx - bx, cy - by)
        nx, ny = -(t1[1] + t2[1]), t1[0] + t2[0]
        nx, ny = _norm(nx, ny)
        out.append((bx + sgn * nx * d, by + sgn * ny * d))
    return out


# ---------------------------------------------------------------- vise-scale scroll field

class Mirror(Mapped):
    """Draw everything twice, the second copy mirrored about x = w/2 (a field whose holes are symmetric),
    as an engraver lays out a ground: compose one half, reverse it for the other."""

    def __init__(self, cv, w, occ):
        Mapped.__init__(self, cv, lambda x, y: (x, y), occ)
        self.w = w

    def poly(self, key, pts, close=True):
        Mapped.poly(self, key, pts, close)
        self.cv.poly(key, [(self.w - x, y) for x, y in pts], close)

    def circle(self, key, x, y, r):
        Mapped.circle(self, key, x, y, r)
        self.cv.circle(key, self.w - x, y, r)


def _mark_rect(occ, x0, y0, x1, y1):
    c = occ.c
    i0, i1 = max(0, int((x0 - occ.x0) / c)), min(occ.nx - 1, int((x1 - occ.x0) / c))
    j0, j1 = max(0, int((y0 - occ.y0) / c)), min(occ.ny - 1, int((y1 - occ.y0) / c))
    if i1 < i0:
        return
    for j in range(j0, j1 + 1):
        occ.g[j][i0:i1 + 1] = b"\x01" * (i1 - i0 + 1)


def _cell(occ, x, y):
    i, j = int((x - occ.x0) / occ.c), int((y - occ.y0) / occ.c)
    if 0 <= i < occ.nx and 0 <= j < occ.ny:
        return occ.g[j][i]
    return 1


class _Grid:
    """Bucket grid for near-neighbour queries."""

    def __init__(self, s=16.0):
        self.s, self.b = s, {}

    def add(self, x, y, item):
        self.b.setdefault((int(x // self.s), int(y // self.s)), []).append(item)

    def near(self, x, y, r):
        k = int(r // self.s) + 1
        bx, by = int(x // self.s), int(y // self.s)
        for i in range(bx - k, bx + k + 1):
            for j in range(by - k, by + k + 1):
                for it in self.b.get((i, j), ()):
                    yield it


def _taper_stem(cv, p0, t0, p3, t3, w0, w1, k=0.42):
    d = math.hypot(p3[0] - p0[0], p3[1] - p0[1]) * k
    pts = _bez(p0, (p0[0] + t0[0] * d, p0[1] + t0[1] * d), (p3[0] - t3[0] * d, p3[1] - t3[1] * d), p3, 20)
    pts = _resample(pts, 1.2)
    n = len(pts)
    if n < 2:
        return pts
    poly, _, _ = _ribbon(pts, [(w0 + (w1 - w0) * i / (n - 1)) / 2 for i in range(n)])
    cv.poly("W", poly)
    if getattr(_base(cv), "model", False) and min(w0, w1) >= 1.4:
        inner, _, _ = _ribbon(pts, [max(0.2, (w0 + (w1 - w0) * i / (n - 1)) / 2 - 0.45) for i in range(n)])
        cv.poly("G0", inner)
    # a groove cut down one flank of a broad stem
    if min(w0, w1) >= 2.2 and n > 4:
        nm = _normals(pts)
        g = []
        for i in range(1, n - 1):
            o = (w0 + (w1 - w0) * i / (n - 1)) / 2 - 0.7
            g.append((pts[i][0] + nm[i][0] * o, pts[i][1] + nm[i][1] * o))
        cv.line("C05", g)
    return pts


def _field_fill(dc, occ, rng, anchors, gmin, wcap, spread=1.0):
    """Grow acanthus into every open pocket of ground of clearance >= gmin (a distance transform of what is
    drawn), each leaf springing from the nearest stem or scroll and sweeping with its flow."""
    d = _dt(occ)
    c = occ.c
    cells = []
    for j in range(occ.ny):
        row = d[j]
        for i in range(occ.nx):
            v = row[i]
            if gmin <= v < 1e8:
                cells.append((v + rng.random() * 0.3, (i + 0.5) * c + occ.x0, (j + 0.5) * c + occ.y0))
    cells.sort(reverse=True)
    chosen, cg = [], _Grid(12.0)
    vmax = cells[0][0] if cells else 0
    for v, x, y in cells:
        if any(math.hypot(x - X, y - Y) < (v + V) * spread for V, X, Y in cg.near(x, y, (v + vmax) * spread)):
            continue
        cg.add(x, y, (v, x, y))
        chosen.append((v, x, y))
    ag = _Grid(16.0)
    for a in anchors:
        ag.add(a[0], a[1], a)
    for v, x, y in chosen:
        best = None
        for ax, ay, tx, ty in ag.near(x, y, v * 3.2 + 2):
            dd = math.hypot(ax - x, ay - y)
            if best is None or dd < best[0]:
                best = (dd, ax, ay, tx, ty)
        sd = rng.choice((-1, 1))
        if best and best[0] < v * 3.2 + 2:
            dd, ax, ay, tx, ty = best
            ang = math.atan2(y - ay, x - ax)
            dl = (math.atan2(ty, tx) - ang + math.pi) % TAU - math.pi
            sd = 1 if dl > 0 else -1
            spn = _curve((ax, ay), ang - sd * 0.4, dd + v * 2.2, sd * 1.2, 14, sd * 0.7)
        else:
            ang = rng.uniform(0, TAU)
            ln = v * 2.6
            spn = _curve((x - math.cos(ang) * ln * 0.5, y - math.sin(ang) * ln * 0.5), ang - sd * 0.3, ln, sd * 0.7, 10,
                         sd * 0.5)
        if v >= 2.6:
            a = math.atan2(spn[1][1] - spn[0][1], spn[1][0] - spn[0][0])
            hand_leaf(dc, spn[0], a, _arclen(spn)[-1] + v * 1.2, min(v * 3.0, wcap), -sd, rng)
        else:
            sp = _fit(dc, lambda f: spn, v * 2.25)
            if len(sp) >= 3:
                lobe(dc, sp, min(v * 2.25, wcap), shade=-sd)
    return len(chosen)


def _to_sheet(cv, x, y):
    while isinstance(cv, Mapped):
        x, y = cv.f(x, y)
        cv = cv.cv
    return x, y


def _fit(cv, make, width):
    """Build a leaf spine with make(flip); if it would run out of the field (into the sheet border or a
    panel), try it turned back the other way, else stop it short, so leaves end inside the field."""
    b = getattr(_base(cv), "bound", None)
    sp = make(False)
    if b is None:
        return sp
    best = None
    for flip in (False, True):
        sp = make(flip)
        n = len(sp)
        stop = n
        for i, (x, y) in enumerate(sp):
            if i and b(*_to_sheet(cv, x, y)) < width * 0.22 * (1 - 0.6 * i / max(1, n - 1)) + 0.3:
                stop = i
                break
        if best is None or stop > best[0]:
            best = (stop, sp)
        if stop == n:
            break
    stop, sp = best
    return sp if stop == len(sp) else sp[:stop]


def hand_leaf(cv, base, ang, length, width, curl, rng, fingers=None):
    """A deeply lobed acanthus leaf fanned like a hand: a palm and 3-5 long pointed finger lobes splaying a
    little from it and all sweeping over toward `curl` (+1 / -1), each with a serrated outline and its own
    midrib cut; the outer fingers lie behind, the middle one on top."""
    n = fingers or (3 if width < 7 else 4 if width < 11 else 5)
    palm = _fit(cv, lambda f: _curve(base, ang, length * 0.34, (-1 if f else 1) * curl * 0.2, 8), width * 0.7)
    if len(palm) < 3:
        return
    s = _arclen(palm)
    items = []
    for k in range(n):
        u = k / (n - 1) - 0.5
        (rx, ry), (tx, ty) = _at(palm, s, 0.45 + 0.5 * (1 - 2 * abs(u)))
        a = math.atan2(ty, tx) + u * 0.8 * rng.uniform(0.9, 1.1)
        ln = length * (0.86 - 0.42 * abs(u)) * rng.uniform(0.92, 1.06)
        bend = curl * 0.75 + u * 0.35
        wd = width * (0.52 - 0.16 * abs(u))
        items.append((abs(u), (rx, ry), a, ln, bend, wd, 1 if u > 0 else -1))
    out = []
    for _, root, a, ln, bend, wd, sh in sorted(items, key=lambda it: -it[0]):
        sp = _fit(cv, lambda f, root=root, a=a, ln=ln, bend=bend: _curve(root, a, ln, -bend if f else bend, 12,
                                                                          (-curl if f else curl) * 0.6), wd)
        if len(sp) >= 5:
            out.append((sp, wd, sh))
    if len(out) < 2:
        if out:
            lobe(cv, out[0][0], out[0][1], shade=out[0][2], teeth=3 if out[0][1] >= 3.5 else 0, rib=True)
        return
    lobe(cv, palm, width * 0.6, shade=curl, cuts=False)
    for sp, wd, sh in out:
        lobe(cv, sp, wd, shade=sh, teeth=3 if wd >= 3.5 else 0, rib=True)


def running_scroll(cv, run, rng):
    """A single running scroll for a narrow run: one wave stem from end to end; at every turn a volute
    branches off into the hollow beneath the crest, and a hand leaf springs from the crest and sweeps on
    along the outside.  Successive volutes alternate side and winding."""
    L, H = run.L, run.H
    m = Mapped(cv, lambda u, v: run.p(u, v))
    hb = H / 2 - 0.3
    n = max(1, int(round(L / (H * 2.3))))
    lam = L / n
    A = H * 0.15

    def wv(u):
        return A * math.sin(TAU * u / lam)

    def wt(u):
        return _norm(1.0, A * TAU / lam * math.cos(TAU * u / lam))

    turns = [(lam / 4 + k * lam / 2, 1 if k % 2 == 0 else -1) for k in range(2 * n)]
    R = min((hb + A) * 0.47, lam * 0.21)
    parts = []
    for uc, sd in turns:
        cx, cy = uc + lam * 0.09, -sd * (hb - R - 0.2)
        bu = uc - lam * 0.05
        bp, t0 = (bu, wv(bu)), wt(bu)
        a0 = math.atan2(bp[1] - cy, bp[0] - cx)
        best = None
        for dn in (1, -1):
            sc = Scroll(cx, cy, R * rng.uniform(0.92, 1.04), dn, a0, rng.uniform(1.25, 1.4), 0.18)
            tx, ty = sc.tangent()
            v = tx * t0[0] + ty * t0[1]
            if best is None or v > best[0]:
                best = (v, sc)
        parts.append((uc, sd, bp, t0, best[1]))
    # leaves behind: from each crest, sweeping on along the outside of the wave
    for uc, sd, bp, t0, sc in parts:
        lu = uc + lam * 0.03
        lp = (lu, wv(lu))
        hand_leaf(m, lp, math.atan2(sd * 0.45, 1.0), lam * 0.46, min(hb - A + 2.0, lam * 0.24) * 1.15, -sd, rng,
                  fingers=3)
    ww = max(1.4, min(3.0, H * 0.1))
    pts = [(u, wv(u)) for u in [L * i / max(8, int(L)) for i in range(max(8, int(L)) + 1)]]
    poly, _, _ = _ribbon(pts, [ww / 2] * len(pts))
    m.poly("W", poly)
    if ww >= 1.8:
        m.poly("G0", _ribbon(pts, [ww / 2 - 0.55] * len(pts))[0])
    m.line("C05", [(x, y + ww / 2 - 0.6) for x, y in pts])
    for uc, sd, bp, t0, sc in parts:
        _taper_stem(m, bp, t0, sc.start(), sc.tangent(), ww, max(1.3, sc.R * 0.28))
        draw_scroll(m, sc, rng, bw=max(1.5, sc.R * 0.32), inner_w=sc.R * 0.6)


def spray(cv, S, rng, f0=0.0, f1=0.42, n=None):
    """A long serrated acanthus spray along the outer curve of scroll S: overlapping pointed leaves springing
    from the backbone one after another, each leaning out and sweeping on round the scroll with it, tips
    turned out, so the outer edge reads as a serrated leaf following the curve."""
    R = S.R
    n = n or max(2, min(4, int(R / 5)))
    leaves = []
    for k in range(n):
        u = k / max(1, n - 1)
        f = f0 + (f1 - f0) * u
        bx, by = S.point(f, rscale=1.04)
        tx, ty = S.tangent_at(f)
        ox, oy = -S.dirn * -ty, -S.dirn * tx  # outward normal
        lean = 0.55 - 0.15 * u
        ang = math.atan2(ty + lean * oy, tx + lean * ox)
        ln = R * (1.05 - 0.45 * u) * rng.uniform(0.9, 1.08)
        turn = S.dirn * ln / (R * 1.35)
        wd = R * (0.36 - 0.1 * u) * rng.uniform(0.92, 1.06)
        leaves.append((_curve((bx, by), ang, ln, turn, 12, -S.dirn * 0.55), wd))
    for spn, wd in leaves[::-1]:
        a = math.atan2(spn[1][1] - spn[0][1], spn[1][0] - spn[0][0])
        ln = _arclen(spn)[-1]
        hand_leaf(cv, spn[0], a, ln, wd * 1.5, S.dirn, rng, fingers=3 if wd < 5 else 4)


def _draw_motif(cv, motif, x, y, s, rng):
    if callable(motif):
        motif(cv, x, y, s)
    elif motif == "shell":
        shell(cv, x, y + s * 0.42, s * 0.55)
    elif motif == "rosette":
        rosette(cv, x, y, s * 0.46)
    else:
        fleuron(cv, x, y + s * 0.5, s, rng=rng)


def compose_field(cv, w, h, holes, seed, motif="fleuron", border=True, scale=1.0, punch=0.4):
    """Fill the ground of a whole sheet w x h with vise-scale scroll, laid around the rectangular `holes`
    (x, y, w, h: panel windows, left transparent).  Dominant C-scrolls with volutes 26-50 px across where the
    ground is wide, subordinate scrolls 2-3x smaller tucked between, every scroll joined to a neighbour by a
    tapering stem and wrapped in acanthus, a motif at the centre of each run that crosses the centre line,
    the rest grown over with acanthus; the cut ground is near-solid black punched with fine white dots
    generated for this field (no tile).  Symmetric holes give a mirror-symmetric composition."""
    rng = rng_for("field", seed)
    C = 1.0
    pad = 1.5
    occ = Occ(0, 0, w, h, C)
    m = 3.5 if border else 1.0
    for r in ((0, 0, w, m), (0, h - m, w, h), (0, 0, m, h), (w - m, 0, w, h)):
        _mark_rect(occ, *r)
    for x, y, hw, hh in holes:
        _mark_rect(occ, x - pad, y - pad, x + hw + pad, y + hh + pad)
    sym = all(any(abs((w - x - hw) - x2) < 1.5 and abs(y - y2) < 1.5 and abs(hw - hw2) < 1.5 and abs(hh - hh2) < 1.5
                  for x2, y2, hw2, hh2 in holes) for x, y, hw, hh in holes)
    cv.add("K", _rect_d(0, 0, w, h))
    cv.clip = _rect_d(0, 0, w, h) + "".join(_rect_d(x, y, x + hw, y + hh) for x, y, hw, hh in holes)
    if getattr(cv, "model", False) or True:
        dB = _dt(occ)

        def bound(x, y, dB=dB, occ=occ):
            i, j = int((x - occ.x0) / occ.c), int((y - occ.y0) / occ.c)
            if 0 <= i < occ.nx and 0 <= j < occ.ny:
                v = dB[j][i]
                return v if v < 1e8 else 0.0
            return 0.0
        cv.bound = bound
    # narrow gaps between two panels carry a single running scroll, composed out from a centre motif
    gaps = []
    for ax, ay, aw, ah in holes:
        for bx, by, bw_, bh in holes:
            o0, o1 = max(ax, bx), min(ax + aw, bx + bw_)
            g0, g1 = ay + ah, by
            if o1 - o0 > 40 and 8 <= g1 - g0 <= 34:
                gaps.append((o0, g0, o1, g1, "h"))
            o0, o1 = max(ay, by), min(ay + ah, by + bh)
            g0, g1 = ax + aw, bx
            if o1 - o0 > 40 and 8 <= g1 - g0 <= 34:
                gaps.append((g0, o0, g1, o1, "v"))
    for k, (x0, y0, x1, y1, d) in enumerate(gaps):
        if any(hx < x1 and hx + hw > x0 and hy < y1 and hy + hh > y0 for hx, hy, hw, hh in holes):
            continue
        if d == "h":
            H = (y1 - y0) - 2 * pad - 1.0
            run = Run([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], H)
        else:
            H = (x1 - x0) - 2 * pad - 1.0
            run = Run([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], H)
        running_scroll(cv, run, rng_for("gap", seed, k))
        _mark_rect(occ, x0, y0, x1, y1)
    plain = Mapped(cv, lambda x, y: (x, y), occ)
    dc = Mirror(cv, w, occ) if sym else plain
    anchors, roots = [], []
    i_back = len(_base(cv).ops)  # pocket leaves go in behind everything from here on
    # motifs: at the centre of every run that crosses the centre line (top, gaps, foot) ...
    ic = int(w / 2 / C)
    runs, j = [], 0
    while j < occ.ny:
        if not occ.g[j][ic]:
            j0 = j
            while j < occ.ny and not occ.g[j][ic]:
                j += 1
            runs.append((j0 * C, j * C))
        else:
            j += 1
    big = max(runs, key=lambda r: r[1] - r[0]) if runs else None
    for y0, y1 in runs:
        L = y1 - y0
        if L < 16:
            continue
        s = min(L * 0.8, 62 * scale)
        cy = (y0 + y1) / 2
        _draw_motif(plain, motif if (y0, y1) == big else ("shell" if L < 40 else "rosette"), w / 2, cy, s, rng)
        for sg in (-1, 1):
            roots.append((w / 2 + sg * s * 0.4, cy + s * 0.2, sg, 0.0))
    # ... and of each side run (the side frames), mirrored when the field is
    jc = int(h / 2 / C)
    i = 0
    while i < occ.nx / 2:
        if not occ.g[jc][i]:
            i0 = i
            while i < occ.nx and not occ.g[jc][i]:
                i += 1
            L = (i - i0) * C
            if 16 <= L < w / 3:
                s = min(L * 0.8, 50 * scale)
                cx = (i0 * C + i * C) / 2
                _draw_motif(dc, "rosette", cx, h / 2, s, rng)
                for sg in (-1, 1):
                    roots.append((cx, h / 2 + sg * s * 0.42, 0.0, sg))
        else:
            i += 1
    if sym:
        _mark_rect(occ, w / 2 - 0.5, 0, w, h)
        roots = [r for r in roots if r[0] < w / 2 + 0.01 and not (abs(r[0] - w / 2) < 0.1)]
        roots = [r for r in roots if r[0] <= w / 2]
    mask = [bytearray(r) for r in occ.g]
    d0 = _dt(occ)
    # scrolls: dominant, then subordinate, then small, each only where the ground has room
    scrolls = []
    sg_ = _Grid(24.0)

    def place(rmin, rmax, step, gap, extra=0.0):
        cand = []
        for j in range(0, occ.ny, step):
            row = d0[j]
            for i in range(0, occ.nx, step):
                v = row[i]
                if rmin * 0.8 + gap <= v < 1e8:
                    cand.append((v + rng.random() * 2.0, (i + 0.5) * C, (j + 0.5) * C, v))
        cand.sort(reverse=True)
        for _, x, y, v in cand:
            R = min(v - gap, rng.uniform(rmin, rmax)) * (0.66 if rng.random() < 0.45 else 1.0)
            if R < rmin * 0.62:
                continue
            ok = True
            for S in sg_.near(x, y, R + 30 * scale):
                if math.hypot(S.cx - x, S.cy - y) < R + S.R + max(3.0, 0.5 * min(R, S.R)) + extra:
                    ok = False
                    break
            if ok:
                S = Scroll(x, y, R, 1, 0.0)
                scrolls.append(S)
                sg_.add(x, y, S)

    place(14 * scale, 24 * scale, 3, 3.0)
    place(6.5 * scale, 11 * scale, 2, 2.0, extra=7.0 * scale)
    # join them: largest first, each to the nearest open attach point (motif flank, scroll turn, stem)
    att = _Grid(24.0)
    for r in roots:
        att.add(r[0], r[1], (r[0], r[1], r[2], r[3], None, 2.6))

    def clear(p, q, own, tgt):
        n = int(math.hypot(q[0] - p[0], q[1] - p[1]) / 1.5) + 1
        for k in range(1, n):
            x, y = p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n
            if _cell_m(mask, occ, x, y):
                return False
            for S in sg_.near(x, y, 30 * scale):
                if S is not own and S is not tgt and math.hypot(S.cx - x, S.cy - y) < S.R * 0.95:
                    return False
        return True

    order = sorted(scrolls, key=lambda S: -S.R)
    stems = []
    tails, used, keep = set(), set(), []
    for S in order:
        best = None
        for it in att.near(S.cx, S.cy, S.R * 3 + 40 * scale):
            ax, ay, tx, ty, own, wd = it
            dd = math.hypot(S.cx - ax, S.cy - ay) - S.R
            if dd < 1.0 or dd > S.R * 3 + 30 * scale:
                continue
            tail = id(it) in tails
            if tail and id(it) in used:
                continue
            sc_ = dd * (0.5 if tail else 1.0)
            if best is None or sc_ < best[0]:
                if clear((ax, ay), (S.cx, S.cy), own, S):
                    best = (sc_, ax, ay, tx, ty, own, wd, it)
        if best:
            _, ax, ay, tx, ty, own, wd, it = best
            used.add(id(it))
            a0 = math.atan2(ay - S.cy, ax - S.cx)
            tdir = _norm(S.cx - ax, S.cy - ay)
            opts = []
            for dn in (1, -1):
                T = Scroll(S.cx, S.cy, S.R, dn, a0, rng.uniform(1.2, 1.4), rng.uniform(0.15, 0.2))
                t = T.tangent()
                sc_ = t[0] * tdir[0] + t[1] * tdir[1] + (0.6 if own is not None and dn != own.dirn else 0.0)
                opts.append((sc_, dn, T))
            T = max(opts, key=lambda o: o[0])[2]
            S.dirn, S.a0, S.turns, S.eye = T.dirn, T.a0, T.turns, T.eye
            t0 = (tx, ty) if tx * tdir[0] + ty * tdir[1] >= 0 else (-tx, -ty)
            stems.append(((ax, ay), t0, S, wd))
        else:
            S.dirn, S.a0 = rng.choice((-1, 1)), rng.uniform(0, TAU)
            S.turns, S.eye = rng.uniform(1.2, 1.4), rng.uniform(0.15, 0.2)
        # the scroll's own tail: a stem leaving here carries the backbone on, full width, into the next volute
        p = S.point(0.0)
        t = S.tangent_at(0.0)
        it = (p[0], p[1], -t[0], -t[1], S, max(1.5, min(4.6, S.R * 0.26)))
        tails.add(id(it))
        keep.append(it)
        att.add(p[0], p[1], it)
        for f in (0.1, 0.22, 0.34, 0.46):
            p = S.point(f)
            t = S.tangent_at(f)
            att.add(p[0], p[1], (p[0], p[1], t[0], t[1], S, max(1.2, S.R * 0.14)))
    base = _base(cv)
    i0 = len(base.ops)
    for (ax, ay), t0, S, wd in stems:
        w1 = max(1.5, min(4.6, S.R * 0.26))
        pts = _taper_stem(dc, (ax, ay), t0, S.start(), S.tangent(), max(1.2, min(wd, 4.6)), w1)
        for q in range(2, len(pts) - 2, 2):
            tx, ty = _norm(pts[q + 1][0] - pts[q - 1][0], pts[q + 1][1] - pts[q - 1][1])
            anchors.append((pts[q][0], pts[q][1], tx, ty))
    # acanthus wrapped round the outside of each larger scroll, springing from where its stem joins
    for S in order:
        if S.R >= 7:
            spray(dc, S, rng, 0.02, 0.5 if S.R >= 12 else 0.38)
    for S in order[::-1]:
        bw = max(1.5, min(4.6, S.R * 0.26))
        draw_scroll(dc, S, rng, bw=bw, inner_w=min(S.R * 0.62, 11))
        for f in (0.05, 0.2, 0.35, 0.5, 0.65, 0.8):
            p = S.point(f)
            t = S.tangent_at(f)
            anchors.append((p[0], p[1], t[0], t[1]))
    for r in roots:
        anchors.append(r[:4])
    i1 = len(base.ops)
    _field_fill(dc, occ, rng, anchors, 3.0, 14 * scale, spread=1.1)
    _field_fill(dc, occ, rng, anchors, 2.2, 9 * scale, spread=1.2)
    chunk = base.ops[i1:]
    del base.ops[i1:]
    base.ops[i_back:i_back] = chunk
    # the punched ground: fine white dots on what ground still shows, at least a cell clear of every cut
    p = punch * C * C
    g = occ.g
    for j in range(1, occ.ny - 1):
        y = (j + 0.5) * C
        for i in range(1, occ.nx - 1):
            x = (i + 0.5) * C
            ii = i if not sym or x < w / 2 else int((w - x) / C)
            if ii < 1 or ii >= occ.nx - 1:
                continue
            if g[j][ii] or g[j - 1][ii] or g[j + 1][ii] or g[j][ii - 1] or g[j][ii + 1]:
                continue
            if any(hx - 1 <= x <= hx + hw + 1 and hy - 1 <= y <= hy + hh + 1 for hx, hy, hw, hh in holes):
                continue
            if rng.random() < p:
                cv.dot(x + rng.uniform(-0.45, 0.45), y + rng.uniform(-0.45, 0.45))
    if border:
        cv.over("S1", _rect_d(1.0, 1.0, w - 1.0, h - 1.0))
        cv.over("S05", _rect_d(2.75, 2.75, w - 2.75, h - 2.75))
    return scrolls


def _cell_m(mask, occ, x, y):
    i, j = int((x - occ.x0) / occ.c), int((y - occ.y0) / occ.c)
    if 0 <= i < occ.nx and 0 <= j < occ.ny:
        return mask[j][i]
    return 1


def field(w, h, holes=(), seed=0, motif="fleuron", border=True):
    """A sheet's engraved ground as one SVG, w x h, holes left transparent."""
    cv = Canvas(w, h)
    cv.tol = 0.15
    cv.model = True
    compose_field(cv, w, h, list(holes), seed, motif=motif, border=border)
    return cv.svg()
