"""Procedural engraved scrollwork (English/Germanic scroll, acanthus, Thai kanok)
as compact SVG fragments for the black-and-white Kindle edition.

Design: one half-wave "unit" of running vine (stem, log-spiral C-scroll on the
concave side, hatched acanthus leaf on the convex side, berries) is drawn once
in <defs> in a few seeded variants and stamped along each side with <use>.
Every side is mirrored about its midpoint (where a facing pair of scrolls forms
a palmette), so all four corners, which carry an identical rosette flourish,
stay exactly symmetric whatever the seed.

Public API:
    scroll_border(width, height, seed, density='full') -> str  (<g> fragment)
    scroll_band(width, height, seed, kanok=True) -> str        (<g> fragment)
    demo()  -> writes /tmp/claude-0/shots/team/scroll_demo.html
"""
import math
import os
import random

S0 = 10.0      # half-wave length of the unit (before scale)
A = 2.2        # stem amplitude
HALF = 4.4     # half-height of the content zone


def _f(x, nd=2):
    s = ('%.' + str(nd) + 'f') % x
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    if s in ('-0', ''):
        s = '0'
    return s


def _pl(pts, nd=2, close=False):
    """Polyline as a relative path ('M x y l dx dy ...'), drift-free rounding."""
    q = 10 ** nd
    r = [(round(x * q), round(y * q)) for x, y in pts]
    out = ['M%s %s' % (_f(r[0][0] / q, nd), _f(r[0][1] / q, nd)), 'l']
    for (x0, y0), (x1, y1) in zip(r, r[1:]):
        if x1 == x0 and y1 == y0:
            continue
        out.append('%s %s' % (_f((x1 - x0) / q, nd), _f((y1 - y0) / q, nd)))
    s = out[0] + out[1] + ' '.join(out[2:]).replace(' -', '-')
    return s + ('z' if close else '')


def _dot(x, y, r, nd=2):
    return 'M%s %sm-%s 0a%s %s 0 1 0 %s 0a%s %s 0 1 0-%s 0' % (
        _f(x, nd), _f(y, nd), _f(r, nd), _f(r, nd), _f(r, nd), _f(2 * r, nd),
        _f(r, nd), _f(r, nd), _f(2 * r, nd))


def _bez(p0, p1, p2, p3, n=10):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def _norm(x, y):
    m = math.hypot(x, y) or 1.0
    return x / m, y / m


# ---------------------------------------------------------------- geometry

def _stem(sc, u0=0.0, u1=S0, n=12):
    return [((u0 + (u1 - u0) * i / n) * sc,
             A * sc * math.sin(math.pi * (u0 + (u1 - u0) * i / n) / S0))
            for i in range(n + 1)]


def _spiral(cx, cy, R, th0, turns, k=0.2, step=0.22):
    """Clockwise (v-up sense: angle decreasing) log spiral, outside-in."""
    pts = []
    th = th0
    end = th0 - turns * 2 * math.pi
    while th >= end:
        r = R * math.exp(-k * (th0 - th))
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
        th -= step * (1.0 + 0.6 * (th0 - th) / (turns * 2 * math.pi))
    return pts


def _branch_spiral(sc, us, cx, cy, R, th0, turns):
    """Tendril leaving the stem at u=us and curling into a log spiral."""
    sp = _spiral(cx * sc, cy * sc, R * sc, th0, turns)
    sx = us * sc
    sy = A * sc * math.sin(math.pi * us / S0)
    tx, ty = _norm(1.0, A * math.pi / S0 * math.cos(math.pi * us / S0))
    ex, ey = sp[0]
    dx, dy = _norm(sp[1][0] - sp[0][0], sp[1][1] - sp[0][1])
    L = math.hypot(ex - sx, ey - sy)
    # leave the stem tangentially but bend away (downward) promptly
    b = _bez((sx, sy), (sx + tx * L * 0.35, sy + ty * L * 0.22 - 0.9 * sc),
             (ex - dx * L * 0.45, ey - dy * L * 0.45), (ex, ey), 9)
    return b + sp[1:], sp[-1]


