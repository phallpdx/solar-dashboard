"""Bulino-style engraved SVG vignettes (120x80) for the Kindle bedtime edition.

Pure line work: hatching, cross-hatching and stipple only; no grey fills.
Hatch 0.5-0.8 px, outlines 1-1.2 px. Pattern/clip ids are prefixed per key.
Standard library only.
"""
import math
import os
import random

_HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80" '
         'width="120" height="80">')
_FRAME = ('<rect x="1.5" y="1.5" width="117" height="77" fill="none" '
          'stroke="#000" stroke-width="1.2"/>'
          '<rect x="3.5" y="3.5" width="113" height="73" fill="none" '
          'stroke="#000" stroke-width="0.5"/>')


def _f(v):
    s = ('%.1f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def _hp(pid, ang, sp, w=0.6):
    """Line-hatch pattern, rotated."""
    return ('<pattern id="%s" width="%s" height="%s" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(%s)"><path d="M0 %sH%s" stroke="#000" '
            'stroke-width="%s"/></pattern>' % (pid, _f(sp), _f(sp), _f(ang),
                                               _f(sp / 2), _f(sp), w))


def _sp(pid, sp, r=0.4):
    """Stipple pattern (offset dots)."""
    h = sp / 2
    return ('<pattern id="%s" width="%s" height="%s" patternUnits="userSpaceOnUse">'
            '<circle cx="%s" cy="%s" r="%s"/><circle cx="%s" cy="%s" r="%s"/></pattern>'
            % (pid, _f(sp), _f(sp), _f(h / 2), _f(h / 2), r, _f(h * 1.5), _f(h * 1.5), r))


def _svg(defs, body):
    return _HEAD + '<defs>' + defs + '</defs>' + body + _FRAME + '</svg>'


def _g(d, w=0.6, extra=''):
    return '<path d="%s" fill="none" stroke="#000" stroke-width="%s"%s/>' % (d, w, extra)


def _water(rng, y0, y1, x0=4.5, x1=115.5, step=1.6, dense=0.55):
    """Engraved water: broken horizontal strokes, tighter toward the viewer."""
    d = []
    y = y0
    while y < y1:
        x = x0 + rng.random() * 3
        while x < x1:
            ln = rng.uniform(4, 16)
            e = min(x + ln, x1)
            d.append('M%s %sH%s' % (_f(x), _f(y), _f(e)))
            x = e + rng.uniform(1, 5) * (1 - dense)
        frac = (y - y0) / max(1, (y1 - y0))
        y += step * (1.25 - 0.55 * frac)
    return ''.join(d)


def _sky(y0, y1, gap0, gap1, x0=4.5, x1=115.5):
    d = []
    y = y0
    while y < y1:
        d.append('M%s %sH%s' % (_f(x0), _f(y), _f(x1)))
        t = (y - y0) / max(1, y1 - y0)
        y += gap0 + (gap1 - gap0) * t
    return ''.join(d)


def _fir(x, top, h, w, sp=1.3):
    """Fir drawn as engraved branch chevrons on a trunk."""
    d = ['M%s %sV%s' % (_f(x), _f(top), _f(top + h + 2))]
    n = max(4, int(h / sp))
    for i in range(1, n + 1):
        y = top + h * i / n
        hw = w * i / n * (0.8 + 0.2 * (i % 2))
        d.append('M%s %sL%s %sL%s %s' % (_f(x - hw), _f(y + 1), _f(x), _f(y - 0.8),
                                         _f(x + hw), _f(y + 1)))
    return ''.join(d)


# ---------------------------------------------------------------- bridge
def _bridge():
    k = 'bridge'
    rng = random.Random(11)
    defs = (_hp(k + 'V', 90, 1.3, 0.6) + _hp(k + 'D', 35, 1.6, 0.5) +
            '<clipPath id="%sC"><rect x="4" y="4" width="112" height="72"/></clipPath>' % k)
    b = ['<g clip-path="url(#%sC)">' % k]
    # sky: sparse at top
    b.append(_g(_sky(6, 30, 2.2, 4.5), 0.5))
    # far hills
    hill = 'M4 50L4 41Q14 36 24 40T46 38T70 41T96 37T116 40L116 50Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sD)"/>' % (hill, hill, k))
    b.append(_g('M4 41Q14 36 24 40T46 38T70 41T96 37T116 40', 0.7))
    # river
    b.append('<rect x="4" y="53" width="112" height="24" fill="#fff"/>')
    b.append(_g(_water(rng, 57, 76.5, step=1.7), 0.5))
    # cables + suspenders
    def cy(x, xa, xb, ya, yc):
        t = (x - xa) / (xb - xa)
        return (1 - t) ** 2 * ya + 2 * t * (1 - t) * yc + t * t * ya
    sus = []
    x = 41.0
    while x < 79.5:
        sus.append('M%s %sV50' % (_f(x), _f(cy(x, 38, 82, 15, 78) + 0.5)))
        x += 2.4
    for xa, xb, s in ((4, 38, -1), (82, 116, 1)):
        x = xa + 2.0
        while x < xb - 2:
            t = (x - xa) / (xb - xa)
            if s < 0:
                yv = 47 - 32 * (t ** 1.6)
            else:
                yv = 15 + 32 * (t ** 0.62)
            sus.append('M%s %sV50' % (_f(x), _f(yv + 0.5)))
            x += 2.4
    b.append(_g(''.join(sus), 0.5))
    b.append(_g('M38 15Q60 78 82 15M2 47Q26 40 38 15M82 15Q94 40 118 47', 1))
    # deck with truss
    b.append('<rect x="4" y="50" width="112" height="3" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    tr = ''.join('M%s 50L%s 53' % (_f(x), _f(x + 1.5 if (i % 2) else x - 1.5))
                 for i, x in enumerate([5.5 + 1.5 * j for j in range(74)]))
    b.append(_g(tr, 0.5))
    # towers
    for tx in (38, 82):
        out = 'M%s 66V16L%s 9L%s 13L%s 9L%s 16V66Z' % (
            _f(tx - 4.5), _f(tx - 3.3), _f(tx), _f(tx + 3.3), _f(tx + 4.5))
        b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sV)" stroke="#000" '
                 'stroke-width="1"/>' % (out, out, k))
        # Gothic pointed arches
        for ya, yb in ((19, 27), (30, 47)):
            a = 'M%s %sV%sQ%s %s %s %sQ%s %s %s %sV%sZ' % (
                _f(tx - 2.4), _f(yb), _f(ya + 3), _f(tx - 2.4), _f(ya + 0.5), _f(tx), _f(ya - 1),
                _f(tx + 2.4), _f(ya + 0.5), _f(tx + 2.4), _f(ya + 3), _f(yb))
            b.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="0.6"/>' % a)
        b.append(_g('M%s 7.5V9M%s 7.5V9' % (_f(tx - 3.3), _f(tx + 3.3)), 0.6))
        # reflection
        rf = ''.join('M%s %sH%s' % (_f(tx - 4 + rng.uniform(-1, 1)), _f(y),
                                    _f(tx + 4 + rng.uniform(-1, 1)))
                     for y in [66.8 + 1.1 * i for i in range(9)])
        b.append(_g(rf, 0.6))
    b.append('</g>')
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- hood
def _hood():
    k = 'hood'
    rng = random.Random(5)
    defs = (_hp(k + 'L', -38, 1.7, 0.5) + _hp(k + 'R', 40, 1.2, 0.6) +
            _hp(k + 'X', -40, 1.5, 0.5) +
            '<clipPath id="%sM"><path d="M4 62L36 30L52 16L60 11L66 15L82 30L116 58V62Z"/>'
            '</clipPath>' % k)
    b = []
    b.append(_g(_sky(6, 36, 1.6, 4.2), 0.5))
    mtn = 'M4 62L36 30L52 16L60 11L66 15L82 30L116 58V62Z'
    b.append('<path d="%s" fill="#fff"/>' % mtn)
    # lower slopes: left light hatch, right shadow cross-hatch
    snow = 'M4 4H116V40L100 42L92 34L86 37L80 31L74 34L69 27L64 32L60 26L56 31L50 25L46 30L40 28L33 37L26 34L4 44Z'
    b.append('<g clip-path="url(#%sM)"><rect x="4" y="4" width="112" height="60" fill="url(#%sL)"/>'
             '<path d="M60 11L66 15L82 30L116 58V62H72L64 30Z" fill="url(#%sR)"/>'
             '<path d="M66 15L82 30L116 58V62H84L68 30Z" fill="url(#%sX)"/>'
             '<path d="%s" fill="#fff"/>' % (k, k, k, k, snow))
    # snow-field ridgeline shading (sparse strokes on shadow side of snow)
    rid = ('M60 11L62 22L60 26M66 15L67 24L64 32M62 15L72 27M64 18L76 31M66 21L80 33'
           'M68 25L86 37M70 30L90 37M56 15L53 22M52 19L47 27')
    b.append(_g(rid, 0.5))
    b.append(_g('M100 42L92 34L86 37L80 31L74 34L69 27L64 32L60 26L56 31L50 25L46 30'
                'L40 28L33 37L26 34L20 37', 0.6))
    b.append('</g>')
    b.append(_g('M4 62L36 30L52 16L60 11L66 15L82 30L116 58', 1.1))
    # lake
    b.append('<rect x="4" y="62" width="112" height="15" fill="#fff"/>')
    b.append(_g(_water(rng, 64, 76.5, step=1.5), 0.5))
    # firs in front
    firs = [(10, 44, 26, 6), (17, 50, 18, 4.5), (24, 47, 22, 5.5), (97, 46, 24, 6),
            (104, 42, 28, 6.5), (111, 50, 18, 4.5), (90, 53, 13, 3.5)]
    for x, t, h, w in firs:
        tri = 'M%s %sL%s %sL%s %sZ' % (_f(x), _f(t), _f(x - w - 0.5), _f(t + h + 1.5),
                                         _f(x + w + 0.5), _f(t + h + 1.5))
        b.append('<path d="%s" fill="#fff"/>' % tri)
        b.append(_g(_fir(x, t, h, w), 0.6))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- cranes
