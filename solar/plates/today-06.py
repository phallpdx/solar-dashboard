"""today-06 "Your yard vs. the forecast": Parker's own backyard weather station on Sauvie Island,
engraved against the forecast. A forecast rain-cloud and a warmer-than-forecast sun hang over the
river cottonwoods and Mt. Hood; below, the station mast (anemometer, a heron weathervane, the
solar panel that feeds it, a louvred Stevenson screen) rises out of acanthus, and the rain gauge
that "catches 28% more" stands in the furrows. Tall plates add a pedestal whose tablet carries the
yard-vs-forecast thermograph (parsed from the page text) and a ribbon with the same two traces.
Easter egg: the weathervane is a Sauvie Island heron (with a tiny solar panel on the mast)."""
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
    import zlib
    import zlib as _z
    import bisect as _bisect
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
        if kind == "archtop":
            # straight sides, a flat foot with eased corners, a round arch springing at 45% height
            spring = cy - b + min(a, b) * .8
            ra, rb = a, spring - (cy - b)
            q = max(2., min(a, b) * .12)
            pts = []
            m = n // 4
            for i in range(m):
                pts.append((cx + a, spring + (cy + b - q - spring) * i / m))
            for i in range(7):
                u = _PI / 2 * i / 6
                pts.append((cx + a - q + q * _m.cos(u), cy + b - q + q * _m.sin(u)))
            for i in range(1, m):
                pts.append((cx + a - q - (2 * a - 2 * q) * i / m, cy + b))
            for i in range(7):
                u = _PI / 2 + _PI / 2 * i / 6
                pts.append((cx - a + q + q * _m.cos(u), cy + b - q + q * _m.sin(u)))
            for i in range(1, m):
                pts.append((cx - a, cy + b - q - (cy + b - q - spring) * i / m))
            for i in range(2 * m + 1):
                u = _PI + _PI * i / (2 * m)
                pts.append((cx + ra * _m.cos(u), spring + rb * _m.sin(u)))
            return pts[:-1]
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
            elif kind == "sun":
                # a sun-disc of sixteen shallow scallops
                k = 1 - .018 * (1 - abs(_m.cos(8 * t)))
                pts.append((cx + a * k * c, cy + b * k * s))
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
            fr = h < 44
            ix, iy, iw, ih = border_rect(bo, None, 0, 0, w, h, True, .9 if fr else 1.25)
            mb = (h / 2 - .5) if fr else (ih / 2 - 1.5)
            ma = min(mb * P.get("band_aspect", 1.9), w * .2)
            my = iy + ih / 2
            st.permit_rect(ix, iy, cx - .5, iy + ih)
            msvg, mo = medallion(st, P.get("shape_band", "oval"), cx, my, ma, mb, lambda x, y, fw, fh: P["scene"](x, y, fw, fh, 0),
                                 max(3.5, mb * .16) if fr else max(5., mb * .2))
            g.update(mx=cx, my=my, ma=ma, mb=mb, box=(ix, iy, iw, ih), lod=0)
            sc = Scroll(st, rng.randrange(1 << 20), rmin=max(4., ih * .085) * P.get("rmin_k", 1.), leaf_k=P.get("leaf_k", 1.))
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
            if fr:
                o.extend(bo)
                o.append(msvg)
            else:
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
            sc = Scroll(st, rng.randrange(1 << 20), rmin=max(5., ih * .045) * P.get("rmin_k", 1.), leaf_k=P.get("leaf_k", 1.))
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
            sc = Scroll(st, rng.randrange(1 << 20), rmin=max(6.5, ih * .021) * P.get("rmin_k", 1.), leaf_k=P.get("leaf_k", 1.))
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
        LIMIT = 196 * 1024
        doc = plate_doc(w, h, "".join(o))
        k, sc, cid, box, cvc = redo
        body0 = o[k]
        ls = sc.leaf_lengths()
        extra, frac = 0, 0.
        while len(doc) > LIMIT and ls and extra < 5:
            # over budget: drop the smallest leaves until the scroll sheds the excess
            frac = min(.95, frac + (len(doc) - LIMIT + 2000) / max(1., len(body0) * .7))
            lmin = ls[min(len(ls) - 1, int(len(ls) * frac))]
            o[k] = _scroll_body(st, sc, P, g, cid, box, cvc, lmin + .01)
            doc = plate_doc(w, h, "".join(o))
            extra += 1
        return doc


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
        """A Bewick sky from the horizon y1 up toward y0: fine lines laid close along the horizon,
        opening upward and breaking into ever shorter strokes with longer gaps until they dissolve
        into the paper; lines part round the sun, and the clouds are modelled on top."""
        rng = _r.Random(seed)
        H = y1 - y0
        thin, thick = [], []
        y = _gy(y1 - 1)
        while y > y0:
            t = (y1 - y) / H                     # 0 at the horizon, 1 at the top
            if t > .78 * dense + .1:
                break
            pitch = 1.5 if t < .12 else 2. if t < .3 else 3. if t < .55 else 4.
            keep = 1. - min(.92, max(0., (t - .25) * 1.5))   # share of each line that is cut
            segs = [(x0, x1)]
            if sun:
                sx, sy, sr = sun
                dy = y - sy
                rr = sr + glow
                if abs(dy) < rr:
                    dx = _m.sqrt(rr * rr - dy * dy)
                    segs = [(x0, sx - dx), (sx + dx, x1)]
            for (p, q) in segs:
                x = p - rng.uniform(0, 20)
                while x < q:
                    L = rng.uniform(8, 40) * (keep + .15)
                    a_, b_ = max(x, p), min(x + L, q)
                    if b_ - a_ > .8 and (keep >= 1. or rng.random() < keep + .1):
                        thin.append(f"M{_N(a_)},{_N(y)}H{_N(b_)}")
                    x += L + rng.uniform(1., 3.) + (1 - keep) * rng.uniform(4, 22)
            y = _gy(y - pitch)
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
        """Mt. Hood: a sharp summit set off-centre, concave flanks with a shoulder on the long ridge,
        the lit face left nearly white with broken glacier strokes, the shadow face cut in fall-line
        hachures crossed in its depth, a jagged snowline with tongues running down the gullies, and
        dark timber below."""
        rng = _r.Random(seed)
        H = base - peak
        f = -lit                                    # +1: shadow face on the right
        px = cx + (skew - .08 * f) * hw
        # long (lit) flank with a shoulder; short steep (shadow) flank
        lf, rf = [], []
        for i in range(41):
            t = i / 40
            x = (cx - f * hw) + (px - (cx - f * hw)) * t
            y = base - H * min(1., t ** 1.55 + .05 * _m.exp(-((t - .74) / .06) ** 2))
            lf.append((x + rng.uniform(-.3, .3), y + rng.uniform(-.25, .25)))
        for i in range(1, 41):
            t = i / 40
            x = px + ((cx + f * hw) - px) * t
            y = peak + H * (1 - (1 - t) ** 1.35)
            rf.append((x + rng.uniform(-.3, .3), y + rng.uniform(-.25, .25)))
        poly = lf + [(px, peak - .6)] + rf
        if f < 0:
            poly = poly[::-1]
        cv.obj([poly], .5)
        srt = sorted(poly)
        xs_ = [q[0] for q in srt]

        def top(x):
            i = min(len(srt) - 1, max(1, _bisect.bisect_left(xs_, x)))
            (xa, ya), (xb, yb) = srt[i - 1], srt[i]
            return ya + (yb - ya) * (x - xa) / ((xb - xa) or 1)
        # the dividing ridge, wandering down from the summit
        ridge = [(px + f * hw * .22 * u ** 1.3 + _m.sin(u * 9 + seed) * hw * .015, peak + H * u) for u in [k / 20 for k in range(21)]]
        shade = ridge + rf[::-1]
        sang = 90 - f * 24
        cv.hair(C.hatch_poly(shade, sang, 1.5))
        deep = [(x, y) for x, y in shade if y > peak + H * .35] or shade
        cv.hair(C.hatch_poly([(px + f * hw * .1, peak + H * .35)] + [p for p in rf if p[1] > peak + H * .35] + [(ridge[-1][0], base)], 90 + f * 40, 3.))
        cv.line(ridge[:16])
        # snowline with tongues down the gullies
        def sline(x):
            u = (x - px) / hw
            return peak + H * (snow + .1 * abs(u) + .05 * _m.sin(x * .9 + seed) + .04 * _m.sin(x * 2.3))
        # glaciers on the lit face: broken strokes down the fall line, gathering into the gullies
        gl = []
        for k in range(1, 9):
            u = k / 9
            x0 = px - f * hw * .02 * k
            x1 = (cx - f * hw) + (px - (cx - f * hw)) * (1 - u) * .55 + (px - f * hw * .9 * u) * .45
            pts = [(x0 + (x1 - x0) * t + _m.sin(t * 5 + k) * 1.2, peak + H * (.05 + .9 * t) * (.4 + .6 * u)) for t in [j / 14 for j in range(15)]]
            seg = []
            for j, q in enumerate(pts):
                if q[1] > sline(q[0]) + 3 * rng.random():
                    break
                if q[1] < top(q[0]) + 1:
                    if len(seg) > 1:
                        gl.append(seg)
                    seg = []
                    continue
                if (j + k) % 5 == 4:
                    if len(seg) > 1:
                        gl.append(seg)
                    seg = []
                else:
                    seg.append(q)
            if len(seg) > 1:
                gl.append(seg)
        cv.hair(gl)
        # crevasse ticks across the upper snowfields
        tk = []
        for k in range(int(H / 3)):
            y = peak + H * rng.uniform(.12, snow * .9)
            span = (y - peak) / H * hw * .7
            x = px - f * rng.uniform(.1, 1.) * span
            if y < top(x) + 1.5 or y < top(x + 2.6) + 1.5:
                continue
            tk.append([(x, y), (x + rng.uniform(1.2, 2.6), y + .4)])
        cv.hair(tk)
        # timber: below the snowline, ruled close and stroked vertically, the snow tongues left white
        tb = []
        for i in range(int(hw * 2 / 1.5)):
            x = cx - hw + i * 1.5 + .25
            y0 = max(sline(x), top(x) + .5)
            if i % 7 == 3:
                y0 += H * .08 * rng.random()
            if base - y0 > 1:
                tb.append([(x, y0), (x, base)])
        cv.hair(tb)
        return poly


    def _clip_y(segs, ymin):
        return [s for s in segs if min(p[1] for p in s) > ymin]


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


    # ----------------------------------------------------------------------------------------------
    # bespoke forms (edition plan 1.6): the plate is planned for its page, never stretched to fill.
    # frieze 18-36 px, headpiece 60-85 px band, tailpiece 40-70 px at 40-60% width, marginal device
    # 40-60 px roundel, vignette 18-30% of the sheet, full-width plate 35-50%.
    # ----------------------------------------------------------------------------------------------

    SHEET_H = 714.


    def _strip_doc(doc):
        a = doc.index("</defs>") + 7
        return doc[a:-6]


    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))


    def silhouette(kind, cx, cy, A, B, n=160):
        """Outer outlines for shaped plates, in the same winding as _shape: lens (pointed at both
        ends), culdelampe (an inverted, concave-sided triangle under an arched top), or any _shape."""
        if kind == "lens":
            pts = []
            for i in range(n):
                t = _TAU * i / n
                c, s = _m.cos(t), _m.sin(t)
                pts.append((cx + A * c, cy + s * max(B * (1 - abs(c) ** 2.4) ** .85, 7.)))
            return pts
        if kind == "culdelampe":
            top, bot = cy - B, cy + B
            pts = []
            for i in range(n):
                t = _TAU * i / n
                c, sn = _m.cos(t), _m.sin(t)
                if sn >= 0:
                    y = top + max(7., (bot - top) * (1 - abs(c)) ** 1.45)
                else:
                    y = top - (bot - top) * .08 * (1 - c * c)
                pts.append((cx + A * c, y))
            return pts
        return _shape(kind, cx, cy, A, B, n)


    def shaped_border(o, sil, r=1.2):
        """Gold line, black channel of beads, fine inner rule, following any outline."""
        bw = 2 * r + 3
        inner = _offset(sil, -bw)
        o.append(f'<path d="{C._d(sil, True, .1)}{C._d(inner[::-1], True, .1)}" fill="#000" fill-rule="evenodd" stroke="none"/>')
        o.append(bead_row(_offset(sil, -bw / 2), r, max(.9, r * .7)))
        o.append(f'<path d="{C._d(_offset(sil, -.5), True, .1)}" fill="none" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{C._d(inner, True, .1)}" fill="none" stroke="#000" stroke-width=".5"/>')
        return inner


    def _ring_sources(cx, cy, a, b, A, B, k=1.):
        """Two main stems for the left half of a ring between a medallion (a, b) and its plate
        (A, B): one from the foot sweeping out and up, one from the crown sweeping out and down."""
        rx, ry = (a + A) / 2, (b + B) / 2
        side = A - a
        r1 = max(3., min(side * .3, B * .5) * k)
        r2 = r1 * .8
        E = lambda deg, sx=1., sy=1.: (cx + rx * sx * _m.cos(_m.radians(deg)), cy + ry * sy * _m.sin(_m.radians(deg)))
        return [((cx - 1, cy + ry * .98), _PI, r1, 1, {"via": [E(112), E(140), E(168, .9)], "turns": 1.6}),
                ((cx - 1, cy - ry * .98), _PI, r2, -1, {"via": [E(-115), E(-150, .85)], "turns": 1.5})]


    def _shaped_plate(bw, bh, P, sil, med, lod, sources=None, legend=None, extra=None, ring_r=1.2):
        """A plate cut to an outline: punched matte, fine scroll grown in the left half and mirrored,
        an inlaid medallion with the scene, the outline's gold line and beads. Returns body svg in a
        bw x bh box."""
        seed = P.get("seed", 1)
        rng = _r.Random(seed + lod)
        st = Studio(bw, bh, seed)
        cx = bw / 2
        o = [matte(sil)]
        bo = []
        inner = shaped_border(bo, sil, ring_r)
        st.permit(_offset(inner, -1.))
        st.permit_rect(cx - .5, -2, bw + 6, bh + 6, 0)
        kind, mx, my, ma, mb = med
        msvg, mo = medallion(st, kind, mx, my, ma, mb, lambda x, y, fw, fh: P["scene"](x, y, fw, fh, lod),
                             _clamp(min(ma, mb) * .16, 3.5, 9.))
        g = {"w": bw, "h": bh, "cx": cx, "mx": mx, "my": my, "ma": ma, "mb": mb, "lod": lod, "box": (0, 0, bw, bh), "sil": sil}
        ban = ""
        if legend:
            bwid = min(ma * 2.6, bw * .7)
            bhh = _clamp(bh * .075, 9., 15.)
            ban = banner(st, mx, my + mb * .93, bwid, bhh, legend, .04)
        if P.get("figures"):
            P["figures"](st, None, g)
        xs = [p[0] for p in sil]
        ys = [p[1] for p in sil]
        A, B = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
        scy = (max(ys) + min(ys)) / 2
        rmin = _clamp(min(A, B) * .05, 3.2, 7.) * P.get("rmin_k", 1.)
        sc = Scroll(st, rng.randrange(1 << 20), rmin=rmin, leaf_k=P.get("leaf_k", 1.))
        srcs = sources(g) if sources else _ring_sources(mx, scy, ma, mb, A, B)
        sc.grow(srcs, 7)
        sc.infill(10)
        sc.clothe()
        sc.leaf_fill(lmax=_clamp(B * .12, 6., 12.))
        cv = Cv()
        if P.get("figures"):
            P["figures"](st, cv, g)
        sc.paint(cv)
        cid = _uidp("sh", bw, bh, seed, lod)
        o.append(f'<clipPath id="{cid}"><path d="{C._d(inner, True, 0)}"/></clipPath><g clip-path="url(#{cid})">'
                 f'<g id="{cid}g">{cv.svg()}</g><use href="#{cid}g" transform="translate({_N(bw)},0) scale(-1,1)"/></g>')
        o.extend(bo)
        o.append(msvg)
        o.append(ban)
        if extra:
            o.append(extra(g))
        return "".join(o)


    def ribbon_plate(bw, bh, P, lod, arch=.035):
        """A ribbon banner whose face carries the scene (river waves, a ridge, a scarf): the face
        arches gently, the ends fold under into swallow tails ribbed with silk lines."""
        st = Studio(bw, bh, P.get("seed", 1))
        cv = C.Canvas()
        tail_w = _clamp(bw * .07, 12., 40.)
        fw = bw - 2 * tail_w * .95
        fh = bh * .7
        cx = bw / 2
        x0, x1 = cx - fw / 2, cx + fw / 2
        rise = arch * fw
        cy = bh * .38 + rise * .5

        def yc(x):
            t = (x - x0) / fw
            return cy - rise * _m.sin(_PI * min(1, max(0, t)))
        for side in (-1, 1):
            ex = x1 if side > 0 else x0
            ey = yc(ex)
            tx0 = ex - side * tail_w * .3
            tx1 = ex + side * tail_w * .9
            dy = fh * .2
            top0, bot0 = (tx0, ey - fh / 2 + dy), (tx0, ey + fh / 2 + dy)
            top1, bot1 = (tx1, ey - fh / 2 + dy - fh * .12), (tx1 - side * fh * .1, ey + fh / 2 + dy)
            notch = (tx1 - side * fh * .45, ey + dy + fh * .05)
            tail = [top0, top1, notch, bot1, bot0]
            cv.obj([tail], 1.)
            nk = max(8, int(fh / 1.6))
            for k in range(1, nk):
                f = k / nk
                if f < .3 and k % 2:
                    continue
                a = _lerp(top0, bot0, f)
                b = _lerp(top1, notch, f / .5) if f < .5 else _lerp(notch, bot1, (f - .5) / .5)
                (cv.line if f > .8 else cv.hair)([a, b])
            fold = [(ex, ey - fh / 2), (ex, ey + fh / 2), (tx0, ey + fh / 2 + dy), (tx0, ey - fh / 2 + dy)]
            cv.obj([fold], 1.)
            cv.hair(C.hatch_poly(fold, 45 * side, 1.5))
            cv.line(C.hatch_poly(fold, -45 * side, 3.))
        n = 60
        top = [(x0 + fw * i / n, yc(x0 + fw * i / n) - fh / 2) for i in range(n + 1)]
        bot = [(x0 + fw * i / n, yc(x0 + fw * i / n) + fh / 2) for i in range(n + 1)]
        face = top + bot[::-1]
        cv.obj([face], 1.)
        o = [cv.svg()]
        cid = _uidp("rb", bw, bh, P.get("seed", 1), lod)
        inner = [(x, y + 2.2) for x, y in top] + [(x, y - 2.2) for x, y in bot[::-1]]
        fy0 = min(p[1] for p in top)
        o.append(f'<clipPath id="{cid}"><path d="{C._d(inner, True, 0)}"/></clipPath>'
                 f'<g clip-path="url(#{cid})">{P["scene"](x0, fy0, fw, fh + rise, lod, yc)}</g>')
        o.append(f'<path d="{C._d(top, False, .1)}{C._d(bot, False, .1)}" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{C._d([(x, y + 1.6) for x, y in top], False, .1)}{C._d([(x, y - 1.6) for x, y in bot], False, .1)}" stroke="#000" stroke-width=".5"/>')
        return "".join(o)


    def compose_form(w, h, ctx, P):
        """Lay the page's planned form into the w x h box the page asks for; the art keeps its own
        size and shape (never enlarged to fill), centred."""
        form = P.get("form", "auto")
        seed = P.get("seed", 1)
        if form in ("frieze", "headpiece") and not P.get("ribbon"):
            lo, hi = (18., 36.) if form == "frieze" else (60., 85.)
            bh = _clamp(h, lo, hi) if h >= lo else h
            body = _strip_doc(compose(w, bh, ctx, P))
            y = (h - bh) / 2 if form == "frieze" else 0.
            return plate_doc(w, h, f'<g transform="translate(0,{_N(y)})">{body}</g>')
        if form == "plate":
            bh = _clamp(h, 120., SHEET_H * .5)
            body = _strip_doc(compose(w, bh, ctx, P))
            return plate_doc(w, h, f'<g transform="translate(0,{_N((h - bh) / 2)})">{body}</g>')
        if form in ("headpiece", "tailpiece") and P.get("ribbon"):
            lo, hi = (60., 85.) if form == "headpiece" else (40., 70.)
            bh = _clamp(h, lo, hi) if h >= lo else h
            bw = w if form == "headpiece" else _clamp(w * .58, min(w, 200.), min(w, 340.))
            lod = 0
            body = ribbon_plate(bw, bh, P, lod)
            if P.get("egg"):
                body += P["egg"]({"w": bw, "h": bh, "form": form})
            return plate_doc(w, h, f'<g transform="translate({_N((w - bw) / 2)},{_N((h - bh) / 2 if form != "headpiece" else 0)})">{body}</g>')
        if form == "tailpiece":
            bh = _clamp(h, 40., 70.) if h >= 40 else h
            bw = _clamp(w * .55, min(w, 200.), min(w, 330.))
            kind = P.get("silhouette", "lens")
            cx = bw / 2
            if kind == "culdelampe":
                bw = min(w, bh * 2.9)
                cx = bw / 2
                sil = silhouette(kind, cx, bh * .54, bw / 2 - .5, bh * .44)
                mb = bh * .34
                med = (P.get("shape_tail", "oval"), cx, bh * .4, mb * 1.3, mb)
            else:
                sil = silhouette(kind, cx, bh / 2, bw / 2 - .5, bh / 2 - .5)
                mb = bh / 2 - 1.
                med = (P.get("shape_tail", "oval"), cx, bh / 2, mb * P.get("tail_aspect", 1.45), mb)
            def lens_src(g):
                L = g["mx"] - g["ma"] - 4
                if kind == "lens":
                    R0 = min(bh * .3, L * .32)
                    return [((g["mx"] - g["ma"] + 2, g["my"] + bh * .08), _PI + .12, R0, 1,
                             {"lead": max(2., L - R0 * 2.4), "lead_k": .002})]
                R0 = min(bh * .17, L * .3)
                return [((g["mx"] - g["ma"] * .9, g["my"] - g["mb"] * .45), _PI - .05, R0, -1,
                         {"lead": max(2., L - R0 * 2.2), "lead_k": .001}),
                        ((g["mx"] - g["ma"] * .55, g["my"] + g["mb"] * .85), _PI * .8, R0 * .7, 1,
                         {"lead": max(2., L * .35), "lead_k": .003})]
            body = _shaped_plate(bw, bh, P, sil, med, 0, sources=lens_src, ring_r=.9)
            return plate_doc(w, h, f'<g transform="translate({_N((w - bw) / 2)},{_N((h - bh) / 2)})">{body}</g>')
        if form == "device":
            D = _clamp(min(w, h), 40., 60.) if min(w, h) >= 40 else min(w, h)
            st = Studio(w, h, seed)
            cx, cy = w / 2, h / 2
            o = []
            msvg, mo = medallion(st, P.get("shape", "round"), cx, cy, D / 2 - .5, D / 2 - .5,
                                 lambda x, y, fw, fh: P["scene"](x, y, fw, fh, 0), _clamp(D * .1, 4., 6.))
            if w >= D * 1.7:
                cv = Cv()
                crest_leaves(Studio(w, h, seed), cv, cx - D / 2 + 2, cy + D * .1, D * .32, True, seed)
                cid = _uidp("dv", w, h, seed)
                sp = cv.svg()
                # sprays at the roundel's flanks: the left one cut, the right its mirror
                o.append(f'<g id="{cid}">{sp}</g><use href="#{cid}" transform="translate({_N(w)},0) scale(-1,1)"/>')
            o.append(msvg)
            if P.get("egg"):
                o.append(P["egg"]({"w": w, "h": h, "D": D, "cx": cx, "cy": cy}))
            return plate_doc(w, h, "".join(o))
        if form == "vignette":
            share = P.get("share", .25)
            bh = _clamp(h, 110., SHEET_H * share * 1.08) if h >= 110 else h
            bw = min(w, bh * P.get("vig_aspect", 2.3))
            kind = P.get("shape", "oval")
            cx = bw / 2
            A, B = bw / 2 - .5, bh / 2 - .5
            sil = silhouette(kind, cx, bh / 2, A, B)
            ma = A * P.get("vig_med_a", .5)
            mb = B * P.get("vig_med_b", .74)
            my = bh / 2 - B * .04
            med = (P.get("shape_med", kind), cx, my, ma, mb)
            legend = P.get("legend") if bh >= 140 else None
            body = _shaped_plate(bw, bh, P, sil, med, 1, legend=legend, extra=P.get("extra"))
            return plate_doc(w, h, f'<g transform="translate({_N((w - bw) / 2)},{_N((h - bh) / 2)})">{body}</g>')
        return compose(w, h, ctx, P)


    # ----------------------------------------------------------------------------------------------
    # free-standing plates (art director, round 3): the subject is the composition. A vignette is a
    # shaped engraved scene whose edges dissolve into the paper the way Bewick's do; no black field,
    # no generic vines. Ornament, when there is any, is built from the page's own motifs (frame_fn).
    # ----------------------------------------------------------------------------------------------

    def ragged(kind, cx, cy, A, B, seed, n=260, rough=1., flat_foot=False):
        """An outline that frays: the base shape with slow swells and a fine per-vertex jitter, so
        the engraved lines stop at uneven lengths and the picture dissolves into white."""
        rng = _r.Random(seed)
        base = _shape(kind, cx, cy, A, B, n) if kind != "lens" else silhouette("lens", cx, cy, A, B, n)
        p1, p2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
        out = []
        m = len(base)
        for i, (x, y) in enumerate(base):
            t = _TAU * i / m
            k = 1 + rough * (.03 * _m.sin(5 * t + p1) + .02 * _m.sin(11 * t + p2) + rng.uniform(-.018, .018))
            dx, dy = x - cx, y - cy
            if flat_foot and dy > B * .55:
                k = 1 + rough * rng.uniform(-.01, .01)
            out.append((cx + dx * k, cy + dy * k))
        return out


    def caption(cx, y, text, cap, maxw):
        """A caption in engraved Roman capitals, centred under the plate."""
        tw = text_width(text, cap)
        if tw > maxw:
            cap *= maxw / tw
        th, tn = letters(text, cx, y, cap)
        return letter_svg(th, tn, cap), cap


    def free_plate(w, h, ctx, P):
        """Lay out the page's planned form (P['form']) and engrave the scene as the plate itself."""
        form = P.get("form", "vignette")
        seed = P.get("seed", 1)
        share = P.get("share", .25)
        kind = P.get("shape", "oval")
        cap_txt = P.get("legend") or ""
        if form == "device":
            D = _clamp(min(w, h), 40., 60.) if min(w, h) >= 40 else min(w, h)
            bw = bh = D
            lod = 0
        elif form == "tailpiece":
            bh = _clamp(h, 40., 70.) if h >= 40 else h
            bw = _clamp(w * P.get("tail_w", .55), min(w, 180.), min(w, 330.))
            lod = 0
        elif form == "plate":
            bh = _clamp(h, 140., SHEET_H * share * 1.06) if h >= 140 else h
            bw = w
            lod = 2 if bh > 260 else 1
        else:
            bh = _clamp(h, 100., SHEET_H * share * 1.08) if h >= 100 else h
            bw = min(w, bh * P.get("aspect", 1.7))
            lod = 1
        ox, oy = (w - bw) / 2, (h - bh) / 2
        capsz = 0.
        if cap_txt and form in ("vignette", "plate") and bh > 120:
            capsz = _clamp(bh * .045, 7., 11.)
        sh = bh - (capsz * 2.2 if capsz else 0)
        cx, cy = bw / 2, sh / 2
        A, B = bw / 2 - 1.5, sh / 2 - 1.5
        if kind == "round":
            A = B = min(A, B)
        g = {"w": bw, "h": bh, "cx": cx, "cy": cy, "A": A, "B": B, "lod": lod, "sh": sh, "form": form}
        o = []
        if P.get("under"):
            o.append(P["under"](g))
        edge = P.get("edge", "ragged")
        if edge == "ragged":
            clip = ragged(kind, cx, cy, A, B, seed, rough=P.get("rough", 1.), flat_foot=P.get("flat_foot", False))
        else:
            clip = _shape(kind, cx, cy, A, B, 200)
        xs = [q[0] for q in clip]
        ys = [q[1] for q in clip]
        fx, fy, fw, fh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
        cid = _uidp("fv", w, h, seed, form)
        o.append(f'<clipPath id="{cid}"><path d="{C._d(clip, True, 0)}"/></clipPath>'
                 f'<g clip-path="url(#{cid})">{P["scene"](fx, fy, fw, fh, lod)}</g>')
        if edge == "ruled":
            # a fine double rule (the roundel device): a 1 px line and a .5 px line inside it
            o.append(f'<path d="{C._d(_offset(clip, .5), True, .1)}" stroke="#000" stroke-width="1" fill="none"/>')
            o.append(f'<path d="{C._d(_offset(clip, 2.5), True, .1)}" stroke="#000" stroke-width=".5" fill="none"/>')
        if P.get("frame"):
            o.append(P["frame"](g))
        if capsz:
            sv, _ = caption(cx, sh + capsz * .7, cap_txt, capsz, bw * .9)
            o.append(sv)
        if P.get("egg"):
            o.append(P["egg"](g))
        return plate_doc(w, h, f'<g transform="translate({_N(ox)},{_N(oy)})">{"".join(o)}</g>')


    def frieze_plate(w, h, P):
        """A gap frieze (18-36 px) on the paper, not on black: a bead-and-reel moulding cut between
        fine rules, each bead an oval turned by its shading cuts, each reel a pair of discs, and the
        page's motif small in a ruled roundel at the centre."""
        bh = _clamp(h, 18., 36.) if h >= 18 else h
        oy = (h - bh) / 2
        cx = w / 2
        o = []
        cv = Cv()
        R = bh / 2 - 1
        mid = oy + bh / 2
        gap = R * 1.25
        rb = bh * .16                                 # bead half-height
        # rules: a 1 px line outside, a .5 px line inside, both edges
        for yy, sw in ((oy + .5, 1.), (oy + 2.25, .5), (oy + bh - .5, 1.), (oy + bh - 2.25, .5)):
            for xa, xb in ((1, cx - R - gap), (cx + R + gap, w - 1)):
                cv.hair([(xa, yy), (xb, yy)]) if sw < 1 else cv.line([(xa, yy), (xb, yy)])
        beads = []
        for side in (-1, 1):
            x = cx + side * (R + gap + 2)
            k = 0
            while (side < 0 and x > 6) or (side > 0 and x < w - 6):
                if k % 2 == 0:
                    bl = rb * 2.4
                    bx = x + side * bl / 2
                    bead = _ell(bx, mid, bl / 2, rb, 18)[:-1]
                    cv.obj([bead], .5)
                    cv.hair([[(bx - bl * .18 + q, mid + rb * .25 - q * .05), (bx + bl * .3 + q, mid + rb * .55 - q * .05)] for q in (0,)] +
                            [_ell(bx + bl * .05, mid + rb * .12, bl * .3, rb * .55, 10, .1, 2.4)])
                    x += side * (bl + 1.2)
                else:
                    for j in range(2):
                        dx = x + side * (rb * .45 + j * rb * 1.)
                        disc = _ell(dx, mid, rb * .35, rb * .95, 10)[:-1]
                        cv.obj([disc], .5)
                        cv.hair([[(dx + rb * .1, mid - rb * .6), (dx + rb * .1, mid + rb * .6)]])
                    x += side * (rb * 2.2 + 1.2)
                k += 1
        o.append(cv.svg())
        # the motif roundel
        clip = _shape("round", cx, mid, R, R, 64)
        cid = _uidp("fz", w, h, P.get("seed", 1))
        o.append(f'<clipPath id="{cid}"><path d="{C._d(clip, True, 0)}"/></clipPath>'
                 f'<g clip-path="url(#{cid})">{P["scene"](cx - R, mid - R, 2 * R, 2 * R, 0)}</g>')
        o.append(f'<path d="{C._d(_offset(clip, .5), True, .1)}" stroke="#000" stroke-width="1" fill="none"/>')
        o.append(f'<path d="{C._d(_offset(clip, 2.), True, .1)}" stroke="#000" stroke-width=".5" fill="none"/>')
        return plate_doc(w, h, "".join(o))
    return _types.SimpleNamespace(**{k: v for k, v in locals().items() if not k.startswith('__')})


