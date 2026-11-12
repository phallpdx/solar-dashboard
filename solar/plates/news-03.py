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

def _vignette(x, y, w, h, fld=None):
    if fld is not None:
        field = list(fld)
        cx = (min(p[0] for p in field) + max(p[0] for p in field)) / 2
        cy = (min(p[1] for p in field) + max(p[1] for p in field)) / 2
    else:
        cx, cy, field = _field(x, y, w, h)
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    fw, fh = max(xs) - min(xs), max(ys) - min(ys)
    band = _MODE["m"] == "band"
    rng = random.Random(int(fw * 7 + fh * 13))
    cid = f"n3f{int(fw)}x{int(fh)}"
    o = [f'<clipPath id="{cid}"><path d="{_P(field)}"/></clipPath><g clip-path="url(#{cid})">']
    o.append(f'<path d="{_P(field)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_P(field)}" fill="url(#s2o)" stroke="none"/>')
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
                ang = math.atan2(sy, sx)
                for k, da in enumerate((-.45, .45, 0.)):
                    ll = S * (.34 if k < 2 else .42)
                    _leaf(cv, ccx + sx * S * .46, ccy + sy * S * .46, ang + da, ll, ll * .24,
                          (1 if da >= 0 else -1) * .9, -(1 if da >= 0 else -1) * 1.6, rng, 3)
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
    o.append(f'<path d="{"".join(pk)}" fill="url(#s2m)" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{"".join(hl)}" stroke="#fff" stroke-width="1"/>')
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


def _hifi(fld, seed):
    """The A/V desk: a turntable on its plinth and a monitor speaker on the sideboard, the wall
    stippled behind them. Easter egg: a little drum kit reflected in the woofer's cone."""
    xs = [q[0] for q in fld]
    ys = [q[1] for q in fld]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W, H = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    rng = random.Random(seed)
    d = C._d(fld, True, 0)
    o = [f'<path d="{d}" fill="url(#s2o)"/>']
    cv = C.Canvas()
    top = y0 + H * .7
    # the record wall: a shelf of LPs standing in their sleeves, spines hatched, one face-out
    shy = y0 + H * .4
    cv.obj([[(x0 - 2, shy), (x1 + 2, shy), (x1 + 2, shy + 3), (x0 - 2, shy + 3)]], 1.)
    cv.hair(C.hatch_poly([(x0 - 2, shy + 3), (x1 + 2, shy + 3), (x1 + 2, shy + 6), (x0 - 2, shy + 6)], 0, 1.5))
    lh = H * .26
    xx = x0
    k = 0
    while xx < x1:
        sw_ = rng.uniform(2.2, 4.)
        tilt = 0 if k % 9 else rng.uniform(1, 3)
        sp = [(xx, shy), (xx + sw_, shy), (xx + sw_ + tilt, shy - lh * rng.uniform(.93, 1.)), (xx + tilt, shy - lh * rng.uniform(.93, 1.))]
        cv.obj([sp], .5)
        if k % 3:
            cv.hair(C.hatch_poly(sp, 90 if k % 2 else 0, 1.5))
        xx += sw_
        k += 1
        if k == 23:
            fx = xx + 2
            face = [(fx, shy), (fx + lh * .95, shy), (fx + lh * .95, shy - lh * .95), (fx, shy - lh * .95)]
            cv.obj([face], 1.)
            cv.hair(C._ell_pts(fx + lh * .47, shy - lh * .47, lh * .33, lh * .33, 28))
            cv.hair(C._ell_pts(fx + lh * .47, shy - lh * .47, lh * .1, lh * .1, 14))
            cv.hair(C.hatch_poly([(fx, shy - lh * .95), (fx + lh * .95, shy - lh * .95), (fx + lh * .95, shy - lh * .7), (fx, shy - lh * .7)], 0, 1.5))
            xx = fx + lh * .95 + 2
    # sideboard: walnut top in perspective, grain, a dark front
    sb = [(x0 - 2, top), (x1 + 2, top), (x1 + 2, top + H * .07), (x0 - 2, top + H * .07)]
    cv.obj([sb], 1.)
    yy = top + 1.5
    while yy < top + H * .07 - 1:
        cv.hair([(xx, yy + .4 * math.sin(xx * .07 + yy)) for xx in range(int(x0), int(x1) + 3, 4)])
        yy += 2
    fr = [(x0 - 2, top + H * .07), (x1 + 2, top + H * .07), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]
    cv.obj([fr], 1.)
    cv.hair(C.hatch_poly(fr, 0, 1.5))
    cv.hair(C.hatch_poly(fr, 90, 3))
    for k in range(1, 4):
        dx = x0 + W * k / 4
        cv.obj([[(dx - 1, top + H * .1), (dx + 1, top + H * .1), (dx + 1, y1 + 2), (dx - 1, y1 + 2)]], 0)
    S = min(H * .62, W * .34)
    # the turntable
    tx = cx - W * .14
    pw, pd = S * 1.3, S * .42
    by = top + H * .02
    plinth = [(tx - pw / 2, by - pd * .2), (tx + pw / 2, by - pd * .2), (tx + pw / 2 - pd * .3, by - pd), (tx - pw / 2 + pd * .3, by - pd)]
    cv.obj([plinth], 1.)
    side = [(tx - pw / 2, by - pd * .2), (tx + pw / 2, by - pd * .2), (tx + pw / 2, by), (tx - pw / 2, by)]
    cv.obj([side], 1.)
    cv.hair(C.hatch_poly(side, 0, 1.5))
    pcx, pcy = tx - pw * .08, by - pd * .6
    pr = pw * .33
    rec = C._ell_pts(pcx, pcy, pr, pr * .3, 48)[:-1]
    cv.obj([rec], 1.)
    k = .95
    while k > .32:
        cv.hair(C._ell_pts(pcx, pcy, pr * k, pr * .3 * k, 40))
        k -= .07
    cv.hair(C.hatch_poly([q for q in rec if q[0] > pcx + pr * .3] + [(pcx + pr * .3, pcy)], 0, 1.5))
    cv.obj([C._ell_pts(pcx, pcy, pr * .26, pr * .078, 20)[:-1]], 1.)
    cv.line([(pcx + pr * .22, pcy - pr * .3), (pcx + pr * .26, pcy - pr * .3)])
    ax, ay = tx + pw * .38, by - pd * .75
    cv.obj([C._ell_pts(ax, ay, pw * .05, pw * .02, 12)[:-1]], 1.)
    cv.obj([], 0)
    cv.line([(ax, ay), (ax - pw * .02, ay + pd * .1), (pcx + pr * .45, pcy + pr * .02)])
    cv.obj([[(pcx + pr * .4, pcy - 1), (pcx + pr * .5, pcy - 1), (pcx + pr * .5, pcy + 1.5), (pcx + pr * .4, pcy + 1.5)]], .5)
    # the speaker
    sx = cx + W * .26
    sw, sh = S * .72, S * 1.15
    st = top + H * .01 - sh
    cab = [(sx - sw / 2, st), (sx + sw / 2, st), (sx + sw / 2, st + sh), (sx - sw / 2, st + sh)]
    cv.obj([cab], 1.)
    sd = [(sx + sw / 2, st), (sx + sw / 2 + sw * .18, st - sw * .1), (sx + sw / 2 + sw * .18, st + sh - sw * .1), (sx + sw / 2, st + sh)]
    cv.obj([sd], 1.)
    cv.hair(C.hatch_poly(sd, 90, 1.5))
    cv.hair(C.hatch_poly(sd, 30, 3))
    tp = [(sx - sw / 2, st), (sx + sw / 2, st), (sx + sw / 2 + sw * .18, st - sw * .1), (sx - sw / 2 + sw * .18, st - sw * .1)]
    cv.obj([tp], 1.)
    cv.hair(C.hatch_poly(tp, 0, 3))
    wr = sw * .36
    wy = st + sh * .62
    cv.obj([C._ell_pts(sx, wy, wr + 1.5, wr + 1.5, 40)[:-1]], 1.)
    for k in range(1, 7):
        cv.hair(C._ell_pts(sx, wy, wr * (1 - k * .11), wr * (1 - k * .11), 36))
    cv.hair(C.hatch_poly([(sx + wr * math.cos(t), wy + wr * math.sin(t)) for t in [-.6 + j * .12 for j in range(20)]] + [(sx, wy)], 60, 1.5, .5))
    # Easter egg: the kit in the cone - bass drum, two toms, two cymbals
    e = wr * .34
    cv.obj([C._ell_pts(sx, wy + e * .25, e * .55, e * .55, 16)[:-1]], .5)
    cv.obj([C._ell_pts(sx - e * .5, wy - e * .35, e * .28, e * .2, 12)[:-1]], .5)
    cv.obj([C._ell_pts(sx + e * .5, wy - e * .35, e * .28, e * .2, 12)[:-1]], .5)
    cv.hair([(sx - e * 1.1, wy - e * .9), (sx - e * .5, wy - e * .75)])
    cv.hair([(sx + e * .5, wy - e * .8), (sx + e * 1.1, wy - e * .95)])
    tw = st + sh * .2
    cv.obj([C._ell_pts(sx, tw, sw * .1, sw * .1, 16)[:-1]], 1.)
    cv.hair(C._ell_pts(sx, tw, sw * .05, sw * .05, 10))
    o.append(cv.svg())
    return "".join(o)


# ==== STUDIO FRAME (batch 2) ====================================================================
# King-tier frame, copied into this plate so it can be cut to the page (house rule: the shared
# modules stay untouched). Fine English scroll as on the GRS vise and Ken Hunt's panels: dozens of
# small logarithmic spirals grown from one stem, each branching into the next and carrying its own
# shaded leaves, packed over a punched matte ground; white "gold-line" wire borders and beading
# frame every panel; the subject sits in an inlaid medallion ringed with beads.
import math as _m
import random as _rnd
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _m.pi
_sm = _C._smooth


