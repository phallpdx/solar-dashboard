"""doodles-03 "The rain jar": Parker's rain gauge on Sauvie Island in a November squall.

Tall: a carved cartouche held by mirrored acanthus volutes; inside, storm clouds over Mt. Hood
and the cottonwood line, slanting rain, a glass gauge on a grained post holding 1.31 in (a black
pointer marks the 2.1 in Portland usually has by now), a heron in the flooded slough and, in the
mud by the post, the dog's paw prints (the Easter egg). The crest carries a raindrop finial, the
ribbon carries the five recent rainy days as five drops sized by their totals, and the pedestal
tablet is a month gauge filled to 1.31 of the usual 5.6 in.
Medium: the same scene in the cartouche between volutes. Short: a frieze round a medallion
holding the gauge in the rain."""
import sys
import math
import random
import re
import engraving_codex as C

# ==== STUDIO ENGINE (batch 5) ====================================================================
# Everything below lives in one function's namespace (ST5) so its names never collide with the
# page's own helpers.
import types as _types


def _studio5():
    # King-tier fine scroll: dense, small logarithmic-spiral scrolls grown from one stem source and
    # branching in rhythm (Hunt), every curl ending in a tight eye and clothed in small lobed leaves
    # shaded with fine cuts on the shadow side and a bright cut edge; a punched matte ground between
    # them; gold-line (fine double rule + beading) borders that follow each panel; an inlaid portrait
    # medallion in a ring of beads for the page's subject; ribbon banners and a knurled pedestal with
    # engraved Roman capitals. Inlined verbatim into each batch-5 plate (identical copies) so every
    # plate stays self-contained; the page's own vignette and figures follow the END marker.
    import math as _m
    import random as _r
    import zlib as _z
    import engraving_codex as C

    _PI = _m.pi
    _TAU = 2 * _PI
    _sm = C._smooth
    _N = C._n
    _CR = ' shape-rendering="crispEdges"'


    def _uidp(*a):
        return "b5" + format(_z.crc32(repr(a).encode()) & 0xffffff, "x")


    def _lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


    def _bez(p0, p1, p2, p3, n):
        out = []
        for i in range(n + 1):
            t = i / n
            a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
            out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
        return out


    def _cum(p):
        S = [0.]
        for i in range(1, len(p)):
            S.append(S[-1] + _m.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]))
        return S


    def _resample(p, step):
        S = _cum(p)
        L = S[-1]
        n = max(2, int(L / step))
        out, j = [], 0
        for k in range(n + 1):
            s = L * k / n
            while j < len(p) - 2 and S[j + 1] < s:
                j += 1
            seg = (S[j + 1] - S[j]) or 1.
            out.append(_lerp(p[j], p[j + 1], (s - S[j]) / seg))
        return out


    def _offset(poly, d):
        """Closed polygon offset outward by d along vertex normals (smooth convex shapes)."""
        n = len(poly)
        sg = 1 if C._area(poly) > 0 else -1
        out = []
        for i in range(n):
            a, b = poly[i - 1], poly[(i + 1) % n]
            tx, ty = b[0] - a[0], b[1] - a[1]
            L = _m.hypot(tx, ty) or 1.
            out.append((poly[i][0] + sg * ty / L * d, poly[i][1] - sg * tx / L * d))
        return out


    def _ell(cx, cy, rx, ry, n=48, a0=0., a1=_TAU):
        return [(cx + rx * _m.cos(a0 + (a1 - a0) * i / n), cy + ry * _m.sin(a0 + (a1 - a0) * i / n))
                for i in range(n + 1)]


    def _shape(kind, cx, cy, a, b, n=120):
        """Closed medallion outlines: oval, round, lozenge-oval (pointed top and bottom), shield,
        arch (round-headed), quatre (four-lobed), octo (canted octagon), cusp (Thai pointed arch)."""
        pts = []
        for i in range(n):
            t = _TAU * i / n
            c, s = _m.cos(t), _m.sin(t)
            if kind == "round":
                r = min(a, b)
                pts.append((cx + r * c, cy + r * s))
            elif kind == "super":
                e = 2.6
                pts.append((cx + a * (abs(c) ** (2 / e)) * (1 if c >= 0 else -1),
                            cy + b * (abs(s) ** (2 / e)) * (1 if s >= 0 else -1)))
            elif kind == "quatre":
                k = 1 + .07 * _m.cos(4 * t)
                pts.append((cx + a * k * c, cy + b * k * s))
            elif kind == "lozenge":
                k = 1 - .1 * abs(s) ** 6
                pts.append((cx + a * c * (1 - .12 * s * s), cy + b * s * (1 + .06 * abs(s))))
            elif kind == "octo":
                e = 1.2
                u = max(abs(c), abs(s), (abs(c) + abs(s)) / 1.32)
                pts.append((cx + a * c / u ** e * .93, cy + b * s / u ** e * .93))
            elif kind == "cusp":
                # a Thai arch: round below, rising to a flame-point above
                if s < 0:
                    kk = abs(c) ** 1.6
                    pts.append((cx + a * c * (1 - .25 * (1 - kk) * abs(s)), cy + b * s * (1 + .18 * (1 - abs(c)) ** 3)))
                else:
                    pts.append((cx + a * c, cy + b * s))
            elif kind == "arch":
                if s < 0:
                    pts.append((cx + a * c, cy + b * s))
                else:
                    e = 4.
                    pts.append((cx + a * (abs(c) ** (2 / e)) * (1 if c >= 0 else -1), cy + b * (abs(s) ** (2 / e))))
            elif kind == "shield":
                if s < 0:
                    pts.append((cx + a * c, cy + b * .78 * s))
                else:
                    pts.append((cx + a * c * (1 - .3 * s ** 2), cy + b * s * (1 + .1 * s)))
            else:  # oval
                pts.append((cx + a * c, cy + b * s))
        return pts


    # ----------------------------------------------------------------------------------------------
    # the studio: canvases and an occupancy grid that the scroll grows into
    # ----------------------------------------------------------------------------------------------

    def _runs(pl, mask, x0, y0, W, H, out):
        """Split polyline pl into its runs not covered by mask, keeping the original vertices (so the
        result needs no simplification) and adding the exact entry and exit points."""
        run = []
        last = None
        n = len(pl)
        for i in range(n - 1):
            ax, ay = pl[i]
            bx, by = pl[i + 1]
            dx, dy = bx - ax, by - ay
            k = max(1, int(abs(dx) + abs(dy)))
            for j in range(0 if i == 0 else 1, k + 1):
                t = j / k
                x, y = ax + dx * t, ay + dy * t
                xi, yi = int(x - x0), int(y - y0)
                if 0 <= xi < W and 0 <= yi < H and mask[yi][xi]:
                    if run:
                        if last is not None and run[-1] is not last:
                            run.append(last)
                        if len(run) > 1:
                            out.append(run)
                        run = []
                    last = None
                else:
                    last = (x, y)
                    if not run:
                        run = [last]
                    elif j == k:
                        run.append(last)
        if run:
            if last is not None and run[-1] is not last:
                run.append(last)
            if len(run) > 1:
                out.append(run)


    class Cv(C.Canvas):
        """The house canvas with a faster emitter: lines are clipped by the objects painted over them
        without resampling, so no simplification pass is needed."""

        def svg(self):
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
                    o_ = out[w]
                    for pl in lines:
                        _runs(pl, mask, x0, y0, W, H, o_)
                if ow:
                    for poly in polys:
                        _runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
                for poly in polys:
                    C._fill_mask(poly, mask, x0, y0, W, H)
            T = C._QT
            res = []
            pen = C._Pen()
            for polys, _, _ in self.objs:
                for poly in polys:
                    pen.add(poly if C._area(poly) >= 0 else poly[::-1], True, .5 if len(poly) > 40 else .25)
            if pen.o:
                res.append(f'<path{T} d="{pen.d()}" fill="#fff" stroke="none"/>')
            for w in (.5, 1., 1.5):
                if out[w]:
                    pen = C._Pen()
                    for pl in out[w]:
                        pen.add(pl, False, .4 if len(pl) > 6 else 0)
                    res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_N(w * C._Q)}"/>')
            return "".join(res)


    class Studio:
        CELL = 3.

        def __init__(self, w, h, seed):
            self.w, self.h = w, h
            self.rng = _r.Random(seed)
            c = self.CELL
            self.gw, self.gh = int(w / c) + 2, int(h / c) + 2
            self.grid = bytearray(self.gw * self.gh)
            self.allow = bytearray(b"\x00" * (self.gw * self.gh))   # 1 = scroll may grow here

        # -- grid -----------------------------------------------------------------------------------
        def _rows(self, poly, fn, pad=0.):
            c = self.CELL
            ys = [p[1] for p in poly]
            n = len(poly)
            r0, r1 = max(0, int(min(ys) / c)), min(self.gh - 1, int(max(ys) / c) + 1)
            edges = []
            for i in range(n):
                ax, ay = poly[i]
                bx, by = poly[(i + 1) % n]
                if ay != by:
                    if ay > by:
                        ax, ay, bx, by = bx, by, ax, ay
                    edges.append((ay, by, ax, (bx - ax) / (by - ay)))
            for r in range(r0, r1 + 1):
                yc = (r + .5) * c
                xs = sorted(ex + (yc - e0) * sl for e0, e1, ex, sl in edges if e0 <= yc < e1)
                for j in range(0, len(xs) - 1, 2):
                    a = max(0, int((xs[j] - pad) / c + .5))
                    b = min(self.gw, int((xs[j + 1] + pad) / c + .5))
                    if b > a:
                        fn(r, a, b)

        def occupy(self, poly, pad=0.):
            g, gw = self.grid, self.gw

            def f(r, a, b):
                g[r * gw + a:r * gw + b] = b"\xff" * (b - a)
            self._rows(poly, f, pad)

        def permit(self, poly, v=1):
            g, gw = self.allow, self.gw
            ch = bytes([v])

            def f(r, a, b):
                g[r * gw + a:r * gw + b] = ch * (b - a)
            self._rows(poly, f)

        def permit_rect(self, x0, y0, x1, y1, v=1):
            self.permit([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], v)

        def free(self, x, y):
            c = self.CELL
            q, r = int(x / c), int(y / c)
            if 0 <= q < self.gw and 0 <= r < self.gh:
                i = r * self.gw + q
                return self.allow[i] and not self.grid[i]
            return False

        def fits(self, pts, rad, skip=0, own=0):
            """True if a stroke along pts with half-width rad lies in allowed cells that are free or
            belong to `own` (a scroll may overlap its own leaves)."""
            c = self.CELL
            g, al, gw, gh = self.grid, self.allow, self.gw, self.gh
            k = max(0, int(rad / c))
            for (x, y) in pts[skip::2]:
                q0, r0 = int(x / c), int(y / c)
                for dq in (-k, 0, k):
                    for dr in (-k, 0, k):
                        q, r = q0 + dq, r0 + dr
                        if not (0 <= q < gw and 0 <= r < gh):
                            return False
                        i = r * gw + q
                        if (g[i] and g[i] != own) or not al[i]:
                            return False
            return True

        def mark(self, pts, rad, own=255):
            c = self.CELL
            g, gw, gh = self.grid, self.gw, self.gh
            k = max(0, int(rad / c + .5))
            ch = bytes([own])
            for (x, y) in pts:
                q0, r0 = int(x / c), int(y / c)
                for r in range(max(0, r0 - k), min(gh, r0 + k + 1)):
                    a, b = max(0, q0 - k), min(gw, q0 + k + 1)
                    if b > a:
                        g[r * gw + a:r * gw + b] = ch * (b - a)

        def obj(self, cv, polys, outline=1.):
            for p in polys:
                if len(p) > 2:
                    self.occupy(p)
            return cv.obj(polys, outline)

        def dist(self):
            """Chamfer distance (cells) to the nearest occupied or forbidden cell (0 outside)."""
            gw, gh = self.gw, self.gh
            al, g = self.allow, self.grid
            D = [0.] * (gw * gh)
            rows = [r for r in range(gh) if any(al[r * gw:(r + 1) * gw])]
            if not rows:
                return D
            r0, r1 = max(1, rows[0]), min(gh - 2, rows[-1])
            cols = [q for q in range(gw) if any(al[r * gw + q] for r in range(r0, r1 + 1, 3))]
            q0, q1 = max(1, cols[0] - 1), min(gw - 2, cols[-1] + 1)
            INF = 1e6
            for r in range(r0, r1 + 1):
                o = r * gw
                for q in range(q0, q1 + 1):
                    if al[o + q] and not g[o + q]:
                        D[o + q] = INF
            a, b = 1., 1.414
            for r in range(r0, r1 + 1):
                o = r * gw
                for q in range(q0, q1 + 1):
                    i = o + q
                    v = D[i]
                    if not v:
                        continue
                    j = i - gw
                    v = min(v, D[i - 1] + a, D[j] + a, D[j - 1] + b, D[j + 1] + b)
                    D[i] = v
            for r in range(r1, r0 - 1, -1):
                o = r * gw
                for q in range(q1, q0 - 1, -1):
                    i = o + q
                    v = D[i]
                    if not v:
                        continue
                    j = i + gw
                    v = min(v, D[i + 1] + a, D[j] + a, D[j + 1] + b, D[j - 1] + b)
                    D[i] = v
            return D


    # ----------------------------------------------------------------------------------------------
    # the leaf: small, lobed, serrated; fine cuts massed on the shadow side, a bright cut edge
    # ----------------------------------------------------------------------------------------------

    def _leaf_rib(x, y, ang, L, W, bend, tip, lobes, rng):
        n = max(12, int(L / .8))
        G = sum(_sm(.6, 1., (i + .5) / 40) ** 2 for i in range(40)) / 40

        def k(u):
            return (bend + tip * _sm(.6, 1., u) ** 2 / G) / L

        pts = C._euler(x, y, ang, L, k, n)
        env = [W * (_m.sin(_PI * min(1., (i / n) * .96 + .04)) ** .6) * (.6 + .4 * (1 - i / n)) *
               (.3 + .7 * _sm(0., .18, i / n)) + .35 for i in range(n + 1)]
        sides = {}
        for side in (1, -1):
            k_ = max(1, lobes + (0 if side > 0 else rng.choice((0, 0, -1, 1))))
            ws = [1.3 - .5 * j / k_ + rng.uniform(-.1, .1) for j in range(k_)]
            tot = sum(ws)
            u0 = .14 + rng.uniform(0, .06)
            nodes = [u0]
            for wj in ws:
                nodes.append(nodes[-1] + (.86 - u0) * wj / tot)
            teeth = 3 if W > 6 else 2
            prof = []
            for i in range(n + 1):
                u = i / n
                f = 1.
                if nodes[0] <= u < nodes[-1]:
                    j = 0
                    while j < k_ - 1 and u >= nodes[j + 1]:
                        j += 1
                    t = (u - nodes[j]) / (nodes[j + 1] - nodes[j])
                    f = .45 + .55 * _m.sin(_PI * t ** 1.3) ** .5
                    if t > .25 and W > 3.5:
                        f *= .84 + .16 * ((t * teeth) % 1.) ** 1.5
                prof.append(max(.35, env[i] * f))
            sides[side] = (prof, nodes)
        return pts, sides


    def leaf(st, cv, x, y, ang, L, W=None, bend=.5, tip=2., lobes=3, dark=1, seed=0, outline=None):
        """A small acanthus leaf rooted at (x, y), heading ang (radians), L long, about W wide each side
        of the midrib; bend (radians over the length) sweeps it, tip rolls the point. `dark` (+1/-1)
        picks the side of the midrib that takes the shade. Returns the outline polygon."""
        rng = _r.Random(seed)
        W = W or L * .24
        pts, sides = _leaf_rib(x, y, ang, L, W, bend, tip, lobes, rng)
        R = C._Rib(pts, sides[1][0], sides[-1][0])
        nn = R.n
        out = C._dp([R.at(i / (nn - 1), 1.) for i in range(nn)] + [R.at(i / (nn - 1), -1.) for i in range(nn - 1, -1, -1)], .35)
        st.obj(cv, [out], outline if outline is not None else (1. if W > 5.5 else .5))
        Ln = R.L
        c = 1 if dark >= 0 else -1
        for side in (c, -c):
            prof, nodes = sides[side]
            dk = side == c
            if not dk and W < 7:
                continue
            pitch = (2. if W > 6 else 3.) if dk else 3.
            u = .04
            while u < .95:
                w = R.width(u, side)
                if w > 1.5:
                    j = None
                    for q in range(len(nodes) - 1):
                        if nodes[q] <= u < nodes[q + 1]:
                            j = q
                            break
                    t = .5 if j is None else (u - nodes[j]) / (nodes[j + 1] - nodes[j])
                    crest = _m.sin(_PI * t) ** 2
                    if dk:
                        reach = .92 - .45 * crest - .3 * _sm(.7, 1., u)
                    else:
                        reach = (.55 - .4 * crest) * (1 - _sm(.35, .8, u))
                    if reach * w > 1.3:
                        fw = min(.08, 2.6 * reach * w / Ln)
                        if reach * w > 4.:
                            cv.hair([R.at(u, side * .08), R.at(u + fw * .5, side * (.08 + (reach - .08) * .55)),
                                     R.at(u + fw, side * reach)])
                        else:
                            cv.hair([R.at(u, side * .08), R.at(u + fw, side * reach)])
                        if dk and reach * w > 3.5 and crest < .5:
                            # the burin swells: a 1 px cut over the middle of the line, deep in the cup
                            cv.line([R.at(u + fw * .2, side * (.08 + (reach - .08) * .2)),
                                     R.at(u + fw * .6, side * (.08 + (reach - .08) * .62))])
                u += pitch / Ln
            for j in range(1, len(nodes) - 1):
                un = nodes[j]
                if R.width(un, side) > 1.8:
                    (cv.heavy if W > 7 else cv.line)([R.at(un + .004, side * .99), R.at(un - .02, side * .62),
                                                       R.at(un - .045, side * .36)])
            if W > 8:
                for j in range(len(nodes) - 1):
                    ua, ub = nodes[j], nodes[j + 1]
                    cv.line([R.at(ua + (ub - ua) * .05, side * .06), R.at(ua + (ub - ua) * .35, side * .32),
                             R.at(ua + (ub - ua) * .6, side * .6)])
        if W > 5:
            C._shadow(cv, R, c, min(2.4, W * .18), .12, .82)
        (cv.line if W > 5 else cv.hair)(R.contour(c * .04, .02, .86))
        return out


    # ----------------------------------------------------------------------------------------------
    # the scroll: a stem that leads in and winds into a logarithmic spiral with a tight eye
    # ----------------------------------------------------------------------------------------------

    def _branch_pts(root, heading, r, sg, turns=1.6, lead=0., lead_k=0., b=.28):
        """Centre line from root heading `heading`: an optional lead of length `lead` (curving lead_k
        per px toward sg), then a log spiral starting at radius r winding sg `turns` turns into an eye."""
        pts = []
        x, y = root
        h = heading
        if lead > 0:
            n = max(3, int(lead / 1.5))
            ld = C._euler(x, y, h, lead, lambda u: sg * lead_k, n)
            pts.extend(ld[:-1])
            x, y = ld[-1]
            h = heading + sg * lead_k * lead
        phi = _m.atan(b)
        a0 = h - sg * (_PI / 2 + phi)
        cx, cy = x - r * _m.cos(a0), y - r * _m.sin(a0)
        th = _TAU * turns
        n = max(16, int(r * th * .6))
        for i in range(n + 1):
            t = th * i / n
            rr = r * _m.exp(-b * t)
            if rr < .9 and i > 4:
                break
            ph = a0 + sg * t
            pts.append((cx + rr * _m.cos(ph), cy + rr * _m.sin(ph)))
        return pts, (cx, cy)


    def _catmull(P, step=1.5):
        """A smooth curve through the points P."""
        out = []
        Q = [P[0]] + list(P) + [P[-1]]
        for i in range(1, len(Q) - 2):
            p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
            n = max(2, int(_m.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
            for k in range(n):
                t = k / n
                t2, t3 = t * t, t * t * t
                out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
        out.append(P[-1])
        return out


    class Branch:
        __slots__ = ("pts", "c", "r", "sg", "w0", "depth", "S", "leaves", "ins", "parent", "eye", "clad", "own")

        def __init__(self, pts, c, r, sg, w0, depth, parent=None, eye=True):
            self.pts, self.c, self.r, self.sg, self.w0, self.depth = pts, c, r, sg, w0, depth
            self.S = _cum(pts)
            self.leaves = []
            self.parent = parent
            self.eye = eye
            self.clad = False
            self.own = 0
            n = len(pts)
            i = int(n * .75)
            a, q = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
            nx, ny = -(q[1] - a[1]), q[0] - a[0]
            self.ins = 1 if nx * (c[0] - pts[i][0]) + ny * (c[1] - pts[i][1]) > 0 else -1

        def at(self, u):
            S, p = self.S, self.pts
            s = min(max(u, 0.), 1.) * S[-1]
            lo, hi = 0, len(S) - 1
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if S[mid] < s:
                    lo = mid
                else:
                    hi = mid
            seg = (S[hi] - S[lo]) or 1.
            q = _lerp(p[lo], p[hi], (s - S[lo]) / seg)
            return q, _m.atan2(p[hi][1] - p[lo][1], p[hi][0] - p[lo][0])

        def wid(self, u):
            return max(.75, self.w0 * (1 - .72 * min(1., u) ** .8) * (.55 + .45 * _sm(0., .08, u)))

        def edge(self, u, side):
            """Point on the stem's edge at u: side +1 = outside of the curl, -1 = inside."""
            p, a = self.at(u)
            nx, ny = -_m.sin(a), _m.cos(a)
            s = -self.ins * side
            w = self.wid(u)
            return (p[0] + nx * s * w, p[1] + ny * s * w), a


    def _leaf_spine(x, y, ang, L, bend, tip):
        G = sum(_sm(.6, 1., (i + .5) / 40) ** 2 for i in range(40)) / 40
        return C._euler(x, y, ang, L, lambda u: (bend + tip * _sm(.6, 1., u) ** 2 / G) / L, 10)


    class Scroll:
        """Grows a family of scrolls from source stems into the allowed free ground of a Studio:
        every scroll sprouts smaller scrolls from its curve, winding the other way (the skeleton),
        then each is clothed in overlapping leaves that may lie over their own scroll but never over
        a neighbour's."""

        def __init__(self, st, seed, rmin=6., leaf_k=1.):
            self.st = st
            self.rng = _r.Random(seed)
            self.rmin = rmin
            self.leaf_k = leaf_k
            self.branches = []
            self.extras = []

        def _id(self, b):
            return 1 + (self.branches.index(b) if b in self.branches else len(self.branches)) % 250

        def _claim(self, b, own):
            st = self.st
            pts = b.pts
            tot = b.S[-1] or 1.
            for i in range(0, len(pts), 2):
                st.mark([pts[i]], b.wid(b.S[i] / tot) + 1., own)

        def try_branch(self, root, heading, r, sg, depth, turns=None, lead=None, skip=0., force=False,
                       parent=None, lead_k=None, scales=(1., .84, .7, .58, .48)):
            st, rng = self.st, self.rng
            for sc in scales:
                rr = r * sc
                if rr < self.rmin:
                    break
                tn = turns or rng.uniform(1.45, 1.85)
                ld = (lead if lead is not None else rng.uniform(.15, .6) * rr) * (sc if lead is None else 1)
                lk = lead_k if lead_k is not None else rng.uniform(.1, .6) / max(rr, 1)
                pts, c = _branch_pts(root, heading, rr, sg, tn, ld, lk, .24)
                w0 = .7 + rr * .085
                sk = 0
                while sk < len(pts) - 1 and _m.hypot(pts[sk][0] - root[0], pts[sk][1] - root[1]) < skip:
                    sk += 1
                pown = parent[0].own if parent else 0
                if force or (st.fits(pts, w0 + 1.4, sk, pown) and st.free(*c)):
                    b = Branch(pts, c, rr, sg, w0, depth, parent)
                    self.branches.append(b)
                    own = len(self.branches) % 250 + 1
                    b.own = own
                    self._claim(b, own)
                    if depth == 0:
                        self._plan_leaves(b, own)
                        b.clad = True
                    return b
            return None

        def _try_leaf(self, b, own, base, hd, L, W, bend, tip, dark, shrink=(1., .82, .66, .52), lmin=4.):
            st = self.st
            for sc in shrink:
                ll = L * sc
                if ll < lmin:
                    return None
                sp = _leaf_spine(base[0], base[1], hd, ll, bend, tip)
                if st.fits(sp[2:], W * sc * .5, 0, own):
                    for p in sp[1:]:
                        st.mark([p], W * sc * .65, own)
                    lf = (base, hd, ll, W * sc, bend, tip, dark)
                    b.leaves.append(lf)
                    return lf
            return None

        def _plan_leaves(self, b, own):
            rng = self.rng
            k_ = self.leaf_k
            ex, ey = b.pts[-1]
            tot = b.S[-1]
            ins = b.ins
            # a sheath leaf over the fork this scroll springs from
            if b.parent:
                base, ang = b.at(.0)
                ll = max(5., b.r * .95) * k_
                self._try_leaf(b, own, base, ang - b.ins * .15, ll, ll * .34, -ins * .4, -ins * 1.6, -ins)
            # leaves along the outside, root to curl, each sized to its distance from the eye
            u = .1
            while u < .74:
                base, ang = b.edge(u, 1)
                hd = ang - ins * rng.uniform(.28, .55)
                rad = _m.hypot(base[0] - b.c[0], base[1] - b.c[1])
                ll = min(b.r * 1.3, 30., max(5., rad * 1.2)) * rng.uniform(.9, 1.1) * k_
                self._try_leaf(b, own, base, hd, ll, ll * rng.uniform(.32, .4), -ins * rng.uniform(.3, .6),
                               -ins * rng.uniform(1.6, 2.4), -ins)
                u += max(.08, ll * .55 / tot)
            # leaves inside the curl, rolling into the eye
            for u, f in ((.5, 1.), (.32, .8)):
                if b.r * f < 6:
                    continue
                p, ang = b.at(u)
                nx, ny = -_m.sin(ang), _m.cos(ang)
                base = (p[0] + nx * ins * b.wid(u) * .6, p[1] + ny * ins * b.wid(u) * .6)
                rad = _m.hypot(base[0] - ex, base[1] - ey)
                ll = max(5., rad * 1.55 * f)
                self._try_leaf(b, own, base, ang + ins * .6, ll, ll * .32, ins * 2.1, ins * 2.3, ins)

        def grow(self, sources, max_depth=7, k_child=(.5, .74)):
            """sources: list of (root, heading, r, sg[, dict]). Breadth first, largest first."""
            q = []
            for src in sources:
                root, heading, r, sg = src[:4]
                kw = src[4] if len(src) > 4 else {}
                if kw.get("via"):
                    lead = _catmull([root] + list(kw["via"]))
                    a, z = lead[-2], lead[-1]
                    hd = _m.atan2(z[1] - a[1], z[0] - a[0])
                    sp, cc = _branch_pts(z, hd, r, sg, kw.get("turns", 1.7), 0., 0., .24)
                    pts = lead[:-1] + sp
                    b = Branch(pts, cc, r, sg, .7 + r * .085, 0, None)
                    self.branches.append(b)
                    own = len(self.branches) % 250 + 1
                    b.own = own
                    self._claim(b, own)
                    self._plan_leaves(b, own)
                    b.clad = True
                    q.append(b)
                    continue
                b = self.try_branch(root, heading, r, sg, 0, force=kw.get("force", True), turns=kw.get("turns"),
                                    lead=kw.get("lead"), lead_k=kw.get("lead_k"))
                if b:
                    q.append(b)
            self._bfs(q, max_depth, k_child)
            return self.branches

        def _bfs(self, q, max_depth, k_child):
            rng = self.rng
            while q:
                q.sort(key=lambda b: -b.r)
                b = q.pop(0)
                if b.depth >= max_depth:
                    continue
                for u in [.05 + .09 * i for i in range(8)]:
                    u += rng.uniform(-.02, .02)
                    for side in ((1, -1) if u < .4 else (1,)):
                        base, ang = b.edge(u, side)
                        turn = -b.ins * side
                        hd = ang + turn * rng.uniform(.45, .9)
                        sg = -b.sg if side > 0 else b.sg
                        kr = b.r * rng.uniform(*k_child) * (1 - .35 * u)
                        c = self.try_branch(base, hd, kr, sg, b.depth + 1, skip=b.wid(u) * 2 + 5., parent=(b, u))
                        if c:
                            q.append(c)
                            break

        def infill(self, passes=14, max_depth=8):
            """Sprout a scroll into each wide hole left, from the nearest stem."""
            st, rng = self.st, self.rng
            c = st.CELL
            for _ in range(passes):
                D = st.dist()
                gw = st.gw
                cand = sorted(((D[i], i) for i in range(len(D)) if 1e5 > D[i] * c > self.rmin * 1.5), reverse=True)
                BK = 24.
                buck = {}
                for b in self.branches:
                    for k in range(0, len(b.pts), 4):
                        if b.S[k] < .8 * b.S[-1]:
                            px, py = b.pts[k]
                            buck.setdefault((int(px / BK), int(py / BK)), []).append((b.pts[k], b, k))
                samples = bool(buck)
                got, tried = [], []
                for d, i in cand:
                    if len(tried) > 40:
                        break
                    x, y = (i % gw + .5) * c, (i // gw + .5) * c
                    if any((x - tx) ** 2 + (y - ty) ** 2 < (td * c * .9) ** 2 for tx, ty, td in tried):
                        continue
                    tried.append((x, y, d))
                    if not samples:
                        break
                    qx, qy = int(x / BK), int(y / BK)
                    near = []
                    rad_ = 1
                    while not near and rad_ < 12:
                        for ax in range(qx - rad_, qx + rad_ + 1):
                            for ay in range(qy - rad_, qy + rad_ + 1):
                                near.extend(buck.get((ax, ay), ()))
                        rad_ += 2
                    if not near:
                        continue
                    (px, py), b, k = min(near, key=lambda s: (s[0][0] - x) ** 2 + (s[0][1] - y) ** 2)
                    u = b.S[k] / (b.S[-1] or 1)
                    e1, ang = b.edge(u, 1)
                    e2, _ = b.edge(u, -1)
                    base = e1 if (e1[0] - x) ** 2 + (e1[1] - y) ** 2 <= (e2[0] - x) ** 2 + (e2[1] - y) ** 2 else e2
                    to = _m.atan2(y - base[1], x - base[0])
                    dd = _m.hypot(x - base[0], y - base[1])
                    rr = d * c * rng.uniform(.8, .95)
                    sg = rng.choice((-1, 1))
                    nb = self.try_branch(base, to - sg * .35, rr, sg, b.depth + 1, skip=b.wid(u) * 2 + 5.,
                                         parent=(b, u), lead=min(rr * .8, max(0., dd - rr * 1.2)))
                    if nb:
                        got.append(nb)
                if not got:
                    break
                self._bfs(got, max_depth, (.5, .74))

        def clothe(self):
            for i, b in sorted(enumerate(self.branches), key=lambda ib: -ib[1].r):
                if not b.clad:
                    self._plan_leaves(b, b.own)
                    b.clad = True

        def leaf_fill(self, dmin=1.5, lmax=14., max_n=300, dmax=5.):
            """Last pass: small leaves into whatever holes remain, each springing from the relief
            beside it."""
            st, rng = self.st, self.rng
            D = st.dist()
            gw, c = st.gw, st.CELL
            cand = sorted(((D[i], i) for i in range(len(D)) if 1e5 > D[i] >= dmin and D[i] <= dmax), reverse=True)
            if not self.branches:
                return 0
            host = self.branches[0]
            n = 0
            for d, i in cand:
                if n >= max_n:
                    break
                x, y = (i % gw + .5) * c, (i // gw + .5) * c
                if not st.free(x, y):
                    continue
                best = None
                for k in range(12):
                    a = _TAU * k / 12
                    for s in range(1, int(d) + 4):
                        if not st.free(x + _m.cos(a) * s * c, y + _m.sin(a) * s * c):
                            if best is None or s < best[0]:
                                best = (s, a)
                            break
                if best is None:
                    continue
                s, a = best
                bx, by = x + _m.cos(a) * (s - .5) * c, y + _m.sin(a) * (s - .5) * c
                hd = a + _PI + rng.uniform(-.6, .6)
                ll = min(lmax, d * c * 2.2)
                sgn = rng.choice((-1, 1))
                if self._try_leaf(host, 254, (bx, by), hd, ll, ll * .34, sgn * .5, sgn * 2., sgn, (1., .8, .6), 3.5):
                    n += 1
            return n

        # -- painting -------------------------------------------------------------------------------
        def paint(self, cv, lmin=0.):
            st = self.st
            rng = _r.Random(self.rng.random() if not hasattr(self, "_prng") else self._prng)
            self._prng = getattr(self, "_prng", None) or rng.random()
            rng = _r.Random(self._prng)
            order = sorted(range(len(self.branches)), key=lambda i: (self.branches[i].depth, i))
            for i in order:
                b = self.branches[i]
                self._stem(cv, b)
                for lf in b.leaves[::-1]:
                    base, hd, ll, W, bend, tip, dark = lf
                    if ll < lmin:
                        rng.random()
                        continue
                    leaf(st, cv, base[0], base[1], hd, ll, W, bend, tip, max(1, min(3, int(ll / 8))), dark,
                         rng.randrange(1 << 20))
            for fn in self.extras:
                fn(cv)

        def leaf_lengths(self):
            return sorted(lf[2] for b in self.branches for lf in b.leaves)

        def _stem(self, cv, b):
            pts = b.pts
            n = len(pts)
            tot = b.S[-1] or 1.
            ws = [b.wid(b.S[k] / tot) for k in range(n)]
            R = C._Rib(pts, ws, ws)
            ins = b.ins
            cv.obj([R.outline()], 1. if b.w0 > 1.7 else .5)
            if b.w0 > 1.6:
                cv.hair(R.contour(ins * .4, 0., .97, minw=1.1))
            if b.w0 > 2.4:
                C._shadow(cv, R, ins, b.w0 * .45, 0., .95)
            if b.eye:
                ex, ey = pts[-1]
                rr = max(.9, ws[-1] * .85)
                cv.obj([_ell(ex, ey, rr + .6, rr + .6, 12)[:-1]], 0)
                q_ = rr
                while q_ > .3:
                    cv.line(_ell(ex, ey, q_, q_, max(8, int(q_ * 6))))
                    q_ -= .8


    # ----------------------------------------------------------------------------------------------
    # grounds: the punched matte, and the fine gold-line borders with beading
    # ----------------------------------------------------------------------------------------------

    def matte_defs(seed=7):
        """A punched matte: black, struck with 1 CSS px white punch dots on a jittered 3 px lattice
        (no two closer than 2 px, so none fills in). One pattern tile 30 x 30 px."""
        rng = _r.Random(seed)
        T = 30
        d = []
        taken = set()
        for gy in range(0, T * 2, 6):
            for gx in range(0, T * 2, 6):
                if rng.random() < .82:
                    x, y = gx + rng.randrange(0, 4), gy + rng.randrange(0, 4)
                    key = (x // 3, y // 3)
                    if key in taken:
                        continue
                    taken.add(key)
                    d.append(f"M{_N(x / 2)},{_N(y / 2)}h1v1h-1z")
        tile = (f'<rect width="{T}" height="{T}" fill="#000"/><path d="{"".join(d)}" fill="#fff"/>')
        return f'<pattern id="b5mat" width="{T}" height="{T}" patternUnits="userSpaceOnUse">{tile}</pattern>'


    def matte(shape):
        if isinstance(shape, tuple):
            x, y, w, h = shape
            d = f"M{_N(x)},{_N(y)}h{_N(w)}v{_N(h)}h{_N(-w)}z"
        elif isinstance(shape, list):
            d = C._d(shape, True, 0)
        else:
            d = shape
        return f'<path d="{d}" fill="url(#b5mat)" stroke="none"/>'


    def bead_row(path_pts, r=1.6, gap=1., closed=True):
        """A string of round beads along path_pts, as three dashed strokes (round dots): a black ring,
        the white ball, and a black shadow dot set down-right then a smaller white dot set up-left,
        which leaves a crescent of shade on each bead. 4 elements, a few hundred bytes."""
        p = path_pts + ([path_pts[0]] if closed else [])
        pitch = 2 * r + gap
        L = _cum(p)[-1]
        n = max(1, int(L / pitch))
        pitch = L / n
        d = C._d(p, False, .05)
        da = f'stroke-dasharray="0 {_N(pitch)}" stroke-linecap="round" fill="none"'
        o = [f'<path d="{d}" stroke="#000" stroke-width="{_N(2 * r + 1)}" {da}/>',
             f'<path d="{d}" stroke="#fff" stroke-width="{_N(2 * r)}" {da}/>']
        if r >= 1.2:
            k = r * .35
            o.append(f'<path d="{d}" transform="translate({_N(k)},{_N(k)})" stroke="#000" stroke-width="{_N(2 * r - 1)}" {da}/>')
            o.append(f'<path d="{d}" transform="translate({_N(-k * .6)},{_N(-k * .6)})" stroke="#fff" stroke-width="{_N(2 * r - 1.2)}" {da}/>')
        return "".join(o)


    def gold_line(o, poly, widths=((0, 1.), (2.5, .5)), closed=True):
        """Fine border rules following poly: list of (offset px, stroke width)."""
        for off, sw in widths:
            p = _offset(poly, off) if off else poly
            o.append(f'<path d="{C._d(p, closed, .1)}" fill="none" stroke="#000" stroke-width="{_N(sw)}"/>')


    def border_rect(o, cv, x, y, w, h, beaded=True, r=1.5):
        """A panel's gold-line frame: a 1 px rule, a white fillet with a row of beads, a .5 px rule."""
        bw = 2 * r + 3 if beaded else 3
        outer = f"M{_N(x)},{_N(y)}h{_N(w)}v{_N(h)}h{_N(-w)}z"
        inner = f"M{_N(x + bw)},{_N(y + bw)}v{_N(h - 2 * bw)}h{_N(w - 2 * bw)}v{_N(-h + 2 * bw)}z"
        o.append(f'<path d="{outer}{inner}" fill="#fff" stroke="none"/>')
        o.append(f'<path d="M{_N(x + .5)},{_N(y + .5)}h{_N(w - 1)}v{_N(h - 1)}h{_N(-w + 1)}z" fill="none" stroke="#000" stroke-width="1"{_CR}/>')
        o.append(f'<path d="M{_N(x + bw - .25)},{_N(y + bw - .25)}h{_N(w - 2 * bw + .5)}v{_N(h - 2 * bw + .5)}h{_N(-w + 2 * bw - .5)}z" fill="none" stroke="#000" stroke-width=".5"{_CR}/>')
        if beaded:
            m = bw / 2
            o.append(f'<path d="M{_N(x + 1)},{_N(y + 1)}h{_N(w - 2)}v{_N(h - 2)}h{_N(-w + 2)}zM{_N(x + bw - .5)},{_N(y + bw - .5)}v{_N(h - 2 * bw + 1)}h{_N(w - 2 * bw + 1)}v{_N(-h + 2 * bw - 1)}z" fill="#000" fill-rule="evenodd" stroke="none"/>')
            pts = [(x + m, y + m), (x + w - m, y + m), (x + w - m, y + h - m), (x + m, y + h - m)]
            o.append(bead_row(pts, r, 1.))
        return (x + bw, y + bw, w - 2 * bw, h - 2 * bw)


    # ----------------------------------------------------------------------------------------------
    # the inlaid medallion: the page's scene in a ring of beads between gold lines
    # ----------------------------------------------------------------------------------------------

    def medallion(st, kind, cx, cy, a, b, scene_fn, ring=None):
        """Returns (svg, outer_poly). Rings from outside in: 1 px rule, a fine reeded torus shaded
        toward the lower right, a .5 px rule, a ring of beads on black, a 1 px rule, then the scene
        (scene_fn(x, y, w, h) -> svg, clipped to the inner field)."""
        ring = ring or max(7., min(a, b) * .11)
        out = _shape(kind, cx, cy, a, b, 160)
        st.occupy(_offset(out, 2.))
        o = []
        cv = C.Canvas()
        cv.obj([out], 1.)
        # the reeded torus: concentric fine lines, dense on the shadow side only
        tor = ring * .45
        k = 1
        while k * 1.5 < tor - .5:
            p = _offset(out, -k * 1.5)
            segs, cur = [], []
            for (x, y) in p:
                sh = ((x - cx) / a * .6 + (y - cy) / b * .8)
                if sh > -.15 + .55 * (k * 1.5 / tor):
                    cur.append((x, y))
                else:
                    if len(cur) > 1:
                        segs.append(cur)
                    cur = []
            if len(cur) > 1:
                segs.append(cur)
            cv.hair(segs)
            k += 1
        mid = _offset(out, -tor)
        cv.line([mid + [mid[0]]])
        o.append(cv.svg())
        # beads on a black channel
        inner_c = _offset(out, -ring)
        ch = f'{C._d(mid, True, .1)}{C._d(inner_c[::-1], True, .1)}'
        o.append(f'<path d="{ch}" fill="#000" fill-rule="evenodd" stroke="none"/>')
        br = max(1., min(2., (ring - tor) / 2 - .8))
        o.append(bead_row(_offset(out, -(tor + ring) / 2), br, max(.9, br * .6)))
        o.append(f'<path d="{C._d(inner_c, True, .1)}" fill="none" stroke="#000" stroke-width="1"/>')
        field = _offset(out, -ring - .5)
        xs, ys = [p[0] for p in field], [p[1] for p in field]
        fx, fy, fw, fh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
        cid = _uidp("m", round(cx), round(cy), round(a), round(b))
        o.append(f'<clipPath id="{cid}"><path d="{C._d(field, True, 0)}"/></clipPath>'
                 f'<g clip-path="url(#{cid})"><path d="{C._d(field, True, 0)}" fill="#fff"/>{scene_fn(fx, fy, fw, fh)}</g>')
        o.append(f'<path d="{C._d(field, True, .1)}" fill="none" stroke="#000" stroke-width=".5"/>')
        return "".join(o), out


    # ----------------------------------------------------------------------------------------------
    # Roman capitals: thick and thin strokes with bracketed serifs, drawn as paths
    # ----------------------------------------------------------------------------------------------

    def _arc(cx, cy, rx, ry, a0, a1, n=10):
        return [(cx + rx * _m.cos(_m.radians(a0 + (a1 - a0) * i / n)),
                 cy + ry * _m.sin(_m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


    def _glyphs():
        T, t = "T", "t"
        G = {
            " ": (3.2, []),
            "A": (6.6, [(T, [(3.3, 0), (6.2, 10)]), (t, [(3.3, 0), (.4, 10)]), (t, [(1.6, 6.4), (5.1, 6.4)])]),
            "B": (5.6, [(T, [(.8, 0), (.8, 10)]), (t, [(.8, 0), (3.4, 0)] + _arc(3.4, 2.4, 1.8, 2.4, -90, 90)[1:] + [(.8, 4.8)]),
                        (t, [(.8, 4.8), (3.6, 4.8)] + _arc(3.6, 7.4, 2., 2.6, -90, 90)[1:] + [(.8, 10)]),
                        (T, _arc(3.4, 2.4, 1.5, 2.1, -50, 50)), (T, _arc(3.6, 7.4, 1.7, 2.3, -50, 50))]),
            "C": (6., [(t, _arc(3.4, 5, 2.9, 5, -60, 60 - 360, 18)), (T, _arc(3.5, 5, 2.6, 4.7, 140, 220))]),
            "D": (6.4, [(T, [(.8, 0), (.8, 10)]), (t, [(.8, 0), (2.6, 0)] + _arc(2.6, 5, 3.2, 5, -90, 90, 14)[1:] + [(.8, 10)]),
                        (T, _arc(2.6, 5, 2.9, 4.6, -40, 40))]),
            "E": (5.2, [(T, [(.8, 0), (.8, 10)]), (t, [(.8, 0), (4.6, 0), (4.6, 1.2)]), (t, [(.8, 4.9), (3.6, 4.9)]),
                        (t, [(.8, 10), (4.8, 10), (4.8, 8.6)])]),
            "F": (5., [(T, [(.8, 0), (.8, 10)]), (t, [(.8, 0), (4.6, 0), (4.6, 1.2)]), (t, [(.8, 5.1), (3.6, 5.1)])]),
            "G": (6.4, [(t, _arc(3.4, 5, 2.9, 5, -55, -360, 18)), (T, _arc(3.5, 5, 2.6, 4.7, 140, 220)),
                        (T, [(6.2, 6.), (6.2, 9.4)]), (t, [(4.4, 6.), (6.2, 6.)])]),
            "H": (6.6, [(T, [(.8, 0), (.8, 10)]), (T, [(5.8, 0), (5.8, 10)]), (t, [(.8, 5), (5.8, 5)])]),
            "I": (2.6, [(T, [(1.3, 0), (1.3, 10)])]),
            "J": (3.6, [(T, [(2.6, 0), (2.6, 8.)] + _arc(1.4, 8., 1.2, 2., 0, 140)[1:])]),
            "K": (6., [(T, [(.8, 0), (.8, 10)]), (t, [(5.2, 0), (.8, 6.2)]), (T, [(2.3, 4.4), (5.6, 10)])]),
            "L": (5., [(T, [(.8, 0), (.8, 10)]), (t, [(.8, 10), (4.8, 10), (4.8, 8.4)])]),
            "M": (8., [(t, [(.8, 10), (.8, 0)]), (T, [(.8, 0), (4, 10)]), (t, [(4, 10), (7.2, 0)]), (T, [(7.2, 0), (7.2, 10)])]),
            "N": (6.6, [(t, [(.8, 10), (.8, 0)]), (T, [(.8, 0), (5.8, 10)]), (t, [(5.8, 10), (5.8, 0)])]),
            "O": (7., [(t, _arc(3.5, 5, 3.1, 5, 0, 360, 24)), (T, _arc(3.5, 5, 2.8, 4.7, 140, 220)), (T, _arc(3.5, 5, 2.8, 4.7, -40, 40))]),
            "P": (5.4, [(T, [(.8, 0), (.8, 10)]), (t, [(.8, 0), (3.2, 0)] + _arc(3.2, 2.7, 2., 2.7, -90, 90)[1:] + [(.8, 5.4)]),
                        (T, _arc(3.2, 2.7, 1.7, 2.4, -50, 50))]),
            "Q": (7., [(t, _arc(3.5, 5, 3.1, 5, 0, 360, 24)), (T, _arc(3.5, 5, 2.8, 4.7, 140, 220)), (T, _arc(3.5, 5, 2.8, 4.7, -40, 40)),
                       (T, [(3.8, 8.6), (6.6, 11.2)])]),
            "R": (5.8, [(T, [(.8, 0), (.8, 10)]), (t, [(.8, 0), (3.2, 0)] + _arc(3.2, 2.6, 2., 2.6, -90, 90)[1:] + [(.8, 5.2)]),
                        (T, _arc(3.2, 2.6, 1.7, 2.3, -50, 50)), (T, [(2.8, 5.2), (5.4, 10)])]),
            "S": (5., [(t, _arc(2.5, 2.5, 2.1, 2.5, -20, -270, 10) + _arc(2.5, 7.5, 2.2, 2.5, -90, 160, 10)[1:]),
                       (T, [(1.1, 1.6), (1.6, 3.6), (3.4, 5.4), (4., 7.6)])]),
            "T": (6., [(T, [(3, 0), (3, 10)]), (t, [(.2, 1.2), (.2, 0), (5.8, 0), (5.8, 1.2)])]),
            "U": (6.6, [(T, [(.8, 0), (.8, 7.)] + _arc(3.3, 7., 2.5, 3., 180, 90, 8)[1:]),
                        (t, _arc(3.3, 7., 2.5, 3., 90, 0, 8) + [(5.8, 0)])]),
            "V": (6.4, [(T, [(.3, 0), (3.2, 10)]), (t, [(3.2, 10), (6.1, 0)])]),
            "W": (9., [(T, [(.3, 0), (2.5, 10)]), (t, [(2.5, 10), (4.5, 1)]), (T, [(4.5, 1), (6.5, 10)]), (t, [(6.5, 10), (8.7, 0)])]),
            "X": (6., [(T, [(.4, 0), (5.6, 10)]), (t, [(5.6, 0), (.4, 10)])]),
            "Y": (6., [(T, [(.4, 0), (3, 5)]), (t, [(5.6, 0), (3, 5)]), (T, [(3, 5), (3, 10)])]),
            "Z": (5.6, [(t, [(.6, 1.2), (.6, 0), (5., 0)]), (T, [(5., 0), (.6, 10)]), (t, [(.6, 10), (5.2, 10), (5.2, 8.6)])]),
            "0": (5.4, [(t, _arc(2.7, 5, 2.3, 5, 0, 360, 22)), (T, _arc(2.7, 5, 2., 4.6, 150, 210)), (T, _arc(2.7, 5, 2., 4.6, -30, 30))]),
            "1": (3.8, [(T, [(2.2, 0), (2.2, 10)]), (t, [(.6, 1.8), (2.2, 0)])]),
            "2": (5., [(t, _arc(2.5, 2.7, 2.1, 2.5, 200, 360, 9)), (T, _arc(2.5, 2.7, 2.1, 2.5, 0, 60, 4)[:-1] + [(.4, 10)]), (t, [(.4, 10), (4.7, 10)])]),
            "3": (5., [(t, _arc(2.4, 2.5, 2., 2.4, 200, 450, 10)), (t, _arc(2.4, 7.4, 2.3, 2.6, -90, 160, 10)), (T, _arc(2.4, 7.4, 2., 2.3, -40, 40, 5))]),
            "4": (5.4, [(t, [(3.8, 0), (.3, 7), (5.2, 7)]), (T, [(3.8, 0), (3.8, 10)])]),
            "5": (5., [(t, [(4.4, 0), (1.2, 0), (.9, 4.4)]), (t, _arc(2.4, 7., 2.3, 3., -120, 150, 12)), (T, _arc(2.4, 7., 2., 2.7, -40, 40, 5))]),
            "6": (5.2, [(t, _arc(2.7, 6.8, 2.2, 3.2, 0, 360, 16)), (T, [(4.2, .4), (1.6, 2.6), (.5, 6.8)])]),
            "7": (5., [(t, [(.4, 1.2), (.4, 0), (4.8, 0)]), (T, [(4.8, 0), (1.8, 10)])]),
            "8": (5., [(t, _arc(2.5, 2.5, 1.9, 2.5, 0, 360, 14)), (t, _arc(2.5, 7.4, 2.3, 2.6, 0, 360, 16)), (T, [(1., 1.6), (4.1, 8.8)])]),
            "9": (5.2, [(t, _arc(2.5, 3.2, 2.2, 3.2, 0, 360, 16)), (T, [(4.7, 3.2), (3.6, 7.4), (1., 9.6)])]),
            ".": (2., [(T, [(1, 9.3), (1, 10)])]),
            ",": (2., [(T, [(1.2, 9.2), (1.2, 10), (.6, 11.4)])]),
            "-": (3.6, [(T, [(.5, 6), (3.1, 6)])]),
            "'": (1.8, [(T, [(.9, 0), (.9, 2.6)])]),
            "&": (6.4, [(t, [(6, 10), (1.8, 3.6)] + _arc(2.8, 2.2, 1.6, 2.2, 180, 360, 8) + [(.9, 7)]
                        + _arc(2.6, 7.8, 2.1, 2.2, 180, 60, 6)), (T, [(5.8, 5.6), (3.7, 9.4)])]),
            "%": (6.4, [(t, _arc(1.6, 2.2, 1.3, 2, 0, 360, 10)), (t, _arc(4.8, 7.8, 1.3, 2, 0, 360, 10)), (T, [(5.4, 0), (1, 10)])]),
            "/": (4., [(T, [(3.6, 0), (.4, 10)])]),
            ":": (2., [(T, [(1, 3.4), (1, 4.1)]), (T, [(1, 9.3), (1, 10)])]),
            "·": (3., [(T, [(1.5, 4.8), (1.5, 5.4)])]),
            "*": (5., [(T, [(2.5, 1.5), (2.5, 7.5)]), (t, [(0, 4.5), (5, 4.5)]), (t, [(.8, 2.2), (4.2, 6.8)]), (t, [(4.2, 2.2), (.8, 6.8)])]),
            "#": (5.4, [(t, [(1.8, 1), (1.2, 9)]), (t, [(4.2, 1), (3.6, 9)]), (t, [(.4, 3.6), (5, 3.6)]), (t, [(.2, 6.6), (4.8, 6.6)])]),
            "$": (5., [(t, _arc(2.5, 3, 2.1, 2, -20, -270, 10) + _arc(2.5, 7, 2.2, 2, -90, 160, 10)[1:]),
                       (T, [(1.1, 2.), (3.6, 5.6), (4., 7.2)]), (t, [(2.5, -.6), (2.5, 10.6)])]),
        }
        return G


    _GLC = {}


    def letters(s, cx, y, cap, warp=None, track=1.):
        """Roman capitals centred on cx with the cap line at y, cap px tall. Returns (thick, thin)
        polyline lists. warp(x) -> dy bends the baseline (for ribbons)."""
        G = _GLC.get("g") or _GLC.setdefault("g", _glyphs())
        k = cap / 10.
        s = s.upper()
        width = sum(G.get(ch, G[" "])[0] + track for ch in s) - track
        x = cx - width * k / 2
        thick, thin = [], []
        serif = cap * .14
        for ch in s:
            adv, strokes = G.get(ch, G[" "])
            for kind, pts in strokes:
                q = [(x + px * k, y + py * k) for px, py in pts]
                if warp:
                    q = [(qx, qy + warp(qx)) for qx, qy in q]
                (thick if kind == "T" else thin).append(q)
                # bracketed serifs at the ends of straight stems lying on the cap or base line
                if len(pts) == 2 or kind == "T":
                    for (px, py), (ox, oy) in ((pts[0], pts[1]), (pts[-1], pts[-2])):
                        if (py <= .05 or py >= 9.95) and abs(px - ox) < 3.5 and abs(py - oy) > 2:
                            sx, sy = x + px * k, y + py * k + (warp(x + px * k) if warp else 0)
                            thin.append([(sx - serif, sy), (sx + serif, sy)])
            x += (adv + track) * k
        return thick, thin


    def letter_svg(thick, thin, cap):
        tw = 1.5 if cap >= 10 else 1.
        o = []
        if thick:
            o.append(f'<path d="{"".join(C._d(p, False, .05) for p in thick)}" fill="none" stroke="#000" stroke-width="{_N(tw)}" stroke-linecap="butt"/>')
        if thin:
            o.append(f'<path d="{"".join(C._d(p, False, .05) for p in thin)}" fill="none" stroke="#000" stroke-width=".5"/>')
        return "".join(o)


    def text_width(s, cap, track=1.):
        G = _GLC.get("g") or _GLC.setdefault("g", _glyphs())
        return (sum(G.get(ch, G[" "])[0] + track for ch in s.upper()) - track) * cap / 10.


    # ----------------------------------------------------------------------------------------------
    # the ribbon banner: a lettered face, folds turned under in shadow, swallow-tailed ends
    # ----------------------------------------------------------------------------------------------

    def banner(st, cx, cy, w, h, text, arch=.05, cap=None):
        """A ribbon banner about w wide; face h tall arched by arch*w; ends fold back under (dark,
        finely cut) and fly out as swallow tails ribbed with fine silk lines. Returns svg."""
        cv = C.Canvas()
        fw = w * .74
        x0, x1 = cx - fw / 2, cx + fw / 2

        def yc(x):
            t = (x - x0) / fw
            return cy - arch * w * _m.sin(_PI * min(1, max(0, t)))
        tail_w = w * .13
        o = []
        for side in (-1, 1):
            ex = x1 if side > 0 else x0
            ey = yc(ex)
            # the tail: behind the face, dropped a little, ending in a swallow-tail notch
            tx0 = ex - side * tail_w * .35
            tx1 = ex + side * tail_w
            dy = h * .45
            top0, bot0 = (tx0, ey - h / 2 + dy), (tx0, ey + h / 2 + dy)
            top1, bot1 = (tx1 + side * h * .2, ey - h / 2 + dy - h * .25), (tx1, ey + h / 2 + dy + h * .1)
            notch = (tx1 - side * h * .55, ey + dy - h * .05)
            tail = [top0, top1, notch, bot1, bot0]
            st.occupy(tail)
            cv.obj([tail], 1.)
            # silk ribs: fine lines along the tail, denser toward its lower edge
            for k in range(1, 9):
                f = k / 9.
                if f < .3 and k % 2:
                    continue
                a = _lerp(top0, bot0, f)
                b = _lerp(top1, bot1, f)
                if f > .45:
                    b = _lerp(b, notch, (f - .45) * 1.2)
                cv.hair([a, b])
            # the fold turned under: a dark triangle where the face meets the tail
            fold = [(ex, ey - h / 2), (ex, ey + h / 2), (tx0, ey + h / 2 + dy), (tx0, ey - h / 2 + dy)]
            cv.obj([fold], 1.)
            cv.hair(C.hatch_poly(fold, 45 * side, 1.5))
            cv.line(C.hatch_poly(fold, -45 * side, 3.))
        # the face
        n = 40
        top = [(x0 + fw * i / n, yc(x0 + fw * i / n) - h / 2) for i in range(n + 1)]
        bot = [(x0 + fw * i / n, yc(x0 + fw * i / n) + h / 2) for i in range(n + 1)]
        face = top + bot[::-1]
        st.occupy(face)
        cv.obj([face], 1.)
        cv.hair([[(x, y + 1.5) for x, y in top]])
        cv.hair([[(x, y - 1.5) for x, y in bot]])
        # shading rolling under at both ends of the face
        for side in (-1, 1):
            for k in range(10):
                x = (x0 + 1 + k * 1.5) if side < 0 else (x1 - 1 - k * 1.5)
                if k > 6 and k % 2:
                    continue
                yy = yc(x)
                cv.hair([(x, yy - h / 2 + 2.2), (x, yy + h / 2 - 2.2)])
        o.append(cv.svg())
        if text:
            cap = cap or min(h * .56, 11.)
            tw = text_width(text, cap)
            avail = fw - 34
            if tw > avail:
                cap *= avail / tw
            th, tn = letters(text, cx, cy - cap / 2, cap, lambda x: yc(x) - cy)
            o.append(letter_svg(th, tn, cap))
        return "".join(o)


    # ----------------------------------------------------------------------------------------------
    # the pedestal: knurled bars, a tablet with an engraved legend, scroll panels on matte
    # ----------------------------------------------------------------------------------------------

    def knurl_bar(o, x, y, w, h):
        """A turned, knurled rod: white highlight along the top, 45-degree knurling, a black belly."""
        r = h / 2
        body = (f"M{_N(x + r)},{_N(y)}h{_N(w - 2 * r)}a{_N(r)},{_N(r)} 0 0,1 0,{_N(h)}"
                f"h{_N(-(w - 2 * r))}a{_N(r)},{_N(r)} 0 0,1 0,{_N(-h)}z")
        o.append(f'<path d="{body}" fill="#fff" stroke="#000" stroke-width="1"/>')
        band = [(x + r * .7, y + h * .3), (x + w - r * .7, y + h * .3), (x + w - r * .7, y + h * .72), (x + r * .7, y + h * .72)]
        o.append(f'<path d="{"".join(C._d(p, False, 0) for p in C.hatch_poly(band, 45, 2.))}" stroke="#000" stroke-width=".5"/>')
        o.append(f'<path d="{"".join(C._d(p, False, 0) for p in C.hatch_poly(band, -45, 3.))}" stroke="#000" stroke-width=".5"/>')
        yb = y + h * .78
        o.append(f'<path d="M{_N(x + r * .6)},{_N(yb)}h{_N(w - r * 1.2)}v{_N(h * .12)}h{_N(-w + r * 1.2)}z" fill="#000"/>')
        o.append(f'<path d="M{_N(x + r)},{_N(y + h * .16)}h{_N(w - 2 * r)}" stroke="#000" stroke-width=".5"/>')


    def plate_doc(w, h, body):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" class="korn codex b5" width="{_N(w)}" height="{_N(h)}" '
                f'viewBox="0 0 {_N(w)} {_N(h)}" fill="none" stroke="#000" stroke-width=".5" '
                f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><defs>{matte_defs()}{C.codex_defs()[6:-7]}</defs>'
                + body + "</svg>")


    def clip_rect(cid, x, y, w, h, body):
        return (f'<clipPath id="{cid}"><path d="M{_N(x)},{_N(y)}h{_N(w)}v{_N(h)}h{_N(-w)}z"/></clipPath>'
                f'<g clip-path="url(#{cid})">{body}</g>')
    # ----------------------------------------------------------------------------------------------
    # the composition: a bordered panel of fine scroll on matte round an inlaid medallion, by height
    # ----------------------------------------------------------------------------------------------

    def crest_leaves(st, cv, x, y, size, up=True, seed=0):
        """Half an anthemion on the centre line (the other half comes from the mirror): three acanthus
        leaves fanning from (x, y), the inner one tall, the outer ones rolling outward."""
        rng = _r.Random(seed)
        base = -_PI / 2 if up else _PI / 2
        sd = 1 if up else -1
        for k, (da, L, b) in enumerate(((1.25, .62, -.9), (.78, .82, -.7), (.3, 1., -.35))):
            a = base - sd * da
            leaf(st, cv, x - 1, y, a, size * L, size * L * .3, b * sd, -2.2 * sd, 2 + (k == 2), -sd, rng.randrange(1 << 20))


    def _sources_tall(P, w, top, bot, mx, my, ma, mb, rng, ix=6.):
        """The main stems of one half, by composition variant P['stems'] (0-3), so no two pages share
        a skeleton: 0 a stem from under the banner up the side into a great curl plus one along the
        top; 1 stems climbing from the lower corner and falling from the shoulder; 2 one great S from
        the foot to the top corner; 3 a fountain from the pedestal, one stem low and one tall."""
        cx = w / 2
        strip = cx - ma - ix
        H = bot - top
        v = P.get("stems", 0) % 4
        if v == 0:
            r1 = min(strip * .42, H * .16)
            r2 = min(strip * .36, (my - mb - top) * .9, H * .14)
            return [
                ((cx - 1, bot - 3), _PI, r1, 1, {"via": [(cx - ma * .55, bot - 7), (ix + strip * .3, bot - H * .2),
                                                         (ix + strip * .36, my + H * .02)], "turns": 1.6}),
                ((cx - 1, top + 3), _PI, r2, -1, {"via": [(cx - ma * .5, top + 8), (ix + strip * .55, top + H * .1),
                                                          (ix + strip * .3, top + H * .26)], "turns": 1.5})]
        if v == 1:
            r1 = min(strip * .4, H * .15)
            r2 = min(strip * .38, H * .14)
            return [
                ((ix + 3, bot - 3), -_PI / 2, r1, 1, {"via": [(ix + strip * .15, bot - H * .3), (ix + strip * .2, top + H * .32),
                                                              (ix + strip * .55, top + H * .16)], "turns": 1.6}),
                ((cx - ma * .9, my - mb * .3), _PI * .75, r2, -1, {"via": [(ix + strip * .7, my + H * .05),
                                                                            (ix + strip * .55, bot - H * .22)], "turns": 1.5})]
        if v == 2:
            r1 = min(strip * .44, H * .17)
            return [
                ((cx - 1, bot - 3), _PI, r1, -1, {"via": [(cx - ma * .7, bot - 6), (ix + strip * .25, bot - H * .14),
                                                          (ix + strip * .7, my + H * .1), (ix + strip * .6, top + H * .3),
                                                          (ix + strip * .3, top + H * .18)], "turns": 1.7}),
                ((cx - 1, top + 3), _PI, r1 * .55, 1, {"via": [(cx - ma * .45, top + 6), (ix + strip * .8, top + H * .06)],
                                                        "turns": 1.4})]
        r1 = min(strip * .46, H * .17)
        r2 = min(strip * .34, H * .12)
        return [
            ((cx - 1, bot - 3), _PI, r1, 1, {"via": [(cx - ma * .8, bot - 5), (ix + strip * .45, bot - H * .12)], "turns": 1.7}),
            ((cx - ma * .4, bot - 4), _PI * 1.1, r2, -1, {"via": [(ix + strip * .8, my + H * .12), (ix + strip * .75, my - H * .1),
                                                                 (ix + strip * .5, top + H * .14)], "turns": 1.6})]


    def _sources_medium(P, w, top, bot, mx, my, ma, mb, rng, ix=6.):
        cx = w / 2
        ih = bot - top
        strip = cx - ma - ix
        v = P.get("stems", 0) % 3
        if v == 0:
            r1 = min(ih * .36, strip * .3)
            r2 = min(ih * .28, strip * .26)
            return [((cx - 1, bot - 2.5), _PI, r1, 1, {"via": [(cx - ma * .7, bot - 4), (ix + strip * .55, my + ih * .3),
                                                                (ix + strip * .42, my - ih * .02)], "turns": 1.6}),
                    ((cx - 1, top + 2.5), _PI, r2, -1, {"via": [(cx - ma * .6, top + 4), (ix + strip * .2, top + ih * .2)],
                                                         "turns": 1.5})]
        if v == 1:
            r1 = min(ih * .34, strip * .28)
            return [((cx - ma - 1, my), _PI, r1, -1, {"via": [(ix + strip * .7, my + ih * .25), (ix + strip * .25, my + ih * .1)],
                                                      "turns": 1.6}),
                    ((cx - ma * .5, top + ih * .08), _PI * 1.05, r1 * .8, 1, {"via": [(ix + strip * .75, top + ih * .12),
                                                                                     (ix + strip * .7, top + ih * .4)], "turns": 1.5})]
        r1 = min(ih * .4, strip * .32)
        return [((ix + 2, bot - 2), -_PI / 3, r1, 1, {"via": [(ix + strip * .3, my + ih * .1), (ix + strip * .55, top + ih * .25)],
                                                     "turns": 1.7}),
                ((cx - 1, bot - 2.5), _PI, r1 * .6, -1, {"via": [(cx - ma * .6, bot - 3), (ix + strip * .8, my + ih * .2)],
                                                           "turns": 1.5})]


    def compose(w, h, ctx, P):
        """P: scene(x, y, w, h, lod) -> svg; shape; legend; tablet; seed; figures(st, cv, g) (drawn in
        the mirrored half before the scroll grows, so they are reserved and mirrored); egg(st, g) ->
        svg drawn unmirrored on top; thai (bool)."""
        seed = P.get("seed", 1)
        rng = _r.Random(seed)
        st = Studio(w, h, seed)
        o = []
        cx = w / 2
        g = {"w": w, "h": h, "cx": cx}
        if h < 110:
            lod = 0
            ix, iy, iw, ih = 0, 0, w, h
            o.append(matte((0, 0, w, h)))
            bo = []
            ix, iy, iw, ih = border_rect(bo, None, 0, 0, w, h, True, 1.25)
            mb = ih / 2 - 1.5
            ma = min(mb * P.get("band_aspect", 1.9), w * .2)
            my = iy + ih / 2
            st.permit_rect(ix, iy, cx - .5, iy + ih)
            msvg, mo = medallion(st, P.get("shape_band", "oval"), cx, my, ma, mb, lambda x, y, fw, fh: P["scene"](x, y, fw, fh, 0),
                                 max(5., mb * .2))
            g.update(mx=cx, my=my, ma=ma, mb=mb, box=(ix, iy, iw, ih), lod=0)
            sc = Scroll(st, rng.randrange(1 << 20), rmin=max(4., ih * .085))
            if P.get("figures"):
                P["figures"](st, None, g)
            L = cx - ma - ix
            R0 = min(ih * .42, L * .3)
            sc.grow([((cx - ma + 2, my + ih * .12), _PI + .1, R0, 1, {"lead": L - R0 * 2.2, "lead_k": .0015})], 6)
            sc.infill(6)
            sc.clothe()
            sc.leaf_fill(lmax=10.)
            cid = _uidp("bl", w, h, seed)
            redo = (len(o), sc, cid, (ix, iy, iw, ih), None)
            o.append(_scroll_body(st, sc, P, g, cid, (ix, iy, iw, ih), None, 0.))
            o.append(msvg)
            o.extend(bo)
        elif h <= 260:
            lod = 1
            o.append(matte((0, 0, w, h)))
            bo = []
            ix, iy, iw, ih = border_rect(bo, None, 0, 0, w, h, True, 1.5)
            mb = ih / 2 - 2
            ma = min(mb * P.get("med_aspect", 1.25), w * .25)
            my = iy + ih / 2
            st.permit_rect(ix, iy, cx - .5, iy + ih)
            msvg, mo = medallion(st, P.get("shape_medium", P.get("shape", "oval")), cx, my, ma, mb, lambda x, y, fw, fh: P["scene"](x, y, fw, fh, 1))
            g.update(mx=cx, my=my, ma=ma, mb=mb, box=(ix, iy, iw, ih), lod=1)
            ban = ""
            if h >= 190 and P.get("legend"):
                bw = ma * 2.5
                bh = min(16., ih * .085)
                ban = banner(st, cx, my + mb * .9, bw, bh, P["legend"], .04)
            if P.get("figures"):
                P["figures"](st, None, g)
            sc = Scroll(st, rng.randrange(1 << 20), rmin=max(5., ih * .045))
            strip = cx - ma - ix
            r1 = min(ih * .36, strip * .3)
            r2 = min(ih * .28, strip * .26)
            sc.grow((P.get("sources_medium") or _sources_medium)(P, w, iy, iy + ih, cx, my, ma, mb, rng, ix), 7)
            sc.infill(10)
            sc.clothe()
            sc.leaf_fill(lmax=12.)
            cid = _uidp("md", w, h, seed)
            redo = (len(o), sc, cid, (ix, iy, iw, ih), None)
            o.append(_scroll_body(st, sc, P, g, cid, (ix, iy, iw, ih), None, 0.))
            o.append(msvg)
            o.append(ban)
            o.extend(bo)
        else:
            lod = 2
            ped_h = min(max(h * .15, 46.), 78.)
            top = 0.
            pan_h = h - ped_h
            o.append(matte((0, 0, w, h)))
            bo = []
            ix, iy, iw, ih = border_rect(bo, None, 0, 0, w, pan_h + 2, True, 1.5)
            mb = ih * .4
            ma = min(mb * P.get("med_aspect", .8), iw * .3)
            my = iy + ih * .44
            st.permit_rect(ix, iy, cx - .5, iy + ih)
            msvg, mo = medallion(st, P.get("shape", "oval"), cx, my, ma, mb, lambda x, y, fw, fh: P["scene"](x, y, fw, fh, 2))
            g.update(mx=cx, my=my, ma=ma, mb=mb, box=(ix, iy, iw, ih), lod=2)
            bw = ma * 2.7
            bh = min(18., ih * .05)
            ban = banner(st, cx, my + mb + bh * .2, bw, bh, P.get("legend", ""), .05)
            cvc = Cv()
            csz = min(my - mb - iy + 4, 34.)
            if P.get("crest"):
                crest_leaves(st, cvc, cx, my - mb - 1, csz * .8, True, seed)
                P["crest"](st, cvc, cx, my - mb - 1, csz)
                st.occupy(_ell(cx, my - mb - csz * .45, csz * .7, csz * .55, 24))
            else:
                crest_leaves(st, cvc, cx, my - mb - 1, csz, True, seed)
            if P.get("figures"):
                P["figures"](st, None, g)
            sc = Scroll(st, rng.randrange(1 << 20), rmin=max(6.5, ih * .021))
            sc.grow((P.get("sources_tall") or _sources_tall)(P, w, iy, iy + ih, cx, my, ma, mb, rng, ix), 8)
            sc.infill(14)
            sc.clothe()
            sc.leaf_fill(lmax=13., max_n=60)
            cid = _uidp("tl", w, h, seed)
            redo = (len(o), sc, cid, (ix, iy, iw, ih), cvc)
            o.append(_scroll_body(st, sc, P, g, cid, (ix, iy, iw, ih), cvc, 0.))
            o.append(msvg)
            o.append(ban)
            o.extend(bo)
            o.append(pedestal(w, pan_h, ped_h, P.get("tablet", ""), seed, P.get("tablet_fn")))
        if P.get("egg"):
            o.append(P["egg"](g))
        LIMIT = 194 * 1024
        tot = sum(len(x) for x in o) + 1800
        if tot > LIMIT:
            # over budget: drop the smallest leaves until the scroll sheds the excess
            k, sc, cid, box, cvc = redo
            body = o[k]
            ls = sc.leaf_lengths()
            frac = min(.8, (tot - LIMIT + 3000) / max(1., len(body) * .8))
            lmin = ls[min(len(ls) - 1, int(len(ls) * frac))] if ls else 0.
            o[k] = _scroll_body(st, sc, P, g, cid, box, cvc, lmin + .01)
        return plate_doc(w, h, "".join(o))


    def _scroll_body(st, sc, P, g, cid, box, cvc, lmin):
        ix, iy, iw, ih = box
        cv = Cv()
        if P.get("figures"):
            P["figures"](st, cv, g)
        sc.paint(cv, lmin)
        if cvc is not None:
            cv.extend(cvc)
        body = cv.svg()
        return clip_rect(cid, ix, iy, iw, ih, f'<g id="{cid}g">{body}</g><use href="#{cid}g" transform="translate({_N(g["w"])},0) scale(-1,1)"/>')


    def pedestal(w, y0, ph, text, seed, fn=None):
        """The base: a knurled cornice, a slab with a white tablet carrying the engraved legend between
        two matte panels of fine scroll, a heavier knurled bar, and a beaded plinth."""
        o = []
        kb = max(6., ph * .13)
        knurl_bar(o, 3, y0 + 1, w - 6, kb)
        sy = y0 + kb + 1
        sh = ph * .5
        o.append(f'<path d="M{_N(8)},{_N(sy)}h{_N(w - 16)}v{_N(sh)}h{_N(-w + 16)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
        # a shaded top face: the slab's lip catching light, then fine cuts deepening under it
        o.append(f'<path d="M{_N(9)},{_N(sy + 2.25)}h{_N(w - 18)}M{_N(9)},{_N(sy + 3.75)}h{_N(w - 18)}" stroke="#000" stroke-width=".5"{_CR}/>')
        o.append(f'<path d="M{_N(9)},{_N(sy + sh - 2)}h{_N(w - 18)}" stroke="#000" stroke-width="1.5"{_CR}/>')
        cap = min(sh * .42, 12.)
        tw = text_width(text, cap) if text else 60.
        tbw = w * .56 if fn else min(w * .62, tw + cap * 3.5)
        tx0 = (w - tbw) / 2
        ty0, tyh = sy + 5, sh - 9
        # side panels: matte with fine scroll growing from the tablet
        px0, px1 = 12., tx0 - 5
        st = Studio(w, y0 + ph + 4, seed + 17)
        st.permit_rect(px0, ty0, px1, ty0 + tyh)
        o.append(matte((px0, ty0, w - 2 * px0, tyh)))
        sc = Scroll(st, seed + 3, rmin=max(3.5, tyh * .16))
        R0 = tyh * .38
        sc.grow([((px1 - 1, ty0 + tyh * .62), _PI, R0, 1, {"lead": (px1 - px0) - R0 * 2.4, "lead_k": .002})], 5)
        sc.infill(4)
        sc.clothe()
        sc.leaf_fill(lmax=8.)
        cv = Cv()
        sc.paint(cv)
        body = cv.svg()
        cid = _uidp("pd", w, y0, seed)
        o.append(clip_rect(cid, px0, ty0, px1 - px0, tyh, f'<g id="{cid}g">{body}</g>') +
                 clip_rect(cid + "r", w - px1, ty0, px1 - px0, tyh, f'<use href="#{cid}g" transform="translate({_N(w)},0) scale(-1,1)"/>'))
        o.append(f'<path d="M{_N(px0)},{_N(ty0)}h{_N(px1 - px0)}v{_N(tyh)}h{_N(px0 - px1)}zM{_N(w - px1)},{_N(ty0)}h{_N(px1 - px0)}v{_N(tyh)}h{_N(px0 - px1)}z" stroke="#000" stroke-width=".5"/>')
        # the tablet: a white field with a gold-line double rule and engraved capitals
        o.append(f'<path d="M{_N(tx0)},{_N(ty0)}h{_N(tbw)}v{_N(tyh)}h{_N(-tbw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="M{_N(tx0 + 2)},{_N(ty0 + 2)}h{_N(tbw - 4)}v{_N(tyh - 4)}h{_N(-tbw + 4)}z" stroke="#000" stroke-width=".5"/>')
        if fn:
            o.append(fn(tx0 + 3, ty0 + 3, tbw - 6, tyh - 6))
        elif text:
            th, tn = letters(text, w / 2, ty0 + (tyh - cap) / 2, cap)
            o.append(letter_svg(th, tn, cap))
        by = sy + sh + 1
        kb2 = max(7., ph * .15)
        knurl_bar(o, 1, by, w - 2, kb2)
        py = by + kb2 + 1
        rest = y0 + ph - py
        if rest > 3:
            o.append(f'<path d="M0,{_N(py)}h{_N(w)}v{_N(rest)}h{_N(-w)}z" fill="#fff" stroke="none"/>')
            r = max(1., min(2., rest / 2 - .8))
            o.append(f'<path d="M0,{_N(py)}h{_N(w)}v{_N(rest)}h{_N(-w)}z" fill="#000" stroke="none"/>')
            o.append(bead_row([(r + 1, py + rest / 2), (w - r - 1, py + rest / 2)], r, 1., False))
            o.append(f'<path d="M0,{_N(py + .25)}h{_N(w)}M0,{_N(y0 + ph - .25)}h{_N(w)}" stroke="#000" stroke-width=".5"{_CR}/>')
        return "".join(o)

    # ----------------------------------------------------------------------------------------------
    # the copperplate scene kit: sky with modelled clouds, mountains, water, banks, firs, the heron
    # ----------------------------------------------------------------------------------------------

    def _gy(y, w=.5):
        """Snap a horizontal line of width w onto the device-pixel grid."""
        return _m.floor(y * 2) / 2 + (.25 if w == .5 else 0.)


    def _envelope(lobes, x0, x1, base, n=60):
        """Upper outline of a cumulus: the union of circles (cx, r) sitting on y=base."""
        top = []
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            y = base
            for (lx, ly, r) in lobes:
                d = x - lx
                if abs(d) < r:
                    y = min(y, ly - _m.sqrt(r * r - d * d))
            top.append((x, y))
        return top


    def cloud(cv, cx, base, wd, ht, rng, lit=-1):
        """A cumulus: a heap of rounded lobes, lit along the top with a broken fine edge, its underside
        modelled by lines that follow the lobes and close up into shade, a flat dark base."""
        k = max(3, int(wd / (ht * .9)))
        lobes = []
        for i in range(k):
            t = (i + .5) / k
            bump = _m.sin(_PI * t) ** .7
            r = ht * (.35 + .55 * bump) * rng.uniform(.8, 1.1)
            lobes.append((cx - wd / 2 + wd * t, base - r * .25, r))
        top = _envelope(lobes, cx - wd / 2 - ht * .2, cx + wd / 2 + ht * .2, base)
        poly = top + [(top[-1][0], base), (top[0][0], base)]
        poly = [p for p in poly]
        cv.obj([poly], 0)
        # lit edge: a fine broken line along the top
        seg = []
        for i, p in enumerate(top):
            if (i // 3) % 4 != 3:
                seg.append(p)
            elif len(seg) > 1:
                cv.hair(seg)
                seg = []
        if len(seg) > 1:
            cv.hair(seg)
        # body: contour lines following the top, dropped by steps, kept to the shadow side and base
        H = ht
        for j in range(1, int(H / 1.6)):
            d = j * 1.6
            line = []
            for (x, y) in top:
                yy = y + d
                if yy >= base - .6:
                    if len(line) > 1:
                        cv.hair(line)
                    line = []
                    continue
                # light from the upper `lit` side: shade grows toward the other side and down
                f = (x - cx) / (wd / 2) * -lit
                depth = (yy - (base - H)) / H
                if depth + .35 * f > .55:
                    line.append((x, yy))
                else:
                    if len(line) > 1:
                        cv.hair(line)
                    line = []
            if len(line) > 1:
                cv.hair(line)
        yb = _gy(base - 1.2, 1.)
        cv.line([(top[0][0] + ht * .3, yb), (top[-1][0] - ht * .3, yb)])
        return poly


    def ruled(thin, thick=()):
        """Background ruled lines (on the device grid) as raw paths: they sit under the layer that
        follows, whose white shapes hide them, so they need no clipping."""
        o = ""
        if thin:
            o += f'<path d="{"".join(thin)}" stroke="#000" stroke-width=".5"{_CR}/>'
        if thick:
            o += f'<path d="{"".join(thick)}" stroke="#000" stroke-width="1"{_CR}/>'
        return o


    def sky(cv, x0, y0, x1, y1, seed, clouds=3, sun=None, glow=0., dense=1.):
        """A copperplate sky from y0 down to the horizon y1: crisp ruled lines, darkest at the zenith
        (1 px at 2 px pitch), opening to .5 px at 2, then 3 px toward the horizon; lines part round
        the sun and stop at the clouds, which are modelled on top."""
        rng = _r.Random(seed)
        H = y1 - y0
        y = _gy(y0)
        thin, thick = [], []
        while y < y1:
            t = (y - y0) / H
            if t < .22 * dense:
                w_, pitch = 1., 2.
            elif t < .62:
                w_, pitch = .5, 2.
            else:
                w_, pitch = .5, 3.
            yy = _gy(y, w_)
            segs = []
            a, b = x0, x1
            if sun:
                sx, sy, sr = sun
                dy = yy - sy
                rr = sr + glow
                if abs(dy) < rr:
                    dx = _m.sqrt(rr * rr - dy * dy)
                    segs = [(a, sx - dx), (sx + dx, b)]
            if not segs:
                segs = [(a, b)]
            for (p, q) in segs:
                if q - p > .8:
                    (thick if w_ == 1. else thin).append(f"M{_N(p)},{_N(yy)}H{_N(q)}")
            y += pitch
        out = ruled(thin, thick)
        if sun:
            sx, sy, sr = sun
            # the sun: rays in alternating lengths, the disc engraved with fine concentric cuts
            cv.obj([], 0)
            for i in range(36):
                a = _TAU * i / 36
                r2 = sr + glow * (.95 if i % 2 else .6)
                cv.hair([(sx + _m.cos(a) * (sr + 2), sy + _m.sin(a) * (sr + 2)), (sx + _m.cos(a) * r2, sy + _m.sin(a) * r2)])
            disc = _ell(sx, sy, sr, sr, 32)[:-1]
            cv.obj([disc], .5)
            q = sr - 1.5
            while q > 1:
                cv.hair(_ell(sx, sy, q, q, max(12, int(q * 4)), .3, _PI + .3))
                q -= 1.5
        polys = []
        for i in range(clouds):
            wd = (x1 - x0) * rng.uniform(.22, .4)
            cx = x0 + (x1 - x0) * (i + rng.uniform(.25, .75)) / clouds
            base = y0 + H * rng.uniform(.35, .75)
            polys.append(cloud(cv, cx, base, wd, wd * rng.uniform(.24, .32), rng))
        return out


    def _ridge(xa, ya, xb, yb, rough, rng, depth=5):
        pts = [(xa, ya), (xb, yb)]
        for d in range(depth):
            new = [pts[0]]
            for i in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                L = _m.hypot(bx - ax, by - ay)
                mx, my = (ax + bx) / 2, (ay + by) / 2
                off = rng.uniform(-1, 1) * L * rough
                nx, ny = -(by - ay) / (L or 1), (bx - ax) / (L or 1)
                new += [(mx + nx * off, my + ny * off), (bx, by)]
            pts = new
        return pts


    def mountain(cv, cx, base, peak, hw, seed, snow=.5, lit=-1, skew=0.):
        """A volcanic peak (Hood): jagged ridges, a lit snow face of broken fall-line strokes, the shadow
        face in fall-line hachures with a 45-degree cross-hatch layered in its depth, forested skirts."""
        rng = _r.Random(seed)
        H = base - peak
        px = cx + skew * hw
        left = _ridge(cx - hw, base, px - hw * .03, peak, .05, rng)
        right = _ridge(px + hw * .03, peak, cx + hw, base, .05, rng)
        poly = left + [(px, peak - 1.2)] + right
        cv.obj([poly], .5)
        # the central ridge splitting light from shade
        ridge = _ridge(px, peak, cx + hw * .12 * -lit, base, .06, rng, 4)
        sh_side = right if lit < 0 else left[::-1]
        shade = ridge + sh_side[::-1] if lit < 0 else ridge + sh_side[::-1]
        # fall-line hachures on the shadow face (each from the ridge outward and down)
        hs = []
        for i in range(1, 60):
            t = i / 60
            a = _lerp(ridge[0], ridge[-1], t)
            bx = cx + (-lit) * hw * t ** .9
            by = peak + H * t
            # follow the slope down-out
            n = 6
            line = [(a[0] + (bx - a[0]) * k / n, a[1] + (by - a[1]) * k / n + H * .06 * _m.sin(_PI * k / n)) for k in range(n + 1)]
            hs.append(line)
        cv.hair(hs)
        # cross-hatch deepening the lower shadow
        lowsh = [(px, peak + H * .45)] + [(cx + (-lit) * hw * u, peak + H * (.45 + .55 * u)) for u in (.4, .8, 1.)] + [(px + (-lit) * hw * .1, base)]
        cv.hair(C.hatch_poly(lowsh, 45 * lit, 3.))
        # the snow face: broken strokes down the fall line, thinning to bare rock below the snowline
        sn = []
        for i in range(1, 40):
            t = i / 40
            x_top = px + lit * hw * .9 * t * .3
            for j in range(5):
                u0 = t * .3 + j * .14 + rng.uniform(0, .06)
                u1 = u0 + rng.uniform(.04, .09)
                if u1 > snow + rng.uniform(-.05, .08):
                    break
                pa = (px + lit * hw * t * u0 * 2.2, peak + H * u0)
                pb = (px + lit * hw * t * u1 * 2.2, peak + H * u1)
                sn.append([pa, pb])
        cv.hair(sn)
        # forested skirts: a dark band of short vertical strokes below the snowline
        sk = []
        for i in range(int(hw * 2 / 3.)):
            x = cx - hw + i * 3.
            u = abs(x - px) / hw
            ytop = peak + H * (snow + .12 + .2 * u) + rng.uniform(-1.5, 1.5)
            yb = base - .5
            if yb - ytop > 1:
                sk.append([(x, ytop), (x, yb)])
        cv.hair(sk)
        return poly


    def water(cv, x0, y0, x1, y1, seed, refl=(), calm=1.):
        """Water from the far shore y0 to y1: ruled ripples on the device grid, tight and long near
        the shore, opening and breaking into short strokes toward the viewer; reflections (x, half
        width) darken as broken stacks of 1 px dashes."""
        rng = _r.Random(seed)
        H = y1 - y0
        y = _gy(y0 + .5)
        thin, thick = [], []
        while y < y1:
            t = (y - y0) / H
            pitch = 1.5 if t < .2 else (2. if t < .6 else 3.)
            dash = (30, 70) if t < .2 else ((10, 34) if t < .6 else (5, 18))
            gap = (1., 3.) if t < .2 else ((2., 5.) if t < .6 else (2., 7.))
            x = x0 - rng.uniform(0, dash[1])
            while x < x1:
                L = rng.uniform(*dash) * calm
                a, b = max(x, x0), min(x + L, x1)
                if b - a > .8:
                    thin.append(f"M{_N(a)},{_N(y)}H{_N(b)}")
                x += L + rng.uniform(*gap)
            for (rx, rw) in refl:
                j = rng.uniform(-1.5, 1.5) * (1 + t * 2)
                thick.append(f"M{_N(rx - rw + j)},{_N(_gy(y, 1.))}H{_N(rx + rw + j)}")
            y += pitch
        return ruled(thin, thick)


    def firline(cv, x0, x1, base, h, seed, step=3.2):
        """A far bank of firs: a jagged silhouette of small spires, ruled close, its crest left bright."""
        rng = _r.Random(seed)
        pts = [(x0 - 2, base + 1)]
        x = x0 - 2
        while x < x1 + 2:
            th = h * rng.uniform(.55, 1.)
            pts += [(x, base - th * .35), (x + step * .5, base - th), (x + step, base - th * .35)]
            x += step * rng.uniform(.8, 1.2)
        pts += [(x1 + 2, base + 1)]
        cv.obj([pts], .5)
        yy = _gy(base - h * .3)
        lines = []
        while yy < base + 1:
            lines.append([(x0 - 2, yy), (x1 + 2, yy)])
            yy += 1.5
        cv.hair(lines)
        return pts


    def fir(cv, x, base, h, rng, lit=-1):
        """A Douglas fir in drooping tiers, painted bottom-up; every tier ruled dark below with needle
        strokes fanning on its lit side and a white upper edge."""
        tiers = max(3, int(h / 7.5))
        w = h * .3
        top = base - h
        trunk = [(x - w * .06, base - h * .14), (x + w * .06, base - h * .14), (x + w * .08, base), (x - w * .08, base)]
        cv.obj([trunk], .5)
        cv.hair([[(x + w * .03, base - h * .12), (x + w * .03, base)]])
        for i in range(tiers - 1, -1, -1):
            t0, t1 = i / tiers, (i + 1) / tiers
            ya = top + (base - h * .12 - top) * t0
            yb = top + (base - h * .12 - top) * t1
            wi = w * (.15 + .85 * t1 ** .9) * rng.uniform(.88, 1.08)
            dr = (yb - ya) * .5
            side = []
            for k in range(1, 6):
                u = k / 5
                side.append((x + wi * u, ya + (yb - ya) * u * .8 + dr * u ** 3))
            side.append((x + wi * .7, yb + dr * .3))
            side.append((x + wi * .35, yb - (yb - ya) * .05))
            shape = [(x, ya - (yb - ya) * .1)] + side + [(x, yb - (yb - ya) * .15)] + [(2 * x - px, py) for px, py in reversed(side)]
            cv.obj([shape], .5)
            y = _gy(ya + (yb - ya) * .45)
            ls = []
            while y < yb + dr:
                ls.append([(x - wi - 1, y), (x + wi + 1, y)])
                y += 2.
            dark = [q for q in ls]
            cv.hair([[(max(a[0], x - wi * (1.05 - .2 * lit)), a[1]), (min(b[0], x + wi * (1.05 + .2 * lit)), b[1])] for a, b in dark])
            nd = []
            for k in range(1, 5):
                u = k / 5
                px, py = x + lit * wi * u * .9, ya + (yb - ya) * u * .8 + dr * u ** 3
                nd.append([(x + lit * wi * u * .3, ya + (yb - ya) * (u * .3 + .2)), (px, py - 1)])
            cv.hair(nd)


    def heron(cv, x, y, s, face=1):
        """A great blue heron from Sauvie Island standing in the shallows (feet at (x, y)), about
        46*s tall, facing right if face > 0: S-neck carved as a round form with feather bulino down its
        back, a black crown stripe trailing a plume, dagger bill, folded wing in long sweeping plumes,
        breast plumes hanging, long jointed legs."""
        f = face
        P = lambda u, v: (x + f * u * s, y - v * s)
        sw = max(.5, s * .5)
        # legs (behind the body)
        for (hx, kx, fx_) in ((-1.5, -2.5, -3.5), (1.5, 1., 2.5)):
            cv.obj([[P(hx - .5, 17), P(hx + .5, 17), P(kx + .45, 8), P(fx_ + .4, 0), P(fx_ - .4, 0), P(kx - .45, 8)]], .5)
            cv.hair([P(fx_, 0), P(fx_ + 3.5, -.3)])
            cv.hair([P(fx_, 0), P(fx_ - 2.5, .4)])
        body = [P(-18, 15), P(-12, 20.5), P(-4, 25.5), P(4, 27.6), P(9, 26.8), P(11.2, 23.5), P(9.5, 19.5), P(3, 16.4),
                P(-6, 15.6), P(-13, 14.8)]
        cv.obj([body], 1.)
        # the folded wing: long plumes sweeping from the shoulder to beyond the tail, closer below
        for k in range(9):
            v0 = 25.5 - k * 1.25
            cv.hair([P(7.5 - k * .6, v0), P(-2, v0 - 1.8 - k * .1), P(-12, v0 - 4.5 - k * .15), P(-18.5 + k * .3, 15.2 - k * .05)])
        cv.line([P(9, 22.5), P(0, 19.8), P(-10, 17.4), P(-18, 15.2)])
        # breast plumes hanging from the throat
        for k in range(6):
            u = 8.2 + k * .5
            cv.hair([P(u, 26 - k * .4), P(u + .3, 20.5 - k * .5)])
        # neck: an S ribbon, shaded down its back
        spine = [P(7.5, 25.5), P(10.5, 29), P(9.6, 32.5), P(7.8, 35.5), P(8.6, 39), P(11.6, 41.6)]
        sp = _catmull(spine, 1.)
        wn = [sw * 2.4 * (1 - .35 * i / (len(sp) - 1)) for i in range(len(sp))]
        R = C._Rib(sp, wn, wn)
        cv.obj([R.outline()], .5)
        back = -1 if f > 0 else 1
        for sv in (.35, .6, .82):
            cv.hair(R.contour(back * sv, .05, .95))
        cv.line(R.contour(-back * .4, .25, .75))
        # head with the black crown stripe and the trailing plume
        head = [P(10, 40.6), P(11, 43.4), P(13.6, 44.6), P(16.4, 44.1), P(17.4, 42.8), P(16, 41.2), P(12.5, 40.2)]
        cv.obj([head], .5)
        cv.heavy([P(10.8, 43.8), P(13.8, 44.5), P(16.2, 44)])
        cv.line([P(11, 43.9), P(6, 45.4), P(2.5, 45.1)])
        cv.hair([P(11, 43.3), P(5.5, 44.1)])
        bill = [P(16.8, 43.4), P(28, 42.2), P(16.8, 41.6)]
        cv.obj([bill], .5)
        cv.hair([P(17, 42.5), P(26, 42.2)])
        cv.obj([_ell(*P(15, 42.8), .9 * s / 1.2 + .3, .9 * s / 1.2 + .3, 8)[:-1]], 0)
        cv.line(_ell(*P(15, 42.8), .45, .45, 6))
    return _types.SimpleNamespace(**{k: v for k, v in locals().items() if not k.startswith('__')})


ST5 = _studio5()
# ==== END STUDIO ENGINE =========================================================================


# ==== PAGE: doodles-03 ============================================================

_n = C._n
_d = C._d
PI = math.pi

# ----------------------------------------------------------------------------------------------
# data from the page (falls back to today's measured numbers)
# ----------------------------------------------------------------------------------------------


def _data(ctx):
    s = (ctx or {}).get("sample", "") or ""
    got, usual_now, usual_month = 1.31, 2.1, 5.6
    m = re.search(r"([\d.]+)\s*in in the jar", s)
    if m:
        got = float(m.group(1))
    m = re.search(r"behind the ([\d.]+) in|ahead of the ([\d.]+) in", s)
    if m:
        usual_now = float(m.group(1) or m.group(2))
    m = re.search(r"usual for \w+ ([\d.]+)", s)
    if m:
        usual_month = float(m.group(1))
    days = [float(x) for x in re.findall(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([\d.]+)", s)] or [.02, .04, .14, .48, .39]
    return got, usual_now, max(usual_month, got, usual_now), days[-6:]


# ----------------------------------------------------------------------------------------------
# small shapes
# ----------------------------------------------------------------------------------------------


def _ell(cx, cy, rx, ry, n=32, rot=0.):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        t = 2 * PI * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def _closed(p):
    return p + [p[0]]


def _drop(cx, cy, r, n=36):
    """A raindrop, tip up, about 2.9 r tall."""
    pts = []
    for i in range(n):
        t = 2 * PI * i / n
        pts.append((cx + 1.25 * r * math.sin(t) * math.sin(t / 2), cy - 1.45 * r * math.cos(t) + .35 * r))
    return pts


def _keep(lines, f):
    return [l for l in lines if f(((l[0][0] + l[-1][0]) / 2, (l[0][1] + l[-1][1]) / 2))]


def _drop_obj(cv, cx, cy, r):
    p = _drop(cx, cy, r)
    cv.obj([p], 1. if r > 2.2 else .5)
    if r > 1.6:
        cv.hair(_keep(C.hatch_poly(p, 70, 1.5), lambda m: m[0] > cx - r * .15 or m[1] > cy + r * .7))
    if r > 5:
        for k in (.72, .5):
            q = _drop(cx + r * (1 - k) * .45, cy + r * (1 - k) * .5, r * k)
            cv.hair([q[4:30]])
    return p


def _hline(poly, y):
    return C.hatch_poly(poly, 0, 1e6, y)


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------


def _cloud(cx, cy, w, h, rng):
    """Billowed top, flat-ish bottom: outline polygon and a top-envelope function."""
    k = max(4, int(w / (h * .6)))
    circles = []
    for i in range(k):
        t = (i + .5) / k
        r = h * (.3 + .45 * math.sin(PI * t) ** .8) * rng.uniform(.8, 1.12)
        circles.append((cx - w / 2 + w * t + rng.uniform(-2, 2), cy + h * .5 - r * .9, r))
    base = cy + h * .5

    def top(x):
        ys = [c[1] - math.sqrt(max(0., c[2] ** 2 - (x - c[0]) ** 2)) for c in circles if abs(x - c[0]) < c[2]]
        return min(min(ys), base - 1) if ys else None
    xs = [x for x in [cx - w / 2 - h + i * .5 for i in range(int((w + 2 * h) * 2))] if top(x) is not None]
    tp = [(x, top(x)) for x in xs]
    bt = [(x, base + .6 * math.sin(x * .3)) for x in xs[::-1]]
    return C._dp(tp, .15) + C._dp(bt, .15), circles, top


def _shade_cloud(cv, poly, circles, top, cy, h):
    """Lit rim under each billow's top, ruled tone below it, dense at the base; billow contours."""
    base = cy + h * .5
    xs0 = min(p[0] for p in poly)
    xs1 = max(p[0] for p in poly)
    lines = []
    y = base - 1.
    while y > base - h * 1.2:
        f = (base - y) / h
        rim = 3.5 + 3 * f
        seg = []
        x = xs0
        while x <= xs1:
            t = top(x)
            ok = t is not None and y > t + rim
            if ok:
                seg.append((x, y))
            elif len(seg) > 1:
                lines.append([seg[0], seg[-1]]); seg = []
            else:
                seg = []
            x += .5
        if len(seg) > 1:
            lines.append([seg[0], seg[-1]])
        y -= 1.5 if f < .3 else (2. if f < .6 else 3.)
    cv.hair(lines)
    arcs = []
    for c in circles:
        for k in (.8,):
            arcs.append([(c[0] + c[2] * k * math.cos(a), c[1] + c[2] * k * math.sin(a))
                         for a in [PI * (1.05 + .55 * i / 12) for i in range(13)]])
    cv.hair(arcs)


def _scene(ctx, field, bx, by, bw, bh, seed, detail=1.):
    """Engrave the whole field with the rain-jar scene. Returns (canvas svg, black-fill path data)."""
    got, usual_now, usual_month, days = _data(ctx)
    rng = random.Random(seed)
    cv = C.Canvas()
    blacks = []
    s = bh / 160.
    big = bh > 60
    hy = by + bh * (.6 if big else .66)      # horizon
    x0, x1 = bx - 2, bx + bw + 2

    # ---- sky: ruled, dense at the top, with slanting rain
    sky = [(x0, by - 2), (x1, by - 2), (x1, hy), (x0, hy)]
    cv.obj([sky], 0)
    y = hy - 1
    lines = []
    while y > by - 2:
        f = (hy - y) / max(1., hy - by)
        lines.append([(x0, y), (x1, y)])
        y -= 3. if f < .45 else (2. if f < .8 else 1.5)
    cv.hair(lines)
    rain = []
    n_rain = int(bw * (hy - by) / 70 * detail)
    ang = math.radians(104)
    for i in range(n_rain):
        px = rng.uniform(x0, x1 + 20)
        py = rng.uniform(by, hy + bh * .12)
        L = rng.uniform(5, 11) * max(.6, s)
        rain.append([(px, py), (px + L * math.cos(ang), py + L * math.sin(ang))])
    clouds = []
    if big:
        specs = [(bx + bw * .3, by + bh * .22, bw * .34, bh * .12), (bx + bw * .7, by + bh * .17, bw * .32, bh * .11),
                 (bx + bw * .62, by + bh * .36, bw * .36, bh * .1)]
    else:
        specs = [(bx + bw * .5, by + bh * .14, bw * .9, bh * .2)]
    for (ccx, ccy, cw, ch) in specs:
        poly, circ, top = _cloud(ccx, ccy, cw, ch, rng)
        clouds.append((poly, circ, top, ccy, ch))
    cv.hair(rain)
    for poly, circ, top, ccy, ch in clouds:
        cv.obj([poly], 1.)
        _shade_cloud(cv, poly, circ, top, ccy, ch)
        cv.hair(_keep(rain, lambda m, cy=ccy, h=ch: m[1] > cy + h * .5))

    # ---- Mt. Hood on the horizon, behind the cottonwoods
    if big:
        mx, mh, mw = bx + bw * .2, bh * .2, bw * .3
        mt = [(mx - mw / 2, hy), (mx - mw * .12, hy - mh * .78), (mx - mw * .03, hy - mh), (mx + mw * .06, hy - mh * .9),
              (mx + mw * .16, hy - mh * .7), (mx + mw / 2, hy)]
        cv.obj([mt], .5)
        shadow = [(mx - mw * .03, hy - mh), (mx + mw * .06, hy - mh * .9), (mx + mw * .16, hy - mh * .7), (mx + mw / 2, hy),
                  (mx + mw * .02, hy), (mx + mw * .01, hy - mh * .5)]
        cv.hair(C.hatch_poly(shadow, 65, 1.5))
        lower = [(mx - mw / 2, hy), (mx - mw * .3, hy - mh * .45), (mx - mw * .2, hy - mh * .36), (mx - mw * .1, hy - mh * .48),
                 (mx + mw * .05, hy - mh * .4), (mx + mw * .2, hy - mh * .5), (mx + mw / 2, hy)]
        cv.hair(C.hatch_poly(lower, 0, 2))
        for k in range(4):
            gx_ = mx - mw * .08 + k * mw * .05
            cv.hair([[(gx_, hy - mh * (.82 - k * .04)), (gx_ - mw * .03 + k * mw * .02, hy - mh * .52)]])

    # ---- cottonwood line along the horizon
    tl = []
    x = x0
    while x <= x1:
        tl.append((x, hy - bh * .03 - abs(math.sin(x * .19)) * bh * .035 - abs(math.sin(x * .053)) * bh * .03))
        x += 2
    trees = tl + [(x1, hy + 1), (x0, hy + 1)]
    cv.obj([trees], .5)
    cv.hair(C.hatch_poly(trees, 90, 1.5))
    cv.line([[(x0, hy + 1), (x1, hy + 1)]])

    # ---- flat fields, then the flooded slough
    wy = hy + bh * .1
    fields = [(x0, hy + 1), (x1, hy + 1), (x1, wy), (x0, wy)]
    cv.obj([fields], 0)
    fl, y, p = [], hy + 2.5, 1.5
    while y < wy:
        fl.append([(x0, y), (x1, y)])
        y += p
        p = min(3., p + .3)
    cv.hair(fl)
    water = [(x0, wy), (x1, wy), (x1, by + bh + 2), (x0, by + bh + 2)]
    cv.obj([water], .5)
    wl, y = [], wy + 1.5
    while y < by + bh + 2:
        f = (y - wy) / max(1., bh * .4)
        dash = 6 + 26 * f
        xx = x0 + rng.uniform(-dash, 0)
        while xx < x1:
            wl.append([(xx, y), (xx + dash, y)])
            xx += dash + rng.uniform(1.5, 3 + 4 * f)
        y += 1.5 if f < .3 else 2.
    cv.hair(wl)
    cv.hair(_keep(rain, lambda m: m[1] < wy + bh * .1))

    # ---- rain rings on the water
    for i in range(int(7 * detail) if big else 2):
        rx_ = rng.uniform(bx + bw * .05, bx + bw * .95)
        ry_ = rng.uniform(wy + 4, by + bh - 6)
        rr = (2.5 + 5 * (ry_ - wy) / max(1, bh * .4)) * max(.7, s)
        cv.obj([_ell(rx_, ry_, rr, rr * .3, 24)], .5)
        cv.hair([_closed(_ell(rx_, ry_, rr * .55, rr * .17, 16))])
        cv.hair([[(rx_ - rr * 1.5, ry_ + rr * .45), (rx_ + rr * 1.5, ry_ + rr * .45)]])

    # ---- the heron, in the slough, looking at the gauge
    if bh > 100 and bw > 140:
        _heron(cv, bx + bw * .77, wy + bh * .16, s, blacks)

    # ---- mud bank with the dog's paw prints (the Easter egg)
    gx = bx + bw * (.4 if big else .5)
    if big:
        lip = [(bx + bw * t / 20 * .64, by + bh * (.82 - .07 * math.sin(PI * t / 20) - .02 * math.sin(t * 1.3) + .12 * (t / 20) ** 3)) for t in range(21)]
        bank = [(x0, by + bh * .82)] + lip + [(bx + bw * .66, by + bh + 2), (x0, by + bh + 2)]
        cv.obj([bank], 1.)
        cv.hair(C.hatch_poly(bank, 20, 2))
        cv.hair(C.hatch_poly(bank, -25, 3, .7))
        for t in range(3, 19, 2):
            px, py = lip[t]
            for k in (-1, 0, 1):
                cv.hair([[(px + k * 1.2, py + .5), (px + k * 2.6 + rng.uniform(-1, 1), py - (3 + rng.uniform(0, 3)) * max(.7, s))]])
        for i in range(4):
            ppx = bx + bw * (.08 + .07 * i)
            ppy = by + bh * (.93 - .025 * i) + (2.5 if i % 2 else -2.5) * s
            pr = 1.9 * max(.8, s)
            blacks.append(_d(_ell(ppx, ppy, pr, pr * .85, 12), True, 0))
            for k in range(4):
                a = -PI / 2 + (k - 1.5) * .55 + .45
                blacks.append(_d(_ell(ppx + pr * 1.9 * math.cos(a), ppy + pr * 1.9 * math.sin(a), pr * .45, pr * .45, 8), True, 0))

    # ---- the gauge on its post
    _gauge(cv, gx, by, bh, hy, got, usual_now, s, blacks, short=not big)
    return cv.svg(), "".join(blacks)


def _heron(cv, hx, hy, s, blacks):
    """Great blue heron, facing left toward the gauge, feet at (hx, hy)."""
    k = 11 * s
    cv.obj([], 0)
    cv.line([[(hx - .3 * k, hy), (hx - .2 * k, hy - 2.4 * k)], [(hx + .35 * k, hy - .15 * k), (hx + .25 * k, hy - 2.4 * k)]])
    cv.hair([[(hx - .3 * k, hy + 1.5), (hx - .3 * k, hy + 1.1 * k)], [(hx + .35 * k, hy + 1.5), (hx + .35 * k, hy + 1. * k)]])
    bcx, bcy = hx + .15 * k, hy - 2.95 * k
    rot = math.radians(22)
    body = _ell(bcx, bcy, 1.5 * k, .72 * k, 40, rot)
    tail = [(bcx + 1. * k, bcy + .2 * k), (bcx + 2.1 * k, bcy + 1.05 * k), (bcx + 1.6 * k, bcy + .5 * k), (bcx + 1.25 * k, bcy + .6 * k)]
    cv.obj([tail], .5)
    cv.hair(C.hatch_poly(tail, 35, 1.5))
    # neck: S curve from the chest up to the head
    fx, fy = bcx - 1.25 * k, bcy - .45 * k
    neck = []
    for i in range(21):
        t = i / 20
        neck.append((fx - .2 * k * t + .55 * k * math.sin(t * PI * 2) * (1 - .4 * t), fy - 2.6 * k * t))
    wdt = [(.42 - .2 * i / 20) * k for i in range(21)]
    R = C._Rib(neck, wdt, wdt)
    cv.obj([R.outline()], 1.)
    for sv in (-.55, -.2):
        cv.hair(R.contour(sv, .04, .96))
    cv.hair(R.contour(.5, .3, .9))
    cv.obj([body], 1.)
    c, sn = math.cos(rot), math.sin(rot)

    def lower(m):
        dx, dy = m[0] - bcx, m[1] - bcy
        return -dx * sn + dy * c > -.1 * k
    cv.hair(C.hatch_poly(body, 22, 3))
    cv.hair(_keep(C.hatch_poly(body, 22, 3, 1.5), lower))
    for j in range(5):
        u = -.35 + j * .17
        p0 = (bcx - 1.1 * k * c - u * k * -sn, bcy - 1.1 * k * sn + u * k * c)
        cv.hair([[p0, (p0[0] + 1.3 * k * c, p0[1] + 1.3 * k * sn + .12 * k), (p0[0] + 2.4 * k * c, p0[1] + 2.4 * k * sn + .45 * k)]])
    hx2, hy2 = neck[-1]
    cv.obj([_ell(hx2 - .05 * k, hy2 - .05 * k, .45 * k, .34 * k, 20)], 1.)
    beak = [(hx2 - .35 * k, hy2 - .16 * k), (hx2 - 1.8 * k, hy2 + .12 * k), (hx2 - .35 * k, hy2 + .14 * k)]
    cv.obj([beak], 1.)
    cv.hair(C.hatch_poly(beak, 0, 1.5))
    blacks.append(_d([(hx2 - .3 * k, hy2 - .3 * k), (hx2 + .4 * k, hy2 - .42 * k), (hx2 + 1.3 * k, hy2 - .3 * k),
                      (hx2 + .35 * k, hy2 - .18 * k)], True, 0))
    blacks.append(_d(_ell(hx2 - .12 * k, hy2 - .06 * k, .09 * k, .09 * k, 8), True, 0))


def _gauge(cv, gx, by, bh, hy, got, usual_now, s, blacks, short=False):
    top_y = by + bh * (.16 if not short else .1)
    gw = max(9., 16 * s)
    glass_top = top_y + gw * .9
    glass_bot = by + bh * (.74 if not short else .9)
    pw = gw * .9
    post_x = gx + gw * .5 + pw * .55
    post = [(post_x - pw / 2, glass_top + gw * .4), (post_x + pw / 2, glass_top + gw * .2),
            (post_x + pw / 2, by + bh + 3), (post_x - pw / 2, by + bh + 3)]
    cv.obj([post], 1.)
    grain = []
    for i in range(1, 5):
        x = post_x - pw / 2 + pw * i / 5
        grain.append([(x + .6 * math.sin(y * .21 + i) + (1.2 * math.exp(-((y - glass_bot) / 6) ** 2) if i == 2 else 0), y)
                      for y in [glass_top + gw * .4 + j * 2 for j in range(int((by + bh - glass_top) / 2))]])
    cv.hair(grain)
    cv.hair(C.hatch_poly([(post_x + pw * .15, glass_top), (post_x + pw / 2, glass_top), (post_x + pw / 2, by + bh + 3),
                          (post_x + pw * .15, by + bh + 3)], 90, 1.5))
    knot_y = glass_bot + (by + bh - glass_bot) * .4
    cv.hair([_closed(_ell(post_x - pw * .1, knot_y, pw * .14, pw * .35, 14))])
    for yy in (glass_top + (glass_bot - glass_top) * .25, glass_bot - (glass_bot - glass_top) * .2):
        br = [(gx - gw * .55, yy - 1.6), (post_x + pw * .3, yy - 1.6), (post_x + pw * .3, yy + 1.6), (gx - gw * .55, yy + 1.6)]
        cv.obj([br], 1.)
        cv.hair([[(gx - gw * .55, yy), (post_x + pw * .3, yy)]])
    gl = gx - gw / 2
    gb = glass_bot - gw * .15
    cyl = [(gl, glass_top), (gl + gw, glass_top), (gl + gw, gb)] + \
          [(gx + gw / 2 * math.cos(a), gb + gw * .2 * math.sin(a)) for a in [PI * i / 10 for i in range(11)]] + [(gl, gb)]
    cv.obj([cyl], 1.)
    scale_top = glass_top + gw * .35
    span = gb - scale_top
    full = 3.
    wl = gb - span * min(got, full) / full
    water = [(gl + .5, wl), (gl + gw - .5, wl), (gl + gw - .5, glass_bot - gw * .1), (gl + .5, glass_bot - gw * .1)]
    cv.hair(C.hatch_poly(water, 0, 1.5))
    cv.hair(_keep(C.hatch_poly(water, 90, 1.5), lambda m: m[0] > gl + gw * .62))
    cv.line([[(gx + gw * .5 * math.cos(a), wl + gw * .12 * math.sin(a)) for a in [PI - PI * i / 8 for i in range(9)]]])
    cv.hair([[(gl + gw * x, glass_top + 1), (gl + gw * x, wl - 1.5)] for x in (.7, .8, .88)])
    cv.hair([[(gl + gw * .14, glass_top + 2), (gl + gw * .14, glass_bot - gw * .3)]])
    ticks = []
    for i in range(int(full * 10) + 1):
        if short and i % 5:
            continue
        y = gb - span * i / (full * 10)
        L = gw * (.42 if i % 10 == 0 else .28 if i % 5 == 0 else .16)
        ticks.append([(gl + gw * .22, y), (gl + gw * .22 + L, y)])
    cv.hair(ticks)
    fun = [(gl - gw * .35, top_y), (gl + gw * 1.35, top_y), (gl + gw, glass_top), (gl, glass_top)]
    cv.obj([fun], 1.)
    cv.hair(_keep(C.hatch_poly(fun, 75, 1.5), lambda m: m[0] > gx))
    cv.hair(_keep(C.hatch_poly(fun, 105, 3), lambda m: m[0] <= gx))
    cv.obj([_ell(gx, top_y, gw * .85 + 1, 2.4, 24)], 1.)
    blacks.append(_d(_ell(gx, top_y + .2, gw * .78, 1.3, 20), True, 0))
    uy = gb - span * min(usual_now, full) / full
    blacks.append(_d([(gl + gw + 1, uy), (gl + gw + 1 + gw * .45, uy - gw * .28), (gl + gw + 1 + gw * .45, uy + gw * .28)], True, 0))
    cv.obj([], 0)
    cv.line([[(gl + gw * .4, uy), (gl + gw - .5, uy)]])
    if not short:
        for dx, dy in ((-.2, -1.6), (.5, -2.6), (.15, -3.7)):
            _drop_obj(cv, gx + dx * gw, top_y + dy * gw * .9, max(1.4, gw * .1))


# ----------------------------------------------------------------------------------------------
# layouts (copied from the house library so the cartouche field, banner and tablet are engraved)
# ----------------------------------------------------------------------------------------------


def _clipd(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _art(art, blk):
    return art + (f'<path d="{blk}" fill="#000" stroke="none"/>' if blk else "")


def _field_art(ctx, cx, cy, cw, ch, seed, uid):
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    field = C._superellipse(cx, cy, a + .5, b + .5)
    art, blk = _scene(ctx, field, cx - a, cy - b, 2 * a, 2 * b, seed)
    return _clipd(uid, _d(field, True, 0), _art(art, blk))


def _tablet(tx, ty, tw, th, got, usual_now, usual_month):
    """The month gauge across the pedestal tablet: a tube filled to today's total, tenth-inch
    ticks, a black pointer at what Portland usually has by now."""
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{C.pat("L")}" stroke="none"/>']
    x0, x1 = tx + 12, tx + tw - 12
    tcy = ty + th * .62
    tr = max(2.5, th * .2)
    full = usual_month
    xg = x0 + (x1 - x0) * got / full
    xu = x0 + (x1 - x0) * usual_now / full
    tube = f"M{_n(x0)},{_n(tcy - tr)}H{_n(x1)}a{_n(tr)},{_n(tr)} 0 0,1 0,{_n(2 * tr)}H{_n(x0)}a{_n(tr)},{_n(tr)} 0 0,1 0,{_n(-2 * tr)}z"
    o.append(f'<path d="{tube}" fill="{C.pat("L")}" stroke="#000" stroke-width="1"/>')
    fill = f"M{_n(x0)},{_n(tcy - tr + 1)}H{_n(xg)}V{_n(tcy + tr - 1)}H{_n(x0)}a{_n(tr - 1)},{_n(tr - 1)} 0 0,1 0,{_n(-2 * tr + 2)}z"
    o.append(f'<path d="{fill}" fill="{C.pat("X")}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{_n(x0)},{_n(tcy - tr * .45)}H{_n(x1)}" stroke="#000" stroke-width=".5"/>')
    tk = []
    i = 0
    while i <= full * 10 + 1e-6:
        x = x0 + (x1 - x0) * i / (full * 10)
        L = tr * (1.6 if i % 10 == 0 else 1.1 if i % 5 == 0 else .6)
        tk.append(f"M{_n(x)},{_n(tcy - tr - 1.2)}v{_n(-L)}")
        i += 1
    o.append(f'<path d="{"".join(tk)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M{_n(xu)},{_n(tcy - tr - 1)}l{_n(-tr * .7)},{_n(-tr * 1.5)}h{_n(tr * 1.4)}z" fill="#000"/>')
    cv = C.Canvas()
    _drop_obj(cv, xg, tcy - tr * .2, tr * 1.05)
    o.append(cv.svg())
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    got, usual_now, usual_month, days = _data(ctx)

    def scene(x, y, fw, fh, lod):
        field = [(x, y), (x + fw, y), (x + fw, y + fh), (x, y + fh)]
        art, blk = _scene(ctx, field, x, y, fw, fh, seed, (.6, .8, 1.)[lod])
        return _art(art, blk)
    P = dict(seed=seed, shape="round", shape_medium="super", shape_band="oval", stems=3, med_aspect=.84,
             legend=f"{got:.2f} in · in the jar", tablet="",
             tablet_fn=lambda tx, ty, tw, th: _tablet(tx, ty, tw, th, got, usual_now, usual_month),
             scene=scene)
    return ST5.compose(w, h, ctx, P)
