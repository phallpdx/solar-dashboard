"""Morning Edition vignettes: bulino line engravings for the Kindle morning paper.

Stdlib only. MORNING_VIGNETTES maps a section key to a complete <svg> (viewBox 0 0 120 80): an engraved
scene inside an oval or cartouche medallion with a beaded or roped rim. Tone is made only with lines and
dots (no grey fills, gradients or opacity) and no element carries a transform attribute: every placed or
mirrored motif is baked into its coordinates. Every id in a vignette starts with its key.

The drawing vocabulary is the Evening Edition's (solar/kindle_evening.py on main): the same three line
weights (W0 .6 hairline, W1 1 rule, W2 1.6 heavy rule), the same tones (stipple light and mid, 45-degree
hatch, cross-hatch, dense hatch, pearl waves), the same heavy-ring-and-dotted-hairline rims and rope band,
and its motifs (acanthus leaf, kanok flame, four-point star, Douglas fir, Mount Hood, river hairlines, the
dog's head, the lotus, the St. Johns towers) are reused here, baked to place.

ornaments: fleuron(seed), rule(width, seed), drop_cap_frame(letter, seed, size=64).
"""
import math
import random
import re

# E-ink grid. The plates are tuned to display at 200 CSS px wide on the Paperwhite (DPR 2), so one
# unit is 5/3 CSS px: .3 u = 0.5 CSS (1 device px), .6 u = 1 CSS, .9 u = 1.5 CSS, 1.2 u = 2 CSS.
# Strokes snap to those widths (see _snap); hatch tiles are 1.2 or 1.8 u (2 or 3 CSS, whole device
# pixels); ruled grounds keep a fixed pitch and make tone with line width (bulino), never pitch.
DISPLAY_W = 200
W0, W1, W2 = .6, .9, .9
HL = .3  # the 0.5 CSS hairline: one device pixel
G = .86  # the scene is engraved at full plate size and set into the medallion at this scale
K = 'stroke="#000"'
CX, CY = 60, 40


def n(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---- affine baking ----------------------------------------------------------------------------

class Aff:
    def __init__(self, a=1, b=0, c=0, d=1, e=0, f=0):
        self.m = (a, b, c, d, e, f)

    def __mul__(self, o):  # self after o
        a, b, c, d, e, f = self.m
        A, B, C, D, E, F = o.m
        return Aff(a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)

    @staticmethod
    def T(x, y):
        return Aff(1, 0, 0, 1, x, y)

    @staticmethod
    def S(sx, sy=None):
        return Aff(sx, 0, 0, sx if sy is None else sy, 0, 0)

    @staticmethod
    def R(deg, cx=0, cy=0):
        r = math.radians(deg)
        co, si = math.cos(r), math.sin(r)
        return Aff.T(cx, cy) * Aff(co, si, -si, co, 0, 0) * Aff.T(-cx, -cy)

    def pt(self, x, y):
        a, b, c, d, e, f = self.m
        return a * x + c * y + e, b * x + d * y + f

    @property
    def det(self):
        a, b, c, d = self.m[:4]
        return a * d - b * c

    @property
    def s(self):
        return math.sqrt(abs(self.det))

    @property
    def axis(self):
        return abs(self.m[1]) < 1e-9 and abs(self.m[2]) < 1e-9


def place(x, y, s=1.0, rot=0, flip=False, sy=None):
    """translate(x,y) rotate(rot) scale(+-s, sy)"""
    return Aff.T(x, y) * Aff.R(rot) * Aff.S(-s if flip else s, s if sy is None else sy)


_TOK = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?")
_NARGS = dict(M=2, L=2, H=1, V=1, C=6, S=4, Q=4, T=2, A=7, Z=0)


def parse_path(d):
    """Absolute M L C Q A Z segments."""
    toks = _TOK.findall(d)
    out, i, cmd = [], 0, None
    x = y = sx = sy = 0.0
    lc = lq = None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                out.append(("Z", []))
                x, y = sx, sy
                lc = lq = None
                continue
        up = cmd.upper()
        k = _NARGS[up]
        a = [float(v) for v in toks[i:i + k]]
        i += k
        rel = cmd.islower()
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if up == "M":
            x, y = a[0] + ox, a[1] + oy
            sx, sy = x, y
            out.append(("M", [x, y]))
            cmd = "l" if rel else "L"
            lc = lq = None
        elif up in "LHV":
            if up == "H":
                x = a[0] + (x if rel else 0)
            elif up == "V":
                y = a[0] + (y if rel else 0)
            else:
                x, y = a[0] + ox, a[1] + oy
            out.append(("L", [x, y]))
            lc = lq = None
        elif up == "C":
            p = [a[0] + ox, a[1] + oy, a[2] + ox, a[3] + oy, a[4] + ox, a[5] + oy]
            out.append(("C", p))
            lc = (p[2], p[3])
            lq = None
            x, y = p[4], p[5]
        elif up == "S":
            c1 = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
            p = [c1[0], c1[1], a[0] + ox, a[1] + oy, a[2] + ox, a[3] + oy]
            out.append(("C", p))
            lc = (p[2], p[3])
            lq = None
            x, y = p[4], p[5]
        elif up == "Q":
            p = [a[0] + ox, a[1] + oy, a[2] + ox, a[3] + oy]
            out.append(("Q", p))
            lq = (p[0], p[1])
            lc = None
            x, y = p[2], p[3]
        elif up == "T":
            c1 = (2 * x - lq[0], 2 * y - lq[1]) if lq else (x, y)
            p = [c1[0], c1[1], a[0] + ox, a[1] + oy]
            out.append(("Q", p))
            lq = c1
            lc = None
            x, y = p[2], p[3]
        elif up == "A":
            p = a[:5] + [a[5] + ox, a[6] + oy]
            out.append(("A", p))
            lc = lq = None
            x, y = p[5], p[6]
    return out


def _ell_xf(A, rx, ry, phi):
    """The image of an ellipse (rx, ry, phi degrees) under A's linear part: (rx, ry, phi)."""
    a, b, c, d = A.m[:4]
    r = math.radians(phi)
    co, si = math.cos(r), math.sin(r)
    # M = L . R(phi) . diag(rx, ry)
    m00, m01 = (a * co + c * si) * rx, (a * -si + c * co) * ry
    m10, m11 = (b * co + d * si) * rx, (b * -si + d * co) * ry
    e00, e01, e11 = m00 * m00 + m01 * m01, m00 * m10 + m01 * m11, m10 * m10 + m11 * m11
    tr, df = e00 + e11, math.sqrt(max(0.0, (e00 - e11) ** 2 + 4 * e01 * e01))
    l1, l2 = (tr + df) / 2, max(0.0, (tr - df) / 2)
    ang = .5 * math.degrees(math.atan2(2 * e01, e00 - e11))
    return math.sqrt(l1), math.sqrt(l2), ang


def xf_path(d, A):
    out = []
    for c, p in parse_path(d):
        if c == "Z":
            out.append("Z")
        elif c == "A":
            rx, ry, ang = _ell_xf(A, p[0], p[1], p[2])
            sw = int(p[4]) if A.det > 0 else 1 - int(p[4])
            x, y = A.pt(p[5], p[6])
            out.append(f"A{n(rx)},{n(ry)} {n(ang)} {int(p[3])} {sw} {n(x)},{n(y)}")
        else:
            q = []
            for i in range(0, len(p), 2):
                x, y = A.pt(p[i], p[i + 1])
                q.append(f"{n(x)},{n(y)}")
            out.append(c + " ".join(q))
    return "".join(out)


def ell_d(cx, cy, rx, ry, rot=0.0):
    r = math.radians(rot)
    dx, dy = rx * math.cos(r), rx * math.sin(r)
    return (f"M{n(cx - dx)},{n(cy - dy)}A{n(rx)},{n(ry)} {n(rot)} 1 0 {n(cx + dx)},{n(cy + dy)}"
            f"A{n(rx)},{n(ry)} {n(rot)} 1 0 {n(cx - dx)},{n(cy - dy)}Z")


_TAG = re.compile(r"<(path|circle|ellipse|rect)\b([^>]*?)(/?)>")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')


def bake(frag, A, sw_scale=True):
    """Apply the affine A to every path, circle, ellipse and rect in a fragment of our own markup."""
    def one(m):
        tag, attrs, close = m.group(1), dict(_ATTR.findall(m.group(2))), m.group(3)
        geo = {}
        if tag == "path":
            geo["d"] = xf_path(attrs.pop("d"), A)
        elif tag == "rect":
            x, y = float(attrs.pop("x", 0)), float(attrs.pop("y", 0))
            w, h = float(attrs.pop("width")), float(attrs.pop("height"))
            geo["d"] = xf_path(f"M{x},{y}H{x + w}V{y + h}H{x}Z", A)
            tag = "path"
        elif tag == "circle":
            cx, cy, r = float(attrs.pop("cx", 0)), float(attrs.pop("cy", 0)), float(attrs.pop("r"))
            X, Y = A.pt(cx, cy)
            rx, ry, ang = _ell_xf(A, r, r, 0)
            if abs(rx - ry) < .05:
                geo.update(cx=n(X), cy=n(Y), r=n(rx))
            else:
                tag = "path"
                geo["d"] = ell_d(X, Y, rx, ry, ang)
        else:
            cx, cy = float(attrs.pop("cx", 0)), float(attrs.pop("cy", 0))
            rx0, ry0 = float(attrs.pop("rx")), float(attrs.pop("ry"))
            X, Y = A.pt(cx, cy)
            rx, ry, ang = _ell_xf(A, rx0, ry0, 0)
            if A.axis:
                geo.update(cx=n(X), cy=n(Y), rx=n(abs(A.m[0]) * rx0), ry=n(abs(A.m[3]) * ry0))
            else:
                tag = "path"
                geo["d"] = ell_d(X, Y, rx, ry, ang)
        if sw_scale and "stroke-width" in attrs:
            attrs["stroke-width"] = n(min(2.2, max(HL, float(attrs["stroke-width"]) * A.s)))
        body = " ".join(f'{k}="{v}"' for k, v in list(geo.items()) + list(attrs.items()))
        return f"<{tag} {body}{close}>"
    return _TAG.sub(one, frag)


# ---- drawing primitives (all ids and tones use the placeholder prefix "Q-") --------------------

def P(d, fill="none", sw=W0, extra=""):
    return f'<path d="{d}" fill="{fill}" {K} stroke-width="{n(sw) if isinstance(sw, float) else sw}"{extra}/>'


def F(d, fill="#000"):
    return f'<path d="{d}" fill="{fill}"/>'


def Wt(d, sw=.9):
    """A white line, cut back through tone."""
    return f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{n(sw)}"/>'


def C(cx, cy, r, fill="#fff", sw=W0, extra=""):
    if sw is None:
        return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}"/>'
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}" {K} stroke-width="{n(sw)}"{extra}/>'


def E(cx, cy, rx, ry, fill="#fff", sw=W0, extra=""):
    if sw is None:
        return f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" fill="{fill}"/>'
    return f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" fill="{fill}" {K} stroke-width="{n(sw)}"{extra}/>'


def dot(cx, cy, r=.8):
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}"/>'


def poly(pts, close=True):
    return "M" + "L".join(f"{n(x)},{n(y)}" for x, y in pts) + ("Z" if close else "")


def tone(t):
    return f"url(#Q-{t})"


TS2, TS, TH, TB, TX, TD, TP, TR, TV, TN = (tone(t) for t in ("s2", "s", "h", "b", "x", "d", "p", "r", "v", "n"))


def star(cx, cy, r, w=None):
    """The Evening Edition's four-point engraved star."""
    w = r * .2 if w is None else w
    return (f'<path d="M{n(cx)},{n(cy - r)}Q{n(cx + w)},{n(cy - w)} {n(cx + r)},{n(cy)}Q{n(cx + w)},{n(cy + w)} '
            f'{n(cx)},{n(cy + r)}Q{n(cx - w)},{n(cy + w)} {n(cx - r)},{n(cy)}Q{n(cx - w)},{n(cy - w)} {n(cx)},{n(cy - r)}Z"/>')


def wstar(cx, cy, r):
    """A white star outlined, for a ruled night sky."""
    w = r * .22
    d = (f"M{n(cx)},{n(cy - r)}Q{n(cx + w)},{n(cy - w)} {n(cx + r)},{n(cy)}Q{n(cx + w)},{n(cy + w)} "
         f"{n(cx)},{n(cy + r)}Q{n(cx - w)},{n(cy + w)} {n(cx - r)},{n(cy)}Q{n(cx - w)},{n(cy - w)} {n(cx)},{n(cy - r)}Z")
    return P(d, "#fff", HL)


def _fy(y):  # scene y -> plate y
    return CY + (y - CY) * G


def _sy(Y):  # plate y -> scene y
    return CY + (Y - CY) / G


def _sx(X):
    return CX + (X - CX) / G


def ruled(y0, y1, sp=1.2, x0=0, x1=120, sw=HL, grow=0.0, ramp=None):
    """Horizontal ruling on the device grid at a fixed pitch (1.2 u = 2 CSS, or 1.8 u = 3 CSS).
    Tone comes from line width: ramp=(top_sw, bottom_sw) steps the width between .6 and .3 (and 0)."""
    pitch = 1.8 if sp > 1.5 else 1.2
    k0 = math.ceil((_fy(y0) - .15) / pitch)
    out = {}
    k = k0
    while True:
        Y = .15 + k * pitch
        if Y > _fy(y1):
            break
        f = (Y - _fy(y0)) / max(.1, _fy(y1) - _fy(y0))
        w = sw if not ramp else (ramp[0] if f < .34 else (ramp[1] if f > .67 else (ramp[0] + ramp[1]) / 2))
        w = .6 if w > .45 else .3
        Yc = Y if w < .45 else round((Y - .15) / .3) * .3  # 1 CSS lines centre on k*.5 CSS
        if (grow and f > .55 and k % 2) or w <= 0:
            k += 1
            continue
        out.setdefault(w, []).append(f"M{n(x0)},{n(_sy(Yc))}H{n(x1)}")
        k += 1
    return "".join(f'<path d="{"".join(v)}" {K} stroke-width="{n(w)}" shape-rendering="crispEdges"/>' for w, v in out.items())


def ruled_v(x0, x1, sp=1.8, y0=0, y1=80, sw=HL):
    d, k = "", math.ceil((CX + (x0 - CX) * G - .15) / 1.8)
    while True:
        X = .15 + k * 1.8
        if X > CX + (x1 - CX) * G:
            break
        d += f"M{n(_sx(X))},{n(y0)}V{n(y1)}"
        k += 1
    return f'<path d="{d}" {K} stroke-width="{n(sw)}" shape-rendering="crispEdges"/>'


def waves_d(x0, x1, y, amp, period, phase=0.0):
    half = period / 2
    x = x0 - phase - period
    d = f"M{n(x)},{n(y)}q{n(half / 2)},{n(-2 * amp)} {n(half)},0"
    x += half
    while x < x1:
        d += f"t{n(half)},0"
        x += half
    return d


def wavy(y0, y1, sp=1.8, amp=.35, per=16, x0=0, x1=120, sw=HL):
    """Bulino sky: gently undulating rules, 3 CSS apart so the anti-aliased curves stay clean."""
    d, y, i = "", y0, 0
    while y <= y1:
        d += waves_d(x0, x1, y, amp, per, (i * 5.3) % per)
        y += max(sp, 1.8 / G)
        i += 1
    return P(d, "none", sw)


def sky(y0, y1, dark=10, x0=0, x1=120):
    """A cross-hatched zenith over bulino ruling: rules at a fixed pitch, heavier above, a 45-degree
    hatch laid over the top with a cloud-soft lower edge."""
    g = ruled(y0, y1, 1.2, x0, x1, ramp=(.6, .3))
    g += F(f"M{x0},{y0 - 4}H{x1}V{y0 + dark}C{x1 * .75},{y0 + dark + 4} {x1 * .4},{y0 + dark - 4} {x0},{y0 + dark + 2}Z", TB)
    return g


def ripples(cx, cy, rx0, ry0, step, count, sw=HL, k=None):
    """Contour ground: concentric ellipses spreading from a subject."""
    k = ry0 / rx0 if k is None else k
    return P("".join(ell_d(cx, cy, rx0 + i * step, (rx0 + i * step) * k) for i in range(count)), "none", sw)


def mini_ball(cx, cy, r, fill="#fff", t=TH, sw=W0):
    """A small sphere: outline and a crescent of hatch on the shadow side, no clip needed."""
    a1, a2 = math.radians(-35), math.radians(145)
    p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    p2 = (cx + r * math.cos(a2), cy + r * math.sin(a2))
    cres = f"M{n(p1[0])},{n(p1[1])}A{n(r)},{n(r)} 0 0 1 {n(p2[0])},{n(p2[1])}A{n(r * 1.15)},{n(r * 1.15)} 0 0 0 {n(p1[0])},{n(p1[1])}Z"
    return C(cx, cy, r, fill, None) + F(cres, t) + C(cx, cy, r, "none", sw)


def lat_lines(cid, cx, cy, r, count=5, sw=HL):
    """Bulino on a sphere: latitude arcs wrapping the ball, clipped to it."""
    d = ""
    for i in range(1, count + 1):
        ph = -math.pi / 2 + math.pi * i / (count + 1)
        y, rx = cy + r * math.sin(ph) * .92, r * math.cos(ph)
        d += f"M{n(cx - rx)},{n(y)}A{n(rx)},{n(rx * .3)} 0 0 0 {n(cx + rx)},{n(y)}"
    return clipped(cid, f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}"/>', P(d, "none", sw))


def cyl_lines(x0, x1, y0, y1, count=7, side=1, sw=HL):
    """Bulino on a cylinder: vertical rules crowding toward the shadowed edge."""
    cx, hw = (x0 + x1) / 2, (x1 - x0) / 2
    d = ""
    for i in range(count):
        th = math.pi / 2 * (.18 + .8 * i / max(1, count - 1))
        x = cx + side * hw * math.sin(th)
        d += f"M{n(x)},{n(y0)}V{n(y1)}"
    return P(d, "none", sw)


def contour_fill(fn, x0, x1, ybot, step=1.4, sw=HL, dx=2.0, count=None):
    """A hill or mass hatched with lines that follow its top edge (fn(x) -> y)."""
    xs = [x0 + (x1 - x0) * i / 40 for i in range(41)]
    top = [(x, fn(x)) for x in xs]
    outline = poly(top + [(x1, ybot), (x0, ybot)])
    lines = ""
    k = 1
    while True:
        pts = [(x, y + k * step) for x, y in top]
        if all(y > ybot for _, y in pts) or (count and k > count):
            break
        lines += poly(pts, False)
        k += 1
    return outline, lines


def rays(cx, cy, r0, r1, nn, a0=0, a1=360, sw=HL, alt=None):
    d = ""
    for i in range(nn):
        a = math.radians(a0 + (a1 - a0) * i / nn)
        rr = r1 if not alt or i % 2 == 0 else alt
        d += f"M{n(cx + r0 * math.cos(a))},{n(cy + r0 * math.sin(a))}L{n(cx + rr * math.cos(a))},{n(cy + rr * math.sin(a))}"
    return f'<path d="{d}" {K} stroke-width="{n(sw)}"/>'


def water(x0, x1, y0, y1, gap_at=None, sw=HL, tight=2.0):
    """The Evening Edition's river: broken horizontal hairlines, a white lane under the light,
    set on the device grid at 3 CSS."""
    lines, i = [], 0
    k = math.ceil((_fy(y0 + 1) - .15) / 1.8)
    ys = []
    while .15 + k * 1.8 < _fy(y1):
        ys.append(_sy(.15 + k * 1.8))
        k += 1
    for y in ys:
        x = x0 + (i * 7) % 11
        while x < x1:
            ln = 6 + (i * 5 + int(x)) % 9
            if not (gap_at and abs(x + ln / 2 - gap_at) < 4 + (y - y0) * .5):
                lines.append(f"M{n(x)},{n(y)}h{n(ln)}")
            x += ln + 3 + (i * 3 + int(x)) % 4
        i += 1
    return f'<path d="{"".join(lines)}" {K} stroke-width="{n(sw)}" shape-rendering="crispEdges"/>'


