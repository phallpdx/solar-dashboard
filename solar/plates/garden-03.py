"""garden-03 "Feathered neighbors": the rare-bird page.

The plate engraves the morning's headline: a Bonaparte's Gull (confirmed at Frenchman's Bar) beating
over the Columbia, Mt. Hood on the horizon, a Great Egret standing at the water's edge in the reeds,
Cackling Geese going over in a V. In the tall plate two great blue herons grow out of the
acanthus on either side of the cartouche (their necks rise from fronds, carved in the same relief),
an engraved quill lies along the ribbon banner, and the pedestal tablet carries a frieze of the
week's waterbirds (teal, cackling goose) on rippled water.
Easter egg: a trail of dog paw prints crossing the mud at the egret's feet (Parker's dog came down
to the river too).
"""
import sys
import math
import random
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


# ==== PAGE: garden-03 ============================================================

PI = math.pi
TAU = 2 * PI
_n = C._n
_d = C._d


# ----------------------------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------------------------

def _cr(pts, closed=False, k=6):
    """Catmull-Rom through pts, k samples per span."""
    n = len(pts)
    if n < 3:
        return list(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[i + 1]
        p3 = pts[(i + 2) % n] if closed else pts[min(n - 1, i + 2)]
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def _map(pts, ox, oy, s, flip=False):
    f = -1 if flip else 1
    return [(ox + f * x * s, oy + y * s) for x, y in pts]


def _rib(pts, w0, w1, wr=None):
    n = len(pts)
    W = [w0 + (w1 - w0) * i / (n - 1) for i in range(n)]
    return C._Rib(pts, W, wr if wr is not None else W)


def _wave_rows(x0, x1, y0, y1, pitch, rng, dash=(8, 26), gap=(2, 5), lane=None, sway=0.):
    """Broken horizontal hairlines (water / mud), optional white glint lane (centre x, half width)."""
    out = []
    y = y0
    row = 0
    while y <= y1:
        x = x0 - rng.uniform(0, 10)
        while x < x1:
            ln = rng.uniform(*dash)
            seg = []
            for j in range(int(ln / 3) + 2):
                xx = x + min(ln, j * 3)
                seg.append((xx, y + sway * math.sin(xx * .11 + row)))
            if lane:
                lx, lw = lane
                lw2 = lw * (.4 + .6 * (y - y0) / max(1, y1 - y0))
                if abs(x + ln / 2 - lx) < lw2:
                    seg = []
            if seg:
                out.append(seg)
            x += ln + rng.uniform(*gap)
        y += pitch
        row += 1
    return out


def _solid(cv, poly, angle=0.):
    """A black mass of 1 px lines 1 px apart, clipped to poly."""
    cv.line(C.hatch_poly(poly, angle, 1.))


# ----------------------------------------------------------------------------------------------
# the birds
# ----------------------------------------------------------------------------------------------

def gull(cv, ox, oy, span, flip=False, phase=0.):
    """Bonaparte's Gull in winter dress, flying left (unless flip), wings up on the stroke.
    span = wingspan in px; (ox, oy) the middle of the body."""
    s = span / 70.
    M = lambda p: _map(p, ox, oy, s, flip)
    lift = phase
    # far wing (behind the body), raised high
    far = _cr([(1, -2), (3, -12), (6 + lift, -24), (9 + lift, -33), (13 + lift, -29), (13, -20), (12, -9), (9, -2)], True, 5)
    farp = M(far)
    cv.obj([farp], .5)
    cv.hair(C.hatch_poly(farp, 60 if not flip else 120, 2.))
    tipf = M(_cr([(5.6 + lift, -26), (9 + lift, -33), (13 + lift, -29), (11.8, -25)], True, 4))
    _solid(cv, tipf, 45)
    # tail and body
    tail = M([(10, -2.2), (19.5, -1.4), (20.4, 1.2), (19, 3.4), (10, 3)])
    cv.obj([tail], .5)
    cv.hair(C.hatch_poly(tail, 0, 3.))
    body = M(_cr([(-12.5, -1.6), (-8, -3.9), (0, -4.3), (8, -3.3), (13, -1), (12, 2.4), (5, 4.3), (-4, 4.4), (-10.5, 2.6)], True, 5))
    cv.obj([body], 1.)
    belly = [(-8, 3.2), (0, 3.6), (8, 2.6)]
    R = _rib(M(_cr(belly, False, 6)), .1, .1)
    for k in range(1, 3):
        cv.hair([(p[0], p[1] - k * 1.5) for p in M(_cr([(-7.5, 3.2), (0, 3.4), (7.5, 2.4)], False, 6))][1:-1])
    cv.hair([q for q in M(_cr([(-9, 2.6), (-2, 3.9), (9, 2.4)], False, 6))])
    # head
    head = M(_cr([(-11, -2.5), (-13.8, -5.4), (-17.5, -6.2), (-20.6, -4.6), (-20.8, -2.2), (-18.6, -.4), (-14, .4), (-10.5, 1)], True, 5))
    cv.obj([head], 1.)
    bill = M([(-20.4, -3.6), (-25.6, -2.9), (-20.6, -2.2)])
    cv.obj([bill], .5)
    _solid(cv, bill, 0)
    ear = M([(-15.2, -3.6)])[0]
    cv.obj([C._ell_pts(ear[0], ear[1], 1.4 * s, 1.1 * s, 10)[:-1]], 0)
    _solid(cv, C._ell_pts(ear[0], ear[1], 1.4 * s, 1.1 * s, 10)[:-1])
    eye = M([(-18.2, -4.2)])[0]
    cv.line(C._ell_pts(eye[0], eye[1], .45 * s + .2, .45 * s + .2, 8))
    # near wing, raised, the leading edge toward us; pale grey mantle in light hatch, black trailing tips
    near = _cr([(-5, -1.5), (-8, -10), (-12 - lift, -20), (-17 - lift, -31), (-20 - lift, -36), (-15.5 - lift, -33),
                (-9 - lift, -26), (-1, -18), (4, -9), (5.5, -2.5)], True, 5)
    nearp = M(near)
    cv.obj([nearp], 1.)
    # secondaries: feather lines from the leading edge back to the trailing edge
    lead = _cr([(-5, -1.5), (-8, -10), (-12 - lift, -20), (-17 - lift, -31), (-20 - lift, -36)], False, 8)
    trail = _cr([(5.5, -2.5), (4, -9), (-1, -18), (-9 - lift, -26), (-15.5 - lift, -33), (-20 - lift, -36)], False, 8)
    nf = 15
    for i in range(1, nf):
        u = i / nf
        a = lead[int(u * (len(lead) - 1))]
        b = trail[int(u * (len(trail) - 1))]
        m = (a[0] + (b[0] - a[0]) * .35, a[1] + (b[1] - a[1]) * .35)
        cv.hair(M([m, b]))
    # mantle shading: lines along the wing, from the root
    for f in (.55, .7, .82, .92):
        pl = [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f) for a, b in
              zip(lead[:int(len(lead) * .78)], trail[:int(len(lead) * .78)])]
        cv.hair(M(pl))
    # the black wing-tip with its white leading wedge (a Bonaparte's mark)
    tip = M(_cr([(-11 - lift, -27.5), (-15.5 - lift, -33), (-20 - lift, -36), (-18.6 - lift, -32.4), (-15 - lift, -29.5)], True, 4))
    _solid(cv, tip, 45)
    cv.obj([M([(-6, -1), (-1, -.4), (3, -1.2), (-2, -3)])], 0)
    cv.hair(M([(-7, -.8), (-1, .3), (4, -.6)]))


