"""Engraved ornaments for the Kindle editions: a shared kit (bands, corners, fleurons,
initials, the beaded cartouche and its wings) and the Morning Edition's plates.
Generated from /tmp/claude-0/design/{orn,vig,gen_css}.py by apply.py.

    write_plates(out)  writes out/orn/*.svg (section plates, card medallions,
                       the cover panorama, the crest, weather glyphs)
    DESIGN_CSS         appended to EINK_CSS: the shared kit, then rules scoped to html.kme
"""

import math
import os
import re
import urllib.parse

K = "#000"


def _level(hx):
    """Nearest of the panel's 16 exact greys (#000, #111 ... #fff); colours become their luma."""
    h = hx.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return hx
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    v = round((.299 * r + .587 * g + .114 * b) / 17)
    return "#" + "0123456789abcdef"[v] * 3


def snap(doc, inverse=False):
    """Normalise an SVG to the e-ink rules (eink/eink-guide.md): strokes on whole device pixels
    (0.5, 1, 1.5 ... CSS; white strokes on black at least 1), hatch tiles on whole device pixels,
    every grey one of the 16 exact levels."""
    def sw(m):
        v = float(m.group(1))
        q = max(.5, round(v * 2) / 2)
        return f'stroke-width="{q:g}"'
    doc = re.sub(r'stroke-width="([\d.]+)"', sw, doc)
    doc = re.sub(r'stroke-width:([\d.]+)', lambda m: f"stroke-width:{max(.5, round(float(m.group(1)) * 2) / 2):g}", doc)
    if inverse:
        doc = re.sub(r'(stroke="#fff"[^>]*?)stroke-width="0?\.5"', r'\1stroke-width="1"', doc)
        doc = re.sub(r'stroke-width="0?\.5"([^>]*?stroke="#fff")', r'stroke-width="1"\1', doc)

    def tile(m):
        w, h = float(m.group(2)), float(m.group(4))
        if max(w, h) > 6:
            return m.group(0)
        return f'{m.group(1)}{max(1, round(w * 2) / 2):g}{m.group(3)}{max(1, round(h * 2) / 2):g}"'
    doc = re.sub(r'(<pattern\b[^>]*?\swidth=")([\d.]+)("[^>]*?\sheight=")([\d.]+)"', tile, doc)
    doc = re.sub(r'((?:fill|stroke|stop-color)=")(#[0-9a-fA-F]{3,6})(")', lambda m: m.group(1) + _level(m.group(2)) + m.group(3), doc)
    return doc


def uri(svg):
    svg = snap(svg)
    return 'url("data:image/svg+xml,' + urllib.parse.quote(svg, safe=" =:/,;'()-.") + '")'


def svg(w, h, body, defs=""):
    # 300 ppi at DPR 2: half a CSS pixel is one crisp device pixel, the finest line the panel draws
    body = re.sub(r'stroke-width="(0?\.\d+)"', lambda m: f'stroke-width="{max(.5, float(m.group(1))):g}"', body)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{HATCH}{defs}</defs>{body}</svg>')


# Hatching: engraved shading at a 3 px pitch, never finer.
HATCH = (
    '<pattern id="h1" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
    '<line x1="0" y1="0" x2="0" y2="3" stroke="#000" stroke-width="1"/></pattern>'
    '<pattern id="h2" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
    '<line x1="0" y1="0" x2="0" y2="3" stroke="#000" stroke-width="1"/></pattern>'
    '<pattern id="hh" width="4" height="3" patternUnits="userSpaceOnUse">'
    '<line x1="0" y1="1.5" x2="4" y2="1.5" stroke="#000" stroke-width="1"/></pattern>'
    '<pattern id="hv" width="3" height="4" patternUnits="userSpaceOnUse">'
    '<line x1="1" y1="0" x2="1" y2="4" stroke="#000" stroke-width="1"/></pattern>'
    '<pattern id="hx" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
    '<path d="M0 0V4M0 0H4" stroke="#000" stroke-width="1"/></pattern>'
)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pts(p):
    return " ".join(f"{f(x)},{f(y)}" for x, y in p)


# ---------------------------------------------------------------- scrolls
def spiral(cx, cy, R, turns=1.55, start=0.0, cw=1, leaf="acanthus", leaves=True, end=0.17, wid=2.2):
    """A foliate scroll: a stem that spirals in, with leaves on its outer edge."""
    n = int(80 * turns)
    tot = turns * 2 * math.pi
    k = -math.log(end) / tot
    P = []
    for i in range(n + 1):
        t = tot * i / n
        r = R * math.exp(-k * t)
        a = start + cw * t
        P.append((cx + r * math.cos(a), cy + r * math.sin(a), r, a))
    out = [f'<polyline points="{pts([(x, y) for x, y, _, _ in P])}" fill="none" stroke="#000" stroke-width="{wid}" stroke-linecap="round"/>']
    inner = [(cx + (r - 3.2) * math.cos(a), cy + (r - 3.2) * math.sin(a)) for x, y, r, a in P if r > 7]
    if len(inner) > 2:
        out.append(f'<polyline points="{pts(inner)}" fill="none" stroke="#000" stroke-width=".8"/>')
    x, y, r, a = P[-1]
    out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(max(1.8, R * .06))}" fill="#000"/>')
    if leaves:
        step = 0.62
        t = 0.25
        while t < tot * 0.72:
            r = R * math.exp(-k * t)
            a = start + cw * t
            px, py = cx + r * math.cos(a), cy + r * math.sin(a)
            nx, ny = math.cos(a), math.sin(a)                     # outward
            tx, ty = -math.sin(a) * cw, math.cos(a) * cw          # direction of travel
            L = max(5.0, r * 0.42)
            out.append(LEAVES[leaf](px, py, nx, ny, tx, ty, L))
            t += step
    return "".join(out)


def _acanthus(px, py, nx, ny, tx, ty, L):
    tip = (px + nx * L * .95 - tx * L * .75, py + ny * L * .95 - ty * L * .75)
    c1 = (px + nx * L * .9 + tx * L * .35, py + ny * L * .9 + ty * L * .35)
    b2 = (px - tx * L * .45, py - ty * L * .45)
    c2 = (px + nx * L * .25 - tx * L * .6, py + ny * L * .25 - ty * L * .6)
    lobe = (px + nx * L * .62 + tx * L * .05, py + ny * L * .62 + ty * L * .05)
    d = (f"M{f(px)},{f(py)} Q{f(c1[0])},{f(c1[1])} {f(lobe[0])},{f(lobe[1])} "
         f"Q{f(lobe[0] + nx * L * .3)},{f(lobe[1] + ny * L * .3)} {f(tip[0])},{f(tip[1])} "
         f"Q{f(c2[0])},{f(c2[1])} {f(b2[0])},{f(b2[1])} Z")
    mid = (f"M{f(px - tx * L * .1)},{f(py - ty * L * .1)} Q{f(px + nx * L * .55)},{f(py + ny * L * .55)} "
           f"{f(tip[0])},{f(tip[1])}")
    hat = []
    for s in (.3, .5):
        a0 = (px + nx * L * s - tx * L * .05, py + ny * L * s - ty * L * .05)
        a1 = (a0[0] - tx * L * .28 + nx * L * .12, a0[1] - ty * L * .28 + ny * L * .12)
        hat.append(f"M{f(a0[0])},{f(a0[1])}L{f(a1[0])},{f(a1[1])}")
    return (f'<path d="{d}" fill="#fff" stroke="#000" stroke-width="1.1" stroke-linejoin="round"/>'
            f'<path d="{mid} {" ".join(hat)}" fill="none" stroke="#000" stroke-width=".8"/>'
            f'<circle cx="{f(tip[0])}" cy="{f(tip[1])}" r="1.2" fill="#000"/>')


def _kranok(px, py, nx, ny, tx, ty, L):
    """Thai kranok: a flame leaf, swept back, with a hooked tip."""
    L *= 1.15
    tip = (px + nx * L * 1.0 - tx * L * .55, py + ny * L * 1.0 - ty * L * .55)
    hook = (tip[0] - tx * L * .28 - nx * L * .12, tip[1] - ty * L * .28 - ny * L * .12)
    c1 = (px + nx * L * .7 + tx * L * .45, py + ny * L * .7 + ty * L * .45)
    c2 = (px + nx * L * .35 - tx * L * .55, py + ny * L * .35 - ty * L * .55)
    b2 = (px - tx * L * .4, py - ty * L * .4)
    d = (f"M{f(px)},{f(py)} C{f(c1[0])},{f(c1[1])} {f(tip[0] + tx * L * .3)},{f(tip[1] + ty * L * .3)} {f(tip[0])},{f(tip[1])} "
         f"Q{f(hook[0] + nx * L * .2)},{f(hook[1] + ny * L * .2)} {f(hook[0])},{f(hook[1])} "
         f"Q{f(c2[0])},{f(c2[1])} {f(b2[0])},{f(b2[1])} Z")
    inner = (f"M{f(px + nx * L * .15)},{f(py + ny * L * .15)} Q{f(px + nx * L * .6 + tx * L * .1)},{f(py + ny * L * .6 + ty * L * .1)} "
             f"{f(tip[0] - nx * L * .12)},{f(tip[1] - ny * L * .12)}")
    return (f'<path d="{d}" fill="#000" stroke="#000" stroke-width=".8" stroke-linejoin="round"/>'
            f'<path d="{inner}" fill="none" stroke="#fff" stroke-width="1.1"/>')


def _nouveau(px, py, nx, ny, tx, ty, L):
    tip = (px + nx * L * 1.1 - tx * L * .2, py + ny * L * 1.1 - ty * L * .2)
    c1 = (px + nx * L * .6 + tx * L * .5, py + ny * L * .6 + ty * L * .5)
    c2 = (px + nx * L * .6 - tx * L * .55, py + ny * L * .6 - ty * L * .55)
    d = f"M{f(px)},{f(py)} Q{f(c1[0])},{f(c1[1])} {f(tip[0])},{f(tip[1])} Q{f(c2[0])},{f(c2[1])} {f(px)},{f(py)} Z"
    return (f'<path d="{d}" fill="url(#h1)" stroke="#000" stroke-width="1.1"/>'
            f'<path d="M{f(px)},{f(py)} L{f(tip[0])},{f(tip[1])}" stroke="#000" stroke-width=".8"/>')


LEAVES = {"acanthus": _acanthus, "kranok": _kranok, "nouveau": _nouveau}


def kranok_flame(x, y, s=1.0, flip=False, fill="#000", line="#fff"):
    """One upright kranok flame, base at (x, y), about 30*s tall."""
    sx = -s if flip else s
    d = "M-6,0 C-9,-8 -4,-14 0,-18 C3,-21 3,-26 -1,-30 C6,-28 9,-21 6,-15 C4,-11 6,-5 7,0 Z"
    il = "M-2,-2 C-4,-8 0,-12 2,-15 C4,-18 4,-22 2,-25"
    return (f'<g transform="translate({f(x)},{f(y)}) scale({f(sx)},{f(s)})">'
            f'<path d="{d}" fill="{fill}" stroke="#000" stroke-width=".8"/>'
            f'<path d="{il}" fill="none" stroke="{line}" stroke-width="1.1"/></g>')


def prajam(x, y, r, fill="#000", line="#fff"):
    """Lai prajam yam: the four-petal Thai flower in a lozenge."""
    p = r * .55
    return (f'<path d="M{f(x)},{f(y - r)} L{f(x + r)},{f(y)} L{f(x)},{f(y + r)} L{f(x - r)},{f(y)} Z" fill="{fill}"/>'
            f'<path d="M{f(x)},{f(y - p)} Q{f(x + p * .5)},{f(y - p * .1)} {f(x)},{f(y)} Q{f(x - p * .5)},{f(y - p * .1)} {f(x)},{f(y - p)} Z '
            f'M{f(x)},{f(y + p)} Q{f(x + p * .5)},{f(y + p * .1)} {f(x)},{f(y)} Q{f(x - p * .5)},{f(y + p * .1)} {f(x)},{f(y + p)} Z '
            f'M{f(x - p)},{f(y)} Q{f(x - p * .1)},{f(y - p * .5)} {f(x)},{f(y)} Q{f(x - p * .1)},{f(y + p * .5)} {f(x - p)},{f(y)} Z '
            f'M{f(x + p)},{f(y)} Q{f(x + p * .1)},{f(y - p * .5)} {f(x)},{f(y)} Q{f(x + p * .1)},{f(y + p * .5)} {f(x + p)},{f(y)} Z" '
            f'fill="none" stroke="{line}" stroke-width=".9"/>')


# ---------------------------------------------------------------- wings
def sheath(cx, cy, R, k, start, cw, t0, t1, W, lobes=3, side=1, shade=True):
    """An acanthus leaf that sheathes the stem between t0 and t1 and flares out
    in pointed lobes, ending in a tip that curls back: the engraver's scroll leaf."""
    N = 28
    stem, outer = [], []
    for i in range(N + 1):
        s = i / N
        t = t0 + (t1 - t0) * s
        r = R * math.exp(-k * t)
        a = start + cw * t
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        nx, ny = math.cos(a) * side, math.sin(a) * side
        u = ((lobes * s) % 1) ** .75
        tri = math.sqrt(max(0, 1 - (2 * u - 1) ** 2))
        env = math.sin(math.pi * min(1, s * 1.1)) ** .5 if s < .88 else (1 - s) * 2.4
        w = W * (r / R) * env * (.5 + .55 * tri)
        stem.append((px, py))
        outer.append((px + nx * w, py + ny * w, px, py, nx, ny, w))
    tx, ty = stem[-1][0] - stem[-2][0], stem[-1][1] - stem[-2][1]
    L = math.hypot(tx, ty) or 1
    tx, ty = tx / L, ty / L
    ex, ey = stem[-1]
    tip = (ex + tx * W * .8 * math.exp(-k * t1) + outer[-1][4] * W * .6 * math.exp(-k * t1),
           ey + ty * W * .8 * math.exp(-k * t1) + outer[-1][5] * W * .6 * math.exp(-k * t1))
    poly = stem + [tip] + [(o[0], o[1]) for o in reversed(outer)]
    out = [f'<path d="M{pts(poly).replace(" ", " L")} Z" fill="#fff" stroke="#000" stroke-width="1.2" stroke-linejoin="round"/>']
    if shade:
        half = stem + [(o[2] + o[4] * o[6] * .42, o[3] + o[5] * o[6] * .42) for o in reversed(outer)]
        out.append(f'<path d="M{pts(half).replace(" ", " L")} Z" fill="url(#h1)"/>')
    veins = []
    for j in range(lobes):
        i = int(N * (j + .5) / lobes)
        o = outer[i]
        veins.append(f"M{f(o[2])},{f(o[3])} Q{f(o[2] + o[4] * o[6] * .5 - tx * 3)},{f(o[3] + o[5] * o[6] * .5 - ty * 3)} {f(o[0])},{f(o[1])}")
    mid = [(o[2] + o[4] * o[6] * .55, o[3] + o[5] * o[6] * .55) for o in outer[2:-3]]
    out.append(f'<path d="{" ".join(veins)} M{pts(mid).replace(" ", " L")}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(out)


def scroll(cx, cy, R, turns=1.6, start=0.0, cw=1, end=.16, wid=2.4, leafw=.5, n=None, kind="acanthus"):
    """A full foliate scroll: stem, overlapping sheath leaves, inner bud."""
    tot = turns * 2 * math.pi
    k = -math.log(end) / tot
    out = [spiral(cx, cy, R, turns, start, cw, leaves=False, end=end, wid=wid)]
    spans = n or int(turns * 3.2)
    span = tot * .78 / spans
    for i in range(spans):
        t0 = 0.05 + i * span
        if kind == "kranok":
            out.append(sheath_kranok(cx, cy, R, k, start, cw, t0, t0 + span * 1.25, R * leafw))
        else:
            out.append(sheath(cx, cy, R, k, start, cw, t0, t0 + span * 1.3, R * leafw, lobes=3 if i < spans - 2 else 2))
    # small inner leaves on the inside of the first turn
    for i in range(2):
        t0 = 0.6 + i * 1.6
        out.append(sheath(cx, cy, R, k, start, cw, t0, t0 + .9, R * .22, lobes=2, side=-1, shade=False))
    return "".join(out)


def sheath_kranok(cx, cy, R, k, start, cw, t0, t1, W):
    """Kranok flame leaf on a scroll: black niello flame, white inner line, hooked tip."""
    N = 22
    stem, outer = [], []
    for i in range(N + 1):
        s = i / N
        t = t0 + (t1 - t0) * s
        r = R * math.exp(-k * t)
        a = start + cw * t
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        nx, ny = math.cos(a), math.sin(a)
        w = W * (r / R) * (math.sin(math.pi * s * .92) ** .8) * (1 + .6 * s)
        stem.append((px, py))
        outer.append((px + nx * w, py + ny * w, px, py, nx, ny, w))
    o = outer[-1]
    back = outer[int(N * .7)]
    hook = (o[0] - (o[0] - back[0]) * .35 + o[4] * 3, o[1] - (o[1] - back[1]) * .35 + o[5] * 3)
    poly = stem + [(o[0] + o[4] * o[6] * .4, o[1] + o[5] * o[6] * .4), hook] + [(q[0], q[1]) for q in reversed(outer[:-1])]
    inner = [(q[2] + q[4] * q[6] * .45, q[3] + q[5] * q[6] * .45) for q in outer[3:-2]]
    return (f'<path d="M{pts(poly).replace(" ", " L")} Z" fill="#000" stroke="#000" stroke-width="1" stroke-linejoin="round"/>'
            f'<path d="M{pts(inner).replace(" ", " L")}" fill="none" stroke="#fff" stroke-width="1.6"/>')


def tendril(d, w=1.6):
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="{w}" stroke-linecap="round"/>'


def wing_acanthus():
    return (tendril("M188,75 C176,75 168,62 160,52 C150,40 136,30 116,28", 2.4)
            + tendril("M188,80 C170,86 164,110 140,120 C124,126 104,124 92,118", 1.6)
            + scroll(112, 76, 50, turns=1.55, start=-math.pi * .48, cw=-1, leafw=.62)
            + scroll(34, 72, 26, turns=1.45, start=math.pi * .55, cw=-1, leafw=.66)
            + tendril("M62,76 C70,96 80,110 92,118", 1.6)
            + spiral(158, 120, 12, turns=1.3, start=math.pi * .9, cw=1, leaves=False, wid=1.6)
            + spiral(170, 30, 10, turns=1.3, start=math.pi * .2, cw=-1, leaves=False, wid=1.6)
            + sheath(158, 120, 12, -math.log(.17) / (1.3 * 2 * math.pi), math.pi * .9, 1, .1, 2.2, 7, lobes=3)
            + prajam(64, 26, 6) + prajam(64, 126, 5))


def wing_kranok():
    return (tendril("M188,75 C176,75 168,62 160,52 C150,40 136,30 116,28", 2.4)
            + tendril("M188,80 C170,86 164,110 140,120 C124,126 104,124 92,118", 1.6)
            + scroll(112, 76, 50, turns=1.55, start=-math.pi * .48, cw=-1, leafw=.36, kind="kranok", n=6)
            + scroll(34, 72, 26, turns=1.45, start=math.pi * .55, cw=-1, leafw=.5, kind="kranok")
            + kranok_flame(170, 140, .5) + kranok_flame(156, 140, .42, True)
            + prajam(64, 26, 7) + prajam(64, 126, 6) + prajam(10, 128, 5) + prajam(10, 22, 5))


def wing_nouveau():
    out = []
    curves = [("M190,72 C150,70 150,16 108,18 C70,20 74,60 44,54 C26,50 22,30 8,28", 2.6),
              ("M190,80 C150,84 142,130 102,128 C70,126 70,96 42,100 C26,102 20,118 6,120", 2.2),
              ("M190,76 C160,76 140,56 120,62 C100,68 104,90 84,90 C66,90 64,74 52,74", 1.4),
              ("M160,50 C140,40 132,64 108,56 C94,52 96,38 82,36", 1.1),
              ("M160,104 C138,112 128,90 106,100 C94,106 96,118 82,120", 1.1)]
    for d, w in curves:
        out.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="{w}" stroke-linecap="round"/>')
    lily = ('<path d="M0,0 C-8,-6 -8,-18 0,-26 C8,-18 8,-6 0,0 Z" fill="#fff" stroke="#000" stroke-width="1.3"/>'
            '<path d="M0,0 C-14,-4 -18,-14 -14,-22 C-8,-14 -4,-8 0,0 Z M0,0 C14,-4 18,-14 14,-22 C8,-14 4,-8 0,0 Z" fill="url(#h1)" stroke="#000" stroke-width="1.1"/>'
            '<path d="M0,-2 V-20" stroke="#000" stroke-width="1"/>')
    for x, y, a in ((8, 28, -70), (6, 120, -110), (52, 74, -90)):
        out.append(f'<g transform="translate({x},{y}) rotate({a})">{lily}</g>')
    leaf = ('<path d="M0,0 C6,-12 22,-16 34,-10 C22,-4 10,4 0,0 Z" fill="url(#h2)" stroke="#000" stroke-width="1.2"/>'
            '<path d="M0,0 C10,-6 22,-10 34,-10" fill="none" stroke="#000" stroke-width="1"/>')
    for x, y, a in ((108, 18, 200), (102, 128, 160), (44, 54, 220), (42, 100, 140), (140, 36, 170), (136, 114, 190), (84, 90, 30)):
        out.append(f'<g transform="translate({x},{y}) rotate({a})">{leaf}</g>')
    for x, y in ((82, 36), (82, 120), (160, 50), (160, 104)):
        out.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#fff" stroke="#000" stroke-width="1.3"/><circle cx="{x}" cy="{y}" r="1.8" fill="#000"/>')
    return "".join(out)


def wing_deco():
    """Jazz-label deco: a black-and-white sunburst fan, stepped bars, a ziggurat end."""
    out = ['<clipPath id="fan"><path d="M190,75 L30,14 L30,136 Z"/></clipPath><g clip-path="url(#fan)">']
    cx, cy = 190, 75
    n = 15
    for i in range(n):
        a0 = math.pi - .42 + .84 * i / n
        a1 = math.pi - .42 + .84 * (i + .45) / n
        r0 = 66
        out.append(f'<path d="M{f(cx + r0 * math.cos(a0))},{f(cy + r0 * math.sin(a0))} L{f(cx + 200 * math.cos(a0))},{f(cy + 200 * math.sin(a0))} L{f(cx + 200 * math.cos(a1))},{f(cy + 200 * math.sin(a1))} L{f(cx + r0 * math.cos(a1))},{f(cy + r0 * math.sin(a1))} Z" fill="#000"/>')
    out.append('</g>')
    for r in (60, 116, 122):
        out.append(f'<path d="M{f(cx + r * math.cos(math.pi - .44))},{f(cy + r * math.sin(math.pi - .44))} A{r},{r} 0 0 0 {f(cx + r * math.cos(math.pi + .44))},{f(cy + r * math.sin(math.pi + .44))}" fill="none" stroke="{'#000' if r == 60 else '#fff'}" stroke-width="{4 if r == 122 else 1.6}"/>')
    out.append('<path d="M30,14 L190,75 L30,136" fill="none" stroke="#000" stroke-width="1.6"/>')
    for i, (x, h) in enumerate(((22, 122), (14, 100), (6, 76))):
        out.append(f'<rect x="{x}" y="{75 - h / 2}" width="4" height="{h}" fill="#000"/>')
    for y in (10, 140):
        out.append(f'<rect x="40" y="{y - 1}" width="120" height="2" fill="#000"/>')
    out.append(prajam(8, 18, 5) + prajam(8, 132, 5))
    return "".join(out)


def wing_woodcut():
    out = []
    wave = ('<path d="M-46,20 C-40,-12 -8,-28 20,-16 C34,-10 34,8 20,10 C8,12 4,0 12,-3 C-6,-8 -22,4 -26,20 Z" fill="#000"/>'
            '<path d="M-36,16 C-30,-6 -8,-18 14,-10 M-28,18 C-22,2 -8,-8 8,-4 M-18,19 C-14,10 -6,4 4,4" fill="none" stroke="#fff" stroke-width="1.3"/>'
            '<path d="M20,-16 C28,-22 36,-18 38,-12 M24,-12 C30,-16 34,-14 36,-10" fill="none" stroke="#000" stroke-width="1.2"/>')
    for x, y, s in ((154, 112, 1.05), (100, 120, .9), (50, 112, .78), (138, 56, .85), (82, 52, .7), (34, 60, .55), (172, 22, .4), (112, 18, .35)):
        out.append(f'<g transform="translate({x},{y}) scale({s})">{wave}</g>')
    for y in (128, 134, 140):
        for x in range(2 + (y % 3) * 3, 186, 10):
            out.append(f'<line x1="{x}" y1="{y}" x2="{x + 6}" y2="{y}" stroke="#000" stroke-width="1.2"/>')
    for x, y in ((60, 30), (20, 28), (186, 92)):
        out.append(f'<circle cx="{x}" cy="{y}" r="2" fill="#000"/>')
    return "".join(out)


def wing_laurel():
    """Victor's laurel: two branches sweep out from the oval, paired leaves, berries, a ribbon."""
    out = []
    for sgn in (-1, 1):
        P0, P1, P2 = (186, 75 + sgn * 10), (120, 75 + sgn * 70), (14, 75 + sgn * 30)
        pts_ = []
        for i in range(31):
            t = i / 30
            x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0]
            y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]
            pts_.append((x, y))
        out.append(f'<polyline points="{pts(pts_)}" fill="none" stroke="#000" stroke-width="2"/>')
        for i in range(2, 30, 3):
            (x0, y0), (x1, y1) = pts_[i], pts_[i + 1]
            a = math.degrees(math.atan2(y1 - y0, x1 - x0))
            for side, fill in ((1, "#000"), (-1, "url(#h1)")):
                out.append(f'<g transform="translate({f(x0)},{f(y0)}) rotate({f(a + 180 + side * 38)})">'
                           f'<path d="M0,0 C4,-6 14,-6 20,0 C14,6 4,6 0,0 Z" fill="{fill}" stroke="#000" stroke-width="1"/>'
                           f'<path d="M2,0 H18" stroke="{"#fff" if fill == "#000" else "#000"}" stroke-width="1"/></g>')
            if i % 6 == 2:
                out.append(f'<circle cx="{f(x0 + 6)}" cy="{f(y0 - sgn * 10)}" r="2.4" fill="#fff" stroke="#000" stroke-width="1.2"/>')
    out.append('<path d="M186,75 C176,60 166,62 168,72 C170,80 180,80 186,75 Z M186,75 C176,90 166,88 168,78" fill="#fff" stroke="#000" stroke-width="1.4"/>')
    return "".join(out)


