"""Civics plate (section front): the Oregon State Capitol (marble drum, the gilded Pioneer on top)
under a glory of burin rays over modelled cloud and stratus, the Stars and Stripes on a mown mall, a
county ballot drop box with a ballot going in, marked with an X of crossed drumsticks (Parker's
Easter egg); Mount Hood hides in the scroll as a second egg.
King-tier frame: the scene in a beaded portrait medallion, fine scroll grown from one stem over a
punched matte, gold-line borders and beading; at the tall size an arched panel with the ribbon
lettered WE THE PEOPLE and a predella carrying the dedication cartouche with Parker's arms
(Somaster, from solar/arms.py)."""
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

    def svg(self, tol_w=.5, tol_l=.5):
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
            + __import__("re").sub(r"(\d\.\d)\d+", r"\1", _AR.arms(w, s, seed)) + "</svg>")


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
    o.append(clip(f"gmF{seed % 997}{int(h)}", fd, scene(min(fx), min(fy), max(fx) - min(fx), max(fy) - min(fy), mode)))
    o.extend(top)
    return _C.svg_doc(w, h, "".join(o))


# ==== GM ENGINE END ====


_n, _d, PI, TAU = C._n, C._d, C.PI, C.TAU
hatch = C.hatch_poly


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circ(cx, cy, r, n=28, bump=0., k=9, ph=0.):
    return [(cx + r * (1 + bump * math.sin(k * t + ph)) * math.cos(t),
             cy + r * (1 + bump * math.sin(k * t + ph)) * math.sin(t))
            for t in [TAU * i / n for i in range(n)]]


def hz(poly, pitch=2.):
    """horizontal hatch on the device grid"""
    return hatch(poly, 0, pitch, .25)


def vt(poly, pitch=2.):
    return hatch(poly, 90, pitch, .25)


def solid(cv, poly, outline=1.):
    cv.obj([poly], outline)
    cv.line(hatch(poly, 0, .8))


def _seg_circle(a, b, cx, cy, r):
    dx, dy = b[0] - a[0], b[1] - a[1]
    fx, fy = a[0] - cx, a[1] - cy
    A = dx * dx + dy * dy
    B = 2 * (fx * dx + fy * dy)
    Cc = fx * fx + fy * fy - r * r
    disc = B * B - 4 * A * Cc
    if A < 1e-9 or disc <= 0:
        return None
    s = math.sqrt(disc)
    return (-B - s) / (2 * A), (-B + s) / (2 * A), dx, dy


def _cut(segs, cx, cy, r):
    """remove the parts of 2-point segments inside circle (cx, cy, r)"""
    out = []
    for (a, b) in segs:
        q = _seg_circle(a, b, cx, cy, r)
        if q is None:
            out.append([a, b])
            continue
        t0, t1, dx, dy = q
        if t0 > 0:
            t = min(1, t0)
            out.append([a, (a[0] + dx * t, a[1] + dy * t)])
        if t1 < 1:
            t = max(0, t1)
            out.append([(a[0] + dx * t, a[1] + dy * t), b])
    return [p for p in out if math.hypot(p[1][0] - p[0][0], p[1][1] - p[0][1]) > .6]


def _keep_in(segs, cx, cy, r):
    """keep only the parts of segments inside circle"""
    out = []
    for (a, b) in segs:
        q = _seg_circle(a, b, cx, cy, r)
        if q is None:
            continue
        t0, t1, dx, dy = q
        t0, t1 = max(0, t0), min(1, t1)
        if t1 - t0 > 1e-3:
            out.append([(a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)])
    return out