def egret(cv, fx, fy, H, flip=False, seed=0):
    """A Great Egret standing at the water's edge facing left (unless flip), feet at (fx, fy),
    H tall to the crown. Drawn white, shaded in bulino along its plumage."""
    s = H / 100.
    M = lambda p: _map(p, fx, fy, s, flip)
    rng = random.Random(seed)
    # legs (black), slightly apart; toes
    legs = [M([(1, -50), (0, -26), (-1.5, 0)]), M([(5, -50), (6, -26), (7, -1)])]
    cv.obj([], 0)
    for L in legs:
        cv.heavy(L)
    cv.line(M([(-1.5, 0), (-7, .8)]) + [])
    cv.line(M([(-1.5, 0), (2, 1.2)]))
    cv.line(M([(7, -1), (12, .2)]))
    cv.line(M([(7, -1), (3.5, .6)]))
    # trailing plumes (aigrettes) over the tail
    for k in range(6):
        cv.hair(M(_cr([(6 + k, -62), (18 + k * .6, -56 + k * .5), (28 + k * .8, -47 + k * .7), (33 + k, -40 + k)], False, 5)))
    # body
    bodyc = [(-12, -66), (-6, -71.5), (4, -72), (14, -67), (24, -58), (31, -48.5), (25, -49.5), (14, -51.5),
             (3, -52), (-6, -55), (-11, -60)]
    body = M(_cr(bodyc, True, 5))
    cv.obj([body], 1.)
    # belly shading: lines following the underside, close at the bottom, opening upward
    under = _cr([(-11, -59), (-5, -54.5), (4, -53), (14, -53), (24, -51)], False, 6)
    for k, off in enumerate((0, 1.5, 3, 4.5, 6.5, 9)):
        pl = [(x, y - off) for x, y in under]
        pl = pl[int(k * 1.2):len(pl) - k]
        if len(pl) > 1:
            cv.hair(M(pl))
    # wing fold line and scapular feathers
    cv.hair(M(_cr([(-4, -64), (6, -63), (16, -59), (25, -52)], False, 6)))
    for i in range(7):
        x = -2 + i * 4
        cv.hair(M([(x, -63.5 + i * .6), (x + 4.5, -59.5 + i * .8)]))
    # neck: the S of an egret
    neck = _cr([(-8, -68), (-13, -75), (-12.5, -83), (-6, -89), (-5, -95), (-9, -99), (-14, -100)], False, 6)
    Rn = C._Rib(M(neck), [3.0 * s - (1.0 * s) * i / (len(neck) - 1) for i in range(len(neck))],
                [3.0 * s - (1.0 * s) * i / (len(neck) - 1) for i in range(len(neck))])
    cv.obj([Rn.outline()], 1.)
    sd = -1 if flip else 1
    for sv in (.35, .6, .82):
        cv.hair(Rn.contour(-sv * sd, .02, .9))
    cv.hair(Rn.contour(.6 * sd, .25, .55))
    # head and bill (yellow, in light hatch), eye, lore
    head = M(_cr([(-10, -97), (-12.5, -101.4), (-17, -102), (-20, -99.6), (-17, -97.4), (-13, -96.6)], True, 5))
    cv.obj([head], 1.)
    bill = M([(-19.6, -101), (-38, -98.6), (-19.8, -98.2)])
    cv.obj([bill], .5)
    cv.hair(C.hatch_poly(bill, 45 if not flip else 135, 1.5))
    e = M([(-16, -100)])[0]
    cv.line(C._ell_pts(e[0], e[1], .9, .9, 8))
    cv.line(M([(-17.2, -100.2), (-19.6, -99.8)]))
    # chest plumes hanging from the lower neck
    for k in range(5):
        cv.hair(M([(-12 + k * .8, -73 + k), (-14 + k * .6, -66 + k * .8)]))


