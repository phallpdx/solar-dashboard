"""Two composed engraved plates for the Kindle Evening Edition (black and white, DPR 2).

    lotus(width, height, seed)                 lotus pond at night inside lai-kranok flame scrolls,
                                               rising to a pointed ogee arch at tall sizes. ids "pt"+seed
    bridge(width, height, seed, moon_phase)    St Johns Bridge in fog over the Willamette, Cathedral
                                               Park arches and firs, moon at phase. ids "pb"+seed
    demo()                                     writes /tmp/claude-0/shots/plates/thai.html

No box: every tone is multiplied by a soft vignette so the cuts thin and break off into the
paper at the edges, the way a vignetted banknote engraving sits in the page. Tone is built only
from line: 0.5 px hairlines and swelling cuts at 1.5-2.5 px pitch. No grey fills, no solid black.
Standard library only.
"""
import math
import os
import random

try:
    from .engraving_eink import swell_d, contour_hatch
    from .engraving_thai import _flame_d
except ImportError:  # run as a script
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from engraving_eink import swell_d, contour_hatch
    from engraving_thai import _flame_d

ST = 'stroke="#000"'   # fill none, round caps and joins are inherited from the root


def _f(v):
    s = '%.1f' % v
    if s.endswith('.0'):
        s = s[:-2]
    return '0' if s == '-0' else s


def _pl(pts, close=False):
    """Polyline path data in relative steps (rounded cumulatively, so it never drifts)."""
    px, py = float(_f(pts[0][0])), float(_f(pts[0][1]))
    s = ['M%s %s' % (_f(px), _f(py))]
    for x, y in pts[1:]:
        dx, dy = float(_f(x - px)), float(_f(y - py))
        s.append('l%s %s' % (_f(dx), _f(dy)))
        px, py = px + dx, py + dy
    return ''.join(s) + ('z' if close else '')


