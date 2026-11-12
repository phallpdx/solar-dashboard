"""Engraved book ornaments for the Kindle morning paper: title cartouches, headpieces, culs-de-lampe and
printer's flowers, in the manner of the Evening Edition plates (solar/kindle_evening.py) and the private
presses it borrows from (Kelmscott, Golden Cockerel, Essex House).

Stdlib only. Every public function returns one self-contained `<svg>` string:

    cartouche(width=560, height=70, seed=0, style="banner")   banner | shield | oval | tablet
    headpiece(width=560, seed=0, theme="foliage", height=48)   foliage waves reeds vines notes sun stars thai roses
    tailpiece(width=560, height=150, seed=0, theme="roses")    any height 60..400
    printers_flowers(width=560, seed=0)                        a row of fleurons, 18 px tall

Rules for e-ink (Kindle Paperwhite 11, Chrome 75): black on white only, no gradients or opacity, tone
from hatching patterns or ruled lines, every stroke at least 0.6 px, coordinates baked (no transform
attributes, because the page reset sets `transform:none !important`), 1-decimal numbers.

The same three line weights as the Evening Edition: W0 hairline .6, W1 rule 1, W2 heavy rule 1.6.
Tone patterns are defined inside each SVG under an id prefix hashed from the call, so any number of
pieces can share a page.

Easter eggs, placed by seed: a tiny sitting dog, a toddler's beach ball, a crossed pair of drumsticks,
a little engraved "P", a surfer on a wave, a heron in the reeds.
"""
import math
import random
import re
import zlib

__all__ = ["cartouche", "headpiece", "tailpiece", "printers_flowers",
           "CARTOUCHE_STYLES", "HEADPIECE_THEMES", "TAILPIECE_THEMES"]

W0, W1, W2 = .5, 1.0, 1.5
CARTOUCHE_STYLES = ("banner", "shield", "oval", "tablet")
HEADPIECE_THEMES = ("foliage", "waves", "reeds", "vines", "notes", "sun", "stars", "thai", "roses")
TAILPIECE_THEMES = HEADPIECE_THEMES + ("dog", "drums", "coast", "jazz", "surf", "portland")
PI = math.pi


# ---------------------------------------------------------------------------------------------
# numbers, affine frames, path data
# ---------------------------------------------------------------------------------------------

def _n(x):
    s = f"{x:.1f}"
    if s == "-0.0":
        return "0"
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


class _M:
    """A 2-D affine frame. (A @ B)(p) == A(B(p))."""
    __slots__ = ("a", "b", "c", "d", "e", "f")

    def __init__(self, a=1., b=0., c=0., d=1., e=0., f=0.):
        self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f

    def __matmul__(self, o):
        return _M(self.a * o.a + self.c * o.b, self.b * o.a + self.d * o.b,
                  self.a * o.c + self.c * o.d, self.b * o.c + self.d * o.d,
                  self.a * o.e + self.c * o.f + self.e, self.b * o.e + self.d * o.f + self.f)

    def __call__(self, x, y):
        return (self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)

    @property
    def k(self):
        return math.sqrt(abs(self.a * self.d - self.b * self.c))


ID = _M()


def _T(x, y):
    return _M(1, 0, 0, 1, x, y)