# ----------------------------------------------------------------------------------------------
# stroke lettering (roman capitals as paths; no <text>)
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_G = {
    "A": (.72, [[(0, 1), (.36, 0), (.72, 1)], [(.15, .64), (.57, .64)]]),
    "B": (.6, [[(0, 0), (0, 1), (.38, 1)] + _arc(.38, .76, .22, .24, 90, -90, 6) + [(0, .52)],
               [(0, 0), (.33, 0)] + _arc(.33, .26, .2, .26, -90, 90, 6)[1:] + [(0, .52)]]),
    "C": (.66, [_arc(.36, .5, .34, .5, -45, -315, 12)]),
    "D": (.68, [[(0, 0), (0, 1), (.3, 1)] + _arc(.3, .5, .36, .5, 90, -90, 10) + [(0, 0)]]),
    "E": (.56, [[(.54, 0), (0, 0), (0, 1), (.54, 1)], [(0, .5), (.42, .5)]]),
    "F": (.54, [[(.54, 0), (0, 0), (0, 1)], [(0, .5), (.42, .5)]]),
    "G": (.7, [_arc(.36, .5, .34, .5, -45, -315, 12) + [(.7, .58), (.42, .58)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    "I": (.08, [[(.04, 0), (.04, 1)]]),
    "J": (.46, [[(.44, 0), (.44, .74)] + _arc(.22, .74, .22, .26, 0, 180, 6)[1:]]),
    "K": (.62, [[(0, 0), (0, 1)], [(.6, 0), (0, .6)], [(.2, .45), (.62, 1)]]),
    "L": (.52, [[(0, 0), (0, 1), (.52, 1)]]),
    "M": (.84, [[(0, 1), (0, 0), (.42, .8), (.84, 0), (.84, 1)]]),
    "N": (.68, [[(0, 1), (0, 0), (.68, 1), (.68, 0)]]),
    "O": (.76, [_arc(.38, .5, .38, .5, 0, 360, 16)]),
    "P": (.58, [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)]]),
    "Q": (.76, [_arc(.38, .5, .38, .5, 0, 360, 16), [(.45, .7), (.78, 1.04)]]),
    "R": (.62, [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .27, .26, .27, -90, 90, 6)[1:] + [(0, .54)],
                [(.28, .54), (.62, 1)]]),
    "S": (.56, [_arc(.28, .25, .26, .25, -20, -270, 7) + _arc(.28, .75, .28, .25, -90, 160, 7)[1:]]),
    "T": (.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "U": (.66, [[(0, 0), (0, .66)] + _arc(.33, .66, .33, .34, 180, 0, 8)[1:] + [(.66, 0)]]),
    "V": (.7, [[(0, 0), (.35, 1), (.7, 0)]]),
    "W": (.96, [[(0, 0), (.24, 1), (.48, .2), (.72, 1), (.96, 0)]]),
    "X": (.64, [[(0, 0), (.64, 1)], [(.64, 0), (0, 1)]]),
    "Y": (.66, [[(0, 0), (.33, .5), (.66, 0)], [(.33, .5), (.33, 1)]]),
    "Z": (.6, [[(0, 0), (.6, 0), (0, 1), (.6, 1)]]),
    "0": (.54, [_arc(.27, .5, .27, .5, 0, 360, 14)]),
    "1": (.36, [[(.04, .2), (.26, 0), (.26, 1)], [(.04, 1), (.48, 1)]]),
    "2": (.54, [_arc(.27, .27, .26, .27, -170, 10, 6) + [(0, 1), (.54, 1)]]),
    "3": (.52, [_arc(.25, .25, .25, .25, -160, 90, 6), _arc(.25, .74, .27, .26, -90, 160, 6)]),
    "4": (.58, [[(.42, 1), (.42, 0), (0, .7), (.58, .7)]]),
    "5": (.54, [[(.5, 0), (.08, 0), (.04, .44)] + _arc(.26, .7, .28, .3, -120, 150, 8)]),
    "6": (.56, [[(.46, .02), (.2, .2), (.02, .65)] + _arc(.28, .7, .26, .3, 180, 540, 12)]),
    "7": (.54, [[(0, 0), (.54, 0), (.2, 1)]]),
    "8": (.54, [_arc(.27, .25, .22, .25, 90, 450, 10), _arc(.27, .74, .27, .26, -90, 270, 12)]),
    "9": (.56, [_arc(.28, .3, .26, .3, 0, 360, 12) + [(.54, .35), (.36, .8), (.1, .98)]]),
    "-": (.4, [[(.04, .55), (.36, .55)]]),
    ".": (.2, [[(.1, .92), (.1, .96)]]),
    "·": (.36, [[(.18, .4), (.26, .51), (.18, .62), (.1, .51), (.18, .4), (.18, .62)]]),
}


def text_width(s, cap):
    return sum((_G.get(ch, (.5, []))[0] + .32) * cap if ch != " " else .5 * cap for ch in s) - .32 * cap


def _along(P, s, off):
    acc = 0.
    for i in range(1, len(P)):
        L = math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1])
        if acc + L >= s or i == len(P) - 1:
            t = (s - acc) / L if L else 0
            x = P[i - 1][0] + (P[i][0] - P[i - 1][0]) * t
            y = P[i - 1][1] + (P[i][1] - P[i - 1][1]) * t
            nx, ny = -(P[i][1] - P[i - 1][1]) / L, (P[i][0] - P[i - 1][0]) / L
            return (x + nx * off, y + ny * off)
        acc += L
    return P[-1]