def _leaf(sc, base, tip, bulge, width, lobes, hatches, flip=1):
    """Acanthus leaf along a curved spine; lobed on the outer (+normal) side.
    Returns (outline_path_pts, [hatch_pts...])."""
    (bx, by), (tx, ty) = base, tip
    mx, my = (bx + tx) / 2, (by + ty) / 2
    nx, ny = _norm(-(ty - by), tx - bx)
    nx, ny = nx * flip, ny * flip
    cx, cy = mx + nx * bulge, my + ny * bulge   # quadratic control of spine
    n = 28

    def spine(t):
        a, b, c = (1 - t) ** 2, 2 * t * (1 - t), t * t
        x = a * bx + b * cx + c * tx
        y = a * by + b * cy + c * ty
        dx = 2 * (1 - t) * (cx - bx) + 2 * t * (tx - cx)
        dy = 2 * (1 - t) * (cy - by) + 2 * t * (ty - cy)
        ux, uy = _norm(-dy, dx)
        return x, y, ux * flip, uy * flip

    def wout(t):
        env = math.sin(math.pi * min(1.0, t * 1.08)) ** 0.75
        return width * env * (0.62 + 0.38 * abs(math.sin(lobes * math.pi * t)))

    def win(t):
        return width * 0.28 * math.sin(math.pi * t) ** 0.9

    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        x, y, ux, uy = spine(t)
        outer.append((x + ux * wout(t), y + uy * wout(t)))
        inner.append((x - ux * win(t), y - uy * win(t)))
    outline = outer + inner[::-1]
    hs = []
    for j in range(hatches):
        f = (j + 1) / (hatches + 1)
        t0, t1 = 0.12 + 0.05 * j, 0.88 - 0.08 * j
        pts = []
        for i in range(9):
            t = t0 + (t1 - t0) * i / 8
            x, y, ux, uy = spine(t)
            w = width * math.sin(math.pi * t) ** 0.75 * 0.62 * f
            pts.append((x + ux * w, y + uy * w))
        hs.append(pts)
    # midrib
    hs.append([spine(0.05 + 0.8 * i / 8)[:2] for i in range(9)])
    return outline, hs


# ------------------------------------------------------------------ units

def _unit(sc, lobes, berries, hatches, leaf=True):
    """Half-wave, crest at +v. Returns (main, hair, fill) path strings."""
    main, hair, fill = [], [], []
    main.append(_pl(_stem(sc)))
    br, eye = _branch_spiral(sc, 1.3, 5.6, -1.15, 2.25, math.pi * 0.62, 1.05)
    hair.append(_pl(br))
    fill.append(_dot(eye[0], eye[1], 0.55 * sc))
    # shading on the outer turn of the spiral (engraver's cut on the shadow side)
    sh = _spiral(5.6 * sc, -1.15 * sc, 1.85 * sc, math.pi * 1.55, 0.3)
    hair.append(_pl(sh))
    if leaf:
        bu = 2.9
        base = (bu * sc, A * sc * math.sin(math.pi * bu / S0) + 0.15 * sc)
        tip = (8.6 * sc, 2.35 * sc)
        ol, hs = _leaf(sc, base, tip, 0.9 * sc, 1.75 * sc, lobes, hatches, 1)
        hair.append(_pl(ol, close=True))
        for h in hs:
            hair.append(_pl(h))
    if berries:
        # small stalk with three berries in the trough above the zero crossing
        st = [(0.2 * sc, 0.25 * sc), (0.0, 1.4 * sc), (0.35 * sc, 2.5 * sc)]
        hair.append(_pl(st))
        for (x, y, r) in ((0.35, 3.25, 0.55), (-0.55, 2.75, 0.45), (1.2, 2.75, 0.45)):
            fill.append(_dot(x * sc, y * sc, r * sc))
    return main, hair, fill


def _mid_unit(sc, lobes, hatches):
    """Half of the central palmette: stem rises to the crest at u=S0/2 and
    a scroll faces its mirror twin under the crest."""
    main, hair, fill = [], [], []
    main.append(_pl(_stem(sc, 0, S0 / 2, 7)))
    br, eye = _branch_spiral(sc, 1.0, 2.75, -1.25, 1.95, math.pi * 0.66, 1.0)
    hair.append(_pl(br))
    fill.append(_dot(eye[0], eye[1], 0.5 * sc))
    base = (3.0 * sc, A * sc * math.sin(math.pi * 0.3) + 0.15 * sc)
    tip = (4.85 * sc, 4.1 * sc)
    ol, hs = _leaf(sc, base, tip, 0.45 * sc, 1.25 * sc, max(2, lobes - 1),
                   max(1, hatches - 1), 1)
    hair.append(_pl(ol, close=True))
    for h in hs:
        hair.append(_pl(h))
    fill.append(_dot(5.0 * sc, 2.95 * sc, 0.45 * sc))
    return main, hair, fill