def _st_mat_tile():
    """An 8 px matte tile: black punched with 1 px white dots set evenly (blue noise)."""
    rng = _rnd.Random(91)
    pts = []
    tries = 0
    while len(pts) < 13 and tries < 4000:
        tries += 1
        p = (rng.randrange(16) * .5, rng.randrange(16) * .5)
        ok = True
        for q in pts:
            dx = min(abs(p[0] - q[0]), 8 - abs(p[0] - q[0]))
            dy = min(abs(p[1] - q[1]), 8 - abs(p[1] - q[1]))
            if dx * dx + dy * dy < 3.6:
                ok = False
                break
        if ok:
            pts.append(p)
    return "".join(f"M{_C._n(x)},{_C._n(y)}h1v1h-1z" for x, y in pts)


_ST_DEFS = ('<defs><pattern id="s2m" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h8v8h-8z" fill="#000"/><path d="{_st_mat_tile()}" fill="#fff"/></pattern>'
            '<pattern id="s2o" width="2" height="2" patternUnits="userSpaceOnUse"><path d="M0,0h.5v.5h-.5zM1,1h.5v.5h-.5z" fill="#000"/></pattern></defs>')


def st_matte(d):
    """The punched matte ground over path data d."""
    return f'<path d="{d}" fill="url(#s2m)" stroke="none"/>'


def st_rect_d(x, y, w, h):
    return f"M{_C._n(x)},{_C._n(y)}h{_C._n(w)}v{_C._n(h)}h{_C._n(-w)}z"


# ---------------------------------------------------------------------------------------------
# the fine scroll: spirals, leaves, growth from one stem
# ---------------------------------------------------------------------------------------------

def _spiral(px, py, head, R, s, turns):
    """A log spiral leaving (px, py) heading `head`, first radius R, turning toward side s
    (+1 = the +normal side), winding `turns` into an eye at .13 R. -> (pts, centre, radii)."""
    th = _TAU * turns
    b = _m.log(1 / .13) / th
    a0 = _m.atan2(s * R, -b * R)
    rot = head - a0
    cr, sr = _m.cos(rot), _m.sin(rot)
    pts, rad = [], []
    t = 0.
    while True:
        r = R * _m.exp(-b * t)
        lx, ly = r * _m.cos(t) - R, s * r * _m.sin(t)
        pts.append((px + lx * cr - ly * sr, py + lx * sr + ly * cr))
        rad.append(r)
        if t >= th:
            break
        t = min(th, t + max(.05, 1.4 / r))
    return pts, (px - R * cr, py - R * sr), rad


def _tangent(pts, i):
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    return _m.atan2(b[1] - a[1], b[0] - a[0])


