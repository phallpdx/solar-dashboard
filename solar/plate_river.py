"""Engraved plate: the Columbia River at night from Sauvie Island (Kindle Evening Edition).

    plate(width, height, seed, moon_phase=None) -> complete <svg> string

A banknote-style vignette in pure line: Mt Hood with contour-hatched rock and swelling-line
snowfields, Douglas firs on the near bank, a cargo ship with lit portholes, the moon at its
phase (0 new, 0.5 full, lit on the right while waxing) and its broken reflection, ruled water
that tightens toward the viewer, stars, and a heron in the shallows. There is no box: the line
work thins and breaks off into the paper at the sides and the top, and the water dissolves at
the bottom, so the plate sits in the page like a printed vignette.

Engraving rules for the Paperwhite at DPR 2: every stroke width and every pitch is a multiple of
0.5 CSS px (one device pixel); tone is built from line density, never from grey fills or solid
blacks (the only fills are paper-white masks and filled burin strokes a few px wide).
Recomposes for the aspect ratio from a 528x90 frieze to a 528x420 upright. Ids are "pr"+seed.
Standard library only.
"""
import math
import random


def _f(v):
    s = "%.1f" % v
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s == "-0" else s


def _fy(v):
    """A hairline's centre on the device grid (x.25 / x.75) so 0.5 px lands on one device pixel."""
    return ("%.2f" % v).rstrip("0").rstrip(".")


def _snap(v, step=0.5):
    return max(step, round(v / step) * step)