def _corner(bw, sc):
    """Top-left corner flourish in the bw x bw box, symmetric about the
    diagonal. Stems arrive at (bw, bw/2) and (bw/2, bw)."""
    main, hair, fill = [], [], []
    c = bw / 2
    # rosette: eight pointed petals
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        r0, r1 = 1.15 * sc, 3.6 * sc if i % 2 else 2.9 * sc
        w = 0.42
        pts = [(c + r0 * math.cos(a - w), c + r0 * math.sin(a - w))]
        for k in range(1, 7):
            t = k / 6
            rr = r0 + (r1 - r0) * t
            aa = a - w * (1 - t) ** 0.8 * math.cos(t * 1.2)
            pts.append((c + rr * math.cos(aa), c + rr * math.sin(aa)))
        for k in range(5, -1, -1):
            t = k / 6
            rr = r0 + (r1 - r0) * t
            aa = a + w * (1 - t) ** 0.8 * math.cos(t * 1.2)
            pts.append((c + rr * math.cos(aa), c + rr * math.sin(aa)))
        hair.append(_pl(pts, close=True))
        # one hatch line down each petal
        hair.append(_pl([(c + (r0 + 0.3 * sc) * math.cos(a + 0.12),
                          c + (r0 + 0.3 * sc) * math.sin(a + 0.12)),
                         (c + (r1 - 0.9 * sc) * math.cos(a + 0.05),
                          c + (r1 - 0.9 * sc) * math.sin(a + 0.05))]))
    ring = [(c + 1.15 * sc * math.cos(i * math.pi / 8), c + 1.15 * sc * math.sin(i * math.pi / 8))
            for i in range(17)]
    main.append(_pl(ring))
    fill.append(_dot(c, c, 0.6 * sc))
    # stems coming in from the sides, ending in the ring
    main.append(_pl([(bw, c), (c + 1.15 * sc, c)]))
    main.append(_pl([(c, bw), (c, c + 1.15 * sc)]))
    return main, hair, fill


def _kanok(sc, h):
    """Thai kanok flame tip at the left end of a band; the stem arrives at
    (0,0) from +u. Flame sweeps out and its tip flicks back over itself."""
    main, hair, fill = [], [], []
    K = h * 1.9
    up = _bez((0, 0.35 * h), (-0.5 * K, 0.9 * h), (-1.05 * K, 0.55 * h), (-0.82 * K, -0.05 * h), 14)
    tipcurl = _bez((-0.82 * K, -0.05 * h), (-0.72 * K, -0.45 * h), (-0.35 * K, -0.62 * h), (-0.18 * K, -0.92 * h), 10)
    low = _bez((-0.18 * K, -0.92 * h), (-0.42 * K, -0.5 * h), (-0.62 * K, -0.12 * h), (-0.6 * K, 0.18 * h), 10)
    back = _bez((-0.6 * K, 0.18 * h), (-0.55 * K, 0.5 * h), (-0.2 * K, 0.4 * h), (0, -0.35 * h), 10)
    outline = up + tipcurl[1:] + low[1:] + back[1:]
    main.append(_pl(outline, close=True))
    # flame serrations along the upper edge
    for t in (0.3, 0.5, 0.7):
        i = int(t * 14)
        x, y = up[i]
        dx, dy = _norm(up[i + 1][0] - x, up[i + 1][1] - y)
        hair.append(_pl([(x, y), (x + (dx * 0.6 - dy * 0.9) * 0.25 * h,
                                  y + (dy * 0.6 + dx * 0.9) * 0.25 * h)]))
    # inner hatching following the flame
    for f in (0.78, 0.6):
        pts = [(-0.08 * K + (x + 0.08 * K) * f, y * f) for x, y in up[2:13]]
        hair.append(_pl(pts))
    # the eye: a small spiral
    sp = _spiral(-0.45 * K, 0.12 * h, 0.2 * h, math.pi * 0.5, 1.0)
    hair.append(_pl(sp))
    fill.append(_dot(sp[-1][0], sp[-1][1], 0.06 * h))
    return main, hair, fill


