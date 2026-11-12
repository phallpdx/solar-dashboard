"""local-04 "New at the St. Johns liquor store": the shop's new bottles as an engraved still life.

A bourbon bottle (its label carries a "P" monogram), a squat tequila bottle with an agave on its
label, a rocks glass with ice and an upright oak cask stand on the bar, with blue agave springing at
either side. Behind them the Willamette and the St. Johns Bridge's gothic towers, under a ruled sky
with the day's moon. The cask head is branded with a tiny "P" (Parker's Easter egg). The house frame
(engraving_codex) carries it: frieze/medallion, cartouche, or full scroll frame with banner and
pedestal, both lettered in drawn paths.
"""
import sys
import math
import random
import datetime

import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, pat, _d, _n, _ell_pts, _uid, _clip, _superellipse

PI = math.pi

# ------------------------------------------------------------------------------------------------
# a small single-stroke roman capital font (grid 4 wide x 6 tall, y down)
# ------------------------------------------------------------------------------------------------
_O = [(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]
_P = [(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]
GLYPH = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.5), (2.5, 3.5)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.5)], [(1.3, 2.7), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2.5, 4), (5, 0), (5, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [_O],
    "P": [_P],
    "Q": [_O, [(2.5, 4.5), (4.3, 6.3)]],
    "R": [_P, [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1.2, 6), (2.5, 2), (3.8, 6), (5, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "*": [[(1, 2), (2, 3), (1, 4), (0, 3), (1, 2)]],
    ".": [[(.5, 5.5), (.5, 6)]],
}


def _gw(ch):
    return 1.6 if ch in "*." else (2.2 if ch == " " else (5 if ch in "MW" else (4 if ch != "I" else 4)))


def text_width(s, size):
    k = size / 6
    return sum((_gw(c) + 1.8) * k for c in s) - 1.8 * k


def text_lines(s, x, y, size, tf=None):
    """Polylines for s, top-left at (x, y), cap height size. tf(px, py) maps points (optional)."""
    k = size / 6
    out = []
    cx = x
    for c in s:
        for pl in GLYPH.get(c, []):
            pts = [(cx + px * k, y + py * k) for px, py in pl]
            out.append([tf(*p) for p in pts] if tf else pts)
        cx += (_gw(c) + 1.8) * k
    return out


def _pd(lines):
    return "".join(_d(p, tol=0) for p in lines)


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------
def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .5 - .76
    return (days / 29.530588) % 1.


def _cyl_hatch(cv, poly, cx, hw, pitch=1.5, glass=False, cross=True, edge=True):
    """Lines along a vertical cylinder: dense in the shadow (right), a white highlight band on the
    left-centre, half density on the turned left edge."""
    for i, l in enumerate(hatch_poly(poly, 90, pitch, cx % pitch)):
        x = l[0][0]
        s = (x - cx) / hw
        k = int(round((x - cx) / pitch))
        if glass:
            keep = s > .62 or s < -.78 or (-.1 < s < .35 and k % 2 == 0) or (.35 <= s <= .62)
        else:
            if s > .25:
                keep = True
            elif s > -.12:
                keep = k % 2 == 0
            elif s > -.5:
                keep = False
            elif s > -.82:
                keep = k % 2 == 0
            else:
                keep = True
        if keep:
            cv.hair(l)
    if cross:
        for l in hatch_poly(poly, 62, 2.):
            mx = (l[0][0] + l[-1][0]) / 2
            if (mx - cx) / hw > .5:
                # trim to the shadow side
                a, b = l
                t0 = 0.
                if a[0] < cx + .5 * hw:
                    t0 = (cx + .5 * hw - a[0]) / ((b[0] - a[0]) or 1e-9)
                    t0 = min(max(t0, 0.), 1.)
                cv.hair([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), b])


def _profile(cx, segs, base_y, base_e):
    """Closed outline of a turned object: segs is [(y, half-width)] top to bottom; the base is an
    elliptical arc (ry = base_e * hw) so it sits in slight perspective."""
    left = [(cx - w, y) for y, w in segs]
    hwb = segs[-1][1]
    arc = [(cx - hwb * math.cos(PI * i / 16), base_y + base_e * hwb * math.sin(PI * i / 16)) for i in range(17)]
    right = [(cx + w, y) for y, w in segs[::-1]]
    return left[:-1] + arc + right[1:]


def _interp(segs, y):
    for (y0, w0), (y1, w1) in zip(segs, segs[1:]):
        if y0 <= y <= y1:
            return w0 + (w1 - w0) * ((y - y0) / ((y1 - y0) or 1))
    return segs[-1][1]


# ------------------------------------------------------------------------------------------------
# the subject pieces
# ------------------------------------------------------------------------------------------------
def _sky(cv, fx, fy, fw, fh, yh, rng, moon=None):
    cv.obj([], 0)
    y = fy + .75
    while y < yh:
        t = (y - fy) / max(1., yh - fy)
        pitch = 3. if t < .38 else (2. if t < .78 else 1.5)
        segs = [[(fx - 2, y), (fx + fw + 2, y)]]
        if moon:
            mx, my, mr = moon
            dy = abs(y - my)
            if dy < mr + 2.2:
                halo = math.sqrt(max(0., (mr + 2.2) ** 2 - dy * dy))
                segs = [[(fx - 2, y), (mx - halo, y)], [(mx + halo, y), (fx + fw + 2, y)]]
        for s in segs:
            cv.hair(s)
        y += pitch
    if moon:
        mx, my, mr = moon
        # a scatter of stars: small engraved four-point crosses
        for i in range(int(fw * (yh - fy) / 1400) + 3):
            sx, sy = fx + rng.uniform(.05, .95) * fw, fy + rng.uniform(.06, .6) * (yh - fy)
            if math.hypot(sx - mx, sy - my) < mr * 2.6:
                continue
            k = rng.choice((1.4, 1.8, 2.4))
            cv.obj([[(sx - k - .6, sy - .9), (sx + k + .6, sy - .9), (sx + k + .6, sy + .9), (sx - k - .6, sy + .9)],
                    [(sx - .9, sy - k - .6), (sx + .9, sy - k - .6), (sx + .9, sy + k + .6), (sx - .9, sy + k + .6)]], 0)
            cv.hair([[(sx - k, sy), (sx + k, sy)], [(sx, sy - k), (sx, sy + k)]])


def _moon(cv, mx, my, r, phase):
    disc = _ell_pts(mx, my, r, r, 36)
    cv.obj([disc], 0)
    k = math.cos(2 * PI * phase)
    n = 24
    dark = []
    if phase < .5:
        for i in range(n + 1):
            yy = -1 + 2 * i / n
            dark.append((mx - r * math.sqrt(1 - yy * yy), my + r * yy))
        for i in range(n, -1, -1):
            yy = -1 + 2 * i / n
            dark.append((mx + r * math.sqrt(1 - yy * yy) * k, my + r * yy))
    else:
        for i in range(n + 1):
            yy = -1 + 2 * i / n
            dark.append((mx + r * math.sqrt(1 - yy * yy), my + r * yy))
        for i in range(n, -1, -1):
            yy = -1 + 2 * i / n
            dark.append((mx - r * math.sqrt(1 - yy * yy) * k, my + r * yy))
    cv.hair(hatch_poly(dark, 0, 1.5, my % 1.5 + .75))
    cv.hair(hatch_poly(dark, 90, 3., mx % 3))
    ring = _ell_pts(mx, my, r + .9, r + .9, 40)
    cv.hair(ring + [ring[0]])
    # the lit limb, a fine heavier arc on the sunward side
    arc = [(mx + (1 if phase < .5 else -1) * (r - .4) * math.cos(a), my + (r - .4) * math.sin(a))
           for a in [-PI / 2 + PI * i / 20 for i in range(21)]]
    cv.line(arc)
    # maria on the lit face
    for a, rr, s in ((.6, .45, .22), (2.3, .35, .16), (4.0, .5, .18)):
        px, py = mx + r * rr * math.cos(a), my + r * rr * math.sin(a)
        cv.hair(hatch_poly(_ell_pts(px, py, r * s * 1.3, r * s, 10), 30, 1.5))


def _hills(cv, fx, fw, yh, fh, rng):
    top = []
    n = 40
    ph = rng.uniform(0, 6)
    for i in range(n + 1):
        t = i / n
        top.append((fx - 2 + (fw + 4) * t,
                    yh - fh * (.035 + .03 * math.sin(t * 5 + ph) ** 2 + .015 * math.sin(t * 17 + ph * 2))))
    poly = top + [(fx + fw + 2, yh + 1), (fx - 2, yh + 1)]
    cv.obj([poly], .5)
    cv.hair(hatch_poly(poly, 0, 1.5, .75))
    cv.hair(hatch_poly(poly, 75, 3.))
    # fir tips along the ridge (Forest Park)
    for i in range(1, n, 2):
        x, y = top[i]
        hgt = fh * .018 + rng.uniform(0, 1.5)
        cv.hair([(x - 1.4, y + .6), (x, y - hgt), (x + 1.4, y + .6)])


def _tower(cv, x, base, top, tw):
    """A gothic St. Johns tower: tapered, pointed spire, two lancet openings, shaded on the right."""
    hgt = base - top
    poly = [(x - tw / 2, base), (x - tw * .42, top + hgt * .14), (x - tw * .28, top + hgt * .06),
            (x, top), (x + tw * .28, top + hgt * .06), (x + tw * .42, top + hgt * .14), (x + tw / 2, base)]
    cv.obj([poly], .5)
    for l in hatch_poly(poly, 90, 1.5, x % 1.5):
        if l[0][0] > x - tw * .05 or int(round((l[0][0] - x) / 1.5)) % 2 == 0:
            cv.hair(l)
    cv.hair(hatch_poly(poly, 0, 3., base % 3))
    # lancets (sky through them shows dark)
    for (y0, y1) in ((top + hgt * .2, top + hgt * .45), (top + hgt * .52, top + hgt * .8)):
        aw = tw * .22
        lan = [(x - aw, y1), (x - aw, y0 + aw * 1.6), (x, y0), (x + aw, y0 + aw * 1.6), (x + aw, y1)]
        cv.obj([lan], .5)
        cv.line(hatch_poly(lan, 0, .8))
    cv.heavy([(x - tw * .5, base - hgt * .9 * .0 - 0), (x + tw * .5, base)])


def _bridge(cv, fx, fw, yh, fh, ytop, centre_gap):
    """The St. Johns Bridge: two gothic towers, the main cables sweeping down between them, the
    suspenders, the deck with its truss, and the piers into the river."""
    deck = yh - fh * .02
    tw = max(4.5, fw * .045)
    xs = (fx + fw * .13, fx + fw * .87)
    ttop = ytop
    cv.obj([], 0)
    # cables: main span between the towers, side spans out to the field edge
    ct = ttop + (deck - ttop) * .12
    span = xs[1] - xs[0]
    main = []
    for i in range(41):
        t = i / 40
        main.append((xs[0] + span * t, ct + (deck - 2 - ct) * (1 - (2 * t - 1) ** 2)))
    cv.line(main)
    sides = []
    for x0, x1 in ((xs[0], fx - 4), (xs[1], fx + fw + 4)):
        pts = []
        for i in range(13):
            t = i / 12
            pts.append((x0 + (x1 - x0) * t, ct + (deck - 1 - ct) * (t ** .8)))
        cv.line(pts)
        sides.append(pts)
    # suspenders
    for i in range(1, 40):
        x, y = main[i]
        if i % 1 == 0 and abs(x - (xs[0] + xs[1]) / 2) > 0:
            cv.hair([(x, y + .6), (x, deck)])
    for pts in sides:
        for x, y in pts[1:-1]:
            cv.hair([(x, y + .6), (x, deck)])
    # deck with a truss under it
    dh = max(2.2, fh * .025)
    dk = [(fx - 4, deck), (fx + fw + 4, deck), (fx + fw + 4, deck + dh), (fx - 4, deck + dh)]
    cv.obj([dk], .5)
    x = fx - 4
    while x < fx + fw + 4:
        cv.hair([(x, deck + dh), (x + dh, deck)])
        x += dh * 1.5
    cv.line([(fx - 4, deck), (fx + fw + 4, deck)])
    for x in xs:
        _tower(cv, x, deck + dh, ttop, tw)
        pier = [(x - tw * .65, deck + dh), (x + tw * .65, deck + dh), (x + tw * .75, yh + fh * .06), (x - tw * .75, yh + fh * .06)]
        cv.obj([pier], .5)
        cv.hair(hatch_poly(pier, 0, 1.5, .75))
    return deck


def _river(cv, fx, fw, y0, y1, rng, moonx=None):
    cv.obj([], 0)
    y = y0 + .75
    while y < y1:
        t = (y - y0) / max(1., y1 - y0)
        pitch = 1.5 if t < .25 else 2.
        x = fx - 2
        while x < fx + fw + 2:
            seg = rng.uniform(6, 26) * (1 + t)
            gap = rng.uniform(1.2, 3.5)
            if moonx is not None and abs(x - moonx) < 6 + t * 10:
                gap += 2.5
                seg *= .35
            cv.hair([(x, y), (min(x + seg, fx + fw + 2), y)])
            x += seg + gap
        y += pitch


def _bar(cv, fx, fw, yt, yb, rng):
    """The bar top: a long oak plank, grain running along it, knots, a dark front edge."""
    poly = [(fx - 3, yt), (fx + fw + 3, yt), (fx + fw + 3, yb + 3), (fx - 3, yb + 3)]
    cv.obj([poly], 1.)
    y = yt + 1.2
    ph = rng.uniform(0, 6)
    i = 0
    while y < yb + 2:
        pts = []
        amp = .6 + .4 * math.sin(i * 1.7 + ph)
        for k in range(0, 61):
            x = fx - 3 + (fw + 6) * k / 60
            pts.append((x, y + amp * math.sin(x * .07 + i * .9 + ph)))
        cv.hair(pts)
        y += 1.5 if (i % 5) in (0, 1) else 2.
        i += 1
    for kx in (rng.uniform(.1, .3), rng.uniform(.65, .9)):
        x = fx + fw * kx
        yy = yt + (yb - yt) * rng.uniform(.4, .7)
        for r in (1.2, 2.4, 3.6):
            cv.hair(_ell_pts(x, yy, r * 2.4, r * .7, 18) + [_ell_pts(x, yy, r * 2.4, r * .7, 18)[0]])
    cv.heavy([(fx - 3, yt), (fx + fw + 3, yt)])


def _cast_shadow(cv, cx, by, hw, lean=1.):
    sh = _ell_pts(cx + hw * .9 * lean, by + hw * .08, hw * 1.25, hw * .2, 24)
    cv.obj([sh], 0)
    cv.line(hatch_poly(sh, 0, 1.5, by % 1.5))


def _monogram(cv, cx, cy, size, weight=1.):
    """A "P" in a double ring."""
    tw = text_width("P", size)
    ls = text_lines("P", cx - tw / 2, cy - size / 2, size)
    if weight >= 1:
        cv.line(ls)
    else:
        cv.hair(ls)


def _barrel(cv, bx, base, H, R, rng, brand=True):
    """An oak cask standing on end: bulged staves shaded along their curve, iron hoops, and a
    head of boards branded with a tiny P."""
    top = base - H
    ery = R * .24

    def rad(y):
        t = (y - top) / H
        return R * (.86 + .14 * math.sin(PI * t))

    n = 30
    left = [(bx - rad(top + H * i / n), top + H * i / n) for i in range(n + 1)]
    right = [(bx + rad(top + H * i / n), top + H * i / n) for i in range(n, -1, -1)]
    rb = rad(base)
    bot = [(bx - rb * math.cos(PI * i / 16), base + ery * math.sin(PI * i / 16)) for i in range(1, 16)]
    rt = rad(top)
    topb = [(bx + rt * math.cos(PI * i / 16), top - ery * math.sin(PI * i / 16)) for i in range(1, 16)]
    poly = left + bot + right + topb
    _cast_shadow(cv, bx, base, rb)
    cv.obj([poly], 1.)
    # staves and shading lines: constant spacing across, curving with the bulge
    pitch = 1.5
    k0 = int(R / pitch)
    for k in range(-k0, k0 + 1):
        s = k * pitch / R
        if abs(s) >= .985:
            continue
        joint = (k % 4 == 0)
        if s > .3:
            keep = True
        elif s > -.1:
            keep = k % 2 == 0
        elif s > -.55:
            keep = joint
        else:
            keep = k % 2 == 0
        if not keep:
            continue
        pts = []
        for i in range(n + 1):
            y = top + H * i / n
            pts.append((bx + s * rad(y), y + ery * math.sqrt(1 - s * s) * (1 if y > top + H * .5 else 1) * 0))
        # follow the top and bottom ellipses
        pts[0] = (pts[0][0], top + ery * math.sqrt(1 - s * s))
        pts[-1] = (pts[-1][0], base + ery * math.sqrt(1 - s * s))
        cv.hair(pts)
    # cross hatch on the shadow side, following the hoops' curve
    yy = top + 3
    while yy < base:
        arc = []
        for i in range(0, 21):
            s = .45 + .53 * i / 20
            arc.append((bx + s * rad(yy), yy + ery * math.sqrt(1 - s * s)))
        cv.hair(arc)
        yy += 2.
    cv.heavy([(bx + rad(top + H * i / n) - .6, top + H * i / n) for i in range(2, n - 1)])
    # hoops
    for t in (.1, .3, .7, .9):
        y = top + H * t
        hb = max(2.2, H * .045)
        ra, rb2 = rad(y), rad(y + hb)
        up = [(bx + ra * math.cos(PI * i / 20), y + ery * math.sin(PI * i / 20)) for i in range(21)]
        lo = [(bx + rb2 * math.cos(PI * i / 20), y + hb + ery * math.sin(PI * i / 20)) for i in range(20, -1, -1)]
        band = [(x - 0.0, yy2) for x, yy2 in up] + lo
        band = [(bx + (p[0] - bx) * 1.02, p[1]) for p in band]
        cv.obj([band], 1.)
        for f in (.35, .7):
            cv.hair([(bx + (ra + (rb2 - ra) * f) * 1.02 * math.cos(PI * i / 20),
                      y + hb * f + ery * math.sin(PI * i / 20)) for i in range(0, 9)])
        cv.line([(bx + (ra + (rb2 - ra) * .5) * 1.02 * math.cos(PI * i / 20),
                  y + hb * .5 + ery * math.sin(PI * i / 20)) for i in range(0, 4)])
        # rivets
        for s in (-.6, .1):
            px = bx + s * ra
            cv.line([(px, y + hb * .5 + ery * math.sqrt(1 - s * s)), (px + .3, y + hb * .5 + ery * math.sqrt(1 - s * s))])
    # head: boards across, chime ring, bung, brand
    head = _ell_pts(bx, top, rt, ery, 40)
    cv.obj([head], 1.)
    inner = _ell_pts(bx, top, rt * .86, ery * .78, 40)
    cv.hair(inner + [inner[0]])
    for l in hatch_poly(inner, 0, 2., top % 2):
        cv.hair(l)
    cv.hair(hatch_poly(_ell_pts(bx, top, rt * .86, ery * .78, 40), 90, rt * .86 * 2 / 5))
    if brand and R > 9:
        # the cooper's brand: a ring with Parker's crossed drumsticks
        sz = min(ery * 1.2, 6.5)
        mx, my = bx + rt * .4, top - ery * .02
        cv.obj([_ell_pts(mx, my, sz * .95, sz * .7, 20)], .5)
        for sgn in (-1, 1):
            a = math.radians(90 + sgn * 38)
            x0, y0 = mx - math.cos(a) * sz * .85, my + math.sin(a) * sz * .6
            x1, y1 = mx + math.cos(a) * sz * .85, my - math.sin(a) * sz * .6
            cv.line([(x0, y0), (x1, y1)])
            cv.line([(x1 - .3, y1), (x1 + .3, y1)])
    # bung on the near stave
    cv.obj([_ell_pts(bx - R * .25, top + H * .5, max(1.2, R * .09), max(.8, R * .06), 12)], 1.)


def _bourbon(cv, cx, base, H, rng, mono=True):
    """A tall bourbon bottle: dark amber glass, cork and wax, a label with a P monogram."""
    bw = H * .155
    nw = H * .052
    top = base - H
    segs = [(top, nw * 1.18), (top + H * .07, nw * 1.18), (top + H * .075, nw), (top + H * .30, nw * 1.02),
            (top + H * .34, nw * 1.25), (top + H * .40, bw * .78), (top + H * .44, bw * .97), (top + H * .47, bw),
            (base, bw)]
    poly = _profile(cx, segs, base, .2)
    _cast_shadow(cv, cx, base, bw)
    cv.obj([poly], 1.)
    body = [p for p in poly if p[1] >= top + H * .335]
    _cyl_hatch(cv, poly, cx, bw, 1.5)
    for l in hatch_poly(poly, 0, 2., base % 2):
        (x0, y), (x1, _) = l
        for a, b in ((x0, cx - bw * .52), (cx - bw * .1, x1)):
            if b - a > 1:
                cv.hair([(a, y), (b, y)])
    # wax over the cork, dripping
    wax = [(cx - nw * 1.25, top + H * .1), (cx - nw * 1.25, top - 1), (cx + nw * 1.25, top - 1),
           (cx + nw * 1.25, top + H * .12), (cx + nw * .7, top + H * .1), (cx + nw * .4, top + H * .16),
           (cx, top + H * .1), (cx - nw * .6, top + H * .13)]
    cv.obj([wax], 1.)
    for l in hatch_poly(wax, 90, 1.5, cx % 1.5):
        if l[0][0] > cx - nw * .5:
            cv.line(l) if l[0][0] > cx + nw * .4 else cv.hair(l)
    # label
    l0, l1 = top + H * .55, top + H * .88
    lw = bw * .985
    e = .2 * bw
    lab = ([(cx - lw * math.cos(PI * i / 16), l1 + e * math.sin(PI * i / 16)) for i in range(17)] +
           [(cx + lw * math.cos(PI * i / 16), l0 + e * math.sin(PI * i / 16)) for i in range(17)][::-1][::-1])
    lab = ([(cx - lw * math.cos(PI * i / 16), l1 + e * math.sin(PI * i / 16)) for i in range(17)] +
           [(cx + lw * math.cos(PI * i / 16), l0 + e * math.sin(PI * i / 16)) for i in range(17)])
    cv.obj([lab], 1.)

    def band(y, s0=-.92, s1=.92):
        return [(cx + lw * (s0 + (s1 - s0) * i / 16), y + e * math.sqrt(max(0., 1 - (s0 + (s1 - s0) * i / 16) ** 2))) for i in range(17)]
    cv.hair(band(l0 + 1.5))
    cv.hair(band(l1 - 1.5))
    # monogram medallion in the upper label, ruled "lettering" below
    my = l0 + (l1 - l0) * .36
    msz = min((l1 - l0) * .42, bw * .8)
    if mono:
        ring = _ell_pts(cx, my + e * .8, msz * .62, msz * .55, 24)
        cv.hair(ring + [ring[0]])
        _monogram(cv, cx, my + e * .8, msz * .62, 1. if msz > 7 else .5)
    for f, wd, wt in ((.66, .7, 1), (.74, .5, 0), (.81, .62, 1), (.88, .4, 0)):
        (cv.line if wt else cv.hair)(band(l0 + (l1 - l0) * f, -wd, wd))
    if mono:
        for f in (.2, .52):
            cv.hair(band(l0 + (l1 - l0) * f, -.85, -.42))
            cv.hair(band(l0 + (l1 - l0) * f, .42, .85))
    for l in hatch_poly(lab, 90, 1.5, cx % 1.5):
        s = (l[0][0] - cx) / lw
        if s > .55 or (s > .3 and int(round((l[0][0] - cx) / 1.5)) % 2 == 0):
            cv.hair(l)
    return bw


def _tequila(cv, cx, base, H, rng):
    """A squat tequila bottle: clear glass, short neck and a wooden-topped stopper, the liquid line,
    an agave on the label."""
    bw = H * .27
    nw = H * .075
    top = base - H
    segs = [(top + H * .14, nw * 1.05), (top + H * .27, nw), (top + H * .32, nw * 1.35), (top + H * .36, bw * .9),
            (top + H * .4, bw), (base, bw)]
    poly = _profile(cx, segs, base, .2)
    _cast_shadow(cv, cx, base, bw)
    cv.obj([poly], 1.)
    liq = top + H * .43
    glass = [p for p in poly]
    # clear glass: thick edges, faint body, liquid ruled horizontally below its line
    _cyl_hatch(cv, poly, cx, bw, 3., glass=True, cross=False)
    lq = [(cx - bw + 1, liq), (cx + bw - 1, liq)] + [(cx + (bw - 1) * math.cos(PI * i / 16), base - 1 + .2 * bw * math.sin(PI * i / 16)) for i in range(17)]
    lq = [(cx - bw + 1, liq + .2 * bw * 0)] + [(cx - (bw - 1) * math.cos(PI * i / 16), liq + .14 * bw * math.sin(PI * i / 16)) for i in range(17)][::-1][:0]
    lq = ([(cx - (bw - 1) * math.cos(PI * i / 16), liq + .12 * bw * math.sin(PI * i / 16)) for i in range(17)] +
          [(cx + (bw - 1) * math.cos(PI * i / 16), base - 1 + .2 * bw * math.sin(PI * i / 16)) for i in range(17)])
    cv.hair(hatch_poly(lq, 0, 3., liq % 3))
    cv.hair(_ell_pts(cx, liq, bw - 1, .12 * bw, 24) + [_ell_pts(cx, liq, bw - 1, .12 * bw, 24)[0]])
    # stopper: wooden cap
    cap = [(cx - nw * 1.5, top + H * .15), (cx - nw * 1.5, top + H * .02), (cx - nw * 1.2, top),
           (cx + nw * 1.2, top), (cx + nw * 1.5, top + H * .02), (cx + nw * 1.5, top + H * .15)]
    cv.obj([cap], 1.)
    for l in hatch_poly(cap, 90, 1.5, cx % 1.5):
        if l[0][0] > cx - nw * .3:
            cv.hair(l)
    cv.hair(hatch_poly(cap, 0, 3.))
    # label: a lozenge with an agave
    l0, l1 = top + H * .55, top + H * .9
    lw = bw * .78
    e = .2 * bw
    lab = ([(cx - lw * math.cos(PI * i / 16), l1 + e * .8 * math.sin(PI * i / 16)) for i in range(17)] +
           [(cx + lw * math.cos(PI * i / 16), l0 + e * .8 * math.sin(PI * i / 16)) for i in range(17)])
    cv.obj([lab], 1.)
    ay = l1 - (l1 - l0) * .22
    ah = (l1 - l0) * .6
    for i in range(7):
        a = -PI / 2 + (i - 3) * .32
        ln = ah * (1 - abs(i - 3) * .12)
        bx, by = cx + ln * math.cos(a), ay + ln * math.sin(a)
        cv.line([(cx + (i - 3) * .4, ay), (bx, by)])
    cv.hair([(cx - lw * .7, ay + 1), (cx + lw * .7, ay + 1)])
    for f, wd in ((.86, .5), (.93, .3)):
        yy = l0 + (l1 - l0) * f
        cv.line([(cx - lw * wd, yy + e * .5), (cx + lw * wd, yy + e * .5)])
    for f in (.12,):
        yy = l0 + (l1 - l0) * f + e * .8
        cv.hair([(cx - lw * .6, yy), (cx + lw * .6, yy)])
    for l in hatch_poly(lab, 90, 1.5, cx % 1.5):
        s = (l[0][0] - cx) / lw
        if s > .55:
            cv.hair(l)
    return bw


def _rocks(cv, cx, base, H, rng):
    """A rocks glass: whiskey ruled dark, ice cubes standing proud, faceted foot."""
    bw = H * .48
    tw_ = H * .55
    top = base - H
    e = .18
    poly = ([(cx - tw_, top), (cx - bw, base)] +
            [(cx - bw * math.cos(PI * i / 16), base + e * bw * math.sin(PI * i / 16)) for i in range(1, 16)] +
            [(cx + bw, base), (cx + tw_, top)] +
            [(cx + tw_ * math.cos(PI * i / 16), top - e * tw_ * math.sin(PI * i / 16)) for i in range(1, 16)])
    _cast_shadow(cv, cx, base, bw, .9)
    cv.obj([poly], 1.)
    lq = top + H * .42
    lwq = bw + (tw_ - bw) * (base - lq) / H
    liquid = ([(cx - lwq * math.cos(PI * i / 16), lq + e * lwq * math.sin(PI * i / 16)) for i in range(17)] +
              [(cx + bw * math.cos(PI * i / 16), base - H * .14 + e * bw * math.sin(PI * i / 16)) for i in range(17)])
    for l in hatch_poly(liquid, 0, 1.5, lq % 1.5):
        cv.hair(l)
    cv.hair(hatch_poly(liquid, 90, 1.5, cx % 1.5 + .75))
    # thick base
    cv.line([(cx - bw * math.cos(PI * i / 16), base - H * .14 + e * bw * math.sin(PI * i / 16)) for i in range(17)])
    # facets
    for f in (-.75, -.35, .35, .75):
        cv.hair([(cx + f * tw_, top + e * tw_ * math.sqrt(1 - f * f) * .9), (cx + f * bw, base + e * bw * math.sqrt(1 - f * f) * .9)])
    cv.line([(cx + tw_ - .8, top + 1), (cx + bw - .8, base)])
    # ice
    for dx, dy, s, rot in ((-.2, -.05, .36, .3), (.25, .02, .32, -.4)):
        x, y = cx + dx * tw_, lq + dy * H
        r = s * H
        cube = [(x + r * math.cos(rot + PI / 2 * k + .2) * (1 if k % 2 else .8),
                 y + r * .8 * math.sin(rot + PI / 2 * k + .2)) for k in range(4)]
        cv.obj([cube], 1.)
        cv.hair(hatch_poly(cube, 30 + rot * 50, 3.))
        cv.hair([cube[0], ((cube[0][0] + cube[2][0]) / 2, (cube[0][1] + cube[2][1]) / 2)])
    rim = _ell_pts(cx, top, tw_, e * tw_, 32)
    cv.obj([], 0)
    cv.line(rim + [rim[0]])


def _agave(cv, bx, by, size, side, rng):
    """A blue agave: stiff, keeled blades fanning from a rosette, toothed edges and a terminal
    spine; each blade shaded along its length, dark under the keel."""
    n = 7
    for i in sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2)):
        t = (i - (n - 1) / 2) / ((n - 1) / 2)
        a = -PI / 2 + t * 1.25 + side * .12
        L = size * (1 - .35 * abs(t)) * rng.uniform(.9, 1.05)
        wd = size * .085
        bend = t * .35
        spine = []
        for k in range(21):
            u = k / 20
            aa = a + bend * u * u
            spine.append((bx + math.cos(a) * L * u + math.cos(aa) * 0, by + math.sin(a) * L * u + L * .25 * bend * u * u * abs(math.sin(a)) * 0 + (L * .18 * u * u if abs(t) > .4 else 0)))
        # blade outline: width tapers to a spine
        lft, rgt = [], []
        for k, (x, y) in enumerate(spine):
            u = k / 20
            if k < 20:
                dx, dy = spine[k + 1][0] - x, spine[k + 1][1] - y
            dl = math.hypot(dx, dy) or 1
            nx, ny = -dy / dl, dx / dl
            ww = wd * (1 - u) ** .9 * (1 + .3 * math.sin(u * PI))
            tooth = .9 if (k % 2 == 1 and 2 < k < 18) else 0.
            lft.append((x + nx * (ww + tooth), y + ny * (ww + tooth)))
            rgt.append((x - nx * (ww + tooth * .6), y - ny * (ww + tooth * .6)))
        blade = lft + rgt[::-1]
        cv.obj([blade], 1.)
        cv.line(spine[:-1])
        # shade one half densely along the blade
        dark = rgt if (t > 0) else lft
        half = spine + dark[::-1]
        cv.hair(hatch_poly(half, math.degrees(a) + 90 * 0, 1.5))
        light = lft if t > 0 else rgt
        hl = spine[:12] + light[:12][::-1]
        cv.hair(hatch_poly(hl, math.degrees(a) + 35, 3.))
        cv.heavy(dark[1:-3])
        cv.hair([spine[-1], (spine[-1][0] + math.cos(a) * 2.5, spine[-1][1] + math.sin(a) * 2.5)])


