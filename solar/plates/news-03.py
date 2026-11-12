"""news-03 "Gadget news" plate: the house Codex frame round a carved circuit-board vignette.
Today's page leads with Nvidia (a GPU), five-driver wireless earbuds and room-corrected speakers,
so the cartouche holds a quad-flat GPU package in deep relief on a cut-away circuit board, its
traces fanning out in white relief to vias, acanthus fronds springing from the package corners,
and (when there is room) a pair of shaded earbuds flanking it. Easter egg: a tiny "P" monogram
cut into the die as its maker's mark, with a pair of crossed drumsticks laid into the copper."""
import sys
import math
import random
import engraving_codex as C

_n = C._n
_MODE = {"m": "tall"}


def _P(pts, close=True):
    """Absolute path data (one decimal) for a point list."""
    s = "M" + "L".join(f"{_n(x)},{_n(y)}" for x, y in pts)
    return s + ("Z" if close else "")


def _hd(lines):
    return "".join(_P(l, False) for l in lines)


def _rrect(x, y, w, h, r, n=5):
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _cut_band(lines, nx, ny, c0, c1):
    """Remove from each 2-pt line the part where nx*x+ny*y lies in [c0, c1] (a highlight streak)."""
    out = []
    for (x0, y0), (x1, y1) in lines:
        f0, f1 = nx * x0 + ny * y0, nx * x1 + ny * y1
        if abs(f1 - f0) < 1e-9:
            if not (c0 <= f0 <= c1):
                out.append([(x0, y0), (x1, y1)])
            continue
        t0, t1 = sorted(((c0 - f0) / (f1 - f0), (c1 - f0) / (f1 - f0)))
        for a, b in ((0., min(t0, 1.)), (max(t1, 0.), 1.)):
            if b - a > .02:
                out.append([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)])
    return out


def _field(x, y, w, h):
    """Outline of the whole white field the frame hands us (the rect is only its largest box)."""
    cx, cy = x + w / 2, y + h / 2
    if _MODE["m"] == "band":
        k = .7071
        rx, ry = w / 2 / k + 5 - 4.6, h / 2 / k + 5 - 4.6
        return cx, cy, C._ell_pts(cx, cy, rx, ry, 72)
    k = 2 ** (-1 / 2.6)
    a, b = w / 2 / k + 6 - 4.4, h / 2 / k + 6 - 4.4
    return cx, cy, C._superellipse(cx, cy, a, b, 2.6, 120)


# ---------------------------------------------------------------- the circuit board ground

def _traces(cx, cy, S, half, ext, rng, pitch):
    """Fan-out copper from the four pin rows: straight out, a 45-degree jog away from the centre
    line, then straight on to a via or off the edge. Returns (polylines, via centres)."""
    lines, vias = [], []
    n = max(3, int(S * .78 / pitch))
    for side in range(4):
        ux, uy = ((0, -1), (1, 0), (0, 1), (-1, 0))[side]
        vx, vy = -uy, ux
        for i in range(n):
            if rng.random() < .12:
                continue
            o = (i - (n - 1) / 2) * pitch
            d0 = half + S * .09
            px, py = cx + ux * d0 + vx * o, cy + uy * d0 + vy * o
            d1 = 4 + abs(o) * .25 + rng.choice((0, 0, 3))
            fan = o * 1.15
            p1 = (px + ux * d1, py + uy * d1)
            p2 = (p1[0] + ux * abs(fan) + vx * fan, p1[1] + uy * abs(fan) + vy * fan)
            L = rng.uniform(.4, 1.) * ext
            p3 = (p2[0] + ux * L, p2[1] + uy * L)
            lines.append([(px, py), p1, p2, p3])
            if L < ext * .8:
                vias.append(p3)
    return lines, vias


def _drumsticks(cx, cy, L, ang=0.):
    """Two crossed drumsticks (the Easter egg), as tapered outlines with bead tips."""
    polys = []
    for s in (-1, 1):
        a = math.radians(ang + s * 35 + 90)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        pts = []
        for t, wd in ((-.5, 1.3), (.3, 1.0), (.45, .45)):
            pts.append((cx + ux * L * t + vx * wd, cy + uy * L * t + vy * wd))
        tip = C._ell_pts(cx + ux * L * .5, cy + uy * L * .5, 1.5, 1.5, 10)
        back = [(cx + ux * L * t - vx * wd, cy + uy * L * t - vy * wd) for t, wd in ((.45, .45), (.3, 1.0), (-.5, 1.3))]
        polys.append((pts + back, tip))
    return polys