ST5 = _studio5()
# ==== END STUDIO ENGINE =========================================================================


# ==== PAGE: today-06 ============================================================

_n, _d, _ell = C._n, C._d, C._ell_pts
hatch = C.hatch_poly


# ----------------------------------------------------------------------------------------------
# small engraving helpers
# ----------------------------------------------------------------------------------------------

def solid(cv, poly, outline=1.):
    """A black mass: white shape, then 1 px lines .8 apart."""
    cv.obj([poly], outline)
    cv.line(hatch(poly, 0, .8))


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def cyl_lines(x0, x1, y0, y1, n, light=.3):
    """Vertical shading lines on a cylinder x0..x1: none on the lit left part, closing up to the
    right like cos(theta)."""
    out = []
    w = x1 - x0
    for i in range(n):
        t = light + (1 - light) * (1 - math.cos(PI2 * (i + .5) / n)) if False else None
    k = 0
    x = x0 + w * light
    while x < x1 - .4:
        out.append([(x, y0), (x, y1)])
        u = (x - x0) / w
        step = max(1.5, 3.2 - 2.2 * (u - light) / (1 - light))
        x += step
        k += 1
    return out


PI2 = math.pi * 2


def _cloud_poly(cx, by, w, h, rng):
    """Cumulus outline: a flat-ish base at by, puffs above. Returns (poly, circles)."""
    circ = []
    n = 6
    for i in range(n):
        t = (i + .5) / n
        r = h * (.40 + .36 * math.sin(math.pi * t)) * rng.uniform(.88, 1.08)
        circ.append((cx - w / 2 + w * t, by - r * .55, r))
    top = []
    N = 70
    x0, x1 = cx - w / 2 - h * .25, cx + w / 2 + h * .25
    for i in range(N + 1):
        x = x0 + (x1 - x0) * i / N
        best = by
        for (ccx, ccy, r) in circ:
            dx = x - ccx
            if abs(dx) < r:
                y = ccy - math.sqrt(r * r - dx * dx)
                best = min(best, y)
        top.append((x, best))
    # trim the ends to the base
    top = [p for p in top if p[1] < by - .3]
    base = [(top[-1][0], by), (top[0][0], by)]
    for k in range(9):
        t = k / 8
        pass
    bottom = []
    for k in range(13):
        t = k / 12
        x = top[-1][0] + (top[0][0] - top[-1][0]) * t
        bottom.append((x, by + h * .1 * math.sin(math.pi * t * 3) ** 2))
    return top + bottom, circ