def _plen(P):
    return sum(math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]) for i in range(1, len(P)))


def letter(s, x, y, cap, path_pts=None):
    """Polylines for string s, cap height `cap`, from x with the cap top at y. path_pts: a centre
    polyline; x is then arc length along it and y the offset across it."""
    out = []
    cur = x
    for ch in s.upper():
        if ch == " ":
            cur += .5 * cap
            continue
        gw, strokes = _G.get(ch, _G["·"])
        for st in strokes:
            pts = [(cur + px * cap, y + py * cap) for px, py in st]
            if path_pts:
                pts = [_along(path_pts, px, py) for px, py in pts]
            out.append(pts)
        cur += (gw + .32) * cap
    return out


def serif_lines(lines, cap):
    out = []
    k = cap * .14
    for pl in lines:
        for a, b in ((pl[0], pl[1]), (pl[-1], pl[-2])):
            if abs(a[0] - b[0]) < .25 * abs(a[1] - b[1]):
                out.append([(a[0] - k, a[1]), (a[0] + k, a[1])])
    return out


def lettering_svg(lines, w=1.):
    d = "".join(_d(p, tol=.05) for p in lines)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w)}"/>'


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def tree(cv, cx, cy, r, seed):
    rng = random.Random(seed)
    blobs = []
    for i in range(5):
        a = rng.uniform(0, TAU)
        d = r * rng.uniform(.15, .45)
        blobs.append((cx + d * math.cos(a), cy + d * math.sin(a) * .8, r * rng.uniform(.5, .66)))
    blobs.sort(key=lambda b: b[1])
    tr = rect(cx - r * .08, cy, cx + r * .08, cy + r * 1.1)
    cv.obj([tr], 1.)
    cv.hair(vt(tr, 1.5))
    for bx, by, br in blobs:
        poly = circ(bx, by, br, 30, .07, 11, rng.uniform(0, 6))
        cv.obj([poly], 1.)
        cv.hair(_cut(hatch(poly, 45, 3., 0), bx - br * .35, by - br * .35, br * .45))
        cv.hair(_cut(hatch(poly, 45, 3., 1.5), bx - br * .25, by - br * .25, br * .95))
        cv.hair(_cut(hatch(poly, -45, 3., .75), bx - br * .15, by - br * .15, br * .98))
        for j in range(7):
            t = PI + .3 + j * .35
            px, py = bx + br * .78 * math.cos(t), by + br * .78 * math.sin(t)
            cv.hair([(px, py), (px + br * .14 * math.cos(t + 1.9), py + br * .14 * math.sin(t + 1.9))])


