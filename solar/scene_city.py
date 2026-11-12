"""Engraved city vignettes for the Kindle "Evening Edition": St Johns Bridge and a Sauvie Island night sky.

    scene(w, h, seed=0, variant="bridge", moon_phase=0.5, planet=None) -> SVG child markup

The markup fills a w x h box edge to edge (the caller clips it into an oval or rectangular
cartouche). Tone comes only from line: ruled lines whose weight is 0.5 / 1 / 1.5 px, crossed rulings
in shadow, stipple for soft tone. White shapes are only knock-outs that are then ruled over.
No transforms, filters, masks, gradients or text. Self-contained (imports nothing from the repo).
"""

import math
import random

__all__ = ['scene']

_ECO = [0]      # economy level, raised by scene() until the plate fits its byte budget


# ------------------------------------------------------------------ numbers and paths

def _f(v):
    s = '%.1f' % v
    if s.endswith('.0'):
        s = s[:-2]
    if s in ('-0', ''):
        return '0'
    if s.startswith('0.'):
        s = s[1:]
    elif s.startswith('-0.'):
        s = '-' + s[2:]
    return s


def _r(v):
    return round(v * 10) / 10.0


def _j(a, b):
    sb = _f(b)
    return _f(a) + ('' if sb[0] == '-' else ' ') + sb