def cloud(cv, cx, by, w, h, rng):
    poly, circ = _cloud_poly(cx, by, w, h, rng)
    cv.obj([poly], 1.)
    top = [p for p in poly if p[1] < by - .3]
    # contour lines following the puffs: a white crown, closing up into a dark belly
    d, k = 2.2, 0
    while True:
        seg, segs = [], []
        for (x, y) in top:
            yy = y + d
            if yy < by - .4:
                seg.append((x, yy))
            elif len(seg) > 1:
                segs.append(seg)
                seg = []
        if len(seg) > 1:
            segs.append(seg)
        if not segs:
            break
        (cv.line if d > h * .62 else cv.hair)(segs)
        d += max(1.5, 3.2 - k * .35)
        k += 1
    # each puff's lower rim, where it overlaps the one behind
    for (ccx, ccy, r) in circ:
        arc = [(ccx + r * math.cos(a), ccy + r * math.sin(a)) for a in
               [.25 + 2.4 * i / 16 for i in range(17)]]
        arc = [p for p in arc if p[1] < by - 1]
        if len(arc) > 1:
            cv.line(arc)
    return poly


def sun(cv, cx, cy, r, nray=20):
    star = []
    for i in range(nray * 2):
        a = math.pi * i / nray - math.pi / 2
        rr = r * (2.05 if i % 4 == 0 else 1.75 if i % 2 == 0 else 1.18)
        star.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    cv.obj([star], .5)
    disc = _ell(cx, cy, r, r, 40)[:-1]
    cv.obj([disc], 1.)
    # concentric engraved rings, closer toward the lower right limb
    for f in (.82, .64, .46):
        cv.hair(_ell(cx, cy, r * f, r * f, 32))
    cv.hair(hatch(_ell(cx + r * .35, cy + r * .35, r * .9, r * .9, 30)[:-1], -45, 1.5))
    cv.line([p for p in _ell(cx, cy, r - 1.2, r - 1.2, 30, .1, 1.6)])


