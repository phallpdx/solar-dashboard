"""coast-02 - Bar and beach warnings: Hazardous Seas Warning at the Columbia River bar.

Vignette: the Columbia River bar in a southerly gale. Cape Disappointment's wooded headland and
its black-banded lighthouse throw a beam across a storm sky; a ship pitches bow-up over the bar
beyond the North Jetty; a great breaker rises in the foreground and its lip rolls into a volute
whose spray breaks into swept acanthus fingers, the frame's own scrollwork. Lettered banner
(COLUMBIA RIVER BAR) and tablet (today's warning, read from the page text).
Easter egg: a Sauvie Island heron standing on the jetty head. The moon phase follows the date.
"""
import sys
import math
import random
import datetime
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_K = 2 ** (-1 / 2.6)
_n = C._n


# ------------------------------------------------------------------------------------------------
# geometry helpers
# ------------------------------------------------------------------------------------------------

def _inside(lines, poly):
    """The parts of polylines that fall inside poly."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, y0 = int(min(xs)) - 2, int(min(ys)) - 2
    W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
    mask = [bytearray(W) for _ in range(H)]
    C._fill_mask(poly, mask, x0, y0, W, H)
    inv = bytes.maketrans(b"\x00\x01", b"\x01\x00")
    mask = [bytearray(r.translate(inv)) for r in mask]
    out = []
    for pl in lines:
        if len(pl) > 1:
            C._clip_runs(pl, mask, x0, y0, W, H, out)
    return out


def _rules(x0, y0, x1, y1, pitch=2., amp=0., wl=14., phase=0., step=3.):
    """Parallel horizontal lines (optionally rippled), a constant gap apart."""
    out = []
    y = y0
    k = 0
    while y <= y1:
        if amp:
            pl = []
            x = x0
            while x <= x1 + step:
                pl.append((x, y + amp * math.sin((x + phase + k * 5.3) / wl * TAU)))
                x += step
        else:
            pl = [(x0, y), (x1, y)]
        out.append(pl)
        y += pitch
        k += 1
    return out


def _cloud(cx, cy, w, h, rng, n=5):
    """A billowing storm cloud: bumps on top, a flat base. Returns (outline, bump centres)."""
    pts = []
    bumps = []
    base = cy + h * .35
    for i in range(n):
        f = (i + .5) / n
        bx = cx - w / 2 + w * f
        br = w / n * rng.uniform(.62, .8)
        top = cy - h * (.15 + .5 * math.sin(PI * f)) * rng.uniform(.85, 1.1)
        bumps.append((bx, top + br * .55, br))
        for j in range(11):
            a = PI + PI * j / 10
            pts.append((bx + br * math.cos(a), min(base, top + br * .55 + br * .75 * math.sin(a))))
    pts = [(cx - w / 2 - w * .04, base)] + pts + [(cx + w / 2 + w * .04, base)]
    return pts, bumps, base


# ------------------------------------------------------------------------------------------------
# path lettering: a single-stroke roman capital, drawn with 1 px lines
# ------------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


_G = {
    "A": [[(0, 1), (.32, 0), (.64, 1)], [(.13, .64), (.51, .64)]],
    "B": [[(0, 1), (0, 0), (.36, 0)] + _arc(.36, .24, .18, .24, -90, 90, 6) + [(0, .48)],
          [(.36, .48)] + _arc(.38, .74, .2, .26, -90, 90, 6) + [(0, 1)]],
    "C": [_arc(.32, .5, .32, .5, -40, -320, 14)],
    "D": [[(0, 0), (0, 1), (.26, 1)] + _arc(.26, .5, .34, .5, 90, -90, 10) + [(0, 0)]],
    "E": [[(.52, 0), (0, 0), (0, 1), (.54, 1)], [(0, .48), (.4, .48)]],
    "F": [[(.52, 0), (0, 0), (0, 1)], [(0, .48), (.4, .48)]],
    "G": [_arc(.32, .5, .32, .5, -40, -340, 14), [(.36, .58), (.62, .58), (.62, .92)]],
    "H": [[(0, 0), (0, 1)], [(.6, 0), (.6, 1)], [(0, .48), (.6, .48)]],
    "I": [[(0, 0), (0, 1)]],
    "K": [[(0, 0), (0, 1)], [(.56, 0), (0, .6)], [(.2, .44), (.6, 1)]],
    "L": [[(0, 0), (0, 1), (.5, 1)]],
    "M": [[(0, 1), (0, 0), (.36, .78), (.72, 0), (.72, 1)]],
    "N": [[(0, 1), (0, 0), (.6, 1), (.6, 0)]],
    "O": [_arc(.34, .5, .34, .5, 0, 360, 18)],
    "P": [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .25, .24, .25, -90, 90, 6) + [(0, .5)]],
    "R": [[(0, 1), (0, 0), (.32, 0)] + _arc(.32, .25, .24, .25, -90, 90, 6) + [(0, .5)], [(.26, .5), (.6, 1)]],
    "S": [_arc(.28, .26, .26, .26, -20, -270, 8) + _arc(.3, .75, .27, .25, -90, 160, 9)],
    "T": [[(0, 0), (.64, 0)], [(.32, 0), (.32, 1)]],
    "U": [[(0, 0), (0, .68)] + _arc(.3, .68, .3, .32, 180, 0, 8) + [(.6, 0)]],
    "V": [[(0, 0), (.32, 1), (.64, 0)]],
    "W": [[(0, 0), (.2, 1), (.41, .28), (.62, 1), (.82, 0)]],
    "X": [[(0, 0), (.6, 1)], [(.6, 0), (0, 1)]],
    "Y": [[(0, 0), (.32, .5), (.64, 0)], [(.32, .5), (.32, 1)]],
    "Z": [[(0, 0), (.58, 0), (0, 1), (.6, 1)]],
    "-": [[(.05, .55), (.4, .55)]],
    "&": [[(.62, 1), (.1, .4)] + _arc(.24, .2, .16, .2, 150, -150, 8)[::-1][:1] + _arc(.24, .2, .16, .2, 150, -150, 8)
          + [(.1, .62)] + _arc(.24, .78, .2, .22, 180, 30, 6) + [(.6, .55)]],
}


def _gw(ch):
    if ch == " ":
        return .42
    g = _G.get(ch)
    return (max(p[0] for s in g for p in s) if g else .5) + .3


def _letter_path(text, path, size, spacing=1.):
    """Letter text (caps) centred along polyline `path` with cap height `size`.
    Returns (strokes, serifs) in plate px; strokes are 1 px."""
    L = [0.]
    for i in range(1, len(path)):
        L.append(L[-1] + math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]))
    total = sum(_gw(c) for c in text) * size * spacing - .3 * size
    s = (L[-1] - total) / 2

    def frame(d):
        d = min(max(d, 0), L[-1] - 1e-6)
        i = max(1, next(k for k in range(1, len(L)) if L[k] >= d))
        t = (d - L[i - 1]) / ((L[i] - L[i - 1]) or 1)
        p = (path[i - 1][0] + (path[i][0] - path[i - 1][0]) * t, path[i - 1][1] + (path[i][1] - path[i - 1][1]) * t)
        a = math.atan2(path[i][1] - path[i - 1][1], path[i][0] - path[i - 1][0])
        return p, a

    out = []
    ser = []
    for ch in text:
        adv = _gw(ch) * size * spacing
        g = _G.get(ch)
        if g:
            gw = (_gw(ch) - .3) * size
            (px, py), a = frame(s + gw / 2)
            ca, sa = math.cos(a), math.sin(a)

            def T(u, v):
                x = u * size - gw / 2
                y = (v - .5) * size
                return (px + x * ca - y * sa, py + x * sa + y * ca)
            for st in g:
                out.append([T(u, v) for u, v in st])
                # bracket serifs on stroke ends at cap and base line
                for (u, v) in (st[0], st[-1]):
                    if v in (0, 1) and ch not in "COSGU&-":
                        ser.append([T(u - .1, v), T(u + .1, v)])
        s += adv
    return out, ser


def _lettering(text, path, size, spacing=1.):
    strokes, ser = _letter_path(text, path, size, spacing)
    return (f'<path d="{"".join(C._d(p, tol=0) for p in strokes)}" fill="none" stroke="#000" stroke-width="1" '
            f'stroke-linecap="square" stroke-linejoin="miter"/>'
            f'<path d="{"".join(C._d(p, tol=0) for p in ser)}" fill="none" stroke="#000" stroke-width=".5"/>')


# ------------------------------------------------------------------------------------------------
# the breaker: a lip that curls into a volute, with acanthus spray
# ------------------------------------------------------------------------------------------------

def _breaker(cv, cx, cy, r, floor, left, right, flip=False, seed=0, spray=True, bottom=None):
    """A plunging breaker whose lip curls round (cx, cy), pitching left (flip mirrors it).
    floor: y of the trough in front; left/right: x extent of the wave's body; bottom: y to fill to."""
    rng = random.Random(seed)
    sg = -1 if flip else 1
    bottom = bottom if bottom is not None else floor + r * 3

    def M(p):
        return (2 * cx - p[0], p[1]) if flip else p

    raw = C.volute_spine(cx, cy, r, -60, 1.12, True, 3.2, -.65, .15)
    n = len(raw)
    S = [0.]
    for k in range(1, n):
        S.append(S[-1] + math.hypot(raw[k][0] - raw[k - 1][0], raw[k][1] - raw[k - 1][1]))
    tot = S[-1]
    apex = min(range(n), key=lambda i: raw[i][1])
    ua = S[apex] / tot
    kl = min(range(apex, n), key=lambda i: raw[i][0])          # the lip's leftmost reach
    # extend the back off to the right edge
    tail0 = raw[0]
    back = [(right + 4, tail0[1] + (right + 4 - tail0[0]) * .18)] if right > tail0[0] else []
    # the face: from under the lip, a concave sweep down into the trough
    lx_, ly_ = raw[kl]
    face = [(lx_ + r * .15, ly_ + r * .55), (lx_ - r * .1, floor - r * .25), (lx_ - r * .7, floor - r * .02),
            (left - 4, floor + r * .05)]
    front = [(left - 4 - r * 1.6 * t * t, floor + r * .05 + (bottom - floor) * t) for t in [j / 8 for j in range(1, 9)]]
    poly = back + raw[:kl + 1] + face + front + [(right + 4, bottom)]
    poly = [M(p) for p in poly]
    cv.obj([poly], 0)
    cv.line([[M(p) for p in back + raw[:kl + 1] + face]])
    cv.hair([[M(p) for p in [face[-1]] + front]])
    # water lines: the surface profile repeated down the body, rising into the back
    prof = back + raw[:apex + 1] + [(left - 8, raw[apex][1] + r * .4)]
    lines = []
    for k in range(1, int((bottom - raw[apex][1]) / 2) + 2):
        f = k * 2.
        lines.append([M((x, y + f + .6 * math.sin(x / 8 + k))) for x, y in prof])
    body_lines = _inside(lines, poly)
    cv.hair(body_lines)
    # the hollow face under the lip: streaks falling from the lip, then the dark barrel
    streaks = []
    for k in range(apex, kl + 1, 2):
        x, y = raw[k]
        pts = [M((x - r * .6 * t * t, y + (floor - y + r * .3) * t)) for t in [j / 10 for j in range(11)]]
        streaks.append(pts)
    barrel = [M((cx - r * 1.15, cy - r * .1)), M((cx - r * .2, cy - r * .7)), M((cx + r * .6, cy - r * .2)),
              M((cx + r * .7, cy + r * .6)), M((cx - r * .3, min(floor + r * .1, cy + r * 1.4))), M((cx - r * 1.3, min(floor - r * .2, cy + r * 1.2)))]
    cv.line(_inside(C.hatch_poly(barrel, 75 * sg, 2.), poly))
    cv.hair(_inside(C.hatch_poly(barrel, -20 * sg, 3.), poly))
    cv.hair(_inside(streaks, poly))

    # the lip: a thick white ribbon thinning into the curl, carved like a stem
    W0 = r * .3
    ws, wo = [], []
    for k in range(n):
        u = S[k] / tot
        w = W0 * (.1 + .9 * C._smooth(0, ua, u)) * (1 - .75 * C._smooth(ua, 1., u))
        ws.append(max(.7, w * .5))
        wo.append(max(.7, w))
    spine = [M(p) for p in raw]
    i = (apex + kl) // 2
    a, b = spine[i - 1], spine[i + 1]
    ccx = 2 * cx - cx if not flip else cx
    ins = 1 if (-(b[1] - a[1])) * (ccx - spine[i][0]) + (b[0] - a[0]) * (cy - spine[i][1]) > 0 else -1
    R = C._Rib(spine, ws if ins > 0 else wo, wo if ins > 0 else ws)
    cv.obj([R.outline()], 1.)
    cv.hair(C._fill_lines(R, .05 * ins, .97 * ins, 1.5, .0, .99, 4))
    cv.hair(C._fill_lines(R, -.1 * ins, -.6 * ins, 3., .0, .9, 2))
    C._shadow(cv, R, ins, W0 * .5, ua * .6, .97)
    ex, ey = spine[-1]
    rr = max(1.6, ws[-1] * .9)
    cv.obj([C._ell_pts(ex, ey, rr + 1.2, rr + 1.2, 16)[:-1]], 0)
    q = rr - .4
    while q > .3:
        cv.line(C._ell_pts(ex, ey, q, q, max(8, int(q * 6))))
        q -= .8

    if spray:
        # acanthus spray: fingers thrown forward off the crest, tips rolling over like the lip
        fr = []
        for j, f in enumerate((.45, .62, .78, .9, 1.0)):
            u = ua * f
            k = min(n - 2, int(u * (n - 1)))
            p0, p1 = spine[max(0, k - 1)], spine[k + 1]
            ta = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            base = R.at(u, -ins * .5)
            ll = r * (.7 + .18 * j) * rng.uniform(.92, 1.06)
            sub = C.Canvas()
            C._finger(sub, base[0], base[1], ta - sg * (.7 - .08 * j), ll, ll * .11, sg * .3, -sg * 5.2, 1.)
            fr.append(sub)
        for sub in fr:
            cv.extend(sub)
        ax, ay = spine[apex]
        fl = []
        for j in range(24):
            dx = rng.uniform(-.2, 1.5) * r * sg
            dy = -rng.uniform(.15, .8) * r + abs(dx) * .2
            fl.append(C._ell_pts(ax + dx, ay + dy, .8, .55, 6))
        cv.hair(fl)
    return spine, poly


