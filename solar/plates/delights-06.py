"""delights-06 "Live from Portland - A Portland show, recorded live" (Internet Archive, Live Music Archive).

The scene is a Portland club stage on show night: a draped proscenium with tasselled curtains and a
fringed valance, hanging spot cans throwing beams onto the backline (amp stacks, a drum kit with ride
cymbal and hi-hat), the singer's vintage mic front and centre, the plank stage lip, and the crowd
rim-lit from the stage with a taper's ORTF mic stand rising out of it. The set list varies by date.
Frame at king tier: the stage in a beaded medallion (an arch on the tall plate, a cushion below),
fine scroll from one stem on a punched matte, gold-line borders and beading; the tall ribbon reads
LIVE FROM PORTLAND over a predella with Parker's arms. Easter eggs: Parker's crossed drumsticks
on the kick-drum head, and a taper's reel of tape hidden in the scroll."""
import sys
import math
import random
import engraving_codex as C

# ==== GM ENGINE BEGIN (king-tier scroll: batch 6) ====
# Fine scroll at king tier (Hunt panels, the GRS vise, the presentation Colt): small, densely packed
# logarithmic-feeling scrolls that all grow from one or two stems and branch in a continuous rhythm,
# each sheathed in its own tiny acanthus leaves (shadow cuts on one side, bright cut edge on the
# other); the ground between them punched to a dark matte; fine "gold-line" borders and beading
# round every panel; the subject in an inlaid medallion ringed with beads. A Thai mode swaps the
# leaves for kranok flames and grows packed cloud scrolls.
# Self-contained apart from the house library (engraving_codex); deterministic; standard library.
import math as _m
import random as _r
import re as _re
import engraving_codex as _C

_Rib, _eul, _sm, _ell, _dd, _nn = _C._Rib, _C._euler, _C._smooth, _C._ell_pts, _C._d, _C._n
_PI, _TAU = _m.pi, 2 * _m.pi
_CRS = ' shape-rendering="crispEdges"'


# ---------------------------------------------------------------------------------------------
# occupancy raster (1 px cells): where relief already lies
# ---------------------------------------------------------------------------------------------

_RING = {}
_SPAN = {}


class Occ:
    def __init__(self, w, h):
        self.W, self.H = int(w) + 2, int(h) + 2
        self.m = [bytearray(self.W) for _ in range(self.H)]

    def poly(self, poly, v=1):
        _C._fill_mask(poly, self.m, 0, 0, self.W, self.H)

    def outside(self, poly):
        """mark everything outside poly"""
        keep = Occ(self.W - 2, self.H - 2)
        keep.poly(poly)
        for y in range(self.H):
            r, k = self.m[y], keep.m[y]
            for x in range(self.W):
                if not k[x]:
                    r[x] = 1

    def rect(self, x0, y0, x1, y1):
        for yy in range(max(0, int(y0)), min(self.H, int(_m.ceil(y1)))):
            row = self.m[yy]
            a, b = max(0, int(x0)), min(self.W, int(_m.ceil(x1)))
            if b > a:
                row[a:b] = b"\x01" * (b - a)

    def free(self, x, y):
        xi, yi = int(x), int(y)
        return 0 <= xi < self.W and 0 <= yi < self.H and not self.m[yi][xi]

    def disc_free(self, x, y, r):
        xi, yi = int(x), int(y)
        W, H, m = self.W, self.H, self.m
        if not (0 <= xi < W and 0 <= yi < H) or m[yi][xi]:
            return False
        ring = _RING.get(r)
        if ring is None:
            n = max(6, int(r * 2.2))
            ring = _RING[r] = [(int(round(r * _m.cos(_TAU * k / n))), int(round(r * _m.sin(_TAU * k / n)))) for k in range(n)]
        for dx, dy in ring:
            X, Y = xi + dx, yi + dy
            if not (0 <= X < W and 0 <= Y < H) or m[Y][X]:
                return False
        return True

    def dot(self, x, y, r):
        ri = int(_m.ceil(r))
        xi, yi = int(x), int(y)
        W, H, m = self.W, self.H, self.m
        if ri <= 0:
            return
        if 0 <= yi - ri and yi + ri < H and 0 <= xi - ri and xi + ri < W:
            key = round(r * 2) / 2
            spans = _SPAN.get(key)
            if spans is None:
                spans = _SPAN[key] = [(dy, int(_m.sqrt(max(0., key * key - dy * dy)))) for dy in range(-ri, ri + 1)]
            for dy, hw in spans:
                row = m[yi + dy]
                row[xi - hw:xi + hw + 1] = b"\x01" * (2 * hw + 1)
            return
        r2 = r * r
        for yy in range(max(0, yi - ri), min(H, yi + ri + 1)):
            row = m[yy]
            dy = yy + .5 - y
            for xx in range(max(0, xi - ri), min(W, xi + ri + 1)):
                dx = xx + .5 - x
                if dx * dx + dy * dy <= r2:
                    row[xx] = 1

    def clearance(self, x, y, rmax):
        r = 1.
        while r < rmax and self.disc_free(x, y, r):
            r += 1.
        return r - 1.


class _Pen2:
    """path data in integer half-px (for transform="scale(.5)"), relative after the first point"""

    def __init__(self):
        self.o = []
        self.cur = None

    def add(self, pts, close=False, tol=.3):
        if len(pts) < 2:
            return
        if tol:
            pts = _C._dp(pts, tol)
        X = [int(round(p[0] * 2)) for p in pts]
        Y = [int(round(p[1] * 2)) for p in pts]
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


class Canvas(_C.Canvas):
    """the house Canvas, emitted at half-px precision with coarser simplification (smaller)"""

    def svg(self, tol_w=.7, tol_l=.7):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for w, lines in strokes.items():
                for pl in lines:
                    _C._clip_runs(pl, mask, x0, y0, W, H, out[w])
            for poly in polys:
                _C._fill_mask(poly, mask, x0, y0, W, H)
        T = ' transform="scale(.5)"'
        res = []
        # white shapes go out in runs of equal outline weight, each run one path filled white and
        # stroked with its own outline: later runs cover earlier runs' outlines (painter's order)
        runs = []
        for polys, ow, _ in self.objs:
            if not polys:
                continue
            if not runs or runs[-1][0] != ow:
                runs.append((ow, []))
            runs[-1][1].extend(polys)
        for ow, polys in runs:
            pen = _Pen2()
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_w)
            if pen.o:
                st = f'stroke="#000" stroke-width="{_nn(ow * 2)}"' if ow else 'stroke="none"'
                res.append(f'<path{T} d="{pen.d()}" fill="#fff" {st}/>')
        for w in (.5, 1., 1.5):
            if out[w]:
                pen = _Pen2()
                for pl in out[w]:
                    if len(pl) > 1 and (len(pl) > 2 or abs(pl[0][0] - pl[-1][0]) + abs(pl[0][1] - pl[-1][1]) > .7):
                        pen.add(pl, False, tol_l)
                res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_nn(w * 2)}"/>')
        return "".join(res)


# ---------------------------------------------------------------------------------------------
# growth: stems that curl into spirals and branch, with leaves
# ---------------------------------------------------------------------------------------------

class _Stem:
    __slots__ = ("P", "W", "H", "sg", "depth", "R", "leafed")


def _grow(occ, x, y, hd, sg, L, Rm, w0, clear=1.6, re=None, lead=0., lk=-1.):
    """Grow one stem: radius of curvature falls from Rm to re over L (a spiral that winds about
    1.4 turns when L = 3 Rm). Stops where it would run into relief; the stem's own body is marked
    a little behind the growing tip."""
    re = re or max(1.3, w0 * .55)
    P, W, Hd = [(x, y)], [w0], [hd]
    s, ds = 0., 1.
    lag = []
    while s < L:
        if s < lead:
            hd += lk * sg * ds / (Rm * 3.)
            u = 0.
        else:
            u = (s - lead) / max(1., L - lead)
            R = re + (Rm - re) * (1 - u) ** 1.15
            hd += sg * ds / R
        w = max(.45, w0 * (1 - .7 * (s / L) ** .9))
        nx, ny = x + _m.cos(hd) * ds, y + _m.sin(hd) * ds
        probe = w + clear
        fx, fy = nx + _m.cos(hd) * probe, ny + _m.sin(hd) * probe
        lx, ly = nx + _m.cos(hd + 1.1) * probe, ny + _m.sin(hd + 1.1) * probe
        rx, ry = nx + _m.cos(hd - 1.1) * probe, ny + _m.sin(hd - 1.1) * probe
        if not occ.free(fx, fy) or (s > w0 + 3 and not (occ.free(lx, ly) and occ.free(rx, ry))):
            break
        x, y = nx, ny
        P.append((x, y))
        W.append(w)
        Hd.append(hd)
        lag.append((x, y, w))
        if len(lag) > 4 + int(w + clear):
            px, py, pw = lag.pop(0)
            occ.dot(px, py, pw + .6)
        s += ds
    for px, py, pw in lag:
        occ.dot(px, py, pw + .6)
    occ.dot(P[0][0], P[0][1], W[0] + .5)
    st = _Stem()
    st.P, st.W, st.H, st.sg = P, W, Hd, sg
    st.R = Rm
    return st


def _lobe(x, y, hd, ln, wd, bend):
    n = max(6, int(ln * 1.1))
    P = _eul(x, y, hd, ln, lambda u: bend / ln * (1 + 2 * u), n)
    W = [max(.35, wd * _m.sin(_PI * min(1., (i / n) / .55) * .5) ** .8 * (1 if i / n < .55 else ((1 - i / n) / .45) ** .7))
         for i in range(n + 1)]
    return _Rib(P, W, W)


class Leaf:
    """An acanthus leaf on a curved midrib: its outer edge a run of round scalloped lobes leaning to
    the tip, each notch creased back to the midrib; the inner edge plainer; the tip rolls over.
    A kranok flame instead swells and hooks, with licks off its back."""

    def __init__(self, x, y, hd, ln, wd, bend, lobes=3, kranok=False, side=1, curl=1.3):
        n = max(10, int(ln * .9))
        G = _GN55

        def kf(u):
            return (bend + side * curl * _sm(.55, 1., u) ** 2 / G) / ln
        self.P = P = _eul(x, y, hd, ln, kf, n)
        self.L = ln
        self.side = side
        u0, u1 = .1, .86
        out_, in_ = [], []
        for i in range(n + 1):
            u = i / n
            e = _m.sin(_PI * .5 * min(1., u / .38)) ** .6 if u < .38 else ((1 - u) / .62) ** (1.1 if kranok else .7)
            e = max(.1, e)
            if kranok:
                fo = 1. - .32 * _sm(.48, .6, u) * (1 - _sm(.6, .72, u)) - .25 * _sm(.72, .8, u) * (1 - _sm(.8, .88, u))
                fi = .7
            elif u0 < u < u1:
                v = ((u - u0) / (u1 - u0) * lobes) % 1.
                v = v ** .8
                fo = .8 * (.66 + .34 * _m.sqrt(max(0., 1 - (2 * v - 1) ** 2)))
                fi = .5 + .08 * _m.sqrt(max(0., 1 - (2 * ((v + .5) % 1.) - 1) ** 2))
            else:
                fo, fi = 1., .68
            out_.append(max(.35, wd * e * fo))
            in_.append(max(.35, wd * e * fi))
        WL, WR = (out_, in_) if side > 0 else (in_, out_)
        self.R = _Rib(P, WL, WR)
        # lean the lobes toward the tip: the lobed edge is shifted forward by its excess width
        R = self.R
        base = [wd * max(.1, (_m.sin(_PI * .5 * min(1., (i / n) / .38)) ** .6 if i / n < .38 else ((1 - i / n) / .62) ** .7)) * .53
                for i in range(n + 1)]
        T = []
        for i in range(n + 1):
            p, q = P[max(0, i - 1)], P[min(n, i + 1)]
            tl = _m.hypot(q[0] - p[0], q[1] - p[1]) or 1
            T.append(((q[0] - p[0]) / tl, (q[1] - p[1]) / tl))
        lean = 0. if kranok else .55
        edge = []
        for i in range(n + 1):
            wv = out_[i]
            nx, ny = R.N[i]
            f = lean * max(0., wv - base[i])
            edge.append((P[i][0] + side * nx * wv + T[i][0] * f, P[i][1] + side * ny * wv + T[i][1] * f))
        inner = [R.at(i / n, -side) for i in range(n + 1)]
        self.edge = edge
        self.poly = edge + inner[::-1]
        self.notches = [] if kranok else [u0 + (u1 - u0) * j / lobes for j in range(1, lobes)] + [u1]
        self.parts = [(self.R, -side)]

    def polys(self):
        return [self.poly]


