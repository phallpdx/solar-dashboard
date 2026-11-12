"""engraving_hand -- the single ornamental "hand" shared by every plate.

English/American scroll-and-acanthus ornament in the manner of banknote and
gun engraving, drawn as pure SVG line work for a 16-grey e-ink page.
Original construction; nothing is traced.

Every public function returns SVG *child* markup (a single <g>, no outer
<svg>) and is deterministic by ``seed``.  The art is rasterised to 1-bit
at 2x, so the rules of the hand are:

  * pure black and white; stroke widths are multiples of 0.5 px and no
    line or gap is thinner than 0.5 px; no greys, filters or text
  * light falls from the upper left (LIGHT); heavy edges, shade cuts and
    cast shadows lie on the side away from it, also in mirrored halves
  * white paper fills give the overlaps (painter's order)
  * a scroll is a spiral backbone that starts at the rim; its leaves
    spring from the inner side and curl into the eye, with a crest of
    leaves on the outer back; the ground is cut away to black and pricked

Public API
    acanthus_leaf(spine=None, start=None, angle=0, length=60, curl=0, ...)
    scroll(cx, cy, r, turns=1.5, direction=1, terminal="flower", ...)
    running_scroll(x, y, w, h, orientation=None, seed=0, symmetric=False, ...)
        (bands under 42 px: a leafy vine on a stippled ground)
    fill_region(w, h, seed=0, hole=None, eggs=(), ...)
    matte(w, h, x=0, y=0, style="pearl", pitch=2.0)
    moulding(x, y, w, h, shape="rect", depth=7)
    corner(size, x=0, y=0, quadrant="tl", seed=0)
    forest_fill(w, h, seed=0, creatures=("bird", "dog", "heron", "squirrel"), ...)
    wrap(markup, w, h)   -> standalone <svg> (for tests only)
"""
import math
import random

import numpy as np

W_MAIN = 1.5
W_SEC = 1.0
W_SHADE = 0.5
PITCH_MIN = 1.5
PITCH_STEP = 0.5
LIGHT = (-0.6, -0.8)          # unit-ish vector pointing *towards* the light
TERMINALS = ("flower", "bud", "dog", "heron", "p", "paw", "drumsticks")
INK = "#000"
PAPER = "#fff"

_G_OPEN = ('<g fill="none" stroke="%s" stroke-linecap="round" '
           'stroke-linejoin="round">' % INK)
_STYLE = {
    "F": ' fill="%s"' % PAPER,                       # paper fill, 1.0 line
    "G": ' fill="%s" stroke-width="1.5"' % PAPER,    # paper fill, 1.5 line
    "E": ' fill="%s" stroke-width=".5"' % PAPER,     # paper fill, 0.5 line
    "W": ' fill="%s" stroke="none"' % PAPER,         # paper only
    "K": ' fill="%s" stroke="none"' % INK,           # small ink spot
    "H": ' stroke-width="1.5"',
    "S": '',
    "T": ' stroke-width=".5"',
    "D": ' stroke-width="1.5" stroke-dasharray="0 3"',   # punched pearl row
    "B": ' stroke-dasharray="0 3"',                  # bead row
    "N": ' stroke-width="1.5" stroke-dasharray="0 2.5"',  # close punched row
    "P": ' stroke="%s" stroke-width="1.5"' % PAPER,  # white line (paper) cut
    "p": ' stroke="%s"' % PAPER,                     # white line 1.0
    "X": ' stroke-width="2"',                        # undercut
    "Q": ' stroke="%s" stroke-dasharray="0 5"' % PAPER,   # white punch marks
    "w": ' stroke="%s" stroke-width=".5"' % PAPER,   # white hairline
}
_MERGE = set("HSTK")


# ----------------------------------------------------------------- path ink
def _num(t):
    """tenths (int) -> shortest decimal string."""
    if t == 0:
        return "0"
    s = "-" if t < 0 else ""
    t = abs(t)
    a, b = divmod(t, 10)
    if b == 0:
        return "%s%d" % (s, a)
    if a == 0:
        return "%s.%d" % (s, b)
    return "%s%d.%d" % (s, a, b)


def _join(nums):
    out = []
    for i, n in enumerate(nums):
        s = _num(n)
        if i and s[0] != "-":
            out.append(" ")
        out.append(s)
    return "".join(out)


class _D:
    """Compact path-data writer (relative commands, 1 decimal)."""

    def __init__(self):
        self.p = []
        self.x = self.y = 0
        self.last = ""

    def _cmd(self, c, nums):
        s = _join(nums)
        if c == self.last and c in "lc":
            if s[0] != "-":
                s = " " + s
            self.p.append(s)
        else:
            self.p.append(c + s)
        self.last = c

    def M(self, x, y):
        self.x, self.y = int(round(x * 10)), int(round(y * 10))
        self._cmd("M", [self.x, self.y])
        return self

    def L(self, x, y):
        X, Y = int(round(x * 10)), int(round(y * 10))
        if X == self.x and Y == self.y:
            return self
        self._cmd("l", [X - self.x, Y - self.y])
        self.x, self.y = X, Y
        return self

    def C(self, a, b, c):
        v = []
        for q in (a, b, c):
            X, Y = int(round(q[0] * 10)), int(round(q[1] * 10))
            v += [X - self.x, Y - self.y]
        self._cmd("c", v)
        self.x += v[4]
        self.y += v[5]
        return self

    def Q(self, a, b):
        v = []
        for q in (a, b):
            X, Y = int(round(q[0] * 10)), int(round(q[1] * 10))
            v += [X - self.x, Y - self.y]
        s = _join(v)
        self.p.append("q" + s)
        self.last = "q"
        self.x += v[2]
        self.y += v[3]
        return self

    def Z(self):
        self.p.append("z")
        self.last = "z"
        return self

    def poly(self, pts, close=False):
        self.M(*pts[0])
        for q in pts[1:]:
            self.L(*q)
        if close:
            self.Z()
        return self

    def cubics(self, segs, move=True):
        if move:
            self.M(*segs[0][0])
        for s in segs:
            self.C(s[1], s[2], s[3])
        return self

    def circle(self, cx, cy, r):
        R = int(round(r * 10))
        if R < 1:
            R = 1
        self.M(cx - R / 10.0, cy)
        rr, dd = _num(R), _num(2 * R)
        self.p.append("a%s %s 0 1 0 %s 0a%s %s 0 1 0-%s 0z" % (rr, rr, dd, rr, rr, dd))
        self.last = "z"
        return self

    def smooth(self, pts, close=True):
        """Catmull-Rom through pts as cubics."""
        n = len(pts)
        self.M(*pts[0])
        rng = range(n) if close else range(n - 1)
        for i in rng:
            if close:
                p0, p1, p2, p3 = (pts[(i - 1) % n], pts[i], pts[(i + 1) % n],
                                  pts[(i + 2) % n])
            else:
                p0 = pts[max(i - 1, 0)]
                p1, p2 = pts[i], pts[i + 1]
                p3 = pts[min(i + 2, n - 1)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
            self.C(c1, c2, p2)
        if close:
            self.Z()
        return self

    def __str__(self):
        return "".join(self.p)


class _Canvas:
    def __init__(self):
        self.items = []          # [style, [d, d, ...]]

    def add(self, style, d):
        d = str(d)
        if not d:
            return
        if self.items and self.items[-1][0] == style and style in _MERGE:
            self.items[-1][1].append(d)
        else:
            self.items.append([style, [d]])

    def markup(self):
        out = [_G_OPEN]
        for st, ds in self.items:
            if st == "R":
                out.append("".join(ds))
                continue
            out.append('<path%s d="%s"/>' % (_STYLE[st], "".join(ds)))
        out.append("</g>")
        return "".join(out)


# --------------------------------------------------------------- geometry
def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _bez(seg, t):
    a, b, c, d = seg
    m = 1 - t
    k0, k1, k2, k3 = m * m * m, 3 * m * m * t, 3 * m * t * t, t * t * t
    return (k0 * a[0] + k1 * b[0] + k2 * c[0] + k3 * d[0],
            k0 * a[1] + k1 * b[1] + k2 * c[1] + k3 * d[1])


def _split(seg, t):
    a, b, c, d = seg
    ab, bc, cd = _lerp(a, b, t), _lerp(b, c, t), _lerp(c, d, t)
    abc, bcd = _lerp(ab, bc, t), _lerp(bc, cd, t)
    m = _lerp(abc, bcd, t)
    return (a, ab, abc, m), (m, bcd, cd, d)


def _sub(seg, t0, t1):
    s = _split(seg, t1)[0]
    if t0 <= 0:
        return s
    return _split(s, t0 / t1)[1]


def _seglerp(s1, s2, t):
    return tuple(_lerp(s1[i], s2[i], t) for i in range(4))


def _spine(start, angle, length, curl, n=16, ease=1.4):
    """Points of a spine: heading turns by ``curl`` radians, mostly late."""
    x, y = start
    pts = [(x, y)]
    ds = length / float(n)
    for i in range(n):
        s = (i + 0.5) / n
        a = angle + curl * s ** ease
        x += math.cos(a) * ds
        y += math.sin(a) * ds
        pts.append((x, y))
    return pts


class _Frame:
    """Arc-length frame along a polyline spine; maps (u, v) -> page."""

    def __init__(self, pts):
        self.pts = pts
        acc = [0.0]
        for i in range(1, len(pts)):
            acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                            pts[i][1] - pts[i - 1][1]))
        self.acc = acc
        self.L = acc[-1] or 1.0

    def at(self, u):
        s = u * self.L
        acc, pts = self.acc, self.pts
        n = len(pts)
        i = 1
        while i < n - 1 and acc[i] < s:
            i += 1
        a, b = pts[i - 1], pts[i]
        seg = (acc[i] - acc[i - 1]) or 1.0
        t = (s - acc[i - 1]) / seg
        tx, ty = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, -ty, tx

    def mp(self, q):
        x, y, nx, ny = self.at(q[0])
        return (x + nx * q[1], y + ny * q[1])

    def seg(self, s):
        return tuple(self.mp(q) for q in s)


class _Mir:
    """Reflection of *parameters* (so light and shade stay unmirrored)."""

    def __init__(self, ax=None, ay=None):
        self.ax, self.ay = ax, ay

    def pt(self, p):
        if p is None:
            return None
        x, y = p
        if self.ax is not None:
            x = 2 * self.ax - x
        if self.ay is not None:
            y = 2 * self.ay - y
        return (x, y)

    def ang(self, a):
        if self.ax is not None:
            a = math.pi - a
        if self.ay is not None:
            a = -a
        return a

    def d(self, d):
        if self.ax is not None:
            d = -d
        if self.ay is not None:
            d = -d
        return d


_ID = _Mir()


# ------------------------------------------------------------------- leaf
def _env(u):
    u = min(max(u, 0.0), 1.0)
    return max(0.0, math.sin(math.pi * u ** 0.8)) ** 0.5