def capitol(cv, cx, G, S, detail):
    """Oregon State Capitol on ground line G, wing span S."""
    wh = .13 * S
    for side in (-1, 1):
        x0, x1 = (cx - S / 2, cx - .16 * S) if side < 0 else (cx + .16 * S, cx + S / 2)
        face = rect(x0, G - wh, x1, G)
        cv.obj([face], 1.)
        cv.hair(hz(face, 3.))
        if side > 0:
            ret = rect(x1 - .03 * S, G - wh, x1, G)
            cv.obj([ret], 1.)
            cv.hair(hz(ret, 1.5))
        n = max(3, int((x1 - x0) / (S * .035)))
        for row in (.3, .68):
            for i in range(n):
                wx = x0 + (x1 - x0) * (i + .5) / n
                if side > 0 and wx > x1 - .035 * S:
                    continue
                cv.heavy([(wx, G - wh * (row + .14)), (wx, G - wh * (row - .14))])
        cv.line([(x0, G - wh + 1.2), (x1, G - wh + 1.2)])
    bw, bh = .36 * S, .27 * S
    bx0, bx1, by0 = cx - bw / 2, cx + bw / 2, G - bh
    blk = rect(bx0, by0, bx1, G)
    cv.obj([blk], 1.)
    cv.hair(hz(rect(bx0, by0, bx1, by0 + bh * .14), 1.5))
    rec = rect(cx - bw * .3, by0 + bh * .18, cx + bw * .3, G)
    cv.obj([rec], 1.)
    cv.hair(vt(rec, 1.5))
    if detail:
        cv.hair(hz(rec, 3.))
    for i in range(5):
        px = cx - bw * .3 + bw * .6 * (i + .5) / 5
        cv.obj([rect(px - .8, by0 + bh * .18, px + .8, G)], .5)
    pl = rect(bx0, by0 + bh * .14, cx - bw * .3, G)
    pr = rect(cx + bw * .3, by0 + bh * .14, bx1, G)
    cv.obj([pl], 1.)
    cv.hair(vt(pl, 3.))
    cv.obj([pr], 1.)
    cv.hair(vt(pr, 1.5))
    cv.heavy([(bx0 - 1, by0), (bx1 + 1, by0)])
    r = .085 * S
    dh = .2 * S
    dy0, dy1 = by0 - dh, by0 - S * .025
    base = rect(cx - r * 1.35, dy1, cx + r * 1.35, by0)
    cv.obj([base], 1.)
    cv.hair(hz(base, 3.))
    cv.hair(_keep_in(hz(base, 1.5), cx + r * 2.6, by0, r * 2))
    drum = rect(cx - r, dy0, cx + r, dy1)
    cv.obj([drum], 1.)
    nf = 22 if detail else 12
    for i in range(1, nf):
        th = -PI / 2 + PI * i / nf
        fx = cx + r * math.sin(th)
        (cv.line if math.sin(th) > .35 else cv.hair)([(fx, dy0 + 2), (fx, dy1)])
    cv.hair(hz(rect(cx + r * .45, dy0, cx + r, dy1), 2.))
    ring = rect(cx - r * 1.1, dy0 - S * .018, cx + r * 1.1, dy0 + 1)
    cv.obj([ring], 1.)
    cv.hair(_keep_in(hz(ring, 1.5), cx + r * 1.7, dy0, r * 1.2))
    lan = rect(cx - r * .55, dy0 - S * .05, cx + r * .55, dy0 - S * .018)
    cv.obj([lan], 1.)
    cv.hair(vt(lan, 2.))
    cv.obj([rect(cx - r * .22, dy0 - S * .065, cx + r * .22, dy0 - S * .05)], 1.)
    # the gilded Pioneer: axe on his shoulder, cloak
    u = S * .0019
    top = dy0 - S * .065
    fig = [(-6, 0), (-5, -14), (-7, -30), (-6, -46), (-9, -60), (-6, -76), (0, -82), (6, -76), (9, -60),
           (8, -46), (6, -30), (5, -14), (7, 0), (2, 0), (1, -28), (-1, -28), (-2, 0)]
    solid(cv, [(cx + px * u * 1.2, top + py * u) for px, py in fig], .5)
    solid(cv, circ(cx, top - 88 * u, 6.5 * u, 12), .5)
    cv.line([(cx - 4 * u, top - 66 * u), (cx - 20 * u, top - 104 * u)])
    solid(cv, [(cx - 20 * u, top - 104 * u), (cx - 27 * u, top - 99 * u), (cx - 22 * u, top - 93 * u)], .5)
    # steps
    sw = bw * .7
    for k in range(4 if detail else 2):
        yy = G + k * S * .012
        st = rect(cx - sw / 2 - k * S * .02, yy, cx + sw / 2 + k * S * .02, yy + S * .012)
        cv.obj([st], .5)
        if k % 2:
            cv.hair(hz(st, 3.))
    # the two marble pylon sculptures
    for side in (-1, 1):
        sx = cx + side * (sw / 2 + S * .04)
        blkp = rect(sx - S * .03, G - S * .055, sx + S * .03, G + S * .02)
        cv.obj([blkp], 1.)
        cv.hair(hatch(blkp, 45 if side > 0 else 90, 2. if side > 0 else 3., .25))
        cv.obj([rect(sx - S * .034, G - S * .062, sx + S * .034, G - S * .055)], 1.)


