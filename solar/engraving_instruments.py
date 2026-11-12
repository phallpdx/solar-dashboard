"""Engraved instruments for the Kindle morning paper.

Dials, thermometers, staffs and almanac charts drawn as 19th-century line engravings, in the
Evening Edition's line style (solar/kindle_evening.py): three line weights (W0 hairline 0.6,
W1 rule 1, W2 heavy rule 1.6), tone only from hatching, cross-hatching, ruling and stipple,
never grey, never opacity. Each function returns one complete, self-contained <svg> (its own
<defs> with ids unique to its inputs), with no transform attributes anywhere, so the Kindle's
`transform:none !important` reset cannot move a thing. All numbers are 13 px or larger.

    weather_glyph(kind, size=56)
    thermometer(now_f, lo_f, hi_f, width=60, height=180)
    sun_dial(sunrise, sunset, now, size=150)            -> size x round(size*.69)
    moon_phase(phase0to1, size=60)                      0 new, .25 first quarter, .5 full, .75 last
    tide_curve(points, now_hour, width=560, height=110)
    gauge(value, vmin, vmax, label, unit, size=150)
    river_staff(ft, flood_ft, width=70, height=180)
    bar_chart(values, labels, width=560, height=130, highlight=None, fmt=None)

Key shapes carry a class (ei-needle, ei-bar, ei-sun, ei-merc, ei-level, ei-now, ei-lit, ei-sc...)
so the self-test in __main__ can measure the drawn geometry against the inputs.
Stdlib only.
"""
import hashlib
import html
import math
import re

W0, W1, W2 = .6, 1, 1.6
K = 'stroke="#000"'
FONT = "Literata, Georgia, serif"


# ------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------

def _n(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _uid(*a):
    return "ei" + hashlib.md5(repr(a).encode()).hexdigest()[:6]


def _p(d, sw=W0, fill="none", extra=""):
    return f'<path d="{d}" fill="{fill}" {K} stroke-width="{_n(sw)}"{extra}/>'


def _circ(cx, cy, r, sw=W0, fill="none", extra=""):
    st = f' {K} stroke-width="{_n(sw)}"' if sw else ""
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="{fill}"{st}{extra}/>'


def _t(x, y, s, size=13, anchor="middle", weight=None, italic=False, halo=0, ls=None, cls=None):
    a = f'x="{_n(x)}" y="{_n(y)}" font-family="{FONT}" font-size="{_n(size)}" text-anchor="{anchor}" fill="#000"'
    if weight:
        a += f' font-weight="{weight}"'
    if italic:
        a += ' font-style="italic"'
    if halo:
        a += f' stroke="#fff" stroke-width="{_n(halo)}" stroke-linejoin="round" paint-order="stroke"'
    if cls:
        a += f' class="{cls}"'
    st = "font-variant-numeric:lining-nums"
    if ls:
        st += f";letter-spacing:{_n(ls)}px !important"
    return f'<text {a} style="{st}">{s if s.startswith("<tspan") else html.escape(s)}</text>'


_CW = {".": .27, ",": .27, ":": .28, " ": .27, " ": .17, "°": .4, "−": .6, "-": .36, "1": .5,
       "m": .82, "w": .74, "i": .29, "l": .29, "t": .36, "f": .34, "j": .29, "r": .4, "I": .36, "M": .9, "W": .95}


def _tw(s, size=13, bold=False):
    """Text width estimate for Literata (lining figures ~0.58 em)."""
    w = 0.0
    for c in s:
        if c in _CW:
            w += _CW[c]
        elif c.isdigit():
            w += .58
        elif c.isupper():
            w += .68
        else:
            w += .5
    return w * size * (1.06 if bold else 1)


def _fmt(v, dec=None):
    if dec is None:
        dec = 0 if abs(v - round(v)) < 1e-9 else 1
    s = f"{abs(v):,.{dec}f}"
    return ("−" if v < 0 and float(s.replace(",", "")) != 0 else "") + s


def _nice_step(span, target):
    """A 1-2-2.5-5 step giving about `target` divisions over span."""
    raw = span / max(target, 1)
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw - 1e-12:
            return m * mag
    return 10 * mag


def _decimals(step):
    for d in range(0, 4):
        if abs(step * 10 ** d - round(step * 10 ** d)) < 1e-9:
            return d
    return 3


def _frange(a, b, step):
    """Multiples of step in [a, b]."""
    i = math.ceil(a / step - 1e-9)
    out = []
    while i * step <= b + 1e-9:
        out.append(round(i * step, 10))
        i += 1
    return out


_TOK = re.compile(r"[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)")


def _xf(d, dx=0.0, dy=0.0, s=1.0, sy=None):
    """Move and scale path data (absolute M L C Q T S Z only): our way round transform attributes."""
    sy = s if sy is None else sy
    out, nums = [], []
    for tok in _TOK.findall(d):
        if tok.isalpha():
            if tok not in "MLCQTSZ":
                raise ValueError("_xf: absolute M L C Q T S Z only, got " + tok)
            out.append(tok)
        else:
            nums.append(float(tok))
            if len(nums) == 2:
                out.append(f"{_n(dx + nums[0] * s)},{_n(dy + nums[1] * sy)} ")
                nums = []
    return "".join(out).replace(" Z", "Z").replace(" M", "M").replace(" L", "L").replace(" C", "C").strip()


def _diag(s, back=False):
    """One seamless tile of 45-degree hatching (no patternTransform)."""
    if back:
        return f"M0,0L{_n(s)},{_n(s)}M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(s * 1.5)}M{_n(s / 2)},{_n(-s / 2)}L{_n(s * 1.5)},{_n(s / 2)}"
    return f"M0,{_n(s)}L{_n(s)},0M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(-s / 2)}M{_n(s / 2)},{_n(s * 1.5)}L{_n(s * 1.5)},{_n(s / 2)}"


def _defs(u, names, k=1.0):
    """Hatch, cross-hatch, rule, stipple and wave tiles, ids '{u}-{name}'. k thickens strokes when
    the widget is drawn smaller than its design size, so no line ever renders under 0.6 px."""
    sw = _n(.6 * k)
    tiles = {
        "h": (3.4, 3.4, f'<path d="{_diag(3.4)}" {K} stroke-width="{sw}"/>'),
        "hb": (3.4, 3.4, f'<path d="{_diag(3.4, True)}" {K} stroke-width="{sw}"/>'),
        "x": (3.4, 3.4, f'<path d="{_diag(3.4)}{_diag(3.4, True)}" {K} stroke-width="{sw}"/>'),
        "d": (2.4, 2.4, f'<path d="{_diag(2.4)}" {K} stroke-width="{_n(.7 * k)}"/>'),
        "r": (4, 2.2, f'<path d="M0,1.1H4" {K} stroke-width="{sw}"/>'),
        "rw": (4, 3, f'<path d="M0,1.5H4" {K} stroke-width="{sw}"/>'),
        "v": (2.4, 4, f'<path d="M1.2,0V4" {K} stroke-width="{sw}"/>'),
        "s": (2.8, 2.8, '<circle cx=".7" cy=".7" r=".55"/><circle cx="2.1" cy="2.1" r=".55"/>'),
        "s2": (4, 4, '<circle cx="1" cy="1" r=".5"/><circle cx="3" cy="3" r=".5"/>'),
        "w": (8, 3.6, f'<path d="M0,1.8Q2,.2 4,1.8T8,1.8" fill="none" {K} stroke-width="{sw}"/>'),
    }
    out = []
    for nm in names:
        w, h, c = tiles[nm]
        out.append(f'<pattern id="{u}-{nm}" width="{_n(w)}" height="{_n(h)}" patternUnits="userSpaceOnUse">{c}</pattern>')
    return "".join(out)


def _svg(w, h, body, defs="", label="", vb=None):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="einst" width="{_n(w)}" height="{_n(h)}" '
            f'viewBox="{vb or f"0 0 {_n(w)} {_n(h)}"}" role="img" aria-label="{html.escape(label)}">'
            + (f"<defs>{defs}</defs>" if defs else "") + body + "</svg>")


def _star4(cx, cy, r, fill="#000", sw=0):
    w = r * .22
    d = (f"M{_n(cx)},{_n(cy - r)}Q{_n(cx + w)},{_n(cy - w)} {_n(cx + r)},{_n(cy)}Q{_n(cx + w)},{_n(cy + w)} "
         f"{_n(cx)},{_n(cy + r)}Q{_n(cx - w)},{_n(cy + w)} {_n(cx - r)},{_n(cy)}Q{_n(cx - w)},{_n(cy - w)} {_n(cx)},{_n(cy - r)}Z")
    st = f' {K} stroke-width="{_n(sw)}"' if sw else ""
    return f'<path d="{d}" fill="{fill}"{st}/>'


def _beads(cx, cy, R, n, r):
    return "".join(f'<circle cx="{_n(cx + R * math.cos(2 * math.pi * i / n))}" cy="{_n(cy + R * math.sin(2 * math.pi * i / n))}" r="{_n(r)}"/>'
                   for i in range(n))


def _rosette(cx, cy, R, r, n, sw=W0):
    return "".join(_circ(cx + R * math.cos(2 * math.pi * i / n), cy + R * math.sin(2 * math.pi * i / n), r, sw)
                   for i in range(n))


def _scroll(x, y, s=1.0, flip=False, sw=W0):
    """A C-scroll with a curled end, drawn rightward from (x, y); flip mirrors it leftward."""
    sx = -s if flip else s
    d = "M0,0C4,-.5 8,-3 9,-6C10,-9 7,-11 5,-9.4C3.6,-8 4.6,-6 6.2,-6.6"
    d2 = "M0,0C3,1.4 6,1.4 8,.4"
    return _p(_xf(d, x, y, sx, s), sw) + _p(_xf(d2, x, y, sx, s), sw)


def _leaf(x, y, s=1.0, flip=False, sw=W0, tone="none"):
    """A small acanthus leaf lying rightward from (x, y)."""
    sx = -s if flip else s
    d = "M0,0C3,-3.6 8,-4.4 12,-2.6C10,-2 9.4,-1.2 9.6,0C8,-.8 6.6,-.6 6,.6C4.4,-.2 2.4,0 0,0Z"
    return _p(_xf(d, x, y, sx, s), sw, tone) + _p(_xf("M1,-.4C4,-1.8 7,-2.2 10,-2", x, y, sx, s), sw)


def _parse_time(s):
    """'7:04', '07:04', '7:04 AM', '4:48 pm', '16:48', '2026-11-12T07:04:00' -> minutes after midnight."""
    s = str(s).strip().lower()
    if "t" in s and re.match(r"\d{4}-\d\d-\d\d", s):
        s = s.split("t", 1)[1]
    m = re.match(r"(\d{1,2})(?::(\d{2}))?(?::\d{2}(?:\.\d+)?)?\s*([ap])?\.?\s*m?\.?", s)
    if not m:
        raise ValueError(f"cannot read time {s!r}")
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ap == "p" and h < 12:
        h += 12
    if ap == "a" and h == 12:
        h = 0
    return h * 60 + mi


