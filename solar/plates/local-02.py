"""local-02: "New and opening around town" (Eater Portland / local news: new restaurants, bars,
a vegan bakery storefront, Pearl District openings).

Subject: opening night of a new Pearl District restaurant. A brick storefront with a striped,
scalloped awning, a hanging blade sign with crossed fork and knife, lit windows with pendant
lamps, an "OPEN" plaque and a grand-opening ribbon tied across the door, potted bay topiaries,
the old warehouses of the Pearl behind with a rooftop water tower, a dusk sky with the date's
moon. Short plates carry a lifted cloche with rising steam in the medallion.
Easter egg: Parker's dog sits on the sidewalk by the door, waiting for scraps (and a tiny "P"
monogram is cut into the door's transom).
"""
import sys
import math
import random
import datetime
import engraving_codex as C

PI = math.pi


# ----------------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------------

def R(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def solid(cv, poly, outline=0.):
    """A black mass: 1 px lines 0.8 px apart."""
    cv.obj([poly], outline)
    cv.line(C.hatch_poly(poly, 0, .8))


def ell(cx, cy, rx, ry, n=32, a0=0., a1=2 * PI):
    return C._ell_pts(cx, cy, rx, ry, n, a0, a1)


def closed(p):
    return p + [p[0]]


def moon_frac(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .5
    return (days / 29.530589) % 1.


def moon(cv, cx, cy, r, f):
    """Moon disc; the dark part ruled densely, lit part white."""
    disc = ell(cx, cy, r, r, 32)
    cv.obj([disc], .5)
    k = math.cos(2 * PI * f)
    side = -1 if f < .5 else 1          # dark limb side (waxing: dark on the left)
    n = 24
    limb = [(cx + side * r * math.sin(PI * i / n), cy - r * math.cos(PI * i / n)) for i in range(n + 1)]
    term = [(cx - side * k * r * math.sin(PI * i / n), cy + r * math.cos(PI * i / n)) for i in range(n + 1)]
    dark = limb + term
    if abs(C._area(dark)) > 2:
        cv.hair(C.hatch_poly(dark, 0, 1.5))
    cv.hair([closed(ell(cx + r * .25, cy - r * .2, r * .22, r * .16, 10)), closed(ell(cx - r * .2, cy + r * .3, r * .18, r * .12, 10))])


def star(cv, x, y, s):
    cv.obj([[(x, y - s), (x + s * .25, y - s * .25), (x + s, y), (x + s * .25, y + s * .25),
             (x, y + s), (x - s * .25, y + s * .25), (x - s, y), (x - s * .25, y - s * .25)]], .5)


# stroke letters on a 4 x 6 grid
_GLYPH = {
    "O": [[(2, 0), (3.4, .6), (4, 3), (3.4, 5.4), (2, 6), (.6, 5.4), (0, 3), (.6, .6), (2, 0)]],
    "P": [[(0, 6), (0, 0), (2.8, 0), (3.8, .8), (3.8, 2.2), (2.8, 3), (0, 3)]],
    "E": [[(3.6, 0), (0, 0), (0, 6), (3.6, 6)], [(0, 3), (2.8, 3)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "W": [[(0, 0), (1, 6), (2, 2.2), (3, 6), (4, 0)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "D": [[(0, 0), (0, 6), (2.2, 6), (3.6, 5), (4, 3), (3.6, 1), (2.2, 0), (0, 0)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "G": [[(3.8, 1), (2.6, 0), (1.2, .2), (.2, 1.6), (0, 3), (.2, 4.6), (1.2, 5.8), (2.8, 6), (4, 5.2), (4, 3.4), (2.4, 3.4)]],
    "R": [[(0, 6), (0, 0), (2.8, 0), (3.8, .8), (3.8, 2.2), (2.8, 3), (0, 3)], [(2, 3), (4, 6)]],
    "U": [[(0, 0), (0, 4.4), (.8, 5.7), (2, 6), (3.2, 5.7), (4, 4.4), (4, 0)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    " ": [],
}


def letters(txt, x, y, hgt, gap=1.6):
    s = hgt / 6.
    out = []
    for ch in txt:
        if ch == " ":
            x += 3 * s
            continue
        for pl in _GLYPH[ch]:
            out.append([(x + px * s, y + py * s) for px, py in pl])
        x += (4 + gap) * s
    return out


def text_w(txt, hgt, gap=1.6):
    n = len(txt.replace(" ", ""))
    return (n * (4 + gap) - gap + 3 * txt.count(" ")) * hgt / 6.


def sphere(cv, cx, cy, r, leafy=False):
    """A shaded ball, light from the upper left: hair hatch overall, heavy in the shadow crescent."""
    disc = ell(cx, cy, r, r, 28)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, -45, 2))
    sh = ell(cx, cy, r, r, 20, -PI * .25, PI * .75) + [
        (cx - r * .25 + r * .75 * math.cos(a), cy - r * .25 + r * .75 * math.sin(a))
        for a in [PI * .75 - PI * i / 20 for i in range(21)]]
    cv.line(C.hatch_poly(sh, 45, 1.5))
    if leafy:
        rng = random.Random(int(cx * 7 + cy))
        for _ in range(int(r * 1.6)):
            a = rng.uniform(0, 2 * PI)
            d = r * math.sqrt(rng.uniform(.05, .85))
            px, py = cx + d * math.cos(a), cy + d * math.sin(a)
            b = rng.uniform(0, PI)
            cv.hair([(px - 1.2 * math.cos(b), py - 1.2 * math.sin(b)), (px, py - .6), (px + 1.2 * math.cos(b), py + 1.2 * math.sin(b))])


# ----------------------------------------------------------------------------------------------
# the scene: opening night on a Pearl District street
# ----------------------------------------------------------------------------------------------

def dog(cv, x, y, s, face=1):
    """Parker's dog sitting in profile, feet at (x, y), about 14*s tall; face=+1 looks right.
    Engraved like everything else: white coat shaded along the form, a black floppy ear, nose and
    eye, a collar, and a tail curled round the haunch."""
    def P(pts):
        return [(x + face * px * s, y - py * s) for px, py in pts]
    body = P([(-4.6, 0), (-5.6, 1.8), (-5.9, 4.4), (-5.0, 6.8), (-2.8, 8.8), (-.6, 10.4), (.2, 12.4),
              (1.2, 13.8), (2.8, 14.1), (3.7, 13.3), (6.2, 12.9), (6.9, 12.1), (6.5, 11.3), (3.9, 10.9),
              (3.0, 9.9), (2.8, 7.8), (2.6, 4.8), (2.6, .6), (3.7, .4), (3.8, 0)])
    cv.obj([], 0)
    cv.heavy(P([(-4.8, .6), (-7.0, 1.0), (-8.0, 2.8), (-7.4, 4.6)]))
    cv.obj([body], 1.)
    # coat shading: dense on the belly and haunch underside, light on the back
    shade = P([(-5.6, 1.8), (-5.9, 4.4), (-4.2, 3.6), (-1.2, 2.4), (1.2, 2.8), (2.6, 4.8), (2.6, .6), (-4.6, 0)])
    cv.line(C.hatch_poly(shade, -20 * face, 1.5))
    cv.hair(C.hatch_poly(body, 30 * face, 2))
    cv.hair([P([(-5.0, 6.8), (-3.4, 5.2), (-2.6, 2.4), (-1.0, .4)]), P([(.6, 0), (.8, 3.4), (2.0, 7.4)])])
    ear = P([(1.4, 13.8), (.1, 12.9), (-.3, 10.4), (.6, 10.0), (1.9, 12.4)])
    solid(cv, ear, .5)
    solid(cv, P([(6.2, 12.9), (7.1, 12.6), (6.9, 11.9), (6.3, 12.0)]))
    solid(cv, P([(3.4, 12.8), (4.1, 12.9), (4.0, 12.3), (3.4, 12.3)]))
    cv.obj([], 0)
    cv.heavy(P([(.0, 10.6), (2.9, 10.0)]))
    cv.hair(P([(3.9, 11.4), (5.6, 11.6)]))
    cv.obj([P([(1.4, 9.9), (2.1, 9.7), (2.0, 8.9), (1.3, 9.1)])], .5)        # tag


def storefront(cv, X, Y, W, H, gy, rng, mfrac, tall=False):
    cx = X + W / 2
    u = H / 100.

    # sky: dusk, darkest at the top
    sky = R(X - 2, Y - 2, W + 4, gy - Y + 4)
    cv.obj([sky], 0)
    t1 = Y + (gy - Y) * .38
    t2 = Y + (gy - Y) * .7
    cv.line(C.hatch_poly(R(X - 2, Y - 2, W + 4, t1 - Y + 2), 0, 2, .5))
    cv.hair(C.hatch_poly(R(X - 2, t1, W + 4, t2 - t1), 0, 2, .5))
    cv.hair(C.hatch_poly(R(X - 2, t2, W + 4, gy - t2), 0, 3, .5))
    # moon and stars
    if tall:
        mr = max(4., min(6.5 * u, H * .05))
        mx, my = X + W * .74, Y + H * .1
    else:
        mr = max(4., 6.5 * u)
        mx, my = X + W * .19, Y + (gy - Y) * .22
    moon(cv, mx, my, mr, mfrac)
    for i in range(int(6 + W / 40)):
        sx, sy = X + rng.uniform(.06, .94) * W, Y + rng.uniform(.04, .34) * (gy - Y)
        if abs(sx - mx) > mr * 2 and abs(sx - cx) > W * .22:
            star(cv, sx, sy, rng.choice((1.6, 2.0, 2.6)))

    fw = min(W * (.56 if not tall else .64), H * 1.12)
    fx0, fx1 = cx - fw / 2, cx + fw / 2
    fy0 = Y + H * (.24 if not tall else .17)
    us = H * .19 if tall else 0.

    # the Pearl behind: brick warehouses with lit windows, a water tower
    x = X - 4
    k = 0
    tower_done = False
    while x < X + W:
        bw = rng.uniform(.17, .26) * W
        bh = rng.uniform(.4, .56) * (gy - Y)
        bx, by = x, gy - bh
        x += bw + rng.choice((0, 0, 3))
        k += 1
        body = R(bx, by, bw, bh + 2)
        cv.obj([body], 1.)
        cv.hair(C.hatch_poly(body, 90 if k % 2 else 0, 2, .25))
        cv.obj([R(bx - 1.5, by - 2.5, bw + 3, 3.5)], .5)
        cv.line(C.hatch_poly(R(bx - 1, by + .4, bw + 2, 2), 0, .8))
        ww, wh = 3.5, 5.
        cols = max(1, int((bw - 6) / 8))
        rows = max(1, int((bh - 14) / 11))
        gx = (bw - cols * ww) / (cols + 1)
        for r in range(rows):
            for c in range(cols):
                wx, wy = bx + gx + c * (ww + gx), by + 7 + r * 11
                if wy + wh > gy - 3:
                    continue
                win = R(wx, wy, ww, wh)
                if rng.random() < .45:
                    cv.obj([win], .5)
                    cv.hair([(wx, wy + wh / 2), (wx + ww, wy + wh / 2)])
                else:
                    solid(cv, win, .5)
        if not tower_done and (bx + bw < fx0 or bx > fx1) and bw > W * .16 and bx > X + W * .02:
            tower_done = True
            tx, tw, th = bx + bw * .5, max(9., bw * .3), max(9., (gy - Y) * .14)
            ty = by - 2.5 - th * .55
            for lx in (-.42, -.14, .14, .42):
                cv.obj([], 0)
                cv.line([(tx + lx * tw, ty), (tx + lx * tw * 1.15, by - 2.5)])
            cv.obj([], 0)
            cv.hair([[(tx - tw * .5, by - 2.5 - th * .1), (tx + tw * .48, ty + 1)], [(tx + tw * .5, by - 2.5 - th * .1), (tx - tw * .48, ty + 1)]])
            tank = R(tx - tw / 2, ty - th * .6, tw, th * .6)
            cv.obj([tank], 1.)
            cv.hair(C.hatch_poly(tank, 90, 1.5))
            cv.line(C.hatch_poly(R(tx + tw * .18, ty - th * .6, tw * .32, th * .6), 90, 1.5))
            for hy in (.25, .7):
                cv.line([(tx - tw / 2, ty - th * .6 * hy), (tx + tw / 2, ty - th * .6 * hy)])
            roof = [(tx - tw * .58, ty - th * .6), (tx, ty - th * 1.0), (tx + tw * .58, ty - th * .6)]
            cv.obj([roof], 1.)
            cv.hair(C.hatch_poly(roof, 0, 1.5))

    # ---- the new restaurant -----------------------------------------------------------------
    cv.obj([R(fx1, fy0 + 3, 3, gy - fy0 - 3)], 0)
    cv.line(C.hatch_poly(R(fx1, fy0 + 3, 3, gy - fy0 - 3), 0, .8))
    face = R(fx0, fy0, fw, gy - fy0)
    cv.obj([face], 1.)
    cv.hair(C.hatch_poly(face, 0, 3, fy0 % 3))
    yy, row = fy0, 0
    while yy < gy - 3:
        off = 3 if row % 2 else 0
        xx = fx0 + off
        seg = []
        while xx < fx1 - .5:
            seg.append([(xx, yy), (xx, yy + 3)])
            xx += 6
        cv.hair(seg)
        yy += 3
        row += 1
    for px in (fx0, fx1 - fw * .06):
        p = R(px, fy0, fw * .06, gy - fy0)
        cv.obj([p], 1.)
        cv.hair(C.hatch_poly(p, 90, 2))
        cv.line(C.hatch_poly(R(px + fw * .04, fy0, fw * .02, gy - fy0), 90, 1.5))
    # cornice with dentils
    ch = max(4., 4.5 * u)
    cor = R(fx0 - 4, fy0 - ch, fw + 8, ch)
    cv.obj([cor], 1.)
    cv.hair(C.hatch_poly(R(fx0 - 4, fy0 - ch * .55, fw + 8, ch * .55), 0, 1.5))
    cv.obj([R(fx0 - 5.5, fy0 - ch - 2, fw + 11, 2)], 1.)
    cv.obj([R(fx0 - 2, fy0, fw + 4, 3)], .5)
    cv.line(C.hatch_poly(R(fx0 - 2, fy0 + .3, fw + 4, 2.7), 90, 3.5, (fx0 + 1.5) % 3.5))
    if us:
        # upper storey: a row of arched windows, half of them lit, with keystones and sills
        nw = 4
        for j in range(nw):
            wx0 = fx0 + fw * .1 + (fw * .8) * j / nw + fw * .035
            ww_ = fw * .8 / nw - fw * .07
            wy0 = fy0 + 3 + us * .2
            wy1 = fy0 + 3 + us * .86
            arch = [(wx0, wy1), (wx0, wy0 + ww_ / 2)] + [
                (wx0 + ww_ / 2 - ww_ / 2 * math.cos(PI * i / 12), wy0 + ww_ / 2 - ww_ / 2 * math.sin(PI * i / 12)) for i in range(13)] + [(wx0 + ww_, wy1)]
            cv.obj([[(p[0] + (p[0] - wx0 - ww_ / 2) * .25, p[1] - 1.8) for p in arch[1:-1]] + [(wx0 + ww_ + 1, wy0 + ww_ / 2), (wx0 - 1, wy0 + ww_ / 2)]], .5)
            cv.hair(C.hatch_poly(R(wx0 - 2, wy0 - 3, ww_ + 4, ww_ / 2 + 2), 0, 1.5))
            cv.obj([arch], 1.)
            if (j + rng.randrange(2)) % 2:
                cv.hair(C.hatch_poly(arch, 0, 3))
                cv.hair([(wx0 + ww_ * .3, wy1), (wx0 + ww_ * .3, wy1 - (wy1 - wy0) * .4)])
            else:
                cv.line(C.hatch_poly(arch, 0, 1.5))
                cv.hair(C.hatch_poly(arch, 90, 2))
            cv.obj([], 0)
            cv.line([(wx0 + ww_ / 2, wy0), (wx0 + ww_ / 2, wy1)])
            cv.hair([(wx0, wy0 + (wy1 - wy0) * .55), (wx0 + ww_, wy0 + (wy1 - wy0) * .55)])
            cv.obj([[(wx0 + ww_ / 2 - 1.6, wy0 - 3), (wx0 + ww_ / 2 + 1.6, wy0 - 3), (wx0 + ww_ / 2 + 1, wy0 + 1), (wx0 + ww_ / 2 - 1, wy0 + 1)]], .5)
            cv.obj([R(wx0 - 2, wy1, ww_ + 4, 2)], 1.)
            cv.line(C.hatch_poly(R(wx0 - 1, wy1 + 2, ww_ + 2, 1.6), 0, .8))
        # flower boxes under the lit windows
    # sign band with an OPEN plaque between two rosettes
    sb0 = fy0 + 4 + us
    sbh = max(9., 10 * u)
    band = R(fx0 + fw * .07, sb0, fw * .86, sbh)
    cv.obj([band], 1.)
    cv.hair(C.hatch_poly(band, 45, 2))
    cv.line(C.hatch_poly(R(fx0 + fw * .07, sb0 + sbh - 2, fw * .86, 2), 0, .8))
    lh = min(sbh * .55, 7.)
    tw = text_w("OPEN", lh)
    plq = ell(cx, sb0 + sbh / 2, tw / 2 + 5, sbh / 2 - 1.2, 32)
    cv.obj([plq], 1.)
    cv.hair(closed(ell(cx, sb0 + sbh / 2, tw / 2 + 3.6, sbh / 2 - 2.4, 32)))
    cv.line(letters("OPEN", cx - tw / 2, sb0 + sbh / 2 - lh / 2, lh))
    for sd in (-1, 1):
        rx = cx + sd * (tw / 2 + 5 + (fw * .43 - tw / 2 - 5) * .5)
        rr = sbh / 2 - 1
        ry_ = sb0 + sbh / 2
        cv.obj([ell(rx, ry_, rr, rr, 20)], 1.)
        for j in range(8):
            a_ = 2 * PI * j / 8
            pet = [(rx, ry_), (rx + rr * .85 * math.cos(a_ + .3), ry_ + rr * .85 * math.sin(a_ + .3)),
                   (rx + rr * .95 * math.cos(a_), ry_ + rr * .95 * math.sin(a_)),
                   (rx + rr * .85 * math.cos(a_ - .3), ry_ + rr * .85 * math.sin(a_ - .3))]
            cv.hair(closed(pet))
        solid(cv, ell(rx, ry_, rr * .28, rr * .28, 10))
    # awning: alternating stripes, scalloped valance, flaring out
    ay0 = sb0 + sbh + 2
    ah = max(10., 13 * u)
    ay1 = ay0 + ah
    flare = ah * .35
    nst = 11
    vh = max(3., 3.6 * u)
    for i in range(nst):
        t0, t1_ = i / nst, (i + 1) / nst
        xa0, xa1 = fx0 + 2 + (fw - 4) * t0, fx0 + 2 + (fw - 4) * t1_
        xb0, xb1 = fx0 - flare + (fw + 2 * flare) * t0, fx0 - flare + (fw + 2 * flare) * t1_
        m = (xb0 + xb1) / 2
        st = [(xa0, ay0), (xa1, ay0), (xb1, ay1)] + [
            (m + (xb1 - xb0) / 2 * math.cos(PI * j / 8), ay1 + vh * math.sin(PI * j / 8)) for j in range(1, 8)] + [(xb0, ay1)]
        cv.obj([st], .5)
        if i % 2 == 0:
            cv.line(C.hatch_poly(st, 0, 1.5))
        else:
            cv.hair(C.hatch_poly(st, 0, 3))
    cv.obj([], 0)
    cv.line([(fx0 - flare, ay1), (fx1 + flare, ay1)])

    # shopfront below the awning
    sy0 = ay1 + vh
    dw = fw * .2
    dx0 = cx - dw / 2
    base_h = max(4., 5 * u)
    for sd in (-1, 1):
        wx0 = fx0 + fw * .08 if sd < 0 else cx + dw / 2 + fw * .04
        wx1 = cx - dw / 2 - fw * .04 if sd < 0 else fx1 - fw * .08
        wy0, wy1 = sy0 + 2, gy - base_h - 2
        win = R(wx0, wy0, wx1 - wx0, wy1 - wy0)
        cv.obj([win], 1.)
        cv.hair(C.hatch_poly(win, 0, 2))
        cv.hair(C.hatch_poly(R(wx0, wy0, wx1 - wx0, (wy1 - wy0) * .45), 90, 2))
        nl = 3
        for j in range(nl):
            lx = wx0 + (wx1 - wx0) * (j + .5) / nl
            ly = wy0 + (wy1 - wy0) * .38
            cv.obj([], 0)
            cv.hair([(lx, wy0), (lx, ly - 2)])
            bell = [(lx - 2.6, ly + 1.4), (lx - 1.6, ly - 1), (lx, ly - 2.2), (lx + 1.6, ly - 1), (lx + 2.6, ly + 1.4)]
            cv.obj([bell], 1.)
            cv.hair([(lx - 1.6, ly + .8), (lx - .6, ly - 1.2)])
        ty_ = wy0 + (wy1 - wy0) * .72
        tab = R(wx0 + 2, ty_, wx1 - wx0 - 4, 1.8)
        cv.obj([tab], .5)
        for j in range(nl):
            gx_ = wx0 + (wx1 - wx0) * (j + .5) / nl
            cv.obj([[(gx_ - 1.2, ty_), (gx_ - 1.2, ty_ - 2.6), (gx_ + 1.2, ty_ - 2.6), (gx_ + 1.2, ty_)]], .5)
            cv.hair([(gx_ - 3.5, ty_ - .2), (gx_ - 2.2, ty_ - 1.6)])
        g = [(wx0 + (wx1 - wx0) * .55, wy0), (wx0 + (wx1 - wx0) * .7, wy0), (wx0 + (wx1 - wx0) * .25, wy1), (wx0 + (wx1 - wx0) * .1, wy1)]
        cv.obj([g], 0)
        cv.hair(C.hatch_poly(g, 0, 3))
        cv.obj([], 0)
        cv.heavy([(wx0 + (wx1 - wx0) / 2, wy0), (wx0 + (wx1 - wx0) / 2, wy1)])
        cv.line([(wx0, wy0 + (wy1 - wy0) * .22), (wx1, wy0 + (wy1 - wy0) * .22)])
        riser = R(wx0 - 1, wy1, wx1 - wx0 + 2, gy - wy1)
        cv.obj([riser], 1.)
        cv.hair(C.hatch_poly(riser, 0, 2))
        cv.obj([R(wx0 + 1.5, wy1 + 1.5, wx1 - wx0 - 3, gy - wy1 - 3)], .5)
        cv.hair(C.hatch_poly(R(wx0 + 1.5, wy1 + 1.5, wx1 - wx0 - 3, gy - wy1 - 3), 90, 3))
        cv.obj([R(wx0 - 2.5, wy1 - .8, wx1 - wx0 + 5, 1.8)], 1.)
    # door with transom, glass and a grand-opening ribbon tied in a bow
    dy0 = sy0 + 1
    door = R(dx0, dy0, dw, gy - dy0 - 2)
    cv.obj([door], 1.)
    cv.line(C.hatch_poly(door, 0, 1.5))
    trh = max(4., (gy - dy0) * .16)
    tr = R(dx0 + 1.5, dy0 + 1.5, dw - 3, trh)
    cv.obj([tr], .5)
    cv.hair(C.hatch_poly(tr, 0, 3))
    cv.line(letters("P", cx - trh * .2, dy0 + 1.5 + trh * .18, trh * .64))
    gl = R(dx0 + dw * .2, dy0 + trh + 4, dw * .6, (gy - dy0) * .42)
    cv.obj([gl], .5)
    cv.hair(C.hatch_poly(gl, 45, 2))
    cv.hair(C.hatch_poly(gl, -45, 2))
    pl = R(dx0 + dw * .2, gl[2][1] + 3, dw * .6, (gy - dy0) * .16)
    cv.obj([pl], .5)
    cv.hair(C.hatch_poly(pl, 0, 2))
    cv.obj([ell(dx0 + dw * .82, gl[2][1] + 1.5, 1, 1, 8)], .5)
    for j in range(2):
        st = R(dx0 - 3 - j * 2.5, gy - 4.2 + j * 2.2, dw + 6 + j * 5, 2.4)
        cv.obj([st], 1.)
        cv.line(C.hatch_poly(R(st[0][0], st[0][1] + 1.4, st[1][0] - st[0][0], 1.), 0, .8))
    ry = dy0 + (gy - dy0) * .48
    rw = 2.2
    rib = [(fx0 + fw * .05, ry - rw - 2), (cx - 2, ry - rw), (cx - 2, ry + rw), (fx0 + fw * .05, ry + rw - 2)]
    rib2 = [(cx + 2, ry - rw), (fx1 - fw * .05, ry - rw - 2), (fx1 - fw * .05, ry + rw - 2), (cx + 2, ry + rw)]
    for rb in (rib, rib2):
        cv.obj([rb], 1.)
        cv.hair([((rb[0][0] + rb[3][0]) / 2, (rb[0][1] + rb[3][1]) / 2), ((rb[1][0] + rb[2][0]) / 2, (rb[1][1] + rb[2][1]) / 2)])
    for sd in (-1, 1):
        tail = [(cx, ry), (cx + sd * 2.6, ry + 7.5), (cx + sd * 1.5, ry + 6.6), (cx + sd * .5, ry + 7.8), (cx - sd * .6, ry + 1)]
        cv.obj([tail], 1.)
        cv.hair([(cx + sd * .8, ry + 2), (cx + sd * 1.5, ry + 6)])
    for sd in (-1, 1):
        loop = [(cx, ry), (cx + sd * 3, ry - 4), (cx + sd * 7, ry - 4.2), (cx + sd * 7.5, ry - .5), (cx + sd * 4.5, ry + 1.5)]
        cv.obj([loop], 1.)
        cv.hair([(cx + sd * 2.5, ry - 1.5), (cx + sd * 6, ry - 2.5)])
        cv.line(C.hatch_poly([(cx, ry), (cx + sd * 7.5, ry - .5), (cx + sd * 4.5, ry + 1.5)], 0, 1.5))
    cv.obj([ell(cx, ry, 1.6, 1.8, 10)], 1.)
    for sd in (-1, 1):
        sx = cx + sd * (dw / 2 + fw * .02)
        sy_ = sy0 + (gy - sy0) * .18
        cv.obj([], 0)
        cv.line([(sx, sy_ + 3), (sx, sy_ + 6)])
        lamp = [(sx - 1.6, sy_ + 3), (sx - 1.2, sy_), (sx, sy_ - 1.2), (sx + 1.2, sy_), (sx + 1.6, sy_ + 3)]
        cv.obj([lamp], 1.)
    # hanging blade sign: bracket and an oval with crossed fork and knife
    bx_ = fx1 + 1
    by_ = ay0 - 2
    sw_ = max(9., 10 * u)
    cv.obj([], 0)
    cv.line([(bx_, by_), (bx_ + sw_ * 1.5, by_)])
    cv.hair([(bx_, by_ + 3), (bx_ + sw_ * .6, by_)])
    cv.hair(ell(bx_ + sw_ * .45, by_ + 1.6, 1.5, 1.5, 12, 0, 1.7 * PI))
    sx_, sy2 = bx_ + sw_ * 1.15, by_ + 2 + sw_ * .7
    cv.hair([[(sx_ - sw_ * .25, by_), (sx_ - sw_ * .25, sy2 - sw_ * .68)], [(sx_ + sw_ * .25, by_), (sx_ + sw_ * .25, sy2 - sw_ * .68)]])
    so = ell(sx_, sy2, sw_ * .55, sw_ * .72, 28)
    cv.obj([so], 1.)
    cv.hair(closed(ell(sx_, sy2, sw_ * .42, sw_ * .58, 28)))
    a = sw_ * .38
    cv.line([(sx_ - a * .6, sy2 + a), (sx_ + a * .5, sy2 - a * .9)])
    for t in (-.9, 0, .9):
        cv.hair([(sx_ + a * .5 + t * .7, sy2 - a * .9 + t * .3), (sx_ + a * .72 + t * .7, sy2 - a * 1.25 + t * .3)])
    knife = [(sx_ + a * .6, sy2 + a), (sx_ - a * .5, sy2 - a * .7), (sx_ - a * .55, sy2 - a * 1.15), (sx_ - a * .15, sy2 - a * .45)]
    cv.obj([knife], 0)
    cv.heavy(knife[:2])
    cv.line([knife[1], knife[2], knife[3]])

    # ---- sidewalk and street ----------------------------------------------------------------
    walk = R(X - 2, gy, W + 4, Y + H - gy + 2)
    cv.obj([walk], 1.)
    cv.hair(C.hatch_poly(walk, 0, 2, gy % 2))
    for i in range(-8, 9):
        x_top = cx + i * fw * .2
        x_bot = cx + (x_top - cx) * 2.4
        if i:
            cv.hair([(x_top, gy), (x_bot, Y + H + 2)])
    curb_y = gy + (Y + H - gy) * .62
    cv.obj([R(X - 2, curb_y, W + 4, 2.4)], 1.)
    cv.line(C.hatch_poly(R(X - 2, curb_y + 2.4, W + 4, Y + H - curb_y), 0, 1.5))
    cv.obj([], 0)
    cv.line(C.hatch_poly([(fx0, gy + .5), (fx1, gy + .5), (fx1 + 6, gy + 3), (fx0 + 6, gy + 3)], 0, 1.5))

    pr = max(5., 7 * u)
    for sd in (-1, 1):
        px = fx0 - pr * 1.1 if sd < 0 else fx1 + pr * 1.1
        pot = [(px - pr * .7, gy - pr * 1.2), (px + pr * .7, gy - pr * 1.2), (px + pr * .5, gy + 1.5), (px - pr * .5, gy + 1.5)]
        cv.obj([], 0)
        cv.line([(px, gy - pr * 1.2), (px, gy - pr * 2.0)])
        sphere(cv, px, gy - pr * 2.6, pr, True)
        cv.obj([pot], 1.)
        cv.hair(C.hatch_poly(pot, 90, 2))
        cv.line(C.hatch_poly([(px + pr * .15, gy - pr * 1.2), (px + pr * .7, gy - pr * 1.2), (px + pr * .5, gy + 1.5), (px + pr * .1, gy + 1.5)], 90, 1.5))
        cv.obj([R(px - pr * .8, gy - pr * 1.35, pr * 1.6, pr * .3)], 1.)
    # Easter egg: Parker's dog waiting by the door
    dog(cv, cx + dw / 2 + fw * .16, gy + (curb_y - gy) * .7, max(.75, .95 * u), -1)
    return cv


def cloche(cv, cx, cy, r, X, Y, W, H):
    """Short-plate medallion: a cloche lifted off a platter, steam curling up from the dish."""
    bg = R(X - 2, Y - 2, W + 4, H + 4)
    cv.obj([bg], 0)
    cv.hair(C.hatch_poly(bg, 0, 2))
    pl = ell(cx, cy + r * .55, r * 1.5, r * .32, 36)
    cv.obj([pl], 1.)
    cv.hair(closed(ell(cx, cy + r * .55, r * 1.2, r * .22, 36)))
    cv.line(C.hatch_poly(ell(cx, cy + r * .62, r * 1.5, r * .26, 36, 0, PI) + [(cx - r * 1.5, cy + r * .55)], 0, 1.5))
    bowl = ell(cx, cy + r * .4, r * .7, r * .38, 24, 0, PI) + [(cx - r * .7, cy + r * .4)]
    cv.obj([bowl], 1.)
    cv.hair(C.hatch_poly(bowl, 0, 1.5))
    cv.obj([], 0)
    for j, ox in enumerate((-.4, -.05, .3)):
        pts = [(cx + ox * r + math.sin(t / 6 * PI * 1.5 + j * 1.3) * r * .13, cy + r * .3 - t / 12 * r * 1.15) for t in range(13)]
        cv.line(pts)
    lx, ly = cx + r * 1.25, cy - r * .3
    rot = .5

    def rp(x, y):
        return (lx + x * math.cos(rot) - y * math.sin(rot), ly + x * math.sin(rot) + y * math.cos(rot))
    dome = [rp(r * .95 * math.cos(PI + PI * i / 24), r * .8 * math.sin(PI + PI * i / 24)) for i in range(25)]
    cv.obj([dome], 1.)
    for k in range(1, 7):
        s = k / 7
        arc = [rp(r * .95 * s * math.cos(PI + PI * i / 24) + r * .95 * (1 - s) * .5, r * .8 * math.sin(PI + PI * i / 24))
               for i in range(25)]
        (cv.line if k > 4 else cv.hair)(arc)
    kx, ky = rp(0, -r * .8)
    cv.obj([ell(kx, ky, r * .14, r * .1, 12)], 1.)


# ----------------------------------------------------------------------------------------------
# figures the volutes curl into (in place of the drilled eye)
# ----------------------------------------------------------------------------------------------

def boss(cv, cx, cy, r):
    """A round sunk boss in the volute's eye: white disc, black fillet ring, ruled field."""
    cv.obj([ell(cx, cy, r, r, 32)], 1.)
    cv.line(closed(ell(cx, cy, r - 1.4, r - 1.4, 32)))
    inner = ell(cx, cy, r - 2.4, r - 2.4, 32)
    cv.obj([inner], .5)
    cv.hair(C.hatch_poly(inner, 0, 2))


def concha(cv, cx, cy, r):
    """The vegan Mexican bakery's concha: a domed sweet bun with its shell-scored sugar crust."""
    rx, ry = r * .8, r * .55
    by = cy + r * .12
    bh = ry * .42
    base = [(cx - rx * .98, by)] + [(cx - rx * .98 * math.cos(PI * i / 12), by + bh * math.sin(PI * i / 12)) for i in range(1, 12)] + [(cx + rx * .98, by)]
    cv.obj([base], 1.)
    cv.hair(C.hatch_poly(base, 0, 2))
    cv.line(C.hatch_poly([(cx + rx * .3, by)] + base[8:], 0, 1.5))
    dome = ell(cx, by + .5, rx, ry, 28, PI, 2 * PI)
    cv.obj([dome + [(cx + rx, by + 1.2), (cx - rx, by + 1.2)]], 1.)
    top = (cx - rx * .05, by - ry * 1.02)
    for k in range(-4, 5):
        a = PI * 1.5 + k * PI / 10
        cv.hair([top, (cx + rx * .97 * math.cos(a) * 1.0, by + ry * .97 * math.sin(a))])
    cv.hair([ell(cx, by, rx * f, ry * f, 18, PI * 1.08, PI * 1.92) for f in (.45, .72)])
    shade = ell(cx, by + .5, rx, ry, 14, PI * 1.62, 2 * PI) + [(cx + rx * .55, by)] + ell(cx, by, rx * .55, ry * .62, 10, 2 * PI, PI * 1.62)[::-1][1:]
    shade = ell(cx, by + .5, rx, ry, 14, PI * 1.62, 2 * PI) + ell(cx + rx * .12, by, rx * .68, ry * .7, 10, PI * 1.62, 2 * PI)[::-1]
    cv.line(C.hatch_poly(shade, 30, 1.5))


def noodle_bowl(cv, cx, cy, r):
    """The new North Portland Thai place: a bowl of noodles with crossed chopsticks
    (two drumsticks in disguise)."""
    rx = r * .66
    ty = cy - r * .02
    cv.obj([], 0)
    cv.heavy([(cx - r * .7, cy - r * .62), (cx + r * .22, ty + r * .05)])
    cv.heavy([(cx + r * .62, cy - r * .7), (cx - r * .12, ty + r * .05)])
    bowl = [(cx - rx, ty)] + [(cx - rx * math.cos(PI * i / 14), ty + r * .55 * math.sin(PI * i / 14)) for i in range(1, 14)] + [(cx + rx, ty)]
    foot = R(cx - r * .22, ty + r * .5, r * .44, r * .12)
    cv.obj([foot], 1.)
    cv.obj([bowl], 1.)
    sh = [(cx + rx * math.cos(PI * i / 14 * .5), ty + r * .55 * math.sin(PI * i / 14 * .5 + 0)) for i in range(15)]
    cv.line(C.hatch_poly([(cx + rx * .1, ty)] + [(cx + rx * math.cos(a), ty + r * .55 * math.sin(a)) for a in [PI * i / 20 for i in range(0, 13)]], 90, 1.5))
    cv.hair([[(cx - rx * .8, ty + r * .2), (cx + rx * .8, ty + r * .2)]])
    rim = ell(cx, ty, rx, r * .14, 24)
    cv.obj([rim], 1.)
    cv.hair([[(cx - rx * .8 + rx * 1.6 * j / 10, ty + r * .05 * math.sin(j * 2.1)) for j in range(11)]])
    for j in range(3):
        x0 = cx - r * .25 + j * r * .25
        cv.hair([(x0 + math.sin(t * 1.3 + j) * 1.2, ty - 2 - t * r * .06) for t in range(7)])


# ----------------------------------------------------------------------------------------------
# layouts (from the house frame, so the cartouche field is engraved to its very edge)
# ----------------------------------------------------------------------------------------------

def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b, C._superellipse(cx, cy, a, b)


def _clip_poly(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{C._d(poly, True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _scene_in(cx, cy, a, b, field, seed, mfrac, tall=False):
    rng = random.Random(seed)
    X, Y, W, H = cx - a, cy - b, 2 * a, 2 * b
    framed = tall
    tall = tall and H > W * .85
    gy = Y + H * (.87 if tall else (.78 if framed else .84))
    cv = storefront(C.Canvas(), X, Y, W, H, gy, rng, mfrac, tall)
    return _clip_poly(C._uid("lf", cx, cy, a, b), field, cv.svg())


def _layout_band(w, h, seed, mfrac):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = ell(cx, cy, rx - 2, ry - 2, 64)
    cv = C.Canvas()
    cloche(cv, cx - rx * .28, cy + ry * .08, ry * .6, cx - rx, cy - ry, 2 * rx, 2 * ry)
    o.append(_clip_poly(C._uid("bc", w, h), field, cv.svg()))
    o.append(f'<path d="{C._d(closed(ell(cx, cy, rx - 4, ry - 4, 64)))}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{C._n(h - .5)}h{C._n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed, mfrac):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.6)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
        a0, fl = (90., True) if side < 0 else (90., False)
        eyes.append(C.volute_spine(vx, vy, r, a0, 1.4, fl, .9, -.5)[-1])
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    for (ex, ey), fig in zip(eyes, (concha, noodle_bowl)):
        fig(cv, ex, ey + r * .06, r * .34)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b, field = _field(cx, cy, cw, ch)
    o.append(_scene_in(cx, cy, a, b, field, seed, mfrac))
    o.append(f'<path d="{C._d(closed(field), tol=.1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, mfrac, density=.85):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h + ped_h * .3
    o.append(f'<path d="M{C._n(px0 - 3.5)},{C._n(py0 - 3.5)}h{C._n(pw + 7)}v{C._n(ph + 7)}h{C._n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{C._n(px0 - 1.5)},{C._n(py0 - 1.5)}h{C._n(pw + 3)}v{C._n(ph + 3)}h{C._n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .25)
    eyes = []
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
        a0, fl = (100., True) if side < 0 else (80., False)
        ex_, ey_ = C.volute_spine(vx, vy, r1, a0, 1.45, fl, .8, -.5)[-1]
        eyes.append((ex_, ey_, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    for (ex, ey, er), fig in zip(eyes, (concha, noodle_bowl)):
        fig(cv, ex, ey + er * .06, er * .34)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b, field = _field(cx, cy, cw, ch)
    o.append(_scene_in(cx, cy, a, b, field, seed, mfrac, True))
    o.append(f'<path d="{C._d(closed(field), tol=.1)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, cl = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lh = min(bh * .5, 8.)
    msg = "NOW OPEN"
    tw = text_w(msg, lh, 2.4)
    bx = cx - tw / 2
    mid = cl[len(cl) // 2]
    o.append(f'<path d="{"".join(C._d(q, tol=0) for q in letters(msg, bx, cy + ch * .47 - 4 - lh / 2, lh, 2.4))}" stroke="#000" stroke-width="1"/>')
    p, (tx, ty, tw2, th2) = C.pedestal(0, h - ped_h, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{C._n(tx + 2)},{C._n(ty + 2)}h{C._n(tw2 - 3)}v{C._n(th2 - 3)}h{C._n(-tw2 + 3)}z" fill="{C.pat("L")}" stroke="none"/>')
    title = "NEW AND OPENING AROUND TOWN"
    lh2 = min(th2 * .5, 8.)
    t2 = text_w(title, lh2, 2.)
    o.append(f'<path d="M{C._n(cx - t2 / 2 - 4)},{C._n(ty + th2 / 2 - lh2 / 2 - 2.5)}h{C._n(t2 + 8)}v{C._n(lh2 + 5)}h{C._n(-t2 - 8)}z" fill="#fff" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(C._d(q, tol=0) for q in letters(title, cx - t2 / 2, ty + th2 / 2 - lh2 / 2, lh2, 2.))}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "2026-11-11")
    seed = sum(map(ord, date)) + 2
    mf = moon_frac(date)
    if h < 110:
        body = _layout_band(w, h, seed, mf)
    elif h <= 260:
        body = _layout_medium(w, h, seed, mf)
    else:
        body = _layout_tall(w, h, seed, mf)
    return C.svg_doc(w, h, body)
