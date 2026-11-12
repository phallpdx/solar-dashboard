"""doodles-02 "Sunset, on the move": looking west from Sauvie Island, the November sun dropping
behind the Tualatin hills at its point on the year's sunset track (Jun 21 .. due west .. Dec 21),
engraved into the house Codex scroll frame. Sky ruled in bulino with white rays cut through it,
streak clouds, hills with firs, the channel with the sun's glitter path, reeds and a great blue
heron (the Sauvie Island Easter egg). Ribbon and pedestal tablet carry path lettering and the
sunset scale."""
import sys
import math
import random
import re
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
CR = ' shape-rendering="crispEdges"'

# ---------------------------------------------------------------- sun geometry


def _doy(date):
    try:
        y, m, d = (int(v) for v in date[:10].split("-"))
    except Exception:
        y, m, d = 2026, 11, 11
    cum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    return cum[m - 1] + d, m, d


def _sunset_az(doy):
    """Sunset azimuth, degrees north (+) / south (-) of due west, at Sauvie Island (45.7 N)."""
    dec = -23.44 * math.cos(2 * math.pi * (doy + 10) / 365)
    s = math.sin(math.radians(dec)) / math.cos(math.radians(45.7))
    return math.degrees(math.asin(max(-1, min(1, s))))


AZ_MAX = _sunset_az(172)

# ---------------------------------------------------------------- stroke lettering (4 x 6 grid)