def _clock(minutes, ampm=False):
    m = int(round(minutes)) % 1440
    h, mm = divmod(m, 60)
    h12 = h % 12 or 12
    s = f"{h12}:{mm:02d}"
    return s + (" am" if h < 12 else " pm") if ampm else s


# ------------------------------------------------------------------------------------------
# weather glyphs
# ------------------------------------------------------------------------------------------

_CLOUD = "M20,46C10,46 8,34 17,32C16,22 28,18 34,24C38,14 54,14 57,26C66,24 72,32 68,40C72,42 70,46 66,46Z"
_CLOUD_CURL = "M24,31C28,28 33,29 35,32M41,26C46,23 52,25 53,30"


def _cloud(u, cid, cx, base, s, tone, k):
    """A cumulus: white with ruled shade along its belly ('light'), hatched ('mid') or cross-hatched ('dark')."""
    d = _xf(_CLOUD, cx - 40 * s, base - 46 * s, s)
    curls = _xf(_CLOUD_CURL, cx - 40 * s, base - 46 * s, s)
    x0, y0, w = cx - 33 * s, base - 33 * s, 66 * s
    if tone == "light":
        shade = (f'<rect x="{_n(x0)}" y="{_n(base - 11 * s)}" width="{_n(w)}" height="{_n(12 * s)}" fill="url(#{u}-r)"/>'
                 f'<rect x="{_n(x0)}" y="{_n(base - 5 * s)}" width="{_n(w)}" height="{_n(6 * s)}" fill="url(#{u}-h)"/>')
    elif tone == "mid":
        shade = (f'<rect x="{_n(x0)}" y="{_n(y0)}" width="{_n(w)}" height="{_n(34 * s)}" fill="url(#{u}-h)"/>'
                 f'<rect x="{_n(x0)}" y="{_n(base - 9 * s)}" width="{_n(w)}" height="{_n(10 * s)}" fill="url(#{u}-x)"/>')
    else:
        shade = (f'<rect x="{_n(x0)}" y="{_n(y0)}" width="{_n(w)}" height="{_n(34 * s)}" fill="url(#{u}-x)"/>'
                 f'<rect x="{_n(x0)}" y="{_n(base - 10 * s)}" width="{_n(w)}" height="{_n(11 * s)}" fill="url(#{u}-d)"/>')
    curl = "" if tone == "dark" else _p(curls, W0 * k)
    return (f'<clipPath id="{u}{cid}"><path d="{d}"/></clipPath><path d="{d}" fill="#fff"/>'
            f'<g clip-path="url(#{u}{cid})">{shade}</g>{_p(d, W1 * k)}{curl}')


def _sun(cx, cy, r, L, k, n=16, u=None, face=True):
    """Engraved sun: alternate black wedge rays and wavy flame rays round a ringed disc."""
    rays, wav = [], []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        if i % 2 == 0:
            r0, r1, hw = r + 1.6 * k, r + L, math.radians(64 / n)
            p0 = (cx + r0 * math.cos(a - hw), cy + r0 * math.sin(a - hw))
            p1 = (cx + r0 * math.cos(a + hw), cy + r0 * math.sin(a + hw))
            tip = (cx + r1 * ca, cy + r1 * sa)
            rays.append(f"M{_n(p0[0])},{_n(p0[1])}L{_n(tip[0])},{_n(tip[1])}L{_n(p1[0])},{_n(p1[1])}Z")
        else:
            r0, r1 = r + 2 * k, r + L * .72
            m = (r0 + r1) / 2
            nx, ny = -sa, ca
            off = L * .14
            wav.append(f"M{_n(cx + r0 * ca)},{_n(cy + r0 * sa)}Q{_n(cx + (r0 + m) / 2 * ca + nx * off)},{_n(cy + (r0 + m) / 2 * sa + ny * off)} "
                       f"{_n(cx + m * ca)},{_n(cy + m * sa)}T{_n(cx + r1 * ca)},{_n(cy + r1 * sa)}")
    out = f'<path d="{"".join(rays)}"/>' + _p("".join(wav), W0 * k)
    out += _circ(cx, cy, r, W1 * k, "#fff")
    if face and u:
        out += _circ(cx, cy, r - 1.8 * k, 0, f"url(#{u}-r)")
    out += _circ(cx, cy, r - 1.8 * k, W0 * k)
    return out


def _fir(x, base, h, tone, k):
    w = h * .42
    tiers = 4
    pr, pl = [], []
    for i in range(1, tiers + 1):
        yy = base - h + h * i / tiers * .9
        ww = w * i / tiers
        pr.append(f"L{_n(x + ww)},{_n(yy)}L{_n(x + ww * .45)},{_n(yy - h * .07)}")
        pl.append(f"L{_n(x - ww * .45)},{_n(yy - h * .07)}L{_n(x - ww)},{_n(yy)}")
    d = (f"M{_n(x)},{_n(base - h)}" + "".join(pr[:-1]) + f"L{_n(x + w)},{_n(base - h * .1)}L{_n(x + .8)},{_n(base - h * .1)}"
         f"L{_n(x + .8)},{_n(base)}L{_n(x - .8)},{_n(base)}L{_n(x - .8)},{_n(base - h * .1)}L{_n(x - w)},{_n(base - h * .1)}"
         + "".join(reversed(pl[:-1])) + "Z")
    return _p(d, W0 * k, tone, ' stroke-linejoin="round"')


def _crescent(cx, cy, r, k, lit_frac=.28, fill="#fff"):
    rx = abs(1 - 2 * lit_frac) * r
    d = (f"M{_n(cx)},{_n(cy - r)}A{_n(r)},{_n(r)} 0 0 1 {_n(cx)},{_n(cy + r)}"
         f"A{_n(rx)},{_n(r)} 0 0 0 {_n(cx)},{_n(cy - r)}Z")
    return _p(d, W1 * k, fill)


def _snowflake(cx, cy, r, k):
    d = ""
    for i in range(6):
        a = math.pi / 3 * i - math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        d += f"M{_n(cx)},{_n(cy)}L{_n(cx + r * ca)},{_n(cy + r * sa)}"
        bx, by = cx + r * .58 * ca, cy + r * .58 * sa
        for s in (-1, 1):
            b = a + s * math.pi / 4
            d += f"M{_n(bx)},{_n(by)}L{_n(bx + r * .36 * math.cos(b))},{_n(by + r * .36 * math.sin(b))}"
    return _p(d, W0 * k * 1.25, extra=' stroke-linecap="round"')


def _rain(x0, y0, n, dx, rows, k, ln=6.0):
    d = ""
    for i in range(n):
        for j in range(rows):
            x = x0 + i * dx + (j % 2) * dx / 2 - j * 2.2
            y = y0 + j * (ln + 3) + (i % 2) * 2.2
            d += f"M{_n(x)},{_n(y)}L{_n(x - ln * .36)},{_n(y + ln)}"
    return _p(d, W1 * k, extra=' stroke-linecap="round"')


WEATHER_KINDS = ("clear", "partly", "cloudy", "fog", "rain", "showers", "snow", "thunder", "wind", "smoke", "night-clear")


def weather_glyph(kind, size=56):
    """An engraved weather emblem in a beaded roundel. kind: one of WEATHER_KINDS."""
    kind = {"sun": "clear", "sunny": "clear", "cloud": "cloudy", "overcast": "cloudy", "storm": "thunder",
            "clear-night": "night-clear", "night": "night-clear", "haze": "smoke", "drizzle": "showers"}.get(kind, kind)
    if kind not in WEATHER_KINDS:
        raise ValueError(f"weather_glyph: unknown kind {kind!r}")
    k = max(1.0, 56.0 / size)          # keeps every rendered stroke at 0.6 px or more
    u = _uid("wx", kind, size)
    c = 28
    g = ""
    if kind == "clear":
        g = _sun(c, c, 8.4, 11, k, 16, u)
    elif kind == "night-clear":
        g = (f'<rect x="0" y="0" width="56" height="56" fill="url(#{u}-r)"/>'
             + _crescent(30, 27, 10.5, k, .3)
             + _p("M33.5,21.5C35,22.8 35.4,25 34.6,26.6M35,30.5C35.6,31.4 35.4,32.6 34.6,33.2", W0 * k)
             + _star4(15, 17, 3.6, "#fff", W0 * k) + _star4(42, 14, 2.6, "#fff", W0 * k)
             + _star4(17, 38, 2.4, "#fff", W0 * k) + _star4(44, 39, 3.2, "#fff", W0 * k)
             + _star4(12, 28, 1.6, "#fff", W0 * k))
    elif kind == "partly":
        g = _sun(21, 22, 6.6, 8, k, 16, u, face=False) + _cloud(u, "c", 33, 43, .5, "light", k)
    elif kind == "cloudy":
        g = _cloud(u, "b", 22, 33, .44, "mid", k) + _cloud(u, "c", 32, 43, .52, "light", k)
    elif kind == "fog":
        g = _circ(28, 19, 7, W0 * k, "#fff", ' stroke-dasharray="1.6 1.6"')
        d = ""
        for i, (x0, x1) in enumerate(((10, 40), (16, 48), (8, 34), (20, 46), (12, 42))):
            y = 26 + i * 4.6
            d += f"M{x0},{_n(y)}Q{_n(x0 + 2.5)},{_n(y - 1.6)} {_n(x0 + 5)},{_n(y)}T{_n(x0 + 10)},{_n(y)}L{x1},{_n(y)}"
        g += _p(d, W1 * k, extra=' stroke-linecap="round"')
    elif kind == "rain":
        g = _cloud(u, "c", 28, 33, .5, "mid", k) + _rain(19, 36, 5, 5.2, 2, k)
    elif kind == "showers":
        g = _sun(36, 17, 5.6, 7, k, 12, u, face=False) + _cloud(u, "c", 26, 35, .46, "light", k) + _rain(21, 38, 3, 6.5, 2, k, 5)
    elif kind == "snow":
        g = (_cloud(u, "c", 28, 32, .5, "light", k) + _snowflake(19, 40, 3.6, k) + _snowflake(30, 44, 3.6, k)
             + _snowflake(40, 39, 3.2, k) + _circ(25, 37.5, .9, 0, "#000") + _circ(35, 45.5, .9, 0, "#000"))
    elif kind == "thunder":
        g = (_cloud(u, "c", 28, 32, .5, "dark", k)
             + _p("M29,30L22.5,40.5H27.5L23.5,50L35,36.5H29.6L33.4,30Z", W0 * k, "#000", ' stroke-linejoin="round"')
             + _rain(14, 35, 2, 4, 1, k, 5) + _rain(39, 35, 2, 4, 1, k, 5))
    elif kind == "wind":
        d = ("M8,22C18,22 26,22.5 33,21C39,19.6 40,13.6 35.6,12.6C32.4,11.9 30.6,15 32.6,17"
             "M7,30C17,30 30,29.6 40,30C46,30.4 48.6,35.6 45.4,38.6C42.6,41 38.6,38.6 40.6,35.6"
             "M11,37.6C17,37.6 23,37.8 28,38.6")
        g = _p(d, W1 * k * 1.25, extra=' stroke-linecap="round"') + _p("M12,26H30M14,34H34", W0 * k, extra=' stroke-linecap="round"')
        g += _leaf(40, 22.5, .62, False, W0 * k, f"url(#{u}-h)") + _leaf(20, 44, .5, False, W0 * k, f"url(#{u}-h)")
    elif kind == "smoke":
        # a pall of wildfire smoke: the sun a dotted ghost behind a hatched billow, a plume off the ridge
        g = _circ(38, 16, 6.4, W0 * k, f"url(#{u}-s2)", ' stroke-dasharray="1.6 1.4"')
        g += _cloud(u, "c", 27, 31, .52, "mid", k)
        plume = "M12,45C10,40 14,37 13,33C16,34 17,37 19,37C19,34 22,32 25,33C24,36 26,39 24,42C22,45 17,46 12,45Z"
        g += _p(plume, W0 * k, f"url(#{u}-h)") + _p("M14,40C16,38.4 18,38.6 19.6,40", W0 * k)
        g += (f'<path d="M4,52L4,47C14,45 24,46 52,45.4L52,52Z" fill="#fff"/>' + _fir(9, 50, 13, f"url(#{u}-x)", k)
              + _fir(40, 50, 17, f"url(#{u}-x)", k) + _fir(47, 50, 12, f"url(#{u}-x)", k) + _fir(32, 50, 10, f"url(#{u}-x)", k)
              + _p("M4,50H52", W0 * k))
    ring = (_circ(c, c, 27, W2 * k, "#fff")
            + f'<g>{_beads(c, c, 24.7, 36, .95)}</g>'
            + _circ(c, c, 22.6, W0 * k))
    clip = f'<clipPath id="{u}k"><circle cx="{c}" cy="{c}" r="22"/></clipPath>'
    body = ring + clip + f'<g clip-path="url(#{u}k)">{g}</g>'
    defs = _defs(u, ("h", "x", "d", "r", "s2"), k)
    return _svg(size, size, body, defs, kind.replace("-", " "), vb="0 0 56 56")


