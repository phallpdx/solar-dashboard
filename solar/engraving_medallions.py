"""Bulino-style engraved round medallions for the Kindle Evening Edition.

MEDALLIONS[key](r, seed) -> standalone <svg> string, 2r x 2r px, r in 12..40.
easter_egg(kind, seed, size) -> tiny <g> fragment (6..14 px) to hide in scrollwork.

Every motif is drawn in a 100x100 design space (centre 50,50) and scaled to
2r px.  Stroke widths and hatch spacing are given in *pixels* and converted
back into design units so lines stay crisp at r=14 on 1x e-ink.  Pure black
line work, hatching and stipple only; no grey fills.  Ids are prefixed with
key+seed.  Standard library only.
"""
import math
import os
import random


def _f(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


class _C(object):
    """Drawing context: design units are 100 across; k = design units per px."""

    def __init__(self, key, r, seed):
        self.r = max(12, min(40, r))
        self.k = 100.0 / (2 * self.r)
        self.small = self.r < 22
        self.pid = '%s%s' % (key, seed)
        self.rng = random.Random('%s-%s' % (key, seed))
        self.defs = []

    def w(self, px):
        return _f(px * self.k)

    def path(self, d, px=0.7, fill='none', extra=''):
        return ('<path d="%s" fill="%s" stroke="#000" stroke-width="%s"%s/>'
                % (d, fill, self.w(px), extra))

    def solid(self, d):
        return '<path d="%s"/>' % d

    def hatch(self, name, ang, sp_px, px=0.55):
        pid = '%s-%s' % (self.pid, name)
        sp = max(1.5, -(-sp_px * 2 // 1) / 2) * self.k  # whole device px at DPR 2
        self.defs.append(
            '<pattern id="%s" width="%s" height="%s" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(%s)"><path d="M0 %sH%s" stroke="#000" '
            'stroke-width="%s"/></pattern>'
            % (pid, _f(sp), _f(sp), _f(ang), _f(sp / 2), _f(sp), self.w(px)))
        return 'url(#%s)' % pid

    def stipple(self, name, sp_px, dot_px=0.45):
        pid = '%s-%s' % (self.pid, name)
        sp = max(1.5, -(-sp_px * 2 // 1) / 2) * self.k  # whole device px at DPR 2
        h = sp / 2
        rr = _f(dot_px * self.k)
        self.defs.append(
            '<pattern id="%s" width="%s" height="%s" patternUnits="userSpaceOnUse">'
            '<circle cx="%s" cy="%s" r="%s"/><circle cx="%s" cy="%s" r="%s"/></pattern>'
            % (pid, _f(sp), _f(sp), _f(h / 2), _f(h / 2), rr,
               _f(h * 1.5), _f(h * 1.5), rr))
        return 'url(#%s)' % pid

    def fillshape(self, d, fill):
        return '<path d="%s" fill="%s"/>' % (d, fill)


def _circ(cx, cy, r):
    return ('M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 %s 0Z'
            % (_f(cx - r), _f(cy), _f(r), _f(r), _f(2 * r), _f(r), _f(r), _f(-2 * r)))


def _ell(cx, cy, rx, ry):
    return ('M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 %s 0Z'
            % (_f(cx - rx), _f(cy), _f(rx), _f(ry), _f(2 * rx), _f(rx), _f(ry), _f(-2 * rx)))


def _star(cx, cy, ro, ri=None, n=5, rot=-90):
    ri = ri if ri is not None else ro * 0.42
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + i * 180.0 / n)
        rr = ro if i % 2 == 0 else ri
        pts.append('%s %s' % (_f(cx + rr * math.cos(a)), _f(cy + rr * math.sin(a))))
    return 'M' + 'L'.join(pts) + 'Z'


def _rim(c, roped):
    """Outer double ring with beads or rope twist between."""
    out = [c.path(_circ(50, 50, 48.6), 1.1), c.path(_circ(50, 50, 40.5), 0.8)]
    rm = 44.6
    circ_px = 2 * math.pi * rm / c.k
    if roped:
        n = max(16, int(circ_px / 2.6))
        d = []
        for i in range(n):
            a = 2 * math.pi * i / n
            a2 = a + 2 * math.pi / n * 0.9
            x1, y1 = 50 + 41.6 * math.cos(a), 50 + 41.6 * math.sin(a)
            x2, y2 = 50 + 47.6 * math.cos(a2), 50 + 47.6 * math.sin(a2)
            d.append('M%.1f %.1fl%.1f %.1f' % (x1, y1, x2 - x1, y2 - y1))
        out.append(c.path(''.join(d), 0.8))
    else:
        n = max(14, int(circ_px / 3.0))
        br = min(2.6, 0.75 * c.k)
        gap = 2 * math.pi * rm / n
        out.append('<circle cx="50" cy="50" r="%s" fill="none" stroke="#000" '
                   'stroke-width="%s" stroke-linecap="round" stroke-dasharray="0 %s"/>'
                   % (_f(rm), _f(2 * br), '%.3f' % gap))
    return ''.join(out)


# ---------------------------------------------------------------- motifs

def _stick(c, x1, y1, x2, y2, px):
    """A drumstick: thick shaft tapering to a bead tip at (x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    wb, wt = px * c.k / 2, px * c.k / 4.5
    ex, ey = x2 - ux * 3.2, y2 - uy * 3.2
    d = ('M%s %sL%s %sL%s %sL%s %sZ' % (
        _f(x1 + nx * wb), _f(y1 + ny * wb), _f(ex + nx * wt), _f(ey + ny * wt),
        _f(ex - nx * wt), _f(ey - ny * wt), _f(x1 - nx * wb), _f(y1 - ny * wb)))
    tip = _ell(0, 0, 2.2 + 0.25 * c.k, 1.5 + 0.2 * c.k)
    return (c.solid(d) + '<path transform="translate(%s %s) rotate(%s)" d="%s"/>'
            % (_f(x2 - ux * 1.2), _f(y2 - uy * 1.2), _f(math.degrees(math.atan2(dy, dx))), tip))


def _laurel(c, side, y0=78, n=None):
    """Laurel branch curving up one side from the bottom."""
    n = n or (4 if c.small else 5)
    out = []
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        a = math.radians(95 + side * (10 + 70 * t)) if side > 0 else math.radians(85 - (10 + 70 * t))
        a = math.radians(90 - side * (8 + 72 * t))
        pts.append((50 + 33 * math.cos(a), 50 + 33 * math.sin(a), a))
    d = 'M' + 'L'.join('%s %s' % (_f(x), _f(y)) for x, y, _ in pts)
    out.append(c.path(d, 0.7))
    lw, lh = (5.5, 2.2) if not c.small else (7.5, 3.2)
    for i, (x, y, a) in enumerate(pts[1:]):
        tang = math.degrees(a) + 90 * (-side)
        for s in (-1, 1):
            rot = tang + s * 35 * side
            out.append('<path transform="translate(%s %s) rotate(%s)" d="%s"/>' % (
                _f(x), _f(y), _f(rot), _ell(lw * 0.55, 0, lw * 0.6, lh * 0.5)))
    return ''.join(out)


def _snare(c):
    o = []
    cy, cb, rx, ry = 44, 66, 30, 10
    shell = ('M%s %sL%s %sA%s %s 0 0 0 %s %sL%s %sA%s %s 0 0 1 %s %sZ' % (
        _f(50 - rx), _f(cy), _f(50 - rx), _f(cb), _f(rx), _f(ry), _f(50 + rx), _f(cb),
        _f(50 + rx), _f(cy), _f(rx), _f(ry), _f(50 - rx), _f(cy)))
    o.append(c.fillshape(shell, c.hatch('sh', 90, 2.0 if c.small else 1.7)))
    o.append(c.path(shell, 1.0))
    # hoops (top/bottom bands)
    o.append(c.path('M%s %sA%s %s 0 0 0 %s %s' % (_f(50 - rx), _f(cb - 3.5), _f(rx), _f(ry),
                                                   _f(50 + rx), _f(cb - 3.5)), 0.7))
    o.append(c.path('M%s %sA%s %s 0 0 0 %s %s' % (_f(50 - rx), _f(cy + 3.5), _f(rx), _f(ry),
                                                   _f(50 + rx), _f(cy + 3.5)), 0.7))
    # tension lugs: white bars cutting the hatching
    nl = 4 if c.small else 6
    for i in range(nl):
        a = math.pi * (0.12 + 0.76 * i / (nl - 1))
        x = 50 - rx * math.cos(a)
        yo = ry * math.sin(a)
        o.append('<path d="M%s %sV%s" stroke="#fff" stroke-width="%s"/>' % (
            _f(x), _f(cy + yo + 4), _f(cb + yo - 4), c.w(2.2)))
        o.append(c.path('M%s %sV%s' % (_f(x), _f(cy + yo + 4), _f(cb + yo - 4)), 1.0))
    # drum head: white ellipse, light stipple
    head = _ell(50, cy, rx, ry)
    o.append('<path d="%s" fill="#fff"/>' % head)
    if not c.small:
        o.append(c.fillshape(_ell(50, cy + 1.5, rx * 0.7, ry * 0.55), c.stipple('hd', 2.4)))
    o.append(c.path(head, 1.1))
    o.append(c.path(_ell(50, cy, rx - 2.2, ry - 1.4), 0.5))
    # sticks crossed above the head
    o.append(_stick(c, 22, 24, 62, 46, 2.4))
    o.append(_stick(c, 80, 22, 40, 47, 2.4))
    return ''.join(o)


def _sticks(c):
    o = [_laurel(c, 1), _laurel(c, -1)]
    o.append(_stick(c, 26, 76, 72, 20, 3.0))
    o.append(_stick(c, 74, 76, 28, 20, 3.0))
    # bow / tie at the crossing
    o.append(c.solid(_circ(50, 50.5, 2.2 + 0.4 * c.k)))
    return ''.join(o)


def _paw(c):
    o = []
    # wreath: two leafy arcs
    o.append(_laurel(c, 1, n=4 if c.small else 6))
    o.append(_laurel(c, -1, n=4 if c.small else 6))
    pad = ('M50 52C40 52 33 61 34 68C35 74 42 73 50 72C58 73 65 74 66 68'
           'C67 61 60 52 50 52Z')
    toes = [(34, 46, 5.4, 7.2, -25), (44.5, 36, 5.6, 7.6, -8),
            (55.5, 36, 5.6, 7.6, 8), (66, 46, 5.4, 7.2, 25)]
    if c.small:
        o.append(c.solid(pad))
        for x, y, a, b, rot in toes:
            o.append('<path transform="translate(%s %s) rotate(%s)" d="%s"/>'
                     % (x, y, rot, _ell(0, 0, a, b)))
    else:
        hp = c.hatch('pd', 45, 1.4, 0.6)
        o.append(c.fillshape(pad, hp) + c.path(pad, 1.2))
        for x, y, a, b, rot in toes:
            e = _ell(0, 0, a, b)
            o.append('<g transform="translate(%s %s) rotate(%s)"><path d="%s" fill="%s"/>%s</g>'
                     % (x, y, rot, e, hp, c.path(e, 1.2)))
    return ''.join(o)


def _bass(c):
    o = []
    # body shoulders and f-holes
    body = 'M47 60C40 62 26 64 18 76M53 60C60 62 74 64 82 76'
    o.append(c.path(body, 1.1))
    bsp = 1.9 if c.small else 1.6
    o.append(c.fillshape('M47 60C40 62 26 64 18 76L13 70C20 62 36 58 47 58Z',
                         c.hatch('bd', 30, bsp)))
    o.append(c.fillshape('M53 60C60 62 74 64 82 76L87 70C80 62 64 58 53 58Z',
                         c.hatch('bd2', -30, bsp)))
    for s in (-1, 1):
        x = 50 + s * 18
        fh = ('M%s 66C%s 70 %s 76 %s 82' % (_f(x + s * 2), _f(x + s * 4), _f(x - s * 3), _f(x - s * 1)))
        o.append(c.path(fh, 1.3 if c.small else 1.0))
        o.append(c.solid(_circ(x + s * 2.4, 65.5, 1.4 + 0.25 * c.k)))
        o.append(c.solid(_circ(x - s * 1, 82.5, 1.4 + 0.25 * c.k)))
        o.append(c.path('M%s 74H%s' % (_f(x - 2.5), _f(x + 2.5)), 0.8))
    # neck + fingerboard (solid ebony)
    o.append(c.solid('M45.5 62L46.5 38H53.5L54.5 62Z'))
    # strings over the fingerboard (white)
    o.append('<path d="M48.2 38V62M51.8 38V62" stroke="#fff" stroke-width="%s"/>' % c.w(0.5))
    # pegbox
    o.append(c.path('M46 38L45 24H55L54 38', 1.0))
    if not c.small:
        o.append(c.fillshape('M47 37L46.3 26H53.7L53 37Z', c.hatch('pb', 0, 1.4)))
    # tuning pegs
    for y in (27, 32):
        o.append(c.path('M45 %sH39M55 %sH61' % (y + 0.5, y + 2), 1.2))
        o.append(c.solid(_circ(38, y + 0.5, 1.3 + 0.2 * c.k) + _circ(62, y + 2, 1.3 + 0.2 * c.k)))
    # scroll: spiral above the pegbox
    d = []
    cx, cy = 50, 17
    for i in range(0, 46 if not c.small else 34):
        t = i / 45.0
        a = -math.pi / 2 + t * 2.4 * math.pi
        rr = 7.5 * (1 - 0.72 * t)
        d.append('%s %s' % (_f(cx + rr * math.cos(a) * 1.05), _f(cy + rr * math.sin(a) * 0.95 + 0.5)))
    o.append(c.path('M45 24C43 20 43 13 50 9.5L' + 'L'.join(d), 1.2))
    o.append(c.path('M55 24C57 21 58 16 56 13', 1.0))
    o.append(c.solid(_circ(50.6, 17.2, 1.2 + 0.25 * c.k)))
    return ''.join(o)


def _vinyl(c):
    o = [c.solid(_circ(50, 50, 37.5))]
    # grooves as white arcs, broken by a light sheen sector
    step = 1.5 * c.k if c.small else 1.15 * c.k
    rr = 14.5
    d = []
    while rr < 36:
        for a0, a1 in ((math.radians(-35), math.radians(205)), (math.radians(222), math.radians(308))):
            x0, y0 = 50 + rr * math.cos(a0), 50 + rr * math.sin(a0)
            x1, y1 = 50 + rr * math.cos(a1), 50 + rr * math.sin(a1)
            large = 1 if (a1 - a0) > math.pi else 0
            d.append('M%s %sA%s %s 0 %d 1 %s %s' % (_f(x0), _f(y0), _f(rr), _f(rr), large, _f(x1), _f(y1)))
        rr += step
    o.append('<path d="%s" fill="none" stroke="#fff" stroke-width="%s"/>' % (''.join(d), c.w(0.5)))
    # label
    o.append('<path d="%s" fill="#fff"/>' % _circ(50, 50, 12.5))
    o.append(c.fillshape(_circ(50, 50, 12.5), c.hatch('lb', 45, 1.6 if c.small else 1.3)))
    o.append(c.path(_circ(50, 50, 12.5), 0.8))
    o.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="%s"/>'
             % (_circ(50, 50, max(2.2, 1.1 * c.k)), c.w(0.7)))
    if not c.small:
        o.append('<path d="M41 47A9.5 9.5 0 0 1 59 47" fill="none" stroke="#fff" stroke-width="%s"/>'
                 % c.w(1.6))
    return ''.join(o)


def _fir(c):
    o = []
    top, base = 14, 76
    n = 7 if c.small else 13
    d = ['M50 %sV%s' % (top, base + 6)]
    for i in range(1, n + 1):
        t = i / float(n)
        y = top + (base - top) * t
        hw = 4 + 26 * t * (0.86 + 0.14 * (i % 2))
        droop = 3 + 4 * t
        d.append('M50 %sQ%s %s %s %s' % (_f(y - 4), _f(50 - hw * 0.5), _f(y - 2),
                                         _f(50 - hw), _f(y + droop - 2)))
        d.append('M50 %sQ%s %s %s %s' % (_f(y - 4), _f(50 + hw * 0.5), _f(y - 2),
                                         _f(50 + hw), _f(y + droop - 2)))
        if not c.small:
            # needles: short ticks under each bough
            for s in (-1, 1):
                for j in range(1, int(hw / 4)):
                    x = 50 + s * j * 4
                    yy = y - 3.6 + droop * (j * 4 / hw) ** 2 * 0.7 + (j * 4 / hw) * 1.5
                    d.append('M%s %sl%s 2.6' % (_f(x), _f(yy), _f(-s * 0.8)))
    o.append(c.path(''.join(d), 1.0 if c.small else 0.75))
    o.append(c.path('M50 %sV%s' % (top, base + 6), 1.6))
    # tip star-like point
    o.append(c.solid(_star(50, top - 1.5, 3.4, 1.4)))
    # ground
    g = 'M18 83Q50 77 82 83'
    o.append(c.path(g, 1.0))
    if not c.small:
        o.append(c.fillshape('M18 83Q50 77 82 83L80 87H20Z', c.hatch('gr', 0, 1.3)))
    return ''.join(o)


def _rose(c):
    o = []
    cx, cy = 50, 44
    # leaves and stem below
    o.append(c.path('M50 60C49 70 47 78 44 86', 1.2))
    for s, (lx, ly, rot) in ((-1, (36, 70, -30)), (1, (63, 74, 30))):
        leaf = 'M0 0C4 -5 12 -5 16 0C12 5 4 5 0 0Z'
        tr = 'translate(%s %s) rotate(%s) scale(%s 1)' % (
            _f(lx if s > 0 else lx + 14 * math.cos(math.radians(rot))), ly, rot, s)
        tr = 'translate(%s %s) rotate(%s)' % (lx, ly, rot if s > 0 else 180 + rot)
        o.append('<g transform="%s">%s%s</g>' % (
            tr, c.fillshape(leaf, c.hatch('lf%d' % s, 60, 1.5)) if not c.small else c.solid(leaf),
            c.path(leaf + 'M0 0H15', 0.7)))
    # outer petals: five scallops
    pet = []
    R = 20
    for i in range(5):
        a0 = math.radians(-90 + 72 * i - 36)
        a1 = math.radians(-90 + 72 * i + 36)
        am = (a0 + a1) / 2
        x0, y0 = cx + R * math.cos(a0) * 0.9, cy + R * math.sin(a0) * 0.85
        x1, y1 = cx + R * math.cos(a1) * 0.9, cy + R * math.sin(a1) * 0.85
        qx, qy = cx + R * 1.45 * math.cos(am), cy + R * 1.35 * math.sin(am)
        pet.append((x0, y0, qx, qy, x1, y1))
    d = 'M%s %s' % (_f(pet[0][0]), _f(pet[0][1])) + ''.join(
        'Q%s %s %s %s' % (_f(p[2]), _f(p[3]), _f(p[4]), _f(p[5])) for p in pet) + 'Z'
    o.append('<path d="%s" fill="#fff"/>' % d)
    o.append(c.fillshape(d, c.hatch('pt', -40, 2.2 if c.small else 1.6)))
    o.append(c.path(d, 1.1))
    # inner cup and spiral heart in white with dark outline
    cup = _ell(cx, cy + 1, 13, 11)
    o.append('<path d="%s" fill="#fff"/>' % cup)
    o.append(c.path('M%s %sC%s %s %s %s %s %s' % (_f(cx - 13), _f(cy), _f(cx - 12), _f(cy + 14),
                                                 _f(cx + 12), _f(cy + 14), _f(cx + 13), _f(cy)), 1.0))
    sp = []
    for i in range(40):
        t = i / 39.0
        a = t * 3.2 * math.pi
        rr = 11 * (1 - 0.85 * t)
        sp.append('%s %s' % (_f(cx + rr * math.cos(a)), _f(cy - 1 + rr * 0.78 * math.sin(a))))
    o.append(c.path('M' + 'L'.join(sp), 1.0 if c.small else 0.8))
    return ''.join(o)


def _salmon(c):
    o = []
    # water below
    d = []
    rng = c.rng
    y = 72
    while y < 88:
        x = 12 + rng.random() * 4
        while x < 88:
            ln = rng.uniform(8, 18)
            e = min(x + ln, 88)
            d.append('M%s %sQ%s %s %s %s' % (_f(x), _f(y), _f((x + e) / 2), _f(y - 1.2), _f(e), _f(y)))
            x = e + rng.uniform(2, 5)
        y += 1.8 * c.k if c.small else 1.9 * c.k
    clip = '%s-wc' % c.pid
    c.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (clip, _circ(50, 50, 40)))
    o.append('<g clip-path="url(#%s)">%s</g>' % (clip, c.path(''.join(d), 0.6)))
    # arched body leaping up-right
    body = ('M18 62C24 44 40 30 60 28C68 27 76 30 82 36C77 40 70 43 62 44'
            'C48 46 36 54 28 66Z')
    o.append('<path d="%s" fill="#fff"/>' % body)
    o.append(c.fillshape('M22 60C30 50 44 44 62 44C70 43 77 40 82 36C78 40 70 46 60 48'
                         'C46 50 36 56 28 66Z', c.hatch('bl', -20, 1.4 if c.small else 1.2)))
    if not c.small:
        o.append(c.fillshape(body, c.hatch('sc', 45, 2.4, 0.4)))
    o.append(c.path(body, 1.1))
    # tail
    tail = 'M24 62L12 60L16 68L14 76L26 68Z'
    o.append(c.fillshape(tail, c.hatch('tl', 0, 1.3)) if not c.small else c.solid(tail))
    o.append(c.path(tail, 1.0))
    # fins
    o.append(c.solid('M48 31L52 22L56 29Z'))
    o.append(c.solid('M44 49L40 56L50 50Z'))
    # lateral line, gill, eye, jaw
    o.append(c.path('M30 56C42 42 56 37 74 36', 0.6))
    o.append(c.path('M70 30C67 34 67 38 69 42', 0.9))
    o.append(c.solid(_circ(75.5, 33.5, 1.6 + 0.2 * c.k)))
    o.append(c.path('M82 36L77 38.5', 0.9))
    # spray drops
    for x, y2 in ((14, 50), (20, 44), (10, 56)):
        o.append(c.solid(_circ(x, y2, 0.9 + 0.25 * c.k)))
    return ''.join(o)


def _moon(c):
    o = []
    # crescent: outer circle minus offset circle
    R = 24
    cx, cy = 44, 52
    ox = 12
    # intersection points of circles (cx,cy,R) and (cx+ox,cy-6,R)
    cx2, cy2 = cx + ox, cy - 7
    dx, dy = cx2 - cx, cy2 - cy
    D = math.hypot(dx, dy)
    a = D / 2
    h = math.sqrt(R * R - a * a)
    mx, my = cx + dx / 2, cy + dy / 2
    p1 = (mx + h * dy / D, my - h * dx / D)
    p2 = (mx - h * dy / D, my + h * dx / D)
    cres = ('M%s %sA%s %s 0 1 0 %s %sA%s %s 0 0 1 %s %sZ'
            % (_f(p1[0]), _f(p1[1]), R, R, _f(p2[0]), _f(p2[1]), R, R, _f(p1[0]), _f(p1[1])))
    o.append(c.fillshape(cres, c.hatch('mn', 30, 1.6 if c.small else 1.25)))
    if not c.small:
        o.append(c.fillshape(cres, c.hatch('mn2', -30, 2.6, 0.45)))
    o.append(c.path(cres, 1.1))
    # stars
    stars = [(70, 28, 6.5), (76, 56, 4.5), (58, 74, 3.6), (30, 22, 3.4)]
    if c.small:
        stars = [(70, 28, 8.5), (74, 60, 6.5)]
    for x, y, s in stars:
        o.append(c.solid(_star(x, y, s, s * 0.4)))
    if not c.small:
        for i in range(10):
            x, y = c.rng.uniform(20, 82), c.rng.uniform(18, 84)
            if math.hypot(x - cx, y - cy) > R + 3:
                o.append(c.solid(_circ(x, y, 0.5 * c.k)))
    return ''.join(o)


def _sun(c):
    o = []
    n = 12 if c.small else 16
    d = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        if i % 2 == 0:
            r0, r1, hw = 17, 36, 4.2
            nx, ny = -sa, ca
            d.append('M%s %sL%s %sL%s %sZ' % (
                _f(50 + r0 * ca + hw * nx), _f(50 + r0 * sa + hw * ny),
                _f(50 + r1 * ca), _f(50 + r1 * sa),
                _f(50 + r0 * ca - hw * nx), _f(50 + r0 * sa - hw * ny)))
        else:
            # flame ray: wavy line
            pts = []
            for j in range(9):
                t = j / 8.0
                rr = 18 + 13 * t
                off = math.sin(t * math.pi * 2) * 2.2
                pts.append('%s %s' % (_f(50 + rr * ca - off * sa), _f(50 + rr * sa + off * ca)))
            o.append(c.path('M' + 'L'.join(pts), 1.2 if c.small else 1.0))
    o.append(c.solid(''.join(d)))
    disc = _circ(50, 50, 15)
    o.append('<path d="%s" fill="#fff"/>' % disc)
    o.append(c.fillshape(disc, c.stipple('dc', 2.2 if c.small else 1.8, 0.45)))
    o.append(c.path(disc, 1.2))
    if not c.small:
        o.append(c.path(_circ(50, 50, 11.5), 0.5))
        # serene face: eyes and smile
        o.append(c.path('M43 47Q45 45 47 47M53 47Q55 45 57 47M44 55Q50 59 56 55', 0.8))
    return ''.join(o)


_MOTIFS = [('snare', _snare, False), ('sticks', _sticks, True), ('paw', _paw, False),
           ('bass', _bass, True), ('vinyl', _vinyl, False), ('fir', _fir, True),
           ('rose', _rose, False), ('salmon', _salmon, True), ('moon', _moon, False),
           ('sun', _sun, True)]


def _make(key, fn, roped):
    def medallion(r, seed=0):
        c = _C(key, r, seed)
        body = fn(c)
        size = _f(2 * c.r)
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
                'width="%s" height="%s"><defs>%s</defs><path d="%s" fill="#fff"/>'
                '%s%s</svg>' % (size, size, ''.join(c.defs), _circ(50, 50, 48.6),
                                body, _rim(c, roped ^ bool(seed % 2 and seed % 3 == 0))))
    medallion.__name__ = 'medallion_' + key
    return medallion


MEDALLIONS = dict((k, _make(k, fn, roped)) for k, fn, roped in _MOTIFS)


# ---------------------------------------------------------------- easter eggs

def easter_egg(kind, seed=0, size=10):
    """Tiny <g> glyph (6..14 px square, origin top-left) to hide in scrollwork.

    kinds: 'paw', 'sticks', 'A' (script initial for Alfred), 'note', 'star'.
    No <svg> wrapper; place with a transform on an enclosing <g>.
    """
    size = max(6, min(14, size))
    s = size / 10.0
    sw = lambda px: _f(px / s)
    rng = random.Random('%s-%s' % (kind, seed))
    tilt = _f(rng.uniform(-12, 12))
    if kind == 'paw':
        body = ('<path d="M5 5.6C3.3 5.6 2.2 7.1 2.4 8.3C2.6 9.4 3.8 9.2 5 9'
                'C6.2 9.2 7.4 9.4 7.6 8.3C7.8 7.1 6.7 5.6 5 5.6Z%s%s%s%s"/>'
                % (_ell(1.6, 4.2, 1, 1.3), _ell(3.8, 2.4, 1, 1.35),
                   _ell(6.2, 2.4, 1, 1.35), _ell(8.4, 4.2, 1, 1.3)))
    elif kind == 'sticks':
        body = ('<path d="M1.5 9L8.5 1M8.5 9L1.5 1" stroke="#000" stroke-width="%s" '
                'stroke-linecap="round" fill="none"/><path d="%s%s"/>'
                % (sw(1.1), _circ(8.6, 0.9, 0.9), _circ(1.4, 0.9, 0.9)))
    elif kind == 'A':
        body = ('<path d="M1 9.3C2.6 9.3 3.8 6.5 5 3.4C5.6 1.8 6.3 0.6 7 0.6'
                'C7.3 3.5 7.4 6.6 8.6 9.2M3.2 6H7.6M0.6 8C1.4 7 3 6.8 3.6 7.4" '
                'fill="none" stroke="#000" stroke-width="%s" stroke-linecap="round" '
                'stroke-linejoin="round"/>' % sw(1.0))
    elif kind == 'note':
        body = ('<path d="%s" transform="rotate(-20 3.4 8)"/><path d="M5.6 7.8V0.8'
                'C6.6 2.6 9 3.2 8.4 6" fill="none" stroke="#000" stroke-width="%s"/>'
                % (_ell(3.4, 8, 2.3, 1.55), sw(1.0)))
    elif kind == 'star':
        body = '<path d="%s"/>' % _star(5, 5.3, 5, 2.1)
    else:
        raise KeyError(kind)
    return ('<g class="egg egg-%s" transform="scale(%s) rotate(%s 5 5)">%s</g>'
            % (kind, _f(s), tilt, body))


EGG_KINDS = ('paw', 'sticks', 'A', 'note', 'star')


# ---------------------------------------------------------------- demo

def demo(path='/tmp/claude-0/shots/team/medallions_demo.html'):
    cells = []
    for k, _, _ in _MOTIFS:
        fn = MEDALLIONS[k]
        cells.append('<div class="c">%s %s<br>%s<div class="n">%s %d+%dB</div></div>'
                     % (fn(14, 1), fn(20, 2), fn(36, 1), k,
                        len(fn(14, 1)), len(fn(36, 1))))
    eggs = []
    for kind in EGG_KINDS:
        for sz in (6, 10, 14):
            eggs.append('<svg width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>'
                        % (sz + 2, sz + 2, sz + 2, sz + 2,
                           '<g transform="translate(1 1)">%s</g>' % easter_egg(kind, 3, sz)))
        eggs.append('&nbsp;')
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'body{margin:0;width:618px;background:#fff;font:10px Georgia,serif}'
            '.w{display:flex;flex-wrap:wrap;padding:4px 8px}'
            '.c{width:120px;text-align:center;margin:2px 0}.c svg{vertical-align:middle}'
            '.n{font-size:9px}.e{padding:2px 12px}.e svg{vertical-align:middle}'
            '</style></head><body><div class="w">%s</div><div class="e">%s</div></body></html>'
            % (''.join(cells), ''.join(eggs)))
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w') as fh:
        fh.write(html)
    return path


if __name__ == '__main__':
    print(demo())
