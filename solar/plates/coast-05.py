"""coast-05 Coast happenings, merged into Shellfish check (edition plan: tailpiece, about 8%).

The tailpiece is a ribbon cartouche of wet sand at the tide line: the last wave's lace of foam, ripple
marks lit on the crest and hatched on the lee, shell bits, a Pacific razor clam with its siphon out,
and a Dungeness crab holding Parker's crossed drumsticks up in its claws (the plan's Easter egg).
King-tier frame: beaded cushion medallion, fine scroll from one stem on a punched matte, gold-line
borders; a heron hides in the scroll. Taller sizes set the crab and clam on the strand in front of
Haystack Rock at Cannon Beach under a CANNON BEACH ribbon."""
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


CR = ' shape-rendering="crispEdges"'


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dpl(pts, close=False):
    if len(pts) < 2:
        return ""
    o = "M" + f(pts[0][0]) + "," + f(pts[0][1])
    px, py = pts[0]
    for x, y in pts[1:]:
        o += "l" + f(x - px) + "," + f(y - py)
        px, py = x, y
    return o + ("z" if close else "")


def pip(x, y, poly):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def runs(y, x0, x1, test, step=.5, minlen=.8):
    """Horizontal runs at row y where test(x) holds."""
    out = []
    a = None
    x = x0
    while x <= x1:
        ok = test(x)
        if ok and a is None:
            a = x
        elif not ok and a is not None:
            if x - a >= minlen:
                out.append((a, x))
            a = None
        x += step
    if a is not None and x1 - a >= minlen:
        out.append((a, x1))
    return out


def hpath(segs):
    return "".join(f"M{f(a)},{f(y)}h{f(b - a)}" for y, a, b in segs)


def P(d, w=.5, crisp=False, fill="none"):
    if not d:
        return ""
    return f'<path d="{d}" fill="{fill}" stroke="#000" stroke-width="{f(w)}"{CR if crisp else ""}/>'


def F(d, fill="#fff", rule=""):
    if not d:
        return ""
    r = f' fill-rule="{rule}"' if rule else ""
    return f'<path d="{d}" fill="{fill}" stroke="none"{r}/>'


def row05(y):
    return math.floor(y * 2) / 2 + .25


def row1(y):
    return round(y * 2) / 2


# ------------------------------------------------------------------------------------------
# the vignette: Haystack Rock at Cannon Beach
# ------------------------------------------------------------------------------------------

HAY = [(0, 0), (.02, .2), (.045, .45), (.07, .66), (.1, .8), (.14, .89), (.2, .95), (.28, .99), (.36, 1.0),
       (.44, .985), (.5, .96), (.55, .93), (.6, .88), (.64, .8), (.67, .72), (.71, .66), (.76, .62), (.8, .58),
       (.84, .5), (.88, .38), (.92, .25), (.96, .12), (1, 0)]