# ------------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------------

def _scene(bx, by, bw, bh, field, moon, seed, detail=2):
    rng = random.Random(seed)
    cv = C.Canvas()

    def P(u, v):
        return (bx + u * bw, by + v * bh)

    hz = .5 if detail >= 1 else .52
    yh = by + hz * bh
    # sky: close ruled
    sky = [P(-.02, -.02), P(1.02, -.02), P(1.02, hz + .01), P(-.02, hz + .01)]
    cv.obj([sky], 0)
    ys_ = by + bh * .3
    cv.hair(_rules(bx - 2, by - 1, bx + bw + 2, ys_, 2.))
    cv.hair(_rules(bx - 2, ys_ + 3, bx + bw + 2, yh, 3.))

    # the moon (phase from the date), behind the cloud wrack
    if detail >= 1:
        mx, my = P(.52, .1)
        mr = max(4., bh * .06)
        disc = C._ell_pts(mx, my, mr, mr, 32)
        cv.obj([disc], .5)
        k = math.cos(TAU * moon)               # 1 new .. -1 full
        waxing = moon < .5
        term = [(mx + (mr * math.sin(a) * k) * (1 if waxing else -1), my - mr * math.cos(a)) for a in
                [PI * j / 16 for j in range(17)]]
        limb = [(mx + (-mr if waxing else mr) * math.sin(a), my - mr * math.cos(a)) for a in
                [PI * j / 16 for j in range(16, -1, -1)]]
        cv.hair(_inside(_rules(mx - mr, my - mr, mx + mr, my + mr, 1.5), term + limb))
        cv.hair([C._ell_pts(mx, my, mr * 1.6, mr * 1.6, 32), C._ell_pts(mx, my, mr * 2.3, mr * 2.3, 40)])

    lx, ly = P(.12, .21)
    # storm clouds: each billow its own carved mass, lit crown, contoured body, ruled dark base
    if detail >= 1:
        specs = ((.8, .17, .44, .15, 5), (.2, .08, .42, .1, 4), (.47, .35, .4, .08, 4), (.98, .38, .3, .07, 3))
        for (u, v, cw_, ch_, nb) in specs:
            ccx, ccy = P(u, v)
            W_, H_ = cw_ * bw, ch_ * bh
            base = ccy + H_ * .45
            bumps = []
            for i in range(nb):
                f = (i + .5) / nb
                br = W_ / nb * rng.uniform(.62, .8)
                bumps.append((ccx - W_ / 2 + W_ * f + rng.uniform(-2, 2),
                              ccy - H_ * .45 * math.sin(PI * f) ** .7 * rng.uniform(.8, 1.1) + br * .35, br))
            xs = [ccx - W_ * .62 + i * 1.5 for i in range(int(W_ * 1.24 / 1.5) + 1)]

            def ytop(x):
                best = base
                for qx, qy, qr in bumps:
                    if abs(x - qx) < qr:
                        best = min(best, qy - qr * .66 * math.sqrt(1 - ((x - qx) / qr) ** 2))
                return best
            tops = [(x, ytop(x)) for x in xs]
            tops = [p for p in tops if p[1] < base - .5]
            if len(tops) < 3:
                continue
            cp = tops + [(x, base + 1.2 * math.sin(x / 9)) for x, _ in tops[::-1]]
            cv.obj([cp], 0)
            cv.hair([tops])
            for qx, qy, qr in bumps:      # the seam where one billow rolls over the next
                cv.hair([C._ell_pts(qx + qr * .1, qy + qr * .05, qr * .8, qr * .5, 14, PI * .15, PI * .8)])

            def runs(pitch, test):
                out = []
                y = math.floor(min(p[1] for p in tops) / pitch) * pitch
                while y < base + 2:
                    cur = []
                    for x, t in tops:
                        if test(y, t):
                            cur.append((x, y))
                        else:
                            if len(cur) > 1:
                                out.append([cur[0], cur[-1]])
                            cur = []
                    if len(cur) > 1:
                        out.append([cur[0], cur[-1]])
                    y += pitch
                return _inside(out, cp)
            cut = lambda y, t: y > t + 2 + .3 * (base - t)
            cv.hair(runs(3., lambda y, t: y > t + 1.2 and not cut(y, t)))
            cv.line(runs(2., cut))
        # squalls slanting down under the south wind
        rain = []
        for i in range(int(bw * .16 / 3)):
            x = bx + bw * .58 + i * 3.
            rain.append([(x, by + bh * .22), (x - bh * .1, yh - 1)])
        cv.hair(_inside(rain, [P(.5, .2), P(.8, .2), P(.8, hz), P(.5, hz)]))
        # the lighthouse beam, a lighter wedge across the dark
        beam = [(lx, ly), P(.62, .19), P(.6, .29)]
        cv.obj([beam], 0)
        cv.hair(_inside(_rules(bx, by, bx + bw, yh, 3.), beam))
        cv.hair([[(lx, ly), P(.62, .19)], [(lx, ly), P(.6, .29)]])

    # far sea under the horizon
    sea = [P(-.02, hz), P(1.02, hz), P(1.02, 1.02), P(-.02, 1.02)]
    cv.obj([sea], 0)
    cv.hair(_rules(bx - 2, yh + 1.5, bx + bw + 2, by + bh, 2., .5, 9., seed % 7))
    cv.line([P(-.02, hz), P(1.02, hz)])

    # Cape Disappointment: wooded headland, cliffs falling to the bar
    head = [P(-.03, .7), P(-.03, .27), P(.03, .27), P(.09, .25), P(.16, .26), P(.2, .3), P(.23, .4),
            P(.25, .47), P(.29, .53), P(.32, .56), P(.31, .6), P(.0, .7)]
    cv.obj([head], 1.)
    cliff = [P(.13, .31), P(.25, .31), P(.36, .62), P(.0, .72), P(-.03, .45)]
    cv.hair(_inside(C.hatch_poly(head, 70, 1.5), cliff))
    cv.hair(_inside(C.hatch_poly(head, 70, 3.), [P(-.03, .2), P(.24, .2), P(.24, .31), P(.13, .31), P(-.03, .45)]))
    for k in range(7):
        t = .33 + k * .04
        cv.line([P(.205 + .012 * k, t), P(.16 + .02 * k, t + .02), P(.09 + .022 * k, t + .012)])
    # firs along the crest
    if detail >= 1:
        for i in range(10):
            fu = -.015 + i * .021
            if .095 < fu < .145:
                continue
            fv = .265 + .012 * math.sin(i * 1.7) if fu < .16 else .29
            fx, fy = P(fu, fv)
            fh = bh * rng.uniform(.065, .1)
            fwd = fh * .36
            tri = [(fx - fwd, fy), (fx - fwd * .3, fy - fh * .55), (fx - fwd * .55, fy - fh * .5), (fx, fy - fh),
                   (fx + fwd * .55, fy - fh * .5), (fx + fwd * .3, fy - fh * .55), (fx + fwd, fy)]
            cv.obj([tri], .5)
            y = fy - fh + 1.2
            while y < fy:
                f = (y - (fy - fh)) / fh
                cv.line([(fx - fwd * f * .85, y + .9), (fx, y), (fx + fwd * f * .85, y + .9)])
                y += 1.6
    # the lighthouse: white conical tower with its black middle band, gallery and lantern
    tw = max(4., bw * .03)
    th = bh * .15
    tt = ly + bh * .03
    tb = tt + th
    tower = [(lx - tw / 2, tb), (lx - tw * .36, tt), (lx + tw * .36, tt), (lx + tw / 2, tb)]
    cv.obj([tower], 1.)
    cv.hair([[(lx + tw * f * .4, tt), (lx + tw * f * .5, tb)] for f in (.25, .55, .85)])
    y = tt + th * .36
    while y < tt + th * .62:
        cv.line([(lx - tw * .44, y), (lx + tw * .44, y)])
        y += .8
    lan = [(lx - tw * .26, tt), (lx - tw * .26, ly), (lx - tw * .1, ly - bh * .028), (lx + tw * .1, ly - bh * .028),
           (lx + tw * .26, ly), (lx + tw * .26, tt)]
    cv.obj([lan], 1.)
    cv.line([(lx - tw * .55, tt), (lx + tw * .55, tt)])
    cv.hair([(lx, ly - bh * .028), (lx, ly - bh * .045)])
    # keeper's house at its foot
    kh = [(lx + tw * .7, tb), (lx + tw * .7, tb - bh * .03), (lx + tw * 1.4, tb - bh * .055), (lx + tw * 2.1, tb - bh * .03), (lx + tw * 2.1, tb)]
    cv.obj([kh], .5)
    cv.hair(_inside(C.hatch_poly(kh, 90, 1.5), [(lx + tw * 1.4, tb - bh * .06), (lx + tw * 2.2, tb - bh * .06), (lx + tw * 2.2, tb + 1), (lx + tw * 1.4, tb + 1)]))

    # the North Jetty, a rubble mound running out across the bar
    jet = [P(.27, .555), P(.33, .54), P(.55, .535), P(.575, .55), P(.55, .565), P(.29, .58)]
    cv.obj([jet], 1.)
    cv.hair(_inside(C.hatch_poly(jet, 0, 1.5), [P(.25, .552), P(.6, .552), P(.6, .6), P(.25, .6)]))
    for i in range(12):
        u = .29 + i * .022
        cv.hair([C._ell_pts(*P(u, .548), bw * .009, bh * .01, 10, PI, TAU)])
    # surf bursting along the jetty
    for i in range(6):
        u = .32 + i * .04
        sx_, sy_ = P(u, .545)
        cv.hair([C._ell_pts(sx_, sy_, bw * .012, bh * .018, 12, PI, TAU), C._ell_pts(sx_ + 1, sy_, bw * .007, bh * .01, 10, PI, TAU)])
    # easter egg: a great blue heron on the jetty head (Sauvie Island)
    hx, hy = P(.556, .536)
    s = max(.55, bh * .0032)
    heron = [(hx - 3.6 * s, hy - 6.4 * s), (hx - 1 * s, hy - 9.6 * s), (hx + .9 * s, hy - 10.2 * s),
             (hx + 1.6 * s, hy - 12 * s), (hx + .6 * s, hy - 14.6 * s), (hx + 1.6 * s, hy - 16.6 * s),
             (hx + 2.7 * s, hy - 16.6 * s), (hx + 5.6 * s, hy - 15.6 * s), (hx + 2.6 * s, hy - 15.4 * s),
             (hx + 2.0 * s, hy - 14.4 * s), (hx + 2.8 * s, hy - 11.8 * s), (hx + 2.2 * s, hy - 8.6 * s),
             (hx + .2 * s, hy - 6.2 * s)]
    cv.obj([heron], .5)
    cv.hair(_inside(C.hatch_poly(heron, 30, 1.5), [(hx - 4 * s, hy - 10 * s), (hx + 2.5 * s, hy - 10 * s), (hx + 2.5 * s, hy - 5 * s), (hx - 4 * s, hy - 5 * s)]))
    cv.line([[(hx - .6 * s, hy - 6.6 * s), (hx - .8 * s, hy)], [(hx + .4 * s, hy - 6.6 * s), (hx + .7 * s, hy)]])
    cv.hair([(hx + 2.2 * s, hy - 16 * s), (hx + .4 * s, hy - 17.4 * s)])

    # the ship pitching over the bar, bow up into the seas
    sx, sy = P(.5, .6)
    sl = bw * (.2 if detail >= 1 else .26)
    ang = math.radians(-9)
    ca, sa = math.cos(ang), math.sin(ang)

    def S(a, b):
        return (sx + a * sl * ca - b * sl * sa, sy + a * sl * sa + b * sl * ca)

    hull = [S(-.5, -.06), S(.5, -.1), S(.47, -.02), S(.4, .06), S(-.46, .06), S(-.5, .02)]
    cv.obj([hull], 1.)
    cv.line(_inside([[S(-.52, b), S(.52, b)] for b in [-.045 + i * .008 for i in range(15)]], hull))
    cv.hair([S(-.49, -.035), S(.49, -.07)])
    house = [S(-.44, -.055), S(-.44, -.19), S(-.38, -.23), S(-.25, -.23), S(-.25, -.065)]
    cv.obj([house], 1.)
    cv.hair(_inside([[S(-.34, b), S(-.24, b)] for b in [-.22 + i * .01 for i in range(16)]], house))
    cv.line([[S(-.42 + k * .035, -.2), S(-.405 + k * .035, -.2)] for k in range(4)])
    stack = [S(-.37, -.23), S(-.36, -.31), S(-.29, -.31), S(-.29, -.23)]
    cv.obj([stack], 1.)
    cv.hair(_inside([[S(-.38, -.24 - k * .012), S(-.28, -.24 - k * .012)] for k in range(7)], stack))
    for cx_ in (-.12, .05, .22):
        box = [S(cx_ - .075, -.065), S(cx_ - .075, -.13), S(cx_ + .075, -.135), S(cx_ + .075, -.075)]
        cv.obj([box], .5)
        cv.hair([[S(cx_ - .075 + k * .025, -.065), S(cx_ - .075 + k * .025, -.13)] for k in range(1, 6)])
    cv.line([S(.36, -.09), S(.36, -.34)])
    cv.hair([[S(.36, -.34), S(-.32, -.31)], [S(.36, -.34), S(.49, -.1)], [S(.36, -.27), S(.42, -.27)]])
    # smoke torn flat by the wind
    if detail >= 1:
        sm = []
        for j in range(4):
            px_, py_ = S(-.33, -.32 - j * .012)
            sm.append([(px_ - k * 2.5, py_ - k * .15 * (j + 1) + math.sin(k * .7 + j) * .8) for k in range(int(bw * .07))])
        cv.hair(sm)
    # bow wave: acanthus spray off the stem
    bwx, bwy = S(.48, -.04)
    C._finger(cv, bwx, bwy, -PI / 2 + .3, sl * .3, sl * .045, -.9, 3.8, .8)
    C._finger(cv, bwx, bwy, -PI / 2 - .5, sl * .26, sl * .04, -.6, -3.8, .8)

    # mid swells: each ruled crest hides those behind it
    def swell(v0, amp, nwav, ph, x0=-.03, x1=1.03):
        xs = [bx + bw * x0 + i * 2 for i in range(int(bw * (x1 - x0) / 2) + 2)]
        crest = [(x, by + bh * v0 - amp * bh * (.5 + .5 * math.sin((x - bx) / bw * TAU * nwav + ph)) ** 1.8) for x in xs]
        poly = crest + [(xs[-1], by + bh * 1.05), (xs[0], by + bh * 1.05)]
        cv.obj([poly], 0)
        cv.line([crest])
        lines = []
        for k in range(1, 45):
            off = k * 2.
            lines.append([(x, y + off + (.7 * math.sin(x / 7 + k * 1.3) if k > 3 else 0)) for x, y in crest])
        cv.hair(_inside(lines, poly))
        for i in range(1, len(crest) - 1):
            if crest[i][1] < crest[i - 1][1] and crest[i][1] <= crest[i + 1][1]:
                fx, fy = crest[i]
                cv.line([C._ell_pts(fx + 2, fy + .3, 5, 1.6, 12, PI, TAU)])
                cv.hair([C._ell_pts(fx + 4, fy + 1.4, 6, 2, 12, PI * 1.1, TAU)])

    swell(.66, .05, 3.3, seed % 5)
    if detail >= 1:
        swell(.78, .07, 2.2, 1 + seed % 3)

    # the great breaker of the bar, its lip rolling into a volute
    r = min(bw * .12, bh * .2)
    if detail < 1:
        r = bh * .22
    _breaker(cv, *P(.77, .72), r, by + bh * .9, bx + bw * .5, bx + bw * 1.05, False, seed, True, by + bh * 1.05)
    # a smaller comber pitching the other way, foreground left
    if detail >= 1:
        r2 = r * .62
        _breaker(cv, *P(.17, .83), r2, by + bh * .97, bx, bx + bw * .39, True, seed + 5, True, by + bh * 1.05)

    body = cv.svg()
    cid = C._uid("c02", bx, by, bw, bh, seed)
    return (f'<clipPath id="{cid}"><path d="{C._d(field, True, 0)}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g>')