def wing_guilloche():
    """Banknote guilloche: phase-shifted waves in a tapering ribbon, a rosette at the end."""
    out = []
    def env(x):
        return 14 + 40 * ((x - 34) / 152) ** 1.3 if x > 34 else 14
    for k in range(6):
        ph = k * math.pi / 3
        P = []
        x = 34.0
        while x <= 188:
            e = env(x)
            P.append((x, 75 + e * .92 * math.sin(x * .16 + ph)))
            x += 1.5
        out.append(f'<polyline points="{pts(P)}" fill="none" stroke="#000" stroke-width="1"/>')
    for sgn in (-1, 1):
        P = [(x, 75 + sgn * env(x)) for x in range(34, 189, 2)]
        out.append(f'<polyline points="{pts(P)}" fill="none" stroke="#000" stroke-width="1.8"/>')
    # a hypotrochoid rosette
    R, r, d = 22, 6.6, 10
    P = []
    for i in range(361):
        t = i * math.pi / 30
        P.append((30 + (R - r) * math.cos(t) + d * math.cos((R - r) / r * t) * .55, 75 + (R - r) * math.sin(t) - d * math.sin((R - r) / r * t) * .55))
    out.append(f'<polyline points="{pts(P)}" fill="none" stroke="#000" stroke-width="1"/>')
    out.append('<circle cx="30" cy="75" r="26" fill="none" stroke="#000" stroke-width="1.8"/><circle cx="30" cy="75" r="5" fill="#000"/>')
    out.append(prajam(30, 40, 6) + prajam(30, 110, 6))
    return "".join(out)


WINGS = {"acanthus": wing_acanthus, "kranok": wing_kranok, "nouveau": wing_nouveau, "deco": wing_deco, "woodcut": wing_woodcut, "laurel": wing_laurel, "guilloche": wing_guilloche}


# ---------------------------------------------------------------- the cartouche
def cartouche(cx, cy, rx, ry, beads=True):
    out = [f'<ellipse cx="{cx}" cy="{cy}" rx="{rx + 9}" ry="{ry + 8}" fill="#fff" stroke="#000" stroke-width="2.4"/>',
           f'<ellipse cx="{cx}" cy="{cy}" rx="{rx + 1.5}" ry="{ry + 1.5}" fill="none" stroke="#000" stroke-width="1"/>']
    if beads:
        n = 44
        for i in range(n):
            a = 2 * math.pi * i / n
            x, y = cx + (rx + 5.2) * math.cos(a), cy + (ry + 4.8) * math.sin(a)
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{1.5 if i % 4 else 2.3}" fill="#000"/>')
    return "".join(out)


def banner(vignette, dialect="acanthus", W=570, H=150):
    """The section-front plate: wings, beaded oval, engraved vignette."""
    cx, cy, rx, ry = W / 2, H / 2, 92, 62
    wing = WINGS[dialect]()
    body = (f'<g>{wing}</g><g transform="translate({W},0) scale(-1,1)">{wing}</g>'
            + cartouche(cx, cy, rx, ry)
            + f'<g clip-path="url(#ov)"><g transform="translate({cx - 90},{cy - 62})">{vignette}</g></g>'
            + f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#000" stroke-width="1.6"/>')
    # a crest finial on top of the oval and a pendant below
    body += (f'<path d="M{cx - 14},{cy - ry - 7} Q{cx},{cy - ry - 22} {cx + 14},{cy - ry - 7}" fill="#fff" stroke="#000" stroke-width="1.4"/>'
             + prajam(cx, cy - ry - 13, 5)
             + f'<path d="M{cx - 10},{cy + ry + 7} L{cx},{cy + ry + 13} L{cx + 10},{cy + ry + 7}" fill="#000"/>')
    defs = f'<clipPath id="ov"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/></clipPath>'
    return svg(W, H, body, defs)


def medallion(vignette, W=96, H=70):
    """A small oval vignette for card heads: same grammar, no wings."""
    s = (W - 14) / 180
    cx, cy = W / 2, H / 2
    rx, ry = 90 * s, 62 * s
    body = (f'<ellipse cx="{cx}" cy="{cy}" rx="{f(rx + 5)}" ry="{f(ry + 5)}" fill="#fff" stroke="#000" stroke-width="1.6"/>'
            + "".join(f'<circle cx="{f(cx + (rx + 2.6) * math.cos(2 * math.pi * i / 30))}" cy="{f(cy + (ry + 2.6) * math.sin(2 * math.pi * i / 30))}" r="1" fill="#000"/>' for i in range(30))
            + f'<g clip-path="url(#ov)"><g transform="translate({f(cx - 90 * s)},{f(cy - 62 * s)}) scale({f(s)})">{vignette}</g></g>'
            + f'<ellipse cx="{cx}" cy="{cy}" rx="{f(rx)}" ry="{f(ry)}" fill="none" stroke="#000" stroke-width="1.1"/>')
    defs = f'<clipPath id="ov"><ellipse cx="{cx}" cy="{cy}" rx="{f(rx)}" ry="{f(ry)}"/></clipPath>'
    # hatch stays at a readable pitch: the pattern is defined in user space of the outer svg
    return svg(W, H, body, defs)


# ---------------------------------------------------------------- bands (repeat-x)
def band_beads():
    return svg(16, 10, '<line x1="0" y1="1" x2="16" y2="1" stroke="#000" stroke-width="1"/>'
               '<line x1="0" y1="9" x2="16" y2="9" stroke="#000" stroke-width="1"/>'
               '<circle cx="4" cy="5" r="1.6" fill="#000"/><path d="M12,2.6 L14.4,5 12,7.4 9.6,5 Z" fill="#000"/>')


def band_purfling():
    return svg(10, 12, '<rect x="0" y="0" width="10" height="1.4" fill="#000"/>'
               '<path d="M0,3 L10,3 L5,9 Z" fill="#000"/>'
               '<rect x="0" y="10.6" width="10" height="1.4" fill="#000"/>')


def band_kranok():
    """Niello: white Thai flames on a black ground, between fine rules."""
    body = ('<rect x="0" y="0" width="56" height="1" fill="#000"/><rect x="0" y="3" width="56" height="16" fill="#000"/>'
            '<rect x="0" y="21" width="56" height="1" fill="#000"/>')
    body += kranok_flame(14, 18.5, .44, False, "#fff", "#000") + kranok_flame(42, 18.5, .44, True, "#fff", "#000")
    body += prajam(28, 11, 5.2, "#fff", "#000") + prajam(0, 11, 5.2, "#fff", "#000") + prajam(56, 11, 5.2, "#fff", "#000")
    return svg(56, 22, body)


def band_acanthus():
    body = ('<path d="M0,12 C10,2 20,2 30,12 S50,22 60,12" fill="none" stroke="#000" stroke-width="1.6"/>'
            '<path d="M10,6 C6,2 10,-1 14,2 C12,4 12,6 10,6 Z M40,18 C44,22 40,25 36,22 C38,20 38,18 40,18 Z" fill="#000"/>'
            '<path d="M20,5 C24,0 30,2 28,6 C26,4 22,4 20,5 Z M50,19 C46,24 40,22 42,18 C44,20 48,20 50,19 Z" fill="url(#h1)" stroke="#000" stroke-width=".9"/>'
            '<circle cx="30" cy="12" r="1.6" fill="#000"/><circle cx="0" cy="12" r="1.6" fill="#000"/><circle cx="60" cy="12" r="1.6" fill="#000"/>')
    return svg(60, 24, body)


def band_deco():
    body = ('<rect x="0" y="0" width="24" height="1.4" fill="#000"/><rect x="0" y="12.6" width="24" height="1.4" fill="#000"/>'
            '<path d="M0,11 L6,4 L12,11 L18,4 L24,11" fill="none" stroke="#000" stroke-width="1.4"/>'
            '<path d="M6,4 L6,11 M18,4 L18,11" stroke="#000" stroke-width=".8"/>')
    return svg(24, 14, body)


def band_wave():
    body = ('<path d="M0,14 C6,14 8,4 16,4 C22,4 24,10 20,11 C17,12 16,9 18,8 C14,8 12,14 24,14 Z" fill="#000"/>'
            '<line x1="0" y1="16.5" x2="24" y2="16.5" stroke="#000" stroke-width="1"/>')
    return svg(24, 18, body)


def band_nouveau():
    body = ('<path d="M0,10 C12,0 18,20 30,10 C42,0 48,20 60,10" fill="none" stroke="#000" stroke-width="1.5"/>'
            '<path d="M0,10 C12,20 18,0 30,10 C42,20 48,0 60,10" fill="none" stroke="#000" stroke-width=".8"/>'
            '<circle cx="15" cy="10" r="2" fill="#000"/><circle cx="45" cy="10" r="2" fill="#fff" stroke="#000"/>')
    return svg(60, 20, body)


def band_laurel():
    body = ('<path d="M0,10 H40" stroke="#000" stroke-width="1.2"/>'
            '<path d="M4,10 C8,4 16,3 20,6 C16,9 8,10 4,10 Z M24,10 C28,4 36,3 40,6 C36,9 28,10 24,10 Z" fill="#000"/>'
            '<path d="M14,10 C18,16 26,17 30,14 C26,11 18,10 14,10 Z" fill="url(#h1)" stroke="#000" stroke-width="1"/>')
    return svg(40, 20, body)


def band_guilloche():
    P1 = [(x / 2, 7 + 5 * math.sin(x / 2 * math.pi / 8)) for x in range(0, 65)]
    P2 = [(x / 2, 7 + 5 * math.sin(x / 2 * math.pi / 8 + math.pi)) for x in range(0, 65)]
    body = (f'<polyline points="{pts(P1)}" fill="none" stroke="#000" stroke-width="1.2"/>'
            f'<polyline points="{pts(P2)}" fill="none" stroke="#000" stroke-width="1.2"/>'
            '<path d="M0,0.7 H32 M0,13.3 H32" stroke="#000" stroke-width="1.4"/>')
    return svg(32, 14, body)


BANDS = {"laurel": band_laurel, "guilloche": band_guilloche, "acanthus": band_acanthus, "kranok": band_kranok, "nouveau": band_nouveau, "deco": band_deco, "woodcut": band_wave}


# ---------------------------------------------------------------- small pieces
def corner():
    """Top-left filigree corner; mirror it with CSS transforms or the variants below."""
    body = ('<path d="M1.5,58 L1.5,10 Q1.5,1.5 10,1.5 L58,1.5" fill="none" stroke="#000" stroke-width="2"/>'
            '<path d="M6,58 L6,14 Q6,6 14,6 L58,6" fill="none" stroke="#000" stroke-width=".9"/>'
            + spiral(24, 24, 13, turns=1.4, start=math.pi * 1.25, cw=1, wid=1.5)
            + '<path d="M36,12 C44,10 50,14 56,12 M12,36 C10,44 14,50 12,56" fill="none" stroke="#000" stroke-width="1.1"/>'
            + prajam(10.5, 10.5, 4))
    return body


def corners():
    c = corner()
    tl = svg(60, 60, c)
    tr = svg(60, 60, f'<g transform="translate(60,0) scale(-1,1)">{c}</g>')
    bl = svg(60, 60, f'<g transform="translate(0,60) scale(1,-1)">{c}</g>')
    br = svg(60, 60, f'<g transform="translate(60,60) scale(-1,-1)">{c}</g>')
    return tl, tr, bl, br


def page_corners():
    """Corners for the whole-page frame: 26 px, frame lines at 2 and 6 px, a curl and a lozenge."""
    c = ('<path d="M2.5,26 L2.5,6 Q2.5,2.5 6,2.5 L26,2.5" fill="none" stroke="#000" stroke-width="1.6"/>'
         '<path d="M6.5,26 L6.5,9 Q6.5,6.5 9,6.5 L26,6.5" fill="none" stroke="#000" stroke-width="1"/>'
         + spiral(15, 15, 6.5, turns=1.25, start=math.pi * 1.25, cw=1, leaves=False, wid=1.3)
         + prajam(21, 21, 3.2))
    return (svg(26, 26, c), svg(26, 26, f'<g transform="translate(26,0) scale(-1,1)">{c}</g>'),
            svg(26, 26, f'<g transform="translate(0,26) scale(1,-1)">{c}</g>'), svg(26, 26, f'<g transform="translate(26,26) scale(-1,-1)">{c}</g>'))


def tag():
    """A small engraved cartouche for numbers and labels: pointed ends, double border, end curls."""
    body = ('<path d="M10,2 H86 L94,14 L86,26 H10 L2,14 Z" fill="#fff" stroke="#000" stroke-width="1.6" stroke-linejoin="round"/>'
            '<path d="M12,5.5 H84 L90,14 L84,22.5 H12 L6,14 Z" fill="none" stroke="#000" stroke-width="1"/>')
    return svg(96, 28, body)


def fleuron(W=140, H=26):
    """A symmetric tailpiece: two small scrolls and a prajam yam."""
    half = (spiral(46, 13, 10, turns=1.3, start=math.pi * .5, cw=1, wid=1.4)
            + '<path d="M62,13 L56,13 C50,13 50,3 46,3" fill="none" stroke="#000" stroke-width="1.3"/>'
            + '<line x1="4" y1="13" x2="34" y2="13" stroke="#000" stroke-width="1"/><circle cx="4" cy="13" r="1.6" fill="#000"/>')
    body = half + f'<g transform="translate({W},0) scale(-1,1)">{half}</g>' + prajam(W / 2, 13, 8)
    return svg(W, H, body)


def initial_box():
    """Ground for a decorated initial: a fine frame with corner curls."""
    body = ('<rect x="1" y="1" width="70" height="70" fill="none" stroke="#000" stroke-width="1.6"/>'
            '<rect x="4.5" y="4.5" width="63" height="63" fill="none" stroke="#000" stroke-width=".8"/>'
            + "".join(spiral(x, y, 6, turns=1.2, start=a, cw=c, leaves=False, wid=1)
                      for x, y, a, c in ((13, 13, math.pi * 1.25, 1), (59, 13, -math.pi * .25, -1), (13, 59, math.pi * .75, -1), (59, 59, math.pi * .25, 1))))
    return svg(72, 72, body)


def lozenge():
    return svg(12, 12, prajam(6, 6, 6))


def swash():
    """A signature underline: a whiplash with a curl at each end."""
    body = ('<path d="M4,10 C30,16 60,2 96,8 C120,12 140,4 156,6" fill="none" stroke="#000" stroke-width="1.6" stroke-linecap="round"/>'
            '<path d="M14,14 C50,18 90,8 130,12" fill="none" stroke="#000" stroke-width=".8"/>'
            + spiral(156, 10, 5, turns=1.2, start=-math.pi / 2, cw=1, leaves=False, wid=1.3))
    return svg(166, 20, body)


# ================================================================ round two: twice as ornate
def rosette_corner(S=50):
    """A dense corner rosette: beaded ring, sixteen petals, a prajam yam heart, scroll arms
    running out along both edges. Top-left; mirror for the others."""
    cx = cy = 17
    out = ['<path d="M2,%d L2,10 Q2,2 10,2 L%d,2" fill="none" stroke="#000" stroke-width="1.8"/>' % (S, S),
           '<path d="M2,%d L2,%d M%d,2 L%d,2" stroke="#000" stroke-width="1.8"/>' % (S - 2, S, S - 2, S)]
    out.append(f'<circle cx="{cx}" cy="{cy}" r="14" fill="#fff" stroke="#000" stroke-width="1.6"/>')
    for i in range(24):
        a = 2 * math.pi * i / 24
        out.append(f'<circle cx="{f(cx + 11.6 * math.cos(a))}" cy="{f(cy + 11.6 * math.sin(a))}" r="1" fill="#000"/>')
    for i in range(8):
        a = 2 * math.pi * i / 8
        x1, y1 = cx + 9.5 * math.cos(a), cy + 9.5 * math.sin(a)
        out.append(f'<path d="M{cx},{cy} Q{f(cx + 6 * math.cos(a + .5))},{f(cy + 6 * math.sin(a + .5))} {f(x1)},{f(y1)} '
                   f'Q{f(cx + 6 * math.cos(a - .5))},{f(cy + 6 * math.sin(a - .5))} {cx},{cy} Z" fill="{"#000" if i % 2 else "#fff"}" stroke="#000" stroke-width="1"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="#fff" stroke="#000" stroke-width="1"/>')
    # scroll arms along each edge
    out.append(spiral(38, 10, 6, turns=1.3, start=math.pi, cw=1, leaves=False, wid=1.4))
    out.append(spiral(10, 38, 6, turns=1.3, start=-math.pi / 2, cw=-1, leaves=False, wid=1.4))
    out.append('<path d="M31,8 C34,4 40,4 44,8 M8,31 C4,34 4,40 8,44" fill="none" stroke="#000" stroke-width="1.2"/>')
    out.append(f'<path d="M30,13 C36,16 40,20 44,16 M13,30 C16,36 20,40 16,44" fill="none" stroke="#000" stroke-width="1.1"/>')
    out.append(prajam(46, 6, 3) + prajam(6, 46, 3))
    return "".join(out)


def rosette_corners(S=50):
    c = rosette_corner(S)
    return (svg(S, S, c), svg(S, S, f'<g transform="translate({S},0) scale(-1,1)">{c}</g>'),
            svg(S, S, f'<g transform="translate(0,{S}) scale(1,-1)">{c}</g>'), svg(S, S, f'<g transform="translate({S},{S}) scale(-1,-1)">{c}</g>'))


# Gutter bands, 12 px across, drawn upright (repeat-y); `hband()` turns one to run along the top.
def gb_rope():
    return 12, 10, ('<path d="M1,0 V10 M11,0 V10" stroke="#000" stroke-width="1"/>'
                    '<path d="M2.5,9 C4,4 8,6 9.5,1" fill="none" stroke="#000" stroke-width="1.5"/>'
                    '<path d="M2.5,4 C3,2 4,1 5,0.5 M7,9.5 C8,9 9,8 9.5,6" fill="none" stroke="#000" stroke-width="1"/>')


def gb_kranok():
    fl = ('<path d="M-3,0 C-5,-4 -2,-7 0,-9 C1.5,-10.5 1.5,-13 -.5,-15 C3,-14 4.5,-10.5 3,-7.5 C2,-5.5 3,-2.5 3.5,0 Z" fill="#fff"/>'
          '<path d="M-1,-1.5 C-2,-4 0,-6 1,-7.5" fill="none" stroke="#000" stroke-width="1"/>')
    return 12, 34, ('<rect x="0" y="0" width="12" height="34" fill="#000"/>'
                    f'<g transform="translate(6,17)">{fl}</g><g transform="translate(6,17) scale(1,-1)">{fl}</g>'
                    + prajam(6, 0, 4.4, "#fff", "#000") + prajam(6, 34, 4.4, "#fff", "#000"))


def gb_wave():
    return 12, 16, ('<path d="M1,0 V16" stroke="#000" stroke-width="1"/>'
                    '<path d="M2,16 C2,10 10,8 10,3 C10,0 6,0 6,3 C6,5 8,5 8,4" fill="none" stroke="#000" stroke-width="1.4"/>'
                    '<path d="M2,16 C2,12 7,10 9,8 L11,8 L11,16 Z" fill="#000"/>')


def gb_reeds():
    return 12, 30, ('<path d="M2,30 C2,20 4,8 3,0 M6,30 C6,22 5,12 7,2 M10,30 C10,22 11,14 9,6" fill="none" stroke="#000" stroke-width="1.2"/>'
                    '<rect x="5.6" y="8" width="3" height="8" rx="1.5" fill="#000"/>'
                    '<path d="M3,18 C0,14 0,10 1,8 M9,22 C12,18 12,14 11,12" fill="none" stroke="#000" stroke-width="1"/>')


def gb_vine():
    return 12, 24, ('<path d="M6,0 C1,6 1,6 6,12 C11,18 11,18 6,24" fill="none" stroke="#000" stroke-width="1.4"/>'
                    '<path d="M3.5,6 C0,3 0,1 1,0 C3,1 4,3 3.5,6 Z M8.5,18 C12,15 12,13 11,12 C9,13 8,15 8.5,18 Z" fill="#000"/>'
                    '<circle cx="10" cy="5" r="1.4" fill="#000"/><circle cx="2" cy="19" r="1.4" fill="#000"/>')


def gb_drum():
    return 12, 20, ('<path d="M1.5,0 V20 M10.5,0 V20" stroke="#000" stroke-width="1.2"/>'
                    '<rect x="3.5" y="6" width="5" height="8" rx="1" fill="#000"/><path d="M6,0 V6 M6,14 V20" stroke="#000" stroke-width="1"/>')


def gb_sun():
    return 12, 12, ('<path d="M0,0 L12,6 L0,12 Z" fill="#000"/><path d="M11,0 V12" stroke="#000" stroke-width="1"/>'
                    '<circle cx="9" cy="6" r="1.2" fill="#000"/>')


def gb_guilloche():
    P1 = [(6 + 4.2 * math.sin(y * math.pi / 8), y) for y in range(0, 17)]
    P2 = [(6 - 4.2 * math.sin(y * math.pi / 8), y) for y in range(0, 17)]
    return 12, 16, (f'<polyline points="{pts(P1)}" fill="none" stroke="#000" stroke-width="1.1"/>'
                    f'<polyline points="{pts(P2)}" fill="none" stroke="#000" stroke-width="1.1"/>'
                    '<path d="M.6,0 V16 M11.4,0 V16" stroke="#000" stroke-width="1.1"/>')


def gb_laurel():
    return 12, 18, ('<path d="M6,0 V18" stroke="#000" stroke-width="1.2"/>'
                    '<path d="M6,9 C2,8 1,4 1,2 C4,3 6,6 6,9 Z" fill="#000"/><path d="M6,17 C10,16 11,12 11,10 C8,11 6,14 6,17 Z" fill="#000"/>')


def gb_interlace():
    return interlace_v()


GUTTER = {"interlace": gb_interlace, "acanthus": gb_rope, "kranok": gb_kranok, "woodcut": gb_wave, "reeds": gb_reeds, "nouveau": gb_vine,
          "deco": gb_drum, "sun": gb_sun, "guilloche": gb_guilloche, "laurel": gb_laurel}


def vband(fn):
    w, h, body = fn()
    return svg(w, h, body)


def hband(fn):
    w, h, body = fn()
    return svg(h, w, f'<g transform="translate({h},0) rotate(90)">{body}</g>')


def dot_rule():
    """The divider between items: dots and diamonds on a hairline."""
    return svg(24, 8, '<path d="M0,4 H24" stroke="#000" stroke-width="1"/>'
               '<path d="M12,1 L15,4 L12,7 L9,4 Z" fill="#000"/><circle cx="3" cy="4" r="1.4" fill="#000"/><circle cx="21" cy="4" r="1.4" fill="#000"/>')


def mini_fleuron():
    """The small fleuron at the centre of each divider, on a white ground so it interrupts the rule."""
    body = ('<rect x="0" y="0" width="56" height="12" fill="#fff"/>'
            + spiral(14, 6, 4.5, turns=1.2, start=math.pi * .5, cw=1, leaves=False, wid=1.2)
            + f'<g transform="translate(56,0) scale(-1,1)">{spiral(14, 6, 4.5, turns=1.2, start=math.pi * .5, cw=1, leaves=False, wid=1.2)}</g>'
            + '<path d="M4,6 H9 M47,6 H52" stroke="#000" stroke-width="1"/>' + prajam(28, 6, 5.5))
    return svg(56, 12, body)


def head_corners(S=30):
    """Corners for the card-title cartouche: a curl, a leaf, a bead."""
    c = (f'<path d="M1.5,{S} L1.5,7 Q1.5,1.5 7,1.5 L{S},1.5" fill="none" stroke="#000" stroke-width="1.6"/>'
         f'<path d="M5,{S} L5,9 Q5,5 9,5 L{S},5" fill="none" stroke="#000" stroke-width="1"/>'
         + spiral(14, 14, 6, turns=1.3, start=math.pi * 1.25, cw=1, leaves=False, wid=1.3)
         + '<path d="M20,9 C24,7 27,9 29,8 M9,20 C7,24 9,27 8,29" fill="none" stroke="#000" stroke-width="1"/>')
    return (svg(S, S, c), svg(S, S, f'<g transform="translate({S},0) scale(-1,1)">{c}</g>'),
            svg(S, S, f'<g transform="translate(0,{S}) scale(1,-1)">{c}</g>'), svg(S, S, f'<g transform="translate({S},{S}) scale(-1,-1)">{c}</g>'))


def terminal():
    """A scroll terminal for the middle of a cartouche's side: a C-scroll pair and a bead."""
    body = (spiral(9, 9, 6.5, turns=1.25, start=math.pi * .5, cw=1, leaves=False, wid=1.3)
            + f'<g transform="translate(0,34) scale(1,-1)">{spiral(9, 9, 6.5, turns=1.25, start=math.pi * .5, cw=1, leaves=False, wid=1.3)}</g>'
            + '<path d="M2.5,15 L2.5,19" stroke="#000" stroke-width="1.4"/>' + prajam(9, 17, 3.4))
    return svg(18, 34, body)


def initial_foliate():
    """An old book's initial: double frame, hatched ground, acanthus leaves in each corner;
    the letter sits on a clear white field in the middle."""
    body = ['<rect x="1" y="1" width="70" height="70" fill="#fff" stroke="#000" stroke-width="1.8"/>',
            '<rect x="4.5" y="4.5" width="63" height="63" fill="url(#hh)" stroke="#000" stroke-width="1"/>',
            '<rect x="13" y="11" width="46" height="50" rx="6" fill="#fff" stroke="#000" stroke-width="1"/>']
    for x, y, a, c in ((10, 10, math.pi * 1.25, 1), (62, 10, -math.pi * .25, -1), (10, 62, math.pi * .75, -1), (62, 62, math.pi * .25, 1)):
        body.append(f'<circle cx="{x}" cy="{y}" r="7.5" fill="#fff"/>')
        body.append(spiral(x, y, 6.5, turns=1.3, start=a, cw=c, leaves=False, wid=1.2))
    for x, y, r in ((36, 7.5, 0), (36, 64.5, 180), (7.5, 36, 270), (64.5, 36, 90)):
        body.append(f'<g transform="translate({x},{y}) rotate({r})"><path d="M-7,0 C-4,-3 4,-3 7,0 C4,3 -4,3 -7,0 Z" fill="#000"/></g>')
    return svg(72, 72, "".join(body))


def num_medallion(S=34):
    """A beaded medal for a numeral."""
    c = S / 2
    body = (f'<circle cx="{c}" cy="{c}" r="{c - 1}" fill="#fff" stroke="#000" stroke-width="1.6"/>'
            + "".join(f'<circle cx="{f(c + (c - 4.2) * math.cos(2 * math.pi * i / 22))}" cy="{f(c + (c - 4.2) * math.sin(2 * math.pi * i / 22))}" r="1" fill="#000"/>' for i in range(22))
            + f'<circle cx="{c}" cy="{c}" r="{c - 7}" fill="none" stroke="#000" stroke-width="1"/>')
    return svg(S, S, body)


def big_medallion(S=64):
    c = S / 2
    out = [f'<circle cx="{c}" cy="{c}" r="{c - 1}" fill="#fff" stroke="#000" stroke-width="1.8"/>']
    for i in range(32):
        a = 2 * math.pi * i / 32
        r0, r1 = c - 3, c - 8
        out.append(f'<line x1="{f(c + r0 * math.cos(a))}" y1="{f(c + r0 * math.sin(a))}" x2="{f(c + r1 * math.cos(a + .09))}" y2="{f(c + r1 * math.sin(a + .09))}" stroke="#000" stroke-width="1"/>')
    out.append(f'<circle cx="{c}" cy="{c}" r="{c - 9}" fill="#fff" stroke="#000" stroke-width="1.2"/>')
    for i in range(28):
        a = 2 * math.pi * i / 28
        out.append(f'<circle cx="{f(c + (c - 11.5) * math.cos(a))}" cy="{f(c + (c - 11.5) * math.sin(a))}" r="1" fill="#000"/>')
    out.append(f'<circle cx="{c}" cy="{c}" r="{c - 14}" fill="none" stroke="#000" stroke-width="1"/>')
    return svg(S, S, "".join(out))


# ================================================================ round three: generative, date-seeded
import random as _random


def seeded(*parts):
    """A random generator seeded from the day (and a name), so each morning's plates are new."""
    return _random.Random("|".join(str(p) for p in parts))


def guilloche_rosette(cx, cy, R, seed, curves=9, inner=.3, sw=1):
    """A banknote rosette: a family of epitrochoids, each turned a little, many fine strokes."""
    rnd = seeded("rosette", seed)
    a = rnd.choice((5, 6, 7, 8))
    b = 1.0
    h = rnd.uniform(.7, .98)
    out = []
    for j in range(curves):
        rot = 2 * math.pi * j / curves / a
        P = []
        for i in range(0, 721):
            t = 2 * math.pi * i / 720
            x = (a + b) * math.cos(t) - h * math.cos((a + b) / b * t)
            y = (a + b) * math.sin(t) - h * math.sin((a + b) / b * t)
            rr = math.hypot(x, y)
            th = math.atan2(y, x) + rot
            r_ = inner * R + (1 - inner) * R * (rr - (a + b - h)) / (2 * h)
            P.append((cx + r_ * math.cos(th), cy + r_ * math.sin(th)))
        out.append(f'<polyline points="{pts(P)}" fill="none" stroke="#000" stroke-width="{sw}"/>')
    return "".join(out)


def guilloche_ring(cx, cy, rx, ry, w, seed, n=4, k=None, sw=1, ink="#000"):
    """A guilloche band running round an ellipse: n phase-shifted waves between two rules."""
    rnd = seeded("ring", seed)
    k = k or rnd.choice((24, 28, 30, 32, 36, 40))
    out = [f'<ellipse cx="{cx}" cy="{cy}" rx="{f(rx)}" ry="{f(ry)}" fill="none" stroke="#000" stroke-width="1.2"/>',
           f'<ellipse cx="{cx}" cy="{cy}" rx="{f(rx + w)}" ry="{f(ry + w)}" fill="none" stroke="#000" stroke-width="1.2"/>']
    for j in range(n):
        ph = 2 * math.pi * j / n
        P = []
        for i in range(0, 361):
            t = 2 * math.pi * i / 360
            d = w / 2 + (w / 2 - 1.2) * math.sin(k * t + ph)
            P.append((cx + (rx + d) * math.cos(t), cy + (ry + d) * math.sin(t)))
        out.append(f'<polyline points="{pts(P)}" fill="none" stroke="{ink}" stroke-width="{sw}"/>')
    return "".join(out).replace('stroke="#000"', f'stroke="{ink}"')


def moon_phase(day):
    """0 new, .5 full: days since the new moon of 6 Jan 2000, over the synodic month."""
    import datetime
    d = datetime.date.fromisoformat(str(day)[:10])
    return ((d - datetime.date(2000, 1, 6)).days - .76) / 29.530588 % 1


def moon_roundel(cx, cy, r, phase, seed):
    """An inverse plate: a black roundel, the night's moon in white at its true phase, a white
    guilloche ring at one-device-pixel strokes and a scatter of engraved stars."""
    rnd = seeded("stars", seed)
    m = r * .5
    lit = math.cos(2 * math.pi * phase)              # terminator ellipse: 1 new, -1 full
    side = 1 if phase < .5 else -1                    # waxing: lit on the right
    tx = abs(lit) * m
    sweep_out = 1 if side > 0 else 0
    sweep_t = (0 if lit > 0 else 1) if side > 0 else (1 if lit > 0 else 0)
    moon = (f'<circle cx="{cx}" cy="{cy}" r="{f(m)}" fill="#444" stroke="#fff" stroke-width=".5"/>'   # earthshine: a flat grey
            f'<path d="M{f(cx)},{f(cy - m)} A{f(m)},{f(m)} 0 0 {sweep_out} {f(cx)},{f(cy + m)} '
            f'A{f(tx)},{f(m)} 0 0 {sweep_t} {f(cx)},{f(cy - m)} Z" fill="#fff"/>')
    stars = "".join(f'<circle cx="{f(cx + a)}" cy="{f(cy + b)}" r="{rnd.choice((.6, .8, 1.1))}" fill="#fff"/>'
                    for a, b in ((rnd.uniform(-r * .6, r * .6), rnd.uniform(-r * .6, r * .6)) for _ in range(14))
                    if m + 3 < math.hypot(a, b) < r - 15)
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#000" stroke="#000" stroke-width="2"/>'
            + guilloche_ring(cx, cy, r - 9, r - 9, 7, seed + "moon", 2, 18, sw=.5, ink="#fff")
            + stars + moon)