def flag(cv, x, y, fw, fh, phase=0.):
    pole_h = fh * 4.2
    cv.obj([rect(x - .7, y, x + .7, y + pole_h)], .5)
    cv.obj([circ(x, y - .6, 1.6, 8)], .5)

    def P(u, v):
        return (x + 1 + u * fw, y + 2 + v * fh + fh * .09 * math.sin(u * 5.2 + phase) * u)
    N = 14
    cv.obj([[P(i / N, 0) for i in range(N + 1)] + [P(1 - i / N, 1) for i in range(N + 1)]], 1.)
    for s in range(0, 7, 2):
        for q in (.25, .7):
            v = (s + q) / 7 + .02
            u0 = .42 if s < 4 else 0
            cv.line([P(u0 + (1 - u0) * i / N, v) for i in range(N + 1)])
    can = [P(i / 6 * .42, 0) for i in range(7)] + [P(.42 - i / 6 * .42, 4 / 7) for i in range(7)]
    cv.obj([can], .5)
    cv.hair(hatch(can, 45, 1.5))
    cv.hair(hatch(can, -45, 3.))


def drop_box(cv, x, y, s, egg=True):
    """county ballot drop box standing at (x, y), height s; a ballot half posted, its X made of
    crossed drumsticks."""
    w = s * .62
    for lg in (rect(x - w * .38, y - s * .1, x - w * .3, y), rect(x + w * .3, y - s * .1, x + w * .38, y)):
        solid(cv, lg, .5)
    body = rect(x - w / 2, y - s * .92, x + w / 2, y - s * .1)
    cv.obj([body], 1.)
    cv.hair(hatch(body, 45, 2.))
    cv.hair(_keep_in(hatch(body, -45, 3.), x + w, y - s * .5, w * .9))
    lid = [(x - w / 2 - 1.5, y - s * .92), (x + w / 2 + 1.5, y - s * .92), (x + w / 2 - 1, y - s), (x - w / 2 + 1, y - s)]
    cv.obj([lid], 1.)
    cv.hair(hz(lid, 1.5))
    pc = rect(x - w * .3, y - s * .6, x + w * .3, y - s * .3)
    cv.obj([pc], .5)
    for k in range(3):
        yy = y - s * .55 + k * s * .09
        cv.hair([(x - w * .22, yy), (x + w * .22, yy)])
    solid(cv, rect(x - w * .34, y - s * .84, x + w * .34, y - s * .78), .5)
    if egg:
        a = math.radians(-8)
        bw_, bh_ = w * .62, s * .5
        ox, oy = x - w * .02, y - s * .81

        def R(px, py):
            return (ox + px * math.cos(a) - py * math.sin(a), oy + px * math.sin(a) + py * math.cos(a))
        cv.obj([[R(-bw_ / 2, 0), R(bw_ / 2, 0), R(bw_ / 2, -bh_), R(-bw_ / 2, -bh_)]], 1.)
        cv.hair([R(-bw_ * .38, -bh_ * .82), R(bw_ * .38, -bh_ * .82)])
        cv.hair([R(-bw_ * .38, -bh_ * .7), R(bw_ * .1, -bh_ * .7)])
        for sx in (-1, 1):
            p0 = R(-bw_ * .05 - sx * bw_ * .3, -bh_ * .1)
            p1 = R(-bw_ * .05 + sx * bw_ * .22, -bh_ * .58)
            cv.line([p0, p1])
            solid(cv, circ(p1[0], p1[1], .9, 6), .5)


