"""river-02 "The Columbia, by the numbers": the river at Sauvie Island this morning.
A USGS staff gauge on a creosoted pile reads the day's level (ctx sample, default 4.7 ft) with the
tide's wet band on the wood; a grain ship runs up the channel under Mt. Hood; the Washington shore
of firs; reeds of the island bank. The house Codex frame carries it. Easter egg: Parker's Sauvie
Island heron standing on top of the gauge pile."""
import sys
import math
import random
import re
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
        e = {"oval": 2., "squircle": 2.8, "cushion": 3.6, "round": 2., "banner": 5., "lunette": 2.}.get(kind, 2.)
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
        elif kind == "banner":
            # a ribbon cartouche: long and square-shouldered, a swallowtail notch cut into each end
            x = cx + a * _m.copysign(abs(c_) ** (2 / e), c_) * (1 - .1 * _m.exp(-(s_ / .22) ** 2))
        elif kind == "lunette":
            if s_ > 0:
                x = cx + a * _m.copysign(abs(c_) ** .25, c_)
                y = cy + b * _m.copysign(abs(s_) ** .2, s_)
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


def _keep_disc(segs, cx, cy, r):
    """clip polylines (lists of points) to a disc: the shadow side of a form"""
    out = []
    for pl in segs:
        cur = []
        for i in range(len(pl) - 1):
            (ax, ay), (bx, by) = pl[i], pl[i + 1]
            n = max(1, int(_m.hypot(bx - ax, by - ay) / 1.5))
            for j in range(n + 1):
                px, py = ax + (bx - ax) * j / n, ay + (by - ay) * j / n
                if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                    cur.append((px, py))
                elif cur:
                    if len(cur) > 1:
                        out.append(cur)
                    cur = []
        if len(cur) > 1:
            out.append(cur)
    return out


def fig_dogface(cv, cx, cy, r):
    """Parker's dog looking straight out, the head filling a circle of radius r (the O of a word)"""
    for sd in (-1, 1):   # floppy ears, hatched dark on the inside
        ear = [(cx + sd * r * .45, cy - r * .75), (cx + sd * r * 1.02, cy - r * .55), (cx + sd * r * 1.08, cy + r * .1),
               (cx + sd * r * .9, cy + r * .45), (cx + sd * r * .62, cy + r * .1)]
        cv.obj([ear], 1.)
        cv.hair(_C.hatch_poly(ear, 70 * sd, 1.5))
    head = _ell(cx, cy, r * .72, r * .82, 24)[:-1]
    cv.obj([head], 1.)
    for k in range(3):   # the brow and the coat over the skull
        cv.hair([(cx - r * (.35 - k * .05), cy - r * (.62 - k * .1)), (cx, cy - r * (.5 - k * .1)), (cx + r * (.35 - k * .05), cy - r * (.62 - k * .1))])
    for sd in (-1, 1):
        cv.obj([_ell(cx + sd * r * .28, cy - r * .12, r * .11, r * .11, 10)[:-1]], 1.)
        cv.hair(_ell(cx + sd * r * .28, cy - r * .12, r * .18, r * .15, 10))
    muz = _ell(cx, cy + r * .32, r * .4, r * .32, 18)[:-1]
    cv.obj([muz], .5)
    cv.hair(_C.hatch_poly(_ell(cx + r * .12, cy + r * .4, r * .25, r * .2, 12)[:-1], 45, 1.5))
    cv.obj([[(cx - r * .14, cy + r * .12), (cx + r * .14, cy + r * .12), (cx, cy + r * .28)]], 1.)
    cv.line([(cx, cy + r * .28), (cx, cy + r * .4), (cx - r * .14, cy + r * .48)])
    cv.line([(cx, cy + r * .4), (cx + r * .14, cy + r * .48)])


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
            + _slim(_simp(_AR.arms(w, s, seed), .25)) + "</svg>")


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