def _leaf_poly(x, y, hd, ln, wd, bend, lobes=3, kranok=False, side=1, curl=1.3):
    return Leaf(x, y, hd, ln, wd, bend, lobes, kranok, side, curl)


def _gn(e0):
    return sum(_sm(e0, 1., (i + .5) / 60) ** 2 for i in range(60)) / 60


_GN55 = _gn(.55)


def _leaf_fits(occ, lf, skip=0., pad=.6):
    x0, y0 = lf.P[0]
    for R, _ in lf.parts:
        for i in range(1, R.n, 2):
            u = i / (R.n - 1)
            for s_ in (1.15 * lf.side, .5 * lf.side, 0.):
                p = R.at(u, s_)
                if _m.hypot(p[0] - x0, p[1] - y0) < skip:
                    continue
                if not occ.free(p[0], p[1]):
                    return False
    return True




def _chamfer(D, i0, i1, j0, j1):
    """3-4 chamfer distance transform of D (0 = occupied) over the box, in place"""
    for j in range(j0, j1):
        Dj, Dp = D[j], (D[j - 1] if j > j0 else None)
        for i in range(i0, i1):
            v = Dj[i]
            if v:
                if i > i0 and Dj[i - 1] + 3 < v:
                    v = Dj[i - 1] + 3
                if Dp is not None:
                    if Dp[i] + 3 < v:
                        v = Dp[i] + 3
                    if i > i0 and Dp[i - 1] + 4 < v:
                        v = Dp[i - 1] + 4
                    if i + 1 < i1 and Dp[i + 1] + 4 < v:
                        v = Dp[i + 1] + 4
                Dj[i] = v
    for j in range(j1 - 1, j0 - 1, -1):
        Dj, Dn = D[j], (D[j + 1] if j + 1 < j1 else None)
        for i in range(i1 - 1, i0 - 1, -1):
            v = Dj[i]
            if v:
                if i + 1 < i1 and Dj[i + 1] + 3 < v:
                    v = Dj[i + 1] + 3
                if Dn is not None:
                    if Dn[i] + 3 < v:
                        v = Dn[i] + 3
                    if i + 1 < i1 and Dn[i + 1] + 4 < v:
                        v = Dn[i + 1] + 4
                    if i > i0 and Dn[i - 1] + 4 < v:
                        v = Dn[i - 1] + 4
                Dj[i] = v