def heron(cx_, by, k, f, seed=0):
    """A great blue heron's neck rising out of the acanthus like a scroll stem, ending in the head:
    black crest plumes, eye, dagger bill; streaked throat in bulino. f = -1 faces left, +1 right.
    Base at (cx_, by); k = scale (1 ~ 60 px tall)."""
    cv = C.Canvas()

    def bez(p0, p1, p2, p3, n=24):
        out = []
        for i in range(n + 1):
            t = i / n
            a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
            out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
        return out
    P = lambda x, y: (cx_ + f * x * k, by + y * k)
    pts = bez(P(0, 0), P(26, -6), P(-6, -40), P(14, -56))
    n = len(pts)
    wl = [k * (7.5 - 4.2 * i / (n - 1)) for i in range(n)]
    R = C._Rib(pts, wl, wl)
    cv.obj([R.outline()], 1.)
    side = 1 if f > 0 else -1     # the throat (front) edge
    cv.hair(C._fill_lines(R, -side * .98, side * .2, 2., 0., 1., 4))
    cv.hair(C._fill_lines(R, side * .35, side * .98, 3., 0., 1., 2))
    C._shadow(cv, R, -side, k * 2.2, .05, .9)
    # streaked throat: short bulino flecks down the front of the neck
    for i in range(2, n - 2):
        a = R.at(i / (n - 1), side * .7)
        b = R.at((i + 1.6) / (n - 1), side * .3)
        (cv.line if i % 2 else cv.hair)([a, b])
    # head
    hx, hy = P(17, -58)
    head = [(hx + 6.2 * k * math.cos(t), hy + 4.4 * k * math.sin(t)) for t in [TAU * i / 20 for i in range(20)]]
    # bill
    bill = [P(19, -61), P(42, -55), P(19, -55.5)]
    cv.obj([bill], 1.)
    cv.hair([P(21, -58), P(40, -55.3)])
    cv.obj([head], 1.)
    cv.hair(_keep_in(hatch(head, 0, 1.5, .25), hx - f * 4 * k, hy + 5 * k, 5 * k))
    # black crown stripe and the trailing plumes
    crown = [P(10, -60), P(16, -63.2), P(22, -61.5), P(16, -60.5)]
    solid(cv, crown, .5)
    for dy, L in ((0, 16), (2, 13)):
        cv.heavy(bez(P(12, -61 + dy), P(4, -62 + dy), P(-2, -64 + dy), P(-2 - L * .3, -68 + dy * .5), 8))
    # eye
    ex, ey = P(19.5, -59.5)
    cv.obj([circ(ex, ey, 1.3 * k, 8)], .5)
    cv.line(hatch(circ(ex, ey, .8 * k, 6), 0, .8))
    # one finger of acanthus wrapping the base of the neck, so it grows from the leafwork
    C.acanthus_frond(*P(0, 4), -90 + f * 60, 26 * k, 3, 34, seed=seed, cv=cv)
    return cv.svg()