def _leaf(cv, spine, width=None, lobes=5, turnover=False, rng=None,
          shade=1.0, base=None):
    """Draw one modelled acanthus leaf along ``spine`` onto canvas ``cv``.

    The leaf is built as overlapping pleats: the tip lobe is laid first and
    each pair of side lobes is laid over the pair in front of it, so every
    overlap is real, the eye sits where two lobes part, and the shade cuts
    of a lobe run out from under the lobe that covers it.
    """
    rng = rng or random.Random(0)
    fr = _Frame(spine)
    L = fr.L
    W = width if width else 0.27 * L
    K = max(1, (int(lobes) - 1) // 2)
    if L < 17:
        K = 1
    b0 = base if base is not None else max(0.8, 0.13 * W)
    big = L >= 50
    _, _, nx, ny = fr.at(0.45)
    sh = 1 if (nx * LIGHT[0] + ny * LIGHT[1]) < 0 else -1
    G = [(0.0 if j == 0 else 0.07 + 0.60 * (j / float(K)) ** 0.9) * L
         for j in range(K + 1)]
    rho = 0.30

    def e(U):
        return W * _env(U / L)

    def mp(q):
        return fr.mp((q[0] / L, q[1]))

    def mseg(s, sg):
        return tuple(mp((q[0], q[1] * sg)) for q in s)

    def lobe_edge(E1, T, f, axis, nf, wid, c1, rn=None):
        """back edge E1 -> shoulder, then a round nose; a rounded tongue."""
        p = (-f[1], f[0])
        if rn is None:
            rn = min(max(0.42 * wid, 0.8), 7.0)
        A = (T[0] - f[0] * rn + p[0] * rn * 0.95, T[1] - f[1] * rn + p[1] * rn * 0.95)
        Bn = (T[0] - f[0] * rn - p[0] * rn * 0.95, T[1] - f[1] * rn - p[1] * rn * 0.95)
        D = math.hypot(A[0] - E1[0], A[1] - E1[1])
        B = (E1, c1, (A[0] - f[0] * 0.42 * D, A[1] - f[1] * 0.42 * D), A)
        segs = []
        if nf >= 2:
            s1, s2 = _split(B, 0.46)
            q = s1[3]
            Q = _bez(axis, 0.4)
            qi = _lerp(q, Q, 0.22)
            segs.append((s1[0], s1[1], (s1[2][0] + 0.35 * (s1[2][0] - Q[0]),
                                        s1[2][1] + 0.35 * (s1[2][1] - Q[1])), qi))
            segs.append((qi, (s2[1][0] + 0.45 * (s2[1][0] - Q[0]),
                              s2[1][1] + 0.45 * (s2[1][1] - Q[1])), s2[2], A))
        else:
            segs.append(B)
        k = 1.33 * rn
        segs.append((A, (A[0] + f[0] * k, A[1] + f[1] * k),
                     (Bn[0] + f[0] * k, Bn[1] + f[1] * k), Bn))
        return segs, Bn, B

    def cuts(dd, B, axis, sg, dark, wid, first=False, tip=False):
        """shade cuts that follow the lobe, densest where it is overlapped."""
        if shade <= 0:
            return
        a, b = mp(_bez(B, 0.4)), mp(_bez(axis, 0.4))
        span = math.hypot(a[0] - b[0], a[1] - b[1])
        pitch = PITCH_MIN if not big else 2.0
        lam_max = (0.86 if dark else 0.42) * min(1.0, shade)
        n = min(int(lam_max * span / pitch), 6 if dark else 2)
        for i in range(n):
            lam = (i + 0.75) * pitch / span
            s = _seglerp(B, axis, lam)
            if dark:
                t1 = (0.9 - 0.5 * lam) * (1.0 if i % 2 == 0 else 0.62)
            else:
                t1 = (0.5 - 0.6 * lam) * (1.0 if i % 2 == 0 else 0.7)
            if lam < 0.3:
                t1 = min(t1, 0.30)
            if tip:
                t1 = min(t1, 0.42 if dark else 0.2)
            t0 = 0.0 if not first else 0.1
            if t1 - t0 < 0.1:
                continue
            w = mseg(_sub(s, t0, t1), sg)
            if math.hypot(w[3][0] - w[0][0], w[3][1] - w[0][1]) < 9:
                dd.M(*w[0]).L(*w[3])
            else:
                dd.cubics([w])

    # ---- the tip lobe (laid first)
    dUl = G[K] - G[K - 1]
    S = (G[K] - 0.45 * dUl, 0.0)
    ve = rho * e(G[K]) * 0.9
    E1 = (G[K] - 0.03 * dUl, ve)
    T = (L, 0.0)
    tipw = e(G[K] + 0.3 * (L - G[K]))
    tlen = L - G[K]
    to = turnover and L >= 26
    nf = 1 if (to or tlen < 14) else 2
    axis = (S, (S[0] + 0.3 * (L - S[0]), 0.0), (L - 0.3 * (L - S[0]), 0.0), T)
    c1 = (G[K] - 0.02 * tlen, ve + 0.95 * (tipw - ve))
    rn = min(max(0.3 * tipw, 0.7), 5.0)
    segs, _, Bt = lobe_edge(E1, T, (1.0, 0.0), axis, nf, tipw, c1, rn)
    # one side carries the nose; the other side is the back edge mirrored
    nose = ((L - rn, rn * 0.95), (L + 0.33 * rn, rn * 0.95), (L + 0.33 * rn, -rn * 0.95),
            (L - rn, -rn * 0.95))
    backs = segs[:-1]
    d = _D().M(*mp(S)).L(*mp(E1))
    for s in backs + [nose]:
        w = mseg(s, 1)
        d.C(w[1], w[2], w[3])
    for s in reversed(backs):
        w = mseg(s, -1)
        d.C(w[2], w[1], w[0])
    d.Z()
    cv.add("F", d)
    cv.add("H", _D().cubics([mseg(s, sh) for s in backs]))
    dd = _D()
    for sg in (1, -1):
        cuts(dd, Bt, axis, sg, sg == sh, tipw, tip=True)
    cv.add("T", dd)

    # ---- turned-over tip: the end of the leaf folds towards the viewer
    if to:
        tq = 0.52
        Q = _bez(Bt, tq)
        dep = min(0.16 * L, 2.2 * Q[1] + 2)
        sk = 0.25 * Q[1] * sh
        hem = ((Q[0], -Q[1]), (Q[0] - dep, -0.75 * Q[1] + sk), (Q[0] - dep, 0.75 * Q[1] + sk),
               (Q[0], Q[1]))
        dsh = _D()
        nn = max(3, int(2.0 * Q[1] / PITCH_MIN))
        for i in range(nn):
            t = (i + 0.5) / nn
            q = _bez(hem, t)
            ln = (0.6 if i % 2 == 0 else 0.38) * dep * (1.25 if (q[1] * sh) > 0 else 0.8)
            dsh.M(*mp((q[0] - 0.4, q[1]))).L(*mp((q[0] - ln - 0.4, q[1] * 0.92)))
        cv.add("T", dsh)
        up = _sub(Bt, tq, 1.0)
        dl = _D().cubics([mseg(up, 1), mseg(nose, 1)])
        w = mseg(up, -1)
        dl.C(w[2], w[1], w[0])
        w = mseg(hem, 1)
        dl.C(w[1], w[2], w[3]).Z()
        cv.add("F", dl)
        cv.add("H", _D().cubics([mseg(hem, 1)]))
        dr = _D()
        inner = ((Q[0], 0.0), (Q[0] + 0.3 * (L - Q[0]), 0.0), (Q[0] + 0.6 * (L - Q[0]), 0.0), (L, 0.0))
        nl = min(3, int(0.7 * Q[1] / PITCH_MIN))
        for i in range(nl):
            lam = (i + 0.9) * PITCH_MIN / max(Q[1], 0.1)
            w = mseg(_sub(_seglerp(up, inner, lam), 0.0, 0.75 - 0.4 * lam), sh)
            dr.M(*w[0]).L(*w[3])
        cv.add("T", dr)

    # ---- side lobes, laid from the tip back to the base
    eyes = []
    for j in range(K - 1, -1, -1):
        dU = G[j + 1] - G[j]
        dd = _D()
        for sg in (sh, -sh):
            jit = 1.0 + (rng.random() - 0.5) * 0.12
            Ut = min(G[j + 1] + 0.30 * dU, 0.94 * L)
            vt = e(G[j] + 0.72 * dU) * jit
            T = (Ut, vt)
            if j == 0:
                S = (0.0, 0.0)
                E1 = (0.0, b0)
                c1 = (-0.10 * dU, b0 + 0.72 * (vt - b0))
            else:
                dp = G[j] - G[j - 1]
                S = (G[j] - 0.45 * dp, 0.0)
                E1 = (G[j] - 0.03 * dp, rho * e(G[j]) * 0.9)
                c1 = (E1[0] - 0.10 * dU, E1[1] + 0.66 * (vt - E1[1]))
            Am = (0.5 * (S[0] + G[j + 1]), 0.0)
            axis = (Am, (Am[0] + 0.4 * (Ut - Am[0]), 0.10 * vt),
                    (Ut - 0.25 * (Ut - Am[0]), 0.62 * vt), T)
            fx, fy = T[0] - axis[2][0], T[1] - axis[2][1]
            fl = math.hypot(fx, fy) or 1.0
            f = (fx / fl, fy / fl)
            wid = math.hypot(T[0] - E1[0], T[1] - E1[1]) * 0.6
            lpx = math.hypot(T[0] - E1[0], T[1] - E1[1])
            nf = 2 if lpx > 13 else 1
            lw = 0.5 * math.hypot(G[j + 1] - E1[0], rho * e(G[j + 1]) - E1[1])
            segs, T2, B = lobe_edge(E1, T, f, axis, nf, lw, c1)
            Ef = (G[j + 1] + 0.02 * dU, rho * e(G[j + 1]))
            D = math.hypot(T2[0] - Ef[0], T2[1] - Ef[1])
            P1 = (G[j + 1] - 0.22 * dU, 0.0)
            front = (T2, (T2[0] - f[0] * 0.5 * D, T2[1] - f[1] * 0.5 * D),
                     (Ef[0] + 0.30 * dU, Ef[1] * 1.25), Ef)
            fold = (Ef, (Ef[0] - 0.12 * dU, Ef[1] * 0.5), (P1[0] + 0.10 * dU, Ef[1] * 0.12), P1)
            pipe = (Ef, (Ef[0] - 0.5 * dU, Ef[1] * 0.85), (G[j] + 0.2 * dU, Ef[1] * 0.4),
                    (G[j] - 0.05 * dU, 0.06 * W))
            if lpx > 15 and shade > 0:
                dd.cubics([mseg(_sub(pipe, 0.1, 1.0), sg)])
            d = _D().M(*mp((S[0], 0.0)))
            if j:
                d.L(*mp((E1[0], E1[1] * sg)))
            else:
                d.L(*mp((0.0, b0 * sg)))
            for s in segs + [front] + ([fold] if fold else []):
                w = mseg(s, sg)
                d.C(w[1], w[2], w[3])
            d.Z()
            cv.add("G" if sg == sh else "F", d)
            cuts(dd, B, axis, sg, sg == sh, wid, first=(j == 0))
            eyes.append(mp((Ef[0], Ef[1] * sg)))
        cv.add("T", dd)

    # ---- eyes and midrib
    de = _D()
    for q in eyes:
        de.M(*q)
        de.p.append("h.1")
        de.last = "h"
    cv.add("H" if W >= 7 else "S", de)
    if big:
        m = _D()
        for o in (0.05 * W, -0.05 * W):
            m.cubics([mseg(((0.0, o * 1.5), (0.3 * L, o), (0.6 * L, o * 0.6),
                            (0.9 * L, 0.0)), 1)])
        cv.add("T", m)
    else:
        cv.add("S", _D().cubics([mseg(((0.0, 0.0), (0.3 * L, 0.0), (0.6 * L, 0.0),
                                       (0.88 * L, 0.0)), 1)]))


def acanthus_leaf(spine=None, start=None, angle=0.0, length=60.0, curl=0.0,
                  width=None, lobes=5, turnover=False, seed=0, shade=1.0):
    """One modelled acanthus leaf.

    Give either ``spine`` (list of (x, y) from base to tip) or ``start``
    (x, y) + ``angle`` (radians, 0 = east, clockwise on screen) + ``length``
    + ``curl`` (total turn of the spine in radians, + = clockwise).
    ``width`` is the half width in px (default 0.3 * length); ``lobes`` 3-7;
    ``turnover`` rolls the tip towards the viewer; ``shade`` 0..1.
    """
    if spine is None:
        spine = _spine(start or (0, 0), angle, length, curl)
    cv = _Canvas()
    _leaf(cv, spine, width, lobes, turnover, random.Random(seed), shade)
    return cv.markup()


# ------------------------------------------------- the leaf, as drawn once
# Canonical half-leaves ("comma" acanthus that rides a stem).  The stem runs
# along +x from (0,0) to (10,0); the leaf rises to y = -12.8 and its turned
# tip reaches x = 20.  Each is mapped through a function (x, y) -> page so
# it bends with whatever carries it.
def _cs(*pts):
    """chain of cubics from a flat point list: start, then 3 points each."""
    segs = []
    p0 = pts[0]
    for i in range(1, len(pts), 3):
        segs.append((p0, pts[i], pts[i + 1], pts[i + 2]))
        p0 = pts[i + 2]
    return segs


_FRONT = _cs((17.2, -5.4), (17.8, -6.8), (16, -7.6), (14.4, -6.2), (12.6, -4.6), (11, -2.4), (10, 0))
_TIP = [(19.2, -10.6), (20.6, -7.8), (19.2, -5.6), (18.7, -4.8), (17.6, -4.6), (17.2, -5.4)]
_CURL = ((17.2, -5.4), (16.6, -6.4), (17, -7.6), (18, -8.2))
_LEAF = {
    # three lobelets, two eyes, turned tip (for leaves 13 px high and more)
    "a": dict(
        back=_cs((0, 0), (-1.4, -2.6), (-.6, -6.2), (2.6, -6.9), (3.8, -7.1), (4.6, -6.2), (4.6, -5.2),
                 (4.6, -4.6), (4.5, -4), (4.3, -3.6),
                 (4.2, -6.6), (5.6, -10.6), (8.8, -10.9), (10.2, -11), (11, -9.8), (10.9, -8.6),
                 (10.9, -7.8), (10.7, -7.1), (10.4, -6.6),
                 (10.6, -9.6), (13.4, -12.8), (16.6, -11.6), *_TIP),
        front=_FRONT,
        pipes=[((4.3, -3.6), (4.8, -2.8), (5.6, -1.6), (6.2, -.6)),
               ((10.4, -6.6), (10.9, -5.2), (10.9, -3.4), (10.2, -1.8))],
        curl=_CURL,
        fans=[([(0.6, -.6), (4.2, -.6)], (0, 1)),
              ([(4.6, -3.4), (5.6, -1.9), (6.5, -.7)], (3, 5)),
              ([(10.7, -6.4), (11.2, -4.4), (10.8, -1.7)], (6, 8))],
        vein=((11.6, -4.4), (13, -7), (15, -9), (17.4, -9.4)),
        root=[((.8, -.9), (1.2, -4.2)), ((1.9, -.8), (2.4, -4.4)), ((3, -.8), (3.4, -3.2))],
        cuts=[((5.2, -3.6), (5.6, -7.4)), ((6.1, -3), (6.8, -7.6)), ((7, -2.6), (7.8, -6.2)),
              ((7.9, -2.2), (8.6, -4.8)),
              ((11.4, -6.6), (12.6, -10)), ((12.2, -5.8), (13.8, -9.4)), ((13, -5), (14.6, -8)),
              ((18.2, -6.2), (18.8, -8)), ((17.6, -6.6), (17.9, -8.2))]),
    # two lobelets, one eye (6.5 - 13 px)
    "c": dict(
        back=_cs((0, 0), (-1.6, -3.6), (-.2, -8.6), (4.6, -9.2), (6, -9.4), (7, -8.4), (6.9, -7.2),
                 (6.9, -6.4), (6.7, -5.6), (6.4, -5),
                 (6.6, -9), (11, -13), (16, -11.6), *_TIP),
        front=_FRONT,
        pipes=[((6.4, -5), (7, -3.8), (7.4, -2.4), (7.2, -1))],
        curl=_CURL,
        fans=[([(0.6, -.6), (6.2, -.6)], (0, 2)),
              ([(6.7, -4.8), (7.5, -3), (7.5, -1)], (3, 5))],
        vein=None,
        root=[((1, -1), (1.6, -5)), ((2.4, -.9), (3.2, -5.4)), ((3.8, -.9), (4.6, -4))],
        cuts=[((7.4, -4.8), (8.4, -9)), ((8.4, -4), (9.8, -8.4)), ((9.4, -3.2), (10.8, -6.6)),
              ((18.2, -6.2), (18.8, -8))]),
    # plain comma (under 6.5 px)
    "d": dict(
        back=_cs((0, 0), (-1.6, -5), (4, -13), (16, -11.6), *_TIP),
        front=_FRONT,
        pipes=[], curl=None, vein=None,
        fans=[([(1, -.6), (9.4, -.6)], (0, 2))],
        root=[((2, -1), (3.4, -5.4))],
        cuts=[((5, -1.2), (7, -6))]),
}

# A whole (two-sided) small acanthus leaf: base (0,0), tip (20,0), half
# width 8.4.  Upper side listed; the lower side is its mirror.
_SYM = dict(
    side=_cs((0, 0), (-.6, -3), (1.4, -6.6), (5, -6.2), (5.9, -6), (6.1, -5.2), (5.7, -4.5),
             (7, -7.8), (11, -8.4), (13.4, -6.6), (14.1, -6), (14.1, -5.3), (13.7, -4.7),
             (15.6, -5.8), (18.6, -3.6), (20, 0)),
    pipes=[((5.7, -4.5), (6.3, -3.4), (6.6, -1.8), (6.2, -.4)),
           ((13.7, -4.7), (14.2, -3.6), (14.4, -2), (13.8, -.5))],
    dark=[((1, -1), (2, -3.8)), ((2.4, -.9), (3.6, -3.6)), ((6.8, -4.6), (8.6, -7)),
          ((7.6, -3.4), (9.6, -5.6)), ((8.6, -2.4), (10, -3.8)), ((14.6, -4.6), (16.2, -5.2)),
          ((15, -3.4), (16.6, -3.8))],
    lit=[((1, -1), (1.8, -3.2)), ((6.9, -4.4), (8.2, -6.4))])


def _cleaf(cv, m, kind, dark=True, shade=1.0, px=1.5, cast=True):
    """Lay one canonical half-leaf through the mapping ``m``.

    ``px`` = page px per canon unit (sets how many shade cuts fit).  The
    leaf is modelled in tone: a fan of cuts runs from the stem out along
    every lobelet, close and crossed at the root (dark), thinning to bare
    paper at the tips (light); the edge that lies over the next leaf is cut
    heavy so it throws a shadow.
    """
    L = _LEAF[kind]

    def ms(s):
        return tuple(m(q[0], q[1]) for q in s)
    back = [ms(s) for s in L["back"]]
    front = [ms(s) for s in L["front"]]
    d = _D().cubics(back)
    for s in front:
        d.C(s[1], s[2], s[3])
    d.Z()
    cv.add("F", d)
    if shade > 0:
        dt = _D()
        cyc = (0.74, 0.44, 0.62, 0.36)
        for base, (s0, s1) in L["fans"]:
            segs = L["back"][s0:s1]
            # px length of the base decides how many cuts it can carry
            bl = 0.0
            for i in range(len(base) - 1):
                bl += math.hypot(base[i + 1][0] - base[i][0], base[i + 1][1] - base[i][1])
            n = max(2, min(int(bl * px / (1.0 if px >= 1.25 else 1.5)), 16))
            for i in range(n):
                f = (i + 0.5) / n
                u = f * (len(base) - 1)
                bi = min(int(u), len(base) - 2)
                S = _lerp(base[bi], base[bi + 1], u - bi)
                v = f * len(segs)
                si = min(int(v), len(segs) - 1)
                E = _bez(segs[si], v - si)
                ln = cyc[i % 4] * (1.0 if dark else 0.72) * (1.2 if px >= 1.25 else 1.0)
                P1 = _lerp(S, E, ln)
                dt.M(*m(*S))
                if math.hypot(P1[0] - S[0], P1[1] - S[1]) * px > 9:
                    Pm = _lerp(S, P1, 0.5)
                    dt.L(*m(Pm[0] - 0.15, Pm[1]))
                dt.L(*m(*P1))
                if dark and px >= 1.2 and i % 2 == 0 and i + 1 < n:
                    # a short cut between, to deepen the root
                    f2 = (i + 1.0) / n
                    u2 = f2 * (len(base) - 1)
                    b2 = min(int(u2), len(base) - 2)
                    S2 = _lerp(base[b2], base[b2 + 1], u2 - b2)
                    v2 = f2 * len(segs)
                    s2 = min(int(v2), len(segs) - 1)
                    E2 = _bez(segs[s2], v2 - s2)
                    if px >= 2.0:
                        dt.M(*m(*_lerp(S2, E2, 0.04))).L(*m(*_lerp(S2, E2, 0.26)))
        for a, b in L["cuts"]:
            if a[0] > 16:
                dt.M(*m(*a)).L(*m(*b))
        cv.add("T", dt)
    ds = _D()
    for s in L["pipes"]:
        ds.cubics([ms(s)])
    if L["curl"]:
        ds.cubics([ms(L["curl"])])
    cv.add("H" if px >= 1.3 else "S", ds)
    if dark and px >= 0.95:
        cv.add("H", _D().cubics(back))
    # the lapping edge, and the shadow it throws on what lies under it
    if px >= 0.8:
        cv.add("X" if px >= 1.3 else "H", _D().cubics(front))
    if shade > 0 and cast and px >= 1.0:
        dc = _D()
        n = max(3, min(int(11 * px / 1.1), 16))
        for i in range(n):
            f = 0.1 + 0.86 * (i + 0.5) / n
            v = f * 2
            q = _bez(L["front"][min(int(v), 1)], v - min(int(v), 1))
            ln = (2.3 if i % 2 == 0 else 1.3) * (0.6 + 0.4 * f)
            dc.M(*m(q[0] + 0.25, q[1] + 0.05)).L(*m(q[0] + ln, q[1] + 0.3 * ln))
        cv.add("T", dc)


def _sleaf(cv, spine, halfw, shade=1.0, turn=0.0):
    """A whole small acanthus leaf along ``spine`` (base first)."""
    fr = _Frame(spine)
    k = halfw / 8.4

    def m(x, y):
        return fr.mp((x / 20.0, y * k))
    _, _, nx, ny = fr.at(0.5)
    # upper side of the canon lies on -normal; which side is from the light?
    up_dark = (-(nx * LIGHT[0] + ny * LIGHT[1])) < 0
    up = [tuple(m(q[0], q[1]) for q in s) for s in _SYM["side"]]
    lo = [tuple(m(q[0], -q[1]) for q in s) for s in _SYM["side"]]
    d = _D().cubics(up)
    for s in reversed(lo):
        d.C(s[2], s[1], s[0])
    d.Z()
    cv.add("F", d)
    cv.add("H", _D().cubics(up if up_dark else lo))
    ds = _D().M(*m(.4, 0))
    ds.C(m(6, 0), m(12, 0), m(18.2, 0))
    if halfw >= 4.5:
        for s in _SYM["pipes"]:
            ds.cubics([tuple(m(q[0], q[1]) for q in s)])
            ds.cubics([tuple(m(q[0], -q[1]) for q in s)])
    cv.add("S", ds)
    if shade > 0 and halfw >= 3.2:
        dt = _D()
        for sg, dk in ((-1 if up_dark else 1, True), (1 if up_dark else -1, False)):
            for a, b in (_SYM["dark"] if dk else _SYM["lit"]):
                if halfw < 5 and abs(a[1]) > 4:
                    continue
                dt.M(*m(a[0], -a[1] * sg)).L(*m(b[0], -b[1] * sg))
        cv.add("T", dt)


# ---------------------------------------------------------------- terminals
def _terminal(cv, kind, cx, cy, s, flip=1, rot=0.0, rng=None):
    cr, sr = math.cos(rot), math.sin(rot)

    def P(x, y):
        x *= flip
        return (cx + s * (x * cr - y * sr), cy + s * (x * sr + y * cr))

    def PP(pts):
        return [P(*q) for q in pts]

    def disc():
        cv.add("F", _D().circle(cx, cy, s))
        if s >= 7:
            cv.add("T", _D().circle(cx, cy, s - 1.5))

    if kind == "flower" and s < 5.2:
        cv.add("F", _D().circle(cx, cy, s))
        dd = _D()
        for i in range(5):
            a = 2 * math.pi * i / 5 + rot
            dd.M(cx + s * 0.55 * math.cos(a), cy + s * 0.55 * math.sin(a))
            dd.p.append("h.1")
            dd.last = "h"
        cv.add("S", dd)
    elif kind == "flower":
        n = 5 if s < 9 else 6
        h = math.pi / n * 1.25
        r0 = 0.30
        for layer in (0, 1):
            for i in range(layer, n, 2):
                a = 2 * math.pi * i / n + rot
                pts = []
                for da, rr in ((-h * 0.45, r0), (-h * 0.9, 0.72), (-h * 0.42, 1.0),
                               (0, 0.9), (h * 0.42, 1.0), (h * 0.9, 0.72),
                               (h * 0.45, r0)):
                    pts.append((cx + s * rr * math.cos(a + da),
                                cy + s * rr * math.sin(a + da)))
                cv.add("F", _D().smooth(pts))
                if s >= 6:
                    dd = _D()
                    for da in ((-0.22, 0.0, 0.22) if s >= 10 else (0.0,)):
                        dd.M(cx + s * 0.4 * math.cos(a + da * h),
                             cy + s * 0.4 * math.sin(a + da * h))
                        dd.L(cx + s * (0.72 - abs(da)) * math.cos(a + da * h * 2),
                             cy + s * (0.72 - abs(da)) * math.sin(a + da * h * 2))
                    cv.add("T", dd)
        cv.add("F", _D().circle(cx, cy, s * 0.3))
        cv.add("K", _D().circle(cx, cy, min(1.6, s * 0.12)))
    elif kind == "bud":
        cv.add("F", _D().smooth(PP([(0, -1), (0.5, -0.45), (0.62, 0.2), (0.3, 0.8),
                                    (0, 0.95), (-0.3, 0.8), (-0.62, 0.2),
                                    (-0.5, -0.45)])))
        dd = _D()
        dd.smooth(PP([(-0.6, 0.15), (-0.25, 0.0), (0, -0.45)]), False)
        dd.smooth(PP([(0.6, 0.15), (0.25, 0.0), (0, -0.45)]), False)
        cv.add("S", dd)
        if s >= 5:
            dd = _D()
            for x in (-0.3, -0.1, 0.1, 0.3):
                dd.M(*P(x, 0.78 - abs(x) * 0.3)).L(*P(x * 0.8, 0.25))
            cv.add("T", dd)
    elif kind == "paw":
        disc()
        pad = PP([(0, 0.02), (0.4, 0.2), (0.5, 0.52), (0.25, 0.68), (0, 0.6),
                  (-0.25, 0.68), (-0.5, 0.52), (-0.4, 0.2)])
        if s <= 8:
            cv.add("K", _D().smooth(pad))
        else:
            cv.add("F", _D().smooth(pad))
            dd = _D()
            for i in range(-3, 4):
                x = i * 1.5 / s
                if abs(x) < 0.42:
                    dd.M(*P(x, 0.16 + abs(x) * 0.3)).L(*P(x, 0.6))
            cv.add("T", dd)
        for (x, y, a) in ((-0.56, -0.02, -0.5), (-0.22, -0.42, -0.15),
                          (0.22, -0.42, 0.15), (0.56, -0.02, 0.5)):
            pts = []
            for k in range(8):
                t = 2 * math.pi * k / 8
                ex, ey = 0.15 * math.cos(t), 0.22 * math.sin(t)
                pts.append((x + ex * math.cos(a) - ey * math.sin(a),
                            y + ex * math.sin(a) + ey * math.cos(a)))
            cv.add("K" if s <= 12 else "F", _D().smooth(PP(pts)))
    elif kind == "p":
        disc()
        dd = _D()
        dd.M(*P(-0.34, -0.56)).L(*P(-0.34, 0.6))
        dd.M(*P(-0.34, -0.56))
        dd.C(P(0.52, -0.62), P(0.52, 0.1), P(-0.34, 0.04))
        cv.add("H", dd)
        dd = _D()
        dd.M(*P(-0.56, 0.6)).L(*P(-0.08, 0.6))
        dd.M(*P(-0.56, -0.56)).L(*P(-0.3, -0.56))
        cv.add("S", dd)
        if s >= 8:
            dd = _D()
            dd.M(*P(-0.16, -0.4)).L(*P(-0.16, 0.5))
            dd.M(*P(-0.14, -0.4)).C(P(0.3, -0.42), P(0.3, -0.08), P(-0.14, -0.1))
            cv.add("T", dd)
    elif kind == "drumsticks":
        disc()
        for sx in (1, -1):
            a, b = (-0.62 * sx, 0.62), (0.5 * sx, -0.5)
            ux, uy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(ux, uy)
            px, py = -uy / ln, ux / ln
            w0, w1 = 0.085, 0.045
            cv.add("F", _D().poly(PP([(a[0] + px * w0, a[1] + py * w0),
                                      (b[0] + px * w1, b[1] + py * w1),
                                      (b[0] - px * w1, b[1] - py * w1),
                                      (a[0] - px * w0, a[1] - py * w0)]), True))
            t = P(b[0] + ux / ln * 0.1, b[1] + uy / ln * 0.1)
            cv.add("F", _D().circle(t[0], t[1], max(1.2, s * 0.13)))
    elif kind == "heron":
        disc()
        neck = PP([(-0.5, 0.92), (-0.42, 0.5), (-0.05, 0.3), (0.12, 0.05),
                   (-0.02, -0.25), (-0.12, -0.42)])
        neck2 = PP([(-0.18, 0.92), (-0.1, 0.62), (0.28, 0.38), (0.4, 0.02),
                    (0.26, -0.3), (0.2, -0.42)])
        cv.add("S", _D().smooth(neck, False))
        cv.add("S", _D().smooth(neck2, False))
        head = PP([(-0.2, -0.5), (-0.02, -0.7), (0.28, -0.66), (0.95, -0.42),
                   (0.3, -0.36), (0.1, -0.3)])
        cv.add("F", _D().poly(head, True))
        dd = _D()
        dd.M(*P(0.3, -0.5)).L(*P(0.92, -0.42))
        cv.add("T", dd)
        dd = _D()
        dd.smooth(PP([(-0.05, -0.66), (-0.45, -0.6), (-0.8, -0.36)]), False)
        dd.smooth(PP([(-0.15, -0.56), (-0.45, -0.45), (-0.66, -0.2)]), False)
        cv.add("S", dd)
        e = P(0.1, -0.53)
        cv.add("K", _D().circle(e[0], e[1], max(0.7, s * 0.06)))
        if s >= 8:
            dd = _D()
            for t in (0.5, 0.62, 0.74, 0.86):
                dd.M(*P(-0.46 + 0.02, t)).L(*P(-0.3, t - 0.06))
            cv.add("T", dd)
    elif kind == "dog":
        disc()
        k = 0.82
        head = [(-0.62, 1.0), (-0.78, 0.35), (-0.72, -0.3), (-0.4, -0.78),
                (0.08, -0.8), (0.34, -0.5), (0.5, -0.28), (0.98, -0.22),
                (1.1, -0.02), (1.02, 0.2), (0.6, 0.36), (0.3, 0.5), (0.12, 0.72),
                (0.1, 1.0)]
        cv.add("F", _D().smooth(PP([(x * k - 0.1, y * k) for x, y in head]), False))
        ear = [(-0.36, -0.7), (-0.66, -0.3), (-0.72, 0.3), (-0.5, 0.56),
               (-0.26, 0.36), (-0.14, -0.1), (-0.12, -0.56)]
        earp = PP([(x * k - 0.1, y * k) for x, y in ear])
        cv.add("F", _D().smooth(earp))
        dd = _D()
        for i in range(1, 7):
            y = -0.55 + i * 0.15
            x0 = -0.62 if y > -0.2 else -0.5
            x1 = -0.2 if y < 0.25 else -0.34
            if s * 0.15 * k >= 1.2 or i % 2 == 0:
                dd.M(*P(x0 * k - 0.1, y * k)).L(*P(x1 * k - 0.1, (y - 0.1) * k))
        cv.add("T", dd)
        nose = P(1.0 * k - 0.1, -0.08 * k)
        cv.add("K", _D().circle(nose[0], nose[1], max(1.0, s * 0.11)))
        eye = P(0.16 * k - 0.1, -0.36 * k)
        cv.add("K", _D().circle(eye[0], eye[1], max(0.8, s * 0.07)))
        dd = _D()
        dd.smooth(PP([(0.98 * k - 0.1, 0.2 * k), (0.7 * k - 0.1, 0.2 * k),
                      (0.46 * k - 0.1, 0.3 * k)]), False)
        dd.smooth(PP([(0.0 * k - 0.1, -0.5 * k), (0.18 * k - 0.1, -0.56 * k),
                      (0.3 * k - 0.1, -0.46 * k)]), False)
        cv.add("S" if s >= 9 else "T", dd)
        if s >= 9:
            dd = _D()   # collar
            dd.M(*P(-0.66 * k - 0.1, 0.74 * k)).L(*P(0.1 * k - 0.1, 0.84 * k))
            cv.add("H", dd)


# ------------------------------------------------------------------ scroll
def _tendril(cv, start, heading, size, d, dot=True):
    """A fine wire that runs out and coils up (about 1.3 turns)."""
    n = 18
    x, y = start
    pts = [(x, y)]
    a = heading
    ds = size * 1.9 / n
    for i in range(n):
        s = (i + 0.5) / n
        a += d * ds * (0.25 + 7.5 * s * s * s) / max(size * 0.42, 1.0) * (1 + 1.6 * s)
        x += math.cos(a) * ds * (1 - 0.45 * s)
        y += math.sin(a) * ds * (1 - 0.45 * s)
        pts.append((x, y))
    cv.add("S", _D().smooth(pts[::2] + [pts[-1]], False))
    if dot:
        cv.add("K", _D().circle(pts[-1][0], pts[-1][1], 0.9))


def _band(cv, pts, hws, shade=True, heavy=True):
    n = len(pts)
    left, right, nor = [], [], []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        nor.append((nx, ny))
        left.append((pts[i][0] + nx * hws[i], pts[i][1] + ny * hws[i]))
        right.append((pts[i][0] - nx * hws[i], pts[i][1] - ny * hws[i]))
    cv.add("F", _D().poly(left + right[::-1], True))
    dh, dt = _D(), _D()
    for edge, sg in ((left, 1), (right, -1)):
        run, inner = [], []
        for i in range(n):
            nx, ny = nor[i][0] * sg, nor[i][1] * sg
            if nx * LIGHT[0] + ny * LIGHT[1] < -0.2:
                run.append(edge[i])
                if hws[i] >= 1.9:
                    o = min(1.5, hws[i] * 0.75)
                    inner.append((edge[i][0] - nx * o, edge[i][1] - ny * o))
                elif len(inner) > 1:
                    dt.poly(inner)
                    inner = []
                else:
                    inner = []
            else:
                if len(run) > 1:
                    dh.poly(run)
                if len(inner) > 1:
                    dt.poly(inner)
                run, inner = [], []
        if len(run) > 1:
            dh.poly(run)
        if len(inner) > 1:
            dt.poly(inner)
    if heavy:
        cv.add("H", dh)
    if shade:
        cv.add("T", dt)


def _scroll(cv, cx, cy, r, turns=1.5, d=1, a0=None, terminal="flower",
            rng=None, stem_from=None, tendril=True, shade=1.0):
    rng = rng or random.Random(0)
    if a0 is None:
        a0 = math.pi * 0.75
    figure = terminal in ("dog", "heron", "p", "paw", "drumsticks")
    hw0, hw1 = max(1.0, 0.05 * r), max(0.6, 0.022 * r)
    # the backbone runs round the rim and draws in by half each turn; the
    # leaves spring from its inner side and fill the scroll
    R0 = r * 0.97 - hw0
    rho = 0.42
    b = -math.log(rho) / (2 * math.pi)
    if figure:
        re = max(4.0, r * 0.24)
        eye = re + 0.8
    else:
        re = 0.0
        eye = max(1.5, 0.085 * r)
    Phi = min(2 * math.pi * 1.5, math.log(R0 / (eye + hw1 + 1.5)) / b)
    rend = R0 * math.exp(-b * Phi)
    ex, ey = cx, cy
    tp = 2 * math.pi

    def rb(p):
        return R0 * math.exp(-b * p)

    def hw(p):
        p = min(max(p, 0.0), Phi)
        return hw0 + (hw1 - hw0) * p / Phi

    def P(p):
        t = a0 + d * p
        q = rb(p)
        return (ex + q * math.cos(t), ey + q * math.sin(t))

    def inner(q):
        # how far in a leaf rooted at q may reach
        if q + tp <= Phi:
            return rb(q + tp) + hw(q + tp) + 0.6
        f = min(1.0, (q + tp - Phi) / 1.7)
        f = f * f * (3 - 2 * f)
        return (rend + hw1 + 0.6) * (1 - f) + eye * f

    def space(q):
        return rb(q) - hw(q) - inner(q)

    pattern = (0.96, 1.0, 0.9, 0.98)
    leaves = []
    p = 0.12 if stem_from is None else 0.2
    k = rng.randrange(4)
    while p < Phi - 0.35:
        s0 = space(p + 0.2)
        if s0 < 3.4:
            break
        hf = pattern[k % 4]
        h = hf * s0
        lw = 1.5 * h / 12.8                  # px of arc per canon unit
        rm = max(rb(p) - 0.45 * h, 0.35 * rb(p))
        leaves.append((p, lw, rm, hf, h))
        p += 10.6 * lw / rm
        k += 1
    for (p, lw, rm, hf, h) in reversed(leaves):
        kind = "a" if h >= 12 else ("c" if h >= 5.0 else "d")
        t = a0 + d * (p + 8 * lw / rm)
        dark = (math.cos(t) * LIGHT[0] + math.sin(t) * LIGHT[1]) > -0.25

        def m(x, y, p=p, lw=lw, rm=rm, hf=hf):
            q = p + x * lw / rm
            t = a0 + d * q
            rad = rb(q) - hw(q) * 0.3 - (-y / 12.8) * hf * max(space(q), 1.0)
            return (ex + rad * math.cos(t), ey + rad * math.sin(t))
        _cleaf(cv, m, kind, dark, shade, lw)

    # ---- leaves on the back, where the backbone has drawn in from the rim
    def spaceo(q):
        return (r - 0.5) - rb(q) - hw(q)
    outs = []
    p = 0.5
    while p < tp - 0.5:
        s0 = spaceo(p + 0.25)
        if s0 < 3.8:
            p += 0.15
            continue
        h = s0 * pattern[k % 4]
        lw = 1.5 * h / 12.8
        rm = rb(p) + 0.5 * h
        if p + 15 * lw / rm > tp + 0.25:
            break
        outs.append((p, lw, rm, h))
        p += 10.6 * lw / rm
        k += 1
    for (p, lw, rm, h) in reversed(outs):
        kind = "a" if h >= 12 else ("c" if h >= 5.0 else "d")
        t = a0 + d * (p + 8 * lw / rm)
        dark = (math.cos(t) * LIGHT[0] + math.sin(t) * LIGHT[1]) < 0.25

        def m(x, y, p=p, lw=lw, rm=rm, h=h):
            q = p + x * lw / rm
            t = a0 + d * q
            rad = rb(q) + hw(q) * 0.3 + (-y / 12.8) * min(h * 1.25, 0.97 * max(spaceo(q), 1.0))
            return (ex + rad * math.cos(t), ey + rad * math.sin(t))
        _cleaf(cv, m, kind, dark, shade, lw)

    # ---- tendril and stem
    pts, hws = [], []
    if stem_from is not None:
        s0 = P(0)
        t = a0
        tx, ty = -d * math.sin(t), d * math.cos(t)
        dist = math.hypot(s0[0] - stem_from[0], s0[1] - stem_from[1])
        c2 = (s0[0] - tx * dist * 0.45, s0[1] - ty * dist * 0.45)
        # leave the parent tangentially (parent turns the other way)
        c1 = _lerp(stem_from, c2, 0.45)
        seg = (stem_from, c1, c2, s0)
        for i in range(8):
            pts.append(_bez(seg, i / 8.0))
            hws.append(hw0 * (1.25 - 0.25 * i / 8.0))
    step = 0.22 if r >= 30 else (0.3 if r >= 16 else 0.6)
    nstep = int(Phi / step)
    for i in range(nstep + 1):
        p = Phi * i / nstep
        pts.append(P(p))
        w = hw(p)
        if stem_from is None and p < 0.7:
            w = 0.4 + (w - 0.4) * (p / 0.7)
        hws.append(w)
    if tendril and stem_from is None and r >= 12:
        s0 = P(0)
        ta = math.atan2(d * math.cos(a0), -d * math.sin(a0)) + math.pi
        _tendril(cv, s0, ta - d * 0.3, r * 0.3, d)
    if r >= 16:
        _band(cv, pts, hws, shade > 0, True)
    else:
        ns = len(pts) - (nstep + 1)
        if ns > 0:
            _band(cv, pts[:ns + 1], hws[:ns + 1], False, False)
        cv.add("H", _D().smooth(pts[ns:], False))
    if hw0 >= 2.3:
        # beaded stem on the stout part of the backbone
        bd = [q for q, w in zip(pts, hws) if w >= 2.0]
        if len(bd) > 3:
            cv.items.append(["B", [str(_D().poly(bd))]])

    # ---- the eye: the stem ends in a ball, or holds a figure
    if figure:
        _terminal(cv, terminal, ex, ey, re, -d if terminal in ("dog", "heron") else 1, 0.0, rng)
    elif terminal:
        _berry(cv, ex, ey, eye - 0.3)
        if eye >= 3.2:
            dd = _D()
            for i in range(5):
                t = a0 + i * 1.2566
                dd.M(ex + 0.35 * eye * math.cos(t), ey + 0.35 * eye * math.sin(t))
                dd.L(ex + 0.8 * eye * math.cos(t + 0.3), ey + 0.8 * eye * math.sin(t + 0.3))
            cv.add("T", dd)


def scroll(cx, cy, r, turns=1.5, direction=1, start_angle=None,
           terminal="flower", seed=0, stem_from=None, tendril=True, shade=1.0):
    """A classic scroll that stays wholly inside the circle (cx, cy, r).

    ``direction`` +1 winds clockwise on screen, -1 anticlockwise.
    ``start_angle`` (radians, 0 = east, clockwise) is where the backbone
    starts on its outer turn; ``stem_from`` (x, y) grows the backbone from
    that point instead of a tendril.  ``terminal`` is one of TERMINALS.
    """
    cv = _Canvas()
    _scroll(cv, cx, cy, r, turns, direction, start_angle, terminal,
            random.Random(seed), stem_from, tendril, shade)
    return cv.markup()


# ------------------------------------------------------------------- matte
def _matte(cv, x, y, w, h, style="pearl", pitch=2.0):
    pitch = max(PITCH_MIN, round(pitch / PITCH_STEP) * PITCH_STEP)
    if style in ("pearl", "stipple"):
        # punched ground: staggered rows of round punch marks
        d = _D()
        row = 0
        yy = y + 1.0
        while yy < y + h - 0.5:
            off = 1.5 if row % 2 else 0.0
            d.M(x + 1.0 + off, yy).L(x + w - 0.5, yy)
            yy += 2.5
            row += 1
        cv.items.append(["D" if style == "pearl" else "B", [str(d)]])
        return
    if style == "deep":
        # the deep ground of the gun engraver: cut right away to black and
        # then matted with rows of fine punch marks
        cv.add("K", _D().poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True))
        d = _D()
        row = 0
        yy = y + 1.5
        while yy < y + h - 0.5:
            d.M(x + 1.5 + (2.5 if row % 2 else 0.0), yy).L(x + w - 0.5, yy)
            yy += 2.5
            row += 1
        cv.items.append(["Q", [str(d)]])
        return
    if style == "night":
        # deep ground: heavy cuts laid close, crossed by a punched row, so
        # it prints near black yet is still made of drawn marks
        d = _D()
        c = 2.5
        while c < w + h:
            x0, x1 = max(0.0, c - h), min(w, c)
            d.M(x + x0, y + c - x0).L(x + x1, y + c - x1)
            c += 2.5
        cv.add("H", d)
        d = _D()
        yy = y + 1.5
        while yy < y + h - 0.5:
            d.M(x + 1.0, yy).L(x + w - 0.5, yy)
            yy += 5.0
        cv.items.append(["N", [str(d)]])
        return
    if style == "scale":
        # fish-scale ground
        d = _D()
        q = max(4.0, pitch * 2)
        row = 0
        yy = y
        while yy < y + h:
            xx = x - (q / 2 if row % 2 else 0)
            d.M(xx, yy)
            n = int((w + q) / q) + 1
            for i in range(n):
                d.C((xx + i * q, yy + q * 0.66), (xx + (i + 1) * q, yy + q * 0.66),
                    (xx + (i + 1) * q, yy))
            yy += q / 2
            row += 1
        cv.add("T", d)
        return
    if style == "basket":
        d = _D()
        q = max(6.0, pitch * 3)
        j = 0
        yy = y
        while yy < y + h:
            i = 0
            xx = x
            while xx < x + w:
                horiz = (i + j) % 2 == 0
                for k in (1, 2, 3):
                    o = q * k / 4.0
                    if horiz:
                        d.M(xx + 0.5, min(yy + o, y + h)).L(min(xx + q - 0.5, x + w), min(yy + o, y + h))
                    elif xx + o <= x + w:
                        d.M(xx + o, yy + 0.5).L(xx + o, min(yy + q - 0.5, y + h))
                xx += q
                i += 1
            yy += q
            j += 1
        cv.add("T", d)
        return
    d = _D()
    if style == "ruled":
        yy = y + pitch / 2
        while yy < y + h:
            d.M(x, yy).L(x + w, yy)
            yy += pitch
    if style in ("hatch", "cross"):
        c = pitch
        while c < w + h:
            x0, x1 = max(0.0, c - h), min(w, c)
            d.M(x + x0, y + c - x0).L(x + x1, y + c - x1)
            c += pitch
    if style == "cross":
        c = -h + pitch
        while c < w:
            x0, x1 = max(0.0, c), min(w, c + h)
            d.M(x + x0, y + x0 - c).L(x + x1, y + x1 - c)
            c += pitch
    cv.add("T", d)