def fir(x, base, h, t=TX):
    """The Evening Edition's Douglas fir."""
    w = h * .42
    tiers = 5
    d = f"M{n(x)},{n(base - h)}"
    pr, pl = [], []
    for i in range(1, tiers + 1):
        yy = base - h + h * i / tiers * .92
        ww = w * i / tiers
        pr.append(f"L{n(x + ww)},{n(yy)}L{n(x + ww * .45)},{n(yy - h * .06)}")
        pl.append(f"L{n(x - ww * .45)},{n(yy - h * .06)}L{n(x - ww)},{n(yy)}")
    d += "".join(pr[:-1]) + f"L{n(x + w)},{n(base - h * .08)}L{n(x + 1)},{n(base - h * .08)}L{n(x + 1)},{n(base)}" \
        + f"L{n(x - 1)},{n(base)}L{n(x - 1)},{n(base - h * .08)}L{n(x - w)},{n(base - h * .08)}" + "".join(reversed(pl[:-1])) + "Z"
    return f'<path d="{d}" fill="{t}" {K} stroke-width="{W0}" stroke-linejoin="round"/>'


def hood(cx, base, s=1.0):
    """The Evening Edition's Mount Hood: snow above a ragged line, the east face hatched."""
    def p(x, y):
        return f"{n(cx + x * s)},{n(base + y * s)}"
    hill = f"M{p(-58, 0)}L{p(-28, -20)}L{p(-14, -29)}L{p(-5, -36)}L{p(0, -40)}L{p(5, -35)}L{p(14, -28)}L{p(28, -18)}L{p(60, 0)}Z"
    shade = f"M{p(0, -40)}L{p(5, -35)}L{p(14, -28)}L{p(28, -18)}L{p(60, 0)}L{p(8, 0)}L{p(3, -22)}Z"
    st = [(3, 3), (3, -2), (4, 5), (3, -4), (4, 4), (3, -5), (4, 4), (3, -3), (4, 3), (4, -2)]
    snow = f"M{p(-20, -24)}" + "".join(f"l{n(a * s)},{n(b * s)}" for a, b in st)
    low = snow + f"L{p(28, -18)}L{p(60, 0)}L{p(-58, 0)}L{p(-28, -20)}Z"
    return (P(hill, "#fff", W0, ' stroke-linejoin="round"') + F(low, TS) + F(shade, TH)
            + P(snow, "none", HL)
            + P(f"M{p(0, -40)}L{p(-3, -28)}M{p(0, -40)}L{p(2, -27)}M{p(-5, -36)}L{p(-10, -26)}", "none", HL)
            + P("".join(f"M{p(2 + k * 1.6, -38 + k * 1.4)}L{p(14 + k * 6, 0)}" for k in range(0, 9)), "none", HL)
            + P("".join(f"M{p(-4 - k * 2.6, -34 + k * 2.2)}L{p(-12 - k * 7, 0)}" for k in range(1, 7)), "none", HL, ' stroke-dasharray="2.4 1.8"'))


def leaf(x, y, s=1.0, rot=0, t=TH, flip=False):
    """The Evening Edition's acanthus leaf, base at (x, y), pointing along rot."""
    g = (P("M0,0C3,-5 8,-7 12,-6C10,-5 9.5,-4 10.5,-3.4C12.5,-4.6 15,-4 16.5,-2.6C14.5,-2.4 13.5,-1.6 14,-.6"
           "C15.5,-1 17.5,0 18.5,1.4C13,2 6,2.2 0,0Z", "#fff", W0)
         + F("M0,0C5,.6 10,1 18,1.2L14,-.6 10.5,-3.4C7,-1 3,0 0,0Z", t)
         + P("M1,-.4C6,-2 10,-3 13,-3", "none", W0))
    return bake(g, place(x, y, s, rot, flip), sw_scale=False)


def kanok(x, y, s=1.0, rot=0, flip=False, fill="#fff"):
    """The Evening Edition's Thai kanok flame."""
    g = (P("M0,0C3,-5 9,-9 15,-9.5C18,-9.7 20.5,-8 20,-5.5C19.6,-7 18,-7.6 16.8,-7C18.4,-5.8 17.6,-3.6 15.6,-3.4"
           "C15.4,-4.4 14.6,-5 13.6,-4.8C14,-3 12.6,-1.4 10.4,-1.4C10.5,-2.4 10,-3.1 9,-3C8.8,-1 6,.2 0,0Z", fill, W0)
         + P("M1.5,-.8C5,-3.6 10,-6.6 16,-7.6", "none", HL))
    return bake(g, place(x, y, s, rot, flip), sw_scale=False)


def pearl(cx, cy, r):
    return C(cx, cy, r, TP, W0)


def rosette(cx, cy, R, r, nn, sw=HL):
    return "".join(C(cx + R * math.cos(2 * math.pi * i / nn), cy + R * math.sin(2 * math.pi * i / nn), r, "none", sw)
                   for i in range(nn))


def moon(cx, cy, r, lit, waxing=True, dark=TX, outline=W0):
    """The moon at a phase: dark side toned, lit side white."""
    k = max(0.0, min(1.0, lit / 100))
    rx = abs(1 - 2 * k) * r
    s1 = 1 if waxing else 0
    s2 = (0 if k < .5 else 1) if waxing else (1 if k < .5 else 0)
    lit_d = (f"M{n(cx)},{n(cy - r)}A{n(r)},{n(r)} 0 0 {s1} {n(cx)},{n(cy + r)}"
             f"A{n(rx)},{n(r)} 0 0 {s2} {n(cx)},{n(cy - r)}Z")
    return C(cx, cy, r, dark, None) + P(lit_d, "#fff", HL) + C(cx, cy, r, "none", outline)


def subj_dog_head():
    """The Evening Edition's dog head in profile (40 x 40 box), for baking to place."""
    return (P("M11,40C10,32 11,24 14,19C16.5,14.5 20.5,11 25,11C28,11 30.2,12.6 31.2,15L35.6,16.8C37.6,17.8 37.6,20.8 35.6,21.8"
              "L30.6,23C28.6,25 27,27.6 27,31L28,40Z", "#fff", W1, ' stroke-linejoin="round"')
            + F("M12.6,40C12,33 12.6,28 14.6,24.6L19,30C20,34 20.6,37 21,40Z", TH)
            + P("M19.4,13.4C14.6,14.4 12.4,19.6 13.2,26.4C15.6,27.6 18,25.6 19,22.4C20,19.2 20.8,15.6 19.4,13.4Z", TX, W0)
            + C(35.8, 18.2, 1.5, "#000", None) + C(26.4, 15.6, 1, "#000", None)
            + P("M35.4,21.6C33.6,22.6 31.6,22.6 30.4,22.2M27.4,14.2Q26.4,13.2 25,13.6", "none", .5)
            + P("M12,32.4C17,34 23,34 27.4,32", "none", 1.8)
            + C(20, 35.6, 1.6, "#fff", W0))


def peek_dog(x, y, s=1.0, flip=False):
    """Easter egg: a small dog's head peeking over an edge at (x, y), nose to the right."""
    g = (P("M0,0C0,-3 1,-5.5 3.4,-6.4C5,-7 6.6,-6.6 7.4,-5.4L9.6,-4.6C10.6,-4.1 10.6,-2.8 9.6,-2.4L7.2,-1.8C6.8,-1 6.6,-.4 6.6,0Z",
           "#fff", W0, ' stroke-linejoin="round"')
         + P("M3.6,-6.2C2,-6 1.2,-4.4 1.6,-2.2C2.6,-1.8 3.4,-2.6 3.8,-3.8C4.2,-4.8 4.4,-5.8 3.6,-6.2Z", TX, HL)
         + C(9.9, -3.6, .7, "#000", None) + C(6.3, -4.9, .45, "#000", None))
    return bake(g, place(x, y, s, 0, flip), sw_scale=False)


def lotus(cx, cy, s=1.0):
    """The Evening Edition's lotus open on the water, baked (box 40 x 40, base at its 20,30)."""
    pet = "M0,0C4,-6 4,-14 0,-20C-4,-14 -4,-6 0,0Z"
    g = ""
    for a, sc, f in ((-72, .62, TH), (72, .62, TH), (-40, .8, TS), (40, .8, TS), (-16, .92, "#fff"), (16, .92, "#fff"), (0, 1, "#fff")):
        g += bake(P(pet, f, W0), place(20, 30, sc, a), sw_scale=False)
    g += (P("M20,30V13", "none", HL) + P("M5,32.5H35M9,35H31", "none", HL))
    return bake(g, place(cx - 20 * s, cy - 30 * s, s))


def ribbon_bows(pts):
    return "".join(P(f"M{n(x - 1.8)},{n(y - 1.2)}L{n(x + 1.8)},{n(y + 1.2)}L{n(x + 1.8)},{n(y - 1.2)}L{n(x - 1.8)},{n(y + 1.2)}Z", TH, HL)
                   for x, y in pts)


def bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def shade(cid, cx, cy, r, dx=-.32, dy=-.36, t=TH, k=1.08):
    """A sphere's shadow side: tone everywhere on the ball outside a lit circle offset toward the light."""
    lx, ly, lr = cx + dx * r, cy + dy * r, r * k
    d = (f"M{n(cx - r - 1)},{n(cy - r - 1)}H{n(cx + r + 1)}V{n(cy + r + 1)}H{n(cx - r - 1)}Z"
         f"M{n(lx - lr)},{n(ly)}A{n(lr)},{n(lr)} 0 1 0 {n(lx + lr)},{n(ly)}A{n(lr)},{n(lr)} 0 1 0 {n(lx - lr)},{n(ly)}Z")
    return (f'<clipPath id="Q-{cid}"><circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}"/></clipPath>'
            f'<g clip-path="url(#Q-{cid})"><path d="{d}" fill="{t}" fill-rule="evenodd"/></g>')


def sphere_hatch(cx, cy, r, light=(-.5, -.6), bands=6, sw=HL):
    """Crescent contour hatching on a sphere's shadow side: arcs concentric with an offset light."""
    lx, ly = cx + light[0] * r, cy + light[1] * r
    d = ""
    for i in range(bands):
        rr = r * (1.05 + i * .12)
        d += f"M{n(lx + rr * math.cos(0.1))},{n(ly + rr * math.sin(0.1))}" + "".join(
            f"L{n(lx + rr * math.cos(a / 10))},{n(ly + rr * math.sin(a / 10))}" for a in range(2, 34))
    return d


# ---- the medallion: rims and corners ----------------------------------------------------------

# The rims: the scene's edge, a bead row, a rope band between hairlines, the heavy rule and a dotted
# outer hairline; acanthus ears at the sides and a pearl at the head and foot.
OA, OB = 52.6 * G, 32.6 * G           # the oval scene's half-axes on the plate
CA, CB = 52.8 * G, 32.8 * G           # the cartouche scene's half-width and half-height
RIM_HEAVY = 6.9


def _cart_geo(o):
    hw, hh = CA + o, CB + o
    Hc, Vc = CA + RIM_HEAVY, CB + RIM_HEAVY
    d = RIM_HEAVY - o
    rr = 4 + d
    k = math.sqrt(max(.01, rr * rr - d * d))
    return hw, hh, Hc, Vc, rr, k


def cart_d(o):
    hw, hh, Hc, Vc, rr, k = _cart_geo(o)
    def arc(x, y):
        return f"A{n(rr)},{n(rr)} 0 0 0 {n(x)},{n(y)}"
    return (f"M{n(60 - Hc + k)},{n(40 - hh)}H{n(60 + Hc - k)}{arc(60 + hw, 40 - Vc + k)}V{n(40 + Vc - k)}{arc(60 + Hc - k, 40 + hh)}"
            f"H{n(60 - Hc + k)}{arc(60 - hw, 40 + Vc - k)}V{n(40 - Vc + k)}{arc(60 - Hc + k, 40 - hh)}Z")


def _cart_poly(o):
    hw, hh, Hc, Vc, rr, k = _cart_geo(o)
    pts = []
    corners = ((60 + Hc, 40 - Vc), (60 + Hc, 40 + Vc), (60 - Hc, 40 + Vc), (60 - Hc, 40 - Vc))
    starts = ((60 + Hc - k, 40 - hh), (60 + hw, 40 + Vc - k), (60 - Hc + k, 40 + hh), (60 - hw, 40 - Vc + k))
    ends = ((60 + hw, 40 - Vc + k), (60 + Hc - k, 40 + hh), (60 - hw, 40 + Vc - k), (60 - Hc + k, 40 - hh))
    for (cx, cy), (sx, sy), (ex, ey) in zip(corners, starts, ends):
        a0, a1 = math.atan2(sy - cy, sx - cx), math.atan2(ey - cy, ex - cx)
        while a1 > a0:
            a1 -= 2 * math.pi
        for i in range(13):
            a = a0 + (a1 - a0) * i / 12
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _oval_poly(o):
    return [(60 + (OA + o) * math.cos(2 * math.pi * i / 240), 40 + (OB + o) * math.sin(2 * math.pi * i / 240)) for i in range(240)]


def _resample(pts, step):
    seg = []
    m = len(pts)
    total = 0.0
    for i in range(m):
        a, b = pts[i], pts[(i + 1) % m]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        seg.append((a, b, l))
        total += l
    count = max(8, int(total / step))
    st = total / count
    out, acc, j, pos = [], 0.0, 0, 0.0
    for i in range(count):
        target = i * st
        while acc + seg[j][2] < target and j < m - 1:
            acc += seg[j][2]
            j += 1
        a, b, l = seg[j]
        t = (target - acc) / l if l else 0
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        tx, ty = (b[0] - a[0]) / (l or 1), (b[1] - a[1]) / (l or 1)
        out.append((x, y, tx, ty))
    return out


def rope_band(pts, half=1.3, step=2.3):
    d = ""
    for x, y, tx, ty in _resample(pts, step):
        nx, ny = ty, -tx
        ax, ay = x - nx * half - tx * 1.1, y - ny * half - ty * 1.1
        bx, by = x + nx * half + tx * 1.1, y + ny * half + ty * 1.1
        qx, qy = x - tx * .3 + nx * .3, y - ty * .3 + ny * .3
        d += f"M{n(ax)},{n(ay)}Q{n(qx)},{n(qy)} {n(bx)},{n(by)}"
    return P(d, "none", W0, ' stroke-linecap="round"')


def ears():
    """Acanthus ears at the sides: C-scroll arms ending in volutes, a leaf between them, a pearl on the rim."""
    one = (P("M9.6,27.4C4.6,28.4 1.8,32.4 3,36", "none", W1) + P(spiral(5, 35.2, .5, 2.3, 1.3, 160, 26), "none", W0)
           + P("M9.6,52.6C4.6,51.6 1.8,47.6 3,44", "none", W1) + P(spiral(5, 44.8, .5, 2.3, 1.3, 200, 26, cw=False), "none", W0)
           + leaf(10.4, 40, .52, 180, TH) + leaf(8.6, 29, .3, 205, TH) + leaf(8.6, 51, .3, 155, TH)
           + pearl(9.6, 40, 1.7) + star(9.6, 40, 1.1))
    return one + bake(one, Aff(-1, 0, 0, 1, 120, 0), sw_scale=False)


def jewels(top):
    g = ""
    for y, flip in ((40 - top, 1), (40 + top, -1)):
        g += (kanok(63, y, .34, 0) + kanok(57, y, .34, 0, flip=True)) if flip == 1 else (kanok(63, y, .34, 0, fill="#fff") + kanok(57, y, .34, 0, flip=True))
        g += pearl(60, y, 2.1) + star(60, y, 1.4)
    return g


def frame(kind):
    """Returns (scene clip shape, rim drawn over the scene, ground drawn under it)."""
    if kind == "cart":
        clip = f'<path d="{cart_d(0)}"/>'
        rim = (P(cart_d(.3), "none", W0) + P(cart_d(1.6), "none", 1.2, ' stroke-dasharray="0 2.4" stroke-linecap="round"')
               + P(cart_d(2.9), "none", HL) + rope_band(_cart_poly(4.45)) + P(cart_d(6), "none", HL)
               + P(cart_d(RIM_HEAVY), "none", W2) + P(cart_d(8.4), "none", W0, ' stroke-dasharray=".6 1.8"'))
        hw, hh, Hc, Vc, rr, k = _cart_geo(RIM_HEAVY)
        rim += "".join(star(x, y, 2) for x in (60 - Hc, 60 + Hc) for y in (40 - Vc, 40 + Vc))
        under = F(cart_d(7.6), "#fff")
        return clip, rim + ears() + jewels(CB + RIM_HEAVY), under
    clip = E(60, 40, OA, OB, "#000", None).replace(' fill="#000"', "")
    def e(o, sw, extra=""):
        return E(60, 40, OA + o, OB + o, "none", sw, extra)
    rim = (e(.3, W0) + e(1.6, 1.2, ' stroke-dasharray="0 2.4" stroke-linecap="round"') + e(2.9, HL)
           + rope_band(_oval_poly(4.45)) + e(6, HL) + e(RIM_HEAVY, W2) + e(8.4, W0, ' stroke-dasharray=".6 1.8"'))
    under = E(60, 40, OA + 7.6, OB + 7.6, "#fff", None)
    return clip, rim + ears() + jewels(OB + RIM_HEAVY), under


# ---- tones: the Evening Edition's patterns, rebuilt on the e-ink grid -------------------------------

def _diag(s, back=False):
    if back:
        return f"M0,0L{n(s)},{n(s)}M{n(-s / 2)},{n(s / 2)}L{n(s / 2)},{n(s * 1.5)}M{n(s / 2)},{n(-s / 2)}L{n(s * 1.5)},{n(s / 2)}"
    return f"M0,{n(s)}L{n(s)},0M{n(-s / 2)},{n(s / 2)}L{n(s / 2)},{n(-s / 2)}M{n(s / 2)},{n(s * 1.5)}L{n(s * 1.5)},{n(s / 2)}"


def _guil_tile():
    return "".join(f'<path d="{waves_d(0, 9, 1.2, .42, 9, ph)}"/>' for ph in (0, 3, 6))


_CE = ' shape-rendering="crispEdges"'
_PAT = {
    "s2": (2.4, 2.4, '<circle cx=".6" cy=".6" r=".3"/><circle cx="1.8" cy="1.8" r=".3"/>'),
    "s": (1.8, 1.8, '<circle cx=".45" cy=".45" r=".3"/><circle cx="1.35" cy="1.35" r=".3"/>'),
    "h": (1.8, 1.8, f'<path d="{_diag(1.8)}" {K} stroke-width=".3"/>'),
    "b": (1.8, 1.8, f'<path d="{_diag(1.8, True)}" {K} stroke-width=".3"/>'),
    "x": (1.8, 1.8, f'<path d="{_diag(1.8)}{_diag(1.8, True)}" {K} stroke-width=".3"/>'),
    "d": (1.8, 1.8, f'<path d="{_diag(1.8)}" {K} stroke-width=".6"/>'),
    "p": (3.6, 1.8, f'<path d="M0,.9Q.9,0 1.8,.9T3.6,.9" fill="none" {K} stroke-width=".3"/>'),
    "r": (3.6, 1.2, f'<path d="M0,.15H3.6" {K} stroke-width=".3"{_CE}/>'),
    "v": (1.2, 3.6, f'<path d="M.15,0V3.6" {K} stroke-width=".3"{_CE}/>'),
    "n": (3.6, 1.2, f'<path d="M0,.3H3.6" {K} stroke-width=".6"{_CE}/>'),
    "g": (9, 2.4, f'<g fill="none" {K} stroke-width=".3">{_guil_tile()}</g>'),
}
TG = tone("g")


_SW = (.3, .6, .9, 1.2, 1.8, 2.4)