_G = {
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "M": [[(0, 6), (0, 0), (2, 3), (4, 0), (4, 6)]],
    "D": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 1), (3, 0), (0, 0)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "W": [[(0, 0), (1, 6), (2, 3), (3, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "1": [[(1, 1), (2, 0), (2, 6)], [(1, 6), (3, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]],
    "3": [[(0, 0), (4, 0), (2, 2.5), (3, 2.5), (4, 3.5), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "5": [[(4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "6": [[(3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "7": [[(0, 0), (4, 0), (1, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6),
           (3, 6), (4, 5), (4, 4), (3, 3)]],
    "9": [[(4, 3), (1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6)]],
    ":": [[(1, 1.6), (1, 2.2)], [(1, 4.4), (1, 5)]],
    "*": [[(1, 2.4), (1, 3.6)], [(.4, 3), (1.6, 3)]],
}
_GW = {":": 2, "*": 2, " ": 2.5}


def _text_w(s, k):
    return sum((_GW.get(c, 4) + 2) * k for c in s) - 2 * k


def _letter_along(text, pts, k):
    """Stroke letters of scale k centred along the polyline pts (centre line of the glyphs)."""
    L = [0.]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))

    def at(s):
        s = max(0, min(L[-1], s))
        for i in range(1, len(L)):
            if L[i] >= s:
                t = (s - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
                a, b = pts[i - 1], pts[i]
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, math.atan2(b[1] - a[1], b[0] - a[0]))
        return (*pts[-1], 0.)
    tw = _text_w(text, k)
    s = (L[-1] - tw) / 2
    out = []
    for c in text:
        gw = _GW.get(c, 4)
        x0, y0, ang = at(s + gw * k / 2)
        ca, sa = math.cos(ang), math.sin(ang)
        for stroke in _G.get(c, []):
            out.append(_d([(x0 + ((gx - gw / 2) * ca - (gy - 3) * sa) * k,
                            y0 + ((gx - gw / 2) * sa + (gy - 3) * ca) * k) for gx, gy in stroke], tol=0))
        s += (gw + 2) * k
    return "".join(out)


def _ly(y, w=.5):
    """Snap a horizontal line to the device grid (0.5 lines at k/2+.25, 1 px lines at k/2)."""
    return math.floor(y * 2) / 2 + (.25 if w == .5 else 0)


# ---------------------------------------------------------------- the scene


def _ridge(x0, x1, base, amp, rng, step=3, waves=((5.5, .55), (13, .25), (29, .12))):
    ph = [rng.uniform(0, 6.3) for _ in waves]
    pts = []
    n = int((x1 - x0) / step) + 1
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        t = (x - x0) / (x1 - x0)
        y = base - amp * sum(a * (.5 + .5 * math.sin(f * t + p)) for (f, a), p in zip(waves, ph))
        pts.append((x, y))
    return pts


def _y_on(pts, x):
    for i in range(1, len(pts)):
        if pts[i][0] >= x:
            a, b = pts[i - 1], pts[i]
            t = (x - a[0]) / ((b[0] - a[0]) or 1)
            return a[1] + (b[1] - a[1]) * t
    return pts[-1][1]


def _runs(xs0, xs1, y, white):
    """Horizontal runs at y from xs0 to xs1, skipping where white(x) is true."""
    out, cur = [], None
    x = xs0
    while x <= xs1:
        if white(x):
            if cur is not None and x - cur > .8:
                out.append((cur, x - .5))
            cur = None
        elif cur is None:
            cur = x
        x += .5
    if cur is not None and xs1 - cur > .8:
        out.append((cur, xs1))
    return out


def _hpath(segs):
    return "".join(f"M{_n(a)},{_n(y)}H{_n(b)}" for y, a, b in segs)


def _heron(x, y, H):
    """A great blue heron standing in the shallows, facing left; (x, y) its feet, H its height."""
    def P(pts):
        return [(x + px * H, y - py * H) for px, py in pts]
    body = P([(.36, .36), (.26, .43), (.12, .55), (.0, .64), (-.07, .62), (-.07, .55), (.02, .46), (.14, .4), (.26, .36)])
    neck = P([(-.04, .6), (-.11, .68), (-.1, .76), (-.03, .82), (-.04, .9), (-.09, .94)])
    head = P([(-.05, .925), (-.12, .92), (-.15, .95), (-.1, .975), (-.05, .965)])
    beak = P([(-.14, .945), (-.31, .925)])
    plume = P([(-.06, .97), (.06, .99)])
    legs = P([(.08, .44), (.07, 0)]), P([(.13, .42), (.16, .08), (.14, 0)])
    wing = P([(.0, .58), (.1, .5), (.22, .43), (.32, .38)])
    halo = (f'<path d="{_d(body, True, 0)}{_d(head, True, 0)}" fill="#fff" stroke="#fff" stroke-width="3"/>'
            f'<path d="{_d(neck, tol=0)}{_d(beak, tol=0)}{_d(legs[0], tol=0)}{_d(legs[1], tol=0)}" stroke="#fff" stroke-width="3"/>')
    ink = (f'<path d="{_d(body, True, 0)}{_d(head, True, 0)}" fill="#000" stroke="#000" stroke-width=".5"/>'
           f'<path d="{_d(neck, tol=0)}" stroke="#000" stroke-width="1.5"/>'
           f'<path d="{_d(beak, tol=0)}{_d(legs[0], tol=0)}{_d(legs[1], tol=0)}" stroke="#000" stroke-width="1"/>'
           f'<path d="{_d(wing, tol=0)}{_d(plume, tol=0)}" stroke="#fff" stroke-width=".5"/>')
    return halo + ink


def scene(bx, by, bw, bh, clip_d, cid, ctx, detail=2):
    """The engraved sunset filling the box (bx, by, bw, bh), clipped to clip_d.
    detail: 0 tiny medallion, 1 cartouche (medium), 2 tall plate."""
    doy, mon, day = _doy((ctx or {}).get("date", ""))
    rng = random.Random(doy * 7919 + int(bw) * 31 + int(bh))
    az = _sunset_az(doy)
    az_next = _sunset_az(doy + 7)
    o = []
    cx = bx + bw / 2
    half = bw * .44                          # half-span of the solstice track
    sunx = cx + az / AZ_MAX * half

    y_far = by + bh * (.6 if detail else .58)    # far ridge base (= shoreline across the water)
    y_water = y_far + bh * .015
    y_bot = by + bh
    r = max(5., min(bw * .1, bh * .1))
    far = _ridge(bx - 2, bx + bw + 2, y_far, bh * .2, rng, 3, ((4.5, .6), (11, .28), (27, .1)))
    near = _ridge(bx - 2, bx + bw + 2, y_far + 2, bh * .085, rng, 2.5, ((6, .55), (15, .3), (41, .1)))
    # firs on the near ridge (south-west hills): spikes added into the outline
    if detail:
        nn = []
        for i, (x, y) in enumerate(near):
            nn.append((x, y))
            if i % 2 == 0 and rng.random() < .55 and abs(x - sunx) > r * .6:
                th = rng.uniform(4, 8 + 5 * detail) * (bh / 260) ** .4
                nn += [(x + .6, y - th * .4), (x + 1.1, y - th), (x + 1.6, y - th * .4)]
        near = nn
    sun_y = _y_on(far, sunx) + r * .28

    # ---- sky: bulino rules, darker overhead, white rays cut through, halo round the sun
    nrays = 26
    step = 2 * math.pi / nrays
    R_long, R_short = max(bw, bh) * .75, max(bw, bh) * .42

    def sky_white(x, y):
        dx, dy = x - sunx, y - sun_y
        d = math.hypot(dx, dy)
        if d < r * 1.3:
            return True
        if dy > 0:
            return False
        a = math.atan2(dy, dx)
        k = round(a / step)
        Rk = R_long if k % 2 else R_short
        if d > Rk:
            return False
        hw = (.26 if k % 2 else .17) * step * (1 - d / Rk) ** .7
        return abs(a - k * step) < hw

    clouds = []
    if detail:
        for j in range(3 + detail):
            cy_ = by + bh * rng.uniform(.12, .48)
            cxx = bx + bw * rng.uniform(.1, .9)
            clouds.append((cxx, cy_, bw * rng.uniform(.18, .34), rng.uniform(2.5, 5.5)))

    def cloud_w(x, y):
        for cxx, cy_, hw, th in clouds:
            t = (x - cxx) / hw
            if abs(t) < 1:
                tt = th * (1 - t * t)
                if cy_ - tt * .35 <= y <= cy_ + tt:
                    return 1.5 if y > cy_ else 1.
        return 0.

    segs = {.5: [], 1.: [], 1.5: []}
    y = math.floor(by * 2) / 2 - 1
    top = by - 2
    sky_bot = y_far - bh * .02
    while y < sky_bot:
        f = (y - by) / max(1, sky_bot - by)
        base_w = 1. if f < .32 else .5
        yy = _ly(y, base_w)
        runs = _runs(bx - 2, bx + bw + 2, yy, lambda x: sky_white(x, yy))
        for a, b in runs:
            # split by cloud weight
            cur, cw0 = a, None
            x = a
            while x <= b:
                cw = cloud_w(x, yy) or base_w
                if cw0 is None:
                    cw0 = cw
                elif cw != cw0:
                    segs[cw0].append((_ly(yy, cw0), cur, x))
                    cur, cw0 = x, cw
                x += 1
            segs[cw0].append((_ly(yy, cw0), cur, b))
        y += 2
    for w_, ss in segs.items():
        if ss:
            o.append(f'<path d="{_hpath(ss)}" stroke="#000" stroke-width="{_n(w_)}"{CR}/>')
    # cloud silver linings: a fine line on each cloud's top edge
    if clouds:
        cl = []
        for cxx, cy_, hw, th in clouds:
            cl.append(_d([(cxx + hw * t, cy_ + th * (1 - t * t) + .8) for t in [i / 12 - 1 for i in range(25)]], tol=.2))
        o.append(f'<path d="{"".join(cl)}" stroke="#000" stroke-width="1"/>')

    # ---- the year's sunset track: Jun 21 .. due west .. Dec 21, tonight's mark, arrow south
    if detail:
        ty0 = by + bh * (.2 if detail == 2 else .16)
        sag = bh * .07

        def tr(a):
            u = a / AZ_MAX
            return (cx + u * half, ty0 + sag * (1 - u * u))
        arc = [tr(AZ_MAX * (2 * i / 60 - 1)) for i in range(61)]
        o.append(f'<path d="{_d(arc, tol=.2)}" stroke="#fff" stroke-width="4"/>')
        o.append(f'<path d="{_d(arc, tol=.2)}" stroke="#000" stroke-width="1"/>')
        dots, ticks = [], []
        for dd in (-20.1, -11.6, 0., 11.6, 20.1):           # sunsets on the 21st of the months
            s = math.sin(math.radians(dd)) / math.cos(math.radians(45.7))
            a = math.degrees(math.asin(s))
            if abs(a) < 1:
                continue
            px, py = tr(a)
            dots.append(_d(_ell(px, py, 1.6, 1.6, 10), True, 0))
        for a, L in ((-AZ_MAX, 4.5), (0, 5.5), (AZ_MAX, 4.5)):
            px, py = tr(a)
            ticks.append(_d([(px, py - L), (px, py + L)], tol=0))
        o.append(f'<path d="{"".join(dots)}" fill="#000" stroke="#fff" stroke-width=".5"/>')
        o.append(f'<path d="{"".join(ticks)}" stroke="#fff" stroke-width="3"/><path d="{"".join(ticks)}" stroke="#000" stroke-width="1.5"/>')
        # tonight: a small rayed sun on the track, a dotted plumb down to the real sun
        tx, tyy = tr(az)
        rr = 3.2 + detail * .6
        rays = "".join(_d([(tx + rr * 1.45 * math.cos(i * math.pi / 4), tyy + rr * 1.45 * math.sin(i * math.pi / 4)),
                           (tx + rr * 2.1 * math.cos(i * math.pi / 4), tyy + rr * 2.1 * math.sin(i * math.pi / 4))], tol=0)
                       for i in range(8))
        o.append(f'<path d="{_d(_ell(tx, tyy, rr * 2.4, rr * 2.4, 24), True, 0)}" fill="#fff" stroke="none"/>')
        o.append(f'<path d="{rays}" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{_d(_ell(tx, tyy, rr, rr, 20), True, 0)}" fill="#000" stroke="none"/>')
        o.append(f'<path d="M{_n(tx)},{_n(tyy + rr * 2.6)}V{_n(sun_y - r * 1.45)}" stroke="#000" stroke-width="1" stroke-dasharray="0 3"/>')
        # arrow: which way the sunset is travelling this week
        sgn = -1 if az_next < az else 1
        ax0 = tx + sgn * rr * 2.8
        ax1 = ax0 + sgn * min(half * .28, 30)
        ay0, ay1 = tr(az + sgn * 1.5)[1] - 7, tr(az + sgn * 6)[1] - 7
        o.append(f'<path d="M{_n(ax0)},{_n(ay0)}L{_n(ax1)},{_n(ay1)}m{_n(-sgn * 4)},-3l{_n(sgn * 4)},3l{_n(-sgn * 4)},3" '
                 f'stroke="#fff" stroke-width="3"/>'
                 f'<path d="M{_n(ax0)},{_n(ay0)}L{_n(ax1)},{_n(ay1)}m{_n(-sgn * 4)},-3l{_n(sgn * 4)},3l{_n(-sgn * 4)},3" stroke="#000" stroke-width="1"/>')

    # ---- the sun: a white disc lightly ruled, half sunk behind the far hills
    disc = _ell(sunx, sun_y, r, r, 40)
    o.append(f'<path d="{_d(disc, True, 0)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    hs = []
    yy = sun_y - r + 1.5
    while yy < sun_y + r:
        hw = math.sqrt(max(0, r * r - (yy - sun_y) ** 2)) - 1.2
        if hw > 1 and abs(yy - sun_y) > r * .15:
            hs.append((_ly(yy), sunx - hw, sunx + hw))
        yy += 3
    if hs:
        o.append(f'<path d="{_hpath(hs)}" stroke="#000" stroke-width=".5"{CR}/>')

    # ---- far hills (Tualatin range): mid tone, horizontal bulino
    fpoly = far + [(bx + bw + 2, y_water + 1), (bx - 2, y_water + 1)]
    o.append(f'<path d="{_d(fpoly, True, .2)}" fill="#fff" stroke="none"/>')
    fh = [(_ly(p[0][1]), p[0][0], p[1][0]) for p in C.hatch_poly(fpoly, 0, 2, .25)]
    o.append(f'<path d="{_hpath(fh)}" stroke="#000" stroke-width="1"{CR}/>')
    o.append(f'<path d="{C.hatch_d(fpoly, -45, 3, .5)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_d(far, tol=.2)}" stroke="#000" stroke-width="1"/>')
    # near ridge with firs: dark, ruled + 45 hatch
    npoly = near + [(bx + bw + 2, y_water + 2), (bx - 2, y_water + 2)]
    near_clip = [(x, max(y, _y_on(far, x) + 3)) if abs(x - sunx) < r * 1.1 else (x, y) for x, y in near]
    npoly = [(x, max(y, by)) for x, y in near_clip] + [(bx + bw + 2, y_water + 2), (bx - 2, y_water + 2)]
    o.append(f'<path d="{_d(npoly, True, .15)}" fill="#000" stroke="none"/>')
    nh = C.hatch_d(npoly, 45, 3, .5)
    o.append(f'<path d="{nh}" stroke="#fff" stroke-width=".5"/>')

    # ---- the channel: ruled water with the sun's glitter path and the hills' reflection
    yw0 = y_water + 2
    ybank = y_bot - bh * (.12 if detail else .1)
    ws = {.5: [], 1.: []}
    y = yw0
    i = 0
    while y < y_bot + 2:
        dep = (y - yw0) / max(1, y_bot - yw0)
        wgt = 1. if dep < .16 else .5
        yy = _ly(y, wgt)
        gw = r * (.7 + 2.2 * dep)
        glitter = []
        gx = sunx - gw
        while gx < sunx + gw:
            L = rng.uniform(1.5, 4.5) * (1 - abs(gx - sunx) / gw * .5)
            glitter.append((gx, gx + L))
            gx += L + rng.uniform(1.2, 3.5)
        breaks = [(xx, xx + rng.uniform(1, 3)) for xx in [bx + rng.uniform(0, bw) for _ in range(int(bw / 40))]]

        def white(x, glitter=glitter, breaks=breaks, gw=gw):
            if abs(x - sunx) < gw:
                return not any(a <= x <= b for a, b in glitter)
            return any(a <= x <= b for a, b in breaks)
        for a, b in _runs(bx - 2, bx + bw + 2, yy, white):
            ws[wgt].append((yy, a, b))
        y += 2
        i += 1
    for w_, ss in ws.items():
        if ss:
            o.append(f'<path d="{_hpath(ss)}" stroke="#000" stroke-width="{_n(w_)}"{CR}/>')

    # ---- foreground: a reedy bank of the island with the heron (Easter egg)
    if detail:
        side = -1 if sunx > cx else 1        # bank on the side away from the sun
        bank = []
        x0b = cx + side * bw * .05
        xe = bx + bw + 2 if side > 0 else bx - 2
        n = 24
        for k in range(n + 1):
            t = k / n
            x = x0b + (xe - x0b) * t
            yb = ybank + (1 - t) ** 2 * bh * .12 - rng.uniform(0, 1.5)
            bank.append((x, yb))
        bank += [(xe, y_bot + 2), (x0b, y_bot + 2)]
        o.append(f'<path d="{_d(bank, True, .2)}" fill="#000" stroke="none"/><path d="{C.hatch_d(bank, -45 * side, 3, .5)}" stroke="#fff" stroke-width=".5"/>')
        o.append(f'<path d="{_d(bank[:n + 1], tol=.2)}" stroke="#000" stroke-width="1.5"/>')
        # reeds and cattails
        reeds, heads = [], []
        for k in range(10 + 6 * detail):
            t = rng.uniform(.25, 1.)
            x = x0b + (xe - x0b) * t
            yb = _y_on(sorted(bank[:n + 1]), x)
            Lr = rng.uniform(.08, .2) * bh
            lean = rng.uniform(-.25, .25) * Lr
            pts = [(x + lean * (s / 6) ** 2, yb - Lr * s / 6) for s in range(7)]
            reeds.append(_d(pts, tol=.2))
            if rng.random() < .4:
                hx, hy = pts[-2]
                heads.append(_d(_ell(hx, hy, 1.3, 3.2, 10), True, 0))
        o.append(f'<path d="{"".join(reeds)}" stroke="#fff" stroke-width="2"/><path d="{"".join(reeds)}" stroke="#000" stroke-width="1"/>')
        if heads:
            o.append(f'<path d="{"".join(heads)}" fill="#000" stroke="#fff" stroke-width=".5"/>')
        # the heron wading just off the bank
        H = bh * (.32 if detail == 2 else .34)
        hx = x0b - side * bw * .07
        hy = ybank + bh * .05
        o.append(_heron(hx, hy, H) if side > 0 else
                 f'<g transform="translate({_n(2 * hx)},0) scale(-1,1)">{_heron(hx, hy, H)}</g>')
    body = "".join(o)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})"><path d="{clip_d}" fill="#fff" stroke="none"/>{body}</g>')


# ---------------------------------------------------------------- layouts (house layouts, adapted)


def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return (cx - a, cy - b, 2 * a, 2 * b)


def _band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip = _d(_ell(cx, cy, rx - 3.5, ry - 3.5, 64), True, 0)
    o.append(scene(cx - rx + 3, cy - ry + 3, 2 * rx - 6, 2 * ry - 6, clip, C._uid("bs", w, h), ctx, 0))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _medium(w, h, seed, ctx):
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
    cv, main = C.Canvas(), C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=9, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene(*_field(cx, cy, cw, ch), inner, C._uid("ms", w, h), ctx, 1))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    # the paper round the panel is lightly ruled (no bare white), the panel is double ruled
    o.append(f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("L")}" stroke="none"/>')
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .48, ph * .62
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .5)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .5)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=8, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene(*_field(cx, cy, cw, ch), inner, C._uid("ts", w, h), ctx, 2))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh_ = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh_, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # ribbon lettering: SUNSET and tonight's time, cut as paths
    m = re.search(r"(\d{1,2}:\d{2})\s*([ap])m", (ctx or {}).get("sample", ""))
    words = "SUNSET" + (f" * {m.group(1)} {m.group(2).upper()}M" if m else "")
    k = min(bh_ * .085, 1.3)
    o.append(f'<path d="{_letter_along(words, centre, k)}" stroke="#000" stroke-width="1"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet(tx, ty, tw, th, ctx))
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


def _tablet(tx, ty, tw, th, ctx):
    """The pedestal tablet engraved with the page's own scale: DEC 21 .. due west .. JUN 21."""
    doy, _, _ = _doy((ctx or {}).get("date", ""))
    az = _sunset_az(doy)
    k = min(th * .11, 1.)
    cy = ty + th / 2 + .5
    lw = _text_w("DEC 21", k)
    x0, x1 = tx + 8 + lw + 8, tx + tw - 8 - lw - 8
    lines = f"M{_n(x0)},{_n(cy)}H{_n(x1)}"
    xm = (x0 + x1) / 2
    for x, L in ((x0, 3.5), (xm, 4.5), (x1, 3.5)):
        lines += f"M{_n(x)},{_n(cy - L)}V{_n(cy + L)}"
    dots = []
    for i in range(1, 12):
        if i == 6:
            continue
        x = x0 + (x1 - x0) * i / 12
        dots.append(_d(_ell(x, cy, 1.2, 1.2, 8), True, 0))
    sx = xm + az / AZ_MAX * (x1 - x0) / 2
    rays = "".join(_d([(sx + 4.2 * math.cos(i * math.pi / 4), cy + 4.2 * math.sin(i * math.pi / 4)),
                       (sx + 6 * math.cos(i * math.pi / 4), cy + 6 * math.sin(i * math.pi / 4))], tol=0) for i in range(8))
    return (f'<path d="{_letter_along("DEC 21", [(tx + 8, cy), (tx + 8 + lw, cy)], k)}'
            f'{_letter_along("JUN 21", [(tx + tw - 8 - lw, cy), (tx + tw - 8, cy)], k)}{lines}" stroke="#000" stroke-width="1"/>'
            f'<path d="{"".join(dots)}" fill="#000" stroke="none"/>'
            f'<path d="{_d(_ell(sx, cy, 7, 7, 20), True, 0)}" fill="#fff" stroke="none"/>'
            f'<path d="{rays}" stroke="#000" stroke-width="1"/>'
            f'<path d="{_d(_ell(sx, cy, 3, 3, 16), True, 0)}" fill="#000" stroke="none"/>')


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 202
    if h < 110:
        body = _band(w, h, seed, ctx)
    elif h <= 260:
        body = _medium(w, h, seed, ctx)
    else:
        body = _tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