class Scroll:
    """A packed field of king-tier scroll grown into an occupancy raster.
    seeds: list of (x, y, heading_rad, curl_sign, length, Rm, w0)."""

    def __init__(self, w, h, occ, seed=0, scale=1., thai=False, leaf_density=1.):
        self.w, self.h, self.occ = w, h, occ
        self.rng = _r.Random(seed)
        self.k = scale
        self.thai = thai
        self.ld = leaf_density
        self.gap = 1.
        self.lmin = 5. * scale
        self.stems, self.leaves, self.eyes, self.figs = [], [], [], []

    def grow(self, seeds, max_stems=400, min_len=None):
        rng, occ, k = self.rng, self.occ, self.k
        min_len = min_len or 7 * k
        q = [(-s[4], i, s, 0) for i, s in enumerate(seeds)]
        cnt = len(q)
        made = 0
        for j in range(len(q)):
            _, i_, sd_, dpt = q[j]
            x, y = sd_[0], sd_[1]
            need = sd_[6] + 3.
            if not occ.disc_free(x, y, need):
                best = None
                for rr in range(2, 40, 2):
                    for t in range(16):
                        a_ = _TAU * t / 16
                        px, py = x + rr * _m.cos(a_), y + rr * _m.sin(a_)
                        if occ.disc_free(px, py, need):
                            best = (px, py)
                            break
                    if best:
                        break
                if best:
                    q[j] = (q[j][0], i_, (best[0], best[1]) + tuple(sd_[2:]), dpt)
        while q and made < max_stems:
            q.sort()
            _, _, sd_, depth = q.pop(0)
            x, y, hd, sg, L, Rm, w0 = sd_[:7]
            lead = sd_[7] if len(sd_) > 7 else 0.
            lk = sd_[8] if len(sd_) > 8 else -1.
            st = _grow(occ, x, y, hd, sg, L, Rm, w0, 1.4 + .25 * k, lead=lead, lk=lk)
            if len(st.P) < min_len:
                continue
            st.depth = depth
            self.stems.append(st)
            made += 1
            n = len(st.P)
            # branch points along the convex side, curling the other way (the S rhythm of Hunt)
            step = max(5., Rm * .9)
            s = step * rng.uniform(.6, .9)
            side = -sg
            while s < n * .85:
                i = int(s)
                if i < 2 or i >= n - 2:
                    break
                px, py = st.P[i]
                h0 = st.H[i]
                w = st.W[i]
                cL = L * rng.uniform(.42, .6) * (1 - .45 * i / n)
                cR = max(3.2 * k, Rm * rng.uniform(.45, .6) * (1 - .35 * i / n))
                cw = max(.6, w * .8)
                best = None
                for side in (-1, 1):
                    bx = px + _m.cos(h0 + side * _PI / 2) * (w + .6)
                    by = py + _m.sin(h0 + side * _PI / 2) * (w + .6)
                    bh = h0 + side * rng.uniform(.5, .8)
                    room = 0
                    for d_ in range(int(w + 3), int(w + 3 + cR * 1.4), 2):
                        if not occ.disc_free(bx + _m.cos(bh) * d_, by + _m.sin(bh) * d_, 1.5):
                            break
                        room += 2
                    if room > 4 and (best is None or room > best[0]):
                        best = (room, bx, by, bh, side)
                if best and cL > min_len:
                    room, bx, by, bh, side = best
                    cnt += 1
                    q.append((-cL, cnt, (bx, by, bh, side, cL, min(cR, room * .9 + 3), cw), depth + 1))
                s += step * rng.uniform(.75, 1.15)
        return self

    def dress(self, x0, y0, x1, y1, rbig, rmax, nbig):
        """the house sequence: big flowing scrolls into the largest openings, leaves, smaller scrolls
        sprouting off them, leaves again, the last curls, and leaves down to the smallest"""
        k = self.k
        self.flow(x0, y0, x1, y1, rbig * k, rmax, nbig).add_leaves()
        self.sprout(6. * k, 1).add_leaves()
        self.sprout(4.5 * k, 1)
        lm = self.lmin
        self.lmin = 4. * k
        self.add_leaves()
        self.sprout(3.4 * k, 1)
        self.lmin = 3.5 * k
        self.add_leaves()
        self.lmin = lm
        return self

    def flow(self, x0, y0, x1, y1, rmin=9., rmax=60., max_n=40, cell=4):
        """Fill the region with scroll that flows: repeatedly find the largest open ground (a
        distance transform of the relief) and grow a scroll into it from the nearest point of an
        existing stem, curling round the opening's centre; so every scroll springs from another
        and the biggest spirals take the biggest spaces."""
        rng, occ, k = self.rng, self.occ, self.k
        gx0, gy0 = int(x0 // cell), int(y0 // cell)
        GW, GH = int((x1 - x0) // cell) + 1, int((y1 - y0) // cell) + 1
        INF = 1 << 20
        D = [[INF] * GW for _ in range(GH)]
        m = occ.m
        for j in range(GH):
            yy = int(y0 + (j + .5) * cell)
            row = m[yy] if 0 <= yy < occ.H else None
            Dj = D[j]
            for i in range(GW):
                xx = int(x0 + (i + .5) * cell)
                if row is None or not (0 <= xx < occ.W) or row[xx]:
                    Dj[i] = 0
        _chamfer(D, 0, GW, 0, GH)
        sc = cell / 3.
        made = 0
        tried = set()
        while made < max_n:
            best, bi, bj = 0, -1, -1
            for j in range(GH):
                Dj = D[j]
                mj = max(Dj)
                if mj > best:
                    i = Dj.index(mj)
                    if (i, j) not in tried:
                        best, bi, bj = mj, i, j
            c = best * sc
            if c < rmin:
                break
            tried.add((bi, bj))
            px, py = x0 + (bi + .5) * cell, y0 + (bj + .5) * cell
            R = min(rmax, c * .55) * rng.uniform(.9, 1.)
            # the nearest stem point to spring from
            near = None
            nd = c * 2.6 + 12
            for st in self.stems:
                P = st.P
                for q in range(0, len(P) - 3, 3):
                    d_ = abs(P[q][0] - px) + abs(P[q][1] - py)
                    if d_ < nd:
                        nd, near = d_, (st, q)
            if near:
                st, q = near
                qx, qy = st.P[q]
                h0, w = st.H[q], st.W[q]
                to = _m.atan2(py - qy, px - qx)
                side = 1 if _m.sin(to - h0) > 0 else -1
                bx = qx + _m.cos(h0 + side * _PI / 2) * (w + .5)
                by = qy + _m.sin(h0 + side * _PI / 2) * (w + .5)
                dist = _m.hypot(px - bx, py - by)
                # head off tangent to a circle round the opening, so the spiral winds round it
                sg = rng.choice((-1, 1))
                hd = to - sg * _m.asin(min(1., R / max(R, dist)))
                ww = max(1.2, min(w * .9, R * .12))
                lead = min(max(0., dist - R), R * 1.2)
                ch = _grow(occ, bx, by, hd, sg, R * 3.3 + lead, R, ww, 1.4 + .25 * k, lead=lead, lk=0.)
                ch.depth = st.depth + 1
            else:
                sg = rng.choice((-1, 1))
                hd = rng.uniform(0, _TAU)
                sx, sy = px - _m.cos(hd + sg * _PI / 2) * R, py - _m.sin(hd + sg * _PI / 2) * R
                ww = max(1.2, R * .12)
                ch = _grow(occ, sx, sy, hd, sg, R * 3.3, R, ww, 1.4 + .25 * k)
                ch.depth = 1
            if len(ch.P) < 6:
                continue
            self.stems.append(ch)
            made += 1
            # update the distance field near the new stem
            xs = [p[0] for p in ch.P]
            ys = [p[1] for p in ch.P]
            reach = rmax * 1.5 + 6
            i0, i1 = max(0, int((min(xs) - reach - x0) / cell)), min(GW, int((max(xs) + reach - x0) / cell) + 1)
            j0, j1 = max(0, int((min(ys) - reach - y0) / cell)), min(GH, int((max(ys) + reach - y0) / cell) + 1)
            for p in ch.P:
                i, j = int((p[0] - x0) / cell), int((p[1] - y0) / cell)
                if 0 <= i < GW and 0 <= j < GH:
                    D[j][i] = 0
            _chamfer(D, i0, i1, j0, j1)
        return self

    def sprout(self, rmin=4., passes=3, max_new=900):
        """grow further scrolls off existing stems into the ground left beside them, each sized to
        the room it finds, so every scroll springs from another (Hunt's continuous flow)"""
        rng, occ, k = self.rng, self.occ, self.k
        new = 0
        for ps in range(passes):
            grown = 0
            for st in sorted(self.stems, key=lambda s: -len(s.P)):
                n = len(st.P)
                if n < 8:
                    continue
                i = 3 + rng.randrange(3)
                while i < n - 4 and new < max_new:
                    px, py = st.P[i]
                    h0, w = st.H[i], st.W[i]
                    best = None
                    for side in (-1, 1):
                        bx = px + _m.cos(h0 + side * _PI / 2) * (w + .5)
                        by = py + _m.sin(h0 + side * _PI / 2) * (w + .5)
                        bh = h0 + side * rng.uniform(.6, 1.)
                        # room: the free disc just beyond the sprout point, in its direction
                        for dd in (2.5, 4.):
                            cx_ = bx + _m.cos(bh) * (dd + rmin)
                            cy_ = by + _m.sin(bh) * (dd + rmin)
                            c = occ.clearance(cx_, cy_, 22 * k)
                            if c >= rmin and (best is None or c > best[0]):
                                best = (c, bx, by, bh, side)
                    if best:
                        c, bx, by, bh, side = best
                        R = max(2.6, c * .62)
                        cw = max(.55, min(w * .8, R * .16))
                        ch = _grow(occ, bx, by, bh, side, R * 3.1, R, cw, 1.3 + .2 * k)
                        if len(ch.P) >= 6:
                            ch.depth = st.depth + 1
                            self.stems.append(ch)
                            new += 1
                            grown += 1
                            i += int(R * 1.2) + 3
                            continue
                    i += 3
            if not grown:
                break
        return self

    def fill_gaps(self, x0, y0, x1, y1, rmin=4.5, grid=3, max_n=500):
        """spawn small curls into whatever free ground is left (nearest the stems first)"""
        rng, occ, k = self.rng, self.occ, self.k
        cand = []
        for yy in range(int(y0) + 2, int(y1) - 1, grid):
            for xx in range(int(x0) + 2, int(x1) - 1, grid):
                cand.append((xx + rng.random() * grid, yy + rng.random() * grid))
        rng.shuffle(cand)
        n = 0
        for (cx, cy) in cand:
            if n >= max_n:
                break
            if not occ.disc_free(cx, cy, rmin):
                continue
            c = occ.clearance(cx, cy, 30 * k)
            if c < rmin:
                continue
            R = c * .55
            sg = rng.choice((-1, 1))
            hd = rng.uniform(0, _TAU)
            sx, sy = cx - _m.cos(hd + sg * _PI / 2) * R * .9, cy - _m.sin(hd + sg * _PI / 2) * R * .9
            st = _grow(occ, sx, sy, hd, sg, R * 3.2, R, max(.6, min(1.6 * k, R * .16)), 1.3)
            if len(st.P) >= 5:
                st.depth = 9
                self.stems.append(st)
                n += 1
        return self

    def add_leaves(self, small=False):
        """sheath the stems with acanthus (or kranok) leaves lying along them, largest stems first;
        each leaf is grown as long as the ground allows"""
        rng, occ, k = self.rng, self.occ, self.k
        stems = [st for st in self.stems if not getattr(st, "leafed", False)]
        for st in stems:
            st.leafed = True
        # leaves may overlap one another (they are painted under the stems, in depth order) but
        # not the stems or the fixed architecture: test against a snapshot taken before them
        snap = Occ(1, 1)
        snap.W, snap.H = occ.W, occ.H
        snap.m = [bytearray(r) for r in occ.m]
        for st in sorted(stems, key=lambda s: -len(s.P)):
            n = len(st.P)
            s = 1.5 + rng.random() * 2
            while s < n - 4:
                i = int(s)
                px, py = st.P[i]
                w = st.W[i]
                h0 = st.H[i]
                kloc = (st.H[min(n - 1, i + 3)] - st.H[i]) / 3.
                placed = 0.
                order = (-st.sg, st.sg) if rng.random() < .75 else (st.sg, -st.sg)
                for side in order:
                    bx = px + _m.cos(h0 + side * _PI / 2) * (w * .6)
                    by = py + _m.sin(h0 + side * _PI / 2) * (w * .6)
                    a = h0 + side * rng.uniform(.3, .55)
                    lmax = min(16 * k, 6 + (st.R or 10) * 1.2)
                    best = None
                    # cheap probe along the leaf's arc: centre and a widening outer edge
                    kk = kloc * .8
                    hx, hy, ha = bx, by, a
                    d = 0.
                    skip = w + 1.8
                    while d < lmax:
                        ha += kk
                        hx += _m.cos(ha)
                        hy += _m.sin(ha)
                        d += 1.
                        if d < skip:
                            continue
                        o = .3 * d + .8
                        ex_ = hx + _m.cos(ha + side * _PI / 2) * o
                        ey_ = hy + _m.sin(ha + side * _PI / 2) * o
                        if not (snap.free(hx, hy) and snap.free(ex_, ey_)):
                            break
                        if d > skip + d * .6 and not (occ.free(hx, hy) and occ.free(ex_, ey_)):
                            break
                    ln = d * rng.uniform(.92, 1.05)
                    tries = 0
                    while ln >= self.lmin and tries < 3:
                        wd = ln * (.36 if self.thai else .5)
                        R = _leaf_poly(bx, by, a, ln, wd, kloc * ln * .8, max(2, min(5, int(ln / 5.5))), self.thai, side,
                                       1.6 + .8 * rng.random())
                        if _leaf_fits(snap, R, w + 1.8):
                            best = R
                            break
                        ln *= .78
                        tries += 1
                    if best is not None:
                        self.leaves.append((best, side, st.depth))
                        for pg in best.polys():
                            occ.poly(pg)
                        for p in best.P[::2]:
                            occ.dot(p[0], p[1], 1.)
                        placed = max(placed, best.L)
                        if rng.random() < .6:
                            break
                s += max(3., placed * rng.uniform(.45, .6) if placed else 2.5)
        return self

    def paint(self, cv, min_outline=.5):
        """into a Canvas: deepest first so parents lie over their branches; leaves under stems"""
        items = []
        for st in self.stems:
            items.append((st.depth, 1, st))
        for lf in self.leaves:
            items.append((lf[2], 0, lf))
        items.sort(key=lambda t: (-t[0], t[1]))
        for depth, kind, it in items:
            if kind == 0:
                R, side, _ = it
                self._paint_leaf(cv, R, side)
            else:
                self._paint_stem(cv, it)

    def _paint_leaf(self, cv, lf, side):
        R = lf.R
        c = -side                      # shadow half: toward the stem; the lobed edge is the bright cut
        cv.obj([lf.poly], .5)
        wo = max(R.wl if side > 0 else R.wr)
        wi = max(R.wr if side > 0 else R.wl)
        if wi > 1.2:
            cv.hair(_C._fill_lines(R, .2 * c, .95 * c, 1.5, .04, .96, 3))
        if wo > 2.:
            cv.hair(R.contour(.08 * side, .05, .85, minw=1.))           # the vein
        nE = len(lf.edge) - 1
        for un in lf.notches:
            if R.width(un, side) > 1.6:
                cv.line([lf.edge[min(nE, int(un * nE + .5))], R.at(un - .035, .5 * side)])
                cv.hair([R.at(un - .035, .5 * side), R.at(un - .07, .14 * side)])
        if wo > 3.5:
            for un in lf.notches:
                cv.hair([R.at(un - .02, .95 * side), R.at(un - .06, .62 * side)])
        if lf.L > 10:
            cv.line(R.inset(c, lambda u: .5 if .08 < u < .85 else None, 0, 1))
        if lf.L > 12:
            k = int(R.n * .84)
            T = _Rib(R.P[k:], R.wl[k:], R.wr[k:])
            cv.hair(T.contour(.55 * side, 0, 1, minw=.7))

    def _paint_stem(self, cv, st):
        P, W = st.P, st.W
        R = _Rib(P, W, W)
        wmax = W[0]
        cv.obj([R.outline()], 1. if wmax > 1.6 else .5)
        c = st.sg                       # the inside of the curl, in shadow
        if wmax > 1.1:
            cv.hair(R.contour(.45 * c, 0., .97, minw=1.2))
        if wmax > 2.2:
            cv.hair(R.contour(.75 * c, 0., .9, minw=2.))
            cv.line(R.inset(c, lambda u: .5, 0., .95))
        if wmax > 3.:
            cv.hair(R.contour(-.35 * c, .05, .7, minw=3.))
        # the tight eye
        ex, ey = P[-1]
        rr = max(.9, W[-1] * .9)
        cv.line(_ell(ex, ey, rr * .55, rr * .55, 8))


# ---------------------------------------------------------------------------------------------
# the matte ground, borders, beading, medallion
# ---------------------------------------------------------------------------------------------

def _stipple_tile(seed, T, n):
    rng = _r.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < 6000:
        tries += 1
        x, y = rng.randrange(T), rng.randrange(T)
        if any(min((x - a) % T, (a - x) % T) < 2 and min((y - b) % T, (b - y) % T) < 2 for a, b in out):
            continue
        out.append((x, y))
    return out


def gm_defs():
    """punched matte: black, struck with single white 1 px punch marks (two densities)"""
    d1 = "".join(f"M{x},{y}h1v1h-1z" for x, y in _stipple_tile(11, 20, 34))
    d2 = "".join(f"M{x},{y}h1v1h-1z" for x, y in _stipple_tile(5, 20, 16))
    return ('<defs>'
            f'<pattern id="gmP" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M0,0h20v20h-20z" fill="#000"/>'
            f'<path d="{d1}" fill="#fff"{_CRS}/></pattern>'
            f'<pattern id="gmQ" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M0,0h20v20h-20z" fill="#000"/>'
            f'<path d="{d2}" fill="#fff"{_CRS}/></pattern>'
            '</defs>')


def matte(d, dense=True):
    return f'<path d="{d}" fill="url(#{"gmP" if dense else "gmQ"})" stroke="none"/>'


def rect_d(x0, y0, x1, y1):
    return f"M{_nn(x0)},{_nn(y0)}H{_nn(x1)}V{_nn(y1)}H{_nn(x0)}z"


def gold_border(x0, y0, x1, y1, beads=True, r=1.5):
    """a fine triple border on the matte: a bright 1.5 px 'gold' wire between 0.5 px cuts, then a
    bead row inside it. Returns (svg, inner rect)."""
    o = []
    # white band with black hairlines (wire inlay)
    o.append(f'<path d="{rect_d(x0, y0, x1, y1)}{rect_d(x0 + 3, y0 + 3, x1 - 3, y1 - 3)}" fill="#fff" fill-rule="evenodd" stroke="none"/>')
    o.append(f'<path d="{rect_d(x0 + .25, y0 + .25, x1 - .25, y1 - .25)}{rect_d(x0 + 2.75, y0 + 2.75, x1 - 2.75, y1 - 2.75)}" '
             f'fill="none" stroke="#000" stroke-width=".5"{_CRS}/>')
    o.append(f'<path d="{rect_d(x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5)}" fill="none" stroke="#000" stroke-width=".5" stroke-dasharray="1.5 1.5"{_CRS}/>')
    ix0, iy0, ix1, iy1 = x0 + 3, y0 + 3, x1 - 3, y1 - 3
    if beads:
        p = 2 * r + 1.
        yy = iy0 + r + .5
        o.append(bead_line([(ix0 + r + 1, yy), (ix1 - r - 1, yy)], r))
        o.append(bead_line([(ix0 + r + 1, iy1 - r - .5), (ix1 - r - 1, iy1 - r - .5)], r))
        if iy1 - iy0 > 30:
            o.append(bead_line([(ix0 + r + .5, iy0 + 2 * r + 2), (ix0 + r + .5, iy1 - 2 * r - 2)], r))
            o.append(bead_line([(ix1 - r - .5, iy0 + 2 * r + 2), (ix1 - r - .5, iy1 - 2 * r - 2)], r))
        ix0, iy0, ix1, iy1 = ix0 + 2 * r + 1, iy0 + 2 * r + 1, ix1 - 2 * r - 1, iy1 - 2 * r - 1
    return "".join(o), (ix0, iy0, ix1, iy1)


def bead_line(pts, r=1.5, closed=False):
    """beads strung along a polyline, drawn as round dashes: a black ring, a white bead, and a
    small dark crescent offset to the lower right (three strokes on one path)"""
    seq = pts + ([pts[0]] if closed else [])
    L = sum(_m.hypot(seq[i][0] - seq[i - 1][0], seq[i][1] - seq[i - 1][1]) for i in range(1, len(seq)))
    p = 2 * r + 1.
    n = max(1, int(L / p))
    p = L / n
    d = _dd(seq, tol=.1)
    da = f'stroke-dasharray="0 {_nn(p)}" stroke-linecap="round" fill="none"'
    return (f'<path d="{d}" stroke="#000" stroke-width="{_nn(2 * r + 1)}" {da}/>'
            f'<path d="{d}" stroke="#fff" stroke-width="{_nn(2 * r)}" {da}/>'
            f'<path d="{d}" stroke="#000" stroke-width="{_nn(max(.8, r * .7))}" {da} transform="translate({_nn(r * .45)},{_nn(r * .45)})"/>'
            f'<path d="{d}" stroke="#fff" stroke-width="{_nn(max(.8, r * .7))}" {da} transform="translate({_nn(r * .2)},{_nn(r * .2)})"/>')


def shape_pts(cx, cy, a, b, kind="oval", n=120):
    pts = []
    for i in range(n):
        t = _TAU * i / n
        c_, s_ = _m.cos(t), _m.sin(t)
        e = {"oval": 2., "squircle": 2.8, "cushion": 3.6, "round": 2.}.get(kind, 2.)
        x = cx + a * _m.copysign(abs(c_) ** (2 / e), c_)
        y = cy + b * _m.copysign(abs(s_) ** (2 / e), s_)
        if kind == "shield":
            if s_ > 0:
                x = cx + a * _m.copysign(abs(c_) ** .7, c_) * (1 - .6 * s_ ** 2.2)
                y = cy + b * s_ ** .8
            else:
                x = cx + a * _m.copysign(abs(c_) ** .35, c_)
                y = cy + b * .9 * _m.copysign(abs(s_) ** .35, s_)
        elif kind == "arch":
            if s_ > 0:
                x = cx + a * _m.copysign(abs(c_) ** .3, c_)
                y = cy + b * _m.copysign(abs(s_) ** .3, s_)
        elif kind == "quatre":
            rr = 1 + .07 * _m.cos(4 * t)
            x, y = cx + a * c_ * rr, cy + b * s_ * rr
        elif kind == "ogee":
            # pointed top (Thai temple window)
            if s_ < 0:
                y = cy + b * s_ * (1 + .25 * (1 - abs(c_)) ** 3)
                x = cx + a * c_ * (1 - .2 * abs(s_) ** 3)
        pts.append((x, y))
    return pts


def medallion(cx, cy, w, h, kind="oval", beads=True):
    """an inlaid portrait medallion: a bright wire, a bead ring on black, a second wire, then the
    field. Returns (svg_frame, field_pts, outer_pts)."""
    a, b = w / 2, h / 2
    rb = max(1.5, min(2.5, min(w, h) * .018))
    ring = 2 * rb + 2.5
    outer = shape_pts(cx, cy, a, b, kind)
    o = [f'<path d="{_dd(outer, True, .1)}" fill="#000" stroke="none"/>']
    w1 = shape_pts(cx, cy, a - 1, b - 1, kind)
    o.append(f'<path d="{_dd(w1 + [w1[0]], tol=.1)}" fill="none" stroke="#fff" stroke-width="1.5"/>')
    w0 = shape_pts(cx, cy, a + .5, b + .5, kind)
    o.append(f'<path d="{_dd(w0 + [w0[0]], tol=.1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    if beads:
        bl = shape_pts(cx, cy, a - 2.5 - rb, b - 2.5 - rb, kind, 240)
        o.append(bead_line(bl, rb, True))
    w2 = shape_pts(cx, cy, a - ring - 1.5, b - ring - 1.5, kind)
    o.append(f'<path d="{_dd(w2 + [w2[0]], tol=.1)}" fill="none" stroke="#fff" stroke-width="1"/>')
    field = shape_pts(cx, cy, a - ring - 2.5, b - ring - 2.5, kind)
    return "".join(o), field, outer


def clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ---------------------------------------------------------------------------------------------
# small figural terminals and eggs that can be carved into the scroll (drawn into a Canvas)
# ---------------------------------------------------------------------------------------------

def fig_drumsticks(cv, cx, cy, s, ang=0.):
    for sd in (-1, 1):
        a = ang + sd * .62 - _PI / 2
        x0, y0 = cx - _m.cos(a) * s * .5, cy - _m.sin(a) * s * .5
        P = [(x0 + _m.cos(a) * s * t, y0 + _m.sin(a) * s * t) for t in (0, .5, 1)]
        R = _Rib(P, [s * .05, s * .045, s * .02], [s * .05, s * .045, s * .02])
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.5, 0, 1))
        tx, ty = P[-1]
        cv.obj([_ell(tx, ty, s * .05, s * .05, 10)[:-1]], .5)


def fig_heron(cv, x, y, s, flip=False):
    """a standing great blue heron, s tall"""
    f = -1 if flip else 1

    def T(u, v):
        return (x + f * u * s, y - v * s)
    body = [T(-.18, .5), T(.05, .62), T(.2, .58), T(.26, .5), T(.12, .36), T(-.1, .34), T(-.3, .38)]
    neck = [T(.12, .58), T(.2, .74), T(.12, .84), T(.17, .95), T(.25, .97), T(.27, .92), T(.18, .86), T(.25, .76), T(.18, .58)]
    bill = [T(.25, .97), T(.46, .93), T(.26, .92)]
    cv.obj([body], .5)
    cv.hair(_C.hatch_poly(body, 30 * f, 1.5))
    cv.obj([neck], .5)
    cv.hair([T(.16, .62), T(.21, .74)])
    cv.obj([bill], .5)
    cv.line([T(.0, .35), T(.02, .0)])
    cv.line([T(.06, .35), T(.1, .0)])
    cv.hair([T(.22, .96), T(.05, .99)])


def fig_mthood(cv, cx, by, w, hgt):
    """Mt Hood: the asymmetric cone with its notched summit, glaciers in the gullies, the shadow
    flank cut in 45-degree bulino, foothills of fir at the foot"""
    sil = [(-.5, 0), (-.36, .18), (-.22, .46), (-.12, .74), (-.05, .92), (-.01, 1.), (.03, .96), (.06, .99),
           (.12, .8), (.2, .58), (.3, .36), (.42, .14), (.5, 0)]
    P = [(cx + u * w, by - v * hgt) for u, v in sil]
    cv.obj([P], .5)
    # shadow flank (right of the ridge): diagonal cuts
    sh = [(cx + .03 * w, by - .96 * hgt), (cx + .06 * w, by - .99 * hgt), (cx + .12 * w, by - .8 * hgt),
          (cx + .2 * w, by - .58 * hgt), (cx + .3 * w, by - .36 * hgt), (cx + .42 * w, by - .14 * hgt),
          (cx + .5 * w, by), (cx + .1 * w, by), (cx + .04 * w, by - .5 * hgt)]
    cv.hair(_C.hatch_poly(sh, 45, 1.5))
    # glaciers: white tongues reaching down the gullies, edged with rock
    for g0, g1, L in ((-.08, -.02, .45), (.0, .07, .5), (-.18, -.12, .3), (.12, .18, .28)):
        tongue = [(cx + g0 * w, by - (.98 - .2) * hgt), (cx + g1 * w, by - .9 * hgt),
                  (cx + (g1 + g0) / 2 * w * 1.6, by - (.9 - L) * hgt)]
        cv.obj([tongue], .5)
    # foothills of fir across the base
    n = max(5, int(w / 5))
    for i in range(n):
        tx = cx - w * .5 + w * (i + .5) / n
        th = hgt * (.12 + .06 * ((i * 7) % 3))
        cv.obj([[(tx - th * .3, by), (tx, by - th), (tx + th * .3, by)]], .5)
        cv.hair([(tx, by - th), (tx + th * .22, by - th * .2)])


def fig_dog(cv, cx, cy, s, flip=False):
    """Parker's dog, curled asleep (s across)"""
    f = -1 if flip else 1
    body = _ell(cx, cy, s * .5, s * .3, 24)[:-1]
    cv.obj([body], .5)
    for k in range(4):
        rr = s * (.42 - .08 * k)
        cv.hair([(cx + f * rr * _m.cos(t), cy + s * .24 * (rr / (s * .42)) * _m.sin(t)) for t in [_PI * (.1 + .8 * i / 10) for i in range(11)]])
    hx, hy = cx + f * s * .34, cy - s * .12
    head = _ell(hx, hy, s * .18, s * .14, 14)[:-1]
    cv.obj([head], .5)
    cv.obj([[(hx - f * s * .05, hy - s * .1), (hx + f * s * .02, hy - s * .26), (hx + f * s * .1, hy - s * .08)]], .5)
    cv.line(_ell(hx + f * s * .14, hy + s * .02, .5, .5, 6))
    cv.hair([(hx - f * s * .02, hy + s * .02), (hx + f * s * .06, hy + s * .03)])


def fig_p(cv, cx, cy, s):
    """a P monogram cut as a ribbon"""
    st = [(cx - s * .2, cy + s * .5), (cx - s * .2, cy - s * .5)]
    bowl = [(cx - s * .2 + s * .36 * _m.sin(t) * 1.1, cy - s * .22 - s * .28 * _m.cos(t)) for t in [_PI * i / 12 for i in range(13)]]
    for pl in (st, bowl):
        R = _Rib(pl, [s * .08] * len(pl), [s * .08] * len(pl))
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.4, 0, 1))


