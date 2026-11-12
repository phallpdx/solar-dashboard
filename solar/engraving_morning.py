"""The Morning Edition: a daily engraved cover plate, cut fresh every morning.

Banknote and bulino line engraving for a Kindle Paperwhite (Chrome 75, e-ink): only crisp black
strokes and white/black fills, tone made by hatching, every stroke >= .6 px, no transforms, no
<text>, coordinates baked and rounded to .1 px. Stdlib only.

    cover_plate(day, width=570, height=None) -> str  # one inline <svg>, native 570 x 324

E-ink rules (eink/eink-guide.md): strokes only .5/1/1.5 CSS, hatch pitches 1/1.5/2/3 on the device-pixel
grid (viewBox offset -.25 puts .5 px rules on whole device pixels; orthogonal hatch is crispEdges),
white-on-black lines >= 1 CSS, text only on white cartouches.
    crest(seed, size=64) -> str                      # the "P" monogram crest

`day` keys (all optional): date, sunrise, sunset, temp_f, sky, moon_phase, river_ft, tide, doy,
edition_no. The plate is seeded by random.Random(date.toordinal()), so a day always gives the same
plate, and it encodes the day:

  * the guilloche sun rosette behind Mt. Hood takes its lobe count, ray count and turn from the
    sunrise time, and sits left or right of the summit by the season's sunrise azimuth;
  * the Columbia's waterline (under a fixed St. Johns Bridge) rises and falls with river_ft;
  * the moon is drawn at its real phase; the snowline on Hood follows the month;
  * the sky (clear, cloudy, rain, fog) sets clouds, rain, mist or birds;
  * the edition number sits in the bottom cartouche, the date in Roman numerals in the top tablet.

Easter eggs (a few rotate in each morning by the date seed): the high temperature and edition
number as micro-digits in the rosette, Sauvie Island's coordinates in the frame's microline, and
some of: a kite, a toy boat, a helium balloon over the bridge, a vinyl record as the sun's core,
a pinwheel in a corner.

Style matches solar/kindle_evening.py's ornament cabinet (W0/W1/W2 line weights, Thai kanok
flames, guilloche bands), but everything here is computed geometry rather than pattern fills.
"""
import bisect
import datetime
import math
import random
import re

W0, W1, W2 = .5, 1, 1.5
PITCHES = (1, 1.5, 2, 3)   # e-ink hatch pitches (CSS px): whole device pixels at DPR 2


def _sw(w):
    """Snap a stroke width to the e-ink set: .5, 1, 1.5 CSS (1, 2, 3 device px), or whole px."""
    if w <= 0:
        return 0
    if w < .75:
        return .5
    if w < 1.25:
        return 1
    if w < 1.75:
        return 1.5
    return float(round(w))


def _pitch(sp):
    return min(PITCHES, key=lambda p: abs(p - sp))
TAU = math.tau

# ----------------------------------------------------------------------------------------------
# Path encoding: absolute start, then relative 1-decimal deltas with minimal separators.
# ----------------------------------------------------------------------------------------------


def _n(x):
    s = f"{x:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    if s in ("-0", "-0.0", "-.0"):
        s = "0"
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


def _cat(nums):
    out, prev = [], None
    for s in nums:
        if prev is not None and not (s[0] == "-" or (s[0] == "." and "." in prev)):
            out.append(" ")
        out.append(s)
        prev = s
    return "".join(out)


def _pd(pts, closed=False, start=None):
    """Polyline -> compact path data. With start=(x, y) the move is relative ("m") to that pen
    position; returns (d, end) in that case."""
    r = [(round(x, 1), round(y, 1)) for x, y in pts]
    if len(r) < 2:
        return ("", start) if start is not None else ""
    px, py = r[0]
    nums = []
    body = ""
    for x, y in r[1:]:
        dx, dy = round(x - px, 1), round(y - py, 1)
        if dx == 0 and dy == 0:
            continue
        nums.append((dx, dy))
        px, py = x, y
    if not nums:
        return ("", start) if start is not None else ""
    if len(nums) == 1 and nums[0][1] == 0:
        body = "h" + _n(nums[0][0])
    elif len(nums) == 1 and nums[0][0] == 0:
        body = "v" + _n(nums[0][1])
    else:
        body = "l" + _cat([v for dx, dy in nums for v in (_n(dx), _n(dy))])
    if start is None:
        head = "M" + _cat([_n(r[0][0]), _n(r[0][1])])
    else:
        head = "m" + _cat([_n(round(r[0][0] - start[0], 1)), _n(round(r[0][1] - start[1], 1))])
    d = head + body + ("z" if closed else "")
    if start is None:
        return d
    end = r[0] if closed else (px, py)
    return d, end


def _pds(polys, closed=False):
    out, pen = [], None
    for p in polys:
        if pen is None:
            d = _pd(p, closed)
            if d:
                out.append(d)
                r = [(round(x, 1), round(y, 1)) for x, y in p]
                pen = r[0] if closed else _endpt(r)
        else:
            d, pen2 = _pd(p, closed, pen)
            if d:
                out.append(d)
                pen = pen2
    return "".join(out)


def _endpt(r):
    # the pen after drawing r, recomputed the way _pd accumulates rounded deltas
    px, py = r[0]
    for x, y in r[1:]:
        px, py = round(px + round(x - px, 1), 1), round(py + round(y - py, 1), 1)
    return px, py


def _wstr(w):
    w = _sw(w)
    return "" if w in (0, W0) else f' stroke-width="{_n(w)}"'




def _path(d, w=W0, fill=None, extra=""):
    if not d:
        return ""
    f = f' fill="{fill}"' if fill else ""
    # paths made only of horizontal/vertical runs are hatch: lay them on the device-pixel grid
    crisp = ' shape-rendering="crispEdges"' if (not fill and re.fullmatch(r"(?:[Mm][-\d. ]+[hv][-\d.]+)+", d)) else ""
    return f'<path d="{d}"{_wstr(w)}{f}{crisp}{extra}/>'


def _circle(cx, cy, r, w=W0, fill=None, extra=""):
    f = f' fill="{fill}"' if fill else ""
    sw = _wstr(w)
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}"{sw}{f}{extra}/>'


def _ellipse(cx, cy, rx, ry, w=W0, fill=None, extra=""):
    f = f' fill="{fill}"' if fill else ""
    return f'<ellipse cx="{_n(cx)}" cy="{_n(cy)}" rx="{_n(rx)}" ry="{_n(ry)}"{_wstr(w)}{f}{extra}/>'


# ----------------------------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------------------------


def _spline(pts, closed=False, n=6):
    """Catmull-Rom through pts."""
    m = len(pts)
    if m < 3:
        return list(pts)
    out = []
    for i in range(m if closed else m - 1):
        p0 = pts[i - 1] if (closed or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if (closed or i + 2 < m) else p2
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def _chunks(chs, n=5):
    """Smooth chunks joined at sharp corners."""
    out = []
    for c in chs:
        s = _spline(c, False, n) if len(c) > 2 else list(c)
        out += s if not out else s[1:]
    return out


def _inside(poly, x, y):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def _runs(p0, p1, pred, step=1.0, minlen=.8):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(L / step))
    segs, start, last = [], None, None
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if y0 == y1:
            y = y0
        if x0 == x1:
            x = x0
        if pred(x, y):
            if start is None:
                start = (x, y)
            last = (x, y)
        elif start is not None:
            if math.hypot(last[0] - start[0], last[1] - start[1]) >= minlen:
                segs.append([start, last])
            start = None
    if start is not None and math.hypot(last[0] - start[0], last[1] - start[1]) >= minlen:
        segs.append([start, last])
    return segs


def _split(pts, pred, minpts=2):
    """Break a polyline where pred fails."""
    out, cur = [], []
    for p in pts:
        if pred(*p):
            cur.append(p)
        else:
            if len(cur) >= minpts:
                out.append(cur)
            cur = []
    if len(cur) >= minpts:
        out.append(cur)
    return out


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _hatch(poly, ang, sp, pred=None, step=.6, phase=0.0, minlen=.8):
    """Parallel lines at angle `ang` (deg) and spacing `sp` filling poly (and pred)."""
    x0, y0, x1, y1 = _bbox(poly)
    sp = _pitch(sp)
    ok = (lambda x, y: pred(x, y) and _inside(poly, x, y)) if pred else (lambda x, y: _inside(poly, x, y))
    if ang % 90 == 0:
        # orthogonal hatch sits on the grid: lines at whole multiples of the pitch
        segs = []
        if ang % 180 == 0:
            y = math.ceil(y0 / sp) * sp
            while y <= y1:
                segs += _runs((x0 - 1, y), (x1 + 1, y), ok, step, minlen)
                y += sp
        else:
            x = math.ceil(x0 / sp) * sp
            while x <= x1:
                segs += _runs((x, y0 - 1), (x, y1 + 1), ok, step, minlen)
                x += sp
        return segs
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + 1
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    segs = []
    k = -R + (phase % sp)
    while k <= R:
        bx, by = cx + nx * k, cy + ny * k
        segs += _runs((bx - dx * R, by - dy * R), (bx + dx * R, by + dy * R), ok, step, minlen)
        k += sp
    return segs


def _map(pts, ox, oy, s=1.0, mirror=False, rot=0.0):
    c, si = math.cos(rot), math.sin(rot)
    out = []
    for x, y in pts:
        x, y = x * s, y * s
        x, y = x * c - y * si, x * si + y * c
        out.append((ox - x if mirror else ox + x, oy + y))
    return out