def _cranes():
    """Willamette harbor: a container gantry crane and a luffing tower crane."""
    k = 'cranes'
    rng = random.Random(3)
    defs = _hp(k + 'D', -30, 1.4, 0.5) + _hp(k + 'V', 90, 1.2, 0.6)
    b = []
    b.append(_g(_sky(5, 44, 1.2, 3.4), 0.5))
    # low sun
    b.append('<circle cx="92" cy="40" r="7" fill="#fff" stroke="#000" stroke-width="0.7"/>')
    # west hills
    hl = 'M4 52V44Q20 38 36 43T70 42T116 45V52Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sD)" stroke="#000" '
             'stroke-width="0.6"/>' % (hl, hl, k))
    # dock and water
    b.append('<rect x="4" y="52" width="112" height="25" fill="#fff"/>')
    b.append(_g(_water(rng, 58, 76.5, step=1.5), 0.5))
    b.append('<rect x="4" y="52" width="112" height="4" fill="url(#%sV)" stroke="#000" '
             'stroke-width="1"/>' % k)
    # gantry crane: two A-legs, portal beam, long boom out over the river
    g = ('M14 52L20 22L26 52M34 52L40 22L46 52'     # legs
         'M17 38H43M15.5 45H44.5'                     # leg ties
         'M8 22H86M8 25H70'                           # boom chords
         'M38 22L40 10L42 22M40 10L86 22M40 10L8 22') # A-frame + stays
    b.append(_g(g + 'M8 23.5H86M100 14V52M102 14V52M104 14V52M76 15.2H114', 3, ' stroke="#fff"'))
    b.append(_g(g, 1))
    tr = ''.join('M%s 22L%s 25' % (_f(x), _f(x + 2)) for x in range(10, 68, 4))
    b.append(_g(tr, 0.5))
    # machinery house and hook
    b.append('<rect x="26" y="25" width="10" height="5" fill="#000"/>')
    b.append(_g('M60 25V40', 0.6) + '<rect x="56" y="40" width="8" height="3" fill="#000"/>')
    # container stacks on the dock
    for x, y, w in ((48, 46, 12), (50, 40, 10), (62, 46, 14)):
        b.append('<rect x="%s" y="%s" width="%s" height="6" fill="url(#%sV)" stroke="#000" '
                 'stroke-width="0.8"/>' % (x, y, w, k))
    # tower crane on the right with lattice mast and jib
    b.append(_g('M100 52V14M104 52V14', 1))
    lat = ''.join('M100 %sL104 %s' % (_f(y), _f(y - 3)) for y in range(51, 16, -3))
    b.append(_g(lat, 0.5))
    b.append(_g('M76 14H114M76 16.5H110M102 14V7M102 7L78 14M102 7L114 14', 1))
    b.append(_g(''.join('M%s 14L%s 16.5' % (x, x + 2) for x in range(78, 110, 3)), 0.5))
    b.append('<rect x="106" y="16.5" width="6" height="4" fill="#000"/>')
    b.append(_g('M82 16.5V30', 0.6) + '<path d="M80.5 30H83.5L82 32Z"/>')
    # tugboat
    tug = 'M66 64H86L83 68H69Z'
    b.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="1"/>' % tug)
    b.append('<rect x="72" y="60" width="7" height="4" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    b.append(_g('M74 60V56', 1.2))
    # reflections
    b.append(_g(''.join('M%s %sH%s' % (_f(x + rng.uniform(-1, 1)), _f(y), _f(x + 3))
                        for x in (19, 39, 100) for y in (58.5, 61, 63.5)), 0.6))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- heron
def _heron():
    k = 'heron'
    rng = random.Random(9)
    defs = (_hp(k + 'B', 60, 1.3, 0.6) + _hp(k + 'N', 100, 1.8, 0.5) +
            _hp(k + 'X', -30, 1.4, 0.5))
    b = []
    b.append(_g(_sky(6, 40, 3.2, 1.6), 0.5))
    # water
    b.append('<rect x="4" y="58" width="112" height="19" fill="#fff"/>')
    b.append(_g(_water(rng, 60, 76.5, step=1.6), 0.5))
    # body: tilted teardrop, back to right
    body = 'M50 40Q56 33 68 36Q80 39 84 50Q77 49 74 52Q64 54 56 50Q48 46 50 40Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sB)"/>' % (body, body, k))
    # wing cross-hatch on lower half
    wing = 'M56 45Q66 41 80 46Q83 48 84 50Q77 49 74 52Q64 54 56 50Z'
    b.append('<path d="%s" fill="url(#%sX)"/>' % (wing, k))
    b.append(_g(body, 1.1))
    b.append(_g('M58 46Q68 42 80 47M62 49Q70 46 78 49', 0.6))
    # plumes hanging from chest and tail
    b.append(_g('M52 44Q50 50 52 54M54 46Q53 51 55 55M82 49Q86 53 88 56M80 50Q83 54 84 57', 0.5))
    # S-shaped neck
    neck = 'M52 40Q46 34 49 27Q52 21 47 16Q45 13 41 13L39 15Q43 16 44 18Q47 23 44 28Q41 35 46 42Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sN)"/>' % (neck, neck, k))
    b.append(_g(neck, 1))
    # head, crest, bill, eye
    b.append(_g('M41 13Q38 11 35 12L39 15', 1))
    b.append('<path d="M37 12.3L24 14.4L37 14.6Z"/>')
    b.append(_g('M41 12Q46 10 52 12.5M41 12.6Q47 11.5 51 14', 0.6))
    b.append(_g('M37.5 12.3Q39 11.4 41 12.2', 1.2))
    b.append('<circle cx="38.7" cy="13.1" r="0.6" fill="#fff" stroke="#000" stroke-width="0.5"/>')
    # legs
    b.append(_g('M64 53L62 66M69 53L72 66M62 66L58 67.5M62 66L65 67.6M72 66L69 67.6M72 66L76 67.4', 1))
    # ripples at feet
    b.append('<ellipse cx="66" cy="67" rx="12" ry="1.6" fill="#fff" stroke="#000" stroke-width="0.5"/>')
    b.append(_g('M56 69.5Q66 71.5 77 69.5', 0.5))
    # reeds
    reeds = []
    for i in range(34):
        x = 5 + rng.random() * 30 if i < 20 else 90 + rng.random() * 25
        h = rng.uniform(16, 38)
        lean = rng.uniform(-5, 5)
        reeds.append('M%s 76.5Q%s %s %s %s' % (_f(x), _f(x + lean * 0.2), _f(76.5 - h * 0.6),
                                              _f(x + lean), _f(76.5 - h)))
    b.append(_g(''.join(reeds), 0.6))
    b.append(_g('M20 46V52M108 42V48M100 50V55', 1.4))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- drums