def scene(x, y, W, H, clip_d, seed, detail=True, uid="cv"):
    """everything inside the cartouche field (bbox x, y, W, H; clipped to clip_d)"""
    cv = C.Canvas()
    cx = x + W / 2
    G = y + H * (.7 if detail else .76)
    S = min(W * .9, (G - y - H * .07) / .74)
    # sky: a glory of rays from behind the drum, alternate wedges ruled
    sky = rect(x - 2, y - 2, x + W + 2, G + 1)
    cv.obj([sky], 0)
    gx, gy = cx, G - .4 * S
    nr = 40 if detail else 24
    R = max(W, H) * 1.6
    for i in range(nr):
        a0 = PI * i / nr - .01 - PI
        a1 = PI * (i + 1) / nr + .01 - PI
        aa = (a0 + a1) / 2
        rr0 = S * .16
        if i % 2:
            # a lit ray: burin lines fanning out of the glory, swelling as they leave the drum
            for f in (.28, .5, .72):
                at = a0 + (a1 - a0) * f
                cv.hair([(gx + rr0 * 1.3 * math.cos(at), gy + rr0 * 1.3 * math.sin(at)),
                         (gx + R * math.cos(at), gy + R * math.sin(at))])
        else:
            cv.line([(gx + rr0 * math.cos(aa), gy + rr0 * math.sin(aa)), (gx + R * math.cos(aa), gy + R * math.sin(aa))])
    # a band of cloud low on the horizon, lit from above
    rng_ = random.Random(seed)
    for k in range(5):
        ccx = x + W * (k + .5) / 5 + rng_.uniform(-6, 6)
        ccy = gy - S * .02 + rng_.uniform(-3, 3)
        cw_, ch_ = W * .14, S * .045
        cl = [(ccx + cw_ * math.cos(t) * (1 + .15 * math.sin(5 * t)), ccy - ch_ * abs(math.sin(t)) ** .7 * (1 + .25 * math.sin(7 * t + k)))
              for t in [PI * j / 18 for j in range(19)]]
        cv.obj([cl], .5)
        # the puff modelled in contour lines that echo its crown, closing up toward the shaded base
        for q in (.25, .45, .62, .76, .88):
            cv.hair([(ccx + (px_ - ccx) * (1 - .35 * q), ccy - (ccy - py_) * (1 - q)) for px_, py_ in cl[2:-2]])
    # stratus wisps between the cloud band and the far range: tapering strokes broken into drifts
    rw_ = random.Random(seed + 11)
    yy_ = gy - S * .01
    while yy_ < gy + S * .09:
        xx_ = x + rw_.uniform(-4, 4)
        while xx_ < x + W:
            L_ = rw_.uniform(10, 30)
            cv.hair([(xx_, yy_), (xx_ + L_ * .5, yy_ - .4), (xx_ + L_, yy_)])
            xx_ += L_ + rw_.uniform(2, 6)
        yy_ += 2.5
    # the far Cascades on the horizon under the glory, then the West Hills in fir
    far = [(x - 2, G + 1)] + [(x - 2 + (W + 4) * i / 40,
                               gy + S * .02 + S * .05 * abs(math.sin(i * .9 + seed % 5)) * (1 - .5 * math.sin(i * .37)))
                              for i in range(41)] + [(x + W + 2, G + 1)]
    cv.obj([far], .5)
    # the distant range: ridges and gullies cut in short slanting strokes, thinning with distance
    rr_ = random.Random(seed + 3)
    yy_ = gy + S * .07
    while yy_ < G - 2:
        xx_ = x + rr_.uniform(0, 4)
        while xx_ < x + W:
            L_ = rr_.uniform(2.5, 5.)
            cv.hair([(xx_, yy_), (xx_ + L_ * .7, yy_ + L_ * .35)])
            xx_ += rr_.uniform(5, 9)
        yy_ += 3.
    hills = [(x - 2, G + 1)] + [(x - 2 + (W + 4) * i / 30,
                                 G - H * (.06 + .025 * math.sin(i * .7 + seed % 7) + .015 * math.sin(i * 1.9)))
                                for i in range(31)] + [(x + W + 2, G + 1)]
    cv.obj([hills], .5)
    for i in range(int(W / 3.2)):
        fx_ = x + i * 3.2 + (i * 7 % 3) * .5
        top_ = G - H * (.06 + .025 * math.sin((fx_ - x + 2) / (W + 4) * 30 * .7 + seed % 7)) + 1.5
        ht_ = 3.5 + (i * 5 % 4)
        cv.hair([(fx_ - ht_ * .3, top_ + ht_), (fx_, top_), (fx_ + ht_ * .3, top_ + ht_)])
    cv.hair(hatch(hills, 45, 3.))
    # the mall
    lawn = rect(x - 2, G, x + W + 2, y + H + 2)
    cv.obj([lawn], 0)
    # mown stripes receding to the Capitol steps, and grass flicked in along each stripe's edge
    vx_, vy_ = cx, G - S * .3
    for j in range(-14, 15):
        bx_ = cx + j * W * .09
        t0 = (G - vy_) / (y + H + 2 - vy_)
        cv.hair([(vx_ + (bx_ - vx_) * t0, G), (bx_, y + H + 2)])
    yy = G + 2
    k = 0
    while yy < y + H:
        f = (yy - G) / max(1., H * .3)
        step = 2. + 2.5 * f
        xx = x + (k % 2) * step * .5
        while xx < x + W:
            cv.hair([(xx, yy), (xx + .6 + f, yy - 1.2 - f * 1.5)])
            xx += step * 2.2
        yy += step
        k += 1
    walk = [(cx - S * .13, G), (cx + S * .13, G), (cx + W * .33, y + H + 2), (cx - W * .33, y + H + 2)]
    cv.obj([walk], .5)
    cv.hair(hz(walk, 3.))
    for k in (-1, 1):
        for f in (.3, .65):
            cv.hair([(cx + k * S * .13 * f, G), (cx + k * W * .33 * f, y + H + 2)])
    if detail:
        flag(cv, cx - S * .33, G - S * .36, S * .15, S * .085, seed % 5)
    capitol(cv, cx, G, S, detail)
    tr = S * .1
    for side in (-1, 1):
        for k, (fx, fy, sc) in enumerate(((.62, .0, 1.), (.78, .08, 1.3), (.92, .2, 1.7))):
            if not detail and k == 0:
                continue
            tree(cv, cx + side * W * fx * .5, G + H * fy - tr * sc * .3, tr * sc, seed * 7 + k * 3 + side)
    if S * .2 >= 13:
        drop_box(cv, cx + W * .27, min(y + H * .95, G + (y + H - G) * .8), max(S * .2, 16))
    cid = C._uid("civ", uid, x, y, W, H)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ----------------------------------------------------------------------------------------------