# ------------------------------------------------------------------------------------------------
# the frame: a wide landscape cartouche, the bar is the hero
# ------------------------------------------------------------------------------------------------

def _warning(ctx):
    s = ((ctx or {}).get("sample") or "").lower()
    for key, words in (("hazardous seas", "HAZARDOUS SEAS WARNING"), ("gale", "GALE WARNING"),
                       ("storm warning", "STORM WARNING"), ("small craft", "SMALL CRAFT ADVISORY"),
                       ("high surf", "HIGH SURF ADVISORY"), ("sneaker", "SNEAKER WAVE ALERT"),
                       ("rip current", "RIP CURRENT STATEMENT")):
        if key in s:
            return words
    return "SURF ZONE FORECAST"


def _tall(w, h, seed, ctx, moon):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .16, 46), 74.)
    top_free = min(h * .05, 24.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw = pw * .64
    ch = min(ph * .8, cw * .9)
    cx, cy = w / 2, py0 + ph * .47
    occ = [("r", cx - cw / 2 + 4, cy - ch / 2 + 4, cx + cw / 2 - 4, cy + ch / 2 - 4)]
    cv = C.Canvas()
    main = C.Canvas()
    side_w = (pw - cw) / 2
    r1 = min(side_w * .48, ph * .22)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + side_w * .42)
        vy = py0 + ph - r1 * 1.15
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(side_w * .42, ph * .19)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + side_w * .36)
        vy = py0 + r2 * 1.15
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .035), rmax=r1 * .8,
                   max_n=11, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t2", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a = iw / 2 / _K + 6 - .3
    b = ih / 2 / _K + 6 - .3
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, C._superellipse(cx, cy, a, b), moon, seed, 2))
    o.append(C.palmette(cx, cy - ch / 2 + 6, min(ch * .07 + top_free, 40), True, rng.randrange(1 << 20)))
    bh_ = min(17., max(13., ph * .055))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .5 - 1, cw * .9, bh_, .035, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_lettering("COLUMBIA RIVER BAR", centre, bh_ * .5, 1.12))
    py = h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_lettering(_warning(ctx), [(tx + 4, ty + th / 2 + .6), (tx + tw - 2, ty + th / 2 + .6)], min(th * .62, 9.), 1.18))
    return C.svg_doc(w, h, "".join(o))