def _ell_pts(cx, cy, rx, ry, n=40, a0=0.0, a1=TAU, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


# ----------------------------------------------------------------------------------------------
# Engraved stroke type: digits, Roman capitals, a few letters, on a 5 x 8 grid
# ----------------------------------------------------------------------------------------------


def _oval(cx, cy, rx, ry, n=14):
    return [(cx + rx * math.cos(TAU * i / n - math.pi / 2), cy + ry * math.sin(TAU * i / n - math.pi / 2)) for i in range(n + 1)]


_G = {
    "0": (5, [("p", _oval(2.5, 4, 2.2, 3.9, 18))]),
    "1": (5, [("l", [(1.2, 1.6), (2.8, 0), (2.8, 8)]), ("l", [(1.3, 8), (4.3, 8)])]),
    "2": (5, [("s", [(.5, 1.9), (1.4, .4), (2.7, 0), (4.1, .6), (4.5, 2), (3.8, 3.7), (2, 5.5), (.4, 8)]),
              ("l", [(.4, 8), (4.7, 8), (4.8, 7)])]),
    "3": (5, [("s", [(.5, 1.2), (2.2, 0), (4, .6), (4.2, 2.2), (3, 3.6), (1.8, 3.8)]),
              ("s", [(1.8, 3.8), (3.6, 4.2), (4.6, 5.8), (3.8, 7.6), (2.2, 8), (.3, 7)])]),
    "4": (5, [("l", [(3.6, 8), (3.6, 0), (.2, 5.6), (4.9, 5.6)]), ("l", [(2.6, 8), (4.6, 8)])]),
    "5": (5, [("l", [(4.4, 0), (1.1, 0), (.7, 3.7)]),
              ("s", [(.7, 3.7), (2.4, 3.1), (4.2, 3.9), (4.7, 5.7), (3.8, 7.5), (2.2, 8), (.3, 7.2)])]),
    "6": (5, [("s", [(4.2, .6), (2.8, 0), (1.2, .8), (.3, 3.5), (.4, 6.2), (1.5, 7.8), (3.1, 7.9), (4.4, 6.6),
                     (4.4, 5), (3.4, 3.7), (2, 3.6), (.6, 4.6)])]),
    "7": (5, [("l", [(.3, 1), (.4, 0), (4.7, 0), (3.2, 3.4), (2.1, 8)])]),
    "8": (5, [("s", [(2.5, 3.8), (.9, 3), (.7, 1.4), (1.7, .1), (3.3, .1), (4.3, 1.4), (4.1, 3), (2.5, 3.8),
                     (.6, 5), (.5, 6.8), (1.6, 7.9), (3.4, 7.9), (4.5, 6.8), (4.4, 5), (2.5, 3.8)])]),
    ":": (3, [("l", [(1.5, 2.4), (1.5, 2.9)]), ("l", [(1.5, 7.1), (1.5, 7.6)])]),
    ".": (2.4, [("l", [(1.1, 7.5), (1.1, 8)])]),
    "·": (3, [("l", [(1.5, 3.8), (1.5, 4.3)])]),
    " ": (3, []),
    "°": (3.4, [("p", _oval(1.6, 1.3, 1.1, 1.2, 10))]),
    "N": (5.4, [("l", [(.7, 8), (.7, 0), (4.7, 8), (4.7, 0)]), ("l", [(-.2, 8), (1.6, 8)]), ("l", [(3.8, 0), (5.6, 0)]),
                ("l", [(-.2, 0), (.9, 0)])]),
    "W": (7, [("l", [(0, 0), (1.7, 8), (3.5, 1.6), (5.3, 8), (7, 0)])]),
    "F": (4.6, [("l", [(.8, 8), (.8, 0), (4.4, 0), (4.4, 1)]), ("l", [(.8, 3.8), (3.2, 3.8)]), ("l", [(0, 8), (1.8, 8)])]),
    "o": (4.6, [("p", _oval(2.3, 2.3, 1.4, 1.8, 12)), ("l", [(.8, 5.4), (3.8, 5.4)])]),
    "I": (3, [("l", [(1.5, 0), (1.5, 8)]), ("l", [(.4, 0), (2.6, 0)]), ("l", [(.4, 8), (2.6, 8)])]),
    "V": (5.4, [("l", [(.5, 0), (2.7, 8), (4.9, 0)]), ("l", [(-.4, 0), (1.4, 0)]), ("l", [(4, 0), (5.8, 0)])]),
    "X": (5.4, [("l", [(.4, 0), (5, 8)]), ("l", [(5, 0), (.4, 8)]), ("l", [(-.4, 0), (1.3, 0)]), ("l", [(4, 0), (5.8, 0)]),
                ("l", [(-.4, 8), (1.3, 8)]), ("l", [(4, 8), (5.8, 8)])]),
    "L": (5, [("l", [(1, 0), (1, 8), (4.6, 8), (4.7, 6.8)]), ("l", [(0, 0), (2.1, 0)])]),
    "C": (5, [("s", [(4.5, 1.2), (3, 0), (1.2, .6), (.3, 4), (1.2, 7.4), (3, 8), (4.6, 6.8)])]),
    "D": (5.4, [("l", [(0, 0), (1, 0), (1, 8), (0, 8)]), ("s", [(1, 0), (3.4, .6), (4.8, 4), (3.4, 7.4), (1, 8)])]),
    "M": (6.6, [("l", [(.6, 8), (.9, 0), (3.3, 6.4), (5.7, 0), (6, 8)]), ("l", [(-.3, 8), (1.5, 8)]), ("l", [(5.1, 8), (6.9, 8)])]),
}
_G.update({
    "P": (5, [("l", [(0, 8), (2, 8)]), ("l", [(1, 8), (1, 0), (0, 0)]),
              ("s", [(1, 0), (3.3, 0), (4.6, 1.1), (4.6, 2.9), (3.3, 4.1), (1, 4.1)])]),
    "O": (5.4, [("p", _oval(2.7, 4, 2.5, 4, 20))]),
    "R": (5.4, [("l", [(0, 8), (2, 8)]), ("l", [(1, 8), (1, 0), (0, 0)]),
                ("s", [(1, 0), (3.3, 0), (4.6, 1.1), (4.6, 2.9), (3.3, 4.1), (1, 4.1)]), ("l", [(2.8, 4.1), (4.6, 8), (5.4, 8)])]),
    "T": (5.2, [("l", [(0, 1), (0, 0), (5.2, 0), (5.2, 1)]), ("l", [(2.6, 0), (2.6, 8)]), ("l", [(1.5, 8), (3.7, 8)])]),
    "A": (5.6, [("l", [(0, 8), (2.8, 0), (5.6, 8)]), ("l", [(1.1, 5), (4.5, 5)]), ("l", [(-.6, 8), (1, 8)]), ("l", [(4.6, 8), (6.2, 8)])]),
    "E": (5, [("l", [(4.6, 1), (4.6, 0), (.9, 0), (.9, 8), (4.7, 8), (4.7, 6.8)]), ("l", [(.9, 4), (3.4, 4)]),
              ("l", [(0, 0), (.9, 0)]), ("l", [(0, 8), (.9, 8)])]),
    "H": (5.6, [("l", [(.9, 0), (.9, 8)]), ("l", [(4.7, 0), (4.7, 8)]), ("l", [(.9, 4), (4.7, 4)]),
                ("l", [(0, 0), (1.8, 0)]), ("l", [(3.8, 0), (5.6, 0)]), ("l", [(0, 8), (1.8, 8)]), ("l", [(3.8, 8), (5.6, 8)])]),
    "G": (5.2, [("s", [(4.6, 1.2), (3, 0), (1.2, .6), (.3, 4), (1.2, 7.4), (3, 8), (4.7, 7)]), ("l", [(4.7, 7), (4.7, 4.6), (3, 4.6)])]),
})
_G["9"] = (5, [(k, [(5 - x, 8 - y) for x, y in p]) for k, p in _G["6"][1]])


def _glyph_polys(ch):
    adv, strokes = _G.get(ch, _G[" "])
    out = []
    for kind, pts in strokes:
        out.append(_spline(pts, False, 4) if kind == "s" else list(pts))
    return adv, out


def _text_polys(s, x, y, h, track=1.2, center=True):
    """Glyph polylines with top-left at (x, y) (or centered on x), cap height h."""
    k = h / 8
    width = sum(_G.get(c, _G[" "])[0] + track for c in s) - track
    cx = x - width * k / 2 if center else x
    out = []
    for c in s:
        adv, polys = _glyph_polys(c)
        out += [[(cx + px * k, y + py * k) for px, py in p] for p in polys]
        cx += (adv + track) * k
    return out, width * k


def _text_on_circle(s, cx, cy, r, a_mid, h, track=1.4):
    """Micro-digits set around an arc, centered on angle a_mid (radians), tops facing outward."""
    k = h / 8
    width = (sum(_G.get(c, _G[" "])[0] + track for c in s) - track) * k
    a = a_mid - width / 2 / r
    out = []
    for c in s:
        adv, polys = _glyph_polys(c)
        for p in polys:
            q = []
            for px, py in p:
                ang = a + px * k / r
                rr = r + (8 - py) * k - h / 2
                q.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
            out.append(q)
        a += (adv + track) * k / r
    return out


_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
          (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _roman(n):
    out = ""
    for v, s in _ROMAN:
        while n >= v:
            out += s
            n -= v
    return out


# ----------------------------------------------------------------------------------------------
# Day data
# ----------------------------------------------------------------------------------------------


def _minutes(s, default):
    if not s:
        return default
    m = re.search(r"(\d{1,2}):(\d{2})\s*([ap])?", str(s).lower())
    if not m:
        return default
    h, mi = int(m.group(1)) % 12, int(m.group(2))
    if m.group(3) == "p":
        h += 12
    elif m.group(3) is None and int(m.group(1)) >= 12:
        h = int(m.group(1))
    return h * 60 + mi


def _moon_phase(d):
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    days = (datetime.datetime(d.year, d.month, d.day, 12) - ref).total_seconds() / 86400
    return (days / 29.530588853) % 1


def _num(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ----------------------------------------------------------------------------------------------
# Ornament pieces (all return (svg_string))
# ----------------------------------------------------------------------------------------------


def _rosette_curve(kind, cx, cy, lobes, R, amp, rot=0.0, step=1.4, extra=0):
    """Engine-turned curves. kind: 'hypo' star, 'epi' looped band, 'wave' woven sine ring."""
    pts = []
    if kind == "wave":
        n = int(TAU * R / step) + 1
        for i in range(n + 1):
            t = TAU * i / n
            r = R + amp * math.sin(lobes * t + rot)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        return pts
    if kind == "epi":
        # base circle R, epicycle radius amp turning (lobes+1) times: a chain of loops
        n = int(max(TAU * R / step, lobes * 15)) + 1
        for i in range(n + 1):
            t = TAU * i / n
            x = R * math.cos(t + rot) - amp * math.cos((lobes + 1) * t + rot)
            y = R * math.sin(t + rot) - amp * math.sin((lobes + 1) * t + rot)
            pts.append((cx + x, cy + y))
        return pts
    # hypotrochoid: k = lobes cusps; R outer, rolling r = R/k, pen d
    k = lobes
    r = R / k
    d = amp
    n = int(max(TAU * R / step, k * 13)) + 1
    for i in range(n + 1):
        t = TAU * i / n
        x = (R - r) * math.cos(t) + d * math.cos((R - r) / r * t)
        y = (R - r) * math.sin(t) - d * math.sin((R - r) / r * t)
        c, s = math.cos(rot), math.sin(rot)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


def _small_rosette(cx, cy, r, lobes, rot):
    """A corner rosette: white disc, rim, dotted ring, hypotrochoid and woven ring."""
    out = _circle(cx, cy, r, W1, "#fff")
    out += _circle(cx, cy, r - 1.6, 1.3, extra=' stroke-dasharray="0 2.2"')
    polys = [_rosette_curve("hypo", cx, cy, lobes, r * .52, r * .2, rot, 1.2)]
    polys += [_rosette_curve("wave", cx, cy, lobes, r * .66, r * .1, rot + ph, 1.3) for ph in (0, math.pi)]
    out += _path(_pds(polys), W0)
    out += _circle(cx, cy, 1.2, W0, "#000")
    return out


def _kanok_pts(L, flip=False):
    """Thai kanok flame in local coords: base at origin, pointing +x, licks on the -y side."""
    chs = [
        [(0, 0), (.04, -.2), (.2, -.36), (.42, -.47)],
        [(.42, -.47), (.38, -.26)],
        [(.38, -.26), (.52, -.33), (.72, -.42)],
        [(.72, -.42), (.66, -.2)],
        [(.66, -.2), (.84, -.2), (.95, -.24), (1.02, -.36)],
        [(1.02, -.36), (.96, -.12), (.72, .05), (.4, .1), (.15, .08), (0, 0)],
    ]
    s = -1 if flip else 1
    outline = [(x * L, y * L * s) for x, y in _chunks(chs, 4 if L > 13 else 3)]
    vein = [(x * L, y * L * s) for x, y in _spline([(.06, 0), (.4, -.07), (.7, -.1), (.93, -.24)], False, 5)]
    low = [(x * L, y * L * s) for x, y in _spline([(.08, .05), (.4, .08), (.7, .04), (.92, -.1)], False, 5)]
    shade = []
    for i in range(1, 9):
        t = i / 10
        a = vein[int(t * (len(vein) - 1))]
        b = low[int(t * (len(low) - 1))]
        shade.append([a, (a[0] + (b[0] - a[0]) * .8, a[1] + (b[1] - a[1]) * .8)])
    return outline, vein, shade


def _kanok(x, y, L, ang, flip=False, mirror_x=None):
    """A kanok flame at (x, y) pointing at angle ang (radians)."""
    o, v, sh = _kanok_pts(L, flip)
    c, s = math.cos(ang), math.sin(ang)

    def m(p):
        q = [(x + a * c - b * s, y + a * s + b * c) for a, b in p]
        return [(2 * mirror_x - a, b) for a, b in q] if mirror_x is not None else q
    return (_path(_pd(m(o), True), .7, "#fff") + _path(_pd(m(v)) + _pds([m(z) for z in sh]), W0))


def _volute(cx, cy, R, a0, turns, band, cw=True):
    """A spiral scroll band from outer angle a0 inward; returns (polygon, centerline)."""
    n = int(turns * 48)
    center, left, right = [], [], []
    sgn = 1 if cw else -1
    for i in range(n + 1):
        t = i / n
        a = a0 + sgn * TAU * turns * t
        r = R * (1 - .78 * t)
        w = band * (1 - .7 * t) / 2
        ca, sa = math.cos(a), math.sin(a)
        center.append((cx + r * ca, cy + r * sa))
        left.append((cx + (r + w) * ca, cy + (r + w) * sa))
        right.append((cx + (r - w) * ca, cy + (r - w) * sa))
    return left + right[::-1], center


# ---- vignettes ------------------------------------------------------------------------------


def _drum_kit(ox, oy, s=1.0):
    """A small drum kit, floor at (ox, oy)."""
    out = []
    P = lambda pts: [(ox + x * s, oy + y * s) for x, y in pts]

    def shell(cx, top, rx, ry, h):
        body = P([(cx - rx, top), (cx - rx, top + h)] + [(cx - rx * math.cos(math.pi * i / 12), top + h + ry * math.sin(math.pi * i / 12)) for i in range(13)] + [(cx + rx, top)])
        rim = _ell_pts(ox + cx * s, oy + top * s, rx * s, ry * s, 20)
        x0 = ox + (cx - rx) * s
        x1 = ox + (cx + rx) * s
        hatch = []
        for i in range(1, 9):
            u = -math.cos(math.pi * i / 9)
            if abs(u) < .45:
                continue
            xx = (x0 + x1) / 2 + u * (x1 - x0) / 2
            yy = (1 - u * u) ** .5
            hatch.append([(xx, oy + (top + ry * yy * .9) * s), (xx, oy + (top + h + ry * yy * .9) * s)])
        hatch += [[(x0 + (x1 - x0) * .08, oy + (top + h * .5) * s), (x1 - (x1 - x0) * .08, oy + (top + h * .5) * s)]]
        return (_path(_pd(body, True), .8, "#fff") + _path(_pds(hatch), W0) + _path(_pd(rim, True), .8, "#fff"))
    # cymbal stands first
    out.append(_path(_pds([P([(-25, 0), (-24, -27)]), P([(-28, 0), (-24, -9), (-21, 0)]),
                           P([(24, 0), (21, -32)]), P([(20, 0), (23.3, -10), (27, 0)])]), .7))
    # bass drum front head
    out.append(_circle(ox, oy - 10.5 * s, 10.5 * s, 1, "#fff"))
    out.append(_circle(ox, oy - 10.5 * s, 8.6 * s, W0))
    rods = []
    for i in range(10):
        a = TAU * i / 10
        rods.append([(ox + 8.6 * s * math.cos(a), oy - 10.5 * s + 8.6 * s * math.sin(a)),
                     (ox + 10.5 * s * math.cos(a), oy - 10.5 * s + 10.5 * s * math.sin(a))])
    out.append(_path(_pds(rods), W0))
    # a little star on the head, and the bass-drum feet
    star = [(ox + (3.2 if i % 2 == 0 else 1.3) * s * math.cos(-math.pi / 2 + i * math.pi / 5),
             oy - 10.5 * s + (3.2 if i % 2 == 0 else 1.3) * s * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    out.append(_path(_pd(star, True), W0, "#000"))
    out.append(_path(_pds([P([(-8, -3), (-12, 0)]), P([(8, -3), (12, 0)])]), .8))
    # rack toms, snare, floor tom
    out.append(shell(-5.5, -25, 4.6, 1.6, 4.8))
    out.append(shell(5.5, -25, 4.6, 1.6, 4.8))
    out.append(_path(_pds([P([(-17, -10), (-17, 0)]), P([(-20, 0), (-17, -5), (-14, 0)]), P([(17, -8), (17, 0)]),
                           P([(20.5, -7), (20.5, 0)])]), .7))
    out.append(shell(-17, -14.5, 6.2, 1.9, 3.6))
    out.append(shell(17.5, -15, 6.4, 2, 8.5))
    # cymbals: hi-hat pair and ride
    for cx, cy, rx, ry, rot in ((-24.5, -27.5, 6.5, 1.3, 0), (-24.5, -26.2, 6.5, 1.1, 0), (20.5, -32.5, 9, 2.2, -.12)):
        e = _ell_pts(ox + cx * s, oy + cy * s, rx * s, ry * s, 24, rot=rot)
        out.append(_path(_pd(e, True), .8, "#fff"))
        out.append(_path(_pds([_ell_pts(ox + cx * s, oy + cy * s, rx * s * .55, ry * s * .5, 16, rot=rot)]), W0))
    # crossed sticks on the snare
    out.append(_path(_pds([P([(-23, -21), (-10, -15.2)]), P([(-21, -14), (-8, -19)])]), 1))
    return "".join(out)


def _dog(ox, oy, s=1.0, mirror=False):
    """A sitting dog in profile (facing right), floor at (ox, oy)."""
    body = _spline([(0, 0), (-3, -6), (-2, -13), (3, -19), (9, -23), (11.5, -27), (13.5, -31.5), (17, -32.6),
                    (20.5, -31.2), (24.5, -29.3), (25, -27.7), (21.8, -26.4), (18.6, -24.8), (19, -18), (20, -9), (20.2, -2),
                    (22.6, -.6), (22.4, 0), (16.6, 0), (16.3, -6), (15, -10), (12, -6.5), (11, -2.8), (13.2, -.4),
                    (13, 0)], True, 4)
    body = _map(body, ox, oy, s, mirror)
    ear = _map(_spline([(14.2, -31.2), (12.4, -29), (12, -25.2), (13.6, -24.2), (15.4, -27), (16.4, -30.6)], False, 4),
               ox, oy, s, mirror)
    tail = _map(_spline([(-1.5, -2), (-6, -1.5), (-10, -3.4), (-12.5, -6.5)], False, 4), ox, oy, s, mirror)
    tail2 = _map(_spline([(-1, -.4), (-6, .2), (-10.4, -1.6), (-12.5, -6.5)], False, 4), ox, oy, s, mirror)
    out = [_path(_pd(tail + tail2[::-1], True), .7, "#fff")]
    out.append(_path(_pd(body, True), .9, "#fff"))
    # contour hatching over the back and haunch (bulino curves), leaving chest and muzzle white
    shade = []
    for i in range(9):
        c = _spline([(-3 + i * .9, -1), (-1.5 + i * 1.6, -9), (2 + i * 1.9, -15), (6 + i * 1.6, -19.5)], False, 4)
        shade.append(_map(c, ox, oy, s, mirror))
    sh = []
    for c in shade:
        sh += _split(c, lambda x, y: _inside(body, x, y))
    out.append(_path(_pds(sh), W0))
    out.append(_path(_pd(ear, True), .7, "#000"))
    eye = _map([(19.2, -30.2)], ox, oy, s, mirror)[0]
    nose = _map([(24.2, -29)], ox, oy, s, mirror)[0]
    out.append(_circle(eye[0], eye[1], .7 * s, W0, "#000"))
    out.append(_circle(nose[0], nose[1], .8 * s, W0, "#000"))
    collar = _map([(11, -25), (13.2, -22.4), (17.6, -23.6), (19, -24.4)], ox, oy, s, mirror)
    tag = _map([(15.6, -21.6)], ox, oy, s, mirror)[0]
    out.append(_path(_pd(collar), 1.1))
    out.append(_circle(tag[0], tag[1], .9 * s, W0, "#fff"))
    return "".join(out)


def _heron(ox, oy, s=1.0, mirror=False):
    """A great blue heron standing in the shallows, facing left, feet at (ox, oy)."""
    body = _chunks([
        [(-20, -40.2), (-15, -40.6), (-11.8, -41.6)],
        [(-11.8, -41.6), (-9, -42.4), (-7.4, -41.4)],
        [(-7.4, -41.4), (-3.4, -43.6), (-.6, -43.6)],          # crest plume
        [(-.6, -43.6), (-5, -42.2), (-6.6, -40.2), (-6.4, -37.6), (-4.6, -34.2), (-3.4, -30.6), (-1.2, -28.2),
         (4, -27.6), (10, -24.6), (16, -18.6)],
        [(16, -18.6), (8, -16.2), (2, -14.8), (-3.4, -16.2), (-6.4, -20.2), (-7.2, -24.6), (-8.6, -29.6),
         (-9.8, -34.4), (-9.6, -38.4), (-11.6, -39.6), (-20, -40.2)]], 4)
    body = _map(body, ox, oy, s, mirror)
    legs = [_map([(0, -14.8), (.6, -7), (-.5, 0)], ox, oy, s, mirror), _map([(2.6, -15), (3.6, -7), (4.4, 0)], ox, oy, s, mirror),
            _map([(-.5, 0), (-3.6, .6)], ox, oy, s, mirror), _map([(4.4, 0), (7, .4)], ox, oy, s, mirror)]
    out = [_path(_pds(legs), .8)]
    out.append(_path(_pd(body, True), .8, "#fff"))
    wing = _map(_spline([(-5.6, -22), (-1, -27), (6, -25.6), (13.6, -19), (6, -17), (-1.6, -16.6), (-5.6, -22)], True, 4),
                ox, oy, s, mirror)
    out.append(_path(_pd(wing, True), W0))
    out.append(_path(_pds(_hatch(wing, -28 if not mirror else 208, 1.4, step=.5)), W0))
    # neck streaks and eye
    streak = [_map([(-8.6 + i * .3, -36 + i * 2.4), (-8 + i * .3, -35 + i * 2.4)], ox, oy, s, mirror) for i in range(5)]
    out.append(_path(_pds(streak), W0))
    eye = _map([(-9.4, -40.8)], ox, oy, s, mirror)[0]
    out.append(_circle(eye[0], eye[1], .5, W0, "#000"))
    # ripples around the legs
    rip = [_ell_pts(ox + 1.8 * s * (-1 if mirror else 1), oy + .6, 7 * s, 1.2 * s, 18, 0, math.pi),
           _ell_pts(ox + 1.8 * s * (-1 if mirror else 1), oy + .8, 11 * s, 1.8 * s, 18, .3, math.pi - .3)]
    out.append(_path(_pds(rip), W0))
    return "".join(out)


def _sternwheeler(ox, oy, s=1.0, mirror=False):
    """A small sternwheeler, waterline center at (ox, oy), bow to the right (unless mirrored)."""
    M = lambda pts: _map(pts, ox, oy, s, mirror)
    out = []
    # smoke from the stacks, trailing aft
    puffs = [(9.6, -27, 2.2), (6.6, -29.6, 2.8), (2.6, -31.2, 3.2), (-2.4, -32.4, 3.4), (-8, -33.2, 3.1), (-13.4, -33.6, 2.6),
             (-18, -34, 2)]
    for px, py, pr in puffs[::-1]:
        c = M([(px, py)])[0]
        out.append(_circle(c[0], c[1], pr * s, W0, "#fff"))
        arc = _ell_pts(c[0], c[1], pr * s * .6, pr * s * .6, 8, .2, 1.8)
        out.append(_path(_pd(arc), W0))
    hull = M([(-21, 0), (21, 0), (25.5, -4.4), (-23.5, -4.4)])
    out.append(_path(_pd(hull, True), .9, "#fff"))
    out.append(_path(_pds(_hatch(hull, 0, 1.1, step=.5)), W0))
    cab1 = M([(-18, -4.4), (15, -4.4), (15, -8.6), (-18, -8.6)])
    cab2 = M([(-13, -8.6), (9, -8.6), (9, -12.6), (-13, -12.6)])
    pilot = M([(-1.5, -12.6), (4.5, -12.6), (4.5, -16), (-1.5, -16)])
    for c in (cab1, cab2, pilot):
        out.append(_path(_pd(c, True), .8, "#fff"))
    ticks = [M([(x, -5.4), (x, -7.6)]) for x in [-16 + 2.2 * i for i in range(14)]]
    ticks += [M([(x, -9.6), (x, -11.6)]) for x in [-11 + 2.4 * i for i in range(9)]]
    ticks += [M([(-19, -8.6), (16, -8.6)]), M([(-14, -12.6), (10, -12.6)]), M([(-2.4, -16), (5.4, -16)])]
    out.append(_path(_pds(ticks), W0))
    for sx in (10.4, 13.2):
        st = M([(sx - .9, -12.6), (sx + .9, -12.6), (sx + .9, -24.4), (sx + 1.6, -25.6), (sx - 1.6, -25.6), (sx - .9, -24.4)])
        out.append(_path(_pd(st, True), .7, "#000"))
    flag = M([(-1, -16), (-1, -21), (-4.6, -19.8), (-1, -18.8)])
    out.append(_path(_pd(flag), .7))
    # stern paddlewheel
    c = M([(-26.6, -5.6)])[0]
    out.append(_circle(c[0], c[1], 6 * s, .9, "#fff"))
    sp = []
    for i in range(10):
        a = TAU * i / 10 + .2
        sp.append([(c[0] + 1.2 * s * math.cos(a), c[1] + 1.2 * s * math.sin(a)), (c[0] + 6 * s * math.cos(a), c[1] + 6 * s * math.sin(a))])
    out.append(_path(_pds(sp), W0))
    out.append(_circle(c[0], c[1], 4.2 * s, W0))
    # wake and the hull's reflection
    wk = [M([(-33 - 4 * i, 1.4 + i * 1.3), (-24 - 4 * i, 1.4 + i * 1.3)]) for i in range(3)]
    wk += [M([(25, .4), (35, 3.6)]), M([(22, 1.4), (30, 5.4)])]
    wk += [M([(-20 + 3 * j, 1.6 + i * 1.3), (-17.8 + 3 * j, 1.6 + i * 1.3)]) for i in range(3) for j in range(14) if (i + j) % 2 == 0]
    out.append(_path(_pds(wk), W0))
    return "".join(out)


def _fir(x, base, h, rng):
    """A Douglas fir in bulino strokes: a white silhouette with drooping branch strokes."""
    tiers = max(7, int(h / 5.5))
    w = h * .23
    left, right = [], []
    for i in range(tiers + 1):
        t = i / tiers
        y = base - h + h * .94 * t
        ww = w * (t ** .85) * (1 + rng.uniform(-.15, .15))
        right += [(x + ww * .45, y - h * .012), (x + ww, y + h * .03)]
        left += [(x - ww * .45, y - h * .012), (x - ww, y + h * .03)]
    sil = [(x, base - h - 2)] + right + [(x + 1.2, base - h * .04), (x + 1.2, base), (x - 1.2, base), (x - 1.2, base - h * .04)] + left[::-1]
    out = [_path(_pd(sil, True), .7, "#fff")]
    strokes = []
    for i in range(1, tiers + 1):
        t = i / tiers
        y = base - h + h * .94 * t
        ww = w * (t ** .85)
        n = 1 + int(ww / 3)
        for j in range(n):
            u = (j + .5) / n
            # right (shadow) side gets more strokes than the left
            yy = y - 3.2 * (1 - u) * (h / 70) - .5
            strokes.append([(x + .4, yy - 1.2), (x + ww * u, yy + ww * u * .45)])
            if j % 2 == 0 and ww > 3:
                strokes.append([(x - .4, yy - 1.2), (x - ww * u * .9, yy + ww * u * .4)])
    strokes.append([(x, base - h - 1.5), (x, base)])
    out.append(_path(_pds(strokes), W0))
    return "".join(out)


def _pinwheel(cx, cy, r):
    """A five-and-five pinwheel of swooshes (a nod to the home team), in a small roundel."""
    out = _circle(cx, cy, r, .9, "#fff")
    arms = []
    for i in range(5):
        a = TAU * i / 5 - math.pi / 2
        for k, sgn in ((0, 1), (1, -1)):
            off = .1 if k == 0 else -.1
            pts = []
            for j in range(9):
                t = j / 8
                rr = r * (.15 + .7 * t)
                aa = a + sgn * (.15 + .9 * t * t) + off
                pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
            arms.append(pts)
    out += _path(_pds(arms), .8)
    return out


def _kite(x, y, rng):
    """A diamond kite with a bowed tail and string."""
    k = [(x, y - 7), (x + 4.4, y - 1), (x, y + 6), (x - 4.4, y - 1)]
    out = _path(_pd(k, True), .8, "#fff")
    out += _path(_pds([[(x, y - 7), (x, y + 6)], [(x - 4.4, y - 1), (x + 4.4, y - 1)]]), W0)
    out += _path(_pds(_hatch([(x, y - 7), (x + 4.4, y - 1), (x, y - 1)], 90, 1.1, step=.4)), W0)
    tail = [(x + 2 * math.sin(i * .9) + i * .3, y + 6 + i * 1.6) for i in range(12)]
    out += _path(_pd(tail), W0)
    bows = [[(px - 1.4, py - .8), (px + 1.4, py + .8)] for px, py in tail[3::3]]
    out += _path(_pds(bows), 1.1)
    string = _spline([(x + .4, y + 2), (x + 14, y + 22), (x + 30, y + 46)], False, 6)
    out += _path(_pd(string), W0, extra=' stroke-dasharray="2 1.4"')
    return out


def _balloon(x, y):
    b = _spline([(x, y - 7), (x + 5, y - 4), (x + 4.4, y + 2), (x + .8, y + 6), (x, y + 6.4), (x - .8, y + 6),
                 (x - 4.4, y + 2), (x - 5, y - 4)], True, 5)
    out = _path(_pd(b, True), .8, "#fff")
    shade = _hatch(b, 70, 1.3, pred=lambda px, py: (px - x + 2) ** 2 + (py - y + 3) ** 2 > 16, step=.4)
    out += _path(_pds(shade), W0)
    out += _path(_pd([(x - .9, y + 7.6), (x + .9, y + 7.6), (x, y + 6.2)], True), W0, "#000")
    string = [(x + math.sin(i * .7) * 1.4, y + 7.6 + i * 2) for i in range(10)]
    return out + _path(_pd(string), W0)


def _toy_boat(x, y):
    """A toddler's paper/toy boat: hull, mast, triangle sail, flag."""
    hull = [(x - 6, y - 2.6), (x + 6, y - 2.6), (x + 4, y), (x - 4, y)]
    out = _path(_pd(hull, True), .8, "#fff")
    out += _path(_pds(_hatch(hull, 90, 1.2, step=.4)), W0)
    sail = [(x - .2, y - 12), (x - .2, y - 3.6), (x - 5.4, y - 3.6)]
    out += _path(_pd(sail, True), .7, "#fff")
    sail2 = [(x + .8, y - 10.4), (x + .8, y - 3.6), (x + 4.6, y - 3.6)]
    out += _path(_pd(sail2, True), .7, "#000")
    out += _path(_pds([[(x + .3, y - 13.4), (x + .3, y - 2.6)], [(x - 9, y + 1.4), (x - 5.6, y + 1.4)], [(x + 6, y + 1.4), (x + 9, y + 1.4)]]), W0)
    out += _path(_pd([(x + .3, y - 13.4), (x + 3, y - 12.6), (x + .3, y - 11.8)], True), W0, "#000")
    return out


def _rose(cx, cy, s=1.0):
    """An engraved rose head with two leaves."""
    o = []
    for side in (-1, 1):
        leaf = _spline([(cx + side * 4 * s, cy + 6 * s), (cx + side * 9 * s, cy + 6.5 * s), (cx + side * 12.5 * s, cy + 9.5 * s),
                        (cx + side * 8 * s, cy + 10.5 * s), (cx + side * 4 * s, cy + 6 * s)], True, 4)
        o.append(_path(_pd(leaf, True), W0, "#fff"))
        o.append(_path(_pd([(cx + side * 4.5 * s, cy + 6.6 * s), (cx + side * 11.5 * s, cy + 9.4 * s)]), W0))
    head = []
    for i in range(61):
        t = TAU * i / 60
        r = (6.2 + 1.5 * abs(math.sin(2.5 * t)) ** .6) * s
        head.append((cx + r * math.cos(t), cy - 1 * s + r * math.sin(t) * .92))
    o.append(_path(_pd(head, True), W1, "#fff"))
    o.append(_path(_pds(_hatch(head, 45, 1.5, pred=lambda x, y: (x - cx) + (y - cy) > 2.5 * s, step=.4)), W0))
    spiral = [(cx + (.6 + 5.4 * t) * s * math.cos(TAU * 2.2 * t + 1), cy - 1 * s + (.6 + 5.4 * t) * s * math.sin(TAU * 2.2 * t + 1) * .9)
              for t in [i / 60 for i in range(61)]]
    o.append(_path(_pd(spiral), W0))
    return "".join(o)


def _surf(cx, cy, s=1.0):
    """A breaking wave with a curling lip and foam claws."""
    M = lambda pts: [(cx + x * s, cy + y * s) for x, y in pts]
    body = M(_chunks([[(-13, 9), (-8, 6.6), (-4, 2.6), (-1.6, -2.4), (.6, -6.2), (3.6, -8.6), (7.4, -8.8), (10.4, -6.4)],
                      [(10.4, -6.4), (11, -3.4), (9.2, -1.4), (6.8, -2), (6.2, -4.2), (7.6, -5.2)],
                      [(7.6, -5.2), (5.2, -4.6), (4, -1), (5, 4), (8.6, 9)]], 4) + [(cx + 13 * s, cy + 9 * s)])
    body = [body[0]] + body[1:]
    o = [_path(_pd(body, True), W1, "#fff")]
    face = lambda x, y: not (-1.2 < (x - cx) / s + .45 * (y - cy) / s - 1.5 < 1.2)
    o.append(_path(_pds(_hatch(body, 120, 1.5, pred=face, step=.4)), W0))
    for i, (fx, fy) in enumerate([(.4, -6.6), (3.4, -9), (7, -9.2), (10, -7.2)]):
        p = (cx + fx * s, cy + fy * s)
        o.append(_kanok(p[0], p[1], 3.4 * s, -2.2 + i * .25, True))
    o.append(_path(_pds([[(cx - 13 * s, cy + 11 * s), (cx + 13 * s, cy + 11 * s)]]), W0))
    return "".join(o)


def _record(cx, cy, s=1.0):
    """A black vinyl record, white grooves 1 CSS wide on black, label and tone arm."""
    o = [_circle(cx, cy, 11 * s, W1, "#000")]
    o.append("".join(_circle(cx, cy, r * s, W1, extra=' stroke="#fff"') for r in (6.2, 8.6)))
    o.append(_circle(cx, cy, 3.8 * s, W0, "#fff"))
    o.append(_circle(cx, cy, .9 * s, W0, "#000"))
    arm = [(cx + 10 * s, cy - 11 * s), (cx + 9 * s, cy - 4 * s), (cx + 5.4 * s, cy + 1.2 * s)]
    o.append(_path(_pd(arm), W1, extra=' stroke="#fff" stroke-width="3"'))
    o.append(_path(_pd(arm), W1))
    o.append(_circle(cx + 10 * s, cy - 11 * s, 1.6 * s, W0, "#fff"))
    o.append(_path(_pd([(cx + 4.6 * s, cy + .4 * s), (cx + 6.6 * s, cy + 2.4 * s)]), 1.5))
    return "".join(o)


def _kranok_pair(cx, cy, s=1.0):
    """Thai lai kranok: two flames back to back around a black bud."""
    o = [_kanok(cx - 1 * s, cy + 6 * s, 14 * s, -2.25, False), _kanok(cx + 1 * s, cy + 6 * s, 14 * s, -.89, True)]
    bud = _spline([(cx - 2.6 * s, cy + 6 * s), (cx - 2 * s, cy + 1 * s), (cx, cy - 9 * s), (cx + 2 * s, cy + 1 * s),
                   (cx + 2.6 * s, cy + 6 * s)], False, 4)
    o.append(_path(_pd(bud, True), W0, "#000"))
    o.append(_path(_pd([(cx - 5 * s, cy + 7.5 * s), (cx + 5 * s, cy + 7.5 * s)]), W1))
    return "".join(o)


def _crane(x, y, s, up):
    """A crane in flight facing left: long neck forward, legs trailing, wings up or down."""
    body = [(x - 8 * s, y - .6 * s), (x - 6.5 * s, y), (x + 4 * s, y + .4 * s), (x + 10.5 * s, y + 1.2 * s)]
    if up:
        wing = _spline([(x - 2 * s, y), (x - 1 * s, y - 3 * s), (x + 1.5 * s, y - 5.5 * s), (x + 4.5 * s, y - 6.5 * s)], False, 3)
    else:
        wing = _spline([(x - 2 * s, y), (x - 1.5 * s, y + 2.5 * s), (x + 1 * s, y + 5 * s), (x + 4 * s, y + 6 * s)], False, 3)
    far = _spline([(x - 1 * s, y), (x + .5 * s, y - 2 * s), (x + 3 * s, y - 2.6 * s)], False, 3) if not up else []
    return [body, wing] + ([far] if far else [])


def _acanthus_leaf(cx, cy, a0, r0, turns=.8):
    """A deeply cut acanthus leaf rolling into a volute around (cx, cy), starting at angle a0, radius r0.
    Returns (outline, lines): lines are the vein, the bulino shading line and the cuts."""
    N = 40
    outer, inner, vein, shade, shade2, cuts = [], [], [], [], [], []
    for i in range(N + 1):
        t = i / N
        ang = a0 - TAU * turns * t
        r = r0 + (1.9 - r0) * t
        w = 5 * (1 - t) ** .7 + .5
        tooth = ((t * 4.5) % 1) ** 1.3 if t < .9 else 0
        ca, sa = math.cos(ang), math.sin(ang)
        P_ = lambda rr: (cx + rr * ca, cy + rr * sa)
        outer.append(P_(r + w * (.25 + .8 * tooth)))
        inner.append(P_(r - w * .7))
        if t < .85:
            vein.append(P_(r + .05 * w))
        if t < .7:
            shade.append(P_(r - .28 * w))
        if t < .32:
            shade2.append(P_(r - .62 * w))
        if 0 < i < N and abs((t * 4.5) % 1) < 1 / 9 and t < .9:
            cuts.append([P_(r + .05 * w), P_(r + w * .85)])
    return outer + inner[::-1], [vein, shade, shade2] + cuts, (cx + 1.9 * math.cos(a0 - TAU * turns), cy + 1.9 * math.sin(a0 - TAU * turns))


def _acanthus_tile(P, H, vertical=False):
    """One repeat of the acanthus scroll border: a white stem waving through a hatched ground, a
    deeply cut leaf rolling into each bay, berries in the corners. Seamless: anything crossing the
    tile's ends is drawn again one period over."""
    T = (lambda pts: [(y, x) for x, y in pts]) if vertical else (lambda pts: pts)
    o = ['<g fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round">']
    w, h = (H, P) if vertical else (P, H)
    o.append(f'<rect width="{w}" height="{h}" fill="#fff" stroke="none"/>')
    ground = [[(0, y), (P, y)] for y in [.5 + 1.5 * k for k in range(int(H / 1.5))]]
    o.append(_path(_pds([T(g) for g in ground]), W0))
    stem = [(x, H / 2 + 6 * math.sin(TAU * x / P)) for x in [-P / 2 + i * 1.4 for i in range(int(2 * P / 1.4) + 2)]]
    o.append(_path(_pd(T(stem)), 3) + _path(_pd(T(stem)), 1, extra=' stroke="#fff"'))
    cA = (.27 * P, H / 2 - 2.5)
    base = (.5 * P, H / 2)
    a0 = math.atan2(base[1] - cA[1], base[0] - cA[0])
    r0 = math.hypot(base[0] - cA[0], base[1] - cA[1])
    outline, lines, eye = _acanthus_leaf(cA[0], cA[1], a0, r0, .92)
    glide = lambda pts, dx: [(x + P / 2 + dx, H - y) for x, y in pts]
    for pts, ls, e in [(outline, lines, eye)] + [(glide(outline, dx), [glide(l, dx) for l in lines], glide([eye], dx)[0])
                                                  for dx in (0, -P)]:
        o.append(_path(_pd(T(pts), True), W0, "#fff"))
        o.append(_path(_pds([T(l) for l in ls]), W0))
        ex, ey = T([e])[0]
        o.append(_circle(ex, ey, .9, W0, "#000"))
    # berries in the narrow corners of each bay
    for bx, by in ((.76 * P, 3.4), (.26 * P, H - 3.4), (.76 * P - P, 3.4)):
        for dx, dy in ((-2.2, 0), (2.2, 0), (0, 1.4)):
            ex, ey = T([(bx + dx, by + dy)])[0]
            o.append(_circle(ex, ey, 1.1, W0, "#fff"))
    return "".join(o) + "</g>"


# ----------------------------------------------------------------------------------------------
# The plate
# ----------------------------------------------------------------------------------------------

VW, VH = 570, 324
PX0, PY0, PX1, PY1 = 34, 34, 536, 280          # the picture, inside the acanthus frame
BAND = 28


def cover_plate(day, width=570, height=None):
    """The engraved cover plate as one inline <svg>. Native size 570 x 338 CSS px: at that size
    every hatch line sits on the Kindle's device-pixel grid. `height` defaults to the native
    aspect; other sizes scale the art (and lose the grid alignment)."""
    day = day or {}
    d = day.get("date") or datetime.date.today()
    if isinstance(d, datetime.datetime):
        d = d.date()
    rng = random.Random(d.toordinal())
    doy = int(_num(day.get("doy"), d.timetuple().tm_yday))
    sunrise = _minutes(day.get("sunrise"), int(395 + 75 * math.cos(TAU * (doy + 10) / 365)))
    temp = day.get("temp_f")
    temp = None if temp is None else int(round(_num(temp, 0)))
    sky = str(day.get("sky") or "").lower()
    phase = _num(day.get("moon_phase"), _moon_phase(d)) % 1
    river = _num(day.get("river_ft"), 10.0)
    edition = day.get("edition_no")
    edition = int(_num(edition, doy)) if edition is not None else doy
    uid = f"m{d.toordinal() % 100000}"
    if height is None:
        height = round(width * VH / VW)

    # ---- eggs for the day: micro-digits and coordinates always; three of the rest rotate --------
    egg_pool = ["kite", "toyboat", "balloon", "vinyl", "pinwheel"]
    erng = random.Random(d.toordinal() * 7 + 3)
    eggs = set(erng.sample(egg_pool, 3))

    # ---- layout ----------------------------------------------------------------------------------
    hx = 262 + rng.uniform(-4, 4)                                  # Mt. Hood's summit
    az = 90 - 32 * math.cos(TAU * (doy - 172) / 365)              # sunrise azimuth (deg)
    off = (az - 93) * 1.2
    off = math.copysign(max(26.0, abs(off)), off if abs(off) > .5 else (1 if rng.random() < .5 else -1))
    sx, sy = hx + off, 86.0                                        # the rosette's center
    y_w = round(2 * max(182.0, min(212.0, 207 - river * 1.15))) / 2   # Columbia waterline, on the grid
    snow = 126 + 18 * math.cos(TAU * (doy - 30) / 365)             # snowline, lower in winter
    lobes = 12 + (sunrise // 7) % 17                               # rosette lobes from sunrise
    nrays = 180 + (sunrise % 60) * 2                               # ray count from sunrise
    rot = (sunrise % 60) / 60 * TAU / lobes                        # rosette turn from the minute
    moon = (98 + rng.uniform(-8, 8), 68 + rng.uniform(-4, 4), 14.5)
    cloudy = any(w in sky for w in ("cloud", "overcast", "rain", "shower", "drizzle", "storm", "snow"))
    rainy = any(w in sky for w in ("rain", "shower", "drizzle", "storm"))
    foggy = any(w in sky for w in ("fog", "mist", "haze", "smoke"))
    partly = "partly" in sky or "mostly sunny" in sky

    hood_ctrl = [(-152, 178), (-122, 167), (-96, 157), (-74, 144), (-57, 130), (-45, 119), (-36, 110), (-31, 104),
                 (-27, 106), (-20, 93), (-13, 82), (-6.5, 72), (-2, 67), (1.5, 65.5), (5, 67.5), (9, 71), (14.5, 80),
                 (19.5, 86), (25, 98), (33, 108), (40, 112), (47, 121), (61, 133), (81, 147), (106, 159), (136, 169), (162, 178)]
    hood_xy = [(hx + a, b + 4) for a, b in hood_ctrl]
    hood_xs = [p[0] for p in hood_xy]

    def hood_top(x):
        if x <= hood_xs[0] or x >= hood_xs[-1]:
            return 1e9
        i = min(bisect.bisect_right(hood_xs, x) - 1, len(hood_xy) - 2)
        (x0, y0), (x1, y1) = hood_xy[i], hood_xy[i + 1]
        y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return y + .7 * math.sin(x * 1.31) + .5 * math.sin(x * 2.93 + 1)

    ph1, ph2 = rng.uniform(0, TAU), rng.uniform(0, TAU)

    def f1(x):
        return 154 + 5 * math.sin(x * .029 + ph1) + 3 * math.sin(x * .081 + .5) + 1.4 * math.sin(x * .21) + .5 * math.sin(x * .9)

    def f2(x):
        return 168 + 4 * math.sin(x * .043 + ph2) + 2.4 * math.sin(x * .11 + 1) + 1 * math.sin(x * .33) + .4 * math.sin(x * 1.3)

    city = [(150 + i * 5, h) for i, h in enumerate([3, 5, 8, 6, 12, 7, 15, 9, 6, 10, 4, 3])]

    def shore_top(x):
        t = y_w - 4.5 - 1.2 * math.sin(x * .07 + 1) - .5 * math.sin(x * .5)
        for bx, bh in city:
            if bx <= x < bx + 4:
                t = min(t, y_w - 4.5 - bh)
        return t

    def isl_top(x):
        if x <= 112:
            return y_w + 3 + (x - 30) * .05 + .8 * math.sin(x * .3)
        if x < 168:
            t = (x - 112) / 56
            return y_w + 7.1 + .8 * math.sin(x * .3) + (t * t * (3 - 2 * t)) * 90
        return 1e9

    SKY, HOOD, F1, F2, SHORE, WATER, ISL = range(7)

    def owner(x, y):
        if y >= isl_top(x):
            return ISL
        if y >= y_w:
            return WATER
        if y >= shore_top(x):
            return SHORE
        if y >= f2(x):
            return F2
        if y >= f1(x):
            return F1
        if y >= hood_top(x):
            return HOOD
        return SKY

    def in_pic(x, y):
        return PX0 < x < PX1 and PY0 < y < PY1

    mx, my, mr = moon

    def sky_ok(x, y):
        return in_pic(x, y) and owner(x, y) == SKY and (x - mx) ** 2 + (y - my) ** 2 > (mr + 6.5) ** 2

    out = []
    A = out.append
    defs = []

    # ==== SKY ====================================================================================
    R_RAY1, R_HALO0, R_HALO1 = 120, 124, 138
    # 1. guilloche underprint: a barleycorn lattice in stepped bands, darkest at the zenith
    for name, hgt in (("a", 4), ("b", 6), ("c", 8)):
        amp = hgt / 4
        w1 = [(x, hgt / 2 + amp * math.sin(TAU * x / 12)) for x in [i * .75 for i in range(17)]]
        w2 = [(x, hgt / 2 - amp * math.sin(TAU * x / 12)) for x, _ in w1]
        defs.append(f'<pattern id="{uid}{name}" width="12" height="{hgt}" patternUnits="userSpaceOnUse">'
                    f'<path d="{_pds([w1, w2])}" fill="none" stroke="#000" stroke-width=".5"/></pattern>')
    hole = lambda cx, cy, r: f"M{_n(cx - r)} {_n(cy)}a{_n(r)} {_n(r)} 0 1 0 {_n(2 * r)} 0a{_n(r)} {_n(r)} 0 1 0 {_n(-2 * r)} 0z"
    defs.append(f'<clipPath id="{uid}p"><rect x="{PX0}" y="{PY0}" width="{PX1 - PX0}" height="{PY1 - PY0}"/></clipPath>')
    defs.append(f'<clipPath id="{uid}s"><path clip-rule="evenodd" d="M0 0H{VW}V{VH}H0z{hole(sx, sy, R_HALO1 + .5)}{hole(mx, my, mr + 6.5)}"/></clipPath>')
    A(f'<g clip-path="url(#{uid}p)"><g clip-path="url(#{uid}s)" stroke="none">'
      f'<rect x="{PX0}" y="{PY0}" width="{PX1 - PX0}" height="46" fill="url(#{uid}a)"/>'
      f'<rect x="{PX0}" y="80" width="{PX1 - PX0}" height="44" fill="url(#{uid}b)"/>'
      f'<rect x="{PX0}" y="124" width="{PX1 - PX0}" height="70" fill="url(#{uid}c)"/></g></g>')

    # 2. the sunburst halo: a woven guilloche ring around the rays, ruled both sides
    halo = []
    hl = max(10, lobes // 2) * 3
    for k in range(3):
        halo += _split(_rosette_curve("wave", sx, sy, hl, (R_HALO0 + R_HALO1) / 2, 3.6, rot + TAU * k / 3, 2.0), sky_ok)
    halo += _split(_ell_pts(sx, sy, R_HALO0 - 1.5, R_HALO0 - 1.5, 260), sky_ok)
    halo += _split(_ell_pts(sx, sy, R_HALO1, R_HALO1, 280), sky_ok)
    A(_path(_pds(halo), W0))

    # 3. rays, tiered; none closer than 1.5 CSS at their root
    rays = []
    r_root = max(52.0, 1.6 * nrays / TAU)
    for i in range(nrays):
        a = TAU * i / nrays + rot
        tier = i % 3
        r0 = 52 if tier == 0 else r_root
        r1 = R_RAY1 if tier == 0 else (R_RAY1 - 18 if tier == 1 else R_RAY1 - 34)
        ca, sa = math.cos(a), math.sin(a)
        rays += _runs((sx + r0 * ca, sy + r0 * sa), (sx + r1 * ca, sy + r1 * sa), sky_ok, 1.3, 2)
    A(_path(_pds(rays), W0))

    # 4. the rosette: hub, woven band, looped band, ruled and beaded rings, micro-digits
    ros = []
    keep = sky_ok
    if "vinyl" not in eggs:
        ros += _split(_rosette_curve("hypo", sx, sy, max(5, lobes // 2), 12, 4.4, rot, 1.2), keep)
    wl = max(6, lobes // 2)
    for k in range(3):
        ros += _split(_rosette_curve("wave", sx, sy, wl, 21.3, 2.8, rot + TAU * k / 3, 1.4), keep)
    for k in range(1 if lobes > 19 else 2):
        ros += _split(_rosette_curve("epi", sx, sy, lobes, 35.5, 4.1, rot + TAU * k / (2 * lobes), 1.6), keep)
    A(_path(_pds(ros), W0))
    A("".join(_circle(sx, sy, r) for r in (15.5, 26.5, 28, 41.5, 43, 48.5)))
    A(_circle(sx, sy, 30.5, 1.5, extra=' stroke-dasharray="0 3"'))
    micro = []
    if temp is not None:
        micro += _text_on_circle(f"{temp}°F", sx, sy, 45.75, -math.pi / 2 - .62, 3.4)
    micro += _text_on_circle(f"No {edition}", sx, sy, 45.75, -math.pi / 2 + .62, 3.4)
    micro += _text_on_circle(f"{d.month}·{d.day}", sx, sy, 45.75, -math.pi / 2, 3.4)
    A(_path(_pds([q for p in micro for q in _split(p, lambda x, y: owner(x, y) == SKY)]), W0))
    if "vinyl" in eggs:
        A(_record(sx, sy, 1.25))

    # 5. the moon at its phase: dark side ruled on the grid, seas hatched at 45 degrees
    waxing = phase < .5
    c = math.cos(TAU * phase)
    mo = []
    yy = math.floor(my - mr) + .5
    while yy < my + mr:
        w = math.sqrt(max(0, mr * mr - (yy - my) ** 2))
        a, b = (mx - w, mx + w * c) if waxing else (mx - w * c, mx + w)
        if b - a > .6:
            mo.append([(a, yy), (b, yy)])
        yy += 1.5
    A(_circle(mx, my, mr, 0, "#fff", ' stroke="none"'))
    A(_path(_pds(mo), W0))
    lit_ok = lambda x, y: (x - mx) ** 2 + (y - my) ** 2 < (mr - 1) ** 2 and (
        (x > mx + math.sqrt(max(0, mr * mr - (y - my) ** 2)) * c) if waxing else (x < mx - math.sqrt(max(0, mr * mr - (y - my) ** 2)) * c))
    maria = []
    for ex, ey, er in ((-4, -5, 3.6), (3.5, -6.5, 2.6), (5, 1, 3), (-7, 3, 3.4), (1, 6.5, 2)):
        maria += _hatch(_ell_pts(mx + ex, my + ey, er, er * .8, 14), 45, 1.5, pred=lit_ok, step=.4, minlen=.5)
    A(_path(_pds(maria), W0))
    if .03 < phase < .97:
        term = [((mx + mr * math.cos(t) * c) if waxing else (mx - mr * math.cos(t) * c), my + mr * math.sin(t))
                for t in [-math.pi / 2 + math.pi * i / 24 for i in range(25)]]
        A(_path(_pd(term), W0))
    A(_circle(mx, my, mr, W1) + _circle(mx, my, mr + 3, W0) + _circle(mx, my, mr + 5.5, 1.5, extra=' stroke-dasharray="0 3"'))

    # 6. clouds: billows outlined where they meet the sky, hatched through, belly ruled darker
    def cloud(cx, cy, wdt, n, bank=False):
        puffs = []
        for i in range(n):
            t = i / max(1, n - 1)
            r = (4.5 + 7.5 * math.sin(math.pi * (.15 + .7 * t))) * rng.uniform(.75, 1.15) * (.8 if bank else 1)
            puffs.append((cx - wdt / 2 + wdt * t + rng.uniform(-2, 2), cy - r * .5 - rng.uniform(0, 2.5), r))
        for i in range(n - 1):
            t = (i + .5) / (n - 1)
            r = 3.5 + 3.5 * math.sin(math.pi * t)
            puffs.append((cx - wdt / 2 + wdt * t, cy - r * .2 - rng.uniform(1, 4), r * 1.2))
        inside = lambda x, y, skip=-1: any((x - px) ** 2 + (y - py) ** 2 < (pr - .2) ** 2
                                           for j, (px, py, pr) in enumerate(puffs) if j != skip)
        base = cy + 2
        o = ["".join(_circle(px, py, pr, 0, "#fff", ' stroke="none"') for px, py, pr in puffs if py - pr < base)]
        outline, inner = [], []
        for j, (px, py, pr) in enumerate(puffs):
            m = max(20, int(pr * 3.2))
            ring = [(px + pr * math.cos(a), py + pr * math.sin(a)) for a in [TAU * i / m for i in range(m + 1)]]
            outline += _split(ring, lambda x, y, j=j: not inside(x, y, j) and y < base)
            arc = [(px + pr * math.cos(a), py + pr * math.sin(a)) for a in [math.pi * (1.05 + .5 * i / 10) for i in range(11)]]
            inner += _split(arc, lambda x, y, j=j: inside(x, y, j) and y < cy - 1)
        hi = lambda x, y: any((x - px + pr * .3) ** 2 + (y - py + pr * .4) ** 2 < (pr * .55) ** 2 for px, py, pr in puffs)
        body = lambda x, y: inside(x, y) and y < base
        x0, x1 = cx - wdt / 2 - 14, cx + wdt / 2 + 14
        light, dark = [], []
        y = math.ceil((cy - 22) / 2) * 2
        while y < base:
            light += _runs((x0, y), (x1, y), lambda x, yy: body(x, yy) and not hi(x, yy), .8, 1.2)
            y += 2
        y = math.ceil((cy - 4) / 2) * 2 + 1
        while y < base:
            dark += _runs((x0, y), (x1, y), lambda x, yy: body(x, yy), .8, 1.2)
            y += 2
        o.append(_path(_pds(light + dark), W0))
        o.append(_path(_pds(outline), W1))
        o.append(_path(_pds(inner), W0))
        o.append(_path(_pds([[(x0 + 10, base), (x1 - 10, base)]]), W0))
        return "".join(o)

    # the engraved cloud bank low along the horizon, behind the hills, every morning
    for bcx, bcy, bw in ((150, 140, 120), (452, 132, 110)):
        A(cloud(bcx + rng.uniform(-8, 8), bcy, bw, 9, True))
    if cloudy or partly:
        spots = [(185, 52, 52, 6), (452, 52, 60, 7), (505, 84, 36, 4), (380, 46, 40, 5)]
        rng.shuffle(spots)
        for cx, cy, wdt, n in spots[:2 if partly else 3]:
            A(cloud(cx + rng.uniform(-10, 10), cy + rng.uniform(-3, 5), wdt, n))
    if rainy:
        rain = []
        for i in range(70):
            x0 = rng.uniform(PX0 + 30, PX1 - 10)
            y0 = rng.uniform(62, 130)
            rain += _runs((x0, y0), (x0 - 2.5, y0 + 7), sky_ok, .8, 2)
        A(_path(_pds(rain), W0))

    # 7. cranes in formation, a long V across the sky
    lead = rng.choice([(150, 104), (430, 56), (468, 100), (176, 112)])
    if (lead[0] - sx) ** 2 + (lead[1] - sy) ** 2 < 70 ** 2:
        lead = (470, 100) if lead[0] < 300 else (180, 108)
    cr = []
    for k in range(9):
        arm = (k + 1) // 2
        side = 1 if k % 2 else -1
        x = lead[0] + arm * 13
        y = lead[1] + side * arm * 6.5
        if k == 0:
            y = lead[1]
        cr += _crane(x, y, 1, (k + d.day) % 3 == 0)
    halo_cr = _path(_pds(cr), 3, extra=' stroke="#fff"')
    A(halo_cr + _path(_pds(cr), W1))

    if "kite" in eggs:
        spots = [(150, 82), (215, 48), (480, 62), (380, 50), (128, 112)]
        spots = [p for p in spots if (p[0] - sx) ** 2 + (p[1] - sy) ** 2 > 70 ** 2 and (p[0] - mx) ** 2 + (p[1] - my) ** 2 > 32 ** 2
                 and abs(p[0] - lead[0] - 40) + abs(p[1] - lead[1]) > 50]
        kx, ky = rng.choice(spots or [(480, 62)])
        A(_kite(kx, ky, rng))

    # ==== TERRAIN =================================================================================
    land = [(x, min(hood_top(x), f1(x), f2(x)) - .3) for x in [PX0 + i * 2 for i in range(252)]]
    A(_path(_pd([(PX0, PY1)] + land + [(PX1, land[-1][1]), (PX1, PY1)], True), 0, "#fff", ' stroke="none"'))
    hood = []
    hpred = lambda x, y: owner(x, y) == HOOD and in_pic(x, y)
    for i in range(15):
        u = -1 + 2 * i / 14 + rng.uniform(-.04, .04)
        x = hx + u * 15
        y = hood_top(x) + 1.6
        ang = math.pi / 2 - u * 1.05
        L = rng.uniform(26, 70) * (1.25 - .5 * abs(u))
        pts = [(x, y)]
        for j in range(int(L / 1.6)):
            ang += rng.uniform(-.09, .09) - (ang - (math.pi / 2 - u * 1.05)) * .1
            x += 1.6 * math.cos(ang)
            y += 1.6 * math.sin(ang)
            pts.append((x, y))
        for off_ in ((-.75, .75) if u > -.1 else (0,)):
            hood += _split([(px + off_, py) for px, py in pts[1:]], hpred)

    def ridge_x(y):
        return hx + 2 + (y - 70) * .42

    snowy = lambda x, y: y > snow + 5 * math.sin(x * .19) + 3 * math.sin(x * .53)
    shade = lambda x, y: hpred(x, y) and x > ridge_x(y) + 2.5 * math.sin(y * .4) and not snowy(x, y)
    lit = lambda x, y: (hpred(x, y) and x <= ridge_x(y) + 2.5 * math.sin(y * .4) and y > 96 and not snowy(x, y)
                        and math.sin(x * .21 + y * .13) + math.sin(y * .37 - x * .05) > -.5)
    hbox = [(hood_xs[0], 60), (hood_xs[-1], 60), (hood_xs[-1], 182), (hood_xs[0], 182)]
    hood += _hatch(hbox, 45, 2, pred=shade, step=.8)
    hood += _hatch(hbox, 135, 3, pred=lit, step=.8)
    A(_path(_pds(hood), W0))
    forest = _hatch(hbox, 0, 1.5, pred=lambda x, y: hpred(x, y) and snowy(x, y), step=1)
    A(_path(_pds(forest), W0))
    edge = [(x, hood_top(x)) for x in [hood_xs[0] + .5 + i * 2.2 for i in range(int((hood_xs[-1] - hood_xs[0]) / 2.2))]]
    A(_path(_pds(_split(edge, lambda x, y: owner(x, y + .8) == HOOD and in_pic(x, y))), W1))

    # foothills (far light, near darker with a serrated tree line), the far shore and the city
    def rows(layer, pitch, y0, y1):
        segs = []
        y = math.ceil(y0 / pitch) * pitch
        while y < y1:
            segs += _runs((PX0, y), (PX1, y), lambda x, yy: owner(x, yy) == layer, 1.0, 1.0)
            y += pitch
        return segs
    terr = rows(F1, 3, 136, 215) + rows(F2, 2, 150, 215) + rows(SHORE, 1, y_w - 22, y_w)
    ser = []
    x = PX0 + 1
    while x < PX1:
        top = f2(x)
        if owner(x, top + .5) == F2:
            ser.append([(x, top), (x, top - 1.2 - 1.8 * abs(math.sin(x * 1.7)))])
        x += 1.5
    A(_path(_pds(terr), W0))
    A(_path(_pds(ser), W0))
    edges = []
    for fn, layer in ((f1, F1), (f2, F2)):
        e = [(x, fn(x)) for x in [PX0 + i * 3.5 for i in range(144)]]
        edges += _split(e, lambda x, y, layer=layer: owner(x, y + .6) == layer)
    A(_path(_pds(edges), W1))

    # the Columbia: grid-ruled in stepped pitches (1, 1.5, 2, 3) going forward, broken by ripples,
    # lighter in Hood's reflection, darker under the towers, glittering under the sun
    T1, T2, TOP, DECK = 412, 518, 110, 172
    hood_ref = lambda x, y: (y - y_w) < .5 * max(0, f1(x) - hood_top(x)) and abs(x - hx) < 120
    tower_ref = lambda x: abs(x - T1) < 9 or abs(x - T2) < 9
    water, ripples = [], []
    y = y_w + .5
    row = 0
    while y < PY1:
        dy = y - y_w
        pitch = 1 if dy < 6 else 1.5 if dy < 24 else 2 if dy < 48 else 3
        glit = 4 + dy * .2
        x = PX0
        while x < PX1:
            L = rng.uniform(18, 70)
            gap = rng.uniform(1, 3.5)
            x1 = min(PX1, x + L)
            okw = lambda xx, yy, row=row: (owner(xx, yy) == WATER and not (sx - glit < xx < sx + glit)
                                           and not (hood_ref(xx, yy) and row % 2 == 1))
            water += _runs((x, y), (x1, y), okw, 1.0, 1.0)
            if rng.random() < .25 and owner(x1 + 1, y) == WATER:
                ripples.append([(x1 - 1, y), (x1 + gap / 2, y - .9), (x1 + gap + 1, y)])
            x = x1 + gap
        gx = sx - glit
        while gx < sx + glit:
            L = rng.uniform(.8, 3.2)
            if rng.random() < .75:
                water.append([(gx, y), (gx + L, y)])
            gx += L + rng.uniform(1, 2.6)
        # darker reflections under the towers: an extra rule between the rows
        if pitch >= 2 and dy < 60:
            for tx in (T1, T2):
                if rng.random() < .7:
                    half = (9 - dy * .1) * rng.uniform(.4, 1)
                    xa = tx + rng.uniform(-2, 2)
                    water.append([(xa - half, y + pitch / 2), (xa + half, y + pitch / 2)])
        y += pitch
        row += 1
    A(_path(_pds(water), W0))
    A(_path(_pds(ripples), W0))

    # Sauvie Island bank and grass
    isl_poly = [(PX0, isl_top(PX0))] + [(x, min(PY1, isl_top(x))) for x in range(36, 168, 2)] + [(168, PY1), (PX0, PY1)]
    il = _hatch(isl_poly, 0, 1.5, step=.8)
    grass = []
    for x in range(PX0 + 1, 160, 2):
        t = isl_top(x)
        if t > PY1 - 4:
            break
        grass.append([(x, t), (x + rng.uniform(-1, 1), t - rng.uniform(1.2, 3))])
    A(_path(_pd(isl_poly), W1))
    A(_path(_pds(il), W0) + _path(_pds(grass), W0))

    # ==== OBJECTS =================================================================================
    firs = []
    x = 42 + rng.uniform(-3, 3)
    while x < 124:
        firs.append((x, rng.uniform(42, 92) * (1 - abs(x - 74) / 140)))
        x += rng.uniform(10, 16)
    for fx, fh in sorted(firs, key=lambda f: -f[1]):
        A(_fir(fx, isl_top(fx) + 1, fh, rng))

    # the St. Johns Bridge
    sag = DECK - 3

    def main_cable(x):
        m = (T1 + T2) / 2
        return TOP + 5 + (sag - TOP - 5) * (1 - ((x - m) / ((T2 - T1) / 2)) ** 2)

    def side_l(x):
        return TOP + 5 + (DECK - TOP - 5) * ((T1 - x) / (T1 - 352)) ** 1.25

    def side_r(x):
        return TOP + 5 + (DECK - TOP - 5) * ((x - T2) / (600 - T2)) ** 1.25
    sus = []
    for x in range(T1 + 3, T2 - 1, 3):
        sus.append([(x, main_cable(x)), (x, DECK)])
    for x in range(T1 - 3, 353, -3):
        sus.append([(x, side_l(x)), (x, DECK)])
    for x in range(T2 + 3, PX1, 3):
        sus.append([(x, side_r(x)), (x, DECK)])
    cables = [[(x, main_cable(x)) for x in range(T1, T2 + 1)], [(x, side_l(x)) for x in range(352, T1 + 1)],
              [(x, side_r(x)) for x in range(T2, PX1)]]
    A(_path(_pds(sus), W0))
    A(_path(_pds(cables), 3, extra=' stroke="#fff"') + _path(_pds(cables), W1))
    deck = [(336, DECK + 1), (PX1, DECK), (PX1, DECK + 4.5), (336, DECK + 5.5)]
    A(_path(_pd(deck, True), W1, "#fff"))
    truss = [[(x, DECK + (1 if i % 2 == 0 else 4)), (x + 3, DECK + (4 if i % 2 == 0 else 1))] for i, x in enumerate(range(338, PX1 - 1, 3))]
    A(_path(_pds(truss), W0))
    piers = []
    for px in (344, 364, 384):
        p = [(px - 2, DECK + 5), (px + 2, DECK + 5), (px + 2, y_w + .5), (px - 2, y_w + .5)]
        A(_path(_pd(p, True), W0, "#fff"))
        piers += _hatch(p, 90, 1.5, step=.5)
    A(_path(_pds(piers), W0))

    def tower(tx):
        o = []
        legs = []
        for side in (-1, 1):
            xo, xi = tx + side * 8, tx + side * 4.5
            legs.append([(xo, y_w + 1), (xo - side * 1.5, TOP + 2), (xo - side * .5, TOP - 3),
                         ((xo + xi) / 2 - side * .5, TOP - 10), (xi + side * .5, TOP - 3), (xi, TOP + 2), (xi, y_w + 1)])
        for leg in legs:
            o.append(_path(_pd(leg, True), W1, "#fff"))
        arches = []
        for y0, y1 in ((TOP + 4, TOP + 24), (TOP + 30, TOP + 52), (DECK + 6, min(y_w - 1, DECK + 24))):
            if y1 - y0 < 6:
                continue
            band = [(tx - 4.5, y0 - 3), (tx + 4.5, y0 - 3), (tx + 4.5, y1), (tx - 4.5, y1)]
            arch = [(tx - 3.5, y1)] + _spline([(tx - 3.5, y0 + 6), (tx - 2.2, y0 + 1.6), (tx, y0)], False, 4) + \
                _spline([(tx, y0), (tx + 2.2, y0 + 1.6), (tx + 3.5, y0 + 6)], False, 4)[1:] + [(tx + 3.5, y1)]
            o.append(_path(_pd(band, True), W0, "#fff"))
            o.append(_path(_pd(arch), W0))
            arches += _hatch(band, 0, 1.5, pred=lambda x, y, a=arch: not _inside(a + [a[0]], x, y), step=.5)
        o.append(_path(_pds(arches), W0))
        o.append(_path(_pds(_hatch(legs[1], 90, 1, step=.6) + _hatch(legs[0], 90, 2, step=.6)), W0))
        o.append(_path(_pds([[(tx - 6.5, TOP - 8), (tx - 6.5, TOP - 15)], [(tx + 6.5, TOP - 8), (tx + 6.5, TOP - 15)]]), W1))
        o.append(_circle(tx - 6.5, TOP - 15.5, .75, W0, "#000") + _circle(tx + 6.5, TOP - 15.5, .75, W0, "#000"))
        return "".join(o)
    A(tower(T1))
    A(tower(T2))
    if "balloon" in eggs:
        A(_balloon(T1 + 30 + rng.uniform(-6, 30), 90 + rng.uniform(-8, 8)))

    bx = 222 + rng.uniform(-12, 12)
    A(_sternwheeler(bx, y_w + 11, .95, mirror=rng.random() < .35))
    if "toyboat" in eggs:
        A(_toy_boat(rng.choice([330, 300, 300]), min(PY1 - 22, y_w + 30)))
    A(_heron(190, 262, .95))

    # ==== IN-PICTURE ORNAMENT: scroll corner panels and kanok spandrels ===========================
    def corner_panel(mirror):
        mx_ = (lambda x: VW - x) if mirror else (lambda x: x)
        mp = lambda pts: [(mx_(x), y) for x, y in pts]
        o = []
        edge = _spline([(PX0, 216), (56, 221), (92, 230), (122, 242), (146, 257), (164, 270), (182, PY1)], False, 6)
        poly = mp(edge + [(PX0, PY1)])
        o.append(_path(_pd(poly, True), W1, "#fff"))
        o.append(_path(_pd(mp([(x, y + 2.5) for x, y in edge[:-3]])), W0))
        o.append(_path(_pds(_hatch(poly, 0, 1.5, pred=lambda x, y: _inside(poly, x, y - 3.5), step=.8)), W0))
        vpoly, vc = _volute(mx_(140), 262, 12, -math.pi / 2, 1.55, 4.2, cw=not mirror)
        stem = mp(_spline([(98, 254), (112, 249.5), (126, 248.6), (140, 250)], False, 5))
        o.append(_path(_pd(stem), 4) + _path(_pd(stem), 2, extra=' stroke="#fff"'))
        o.append(_path(_pd(vpoly, True), W0, "#fff"))
        o.append(_path(_pd(vc[int(len(vc) * .1):]), W0))
        o.append(_circle(vc[-1][0], vc[-1][1], 1.5, W0, "#000"))
        for (lx, ly, L, a, fl) in ((108, 249, 13, -2.2, True), (122, 247, 12, -1.5, True), (152, 255, 11, -.6, True),
                                   (148, 272, 10, .25, False), (104, 262, 11, .5, False)):
            o.append(_kanok(lx, ly, L, a, fl, mirror_x=VW / 2 if mirror else None))
        cx, cy, rx, ry = mx_(70), 251, 31, 22.5
        o.append(_ellipse(cx, cy, rx + 3, ry + 3, W1, "#fff"))
        o.append(_ellipse(cx, cy, rx + 1.5, ry + 1.5, 1.5, extra=' stroke-dasharray="0 3"'))
        o.append(_ellipse(cx, cy, rx, ry, W0))
        bg = _ell_pts(cx, cy, rx - .5, ry - .5, 40)
        o.append(_path(_pds(_hatch(bg, 0, 2, step=.8)), W0))
        o.append(_kanok(cx - 2, cy - ry - 2.5, 12, -2.6, False) + _kanok(cx + 2, cy - ry - 2.5, 12, -.54, True))
        o.append(_path(_pd(_spline([(cx - 2.5, cy - ry - 2), (cx, cy - ry - 11), (cx + 2.5, cy - ry - 2)], False, 4), True), W0, "#000"))
        return "".join(o), (cx, cy)

    s_, (cx, cy) = corner_panel(False)
    A(s_)
    A(_drum_kit(cx, cy + 15, .9))
    s_, (cx, cy) = corner_panel(True)
    A(s_)
    A(_dog(cx - 9, cy + 15, .95))

    for mirror in (False, True):
        mx_ = (lambda x: VW - x) if mirror else (lambda x: x)
        sp_curve = [(mx_(PX0), PY0)] + [(mx_(PX0 + 40 * (1 - math.sin(t)) ** 1.6), PY0 + 40 * (1 - math.cos(t)) ** 1.6)
                                        for t in [i / 12 * math.pi / 2 for i in range(13)]]
        A(_path(_pd(sp_curve, True), W1, "#fff"))
        A(_path(_pds(_hatch(sp_curve, 0, 1.5, step=.6)), W0))
        for a, L in ((0.05, 22), (.78, 26), (1.52, 22)):
            ang = (math.pi - a) if mirror else a
            A(_kanok(mx_(PX0 + 2), PY0 + 2, L, ang, flip=not mirror if a < .7 else mirror))
        if mirror and "pinwheel" in eggs:
            A(_pinwheel(mx_(PX0 + 12), PY0 + 12, 8))
        else:
            A(_small_rosette(mx_(PX0 + 11), PY0 + 11, 7, 5 + rng.randrange(4), rng.uniform(0, 1)))

    # ==== THE FRAME: acanthus scroll border, medallions, cartouche and ribbon ======================
    P = 42
    defs.append(f'<pattern id="{uid}h" width="{P}" height="{BAND}" patternUnits="userSpaceOnUse" x="0" y="3.5">'
                f'{_acanthus_tile(P, BAND)}</pattern>')
    defs.append(f'<pattern id="{uid}H" width="{P}" height="{BAND}" patternUnits="userSpaceOnUse" x="0" y="{PY1 + 2.5}">'
                f'{_acanthus_tile(P, BAND)}</pattern>')
    defs.append(f'<pattern id="{uid}v" width="{BAND}" height="{P}" patternUnits="userSpaceOnUse" x="3.5" y="0">'
                f'{_acanthus_tile(P, BAND, True)}</pattern>')
    defs.append(f'<pattern id="{uid}V" width="{BAND}" height="{P}" patternUnits="userSpaceOnUse" x="{PX1 + 2.5}" y="0">'
                f'{_acanthus_tile(P, BAND, True)}</pattern>')
    bot = PY1 + 2.5
    A(f'<g stroke="none"><rect x="3.5" y="3.5" width="{VW - 7}" height="{BAND}" fill="url(#{uid}h)"/>'
      f'<rect x="3.5" y="{bot}" width="{VW - 7}" height="{BAND}" fill="url(#{uid}H)"/>'
      f'<rect x="3.5" y="3.5" width="{BAND}" height="{bot + BAND - 3.5}" fill="url(#{uid}v)"/>'
      f'<rect x="{PX1 + 2.5}" y="3.5" width="{BAND}" height="{bot + BAND - 3.5}" fill="url(#{uid}V)"/></g>')
    outer_b = bot + BAND
    # rules: 1.5 outside, hairlines either side of the band, 1 px round the picture
    A(f'<rect x="1" y="1" width="{VW - 2}" height="{_n(outer_b + 2.5 - 1)}" stroke-width="1.5"/>'
      f'<rect x="3" y="3" width="{VW - 6}" height="{_n(outer_b - 2.5)}"/>'
      f'<rect x="{PX0 - 2}" y="{PY0 - 2}" width="{PX1 - PX0 + 4}" height="{PY1 - PY0 + 4}"/>'
      f'<rect x="{PX0 - .75}" y="{PY0 - .75}" width="{PX1 - PX0 + 1.5}" height="{PY1 - PY0 + 1.5}" stroke-width="1"/>')

    def medallion(cx, cy, art):
        o = [_circle(cx, cy, 18, W1, "#fff"), _circle(cx, cy, 16.5, W0), _circle(cx, cy, 14.5, 1.5, extra=' stroke-dasharray="0 3"')]
        bg = _ell_pts(cx, cy, 12.6, 12.6, 36)
        o.append(_path(_pds(_hatch(bg, 0, 2, step=.6)), W0))
        o.append(_circle(cx, cy, 13, W0))
        o.append(art)
        return "".join(o)
    mid_y = (PY0 + PY1) / 2
    c0, c1 = 3.5 + BAND / 2, VW - 3.5 - BAND / 2
    r0, r1 = 3.5 + BAND / 2, bot + BAND / 2
    A(medallion(c0, r0, _rose(c0, r0 - 1, 1.15)))
    A(medallion(c1, r0, _surf(c1, r0 - .5, .85)))
    A(medallion(c0, r1, _record(c0, r1, 1)))
    A(medallion(c1, r1, _heron(c1 + 1, r1 + 10, .48)))
    A(medallion(VW / 2, r0, _kranok_pair(VW / 2, r0, .95)))
    A(medallion(c0, mid_y, _drum_kit(c0, mid_y + 8, .45)))
    A(medallion(c1, mid_y, _dog(c1 - 6, mid_y + 9, .55)))

    # the scroll cartouche under the plate, carrying the edition number and Sauvie's coordinates,
    # with a ribbon banner behind it: PORTLAND to the left, the date in Roman numerals to the right
    rib_y = outer_b + 3
    roman = f"{_roman(d.day)}·{_roman(d.month)}·{_roman(d.year)}"
    lt, lw = _text_polys("PORTLAND", 0, 0, 6, 1.6)
    rt, rw = _text_polys(roman, 0, 0, 6, 1.6)
    half = max(lw, rw) + 58
    rx0, rx1 = VW / 2 - half, VW / 2 + half
    for sgn, xe in ((-1, rx0), (1, rx1)):
        tail = [(xe - sgn * 6, rib_y - 4), (xe + sgn * 14, rib_y - 4), (xe + sgn * 9, rib_y + 2), (xe + sgn * 14, rib_y + 8),
                (xe - sgn * 6, rib_y + 8)]
        A(_path(_pd(tail, True), W1, "#fff"))
        A(_path(_pds(_hatch(tail, 0, 1.5, step=.5)), W0))
        fold = [(xe, rib_y + 8), (xe - sgn * 6, rib_y + 8), (xe, rib_y + 4)]
        A(_path(_pd(fold, True), W0, "#000"))
    ribbon = [(rx0, rib_y - 8), (rx1, rib_y - 8), (rx1, rib_y + 4), (rx0, rib_y + 4)]
    A(_path(_pd(ribbon, True), W1, "#fff"))
    A(_path(_pds([[(rx0 + 2, rib_y - 6), (rx1 - 2, rib_y - 6)], [(rx0 + 2, rib_y + 2), (rx1 - 2, rib_y + 2)]]), W0))
    tl, _ = _text_polys("PORTLAND", (rx0 + VW / 2 - 44) / 2, rib_y - 5, 6, 1.6)
    tr, _ = _text_polys(roman, (rx1 + VW / 2 + 44) / 2, rib_y - 5, 6, 1.6)
    A(_path(_pds(tl + tr), W1))
    cw, ch = 88, 40
    ctop = outer_b - 28
    cart = _chunks([[(VW / 2 - cw / 2, ctop + ch), (VW / 2 - cw / 2 + 5, ctop + ch / 2), (VW / 2 - cw / 2 + 1, ctop + 2)],
                    [(VW / 2 - cw / 2 + 1, ctop + 2), (VW / 2, ctop - 3), (VW / 2 + cw / 2 - 1, ctop + 2)],
                    [(VW / 2 + cw / 2 - 1, ctop + 2), (VW / 2 + cw / 2 - 5, ctop + ch / 2), (VW / 2 + cw / 2, ctop + ch)],
                    [(VW / 2 + cw / 2, ctop + ch), (VW / 2, ctop + ch + 3), (VW / 2 - cw / 2, ctop + ch)]], 5)
    A(_path(_pd(cart, True), W1, "#fff"))
    inner = [(VW / 2 + (x - VW / 2) * .92, ctop + ch / 2 + (y - ctop - ch / 2) * .84) for x, y in cart]
    A(_path(_pd(inner, True), W0))
    for sgn in (-1, 1):
        vp, vc = _volute(VW / 2 + sgn * (cw / 2 + 4), ctop + ch / 2 + 2, 7, math.pi if sgn < 0 else 0, 1.3, 2.6, cw=sgn > 0)
        A(_path(_pd(vp, True), W0, "#fff"))
        A(_circle(vc[-1][0], vc[-1][1], 1, W0, "#000"))
        A(_kanok(VW / 2 + sgn * 14, ctop - 1, 16, -math.pi / 2 + sgn * 1.25, flip=sgn < 0))
    ep, ew = _text_polys(f"No {edition}", VW / 2, ctop + 9, 11, 1.4)
    A(_path(_pds(ep), W1))
    cp, cwid = _text_polys("45.68N 122.82W", VW / 2, ctop + 25, 4, 1.6)
    A(_path(_pds(cp), W0))

    body = "".join(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="morning-plate" width="{width}" height="{height}" '
            f'viewBox="-.25 -.25 {VW} {VH}" role="img" aria-label="The Morning Edition, engraved plate for {d.isoformat()}" '
            f'style="display:block;max-width:100%;height:auto;background:#fff">'
            f'<defs>{"".join(defs)}</defs>'
            f'<rect x="-.25" y="-.25" width="{VW}" height="{VH}" fill="#fff"/>'
            f'<g fill="none" stroke="#000" stroke-width=".5" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


# ----------------------------------------------------------------------------------------------
# The crest
# ----------------------------------------------------------------------------------------------


def crest(seed, size=64):
    """A monogram "P" crest with laurels and a beaded rim, varying with the seed (a date or int)."""
    if isinstance(seed, (datetime.date, datetime.datetime)):
        seed = seed.toordinal()
    rng = random.Random(seed)
    c = 32
    out = []
    A = out.append
    lobes = 9 + rng.randrange(8)
    rot = rng.uniform(0, TAU)
    A(_circle(c, c, 30.6, 1.4, "#fff"))
    A(_circle(c, c, 28.6, 1.6, extra=' stroke-dasharray="0 2.6"'))
    A(_circle(c, c, 26.8, .7))
    ring = [_rosette_curve("wave", c, c, lobes, 24.2, 1.9, rot + TAU * k / 4, .9) for k in range(4)]
    A(_path(_pds(ring), W0))
    A(_circle(c, c, 21.6, .8, "#fff"))
    # laurels
    leaves = []
    nleaf = 6 + rng.randrange(3)
    for side in (-1, 1):
        stem = []
        for i in range(nleaf + 1):
            a = math.pi / 2 + side * (.35 + 1.75 * i / nleaf)
            stem.append((c + 18 * math.cos(a), c + 18 * math.sin(a)))
        A(_path(_pd(stem), .7))
        for i in range(1, nleaf + 1):
            a = math.pi / 2 + side * (.35 + 1.75 * i / nleaf)
            px, py = c + 18 * math.cos(a), c + 18 * math.sin(a)
            tang = a + side * math.pi / 2
            for off in (-.75, .75):
                la = tang + off * side * -1
                L = 4.6 - i * .15
                tip = (px + L * math.cos(la - side * .2 * 0), py + L * math.sin(la))
                nrm = la + math.pi / 2
                leaf = [(px, py), (px + L * .5 * math.cos(la) + 1.2 * math.cos(nrm), py + L * .5 * math.sin(la) + 1.2 * math.sin(nrm)),
                        tip, (px + L * .5 * math.cos(la) - 1.2 * math.cos(nrm), py + L * .5 * math.sin(la) - 1.2 * math.sin(nrm))]
                leaves.append(_spline(leaf, True, 3))
    A("".join(_path(_pd(l, True), W0, "#fff") for l in leaves))
    A(_path(_pds([[l[0], l[len(l) // 2]] for l in leaves]), W0))
    # the P: a bold engraved capital with a hairline-shaded bowl, filled black
    stem = [(25.2, 18.6), (30.6, 18.6), (30.6, 41.4), (32.8, 43.2), (23, 43.2), (25.2, 41.4)]
    bowl_o = _spline([(28, 18.6), (35, 18.4), (40.2, 21.4), (40.6, 26.4), (36.8, 31), (30, 31.6)], False, 6)
    bowl_i = _spline([(30.4, 29.2), (34, 28.6), (35.8, 25.6), (35, 21.8), (31.6, 20.8), (30.4, 21)], False, 6)
    serif = [(23, 18.6), (31, 18.6), (31, 20.2), (23, 20.2)]
    A(_path(_pd(stem, True) + _pd(bowl_o + bowl_i, True) + _pd(serif, True), .6, "#000", extra=' fill-rule="nonzero"'))
    # hairline swash and a star that moves with the day
    A(_path(_pd(_spline([(23, 44.6), (28, 46), (36, 45.4), (41.4, 42.6)], False, 6)), .7))
    sa = rng.choice([-1.02, -2.12, -1.2, -1.94])
    stx, sty = c + 16.5 * math.cos(sa), c + 16.5 * math.sin(sa) + 1
    star = [(stx + (2.2 if i % 2 == 0 else .8) * math.cos(-math.pi / 2 + i * math.pi / 4),
             sty + (2.2 if i % 2 == 0 else .8) * math.sin(-math.pi / 2 + i * math.pi / 4)) for i in range(8)]
    A(_path(_pd(star, True), W0, "#000"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="morning-crest" width="{size}" height="{size}" viewBox="0 0 64 64" '
            f'role="img" aria-label="P crest"><g fill="none" stroke="#000" stroke-width=".6" stroke-linecap="round" stroke-linejoin="round">'
            f'{"".join(out)}</g></svg>')


if __name__ == "__main__":
    import sys
    svg = cover_plate({"date": datetime.date.today()})
    sys.stdout.write(svg)