def _snap(svg):
    """Every stroke on a whole number of device pixels at 200 px: .5, 1, 1.5 CSS (2, 3, 4 for shapes
    drawn as thick strokes). White lines cut through tone are at least 1 CSS."""
    def tag(m):
        t = m.group(0)
        w = re.search(r'stroke-width="([\d.]+)"', t)
        if not w:
            return t
        v = float(w.group(1))
        opts = _SW[1:] if 'stroke="#fff"' in t else _SW
        best = min(opts, key=lambda o: abs(o - v))
        return t.replace(w.group(0), f'stroke-width="{n(best)}"')
    return re.sub(r"<(?:path|circle|ellipse|rect|line|polyline|text)\b[^>]*>", tag, svg)


def finish(key, body, kind="bead", desc="", behind="", sprays=True):
    clip, rim, under = frame(kind)
    body = bake(body, Aff.T(60, 40) * Aff.S(G) * Aff.T(-60, -40), sw_scale=False)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80" width="{DISPLAY_W}" height="{n(DISPLAY_W * 2 / 3)}" role="img" '
           f'aria-label="{desc}"><defs>@@DEFS@@<clipPath id="Q-clip">{clip}</clipPath></defs>'
           f'{behind}{under}<g clip-path="url(#Q-clip)">{body}</g>{rim}</svg>')
    used = sorted(set(re.findall(r"url\(#Q-(\w+)\)", svg)) & set(_PAT))
    defs = "".join(f'<pattern id="Q-{u}" width="{_PAT[u][0]}" height="{_PAT[u][1]}" patternUnits="userSpaceOnUse">{_PAT[u][2]}</pattern>'
                   for u in used)
    svg = svg.replace("@@DEFS@@", defs)
    svg = svg.replace('id="Q-', f'id="{key}-').replace("url(#Q-", f"url(#{key}-")
    assert "transform" not in svg
    return _snap(svg)


# ---- helpers for scenes -------------------------------------------------------------------------

def cloud(x, y, s=1.0):
    d = (f"M{n(x)},{n(y)}c{n(-4 * s)},0 {n(-5 * s)},{n(-4 * s)} {n(-1 * s)},{n(-4.6 * s)}c{n(0)},{n(-3.4 * s)} {n(5 * s)},{n(-4.6 * s)} {n(7 * s)},{n(-2 * s)}"
         f"c{n(2 * s)},{n(-3 * s)} {n(8 * s)},{n(-3 * s)} {n(9 * s)},{n(1 * s)}c{n(4 * s)},{n(-1 * s)} {n(6 * s)},{n(3.4 * s)} {n(3 * s)},{n(5.6 * s)}Z")
    return P(d, "#fff", W0) + P(f"M{n(x + 1 * s)},{n(y - 1.2 * s)}h{n(15 * s)}M{n(x + 3 * s)},{n(y - 2.4 * s)}h{n(10 * s)}", "none", HL)


def birds(pts, sw=.7):
    return P("".join(f"M{n(x - 2.4 * s)},{n(y)}q{n(1.2 * s)},{n(-1.6 * s)} {n(2.4 * s)},0q{n(1.2 * s)},{n(-1.6 * s)} {n(2.4 * s)},0"
                     for x, y, s in pts), "none", sw)


def offset_band(curve, wfun, steps=40):
    """A tapering band along a cubic bezier; returns (outline path, left pts, right pts, centre pts)."""
    L, R, Cn = [], [], []
    for i in range(steps + 1):
        t = i / steps
        x, y = bezier(*curve, t)
        x2, y2 = bezier(*curve, min(1, t + .01))
        x1, y1 = bezier(*curve, max(0, t - .01))
        dx, dy = x2 - x1, y2 - y1
        l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        w = wfun(t) / 2
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
        Cn.append((x, y))
    return poly(L + R[::-1]), L, R, Cn


def spiral(cx, cy, r0, r1, turns, a0=0, steps=60, cw=True):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0) + (1 if cw else -1) * 2 * math.pi * turns * t
        r = r0 + (r1 - r0) * t
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts, False)


def letter_paths(ch):
    return {
        "A": "M.28,.82L.5,.18L.72,.82M.36,.6H.64",
        "B": "M.32,.82V.18H.52C.72,.18 .72,.48 .52,.48H.32M.52,.48C.76,.48 .76,.82 .52,.82H.32",
        "C": "M.72,.3C.62,.16 .28,.14 .28,.5C.28,.86 .62,.84 .72,.7",
        "P": "M.34,.84V.16H.56C.8,.16 .8,.52 .56,.52H.34",
    }[ch]


def glyph(ch, x, y, s, sw=1.0):
    return bake(P(letter_paths(ch), "none", sw, ' stroke-linecap="round" stroke-linejoin="round"'), place(x, y, s), sw_scale=False)


def grass(x0, x1, y, h=3.0, step=2.2, sw=HL):
    d, x, i = "", x0, 0
    while x < x1:
        hh = h * (.6 + .4 * ((i * 7) % 5) / 4)
        d += f"M{n(x)},{n(y)}q{n(.4)},{n(-hh * .6)} {n(1.4 if i % 2 else -1)},{n(-hh)}"
        x += step
        i += 1
    return P(d, "none", sw)


def clipped(cid, shape, inner):
    return f'<clipPath id="Q-{cid}">{shape}</clipPath><g clip-path="url(#Q-{cid})">{inner}</g>'


def rubber_duck(x, y, s=1.0):
    g = (P("M-3,0C-3.4,-2 -2,-2.8 0,-2.4C.4,-4.4 3,-4.6 3.4,-2.8L4.8,-2.4L3.4,-1.8C3.6,-.6 3,0 2,0Z", "#fff", W0)
         + dot(2.2, -3.4, .35) + P("M-1.6,-1.2C-.6,-.6 .6,-.8 1,-1.6", "none", HL)
         + P("M-4,.6h9", "none", HL))
    return bake(g, place(x, y, s), sw_scale=False)


# ---- the scenes ---------------------------------------------------------------------------------

def v_sunrise():
    """Today: the sun coming up over the Sauvie Island fields, a barn and silo, the fence line."""
    sx, sy = 60, 50
    g = rays(sx, sy, 13.5, 64, 84, 180, 360, HL, alt=34)
    g += cloud(14, 26, .9) + cloud(84, 20, 1.0) + cloud(38, 14, .6)
    g += birds([(30, 34, .8), (36, 31, .6), (90, 32, .7)])
    g += C(sx, sy, 11, "#fff", W1) + C(sx, sy, 9.6, "none", HL, ' stroke-dasharray=".6 1.2"') + ripples(sx, sy, 1.8, 1.8, 1.2, 6) + star(sx, sy, 1.6)
    # tree lines and the barn on the horizon
    def trees(x0, x1, seed):
        d, x = f"M{n(x0)},{n(sy + 1)}", x0
        i = seed
        while x < x1:
            h = 3 + 2.4 * abs(math.sin(i * 1.7))
            d += f"Q{n(x + 1.6)},{n(sy - h - 1.6)} {n(x + 3.2)},{n(sy - h * .6)}"
            x += 3.2
            i += 1
        return P(d + f"L{n(x)},{n(sy + 1)}Z", TX, W0, ' stroke-linejoin="round"')
    g += trees(4, 46, 1) + trees(76, 118, 4)
    barn = (P("M84,52V46L86,41.4L91,38.6L96,41.4L98,46V52Z", "#fff", W0)
            + P("M84,46L86,41.4L91,38.6L96,41.4L98,46", "none", W1) + F("M86.4,42.2L91,39.6L95.6,42.2L96.8,45.6H85.2Z", TD)
            + P("M88.6,52V47.6H93.4V52M88.6,47.6L93.4,52M93.4,47.6L88.6,52", "none", HL)
            + P("M99,52V41.6C99,39.4 103,39.4 103,41.6V52Z", "#fff", W0) + P("M99,44H103M99,46.6H103M99,49.2H103", "none", HL))
    g += barn
    # the fields: furrows running to the sun
    vx, vy = sx, sy - 2
    field = ""
    k = 0
    for xb in range(-180, 300, 15):
        xa, xc = xb, xb + 15
        typ = k % 4
        if typ == 1:
            field += F(f"M{vx},{vy}L{xa},84L{xc},84Z", TS)
        elif typ == 3:
            field += F(f"M{vx},{vy}L{xa},84L{xc},84Z", TS2)
        else:
            field += P("".join(f"M{vx},{vy}L{n(xa + 15 * j / 4)},84" for j in (1, 2, 3)), "none", HL)
        field += P(f"M{vx},{vy}L{xa},84", "none", W0)
        k += 1
    g += clipped("fl", '<rect x="0" y="51.4" width="120" height="30"/>', f'<rect x="0" y="51.4" width="120" height="30" fill="#fff"/>{field}')
    g += P("M0,51.4H120", "none", W0) + F("M0,51.4H120V53H0Z", TD)
    # the fence and its watcher
    posts = "".join(f"M{x},{n(62 - (x - 8) * .09)}v{n(6 + (x % 3))}" for x in range(8, 52, 7))
    g += peek_dog(30.4, 63.4, .75)
    g += P(posts, "none", 1.3) + P("M6,63.6L52,59.6M6,66L52,62", "none", HL)
    g += grass(8, 112, 76, 3.4, 2.6)
    return finish("sunrise", g, "bead", "The sun rising over the Sauvie Island fields")


def v_road():
    """Roads and mountains: the road winding up to Mount Hood, skis crossed behind the medallion."""
    g = sky(6, 46, 9)
    g += birds([(28, 20, .7), (34, 17, .55)])
    g += hood(60, 45, .95)
    hills = P("M0,45C14,41 26,43 36,42.6C48,42 54,45 64,44C78,43 92,40.6 104,42.6C112,43.6 116,43 120,43.6V54H0Z", TX, W0)
    g += hills + "".join(fir(x, 45.6 + (x % 4) * .3, 6 + (x * 7) % 4) for x in range(3, 120, 5))
    g += F("M0,52H120V82H0Z", "#fff") + P("M0,52.4C30,51 90,51 120,52.4", "none", W0)
    g += F("M0,53H120V62H0Z", TS) + F("M0,62H120V82H0Z", TS2)
    curve = ((58, 51.6), (34, 58), (98, 62), (46, 84))
    outline, L, R, Cn = offset_band(curve, lambda t: 1.2 + 30 * t ** 1.7)
    g += F(outline, "#fff")
    g += P(poly(L, False), "none", W0) + P(poly(R, False), "none", W0)
    g += P(poly(Cn[6:], False), "none", .7, ' stroke-dasharray="2.4 2"')
    # verge shadow
    g += P(poly([(x + 1.6, y) for x, y in R[14:]], False), "none", HL)
    g += fir(14, 76, 34) + fir(24, 74, 22) + fir(104, 74, 30) + fir(96, 70, 16)
    g += grass(30, 50, 64, 2.6) + grass(74, 94, 66, 2.6)
    # skis crossed behind the medallion: tails low, upturned tips at the top corners
    def ski(x0, y0, x1, y1, curl):
        dx, dy = x1 - x0, y1 - y0
        l = math.hypot(dx, dy)
        ux, uy = dx / l, dy / l
        nx, ny = -uy * 1.5, ux * 1.5
        tipx, tipy = x1 + ux * 3 + curl * 2.4, y1 + uy * 3 - 2.6
        d = (f"M{n(x0 + nx)},{n(y0 + ny)}L{n(x1 + nx)},{n(y1 + ny)}Q{n(x1 + ux * 3 + nx)},{n(y1 + uy * 3 + ny)} {n(tipx)},{n(tipy)}"
             f"Q{n(x1 + ux * 1.6 - nx)},{n(y1 + uy * 1.6 - ny)} {n(x1 - nx)},{n(y1 - ny)}L{n(x0 - nx)},{n(y0 - ny)}Q{n(x0 - ux * 1.4)},{n(y0 - uy * 1.4)} {n(x0 + nx)},{n(y0 + ny)}Z")
        return P(d, TS, W0) + P(f"M{n(x0)},{n(y0)}L{n(x1)},{n(y1)}", "none", HL)
    behind = ski(6, 77, 110, 4, 1) + ski(114, 77, 10, 4, -1)
    behind += P("M2,10.4L13.6,70M118,10.4L106.4,70", "none", .8) + C(5.4, 27.6, 1.6, "#fff", W0) + C(114.6, 27.6, 1.6, "#fff", W0)
    return finish("road", g, "rope", "A winding road to Mount Hood with skis crossed", behind=behind, sprays=False)


def v_toddler():
    """The little one: a dappled rocking horse modelled in curved line, lettered blocks, a kite and its
    bows, a striped ball, daisies and a butterfly."""
    g = sky(6, 66, 9)
    g += cloud(36, 16, .7) + cloud(70, 26, .55)
    kx, ky = 97, 17
    T, Rr, B, Lf = (kx, ky - 9), (kx + 7.4, ky), (kx, ky + 12), (kx - 7.4, ky)
    g += F(poly([T, Rr, B, Lf]), "#fff")
    g += F(poly([T, (kx, ky), Lf]), TH) + F(poly([(kx, ky), Rr, B]), TX)
    g += P(poly([T, Rr, B, Lf]), "none", W1) + P(f"M{kx},{ky - 9}V{ky + 12}M{kx - 7.4},{ky}H{kx + 7.4}", "none", HL)
    tail = ((kx, ky + 12), (90, 38), (80, 22), (66, 34))
    g += P(f"M{kx},{ky + 12}C90,38 80,22 66,34", "none", HL)
    g += ribbon_bows([bezier(*tail, t) for t in (.22, .45, .68, .9)])
    g += P(f"M{kx},{ky + 3}C108,30 104,48 118,62", "none", HL)
    g += butterfly(52, 30, .55)
    # floor of boards and the lawn's edge
    g += F("M0,66H120V82H0Z", "#fff") + P("M0,66H120", "none", W0)
    g += clipped("fb", '<rect x="0" y="66" width="120" height="16"/>', P("".join(f"M60,48L{x},84" for x in range(-100, 240, 12)), "none", HL))
    g += P("M0,70.6H120M0,76H120", "none", HL)
    # rocking horse
    h = P("M10,62.6Q38,76 68,62.6L68.6,65Q38,79 9.4,65Z", "#fff", W0) + P("M12,63.6Q38,76.4 66,63.6M11,64.4Q38,77.6 67,64.4", "none", HL)
    h += (P("M29.4,46.6L33,46.8L29.6,64.6L26.6,64.6Z", "#fff", W0) + P("M47,46.4L50.4,46.6L57,63L54,63.4Z", "#fff", W0)
          + P("M31.6,48L28.6,63.6M32.4,48L29.4,63.6M49.6,48L55.6,62.6M48.8,48L54.8,62.8", "none", HL)
          + P("M26,46.6L29.4,46.6L24.6,64.6L21.4,64.4Z", "#fff", W0) + P("M43,46.8L46.6,46.8L51,64.8L47.8,65Z", "#fff", W0)
          + P("M28.4,48L24,63.4M45.6,48.4L49.8,64", "none", HL))
    body = ("M51,38C53,42 52,47.4 47,48.2L28,48.4C25,48.4 23,46 24,42C23,38 22,34 21,30C20,28 17,27.4 14,28.2"
            "C12,28.4 10.8,26 12,24.4C13,22 15,20 18,19L19,15.6L21.2,18.8C24,19 26,21 28,26C29,30 30,35 33,36C38,37 45,37 51,38Z")
    h += P(body, "#fff", W1, ' stroke-linejoin="round"')
    h += clipped("hb", f'<path d="{body}"/>', P("".join(f"M{20 + k},{49 - k * .2}C{30 + k},{44 - k * .5} {44 + k * .4},{43 - k * .6} {54},{40 - k * .4}" for k in range(0, 8, 2))
                                                + "".join(f"M{n(23.6 + k * 1.2)},45C{n(23 + k * 1.2)},38 {n(21 + k)},31 {n(17 + k)},26" for k in range(3)), "none", HL))
    h += "".join(C(x, y, 1.1, "#fff", HL) for x, y in ((44, 41), (47.6, 40.6), (40, 42.4), (46, 44), (36.6, 42.6), (49.4, 43)))
    mane = "".join(f"M{n(21 + 12 * t)},{n(19 + 17 * t ** 1.3)}l{n(2.6)},{n(.6)}" for t in [i / 12 for i in range(13)])
    h += P(mane, "none", 1.2, ' stroke-linecap="round"') + P("M18.6,18.6C17,20 16.4,21.6 16.8,23", "none", W1)
    h += P("M33,36.4C36,34.6 41,34.6 44,36.8L43,41.4C40,42.4 36,42.4 34,41.4Z", TX, W0) + P("M38.6,42V46.6M37.4,46.6H39.8", "none", W0)
    h += P("M51.4,38.4C55,39 57,43 58,48M51.4,39.4C54,41 55,45 55.4,49M52,38C56,37 59,40 60,44M52,39C55.6,40 57.4,44 57.4,48.6", "none", W0)
    h += dot(19.4, 22.6, .7) + P("M13,26.2L20.6,24.6L22,20.6M20.6,24.6C26,30 30,33 34,35.6", "none", HL)
    h += P("M17,23.6H25", "none", 1.2, ' stroke-linecap="round"') + star(20.6, 24.6, 1)
    g += bake(h, place(12, 4.4, .84), sw_scale=False)
    # the striped ball, daisies
    g += C(62, 64.4, 3.4, "#fff", W0) + clipped("bl", '<circle cx="62" cy="64.4" r="3.4"/>', F("M60.4,60H63.6L63,69H61Z", TD) + P("M58,62.6H66M58,66.2H66", "none", HL)) + C(62, 64.4, 3.4, "none", W0)
    for x, y in ((8, 74), (20, 76), (106, 74), (96, 77)):
        g += "".join(C(x + 1.4 * math.cos(a), y + 1.4 * math.sin(a), .7, "#fff", HL) for a in [i * math.pi / 3 for i in range(6)]) + C(x, y, .7, TS, HL)
    def cube(x, y, s, ch):
        a = .42 * s
        side = f"M{n(x + s)},{n(y)}L{n(x + s + a)},{n(y - a * .85)}V{n(y + s - a * .85)}L{n(x + s)},{n(y + s)}Z"
        return (P(f"M{n(x)},{n(y)}L{n(x + a)},{n(y - a * .85)}H{n(x + s + a)}L{n(x + s)},{n(y)}Z", "#fff", W0)
                + star(x + s / 2 + a / 2, y - a * .42, 1.2)
                + P(side, "#fff", W0) + clipped(f"cs{ch}", f'<path d="{side}"/>', P("".join(f"M{n(x + s + a * f)},{n(y - 9)}V{n(y + s + 2)}" for f in (.25, .5, .75)), "none", HL)
                                                     + F(side, TH))
                + P(f"M{n(x)},{n(y)}H{n(x + s)}V{n(y + s)}H{n(x)}Z", "#fff", W0)
                + P(f"M{n(x + 1.2)},{n(y + 1.2)}H{n(x + s - 1.2)}V{n(y + s - 1.2)}H{n(x + 1.2)}Z", "none", HL)
                + P(f"M{n(x + 2)},{n(y + 2)}H{n(x + s - 2)}V{n(y + s - 2)}H{n(x + 2)}Z", "none", HL, ' stroke-dasharray=".6 .6"')
                + glyph(ch, x, y, s, 1.2))
    g += peek_dog(100.4, 58.6, .8)
    g += cube(68, 55, 11.6, "A") + cube(84.4, 55, 11.6, "B") + cube(76, 43.4, 11.6, "C")
    return finish("toddler", g, "bead", "A rocking horse, wooden blocks and a kite")