def _smooth(e0, e1, x):
    if e1 == e0:
        return 1.0
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class _Plate(object):
    def __init__(self, W, H, seed, phase):
        self.W, self.H, self.seed = float(W), float(H), seed
        self.rng = random.Random("pr:%s" % seed)
        self.phase = phase % 1.0
        self.out = []
        self.pid = "pr%s" % seed
        a = H / float(W)
        self.tall = min(1.0, max(0.0, (a - 0.17) / 0.6))       # 0 frieze .. 1 upright
        self.fx = min(70.0, 0.13 * W)                          # side fade
        self.ft = 0.10 * H + 8                                 # top fade
        self.fb = 0.10 * H + 6                                 # bottom fade (water dissolves)
        # horizon: a tall plate gives the sky more room
        self.hz = round(H * (0.56 + 0.10 * self.tall))
        self.sky = self.hz
        self.wat = H - self.hz

    # ---- the vignette: 1 in the body of the plate, 0 at the open paper edge
    def vig(self, x, y):
        v = _smooth(0, self.fx, x) * _smooth(0, self.fx, self.W - x)
        v *= _smooth(0, self.ft, y) * _smooth(0, self.fb, self.H - y)
        # soften the corners into an oval
        return v

    def keep(self, x, y, salt):
        """Open vignette edge: each cut ends at its own ragged point near the sides, and rows
        thin out toward the top and dissolve at the bottom, so the line work breaks off into
        the paper the way a banknote vignette does."""
        n1 = (math.sin(salt * 12.9898 + self.seed) * 43758.5453) % 1.0
        n2 = (math.sin(salt * 78.233 + self.seed) * 24634.6345) % 1.0
        n3 = (math.sin(salt * 37.719 + self.seed) * 13758.937) % 1.0
        vy = _smooth(0, self.ft, y) * _smooth(0, self.fb, self.H - y)
        if vy < 0.999 and vy < n3:
            return False
        sag = (1 - vy) * self.fx * 0.8
        if x < self.fx * (0.1 + 0.8 * n1) + sag:
            return False
        if x > self.W - self.fx * (0.1 + 0.8 * n2) - sag:
            return False
        return True

    def pl(self, pts):
        """Polyline as compact relative path data."""
        x0, y0 = pts[0]
        d = "M%s %sl" % (_f(x0), _f(y0))
        px, py = float(_f(x0)), float(_f(y0))
        parts = []
        for x, y in pts[1:]:
            dx, dy = float(_f(x - px)), float(_f(y - py))
            parts.append("%s %s" % (_f(dx), _f(dy)))
            px, py = px + dx, py + dy
        return d + " ".join(parts)

    # ---- output helpers
    def add(self, s):
        self.out.append(s)

    def stroke(self, d, w):
        if d:
            self.add('<path fill="none" stroke="#000" stroke-width="%s" d="%s"/>' % (_f(w) if w < 1 or w % 1 else int(w), d))

    def swell(self, pts, ws):
        """Filled burin stroke along pts with full widths ws."""
        n = len(pts)
        if n < 2:
            return ""
        L, R = [], []
        for i in range(n):
            x0, y0 = pts[max(0, i - 1)]
            x1, y1 = pts[min(n - 1, i + 1)]
            dx, dy = x1 - x0, y1 - y0
            l = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / l, dx / l
            w = ws[i] / 2.0
            L.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
            R.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
        ring = L + R[::-1]
        return "M" + " ".join("%s %s" % (_f(x), _f(y)) for x, y in ring) + "z"

    # ---- scene parts
    def moon_geom(self):
        sky = self.sky
        r = max(5.0, min(24.0, sky * (0.13 + 0.03 * self.tall)))
        mx = round(self.W * 0.27)
        my = round(self.ft * 0.6 + r + (sky - self.ft - 2 * r) * (0.18 + 0.12 * self.tall))
        my = max(my, self.H * 0.4 + r + 3)
        my = min(my, self.hz - r * 1.4 - 3)
        my = max(my, r + 3)
        self.mr, self.mx, self.my = r, mx, my
        k = math.cos(2 * math.pi * self.phase)
        self.mk = k
        self.illum = (1 - k) / 2.0

    def lit_span(self, y):
        dy = y - self.my
        r = self.mr
        if abs(dy) >= r:
            return None
        hw = math.sqrt(r * r - dy * dy)
        k = self.mk
        if self.phase <= 0.5:
            a, b = self.mx + k * hw, self.mx + hw
        else:
            a, b = self.mx - hw, self.mx - k * hw
        return (a, b) if b - a > 0.2 else None

    def mountain_geom(self):
        sky = self.sky
        mh = min(sky * (0.66 - 0.16 * self.tall), 0.15 * self.W)
        mh = max(mh, 18)
        self.mh = mh
        self.px = self.W * 0.64
        self.Ll = mh * 3.0
        self.Lr = mh * 3.3
        rng = random.Random("mt:%s" % self.seed)
        self.mph = [rng.uniform(0, 6.28) for _ in range(4)]

    def mtop(self, x):
        u = (x - self.px) / (self.Ll if x < self.px else self.Lr)
        au = abs(u)
        if au >= 1:
            return self.hz + 1
        s = 0.8 * (1 - au) ** 2.1 + 0.2 * (1 - au) ** 0.9
        # Illumination Rock shoulder on the left, Steel Cliff on the right
        if u < 0:
            s += 0.05 * math.exp(-((u + 0.3) / 0.08) ** 2)
        else:
            s += 0.035 * math.exp(-((u - 0.22) / 0.06) ** 2)
        p = self.mph
        s += 0.012 * math.sin(x * 0.23 + p[0]) + 0.008 * math.sin(x * 0.61 + p[1])
        s *= 1 - 0.02 * math.sin(x * 0.09 + p[2])
        return self.hz - self.mh * s * (1 - 0.02 * au)

    def shore_top(self, x):
        """The far (Washington) shore: a low band of firs along the horizon."""
        h = max(2.0, min(6.0, self.sky * 0.06))
        t = (x % 6.0) / 6.0
        spike = (1 - abs(t - 0.5) * 2) * h * (0.6 + 0.4 * math.sin(math.floor(x / 6.0) * 2.7 + self.seed))
        return self.hz - 1.5 - h * 0.45 - spike

    # ---- 1. sky ruling with stars, moon carved out
    def draw_sky(self):
        rng = self.rng
        W, hz = self.W, self.hz
        mx, my, r = self.mx, self.my, self.mr
        # stars
        n = int(W * self.sky / 1300.0 * (0.8 + 0.3 * self.tall))
        stars = []
        tries = 0
        while len(stars) < n and tries < n * 30:
            tries += 1
            x = rng.uniform(self.fx * 0.5, W - self.fx * 0.5)
            y = rng.uniform(self.ft * 0.4, hz - 6)
            if y > self.mtop(x) - 5 or math.hypot(x - mx, y - my) < r * 2.2 + 4:
                continue
            if x > self.tree_x0 - 4 and y > self.tree_top(x) - 4:
                continue
            if self.vig(x, y) < 0.35:
                continue
            if any(math.hypot(x - a, y - b) < 9 for a, b, _ in stars):
                continue
            stars.append((round(x * 2) / 2, round(y * 2) / 2, rng.random()))
        self.stars = stars
        d = {0.5: [], 1.0: []}
        y = 1.25
        salt = 0
        while y < hz - 1:
            t = y / float(hz)
            pitch = _snap(2.0 + 0.5 * self.tall + 1.5 * t)
            w = 0.5
            gaps = []
            if abs(y - my) < r + 3:
                hw = math.sqrt(max(0.0, (r + 3) ** 2 - (y - my) ** 2))
                gaps.append((mx - hw, mx + hw))
            for sx, sy, b in stars:
                g = 1.5 + 2.0 * b
                if abs(y - sy) < g:
                    hw = math.sqrt(g * g - (y - sy) ** 2) + 0.5
                    gaps.append((sx - hw, sx + hw))
            # stop at the mountain and the far shore (they are drawn over a white mask anyway)
            x = 0.0
            run = None
            salt += 1
            while x <= W:
                on = (not any(a <= x <= b for a, b in gaps)) and self.keep(x, y, salt)
                if on and run is None:
                    run = x
                elif not on and run is not None:
                    if x - run > 1:
                        d[w].append("M%s %sH%s" % (_f(run), _fy(y), _f(x)))
                    run = None
                x += 2.0
            if run is not None and W - run > 1:
                d[w].append("M%s %sH%s" % (_f(run), _fy(y), _f(W)))
            y += pitch
        for w, segs in d.items():
            self.stroke("".join(segs), w)
        # bright stars get four-point rays
        rays = []
        for sx, sy, b in stars:
            if b > 0.55:
                L = 1.5 + 2.5 * b
                rays.append("M%s %sh%s M%s %sv%s" % (_f(sx - L), _f(sy), _f(2 * L), _f(sx), _f(sy - L), _f(2 * L)))
            elif b > 0.3:
                rays.append("M%s %sh1" % (_f(sx - 0.5), _f(sy)))
        self.stroke("".join(rays), 0.5)

    # ---- 2. the moon: paper where lit, cross-hatched dark limb, a few maria
    def draw_moon(self):
        mx, my, r = self.mx, self.my, self.mr
        self.add('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#000" stroke-width="0.5"/>' % (_f(mx), _f(my), _f(r)))
        h, v, m = [], [], []
        maria = [(-0.25, -0.3, 0.3), (0.2, -0.15, 0.22), (0.05, 0.3, 0.25), (-0.35, 0.2, 0.18)]
        y = my - r + 1.5
        while y < my + r - 0.5:
            hw = math.sqrt(r * r - (y - my) ** 2) - 0.5
            span = self.lit_span(y)
            segs = [(mx - hw, mx + hw)]
            if span:
                a, b = span
                segs = [(mx - hw, a - 0.5), (b + 0.5, mx + hw)]
                # maria inside the lit part, as short hairline dashes
                for cx, cy, rr in maria:
                    cx, cy, rr = mx + cx * r, my + cy * r, rr * r
                    if abs(y - cy) < rr:
                        ww = math.sqrt(rr * rr - (y - cy) ** 2)
                        p0, p1 = max(a + 1, cx - ww), min(b - 1, cx + ww)
                        if p1 - p0 > 0.8:
                            m.append("M%s %sH%s" % (_f(p0), _f(y), _f(p1)))
            for p0, p1 in segs:
                if p1 - p0 > 0.5:
                    h.append("M%s %sH%s" % (_f(p0), _f(y), _f(p1)))
            y += 1.5
        # vertical second set over the dark part: cross-hatching, the deepest tone
        x = mx - r + 1
        while x < mx + r - 0.5:
            hh = math.sqrt(max(0.0, r * r - (x - mx) ** 2)) - 0.5
            yy = my - hh
            run = None
            while yy <= my + hh:
                sp = self.lit_span(yy)
                dark = not (sp and sp[0] - 0.5 <= x <= sp[1] + 0.5)
                if dark and run is None:
                    run = yy
                elif not dark and run is not None:
                    if yy - run > 0.8:
                        v.append("M%s %sV%s" % (_f(x), _f(run), _f(yy)))
                    run = None
                yy += 0.5
            if run is not None and my + hh - run > 0.8:
                v.append("M%s %sV%s" % (_f(x), _f(run), _f(my + hh)))
            x += 2.0
        self.stroke("".join(h) + "".join(v) + "".join(m), 0.5)

    # ---- 3. Mt Hood
    def draw_mountain(self):
        x0 = max(0.0, self.px - self.Ll)
        x1 = min(self.W, self.px + self.Lr)
        pts = []
        x = x0
        while x <= x1:
            pts.append((x, self.mtop(x)))
            x += 3.0
        pts.append((x1, self.mtop(x1)))
        mask = self.pl([(x0, self.hz)] + pts + [(x1, self.hz)]) + "z"
        self.add('<path fill="#fff" d="%s"/>' % mask)
        px, mh, hz = self.px, self.mh, self.hz
        # ridge line: swelling burin, heavy on the shadow (right) side, lifting to a hairline in the light
        ridge = [p for p in pts if self.vig(p[0], p[1]) > 0.3]
        ws = []
        for xx, yy in ridge:
            e = (hz - yy) / mh
            base = 1.0 if xx > px else 0.5
            ws.append(base * (0.6 + 0.8 * e) if e > 0.05 else 0.4)
        self.add('<path d="%s"/>' % self.swell(ridge, ws))

        def snowline(xx):
            u = (xx - px) / (self.Ll if xx < px else self.Lr)
            return hz - mh * (0.48 + 0.07 * math.sin(xx * 0.35 + self.seed) + 0.06 * math.sin(xx * 0.9)) + abs(u) * mh * 0.1

        # contour hatching: offset curves of the ridge, width by side and elevation
        cls = {0.5: [], 1.0: []}
        pitch = 2.5 if mh > 45 else (2.0 if mh > 25 else 1.5)
        k = 1
        salt = 100
        while True:
            off = k * pitch
            if off > mh:
                break
            runs = {}
            cur_w, cur = None, []
            x = x0
            while x <= x1 + 0.1:
                yy = self.mtop(x) + off
                w = None
                if yy < hz - 0.5 and self.keep(x, yy, salt + k):
                    e = (hz - yy) / mh
                    shadow = x > px + (hz - yy) * 0.05
                    snow = yy < snowline(x)
                    if snow:
                        # shadowed snow: broken hairlines; lit snow is paper
                        if shadow and (k % 2 == 0 or e < 0.75) and ((int(x / 7) + k) % 3 != 0):
                            w = 0.5
                    else:
                        w = 1.0 if shadow else 0.5
                        if not shadow and e > 0.3 and k % 2:
                            w = None   # lit rock just under the snow: open, sparkling
                if w != cur_w:
                    if cur_w is not None and len(cur) > 1:
                        runs.setdefault(cur_w, []).append(cur)
                    cur_w, cur = w, []
                if w is not None:
                    cur.append((x, yy))
                x += 5.0
            if cur_w is not None and len(cur) > 1:
                runs.setdefault(cur_w, []).append(cur)
            for w, rl in runs.items():
                for r in rl:
                    cls[w].append(self.pl(r))
            k += 1
        for w, segs in cls.items():
            self.stroke("".join(segs), w)
        # cross-hatching for the deepest shadow: lower right flank
        xh = []
        x = px + mh * 0.2
        while x < x1 - 2:
            yt = self.mtop(x)
            ya = max(yt + 2, snowline(x) + 1)
            if ya < hz - 1 and self.keep(x, ya, 7):
                L = (hz - 1 - ya)
                xh.append("M%s %sl%s %s" % (_f(x), _f(ya), _f(-L * 0.35), _f(L)))
            x += 2.5
        self.stroke("".join(xh), 0.5)
        # snowfields: gullies as swelling fall-lines radiating from the summit
        rng = random.Random("sn:%s" % self.seed)
        g = []
        ng = int(9 + mh / 6)
        for i in range(ng):
            t = (i + 0.5) / ng
            xs = px + (t - 0.5) * 2 * (self.Ll * 0.42 if t < 0.5 else self.Lr * 0.42)
            ys = self.mtop(xs) + 1.0
            ln = (snowline(xs) - ys) * rng.uniform(0.6, 1.25)
            if ln < 3:
                continue
            ang = (xs - px) / mh * 0.35
            seg = []
            for j in range(7):
                s = j / 6.0
                seg.append((xs + math.sin(ang) * ln * s + 0.8 * math.sin(s * 5 + i), ys + ln * s))
            wmax = 1.5 if xs > px else 1.0
            ws = [wmax * math.sin(math.pi * (0.1 + 0.85 * j / 6.0)) for j in range(7)]
            if self.vig(xs, ys) > 0.4:
                g.append(self.swell(seg, ws))
        self.add('<path d="%s"/>' % "".join(g))

    # ---- 4. far shore treeline
    def draw_far_shore(self):
        W, hz = self.W, self.hz
        pts = []
        x = 0.0
        while x <= W:
            pts.append((x, self.shore_top(x)))
            x += 2.0
        self.add('<path fill="#fff" d="%sz"/>' % self.pl([(0, hz + 0.5)] + pts + [(W, hz + 0.5)]))
        d = []
        for xx, yy in pts:
            if self.keep(xx, hz - 2, 300) and xx < self.tree_x0 + 4:
                d.append("M%s %sv%s" % (_f(xx), _f(hz), _f(yy - hz)))
        self.stroke("".join(d), 0.5)
        self.stroke("M%s %sH%s" % (_f(self.fx * 0.4), _f(hz), _f(W - self.fx * 0.2)), 0.5)

    # ---- 5. water
    def draw_water(self):
        rng = random.Random("wa:%s" % self.seed)
        W, hz, H = self.W, self.hz, self.H
        mx, r = self.mx, self.mr
        ill = self.illum
        s = self.ship
        d = {0.5: [], 1.0: []}
        y = hz + 1.75
        li = 0
        while y < H - 0.5:
            t = (y - hz) / max(1.0, self.wat)
            pitch = _snap(3.0 - (1.5 - 0.5 * self.tall) * t)
            li += 1
            # moon glade: broken lozenges of paper under the moon
            rw = (r * 0.45 + (y - hz) * 0.12) * (0.3 + 0.7 * ill) if ill > 0.03 else 0
            sx0, sx1 = s["x0"], s["x1"]
            in_ship_refl = s["yw"] <= y < s["yw"] + s["hh"] * 2.2
            x = 0.0
            segs = []
            while x < W:
                L = rng.uniform(25, 110)
                g = rng.uniform(1.0, 3.5) if t > 0.15 else rng.uniform(2, 6)
                segs.append((x, min(W, x + L)))
                x += L + g
            out = []
            for a, b in segs:
                # carve the glade
                if rw > 0 and b > mx - rw and a < mx + rw:
                    pos = mx - rw
                    if a < pos:
                        out.append((a, pos))
                    xx = pos
                    while xx < mx + rw:
                        c = abs(xx - mx) / rw
                        gap = rng.uniform(3, 9) * (1.3 - c)
                        dash = rng.uniform(1, 3) * (0.4 + c)
                        xx += max(1.0, gap)
                        e = min(xx + dash, mx + rw)
                        if e - xx > 0.6:
                            out.append((xx, e))
                        xx = e
                    if b > mx + rw:
                        out.append((mx + rw, b))
                else:
                    out.append((a, b))
            for a, b in out:
                # thin the cut into the paper at the edges
                cut = []
                xx = a
                run = None
                while xx <= b:
                    on = self.keep(xx, y, 500 + li)
                    if in_ship_refl and sx0 + 2 < xx < sx1 - 2:
                        # lit porthole streaks in the ship's dark reflection
                        if any(abs(xx - p) < 0.8 for p in s["ports"]) and (li % 3):
                            on = False
                    if on and run is None:
                        run = xx
                    elif not on and run is not None:
                        cut.append((run, xx))
                        run = None
                    xx += 1.0 if in_ship_refl else 2.0
                if run is not None:
                    cut.append((run, b))
                for p, q in cut:
                    if q - p < 0.6:
                        continue
                    w = 0.5
                    if in_ship_refl and sx0 < p < sx1:
                        w = 1.0
                    if y < hz + 4 and li <= 2:
                        w = 1.0
                    d[w].append("M%s %sH%s" % (_f(p), _fy(y + (0.25 if w == 1.0 else 0)), _f(q)))
            y += pitch
        for w, segs in d.items():
            self.stroke("".join(segs), w)

    # ---- 6. the cargo ship
    def ship_geom(self):
        sl = min(0.24 * self.W, max(60.0, self.wat * 2.0 + self.sky * 0.6))
        hh = max(3.5, sl * 0.075)
        x0 = round(max(self.W * 0.44 - sl * 0.5, self.mx + self.mr + 12))
        yw = round(self.hz + max(4.0, self.wat * 0.22))
        x1 = x0 + sl
        nports = int(sl * 0.55 / 4)
        ports = [x0 + sl * 0.18 + i * 4.0 for i in range(nports)]
        self.ship = dict(x0=x0, x1=x1, yw=yw, hh=hh, sl=sl, ports=ports)

    def draw_ship(self):
        s = self.ship
        x0, x1, yw, hh, sl = s["x0"], s["x1"], s["yw"], s["hh"], s["sl"]
        bow_top = yw - hh * 1.35
        deck = yw - hh
        hull = "M%s %sL%s %sL%s %sL%s %sL%s %sz" % (_f(x0), _f(bow_top), _f(x1), _f(deck), _f(x1 - 1.5), _f(yw), _f(x0 + hh * 1.1), _f(yw), _f(x0), _f(bow_top))
        cid = self.pid + "h"
        # superstructure (stern), funnel, container stacks
        bx0, bx1 = x0 + sl * 0.80, x0 + sl * 0.93
        btop = deck - hh * 2.6
        rng = random.Random("sh:%s" % self.seed)
        stacks = []
        cx = x0 + sl * 0.12
        ch = max(1.5, _snap(hh * 0.5))
        while cx + sl * 0.08 < x0 + sl * 0.77:
            cw = sl * 0.075
            tiers = rng.choice([1, 2, 2, 3, 3])
            stacks.append((cx, cx + cw, tiers))
            cx += cw + 0.5
        # paper masks
        mask = hull + "M%s %sH%sV%sH%sz" % (_f(bx0), _f(deck), _f(bx1), _f(btop), _f(bx0))
        for a, b, t in stacks:
            mask += "M%s %sH%sV%sH%sz" % (_f(a), _f(deck), _f(b), _f(deck - t * ch), _f(a))
        self.add('<path fill="#fff" d="%s"/>' % mask)
        self.add('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, hull))
        # hull: horizontal ruling + diagonal cross-hatch (deepest shadow), lit portholes left white
        h = []
        y = deck + 0.75
        py = yw - hh * 0.55
        while y < yw:
            gaps = [(p - 0.9, p + 0.9) for p in s["ports"]] if abs(y - py) < 1.0 else []
            a = x0 - 1
            for g0, g1 in gaps:
                h.append("M%s %sH%s" % (_f(a), _f(y), _f(g0)))
                a = g1
            h.append("M%s %sH%s" % (_f(a), _f(y), _f(x1 + 1)))
            y += 1.5
        dg = []
        x = x0 - hh
        while x < x1 + 2:
            dg.append("M%s %sl%s %s" % (_f(x), _f(bow_top - 1), _f(hh * 1.6), _f(hh * 1.6)))
            x += 2.0
        self.add('<g clip-path="url(#%s)">' % cid)
        self.stroke("".join(h), 0.5)
        self.stroke("".join(dg), 0.5)
        self.add('</g>')
        self.stroke(hull, 1.0)
        # containers: outlines and corrugations
        c = []
        for a, b, t in stacks:
            for i in range(t):
                yb = deck - i * ch
                c.append("M%s %sH%sV%sH%sz" % (_f(a), _f(yb), _f(b), _f(yb - ch), _f(a)))
            x = a + 1.5
            while x < b - 0.5:
                c.append("M%s %sV%s" % (_f(x), _f(deck), _f(deck - t * ch)))
                x += 1.5
        self.stroke("".join(c), 0.5)
        # bridge: ruled, a row of lit windows, funnel, mast and lights
        b = []
        y = btop + 1.5
        wy = btop + hh * 0.6
        while y < deck:
            if abs(y - wy) < 0.8:
                xx = bx0
                while xx < bx1:
                    b.append("M%s %sH%s" % (_f(xx), _f(y), _f(min(bx1, xx + 0.5))))
                    xx += 2.5
            else:
                b.append("M%s %sH%s" % (_f(bx0), _f(y), _f(bx1)))
            y += 1.5
        b.append("M%s %sH%sV%sH%sz" % (_f(bx0), _f(deck), _f(bx1), _f(btop), _f(bx0)))
        fx = bx0 + (bx1 - bx0) * 0.55
        b.append("M%s %sV%sH%sV%s" % (_f(fx), _f(btop), _f(btop - hh), _f(fx + hh * 0.8), _f(btop)))
        b.append("M%s %sV%s" % (_f(x0 + sl * 0.06), _f(bow_top), _f(bow_top - hh * 2.2)))
        b.append("M%s %sV%s" % (_f(bx0 + 1.5), _f(btop), _f(btop - hh * 1.8)))
        self.stroke("".join(b), 0.5)
        lt = []
        for lx, ly in ((x0 + sl * 0.06, bow_top - hh * 2.2), (bx0 + 1.5, btop - hh * 1.8)):
            lt.append("M%s %sh3M%s %sv3" % (_f(lx - 1.5), _f(ly - 1.5), _f(lx), _f(ly - 3)))
        self.stroke("".join(lt), 0.5)

    # ---- 7. near bank and Douglas firs (right)
    def trees_geom(self):
        W = self.W
        self.tree_x0 = W - self.fx * 0.5 - max(46.0, W * 0.15)
        bank_y = self.hz + self.wat * 0.35
        tops = self.hz - min(self.sky * 0.82, self.mh * 1.9 + 20)
        self.trees = []
        spec = [(0.30, 1.0), (0.66, 0.74), (0.06, 0.58)]
        span = W - self.fx * 0.35 - self.tree_x0
        for fx_, hf in spec:
            tx = self.tree_x0 + span * fx_
            base = bank_y + (tx - self.tree_x0) / span * self.wat * 0.08
            th = (base - tops) * hf
            self.trees.append((tx, base, th, th * 0.17))
        self.bank_y = bank_y

    def tree_top(self, x):
        best = self.hz
        for tx, base, th, bw in self.trees:
            hw = bw * 1.15
            if abs(x - tx) < hw:
                best = min(best, base - th + (abs(x - tx) / hw) * th * 0.9)
        return best

    def draw_trees(self):
        W, H = self.W, self.H
        rng = random.Random("fr:%s" % self.seed)
        x0 = self.tree_x0 - 10
        # bank silhouette
        by = self.bank_y
        bank = []
        x = x0
        while x <= W:
            t = (x - x0) / (W - x0)
            bank.append((x, by + 3 - 6 * t ** 0.6 + 0.8 * math.sin(x * 0.7)))
            x += 3
        bot = min(H, by + self.wat * 0.25)
        self.add('<path fill="#fff" d="M%s %s%sL%s %sz"/>' % (_f(x0), _f(bot), "".join("L%s %s" % (_f(a), _f(b)) for a, b in bank), _f(W), _f(bot)))
        bd = []
        k = 0
        y = min(b for a, b in bank)
        while y < bot:
            xs = [a for a, b in bank if b <= y and (a - x0) > (y - by) * 0.8]
            if xs:
                a = xs[0]
                e = W
                while e > a and not self.keep(e, y, 900 + k):
                    e -= 2.0
                if e - a > 1:
                    bd.append("M%s %sH%s" % (_f(a), _f(y), _f(e)))
            y += 1.5
            k += 1
        self.stroke("".join(bd), 0.5)
        lit, shade, needles = [], [], []
        masks = []
        for tx, base, th, bw in sorted(self.trees, key=lambda t: t[2]):
            top = base - th
            # paper mask: the fir silhouette
            sil = []
            n = 16
            for i in range(n + 1):
                yy = top + th * i / n
                w = bw * (i / float(n)) ** 0.85 * (1.0 if i % 2 else 0.75)
                sil.append((tx - w, yy))
            sil_r = [(2 * tx - a, b + 1) for a, b in sil[::-1]]
            masks.append(self.pl([(tx, top)] + sil + sil_r) + "z")
            self.add('<path fill="#fff" d="%s"/>' % masks[-1])
            p = []
            # trunk
            self.add('<path d="%s"/>' % self.swell([(tx, top), (tx, top + th * 0.5), (tx, base + 1)], [0.3, 1.0, 1.5]))
            # drooping branch tiers, heavier on the shadow side
            y = top + 1.5
            sp = max(2.0, _snap(th / 24.0))
            while y < base - 1:
                f = (y - top) / th
                w = bw * f ** 0.85 * rng.uniform(0.65, 1.05)
                if w > 1.0:
                    dr = w * 0.38
                    for side in (-1, 1):
                        ww = w * rng.uniform(0.8, 1.05)
                        seg = "M%s %sq%s %s %s %s" % (_f(tx), _f(y), _f(side * ww * 0.5), _f(dr * 0.9), _f(side * ww), _f(dr * 0.7))
                        if side > 0 or f > 0.75:
                            shade.append(seg)
                        else:
                            lit.append(seg)
                        # hanging needle tufts on the shadow side
                        if False:
                            xx = tx + 1.5
                            while xx < tx + ww - 1:
                                q = (xx - tx) / ww
                                yb = y + dr * 0.9 * q * (2 - q) * 0.9
                                needles.append("M%s %sv%s" % (_f(xx), _f(yb), _f(min(2.5, sp + 0.5))))
                                xx += 2.0
                y += sp
            # shadow half: vertical hairlines, then a diagonal second set low down (deepest shade)
            x = tx + 1.0
            while x < tx + bw:
                q = (x - tx) / bw
                y0 = top + th * (q ** (1 / 0.85))
                needles.append("M%s %sV%s" % (_f(x), _f(max(y0 + 2, top + th * 0.3)), _f(base)))
                if q < 0.7:
                    yc = top + th * 0.55
                    if yc > y0:
                        needles.append("M%s %sl%s %s" % (_f(x), _f(yc), _f(bw * 0.25), _f(base - yc)))
                x += 2.5
        self.stroke("".join(lit), 0.5)
        self.stroke("".join(shade), 1.0)
        self.stroke("".join(needles), 0.5)

    # ---- 8. heron in the shallows (left foreground)
    def draw_heron(self):
        hs = max(16.0, min(self.wat * 0.95, self.H * 0.42, 100.0))
        fx = self.W * 0.135 + self.fx * 0.2
        fy = self.H - self.fb * 0.9 - 2
        fy = min(fy, self.H - 6)

        def P(x, y):
            return (fx + x * hs, fy + y * hs)

        body = [P(0.30, -0.47), P(0.18, -0.58), P(0.0, -0.64), P(-0.12, -0.62), P(-0.15, -0.55),
                P(-0.06, -0.47), P(0.08, -0.43), P(0.22, -0.43)]
        bd = "M" + " ".join("%s %s" % (_f(a), _f(b)) for a, b in body) + "z"
        neck = [P(-0.12, -0.60), P(-0.18, -0.68), P(-0.13, -0.77), P(-0.05, -0.84), P(-0.08, -0.92), P(-0.13, -0.96)]
        head = [P(-0.10, -0.99), P(-0.16, -0.995), P(-0.20, -0.97), P(-0.13, -0.95)]
        hd = "M" + " ".join("%s %s" % (_f(a), _f(b)) for a, b in head) + "z"
        # paper mask so the water and sky lines stop at the bird
        self.add('<path fill="#fff" d="%s%s%s"/>' % (bd, self.swell(neck, [3.5, 3.5, 3.0, 2.5, 2.5, 2]), hd))
        # wing: curved contour hatch, darker toward the back
        wing = []
        for i in range(int(hs / 6) + 3):
            t = i / float(int(hs / 6) + 2)
            a = P(-0.05 + 0.32 * t, -0.60 + 0.12 * t)
            b = P(0.06 + 0.24 * t, -0.48 + 0.02 * t)
            wing.append("M%s %sQ%s %s %s %s" % (_f(a[0]), _f(a[1]), _f((a[0] + b[0]) / 2 + 1.5), _f((a[1] + b[1]) / 2 - 1), _f(b[0]), _f(b[1])))
        self.stroke("".join(wing), 0.5)
        self.stroke(bd, 0.5)
        # back: one swelling stroke for the folded wing edge; the neck as a swelling S
        back = [P(-0.08, -0.62), P(0.05, -0.645), P(0.18, -0.60), P(0.30, -0.49), P(0.36, -0.42)]
        ws = [0.5, 1.5, 2.0, 1.5, 0.5]
        nk = [(x + 0.8, y) for x, y in neck]
        self.add('<path d="%s%s"/>' % (self.swell(back, ws), self.swell(nk, [0.5, 1.5, 1.5, 1.0, 1.0, 0.5])))
        self.stroke("M" + " ".join("%s %s" % (_f(a), _f(b)) for a, b in neck), 0.5)
        self.stroke(hd, 0.5)
        # beak, plume, eye
        b0, b1, b2 = P(-0.19, -0.975), P(-0.40, -0.955), P(-0.19, -0.958)
        self.add('<path d="M%s %sL%s %sL%s %sz"/>' % (_f(b0[0]), _f(b0[1]), _f(b1[0]), _f(b1[1]), _f(b2[0]), _f(b2[1])))
        pl = [P(-0.11, -0.99), P(-0.0, -0.985), P(0.10, -0.965)]
        self.add('<path d="%s"/>' % self.swell(pl, [0.6, 1.0, 0.3]))
        e = P(-0.15, -0.98)
        self.stroke("M%s %sh0.5" % (_f(e[0]), _f(e[1])), 1.0)
        # legs, knees and their broken reflection
        legs = []
        for dx in (0.02, 0.10):
            k = P(dx + 0.03, -0.25)
            top = P(dx + 0.02, -0.45)
            ft = P(dx, 0)
            legs.append("M%s %sL%s %sL%s %s" % (_f(top[0]), _f(top[1]), _f(k[0]), _f(k[1]), _f(ft[0]), _f(ft[1])))
            legs.append("M%s %sh%s" % (_f(ft[0] - 1.5), _f(ft[1]), _f(3.5)))
        self.stroke("".join(legs), 1.0 if hs > 40 else 0.5)
        # ripple rings and reflection under the feet, on paper
        rr = []
        for i in range(3):
            w = hs * (0.15 + 0.13 * i)
            y = fy + 1.5 + i * 1.5
            if y < self.H - 1:
                rr.append("M%s %sh%s" % (_f(fx - w * 0.5 + 0.06 * hs), _f(y), _f(w)))
        self.add('<path fill="#fff" d="M%s %sh%sv%sh%sz"/>' % (_f(fx - hs * 0.25), _f(fy + 0.5), _f(hs * 0.6), _f(min(hs * 0.35, self.H - fy - 1)), _f(-hs * 0.6)))
        refl = []
        for dx in (0.02, 0.10):
            x = fx + dx * hs
            y = fy + 1.0
            while y < min(self.H - 1, fy + hs * 0.33):
                refl.append("M%s %sv1" % (_f(x + (y % 3 - 1) * 0.5), _f(y)))
                y += 2.0
        self.stroke("".join(rr), 0.5)
        self.stroke("".join(refl), 0.5)


    # ---- 9. acanthus scrolls at the lower corners, dissolving into the paper
    def draw_scrolls(self):
        sz = max(10.0, min(30.0, self.H * 0.16))
        g = []
        for side in (-1, 1):
            cx = self.fx * 0.55 if side < 0 else self.W - self.fx * 0.55
            cy = self.H - sz * 0.75
            # volute: a spiral that swells and lifts out
            pts, ws = [], []
            n = 26
            for i in range(n):
                t = i / (n - 1.0)
                a = -side * (0.3 + 4.2 * t) * math.pi / 2 - math.pi / 2
                rr = sz * 0.5 * (1 - 0.78 * t)
                pts.append((cx + side * 0.0 + math.cos(a) * rr * -side, cy + math.sin(a) * rr))
                ws.append(1.5 * math.sin(math.pi * (0.08 + 0.9 * t)) + 0.2)
            g.append(self.swell(pts, ws))
            # acanthus leaf lobes curling off the volute toward the centre of the plate
            for j in range(3):
                bx, by = pts[3 + j * 3]
                lp, lw = [], []
                L = sz * (0.9 - 0.2 * j)
                for i in range(9):
                    t = i / 8.0
                    lp.append((bx - side * L * t, by - L * 0.35 * math.sin(math.pi * t) + j * 1.5 * t))
                    lw.append(1.5 * math.sin(math.pi * t) * (1 - 0.6 * t) + 0.1)
                g.append(self.swell(lp, lw))
                # hairline veins that fade out
                for v in range(2):
                    q = lp[3 + v * 2]
                    g2 = [(q[0], q[1] + 1), (q[0] - side * 2.5, q[1] - 1.5)]
                    g.append(self.swell(g2, [0.5, 0.1]))
        self.add('<path d="%s"/>' % "".join(g))

    def build(self):
        self.moon_geom()
        self.mountain_geom()
        self.ship_geom()
        self.trees_geom()
        self.draw_sky()
        self.draw_moon()
        self.draw_mountain()
        self.draw_far_shore()
        self.draw_water()
        self.draw_ship()
        self.draw_trees()
        self.draw_heron()
        self.draw_scrolls()
        W, H = int(self.W), int(self.H)
        return ('<svg xmlns="http://www.w3.org/2000/svg" id="%s" width="%d" height="%d" viewBox="0 0 %d %d" '
                'role="img" aria-label="Engraving: the Columbia River at night from Sauvie Island, Mt Hood, '
                'a cargo ship, the moon and a heron">%s</svg>' % (self.pid, W, H, W, H, "".join(self.out)))


def plate(width, height, seed, moon_phase=None):
    """Complete <svg> for the river plate. moon_phase in [0, 1): 0 new, 0.5 full, waxing lit right.
    None picks a seeded phase."""
    if moon_phase is None:
        moon_phase = random.Random("ph:%s" % seed).uniform(0.15, 0.85)
    return _Plate(width, height, seed, moon_phase).build()


def demo(path="/tmp/claude-0/shots/plates/river.html"):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = []
    for sd, (w, h), ph in ((7, (528, 90), 0.62), (8, (528, 200), 0.32), (9, (528, 380), 0.5)):
        svg = plate(w, h, sd, ph)
        rows.append('<div class="c"><p>%dx%d &middot; phase %.2f &middot; %d bytes</p>%s</div>' % (w, h, ph, len(svg), svg))
    html = ('<!doctype html><meta charset="utf-8"><title>River plate</title><style>body{margin:0;background:#fff;'
            'font:12px Georgia,serif;color:#000;width:560px}.c{padding:8px 16px 18px}p{margin:0 0 6px}'
            'svg{display:block}</style>' + "".join(rows))
    with open(path, "w") as f:
        f.write(html)
    return path


if __name__ == "__main__":
    print(demo())