def inverse(doc, panel=None):
    """The same engraving printed white on a velvet black ground. panel=(x, y, w, h) stays pure
    white: text is always black ink on white."""
    w = float(re.search(r'width="([\d.]+)"', doc).group(1))
    h = float(re.search(r'height="([\d.]+)"', doc).group(1))
    swap = {"#000": "#fff", "#fff": "#000", "#eee": "#222", "#ddd": "#222", "white": "#000", "black": "#fff"}
    body = re.sub(r'(fill|stroke)="(#000|#fff|#eee|#ddd|white|black)"', lambda m: f'{m.group(1)}="{swap[m.group(2)]}"', doc)
    head, rest = body.split("</defs>", 1)
    ground = f'<rect width="{w:g}" height="{h:g}" fill="#000"/>'
    tail = ""
    if panel:      # the reading area stays open (the page's own underprint and white text blocks show through)
        x, y, pw, ph = panel
        ground = (f'<path d="M0,0H{w:g}V{h:g}H0Z M{x},{y}V{y + ph}H{x + pw}V{y}Z" fill="#000" fill-rule="evenodd"/>')
    rest = rest.rsplit("</svg>", 1)[0]
    return snap(head + "</defs>" + ground + tail + rest + "</svg>", inverse=True)


def interlace_v(W=22, H=44):
    """The page-frame band: microline edges, two interlaced strands (over and under), leaves in the loops."""
    out = ['<path d="M1,0 V44 M3.5,0 V44 M18.5,0 V44 M21,0 V44" stroke="#000" stroke-width="1"/>']
    A = [(11 + 5.2 * math.sin(2 * math.pi * y / 44), y) for y in range(0, 45)]
    B = [(11 - 5.2 * math.sin(2 * math.pi * y / 44), y) for y in range(0, 45)]
    for P in (A, B):
        out.append(f'<polyline points="{pts(P)}" fill="none" stroke="#000" stroke-width="3.4"/>')
        out.append(f'<polyline points="{pts(P)}" fill="none" stroke="#fff" stroke-width="1.4"/>')
    # over-under: strand A passes over at y=0/44, B over at y=22
    out.append('<rect x="8" y="18" width="6" height="8" fill="#fff"/>')
    BB = [(11 - 5.2 * math.sin(2 * math.pi * y / 44), y) for y in range(17, 28)]
    out.append(f'<polyline points="{pts(BB)}" fill="none" stroke="#000" stroke-width="3.4"/><polyline points="{pts(BB)}" fill="none" stroke="#fff" stroke-width="1.4"/>')
    for y, s in ((11, 1), (33, -1)):
        out.append(f'<path d="M11,{y - 4} C{11 + 3 * s},{y - 1} {11 + 3 * s},{y + 1} 11,{y + 4} C{11 - 3 * s},{y + 1} {11 - 3 * s},{y - 1} 11,{y - 4} Z" fill="#000"/>')
    for y in (0, 22, 44):
        out.append(f'<circle cx="6" cy="{y}" r="1" fill="#000"/><circle cx="16" cy="{y}" r="1" fill="#000"/>')
    return W, H, "".join(out)


def corner_roundel(vignette, seed, S=62, sc=.3):
    """A frame corner: a guilloche rosette ring with an engraved vignette set into it."""
    c = S / 2
    body = (f'<rect x="0" y="0" width="{S}" height="{S}" fill="#fff"/>'
            + f'<circle cx="{c}" cy="{c}" r="{c - 1}" fill="#fff" stroke="#000" stroke-width="1.8"/>'
            + guilloche_ring(c, c, c - 13, c - 13, 9, seed, 2, 14)
            + f'<circle cx="{c}" cy="{c}" r="{c - 14}" fill="#fff" stroke="#000" stroke-width="1.2"/>'
            + f'<g clip-path="url(#cr)"><g transform="translate({c},{c}) scale({sc}) translate(-90,-62)">{vignette}</g></g>')
    return svg(S, S, body, f'<clipPath id="cr"><circle cx="{c}" cy="{c}" r="{c - 15}"/></clipPath>')


def mid_medallion(seed, W=22, H=40):
    """The frame's midpoint: an upright oval with a prajam yam, set over the band."""
    body = (f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>'
            f'<ellipse cx="11" cy="20" rx="10" ry="19" fill="#fff" stroke="#000" stroke-width="1.6"/>'
            f'<ellipse cx="11" cy="20" rx="7" ry="15.5" fill="none" stroke="#000" stroke-width="1"/>'
            + prajam(11, 20, 6) + '<circle cx="11" cy="8" r="1.4" fill="#000"/><circle cx="11" cy="32" r="1.4" fill="#000"/>')
    return svg(W, H, body)


def _band_pattern(pid, fn, W):
    """A gutter band tile, scaled to the frame's width, as an SVG <pattern> running down the page."""
    w, h, body = fn()
    k = (W - 8) / w
    return (f'<pattern id="{pid}" width="{f(W - 8)}" height="{f(h * k)}" patternUnits="userSpaceOnUse">'
            f'<g transform="scale({f(k)})">{body}</g></pattern>')


def _band_pattern_h(pid, fn, W):
    w, h, body = fn()
    k = (W - 8) / w
    return (f'<pattern id="{pid}" width="{f(h * k)}" height="{f(W - 8)}" patternUnits="userSpaceOnUse">'
            f'<g transform="translate({f(h * k)},0) rotate(90) scale({f(k)})">{body}</g></pattern>')


def page_frame(seed, dialect_fn, corners, sun_text="", W=618, H=714, B=26, moon=None):
    """The whole-page engraved frame, one SVG per section per day: microline rules, a dialect band
    all round, four vignette roundels at the corners, oval medallions at the side midpoints, a
    guilloche rosette at the top midpoint and the sunrise time engraved at the foot."""
    defs = _band_pattern("bv", dialect_fn, B) + _band_pattern_h("bh", dialect_fn, B)
    out = [f'<path d="M0,0 H{W} V{H} H0 Z M{B},{B} V{H - B} H{W - B} V{B} Z" fill="#ddd" fill-rule="evenodd"/>',  # the underprint tint
           # microline: three one-device-pixel rules inside the frame, banknote fashion
           "".join(f'<rect x="{B + 1 + k}" y="{B + 1 + k}" width="{W - 2 * B - 2 - 2 * k}" height="{H - 2 * B - 2 - 2 * k}" fill="none" stroke="#000" stroke-width=".5"/>'
                   for k in (2, 3.5)),
           f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="#000" stroke-width="1.6"/>',
           f'<rect x="{B + 1}" y="{B + 1}" width="{W - 2 * B - 2}" height="{H - 2 * B - 2}" fill="none" stroke="#000" stroke-width="1"/>',
           f'<rect x="4" y="{B}" width="{B - 8}" height="{H - 2 * B}" fill="url(#bv)"/>',
           f'<rect x="{W - B + 4}" y="{B}" width="{B - 8}" height="{H - 2 * B}" fill="url(#bv)"/>',
           f'<rect x="{B}" y="4" width="{W - 2 * B}" height="{B - 8}" fill="url(#bh)"/>',
           f'<rect x="{B}" y="{H - B + 4}" width="{W - 2 * B}" height="{B - 8}" fill="url(#bh)"/>',
           f'<path d="M3.5,{B} V{H - B} M{B - 3.5},{B} V{H - B} M{W - 3.5},{B} V{H - B} M{W - B + 3.5},{B} V{H - B} '
           f'M{B},3.5 H{W - B} M{B},{B - 3.5} H{W - B} M{B},{H - 3.5} H{W - B} M{B},{H - B + 3.5} H{W - B}" stroke="#000" stroke-width="1"/>']
    # midpoints
    for x in (2, W - B + 2):
        out.append(f'<g transform="translate({x - 1},{H / 2 - 24})"><ellipse cx="12" cy="24" rx="12" ry="23" fill="#fff" stroke="#000" stroke-width="1.6"/>'
                   f'<ellipse cx="12" cy="24" rx="8.5" ry="19" fill="none" stroke="#000" stroke-width="1"/>{prajam(12, 24, 7)}</g>')
    out.append(f'<circle cx="{W / 2}" cy="{B / 2 + 1}" r="15" fill="#fff" stroke="#000" stroke-width="1.6"/>'
               f'<circle cx="{W / 2}" cy="{B / 2 + 1}" r="11.5" fill="none" stroke="#000" stroke-width="1"/>' + prajam(W / 2, B / 2 + 1, 8))
    if sun_text:
        out.append(f'<rect x="{W / 2 - 74}" y="{H - B - 1}" width="148" height="{B + 1}" rx="4" fill="#fff" stroke="#000" stroke-width="1.4"/>'
                   f'<text x="{W / 2}" y="{H - 8}" text-anchor="middle" font-family="Georgia,serif" font-size="13" font-style="italic" fill="#000">{sun_text}</text>')
    # corner roundels
    S = 66
    for (x, y), vg in zip(((0, 0), (W - S, 0), (0, H - S), (W - S, H - S)), corners):
        c = S / 2
        cid = f"c{x}{y}"
        defs += f'<clipPath id="{cid}"><circle cx="{x + c}" cy="{y + c}" r="{c - 15}"/></clipPath>'
        if moon is not None and (x, y) == (W - S, 0):
            out.append(moon_roundel(x + c, y + c, c - 1, moon, seed))
            continue
        out.append(f'<circle cx="{x + c}" cy="{y + c}" r="{c - 1}" fill="#eee" stroke="#000" stroke-width="2"/>'
                   + guilloche_ring(x + c, y + c, c - 13, c - 13, 9, f"{seed}{x}{y}", 4, 14, sw=.5)
                   + f'<circle cx="{x + c}" cy="{y + c}" r="{c - 14}" fill="#fff" stroke="#000" stroke-width="1.2"/>'
                   + f'<g clip-path="url(#{cid})"><g transform="translate({x + c},{y + c}) scale(.29) translate(-90,-62)">{vg}</g></g>')
    return svg(W, H, "".join(out), defs)


def tailpiece(vignette, dialect="acanthus"):
    """A cul-de-lampe: the section's plate, then fleurons narrowing to a point below it."""
    W, H = 570, 236
    plate = banner(vignette, dialect)
    inner = plate.split("<defs>", 1)[1]
    defs, body = inner.split("</defs>", 1)
    body = body.rsplit("</svg>", 1)[0]
    fl = fleuron().split("</defs>", 1)[1].rsplit("</svg>", 1)[0]
    rows = (f'<g transform="translate({W / 2 - 105},156) scale(1.5)">{fl}</g>'
            f'<g transform="translate({W / 2 - 70},190)">{fl}</g>'
            f'<g transform="translate({W / 2 - 35},214) scale(.5)">{fl}</g>'
            + prajam(W / 2, 230, 5))
    return svg(W, H, body + rows, defs.replace(HATCH, ""))


# ---------------------------------------------------------------- vignettes
WING_SRC = wing_acanthus


def water(y0, y1, step=4, seed=3, x0=0, x1=180, gaps=True):
    out, s = [], seed
    y = y0
    i = 0
    while y <= y1:
        x = x0
        while x < x1:
            s = (s * 1103515245 + 12345) & 0x7FFFFFFF
            ln = 10 + s % 40
            gap = 3 + (s >> 8) % 7 if gaps else 0
            out.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(min(x + ln, x1))}" y2="{f(y)}" stroke="#000" stroke-width="{.8 + .1 * (i % 3)}"/>')
            x += ln + gap
        y += step
        i += 1
    return "".join(out)


def rays(cx, cy, r0, r1, a0, a1, n, w=.8):
    out = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        rr = r1 if i % 2 == 0 else r1 * .82
        out.append(f'<line x1="{f(cx + r0 * math.cos(a))}" y1="{f(cy + r0 * math.sin(a))}" x2="{f(cx + rr * math.cos(a))}" y2="{f(cy + rr * math.sin(a))}" stroke="#000" stroke-width="{w}"/>')
    return "".join(out)