def matte(w, h, x=0, y=0, style="pearl", pitch=2.0):
    """Ground texture for the space between scrolls.

    style: "hatch" (45 degree cuts), "cross", "ruled" (horizontal) or
    "stipple".  ``pitch`` is the axis step, a multiple of 0.5 and >= 1.5.
    """
    cv = _Canvas()
    _matte(cv, x, y, w, h, style, pitch)
    return cv.markup()


# ---------------------------------------------------------------- moulding
def _moulding(cv, x, y, w, h, shape="rect", depth=7.0, fill=True):
    """heavy rule, hatched bevel, rule, pearl beading, fine fillet."""
    dp = max(4.0, depth)
    bev = 3.0 if dp >= 6.5 else dp - 1.0     # bevel width
    pearls = dp >= 6.5
    if shape == "oval":
        cx, cy, a, b = x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0

        def ell(aa, bb):
            k = 0.5523
            dd = _D().M(cx - aa, cy)
            dd.C((cx - aa, cy - k * bb), (cx - k * aa, cy - bb), (cx, cy - bb))
            dd.C((cx + k * aa, cy - bb), (cx + aa, cy - k * bb), (cx + aa, cy))
            dd.C((cx + aa, cy + k * bb), (cx + k * aa, cy + bb), (cx, cy + bb))
            dd.C((cx - k * aa, cy + bb), (cx - aa, cy + k * bb), (cx - aa, cy))
            return dd.Z()
        cv.add("G" if fill else "H", ell(a, b))
        dd = _D()
        per = math.pi * (a + b)
        n = int(per / PITCH_MIN)
        for i in range(n):
            t = 2 * math.pi * i / n
            ct, st = math.cos(t), math.sin(t)
            lit = ct * LIGHT[0] + st * LIGHT[1]
            if lit > 0.25 and i % 3:
                continue
            if -0.25 <= lit <= 0.25 and i % 2:
                continue
            dd.M(cx + (a - 1.0) * ct, cy + (b - 1.0) * st)
            dd.L(cx + (a - bev + 0.6) * ct, cy + (b - bev + 0.6) * st)
        cv.add("T", dd)
        cv.add("S", ell(a - bev, b - bev))
        if pearls:
            cv.items.append(["D", [str(ell(a - bev - 2.0, b - bev - 2.0))]])
        cv.add("T", ell(a - dp, b - dp))
        return
    cv.add("G" if fill else "H",
           _D().poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True))
    dd = _D()
    for side in ("t", "l", "b", "r"):
        dark = side in ("b", "r")
        pt = PITCH_MIN if dark else 3.0
        ln = w if side in ("t", "b") else h
        n = int((ln - 2) / pt)
        for i in range(1, n + 1):
            s = i * pt
            o = min(s, ln - s, bev)          # mitre
            if o < 1.2:
                continue
            if side == "t":
                dd.M(x + s, y + 1.0).L(x + s, y + o - 0.5)
            elif side == "b":
                dd.M(x + s, y + h - 1.0).L(x + s, y + h - o + 0.5)
            elif side == "l":
                dd.M(x + 1.0, y + s).L(x + o - 0.5, y + s)
            else:
                dd.M(x + w - 1.0, y + s).L(x + w - o + 0.5, y + s)
    for (px, py, sx, sy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x + w, y + h, -1, -1),
                             (x, y + h, 1, -1)):
        dd.M(px, py).L(px + sx * bev, py + sy * bev)
    cv.add("T", dd)

    def box(o, close=True):
        return _D().poly([(x + o, y + o), (x + w - o, y + o), (x + w - o, y + h - o),
                          (x + o, y + h - o)], close)
    cv.add("S", box(bev))
    if pearls:
        o = bev + 2.0
        # pearls: pitch fitted so a pearl sits in every corner
        dd = _D()
        for (ax, ay, bx, by) in ((x + o, y + o, x + w - o, y + o), (x + w - o, y + o, x + w - o, y + h - o),
                                 (x + w - o, y + h - o, x + o, y + h - o), (x + o, y + h - o, x + o, y + o)):
            dd.M(ax, ay).L(bx, by)
        cv.items.append(["D", [str(dd)]])
    cv.add("T", box(dp))