def heron_head(cv, root, head, side, H, seed=0):
    """A great blue heron's neck and head carved into the scroll: the neck rises from root (x, y)
    in an S to the head at head (x, y), the bill pointing toward -side (inward). H ~ neck length."""
    rng = random.Random(seed)
    rx, ry = root
    hx, hy = head
    dx, dy = hx - rx, hy - ry
    # control points: out, then back in, like a heron's retracted S
    ctrl = [(rx, ry), (rx + dx * .1 + side * H * .14, ry + dy * .3), (rx + dx * .25 + side * H * .06, ry + dy * .6),
            (rx + dx * .7 - side * H * .02, ry + dy * .82), (hx + side * H * .06, hy + H * .03), (hx, hy)]
    sp = _cr(ctrl, False, 8)
    n = len(sp)
    w0, w1 = H * .07, H * .04
    W = [w0 + (w1 - w0) * (i / (n - 1)) ** .8 for i in range(n)]
    R = C._Rib(sp, W, W)
    cv.obj([R.outline()], 1.)
    # which side of the rib faces the throat (inward)?
    i = n // 2
    a, b = sp[i - 1], sp[i + 1]
    nx, ny = -(b[1] - a[1]), b[0] - a[0]
    inward = 1 if nx * (-side) > 0 else -1
    # back of the neck: dense contour bulino into a black shadow; front: streaked white
    lines = C._fill_lines(R, -.05 * inward, -.98 * inward, 1.5, .02, .97, 3)
    cv.hair(lines)
    C._shadow(cv, R, -inward, min(3., w0 * .35), .05, .9)
    # throat streaks: short dark dashes down the front of the neck
    u = .12
    while u < .85:
        cv.line([R.at(u, .55 * inward), R.at(u + 3. / R.L, .3 * inward)])
        cv.hair([R.at(u + 1.5 / R.L, .85 * inward), R.at(u + 4.5 / R.L, .7 * inward)])
        u += 6.5 / R.L
    # the head, carved in the round: local (u forward, v down) in units of hl, forward = -side
    hl = H * .25
    d = -side
    L = lambda pts: [(hx + d * u * hl, hy + v * hl) for u, v in pts]
    # crest plumes trailing back (black), behind the head
    for pl in ([(-.25, -.24), (-.8, -.2), (-1.3, -.06), (-.8, -.1), (-.3, -.1)],
               [(-.3, -.1), (-.9, .02), (-1.15, .13), (-.8, .06), (-.3, .02)]):
        p = L(_cr(pl, True, 4))
        cv.obj([p], .5)
        _solid(cv, p, 45)
    head = L(_cr([(-.45, .25), (-.55, .02), (-.4, -.22), (-.05, -.32), (.3, -.24), (.55, -.1), (.55, .12),
                  (.25, .3), (-.1, .36)], True, 5))
    cv.obj([head], 1.)
    # black brow stripe from the eye back to the plume
    brow = L(_cr([(.3, -.2), (.05, -.27), (-.3, -.24), (-.45, -.12), (-.2, -.15), (.05, -.16), (.3, -.13)], True, 4))
    cv.obj([brow], 0)
    _solid(cv, brow, 45)
    # cheek and throat bulino, following the head
    for k in range(4):
        v = .02 + k * .07
        cv.hair(L([(.42, v - .02), (.1, v + .03), (-.3, v + .02)]))
    # the dagger bill
    bill = L([(.5, -.12), (2.0, .03), (.5, .14)])
    cv.obj([bill], 1.)
    cv.hair(C.hatch_poly(L([(.5, -.12), (2.0, .03), (.5, .02)]), 45, 1.5))
    cv.line(L([(.52, .02), (1.7, .03)]))
    # the eye: a ring with a black pupil
    ex, ey = L([(.22, -.07)])[0]
    cv.obj([C._ell_pts(ex, ey, max(1.6, hl * .09), max(1.6, hl * .09), 12)[:-1]], 1.)
    cv.line(C._ell_pts(ex, ey, .6, .6, 6))