def heron(cv, x, y, s, facing=1):
    """A heron weathervane figure standing on a rod at (x, y), about 10 s long. Black silhouette."""
    f = facing
    P = lambda a, b: (x + f * a * s, y - b * s)
    body = [P(-4.5, 4.2), P(-2, 5.6), P(1, 5.8), P(2.6, 5.2), P(3.4, 6.6), P(3.0, 8.6), P(3.6, 10.2),
            P(4.6, 10.6), P(8.6, 10.0), P(4.8, 9.7), P(4.1, 9.0), P(4.3, 7.0), P(3.9, 5.0), P(2.6, 3.9),
            P(.6, 3.3), P(-2, 3.4), P(-5.2, 3.0)]
    solid(cv, body, .5)
    cv.line([P(.2, 3.4), P(-.2, 0)])
    cv.line([P(1.2, 3.4), P(1.6, 0)])


def anemometer(cv, x, y, s):
    """Three-cup anemometer whose hub sits at (x, y)."""
    cv.obj([rect(x - .6 * s, y - 1 * s, 1.2 * s, 4 * s)], .5)
    for sd in (-1, 1):
        cv.line([(x, y), (x + sd * 7 * s, y - .6 * s)])
    cv.line([(x, y), (x + 2.2 * s, y + 1.6 * s)])
    # left cup: opening toward us (black mouth, white rim)
    lx, ly = x - 7 * s, y - .6 * s
    cv.obj([_ell(lx - 1.6 * s, ly, 2.4 * s, 2.0 * s, 20)[:-1]], 1.)
    solid(cv, _ell(lx - 1.6 * s, ly, 1.5 * s, 1.25 * s, 18)[:-1], 0)
    # right cup: seen from the back, a shaded bowl
    rx, ry = x + 7 * s, y - .6 * s
    bowl = [(rx + 2.6 * s * math.cos(a), ry + 2.1 * s * math.sin(a)) for a in
            [-math.pi / 2 + math.pi * i / 14 for i in range(15)]]
    bowl = [(rx, ry - 2.1 * s)] + bowl
    cv.obj([bowl], 1.)
    cv.hair(hatch(bowl, 90, 1.5))
    # front cup, foreshortened
    fx, fy = x + 2.2 * s, y + 1.6 * s
    cv.obj([_ell(fx, fy + 1.2 * s, 1.8 * s, 1.5 * s, 16)[:-1]], 1.)
    cv.line(hatch(_ell(fx + .4 * s, fy + 1.5 * s, 1.1 * s, 1.0 * s, 12)[:-1], 0, .8))
    cv.obj([_ell(x, y, 1.2 * s, .9 * s, 12)[:-1]], 1.)


