"""music-03 "Album birthdays" plate.

Subject: a birthday for records. An LP lies like a cake on the cartouche's field, its grooves cut
as concentric engraved rings with the X-shaped sheen of real vinyl, a ring of birthday candles
(one per decade of today's headline anniversary, e.g. Kiss's Rock and Roll Over turning 50) and
a tonearm at rest, all under a glory of rays on a ruled sky.
Grown into the ornament: a pair of drumsticks crosses behind the cartouche (their beaded tips
break out between the scrolls), and Parker's Easter egg is a bar of swing ride-cymbal rhythm
("ding, ding-a ding") cut on the ribbon banner in x-noteheads, plus crossed sticks on the label.
The pedestal tablet carries the release year and today's year in engraved numerals.
"""
import sys
import math
import random
import re
import engraving_codex as C
from engraving_codex import _n, _d, _ell_pts, pat, Canvas, TAU, PI

CR = ' shape-rendering="crispEdges"'


# ------------------------------------------------------------------------------------------
# page facts
# ------------------------------------------------------------------------------------------

def _facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    date = (ctx or {}).get("date", "") or "2026-11-11"
    try:
        yr = int(date[:4])
    except ValueError:
        yr = 2026
    age, rel = None, None
    m = re.search(r"(\d{4})\s*·\s*turns\s+(\d+)\s+today", s)
    if m:
        rel, age = int(m.group(1)), int(m.group(2))
    else:
        ys = [int(y) for y in re.findall(r"·\s*(\d{4})\b", s) if 1900 < int(y) <= yr]
        if ys:
            best = max(ys, key=lambda y: ((yr - y) % 10 == 0, (yr - y) % 5 == 0, yr - y))
            rel, age = best, yr - best
    if age is None:
        rel, age = yr - 50, 50
    return dict(year=yr, rel=rel, age=age, candles=max(1, min(6, age // 10 or 1)))


# ------------------------------------------------------------------------------------------
# engraved numerals (stroke font, 6 x 10 box)
# ------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_DIG = {
    "0": [_arc(3, 5, 3, 5, 0, 360, 20)],
    "1": [[(1.5, 2), (3.5, 0), (3.5, 10)], [(1.5, 10), (5.5, 10)]],
    "2": [_arc(3, 3, 2.8, 2.8, 200, 360, 8) + [(0.2, 10), (6, 10)]],
    "3": [_arc(3, 2.6, 2.6, 2.4, 200, 450, 9), _arc(3, 7.2, 2.9, 2.8, 270, 520, 10)],
    "4": [[(4.5, 10), (4.5, 0), (0, 7), (6, 7)]],
    "5": [[(5.6, 0), (1, 0), (0.6, 4.3)] + _arc(3, 6.8, 3, 3.2, 230, 495, 11)],
    "6": [_arc(3, 7, 3, 3, 0, 360, 14), [(0.1, 7)] + _arc(4.5, 5.5, 4.4, 5.5, 180, 275, 6)],
    "7": [[(0, 0), (6, 0), (2.2, 10)]],
    "8": [_arc(3, 2.5, 2.5, 2.5, 0, 360, 12), _arc(3, 7.3, 3, 2.7, 0, 360, 14)],
    "9": [_arc(3, 3, 3, 3, 0, 360, 14), [(5.9, 3)] + _arc(1.5, 4.5, 4.4, 5.5, 0, 95, 6)],
}


def _numerals(s, x, y, hgt, out):
    """Polylines for string s (digits, '*' star, ' ') starting at x, top y, height hgt."""
    k = hgt / 10.
    adv = 8.2 * k
    for ch in s:
        if ch in _DIG:
            for pl in _DIG[ch]:
                out.append([(x + px * k, y + py * k) for px, py in pl])
        elif ch == "*":
            cx, cy, r = x + 3 * k, y + 5 * k, 3.4 * k
            pts = [(cx + (r if i % 2 == 0 else r * .42) * math.sin(PI * i / 5),
                    cy - (r if i % 2 == 0 else r * .42) * math.cos(PI * i / 5)) for i in range(11)]
            out.append(pts)
        x += adv
    return x


def _num_width(s, hgt):
    return len(s) * 8.2 * hgt / 10. - 2.2 * hgt / 10.


# ------------------------------------------------------------------------------------------
# the vignette: a record birthday cake
# ------------------------------------------------------------------------------------------

def _earc(cx, cy, rx, ry, t0, t1):
    """SVG path data for an axis-aligned elliptic arc from param t0 to t1 (radians, t1 > t0)."""
    if t1 - t0 >= TAU - 1e-6:
        return (f"M{_n(cx + rx)},{_n(cy)}A{_n(rx)},{_n(ry)} 0 1,1 {_n(cx - rx)},{_n(cy)}"
                f"A{_n(rx)},{_n(ry)} 0 1,1 {_n(cx + rx)},{_n(cy)}")
    p0 = (cx + rx * math.cos(t0), cy + ry * math.sin(t0))
    p1 = (cx + rx * math.cos(t1), cy + ry * math.sin(t1))
    return (f"M{_n(p0[0])},{_n(p0[1])}A{_n(rx)},{_n(ry)} 0 {1 if t1 - t0 > PI else 0},1 "
            f"{_n(p1[0])},{_n(p1[1])}")


def _poly_d(pts, close=True):
    return _d(pts, close, 0)


def _stick(cv, x0, y0, x1, y1, wb, tip=True, shade=1):
    """A drumstick from butt (x0, y0) to tip (x1, y1): butt width wb, long taper, bead tip.
    Turned wood: highlight along one side, bulino along the length, black underside."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    prof = []
    for i in range(25):
        u = i / 24
        hw = wb / 2 * (1 if u < .62 else 1 - .62 * ((u - .62) / .38) ** 1.3)
        prof.append((u, hw))
    side_a = [(x0 + ux * L * u * .93 + nx * hw, y0 + uy * L * u * .93 + ny * hw) for u, hw in prof]
    side_b = [(x0 + ux * L * u * .93 - nx * hw, y0 + uy * L * u * .93 - ny * hw) for u, hw in prof]
    cap = _arc(0, 0, 1, 1, 90, 270, 6)
    butt = [(x0 + (-c[0] * wb * .25) * ux + c[1] * wb / 2 * nx, y0 + (-c[0] * wb * .25) * uy + c[1] * wb / 2 * ny)
            for c in cap]
    poly = side_a + side_b[::-1] + butt[::-1]
    cv.obj([poly], 1.)
    # bulino along the shaft, dense on the shade side
    for s in (-.75, -.5, -.25, .05, .4):
        pl = [(x0 + ux * L * u * .93 + nx * hw * s * shade, y0 + uy * L * u * .93 + ny * hw * s * shade)
              for u, hw in prof[1:-1]]
        cv.hair(pl)
    cv.heavy([(x0 + ux * L * u * .93 - nx * (hw - .9) * shade, y0 + uy * L * u * .93 - ny * (hw - .9) * shade)
              for u, hw in prof[:-2]])
    if tip:
        tr = max(1.6, wb * .42)
        tx, ty = x0 + ux * (L * .93 + tr * .6), y0 + uy * (L * .93 + tr * .6)
        bead = [(tx + ux * tr * 1.25 * math.cos(t) + nx * tr * math.sin(t),
                 ty + uy * tr * 1.25 * math.cos(t) + ny * tr * math.sin(t)) for t in [TAU * i / 18 for i in range(18)]]
        cv.obj([bead], 1.)
        cv.hair([[(tx + nx * tr * s - ux * tr, ty + ny * tr * s - uy * tr), (tx + nx * tr * s + ux * tr, ty + ny * tr * s + uy * tr)]
                 for s in (-.6, -.3)])


def _clip_y(poly, y0, y1):
    """Sutherland-Hodgman clip of a polygon to the band y0 <= y <= y1."""
    for lim, keep in ((y0, lambda p: p[1] >= y0), (y1, lambda p: p[1] <= y1)):
        out = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if keep(a):
                out.append(a)
            if keep(a) != keep(b) and b[1] != a[1]:
                t = (lim - a[1]) / (b[1] - a[1])
                out.append((a[0] + (b[0] - a[0]) * t, lim))
        poly = out
        if not poly:
            break
    return poly


def _candle(cv, bx, by, cw, ch, flame=True):
    """A spiral-striped birthday candle standing on (bx, by), with wick and flame."""
    x0, x1 = bx - cw / 2, bx + cw / 2
    top = by - ch
    ey = cw * .22
    body = [(x0, top)] + [(x1, top)] + _arc(bx, by, cw / 2, ey, 0, 180, 6)
    cv.obj([body], 1.)
    # spiral stripes: 45 deg bands, alternating hatched / plain
    band = max(3., cw * .9)
    k = 0
    yy = by + cw
    while yy > top - cw:
        if k % 2 == 0:
            poly = [(x0, yy), (x1, yy - cw), (x1, yy - cw - band * .55), (x0, yy - band * .55)]
            poly = _clip_y(poly, top + .5, by)
            if len(poly) > 2:
                cv.line(C.hatch_poly(poly, -45, 2))
        yy -= band
        k += 1
    cv.line([(x1 - .6, top + 1), (x1 - .6, by)])
    cv.hair([(x0 + cw * .3, top + 1.5), (x0 + cw * .3, by - 1)])
    cv.obj([_arc(bx, top, cw / 2, ey, 0, 360, 12)], .5)
    cv.line([(bx, top), (bx + .4, top - 2.2)])
    if flame:
        fh = max(5., ch * .42)
        fw = max(2.5, cw * .95)
        fy = top - 2
        outer = ([(bx + .6, fy - fh)] + [(bx + fw / 2 * math.sin(PI * t) * (1 - .25 * t), fy - fh + fh * t ** .8)
                                       for t in [i / 10 for i in range(1, 11)]]
                 + [(bx - fw / 2 * math.sin(PI * t) * (1 - .25 * t), fy - fh + fh * t ** .8)
                    for t in [i / 10 for i in range(10, 0, -1)]])
        cv.obj([outer], 1.)
        core = [(bx, fy - fh * .5), (bx + fw * .2, fy - fh * .2), (bx, fy - 1), (bx - fw * .2, fy - fh * .2)]
        cv.obj([core], .5)
        cv.hair([(bx + fw * .28, fy - fh * .62), (bx + fw * .3, fy - fh * .25)])


def _vignette(x, y, w, h, clip_d, facts, seed, small=False):
    """The record-birthday scene filling the bbox (x, y, w, h), clipped to clip_d."""
    rng = random.Random(seed)
    cx = x + w / 2
    o = []
    o.append(f'<path d="M{_n(x)},{_n(y)}h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>')
    k = .5
    if small:
        R = min(w * .43, h * .62 / k / 2 * 1.6)
        dcy = y + h * .62
        ch = h * .3
        n_c = 1
        flame_y = dcy - ch - 4
    else:
        ch = h * .19
        R = min(w * .39, (.8 * h - 1.55 * ch - 6) / (1.62 * k))
        dcy = y + h - R * k - h * .1
        n_c = facts["candles"]
        flame_y = dcy - R * k * .62 - ch - 4
    # glory: rays from the candle cluster
    gx, gy = cx - R * .05, flame_y + ch * .1
    rays = []
    nr = 72 if not small else 36
    for i in range(nr):
        a = TAU * (i + .5) / nr
        r0 = min(w, h) * (.16 if i % 2 else .1)
        r1 = max(w, h) * (1.1 if i % 3 else .9)
        rays.append([(gx + r0 * math.cos(a), gy + r0 * math.sin(a)), (gx + r1 * math.cos(a), gy + r1 * math.sin(a))])
    o.append(f'<path d="{"".join(_d(r, tol=0) for r in rays)}" stroke="#000" stroke-width=".5"/>')
    # a table top under the disc: mid ruled with a front edge
    ty = dcy + R * k * .55
    o.append(f'<path d="M{_n(x)},{_n(ty)}h{_n(w)}v{_n(y + h - ty)}h{_n(-w)}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="M{_n(x)},{_n(ty)}h{_n(w)}v{_n(y + h - ty)}h{_n(-w)}z" fill="{pat("M")}" stroke="none"/>')
    o.append(f'<path d="M{_n(x)},{_n(ty)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    # disc: shadow, edge, black face
    o.append(f'<path d="{_earc(cx + 3, dcy + 5, R + 2, R * k + 2, 0, TAU)}" fill="#000"/>')
    o.append(f'<path d="{_earc(cx, dcy + 2.5, R, R * k, 0, TAU)}" fill="#000" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_earc(cx, dcy + 2.5, R - .5, R * k - .5, .15, PI - .15)}" stroke="#fff" stroke-width=".5"/>')
    o.append(f'<path d="{_earc(cx, dcy, R, R * k, 0, TAU)}" fill="#000" stroke="#000" stroke-width="1"/>')
    rl = R * .38
    # grooves: base rings every 4 px, sheen wedges filled in to 2 px near the ends of the ellipse
    gaps = {int(R * f) // 2 * 2 for f in (.55, .74, .9)}
    base, sheen = [], []
    r = rl + 4
    i = 0
    while r < R - 1.5:
        ri = int(r) // 2 * 2
        if ri not in gaps and ri + 2 not in gaps:
            if i % 2 == 0:
                base.append(_earc(cx, dcy, r, r * k, 0, TAU))
            else:
                for c in (PI * 1.0, 0.):
                    hw = .30 + .1 * math.sin(r * .21 + seed)
                    sheen.append(_earc(cx, dcy, r, r * k, c - hw * .5, c + hw))
        r += 2
        i += 1
    o.append(f'<path d="{"".join(base)}" stroke="#fff" stroke-width=".5"/>')
    if sheen:
        o.append(f'<path d="{"".join(sheen)}" stroke="#fff" stroke-width=".5"/>')
    o.append(f'<path d="{_earc(cx, dcy, R - 1, R * k - 1, PI * 1.05, PI * 1.95)}" stroke="#fff" stroke-width="1"/>')
    # label
    o.append(f'<path d="{_earc(cx, dcy, rl + 2, rl * k + 1, 0, TAU)}" fill="#000"/>')
    o.append(f'<path d="{_earc(cx, dcy, rl, rl * k, 0, TAU)}" fill="{pat("D")}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_earc(cx, dcy, rl * .8, rl * k * .8, 0, TAU)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_earc(cx, dcy, rl * .8, rl * k * .8, 0, TAU)}" fill="{pat("L")}" stroke="none"/>')
    cv = Canvas()
    if not small:
        # crossed drumsticks printed on the label (the Easter egg's echo)
        ls = rl * .7
        for sx in (-1, 1):
            _stick(cv, cx - sx * ls, dcy + ls * k * .7, cx + sx * ls, dcy - ls * k * .9, max(2., rl * .09), True, sx)
    cv.obj([_ell_pts(cx, dcy, 1.8, 1.0, 12)], .5)
    # candles on the vinyl, painted back to front
    spots = []
    if n_c == 1:
        spots = [(cx, dcy)]
    else:
        for j in range(n_c):
            a = math.radians(115 + 290 * j / n_c * (1 if n_c > 1 else 0) + 12)
            a = math.radians(105 + (225 / (n_c - 1)) * j) if n_c > 1 else a
            rr = R * .62
            spots.append((cx + rr * math.cos(a), dcy + rr * k * math.sin(a)))
    spots.sort(key=lambda p: p[1])
    cw_ = max(4., min(12., R * .115))
    for bx, by in spots:
        depth = (by - dcy) / (R * k) if R else 0
        _candle(cv, bx, by, cw_ * (1 + .08 * depth), ch * (1 + .06 * depth))
    # tonearm resting on the right
    if not small:
        px, py = cx + R * .86, dcy - R * k * 1.45
        hx, hy = cx + R * .74, dcy + R * k * .45
        ax = [(px, py), (px + (hx - px) * .5 + R * .07, py + (hy - py) * .5), (hx, hy)]
        tube = []
        for t in [i / 16 for i in range(17)]:
            bx_ = (1 - t) ** 2 * ax[0][0] + 2 * (1 - t) * t * ax[1][0] + t * t * ax[2][0]
            by_ = (1 - t) ** 2 * ax[0][1] + 2 * (1 - t) * t * ax[1][1] + t * t * ax[2][1]
            tube.append((bx_, by_))
        def offs(pl, d):
            res = []
            for i_, p in enumerate(pl):
                a_ = pl[max(0, i_ - 1)]
                b_ = pl[min(len(pl) - 1, i_ + 1)]
                L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1
                res.append((p[0] - (b_[1] - a_[1]) / L_ * d, p[1] + (b_[0] - a_[0]) / L_ * d))
            return res
        tw = max(2., R * .05)
        # base plinth (a turned boss) and counterweight
        cv.obj([_ell_pts(px, py + 3, R * .17, R * .17 * k, 28)], 1.)
        cv.hair(C.hatch_poly(_ell_pts(px, py + 3, R * .17, R * .17 * k, 28), 45, 1.5))
        cv.obj([_ell_pts(px, py + 1, R * .11, R * .11 * k, 20)], 1.)
        cv.hair(C.hatch_poly(_ell_pts(px, py + 1, R * .11, R * .11 * k, 20), 0, 2))
        cv.obj([_ell_pts(px, py - 1, R * .07, R * .07 * k, 16)], 1.)
        cw0 = [(px + 2, py - 5), (px + R * .16, py - 8), (px + R * .17, py - 1), (px + 2, py + 2)]
        cv.obj([cw0], 1.)
        cv.hair(C.hatch_poly(cw0, 0, 1.5))
        poly = offs(tube, tw) + offs(tube, -tw)[::-1]
        cv.obj([poly], 1.)
        cv.hair(offs(tube, tw * .35))
        cv.heavy(offs(tube, -tw * .55))
        # headshell
        a_ = math.atan2(tube[-1][1] - tube[-3][1], tube[-1][0] - tube[-3][0])
        ux, uy = math.cos(a_), math.sin(a_)
        hs = R * .11
        head = [(hx + uy * tw * 1.6, hy - ux * tw * 1.6), (hx + ux * hs + uy * tw * 2.2, hy + uy * hs - ux * tw * 2.2),
                (hx + ux * hs - uy * tw * 2.2, hy + uy * hs + ux * tw * 2.2), (hx - uy * tw * 1.6, hy + ux * tw * 1.6)]
        cv.obj([head], 1.)
        cv.hair(C.hatch_poly(head, 45, 1.5))
        cv.line([(hx + ux * hs * .5, hy + uy * hs * .5 + tw * 1.4), (hx + ux * hs * .5, hy + uy * hs * .5 + tw * 2.6)])
    o.append(cv.svg())
    cid = f"mv{abs(hash((round(x), round(y), round(w), round(h)))) % 99999}"
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{"".join(o)}</g>')


# ------------------------------------------------------------------------------------------
# frame pieces
# ------------------------------------------------------------------------------------------

def _crossed_sticks(cv, cx, cy, cw, ch, wb):
    """Two drumsticks crossing behind the cartouche: butts low, beaded tips breaking out above."""
    dx, dy = cw * .78, ch * .62
    _stick(cv, cx - dx * .95, cy + dy, cx + dx, cy - dy * 1.02, wb, True, 1)
    _stick(cv, cx + dx * .95, cy + dy, cx - dx, cy - dy * 1.02, wb, True, -1)


def _swing_staff(centre, hb):
    """A bar-ruled five-line staff on the ribbon face with the jazz ride pattern in x-noteheads."""
    n = len(centre) - 1
    def at(u, s):
        f = u * n
        i = min(n - 1, int(f))
        t = f - i
        p0, p1 = centre[i], centre[i + 1]
        x_ = p0[0] + (p1[0] - p0[0]) * t
        y_ = p0[1] + (p1[1] - p0[1]) * t
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1
        return x_ - (p1[1] - p0[1]) / L * s, y_ + (p1[0] - p0[0]) / L * s
    sp = max(1.5, min(2., hb * .13))
    u0, u1 = .07, .93
    lines = []
    for j in range(-2, 3):
        lines.append([at(u0 + (u1 - u0) * i / 40, j * sp) for i in range(41)])
    o = [f'<path d="{"".join(_d(l, tol=.1) for l in lines)}" stroke="#000" stroke-width=".5"/>']
    # bars: 4 bars of ride pattern: quarter, swung pair (dotted-8th + 16th shown as triplet pair), quarter, pair
    bars = 4
    thick, xs = [], []
    stems = []
    beams = []
    full = (u1 - u0)
    for b in range(bars + 1):
        ub = u0 + full * b / bars
        thick.append([at(ub, -2 * sp), at(ub, 2 * sp)])
    for b in range(bars):
        ub = u0 + full * b / bars
        bw = full / bars
        hits = [(.1, None), (.32, "a"), (.47, "b"), (.6, None), (.82, "a"), (.97, "b")]
        prev = None
        for t, kind in hits:
            if t > .95:
                t = .9
            u = ub + bw * t * .95
            hx, hy = at(u, -2 * sp - sp * .0)  # top line: ride cymbal
            r = sp * .7
            xs.append([(hx - r, hy - r), (hx + r, hy + r)])
            xs.append([(hx - r, hy + r), (hx + r, hy - r)])
            sx, sy = hx + r, hy
            stems.append([(sx, sy), (sx, sy + 4 * sp * .0 + sp * 3.2)])
            if kind == "a":
                prev = (sx, sy + sp * 3.2)
            elif kind == "b" and prev:
                beams.append([prev, (sx, sy + sp * 3.2)])
                prev = None
    o.append(f'<path d="{"".join(_d(l, tol=0) for l in xs + stems)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(_d(l, tol=0) for l in thick + beams)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _tablet(tx, ty, tw, th, facts):
    """Fill the pedestal's tablet: ruled field, engraved '1976 * 50 * 2026'."""
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{pat("L")}" stroke="none"/>']
    s = f"{facts['rel']} * {facts['age']} * {facts['year']}"
    nh = max(5., min(th - 6, 12.))
    nw = _num_width(s, nh)
    x0 = tx + (tw - nw) / 2
    y0 = ty + (th - nh) / 2 + .5
    # white knock-out behind the numerals so they read
    o.append(f'<path d="M{_n(x0 - 4)},{_n(y0 - 2)}h{_n(nw + 8)}v{_n(nh + 4)}h{_n(-(nw + 8))}z" fill="#fff" stroke="#000" stroke-width=".5"/>')
    pls = []
    _numerals(s, x0, y0, nh, pls)
    o.append(f'<path d="{"".join(_d(p, tol=0) for p in pls)}" stroke="#000" stroke-width="{1.5 if nh >= 9 else 1}"/>')
    # flourishes: little ruled bars each side of the numerals
    for sx in (-1, 1):
        ex = x0 - 6 if sx < 0 else x0 + nw + 6
        ln = (tw - nw) / 2 - 12
        if ln > 8:
            a, b = (ex - ln, ex) if sx < 0 else (ex, ex + ln)
            o.append(f'<path d="M{_n(a)},{_n(y0 + nh / 2 - 1.5)}H{_n(b)}M{_n(a)},{_n(y0 + nh / 2 + 1.5)}H{_n(b)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts (house layouts, adapted: no blank paper, bespoke centre, sticks and staff)
# ------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, facts):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("mb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    inner = _ell_pts(cx, cy, rx - 2.5, ry - 2.5, 64)
    o.append(_vignette(cx - rx, cy - ry, 2 * rx, 2 * ry, _d(inner, True, 0), facts, seed, small=True))
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 2.5, ry - 2.5, 64), True)}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    o.append(f'<path d="M0,{_n(h - 2)}h{_n(w)}v2h{_n(-w)}z" fill="{pat("M")}" stroke="none"/>')
    return "".join(o)