def ext_at(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    if len(xs) < 2:
        return None
    return min(xs), max(xs)


def engrave_rock(poly, by, top, rng, fine=1.):
    """Basalt carved as facets: the rock is cut into a jittered grid of planes in its own (u, t)
    coordinates; each plane is hatched by its tone (lit from the left, darkening to the right),
    seams are cut in 1 px and the shadow-side rim in 1.5 px. Returns (white_fill_d, svg)."""
    H = by - top

    def at(u, t):
        t = min(t, .985)
        y = by - t * H
        e = ext_at(poly, y)
        if not e:
            return None
        l, r = e
        if 0 < u < 1:
            u = min(.99, max(.01, u + .06 * math.sin(t * 5.5 + u * 9)))
        return (l + u * (r - l), y)
    ncol = max(3, int(7 * fine))
    us = [0.] + sorted(rng.uniform(.1, .9) for _ in range(ncol - 1)) + [1.]
    half, one, seams = [], [], []
    for i in range(len(us) - 1):
        nrow = rng.randint(2, 4)
        ts = [0.] + sorted(rng.uniform(.12, .85) for _ in range(nrow - 1)) + [1.]
        for j in range(len(ts) - 1):
            u0, u1, t0, t1 = us[i], us[i + 1], ts[j], ts[j + 1]
            ed = []
            for k in range(7):
                ed.append(at(u0 + (u1 - u0) * k / 6, t0))
            for k in range(7):
                ed.append(at(u1, t0 + (t1 - t0) * k / 6))
            for k in range(7):
                ed.append(at(u1 - (u1 - u0) * k / 6, t1))
            for k in range(7):
                ed.append(at(u0, t1 - (t1 - t0) * k / 6))
            ed = [q for q in ed if q]
            if len(ed) < 4:
                continue
            um = (u0 + u1) / 2
            tone = um * 3.2 + rng.uniform(-.7, .7) + (.4 if t0 < .1 else 0)
            if tone < .8:
                half += C.hatch_poly(ed, 60, 3, rng.uniform(0, 3))
                half += C.hatch_poly(ed, 0, 3, rng.uniform(0, 3))
            elif tone < 1.6:
                half += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
            elif tone < 2.4:
                one += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
            else:
                one += C.hatch_poly(ed, 60, 2, rng.uniform(0, 2))
                half += C.hatch_poly(ed, -30, 3, rng.uniform(0, 3))
            if t1 < 1:
                seams.append([q for q in (at(u0 + (u1 - u0) * k / 6, t1) for k in range(7)) if q])
        seams.append([q for q in (at(us[i + 1], k / 12 * .97) for k in range(13)) if q])
    o = [P("".join(dpl(p) for p in half), .5), P("".join(dpl(p) for p in one), 1),
         P("".join(dpl(p) for p in seams if p and len(p) > 1), 1)]
    n = len(poly)
    peak = min(range(n), key=lambda i: poly[i][1])
    o.append(P(dpl(poly[peak:]), 1.5))
    o.append(P(dpl(poly[:peak + 1]), 1))
    return dpl(poly, True), "".join(o)


def heron(x, y, s, flip=False):
    """A great blue heron standing at (x, y) = feet, s = height: body tilted, S-neck, dagger bill,
    black crest plume, dark wing coverts in bulino."""
    sx = -1 if flip else 1

    def T(px, py):
        return (x + sx * px * s, y - py * s)
    out = [(-.36, .32), (-.28, .41), (-.12, .53), (.04, .6), (.13, .63), (.15, .7), (.1, .78), (.09, .86),
           (.13, .92), (.2, .95), (.25, .955), (.46, .925), (.25, .92), (.21, .9), (.17, .86), (.17, .8),
           (.22, .72), (.23, .63), (.2, .54), (.13, .45), (0, .4), (-.18, .36)]
    sil = [T(*q) for q in out]
    o = [F(dpl(sil, True)), P(dpl(sil, True), 1)]
    # wing: closed, dark, feathered in bulino
    wing = [T(-.34, .33), T(-.2, .44), T(0, .54), T(.12, .58), T(.12, .5), T(0, .44), T(-.2, .37)]
    o.append(F(dpl(wing, True), C.pat("M")) + P(dpl(wing, True), 1))
    fl = [[T(.1 - k * .06, .52 - k * .03), T(-.25 - k * .02, .37 - k * .005)] for k in range(4)]
    o.append(P("".join(dpl(p) for p in fl), .5))
    # neck streaks and breast plumes
    o.append(P(dpl([T(.155, .62), T(.13, .72), T(.12, .8)]) + dpl([T(.16, .52), T(.1, .44)]) + dpl([T(.12, .5), T(.06, .43)]), .5))
    o.append(F(dpl([T(.15, .935), T(-.02, .95), T(.15, .92)], True), "#000"))
    o.append(P(dpl([T(.25, .938), T(.46, .925)]), .5))
    eye = T(.2, .935)
    o.append(F(f"M{f(eye[0] - .7)},{f(eye[1])}a.7,.7 0 1,0 1.4,0a.7,.7 0 1,0 -1.4,0z", "#000"))
    legs = [[T(.02, .42), T(.01, .2), T(0, 0)], [T(.07, .43), T(.08, .21), T(.1, 0)],
            [T(-.06, 0), T(.05, 0)], [T(.05, 0), T(.17, 0)]]
    o.append(P("".join(dpl(p) for p in legs), 1))
    return "".join(o)


def paw(x, y, s, ang):
    """One dog paw print (pad + four toes) as closed paths, centred (x, y)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def T(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    o = ""
    for (px, py, rx, ry) in [(0, .35, .55, .42), (-.55, -.3, .2, .27), (-.2, -.62, .2, .27), (.2, -.62, .2, .27), (.55, -.3, .2, .27)]:
        o += dpl([T(px + rx * math.cos(t * math.pi / 6), py + ry * math.sin(t * math.pi / 6)) for t in range(12)], True)
    return o


def vignette(x0, y0, W, H, clip_d, cid, seed=0, mode="tall"):
    """Fill the whole box (clipped to clip_d) with the Cannon Beach scene."""
    rng = random.Random(seed * 31 + 7)
    o = []
    x1, y1 = x0 + W, y0 + H
    band = mode == "band"
    hz = y0 + H * (.6 if band else .56)
    shore = y0 + H * (1.1 if band else .74)
    sx, sy, sr = x0 + W * .22, hz - H * .015, H * (.13 if band else .1)
    rbw = W * (.3 if band else .36)
    rbh = min(H * (.5 if band else .42), (hz - y0) * .82, rbw * .72)
    rbx = x0 + W * (.46 if band else .42)
    rock = [(rbx + u * rbw, hz + 1.5 - t * rbh) for u, t in
            [(u + rng.uniform(-.006, .006) * (0 < u < 1), t * rng.uniform(.98, 1.02) if 0 < t < 1 else t) for u, t in HAY]]
    needles = []
    nx = rbx + rbw * 1.08
    for (dx, wv, hv) in ((0, .09, .34), (.13, .06, .22), (.23, .045, .12)):
        bx = nx + rbw * dx
        bw_, bh_ = rbw * wv, rbh * hv
        needles.append([(bx, hz + 1), (bx + bw_ * .15, hz - bh_ * .6), (bx + bw_ * .38, hz - bh_), (bx + bw_ * .6, hz - bh_ * .92),
                        (bx + bw_ * .8, hz - bh_ * .45), (bx + bw_, hz + 1)])
    head = [(x0 - 2, hz + .5), (x0 - 2, hz - H * .15)]
    for i in range(1, 25):
        t = i / 24
        head.append((x0 - 2 + W * .3 * t, hz - H * .15 * (1 - t ** 1.6) - (math.sin(i * 2.3) * .9 + .9) * (1 - t)))
    head.append((x0 + W * .3, hz + .5))
    head = [(x0 + x1 - hx_, hy_) for hx_, hy_ in head]  # Tillamook Head lies north: right

    # ---- sky: ruled at pitch 2, doubled to pitch 1 in the deep upper sky; light cloud banks
    #      (pitch 3) with scalloped rims; rays of the sun thin the lines out to pitch 4.
    rays = 18

    def in_ray(x, y):
        a = math.atan2(y - sy, x - sx)
        return (int((a + math.pi) / (2 * math.pi) * rays * 2) % 2) == 0

    clouds = []
    for i in range(3):
        cx_ = x0 + W * (.12 + .33 * i + rng.uniform(-.05, .05))
        cy_ = y0 + (hz - y0) * rng.uniform(.3, .5)
        cw_ = W * rng.uniform(.18, .26)
        ch_ = (hz - y0) * rng.uniform(.07, .1)
        top_ = [(cx_ - cw_ / 2 + cw_ * t, cy_ - ch_ * (math.sin(math.pi * t) ** .7) * (.7 + .3 * abs(math.sin(t * math.pi * 4 + i))))
                for t in [k / 24 for k in range(25)]]
        bot_ = [(cx_ + cw_ / 2 - cw_ * t, cy_ + ch_ * .25 * math.sin(math.pi * t)) for t in [k / 12 for k in range(1, 12)]]
        clouds.append(top_ + bot_)
    sky = []
    y = row05(y0) - .5
    k = 0
    deep = y0 + (hz - y0) * .2
    while y < hz:
        incl = [c for c in clouds if min(q[1] for q in c) - 1 < y < max(q[1] for q in c) + 1]

        def tst(x, y=y, k=k):
            if (x - sx) ** 2 + (y - sy) ** 2 < (sr * 1.25) ** 2:
                return False
            if pip(x, y, head):
                return False
            for c in incl:
                if pip(x, y, c):
                    return k % 3 == 0
            if k % 2 == 1 and in_ray(x, y) and math.hypot(x - sx, y - sy) < W * .55:
                return False
            return True
        for a, b in runs(y, x0 - 1, x1 + 1, tst):
            sky.append((y, a, b))
        if y < deep:
            yy = y + 1
            frac = max(0., (yy - y0) / (deep - y0) - .55) / .45

            def t2(x, yy=yy):
                if (x - sx) ** 2 + (yy - sy) ** 2 < (sr * 2.2) ** 2:
                    return False
                for c in incl:
                    if pip(x, yy, c):
                        return False
                return True
            for a, b in runs(yy, x0 - 1, x1 + 1, t2):
                # break the doubled rule into dashes as it fades toward the horizon
                x = a
                while x < b:
                    L = rng.uniform(4, 30) * (1 - frac * .7)
                    if b - x > 1.5:
                        sky.append((yy, x, min(b, x + L)))
                    x += L + rng.uniform(1, 2 + 10 * frac)
        y += 2
        k += 1
    o.append(P(hpath(sky), .5, True))
    o.append(P(''.join(dpl(c[:25]) for c in clouds), .5))
    sun = []
    y = row05(sy - sr)
    while y < hz:
        dd = sr * sr - (y - sy) ** 2
        if dd > 0:
            hw = math.sqrt(dd)
            sun.append((y, sx - hw, sx + hw))
        y += 3
    o.append(P(hpath(sun), .5, True))
    o.append(P(dpl([(sx + sr * math.cos(t), sy + sr * math.sin(t)) for t in [math.pi + math.pi * i / 30 for i in range(31)]]), 1))
    # headland: a forested dark mass, 1 px rules at pitch 2
    hd = []
    y = row1(hz - H * .2)
    while y < hz:
        for a, b in runs(y, x1 - W * .32, x1 + 2, lambda x, y=y: pip(x, y, head)):
            hd.append((y, a, b))
        y += 2
    o.append(P(hpath(hd), 1, True))
    o.append(P(dpl(head[1:-1]), 1))
    trees = []
    for i in range(2, 22, 2):
        px, py = head[i]
        trees.append([(px - 1, py + .5), (px, py - 2.2), (px + 1, py + .5)])
    o.append(P("".join(dpl(p) for p in trees), .5))
    # ---- sea
    sea_half, sea_one = [], []
    y = row05(hz) + .5
    while y < shore:
        d = (y - hz) / max(1, shore - hz)
        pitch = 1.5 if d < .35 else 2
        x = x0 - 1
        while x < x1 + 1:
            L = rng.uniform(3, 10 + 25 * d)
            gap = rng.uniform(.8, 2.2 + 1.5 * d)
            if abs(x - sx) < sr * (1 - d * .3):
                L *= .4
                gap *= 2.2
            seg = (y, x, min(x + L, x1 + 1))
            refl = rbx + rbw * .05 < x < rbx + rbw * .9 and d < .5
            (sea_one if (refl and rng.random() < .8) or rng.random() < .07 else sea_half).append(seg)
            x += L + gap
        y += pitch
    sea_one = [(row1(yy), a, b) for yy, a, b in sea_one]
    o.append(P(hpath(sea_half), .5, True))
    o.append(P(hpath(sea_one), 1, True))
    o.append(P(f"M{f(x0 - 1)},{f(row1(hz))}h{f(W + 2)}", 1, True))
    # ---- rocks
    for nd in needles:
        dn, sv = engrave_rock(nd, hz + 1, min(p[1] for p in nd), rng, fine=.3)
        o.append(F(dn) + sv)
    rd, rs = engrave_rock(rock, hz + 1.5, min(p[1] for p in rock), rng)
    o.append(F(rd) + rs)
    tick = []
    for i in range(7):
        px = rbx + rbw * (.28 + i * .04)
        topy = min((p[1] for p in rock if abs(p[0] - px) < rbw * .05), default=hz)
        tick.append(f"M{f(px)},{f(topy - .3)}v-1.6")
    o.append(P("".join(tick), 1))
    fx0, fx1 = rbx - rbw * .08, nx + rbw * .3
    foam = [(fx0, hz + 1.5)]
    n = 30
    for i in range(n + 1):
        t = i / n
        foam.append((fx0 + (fx1 - fx0) * t, hz + 2.5 + math.sin(t * math.pi) * 2.5 + (math.sin(i * 1.9) * .8)))
    for i in range(n, -1, -1):
        foam.append((fx0 + (fx1 - fx0) * i / n, hz + 1.5))
    o.append(F(dpl(foam, True)))
    curls = []
    for i in range(int((fx1 - fx0) / 5)):
        cx_ = fx0 + 3 + i * 5 + rng.uniform(-1, 1)
        cy_ = hz + 3 + rng.uniform(-.5, .8)
        curls.append([(cx_ - 2, cy_ + .8), (cx_ - .5, cy_ - .6), (cx_ + 1, cy_ - .2), (cx_ + .6, cy_ + .6)])
    o.append(P("".join(dpl(p) for p in curls), .5))
    if not band:
        stx, sty = rbx + rbw * .42, y0 + (hz - rbh - y0) * .45 + H * .02
        sr2 = H * .035
        star = []
        for i in range(16):
            a = -math.pi / 2 + i * math.pi / 8
            rr = sr2 * (1 if i % 4 == 0 else (.45 if i % 2 == 0 else .25))
            star.append((stx + rr * math.cos(a), sty + rr * math.sin(a)))
        R = sr2 * 1.3
        o.append(F(f"M{f(stx - R)},{f(sty)}a{f(R)},{f(R)} 0 1,0 {f(2 * R)},0a{f(R)},{f(R)} 0 1,0 {f(-2 * R)},0z"))
        o.append(F(dpl(star, True)) + P(dpl(star, True), .5))
        o.append(F(f"M{f(stx - .8)},{f(sty)}a.8,.8 0 1,0 1.6,0a.8,.8 0 1,0 -1.6,0z", "#000"))
    gulls = []
    for i in range(4 if band else 7):
        gx = x0 + W * rng.uniform(.08, .95)
        gy = y0 + (hz - y0) * rng.uniform(.12, .7)
        if math.hypot(gx - sx, gy - sy) < sr * 1.6 or (rbx - 4 < gx < rbx + rbw + 4 and gy > hz - rbh - 4):
            continue
        s = rng.uniform(2.2, 3.6) * (H / 140 if not band else .7)
        s = max(2., min(4.5, s))
        gulls.append([(gx - s, gy - s * .2), (gx - s * .45, gy - s * .55), (gx, gy), (gx + s * .45, gy - s * .55), (gx + s, gy - s * .2)])
    if gulls:
        o.append(P("".join(dpl(g) for g in gulls), 1))
    if not band:
        wet = []
        y = row05(shore)
        while y < y1 + 1:
            x = x0 - 1
            while x < x1 + 1:
                L = rng.uniform(10, 40)
                wet.append((y, x, x + L))
                x += L + rng.uniform(1.5, 4)
            y += 2
        edge = [(x0 - 2, shore - 2)]
        for i in range(41):
            t = i / 40
            edge.append((x0 - 2 + (W + 4) * t, shore + 1.5 + math.sin(t * 19 + seed) * 1.6 + math.sin(t * 7) * 1.2))
        edge.append((x1 + 2, shore - 2))
        dry_top = [(x0 + W * t, shore + H * .07 + math.sin(t * 5.2 + 1) * H * .03 + t * H * .04) for t in [i / 30 for i in range(31)]]
        dry = [(x0 - 2, dry_top[0][1])] + dry_top + [(x1 + 2, dry_top[-1][1]), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]
        o.append(F(f"M{f(x0 - 2)},{f(shore - 2)}H{f(x1 + 2)}V{f(y1 + 2)}H{f(x0 - 2)}z"))
        o.append(P(hpath(wet), .5, True))
        o.append(F(dpl(edge, True)) + P(dpl(edge[1:-1]), .5))
        o.append(F(dpl(dry, True), C.pat("S")) + P(dpl(dry_top), 1))
        hh = H * .3
        hx, hy = x0 + W * .82, shore + H * .055
        o.append(heron(hx, hy, hh, flip=True))
        o.append(P(f"M{f(hx - 4)},{f(row05(hy + 1.5))}h9M{f(hx - 2)},{f(row05(hy + 3.5))}h5", .5, True))
        lx, ly, lw, lh = x0 + W * .04, y1 - H * .085, W * .3, H * .055
        logp = [(lx + lw * t, ly - lh * .5 + math.sin(t * 3) * lh * .12) for t in [i / 16 for i in range(17)]]
        logp += [(lx + lw * t, ly + lh * .5 + math.sin(t * 3) * lh * .12) for t in [i / 16 for i in range(16, -1, -1)]]
        o.append(F(dpl(logp, True)) + P(dpl(logp, True), 1))
        grain = []
        for j in range(1, int(lh / 1.6)):
            v = -.5 + j * 1.6 / lh
            grain.append([(lx + lw * t + 2, ly + lh * v + math.sin(t * 3) * lh * .12 + math.sin(t * 25 + j) * .35)
                          for t in [i / 30 for i in range(30)] if t < .97])
        o.append(P("".join(dpl(g) for g in grain[len(grain) // 2:]), 1))
        o.append(P("".join(dpl(g) for g in grain[:len(grain) // 2]), .5))
        ex, ey = lx + lw, ly + math.sin(3) * lh * .12
        el = lambda rx, ry: f"M{f(ex - rx)},{f(ey)}a{f(rx)},{f(ry)} 0 1,0 {f(2 * rx)},0a{f(rx)},{f(ry)} 0 1,0 {f(-2 * rx)},0z"
        o.append(F(el(lh * .22, lh * .5)) + P(el(lh * .22, lh * .5) + el(lh * .1, lh * .25), .5))
        # EASTER EGG: a dog's paw-print trail across the sand toward the heron
        pr = ""
        ps = max(2.2, H * .014)
        for i in range(9):
            t = i / 8
            px = x0 + W * (.3 + .44 * t)
            py = shore + H * (.085 - .02 * t) + (ps * 1.3 if i % 2 else -ps * 1.3)
            pr += paw(px, py, ps, math.pi / 2 - .12)
        o.append(F(pr) + P(pr, .5))
        gr = []
        for side in (0, 1):
            bx = x0 + (W * .02 if side == 0 else W * .96)
            for i in range(7):
                a = -math.pi / 2 + (i - 3) * .22
                L = H * rng.uniform(.06, .11)
                gr.append([(bx + i * 1.2, y1 + 1), (bx + i * 1.2 + math.cos(a) * L * .5 + 1, y1 + 1 + math.sin(a) * L * .55),
                           (bx + i * 1.2 + math.cos(a) * L + (i - 3) * .9, y1 + 1 + math.sin(a) * L)])
        o.append(P("".join(dpl(g) for g in gr), 1))
    body = "".join(o)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------
# drawn lettering for the ribbon
# ------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


GLYPHS = {
    "C": (.62, [_arc(.33, .5, .31, .5, -.28 * math.pi, -1.72 * math.pi, 14)]),
    "A": (.7, [[(0, 1), (.35, 0), (.7, 1)], [(.14, .64), (.56, .64)]]),
    "N": (.66, [[(0, 1), (0, 0), (.66, 1), (.66, 0)]]),
    "O": (.7, [_arc(.35, .5, .35, .5, 0, 2 * math.pi, 18)]),
    "B": (.58, [[(0, 0), (0, 1)], [(0, 0), (.36, 0)] + _arc(.36, .24, .2, .24, -math.pi / 2, math.pi / 2, 6) + [(0, .48)],
                [(0, .48), (.38, .48)] + _arc(.38, .74, .22, .26, -math.pi / 2, math.pi / 2, 6) + [(0, 1)]]),
    "E": (.56, [[(.56, 0), (0, 0), (0, 1), (.56, 1)], [(0, .5), (.44, .5)]]),
    "H": (.66, [[(0, 0), (0, 1)], [(.66, 0), (.66, 1)], [(0, .5), (.66, .5)]]),
    " ": (.45, []),
}


def letter_along(centre, text, cap):
    """Stroke the text centred along the polyline centre, caps `cap` px tall."""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.dist(centre[i - 1], centre[i]))
    tot = L[-1]
    track = .32
    widths = [GLYPHS[c][0] * cap for c in text]
    tw = sum(widths) + track * cap * (len(text) - 1)
    s = (tot - tw) / 2

    def at(sv):
        sv = max(0, min(tot - 1e-6, sv))
        for i in range(1, len(L)):
            if L[i] >= sv:
                t = (sv - L[i - 1]) / max(1e-9, L[i] - L[i - 1])
                p0, p1 = centre[i - 1], centre[i]
                a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
                return p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, a
        return centre[-1][0], centre[-1][1], 0
    out = []
    for c, wv in zip(text, widths):
        for stroke in GLYPHS[c][1]:
            pts = []
            for gx, gy in stroke:
                px, py, a = at(s + gx * cap)
                dy = (gy - .5) * cap
                pts.append((px - math.sin(a) * dy, py + math.cos(a) * dy))
            out.append(pts)
        s += wv + track * cap
    return "".join(dpl(p) for p in out)


def running_dog(tx, ty, tw, th):
    """A Vitruvian wave ('running dog') across the tablet on a light ruled ground."""
    o = [F(f"M{f(tx + 2)},{f(ty + 2)}h{f(tw - 3)}v{f(th - 3)}h{f(-(tw - 3))}z", C.pat("L"))]
    h = th - 4
    per = max(8., h * 1.7)
    n = max(1, int((tw - 6) / per))
    per = (tw - 6) / n
    base = ty + 2 + h * .92
    pts = []
    for i in range(n):
        x = tx + 3 + i * per
        r = h * .34
        cx, cy = x + per * .55, ty + 2 + h * .45
        seg = [(x, base), (x + per * .25, base - h * .1)]
        for j in range(19):
            t = j / 18
            a = math.pi * .95 - t * math.pi * 2.1
            rr = r * (1 - .62 * t)
            seg.append((cx + rr * math.cos(a) * 1.05, cy - rr * math.sin(a)))
        pts.append(seg)
    o.append(P("".join(dpl(p) for p in pts), 1))
    o.append(P(f"M{f(tx + 3)},{f(base + .5)}h{f(tw - 6)}", 1))
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts (adapted from the house frame so the vignette fills the whole carved field)
# ------------------------------------------------------------------------------------------

def _field(cx, cy, w, h, inset=4.5):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return dpl(C._superellipse(cx, cy, a - inset, b - inset), True), (cx - a, cy - b, 2 * a, 2 * b)


def _redots(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    bp = C._superellipse(cx, cy, a - 4.5, b - 4.5)
    return P(dpl(bp + [bp[0]]), 1)


def layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = [F(f"M0,0h{f(w)}v{f(h)}h{f(-w)}z", C.pat("D"))]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{f(px0 - 3.5)},{f(py0 - 3.5)}h{f(pw + 7)}v{f(ph + 7)}h{f(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{f(px0 - 1.5)},{f(py0 - 1.5)}h{f(pw + 3)}v{f(ph + 3)}h{f(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = (pw * .5, ph * .64) if h >= 400 else (pw * .56, ph * .72)
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .04), rmax=r1 * .9,
                   max_n=int(14 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    clip_d, (fx, fy, fw, fh) = _field(cx, cy, cw, ch)
    o.append(vignette(fx, fy, fw, fh, clip_d, C._uid("v", w, h, seed), seed, "tall"))
    o.append(_redots(cx, cy, cw, ch))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, max(11, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(P(letter_along(centre, "CANNON BEACH", bh * .56), 1))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(running_dog(tx, ty, tw, th))
    fy2 = py + ped_h
    fh2 = h - fy2
    if fh2 > 14:
        o.append(C.dark_ground((w * .06, fy2, w * .88, fh2 - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy2, w * .88, fh2 - 2,
                         C.scroll_band(w * .06, fy2, w * .88, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy2 + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{f(w * .06)},{f(h - 1.5)}h{f(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.7)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .07), rmax=r * .8,
                   max_n=int(14 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    clip_d, (fx, fy, fw, fh) = _field(cx, cy, cw, gh + 4)
    o.append(vignette(fx, fy, fw, fh, clip_d, C._uid("v", w, h, seed), seed, "tall"))
    o.append(_redots(cx, cy, cw, gh + 4))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.2, 150)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    ell = C._ell_pts(cx, cy, rx - 3, ry - 3, 64)
    o.append(vignette(cx - rx, cy - ry, 2 * rx, 2 * ry, dpl(ell, True), C._uid("v", w, h, seed), seed, "band"))
    o.append(f'<path d="M0,{f(h - .5)}h{f(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)



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


def razor_clam(cv, x, y, L, ang):
    """a Pacific razor clam lying on the sand, L long, its siphon end at (x, y) side"""
    ca, sa = _m.cos(ang), _m.sin(ang)
    W = L * .3

    def T(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)
    sh = []
    for i in range(25):
        t = i / 24
        sh.append(T(L * t, -W / 2 * (1 - (2 * t - 1) ** 8) ** .5 * (.92 + .08 * t)))
    for i in range(25):
        t = 1 - i / 24
        sh.append(T(L * t, W / 2 * (1 - (2 * t - 1) ** 8) ** .5 * (.92 + .08 * t)))
    # the siphon pushing out of the gape, ringed
    sip = [T(-L * .02, -W * .16), T(-L * .14, -W * .14), T(-L * .18, 0), T(-L * .14, W * .14), T(-L * .02, W * .16)]
    cv.obj([sip], .5)
    for q in (.06, .1, .14):
        cv.hair([T(-L * q, -W * .15), T(-L * q, W * .15)])
    cv.obj([sh], 1.)
    # growth lines: arcs concentric on the beak near one end, swelling to the shadowed lower edge
    for k in range(1, 12):
        r = L * k / 11
        pts = [T(L * .22 + (r * _m.cos(a)) * .95 - L * .22 * (k / 11) * 0, r * _m.sin(a) * .3) for a in
               [(-1 + 2 * j / 12) * 1.2 for j in range(13)]]
        pts = [p for p in pts if _m.hypot(p[0] - T(L / 2, 0)[0], p[1] - T(L / 2, 0)[1]) < L * .48]
        if len(pts) > 1:
            cv.hair(pts)
    # the glossy periostracum: a dark band along the lower edge, a bright stripe left along the top
    for v in (.3, .36, .42):
        cv.hair([T(L * .04, W * v), T(L * .5, W * (v + .04)), T(L * .96, W * v)])
    cv.line([T(L * .08, W * .44), T(L * .5, W * .48), T(L * .92, W * .44)])
    cv.hair([T(L * .1, -W * .18), T(L * .55, -W * .22), T(L * .9, -W * .16)])


def dungeness(cv, cx, cy, s, sticks=True):
    """a Dungeness crab from above, carapace s wide, holding Parker's crossed drumsticks up in its claws"""
    a, b = s / 2, s * .34
    # walking legs first, under the shell: four a side, jointed, the tips sharp
    for sd in (-1, 1):
        for i in range(4):
            ba = -.25 + i * .32
            bx = cx + sd * a * .78 * _m.cos(ba)
            by = cy + b * .55 * _m.sin(ba) + b * .1
            l1, l2, l3 = s * .2, s * .17, s * .12
            a1 = ba + (-.3 + i * .12)
            p1 = (bx + sd * l1 * _m.cos(a1), by + l1 * _m.sin(a1) - s * .03)
            a2 = a1 + .6 + i * .08
            p2 = (p1[0] + sd * l2 * _m.cos(a2), p1[1] + l2 * _m.sin(a2))
            a3 = a2 + .5
            p3 = (p2[0] + sd * l3 * _m.cos(a3), p2[1] + l3 * _m.sin(a3))
            R = _Rib([(bx, by), p1, p2, p3], [s * .05, s * .045, s * .035, .4], [s * .05, s * .045, s * .035, .4])
            cv.obj([R.outline()], .5)
            cv.hair(R.contour(.5, 0, .9))
            cv.hair([(p1[0] - s * .01, p1[1] - s * .03), (p1[0] + s * .01, p1[1] + s * .03)])
            cv.hair([(p2[0] - s * .012, p2[1] - s * .025), (p2[0] + s * .012, p2[1] + s * .025)])
    # the claws, reaching forward and up
    tips = []
    for sd in (-1, 1):
        sx = cx + sd * a * .55
        sy = cy - b * .6
        mer = (sx + sd * s * .2, sy - s * .14)
        car = (mer[0] + sd * s * .02, mer[1] - s * .16)
        arm = _Rib([(sx, sy), mer, car], [s * .05, s * .055, s * .05], [s * .05, s * .055, s * .05])
        cv.obj([arm.outline()], .5)
        cv.hair(arm.contour(.4, 0, .9, minw=1.))
        # the hand (propodus) swelling, then the two fingers closing on a drumstick
        hx, hy = car[0] - sd * s * .04, car[1] - s * .12
        hand = [(car[0] - s * .07, car[1] + s * .02), (car[0] + s * .07, car[1] + s * .02),
                (hx + s * .065, hy), (hx + s * .03, hy - s * .07), (hx - s * .05, hy - s * .05), (hx - s * .07, hy)]
        cv.obj([hand], 1.)
        cv.hair(_keep_disc(_C.hatch_poly(hand, 60, 1.5), hx + sd * s * .06, hy + s * .05, s * .07))
        f1 = [(hx - sd * s * .02, hy - s * .06), (hx - sd * s * .09, hy - s * .15), (hx - sd * s * .05, hy - s * .07)]
        f2 = [(hx + sd * s * .03, hy - s * .07), (hx - sd * s * .04, hy - s * .17), (hx + sd * s * .0, hy - s * .07)]
        cv.obj([f1, f2], .5)
        for k in range(3):
            cv.hair([(hx - s * .05 + k * s * .04, hy - s * .02), (hx - s * .045 + k * s * .04, hy - s * .035)])
        tips.append((hx - sd * s * .055, hy - s * .13))
    # the carapace: a broad fan, toothed along the front edge, modelled toward the shadowed rear
    car_ = []
    for i in range(61):
        t = _PI + _PI * i / 60
        tooth = (1 + .045 * abs(_m.sin(t * 9))) if _m.sin(t) < -.15 else 1.
        car_.append((cx + a * _m.cos(t) * tooth, cy + b * .9 * _m.sin(t) * tooth))
    for i in range(1, 30):
        t = _PI * i / 30
        car_.append((cx - a * _m.cos(t) * (1 - .35 * _m.sin(t) ** 2), cy + b * .75 * _m.sin(t) ** .8))
    cv.obj([car_], 1.)
    for q in (.82, .64, .46):
        ring = [(cx + (px - cx) * q, cy + (py - cy) * q - b * (1 - q) * .1) for px, py in car_]
        cv.hair(_keep_disc([ring + [ring[0]]], cx + a * .3, cy + b * .5, a * .8))
    cv.hair(_keep_disc(_C.hatch_poly(car_, 30, 1.5), cx + a * .45, cy + b * .55, a * .55))
    # the gastric and cardiac grooves: the H on the back, and granules
    cv.hair([(cx - a * .22, cy - b * .3), (cx - a * .12, cy + b * .05), (cx - a * .2, cy + b * .45)])
    cv.hair([(cx + a * .22, cy - b * .3), (cx + a * .12, cy + b * .05), (cx + a * .2, cy + b * .45)])
    cv.hair([(cx - a * .12, cy + b * .05), (cx + a * .12, cy + b * .05)])
    cv.obj([_ell(cx - a * .1, cy - b * .78, s * .022, s * .022, 6)[:-1], _ell(cx + a * .1, cy - b * .78, s * .022, s * .022, 6)[:-1]], .5)
    if sticks:
        (lx, ly), (rx, ry) = tips
        L = s * .85
        for (tx, ty), sd in (((lx, ly), -1), ((rx, ry), 1)):
            ang = -_PI / 2 - sd * 1.0
            p0 = (tx - _m.cos(ang) * L * .08, ty - _m.sin(ang) * L * .08)
            p1 = (tx + _m.cos(ang) * L * .92, ty + _m.sin(ang) * L * .92)
            R = _Rib([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1], [s * .028, s * .025, s * .012],
                     [s * .028, s * .025, s * .012])
            cv.obj([R.outline()], .5)
            cv.hair(R.contour(.5, 0, 1))
            cv.obj([_ell(p1[0], p1[1], s * .025, s * .025, 8)[:-1]], .5)


def strand(x, y, W, H, seed, band=True):
    """the wet sand at the tide line: lace of the last wave along the top, ripple marks, the clam
    and the crab, a few shell bits; the whole field worked, nothing left bare"""
    rng = _r.Random(seed)
    cv = Canvas()
    cv.obj([[(x - 2, y - 2), (x + W + 2, y - 2), (x + W + 2, y + H + 2), (x - 2, y + H + 2)]], 0)
    sea = y + H * (.14 if band else .3)
    # the sea: swells in burin lines, breaking into a lace of foam at the edge
    yy = y - 1
    k = 0
    while yy < sea:
        pts = [(x - 2 + i * 3, yy + .8 * _m.sin(i * .7 + k * 1.3 + seed)) for i in range(int(W / 3) + 3)]
        cv.line(pts) if (sea - yy) > H * .06 else cv.hair(pts)
        yy += 1.5 + 1.5 * (yy - y) / max(1., sea - y)
        k += 1
    lace = []
    for i in range(int(W / 2) + 3):
        lx = x - 2 + i * 2
        lace.append((lx, sea + 1.6 * _m.sin(lx * .21 + seed) + 1.2 * _m.sin(lx * .053)))
    foam = lace + [(x + W + 2, sea + 7), (x - 2, sea + 7)]
    cv.obj([foam], 0)
    cv.line(lace)
    for j in range(int(W / 5)):
        fx = x + rng.uniform(0, W)
        fy = sea + rng.uniform(2.5, 6)
        cv.obj([_ell(fx, fy, rng.uniform(.8, 1.6), .7, 6)[:-1]], .5)
    # ripple marks: sinuous ridges, each crest a lit edge with its lee side hatched into shadow
    yy = sea + 8
    k = 0
    while yy < y + H + 4:
        ph = rng.uniform(0, 6)
        amp = 1.2 + k * .15
        crest = [(x - 2 + i * 2.5, yy + amp * _m.sin(i * .19 + ph) + .6 * _m.sin(i * .53 + ph * 2)) for i in range(int(W / 2.5) + 3)]
        cv.line(crest)
        for i in range(0, len(crest) - 1, 2):
            px, py = crest[i]
            cv.hair([(px, py + 1.2), (px - .8, py + 2.6 + .3 * k)])
        yy += 5.5 + k * .8
        k += 1
    # shell bits and a sand dollar
    for j in range(int(W * H / 900) + 2):
        bx, by = x + rng.uniform(0, W), sea + 8 + rng.uniform(0, max(1., y + H - sea - 10))
        r = rng.uniform(1.2, 2.4)
        cv.obj([[(bx - r, by), (bx, by - r * .8), (bx + r, by)]], .5)
        cv.hair([(bx, by - r * .7), (bx, by)])
    s = min(H * (.62 if band else .4), W * .3)
    cyc = y + H * (.66 if band else .8)
    razor_clam(cv, x + W * .3 - s * .8, cyc - s * .05, s * 1.5, -.12)
    dungeness(cv, x + W * .64, cyc + s * .02, s * .85)
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 5

    def sc(x, y, sw, sh, mode):
        if mode in ("band", "egg"):
            return strand(x, y, sw, sh, seed, True)
        d = f"M{f(x)},{f(y)}h{f(sw)}v{f(sh)}h{f(-sw)}z"
        return vignette(x, y, sw, sh, d, C._uid("v", w, h, seed), seed, "tall") + strand(x, y + sh * .62, sw, sh * .38, seed, True)

    def banner(centre, rh):
        return P(letter_along(centre, "CANNON BEACH", rh * .56), 1)

    def egg(cv, x, y, s):
        # a heron fishing the slough, hidden in the scroll
        fig_heron(cv, x, y + s * .45, s)

    return compose(w, h, sc, seed, medal="cushion", egg=egg, banner=banner, mw_frac=.62)