def fig_sun(cv, cx, cy, r, rays=16):
    """a sun: a modelled disc with a face-less boss and alternating straight and waved rays"""
    for k in range(rays):
        t = _TAU * k / rays
        L = r * (1.75 if k % 2 == 0 else 1.45)
        wv = k % 2
        pts = []
        for i in range(9):
            u = i / 8
            rr = r * 1.02 + (L - r) * u
            off = (.08 * _m.sin(u * _PI * 2) if wv else 0.)
            pts.append((cx + _m.cos(t + off) * rr, cy + _m.sin(t + off) * rr))
        R = _Rib(pts, [r * .16 * (1 - i / 8) + .4 for i in range(9)], [r * .16 * (1 - i / 8) + .4 for i in range(9)])
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.45, 0, .85, minw=.9))
    disc = _ell(cx, cy, r, r, 36)[:-1]
    cv.obj([disc], 1.)
    for q in (.78, .55):
        cv.hair(_ell(cx, cy, r * q, r * q, 28))
    cv.hair(_C.hatch_poly(_ell(cx + r * .25, cy + r * .25, r * .62, r * .62, 20)[:-1], 45, 1.5))


def arms_placeholder(cx, cy, s):
    """Parker's arms are pending: a beaded cartouche with crossed drumsticks over a sun. s tall."""
    w = s * .86
    fr, field, outer = medallion(cx, cy, w, s, "shield", True)
    cv = Canvas()
    fig_sun(cv, cx, cy - s * .04, s * .17)
    fig_drumsticks(cv, cx, cy + s * .02, s * .62)
    body = fr + f'<path d="{_dd(field, True, .1)}" fill="#fff" stroke="none"/>'
    gr = Canvas()
    gr.obj([field], 0)
    gr.hair(_C.hatch_poly(field, 0, 1.5, .25))
    return body + clip(f"gmA{int(cx)}{int(cy)}", _dd(field, True, .1), gr.svg() + cv.svg())


# ---------------------------------------------------------------------------------------------
# shaped panels and the gold line
# ---------------------------------------------------------------------------------------------

def arms_somaster(cx, cy, s, seed=0):
    """Parker's arms (Somaster) from the shared solar/arms.py, s tall; the placeholder if it is missing."""
    try:
        import arms as _AR
    except Exception:
        return arms_placeholder(cx, cy, s)
    w = s * 120. / 140.
    return (f'<svg x="{_nn(cx - w / 2)}" y="{_nn(cy - s / 2)}" width="{_nn(w)}" height="{_nn(s)}" overflow="visible">'
            + _slim(_AR.arms(w, s, seed)) + "</svg>")


def panel_pts(kind, x0, y0, x1, y1, d=0., c=None):
    """outline of a shaped panel inset by d: 'rect', 'cut' (chamfered corners c), 'arch' (round
    arched top), 'lunette' (arched top and bottom)."""
    x0, y0, x1, y1 = x0 + d, y0 + d, x1 - d, y1 - d
    if kind == "cut":
        c = max(1., (c or 12.) - d * .41)
        return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
    if kind in ("arch", "lunette"):
        w = x1 - x0
        ah = max(4., (c or w * .18) - d * .5)
        pts = []
        n = 48
        for i in range(n + 1):
            t = _PI + _PI * i / n
            pts.append(((x0 + x1) / 2 + w / 2 * _m.cos(t), y0 + ah + ah * _m.sin(t)))
        if kind == "lunette":
            for i in range(n + 1):
                t = _PI * i / n
                pts.append(((x0 + x1) / 2 + w / 2 * _m.cos(t), y1 - ah + ah * _m.sin(t)))
        else:
            pts += [(x1, y1), (x0, y1)]
        return pts
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def gold_line(kind, x0, y0, x1, y1, c=None, beads=True, r=1.4):
    """a fine triple 'gold' border along a shaped panel: a bright 1.5 px wire between 0.5 px cuts,
    a 0.5 px rule, and a bead row inside. Returns (svg, inner_pts at the beads' inner edge)."""
    P0 = panel_pts(kind, x0, y0, x1, y1, 0., c)
    P1 = panel_pts(kind, x0, y0, x1, y1, 3., c)
    o = [f'<path d="{_dd(P0, True, 0)}{_dd(P1[::-1], True, 0)}" fill="#fff" stroke="none"/>',
         f'<path d="{_dd(P0 + [P0[0]], tol=0)}{_dd(P1 + [P1[0]], tol=0)}" fill="none" stroke="#000" stroke-width=".5"/>',
         f'<path d="{_dd(panel_pts(kind, x0, y0, x1, y1, 1.5, c) + [panel_pts(kind, x0, y0, x1, y1, 1.5, c)[0]], tol=0)}" '
         f'fill="none" stroke="#000" stroke-width=".5" stroke-dasharray="2 1.5"/>']
    d = 3.
    if beads:
        BP = panel_pts(kind, x0, y0, x1, y1, 3. + r + 1., c)
        o.append(bead_line(BP, r, True))
        d = 3. + 2 * r + 2.
    P2 = panel_pts(kind, x0, y0, x1, y1, d, c)
    o.append(f'<path d="{_dd(P2 + [P2[0]], tol=0)}" fill="none" stroke="#fff" stroke-width="1"/>')
    return "".join(o), panel_pts(kind, x0, y0, x1, y1, d + 1., c)