def paw_trail(cv, x, y, k, n=4, ang=-.35):
    """The Easter egg: a dog's paw prints walking across the mud."""
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(n):
        side = 1 if i % 2 else -1
        px = x + ca * i * 9 * k - sa * side * 2.6 * k
        py = y + sa * i * 9 * k + ca * side * 2.6 * k
        polys = [C._ell_pts(px, py, 1.7 * k, 1.4 * k, 12)[:-1]]
        for t, (u, v) in enumerate(((2.2, -1.6), (2.8, -.4), (2.8, .8), (2.2, 2.0))):
            tx = px + ca * u * k - sa * (v - .2) * k
            ty = py + sa * u * k + ca * (v - .2) * k
            polys.append(C._ell_pts(tx, ty, .65 * k, .55 * k, 8)[:-1])
        cv.obj(polys, .5)


def goose_swim(cv, x, y, s, flip=False, teal=False):
    """A cackling goose (or a blue-winged teal) swimming, waterline at y."""
    M = lambda p: _map(p, x, y, s, flip)
    if teal:
        body = M(_cr([(-6, -1), (-3, -4), (4, -4.2), (8, -2.4), (6, .2), (-5, .2)], True, 4))
        head = M(_cr([(-5, -3), (-6, -7), (-8.6, -7.6), (-10, -6), (-8, -5), (-6.5, -2.5)], True, 4))
        cv.obj([body, head], .5)
        cv.hair(C.hatch_poly(body, 0, 1.5))
        cface = M([(-8.4, -6.8), (-7.4, -7.2), (-7.4, -5.6)])
        cv.line(cface)
        cv.line(M([(-10, -6), (-11.6, -5.6)]))
        return
    body = M(_cr([(-8, -1), (-5, -5), (4, -5.6), (10, -4.4), (12, -2.4), (9, .2), (-7, .2)], True, 4))
    neck = M(_cr([(-6, -3.5), (-7.4, -9), (-7.6, -13), (-9.6, -14.4), (-11.8, -13.4), (-9.6, -12.4), (-9.2, -8.6), (-7.6, -3)], True, 4))
    cv.obj([body], .5)
    cv.hair(C.hatch_poly(body, 0, 1.5))
    cv.obj([neck], .5)
    _solid(cv, neck, 90)
    cv.obj([M(_cr([(-9.4, -12.6), (-8, -12.2), (-8.2, -10.6), (-9.2, -11.2)], True, 3))], 0)
    cv.line(M([(-11.8, -13.4), (-13.4, -13)]))
    cv.line(M([(-6, -.2), (8, -.2)]))