class _Grid:
    def __init__(self, cell=24.):
        self.c = cell
        self.g = {}
        self.maxr = 0.

    def add(self, x, y, r, oid):
        self.g.setdefault((int(x // self.c), int(y // self.c)), []).append((x, y, r, oid))
        self.maxr = max(self.maxr, r)

    def clear(self, x, y, r, slack, ignore):
        reach = r + self.maxr
        c = self.c
        for i in range(int((x - reach) // c), int((x + reach) // c) + 1):
            for j in range(int((y - reach) // c), int((y + reach) // c) + 1):
                for qx, qy, qr, oid in self.g.get((i, j), ()):
                    if oid != ignore and (qx - x) ** 2 + (qy - y) ** 2 < ((r + qr) * slack) ** 2:
                        return False
        return True


def st_sweep(x, y, ang, L, k0, k1=None, n=None):
    """A sweeping stem: from (x, y) heading ang (radians), L long, curvature k0 -> k1 (1/px)."""
    k1 = k0 if k1 is None else k1
    return _C._euler(x, y, ang, L, lambda u: k0 + (k1 - k0) * u, n or max(8, int(L / 2)))


class ScrollField:
    """Grows fine scroll over a region. inside(x, y) says where scroll may grow. Scrolls branch
    from stems and from one another, each sized to the room it finds, until the field is packed."""

    def __init__(self, inside, rmin=7., rmax=30., seed=0, slack=.88):
        self.inside = inside
        self.rmin, self.rmax = rmin, rmax
        self.rng = _rnd.Random(seed)
        self.grid = _Grid(20.)
        self.slack = slack
        self.items = []
        self.queue = []

    def _ok(self, c, R, parent):
        if not self.inside(c[0], c[1]):
            return False
        if parent is not None and self.items[parent][1] == "scroll":
            pc, pR = self.items[parent][2][1], self.items[parent][2][4]
            if (pc[0] - c[0]) ** 2 + (pc[1] - c[1]) ** 2 < ((pR + R) * .78) ** 2:
                return False
        for k in range(8):
            a = k * _TAU / 8
            if not self.inside(c[0] + R * .55 * _m.cos(a), c[1] + R * .55 * _m.sin(a)):
                return False
        return self.grid.clear(c[0], c[1], R, self.slack, parent)

    def stem(self, pts, w0=2.2, w1=1.2, leaves=True, gen=0):
        """A sweeping lead, the source the scrolls grow from (points run from the root out)."""
        oid = len(self.items)
        for p in pts[::2]:
            self.grid.add(p[0], p[1], 2.5, oid)
        self.items.append((gen, "stem", (pts, w0, w1, leaves)))
        self.queue.append((gen, oid, "stem", pts, 0, None))
        return oid

    def scroll(self, px, py, head, R, s, gen=0, parent=None, turns=None, force=False):
        turns = turns or self.rng.uniform(1.25, 1.55)
        pts, c, rad = _spiral(px, py, head, R, s, turns)
        if not force and not self._ok(c, R, parent):
            return False
        oid = len(self.items)
        self.grid.add(c[0], c[1], R, oid)
        self.items.append((gen, "scroll", (pts, c, rad, s, R)))
        self.queue.append((gen, oid, "scroll", pts, s, (c, R)))
        return True

    def grow(self, max_items=300):
        rng = self.rng
        qi = 0
        while qi < len(self.queue) and len(self.items) < max_items:
            gen, oid, kind, pts, s, info = self.queue[qi]
            qi += 1
            n = len(pts)
            cand = []
            if kind == "scroll":
                c, R = info
                for f in (.03, .14, .27, .4, .52):
                    i = int(f * (n - 1))
                    q = pts[i]
                    tau = _tangent(pts, i)
                    rh = _m.hypot(q[0] - c[0], q[1] - c[1])
                    cand.append((q, tau, -s, self.rmax))
                    cand.append((q, tau + _PI, s, self.rmax * .8))
            else:
                for i in range(3, n - 2, 4):
                    q = pts[i]
                    tau = _tangent(pts, i)
                    for sd in (1, -1):
                        cand.append((q, tau + sd * .15, -sd, self.rmax))
                        cand.append((q, tau + _PI - sd * .2, sd, self.rmax * .7))
                rng.shuffle(cand)
            for q, head, cs, top in cand:
                Rc = min(self.rmax, top)
                while Rc >= self.rmin:
                    if self.scroll(q[0], q[1], head + cs * rng.uniform(-.05, .2), Rc, cs, gen + 1, oid):
                        break
                    Rc *= .82
        return self

    def _branch_to(self, oid, cx, cy, R):
        """A scroll centred at (cx, cy) whose stem leads in from the nearest coil of item oid,
        joining it tangentially, so every scroll grows out of another."""
        it = self.items[oid]
        pts = it[2][0]
        if it[1] == "scroll":
            pc, pR, rad = it[2][1], it[2][4], it[2][2]
            idx = [i for i in range(0, len(pts), 2) if rad[i] > pR * .45 and
                   (pts[i][0] - pc[0]) * (cx - pts[i][0]) + (pts[i][1] - pc[1]) * (cy - pts[i][1]) > 0] or list(range(0, len(pts) // 3))
        else:
            idx = list(range(0, len(pts), 2))
        bi = min(idx, key=lambda i: (pts[i][0] - cx) ** 2 + (pts[i][1] - cy) ** 2)
        q = pts[bi]
        tau = _tangent(pts, bi)
        ua = _m.atan2(q[1] - cy, q[0] - cx)
        S = (cx + R * _m.cos(ua), cy + R * _m.sin(ua))
        hx, hy = _m.cos(tau), _m.sin(tau)
        if hx * (S[0] - q[0]) + hy * (S[1] - q[1]) < 0:
            hx, hy = -hx, -hy
        turns = self.rng.uniform(1.25, 1.55)
        th = _TAU * turns
        bb = _m.log(1 / .13) / th
        best = None
        for sg in (1, -1):
            tx = -bb * _m.cos(ua) - sg * _m.sin(ua)
            ty = -bb * _m.sin(ua) + sg * _m.cos(ua)
            dot = tx * hx + ty * hy
            if best is None or dot > best[0]:
                best = (dot, sg, tx, ty)
        _, sg, tx, ty = best
        tl = _m.hypot(tx, ty)
        tx, ty = tx / tl, ty / tl
        L = _m.hypot(S[0] - q[0], S[1] - q[1])
        lead = []
        if L > 1.5:
            k = L * .45 + 2
            p1 = (q[0] + hx * k, q[1] + hy * k)
            p2 = (S[0] - tx * k, S[1] - ty * k)
            m = max(3, int(L / 1.5))
            for i in range(m):
                t = i / m
                a, b_, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
                lead.append((a * q[0] + b_ * p1[0] + c * p2[0] + d * S[0], a * q[1] + b_ * p1[1] + c * p2[1] + d * S[1]))
        sp, rad = [], []
        t = 0.
        while True:
            r = R * _m.exp(-bb * t)
            ph = ua + sg * t
            sp.append((cx + r * _m.cos(ph), cy + r * _m.sin(ph)))
            rad.append(r)
            if t >= th:
                break
            t = min(th, t + max(.05, 1.4 / r))
        allp = lead + sp
        allr = [R] * len(lead) + rad
        noid = len(self.items)
        self.grid.add(cx, cy, R, noid)
        self.items.append((it[0] + 1, "scroll", (allp, (cx, cy), allr, sg, R)))
        return True

    def fill(self, x, y, w, h, step=5., max_items=320):
        """Pack the field: find the widest free spot, branch a scroll into it from the nearest
        scroll's outer coil, repeat until no gap of about rmin is left."""
        rng = self.rng
        P = []
        nx, ny = max(2, int(w / step)), max(2, int(h / step))
        for j in range(ny):
            for i in range(nx):
                px, py = x + (i + .5) * w / nx, y + (j + .5) * h / ny
                if self.inside(px, py):
                    P.append([px, py, 1e9, None])
        if not P:
            return self
        cell = {}
        for k, p in enumerate(P):
            cell.setdefault((int(p[0] // 30), int(p[1] // 30)), []).append(k)

        def upd(oid, cx, cy, R, reach=None):
            reach = R + (reach or self.rmax * 3)
            for i in range(int((cx - reach) // 30), int((cx + reach) // 30) + 1):
                for j in range(int((cy - reach) // 30), int((cy + reach) // 30) + 1):
                    for k in cell.get((i, j), ()):
                        p = P[k]
                        d = _m.hypot(p[0] - cx, p[1] - cy) - R
                        if d < p[2]:
                            p[2], p[3] = d, oid
        obs = []
        for oid, it in enumerate(self.items):
            if it[1] == "scroll":
                obs.append((it[2][1][0], it[2][1][1], it[2][4], oid))
            else:
                obs.extend((q[0], q[1], 2.5, oid) for q in it[2][0][::5])
        for p in P:
            for ox, oy, orr, oid in obs:
                d = _m.hypot(p[0] - ox, p[1] - oy) - orr
                if d < p[2]:
                    p[2], p[3] = d, oid
        import heapq
        hp = [(-p[2], k) for k, p in enumerate(P)]
        heapq.heapify(hp)
        while len(self.items) < max_items and hp:
            nd, k = heapq.heappop(hp)
            best = P[k]
            if -nd != best[2]:
                heapq.heappush(hp, (-best[2], k))
                continue
            if best[2] < self.rmin * 1.15:
                break
            px, py, D, oid = best
            if oid is None:
                continue
            R = min(self.rmax, D * .97) * rng.uniform(.9, 1.)
            self._branch_to(oid, px, py, R)
            upd(len(self.items) - 1, px, py, R)
            for kk in cell.get((int(px // 30), int(py // 30)), ()):
                heapq.heappush(hp, (-P[kk][2], kk))
        return self

    def draw(self, cv, egg=None, egg_gen=2):
        """Paint the branches first so each parent lies over its children. egg(cv, x, y, r) is
        cut into the eye of one scroll of generation egg_gen (the first big enough)."""
        rng = _rnd.Random(7)
        order = sorted(range(len(self.items)), key=lambda k: -self.items[k][0])
        egg_done = egg is None
        for k in order:
            gen, kind, data = self.items[k]
            if kind == "stem":
                pts, w0, w1, lv = data
                _draw_stem(cv, pts, w0, w1, rng, lv)
                continue
            pts, c, rad, s, R = data
            use = None
            if not egg_done and gen >= egg_gen and R > 14:
                use, egg_done = egg, True
            _draw_scroll(cv, pts, c, rad, s, R, rng, use)


def _leaf(cv, x, y, ang, L, W, bend, curl, rng, lobes=None):
    """A fine-scroll leaf: a curved blade scalloped on its outer edge and turning over at the tip,
    fine parallel cuts on its shadow side, a bright cut edge, a centre vein."""
    n = max(8, int(L / 1.2))
    sp = _C._euler(x, y, ang, L, lambda u: (bend + curl * _sm(.55, 1., u) ** 2 * 3.2) / L, n)
    c = 1 if bend >= 0 else -1
    nl = lobes or (3 if L > 14 else 2)
    ph = rng.uniform(0, .3)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        pr = min(1., u / .22) ** .6 * (1 - u) ** .7 * 1.35
        v = (u * nl + ph) % 1.
        wo.append(W * pr * (.6 + .4 * _m.sin(_PI * v) ** .6) + .3)
        wi.append(W * pr * .85 + .3)
    R = _C._Rib(sp, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    cv.hair(_C._fill_lines(R, .22 * c, .92 * c, 1.5, .06, .9, 2))
    if W > 2.4:
        cv.hair(R.contour(-.05 * c, .12, .72))
    for j in range(nl):
        u = (j - ph) / nl
        if .18 < u < .85 and R.width(u, -c) > 1.8:
            cv.hair([R.at(u, -.95 * c), R.at(u + .05, -.4 * c)])
    return R


def _draw_stem(cv, pts, w0, w1, rng, leaves):
    n = len(pts)
    W = [w0 + (w1 - w0) * i / max(1, n - 1) for i in range(n)]
    R = _C._Rib(pts, W, W)
    if leaves:
        L = R.L
        u = .06
        sd = 1
        while u < .94:
            i = int(u * (n - 1))
            q = R.at(u, sd * .8)
            ll = rng.uniform(9, 13)
            _leaf(cv, q[0], q[1], _tangent(pts, i) + sd * .55, ll, ll * .22, -sd * .5, sd * 2.2, rng)
            sd = -sd
            u += rng.uniform(13, 18) / L
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(-.4, 0., 1.))
    cv.hair(R.contour(-.8, 0., 1.))


def _draw_scroll(cv, pts, c, rad, s, R, rng, egg=None):
    n = len(pts)
    hw0 = max(1., min(3.2, R * .13))
    W = [max(.6, hw0 * (rad[i] / R) ** .55) for i in range(n)]
    Rb = _C._Rib(pts, W, W)
    # where the coil proper starts (after any lead-in)
    k0 = 0
    while k0 < n - 1 and rad[k0 + 1] >= R - 1e-6:
        k0 += 1
    span = n - 1 - k0
    nlv = 1 if R < 10 else (2 if R < 16 else 3)
    fs = (.03, .2, .36)[:nlv]
    for j, f in enumerate(fs[::-1]):
        i = k0 + int(f * span)
        q = Rb.at(i / (n - 1), -s)
        ll = rad[i] * rng.uniform(.8, .95)
        _leaf(cv, q[0], q[1], _tangent(pts, i) - s * .55, ll, ll * .25, s * .9, -s * rng.uniform(1.2, 1.8), rng)
    if k0 > 6:
        i = k0 // 2
        q = Rb.at(i / (n - 1), s)
        ll = min(R * .7, 12.)
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .6, ll, ll * .24, -s * .7, s * 1.6, rng)
    cv.obj([Rb.outline()], .5)
    cv.hair(Rb.contour(.5 * s, 0., .92))
    if hw0 > 1.8:
        cv.hair(Rb.contour(.82 * s, 0., .8))
        cv.hair(Rb.contour(-.55 * s, .0, .35))
    if R > 15:
        i = k0 + int(.55 * span)
        q = Rb.at(i / (n - 1), s)
        ll = rad[i] * .95
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .35, ll, ll * .2, s * 1.6, s * .3, rng, 2)
    ex, ey = pts[-1]
    if egg:
        egg(cv, ex, ey, max(5., R * .4))
    else:
        rr = max(1.1, W[-1] * 1.4)
        cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)
        cv.line(_C._ell_pts(ex, ey, .3, .3, 4))


# ---------------------------------------------------------------------------------------------
# borders, beading, medallion, arms
# ---------------------------------------------------------------------------------------------

def st_wire(d):
    """A gold-line (wire inlay) border along path d: white wire, black, white wire on a black bed."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="5"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="3"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>')


def st_beads(d, pitch=3.5, r=1.):
    """A row of white beads on a black fillet along path d."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_C._n(2 * r + 2)}"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_C._n(2 * r)}" stroke-linecap="round" '
            f'stroke-dasharray="0 {_C._n(pitch)}"/>')


def st_ell_d(cx, cy, rx, ry, n=96):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n), True, .1)


def st_poly_d(poly):
    return _C._d(list(poly), True, .1)


def st_medallion(cx, cy, rx, ry):
    """An inlaid portrait medallion: wire, a ring of beads, wire. -> (svg, field polygon)."""
    o = [f'<path d="{st_ell_d(cx, cy, rx + 7, ry + 7)}" fill="#000" stroke="none"/>',
         st_wire(st_ell_d(cx, cy, rx + 5.5, ry + 5.5)),
         st_beads(st_ell_d(cx, cy, rx + 1.5, ry + 1.5, 180), 3.5, 1.),
         f'<path d="{st_ell_d(cx, cy, rx - .5, ry - .5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), _C._ell_pts(cx, cy, rx - 1.2, ry - 1.2, 120)[:-1]


def st_arch(cx, top, bot, half, n=48):
    """An arched (round-headed) panel polygon: the binding's central panel."""
    r = half
    pts = [(cx - half, bot)]
    for i in range(n + 1):
        a = _PI + _PI * i / n
        pts.append((cx + r * _m.cos(a), top + r + r * _m.sin(a)))
    pts.append((cx + half, bot))
    return pts


def st_arch_medallion(cx, top, bot, half):
    o = [f'<path d="{st_poly_d(st_arch(cx, top - 7, bot + 7, half + 7))}" fill="#000" stroke="none"/>',
         st_wire(st_poly_d(st_arch(cx, top - 5.5, bot + 5.5, half + 5.5))),
         st_beads(st_poly_d(st_arch(cx, top - 1.5, bot + 1.5, half + 1.5, 96)), 3.5, 1.),
         f'<path d="{st_poly_d(st_arch(cx, top + .5, bot - .5, half - .5))}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_arch(cx, top + 1.2, bot - 1.2, half - 1.2, 72)


def st_shape_pts(shape, cx, cy, rx, ry, g=0., n=120, ph=0.):
    """The outline of a shaped panel grown outward by g: oval, roundel, arch or irregular."""
    if shape == "arch":
        return st_arch(cx, cy - ry - g, cy + ry + g, rx + g, max(24, n // 2))
    if shape == "roundel":
        rx = ry = min(rx, ry)
    pts = []
    for i in range(n):
        t = _TAU * i / n
        k = 1.
        if shape == "irregular":
            k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
        pts.append((cx + (rx * k + g) * _m.cos(t), cy + (ry * k + g) * _m.sin(t)))
    return pts


def st_shape_in(shape, x, y, cx, cy, rx, ry, g=0., ph=0.):
    if shape == "arch":
        if y >= cy - ry + rx:
            return abs(x - cx) < rx + g and y < cy + ry + g
        return _m.hypot(x - cx, y - (cy - ry + rx)) < rx + g
    if shape == "roundel":
        rx = ry = min(rx, ry)
    t = _m.atan2((y - cy) / max(ry, 1), (x - cx) / max(rx, 1))
    k = 1.
    if shape == "irregular":
        k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
    return ((x - cx) / (rx * k + g)) ** 2 + ((y - cy) / (ry * k + g)) ** 2 < 1


def st_shaped_medallion(shape, cx, cy, rx, ry, ph=0.):
    """A shaped inlaid panel: black bed, wire, beads, white fillet. -> (svg, field polygon)."""
    if shape == "oval":
        return st_medallion(cx, cy, rx, ry)
    P = lambda g, n=120: st_poly_d(st_shape_pts(shape, cx, cy, rx, ry, g, n, ph))
    o = [f'<path d="{P(7)}" fill="#000" stroke="none"/>', st_wire(P(5.5)), st_beads(P(1.5, 180), 3.5, 1.),
         f'<path d="{P(-.5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_shape_pts(shape, cx, cy, rx, ry, -1.2, 120, ph)


def st_dedication(cx, foot, hh):
    """The small Somaster dedication cartouche at a front vignette's foot (about 30 px)."""
    return st_arms(cx, foot - hh / 2, hh * .5, hh * .5, mantling=True)


def st_device(w, h, seed, hk):
    """A marginal device (a 40-60 px roundel): the subject in a beaded roundel, the corners of
    the block cut away to the matte with a leaf in each spandrel."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    cx, cy = w / 2, h / 2
    r = min(w, h) / 2 - (4.5 if min(w, h) < 64 else 7.5)
    cv = StCanvas()
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * (w / 2 - 3), cy + sy * (h / 2 - 3)
            a = _m.atan2(cy - py, cx - px)
            if _m.hypot(px - cx, py - cy) > r + 9:
                L = max(4., (_m.hypot(px - cx, py - cy) - r - 6) * 1.1)
                _leaf(cv, px, py, a, L, L * .42, .5 * sx * sy, .35, _rnd.Random(seed + sx * 3 + sy))
    o.append(cv.svg())
    o.append(st_wire(st_rect_d(1.5, 1.5, w - 3, h - 3)))
    o.append(f'<path d="{st_ell_d(cx, cy, r + 3.5, r + 3.5)}" fill="#000"/>'
             f'<path d="{st_ell_d(cx, cy, r + 2, r + 2)}" fill="none" stroke="#fff" stroke-width="1" stroke-dasharray="1 1.5"/>'
             f'<path d="{st_ell_d(cx, cy, r - .2, r - .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    fld = _C._ell_pts(cx, cy, r - .9, r - .9, 72)[:-1]
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2d{w}x{h}v", fld, hk["field"](fld, "device") + st_rim(fld, 2.5)))
    return "".join(o)


def st_clip_poly(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{_C._d(list(poly), True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_clip_rect(cid, x, y, w, h, body):
    return f'<clipPath id="{cid}"><path d="{st_rect_d(x, y, w, h)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_sun(cv, cx, cy, r, rays=16):
    disc = _C._ell_pts(cx, cy, r, r, 28)[:-1]
    for k in range(rays):
        a = k * _TAU / rays
        ln = r * (1.9 if k % 2 == 0 else 1.5)
        w = _PI / rays * .7
        tri = [(cx + r * .9 * _m.cos(a - w), cy + r * .9 * _m.sin(a - w)), (cx + ln * _m.cos(a), cy + ln * _m.sin(a)),
               (cx + r * .9 * _m.cos(a + w), cy + r * .9 * _m.sin(a + w))]
        cv.obj([tri], .5)
        cv.hair([(cx + r * _m.cos(a + w * .4), cy + r * _m.sin(a + w * .4)), (cx + ln * .9 * _m.cos(a), cy + ln * .9 * _m.sin(a))])
    cv.obj([disc], .5)
    cv.hair([p for p in _C.hatch_poly(disc, 45, 1.5) if p[0][0] + p[0][1] > cx + cy - r * .3])


def _stick(cv, x0, y0, x1, y1, w):
    a = _m.atan2(y1 - y0, x1 - x0)
    n = 16
    pts = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    W = [w * (1 - .55 * _sm(.6, .95, i / n)) for i in range(n + 1)]
    R = _C._Rib(pts, W, W)
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(.6, .02, .93))
    tx, ty = x1 + _m.cos(a) * w * .5, y1 + _m.sin(a) * w * .5
    cv.obj([_C._ell_pts(tx, ty, w * 1.1, w * .8, 12)[:-1]], .5)


def st_crossed_sticks(cv, cx, cy, L, w=1.3, ang=0.):
    """Parker's crossed drumsticks, bead tips up."""
    for sd in (-1, 1):
        a = ang - _PI / 2 + sd * .62
        dx, dy = _m.cos(a) * L / 2, _m.sin(a) * L / 2
        _stick(cv, cx - dx, cy - dy, cx + dx, cy + dy, w)


_FLEUR = [(0, -1), (.13, -.72), (.16, -.42), (.1, -.15), (.24, -.2), (.42, -.42), (.62, -.48), (.78, -.38),
          (.8, -.18), (.68, -.02), (.54, .04), (.62, -.12), (.6, -.26), (.48, -.26), (.34, -.08), (.22, .1),
          (.36, .1), (.36, .22), (.14, .22), (.2, .5), (.38, .72), (.2, .7), (.08, .54), (0, .62)]


def _fleur(cx, cy, s):
    """A fleur-de-lis about 2s tall, as one closed polygon."""
    right = [(cx + x * s, cy + y * s) for x, y in _FLEUR]
    left = [(cx - x * s, cy + y * s) for x, y in _FLEUR[::-1]][1:-1]
    return right + left


def _heater(cx, top, w, h, n=24):
    """A heater shield outline: straight chief, sides curving to the point."""
    pts = [(cx - w / 2, top), (cx + w / 2, top)]
    for i in range(n + 1):
        t = i / n
        pts.append((cx + w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    for i in range(n, -1, -1):
        t = i / n
        pts.append((cx - w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    return pts


def st_arms(cx, cy, rx, ry, mantling=True):
    """Parker's arms, Somaster: Or, a castle between five fleurs-de-lis sable. A heater shield,
    Or as an even field of fine dots (Petra Sancta), the charges sable cut in solid black with
    white mortar lines; acanthus mantling springs from behind the shield's top corners."""
    o = []
    sh = min(ry * 2, rx * 2.3)
    sw = sh * .84
    top = cy - sh / 2
    shield = _heater(cx, top, sw, sh)
    if mantling:
        cv = _C.Canvas()
        rng = _rnd.Random(5)
        for sd in (-1, 1):
            for k, (a, L) in enumerate(((-.3, .9), (.25, .8), (.85, .7), (1.35, .55))):
                ang = (_PI / 2 - (a + 1.2)) if sd > 0 else (_PI / 2 + (a + 1.2))
                x0, y0 = cx + sd * sw * .42, top + sh * .1 + k * sh * .12
                _leaf(cv, x0, y0, -ang + _PI if False else (a * sd + (0 if sd > 0 else _PI)), sh * L * .55, sh * L * .12,
                      sd * .8, -sd * 2., rng, 3)
        o.append(cv.svg())
    d = st_poly_d(shield)
    o.append(f'<path d="{d}" fill="#000" stroke="#000" stroke-width="3"/>')
    o.append(f'<path d="{d}" fill="#fff" stroke="#fff" stroke-width="1"/>')
    o.append(f'<path d="{d}" fill="url(#s2o)" stroke="#000" stroke-width=".5"/>')
    blk = []
    s = sh * .085
    for fx, fy in ((-.26, .14), (0, .14), (.26, .14), (-.36, .55), (.36, .55)):
        blk.append(_fleur(cx + fx * sw, top + fy * sh + s * .1, s))
    # the castle: two towers and a curtain wall, crenellated, an arched gate with a portcullis
    cw, chh = sw * .46, sh * .3
    bx0, by1 = cx - cw / 2, top + sh * .72
    tw, th = cw * .24, chh * 1.3
    mer = tw / 5
    for tx in (bx0, bx0 + cw - tw):
        ty = by1 - th
        pts = [(tx, by1), (tx, ty)]
        for k in range(5):
            x = tx + k * mer
            if k % 2 == 0:
                pts += [(x, ty - mer), (x + mer, ty - mer)]
            else:
                pts += [(x, ty), (x + mer, ty)]
        pts += [(tx + tw, ty), (tx + tw, by1)]
        blk.append(pts)
    wy = by1 - chh * .72
    wx0, wx1 = bx0 + tw - .2, bx0 + cw - tw + .2
    nm = max(3, int((wx1 - wx0) / mer))
    mm = (wx1 - wx0) / nm
    pts = [(wx0, by1), (wx0, wy)]
    for k in range(nm):
        x = wx0 + k * mm
        if k % 2 == 1:
            pts += [(x, wy - mer * .9), (x + mm, wy - mer * .9)]
        else:
            pts += [(x, wy), (x + mm, wy)]
    pts += [(wx1, wy), (wx1, by1)]
    blk.append(pts)
    o.append(f'<path d="{"".join(st_poly_d(p) for p in blk)}" fill="#000" stroke="none"/>')
    # white work in the sable: mortar courses, tower windows, the gate and its portcullis
    lines = []
    for k in range(1, 6):
        y = by1 - k * chh * .2
        lines.append([(bx0 + 1, y), (bx0 + tw - 1, y)])
        lines.append([(bx0 + cw - tw + 1, y), (bx0 + cw - 1, y)])
        if y > wy + 1:
            lines.append([(wx0 + 1, y), (wx1 - 1, y)])
    gw, gh = cw * .2, chh * .55
    gate = [(cx - gw / 2, by1)] + [(cx - gw / 2 * _m.cos(t * _PI / 12), by1 - gh * .6 - gw / 2 * _m.sin(t * _PI / 12)) for t in range(13)] + [(cx + gw / 2, by1)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in lines)}" stroke="#fff" stroke-width="1" fill="none"/>')
    o.append(f'<path d="{st_poly_d(gate)}" fill="#fff" stroke="none"/>')
    pc = [[(cx + gw * (k / 4 - .5) * .8, by1 - gh * .95), (cx + gw * (k / 4 - .5) * .8, by1)] for k in range(5)]
    pc += [[(cx - gw * .45, by1 - gh * .3 * k), (cx + gw * .45, by1 - gh * .3 * k)] for k in (1, 2)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in pc)}" stroke="#000" stroke-width=".5" fill="none"/>')
    for tx in (bx0 + tw / 2, bx0 + cw - tw / 2):
        o.append(f'<path d="M{_C._n(tx)},{_C._n(by1 - th * .75)}v{_C._n(th * .22)}" stroke="#fff" stroke-width="1"/>')
    return "".join(o)


def st_sky(x0, y0, x1, y1, seed, avoid=None, clouds=None, top_dark=.32, pitch=(2., 2., 3., 3.)):
    """A Dore sky, not a ruled one: long lines that swell over billowing cloud banks (lit tops
    left white, undersides shaded), dark and cross-cut at the zenith, opening toward the horizon.
    Returns (hair polylines, line polylines). avoid(x, y) breaks the lines (moon, towers)."""
    rng = _rnd.Random(seed)
    W, H = x1 - x0, y1 - y0
    if clouds is None:
        clouds = []
        n = max(2, int(W / 80) + 1)
        for i in range(n):
            cx = x0 + W * (i + rng.uniform(.2, .8)) / n
            cy = y0 + H * rng.uniform(.3, .75)
            clouds.append((cx, cy, W / n * rng.uniform(.45, .7), H * rng.uniform(.09, .16)))
    hair, heavy = [], []

    def cloud_at(x, y):
        for cx, cy, rx, ry in clouds:
            dx = (x - cx) / rx
            if abs(dx) < 1:
                top = cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))
                bot = cy + ry * .35 * (1 - dx * dx) ** .5
                if top <= y <= bot:
                    return (y - top) / max(.5, bot - top)
        return None
    y = y0 + .75
    while y < y1:
        f = (y - y0) / max(1., H)
        p = pitch[min(len(pitch) - 1, int(f * len(pitch)))]
        run = []
        x = x0
        while x <= x1 + 3:
            yy = y
            for ccx, ccy, crx, cry in clouds:
                dx = (x - ccx) / (crx * 1.5)
                if abs(dx) < 1 and y > ccy:
                    yy += cry * .22 * (1 - dx * dx) ** 2 * max(0., 1 - (y - ccy) / (cry * 3))
            cf = cloud_at(x, yy)
            lit = cf is not None and cf < .55
            if lit or (avoid and avoid(x, yy)):
                if len(run) > 1:
                    hair.append(run)
                run = []
            else:
                run.append((x, yy))
            x += 3.
        if len(run) > 1:
            hair.append(run)
        y += p
    # cloud edges: billowed tops, shaded bellies
    for cx, cy, rx, ry in clouds:
        top = []
        for i in range(41):
            dx = -1 + 2 * i / 40
            top.append((cx + dx * rx, cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))))
        hair.append(top)
        for k in range(1, 4):
            arc = []
            for i in range(31):
                dx = -.85 + 1.7 * i / 30
                arc.append((cx + dx * rx * (1 - .12 * k), cy - ry * (1 - dx * dx) ** .5 * (.55 - .14 * k) + ry * .1 * k))
            hair.append(arc)
    # the zenith: cross-cut so the sky deepens upward
    zt = y0 + H * top_dark
    for ln in _C.hatch_poly([(x0, y0), (x1, y0), (x1, zt), (x0, zt)], 30, 3.):
        if avoid:
            a_, b_ = ln
            seg, cur = [], []
            for i in range(int(_m.dist(a_, b_) / 2) + 2):
                t = i / max(1, int(_m.dist(a_, b_) / 2) + 1)
                q = (a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t)
                if avoid(*q):
                    if len(cur) > 1:
                        hair.append(cur)
                    cur = []
                else:
                    cur.append(q)
            if len(cur) > 1:
                hair.append(cur)
        else:
            hair.append(ln)
    return hair, heavy


def st_rim(fld, depth=12., uid="r"):
    """Light emerging from dark: concentric cuts round the inside of a medallion field, close and
    heavy at the rim, thinning inward, so the subject glows out of a dark surround."""
    cx = sum(p[0] for p in fld) / len(fld)
    cy = sum(p[1] for p in fld) / len(fld)
    size = min(max(abs(p[0] - cx) for p in fld), max(abs(p[1] - cy) for p in fld))
    o1, o5 = [], []
    d = .75
    while d < depth:
        k = 1 - d / size
        ring = [(cx + (p[0] - cx) * k, cy + (p[1] - cy) * k) for p in fld]
        (o1 if d < depth * .35 else o5).append(_C._d(ring + [ring[0]], tol=.2))
        d += 2. if d < depth * .35 else 1.5 + (d / depth) * 1.5
    return (f'<path d="{"".join(o1)}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="{"".join(o5)}" fill="none" stroke="#000" stroke-width=".5"/>')


# ---------------------------------------------------------------------------------------------
# Easter eggs cut into a scroll's eye: egg(cv, x, y, r) draws inside a disc of radius r
# ---------------------------------------------------------------------------------------------

def _egg_disc(cv, x, y, r):
    cv.obj([_C._ell_pts(x, y, r, r, 28)[:-1]], 1.)
    cv.hair(_C._ell_pts(x, y, r - 1.2, r - 1.2, 28))


def egg_sticks(cv, x, y, r):
    """Parker's crossed drumsticks."""
    _egg_disc(cv, x, y, r)
    st_crossed_sticks(cv, x, y + r * .05, r * 1.45, max(.6, r * .09))


def egg_P(cv, x, y, r):
    """A "P" monogram, cut as a stem and a bowl with a flourish."""
    _egg_disc(cv, x, y, r)
    h = r * 1.1
    cv.line([(x - h * .22, y + h * .5), (x - h * .22, y - h * .5)])
    bowl = [(x - h * .22, y - h * .5)] + [(x - h * .05 + h * .3 * _m.sin(t * _PI / 10), y - h * .25 - h * .25 * _m.cos(t * _PI / 10)) for t in range(11)] + [(x - h * .22, y)]
    cv.line(bowl)
    cv.hair([(x - h * .45, y + h * .5), (x + h * .05, y + h * .5)])
    cv.hair([(x - h * .22, y + h * .5), (x - h * .5, y + h * .62), (x - h * .62, y + h * .45)])


def egg_note(cv, x, y, r):
    """A swing eighth-note pair (jazz)."""
    _egg_disc(cv, x, y, r)
    s = r * .32
    for dx in (-1, 1):
        hx, hy = x + dx * s * 1.1 - s * .4, y + s * 1.1
        cv.obj([_C._ell_pts(hx, hy, s * .55, s * .38, 12)[:-1]], .5)
        cv.line(_C._ell_pts(hx, hy, s * .3, s * .15, 8))
        cv.line([(hx + s * .5, hy), (hx + s * .5, y - s * 1.5)])
    cv.heavy([(x - s * .6 + s * .1, y - s * 1.5), (x + s * 1.6 + s * .1, y - s * 1.5)])


def egg_cymbal(cv, x, y, r):
    """A tiny ride cymbal on its stand, lathe rings and a bell."""
    _egg_disc(cv, x, y, r)
    cy = y - r * .15
    cv.obj([_C._ell_pts(x, cy, r * .8, r * .22, 24)[:-1]], .5)
    for k in (1, 2, 3):
        cv.hair(_C._ell_pts(x, cy, r * .8 * k / 4, r * .22 * k / 4, 20))
    cv.obj([_C._ell_pts(x, cy - r * .08, r * .16, r * .1, 10)[:-1]], .5)
    cv.line([(x, cy + r * .2), (x, y + r * .7)])
    cv.hair([(x, y + r * .55), (x - r * .35, y + r * .78)])
    cv.hair([(x, y + r * .55), (x + r * .35, y + r * .78)])


def egg_hood(cv, x, y, r):
    """Mt. Hood: the snow cone, its glaciers and a timber line."""
    _egg_disc(cv, x, y, r)
    pk = [(x - r * .82, y + r * .45), (x - r * .1, y - r * .55), (x + r * .05, y - r * .6), (x + r * .82, y + r * .45)]
    cv.obj([pk], .5)
    cv.hair([(x - r * .02, y - r * .5), (x - r * .25, y + r * .05)])
    cv.hair([(x + r * .05, y - r * .5), (x + r * .3, y + r * .1)])
    cv.hair(_C.hatch_poly([(x + r * .05, y - r * .58), (x + r * .82, y + r * .45), (x + r * .25, y + r * .45)], 60, 1.5))
    for k in range(7):
        tx = x - r * .7 + k * r * .23
        cv.line([(tx, y + r * .62), (tx, y + r * .38)])


def egg_pinwheel(cv, x, y, r):
    """The Blazers pinwheel: five pairs of swept bars turning about a hub."""
    _egg_disc(cv, x, y, r)
    for k in range(5):
        a = k * _TAU / 5 - _PI / 2
        for off in (-.12, .12):
            p0 = (x + r * .18 * _m.cos(a + off), y + r * .18 * _m.sin(a + off))
            p1 = (x + r * .78 * _m.cos(a + off + .35), y + r * .78 * _m.sin(a + off + .35))
            cv.line([p0, p1])


def egg_heron(cv, x, y, r):
    """A Sauvie Island heron's head and S neck, crest plume and dagger bill."""
    _egg_disc(cv, x, y, r)
    neck = [(x - r * .1, y + r * .8), (x - r * .35, y + r * .3), (x - r * .05, y - r * .05), (x - r * .25, y - r * .4)]
    cv.line(neck)
    cv.line([(x - r * .05 + r * .15, y + r * .8), (x - r * .2 + r * .12, y + r * .3), (x + r * .12, y - r * .02), (x - r * .1, y - r * .35)])
    hd = _C._ell_pts(x - r * .2, y - r * .45, r * .16, r * .11, 12)[:-1]
    cv.obj([hd], .5)
    cv.line([(x - r * .05, y - r * .48), (x + r * .65, y - r * .38)])
    cv.hair([(x - r * .32, y - r * .5), (x - r * .7, y - r * .55)])


def egg_dog(cv, x, y, r):
    """Parker's dog, head on its paws, curled asleep in the eye of the scroll."""
    _egg_disc(cv, x, y, r)
    body = _C._ell_pts(x + r * .05, y + r * .15, r * .72, r * .42, 24)[:-1]
    cv.obj([body], .5)
    cv.hair(_C._fill_lines(_C._Rib([(x - r * .6, y + r * .15), (x + r * .7, y + r * .15)], [r * .38, r * .38], [r * .38, r * .38]), -.3, -.95, 1.5, .1, .9, 2))
    head = _C._ell_pts(x - r * .38, y - r * .05, r * .26, r * .2, 16)[:-1]
    cv.obj([head], .5)
    cv.obj([[(x - r * .48, y - r * .2), (x - r * .3, y - r * .45), (x - r * .22, y - r * .16)]], .5)
    cv.line(_C._ell_pts(x - r * .6, y - r * .02, .5, .5, 4))
    cv.hair([(x - r * .45, y - r * .06), (x - r * .36, y - r * .04)])
    cv.hair([(x + r * .7, y + r * .1), (x + r * .55, y + r * .45), (x + r * .1, y + r * .52)])


def egg_kranok(cv, x, y, r):
    """A Thai kranok flame: three flame tongues curling up out of a lotus calyx."""
    _egg_disc(cv, x, y, r)
    for sd, L, a in ((0, 1., -_PI / 2), (-1, .7, -_PI / 2 - .55), (1, .7, -_PI / 2 + .55)):
        bx = x + sd * r * .12
        rib = _C._euler(bx, y + r * .5, a, r * L, lambda u, s_=sd or 1: s_ * 2.2 * _sm(.5, 1, u) / (r * L), 12)
        W = [r * .16 * (1 - i / 12) ** .7 + .3 for i in range(13)]
        R = _C._Rib(rib, W, W)
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.4, .05, .85))
    cv.obj([_C._ell_pts(x, y + r * .55, r * .3, r * .14, 14)[:-1]], .5)


def egg_panel(cv, x, y, r):
    """A solar panel on its rack: a grid of cells, one ray of sun."""
    _egg_disc(cv, x, y, r)
    q = [(x - r * .7, y + r * .2), (x + r * .45, y + r * .2), (x + r * .7, y - r * .35), (x - r * .45, y - r * .35)]
    cv.obj([q], .5)
    for k in range(1, 4):
        t = k / 4
        cv.hair([(q[0][0] + (q[1][0] - q[0][0]) * t, q[0][1]), (q[3][0] + (q[2][0] - q[3][0]) * t, q[3][1])])
    cv.hair([((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2), ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)])
    cv.line([(x - r * .1, y + r * .2), (x - r * .1, y + r * .65)])
    cv.line([(x - r * .4, y + r * .65), (x + r * .25, y + r * .65)])


# ---------------------------------------------------------------------------------------------
# lettering: engraved Roman capitals as strokes (no <text>)
# ---------------------------------------------------------------------------------------------

_OV = [(.5 + .5 * _m.cos(_TAU * i / 20 - _PI / 2), .5 + .5 * _m.sin(_TAU * i / 20 - _PI / 2)) for i in range(21)]
_GL = {
    "A": ([[(0, 1), (.5, 0), (1, 1)], [(.22, .62), (.78, .62)]], .85),
    "B": ([[(0, 0), (0, 1), (.7, 1), (.9, .85), (.9, .65), (.7, .5), (0, .5)], [(0, 0), (.62, 0), (.82, .12), (.82, .38), (.62, .5)]], .75),
    "C": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .85)]], .8),
    "D": ([[(0, 0), (0, 1), (.55, 1), (.92, .72), (.92, .28), (.55, 0), (0, 0)]], .8),
    "E": ([[(.85, 0), (0, 0), (0, 1), (.85, 1)], [(0, .5), (.65, .5)]], .7),
    "F": ([[(.85, 0), (0, 0), (0, 1)], [(0, .5), (.65, .5)]], .65),
    "G": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .8), (.95, .55), (.55, .55)]], .82),
    "H": ([[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .5), (1, .5)]], .8),
    "I": ([[(.5, 0), (.5, 1)]], .3),
    "J": ([[(.8, 0), (.8, .78), (.6, 1), (.2, 1), (0, .8)]], .6),
    "K": ([[(0, 0), (0, 1)], [(.9, 0), (0, .62)], [(.3, .42), (.95, 1)]], .78),
    "L": ([[(0, 0), (0, 1), (.85, 1)]], .65),
    "M": ([[(0, 1), (0, 0), (.5, .65), (1, 0), (1, 1)]], 1.),
    "N": ([[(0, 1), (0, 0), (1, 1), (1, 0)]], .82),
    "O": ([_OV], .9),
    "P": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)]], .72),
    "Q": ([_OV, [(.6, .72), (1, 1.06)]], .9),
    "R": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)], [(.45, .5), (.95, 1)]], .76),
    "S": ([[(.9, .12), (.7, 0), (.25, 0), (.05, .15), (.05, .35), (.25, .47), (.75, .53), (.95, .66), (.95, .85), (.75, 1), (.25, 1), (.05, .88)]], .7),
    "T": ([[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]], .78),
    "U": ([[(0, 0), (0, .75), (.25, 1), (.75, 1), (1, .75), (1, 0)]], .8),
    "V": ([[(0, 0), (.5, 1), (1, 0)]], .82),
    "W": ([[(0, 0), (.25, 1), (.5, .35), (.75, 1), (1, 0)]], 1.1),
    "X": ([[(0, 0), (1, 1)], [(1, 0), (0, 1)]], .8),
    "Y": ([[(0, 0), (.5, .5), (1, 0)], [(.5, .5), (.5, 1)]], .8),
    "Z": ([[(0, 0), (1, 0), (0, 1), (1, 1)]], .76),
    "0": ([[(.5 + .45 * _m.cos(_TAU * i / 20), .5 + .5 * _m.sin(_TAU * i / 20)) for i in range(21)]], .65),
    "1": ([[(.25, .2), (.55, 0), (.55, 1)], [(.25, 1), (.85, 1)]], .55),
    "2": ([[(.05, .2), (.25, 0), (.75, 0), (.95, .2), (.95, .4), (0, 1), (1, 1)]], .65),
    "3": ([[(.05, .1), (.3, 0), (.75, 0), (.95, .2), (.9, .4), (.5, .5), (.9, .6), (.95, .8), (.75, 1), (.3, 1), (.05, .9)]], .65),
    "4": ([[(.75, 1), (.75, 0), (0, .7), (1, .7)]], .65),
    "5": ([[(.9, 0), (.15, 0), (.05, .45), (.6, .4), (.95, .6), (.95, .8), (.7, 1), (.25, 1), (.05, .9)]], .65),
    "6": ([[(.85, .05), (.5, 0), (.15, .2), (.05, .6), (.15, .9), (.5, 1), (.85, .9), (.95, .7), (.8, .5), (.45, .45), (.1, .6)]], .65),
    "7": ([[(0, 0), (1, 0), (.35, 1)]], .62),
    "8": ([[(.5, .5), (.15, .38), (.1, .15), (.3, 0), (.7, 0), (.9, .15), (.85, .38), (.5, .5), (.1, .65), (.05, .85), (.3, 1), (.7, 1), (.95, .85), (.9, .65), (.5, .5)]], .65),
    "9": ([[(.9, .4), (.55, .55), (.15, .45), (.05, .25), (.2, .05), (.55, 0), (.9, .2), (.95, .5), (.8, .85), (.45, 1), (.15, .95)]], .65),
    "-": ([[(.1, .55), (.9, .55)]], .5),
    "·": ([[(.45, .5), (.55, .5)]], .35),
    ".": ([[(.45, .95), (.55, .95)]], .3),
    ",": ([[(.5, .9), (.35, 1.15)]], .3),
    ":": ([[(.5, .3), (.5, .32)], [(.5, .9), (.5, .92)]], .3),
    "'": ([[(.5, 0), (.4, .25)]], .25),
    "/": ([[(1, 0), (0, 1)]], .55),
    "&": ([[(1, 1), (.2, .35), (.25, .08), (.5, 0), (.7, .1), (.7, .3), (.1, .7), (.15, .95), (.5, 1), (.85, .7)]], .8),
    "°": ([[(.3 + .2 * _m.cos(_TAU * i / 10), .15 + .15 * _m.sin(_TAU * i / 10)) for i in range(11)]], .45),
    "%": ([[(1, 0), (0, 1)], [(.2 + .15 * _m.cos(_TAU * i / 10), .18 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)],
           [(.8 + .15 * _m.cos(_TAU * i / 10), .82 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)]], .75),
    " ": ([], .45),
}