def v_solarpanel():
    """Sun and power: a gabled house with panels on its roof under a radiant sun."""
    g = sky(6, 66, 9)
    sx, sy = 26, 21
    g += C(sx, sy, 19, "#fff", None) + rays(sx, sy, 10, 19, 32, 0, 360, W0, alt=14.5)
    g += C(sx, sy, 7.6, "#fff", W1) + ripples(sx, sy, 2.4, 2.4, 1.2, 4) + C(sx, sy, 6.4, "none", HL, ' stroke-dasharray=".6 1.2"') + star(sx, sy, 2)
    g += P("M33,26L48,38M36,24L66,34M37,21L84,30", "none", HL, ' stroke-dasharray="2 2.4"')
    g += fir(14, 66, 30) + fir(108, 66, 24)
    R0, R1, E0, E1 = (40, 34), (90, 34), (52, 48), (102, 48)
    def at(u, v):
        a = (R0[0] + (R1[0] - R0[0]) * u, R0[1] + (R1[1] - R0[1]) * u)
        b = (E0[0] + (E1[0] - E0[0]) * u, E0[1] + (E1[1] - E0[1]) * u)
        return (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v)
    g += P(poly([(84, 26), (88.4, 26), (88.4, 34), (84, 34)]), TX, W0) + P("M83.2,25.6H89.2", "none", W1)
    g += P(poly([R0, R1, E1, E0]), "#fff", W1)
    g += F(poly([R0, R1, E1, E0]), TS2)
    for i in range(4):
        for j in range(2):
            u0, u1 = .06 + i * .235, .06 + i * .235 + .21
            v0, v1 = .14 + j * .4, .14 + j * .4 + .34
            q = [at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)]
            g += P(poly(q), TD, W0)
            cells = ""
            for k in (1, 2, 3):
                a, b = at(u0 + (u1 - u0) * k / 4, v0), at(u0 + (u1 - u0) * k / 4, v1)
                cells += f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}"
            a, b = at(u0, (v0 + v1) / 2), at(u1, (v0 + v1) / 2)
            cells += f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}"
            g += Wt(cells, .55)
    g += P(f"M{R0[0]},{R0[1]}H{R1[0]}", "none", W1)
    # gable end and the long wall
    g += P("M28,66V48L40,33.4L52,48V66Z", "#fff", W0)
    g += P("".join(f"M28,{y}H52" for y in range(50, 66, 2)), "none", HL)
    g += P("M26.6,49.4L40,33L53.4,49.4", "none", W1, ' stroke-linejoin="round"')
    g += C(40, 42.6, 2.6, TS, W0) + P("M37.4,42.6H42.6M40,40V45.2", "none", HL)
    g += P("M52,48H102V66H52Z", TH, W0) + P("M51,48.4H103", "none", W1)
    for x in (58, 74, 90):
        g += P(f"M{x},52H{x + 8}V60H{x}Z", "#fff", W0) + P(f"M{x + 4},52V60M{x},56H{x + 8}", "none", HL)
    g += P("M33,66V56H39V66", "#fff", W0) + dot(37.6, 61.4, .5)
    g += F("M0,66H120V82H0Z", "#fff") + P("M0,66H120", "none", W0) + F("M0,67.6H120V82H0Z", TS2)
    g += P("M36,66L30,82M36,66L42,82", "none", HL)
    g += grass(4, 26, 68, 2.6) + grass(48, 116, 68, 2.6)
    g += peek_dog(44.6, 67.4, .7)
    return finish("solarpanel", g, "bead", "A house with solar panels on its roof under a radiant sun")


def ivy(x, y, s, rot, shade=True):
    g = P("M0,0C2.2,-1.4 3,-4.6 0,-8C-3,-4.6 -2.2,-1.4 0,0Z", "#fff", W0)
    if shade:
        g += F("M0,0C2.2,-1.4 3,-4.6 0,-8Z", TH)
    g += P("M0,0V-7", "none", HL)
    return bake(g, place(x, y, s, rot), sw_scale=False)


def v_garden():
    """A garden: a wren on a branch among vines, a spotted mushroom and an open bloom."""
    g = sky(6, 70, 8)
    # vines across the top
    vine = "M6,28C14,16 26,12 36,16C44,19 46,12 56,10C66,8 72,16 82,13C90,11 96,8 110,14"
    g += P(vine, "none", .8) + P("M36,16C38,22 34,26 30,24C28,23 29,20 31,21", "none", HL)
    g += P("M82,13C84,20 90,22 92,18C93,16 91,15 90,16.4", "none", HL)
    for (x, y, r, sh) in ((12, 22, -40, 1), (22, 14.6, 20, 0), (30, 14, -20, 1), (44, 16, 160, 0), (50, 11, 30, 1),
                          (62, 9.6, -30, 0), (70, 14, 170, 1), (78, 13.6, 20, 0), (96, 10, 10, 1), (104, 11.4, 160, 0)):
        g += ivy(x, y, .9, r, sh)
    # the branch
    g += P("M2,46C30,43.4 60,41 104,33L106,35.6C64,45 30,50 2,52Z", "#fff", W1)
    g += F("M2,49C30,47.6 64,42 105,34.6L106,35.6C64,45 30,50 2,52Z", TX)
    g += P("M12,48C18,47.6 22,47.2 28,46.6M50,45C56,44.4 62,43 66,42.4M82,39C88,37.8 92,37 96,36", "none", HL)
    g += P("M78,39.4C82,32 86,28 92,24", "none", W1) + ivy(92, 24, 1, 50) + ivy(86, 28.6, .8, -20)
    g += P("M20,47.6C18,42 14,40 10,40", "none", W0) + ivy(10, 40, .8, -80, False)
    # the wren
    wren = ("M44,29.4C45,27.6 47,26.4 50,26.2C53,26 55.6,27.2 57,29C59.6,30 62,31 64.6,32L67.6,23.6C68.2,22.4 69.8,22.4 70.2,23.6"
            "L67.4,34C66.6,36 65,37 63.4,37.6C62,40.6 58,42.2 53.6,42C49.6,41.8 46,40 44.6,36.6C44,34.6 44,32 44,29.4Z")
    g += P(wren, "#fff", W0, ' stroke-linejoin="round"')
    g += F("M44,29.4C45,27.6 47,26.4 50,26.2C53,26 55.6,27.2 57,29C59.6,30 62,31 64.6,32L63.4,37.6C60,34 52,31 44.4,31.4Z", TS)
    g += P("M50,32.6C54,31.6 60,32.4 63.4,35.6C60.4,38 54,38.6 50,36.6Z", "#fff", W0)
    g += P("M53,33V37.6M55.6,32.8V38M58.2,33.2V37.8M60.8,34.4V37.2", "none", HL)
    g += P("M65.4,30.4L68.6,31.4M66,28.2L69.2,29.2M66.6,26L69.6,27", "none", .7)
    g += P("M44.2,29.4L40.4,30.2L44.2,30.8Z", "#000", HL) + dot(47.4, 29.4, .65)
    g += Wt("M46,28C47.6,27.4 50,27.4 52.6,28.2", .7)
    g += P("M52.6,41.8L52,44.6M55.6,41.8L56.4,44.4M50.6,44.6H53.6M55,44.6H58", "none", W0)
    g += P("M46,37C48,39 50,40.4 53,40.8M47,34.6C48.4,36 49.6,37 51,37.6", "none", HL, ' stroke-dasharray="1 1"')
    # mushroom
    m = ""
    m += P("M10,63.4C10,53 34,53 34,63.4Z", TX, W1)
    m += "".join(C(x, y, r, "#fff", HL) for x, y, r in ((16, 58.6, 1.6), (22, 56, 1.2), (28, 58, 1.8), (20, 61.4, 1.0), (31, 61.6, .9), (13.6, 61.8, .8)))
    m += P("M10,63.4C14,65.6 30,65.6 34,63.4", "#fff", W0)
    m += P("".join(f"M{n(22 + 11 * math.cos(a))},{n(64 + 1.4 * math.sin(a))}L22,64" for a in [math.pi * (.15 + .7 * i / 10) for i in range(11)]), "none", HL)
    m += P("M19.4,65.6C19,70 18,73 17,76H27.4C26.4,73 25,70 24.6,65.6Z", "#fff", W0) + F("M22.4,65.6C23,70 24.4,73 25.4,76H27.4C26.4,73 25,70 24.6,65.6Z", TS)
    m += P("M19.2,68C21,69 23,69 25,68", "none", W0)
    m += P("M36,74C36,69.6 44,69.6 44,74Z", TH, W0) + P("M39.2,74V77M40.8,74V77", "none", W0)
    g += bake(m, place(10, -2, 1), sw_scale=False)
    # the bloom
    fx, fy = 88, 56
    g += P("M88,64C87,70 89,74 88,80", "none", W1) + ivy(88, 70, 1.2, 50) + ivy(88, 74, 1.1, -60)
    for i in range(5):
        a = math.radians(i * 72 - 90 + 36)
        g += P(ell_d(fx + 5 * math.cos(a), fy + 5 * math.sin(a), 4.6, 3.2, math.degrees(a)), TH, W0)
    for i in range(5):
        a = math.radians(i * 72 - 90)
        g += P(ell_d(fx + 5.4 * math.cos(a), fy + 5.4 * math.sin(a), 5, 3.6, math.degrees(a)), "#fff", W0)
        g += P(f"M{n(fx + 2 * math.cos(a))},{n(fy + 2 * math.sin(a))}L{n(fx + 8.4 * math.cos(a))},{n(fy + 8.4 * math.sin(a))}", "none", HL)
    g += C(fx, fy, 2.6, TS, W0) + "".join(dot(fx + 3.4 * math.cos(i * .9), fy + 3.4 * math.sin(i * .9), .4) for i in range(7))
    # a bee on its way
    g += E(76, 46, 1.8, 1.1, TH, HL) + P("M75.4,45L74,42.8C75,42.4 76,43.4 75.8,45M76.6,45L78,42.8C79,43.2 78.4,44.6 76.8,45", "#fff", HL)
    g += P("M70,49C72,48.6 72,46 74,46.6", "none", HL, ' stroke-dasharray="1 1"')
    g += F("M0,74C30,72 80,73 120,72V82H0Z", TS2) + grass(4, 116, 76, 4, 2.4)
    g += peek_dog(66, 73, .75)
    return finish("garden", g, "rope", "A wren on a branch with vines, a mushroom and a bloom")


def v_heron():
    """The river: a great blue heron in the reeds on the Columbia, a sternwheeler far off."""
    g = sky(6, 40, 8)
    g += C(100, 37, 6.6, "#fff", W0) + C(100, 37, 4.6, "none", HL, ' stroke-dasharray="1 1.6"')
    g += birds([(70, 18, .7), (78, 14, .55)])
    g += P("M0,40C20,36 40,38 60,37C80,36 100,33.6 120,36.6V43H0Z", TS, W0)
    g += "".join(fir(x, 38 - (x % 5) * .2, 4 + x % 3, TX) for x in range(4, 70, 4))
    # sternwheeler, bow to the left, smoke trailing aft
    g += F("M0,42H120V82H0Z", "#fff") + P("M0,42H120", "none", W0)
    sw = (P("M78,41.4H98.6L97,43.4H80.4Z", "#fff", W0) + P("M80.6,38.6H95V41.4H80.6Z", "#fff", W0) + P("M82.6,36.6H93V38.6H82.6Z", "#fff", W0)
          + P("M86.4,35H89.6V36.6H86.4Z", TX, HL) + P("M82,39.6H94M84,37.6H92", "none", HL, ' stroke-dasharray=".8 .8"')
          + P("M84,36.6V30.6M86,36.6V30.6", "none", .8) + P("M83.2,30.6H84.8M85.2,30.6H86.8", "none", W0)
          + P("M85,30C88,27.6 92,29 96,26.6C100,24.6 104,26 108,24", "none", HL, ' stroke-dasharray="1.4 1"')
          + P("M95.4,37.6H100.4V42.4H95.4Z", TX, W0))
    g += sw + water(0, 120, 42, 80, gap_at=100)
    # reeds behind
    # the heron
    g += P("M33,47L32,66M36.4,46.6L38.6,66", "none", W1)
    g += P("M31.6,56.6L32.6,56.6M37.4,56.4L38.2,56.4", "none", 1.6)
    g += E(32, 66.4, 4, .8, "none", HL) + E(38.6, 66.4, 4, .8, "none", HL)
    g += P("M30.6,69H34.6M36.4,69H40.6M30,71.4H35.6M37,71.8H41M32.4,74.4H39", "none", .8)
    body = "M38,30C45,31 46.4,39 41.6,45C38.6,48 31,48.4 26,47.4L19.4,50C23.6,45 27.6,38 32,33C34,31 36,30 38,30Z"
    g += P(body, "#fff", W0) + F(body, TH)
    g += P("M33,32.6C30,37 27,42 22.6,48M36,33C34,38 31,43 26.6,47.4M38.6,33.4C37.4,38 35,42.4 31,47.4", "none", HL)
    g += Wt("M39.6,34C42,37 42,41 40,44", .9)
    neck = ("M37,31C35,26 38,22 38,18C38,13 40,9 45,8C47,7.6 49,8.2 50,9.4L62,11.4L50,12.2"
            "C48.6,13 46.6,13.4 44.6,13.4C42.6,15.4 42.4,19 43.4,23C44.4,27 43.4,31 40.6,33Z")
    g += P(neck, "#fff", W0, ' stroke-linejoin="round"')
    g += P("M50,10.8L61,11.4", "none", HL) + F("M44,8.6C46,7.8 48.4,8 49.4,9.2L46,9.6C45,9.6 44.4,9.4 44,8.6Z")
    g += P("M44.4,8.8C40,8.6 36.6,9.6 33.6,12M44.2,9.4C41,9.8 38.6,11 36.6,13", "none", .8)
    g += dot(47.4, 10.4, .6)
    g += P("M43.4,15C42.4,19 42.8,24 41.4,30", "none", .6, ' stroke-dasharray="1.6 1"')
    g += clipped("nk", f'<path d="{neck}"/>', P("M39.4,16C39.4,21 37.8,26 38.6,31M40.6,14C40.4,20 39.2,25 39.8,31.4", "none", HL))
    g += F("M38,18C38,22 36,27 37,31L39,31.6C38,27 39.4,22 39.4,17Z", TH)
    g += P("M40.4,32C41,36 40.4,40 39.2,43M39.4,32.4C39.6,36 38.8,39 37.6,41.6", "none", HL)
    # reeds and cattails in front
    front = "".join(f"M{x},80C{x + 1},70 {x - 1},{62 - (x * 7) % 8} {x - 4},{54 - (x * 3) % 10}" for x in (15, 18, 21, 24, 97, 100, 103, 106))
    g += P(front, "none", .7)
    for x, y in ((18, 50), (23, 55), (99, 50), (104, 55)):
        g += P(f"M{x},{y + 9}V{y + 16}", "none", .6) + P(f"M{x - 1.2},{y}h2.4v8h-2.4Z", TD, HL) + P(f"M{x},{y}v-3", "none", .6)
    g += P("M26,80C28,70 31,66 36,62M94,80C93,72 91,68 88,64M20,80C22,72 20,66 16,62", "none", W0)
    g += rubber_duck(98.6, 63, .9)
    return finish("heron", g, "rope", "A great blue heron in the reeds on the Columbia, a sternwheeler far off")


def v_sky():
    """The sky: a telescope on its tripod under a cross-hatched night, the Milky Way in stipple, the
    Dipper and Cassiopeia, a haloed crescent, a ringed planet and an observatory on the hill."""
    g = ruled(-6, 86, 1.2, sw=.6) + F("M0,0H120V82H0Z", TB)
    mw = "M-6,58C10,46 22,30 40,18C52,10 60,4 70,-4L84,-4C70,8 60,16 50,24C34,36 20,52 6,70Z"
    g += F(mw, "#fff") + F(mw, TS2)
    g += P("M-6,58C10,46 22,30 40,18C52,10 60,4 70,-4", "none", HL, ' stroke-dasharray=".6 1.2"')
    g += P("M84,-4C70,8 60,16 50,24C34,36 20,52 6,70", "none", HL, ' stroke-dasharray=".6 1.2"')
    g += "".join(C(x, y, .45, "#000", None) for x, y in ((30, 34), (44, 20), (22, 44), (56, 10), (36, 28), (16, 52), (48, 18), (62, 6), (26, 40)))
    dip = [(14, 18), (21, 15.6), (27.4, 17), (32.6, 20.4), (33.4, 27.4), (42.6, 28), (42.4, 20.4)]
    g += Wt(poly(dip, False) + f"M{dip[3][0]},{dip[3][1]}L{dip[6][0]},{dip[6][1]}", .6)
    g += "".join(wstar(x, y, 2.4 if i in (1, 6) else 2) for i, (x, y) in enumerate(dip))
    cas = [(52, 9.6), (57, 14), (62, 10.6), (67, 14.6), (72, 9.4)]
    g += Wt(poly(cas, False), .6) + "".join(wstar(x, y, 1.9) for x, y in cas)
    g += wstar(50, 23, 2.8) + C(50, 23, 4.2, "none", .6, ' stroke="#fff" stroke-dasharray=".6 1.2"').replace('stroke="#000" ', '')
    g += "".join(wstar(x, y, r) for x, y, r in ((8, 40, 1.4), (60, 28, 1.3), (76, 30, 1.5), (100, 8, 1.3), (68, 44, 1.3), (84, 50, 1.2), (110, 32, 1.3)))
    g += "".join(C(x, y, .5, "#fff", None) for x, y in ((74, 37), (75.6, 38.4), (77, 36.8), (76, 35.4), (78.2, 38.2), (73.6, 39)))
    # the crescent, haloed
    g += "".join(C(92, 22, r, "none", .6, ' stroke="#fff" stroke-dasharray="1.2 1.8"').replace('stroke="#000" ', '') for r in (14, 16.4))
    g += C(92, 22, 12.2, "#fff", None) + moon(92, 22, 11, 30, True, dark=TS, outline=W1)
    g += P("M92.6,11.4A10.6,10.6 0 0 1 92.6,32.6M95,12.4A9.6,9.6 0 0 1 95,31.6", "none", HL)
    g += C(99.6, 18, 1.2, "none", HL) + C(100.4, 26, .9, "none", HL) + C(97.6, 29, .7, "none", HL)
    # Saturn
    g += C(106, 46, 2.6, "#fff", W0) + P(ell_d(106, 46, 5.4, 1.4, -18), "none", W0) + F("M106,43.4A2.6,2.6 0 0 1 106,48.6Z", TH)
    # the falling star
    g += P("M72,34L54,45", "none", 1.8) + Wt("M72,34L54,45", .6) + wstar(72, 34, 2.4)
    # hills hatched along their contours, firs and the observatory dome
    def hill(x):
        return 64 + 2.4 * math.cos((x - 20) / 18) - (x / 120) * 3
    out, lines = contour_fill(hill, -2, 122, 84, 1.8)
    g += P(out, "#fff", W0) + P(lines, "none", HL)
    g += "".join(fir(x, hill(x) + .6, 8 + (x * 3) % 5, TD) for x in range(70, 92, 5))
    g += P("M95,60V54H109V60Z", "#fff", W0) + cyl_lines(95, 109, 54, 60, 5)
    g += P("M94,54A8,7 0 0 1 110,54Z", "#fff", W1) + F("M102,54A8,7 0 0 1 110,54Z", TH)
    g += P("M98,54A4,7 0 0 1 102,47M106,54A4,7 0 0 0 102,47", "none", HL) + P("M100.6,47.2L102.6,47L103.6,54H100Z", TD, HL)
    g += P("M99,57h2v3h-2Z", TD, HL)
    # the telescope
    x0, y0, x1, y1 = 27, 57, 72, 33
    dx, dy = x1 - x0, y1 - y0
    l = math.hypot(dx, dy)
    nx, ny = -dy / l, dx / l
    def q(t, w):
        return (x0 + dx * t + nx * w, y0 + dy * t + ny * w)
    def seg(t0, t1, w):
        a, b = q(t0, w), q(t1, w)
        return f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}"
    legs = "M47,52L36,77M47,52L48,78M47,52L60,76"
    g += P(legs, "none", 2.4) + P(legs, "none", .6).replace('stroke="#000"', 'stroke="#fff"')
    g += P("M40,66L55,66M41.4,70.4L54.4,70.4", "none", W0)
    g += P(poly([q(.42, -2), q(.42, -5.6), q(.56, -5.6), q(.56, -2)]), "#fff", W0) + P(seg(.45, .53, -3.2) + seg(.45, .53, -4.4), "none", HL)
    g += P(poly([q(0, 2), q(.86, 2.6), q(.86, -2.6), q(0, -2)]), "#fff", W1)
    g += P("".join(seg(.02, .84, w) for w in (-.9, -1.5, -1.9, 1.3)), "none", HL)
    g += P(poly([q(.84, 3.2), q(1, 3.2), q(1, -3.2), q(.84, -3.2)]), "#fff", W1)
    g += P("".join(seg(.85, .99, w) for w in (-1.2, -1.8, -2.4, 1.8)), "none", HL)
    for t in (.1, .3, .62, .8):
        a, b = q(t, 2.4), q(t, -2.4)
        g += P(f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}", "none", W1)
    g += P(poly([q(.5, 3.2), q(.74, 3.2), q(.74, 4.6), q(.5, 4.6)]), "#fff", W0)
    e0 = q(-.02, 0)
    g += P(f"M{n(e0[0])},{n(e0[1])}l-1.4,-5.4", "none", 2.4) + P(f"M{n(e0[0])},{n(e0[1])}l-1.4,-5.4", "none", .6).replace('stroke="#000"', 'stroke="#fff"')
    # the observer's lantern and star book on the grass
    g += P("M18,66H24V72H18Z", "#fff", W0) + P("M18.6,66V72M23.4,66V72", "none", HL) + P("M18,66L21,63.6L24,66M21,63.6V62.4", "none", W0)
    g += C(21, 69, 1, "#000", None) + rays(21, 69, 3.2, 5.6, 10, 180, 360, HL)
    g += P("M60,70L66,68.4L72,70L66,71.6Z", "#fff", W0) + P("M66,68.4V71.6M61.6,70L66,69.2", "none", HL)
    return finish("sky", g, "bead", "A telescope under the stars and a crescent moon")