def moulding(x, y, w, h, shape="rect", depth=7.0, fill=True):
    """A moulded cartouche edge: heavy outer rule, hatched bevel, rule,
    pearl beading and a fine fillet.  With ``fill`` the whole inside is
    clean paper; the clear opening is inset by ``depth`` (default 7)."""
    cv = _Canvas()
    _moulding(cv, x, y, w, h, shape, depth, fill)
    return cv.markup()


# ------------------------------------------------------------- composition
def _pack(x0, y0, x1, y1, rmax, rmin, rng, blocks=(), ovals=(), preset=(),
          step=2.0, anchor=None, gap=0.6, vary=0.72, big=0, rbig=None):
    """Greedy circle packing of the box, avoiding blocks/ovals/presets."""
    xs = np.arange(x0 + step / 2, x1, step)
    ys = np.arange(y0 + step / 2, y1, step)
    X, Y = np.meshgrid(xs, ys)
    clear = np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))
    for (bx0, by0, bx1, by1) in blocks:
        dx = np.maximum(np.maximum(bx0 - X, X - bx1), 0)
        dy = np.maximum(np.maximum(by0 - Y, Y - by1), 0)
        dd = np.hypot(dx, dy)
        dd[(dx == 0) & (dy == 0)] = -1
        clear = np.minimum(clear, dd)
    for (ox, oy, oa, ob) in ovals:
        kk = np.sqrt(((X - ox) / oa) ** 2 + ((Y - oy) / ob) ** 2)
        clear = np.minimum(clear, (kk - 1) * min(oa, ob))
    out = []
    for (px, py, pr) in preset:
        clear = np.minimum(clear, np.hypot(X - px, Y - py) - pr - gap)
    ax, ay = anchor if anchor else (x0, y1)
    adist = np.hypot(X - ax, Y - ay)
    first = True
    while len(out) < 400:
        m = float(clear.max())
        if m < rmin:
            break
        cap = rmax if first else rmax * (vary + (1 - vary) * rng.random())
        if len(out) < big and rbig:
            cap = rbig * (1.0 if first else 0.82 + 0.18 * rng.random())
        cap = min(cap, m)
        if cap < rmin:
            cap = rmin
        score = np.where(clear >= cap, 1e6 - (clear - cap) * 40 - adist * (1.0 if first else (0.0 if len(out) < big else 0.15)),
                         clear)
        i = int(np.argmax(score))
        iy, ix = divmod(i, X.shape[1])
        r = float(min(clear[iy, ix], cap))
        px, py = float(X[iy, ix]), float(Y[iy, ix])
        out.append((px, py, r))
        clear = np.minimum(clear, np.hypot(X - px, Y - py) - r - gap)
        first = False
    return out


