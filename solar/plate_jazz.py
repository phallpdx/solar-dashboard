"""Jazz plate for Parker's Kindle Evening Edition: a bulino-style engraved vignette.

plate(width, height, seed) -> complete <svg> string drawn in CSS px (no viewBox scaling), so every
stroke width and hatch pitch is a multiple of 0.5 px (1 device px at DPR 2).

Short sizes (height < 170) give a running frieze -- drum kit, saxophone, keyboard and upright bass
strung on an acanthus scroll that ends in tendrils.  Taller sizes give a club stage under one
hanging lamp: curtains, drum kit, a leaning upright bass, and the dog asleep on the rug.  There is
no frame: like a banknote vignette, the line work thins and breaks off into the white paper.

Standard library only.  All ids are prefixed "pj<seed>".
"""
import math
import random


def _n(v):
    s = "%.1f" % v
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s == "-0" else s


def _pl(pts, close=False):
    """Path data: absolute move, then relative lines between rounded points (compact)."""
    r = [(round(x * 10), round(y * 10)) for x, y in pts]
    out = ["M%s %s" % (_n(r[0][0] / 10.0), _n(r[0][1] / 10.0))]
    rel = []
    for (ax, ay), (bx, by) in zip(r, r[1:]):
        if (ax, ay) != (bx, by):
            dx, dy = _n((bx - ax) / 10.0), _n((by - ay) / 10.0)
            rel.append(dx + ("" if dy.startswith("-") else " ") + dy)
    if rel:
        out.append("l" + " ".join(rel).replace(" -", "-"))
    return "".join(out) + ("z" if close else "")