# ------------------------------------------------------------------------------------------
# thermometer
# ------------------------------------------------------------------------------------------

def thermometer(now_f, lo_f, hi_f, width=60, height=180):
    """Mercury column to now_f; a bracket from lo_f to hi_f (today's range); scale in degrees F."""
    u = _uid("th", now_f, lo_f, hi_f, width, height)
    lo_f, hi_f = min(lo_f, hi_f), max(lo_f, hi_f)
    W, H = width, height
    smin = math.floor((min(lo_f, now_f) - 3) / 10) * 10
    smax = math.ceil((max(hi_f, now_f) + 3) / 10) * 10
    while smax - smin < 30:
        smax += 5
        smin -= 5
    y0, y1 = 44.0, H - 34.0
    ppd = (y1 - y0) / (smax - smin)

    def Y(f):
        return y1 - (f - smin) * ppd

    tx = round(W * .34) + .5
    bulb_cy, bulb_r = H - 19.0, 7.4
    lab = 10 if 10 * ppd >= 15 else 20
    minor = 2 if 2 * ppd >= 2.4 else 5
    out = []
    # the plate: double border, an arched head, scrolls at the foot
    pl, pr, pt, pb = 2.0, W - 2.0, 3.0, H - 2.0
    arch = (f"M{_n(pl)},{_n(pb)}V{_n(pt + 12)}C{_n(pl)},{_n(pt + 4)} {_n(W / 2 - 10)},{_n(pt + 4)} {_n(W / 2)},{_n(pt)}"
            f"C{_n(W / 2 + 10)},{_n(pt + 4)} {_n(pr)},{_n(pt + 4)} {_n(pr)},{_n(pt + 12)}V{_n(pb)}Z")
    out.append(_p(arch, W1, "#fff"))
    inner = (f"M{_n(pl + 2.6)},{_n(pb - 2.6)}V{_n(pt + 13)}C{_n(pl + 2.6)},{_n(pt + 6.8)} {_n(W / 2 - 9)},{_n(pt + 6.8)} {_n(W / 2)},{_n(pt + 3.2)}"
             f"C{_n(W / 2 + 9)},{_n(pt + 6.8)} {_n(pr - 2.6)},{_n(pt + 6.8)} {_n(pr - 2.6)},{_n(pt + 13)}V{_n(pb - 2.6)}Z")
    out.append(_p(inner, W0))
    out.append(_circ(W / 2, pt + 1.2, 1.2, 0, "#000"))
    # reading
    out.append(_t(W / 2 + 2, 24, f"{_fmt(now_f, 0)}°", 16, weight=700))
    out.append(_p(f"M{_n(pl + 7)},{_n(29.5)}H{_n(pr - 7)}", W0) + _star4(W / 2, 29.5, 2.2))
    # scale ticks & numerals
    ticks = ""
    for v in _frange(smin, smax, minor):
        y = Y(v)
        major = abs(v / lab - round(v / lab)) < 1e-9
        mid = (not major) and abs(v / 5 - round(v / 5)) < 1e-9 and minor < 5
        ticks += f"M{_n(tx + 4.2)},{_n(y)}H{_n(tx + (11 if major else 8.6 if mid else 7.2))}"
    out.append(_p(ticks, W0))
    major_ticks = "".join(f"M{_n(tx + 4.2)},{_n(Y(v))}H{_n(tx + 11)}" for v in _frange(smin, smax, lab))
    out.append(_p(major_ticks, W1))
    for v in _frange(smin, smax, lab):
        out.append(_t(tx + 13, Y(v) + 4.6, _fmt(v, 0), 13, "start", cls="ei-sc"))
    # the tube and bulb
    top = y0 - 7
    tube = (f"M{_n(tx - 3.4)},{_n(bulb_cy - bulb_r + 1)}V{_n(top)}A3.4,3.4 0 0 1 {_n(tx + 3.4)},{_n(top)}"
            f"V{_n(bulb_cy - bulb_r + 1)}")
    out.append(_p(tube, W1, "#fff"))
    my = Y(now_f)
    my = max(top - 1, min(bulb_cy, my))
    out.append(f'<rect class="ei-merc" x="{_n(tx - 1.7)}" y="{_n(my)}" width="3.4" height="{_n(bulb_cy - my)}" fill="#000"/>')
    out.append(_circ(tx, bulb_cy, bulb_r, W1, "#000"))
    out.append(_circ(tx, bulb_cy, bulb_r + 2.2, W0))
    out.append(_p(f"M{_n(tx - 4.2)},{_n(bulb_cy - 2.4)}A4.6,4.6 0 0 1 {_n(tx - 1)},{_n(bulb_cy - 4.8)}", 1.1, extra=' stroke="#fff" stroke-linecap="round"').replace(K + " ", "", 1))
    # bulb guard: two scrolls and a shelf
    out.append(_scroll(tx + 10, bulb_cy + 4, .78, False, W0) + _scroll(tx - 10, bulb_cy + 4, .78, True, W0))
    out.append(_p(f"M{_n(tx - 10)},{_n(bulb_cy + 4)}H{_n(tx - 6)}M{_n(tx + 6)},{_n(bulb_cy + 4)}H{_n(tx + 10)}", W0))
    out.append(_leaf(tx + 4, top - 2, .5, False, W0, f"url(#{u}-h)") + _leaf(tx - 4, top - 2, .5, True, W0, f"url(#{u}-h)"))
    # today's range: bracket left of the tube with H and L
    yh, yl = Y(hi_f), Y(lo_f)
    bx = tx - 8.5
    out.append(f'<rect x="{_n(bx - 2.6)}" y="{_n(yh)}" width="2.6" height="{_n(max(yl - yh, .1))}" fill="url(#{u}-h)"/>')
    out.append(_p(f"M{_n(tx - 4.4)},{_n(yh)}H{_n(bx)}V{_n(yl)}H{_n(tx - 4.4)}", W1, extra=' class="ei-range"'))
    out.append(f'<path d="M{_n(tx - 4.2)},{_n(yh)}l-3,-2.2v4.4Z"/><path d="M{_n(tx - 4.2)},{_n(yl)}l-3,-2.2v4.4Z"/>')
    ly_h, ly_l = yh + 3.8, yl + 3.8
    if ly_l - ly_h < 11:
        mid = (ly_h + ly_l) / 2
        ly_h, ly_l = mid - 5.5, mid + 5.5
    out.append(_t(bx - 6.2, ly_h, "H", 10.5, weight=700) + _t(bx - 6.2, ly_l, "L", 10.5, weight=700))
    defs = _defs(u, ("h",))
    return _svg(W, H, "".join(out), defs, f"{_fmt(now_f, 0)} degrees; low {_fmt(lo_f, 0)}, high {_fmt(hi_f, 0)}")


# ------------------------------------------------------------------------------------------
# sun dial
# ------------------------------------------------------------------------------------------