def _garc(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * _m.cos(_m.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * _m.sin(_m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_GF = {
    "A": (.72, [[(0, 1), (.36, 0), (.72, 1)], [(.15, .64), (.57, .64)]]),
    "B": (.6, [[(0, 0), (0, 1), (.38, 1)] + _garc(.38, .76, .22, .24, 90, -90, 6) + [(0, .52)],
               [(0, 0), (.33, 0)] + _garc(.33, .26, .2, .26, -90, 90, 6)[1:] + [(0, .52)]]),
    "C": (.66, [_garc(.36, .5, .34, .5, -45, -315, 12)]),
    "D": (.68, [[(0, 0), (0, 1), (.3, 1)] + _garc(.3, .5, .36, .5, 90, -90, 10) + [(0, 0)]]),
    "E": (.56, [[(.54, 0), (0, 0), (0, 1), (.54, 1)], [(0, .5), (.42, .5)]]),
    "F": (.54, [[(.54, 0), (0, 0), (0, 1)], [(0, .5), (.42, .5)]]),
    "G": (.7, [_garc(.36, .5, .34, .5, -45, -315, 12) + [(.7, .58), (.42, .58)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    "I": (.08, [[(.04, 0), (.04, 1)]]),
    "J": (.46, [[(.44, 0), (.44, .74)] + _garc(.22, .74, .22, .26, 0, 180, 6)[1:]]),
    "K": (.62, [[(0, 0), (0, 1)], [(.6, 0), (0, .6)], [(.2, .45), (.62, 1)]]),
    "L": (.52, [[(0, 0), (0, 1), (.52, 1)]]),
    "M": (.84, [[(0, 1), (0, 0), (.42, .8), (.84, 0), (.84, 1)]]),
    "N": (.68, [[(0, 1), (0, 0), (.68, 1), (.68, 0)]]),
    "O": (.76, [_garc(.38, .5, .38, .5, 0, 360, 16)]),
    "P": (.58, [[(0, 1), (0, 0), (.32, 0)] + _garc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)]]),
    "Q": (.76, [_garc(.38, .5, .38, .5, 0, 360, 16), [(.45, .7), (.78, 1.04)]]),
    "R": (.62, [[(0, 1), (0, 0), (.32, 0)] + _garc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)],
                [(.28, .54), (.62, 1)]]),
    "S": (.56, [_garc(.28, .25, .26, .25, -20, -270, 7) + _garc(.28, .75, .28, .25, -90, 160, 7)[1:]]),
    "T": (.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "U": (.66, [[(0, 0), (0, .66)] + _garc(.33, .66, .33, .34, 180, 0, 8)[1:] + [(.66, 0)]]),
    "V": (.7, [[(0, 0), (.35, 1), (.7, 0)]]),
    "W": (.96, [[(0, 0), (.24, 1), (.48, .2), (.72, 1), (.96, 0)]]),
    "X": (.64, [[(0, 0), (.64, 1)], [(.64, 0), (0, 1)]]),
    "Y": (.66, [[(0, 0), (.33, .5), (.66, 0)], [(.33, .5), (.33, 1)]]),
    "Z": (.6, [[(0, 0), (.6, 0), (0, 1), (.6, 1)]]),
    "0": (.54, [_garc(.27, .5, .27, .5, 0, 360, 14)]),
    "1": (.36, [[(.04, .2), (.26, 0), (.26, 1)], [(.04, 1), (.48, 1)]]),
    "2": (.54, [_garc(.27, .27, .26, .27, -170, 10, 6) + [(0, 1), (.54, 1)]]),
    "3": (.52, [_garc(.25, .25, .25, .25, -160, 90, 6), _garc(.25, .74, .27, .26, -90, 160, 6)]),
    "4": (.58, [[(.42, 1), (.42, 0), (0, .7), (.58, .7)]]),
    "5": (.54, [[(.5, 0), (.08, 0), (.04, .44)] + _garc(.26, .7, .28, .3, -120, 150, 8)]),
    "6": (.56, [[(.46, .02), (.2, .2), (.02, .65)] + _garc(.28, .7, .26, .3, 180, 540, 12)]),
    "7": (.54, [[(0, 0), (.54, 0), (.2, 1)]]),
    "8": (.54, [_garc(.27, .25, .22, .25, 90, 450, 10), _garc(.27, .74, .27, .26, -90, 270, 12)]),
    "9": (.56, [_garc(.28, .3, .26, .3, 0, 360, 12) + [(.54, .35), (.36, .8), (.1, .98)]]),
    "-": (.4, [[(.04, .55), (.36, .55)]]),
    ".": (.2, [[(.1, .92), (.1, .96)]]),
    "·": (.36, [[(.18, .4), (.26, .51), (.18, .62), (.1, .51), (.18, .4), (.18, .62)]]),
}


def motto(centre, txt, rh, w=1., holes=None, fill=.86):
    """txt lettered in drawn capitals along the ribbon centre line, cap = half the ribbon height"""
    cap = rh * .5
    L = sum(_m.dist(centre[i - 1], centre[i]) for i in range(1, len(centre)))
    tw = sum((_GF.get(ch, (.5, []))[0] + .32) * cap if ch != " " else .5 * cap for ch in txt) - .32 * cap
    _GF.setdefault("@", (.76, []))
    while tw > L * fill and cap > 3:
        cap *= .92
        tw = sum((_GF.get(ch, (.5, []))[0] + .32) * cap if ch != " " else .5 * cap for ch in txt) - .32 * cap

    def along(s, off):
        acc = 0.
        for i in range(1, len(centre)):
            p, q = centre[i - 1], centre[i]
            Lq = _m.dist(p, q)
            if acc + Lq >= s or i == len(centre) - 1:
                t = (s - acc) / Lq if Lq else 0
                nx, ny = (-(q[1] - p[1]) / Lq, (q[0] - p[0]) / Lq) if Lq else (0, 1)
                return (p[0] + (q[0] - p[0]) * t + nx * off, p[1] + (q[1] - p[1]) * t + ny * off)
            acc += Lq
        return centre[-1]
    out, cur = [], (L - tw) / 2
    for ch in txt.upper():
        if ch == " ":
            cur += .5 * cap
            continue
        gw, strokes = _GF.get(ch, _GF["·"])
        if ch == "@" and holes is not None:
            holes.append(along(cur + gw * cap / 2, 0.) + (cap,))
        for st in strokes:
            out.append([along(cur + px * cap, -cap / 2 + py * cap) for px, py in st])
        cur += (gw + .32) * cap
    return f'<path d="{"".join(_dd(p, False, .05) for p in out)}" fill="none" stroke="#000" stroke-width="{_nn(w)}"/>'


def _extras(fn, occ, g):
    out = []
    if fn:
        for poly, svg in fn(g):
            if poly:
                occ.poly(poly)
            out.append(svg)
    return out


def _rdp(P, tol):
    if len(P) < 3:
        return P
    (ax, ay), (bx, by) = P[0], P[-1]
    dx, dy = bx - ax, by - ay
    L = _m.hypot(dx, dy) or 1e-9
    i, dm = 0, -1.
    for j in range(1, len(P) - 1):
        dd = abs((P[j][0] - ax) * dy - (P[j][1] - ay) * dx) / L
        if dd > dm:
            i, dm = j, dd
    if dm <= tol:
        return [P[0], P[-1]]
    return _rdp(P[:i + 1], tol)[:-1] + _rdp(P[i:], tol)


def _simp(sv, tol=.3):
    """path data of absolute M/L/Z polylines -> simplified, relative, one decimal"""
    def one(m):
        d = m.group(1)
        if not _re.fullmatch(r"(?:[MLZz][-\d., ]*)+", d):
            return m.group(0)
        o, cx, cy = [], 0., 0.
        for sub in _re.findall(r"M[^M]*", d):
            closed = sub.rstrip().endswith(("Z", "z"))
            nums = [float(v) for v in _re.findall(r"-?\d*\.?\d+", sub)]
            P = _rdp(list(zip(nums[0::2], nums[1::2])), tol)
            q = []
            for k, (x, y) in enumerate(P):
                x, y = round(x, 1), round(y, 1)
                if k == 0:
                    q.append(f"M{_nn(x)} {_nn(y)}" if not o else f"m{_nn(round(x - cx, 1))} {_nn(round(y - cy, 1))}")
                else:
                    q.append(f"l{_nn(round(x - cx, 1))} {_nn(round(y - cy, 1))}")
                cx, cy = x, y
            if closed:
                q.append("z")
                cx, cy = round(P[0][0], 1), round(P[0][1], 1)
            o.append("".join(q))
        return ' d="' + "".join(o) + '"'
    return _re.sub(r' d="([^"]*)"', one, sv)


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
            panel=None, ribbon=True, banner=None, extras=None, mw_frac=None):
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
        mw = min(H * 2.3, 210.) if mw_frac is None else max(H * 1.2, (x1 - x0) * mw_frac)
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
        acs_m = ""
        if mode == "medium":
            mh = H - 4
            cy = (y0 + y1) / 2
            if arms:
                # a section front: the small dedication cartouche with Parker's arms at the vignette's foot
                acs_sz = max(26., min(40., H * .24))
                mh = H - 4 - acs_sz * .55
                cy = y0 + 2 + mh / 2
                ay = y1 - acs_sz / 2 - 1
                acs_m = arms_somaster(cx, ay, acs_sz, seed % 5)
                occ.poly(shape_pts(cx, ay, acs_sz * .42 + 2, acs_sz / 2 + 1, "cushion"))
            mw = min(w * .4, mh * 1.32) if mw_frac is None else max(mh, w * mw_frac)
        else:
            mw = min(w * .52, (H) * .74)
            mh = min(H * .74, mw * 1.3)
            cy = y0 + H * .06 + mh / 2 + (cc * .35 if kind == "arch" else 0)
            mh = min(mh, (y1 - cy) * 2 - 30)
        mk = medal
        fr, field, outer = medallion(cx, cy, mw, mh, mk)
        if acs_m:
            top.append(acs_m)
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


TAU = 2 * math.pi
_K = 2 ** (-1 / 2.6)


def _level(ctx):
    m = re.search(r"at ([0-9]+(?:\.[0-9])?) ft at Vancouver", (ctx or {}).get("sample", "") or "")
    try:
        return float(m.group(1)) if m else 4.7
    except ValueError:
        return 4.7


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _wave_row(x0, x1, y, amp, per, ph, step=2.):
    pts = []
    x = x0
    while x <= x1 + step:
        xx = min(x, x1)
        pts.append((xx, y + amp * math.sin(TAU * xx / per + ph) + amp * .4 * math.sin(TAU * xx / (per * .37) + ph * 1.7)))
        if xx >= x1:
            break
        x += step
    return pts


def _split(pl, rng, dash=(10, 40), gap=(1.6, 3.4)):
    """Break a polyline into dashes (by arc length)."""
    out, cur, acc = [], [pl[0]], 0.
    target = rng.uniform(*dash)
    gapping = False
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        acc += L
        if not gapping:
            cur.append(b)
            if acc >= target:
                if len(cur) > 1:
                    out.append(cur)
                gapping, acc, target = True, 0., rng.uniform(*gap)
        else:
            if acc >= target:
                cur = [b]
                gapping, acc, target = False, 0., rng.uniform(*dash)
    if not gapping and len(cur) > 1:
        out.append(cur)
    return out


# ---------------------------------------------------------------- stroke digits (no <text>)
_DIG = {
    "0": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)]],
    "1": [[(.5, 0), (.5, 2)], [(.15, .35), (.5, 0)]],
    "2": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (1, 2)]],
    "3": [[(0, 0), (1, 0), (1, 2), (0, 2)], [(.2, 1), (1, 1)]],
    "4": [[(0, 0), (0, 1), (1, 1)], [(1, 0), (1, 2)]],
    "5": [[(1, 0), (0, 0), (0, 1), (1, 1), (1, 2), (0, 2)]],
    "6": [[(1, 0), (0, 0), (0, 2), (1, 2), (1, 1), (0, 1)]],
    "7": [[(0, 0), (1, 0), (.4, 2)]],
    "8": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)], [(0, 1), (1, 1)]],
    "9": [[(1, 1), (0, 1), (0, 0), (1, 0), (1, 2), (0, 2)]],
}