def stevenson(cv, cx, top, s):
    """A louvred Stevenson screen, centre cx, roof ridge at top."""
    bw, bh = 15 * s, 12 * s
    dep = 4 * s
    ry = top + 4 * s
    # side face (perspective) to the right
    side = [(cx + bw / 2, ry + 1.6 * s), (cx + bw / 2 + dep, ry), (cx + bw / 2 + dep, ry + bh - 1.4 * s),
            (cx + bw / 2, ry + bh + 1.6 * s)]
    cv.obj([side], 1.)
    cv.hair(hatch(side, 0, 1.5))
    cv.line(hatch(side, 60, 3))
    front = rect(cx - bw / 2, ry + 1.6 * s, bw, bh)
    cv.obj([front], 1.)
    # louvres: each a 1 px slat edge with a hair shadow under it
    y = ry + 1.6 * s + 2
    while y < ry + 1.6 * s + bh - 1.5:
        cv.line([(cx - bw / 2 + 1.2, y), (cx + bw / 2 - 1.2, y)])
        cv.hair([(cx - bw / 2 + 1.2, y + 1.5), (cx + bw / 2 - 1.2, y + 1.5)])
        y += 3.2 if s < 1.4 else 3.6
    cv.line([(cx, ry + 1.6 * s), (cx, ry + 1.6 * s + bh)])
    # gabled roof with a shadowed eave
    roof = [(cx - bw / 2 - 2 * s, ry + 2.2 * s), (cx - bw / 4, top), (cx + bw / 2 + dep * .6, top - .4 * s),
            (cx + bw / 2 + dep + 1.6 * s, ry + .6 * s), (cx + bw / 2 + 1 * s, ry + 2.4 * s)]
    cv.obj([roof], 1.)
    cv.hair(hatch(roof, -20, 1.5))
    cv.line([(cx - bw / 2 - 1.6 * s, ry + 2.9 * s), (cx + bw / 2 + 1 * s, ry + 3.0 * s)])
    # legs
    for lx in (cx - bw / 2 + 1.5 * s, cx + bw / 2 - 1.5 * s):
        cv.obj([rect(lx - .6 * s, ry + 1.6 * s + bh, 1.2 * s, 3.2 * s)], .5)