def v_newspaper():
    """The news: a wooden hand press with carved brackets and a sunburst crest, the morning sheet on its
    tympan, sheets drying on a line, a guilloche wall and a boarded floor."""
    g = F("M0,0H120V70H0Z", TG)
    g += F("M0,70H120V82H0Z", "#fff") + P("M0,70H120", "none", W1)
    g += clipped("fl", '<rect x="0" y="70" width="120" height="12"/>', P("".join(f"M60,52L{x},84" for x in range(-120, 260, 10)), "none", HL))
    g += P("M0,73.6H120M0,78H120", "none", HL)
    # drying line
    g += P("M6,24C12,26 22,26 28,24", "none", HL)
    for x0 in (9, 18):
        g += P(f"M{x0},25.2H{x0 + 7}V35H{x0}Z", "#fff", W0) + P(f"M{x0 + 1},27.6H{x0 + 6}", "none", W0) + P("".join(f"M{x0 + 1},{y}H{x0 + 6}" for y in (29.4, 30.8, 32.2, 33.6)), "none", HL)
        g += P(f"M{x0 + 3.4},23.6V26.4", "none", W1)
    # crest
    crest = "M28,12Q56,0 84,12Z"
    g += P(crest, "#fff", W1) + clipped("cr", f'<path d="{crest}"/>', rays(56, 12, 2, 20, 30, 180, 360, HL, alt=12))
    g += C(56, 12, 3, "#fff", W0) + star(56, 12, 2) + kanok(84, 12, .4, -160, True) + kanok(28, 12, .4, -20)
    # cheeks with wood grain and carved brackets
    for x in (30, 75):
        g += P(f"M{x},12H{x + 7}V70H{x}Z", "#fff", W1)
        g += P("".join(f"M{x + o},14C{x + o + .8},30 {x + o - .6},48 {x + o + .4},68" for o in (1.4, 2.8, 4.2)), "none", HL)
        g += P(f"M{x + 5.6},12V70", "none", HL) + P(f"M{x + 6.2},12V70", "none", HL)
        g += P(f"M{x - 4},68H{x + 11}V72H{x - 4}Z", "#fff", W0) + P(f"M{x - 4},70.4H{x + 11}", "none", HL)
    g += leaf(37, 21, .42, 40) + leaf(75, 21, .42, 140, flip=False)
    g += P("M26,12H86V20H26Z", "#fff", W1) + P("M26,14H86M26,18.6H86", "none", HL)
    g += P("".join(f"M{x},18.6h1.4v1.4h-1.4Z" for x in range(27, 86, 3)), "#fff", HL)
    g += P("M37,33H75V37H37Z", "#fff", W0) + P("M37,34.4H75M37,35.6H75", "none", HL)
    # screw, hose and platen
    g += P("M53,20H59V38H53Z", "#fff", W0) + P("".join(f"M53,{y}L59,{y - 2.4}" for y in range(23, 39, 2)), "none", HL) + cyl_lines(53, 59, 20, 33, 3)
    g += P("M52,38H60V44H52Z", "#fff", W0) + cyl_lines(52, 60, 38, 44, 4) + P("M52,41H60", "none", HL)
    g += P("M40,44H72V48H40Z", "#fff", W1) + P("M40,46.4H72M40,47.2H72", "none", HL)
    g += P("M59,28.6C70,27 84,26 98,22", "none", 1.8) + Wt("M60,28.2C70,26.6 84,25.6 97,22", .6) + mini_ball(98.6, 21.8, 1.8)
    # bed and rails
    g += P("M10,54H108V58H10Z", "#fff", W1) + P("M10,55.6H108M10,56.4H108M10,57.2H108", "none", HL) + P("M14,58V70M104,58V70", "none", W1)
    g += P("M42,52H70V54H42Z", "#fff", HL) + P("M44,52.6H68M44,53.4H68", "none", HL)
    # the morning's sheet raised on its tympan
    sheet = [(84, 53.4), (104, 53.4), (110, 30), (90, 30)]
    g += P(poly([(x + 1.6, y + 1.2) for x, y in sheet]), TH, W0) + P(poly(sheet), "#fff", W1)
    def at(u, v):
        a = (sheet[3][0] + (sheet[2][0] - sheet[3][0]) * u, 30)
        b = (sheet[0][0] + (sheet[1][0] - sheet[0][0]) * u, 53.4)
        return (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v)
    hd = at(.1, .1), at(.9, .1)
    g += P(f"M{n(hd[0][0])},{n(hd[0][1])}L{n(hd[1][0])},{n(hd[1][1])}", "none", W1)
    for c0, c1 in ((.08, .3), (.36, .64), (.7, .92)):
        lines = ""
        for v in [.2 + .065 * i for i in range(12)]:
            if c0 == .36 and v < .5:
                continue
            a, b = at(c0, v), at(c1, v)
            lines += f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}"
        g += P(lines, "none", HL)
    g += P(poly([at(.36, .2), at(.64, .2), at(.64, .46), at(.36, .46)]), TX, HL)
    # stack of fresh copies and the ink balls
    g += P("M10,62H28V70H10Z", "#fff", W0) + P("M10,63.6H28M10,65.2H28M10,66.8H28M10,68.4H28", "none", HL)
    g += P("M12,62C12,57.6 20,57.6 20,62Z", "#fff", W0) + clipped("ib", '<path d="M12,62C12,57.6 20,57.6 20,62Z"/>', ripples(16, 62, 1.6, 1, 1.2, 4))
    g += P("M16,58V54", "none", 1.2) + C(16, 53.6, 1, "#fff", W0)
    g += peek_dog(41, 70.2, .75)
    return finish("newspaper", g, "cart", "A wooden hand press with the morning sheet")


def bull():
    return (P("M1.5,5.5C2,3.5 4,2.6 7,2.8C10,3 12,1.6 14.5,1.4C16.5,1.3 17.6,2.2 18.2,3.6L19.4,3.4C20.6,3.6 21.4,4.6 21.6,6"
              "C21.8,7 21.8,8 21.2,8.6C20.4,9 19.4,8.8 18.8,8.2C18,8.6 17.4,9.2 17.2,9.8L16.6,14H15L14.6,10.6C13.6,10.8 12.6,10.8 11.8,10.6"
              "L11.6,14H10.2L10,10.6C8,10.8 6.5,10.6 5.6,10.2L5.2,14H3.8L3.6,10C2.4,9.6 1.6,8.4 1.5,5.5Z", TX, W0, ' stroke-linejoin="round"')
            + Wt("M3,4.6C6,3.4 10,3.6 14,2.4", .6)
            + P("M18.6,3.4C18,1.6 18.8,.4 20.4,0M19.8,3.4C20.8,2 22.2,1.8 23,.6", "none", .9)
            + P("M1.6,6C.6,7 .4,9.5 .8,11.5", "none", W0) + dot(.8, 11.8, .6) + C(19.8, 5.4, .55, "#fff", None))


def bear():
    return (P("M1,8C1,6.8 2,6 3.4,5.8C4.4,5.2 5,4 6.2,3.6L6.4,2.6C6.8,2 7.8,2.2 7.8,3C9,3 10,3.2 11,2.6C13,1.6 15.6,1.4 17.6,2.2"
              "C20,3.2 21.6,5.6 21.4,8.6C21.2,10.2 20.6,11 20.4,11.4L20.6,14H18.4L18,11.6C17,11.8 16.4,11.6 16,11.2L15.8,14H13.8L13.6,11.4"
              "C11.6,11.8 9.6,11.8 8,11.4L7.8,14H5.8L5.8,11C5,10.6 4.6,10 4.4,9.4C3.6,9.4 2.4,9.6 1.6,9.2C1.2,9 1,8.6 1,8Z", TD, W0, ' stroke-linejoin="round"')
            + Wt("M8,3.4C11,3 13,1.8 17,2.6", .6) + C(4.2, 6.2, .55, "#fff", None) + dot(1, 7.9, .6))


def v_markets():
    """Money and markets: a bull and a bear in balance on an engraved scale, a balloon tied to its finial."""
    g = rays(60, 14, 6, 72, 90, 0, 360, HL, alt=40)
    # balloon
    g += P("M60,13.6C64,10 66,22 74,18C80,15 82,20 88.4,18.6", "none", HL)
    g += P(ell_d(90, 11.4, 5.4, 6.8), "#fff", W0) + clipped("bl", f'<path d="{ell_d(90, 11.4, 5.4, 6.8)}"/>', shade("bs", 90, 11.4, 6.6))
    g += P("M89,18.2L90,19.4L91,18.2Z", "#000", HL) + Wt("M87,7.4C87.6,6.4 88.6,5.8 89.6,5.8", .8)
    # chains and pans
    for bx, x0, x1 in ((22, 9, 35), (98, 85, 111)):
        g += P(f"M{bx},21L{x0 + 1.4},50M{bx},21L{x1 - 1.4},50M{bx},21V44", "none", .8, ' stroke-dasharray="1.2 .7"')
    g += P(f"M8,50H36Q32,57 22,57.4Q12,57 8,50Z", "#fff", W1) + F("M10,52.4H34Q31,57 22,57.4Q13,57 10,52.4Z", TH)
    g += P(f"M84,50H112Q108,57 98,57.4Q88,57 84,50Z", "#fff", W1) + F("M86,52.4H110Q107,57 98,57.4Q89,57 86,52.4Z", TH)
    g += bake(bull(), place(10.4, 36, 1.06), sw_scale=False)
    g += bake(bear(), place(86.6, 36.4, 1.06), sw_scale=False)
    # column and plinth
    g += P("M57.4,26H62.6V64H57.4Z", TV, W0) + P("M55.6,30H64.4V32H55.6ZM55,46H65V48.4H55ZM54.4,60H65.6V63H54.4Z", "#fff", W0)
    g += P("M50,63H70V67H50Z", TH, W0) + P("M44,67H76V71.6H44Z", "#fff", W1) + P("M46,69.2H74", "none", HL, ' stroke-dasharray="1 1"')
    # coins
    for x in (34, 86):
        g += "".join(P(ell_d(x, 70 - i * 1.6, 5, 1.4), "#fff", W0) for i in range(4)) + P(ell_d(x, 63.6, 5, 1.4), TS, W0)
    # beam
    g += P("M20.6,20.2L57,19L63,19L99.4,20.2V21.8L63,23L57,23L20.6,21.8Z", "#fff", W1) + F("M20.6,21L99.4,21V21.8L63,23H57L20.6,21.8Z", TH)
    g += C(20.6, 21, 1.6, TP, W0) + C(99.4, 21, 1.6, TP, W0)
    g += P("M60,21V12.4", "none", 1.2) + pearl(60, 21, 3) + star(60, 21, 1.8) + C(60, 12.4, 1.4, "#fff", W0)
    return finish("markets", g, "cart", "A bull and a bear balanced in a scale, with a helium balloon")


def v_civics():
    """The Oregon State Capitol's gilded pioneer on his fluted drum, a glory behind him."""
    g = rays(60, 18, 8, 70, 100, 180, 360, HL, alt=40) + rays(60, 18, 8, 70, 30, 0, 180, HL)
    g += fir(14, 74, 32) + fir(24, 76, 22) + fir(106, 74, 30) + fir(96, 76, 22)
    # the fluted drum
    g += P("M32,47V70H88V47Z", "#fff", W1)
    fl = "".join(f"M{n(x)},48V70" for x in [32 + 56 * (1 - math.cos(math.pi * i / 32)) / 2 for i in range(1, 32)])
    g += P(fl, "none", HL) + F("M72,48H88V70H72Z", TH) + F("M82,48H88V70H82Z", TX)
    g += P("M32,47C32,44 88,44 88,47C88,50 32,50 32,47Z", "#fff", W1) + F("M32,47C32,50 88,50 88,47V50.6C82,53 38,53 32,50.6Z", TS)
    g += P("M32,50.6C38,53 82,53 88,50.6", "none", W0)
    g += P("M30,70H90V73H30Z", "#fff", W1) + P("M30,71.4H90", "none", HL)
    # lantern and pedestal
    g += P("M48,36V45H72V36Z", "#fff", W0) + P("".join(f"M{x},37V45" for x in range(50, 71, 2)), "none", HL) + F("M65,36H72V45H65Z", TH)
    g += P("M46,36C46,33.4 74,33.4 74,36C74,38.2 46,38.2 46,36Z", "#fff", W0) + P("M54,31H66V34.6H54Z", TS, W0)
    g += P("M52.6,30H67.4V31.4H52.6Z", "#fff", W0)
    # the pioneer: axe on his shoulder, his coat stippled gold, a cloak over his arm
    g += P("M56.6,16.6C55,18 54.6,22 54.8,26.4L57.4,26.8L58,23H62L62.6,26.8L65.2,26.4C65.4,22 65,18 63.4,16.6C62,15.8 58,15.8 56.6,16.6Z", TS, W0)
    g += P("M57.4,26.8L57,30H59.4L59.6,26.9M60.6,26.9L60.8,30H63.2L62.6,26.8", "#fff", W0)
    g += P("M56.6,16.8C54,18 52.4,22 52.8,28L55.4,28.6C55,24 55.4,20 57,18Z", TH, W0)
    g += P("M55.2,25L66.2,8.6", "none", 1.3, ' stroke-linecap="round"') + P("M64.6,8.6L68.8,7.4L69,11.8L66.2,10.8Z", "#fff", W0)
    g += P("M63.4,17C65.4,17.6 66,19.4 64.6,21.4", "none", 1.1)
    g += C(60, 13.4, 2.4, "#fff", W0) + P("M58,14.4C58.4,16.6 61.6,16.6 62,14.4C61,15.4 59,15.4 58,14.4Z", TX, HL) + P("M57.8,12.6C58.4,10.6 61.6,10.6 62.2,12.6", "none", W0)
    g += F("M0,73H120V82H0Z", "#fff") + P("M0,73H120", "none", W0) + F("M0,74.6H120V82H0Z", TS2)
    return finish("civics", g, "bead", "The gilded pioneer atop the Oregon Capitol dome")


def laurel(side):
    """A laurel branch rising from the bottom centre along the oval; side -1 left, 1 right."""
    p0, p1, p2, p3 = (60 - 3 * side, 69.6), (60 - 24 * side, 72), (60 - 40 * side, 64), (60 - 43 * side, 47)
    g = P(f"M{n(p0[0])},{p0[1]}C{n(p1[0])},{p1[1]} {n(p2[0])},{p2[1]} {n(p3[0])},{p3[1]}", "none", W1)
    for i in range(9):
        t = .08 + i * .105
        x, y = bezier(p0, p1, p2, p3, t)
        x2, y2 = bezier(p0, p1, p2, p3, t + .01)
        ang = math.degrees(math.atan2(y2 - y, x2 - x))
        for sgn, f in ((1, TH), (-1, "#fff")):
            g += bake(P("M0,0C1.8,-1.6 4.6,-1.8 7,0C4.6,1.8 1.8,1.6 0,0Z", f, W0), place(x, y, .9, ang - 38 * sgn), sw_scale=False)
        if i % 3 == 1:
            g += dot(x + 2 * side, y + 1, .8)
    return g


def pinwheel(cx, cy, r):
    """Easter egg: the Blazers' pinwheel, two interlocked sets of five stripes."""
    g = ""
    for k in range(5):
        o = (k - 2) * r * .26
        g += f"M{n(cx - r * .9 + o * .3)},{n(cy - r * .2 + o)}L{n(cx + o * .3 - .2)},{n(cy - r * .9 + o)}"
        g += f"M{n(cx + r * .9 - o * .3)},{n(cy + r * .2 - o)}L{n(cx - o * .3 + .2)},{n(cy + r * .9 - o)}"
    return C(cx, cy, r + .9, "#fff", W0) + P(g, "none", .55)