def _ell_rings(cx, cy, rx, ry, n, rot=0):
    return ''.join('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s/>' % (
        _f(cx), _f(cy), _f(rx * i / n), _f(ry * i / n),
        ' transform="rotate(%s %s %s)"' % (rot, _f(cx), _f(cy)) if rot else '')
        for i in range(2, n + 1))


def _drums():
    k = 'drums'
    defs = (_hp(k + 'V', 90, 1.4, 0.6) + _hp(k + 'D', 45, 1.6, 0.5) + _sp(k + 'S', 2.2))
    b = []
    # floor rug stipple
    b.append('<ellipse cx="60" cy="72" rx="52" ry="5" fill="url(#%sS)"/>' % k)
    # hi-hat stand + cymbals (left)
    b.append(_g('M20 24V70M16 70L20 62L24 70M14 70L26 70', 0.8))
    b.append('<g fill="#fff" stroke="#000" stroke-width="0.5">%s</g>' % _ell_rings(20, 24, 11, 2.2, 4))
    b.append('<ellipse cx="20" cy="26" rx="11" ry="2.2" fill="#fff" stroke="#000" stroke-width="1"/>'
             '<ellipse cx="20" cy="24" rx="11" ry="2.2" fill="none" stroke="#000" stroke-width="1"/>')
    # ride cymbal (right), tilted, with lathe rings
    b.append(_g('M100 21L104 70M100 70L104 62L108 70', 0.8))
    b.append('<g fill="none" stroke="#000" stroke-width="0.5">%s</g>' % _ell_rings(100, 20, 16, 4.5, 6, -12))
    b.append('<ellipse cx="100" cy="20" rx="16" ry="4.5" transform="rotate(-12 100 20)" fill="none" '
             'stroke="#000" stroke-width="1"/><circle cx="100" cy="20" r="1.2"/>')
    # snare (left of kick)
    sn = 'M23 44V53A11 3 0 0 0 45 53V44Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sV)" stroke="#000" stroke-width="1"/>' % (sn, sn, k))
    b.append(_g('M26.5 46.5V55.2M30 46.8V55.8M34 47V56M38 46.8V55.8M41.5 46.5V55.2', 0.8,
                ' stroke-dasharray="1.6 1"'))
    b.append('<ellipse cx="34" cy="44" rx="11" ry="3" fill="#fff" stroke="#000" stroke-width="1"/>')
    b.append(_g('M28 56L26 70M40 56L42 70', 0.8))
    # floor tom (right)
    ft = 'M78 46V64A10 2.8 0 0 0 98 64V46Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sV)" stroke="#000" stroke-width="1"/>' % (ft, ft, k))
    b.append('<ellipse cx="88" cy="46" rx="10" ry="2.8" fill="#fff" stroke="#000" stroke-width="1"/>')
    b.append(_g('M80 66L79 70M96 66L97 70', 0.8))
    # kick drum front head: shell rim cross-hatched, head with concentric engraving
    b.append('<circle cx="60" cy="54" r="17" fill="#fff"/>')
    b.append('<circle cx="60" cy="54" r="17" fill="url(#%sD)"/>' % k)
    b.append('<circle cx="60" cy="54" r="14.3" fill="#fff" stroke="#000" stroke-width="1"/>')
    b.append('<circle cx="60" cy="54" r="17" fill="none" stroke="#000" stroke-width="1.2"/>')
    b.append('<g fill="none" stroke="#000" stroke-width="0.5">' +
             ''.join('<circle cx="60" cy="54" r="%s"/>' % _f(r) for r in (11.8, 12.8)) + '</g>')
    lugs = ''.join('<circle cx="%s" cy="%s" r="0.7"/>' % (_f(60 + 15.6 * math.cos(a)), _f(54 + 15.6 * math.sin(a)))
                   for a in [2 * math.pi * i / 10 for i in range(10)])
    b.append(lugs)
    # shading crescent on head (lower right)
    sh = ''.join('M%s %sA%s %s 0 0 1 %s %s' % (
        _f(60 + r * math.cos(0.1)), _f(54 + r * math.sin(0.1)), _f(r), _f(r),
        _f(60 + r * math.cos(1.9)), _f(54 + r * math.sin(1.9))) for r in (6, 7.4, 8.8, 10.2))
    b.append(_g(sh, 0.5))
    # rack tom on top of kick
    rt = 'M52 32V39A8 2.4 0 0 0 68 39V32Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sV)" stroke="#000" stroke-width="1"/>' % (rt, rt, k))
    b.append('<ellipse cx="60" cy="32" rx="8" ry="2.4" fill="#fff" stroke="#000" stroke-width="1"/>')
    # crossed sticks
    for x1, y1, x2, y2 in ((44, 6, 76, 28), (76, 6, 44, 28)):
        b.append(_g('M%s %sL%s %s' % (x1, y1, x2, y2), 2.4))
        b.append(_g('M%s %sL%s %s' % (x1, y1, x2, y2), 1, ' stroke="#fff"'))
        b.append('<circle cx="%s" cy="%s" r="1.1"/>' % (x1, y1))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- jazz (upright bass)
