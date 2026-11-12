"""Deep, tonally modelled acanthus running scroll, as a repeating tile for a CSS background.

One full wave of a running vine (two mirrored half-waves): a swelling stem, a C-scroll volute on
one side and a lobed acanthus leaf on the other, each leaf modelled with contour hatching that swells
toward the shaded edge, so the leaves read in relief rather than as outlines. Drawn inside a data-URI
SVG, so the Kindle page's CSS reset (which kills SVG transforms) never touches it.

Public API:
    vine_tile(width=24, period=44, seed=0, vertical=True) -> svg string (tile, repeats seamlessly)
    data_uri(svg) -> 'url("data:image/svg+xml;base64,...")'
"""
import base64
import math
import random

from .engraving_eink import swell_d


def _f(v):
    s = "%.2f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def _bez(p0, p1, p2, p3, n=14):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _sw(pts, w0, w1, prof="swell"):
    n = len(pts)
    ws = []
    for i in range(n):
        t = i / (n - 1.0)
        if prof == "taper":
            ws.append(w0 + (w1 - w0) * t)
        else:
            ws.append(w0 + (w1 - w0) * math.sin(t * math.pi))
    return swell_d(pts, ws, 1)


def _spiral(cx, cy, r0, th0, turns, sgn, k=0.22, step=0.2):
    pts = []
    th = 0.0
    while th < turns * 2 * math.pi:
        r = r0 * math.exp(-k * th)
        a = th0 + sgn * th
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        th += step
    return pts


def _leaf(base, tip, bulge, width, lobes, side, rng):
    """A lobed acanthus leaf from base to tip, bowed by `bulge`. Returns (outline d, hatch d, rib d).
    The shaded half (side) takes dense swelling contour hatches; the lit half a few hairlines."""
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    n = 24
    mid = []
    for i in range(n + 1):
        t = i / n
        o = bulge * math.sin(t * math.pi)
        mid.append((bx + dx * t + nx * o, by + dy * t + ny * o))

    def half(t):  # lobed half-width profile
        env = math.sin(math.pi * min(1, t * 1.05)) ** .8 * (1 - .35 * t)
        lob = .72 + .28 * abs(math.cos(t * math.pi * lobes))
        return width * env * lob

    left, right = [], []
    for i, (x, y) in enumerate(mid):
        t = i / n
        h = half(t)
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h * .8, y - ny * h * .8))
    ring = left + right[::-1]
    outline = "M" + "L".join("%s %s" % (_f(x), _f(y)) for x, y in ring) + "Z"
    # contour hatching: strokes from the midrib to the edge, following the lobes, swelling on the shade side
    hd = []
    sh = left if side > 0 else right
    lt = right if side > 0 else left
    for i in range(1, n, 1):
        t = i / n
        mx, my = mid[i]
        ex, ey = sh[i]
        pts = [(mx + (ex - mx) * s, my + (ey - my) * s + .6 * math.sin(s * math.pi)) for s in (0, .25, .5, .75, .95)]
        tone = .55 + .4 * math.sin(t * math.pi)
        hd.append(_sw(pts, .1, .18 + .4 * tone))
        if i % 3 == 0 and .15 < t < .85:
            ex, ey = lt[i]
            pts = [(mx + (ex - mx) * s, my + (ey - my) * s) for s in (.15, .45, .8)]
            hd.append(_sw(pts, .1, .35))
    rib = _sw(mid[1:-2], .15, .5)
    return outline, "".join(hd), rib


def _stem_pt(c, y0, P, A, s, t):
    p = _bez((c, y0), (c + s * A * 1.4, y0 + P * .18), (c + s * A * 1.4, y0 + P * .32), (c, y0 + P / 2), 40)
    return p[int(t * 40)], p