def corner_spray(cv, x, y, ang, s, rng, thai=False):
    """foliage filling a corner: a fan of leaves springing from (x, y) toward ang"""
    for k, off in enumerate((-.55, .55, 0.)):
        ln = s * (.8 if off else 1.)
        side = 1 if off <= 0 else -1
        lf = Leaf(x, y, ang + off, ln, ln * (.36 if thai else .48), side * .3, max(2, int(ln / 6)), thai, side, 1.6)
        Scroll._paint_leaf(None, cv, lf, side)
    cv.obj([_ell(x, y, s * .14, s * .14, 14)[:-1]], 1.)
    cv.line(_ell(x, y, s * .06, s * .06, 8))


# ---------------------------------------------------------------------------------------------
# the composer
# ---------------------------------------------------------------------------------------------

def _extras(fn, occ, g):
    out = []
    if fn:
        for poly, svg in fn(g):
            if poly:
                occ.poly(poly)
            out.append(svg)
    return out


def _slim(sv):
    """one decimal, no 0. or .0 padding inside path data"""
    def dd(m):
        d = _re.sub(r"(\d\.\d)\d+", r"\1", m.group(1))
        d = _re.sub(r"(\d)\.0(?!\d)", r"\1", d)
        d = _re.sub(r"(?<![\d.])0\.(\d)", r".\1", d)
        return ' d="' + d + '"'
    return _re.sub(r' d="([^"]*)"', dd, sv)


def _rel_h(m):
    """d of absolute M x,y h l runs -> one relative path (same marks, fewer bytes)"""
    o, px, py = [], None, None
    for x, y, l in _re.findall(r"M([-\d.]+),([-\d.]+)h([-\d.]+)", m.group(1)):
        x, y, l = round(float(x), 1), round(float(y), 1), round(float(l), 1)
        if px is None:
            o.append(f"M{_nn(x)} {_nn(y)}h{_nn(l)}")
        else:
            o.append(f"m{_nn(round(x - px, 1))} {_nn(round(y - py, 1))}h{_nn(l)}")
        px, py = round(x + l, 1), y
    return 'd="' + "".join(o) + '"'


def compose(w, h, scene, seed=0, medal="oval", thai=False, egg=None, arms=False, k=None,
            panel=None, ribbon=True, banner=None, extras=None):
    """A complete king-tier plate filling w x h edge to edge.
    scene(x, y, sw, sh, mode) -> svg drawn in the box (it is clipped to the medallion field);
    mode is 'band', 'medium' or 'tall'. egg(cv, x, y, s) carves Parker's Easter egg into the
    scroll at a spot kept clear for it. arms: the dedication cartouche under a tall scene.
    banner(centre_pts, ribbon_h) -> svg letters the tall plate's ribbon. extras(g) -> [(poly, svg)]
    places figures beside the medallion (g: dict of the layout's geometry); the scroll grows round
    each poly and the svg is laid over it."""
    rng = _r.Random(seed)
    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    if k is None:
        k = 1.05 if mode == "band" else (1.2 if mode == "medium" else 1.35)
    o = [gm_defs(), matte(rect_d(0, 0, w, h))]
    occ = Occ(w, h)
    top = []          # svg laid over the scroll
    cvx = Canvas()    # extra carved figures (eggs, corner sprays) painted over the scroll
    seeds = []
    if mode == "band":
        b, inner = gold_line("rect", .5, .5, w - .5, h - .5, beads=h >= 70, r=1.2)
        occ.outside(inner)
        x0, y0 = inner[0]
        x1, y1 = inner[2]
        H = y1 - y0
        mw = min(H * 2.3, 210.)
        mh = H + 6
        cx, cy = w / 2, h / 2
        fr, field, outer = medallion(cx, cy, mw, mh, medal if medal != "arch" else "cushion")
        occ.poly(shape_pts(cx, cy, mw / 2 + 2.5, mh / 2 + 2.5, medal if medal != "arch" else "cushion"))
        Wr = (x1 - x0 - mw) / 2
        for sd in (-1, 1):
            Rm = H * .36
            lead = Wr * .35
            seeds.append((cx + sd * (mw / 2 - 6), y1 - max(3., H * .18), (0 if sd > 0 else _PI) - sd * .25, -sd,
                          Rm * 3.2 + lead, Rm, max(1.6, H * .045), lead))
            seeds.append((cx + sd * (mw / 2 - 6), y0 + max(3., H * .18), (0 if sd > 0 else _PI) + sd * .25, sd,
                          Rm * 2.8 + lead * 1.6, Rm * .85, max(1.4, H * .04), lead * 1.6))
        top += _extras(extras, occ, dict(mode=mode, cx=cx, cy=cy, mw=mw, mh=mh, x0=x0, y0=y0, x1=x1, y1=y1, w=w, h=h))
        if egg:
            ex = x0 + Wr * .18 if rng.random() < .5 else x1 - Wr * .18
            es = min(H * .62, 30.)
            occ.dot(ex, cy, es * .62)
            egg(cvx, ex, cy, es)
        S = Scroll(w, h, occ, seed, k, thai)
        S.grow(seeds).dress(x0, y0, x1, y1, 8., H * .42, 60)
        border = b
    else:
        kind = panel or ("cut" if mode == "medium" else "arch")
        cc = min(h * .14, 26.) if kind == "cut" else min(w * .2, h * .22)
        if mode == "tall":
            pred = min(max(h * .2, 64.), 112.)
            mainb = (.5, .5, w - .5, h - pred - 1)
        else:
            pred = 0.
            mainb = (.5, .5, w - .5, h - .5)
        b, inner = gold_line(kind, *mainb, c=cc)
        occ.outside(inner)
        xs = [p[0] for p in inner]
        ys = [p[1] for p in inner]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        H = y1 - y0
        # the spandrels / cut corners outside the shaped panel: foliage springing from the corners
        csz = cc * .62
        span_seeds = []
        if kind == "cut":
            for (qx, qy, a) in ((2, 2, .78), (w - 2, 2, _PI - .78), (2, mainb[3] - 2, -.78), (w - 2, mainb[3] - 2, _PI + .78)):
                corner_spray(cvx, qx, qy, a, csz, rng, thai)
        else:
            for sd in (-1, 1):
                qx = 4 if sd < 0 else w - 4
                span_seeds.append((qx, 4, (0 if sd < 0 else _PI) + (-sd) * -.3, sd, cc * 1.4, cc * .36, 1.8, cc * .3))
                span_seeds.append((qx, cc * .9, -_PI / 2, -sd, cc * 1.1, cc * .3, 1.6, 0.))
        cx = w / 2
        if mode == "medium":
            mh = H - 4
            mw = min(w * .4, mh * 1.32)
            cy = (y0 + y1) / 2
        else:
            mw = min(w * .52, (H) * .74)
            mh = min(H * .74, mw * 1.3)
            cy = y0 + H * .06 + mh / 2 + (cc * .35 if kind == "arch" else 0)
            mh = min(mh, (y1 - cy) * 2 - 30)
        mk = medal
        fr, field, outer = medallion(cx, cy, mw, mh, mk)
        occ.poly(shape_pts(cx, cy, mw / 2 + 2.5, mh / 2 + 2.5, mk))
        rib = ""
        rw, ry = mw, cy + mh / 2
        if mode == "tall" and ribbon:
            rw, rh = mw * 1.25, 13.
            ry = cy + mh / 2 - 4
            rib, centre = _C.ribbon_banner(cx, ry, rw, rh, .03, seed)
            if banner:
                rib += banner(centre, rh)
            occ.rect(cx - rw / 2 - 4, ry - rh / 2 - 4, cx + rw / 2 + 4, ry + rh * 1.5)
        Wr = (x1 - x0 - mw) / 2
        for sd in (-1, 1):
            Rm = min(Wr * .36, H * .36)
            lead = Wr * .4
            if mode == "tall":
                # a long vine rising up the side from the ribbon's end, curling over at the top
                Rv = min(Wr * .4, H * .2)
                lv = H * .5
                if not extras:
                    seeds.append((cx + sd * (mw / 2 + 10), ry - 6, -_PI / 2 + sd * .12, sd, Rv * 3.2 + lv, Rv,
                                  max(2.4, Rv * .085), lv, 0.))
                # from the crown of the medallion outward along the arch, curling down
                Ra = min(Wr * .34, H * .16)
                seeds.append((cx + sd * 8, cy - mh / 2 - 6, (0 if sd > 0 else _PI) - sd * .2, sd,
                              Ra * 3.2 + Wr * .5, Ra, max(2., Ra * .085), Wr * .5))
                # from the ribbon's foot downward and out
                Rb = min(Wr * .3, (y1 - ry) * .45)
                seeds.append((cx + sd * (rw * .3), y1 - 6, (0 if sd > 0 else _PI) - sd * .15, -sd,
                              Rb * 3.2 + Wr * .4, Rb, max(1.8, Rb * .08), Wr * .4))
            else:
                seeds.append((cx + sd * (mw * .32), y1 - 10,
                              (0 if sd > 0 else _PI) - sd * .45, -sd, Rm * 3.3 + lead, Rm, max(2.2, Rm * .08), lead))
                Rm2 = min(Wr * .27, H * .26)
                seeds.append((cx + sd * (mw * .3), y0 + 9, (0 if sd > 0 else _PI) + sd * .35, sd,
                              Rm2 * 3.3 + lead * .7, Rm2, max(1.8, Rm2 * .08), lead * .7))
        top += _extras(extras, occ, dict(mode=mode, cx=cx, cy=cy, mw=mw, mh=mh, x0=x0, y0=y0, x1=x1, y1=y1, w=w, h=h,
                                         ry=ry, rw=rw))
        if egg:
            ex = x0 + Wr * .5 if rng.random() < .5 else x1 - Wr * .5
            ey = y1 - min(30., H * .18) if mode == "tall" else cy
            es = min(H * .3, 40., Wr * .5)
            occ.dot(ex, ey, es * .62)
            egg(cvx, ex, ey, es)
        if span_seeds:
            occS = Occ(w, h)
            occS.poly(panel_pts(kind, *mainb, 0., cc))
            occS.rect(0, mainb[3], w, h)
            SS = Scroll(w, h, occS, seed + 3, k * .8, thai)
            SS.grow(span_seeds).dress(0, 0, w, cc * 1.6, 8., cc * .5, 30)
            SS.paint(cvx)
        S = Scroll(w, h, occ, seed, k, thai)
        S.grow(seeds).dress(x0, y0, x1, y1, 9., min(H * .3, 46.), 105)
        border = b
        if mode == "tall":
            top.append(rib)
            # the predella: a second gold-lined panel, scroll flowing out from a central cartouche
            py0 = h - pred
            pb, pin = gold_line("cut", .5, py0, w - .5, h - .5, c=min(pred * .2, 18.))
            occ2 = Occ(w, h)
            occ2.outside(pin)
            pys = [p[1] for p in pin]
            qy0, qy1 = min(pys), max(pys)
            ph = qy1 - qy0
            cs = ph * .92
            if arms:
                cs = ph * 1.02
                acs = arms_somaster(cx, (qy0 + qy1) / 2, cs, seed % 5)
                occ2.poly(shape_pts(cx, (qy0 + qy1) / 2, cs * .42 + 2, cs / 2 + 1, "cushion"))
            else:
                ew, eh = min(cs * 1.7, 120.), cs
                efr, efield, _ = medallion(cx, (qy0 + qy1) / 2, ew, eh, "cushion")
                acs = efr
                occ2.poly(shape_pts(cx, (qy0 + qy1) / 2, ew / 2 + 2.5, eh / 2 + 2.5, "cushion"))
                pred_field = (efield, ew, eh)
            sd2 = []
            for sd in (-1, 1):
                Rm = ph * .36
                ld = (w / 2) * .3
                sd2.append((cx + sd * (cs * .45 if arms else min(cs * 1.7, 120.) * .45), qy1 - ph * .2,
                            (0 if sd > 0 else _PI) - sd * .3, -sd, Rm * 3.2 + ld, Rm, max(1.8, ph * .04), ld))
                sd2.append((cx + sd * (cs * .4 if arms else min(cs * 1.7, 120.) * .4), qy0 + ph * .2,
                            (0 if sd > 0 else _PI) + sd * .3, sd, Rm * 2.8 + ld * 1.5, Rm * .8, max(1.6, ph * .035), ld * 1.5))
            S2 = Scroll(w, h, occ2, seed + 7, k * .85, thai)
            S2.grow(sd2).dress(4, qy0, w - 4, qy1, 8., ph * .45, 50)
            cv2 = Canvas()
            S2.paint(cv2)
            border += pb
            top.append(cv2.svg())
            top.append(acs)
            if not arms:
                ef, ew, eh = pred_field
                top.append(f'<path d="{_dd(ef, True, .1)}" fill="#fff" stroke="none"/>')
                top.append(clip(f"gmE{seed % 997}", _dd(ef, True, .1), scene(cx - ew / 2, (qy0 + qy1) / 2 - eh / 2, ew, eh, "egg")))
    cv = Canvas()
    S.paint(cv)
    o.append(cv.svg())
    o.append(cvx.svg())
    o.append(border)
    o.append(fr)
    fd = _dd(field, True, .1)
    fx = [p[0] for p in field]
    fy = [p[1] for p in field]
    o.append(f'<path d="{fd}" fill="#fff" stroke="none"/>')
    sv = scene(min(fx), min(fy), max(fx) - min(fx), max(fy) - min(fy), mode)
    sv = _slim(_re.sub(r'd="((?:M[-\d.]+,[-\d.]+h[-\d.]+)+)"', _rel_h, sv))
    o.append(clip(f"gmF{seed % 997}{int(h)}", fd, sv))
    o.extend(top)
    return _C.svg_doc(w, h, "".join(o))