def st_text_w(text, h, track=.32):
    t = [ch if ch in _GL else " " for ch in text.upper()]
    return sum(_GL[ch][1] * h * .78 for ch in t) + track * h * max(0, len(t) - 1)


def st_letter(text, h, centre=None, cx=0., cy=0., track=.32, sw=None, fit=None):
    """Monoline engraved capitals h tall, centred on (cx, cy) or along the polyline `centre`.
    fit shrinks the lettering to that width. -> svg path."""
    t = [ch if ch in _GL else " " for ch in text.upper()]
    if fit:
        tw = st_text_w(text, h, track)
        if tw > fit:
            h *= fit / tw
    tw = st_text_w(text, h, track)
    if centre:
        acc = [0.]
        for i in range(1, len(centre)):
            acc.append(acc[-1] + _m.dist(centre[i], centre[i - 1]))
        tot = acc[-1]

        def at(sv):
            sv = max(0., min(tot, sv))
            for i in range(1, len(acc)):
                if acc[i] >= sv:
                    f = (sv - acc[i - 1]) / max(1e-6, acc[i] - acc[i - 1])
                    p0, p1 = centre[i - 1], centre[i]
                    return p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, _m.atan2(p1[1] - p0[1], p1[0] - p0[0])
            return centre[-1][0], centre[-1][1], 0.
        pos = (tot - tw) / 2
    else:
        pos = -tw / 2
    d = []
    for ch in t:
        strokes, wf = _GL[ch]
        gw = wf * h * .78
        if centre:
            mx, my, a = at(pos + gw / 2)
        else:
            mx, my, a = cx + pos + gw / 2, cy, 0.
        ca, sa = _m.cos(a), _m.sin(a)
        for st in strokes:
            pts = []
            for gx, gy in st:
                lx, ly = (gx - .5) * gw, (gy - .5) * h
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            d.append(_C._d(pts, tol=.05))
        pos += gw + track * h
    w = sw or (1. if h >= 7 else .5)
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width="{_C._n(w)}"/>'