def cattail(cv, x, y, hgt, lean, rng, head=True):
    """A reed blade or bulrush rising from (x, y) hgt px, leaning `lean` (px at the top)."""
    pts = _cr([(x, y), (x + lean * .15, y - hgt * .4), (x + lean * .5, y - hgt * .75), (x + lean, y - hgt)], False, 6)
    if head:
        R = _rib(pts, 1.2, .5)
        cv.obj([R.outline()], .5)
        hi = int(len(pts) * .62)
        hx0, hy0 = pts[hi]
        hx1, hy1 = pts[min(len(pts) - 1, hi + 5)]
        ang = math.atan2(hy1 - hy0, hx1 - hx0)
        L = math.hypot(hx1 - hx0, hy1 - hy0)
        cx, cy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
        hw = max(2., hgt * .035)
        poly = [(cx + math.cos(ang) * L * .5 * math.cos(t) - math.sin(ang) * hw * math.sin(t),
                 cy + math.sin(ang) * L * .5 * math.cos(t) + math.cos(ang) * hw * math.sin(t)) for t in
                [TAU * i / 16 for i in range(16)]]
        cv.obj([poly], 1.)
        _solid(cv, poly, 45)
        # a highlight hairline down the lit side stays white: cover it with a thin white sliver
        hl = [(cx + math.cos(ang) * L * .35 * math.cos(t) - math.sin(ang) * hw * .35 * math.sin(t) - math.sin(ang) * hw * .3,
               cy + math.sin(ang) * L * .35 * math.cos(t) + math.cos(ang) * hw * .35 * math.sin(t) + math.cos(ang) * hw * .3)
              for t in [TAU * i / 12 for i in range(12)]]
        cv.obj([hl], 0)
    else:
        # a leaf blade: wide at the base, twisting, shaded on one side
        sg = 1 if lean >= 0 else -1
        n = len(pts)
        W = [max(.4, 2.6 * (1 - i / (n - 1)) ** .7) for i in range(n)]
        R = C._Rib(pts, W, [w * .6 for w in W])
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(-.2 * sg, 0, .8))
        C._shadow(cv, R, -sg, 1.2, .05, .7)


# ----------------------------------------------------------------------------------------------
# the scene: river at Frenchman's Bar, Mt. Hood, the gull, the egret, the reeds
# ----------------------------------------------------------------------------------------------

