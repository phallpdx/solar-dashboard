"""nearby-04 "Planes overhead": an Alaska Airlines 737 climbing out over the Columbia and Sauvie
Island, contrail behind, Mt. Hood on the horizon and a Hillsboro Cessna far off, carved inside the
house Codex frame. The 737's fin carries the Alaska face in a fur ruff (the Codex's carved face,
re-cast for the page). The pedestal tablet is a flight strip carrying one little plane per aircraft
the page lists today; the ribbon is a runway. Easter egg: a great blue heron from Sauvie Island
flying low over the river, under the jet."""
import sys
import math
import random
import re
import engraving_codex as C
from engraving_codex import (Canvas, hatch_poly, _ell_pts, _d, _n, _Rib, _fill_lines, _shadow,
                             _superellipse, _volute, _pair_unit, fill_scrolls, cartouche, palmette,
                             ribbon_banner, pedestal, knurled_bar, egg_and_dart, bead_moulding,
                             dark_ground, scroll_band, _clip, _uid, _medallion, _CR, pat, svg_doc)

PI = math.pi


# ------------------------------------------------------------------------------------------------
# geometry helpers
# ------------------------------------------------------------------------------------------------

def _xf(pts, ox, oy, s, ang):
    c, si = math.cos(ang), math.sin(ang)
    return [(ox + s * (x * c - y * si), oy + s * (x * si + y * c)) for x, y in pts]


