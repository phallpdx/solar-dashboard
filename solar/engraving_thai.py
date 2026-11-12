"""Thai ornament (lai thai) engraving for the black-and-white Kindle edition.

Pure black line work: outlines 0.8-1.1 px, hatching 0.5 px, black stipple
dots, no grey fills.  Every id is prefixed with the seed so several pieces can
share a page.  No Thai script is rendered, only ornament.

Public API (each returns a standalone <svg> string):
    thai_corner(size, seed, rot=0)      kranok flame corner, rot in 0/90/180/270
    pra_jam_yam(r, seed)                four-petal rosette medallion, r 8..40
    kranok_band(width, height, seed)    tiling lai-kanok frieze, height 8..24
    thai_cartouche(width, height, seed) flame-edged frame, empty center
    demo()  -> writes /tmp/claude-0/shots/team/thai_demo.html
"""
import math
import os
import random

OUT = 'stroke="#000" fill="none" stroke-linecap="round" stroke-linejoin="round"'


def _f(x):
    s = '%.1f' % x
    if s.endswith('.0'):
        s = s[:-2]
    return '0' if s == '-0' else s


def _path(pts, close=False):
    s = 'M' + ' '.join('%s %s' % (_f(x), _f(y)) for x, y in pts)
    return s + ('z' if close else '')


def _pid(seed):
    return 'th%s' % str(seed).replace(' ', '_')


def _svg(w, h, body, extra=''):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
            'viewBox="0 0 %s %s"%s>%s</svg>' % (_f(w), _f(h), _f(w), _f(h), extra, body))


def _xf(pts, x, y, ang, s, flip=False):
    c, n = math.cos(ang), math.sin(ang)
    out = []
    for px, py in pts:
        if flip:
            py = -py
        px, py = px * s, py * s
        out.append((x + px * c - py * n, y + px * n + py * c))
    return out