def _cl(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


class _P(object):
    """Path data accumulator: runs in relative steps, rounded cumulatively so nothing drifts."""

    tol = 0.22

    def __init__(self):
        self.d = []
        self.x = self.y = None

    def run(self, pts, close=False):
        q = [pts[0]]
        a = 0
        n = len(pts)
        while a < n - 1:
            b = a + 1
            while b + 1 < n:
                ax, ay = pts[a]
                cx, cy = pts[b + 1]
                L = math.hypot(cx - ax, cy - ay) + 1e-9
                ok = True
                for m in range(a + 1, b + 1):
                    if abs((pts[m][0] - ax) * (cy - ay) - (pts[m][1] - ay) * (cx - ax)) / L > self.tol:
                        ok = False
                        break
                if not ok:
                    break
                b += 1
            q.append(pts[b])
            a = b
        x0, y0 = _r(q[0][0]), _r(q[0][1])
        if self.x is None or close:
            s = 'M' + _j(x0, y0)
        else:
            s = 'm' + _j(_r(x0 - self.x), _r(y0 - self.y))
        px, py = x0, y0
        if len(q) == 1:
            s += 'h0'
        for x, y in q[1:]:
            dx, dy = _r(x - px), _r(y - py)
            if dx == 0 and dy == 0:
                continue
            if dy == 0:
                s += 'h' + _f(dx)
            elif dx == 0:
                s += 'v' + _f(dy)
            else:
                s += 'l' + _j(dx, dy)
            px, py = _r(px + dx), _r(py + dy)
        if close:
            s += 'z'
            self.x = self.y = None
        else:
            self.x, self.y = px, py
        self.d.append(s)

    def dot(self, x, y):
        self.run([(x, y)])

    def s(self):
        return ''.join(self.d)


def _pd(pts, close=True):
    p = _P()
    p.run(pts, close)
    return p.s()


def _stroke(d, w):
    return '<path d="%s" stroke-width="%s"/>' % (d, _f(w)) if d else ''


def _wline(d, w=0.5, rule=''):
    return '<path d="%s" fill="#fff" stroke-width="%s"%s/>' % (d, _f(w), rule) if d else ''


def _white(d, rule=''):
    return '<path d="%s" fill="#fff" stroke="none"%s/>' % (d, rule) if d else ''


def _inpoly(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    ed = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        if a[1] != b[1]:
            ed.append((a[0], a[1], b[0], b[1]))

    def f(x, y):
        if x < x0 or x > x1 or y < y0 or y > y1:
            return False
        c = False
        for ax, ay, bx, by in ed:
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                c = not c
        return c
    f.box = (x0, y0, x1, y1)
    return f


# ------------------------------------------------------------------ line families

def _hl(x0, x1, y, step=3.0):
    n = max(1, int(math.ceil((x1 - x0) / step)))
    return [(x0 + (x1 - x0) * i / n, y) for i in range(n + 1)]


def _vl(x, y0, y1, step=2.0):
    n = max(1, int(math.ceil((y1 - y0) / step)))
    return [(x, y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def _hfam(x0, x1, y0, y1, pitch, step=3.0):
    out = []
    y = y0
    while y <= y1:
        out.append(_hl(x0, x1, y, step))
        y += pitch
    return out


def _vfam(x0, x1, y0, y1, pitch, step=2.0):
    out = []
    x = x0
    while x <= x1:
        out.append(_vl(x, y0, y1, step))
        x += pitch
    return out


def _dfam(box, ang, pitch, step=2.0):
    """Parallel straight lines at angle ang (degrees) covering box, perpendicular pitch."""
    x0, y0, x1, y1 = box
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cs = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    on = [c[0] * nx + c[1] * ny for c in cs]
    ot = [c[0] * dx + c[1] * dy for c in cs]
    out = []
    o = math.floor(min(on) / pitch) * pitch + pitch / 2.0
    while o < max(on):
        pts = []
        t = min(ot)
        while t <= max(ot) + step:
            x, y = o * nx + t * dx, o * ny + t * dy
            if x0 - step <= x <= x1 + step and y0 - step <= y <= y1 + step:
                pts.append((x, y))
            t += step
        if len(pts) > 1:
            out.append(pts)
        o += pitch
    return out


def _bis(a, b, tone):
    """a is inked, b is not: the last inked point toward b."""
    for _ in range(5):
        m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        if tone(m[0], m[1]) > 0:
            a = m
        else:
            b = m
    return a


def _rule(lines, tone, pitch, rng, cap=None, lo=0.4, cell=7.0, soft=False):
    """The burin: each line is cut at 0.5 / 1 / 1.5 px according to tone (0 paper .. 1 black) or
    lifted where the tone runs out (broken dashes in faint tone, exact edges where tone is 0)."""
    if cap is None:
        cap = min(1.5, math.floor((pitch - 0.5) * 2) / 2.0)
    acc = {0.5: _P(), 1.0: _P(), 1.5: _P()}
    for pts in lines:
        n = len(pts)
        if n < 2:
            continue
        nz = [rng.random() for _ in range(32)]
        off = rng.randrange(32)
        ts, qs, dist = [], [], 0.0
        for i, (x, y) in enumerate(pts):
            if i:
                dist += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
            t = tone(x, y)
            ts.append(t)
            w = t * pitch
            if soft:        # weight tapers and the line breaks progressively: no hard step
                r = nz[(int(dist / cell) + off) % 32]
                if w >= 1.4:
                    q = 1.5
                elif w >= 1.2:
                    q = 1.5 if r < (w - 1.2) / 0.2 else 1.0
                elif w >= 0.9:
                    q = 1.0
                elif w >= 0.68:
                    q = 1.0 if r < (w - 0.68) / 0.22 else 0.5
                elif w >= 0.45:
                    q = 0.5
                elif w > 0.03 and r < (w / 0.45) ** 1.2:
                    q = 0.5
                else:
                    q = 0.0
            elif w >= 1.25:
                q = 1.5
            elif w >= 0.75:
                q = 1.0
            elif w >= lo:
                q = 0.5
            elif w > 0.03 and nz[(int(dist / cell) + off) % 32] < (w / lo) ** 1.5:
                q = 0.5
            else:
                q = 0.0
            qs.append(min(q, cap))
        run, rq = [], 0.0
        for i in range(n):
            q = qs[i]
            if i == 0:
                if q:
                    run, rq = [pts[0]], q
                continue
            if q == rq:
                if q:
                    run.append(pts[i])
                continue
            a, b = pts[i - 1], pts[i]
            if rq and q:
                m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                run.append(m)
                acc[rq].run(run)
                run = [m, b]
            elif rq:
                if ts[i] <= 0:
                    e = _bis(a, b, tone)
                    if e != a:
                        run.append(e)
                if len(run) > 1:
                    acc[rq].run(run)
                run = []
            else:
                if ts[i - 1] <= 0:
                    s0 = _bis(b, a, tone)
                    run = [s0, b] if s0 != b else [b]
                else:
                    run = [b]
            rq = q
        if rq and len(run) > 1:
            acc[rq].run(run)
    return ''.join(_stroke(acc[w].s(), w) for w in (0.5, 1.0, 1.5))


# ------------------------------------------------------------------ shapes

def _arch(cx, a, ybase, yspring, rise, n=6):
    """Pointed (two-centred) arch opening as a point list: jamb, arc, apex, arc, jamb."""
    rise = max(rise, a)
    R = (a * a + rise * rise) / (2.0 * a)
    left = []
    for i in range(n + 1):
        d = a * i / float(n)
        left.append((cx - a + d, yspring - math.sqrt(max(0.0, R * R - (R - d) ** 2))))
    pts = [(cx - a, ybase)] + left + [(2 * cx - x, y) for x, y in reversed(left[:-1])] + [(cx + a, ybase)]
    return pts


_MARIA = ((-0.28, -0.48, 0.30, 0.24), (0.22, -0.38, 0.17, 0.17), (0.42, -0.10, 0.20, 0.17),
          (0.72, -0.24, 0.09, 0.11), (0.62, 0.14, 0.11, 0.16), (0.42, 0.28, 0.08, 0.08),
          (-0.62, -0.12, 0.22, 0.38), (-0.18, 0.38, 0.20, 0.16), (-0.50, 0.40, 0.09, 0.09),
          (-0.05, -0.80, 0.40, 0.05), (0.05, -0.18, 0.08, 0.07))


def _maria(x, y):
    x += 0.035 * math.sin(11 * y + 1.0)
    y += 0.035 * math.sin(9 * x + 2.0)
    m = 0.0
    for mx, my, rx, ry in _MARIA:
        v = 1.0 - ((x - mx) / rx) ** 2 - ((y - my) / ry) ** 2
        if v > 0:
            m = max(m, _cl(v * 2.2))
    return m


def _moon(cx, cy, r, phase, rng, tilt=-0.3):
    """Portrait moon: curved rules following the globe, maria in swelling line, the night side in
    crossed rulings (earthshine), limb shading. Lit on the right while waxing; 0.5 is full."""
    phase = phase % 1.0
    k = math.cos(2 * math.pi * phase)
    sg = 1.0 if phase < 0.5 else -1.0
    thin = (1 - k) / 2 < 0.3   # a thin moon: the night side stays pale (earthshine), so it never reads as a black hole
    ct, st = math.cos(tilt), math.sin(tilt)
    fine = r >= 14

    def geom(x, y):
        nx, ny = (x - cx) / r, (y - cy) / r
        rr = nx * nx + ny * ny
        if rr >= 1.0:
            return None
        d = sg * nx - k * math.sqrt(max(0.0, 1 - ny * ny))
        return nx, ny, rr, d

    def lit(x, y):
        g = geom(x, y)
        if g is None:
            return 0.0
        nx, ny, rr, d = g
        if d <= 0:
            return 0.16 if thin else 0.62
        t = 0.5 * _maria(nx * ct - ny * st, nx * st + ny * ct) if fine else 0.3 * _maria(nx, ny)
        t += 0.3 * rr ** 4 + 0.45 * _cl(1 - d / 0.22) ** 1.5
        return t if t > 0.2 else 0.0

    def dark(x, y):
        g = geom(x, y)
        if g is None:
            return 0.0
        nx, ny, rr, d = g
        if d > 0:
            return 0.3 if r > 30 and _ECO[0] < 2 and _maria(nx * ct - ny * st, nx * st + ny * ct) > 0.75 else 0.0
        return 0.0 if thin else 0.34

    out = ['<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke-width=".5"/>' % (_f(cx), _f(cy), _f(r))]
    lines = []
    y0 = -r * 1.12 + 0.6
    while y0 < r:
        pts = []
        x = -r
        while x <= r + 0.01:
            pts.append((cx + x, cy + y0 + 0.11 * r * (1 - (x / r) ** 2)))
            x += 2.0
        lines.append(pts)
        y0 += 1.5
    out.append(_rule(lines, lit, 1.5, rng))
    out.append(_rule(_dfam((cx - r, cy - r, cx + r, cy + r), 62, 1.5, 1.5), dark, 1.5, rng, cap=0.5))
    if r >= 20:
        cr = []
        for ox, oy, rr in ((-0.10, 0.70, 0.07), (-0.33, -0.12, 0.06), (-0.62, -0.02, 0.035), (-0.12, -0.76, 0.05),
                           (0.30, 0.55, 0.05), (0.10, 0.25, 0.045), (0.2, 0.8, 0.04)):
            x, y = cx + ox * r, cy + oy * r
            g = geom(x, y)
            if g and g[3] > 0.1:
                a = max(1.0, rr * r)
                cr.append('M%sa%s %s 0 1 1 %s' % (_j(x - a, y + a * 0.3), _f(a), _f(a), _j(2 * a, 0)))
        out.append(_stroke(''.join(cr), 0.5))
        g = geom(cx - 0.1 * r, cy + 0.7 * r)
        if g and g[3] > 0.1 and r >= 30:     # Tycho's rays, stippled
            p = _P()
            for i in range(9):
                a = -2.6 + i * 0.42
                for j in range(2, 7):
                    x, y = cx - 0.1 * r + math.cos(a) * j * 0.09 * r, cy + 0.7 * r + math.sin(a) * j * 0.09 * r
                    gg = geom(x, y)
                    if gg and gg[3] > 0.05 and gg[2] < 0.9:
                        p.dot(x, y)
            out.append(_stroke(p.s(), 0.5))
    return ''.join(out)


def _wst(d, w):
    return '<path d="%s" stroke="#fff" stroke-width="%s"/>' % (d, _f(w)) if d else ''


def _fir(x, base, h, rng, tone=0.7, lit=1):
    """A Douglas fir as a wood engraver cuts it: a dark mass built of drooping bough strokes
    (each tier kinked and spaced by hand, heavy on the shadow side), then the boughs themselves
    cut out of the dark in white line where the moon catches them, the trunk glimpsed between
    tiers (lit = +1 moon to the right)."""
    n = int(_cl(h / 10.0, 5, 20))
    top = base - h
    dy = h / float(n)

    def hw(t):
        return h * 0.2 * t ** 0.8 + 0.8
    L, R, ws = [], [], {}
    for i in range(1, n + 1):
        t = i / float(n)
        y = top + h * t
        for side, sgn in ((L, -1), (R, 1)):
            w = hw(t) * rng.uniform(0.82, 1.16)
            ws[(i, sgn)] = w
            side.append((x + sgn * w, y + dy * 0.3))
            if i < n:
                side.append((x + sgn * w * rng.uniform(0.6, 0.78), y - dy * 0.04))
    poly = [(x, top - 1)] + R + [(x + 1, base + 1), (x - 1, base + 1)] + L[::-1]
    ins = _inpoly(poly)
    wmax = hw(1.0) * 1.2
    vp = 2.6
    fam = []
    y0 = top - wmax * 0.8
    while y0 < base + 2:
        k1, k2 = rng.uniform(0.8, 1.0), rng.uniform(0.35, 0.55)
        kx = wmax * rng.uniform(0.35, 0.5)
        key = [(-wmax, y0 + kx * k1 + (wmax - kx) * k2), (-kx, y0 + kx * k1), (0, y0), (kx, y0 + kx * k1), (wmax, y0 + kx * k1 + (wmax - kx) * k2)]
        pts = []
        for a, b in zip(key, key[1:]):
            m = max(1, int(abs(b[0] - a[0]) / 1.5))
            pts += [(x + a[0] + (b[0] - a[0]) * q / m, a[1] + (b[1] - a[1]) * q / m) for q in range(m)]
        pts.append((x + key[-1][0], key[-1][1]))
        fam.append(pts)
        y0 += vp + rng.uniform(0, 0.5)

    def tf(px, py):
        if not ins(px, py):
            return 0.0
        side = (px - x) / wmax * lit
        return 0.6 if side < 0.08 else 0.36     # shadow side: the heaviest cuts
    out = [_wline(_pd(poly)), _rule(fam, tf, vp, rng, cap=1.5)]
    bb = ins.box
    out.append(_rule(_dfam(bb, 90 + 16 * lit, 2.0, 2.0),
                     lambda px, py: 0.3 if ins(px, py) and (px - x) * lit < -0.05 * wmax else 0.0, 2.0, rng, cap=0.5))
    # needle clusters: sprays of white cuts along every bough (thick where the moon strikes), and
    # black needles breaking the outline at the tips; the trunk glimpsed between tiers
    w10, w05, bn = _P(), _P(), _P()
    nl = _cl(dy * 0.5, 2.2, 5.5)
    for i in range(2, n + 1):
        t = i / float(n)
        y = top + h * t
        for sgn in (-1, 1):
            w = ws[(i, sgn)]
            if w < 3.0:
                continue
            m = max(2, int(w / 3.4))
            for q in range(m):
                f = 0.16 + 0.84 * (q + rng.uniform(0.2, 0.8)) / m
                bx_ = x + sgn * w * f
                by_ = y - dy * 0.8 + dy * 1.0 * f ** 1.3
                a0 = math.atan2(0.55, sgn)
                on = sgn == lit
                for k, da in enumerate((0.0, 0.6, -0.6)):
                    if not on and (k or q % 2):
                        continue
                    a = a0 + da * sgn + rng.uniform(-0.15, 0.15)
                    ln = nl * rng.uniform(0.7, 1.1) * (1.0 if k == 0 else 0.75)
                    (w10 if on and k == 0 and f > 0.45 else w05).run([(bx_, by_), (bx_ + math.cos(a) * ln, by_ + math.sin(a) * ln)])
            tx, ty = x + sgn * w, y + dy * 0.3
            for da in (-0.5, 0.0, 0.5):
                a = math.atan2(0.5, sgn) + da
                bn.run([(tx - sgn * 0.5, ty - 0.5), (tx + math.cos(a) * nl * 0.6, ty + math.sin(a) * nl * 0.6)])
        if i % 2 == 0 and dy > 5:
            w10.run([(x - lit * 0.5, y - dy * 0.5), (x - lit * 0.5, y - dy * 0.12)])
    out.append(_wst(w10.s(), 1.0) + _wst(w05.s(), 0.5) + _stroke(bn.s(), 0.5))
    out.append(_stroke('M%sV%s' % (_j(x, top - 3), _f(top + 2)), 0.5))
    return ''.join(out)


def _grid(fn, x0, y0, x1, y1, cell):
    """Sample fn on a grid once; return a fast bilinear lookup."""
    nx = int((x1 - x0) / cell) + 3
    ny = int((y1 - y0) / cell) + 3
    g = [[fn(x0 + i * cell, y0 + j * cell) for i in range(nx)] for j in range(ny)]

    def f(x, y):
        fx = (x - x0) / cell
        fy = (y - y0) / cell
        fx = 0.0 if fx < 0 else (nx - 1.001 if fx > nx - 1.001 else fx)
        fy = 0.0 if fy < 0 else (ny - 1.001 if fy > ny - 1.001 else fy)
        i = int(fx)
        j = int(fy)
        a = fx - i
        b = fy - j
        r0 = g[j]
        r1 = g[j + 1]
        return (r0[i] * (1 - a) + r0[i + 1] * a) * (1 - b) + (r1[i] * (1 - a) + r1[i + 1] * a) * b
    return f


def _wfam(x0, x1, y0, y1, pitch, step=3.0, a1=2.5, l1=70.0, a2=1.2, l2=29.0):
    """Near-horizontal lines that undulate together, as a hand lays a tint."""
    out = []
    y = y0
    n = int((x1 - x0) / step) + 1
    while y <= y1:
        out.append([(x0 + i * step, y + a1 * math.sin((x0 + i * step) / l1 + y / 23.0) + a2 * math.sin((x0 + i * step) / l2 - y / 11.0))
                    for i in range(n + 1)])
        y += pitch
    return out


def _bend(lines, amp=1.5, wl=40.0):
    return [[(x, y + amp * math.sin(x / wl + y / (wl * 1.3))) for x, y in ln] for ln in lines]


def _cloudfield(banks, rng):
    """Cloud density from banks of soft lobes with flat bases."""
    blobs = []
    for bx, by, ln, R in banks:
        n = max(3, int(ln / (R * 1.1)))
        for i in range(n):
            f = (i + 0.5) / n
            r = R * (0.45 + 0.6 * math.sin(math.pi * f)) * rng.uniform(0.75, 1.15)
            blobs.append((bx - ln / 2.0 + ln * f + rng.uniform(-0.3, 0.3) * R, by - r * rng.uniform(0.3, 0.8), r * 1.5, r, by))

    def c(x, y):
        v = 0.0
        for cx, cy, rx, ry, base in blobs:
            dx = (x - cx) / rx
            if -2.2 < dx < 2.2:
                dy = (y - cy) / ry
                if -2.2 < dy < 2.2:
                    g = math.exp(-dx * dx - dy * dy)
                    if y > base:
                        g *= max(0.0, 1 - (y - base) / (ry * 0.35))
                    v += g
        return v
    return c


def _skytone(W, yh, night, cfield, mx, my):
    """Night tone with clouds modelled by the moon: bright rims facing it, dark far sides."""
    cg = _grid(cfield, 0, 0, W, yh, 3.0)

    def t(x, y):
        nt = night(x, y)
        c0 = cg(x, y)
        cc = _cl(c0 * 1.5)
        if cc <= 0.01:
            return nt
        d = math.hypot(x - mx, y - my) + 1e-6
        lit = _cl(0.42 + 2.4 * (c0 - cg(x + 7 * (mx - x) / d, y + 7 * (my - y) / d)))
        lit *= _cl(1.3 - d / (0.8 * W))
        return nt * (1 - cc) + (0.08 + 0.66 * (1 - lit)) * cc
    return _grid(t, 0, 0, W, yh, 3.0)


def _skycut(W, yh, tone, rng):
    """Three layers of curved cuts: an undulating tint, then two crossed layers in the darks."""
    o = _rule(_wfam(0, W, 0.75, yh + 2, 1.5, 3.0), tone, 1.5, rng, cap=1.0, cell=8.0, soft=True)
    o += _rule(_bend(_dfam((0, 0, W, yh), -32, 2.0, 3.0), 1.5, 40.0), lambda x, y: (tone(x, y) - 0.42) * 1.2, 2.0, rng, cap=1.0, cell=8.0, soft=True)
    o += _rule(_bend(_dfam((0, 0, W, yh), 58, 2.0, 3.0), 1.5, 33.0), lambda x, y: (tone(x, y) - 0.66) * 1.6, 2.0, rng, cap=0.5, cell=8.0, soft=True)
    return o


def _tree(fills, hv, lt, x, yb, h, w, sh, dark, rng):
    """One small fir of a wooded hillside (appended to the row's shared paths)."""
    if h < 7:
        fills.run([(x - w, yb), (x + rng.uniform(-0.3, 0.3), yb - h), (x + w, yb)])
        (hv if dark else lt).run([(x + sh * 0.4, yb - h + 1.5), (x + sh * w * 0.45, yb)])
        return
    L = [(x - w, yb), (x - w * 0.5, yb - h * 0.3), (x - w * 0.72, yb - h * 0.34), (x - w * 0.25, yb - h * 0.62), (x - w * 0.42, yb - h * 0.66)]
    R = [(x + w * 0.42, yb - h * 0.66), (x + w * 0.25, yb - h * 0.62), (x + w * 0.72, yb - h * 0.34), (x + w * 0.5, yb - h * 0.3), (x + w, yb)]
    fills.run(L + [(x + rng.uniform(-0.4, 0.4), yb - h)] + R)
    (hv if dark else lt).run([(x + sh * 0.4, yb - h + 2), (x + sh * 0.5, yb)])
    k = 0
    st = 0.16 if dark else 0.24
    while 0.2 + st * k < 0.95:
        f = 0.2 + st * k
        (hv if dark else lt).run([(x + sh * 0.5, yb - h * (1 - f) - 1), (x + sh * w * f * 0.95, yb - h * (1 - f) + h * 0.14)])
        if dark:
            lt.run([(x - sh * 0.8, yb - h * (1 - f)), (x - sh * w * f * 0.8, yb - h * (1 - f) + h * 0.12)])
        k += 1
    if dark and w > 3.2:
        hv.run([(x + sh * w * 0.45, yb - h * 0.3), (x + sh * w * 0.55, yb)])


def _forest(top, ybot, x0, x1, hfn, rng, shade, dark=True):
    """A hillside massed with individual firs, rank on rank from the crest down to ybot."""
    out = []
    off = 0.0
    hm = max(3.0, hfn((x0 + x1) / 2.0))
    for r in range(80):
        fills, hv, lt = _P(), _P(), _P()
        drew = False
        x = x0 - rng.uniform(0, 4)
        while x < x1 + 4:
            h = hfn(x) * rng.uniform(0.75, 1.3) * (1.0 + 0.04 * r)
            w = max(1.6, h * rng.uniform(0.26, 0.36))
            yb = top(x) + off + rng.uniform(-0.8, 0.8)
            yq = ybot(x) if callable(ybot) else ybot
            if yb <= yq + 1:
                drew = True
                _tree(fills, hv, lt, x, min(yb, yq), h, w, shade(x), dark, rng)
            x += w * rng.uniform(1.4, 2.0) * (1.0 if dark else 1.45)
        if not drew:
            break
        out.append(_wline(fills.s()) + _stroke(hv.s(), 1.0) + _stroke(lt.s(), 0.5))
        off += hm * 0.5
    return ''.join(out)


def _tuft(P, x, y, sz, rng):
    for j in range(4):
        dx = (j - 1.5) * sz * 0.34 + rng.uniform(-0.6, 0.6)
        P.run([(x + dx * 0.25, y), (x + dx * 0.8, y - sz * 0.62), (x + dx * 1.35, y - sz * rng.uniform(0.8, 1.05))])


def _stone(fills, light, heavy, x, y, r, rng):
    pts = []
    for k in range(8):
        a = math.pi * 2 * k / 8
        rr = r * rng.uniform(0.85, 1.12)
        pts.append((x + rr * 1.35 * math.cos(a), y - rr * 0.8 * max(math.sin(a), -0.22)))
    fills.run(pts, True)
    heavy.run([(x + 0.1 * r, y - 0.02 * r), (x + 1.05 * r, y - 0.02 * r)])
    light.run([(x + 0.45 * r, y - 0.3 * r), (x + 1.1 * r, y - 0.3 * r)])
    heavy.run([(x - 0.7 * r, y + 0.22 * r + 1.6), (x + 1.7 * r, y + 0.22 * r + 1.6)])


def _reed(light, head, x, y, hh, rng):
    lean = rng.uniform(-0.18, 0.3) * hh
    light.run([(x, y), (x + lean * 0.4, y - hh * 0.55), (x + lean, y - hh)])
    hl = max(2.0, hh * 0.16)
    head.run([(x + lean * 0.78, y - hh * 0.8 + hl * 0.2), (x + lean * 0.92, y - hh * 0.8 - hl * 0.8)])
    light.run([(x + 1, y), (x + 1 + hh * 0.16, y - hh * 0.42), (x + 1 + hh * 0.42, y - hh * 0.46)])


def _star(x, y, R):
    """A bright planet as a rayed star."""
    d = ''
    for i in range(8):
        a = i * math.pi / 4
        L = R if i % 2 == 0 else R * 0.5
        d += 'M%sL%s' % (_j(x + math.cos(a) * 2.2, y + math.sin(a) * 2.2), _j(x + math.cos(a) * L, y + math.sin(a) * L))
    d2 = ''
    for i in range(4):
        a = i * math.pi / 2
        d2 += 'M%sL%s' % (_j(x, y), _j(x + math.cos(a) * R * 0.42, y + math.sin(a) * R * 0.42))
    return _stroke(d, 0.5) + _stroke(d2, 1.0) + _stroke('M%sh0' % _j(x, y), 1.5)


def _wstar(x, y, a):
    """Four-pointed white star knock-out (path data)."""
    b = a * 0.28
    return _pd([(x - a, y), (x - b, y - b), (x, y - a), (x + b, y - b), (x + a, y), (x + b, y + b), (x, y + a), (x - b, y + b)])


# ====================================================================== St Johns Bridge

def _bridge(W, H, rng, phase):
    out = []
    frieze = H < 0.3 * W
    yh = H * (0.66 if frieze else 0.70)             # far waterline
    eb = (H - yh) * (0.34 if frieze else 0.30)      # near tower base drop below it
    T = min(yh + eb - max(3.0, 0.045 * H), 0.66 * W)
    sf = 0.6 if frieze else 0.5
    xn = W * 0.655
    xf = xn - max(min(0.37 * W, T * 2.6), T * 0.62)
    xv = xn - (xn - xf) / (1 - sf)
    kk = 1.0 / sf - 1.0
    e = eb / T
    hwN = 0.092 * T
    hd, ht, hp, hc = 0.46, 0.036, 0.11, 0.93

    def S(u):
        return 1.0 / (1.0 + kk * u)

    def P(u, h, v=0.0):
        s = S(u)
        return (xv + (xn - xv) * s + v * 0.42 * hwN * s, yh + s * T * (e - h))

    def cable(u):
        if u < 0:
            t = -u / 0.42
            return hc + (hd - hc) * t - 0.035 * math.sin(math.pi * t)
        if u > 1:
            t = (u - 1) / 0.42
            return hc + (hd - hc) * t - 0.035 * math.sin(math.pi * t)
        return hd + 0.03 + (hc - hd - 0.03) * (2 * u - 1) ** 2

    # moon between the towers, above the sag of the cable
    mr = _cl(0.085 * min(H, W * 0.6), 7.0, 30.0)
    mx = xf + (xn - xf) * 0.52
    my = max(mr + 3.0, yh + eb - T * 0.80)
    if yh + eb - T > 0.25 * H:        # tall narrow panel: lift the moon into the open sky
        my = max(mr + 6.0, (yh + eb - T) * 0.55)
        mx = W * 0.36

    def ridge1(x):
        g = _cl(1 - x / W) ** 1.2
        return yh - T * (0.13 + 0.22 * g + 0.025 * math.sin(x / W * 9 + 1) + 0.012 * math.sin(x / W * 23))

    def ridge2(x):
        g = _cl(1 - x / W) ** 1.7
        return yh - T * (0.045 + 0.17 * g + 0.02 * math.sin(x / W * 13 + 2.2)) - 1.5

    def night(x, y):
        d = math.hypot(x - mx, y - my)
        halo = _cl((d - mr * 1.1) / (mr * 4.5))
        halo = halo * halo * (3 - 2 * halo)
        return (0.5 + 0.36 * _cl(1 - y / yh) ** 1.1) * (0.03 + 0.97 * halo)
    cR = _cl(yh * 0.09, 5.0, 22.0)
    banks = [(W * 0.16, yh * 0.38, W * 0.34, cR), (W * 0.87, yh * 0.22, W * 0.28, cR * 0.9),
             (mx - mr * 2.4, my + mr * 2.5, W * 0.3, cR * 0.7), (W * 0.47, yh * 0.1, W * 0.42, cR * 0.75)]
    if yh > 100:
        banks += [(W * 0.3, yh * 0.8, W * 0.5, cR * 0.55), (W * 0.8, yh * 0.62, W * 0.3, cR * 0.6)]
    tg = _skytone(W, yh, night, _cloudfield(banks, rng), mx, my)

    def sky(x, y):
        return 0.0 if y > ridge1(x) + 2 else tg(x, y)
    out.append(_skycut(W, yh, sky, rng))
    # a few stars: white pin-pricks through the tint
    p = _P()
    for _ in range(int(W * yh / 1800)):
        sx, sy = rng.uniform(4, W - 4), rng.uniform(3, yh * 0.7)
        if math.hypot(sx - mx, sy - my) > mr * 2.5 and tg(sx, sy) > 0.55:
            p.dot(sx, sy)
    out.append('<path d="%s" stroke="#fff" stroke-width="1"/>' % p.s())
    out.append(_moon(mx, my, mr, phase, rng))

    # Forest Park: a pale far ridge and a nearer wooded one, both cut in contours that follow the
    # slope, with individual firs standing along each crest
    amp = _cl(T * 0.03, 2.2, 7.0)
    shd = lambda x: -1 if x < mx else 1
    step = 6.0
    for rf in (ridge1, ridge2):
        rr = [(x * step, rf(x * step)) for x in range(int(W / step) + 2)]
        out.append(_white(_pd([(-2, yh + 1)] + rr + [(W + step, yh + 1)])))
        if rf is ridge1:        # pale and small with distance, in hairline only
            out.append(_forest(ridge1, lambda x: min(yh, ridge2(x) + amp * 2), 0, W, lambda x: amp * 1.15, rng, shd, False))
            out.append(_rule(_wfam(0, W, yh - 0.36 * T, yh, 2.0, 4.0, 1.5, 50.0, 0.8, 21.0),
                             lambda x, y: 0.26 if ridge1(x) + 2 < y < ridge2(x) + 3 else 0.0, 2.0, rng, cap=0.5, soft=True))
        else:
            out.append(_forest(ridge2, yh, 0, W, lambda x: amp * 2.5, rng, shd, True))

            def mist(x, y):
                if y < ridge2(x) + 1 or y > yh:
                    return 0.0
                return 0.42 + 0.3 * _cl((y - ridge2(x)) / max(4.0, yh - ridge2(x)))
            out.append(_rule(_wfam(0, W, yh - 0.3 * T, yh, 1.5, 4.0, 1.0, 40.0, 0.5, 17.0), mist, 1.5, rng, cap=1.0, soft=True))
    out.append(_stroke('M0 %sH%s' % (_f(yh), _f(W)), 0.5))

    # ---------------------------------------------------------------- geometry of the right bank
    hwp = hwN                                          # near tower half width, px
    Y0 = yh + eb
    bx0 = xn + 1.45 * hwp
    xsb = bx0 - (H - Y0) * 0.75
    shore = []
    for i in range(9):
        t = i / 8.0
        shore.append((bx0 + (xsb - bx0) * t ** 1.25 + (2.0 * math.sin(i * 2.1) if 0 < i < 8 else 0), Y0 + (H - Y0) * t))
    bank = shore + [(W + 1, H), (W + 1, Y0 - 1)]
    inbank = _inpoly(bank)
    pawx = xsb + (W - xsb) * 0.30
    pawy = H - (H - Y0) * 0.34

    # ---------------------------------------------------------------- river
    refl = [(xn, hwp * 1.1, Y0, T * 0.62), (xf, hwp * sf * 1.1, yh + sf * eb, T * sf * 0.62)]

    def river(x, y):
        if inbank(x, y):
            return 0.0
        d = max(0.0, (y - yh) / (H - yh))
        j = 2.2 * math.sin(y * 12.9898) + 1.3 * math.sin(y * 4.7)
        t = 0.34 + 0.24 * d
        t += 0.42 * math.exp(-(y - yh) / (0.16 * (H - yh) + 1)) * _cl((yh - ridge2(x)) / (0.2 * T) + 0.3)
        for c, hw_, yb, hpx in refl:
            if yb - 1 < y < yb + hpx:
                f = 1 - (y - yb) / hpx
                if abs(x - c - j * (1.5 - f)) < hw_:
                    t += 0.5 * f ** 0.5
                    if abs(x - c - j) < hw_ * 0.38 and f > 0.25:
                        t -= 0.3
        gw = mr * (0.45 + 1.5 * d)
        if abs(x - mx - j * (1 + 2 * d)) < gw:
            t *= 0.18
        return t
    y = yh + 1.5
    ek = 0.5 * max(0, _ECO[0] - 1)
    bands = ((0.22, 1.5 + ek), (0.5, 2.0 + ek), (0.78, 2.5 + ek), (1.01, 3.0 + ek))
    nxr = int(W / 2.0) + 2
    for lim, pt in bands:
        fam = []
        while y <= yh + (H - yh) * lim and y < H + 1:
            d = (y - yh) / (H - yh)
            am = min(0.3 * pt, 0.2 + 1.3 * d)
            wl = 4.0 + 15.0 * d
            ph, ph2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
            fam.append([(i * 2.0, y + am * math.sin(i * 2.0 / wl + ph) + 0.4 * am * math.sin(i * 2.0 / (wl * 0.37) + ph2)) for i in range(nxr)])
            y += pt
        out.append(_rule(fam, river, pt, rng, cell=6.0, soft=True))
    out.append(_rule(_bend(_dfam((0, yh, W, H), 9, 2.5, 3.0), 1.0, 25.0), lambda x, y: (river(x, y) - 0.6) * 1.5, 2.5, rng, cap=0.5, cell=6.0, soft=True))
    rp = _P()
    for _ in range(int(W * (H - yh) / 500.0)):      # loose ripple strokes in the lit water
        d = rng.uniform(0.08, 1.0)
        ry_ = yh + (H - yh) * d
        rx_ = mx + rng.gauss(0, mr * (1.2 + 3.0 * d))
        a = 1.5 + 5.0 * d * rng.uniform(0.5, 1.0)
        if 2 < rx_ < W - 2 and not inbank(rx_, ry_):
            rp.run([(rx_ - a, ry_), (rx_ - a * 0.3, ry_ + 0.3 + 0.5 * d), (rx_ + a * 0.4, ry_ + 0.3 + 0.5 * d), (rx_ + a, ry_ - 0.2)])
    out.append(_stroke(rp.s(), 0.5))

    # ---------------------------------------------------------------- deck, truss, cables
    s0 = (W + 6 - xv) / (xn - xv)
    u0 = (1.0 / s0 - 1.0) / kk
    u1 = 1.42
    gap = P(0.3, hd - ht, 1)[1] - (P(0.3, hd - ht, -1)[1] +
                                   (P(0.3, hd - ht, 1)[0] - P(0.3, hd - ht, -1)[0]) *
                                   (P(0.4, hd, -1)[1] - P(0.3, hd, -1)[1]) / (P(0.4, hd, -1)[0] - P(0.3, hd, -1)[0]))
    # far cable and its suspenders
    us = [u1 + (max(u0, -0.42) - u1) * i / 60.0 for i in range(61)]
    out.append(_stroke(_pd([P(u, cable(u), 1) for u in us], False), 0.5))
    if abs(gap) >= 1.5:
        under = [P(u0, hd - ht, -1), P(u1, hd - ht, -1), P(u1, hd - ht, 1), P(u0, hd - ht, 1)]
        inu = _inpoly(under)
        out.append(_white(_pd(under)))
        bb = inu.box
        out.append(_rule(_dfam(bb, 75, 1.5, 1.5), lambda x, y: 0.66 if inu(x, y) else 0.0, 1.5, rng))
        out.append(_stroke(_pd([under[2], under[3]], False), 0.5))
    band = [P(u0, hd, -1), P(u1, hd, -1), P(u1, hd - ht, -1), P(u0, hd - ht, -1)]
    out.append(_white(_pd(band)))
    zz = _P()
    du = 1.0 / 34
    u = u0
    i = 0
    while u < u1:
        if ht * T * S(u) >= 2.2:
            a, b = P(u, hd, -1), P(u + du / 2, hd - ht, -1)
            c = P(u + du, hd, -1)
            zz.run([a, b, c])
        elif ht * T * S(u) >= 1.2:
            zz.run([P(u, hd, -1), P(u, hd - ht, -1)])
        u += du
        i += 1
    out.append(_stroke(zz.s(), 0.5))
    umid = 0.45
    out.append(_stroke(_pd([P(u0, hd, -1), P(umid, hd, -1)], False), 1.0))
    out.append(_stroke(_pd([P(umid, hd, -1), P(u1, hd, -1)], False) + _pd([P(u0, hd - ht, -1), P(u1, hd - ht, -1)], False) +
                       (_pd([P(u0, hd + 0.014, -1), P(0.8, hd + 0.014, -1)], False) if T > 150 else ''), 0.5))
    # near cable and suspenders
    sp = _P()
    dus = 1.0 / ((26 if T > 110 else 20) - 4 * min(2, _ECO[0]))
    u = math.ceil(max(u0, -0.42) / dus) * dus
    while u < u1:
        if cable(u) - hd > 0.012 and abs(u) > 0.03 and abs(u - 1) > 0.03:
            sp.run([P(u, cable(u), -1), P(u, hd, -1)])
        u += dus
    out.append(_stroke(sp.s(), 0.5))
    usn = [u for u in us if u <= 0.5]
    usf = [u for u in us if u >= 0.5]
    out.append(_stroke(_pd([P(u, cable(u), -1) for u in usf] + [P(0.5, cable(0.5), -1)], False), 1.0))
    out.append(_stroke(_pd([P(0.5, cable(0.5), -1)] + [P(u, cable(u), -1) for u in usn], False), 1.5 if T > 110 else 1.0))

    # ---------------------------------------------------------------- towers
    def tower(u, near):
        s = S(u)
        c = xv + (xn - xv) * s
        hw_ = hwN * s
        Ts = T * s
        yb = yh + s * eb

        def Y(h):
            return yb - h * Ts

        def tap(h):
            return 1.0 - 0.2 * _cl((h - hp) / (1 - hp))
        ai = 0.40 * hw_
        o = []
        # silhouette, clockwise from the pier's lower left
        left = [(-1.16, 0.0), (-1.16, hp), (-1.0, hp + 0.012), (-1.0, 0.925), (-0.93, 0.935), (-0.72, 1.0), (-0.52, 0.935), (-0.5, 0.915)]
        sil = [(c + v * hw_ * (tap(h) if abs(v) <= 1 and h > hp else 1), Y(h)) for v, h in left]
        sil += [(c - ai, Y(0.915)), (c - ai, Y(0.905)), (c, Y(0.925)), (c + ai, Y(0.905)), (c + ai, Y(0.915))]
        sil += [(c - v * hw_ * (tap(h) if abs(v) <= 1 and h > hp else 1), Y(h)) for v, h in reversed(left)]
        ops = [_arch(c, ai, Y(hp + 0.015), Y(0.33), 0.065 * Ts),
               _arch(c, ai, Y(hd + 0.004), Y(0.615), 0.07 * Ts),
               _arch(c, ai * 0.92, Y(0.735), Y(0.80), 0.065 * Ts)]
        if hw_ > 9:      # little arch through the concrete pier
            ops.append(_arch(c, ai * 0.8, Y(0.0) + 1, Y(0.045), 0.04 * Ts, 4))
        ins = _inpoly(sil)
        inop = [_inpoly(q) for q in ops]
        d = _pd(sil) + ''.join(_pd(q) for q in ops)
        o.append(_wline(d, 1.0 if near and hw_ > 7 else 0.5, ' fill-rule="evenodd"'))
        atm = 1.0 if near else 0.8

        def tf(x, y):
            if not ins(x, y):
                return 0.0
            for f in inop:
                if f(x, y):
                    return 0.0
            h = (yb - y) / Ts
            v = (x - c) / hw_
            if h < hp:
                return atm * (0.3 + 0.2 * (v + 1.16) / 2.32)
            if h > 0.93:
                return atm * (0.2 if (v < -0.72 or 0 < v < 0.72) else 0.6)
            if abs(v) * 1.0 > 0.40:
                tp = tap(h)
                f = (abs(v) - 0.4) / max(0.05, tp - 0.4)
                f = 1 - f if v < 0 else f
                base = (0.2 + 0.26 * f) if v < 0 else (0.36 + 0.3 * f)
                return atm * base
            t = 0.4
            for hb in (0.425, 0.735, 0.905):       # shadow under each strut
                if 0 < hb - h < 0.03:
                    t = 0.68
            return atm * t
        pt = 1.5
        o.append(_rule(_vfam(c - hw_ * 1.16 + 0.5, c + hw_ * 1.16, Y(1.0), yb, pt, 2.0), tf, pt, rng))
        # crossed ruling: the shadowed leg, soffits, pier courses

        def xf_(x, y):
            t = tf(x, y)
            if t <= 0:
                return 0.0
            h = (yb - y) / Ts
            v = (x - c) / hw_
            if h < hp:
                return 0.34
            if v > 0.4 and h < 0.93:
                return 0.34 if v > 0.7 else 0.0
            if abs(v) < 0.4:
                return 0.34 if t > 0.6 else 0.0
            return 0.0
        if hw_ > 4:
            o.append(_rule(_hfam(c - hw_ * 1.2, c + hw_ * 1.2, Y(0.93), yb, 2.0, 1.5), xf_, 1.5, rng, cap=0.5))
        # inner leg faces (the depth of the steel) and strut lines
        dl = _P()
        if hw_ > 6 and _ECO[0] < 3:
            for sgn in (-1,):
                for hb in (0.425, 0.69, 0.735):
                    dl.run([(c - ai, Y(hb)), (c + ai, Y(hb))])
            # lancet panels down each leg
            hh = hp + 0.03
            while hh < 0.89:
                if not (hd - ht - 0.06 < hh < hd + 0.01):
                    for sgn in (-1, 1):
                        lc = c + sgn * hw_ * (0.4 + tap(hh + 0.03)) / 2.0
                        a = max(0.9, hw_ * 0.085)
                        q = _arch(lc, a, Y(hh), Y(hh + 0.034), a * 1.6, 2)
                        dl.run(q)
                hh += 0.058
        if hw_ > 9:
            rb, rw, mj = _P(), _P(), _P()
            hh = hp + 0.02
            while hh < 0.92:
                tp = tap(hh)
                for v in (-tp + 0.07, -0.47, 0.47, tp - 0.07):
                    (rb if v < 0 else rw).dot(c + v * hw_, Y(hh))
                hh += max(0.012, 3.0 / Ts)
            for hb in (0.415, 0.435, 0.70, 0.725, 0.895, 0.915):       # rivet rows on the struts
                xx = c - ai + 1.5
                while xx < c + ai - 1:
                    rw.dot(xx, Y(hb))
                    xx += 3.0
            yy = Y(hp) + 3.0
            k = 0
            while yy < yb - 1:                                         # masonry courses of the pier
                mj.run([(c - 1.16 * hw_ + 0.5, yy), (c + 1.16 * hw_ - 0.5, yy)])
                xx = c - 1.16 * hw_ + (3.0 if k % 2 else 6.5)
                while xx < c + 1.16 * hw_ - 1:
                    mj.run([(xx, yy - 3.0), (xx, yy)])
                    xx += 7.0
                yy += 3.0
                k += 1
            o.append(_stroke(rb.s(), 1.0) + _wst(rw.s(), 1.0) + _wst(mj.s(), 0.5))
        # finials
        for sgn in (-1, 1):
            tx = c + sgn * 0.72 * hw_ * tap(1.0)
            dl.run([(tx, Y(1.0)), (tx, Y(1.0) - max(2.0, 0.022 * Ts))])
            if hw_ > 8:
                dl.run([(tx - 1.2, Y(1.0) - 0.012 * Ts), (tx + 1.2, Y(1.0) - 0.012 * Ts)])
        o.append(_stroke(dl.s(), 0.5))
        return ''.join(o)

    out.append(tower(1.0, False))
    out.append(tower(0.0, True))

    # ---------------------------------------------------------------- Cathedral Park: trees, pier, bank
    up = -0.24 if not frieze else -0.2
    def ytree(x):
        g = _cl((x - bx0 + hwp * 0.2) / (W - bx0 + 1)) ** 0.6
        return Y0 - 1 - T * 0.15 * g * (1 + 0.12 * math.sin(x / 9.0))
    if W - bx0 > 8:
        out.append(_forest(ytree, Y0 + 1, bx0 - hwp * 0.2, W, lambda x: _cl(T * 0.05, 5.0, 13.0), rng, lambda x: 1, True))
        fx_ = bx0 + T * 0.03
        while fx_ < W + 6:
            g_ = _cl((fx_ - bx0) / (W - bx0 + 1))
            fh_ = T * (0.09 + 0.15 * g_) * rng.uniform(0.85, 1.15)
            if fh_ >= 14:
                out.append(_fir(fx_, Y0 + 1, fh_, rng, 0.72, -1))
            fx_ += max(7.0, fh_ * rng.uniform(0.28, 0.4))

    s = S(up)
    c = xv + (xn - xv) * s
    if c - hwN * s < W - 2:
        hw_ = hwN * s * 0.86
        yb = yh + s * T * (e - 0.012)
        ytp = yh + s * T * (e - (hd - ht))
        leg = 0.3 * hw_
        sil = [(c - hw_, yb), (c - hw_ * 0.94, ytp), (c + hw_ * 0.94, ytp), (c + hw_, yb)]
        opn = _arch(c, hw_ - leg, yb, ytp + (yb - ytp) * 0.36, (hw_ - leg) * 1.25, 6)
        ins, ino = _inpoly(sil), _inpoly(opn)
        d = _pd(sil) + _pd(opn)
        out.append(_wline(d, 0.5, ' fill-rule="evenodd"'))

        def pf(x, y):
            if not ins(x, y) or ino(x, y):
                return 0.0
            return 0.22 + 0.36 * _cl((x - c + hw_) / (2 * hw_)) + (0.25 if y < ytp + 0.03 * T * s else 0)
        out.append(_rule(_vfam(c - hw_ + 0.5, c + hw_, ytp, yb, 2.0, 2.0), pf, 2.0, rng))
        out.append(_rule(_hfam(c, c + hw_, ytp, yb, 2.0, 2.0), lambda x, y: 0.28 if pf(x, y) > 0 and x > c + hw_ - leg else 0.0, 2.0, rng, cap=0.5))

    out.append(_white(_pd(bank)))
    paw_ok = W - pawx > 12 and H - Y0 > 14

    def shx(y):
        t = _cl((y - Y0) / (H - Y0))
        return bx0 + (xsb - bx0) * t ** 1.25

    def bf(x, y):
        if not inbank(x, y):
            return 0.0
        if paw_ok and math.hypot(x - pawx, y - pawy) < 5.5:
            return 0.0
        d = (y - Y0) / (H - Y0)
        t = 0.34 + 0.16 * d + 0.13 * math.sin(x / 23.0 + y / 6.0) + 0.3 * math.exp(-(x - shx(y)) / 7.0)
        if ((x - c) / (hwN * s * 1.9)) ** 2 + ((y - Y0 - (H - Y0) * 0.26) / ((H - Y0) * 0.2)) ** 2 < 1:
            t += 0.22        # the approach casts its shade
        return t
    fam = []
    y = Y0 + 1.5
    while y < H + 6:
        d = (y - Y0) / (H - Y0)
        sx = shx(y)
        pts = []
        x = sx - 3
        while x <= W + 3:
            pts.append((x, y + 5.0 * math.exp(-(x - sx) / 8.0) - (x - sx) * 0.035 + 1.0 * math.sin(x / 29.0 + y / 5.0)))
            x += 3.0
        fam.append(pts)
        y += 2.0 + round(d * 2.0) * 0.5
    out.append(_rule(fam, bf, 2.5, rng, cap=1.5, cell=7.0, soft=True))
    out.append(_rule(_bend(_dfam(inbank.box, 62, 2.0, 2.5), 1.2, 21.0), lambda x, y: (bf(x, y) - 0.5) * 1.6, 2.0, rng, cap=0.5, cell=6.0, soft=True))
    sf_, sl_, sh_, gr, rh = _P(), _P(), _P(), _P(), _P()
    area = (W - xsb) * (H - Y0) * 0.6
    gs = _cl((H - Y0) * 0.11, 3.0, 9.0)
    for _ in range(int(area / 300.0) + 2):          # stones
        y = Y0 + (H - Y0) * rng.uniform(0.12, 0.97)
        x = shx(y) + rng.uniform(3, max(8.0, (W - shx(y)) * 0.8))
        if inbank(x, y) and not (paw_ok and math.hypot(x - pawx, y - pawy) < gs * 1.6 + 6):
            _stone(sf_, sl_, sh_, x, y, gs * rng.uniform(0.35, 0.75) * (0.6 + 0.6 * (y - Y0) / (H - Y0)), rng)
    out.append(_wline(sf_.s()) + _stroke(sl_.s(), 0.5) + _stroke(sh_.s(), 1.0))
    for _ in range(int(area / 110.0) + 3):          # grass tufts
        y = Y0 + (H - Y0) * rng.uniform(0.08, 1.0)
        x = shx(y) + rng.uniform(4, max(9.0, W - shx(y)))
        if inbank(x, y) and not (paw_ok and math.hypot(x - pawx, y - pawy) < gs + 5):
            _tuft(gr, x, y, gs * (0.6 + 0.7 * (y - Y0) / (H - Y0)) * rng.uniform(0.8, 1.2), rng)
    y = Y0 + 3
    while y < H + 4:                                                # reeds at the water's edge
        d = (y - Y0) / (H - Y0)
        for _k in range(3):
            _reed(gr, rh, shx(y) + rng.uniform(-5, 2), y + rng.uniform(-1, 2), gs * (1.3 + 1.6 * d) * rng.uniform(0.8, 1.2), rng)
        y += gs * (0.6 + 0.8 * d)
    out.append(_stroke(gr.s(), 0.5) + _stroke(rh.s(), 1.5))
    out.append(_stroke('M%sL%s' % (_j(bx0, Y0), _j(W, Y0 - 1)), 1.0))
    out.append(_stroke(_pd(shore, False), 0.5))
    if paw_ok:      # the hidden paw print
        p = _P()
        for ox, oy in ((-2.2, -1.2), (-0.8, -2.6), (0.9, -2.6), (2.3, -1.2)):
            p.dot(pawx + ox, pawy + oy)
        out.append(_stroke(p.s(), 1.0))
        out.append(_stroke('M%sh1.4' % _j(pawx - 0.7, pawy + 0.8), 1.5))

    # ---------------------------------------------------------------- foreground firs (left repoussoir)
    lim = 0.44 * W
    if frieze:
        firs = [(0.035, 0.8), (0.085, 0.97), (0.135, 0.62)]
    elif W < 320:
        firs = [(0.05, 0.6), (0.14, 0.42)]
    else:
        firs = [(0.04, 0.58), (0.105, 0.74), (0.17, 0.44)]
    for fx, fh in sorted(firs, key=lambda q: q[1]):
        out.append(_fir(W * fx, H + 1, min(H * fh, lim * fh / 0.78), rng, 0.72, 1))
    return ''.join(out)


# ====================================================================== Sauvie Island night sky

_CONS = {
    # stars (x, y, magnitude-ish size) and line index pairs; unit about one "hand"
    'P': ([(0, 0, 1), (0, -1.1, 1), (0, -2.2, 2), (0.85, -2.3, 1), (1.3, -1.75, 2), (0.9, -1.15, 1)],
          [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 1)]),
    'dipper': ([(0, 0, 2), (0.9, -0.25, 1), (1.7, -0.2, 1), (2.5, 0.15, 2), (2.7, 0.95, 1), (3.7, 1.0, 2), (3.8, 0.2, 1)],
               [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)]),
    'cass': ([(0, 0, 1), (0.6, 0.8, 2), (1.3, 0.2, 1), (2.0, 0.9, 2), (2.6, 0.1, 1)], [(0, 1), (1, 2), (2, 3), (3, 4)]),
    'cyg': ([(0, 0, 2), (0.5, 0.9, 1), (1.0, 1.9, 2), (1.5, 3.0, 1), (-0.4, 2.1, 1), (2.2, 1.5, 1)],
            [(0, 1), (1, 2), (2, 3), (4, 2), (2, 5)]),
    'lyra': ([(0, 0, 2), (0.35, 0.7, 1), (1.0, 0.75, 1), (1.2, 1.6, 1), (0.55, 1.55, 1)], [(0, 1), (1, 2), (2, 3), (3, 4), (4, 1)]),
}


def _sky(W, H, rng, phase, planet):
    out = []
    frieze = H < 0.3 * W
    L = _cl(0.2 * H, 22.0, 78.0) if not frieze else max(20.0, 0.27 * H)
    yh = H - L
    mr = _cl(min(yh * 0.25, W * 0.12), 9.0, 60.0)
    mx = W * 0.27
    my = _cl(yh * 0.44, mr + 3, yh - mr - 3)
    pname = (planet or 'venus').lower()
    low = pname in ('venus', 'mercury')
    px = W * (0.86 if low else 0.80)
    py = yh * (0.66 if low else 0.36)
    pR = _cl(yh * 0.085, 6.0, 15.0) * (1.25 if pname in ('venus', 'jupiter') else 1.0)
    # Milky Way axis
    ax, ay = W * 0.61, yh * 0.5
    ang = math.radians(62 if not frieze else 50)
    dxm, dym = math.cos(ang), -math.sin(ang)
    sig = _cl(0.085 * W, 14.0, 60.0)

    def mw(x, y):
        o = (x - ax) * (-dym) + (y - ay) * dxm
        t = (x - ax) * dxm + (y - ay) * dym
        o += sig * 0.35 * math.sin(t / (sig * 1.7) + 1.0)
        g = math.exp(-(o / sig) ** 2)
        rift = math.exp(-((o + sig * 0.18) / (sig * 0.22)) ** 2) * (0.5 + 0.5 * math.sin(t / (sig * 1.1)))
        return g, rift

    def night(x, y):
        d = math.hypot(x - mx, y - my)
        halo = _cl((d - mr * 1.05) / (mr * 2.6))
        halo = halo * halo * (3 - 2 * halo)
        t = 0.52 + 0.36 * _cl(1 - y / yh)
        g, rift = mw(x, y)
        t *= 1 - 0.5 * g * (1 - 0.9 * rift)
        t *= 0.03 + 0.97 * halo
        dp = _cl((math.hypot(x - px, y - py) - pR * 0.3) / (pR * 1.7))
        t *= 0.1 + 0.9 * dp * dp
        return t
    cR = _cl(yh * 0.05, 3.0, 12.0)
    tg = _skytone(W, yh + 3, night, _cloudfield([(W * 0.52, yh * 0.9, W * 0.5, cR), (W * 0.9, yh * 0.8, W * 0.3, cR * 0.9), (W * 0.1, yh * 0.72, W * 0.3, cR * 0.8)], rng), mx, my)
    sky = tg
    out.append(_skycut(W, yh, tg, rng))

    # Milky Way stipple
    p5, p10 = _P(), _P()
    n = int(min(900, yh * sig / 6.0))
    tl = math.hypot(W, yh) * 0.6
    for _ in range(n):
        t = rng.uniform(-tl, tl)
        o = rng.gauss(0, sig * 0.62)
        x = ax + t * dxm + o * (-dym)
        y = ay + t * dym + o * dxm
        if not (1 < x < W - 1 and 1 < y < yh - 2):
            continue
        g, rift = mw(x, y)
        if rng.random() < rift * 0.9 or math.hypot(x - mx, y - my) < mr + 3 or math.hypot(x - px, y - py) < pR:
            continue
        (p10 if rng.random() < 0.2 else p5).dot(x, y)
    out.append(_stroke(p5.s(), 1.0) + _stroke(p10.s(), 1.5))

    # field stars: white pin-pricks on the rules
    p = _P()
    for _ in range(int(W * yh / 1500)):
        sx, sy = rng.uniform(3, W - 3), rng.uniform(2, yh - 4)
        if math.hypot(sx - mx, sy - my) > mr * 1.6:
            p.dot(sx, sy)
    out.append('<path d="%s" stroke="#fff" stroke-width="1"/>' % p.s())

    # constellations: white-line cuts with a hairline in them, stars as white sparks with a dot
    un = _cl(yh * 0.085, 5.5, 15.0)
    place = [('P', W * 0.455, yh * 0.60 + un * 1.1, un)]
    if W >= 380:
        place.append(('dipper', W * 0.035, max(un * 1.2, yh * 0.14), un * 0.9))
        place.append(('cass', W * 0.895, max(un * 0.8, yh * 0.1), un * 0.8))
    if yh > 120:
        place.append(('cyg', ax + sig * 0.1, yh * 0.2, un * 0.9))
        place.append(('lyra', W * 0.47, yh * 0.12, un * 0.8))
    wl, bl, ws, bd, bd2 = _P(), _P(), [], _P(), _P()
    for name, ox, oy, u in place:
        stars, links = _CONS[name]
        pts = [(ox + sx * u, oy + sy * u) for sx, sy, _m in stars]
        if any(not (3 < x < W - 3 and 3 < y < yh - 3) or math.hypot(x - mx, y - my) < mr + 4 for x, y in pts):
            if name != 'P':
                continue
        for a, b in links:
            (x0, y0), (x1, y1) = pts[a], pts[b]
            d = math.hypot(x1 - x0, y1 - y0)
            g = min(3.2, d * 0.3)
            sa = (x0 + (x1 - x0) * g / d, y0 + (y1 - y0) * g / d)
            sb = (x1 - (x1 - x0) * g / d, y1 - (y1 - y0) * g / d)
            wl.run([sa, sb])
            bl.run([sa, sb])
        for (x, y), (_x, _y, m) in zip(pts, stars):
            ws.append(_wstar(x, y, 2.6 if m > 1 else 2.0))
            bd.dot(x, y)
            if m > 1:
                bd2.dot(x, y)
    out.append('<path d="%s" stroke="#fff" stroke-width="1.5"/>' % wl.s())
    out.append(_stroke(bl.s(), 0.5))
    out.append(_white(''.join(ws)))
    out.append(_stroke(bd.s(), 1.0) + _stroke(bd2.s(), 1.5))

    out.append(_star(px, py, pR))
    out.append(_moon(mx, my, mr, phase, rng))

    # ---------------------------------------------------------------- the island
    def tree(x):
        return yh - L * (0.16 + 0.07 * math.sin(x / W * 17 + 1) + 0.05 * math.sin(x / W * 41 + 3))
    out.append(_white(_pd([(-2, yh + 2)] + [(x * 6.0, tree(x * 6.0)) for x in range(int(W / 6.0) + 2)] + [(W + 6, yh + 2)])))
    out.append(_forest(tree, yh + 2, 0, W, lambda x: _cl(L * 0.15, 4.0, 11.0), rng, lambda x: -1 if x < mx else 1, True))

    # field with a moonlit slough
    def slough(x, y):
        d = max(0.0, (y - yh) / L)
        cxs = mx + W * 0.05 + (d ** 1.4) * W * 0.16 + 5 * math.sin(d * 5)
        hw_ = 3 + d * W * 0.07
        return abs(x - cxs) < hw_ * (0.8 + 0.3 * math.sin(y * 7.1))

    def field(x, y):
        d = (y - yh) / L
        t = 0.4 + 0.24 * d + 0.03 * math.sin(x / 11.0 + y * 0.9)
        if slough(x, y):
            t *= 0.22
        return t
    y = yh + 1.5
    for lim, pt in ((0.3, 1.5), (0.62, 2.0), (1.01, 2.5)):
        fam = []
        while y <= yh + L * lim and y < H + 1:
            pts = []
            x = 0.0
            d = (y - yh) / L
            while x <= W + 3:
                pts.append((x, y + d * 0.7 * math.sin(x / 47.0 + y * 0.3)))
                x += 3.0
            fam.append(pts)
            y += pt
        out.append(_rule(fam, field, pt, rng, cell=9.0, soft=True))
    # ploughed furrows running to the horizon, then stones, grass and reeds along the slough
    fam = []
    vx = W * 0.52
    xb = -W * 0.7
    while xb < W * 1.7:
        a = (vx + (xb - vx) * 0.5, yh + L * 0.5)
        m = max(2, int(L * 0.5 / 2.5))
        fam.append([(a[0] + (xb - a[0]) * i / m, a[1] + (H + 1 - a[1]) * i / m) for i in range(m + 1)])
        xb += 7.0
    out.append(_rule(fam, lambda x, y: 0.0 if slough(x, y + 1) or x < 0 or x > W else 0.1 + 0.3 * (y - yh - L * 0.5) / (L * 0.5) + 0.08 * math.sin(x / 13.0),
                     2.5, rng, cap=1.0, cell=6.0, soft=True))
    sf_, sl_, sh_, gr, rh = _P(), _P(), _P(), _P(), _P()
    gs = _cl(L * 0.13, 3.0, 9.0)

    def scx(y):
        d = max(0.0, (y - yh) / L)
        return mx + W * 0.05 + (d ** 1.4) * W * 0.16 + 5 * math.sin(d * 5), 3 + d * W * 0.07
    y = yh + L * 0.18
    while y < H + 3:
        d = (y - yh) / L
        cxs, hws = scx(y)
        for sg in (-1, 1):
            if rng.random() < 0.8:
                _reed(gr, rh, cxs + sg * (hws * 1.05 + rng.uniform(0, 4)), y + rng.uniform(-1, 1), gs * (0.7 + 2.0 * d) * rng.uniform(0.8, 1.2), rng)
        y += gs * (0.4 + 0.8 * d)
    for _ in range(int(W * L / 320.0) + 4):
        y = yh + L * rng.uniform(0.3, 1.0)
        x = rng.uniform(2, W - 2)
        cxs, hws = scx(y)
        if abs(x - cxs) > hws * 1.3 + 3:
            sz = gs * (0.4 + 0.9 * (y - yh) / L)
            if rng.random() < 0.22:
                _stone(sf_, sl_, sh_, x, y, sz * rng.uniform(0.4, 0.7), rng)
            else:
                _tuft(gr, x, y, sz * rng.uniform(0.8, 1.2), rng)
    out.append(_wline(sf_.s()) + _stroke(sl_.s(), 0.5) + _stroke(sh_.s(), 1.0) + _stroke(gr.s(), 0.5) + _stroke(rh.s(), 1.5))

    # barn (gambrel roof, three-quarter view), moonlit from the left
    b = min(_cl(L * 0.62, 13.0, 52.0), W * 0.105)
    bx = W * 0.665
    yb = yh + L * 0.24
    A = lambda fx, fy: (bx + fx * b, yb - fy * b)
    front = [A(0, 0), A(0, 0.5), A(0.15, 0.78), A(0.5, 0.96), A(0.85, 0.78), A(1, 0.5), A(1, 0)]
    side = [A(1, 0), A(1, 0.5), A(2.3, 0.53), A(2.3, 0.05)]
    rlo = [A(1, 0.5), A(0.85, 0.78), A(2.17, 0.80), A(2.3, 0.53)]
    rup = [A(0.85, 0.78), A(0.5, 0.96), A(1.84, 0.97), A(2.17, 0.80)]
    door = [A(0.33, 0), A(0.33, 0.34), A(0.67, 0.34), A(0.67, 0)]
    inf, ins_, inl, inu, ind = [_inpoly(q) for q in (front, side, rlo, rup, door)]
    out.append(_white(''.join(_pd(q) for q in (front, side, rlo, rup))))
    out.append(_rule(_vfam(bx + 0.5, bx + b, yb - b, yb, 2.0, 1.5),
                     lambda x, y: (0.7 if ind(x, y) else 0.26) if inf(x, y) else 0.0, 2.0, rng))
    out.append(_rule(_hfam(bx, bx + b, yb - 0.34 * b, yb, 1.5, 1.5), lambda x, y: 0.34 if ind(x, y) else 0.0, 1.5, rng, cap=0.5))
    out.append(_rule(_vfam(bx + b + 0.75, bx + 2.3 * b, yb - b, yb, 1.5, 1.5), lambda x, y: 0.62 if ins_(x, y) else 0.0, 1.5, rng))
    out.append(_rule(_hfam(bx + b, bx + 2.3 * b, yb - 0.55 * b, yb, 2.0, 2.0), lambda x, y: 0.26 if ins_(x, y) else 0.0, 2.0, rng, cap=0.5))
    out.append(_rule(_dfam(inl.box, 62, 1.5, 1.5), lambda x, y: 0.5 if inl(x, y) else 0.0, 1.5, rng))
    out.append(_rule(_dfam(inu.box, 28, 2.0, 1.5), lambda x, y: 0.26 if inu(x, y) else 0.0, 2.0, rng))
    out.append(_stroke(''.join(_pd(q) for q in (front, side, rlo, rup)), 0.5))
    if b > 20:
        out.append(_stroke(_pd([A(0.42, 0.62), A(0.42, 0.76), A(0.58, 0.76), A(0.58, 0.62)]) + _pd([A(0.5, 0.62), A(0.5, 0.76)], False), 0.5))
    # fence running from the barn
    fp = _P()
    fx = bx - b * 0.15
    k = 0
    while fx > W * 0.36:
        d = 0.24 + 0.012 * k * k
        if d > 0.85:
            break
        yy = yh + L * d
        hgt = 2.0 + d * L * 0.16
        fp.run([(fx, yy), (fx, yy - hgt)])
        fx -= 5 + k * 2.2
        k += 1
        if fx > W * 0.36 and 0.24 + 0.012 * k * k <= 0.85:
            y2 = yh + L * (0.24 + 0.012 * k * k)
            fp.run([(fx + 5 + (k - 1) * 2.2, yy - hgt * 0.7), (fx, y2 - (2.0 + (y2 - yh) * 0.16) * 0.7)])
    out.append(_stroke(fp.s(), 0.5))

    # firs: a stand at the left, a pair by the barn, one at the far right
    fmax = (0.8 * H) if frieze else min(2.0 * L, 0.4 * H, 0.5 * W)
    stand = [(0.03, 0.78, 0.5), (0.075, 1.0, 0.42), (0.125, 0.66, 0.6), (0.17, 0.45, 0.4)]
    if W < 320:
        stand = [(0.05, 0.9, 0.5), (0.14, 0.6, 0.6)]
    hb = fmax * 0.5
    stand.append(((bx - hb * 0.22 - 3) / W, 0.5, 0.35))                 # beside the barn, clear of it
    he = fmax * 0.7
    if bx + 2.3 * b < W - he * 0.44 - 2:                                # room at the far right
        stand.append(((W - he * 0.2) / W, 0.7, 0.55))
    for fx, fh, fb in sorted(stand, key=lambda q: q[2]):
        out.append(_fir(W * fx, yh + L * fb, fmax * fh, rng, 0.72, 1 if W * fx < mx else -1))
    return ''.join(out)


# ====================================================================== entry point

def scene(w, h, seed=0, variant="bridge", moon_phase=0.5, planet=None, **kw):
    """SVG child markup (no outer <svg>) filling a w x h box edge to edge."""
    W, H = float(w), float(h)
    rng = random.Random('city-%s-%s-%d-%d' % (variant, seed, int(W), int(H)))
    phase = 0.5 if moon_phase is None else float(moon_phase)
    _ECO[0] = 0
    body = _sky(W, H, rng, phase, planet) if variant == 'sky' else _bridge(W, H, rng, phase)
    return ('<g fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M0 0H%sV%sH0z" fill="#fff" stroke="none"/>%s</g>' % (_f(W), _f(H), body))