# ---------------------------------------------------------------- the GPU package

def _chip(cx, cy, S, rng):
    """Returns svg for a quad-flat package of side S at (cx, cy), lit from upper left."""
    o = []
    h = S / 2
    pl = S * .085                       # pin length
    n = max(4, int(S * .78 / max(2.5, S * .045)))
    pitch = S * .78 / n
    pw = pitch * .5
    # cast shadow down-right, solid black
    sh = _rrect(cx - h + 3, cy - h + 3, S, S, S * .03)
    o.append(f'<path d="{_P(sh)}" fill="#000" stroke="none"/>')
    # pins
    pins, pin_dark = [], []
    for side in range(4):
        ux, uy = ((0, -1), (1, 0), (0, 1), (-1, 0))[side]
        vx, vy = -uy, ux
        for i in range(n):
            off = (i - (n - 1) / 2) * pitch
            bx, by = cx + ux * (h - 1) + vx * off, cy + uy * (h - 1) + vy * off
            q = [(bx - vx * pw / 2, by - vy * pw / 2), (bx + ux * (pl + 1) - vx * pw / 2, by + uy * (pl + 1) - vy * pw / 2),
                 (bx + ux * (pl + 1) + vx * pw / 2, by + uy * (pl + 1) + vy * pw / 2), (bx + vx * pw / 2, by + vy * pw / 2)]
            pins.append(q)
            # gull-wing bend: dark band on the knee
            k0, k1 = .35, .6
            pin_dark.append([(bx + ux * (pl + 1) * k0 - vx * pw / 2, by + uy * (pl + 1) * k0 - vy * pw / 2),
                             (bx + ux * (pl + 1) * k1 - vx * pw / 2, by + uy * (pl + 1) * k1 - vy * pw / 2),
                             (bx + ux * (pl + 1) * k1 + vx * pw / 2, by + uy * (pl + 1) * k1 + vy * pw / 2),
                             (bx + ux * (pl + 1) * k0 + vx * pw / 2, by + uy * (pl + 1) * k0 + vy * pw / 2)])
    o.append(f'<path d="{"".join(_P(q) for q in pins)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(_P(q) for q in pin_dark)}" fill="#000" stroke="none"/>')
    # substrate: mid-toned (45 hatch), darker cross-hatched toward the lower right
    body = _rrect(cx - h, cy - h, S, S, S * .03)
    o.append(f'<path d="{_P(body)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_P(body)}" fill="{C.pat("D")}" stroke="none"/>')
    lowr = [(cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]
    o.append(f'<path d="{_P(lowr)}" fill="{C.pat("X")}" stroke="none"/>')
    # bevel: white upper-left lip, black lower-right lip
    b = max(2., S * .035)
    o.append(f'<path d="{_P([(cx - h, cy + h), (cx - h, cy - h), (cx + h, cy - h), (cx + h - b, cy - h + b), (cx - h + b, cy - h + b), (cx - h + b, cy + h - b)])}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_P([(cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h), (cx - h + b, cy + h - b), (cx + h - b, cy + h - b), (cx + h - b, cy - h + b)])}" fill="#000" stroke="none"/>')
    o.append(f'<path d="{_P(body)}" fill="none" stroke="#000" stroke-width="1"/>')
    # ring of SMD capacitors round the die
    di = S * .3
    caps = []
    m = max(2, int(S / 24))
    for side in range(4):
        ux, uy = ((0, -1), (1, 0), (0, 1), (-1, 0))[side]
        vx, vy = -uy, ux
        for i in range(m):
            off = (i - (m - 1) / 2) * (di * 1.6 / max(1, m - 1) if m > 1 else 0)
            px, py = cx + ux * (di + S * .1) + vx * off, cy + uy * (di + S * .1) + vy * off
            cw, chh = S * .035, S * .022
            caps.append(_rrect(px - (cw if ux == 0 else chh), py - (chh if ux == 0 else cw),
                               2 * (cw if ux == 0 else chh), 2 * (chh if ux == 0 else cw), .4, 1))
    o.append(f'<path d="{"".join(_P(q) for q in caps)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(_P(q) for q in caps)}" fill="{C.pat("V")}" stroke="none"/>')
    # die / heat spreader: raised, brushed, a diagonal highlight streak
    dx0, dy0, dw = cx - di, cy - di, 2 * di
    o.append(f'<path d="{_P(_rrect(dx0 + 2.5, dy0 + 2.5, dw, dw, 2))}" fill="#000" stroke="none"/>')
    die = _rrect(dx0, dy0, dw, dw, 2)
    o.append(f'<path d="{_P(die)}" fill="#fff" stroke="#000" stroke-width="1.5"/>')
    face = _rrect(dx0 + 2.5, dy0 + 2.5, dw - 5, dw - 5, 1)
    hl = _cut_band(C.hatch_poly(face, 0, 1.5 if S < 60 else 2, .25), 1, 1, cx + cy - dw * .34, cx + cy - dw * .16)
    hl = _cut_band(hl, 1, 1, cx + cy - dw * .08, cx + cy - dw * .02)
    o.append(f'<path d="{_hd(hl)}" stroke="#000" stroke-width=".5"/>')
    # die chamfer: dark on right/bottom
    o.append(f'<path d="{_P([(dx0 + dw, dy0 + 1), (dx0 + dw, dy0 + dw), (dx0 + 1, dy0 + dw), (dx0 + 3.5, dy0 + dw - 2.5), (dx0 + dw - 2.5, dy0 + dw - 2.5), (dx0 + dw - 2.5, dy0 + 3.5)])}" fill="#000" stroke="none"/>')
    # pin-1 dimple
    o.append(f'<path d="{_P(C._ell_pts(cx - h + S * .1, cy - h + S * .1, S * .028 + .8, S * .028 + .8, 16))}" fill="#000" stroke="#fff" stroke-width=".5"/>')
    # maker's mark on the die: an engraved P monogram in a small oval (the Easter egg)
    if S >= 46:
        mr = max(4.5, dw * .13)
        mx, my = dx0 + dw - mr - 5, dy0 + dw - mr * 1.25 - 5
        ov = C._ell_pts(mx, my, mr * .82, mr * 1.05, 28)
        o.append(f'<path d="{_P(ov)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        u = mr * .55
        stem = [(mx - u * .45, my + u * 1.25), (mx - u * .45, my - u * 1.2)]
        bowl = [(mx - u * .45, my - u * 1.2)] + [(mx + u * .05 + u * .55 * math.cos(t), my - u * .55 + u * .65 * math.sin(t))
                                                 for t in [(-math.pi / 2 + math.pi * i / 10) for i in range(11)]] + [(mx - u * .45, my + u * .1)]
        o.append(f'<path d="{_P(stem, False)}{_P(bowl, False)}" stroke="#000" stroke-width="1.5"/>')
        # serif
        o.append(f'<path d="M{_n(mx - u * .9)},{_n(my + u * 1.25)}H{_n(mx)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


# ---------------------------------------------------------------- the earbuds

def _crescent(cx, cy, r, ang, t, n=24):
    """Shadow crescent on a ball: the outer arc facing `ang` and an inner arc pulled back by t*r."""
    a = math.radians(ang)
    outer = [(cx + r * math.cos(a + math.pi * (i / n - .5)), cy + r * math.sin(a + math.pi * (i / n - .5))) for i in range(n + 1)]
    ox, oy = cx - math.cos(a) * r * t, cy - math.sin(a) * r * t
    rr = r
    inner = []
    for i in range(n + 1):
        b = a + math.pi * (.5 - i / n)
        p = (ox + rr * math.cos(b), oy + rr * math.sin(b))
        inner.append(p)
    return outer + inner


def _earbud(cx, cy, r, side):
    """A shaded true-wireless earbud: round housing with a driver grille facing the centre, a
    silicone tip, and a stem hanging down and outward. side -1 = left of centre (faces right)."""
    o = []
    face = 0 if side < 0 else 180       # direction of the tip (towards the chip)
    fa = math.radians(face)
    # stem
    sa = math.radians(90 + side * 14)
    sx0, sy0 = cx + math.cos(sa) * r * .55, cy + math.sin(sa) * r * .55
    L = r * 1.75
    sx1, sy1 = sx0 + math.cos(sa) * L, sy0 + math.sin(sa) * L
    wv = (-math.sin(sa), math.cos(sa))
    sw0, sw1 = r * .3, r * .24
    stem = ([(sx0 + wv[0] * sw0, sy0 + wv[1] * sw0), (sx1 + wv[0] * sw1, sy1 + wv[1] * sw1)]
            + [(sx1 + sw1 * math.cos(sa + math.pi / 2 - math.pi * i / 8), sy1 + sw1 * math.sin(sa + math.pi / 2 - math.pi * i / 8)) for i in range(9)]
            + [(sx0 - wv[0] * sw0, sy0 - wv[1] * sw0)])
    # cast shadow behind everything
    blob = C._ell_pts(cx + 3, cy + 3, r, r, 32)
    o.append(f'<path d="{_P(blob)}{_P([(x + 3, y + 3) for x, y in stem])}" fill="#000" stroke="none"/>')
    o.append(f'<path d="{_P(stem)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    # stem shading: the side away from the light
    shade_side = [(sx0 + wv[0] * sw0 * (1 if side > 0 else -1) * .1, sy0 + wv[1] * sw0 * (1 if side > 0 else -1) * .1)]
    k = 1 if side < 0 else -1          # which half is dark (right half of left bud's stem)
    half = [(sx0, sy0), (sx1, sy1), (sx1 - k * wv[0] * sw1, sy1 - k * wv[1] * sw1), (sx0 - k * wv[0] * sw0, sy0 - k * wv[1] * sw0)]
    del shade_side
    o.append(f'<path d="{_P(half)}" fill="{C.pat("M")}" stroke="none"/>')
    edge = [(sx0 - k * wv[0] * sw0 * .75, sy0 - k * wv[1] * sw0 * .75), (sx1 - k * wv[0] * sw1 * .75, sy1 - k * wv[1] * sw1 * .75)]
    o.append(f'<path d="{_P(edge, False)}" stroke="#000" stroke-width="1.5"/>')
    lt = [(sx0 + k * wv[0] * sw0 * .55, sy0 + k * wv[1] * sw0 * .55), (sx1 + k * wv[0] * sw1 * .55, sy1 + k * wv[1] * sw1 * .55)]
    o.append(f'<path d="{_hd(C.hatch_poly([(sx0, sy0), (sx1, sy1), (sx1 + k * wv[0] * sw1, sy1 + k * wv[1] * sw1), (sx0 + k * wv[0] * sw0, sy0 + k * wv[1] * sw0)], math.degrees(sa), 3, .5))}" stroke="#000" stroke-width=".5"/>')
    del lt
    # stem mic slot at the foot
    o.append(f'<path d="M{_n(sx1 - wv[0] * sw1 * .4)},{_n(sy1 - wv[1] * sw1 * .4)}L{_n(sx1 + wv[0] * sw1 * .4)},{_n(sy1 + wv[1] * sw1 * .4)}" stroke="#000" stroke-width="1.5"/>')
    # housing
    ball = C._ell_pts(cx, cy, r, r, 40)
    o.append(f'<path d="{_P(ball)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_P(ball)}" fill="{C.pat("L")}" stroke="none"/>')
    o.append(f'<path d="{_P(_crescent(cx, cy, r, 45 if side < 0 else 135, .45))}" fill="{C.pat("M")}" stroke="none"/>')
    o.append(f'<path d="{_P(_crescent(cx, cy, r, 60 if side < 0 else 120, .82))}" fill="{C.pat("X")}" stroke="none"/>')
    o.append(f'<path d="{_P(ball)}" fill="none" stroke="#000" stroke-width="1.5"/>')
    # specular highlight
    o.append(f'<path d="{_P(C._ell_pts(cx - r * .38, cy - r * .42, r * .16, r * .09, 14))}" fill="#fff" stroke="none"/>')
    # silicone tip toward the chip
    tx, ty = cx + math.cos(fa) * r * .95, cy + math.sin(fa) * r * .95 - r * .1
    tip = C._ell_pts(tx, ty, r * .32, r * .48, 24)
    o.append(f'<path d="{_P(tip)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_hd(C.hatch_poly(tip, 90, 2, .3))}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_P(C._ell_pts(tx + math.cos(fa) * r * .12, ty, r * .12, r * .2, 14))}" fill="#000" stroke="none"/>')
    # five-driver grille ring on the outer face (rows of dots)
    gx, gy = cx - math.cos(fa) * r * .15, cy + r * .05
    gr = r * .42
    o.append(f'<path d="{_P(C._ell_pts(gx, gy, gr, gr, 28))}" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_P(C._ell_pts(gx, gy, gr - 1, gr - 1, 28))}" fill="{C.pat("S")}" stroke="none"/>')
    dots = []
    for j in range(5):
        a = math.radians(-90 + 72 * j)
        dots.append(C._ell_pts(gx + gr * .55 * math.cos(a), gy + gr * .55 * math.sin(a), gr * .17, gr * .17, 10))
    o.append(f'<path d="{"".join(_P(d) for d in dots)}" fill="#000" stroke="#fff" stroke-width=".5"/>')
    return "".join(o)


# ---------------------------------------------------------------- the vignette

def _vignette(x, y, w, h):
    cx, cy, field = _field(x, y, w, h)
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    fw, fh = max(xs) - min(xs), max(ys) - min(ys)
    band = _MODE["m"] == "band"
    rng = random.Random(int(fw * 7 + fh * 13))
    cid = f"n3f{int(fw)}x{int(fh)}"
    o = [f'<clipPath id="{cid}"><path d="{_P(field)}"/></clipPath><g clip-path="url(#{cid})">']
    o.append(f'<path d="{_P(field)}" fill="#fff" stroke="none"/>')
    o.append(C.dark_ground(field, "G"))
    square = fh > fw * .75
    if band:
        S = min(fw * .5, fh * .62)
        ccx, ccy = cx, cy
    elif square:
        S = min(fw * .38, fh * .38)
        ccx, ccy = cx, cy - fh * .12
    else:
        S = min(fw * .34, fh * .56)
        ccx, ccy = cx, cy - fh * .02
    ext = max(fw, fh)
    tp = max(2.5, S * .045)
    lines, vias = _traces(ccx, ccy, S, S / 2, ext * .5, rng, tp * 2)
    o.append(f'<path d="{_hd(lines)}" stroke="#000" stroke-width="{3 if S >= 60 else 2.5}" fill="none"/>')
    o.append(f'<path d="{_hd(lines)}" stroke="#fff" stroke-width="1.5" fill="none"/>')
    vr = 2.6 if S >= 60 else 2.
    vd = "".join(_P(C._ell_pts(vx, vy, vr, vr, 12)) for vx, vy in vias)
    o.append(f'<path d="{vd}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(_P(C._ell_pts(vx, vy, .8, .8, 6)) for vx, vy in vias)}" fill="#000" stroke="none"/>')
    if not band:
        cv = C.Canvas()
        for sx in (-1, 1):
            for sy in (-1, 1):
                ang = math.degrees(math.atan2(sy, sx))
                C.acanthus_frond(ccx + sx * S * .5, ccy + sy * S * .5, ang, S * .5, 3, 34,
                                 .9 * sx * sy, 4.5 * sx * sy, rng.randrange(999), cv=cv)
        o.append(cv.svg())
    o.append(_chip(ccx, ccy, S, rng))
    if not band:
        if square:
            r = fw * .095
            pos = [(cx + sd * fw * .31, cy + fh * .2) for sd in (-1, 1)]
        else:
            room = fw / 2 - S / 2 - S * .3
            r = min(room * .34, fh * .19)
            pos = [(ccx + sd * (S / 2 + S * .25 + room * .5), ccy - r * .5) for sd in (-1, 1)]
        if r >= 9:
            for (ex, ey), side in zip(pos, (-1, 1)):
                o.append(_earbud(ex, ey, r, side))
        dl = min(S * .32, 28)
        if square:
            dx, dy = cx, cy + fh * .27
        else:
            dx, dy = cx, ccy - S / 2 - S * .1 - dl * .45
        dpol = _drumsticks(dx, dy, dl, 0 if square else 180)
        o.append(f'<path d="{"".join(_P(a) + _P(b) for a, b in dpol)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append("</g>")
    return "".join(o)


def _waveform(centre, bh):
    """An audio waveform engraved along the ribbon's face (the page is A/V news): the face lightly
    ruled, a black symmetric wave whose envelope swells and beats, with a white centre line."""
    o = []
    n = len(centre) - 1
    top, bot = [], []
    for i in range(n + 1):
        x0, y0 = centre[max(0, i - 1)]
        x1, y1 = centre[min(n, i + 1)]
        a = math.atan2(y1 - y0, x1 - x0)
        top.append((centre[i][0] + math.sin(a) * bh * .36, centre[i][1] - math.cos(a) * bh * .36))
        bot.append((centre[i][0] - math.sin(a) * bh * .36, centre[i][1] + math.cos(a) * bh * .36))
    o.append(f'<path d="{_P(top + bot[::-1])}" fill="{C.pat("L")}" stroke="none"/>')
    # dense wave as vertical strokes
    strokes = []
    x0, x1 = centre[0][0], centre[-1][0]
    m = int((x1 - x0) / 1.5)
    for j in range(m + 1):
        x = x0 + (x1 - x0) * j / m
        u = j / m
        k = min(int(u * n), n - 1)
        f = u * n - k
        yc = centre[k][1] * (1 - f) + centre[k + 1][1] * f
        env = (math.sin(math.pi * u) ** .7) * (.55 + .45 * abs(math.sin(u * 23.)) * abs(math.sin(u * 7.3 + 1)))
        amp = bh * .34 * env * (.6 + .4 * abs(math.sin(j * 1.7)))
        if amp > .4:
            strokes.append([(x, yc - amp), (x, yc + amp)])
    o.append(f'<path d="{_hd(strokes)}" stroke="#000" stroke-width="1" stroke-linecap="butt"/>')
    return "".join(o)


def _dimm(tx, ty, tw, th):
    """The pedestal's tablet engraved as a memory module: ruled board, a row of DRAM packages
    with legs and highlights, gold-finger contacts along the foot, a notch."""
    o = []
    o.append(f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{C.pat("D")}" stroke="none"/>')
    fh = max(2.5, th * .26)
    fy = ty + th - fh - 1
    fingers = []
    x = tx + 4
    notch = tx + tw * .62
    while x < tx + tw - 4:
        if not (notch - 3 < x < notch + 3):
            fingers.append(f"M{_n(x)},{_n(fy)}h1.5v{_n(fh)}h-1.5z")
        x += 3
    o.append(f'<path d="{"".join(fingers)}" fill="#000" stroke="none"/>')
    ch = (th - fh - 3) * .78
    cy = ty + 2 + (th - fh - 3 - ch) / 2
    nchip = 8
    cw = min(ch * 2.6, (tw - 16) / nchip - 6)
    gap = (tw - 8 - nchip * cw) / (nchip + 1)
    pk, leg, hl = [], [], []
    for i in range(nchip):
        cx = tx + 4 + gap + i * (cw + gap)
        pk.append(f"M{_n(cx)},{_n(cy)}h{_n(cw)}v{_n(ch)}h{_n(-cw)}z")
        lx = cx + 1.5
        while lx < cx + cw - 1:
            leg.append(f"M{_n(lx)},{_n(cy - 1.2)}v{_n(ch + 2.4)}")
            lx += 2
        hl.append(f"M{_n(cx + 1.5)},{_n(cy + 1)}h{_n(cw * .4)}")
    o.append(f'<path d="{"".join(leg)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(pk)}" fill="#000" stroke="#fff" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(hl)}" stroke="#fff" stroke-width=".5"/>')
    return "".join(o)


def _tall(w, h, seed, fill_fn, density=1.):
    """engraving_codex._layout_tall, copied so the ribbon carries a waveform and the pedestal's
    tablet a memory module instead of blank white."""
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
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
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(fill_fn(ix, iy, iw, ih))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_waveform(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, tab = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_dimm(*tab))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    _MODE["m"] = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    if _MODE["m"] == "tall":
        return C.svg_doc(w, h, _tall(w, h, seed, _vignette))
    return C.frame_plate(w, h, seed, _vignette)