# ------------------------------------------------------------------------------------------------
# the scene, fitted to the field (fx, fy, fw, fh)
# ------------------------------------------------------------------------------------------------
def scene(fx, fy, fw, fh, ctx, seed, small=False):
    rng = random.Random(seed)
    cv = Canvas()
    horizon = fy + fh * (.52 if not small else .5)
    bar_y = fy + fh * (.74 if not small else .7)
    S = min(fh * .66, fw * .44)  # bourbon height
    phase = _moon_phase((ctx or {}).get("date", ""))
    mr = max(3.2, min(9., min(fw, fh) * .055))
    mx, my = fx + fw * .74, fy + fh * .15 + mr
    moon = (mx, my, mr) if not small else None
    _sky(cv, fx, fy, fw, fh, horizon, rng, moon)
    if moon:
        _moon(cv, mx, my, mr, phase)
    if not small:
        _hills(cv, fx, fw, horizon, fh, rng)
        _bridge(cv, fx, fw, horizon, fh, fy + fh * .1, 0)
    _river(cv, fx, fw, horizon + 1, bar_y, rng, mx if moon else None)
    _bar(cv, fx, fw, bar_y, fy + fh, rng)
    yb = bar_y + (fy + fh - bar_y) * .32
    if small:
        _bourbon(cv, fx + fw * .4, yb, S * 1.12, rng, True)
        _rocks(cv, fx + fw * .66, yb + (fy + fh - yb) * .25, S * .32, rng)
        return cv.svg()
    side = fw > fh * 1.35
    _barrel(cv, fx + fw * (.2 if side else .22), yb - 1, S * .6, S * .23, rng)
    _agave(cv, fx + fw * .1, fy + fh, S * .62, 1, rng)
    _bourbon(cv, fx + fw * .44, yb, S, rng, True)
    _tequila(cv, fx + fw * .66, yb + 1, S * .72, rng)
    _rocks(cv, fx + fw * .55, yb + (fy + fh - yb) * .45, S * .26, rng)
    _agave(cv, fx + fw * .9, fy + fh, S * .7, -1, rng)
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# frame layouts (adapted from engraving_codex: the vignette fills the whole field, lettering on the
# banner and the pedestal's tablet, and a light ruled ground under everything so no paper is bare)
# ------------------------------------------------------------------------------------------------
def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _cartouche_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
         (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def _roman(n):
    s = ""
    for v, r in ROMAN:
        while n >= v:
            s += r
            n -= v
    return s


def _date_words(ctx):
    try:
        d = datetime.date.fromisoformat((ctx or {}).get("date", "")[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    return MONTHS[d.month - 1], _roman(d.year)


def _banner_letters(centre, h, words):
    """Letter the banner face along its centre line."""
    size = min(h * .5, 7.5)
    L = [0.]
    for (x0, y0), (x1, y1) in zip(centre, centre[1:]):
        L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
    tot = L[-1]
    tw = text_width(words, size)
    while tw > tot * .86 and size > 3:
        size *= .92
        tw = text_width(words, size)
    s0 = (tot - tw) / 2

    def at(s):
        for i in range(1, len(L)):
            if L[i] >= s:
                f = (s - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
                (x0, y0), (x1, y1) = centre[i - 1], centre[i]
                ang = math.atan2(y1 - y0, x1 - x0)
                return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, ang
        x, y = centre[-1]
        return x, y, 0.

    def tf(px, py):
        x, y, a = at(s0 + px)
        dy = py - size / 2
        return x - math.sin(a) * dy, y + math.cos(a) * dy

    lines = text_lines(words, 0, 0, size, tf)
    return f'<path d="{_pd(lines)}" stroke="#000" stroke-width="1" fill="none"/>'


def _tablet(tx, ty, tw, th, words):
    o = [f'<path d="M{_n(tx + 2.5)},{_n(ty + 2.5)}h{_n(tw - 4)}v{_n(th - 4)}h{_n(-tw + 4)}z" fill="{pat("L")}" stroke="none"/>']
    size = min(th * .55, 9.)
    w = text_width(words, size)
    while w > tw * .9:
        size *= .92
        w = text_width(words, size)
    x, y = tx + (tw - w) / 2, ty + (th - size) / 2 + .5
    lines = text_lines(words, x, y, size)
    # a white knock-out under the letters so they read on the ruled tablet
    o.append(f'<path d="M{_n(x - 2)},{_n(y - 1.5)}h{_n(w + 4)}v{_n(size + 3)}h{_n(-w - 4)}z" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_pd(lines)}" stroke="#000" stroke-width="{1 if size > 5 else .5}" fill="none"/>')
    return "".join(o)


def _layout_band(w, h, seed, ctx):
    o = [C.dark_ground((0, 0, w, h), "L")]
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(_clip(_uid("b4", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o.append(_field_clip(_uid("bf", w, h, seed), fd, scene(cx - rx, cy - ry, 2 * rx, 2 * ry, ctx, seed, True)))
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = [C.dark_ground((0, 0, w, h), "L")]
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
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .065), rmax=r * .8,
                   max_n=int(12 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("m4", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _cartouche_field(cx, cy, cw, gh + 4)
    o.append(_field_clip(_uid("mf", w, h, seed), fd, scene(fx, fy, fw, fh, ctx, seed, fh < 70)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = [C.dark_ground((0, 0, w, h), "L")]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = min(pw * .56, ph * 1.4), ph * .66
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .18, ph * .25, (pw - cw) * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21, (pw - cw) * .17)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .035), rmax=r1 * .9,
                   max_n=int(14 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("t4", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, fd = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = _cartouche_field(cx, cy, cw, ch)
    o.append(_field_clip(_uid("tf", w, h, seed), fd, scene(fx, fy, fw, fh, ctx, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, max(11., ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_letters(centre, bh, "NEW AT ST JOHNS"))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    mon, yr = _date_words(ctx)
    o.append(_tablet(tx, ty, tw, th, f"SPIRITS * {mon} {yr}"))
    fy2 = py + ped_h
    fh2 = h - fy2
    if fh2 > 14:
        o.append(C.dark_ground((w * .06, fy2, w * .88, fh2 - 2), "G"))
        o.append(_clip(_uid("f4", w, h, seed), w * .06, fy2, w * .88, fh2 - 2,
                       C.scroll_band(w * .06, fy2, w * .88, fh2 - 2, rng.randrange(1 << 20), fh2 * 1.2,
                                     r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy2 + 1, fh2 * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 404
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