def _svg(w, h, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%s" height="%s" viewBox="0 0 %s %s" '
            'fill="none" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (_f(w), _f(h), _f(w), _f(h), body))


def _clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def _vig(W, H, x, y, soft=0.3):
    """1 in the body of the plate, falling softly to 0 at a superelliptical edge: the cuts thin
    and break off into the paper with no box."""
    dx = abs(x - W / 2) / (W / 2)
    dy = abs(y - H / 2) / (H / 2)
    r = (dx ** 5 + dy ** 3) ** 0.25 if H < 150 else (dx ** 4 + dy ** 4) ** 0.25
    return _clamp((1.0 - r) / soft) ** 0.8


def _hlines(x0, x1, y0, y1, pitch, rng, amp=0.0, wl=40.0, step=2.0):
    lines = []
    y = y0
    while y <= y1:
        ph = rng.uniform(0, 6.3)
        a = amp * rng.uniform(0.5, 1.0)
        pts = []
        x = x0
        while x <= x1:
            pts.append((x, y + a * math.sin(x / wl * 6.283 + ph)))
            x += step
        lines.append(pts)
        y += pitch
    return lines


def _hatch(lines, tone, pitch, wmin=0.3, gain=0.92):
    d = contour_hatch(lines, tone, pitch, wmin=wmin, gain=gain, nd=1)
    return '<path fill="#000" d="%s"/>' % d if d else ''


_JIT = random.Random(7)


def _rule(lines, tone, pitch, gain=0.92, step=8.0, wmax=1.5):
    """Engraved rules as stroked polylines whose width is quantised to 0.5 / 1 / 1.5 px from tone;
    where tone drops below a (jittered) threshold the cut lifts and the paper shows."""
    groups = {}
    for pts in lines:
        # resample to ~step spacing to keep the plate small
        if len(pts) > 2:
            keep, acc = [pts[0]], 0.0
            for a, b in zip(pts, pts[1:]):
                acc += math.hypot(b[0] - a[0], b[1] - a[1])
                if acc >= step:
                    keep.append(b)
                    acc = 0.0
            if keep[-1] != pts[-1]:
                keep.append(pts[-1])
            pts = keep
        run, rw = [], None
        for x, y in pts:
            w = max(0.0, tone(x, y)) * pitch * gain
            # below one device pixel the burin skips: presence is dithered, so tone fades as
            # broken dashes rather than a hard edge
            if w < 0.5:
                q = 0.5 if _JIT.random() < (w / 0.5) ** 1.6 else 0.0
            else:
                q = 0.5 if w < 0.8 + 0.2 * _JIT.random() else (1.0 if w < 1.3 else 1.5)
                q = min(q, wmax)
            if q != rw and run:
                if rw and len(run) > 1:
                    groups.setdefault(rw, []).append(run)
                run = [run[-1]] if q and rw else []
            rw = q
            run.append((x, y))
        if rw and len(run) > 1:
            groups.setdefault(rw, []).append(run)
    out = []
    for w, runs in sorted(groups.items()):
        d = []
        for r in runs:
            # drop collinear interior points: straight rules become a single M..L
            q = [r[0]]
            for i in range(1, len(r) - 1):
                ax, ay = r[i][0] - q[-1][0], r[i][1] - q[-1][1]
                bx, by = r[i + 1][0] - r[i][0], r[i + 1][1] - r[i][1]
                if abs(ax * by - ay * bx) > 0.15 * (math.hypot(ax, ay) * math.hypot(bx, by) + 1e-9) or math.hypot(ax, ay) > 60:
                    q.append(r[i])
            q.append(r[-1])
            if all(abs(p[1] - q[0][1]) < 0.05 for p in q):
                d.append('M%s %sH%s' % (_f(q[0][0]), _f(q[0][1]), _f(q[-1][0])))
                continue
            seg = 'M%s %s' % (_f(q[0][0]), _f(q[0][1]))
            px, py = float(_f(q[0][0])), float(_f(q[0][1]))
            for x, y in q[1:]:
                dx, dy = float(_f(x - px)), float(_f(y - py))
                seg += 'l%s %s' % (_f(dx), _f(dy))
                px, py = px + dx, py + dy
            d.append(seg)
        out.append('<path d="%s" %s stroke-width="%s"/>' % (''.join(d), ST, _f(w)))
    return ''.join(out)


def _flames(spec):
    """spec: list of (x, y, ang, s, flip). White-filled kranok flames with hairline detail."""
    o, d = [], []
    for x, y, a, s, fl in spec:
        a1, b1 = _flame_d(x, y, a, s, curl=1.0, hatch=4 if s > 12 else 2, flip=fl)
        o.append(a1)
        d.append(b1)
    return ('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5" stroke-linejoin="round"/>'
            '<path d="%s" %s stroke-width="0.5"/>' % (''.join(o), ''.join(d), ST))


# ====================================================================== lotus

def _petal(bx, by, ang, L, w, side, pitch=1.5, bend=0.0):
    """One lotus petal: outline (closed) and contour-hatch lines that follow its length."""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca

    def hw(t):
        return w * 1.9 * (t ** 0.55) * ((1 - t) ** 0.85)

    def P(t, u):
        b = bend * L * t * t
        return (bx + ca * t * L + nx * (u * hw(t) + b), by + sa * t * L + ny * (u * hw(t) + b))
    n = 10
    left = [P(i / n, -1) for i in range(n + 1)]
    right = [P(i / n, 1) for i in range(n + 1)]
    outline = left + right[::-1]
    k = max(2, int(2 * w / pitch))
    lines = []
    for j in range(1, k):
        u = -1 + 2.0 * j / k
        lines.append([P(0.02 + 0.96 * i / 9, u) for i in range(10)])
    cross = []
    for j in range(1, int(L / pitch / 1.0)):
        t = j * pitch * 1.0 / L
        if t > 0.6:
            break
        cross.append([P(t, -0.95 + 1.9 * i / 5) for i in range(6)])
    # tone: deep at the base, a shadowed flank, the tip left as paper
    span = {}

    def tone(x, y):
        dx, dy = x - bx, y - by
        t = _clamp((dx * ca + dy * sa) / L)
        u = (-dx * sa + dy * ca) / (hw(t) + 0.01)
        return _clamp(0.62 * (1 - t) ** 1.4 + 0.30 * _clamp((u * side + 1) / 2) ** 2 * (1 - t * 0.6)
                      - 0.08)
    def ctone(x, y):
        return _clamp((tone(x, y) - 0.36) * 1.5)
    return outline, lines, tone, cross, ctone


def _bloom(cx, cy, s, rng, pitch=1.5, open_=1.0):
    """A lotus bloom based at (cx, cy) with petal length s."""
    out = []
    spec = [(-1.05, 0.95, 0.30, -1), (1.05, 0.95, 0.30, 1),   # outer back
            (-0.62, 1.0, 0.27, -1), (0.62, 1.0, 0.27, 1),
            (0.0, 1.05, 0.22, 1),
            (-0.85, 0.78, 0.36, 1), (0.85, 0.78, 0.36, -1),     # front, wide
            (-0.38, 0.82, 0.34, 1), (0.38, 0.82, 0.34, -1)]
    for da, ls, ws, side in spec:
        ang = -math.pi / 2 + da * open_
        bend = -0.06 * (1 if da > 0 else -1) if abs(da) > 0.5 else 0.0
        o, lines, tone, cross, ctone = _petal(cx, cy, ang, s * ls, s * ws, side, pitch, bend)
        out.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % _pl(o, True))
        out.append(_rule(lines, tone, pitch, step=5.0))
        out.append(_rule(cross, ctone, pitch, step=4.0))
    # receptacle cup
    out.append('<path d="M%s %sq%s %s %s 0" %s stroke-width="1"/>' % (
        _f(cx - s * 0.32), _f(cy - s * 0.04), _f(s * 0.32), _f(s * 0.22), _f(s * 0.64), ST))
    return ''.join(out)


def _bud(bx, by, s, lean, pitch=1.5):
    out = []
    for da, w, side in ((-0.12, 0.26, -1), (0.12, 0.26, 1), (0.0, 0.2, 1)):
        o, lines, tone, cross, ctone = _petal(bx, by, -math.pi / 2 + lean + da, s, s * w, side, pitch)
        out.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % _pl(o, True))
        out.append(_rule(lines, tone, pitch, step=5.0))
        out.append(_rule(cross, ctone, pitch, step=4.0))
    return ''.join(out)