# ==== GM ENGINE END ====


PI, TAU = math.pi, 2 * math.pi
CR = ' shape-rendering="crispEdges"'

_n, _d = C._n, C._d
PI, TAU = math.pi, 2 * math.pi
CR = ' shape-rendering="crispEdges"'


# ------------------------------------------------------------------------------------------------
# stroke lettering (drawn as paths, never <text>)
# ------------------------------------------------------------------------------------------------

def _oval(cx, cy, rx, ry, a0=0., a1=TAU, n=14):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


_G = {
    "A": (4, [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]]),
    "B": (4, [[(0, 0), (0, 6), (3, 6), (4, 5.1), (4, 3.9), (3, 3), (0, 3)], [(0, 0), (2.8, 0), (3.7, .8), (3.7, 2.2), (2.8, 3)]]),
    "C": (4, [[(4, 1), (3, 0), (1, 0), (0, 1.2), (0, 4.8), (1, 6), (3, 6), (4, 5)]]),
    "D": (4, [[(0, 0), (0, 6), (2.4, 6), (4, 4.4), (4, 1.6), (2.4, 0), (0, 0)]]),
    "E": (3.6, [[(3.6, 0), (0, 0), (0, 6), (3.6, 6)], [(0, 3), (2.8, 3)]]),
    "G": (4, [[(4, 1), (3, 0), (1, 0), (0, 1.2), (0, 4.8), (1, 6), (3, 6), (4, 5), (4, 3.4), (2.3, 3.4)]]),
    "H": (4, [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]]),
    "I": (2, [[(1, 0), (1, 6)], [(0, 0), (2, 0)], [(0, 6), (2, 6)]]),
    "L": (3.5, [[(0, 0), (0, 6), (3.5, 6)]]),
    "M": (5, [[(0, 6), (0, 0), (2.5, 4), (5, 0), (5, 6)]]),
    "N": (4, [[(0, 6), (0, 0), (4, 6), (4, 0)]]),
    "O": (4.4, [_oval(2.2, 3, 2.2, 3, n=20)]),
    "P": (4, [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]]),
    "R": (4, [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]]),
    "S": (4, [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]]),
    "T": (4, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
    "U": (4, [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]]),
    "W": (5.4, [[(0, 0), (1.3, 6), (2.7, 2), (4.1, 6), (5.4, 0)]]),
    "Y": (4, [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]]),
    "1": (3, [[(.6, 1.2), (1.8, 0), (1.8, 6)], [(.6, 6), (3, 6)]]),
    "8": (4, [_oval(2, 1.5, 1.6, 1.5, n=16), _oval(2, 4.4, 1.9, 1.6, n=16)]),
    "9": (4, [_oval(2, 2, 2, 2, n=18), [(4, 2), (4, 4.4), (3, 6), (1, 6), (0, 5)]]),
    "*": (2.4, [[(1.2, 2.2), (2.2, 3), (1.2, 3.8), (.2, 3), (1.2, 2.2)]]),
    " ": (2.6, []),
}


def _word_w(s, track=1.6):
    return sum(_G[c][0] + track for c in s) - track


def letter_line(s, cx, cy, size, track=1.6):
    """Polylines of s centred at (cx, cy), cap height `size` px."""
    k = size / 6.
    x = cx - _word_w(s, track) * k / 2
    out = []
    for c in s:
        gw, strokes = _G[c]
        for st in strokes:
            out.append([(x + px * k, cy - size / 2 + py * k) for px, py in st])
        x += (gw + track) * k
    return out


def letter_arc(s, centre, size, track=1.6):
    """Letters set along a polyline (the ribbon's face centre), centred on it."""
    L = [0.]
    for (ax, ay), (bx, by) in zip(centre, centre[1:]):
        L.append(L[-1] + math.hypot(bx - ax, by - ay))
    k = size / 6.
    tot = _word_w(s, track) * k
    s0 = L[-1] / 2 - tot / 2

    def at(u):
        u = max(0, min(L[-1] - 1e-6, u))
        for i in range(len(L) - 1):
            if L[i + 1] >= u:
                t = (u - L[i]) / max(1e-6, L[i + 1] - L[i])
                (ax, ay), (bx, by) = centre[i], centre[i + 1]
                return ax + (bx - ax) * t, ay + (by - ay) * t, math.atan2(by - ay, bx - ax)
        return centre[-1][0], centre[-1][1], 0.

    out = []
    u = s0
    for c in s:
        gw, strokes = _G[c]
        mx, my, a = at(u + gw * k / 2)
        ca, sa = math.cos(a), math.sin(a)
        for st in strokes:
            pts = []
            for px, py in st:
                lx, ly = (px - gw / 2) * k, (py - 3) * k
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            out.append(pts)
        u += (gw + track) * k
    return out


def _pl_d(pls):
    return "".join(_d(p, tol=0) for p in pls if len(p) > 1)



_G.update({
    "V": (4, [[(0, 0), (2, 6), (4, 0)]]),
    "F": (3.6, [[(3.6, 0), (0, 0), (0, 6)], [(0, 3), (2.8, 3)]]),
    "K": (4, [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.4, 2.6), (4, 6)]]),
})


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _blk(polys):
    return "".join(_d(p, True, 0) for p in polys if len(p) > 2)


