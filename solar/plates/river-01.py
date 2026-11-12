"""river-01 "Ship across the way": the Columbia off Sauvie Island, the berth across the river empty,
the last caller (parsed from the page text, e.g. Poavosa Wisdom III) steaming away downriver past
Mt. St. Helens. House codex frame; the ship's name and sailing date are engraved on the pedestal
tablet, THE COLUMBIA on the ribbon. Easter eggs: Parker's dog sitting on the Sauvie bank watching
the ship go, and a "P" house-flag monogram on the ship's funnel."""
import sys
import math
import random
import re
import engraving_codex as C
import engraving_morning as EM

_n, _d = C._n, C._d
PI = math.pi

# ------------------------------------------------------------------------------------------------
# small drawing kit: painter-ordered layers (white fill path + one path per stroke weight)
# ------------------------------------------------------------------------------------------------


class Layer:
    def __init__(self):
        self.white, self.black, self.L = [], [], {.5: [], 1.: [], 1.5: []}

    def fill(self, poly):
        if len(poly) > 2:
            self.white.append(poly)

    def solid(self, poly):
        if len(poly) > 2:
            self.black.append(poly)

    def add(self, w, pls):
        for p in pls:
            if len(p) > 1:
                self.L[w].append(p)

    def svg(self, outline=None):
        o = []
        if self.white:
            d = "".join(_d(p, True, .12) for p in self.white)
            st = f' stroke="#000" stroke-width="{outline}"' if outline else ' stroke="none"'
            o.append(f'<path d="{d}" fill="#fff"{st}/>')
        for w in (.5, 1., 1.5):
            if self.L[w]:
                d = "".join(_d(p, False, .15 if len(p) > 2 else 0) for p in self.L[w])
                o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_n(w)}"/>')
        if self.black:
            o.append(f'<path d="{"".join(_d(p, True, .12) for p in self.black)}" fill="#000" stroke="none"/>')
        return "".join(o)