def st_tablet_text(tx, ty, tw, th, lines):
    """Lines of lettering in a tablet, over a dotted Or ground cut back behind each line."""
    o = [f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>']
    n = len(lines)
    lh = min(th / (n * 1.6 + .4), 11.)
    for i, ln in enumerate(lines):
        cy = ty + th * (i + .5) / n
        w = min(tw - 8, st_text_w(ln, lh) + lh * 1.4)
        o.append(f'<path d="{st_rect_d(tx + (tw - w) / 2, cy - lh * .85, w, lh * 1.7)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
        o.append(st_letter(ln, lh, cx=tx + tw / 2, cy=cy, fit=tw - 12))
    return "".join(o)


def st_doc(w, h, body):
    return _C.svg_doc(w, h, _ST_DEFS + body)
# ==== END STUDIO FRAME ==========================================================================
# ==== STUDIO LAYOUTS ============================================================================


def _in_ell(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1


def st_border(w, h, inset=3.):
    """The plate's own gold-line border and an inner row of beads, all four edges."""
    return (st_wire(st_rect_d(inset, inset, w - 2 * inset, h - 2 * inset))
            + st_beads(st_rect_d(inset + 4.5, inset + 4.5, w - 2 * inset - 9, h - 2 * inset - 9), 3.5, 1.))


def _st_clip_runs(pl, mask, x0, y0, W, H, out, step=1.5):
    """_clip_runs at a 1.5 px test step (lines are cut cleanly enough; half the work)."""
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L = _m.hypot(dx, dy)
        if L > step:
            k = int(L / step)
            for j in range(1, k + 1):
                t = j / (k + 1)
                pts.append((px + dx * t, py + dy * t))
        pts.append(q)
        px, py = q
    run = []
    for (x, y) in pts:
        xi, yi = int(x - x0), int(y - y0)
        if 0 <= xi < W and 0 <= yi < H and mask[yi][xi]:
            if len(run) > 1:
                out.append(run)
            run = []
        else:
            run.append((x, y))
    if len(run) > 1:
        out.append(run)


class StCanvas(_C.Canvas):
    """The house Canvas, emitting with a slightly coarser simplification for the fine cuts so a
    packed field of scroll stays inside the byte budget (the eye cannot see 0.15 px)."""

    def svg(self, tol_fill=.95, tol_hair=.65, tol_line=.55):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for wd, lines in strokes.items():
                for pl in lines:
                    _st_clip_runs(pl, mask, x0, y0, W, H, out[wd])
            if ow:
                for poly in polys:
                    _st_clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                _C._fill_mask(poly, mask, x0, y0, W, H)
        res = []
        pen = _C._Pen()
        for polys, _, _ in self.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="#fff" stroke="none"/>')
        for wd in (.5, 1., 1.5):
            if out[wd]:
                pen = _C._Pen()
                for pl in out[wd]:
                    if len(pl) > 2 or _m.dist(pl[0], pl[-1]) > .6:
                        pen.add(pl, False, tol_hair if wd < 1 else tol_line)
                res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_C._n(wd * 4)}"/>')
        return "".join(res)


def _scroll_layer(field, uid, x, y, w, h, egg=None, egg_gen=2):
    cv = StCanvas()
    field.draw(cv, egg, egg_gen)
    return st_clip_rect(uid, x, y, w, h, cv.svg())


def st_band(w, h, seed, hk):
    """h < 110: a carved band. An inlaid medallion holds the subject; from it a stem runs to
    either edge, the fine scroll branching off it to fill the band."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2 + hk.get("dx", 0.), h / 2
    ry = max(4., h / 2 - 8.5)
    rx = min(w * .2, max(ry * 1.5, ry * hk.get("aspect", 1.7)))
    if h < 40:
        ins = 5.
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 2 < y < fy1 + 2 and not _in_ell(x, y, cx, cy, rx + 12, ry + 12)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(3.5 if h < 40 else 4.5, gh * .12), rmax=max(4.6, gh * .32), seed=seed, slack=.9)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        L = (w / 2 - rx - 14) * 1.05
        x0 = cx + sd * (rx + 9)
        a = 0. if sd > 0 else _PI
        pts = []
        n = int(L / 2)
        for i in range(n + 1):
            u = i / n
            pts.append((x0 + sd * L * u, cy + gh * .18 * _m.sin(u * _TAU * (L / (gh * 2.2)) + (0 if sd > 0 else 1.3))))
        F.stem(pts, 1.6, 1.0, leaves=False)
    F.grow(8)
    F.fill(fx0 - 4, fy0 - 2, fx1 - fx0 + 8, fy1 - fy0 + 4, 3., hk.get("max_items", 160))
    o.append(_scroll_layer(F, f"s2b{w}x{h}", 0, 0, w, h, hk.get("egg"), 1))
    o.append(st_border(w, h, 1.5 if h < 40 else 3.))
    m, fld = st_medallion(cx, cy, rx, ry)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2b{w}x{h}v", fld, hk["field"](fld, "band") + st_rim(fld, hk.get("rim", 5.))))
    return "".join(o)


def st_medium(w, h, seed, hk):
    """110-260: the medallion between two panels of fine scroll, each grown from a stem that
    sweeps out of the medallion's foot; gold-line border and beading round the plate."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2, h / 2
    shape = hk.get("shape", "oval")
    ded = 15. if hk.get("dedication") else 0.
    ry = h / 2 - ins - 6
    rx = min(w * hk.get("cw", .21), ry * hk.get("aspect", 1.45))
    if shape == "roundel":
        rx = ry
    if shape == "arch":
        rx = min(rx, ry * 1.1)
    ph = (seed % 97) * .07
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 3 < y < fy1 + 3 and not st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph) and not (ded and abs(x - cx) < 34 and y > h - ins - 2 * ded - 6)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(6., gh * .055), rmax=min(26., gh * .2), seed=seed, slack=.88)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        a0 = _PI / 2 + sd * .25 * _PI
        x0, y0 = cx + (rx + 10) * _m.cos(_PI / 2 - sd * .9), cy + (ry + 10) * _m.sin(_PI / 2 - sd * .9)
        head = 0. if sd > 0 else _PI
        L = (w / 2 - rx - 20)
        k = -sd * .9 / L
        F.stem(st_sweep(x0, y0, head + sd * .35, L * 1.05, k * 1.5, -k * 1.2), 2., 1.1)
        x1, y1 = cx + (rx + 10) * _m.cos(-_PI / 2 + sd * .9), cy + (ry + 10) * _m.sin(-_PI / 2 + sd * .9)
        F.stem(st_sweep(x1, y1, head - sd * .35, L * .8, -k * 1.5, k), 1.8, 1.)
    F.grow(10)
    F.fill(fx0 - 4, fy0 - 3, fx1 - fx0 + 8, fy1 - fy0 + 6, 4., hk.get("max_items", 260))
    o.append(_scroll_layer(F, f"s2m{w}x{h}", 0, 0, w, h, hk.get("egg"), 2))
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2m{w}x{h}v", fld, hk["field"](fld, "medium") + st_rim(fld, hk.get("rim", 9.))))
    if ded:
        o.append(st_dedication(cx, h - 3, 2 * ded))
    if hk.get("crest"):
        o.append(hk["crest"](cx, cy - ry - 2, min(14., ins + 4), "medium"))
    return "".join(o)