def _digit(ch, x, y, hgt):
    s = hgt / 2
    return [[(x + px * s * .85, y + py * s) for px, py in st] for st in _DIG[ch]]


# ---------------------------------------------------------------- the scene
def _scene(cv, X0, Y0, W, H, level, seed, compact):
    rng = random.Random(seed)
    X1, Y1 = X0 + W, Y0 + H
    hy = Y0 + H * (.52 if not compact else .5)            # horizon (far waterline)
    S = H / 100.

    # sky: ruled, denser aloft, with long dawn streaks of cloud
    sky = _rect(X0 - 2, Y0 - 2, W + 4, hy - Y0 + 4)
    cv.obj([sky], 0)
    y = Y0
    while y < hy:
        t = (y - Y0) / max(1., hy - Y0)
        cv.hair([(X0, y), (X1, y)])
        y += 1.5 if t < .35 else (2. if t < .7 else 3.)
    if not compact:
        for i in range(4):
            cx = X0 + W * (.12 + .26 * i + rng.uniform(-.05, .05))
            cy = Y0 + (hy - Y0) * rng.uniform(.18, .5)
            L, th = W * rng.uniform(.12, .2), max(3.5, H * .022)
            top = [(cx - L + 2 * L * k / 16, cy - th * math.sin(math.pi * k / 16) ** .7) for k in range(17)]
            bot = [(cx + L - 2 * L * k / 16, cy + th * .45 * math.sin(math.pi * k / 16)) for k in range(17)]
            poly = top + bot
            cv.obj([poly], .5)
            cv.hair(C.hatch_poly(poly, 0, 3, .5 + cy % 3, 1.5))
        # two gulls
        for gx, gy, gs in ((.3, .2, 1.), (.36, .26, .8)):
            x, y = X0 + W * gx, Y0 + (hy - Y0) * gy
            r = 3.2 * S * gs
            cv.obj([], 0)
            cv.line([(x - r, y + r * .1), (x - r * .45, y - r * .45), (x, y + r * .15), (x + r * .45, y - r * .45), (x + r, y + r * .1)])

    # Mt. Hood: steep summit pyramid, concave flanks, the Steel Cliff shoulder to the east
    pkx, pky = X0 + W * .45, hy - H * (.36 if not compact else .3)
    mh = hy - pky
    mw = min(W * .36, mh * 2.3)
    rm = random.Random(seed + 7)
    left, right = [], []
    for k in range(25):
        t = k / 24.
        yy = pky + mh * t
        xl = mw * (.32 * t + .68 * t ** 2.3) * (1 + .03 * math.sin(k * 2.1)) + rm.uniform(0, .8)
        xr = mw * (.3 * t + .7 * t ** 2.1) * 1.08 + mw * .1 * math.exp(-((t - .38) / .1) ** 2) + rm.uniform(0, .8)
        left.append((pkx - xl, yy))
        right.append((pkx + xr, yy))
    mtn = left[::-1] + [(pkx - .6, pky - 1.2), (pkx + .6, pky - 1.2)] + right
    base = mtn + [(pkx + mw * 1.3, hy + 2), (pkx - mw * 1.3, hy + 2)]
    cv.obj([base], 1)
    inside = lambda p: _inside(p, base)
    snow_y = lambda x: pky + mh * (.52 + .13 * math.sin((x - pkx) / mw * 9 + 1) + .07 * math.sin((x - pkx) / mw * 23)
                                   + .25 * (abs(x - pkx) / mw) ** 2)
    ridge = [(pkx + mh * .07 * t * math.sin(t * 4), pky + mh * t) for t in [k / 20 for k in range(21)]]
    east = [(pkx, pky)] + right[1:] + ridge[::-1]
    cv.hair(_clip_lines(C.hatch_poly(east, 64, 1.5), base))
    west = left + [(pkx, hy)] + ridge[::-1]
    cv.hair(C.hatch_poly(west, -14, 3., .7))
    xs = [pkx - mw * 1.3 + i * mw * 2.6 / 80 for i in range(81)]
    rock = [(x, snow_y(x)) for x in xs] + [(xs[-1], hy + 2), (xs[0], hy + 2)]
    cv.hair(_clip_lines(C.hatch_poly(rock, -30, 1.5) + C.hatch_poly(rock, 30, 3), base))
    # glaciers and couloirs: heavier lines raking down the snowfield
    for k in range(7 if not compact else 3):
        f = -.6 + 1.2 * k / (6 if not compact else 2)
        x0 = pkx + mw * f * .18
        y0 = pky + mh * (.08 + .05 * abs(f))
        pts = [(x0 + mw * f * .55 * t + 1.2 * math.sin(t * 7 + k), y0 + mh * .5 * t) for t in [j / 10 for j in range(11)]]
        pts = [p for p in pts if inside(p) and p[1] < snow_y(p[0]) + 2]
        if len(pts) > 1:
            (cv.line if f > 0 else cv.hair)(pts)
    cv.line(ridge[:13])

    # foothills, then the Washington shore of firs
    fh = [(X0 - 2, hy - H * .07)]
    for i in range(41):
        x = X0 + W * i / 40
        fh.append((x, hy - H * (.05 + .025 * math.sin(i * .5 + seed) + .015 * math.sin(i * 1.3))))
    fh += [(X1 + 2, hy - H * .05), (X1 + 2, hy + 1), (X0 - 2, hy + 1)]
    cv.obj([fh], .5)
    cv.hair(C.hatch_poly(fh, 20, 1.5))
    cv.hair(C.hatch_poly(fh, -40, 3))
    shore = [(X0 - 2, hy)]
    x = X0 - 2
    rs = random.Random(seed + 3)
    while x < X1 + 2:
        th = H * rs.uniform(.022, .05)
        wv = th * .45
        base = hy - H * .018
        shore += [(x, base), (x + wv, base - th), (x + 2 * wv, base)]
        x += 2 * wv * rs.uniform(.7, 1.0)
    shore += [(X1 + 2, hy + 1), (X0 - 2, hy + 1)]
    cv.obj([shore], .5)
    cv.line(C.hatch_poly(shore, 90, 1.5))
    cv.hair(C.hatch_poly(shore, 0, 2))

    # the river
    wy0 = hy
    water = _rect(X0 - 2, wy0, W + 4, Y1 - wy0 + 2)
    cv.obj([water], 0)
    # the ship's span (for its reflection)
    L = min(W * .5, H * 1.25)
    sx = X0 + W * (.1 if not compact else .06)
    ys = hy + H * .075
    hh = max(3., L * .075)
    rw = random.Random(seed + 11)
    y = wy0 + 1
    while y < Y1 + 2:
        t = (y - wy0) / max(1., Y1 - wy0)
        amp = .25 + 1.1 * t
        row = _wave_row(X0 - 2, X1 + 2, y, amp, 14 + 30 * t, rw.uniform(0, TAU))
        in_refl = ys - 1 < y < ys + hh * 2.6
        if in_refl:
            a = [p for p in row if p[0] < sx + L * .02]
            b = [p for p in row if sx + L * .02 <= p[0] <= sx + L * .96]
            c = [p for p in row if p[0] > sx + L * .96]
            for part in (a, c):
                if len(part) > 1:
                    cv.hair(_split(part, rw, (8 + 30 * (1 - t), 30 + 40 * (1 - t))))
            if len(b) > 1:
                cv.line(_split(b, rw, (14, 50), (.8, 1.6)))
        else:
            segs = _split(row, rw, (8 + 30 * (1 - t), 30 + 40 * (1 - t)), (1.4, 2.4 + 2 * t))
            (cv.line if t > .55 else cv.hair)(segs)
        y += 1.5 if t < .2 else (2. if t < .5 else 3.)

    # the grain ship running up the channel
    _ship(cv, sx, ys, L, hh, compact)

    # the gauge pile in the foreground
    gx = X0 + W * (.86 if not compact else .84)
    wl = hy + H * (.31 if not compact else .3)
    pw = max(5., H * .085)
    ft = H * .105
    top = wl - ft * (3.3 if not compact else 2.4)
    _pile(cv, gx, top, wl, pw, ft, level, compact)
    if not compact:
        _heron(cv, gx + pw * .1, top - pw * .1, H * .25)
    # the island bank, reeds and cattails, bottom left
    _bank(cv, X0, Y1, W, H, seed, compact)