def _link(circles, rng, rs_min=18.5, d0=1, root_angle=None):
    """Turn packed circles into a tree of scroll specs + filler specs."""
    scrolls, fills = [], []
    for (x, y, r) in circles:
        if r >= rs_min:
            best, bg = None, 1e9
            for s in scrolls:
                gp = math.hypot(x - s["x"], y - s["y"]) - r - s["r"]
                # prefer big parents close by
                sc = gp - 0.05 * s["r"]
                if gp < 0.45 * r + 3 and sc < bg:
                    best, bg = s, sc
            s = dict(x=x, y=y, r=r, seed=rng.randrange(1 << 20), stem=None,
                     turns=1.45 + 0.25 * rng.random(), terminal="flower")
            if best is None:
                s["d"] = d0
                s["a0"] = root_angle if root_angle is not None else math.pi * 0.6
            else:
                s["d"] = -best["d"]
                ua = math.atan2(y - best["y"], x - best["x"])
                s["a0"] = ua + math.pi
                ga = ua - best["d"] * 0.95
                hwp = max(1.0, 0.05 * best["r"])
                pp = (best["d"] * (ga - best["a0"])) % (2 * math.pi)
                rbp = (best["r"] * 0.97 - hwp) * 0.42 ** (pp / (2 * math.pi))
                s["stem"] = (best["x"] + rbp * math.cos(ga), best["y"] + rbp * math.sin(ga))

            scrolls.append(s)
        else:
            fills.append((x, y, r, rng.randrange(1 << 20)))
    return scrolls, fills


def _leaflet(cv, base, ang, ln, wd, bend=0.0):
    """A small one-piece leaf (three scallops a side) for the gaps."""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        v = v + bend * ln * u * u
        return (base[0] + ca * u * ln - sa * v, base[1] + sa * u * ln + ca * v)

    dark = 1 if (-sa * LIGHT[0] + ca * LIGHT[1]) < 0 else -1
    d = _D().M(*P(0, 0))
    half = {}
    for sg in (1, -1):
        w = wd * sg
        half[sg] = [(P(0, 0), P(-0.06, 0.9 * w), P(0.3, 1.25 * w), P(0.48, 0.74 * w)),
                    (P(0.48, 0.74 * w), P(0.52, 1.05 * w), P(0.84, 0.8 * w), P(1, 0))]
    for s in half[1]:
        d.C(s[1], s[2], s[3])
    for s in reversed(half[-1]):
        d.C(s[2], s[1], s[0])
    d.Z()
    cv.add("F", d)
    if wd >= 4.5:
        cv.add("H", _D().cubics(half[dark]))
    dd = _D().M(*P(0.04, 0)).L(*P(0.8, 0))
    if wd >= 3.4:
        for u in (0.16, 0.3):
            dd.M(*P(u, 0.3 * wd * dark)).L(*P(u + 0.16, 0.86 * wd * dark))
        dd.M(*P(0.5, 0.22 * wd * dark)).L(*P(0.66, 0.6 * wd * dark))
        dd.M(*P(0.18, -0.3 * wd * dark)).L(*P(0.3, -0.7 * wd * dark))
    cv.add("T", dd)


def _berry(cv, x, y, rr):
    cv.add("F", _D().circle(x, y, rr))
    if rr >= 2.4:
        dd = _D().M(x + rr * 0.05, y + rr * 0.58)
        dd.C((x + rr * 0.4, y + rr * 0.5), (x + rr * 0.58, y + rr * 0.3), (x + rr * 0.6, y - rr * 0.05))
        cv.add("T", dd)
    else:
        dd = _D().M(x, y)
        dd.p.append("h.1")
        dd.last = "h"
        cv.add("S", dd)


def _berries3(cv, x, y, r, sd=0):
    """three small berries (never one big ball)"""
    rr = max(1.0, min(1.5, 0.45 * r))
    off = max(rr * 0.9, min(0.5 * r, 2.0))
    if r < 2.6:
        _berry(cv, x, y, rr)
        return
    for j in range(3):
        a = sd * 0.37 + 2.094 * j
        _berry(cv, x + off * math.cos(a), y + off * math.sin(a), rr)


def _hleaf(cv, spine, height, side=1, kind=None, dark=True):
    """A half (comma) acanthus leaf laid along ``spine``, rising ``height``
    to the ``side`` (+1 = left of travel on screen... i.e. -normal)."""
    fr = _Frame(spine)
    if kind is None:
        kind = "a" if height >= 13 else ("c" if height >= 6.5 else "d")

    def m(x, y):
        return fr.mp((x / 20.0, y * height / 12.8 * side))
    _cleaf(cv, m, kind, dark, 1.0, 0.5 * (height / 12.8 + fr.L / 20.0))


def _fillers(cv, fills, scrolls, mir):
    """Small growth for the gaps: leaves, tendrils, berries."""
    for n, (x, y, r, sd) in enumerate(fills):
        near, ng = None, 1e9
        for s in scrolls:
            gp = math.hypot(x - s["x"], y - s["y"]) - s["r"]
            if gp < ng:
                near, ng = s, gp
        p = mir.pt((x, y))
        if near is not None and ng < r + 5 and r >= 3.2:
            ua = math.atan2(y - near["y"], x - near["x"])
            st = mir.pt((near["x"] + (near["r"] - 3.0) * math.cos(ua),
                         near["y"] + (near["r"] - 3.0) * math.sin(ua)))
            ang = mir.ang(ua)
            ln = ng + r * 1.8 + 3.0
            sgn = mir.d(1 if sd % 2 else -1)
            if r >= 3.6:
                # a comma leaf springing from the backbone into the gap
                sg = 1 if sd % 2 else -1
                R = near["r"] - 1.0
                dl = min(1.3, (1.3 * r + 2.0) / R)
                A = (near["x"] + R * math.cos(ua - sg * dl), near["y"] + R * math.sin(ua - sg * dl))
                B = (near["x"] + (R + 0.45 * ng + 0.2 * r) * math.cos(ua - sg * 0.25 * dl),
                     near["y"] + (R + 0.45 * ng + 0.2 * r) * math.sin(ua - sg * 0.25 * dl))
                C = (x + 0.75 * r * math.cos(ua + sg * 0.5), y + 0.75 * r * math.sin(ua + sg * 0.5))
                sp = []
                for i in range(11):
                    u = i / 10.0
                    sp.append(mir.pt(((1 - u) ** 2 * A[0] + 2 * u * (1 - u) * B[0] + u * u * C[0],
                                      (1 - u) ** 2 * A[1] + 2 * u * (1 - u) * B[1] + u * u * C[1])))
                _hleaf(cv, sp, min(1.15 * r, 0.5 * (ng + 2 * r)), mir.d(-sg))
            elif sd % 3:
                _tendril(cv, st, ang - 0.5 * sgn, r * 1.25 + 0.5 * ng, sgn)
            else:
                _berries3(cv, p[0], p[1], r, sd)
        elif r >= 3.4:
            # a gap out of reach of any backbone: a leaf of its own on a
            # thread of stem
            a = (sd % 628) / 100.0
            sgn = 1 if sd % 2 else -1
            sp = _spine((x - r * math.cos(a), y - r * math.sin(a)), a - sgn * 0.3, 2.0 * r, sgn * 0.7, n=10, ease=1.0)
            _hleaf(cv, [mir.pt(q) for q in sp], 0.95 * r, mir.d(-sgn))
            if near is not None and ng < 30:
                ua = math.atan2(y - near["y"], x - near["x"])
                st = (near["x"] + (near["r"] - 1.0) * math.cos(ua), near["y"] + (near["r"] - 1.0) * math.sin(ua))
                md = ((st[0] + sp[0][0]) / 2 + 0.2 * (sp[0][1] - st[1]), (st[1] + sp[0][1]) / 2 - 0.2 * (sp[0][0] - st[0]))
                cv.add("p", _D().M(*mir.pt(st)).Q(mir.pt(md), mir.pt(sp[0])))
        else:
            _berries3(cv, p[0], p[1], r, sd)