# ---------------------------------------------------------------- assembly

def _group(gid, parts, wm, wh):
    main, hair, fill = parts
    s = '<g id="%s">' % gid
    if main:
        s += '<path stroke-width="%s" d="%s"/>' % (wm, ''.join(main))
    if hair:
        s += '<path stroke-width="%s" d="%s"/>' % (wh, ''.join(hair))
    if fill:
        s += '<path fill="#000" stroke="none" d="%s"/>' % ''.join(fill)
    return s + '</g>'


def _use(ref, m):
    a, b, c, d, e, f = m
    return '<use href="#%s" transform="matrix(%s %s %s %s %s %s)"/>' % (
        ref, _f(a, 4), _f(b, 4), _f(c, 4), _f(d, 4), _f(e, 1), _f(f, 1))


def _mul(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2,
            b1 * c2 + d1 * d2, a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def _run(L, sc, rng, nvar, pfx, sigma0, sparse=False):
    """Uses (in run coords: u along 0..L, v across) for a mirrored vine of
    length L. Returns list of (ref, matrix)."""
    s_nom = S0 * sc
    k = max(0, int(round(L / 2 / s_nom - 0.5)))
    n = k + 0.5
    s = L / 2 / n
    st = s / s_nom
    out = []
    choice = [rng.randrange(nvar) for _ in range(k)]
    for j in range(k):
        sg = sigma0 * (1 if j % 2 == 0 else -1)
        ref = '%su%d' % (pfx, choice[j])
        m = (st, 0, 0, sg, j * s, 0)
        out.append((ref, m))
        out.append((ref, _mul((-1, 0, 0, 1, L, 0), m)))
    sg = sigma0 * (1 if k % 2 == 0 else -1)
    m = (st, 0, 0, sg, k * s, 0)
    out.append((pfx + 'm', m))
    out.append((pfx + 'm', _mul((-1, 0, 0, 1, L, 0), m)))
    return out


def _defs(pfx, sc, rng, density, wm, wh):
    light = density == 'light'
    nvar = 3 if light else 5
    d = ''
    for i in range(nvar):
        lobes = rng.choice((3, 4, 5))
        berries = rng.random() < (0.3 if light else 0.6)
        leaf = (not light) or i % 2 == 0
        d += _group('%su%d' % (pfx, i),
                    _unit(sc, lobes, berries, 1 if light else 2, leaf), wm, wh)
    d += _group(pfx + 'm', _mid_unit(sc, rng.choice((3, 4)), 1 if light else 2), wm, wh)
    return d, nvar


def scroll_border(width, height, seed, density='full'):
    """Rectangular engraved scroll frame (a <g> fragment) in width x height."""
    rng = random.Random(seed * 7919 + (1 if density == 'light' else 0))
    light = density == 'light'
    W, H = float(width), float(height)
    bw = 8.0 if light else 14.0
    sc = 0.58 if light else 1.0
    wm, wh = ('0.8', '0.5') if light else ('1', '0.6')
    pfx = 'es%d%s' % (seed % 100000, 'l' if light else 'f')
    defs, nvar = _defs(pfx, sc, rng, density, wm, wh)
    defs += _group(pfx + 'c', _corner(bw, sc), wm, wh)
    sigma0 = rng.choice((1, -1))
    c = bw / 2
    # side frames: run coords (u, v) -> page; v positive points inward
    sides = [
        ((1, 0, 0, 1, bw, c), W - 2 * bw),            # top
        ((1, 0, 0, -1, bw, H - c), W - 2 * bw),       # bottom
        ((0, 1, 1, 0, c, bw), H - 2 * bw),            # left
        ((0, 1, -1, 0, W - c, bw), H - 2 * bw),       # right
    ]
    uses = []
    for fr, L in sides:
        for ref, m in _run(L, sc, rng, nvar, pfx, sigma0, light):
            uses.append(_use(ref, _mul(fr, m)))
    for m in ((1, 0, 0, 1, 0, 0), (-1, 0, 0, 1, W, 0),
              (1, 0, 0, -1, 0, H), (-1, 0, 0, -1, W, H)):
        uses.append(_use(pfx + 'c', m))
    # double rules
    if light:
        rules = [(0.3, '0.8'), (bw - 0.3, '0.5')]
    else:
        rules = [(0.5, '1'), (2.0, '0.6'), (bw - 2.0, '0.6'), (bw - 0.5, '1')]
    rp = {}
    for inset, w in rules:
        rp.setdefault(w, []).append('M%s %sH%sV%sH%sz' % (
            _f(inset, 1), _f(inset, 1), _f(W - inset, 1), _f(H - inset, 1), _f(inset, 1)))
    # corner-box separators: inner rules carried across the band
    ii = rules[-1][0] if not light else bw - 0.3
    sep = ''
    for x in (ii, W - ii):
        sep += 'M%s 0V%sM%s %sV%s' % (_f(x, 1), _f(bw, 1), _f(x, 1), _f(H - bw, 1), _f(H, 1))
    for y in (ii, H - ii):
        sep += 'M0 %sH%sM%s %sH%s' % (_f(y, 1), _f(bw, 1), _f(W - bw, 1), _f(y, 1), _f(W, 1))
    rp.setdefault(wh, []).append(sep)
    rules_svg = ''.join('<path stroke-width="%s" d="%s"/>' % (w, ''.join(v))
                        for w, v in rp.items())
    return ('<g class="engr-scroll" fill="none" stroke="#000" stroke-linecap="round" '
            'stroke-linejoin="round"><defs>%s</defs>%s%s</g>'
            % (defs, rules_svg, ''.join(uses)))


def scroll_band(width, height, seed, kanok=True):
    """Horizontal engraved scroll band (<g> fragment), height ~18-28 px."""
    rng = random.Random(seed * 104729 + 3)
    W, Hh = float(width), float(height)
    rule_in = 2.6
    sc = max(0.6, (Hh - 2 * rule_in) / (2 * HALF + 0.4))
    wm, wh = '1', '0.6'
    pfx = 'eb%d' % (seed % 100000)
    defs, nvar = _defs(pfx, sc, rng, 'full', wm, wh)
    c = Hh / 2
    kw = 0.0
    if kanok:
        kh = (Hh / 2 - rule_in) * 0.95
        defs += _group(pfx + 'k', _kanok(sc, kh), wm, wh)
        kw = kh * 1.9 * 1.05 + 2
    L = W - 2 * kw
    sigma0 = rng.choice((1, -1))
    uses = []
    for ref, m in _run(L, sc, rng, nvar, pfx, sigma0):
        uses.append(_use(ref, _mul((1, 0, 0, -1, kw, c), m)))
    if kanok:
        uses.append(_use(pfx + 'k', (1, 0, 0, -1, kw, c)))
        uses.append(_use(pfx + 'k', (-1, 0, 0, -1, W - kw, c)))
    rules = ('<path stroke-width="1" d="M0 0.5H%sM0 %sH%s"/>'
             '<path stroke-width="0.6" d="M0 2H%sM0 %sH%s"/>' % (
                 _f(W, 1), _f(Hh - 0.5, 1), _f(W, 1), _f(W, 1), _f(Hh - 2, 1), _f(W, 1)))
    return ('<g class="engr-band" fill="none" stroke="#000" stroke-linecap="round" '
            'stroke-linejoin="round"><defs>%s</defs>%s%s</g>' % (defs, rules, ''.join(uses)))


def demo(seed=None):
    import datetime
    if seed is None:
        seed = datetime.date.today().toordinal()
    b = scroll_border(618 - 16, 714 - 16, seed)
    bl = scroll_border(300, 120, seed + 1, density='light')
    band = scroll_band(618 - 16 - 60, 24, seed)
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;background:#fff;width:618px;height:714px;overflow:hidden}'
            '</style></head><body><svg width="618" height="714" viewBox="0 0 618 714">'
            '<g transform="translate(8 8)">%s</g>'
            '<g transform="translate(38 120)">%s</g>'
            '<g transform="translate(159 300)">%s</g>'
            '<text x="309" y="250" font-family="Georgia,serif" font-size="22" '
            'text-anchor="middle">Goodnight</text>'
            '</svg></body></html>' % (b, band, bl))
    out = '/tmp/claude-0/shots/team/scroll_demo.html'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as fh:
        fh.write(html)
    return {'border': len(b), 'band': len(band), 'light': len(bl)}


if __name__ == '__main__':
    print(demo())