def _jazz():
    k = 'jazz'
    defs = (_hp(k + 'A', 65, 1.3, 0.6) + _hp(k + 'B', -25, 1.6, 0.5) + _sp(k + 'S', 2.4))
    b = []
    # spotlight cone of stipple behind
    b.append('<path d="M48 4H72L104 77H16Z" fill="url(#%sS)"/>' % k)
    b.append(_g('M48 4L16 77M72 4L104 77', 0.5))
    body = ('M60 30Q50 30 48 36Q47 41 51 45Q45 48 44 56Q43 66 50 71Q55 74 60 74'
            'Q65 74 70 71Q77 66 76 56Q75 48 69 45Q73 41 72 36Q70 30 60 30Z')
    b.append('<path d="%s" fill="#fff"/>' % body)
    b.append('<clipPath id="%sC"><path d="%s"/></clipPath>' % (k, body))
    b.append('<g clip-path="url(#%sC)"><rect x="40" y="28" width="40" height="48" fill="url(#%sA)"/>'
             '<rect x="62" y="28" width="18" height="48" fill="url(#%sB)"/>'
             '<path d="M53 38Q50 50 54 66" stroke="#fff" stroke-width="2.4" fill="none"/></g>' % (k, k, k))
    b.append(_g(body, 1.2))
    b.append(_g('M60 31.5Q51.5 31.5 49.8 36.5Q49 41 53 45.2Q47 48.5 46 56Q45.2 65 51.2 69.6', 0.5))
    # fingerboard, neck, scroll, pegs
    b.append('<path d="M58.6 8V60L60 62L61.4 60V8Z" fill="#000"/>')
    b.append(_g('M58.5 8Q56 4.5 59.5 3.5Q63.5 3.4 62.6 6.6Q61.6 8.4 60 7', 1))
    b.append(_g('M56 9H58.5M61.5 9H64M56 12H58.5M61.5 12H64', 1))
    # f-holes
    b.append(_g('M52.5 50Q54.5 54 52.5 58Q50.5 62 52.5 66M67.5 50Q65.5 54 67.5 58Q69.5 62 67.5 66', 0.8))
    b.append('<circle cx="52.5" cy="50" r="0.8"/><circle cx="52.5" cy="66" r="0.8"/>'
             '<circle cx="67.5" cy="50" r="0.8"/><circle cx="67.5" cy="66" r="0.8"/>')
    # bridge, tailpiece, strings, endpin
    b.append('<path d="M56 58.6H64L63 60H57Z" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    b.append('<path d="M58 64H62L61 72H59Z"/>')
    b.append(_g('M58.9 10V64M59.6 10V64M60.4 10V64M61.1 10V64', 0.5, ' stroke="#fff"'))
    b.append(_g('M58.9 60V64M59.6 60V64M60.4 60V64M61.1 60V64', 0.5))
    b.append(_g('M60 74V77', 1.2))
    # bow resting across
    b.append(_g('M30 66L92 40', 1))
    b.append(_g('M30 67.4L92 41.4', 0.5))
    b.append('<path d="M88.5 40.6L92.5 39L93 42Z"/>')
    # musical notes drifting
    b.append('<ellipse cx="25" cy="22" rx="2" ry="1.4" transform="rotate(-20 25 22)"/>'
             '<ellipse cx="33" cy="18" rx="2" ry="1.4" transform="rotate(-20 33 18)"/>')
    b.append(_g('M26.8 21.4V12L34.8 8.4V17.4', 0.8) + _g('M26.8 13.4L34.8 9.8', 1.4))
    b.append('<ellipse cx="94" cy="20" rx="2" ry="1.4" transform="rotate(-20 94 20)"/>')
    b.append(_g('M95.8 19.4V11Q98 13 99 16', 0.8))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- record
def _record():
    k = 'record'
    defs = (_hp(k + 'D', 45, 1.5, 0.5) + _hp(k + 'H', 0, 1.3, 0.5))
    b = []
    # plinth: wood grain hatch
    b.append('<rect x="8" y="8" width="104" height="64" rx="3" fill="url(#%sH)" stroke="#000" '
             'stroke-width="1.2"/>' % k)
    # platter
    b.append('<circle cx="48" cy="40" r="29" fill="#fff" stroke="#000" stroke-width="1"/>')
    b.append('<circle cx="48" cy="40" r="27" fill="none" stroke="#000" stroke-width="0.5" '
             'stroke-dasharray="0.6 0.9"/>')
    # record grooves
    g = ''.join('<circle cx="48" cy="40" r="%s"/>' % _f(r) for r in
                [10.5 + 0.9 * i for i in range(17)])
    b.append('<circle cx="48" cy="40" r="26" fill="#000"/>')
    b.append('<g fill="none" stroke="#fff" stroke-width="0.4">%s</g>' % g)
    # sheen wedges (white) reflecting light
    def wedge(a0, a1, r0=11, r1=25.8):
        p = lambda r, a: '%s %s' % (_f(48 + r * math.cos(a)), _f(40 + r * math.sin(a)))
        return 'M%sL%sA%s %s 0 0 1 %sL%sA%s %s 0 0 0 %sZ' % (
            p(r0, a0), p(r1, a0), _f(r1), _f(r1), p(r1, a1), p(r0, a1), _f(r0), _f(r0), p(r0, a0))
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="#fff"/>' % (
        wedge(-2.2, -1.85), wedge(0.95, 1.3)))
    b.append('<g fill="none" stroke="#000" stroke-width="0.5"><path d="%s"/><path d="%s"/></g>' % (
        wedge(-2.2, -1.85), wedge(0.95, 1.3)))
    # label
    b.append('<circle cx="48" cy="40" r="9" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    b.append('<circle cx="48" cy="40" r="7.6" fill="url(#%sD)"/>' % k)
    b.append('<circle cx="48" cy="40" r="4.2" fill="#fff" stroke="#000" stroke-width="0.5"/>')
    b.append('<circle cx="48" cy="40" r="0.9"/>')
    # tonearm
    b.append('<circle cx="96" cy="20" r="6" fill="#fff" stroke="#000" stroke-width="1"/>'
             '<circle cx="96" cy="20" r="3.4" fill="url(#%sD)" stroke="#000" stroke-width="0.6"/>' % k)
    b.append('<rect x="93" y="5" width="6" height="6" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    b.append(_g('M96 20L98 46Q98 54 74 54', 2.6))
    b.append(_g('M96 20L98 46Q98 54 74 54', 1, ' stroke="#fff"'))
    b.append('<path d="M75 51L69 52.6L69.6 56.4L75.6 56.6Z" fill="#fff" stroke="#000" stroke-width="1"/>')
    # knobs and speed button
    b.append('<circle cx="100" cy="64" r="3" fill="#fff" stroke="#000" stroke-width="0.8"/>'
             '<circle cx="90" cy="64" r="3" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    b.append(_g('M100 61.6V64M90 64L92 62.4', 0.8))
    b.append('<circle cx="14" cy="66" r="1.8" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- dog
def _dog():
    """Sleeping dog curled on a fringed rug, head in clear profile."""
    k = 'dog'
    defs = (_sp(k + 'S', 2.4) + _hp(k + 'D', 30, 1.3, 0.6) + _hp(k + 'E', -50, 1.1, 0.6))
    b = []
    # rug with border and fringe
    b.append('<path d="M10 58H110L114 74H6Z" fill="url(#%sS)" stroke="#000" stroke-width="1"/>' % k)
    b.append(_g('M13 61H107L110 71H10Z', 0.6))
    b.append(_g(''.join('M%s 74v2.5' % x for x in range(8, 114, 3)), 0.5))
    # body: curled oval (back to the viewer's right)
    body = 'M44 64Q38 46 60 38Q84 32 96 46Q102 56 94 64Z'
    b.append('<path d="%s" fill="#fff"/>' % body)
    b.append('<clipPath id="%sC"><path d="%s"/></clipPath>' % (k, body))
    arcs = ''.join('M%s 66A%s %s 0 0 1 %s 66' % (_f(70 - r * 1.3), _f(r * 1.3), _f(r), _f(70 + r * 1.3))
                   for r in [8 + i * 1.8 for i in range(12)])
    b.append('<g clip-path="url(#%sC)">%s<rect x="40" y="56" width="62" height="10" fill="url(#%sD)"/></g>'
             % (k, _g(arcs, 0.5, ' stroke-dasharray="3 1.2"'), k))
    b.append(_g(body, 1.2))
    # haunch line and tail curling to the front
    b.append(_g('M80 64Q76 50 88 46', 0.8))
    tail = 'M95 62Q100 68 84 68Q66 68 56 65Q70 65 84 64.4Q92 64 95 62Z'
    b.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="1"/>' % tail)
    # front legs stretched forward
    b.append('<path d="M46 63H22Q18 63 18 66Q18 68 22 68H48Z" fill="#fff" stroke="#000" stroke-width="1"/>')
    b.append(_g('M20.5 64.8V67.4M23 64.6V67.6', 0.5))
    # head in profile resting on the paws, snout pointing left
    head = ('M50 54Q50 42 40 41Q33 41 30 46L21 48Q15 49 15 53Q15 57 21 58'
            'L36 60Q48 61 50 54Z')
    b.append('<path d="%s" fill="#fff"/>' % head)
    b.append(_g('M24 57.4Q34 59 44 57.6M40 44Q46 47 48 52', 0.5))
    b.append(_g(head, 1.2))
    # muzzle: stop, mouth, nose
    b.append(_g('M30 46Q31 49 30 52M17 55.6Q22 56 27 55', 0.7))
    b.append('<path d="M14 51Q15 48.6 18 49.2Q18.6 51.4 16 52.4Q14.4 52.4 14 51Z"/>')
    # closed eye
    b.append(_g('M32.5 48.8Q34.5 50.4 36.5 48.6', 1))
    # long floppy ear, dark
    ear = 'M40 42Q47 40 48 46Q50 54 45 58Q42 53 41 48Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sE)" stroke="#000" '
             'stroke-width="1"/>' % (ear, ear, k))
    # sleep z's
    b.append(_g('M24 34H29L24 39H29M31 25H35L31 29H35M37 17H40L37 20H40', 0.8))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- firs
def _firs():
    k = 'firs'
    rng = random.Random(21)
    defs = _hp(k + 'G', -20, 1.4, 0.5)
    b = []
    b.append(_g(_sky(6, 30, 3.6, 2), 0.5))
    # distant ridge of small firs
    far = ''.join(_fir(x, 34 + rng.uniform(-3, 2), 14, 2.6) for x in range(15, 116, 22))
    b.append(_g(far, 0.5))
    # ground
    gr = 'M4 66Q30 60 60 63T116 62V77H4Z'
    b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sG)"/>' % (gr, gr, k))
    b.append(_g('M4 66Q30 60 60 63T116 62', 0.8))
    # main stand
    for x, t, h, w in ((20, 10, 54, 9), (40, 16, 47, 8), (58, 6, 58, 10), (78, 14, 49, 8.5),
                       (97, 9, 54, 9.5), (110, 24, 38, 6), (8, 26, 38, 6)):
        tri = 'M%s %sL%s %sL%s %sZ' % (_f(x), _f(t), _f(x - w), _f(t + h + 1),
                                         _f(x + w), _f(t + h + 1))
        b.append('<path d="%s" fill="#fff"/>' % tri)
        b.append(_g(_fir(x, t, h, w, 2.2), 0.6))
        b.append(_g('M%s %sV%s' % (_f(x), _f(t + h - 2), _f(t + h + 4)), 1.2))
    # rain
    rain = ''.join('M%s %sl-1.2 4' % (_f(5 + rng.random() * 110), _f(5 + rng.random() * 66))
                   for _ in range(45))
    b.append(_g(rain, 0.5, ' stroke-linecap="round"'))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- river
def _river():
    k = 'river'
    rng = random.Random(4)
    defs = _hp(k + 'X', 30, 1.3, 0.6) + _hp(k + 'Y', -30, 1.6, 0.5)
    b = []
    b.append(_g(_sky(5, 46, 1.2, 1.9), 0.5))
    # crescent moon with halo rings
    b.append('<circle cx="84" cy="18" r="11" fill="#fff"/>')
    b.append('<circle cx="84" cy="18" r="11" fill="none" stroke="#000" stroke-width="0.5" '
             'stroke-dasharray="0.8 1.2"/>')
    b.append('<path d="M84 10A8 8 0 1 0 89.5 23.8A6.5 6.5 0 1 1 84 10Z" fill="#000"/>')
    stars = ''.join('M%s %sh2M%s %sv2' % (_f(x - 1), _f(y), _f(x), _f(y - 1)) for x, y in
                    ((14, 12), (30, 22), (48, 9), (62, 28), (106, 34), (22, 36), (100, 9)))
    b.append('<g stroke="#fff" stroke-width="2.2">%s</g>' % ''.join(
        '<circle cx="%s" cy="%s" r="1.4" fill="#fff" stroke="none"/>' % (x, y) for x, y in
        ((14, 12), (30, 22), (48, 9), (62, 28), (106, 34), (22, 36), (100, 9))))
    b.append(_g(stars, 0.6))
    # gorge walls
    for d in ('M4 52L4 34Q12 30 20 36Q30 40 40 46L52 52Z', 'M116 52V38Q106 36 98 42Q88 46 78 52Z'):
        b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sX)"/>'
                 '<path d="%s" fill="url(#%sY)" stroke="#000" stroke-width="1"/>' % (d, d, k, d, k))
    # water
    b.append('<rect x="4" y="52" width="112" height="25" fill="#fff"/>')
    b.append(_g(_water(rng, 53.5, 76.5, step=1.2, dense=0.8), 0.6))
    # moon glade: broken, wavering strokes widening toward the viewer
    gl = []
    y = 53.6
    i = 0
    while y < 76.5:
        w = 1 + (y - 53) * 0.32
        cx = 84 + rng.uniform(-1.2, 1.2) + (y - 53) * 0.05
        x = cx - w - rng.uniform(0, 1.5)
        while x < cx + w:
            e = min(x + rng.uniform(1.2, 4.5), cx + w + rng.uniform(0, 1.5))
            gl.append('M%s %sH%s' % (_f(x), _f(y), _f(e)))
            x = e + rng.uniform(0.8, 2.2)
        y += 1.2 + rng.uniform(-0.2, 0.5)
        i += 1
    b.append('<path d="M83 52.5H85L92 76.5H76Z" fill="#fff"/>')
    b.append(_g(''.join(gl), 0.6))
    b.append(_g('M4 52H116', 0.8))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- news