def st_pedestal(x, y, w, h, seed, hk, uid):
    """The base: knurled cornice, a frieze panel (gold-line border, fine scroll from the centre
    out) round a sunk tablet, a second knurled bar, beading. -> svg"""
    o = []
    kb = 6.
    o.append(_C.knurled_bar(x, y, w, kb))
    py0, py1 = y + kb + 1, y + h - kb - 5
    ph = py1 - py0
    tw, th = min(w * .5, 300.), ph - 10
    tx, ty = x + (w - tw) / 2, py0 + 5
    o.append(st_matte(st_rect_d(x, py0, w, ph)))

    def inside(px, py):
        return x + 6 < px < x + w - 6 and py0 + 2 < py < py1 - 2 and not (tx - 8 < px < tx + tw + 8)
    F = ScrollField(inside, rmin=max(4.5, ph * .16), rmax=ph * .4, seed=seed + 11, slack=.9)
    for sd in (-1, 1):
        xs = tx - 6 if sd < 0 else tx + tw + 6
        L = (w - tw) / 2 - 14
        pts = [(xs + sd * L * i / 30, py0 + ph / 2 + ph * .15 * _m.sin(i / 30 * _TAU * (L / (ph * 2)))) for i in range(31)]
        F.stem(pts, 1.4, .9, leaves=False)
    F.grow(6)
    F.fill(x + 6, py0 + 2, w - 12, ph - 4, 3., 120)
    o.append(_scroll_layer(F, uid + "p", x, py0, w, ph))
    o.append(st_wire(st_rect_d(x + 2.5, py0 + 1.5, w - 5, ph - 3)))
    o.append(f'<path d="{st_rect_d(tx - 3, ty - 3, tw + 6, th + 6)}" fill="#000"/>')
    o.append(st_beads(st_rect_d(tx - 1.5, ty - 1.5, tw + 3, th + 3), 3.5, 1.))
    o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="#fff" stroke="none"/>')
    if hk.get("tablet"):
        o.append(hk["tablet"](tx, ty, tw, th))
    elif hk.get("tablet_lines"):
        o.append(st_tablet_text(tx, ty, tw, th, hk["tablet_lines"]))
    else:
        o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>')
    o.append(_C.knurled_bar(x + 4, py1, w - 8, kb))
    o.append(st_beads(f"M{_C._n(x + 3)},{_C._n(y + h - 2.5)}h{_C._n(w - 6)}", 3.5, 1.))
    return "".join(o)