def scene(x, y, w, h, seed=0, mode="tall"):
    """The whole engraved view filling x..x+w, y..y+h (caller clips it)."""
    rng = random.Random(seed)
    cv = C.Canvas()
    band = mode == "band"
    hy = y + h * (.6 if band else .56)            # horizon (far shore waterline)
    # sky: ruled, darkening upward (engraver's sky), lines a fixed 2 px apart, weight by height
    sky = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, hy + 1), (x - 2, hy + 1)]
    cv.obj([sky], 0)
    yy = y - 1.75
    while yy < hy:
        t = (yy - y) / max(1., hy - y)
        if t < .38:
            cv.line([(x - 2, yy), (x + w + 2, yy)]) if t < .14 else cv.hair([(x - 2, yy), (x + w + 2, yy)])
            yy += 2 if t < .14 else 1.5
        else:
            cv.hair([(x - 2, yy), (x + w + 2, yy)])
            yy += 2 if t < .7 else 3
    # clouds, lit from the low winter sun
    if not band:
        for (cx, cy, cw) in ((x + w * .78, y + h * .14, w * .26), (x + w * .14, y + h * .46, w * .22)):
            pts = []
            lobes = [(cx - cw * .38, cw * .12), (cx - cw * .16, cw * .19), (cx + cw * .08, cw * .23),
                     (cx + cw * .3, cw * .15)]
            for i in range(41):
                px = cx - cw * .5 + cw * i / 40
                top = max([math.sqrt(max(0, r * r - (px - lx) ** 2)) for lx, r in lobes] + [0])
                pts.append((px, cy - top * .8))
            base = [(cx + cw * .5, cy + 1), (cx - cw * .5, cy + 1)]
            poly = pts + base
            cv.obj([poly], .5)
            for k in range(1, 4):
                cv.hair([(cx - cw * (.44 - k * .05), cy - k * 1.5), (cx + cw * (.44 - k * .06), cy - k * 1.5)])
    # Mt. Hood on the horizon
    mx, mw, mh = x + w * (.68 if not band else .7), w * (.36 if not band else .5), h * (.27 if not band else .3)
    prof = [(-1, 0), (-.82, .1), (-.66, .2), (-.5, .33), (-.36, .47), (-.24, .62), (-.13, .78), (-.06, .9), (0, 1),
            (.05, .95), (.1, .87), (.17, .78), (.25, .67), (.34, .55), (.46, .41), (.6, .27), (.76, .15), (.9, .07), (1, 0)]
    MP = lambda p: [(mx + u * mw / 2, hy - v * mh) for u, v in p]
    mt = MP(prof)
    cv.obj([mt], .5)
    cv.hair(C.hatch_poly(mt, 0, 2., .25))
    snow = MP([(-.36, .47), (-.24, .62), (-.13, .78), (-.06, .9), (0, 1), (.05, .95), (.1, .87), (.17, .78), (.25, .67),
               (.34, .55), (.3, .5), (.25, .56), (.2, .46), (.15, .55), (.1, .4), (.05, .5), (0, .36), (-.05, .5), (-.1, .42),
               (-.16, .55), (-.22, .47), (-.28, .52)])
    cv.obj([snow], 0)
    # shadow flank (sun low in the south-east, behind and to the right: west face in shade)
    shade = MP([(0, 1), (-.06, .9), (-.13, .78), (-.24, .62), (-.36, .47), (-.5, .33), (-.66, .2), (-.82, .1), (-1, 0),
                (-.3, 0), (-.18, .2), (-.12, .38), (-.07, .55), (-.03, .75)])
    cv.obj([shade], 0)
    cv.hair(C.hatch_poly(shade, 45, 2.))
    for g in ((.02, .92, .06, .55), (.12, .8, .2, .5), (.2, .7, .3, .48), (-.04, .88, -.02, .6)):
        cv.hair(MP([(g[0], g[1]), ((g[0] + g[2]) / 2 + .01, (g[1] + g[3]) / 2), (g[2], g[3])]))
    # far shore: Douglas firs along the Washington bank
    top = []
    xx = x - 2
    while xx < x + w + 2:
        th = rng.uniform(.03, .065) * h if not band else rng.uniform(.04, .08) * h
        tw = rng.uniform(3, 6)
        top += [(xx, hy - th * .25), (xx + tw * .5, hy - th), (xx + tw, hy - th * .3)]
        xx += tw
    shore = top + [(x + w + 2, hy + 1.5), (x - 2, hy + 1.5)]
    cv.obj([shore], .5)
    cv.line(C.hatch_poly(shore, 0, 1.5))
    # the river, its glint lane under the light
    wy1 = y + h + 2
    water = [(x - 2, hy + 1.5), (x + w + 2, hy + 1.5), (x + w + 2, wy1), (x - 2, wy1)]
    cv.obj([water], 0)
    cv.hair(_wave_rows(x - 2, x + w + 2, hy + 2.75, hy + 6, 1.5, rng, (10, 40), (1, 3)))
    cv.hair(_wave_rows(x - 2, x + w + 2, hy + 8, wy1, 2, rng, (6, 22), (2, 6), lane=(x + w * .43, w * .07)))
    # Mt. Hood's reflection, broken
    for k in range(5):
        ry = hy + 4 + k * 3
        half = mw * (.18 - k * .03)
        if half > 2:
            cv.hair([(mx - half, ry), (mx + half * .4, ry)])
    # Cackling Geese in a V, far off
    if not band:
        gx, gy = x + w * .5, y + h * .12
        for i in range(-3, 5):
            k = abs(i)
            step = min(w * .022, h * .04)
            bx, by = gx + i * step * 1.4 + (k * step * 1.3 if i < 0 else 0), gy + k * step * .9
            bs = max(1.5, min(h * .008, step * .4))
            cv.obj([], 0)
            cv.line([(bx - bs * 1.6, by - bs * .6), (bx - bs * .6, by - bs * .1), (bx, by + bs * .3),
                     (bx + bs * .6, by - bs * .1), (bx + bs * 1.6, by - bs * .7)])
    # the gull: the morning's rare bird
    if band:
        gull(cv, x + w * .4, y + h * .5, min(w * .5, h * .95), phase=rng.uniform(-1, 1))
    elif mode == "med":
        gull(cv, x + w * .3, y + h * .36, min(w * .34, h * .62), phase=rng.uniform(-1, 1))
    else:
        gull(cv, x + w * .33, y + h * .33, min(w * .38, h * .5), phase=rng.uniform(-1, 1))
    # foreground mud bank (Frenchman's Bar is a sand-and-mud bar)
    if not band or h > 44:
        mt0 = y + h * (.8 if not band else .86)
        mud_top = [(x - 2 + w * i / 30, mt0 + h * .04 * math.sin(i / 30 * 5.2 + .6) - (h * .05) * (i / 30) ** 2)
                   for i in range(31)]
        mud = [(x - 2, mt0)] + mud_top + [(x + w + 2, y + h + 2), (x - 2, y + h + 2)]
        cv.obj([mud], 1.)
        # contour hatching along the bank, dense at the lip
        for k in range(1, 40):
            off = 1.5 * k if k < 6 else 9 + (k - 6) * 2
            pl = [(px, py + off) for px, py in mud_top]
            if pl[0][1] > y + h + 2:
                break
            cv.hair(pl)
        # the egg: a dog's paw prints in the mud
        k = max(1., min(1.6, h / 180))
        paw_trail(cv, x + w * (.42 if not band else .12), y + h * (.92 if not band else .95), k,
                  4 if not band else 3, -.12)
    # the egret, and the reeds it stands in
    if not band:
        EH = h * (.6 if mode == "tall" else .62)
        ex, ey = x + w * (.7 if mode == "tall" else .7), y + h * .88
        # ripples round its feet
        cv.obj([], 0)
        egret(cv, ex, ey, EH, seed=seed)
        cv.obj([], 0)
        for r in (1, 1.6, 2.3):
            cv.hair(C._ell_pts(ex + EH * .02, ey + 1, EH * .07 * r, EH * .012 * r, 20, .15, PI - .15))
        # reeds: a stand at the left edge, a few at the right, cattails among them
        for cx0, n, hmax, lean_dir in ((x + w * .1, 9 if mode == "tall" else 6, .55, 1), (x + w * .9, 6, .45, -1)):
            for i in range(n):
                rx = cx0 + lean_dir * i * w * .012 + rng.uniform(-2, 2)
                hg = h * hmax * rng.uniform(.55, 1.)
                lean = lean_dir * rng.uniform(-.05, .25) * hg
                cattail(cv, rx, y + h + 2, hg, lean, rng, head=(i % 3 == 1))
    return cv.svg()


def scene_clipped(cid, clip_d, x, y, w, h, seed, mode):
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{scene(x, y, w, h, seed, mode)}</g>')


# ----------------------------------------------------------------------------------------------
# banner quill and tablet frieze


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) * 7 + 3
    P = dict(seed=seed, form="vignette", share=.25, shape="oval", vig_aspect=2.2, vig_med_a=.5, vig_med_b=.72,
             stems=1, med_aspect=.8,
             legend="Bonaparte's Gull · Frenchman's Bar", tablet="Feathered Neighbors",
             scene=lambda x, y, fw, fh, lod: scene(x, y, fw, fh, seed, ("band", "medium", "tall")[lod]))
    return ST5.free_plate(w, h, ctx, dict(P, aspect=1.75, shape="oval"))