def _medium(w, h, seed, ctx, moon):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .56, gh * 2.0)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    side_w = (w - cw) / 2
    r = min(gh * .44, side_w / 2.3)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r * 1.05)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .065), rmax=r * .8,
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m2", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a = iw / 2 / _K + 6 - .3
    b = ih / 2 / _K + 6 - .3
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, C._superellipse(cx, cy, a, b), moon, seed, 1))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return C.svg_doc(w, h, "".join(o))


def plate(w, h, ctx):
    ctx = ctx or {}
    date = (ctx.get("date") or "2026-11-11")[:10]
    seed = sum(map(ord, date)) + 17 * int(ctx.get("sheet", 0) or 0)
    try:
        y, m, d = (int(t) for t in date.split("-"))
        days = (datetime.date(y, m, d) - datetime.date(2000, 1, 6)).days
    except Exception:
        days = 0
    moon = (days % 29.530588) / 29.530588
    if h < 110:
        def fill(x, y, iw, ih):
            cx, cy = x + iw / 2, y + ih / 2
            rx = iw / 2 / .7071 + 5 - 2.2
            ry = ih / 2 / .7071 + 5 - 2.2
            return _scene(cx - rx, cy - ry, 2 * rx, 2 * ry, C._ell_pts(cx, cy, rx, ry, 64), moon, seed, 0)
        return C.frame_plate(w, h, seed, fill)
    if h <= 260:
        return _medium(w, h, seed, ctx, moon)
    return _tall(w, h, seed, ctx, moon)