def _R(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return _M(c, s, -s, c, 0, 0)


def _S(sx, sy=None):
    return _M(sx, 0, 0, sx if sy is None else sy, 0, 0)


def _at(x, y, s=1., rot=0., flip=False, vflip=False):
    """Frame for a motif drawn at the origin: scale, mirror, rotate (degrees), then move to (x, y)."""
    return _T(x, y) @ _R(rot) @ _S(-s if flip else s, -s if vflip else s)


_TOK = re.compile(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_NARG = dict(M=2, L=2, C=6, Q=4, S=4, T=2, H=1, V=1)


def _fi(v):
    """An integer count of tenths as the shortest decimal."""
    q, r = divmod(abs(v), 10)
    t = (str(q) if q else "") + (f".{r}" if r else "")
    return ("-" + t if v < 0 else t) if t else "0"


class _Pen:
    """Path data writer: relative commands on a grid of tenths, so rounding never drifts."""

    def __init__(self):
        self.o, self.last = [], ""
        self.cx = self.cy = self.sx = self.sy = 0

    def cmd(self, c, pts):
        ip = [(round(x * 10), round(y * 10)) for x, y in pts]
        if not self.o:
            nums, letter = [_fi(ip[0][0]), _fi(ip[0][1])], "M"
        else:
            nums, letter = [], c.lower()
            for X, Y in ip:
                nums += [_fi(X - self.cx), _fi(Y - self.cy)]
        txt = nums[0] + "".join(t if t[0] == "-" else "," + t for t in nums[1:])
        if letter == self.last and letter not in "mM":
            self.o.append(txt if txt[0] == "-" else " " + txt)
        else:
            self.o.append(letter + txt)
        self.last = letter
        self.cx, self.cy = ip[-1]
        if c == "M":
            self.sx, self.sy = self.cx, self.cy

    def close(self):
        self.o.append("z")
        self.last = "z"
        self.cx, self.cy = self.sx, self.sy

    def __str__(self):
        return "".join(self.o)


def _tp(d, m=ID):
    """Bake frame m into path data (written relative, in tenths)."""
    toks = _TOK.findall(d)
    pen = _Pen()
    x = y = sx = sy = 0.
    pc = pq = None
    cmd, i = "M", 0
    put = lambda c, *pts: pen.cmd(c, [m(*p) for p in pts])
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                pen.close()
                x, y = sx, sy
                pc = pq = None
            continue
        C = cmd.upper()
        rel = cmd != C
        n = _NARG[C]
        a = [float(v) for v in toks[i:i + n]]
        i += n
        if C == "H":
            a, C, rel = [a[0] + (x if rel else 0), y], "L", False
        elif C == "V":
            a, C, rel = [x, a[0] + (y if rel else 0)], "L", False
        if rel:
            a = [v + (x if k % 2 == 0 else y) for k, v in enumerate(a)]
        if C == "M":
            put("M", (a[0], a[1]))
            x, y = sx, sy = a[0], a[1]
            cmd = "l" if cmd == "m" else "L"
            pc = pq = None
        elif C == "L":
            put("L", (a[0], a[1]))
            x, y = a
            pc = pq = None
        elif C == "C":
            put("C", (a[0], a[1]), (a[2], a[3]), (a[4], a[5]))
            pc, pq = (a[2], a[3]), None
            x, y = a[4], a[5]
        elif C == "S":
            c1 = (2 * x - pc[0], 2 * y - pc[1]) if pc else (x, y)
            put("C", c1, (a[0], a[1]), (a[2], a[3]))
            pc, pq = (a[0], a[1]), None
            x, y = a[2], a[3]
        elif C == "Q":
            put("Q", (a[0], a[1]), (a[2], a[3]))
            pq, pc = (a[0], a[1]), None
            x, y = a[2], a[3]
        elif C == "T":
            c1 = (2 * x - pq[0], 2 * y - pq[1]) if pq else (x, y)
            put("Q", c1, (a[0], a[1]))
            pq, pc = c1, None
            x, y = a
    return str(pen)


def _ell(cx, cy, rx, ry):
    """Ellipse as four cubics (so a frame can rotate or shear it)."""
    k = .5523
    return (f"M{cx + rx},{cy}C{cx + rx},{cy + ry * k} {cx + rx * k},{cy + ry} {cx},{cy + ry}"
            f"C{cx - rx * k},{cy + ry} {cx - rx},{cy + ry * k} {cx - rx},{cy}"
            f"C{cx - rx},{cy - ry * k} {cx - rx * k},{cy - ry} {cx},{cy - ry}"
            f"C{cx + rx * k},{cy - ry} {cx + rx},{cy - ry * k} {cx + rx},{cy}Z")


def _poly(pts, close=False):
    if not pts:
        return ""
    pen = _Pen()
    pen.cmd("M", [pts[0]])
    for p in pts[1:]:
        pen.cmd("L", [p])
    if close:
        pen.close()
    return str(pen)


def _cr(pts, close=False):
    """Catmull-Rom spline through points (already in plate space) as cubic path data."""
    n = len(pts)
    if n < 3:
        return _poly(pts, close)
    P = (lambda i: pts[i % n]) if close else (lambda i: pts[max(0, min(n - 1, i))])
    pen = _Pen()
    pen.cmd("M", [pts[0]])
    for i in range(n if close else n - 1):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        pen.cmd("C", [c1, c2, p2])
    if close:
        pen.close()
    return str(pen)


# ---- centre lines ---------------------------------------------------------------------------

def _bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def _bezs(*segs, n=16):
    """Chain of cubic segments, each given as (p1, p2, p3) after a start point: _bezs(p0, (c1,c2,p), ...)."""
    p0, pts = segs[0], [segs[0]]
    for c1, c2, p in segs[1:]:
        pts += _bez(p0, c1, c2, p, n)[1:]
        p0 = p
    return pts


def _spiral(cx, cy, r0, a0, turns, shrink=.22, cw=1, n=None):
    """Volute centre line from radius r0 at angle a0 (degrees) winding in by `turns`."""
    n = n or max(10, int(turns * 28))
    out = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0) + cw * 2 * PI * turns * t
        r = r0 * shrink ** t
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def _arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _mp(m, pts):
    return [m(*p) for p in pts]


def _dp(pts, tol):
    """Douglas-Peucker simplification."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1e-9
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            dd = abs((px - ax) * dy - (py - ay) * dx) / L
            if dd > best:
                best, bi = dd, i
        if best > tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def _swell_d(pts, w0, w1, wm=0., tol=.25):
    """A tapering, swelling engraved line along pts (plate space) as a closed polygon: width runs
    w0 -> w1 with an added bulge wm at mid-length."""
    n = len(pts)
    if n < 2:
        return ""
    # arc length
    acc = [0.]
    for i in range(1, n):
        acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    tot = acc[-1] or 1
    L, Rt = [], []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        t = acc[i] / tot
        w = (w0 + (w1 - w0) * t + wm * math.sin(PI * t)) / 2
        L.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        Rt.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    ring = _dp(L, tol) + _dp(Rt[::-1], tol)
    return _poly(ring, True)


# ---------------------------------------------------------------------------------------------
# the plate: one SVG, its tone patterns, its parts
# ---------------------------------------------------------------------------------------------

def _diag(s, back=False):
    if back:
        return f"M0,0L{_n(s)},{_n(s)}M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(s * 1.5)}M{_n(s / 2)},{_n(-s / 2)}L{_n(s * 1.5)},{_n(s / 2)}"
    return f"M0,{_n(s)}L{_n(s)},0M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(-s / 2)}M{_n(s / 2)},{_n(s * 1.5)}L{_n(s * 1.5)},{_n(s / 2)}"


# name -> (w, h, content). E-ink rules (Kindle PW11, DPR 2): tiles are whole device pixels (1, 1.5, 2, 3
# or 4 CSS), strokes 0.5 or 1 CSS, orthogonal rules crisp on the half-pixel grid, 45-degree diagonals,
# each cross-hatch layer at a 3 CSS pitch or wider so it never fills in.
_CR = ' shape-rendering="crispEdges"'
_PATS = {
    "h": (3, 3, f'<path d="{_diag(3)}" stroke="#000" stroke-width=".5"/>'),                 # 45-degree hatch
    "b": (3, 3, f'<path d="{_diag(3, True)}" stroke="#000" stroke-width=".5"/>'),           # back diagonal
    "x": (4, 4, f'<path d="{_diag(4)}{_diag(4, True)}" stroke="#000" stroke-width=".5"/>'),  # cross-hatch
    "X": (3, 3, f'<path d="{_diag(3)}{_diag(3, True)}" stroke="#000" stroke-width=".5"/>'),  # deep shade
    "v": (3, 3, f'<path d="M0,1.25H3" stroke="#000" stroke-width=".5"{_CR}/>'),             # ruled ground
    "V": (2, 2, f'<path d="M0,1H2" stroke="#000" stroke-width="1"{_CR}/>'),                  # dense ruled ground
    "u": (3, 3, f'<path d="M1.25,0V3" stroke="#000" stroke-width=".5"{_CR}/>'),             # vertical rules
    "s": (3, 3, '<circle cx=".75" cy=".75" r=".5" fill="#000"/><circle cx="2.25" cy="2.25" r=".5" fill="#000"/>'),
    "t": (4, 4, '<circle cx="1" cy="1" r=".5" fill="#000"/><circle cx="3" cy="3" r=".5" fill="#000"/>'),
    "c": (3, 3, '<rect width="3" height="3" fill="#000"/><circle cx="1.5" cy="1.5" r=".75" fill="#fff"/>'),  # crible
    "w": (6, 3, '<path d="M0,1.5Q1.5,0 3,1.5T6,1.5" fill="none" stroke="#000" stroke-width=".5"/>'),       # watered
}


def _sw(x):
    """Snap a stroke width to whole device pixels: 0.5, 1, 1.5, 2 ... CSS."""
    return max(.5, round(x * 2) / 2)


class _Plate:
    def __init__(self, w, h, key, cls):
        self.w, self.h, self.cls = w, h, cls
        z = zlib.crc32(key.encode()) & 0xffffff
        al = "abcdefghijklmnopqrstuvwxyz0123456789"
        self.pid = "q" + "".join(al[(z >> (5 * i)) % 36] for i in range(4))
        self.parts = []
        self.used = set()

    def f(self, fill):
        if fill and fill[0] == "@":
            self.used.add(fill[1:])
            return f"url(#{self.pid}{fill[1:]})"
        return fill

    # strokes: root defaults are fill none, stroke black, width .6
    def line(self, d, m=ID, sw=W0, extra=""):
        if not d:
            return
        sw = _sw(sw)
        w = "" if sw == W0 else f' stroke-width="{_n(sw)}"'
        self.parts.append(f'<path d="{_tp(d, m or ID)}"{w}{extra}/>')

    def shape(self, d, m=ID, fill="#fff", sw=W0, extra=""):
        sw = _sw(sw) if sw else 0
        w = ' stroke="none"' if not sw else "" if sw == W0 else f' stroke-width="{_n(sw)}"'
        self.parts.append(f'<path d="{_tp(d, m or ID)}" fill="{self.f(fill)}"{w}{extra}/>')

    def blob(self, d, m=ID, fill="#000"):
        if not d:
            return
        self.parts.append(f'<path d="{_tp(d, m or ID)}" fill="{self.f(fill)}" stroke="none"/>')

    def white(self, d, m=ID, sw=W0):
        """A white line (for highlights cut into black)."""
        self.parts.append(f'<path d="{_tp(d, m or ID)}" stroke="#fff" stroke-width="{_n(max(_sw(sw), 1))}"/>')

    def circle(self, x, y, r, fill="#fff", sw=W0, m=ID):
        x, y = m(x, y)
        r *= m.k
        if sw:
            sw = _sw(sw)
            w = "" if sw == W0 else f' stroke-width="{_n(sw)}"'
            self.parts.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="{self.f(fill)}"{w}/>')
        else:
            self.parts.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="{self.f(fill)}" stroke="none"/>')

    def dot(self, x, y, r, m=ID):
        self.circle(x, y, r, "#000", 0, m)

    def swell(self, pts, w0, w1, wm=0., m=None, fill="#000"):
        if m is not None:
            pts = _mp(m, pts)
        d = _swell_d(pts, w0, w1, wm)
        self.parts.append(f'<path d="{d}" fill="{self.f(fill)}" stroke="none"/>')

    def rect(self, x, y, w, h, fill="#fff", sw=W0):
        if sw:
            sw = _sw(sw)
            ww = "" if sw == W0 else f' stroke-width="{_n(sw)}"'
            self.parts.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" fill="{self.f(fill)}"{ww}/>')
        else:
            self.parts.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" fill="{self.f(fill)}" stroke="none"/>')

    def svg(self):
        defs = "".join(
            f'<pattern id="{self.pid}{k}" width="{_PATS[k][0]}" height="{_PATS[k][1]}" patternUnits="userSpaceOnUse">{_PATS[k][2]}</pattern>'
            for k in sorted(self.used))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" class="korn {self.cls}" width="{_n(self.w)}" height="{_n(self.h)}" '
                f'viewBox="0 0 {_n(self.w)} {_n(self.h)}" fill="none" stroke="#000" stroke-width=".5" '
                f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                + (f"<defs>{defs}</defs>" if defs else "") + "".join(self.parts) + "</svg>")


# ---------------------------------------------------------------------------------------------
# motifs. Each draws into a plate through a frame m; local units are given per motif.
# ---------------------------------------------------------------------------------------------

def _wk(m, w, lo=.6):
    """A line width in plate pixels for a local width w, never under lo."""
    return max(lo, w * m.k)


# acanthus leaf (from the Evening Edition): base at origin pointing +x, 18.5 long, lobes on -y.
_ACANTH = ("M0,0C3,-5 8,-7 12,-6C10,-5 9.5,-4 10.5,-3.4C12.5,-4.6 15,-4 16.5,-2.6C14.5,-2.4 13.5,-1.6 14,-.6"
           "C15.5,-1 17.5,0 18.5,1.4C13,2 6,2.2 0,0Z")
_ACANTH_SH = "M0,0C5,.6 10,1 18,1.2L14,-.6 10.5,-3.4C7,-1 3,0 0,0Z"
_ACANTH_V = "M1,-.4C6,-2 10,-3 13,-3"


def _acanthus(pl, m, tone="@h"):
    pl.shape(_ACANTH, m)
    pl.blob(_ACANTH_SH, m, tone)
    pl.line(_ACANTH_V, m)


# Thai kanok flame (lai kranok): base at origin pointing +x, about 20 x 10, flame licks on the belly.
_KANOK = ("M0,0C3,-5 9,-9 15,-9.5C18,-9.7 20.5,-8 20,-5.5C19.6,-7 18,-7.6 16.8,-7C18.4,-5.8 17.6,-3.6 15.6,-3.4"
          "C15.4,-4.4 14.6,-5 13.6,-4.8C14,-3 12.6,-1.4 10.4,-1.4C10.5,-2.4 10,-3.1 9,-3C8.8,-1 6,.2 0,0Z")
_KANOK_V = "M1.5,-.8C5,-3.6 10,-6.6 16,-7.6"


def _kanok(pl, m, fill="#fff", sw=W0):
    pl.shape(_KANOK, m, fill, sw)
    pl.line(_KANOK_V, m)


def _leafy(pl, pts, wmax, lobes=4, side=1, tone="@h", veins=True, sw=W0, away=None, tol=.18):
    """A leafy acanthus scroll grown along a centre line in plate space: lobed on the outer side
    (normal * side), smooth and shaded on the inner side; widest a third of the way along."""
    n = len(pts)
    acc = [0.]
    for i in range(1, n):
        acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    tot = acc[-1] or 1
    if away is not None:
        i = n // 3
        a, b = pts[i - 1], pts[i + 1]
        side = 1 if (-(b[1] - a[1])) * (pts[i][0] - away[0]) + (b[0] - a[0]) * (pts[i][1] - away[1]) > 0 else -1
    out, inn, nrm = [], [], []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl * side, tx / tl * side
        t = acc[i] / tot
        w = wmax * math.sin(PI * min(1, t ** .75)) ** .8
        g = abs(math.sin(lobes * PI * t)) ** .55
        wo = w * (.5 + .5 * g)
        out.append((pts[i][0] + nx * wo, pts[i][1] + ny * wo))
        inn.append((pts[i][0] - nx * w * .42, pts[i][1] - ny * w * .42))
        nrm.append((nx, ny, w, t))
    ring = _dp(out, tol) + _dp(inn[::-1], tol)
    pl.shape(_poly(ring, True), None, "#fff", sw)
    pl.blob(_poly(_dp(pts, tol) + _dp(inn[::-1], tol), True), None, tone)
    if veins:
        d = _poly(_dp(pts[: int(n * .9)], tol))
        for k in range(lobes):
            t = (k + .5) / lobes
            i = min(n - 1, int(t * (n - 1)))
            nx, ny, w, _ = nrm[i]
            if w > 1.6:
                p = pts[i]
                j = min(n - 1, i + max(1, n // (lobes * 3)))
                q = pts[j]
                d += f"M{_n(p[0] + nx * w * .1)},{_n(p[1] + ny * w * .1)}Q{_n(q[0] + nx * w * .4)},{_n(q[1] + ny * w * .4)} {_n(p[0] + nx * w * .78)},{_n(p[1] + ny * w * .78)}"
        pl.line(d, None)


def _leaf(pl, m, wd=.32, tone="@h"):
    """A lanceolate leaf, base at origin, tip at (1, 0); lower half toned."""
    a, b = wd, wd * .8
    pl.shape(f"M0,0C.25,{-a} .7,{-b} 1,0C.7,{b} .25,{a} 0,0Z", m)
    pl.blob(f"M0,0L1,0C.7,{b} .25,{a} 0,0Z", m, tone)


def _leaf_black(pl, m, wd=.3):
    pl.blob(f"M0,0C.25,{-wd} .7,{-wd * .8} 1,0C.7,{wd * .8} .25,{wd} 0,0Z", m)


def _volute(pl, m, r=1., turns=1.3, w=.22, a0=90., cw=1, eye=True):
    """A spiral scroll end at the origin's circle of radius r, starting at angle a0; swelling line."""
    pts = _spiral(0, 0, r, a0, turns, .2, cw)
    pl.swell(_mp(m, pts), _wk(m, w * .9), _wk(m, w * .25, .45), _wk(m, w * .5, 0))
    if eye:
        ex, ey = pts[-1]
        pl.dot(ex, ey, w * .7, m)


def _scallops(m, r, n, a0, dip, ox=0., oy=0., bulge=1.28):
    """A closed ring of n petal scallops: dips at radius r*dip, each petal a quadratic through r."""
    d = ""
    for i in range(n + 1):
        a = math.radians(a0 + 360 * i / n)
        p = m(ox + r * dip * math.cos(a), oy + r * dip * math.sin(a))
        if i == 0:
            d = f"M{_n(p[0])},{_n(p[1])}"
            continue
        am = math.radians(a0 + 360 * (i - .5) / n)
        c = m(ox + r * bulge * math.cos(am), oy + r * bulge * math.sin(am))
        d += f"Q{_n(c[0])},{_n(c[1])} {_n(p[0])},{_n(p[1])}"
    return d + "Z"


def _rose(pl, m, spin=0., tone="@h"):
    """A full-blown rose seen from above, unit radius: hatched outer petals, a white cup, a spiral heart."""
    sw = W0 if m.k < 14 else W1
    pl.shape(_scallops(m, .86, 5, -90 + spin, .82), None, tone, sw)
    pl.shape(_scallops(m, .7, 5, -54 + spin, .8, -.07, -.08), None, "#fff")
    pl.shape(_scallops(m, .46, 4, -20 + spin, .82, -.06, -.08), None, "@h")
    pl.shape(_scallops(m, .32, 3, 30 + spin, .85, -.07, -.1), None, "#fff")
    pts = _spiral(-.07, -.1, .26, spin * 3, 1.4, .18, 1, 20)
    pl.swell(_mp(m, pts), _wk(m, .1), _wk(m, .03, .4), _wk(m, .05, 0))
    if m.k > 11:   # petal turnover lines
        d = ""
        for k in range(5):
            a = math.radians(-54 + spin + 72 * k + 36)
            p1 = m(-.07 + .62 * math.cos(a), -.08 + .62 * math.sin(a))
            p2 = m(-.07 + .74 * math.cos(a + .3), -.08 + .74 * math.sin(a + .3))
            d += f"M{_n(p1[0])},{_n(p1[1])}L{_n(p2[0])},{_n(p2[1])}"
        pl.line(d, None)


def _bud(pl, m, tone="@h"):
    """A rose bud, base at origin pointing +x, length 1, with three sepals."""
    pl.shape("M.12,0C.1,-.34 .5,-.42 1,0C.5,.42 .1,.34 .12,0Z", m)
    pl.blob("M.12,0L1,0C.5,.42 .1,.34 .12,0Z", m, tone)
    pl.line("M.3,.16C.5,.05 .7,-.1 .95,-.02", m)
    pl.blob("".join(_tp("M0,0C.25,-.2 .7,-.16 1,0C.7,.16 .25,.2 0,0Z", m @ _at(0, 0, sc, rot)) for rot, sc in ((-28, .62), (0, .5), (28, .62))),
            None)


def _vine_leaf(pl, m, tone="@h"):
    """A five-lobed vine leaf, base at origin pointing +x, about unit length."""
    lob = ((-78, .6), (-40, .86), (0, 1.), (40, .86), (78, .6))
    pts = [m(-.06, 0)]
    for k, (a, r) in enumerate(lob):
        for da, rr in ((-17, .44), (0, r)):
            aa = math.radians(a + da)
            pts.append(m(rr * math.cos(aa), rr * math.sin(aa)))
    aa = math.radians(95)
    pts.append(m(.44 * math.cos(aa), .44 * math.sin(aa)))
    pl.shape(_cr(pts, True), None)
    half = [m(0, 0)] + pts[5:]
    pl.blob(_cr(half, True), None, tone)
    d = ""
    for a, r in lob:
        aa = math.radians(a)
        d += f"M0,0L{_n(r * .8 * math.cos(aa))},{_n(r * .8 * math.sin(aa))}"
    pl.line(d, m)


def _grapes(pl, m):
    """A hanging cluster, stalk at origin pointing +x, about unit length."""
    rows = ((.14, (-.1, .1)), (.32, (-.19, 0, .19)), (.5, (-.1, .1)), (.68, (-.12, .08)), (.86, (0,)))
    for i, (x, ys) in enumerate(rows):
        for k, y in enumerate(ys):
            pl.circle(x, y, .1, "@h" if (i + k) % 2 else "#fff", W0, m)


def _star4(pl, x, y, r, w=None):
    w = r * .2 if w is None else w
    pl.blob(f"M{_n(x)},{_n(y - r)}Q{_n(x + w)},{_n(y - w)} {_n(x + r)},{_n(y)}Q{_n(x + w)},{_n(y + w)} "
            f"{_n(x)},{_n(y + r)}Q{_n(x - w)},{_n(y + w)} {_n(x - r)},{_n(y)}Q{_n(x - w)},{_n(y - w)} {_n(x)},{_n(y - r)}Z", None)


def _star5(pl, x, y, r, fill="#fff", rot=0.):
    pts = []
    for i in range(10):
        a = math.radians(-90 + rot + i * 36)
        rr = r if i % 2 == 0 else r * .42
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    pl.shape(_poly(pts, True), None, fill)


# ---- the Easter eggs ------------------------------------------------------------------------

_DOG_SIT = ("M.6,0C-.4,-1.6 -.2,-4 1.4,-5.2C2.6,-6 3.6,-6.6 4.3,-7.7L4.6,-9.5C4.8,-10.5 5.9,-10.9 6.7,-10.5"
            "L7.3,-9.7L8.9,-9.3C9.6,-9.1 9.6,-8.2 8.9,-8L7.4,-7.6C6.9,-6.6 6.9,-5.3 7,-4.3L7.2,-.4L7.8,0"
            "H5.9L5.8,-3.2L4.4,-1.6L4.6,-.4L5.2,0Z")


def _tiny_dog(pl, x, y, s=1., flip=False):
    """A tiny dog sitting, feet at (x, y), about 11 px tall at s=1, facing right (or left)."""
    m = _at(x, y, s, 0, flip)
    pl.blob(_DOG_SIT, m)
    pl.swell(_mp(m, _bezs((1, -1.2), ((-.4, -1.6), (-1.6, -2.6), (-1.6, -4.2)), n=8)), _wk(m, .9), _wk(m, .4, .5))
    pl.white("M5.5,-9.6C5.2,-8.6 5.3,-7.8 5.8,-7.2", m)   # the ear
    pl.dot(7.6, -8.9, .35 if s > 1.2 else .01, m)


def _ball(pl, x, y, r):
    """A toddler's beach ball."""
    m = _at(x, y, r)
    pl.circle(0, 0, 1, "#fff", W0, m)
    pl.shape("M0,-1C-.62,-.5 -.62,.5 0,1C.62,.5 .62,-.5 0,-1Z", m, "@h")
    pl.shape("M0,-1C.95,-.6 .95,.6 0,1", m, "none")
    pl.circle(0, -.98, .18, "#fff", W0, m)
    pl.line("M-.55,-.55Q-.68,-.3 -.66,-.1", m)


def _drumsticks(pl, x, y, s=1., ang=28):
    """A crossed pair of drumsticks centred at (x, y), each about 2s*10 long."""
    for sgn in (1, -1):
        a = math.radians(90 + sgn * ang)
        dx, dy = math.cos(a) * 10 * s, math.sin(a) * 10 * s
        p0, p1 = (x - dx, y + dy), (x + dx * .95, y - dy * .95)
        pl.swell([p0, p1], max(1.4, 1.5 * s), max(.6, .55 * s))
        pl.circle(x + dx, y - dy, max(.8, .75 * s), "#000", 0)


def _monogram(pl, x, y, h, fill="#000"):
    """A little engraved P, baseline-left at (x, y), cap height h."""
    m = _at(x, y, h)
    pl.swell(_mp(m, [(.18, 0), (.18, -1)]), _wk(m, .15, .9), _wk(m, .15, .9))
    pl.swell(_mp(m, _bezs((.18, -1), ((.82, -1.04), (.86, -.44), (.18, -.46)), n=14)), _wk(m, .04, .6), _wk(m, .05, .6),
             _wk(m, .14, 0))
    pl.line("M0,0H.4M0,-1H.22", m, _wk(m, .06))


# ---- sea and shore --------------------------------------------------------------------------

def _breaker(pl, m, foam=True, surfer=False):
    """A curling wave travelling +x: base from (0, 0) to (1.15, 0), crest about .8 high; the curl is
    hatched, the face carries contour lines, foam claws at the lip."""
    body = ("M0,0C.18,-.04 .3,-.3 .42,-.52C.54,-.74 .74,-.86 .92,-.8C1.06,-.75 1.1,-.6 1.02,-.5"
            "C.96,-.43 .86,-.46 .86,-.54C.86,-.6 .93,-.6 .94,-.56"
            "C.86,-.66 .7,-.62 .64,-.48C.56,-.3 .66,-.1 .82,-.04C.92,0 1.04,0 1.15,0Z")
    pl.shape(body, m, "#fff", W0 if m.k < 30 else W1)
    pl.blob("M.94,-.56C.86,-.66 .7,-.62 .64,-.48C.56,-.3 .66,-.1 .82,-.04C.92,0 1.04,0 1.15,0"
            "C.95,-.06 .82,-.2 .82,-.36C.82,-.48 .88,-.54 .94,-.56Z", m, "@x")
    pl.line("M.12,-.04C.24,-.14 .34,-.36 .46,-.54C.56,-.68 .7,-.76 .84,-.76"
            "M.26,-.03C.36,-.12 .44,-.3 .54,-.46C.6,-.56 .68,-.62 .76,-.66"
            "M.42,-.02C.48,-.1 .52,-.22 .58,-.34", m)
    if foam:
        for k, (fx, fy, r) in enumerate(((1.04, -.72, .04), (1.09, -.62, .03), (1.0, -.86, .035), (1.1, -.78, .025))):
            pl.circle(fx, fy, r, "#fff", W0, m)
    if surfer and m.k > 14:
        # a tiny surfer riding down the face
        sx, sy = .5, -.42
        p = lambda x, y: m(sx + x, sy + y)
        sx, sy = .44, -.36
        b0, b1 = p(-.06, .03), p(.07, -.01)
        bw = max(1.2, .018 * m.k)
        pl.swell([b0, b1], bw, bw)
        q = lambda x, y: f"{_n(p(x * .5, y * .5)[0])},{_n(p(x * .5, y * .5)[1])}"
        pl.line(f"M{q(-.02, .03)}L{q(0, -.06)}L{q(.04, .02)}M{q(0, -.06)}L{q(.02, -.13)}M{q(-.06, -.1)}L{q(.08, -.09)}", None, max(.8, .01 * m.k))
        c = p(.012, -.08)
        pl.circle(c[0], c[1], max(.9, .013 * m.k), "#000", 0)


def _sea_lines(pl, x0, x1, y0, y1, seed=0, step=2.6):
    """Broken horizontal hairlines for water, closer together toward the horizon."""
    rnd = random.Random(seed)
    d = ""
    step = max(3, round(step))                 # whole-pixel pitch, lines on the half-pixel grid
    y = math.floor(y0 + 1) + .25
    while y < y1:
        x = x0 + rnd.uniform(0, 6)
        while x < x1:
            ln = rnd.uniform(9, 24)
            d += f"M{_n(x)},{_n(y)}h{_n(min(ln, x1 - x))}"
            x += ln + rnd.uniform(2, 4)
        y += step
    pl.line(d, None, W0, ' shape-rendering="crispEdges"')


def _scallop(pl, m, n=11):
    """A scallop shell, hinge at origin, fan opening toward -y, unit radius."""
    pts = []
    for i in range(2 * n + 1):
        a = math.radians(-160 + 140 * i / (2 * n))
        r = 1 if i % 2 == 0 else .93
        pts.append(m(r * math.cos(a), r * math.sin(a) * .95))
    rim = [m(-.22, -.05)] + pts + [m(.22, -.05)]
    pl.shape(_cr(rim, True), None, "#fff", W0 if m.k < 20 else W1)
    rib = ""
    for i in range(0, 2 * n + 1, 2):
        a = math.radians(-160 + 140 * i / (2 * n))
        p0 = m(.16 * math.cos(a), .16 * math.sin(a) - .05)
        p1 = m(.97 * math.cos(a), .97 * math.sin(a) * .95)
        rib += f"M{_n(p0[0])},{_n(p0[1])}L{_n(p1[0])},{_n(p1[1])}"
        if i % 4 == 2:
            a2 = math.radians(-160 + 140 * (i + 1) / (2 * n))
            q0 = m(.2 * math.cos(a), .2 * math.sin(a) - .05)
            q1 = m(.92 * math.cos(a2), .92 * math.sin(a2) * .95)
            pl.blob(_poly([q0, p1, q1], True), None, "@h")
    pl.line(rib, None, W0 if m.k < 25 else .8)
    pl.line(_cr([m(.6 * math.cos(math.radians(a)), .6 * math.sin(math.radians(a)) * .95) for a in range(-155, -20, 15)]), None)
    pl.shape("M-.22,-.05L-.42,-.12L-.36,.06L-.04,.08ZM.22,-.05L.42,-.12L.36,.06L.04,.08Z", m, "@h")


def _moon_snail(pl, m):
    """A moon snail shell seen from above: a spiral whorl, unit radius."""
    pl.circle(0, 0, 1, "#fff", W1 if m.k > 12 else W0, m)
    pl.blob(_cr(_mp(m, _arc(0, 0, 1, 1, -10, 120, 10) + _arc(.1, .05, .78, .8, 120, -10, 10)), True), None, "@h")
    pts = _spiral(.05, .05, .92, -30, 2.2, .1)
    pl.swell(_mp(m, pts), _wk(m, .08), _wk(m, .03, .5))
    pl.circle(.05, .05, .1, "#000", 0, m)


def _sand_dollar(pl, m):
    """A sand dollar: stippled disc, five white petals."""
    pl.circle(0, 0, 1, "@t", W0, m)
    for k in range(5):
        a = -90 + 72 * k
        mm = m @ _at(math.cos(math.radians(a)) * .14, math.sin(math.radians(a)) * .14, .58, a)
        pl.shape("M0,0C.25,-.28 .7,-.24 1,0C.7,.24 .25,.28 0,0Z", mm)
        pl.line("M.12,0H.85", mm)
    pl.circle(0, 0, .08, "#000", 0, m)


def _starfish(pl, m, rot=10):
    pts = []
    for i in range(10):
        a = math.radians(-90 + rot + i * 36)
        r = 1 if i % 2 == 0 else .38
        pts.append(m(r * math.cos(a), r * math.sin(a)))
    d = f"M{_n(pts[0][0])},{_n(pts[0][1])}"
    for i in range(1, 11):
        p, q = pts[i % 10], pts[(i - 1) % 10]
        if i % 2 == 1:   # out-arm tip to valley: curve inward
            c = m(0, 0)
            cx, cy = (p[0] * 2 + q[0] + c[0] * .3) / 3.3, (p[1] * 2 + q[1] + c[1] * .3) / 3.3
        else:
            cx, cy = (p[0] * 2 + q[0]) / 3, (p[1] * 2 + q[1]) / 3
        d += f"Q{_n(cx)},{_n(cy)} {_n(p[0])},{_n(p[1])}"
    pl.shape(d + "Z", None, "@s")
    for i in range(0, 10, 2):
        a = math.radians(-90 + rot + i * 36)
        for r in (.3, .52, .72):
            pl.circle(r * math.cos(a), r * math.sin(a), .05, "#fff", W0, m)


# ---- marsh ------------------------------------------------------------------------------------

def _reed(pl, x, y, h, lean, cattail=False, w=1.):
    """A reed from (x, y) rising h with a lean; a cattail head when asked."""
    top = (x + lean, y - h)
    pts = _bez((x, y), (x, y - h * .4), (x + lean * .6, y - h * .8), top, 10)
    pl.swell(pts, 1.1 * w, .5 * w)
    if cattail:
        i0 = int(len(pts) * .55)
        a, b = pts[i0], pts[int(len(pts) * .82)]
        pl.swell(_bez(a, a, b, b, 4), 2.6 * w, 2.4 * w, .6 * w, fill="#000")
        pl.white(f"M{_n(a[0] + .5)},{_n(a[1] - 1.5)}L{_n(b[0] + .3)},{_n(b[1] + 1.5)}", None)


def _blade(pl, x, y, h, bend, w=1.4):
    """A grass blade or flag leaf curving over."""
    pts = _bez((x, y), (x + bend * .1, y - h * .6), (x + bend * .6, y - h), (x + bend, y - h * .8), 12)
    pl.swell(pts, w, .4)


_HERON = ("M18,22C18,17 21,14 22,11C23,8 21,6.5 19.5,7C18.6,7.3 18.4,8.2 18.8,8.8")


def _heron(pl, m):
    """A heron standing in the shallows (the Evening Edition's, in the 40 x 40 roundel frame)."""
    pl.line(_HERON, m, _wk(m, .9 / 3, 1))
    pl.blob("M19.4,7.2L12.5,8.4L19.6,8.2Z", m)
    pl.shape("M16,22C18,19 24,18 27,21C29,23 30,26 31,28C27,27 22,27 18,26C16,25 15.5,23.5 16,22Z", m, "@h")
    pl.line("M21,26.5L20,33M23,26.8L24,33", m)
    pl.line("M28,23.5C28.6,25 29.6,26.5 31,28M25,21.5C26.4,23 27.4,25 28,27", m)


# ---- sky ----------------------------------------------------------------------------------------

def _sun(pl, cx, cy, r, rays=16, face=True, ray_len=None):
    """An engraved sun: straight rays alternating with flame rays, a ringed disc, a face when large."""
    ray_len = ray_len or r * .9
    for i in range(rays):
        a = 2 * PI * i / rays
        ca, sa = math.cos(a), math.sin(a)
        if i % 2 == 0:
            p0 = (cx + ca * r * 1.08, cy + sa * r * 1.08)
            p1 = (cx + ca * (r + ray_len), cy + sa * (r + ray_len))
            pl.swell([p0, p1], max(.9, r * .2), .6)
        else:
            pts = []
            for k in range(13):
                t = k / 12
                rr = r * 1.1 + ray_len * .7 * t
                off = math.sin(t * 2 * PI) * r * .09
                pts.append((cx + ca * rr - sa * off, cy + sa * rr + ca * off))
            pl.swell(pts, max(.8, r * .12), .5)
    pl.circle(cx, cy, r, "#fff", W1 if r > 8 else W0)
    pl.circle(cx, cy, r * .84, "none", W0)
    if face and r >= 9:
        m = _at(cx, cy, r * .84)
        pl.line("M-.45,-.25Q-.28,-.4 -.12,-.25M.12,-.25Q.28,-.4 .45,-.25", m, _wk(m, .06))
        pl.dot(-.28, -.16, .07, m)
        pl.dot(.28, -.16, .07, m)
        pl.line("M0,-.15Q.1,.12 -.04,.14M-.3,.36Q0,.52 .3,.36", m, _wk(m, .06))
        pl.blob(_poly(_mp(m, _arc(0, 0, .95, .95, 20, 160, 12) + _arc(0, -.05, .8, .85, 160, 20, 12)), True), None, "@s")
    else:
        pl.circle(cx, cy, r * .55, "@s", 0)


def _crescent(pl, m, tone="@h", face=True):
    """A waxing crescent with a sleeping face, unit radius, horns to the right."""
    d = ("M.35,-.94C-.35,-1.1 -1.05,-.6 -1,0C-.95,.6 -.35,1.1 .35,.94"
         "C-.15,.78 -.48,.42 -.48,0C-.48,-.42 -.15,-.78 .35,-.94Z")
    pl.shape(d, m, "#fff", W0 if m.k < 14 else W1)
    pl.blob("M-.5,-.75C-.92,-.5 -1.02,.2 -.75,.6C-.55,.85 -.2,.98 .1,.98C-.4,.86 -.86,.4 -.86,0C-.86,-.36 -.72,-.6 -.5,-.75Z", m, tone)
    if face and m.k > 9:
        pl.line("M-.36,-.22Q-.28,-.14 -.2,-.2", m)
        pl.line("M-.46,.28Q-.36,.34 -.3,.3", m)


def _cloud(pl, x0, x1, base, h, seed=0):
    """A cumulus bank: rounded billows over a ruled shadow."""
    rnd = random.Random(seed)
    pts = [(x0, base)]
    x = x0
    n = max(3, int((x1 - x0) / (h * 1.1)))
    for i in range(n):
        xa = x0 + (x1 - x0) * (i + .5) / n
        pts.append((xa, base - h * (.55 + .45 * math.sin(PI * (i + .5) / n)) * rnd.uniform(.85, 1.05)))
    pts.append((x1, base))
    d = f"M{_n(x0)},{_n(base)}"
    for i in range(1, len(pts)):
        (ax, ay), (bx, by) = pts[i - 1], pts[i]
        mx = (ax + bx) / 2
        top = min(ay, by) - h * .35
        d += f"C{_n(ax)},{_n(top)} {_n(bx)},{_n(top)} {_n(bx)},{_n(by)}"
    pl.shape(d + "Z", None, "#fff")
    pl.blob(f"M{_n(x0 + h * .3)},{_n(base - h * .22)}H{_n(x1 - h * .3)}V{_n(base)}H{_n(x0 + h * .3)}Z", None, "@v")


# ---- music ----------------------------------------------------------------------------------------

def _note(pl, x, y, sp, stem_up=True, flag=0, open_head=False):
    """A note head at (x, y), staff spacing sp; returns the stem tip."""
    m = _at(x, y, sp, -22)
    if open_head:
        pl.shape(_ell(0, 0, .62, .4), m, "#fff", W1)
    else:
        pl.blob(_ell(0, 0, .62, .42), m)
    hx = x + sp * .56 * (1 if stem_up else -1)
    tip = (hx, y - sp * 3.3) if stem_up else (hx, y + sp * 3.3)
    pl.line(f"M{_n(hx)},{_n(y + (-.15 if stem_up else .15) * sp)}L{_n(tip[0])},{_n(tip[1])}", None, max(.7, sp * .14))
    for k in range(flag):
        yy = tip[1] + (k * sp * .8 if stem_up else -k * sp * .8)
        s = 1 if stem_up else -1
        pl.swell(_bez((tip[0], yy), (tip[0] + sp * .2, yy + s * sp * .9), (tip[0] + sp * 1.2, yy + s * sp * 1.2),
                      (tip[0] + sp * .8, yy + s * sp * 2.4), 10), max(1.2, sp * .4), .5)
    return tip


def _snare(pl, m, sticks=True, mono=False):
    """A snare drum, top head centred at origin, unit radius, shell .55 deep; ruled cylinder shading."""
    k = m.k
    ry, dep = .3, .55
    pl.shape(f"M-1,0L-1,{dep}C-1,{dep + ry * .55} -.55,{dep + ry} 0,{dep + ry}C.55,{dep + ry} 1,{dep + ry * .55} 1,{dep}L1,0Z", m, "#fff",
             W1 if k > 12 else W0)
    d = ""
    xs = [-.94, -.86] + [-.7 + 1.4 * (i / 9) ** .8 for i in range(10)] + [.76, .82, .87, .91, .95, .98]
    for x in xs:
        yv = ry * math.sqrt(max(0, 1 - x * x))
        d += f"M{x:.3f},{yv + .1:.3f}V{dep + yv - .08:.3f}"
    pl.line(d, m)
    for yy in (0, dep):
        pts = _arc(0, yy, 1, ry, 0, 180, 16)
        pl.swell(_mp(m, pts), _wk(m, .07, .9), _wk(m, .07, .9), _wk(m, .02, 0))
    for x in (-.78, -.3, .2, .66):
        yv = ry * math.sqrt(1 - x * x)
        pl.shape(f"M{x - .035},{yv + dep * .32}h.07v{dep * .32}h-.07Z", m, "#000", 0)
        pl.line(f"M{x},{yv + .04}V{yv + dep - .03}", m, _wk(m, .025, .6))
    pl.shape(_ell(0, 0, 1, ry), m, "#fff", W1 if k > 12 else W0)
    pl.line(_cr(_mp(m, _arc(0, 0, .9, ry * .86, 200, 340, 8))), None)
    if mono:
        _monogram(pl, *m(-.08, ry * .55 + .03), .22 * k)
    if sticks:
        a, b = m(-.9, -.65), m(.25, .05)
        pl.swell([a, b], _wk(m, .06, .7), _wk(m, .1, 1.2))
        pl.circle(a[0], a[1], _wk(m, .045, .8), "#000", 0)
        a, b = m(.95, -.55), m(-.15, .1)
        pl.swell([a, b], _wk(m, .06, .7), _wk(m, .1, 1.2))
        pl.circle(a[0], a[1], _wk(m, .045, .8), "#000", 0)


def _prajamyam(pl, m, fill="#fff"):
    """The Thai four-petal flower (dok prajam yam): four kanok petals round a pearl, unit radius."""
    for k in range(4):
        a = 45 + 90 * k
        pl.shape("M0,0C.18,-.28 .62,-.34 1,0C.62,.34 .18,.28 0,0Z", m @ _at(0, 0, 1, a), fill)
        pl.line("M.12,0C.4,-.08 .65,-.06 .86,0", m @ _at(0, 0, 1, a))
        pl.blob("M0,0C.12,-.1 .3,-.12 .5,0C.3,.12 .12,.1 0,0Z", m @ _at(0, 0, .9, 90 * k))
    pl.circle(0, 0, .2, "#fff", W0, m)
    pl.dot(0, 0, .08, m)


def _quatrefoil(pl, cx, cy, r):
    """Four acanthus leaves round a pearl: the foliage emblem and the end-block rosette."""
    for k in range(4):
        _acanthus(pl, _at(cx, cy, r / 19, 45 + 90 * k))
    pl.circle(cx, cy, r * .22, "#fff", W1 if r > 12 else W0)
    _star4(pl, cx, cy, r * .16)


def _rosette(pl, cx, cy, r):
    """A plain engraved rosette: hatched outer petals, white inner petals, a pearl with a star."""
    pl.shape(_scallops(_at(cx, cy, r), 1, 8, -90, .55, bulge=1.25), None, "@h")
    pl.shape(_scallops(_at(cx, cy, r), .62, 8, -67.5, .5, bulge=1.3), None, "#fff")
    pl.circle(cx, cy, r * .26, "#fff", W0)
    pl.dot(cx, cy, r * .1)


def _emblem(pl, theme, cx, cy, r, seed=0):
    """The theme's emblem, drawn inside a circle of radius r at (cx, cy)."""
    if theme == "foliage":
        _quatrefoil(pl, cx, cy, r * .95)
    elif theme == "roses":
        for k in range(5):
            _leaf(pl, _at(cx, cy, r * .95, -90 + 72 * k + 36), .3)
        _rose(pl, _at(cx, cy, r * .62), seed * 17)
    elif theme == "vines":
        _vine_leaf(pl, _at(cx - r * .1, cy - r * .55, r * .7, -150))
        _grapes(pl, _at(cx + r * .05, cy - r * .55, r * 1.25, 80))
        pl.swell(_spiral(cx + r * .4, cy - r * .5, r * .28, 180, 1.2, .3), .9, .5)
    elif theme == "waves":
        pl.blob(_poly(_arc(cx, cy, r, r, 0, 180, 14), True), None, "@v")
        _sun(pl, cx + r * .3, cy - r * .2, r * .16, 12, False, r * .16)
        _breaker(pl, _at(cx - r * .95, cy + r * .45, r * 1.25), surfer=(seed % 3 == 1))
    elif theme == "reeds":
        _heron(pl, _at(cx - r * 1.15, cy - r * 1.2, r / 17))
        for i, (dx, hh, ln) in enumerate(((.55, .9, .1), (.7, .7, .15), (-.6, .8, -.1))):
            _reed(pl, cx + dx * r, cy + r * .75, r * hh, r * ln, i == 0, .8)
        pl.line(f"M{_n(cx - r * .8)},{_n(cy + r * .58)}H{_n(cx + r * .8)}M{_n(cx - r * .5)},{_n(cy + r * .7)}H{_n(cx + r * .4)}")
    elif theme == "notes":
        _snare(pl, _at(cx, cy - r * .05, r * .62), True, True)
    elif theme == "sun":
        _sun(pl, cx, cy, r * .5, 16, True, r * .38)
    elif theme == "stars":
        _crescent(pl, _at(cx - r * .15, cy, r * .62))
        _star4(pl, cx + r * .45, cy - r * .35, r * .2)
        _star4(pl, cx + r * .55, cy + r * .3, r * .13)
        _star4(pl, cx + r * .2, cy + r * .58, r * .09)
    elif theme == "thai":
        _prajamyam(pl, _at(cx, cy, r * .85))
    elif theme == "dog":
        _tiny_dog(pl, cx - r * .45, cy + r * .6, r / 9.5)
    else:
        _quatrefoil(pl, cx, cy, r)


def _medallion(pl, cx, cy, r, theme, seed, ground=None):
    pl.circle(cx, cy, r, "#fff", W2)
    if ground:
        pl.circle(cx, cy, r - 2.4, ground, W0)
    else:
        pl.circle(cx, cy, r - 2.4, "none", W0)
    _emblem(pl, theme, cx, cy, r - 3.4, seed)


def _end_block(pl, x, y, s, theme):
    pl.rect(x, y, s, s, "#fff", W1)
    pl.rect(x + 2, y + 2, s - 4, s - 4, "none", W0)
    c, r = x + s / 2, y + s / 2
    if theme == "thai":
        _prajamyam(pl, _at(c, r, s * .4))
    elif theme == "notes":
        _drumsticks(pl, c, r, s / 26)
    elif theme == "waves":
        _scallop(pl, _at(c, r + s * .3, s * .38))
    elif theme == "sun":
        _sun(pl, c, r, s * .15, 12, False, s * .16)
    elif theme == "stars":
        _star5(pl, c, r, s * .32)
    elif theme == "reeds":
        _reed(pl, c - 2, y + s - 4, s * .7, -2, True, .8)
        _reed(pl, c + 3, y + s - 4, s * .6, 3, True, .8)
        _blade(pl, c, y + s - 4, s * .5, -8, 1.1)
    else:
        _rosette(pl, c, r, s * .36)
    for cx, cy in ((x, y), (x + s, y), (x, y + s), (x + s, y + s)):
        pl.circle(cx, cy, 1.4, "#000", 0)


def _coil(S, T, r0, turns, shrink, toward):
    """A spiral leaving point S tangent to direction T, curling to the side of unit normal `toward`."""
    C = (S[0] + r0 * toward[0], S[1] + r0 * toward[1])
    a0 = math.atan2(S[1] - C[1], S[0] - C[0])
    cw = 1 if (-math.sin(a0) * T[0] + math.cos(a0) * T[1]) > 0 else -1
    return _spiral(C[0], C[1], r0, math.degrees(a0), turns, shrink, cw, max(14, int(turns * 30))), C


def _rinceau(pl, G, x0, x1, yc, U, theme, seed, top_first=True):
    """The running scroll for one side, drawn outward in local +x from x0 to x1 through frame G, in a band
    U tall. A wavy stem; from each crest a branch coils into the hollow beneath it and ends in a flower;
    leaves and berries take the outer side of each crest."""
    rnd = random.Random(seed)
    A = U * .19
    L = max(32, U * {"vines": .86, "thai": .8}.get(theme, .84))
    nh = max(2, round((x1 - x0) / L))
    L = (x1 - x0) / nh
    sg = 1 if top_first else -1
    ys = lambda u: yc - sg * A * math.sin(PI * (u - x0) / L)
    stem = [(x0 + (x1 - x0) * i / (nh * 14), ys(x0 + (x1 - x0) * i / (nh * 14))) for i in range(nh * 14 + 1)]
    r0 = U * .29
    for j in range(nh):                          # outer side of each crest, behind the stem
        s = sg if j % 2 == 0 else -sg            # +1: this crest is above the axis
        uc = x0 + L * (j + .5)
        yo = ys(uc) - s * U * .02
        if theme == "foliage":
            _acanthus(pl, G @ _at(uc + L * .3, yo + s * U * .02, U / 46, -180 + 12 * s, False, s < 0))
        elif theme == "roses":
            _leaf(pl, G @ _at(uc + L * .32, yo + s * U * .03, U * .34, -180 + 10 * s), .28)
        elif theme == "vines":
            pl.swell(_mp(G, _coil((uc + L * .1, yo), (1, 0), U * .1, 1.5, .2, (0, -s))[0]), .9, .5)
            _leaf(pl, G @ _at(uc - L * .05, yo, U * .26, -180 + 30 * s), .28)
        elif theme == "thai":
            _kanok(pl, G @ _at(uc + L * .32, yo + s * U * .02, U / 62, -180 + 14 * s, False, s > 0))
    pl.swell(_mp(G, stem), 2.1, 1.3, .5)
    for j in range(nh):
        s = sg if j % 2 == 0 else -sg
        uc = x0 + L * (j + .5)
        S = (uc - L * .1, ys(uc - L * .1))
        N = (0, s)
        if theme == "foliage":
            sp, C = _coil(S, (1, 0), r0, 1.05, .28, N)
            _leafy(pl, _mp(G, sp), U * .2, 3, away=G(*C), tol=.32)
            pl.circle(*sp[-1], U * .045, "#fff", W0, G)
            pl.dot(*sp[-1], U * .02, G)
        elif theme == "roses":
            sp, C = _coil(S, (1, 0), r0 * .9, .5, .6, N)
            pl.swell(_mp(G, sp), 1.4, 1.)
            k = len(sp) // 3
            _leaf(pl, G @ _at(*sp[k], U * .26, 90 * s + 30 * s), .32)
            _rose(pl, G @ _at(C[0] + U * .02, C[1] + s * U * .01, U * .2), rnd.uniform(0, 72))
        elif theme == "vines":
            if j % 2 == 0:
                sp, C = _coil(S, (1, 0), r0 * .8, 1.6, .15, N)
                pl.swell(_mp(G, sp), 1.2, .6)
                _vine_leaf(pl, G @ _at(uc + L * .12, ys(uc + L * .12), U * .36, 90 * s - 15 * s))
            else:
                pl.swell(_mp(G, [(uc - L * .1, ys(uc - L * .1)), (uc - L * .02, yc + s * U * .05)]), 1.2, .8)
                _grapes(pl, G @ _at(uc - L * .02, yc + s * U * .02, U * .45, 90 * s - 8 * s))
        elif theme == "thai":
            sp, C = _coil(S, (1, 0), r0 * .95, 1.0, .32, N)
            pl.swell(_mp(G, sp), 1.6, .7)
            i = int(len(sp) * .2)
            a = math.degrees(math.atan2(sp[i + 1][1] - sp[i][1], sp[i + 1][0] - sp[i][0]))
            _kanok(pl, G @ _at(*sp[i], U / 58, a - 150 * s, False, s > 0))
            pl.shape(_scallops(G, U * .1, 6, 0, .7, *C), None, "#fff")
            pl.dot(*C, U * .035, G)


def headpiece(width=560, seed=0, theme="foliage", height=48):
    """A decorative band to sit above a card title: ruled frame, end blocks, a running pattern each side,
    a central medallion with the theme's emblem. Height 40-60."""
    w, h = float(width), float(max(40, min(60, height)))
    theme = theme if theme in HEADPIECE_THEMES else "foliage"
    pl = _Plate(w, h, f"hp{w}{h}{seed}{theme}", f"kbook-head kbook-{theme}")
    rnd = random.Random(seed * 7919 + len(theme))
    h = round(h)
    t0, t1 = 5.25, h - 5.25                # the band inside the rules (rules on the device grid)
    yc, bh = h / 2, t1 - t0
    eb = bh                                # end block size
    R = h / 2 - 1.5                        # medallion radius
    cx = w / 2
    ground = {"foliage": "@v", "vines": "@v", "roses": "@v", "thai": "@t", "stars": "@V"}.get(theme)
    if ground:
        pl.rect(eb, t0, w - 2 * eb, bh, ground, 0)
    xa, xb = cx + R + 3, w - eb - 3        # running field, right side
    mir = _T(w, 0) @ _S(-1, 1)
    sides = ((ID, True), (mir, seed % 2 == 0))
    if theme in ("foliage", "vines", "roses", "thai"):
        for G, tf in sides:
            _rinceau(pl, G, xa, xb, yc, bh, theme, seed + (G is ID), tf)
    elif theme == "waves":
        pl.rect(eb, t0, w - 2 * eb, bh * .55, "@v", 0)
        for G, _ in sides:
            u, k = xa - 6, 0
            while u < xb - 8:
                s = bh * (.95 if k % 2 == 0 else .7) * rnd.uniform(.9, 1.05)
                _breaker(pl, G @ _at(u, t1 - 1.5, s), True, surfer=(k == 1 and G is ID and seed % 3 == 0 and s > 24))
                u += s * .78
                k += 1
            # gulls
            for _ in range(2):
                gx, gy = rnd.uniform(xa + 20, xb - 20), t0 + rnd.uniform(3, 7)
                pl.line(f"M{_n(gx - 3)},{_n(gy)}Q{_n(gx - 1.5)},{_n(gy - 2)} {_n(gx)},{_n(gy)}Q{_n(gx + 1.5)},{_n(gy - 2)} {_n(gx + 3)},{_n(gy)}", G, .7)
        pl.rect(eb, t1 - 1.5, w - 2 * eb, 1.5, "#fff", 0)
        _sea_lines(pl, eb, w - eb, t1 - 1.6, t1, seed, 2)
    elif theme == "reeds":
        _sea_lines(pl, eb + 2, w - eb - 2, t1 - 7, t1 - 1, seed, 2.2)
        for G, _ in sides:
            u = xa
            while u < xb - 4:
                hh = bh * rnd.uniform(.55, .95)
                lean = rnd.uniform(-5, 5)
                x, yb = G(u, t1 - 4)
                _reed(pl, x, yb, hh, lean * (1 if G is ID else -1), rnd.random() < .35)
                if rnd.random() < .5:
                    x2, _ = G(u + 2, 0)
                    _blade(pl, x2, yb, hh * .6, rnd.choice((-1, 1)) * rnd.uniform(6, 12))
                u += rnd.uniform(5, 11)
            for _ in range(2):    # ducks in flight
                gx, gy = rnd.uniform(xa + 30, xb - 30), t0 + rnd.uniform(4, 9)
                gx, gy = G(gx, gy)
                pl.line(f"M{_n(gx - 3.5)},{_n(gy - 1)}Q{_n(gx - 1.5)},{_n(gy - 2.5)} {_n(gx)},{_n(gy)}Q{_n(gx + 1.5)},{_n(gy - 2.5)} {_n(gx + 3.5)},{_n(gy - 1)}", None, .8)
        if seed % 2 == 0:
            x, yb = (xb - 30, t1 - 4) if seed % 4 == 0 else mir(xb - 30, t1 - 4)
            _tiny_dog(pl, x, yb, .95, seed % 4 != 0)
    elif theme == "notes":
        sp = bh / 6.5
        for G, _ in sides:
            xs0, xs1 = (xa, xb) if G is ID else (mir(xb, 0)[0], mir(xa, 0)[0])
            ytop = yc - 2 * sp
            pl.line("".join(f"M{_n(xs0)},{_n(ytop + i * sp)}H{_n(xs1)}" for i in range(5)))
            pl.line(f"M{_n(xs1)},{_n(ytop)}V{_n(ytop + 4 * sp)}" if G is ID else f"M{_n(xs0)},{_n(ytop)}V{_n(ytop + 4 * sp)}", None, W1)
            if G is ID:
                pl.line(f"M{_n(xs1 - 2.4)},{_n(ytop)}V{_n(ytop + 4 * sp)}")
            else:
                _clef(pl, xs0 + sp * 1.6, ytop, sp)
            x = xs0 + (sp * 5 if G is not ID else sp * 2)
            bar = 0
            while x < xs1 - sp * 4:
                kind = rnd.random()
                pos = rnd.randint(-3, 5)
                yn = ytop + 4 * sp - pos * sp / 2
                up = pos < 4
                if kind < .4 and x < xs1 - sp * 7:   # beamed pair
                    pos2 = max(-3, min(5, pos + rnd.choice((-2, -1, 1, 2))))
                    yn2 = ytop + 4 * sp - pos2 * sp / 2
                    t1_ = _note(pl, x, yn, sp, True)
                    t2_ = _note(pl, x + sp * 2.6, yn2, sp, True)
                    top = min(t1_[1], t2_[1])
                    pl.line(f"M{_n(t1_[0])},{_n(t1_[1])}V{_n(top)}M{_n(t2_[0])},{_n(t2_[1])}V{_n(top)}", None, max(.7, sp * .14))
                    pl.shape(f"M{_n(t1_[0] - .3)},{_n(top)}L{_n(t2_[0] + .3)},{_n(top)}V{_n(top + sp * .45)}H{_n(t1_[0] - .3)}Z", None, "#000", 0)
                    x += sp * 5.2
                else:
                    _note(pl, x, yn, sp, up, 1 if kind < .7 else 0, kind > .88)
                    x += sp * 3.2
                bar += 1
                if bar % 3 == 0 and x < xs1 - sp * 4:
                    pl.line(f"M{_n(x - sp * .6)},{_n(ytop)}V{_n(ytop + 4 * sp)}")
                    x += sp * .8
            # ledger flourish
    elif theme == "sun":
        # a glory: rays from the centre across the band, clouds over them
        d = ""
        n = 46
        for i in range(n):
            a = -PI / 2 + PI * (i + .5) / n
            ca, sa = math.cos(a), math.sin(a)
            r0 = R + 3
            # intersect ray with the band rectangle [eb, w-eb] x [t0, t1]
            tx = (w - eb - 2 - cx) / ca if ca > 1e-6 else 1e9
            ty = ((t1 - yc) / sa if sa > 0 else (t0 - yc) / sa) if abs(sa) > 1e-6 else 1e9
            r1 = min(tx, ty) * (1 if i % 2 == 0 else .8)
            if r1 > r0 + 2:
                for sx in (1, -1):
                    d += f"M{_n(cx + sx * ca * r0)},{_n(yc + sa * r0)}L{_n(cx + sx * ca * r1)},{_n(yc + sa * r1)}"
        pl.line(d)
        for G, _ in sides:
            for k in range(2):
                c0 = xa + 20 + (xb - xa) * (.12 + .5 * k) + rnd.uniform(-10, 10)
                c1 = c0 + rnd.uniform(46, 70)
                a, b = G(c0, 0)[0], G(c1, 0)[0]
                _cloud(pl, min(a, b), max(a, b), t1 - 4 - k * 6, bh * (.32 if k else .38), seed + k)
            if seed % 3 == 0 and G is ID:
                _ball(pl, xb - 12, t1 - 6, 4)
    elif theme == "stars":
        for G, _ in sides:
            for _ in range(int((xb - xa) / 9)):
                x, y = G(rnd.uniform(xa + 3, xb - 3), rnd.uniform(t0 + 3, t1 - 3))
                r = rnd.choice((1.6, 2.2, 2.2, 3, 3.8))
                pl.circle(x, y, r * .55, "#fff", 0)
                _star4(pl, x, y, r * 1.2, r * .26)
        _constellation(pl, xa + (xb - xa) * .45, t0 + 3, bh - 6, seed)
        # a falling star
        x0_, y0_ = mir(xa + (xb - xa) * .3, t0 + 6)
        pl.rect(x0_ - 30, y0_ - 2.5, 30, 5, "#fff", 0)
        pl.swell([(x0_ - 28, y0_ + 2), (x0_, y0_ - 1)], .5, 1.6)
        _star5(pl, x0_ + 1, y0_ - 1, 3.6)
    # frame rules over the ground
    pl.line(f"M0,.75H{_n(w)}M0,{h - .75}H{_n(w)}", None, W2, ' shape-rendering="crispEdges"')
    pl.line(f"M{_n(eb)},{_n(t0 - .5)}H{_n(w - eb)}M{_n(eb)},{_n(t1 + .5)}H{_n(w - eb)}")
    for x in (0, w - eb):
        _end_block(pl, x, t0 - 1.2, eb + 2.4 if False else eb, theme)
    _medallion(pl, cx, yc, R, theme, seed, "@t" if theme in ("foliage", "roses", "vines") else None)
    return pl.svg()


def _clef(pl, x, ytop, sp):
    """A treble clef on a staff whose top line is ytop."""
    g = ytop + 3 * sp     # the G line
    pts = (_bezs((x + sp * .1, ytop + 5.4 * sp), ((x - sp * .9, ytop + 5.6 * sp), (x - sp * .6, ytop + 4.2 * sp), (x, ytop + 4.5 * sp)))
           + _bezs((x + sp * .2, ytop + 4.6 * sp), ((x + sp * .4, ytop + 2 * sp), (x + sp * 1.2, ytop - .6 * sp), (x + sp * .5, ytop - 1.4 * sp)),
                   ((x - sp * .3, ytop - .4 * sp), (x - sp * 1.4, ytop + 2.2 * sp), (x - sp * .9, ytop + 3.3 * sp)),
                   ((x - sp * .4, ytop + 4.4 * sp), (x + sp * 1.4, ytop + 4.2 * sp), (x + sp * 1.1, ytop + 3 * sp)),
                   ((x + sp * .8, ytop + 1.8 * sp), (x - sp * .6, ytop + 2.1 * sp), (x - sp * .2, g + sp * .3)))[1:])
    pl.swell(pts, .6, .9, sp * .3)
    pl.dot(x - sp * .25, ytop + 5.3 * sp, sp * .32)


def _constellation(pl, x, y, h, seed):
    """Easter egg: a little constellation that spells P."""
    s = h / 10
    pts = [(x, y + 10 * s), (x, y + 5.2 * s), (x, y), (x + 4.6 * s, y + .6 * s), (x + 5.6 * s, y + 3 * s), (x + 3.8 * s, y + 5.2 * s)]
    pl.line(_poly(pts + [(x, y + 5.2 * s)]), None, .6, ' stroke-dasharray="1.2 1.6"')
    for i, (px, py) in enumerate(pts):
        pl.circle(px, py, 1.8, "#fff", 0)
        _star4(pl, px, py, 2.4 if i % 2 == 0 else 1.8)


# ---------------------------------------------------------------------------------------------
# cartouches
# ---------------------------------------------------------------------------------------------

def _spray(pl, G, x, y, size, seed=0, ang=-30):
    """A small leafy spray from (x, y) in local coords of G, reaching `size` toward angle `ang`."""
    a = math.radians(ang)
    tip = (x + size * math.cos(a), y + size * math.sin(a))
    mid = (x + size * .5 * math.cos(a - .35), y + size * .5 * math.sin(a - .35))
    pts = _bez((x, y), mid, mid, tip, 10)
    pl.swell(_mp(G, pts), 1.1, .5)
    for k, t in enumerate((.3, .55, .8)):
        p = pts[int(t * 10)]
        side = 1 if k % 2 == 0 else -1
        _leaf(pl, G @ _at(p[0], p[1], size * (.38 - .07 * k), ang + 48 * side), .3)
    pl.circle(*tip, size * .07, "#fff", W0, G)


def _swash(pl, G, x0, y0, length, amp, curl=1):
    """A calligraphic swash: a swelling hairline running out from (x0, y0), ending in a small curl.
    curl=1 curls toward -y (above), -1 toward +y."""
    x1 = x0 + length
    pts = _bezs((x0, y0), ((x0 + length * .25, y0 - curl * amp * .7), (x0 + length * .6, y0 + curl * amp * .9), (x1, y0 - curl * amp * .1)), n=24)
    r = amp * .55
    sp = _spiral(x1, y0 - curl * amp * .1 - curl * r, r, 90 * curl, 1.1, .3, -curl)
    pl.swell(_mp(G, pts + sp[1:]), .5, .5, 1.7)
    # a hairline companion
    pl.swell(_mp(G, _bezs((x0 + length * .12, y0 - curl * amp * .5), ((x0 + length * .3, y0 - curl * amp * 1.1), (x0 + length * .5, y0 - curl * amp * .3),
                                                                      (x0 + length * .62, y0 - curl * amp * .1)), n=14)), .4, .4, .6)
    pl.dot(*sp[-1], .8, G)


def _field_lines(pl, field, insets=(0, 3.4, 5.4), band="@h"):
    """Draw a moulded frame round a field: heavy outer line, toned band, two hairlines, white centre."""
    pl.shape(field(insets[0]), None, band, W2)
    pl.shape(field(insets[1]), None, "#fff", W0)
    if len(insets) > 2:
        pl.shape(field(insets[2]), None, "none", W0)


def _egg(pl, kind, x, y, s=1.):
    """Place one Easter egg standing on (x, y)."""
    if kind == "dog":
        _tiny_dog(pl, x - 5 * s, y, .9 * s)
    elif kind == "ball":
        _ball(pl, x, y - 3.6 * s, 3.6 * s)
    elif kind == "sticks":
        _drumsticks(pl, x, y - 2.4 * s, .7 * s, 74)
    elif kind == "P":
        pl.circle(x, y - 5 * s, 5 * s, "#fff", W0)
        _monogram(pl, x - 2.6 * s, y - 2.2 * s, 5.6 * s)


_EGGS = ("dog", "ball", "sticks", "P")


def cartouche(width=560, height=70, seed=0, style="banner"):
    """An engraved title cartouche with scroll terminals; the centre is left white for an HTML title
    laid over it (a 26 px serif fits comfortably at the default 560 x 70)."""
    w, h = float(width), float(max(48, height))
    style = style if style in CARTOUCHE_STYLES else "banner"
    pl = _Plate(w, h, f"ct{w}{h}{seed}{style}", f"kbook-cart kbook-{style}")
    rnd = random.Random(seed * 31 + len(style))
    cx, cy = w / 2, h / 2
    mir = _T(w, 0) @ _S(-1, 1)
    egg = _EGGS[seed % 4]
    if style == "banner":
        Lt = min(70, w * .13)
        a, b = h * .2, h * .76
        d = h * .19
        L = Lt + 6
        for G in (ID, mir):
            sh = lambda pts: _mp(G, pts)
            # the tail, seen from behind, with a swallowtail notch and a little upward flare
            tail = [(L + 12, a + d), (Lt * .5, a + d - 1.5), (2, a + d - 3), (2 + Lt * .32, (a + b) / 2 + d - 1.5),
                    (2, b + d - 3), (Lt * .5, b + d - 1.5), (L + 12, b + d)]
            pl.shape(_poly(sh(tail), True), None, "@v", W1)
            pl.line(_poly(sh([(L + 12, a + d + 2.6), (Lt * .5, a + d + 1.1), (6, a + d - .2)])), None)
            pl.line(_poly(sh([(L + 12, b + d - 2.6), (Lt * .5, b + d - 4.1), (6, b + d - 5.8)])), None)
            # the fold
            pl.shape(_poly(sh([(L, b), (L + 12, b + d), (L + 12, b)]), True), None, "@X", W0)
            # a scroll spray above the tail
            _spray(pl, G, L - 2, a + d - 3, min(34, Lt * .6), seed, -158)
        # the front of the ribbon, arched a little
        R = w - L
        bow = min(3.5, h * .05)
        yb = lambda x, y0: y0 - bow * (1 - ((x - cx) / (cx - L)) ** 2)
        xs = [L + (R - L) * i / 24 for i in range(25)]
        top = [(x, yb(x, a)) for x in xs]
        bot = [(x, yb(x, b)) for x in xs[::-1]]
        pl.shape(_cr(top) + "L" + _cr(bot)[1:] + "Z", None, "@h", W2)
        top3 = [(x, yb(x, a + 3)) for x in xs]
        bot3 = [(x, yb(x, b - 3)) for x in xs[::-1]]
        pl.shape(_cr(top3) + "L" + _cr(bot3)[1:] + "Z", None, "#fff", W0)
        pl.line(_cr([(x, yb(x, a + 4.8)) for x in xs]))
        pl.line(_cr([(x, yb(x, b - 4.8)) for x in xs]))
        for x0, sgn in ((L, 1), (R, -1)):     # the ribbon turning at each end: ruled shading
            dd = ""
            for k, off in enumerate((1.6, 3.4, 5.4, 7.8, 10.6, 14)):
                x = x0 + sgn * off
                dd += f"M{_n(x)},{_n(yb(x, a + 3.6))}L{_n(x)},{_n(yb(x, b - 3.6))}"
            pl.line(dd)
        for G in (ID, mir):
            _swash(pl, G, cx + 14, yb(cx, a) - 4.5, (R - L) * .3, a * .5, 1)
            _swash(pl, G, cx + 14, yb(cx, b) + 4.5, (R - L) * .3, (h - b) * .45, -1)
        # crest above and pendant below the centre
        _crest(pl, cx, yb(cx, a), yb(cx, a) - .5, seed)
        _pendant(pl, cx, yb(cx, b), h - yb(cx, b) - 1, seed)
        _egg(pl, egg, R - 16 if seed % 2 else L + 18, yb(L + 18, a) - .8, .85)
    elif style == "shield":
        l0, r0, t0, b0 = w * .085, w * .915, h * .14, h * .86
        cn, pk = h * .13, min(16, w * .03)

        def field(i):
            l, r, t, bb = l0 + i, r0 - i, t0 + i, b0 - i
            c = cn + i * .4
            p = pk - i * .8
            mid = (t + bb) / 2
            return (f"M{l0 + c},{t}H{r0 - c}Q{r0 - c},{t0 + c} {r},{t0 + c}"
                    f"C{r},{mid - 6} {r + p * .5},{mid - 2} {r + p},{mid}C{r + p * .5},{mid + 2} {r},{mid + 6} {r},{b0 - c}"
                    f"Q{r0 - c},{b0 - c} {r0 - c},{bb}H{l0 + c}Q{l0 + c},{b0 - c} {l},{b0 - c}"
                    f"C{l},{mid + 6} {l - p * .5},{mid + 2} {l - p},{mid}C{l - p * .5},{mid - 2} {l},{mid - 6} {l},{t0 + c}"
                    f"Q{l0 + c},{t0 + c} {l0 + c},{t}Z")
        for G in (ID, mir):    # C-scroll terminals: two leafy volutes leaving the point
            px = l0 - pk
            for sv in (-1, 1):
                pts = (_bezs((px + 1, cy), ((px - 6, cy + sv * 2), (px - 10, cy + sv * 10), (px - 8, cy + sv * h * .3)))
                       + _spiral(px - 8 + h * .1, cy + sv * h * .3, h * .1, 180, 1.05, .3, -sv)[1:])
                _leafy(pl, _mp(G, pts), h * .13, 3, away=G(px - 6, cy), tol=.25)
                pl.dot(*pts[-1], 1.1, G)
            _spray(pl, G, l0 + cn * .5, t0, min(34, w * .07), seed, -170)
            _spray(pl, G, l0 + cn * .5, b0, min(34, w * .07), seed + 1, 170)
        _field_lines(pl, lambda i: _tp(field(i)), (0, 3.2, 5))
        for G in (ID, mir):   # pearls at the concave corners
            for yy in (t0 + cn * .55, b0 - cn * .55):
                pl.circle(l0 + cn * .55, yy, 1.6, "#000", 0, G)
        for G in (ID, mir):
            _swash(pl, G, cx + 16, t0 - 3.5, (r0 - l0) * .26, t0 * .55, 1)
            _swash(pl, G, cx + 16, b0 + 3.5, (r0 - l0) * .26, (h - b0) * .5, -1)
        _crest(pl, cx, t0, t0 + 1, seed, shell=True)
        _pendant(pl, cx, b0, h - b0 - .5, seed)
        _egg(pl, egg, r0 - cn - 14 if seed % 2 else l0 + cn + 16, t0 - .8, .7)
    elif style == "oval":
        A, B = w * .37, h * .41
        n = 3.2

        def field(i):
            pts = []
            for k in range(64):
                t = 2 * PI * k / 64
                c, s_ = math.cos(t), math.sin(t)
                x = (A - i) * math.copysign(abs(c) ** (2 / n), c)
                y = (B - i) * math.copysign(abs(s_) ** (2 / n), s_)
                pts.append((cx + x, cy + y))
            return _cr(_dp(pts, .15), True)
        for G in (ID, mir):    # laurel sprays crossing at the ends, a bow, and volute terminals
            ex = cx - A
            for sv in (-1, 1):
                pts = _bezs((ex + 10, cy + sv * B * .9), ((ex - 4, cy + sv * B * .9), (ex - 14, cy + sv * B * .4), (ex - 18, cy - sv * 2)))
                pl.swell(_mp(G, pts), 1.3, .7)
                for k in range(1, 7):
                    p = pts[min(len(pts) - 1, k * len(pts) // 7)]
                    _leaf(pl, G @ _at(p[0], p[1], 8.5 - k * .5, 205 + sv * 55 - k * 6 * sv), .3)
                    _leaf(pl, G @ _at(p[0], p[1], 8 - k * .5, 160 - sv * 60 + k * 5 * sv), .3)
                pts = (_bezs((ex - 16, cy + sv * 1), ((ex - 24, cy + sv * 3), (ex - 30, cy + sv * B * .4), (ex - 40, cy + sv * B * .55)))
                       + _spiral(ex - 40, cy + sv * B * .55 - sv * B * .3, B * .3, 90 * sv, 1.1, .3, sv)[1:])
                if ex - 56 > 0:
                    pl.swell(_mp(G, pts), 2, .6, .6)
                    pl.dot(*pts[-1], 1.2, G)
            pl.circle(ex - 16, cy, 3, "#fff", W1, G)
            pl.dot(ex - 16, cy, 1.1, G)
        _field_lines(pl, field, (0, 4.2, 6))
        # pearls set in the moulding
        npl = int(2 * (2 * A) / 24)
        for k in range(npl):
            t = 2 * PI * (k + .5) / npl
            c, s_ = math.cos(t), math.sin(t)
            x = (A - 2.1) * math.copysign(abs(c) ** (2 / n), c)
            y = (B - 2.1) * math.copysign(abs(s_) ** (2 / n), s_)
            pl.circle(cx + x, cy + y, 1.5, "#fff", W0)
        for G in (ID, mir):
            _swash(pl, G, cx + 14, cy - B - 3.5, A * .45, (cy - B) * .55, 1)
            _swash(pl, G, cx + 14, cy + B + 3.5, A * .45, (cy - B) * .5, -1)
        _crest(pl, cx, cy - B, cy - B, seed)
        _pendant(pl, cx, cy + B, h - cy - B - .5, seed)
        _egg(pl, egg, cx + A * .72 if seed % 2 else cx - A * .72, cy - B * .93, .7)
    else:  # tablet: a tabula ansata with acanthus ears
        l0, r0, t0, b0 = w * .1, w * .9, h * .16, h * .84
        ch = 5

        def field(i):
            l, r, t, bb = l0 + i, r0 - i, t0 + i, b0 - i
            c = ch
            return (f"M{l + c},{t}H{r - c}L{r},{t + c}V{bb - c}L{r - c},{bb}H{l + c}L{l},{bb - c}V{t + c}Z")
        for G in (ID, mir):
            # dovetail handle, ruled, with a pearl
            ear = [(l0 + 1, cy - h * .2), (l0 - w * .05, cy - h * .34), (l0 - w * .05, cy + h * .34), (l0 + 1, cy + h * .2)]
            pl.shape(_poly(_mp(G, ear), True), None, "@v", W1)
            pl.circle(l0 - w * .05 + 6, cy, 2.6, "#fff", W0, G)
            pl.dot(l0 - w * .05 + 6, cy, 1, G)
            # acanthus ears: leafy scrolls rolling away from the handle, up and down
            ex = l0 - w * .05
            for sv in (-1, 1):
                pts = (_bezs((ex + 2, cy + sv * h * .3), ((ex - 6, cy + sv * h * .36), (ex - 12, cy + sv * h * .2), (ex - 14, cy + sv * 3)))
                       + _spiral(ex - 14 + h * .1, cy + sv * 3, h * .1, 180, 1.0, .3, sv)[1:])
                _leafy(pl, _mp(G, pts), h * .12, 3, away=G(ex - 6, cy + sv * h * .12), tol=.25)
                pl.dot(*pts[-1], 1.1, G)
            _spray(pl, G, l0 + 8, t0, min(30, w * .06), seed, -165)
            _spray(pl, G, l0 + 8, b0, min(30, w * .06), seed + 2, 165)
        _field_lines(pl, lambda i: _tp(field(i)), (0, 3.2, 5), "@v")
        for G in (ID, mir):
            for yy in (t0, b0):
                pl.circle(l0, yy, 2.2, "#fff", W0, G)
                pl.dot(l0, yy, .9, G)
        for G in (ID, mir):
            _swash(pl, G, cx + 14, t0 - 3.5, (r0 - l0) * .26, t0 * .55, 1)
            _swash(pl, G, cx + 14, b0 + 3.5, (r0 - l0) * .26, (h - b0) * .5, -1)
        _crest(pl, cx, t0, t0, seed)
        _pendant(pl, cx, b0, h - b0 - .5, seed)
        _egg(pl, egg, r0 - 22 if seed % 2 else l0 + 22, t0 - .8, .7)
    return pl.svg()


def _crest(pl, x, y, room, seed, shell=False):
    """A small crest standing on (x, y), at most `room` tall: a shell, or acanthus round a pearl."""
    room = max(6, room)
    if shell:
        _scallop(pl, _at(x, y + 1, room * .95))
        return
    s = room / 16
    _acanthus(pl, _at(x - 1, y, s * .85, -160, False, True))
    _acanthus(pl, _at(x + 1, y, s * .85, -20))
    pl.circle(x, y - room * .4, room * .3, "#fff", W1)
    _star4(pl, x, y - room * .4, room * .22)


def _pendant(pl, x, y, room, seed):
    """A pendant hanging from (x, y) within `room`: acanthus pair, a pearl, a falling dot."""
    room = max(6, room)
    s = room / 18
    _acanthus(pl, _at(x - 1, y, s, 160, False, False))
    _acanthus(pl, _at(x + 1, y, s, 20, False, True))
    pl.circle(x, y + room * .38, room * .2, "#fff", W0)
    pl.dot(x, y + room * .38, room * .08)
    pl.dot(x, y + room * .8, room * .09)


# ---------------------------------------------------------------------------------------------
# culs-de-lampe
# ---------------------------------------------------------------------------------------------

_EMBLEM_OF = {"dog": "dog", "drums": "notes", "jazz": "notes", "coast": "waves", "surf": "waves", "portland": "roses"}
_FLAVOUR = {"roses": "roses", "portland": "roses", "vines": "vines", "thai": "thai", "waves": "sea", "coast": "sea",
            "surf": "sea", "reeds": "reeds"}


def _arm(pl, G, x0, y0, x1, y1, thick, flavour, rnd, curl_up=True):
    """One arm of a cul-de-lampe, local +x outward: a stem dipping from (x0, y0) to (x1, y1) and rolling
    into a volute, dressed for the flavour."""
    rv = max(3.5, thick * 1.0)
    D = x1 - x0
    pts = _bezs((x0, y0), ((x0 + D * .3, y0 - thick * 1.5), (x1 - D * .3, y1 - thick * 1.7), (x1, y1)), n=30)
    sp = _spiral(x1 - rv, y1, rv, 0, 1.05, .3, 1)
    cu = 1
    line = pts + sp[1:]
    if flavour == "thai":
        pl.swell(_mp(G, line), max(1.4, thick * .26), .6)
        nk = max(2, int((x1 - x0) / (thick * 2.8)))
        for k in range(nk):
            p = pts[int((k + .5) / nk * (len(pts) - 1))]
            _kanok(pl, G @ _at(p[0], p[1], thick / 9.5 * (1 - .3 * k / nk), -24 if k % 2 == 0 else 204, False, k % 2 == 1))
        pl.circle(x1 - rv, y1, rv * .45, "#fff", W0, G)
        pl.dot(x1 - rv, y1, rv * .18, G)
        return
    if flavour == "sea":
        pl.swell(_mp(G, line), max(1.2, thick * .22), .6, thick * .1)
        s = thick * 2.3
        _breaker(pl, G @ _at(x1 - s * .95, y1 + thick * .8, s), True)
        nk = max(1, int((x1 - x0 - s) / (thick * 2.4)))
        for k in range(nk):
            p = pts[int((k + .5) / nk * (len(pts) - 1) * .7)]
            pl.swell(_mp(G, _spiral(p[0], p[1] - thick * .45, thick * .45, 90, .9, .35, -1)), .9, .5)
        return
    pl.swell(_mp(G, line), max(1.6, thick * .34), .6, thick * .12)
    nl = max(3, min(7, int(D / (thick * 1.7))))
    for i in range(nl):
        t = .1 + .78 * i / (nl - 1)
        j = int(t * (len(pts) - 1))
        p, q = pts[j], pts[min(len(pts) - 1, j + 1)]
        a = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        up = i % 2 == 0
        sc = thick / 10.5 * (1.1 - .45 * t)
        _acanthus(pl, G @ _at(p[0], p[1], sc, a - (34 if up else -30), False, not up))
    pl.dot(*sp[-1], max(.8, rv * .12), G)
    _acanthus(pl, G @ _at(x0 + thick * .2, y0 - thick * .2, thick / 11, -62))
    # a secondary C-scroll hanging under the arm
    j = int(len(pts) * .52)
    b0 = pts[j]
    r2 = thick * .62
    sub = _bezs(b0, ((b0[0] + D * .04, b0[1] + thick * .8), (b0[0] + D * .14, b0[1] + thick * 1.2), (b0[0] + D * .24, b0[1] + thick * 1.1)), n=12)
    e = sub[-1]
    sub += _spiral(e[0], e[1] + r2, r2, -90, 1.0, .3, 1)[1:]
    pl.swell(_mp(G, sub), max(1.2, thick * .2), .5, thick * .06)
    _acanthus(pl, G @ _at(*sub[6], thick / 16, 30, False, True))
    pl.dot(*sub[-1], .8, G)
    if flavour in ("roses",):
        _rose(pl, G @ _at(x1 - rv, y1, rv * .8), rnd.uniform(0, 70))
    elif flavour == "vines":
        _grapes(pl, G @ _at(x1 - rv * 1.3, y1 + rv * .6, rv * 2.2, 100))


def _cascade(pl, cx, ya, y1, spread, theme, seed, centre=True, stem_top=None):
    """The inverted triangle: two arms at height ya reaching `spread` each way, then rows of tendrils
    narrowing to a pendant at y1."""
    rnd = random.Random(seed)
    flav = _FLAVOUR.get(theme, "foliage")
    H = y1 - ya
    thick = max(4.5, min(10, spread * .065, H * .2 + 2, (ya - 1) / 1.9 if centre else 99))
    mir = _T(2 * cx, 0) @ _S(-1, 1)
    # rows of tendrils under the arms
    n = max(1, int((H - thick * 2) / max(11, thick * 2.1)))
    dy = (H - thick * 2.2) / (n + 1)
    for G in (ID, mir):
        for i in range(n):
            y = ya + thick * .9 + dy * (i + 1)
            f = 1 - (i + 1) / (n + 1)
            hw = spread * .74 * f ** 1.15
            if hw < 8:
                continue
            r = max(2.6, min(thick * .7, hw * .22))
            pts = _bezs((cx, y - dy * .45), ((cx + hw * .3, y - dy * .5), (cx + hw * .65, y + r * .2), (cx + hw - r, y + r * .3)), n=16)
            sp = _spiral(cx + hw - r, y + r * .3 - r, r, 90, 1.0, .3, -1)
            pl.swell(pts + sp[1:], 1.6, .5, .6, m=G)
            kk = len(pts) // 2
            if flav == "thai":
                _kanok(pl, G @ _at(*pts[kk], max(.25, hw / 70), 18, False, False))
            elif flav == "roses":
                _leaf(pl, G @ _at(*pts[kk], min(14, hw * .4), 40), .3)
                _bud(pl, G @ _at(*pts[int(len(pts) * .25)], min(11, hw * .3), -60))
            elif flav == "vines":
                _vine_leaf(pl, G @ _at(*pts[kk], min(12, hw * .34), 55))
            elif flav == "sea":
                pl.circle(*G(*sp[-1]), max(1.2, r * .3), "#fff", W0)
                if i % 2 == 0:
                    _breaker(pl, G @ _at(pts[kk][0] - hw * .1, pts[kk][1] + 1, min(16, hw * .32)), False)
            else:
                _acanthus(pl, G @ _at(*pts[kk], min(1.0, hw / 30), 28, False, True))
                _acanthus(pl, G @ _at(*pts[kk // 2], min(.7, hw / 44), -38))
            if flav != "sea":
                pl.circle(*sp[-1], max(.9, r * .2), "#000", 0, G) if False else pl.dot(*G(*sp[-1]), max(.8, r * .16))
        _arm(pl, G, cx + 2, ya, cx + spread - thick * 1.2, ya + thick * .3, thick, flav, rnd)
    # the stem and the pendant
    st = ya if stem_top is None else stem_top
    pl.swell([(cx, st), (cx, y1 - 9)], max(2, thick * .35), .9)
    pl.circle(cx, y1 - 7, 2.6, "#fff", W0)
    pl.dot(cx, y1 - 7, 1)
    pl.dot(cx, y1 - 2.4, 1.3)
    if centre:
        r = max(4.5, min(thick * 1.3, H * .2))
        if flav == "thai":
            pl.circle(cx, ya, r, "#fff", W1)
            _prajamyam(pl, _at(cx, ya, r * .9))
        elif flav == "roses":
            _rose(pl, _at(cx, ya, r), seed * 13)
        elif flav == "sea":
            _scallop(pl, _at(cx, ya + r * .55, r * 1.1))
        else:
            _rosette(pl, cx, ya, r)


def _ground(pl, x0, x1, y, seed):
    """A ledge of ground under a still life: a ruled shadow and a few broken hairlines."""
    pl.blob(_ell((x0 + x1) / 2, y, (x1 - x0) / 2, 2.6), None, "@v")
    pl.line(f"M{_n(x0)},{_n(y)}H{_n(x1)}")


# ---- the four still lifes, drawn in a 160 x 100 box (ground at y = 100) ---------------------------------

def _still_basket(pl, m, seed, egg):
    rnd = random.Random(seed)
    k = m.k
    # handle
    outer = _arc(80, 62, 46, 54, 180, 360, 24)
    inner = _arc(80, 62, 41.5, 49.5, 360, 180, 24)
    pl.shape(_poly(_mp(m, outer + inner), True), None, "@x", W1 if k > 1.4 else W0)
    d = ""
    for a in range(186, 356, 9):     # the wicker binding round the handle
        p0 = m(80 + 41.5 * math.cos(math.radians(a)), 62 + 49.5 * math.sin(math.radians(a)))
        p1 = m(80 + 46 * math.cos(math.radians(a + 5)), 62 + 54 * math.sin(math.radians(a + 5)))
        d += f"M{_n(p0[0])},{_n(p0[1])}L{_n(p1[0])},{_n(p1[1])}"
    pl.white(d, None, 1.1)
    # leaves behind the roses
    for x, y, a, s in ((34, 56, 196, 22), (126, 54, -16, 22), (64, 34, -118, 18), (100, 32, -64, 19), (46, 46, -150, 18),
                       (116, 44, -32, 18), (82, 28, -88, 14)):
        _leaf(pl, m @ _at(x, y, s, a), .3)
    _bud(pl, m @ _at(84, 30, 16, -95))
    _bud(pl, m @ _at(56, 40, 13, -135))
    # body of the basket
    body = "M33,62C36,80 44,94 52,98H108C116,94 124,80 127,62Z"
    pl.shape(body, m, "#fff", W1)
    pen = ""
    for row in range(5):
        y = 66 + row * 6.2
        t0 = (y - 62) / 36
        xl = 33 + 19 * t0 ** 1.4 + 1.5
        xr = 127 - 19 * t0 ** 1.4 - 1.5
        x = xl - (row % 2) * 4.5
        col = 0
        while x < xr:
            xa, xb = max(xl, x), min(xr, x + 9)
            if xb - xa > 1.5:
                fill = "@h" if col % 2 == 0 else "#fff"
                pl.shape(f"M{xa},{y}H{xb}V{y + 5.2}H{xa}Z", m, fill, W0)
            x += 9
            col += 1
    # rim: a twisted rope
    pl.shape("M31,59H129V65.5H31Z", m, "#fff", W1)
    d = "".join(f"M{x},65.5L{x + 4},59" for x in range(32, 128, 3))
    pl.line(d, m, _wk(m, .45, .7))
    pl.shape("M50,98H110V101H50Z", m, "@v", W0)
    # roses heaped on the rim, back row first
    for x, y, r in sorted(((60, 46, 12.5), (84, 40, 14.5), (106, 48, 12), (43, 55, 10), (118, 56, 10), (70, 56, 11), (95, 56, 11.5)),
                          key=lambda t: t[1]):
        _rose(pl, m @ _at(x, y, r), rnd.uniform(0, 72))
    # a bud and a leaf spilling over the rim
    _bud(pl, m @ _at(36, 64, 15, 120))
    _leaf(pl, m @ _at(126, 63, 16, 60), .3)
    if egg == "P":
        pl.circle(80, 83, 6.6, "#fff", W0, m)
        x, y = m(77.2, 86.2)
        _monogram(pl, x, y, 7 * k)
    # a fallen petal
    pl.shape("M138,97C140,94 145,94 147,97C144,99 140,99 138,97Z", m, "@h")


def _still_drums(pl, m, seed, egg):
    k = m.k
    # cymbal on its stand, behind
    pl.line("M140,30V98M140,98L130,100M140,98L150,100M140,80L132,99M140,80L148,99", m, _wk(m, .55, .7))
    pl.shape(_ell(140, 28, 22, 4.2), m, "#fff", W0)
    pl.blob("M118,28C122,31 158,31 162,28C158,32.4 122,32.4 118,28Z", m, "@h")
    pl.line(_cr(_mp(m, _arc(140, 28, 15, 2.6, 0, 360, 16))), None)
    pl.shape(_ell(140, 26.6, 4, 1.8), m, "#fff", W0)
    # the lyre
    for sx in (1, -1):
        G = m @ _T(58, 0) @ _S(sx, 1) @ _T(-58, 0)
        pts = (_bezs((54, 90), ((40, 82), (34, 58), (44, 40)), ((50, 30), (46, 20), (38, 18)))
               + _spiral(38, 12, 6, 90, 1.1, .3, 1)[1:])
        pl.swell(_mp(G, pts), _wk(m, 1.5), _wk(m, .5), _wk(m, 1.1, 0))
        pl.line(_poly(_mp(G, [(p[0] + 2.2, p[1]) for p in pts[4:30]])), None)
    pl.line("M41,27H75", m, _wk(m, 1.4))
    for x in (41, 75):
        pl.circle(x, 27, 1.8, "#fff", W0, m)
    pl.line("".join(f"M{50 + i * 3},88L{48 + i * 3.6},27" for i in range(5)), m)
    pl.shape("M48,86H68V93C64,95 52,95 48,93Z", m, "@h", W0)
    _rosette(pl, *m(58, 34), 3 * k)
    # bass drum, facing us
    bx, by, R = 112, 66, 31
    pl.blob(_cr(_mp(m, _arc(bx, by, R, R, 90, 270, 16) + _arc(bx - 7, by, R * .9, R, 270, 90, 16)), True), None, "@u")
    pl.circle(bx - 3, by, R, "#fff", W1, m)
    pl.circle(bx - 3, by, R - 3.5, "@v", W0, m)
    pl.circle(bx - 3, by, R - 4.8, "#fff", W0, m)
    for i in range(10):
        a = 2 * PI * (i + .5) / 10
        c = (bx - 3 + (R - .5) * math.cos(a), by + (R - .5) * math.sin(a))
        pl.circle(*c, 1.5, "#fff", W0, m)
        pl.dot(*c, .5, m)
    # the bass drum's front head: a ring with the press mark
    pl.circle(bx - 3, by, 11, "none", W0, m)
    pl.circle(bx - 3, by, 9.5, "none", W0, m)
    x, y = m(bx - 7.2, by + 6)
    _monogram(pl, x, y, 12 * k)
    pl.line(f"M{bx - 24},{by + 26}L{bx - 30},{by + 34}M{bx + 18},{by + 26}L{bx + 24},{by + 34}", m, _wk(m, .9))
    # snare in front
    _snare(pl, m @ _at(44, 74, 22), sticks=False)
    pl.line("M30,92L26,100M58,92L62,100M44,93V100", m, _wk(m, .6))
    # sticks resting on the ground
    a, b = m(70, 99), m(108, 93)
    pl.swell([a, b], _wk(m, 1.2), _wk(m, .6))
    pl.circle(*b, _wk(m, .9), "#000", 0)
    a, b = m(74, 93), m(112, 99.5)
    pl.swell([a, b], _wk(m, 1.2), _wk(m, .6))
    pl.circle(*b, _wk(m, .9), "#000", 0)


def _still_shells(pl, m, seed, egg):
    rnd = random.Random(seed)
    k = m.k
    # sky ruled to the horizon, the sun, gulls
    pl.blob("M0,40H160V0H0Z", m, "@v")
    _sun(pl, *m(128, 22), 9 * k, 16, k > 1.5, 6 * k)
    for gx, gy in ((48, 12), (60, 18), (100, 10)):
        pl.line(f"M{gx - 4},{gy}Q{gx - 2},{gy - 2.6} {gx},{gy}Q{gx + 2},{gy - 2.6} {gx + 4},{gy}", m, _wk(m, .45, .7))
    # sea
    pl.shape("M0,40H160V78H0Z", m, "#fff", 0)
    x0, y0 = m(0, 40)
    x1, y1 = m(160, 78)
    _sea_lines(pl, x0, x1, y0, y1, seed, 3.2)
    pl.line("M0,40H160", m)
    _breaker(pl, m @ _at(108, 76, 30), True)
    _breaker(pl, m @ _at(-4, 80, 98), True, surfer=(egg in ("P", "dog")))
    # sand
    pl.shape("M0,78C30,74 60,80 90,77C120,74 140,79 160,77V100H0Z", m, "@t", W0)
    pl.line("M8,86C20,84 30,87 40,85M100,88C112,86 122,89 136,87", m)
    _starfish(pl, m @ _at(30, 91, 10.5), 14)
    _scallop(pl, m @ _at(66, 99, 17))
    _moon_snail(pl, m @ _at(103, 91, 8.5))
    _sand_dollar(pl, m @ _at(132, 92, 9.5))
    for _ in range(9):
        pl.circle(rnd.uniform(10, 150), rnd.uniform(84, 98), rnd.uniform(.5, 1.1), "#fff", W0, m)
    if egg == "ball":
        _ball(pl, *m(150, 92), 4.5 * k)
    elif egg == "dog":
        x, y = m(150, 96)
        _tiny_dog(pl, x - 6, y, .8 * k, True)


def _still_dog(pl, m, seed, egg):
    k = m.k
    # cushion
    cush = "M18,72C50,66 110,66 142,72C147,80 147,92 142,99C110,104 50,104 18,99C13,92 13,80 18,72Z"
    pl.shape(cush, m, "#fff", W1)
    pl.blob("M15,88C40,94 120,94 145,88C145,92 144,96 142,99C110,104 50,104 18,99C16,96 15,92 15,88Z", m, "@h")
    pl.line("M17,78C50,73 110,73 143,78", m)
    for x, y in ((40, 90), (80, 92), (120, 90)):
        pl.circle(x, y, 1.6, "#fff", W0, m)
        pl.line(f"M{x - 5},{y - 3}Q{x},{y} {x - 4},{y + 3}M{x + 5},{y - 3}Q{x},{y} {x + 4},{y + 3}", m)
    for x, y, sx in ((18, 72, -1), (142, 72, 1), (18, 99, -1), (142, 99, 1)):   # tassels
        pl.circle(x + sx * 1.5, y, 2, "#000", 0, m)
        pl.shape(f"M{x + sx * 2},{y + 1}L{x + sx * 7},{y + 8}L{x + sx * 2},{y + 9}Z", m, "@u", W0)
    # the dog, asleep: tail, body, ear, head on its paws
    body = "M28,75C24,58 40,42 66,40C88,38 104,45 110,56L114,75Z"
    pl.shape(body, m, "#fff", W1)
    pl.blob("M28,75C24,58 40,42 66,40C50,46 40,58 42,75Z", m, "@h")
    pl.blob("M60,75C64,66 80,62 100,64C106,66 110,70 112,75Z", m, "@b")
    pl.line("M36,73C33,61 42,52 55,50M34,66C34,56 44,48 58,46M48,74C46,66 50,60 58,58", m)
    for i in range(6):       # contour hatching along the back
        o = i * 2.2
        pl.line(f"M{40 + o * .6},{62 + o * .8}C{44 + o * .4},{52 + o * .6} {56},{46 + o * .7} {72},{45 + o * .8}", m)
    pl.swell(_mp(m, _bezs((32, 70), ((24, 78), (40, 80), (64, 77)), ((72, 76), (80, 74), (86, 73)))), _wk(m, 1.4), _wk(m, .5), _wk(m, .6, 0))
    pl.shape("M102,62C102,52 110,46 120,47C128,48 132,54 136,59C141,61 147,63 147,68C147,72 142,74 136,74L104,74C102,70 102,66 102,62Z",
             m, "#fff", W1)
    pl.shape("M113,50C107,54 105,62 107,71C112,69 116,61 118,52Z", m, "@x", W0)
    pl.line("M123,57Q126.5,59.5 130,57", m, _wk(m, .7))
    pl.line("M137,70Q140,71.6 144,69.5M131,62C134,63 136,64 140,64", m)
    pl.circle(146, 66, 1.6, "#000", 0, m)
    pl.shape(_ell(124, 74, 9, 2.8), m, "#fff", W0)
    pl.line("M128,72.6V75.4M131,72.8V75.2", m)
    pl.swell(_mp(m, _bezs((104, 54), ((106, 60), (107, 66), (106, 73)))), _wk(m, 2.4), _wk(m, 2.4))
    pl.circle(106.5, 75, 2.4, "#fff", W0, m)
    if egg in ("P", "sticks"):
        x, y = m(105.4, 76.4)
        _monogram(pl, x, y, 2.6 * k)
    # zzz, faint
    for i, (x, y, s) in enumerate(((130, 40, 3), (137, 33, 4), (145, 24, 5))):
        pl.line(f"M{x},{y}h{s}l{-s},{s}h{s}", m, _wk(m, .45, .6))
    if egg in ("ball", "dog"):
        _ball(pl, *m(152, 94), 5.5 * k)


_STILL = {"basket": _still_basket, "drums": _still_drums, "shells": _still_shells, "dog": _still_dog}
_SUBJECT = {"roses": "basket", "foliage": "basket", "vines": "basket", "portland": "basket",
            "notes": "drums", "jazz": "drums", "drums": "drums",
            "waves": "shells", "coast": "shells", "surf": "shells", "sun": "shells",
            "dog": "dog", "reeds": "dog", "stars": "dog"}


def tailpiece(width=560, height=150, seed=0, theme="roses"):
    """A cul-de-lampe filling width x height (height 60-400). Small: an inverted cascade of foliage.
    Medium: a medallion with the theme's emblem over the cascade. Large: a still life on a bracket
    (a basket of roses, a lyre and drums, shells and a wave, a dog asleep on a cushion)."""
    w, h = float(width), float(max(60, min(400, height)))
    theme = theme if theme in TAILPIECE_THEMES else "foliage"
    pl = _Plate(w, h, f"tp{w}{h}{seed}{theme}", f"kbook-tail kbook-{theme}")
    cx = w / 2
    egg = _EGGS[seed % 4]
    if h < 120:
        spread = min(w / 2 - 4, 40 + h * 1.9)
        _cascade(pl, cx, max(h * .26, min(10, h * .11) * 1.9 + 1), h - .5, spread, theme, seed)
        if seed % 3 == 0:
            _egg(pl, egg, cx + spread * .55, h * .26 - 3, .8)
    elif h < 230:
        r = min(h * .25, 44)
        y = r + 3
        spread = min(w / 2 - 4, r * 4.6)
        _cascade(pl, cx, y, h - .5, spread, theme, seed, centre=False)
        _medallion(pl, cx, y, r, _EMBLEM_OF.get(theme, theme), seed, "@t" if theme in ("roses", "vines", "foliage") else None)
        if seed % 2 == 0:
            _egg(pl, egg, cx + spread * .62, y - 1, .9)
    else:
        subj = _SUBJECT.get(theme) or ("dog", "basket", "shells", "drums")[seed % 4]
        if seed % 5 == 4:
            subj = ("dog", "basket", "shells", "drums")[(list(_STILL).index(subj) + 1 + seed) % 4]
        hs = h * .6
        ws = min(w * .82, hs * 1.6)
        k = min(ws / 160, hs / 100)
        ox, oy = cx - 80 * k, 2 + hs - 100 * k
        ledge = oy + 100 * k + 1
        lw = 80 * k + 18
        mir = _T(2 * cx, 0) @ _S(-1, 1)
        ey = (ledge - 3) / 1.57                  # the ruled oval behind the subject
        ex = min(86 * k, w / 2 - 34)
        ecy = 3 + ey
        if subj != "shells":
            arc = _arc(cx, ecy, ex, ey, 180 - 35, 360 + 35, 40)
            pl.shape(_cr(arc) + "Z", None, "@v", W0)
            pl.line(_cr(_arc(cx, ecy, ex + 3, ey + 3, 180 - 32, 360 + 32, 40)))
        # brackets: leafy scrolls rising round the oval and rolling outward
        for G in (ID, mir):
            a0 = 32
            pts = [(cx + (ex + 9) * math.cos(math.radians(a)), ecy + (ey + 9) * math.sin(math.radians(a))) for a in range(a0, -50, -4)]
            e = pts[-1]
            pts += _spiral(e[0] + 7, e[1], 7, 180, 1.05, .3, 1)[1:]
            if cx + ex + 30 < w:
                _leafy(pl, _mp(G, pts), min(9, hs * .05), 4, away=G(cx, ecy), tol=.25)
                pl.dot(*pts[-1], 1, G)
        n0 = len(pl.parts)
        _STILL[subj](pl, _T(ox, oy) @ _S(k), seed, egg)
        if subj == "shells":
            cid = pl.pid + "clip"
            clip = _cr(_arc(cx, ecy, ex, ey, 180 - 35, 360 + 35, 40)) + "Z"
            pl.parts[n0:] = ([f'<clipPath id="{cid}"><path d="{clip}" fill="#000" stroke="none"/></clipPath><g clip-path="url(#{cid})">']
                             + pl.parts[n0:] + ["</g>", f'<path d="{clip}"/>'])
            pl.line(_cr(_arc(cx, ecy, ex + 3, ey + 3, 180 - 32, 360 + 32, 40)))
        # the ledge the still life stands on
        pl.rect(cx - lw, ledge, 2 * lw, 3.2, "#fff", W2)
        pl.rect(cx - lw + 3, ledge + 3.2, 2 * lw - 6, 4, "@v", W0)
        for x in (cx - lw, cx + lw):
            pl.circle(x, ledge + 1.6, 2.6, "#fff", W1)
            pl.dot(x, ledge + 1.6, 1)
        spread = min(w / 2 - 4, lw + 30)
        _cascade(pl, cx, ledge + 14, h - .5, spread, theme, seed, centre=True, stem_top=ledge + 7)
        if seed % 3 == 1 and subj != "dog":
            _tiny_dog(pl, cx + lw - 16, ledge, .9, True)
    return pl.svg()


# ---------------------------------------------------------------------------------------------
# printer's flowers
# ---------------------------------------------------------------------------------------------

_HEDERA = ("M6,0C3,-1.4 1.4,-4.4 -1,-4.4C-3.2,-4.4 -4,-2.4 -3.2,-.8Q-3,0 -3.2,.8C-4,2.4 -3.2,4.4 -1,4.4"
           "C1.4,4.4 3,1.4 6,0Z")


def _hedera(pl, m):
    """The Aldine ivy leaf: black, a white vein, a curled stalk; tip at +x."""
    pl.blob(_HEDERA, m)
    pl.white("M-2.2,0C0,-.3 2.4,-.2 4.4,0", m)
    pl.swell(_mp(m, _bezs((-3.1, 0), ((-4.6, 0), (-6, -1), (-6, -2.6)), n=8) + _spiral(-4.6, -2.6, 1.4, 180, .9, .35, 1)[1:]),
             max(.9, .9 * m.k), .5)


def printers_flowers(width=560, seed=0, height=18):
    """A row of cast fleurons for between items, swelling to a larger centre flower and diminishing
    toward the ends. Four sets by seed: Aldine ivy leaves, Thai kanok pairs, stars and lozenges, roses."""
    w, h = float(width), float(max(12, height))
    pl = _Plate(w, h, f"pf{w}{h}{seed}", "kbook-flowers")
    kind = seed % 4
    cx, cy = w / 2, h / 2
    u = h * 1.45                     # unit pitch at full size
    R = h * .46
    if kind == 0:
        _rosette(pl, cx, cy, R)
    elif kind == 1:
        _prajamyam(pl, _at(cx, cy, R))
    elif kind == 2:
        _star4(pl, cx, cy, R * 1.05, R * .22)
        pl.circle(cx, cy, R * .28, "#fff", W0)
    else:
        _rose(pl, _at(cx, cy, R * .95), seed * 11)
    for sgn in (1, -1):
        x, i = R + u * .55, 0
        while x < w / 2 - 6:
            f = 1 - .45 * (x / (w / 2)) ** 1.3
            sc = h / 18 * f * 1.35
            px = cx + sgn * x
            G = _at(px, cy, sc, 0, sgn > 0)        # pointing back toward the centre
            if i % 2 == 1:
                pl.dot(px, cy, 1.3 * sc)
                pl.dot(px - sgn * 3.2 * sc, cy - 3 * sc, .7 * sc)
                pl.dot(px - sgn * 3.2 * sc, cy + 3 * sc, .7 * sc)
            elif kind == 0:
                _hedera(pl, G)
            elif kind == 1:
                _kanok(pl, _at(px - 9 * sc * sgn, cy - .4 * sc, sc * .48, -10 * sgn, sgn < 0) if True else G)
                _kanok(pl, _at(px - 9 * sc * sgn, cy + .4 * sc, sc * .48, 10 * sgn, sgn < 0, True))
            elif kind == 2:
                pl.shape(f"M{_n(px - 5 * sc)},{_n(cy)}L{_n(px)},{_n(cy - 4.6 * sc)}L{_n(px + 5 * sc)},{_n(cy)}L{_n(px)},{_n(cy + 4.6 * sc)}Z",
                         None, "@h", W0)
                _star4(pl, px, cy, 2 * sc)
            else:
                _leaf(pl, _at(px - 6 * sc * sgn, cy, 11 * sc, -24 if sgn > 0 else 204), .32)
                _leaf(pl, _at(px - 6 * sc * sgn, cy, 11 * sc, 24 if sgn > 0 else 156), .32)
            x += u * f * (.75 if i % 2 == 1 else 1.05)
            i += 1
    return pl.svg()