def vine_tile(width=24, period=44, seed=0, vertical=True, opaque=False):
    """One wave of the running scroll, `width` across and `period` along, seamless when repeated:
    a swelling stem; from each bend a branch springs and rolls into a volute whose band is shaded
    with parallel cuts; an acanthus leaf sheaths the junction and a second leaf turns over on the
    outside of the bend, both modelled with contour hatching."""
    rng = random.Random(seed)
    W, P = float(width), float(period)
    c = W / 2
    A = W * .13
    fills, lines = [], []
    for k, s in ((0, 1), (1, -1), (2, 1), (3, -1)):
        y0 = k * P / 2
        alt = k >= 2  # the second wave varies the first, so the repeat is long and less regular
        (sx, sy), stem = _stem_pt(c, y0, P, A, s, .22)
        fills.append(_sw(stem, .6, 1.05))
        # volute: centre in the hollow of the bend; the spiral starts on the stem and rolls inward
        cx, cy = c - s * W * (.17 if alt else .2), y0 + P * (.34 if alt else .3)
        r0 = math.hypot(sx - cx, sy - cy)
        th0 = math.atan2(sy - cy, sx - cx)
        sg = -s  # roll away from the stem, downward, then back
        kk = math.log(r0 / 1.2) / (1.6 * 2 * math.pi)
        sp = _spiral(cx, cy, r0, th0, 1.6, sg, k=kk, step=.12)
        fills.append(_sw(sp, .9, .2, "taper"))
        # the volute's band shaded by inner parallel cuts that thin out toward the eye
        for off, w in ((1.0, .38), (1.8, .28), (2.6, .2)):
            sp2 = [(cx + (x - cx) * max(.1, 1 - off / max(r0 * math.exp(-kk * i * .12), 1.5)),
                    cy + (y - cy) * max(.1, 1 - off / max(r0 * math.exp(-kk * i * .12), 1.5))) for i, (x, y) in enumerate(sp[:int(len(sp) * .55)])]
            if len(sp2) > 3:
                fills.append(_sw(sp2, .1, w))
        ex, ey = sp[-1]
        fills.append('M%s %sm-.7 0a.7 .7 0 1 0 1.4 0a.7 .7 0 1 0-1.4 0' % (_f(ex), _f(ey)))
        # sheath leaf at the junction, lying along the branch on the volute's outer side
        base = (sx, sy)
        tip = (c - s * (W / 2 - .8), y0 + P * .1)
        o, h, r = _leaf(base, tip, s * 1.6, W * .13, 2.5, -s, rng)
        lines.append(o); fills.append(h); fills.append(r)
        # turnover leaf on the outside of the bend, sweeping along the stem to the border edge
        (bx, by), _ = _stem_pt(c, y0, P, A, s, .45)
        tip2 = (c + s * (W / 2 - .8), y0 + P * .62)
        o, h, r = _leaf((bx, by), tip2, -s * (1.8 if alt else 2.4), W * (.2 if alt else .17), 2 if alt else 3, s, rng)
        lines.append(o); fills.append(h); fills.append(r)
        curl = _spiral(tip2[0] - s * 1.7, tip2[1] - 1.0, 1.8, 0 if s > 0 else math.pi, .9, -s, k=.3)
        fills.append(_sw(curl, .5, .15, "taper"))
        # pearl in the remaining hollow
    body = ('<path d="%s" fill="#fff" stroke="#000" stroke-width=".4" stroke-linejoin="round"/>'
            '<path d="%s" fill="#000"/>' % ("".join(lines), "".join(fills)))
    P = P * 2
    if opaque:
        body = '<rect width="%s" height="%s" fill="#fff"/>' % (_f(W), _f(P)) + body
    if vertical:
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">%s</svg>'
                % (_f(W), _f(P), _f(W), _f(P), body))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">'
            '<g transform="matrix(0 1 1 0 0 0)">%s</g></svg>' % (_f(P), _f(W), _f(P), _f(W), body))


def data_uri(svg):
    """A CSS url() for an SVG, percent-encoded only where it must be (smaller than base64)."""
    from urllib.parse import quote
    return 'url("data:image/svg+xml,%s")' % quote(svg.replace('"', "'"), safe=" =:/,.-'()<>;!*+@?&_~")


def ground_tile(seed=0, col=32, period=44):
    """The engraved ground for a whole page: four running acanthus columns, two cuts each struck
    upright and mirrored and set at different phases so the repeat is long, leaves white in relief,
    on a field of fine horizontal cuts (0.5 px at 4 px pitch). Seamless; 4*col wide, 2*period tall."""
    import re as _re
    W, P = 4 * col, 2 * period
    inner = lambda s: _re.sub(r'^<svg[^>]*>', '', s)[:-6]
    ia, ib = inner(vine_tile(col, period, seed)), inner(vine_tile(col, period, seed + 5))
    hatch = "".join("M0 %sH%s" % (_f(y + 1.25), W) for y in range(0, P, 4))

    def at(ref, x, dy, mirror=False):
        m = "matrix(-1 0 0 1 %d %s)" % (x + col, _f(dy)) if mirror else "translate(%d,%s)" % (x, _f(dy))
        return ('<use href="#%s" xlink:href="#%s" transform="%s"/><use href="#%s" xlink:href="#%s" transform="%s"/>'
                % (ref, ref, m, ref, ref, m.replace(_f(dy) + ")", _f(dy - P) + ")")))
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%d" height="%d" viewBox="0 0 %d %d">'
            '<defs><g id="a">%s</g><g id="b">%s</g></defs><path d="%s" stroke="#000" stroke-width=".5"/>%s%s%s%s</svg>'
            % (W, P, W, P, ia, ib, hatch,
               at("a", 0, 0), at("b", col, P / 4), at("a", 2 * col, P / 2, True), at("b", 3 * col, P * 3 / 4, True)))