# layouts (the house layouts, adapted: the field engraved whole, banner and tablet lettered)
# ----------------------------------------------------------------------------------------------

def _districts(ctx):
    head = ((ctx or {}).get("sample", "") or "").split("|")[0]
    parts = []
    for pat, fmt in ((r"District (\d+)", "OR-{}"), (r"Senate (\d+)", "SEN {}"), (r"House (\d+)", "HSE {}")):
        m = re.search(pat, head)
        if m:
            parts.append(fmt.format(m.group(1)))
    return " · ".join(parts) if parts else "VOX POPULI"


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 17

    def sc(x, y, sw, sh, mode):
        d = f"M{_n(x)},{_n(y)}h{_n(sw)}v{_n(sh)}h{_n(-sw)}z"
        return scene(x, y, sw, sh, d, seed, mode != "band", mode)

    def banner(centre, rh):
        cap = rh * .5
        txt = "WE THE PEOPLE"
        L = _plen(centre)
        return lettering_svg(letter(txt, (L - text_width(txt, cap)) / 2, -cap / 2, cap, centre), 1.)

    def extras(g):
        out = []
        if g["mode"] == "tall":
            hk = min(g["mh"] / 150., 1.6)
            for side in (-1, 1):
                bx = g["cx"] + side * (g["mw"] / 2 + 6)
                by = g["cy"] + g["mh"] * .18
                pts = [(-6, 8), (24, 8), (22, -20), (8, -38), (20, -50), (44, -52), (44, -60), (24, -68),
                       (4, -66), (-6, -52), (-4, -36), (6, -20)]
                box = [(bx + side * u * hk, by + v * hk) for u, v in pts]
                out.append((box, heron(bx, by, hk, side, seed + side)))
        return out

    def egg(cv, x, y, s):
        fig_mthood(cv, x, y + s * .35, s * 1.3, s * .8)

    return compose(w, h, sc, seed, medal="oval", egg=egg, arms=True, banner=banner)