def _news():
    """Folded evening paper with a quill laid across it."""
    k = 'news'
    defs = _hp(k + 'D', 45, 1.4, 0.5) + _hp(k + 'H', -45, 1.4, 0.5) + _sp(k + 'S', 2.6)
    b = []
    b.append('<rect x="4" y="4" width="112" height="73" fill="url(#%sS)"/>' % k)
    # shadow beneath the paper
    sh = 'M22 22L100 16L106 70L28 76Z'
    b.append('<path d="%s" fill="url(#%sD)"/>' % (sh, k))
    # paper: front page, folded at the middle
    pg = 'M18 18L96 12L100 64L22 70Z'
    b.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="1.2"/>' % pg)
    b.append(_g('M20 44L98 38', 0.8, ' stroke-dasharray="2 1"'))
    b.append('<path d="M20 44L98 38L100 64L22 70Z" fill="url(#%sH)" opacity="1" '
             'style="mix-blend-mode:normal"/>' % k)
    b.append('<path d="M23 47L97 41.4L99 61L24.6 66.6Z" fill="#fff"/>')
    # masthead
    b.append('<path d="M24 20.6L90 15.6L90.6 22.4L24.6 27.4Z" fill="#000"/>')
    b.append(_g('M30 24.6L84 20.5', 1.6, ' stroke="#fff" stroke-dasharray="3 1.4"'))
    b.append(_g('M24.8 29.4L91 24.4', 0.5))
    # columns of text above and below the fold
    def lines(x0, x1, y0, n, dy=2.2, sl=-0.077):
        return ''.join('M%s %sL%s %s' % (_f(x0), _f(y0 + i * dy - x0 * sl * 0 + 0),
                                         _f(x1), _f(y0 + i * dy + (x1 - x0) * sl))
                       for i in range(n))
    b.append(_g(lines(26, 48, 33, 4) + lines(52, 70, 31.2, 4) + lines(74, 92, 29.8, 4), 0.6))
    b.append('<path d="M52 31.2L70 29.8L70.6 38L52.6 39.4Z" fill="#fff" stroke="#000" stroke-width="0.6"/>')
    b.append(_g(lines(54, 68, 32.6, 3, 2.2), 0.5))
    b.append(_g(lines(27, 50, 49, 7, 2.3) + lines(54, 74, 47.2, 7, 2.3) + lines(78, 96, 45.8, 7, 2.3), 0.5))
    # quill across the page, nib at lower left
    sh_ = 'M30 74L104 6'
    b.append(_g(sh_, 1.2))
    barbs = []
    for i in range(26):
        t = 0.22 + i * 0.03
        x, y = 30 + 74 * t, 74 - 68 * t
        ln = 7 * math.sin(math.pi * (t - 0.2) / 0.8) + 1
        barbs.append('M%s %sl%s %s' % (_f(x), _f(y), _f(ln * 0.95), _f(ln * 0.4)))
        barbs.append('M%s %sl%s %s' % (_f(x), _f(y), _f(-ln * 0.4), _f(-ln * 0.95)))
    vane = ('M44 61Q60 34 104 6Q96 30 56 62Z')
    b.append('<path d="%s" fill="#fff"/>' % vane)
    b.append(_g(''.join(barbs), 0.5))
    b.append(_g(sh_, 1.2))
    b.append('<path d="M30 74L33.4 68.6L35 70.2Z"/>')
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- solar
def _solar():
    """Rooftop array under a radiant sun, with firs."""
    k = 'solar'
    defs = (_hp(k + 'R', 0, 1.3, 0.6) + _hp(k + 'W', 90, 1.4, 0.5) + _hp(k + 'G', -20, 1.6, 0.5))
    b = []
    # radiant sun: alternating long and short rays
    cx, cy = 30, 22
    rays = []
    for i in range(32):
        a = 2 * math.pi * i / 32
        r1 = 21 if i % 2 == 0 else 15
        rays.append('M%s %sL%s %s' % (_f(cx + 10 * math.cos(a)), _f(cy + 10 * math.sin(a)),
                                      _f(cx + r1 * math.cos(a)), _f(cy + r1 * math.sin(a))))
    b.append(_g(''.join(rays), 0.6))
    b.append('<circle cx="30" cy="22" r="8" fill="#fff" stroke="#000" stroke-width="1.2"/>')
    b.append('<circle cx="30" cy="22" r="5.6" fill="none" stroke="#000" stroke-width="0.5" '
             'stroke-dasharray="1 1"/>')
    # ground
    gr = 'M4 70Q40 66 70 68T116 67V77H4Z'
    b.append('<path d="%s" fill="url(#%sG)"/>' % (gr, k))
    b.append(_g('M4 70Q40 66 70 68T116 67', 0.8))
    # house: walls and gable end
    b.append('<path d="M46 50H96V70H46Z" fill="url(#%sW)" stroke="#000" stroke-width="1"/>' % k)
    b.append('<path d="M96 50L104 40L112 50V70H96Z" fill="#fff" stroke="#000" stroke-width="1"/>')
    b.append(_g(''.join('M%s %sH%s' % (_f(97), _f(y), _f(111)) for y in range(52, 70, 2)), 0.5))
    b.append('<rect x="101" y="58" width="6" height="12" fill="#000"/>')
    b.append('<rect x="56" y="56" width="8" height="7" fill="#fff" stroke="#000" stroke-width="0.8"/>'
             '<rect x="76" y="56" width="8" height="7" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    b.append(_g('M60 56V63M56 59.5H64M80 56V63M76 59.5H84', 0.5))
    # roof slope (parallelogram) carrying the panels
    roof = 'M42 51L52 36H104L96 51Z'
    b.append('<path d="%s" fill="#fff" stroke="#000" stroke-width="1.2"/>' % roof)
    # panel grid: 2 rows x 5 columns, cells cross-hatched with a white sun glint
    for r in range(2):
        y0, y1 = 38.5 + r * 6, 43.5 + r * 6
        for c in range(5):
            def px(y, u):
                # x along slanted roof at row y
                t = (y - 36) / 15.0
                left = 52 - 10 * t + 1.5
                right = 104 - 8 * t - 2
                return left + (right - left) * u
            u0, u1 = c / 5.0 + 0.01, (c + 1) / 5.0 - 0.01
            cell = 'M%s %sL%s %sL%s %sL%s %sZ' % (_f(px(y0, u0)), _f(y0), _f(px(y0, u1)), _f(y0),
                                                 _f(px(y1, u1)), _f(y1), _f(px(y1, u0)), _f(y1))
            b.append('<path d="%s" fill="url(#%sR)" stroke="#000" stroke-width="0.8"/>' % (cell, k))
            mx = (px(y0, u0) + px(y0, u1)) / 2
            b.append(_g('M%s %sL%s %s' % (_f(mx - 1.5), _f(y1 - 0.4), _f(mx + 2.5), _f(y0 + 0.4)),
                        0.6, ' stroke="#fff"'))
    # chimney
    b.append('<rect x="88" y="30" width="5" height="6" fill="#fff" stroke="#000" stroke-width="0.8"/>')
    # firs either side
    for x, t, h, w in ((10, 36, 34, 6), (18, 44, 26, 5), (116, 30, 40, 6)):
        tri = 'M%s %sL%s %sL%s %sZ' % (_f(x), _f(t), _f(x - w), _f(t + h + 1), _f(x + w), _f(t + h + 1))
        b.append('<path d="%s" fill="#fff"/>' % tri)
        b.append(_g(_fir(x, t, h, w, 1.8), 0.6))
    return _svg(defs, ''.join(b))


# ---------------------------------------------------------------- lotus
def _lotus():
    """Thai lotus in bloom on water, flanked by lai-thai flame flourishes."""
    k = 'lotus'
    rng = random.Random(8)
    defs = _hp(k + 'P', 75, 1.2, 0.5) + _hp(k + 'L', -15, 1.4, 0.5)
    b = []
    # water
    b.append(_g(_water(rng, 60, 76.5, step=1.5), 0.5))
    # lily pads
    for cx, cy, rx in ((26, 64, 13), (94, 65, 12)):
        pad = 'M%s %sA%s %s 0 1 1 %s %sL%s %sZ' % (
            _f(cx + 1), _f(cy - 3.5), _f(rx), _f(rx * 0.28), _f(cx - 1), _f(cy - 3.5), _f(cx), _f(cy))
        b.append('<path d="%s" fill="#fff"/><path d="%s" fill="url(#%sL)" stroke="#000" '
                 'stroke-width="0.9"/>' % (pad, pad, k))
    # stem
    b.append(_g('M60 64Q58 58 60 54', 1.2))
    # petals: back row then front row, pointed flame-like tips
    def petal(ang, ln, wd, base=(60, 56)):
        bx, by = base
        a = math.radians(ang - 90)
        tx, ty = bx + ln * math.cos(a), by + ln * math.sin(a)
        nx, ny = -math.sin(a) * wd, math.cos(a) * wd
        mx, my = bx + ln * 0.5 * math.cos(a), by + ln * 0.5 * math.sin(a)
        return 'M%s %sQ%s %s %s %sQ%s %s %s %sZ' % (
            _f(bx), _f(by), _f(mx + nx), _f(my + ny), _f(tx), _f(ty),
            _f(mx - nx), _f(my - ny), _f(bx), _f(by))
    for ang, ln, wd, shade in ((-62, 20, 6, 1), (62, 20, 6, 1), (-34, 26, 6.5, 0), (34, 26, 6.5, 0),
                               (-14, 30, 6.5, 1), (14, 30, 6.5, 1), (0, 34, 7, 0)):
        p = petal(ang, ln, wd)
        b.append('<path d="%s" fill="#fff"/>' % p)
        if shade:
            b.append('<path d="%s" fill="url(#%sP)"/>' % (p, k))
        b.append(_g(p, 1))
    # vein lines on unshaded petals
    b.append(_g('M60 54V28M60 54L50 36M60 54L70 36', 0.5))
    # receptacle cup
    b.append('<path d="M50 56Q60 62 70 56Q60 58 50 56Z" fill="#000"/>')
    # lai-thai flame flourishes: spiral curl with flicked flame tips
    def kanok(sx, d):
        s = lambda x: _f(60 + d * (x - 60))
        return ('M%s 50Q%s 38 %s 36Q%s 34 %s 40Q%s 44 %s 41Q%s 38 %s 39'
                'M%s 36Q%s 26 %s 18M%s 40Q%s 33 %s 28M%s 50Q%s 47 %s 44'
                % (s(sx), s(sx - 10), s(sx - 18), s(sx - 24), s(sx - 22), s(sx - 20), s(sx - 17),
                   s(sx - 16), s(sx - 18),
                   s(sx - 18), s(sx - 22), s(sx - 16), s(sx - 22), s(sx - 28), s(sx - 26),
                   s(sx - 4), s(sx - 10), s(sx - 14)))
    fl = kanok(44, 1) + kanok(44, -1)
    b.append(_g(fl, 1))
    # flame tips as small solid teardrops
    for d in (1, -1):
        for x, y, r in ((44 - 28, 18, 1.6), (44 - 30, 26, 1.2), (44 - 18, 44, 1.2)):
            xx = 60 + d * (x - 60)
            b.append('<path d="M%s %sQ%s %s %s %sQ%s %s %s %sZ"/>' % (
                _f(xx), _f(y - 2.6 * r), _f(xx + r), _f(y), _f(xx), _f(y + r),
                _f(xx - r), _f(y), _f(xx), _f(y - 2.6 * r)))
    # small dotted aura above the bloom
    b.append(''.join('<circle cx="%s" cy="%s" r="0.6"/>' % (_f(60 + 30 * math.cos(a)), _f(46 - 34 * math.sin(a)))
                     for a in [math.pi * (0.25 + i * 0.05) for i in range(11)]))
    return _svg(defs, ''.join(b))


VIGNETTES = {
    'bridge': _bridge(),
    'hood': _hood(),
    'cranes': _cranes(),
    'heron': _heron(),
    'drums': _drums(),
    'jazz': _jazz(),
    'record': _record(),
    'dog': _dog(),
    'firs': _firs(),
    'river': _river(),
    'news': _news(),
    'solar': _solar(),
    'lotus': _lotus(),
}


def demo(path='/tmp/claude-0/shots/team/vignettes_demo.html'):
    cells = []
    for key, svg in VIGNETTES.items():
        big = svg.replace('width="120" height="80"', 'width="240" height="160"', 1)
        cells.append('<div class="c"><div class="k">%s &middot; %d B</div>%s %s</div>'
                     % (key, len(svg.encode()), svg, big))
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'body{margin:8px;background:#fff;font:11px Georgia,serif}'
            '.g{display:grid;grid-template-columns:375px 375px}.c{white-space:nowrap;margin-bottom:6px}'
            '.c svg{vertical-align:top;margin-right:6px}.k{margin:2px 0}'
            '</style></head><body><div class="g">%s</div></body></html>' % ''.join(cells))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write(html)
    return path


if __name__ == '__main__':
    print(demo())