def clip_half(poly, a, b, c):
    """Sutherland-Hodgman: keep the part of poly where a*x + b*y + c >= 0."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def band(poly, y0, y1):
    return clip_half(clip_half(poly, 0, 1, -y0), 0, -1, y1)


def hatch(poly, ang, pitch, phase=0., inset=0.):
    return C.hatch_poly(poly, ang, pitch, phase, inset) if len(poly) > 2 else []


def ell(cx, cy, rx, ry, n=40, a0=0., a1=2 * PI):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def broken(x0, x1, y, rng, seg=(6, 26), gap=(1.2, 4.), wob=0.):
    out, x = [], x0 + rng.uniform(0, gap[1])
    while x < x1:
        L = rng.uniform(*seg)
        xe = min(x1, x + L)
        if xe - x > .8:
            if wob:
                k = max(2, int((xe - x) / 3))
                out.append([(x + (xe - x) * i / k, y + wob * math.sin((x + (xe - x) * i / k) * .35 + y)) for i in range(k + 1)])
            else:
                out.append([(x, y), (xe, y)])
        x = xe + rng.uniform(*gap)
    return out


# ------------------------------------------------------------------------------------------------
# lettering: the house stroke font plus the capitals it lacks
# ------------------------------------------------------------------------------------------------

_G = dict(EM._G)
_G.update({
    "B": (5.2, [("l", [(.9, 0), (.9, 8)]), ("s", [(.9, 0), (3.2, 0), (4.3, .9), (4.3, 2.9), (3.2, 3.9), (.9, 3.9)]),
                ("s", [(.9, 3.9), (3.5, 3.9), (4.8, 5), (4.8, 6.9), (3.5, 8), (.9, 8)]),
                ("l", [(0, 0), (.9, 0)]), ("l", [(0, 8), (.9, 8)])]),
    "S": (4.8, [("s", [(4.3, 1.1), (3, 0), (1.3, .2), (.5, 1.8), (1.4, 3.4), (3.5, 4.4), (4.5, 6), (3.8, 7.7), (2.2, 8), (.4, 6.9)])]),
    "U": (5.6, [("s", [(.9, 0), (.9, 5.3), (1.5, 7.4), (2.8, 8), (4.1, 7.4), (4.7, 5.3), (4.7, 0)]),
                ("l", [(0, 0), (1.8, 0)]), ("l", [(3.8, 0), (5.6, 0)])]),
    "K": (5.4, [("l", [(.9, 0), (.9, 8)]), ("l", [(4.6, 0), (.9, 4.7)]), ("l", [(2.2, 3.2), (5, 8)]),
                ("l", [(0, 0), (1.8, 0)]), ("l", [(0, 8), (1.8, 8)])]),
    "Y": (5.4, [("l", [(.3, 0), (2.7, 4.2), (5.1, 0)]), ("l", [(2.7, 4.2), (2.7, 8)]), ("l", [(1.8, 8), (3.6, 8)])]),
    "J": (4.4, [("s", [(3.6, 0), (3.6, 5.8), (3, 7.6), (1.8, 8), (.4, 7.2)]), ("l", [(2.6, 0), (4.4, 0)])]),
    "Q": (5.4, [EM._G["O"][1][0], ("l", [(3, 6.2), (5.2, 8.8)])]),
    "Z": (5, [("l", [(.5, 1.2), (.5, 0), (4.6, 0), (.4, 8), (4.7, 8), (4.7, 6.8)])]),
    "-": (3.4, [("l", [(.4, 4.6), (3, 4.6)])]),
    "'": (1.4, [("l", [(.7, 0), (.7, 2.2)])]),
    ",": (1.6, [("l", [(1, 7.4), (.4, 9.2)])]),
})


def text_polys(s, cx, cy, h, track=1.3, shape=None):
    """Glyph polylines centred on (cx, cy), cap height h; shape(x) -> dy bends the baseline."""
    k = h / 8
    adv = lambda c: _G.get(c, _G[" "])[0]
    width = (sum(adv(c) + track for c in s) - track) * k
    x = cx - width / 2
    out = []
    for c in s:
        a, strokes = _G.get(c, _G[" "])
        gx = x + a * k / 2
        dy = shape(gx) if shape else 0.
        for kind, pts in strokes:
            pts = EM._spline(pts, False, 4) if kind == "s" else list(pts)
            out.append([(x + px * k, cy - h / 2 + py * k + dy) for px, py in pts])
        x += (a + track) * k
    return out, width


def page_facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    name, when = "", ""
    m = re.search(r"last one was (.+?) \(", s)
    if m:
        name = m.group(1).strip()
    m = re.search(r"left \w+, (\w+ \d+)", s)
    if m:
        when = m.group(1)
    m2 = re.search(r"after (\d+) days?", s)
    parked = "no ship parked" not in s.lower() and bool(re.search(r"\bparked\b|\bat anchor\b|\bmoored\b", s.lower()))
    name = re.sub(r"[^A-Z0-9 .'\-]", "", name.upper())[:24]
    when = when.upper()
    return name, when, (m2.group(1) if m2 else ""), parked


# ------------------------------------------------------------------------------------------------
# the vignette: the Columbia from the Sauvie Island bank
# ------------------------------------------------------------------------------------------------

_DOG_SIT = ("M.6,0C-.4,-1.6 -.2,-4 1.4,-5.2C2.6,-6 3.6,-6.6 4.3,-7.7L4.6,-9.5C4.8,-10.5 5.9,-10.9 6.7,-10.5"
            "L7.3,-9.7L8.9,-9.3C9.6,-9.1 9.6,-8.2 8.9,-8L7.4,-7.6C6.9,-6.6 6.9,-5.3 7,-4.3L7.2,-.4L7.8,0"
            "H5.9L5.8,-3.2L4.4,-1.6L4.6,-.4L5.2,0Z")


def moon_phase(date):
    try:
        y, m, d = (int(v) for v in date.split("-"))
    except Exception:
        return .3
    import datetime
    days = (datetime.date(y, m, d) - datetime.date(2000, 1, 6)).days
    return (days % 29.530588) / 29.530588


def ship(lay, x0, ys, L, moving, rng):
    """A bulk carrier heading left (bow at x0), waterline ys, length L. Draws into a dict of layers."""
    hh = max(5., L * .072)
    x1 = x0 + L
    dk = ys - hh
    fc = ys - hh * 1.32
    fx = x0 + L * .075
    hull = [(x0 - hh * .35, fc), (fx, fc), (fx + .5, dk), (x1 - hh * .2, dk), (x1, dk - hh * .08),
            (x1 - hh * .25, ys - hh * .45), (x1 - hh * .7, ys), (x0 + hh * .95, ys), (x0 + hh * .3, ys - hh * .45)]
    H = lay["hull"]
    H.fill(hull)
    # hull: dark, ruled; a white sheer strake under the deck edge and a light boot-top at the water
    body = band(hull, dk + 1.6, ys - 2.2)
    fcb = band(hull, fc + 1.6, dk + 1.6)
    H.add(1., hatch(band(hull, dk + 2.2, ys - 2.4), 0, 2, .5))
    H.add(1., hatch(fcb, 0, 2, .5))
    H.solid(band(hull, dk + hh * .32, ys - 2.6))
    H.add(.5, [[(fx + 2, dk + 1.2), (x1 - hh * .3, dk + 1.2)]])
    H.add(.5, hatch(band(hull, ys - 2.2, ys), 0, 3, .3))
    H.add(1., [hull + [hull[0]]])
    H.add(1.5, [[(x0 + hh, ys), (x1 - hh * .7, ys)]])
    # draft marks and a hawse pipe at the bow
    for i in range(3):
        H.add(.5, [[(x0 + hh * .62 + i * .6, ys - 2 - i * 2.2), (x0 + hh * .62 + i * .6 + 1.4, ys - 2 - i * 2.2)]])
    H.solid(ell(fx - hh * .9, fc + hh * .55, max(.9, hh * .1), max(.7, hh * .08), 10))
    # hatch covers and cranes
    D = lay["deck"]
    s0, s1 = fx + L * .04, x1 - L * .2
    nh = 5
    cwid = (s1 - s0) / nh
    ch = max(2.5, hh * .34)
    for i in range(nh):
        a = s0 + i * cwid + cwid * .1
        b = a + cwid * .8
        cv = [(a, dk), (a + .8, dk - ch), (b - .8, dk - ch), (b, dk)]
        D.fill(cv)
        D.add(.5, [cv + [cv[0]]])
        D.add(.5, hatch(cv, 90, 2, .5, .4))
    for i in range(1, nh):
        px = s0 + i * cwid
        pw = max(1.4, hh * .13)
        ph = hh * 1.25
        post = [(px - pw / 2, dk), (px - pw / 2, dk - ph), (px + pw / 2, dk - ph), (px + pw / 2, dk)]
        D.solid(post)
        cab = [(px - pw * 1.5, dk - ph), (px - pw * 1.3, dk - ph - pw * 1.6), (px + pw * 1.6, dk - ph - pw * 1.6),
               (px + pw * 1.6, dk - ph)]
        D.fill(cab)
        D.add(.5, [cab + [cab[0]]])
        D.add(.5, hatch(band(cab, dk - ph - pw * 1.6, dk - ph), 90, 1.5, .25, .3)[len(cab) // 2:])
        # stowed jib resting forward and down toward the next hatch
        tip = (px - cwid * .78, dk - ch - .8)
        D.add(1., [[(px - pw * 1.2, dk - ph - pw * .6), tip]])
        D.add(.5, [[(px - pw * .2, dk - ph - pw * 1.5), (tip[0] + 1.5, tip[1] - .6)]])
        D.add(.5, [[(px + pw * .5, dk - ph - pw * 1.6), (px - cwid * .3, dk - ph * .55)]])
    # foremast on the forecastle
    D.add(1., [[(x0 + L * .02, fc), (x0 + L * .02, fc - hh * 1.2)]])
    D.add(.5, [[(x0 + L * .02 - 1.5, fc - hh * .85), (x0 + L * .02 + 1.5, fc - hh * .85)]])
    D.add(.5, [[(x0 - hh * .35, fc - .6), (fx, fc - .6)], [(x0 - hh * .35, fc - 1.4), (fx, fc - 1.4)]])
    # accommodation block aft: decks, windows, a shaded after face, bridge wings
    S = lay["super"]
    xs0, xs1 = x1 - L * .16, x1 - L * .045
    decks = 4
    dh = hh * .5
    top = dk - decks * dh
    blk = [(xs0, dk), (xs0, top), (xs1, top), (xs1, dk)]
    S.fill(blk)
    S.add(1., [blk + [blk[0]]])
    shade_w = (xs1 - xs0) * .2
    S.add(.5, hatch([(xs1 - shade_w, dk), (xs1 - shade_w, top), (xs1, top), (xs1, dk)], 90, 1.5, .25))
    for j in range(1, decks):
        y = dk - j * dh
        S.add(.5, [[(xs0, y), (xs1, y)]])
    for j in range(decks):
        y = dk - j * dh - dh * .52
        x = xs0 + 1.6
        while x < xs1 - shade_w - 1.6:
            S.add(1., [[(x, y), (x + 1.1, y)]])
            x += max(2.6, dh * .55)
    S.add(.5, hatch(band(blk, top, top + dh), 0, 1.5, .25)) if dh > 3 else None
    wing = [(xs0 - hh * .45, top), (xs0 - hh * .45, top - dh * .55), (xs1 + hh * .15, top - dh * .55), (xs1 + hh * .15, top)]
    S.fill(wing)
    S.add(.5, [wing + [wing[0]]])
    S.add(1., [[(xs0 - hh * .45, top - dh * .55 + .4), (xs0 + (xs1 - xs0) * .7, top - dh * .55 + .4)]])
    x = xs0 - hh * .3
    while x < xs1 - shade_w:
        S.add(1., [[(x, top - dh * .25), (x + 1.1, top - dh * .25)]])
        x += max(2.4, dh * .5)
    # mast and radar
    mx = xs0 + (xs1 - xs0) * .35
    S.add(1., [[(mx, top - dh * .55), (mx, top - hh * 1.6)]])
    S.add(1., [[(mx - hh * .45, top - hh * 1.25), (mx + hh * .45, top - hh * 1.25)]])
    S.add(.5, [[(mx - hh * .25, top - hh * .9), (mx + hh * .25, top - hh * .9)]])
    # funnel with the house flag: a P monogram
    fw = hh * .78
    fxl = xs1 - fw - hh * .05
    fh = hh * 1.35
    fun = [(fxl, top - dh * .55), (fxl + fw * .18, top - dh * .55 - fh), (fxl + fw * 1.12, top - dh * .55 - fh),
           (fxl + fw, top - dh * .55)]
    F = lay["funnel"]
    F.fill(fun)
    F.add(1., [fun + [fun[0]]])
    F.solid(band(fun, top - dh * .55 - fh, top - dh * .55 - fh * .82))
    F.add(.5, hatch(band(clip_half(fun, -1, 0, fxl + fw * .82), top - dh * .55 - fh * .8, top - dh * .55), 90, 1.5, .5))
    F.add(.5, hatch(band(fun, top - dh * .55 - fh * .2, top - dh * .55), 0, 1.5, .5))
    pc = (fxl + fw * .5, top - dh * .55 - fh * .48)
    ph = max(3.2, fh * .38)
    pl, _ = text_polys("P", pc[0], pc[1], ph, 0)
    F.add(1. if ph > 4.5 else .5, pl)
    F.add(.5, [ell(pc[0], pc[1], ph * .72, ph * .72, 20) + [ell(pc[0], pc[1], ph * .72, ph * .72, 20)[0]]])
    if moving:
        # a thin haze from the funnel, laid back by the ship's way
        sx, sy = fxl + fw * .65, top - dh * .55 - fh - 1
        for k in range(3):
            pts = [(sx + t * hh * 3.2, sy - t * hh * .55 - k * 1.6 + math.sin(t * 5 + k) * 1.2) for t in [i / 14 for i in range(15)]]
            F.add(.5, [pts[k * 2:]])
    return hull, (xs0, xs1, top), hh


def scene(X, Y, W, H, clip_d, info, seed, kind):
    """The vignette filling box X, Y, W, H, clipped to clip_d. kind: band | medium | tall."""
    name, when, days, parked = info[:4]
    rng = random.Random(seed)
    small = kind == "band"
    hz = Y + H * (.46 if kind == "tall" else .5 if kind == "medium" else .5)
    lay = {k: Layer() for k in ("sky", "cloud", "moon", "mtn", "hill", "trees", "water", "refl", "wake",
                                  "hull", "deck", "super", "funnel", "fg", "dolph")}
    # ---- sky: ruled, darkest at the zenith, opening toward the horizon
    S = lay["sky"]
    y = Y + .5
    while y < hz:
        t = (y - Y) / max(1, hz - Y)
        S.add(.5, [[(X, y), (X + W, y)]])
        y += 1.5 if t < .32 else 2. if t < .7 else 3.
    # ---- clouds
    if not small:
        Cl = lay["cloud"]
        for ci in range(2 if kind == "tall" else 1):
            cxw = X + W * (.72 if ci == 0 else .22) + rng.uniform(-W * .05, W * .05)
            yb = Y + (hz - Y) * (.42 if ci == 0 else .3) + rng.uniform(-3, 3)
            cw = W * (.34 if ci == 0 else .22)
            bumps = []
            for k in range(6):
                bx = cxw - cw / 2 + cw * (k + .5) / 6 + rng.uniform(-3, 3)
                br = (H * .05 + rng.uniform(0, H * .035)) * (1 - abs(k - 2.5) / 4.2)
                bumps.append((bx, yb - br * .35, br))
            xs = [cxw - cw / 2 - 4 + i * (cw + 8) / 60 for i in range(61)]
            top = []
            for x in xs:
                v = yb
                for bx, by, br in bumps:
                    if abs(x - bx) < br:
                        v = min(v, by - math.sqrt(br * br - (x - bx) ** 2))
                top.append((x, min(v, yb - .5)))
            poly = top + [(xs[-1], yb), (xs[0], yb)]
            Cl.fill(poly)
            Cl.add(.5, [top])
            ymin = min(p[1] for p in top)
            Cl.add(.5, hatch(band(poly, ymin, yb - (yb - ymin) * .45), 0, 3, .75, .8))
            Cl.add(.5, hatch(band(poly, yb - (yb - ymin) * .45, yb), 0, 1.5, .25, .4))
            for bx, by, br in bumps[1:-1]:
                arc = ell(bx, by, br * .8, br * .8, 18, PI * 1.1, PI * 1.55)
                Cl.add(.5, [[p for p in arc if p[1] < yb - 1]])
    # ---- moon by date (lit side right when waxing)
    if kind != "band":
        ph = moon_phase(info[4] if len(info) > 4 else "")
        mr = max(4.5, H * .045)
        mcx, mcy = X + W * .9 - mr, Y + (hz - Y) * .2 + mr
        M = lay["moon"]
        disc = ell(mcx, mcy, mr, mr, 32)
        M.fill(disc)
        M.add(.5, [disc + [disc[0]]])
        f = (1 - math.cos(2 * PI * ph)) / 2
        waxing = ph < .5

        def dark(p):
            yy = (p[1] - mcy) / mr
            half = math.sqrt(max(1e-6, 1 - yy * yy))
            u = (p[0] - mcx) / (mr * half)
            return (u < 1 - 2 * f) if waxing else (u > 2 * f - 1)
        M.add(.5, [q for s_ in hatch(disc, 0, 1.5, .5, .3) for q in _split(s_, dark)])
        M.add(.5, [ell(mcx + mr * .25, mcy - mr * .2, mr * .22, mr * .18, 10, 0, 2 * PI)])
    # ---- a few gulls working the river
    if not small:
        Gl = lay["moon"]
        for i in range(3):
            gx = X + W * (.48 + .1 * i) + rng.uniform(-6, 6)
            gy = Y + (hz - Y) * (.62 + .1 * (i % 2)) + rng.uniform(-3, 3)
            g = max(2.2, W * .009) * (1 - .15 * i)
            Gl.add(1., [[(gx - g, gy - g * .2), (gx - g * .45, gy - g * .55), (gx, gy), (gx + g * .45, gy - g * .55), (gx + g, gy - g * .2)]])
    # ---- Mt. St. Helens (flat-topped, the crater open to the north)
    mcx = X + W * (.3 if kind == "tall" else .27)
    mh = (hz - Y) * (.6 if kind == "tall" else .58)
    mb = W * (.26 if kind == "tall" else .21)
    mtop = hz - H * .035 - mh
    tw = mb * .2
    left = [(mcx - mb, hz - H * .03)] + [(mcx - mb + (mb - tw) * t, hz - H * .03 - mh * (t ** 1.6)) for t in [i / 16 for i in range(1, 17)]]
    right = [(mcx + mb - (mb - tw) * t, hz - H * .03 - mh * (t ** 1.7)) for t in [i / 16 for i in range(16, 0, -1)]] + [(mcx + mb, hz - H * .03)]
    crater = [(mcx - tw * .5, mtop + mh * .05), (mcx - tw * .1, mtop + mh * .1), (mcx + tw * .3, mtop + mh * .04)]
    mpoly = left + crater + right
    Mt = lay["mtn"]
    Mt.fill(mpoly)
    Mt.add(.5, [left + crater + right])
    snow_y = lambda x: mtop + mh * (.5 + .12 * math.sin((x - mcx) * .35) + .08 * math.sin((x - mcx) * .9 + 1))
    # lower slopes: ruled mid-tone (distance)
    xs = [mcx - mb + 2 * mb * i / 60 for i in range(61)]
    edge = [(x, snow_y(x)) for x in xs]
    lower = clip_half(mpoly, 0, 1, -mtop - mh * .38)
    Mt.add(.5, [seg for s in hatch(lower, 0, 1.5, .5) for seg in _below(s, snow_y)])
    east = clip_half(lower, 1, -.3, -(mcx + tw * .2) + .3 * mtop)
    Mt.add(.5, [seg for s in hatch(east, 62, 2, .5) for seg in _below(s, snow_y)])
    Mt.add(1., [[p for p in right if p[1] > mtop + mh * .3]])
    # snow: light on the lit (west) face, shaded on the east, gullies running down
    snow = clip_half(mpoly, 0, -1, mtop + mh * .72)
    sh_poly = clip_half(snow, 1, -.35, -(mcx + tw * .2) + .35 * mtop)
    Mt.add(1., [seg for s in hatch(sh_poly, 70, 2, .5) for seg in _above(s, snow_y)])
    Mt.add(.5, [seg for s in hatch(clip_half(snow, -1, .35, (mcx + tw * .2) - .35 * mtop), 0, 3, 1) for seg in _above(s, snow_y)])
    for g in range(-3, 4):
        gx = mcx + g * tw * .45
        pts = [(gx + g * mb * .22 * t + math.sin(t * 6 + g) * .8, mtop + mh * .06 + mh * .62 * t) for t in [i / 10 for i in range(11)]]
        Mt.add(.5, [[p for p in pts if p[1] < snow_y(p[0]) + 2]])
    Mt.add(.5, [[(x, y) for x, y in edge if _inside(mpoly, x, y)]])
    # ---- the Washington hills beyond the river
    Hl = lay["hill"]
    hill_top = lambda x: hz - H * (.05 + .025 * math.sin((x - X) / W * 5.2 + seed % 7) + .015 * math.sin((x - X) / W * 13))
    hp = [(X + W * i / 80, hill_top(X + W * i / 80)) for i in range(81)] + [(X + W, hz), (X, hz)]
    Hl.fill(hp)
    Hl.add(.5, [hp[:81]])
    Hl.add(.5, hatch(hp, 0, 1.5, .25, .3))
    Hl.add(.5, hatch(hp, -25, 3, 0, .3))
    # ---- the tree line on the far bank: crowns, poplars, dark
    Tr = lay["trees"]
    tb = hz
    crowns, x = [], X - 2
    tt = []
    while x < X + W + 4:
        r = H * rng.uniform(.012, .022)
        if rng.random() < .12:
            # a poplar
            ph_ = H * rng.uniform(.05, .075)
            tt += [(x, tb - H * .02), (x + r * .4, tb - ph_), (x + r * .8, tb - H * .02)]
            x += r * .8
        else:
            for i in range(7):
                a = PI + PI * i / 6
                tt.append((x + r + r * math.cos(a), tb - H * .018 - r * .3 + r * math.sin(a) * .9))
            x += r * 1.7
        crowns.append(x)
    tpoly = tt + [(X + W + 4, tb), (X - 2, tb)]
    Tr.fill(tpoly)
    Tr.add(.5, [tt])
    Tr.add(.5, hatch(tpoly, 0, 1.5, .5, .2))
    Tr.add(.5, hatch(tpoly, 65, 2, 0, .2))
    Tr.add(1., [[(X, tb - .6), (X + W, tb - .6)]])
    # ---- the river: ruled water, densest under the far bank, sparkling broken lines in mid-stream
    sx0 = X + W * (.16 if kind == "tall" else .14)
    L = W * (.6 if kind == "tall" else .62)
    ys = hz + (Y + H - hz) * (.3 if kind == "tall" else .34 if kind == "medium" else .5)
    if parked:
        sx0 = X + W * .3
    hull, (xs0, xs1, stop), hh = ship(lay, sx0, ys, L, not parked, rng)
    Wt = lay["water"]
    R = lay["refl"]
    y = hz + .75
    while y < Y + H:
        t = (y - hz) / max(1, Y + H - hz)
        if t < .1:
            Wt.add(.5, broken(X, X + W, y, rng, (14, 60), (1., 2.5)))
            y += 1.5
            continue
        # reflections of the hull and the accommodation block
        segs = broken(X, X + W, y, rng, (5, 22) if t < .55 else (8, 34), (1.2, 4.) if t < .55 else (1.5, 5.), .35 if t > .5 else 0)
        rh = (y - ys)
        refl = []
        if 0 < rh < hh * 1.3:
            refl.append((sx0 + hh * .9 + rh * .3, sx0 + L - hh * .7 - rh * .2, 1.))
        if 0 < rh < hh * 1.9:
            refl.append((xs0 + rh * .3, xs1 - rh * .3, .5))
        keep = []
        for s in segs:
            xa, xb = s[0][0], s[-1][0]
            cut = [(a, b) for a, b, _ in refl if b > xa and a < xb]
            if not cut:
                keep.append(s)
            else:
                a, b = cut[0]
                if xa < a - 1:
                    keep.append([(xa, y), (a - 1, y)])
                if xb > b + 1:
                    keep.append([(b + 1, y), (xb, y)])
        Wt.add(.5, keep)
        for a, b, wgt in refl:
            R.add(wgt, broken(a, b, y, rng, (4, 16), (.8, 2.2)))
        y += 2. if t < .7 else 2.5 if t < .85 else 2.
    # ---- the ship's way: a white bow wave and a spreading wake astern
    Wk = lay["wake"]
    if not parked:
        bw = [(sx0 + hh * .2, ys - hh * .35), (sx0 - hh * .9, ys + .8), (sx0 + hh * .6, ys + hh * .3), (sx0 + hh * 2.6, ys + 1.2), (sx0 + hh * 1.4, ys)]
        Wk.fill(bw)
        Wk.add(.5, [bw[:3], [(sx0 - hh * .4, ys + .9), (sx0 + hh * 2., ys + hh * .22)]])
        ex = sx0 + L
        for k, sp in enumerate((.1, .2, .32)):
            pts = [(ex - hh * .5 + u * W * .35, ys + 1 + u * u * H * sp * .4 + math.sin(u * 30 + k) * .5) for u in [i / 30 for i in range(31)]]
            pts = [p for p in pts if p[0] < X + W]
            i = 0
            segs = []
            while i < len(pts) - 2:
                n_ = rng.randint(3, 6)
                segs.append(pts[i:i + n_])
                i += n_ - 1 + (1 if rng.random() < .5 else 0)
            Wk.add(.5 if k else 1., segs)
        wk = [(ex - hh * .7, ys - 1), (ex + W * .35, ys + 1.5), (ex + W * .35, ys + H * .06), (ex - hh * .3, ys + 2.4)]
        Wk.fill(wk)
        Wk.add(.5, [s for s in hatch(wk, 2, 2.5, .3, .4)])
    # ---- the Sauvie Island bank in the foreground, with reeds, and the empty mooring dolphins
    Fg = lay["fg"]
    if not small:
        by0 = Y + H * (.8 if kind == "tall" else .78)
        bank_top = [(X + W * .46 * t, by0 + (Y + H - by0) * (t ** 2.2) * .9 + math.sin(t * 9) * 1.2) for t in [i / 30 for i in range(31)]]
        bank = [(X - 2, by0)] + bank_top + [(X + W * .48, Y + H + 2), (X - 2, Y + H + 2)]
        Fg.fill(bank)
        Fg.add(1., [bank_top])
        Fg.add(.5, hatch(bank, 0, 1.5, .25, .2))
        tufts = []
        for i in range(int(W * .5 / 1.8)):
            t = i / (W * .5 / 1.8)
            bx_ = X + W * .47 * t
            by_ = by0 + (Y + H - by0) * (min(1, t / .98) ** 2.2) * .9 + 1.4
            for j in range(4):
                yy = by_ + j * (Y + H - by_) / 4 + rng.uniform(0, 2)
                if yy < Y + H:
                    hgt = rng.uniform(2.2, 4.2) * (1 - j * .15)
                    tufts.append([(bx_ + rng.uniform(-.6, .6), yy), (bx_ + rng.uniform(-.8, 1.4), yy - hgt)])
        Fg.add(.5, tufts)
        reeds = []
        for i in range(int(W * .45 / 3)):
            t = rng.random() ** 1.4
            bx_ = X + W * .44 * t
            by_ = by0 + (Y + H - by0) * (t ** 2.2) * .9 + 1
            hgt = H * rng.uniform(.03, .08) * (1 - t * .6)
            lean = rng.uniform(-.3, .5)
            reeds.append([(bx_ + lean * hgt * u * u, by_ - hgt * u) for u in (0, .35, .7, 1)])
            if rng.random() < .25:
                reeds.append([(bx_ + lean * hgt * .7 + x_, by_ - hgt * .7 + y_) for x_, y_ in ((-.6, 0), (-.7, -2.4), (-.2, -3), (.2, -2.4), (.1, 0))])
        Fg.add(.5, reeds)
        # dog sitting on the bank watching the ship go (Parker's Easter egg)
        dx_ = X + W * .2
        dy_ = by0 + (Y + H - by0) * (.44 ** 2.2) * .9 + .6
        ds = max(.65, H * .0075)
        Fg_extra = (f'<path transform="translate({_n(dx_)},{_n(dy_)}) scale({ds:.2f})" d="{_DOG_SIT}" fill="#000" stroke="#fff" stroke-width="{.5 / ds:.3f}"/>'
                    f'<path transform="translate({_n(dx_)},{_n(dy_)}) scale({ds:.2f})" d="M5.5,-9.6C5.2,-8.6 5.3,-7.8 5.8,-7.2M1.6,-4.6C2.6,-5.4 3.6,-6 4.2,-6.9" fill="none" stroke="#fff" stroke-width="{.5 / ds:.2f}"/>')
        # the empty berth: a mooring dolphin of bound pilings
        Do = lay["dolph"]
        for k, (fxr, sc) in enumerate(((.86, 1.),)):
            px = X + W * fxr
            wl = ys + (Y + H - ys) * (.62 if k == 0 else .25)
            pw = W * .045 * sc
            ph = H * .16 * sc
            dp = [(px - pw / 2, wl), (px - pw * .38, wl - ph), (px + pw * .38, wl - ph), (px + pw / 2, wl)]
            Do.fill(dp)
            Do.add(1., [dp + [dp[0]]])
            Do.add(.5, hatch(clip_half(dp, 1, 0, -px + pw * .05), 90, 1.5, .25))
            Do.add(.5, hatch(clip_half(dp, -1, 0, px - pw * .05), 90, 3, .5))
            for j in range(1, 4):
                q = j / 4
                Do.add(.5, [[(px - pw * .38, wl - ph * q), (px + pw * .38, wl - ph * q)]])
            for j in (-1, 0, 1):
                Do.add(1., [[(px + j * pw * .28, wl - ph), (px + j * pw * .3, wl - ph - 1.5)]])
            Do.add(1., [[(px - pw * .5, wl - ph * .3), (px + pw * .5, wl - ph * .3)]])
            rr = []
            for j in range(int(ph * .9 / 2)):
                yy = wl + 1 + j * 2
                ww = pw * .5 * (1 - j / (ph * .5))
                if ww > .8:
                    rr.append([(px - ww + rng.uniform(-1, 1), yy), (px + ww + rng.uniform(-1, 1), yy)])
            R.add(1., rr)
        # a channel nun buoy marking the ship channel
        bxp, byp = X + W * .58, ys + (Y + H - ys) * .48
        bs = max(4., H * .028)
        nun = [(bxp - bs * .55, byp), (bxp - bs * .4, byp - bs * 1.2), (bxp, byp - bs * 1.9), (bxp + bs * .4, byp - bs * 1.2), (bxp + bs * .55, byp)]
        Do.fill(nun)
        Do.add(1., [nun + [nun[0]]])
        Do.add(.5, hatch(clip_half(nun, 1, 0, -bxp + bs * .1), 90, 1.5, .25))
        Do.add(.5, hatch(nun, 0, 2, .5, .3))
        Do.solid([(bxp - bs * .75, byp + .2), (bxp + bs * .75, byp + .2), (bxp + bs * .6, byp + bs * .45), (bxp - bs * .6, byp + bs * .45)])
        R.add(.5, [[(bxp - bs * (.5 - j * .08) + rng.uniform(-.5, .5), byp + bs * .6 + j * 1.6), (bxp + bs * (.5 - j * .08), byp + bs * .6 + j * 1.6)] for j in range(5)])
    else:
        Fg_extra = ""
    order = ("sky", "cloud", "moon", "mtn", "hill", "trees", "water", "refl", "dolph", "wake", "hull", "deck", "super", "funnel", "fg")
    body = "".join(lay[k].svg() for k in order) + Fg_extra
    cid = C._uid("rv", X, Y, W, H, kind)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            c = not c
    return c


def _split(seg, keep):
    (ax, ay), (bx, by) = seg
    L = math.hypot(bx - ax, by - ay)
    k = max(2, int(L))
    out, cur = [], []
    for i in range(k + 1):
        p = (ax + (bx - ax) * i / k, ay + (by - ay) * i / k)
        if keep(p):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append([cur[0], cur[-1]])
            cur = []
    if len(cur) > 1:
        out.append([cur[0], cur[-1]])
    return out


def _below(seg, f):
    return _split(seg, lambda p: p[1] > f(p[0]) + .4)


def _above(seg, f):
    return _split(seg, lambda p: p[1] < f(p[0]) - .4)


# ------------------------------------------------------------------------------------------------
# frame layouts (the house layouts, re-cut for this page)
# ------------------------------------------------------------------------------------------------

_K = 2 ** (-1 / 2.6)


def _field(cx, cy, a, b, pad=4.6):
    return C._d(C._superellipse(cx, cy, a - pad, b - pad), True, .1)


def _layout_band(w, h, seed, info):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.9, 190)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .86, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip = C._d(C._ell_pts(cx, cy, rx - 4.6, ry - 4.6, 64), True, 0)
    o.append(scene(cx - rx, cy - ry, 2 * rx, 2 * ry, clip, info, seed, "band"))
    o.append(f'<path d="{C._d(C._ell_pts(cx, cy, rx - 4, ry - 4, 64), True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, info):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .5, gh * 2.)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = iw / 2 / _K + 6, ih / 2 / _K + 6
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, _field(cx, cy, a, b), info, seed, "medium"))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, info):
    name, when, days, parked = info[:4]
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # the page's own diagonal ground carried behind the breakout crest, and a mid ground under the base
    o.append(f'<path d="M0,0h{_n(w)}v{_n(py0)}h{_n(-w)}z" fill="{C.pat("D")}" stroke="none"/>')
    o.append(f'<path d="M0,{_n(py0 + ph - 2)}h{_n(w)}v{_n(h - py0 - ph + 2)}h{_n(-w)}z" fill="{C.pat("M")}" stroke="none"/>')
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .6, ph * .66
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    side_w = (pw - cw) / 2
    r1 = min(side_w * .62, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(side_w * .55, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = iw / 2 / _K + 6, ih / 2 / _K + 6
    o.append(scene(cx - a, cy - b, 2 * a, 2 * b, _field(cx, cy, a, b), info, seed, "tall"))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .16 + top_free, 56), True, rng.randrange(1 << 20)))
    bh = min(17, max(13, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.25, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # THE COLUMBIA on the ribbon, following its arch
    ys_ = {round(p[0]): p[1] for p in centre}
    base_y = centre[len(centre) // 2][1]

    def arch(x):
        best = min(centre, key=lambda p: abs(p[0] - x))
        return best[1] - base_y
    tp, _ = text_polys("THE COLUMBIA", cx, base_y + .3, bh * .5, 1.6, arch)
    o.append(f'<path d="{"".join(_d(p, False, .12) for p in tp)}" fill="none" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw_, th_) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: the last caller and her sailing
    line = name or "THE LAST CALLER"
    if when:
        line += "  ·  SAILED " + when
    lh = min(th_ * .52, 9.)
    tp, tw2 = text_polys(line, tx + tw_ / 2, ty + th_ / 2 + .6, lh, 1.5)
    if tw2 > tw_ - 12:
        tp, tw2 = text_polys(line, tx + tw_ / 2, ty + th_ / 2 + .6, lh * (tw_ - 12) / tw2, 1.5)
    o.append(f'<path d="{"".join(_d(p, False, .12) for p in tp)}" fill="none" stroke="#000" stroke-width="1"/>')
    # small anchors flanking the lettering
    if tw2 + 34 < tw_:
        for sx in (-1, 1):
            ax = tx + tw_ / 2 + sx * (tw2 / 2 + 10)
            o.append(_anchor(ax, ty + th_ / 2, th_ * .62))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _anchor(x, y, s):
    """A small fouled anchor, centred at (x, y), s tall."""
    k = s / 10
    d = (f"M{_n(x)},{_n(y - 4 * k)}V{_n(y + 4.4 * k)}"
         f"M{_n(x - 2.4 * k)},{_n(y - 2.6 * k)}H{_n(x + 2.4 * k)}"
         f"M{_n(x - 3.6 * k)},{_n(y + 1.6 * k)}Q{_n(x - 3 * k)},{_n(y + 4.6 * k)} {_n(x)},{_n(y + 4.6 * k)}"
         f"Q{_n(x + 3 * k)},{_n(y + 4.6 * k)} {_n(x + 3.6 * k)},{_n(y + 1.6 * k)}")
    ring = C._d(C._ell_pts(x, y - 4.9 * k, .9 * k, .9 * k, 10), True, 0)
    return (f'<path d="{d}{ring}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="M{_n(x - 3.6 * k)},{_n(y + 1.6 * k)}l{_n(-.6 * k)},{_n(1.2 * k)}l{_n(1.4 * k)},{_n(-.4 * k)}z'
            f'M{_n(x + 3.6 * k)},{_n(y + 1.6 * k)}l{_n(.6 * k)},{_n(1.2 * k)}l{_n(-1.4 * k)},{_n(-.4 * k)}z" fill="#000"/>')


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 17
    info = page_facts(ctx) + (ctx.get("date", ""),)
    if h < 110:
        body = _layout_band(w, h, seed, info)
    elif h <= 260:
        body = _layout_medium(w, h, seed, info)
    else:
        body = _layout_tall(w, h, seed, info)
    return C.svg_doc(w, h, body)