def solar_panel(cv, x, y, s):
    """A small tilted panel clamped to the mast at (x, y), facing south-left."""
    p = [(x - 1 * s, y), (x - 9 * s, y + 2.4 * s), (x - 8.4 * s, y + 8 * s), (x - .6 * s, y + 5.2 * s)]
    cv.obj([p], 1.)
    cv.line(hatch(p, 15, 1.5))
    # cell grid: white rules through the dark glass
    cv.obj([], 0)
    for t in (1 / 3, 2 / 3):
        a = (p[0][0] + (p[1][0] - p[0][0]) * t, p[0][1] + (p[1][1] - p[0][1]) * t)
        b = (p[3][0] + (p[2][0] - p[3][0]) * t, p[3][1] + (p[2][1] - p[3][1]) * t)
        cv.obj([[(a[0] - .4, a[1]), (a[0] + .4, a[1]), (b[0] + .4, b[1]), (b[0] - .4, b[1])]], 0)
    a = ((p[0][0] + p[3][0]) / 2, (p[0][1] + p[3][1]) / 2)
    b = ((p[1][0] + p[2][0]) / 2, (p[1][1] + p[2][1]) / 2)
    cv.obj([[(a[0], a[1] - .4), (b[0], b[1] - .4), (b[0], b[1] + .4), (a[0], a[1] + .4)]], 0)
    cv.obj([], 0)
    cv.line([(x - 1 * s, y + 2.6 * s), (x, y + 2.6 * s)])


def rain_gauge(cv, cx, base, s, w=None, h=None):
    w = w or 9 * s
    h = h or 24 * s
    x0, x1 = cx - w / 2, cx + w / 2
    top = base - h
    er = w * .18
    body = [(x0, top)] + [(x1, top)] + [(cx + w / 2 * math.cos(a), base + er * math.sin(a))
                                       for a in [math.pi * i / 16 for i in range(17)]]
    # shadow cast on the ground to the right
    sh = _ell(cx + w * .55, base + er * .5, w * .85, er * 1.1, 20)[:-1]
    solid(cv, sh, 0)
    cv.obj([body], 1.)
    cv.hair(cyl_lines(x0, x1, top + er, base + er * .7, 0, .42))
    cv.line([[(x1 - 1.2, top + er), (x1 - 1.2, base + er * .6)]])
    # collar where the funnel meets the tube
    col = top + h * .22
    cv.line([(x0, col)] + [(cx + w / 2 * math.cos(a), col + er * .8 * math.sin(a))
                           for a in [math.pi - math.pi * i / 12 for i in range(13)]])
    # graduations on the lit side
    y = col + 2.5
    k = 0
    while y < base - 1.5:
        L = w * (.34 if k % 5 == 0 else .18)
        cv.hair([(x0 + w * .1, y), (x0 + w * .1 + L, y)])
        y += max(1.5, 1.6 * s)
        k += 1
    # funnel mouth: white rim, black throat
    rim = _ell(cx, top, w / 2 + .6, er + .6, 24)[:-1]
    cv.obj([rim], 1.)
    solid(cv, _ell(cx, top + .3, w / 2 - 1.2, er * .6, 20)[:-1], 0)


def treeline(cv, X, W, hz, s, rng):
    pts = [(X - 4, hz + 1)]
    x = X - 4
    while x < X + W + 4:
        r = rng.uniform(2.5, 5.5) * s
        for i in range(7):
            a = math.pi + math.pi * i / 6
            pts.append((x + r + r * math.cos(a), hz - r * .9 - r * .6 * math.sin(-a) + rng.uniform(-.3, .3)))
        x += r * 1.7
    pts.append((X + W + 4, hz + 1))
    cv.obj([pts], .5)
    cv.hair(hatch(pts, 90, 1.5))
    cv.hair(hatch(pts, 0, 2, .5))
    return pts