def _render_scrolls(cv, scrolls, mir):
    for s in reversed(scrolls):
        c = mir.pt((s["x"], s["y"]))
        _scroll(cv, c[0], c[1], s["r"], s["turns"], mir.d(s["d"]), mir.ang(s["a0"]),
                s["terminal"], random.Random(s["seed"]), mir.pt(s["stem"]), True)


def fill_region(w, h, seed=0, hole=None, x=0, y=0, eggs=(), matte_style="deep",
                matte_pitch=2.0, rmax=None, frame=False, grow="corners"):
    """Bilaterally symmetric scrollwork filling the w x h rectangle at (x, y).

    ``hole`` = (hx, hy, hw, hh, shape) relative to the rectangle, shape
    "rect" or "oval": the scrolls keep clear of it and it receives a
    moulded frame (the clear paper opening is inset by depth 5 + 1.5).
    ``eggs``: terminal names (see TERMINALS) hidden in the eyes of some
    scrolls, left half first; ``grow``: "corners" or "centre".
    """
    if hole is None and h < 72 and w >= 3 * h:
        # a frieze: one continuous vine
        return running_scroll(x, y, w, h, "h", seed, True, "flower", (), matte_style, matte_pitch,
                              "flower" if h >= 30 else None)
    rng = random.Random(seed)
    cv = _Canvas()
    _matte(cv, x, y, w, h, matte_style, matte_pitch)
    half = w / 2.0
    blocks, ovals = [], []
    if hole:
        hx, hy, hw_, hh, shp = (list(hole) + ["rect"])[:5]
        m = 1.5
        if shp == "oval":
            ovals.append((x + hx + hw_ / 2.0, y + hy + hh / 2.0, hw_ / 2.0 + m, hh / 2.0 + m))
        else:
            blocks.append((x + hx - m, y + hy - m, x + hx + hw_ + m, y + hy + hh + m))
    if rmax is None:
        rmax = min(h / 2.0 - 0.5, half / 2.0 - 0.5, 32.0)
        rmax = max(rmax, min(h / 2.0 - 0.5, half - 0.5, 20.0))
    anchor = (x, y + h) if grow == "corners" else (x + half, y + h)
    rbig = min(h / 2.0 - 0.5, half / 2.0 - 0.5, rmax * 1.5)
    nbig = 0 if rbig < rmax * 1.15 else max(1, int(half * h / 26000.0 + 0.5))
    circles = _pack(x + 0.5, y + 0.5, x + half, y + h - 0.5, rmax, 2.4, rng,
                    blocks, ovals, anchor=anchor, vary=0.5, big=nbig, rbig=rbig)
    ra = -0.6 if grow == "corners" else math.pi + 0.6
    scrolls, fills = _link(circles, rng, d0=1 if grow == "corners" else -1,
                           root_angle=ra)
    eggs = list(eggs)
    big = sorted(range(len(scrolls)), key=lambda i: -scrolls[i]["r"])
    mirrored_eggs = {}
    for n, i in enumerate(big):
        if n < len(eggs) and eggs[n]:
            if n % 2 == 0:
                scrolls[i]["terminal"] = eggs[n]
            else:
                mirrored_eggs[i] = eggs[n]
    for mir in (_ID, _Mir(ax=x + half)):
        _fillers(cv, fills, scrolls, mir)
        if mir is not _ID and mirrored_eggs:
            sc = [dict(s) for s in scrolls]
            for i, t in mirrored_eggs.items():
                sc[i]["terminal"] = t
            _render_scrolls(cv, sc, mir)
        else:
            _render_scrolls(cv, scrolls, mir)
    if hole:
        _moulding(cv, x + hx, y + hy, hw_, hh, shp, 7.0, True)
    if frame:
        _moulding(cv, x, y, w, h, "rect", 4.0, False)
    return cv.markup()


def _vine(cv, x, y, w, h, horiz, rng, symmetric, eggs, centre):
    """Narrow running border: one waving stem, a large acanthus leaf in the
    hollow of every wave and a small one on its back."""
    ln, th = (w, h) if horiz else (h, w)
    A = 0.2 * th
    mgn = 3.0
    rc = (th / 2.0 - 1.5) if symmetric else 0.0
    span = (ln / 2.0 - rc - mgn) if symmetric else (ln - 2 * mgn)
    nb = max(1, int(round(span / (1.45 * th))))
    lam = span / nb
    s_begin = (ln / 2.0 + rc) if symmetric else mgn

    def build(flip):
        def W(s, t):
            if flip:
                s = ln - s
            return (x + s, y + h / 2.0 + t) if horiz else (x + w / 2.0 - t, y + s)

        def ts(s):
            u = (s - s_begin) / lam
            i = min(int(u), nb - 1) if u >= 0 else 0
            sg = 1 if i % 2 == 0 else -1
            return sg * A * math.sin(math.pi * (u - i)) if 0 <= u <= nb else 0.0

        for i in range(nb - 1, -1, -1):
            sg = 1 if i % 2 == 0 else -1
            s0 = s_begin + i * lam
            # small leaf on the back of the wave
            def m2(xx, yy, s0=s0, sg=sg):
                s = s0 + 0.3 * lam + xx * (0.62 * lam / 20.0)
                t0 = ts(s)
                room = th / 2.0 - 0.8 - sg * t0
                return W(s, t0 + sg * (-yy / 12.8) * room * 0.94)
            rm = th / 2.0 - 0.8 - A
            _cleaf(cv, m2, "c" if rm >= 6.5 else "d", (i % 2 == 0) != flip, 1.0, 0.62 * lam / 20.0)
            egg = eggs.get(i if not flip else -1 - i)
            if egg:
                c = W(s0 + 0.52 * lam, -sg * (th / 2.0 - 0.8 - (th / 2.0 - 0.8 + A) * 0.5))
                _terminal(cv, egg, c[0], c[1], min(0.5 * (th / 2.0 - 0.8 + A) - 1.0, 0.3 * lam), 1, 0.0, rng)
                continue
            # the large leaf in the hollow
            lf = 1.08 if i < nb - 1 else 0.93
            def m1(xx, yy, s0=s0, sg=sg, lf=lf):
                s = s0 + 0.04 * lam + xx * (lf * lam / 20.0)
                t0 = ts(s)
                room = th / 2.0 - 0.8 + sg * t0
                return W(s, t0 - sg * (-yy / 12.8) * room * 0.96)
            rm = th / 2.0 - 0.8 + A * 0.7
            _cleaf(cv, m1, "a" if rm >= 12 else "c", (i % 2 == 1) != flip, 1.0, lam / 20.0)
        pts = []
        n = max(8, int(nb * 10))
        for j in range(n + 1):
            s = s_begin + span * j / n
            pts.append(W(s, ts(s)))
        if symmetric:
            pts.insert(0, W(ln / 2.0, 0))
        _band(cv, pts, [1.1] * len(pts), False, False)
        e = pts[-1]
        _berry(cv, e[0], e[1], 2.2)

    build(False)
    if symmetric:
        build(True)
        c = (x + w / 2.0, y + h / 2.0)
        if centre in ("flower", "bud"):
            _terminal(cv, "flower", c[0], c[1], rc, 1, 0.3, rng)
        else:
            _terminal(cv, centre, c[0], c[1], rc, 1, 0.0, rng)


def running_scroll(x, y, w, h, orientation=None, seed=0, symmetric=False,
                   terminal="flower", eggs=(), matte_style="deep",
                   matte_pitch=2.0, centre="flower"):
    """A running border of linked, alternating scrolls filling x, y, w, h.

    ``orientation`` "v" or "h" (default: the long side).  Every scroll is
    whole, so the ends are clean.  ``symmetric`` grows both halves outward
    from a central motif (``centre``: a TERMINALS name).  ``eggs`` is a list
    of (index, terminal) hiding a terminal in the index-th scroll.
    """
    rng = random.Random(seed)
    if orientation is None:
        orientation = "h" if w >= h else "v"
    horiz = orientation == "h"
    ln, th = (w, h) if horiz else (h, w)
    r = th / 2.0 - 0.5
    cv = _Canvas()
    if th < 42:
        _matte(cv, x, y, w, h, "stipple" if matte_style == "deep" else matte_style, matte_pitch)
        _vine(cv, x, y, w, h, horiz, rng, symmetric, dict(eggs), centre)
        return cv.markup()
    _matte(cv, x, y, w, h, matte_style, matte_pitch)

    def pos(s):
        return (x + s, y + h / 2.0) if horiz else (x + w / 2.0, y + s)

    centres = []
    rc = 0.0
    if symmetric:
        rc = min(r, max(6.0, r * 0.8))
        span = ln / 2.0 - rc
        n = max(1, int(round(span / (2 * r))))
        pitch = span / n
        rr = min(r, pitch / 2.0)
        for i in range(n):
            centres.append(ln / 2.0 + rc + pitch * (i + 0.5))
    else:
        n = max(1, int(round(ln / (2 * r))))
        pitch = ln / float(n)
        rr = min(r, pitch / 2.0)
        for i in range(n):
            centres.append(pitch * (i + 0.5))
    rr -= 0.3
    scrolls = []
    eggs = dict(eggs)
    for i, s in enumerate(centres):
        c = pos(s)
        sc = dict(x=c[0], y=c[1], r=rr, seed=rng.randrange(1 << 20), stem=None,
                  turns=1.4 + 0.2 * rng.random() if rr >= 16 else 1.15,
                  terminal=eggs.get(i, terminal if rr >= 11 else "bud"))
        if i == 0:
            sc["d"] = 1
            sc["a0"] = (math.pi if horiz else -math.pi / 2) - 0.9
            if symmetric:
                cc = pos(ln / 2.0)
                sc["stem"] = cc
                sc["a0"] = (math.pi if horiz else -math.pi / 2) - 0.5
        else:
            pv = scrolls[-1]
            sc["d"] = -pv["d"]
            ua = math.atan2(c[1] - pv["y"], c[0] - pv["x"])
            sc["a0"] = ua + math.pi
            ga = ua - pv["d"] * 0.95
            rbp = pv["r"] * 0.58
            sc["stem"] = (pv["x"] + rbp * math.cos(ga), pv["y"] + rbp * math.sin(ga))
        scrolls.append(sc)
    # small leaves and berries in the spandrels
    lo, hi = (ln / 2.0, ln) if symmetric else (0.0, ln)
    if horiz:
        box = (x + lo, y + 0.5, x + hi, y + h - 0.5)
    else:
        box = (x + 0.5, y + lo, x + w - 0.5, y + hi)
    pre = [(s["x"], s["y"], s["r"]) for s in scrolls]
    if symmetric:
        cc = pos(ln / 2.0)
        pre.append((cc[0], cc[1], rc))
    fills = [(a, b_, c, rng.randrange(1 << 20))
             for (a, b_, c) in _pack(box[0], box[1], box[2], box[3], 9.0, 2.4, rng,
                                    preset=pre)]
    mirs = [_ID]
    if symmetric:
        cc = pos(ln / 2.0)
        mirs.append(_Mir(ax=cc[0]) if horiz else _Mir(ay=cc[1]))
    for mir in mirs:
        _fillers(cv, fills, scrolls, mir)
        _render_scrolls(cv, scrolls, mir)
    if symmetric:
        cc = pos(ln / 2.0)
        if centre in ("flower", "bud"):
            cv.add("F", _D().circle(cc[0], cc[1], rc))
            _terminal(cv, centre, cc[0], cc[1], rc - 1.5, 1, 0.3, rng)
        else:
            _terminal(cv, centre, cc[0], cc[1], rc, 1, 0.0, rng)
    return cv.markup()


def corner(size, x=0, y=0, quadrant="tl", seed=0, terminal="flower",
           matte_style="deep", matte_pitch=2.0):
    """A square corner piece (size x size at x, y): one scroll springing from
    the corner with leaves thrown along both edges.  ``quadrant`` "tl",
    "tr", "bl", "br" names the page corner it sits in."""
    rng = random.Random(seed)
    cv = _Canvas()
    _matte(cv, x, y, size, size, matte_style, matte_pitch)
    mir = _Mir(ax=(x + size / 2.0) if "r" in quadrant else None,
               ay=(y + size / 2.0) if "b" in quadrant else None)
    r = size * 0.36
    c = (x + size - r - 0.5, y + size - r - 0.5) if size >= 40 else (x + size / 2.0, y + size / 2.0)
    if size < 40:
        r = size / 2.0 - 0.5
    sc = [dict(x=c[0], y=c[1], r=r, seed=rng.randrange(1 << 20),
               stem=(x + 1.5, y + 1.5) if size >= 40 else None,
               turns=1.5, terminal=terminal, d=1, a0=-1.0)]
    pre = [(c[0], c[1], r)]
    circ = _pack(x + 0.5, y + 0.5, x + size - 0.5, y + size - 0.5, max(6.0, size * 0.2),
                 2.4, rng, preset=pre, anchor=(x + size, y))
    more, fills = _link([(c[0], c[1], r)] + circ, rng, rs_min=min(18.5, r))
    more[0].update(sc[0])
    _fillers(cv, fills, more, mir)
    _render_scrolls(cv, more, mir)
    return cv.markup()


# ------------------------------------------------------------------ forest
def _bird(cv, cx, cy, s, flip=1):
    def P(x, y):
        return (cx + s * x * flip, cy + s * y)

    def PP(pts):
        return [P(*q) for q in pts]

    d = _D()
    for (tx, ty, w) in ((-0.98, 0.5, 0.1), (-0.95, 0.2, 0.09), (-0.8, 0.72, 0.09)):
        o = (-0.28, 0.12)
        mx, my = (o[0] + tx) / 2, (o[1] + ty) / 2
        nx, ny = -(ty - o[1]), (tx - o[0])
        d.M(*P(*o)).Q(P(mx + nx * w, my + ny * w), P(tx, ty)).Q(P(mx - nx * w, my - ny * w), P(*o)).Z()
    cv.add("E", d)
    cv.add("F", _D().smooth(PP([(-0.4, 0.12), (-0.2, -0.22), (0.15, -0.32), (0.45, -0.2), (0.5, 0.05),
                                (0.3, 0.3), (-0.05, 0.36), (-0.3, 0.3)])))
    h = P(0.52, -0.36)
    cv.add("F", _D().circle(h[0], h[1], s * 0.2))
    cv.add("F", _D().poly(PP([(0.68, -0.44), (0.99, -0.33), (0.68, -0.25)]), True))
    cv.add("F", _D().smooth(PP([(-0.25, -0.08), (0.1, -0.2), (0.32, -0.05), (0.1, 0.14), (-0.3, 0.2),
                                (-0.56, 0.3)])))
    dd = _D()
    for k in range(4):
        dd.M(*P(0.2 - 0.14 * k, -0.1 + 0.02 * k)).L(*P(-0.02 - 0.16 * k, 0.14 + 0.03 * k))
    for (x, y) in ((0.36, 0.02), (0.3, 0.16), (0.42, 0.14)):
        dd.M(*P(x - 0.06, y)).Q(P(x, y + 0.07), P(x + 0.06, y))
    dd.M(*P(-0.9, 0.46)).L(*P(-0.4, 0.2))
    cv.add("T", dd)
    dd = _D()
    dd.M(*P(0.46, -0.54)).L(*P(0.32, -0.76))
    dd.M(*P(0.54, -0.56)).L(*P(0.5, -0.82))
    dd.M(*P(0.08, 0.36)).L(*P(0.1, 0.6))
    dd.M(*P(0.22, 0.32)).L(*P(0.26, 0.58))
    cv.add("p", dd)
    e = P(0.57, -0.4)
    cv.add("K", _D().circle(e[0], e[1], max(0.7, s * 0.05)))