def fir(x, y, h, w=None):
    w = w or h * .42
    tiers = 5
    d = [f"M{f(x)},{f(y - h)}"]
    for i in range(1, tiers + 1):
        yy = y - h + h * i / tiers * .92
        ww = w / 2 * i / tiers
        d.append(f"L{f(x + ww)},{f(yy)} L{f(x + ww * .45)},{f(yy - h * .05)}")
    d.append(f"L{f(x + 1.2)},{f(y - h * .08)} L{f(x + 1.2)},{f(y)} L{f(x - 1.2)},{f(y)} L{f(x - 1.2)},{f(y - h * .08)}")
    for i in range(tiers, 0, -1):
        yy = y - h + h * i / tiers * .92
        ww = w / 2 * i / tiers
        d.append(f"L{f(x - ww * .45)},{f(yy - h * .05)} L{f(x - ww)},{f(yy)}")
    d.append("Z")
    return f'<path d="{" ".join(d)}" fill="#000"/>'


def firs(xs, y, h):
    return "".join(fir(x, y - (i % 2) * 2, h * (0.8 + .25 * ((i * 7) % 3) / 2)) for i, x in enumerate(xs))


def hood(x, y, s=1.0, hatch=True):
    """Mt. Hood: the sharp summit, snow above, hatched flanks below."""
    pk = f'<g transform="translate({f(x)},{f(y)}) scale({f(s)})">'
    pk += '<path d="M-60,0 L-26,-30 L-12,-44 L-4,-52 L2,-48 L8,-50 L20,-36 L36,-22 L64,0 Z" fill="#fff" stroke="#000" stroke-width="1.4" stroke-linejoin="round"/>'
    if hatch:
        pk += '<path d="M2,-48 L8,-50 L20,-36 L36,-22 L64,0 L10,0 L14,-18 L6,-30 Z" fill="url(#h1)"/>'
        pk += '<path d="M-60,0 L-40,-16 L-30,-12 L-22,-20 L-12,-10 L-4,-16 L6,-6 L18,-12 L30,-4 L40,-8 L64,0 Z" fill="url(#hh)"/>'
    pk += '<path d="M-4,-52 L-8,-40 L-2,-36 L-6,-26 M2,-48 L6,-38 L2,-30 M-12,-44 L-18,-34" fill="none" stroke="#000" stroke-width=".9"/>'
    return pk + '</g>'


def heron(x, y, s=1.0):
    return (f'<g transform="translate({f(x)},{f(y)}) scale({f(s)})" fill="#000">'
            '<path d="M0,0 C-2,-6 -8,-10 -12,-14 C-14,-18 -10,-22 -6,-20 L4,-22 L-4,-18 C-2,-14 4,-10 6,-4 C10,0 14,4 18,6 L8,4 Z"/>'
            '<path d="M2,2 L0,18 M6,4 L6,18" stroke="#000" stroke-width="1.1" fill="none"/></g>')


def bird_v(x, y, s=1.0):
    return f'<path d="M{f(x - 5 * s)},{f(y - 2 * s)} Q{f(x - 2 * s)},{f(y - 3 * s)} {f(x)},{f(y)} Q{f(x + 2 * s)},{f(y - 3 * s)} {f(x + 5 * s)},{f(y - 2 * s)}" fill="none" stroke="#000" stroke-width="1.1"/>'