def v_sports():
    """Sports: a basketball and a soccer ball in a laurel, Mount Hood behind."""
    g = sky(6, 48, 9)
    g += hood(60, 46, .78) + P("M0,46C20,43 40,45 60,44C80,43 100,42 120,44V52H0Z", TX, W0)
    g += "".join(fir(x, 46.4 - (x % 3) * .3, 5 + (x * 7) % 4) for x in range(4, 120, 6))
    g += F("M0,51C30,49 90,49 120,51V82H0Z", "#fff") + P("M0,51C30,49 90,49 120,51", "none", W0)
    g += P("M0,55C30,53 90,53 120,55M0,60C30,58 90,58 120,60M0,66C30,64 90,64 120,66", "none", HL)
    g += laurel(-1) + laurel(1)
    # basketball
    bx, by, br = 45, 55, 11.6
    ball = f'<circle cx="{bx}" cy="{by}" r="{br}"/>'
    g += C(bx, by, br, TS2, None) + lat_lines("bl", bx, by, br, 4) + shade("bb", bx, by, br)
    g += P(f"M{bx},{n(by - br)}C{bx - 4},{by - 6} {bx - 4},{by + 6} {bx},{n(by + br)}M{n(bx - br)},{by}C{bx - 6},{by + 1.6} {bx + 6},{by + 1.6} {n(bx + br)},{by}"
           f"M{bx - 8.2},{by - 8.2}C{bx - 4.6},{by - 3} {bx - 4.6},{by + 3} {bx - 8.2},{by + 8.2}M{bx + 8.2},{by - 8.2}C{bx + 4.6},{by - 3} {bx + 4.6},{by + 3} {bx + 8.2},{by + 8.2}", "none", W1)
    g += C(bx, by, br, "none", W1)
    # soccer ball
    sx, sy, sr = 75.4, 57, 10.4
    inner = ""
    pent = [(sx + 3.8 * math.cos(math.radians(-90 + 72 * i)), sy + 3.8 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    inner += F(poly(pent), TD) + P(poly(pent), "none", W0)
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        vx, vy = pent[i]
        ox, oy = sx + 7.6 * math.cos(a), sy + 7.6 * math.sin(a)
        inner += P(f"M{n(vx)},{n(vy)}L{n(ox)},{n(oy)}", "none", W0)
        b = a + math.radians(36)
        cx2, cy2 = sx + 11 * math.cos(b), sy + 11 * math.sin(b)
        pp = [(cx2 + 4 * math.cos(b + math.radians(36 + 72 * k)), cy2 + 4 * math.sin(b + math.radians(36 + 72 * k))) for k in range(5)]
        inner += F(poly(pp), TD) + P(poly(pp), "none", W0)
        inner += P(f"M{n(ox)},{n(oy)}L{n(sx + 9.4 * math.cos(a - .3))},{n(sy + 9.4 * math.sin(a - .3))}M{n(ox)},{n(oy)}L{n(sx + 9.4 * math.cos(a + .3))},{n(sy + 9.4 * math.sin(a + .3))}", "none", W0)
    g += C(sx, sy, sr, "#fff", None) + clipped("sb", f'<circle cx="{sx}" cy="{sy}" r="{sr}"/>', inner) + shade("ss", sx, sy, sr, t=TH) + C(sx, sy, sr, "none", W1)
    # ribbon and its badge
    g += P("M55,70L50,75L53,75.6L57,72ZM65,70L70,75L67,75.6L63,72Z", TH, W0)
    g += pinwheel(60, 69.6, 3.2)
    return finish("sports", g, "rope", "A basketball and a soccer ball in laurels, Mount Hood behind")


def v_jazz():
    """Music and shows: the kit's kick drum with the dog on its head, a ride, a bass scroll and a record."""
    g = F("M0,0H120V82H0Z", TG)
    # the record, behind
    rx_, ry_ = 86, 24
    g += C(rx_, ry_, 17.4, TX, W1)
    g += "".join(C(rx_, ry_, r, "none", .5).replace('stroke="#000"', 'stroke="#fff"') for r in (8.4, 10, 11.6, 13.2, 14.8, 16.2))
    g += Wt(f"M{rx_ - 12},{ry_ - 7}A14,14 0 0 1 {rx_ - 3},{ry_ - 13.6}", 1.6) + Wt(f"M{rx_ + 12},{ry_ + 7}A14,14 0 0 1 {rx_ + 3},{ry_ + 13.6}", 1.2)
    g += C(rx_, ry_, 6, "#fff", W0) + C(rx_, ry_, 4.6, "none", HL) + P(f"M{rx_ - 3},{ry_ - 1.6}H{rx_ + 3}M{rx_ - 2.4},{ry_ + 2}H{rx_ + 2.4}", "none", HL) + dot(rx_, ry_, .8)
    # notes
    g += P("M44,16v-7l6,-1.5v7", "none", W0) + E(42.8, 16.2, 1.6, 1.1, "#000", None) + E(48.8, 14.8, 1.6, 1.1, "#000", None)
    g += P("M58,22v-6", "none", W0) + E(56.8, 22.2, 1.6, 1.1, "#000", None) + P("M58,16c1,1 3,1.6 2.6,4", "none", W0)
    # bass scroll and pegbox
    g += P("M21.4,24C22,36 23.4,48 24,58H31C31.6,48 32.6,36 33.2,24Z", "#fff", W1) + F("M30.4,26C30.6,36 30,48 29.8,56H31C31.6,48 32.6,36 33.2,24Z", TH)
    g += P("M25,28C25.4,38 25.8,46 26,54H29C29.2,46 29.6,38 30,28Z", TD, W0)
    for y in (32, 40, 48):
        g += P(f"M22.4,{y}H17.6", "none", 1.2) + P(ell_d(15.4, y, 2.4, 1.6), TH, W0) + C(27.5, y + 1.6, .9, "#fff", HL)
    g += P("M24,58L27,82H35L31,58Z", "#fff", W0) + P("M25.6,58L28.6,82H33.4L29.4,58Z", TD, HL)
    g += Wt("M26.6,58.4L29.8,82M27.6,58.4L30.8,82M28.6,58.4L31.8,82", .45)
    g += C(27.2, 18.4, 7, "#fff", W1) + F(f"M20.2,18.4A7,7 0 0 0 34.2,18.4Z", TH)
    g += P(spiral(27.2, 18.4, 1, 6.2, 2.2, 160, 70), "none", W1) + P(spiral(27.2, 18.4, .8, 4.4, 1.7, 200, 50), "none", HL)
    g += C(27.2, 18.4, 1.3, "#000", None)
    # ride cymbal
    g += P("M98,40V73M98,66L92,73M98,66L104,73", "none", W0)
    g += P(ell_d(98, 40, 16, 3.4, -8), "#fff", W0) + P(ell_d(98, 40, 12, 2.5, -8), "none", HL) + P(ell_d(98, 40, 8, 1.7, -8), "none", HL)
    g += F("M82.6,41.6C88,44.4 104,43 112.6,36.2C110,40.4 98,44.6 82.6,41.6Z", TH)
    g += P(ell_d(98, 40, 3, 1.2, -8), TS, HL)
    # kick drum
    kx, ky = 58, 52
    g += P(f"M{kx - 12},{ky + 14}L{kx - 18},{ky + 21}M{kx + 12},{ky + 14}L{kx + 18},{ky + 21}", "none", W1)
    g += C(kx, ky, 18, TH, W1) + C(kx, ky, 15.6, "#fff", W0)
    g += "".join(dot(kx + 16.8 * math.cos(a), ky + 16.8 * math.sin(a), .9) for a in [i * math.pi / 5 + .3 for i in range(10)])
    g += C(kx, ky, 9.6, "none", W1) + C(kx, ky, 8.6, "none", HL, ' stroke-dasharray="1 1.6"')
    dog = bake(subj_dog_head(), place(kx - 20 * .4 - .8, ky - 20 * .4 - 1.2, .4))
    g += clipped("kd", f'<circle cx="{kx}" cy="{ky}" r="8.2"/>', dog)
    g += "".join(star(kx + 12.2 * math.cos(a), ky + 12.2 * math.sin(a), 1.3) for a in (math.pi * 1.25, math.pi * 1.75))
    g += glyph("P", kx - 1.4, ky + 9.7, 2.8, .55)
    g += P(f"M{kx - 5},{ky + 18}H{kx + 5}V{ky + 21}H{kx - 5}Z", TX, W0)
    g += F("M0,73H120V82H0Z", "#fff") + E(60, 74.4, 48, 3.6, TP, W0)
    return finish("jazz", g, "bead", "A drum kit with a dog on the kick drum, a ride cymbal, a bass scroll and a record")


def reel(cx, cy, r):
    g = C(cx, cy, r, "#fff", W1) + C(cx, cy, r - 1.4, "none", HL)
    for i in range(5):
        a = math.radians(i * 72 - 90)
        g += C(cx + r * .56 * math.cos(a), cy + r * .56 * math.sin(a), r * .24, TD, W0)
    g += C(cx, cy, r * .16, "#fff", W0) + dot(cx, cy, r * .06)
    return g


def v_screen():
    """On screen: a projector with its two reels throwing a beam onto a screen in the dark."""
    g = F("M0,0H120V82H0Z", TX)
    lens = (49, 50.4)
    scr = [(96, 16), (110, 10), (110, 74), (96, 66)]
    g += F(f"M{lens[0]},{lens[1] - 2}L96,16V66L{lens[0]},{lens[1] + 2}Z", "#fff")
    g += P("".join(f"M{lens[0]},{lens[1]}L96,{y}" for y in range(18, 66, 4)), "none", HL, ' stroke-dasharray="3 2"')
    g += P(f"M{lens[0]},{lens[1] - 2}L96,16M{lens[0]},{lens[1] + 2}L96,66", "none", W0)
    g += "".join(dot(x, y, .45) for x, y in ((60, 46), (66, 54), (72, 40), (78, 58), (84, 34), (70, 49), (88, 62), (62, 51)))
    g += P(poly(scr), "#fff", W1) + P(poly([(97.6, 18), (108.4, 13), (108.4, 71), (97.6, 64)]), "none", HL)
    g += bake(hood(0, 0, .14), Aff(1, -.3, 0, 1, 103, 49.6), sw_scale=False)
    g += P("M98,52L108.4,48.6", "none", HL)
    # table
    g += P("M8,60H48V62.6H8Z", "#fff", W0) + P("M12,62.6L8,82M44,62.6L48,82M28,62.6V82", "none", 1.4)
    # projector
    g += P("M14,44H42V60H14Z", "#fff", W1) + F("M14,52H42V60H14Z", TH) + P("M17,47H30V50H17Z", TS, HL)
    g += P("M42,46.4H49V54.4H42Z", "#fff", W0) + P("M44,46.4V54.4M46.4,46.4V54.4", "none", HL)
    g += P("M20,44L22,30M36,44L36,27", "none", W1)
    g += reel(36, 26, 9) + reel(22, 30, 11.4)
    g += P("M11,32C10,40 12,46 16,46M47,26C48,34 46,42 42,46", "none", W0)
    # film strip curling across the floor
    curve = ((4, 72), (30, 66), (60, 80), (96, 72))
    outline, L, R, Cn = offset_band(curve, lambda t: 5.4, 30)
    g += P(outline, "#fff", W0)
    g += "".join(F(f"M{n(x - .6)},{n(y - .6)}h1.2v1.2h-1.2Z") for x, y in [((a[0] * .75 + c[0] * .25), (a[1] * .75 + c[1] * .25)) for a, c in zip(L, Cn)])
    g += "".join(F(f"M{n(x - .6)},{n(y - .6)}h1.2v1.2h-1.2Z") for x, y in [((a[0] * .75 + c[0] * .25), (a[1] * .75 + c[1] * .25)) for a, c in zip(R, Cn)])
    g += P("".join(f"M{n(L[i][0] * .5 + Cn[i][0] * .5)},{n(L[i][1] * .5 + Cn[i][1] * .5)}L{n(R[i][0] * .5 + Cn[i][0] * .5)},{n(R[i][1] * .5 + Cn[i][1] * .5)}" for i in range(0, 31, 3)), "none", HL)
    # the 4K disc, glinting
    g += C(64, 64.4, 4.6, "#fff", W0) + C(64, 64.4, 4, "none", HL, ' stroke-dasharray=".8 1.2"')
    g += P("M62.6,62.6L61.6,64.6H63.4M62.9,62.4V66M64.4,62.4V66M66,62.4L64.4,64.2L66,66", "none", .45)
    g += star(67.6, 60.6, 2.6)
    return finish("screen", g, "cart", "A film reel and projector throwing a beam")


def stag(x, y, s=1.0):
    """The White Stag, leaping left: forelegs tucked, hind legs thrown back, a full rack of antlers."""
    g = (P("M5,6.4C8,4.6 14,4.4 18,5C20,5.4 21.4,6.4 21.6,7.6L25.6,10.4L25,11.2L20.4,9.4L24.4,13.2L23.6,13.8L18.4,10"
           "C15,10.6 11,10.6 8.4,9.8L5.6,11.6L3.4,13.4L2.8,12.8L4.6,11L3.6,9.8L1.4,11L1,10.4L4,8.4C3.6,7.8 3.6,7 4,6.6Z", "#fff", .8, ' stroke-linejoin="round"')
         + P("M5.4,6.8C4.4,5 3.6,3.6 3,2.6L.4,2.8L.2,2L2.6,.6C3.6,.2 4.6,.6 5,1.4C5.6,3 7,4.6 8.4,5.4", "#fff", .8, ' stroke-linejoin="round"')
         + P("M4.6,1.2L6.4,.2L5.6,1.8", "#fff", .6)
         + P("M3.8,.6C4.6,-2 6.6,-4 9.4,-4.6M5,-1.8L4.2,-4.2M6.4,-3.2L6.2,-5.6M7.8,-4L8.6,-6.2"
             "M3.2,.6C2.8,-1.6 1.6,-3 .2,-3.4M1.8,-2.4L1.4,-4.2M.9,-3L-.6,-2.6", "none", .8, ' stroke-linecap="round"')
         + P("M21.4,6.6L23,5.2", "none", .9) + dot(2.4, 1.8, .4)
         + P("M9,6C12,5.2 15,5.2 18,6M17,8.4C18.6,7.6 20,7.6 21,8.2", "none", HL))
    return bake(g, place(x, y, s), sw_scale=False)


def v_portland():
    """Around Portland: the St. Johns Bridge's Gothic towers, the White Stag sign on an Old Town roof."""
    g = sky(6, 46, 9)
    g += birds([(70, 14, .6), (76, 11, .5)])
    g += P("M0,44C20,38 46,36 70,39C90,41 106,36 120,37V54H0Z", TS, W0)
    g += "".join(fir(x, 42 - (x % 13) * .3, 6 + x % 5) for x in range(40, 120, 6))
    def tower(x, top, base):
        h = base - top
        return (P(f"M{x - 3.6},{base}V{top + 7}L{x - 1.8},{top + 3}L{x},{top}L{x + 1.8},{top + 3}L{x + 3.6},{top + 7}V{base}Z", "#fff", W1)
                + P(f"M{x - 2},{base - 4}V{top + 11}Q{x - 2},{top + 8} {x},{top + 6.4}Q{x + 2},{top + 8} {x + 2},{top + 11}V{base - 4}", TD, HL)
                + Wt(f"M{x - 3.6},{top + h * .45}H{x + 3.6}M{x - 3.6},{top + h * .7}H{x + 3.6}", .9))
    tl, tr = 54, 98
    cab = P(f"M30,50Q44,40 {tl},13M{tl},13Q{(tl + tr) / 2},64 {tr},13M{tr},13Q110,34 122,40", "none", W1)
    sus = ""
    for x in range(tl + 4, tr - 2, 3):
        u = (x - tl) / (tr - tl)
        yy = (1 - u) ** 2 * 13 + 2 * (1 - u) * u * 64 + u * u * 13
        sus += f"M{x},{n(yy)}V50"
    g += cab + P(sus, "none", HL)
    g += tower(tl, 12, 56) + tower(tr, 12, 56)
    g += P("M28,50H120", "none", W2) + P("M28,52.4H120", "none", W0)
    g += F("M0,55H120V82H0Z", "#fff") + P("M0,55H120", "none", W0) + water(0, 120, 55, 80)
    # Old Town building and the sign
    g += P("M4,52H40V82H4Z", TH, W0) + P("M4,52H40", "none", W1)
    for r in range(3):
        for c in range(4):
            g += P(f"M{8 + c * 8},{57 + r * 8}h4v5h-4Z", "#fff", HL)
    g += peek_dog(15.4, 70.4, .5)
    g += P("M10,52L12,46M34,52L32,46M16,52L22,46M28,52L22,46", "none", W0)
    g += P("M8,36.6H36V46H8Z", "#fff", W1) + P("M9.6,38.2H34.4V44.4H9.6Z", "none", HL)
    g += P("M11.6,40.4h3m1,0h3m1,0h3m1,0h3m1,0h3M14,42.6h3m1,0h3m1,0h3", "none", .7)
    g += stag(9.6, 27.4, 1.06)
    return finish("portland", g, "rope", "The St. Johns Bridge and the White Stag sign")


def v_almanac():
    """The almanac: an armillary sphere in a guilloche rosette, an hourglass running, the sun and moon
    in the upper corners and a compass rose."""
    g = F("M0,0H120V82H0Z", TG)
    ax, ay, R = 44, 37, 19
    g += C(ax, ay, 29, "#fff", None) + rosette(ax, ay, 12, 15, 16, HL) + C(ax, ay, 28.4, "none", W0) + C(ax, ay, 22, "#fff", W0)
    # sun and moon
    g += C(18, 17, 6.4, "#fff", None) + rays(18, 17, 4.6, 7.6, 16, 0, 360, W0, alt=6.4) + C(18, 17, 3.8, "#fff", W1)
    g += dot(16.8, 16.4, .4) + dot(19.2, 16.4, .4) + P("M16.6,18.4Q18,19.6 19.4,18.4", "none", HL)
    g += C(102, 17, 6, "#fff", None) + moon(102, 17, 4.6, 25, True, dark=TS) + star(108, 23, 1.2)
    # compass rose
    rx_, ry_ = 16, 62
    g += C(rx_, ry_, 6, "#fff", W0) + C(rx_, ry_, 5, "none", HL, ' stroke-dasharray=".3 .9"')
    for i in range(8):
        a = math.radians(i * 45 - 90)
        L_ = 5.6 if i % 2 == 0 else 3.4
        tip = (rx_ + L_ * math.cos(a), ry_ + L_ * math.sin(a))
        s1 = (rx_ + 1.1 * math.cos(a + 1.57), ry_ + 1.1 * math.sin(a + 1.57))
        s2 = (rx_ + 1.1 * math.cos(a - 1.57), ry_ + 1.1 * math.sin(a - 1.57))
        g += F(poly([(rx_, ry_), tip, s1]), "#000") + P(poly([(rx_, ry_), tip, s2]), "#fff", HL)
    # stand
    stand = (f"M{ax - 2},{ay + R}C{ax - 2},{ay + 24} {ax - 5},{ay + 26} {ax - 5},{ay + 29}C{ax - 5},{ay + 31} {ax - 2},{ay + 31} {ax - 2},{ay + 33}"
             f"H{ax + 2}C{ax + 2},{ay + 31} {ax + 5},{ay + 31} {ax + 5},{ay + 29}C{ax + 5},{ay + 26} {ax + 2},{ay + 24} {ax + 2},{ay + R}Z")
    g += P(stand, "#fff", W0) + clipped("st", f'<path d="{stand}"/>', cyl_lines(ax - 5, ax + 5, ay + R, ay + 34, 5))
    g += P(f"M{ax - 10},{ay + 33}H{ax + 10}V{ay + 35.4}H{ax - 10}Z", "#fff", W0) + P(f"M{ax - 10},{ay + 34.2}H{ax + 10}", "none", HL)
    g += P(f"M{ax - 12},{ay + 35.4}H{ax + 12}V{ay + 37}H{ax - 12}Z", TH, W0)
    tilt = -23.5
    g += P(ell_d(ax, ay, 15.6, 5.4, tilt), TS, W0) + P(ell_d(ax, ay, 15.6, 3.8, tilt), "#fff", HL)
    r_ = math.radians(tilt)
    ticks = ""
    for i in range(24):
        a = 2 * math.pi * i / 24
        def pt(rx, ry):
            x, y = rx * math.cos(a), ry * math.sin(a)
            return ax + x * math.cos(r_) - y * math.sin(r_), ay + x * math.sin(r_) + y * math.cos(r_)
        p1, p2 = pt(15.6, 5.4), pt(15.6, 3.8)
        ticks += f"M{n(p1[0])},{n(p1[1])}L{n(p2[0])},{n(p2[1])}"
    g += P(ticks, "none", HL)
    g += P(ell_d(ax, ay, 17, 6.2, 12), "none", W0) + P(ell_d(ax, ay, 6.4, 17, tilt), "none", W0) + P(ell_d(ax, ay, 11, 17, tilt), "none", HL)
    g += C(ax, ay, 4.2, "#fff", W0) + lat_lines("gl", ax, ay, 4.2, 3) + shade("gs", ax, ay, 4.2) + C(ax, ay, 4.2, "none", W0)
    ux, uy = -math.sin(r_), math.cos(r_)
    g += P(f"M{n(ax - ux * 24)},{n(ay - uy * 24)}L{n(ax + ux * 24)},{n(ay + uy * 24)}", "none", W1)
    g += mini_ball(ax - ux * 24.6, ay - uy * 24.6, 1.5) + mini_ball(ax + ux * 24.6, ay + uy * 24.6, 1.5)
    g += P(f"M{ax},{ay}m-{R},0a{R},{R} 0 1 0 {2 * R},0a{R},{R} 0 1 0 -{2 * R},0Zm2.2,0a{R - 2.2},{R - 2.2} 0 1 1 {2 * R - 4.4},0a{R - 2.2},{R - 2.2} 0 1 1 -{2 * R - 4.4},0Z",
           "#fff", W0, ' fill-rule="evenodd"')
    g += P("".join(f"M{n(ax + R * math.cos(a))},{n(ay + R * math.sin(a))}L{n(ax + (R - 2.2) * math.cos(a))},{n(ay + (R - 2.2) * math.sin(a))}"
                   for a in [math.radians(i * 10) for i in range(36)]), "none", HL)
    g += P(f"M{ax},{ay}m-{R - 1.1},0a{R - 1.1},{R - 1.1} 0 1 0 {2 * R - 2.2},0", "none", HL)
    g += P(ell_d(ax, ay + 1, 22, 4.6), "none", 1.8) + P(ell_d(ax, ay + 1, 22, 4.6), "none", .6).replace('stroke="#000"', 'stroke="#fff"')
    g += star(ax, ay - R - 4.4, 2.4)
    # hourglass
    hx = 90
    for y0 in (22, 65):
        g += P(f"M{hx - 12.6},{y0}H{hx + 12.6}V{y0 + 3.4}H{hx - 12.6}Z", "#fff", W1) + P(f"M{hx - 12.6},{y0 + 1.2}H{hx + 12.6}M{hx - 12.6},{y0 + 2.2}H{hx + 12.6}", "none", HL)
    glass = (f"M{hx - 10},25.4C{hx - 10},34 {hx - 1.6},40 {hx - 1.2},45.2C{hx - 1.6},50 {hx - 10},56 {hx - 10},65H{hx + 10}"
             f"C{hx + 10},56 {hx + 1.6},50 {hx + 1.2},45.2C{hx + 1.6},40 {hx + 10},34 {hx + 10},25.4Z")
    g += P(glass, "#fff", W0)
    g += F(f"M{hx - 7.6},35.6C{hx - 5},40 {hx - 1.4},42.8 {hx - 1},44.6H{hx + 1}C{hx + 1.4},42.8 {hx + 5},40 {hx + 7.6},35.6Z", TS)
    g += P(f"M{hx},45.4V61", "none", HL, ' stroke-dasharray=".6 .6"') + F(f"M{hx - 9.4},64.6C{hx - 7},59.6 {hx - 2},57.6 {hx},57.4C{hx + 2},57.6 {hx + 7},59.6 {hx + 9.4},64.6Z", TS)
    g += clipped("hg", f'<path d="{glass}"/>', P("".join(f"M{n(hx + 9 - k * 1.4)},25.4C{n(hx + 9 - k * 1.4)},33 {n(hx + 2.4 - k * .3)},40 {n(hx + 2)},45.2" for k in range(3))
                                                + "".join(f"M{n(hx + 2)},45.2C{n(hx + 2.4 - k * .3)},50 {n(hx + 9 - k * 1.4)},57 {n(hx + 9 - k * 1.4)},65" for k in range(3)), "none", HL))
    g += Wt(f"M{hx - 7},28C{hx - 6.6},32 {hx - 4.4},35 {hx - 3},37", .6)
    for px in (hx - 11.2, hx + 11.2):
        g += P(f"M{n(px - 1)},25.4H{n(px + 1)}V65H{n(px - 1)}Z", "#fff", W0) + cyl_lines(px - 1, px + 1, 25.4, 65, 2)
        g += "".join(mini_ball(px, y, 1.6) for y in (30, 45.2, 60))
    g += star(hx, 16, 2.4) + star(hx - 7, 12, 1.4) + star(hx + 7, 12, 1.4)
    return finish("almanac", g, "cart", "An armillary sphere with an hourglass")


def v_science():
    """Science: an atom ringed in contour ground, a brass microscope, a flask, a fern uncurling."""
    ax, ay = 34, 27
    g = ripples(ax, ay, 21, 13, 1.8, 26)
    g += F("M0,70H120V82H0Z", "#fff") + P("M0,70H120", "none", W1)
    g += P("".join(waves_d(0, 120, y, .25, 22, y * 3) for y in (72, 74, 76, 78)), "none", HL)
    g += C(ax, ay, 19.4, "#fff", None) + C(ax, ay, 19.4, "none", W0, ' stroke-dasharray=".6 1.8"') + C(ax, ay, 20.6, "none", HL)
    for rot in (0, 60, 120):
        g += P(ell_d(ax, ay, 17, 5.6, rot), "none", W1) + P(ell_d(ax, ay, 17, 5.6, rot), "none", .6).replace('stroke="#000"', 'stroke="#fff"')
        g += P(ell_d(ax, ay, 15.6, 4.6, rot), "none", HL)
    for rot, t in ((0, .6), (60, 2.4), (120, 4.2)):
        r_ = math.radians(rot)
        x, y = 17 * math.cos(t), 5.6 * math.sin(t)
        g += mini_ball(ax + x * math.cos(r_) - y * math.sin(r_), ay + x * math.sin(r_) + y * math.cos(r_), 1.6, "#fff", TD)
    for i, (dx, dy) in enumerate(((0, 0), (2, -1), (-2, 1), (1.4, 1.8), (-1.2, -2), (2.2, 1), (-2.2, -.6))):
        g += mini_ball(ax + dx, ay + dy, 1.8, "#fff", TD if i % 2 else TH)
    g += "".join(wstar(x, y, 1.2) for x, y in ((14, 12), (54, 10), (56, 42)))
    # a benzene ring
    hexa = [(102 + 4 * math.cos(math.radians(30 + 60 * i)), 30 + 4 * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    g += C(102, 30, 5.6, "#fff", None) + P(poly(hexa), "none", W0) + C(102, 30, 2.4, "none", HL)
    # microscope
    g += P("M72,72H104C106,72 106,67.6 104,67.6H72C70,67.6 70,72 72,72Z", "#fff", W1)
    g += P("M71.4,69.4H104.6M71.2,70.8H104.8", "none", HL)
    g += P("M92,55H97V67.6H92Z", "#fff", W0) + cyl_lines(92, 97, 55, 67.6, 4)
    g += mini_ball(86.6, 61, 3) + C(86.6, 61, 2, "none", HL) + P("M89.6,61H92", "none", W0)
    g += P("M71,52H100V55.4H71Z", "#fff", W1) + P("M71,54.2H100", "none", HL) + P("M74,51.4H79M90,51.4H95", "none", W0)
    g += P("M80,51.2H90V52H80Z", "#fff", HL) + C(85, 51.6, .4, "#000", None)
    arm = "M95,55C102,46 102,34 93,27L89.6,30.2C96.6,36 96.6,46 91.4,53Z"
    g += P(arm, "#fff", W0) + P("M94,53.4C99.6,46 99.6,35 92.2,28.6M96,53.8C101,46 101,35 93.4,27.8", "none", HL)
    g += P("M83.4,16H90.2V47H83.4Z", "#fff", W1) + cyl_lines(83.4, 90.2, 16, 47, 6) + P("M83.4,22H90.2M83.4,40H90.2", "none", W0)
    g += P("M81.6,11.6H92V16H81.6Z", "#fff", W0) + cyl_lines(81.6, 92, 11.6, 16, 5) + P("M83,9H90.6V11.6H83Z", TS, W0)
    g += P("M84.6,47H89V51.2H84.6Z", "#fff", W0) + cyl_lines(84.6, 89, 47, 51.2, 3)
    g += C(94.2, 33, 3.4, "#fff", W0) + C(94.2, 33, 2.4, "none", HL, ' stroke-dasharray=".6 .9"') + C(94.2, 33, .8, "#000", None)
    # flask
    fl = "M59.4,50H64.6V56.6L71,69.4H53Z"
    g += P(fl, "#fff", W0) + clipped("fk", f'<path d="{fl}"/>', F("M50,62H74V72H50Z", TH) + P("M53,62.4H71", "none", HL))
    g += P("M66.6,58L70,66M65.6,58.6L68.4,66", "none", HL) + Wt("M57.4,63L55.4,67.4", .6)
    g += "".join(C(x, y, r, "#fff", HL) for x, y, r in ((61, 65, .8), (63.4, 66.6, .6), (62, 60, .5), (63, 56, .4), (61.8, 53, .5)))
    g += P("M58.8,48.4H65.2V50H58.8Z", TD, HL)
    # fern
    curve = ((14, 78), (16, 62), (32, 52), (56, 54))
    g += P("M14,78C16,62 32,52 56,54", "none", W1)
    for i in range(16):
        t = .1 + i * .055
        x, y = bezier(*curve, t)
        x2, y2 = bezier(*curve, t + .01)
        ang = math.degrees(math.atan2(y2 - y, x2 - x))
        ln = 9 * (1 - t) + 1.6
        for sgn in (1, -1):
            g += bake(P(f"M0,0C{n(ln * .3)},-1.6 {n(ln * .7)},-1.6 {n(ln)},0C{n(ln * .7)},1.2 {n(ln * .3)},1.2 0,0Z", TH if sgn > 0 else "#fff", HL)
                      + P(f"M.4,0H{n(ln * .8)}", "none", HL), place(x, y, 1, ang - 62 * sgn), sw_scale=False)
    g += P(spiral(44, 66, .6, 4.6, 1.3, 90, 30, False), "none", W1) + P("M48.6,66C50,70 50,74 48,80", "none", W1)
    return finish("science", g, "bead", "An atom, a microscope, a flask and a fern")


def v_doodles():
    """Diversions: a poem on an unrolled scroll with its seal, a quill in a cut-glass inkwell, a chess
    knight on its board, spectacles laid by, a guilloche ground behind."""
    g = F("M0,0H120V66H0Z", TG)
    g += F("M0,64H120V82H0Z", "#fff") + P("M0,64H120", "none", W1)
    g += P("".join(waves_d(0, 120, y, .3, 26, y * 5) for y in (66, 68.4, 70.8, 73.2, 75.6)), "none", HL)
    # scroll
    g += P("M14,16H52V64H14Z", "#fff", W0) + F("M14,16.8H52V19H14Z", TS2) + F("M14,61H52V63.4H14Z", TS2)
    for y in (14, 64):
        g += P(f"M12,{y - 2.6}H54V{y + 2.6}H12Z", "#fff", W1) + P(f"M12,{y + .6}H54M12,{y + 1.4}H54M12,{y + 2}H54", "none", HL)
        g += C(12, y, 2.6, "#fff", W0) + P(spiral(12, y, .3, 2.2, 1.6, 0, 26), "none", HL)
        g += C(54, y, 2.6, "#fff", W0) + P(spiral(54, y, .3, 2.2, 1.6, 180, 26), "none", HL)
    g += P("M22,21.6C26,20.2 30,22.8 34,21.2C38,19.8 42,22.2 44,21.2", "none", W1)
    g += P("M16.6,24.6H23.4V31.4H16.6Z", "#fff", W0) + F("M17.4,25.4H22.6V30.6H17.4Z", TH)
    g += P("M18.4,30L20,26L21.6,30M18.9,28.6H21.1", "none", W0, ' stroke-linecap="round"') + kanok(23.6, 31.2, .18, -30)
    verse, y = "", 27.4
    for i in range(10):
        if i in (4, 8):
            y += 1.8
            continue
        x0 = 25 if y < 32 else (18 if i % 4 else 21)
        x1 = 48 - (i * 7) % 9
        verse += f"M{x0},{n(y)}" + "".join("q.8,-1 1.6,0t1.6,0" for _ in range(int((x1 - x0) / 3.2)))
        y += 3.4
    g += P(verse, "none", HL)
    g += P("M28,58.6h10", "none", HL) + kanok(36, 59, .22) + kanok(30, 59, .22, flip=True)
    # ribbon and wax seal
    g += P("M38,66.6L36,74L38.4,72.6L39.6,74.6L40,66.6Z", TH, HL) + P("M41,66.6L42.6,73.4L43.6,71.4L45.4,72.4L43,66.6Z", "#fff", HL)
    g += P("M36,67.6C36,64.4 44,64.4 44,67.6C44,70.6 36,70.6 36,67.6Z", TD, W0) + star(40, 67.6, 1.6)
    # spectacles
    g += P(ell_d(22, 72, 3.2, 1.5) + ell_d(30, 72, 3.2, 1.5), "#fff", W0) + P("M25.2,71.6Q26,70.8 26.8,71.6M18.8,71.6L13,70M33.2,71.6L36,70.4", "none", HL)
    g += Wt("M20,71.2L21.4,70.8M28,71.2L29.4,70.8", .6)
    # chessboard under the knight
    bd = [(80, 65.4), (114, 65.4), (118, 74), (77, 74)]
    g += P(poly(bd), "#fff", W0)
    for i in range(6):
        for j in range(2):
            if (i + j) % 2:
                u0, u1, v0, v1 = i / 6, (i + 1) / 6, j / 2, (j + 1) / 2
                def at(u, v):
                    return (bd[0][0] + (bd[1][0] - bd[0][0]) * u + ((bd[3][0] + (bd[2][0] - bd[3][0]) * u) - (bd[0][0] + (bd[1][0] - bd[0][0]) * u)) * v,
                            65.4 + 8.6 * v)
                g += F(poly([at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)]), TD)
    # inkwell and quill
    qx0, qy0, qx1, qy1 = 66, 58, 92, 8
    dx, dy = qx1 - qx0, qy1 - qy0
    l = math.hypot(dx, dy)
    nx, ny = -dy / l, dx / l
    def q(t, w):
        return (qx0 + dx * t + nx * w, qy0 + dy * t + ny * w)
    def wv(t):
        return 0 if t < .3 else 6 * math.sin(math.pi * (t - .3) / .74) ** .7
    left = [q(t / 30, wv(t / 30)) for t in range(9, 31)]
    right = [q(t / 30, -.55 * wv(t / 30)) for t in range(9, 31)]
    g += P(poly([q(.3, 0)] + left + right[::-1]), "#fff", W0)
    barbs = ""
    for i in range(10, 30):
        t = i / 30
        a, b = q(t, 0), q(t + .05, wv(t + .05) * .98)
        c = q(t + .04, -.55 * wv(t + .04) * .98)
        barbs += f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}M{n(a[0])},{n(a[1])}L{n(c[0])},{n(c[1])}"
    g += P(barbs, "none", HL)
    for t0, t1 in ((.52, .56), (.74, .77)):
        a, b = q(t0, 0), q(t1, wv(t1))
        g += Wt(f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}", .6)
    a, b = q(0, 0), q(1, 0)
    g += P(f"M{n(a[0])},{n(a[1])}L{n(b[0])},{n(b[1])}", "none", W1)
    well = "M58,72H74L72.6,62C72.4,60.4 71,59.6 69.6,59.6H62.4C61,59.6 59.6,60.4 59.4,62Z"
    g += P(well, "#fff", W1) + clipped("iw", f'<path d="{well}"/>', cyl_lines(58, 74, 59, 72, 6) + cyl_lines(58, 74, 59, 72, 2, -1)
                                                + P("M58,64.6H74M58,68H74", "none", HL))
    g += P("M63,56.6H69V59.6H63Z", "#fff", W0) + P("M64.6,56.6V59.6M67.4,56.6V59.6", "none", HL)
    # knight
    kn = ("M92,64C92,58 90,54 89.6,50C89.4,48 88,47 86,47C84.6,46.6 84,45.4 84.6,44C85.6,42 88,39 90,37C91,36 92,35 93,34.4L94,31.6L95.6,33.6"
          "C99,34 103,37 104.6,42C106,47 106,54 104.8,58C104,61 104,63 104.6,64Z")
    g += P(kn, "#fff", W1, ' stroke-linejoin="round"')
    g += clipped("kn", f'<path d="{kn}"/>', P("".join(f"M{n(96 + k * 1.5)},{n(34 + k * .3)}C{n(100 + k * 1.2)},{n(38 + k * .2)} {n(102 + k)},44 {n(101 + k)},{66}" for k in range(-1, 6)), "none", HL)
                 + P("M88,50C90,52 91,58 91,64M86.4,46.4C88.6,47 90.4,48.6 91,51", "none", HL))
    g += P("M95.6,35.4C97,40 98,44 98.6,50M97.4,36C99,40 100.4,44 100.6,48", "none", W0)
    g += dot(89.4, 40.6, .7) + P("M85.6,44.4L86.6,44.2M86,47C87.6,47.4 89,48.4 89.6,50", "none", HL)
    g += P("M88,64H108V67H88Z", "#fff", W1) + cyl_lines(88, 108, 64, 67, 5)
    g += P("M85.6,67H110.4C111.4,67.6 111.4,70 110.4,70.4H85.6C84.6,70 84.6,67.6 85.6,67Z", "#fff", W1) + cyl_lines(85, 111, 67.4, 70, 6)
    g += P("M90,62.4H106", "none", W0)
    return finish("doodles", g, "cart", "A quill, a poem scroll and a chess knight")


def butterfly(x, y, s=1.0):
    g = (P("M0,0C-2,-4 -6,-5 -6.4,-2C-6.6,0 -3,0.4 0,0ZM0,0C2,-4 6,-5 6.4,-2C6.6,0 3,.4 0,0Z", "#fff", W0)
         + P("M0,0C-2,1 -4.6,3 -3.4,4.4C-2.2,5 -.6,2.4 0,0ZM0,0C2,1 4.6,3 3.4,4.4C2.2,5 .6,2.4 0,0Z", TH, W0)
         + C(-4, -2.2, .7, "#000", None) + C(4, -2.2, .7, "#000", None)
         + P("M0,-1.2V2.6M0,-1.2L-1,-3.4M0,-1.2L1,-3.4", "none", W0))
    return bake(g, place(x, y, s), sw_scale=False)


def v_delights():
    """Delights: a banded cornucopia spilling small wonders in a glory: fruit and flowers, a watch, a key,
    a butterfly, a shell, a bell, a moon and stars."""
    g = rays(58, 50, 8, 70, 72, 180, 360, HL, alt=34) + rays(58, 50, 8, 70, 24, 0, 180, HL)
    g += F("M0,70H120V82H0Z", "#fff") + P("M0,70H120", "none", W1) + ruled(71, 82, 1.2, sw=.3)
    g += "".join(star(x, y, r) for x, y, r in ((70, 14, 2.4), (82, 22, 1.6), (96, 18, 2.8), (60, 22, 1.4), (106, 30, 1.6), (88, 10, 1.4), (40, 12, 1.6)))
    # horn, its bands and the contour hatch that wraps it
    curve = ((14, 16), (12, 40), (30, 56), (56, 50))
    outline, L, R, Cn = offset_band(curve, lambda t: .6 + 22 * t ** 1.5)
    g += P(outline, "#fff", W1)
    wrap = ""
    for i in range(6, 40):
        a, b, c = L[i], R[i], Cn[i]
        wrap += f"M{n(c[0])},{n(c[1])}Q{n((c[0] + b[0]) / 2 + 1)},{n((c[1] + b[1]) / 2 + .8)} {n(b[0])},{n(b[1])}"
    long_ = "".join(poly([(r[0] * (1 - f) + c[0] * f, r[1] * (1 - f) + c[1] * f) for r, c in zip(R[8:], Cn[8:])], False) for f in (.2, .45))
    g += P(wrap, "none", HL) + P(long_, "none", HL)
    for i in range(6, 40, 4):
        a, b = L[i], R[i]
        g += P(f"M{n(a[0])},{n(a[1])}Q{n(Cn[i][0] + 1.6)},{n(Cn[i][1] + 1.2)} {n(b[0])},{n(b[1])}", "none", W1)
    for i in range(8, 40, 4):
        a, b = L[i], R[i]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        g += dot(m[0] - (b[0] - a[0]) * .2, m[1] - (b[1] - a[1]) * .2, .6)
    g += C(14.6, 12.8, 3.4, "#fff", W0) + P(spiral(14.6, 12.8, .6, 3, 1.4, 90, 26), "none", W0)
    # a ribbon round the narrow end
    rb = L[12], R[12]
    g += P(f"M{n(rb[0][0])},{n(rb[0][1])}L{n(rb[1][0])},{n(rb[1][1])}", "none", 1.8)
    g += P(f"M{n(rb[1][0])},{n(rb[1][1])}C{n(rb[1][0] - 2)},{n(rb[1][1] + 6)} {n(rb[1][0] + 4)},{n(rb[1][1] + 8)} {n(rb[1][0])},{n(rb[1][1] + 13)}L{n(rb[1][0] + 2)},{n(rb[1][1] + 11)}L{n(rb[1][0] + 3)},{n(rb[1][1] + 13)}C{n(rb[1][0] + 6)},{n(rb[1][1] + 8)} {n(rb[1][0] + 1)},{n(rb[1][1] + 5)} {n(rb[1][0] + 1.4)},{n(rb[1][1])}Z", TH, W0)
    mx, my = Cn[40]
    g += P(ell_d(mx, my, 4.4, 11, 10), TD, W1) + P(ell_d(mx, my, 3.2, 9.6, 10), "none", .6).replace('stroke="#000"', 'stroke="#fff"')
    # the spill
    gr = [(62, 58), (66, 58.4), (70, 59), (64, 62), (68, 62.4), (66, 66), (60.4, 61.6)]
    g += "".join(mini_ball(x, y, 2.2) for x, y in gr) + P("M64,55.6C64,54 65,53 67,52", "none", W0) + ivy(70, 54, .9, 40)
    g += C(74, 46, 6, "#fff", W0) + lat_lines("ap", 74, 46, 6, 4) + shade("as", 74, 46, 6) + C(74, 46, 6, "none", W0)
    g += P("M74,40.2C74,38.6 74.6,37.6 75.6,37", "none", W0) + ivy(75.6, 40, .8, 50)
    pear = "M86,66C80,66 79,60 82,56.6C84,54.4 84,51 86,50.4C88,51 88,54.4 90,56.6C93,60 92,66 86,66Z"
    g += P(pear, "#fff", W0) + clipped("pr", f'<path d="{pear}"/>', P("".join(f"M{n(86 + k * 1.2)},50C{n(88 + k * 1.2)},56 {n(92 + k)},60 {n(87 + k)},67" for k in range(0, 6)), "none", HL))
    g += P("M86,50.4V48", "none", W0)
    g += C(64, 40, 4.4, "#fff", W0) + P(spiral(64, 40, .4, 3.8, 2.2, 0, 40), "none", HL) + ivy(60, 44, .9, -120)
    g += C(100, 52, 6.4, "#fff", W1) + C(100, 52, 5, "none", HL) + C(100, 52, 5.8, "none", HL, ' stroke-dasharray=".3 .9"')
    g += P("".join(f"M{n(100 + 4.4 * math.cos(a))},{n(52 + 4.4 * math.sin(a))}L{n(100 + 5 * math.cos(a))},{n(52 + 5 * math.sin(a))}" for a in [i * math.pi / 6 for i in range(12)]), "none", HL)
    g += P("M100,52V48.6M100,52L102.6,53.4", "none", W0) + C(100, 44.6, 1.2, "#fff", W0)
    g += P("M100,43.4C96,38 90,44 86,40", "none", W0, ' stroke-dasharray="1.2 .6"')
    g += C(98, 66, 2.2, "none", W1) + C(98, 66, 1, "none", HL) + P("M100.2,66H109M106,66V68.6M108,66V68", "none", W1)
    g += moon(80, 30, 4.4, 20, True, dark=TS2)
    g += butterfly(92, 30, .9)
    sh = "".join(f"M48,68L{n(48 + 4.4 * math.cos(a))},{n(68 - 4.4 * math.sin(a))}" for a in [math.radians(20 + 14 * i) for i in range(11)])
    g += P("M48,68L52.1,66.5A4.4,4.4 0 0 0 43.9,66.5Z", "#fff", W0) + P(sh, "none", HL)
    g += P("M106,36C106,32 110,32 110,36L111,39H105Z", "#fff", W0) + F("M108.4,32.8C110,34 110,36 110,36L111,39H109Z", TH) + C(108, 39.8, .8, "#000", None)
    g += mini_ball(54, 66, 2.6, "#fff", TS) + P("M54,66m-1.6,0h3.2M54,64.4v3.2", "none", HL)
    return finish("delights", g, "bead", "A cornucopia of small wonders")


def v_coast():
    """The beach: a surfer on a breaking wave below Haystack Rock, shells on the sand, a Gearhart cottage."""
    g = sky(6, 44, 8)
    g += birds([(44, 14, .7), (50, 18, .55), (98, 20, .6)])
    g += F("M0,44H120V82H0Z", "#fff") + water(0, 120, 44, 66, tight=2.2)
    rock = "M56,50C57,42 59,32 63,25C65.6,20.6 69,16.6 73.6,16.6C78,16.6 80.6,20 82.4,23C86,29 88.4,38 90.6,50Z"
    g += P(rock, "#fff", W1)
    g += clipped("rk", f'<path d="{rock}"/>', F("M74,10H96V52H74Z", TX) + F("M66,10H74V52H66Z", TH)
                 + P("".join(f"M{x},16C{x - 1},28 {x + 1},40 {x - 2},52" for x in range(58, 92, 3)), "none", HL))
    g += P("M66,22.6C68,19 72,17.6 76,18.4", "none", W0) + "".join(dot(x, y, .5) for x, y in ((70, 19.4), (73, 18.6), (67.6, 21.6)))
    g += P("M92,50L93,42L94.4,40.6L96,44L97,50Z", TX, W0) + P("M98,50L99,46L100.4,47L101,50Z", TX, W0)
    g += P("M50,50.6C60,49.6 80,49.6 104,50.6", "none", W0)
    # the wave
    wave = ("M60,63C52,60 44,50 42,42C40,34 34,30.4 28,31C22,31.6 18,36 18,40C18,43 20.6,45 23,43.2C21.6,41 22.6,38.2 25.4,37.8"
            "C29,37.4 31,41 30.4,46C29.6,53 22,59 6,63Z")
    g += P(wave, "#fff", W1)
    g += clipped("wv", f'<path d="{wave}"/>', "".join(P(f"M{n(4 + k * 3.4)},64C{n(14 + k * 3)},{n(56 - k * .4)} {n(22 + k * 2.4)},50 {n(26 + k * 2.6)},40", "none", HL) for k in range(7))
                 + F("M30,40H60V66H30Z", TH))
    g += P("M23,43.2C22,41 23,38.4 25.6,38C28,37.8 29.6,40.6 29.4,44C27.4,46 24.6,45.6 23,43.2Z", TD, HL)
    g += "".join(C(x, y, r, "#fff", HL) for x, y, r in ((18, 34, .8), (16, 37.6, .6), (21.4, 30.6, .7), (25, 28.6, .6), (14.6, 33, .5), (30, 29.4, .5)))
    # surfer
    g += P("M10.6,56.4L23,51.6", "none", 1.8, ' stroke-linecap="round"')
    g += P("M15.6,53.6L17.4,49.6L19.4,53M17.4,49.6L18.4,46M15.6,46.6L18.4,46.4L21.6,44.6", "none", .9, ' stroke-linecap="round"') + dot(18.6, 44.6, 1)
    # surf foam and sand
    g += P("M0,64C10,62 14,65 22,63C30,61 36,65 46,63C56,61 64,65 76,63C86,61 98,64 120,62", "none", W0)
    g += F("M0,66C30,64 70,65 120,63V82H0Z", TS2) + P("M0,66C30,64 70,65 120,63", "none", W0)
    # dune and cottage
    g += P("M84,64C90,56 102,54 120,55V66H84Z", TS, W0) + grass(88, 116, 57.6, 3.4, 2)
    g += P("M95,56V49.4L100.6,44.4L106.2,49.4V56Z", "#fff", W0) + P("M95,51H106.2M95,52.6H106.2M95,54.2H106.2", "none", HL, ' stroke-dasharray="1.2 .6"')
    g += P("M93.6,50.4L100.6,43.4L107.6,50.4", "none", 1.2) + P("M98.6,49.4H102.6V52.4H98.6Z", "#fff", HL) + P("M102.6,45.4H104.4V43H102.6Z", TX, HL)
    g += peek_dog(88.6, 61.4, .6)
    # shells and a tide pool with a lotus
    sh = "".join(f"M56,71L{n(56 + 4.6 * math.cos(a))},{n(71 - 4.6 * math.sin(a))}" for a in [math.radians(20 + 14 * i) for i in range(11)])
    g += P("M56,71L60.3,69.4A4.6,4.6 0 0 0 51.7,69.4Z", "#fff", W0) + P(sh, "none", HL)
    g += C(68, 68.6, 2.6, "#fff", W0) + P(spiral(68, 68.6, .3, 2.2, 2, 0, 30), "none", HL)
    g += C(79, 67.6, 2.4, "#fff", W0) + P("".join(f"M79,67.6L{n(79 + 1.6 * math.cos(a))},{n(67.6 + 1.6 * math.sin(a))}" for a in [i * 1.2566 - 1.57 for i in range(5)]), "none", HL)
    g += E(38, 68.8, 8, 2.8, "#fff", W0) + P("M31.4,69.4H35M41,68H44.6", "none", HL) + lotus(37.4, 69.2, .24)
    return finish("coast", g, "rope", "A surfer on a breaking wave below Haystack Rock, with shells and a beach house")


def v_dog():
    """The end page: the dog lying on the rug before the fire, a clock and candles on the mantel."""
    g = ruled_v(2, 120, 2.4) + P("M0,22H120", "none", W0)
    fp = P("M30,20H90V68H30Z", "#fff", W0)
    br = ""
    for i, y in enumerate(range(20, 68, 3)):
        br += f"M30,{y}H90" + "".join(f"M{x},{y}v3" for x in range(32 + (i % 2) * 3, 90, 6))
    fp += P(br, "none", HL)
    fp += P("M43,68V42C43,31 77,31 77,42V68Z", TD, W1) + P("M40.6,68V42C40.6,28.4 79.4,28.4 79.4,42V68", "none", W0)
    fp += P("M58,29V33.6M50,30.4L51.6,34.6M66,30.4L64.4,34.6M44.6,34.4L47,37.6M71.4,34.4L69,37.6", "none", W0)
    fp += P("M48,61C46,54 50,52 50,47C53,50 52,54 54,55C54,50 56,45 60,41C60,46 64,49 63,54C65,52 66,50 66,47C70,51 72,56 70,61Z", "#fff", W0)
    fp += P("M54,61C53,57 56,55 56,51C58,54 60,56 59,61ZM61.6,61C61,58 63,56.4 64,54C65.6,57 66,59 65,61Z", TS, HL)
    fp += P("M45,61.4L75,64.6L74.4,67L44.4,63.8Z", TH, W0) + P("M46,66L74,61.4L75,63.4L47,68Z", TX, W0)
    fp += P("M24,16H96V20H24Z", "#fff", W1) + F("M24,18.4H96V20H24Z", TH) + P("M26,20H94V21.4H26Z", TX, HL)
    fp += P("M54,16V11C54,7 66,7 66,11V16Z", "#fff", W0) + C(60, 11.6, 3, "#fff", W0) + P("M60,11.6V9.6M60,11.6L61.6,12.2", "none", .6)
    fp += P("M34,16V12.6H36V16ZM84,16V12.6H86V16Z", TS, HL) + P("M35,12.6C34,11.4 35,10 35,9.6C36,10.4 36,11.6 35,12.6ZM85,12.6C84,11.4 85,10 85,9.6C86,10.4 86,11.6 85,12.6Z", "#fff", HL)
    fp += P("M22,68H98V71H22Z", "#fff", W1) + F("M22,69.6H98V71H22Z", TX)
    g += bake(fp, place(9, 2.6, .85), sw_scale=False)
    # the rug
    g += P(poly([(14, 63.4), (106, 63.4), (116, 80), (4, 80)]), "#fff", W1)
    g += P(poly([(17.4, 65), (102.6, 65), (110, 77), (10, 77)]), TP, W0) + P(poly([(21, 66.6), (99, 66.6), (104, 74.4), (16, 74.4)]), "#fff", W0)
    g += P("".join(f"M{x},70.5l2.2,-2.2l2.2,2.2l-2.2,2.2Z" for x in range(24, 96, 7)), "none", HL)
    g += P("".join(f"M{x},63.4l-.6,-1.4" for x in range(16, 106, 2)), "none", HL)
    # the dog, lying with his head up, paws out toward the warmth
    body = ("M20,67C18,61 22,55 30,54C40,52.6 52,53.4 60,55.4L66,57C68,60.6 70,62.6 74,63.4L86,63.8C88.4,64 88.4,67.2 86,67.4"
            "L72,67.6C60,68.4 40,68.4 28,68.2C23,68.2 20.6,67.8 20,67Z")
    g += P(body, "#fff", W1, ' stroke-linejoin="round"')
    g += F("M20,67C18,61 22,55 30,54C40,52.6 52,53.4 60,55.4L58.6,58C50,57 40,57 32,58.4C26.6,59.4 23,62 22.4,67.4Z", TH)
    g += P("M29,61C33,57.6 40,58.4 41,62.6C41.6,65.4 39.6,67.4 36.4,67.8", "none", W0) + P("M66.6,64.6C70,64 74,64.6 76,65.6M84,64V67.2M81.4,64V67.4", "none", HL)
    g += P("M20.4,66C15,66 12.6,62 14.4,58.6", "none", 1.2)
    g += P("M44,59.4C48,60.6 54,61 58,60.4M46,63C50,64 54,64 58,63.4", "none", HL, ' stroke-dasharray="1.4 1"')
    g += bake(subj_dog_head(), place(50.6, 30.4, .68))
    return finish("dog", g, "bead", "A loyal dog lying by the hearth on a rug")


# ---- ornaments ---------------------------------------------------------------------------------

def _standalone(prefix, w, h, body, label="", dw=None, dh=None):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(w)} {n(h)}" width="{n(dw or w)}" height="{n(dh or h)}" '
           f'{"role=" + chr(34) + "img" + chr(34) + " aria-label=" + chr(34) + label + chr(34) if label else "aria-hidden=" + chr(34) + "true" + chr(34)}>'
           f'<defs>@@DEFS@@</defs>{body}</svg>')
    used = sorted(set(re.findall(r"url\(#Q-(\w+)\)", svg)) & set(_PAT))
    defs = "".join(f'<pattern id="Q-{u}" width="{_PAT[u][0]}" height="{_PAT[u][1]}" patternUnits="userSpaceOnUse">{_PAT[u][2]}</pattern>'
                   for u in used)
    svg = svg.replace("@@DEFS@@", defs).replace('id="Q-', f'id="{prefix}-').replace("url(#Q-", f"url(#{prefix}-")
    assert "transform" not in svg
    return _snap(svg)