def _heron(cv, cx, cy, s, flip=1):
    def P(x, y):
        return (cx + s * x * flip, cy + s * y)

    def PP(pts):
        return [P(*q) for q in pts]

    dd = _D()
    dd.M(*P(-0.08, 0.3)).L(*P(-0.1, 0.95)).L(*P(0.06, 0.97))
    dd.M(*P(0.08, 0.3)).L(*P(0.14, 0.62)).L(*P(0.06, 0.95)).L(*P(0.24, 0.97))
    cv.add("p", dd)
    cv.add("F", _D().smooth(PP([(-0.62, 0.3), (-0.4, -0.02), (0.02, -0.1), (0.3, 0.06), (0.2, 0.32),
                                (-0.2, 0.38)])))
    cv.add("F", _D().smooth(PP([(0.1, 0.06), (0.3, -0.2), (0.12, -0.48), (0.2, -0.8), (0.36, -0.82),
                                (0.3, -0.5), (0.48, -0.2), (0.32, 0.14)])))
    cv.add("F", _D().poly(PP([(0.34, -0.9), (0.98, -0.8), (0.36, -0.74)]), True))
    h = P(0.28, -0.82)
    cv.add("F", _D().circle(h[0], h[1], s * 0.12))
    dd = _D()
    for k in range(4):
        dd.M(*P(-0.36 + 0.12 * k, 0.02)).L(*P(-0.5 + 0.14 * k, 0.3))
    dd.M(*P(-0.62, 0.3)).L(*P(-0.78, 0.5))
    dd.M(*P(-0.5, 0.3)).L(*P(-0.62, 0.52))
    dd.M(*P(0.2, -0.86)).L(*P(-0.12, -0.72))
    dd.M(*P(0.2, -0.82)).L(*P(-0.06, -0.62))
    cv.add("T", dd)
    e = P(0.31, -0.84)
    cv.add("K", _D().circle(e[0], e[1], max(0.6, s * 0.035)))


CREATURES = ("bird", "heron", "dog", "squirrel", "paw", "p", "drumsticks", "flower")


def _dot(d, x, y):
    d.M(x, y)
    d.p.append("h.1")
    d.last = "h"


def _lens(d, B, T, th, bow=0.3):
    """one blade from B to T, ``th`` wide, bowed to one side"""
    mx, my = (B[0] + T[0]) / 2.0, (B[1] + T[1]) / 2.0
    ln = math.hypot(T[0] - B[0], T[1] - B[1]) or 1.0
    nx, ny = -(T[1] - B[1]) / ln, (T[0] - B[0]) / ln
    d.M(*B).Q((mx + nx * th * (1 + bow), my + ny * th * (1 + bow)), T)
    d.Q((mx - nx * th * (1 - bow), my - ny * th * (1 - bow)), B).Z()


def _frond(cv, o, ang, ln, curl, wd, fern=False):
    """A palm or fern frond: paired leaflets down a curving rib."""
    sp = _spine(o, ang, ln, curl, n=14, ease=1.0)
    fr = _Frame(sp)
    n = max(4, int(ln / (2.3 if fern else 3.0)))
    d = _D()
    for i in range(n, -1, -1):
        u = 0.1 + 0.86 * i / n
        L = wd * (0.5 + 0.5 * math.sin(math.pi * min(1.0, u * 1.7) * 0.5)) * (1.0 - 0.72 * u * u)
        if L < 1.6:
            continue
        th = max(0.8, min(2.0, L * (0.3 if fern else 0.17)))
        fw = (0.25 if fern else 0.75) * L / ln
        for sd in (1, -1):
            _lens(d, fr.mp((u, 0)), fr.mp((min(1.0, u + fw), sd * L)), th, 0.4 * sd)
    cv.add("E", d)
    cv.add("T", _D().smooth([fr.mp((k / 10.0, 0)) for k in range(11)], False))
    return sp


def _ovate(cv, o, ang, ln, wd, bend=0.0):
    """A plain laurel leaf with midrib and veins."""
    sp = _spine(o, ang, ln, bend, n=8, ease=1.0)
    fr = _Frame(sp)
    up = [fr.mp((u, wd * math.sin(math.pi * u ** 0.8))) for u in (0.0, .15, .3, .45, .6, .75, .9, 1.0)]
    dn = [fr.mp((u, -wd * math.sin(math.pi * u ** 0.8))) for u in (0.9, .75, .6, .45, .3, .15)]
    cv.add("F", _D().smooth(up + dn))
    d = _D().smooth([fr.mp((k / 8.0, 0)) for k in range(8)], False)
    if wd >= 2.4:
        nv = max(2, int(ln / 3.5))
        for k in range(nv):
            u = 0.14 + 0.62 * k / nv
            for sd in (1, -1):
                d.M(*fr.mp((u, 0))).L(*fr.mp((u + 0.16, sd * 0.72 * wd * math.sin(math.pi * (u + 0.16) ** 0.8))))
            # the shadow side takes a second cut
            d.M(*fr.mp((u + 0.07, 0))).L(*fr.mp((u + 0.2, 0.6 * wd * math.sin(math.pi * (u + 0.2) ** 0.8))))
    cv.add("T", d)


def _figleaf(cv, o, ang, R, rng):
    """A broad five-lobed fig / vine leaf on its stalk."""
    ca, sa = math.cos(ang), math.sin(ang)
    c = (o[0] + 0.62 * R * ca, o[1] + 0.62 * R * sa)
    cv.add("P", _D().M(*o).L(*c))

    def pol(a, q):
        return (c[0] + q * math.cos(ang + a), c[1] + q * math.sin(ang + a))
    lens = (0.62, 0.95, 1.12, 0.95, 0.62)
    pts = [pol(math.pi, 0.1 * R)]
    tips = []
    for k in range(5):
        a = (k - 2) * 0.92 + (rng.random() - 0.5) * 0.12
        L = lens[k] * R * (0.92 + 0.12 * rng.random())
        if k:
            pts.append(pol(a - 0.46, 0.36 * R))
        pts += [pol(a - 0.36, 0.7 * L), pol(a - 0.17, 0.93 * L), pol(a + 0.02, L), pol(a + 0.2, 0.9 * L),
                pol(a + 0.36, 0.68 * L)]
        tips.append((a, L))
    cv.add("F", _D().smooth(pts))
    d = _D()
    for a, L in tips:
        d.M(*pol(math.pi, 0.02 * R)).Q(pol(a - 0.1, 0.45 * L), pol(a, 0.86 * L))
        for u in (0.4, 0.58, 0.74):
            for sd, wl in ((1, 0.2), (-1, 0.2)):
                d.M(*pol(a, u * L)).L(*pol(a + sd * wl * (1.25 - u), (u + 0.17) * L))
    # tone: the side away from the light is laid with close cuts
    for a, L in tips:
        t = ang + a
        if math.cos(t) * LIGHT[0] + math.sin(t) * LIGHT[1] < 0.1:
            for i in range(5):
                u = 0.3 + 0.1 * i
                d.M(*pol(a + 0.07, u * L)).L(*pol(a + 0.2 * (1.2 - u) + 0.07, (u + 0.2) * L))
    cv.add("T", d)


def _spray(cv, o, ang, R, rng):
    """Three acanthus leaves springing from one point."""
    for da, fl in ((0.62, 0.8), (-0.62, 0.8), (0.0, 1.0)):
        sg = 1 if da > 0 else (-1 if da < 0 else (1 if rng.random() < 0.5 else -1))
        sp = _spine(o, ang + da - sg * 0.25, 1.9 * R * fl, sg * 0.9, n=10, ease=1.0)
        _hleaf(cv, sp, 0.62 * R * fl, -sg)


def _fiddle(cv, o, ang, R, sg):
    pts = []
    for i in range(22):
        u = i / 21.0
        if u < 0.45:
            q = (o[0] + math.cos(ang) * u * 2.6 * R, o[1] + math.sin(ang) * u * 2.6 * R)
        else:
            t = (u - 0.45) / 0.55
            cc = (o[0] + math.cos(ang) * 1.17 * R - math.sin(ang) * sg * 0.55 * R,
                  o[1] + math.sin(ang) * 1.17 * R + math.cos(ang) * sg * 0.55 * R)
            a = ang - sg * math.pi / 2 + sg * t * 4.6
            rr = 0.55 * R * (1 - 0.8 * t)
            q = (cc[0] + rr * math.cos(a), cc[1] + rr * math.sin(a))
        pts.append(q)
    cv.add("P" if R >= 4 else "p", _D().smooth(pts, False))
    d = _D()
    for i in (2, 4, 6, 8):
        q = pts[i]
        _lens(d, q, (q[0] - math.sin(ang) * sg * -0.5 * R + math.cos(ang) * 0.3 * R,
                     q[1] + math.cos(ang) * sg * -0.5 * R + math.sin(ang) * 0.3 * R), 0.9, 0.3)
    cv.add("E", d)


def _blossom(cv, cx, cy, R, kind, rot, rng):
    if kind == 0:
        _terminal(cv, "flower", cx, cy, R, 1, rot, rng)
    elif kind == 1:
        # a daisy: thin rays round a dark eye
        d = _D()
        n = 9 if R < 8 else 13
        for k in range(n):
            a = rot + 2 * math.pi * k / n
            _lens(d, (cx + 0.2 * R * math.cos(a), cy + 0.2 * R * math.sin(a)),
                  (cx + R * math.cos(a), cy + R * math.sin(a)), max(0.8, 2.0 * R / n), 0.0)
        cv.add("E", d)
        cv.add("F", _D().circle(cx, cy, 0.26 * R))
        cv.add("K", _D().circle(cx, cy, max(0.6, 0.12 * R)))
    else:
        # a bell seen from the side, three petals and a calyx
        ca, sa = math.cos(rot), math.sin(rot)
        o = (cx - 0.8 * R * ca, cy - 0.8 * R * sa)
        d = _D()
        for da in (0.5, -0.5, 0.0):
            _lens(d, o, (o[0] + 1.75 * R * math.cos(rot + da), o[1] + 1.75 * R * math.sin(rot + da)),
                  0.42 * R, 0.5 if da > 0 else (-0.5 if da < 0 else 0))
        cv.add("F", d)
        dd = _D()
        for da in (-0.5, -0.25, 0.0, 0.25, 0.5):
            dd.M(o[0] + 0.5 * R * math.cos(rot + da), o[1] + 0.5 * R * math.sin(rot + da))
            dd.L(o[0] + 1.0 * R * math.cos(rot + da), o[1] + 1.0 * R * math.sin(rot + da))
        cv.add("T", dd)
        _berry(cv, o[0], o[1], max(1.2, 0.2 * R))


def _scene_fig(kind, px, py, size, flip, seed):
    """The heron (``size`` = height, px, py = feet) or the sleeping dog
    (``size`` = length, px = middle, py = ground) exactly as the river
    scene engraver cuts them; "" if that hand is not to be had."""
    try:
        try:
            from . import scene_river as SR
        except Exception:
            import scene_river as SR

        class _O(object):
            pass
        o = _O()
        o.ink = SR._Ink()
        o.seed = seed
        if kind == "heron":
            o.hh, o.hsc, o.hfx, o.hfy = size, size / 94.0, 500.0, 500.0
            SR._Scene.heron(o)
        else:
            o.dogw, o.dogx, o.dogy = size, 500.0, 500.0
            SR._Scene.dog(o)
        o.ink.flush()
        return ('<g transform="translate(%s %s) scale(%d 1) translate(-500 -500)">%s</g>'
                % (_num(int(round(px * 10))), _num(int(round(py * 10))), flip, "".join(o.ink.out)))
    except Exception:
        return ""


def _sticks(cv, cx, cy, s, rot=0.5):
    """a pair of drumsticks lying crossed"""
    for a in (rot, rot + 1.25):
        ca, sa = math.cos(a), math.sin(a)
        A = (cx - s * ca, cy - s * sa)
        B = (cx + s * ca, cy + s * sa)
        wb, wt = max(1.2, 0.09 * s), max(0.8, 0.05 * s)
        nx, ny = -sa, ca
        cv.add("F", _D().poly([(A[0] + nx * wb, A[1] + ny * wb), (B[0] + nx * wt, B[1] + ny * wt),
                               (B[0] - nx * wt, B[1] - ny * wt), (A[0] - nx * wb, A[1] - ny * wb)], True))
        cv.add("F", _D().circle(B[0], B[1], max(1.4, 0.13 * s)))
        cv.add("T", _D().M(A[0] + ca * 0.2 * s, A[1] + sa * 0.2 * s).L(B[0] - ca * 0.3 * s, B[1] - sa * 0.3 * s))


def _vine_p(cv, cx, cy, s):
    """the letter P grown from a vine: a stout stem, a tendril for the bowl"""
    st = [(cx - 0.3 * s, cy + s), (cx - 0.34 * s, cy + 0.3 * s), (cx - 0.3 * s, cy - 0.4 * s), (cx - 0.36 * s, cy - 0.95 * s)]
    bowl = [(cx - 0.36 * s, cy - 0.9 * s), (cx + 0.2 * s, cy - 0.98 * s), (cx + 0.58 * s, cy - 0.6 * s),
            (cx + 0.5 * s, cy - 0.18 * s), (cx + 0.1 * s, cy + 0.02 * s), (cx - 0.3 * s, cy - 0.06 * s),
            (cx - 0.02 * s, cy - 0.3 * s), (cx + 0.14 * s, cy - 0.36 * s)]
    wd = max(2.0, 0.2 * s)
    for pts in (st, bowl):
        d = str(_D().smooth(pts, False))
        cv.items.append(["R", ['<path stroke-width="%s" d="%s"/><path stroke="#fff" stroke-width="%s" d="%s"/>'
                               % (_num(int(round((wd + 1.5) * 10))), d, _num(int(round(wd * 10))), d)]])
    _ovate(cv, (cx - 0.3 * s, cy + 0.75 * s), -0.5, 0.7 * s, 0.16 * s, -0.4)
    _ovate(cv, (cx - 0.34 * s, cy - 0.9 * s), math.pi + 0.6, 0.5 * s, 0.13 * s, 0.4)