class _Plate:
    def __init__(self, w, h, seed):
        self.w, self.h, self.seed = w, h, seed
        self.rng = random.Random(seed)
        self.pre = "pj%s" % seed
        self.defs = []
        self.nclip = 0
        self.pats = {}
        self.layers = []
        self.layer()

    def layer(self):
        """Start a new layer; its white masks knock out the line work of layers beneath."""
        self.strokes = {}          # width -> list of path data
        self.fills = []            # swelling burin cuts (filled outlines)
        self.body = []             # clipped hatch families
        self.masks = []            # paper-white silhouettes (occlusion, not tone)
        self.layers.append((self.masks, self.body, self.strokes, self.fills))

    def mask(self, pts):
        self.masks.append(_pl(pts, True))

    # -- primitives --------------------------------------------------------------------------
    def line(self, pts, w=0.5, close=False):
        if len(pts) > 1:
            self.strokes.setdefault(w, []).append(_pl(pts, close))

    def swell(self, pts, wmax, w0=0.0, w1=0.0):
        """A burin cut: width rises from w0 to wmax mid-stroke and falls to w1."""
        if len(pts) == 3:
            (ax, ay), (bx, by), (cx, cy) = pts
            m = int(min(9, max(2, (math.hypot(bx - ax, by - ay) + math.hypot(cx - bx, cy - by)) / 5)))
            pts = [((1 - t) ** 2 * ax + 2 * t * (1 - t) * bx + t * t * cx,
                    (1 - t) ** 2 * ay + 2 * t * (1 - t) * by + t * t * cy)
                   for t in [i / float(m) for i in range(m + 1)]]
        n = len(pts)
        if n < 2:
            return
        left, right = [], []
        for i, (x, y) in enumerate(pts):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, n - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1.0
            t = i / (n - 1)
            base = w0 + (w1 - w0) * t
            wv = base + (wmax - base) * math.sin(math.pi * t) ** 0.8
            hw = max(wv, 0.25) / 2
            nx, ny = -dy / L * hw, dx / L * hw
            left.append((x + nx, y + ny))
            right.append((x - nx, y - ny))
        self.fills.append(_pl(left + right[::-1], True))

    def arc(self, w, cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, n=None, rot=0.0):
        """Elliptic arc as SVG 'A' commands (compact)."""
        c, s = math.cos(rot), math.sin(rot)
        P = lambda t: (cx + rx * math.cos(t) * c - ry * math.sin(t) * s,
                       cy + rx * math.cos(t) * s + ry * math.sin(t) * c)
        span = a1 - a0
        k = 2 if abs(span) > math.pi else 1
        x, y = P(a0)
        d = "M%s %s" % (_n(x), _n(y))
        for i in range(1, k + 1):
            x, y = P(a0 + span * i / k)
            d += "A%s %s %s 0 %d %s %s" % (_n(rx), _n(ry), _n(math.degrees(rot)), 1 if span > 0 else 0, _n(x), _n(y))
        self.strokes.setdefault(w, []).append(d)

    def clip(self, d, evenodd=False):
        self.nclip += 1
        cid = "%sc%d" % (self.pre, self.nclip)
        rule = ' clip-rule="evenodd"' if evenodd else ""
        self.defs.append('<clipPath id="%s"><path%s d="%s"/></clipPath>' % (cid, rule, d))
        return cid

    def hatch(self, cid, box, angle, pitch, w=0.5, gap=None, clip2=None):
        """Parallel straight cuts at `pitch` px, clipped to clip `cid`.  gap=(cx,cy,rx,ry): a
        vignette ellipse -- lines thin, break and stop near its edge."""
        x0, y0, x1, y1 = box
        if not gap:
            # uniform hatching: one tiny <pattern> tile, rotated by patternTransform
            key = (angle, pitch, w)
            if key not in self.pats:
                pid = "%sp%d" % (self.pre, len(self.pats))
                self.pats[key] = pid
                self.defs.append('<pattern id="%s" patternUnits="userSpaceOnUse" width="8" height="%s"%s>'
                                 '<path d="M-1 %sh10" stroke="#000" stroke-width="%s"/></pattern>'
                                 % (pid, _n(pitch), ' patternTransform="rotate(%s)"' % _n(angle) if angle else "",
                                    _n(pitch / 2), _n(w)))
            r = ('<rect clip-path="url(#%s)" fill="url(#%s)" stroke="none" x="%s" y="%s" '
                 'width="%s" height="%s"/>' % (cid, self.pats[key], _n(x0), _n(y0),
                                              _n(x1 - x0), _n(y1 - y0)))
            if clip2:
                r = '<g clip-path="url(#%s)">%s</g>' % (clip2, r)
            self.body.append(r)
            return
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        R = math.hypot(x1 - x0, y1 - y0) / 2 + 2
        a = math.radians(angle)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        segs = []
        ks = [(x - cx) * nx + (y - cy) * ny for x in (x0, x1) for y in (y0, y1)]
        k = min(ks) + pitch / 2
        while k <= max(ks):
            px, py = cx + nx * k, cy + ny * k
            p0 = (px - ux * R, py - uy * R)
            p1 = (px + ux * R, py + uy * R)
            if gap:
                p0, p1 = self._vig_cut(p0, p1, gap)
            if p0:
                segs.append(_pl([p0, p1]))
            k += pitch
        if segs:
            self.body.append('<path clip-path="url(#%s)" stroke-width="%s" d="%s"/>'
                             % (cid, _n(w) if w != 0.5 else ".5", "".join(segs)))

    def _vig_cut(self, p0, p1, gap):
        """Trim the segment to a jittered ellipse so line ends break off irregularly."""
        gx, gy, rx, ry = gap
        j = 1 + self.rng.uniform(-0.09, 0.05)
        rx, ry = rx * j, ry * j
        # solve |((p0 + t (p1-p0)) - g) / r| = 1
        dx, dy = (p1[0] - p0[0]) / rx, (p1[1] - p0[1]) / ry
        ex, ey = (p0[0] - gx) / rx, (p0[1] - gy) / ry
        A = dx * dx + dy * dy
        B = 2 * (ex * dx + ey * dy)
        C = ex * ex + ey * ey - 1
        disc = B * B - 4 * A * C
        if disc <= 0 or A == 0:
            return None, None
        s = math.sqrt(disc)
        t0, t1 = max((-B - s) / (2 * A), 0), min((-B + s) / (2 * A), 1)
        if t1 <= t0:
            return None, None
        f = lambda t: (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
        return f(t0), f(t1)

    def svg(self):
        parts = []
        for masks, body, strokes, fl in self.layers:
            if masks:
                parts.append('<path fill="#fff" stroke="none" d="%s"/>' % "".join(masks))
            parts.extend(body)
            for w in sorted(strokes):
                parts.append('<path stroke-width="%s" d="%s"/>' % (_n(w) if w != 0.5 else ".5",
                                                                  "".join(strokes[w])))
            if fl:
                parts.append('<path fill="#000" stroke="none" d="%s"/>' % "".join(fl))
        return ('<svg xmlns="http://www.w3.org/2000/svg" id="%s" width="%d" height="%d" '
                'viewBox="0 0 %d %d" role="img" aria-label="Engraved jazz plate">'
                '<defs>%s</defs><g fill="none" stroke="#000" stroke-linecap="round" '
                'stroke-linejoin="round">%s</g></svg>'
                % (self.pre, self.w, self.h, self.w, self.h, "".join(self.defs), "".join(parts)))


def _ell(cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, n=None, rot=0.0):
    if n is None:
        n = max(6, int(abs(a1 - a0) * max(rx, ry) / 6) + 2)
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


# ------------------------------------------------------------------------------ instruments

def _cymbal(P, cx, cy, rx, rot=0.0, stand_to=None):
    ry = max(rx * 0.2, 2.0)
    P.mask(_ell(cx, cy, rx + 1, ry + 1, n=16, rot=rot))
    P.swell(_ell(cx, cy, rx, ry, 0.15, math.pi - 0.15, rot=rot), 1.5, 0.5, 0.5)
    P.arc(0.5, cx, cy, rx, ry, math.pi, 2 * math.pi, rot=rot)
    # lathe rings: concentric ellipses, tighter toward the rim
    r = rx - 1.5
    i = 0
    while r > rx * 0.22:
        a0, a1 = (0.0, 2 * math.pi) if i % 2 == 0 else (0.3, math.pi - 0.3)
        P.arc(0.5, cx, cy, r, r * ry / rx, a0, a1, rot=rot)
        r -= 1.5 + 1.5 * (i % 3 == 2)
        i += 1
    bell = rx * 0.18
    P.arc(1, cx, cy - ry * 0.25, bell, bell * 0.55, math.pi, 2 * math.pi, rot=rot)
    if stand_to:
        P.line([(cx, cy + ry * 0.4), (cx, stand_to)], 1)


def _cylinder(P, cx, ytop, rx, ry, h, light=-0.5, lugs=6):
    """Drum shell: hoop ellipses + vertical contour cuts that crowd at the edges (round form)
    and swell on the shadow side."""
    P.mask(_ell(cx, ytop, rx + 1, ry + 1, math.pi, 2 * math.pi, n=8) + _ell(cx, ytop + h, rx + 1, ry + 1, 0, math.pi, n=8))
    P.swell(_ell(cx, ytop, rx, ry), 1.5, 1, 1)
    P.arc(0.5, cx, ytop + 2, rx, ry, 0, math.pi)
    P.swell(_ell(cx, ytop + h, rx, ry, 0, math.pi), 1.5, 1, 1)
    P.arc(0.5, cx, ytop + h - 2, rx, ry, 0, math.pi)
    P.line([(cx - rx, ytop), (cx - rx, ytop + h)], 1)
    P.line([(cx + rx, ytop), (cx + rx, ytop + h)], 1.5)
    steps = max(6, int(rx * math.pi / 2 / 1.5))
    for i in range(1, steps * 2):
        th = -math.pi / 2 + math.pi * i / (steps * 2)
        sx = math.sin(th)
        x = cx + rx * sx
        tone = (sx - light) / (1 - light)
        if tone < 0.25 or i % 2 and tone < 0.6:
            continue
        y0 = ytop + 2.5 + ry * math.cos(th)
        y1 = ytop + h - 2.5 + ry * math.cos(th)
        if y1 - y0 < 2:
            continue
        P.line([(x, y0), (x, y1)], 1.5 if tone > 0.85 else (1 if tone > 0.6 else 0.5))
    for k in range(lugs):
        th = -math.pi / 2 + math.pi * (k + 0.5) / lugs
        x = cx + rx * math.sin(th) * 0.98
        yo = ry * math.cos(th)
        P.line([(x, ytop + 2 + yo), (x, ytop + h - 2 + yo)], 1)


def _drum_kit(P, ox, oy, s):
    """Base centre (ox, oy); s = px per unit, kit ~100 units tall."""
    X = lambda u: ox + u * s
    Y = lambda v: oy + v * s
    # stands
    P.line([(X(-50), Y(-74)), (X(-50), Y(0))], 1)
    for d in (-1, 1):
        P.line([(X(-50), Y(-14)), (X(-50 + 9 * d), Y(0))], 0.5)
        P.line([(X(46), Y(-14)), (X(46 + 9 * d), Y(0))], 0.5)
    _cymbal(P, X(-50), Y(-74), 15 * s)
    _cymbal(P, X(-50), Y(-71), 15 * s)
    _cymbal(P, X(46), Y(-86), 21 * s, rot=0.08, stand_to=Y(0))
    _cymbal(P, X(-30), Y(-95), 17 * s, rot=-0.2)
    P.line([(X(-30), Y(-93)), (X(-24), Y(-62))], 1)
    _cylinder(P, X(6), Y(-74), 11 * s, 3.5 * s, 12 * s, lugs=4)
    P.layer()
    # bass drum (front head) with lathe rings and a monogram
    r = 30 * s
    bx, by = X(0), Y(-30)
    P.mask(_ell(bx, by, r + 3.5, r + 3.5, n=24))
    P.swell(_ell(bx, by, r, r), 2.5, 1.5, 1.5)
    P.arc(1, bx, by, r - 3, r - 3)
    rr = r - 5.5
    while rr > r * 0.55:
        P.arc(0.5, bx, by, rr, rr, -0.3, 1.9)
        rr -= 1.5
    head = P.clip(_pl(_ell(bx, by, r - 3, r - 3), True))
    sh = P.clip(_pl([(bx - 2 * r, by - 2 * r), (bx + 2 * r, by - 2 * r), (bx + 2 * r, by + 2 * r), (bx - 2 * r, by + 2 * r)], True)
                + _pl(_ell(bx - r * 0.2, by - r * 0.25, r * 0.95, r * 0.95), True), True)
    P.hatch(sh, (bx - r, by - r, bx + r, by + r), 30, 2, clip2=head)
    sh2 = P.clip(_pl([(bx - 2 * r, by - 2 * r), (bx + 2 * r, by - 2 * r), (bx + 2 * r, by + 2 * r), (bx - 2 * r, by + 2 * r)], True)
                 + _pl(_ell(bx - r * 0.12, by - r * 0.15, r * 0.95, r * 0.95), True), True)
    P.hatch(sh2, (bx - r, by - r, bx + r, by + r), -40, 2, clip2=head)
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.3
        c, si = math.cos(a), math.sin(a)
        P.line([(bx + c * (r - 1), by + si * (r - 1)), (bx + c * (r + 3), by + si * (r + 3))], 1.5)
    P.body.append('<text x="%s" y="%s" font-family="Georgia,serif" font-style="italic" '
                  'font-size="%s" text-anchor="middle" fill="none" stroke="#000" '
                  'stroke-width=".5">P</text>' % (_n(bx), _n(by + r * 0.3), _n(r * 0.95)))
    P.arc(0.5, bx, by, r * 0.5, r * 0.5, 0.2, 2.9)
    # snare, rack tom, floor tom
    P.layer()
    _cylinder(P, X(-36), Y(-46), 15 * s, 4 * s, 11 * s)
    P.line([(X(-36), Y(-46 + 15)), (X(-36), Y(0))], 1)
    for d in (-1, 1):
        P.line([(X(-36), Y(-12)), (X(-36 + 10 * d), Y(0))], 0.5)
    _cylinder(P, X(42), Y(-40), 15 * s, 4 * s, 28 * s)
    for d in (-1, 1):
        P.line([(X(42 + 13 * d), Y(-20)), (X(42 + 15 * d), Y(0))], 1)
    # sticks resting across the floor tom
    P.swell([(X(26), Y(-46)), (X(42), Y(-49)), (X(60), Y(-52))], 1.5, 0.5, 1)
    P.swell([(X(30), Y(-50)), (X(44), Y(-47)), (X(58), Y(-43))], 1.5, 0.5, 1)
    # ground shadow: short horizontal hairlines
    for i in range(4):
        y = oy + 1 + i * 1.5
        P.line([(X(-58 + i * 4), y), (X(64 - i * 5), y)], 0.5)


def _bass(P, ox, oy, s, lean=-0.21):
    """Upright bass, endpin at (ox, oy), ~100 units tall, leaning."""
    c, si = math.cos(lean), math.sin(lean)
    T = lambda u, v: (ox + (u * c - v * si) * s, oy + (u * si + v * c) * s)

    def hw(v):  # half-width of the body along its height (v from -6 to -58)
        t = (-v - 6) / 52.0
        t = min(max(t, 0), 1)
        w = (11.5 + 3.8 * math.cos(2 * math.pi * (t - 0.25) / 0.62)) * (1 - 0.22 * t)
        if t > 0.55:
            w = max(w, 8.6 * (1 - 0.22 * t))
        return w * (math.sin(t * math.pi) ** 0.3)

    vs = [-6 - 52 * i / 40 for i in range(41)]
    right = [T(hw(v), v) for v in vs]
    left = [T(-hw(v), v) for v in vs]
    outline = right + left[::-1]
    P.mask([T(hw(v) + 1.5, v) for v in vs[::4]] + [T(3.5, -93), T(3, -101), T(-3, -101), T(-3.5, -93)] +
           [T(-hw(v) - 1.5, v) for v in vs[::-4]])
    P.swell(right, 2.5, 1, 1)
    P.swell(left, 1.5, 1, 1)
    # inner purfling
    P.line([T(hw(v) - 1.6, v) for v in vs[2:-2]] , 0.5)
    P.line([T(-hw(v) + 1.6, v) for v in vs[2:-2]], 0.5)
    cid = P.clip(_pl(outline, True))
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    box = (min(xs), min(ys), max(xs), max(ys))
    # modelling: contour cuts following the body's swell on the shadow side
    for k in range(1, 9):
        f = 1 - k * 0.075
        pts = [T(hw(v) * f, v) for v in vs[3:-3:2]]
        if k < 4:
            P.swell(pts, 0.5 + 0.25 * (4 - k), 0.5, 0.5)
        else:
            P.line(pts, 0.5)
    # wood grain: long hairlines down the top, sparse
    for g in (-0.6, -0.35, -0.1, 0.15):
        P.line([T(hw(v) * g, v) for v in vs[4:-4:3]], 0.5)
    sh = P.clip(_pl([T(hw(v) * 0.45, v) for v in vs] + [T(40, -60), T(40, 0)], True))
    P.hatch(sh, box, 70, 2, clip2=cid)
    P.hatch(cid, box, -20, 2.5)
    # f-holes
    for d in (-1, 1):
        P.swell([T(d * 5 + d * 1.5 * math.sin(t * 3.3), -26 - t * 12) for t in [i / 8 for i in range(9)]], 1.5, 1, 1)
    # bridge, tailpiece, fingerboard, neck, scroll
    P.line([T(-4.5, -24.5), T(4.5, -24.5)], 1.5)
    P.swell([T(0, -8), T(0, -12), T(0, -17)], 3, 2, 1)
    P.swell([T(0, -30), T(0, -60), T(0, -92)], 3, 2.5, 2)
    P.line([T(-2.5, -58), T(-1.8, -93)], 1)
    P.line([T(2.5, -58), T(1.8, -93)], 1.5)
    for k in range(4):
        u = -1.5 + k
        P.line([T(u * 0.9, -16), T(u * 1.5, -24.5), T(u * 0.5, -92)], 0.5)
    sp = []
    for i in range(30):
        a = i / 29 * 4.2
        rr = 4.2 * (1 - i / 36)
        sp.append(T(1 + rr * math.cos(a + 2.5), -97 + rr * math.sin(a + 2.5)))
    P.swell(sp, 2, 1, 0.5)
    P.line([T(-1.8, -93), T(-3, -96)], 1)
    P.line([T(0, -2), T(0, -6)], 1.5)


def _dog(P, ox, oy, s, rng):
    """A curled sleeping dog, belly line at (ox, oy), about 70 x 26 units."""
    X = lambda u: ox + u * s
    Y = lambda v: oy + v * s
    P.mask(_ell(X(4), Y(-10), 29 * s, 13 * s, n=20) + _ell(X(-24), Y(-7), 17 * s, 9 * s, n=12))
    # body
    body = _ell(X(4), Y(-11), 27 * s, 12 * s, math.pi * 1.02, math.pi * 2.02)
    P.swell(body, 2, 1, 1)
    P.swell([(X(31), Y(-9)), (X(26), Y(-1)), (X(10), Y(0.5)), (X(-14), Y(0))], 1.5, 1, 0.5)
    # haunch
    P.swell(_ell(X(18), Y(-9), 11 * s, 8 * s, math.pi * 1.1, math.pi * 2.3), 1.5, 0.5, 0.5)
    # fur: short swelling strokes following the body contour, denser toward the belly
    for ring in range(1, 6):
        f = 1 - ring * 0.15
        for j in range(16):
            a = math.pi * (1.08 + 0.9 * j / 15) + rng.uniform(-0.04, 0.04)
            if ring < 3 and j % 2:
                continue
            cx, cy = X(4) + 27 * s * f * math.cos(a), Y(-11) + 12 * s * f * math.sin(a)
            da = 0.12
            seg = [(X(4) + 27 * s * f * math.cos(a + d), Y(-11) + 12 * s * f * math.sin(a + d) + d * 6 * s)
                   for d in (-da, 0, da)]
            P.line(seg, 1 if ring > 3 else 0.5)
    for i in range(int(36 * s / 1.5)):
        x = X(-20) + i * 1.5
        if x > X(28):
            break
        P.line([(x, Y(-3.5) + rng.uniform(-0.5, 0.5)), (x + 0.8, Y(-0.5))], 0.5)
    dc = P.clip(_pl(_ell(X(4), Y(-10.5), 27 * s, 11.5 * s, n=20), True))
    low = P.clip(_pl([(X(-30), Y(-6)), (X(20), Y(-9)), (X(40), Y(-14)), (X(40), Y(4)), (X(-30), Y(4))], True))
    P.hatch(low, (X(-24), Y(-24), X(32), Y(2)), 15, 2, clip2=dc)
    deep = P.clip(_pl([(X(-30), Y(-2.5)), (X(30), Y(-5)), (X(40), Y(4)), (X(-30), Y(4))], True))
    P.hatch(deep, (X(-24), Y(-24), X(32), Y(2)), -50, 2, clip2=dc)
    hc = P.clip(_pl(_ell(X(-22), Y(-7), 9 * s, 7 * s, n=14), True))
    P.hatch(P.clip(_pl([(X(-32), Y(-5)), (X(-12), Y(-7)), (X(-12), Y(2)), (X(-32), Y(2))], True)),
            (X(-32), Y(-15), X(-12), Y(2)), 20, 2, clip2=hc)
    # tail curled around the front
    P.swell([(X(30), Y(-4)), (X(24), Y(1.5)), (X(8), Y(2.5)), (X(-6), Y(1))], 2.5, 1.5, 0.5)
    # head resting on forepaws
    P.swell(_ell(X(-22), Y(-8), 9 * s, 7 * s, math.pi * 0.9, math.pi * 2.1), 2, 1, 1)
    P.swell([(X(-30), Y(-11)), (X(-37), Y(-8)), (X(-39), Y(-4)), (X(-33), Y(-1.5))], 1.5, 1, 1)
    P.fills.append(_pl(_ell(X(-39), Y(-7.5), 1.6 * s, 1.2 * s, n=8), True))  # nose
    P.swell(_ell(X(-27), Y(-10), 2.5 * s, 1.5 * s, 0.1, math.pi - 0.1), 1, 0.5, 0.5)  # shut eye
    ear = [(X(-20), Y(-14)), (X(-14), Y(-12)), (X(-12), Y(-5)), (X(-16), Y(-3)), (X(-19), Y(-8))]
    P.swell(ear, 2, 1, 0.5)
    P.hatch(P.clip(_pl(ear, True)), (X(-21), Y(-15), X(-11), Y(-2)), 70, 1.5)
    P.swell([(X(-35), Y(-2.5)), (X(-26), Y(0.5)), (X(-15), Y(-1.5))], 1.5, 1, 0.5)   # jowl
    P.swell([(X(-30.5), Y(-12)), (X(-29), Y(-9.5)), (X(-31), Y(-7))], 1, 0.5, 0.5)   # stop
    P.swell(_ell(X(16), Y(-1), 4.5 * s, 2.2 * s, math.pi * 0.6, math.pi * 1.9), 1.5, 1, 0.5)  # hind paw
    P.line([(X(-17), Y(-12)), (X(-15), Y(-6))], 0.5)
    P.line([(X(-16), Y(-11)), (X(-14), Y(-5))], 0.5)
    for k in range(2):
        P.swell([(X(-34 + k * 5), Y(0)), (X(-24 + k * 4), Y(0.2)), (X(-14 + k * 3), Y(-1))], 1.5, 1, 0.5)
    # muzzle and cheek hairs
    for k in range(4):
        P.line([(X(-30 + k * 2), Y(-6.5 + k * 0.4)), (X(-28 + k * 2), Y(-3 + k * 0.3))], 0.5)


def _sax(P, ox, oy, s):
    """Saxophone, base of the bow at (ox, oy), ~100 units tall."""
    cl = []
    for i in range(40):  # body down
        t = i / 39
        cl.append((0 - 2 * t, -78 + 62 * t))
    for i in range(1, 20):  # U-bend
        a = math.pi * i / 19
        cl.append((-2 + 9 - 9 * math.cos(a) - 0, -16 + 9 * math.sin(a)))
    for i in range(1, 26):  # rising bell
        t = i / 25
        cl.append((16 + 6 * t, -16 - 32 * t))
    rad = [2.6 + 5.0 * (i / len(cl)) ** 1.6 for i in range(len(cl))]
    for j in range(len(cl) - 12, len(cl)):
        rad[j] += 6 * ((j - len(cl) + 12) / 12) ** 2.2
    pts = [(ox + x * s, oy + y * s) for x, y in cl]
    rad = [r * s for r in rad]
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        left.append((x + nx * rad[i], y + ny * rad[i]))
        right.append((x - nx * rad[i], y - ny * rad[i]))
        # ring hatching across the tube: contour cuts on the shadow half
        if i % 2 == 0 and i < len(pts) - 2:
            P.line([(x + nx * rad[i] * 0.15, y + ny * rad[i] * 0.15),
                    (x + nx * rad[i] * 0.97, y + ny * rad[i] * 0.97)], 1 if i % 4 == 0 else 0.5)
    P.mask(left[::3] + [left[-1], right[-1]] + right[::-3])
    P.mask(_ell(pts[-1][0], pts[-1][1], rad[-1] + 1, rad[-1] * 0.4 + 1, n=12))
    P.swell(left, 2, 1, 1)
    P.swell(right, 1.5, 0.5, 1)
    bx, by = pts[-1]
    P.swell(_ell(bx, by, rad[-1], rad[-1] * 0.35, rot=0.18), 1.5, 1, 1)
    P.arc(0.5, bx, by, rad[-1] - 1.5, rad[-1] * 0.35 - 1, 0, math.pi, rot=0.18)
    # neck and mouthpiece
    nk = [(ox, oy - 78 * s), (ox - 1 * s, oy - 88 * s), (ox - 6 * s, oy - 95 * s), (ox - 13 * s, oy - 96 * s)]
    P.swell(nk, 2.5, 3, 1.5)
    P.line([(ox - 13 * s, oy - 96 * s), (ox - 18 * s, oy - 95.5 * s)], 1.5)
    # keys: pearl buttons with rods
    for k in range(7):
        i = 5 + k * 5
        x, y = pts[i]
        r = 2 * s
        P.arc(1, x - rad[i] * 0.2, y, r, r, n=10)
        P.line([(x - rad[i] * 0.2 + r, y), (x + rad[i] * 1.3, y + 1)], 0.5)
    P.line([(pts[5][0] + rad[5] * 1.3, pts[5][1]), (pts[35][0] + rad[35] * 1.3, pts[35][1])], 0.5)


def _keys(P, x0, y0, wk, hk, n):
    """A run of piano keys; black keys are cross-hatched, never solid."""
    x1 = x0 + wk * n
    P.mask([(x0 - 1, y0 - 1), (x1 + 1, y0 - 1), (x1 + 1, y0 + hk + 1), (x0 - 1, y0 + hk + 1)])
    P.line([(x0, y0), (x1, y0)], 1)
    P.swell([(x0, y0 + hk), ((x0 + x1) / 2, y0 + hk), (x1, y0 + hk)], 1.5, 1, 1)
    for i in range(n + 1):
        P.line([(x0 + i * wk, y0), (x0 + i * wk, y0 + hk)], 0.5)
    pat = [1, 1, 0, 1, 1, 1, 0]
    for i in range(n - 1):
        if not pat[i % 7]:
            continue
        bx = x0 + (i + 1) * wk - wk * 0.32
        bw, bh = wk * 0.64, hk * 0.6
        d = _pl([(bx, y0), (bx + bw, y0), (bx + bw, y0 + bh), (bx, y0 + bh)], True)
        cid = P.clip(d)
        P.hatch(cid, (bx, y0, bx + bw, y0 + bh), 90, 1.5)
        P.hatch(cid, (bx, y0, bx + bw, y0 + bh), 35, 2)
        P.line([(bx, y0), (bx, y0 + bh), (bx + bw, y0 + bh), (bx + bw, y0)], 0.5)


def _scroll(P, x0, x1, ymid, amp, rng, curl=1.0):
    """Running acanthus scroll: a swelling stem with alternating spiral curls and leaf cuts."""
    n = max(2, int((x1 - x0) / (amp * 3.2)))
    lam = (x1 - x0) / n
    stem = [(x0 + (x1 - x0) * i / 72, ymid + amp * 0.45 * math.sin(2 * math.pi * i / 72 * n))
            for i in range(73)]
    P.swell(stem, 1.5, 0.5, 0.5)
    for k in range(n):
        side = 1 if k % 2 else -1
        bx = x0 + lam * (k + 0.5)
        by = ymid + side * amp * 0.45 * math.sin(math.pi / 2)
        sp = []
        for i in range(26):
            a = i / 25 * 2 * math.pi * 1.15
            r = amp * 0.8 * curl * (1 - i / 30)
            sp.append((bx + side * r * math.sin(a) * 0.9, by - side * (amp * 0.8 * curl - r * math.cos(a))))
        P.swell(sp, 2.5, 1, 0.5)
        ccy = by - side * amp * 0.8 * curl
        cc = P.clip(_pl(_ell(bx, ccy, amp * 0.7, amp * 0.7, n=16), True))
        half = P.clip(_pl([(bx - amp, ccy), (bx + amp, ccy + side * amp * 0.3), (bx + amp, ccy + side * amp), (bx - amp, ccy + side * amp)], True))
        P.hatch(half, (bx - amp, ccy - amp, bx + amp, ccy + amp), 35 * side, 1.5, clip2=cc)
        # acanthus leaf: lobes peeling off the stem and lying along the curl, with vein cuts
        for j, f in ((0, 1.0), (1, 0.75), (2, 0.5)):
            lx0 = bx - side * lam * (0.18 + 0.1 * j)
            P.swell([(lx0, by), (lx0 - side * amp * 0.2, by + side * amp * (0.45 + 0.1 * j)),
                     (lx0 - side * amp * (0.6 + 0.2 * j), by + side * amp * 0.25 * f)], 1.5 + 0.5 * (j == 0), 1, 0.25)
            P.line([(lx0 - side * 1, by + side * 1.5), (lx0 - side * amp * (0.3 + 0.1 * j), by + side * amp * 0.35)], 0.5)


def _tendril(P, x, y, d, size):
    """Terminal tendril: a fine spiral where the frieze breaks off into the paper."""
    sp = []
    for i in range(28):
        a = i / 27 * 2.6 * math.pi
        r = size * (1 - i / 31)
        sp.append((x + d * (size * 1.2 + r * math.sin(a) - size * 1.2 * i / 27), y - size + r * math.cos(a)))
    P.swell(sp, 1.5, 1, 0.25)
    P.swell([(x + d * size * 0.8, y + size * 0.25), (x + d * size * 2.2, y + size * 0.6),
             (x + d * size * 3.4, y + size * 0.1)], 1, 0.5, 0.25)


# --------------------------------------------------------------------------------- layouts

def _frieze(P):
    w, h, rng = P.w, P.h, P.rng
    cy = h * 0.55
    s = (h - 8) / 104.0
    margin = 6 + h * 0.35
    # the scroll is the spine; instruments ride on it
    _scroll(P, margin, w - margin, cy + h * 0.18, h * 0.22, rng)
    _tendril(P, margin, cy + h * 0.18, -1, h * 0.14)
    _tendril(P, w - margin, cy + h * 0.18, 1, h * 0.14)
    P.layer()
    base = h - 4
    kx = w * 0.20
    P2 = s * 0.95
    _drum_kit(P, kx, base, P2)
    _sax(P, w * 0.395, base - 2, s * 0.92)
    kw = max(4.0, round(w * 0.2 / 15 * 2) / 2)
    _keys(P, w * 0.47, base - h * 0.42, kw, h * 0.34, 15)
    _bass(P, w * 0.82, base, s * 0.98)
    # musical sparkle: a pair of beamed notes floating above the keys
    nx, ny = w * 0.47 + kw * 7.5, base - h * 0.62
    for d in (0, 1):
        P.fills.append(_pl(_ell(nx + d * 9, ny + d * 2, 2.2, 1.6, n=10, rot=-0.4), True))
        P.line([(nx + d * 9 + 2, ny + d * 2), (nx + d * 9 + 2, ny - 12 + d * 2)], 1)
    P.swell([(nx + 2, ny - 12), (nx + 6.5, ny - 11), (nx + 11, ny - 10)], 2, 2, 2)


def _scene(P):
    w, h, rng = P.w, P.h, P.rng
    cx = w / 2
    gap = (cx, h * 0.5, w * 0.5, h * 0.52)      # the vignette edge
    yf = h * 0.56                               # back of the stage floor
    yfront = h * 0.86                           # stage lip
    s = min(h / 380.0, w / 600.0) * 1.9
    # back wall: horizontal cuts, open in the cone of lamplight
    lx, ly = w * 0.47, h * 0.2
    cone = _pl([(lx - 10 * s, ly), (lx - w * 0.3, yfront), (lx + w * 0.3, yfront), (lx + 10 * s, ly)], True)
    wall = _pl([(0, 0), (w, 0), (w, yf), (0, yf)], True) + cone
    cw = P.clip(wall, True)
    P.hatch(cw, (0, 0, w, yf), 0, 2.5, gap=gap)
    darkwall = P.clip(_pl([(0, 0), (w, 0), (w, h * 0.12), (0, h * 0.12)], True) + cone, True)
    P.hatch(darkwall, (0, 0, w, h * 0.12), 60, 3, gap=gap)
    # curtains: gathered vertical folds, crowded lines read as the shadowed troughs
    for side in (-1, 1):
        x_in = cx + side * w * 0.3
        x_out = cx + side * w * 0.47
        i = 0
        x = x_in
        while (x - x_out) * side < 0:
            sway = 2.2 * math.sin(i * 0.9)
            top = h * 0.06 + abs(x - cx) * 0.02 + rng.uniform(0, 3)
            bot = yf + h * 0.05 - (abs(x - x_in) * 0.15)
            pts = [(x + sway * (j / 6) ** 2 + side * (j / 6) * 3, top + (bot - top) * j / 6) for j in range(7)]
            if i % 4 == 0:
                P.swell(pts[::2], 1.5, 0.5, 0.5)
            else:
                P.line(pts, 1 if math.sin(i * 0.9) < -0.3 else 0.5)
            x += side * (2 + 2.5 * (1 + math.sin(i * 0.9)) / 2)
            i += 1
        # tie-back swag
        P.swell([(x_in, h * 0.32), (x_in + side * w * 0.07, h * 0.36), (x_out, h * 0.34)], 2.5, 1, 1)
    # valance swags across the top
    for k in range(5):
        x0 = w * 0.18 + k * w * 0.128
        for j in range(2):
            P.swell([(x0, h * 0.04 + j * 2.5), (x0 + w * 0.064, h * 0.1 + j * 3), (x0 + w * 0.128, h * 0.04 + j * 2.5)],
                    1.5 - 0.5 * (j == 1), 0.5, 0.5)
    # the lamp
    P.line([(lx, 0), (lx, ly - 13 * s)], 1)
    _cylinder(P, lx, ly - 13 * s, 7 * s, 2 * s, 4 * s, lugs=0)
    shade = [(lx - 7 * s, ly - 9 * s), (lx - 20 * s, ly), (lx + 20 * s, ly), (lx + 7 * s, ly - 9 * s)]
    P.swell(shade[:2], 1.5, 1, 1)
    P.swell(shade[2:], 2, 1, 1)
    P.swell(_ell(lx, ly, 20 * s, 3.5 * s, 0, math.pi), 1.5, 1, 1)
    sc = P.clip(_pl(shade, True))
    for k in range(-8, 9):
        f = k / 8.0
        P.line([(lx + 7 * s * f, ly - 9 * s), (lx + 20 * s * f, ly + 3.5 * s * math.sqrt(1 - f * f))],
               1 if f > 0.2 else 0.5)
    P.hatch(sc, (lx, ly - 10 * s, lx + 21 * s, ly + 4 * s), 20, 2)
    # rays of lamplight: very fine broken hairlines
    for k in range(-3, 4):
        a = k * 0.12
        r0, r1 = 14 * s, (yf - ly) * (0.55 + rng.uniform(0, 0.3))
        P.line([(lx + math.sin(a) * r0, ly + 5 * s), (lx + math.sin(a) * r1 * 1.4, ly + r1)], 0.5)
    # stage floor: boards converging on the lamp's vanishing point
    P.swell([(w * 0.08, yf), (cx, yf), (w * 0.92, yf)], 1.5, 0.5, 0.5)
    fl = P.clip(_pl([(0, yf), (w, yf), (w, yfront), (0, yfront)], True))
    vx, vy = lx, yf - h * 0.6
    for k in range(-18, 19):
        x_end = cx + k * w * 0.045
        P.line([(vx + (x_end - vx) * (yf - vy) / (yfront - vy), yf), (x_end, yfront)], 0.5)
    lit = P.clip(_pl([(0, yf), (w, yf), (w, yfront), (0, yfront)], True) +
                 _pl(_ell(lx, (yf + yfront) / 2 - 4, w * 0.27, (yfront - yf) * 0.42), True), True)
    P.hatch(lit, (0, yf, w, yfront), -12, 2.5, gap=gap)
    # stage lip: a moulding with cross-hatched shadow beneath, breaking off at the vignette
    P.swell([(w * 0.06, yfront), (cx, yfront), (w * 0.94, yfront)], 2, 1, 0.5)
    P.line([(w * 0.08, yfront + 3), (w * 0.92, yfront + 3)], 0.5)
    apron = P.clip(_pl([(0, yfront + 4), (w, yfront + 4), (w, h), (0, h)], True))
    P.hatch(apron, (0, yfront + 4, w, yfront + 12), 0, 1.5, gap=(cx, yfront, w * 0.44, h * 0.12))
    # acanthus scroll beneath the stage, ending in tendrils that dissolve into the paper
    amp = min((h - yfront - 6) / 2.3, 24)
    sy = yfront + 4 + amp * 1.15
    _scroll(P, w * 0.16, w * 0.84, sy, amp, rng)
    _tendril(P, w * 0.16, sy, -1, amp * 0.5)
    _tendril(P, w * 0.84, sy, 1, amp * 0.5)
    # rug at the front of the stage
    rx, ry = w * 0.2, (yfront - yf) * 0.2
    rcx, rcy = w * 0.31, yfront - ry - 4
    P.layer()
    P.mask(_ell(rcx, rcy, rx + 1, ry + 1, n=24))
    rc = P.clip(_pl(_ell(rcx, rcy, rx - 5, ry - 2.5, n=24), True))
    P.hatch(rc, (rcx - rx, rcy - ry, rcx + rx, rcy + ry), 45, 2.5)
    P.hatch(P.clip(_pl(_ell(rcx, rcy, rx - 5, ry - 2.5, n=24), True) + _pl(_ell(rcx - rx * 0.15, rcy - ry * 0.25, rx * 0.9, ry * 0.85, n=24), True), True),
            (rcx - rx, rcy - ry, rcx + rx, rcy + ry), -45, 2.5)
    P.swell(_ell(rcx, rcy, rx, ry), 1.5, 1, 1)
    P.arc(0.5, rcx, rcy, rx - 4, ry - 2)
    for k in range(36):
        a = 2 * math.pi * k / 36
        P.line([(rcx + (rx - 1) * math.cos(a), rcy + (ry - 0.5) * math.sin(a)),
                (rcx + (rx - 3.5) * math.cos(a), rcy + (ry - 1.5) * math.sin(a))], 0.5)
    for d in (-1, 1):
        for k in range(6):
            x = rcx + d * (rx + 1)
            P.line([(x, rcy - 4 + k * 1.5), (x + d * 4, rcy - 4 + k * 1.5)], 0.5)
    # the players' instruments, back to front
    P.layer()
    _bass(P, w * 0.8, yf + (yfront - yf) * 0.45, s * 1.3, lean=-0.24)
    P.layer()
    _drum_kit(P, w * 0.56, yf + (yfront - yf) * 0.6, s * 0.95)
    P.layer()
    _dog(P, rcx + rx * 0.05, rcy + ry * 0.4, s * 1.25, rng)


def plate(width=528, height=300, seed=0):
    P = _Plate(int(width), int(height), seed)
    if height < 170:
        _frieze(P)
    else:
        _scene(P)
    return P.svg()


def demo(path="/tmp/claude-0/shots/plates/jazz.html"):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = []
    for (w, h) in ((528, 90), (528, 200), (528, 380)):
        svg = plate(w, h, seed=h)
        rows.append('<div style="margin:10px 0"><div style="font:11px sans-serif">%dx%d - %d bytes</div>%s</div>'
                    % (w, h, len(svg), svg))
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>body{background:#fff;margin:12px;'
            'width:528px}</style></head><body>%s</body></html>' % "".join(rows))
    with open(path, "w") as f:
        f.write(html)
    return path


if __name__ == "__main__":
    print(demo())
    print(len(plate(528, 300, 1)))