def _layout_medium(w, h, seed, facts):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.5)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main, sticks = Canvas(), Canvas(), Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    _crossed_sticks(sticks, cx, cy, cw * .78, gh * .52, max(7., gh * .055))
    cv.extend(main)
    cv.extend(sticks)
    o.append(C._clip(C._uid("mm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = cw / 2, (gh + 4) / 2
    o.append(_vignette(cx - a, cy - b, 2 * a, 2 * b, inner_d, facts, seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, facts, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # the paper above the panel is lightly ruled so the crest rises out of tone, never blank
    o.append(f'<path d="M0,0h{_n(w)}v{_n(py0)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>')
    o.append(C.bead_moulding(0, 2.5, w, 1., fillet=False))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(py0)}h{_n(px0 - 3.5)}v{_n(ph)}H0zM{_n(w)},{_n(py0)}h{_n(-(px0 - 3.5))}v{_n(ph)}H{_n(w)}z" fill="{pat("M")}" stroke="none"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main, sticks = Canvas(), Canvas(), Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(9 * density), edge=.6, cv=cv)
    _crossed_sticks(sticks, cx, cy, cw * .9, ch * .78, max(9., ph * .026))
    cv.extend(main)
    cv.extend(sticks)
    o.append(C._clip(C._uid("mt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner_d = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(_vignette(cx - cw / 2, cy - ch / 2, cw, ch, inner_d, facts, seed))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    hb = min(20, ph * .06)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, hb, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_swing_staff(centre, hb))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    # ground behind the pedestal's flanks so the plinth's sides are never bare paper
    o.append(f'<path d="M0,{_n(py)}h{_n(w)}v{_n(h - py)}H0z" fill="{pat("M")}" stroke="none"/>')
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, facts))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("mf", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    facts = _facts(ctx)
    seed = sum(map(ord, ctx.get("date", ""))) + 3 * int(ctx.get("sheet", 0) or 0) % 7
    if h < 110:
        body = _layout_band(w, h, seed, facts)
    elif h <= 260:
        body = _layout_medium(w, h, seed, facts)
    else:
        body = _layout_tall(w, h, seed, facts)
    return C.svg_doc(w, h, body)