def _pawprint(cv, cx, cy, s, rot=0.0):
    ca, sa = math.cos(rot), math.sin(rot)

    def P(x, y):
        return (cx + s * (x * ca - y * sa), cy + s * (x * sa + y * ca))
    cv.add("F", _D().smooth([P(-0.42, 0.34), P(-0.3, 0.02), P(0, -0.1), P(0.3, 0.02), P(0.42, 0.34),
                             P(0.2, 0.5), P(0, 0.42), P(-0.2, 0.5)]))
    for (px, py, pr) in ((-0.5, -0.2, 0.17), (-0.18, -0.48, 0.18), (0.18, -0.48, 0.18), (0.5, -0.2, 0.17)):
        q = P(px, py)
        cv.add("F", _D().circle(q[0], q[1], pr * s))


def _forest_ground(cv, x, y, w, h, rng):
    """Black ground, pricked close at the top and left dark toward the
    foot, with pale stems standing behind the foliage."""
    cv.add("K", _D().poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True))
    d = _D()
    yy = y + 1.2
    row = 0
    while yy < y + h - 0.8:
        f = (yy - y) / h
        keep = 0.3 - 0.24 * f
        xx = x + 1.2 + (1.4 if row % 2 else 0.0)
        while xx < x + w - 0.8:
            if rng.random() < keep:
                _dot(d, xx + (rng.random() - 0.5) * 0.9, yy + (rng.random() - 0.5) * 0.9)
            xx += 2.8
        yy += 2.4
        row += 1
    cv.items.append(["p", [str(d)]])
    g = _D()
    n = max(1, int(w / 45.0))
    for i in range(n):
        bx = x + w * (i + rng.random()) / n
        ht = h * (0.25 + 0.6 * rng.random())
        lean = (rng.random() - 0.5) * 0.5 * ht
        top = (min(max(bx + lean, x + 1), x + w - 1), y + h - ht)
        g.M(bx, y + h - 0.5).Q((bx - lean * 0.3, y + h - ht * 0.55), top)
        if rng.random() < 0.6:
            m = (bx + lean * 0.2, y + h - ht * 0.5)
            g.M(*m).Q((m[0] + 3, m[1] - 3), (min(m[0] + 7, x + w - 1), m[1] - 3.5))
    cv.items.append(["w", [str(g)]])


def _foliage(cv, cx_, cy_, r_, ua, rng, fl):
    """one mass of leaves about a packed circle (drawn larger than the
    circle, so that neighbours overlap)"""
    k = rng.random()
    sg = 1 if rng.random() < 0.5 else -1
    if r_ < 3.0:
        _berries3(cv, cx_, cy_, r_ + 1.0, int(k * 100))
        return
    R = r_ * (1.45 if r_ >= 6 else 1.3)
    o = (cx_ - 0.85 * R * math.cos(ua), cy_ - 0.85 * R * math.sin(ua))
    if r_ < 6.0:
        if k < 0.1:
            _berries3(cv, cx_, cy_, r_, int(k * 1000))
        elif k < 0.25:
            _fiddle(cv, o, ua, R * 0.8, sg)
        elif k < 0.6:
            _ovate(cv, o, ua, 1.9 * R, 0.5 * R, sg * 0.5)
        else:
            _ovate(cv, o, ua + 0.5, 1.7 * R, 0.36 * R, 0.4)
            _ovate(cv, o, ua - 0.5, 1.7 * R, 0.36 * R, -0.4)
    elif r_ < 11.5:
        if k < 0.1 and fl[0] < fl[1]:
            fl[0] += 1
            _blossom(cv, cx_, cy_, r_ * 0.92, fl[0] % 3, ua, rng)
        elif k < 0.38:
            _frond(cv, o, ua - sg * 0.35, 1.9 * R, sg * 0.7, 0.62 * R, fern=k < 0.24)
        elif k < 0.6:
            _figleaf(cv, o, ua, 0.86 * R, rng)
        elif k < 0.82:
            _spray(cv, o, ua, R * 0.95, rng)
        else:
            for da in (0.75, -0.75, 0.0):
                _ovate(cv, o, ua + da, 1.75 * R * (1.0 if da == 0 else 0.8), 0.3 * R, da * 0.5)
    else:
        if k < 0.34:
            for da, f2 in ((0.8, 0.82), (-0.8, 0.82), (0.0, 1.0)):
                s2 = sg if da == 0 else (1 if da > 0 else -1)
                _frond(cv, o, ua + da - s2 * 0.3, 1.85 * R * f2, s2 * 0.75, 0.36 * R, fern=False)
        elif k < 0.58:
            _figleaf(cv, o, ua, 0.86 * R, rng)
        elif k < 0.85:
            _spray(cv, o, ua, R * 0.95, rng)
        else:
            _frond(cv, o, ua - sg * 0.4, 1.95 * R, sg * 0.8, 0.6 * R, fern=True)


def forest_fill(w, h, seed=0, creatures=(), x=0, y=0, rmax=None, ground="night",
                hole=None):
    """White-line forest for dark areas: overlapping masses of acanthus,
    palm and fern fronds, fig leaves, laurel and a few blossoms at three
    scales, the black ground left only as the gaps between the leaves.
    ``creatures`` (names from CREATURES) live in it, partly behind the
    leaves: "heron" and "dog" are cut exactly as in the river scene (and
    are left out where the region is too small to draw them well), "bird"
    perches on a twig, "paw" leaves prints, "drumsticks" lie crossed and
    "p" is a vine-letter.  ``hole`` as in fill_region."""
    rng = random.Random(seed)
    cv = _Canvas()
    cid = "ff%d_%d_%d_%d_%d" % (int(x), int(y), int(w), int(h), seed)
    cv.items.append(["R", ['<clipPath id="%s"><path d="M%s %sh%sv%sh-%sz"/></clipPath><g clip-path="url(#%s)">'
                           % (cid, _num(int(x * 10)), _num(int(y * 10)), _num(int(w * 10)), _num(int(h * 10)),
                              _num(int(w * 10)), cid)]])
    if ground in ("night", "forest"):
        _forest_ground(cv, x, y, w, h, rng)
    else:
        _matte(cv, x, y, w, h, ground)
    blocks, ovals = [], []
    if hole:
        hx, hy, hw_, hh, shp = (list(hole) + ["rect"])[:5]
        if shp == "oval":
            ovals.append((x + hx + hw_ / 2.0, y + hy + hh / 2.0, hw_ / 2.0 + 1.5, hh / 2.0 + 1.5))
        else:
            blocks.append((x + hx - 1.5, y + hy - 1.5, x + hx + hw_ + 1.5, y + hy + hh + 1.5))
    lim = min(h / 2.0 - 0.5, w / 2.0 - 0.5)
    if rmax is None:
        rmax = max(6.0, min(lim, 21.0))

    def free(bx0, by0, bx1, by1, others):
        if bx0 < x or bx1 > x + w or by0 < y or by1 > y + h:
            return False
        if hole and bx1 > x + hx - 3 and bx0 < x + hx + hw_ + 3 and by1 > y + hy - 3 and by0 < y + hy + hh + 3:
            return False
        for (c0, c1, c2, c3) in others:
            if bx1 > c0 - 4 and bx0 < c2 + 4 and by1 > c1 - 4 and by0 < c3 + 4:
                return False
        return True

    # the creatures take their places first, spread along the region
    cre, boxes, preset = [], [], []
    names = [n for n in creatures if n in CREATURES and n != "squirrel"]
    for n_, name in enumerate(names):
        for shrink in (1.0, 0.82, 0.66):
            if name == "heron":
                sz = min(0.84 * h, 0.8 * w, 112.0) * shrink
                if sz < 46:
                    break
                bw, bh_ = 0.72 * sz, sz
            elif name == "dog":
                sz = min(0.3 * w, 1.9 * (h - 4), 150.0) * shrink
                if sz < 62:
                    break
                bw, bh_ = sz, 0.47 * sz
            else:
                sz = max(5.0, min(lim, {"bird": 9.0, "paw": 9.0, "flower": 9.0}.get(name, 14.0)) * shrink)
                bw = bh_ = 2 * sz
            got = None
            for _ in range(40):
                t = (n_ + 0.1 + 0.8 * rng.random()) / len(names)
                if w >= h:
                    cx_ = x + t * w
                    cy_ = y + h - 1.5 - bh_ / 2.0 if name in ("heron", "dog") else y + bh_ / 2 + rng.random() * (h - bh_)
                else:
                    cy_ = y + t * h
                    cx_ = x + bw / 2 + rng.random() * max(0.0, w - bw)
                cx_ = min(max(cx_, x + bw / 2 + 0.5), x + w - bw / 2 - 0.5)
                cy_ = min(max(cy_, y + bh_ / 2 + 0.5), y + h - bh_ / 2 - 0.5)
                bx = (cx_ - bw / 2, cy_ - bh_ / 2, cx_ + bw / 2, cy_ + bh_ / 2)
                if free(bx[0], bx[1], bx[2], bx[3], boxes):
                    got = (name, cx_, cy_, sz, bx)
                    break
            if got:
                cre.append(got)
                boxes.append(got[4])
                if name not in ("heron", "dog"):
                    preset.append((got[1], got[2], sz))
                break
    rbig = min(lim, 36.0)
    nbig = 0 if rbig < rmax * 1.2 else max(1, int(w * h / 13000.0 + 0.5))
    circ = _pack(x + 0.5, y + 0.5, x + w - 0.5, y + h - 0.5, rmax, 2.2, rng, blocks, ovals,
                 preset=preset, vary=0.3, anchor=(x + w * rng.random(), y + h), gap=0.0,
                 big=nbig, rbig=rbig)
    root = (x + w / 2.0, y + h + 10)
    fl = [0, max(1, int(w * h / 9000.0))]
    for i in sorted(range(len(circ)), key=lambda i: circ[i][2]):
        cx_, cy_, r_ = circ[i]
        ua = math.atan2(cy_ - root[1], cx_ - root[0]) + (rng.random() - 0.5) * 1.6
        _foliage(cv, cx_, cy_, r_, ua, rng, fl)
    # the creatures, each in a shadowed clearing with leaves before it
    for (name, cx_, cy_, sz, bx) in cre:
        flip = 1 if cx_ < x + w / 2.0 else -1
        if name in ("heron", "dog"):
            if name == "heron":
                fx, fy = cx_ - flip * 0.06 * sz, bx[3] - 1.0
                mk = _scene_fig("heron", fx, fy, sz, flip, seed)
                ell = (cx_ + flip * 0.03 * sz, cy_ + 0.05 * sz, 0.25 * sz, 0.47 * sz)
            else:
                mk = _scene_fig("dog", cx_, bx[3], sz, flip, seed)
                ell = (cx_, cy_ + 0.06 * sz, 0.5 * sz, 0.2 * sz)
            if not mk:
                continue
            pts = [(ell[0] + ell[2] * math.cos(k * 0.5236), ell[1] + ell[3] * math.sin(k * 0.5236)) for k in range(12)]
            cv.add("K", _D().smooth(pts))
            dd = _D()
            for k in range(int(ell[2] * ell[3] / 14.0)):
                a, q = rng.random() * 6.283, math.sqrt(rng.random()) * 0.92
                _dot(dd, ell[0] + ell[2] * q * math.cos(a), ell[1] + ell[3] * q * math.sin(a))
            cv.items.append(["w", [str(dd)]])
            cv.items.append(["R", [mk]])
            # leaves in front, at the foot
            base = bx[3] + 2.0
            if name == "heron":
                _frond(cv, (cx_ - flip * 0.34 * sz, base), -math.pi / 2 - flip * 0.15, 0.42 * sz, flip * 0.7, 0.085 * sz)
                _spray(cv, (cx_ + flip * 0.3 * sz, base), -math.pi / 2 + flip * 0.2, 0.13 * sz, rng)
                _ovate(cv, (cx_ - flip * 0.1 * sz, base), -math.pi / 2 + flip * 0.5, 0.2 * sz, 0.035 * sz, flip * 0.5)
            else:
                _frond(cv, (cx_ - flip * 0.5 * sz, base), -math.pi / 2 + flip * 0.35, 0.36 * sz, flip * 0.9, 0.075 * sz)
                _spray(cv, (cx_ + flip * 0.52 * sz, base), -math.pi / 2 - flip * 0.3, 0.09 * sz, rng)
                _ovate(cv, (cx_ + flip * 0.1 * sz, base), -math.pi / 2 + flip * 0.8, 0.16 * sz, 0.03 * sz, flip * 0.5)
        elif name == "bird":
            cv.add("P", _D().M(cx_ - 1.6 * sz, cy_ + 0.42 * sz).Q((cx_, cy_ + 0.3 * sz), (cx_ + 1.6 * sz, cy_ + 0.5 * sz)))
            _bird(cv, cx_, cy_, sz * 0.98, flip)
            _ovate(cv, (cx_ - flip * sz * 0.9, cy_ + 0.45 * sz), -0.5 if flip > 0 else math.pi + 0.5,
                   0.9 * sz, 0.22 * sz, 0.3 * flip)
        elif name == "paw":
            _pawprint(cv, cx_ - 0.35 * sz, cy_ + 0.3 * sz, sz * 0.62, -0.3)
            _pawprint(cv, cx_ + 0.4 * sz, cy_ - 0.35 * sz, sz * 0.62, 0.25)
        elif name == "drumsticks":
            _sticks(cv, cx_, cy_, sz * 0.95, 0.4)
            _ovate(cv, (cx_ - 0.9 * sz, cy_ + 0.5 * sz), -0.4, 0.9 * sz, 0.2 * sz, 0.3)
        elif name == "p":
            _vine_p(cv, cx_, cy_, sz * 0.95)
        else:
            _blossom(cv, cx_, cy_, sz * 0.95, 0, 0.3, rng)
    if hole:
        _moulding(cv, x + hx, y + hy, hw_, hh, shp, 7.0, True)
    cv.items.append(["R", ["</g>"]])
    return cv.markup()


def wrap(markup, w, h):
    """Standalone <svg> around child markup (test sheets only)."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d">%s</svg>' % (w, h, w, h, markup))