def mt_hood(cv, x, hz, s):
    peak = (x, hz - 17 * s)
    m = [(x - 22 * s, hz), (x - 9 * s, hz - 8 * s), (x - 3.5 * s, hz - 14 * s), peak, (x + 4 * s, hz - 13 * s),
         (x + 11 * s, hz - 7 * s), (x + 24 * s, hz)]
    cv.obj([m], .5)
    snow = [(x - 7 * s, hz - 10 * s), (x - 3.5 * s, hz - 14 * s), peak, (x + 4 * s, hz - 13 * s), (x + 8 * s, hz - 9 * s),
            (x + 5 * s, hz - 10 * s), (x + 3 * s, hz - 8.5 * s), (x + .5 * s, hz - 11 * s), (x - 2 * s, hz - 8.5 * s),
            (x - 4.5 * s, hz - 10.5 * s)]
    lower = [p for p in m]
    # shaded east flank darker, west flank light ruled; the snowcap stays carved white
    east = [peak, (x + 24 * s, hz), (x + 1 * s, hz)]
    cv.hair(hatch(lower, 0, 2))
    cv.hair(hatch(east, 60, 1.5))
    cv.obj([snow], 0)
    for k in range(3):
        cv.hair([(x + (k - 1) * 2.2 * s, hz - (12.5 - abs(k - 1)) * s), (x + (k - 1) * 3.6 * s, hz - 9 * s)])


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def scene(X, Y, W, H, seed, level=2):
    """Engraved yard-vs-forecast vignette filling the box (callers clip it to the field)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    s = max(.45, min(H / 100., W / 115.))
    hz = Y + H * (.64 if level else .7)
    # sky: ruled, darker aloft
    sky = rect(X - 3, Y - 3, W + 6, hz - Y + 4)
    cv.obj([sky], 0)
    yy = Y - 3
    cv.hair([[(X - 3, y), (X + W + 3, y)] for y in [Y - 3 + 1.5 * k for k in range(int((hz - Y + 4) / 1.5) + 1)]
             if y < Y + (hz - Y) * .35])
    y = Y + (hz - Y) * .35
    tog = 0
    while y <= hz + 1:
        cv.hair([(X - 3, y), (X + W + 3, y)])
        y += 2 if y < Y + (hz - Y) * .7 else 3
    if level == 0:
        ccx, cby = X + W * .5, Y + H * .4
        cloud(cv, ccx, cby, W * .52, H * .3, rng)
        cv.obj([], 0)
        ground = rect(X - 3, hz, W + 6, Y + H - hz + 3)
        cv.obj([ground], .5)
        y, p = hz + 1.5, 1.5
        while y < Y + H + 3:
            cv.hair([(X - 3, y), (X + W + 3, y)])
            p = min(3, p + .25)
            y += p
        cv.obj([], 0)
        for i in range(-3, 4):
            x = ccx + i * W * .075
            cv.line([[(x + 1.2 * (k + .5) * .3 - k * 0, cby + 4 + k * 4.5), (x - 1.0 - k * .3, cby + 7 + k * 4.5)]
                     for k in range(int((Y + H - cby) / 4.5)) if (k + i) % 2 == 0][:3])
        rain_gauge(cv, ccx + W * .02, hz + (Y + H - hz) * .45, s, W * .09, H * .32)
        return cv.svg()

    # sun (warmer than forecast) peeping round the cloud, upper right
    sun(cv, X + W * .52, Y + H * .2, H * .075)
    # Mt. Hood far off, and the cottonwoods along the channel
    mt_hood(cv, X + W * .5, hz - 1, s * .9)
    treeline(cv, X, W, hz + .5, s * .8, rng)
    # forecast cloud, its rain slanting across the fields
    ccx, cby = X + W * .3, Y + H * .36
    cl = cloud(cv, ccx, cby, W * .38, H * .16, rng)
    # ground: perspective furrows over ruled tilth
    ground = rect(X - 3, hz + 1, W + 6, Y + H - hz + 3)
    cv.obj([ground], .5)
    y, p = hz + 2.5, 1.5
    while y < hz + (Y + H - hz) * .3:
        cv.hair([(X - 3, y), (X + W + 3, y)])
        p = min(3, p * 1.18)
        y += p
    vx, vy = X + W * .4, hz - H * .35
    t0 = (hz + 1 - vy) / (Y + H + 3 - vy)
    for i in range(-20, 30):
        bx = vx + i * W * .036
        (cv.line if i % 2 else cv.hair)([(vx + (bx - vx) * t0, hz + 1), (bx, Y + H + 3)])
    # grass and stubble along the furrows nearer the eye
    for j in range(60):
        gx0 = X + rng.uniform(0, W)
        gy0 = hz + (Y + H - hz) * rng.uniform(.35, 1.)
        hh = (1.5 + 2.5 * (gy0 - hz) / (Y + H - hz)) * s
        for k in (-1, 0, 1):
            cv.hair([(gx0, gy0), (gx0 + k * hh * .45, gy0 - hh)])
    # rain
    cv.obj([], 0)
    span = W * .34
    k = 0
    for i in range(16):
        x = ccx - span / 2 + span * i / 15
        y0 = cby + 2 + (i % 3) * 2.5
        pts = []
        y = y0
        while y < hz + (Y + H - hz) * .5:
            pts.append([(x - (y - y0) * .28, y), (x - (y + 3.5 * s - y0) * .28, y + 3.5 * s)])
            y += 7.5 * s
        cv.line(pts)
    # the rain gauge in the furrows, catching it
    gx = X + W * .36
    gbase = Y + H * .9
    rain_gauge(cv, gx, gbase, s)
    # the station mast rising out of acanthus
    s0 = s
    s = s * 1.3
    mx = X + W * .72
    mbase = Y + H * .93
    mtop = Y + H * .14
    mast = rect(mx - 1.3 * s, mtop, 2.6 * s, mbase - mtop)
    cv.obj([mast], 1.)
    cv.hair([(mx + .2 * s, mtop + 2), (mx + .2 * s, mbase)])
    cv.line([(mx + .8 * s, mtop + 2), (mx + .8 * s, mbase)])
    # cross arm with the heron vane
    ay = mtop + 15 * s
    arm = rect(mx - 1, ay - .7 * s, 15 * s, 1.4 * s)
    cv.obj([arm], .5)
    cv.line([(mx, ay + .5 * s), (mx + 15 * s, ay + .5 * s)])
    vx2 = mx + 13 * s
    cv.obj([rect(vx2 - .5 * s, ay - 4 * s, 1 * s, 4 * s)], .5)
    rod = [(vx2 - 10 * s, ay - 4.4 * s), (vx2 + 6 * s, ay - 4.4 * s)]
    cv.line(rod)
    arrow = [(vx2 + 8 * s, ay - 4.4 * s), (vx2 + 5 * s, ay - 6 * s), (vx2 + 5.6 * s, ay - 4.4 * s),
             (vx2 + 5 * s, ay - 2.8 * s)]
    solid(cv, arrow, .5)
    heron(cv, vx2 - 4 * s, ay - 4.4 * s, s * .8, 1)
    # solar panel (Parker's) feeding the station
    solar_panel(cv, mx - 1.3 * s, ay + 3 * s, s)
    anemometer(cv, mx, mtop, s)
    # Stevenson screen on the mast
    stevenson(cv, mx, Y + H * .44, s * .9)
    # acanthus springing from the foot of the mast
    s = s0
    L = H * .25
    C.acanthus_frond(mx - 1, mbase + 1, -150, L, 3, 24, -.8, -4.2, rng.randrange(1 << 20), cv=cv)
    C.acanthus_frond(mx + 1, mbase + 1, -30, L * .95, 3, 24, .8, 4.2, rng.randrange(1 << 20), cv=cv)
    C.acanthus_finger(mx, mbase + 2, -95, L * .7, cv=cv, bend=-.3, curl=-3.5)
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# yard vs forecast data (parsed from the page; falls back to the sample day)
# ----------------------------------------------------------------------------------------------

def temps(ctx):
    txt = (ctx or {}).get("sample", "") or ""
    yard = [(int(a), int(b)) for a, b in re.findall(r"(\d+)\D{0,3}/\s*(\d+)\D{0,3}\s*forecast", txt)]
    fc = [(int(a), int(b)) for a, b in re.findall(r"forecast\s*(\d+)\D{0,3}/\s*(\d+)", txt)]
    if len(yard) < 1 or len(fc) < 1:
        yard, fc = [(67, 52), (61, 50), (54, 49)], [(65, 51), (60, 48), (53, 48)]
    n = min(len(yard), len(fc), 3)
    if n < 3:
        yard = (yard + [(61, 50), (54, 49)])[:3]
        fc = (fc + [(60, 48), (53, 48)])[:3]
    return yard[:3], fc[:3]


def _trace(days, x, y, w, h, lo, hi, n=90):
    """Diurnal curve through the daily (high, low) pairs: low at dawn, high mid-afternoon."""
    pts = []
    for i in range(n + 1):
        t = i / n * len(days)
        d = min(int(t), len(days) - 1)
        f = t - d
        H, L = days[d]
        Ln = days[min(d + 1, len(days) - 1)][1]
        if f < .25:
            v = L + (H - L) * 0 if False else L
            v = L
            v = L + 0 * f
            # night: easing from previous evening down to the low
            v = L + (H - L) * .0
        if f < .6:
            v = L + (H - L) * (1 - math.cos(math.pi * max(0, f - .22) / .38)) / 2 if f > .22 else L
        else:
            v = Ln + (H - Ln) * (1 + math.cos(math.pi * (f - .6) / .62)) / 2
        pts.append((x + w * i / n, y + h - (v - lo) / (hi - lo) * h))
    return pts


def thermograph(x, y, w, h, ctx, frame=True):
    yard, fc = temps(ctx)
    vals = [v for d in yard + fc for v in d]
    lo, hi = min(vals) - 2, max(vals) + 2
    o = []
    if frame:
        o.append(f'<path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("L")}" stroke="none"/>')
        g = "".join(f"M{_n(x + w * k / 3)},{_n(y + 1)}v{_n(h - 2)}" for k in (1, 2))
        g += "".join(f"M{_n(x + w * k / 12)},{_n(y + h - 2.5)}v2.5" for k in range(1, 12))
        o.append(f'<path d="{g}" stroke="#000" stroke-width=".5"/>')
    py0, ph = y + h * .08, h * .8
    f = _trace(fc, x + 2, py0, w - 4, ph, lo, hi)
    yv = _trace(yard, x + 2, py0, w - 4, ph, lo, hi)
    o.append(f'<path d="{_d(f, tol=.2)}" stroke="#000" stroke-width="1" stroke-dasharray="3 2.5" fill="none"/>')
    o.append(f'<path d="{_d(yv, tol=.2)}" stroke="#000" stroke-width="1.5" fill="none"/>')
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# layouts (from the house codex, with the field engraved edge to edge)




def cups(cv, cx, cy, s, spin=0.):
    """A cup anemometer: a turned mast, a hub, three arms in perspective, each ending in a
    hemispherical cup turned by fine cuts on its shadowed side."""
    mast = [(cx - s * .05, cy), (cx + s * .05, cy), (cx + s * .07, cy + s * 1.6), (cx - s * .07, cy + s * 1.6)]
    cv.obj([mast], .5)
    cv.hair([[(cx + s * .02, cy + s * .1), (cx + s * .03, cy + s * 1.6)]])
    cups = []
    for k in range(3):
        a = spin + math.tau * k / 3
        ex, ey = cx + math.cos(a) * s, cy + math.sin(a) * s * .32
        cups.append((math.sin(a), a, ex, ey))
    cups.sort()
    for depth, a, ex, ey in cups:
        cv.line([(cx, cy), (ex, ey)])
        r = s * .27
        face = math.cos(a)                     # how far the cup's mouth turns to us
        disc = [(ex + r * (.55 + .45 * abs(face)) * math.cos(t), ey + r * math.sin(t)) for t in [math.tau * i / 20 for i in range(20)]]
        cv.obj([disc], 1.)
        half = [p for p in disc if p[0] >= ex - .2] if face > 0 else [p for p in disc if p[0] <= ex + .2]
        if len(half) > 2:
            cv.hair(C.hatch_poly(half, 90, 1.5))
        cv.hair([[(ex - r * .2 * face, ey - r * .55), (ex - r * .2 * face, ey + r * .55)]])
    hub = [(cx + s * .12 * math.cos(t), cy - s * .05 + s * .09 * math.sin(t)) for t in [math.tau * i / 14 for i in range(14)]]
    cv.obj([hub], 1.)


def note_drop(cx, cy, s):
    """A raindrop cut as a jazz eighth note: the drop is the note head, a stem rises from its
    right flank, one flag curls off the top. Black, svg string."""
    head = [(cx + s * .5 * math.cos(t) * (1 - .55 * max(0., -math.sin(t))) , cy + s * .5 * math.sin(t) - s * .45 * max(0., -math.sin(t)) ** 3) for t in [math.tau * i / 24 for i in range(24)]]
    d = "M" + "L".join(f"{C._n(x)},{C._n(y)}" for x, y in head) + "z"
    sx = cx + s * .48
    st = f"M{C._n(sx)},{C._n(cy)}V{C._n(cy - s * 2.1)}"
    fl = f"M{C._n(sx)},{C._n(cy - s * 2.1)}C{C._n(sx + s * .2)},{C._n(cy - s * 1.6)} {C._n(sx + s * 1.)},{C._n(cy - s * 1.5)} {C._n(sx + s * .7)},{C._n(cy - s * .8)}"
    return (f'<path d="{d}" fill="#000" stroke="#000" stroke-width=".5"/>'
            f'<path d="{st}{fl}" fill="none" stroke="#000" stroke-width="1"/>')


def device_scene(x, y, fw, fh, seed, sky="rain"):
    """The marginal roundel: a cup anemometer on its mast against the morning sky, rain or sun;
    one raindrop falls as a jazz eighth note (Parker's Easter egg)."""
    rng = random.Random(seed)
    cv = ST5.Cv()
    S = min(fw, fh)
    cx, cy = x + fw * .5, y + fh * .55
    hz = y + fh * .78
    skysvg = ST5.sky(cv, x - 2, y - 2, x + fw + 2, hz, seed, clouds=0)
    if sky == "sun":
        ST5.sky(cv, x - 2, y - 2, x + fw + 2, y - 1, seed, clouds=0, sun=(x + fw * .72, y + fh * .28, S * .13), glow=S * .08)
        ST5.cloud(cv, x + fw * .3, y + fh * .36, fw * .46, fh * .16, rng)
    else:
        ST5.cloud(cv, x + fw * .55, y + fh * .3, fw * .9, fh * .22, rng)
        streaks = []
        for i in range(int(fw / 3.)):
            sx = x + i * 3. + rng.uniform(-.8, .8)
            sy = y + fh * (.33 + rng.uniform(0, .12))
            L = rng.uniform(3, 7)
            if abs(sx - cx) > S * .08:
                streaks.append([(sx, sy), (sx - L * .3, sy + L)])
        cv.hair(streaks)
    ground = [(x - 2, hz), (x + fw + 2, hz - fh * .03), (x + fw + 2, y + fh + 2), (x - 2, y + fh + 2)]
    cv.obj([ground], .5)
    cv.hair([[(x - 2, hz + 2 + k * 2.), (x + fw + 2, hz + 1 + k * 2.)] for k in range(int(fh * .22 / 2))])
    cups(cv, cx, cy - S * .12, S * .3, .35 + seed % 7 * .2)
    return skysvg + cv.svg() + note_drop(x + fw * (.8 if sky == "rain" else .2), y + fh * .7, S * .065)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 6
    P = dict(seed=seed, form="device", shape="round",
             scene=lambda x, y, fw, fh, lod: device_scene(x, y, fw, fh, seed, "sun"))
    return ST5.free_plate(w, h, ctx, dict(P, shape="round", edge="ruled"))