def _inside(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (x1 - x0) * (y - y0) / (y1 - y0):
            c = not c
    return c


def _clip_lines(lines, poly):
    """Keep the parts of 2-point lines inside poly (sampled)."""
    out = []
    for (a, b) in lines:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(2, int(L / 1.))
        cur = []
        for i in range(n + 1):
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            if _inside(p, poly):
                cur.append(p)
            elif cur:
                if len(cur) > 1:
                    out.append([cur[0], cur[-1]])
                cur = []
        if len(cur) > 1:
            out.append([cur[0], cur[-1]])
    return out


def _ship(cv, sx, ys, L, hh, compact):
    bx = sx + L
    # bow wave and wake foam
    foam = [(bx - L * .08, ys + .5), (bx + L * .015, ys - hh * .15), (bx + L * .05, ys + hh * .35), (bx - L * .1, ys + hh * .45)]
    hull = [(sx, ys - hh), (sx + L * .03, ys - hh * .02), (sx + L * .045, ys), (bx - L * .04, ys), (bx, ys - hh * 1.25),
            (bx - L * .06, ys - hh * 1.25), (bx - L * .07, ys - hh * 1.0), (sx + L * .02, ys - hh)]
    cv.obj([hull], 1)
    cv.heavy(C.hatch_poly(hull, 0, 1.5, .3))
    # hatch covers along the deck, cranes between them
    nh = 5
    hy0 = ys - hh
    for i in range(nh):
        x0 = sx + L * (.24 + i * .135)
        cov = [(x0, hy0), (x0 + L * .09, hy0), (x0 + L * .085, hy0 - hh * .45), (x0 + L * .005, hy0 - hh * .45)]
        cv.obj([cov], .5)
        cv.hair(C.hatch_poly(cov, 90, 1.5))
    for i in range(4):
        x0 = sx + L * (.355 + i * .135)
        post = _rect(x0 - .9, hy0 - hh * 1.6, 1.8, hh * 1.6)
        cv.obj([post], .5)
        cv.heavy([(x0, hy0 - hh * 1.5), (x0 - L * .075, hy0 - hh * 2.6)])
        cv.hair([(x0, hy0 - hh * 2.1), (x0 - L * .075, hy0 - hh * 2.6)])
        cv.line([(x0, hy0), (x0, hy0 - hh * 2.2)])
    # forecastle mast
    cv.obj([], 0)
    cv.line([(bx - L * .05, ys - hh * 1.25), (bx - L * .05, ys - hh * 2.4)])
    # accommodation block aft, bridge wings, funnel
    ax0, ax1 = sx + L * .035, sx + L * .17
    tiers = 4
    th = hh * .62
    for k in range(tiers):
        inset = L * .006 * k
        blk = _rect(ax0 + inset, hy0 - th * (k + 1), ax1 - ax0 - inset * 2, th)
        cv.obj([blk], .5)
        cv.hair(C.hatch_poly(blk, 90, 3, .5))
        # windows
        n = int((ax1 - ax0 - inset * 2) / 2.6)
        wy = hy0 - th * (k + .5)
        cv.line([[(ax0 + inset + 1.5 + j * 2.6, wy - .3), (ax0 + inset + 2.6 + j * 2.6, wy - .3)] for j in range(n)])
    wing = _rect(ax0 - L * .02, hy0 - th * tiers - 1.6, ax1 - ax0 + L * .04, 1.6)
    cv.obj([wing], .5)
    fx = ax0 + (ax1 - ax0) * .22
    fun = [(fx, hy0 - th * tiers - 1.6), (fx + L * .05, hy0 - th * tiers - 1.6), (fx + L * .045, hy0 - th * tiers - hh * 1.6),
           (fx + L * .003, hy0 - th * tiers - hh * 1.6)]
    cv.obj([fun], .5)
    cv.hair(C.hatch_poly(fun, 90, 1.5))
    band = [(fx + L * .003, hy0 - th * tiers - hh * 1.6), (fx + L * .045, hy0 - th * tiers - hh * 1.6),
            (fx + L * .046, hy0 - th * tiers - hh * 1.25), (fx + L * .002, hy0 - th * tiers - hh * 1.25)]
    cv.heavy(C.hatch_poly(band, 0, 1.2))
    if not compact:
        # radar mast, and a thread of smoke trailing aft
        mx = ax0 + (ax1 - ax0) * .7
        cv.obj([], 0)
        cv.line([(mx, hy0 - th * tiers - 1.6), (mx, hy0 - th * tiers - hh * 2.1)])
        cv.hair([(mx - 2, hy0 - th * tiers - hh * 1.8), (mx + 2, hy0 - th * tiers - hh * 1.8)])
    cv.obj([foam], 0)
    cv.hair([[(bx - L * .06 + i * 1.5, ys + .8 + i * .5), (bx + L * .04 - i * .8, ys + .8 + i * .9)] for i in range(3)])


def _pile(cv, gx, top, wl, pw, ft, level, compact):
    x0 = gx - pw / 2
    # ripples ringing the pile
    rp = []
    for i in range(3):
        rx, ry = pw * (.9 + .55 * i), 1.2 + .8 * i
        rp.append([(gx + rx * math.cos(a), wl + 1 + i * .6 + ry * math.sin(a)) for a in [math.pi * k / 18 for k in range(19)]])
    cv.obj([], 0)
    cv.hair(rp)
    pile = [(x0, top + pw * .15), (x0 + pw, top + pw * .15), (x0 + pw, wl), (x0, wl)]
    cv.obj([pile], 1)
    # cylinder: dense on the shadow side, wood grain
    for k in range(9):
        u = (k + .5) / 9
        xx = x0 + pw * u
        if u > .6:
            cv.hair([(xx, top + pw * .2), (xx, wl)])
        else:
            pts = [(xx + .35 * math.sin((yy - top) / 5 + k), yy) for yy in [top + pw * .2 + j * 3 for j in range(int((wl - top) / 3))]]
            cv.hair(_split(pts, random.Random(k), (8, 30), (1.5, 3)))
    cv.line([(x0 + pw * .82, top + pw * .2), (x0 + pw * .82, wl)])
    # the tide's wet band: the river rises and falls a foot or two with each tide
    wet = _rect(x0, wl - ft * 1.6, pw, ft * 1.6)
    cv.hair(C.hatch_poly(wet, 35, 1.5))
    # weathered top
    cap = [(gx + pw / 2 * math.cos(a), top + pw * .15 + pw * .16 * math.sin(a)) for a in [TAU * k / 24 for k in range(24)]]
    cv.obj([cap], 1)
    cv.hair([[(gx + pw / 2 * r * math.cos(a), top + pw * .15 + pw * .16 * r * math.sin(a)) for a in [TAU * k / 20 for k in range(21)]]
             for r in (.35, .7)])
    # the staff gauge: enamel plate, foot marks, tenths in E blocks, foot numerals
    bw = pw * .78
    bx = gx - bw / 2 - pw * .05
    btop = top + ft * .55
    plate = _rect(bx, btop, bw, wl - btop)
    cv.obj([plate], 1)
    f_top = level + (wl - btop) / ft
    f = math.floor(level * 5) / 5 + .2
    while f < f_top - .05:
        yy = wl - (f - level) * ft
        whole = abs(f - round(f)) < 1e-6
        half = abs(f * 2 - round(f * 2)) < 1e-6
        step = .2 if ft > 14 else .5
        if not whole and not (half and step == .5) and abs(f / step - round(f / step)) > 1e-6:
            f += .2
            continue
        if whole:
            cv.heavy([(bx, yy), (bx + bw, yy)])
            if ft > 14 and yy - ft * .38 > btop + 1:
                cv.line(_digit(str(int(round(f)) % 10), bx + bw * .55, yy - ft * .4, ft * .3))
        elif half:
            cv.heavy([(bx, yy), (bx + bw * .45, yy)])
            cv.line([(bx + .6, yy), (bx + .6, yy + ft * .2)])
        else:
            cv.line([(bx, yy), (bx + bw * .3, yy)])
        f += .2
    # the needle of today: a heavier waterline hugging the pile
    cv.obj([], 0)
    cv.heavy([(x0 - pw * .5, wl), (x0 + pw * 1.5, wl)])


def _heron(cv, fx, fy, hgt):
    """A great blue heron standing on the pile, facing left; feet at (fx, fy)."""
    s = hgt
    P = lambda pts: [(fx + x * s, fy + y * s) for x, y in pts]
    legs = [P([(.03, -.36), (.0, -.12), (-.02, 0)]), P([(.07, -.36), (.08, -.14), (.06, 0)])]
    cv.obj([], 0)
    cv.line(legs)
    cv.hair([P([(-.02, 0), (-.08, .005)]), P([(.06, 0), (.12, .004)])])
    body = P([(-.11, -.52), (-.04, -.6), (.06, -.61), (.17, -.55), (.27, -.46), (.36, -.37), (.3, -.36), (.18, -.37),
              (.08, -.35), (-.02, -.37), (-.1, -.43), (-.13, -.48)])
    cv.obj([body], 1)
    wing = P([(-.04, -.56), (.06, -.6), (.17, -.55), (.27, -.46), (.35, -.375), (.2, -.39), (.06, -.42), (-.02, -.46)])
    cv.hair(C.hatch_poly(body, -28, 1.5))
    cv.hair(C.hatch_poly(wing, 30, 3))
    cv.hair([P([(.0, -.5), (.18, -.43)]), P([(.04, -.55), (.24, -.44)])])
    # breast plumes
    cv.hair([P([(-.1 + .02 * i, -.44 + .01 * i), (-.06 + .02 * i, -.36)]) for i in range(4)])
    # neck: S curve, white with a streaked front
    spine = P([(-.08, -.52), (-.15, -.6), (-.13, -.7), (-.06, -.78), (-.07, -.86), (-.1, -.9)])
    wdt = .045 * s
    l, r = [], []
    for i, (x, y) in enumerate(spine):
        a, b = spine[max(0, i - 1)], spine[min(len(spine) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        k = 1.25 if i == 0 else 1.
        l.append((x + nx * wdt * k, y + ny * wdt * k))
        r.append((x - nx * wdt * k, y - ny * wdt * k))
    neck = l + r[::-1]
    cv.obj([neck], 1)
    cv.line([r[1:-1]])
    cv.hair([[(x + (rr[0] - x) * .45, y + (rr[1] - y) * .45), (x + (rr[0] - x) * .8, y + (rr[1] - y) * .8)]
             for (x, y), rr in zip(l[1:-1], r[1:-1])])
    head = [(fx + (-.1 + .055 * math.cos(a)) * s, fy + (-.915 + .035 * math.sin(a)) * s) for a in [TAU * k / 16 for k in range(16)]]
    cv.obj([head], 1)
    cv.heavy([P([(-.08, -.94), (.05, -.935)]), P([(-.02, -.935), (.13, -.9)])])   # black crest and plume
    beak = P([(-.15, -.925), (-.38, -.9), (-.15, -.9)])
    cv.obj([beak], 1)
    cv.hair([P([(-.15, -.912), (-.36, -.901)])])
    e = P([(-.115, -.918)])[0]
    cv.heavy([[(e[0] - .4, e[1]), (e[0] + .4, e[1])]])


def _bank(cv, X0, Y1, W, H, seed, compact):
    rng = random.Random(seed + 21)
    bh = H * (.16 if not compact else .14)
    bank = [(X0 - 2, Y1 + 2), (X0 - 2, Y1 - bh)]
    for i in range(1, 21):
        t = i / 20
        bank.append((X0 + W * .34 * t, Y1 - bh * (1 - t ** 1.6) - rng.uniform(0, 1.5)))
    bank.append((X0 + W * .34, Y1 + 2))
    cv.obj([bank], 1)
    cv.hair(C.hatch_poly(bank, 45, 1.5))
    cv.hair(C.hatch_poly(bank, -45, 3))
    # reeds and cattails rising off the bank, blades arching and folding over
    n = 26 if not compact else 12
    for i in range(n):
        t = (i + rng.uniform(0, .8)) / n
        x = X0 + W * .32 * t
        base = Y1 - bh * (1 - (t * .9) ** 1.6) + 2
        hgt = H * rng.uniform(.14, .3) * (1 - t * .45)
        bend = rng.uniform(-.5, .6)
        tip_droop = rng.random() < .35
        pts = []
        for k in range(13):
            u = k / 12
            dx = bend * hgt * .5 * u ** 2
            dy = -hgt * u
            if tip_droop and u > .7:
                dy = -hgt * .7 - hgt * .3 * math.sin((u - .7) / .3 * math.pi / 2) * .4
                dx += bend * hgt * .6 * (u - .7) + math.copysign(hgt * .25 * (u - .7), bend)
            pts.append((x + dx, base + dy))
        w = max(.9, H * .007) * (1.6 if i % 4 == 0 else 1)
        poly = [(px - w * (1 - k / 12), py) for k, (px, py) in enumerate(pts)] + \
               [(px + w * (1 - k / 12) + .2, py) for k, (px, py) in enumerate(pts)][::-1]
        cv.obj([poly], .5)
        cv.hair([pts[:10]])
        if i % 5 == 2 and not tip_droop:
            hx, hy = pts[8]
            ch = hgt * .2
            cat = [(hx - 1.7 + j % 2 * 3.4, hy - ch * (j // 2)) for j in (0, 1, 3, 2)]
            cat = [(hx - 1.2, hy), (hx + 1.2, hy), (hx + 1.3, hy - ch), (hx, hy - ch - 1.2), (hx - 1.3, hy - ch)]
            cv.obj([cat], 1)
            cv.heavy(C.hatch_poly(cat, 0, 1.5))
            cv.obj([], 0)
            cv.line([(hx, hy - ch - 1.5), (hx + bend, hy - ch - hgt * .12)])



# ---------------------------------------------------------------- engraved roman capitals (stroke paths)
def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


_CAP = {
    "A": (1.1, [[(0, 2), (.55, 0), (1.1, 2)], [(.22, 1.3), (.88, 1.3)]]),
    "B": (.9, [[(0, 0), (0, 2)], [(0, 0), (.55, 0)] + _arc(.55, .48, .32, .48, -90, 90, 8) + [(0, .96)],
               [(0, .96), (.55, .96)] + _arc(.55, 1.48, .36, .52, -90, 90, 8) + [(0, 2)]]),
    "C": (1., [_arc(.62, 1, .6, 1, -50, -310, 16)]),
    "E": (.8, [[(.8, 0), (0, 0), (0, 2), (.8, 2)], [(0, 1), (.6, 1)]]),
    "F": (.8, [[(.8, 0), (0, 0), (0, 2)], [(0, 1), (.6, 1)]]),
    "G": (1.05, [_arc(.6, 1, .6, 1, -50, -340, 16) + [(1.08, 1.1), (.65, 1.1)]]),
    "H": (1., [[(0, 0), (0, 2)], [(1, 0), (1, 2)], [(0, 1), (1, 1)]]),
    "I": (.1, [[(.05, 0), (.05, 2)]]),
    "L": (.75, [[(0, 0), (0, 2), (.75, 2)]]),
    "M": (1.3, [[(0, 2), (.08, 0), (.65, 2), (1.22, 0), (1.3, 2)]]),
    "N": (1., [[(0, 2), (0, 0), (1, 2), (1, 0)]]),
    "O": (1.2, [_arc(.6, 1, .6, 1, 0, 360, 20)]),
    "R": (.9, [[(0, 2), (0, 0), (.5, 0)] + _arc(.5, .5, .35, .5, -90, 90, 8) + [(0, 1)], [(.4, 1), (.95, 2)]]),
    "S": (.85, [_arc(.43, .5, .4, .5, -20, -270, 10) + _arc(.43, 1.5, .42, .5, -90, 160, 10)]),
    "T": (.9, [[(0, 0), (.9, 0)], [(.45, 0), (.45, 2)]]),
    "U": (1., [[(0, 0), (0, 1.45)] + _arc(.5, 1.45, .5, .55, 180, 0, 10)[1:] + [(1, 0)]]),
    "V": (1.05, [[(0, 0), (.52, 2), (1.05, 0)]]),
    "W": (1.5, [[(0, 0), (.38, 2), (.75, .4), (1.12, 2), (1.5, 0)]]),
    ".": (.2, [[(.1, 1.85), (.1, 1.95)]]),
    "\u00b7": (.2, [[(.1, .95), (.1, 1.05)]]),
}


def _letter_run(text, cx, cy, hgt, track=.42, path=None):
    """Polylines for text centred at (cx, cy), cap height hgt; optional centre line path to follow."""
    s = hgt / 2
    glyphs = []
    width = 0.
    for ch in text:
        if ch == " ":
            width += .7 * s
            glyphs.append(None)
            continue
        if ch.isdigit():
            gw, strokes = .85, _DIG[ch]
        else:
            gw, strokes = _CAP.get(ch, (.6, []))
        glyphs.append((width, gw, strokes))
        width += (gw + track) * s
    width -= track * s
    out = []
    for g in glyphs:
        if not g:
            continue
        x0, gw, strokes = g
        for st in strokes:
            pl = []
            for px, py in st:
                X = cx - width / 2 + x0 + px * s * (.85 if gw == .85 else 1)
                Y = cy - hgt / 2 + py * s
                if path:
                    Y += _path_y(path, X) - cy
                pl.append((X, Y))
            out.append(pl)
    return out, width


def _path_y(path, x):
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
    return path[0][1] if x < path[0][0] else path[-1][1]


def _tall_extras(w, h, level, rising):
    """Letter the house banner and engrave today's reading into the pedestal tablet."""
    ped_h = min(max(h * .17, 48), 86.)
    top_free = min(h * .055, 26.)
    py0 = top_free
    ph = h - top_free - ped_h + ped_h * .3
    pw = w - 12
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    bh = min(16, ph * .05)
    _, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, 0)
    cv = C.Canvas()
    cv.obj([], 0)
    letters, _ = _letter_run("THE COLUMBIA", cx, cy + ch * .47, bh * .52, .5, centre)
    cv.heavy(letters)
    _, (tx, ty, tw, th) = C.pedestal(0, h - ped_h, w, ped_h, 0)
    # the tablet: ruled ground, the reading cut in heavy capitals, a running wave either side
    tab = [(tx + 2, ty + 2), (tx + tw - .8, ty + 2), (tx + tw - .8, ty + th - .8), (tx + 2, ty + th - .8)]
    cv.obj([tab], 0)
    txt = ("VANCOUVER  %s FT  %s" % (("%.1f" % level), "RISING" if rising else "FALLING"))
    lh = min(th * .5, 9)
    letters, lw = _letter_run(txt, tx + tw / 2, ty + th / 2 + .6, lh, .5)
    cv.hair([[(x0, y), (x1, y)] for y in [ty + 3.5 + 2 * k for k in range(int((th - 4) / 2))]
             for x0, x1 in ((tx + 3, tx + tw / 2 - lw / 2 - 4), (tx + tw / 2 + lw / 2 + 4, tx + tw - 2))])
    knock = [(tx + tw / 2 - lw / 2 - 3, ty + 2.5), (tx + tw / 2 + lw / 2 + 3, ty + 2.5),
             (tx + tw / 2 + lw / 2 + 3, ty + th - 1.5), (tx + tw / 2 - lw / 2 - 3, ty + th - 1.5)]
    cv.obj([knock], .5)
    cv.heavy(letters)
    # running-dog waves on the ruled ends
    for side in (-1, 1):
        x_a = tx + 6 if side < 0 else tx + tw / 2 + lw / 2 + 7
        x_b = tx + tw / 2 - lw / 2 - 7 if side < 0 else tx + tw - 5
        P = th * 1.3
        n = int((x_b - x_a) / P)
        if n < 1:
            continue
        x_a += ((x_b - x_a) - n * P) / 2
        yb = ty + th - 3
        r0 = th * .28
        pl = []
        for i in range(n):
            ox = x_a + i * P
            ccx, ccy = ox + P * .55, ty + th * .48
            pl += [(ox + P * .05 * k / 6, yb - (yb - ccy) * (k / 6) ** 2 * 0) for k in range(1)]
            pl += [(ox + (ccx - r0 - ox) * k / 6, yb + (ccy - yb) * math.sin(k / 6 * math.pi / 2)) for k in range(7)]
            for k in range(25):
                a = math.pi + 1.4 * TAU * k / 24
                r = r0 * (1 - .7 * k / 24)
                pl.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
            spiral_end = pl[-1]
            cv.obj([], 0)
            cv.heavy([pl[-25:]])
            pl = [(ccx + r0 * .2, yb)]
        cv.line([[(x_a, yb), (x_a + n * P, yb)]])
    return cv.svg()

# ---------------------------------------------------------------- field recovery + plate
def _field_from_box(ix, iy, iw, ih, kind):
    cx, cy = ix + iw / 2, iy + ih / 2
    if kind == "band":
        rx, ry = iw / 2 / .7071 + 5, ih / 2 / .7071 + 5
        a, b = rx - 4.6, ry - 4.6
        pts = [(cx + a * math.cos(t), cy + b * math.sin(t)) for t in [TAU * k / 96 for k in range(96)]]
    else:
        a, b = (iw / 2) / _K + 6 - 4.8, (ih / 2) / _K + 6 - 4.8
        pts = C._superellipse(cx, cy, a, b)
    return cx, cy, a, b, pts



def st_johns(cv, x0, x1, deck, th):
    """the St. Johns Bridge far off: two gothic towers th tall, the cables in catenary, the deck"""
    span = x1 - x0
    t1, t2 = x0 + span * .25, x0 + span * .75
    top = deck - th
    cab = []
    for i in range(41):
        u = i / 40
        xx = x0 + span * u
        if xx < t1:
            yy = deck - (xx - x0) / (t1 - x0) * th * .95
        elif xx > t2:
            yy = deck - (x1 - xx) / (x1 - t2) * th * .95
        else:
            v = (xx - t1) / (t2 - t1)
            yy = top + th * .05 + th * .78 * (1 - (2 * v - 1) ** 2)
        cab.append((xx, yy))
    cv.obj([], 0)
    cv.line(cab)
    for xx, yy in cab[1:-1:2]:
        cv.hair([(xx, yy), (xx, deck)])
    cv.line([(x0 - span * .05, deck), (x1 + span * .05, deck)])
    for tx in (t1, t2):
        tw = max(1.6, th * .14)
        tw_ = [(tx - tw, deck + th * .35), (tx + tw, deck + th * .35), (tx + tw * .7, top + th * .1), (tx, top - th * .06),
               (tx - tw * .7, top + th * .1)]
        cv.obj([tw_], .5)
        cv.hair([(tx, top + th * .12), (tx, deck - th * .4)])
        cv.hair([(tx - tw * .5, deck - th * .55), (tx, deck - th * .75), (tx + tw * .5, deck - th * .55)])


def river_band(x, y, W, H, seed, ship=True):
    """the headpiece: a banner of the Columbia off Sauvie Island; swells in swelling burin lines, the
    Washington shore of firs, the St. Johns Bridge far upstream, and a bulk carrier at the moorings
    when one is in"""
    rng = random.Random(seed)
    cv = C.Canvas()
    cv.obj([_rect(x - 2, y - 2, W + 4, H + 4)], 0)
    hy = y + H * .38
    # sky: dawn streaks in broken strokes, closing up toward the zenith
    yy = y
    while yy < hy:
        t = (yy - y) / max(1., hy - y)
        xx = x - 2 + rng.uniform(0, 5)
        while xx < x + W:
            L = rng.uniform(8, 30)
            cv.hair([(xx, yy), (xx + L, yy)])
            xx += L + rng.uniform(1.5, 3.5 + 8 * t)
        yy += 1.5 if t < .4 else 2.
    st_johns(cv, x + W * .74, x + W * .97, hy - H * .03, H * .26)
    # the Washington shore
    shore = [(x - 2, hy + 1)]
    xx = x - 2
    while xx < x + W + 2:
        th = H * rng.uniform(.06, .14)
        wv = th * .4
        shore += [(xx, hy - 1), (xx + wv, hy - 1 - th), (xx + 2 * wv, hy - 1)]
        xx += 2 * wv * rng.uniform(.6, 1.)
    shore += [(x + W + 2, hy + 1)]
    cv.obj([shore], .5)
    cv.hair(C.hatch_poly(shore, 90, 1.5))
    cv.hair(_keep_disc(C.hatch_poly(shore, 20, 2.), x + W * .3, hy, W * .4))
    # the river: rows of swell, the crests cut heavier as they come forward
    water = _rect(x - 2, hy, W + 4, y + H - hy + 3)
    cv.obj([water], 0)
    L = min(W * .42, H * 2.2)
    sx = x + W * .14
    ys = hy + H * .22
    hh = max(3., L * .08)
    yy = hy + 1
    while yy < y + H + 2:
        t = (yy - hy) / max(1., y + H - hy)
        row = _wave_row(x - 2, x + W + 2, yy, .3 + 1.2 * t, 12 + 26 * t, rng.uniform(0, TAU))
        segs = _split(row, rng, (8 + 26 * (1 - t), 24 + 40 * (1 - t)), (1.2, 2. + 2 * t))
        (cv.line if t > .5 else cv.hair)(segs)
        yy += 1.5 if t < .3 else 2.
    if ship:
        # moored: the dolphins she lies to, hawsers out fore and aft
        for fx in (-.04, 1.06):
            px = sx + L * fx
            for k in (-1, 0, 1):
                pile = _rect(px + k * 1.6 - .7, ys - hh * 1.6 + abs(k) * .8, 1.4, hh * 1.9)
                cv.obj([pile], .5)
                cv.hair(C.hatch_poly(pile, 90, 1.5))
        cv.hair([(sx + L * .01, ys - hh * .9), (sx - L * .04, ys - hh * 1.3)])
        cv.hair([(sx + L * .99, ys - hh * 1.1), (sx + L * 1.06, ys - hh * 1.3)])
        _ship(cv, sx, ys, L, hh, False)
    else:
        for fx in (.2, .5):
            px = sx + L * fx
            for k in (-1, 0, 1):
                pile = _rect(px + k * 1.6 - .7, ys - hh * 1.6 + abs(k) * .8, 1.4, hh * 1.9)
                cv.obj([pile], .5)
                cv.hair(C.hatch_poly(pile, 90, 1.5))
        gx, gy, r = sx + L * .5, ys - hh * 2.4, hh * .9
        cv.line([(gx - r, gy + r * .1), (gx - r * .45, gy - r * .45), (gx, gy + r * .15), (gx + r * .45, gy - r * .45), (gx + r, gy + r * .1)])
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 17 * int(ctx.get("sheet", 0) or 0)
    level = _level(ctx)
    smp = (ctx.get("sample", "") or "")
    ship = not re.search(r"no ship", smp, re.I)

    def sc(x, y, sw, sh, mode):
        if mode in ("band", "egg"):
            return river_band(x, y, sw, sh, seed, ship)
        cv = C.Canvas()
        _scene(cv, x, y, sw, sh, level, seed, False)
        return cv.svg()

    def egg(cv, x, y, s):
        # Parker's heron, fishing from the scroll
        fig_heron(cv, x, y + s * .45, s)

    return compose(w, h, sc, seed, medal="banner" if h < 110 else "lunette", egg=egg,
                   banner=lambda centre, rh: motto(centre, "THE COLUMBIA", rh), mw_frac=.74)