def _fleuron_body(cx, cy, seed):
    """A fleuron centred on (cx, cy), about 44 x 14: one of three families, varied by the seed."""
    rng = random.Random(seed)
    kind = seed % 3
    tilt = rng.uniform(-8, 8)
    if kind == 0:  # the Evening's inlay: a pearl lozenge between acanthus leaves
        g = (leaf(cx + 7, cy, .6, -14 + tilt) + leaf(cx - 7, cy, .6, -14 + tilt, flip=True)
             + P(f"M{n(cx - 7)},{n(cy)}L{n(cx)},{n(cy - 5)}L{n(cx + 7)},{n(cy)}L{n(cx)},{n(cy + 5)}Z", TP, W1) + star(cx, cy, 2.4))
    elif kind == 1:  # the tailpiece: two kanok flames leaving a pearl
        g = (kanok(cx + 4, cy + 2, .78, tilt) + kanok(cx - 4, cy + 2, .78, tilt, flip=True)
             + pearl(cx, cy + 1, 3.4) + star(cx, cy + 1, 1.8))
    else:  # a lotus on a bar, flanked by leaves
        g = (P(f"M{n(cx - 20)},{n(cy + 4)}H{n(cx + 20)}", "none", W0)
             + leaf(cx + 6, cy + 3.4, .55, -22 + tilt) + leaf(cx - 6, cy + 3.4, .55, -22 + tilt, flip=True) + lotus(cx, cy + 4, .3))
    k = rng.choice((1, 2, 3))
    g += "".join(dot(cx + sgn * (20 + 2.6 * i), cy + (1 if kind == 1 else 0), max(.5, 1.1 - .25 * i)) for sgn in (1, -1) for i in range(k))
    return g