def _stick(x0, y0, x1, y1, w0, w1):
    """A tapered stick (drumstick, stand leg) as a polygon from width w0 to w1, with a bead tip."""
    a = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(a), math.cos(a)
    return [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
            (x1 + math.cos(a) * w1 * 1.2, y1 + math.sin(a) * w1 * 1.2),
            (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]


def _rings(cx, cy, rx, ry, r0, r1, pitch, a0=0., a1=TAU, n=40):
    out = []
    r = r1
    while r > r0:
        k = r / r1
        out.append(_oval(cx, cy, rx * k, ry * k, a0, a1, n))
        r -= pitch
    return out


# ------------------------------------------------------------------------------------------------
# the subject: a Portland club stage, show night
# ------------------------------------------------------------------------------------------------

def stage(fx, fy, fw, fh, seed=0, egg=True):
    rng = random.Random(seed)
    o = []
    S = min(fh / 100., fw / 140.)                   # one unit
    cx = fx + fw / 2
    yF = fy + fh * .70                              # back edge of the stage floor
    yL = fy + fh * .82                              # stage lip
    yV = fy + fh * .11                              # valance bottom

    # backdrop: a heavy black drape behind the band, in deep vertical folds (bulino rules that
    # crowd together in the troughs and part on the crests)
    lines = []
    x = fx - 2.
    while x < fx + fw + 2:
        lines.append(f"M{_n(x)},{_n(fy - 2)}V{_n(yF + 1)}")
        ph = math.sin((x - fx) / (fw / 9.) * PI)
        x += 1.5 if ph < .35 else 3.
    o.append(f'<path d="{"".join(lines)}" stroke="#000" stroke-width=".5"{CR}/>')
    dk = []
    for k in range(10):
        xk = fx + fw / 9. * (k - .5) * 1. + fw / 18.
        dk.append(_rect(xk - .6 * S, fy - 2, xk + .6 * S, yF + 1))
    o.append(f'<path d="{_blk(dk)}" fill="#000"/>')

    cv = C.Canvas()
    black = []

    # light beams from the spot cans, ruled light, cut out of the backdrop
    cans = [(-.36, rng.random() < .8), (-.15, True), (.15, True), (.36, rng.random() < .8)]
    for u, lit in cans:
        if not lit:
            continue
        sx, sy = cx + u * fw, yV + 3 * S
        tx = cx + u * fw * .25 + rng.uniform(-8, 8) * S
        beam = [(sx - 2.5 * S, sy), (sx + 2.5 * S, sy), (tx + 15 * S, yF + 6 * S), (tx - 15 * S, yF + 6 * S)]
        cv.obj([beam], 0)
        cv.hair(C.hatch_poly(beam, 0, 3, .25))

    # stage floor: planks converging on the band, ruled for depth
    floor = [(fx - 2, yF), (fx + fw + 2, yF), (fx + fw + 2, yL), (fx - 2, yL)]
    cv.obj([floor], 1.)
    vx, vy = cx, yF - (yL - yF) * 2.2
    planks = []
    for i in range(-14, 15):
        bx = cx + i * fw / 18
        t0 = (yF - vy) / (yL - vy)
        planks.append([(vx + (bx - vx) * t0, yF), (bx, yL)])
    cv.hair(planks)
    cv.hair(C.hatch_poly(floor, 0, 2, .25))
    # stage lip: a black fascia with a white nosing
    black.append(_rect(fx - 2, yL, fx + fw + 2, yL + 2.6 * S))

    # amp stacks either side of the kit
    def amp(ax, w_, h_):
        cab = _rect(ax - w_ / 2, yF + 2 * S - h_, ax + w_ / 2, yF + 2 * S)
        cv.obj([cab], 1.)
        g = _rect(ax - w_ / 2 + 2 * S, yF + 2 * S - h_ + 2 * S, ax + w_ / 2 - 2 * S, yF)
        cv.obj([g], .5)
        cv.hair(C.hatch_poly(g, 45, 2))
        cv.hair(C.hatch_poly(g, -45, 2))
        cv.line([[(ax - w_ / 2, yF + 2 * S - h_ / 2), (ax + w_ / 2, yF + 2 * S - h_ / 2)]])
        hy = yF + 2 * S - h_
        head = _rect(ax - w_ / 2, hy - h_ * .3, ax + w_ / 2, hy)
        cv.obj([head], 1.)
        cv.hair(C.hatch_poly(head, 0, 1.5, .25))
        panel = _rect(ax - w_ * .42, hy - h_ * .2, ax + w_ * .42, hy - h_ * .08)
        black.append(panel)
        for k in range(6):
            kx = ax - w_ * .36 + k * w_ * .144
            black.append(_oval(kx, hy - h_ * .26, max(.8, 1.1 * S), max(.8, 1.1 * S), n=8))
    aw, ah = fw * .16, fh * .26
    amp(cx - fw * .31, aw, ah)
    amp(cx + fw * .31, aw, ah)

    # an electric guitar on its stand, leaning, in front of the left stack
    def guitar(gx, gy, sc, lean):
        ca, sa = math.cos(lean), math.sin(lean)
        T = lambda pts: [(gx + x_ * ca - y_ * sa, gy + x_ * sa + y_ * ca) for x_, y_ in pts]
        body = []
        bouts = ((0., .38 * sc, 1.0 * sc, .86 * sc), (-.06 * sc, -.5 * sc, .78 * sc, .62 * sc))

        def inside(px, py):
            return any(((px - ex) / rx) ** 2 + ((py - ey) / ry) ** 2 <= 1 for ex, ey, rx, ry in bouts)
        for i in range(48):                     # ray-cast the union of two bouts: a waisted body
            t = TAU * i / 48
            r = 2.2 * sc
            while r > .05 * sc and not inside(r * math.cos(t), r * math.sin(t)):
                r -= .03 * sc
            body.append((r * math.cos(t), r * math.sin(t)))
        neck = T(_rect(-sc * .1, -sc * 3.5, sc * .1, -sc * .8))
        hs = T([(-sc * .13, -sc * 3.5), (sc * .13, -sc * 3.5), (sc * .2, -sc * 4.3), (-sc * .08, -sc * 4.2)])
        stand = [[(gx - sc * .9, yF + 2 * S), (gx, gy + sc * .6), (gx + sc * .9, yF + 2 * S)]]
        cv.obj([], 0)
        cv.line(stand)
        cv.obj([T(body)], 1.)
        bp = T(body)
        cv.hair([l for l in C.hatch_poly(bp, 45 + math.degrees(lean), 1.5)])
        cv.hair(C.hatch_poly(bp, -45 + math.degrees(lean), 3))
        guard = T([(x_ * .55 + sc * .12, y_ * .55 + sc * .12) for x_, y_ in body])
        cv.obj([guard], .5)
        cv.hair([q for q in [T([(-sc * .3, sc * .55), (sc * .3, sc * .55)])]])
        cv.obj([neck], .5)
        cv.hair(C.hatch_poly(neck, 90 + math.degrees(lean), 1.5))
        frets = [T([(-sc * .1, -sc * 3.5 + k * sc * .22), (sc * .1, -sc * 3.5 + k * sc * .22)]) for k in range(12)]
        cv.hair(frets)
        cv.obj([hs], .5)
        cv.hair(C.hatch_poly(hs, 0, 1.5))
        for py_ in (-sc * .35, sc * .05):
            black.append(T(_rect(-sc * .26, py_, sc * .26, py_ + sc * .14)))
        black.append(T(_rect(-sc * .3, sc * .5, sc * .3, sc * .6)))
        for k in range(3):
            black.append(T(_oval(sc * .5, sc * .45 + k * sc * .22, sc * .07, sc * .07, n=6)))
    guitar(cx - fw * .21, yF - fh * .06, fh * .07, -.22)

    # --- drum kit, centred behind the mic
    R = fh * .14                                    # kick drum radius
    ky = yF + 3 * S - R
    kx = cx + 3 * S
    # hi-hat (left) and ride cymbal (right) on their stands
    hhx, hhy = kx - R * 1.75, ky - R * 1.15
    rdx, rdy = kx + R * 1.9, ky - R * 1.35
    cv.obj([], 0)
    cv.line([[(hhx, hhy), (hhx, yF + 2 * S)], [(hhx - 4 * S, yF + 2 * S), (hhx, yF - 3 * S), (hhx + 4 * S, yF + 2 * S)]])
    cv.line([[(rdx, rdy), (rdx - 2 * S, yF + 2 * S)], [(rdx - 6 * S, yF + 2 * S), (rdx - 2 * S, yF - 3 * S), (rdx + 3 * S, yF + 2 * S)]])
    # toms
    for tx_, ty_, tr in ((kx - R * .45, ky - R * 1.08, R * .36), (kx + R * .5, ky - R * 1.12, R * .4)):
        body = _rect(tx_ - tr, ty_, tx_ + tr, ty_ + tr * .9) + []
        shell = [(tx_ - tr, ty_)] + _oval(tx_, ty_ + tr * .9, tr, tr * .28, 0, PI, 12)[::-1][::-1][::-1] + [(tx_ + tr, ty_)]
        shell = [(tx_ - tr, ty_), (tx_ + tr, ty_)] + _oval(tx_, ty_ + tr * .9, tr, tr * .28, 0, PI, 14)
        cv.obj([shell], 1.)
        cv.hair([l for l in C.hatch_poly(shell, 90, 1.5) if l[0][0] > tx_ + tr * .25 or l[0][0] < tx_ - tr * .8])
        cv.hair([l for l in C.hatch_poly(shell, 90, 3) if tx_ - tr * .8 <= l[0][0] <= tx_ + tr * .25])
        top = _oval(tx_, ty_, tr, tr * .28, n=24)
        cv.obj([top], 1.)
        cv.hair([_oval(tx_, ty_, tr * .8, tr * .2, PI * .9, PI * 1.9, 10)])
    # floor tom, right
    ftx, fty, ftr = kx + R * 1.35, yF - R * .95, R * .42
    shell = [(ftx - ftr, fty), (ftx + ftr, fty)] + _oval(ftx, fty + R * .85, ftr, ftr * .28, 0, PI, 14)
    cv.obj([shell], 1.)
    cv.hair(C.hatch_poly(shell, 90, 1.5))
    cv.obj([_oval(ftx, fty, ftr, ftr * .28, n=24)], 1.)
    # kick drum: shell ring, lugs, resonant head
    ring = _oval(kx, ky, R, R, n=64)
    cv.obj([ring], 1.5)
    cv.hair([q for q in _rings(kx, ky, R, R, R * .88, R - .8, 1.5)])
    lugs = []
    for i in range(10):
        a = TAU * (i + .5) / 10
        lugs.append([(kx + R * .9 * math.cos(a), ky + R * .9 * math.sin(a)), (kx + R * 1.06 * math.cos(a), ky + R * 1.06 * math.sin(a))])
    cv.heavy(lugs)
    head = _oval(kx, ky, R * .86, R * .86, n=56)
    cv.obj([head], 1.)
    # the head is lit from the left beam: light ruling, darker toward the right edge
    cv.hair(C.hatch_poly(head, 0, 3, .25))
    cv.hair([l for l in C.hatch_poly(head, 0, 3, 1.75) if max(p[0] for p in l) > kx + R * .35])
    cv.hair([_oval(kx, ky, R * .78, R * .78, -PI * .4, PI * .45, 18)])
    if egg:
        # Easter egg: Parker's crossed drumsticks on the kick head
        L = R * .62
        for s_ in (-1, 1):
            st = _stick(kx - s_ * L * .7, ky + L * .7, kx + s_ * L * .7, ky - L * .7, max(1.6, 2.2 * S), max(1, 1.2 * S))
            cv.obj([st], 1.)
    # cymbals, in front of the stands, lathe-turned
    for (yx, yy, yr, two) in ((hhx, hhy, R * .62, True), (rdx, rdy, R * .95, False)):
        for dy in ((0., 1.6 * S) if two else (0.,)):
            cym = _oval(yx, yy + dy, yr, max(1.8, yr * .16), n=36)
            cv.obj([cym], 1.)
            cv.hair([l for l in C.hatch_poly(cym, 0, 1.5) if l[0][1] > yy + dy])
            cv.hair([[(yx - yr * k, yy + dy), (yx + yr * k, yy + dy)] for k in (.55, .3)])
            black.append(_oval(yx, yy + dy - .4 * S, yr * .14, max(1.1, yr * .1), n=10))

    # --- the singer's mic: a vintage chromed capsule on a tall stand, front and centre
    mx, my = cx - fw * .07, fy + fh * .44
    mh, mw = fh * .17, fh * .1
    cv.obj([], 0)
    st = _stick(mx, yL - 1, mx, my + mh * .6, max(1.4, 1.8 * S), max(1.2, 1.4 * S))
    cv.obj([st], 1.)
    base = [(mx - 9 * S, yL + 1), (mx - 1 * S, yL - 6 * S), (mx + 1 * S, yL - 6 * S), (mx + 9 * S, yL + 1)]
    cv.obj([base], 1.)
    cv.hair(C.hatch_poly(base, 0, 1.5))
    yoke = _rect(mx - mw * .62, my + mh * .2, mx + mw * .62, my + mh * .62)
    cv.obj([[(mx - mw * .62, my + mh * .2), (mx - mw * .5, my + mh * .2), (mx - mw * .5, my + mh * .5),
             (mx + mw * .5, my + mh * .5), (mx + mw * .5, my + mh * .2), (mx + mw * .62, my + mh * .2),
             (mx + mw * .62, my + mh * .62), (mx - mw * .62, my + mh * .62)]], 1.)
    cv.hair(C.hatch_poly(yoke, 0, 1.5))
    caps = []
    n = 28
    for i in range(n + 1):          # rounded-shield capsule, wide at the shoulders
        t = i / n
        y_ = my - mh * .5 + mh * t
        wd = mw * .5 * (.55 + .45 * math.sin(PI * min(1, t * 1.25)) ** .5)
        caps.append((mx + wd, y_))
    caps = caps + [(2 * mx - x_, y_) for x_, y_ in caps[::-1]]
    cv.obj([caps], 1.)
    # grille: horizontal chrome bars, black slots between; centre rib, shaded right side
    for y_ in [my - mh * .42 + k * max(1.5, mh * .055) for k in range(30)]:
        if y_ > my + mh * .44:
            break
        cv.line([[(mx - mw * .5, y_), (mx + mw * .5, y_)]])
    cv.obj([_rect(mx - mw * .06, my - mh * .5, mx + mw * .06, my + mh * .5)], .5)
    cv.hair([[(mx - mw * .02, my - mh * .48), (mx - mw * .02, my + mh * .48)]])
    cv.obj([caps[:n + 1] + [(mx + mw * .3, my + mh * .5), (mx + mw * .3, my - mh * .5)]], 0)
    for y_ in [my - mh * .42 + k * max(1.5, mh * .055) for k in range(30)]:
        if y_ > my + mh * .44:
            break
        cv.heavy([[(mx + mw * .3, y_), (mx + mw * .5, y_)]])
    cv.obj([], 0)
    cv.line([caps + [caps[0]]])

    # --- curtains: gathered, tied back, deep folds
    def curtain(side):
        e = fx - 3 if side < 0 else fx + fw + 3
        tie = fy + fh * .52
        wt, wk, wb = fw * .17, fw * .045, fw * .12

        def inner(y_):
            if y_ < tie:
                t = max(0., (y_ - fy) / (tie - fy))
                ww = wt + (wk - wt) * (t ** 1.5)
            else:
                t = min(1., (y_ - tie) / (fy + fh - tie))
                ww = wk + (wb - wk) * (1 - (1 - t) ** 2)
            return e - side * ww
        ys = [fy - 3 + (fh + 6) * i / 60 for i in range(61)]
        poly = [(e, ys[0])] + [(inner(y_), y_) for y_ in ys] + [(e, ys[-1])]
        cv.obj([poly], 1.)
        NF = 7
        lines = []
        for j in range(NF * 5):
            t = (j + .5) / (NF * 5)
            ph = (t * NF) % 1
            if ph < .28:
                continue                     # highlight crest of the fold
            lines.append([(e + (inner(y_) - e) * t, y_) for y_ in ys])
            if ph > .7:
                lines.append([(e + (inner(y_) - e) * (t + .5 / (NF * 5)), y_) for y_ in ys])
        cv.hair(lines)
        # tie-back cord and tassel
        tx_ = inner(tie)
        band = [(e, tie - 2.2 * S), (tx_ - side * 1.5 * S, tie - 2.2 * S), (tx_ - side * 1.5 * S, tie + 2.2 * S), (e, tie + 2.2 * S)]
        cv.obj([band], 1.)
        cv.hair(C.hatch_poly(band, 60 * side, 1.5))
        tas = [(tx_ - side * 1 * S, tie), (tx_ - side * 4 * S, tie + 6 * S), (tx_ + side * 2 * S, tie + 6 * S)]
        cv.obj([tas], 1.)
        cv.hair(C.hatch_poly(tas, 90, 1.5))
    curtain(-1)
    curtain(1)

    # --- valance: swagged, scalloped, fringed, with the spot cans hanging under it
    cv.obj([], 0)
    for u, lit in cans:
        sx = cx + u * fw
        can = [(sx - 3 * S, yV - 1), (sx + 3 * S, yV - 1), (sx + 3.6 * S, yV + 5 * S), (sx - 3.6 * S, yV + 5 * S)]
        cv.obj([can], 1.)
        cv.hair(C.hatch_poly(can, 90, 1.5))
        if lit:
            black.append(_oval(sx, yV + 5 * S, 3.4 * S, 1.2 * S, n=12))
    nsw = 5
    sw = (fw + 6) / nsw
    edge = []
    for i in range(nsw * 16 + 1):
        x_ = fx - 3 + (fw + 6) * i / (nsw * 16)
        t = ((x_ - fx + 3) / sw) % 1
        edge.append((x_, yV - 3 * S + 6 * S * math.sin(PI * t)))
    val = [(fx - 3, fy - 3), (fx + fw + 3, fy - 3)] + edge[::-1]
    cv.obj([val], 1.)
    sw_lines = []
    for k in range(1, 6):
        q = []
        for x_, y_ in edge:
            t = ((x_ - fx + 3) / sw) % 1
            q.append((x_, y_ - k * 1.6 * S * (.4 + .6 * math.sin(PI * t))))
        sw_lines.append(q)
    cv.hair(sw_lines)
    cv.hair([l for l in C.hatch_poly(val, 0, 1.5) if l[0][1] < yV - 7 * S])
    cv.hair([[(x_, y_), (x_, y_ + 2.4 * S)] for x_, y_ in edge[::2]])
    o.append(cv.svg())

    # --- the crowd in silhouette, hands up, and the taper's stand rising out of it
    crowd_y = yL + fh * .045
    rimw = []
    hd = []
    for row, (dy, rs) in enumerate(((0., 1.), (5.5, 1.15))):
        xx = fx - 4 + rng.uniform(0, 6) * S
        while xx < fx + fw + 6:
            r = rng.uniform(3.2, 4.4) * S * rs
            yy = crowd_y + dy * S + rng.uniform(-1.5, 2.5) * S
            hd.append(_oval(xx, yy, r * .82, r, n=14))
            hd.append(_oval(xx, yy + r * 2.0, r * 2.0, r * 1.25, n=18))
            # rim light from the stage on the crown and the shoulders, both rows
            rimw.append(_oval(xx - r * .1, yy - r * .1, r * .62, r * .82, PI * 1.05, PI * 1.6, 6))
            rimw.append(_oval(xx, yy + r * 2.0, r * 1.75, r * 1.0, PI * 1.08, PI * 1.42, 6))
            rimw.append(_oval(xx, yy + r * 2.0, r * 1.75, r * 1.0, PI * 1.62, PI * 1.9, 6))
            if row == 1:
                rimw.append(_oval(xx, yy + r * 2.0, r * 1.3, r * .62, PI * 1.15, PI * 1.85, 8))
            if row == 0:
                if rng.random() < .3:
                    side = rng.choice((-1, 1))
                    ax_ = xx + side * r * 1.4
                    hand_y = yy - rng.uniform(8, 13) * S
                    hd.append(_stick(ax_, yy + r * 1.2, ax_ + side * 2 * S, hand_y, 2.2 * S, 1.6 * S))
                    hd.append(_oval(ax_ + side * 2 * S, hand_y - .8 * S, 1.4 * S, 1.8 * S, n=8))
                    rimw.append([(ax_ - 1.0 * S, yy), (ax_ + side * 2 * S - 1.0 * S, hand_y + 1 * S)])
            xx += r * rng.uniform(1.8, 2.5)
    hd.append(_rect(fx - 4, crowd_y + 9 * S, fx + fw + 4, fy + fh + 4))
    tx_ = cx + fw * .235
    top_ = fy + fh * .36
    hd.append(_rect(tx_ - .8, top_, tx_ + .8, crowd_y + 4 * S))
    hd.append(_rect(tx_ - 11 * S, top_ - .8, tx_ + 11 * S, top_ + .8))
    for s_ in (-1, 1):   # a pair of pencil condensers in ORTF, the taper's signature
        hd.append(_stick(tx_ + s_ * 10 * S, top_ + 1, tx_ + s_ * 4 * S, top_ - 12 * S, 2.6 * S, 2.2 * S))
        hd.append(_rect(tx_ + s_ * 10 * S - 1.2 * S, top_ - 2, tx_ + s_ * 10 * S + 1.2 * S, top_ + 2))
    o.append(f'<path d="{_blk(black)}{_blk(hd)}" fill="#000" stroke="none"/>')
    # rim light from the stage on the front row; the dark house behind them ruled, never solid
    o.append(f'<path d="{"".join(_d(p, False, .2) for p in rimw)}" stroke="#fff" stroke-width="1" fill="none" stroke-linecap="round"/>')
    floor_d = _rect(fx - 4, crowd_y + 14 * S, fx + fw + 4, fy + fh + 4)
    o.append(f'<path d="{C.hatch_d(floor_d, 0, 3, 1.25)}" stroke="#fff" stroke-width="1"{CR}/>')
    # the room behind them is not empty paper: rim light on shoulders
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# a reel of tape (short plates' medallion)
# ------------------------------------------------------------------------------------------------

def reel_medallion(cx, cy, rx, ry, seed=0):
    o = []
    outer = _oval(cx, cy, rx + 1, ry + 1, n=64)
    o.append(f'<path d="{_d(outer, True, 0)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_d(outer, True, 0)}{_d(_oval(cx, cy, rx - 2, ry - 2, n=64)[::-1], True, 0)}" fill="#000" fill-rule="evenodd"/>')
    r = ry - 3.5
    # the wound tape pack behind the flange: tight concentric turns
    pack = _rings(cx, cy, r, r, r * .35, r, 1.5, n=48)
    o.append(f'<path d="{"".join(_d(p, True, .2) for p in pack)}" stroke="#000" stroke-width=".5" fill="none"/>')
    # the flange outside the reel, out to the oval edge: light ruling
    if rx - 2 > r + 2:
        ring = _d(_oval(cx, cy, rx - 2, ry - 2, n=64), True, 0) + _d(_oval(cx, cy, r, r, n=48)[::-1], True, 0)
        o.append(f'<path d="{ring}" fill="{C.pat("M")}" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(_oval(cx, cy, r, r, n=48), True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
    # three spokes of the reel flange
    cv = C.Canvas()
    rot = (seed % 12) * TAU / 36
    for k in range(3):
        a = rot + TAU * k / 3
        sp = []
        for i in range(9):
            t = a - .32 + .64 * i / 8
            sp.append((cx + r * .96 * math.cos(t), cy + r * .96 * math.sin(t)))
        for i in range(9):
            t = a + .6 - 1.2 * i / 8
            sp.append((cx + r * .36 * math.cos(t), cy + r * .36 * math.sin(t)))
        cv.obj([sp], 1.)
        cv.hair(C.hatch_poly(sp, 0, 3, .25))
        cv.hair([l for l in C.hatch_poly(sp, 0, 3, 1.75)
                 if math.cos(math.atan2(l[0][1] - cy, l[0][0] - cx) - a - .25) < .97])
    rim_o, rim_i = _oval(cx, cy, r, r, n=56), _oval(cx, cy, r * .93, r * .93, n=56)
    cv.obj([], 0)
    cv.line([rim_o + [rim_o[0]], rim_i + [rim_i[0]]])
    hub = _oval(cx, cy, r * .36, r * .36, n=32)
    cv.obj([hub], 1.)
    cv.hair(_rings(cx, cy, r * .36, r * .36, r * .22, r * .34, 1.5, n=24))
    cv.obj([_oval(cx, cy, r * .22, r * .22, n=24)], .5)
    cv.hair(C.hatch_poly(_oval(cx, cy, r * .22, r * .22, n=24), 0, 3, .25))
    o.append(cv.svg())
    # Easter egg: crossed drumsticks on the hub label
    L = r * .2
    st = [_stick(cx - L, cy + L, cx + L, cy - L, 1.4, .9), _stick(cx + L, cy + L, cx - L, cy - L, 1.4, .9)]
    o.append(f'<path d="{_blk(st)}" fill="#000"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# layouts (house layouts, re-cut for this page: no blank white anywhere)
# ------------------------------------------------------------------------------------------------

def _bg(w, h):
    return C.dark_ground((0, 0, w, h), "D")


def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _field_box(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _layout_band(w, h, seed):
    o = [_bg(w, h)]
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.25, 100)
    o.append(C._clip(C._uid("b6", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .85, r_scale=1.15 * max(1., 62. / gh))))
    o.append(reel_medallion(w / 2, top + gh / 2, gap / 2, gh / 2 - 1, seed))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = [_bg(w, h)]
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.75)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m6", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_box(cx, cy, cw, gh + 4)
    o.append(_field_clip(C._uid("mv6", w, h, seed), inner, stage(fx, fy, fw, fh, seed, egg=True)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = [_bg(w, h)]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .6, ph * .72
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
    r1 = min(pw * .16, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .45)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .13, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .45)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .035), rmax=r1 * .9,
                   max_n=13, edge=.5, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t6", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _field_box(cx, cy, cw, ch)
    o.append(_field_clip(C._uid("tv6", w, h, seed), inner, stage(fx, fy, fw, fh, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 60), True, rng.randrange(1 << 20)))
    bh = min(17, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .48, cw * 1.3, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(f'<path d="{_pl_d(letter_arc("LIVE FROM PORTLAND", centre, bh * .48, 2.0))}" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    words = "LIVE MUSIC ARCHIVE * TAPED IN PORTLAND"
    size = min(th * .56, 10)
    ww = _word_w(words, 2.2) * size / 6
    if ww > tw - 14:
        words = "LIVE MUSIC ARCHIVE"
        ww = _word_w(words, 2.2) * size / 6
    o.append(f'<path d="{_d(_rect(tx + 2.5, ty + 2.5, tx + tw - 1, ty + th - 1), True, 0)}" fill="{C.pat("L")}" stroke="none"/>')
    o.append(f'<path d="{_d(_rect(tx + tw / 2 - ww / 2 - 4, ty + 2.5, tx + tw / 2 + ww / 2 + 4, ty + th - 1), True, 0)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_pl_d(letter_line(words, tx + tw / 2 + .5, ty + th / 2 + .8, size, 2.2))}" stroke="#000" stroke-width="1"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f6", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.25, r_scale=1.15, n=2)))
        o.append(reel_medallion(w / 2, fy + fh / 2 - 1, fh * .62, fh / 2 - 2, seed))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 6

    def sc(x, y, sw, sh, mode):
        return stage(x, y, sw, sh, seed, True)

    def banner(centre, rh):
        return f'<path d="{_pl_d(letter_arc("LIVE FROM PORTLAND", centre, rh * .48, 2.0))}" stroke="#000" stroke-width="1"/>'

    def egg(cv, x, y, s):
        # a reel of the taper's tape, spokes and wound pack, hidden in the scroll
        r = s * .48
        cv.obj([_ell(x, y, r, r, 30)[:-1]], 1.)
        for q in (.86, .74, .62):
            cv.hair(_ell(x, y, r * q, r * q, 26))
        cv.obj([_ell(x, y, r * .5, r * .5, 22)[:-1]], .5)
        for i in range(3):
            a = _TAU * i / 3 + .3
            cv.obj([[(x + r * .14 * _m.cos(a + .5), y + r * .14 * _m.sin(a + .5)),
                     (x + r * .46 * _m.cos(a + .32), y + r * .46 * _m.sin(a + .32)),
                     (x + r * .46 * _m.cos(a - .32), y + r * .46 * _m.sin(a - .32)),
                     (x + r * .14 * _m.cos(a - .5), y + r * .14 * _m.sin(a - .5))]], .5)
            cv.hair(_C.hatch_poly([(x + r * .16 * _m.cos(a + .45), y + r * .16 * _m.sin(a + .45)),
                                   (x + r * .44 * _m.cos(a + .28), y + r * .44 * _m.sin(a + .28)),
                                   (x + r * .44 * _m.cos(a - .28), y + r * .44 * _m.sin(a - .28)),
                                   (x + r * .16 * _m.cos(a - .45), y + r * .16 * _m.sin(a - .45))], 45, 1.5))
        cv.obj([_ell(x, y, r * .12, r * .12, 12)[:-1]], .5)

    return compose(w, h, sc, seed, medal="arch" if h > 260 else "cushion", egg=egg, arms=True, banner=banner)