def sun(cx, cy, r, nrays=24, face=False):
    out = [rays(cx, cy, r + 3, r + 18, 0, 2 * math.pi * (nrays - 1) / nrays, nrays, .9)]
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="#000" stroke-width="1.6"/>')
    if face:
        out.append(f'<path d="M{cx - r * .45},{cy - r * .15} q{r * .15},-{r * .15} {r * .3},0 M{cx + r * .15},{cy - r * .15} q{r * .15},-{r * .15} {r * .3},0 '
                   f'M{cx - r * .4},{cy + r * .3} q{r * .4},{r * .35} {r * .8},0" fill="none" stroke="#000" stroke-width="1.2"/>'
                   f'<circle cx="{cx - r * .3}" cy="{cy - r * .02}" r="1.4" fill="#000"/><circle cx="{cx + r * .3}" cy="{cy - r * .02}" r="1.4" fill="#000"/>')
    else:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r - 4}" fill="url(#hh)"/>')
    return "".join(out)


V = {}

# Today: first light over Mt. Hood and the Columbia.
V["today"] = (rays(110, 72, 16, 120, math.pi * 1.02, math.pi * 1.98, 31)
              + '<rect x="0" y="72" width="180" height="60" fill="#fff"/>'
              + '<circle cx="110" cy="72" r="13" fill="#fff" stroke="#000" stroke-width="1.6"/>'
              + hood(72, 80, .95)
              + '<path d="M0,80 C30,74 60,82 90,78 C120,74 150,80 180,76 L180,86 L0,86 Z" fill="#000"/>'
              + firs([6, 14, 22, 160, 168, 176], 84, 20)
              + water(90, 124, 4)
              + bird_v(140, 30, 1.2) + bird_v(152, 38) + bird_v(36, 26))

# Roads: the road up the mountain.
V["roads"] = (hood(90, 66, 1.05)
              + firs([8, 18, 30, 150, 162, 172], 84, 26)
              + '<path d="M60,124 C70,104 112,100 100,88 C92,80 74,82 84,74" fill="none" stroke="#000" stroke-width="2"/>'
              + '<path d="M120,124 C116,104 132,94 112,86 C100,82 92,80 92,74" fill="none" stroke="#000" stroke-width="2"/>'
              + '<path d="M90,124 C94,108 120,100 106,88" fill="none" stroke="#000" stroke-width="1.4" stroke-dasharray="5 4"/>'
              + '<path d="M0,84 C40,78 60,86 84,76 L84,124 L0,124 Z M180,84 C140,80 130,86 112,78 L120,124 L180,124 Z" fill="url(#h2)"/>')

# Family: a good dog, sitting, and a kite in the sky.
DOG = ('<path d="M58,44 C60,38 66,32 74,30 C82,28 88,32 91,38 C95,48 93,56 92,62 C104,66 118,74 124,90 C128,100 126,110 118,112 '
       'L98,112 C96,106 93,100 90,98 L88,112 L72,112 C74,106 76,96 76,84 C72,74 70,64 73,58 C67,56 61,54 57,52 C53,51 51,48 53,46 Z" '
       'fill="#fff" stroke="#000" stroke-width="1.6" stroke-linejoin="round"/>'
       '<path d="M92,62 C104,66 118,74 124,90 C128,100 126,110 118,112 L98,112 C100,100 108,92 104,80 C100,72 94,68 92,62 Z" fill="url(#h1)"/>'
       '<path d="M82,31 C92,34 92,50 85,56 C79,51 78,40 82,31 Z" fill="#000"/>'
       '<circle cx="55" cy="45" r="2.6" fill="#000"/><circle cx="71" cy="39" r="1.8" fill="#000"/>'
       '<path d="M73,60 C80,64 88,64 93,60" fill="none" stroke="#000" stroke-width="3"/>'
       '<circle cx="82" cy="66" r="2.4" fill="#fff" stroke="#000" stroke-width="1"/>'
       '<path d="M122,100 C134,100 142,90 141,78" fill="none" stroke="#000" stroke-width="3" stroke-linecap="round"/>'
       '<path d="M80,110 L80,100 M86,110 L86,100" stroke="#000" stroke-width=".8"/>')
DOG_ONLY = DOG
V["family"] = ('<rect x="0" y="112" width="180" height="12" fill="url(#hh)"/>'
               + '<path d="M0,112 L180,112" stroke="#000" stroke-width="1.4"/>'
               + "".join(f'<path d="M{x},112 l2,-5 l2,5" fill="none" stroke="#000" stroke-width=".8"/>' for x in range(4, 180, 9))
               + DOG
               + '<path d="M140,16 L154,30 L140,48 L126,30 Z" fill="#fff" stroke="#000" stroke-width="1.4"/>'
               + '<path d="M140,16 L140,30 L126,30 Z M140,30 L154,30 L140,48 Z" fill="#000"/>'
               + '<path d="M140,48 C136,60 146,66 140,78 C136,86 130,86 128,96" fill="none" stroke="#000" stroke-width=".9"/>'
               + '<path d="M138,58 l4,2 -4,2 Z M140,70 l-4,2 4,2 Z" fill="#000"/>')

# Solar: an almanac sun over the panels on the roof.
V["solar"] = (sun(90, 40, 17, 28, face=True)
              + '<path d="M0,98 L180,98" stroke="#000" stroke-width="1.4"/>'
              + "".join(f'<g transform="translate({x},74) skewX(-24)"><rect width="36" height="22" fill="#fff" stroke="#000" stroke-width="1.4"/>'
                        f'<path d="M0,7.3H36M0,14.6H36M9,0V22M18,0V22M27,0V22" stroke="#000" stroke-width=".7"/>'
                        f'<rect x="0" y="0" width="9" height="7.3" fill="url(#h1)"/></g>' for x in (30, 76, 122))
              + '<rect x="0" y="99" width="180" height="26" fill="url(#h2)"/>'
              + bird_v(30, 26) + bird_v(150, 22, 1.2))

STAR_ = '<path d="M0,-5 L1.2,-1.2 L5,0 L1.2,1.2 L0,5 L-1.2,1.2 L-5,0 L-1.2,-1.2 Z" fill="#000"/>'

# Garden: a Portland rose, and a bird on the cane.
ROSE = ('<g transform="translate(-4,6)">'
        '<path d="M48,52 C44,38 56,28 70,32 C78,22 96,24 98,36 C108,38 110,52 102,60 C96,74 58,76 48,60 Z" fill="#fff" stroke="#000" stroke-width="1.6"/>'
        '<path d="M48,60 C58,76 96,74 102,60 C96,68 60,70 48,60 Z" fill="url(#h1)"/>'
        '<path d="M54,52 C56,42 70,36 80,42 M62,58 C66,48 82,46 92,52 M88,40 C94,40 98,46 96,52 M56,60 C70,66 88,64 98,56" fill="none" stroke="#000" stroke-width="1.2"/>'
        '<path d="M72,44 C74,38 84,38 86,44 C88,50 80,52 76,48 C74,46 76,43 80,44" fill="none" stroke="#000" stroke-width="1.4"/>'
        '<path d="M60,70 L52,78 L64,74 Z M90,70 L100,78 L88,74 Z" fill="#000"/>'
        '</g>')
LEAF = '<path d="M0,0 C6,-8 18,-8 24,0 C18,8 6,8 0,0 Z" fill="url(#h2)" stroke="#000" stroke-width="1.1"/><path d="M0,0 L24,0" stroke="#000" stroke-width=".8"/>'
V["garden"] = ('<path d="M72,74 C66,90 76,104 70,124" fill="none" stroke="#000" stroke-width="2.2"/>'
               + "".join(f'<path d="M{x},{y} l-4,-2 l1,4 Z" fill="#000"/>' for x, y in ((70, 84), (72, 100), (70, 114)))
               + f'<g transform="translate(72,92) rotate(-30)">{LEAF}</g><g transform="translate(70,106) rotate(200)">{LEAF}</g>'
               + f'<g transform="translate(68,78) rotate(210)">{LEAF}</g>'
               + ROSE
               + '<path d="M120,100 C116,80 118,60 120,44" fill="none" stroke="#000" stroke-width="1.6"/>'
               + '<g transform="translate(130,64)"><path d="M-12,0 C-10,-10 2,-14 10,-8 L16,-10 L12,-5 C14,4 4,10 -6,8 L-18,14 L-12,4 Z" fill="#000"/>'
               + '<path d="M-6,0 C-2,-4 4,-4 6,0" fill="none" stroke="#fff" stroke-width="1"/><circle cx="6" cy="-7" r="1" fill="#fff"/>'
               + '<path d="M-2,8 L-4,16 M2,8 L2,16" stroke="#000" stroke-width="1"/></g>'
               + '<path d="M108,80 L132,80" stroke="#000" stroke-width="1.4"/>'
               + bird_v(150, 30) + bird_v(30, 20))

# River: a freighter on the Columbia, a heron on the bank, firs beyond.
V["river"] = ('<path d="M0,62 C30,50 60,58 90,52 C120,46 150,54 180,50 L180,66 L0,66 Z" fill="url(#h2)" stroke="#000" stroke-width="1"/>'
              + firs([8, 16, 26, 36, 46, 140, 150, 158, 168, 176], 66, 18)
              + '<path d="M26,78 L156,78 L148,92 L34,92 Z" fill="#000"/>'
              + "".join(f'<rect x="{x}" y="{70 - (i % 2) * 6}" width="12" height="{8 + (i % 2) * 6}" fill="{"url(#hv)" if i % 3 else "#fff"}" stroke="#000" stroke-width="1"/>'
                        for i, x in enumerate(range(40, 124, 12)))
              + '<rect x="128" y="56" width="16" height="22" fill="#fff" stroke="#000" stroke-width="1.2"/>'
              + '<path d="M130,62 H142 M136,56 V48 M132,48 H140" stroke="#000" stroke-width="1"/>'
              + '<path d="M44,85 H140" stroke="#fff" stroke-width="1"/>'
              + water(96, 124, 4, 7)
              + heron(18, 92, .9) + bird_v(100, 20, 1.2) + bird_v(116, 26))

# The sky (nearby): sundown over the island, a jet's contrail, the first stars.
V["nearby"] = (rays(64, 96, 16, 110, math.pi * 1.04, math.pi * 1.96, 27)
               + '<rect x="0" y="96" width="180" height="30" fill="#fff"/>'
               + '<path d="M48,96 A16,16 0 0 1 80,96" fill="#fff" stroke="#000" stroke-width="1.6"/>'
               + '<path d="M0,96 C30,92 50,98 90,94 C120,91 150,97 180,94 L180,100 L0,100 Z" fill="#000"/>'
               + firs([96, 104, 112, 150, 158, 166, 174], 96, 14)
               + water(104, 124, 4, 13)
               + '<path d="M20,64 C40,58 70,62 96,58 C80,66 44,68 20,64 Z M120,74 C134,70 150,72 164,70 C152,76 132,78 120,74 Z" fill="url(#hh)" stroke="#000" stroke-width="1"/>'
               + '<path d="M40,40 L136,18 M40,44 L136,22" stroke="#000" stroke-width="1" stroke-dasharray="6 3"/>'
               + '<g transform="translate(142,20) rotate(-13)"><path d="M-8,0 L8,0 L10,-1 L8,-2 L-6,-2 Z M-2,-1 L4,-8 L6,-8 L4,-1 Z M-2,-1 L4,6 L6,6 L4,-1 Z M-8,-1 L-11,-5 L-9,-5 L-6,-1 Z" fill="#000"/></g>'
               + "".join(f'<g transform="translate({x},{y}) scale({sc})">{STAR_}</g>' for x, y, sc in ((150, 46, .9), (166, 34, .6), (122, 48, .6), (20, 24, .7)))
               + '<path d="M96,10 L76,28" stroke="#000" stroke-width="1.4"/><circle cx="76" cy="28" r="1.8" fill="#000"/>')

# News: quill, inkwell and the morning's sheet.
V["news"] = ('<path d="M30,104 L120,104 L150,82 L60,82 Z" fill="#fff" stroke="#000" stroke-width="1.4"/>'
             + "".join(f'<line x1="{60 + i * 4}" y1="{86 + i * 4}" x2="{120 + i * 4}" y2="{86 + i * 4}" stroke="#000" stroke-width=".9"/>' for i in range(0, 4))
             + '<rect x="66" y="84" width="30" height="5" fill="#000" transform="skewX(-50) translate(100,0)"/>'
             + '<path d="M118,60 L146,60 L150,82 L114,82 Z" fill="#000"/><ellipse cx="132" cy="60" rx="14" ry="3" fill="#fff" stroke="#000" stroke-width="1.2"/>'
             + '<path d="M132,60 C110,40 96,22 86,8 C104,16 120,34 134,58" fill="#fff" stroke="#000" stroke-width="1.4"/>'
             + "".join(f'<line x1="{f(132 - i * 3.4)}" y1="{f(58 - i * 3.6)}" x2="{f(132 - i * 3.4 - 8 + i * .2)}" y2="{f(58 - i * 3.6 - 2)}" stroke="#000" stroke-width=".8"/>' for i in range(2, 13))
             + '<path d="M0,110 H180" stroke="#000" stroke-width="1.2"/><rect x="0" y="111" width="180" height="14" fill="url(#h1)"/>')

# Markets: a bull and a tape of candles.
V["markets"] = ("".join(f'<line x1="{x}" y1="{y - 12}" x2="{x}" y2="{y + h + 10}" stroke="#000" stroke-width="1"/>'
                        f'<rect x="{x - 5}" y="{y}" width="10" height="{h}" fill="{"#000" if i % 2 else "#fff"}" stroke="#000" stroke-width="1.2"/>'
                        for i, (x, y, h) in enumerate(((22, 84, 16), (40, 76, 18), (58, 70, 12), (76, 62, 18), (94, 56, 12), (112, 44, 20), (130, 40, 12), (148, 28, 18))))
                 + '<path d="M14,100 C50,84 90,70 160,22" fill="none" stroke="#000" stroke-width="1.6"/><path d="M160,22 l-10,2 l6,6 Z" fill="#000"/>'
                 + '<path d="M0,116 H180" stroke="#000" stroke-width="1.2"/>' + "".join(f'<line x1="{x}" y1="116" x2="{x}" y2="120" stroke="#000"/>' for x in range(4, 180, 12)))

# Civics: the Oregon State Capitol and its gilded pioneer.
V["civics"] = ('<rect x="20" y="88" width="140" height="22" fill="#fff" stroke="#000" stroke-width="1.4"/>'
               + "".join(f'<rect x="{x}" y="92" width="5" height="18" fill="url(#hv)" stroke="#000" stroke-width=".8"/>' for x in range(28, 156, 12))
               + '<rect x="62" y="44" width="56" height="44" fill="#fff" stroke="#000" stroke-width="1.6"/>'
               + "".join(f'<line x1="{x}" y1="48" x2="{x}" y2="88" stroke="#000" stroke-width="{1.2 if x % 8 == 0 else .7}"/>' for x in range(66, 118, 4))
               + '<path d="M66,44 C66,30 114,30 114,44 Z" fill="#fff" stroke="#000" stroke-width="1.4"/>'
               + '<rect x="84" y="24" width="12" height="10" fill="#000"/>'
               + '<path d="M90,24 L90,8 M86,12 L94,10 M88,24 L86,16 M92,24 L94,16" stroke="#000" stroke-width="1.6"/><circle cx="90" cy="6" r="2.4" fill="#000"/>'
               + '<path d="M10,110 H170 L176,118 H4 Z" fill="url(#h1)" stroke="#000" stroke-width="1.2"/>'
               + firs([8, 172], 110, 26))

# Sports: the ball, the laurel and the Timbers' axes.
LAUREL = "".join(f'<path transform="translate({f(90 + 46 * math.cos(a))},{f(66 + 46 * math.sin(a))}) rotate({f(math.degrees(a) + 60)})" d="M0,0 C3,-6 10,-6 12,0 C10,6 3,6 0,0 Z" fill="#000"/>'
                 for a in [math.pi * (0.25 + .065 * i) for i in range(9)] + [math.pi * (0.75 - .065 * i) for i in range(9)])
V["sports"] = ('<path d="M0,112 H180" stroke="#000" stroke-width="1.4"/><rect x="0" y="113" width="180" height="12" fill="url(#hh)"/>'
               '<circle cx="66" cy="70" r="34" fill="#fff" stroke="#000" stroke-width="1.8"/>'
               '<path d="M66,36 V104 M32,70 H100 M42,46 C56,58 56,82 42,94 M90,46 C76,58 76,82 90,94" fill="none" stroke="#000" stroke-width="1.6"/>'
               '<path d="M66,36 A34,34 0 0 1 100,70 L66,70 Z" fill="url(#h2)"/>'
               '<circle cx="128" cy="86" r="24" fill="#fff" stroke="#000" stroke-width="1.8"/>'
               '<path d="M128,78 L136,84 L133,93 L123,93 L120,84 Z" fill="#000"/>'
               '<path d="M128,78 V64 M136,84 L150,80 M133,93 L141,106 M123,93 L115,106 M120,84 L106,80" stroke="#000" stroke-width="1.3"/>'
               '<path d="M128,64 A24,24 0 0 1 150,80 L136,84 L128,78 Z" fill="url(#h1)"/>'
               + "".join(f'<g transform="translate({x},{y}) scale({sc})"><path d="M0,-5 L1.2,-1.2 L5,0 L1.2,1.2 L0,5 L-1.2,1.2 L-5,0 L-1.2,-1.2 Z" fill="#000"/></g>' for x, y, sc in ((130, 30, 1.2), (150, 44, .8), (24, 30, .8))))

# Music: the drum kit. Bass drum, snare, tom, hi-hat, ride, crossed sticks.
def cymbal(x, y, rx, tilt=0):
    return (f'<g transform="translate({x},{y}) rotate({tilt})"><ellipse rx="{rx}" ry="{rx * .2}" fill="#fff" stroke="#000" stroke-width="1.4"/>'
            + "".join(f'<ellipse rx="{f(rx * k)}" ry="{f(rx * .2 * k)}" fill="none" stroke="#000" stroke-width=".7"/>' for k in (.75, .5))
            + f'<ellipse rx="{f(rx * .14)}" ry="{f(rx * .06)}" fill="#000"/></g>')
V["music"] = ('<path d="M0,118 H180" stroke="#000" stroke-width="1.2"/>'
              + '<path d="M150,34 L150,118 M140,118 L150,100 L160,118 M30,46 L30,118 M22,118 L30,104 L38,118 M42,104 L48,118 M60,104 L54,118" stroke="#000" stroke-width="1.2" fill="none"/>'
              + cymbal(150, 34, 26, -8) + cymbal(30, 46, 18) + cymbal(30, 50, 18)
              + '<circle cx="96" cy="86" r="30" fill="#fff" stroke="#000" stroke-width="2"/><circle cx="96" cy="86" r="25" fill="none" stroke="#000" stroke-width="1"/>'
              + "".join(f'<rect x="{f(96 + 27.5 * math.cos(a) - 2)}" y="{f(86 + 27.5 * math.sin(a) - 2)}" width="4" height="4" fill="#000"/>' for a in [i * math.pi / 5 for i in range(10)])
              + '<circle cx="96" cy="86" r="16" fill="url(#h1)" stroke="#000" stroke-width="1"/>'
              + '<path d="M86,82 L92,90 L96,82 L100,90 L106,82" fill="none" stroke="#000" stroke-width="2"/>'
              + '<path d="M84,56 L84,42 M108,56 L108,42" stroke="#000" stroke-width="1"/>'
              + '<path d="M80,40 C80,46 112,46 112,40 L112,30 L80,30 Z" fill="url(#hv)" stroke="#000" stroke-width="1.4"/><ellipse cx="96" cy="30" rx="16" ry="4" fill="#fff" stroke="#000" stroke-width="1.4"/>'
              + '<path d="M44,74 L44,94 C44,99 72,99 72,94 L72,74" fill="url(#hv)" stroke="#000" stroke-width="1.4"/><ellipse cx="58" cy="74" rx="14" ry="4" fill="#fff" stroke="#000" stroke-width="1.4"/>'
              + '<path d="M58,98 L58,118 M50,118 L58,108 L66,118" stroke="#000" stroke-width="1.2" fill="none"/>'
              + '<path d="M44,62 L76,40 M50,40 L80,60" stroke="#000" stroke-width="2.4" stroke-linecap="round"/>'
              + '<circle cx="76" cy="40" r="2" fill="#000"/><circle cx="50" cy="40" r="2" fill="#000"/>')

# Watch: the film reel and a ribbon of film.
V["watch"] = ('<circle cx="70" cy="56" r="40" fill="#fff" stroke="#000" stroke-width="2"/><circle cx="70" cy="56" r="34" fill="url(#h1)" stroke="#000" stroke-width="1"/>'
              + "".join(f'<circle cx="{f(70 + 20 * math.cos(a))}" cy="{f(56 + 20 * math.sin(a))}" r="9" fill="#fff" stroke="#000" stroke-width="1.4"/>' for a in [i * 2 * math.pi / 5 - math.pi / 2 for i in range(5)])
              + '<circle cx="70" cy="56" r="5" fill="#000"/>'
              + '<path d="M104,76 C130,88 140,108 180,104 L180,124 C140,128 124,108 98,94 Z" fill="#000"/>'
              + "".join(f'<rect x="{x}" y="{f(102 + (x - 120) * .1)}" width="5" height="4" fill="#fff"/>' for x in range(122, 180, 9))
              + '<path d="M0,118 H60" stroke="#000" stroke-width="1.2"/>' + bird_v(150, 30))

# Local: St. Johns Bridge, its gothic towers, Forest Park behind.
TOWER = '<path d="M-7,72 L-7,16 L-4,8 L0,2 L4,8 L7,16 L7,72 Z" fill="#fff" stroke="#000" stroke-width="1.6"/><path d="M-3,40 L-3,24 L0,18 L3,24 L3,40 Z M-3,62 L-3,48 L0,44 L3,48 L3,62 Z" fill="#000"/><path d="M-7,16 H7" stroke="#000"/>'
V["local"] = ('<path d="M0,64 C20,50 40,56 60,46 C80,40 100,50 120,44 C140,40 160,50 180,46 L180,72 L0,72 Z" fill="url(#h2)" stroke="#000" stroke-width="1"/>'
              + firs(list(range(4, 180, 9)), 66, 13)
              + '<path d="M0,86 H180 M0,90 H180" stroke="#000" stroke-width="1.4"/>'
              + '<path d="M0,40 Q25,20 46,12 Q90,70 134,12 Q155,20 180,40" fill="none" stroke="#000" stroke-width="1.6"/>'
              + "".join(f'<line x1="{x}" y1="{f(12 + (58 * (1 - ((x - 90) / 44) ** 2)) if 46 < x < 134 else (12 + (x - 46) * -.7 if x <= 46 else 12 + (x - 134) * .6))}" x2="{x}" y2="86" stroke="#000" stroke-width=".7"/>'
                        for x in range(6, 180, 6) if abs(x - 46) > 6 and abs(x - 134) > 6)
              + f'<g transform="translate(46,16)">{TOWER}</g><g transform="translate(134,16)">{TOWER}</g>'
              + '<rect x="38" y="88" width="16" height="36" fill="#000"/><rect x="126" y="88" width="16" height="36" fill="#000"/>'
              + water(96, 124, 4, 11))

# Almanac: the moon with a face, stars, firs.
STAR = '<path d="M0,-5 L1.2,-1.2 L5,0 L1.2,1.2 L0,5 L-1.2,1.2 L-5,0 L-1.2,-1.2 Z" fill="#000"/>'
V["almanac"] = ('<path d="M104,14 A40,40 0 1 0 104,98 A32,32 0 1 1 104,14 Z" fill="url(#h1)" stroke="#000" stroke-width="1.8"/>'
                + '<path d="M72,46 q-4,4 0,8 M70,72 q6,6 14,4" fill="none" stroke="#000" stroke-width="1.4"/><circle cx="76" cy="52" r="1.8" fill="#000"/>'
                + "".join(f'<g transform="translate({x},{y}) scale({s})">{STAR}</g>' for x, y, s in ((130, 30, 1.2), (150, 56, .8), (120, 64, .7), (40, 30, 1), (24, 60, .7), (156, 20, .6), (140, 84, .9)))
                + firs([10, 22, 34, 146, 158, 170], 124, 30) + '<path d="M0,122 H180" stroke="#000" stroke-width="1.2"/>')

# Science: a brass telescope on its tripod, Saturn above.
V["science"] = ('<g transform="translate(86,66) rotate(-28)"><rect x="-50" y="-7" width="76" height="14" fill="url(#hv)" stroke="#000" stroke-width="1.6"/>'
                '<rect x="26" y="-9" width="20" height="18" fill="#fff" stroke="#000" stroke-width="1.6"/><rect x="-62" y="-4" width="12" height="8" fill="#000"/>'
                '<path d="M-20,-7 V7 M0,-7 V7" stroke="#000" stroke-width="1.2"/></g>'
                + '<path d="M84,70 L60,120 M88,70 L94,120 M86,70 L118,120" stroke="#000" stroke-width="1.8"/>'
                + '<g transform="translate(150,28) rotate(-18)"><circle r="10" fill="#fff" stroke="#000" stroke-width="1.4"/><path d="M-10,0 H10" stroke="#000" stroke-width=".7"/>'
                '<ellipse rx="20" ry="5" fill="none" stroke="#000" stroke-width="1.6"/><path d="M-10,-1 A10,10 0 0 1 10,-1" fill="#fff" stroke="#000" stroke-width="1.4"/></g>'
                + "".join(f'<g transform="translate({x},{y}) scale({s})">{STAR}</g>' for x, y, s in ((30, 24, 1), (54, 14, .7), (120, 10, .7), (20, 52, .6)))
                + '<path d="M0,120 H180" stroke="#000" stroke-width="1.2"/>')

# By the numbers (doodles): dividers walking a hand-drawn chart.
V["doodles"] = ('<rect x="10" y="20" width="160" height="94" fill="url(#hh)"/>'
                + "".join(f'<rect x="{x}" y="{y}" width="16" height="{114 - y}" fill="#fff" stroke="#000" stroke-width="1.4"/>'
                          f'<rect x="{x + 3}" y="{y + 3}" width="10" height="{111 - y - 3}" fill="url(#h1)"/>' for x, y in ((22, 84), (46, 70), (70, 78), (94, 56), (118, 64), (142, 40)))
                + '<path d="M10,114 H170" stroke="#000" stroke-width="1.8"/>'
                + "".join(f'<path d="M{x},114 V{118 if x % 20 else 121}" stroke="#000" stroke-width="1.2"/>' for x in range(10, 171, 10))
                + '<path d="M30,76 L54,62 L78,70 L102,48 L126,56 L150,32" fill="none" stroke="#000" stroke-width="1.6"/>'
                + "".join(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#000"/>' for x, y in ((30, 76), (54, 62), (78, 70), (102, 48), (126, 56), (150, 32)))
                + '<path d="M96,4 L74,100 L77,100 L99,10 Z M100,4 L132,94 L129,95 L97,10 Z" fill="#fff" stroke="#000" stroke-width="1.4"/>'
                + '<path d="M84,52 Q100,62 116,50" fill="none" stroke="#000" stroke-width="1.2"/>'
                + '<circle cx="98" cy="8" r="6" fill="#fff" stroke="#000" stroke-width="1.6"/><circle cx="98" cy="8" r="2" fill="#000"/>')

# Delights: a record on the platter, jazz rising off it.
V["delights"] = ('<circle cx="80" cy="66" r="48" fill="#000"/>'
                 + "".join(f'<circle cx="80" cy="66" r="{r}" fill="none" stroke="#fff" stroke-width=".8"/>' for r in range(20, 46, 4))
                 + '<circle cx="80" cy="66" r="15" fill="#fff"/><circle cx="80" cy="66" r="12" fill="none" stroke="#000" stroke-width=".8"/><circle cx="80" cy="66" r="2.4" fill="#000"/>'
                 + '<path d="M70,62 H90 M72,70 H88" stroke="#000" stroke-width="1"/>'
                 + '<path d="M60,40 A30,30 0 0 1 100,36" fill="none" stroke="#fff" stroke-width="2.4"/>'
                 + '<path d="M162,14 L150,70 L118,92" fill="none" stroke="#000" stroke-width="2.4"/><rect x="110" y="88" width="12" height="8" fill="#000" transform="rotate(-30 116 92)"/>'
                 + '<circle cx="162" cy="14" r="7" fill="#fff" stroke="#000" stroke-width="1.6"/>'
                 + '<path d="M140,30 V16 L150,13 V27 M140,30 a3,2 0 1 1 -1,-2 M150,27 a3,2 0 1 1 -1,-2" fill="none" stroke="#000" stroke-width="1.3"/>'
                 + '<path d="M22,26 V12 L30,10 V24" fill="none" stroke="#000" stroke-width="1.3"/><circle cx="20" cy="26" r="2.6" fill="#000"/><circle cx="28" cy="24" r="2.6" fill="#000"/>')

# World: a Thai temple gable with chofa, bai raka and a prang behind.
def chofa(x, y, s=1):
    return f'<path transform="translate({x},{y}) scale({s},1)" d="M0,0 C-2,-8 2,-14 8,-14 C4,-12 4,-8 6,-6 C2,-6 2,-2 0,0 Z" fill="#000"/>'
V["world"] = ('<path d="M90,6 C86,16 84,26 80,36 L100,36 C96,26 94,16 90,6 Z" fill="url(#hh)" stroke="#000" stroke-width="1.2"/>'
              + "".join(f'<path d="M{80 - i},{36 - i * 7} H{100 + i}" stroke="#000" stroke-width=".9"/>' for i in range(0, 4))
              + '<path d="M90,6 V0" stroke="#000" stroke-width="1.4"/>'
              + '<path d="M90,30 L36,80 L144,80 Z" fill="#fff" stroke="#000" stroke-width="1.8" stroke-linejoin="round"/>'
              + '<path d="M90,42 L52,78 L128,78 Z" fill="#000"/>'
              + kranok_flame(90, 74, .9, False, "#fff", "#000") + kranok_flame(74, 76, .55, True, "#fff", "#000") + kranok_flame(106, 76, .55, False, "#fff", "#000")
              + prajam(90, 52, 0)
              + "".join(f'<path d="M{f(90 - (i + 1) * 5.6)},{f(30 + (i + 1) * 5.2)} l-2,-5" stroke="#000" stroke-width="1.2"/><path d="M{f(90 + (i + 1) * 5.6)},{f(30 + (i + 1) * 5.2)} l2,-5" stroke="#000" stroke-width="1.2"/>' for i in range(9))
              + chofa(90, 30) + chofa(36, 80, -1) + chofa(144, 80)
              + '<path d="M24,86 L156,86 L170,92 L10,92 Z" fill="#000"/>'
              + '<rect x="44" y="92" width="92" height="22" fill="#fff" stroke="#000" stroke-width="1.4"/>'
              + "".join(f'<rect x="{x}" y="92" width="5" height="22" fill="url(#hv)" stroke="#000" stroke-width=".8"/>' for x in range(50, 134, 14))
              + '<path d="M0,114 H180" stroke="#000" stroke-width="1.6"/><rect x="0" y="116" width="180" height="10" fill="url(#h1)"/>'
              + '<path d="M16,114 C14,90 20,70 12,52 M12,52 C4,50 0,56 -2,58 M12,52 C18,46 26,48 30,52 M12,52 C10,44 14,40 20,40 M12,52 C6,44 0,44 -4,46" fill="none" stroke="#000" stroke-width="1.6"/>'
              + '<path d="M168,114 C166,92 170,76 164,60 M164,60 C158,56 152,60 150,64 M164,60 C170,54 178,56 182,60 M164,60 C164,52 170,48 176,50" fill="none" stroke="#000" stroke-width="1.6"/>')

# Coast: a breaking wave off Haystack Rock, a board on the sand.
V["coast"] = ('<circle cx="140" cy="34" r="12" fill="#fff" stroke="#000" stroke-width="1.4"/>' + rays(140, 34, 15, 26, math.pi, 2 * math.pi, 11)
              + '<path d="M118,72 C120,50 130,40 140,42 C150,44 156,58 160,72 Z" fill="#000"/>'
              + '<path d="M128,72 C130,58 136,50 142,50" fill="none" stroke="#fff" stroke-width="1"/>'
              + '<path d="M0,110 C10,80 30,40 70,34 C96,30 112,48 104,62 C98,72 84,68 86,60 C88,54 96,56 94,60 C88,50 70,52 60,66 C48,82 50,100 62,110 Z" fill="#000"/>'
              + '<path d="M10,104 C20,74 40,48 70,42 M20,106 C28,82 44,62 64,56 M30,108 C36,92 46,78 58,72" fill="none" stroke="#fff" stroke-width="1.2"/>'
              + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#000"/>' for x, y, r in ((98, 30, 2), (106, 36, 1.5), (110, 44, 1.2), (88, 26, 1.4), (114, 52, 1)))
              + '<path d="M60,110 C90,104 130,108 180,104" fill="none" stroke="#000" stroke-width="1.2"/>'
              + water(78, 102, 4, 5, 100, 180)
              + '<path d="M120,118 C130,112 160,112 172,116 C160,120 130,122 120,118 Z" fill="#fff" stroke="#000" stroke-width="1.4"/><path d="M124,117 H168" stroke="#000" stroke-width=".8"/>'
              + '<rect x="0" y="112" width="120" height="14" fill="url(#h2)"/>')

# Alfred: the cloche on its salver.
V["alfred"] = ('<path d="M40,84 A50,46 0 0 1 140,84 Z" fill="#fff" stroke="#000" stroke-width="2"/>'
               + '<path d="M50,82 A40,38 0 0 1 72,46" fill="none" stroke="#000" stroke-width="1"/><path d="M58,80 A34,32 0 0 1 74,54" fill="none" stroke="#000" stroke-width=".8"/>'
               + '<path d="M140,84 A50,46 0 0 0 112,44 L100,84 Z" fill="url(#h1)"/>'
               + '<ellipse cx="90" cy="34" rx="8" ry="5" fill="#000"/><path d="M90,38 V40" stroke="#000" stroke-width="2"/>'
               + '<path d="M20,86 H160 L150,96 H30 Z" fill="#fff" stroke="#000" stroke-width="1.8"/><path d="M30,92 H150" stroke="#000" stroke-width=".8"/>'
               + '<path d="M40,96 L36,104 M140,96 L144,104" stroke="#000" stroke-width="1.6"/>'
               + "".join(f'<g transform="translate({x},{y}) scale({s})">{STAR}</g>' for x, y, s in ((48, 30, 1), (134, 28, .8), (150, 52, .6), (28, 56, .6))))

# End: the dog asleep by the door, the day begun.
V["end"] = ('<path d="M0,104 H180" stroke="#000" stroke-width="1.4"/><rect x="0" y="105" width="180" height="20" fill="url(#hh)"/>'
            + '<path d="M40,104 C36,86 52,72 78,72 C104,70 128,76 136,92 C140,100 138,104 132,104 Z" fill="#fff" stroke="#000" stroke-width="1.6"/>'
            + '<path d="M78,72 C104,70 128,76 136,92 C140,100 138,104 132,104 L96,104 C110,96 112,84 96,78 Z" fill="url(#h1)"/>'
            + '<path d="M40,104 C30,104 26,96 30,90 C34,84 44,84 48,88 C52,92 50,100 44,104 Z" fill="#fff" stroke="#000" stroke-width="1.6"/>'
            + '<path d="M36,86 C42,80 50,84 50,92 C46,90 40,90 36,86 Z" fill="#000"/>'
            + '<path d="M32,94 q3,2 6,0" fill="none" stroke="#000" stroke-width="1.2"/><circle cx="27" cy="96" r="2" fill="#000"/>'
            + '<path d="M136,98 C150,100 156,92 150,86" fill="none" stroke="#000" stroke-width="2.6" stroke-linecap="round"/>'
            + '<path d="M52,104 L66,104" stroke="#000" stroke-width="1.6"/>'
            + '<text x="58" y="58" font-family="Georgia,serif" font-style="italic" font-size="16">z</text><text x="70" y="44" font-family="Georgia,serif" font-style="italic" font-size="20">z</text>'
            + '<path d="M140,40 l16,0 0,16 c0,8 -16,8 -16,0 Z M156,44 c6,0 6,8 0,8" fill="#fff" stroke="#000" stroke-width="1.6"/><path d="M134,62 H162" stroke="#000" stroke-width="1.6"/>'
            + '<path d="M144,34 c-3,-4 3,-6 0,-10 M152,34 c-3,-4 3,-6 0,-10" fill="none" stroke="#000" stroke-width="1"/>')

# The cover panorama: Hood, the river, St. Johns' towers, firs, sunrise. 570 x 64.
def panorama():
    W, H = 570, 64
    out = [rays(300, 50, 14, 300, math.pi * 1.0, math.pi * 2.0, 61, .7),
           f'<rect x="0" y="50" width="{W}" height="20" fill="#fff"/>',
           '<path d="M286,50 A14,14 0 0 1 314,50 Z" fill="#fff" stroke="#000" stroke-width="1.4"/>',
           '<path d="M290,46 H310 M294,42 H306" stroke="#000" stroke-width="1"/>',
           hood(400, 51, .5),
           '<path d="M470,51 L488,38 L496,36 L504,38 L522,51 Z" fill="#fff" stroke="#000" stroke-width="1.2"/><path d="M496,36 L504,38 L522,51 L500,51 Z" fill="url(#h1)"/>',
           '<path d="M0,50 C60,46 120,52 200,49 C260,47 340,52 420,48 C480,45 520,50 570,47 L570,55 L0,55 Z" fill="#000"/>',
           firs(list(range(6, 100, 9)), 52, 14), firs(list(range(530, 570, 9)), 52, 13),
           f'<g transform="translate(130,19) scale(.44)">{TOWER}</g><g transform="translate(206,19) scale(.44)">{TOWER}</g>',
           '<path d="M100,50 Q118,34 130,20 Q168,52 206,20 Q218,34 236,50" fill="none" stroke="#000" stroke-width="1.2"/>',
           "".join(f'<line x1="{x}" y1="{f(20 + 30 * (1 - ((x - 168) / 38) ** 2))}" x2="{x}" y2="44" stroke="#000" stroke-width="1"/>' for x in range(140, 200, 6)),
           '<path d="M100,44 H236" stroke="#000" stroke-width="1.6"/>',
           water(57, 64, 3.4, 9, 0, W),
           heron(548, 47, .5), bird_v(350, 18), bird_v(362, 24), bird_v(260, 14, 1.2)]
    return W, H, "".join(out)


WEATHER = {}
WEATHER["sun"] = sun(30, 30, 10, 16)
WEATHER["cloud"] = ('<path d="M10,44 C2,44 2,32 10,32 C10,22 24,18 30,26 C34,16 52,18 52,30 C60,30 60,44 52,44 Z" fill="#fff" stroke="#000" stroke-width="1.8"/>'
                    '<path d="M10,44 C6,40 8,36 12,36 L52,36 C58,38 56,44 52,44 Z" fill="url(#hh)"/>')
WEATHER["part"] = (rays(40, 24, 12, 20, math.pi * .9, math.pi * 2.1, 9, 1.1) + '<circle cx="40" cy="24" r="9" fill="#fff" stroke="#000" stroke-width="1.6"/>'
                   + '<g transform="translate(-4,6)">' + WEATHER["cloud"] + '</g>')
WEATHER["rain"] = WEATHER["cloud"] + "".join(f'<path d="M{x},48 l-4,9" stroke="#000" stroke-width="1.6" stroke-linecap="round"/>' for x in (18, 28, 38, 48))
WEATHER["fog"] = WEATHER["cloud"] + '<path d="M6,50 H54 M12,55 H50" stroke="#000" stroke-width="1.6"/>'
WEATHER["snow"] = WEATHER["cloud"] + "".join(f'<g transform="translate({x},{y}) scale(.7)">{STAR}</g>' for x, y in ((18, 52), (32, 56), (46, 52)))
WEATHER["storm"] = WEATHER["cloud"] + '<path d="M32,44 L26,54 L32,54 L28,62 L40,50 L34,50 L38,44 Z" fill="#000"/>'

DIALECT = {"today": "acanthus", "roads": "acanthus", "family": "nouveau", "solar": "deco", "garden": "nouveau",
           "river": "woodcut", "nearby": "acanthus", "news": "acanthus", "markets": "guilloche", "civics": "laurel",
           "sports": "laurel", "music": "deco", "watch": "deco", "local": "acanthus", "almanac": "nouveau",
           "science": "guilloche", "doodles": "nouveau", "delights": "nouveau", "world": "kranok", "coast": "woodcut"}


# ================================================================ the cover, twice as ornate
def sternwheeler(x, y, s=1.0):
    return (f'<g transform="translate({f(x)},{f(y)}) scale({f(s)})">'
            '<path d="M-30,0 L28,0 L24,6 L-26,6 Z" fill="#000"/>'
            '<rect x="-24" y="-8" width="44" height="8" fill="#fff" stroke="#000" stroke-width="1.2"/>'
            '<path d="M-20,-8 V0 M-12,-8 V0 M-4,-8 V0 M4,-8 V0 M12,-8 V0" stroke="#000" stroke-width="1"/>'
            '<rect x="-16" y="-15" width="28" height="7" fill="#fff" stroke="#000" stroke-width="1.2"/>'
            '<rect x="-6" y="-20" width="12" height="5" fill="#000"/>'
            '<path d="M-12,-15 V-30 M-8,-15 V-28" stroke="#000" stroke-width="2"/><path d="M-14,-31 H-6" stroke="#000" stroke-width="1.4"/>'
            '<path d="M24,-10 A10,10 0 0 1 24,10" fill="#fff" stroke="#000" stroke-width="1.4"/>'
            '<path d="M24,0 L33,-4 M24,0 L34,0 M24,0 L33,4 M24,0 L30,-8 M24,0 L30,8" stroke="#000" stroke-width="1"/></g>')


def cover_scene_inner():
    """330 x 112: sunburst, Mt. Hood, St. Johns Bridge, the Columbia with a sternwheeler, firs."""
    out = [rays(190, 70, 14, 260, math.pi * 1.0, math.pi * 2.0, 49, 1),
           '<rect x="0" y="70" width="330" height="50" fill="#fff"/>',
           '<path d="M176,70 A14,14 0 0 1 204,70 Z" fill="#fff" stroke="#000" stroke-width="1.6"/>',
           '<path d="M180,66 H200 M184,62 H196" stroke="#000" stroke-width="1"/>',
           hood(236, 72, .72),
           '<path d="M0,70 C50,66 100,72 160,69 C220,66 280,72 330,68 L330,76 L0,76 Z" fill="#000"/>',
           firs(list(range(4, 40, 8)), 72, 18), firs(list(range(292, 330, 8)), 72, 18),
           f'<g transform="translate(70,26) scale(.6)">{TOWER}</g><g transform="translate(140,26) scale(.6)">{TOWER}</g>',
           '<path d="M40,70 Q58,46 70,27 Q105,72 140,27 Q152,46 170,70" fill="none" stroke="#000" stroke-width="1.4"/>',
           "".join(f'<line x1="{x}" y1="{f(27 + 34 * (1 - ((x - 105) / 35) ** 2))}" x2="{x}" y2="62" stroke="#000" stroke-width="1"/>' for x in range(76, 136, 6)),
           '<path d="M40,62 H170" stroke="#000" stroke-width="2"/>',
           water(80, 112, 4, 21, 0, 330),
           '<rect x="210" y="84" width="96" height="22" fill="#fff"/>',
           sternwheeler(258, 100, .95),
           bird_v(260, 30, 1.3), bird_v(276, 38), bird_v(120, 12, 1.1)]
    return "".join(out)


def cover_scene():
    """570 x 124: the scene in an arched, beaded frame, set in acanthus wings that hold two
    roundels: the dog on the left, the drum kit on the right."""
    W, H = 570, 124
    wing = f'<g transform="translate(0,14) scale(.62)">{WING_SRC()}</g>'
    out = [wing, f'<g transform="translate({W},0) scale(-1,1)">{wing}</g>']
    for cx, vg, sc, dx, dy in ((62, DOG_ONLY, .42, -97, -72), (W - 62, V["music"], .33, -90, -76)):
        out.append(f'<circle cx="{cx}" cy="62" r="31" fill="#fff" stroke="#000" stroke-width="2"/>')
        out.append("".join(f'<circle cx="{f(cx + 27.5 * math.cos(2 * math.pi * i / 26))}" cy="{f(62 + 27.5 * math.sin(2 * math.pi * i / 26))}" r="1.1" fill="#000"/>' for i in range(26)))
        out.append(f'<circle cx="{cx}" cy="62" r="24" fill="#fff" stroke="#000" stroke-width="1.2"/>')
        out.append(f'<g clip-path="url(#r{cx})"><g transform="translate({cx},62) scale({sc}) translate({dx},{dy})">{vg}</g></g>')
    arch = "M120,122 V34 Q120,4 150,4 H420 Q450,4 450,34 V122 Z"
    inner = "M126,116 V36 Q126,10 152,10 H418 Q444,10 444,36 V116 Z"
    out.append(f'<path d="{arch}" fill="#fff" stroke="#000" stroke-width="2.2"/>')
    out.append(f'<g clip-path="url(#sc)"><g transform="translate(120,6)">{cover_scene_inner()}</g></g>')
    out.append(f'<path d="{inner}" fill="none" stroke="#000" stroke-width="1.2"/>')
    defs = ('<clipPath id="sc"><path d="' + inner + '"/></clipPath>'
            + f'<clipPath id="r62"><circle cx="62" cy="62" r="23"/></clipPath><clipPath id="r{W - 62}"><circle cx="{W - 62}" cy="62" r="23"/></clipPath>')
    return W, H, "".join(out), defs


def crest_laurel():
    """150 x 66: the owner's oval, laurel branches round it, a prajam yam above. The P is set in type."""
    out = []
    for sgn in (-1, 1):
        for i in range(7):
            a = math.pi / 2 + sgn * (0.55 + i * 0.3)
            x, y = 75 + 40 * math.cos(a), 34 + 30 * math.sin(a)
            d = math.degrees(a) + (90 if sgn > 0 else -90)
            out.append(f'<g transform="translate({f(x)},{f(y)}) rotate({f(d)})"><path d="M0,0 C3,-6 11,-6 15,0 C11,6 3,6 0,0 Z" fill="{"#000" if i % 2 else "url(#h1)"}" stroke="#000" stroke-width="1"/></g>')
        P = [(75 + 40 * math.cos(math.pi / 2 + sgn * (0.4 + i * .1)), 34 + 30 * math.sin(math.pi / 2 + sgn * (0.4 + i * .1))) for i in range(21)]
        out.append(f'<polyline points="{pts(P)}" fill="none" stroke="#000" stroke-width="1.4"/>')
    out.append('<path d="M63,62 L75,56 L87,62 L80,64 L75,61 L70,64 Z" fill="#000"/>')
    out.append('<ellipse cx="75" cy="33" rx="22" ry="25" fill="#fff" stroke="#000" stroke-width="2.4"/>')
    out.append('<ellipse cx="75" cy="33" rx="17.5" ry="20.5" fill="none" stroke="#000" stroke-width="1"/>')
    out.append("".join(f'<circle cx="{f(75 + 19.8 * math.cos(a))}" cy="{f(33 + 22.8 * math.sin(a))}" r="1" fill="#000"/>' for a in [i * 2 * math.pi / 30 for i in range(30)]))
    out.append(prajam(75, 5, 4.5))
    return "".join(out)


# ---------------------------------------------------------------- plates and CSS
SECS = list(DIALECT)


def write_plates(out):
    os.makedirs(os.path.join(out, "orn", "kit"), exist_ok=True)
    for k_, s_ in KIT.items():
        with open(os.path.join(out, "orn", "kit", k_ + ".svg"), "w") as f_:
            f_.write(snap(s_))
    d = os.path.join(out, "orn")
    os.makedirs(d, exist_ok=True)
    tp = eng("engraving_book", "tailpiece")
    import zlib
    for s in SECS:
        v = vignette(s)
        open(os.path.join(d, f"{s}.svg"), "w").write(banner(v, DIALECT[s]))
        open(os.path.join(d, f"{s}-m.svg"), "w").write(medallion(v))
        try:
            t_ = tp(570, 236, zlib.crc32(s.encode()) % 10000, TAIL_THEME.get(s, "foliage")) if tp else None
        except Exception:  # noqa: BLE001
            t_ = None
        open(os.path.join(d, f"{s}-tail.svg"), "w").write(t_ or tailpiece(v, DIALECT[s]))
    open(os.path.join(d, "alfred.svg"), "w").write(medallion(V["alfred"], 150, 106))
    open(os.path.join(d, "end.svg"), "w").write(banner(V["end"], "acanthus"))
    W, H, body = panorama()
    open(os.path.join(d, "pano.svg"), "w").write(svg(W, H, body))
    wg = eng("engraving_instruments", "weather_glyph")
    kinds = {"sun": "clear", "cloud": "cloudy", "part": "partly", "rain": "rain", "fog": "fog", "snow": "snow", "storm": "thunder"}
    for k, b in WEATHER.items():
        try:
            g_ = wg(kinds[k], 64) if wg else None
        except Exception:  # noqa: BLE001
            g_ = None
        open(os.path.join(d, f"wx-{k}.svg"), "w").write(g_ or svg(60, 64, b))
    cr = eng("engraving_morning", "crest")
    try:
        c_ = nest(cr("crest", 64), 43, 1, 64, 64) if cr else None
    except Exception:  # noqa: BLE001
        c_ = None
    open(os.path.join(d, "crest.svg"), "w").write(svg(150, 66, c_ or crest_laurel()))
    W, H, body, defs = cover_scene()
    open(os.path.join(d, "scene.svg"), "w").write(svg(W, H, body, defs))
    # Inverse plates, used sparingly: the night sky, the record sleeve, the end of the edition
    for s in INVERSE:
        open(os.path.join(d, f"{s}-inv.svg"), "w").write(inverse(open(os.path.join(d, f"{s}.svg")).read()))
        open(os.path.join(d, f"{s}-m-inv.svg"), "w").write(inverse(open(os.path.join(d, f"{s}-m.svg")).read()))
    open(os.path.join(d, "end-inv.svg"), "w").write(inverse(open(os.path.join(d, "end.svg")).read()))


INVERSE = ("nearby", "music")


def eng(mod, name):
    """An engraver's piece if their module is installed (solar/<mod>.py, or importable), else None.
    Every slot below falls back to this module's own drawing."""
    import importlib
    for m in ((f".{mod}", __package__) if __package__ else (), (mod, None)):
        if not m:
            continue
        try:
            return getattr(importlib.import_module(*m), name)
        except Exception:  # noqa: BLE001  a missing or broken engraver never breaks the edition
            pass
    return None


VIG_KEY = {"today": "sunrise", "roads": "road", "family": "toddler", "solar": "solarpanel", "garden": "garden", "river": "heron",
           "nearby": "sky", "news": "newspaper", "markets": "markets", "civics": "civics", "sports": "sports", "music": "jazz",
           "watch": "screen", "local": "portland", "almanac": "almanac", "science": "science", "doodles": "doodles",
           "delights": "delights", "world": None, "coast": "coast"}


def nest(svg_str, x, y, w, h):
    """Place a complete <svg> inside another at x, y, w x h."""
    m = re.search(r"<svg\b[^>]*>", svg_str)
    tag = re.sub(r'\s(?:x|y|width|height)="[^"]*"', "", m.group(0))
    return svg_str[:m.start()] + tag.replace("<svg", f'<svg x="{x}" y="{y}" width="{w}" height="{h}"', 1) + svg_str[m.end():]


def vignette(s):
    """Slot: the section's vignette, 180 x 124. The engravers' MORNING_VIGNETTES win when present."""
    mv = eng("engraving_morning_vignettes", "MORNING_VIGNETTES") or {}
    k = VIG_KEY.get(s)
    if k and k in mv:
        return nest(mv[k], 0, 2, 180, 120)
    if s == "world":
        tv = eng("engraving_thai", "thai_vignettes")
        try:
            return nest(tv()["wat_arun"], 0, 2, 180, 120)
        except Exception:  # noqa: BLE001
            pass
    return V.get(s, V["today"])


FRAME_BAND = {"world": "kranok", "coast": "woodcut", "river": "reeds", "garden": "nouveau", "family": "nouveau", "delights": "nouveau",
              "almanac": "nouveau", "doodles": "nouveau", "music": "deco", "watch": "deco", "solar": "sun", "markets": "guilloche",
              "science": "guilloche", "sports": "laurel", "civics": "laurel"}


def write_frames(out, seed, sun_text=""):
    """Today's page frames (one refined border per section, the inverse ones in velvet black), the cover
    plate, and the scenes that fill each page's free space."""
    d = os.path.join(out, "orn")
    os.makedirs(d, exist_ok=True)
    cp = eng("engraving_morning", "cover_plate")       # the daily cover plate replaces the panorama scene
    if cp:
        import datetime
        try:
            day = {"date": datetime.date.fromisoformat(str(seed)[:10]), "moon_phase": moon_phase(seed),
                   "sunrise": sun_text.replace("Sunrise ", "") or None}
            day["edition_no"] = day["date"].timetuple().tm_yday
            day.update(COVER_DAY)
            open(os.path.join(d, "scene.svg"), "w").write(cp(day, 570))      # native 570 x 324, shown at exactly 570 px
        except Exception:  # noqa: BLE001
            pass
    import glob as _g
    for f_ in _g.glob(os.path.join(d, "frame-*.svg")) + _g.glob(os.path.join(d, "scene-*.svg")) + _g.glob(os.path.join(d, "art-*.svg")):
        os.remove(f_)        # earlier frames and fills: never shipped again
    HF = _hunt()
    import zlib
    open(os.path.join(d, "frame.svg"), "w").write(HF.page_frame(None, 0))
    for s in SECS + ["edition", "end"]:
        open(os.path.join(d, f"motif-{s}.svg"), "w").write(HF.motif_tablet(s if s in HF.MOTIFS else "edition"))
    open(os.path.join(d, "gap.svg"), "w").write(HF.gap_bar(232, 20, 1))
    snap_dir(d)


def _hunt():
    try:
        from . import kindle_frame as HF      # in the package
    except ImportError:
        sys.path.insert(0, os.path.join(HERE, "hunt"))
        import hunt_frame as HF
    return HF


def outline_z(doc):
    """An image-SVG cannot use the page's fonts (and the Kindle has no Georgia): the sleeping dog's z's are drawn as paths."""
    def z(m):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        x, y, f = float(a.get("x", 0)), float(a.get("y", 0)), float(a.get("font-size", 16))
        w = f * .42
        sw = 1 if f >= 14 else .5
        return (f'<path d="M{x:.1f},{y - f * .45:.1f}h{w:.1f}l{-w:.1f},{f * .45:.1f}h{w:.1f}" fill="none" stroke="{a.get("fill", "#000")}" '
                f'stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>')
    return re.sub(r"<text\b([^>]*)>\s*z\s*</text>", z, doc)


def snap_dir(d):
    """Every engraved file through the e-ink normaliser: the engravers' own snap_svg when installed, else snap."""
    sn = eng("snap_svg", "snap")
    if sn:
        sn.__globals__["FINE_MAX"] = .6      # 0.6 px and up print at 1 px: solid black, not two half-greys
    for fn in os.listdir(d):
        if not fn.endswith(".svg"):
            continue
        p = os.path.join(d, fn)
        doc = outline_z(dedupe_attrs(open(p).read()))
        try:
            out = sn(doc) if sn else None
        except Exception:  # noqa: BLE001
            out = None
        inv = "-inv" in fn or fn in INVERSE_FRAMES
        out = snap(out, inverse=True) if inv and isinstance(out, str) and out.startswith("<") else out
        out = out if isinstance(out, str) and out.startswith("<") else snap(doc, inverse=inv)
        open(p, "w").write(out)


def dedupe_attrs(doc):
    """Repair a tag that names an attribute twice (invalid XML, so the browser drops the whole image): the last one wins."""
    def fix(m):
        seen = {}
        for a in re.finditer(r'\s([\w:-]+)="[^"]*"', m.group(2)):
            seen[a.group(1)] = a.group(0)
        if len(seen) == len(re.findall(r'\s[\w:-]+="', m.group(2))):
            return m.group(0)
        return "<" + m.group(1) + "".join(seen.values()) + m.group(3)
    return re.sub(r'<([\w:]+)((?:\s[\w:-]+="[^"]*")+)(\s*/?>)', fix, doc)


INVERSE_FRAMES = ("frame-nearby.svg", "frame-music.svg", "frame-end.svg")


LEGEND = {"today": "Carpe diem", "roads": "Iter et via", "family": "Domus", "solar": "Sol invictus", "garden": "Hortus",
          "river": "Flumen", "nearby": "Ad astra", "news": "Nuntii", "markets": "Pecunia", "civics": "Res publica",
          "sports": "Victoria", "music": "Musica", "watch": "Spectacula", "local": "Urbs", "almanac": "Annales",
          "science": "Scientia", "doodles": "Numeri", "delights": "Delectatio", "world": "Siam", "coast": "Mare",
          "edition": "Sauvie Island", "end": "Finis"}
TAIL_THEME = {"today": "sun", "roads": "foliage", "family": "dog", "solar": "sun", "garden": "roses", "river": "reeds",
              "nearby": "stars", "news": "foliage", "markets": "vines", "civics": "foliage", "sports": "foliage", "music": "jazz",
              "watch": "notes", "local": "portland", "almanac": "stars", "science": "stars", "doodles": "vines",
              "delights": "roses", "world": "thai", "coast": "surf", "end": "dog"}
PLATE_HEIGHTS = tuple(range(60, 421, 30))     # the plates are cut every 30 px; a gap shows at most 15 px of ground each side
COVER_DAY = {}     # temp_f, sky, river_ft, tide from the edition's data, when the builder has them
BAND = 24          # the frame band; the reading panel starts 10 px inside it (html.kme --m: 34px)


def engraved_frame(s, seed, sun_text, corners, moon):
    """The engravers' page frame (engraving_frames.page_frame, or the Thai kranok border for Thailand),
    its four empty corner slots filled: the section vignette, tonight's moon on the cover, the dog,
    the coast. None if no engraver module is installed, and the caller draws its own."""
    if s == "world" and eng("engraving_thai", "kranok_border"):
        try:
            return eng("engraving_thai", "kranok_border")(618, 714, f"{seed}", BAND)
        except Exception:  # noqa: BLE001
            return None
    pf, fm = eng("engraving_frames", "page_frame"), eng("engraving_frames", "frame_metrics")
    if not (pf and fm):
        return None
    try:
        doc = pf(width=618, height=714, seed=f"{seed}", section_key=s, band=BAND, top_legend=LEGEND.get(s),
                 bottom_legend=sun_text or None)
        slots = fm(618, 714, BAND)["slots"]
        r = fm(618, 714, BAND)["slot_diameter"] / 2
    except Exception:  # noqa: BLE001
        return None
    # legends at the 13 px floor, not compressed to fit
    doc = re.sub(r'font-size="1[01](?:\.\d+)?"', 'font-size="13"', doc)
    doc = re.sub(r'\s(?:textLength|lengthAdjust)="[^"]*"', "", doc)
    out = []
    for k, ((cx, cy), vg) in enumerate(zip(slots, corners)):
        if moon is not None and k == 1:
            out.append(slot_moon(cx, cy, r, moon, f"{seed}"))
            continue
        cid = f"fs{k}"
        out.append(f'<clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{r - 1}"/></clipPath>'
                   f'<circle cx="{cx}" cy="{cy}" r="{r - .5}" fill="#fff"/>'
                   f'<g clip-path="url(#{cid})"><g transform="translate({cx},{cy}) scale(.3) translate(-90,-62)">{vg}</g></g>'
                   f'<circle cx="{cx}" cy="{cy}" r="{r - .5}" fill="none" stroke="#000" stroke-width="1"/>')
    return doc.rsplit("</svg>", 1)[0] + "".join(out) + "</svg>"


def slot_moon(cx, cy, r, phase, seed):
    """Tonight's moon in a corner slot: an inverse roundel, velvet black, the moon white at its true phase."""
    import math
    rnd = seeded("slotstars", seed)
    m = r * .52
    lit = math.cos(2 * math.pi * phase)
    side = 1 if phase < .5 else -1
    tx = abs(lit) * m
    so = 1 if side > 0 else 0
    st = (0 if lit > 0 else 1) if side > 0 else (1 if lit > 0 else 0)
    stars = "".join(f'<circle cx="{cx + a:.1f}" cy="{cy + b:.1f}" r="{rnd.choice((.5, .7, .9))}" fill="#fff"/>'
                    for a, b in ((rnd.uniform(-r, r), rnd.uniform(-r, r)) for _ in range(30))
                    if m + 2 < math.hypot(a, b) < r - 2.5)
    return (f'<circle cx="{cx}" cy="{cy}" r="{r - .5}" fill="#000"/>{stars}'
            f'<circle cx="{cx}" cy="{cy}" r="{m:.1f}" fill="#444" stroke="#fff" stroke-width=".5"/>'
            f'<path d="M{cx},{cy - m:.1f} A{m:.1f},{m:.1f} 0 0 {so} {cx},{cy + m:.1f} A{tx:.1f},{m:.1f} 0 0 {st} {cx},{cy - m:.1f} Z" fill="#fff"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r - 2}" fill="none" stroke="#fff" stroke-width=".5"/>')


def tint():
    """The page ground: a banknote line tint, hairlines at a 2 px pitch, one device pixel in a light exact grey.
    It reads as an even pale engraved tone, with no stripe or wave of its own. Text prints on white over it (.kink)."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="2" viewBox="0 0 4 2">'
            '<path d="M0,.75H4" stroke="#bbb" stroke-width=".5" shape-rendering="crispEdges"/></svg>')


SCENE_CROPS = ((28, 140, 300, 160), (242, 140, 300, 160), (135, 28, 300, 160), (135, 150, 300, 160), (28, 28, 300, 160))   # firs and drums; bridge and dog; Hood in its sunburst; the Columbia and its sternwheeler; moon and sky


def write_scenes(d, seed):
    """The plates that fill the free space at the foot of a page: ONE engraved scene per page, cover-fitted to
    the space. Each page draws a different day's cover plate (sun, river, moon and eggs move with the date)
    through a different window (the firs and drums, Hood in its sunburst, the bridge and the dog, the
    Columbia with its sternwheeler). Thailand gets a kranok panel; pages with their own art use it."""
    import datetime
    cp = eng("engraving_morning", "cover_plate")
    base = datetime.date.fromisoformat(str(seed)[:10])
    for k in range(7):
        doc = None
        if cp:
            try:
                doc = dedupe_attrs(cp({"date": base - datetime.timedelta(days=17 * (k + 1)), "edition_no": None}, 570))
            except Exception:  # noqa: BLE001
                doc = None
        if not doc:
            W_, H_, body, defs = cover_scene()
            doc = svg(W_, H_, body, defs)
        for c, (x, y, w, h) in enumerate(SCENE_CROPS):
            m = re.search(r"<svg\b[^>]*>", doc)
            tag = re.sub(r'\s(?:viewBox|preserveAspectRatio|style|width|height)="[^"]*"', "", m.group(0))
            tag = tag.replace("<svg", f'<svg width="{w}" height="{h}" viewBox="{x} {y} {w} {h}" preserveAspectRatio="xMidYMid slice"', 1)
            open(os.path.join(d, f"scene-{k}{c}.svg"), "w").write(doc[:m.start()] + tag + doc[m.end():])
    kb = eng("engraving_thai", "kranok_band")
    try:
        t_ = kb(550, 220, f"{seed}") if kb else None
    except Exception:  # noqa: BLE001
        t_ = None
    if t_:
        open(os.path.join(d, "scene-world.svg"), "w").write(t_)
    art = ART_DIR if os.path.isdir(ART_DIR) else None
    for slug in (sorted(os.listdir(art)) if art else []):
        for f in ("tailpiece.svg", "plate.svg"):
            p = os.path.join(art, slug, f)
            if os.path.exists(p):
                open(os.path.join(d, f"art-{slug}.svg"), "w").write(dedupe_attrs(open(p).read()))
                break


ART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kindle_art")   # per-page art: <card-id or section>/
if not os.path.isdir(ART_DIR):
    ART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")


def fine_frame(s, seed, sun_text, W=618, H=714):
    """One refined engraved border: a heavy and a hair rule outside, a single continuous guilloche strand
    pair running round the page between them (one line, never a repeated block), a hair and a fine rule
    inside, and acanthus corner pieces. The day's sunrise is lettered in a small cartouche at the foot."""
    import math
    out = [f'<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" fill="none" stroke="#000" stroke-width="1"/>',
           f'<rect x="4.25" y="4.25" width="{W - 8.5}" height="{H - 8.5}" fill="none" stroke="#000" stroke-width=".5"/>',
           f'<rect x="13.75" y="13.75" width="{W - 27.5}" height="{H - 27.5}" fill="none" stroke="#000" stroke-width=".5"/>',
           f'<rect x="16.5" y="16.5" width="{W - 33}" height="{H - 33}" fill="none" stroke="#000" stroke-width="1"/>']
    # the strand: a closed path round the band's centre line, two sine waves in counter-phase
    per = 2 * (W - 18) + 2 * (H - 18)
    def at(u):          # point on the band centre line (inset 9) at arc length u
        u %= per; a, b = W - 18, H - 18
        if u < a: return 9 + u, 9, 0, 1
        u -= a
        if u < b: return W - 9, 9 + u, -1, 0
        u -= b
        if u < a: return W - 9 - u, H - 9, 0, -1
        u -= a
        return 9, H - 9 - u, 1, 0
    k = round(per / 22)
    for ph in (0, math.pi):
        pts = []
        for i in range(0, int(per) + 1, 1):
            x, y, nx, ny = at(i)
            d = 2.6 * math.sin(2 * math.pi * k * i / per + ph)
            pts.append(f"{x + nx * d:.2f},{y + ny * d:.2f}")
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#000" stroke-width=".5"/>')
    c = corner()
    for tx, sx, sy in ((0, 1, 1), (W, -1, 1), (0, 1, -1), (W, -1, -1)):
        ty = 0 if sy > 0 else H
        out.append(f'<g transform="translate({tx},{ty}) scale({sx},{sy})"><rect x="0" y="0" width="34" height="34" fill="#fff"/>'
                   f'<g transform="scale(.62)">{c}</g></g>')
    if sun_text:
        out.append(f'<rect x="{W / 2 - 62}" y="{H - 18}" width="124" height="18" fill="#fff" stroke="#000" stroke-width=".5"/>'
                   f'<text x="{W / 2}" y="{H - 5}" text-anchor="middle" font-family="Georgia,serif" font-size="13" font-style="italic" fill="#000">{sun_text}</text>')
    return svg(W, H, "".join(out))


def tail_plate(art, W, H, seed):
    """ONE composed plate for a leftover space of exactly W x H: a ruled frame, a sunburst engraved from the
    centre in fine rays, a line tint inside the burst, and the section's cul-de-lampe over it. Not a tile."""
    import math
    cx, cy = W / 2, H / 2
    rx, ry = min(W * .42, .75 * H + 60), H * .46
    rays = []
    n = 144
    for i in range(n):
        t = 2 * math.pi * i / n
        x0, y0 = cx + rx * math.cos(t), cy + ry * math.sin(t)
        rays.append(f"M{x0:.1f},{y0:.1f}L{cx + 2 * W * math.cos(t):.1f},{cy + 2 * W * math.sin(t):.1f}")
    inner = (f'<clipPath id="tpc"><rect x="5" y="5" width="{W - 10}" height="{H - 10}"/></clipPath>'
             f'<pattern id="tpl" width="4" height="2" patternUnits="userSpaceOnUse"><path d="M0,.75H4" stroke="#bbb" stroke-width=".5" shape-rendering="crispEdges"/></pattern>')
    body = (f'<rect x="5" y="5" width="{W - 10}" height="{H - 10}" fill="url(#tpl)"/>'
            f'<g clip-path="url(#tpc)"><path d="{"".join(rays)}" stroke="#777" stroke-width=".5" fill="none"/></g>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.1f}" ry="{ry:.1f}" fill="none" stroke="#000" stroke-width=".5"/>'
            + (nest(art, 8, 6, W - 16, H - 12) if art else "")
            + f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<rect x="4" y="4" width="{W - 8}" height="{H - 8}" fill="none" stroke="#000" stroke-width=".5"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{inner}</defs>{body}</svg>'


def velvet(doc):
    """An inverse frame keeps its band solid black: at reading distance a white-engraved band
    averages to grey, and the drama of the inverse plate is the depth of the black."""
    return re.sub(r'<rect[^>]*fill="url\(#b[vh]\)"/>', "", doc)


def crest():
    """The owner's crest: an oval cartouche between two small acanthus scrolls,
    a prajam yam above; the initial is set in type over it."""
    import math
    W, H = 132, 56
    half = (scroll(30, 30, 18, turns=1.4, start=-math.pi * .45, cw=-1, leafw=.62)
            + tendril("M66,30 C58,30 54,14 34,12", 1.6))
    body = (half + f'<g transform="translate({W},0) scale(-1,1)">{half}</g>'
            + '<ellipse cx="66" cy="30" rx="21" ry="24" fill="#fff" stroke="#000" stroke-width="2.2"/>'
            + '<ellipse cx="66" cy="30" rx="17" ry="20" fill="none" stroke="#000" stroke-width="1"/>'
            + "".join(f'<circle cx="{66 + 19 * math.cos(a):.1f}" cy="{30 + 22 * math.sin(a):.1f}" r="1" fill="#000"/>'
                      for a in [i * 2 * math.pi / 28 for i in range(28)])
            + prajam(66, 4, 4))
    return svg(W, H, body)


def kit():
    tl, tr, bl, br = corners()
    ptl, ptr, pbl, pbr = page_corners()
    rtl, rtr, rbl, rbr = rosette_corners()
    htl, htr, hbl, hbr = head_corners()
    v = {
        "r-tl": rtl, "r-tr": rtr, "r-bl": rbl, "r-br": rbr, "h-tl": htl, "h-tr": htr, "h-bl": hbl, "h-br": hbr,
        "term": terminal(), "terml": svg(18, 34, '<g transform="translate(18,0) scale(-1,1)">' + terminal().split('<defs>', 1)[1].split('</defs>', 1)[1].rsplit('</svg>', 1)[0] + '</g>'),
        "dotrule": svg(8, 8, '<path d="M0,4.25H8" stroke="#000" stroke-width=".5"/>'), "minifleur": svg(8, 8, ""), "initial2": initial_foliate(),
        "nummed": num_medallion(), "bigmed": big_medallion(),
        **{f"gv-{k}": vband(fn) for k, fn in GUTTER.items()}, **{f"gh-{k}": hband(fn) for k, fn in GUTTER.items()},
        "p-tl": ptl, "p-tr": ptr, "p-bl": pbl, "p-br": pbr, "tag": tag(),
        "beads": svg(8, 10, '<path d="M0,5.25H8" stroke="#000" stroke-width=".5"/>'), "purfling": band_purfling(),
        "kranok": svg(8, 22, '<path d="M0,15.5H8" stroke="#000" stroke-width="1"/><path d="M0,18.25H8" stroke="#000" stroke-width=".5"/>'),
        "acanthus": band_acanthus(), "deco": band_deco(), "woodcut": band_wave(), "nouveau": band_nouveau(),
        "fleuron": fleuron(), "initial": initial_box(), "lozenge": lozenge(), "swash": swash(),
        "c-tl": tl, "c-tr": tr, "c-bl": bl, "c-br": br,
    }
    out = []
    for k, s in v.items():   # small motifs stay inline; anything over 2 KB is a cached file (orn/kit/<name>.svg), never a :root data-URI
        u = uri(s)
        if len(u) > 2048:
            KIT[k] = s
            u = f"url(orn/kit/{k}.svg)"
        out.append(f"--orn-{k}:{u};")
    return "".join(out)


KIT = {}


def css():
    gut = {"world": "kranok", "coast": "woodcut", "river": "reeds", "garden": "nouveau", "family": "nouveau", "delights": "nouveau",
           "almanac": "nouveau", "doodles": "nouveau", "music": "deco", "watch": "deco", "solar": "sun", "markets": "guilloche",
           "science": "guilloche", "sports": "laurel", "civics": "laurel"}
    gut_of = "".join(f'html.kme body[data-ksec="{s_}"]{{--gv:var(--orn-gv-{gut[s_]});--gh:var(--orn-gh-{gut[s_]})}}\n' for s_ in gut)
    band_of = gut_of + "".join(
        f'html.kme body[data-ksec="{s}"]{{--band:var(--orn-{DIALECT[s]});--band-h:{BAND_H[DIALECT[s]]}px;'
        f'--plate:url(orn/{s}.svg);--med:url(orn/{s}-m.svg)}}\n' for s in SECS)
    frames = "".join(f'html.kme body[data-ksec="{s_}"]:before{{background-image:url(orn/motif-{s_}.svg),url(orn/frame.svg) !important}}\n' for s_ in SECS)
    frames += "".join(f'html.kme body[data-ksec="{s_}"]{{--plate:url(orn/{s_}-inv.svg);--med:url(orn/{s_}-m-inv.svg)}}\n' for s_ in INVERSE)
    frames += "".join(f'html.kme body[data-ksec="{s_}"] #kmain .kfhead:after{{background-color:#000 !important}}\n' for s_ in INVERSE)
    frames += ('html.kme body.kendpage:before{background-image:url(orn/motif-end.svg),url(orn/frame.svg) !important}\n'
               'html.kme .kendpage #kmain .kend:before{background-image:url(orn/end-inv.svg) !important}\n')
    t = re.sub(r"((?:background|background-image|box-shadow):[^;{}]*?)(?<!important)(?=[;}])", r"\1 !important", TEMPLATE)
    cpv = bool(eng("engraving_morning", "cover_plate"))
    arts = sorted(os.listdir(ART_DIR)) if os.path.isdir(ART_DIR) else []
    t = t.replace("ART_RULES", "".join(f'html.kme #ktail2[data-slug="{a_}"]{{background-image:url(orn/art-{a_}.svg) !important}}\n' for a_ in arts
                                       if any(os.path.exists(os.path.join(ART_DIR, a_, f)) for f in ("tailpiece.svg", "plate.svg"))))
    t = t.replace("FRAMES", frames).replace("SCENE_H", "299" if cpv else "118").replace("SCENE_W", "526" if cpv else "526")
    t = t.replace("SCENE_M", "0")   # the plate overhangs the panel into the frame's margin, kept pixel-exact
    t = t.replace("CREST_TEXT", "html.kme .kcontents #kmain .kear .kcrest{color:transparent !important}"
                  if eng("engraving_morning", "crest") else "")
    return t.replace("/*KIT*/", kit()).replace("/*BANDS*/", band_of)


BAND_H = {"laurel": 20, "guilloche": 14, "acanthus": 24, "kranok": 22, "nouveau": 20, "deco": 14, "woodcut": 18}

TEMPLATE = r"""
/* ===================================================================
   THE DESIGNER LAYER: engraved, private-press, for one reader.
   Part 1 is a shared kit (both editions may use it). Part 2 is scoped
   to html.kme, the class only the Morning Edition's pages carry.
   =================================================================== */

/* ---------- Part 1. Shared kit: display face, ornaments, frames ---------- */
:root{--k-disp:'Literata',Georgia,serif;--k-figs:'Literata',Georgia,serif;/*KIT*/}
.korn-band{display:block;height:22px;background:var(--orn-kranok) repeat-x 0 0/auto 22px}
.korn-beads{display:block;height:10px;background:var(--orn-beads) repeat-x 0 0/auto 10px}
.korn-fleuron{display:block;height:26px;background:var(--orn-fleuron) no-repeat center/140px 26px}
.korn-frame{position:relative;padding:14px 16px;
  background:var(--orn-c-tl) no-repeat 0 0/60px 60px,var(--orn-c-tr) no-repeat 100% 0/60px 60px,
             var(--orn-c-bl) no-repeat 0 100%/60px 60px,var(--orn-c-br) no-repeat 100% 100%/60px 60px}

/* ---------- Part 2. The Morning Edition ---------- */
/*BANDS*/
html.kme{--band:var(--orn-beads);--band-h:10px}

/* Running head: a Thai lozenge before the section, a double rule beneath. */
html.kme body .krun{border-bottom:3px double #000 !important;padding-bottom:4px !important}
html.kme body .krun>a:before{content:'';display:inline-block;width:11px;height:11px;margin:0 8px 0 0;vertical-align:-1px;
  background:var(--orn-lozenge) no-repeat center/11px 11px}
html.kme body .kbar{border-top:3px double #000 !important}
html.kme body .kbar #kmore{border:1px solid #000 !important;font-family:var(--k-disp) !important;font-style:italic;font-weight:700;letter-spacing:.02em;text-transform:none}

/* The whole page in an engraved frame: corners in the gutters, double rules between them. */
html.kme{background:
  var(--orn-p-tl) no-repeat 0 0/26px 26px,var(--orn-p-tr) no-repeat 100% 0/26px 26px,
  var(--orn-p-bl) no-repeat 0 100%/26px 26px,var(--orn-p-br) no-repeat 100% 100%/26px 26px,
  linear-gradient(#000,#000) no-repeat 2px 26px/1.6px calc(100% - 52px),linear-gradient(#000,#000) no-repeat 6px 26px/1px calc(100% - 52px),
  linear-gradient(#000,#000) no-repeat calc(100% - 2px) 26px/1.6px calc(100% - 52px),linear-gradient(#000,#000) no-repeat calc(100% - 6px) 26px/1px calc(100% - 52px),
  linear-gradient(#000,#000) no-repeat 26px 2px/calc(100% - 52px) 1.6px,linear-gradient(#000,#000) no-repeat 26px 6px/calc(100% - 52px) 1px,
  linear-gradient(#000,#000) no-repeat 26px calc(100% - 2px)/calc(100% - 52px) 1.6px,linear-gradient(#000,#000) no-repeat 26px calc(100% - 6px)/calc(100% - 52px) 1px,
  #fff;min-height:100%}
html.kme body{background:transparent}
/* The kicker's rule becomes a beaded inlay */
html.kme #kmain .kkick:after,html.kme #kmain .kkicker:after{height:10px;border:0;background:var(--orn-beads) repeat-x 0 0/auto 10px}
/* Section numbers and story counts sit in small engraved cartouches */
html.kme .ksecfront #kmain .kfnum,html.kme .ksecfront #kmain .kfhead:before{width:96px;height:28px;text-align:center;line-height:28px !important;background:var(--orn-tag) no-repeat 0 0/96px 28px}
html.kme .ksecfront #kmain .kfhead:before{font-size:14px !important;line-height:28px !important}

/* ===== Type: Literata throughout, heavy for display ===== */
html.kme #kmain h2,html.kme #kmain .kh2,html.kme #kmain .sci-title{font-family:var(--k-disp) !important;font-weight:800 !important;letter-spacing:-.005em !important}
html.kme #kmain .kkick,html.kme #kmain .kkicker{display:flex !important;align-items:center;color:#000 !important;letter-spacing:.16em !important}
html.kme #kmain .kkick:before,html.kme #kmain .kkicker:before{content:'';flex:none;width:10px;height:10px;margin:0 8px 0 0;background:var(--orn-lozenge) no-repeat center/10px 10px}
html.kme #kmain .kkick:after,html.kme #kmain .kkicker:after{content:'';-webkit-box-flex:1;flex:1 1 auto;min-width:16px;height:0;margin:0 0 0 10px;border-top:1px solid #000}
/* the numbers: heavy Literata, lining figures */
html.kme #kmain .tile .big,html.kme #kmain .mini .v,html.kme #kmain .kscore b,html.kme #kmain .kdeg,html.kme #kmain .big{
  font-family:var(--k-figs) !important;font-weight:900 !important;font-variant-numeric:lining-nums tabular-nums !important;letter-spacing:0 !important}
html.kme #kmain .mini .v small,html.kme #kmain .tile .u,html.kme #kmain .kdeg small{font-family:var(--k-serif) !important;font-weight:430 !important}
html.kme #kmain .tile .k,html.kme #kmain .mini .k{letter-spacing:.14em !important}

/* Card head: an engraved oval of the section, set into the head like a bookplate. */
html.kme.kme #kmain .sec-body>.card:first-child>.head:before,html.kme.kme #kmain>.head:first-child:before,html.kme.kme #kmain .kpanel:first-child>.head:before,html.kme.kme #kmain .kslot:first-child+.kpanel>.head:before,
html.kme.kme #kmain .sec-body>.card:first-child>.team-top:before{
  content:none;display:none}
html.kme body.ksecfront #kmain .head:before{display:none}

/* ===== The Cover ===== */
html.kme .kcontents #kmain .kmast{position:relative;padding:12px 16px 10px !important;margin:6px 0 12px !important;
  background:var(--orn-c-bl) no-repeat 0 100%/44px 44px,var(--orn-c-br) no-repeat 100% 100%/44px 44px}
html.kme .kcontents #kmain .kear{align-items:center !important;margin:0 26px 0 !important;font:600 13px/16px var(--k-serif) !important;letter-spacing:.14em !important}
html.kme .kcontents #kmain .kear span{-webkit-box-flex:1;flex:1 1 0;min-width:0}
html.kme .kcontents #kmain .kear span:last-child{text-align:right}
html.kme .kcontents #kmain .kear .kcrest{flex:none;width:132px;height:56px;position:relative;background:url(orn/crest.svg) no-repeat center/132px 56px;
  font:italic 900 28px/56px var(--k-disp);letter-spacing:0;text-align:center;text-transform:none}
html.kme .kcontents #kmain .kname{font:900 47px/56px var(--k-disp) !important;letter-spacing:-.01em !important;margin:2px 0 0 !important;white-space:nowrap}
html.kme .kcontents #kmain .kname i{font:italic 700 34px/58px var(--k-disp);margin-right:4px;vertical-align:4px}
html.kme .kcontents #kmain .kname:after{content:'';display:block;height:48px;margin:0;background:url(orn/pano.svg) no-repeat center/auto 48px}
html.kme .kcontents #kmain .kdate{border:0 !important;margin:2px 14px 0 !important;padding:15px 0 29px !important;font:600 13px/16px var(--k-serif) !important;letter-spacing:.1em !important;white-space:nowrap;
  background:var(--orn-beads) repeat-x 0 0/auto 10px,var(--orn-kranok) repeat-x 0 100%/auto 22px}
html.kme .kcontents #kmain .kgl{align-items:center !important;-webkit-box-pack:center;justify-content:center;border:0 !important;border-bottom:3px double #000 !important;margin:0 0 4px !important;padding:0 0 6px !important}
html.kme .kcontents #kmain .kgl:before{content:'';flex:none;width:54px;height:54px;margin:0 12px 0 0;background:url(orn/wx-cloud.svg) no-repeat center/50px 54px}
html.kme .kcontents #kmain .kgl.kwx-sun:before{background-image:url(orn/wx-sun.svg)}
html.kme .kcontents #kmain .kgl.kwx-part:before{background-image:url(orn/wx-part.svg)}
html.kme .kcontents #kmain .kgl.kwx-rain:before{background-image:url(orn/wx-rain.svg)}
html.kme .kcontents #kmain .kgl.kwx-fog:before{background-image:url(orn/wx-fog.svg)}
html.kme .kcontents #kmain .kgl.kwx-snow:before{background-image:url(orn/wx-snow.svg)}
html.kme .kcontents #kmain .kgl.kwx-storm:before{background-image:url(orn/wx-storm.svg)}
html.kme .kcontents #kmain .kgl .kdeg{font:900 56px/56px var(--k-figs) !important;letter-spacing:-.02em !important}
html.kme .kcontents #kmain .kgl .kdeg small{font:600 13px/18px var(--k-serif) !important;letter-spacing:.14em !important;text-transform:uppercase;white-space:nowrap;margin:0 0 6px 16px !important}
html.kme .kcontents #kmain .kresume{border:0 !important;padding:8px 14px !important;margin:0 0 12px !important;
  box-shadow:inset 0 0 0 1px #000,inset 0 0 0 4px #fff,inset 0 0 0 5px #000}
html.kme .kcontents #kmain .klab{text-align:center;padding:0 0 2px !important;margin:0 !important;
  background:var(--orn-fleuron) no-repeat center 0/120px 22px;padding-top:24px !important;letter-spacing:.2em !important}
html.kme .kcontents #kmain .kleads a{padding:5px 0 6px !important}
html.kme .kcontents #kmain .kleads a b{font:680 17px/23px var(--k-serif) !important}
html.kme .kcontents #kmain .kleads a:first-child b{font:800 26px/31px var(--k-disp) !important}
html.kme .kcontents #kmain .kleads a:last-child{border-bottom:3px double #000 !important}
/* Contents */
html.kme .kcontents #kmain .ktochead{font:italic 900 30px/34px var(--k-disp) !important;text-align:center;padding:0 0 26px !important;margin:0 0 0 !important;
  background:var(--orn-kranok) repeat-x 0 100%/auto 22px}
html.kme .kcontents #kmain .kpart{text-align:center;border:0 !important;margin:8px 0 0 !important;padding:0 0 2px !important;
  background:linear-gradient(#000,#000) no-repeat 0 8px/30% 1px,linear-gradient(#000,#000) no-repeat 100% 8px/30% 1px}
html.kme .kcontents #kmain .kn{font:italic 700 17px/1 var(--k-disp) !important;width:30px !important}

/* ===== Section fronts: one frame grammar, a dialect per section ===== */
html.kme .ksecfront #kmain .kfhead{display:flex !important;flex-direction:column;align-items:center;text-align:center;border:0 !important;
  padding:0 0 12px !important;margin:2px 0 4px !important;background:none;border-bottom:.5px solid #000 !important}
html.kme .ksecfront #kmain .kfhead>div{width:100%}
html.kme .ksecfront #kmain .kfhead{position:relative}
html.kme .ksecfront #kmain .kfnum{position:absolute;left:0;top:0;margin:0 !important;font:italic 700 17px/20px var(--k-disp) !important;letter-spacing:.04em}
html.kme .ksecfront #kmain .kfhead:before{content:attr(data-n) " pages";position:absolute;right:0;top:0;font:italic 430 15px/20px var(--k-serif)}
html.kme .ksecfront #kmain .kfhead[data-n="1"]:before{content:"1 page"}
html.kme .ksecfront #kmain .kfnum:before{content:'No. ';font-variant:small-caps}
html.kme .ksecfront #kmain .kfhead .kkick{-webkit-box-pack:center;justify-content:center;margin:1px 0 0 !important;min-height:20px}
html.kme .ksecfront #kmain .kfhead .kkick:before{display:none}
html.kme .ksecfront #kmain .kfhead .kkick:after{display:none}
html.kme .ksecfront #kmain .kfname{font:900 46px/50px var(--k-disp) !important;letter-spacing:-.01em !important;margin:2px 0 0 !important}
html.kme .ksecfront #kmain .kfsub{font:italic 430 15px/20px var(--k-serif) !important;margin:4px 70px 0 !important;padding:0 !important;border:0 !important}
html.kme .ksecfront #kmain .kfhead:after{content:'';order:5;display:block;width:100%;height:136px;margin:8px 0 0;background:var(--plate) no-repeat center/auto 100%}
html.kme .ksecfront #kmain .kfhead[data-n="1"]:after,html.kme .ksecfront #kmain .kfhead[data-n="2"]:after,html.kme .ksecfront #kmain .kfhead[data-n="3"]:after{height:150px}
html.kme .ksecfront #kmain .kfhead[data-n="6"]:after,html.kme .ksecfront #kmain .kfhead[data-n="7"]:after{height:100px;margin-top:4px}
html.kme .ksecfront #kmain .kfhead[data-n="8"]:after,html.kme .ksecfront #kmain .kfhead[data-n="9"]:after,html.kme .ksecfront #kmain .kfhead[data-n="10"]:after,
html.kme .ksecfront #kmain .kfhead[data-n="11"]:after,html.kme .ksecfront #kmain .kfhead[data-n="12"]:after{height:84px;margin-top:2px}
html.kme .ksecfront #kmain .kfl .kn{font:italic 700 20px/24px var(--k-disp) !important;width:40px !important}
html.kme .ksecfront #kmain .kfl a{border-bottom:1px solid #000 !important}
html.kme .ksecfront #kmain .kfl li:last-child a{border-bottom:3px double #000 !important}

/* Long sections: a smaller plate and a tighter list, chosen by the number of stories */
html.kme .ksecfront #kmain .kfhead[data-n="4"]:after,html.kme .ksecfront #kmain .kfhead[data-n="5"]:after{height:118px}
html.kme .ksecfront #kmain .kfhead[data-n="6"]+.kfl a{padding:8px 0 !important}
html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl li,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl li,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl li,
html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl li,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl li,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl li{margin:0 !important}
html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl .kt b,
html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl .kt b{line-height:22px !important}
html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl a,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl a,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl a,
html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl a,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl a,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl a{padding:6px 0 !important}
html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl small,
html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl small{display:none !important}
html.kme .ksecfront #kmain .kfhead[data-n="7"] .kfsub,html.kme .ksecfront #kmain .kfhead[data-n="8"] .kfsub,html.kme .ksecfront #kmain .kfhead[data-n="9"] .kfsub,
html.kme .ksecfront #kmain .kfhead[data-n="10"] .kfsub,html.kme .ksecfront #kmain .kfhead[data-n="11"] .kfsub,html.kme .ksecfront #kmain .kfhead[data-n="12"] .kfsub{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
html.kme .kcontents #kmain .kpartbox a{padding:3px 0 2px !important}
html.kme .kcontents #kmain .kt{font-size:17px !important}
html.kme .kcontents #kmain .kc{font-size:13px !important}

/* ===== Alfred: a letter on the house's stationery ===== */
html.kme #kmain .brief{position:relative;padding:10px 18px 14px !important;
  background:var(--orn-c-tl) no-repeat 0 0/48px 48px,var(--orn-c-tr) no-repeat 100% 0/48px 48px,
             var(--orn-c-bl) no-repeat 0 100%/48px 48px,var(--orn-c-br) no-repeat 100% 100%/48px 48px !important}
html.kme #kmain .brief-head{display:block !important;text-align:center}
html.kme #kmain .brief-head:before{content:'';display:block;height:72px;margin:0 auto 2px;background:url(orn/alfred.svg) no-repeat center/100px 72px}
html.kme #kmain .brief-head .kkicker{-webkit-box-pack:center;justify-content:center}
html.kme #kmain .brief-head .kkicker:before{display:none}
html.kme #kmain .brief-head .kkicker:after{display:none}
html.kme #kmain .brief-head .kkicker{background:var(--orn-fleuron) no-repeat center 100%/120px 22px;padding:0 0 26px !important;margin:0 0 6px !important}
html.kme #kmain .brief h2{max-width:440px;margin:0 auto 4px !important}
html.kme #kmain .brief h2,html.kme #kmain .brief h2 .aside{font:italic 700 27px/33px var(--k-disp) !important;text-align:center}
html.kme #kmain .kalfred{font:430 19px/28px var(--k-serif) !important}
html.kme #kmain .kalfred:first-letter{float:left;font:900 68px/58px var(--k-disp);margin:4px 10px 0 0;padding:6px 8px 4px;
  background:var(--orn-initial) no-repeat center/100% 100%}
html.kme #kmain .brief h3.sub{text-align:center}
html.kme #kmain .brief-sign{text-align:right}
html.kme #kmain .brief-sign .aside{display:inline-block;font:italic 700 22px/28px var(--k-disp) !important;padding:0 0 18px;
  background:var(--orn-swash) no-repeat 100% 100%/166px 20px}

/* ===== Drop caps and the poem ===== */
html.kme #kmain .poem-title{font:italic 800 30px/36px var(--k-disp) !important;display:block}
html.kme #kmain .poem-by{display:block;padding:0 0 28px !important;background:var(--orn-fleuron) no-repeat 0 100%/120px 22px}
html.kme #kmain .recap>b{font-family:var(--k-disp) !important;font-weight:800 !important}

/* Scores: a scoreboard in a double-ruled frame */
html.kme #kmain .kscore>div{box-shadow:inset 0 0 0 1px #000,inset 0 0 0 4px #fff,inset 0 0 0 5px #000;padding:10px 12px !important}
html.kme #kmain .kscore b{font-size:30px !important;line-height:36px !important}

/* "Also in": a fleuron above it */
html.kme #krail h4{padding-top:30px !important;background:var(--orn-fleuron) no-repeat center 0/140px 26px;text-align:center;border:0 !important}

/* ===== The end ===== */
html.kme .kendpage #kmain .kend{text-align:center;padding:4px 0 0}
html.kme .kendpage #kmain .kend:before{content:'';display:block;height:150px;background:url(orn/end.svg) no-repeat center/auto 150px}
html.kme .kendpage #kmain .kend .kkick{-webkit-box-pack:center;justify-content:center;margin:12px 0 0 !important}
html.kme .kendpage #kmain .kend .kkick:before,html.kme .kendpage #kmain .kend .kkick:after{display:none}
html.kme .kendpage #kmain .kend .kfname{font:italic 900 42px/48px var(--k-disp) !important;margin:6px 0 0 !important}
html.kme .kendpage #kmain .kend .kfsub{font:italic 430 17px/24px var(--k-serif) !important;margin:6px 0 0 !important;border:0 !important;padding:0 0 30px !important;
  background:var(--orn-kranok) repeat-x 0 100%/auto 22px}
html.kme .kendpage #kmain .kend .kbig{border:0 !important;margin:20px 40px 14px !important;font:italic 800 21px/54px var(--k-disp) !important;
  box-shadow:inset 0 0 0 2px #000,inset 0 0 0 5px #fff,inset 0 0 0 6px #000}
html.kme .kendpage #kmain .kendsrc:before{content:'\2014\00a0 30 \00a0\2014';display:block;margin:0 0 10px;font:italic 700 20px/24px var(--k-disp);letter-spacing:.2em}
html.kme .kendpage #kmain .kendsrc{font:italic 430 15px/20px var(--k-serif) !important}
html.kme .kendpage #kmain .kendsrc:after{content:'Set in Literata. Engraved and printed for one reader on Sauvie Island.';display:block;margin:6px 30px 0;font:600 13px/18px var(--k-serif);letter-spacing:.12em;text-transform:uppercase;font-style:normal}

/* ================= ROUND TWO: twice as ornate ================= */
/* Every page in a full engraved border: rosette corners, a dialect band down each side and across. */
html.kme{--gv:var(--orn-gv-acanthus);--gh:var(--orn-gh-acanthus)}
html.kme.kme{background:#fff}
html.kme body{background:
  var(--orn-r-tl) no-repeat 0 0/50px 50px,var(--orn-r-tr) no-repeat 100% 0/50px 50px,
  var(--orn-r-bl) no-repeat 0 100%/50px 50px,var(--orn-r-br) no-repeat 100% 100%/50px 50px,
  var(--gv) repeat-y 3px 0/12px auto,var(--gv) repeat-y calc(100% - 3px) 0/12px auto,
  var(--gh) repeat-x 0 3px/auto 12px,var(--gh) repeat-x 0 calc(100% - 3px)/auto 12px,#fff}
/* corners sit over the bands: the bands are clipped by a white ground behind each rosette */
html.kme body:before,html.kme body:after{content:'';position:fixed;z-index:0;width:50px;height:50px;pointer-events:none}
html.kme body .krun{margin:18px 0 12px !important;padding-left:30px !important;padding-right:30px !important;position:relative;z-index:1}
html.kme.kpaged body .kbar{margin:0 0 16px !important;padding:0 30px !important}
html.kme.kjumpopen #kjump{top:66px !important;bottom:70px !important}
html.kme body .kbar{border-top:.5px solid #000 !important;background:none !important;padding-top:0 !important}
html.kme body .krun{border-bottom:0 !important;background:var(--orn-beads) repeat-x 0 100%/auto 10px !important;padding-bottom:12px !important;height:44px !important}

/* Card titles in an engraved cartouche with scroll terminals */
html.kme #kmain .sec-body>.card:first-child>.head,html.kme #kmain>.head:first-child,html.kme #kmain .sec-body>.card:first-child>.team-top,html.kme #kmain .kpanel:first-child>.head,html.kme #kmain .kslot:first-child+.kpanel>.head{
  position:relative;padding:12px 22px 12px !important;margin:0 0 8px !important;
  background:var(--orn-h-tl) no-repeat 0 0/30px 30px,var(--orn-h-tr) no-repeat 100% 0/30px 30px,
    var(--orn-h-bl) no-repeat 0 100%/30px 30px,var(--orn-h-br) no-repeat 100% 100%/30px 30px,
    var(--orn-terml) no-repeat 0 50%/18px 34px,var(--orn-term) no-repeat 100% 50%/18px 34px,
    linear-gradient(#000,#000) no-repeat 1.5px 30px/1.6px calc(50% - 47px),linear-gradient(#000,#000) no-repeat 1.5px calc(100% - 30px)/1.6px calc(50% - 47px),
    linear-gradient(#000,#000) no-repeat calc(100% - 1.5px) 30px/1.6px calc(50% - 47px),linear-gradient(#000,#000) no-repeat calc(100% - 1.5px) calc(100% - 30px)/1.6px calc(50% - 47px),
    linear-gradient(#000,#000) no-repeat 30px 1.5px/calc(100% - 60px) 1.6px,linear-gradient(#000,#000) no-repeat 30px 5px/calc(100% - 60px) 1px,
    linear-gradient(#000,#000) no-repeat 30px calc(100% - 1.5px)/calc(100% - 60px) 1.6px,linear-gradient(#000,#000) no-repeat 30px calc(100% - 5px)/calc(100% - 60px) 1px}
/* note 5: the page's title cartouche on the first panel's head (over the panel rule that clears heads in panels) */
html.kme.kfit3 #kmain .facts[data-n="4"],html.kme.kfit3 #kmain .facts[data-n="8"]{grid-template-columns:1fr 1fr !important}   /* the facts stay two to a row (today-01), even squeezed */
html.kme{--kgap:28px}   /* Parker's scroll field needs 28 px of room between panels; a 40 px field round the page */
html.kme #kview #kmain .kpanel:first-child>.head,html.kme #kview #kmain .kslot:first-child+.kpanel>.head{position:relative !important;padding:12px 22px 12px !important;margin:0 0 8px !important;
  background:var(--orn-h-tl) no-repeat 0 0/30px 30px,var(--orn-h-tr) no-repeat 100% 0/30px 30px,
    var(--orn-h-bl) no-repeat 0 100%/30px 30px,var(--orn-h-br) no-repeat 100% 100%/30px 30px,
    var(--orn-terml) no-repeat 0 50%/18px 34px,var(--orn-term) no-repeat 100% 50%/18px 34px,
    linear-gradient(#000,#000) no-repeat 1.5px 30px/1.6px calc(50% - 47px),linear-gradient(#000,#000) no-repeat 1.5px calc(100% - 30px)/1.6px calc(50% - 47px),
    linear-gradient(#000,#000) no-repeat calc(100% - 1.5px) 30px/1.6px calc(50% - 47px),linear-gradient(#000,#000) no-repeat calc(100% - 1.5px) calc(100% - 30px)/1.6px calc(50% - 47px),
    linear-gradient(#000,#000) no-repeat 30px 1.5px/calc(100% - 60px) 1.6px,linear-gradient(#000,#000) no-repeat 30px 5px/calc(100% - 60px) 1px,
    linear-gradient(#000,#000) no-repeat 30px calc(100% - 1.5px)/calc(100% - 60px) 1.6px,linear-gradient(#000,#000) no-repeat 30px calc(100% - 5px)/calc(100% - 60px) 1px !important}
html.kme #kmain .sec-body>.card:first-child>.head:after,html.kme #kmain>.head:first-child:after,html.kme #kmain .sec-body>.card:first-child>.team-top:after,html.kme #kmain .kpanel:first-child>.head:after,html.kme #kmain .kslot:first-child+.kpanel>.head:after{content:'';display:block;clear:both}

/* Dividers: dots and diamonds; the lists that lead somewhere carry a small fleuron at the centre */
html.kme #kmain .lines>div,html.kme #kmain .story,html.kme #kmain .brief-rest>li{border-bottom:0 !important;background:var(--orn-dotrule) repeat-x 0 100%/auto 8px;padding-bottom:11px !important}
html.kme .ksecfront #kmain .kfl a,html.kme #krail a,html.kme .kcontents #kmain .kleads a{border-bottom:0 !important;
  background:var(--orn-minifleur) no-repeat 50% 100%/56px 12px,var(--orn-dotrule) repeat-x 0 calc(100% - 2px)/auto 8px;padding-bottom:14px !important}
html.kme .ksecfront #kmain .kfl li:last-child a{border-bottom:0 !important}
html.kme.kfit4 #kmain .lines>div,html.kme.kfit4 #kmain .story{background:none;border-bottom:1px solid #000 !important}

/* Drop caps: a foliate initial, the letter on a clear field */
html.kme #kmain .kalfred:first-letter,html.kme #kmain .recap p:first-letter{float:left;font:900 50px/50px var(--k-disp);margin:3px 10px 0 0;padding:12px 14px 10px;
  background:var(--orn-initial2) no-repeat center/100% 100%}

/* Alfred's card: a full engraved border, rosette corners */
html.kme #kmain .brief{padding:16px 26px 18px !important;
  background:var(--orn-r-tl) no-repeat 0 0/50px 50px,var(--orn-r-tr) no-repeat 100% 0/50px 50px,
    var(--orn-r-bl) no-repeat 0 100%/50px 50px,var(--orn-r-br) no-repeat 100% 100%/50px 50px,
    linear-gradient(#000,#000) no-repeat 2px 50px/1.8px calc(100% - 100px),linear-gradient(#000,#000) no-repeat 7px 50px/1px calc(100% - 100px),
    linear-gradient(#000,#000) no-repeat calc(100% - 2px) 50px/1.8px calc(100% - 100px),linear-gradient(#000,#000) no-repeat calc(100% - 7px) 50px/1px calc(100% - 100px),
    linear-gradient(#000,#000) no-repeat 50px 2px/calc(100% - 100px) 1.8px,linear-gradient(#000,#000) no-repeat 50px 7px/calc(100% - 100px) 1px,
    linear-gradient(#000,#000) no-repeat 50px calc(100% - 2px)/calc(100% - 100px) 1.8px,linear-gradient(#000,#000) no-repeat 50px calc(100% - 7px)/calc(100% - 100px) 1px !important}

/* Section fronts: a roman numeral in a beaded medal; list numbers in small medals */
html.kme .ksecfront #kmain .kfnum{width:56px !important;height:56px !important;line-height:56px !important;top:-4px !important;font:italic 800 19px/56px var(--k-disp) !important;letter-spacing:0;
  background:none}
html.kme .ksecfront #kmain .kfnum:before{content:none}
html.kme .ksecfront #kmain .kfhead>div{padding:0 62px;box-sizing:border-box}
html.kme .ksecfront #kmain .kfname{font-size:42px !important;line-height:48px !important}
html.kme .ksecfront #kmain .kfsub{margin:4px 0 0 !important}
html.kme .ksecfront #kmain .kfl .kn{flex:none;width:32px !important;height:32px;line-height:32px !important;margin:0 10px 0 0;text-align:center;font:italic 700 14px/32px var(--k-disp) !important;
  background:none;-webkit-align-self:center;align-self:center}
html.kme .ksecfront #kmain .kfl a{align-items:center !important}

/* The cover: the scene, the laurel crest, the leads in an inlaid panel */
html.kme .kcontents #kmain .kear .kcrest{width:150px !important;height:66px !important;background:url(orn/crest.svg) no-repeat center/150px 66px;font:italic 900 26px/66px var(--k-disp) !important;padding-bottom:4px}
html.kme .kcontents #kmain .kname:after{height:SCENE_Hpx !important;width:SCENE_Wpx;margin:4px 0 0 SCENE_Mpx !important;background:url(orn/scene.svg) no-repeat 0 0/SCENE_Wpx SCENE_Hpx}
CREST_TEXT
html.kme .kcontents #kmain .kleads{position:relative;padding:8px 20px 10px;margin:0 0 4px;
  background:var(--orn-h-tl) no-repeat 0 0/30px 30px,var(--orn-h-tr) no-repeat 100% 0/30px 30px,
    var(--orn-h-bl) no-repeat 0 100%/30px 30px,var(--orn-h-br) no-repeat 100% 100%/30px 30px,
    linear-gradient(#000,#000) no-repeat 1.5px 30px/1.6px calc(100% - 60px),linear-gradient(#000,#000) no-repeat 5px 30px/1px calc(100% - 60px),
    linear-gradient(#000,#000) no-repeat calc(100% - 1.5px) 30px/1.6px calc(100% - 60px),linear-gradient(#000,#000) no-repeat calc(100% - 5px) 30px/1px calc(100% - 60px),
    linear-gradient(#000,#000) no-repeat 30px 1.5px/calc(100% - 60px) 1.6px,linear-gradient(#000,#000) no-repeat 30px calc(100% - 1.5px)/calc(100% - 60px) 1.6px}
html.kme .kcontents #kmain .kleads a:nth-child(n+3){display:none !important}
html.kme .kcontents #kmain .kleads a:last-child{border-bottom:0 !important;background:none}
html.kme .kcontents #kmain .kleads a:nth-last-child(2){background:none}
html.kme .kcontents #kmain .ktoc .kpartbox{grid-column-gap:14px !important}
html.kme .kcontents #kmain .ktoc .kt{min-width:0}
html.kme .kcontents #kmain .ktoc{position:relative;padding:4px 18px 8px !important;
  background:var(--orn-h-tl) no-repeat 0 0/30px 30px,var(--orn-h-tr) no-repeat 100% 0/30px 30px,
    var(--orn-h-bl) no-repeat 0 100%/30px 30px,var(--orn-h-br) no-repeat 100% 100%/30px 30px,
    var(--orn-gv-kranok) repeat-y 0 30px/12px auto,var(--orn-gv-kranok) repeat-y 100% 30px/12px auto}


/* ================= ROUND THREE: the whole page inside an engraved frame ================= */
html.kme{--m:40px;background:#fff}
/* the master frame (Hunt: bas-relief acanthus on a cut-away ground, Parker's figures in the corners), the
   section's carved cartouche, and the light foliage ground: one fixed layer, never re-rastered on a turn */
html.kme body{background:transparent;padding:0 40px !important}
html.kme body:before{content:"";position:fixed;left:0;top:0;width:100%;height:100%;z-index:-1;pointer-events:none;will-change:transform;
  background-image:url(orn/motif-edition.svg),url(orn/frame.svg);background-repeat:no-repeat;
  background-position:center bottom,0 0;background-size:86px 26px,100% 100%}
html.kme body .krun,html.kme body .kbar,html.kme #kcont{background:none !important}
html.kme body .krun *,html.kme body .kbar *,html.kme #kcont *{background-color:transparent !important}
html.kme body .krun,html.kme body .kbar,html.kme #kcont{position:relative;z-index:1}
html.kme #kkf{position:absolute;left:0;top:0;width:0;height:0;z-index:0;pointer-events:none}
html.kme #kkf i{position:absolute;display:block;background:#fff}
/* the engraved fill: one SVG per sheet, cut at build time to every free rectangle round the labels; the pager
   shows it only when the sheet lays out as measured, else the light ground and the gap fleurons stay */
html.kme #kfill{display:block;position:fixed;left:0;top:0;width:618px;height:714px;z-index:-1;pointer-events:none;border:0}
/* a placed plate (solar/plate_slots.py): a fixed-size engraving in the flow, centred between panels */
html.kme #kmain .kslot{display:block;margin:10px auto;overflow:hidden}
html.kme #kmain .kslot img{display:block;border:0}
html.kme .ksecfront #kmain .kfhead.khasslot:after{display:none !important}
FRAMES
html.kme body[data-kfills]:not(.knofill):before{background-image:none !important}   /* the sheet's field covers frame and motif: fetched only where a sheet shows no field */
html.kme body .krun{margin:40px 0 28px !important;padding-left:14px !important;padding-right:14px !important;border-bottom-color:transparent !important}
html.kme.kpaged body .kbar{margin:28px 0 40px !important;padding:0 14px !important;border-top-color:transparent !important}
html.kme.kjumpopen #kjump{top:84px !important;bottom:96px !important;left:40px !important;right:40px !important}
/* no white unless behind text: #kko holds a white knock-out under each line of text, chart and picture */
html.kme #kview,html.kme #kclip{background:none !important}
html.kme #kmain{z-index:1}
html.kme #kko{position:absolute;left:0;top:0;width:100%;height:0;z-index:0;pointer-events:none}
html.kme #kko i{position:absolute;display:block;background:#fff}
html.kme #kko i.kl,html.kme #kkf i.kl{border:0;box-shadow:none !important;box-sizing:border-box}   /* the edge is the studio's inlay, drawn in the sheet's field */
html.kme .kcontents #kmain .kgl:before{width:64px !important;height:64px !important;background-size:64px 64px !important}
html.kme .kcontents #kmain .kgl:after{display:none}
html.kme .kcontents #kmain .kgl .kdeg small{letter-spacing:.05em !important}
html.kme #kmain .bars{padding-top:18px !important;box-sizing:content-box !important}
/* the cover's reading area opens to the frame (570 px) so the plate prints at its native width; text keeps 10 px */
html.kme body.kcontents{padding:0 40px !important}
html.kme .kcontents #kmain>*{margin-left:0 !important;margin-right:0 !important}
html.kme .kcontents #kmain>.kmast{margin-left:0 !important;margin-right:0 !important}
html.kme #kmain .kinl{background-color:#fff !important;-webkit-box-decoration-break:clone;box-decoration-break:clone;padding:0 4px}
/* the cover has no running head: its sheets start inside the frame too */
html.kme body.kcontents .kbar{margin-top:30px !important}
html.kme body.kcontents #kview{top:30px}
/* the tailpiece: fills what a short last sheet leaves empty, never adds a sheet */
#ktail{display:none}
#ktail2{display:none}
html.kme #ktail,html.kme #ktail2{position:absolute;left:0;right:0;z-index:2}
html.kme #ktail2{background:none;border:0;overflow:hidden;contain:strict;text-align:center}
html.kme #ktail2 img{display:block;margin:0 auto;border:0}
html.kme .kcontents #kmain .kgl .kink{outline:0 !important}
html.kme #kclip .kgap.kthin{left:25%;right:25%;background:url(orn/gap.svg) no-repeat 50% 50%/auto 14px}
#kclip .kgap{display:none}
html.kme #kclip .kgap{display:block;position:absolute;left:25%;right:25%;z-index:2;background:url(orn/gap.svg) no-repeat 50% 50%/auto 20px}
html.kme #kclip .kgap.kbig{left:20%;right:20%;background:url(orn/gap.svg) no-repeat 50% 50%/auto 24px}
html.kme #ktail.ksmall{background:var(--orn-fleuron) no-repeat center center/auto 26px,var(--orn-dotrule) repeat-x 0 50%/auto 8px}

/* long section fronts: the stories in two columns so the plate keeps its sheet */
html.kme .ksecfront #kmain .kfhead[data-n="6"]+.kfl,html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl,html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl{display:grid !important;grid-template-columns:1fr 1fr;grid-column-gap:18px}
html.kme .ksecfront #kmain .kfhead[data-n="6"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl .kt b{font-size:16px !important;line-height:20px !important}
html.kme .ksecfront #kmain .kfhead[data-n="6"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl small,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl small{display:none !important}
html.kme .ksecfront #kmain .kfhead[data-n="6"]+.kfl li:last-child a,html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl li:last-child a,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl li:last-child a,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl li:last-child a,html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl li:last-child a,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl li:last-child a,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl li:last-child a{background:var(--orn-minifleur) no-repeat 50% 100%/56px 12px,var(--orn-dotrule) repeat-x 0 calc(100% - 2px)/auto 8px !important}
html.kme .ksecfront #kmain .kfhead[data-n="6"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="7"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="8"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="9"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="10"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="11"]+.kfl .kt b,html.kme .ksecfront #kmain .kfhead[data-n="12"]+.kfl .kt b{display:block !important;white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis}
"""


DESIGN_CSS = css()


def wx_class(cond):
    """The cover's weather glyph, from the condition words ("Sauvie Island · Cloudy")."""
    c = (cond or "").lower()
    for k, words in (("storm", ("thunder", "storm")), ("snow", ("snow", "sleet", "flurr")),
                     ("rain", ("rain", "shower", "drizzle")), ("fog", ("fog", "mist", "haze", "smoke")),
                     ("part", ("partly", "mostly sunny", "few clouds", "scattered")),
                     ("sun", ("sunny", "clear", "fair")), ("cloud", ("cloud", "overcast"))):
        if any(w in c for w in words):
            return "kwx-" + k
    return "kwx-cloud"


def roman(n):
    out = ""
    for v, r in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
                 (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += r
            n -= v
    return out


FLASH_JS = r"""<script>/* page prep, before the pager lays out: a chart and its labels and axis are one unit; web chrome goes */
(function(){try{if(!/ kme /.test(' '+document.documentElement.className+' '))return;var m=document.getElementById('kmain');if(!m)return;
var bs=m.querySelectorAll('.bars');for(var i=0;i<bs.length;i++){var b=bs[i],w=document.createElement('div');w.className='kchart';
b.parentNode.insertBefore(w,b);w.appendChild(b);var nx=w.nextElementSibling;while(nx&&/\b(kbx|axis|legend)\b/.test(nx.className)){var n2=nx.nextElementSibling;w.appendChild(nx);nx=n2;}}
var ws=m.querySelectorAll('.kmast .kear>span:not(.kcrest),.kmast .kname,.kmast .kdate');
for(var q=0;q<ws.length;q++){var e=ws[q],sp=document.createElement('span');sp.className='kinl';while(e.firstChild)sp.appendChild(e.firstChild);e.appendChild(sp);e.className+=' knok';}
var as=m.querySelectorAll('a');for(var j=0;j<as.length;j++){var t=(as[j].textContent||'').trim();
if(/^(listen|watch|read more|tickets|buy|stream)( on| now| it)?\b/i.test(t)||/(\u2192|\u203a)$/.test(t)&&!as[j].closest('.kbar,.krun,.kfl,.ktoc,.kleads,.krail'))as[j].style.setProperty('display','none','important');}}catch(e){}})();</script>
<script>/* the chapter flash: one short full refresh (black, then the page) only where an inverse section
begins, so its black plate prints clean; every other page goes straight to the page */
(function(){try{var r=document.documentElement,b=document.body;if(!/ kme /.test(' '+r.className+' '))return;
var s=b.getAttribute('data-ksec')||(/kendpage/.test(b.className)?'end':'cover'),st=window.sessionStorage,last=null,inv=/^(nearby|music|end)$/.test(s);
try{last=st.getItem('kme:sec');st.setItem('kme:sec',s);}catch(e){}
if(!inv||last===s)return;var f=document.createElement('div');
f.style.cssText='position:fixed;left:0;top:0;width:100%;height:100%;background:#000;z-index:2147483647';b.appendChild(f);
setTimeout(function(){if(f.parentNode)b.removeChild(f);},120);}catch(e){}})();</script>"""