def fleuron(seed=0):
    """A small fleuron divider (48 x 16)."""
    return _standalone(f"fl{seed}", 48, 16, _fleuron_body(24, 8, seed))


def rule(width=300, seed=0):
    """An ornamental rule: hairlines set with dots and diamonds, curled ends, a fleuron at the centre (14 deep)."""
    rng = random.Random(seed)
    w, y, c = float(width), 7, width / 2
    step = rng.choice((9, 10, 12))
    half = P(f"M{n(c + 25)},{y}H{n(w - 10)}", "none", W0) + P(f"M{n(c + 25)},{y + 2.2}H{n(w - 14)}", "none", HL)
    half += P(f"M{n(w - 10)},{y}c3.5,0 5,-2.6 3.4,-4.2c-1.4,-1.4 -3.4,0 -2,1.4", "none", W0)
    x, i = c + 30, 0
    while x < w - 16:
        if i % 2:
            half += P(f"M{n(x - 2)},{y}L{n(x)},{n(y - 2)}L{n(x + 2)},{y}L{n(x)},{n(y + 2)}Z", "#fff", HL)
        else:
            half += dot(x, y, .9)
        x += step
        i += 1
    body = half + bake(half, Aff(-1, 0, 0, 1, w, 0), sw_scale=False) + _fleuron_body(c, y, seed)
    return _standalone(f"ru{seed}", w, 14, body)


def drop_cap_frame(letter, seed=0, size=64):
    """A boxed foliated initial: acanthus scrolls in hatched line behind a bold Literata letter."""
    rng = random.Random(seed)
    flip = seed % 2 == 1
    g = P("M1.2,1.2H62.8V62.8H1.2Z", "#fff", W2) + P("M3.4,3.4H60.6V60.6H3.4Z", "none", W0, ' stroke-dasharray="1 1.6"')
    g += P("M5,5H59V59H5Z", "#fff", W0)
    fol = F("M5,5H59V59H5Z", TR)
    scrolls = (((8, 58), (6, 34), (22, 26), (30, 36)), ((56, 6), (58, 30), (42, 38), (34, 28)),
               ((58, 58), (44, 60), (38, 50), (46, 44)), ((6, 6), (20, 4), (26, 14), (18, 18)))
    for k, cv in enumerate(scrolls):
        d = f"M{cv[0][0]},{cv[0][1]}C{cv[1][0]},{cv[1][1]} {cv[2][0]},{cv[2][1]} {cv[3][0]},{cv[3][1]}"
        fol += P(d, "none", 2.2) + Wt(d, .8)
        ex, ey = cv[3]
        fol += C(ex, ey, 3.6, "#fff", W0) + P(spiral(ex, ey, .5, 3.2, 1.5, rng.uniform(0, 360), 30), "none", HL)
        cnt = 6 if k < 2 else 3
        for i in range(cnt):
            t = .12 + i * (.72 / cnt)
            x, y_ = bezier(*cv, t)
            x2, y2 = bezier(*cv, t + .01)
            ang = math.degrees(math.atan2(y2 - y_, x2 - x))
            side = 1 if i % 2 else -1
            sc = (.78 if k < 2 else .6) * (1 - .25 * t)
            fol += leaf(x, y_, sc, ang + side * (52 + rng.uniform(-8, 8)), TH, flip=False)
    fol += "".join(kanok(x, y_, .34, r) for x, y_, r in ((7.4, 30, -80), (56.6, 34, 100)))
    fol += star(32, 7.6, 2) + star(32, 56.6, 2) + dot(7.6, 32, .9) + dot(56.4, 32, .9)
    if flip:
        fol = bake(fol, Aff(-1, 0, 0, 1, 64, 0), sw_scale=False)
    g += clipped("fc", '<rect x="5" y="5" width="54" height="54"/>', fol) + P("M5,5H59V59H5Z", "none", W0)
    g += (f'<text x="32" y="47" text-anchor="middle" font-family="Literata, serif" font-weight="700" font-size="44" '
          f'fill="#000" stroke="#fff" stroke-width="3.2" stroke-linejoin="round" paint-order="stroke">{letter}</text>')
    return _standalone(f"dc{seed}", 64, 64, g, label=letter, dw=size, dh=size)


MORNING_VIGNETTES = {
    "sunrise": v_sunrise(),
    "road": v_road(),
    "toddler": v_toddler(),
    "solarpanel": v_solarpanel(),
    "garden": v_garden(),
    "heron": v_heron(),
    "sky": v_sky(),
    "newspaper": v_newspaper(),
    "markets": v_markets(),
    "civics": v_civics(),
    "sports": v_sports(),
    "jazz": v_jazz(),
    "screen": v_screen(),
    "portland": v_portland(),
    "almanac": v_almanac(),
    "science": v_science(),
    "doodles": v_doodles(),
    "delights": v_delights(),
    "coast": v_coast(),
    "dog": v_dog(),
}


ornaments = {"fleuron": fleuron, "rule": rule, "drop_cap_frame": drop_cap_frame}