def _clip_path(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _blk(polys):
    d = "".join(_d(p, True, 0) for p in polys if len(p) > 2)
    return f'<path d="{d}" fill="#000" stroke="none"/>' if d else ""


# ------------------------------------------------------------------------------------------------
# the 737 (local frame: tail at x=0, nose at x=1, y down; then rotated / scaled)
# ------------------------------------------------------------------------------------------------

def _fus_half(x):
    if x < .26:
        return .016 + .040 * (x / .26) ** .8
    if x < .86:
        return .056
    t = (x - .86) / .14
    return .056 * math.sqrt(max(0., 1 - t ** 2.2))


def _fus_y(x):
    return -.034 * max(0., 1 - x / .27) ** 2


def plane_737(cv, ox, oy, L, ang, detail=2, extra=None):
    """Draw the jet into cv. (ox, oy) is the tail, L the fuselage length, ang its climb heading.
    detail 0 tiny / 1 medium / 2 full. extra: list collecting black polygons (cockpit, intake)."""
    X = lambda pts: _xf(pts, ox, oy, L, ang)
    lw = 1. if detail else .5
    # far wing (behind the fuselage, seen from above, foreshortened)
    fw = X([(.60, -.03), (.40, -.215), (.345, -.215), (.44, -.03)])
    cv.obj([fw], lw)
    if detail:
        cv.hair(hatch_poly(fw, math.degrees(ang) + 62, 3 if detail < 2 else 2))
    # far stabiliser
    fs = X([(.16, -.02), (.06, -.11), (.025, -.11), (.07, -.02)])
    cv.obj([fs], lw)
    if detail:
        cv.hair(hatch_poly(fs, math.degrees(ang) + 62, 2))
    # fin
    fin = X([(.25, -.045), (.085, -.28), (.02, -.28), (.035, -.04)])
    cv.obj([fin], lw)
    if detail:
        cv.hair(hatch_poly(fin, math.degrees(ang) + 90 - 0, 1.5 if detail == 2 else 2))
    # fuselage as a rib (normal +1 = belly)
    n = 60
    cen = [(i / n, _fus_y(i / n)) for i in range(n + 1)]
    hw = [_fus_half(i / n) for i in range(n + 1)]
    cpts = X(cen)
    R = _Rib(cpts, [max(.05, h * L) for h in hw], [max(.05, h * L) for h in hw])
    cv.obj([R.outline()], lw)
    if detail:
        hw_px = .056 * L
        k = max(1, int(hw_px / 1.6))
        for j in range(k):
            cv.hair(R.contour(.15 + .85 * (j + .5) / k, .03, .97))
        _shadow(cv, R, 1, max(.7, hw_px * .3), .05, .92)
        # top highlight line + cheat line (livery stripe)
        cv.hair(R.contour(-.55, .1, .95))
        if detail == 2:
            cv.line(R.contour(.12, .22, .93))
    else:
        cv.hair(R.contour(.5, .05, .95))
    # Alaska face on the fin: a fur ruff round a face
    if detail == 2:
        fc = X([(.085, -.165)])[0]
        rr = L * .052
        ruff = _ell_pts(fc[0], fc[1], rr, rr * 1.08, 30)[:-1]
        cv.obj([ruff], 1.)
        for i in range(30):
            a = 2 * PI * i / 30
            r0, r1 = rr * .6, rr * (.95 if i % 2 else .82)
            cv.hair([(fc[0] + r0 * math.cos(a), fc[1] + r0 * 1.08 * math.sin(a)),
                     (fc[0] + r1 * math.cos(a + .12), fc[1] + r1 * 1.08 * math.sin(a + .12))])
        face = _ell_pts(fc[0], fc[1] + rr * .05, rr * .5, rr * .6, 20)[:-1]
        cv.obj([face], .5)
        e = rr * .2
        cv.line([[(fc[0] - e * 1.2, fc[1] - e * .3), (fc[0] - e * .3, fc[1] - e * .2)],
                 [(fc[0] + e * .3, fc[1] - e * .2), (fc[0] + e * 1.2, fc[1] - e * .3)]])
        cv.hair([(fc[0] - e, fc[1] + e * 1.2), (fc[0], fc[1] + e * 1.5), (fc[0] + e, fc[1] + e * 1.2)])
        cv.hair([(fc[0], fc[1] - e * .1), (fc[0] + e * .25, fc[1] + e * .6)])
    # near stabiliser
    ns = X([(.17, .01), (.035, .125), (-.005, .125), (.065, .012)])
    cv.obj([ns], lw)
    if detail:
        cv.hair(hatch_poly(ns, math.degrees(ang) + 35, 1.5 if detail == 2 else 2))
    # near wing (underside, swept back) with winglet
    nw = X([(.63, .035), (.37, .27), (.315, .28), (.44, .045)])
    cv.obj([nw], lw)
    if detail:
        cv.hair(hatch_poly(nw, math.degrees(ang) + 48, 1.5 if detail == 2 else 2))
        # flap-track fairings
        for t in (.3, .55, .78):
            a = (.44 + (.315 - .44) * t, .045 + (.28 - .045) * t)
            b = (a[0] + .045, a[1] + .012)
            cv.line(X([a, b]))
        wl = X([(.32, .28), (.30, .335), (.335, .33), (.37, .27)])
        cv.obj([wl], lw)
        cv.hair(hatch_poly(wl, math.degrees(ang) + 90, 1.5))
    # engine nacelle under the near wing
    eng_c = X([(.585, .125)])[0]
    erx, ery = L * .085, L * .042
    eng = [(eng_c[0] + erx * math.cos(t) * math.cos(ang) - ery * math.sin(t) * math.sin(ang),
            eng_c[1] + erx * math.cos(t) * math.sin(ang) + ery * math.sin(t) * math.cos(ang))
           for t in [2 * PI * i / 32 for i in range(32)]]
    pylon = X([(.6, .05), (.53, .1), (.59, .11), (.625, .055)])
    cv.obj([pylon], lw)
    cv.obj([eng], lw)
    if detail:
        cv.hair(hatch_poly(eng, math.degrees(ang), 1.5 if detail == 2 else 2))
        # intake lip: white front ring with a black hole
        ic = X([(.66, .125)])[0]
        ring = [(ic[0] + ery * .55 * math.cos(t) * math.cos(ang) - ery * math.sin(t) * math.sin(ang),
                 ic[1] + ery * .55 * math.cos(t) * math.sin(ang) + ery * math.sin(t) * math.cos(ang))
                for t in [2 * PI * i / 24 for i in range(24)]]
        cv.obj([ring], 1.)
        if extra is not None:
            hole = [(ic[0] + ery * .3 * math.cos(t) * math.cos(ang) - ery * .65 * math.sin(t) * math.sin(ang),
                     ic[1] + ery * .3 * math.cos(t) * math.sin(ang) + ery * .65 * math.sin(t) * math.cos(ang))
                    for t in [2 * PI * i / 18 for i in range(18)]]
            extra.append(hole)
    # windows and cockpit
    if detail == 2 and extra is not None:
        for i in range(22):
            x = .30 + i * .025
            if .55 < x < .58:
                continue
            p = X([(x, -.012)])[0]
            extra.append(_ell_pts(p[0], p[1], max(.55, L * .0045), max(.55, L * .0045), 6)[:-1])
        extra.append(X([(.905, -.03), (.955, -.026), (.948, -.01), (.9, -.012)]))
        d1 = X([(.29, -.03), (.30, .035)])
        cv.line([d1])
    if detail and extra is not None and detail < 2:
        extra.append(X([(.9, -.03), (.955, -.026), (.948, -.008), (.9, -.01)]))
    return X([(.0, .0)])[0]


def cessna(cv, cx, cy, s, ang=-.15):
    """A small high-wing trainer (Hillsboro Aero), side-on, s px long."""
    X = lambda pts: _xf(pts, cx, cy, s, ang)
    body = X([(-.5, -.04), (-.1, -.08), (.35, -.1), (.48, -.04), (.5, .04), (.3, .1), (-.1, .06), (-.5, .01)])
    fin = X([(-.5, -.03), (-.42, -.03), (-.36, -.07), (-.47, -.26), (-.52, -.26)])
    wing = X([(.0, -.13), (.33, -.13), (.33, -.09), (.0, -.09)])
    gear = X([(.12, .08), (.08, .2), (.16, .2)])
    cv.obj([fin], .5)
    cv.hair(hatch_poly(fin, 90, 1.5))
    cv.obj([body], .5)
    cv.hair(hatch_poly(body, 0, 1.5, .5))
    cv.obj([wing], .5)
    cv.hair([X([(.12, -.09), (.2, .02)])[0], X([(.12, -.09), (.2, .02)])[1]])
    cv.hair(X([(.1, .1), (.12, .2)]))


def heron(cv, cx, cy, s, flip=False):
    """Great blue heron in flight, side-on: neck folded back in an S, dagger bill, legs trailing
    straight, broad arched wings (far wing up, near wing on the down-stroke). s = body length px."""
    k = -1 if flip else 1
    X = lambda pts: [(cx + k * x * s, cy + y * s) for x, y in pts]
    far = X([(-.05, -.12), (.22, -.12), (.1, -.5), (-.2, -.78), (-.42, -.8), (-.3, -.5)])
    body = X([(-.42, .02), (-.15, -.12), (.22, -.13), (.4, -.05), (.3, .07), (-.1, .1)])
    neck = X([(.34, -.08), (.5, -.1), (.46, -.22), (.52, -.3), (.64, -.31), (1.0, -.27),
              (.64, -.24), (.58, -.2), (.6, -.08), (.38, .04)])
    near = X([(.0, -.06), (.28, -.07), (.2, .28), (-.05, .55), (-.32, .6), (-.22, .3)])
    cv.obj([far], .5)
    cv.hair(hatch_poly(far, 70, 1.5))
    cv.line(X([(-.35, .04), (-1.05, .13)]))
    cv.obj([body, neck], .5)
    cv.hair(hatch_poly(body, 0, 1.5, .5))
    cv.hair(X([(.5, -.29), (.62, -.31)]))
    cv.obj([near], .5)
    cv.line(hatch_poly(near, -65, 1.5))


# ------------------------------------------------------------------------------------------------
# the scene, fitted to any field
# ------------------------------------------------------------------------------------------------

def _cloud(cx, cy, w, h, rng):
    """A cumulus: the upper envelope of a few rounded heads on a flat base."""
    n = 4
    heads = []
    for i in range(n):
        f = (i + .5) / n
        heads.append((cx - w / 2 + w * f + rng.uniform(-1, 1) * w * .04, w / n * .75,
                      h * (.55 + .5 * math.sin(PI * f) ** .7) * rng.uniform(.85, 1.1)))
    top = []
    m = 40
    for i in range(m + 1):
        x = cx - w / 2 + w * i / m
        y = cy
        for hx, rx, ry in heads:
            t = (x - hx) / rx
            if abs(t) < 1:
                y = min(y, cy - ry * .25 - ry * math.sqrt(1 - t * t))
        top.append((x, y))
    return top


def scene(x0, y0, W, H, seed, nplanes=5):
    """Engrave the whole box x0,y0,W,H (the caller clips it to the field)."""
    rng = random.Random(seed)
    cv = Canvas()
    blk = []
    tiny = H < 40
    hz = y0 + H * (.68 if not tiny else .76)          # horizon
    bot = y0 + H + 2
    # sky: graded ruled lines, darkest at the zenith, lightening to the horizon
    bands = [(0, .26, 1.5), (.26, .6, 2.), (.6, 1.0, 3.)] if not tiny else [(0, .45, 1.5), (.45, 1., 2.)]
    cv.obj([], 0)
    for f0, f1, p in bands:
        ya, yb = y0 + (hz - y0) * f0 - .1, y0 + (hz - y0) * f1 + .1
        cv.hair(hatch_poly([(x0 - 2, ya), (x0 + W + 2, ya), (x0 + W + 2, yb), (x0 - 2, yb)], 0, p, .25))
    # clouds, white with shaded bellies
    if not tiny:
        for cxf, cyf, cwf, chf in ((.66, .15, .32, .09), (.2, .1, .2, .05)):
            ccx, ccy, cw, chh = x0 + W * cxf, y0 + H * cyf, W * cwf, H * chf
            pts = _cloud(ccx, ccy, cw, chh, rng)
            cv.obj([pts], .5)
            belly = [(ccx - cw / 2, ccy + .2), (ccx + cw / 2, ccy + .2), (ccx + cw * .42, ccy - chh * .45),
                     (ccx - cw * .42, ccy - chh * .45)]
            cv.hair(hatch_poly(belly, 0, 1.5, .4))
            cv.hair(hatch_poly(pts, 0, 3, 1.1, .8))
    # Mt. Hood, right of centre, snow above the treeline
    mx = x0 + W * (.8 if not tiny else .74)
    mh = H * (.27 if not tiny else .3)
    mw = W * .26
    top = hz - mh
    mtn = [(mx - mw, hz + 1), (mx - mw * .62, hz - mh * .28), (mx - mw * .3, hz - mh * .62),
           (mx - mw * .1, hz - mh * .93), (mx - mw * .02, hz - mh), (mx + mw * .05, hz - mh * .97),
           (mx + mw * .16, hz - mh * .8), (mx + mw * .45, hz - mh * .42), (mx + mw * .75, hz - mh * .18),
           (mx + mw * 1.05, hz + 1)]
    cv.obj([mtn], .5)
    east = [(mx - mw * .02, hz - mh), (mx + mw * .05, hz - mh * .97), (mx + mw * .16, hz - mh * .8),
            (mx + mw * .45, hz - mh * .42), (mx + mw * .75, hz - mh * .18), (mx + mw * 1.05, hz + 1),
            (mx + mw * .25, hz + 1), (mx + mw * .12, hz - mh * .45), (mx + mw * .04, hz - mh * .7)]
    cv.hair(hatch_poly(east, -58, 1.5))
    cv.hair(hatch_poly(mtn, 0, 3, 1.75, .6))
    # forest below the snowline
    fl = [(mx - mw, hz + 1)] + [(mx - mw + 2 * mw * .5 * i / 16 * 2, hz - mh * (.24 - .18 * abs(i / 16 - .5)) - rng.uniform(0, 1.2))
                                for i in range(17)] + [(mx + mw * 1.05, hz + 1)]
    cv.obj([fl], 0)
    cv.line(hatch_poly(fl, 70, 2))
    cv.hair(hatch_poly(fl, 0, 1.5))
    # foothills running off to the right
    hx1 = mx - mw * .5
    hills = [(x0 - 2, hz + 1)] + [(x0 - 2 + (hx1 - x0 + 2) * t / 24, hz - H * (.05 + .03 * math.sin(t * .7 + seed % 7)))
                                  for t in range(25)] + [(hx1, hz + 1)]
    cv.obj([hills], .5)
    cv.hair(hatch_poly(hills, 0, 1.5))
    # Sauvie Island lowland and the cottonwood bank
    river_y = hz + (y0 + H - hz) * .36
    land = [(x0 - 2, hz), (x0 + W + 2, hz), (x0 + W + 2, river_y + 1), (x0 - 2, river_y + 1)]
    cv.obj([land], .5)
    cv.hair(hatch_poly(land, 0, 2, .5))
    trees = [(x0 - 2, river_y + 1)]
    tx = x0 - 2
    th = (river_y - hz) * .7
    while tx < x0 + W + 2:
        r = rng.uniform(.6, 1.) * max(1.5, th * .55)
        trees += _ell_pts(tx + r, river_y - th * rng.uniform(.4, .75), r, r * .8, 9, PI, 2 * PI)
        tx += r * rng.uniform(1.4, 2.)
    trees += [(x0 + W + 2, river_y + 1)]
    cv.obj([trees], .5)
    cv.line(hatch_poly(trees, 90, 1.5))
    cv.hair(hatch_poly(trees, 0, 1.5))
    # the Columbia: broken ripples, opening out toward us
    water = [(x0 - 2, river_y + 1), (x0 + W + 2, river_y + 1), (x0 + W + 2, bot), (x0 - 2, bot)]
    cv.obj([water], 0)
    yy = river_y + 2
    row = 0
    while yy < bot:
        f = (yy - river_y) / max(8., bot - river_y)
        xx = x0 - 2 - rng.uniform(0, 6)
        while xx < x0 + W + 2:
            seg = rng.uniform(5, 13) * (1 + f)
            cv.hair([(xx, yy), (xx + seg, yy)])
            xx += seg + rng.uniform(1.5, 3.)
        yy += 1.5 if f < .5 else 2.
        row += 1
    # the Hillsboro Cessna far off, and the heron low over the river (Easter egg)
    if not tiny:
        cessna(cv, x0 + W * .24, y0 + H * .25, W * .12, -.05)
        heron(cv, x0 + W * .62, river_y + (bot - river_y) * .5, max(9., W * .13), False)
    # the jet, climbing out to the right
    L = W * (.7 if not tiny else .62)
    ang = -.30
    ox, oy = x0 + W * (.13 if not tiny else .19), y0 + H * (.53 if not tiny else .64)
    if tiny:
        L = min(L, H * 1.35)
    det = 2 if W >= 110 else (1 if W >= 60 else 0)
    plane_737(cv, ox, oy, L, ang, det, blk)
    return cv.svg() + _blk(blk)


# ------------------------------------------------------------------------------------------------
# frame furniture filled for this page
# ------------------------------------------------------------------------------------------------

def _mini_plane(cx, cy, s, ang=0.):
    """A top-view airliner glyph s px long (black polygon)."""
    pts = [(.5, 0), (.42, -.05), (.1, -.06), (-.05, -.48), (-.15, -.48), (-.08, -.06), (-.38, -.05), (-.48, -.2),
           (-.53, -.2), (-.5, 0)]
    full = pts + [(x, -y) for x, y in pts[::-1][1:-1]]
    return _xf(full, cx, cy, s, ang)


def flight_strip(tx, ty, tw, th, n):
    """Fill the pedestal tablet: a light-ruled strip with a dashed great-circle route and one
    plane per aircraft overhead today."""
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{pat("L")}" stroke="none"/>']
    cy = ty + th * .55
    pts = [(tx + 8 + (tw - 16) * i / 40, cy - th * .18 * math.sin(PI * i / 40)) for i in range(41)]
    o.append(f'<path d="{_d(pts)}" stroke="#000" stroke-width="1" stroke-dasharray="3 2.5" fill="none"/>')
    polys = []
    s = min(th * .75, 16)
    for i in range(n):
        u = (i + .5) / n
        k = int(u * 40)
        p = pts[k]
        a = math.atan2(pts[min(40, k + 1)][1] - pts[max(0, k - 1)][1], pts[min(40, k + 1)][0] - pts[max(0, k - 1)][0])
        r = s * .62
        polys.append(_ell_pts(p[0], p[1], r, r, 18)[:-1])
    o.append(f'<path d="{"".join(_d(p, True, 0) for p in polys)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    planes = [_mini_plane(pts[int((i + .5) / n * 40)][0], pts[int((i + .5) / n * 40)][1], s * .85, 0) for i in range(n)]
    o.append(_blk(planes))
    for ex in (tx + 5, tx + tw - 5):
        o.append(f'<path d="{_d(_ell_pts(ex, cy - .5, 2, 2, 10), True, 0)}" fill="#000"/>')
    return "".join(o)


def runway(centre, h):
    """Ribbon face as a runway: light ruled with a dashed centreline and threshold bars."""
    n = len(centre) - 1
    top, bot = [], []
    for i, p in enumerate(centre):
        a, b = centre[max(0, i - 1)], centre[min(n, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        top.append((p[0] - nx * (h / 2 - 1.6), p[1] - ny * (h / 2 - 1.6)))
        bot.append((p[0] + nx * (h / 2 - 1.6), p[1] + ny * (h / 2 - 1.6)))
    face = top + bot[::-1]
    o = [f'<path d="{_d(face, True, 0)}" fill="{pat("L")}" stroke="none"/>']
    o.append(f'<path d="{_d(centre[4:-4])}" stroke="#000" stroke-width="1" stroke-dasharray="4 3" fill="none"/>')
    bars = []
    for end in (2, n - 2):
        p = centre[end]
        for j in (-2, -1, 1, 2):
            yy = p[1] + j * h * .16
            bars.append([(p[0] - 3, yy - .5), (p[0] + 3, yy - .5), (p[0] + 3, yy + .5), (p[0] - 3, yy + .5)])
    o.append(_blk(bars))
    return "".join(o)


def propeller(cx, cy, r, a0=0.):
    """A three-blade propeller boss carved over a pedestal rosette."""
    o = [f'<path d="{_d(_ell_pts(cx, cy, r, r, 28), True, 0)}" fill="{pat("D")}" stroke="#000" stroke-width="1"/>']
    blades = []
    for i in range(3):
        a = a0 + 2 * PI * i / 3
        bl = [(.15, -.12), (.55, -.2), (.95, -.1), (1.0, .02), (.6, .12), (.15, .1)]
        blades.append(_xf(bl, cx, cy, r * .95, a))
    o.append(f'<path d="{"".join(_d(b, True, 0) for b in blades)}" fill="#000" stroke="#000" stroke-width=".5"/>')
    hl = "".join(_d(_xf([(.3, -.04), (.85, -.06)], cx, cy, r * .95, a0 + 2 * PI * i / 3), tol=0) for i in range(3))
    o.append(f'<path d="{hl}" stroke="#fff" stroke-width=".5"/>')
    o.append(f'<path d="{_d(_ell_pts(cx, cy, r * .26, r * .26, 14), True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _field_scene(cx, cy, a, b, seed, nplanes, cid):
    d = _d(_superellipse(cx, cy, a + .5, b + .5), True, 0)
    return _clip_path(cid, d, scene(cx - a - 1, cy - b - 1, 2 * a + 2, 2 * b + 2, seed, nplanes))


def _cart_field(cw, ch):
    bw = max(5., min(cw, ch) * .07)
    return cw / 2 - bw * 1.6, ch / 2 - bw * 1.6


# ------------------------------------------------------------------------------------------------
# layouts (copied from the house frame, with the field filled edge to edge)
# ------------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, n):
    o = []
    top = 7.
    o.append(bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.1, 150)
    o.append(_clip(_uid("b", w, h, seed), 0, top, w, gh,
                   scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(_medallion(cx, cy, rx, ry))
    d = _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(_clip_path(_uid("bs", w, h, seed), d, scene(cx - rx, cy - ry, 2 * rx, 2 * ry, seed, n)))
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 2.5, ry - 2.5, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, n):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.75)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = Canvas()
    main = Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                 max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_field(cw, gh + 4)
    o.append(_field_scene(cx, cy, a, b, seed, n, _uid("ms", w, h, seed)))
    o.append(knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, n):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        _pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                 max_n=6, edge=.6, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_field(cw, ch)
    o.append(_field_scene(cx, cy, a, b, seed, n, _uid("ts", w, h, seed)))
    o.append(palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(runway(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(flight_strip(tx, ty, tw, th, n))
    fh_ = th / .6
    inset = w * .035
    for sx in (-1, 1):
        rx = w / 2 + sx * (tw / 2 + (w - 3 * inset - tw) / 4)
        o.append(propeller(rx, ty + th / 2, min(fh_ * .32, 9) + .5, seed * .37 + sx * .6))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(_clip(_uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                       scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                   r_scale=1.15, n=2)))
        o.append(palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def _count(ctx):
    m = re.search(r"(\d+)\s+planes?", (ctx or {}).get("sample", "") or "")
    n = int(m.group(1)) if m else 5
    return max(1, min(n, 9))


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    n = _count(ctx)
    if h < 110:
        body = _layout_band(w, h, seed, n)
    elif h <= 260:
        body = _layout_medium(w, h, seed, n)
    else:
        body = _layout_tall(w, h, seed, n)
    # the paper round the carving is lightly ruled, never bare
    base = dark_ground((0, 0, w, h), "L")
    return svg_doc(w, h, base + body)