def _dur(mins):
    h, m = divmod(int(round(mins)), 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def sun_dial(sunrise, sunset, now, size=150):
    """The day's light as a semicircular dial: sunrise at the left horizon, sunset at the right,
    the sun at its true fraction of the daylight, the arc inked solid for the light already spent."""
    u = _uid("sd", sunrise, sunset, now, size)
    sr, ss, nw = _parse_time(sunrise), _parse_time(sunset), _parse_time(now)
    if ss <= sr:
        ss += 720 if ss + 720 > sr else 1440
    day = ss - sr
    f = (nw - sr) / day
    W = size
    R = W / 2 - 13
    cx, cy = W / 2, R + 15
    H = round(cy + 25)

    def P(fr, r):
        th = math.pi * (1 - fr)
        return cx + r * math.cos(th), cy - r * math.sin(th)

    out = []
    # hour lines, as on a garden sundial, and the gnomon
    lines = ""
    first_h = math.ceil(sr / 60)
    hours = [h for h in range(first_h, int(ss // 60) + 1) if sr < h * 60 < ss]
    for h in hours:
        fr = (h * 60 - sr) / day
        a, b = P(fr, 9), P(fr, R - 29)
        lines += f"M{_n(a[0])},{_n(a[1])}L{_n(b[0])},{_n(b[1])}"
    out.append(_p(lines, W0, extra=' stroke-dasharray="1.2 1.8"'))
    out.append(_p(f"M{_n(cx - 7)},{_n(cy)}A7,7 0 0 1 {_n(cx + 7)},{_n(cy)}", W0, f"url(#{u}-x)"))
    # the arc band: inked for spent light, ruled for light to come
    ro, ri = R + 2.6, R - 2.6
    fe = max(0.0, min(1.0, f))
    out.append(_p(f"M{_n(cx - ro)},{_n(cy)}A{_n(ro)},{_n(ro)} 0 0 1 {_n(cx + ro)},{_n(cy)}", W0))
    out.append(_p(f"M{_n(cx - ri)},{_n(cy)}A{_n(ri)},{_n(ri)} 0 0 1 {_n(cx + ri)},{_n(cy)}", W0))
    nb = int(math.pi * (R + 7.5) / 4.2)
    out.append("<g>" + "".join(f'<circle cx="{_n(P(i / nb, R + 7.5)[0])}" cy="{_n(P(i / nb, R + 7.5)[1])}" r=".85"/>'
                               for i in range(1, nb)) + "</g>")
    if fe > 0:
        a0, a1 = P(0, ro), P(fe, ro)
        b0, b1 = P(fe, ri), P(0, ri)
        out.append(f'<path class="ei-spent" d="M{_n(a0[0])},{_n(a0[1])}A{_n(ro)},{_n(ro)} 0 0 1 {_n(a1[0])},{_n(a1[1])}'
                   f'L{_n(b0[0])},{_n(b0[1])}A{_n(ri)},{_n(ri)} 0 0 0 {_n(b1[0])},{_n(b1[1])}Z"/>')
    # quarter-hour and hour ticks across the band; numerals inside
    qt, ht = "", ""
    q = math.ceil(sr / 15)
    while q * 15 < ss:
        fr = (q * 15 - sr) / day
        if q % 4 == 0:
            a, b = P(fr, ri - 3.4), P(fr, ro + 3.4)
            ht += f"M{_n(a[0])},{_n(a[1])}L{_n(b[0])},{_n(b[1])}"
        else:
            a, b = P(fr, ri), P(fr, ro)
            qt += f"M{_n(a[0])},{_n(a[1])}L{_n(b[0])},{_n(b[1])}"
        q += 1
    out.append(_p(qt, W0) + _p(ht, W1))
    # spent band hides its own ticks; redraw them white so the hours still read across the black
    if fe > 0:
        wt = ""
        q = math.ceil(sr / 15)
        while q * 15 < sr + fe * day:
            fr = (q * 15 - sr) / day
            a, b = P(fr, ri + .5), P(fr, ro - .5)
            wt += f"M{_n(a[0])},{_n(a[1])}L{_n(b[0])},{_n(b[1])}"
            q += 1
        out.append(f'<path d="{wt}" stroke="#fff" stroke-width=".8" fill="none"/>')
    rn = R - 19.5
    step = 1
    px_per_h = math.pi * rn / (day / 60)
    while px_per_h * step < 19:
        step += 1
    for h in hours:
        if h % step:
            continue
        fr = (h * 60 - sr) / day
        if fr < .07 or fr > .93:
            continue
        x, y = P(fr, rn)
        out.append(_t(x, y + 4.6, str(h % 12 or 12), 13, cls="ei-hr"))
    # sunrise and sunset ticks at the horizon
    out.append(_p(f"M{_n(cx - R)},{_n(cy - 8)}V{_n(cy + 4)}M{_n(cx + R)},{_n(cy - 8)}V{_n(cy + 4)}", W2, extra=' class="ei-rs"'))
    # horizon: heavy rule, hairline, water dashes
    out.append(_p(f"M3,{_n(cy)}H{_n(W - 3)}", W2) + _p(f"M3,{_n(cy + 2.6)}H{_n(W - 3)}", W0))
    # the sun
    if 0 <= f <= 1:
        sx, sy = P(f, R)
        out.append(f'<g class="ei-sun" data-cx="{_n(sx)}" data-cy="{_n(sy)}">'
                   + _circ(sx, sy, 10.6, 0, "#fff") + _sun(sx, sy, 5.2, 4.6, 1, 12, u, face=False) + "</g>")
        caption = f"{_dur(day)} light"
    else:
        ex = cx - R if f < 0 else cx + R
        out.append(f'<clipPath id="{u}h"><rect x="0" y="0" width="{W}" height="{_n(cy - 1)}"/></clipPath>'
                   f'<g clip-path="url(#{u}h)" class="ei-sun" data-cx="{_n(ex)}" data-cy="{_n(cy)}">'
                   + _circ(ex, cy, 6.4, W1, f"url(#{u}-x)") + "</g>")
        caption = f"rises in {_dur(sr - nw)}" if f < 0 else f"set {_dur(nw - ss)} ago"
        if nw < sr - 6 * 60 or f > 1 and nw - ss > 8 * 60:
            caption = f"{_dur(day)} light"
    ly = cy + 17.5
    out.append(_t(cx - R - 1, ly, _clock(sr), 13, "middle", weight=600) + _t(cx + R + 1, ly, _clock(ss), 13, "middle", weight=600))
    out.append(_t(cx, ly, caption, 13, italic=True))
    # flourishes under the horizon ends
    defs = _defs(u, ("x", "s2"))
    return _svg(W, H, "".join(out), defs, f"sunrise {_clock(sr, True)}, sunset {_clock(ss, True)}, now {_clock(nw, True)}")


# ------------------------------------------------------------------------------------------
# moon
# ------------------------------------------------------------------------------------------

def moon_phase(phase0to1, size=60):
    """The moon at its phase (0 new, .25 first quarter, .5 full, .75 last quarter), northern sky:
    lit limb on the right while waxing. Dark side cross-hatched; lit side white with stippled seas."""
    p = phase0to1 % 1.0
    u = _uid("mn", round(p, 4), size)
    k = max(1.0, 60.0 / size)
    lit = (1 - math.cos(2 * math.pi * p)) / 2
    waxing = p < .5
    c, r = 30.0, 21.0
    rx = abs(1 - 2 * lit) * r
    if waxing:
        limb, term = 1, (0 if lit < .5 else 1)
    else:
        limb, term = 0, (1 if lit < .5 else 0)
    lit_d = (f"M{_n(c)},{_n(c - r)}A{_n(r)},{_n(r)} 0 0 {limb} {_n(c)},{_n(c + r)}"
             f"A{_n(rx)},{_n(r)} 0 0 {term} {_n(c)},{_n(c - r)}Z")
    out = [_circ(c, c, 28.6, W1 * k, "#fff"), f"<g>{_beads(c, c, 26.4, 40, .8)}</g>", _circ(c, c, 24.2, W0 * k)]
    out.append(_circ(c, c, r, 0, f"url(#{u}-x)"))
    if lit > .995:
        shape = f'<circle cx="{_n(c)}" cy="{_n(c)}" r="{_n(r)}"/>'
        out.append(_circ(c, c, r, 0, "#fff", ' class="ei-lit" data-rx="0" data-side="full"'))
    elif lit > .005:
        shape = f'<path d="{lit_d}"/>'
        out.append(f'<path class="ei-lit" d="{lit_d}" fill="#fff" {K} stroke-width="{_n(W0 * k)}" '
                   f'data-rx="{_n(rx)}" data-side="{"r" if waxing else "l"}" data-gibbous="{int(lit >= .5)}"/>')
    else:
        shape = None
    if shape:
        u2 = r / 50
        seas = [(-14, -18, 13, 10), (10, -16, 9, 8), (16, 0, 10, 9), (-24, 6, 10, 16), (-6, 22, 9, 6), (24, 16, 6, 6)]
        m = "".join(f'<ellipse cx="{_n(c + a * u2)}" cy="{_n(c + b * u2)}" rx="{_n(cc * u2)}" ry="{_n(d * u2)}"/>' for a, b, cc, d in seas)
        craters = "".join(_circ(c + a * u2, c + b * u2, cc * u2, W0 * k, "#fff") for a, b, cc in
                          ((-6, 38, 3.4), (30, -22, 2.6)))
        out.append(f'<clipPath id="{u}c">{shape}</clipPath><g clip-path="url(#{u}c)"><g fill="url(#{u}-r)">{m}</g>{craters}</g>')
    out.append(_circ(c, c, r, W1 * k))
    defs = _defs(u, ("x", "r"), k)
    pct = round(lit * 100)
    name = ("new" if lit < .02 else "full" if lit > .98 else
            ("waxing " if waxing else "waning ") + ("crescent" if lit < .48 else "gibbous" if lit > .52 else "half"))
    return _svg(size, size, "".join(out), defs, f"moon {pct}% lit, {name}", vb="0 0 60 60")


# ------------------------------------------------------------------------------------------
# tide chart
# ------------------------------------------------------------------------------------------

def _tide_fn(pts):
    """Exact through every point. Alternating highs and lows (a tide table) are joined with the
    harmonic half-cosine; denser series with a monotone cubic (Fritsch-Carlson), so no overshoot."""
    ts = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(pts)
    alt = n >= 2 and all((ys[i + 1] - ys[i]) * (ys[i] - ys[i - 1]) < 0 for i in range(1, n - 1)) \
        and (ts[-1] - ts[0]) / (n - 1) >= 2.5 and all(ys[i + 1] != ys[i] for i in range(n - 1))
    if alt:
        def f(t):
            i = max(0, min(n - 2, next((j for j in range(n - 1) if t <= ts[j + 1]), n - 2)))
            uu = (t - ts[i]) / (ts[i + 1] - ts[i])
            return ys[i] + (ys[i + 1] - ys[i]) * (1 - math.cos(math.pi * uu)) / 2
        return f, True
    d = [(ys[i + 1] - ys[i]) / (ts[i + 1] - ts[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]
            s = a * a + b * b
            if s > 9:
                t3 = 3 / math.sqrt(s)
                m[i], m[i + 1] = t3 * a * d[i], t3 * b * d[i]

    def f(t):
        i = max(0, min(n - 2, next((j for j in range(n - 1) if t <= ts[j + 1]), n - 2)))
        h = ts[i + 1] - ts[i]
        s = (t - ts[i]) / h
        h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        return h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]
    return f, False


def _hour_label(h):
    h = int(round(h)) % 24
    return "12 am" if h == 0 else "noon" if h == 12 else f"{h % 12} {'am' if h < 12 else 'pm'}"


def tide_curve(points, now_hour, width=560, height=110):
    """Tide height through the day. points: [(hour, ft)], hours may run past 24 into tomorrow.
    Highs and lows labelled with height and time; the 'now' marker at now_hour."""
    pts = sorted((float(a), float(b)) for a, b in points)
    if len(pts) < 2:
        raise ValueError("tide_curve needs two or more points")
    u = _uid("td", tuple(pts), now_hour, width, height)
    W, H = width, height
    fn, alt = _tide_fn(pts)
    t0, t1 = pts[0][0], pts[-1][0]
    vmin, vmax = min(p[1] for p in pts), max(p[1] for p in pts)
    if vmax - vmin < .2:
        vmin, vmax = vmin - .1, vmax + .1
    top, bot, floor_y = 24.0, 68.0, H - 18.0
    ppf = (bot - top) / (vmax - vmin)
    cands = [.1, .2, .25, .5, 1, 2, 2.5, 5, 10, 20, 25, 50]
    ok = [s for s in cands if s * ppf >= 15 and len(_frange(vmin, vmax, s)) >= 2]
    step = ok[0] if ok else max((s for s in cands if len(_frange(vmin, vmax, s)) >= 2), default=.1)
    dec = _decimals(step)
    ticks = _frange(vmin, vmax, step)
    sc_w = max(_tw(_fmt(v, dec)) for v in ticks)
    L, R = 9 + sc_w + 7, W - 10

    def X(t):
        return L + (t - t0) / (t1 - t0) * (R - L)

    def Y(v):
        return bot - (v - vmin) * ppf

    # sample every given point exactly, plus a vertex every ~3 px between
    ts = set(p[0] for p in pts)
    nseg = max(2, int((R - L) / 3))
    ts.update(t0 + (t1 - t0) * i / nseg for i in range(nseg + 1))
    ts = sorted(ts)
    pk = {p[0]: p[1] for p in pts}
    curve = [(X(t), Y(pk.get(t, fn(t)))) for t in ts]
    cd = "M" + "L".join(f"{_n(x)},{_n(y)}" for x, y in curve)
    out = []
    # frame with corner blocks
    out.append(_p(f"M1,1H{_n(W - 1)}V{_n(H - 1)}H1Z", W1) + _p(f"M3.5,3.5H{_n(W - 3.5)}V{_n(H - 3.5)}H3.5Z", W0))
    for x, y in ((1, 1), (W - 1, 1), (1, H - 1), (W - 1, H - 1)):
        out.append(f'<rect x="{_n(x - 3)}" y="{_n(y - 3)}" width="6" height="6" fill="#fff" {K} stroke-width="{W0}"/>'
                   + _circ(x, y, 1.2, 0, "#000"))
    # hours: dotted hairlines, ticks
    span = t1 - t0
    lab_step = 3 if (R - L) / span * 3 >= 56 else 6 if (R - L) / span * 6 >= 56 else 12
    grid, tk = "", ""
    for h in range(math.ceil(t0), math.floor(t1) + 1):
        x = X(h)
        if h % lab_step == 0:
            grid += f"M{_n(x)},{_n(top - 8)}V{_n(floor_y)}"
            tk += f"M{_n(x)},{_n(floor_y)}V{_n(floor_y + 5)}"
        else:
            tk += f"M{_n(x)},{_n(floor_y)}V{_n(floor_y + 2.6)}"
    out.append(_p(grid, W0, extra=' stroke-dasharray="1 2.4"'))
    # height scale
    sct = ""
    for v in ticks:
        y = Y(v)
        sct += f"M{_n(L - 4)},{_n(y)}H{_n(L)}"
        out.append(_t(L - 7, y + 4.6, _fmt(v, dec), 13, "end", cls="ei-sc"))
    out.append(_t(L - 7, 13, "ft", 11, "end", italic=True))
    out.append(_p(f"M{_n(L)},{_n(top - 8)}V{_n(floor_y)}", W0) + _p(sct, W0))
    if vmin < 0 < vmax:
        out.append(_p(f"M{_n(L)},{_n(Y(0))}H{_n(R)}", W0, extra=' stroke-dasharray="4 2"'))
    # water: wave-hatched under the curve, the curve heavy on top with a white bead either side
    area = cd + f"L{_n(curve[-1][0])},{_n(floor_y)}L{_n(curve[0][0])},{_n(floor_y)}Z"
    out.append(f'<path d="{area}" fill="url(#{u}-w)"/>')
    out.append(f'<path d="{cd}" fill="none" stroke="#fff" stroke-width="4.4" stroke-linejoin="round"/>')
    out.append(f'<path class="ei-curve" d="{cd}" fill="none" {K} stroke-width="{W2}" stroke-linejoin="round"/>')
    out.append(_p(f"M{_n(L)},{_n(floor_y)}H{_n(R)}", W2) + _p(tk, W0))
    placed = []
    for h in range(math.ceil(t0), math.floor(t1) + 1):
        if h % lab_step == 0:
            s = _hour_label(h)
            w = _tw(s)
            x = min(max(X(h), L + w / 2), R - w / 2)
            if all(x - w / 2 > b + 8 or x + w / 2 < a - 8 for a, b in placed):
                placed.append((x - w / 2, x + w / 2))
                out.append(_t(x, H - 5.5, s, 13, cls="ei-hl"))
    has_now = t0 <= now_hour <= t1
    xn = X(now_hour) if has_now else -99
    if has_now:
        out.append(f'<path d="M{_n(xn)},{_n(top - 12)}V{_n(floor_y)}" stroke="#fff" stroke-width="4" fill="none"/>')
        out.append(f'<path class="ei-now" d="M{_n(xn)},{_n(top - 12)}V{_n(floor_y)}" {K} stroke-width="{W1}" fill="none" data-x="{_n(xn)}"/>')
    # highs and lows
    ys = [p[1] for p in pts]
    ext = []
    for i, (t, v) in enumerate(pts):
        if alt:
            nb = ys[i + 1] if i == 0 else ys[i - 1]
            ext.append((t, v, v > nb))
        elif 0 < i < len(pts) - 1:
            if v > ys[i - 1] and v >= ys[i + 1] or v >= ys[i - 1] and v > ys[i + 1]:
                ext.append((t, v, True))
            elif v < ys[i - 1] and v <= ys[i + 1] or v <= ys[i - 1] and v < ys[i + 1]:
                ext.append((t, v, False))
    boxes = []

    def hits(b):
        return any(not (b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3]) for o in boxes)
    for t, v, is_hi in ext:
        x, y = X(t), Y(v)
        s1 = f"{'High' if is_hi else 'Low'} {_fmt(v, 1)} ft"
        s2 = f" {_clock(t * 60, True)}"
        w = _tw(s1, 13, True) + _tw(s2, 13)
        ly = y - 7 if is_hi else y + 17.5
        opts = [min(max(x - w / 2, L + 3), R - w - 3), xn + 7, xn - 7 - w, x - w + 6, x - 6]
        opts = [o for o in opts if L + 3 <= o <= R - w - 3] or [min(max(x - w / 2, L + 3), R - w - 3)]
        lx = next((o for o in opts if not (o - 4 < xn < o + w + 4) and not hits((o - 3, ly - 13, o + w + 3, ly + 4))
                   and o - 10 <= x <= o + w + 10), opts[0])
        if not is_hi:
            out.append(f'<rect x="{_n(lx - 3)}" y="{_n(ly - 12.5)}" width="{_n(w + 6)}" height="17" fill="#fff" {K} stroke-width="{W0}"/>')
        out.append(_circ(x, y, 2.4, W1, "#fff", f' class="ei-ext" data-v="{v}"'))
        out.append(_t(lx, ly, f'<tspan font-weight="700">{s1}</tspan><tspan>{html.escape(s2)}</tspan>', 13, "start", halo=3 if is_hi else 0))
        boxes.append((lx - 3, ly - 13, lx + w + 3, ly + 4))
    # now: the point on the curve, and its reading wherever it fits
    if has_now:
        vn = fn(now_hour)
        yn = Y(vn)
        out.append(_circ(xn, yn, 4.2, W1, "#fff") + _circ(xn, yn, 1.6, 0, "#000"))
        s1, s2 = "Now", f" {_fmt(vn, 1)} ft"
        w = _tw(s1, 13, True) + _tw(s2, 13)
        cands = [(xn + 5, top - 10, 0), (xn - 5 - w, top - 10, 0), (xn + 8, yn - 8, 0), (xn - 8 - w, yn - 8, 0),
                 (xn + 8, floor_y - 5, 1), (xn - 8 - w, floor_y - 5, 1)]

        def free(cx, by, plate):
            b = (cx - 3, by - 12.5, cx + w + 3, by + 4)
            if b[0] < L + 2 or b[2] > R - 2 or b[1] < 4:
                return False
            if hits(b):
                return False
            if plate:
                return True
            near = [yy for xx, yy in curve if b[0] - 2 <= xx <= b[2] + 2]
            return not near or b[3] < min(near) - 2
        px, py, plate = next((c for c in cands if free(*c)), cands[4])
        if plate:
            out.append(f'<rect x="{_n(px - 3)}" y="{_n(py - 12.5)}" width="{_n(w + 6)}" height="17" fill="#fff" {K} stroke-width="{W0}"/>')
        out.append(_t(px, py, f'<tspan font-weight="700">{s1}</tspan><tspan>{html.escape(s2)}</tspan>', 13, "start", halo=0 if plate else 3))
    defs = _defs(u, ("w",))
    desc = "; ".join(f"{'high' if h_ else 'low'} {_fmt(v, 1)} ft at {_clock(t * 60, True)}" for t, v, h_ in ext)
    return _svg(W, H, "".join(out), defs, "tide: " + desc)


# ------------------------------------------------------------------------------------------
# gauge
# ------------------------------------------------------------------------------------------

def _gauge_angle(value, vmin, vmax):
    """Degrees clockwise from 12 o'clock; the scale runs -135 (vmin) to +135 (vmax)."""
    fr = (min(max(value, vmin), vmax) - vmin) / (vmax - vmin)
    return -135 + 270 * fr


def gauge(value, vmin, vmax, label, unit, size=150):
    """A brass-instrument dial: beaded bezel, railroad scale, Breguet needle, value in the cartouche."""
    if vmax <= vmin:
        raise ValueError("gauge: vmax must exceed vmin")
    u = _uid("ga", value, vmin, vmax, label, unit, size)
    S = size
    c = S / 2
    Ro = S / 2 - 1.5
    Rs = Ro - 11.5

    def P(ang, r):
        a = math.radians(ang)
        return c + r * math.sin(a), c - r * math.cos(a)

    span = vmax - vmin
    step = _nice_step(span, 5)
    if span / step > 7:
        step = _nice_step(span, 4)
    dec = _decimals(step)
    mant = round(step / 10 ** math.floor(math.log10(step)), 6)
    sub = step / (4 if mant == 2 else 5)
    out = []
    # bezel
    out.append(_circ(c, c, Ro, W2, "#fff") + f"<g>{_beads(c, c, Ro - 3.3, 60, .95)}</g>" + _circ(c, c, Ro - 5.8, W0))
    out.append(_circ(c, c, Ro - 7.2, W0))
    # railroad track: ink alternate sub-divisions
    r1, r2 = Rs - 3.2, Rs
    track = ""
    vals = _frange(vmin, vmax, sub)
    edges = sorted(set([vmin] + vals + [vmax]))
    for i in range(len(edges) - 1):
        a_, b_ = edges[i], edges[i + 1]
        idx = round((a_ - math.floor(vmin / sub) * sub) / sub)
        if idx % 2 == 0:
            A0, A1 = _gauge_angle(a_, vmin, vmax), _gauge_angle(b_, vmin, vmax)
            p0, p1, p2, p3 = P(A0, r2), P(A1, r2), P(A1, r1), P(A0, r1)
            track += (f"M{_n(p0[0])},{_n(p0[1])}A{_n(r2)},{_n(r2)} 0 0 1 {_n(p1[0])},{_n(p1[1])}"
                      f"L{_n(p2[0])},{_n(p2[1])}A{_n(r1)},{_n(r1)} 0 0 0 {_n(p3[0])},{_n(p3[1])}Z")
    out.append(f'<path d="{track}"/>')
    a0, a1 = P(-135, r2), P(135, r2)
    b0, b1 = P(-135, r1), P(135, r1)
    out.append(_p(f"M{_n(a0[0])},{_n(a0[1])}A{_n(r2)},{_n(r2)} 0 1 1 {_n(a1[0])},{_n(a1[1])}", W0)
               + _p(f"M{_n(b0[0])},{_n(b0[1])}A{_n(r1)},{_n(r1)} 0 1 1 {_n(b1[0])},{_n(b1[1])}", W0))
    # major ticks, half ticks, numerals
    mt, ht = "", ""
    nr = Rs - 15.5
    for v in _frange(vmin, vmax, step):
        A = _gauge_angle(v, vmin, vmax)
        p, q = P(A, Rs - 9), P(A, Rs + 1.5)
        mt += f"M{_n(p[0])},{_n(p[1])}L{_n(q[0])},{_n(q[1])}"
        x, y = P(A, nr)
        out.append(_t(x, y + 4.6, _fmt(v, dec), 13, cls="ei-sc", ls=None))
        out[-1] = out[-1].replace('class="ei-sc"', f'class="ei-sc" data-a="{_n(A)}"')
    for v in _frange(vmin, vmax, step / 2):
        if abs(v / step - round(v / step)) > 1e-6:
            A = _gauge_angle(v, vmin, vmax)
            p, q = P(A, Rs - 6), P(A, Rs)
            ht += f"M{_n(p[0])},{_n(p[1])}L{_n(q[0])},{_n(q[1])}"
    out.append(_p(mt, W2) + _p(ht, W1))
    # stop pins
    for A in (-141, 141):
        x, y = P(A, Rs - 2)
        out.append(_circ(x, y, 1.6, W0, "#fff"))
    # dial ornament: guilloche rosette under the boss, leaves flanking the cartouche
    out.append(_rosette(c, c, 6.2, 6.2, 14))
    # the cartouche: label and reading in the open quadrant at the bottom
    vy = c + Rs * (.86 if S >= 140 else .92)
    vs = f"{_fmt(value, 1 if abs(value) < 100 and abs(value - round(value)) > 1e-9 else 0)} {unit}".strip()
    if S >= 140:  # below 140 px the dial has no room for the label: give it in the heading
        out.append(_t(c, c + Rs * .5, label.upper(), 10.5, weight=600, ls=1.2, halo=2.5))
    vf = 17 if S >= 140 else 14
    vw = _tw(vs, vf, True)
    out.append(_p(f"M{_n(c - vw / 2 - 5)},{_n(vy - 15)}H{_n(c + vw / 2 + 5)}M{_n(c - vw / 2 - 5)},{_n(vy + 5)}H{_n(c + vw / 2 + 5)}", W0))
    out.append(_t(c, vy, vs, vf, weight=700, cls="ei-val"))
    out.append(_scroll(c - vw / 2 - 5, vy - 5, .7, True) + _scroll(c + vw / 2 + 5, vy - 5, .7, False))
    # needle (Breguet): tapered shaft, open moon near the tip, spear point; counterweight tail
    A = _gauge_angle(value, vmin, vmax)
    Ln = Rs - 2.5
    a = math.radians(A)
    ux, uy = math.sin(a), -math.cos(a)
    nx, ny = -uy, ux

    def Q(along, across):
        return c + ux * along + nx * across, c + uy * along + ny * across
    mr, mo = 3.3, Ln * .7
    pts = [Q(0, -2.2), Q(mo - mr - .2, -.9), Q(mo - mr - .2, .9), Q(0, 2.2)]
    shaft = "M" + "L".join(f"{_n(x)},{_n(y)}" for x, y in pts) + "Z"
    spear = [Q(mo + mr - .2, -1.1), Q(Ln - 6, -1.9), Q(Ln, 0), Q(Ln - 6, 1.9), Q(mo + mr - .2, 1.1)]
    spear_d = "M" + "L".join(f"{_n(x)},{_n(y)}" for x, y in spear) + "Z"
    tail = [Q(0, -1.6), Q(-12, -1.2), Q(-12, 1.2), Q(0, 1.6)]
    tail_d = "M" + "L".join(f"{_n(x)},{_n(y)}" for x, y in tail) + "Z"
    tip = Q(Ln, 0)
    mc = Q(mo, 0)
    tw_ = Q(-14.5, 0)
    out.append(f'<g class="ei-needle" data-tipx="{_n(tip[0])}" data-tipy="{_n(tip[1])}" data-cx="{_n(c)}" data-cy="{_n(c)}">'
               f'<path d="{shaft}{spear_d}{tail_d}" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>'
               f'<path d="{shaft}{spear_d}{tail_d}"/>'
               + _circ(mc[0], mc[1], mr, 1.5) + _circ(tw_[0], tw_[1], 3.2, 1.3, "#fff") + "</g>")
    out.append(_circ(c, c, 5.4, W1, "#000") + _circ(c, c, 2.2, W0, "#fff") + _circ(c, c, .7, 0, "#000"))
    defs = ""
    return _svg(S, S, "".join(out), defs, f"{label}: {vs} (scale {_fmt(vmin)} to {_fmt(vmax)})")


# ------------------------------------------------------------------------------------------
# river staff
# ------------------------------------------------------------------------------------------

_HERON = ("M14,20C16,16 24,15 29,19C32,21 34,25 35.5,28.5C30,27.4 24,27 19,26C15.4,25 13.4,23 14,20Z")


def _heron(x, y, s, u, k=1.0):
    """A great blue heron standing, facing left; (x, y) is where its feet meet the water."""
    dx, dy = x - 22 * s, y - 37 * s
    body = _p(_xf(_HERON, dx, dy, s), W0 * k, "#fff") + _p(_xf("M17,22C21,19 27,19 31,22.4C32.6,24 33.8,26 35,28C30,27 24,26.6 19.4,25.4Z", dx, dy, s), 0, f"url(#{u}-h)").replace(f'{K} stroke-width="0"', "")
    wing = _p(_xf("M19,20.6C23,19 28,20 31,23", dx, dy, s), W0 * k)
    neck = _p(_xf("M15.4,19.6C12.6,16 16.6,12.6 15.4,8.6C14.8,6.8 13.6,5.6 12.6,5.4", dx, dy, s), max(1.5 * s, W0 * k), extra=' stroke-linecap="round"')
    head = _p(_xf("M10.4,4.6C11.4,3.4 13.8,3.6 14.2,5.2C14.2,6.2 13.2,6.8 12,6.6Z", dx, dy, s), W0 * k, "#000")
    beak = f'<path d="{_xf("M11,4.9L2.6,6.4L11,6.2Z", dx, dy, s)}"/>'
    plume = _p(_xf("M12.4,4.2C14.6,2.8 17.4,2.8 19.6,3.6", dx, dy, s), W0 * k)
    legs = _p(_xf("M22,26.2L21,37M24.2,26.6L25.4,37", dx, dy, s), W0 * k * 1.3)
    art = body + wing + neck + head + beak + plume + legs
    halo = re.sub(r'stroke-width="[\d.]+"', 'stroke-width="3"', neck + legs + plume).replace('stroke="#000"', 'stroke="#fff"')
    halo += _p(_xf(_HERON, dx, dy, s), 3, "#fff").replace('stroke="#000"', 'stroke="#fff"')
    return halo + art


def _reeds(x0, base, n, hmax, u, k=1.0, seed=0):
    out = ""
    for i in range(n):
        x = x0 + i * 3.1
        h = hmax * (.62 + .38 * ((i * 7 + seed) % 5) / 4)
        lean = ((i * 3 + seed) % 5 - 2) * .9
        out += _p(f"M{_n(x)},{_n(base)}C{_n(x + lean * .3)},{_n(base - h * .4)} {_n(x + lean)},{_n(base - h * .7)} {_n(x + lean * 1.4)},{_n(base - h)}", W0 * k)
        if i % 2 == 0:
            ex, ey = x + lean * 1.2, base - h * .82
            out += f'<ellipse cx="{_n(ex)}" cy="{_n(ey)}" rx="1.25" ry="3.2"/>'
        else:
            out += _p(f"M{_n(x)},{_n(base - h * .2)}C{_n(x + 2)},{_n(base - h * .45)} {_n(x + 4.5)},{_n(base - h * .55)} {_n(x + 6)},{_n(base - h * .5)}", W0 * k)
    return out


def river_staff(ft, flood_ft, width=70, height=180):
    """A staff gauge on its post in the river: feet marked up the board, the water at ft,
    flood stage ruled across, a heron and reeds at the foot."""
    u = _uid("rs", ft, flood_ft, width, height)
    W, H = width, height
    smin = min(0.0, math.floor(ft))
    need = max(flood_ft * 1.12, ft * 1.08, smin + 4)
    y0, y1 = 30.0, H - 42.0
    for stp in (1, 2, 5, 10, 20, 50):
        smax = math.ceil(need / stp) * stp
        if stp * (y1 - y0) / (smax - smin) >= 16:
            break
    ppf = (y1 - y0) / (smax - smin)

    def Y(v):
        return y1 - (v - smin) * ppf
    minor = next(m for m in (.1, .2, .5, 1, 2, 5, 10) if m * ppf >= 2.4 and abs(stp / m - round(stp / m)) < 1e-9)
    bx0, bx1 = round(W * .4), round(W * .4) + 15
    out = []
    # the reading
    out.append(_t(W / 2, 17, f"{_fmt(ft, 1)} ft", 15, weight=700))
    out.append(_p(f"M{_n(W / 2 - 22)},{_n(22.5)}H{_n(W / 2 + 22)}", W0) + _star4(W / 2, 22.5, 2.2))
    # post and finial
    out.append(_p(f"M{_n((bx0 + bx1) / 2 - 2.5)},{_n(y0 - 3)}V{_n(H - 6)}M{_n((bx0 + bx1) / 2 + 2.5)},{_n(y0 - 3)}V{_n(H - 6)}", W0))
    # board: E-pattern blocks on the left half, ticks on the right half
    out.append(f'<rect x="{bx0}" y="{_n(Y(smax) - 3)}" width="{bx1 - bx0}" height="{_n(y1 - Y(smax) + 3)}" fill="#fff" {K} stroke-width="{W1}"/>')
    out.append(_p(f"M{bx0 - 2},{_n(Y(smax) - 3)}H{bx1 + 2}L{_n((bx0 + bx1) / 2)},{_n(Y(smax) - 8.5)}Z", W1, "#fff")
               + _circ((bx0 + bx1) / 2, Y(smax) - 10.5, 1.6, W0, "#000"))
    blocks, ticks = "", ""
    vs = _frange(smin, smax, minor)
    for i, v in enumerate(vs[:-1]):
        if round((v - smin) / minor) % 2 == 0:
            blocks += f"M{bx0},{_n(Y(v))}H{_n(bx0 + 6)}V{_n(Y(v + minor))}H{bx0}Z"
    for v in vs:
        major = abs(v / stp - round(v / stp)) < 1e-9
        ticks += f"M{_n(bx0 + 6)},{_n(Y(v))}H{_n(bx1 if major else bx1 - 4)}"
    out.append(f'<path d="{blocks}"/>' + _p(ticks, W0))
    out.append(_p("".join(f"M{bx0 - 3},{_n(Y(v))}H{bx1}" for v in _frange(smin, smax, stp)), W1))
    for v in _frange(smin, smax, stp):
        out.append(_t(bx0 - 5, Y(v) + 4.6, _fmt(v, 0), 13, "end", halo=3.2, cls="ei-sc"))
    # flood stage
    yf = Y(flood_ft)
    out.append(_p(f"M{bx0 - 3},{_n(yf)}H{W - 3}", W1, extra=' stroke-dasharray="3 1.6" class="ei-flood"'))
    # water: wave-hatched from the level down, the level line heavy with a pointer
    yl = max(Y(smax) - 2, min(y1 + 30, Y(ft)))
    out.append(f'<rect x="2" y="{_n(yl)}" width="{W - 4}" height="{_n(H - 4 - yl)}" fill="url(#{u}-w)"/>')
    out.append(f'<path d="M2,{_n(yl)}Q5,{_n(yl - 1.6)} 8,{_n(yl)}T14,{_n(yl)}T20,{_n(yl)}H{W - 20}Q{W - 17},{_n(yl - 1.6)} {W - 14},{_n(yl)}T{W - 8},{_n(yl)}T{W - 2},{_n(yl)}" '
               f'fill="none" {K} stroke-width="{W2}" class="ei-level" data-y="{_n(Y(ft))}"/>')
    out.append(f'<path d="M{bx1 + 1.5},{_n(yl)}l6,-4v8Z"/>')
    # re-ink the numerals below the water so they stay legible (halo already white)
    # flood legend, kept clear of the water line
    fs = _fmt(flood_ft, 1 if flood_ft != int(flood_ft) else 0)
    if yl < yf and yf - yl < 30:          # water above flood and close: legend below the flood line
        fl = (yf + 12, yf + 26)
    elif yl >= yf and yl - yf < 30:       # water just below flood: legend above it
        fl = (yf - 17, yf - 4)
    else:
        fl = (yf - 4, yf + 14)
    out.append(_t(W - 3, fl[0], "flood", 10.5, "end", italic=True, halo=3))
    out.append(_t(W - 3, fl[1], fs, 13, "end", weight=700, halo=3))
    # the foot: a bank with a heron on it, reeds in the shallows, a stippled bed
    base = H - 5
    bank = (f"M{W * .52:.1f},{base}C{W * .6:.1f},{base - 6} {W * .7:.1f},{base - 9} {W - 2},{base - 9.5}V{base}Z")
    out.append(_p(bank, W0, "#fff") + f'<path d="{bank}" fill="url(#{u}-s2)"/>')
    out.append(_heron(W - 15.5, base - 8.6, .8, u))
    out.append(_reeds(5, base, 5, 22, u, seed=1))
    out.append(f'<rect x="2" y="{base}" width="{W - 4}" height="3" fill="url(#{u}-s)"/>' + _p(f"M2,{base}H{W - 2}", W0))
    out.append(_p(f"M1,1H{W - 1}V{H - 1}H1Z", W1))
    defs = _defs(u, ("w", "h", "s", "s2"))
    return _svg(W, H, "".join(out), defs, f"river {_fmt(ft, 1)} ft, flood stage {_fmt(flood_ft, 1)} ft")


# ------------------------------------------------------------------------------------------
# bar chart
# ------------------------------------------------------------------------------------------

def bar_chart(values, labels, width=560, height=130, highlight=None, fmt=None):
    """Engraved bars: diagonal-hatched, the highlighted bar cross-hatched with a bold value; a fine
    dotted scale with numerals at left; every bar's value above it when there is room.
    fmt: optional callable(value) -> str for the value labels."""
    vals = [float(v) for v in values]
    labels = [str(s) for s in labels]
    if len(vals) != len(labels) or not vals:
        raise ValueError("bar_chart: values and labels must be the same non-zero length")
    u = _uid("bc", tuple(vals), tuple(labels), width, height, highlight)
    W, H = width, height
    vmax, vmin = max(vals + [0.0]), min(vals + [0.0])
    top, base = 22.0, H - 24.0
    best = None
    span0 = max(vmax - vmin, 1e-9)
    mag = 10 ** math.floor(math.log10(span0))
    for st in [m * mag * f for f in (.1, 1, 10) for m in (1, 2, 2.5, 5)]:
        h_, l_ = math.ceil(vmax / st - 1e-9) * st, math.floor(vmin / st + 1e-9) * st
        if h_ == l_:
            h_ = l_ + st
        nint = round((h_ - l_) / st)
        room = (vmin - l_) * (base - top) / (h_ - l_) if vmin < 0 else 99
        if 2 <= nint <= 5 and (base - top) / nint >= 16 and room >= 15:
            cand = (h_ - l_, -st, st, h_, l_)
            best = min(best, cand) if best else cand
    if best is None:
        st = _nice_step(span0, 3)
        best = (0, 0, st, math.ceil(vmax / st - 1e-9) * st or st, math.floor(vmin / st + 1e-9) * st)
    step, hi, lo = best[2], best[3], best[4]
    dec = _decimals(step)
    if fmt is None:
        vd = 0 if all(abs(v - round(v)) < 1e-9 for v in vals) else (1 if max(abs(v) for v in vals) < 100 else 0)
        fmt = lambda v: _fmt(v, vd)  # noqa: E731
    sc = [_fmt(v, dec) for v in _frange(lo, hi, step)]
    L = 8 + max(_tw(s) for s in sc) + 6
    R = W - 6

    def Y(v):
        return base - (v - lo) / (hi - lo) * (base - top)
    y_zero = Y(0)
    n = len(vals)
    slot = (R - L) / n
    bw = max(3.0, min(slot * .62, 46))
    out = []
    # scale and gridlines
    grid = ""
    for v in _frange(lo, hi, step):
        y = Y(v)
        if abs(v) > 1e-12:
            grid += f"M{_n(L)},{_n(y)}H{_n(R)}"
        out.append(_t(L - 6, y + 4.6, _fmt(v, dec), 13, "end", cls="ei-sc"))
    out.append(_p(grid, W0, extra=' stroke-dasharray="1 2.6"'))
    out.append(_p(f"M{_n(L)},{_n(top - 6)}V{_n(base)}", W0)
               + _p("".join(f"M{_n(L - 3.5)},{_n(Y(v))}H{_n(L)}" for v in _frange(lo, hi, step)), W0))
    # bars
    hl = highlight if highlight is None or highlight >= 0 else n + highlight
    vlab = [fmt(v) for v in vals]
    fit_all = all(_tw(s, 13, True) <= slot - 2 for s in vlab)
    show = set(range(n)) if fit_all else {i for i in (hl, vals.index(max(vals)), n - 1) if i is not None}
    lw = max(_tw(s) for s in labels)
    every = 1
    while lw > slot * every - 4 and every < n:
        every += 1
    for i, v in enumerate(vals):
        cx = L + slot * (i + .5)
        x = cx - bw / 2
        y = Y(v)
        yt, yb = min(y, y_zero), max(y, y_zero)
        tone = "x" if i == hl else "h"
        out.append(f'<rect class="ei-bar" x="{_n(x)}" y="{_n(yt)}" width="{_n(bw)}" height="{_n(yb - yt)}" '
                   f'fill="url(#{u}-{tone})" {K} stroke-width="{W1 if i != hl else W2}" data-v="{v}"/>')
        if bw >= 9 and yb - yt > 3:
            # engraved highlight: a white fillet down the lit edge
            out.append(f'<path d="M{_n(x + 2.2)},{_n(yt + 1.4)}V{_n(yb - .8)}" stroke="#fff" stroke-width="1.6" fill="none"/>')
        if i in show and not (v == 0 and n > 8 and i != hl):
            ly = yt - 5 if v >= 0 else yb + 15
            out.append(_t(cx, ly, vlab[i], 13, weight=700 if i == hl else 500, halo=3 if i != hl else 0, cls="ei-vl"))
        if i % every == 0 or i == hl:
            out.append(_t(cx, H - 6.5, labels[i], 13, weight=700 if i == hl else None, italic=False))
    # base: plinth rule pair
    out.append(_p(f"M{_n(L - 4)},{_n(y_zero)}H{_n(R + 2)}", W2) + _p(f"M{_n(L - 4)},{_n(y_zero + 2.8)}H{_n(R + 2)}", W0))
    if hl is not None:
        cx = L + slot * (hl + .5)
        tw = _tw(labels[hl], 13, True)
        out.append(_p(f"M{_n(cx - tw / 2 - 2)},{_n(H - 2.2)}H{_n(cx + tw / 2 + 2)}", W0))
    defs = _defs(u, ("h", "x"))
    return _svg(W, H, "".join(out), defs, "; ".join(f"{a} {b}" for a, b in zip(labels, vlab)))


# ------------------------------------------------------------------------------------------
# self-test: measure the drawn geometry against the inputs
# ------------------------------------------------------------------------------------------

def _attr(el, name):
    m = re.search(rf'\b{name}="([^"]*)"', el)
    return m.group(1) if m else None


def _selftest():
    import xml.dom.minidom as _md
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    def wellformed(svg, what):
        try:
            _md.parseString(svg)
        except Exception as e:  # noqa: BLE001
            fails.append(f"{what}: not well-formed XML ({e})")
        check("transform" not in svg, f"{what}: has a transform")
        check("opacity" not in svg and "Gradient" not in svg, f"{what}: grey tone")
        for sw in re.findall(r'stroke-width="([\d.]+)"', svg):
            if 0 < float(sw) < .6 - 1e-9:
                fails.append(f"{what}: stroke {sw} < .6")
                break
        for fs in re.findall(r'<text[^>]*font-size="([\d.]+)"[^>]*>([^<]*\d[^<]*)</text>', svg):
            if float(fs[0]) < 13:
                fails.append(f"{what}: number {fs[1]!r} at {fs[0]}px")
        check(len(svg.encode()) < 25000, f"{what}: {len(svg)} bytes")

    def scale_fit(svg, axis):
        """Fit value -> coordinate from the drawn scale numerals (independent of the drawing code)."""
        pts = []
        for el in re.findall(r"<text[^>]*ei-sc[^>]*>[^<]*</text>", svg):
            v = float(re.search(r">([^<]*)<", el).group(1).replace("−", "-").replace(",", ""))
            c = float(_attr(el, axis)) - (4.6 if axis == "y" else 0)
            pts.append((v, c))
        (v0, c0), (v1, c1) = pts[0], pts[-1]
        return lambda v: c0 + (v - v0) * (c1 - c0) / (v1 - v0)

    # gauge: needle angle
    for val, a, b in ((4.2, 0, 8), (0, 0, 8), (8, 0, 8), (17, 0, 40), (12.3, 0, 30), (-3, 0, 10), (55, 0, 50)):
        s = gauge(val, a, b, "Solar", "kW")
        wellformed(s, f"gauge {val}")
        g = re.search(r'<g class="ei-needle"[^>]*>', s).group(0)
        tx, ty, cx, cy = (float(_attr(g, k)) for k in ("data-tipx", "data-tipy", "data-cx", "data-cy"))
        ang = math.degrees(math.atan2(tx - cx, -(ty - cy)))
        want = -135 + 270 * (min(max(val, a), b) - a) / (b - a)
        check(abs(ang - want) < .25, f"gauge {val} in [{a},{b}]: needle {ang:.2f} deg, want {want:.2f}")
        for el in re.findall(r"<text[^>]*ei-sc[^>]*>[^<]*</text>", s):
            v = float(re.search(r">([^<]*)<", el).group(1).replace("−", "-"))
            check(abs(float(_attr(el, "data-a")) - (-135 + 270 * (v - a) / (b - a))) < .01, f"gauge tick {v}")
        check(f">{_fmt(val, 1 if abs(val - round(val)) > 1e-9 else 0)} kW<" in s, f"gauge {val}: readout")

    # bar chart: bar tops against the drawn scale
    for vals, hl in (([3.1, 4.6, 0.8, 5.9, 2.2, 6.4, 4.0], 6), ([12, 30, 25, 41, 8], None), ([1.2] * 24, 3),
                     ([-2, 3.5, 7, -1.2], 1)):
        s = bar_chart(vals, [f"d{i}" for i in range(len(vals))], highlight=hl)
        wellformed(s, f"bars {vals[:3]}")
        Yv = scale_fit(s, "y")
        for el in re.findall(r"<rect class=\"ei-bar\"[^>]*>", s):
            v = float(_attr(el, "data-v"))
            y, h = float(_attr(el, "y")), float(_attr(el, "height"))
            top = y if v >= 0 else y + h
            check(abs(top - Yv(v)) < .02 and abs((y + h if v >= 0 else y) - Yv(0)) < .02, f"bar {v}: top {top} want {Yv(v):.2f}")

    # sun dial: sun on the arc at the right fraction of daylight
    for sr, ss, nw in (("7:04", "16:48", "10:30"), ("6:12 AM", "5:58 PM", "12:05 PM"), ("5:21", "21:02", "13:11"),
                       ("7:04", "16:48", "7:04"), ("7:04", "16:48", "16:48"), ("7:04 am", "4:48 pm", "6:00 am"),
                       ("7:04", "16:48", "19:30")):
        s = sun_dial(sr, ss, nw)
        wellformed(s, f"sun {nw}")
        g = re.search(r'<g class="ei-sun"[^>]*>', s) or re.search(r'<g clip-path[^>]*class="ei-sun"[^>]*>', s)
        x, y = float(_attr(g.group(0), "data-cx")), float(_attr(g.group(0), "data-cy"))
        rs = re.search(r'd="M([\d.]+),([\d.]+)V[\d.]+M([\d.]+),', re.search(r'<path d="[^"]*" [^>]*class="ei-rs"', s).group(0))
        xl, xr = float(rs.group(1)), float(rs.group(3))
        hy = float(rs.group(2)) + 8
        c, R = (xl + xr) / 2, (xr - xl) / 2
        a, b, m = _parse_time(sr), _parse_time(ss), _parse_time(nw)
        fr = (m - a) / (b - a)
        if 0 <= fr <= 1:
            got = 1 - math.atan2(hy - y, x - c) / math.pi
            check(abs(got - fr) < .002 and abs(math.hypot(x - c, y - hy) - R) < .05, f"sun {nw}: at {got:.4f} want {fr:.4f}")
        else:
            check(abs(y - hy) < .05 and abs(x - (xl if fr < 0 else xr)) < .05, f"sun {nw}: night marker misplaced")
        check(f">{_clock(a)}<" in s and f">{_clock(b)}<" in s, f"sun {nw}: rise/set labels")
        for el in re.findall(r"<text[^>]*ei-hr[^>]*>[^<]*</text>", s):  # each hour numeral sits on its hour line
            hh = int(re.search(r">(\d+)<", el).group(1))
            ex, ey = float(_attr(el, "x")), float(_attr(el, "y")) - 4.6
            ang = 1 - math.atan2(hy - ey, ex - c) / math.pi
            mins = a + ang * (b - a)
            check(abs(((mins / 60 - hh) % 12 + 6) % 12 - 6) < .02, f"sun hour numeral {hh} misplaced ({mins / 60:.3f})")

    # thermometer: mercury top on the scale
    for now, lo, hi in ((52, 44, 61), (-4, -12, 9), (98, 71, 104), (33, 33, 33), (61.4, 48.2, 66.9)):
        s = thermometer(now, lo, hi)
        wellformed(s, f"thermo {now}")
        Yv = scale_fit(s, "y")
        el = re.search(r'<rect class="ei-merc"[^>]*>', s).group(0)
        check(abs(float(_attr(el, "y")) - Yv(now)) < .02, f"thermo {now}: mercury at {_attr(el, 'y')} want {Yv(now):.2f}")
        rg = re.search(r'<path d="M[\d.]+,([\d.]+)H[\d.]+V([\d.]+)H', s)
        check(abs(float(rg.group(1)) - Yv(hi)) < .02 and abs(float(rg.group(2)) - Yv(lo)) < .02, f"thermo {now}: range bracket")

    # moon: lit fraction and side from the drawn terminator
    for p in (0, .03, .125, .25, .37, .5, .62, .75, .88, .97):
        s = moon_phase(p)
        wellformed(s, f"moon {p}")
        want = (1 - math.cos(2 * math.pi * p)) / 2
        el = re.search(r'<[a-z]+[^>]*class="ei-lit"[^>]*>', s)
        if want < .005:
            check(el is None, f"moon {p}: should be dark")
            continue
        el = el.group(0)
        if _attr(el, "data-side") == "full":
            check(want > .995, f"moon {p}: drawn full")
            continue
        rx = float(_attr(el, "data-rx"))
        d = _attr(el, "d")
        flags = re.findall(r"A[\d.]+,[\d.]+ 0 0 (\d) ", d)
        limb_right = flags[0] == "1"
        r = 21.0
        # lit area = half disc +/- half ellipse; gibbous when the terminator bulges toward the dark limb
        gib = flags[1] == ("1" if limb_right else "0")
        got = (.5 + rx / r / 2) if gib else (.5 - rx / r / 2)
        check(abs(got - want) < .002, f"moon {p}: lit {got:.3f} want {want:.3f}")
        check(limb_right == (p % 1 < .5), f"moon {p}: lit on the wrong side")

    # tide: curve through every point, extremes labelled, now marker on the hour axis
    tides = [(-0.4, 2.1), (5.2, 8.4), (11.6, -0.6), (17.9, 7.1), (23.8, 1.9), (29.9, 8.0)]
    hourly = [(h, 4.5 + 3.6 * math.sin((h - 2.5) / 12.42 * 2 * math.pi)) for h in range(0, 25)]
    for pts, now in ((tides, 8.25), (hourly, 14.5), (tides[1:4], 9.0)):
        s = tide_curve(pts, now)
        wellformed(s, f"tide {len(pts)}")
        Yv = scale_fit(s, "y")
        d = re.search(r'class="ei-curve" d="([^"]*)" fill="none" stroke="#000"', s).group(1)
        verts = [tuple(map(float, xy.split(","))) for xy in re.findall(r"[\d.]+,[\d.]+", d)]
        x0, x1 = verts[0][0], verts[-1][0]
        t0, t1 = pts[0][0], pts[-1][0]
        Xt = lambda t: x0 + (t - t0) / (t1 - t0) * (x1 - x0)  # noqa: E731
        for t, v in pts:
            check(any(abs(x - Xt(t)) < .01 and abs(y - Yv(v)) < .04 for x, y in verts), f"tide: curve misses ({t}, {v})")
        el = re.search(r'class="ei-now"[^>]*data-x="([\d.]+)"', s)
        check(abs(float(el.group(1)) - Xt(now)) < .006, "tide: now marker misplaced")
        if pts is tides:
            for t, v in tides:
                kind = "High" if v > 5 else "Low"
                check(f">{kind} {_fmt(v, 1)} ft<" in s and _clock(t * 60, True) in s, f"tide: {kind} {v} label")

    # river staff: water level on the board's scale
    for ft, fl in ((5.2, 18), (11.7, 15), (19.3, 18), (-0.8, 12), (2.4, 6.5)):
        s = river_staff(ft, fl)
        wellformed(s, f"river {ft}")
        Yv = scale_fit(s, "y")
        el = re.search(r'class="ei-level" data-y="([\d.]+)"', s)
        check(abs(float(el.group(1)) - Yv(ft)) < .02, f"river {ft}: level {el.group(1)} want {Yv(ft):.2f}")
        fy = re.search(r'd="M[\d.]+,([\d.]+)H[\d.]+" fill="none" stroke="#000" stroke-width="1" stroke-dasharray="3 1.6" class="ei-flood"', s)
        check(abs(float(fy.group(1)) - Yv(fl)) < .02, f"river {ft}: flood line")

    for kind in WEATHER_KINDS:
        for sz in (56, 40, 80):
            wellformed(weather_glyph(kind, sz), f"glyph {kind} {sz}")
    return fails


if __name__ == "__main__":
    fails = _selftest()
    if fails:
        print("FAIL")
        for f in fails:
            print("  " + f)
        raise SystemExit(1)
    print("self-test passed: needles, bars, sun, mercury, moon, tide and river all match their inputs")