def st_tall(w, h, seed, hk):
    """> 260: the full plate. The scene in a great inlaid medallion (an arched panel on a section
    front, like the binding) over a ribbon banner and the dedication cartouche with Parker's arms
    (placeholder); fine scroll grown from a stem rising either side of the arms packs the field;
    a pedestal; under it, when tall, a frieze of the same scroll."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    ped_h = min(max(h * .13, 40), 62.)
    fz = min(max(h * .09, 30), 50.) if (h >= 440 and hk.get("frieze", True)) else 0.
    py = h - ped_h - fz - ins * (1 if fz else .6)
    shape = hk.get("shape") or ("arch" if hk.get("arch") else "oval")
    arch = shape == "arch"
    rx = w * hk.get("cw", .3)
    top = ins + 12
    bot = py - (62 if py > 300 else 46)
    ry = (bot - top) / 2
    if shape == "roundel":
        rx = ry = min(rx * 1.25, ry)
        top = bot - 2 * ry
    cx, cy = w / 2, top + ry
    ph = (seed % 97) * .07
    ay = bot + 4
    ary = min(26., (py - ay) * .4)
    arx = ary * 1.25
    aby = py - ary - 8

    def inside(x, y):
        if not (ins - 4 < x < w - ins + 4 and ins - 3 < y < py - 3):
            return False
        if st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph):
            return False
        if abs(x - cx) < rx * 1.05 + 10 and bot - 4 < y < bot + 16:
            return False
        if _in_ell(x, y, cx, aby, arx + 10, ary + 9):
            return False
        return True
    F = ScrollField(inside, rmin=hk.get("rmin", 8.), rmax=min(hk.get("rmax", 30.), w * .058), seed=seed, slack=.88)
    for sd in (-1, 1):
        x0, y0 = cx + sd * (arx + 8), aby + ary * .3
        F.stem(st_sweep(x0, y0, (0. if sd > 0 else _PI) - sd * .25, (py - ins) * .55 + w * .1,
                        -sd * .004, -sd * .022), 3., 1.6)
        F.stem(st_sweep(cx + sd * (rx * .7), ins + 4, (0. if sd > 0 else _PI) + sd * .15, w * .3, sd * .004, sd * .02), 2.6, 1.4)
    F.grow(4)
    F.fill(ins - 4, ins - 3, w - 2 * ins + 8, py - ins, 6., hk.get("max_items", 340))
    uid = f"s2t{w}x{h}"
    o.append(_scroll_layer(F, uid, 0, 0, w, py, hk.get("egg"), 2))
    if fz:
        fy0 = py + ped_h + 2
        fh = h - ins - fy0

        def inside2(x, y):
            return ins - 4 < x < w - ins + 4 and fy0 < y < fy0 + fh and abs(x - w / 2) > fh * .7
        G = ScrollField(inside2, rmin=max(4.5, fh * .15), rmax=fh * .4, seed=seed + 5, slack=.9)
        for sd in (-1, 1):
            L = w / 2 - fh * .7 - 8
            G.stem([(w / 2 + sd * (fh * .7 + L * i / 40), fy0 + fh / 2 + fh * .17 * _m.sin(i / 40 * _TAU * (L / (fh * 2.1)))) for i in range(41)],
                   1.5, 1., leaves=False)
        G.grow(6)
        G.fill(ins - 4, fy0, w - 2 * ins + 8, fh, 4., 140)
        o.append(_scroll_layer(G, uid + "f", 0, fy0, w, fh, hk.get("egg2"), 1))
        cvp = _C.Canvas()
        _C.palmette(w / 2, fy0 + 1, fh * .8, False, seed, cv=cvp)
        o.append(cvp.svg())
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(uid + "v", fld, hk["field"](fld, "tall") + st_rim(fld, hk.get("rim", 14.))))
    if hk.get("crest"):
        o.append(hk["crest"](cx, top - 3, top - 4, "tall"))
    bh = min(16., (py - bot) * .4)
    bs, centre = _C.ribbon_banner(cx, bot + 2, rx * 2.5, bh, .035, seed)
    o.append(bs)
    if hk.get("banner"):
        o.append(hk["banner"](centre, bh))
    elif hk.get("motto"):
        o.append(st_letter(hk["motto"], bh * .55, centre=centre[4:-4], fit=_m.dist(centre[4], centre[-5]) * .92))
    if hk.get("dedication"):
        o.append(st_arms(cx, aby, arx, ary))
    else:
        # not a front: a small inlaid cartouche carries the page's own device instead of the arms
        em, efl = st_medallion(cx, aby, arx * .78, ary * .78)
        o.append(em)
        o.append(f'<path d="{st_poly_d(efl)}" fill="url(#s2o)" stroke="none"/>')
        if hk.get("egg"):
            ecv = StCanvas()
            hk["egg"](ecv, cx, aby, ary * .62)
            o.append(ecv.svg())
    o.append(st_pedestal(0, py, w, ped_h, seed, hk, uid))
    return "".join(o)


def st_plate(w, h, seed, hk):
    base = _C.Canvas
    _C.Canvas = StCanvas
    try:
        return _st_plate(w, h, seed, hk)
    finally:
        _C.Canvas = base


def _st_plate(w, h, seed, hk):
    if h <= 72 and w <= 110 and hk.get("device", True):
        body = st_device(w, h, seed, hk)
    elif h < 110:
        body = st_band(w, h, seed, hk)
    elif h <= 260:
        body = st_medium(w, h, seed, hk)
    else:
        body = st_tall(w, h, seed, hk)
    return st_doc(w, h, body)
# ==== END STUDIO LAYOUTS ========================================================================


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 3
    _MODE["m"] = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    hk = dict(field=lambda fld, mode: _hifi(fld, seed), egg=egg_sticks, shape="oval", aspect=1.9, cw=.25,
              rmin=9., rmax=30., banner=_waveform, tablet_lines=["STORIES · REVIEWS", "BUY · WAIT · SKIP"])
    return st_plate(w, h, seed, hk)