def _stem(x0, y0, x1, y1, curve):
    mx, my = (x0 + x1) / 2 + curve, (y0 + y1) / 2
    pts = []
    for i in range(13):
        t = i / 12.0
        pts.append(((1 - t) ** 2 * x0 + 2 * t * (1 - t) * mx + t * t * x1,
                    (1 - t) ** 2 * y0 + 2 * t * (1 - t) * my + t * t * y1))
    ws = [1.5 - 0.5 * i / 12 for i in range(13)]
    return '<path fill="#000" d="%s"/>' % swell_d(pts, ws, 1)


def _pad(cx, cy, rx, ry, rot, rng, pitch=1.5):
    """Lily pad in perspective: notched ellipse, radial veins, shading arcs on the far side."""
    notch = rng.uniform(-0.6, 0.6) + (math.pi / 2 if rng.random() < 0.5 else -math.pi / 2)
    pts = []
    for i in range(25):
        a = notch + 0.18 + (2 * math.pi - 0.36) * i / 24
        rr = 1 + 0.03 * math.sin(a * 5 + rot)
        pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
    pts.append((cx, cy))
    o = ['<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % _pl(pts, True)]
    lines = []
    for k in range(1, int(rx / 2.5)):
        f = k / (rx / 2.5)
        lines.append([(cx + rx * f * math.cos(notch + 0.25 + (2 * math.pi - 0.5) * i / 18),
                       cy + ry * f * math.sin(notch + 0.25 + (2 * math.pi - 0.5) * i / 18))
                      for i in range(19)])

    def tone(x, y):
        return _clamp(0.18 + 0.55 * _clamp((cy - y) / ry + 0.2) + 0.15 * ((x - cx) / rx))
    o.append(_rule(lines, tone, pitch, gain=0.6, step=7.0))
    veins = []
    for i in range(9):
        a = notch + 0.4 + (2 * math.pi - 0.8) * i / 8
        veins.append(_pl([(cx, cy), (cx + rx * 0.9 * math.cos(a), cy + ry * 0.9 * math.sin(a))]))
    o.append('<path d="%s" %s stroke="#fff" stroke-width="0.5"/>' % (''.join(veins), ST))
    o.append('<path d="%s" %s stroke-width="1"/>' % (_pl(pts[:25]), ST))
    return ''.join(o)


def _spray(x, y, s, flip, rng):
    """A kranok spray: flames fanning upward from a scrolled base (the plate's open edge)."""
    sg = -1 if flip else 1
    spec = []
    # scrolled tendril curling in
    pts = []
    for i in range(30):
        t = i / 29.0
        a = math.pi * 0.9 + t * math.pi * 1.7
        r = s * 0.5 * (1 - 0.75 * t)
        pts.append((x + sg * (s * 0.35 + r * math.cos(a)), y - s * 0.3 + r * math.sin(a) * 0.8))
    tend = '<path fill="#000" d="%s"/>' % swell_d(pts, [0.5 + 0.5 * math.sin(math.pi * i / 29) for i in range(30)], 1)
    for i, (da, sc) in enumerate(((-0.25, 1.0), (0.35, 0.8), (-0.75, 0.6))):
        ang = -math.pi / 2 + sg * da
        spec.append((x + sg * s * 0.1 * i, y - s * 0.05 * i, ang, s * sc, not flip if i % 2 else flip))
    return tend + _flames(spec)


def _ogee(W, H, top, spring, m):
    """Left half of an ogee arch from springing line to the pointed apex."""
    pts = []
    for i in range(41):
        t = i / 40.0
        f = 0.62 * math.sin(min(t / 0.62, 1) * math.pi / 2) + 0.38 * (max(0, t - 0.62) / 0.38) ** 2.3
        x = m + (W / 2 - m) * t
        pts.append((x, spring - (spring - top) * f))
    return pts


def lotus(width, height, seed=0):
    W, H = float(width), float(height)
    pid = 'pt%s' % seed
    rng = random.Random('lotus%s' % seed)
    body = []
    tall = H >= 230
    yw = H * (0.58 if H < 150 else 0.66)                     # water line
    arch = None
    if tall:
        m = W * 0.11
        spring, top = H * 0.62, H * 0.04
        L = _ogee(W, H, top, spring, m)
        arch = L + [(W - x, y) for x, y in L[::-1]]

    def in_arch(x, y):
        if not arch or y > H * 0.62:
            return True
        i = min(40, max(0, int(round((min(x, W - x) - arch[0][0]) / (W / 2 - arch[0][0]) * 40))))
        return min(x, W - x) >= arch[0][0] and y >= arch[i][1]

    # night sky: ruled hairlines, thinning into paper at the vignette; open around the moon
    mx, my, mr = W * 0.73, max(10, H * 0.16), max(5, min(H * 0.07, 18))
    if tall:
        mx, my = W * 0.69, H * 0.44

    def sky(x, y):
        if not in_arch(x, y):
            return 0
        d = math.hypot(x - mx, y - my)
        halo = _clamp((d - mr * 1.6) / (mr * 2.5))
        return (0.23 + 0.1 * (1 - y / yw)) * halo * _vig(W, H, x, y)
    body.append(_rule(_hlines(0, W, 2, yw - 1, 2.5, rng, 0, 90, 4), sky, 2.5, step=16.0, wmax=0.5))
    body.append(_moon(mx, my, mr, 0.2))
    # stars: tiny four-point cuts
    st = []
    for i in range(min(40, int(W * H / 2500))):
        x, y = rng.uniform(W * 0.15, W * 0.85), rng.uniform(4, yw * 0.8)
        if in_arch(x, y) and math.hypot(x - mx, y - my) > mr * 2.5 and _vig(W, H, x, y) > 0.5:
            r = rng.choice((1.5, 2.0, 2.5))
            st.append('M%s %sh%sM%s %sv%s' % (_f(x - r), _f(y), _f(2 * r), _f(x), _f(y - r), _f(2 * r)))
    body.append('<path d="%s" %s stroke="#fff" stroke-width="1.5"/>' % (''.join(st), ST))
    body.append('<path d="%s" %s stroke-width="0.5"/>' % (''.join(st), ST))

    # water: wavy ruled lines, denser toward the foreground, broken under the blooms (reflections)
    s = min(H * (0.28 if tall else 0.4), W * 0.13)
    blooms = [(W * 0.5, yw - s * 0.35, s), (W * 0.29, yw - s * 0.06, s * 0.8)]
    if W > 300:
        blooms.append((W * 0.71, yw - s * 0.06, s * 0.8))

    wp = 2.5 if tall else 2.0

    def water(x, y):
        d = (y - yw) / (H - yw)
        t = 0.28 + 0.3 * d
        for bx, by, bs in blooms:
            if abs(x - bx) < bs * 0.5:
                t *= 0.35 + 0.65 * (abs(x - bx) / (bs * 0.5)) ** 2
        if abs(x - mx) < mr and not tall:
            t *= 0.3
        return t * _vig(W, H, x, y)
    body.append(_rule(_hlines(0, W, yw, H - 1, wp, rng, 0, 26, 4), water, wp, step=16.0, wmax=0.5))

    # lily pads, back to front
    pads = []
    n = max(4, int(W / 85))
    for i in range(n):
        x = W * (0.12 + 0.76 * (i + rng.uniform(-0.3, 0.3)) / (n - 1))
        y = yw + (H - yw) * rng.uniform(0.2, 0.75)
        if any(abs(x - bx) < bs * 0.25 for bx, by, bs in blooms[:1]):
            y = max(y, yw + (H - yw) * 0.55)
        rx = min(W * 0.07, (H - yw) * 0.55) * (0.6 + 0.5 * (y - yw) / (H - yw))
        pads.append((y, x, rx))
    pads.sort()
    for y, x, rx in pads:
        if _vig(W, H, x, y) > 0.35:
            body.append(_pad(x, y, rx, rx * 0.3, rng.random(), rng))

    # buds on tall stems
    buds = [(W * 0.39, yw - s * 0.95, s * 0.42, -0.15), (W * 0.61, yw - s * 0.8, s * 0.36, 0.2)]
    for bx, by, bs, lean in buds:
        if by - bs < 3:
            by = 3 + bs
        body.append(_stem(bx + rng.uniform(-3, 3), yw + 4, bx, by, rng.uniform(-6, 6)))
        body.append(_bud(bx, by, bs, lean, 2.0))
    # blooms
    # the two side blooms are one engraved die struck twice (<use> with x/y, no transforms)
    side = pid + 'b'
    defs = '<defs><g id="%s">%s</g></defs>' % (side, _bloom(0, 0, blooms[1][2], rng, pitch=2.0, open_=0.9))
    body.append(defs)
    for k, (bx, by, bs) in enumerate(blooms):
        body.append(_stem(bx + 2, yw + 3, bx, by + bs * 0.05, 4 - 8 * k))
        if k == 0:
            body.append(_bloom(bx, by, bs, rng, pitch=1.5))
        else:
            body.append('<use xlink:href="#%s" href="#%s" x="%s" y="%s"/>' % (side, side, _f(bx), _f(by)))
    # ripples at the stems
    rp = []
    for bx, by, bs in blooms:
        for r in (bs * 0.25, bs * 0.4):
            rp.append('M%s %sa%s %s 0 0 0 %s 0' % (_f(bx - r), _f(yw + 4), _f(r), _f(r * 0.22), _f(2 * r)))
    body.append('<path d="%s" %s stroke-width="0.5" stroke-dasharray="4 2"/>' % (''.join(rp), ST))

    # the kranok frame is the edge: sprays at the lower corners, an ogee arch at tall sizes
    fs = min(H * 0.55, W * 0.12) if not tall else W * 0.1
    body.append(_spray(W * 0.03 + fs * 0.25, H - 2, fs, False, rng))
    body.append(_spray(W * 0.97 - fs * 0.25, H - 2, fs, True, rng))
    if tall:
        Lp = _ogee(W, H, top, spring, m)
        band = Lp + [(W - x, y) for x, y in Lp[::-1]]
        # a scalloped halo of ruled hatching hugs the arch (one <pattern>, unrotated, 2 px pitch),
        # its outer edge breaking into flame-scallops so the frame opens into the paper
        hp = pid + 'h'
        halo = []
        n = len(band)
        for i, (x, y) in enumerate(band):
            j0, j1 = max(0, i - 1), min(n - 1, i + 1)
            tx, ty = band[j1][0] - band[j0][0], band[j1][1] - band[j0][1]
            L = math.hypot(tx, ty) or 1
            nx, ny = ty / L, -tx / L
            if x > W / 2:
                nx, ny = ty / L, -tx / L
            off = W * (0.035 + 0.025 * abs(math.sin(i * 0.55)))
            halo.append((x + nx * off, max(1.5, y + ny * off)))
        body.append('<defs><pattern id="%s" width="2" height="4" patternUnits="userSpaceOnUse">'
                    '<path d="M0.75 0V4" stroke="#000" stroke-width="0.5"/></pattern></defs>' % hp)
        body.append('<path d="%s" fill="url(#%s)"/>' % (_pl(halo + band[::-1], True), hp))
        body.append('<path d="%s" %s stroke-width="1"/>' % (_pl(band), ST))
        inner = [(x + (3 if x < W / 2 else -3), y + 3) for x, y in band]
        body.append('<path d="%s" %s stroke-width="0.5"/>' % (_pl(inner), ST))
        # descending legs of the arch, breaking into the water
        legs = []
        for x in (m, W - m):
            for dx in (0, 3 if x < W / 2 else -3):
                legs.append('M%s %sV%s' % (_f(x + dx), _f(spring), _f(H * 0.92)))
        body.append('<path d="%s" %s stroke-width="0.5" stroke-dasharray="40 2 20 3 10 4 6 5 3 6"/>' % (''.join(legs), ST))
        # flames along the arch, pointing outward, sizes shrinking toward the apex
        spec = []
        for i in range(3, 38, 7):
            x, y = Lp[i]
            x2, y2 = Lp[i + 1]
            tang = math.atan2(y2 - y, x2 - x)
            sz = W * 0.06 * (1 - i / 60.0)
            spec.append((x, y - 1, tang - 0.9, sz, False))
            spec.append((W - x, y - 1, math.pi - tang + 0.9, sz, True))
        ax, ay = W / 2, top + 1
        spec.append((ax, ay + 2, -math.pi / 2, W * 0.07, False))
        body.append(_flames(spec))
    return _svg(W, H, ''.join(body))


# ====================================================================== bridge

def _moon(cx, cy, r, phase):
    """Engraved moon: the night side ruled in hairlines at 1.5 px (crossed near the limb), the
    lit side left as paper with a few dotted maria. Lit on the right while waxing. No clip paths:
    each rule's dark span is solved for directly."""
    phase %= 1.0
    k = math.cos(2 * math.pi * phase)
    wax = phase < 0.5
    out = ['<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % (_f(cx), _f(cy), _f(r))]
    d, d2 = [], []
    y = -r + 0.75
    while y < r:
        h = math.sqrt(max(0.0, r * r - y * y))
        if wax:
            x0, x1 = cx - h, cx + k * h
        else:
            x0, x1 = cx - k * h, cx + h
        if x1 - x0 > 0.8:
            d.append('M%s %sH%s' % (_f(x0 + 0.3), _f(cy + y), _f(x1)))
        y += 1.5
    # cross rules hugging the dark limb for depth
    for i in range(int(2 * r / 1.5)):
        x = cx - r + 0.75 + i * 1.5
        h = math.sqrt(max(0.0, r * r - (x - cx) ** 2))
        if (wax and x < cx - r * 0.45) or (not wax and x > cx + r * 0.45):
            if abs(k) > -2 and ((wax and x < cx + k * h) or (not wax and x > cx - k * h)):
                d2.append('M%s %sV%s' % (_f(x), _f(cy - h * 0.92), _f(cy + h * 0.92)))
    out.append('<path d="%s%s" %s stroke-width="0.5"/>' % (''.join(d), ''.join(d2), ST))
    mar = []
    for ox, oy, rr in ((0.3, -0.3, 0.2), (0.05, 0.15, 0.16), (0.35, 0.35, 0.12)):
        mx = cx + (ox if wax else -ox) * r
        if (wax and mx > cx + k * r) or (not wax and mx < cx - k * r):
            mar.append('M%s %sa%s %s 0 1 0 0.1 0' % (_f(mx - rr * r), _f(cy + oy * r), _f(rr * r), _f(rr * r * 0.8)))
    if mar:
        out.append('<path d="%s" %s stroke-width="0.5" stroke-dasharray="1 1.5"/>' % (''.join(mar), ST))
    return ''.join(out)



def _moon_dark(cx, cy, r, phase):
    """Path of the unlit part of the disc (lit on the right while waxing)."""
    phase %= 1.0
    k = math.cos(2 * math.pi * phase)
    wax = phase < 0.5
    sg = 1 if wax else -1
    pts = []
    for i in range(25):     # limb on the dark side, top to bottom
        a = -math.pi / 2 + math.pi * i / 24
        pts.append((cx - sg * r * math.cos(a), cy + r * math.sin(a)))
    for i in range(25):     # terminator back up
        yy = r - 2 * r * i / 24
        pts.append((cx + sg * k * r * math.sqrt(max(0, 1 - (yy / r) ** 2)), cy + yy))
    return _pl(pts, True)


def _fir(x, base, h, rng, tone=0.8):
    """A Douglas fir: drooping branch cuts, heavy (1 px) near the trunk and in the lower tiers,
    lifting to hairlines at the tips and the crown."""
    heavy, light = [], []
    n = int(h / 2.5)
    for i in range(n):
        t = i / float(n)
        y = base - h * t
        hw = h * 0.24 * (1 - t) ** 1.05 * rng.uniform(0.8, 1.1) + 0.8
        for sg in (-1, 1):
            mid = 'M%s %sq%s %s %s %s' % (_f(x), _f(y), _f(sg * hw * 0.5), _f(0), _f(sg * hw * 0.55), _f(hw * 0.12))
            tip = 'M%s %sq%s %s %s %s' % (_f(x + sg * hw * 0.5), _f(y + hw * 0.1), _f(sg * hw * 0.3),
                                          _f(hw * 0.05), _f(sg * hw * 0.5), _f(hw * 0.3))
            (heavy if (t < 0.7 and tone > 0.6) else light).append(mid)
            light.append(tip)
    out = '<path d="%s" %s stroke-width="1"/>' % (''.join(heavy), ST) if heavy else ''
    out += '<path d="%s M%s %sV%s" %s stroke-width="0.5"/>' % (''.join(light), _f(x), _f(base + 2), _f(base - h), ST)
    return out


def _gothic(x0, x1, ybot, yspring):
    """Pointed (equilateral-ish) arch opening as a closed path."""
    w = x1 - x0
    hh = w * 0.85
    return ('M%s %sL%s %sQ%s %s %s %sQ%s %s %s %sL%s %sz' % (
        _f(x0), _f(ybot), _f(x0), _f(yspring), _f(x0), _f(yspring - hh * 0.6), _f((x0 + x1) / 2),
        _f(yspring - hh), _f(x1), _f(yspring - hh * 0.6), _f(x1), _f(yspring), _f(x1), _f(ybot)))


def bridge(width, height, seed=0, moon_phase=None):
    W, H = float(width), float(height)
    pid = 'pb%s' % seed
    rng = random.Random('bridge%s' % seed)
    phase = 0.32 if moon_phase is None else moon_phase
    body = []
    short = H < 150
    yr = H * (0.76 if short else 0.8)       # river surface
    yd = H * (0.5 if short else 0.62)       # deck
    ytop = max(4, H * (0.06 if short else 0.24))
    t1, t2 = W * 0.3, W * 0.66
    tw = max(9, min(H * 0.075, 22))
    mr = max(7, min(H * 0.085, 26))
    # the moon hangs in the main span, framed by the towers and the cable's sag
    mx, my = (t1 + t2) / 2 + (t2 - t1) * 0.2, ytop + mr + 3
    if not short:
        my = H * 0.4

    fogs = [(yr - H * 0.05, H * 0.035), (yd + H * 0.07, H * 0.03), (ytop + H * 0.22, H * 0.025)]

    def fog(y):
        f = 0
        for fy, fh in fogs:
            f = max(f, math.exp(-((y - fy) / fh) ** 2))
        return f

    def sky(x, y):
        d = math.hypot(x - mx, y - my)
        halo = _clamp((d - mr * 1.5) / (mr * 3))
        return (0.23 + 0.08 * (1 - y / yr)) * halo * (1 - 0.85 * fog(y)) * _vig(W, H, x, y)
    body.append(_rule(_hlines(0, W, 2, yr, 2.5, rng, 0, 70, 4), sky, 2.5, step=16.0, wmax=0.5))

    body.append(_moon(mx, my, mr, phase))

    # west hills (Forest Park) behind, a soft contour hatch dissolving into fog
    hill = lambda x: yd - H * 0.1 - H * 0.06 * math.sin(x / W * 3.1 + 0.4) - H * 0.03 * math.sin(x / W * 9)
    hl = []
    for k in range(0, int(H * 0.25 / 2)):
        hl.append([(x, hill(x) + k * 2.0) for x in range(0, int(W) + 1, 3)])
    body.append(_rule(hl, lambda x, y: 0 if math.hypot(x - mx, y - my) < mr + 1.5 else 0.42 * (1 - fog(y)) * _vig(W, H, x, y) * _clamp((yr - y) / (H * 0.1)), 2.0))

    # cables (parabolic main span, side spans to the anchorages)
    def cable(x):
        if x < t1:
            u = (t1 - x) / t1
            return ytop + tw * 1.1 + (yd - 2 - ytop - tw * 1.1) * (u ** 1.2)
        if x > t2:
            u = (x - t2) / (W - t2)
            return ytop + tw * 1.1 + (yd - 2 - ytop - tw * 1.1) * (u ** 1.2)
        u = (x - (t1 + t2) / 2) / ((t2 - t1) / 2)
        return yd - 3 - (yd - 3 - ytop - tw * 1.1) * u * u
    sus = []
    x = 4.0
    while x < W - 4:
        if abs(x - t1) > tw * 0.7 and abs(x - t2) > tw * 0.7 and _vig(W, H, x, yd) > 0.25:
            sus.append('M%s %sV%s' % (_f(x), _f(cable(x)), _f(yd)))
        x += 7.5
    body.append('<path d="%s" %s stroke-width="0.5"/>' % (''.join(sus), ST))
    cpts = [(x, cable(x)) for x in range(0, int(W) + 1, 2)]
    body.append('<path fill="#000" d="%s"/>' % swell_d(cpts, [1.5 * _vig(W, H, x, y, 0.08) for x, y in cpts], 1))
    body.append('<path d="%s" %s stroke-width="0.5"/>' % (_pl([(x, y + 1.5) for x, y in cpts if _vig(W, H, x, y, 0.08) > 0.3]), ST))

    # deck with lattice truss, thinning into fog at the ends
    td = 3.0 if short else 4.0
    dl = [[(x, yd + o) for x in range(0, int(W) + 1, 2)] for o in (0, td)]
    body.append(_rule(dl, lambda x, y: 0.55 * _vig(W, H, x, y, 0.08), 2.0))
    zz = []
    x = 2.0
    while x < W - 2:
        if _vig(W, H, x, yd, 0.08) > 0.4:
            zz.append('M%s %sl2 %s' % (_f(x), _f(yd), _f(td)))
        x += 4.0
    body.append('<path d="%s" %s stroke-width="0.5"/>' % (''.join(zz), ST))

    # towers: two legs, stacked pointed arches, spires; vertical contour hatching lit from the moon
    for tx in (t1, t2):
        lw = tw * 0.32
        xl0, xl1, xr0, xr1 = tx - tw / 2, tx - tw / 2 + lw, tx + tw / 2 - lw, tx + tw / 2
        yb = yr + 1
        legs = _pl([(xl0, yb), (xl0, ytop + tw * 0.4), (xr1, ytop + tw * 0.4), (xr1, yb), (xr0, yb),
                    (xr0, yd + td), (xl1, yd + td), (xl1, yb)], True)
        body.append('<path d="%s" fill="#fff"/>' % legs)
        vl = []
        xx = xl0 + 0.75
        while xx < xr1:
            vl.append([(xx, y) for y in range(int(ytop + tw * 0.4), int(yb) + 1, 2)])
            xx += 1.5

        def ttone(x, y, xl0=xl0, xr1=xr1):
            side = (x - xl0) / (xr1 - xl0)
            return (0.38 + 0.55 * (1 - side) ** 1.5) * (1 - 0.8 * fog(y))
        clip = '%st%d' % (pid, int(tx))
        body.append('<clipPath id="%s"><path d="%s"/></clipPath><g clip-path="url(#%s)">%s</g>' % (
            clip, legs, clip, _rule(vl, ttone, 1.5)))
        # openings: tall gothic windows above the deck and a portal arch below the cross
        ops = _gothic(xl1, xr0, yd - 1, ytop + tw * 2.1)
        h2 = (yd - ytop) * 0.18
        body.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % ops)
        body.append('<path d="%s" %s stroke-width="1"/>' % (legs, ST))
        # lancet windows on the leg faces
        win = []
        for lx0, lx1 in ((xl0, xl1), (xr0, xr1)):
            c = (lx0 + lx1) / 2
            ww = max(1.0, lw * 0.18)
            y0 = ytop + tw * 0.8
            while y0 + lw * 1.4 < yd - 2:
                win.append(_gothic(c - ww, c + ww, y0 + lw * 1.2, y0 + lw * 0.5))
                y0 += lw * 2.0
        body.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % ''.join(win))
        # spires (copper-green in life; here, cut in hairline)
        sp = []
        for lx0, lx1 in ((xl0, xl1), (xr0, xr1)):
            c = (lx0 + lx1) / 2
            sp.append('M%s %sL%s %sL%s %sz' % (_f(lx0), _f(ytop + tw * 0.4), _f(c), _f(ytop - tw * 0.55),
                                              _f(lx1), _f(ytop + tw * 0.4)))
        body.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % ''.join(sp))
        sh = []
        for lx0, lx1 in ((xl0, xl1), (xr0, xr1)):
            c = (lx0 + lx1) / 2
            for k in range(1, 4):
                f = k / 4.0
                sh.append('M%s %sL%s %s' % (_f(c), _f(ytop - tw * 0.55), _f(c - (c - lx0) * f), _f(ytop + tw * 0.4)))
        body.append('<path d="%s" %s stroke-width="0.5"/>' % (''.join(sh), ST))

    # river: ruled water, a broken moon path, tower reflections, all dissolving at the edges
    def river(x, y):
        d = (y - yr) / (H - yr)
        t = 0.28 + 0.28 * d
        if abs(x - mx) < mr * (0.6 + d):
            t *= 0.25 + 0.75 * rng.random()
        for tx in (t1, t2):
            if abs(x - tx) < tw * 0.5:
                t += 0.2 * (1 - d)
        return t * (1 - 0.8 * fog(y)) * _vig(W, H, x, y)
    body.append(_rule(_hlines(0, W, yr + 1, H - 1, 2.0, rng, 0, 30, 4), river, 2.0, step=10.0, wmax=0.5))

    # Cathedral Park: the east approach on pointed concrete arches, right bank, firs
    gx0 = t2 + tw * 0.8
    bank = lambda x: yr - (yr - yd) * 0.15 - (x - gx0) / (W - gx0) * (yr - yd) * 0.35
    bank_pts = [(x, bank(x)) for x in range(int(gx0), int(W) + 1, 3)]
    aw = max(8, tw * 0.9)
    x = gx0 + 2
    arches = []
    while x + aw < W:
        if _vig(W, H, x + aw / 2, yd, 0.06) > 0.3:
            arches.append(_gothic(x + 1.5, x + aw - 1.5, bank(x + aw / 2), yd + td + aw * 0.95))
        x += aw
    if arches:
        cl = pid + 'a'
        piers = _pl([(gx0, yd + td), (W, yd + td), (W, H), (gx0, H)], True)
        vl = [[(xx, y) for y in range(int(yd + td), int(yr) + 4, 2)] for xx in [gx0 + 1 + i * 1.5 for i in range(int((W - gx0) / 1.5))]]
        body.append('<clipPath id="%s"><path d="%s"/></clipPath><g clip-path="url(#%s)">%s</g>' % (
            cl, piers, cl, _rule(vl, lambda x, y: 0.3 * _vig(W, H, x, y, 0.06) * _clamp((bank(x) - y) / 3) * (1 - 0.6 * fog(y)), 1.5)))
        body.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.5"/>' % ''.join(arches))
    gl = [[(x, bank(x) + k * 2) for x in range(int(gx0), int(W) + 1, 3) if bank(x) + k * 2 < yr + 1] for k in range(int((yr - yd) * 0.5 / 2) + 2)]
    gl = [g for g in gl if len(g) > 1]
    body.append(_rule(gl, lambda x, y: 0.35 * _vig(W, H, x, y), 2.0))
    # firs on both banks, foreground
    fh = H * (0.42 if short else 0.36)
    for fx, sc in ((W * 0.06, 0.9), (W * 0.11, 1.15), (W * 0.15, 0.75), (W * 0.9, 1.1), (W * 0.95, 0.85)):
        base = H - 2 if fx < W / 2 else min(H - 2, bank(fx) + 4)
        body.append(_fir(fx, base, fh * sc, rng, 0.75 if 0.08 < fx / W < 0.92 else 0.5))

    # fog: broken, thinning drifts across the legs and the water; white veils under them
    for fy, fh2 in fogs[:2]:
        veil = [(x, fy - fh2 * 0.6 + 1.5 * math.sin(x / 23.0 + fy)) for x in range(0, int(W) + 1, 8)]
        veil += [(x, fy + fh2 * 0.6 + 1.5 * math.sin(x / 19.0 + fy)) for x in range(int(W), -1, -8)]
        fl = []
        y = fy - fh2 * 0.6
        while y < fy + fh2 * 0.6:
            pts, x = [], rng.uniform(0, 30)
            while x < W:
                L = rng.uniform(20, 70)
                seg = [(xx, y + 0.6 * math.sin(xx / 15.0)) for xx in range(int(x), int(min(W, x + L)), 2)]
                if len(seg) > 2:
                    fl.append(seg)
                x += L + rng.uniform(8, 40)
            y += 2.0

        def ft(x, y, fy=fy, fh2=fh2):
            return 0.5 * (1 - abs(y - fy) / (fh2 * 0.6)) * (0.5 + 0.5 * math.sin(x / 31.0 + y)) * _vig(W, H, x, y)
        body.append(_rule(fl, ft, 2.0))
    return _svg(W, H, ''.join(body))


# ====================================================================== demo

def demo(path='/tmp/claude-0/shots/plates/thai.html'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = []
    for h in (90, 200, 380):
        a, b = lotus(528, h, 1), bridge(528, h, 2, 0.32)
        rows.append('<p>lotus 528x%d (%.1f KB)</p>%s<p>bridge 528x%d (%.1f KB)</p>%s' % (
            h, len(a) / 1024.0, a, h, len(b) / 1024.0, b))
    a, b = lotus(528, 300, 3), bridge(528, 300, 4, 0.75)
    rows.append('<p>300: lotus %.1f KB, bridge %.1f KB</p>' % (len(a) / 1024.0, len(b) / 1024.0))
    html = ('<!doctype html><meta charset="utf-8"><body style="margin:0;padding:16px;background:#fff;'
            'width:560px;font:12px sans-serif">%s</body>' % ''.join(rows))
    with open(path, 'w') as fh:
        fh.write(html)
    return path


if __name__ == '__main__':
    print(demo())