def _flame(curl=0.9, hatch=5, inner=True):
    """Kranok flame in unit space: base at (0,0), tip near (1, -curl*..).

    Returns (outline, inner_line, hatch_segments) as unit-space point lists.
    The spine bends upward (negative y) and the tip hooks back over itself.
    """
    n = 18
    sp = []
    for i in range(n + 1):
        t = i / n
        sp.append((t - 0.12 * t ** 4 * curl, -curl * 0.55 * t ** 2.4))
    def wid(t):
        return 0.24 * math.sin(math.pi * min(1, t * 0.92 + 0.08)) ** 0.7 * (1 - t) ** 0.55 + 0.004
    up, dn = [], []
    norms = []
    for i in range(n + 1):
        a = sp[max(0, i - 1)]
        b = sp[min(n, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        norms.append((nx, ny))
        w = wid(i / n)
        up.append((sp[i][0] - nx * w * 1.15, sp[i][1] - ny * w * 1.15))
        dn.append((sp[i][0] + nx * w * 0.85, sp[i][1] + ny * w * 0.85))
    # hooked tip: little curl back over the convex side
    tip = sp[-1]
    hook = [(tip[0] - 0.02 - 0.09 * math.sin(a), tip[1] + 0.05 - 0.07 * math.cos(a) - 0.05)
            for a in (0.2, 1.1, 2.0, 2.9)]
    outline = dn + hook[::-1][:1] + up[::-1]
    inn = []
    if inner:
        for i in range(2, n - 2):
            w = wid(i / n)
            nx, ny = norms[i]
            inn.append((sp[i][0] - nx * w * 0.55, sp[i][1] - ny * w * 0.55))
    hs = []
    for k in range(hatch):
        i = int(2 + k * (n - 6) / max(1, hatch))
        hs.append([sp[i], dn[i]])
    return outline, inn, hs


def _flame_d(x, y, ang, s, curl=0.9, hatch=5, flip=False, inner=True):
    """Return (outline_d, detail_d) path strings for one flame placed in space."""
    o, inn, hs = _flame(curl, hatch, inner)
    d1 = _path(_xf(o, x, y, ang, s, flip), True)
    parts = []
    if inn and s > 7:
        parts.append(_path(_xf(inn, x, y, ang, s, flip)))
    if s > 9:
        for seg in hs:
            parts.append(_path(_xf(seg, x, y, ang, s, flip)))
    return d1, ''.join(parts)


def _dot(x, y, r):
    return 'M%s %sm-%s 0a%s %s 0 1 0 %s 0a%s %s 0 1 0-%s 0' % (
        _f(x), _f(y), _f(r), _f(r), _f(r), _f(2 * r), _f(r), _f(r), _f(2 * r))


def _rosette_paths(cx, cy, r, rng, petals=4):
    """Outline + detail paths for a pra jam yam rosette centred at cx,cy."""
    o, d, dots = [], [], []
    k = 0.92 + rng.random() * 0.06
    for i in range(petals):
        a = -math.pi / 2 + i * 2 * math.pi / petals
        c, s = math.cos(a), math.sin(a)
        # pointed ogee petal from centre ring out to the tip
        r0, r1 = r * 0.22, r * k
        pts = []
        m = 10
        for j in range(m + 1):
            t = j / m
            w = r * 0.36 * math.sin(math.pi * t) ** 0.8 * (1 - 0.45 * t)
            pts.append((r0 + (r1 - r0) * t, w))
        side = [(cx + px * c - py * s, cy + px * s + py * c) for px, py in pts]
        other = [(cx + px * c + py * s, cy + px * s - py * c) for px, py in pts[::-1]]
        o.append(_path(side + other[1:], True))
        if r >= 14:
            ins = [(cx + px * c - py * s * 0.55, cy + px * s + py * c * 0.55) for px, py in pts[1:-2]]
            ins2 = [(cx + px * c + py * s * 0.55, cy + px * s - py * c * 0.55) for px, py in pts[-3:0:-1]]
            d.append(_path(ins + ins2))
            mr = [(cx + (r0 + 0.08 * r) * c, cy + (r0 + 0.08 * r) * s),
                  (cx + (r1 - 0.2 * r) * c, cy + (r1 - 0.2 * r) * s)]
            d.append(_path(mr))
        # small leaf between petals
        b = a + math.pi / petals
        cb, sb = math.cos(b), math.sin(b)
        lp = []
        for j in range(7):
            t = j / 6
            w = r * 0.12 * math.sin(math.pi * t)
            lp.append((r * 0.3 + r * 0.42 * t, w))
        sd = [(cx + px * cb - py * sb, cy + px * sb + py * cb) for px, py in lp]
        ot = [(cx + px * cb + py * sb, cy + px * sb - py * cb) for px, py in lp[::-1]]
        o.append(_path(sd + ot[1:], True))
        dots.append(_dot(cx + r * 0.86 * cb, cy + r * 0.86 * sb, max(0.6, r * 0.045)))
    cr = r * 0.2
    o.append(_dot(cx, cy, cr))
    dots.append(_dot(cx, cy, max(0.7, r * 0.07)))
    if r >= 12:
        # stippled ring just inside the centre circle
        nst = 8
        for i in range(nst):
            a = i * 2 * math.pi / nst
            dots.append(_dot(cx + cr * 0.6 * math.cos(a), cy + cr * 0.6 * math.sin(a), 0.45))
    return ''.join(o), ''.join(d), ''.join(dots)


# ---------------------------------------------------------------- rosette
def pra_jam_yam(r, seed):
    r = max(8, min(40, r))
    rng = random.Random('pjy%s' % seed)
    p = _pid(seed)
    pad = 1.5
    S = 2 * (r + pad)
    c = r + pad
    sw = 0.8 if r < 16 else 1.0
    o, d, dots = _rosette_paths(c, c, r * 0.8, rng)
    body = ['<g id="%s-pjy">' % p]
    body.append('<circle cx="%s" cy="%s" r="%s" %s stroke-width="%s"/>' % (_f(c), _f(c), _f(r), OUT, sw))
    if r >= 14:
        body.append('<circle cx="%s" cy="%s" r="%s" %s stroke-width="0.5"/>' % (
            _f(c), _f(c), _f(r - 2.2), OUT))
        # beaded ring between the two circles
        nb = int(r * 1.1)
        bd = ''.join(_dot(c + (r - 1.1) * math.cos(2 * math.pi * i / nb),
                          c + (r - 1.1) * math.sin(2 * math.pi * i / nb), 0.45) for i in range(nb))
        body.append('<path d="%s" fill="#000"/>' % bd)
    body.append('<path d="%s" %s stroke-width="%s"/>' % (o, OUT, sw))
    if d:
        body.append('<path d="%s" %s stroke-width="0.5"/>' % (d, OUT))
    body.append('<path d="%s" fill="#000"/>' % dots)
    body.append('</g>')
    return _svg(S, S, ''.join(body))


# ---------------------------------------------------------------- corner
def thai_corner(size, seed, rot=0):
    S = max(60, min(90, size))
    rng = random.Random('cor%s' % seed)
    p = _pid(seed)
    rot = int(rot) % 360
    m = 3.0                       # margin
    outs, dets = [], []
    # double rule along the top and left edge (the frame arms)
    rules = [_path([(m, S - 2), (m, m), (S - 2, m)]),
             _path([(m + 4, S - 2), (m + 4, m + 4), (S - 2, m + 4)])]
    # main flame from the corner pointing diagonally inward
    big = S * 0.52
    o, dd = _flame_d(m + 6, m + 6, math.pi / 4 + 0.25, big, curl=1.0, hatch=6)
    outs.append(o); dets.append(dd)
    o, dd = _flame_d(m + 6, m + 6, math.pi / 4 - 0.25, big * 0.82, curl=1.0, hatch=5, flip=True)
    outs.append(o); dets.append(dd)
    # sprouting flames along each arm, shrinking toward the ends
    n = 3
    for i in range(n):
        t = i / n
        sz = S * (0.28 - 0.06 * i) * (0.95 + 0.1 * rng.random())
        pos = m + 4 + S * (0.32 + 0.2 * i)
        o, dd = _flame_d(pos, m + 5.5, 0.75, sz, curl=1.1, hatch=3)
        outs.append(o); dets.append(dd)
        o, dd = _flame_d(m + 5.5, pos, math.pi / 2 - 0.75, sz, curl=1.1, hatch=3, flip=True)
        outs.append(o); dets.append(dd)
    o2, d2, dots = _rosette_paths(m + 2, m + 2, 5.2, rng)
    body = ['<g id="%s-corner" transform="rotate(%d %s %s)">' % (p, rot, _f(S / 2), _f(S / 2))]
    body.append('<path d="%s" %s stroke-width="1.1"/>' % (''.join(rules), OUT))
    body.append('<path d="%s" stroke="#000" fill="#fff" stroke-width="0.9" stroke-linejoin="round"/>' % ''.join(outs))
    body.append('<path d="%s" %s stroke-width="0.5"/>' % (''.join(dets), OUT))
    body.append('<circle cx="%s" cy="%s" r="6.2" fill="#fff" stroke="#000" stroke-width="0.9"/>' % (_f(m + 2), _f(m + 2)))
    body.append('<path d="%s" %s stroke-width="0.6"/>' % (o2, OUT))
    body.append('<path d="%s" fill="#000"/>' % dots)
    body.append('</g>')
    return _svg(S, S, ''.join(body), ' overflow="hidden"')


# ---------------------------------------------------------------- band
def kranok_band(width, height, seed):
    H = max(8, min(24, height))
    W = max(H, width)
    p = _pid(seed)
    rng = random.Random('band%s' % seed)
    P = round(H * 1.0, 1)        # pattern period
    rule = 1.2 if H >= 14 else 0.9
    inner_top, inner_bot = rule + 1.2, H - rule - 1.2
    zone = inner_bot - inner_top
    curl = 0.9 + rng.random() * 0.25
    # one leaning flame per period rising from the bottom rule, plus a seed bud
    o, dd = _flame_d(P * 0.12, inner_bot, -0.62, zone * 1.4, curl=curl,
                     hatch=4 if H >= 14 else 0, inner=H >= 14)
    tile = ['<path d="%s" stroke="#000" fill="none" stroke-width="%s" stroke-linejoin="round"/>' % (
        o, '0.8' if H >= 12 else '0.6')]
    if dd and H >= 14:
        tile.append('<path d="%s" %s stroke-width="0.5"/>' % (dd, OUT))
    tile.append('<path d="%s" fill="#000"/>' % _dot(P * 0.86, inner_top + zone * 0.2, max(0.5, H * 0.04)))
    pat = ('<pattern id="%s-kb" patternUnits="userSpaceOnUse" x="0" y="0" width="%s" height="%s">'
           '%s</pattern>' % (p, _f(P), _f(H), ''.join(tile)))
    body = ['<defs>%s</defs>' % pat,
            '<rect x="0" y="0" width="%s" height="%s" fill="url(#%s-kb)"/>' % (_f(W), _f(H), p),
            '<path d="M0 %s H%s M0 %s H%s" stroke="#000" stroke-width="%s"/>' % (
                _f(rule / 2), _f(W), _f(H - rule / 2), _f(W), rule)]
    if H >= 16:
        body.append('<path d="M0 %s H%s M0 %s H%s" stroke="#000" stroke-width="0.5"/>' % (
            _f(rule + 0.9), _f(W), _f(H - rule - 0.9), _f(W)))
    return _svg(W, H, ''.join(body))


# ---------------------------------------------------------------- cartouche
def thai_cartouche(width, height, seed):
    W, H = max(80, width), max(40, height)
    p = _pid(seed)
    rng = random.Random('cart%s' % seed)
    fs = min(15.0, max(9.0, min(W, H) * 0.17))     # flame size along edge
    pad = fs * 1.0
    x0, y0, x1, y1 = pad, pad, W - pad, H - pad
    # ogee-pointed ends: rectangle whose short sides are pointed arches
    a = min(H * 0.22, (y1 - y0) / 2 * 0.7)

    def frame(o):
        xa, xb, ya, yb = x0 + o, x1 - o, y0 + o, y1 - o
        ym = (ya + yb) / 2
        return ('M%s %s H%s Q%s %s %s %s Q%s %s %s %s H%s Q%s %s %s %s Q%s %s %s %sz' % (
            _f(xa + a), _f(ya), _f(xb - a), _f(xb), _f(ya), _f(xb + a * 0.15), _f(ym),
            _f(xb), _f(yb), _f(xb - a), _f(yb), _f(xa + a), _f(xa), _f(yb),
            _f(xa - a * 0.15), _f(ym), _f(xa), _f(ya), _f(xa + a), _f(ya)))
    # flame unit in defs, stamped with <use> around the outside edge
    o, dd = _flame_d(0, 0, -math.pi / 2 + 0.55, fs, curl=1.0, hatch=0, inner=False)
    defs = ('<defs><g id="%s-cf"><path d="%s" stroke="#000" fill="#fff" stroke-width="0.7" '
            'stroke-linejoin="round"/></g></defs>' % (p, o))
    uses = []
    step = fs * 0.95
    xa, xb = x0 + a, x1 - a
    n = max(1, int((xb - xa) / step))
    st = (xb - xa) / n
    for i in range(n + 1):
        x = xa + i * st
        uses.append('<use href="#%s-cf" x="%s" y="%s"/>' % (p, _f(x), _f(y0 + 0.5)))
    # end flames radiate from the pointed tips
    ym = (y0 + y1) / 2
    ends = []
    for side in (1,):
        tx = (x0 - a * 0.15 * 0.5) if side < 0 else (x1 + a * 0.15 * 0.5)
        for k, ang in enumerate((-0.9, -0.45, 0, 0.45, 0.9)):
            base = math.pi if side < 0 else 0
            aa = base + ang * (-side)
            sz = fs * (1.25 if k == 2 else 1.0)
            fx = tx - side * 1.5 + (abs(ang) * 3 * (-side))
            fy = ym + math.sin(ang) * (y1 - y0) * 0.35
            o2, d2 = _flame_d(fx, fy, aa, sz, curl=0.9, hatch=0, inner=False,
                              flip=(ang > 0) != (side < 0))
            ends.append(o2)
    # top edge + right end drawn once, bottom + left are the same half
    # rotated 180 degrees about the centre (the frame is point-symmetric)
    half = ('<g id="%s-ch">%s<path d="%s" stroke="#000" fill="#fff" stroke-width="0.7" '
            'stroke-linejoin="round"/></g>' % (p, ''.join(uses), ''.join(ends)))
    body = [defs, '<g id="%s-cart">' % p, half,
            '<use href="#%s-ch" transform="rotate(180 %s %s)"/>' % (p, _f(W / 2), _f(H / 2))]
    body.append('<path d="%s" stroke="#000" fill="#fff" stroke-width="1.1"/>' % frame(0))
    body.append('<path d="%s" %s stroke-width="0.5"/>' % (frame(2.2), OUT))
    # small rosettes at the two pointed ends, inside the frame
    rr = min(6.0, (y1 - y0) * 0.14)
    if rr >= 3.5:
        for cx in (x0 + rr + 3.5, x1 - rr - 3.5):
            oo, ddd, dots = _rosette_paths(cx, ym, rr, rng)
            body.append('<path d="%s" %s stroke-width="0.6"/><path d="%s" fill="#000"/>' % (oo, OUT, dots))
    body.append('</g>')
    return _svg(W, H, ''.join(body))


# ---------------------------------------------------------------- demo
def demo():
    d = '/tmp/claude-0/shots/team'
    os.makedirs(d, exist_ok=True)
    cell = '<div style="display:inline-block;vertical-align:middle;margin:4px">%s</div>'
    rows = []
    rows.append('<div>' + ''.join(cell % thai_corner(72, 'c%d' % r, r) for r in (0, 90, 180, 270))
                + cell % thai_corner(60, 'c60') + cell % thai_corner(90, 'c90') + '</div>')
    rows.append('<div>' + ''.join(cell % pra_jam_yam(r, 'r%d' % r) for r in (8, 12, 18, 26, 40)) + '</div>')
    for h in (8, 12, 16, 24):
        rows.append('<div style="margin:5px 4px">%s</div>' % kranok_band(600, h, 'b%d' % h))
    cart = thai_cartouche(380, 90, 'k1')
    rows.append('<div style="position:relative;width:380px;margin:6px auto">%s'
                '<div style="position:absolute;inset:0;display:flex;align-items:center;'
                'justify-content:center;font:bold 20px Georgia,serif">Evening Edition</div></div>' % cart)
    rows.append('<div>' + cell % thai_cartouche(220, 60, 'k2') + cell % thai_cartouche(160, 48, 'k3') + '</div>')
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>Thai ornament</title></head>'
            '<body style="margin:0;padding:4px 0;background:#fff;width:618px">%s</body></html>' % ''.join(rows))
    path = os.path.join(d, 'thai_demo.html')
    with open(path, 'w') as fh:
        fh.write(html)
    return path


if __name__ == '__main__':
    print(demo())
