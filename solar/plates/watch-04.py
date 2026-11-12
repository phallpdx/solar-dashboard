"""watch-04: Classic movie of the day -- Psycho (Hitchcock, 1960).

The vignette is the Bates house: a Second Empire mansion with its mansard tower on the hill, a
lit upstairs window with Mother's silhouette, a dead tree, crows, a night sky ruled dark round a
moon of today's phase. Tall plates add the Bates Motel and its sign at the foot of the hill, a
ribbon lettered PSYCHO and a pedestal whose tablet is a strip of film lettered HITCHCOCK; two
crows perch on the frame. Easter egg: a Sauvie Island great blue heron flies through the moon's
glow among Norman's birds.
"""
import sys
import math
import random
import datetime
import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, pat, dark_ground, _d, _n, _ell_pts, _superellipse, _uid

_CR = C._CR

# ------------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------------


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _blk(polys, fill="#000"):
    polys = [p for p in polys if p and len(p) > 2]
    if not polys:
        return ""
    return f'<path d="{"".join(_d(p, True, 0) for p in polys)}" fill="{fill}" stroke="none"/>'


def _strokes(lines, w, col="#000"):
    lines = [l for l in lines if l and len(l) > 1]
    if not lines:
        return ""
    return f'<path d="{"".join(_d(l, False, 0) for l in lines)}" fill="none" stroke="{col}" stroke-width="{_n(w)}"/>'


def _clipg(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _moon_phase(date):
    try:
        d = datetime.datetime.strptime(date[:10], "%Y-%m-%d") + datetime.timedelta(hours=12)
    except Exception:
        return .3
    n = datetime.datetime(2000, 1, 6, 18, 14)
    return ((d - n).total_seconds() / 86400 / 29.530588) % 1.


# stroke font on a 4 x 6 grid (y down)
_GLYPH = {
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "M": [[(0, 6), (0, 0), (2, 3.5), (4, 0), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 4)], [(1.4, 2.6), (4, 6)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 3.8), (3.2, 3.8)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (4, 1), (4, 2), (3, 3)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
}


def _text_lines(txt, cx, cy, s, track=2.2, pts=None):
    """Polylines for txt centred on (cx, cy), letter height 6*s; if pts (a centre line) is given
    the letters follow it."""
    n = len(txt)
    wid = (n * 4 + (n - 1) * track) * s
    x = cx - wid / 2
    out = []
    for ch in txt:
        g = _GLYPH.get(ch)
        if g:
            if pts:
                mx = x + 2 * s
                yoff = _interp_y(pts, mx) - cy
            else:
                yoff = 0
            for pl in g:
                out.append([(x + gx * s, cy - 3 * s + gy * s + yoff) for gx, gy in pl])
        x += (4 + track) * s
    return out


def _interp_y(pts, x):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0 or 1)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]


def _smooth(t):
    t = max(0., min(1., t))
    return t * t * (3 - 2 * t)


def _profile(ctrl, t):
    """Piecewise smooth interpolation through (t, v) control points."""
    for (t0, v0), (t1, v1) in zip(ctrl, ctrl[1:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * _smooth((t - t0) / (t1 - t0))
    return ctrl[0][1] if t < ctrl[0][0] else ctrl[-1][1]


# ------------------------------------------------------------------------------------------------
# birds
# ------------------------------------------------------------------------------------------------

def _crow_flying(x, y, s, flap, rng):
    """A crow in flight: two swept wings and a body, black. s = half span."""
    up = flap
    lw = [(x, y), (x - s * .45, y - s * .32 * up), (x - s, y - s * .05 * up + s * .12),
          (x - s * .5, y - s * .1 * up + s * .02), (x - s * .12, y + s * .12)]
    rw = [(2 * x - px, py) for px, py in lw]
    body = _ell_pts(x, y + s * .05, s * .26, s * .1, 10)
    return [lw, rw[::-1], body]


def _heron(x, y, s, d=1):
    """Great blue heron in flight (the Sauvie Island egg): neck folded back in an S, bill forward,
    legs trailing, broad bowed wings. s about half span. d = +1 flies right."""
    def P(px, py):
        return (x + d * px * s, y + py * s)
    body = [P(-.42, .0), P(-.2, -.07), P(.12, -.08), P(.24, -.03), P(.1, .07), P(-.3, .06)]
    neck = [P(.16, -.07), P(.3, -.04), P(.36, .07), P(.43, .06), P(.45, -.03), P(.42, -.09), P(.3, -.1)]
    head = [P(.4, -.1), P(.49, -.12), P(.8, -.05), P(.49, -.04), P(.42, -.03)]
    plume = [P(.44, -.11), P(.3, -.16), P(.42, -.13)]
    wing_up = [P(-.02, -.06), P(-.18, -.42), P(-.42, -.7), P(-.66, -.74), P(-.56, -.56), P(-.48, -.3),
               P(-.36, -.12), P(-.22, -.04)]
    wing_dn = [P(.02, .02), P(-.1, .26), P(-.32, .44), P(-.46, .44), P(-.36, .26), P(-.24, .08)]
    legs = [[P(-.38, .02), P(-1.0, .06)], [P(-.38, .04), P(-.98, .11)]]
    body = body
    neck = neck + plume[:0]
    return [body, neck, head, wing_up, wing_dn], legs


def _crow_perched(x, y, s, d=1):
    """A crow perched on a ledge at (x, y): s = height. Facing d."""
    def P(px, py):
        return (x + d * px * s, y + py * s)
    body = [P(-.05, -.02), P(-.3, -.35), P(-.22, -.6), P(-.02, -.72), P(.16, -.74), P(.26, -.86),
            P(.3, -.98), P(.42, -1.0), P(.52, -.94), P(.7, -.9), P(.52, -.86), P(.46, -.8),
            P(.32, -.58), P(.2, -.35), P(.08, -.16), P(.0, -.02)]
    tail = [P(-.22, -.42), P(-.62, -.02), P(-.52, .02), P(-.1, -.3)]
    feet = [[P(-.04, -.12), P(-.06, 0)], [P(.04, -.12), P(.06, 0)]]
    feather = [[P(-.18, -.46), P(.12, -.68)], [P(-.2, -.36), P(.1, -.55)], [P(-.16, -.27), P(.08, -.42)]]
    eye = P(.4, -.92)
    return [body, tail], feet, feather, eye


# ------------------------------------------------------------------------------------------------
# the scene: the Bates house on the hill
# ------------------------------------------------------------------------------------------------

def scene(clip_d, X, Y, W, H, mode, seed, date):
    """Everything inside the field bbox X,Y,W,H, clipped to clip_d. mode: 'tall' | 'med' | 'small'."""
    rng = random.Random(seed)
    small = mode == "small"
    tall = mode == "tall"
    out = []
    pad = 3

    # ---- geometry
    mR = min(W, H) * (.1 if not small else .13)
    mx, my = X + W * (.22 if not small else .26), Y + H * (.25 if not small else .32)
    if tall:
        crest = [(0, .76), (.3, .7), (.48, .6), (.86, .58), (1., .62)]
    elif small:
        crest = [(0, .9), (.3, .82), (.46, .76), (.86, .74), (1., .78)]
    else:
        crest = [(0, .86), (.3, .8), (.46, .7), (.86, .68), (1., .72)]

    def cy_at(x):
        return Y + H * _profile(crest, (x - X) / W)

    # ---- sky (back canvas)
    back = Canvas()
    back.obj([_rect(X - pad, Y - pad, W + 2 * pad, H + 2 * pad)], 0)
    G = mR * 2.3
    y = math.floor(Y - pad)
    yb = Y + H + pad
    while y < yb:
        f = (y - Y) / H
        dy = y - my
        segs = []
        if abs(dy) < G:
            gx = math.sqrt(G * G - dy * dy)
            segs = [(X - pad, mx - gx, False), (mx - gx, mx + gx, True), (mx + gx, X + W + pad, False)]
        else:
            segs = [(X - pad, X + W + pad, False)]
        yi = int(round(y))
        for a, b, glow in segs:
            if b - a < .5:
                continue
            if glow:
                if yi % 3 == 0:
                    back.hair([(a, yi + .25), (b, yi + .25)])
            elif f < .32:
                if yi % 2 == 0:
                    back.line([(a, yi), (b, yi)])
            elif f < .5:
                if yi % 2 == 0:
                    back.line([(a, yi), (b, yi)]) if (yi // 2) % 2 == 0 else back.hair([(a, yi + .25), (b, yi + .25)])
            else:
                if yi % 2 == 0:
                    back.hair([(a, yi + .25), (b, yi + .25)])
        y += 1

    # moon (today's phase)
    ph = _moon_phase(date)
    k = math.cos(TAU * ph)
    disc = _ell_pts(mx, my, mR, mR, 80)[:-1]
    back.obj([disc], 1.)
    side = -1 if ph < .5 else 1          # dark side: left while waxing
    dark = []
    for i in range(25):
        t = -PI / 2 + PI * i / 24
        dark.append((mx + side * mR * math.cos(t), my + mR * math.sin(t)))
    for i in range(25):
        t = PI / 2 - PI * i / 24
        dark.append((mx - side * mR * k * math.cos(t), my + mR * math.sin(t)))
    lit_frac = (1 - k) / 2
    if lit_frac < .97:
        back.hair(hatch_poly(dark, 45, 2))
        back.hair(hatch_poly(dark, -45, 3))
    # maria and craters on the whole disc (hidden in the dark part by the hatch anyway)
    for (u, v, a, b, ang) in ((-.3, -.25, .32, .22, .3), (.25, -.05, .28, .34, -.2), (-.05, .35, .35, .2, .1),
                              (.42, .4, .14, .12, 0)):
        bl = [(mx + mR * (u + a * math.cos(t) * math.cos(ang) - b * math.sin(t) * math.sin(ang) * (1 + .15 * math.sin(3 * t))),
               my + mR * (v + a * math.cos(t) * math.sin(ang) + b * math.sin(t) * math.cos(ang) * (1 + .15 * math.sin(3 * t))))
              for t in [TAU * j / 18 for j in range(18)]]
        back.hair(hatch_poly(bl, 0, 3))
    # limb shading on the lit side (bulino arcs)
    for f in (.86, .93):
        arc = [(mx + mR * f * math.cos(t), my + mR * f * math.sin(t)) for t in
               [(-side) * 0 + (PI / 2 + PI * j / 20 if side > 0 else -PI / 2 + PI * j / 20) for j in range(21)]]
        back.hair(arc)
    # stipple over the lit face
    st = []
    for j in range(int(mR * mR * .12)):
        r = mR * math.sqrt(rng.random()) * .8
        t = rng.random() * TAU
        st.append([(mx + r * math.cos(t), my + r * math.sin(t)), (mx + r * math.cos(t) + .5, my + r * math.sin(t))])
    back.hair(st)

    # clouds drifting across
    if not small:
        for (u, v, L, T) in ((-.05, .5, .42, .04), (.55, .14, .5, .035)):
            cx0, cy0 = X + W * u, Y + H * v
            Lp, Tp = W * L, H * T + 3
            top = [(cx0 + Lp * i / 30, cy0 - Tp * (.4 + .6 * abs(math.sin(i / 30 * PI * 3.2 + u * 9))) * math.sin(PI * i / 30) ** .5)
                   for i in range(31)]
            bot = [(cx0 + Lp * (1 - i / 30), cy0 + Tp * .35 * math.sin(PI * i / 30)) for i in range(31)]
            cl = top + bot
            back.obj([cl], .5)
            back.hair(hatch_poly(cl, 0, 3, 1.25))
            back.hair(hatch_poly([(p[0], p[1]) for p in bot] + [(q[0], cy0 - Tp * .15) for q in bot[::-1]], 45, 2))
    out.append(back.svg())

    # ---- birds in the sky (black): crows and the heron
    birds = []
    nb = 2 if small else (5 if tall else 4)
    for i in range(nb):
        bx = X + W * (.45 + .4 * rng.random())
        by_ = Y + H * (.1 + .22 * rng.random())
        birds += _crow_flying(bx, by_, max(2.2, min(W, H) * rng.uniform(.018, .03)), rng.choice((1, -.6, .4)), rng)
    hs = max(5., mR * (1.05 if not small else .8))
    hb, legs = _heron(mx - mR * .55, my + mR * 1.45, hs, -1)
    birds += hb
    out.append(_blk(birds))
    out.append(_strokes(legs + [[l[0], (l[1][0] + .1, l[1][1])] for l in legs[:0]], 1. if hs > 7 else .5))

    # ---- hill, tree, stairs, house (mid canvas)
    mid = Canvas()
    # dead tree
    tx = X + W * (.3 if not small else .25)
    tby = cy_at(tx) + 2
    TL = H * (.32 if tall else .36)
    tl_lines = {1.5: [], 1.: [], .5: []}

    def branch(x0, y0, ang, L, depth):
        pts = [(x0, y0)]
        x, y = x0, y0
        a = ang
        for j in range(5):
            a += rng.uniform(-.22, .22)
            x += math.cos(a) * L / 5
            y += math.sin(a) * L / 5
            pts.append((x, y))
        w = 1.5 if depth == 0 else (1. if depth < 2 else .5)
        tl_lines[w].append(pts)
        if depth < (3 if not small else 2):
            nkid = 2 if depth else 3
            for c in range(nkid):
                aa = a + (c - (nkid - 1) / 2) * rng.uniform(.5, .8) + rng.uniform(-.15, .15)
                f = rng.uniform(.4, .75)
                px_, py_ = pts[int(len(pts) * rng.uniform(.5, 1)) - 1] if depth else pts[-1]
                branch(px_, py_, aa, L * f, depth + 1)
    branch(tx, tby, -PI / 2 - .08, TL * .55, 0)
    mid.obj([], 0)
    # trunk mass: a few parallel heavy strokes
    trunk = [(tx - 1.5, tby + 1), (tx - .6, tby - TL * .55 * .7)]
    mid.heavy([trunk, [(tx + 1.2, tby + 1), (tx + .2, tby - TL * .55 * .5)],
               [(tx - 3, tby + 1), (tx - 1.4, tby - 3)], [(tx + 2.8, tby + 1), (tx + 1.2, tby - 3)]])
    mid.line([[(tx - .2, tby), (tx - .9, tby - TL * .55 * .85)], [(tx + .6, tby), (tx - .3, tby - TL * .55 * .8)]])
    for w_, ls in tl_lines.items():
        mid._add(w_, ls)

    # hill
    hill_top = [(X - pad + (W + 2 * pad) * i / 60, cy_at(X - pad + (W + 2 * pad) * i / 60)) for i in range(61)]
    hill = hill_top + [(X + W + pad, Y + H + pad), (X - pad, Y + H + pad)]
    mid.obj([hill], 1.)
    for j in range(1, 80):
        off = j * 2
        ln = [(px, py + off) for px, py in hill_top]
        if ln[0][1] > Y + H + pad and ln[-1][1] > Y + H + pad:
            break
        mid.hair(ln)
    deep = [(px, py + H * .08) for px, py in hill_top] + [(X + W + pad, Y + H + pad), (X - pad, Y + H + pad)]
    mid.hair(hatch_poly(deep, 45, 3))
    deeper = [(px, py + H * .16) for px, py in hill_top] + [(X + W + pad, Y + H + pad), (X - pad, Y + H + pad)]
    mid.hair(hatch_poly(deeper, -45, 3))
    grass = []
    gx = X - pad
    while gx < X + W + pad:
        gy = cy_at(gx)
        ln = rng.uniform(1.5, 3.5) * (1 if not small else .6)
        grass.append([(gx, gy + .5), (gx + rng.uniform(-1, 1.2), gy - ln)])
        gx += rng.uniform(1.4, 2.6)
    mid.hair(grass)

    # house
    u = min(H * (.5 if tall else (.62 if small else .58)), W * .55) / 100
    hx = X + W * (.6 if not small else .6)
    x0 = hx - 50 * u
    by = Y + H * _profile(crest, (hx - X) / W) + 1.5 * u
    blk = []
    whitebits = []
    fine = u > .8

    def wall_h(poly, pitch=3):
        mid.hair(hatch_poly(poly, 0, pitch, .25))

    # side wall (receding right) and its roof
    sx0 = x0 + 90 * u
    sw = 16 * u
    side_wall = [(sx0, by), (sx0, by - 50 * u), (sx0 + sw, by - 55 * u), (sx0 + sw, by - 4 * u)]
    mid.obj([side_wall], 1.)
    mid.hair(hatch_poly(side_wall, 0, 1.5, .25))
    mid.hair(hatch_poly(side_wall, 45, 3))
    side_roof = [(sx0 + 3 * u, by - 50 * u), (sx0 + sw + 3 * u, by - 55 * u), (sx0 + sw - 4 * u, by - 75 * u), (sx0 - 4 * u, by - 70 * u)]
    mid.obj([side_roof], 1.)
    mid.line(hatch_poly(side_roof, 90, 2))
    mid.hair(hatch_poly(side_roof, 45, 3))
    for j in range(2):
        wy = by - (44 - j * 27) * u
        win = [(sx0 + 5 * u, wy + 1.5 * u), (sx0 + 10 * u, wy), (sx0 + 10 * u, wy + 12 * u), (sx0 + 5 * u, wy + 13.5 * u)]
        blk.append(win)

    # front block
    front = _rect(x0, by - 50 * u, 90 * u, 50 * u)
    mid.obj([front], 1.)
    wall_h(front, 3 if fine else 2)
    # shadow band under the cornice and down the corners
    mid.hair(hatch_poly(_rect(x0, by - 50 * u, 90 * u, 4 * u), 45, 1.5))
    mid.hair(hatch_poly(_rect(sx0 - 3 * u, by - 50 * u, 3 * u, 50 * u), 45, 2))
    # mansard roof
    roof = ([(x0 - 3 * u, by - 50 * u)] +
            [(x0 - 3 * u + 7 * u * math.sin(t * PI / 2) ** .7, by - 50 * u - 20 * u * t) for t in [i / 8 for i in range(1, 9)]] +
            [(x0 + 93 * u - 7 * u * math.sin(t * PI / 2) ** .7, by - 50 * u - 20 * u * t) for t in [i / 8 for i in range(8, -1, -1)]])
    mid.obj([roof], 1.)
    mid.hair(hatch_poly(roof, 90, 1.5))
    for j in range(1, 7):
        yy = by - 50 * u - j * 3 * u
        mid.hair([(x0 - 3 * u, yy), (x0 + 93 * u, yy)])
    mid.hair(hatch_poly([(x0 - 3 * u, by - 50 * u), (x0 + 93 * u, by - 50 * u), (x0 + 92 * u, by - 56 * u), (x0 - 2 * u, by - 56 * u)], 45, 3))
    # chimneys
    for cxu in (40, 76):
        ch = _rect(x0 + cxu * u, by - 80 * u, 4.5 * u, 11 * u)
        mid.obj([ch], 1.)
        mid.hair(hatch_poly(ch, 0, 1.5, .25))
        blk.append(_rect(x0 + (cxu - .8) * u, by - 81.5 * u, 6.1 * u, 2 * u))
    # cresting on the main roof
    blk.append(_rect(x0 + 3 * u, by - 71 * u, 84 * u, 1.2 * u))
    cres = []
    if u > .45:
        cx_ = x0 + 4 * u
        while cx_ < x0 + 86 * u:
            cres.append([(cx_, by - 71 * u), (cx_, by - 73.5 * u)])
            cx_ += max(1.5, 2 * u)
        mid.obj([], 0)
        mid.hair(cres)
    # cornice (black) with white brackets
    blk.append(_rect(x0 - 3.5 * u, by - 51.5 * u, 97 * u, 2.2 * u))
    # dormers
    for dxu in (42, 60, 78):
        dx = x0 + dxu * u
        dor = [(dx - 4.5 * u, by - 52 * u), (dx - 4.5 * u, by - 63 * u), (dx, by - 67 * u), (dx + 4.5 * u, by - 63 * u), (dx + 4.5 * u, by - 52 * u)]
        mid.obj([dor], 1.)
        if fine:
            wall_h(dor, 3)
        blk.append([(dx - 2.4 * u, by - 53 * u)] + [(dx + 2.4 * u * math.cos(t), by - 60 * u - 2.4 * u * math.sin(t)) for t in [PI - PI * i / 8 for i in range(9)]] + [(dx + 2.4 * u, by - 53 * u)])
    # second floor windows
    lit = None
    for i, wxu in enumerate((40, 53, 66, 79)):
        wx = x0 + wxu * u
        top = by - 45 * u
        mid.line([(wx - 4.2 * u, top - .5 * u)] + [(wx + 4.2 * u * math.cos(t), top - .5 * u - 2 * u * math.sin(t)) for t in [PI - PI * j / 8 for j in range(9)]])
        mid.line([(wx - 4 * u, top + 14.5 * u), (wx + 4 * u, top + 14.5 * u)])
        r = _rect(wx - 3 * u, top, 6 * u, 13 * u)
        if i == 0:
            lit = (wx, top, u)
        else:
            blk.append(r)
    # porch on the right part of the ground floor
    px0, px1 = x0 + 33 * u, x0 + 92 * u
    pwall = _rect(px0, by - 19 * u, px1 - px0 - 2 * u, 19 * u)
    mid.obj([pwall], 0)
    mid.hair(hatch_poly(pwall, 45, 1.5))
    mid.hair(hatch_poly(pwall, 0, 3, .25))
    proof = [(px0 - 1 * u, by - 18 * u), (px0 + 1 * u, by - 23 * u), (px1 + 1 * u, by - 23 * u), (px1 + 2 * u, by - 18 * u)]
    mid.obj([proof], 1.)
    mid.hair(hatch_poly(proof, 90, 2))
    ncol = 6
    for j in range(ncol + 1):
        cxp = px0 + (px1 - px0) * j / ncol
        col = _rect(cxp - .9 * u, by - 18 * u, 1.8 * u, 17 * u)
        mid.obj([col], .5)
    rail = _rect(px0, by - 8 * u, px1 - px0, 1 * u)
    mid.obj([rail], .5)
    if fine:
        bal = []
        xb = px0 + 1
        while xb < px1:
            bal.append([(xb, by - 7 * u), (xb, by - 1.5 * u)])
            xb += 2
        mid.obj([], 0)
        mid.hair(bal)
    floor = _rect(px0 - 1 * u, by - 1.5 * u, px1 - px0 + 3 * u, 1.5 * u)
    mid.obj([floor], .5)
    blk.append(_rect(px0 - 1 * u, by - 18.5 * u, px1 - px0 + 3 * u, 1.3 * u))
    # tower (left front), drawn last so it stands proud
    t0, t1 = x0 + 6 * u, x0 + 30 * u
    tw = _rect(t0, by - 80 * u, t1 - t0, 80 * u)
    tside = [(t1, by), (t1, by - 80 * u), (t1 + 3.5 * u, by - 81 * u), (t1 + 3.5 * u, by - 1 * u)]
    mid.obj([tside], 1.)
    mid.hair(hatch_poly(tside, 0, 1.5, .25))
    mid.hair(hatch_poly(tside, 45, 2))
    mid.obj([tw], 1.)
    wall_h(tw, 3 if fine else 2)
    mid.hair(hatch_poly(_rect(t0, by - 80 * u, t1 - t0, 4 * u), 45, 1.5))
    mid.hair(hatch_poly(_rect(t0, by - 51 * u, t1 - t0, 3 * u), 45, 1.5))
    troof = ([(t0 - 2.5 * u, by - 80 * u)] +
             [(t0 - 2.5 * u + 6 * u * math.sin(t * PI / 2) ** .7, by - 80 * u - 22 * u * t) for t in [i / 8 for i in range(1, 9)]] +
             [(t1 + 2.5 * u - 6 * u * math.sin(t * PI / 2) ** .7, by - 80 * u - 22 * u * t) for t in [i / 8 for i in range(8, -1, -1)]])
    mid.obj([troof], 1.)
    mid.hair(hatch_poly(troof, 90, 1.5))
    for j in range(1, 7):
        yy = by - 80 * u - j * 3.2 * u
        mid.hair([(t0 - 3 * u, yy), (t1 + 3 * u, yy)])
    blk.append(_rect(t0 - 3 * u, by - 81.5 * u, t1 - t0 + 6 * u, 2.2 * u))
    blk.append(_rect(t0 + 2.5 * u, by - 103 * u, t1 - t0 - 5 * u, 1.2 * u))
    tcx = (t0 + t1) / 2
    if u > .45:
        cr = []
        xx = t0 + 3.5 * u
        while xx < t1 - 3 * u:
            cr.append([(xx, by - 102 * u), (xx, by - 105.5 * u)])
            xx += max(1.5, 2 * u)
        mid.obj([], 0)
        mid.hair(cr)
        mid.line([(tcx, by - 102 * u), (tcx, by - 110 * u)])
    blk.append(_ell_pts(tcx, by - 91 * u, 2.6 * u, 3.6 * u, 16)[:-1])
    for (top, hh) in ((by - 76 * u, 15 * u), (by - 46 * u, 15 * u), (by - 17 * u, 15 * u)):
        mid.line([(tcx - 5.2 * u, top - .5 * u)] + [(tcx + 5.2 * u * math.cos(t), top - .5 * u - 2.6 * u * math.sin(t)) for t in [PI - PI * j / 8 for j in range(9)]])
        mid.line([(tcx - 5 * u, top + hh + 1.2 * u), (tcx + 5 * u, top + hh + 1.2 * u)])
        blk.append([(tcx - 3.6 * u, top + hh)] + [(tcx + 3.6 * u * math.cos(t), top + 2 * u - 2 * u * math.sin(t)) for t in [PI - PI * j / 8 for j in range(9)]] + [(tcx + 3.6 * u, top + hh)])
    # front door under the porch
    blk.append(_rect(x0 + 60 * u, by - 15 * u, 6 * u, 13.5 * u))
    # stairs down the hill toward the lower left
    sx = px0 + 22 * u
    s_top = (sx, by + .5)
    s_bot = (X + W * (.48 if tall else .4), Y + H + pad)
    if tall:
        s_bot = (X + W * .46, Y + H * .86)
    stair = [(s_top[0] - 3.5 * u, s_top[1]), (s_top[0] + 3.5 * u, s_top[1]),
             (s_bot[0] + 6 * u, s_bot[1]), (s_bot[0] - 6 * u, s_bot[1])]
    if u > .45:
        mid.obj([stair], 0)
        mid.hair(hatch_poly(stair, 0, 3, .25))
        mid.line([[stair[0], stair[3]], [stair[1], stair[2]]])
    out.append(mid.svg())
    out.append(_blk(blk))
    # window muntins and glints on big plates
    if fine:
        out.append(_strokes([[(x0 + wxu * u, by - 45 * u), (x0 + wxu * u, by - 32 * u)] for wxu in (53, 66, 79)], .5, "#fff"))
    # Mother's lit window
    wx, top, uu = lit
    out.append(_blk([_rect(wx - 3 * u, top, 6 * u, 13 * u)], "#fff"))
    mother = [_ell_pts(wx + .4 * u, top + 5 * u, 1.3 * u, 1.5 * u, 12)[:-1],
              [(wx - 2.2 * u, top + 13 * u), (wx - 1.6 * u, top + 8.5 * u), (wx - .3 * u, top + 6.8 * u),
               (wx + 1.4 * u, top + 6.8 * u), (wx + 2.4 * u, top + 9 * u), (wx + 2.6 * u, top + 13 * u)],
              _ell_pts(wx + .6 * u, top + 3.4 * u, .9 * u, .7 * u, 8)[:-1]]
    out.append(_blk(mother))
    sash = [[(wx - 3 * u, top), (wx + 3 * u, top), (wx + 3 * u, top + 13 * u), (wx - 3 * u, top + 13 * u), (wx - 3 * u, top)]]
    out.append(_strokes(sash + ([[(wx - 3 * u, top + 6.5 * u), (wx - 1.4 * u, top + 6.5 * u)]] if fine else []), .5))

    # ---- the Bates Motel at the foot of the hill (tall)
    if tall:
        mot = Canvas()
        mb = Y + H * .95
        mt = mb - H * .1
        m0, m1 = X + W * .02, X + W * .56
        ground = [(X - pad, Y + H * .88), (X + W + pad, Y + H * .86), (X + W + pad, Y + H + pad), (X - pad, Y + H + pad)]
        mot.obj([ground], .5)
        mot.hair(hatch_poly(ground, 0, 2, .25))
        mot.hair(hatch_poly(ground, 45, 3))
        wall = _rect(m0, mt, m1 - m0, mb - mt)
        mot.obj([wall], 1.)
        mot.hair(hatch_poly(wall, 90, 2))
        office = _rect(m1 - 2, mt - H * .03, W * .12, mb - mt + H * .03)
        mot.obj([office], 1.)
        mot.hair(hatch_poly(office, 0, 3, .25))
        roofb = [(m0 - 3, mt - 3), (m1, mt - 3), (m1, mt + 1), (m0 - 3, mt + 1)]
        mot.obj([roofb], 1.)
        mot.hair(hatch_poly(roofb, 0, 1.5, .25))
        oroof = [(m1 - 4, mt - H * .03 - 3.5), (m1 + W * .12 + 3, mt - H * .03 - 3.5), (m1 + W * .12 + 3, mt - H * .03), (m1 - 4, mt - H * .03)]
        mot.obj([oroof], 1.)
        mot.hair(hatch_poly(oroof, 0, 1.5, .25))
        out.append(mot.svg())
        mblk = []
        n = 6
        span = (m1 - m0) / n
        for j in range(n):
            dx = m0 + span * j + span * .18
            mblk.append(_rect(dx, mt + (mb - mt) * .3, span * .2, (mb - mt) * .7 - .5))
            mblk.append(_rect(dx + span * .36, mt + (mb - mt) * .3, span * .42, (mb - mt) * .35))
        mblk.append(_rect(m0 - 3, mt + 1, m1 - m0 + 3, 1.2))
        # office: lit window and door
        ox = m1 + W * .015
        mblk.append(_rect(ox + W * .06, mt + (mb - mt) * .25, W * .03, (mb - mt) * .75 - .5))
        # sign on a pole
        sxp = m1 + W * .2
        sy0 = mt - H * .14
        sw_, sh_ = W * .17, H * .055
        mblk.append(_rect(sxp - 1, sy0 + sh_, 2, mb - sy0 - sh_))
        mblk.append(_rect(sxp - sw_ / 2, sy0, sw_, sh_))
        out.append(_blk(mblk))
        out.append(_blk([_rect(ox + W * .005, mt + (mb - mt) * .25, W * .045, (mb - mt) * .4)], "#fff"))
        s = min(sh_ * .62 / 6, sw_ / 34)
        out.append(_strokes(_text_lines("MOTEL", sxp, sy0 + sh_ / 2, s, 2.4), 1. if s > .9 else .5, "#fff"))
        out.append(_strokes([_rect(sxp - sw_ / 2 + 1.5, sy0 + 1.5, sw_ - 3, sh_ - 3) + [(sxp - sw_ / 2 + 1.5, sy0 + 1.5)]], .5, "#fff"))

    cid = _uid("w04", X, Y, W, H, mode)
    return _clipg(cid, clip_d, "".join(out))


PI = math.pi
TAU = 2 * PI


# ------------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex so the vignette fills the whole field)
# ------------------------------------------------------------------------------------------------

def _cartouche_open(cx, cy, w, h, seed):
    """codex cartouche, without its white field, plus the field outline to clip the scene to."""
    svg, rect, inner_d = C.cartouche(cx, cy, w, h, seed)
    first = svg.find("/>") + 2          # drop the white field fill
    svg = svg[first:]
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    field = _superellipse(cx, cy, a - 5, b - 5)
    ring = _superellipse(cx, cy, a, b)
    under = f'<path d="{_d(ring, True, .1)}" fill="#fff" stroke="none"/>'
    return under, svg, _d(field, True, .1), (cx - a + 5, cy - b + 5, 2 * a - 10, 2 * b - 10)


def _band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 128)
    o.append(C._clip(_uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx + 1, ry + 1, 64), True)}" fill="#fff" stroke="none"/>')
    clip = _ell_pts(cx, cy, rx - 3.5, ry - 3.5, 64)
    o.append(scene(_d(clip, True, .1), cx - rx + 3.5, cy - ry + 3.5, 2 * rx - 7, 2 * ry - 7, "small", seed, ctx.get("date", "")))
    ring = _d(_ell_pts(cx, cy, rx + 1, ry + 1, 64), True) + _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def _medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(dark_ground((0, gy0, w, gh), "G"))
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    under, frame, clip_d, (X, Y, W, H) = _cartouche_open(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(under)
    o.append(scene(clip_d, X, Y, W, H, "med", seed, ctx.get("date", "")))
    o.append(frame)
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tablet_film(tx, ty, tw, th):
    """The pedestal's tablet as a strip of film: sprocket holes along both edges, frame gates,
    and HITCHCOCK in white across the middle frames."""
    o = [f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#000" stroke="none"/>']
    s = max(.8, min((th - 5) / 6, 1.8))
    txt_w = (9 * 4 + 8 * 2.4) * s
    hole_h = max(1.5, min(2.5, th * .13))
    holes = []
    x = tx + 3
    while x < tx + tw - 4:
        if abs(x + 1 - (tx + tw / 2)) > txt_w / 2 + 5:
            holes.append(_rect(x, ty + 1.5, 2, hole_h))
            holes.append(_rect(x, ty + th - 1.5 - hole_h, 2, hole_h))
        x += 5
    o.append(_blk(holes, "#fff"))
    tl = _text_lines("HITCHCOCK", tx + tw / 2, ty + th / 2, s, 2.4)
    o.append(_strokes(tl, 1. if s >= .9 else .5, "#fff"))
    b0, b1 = ty + 2.5 + hole_h, ty + th - 2.5 - hole_h
    bh = b1 - b0
    fl, hl = [], []
    fw = max(6., bh * 1.4)
    for sd in (-1, 1):
        x = tx + tw / 2 + sd * (txt_w / 2 + 7)
        while (sd > 0 and x + fw < tx + tw - 3) or (sd < 0 and x - fw > tx + 3):
            x0 = x if sd > 0 else x - fw
            fl.append(_rect(x0, b0, fw, bh) + [(x0, b0)])
            hl += hatch_poly(_rect(x0 + 1, b0 + 1, fw - 2, bh - 2), 45, 3)
            x += sd * (fw + 2.5)
    o.append(_strokes(fl + hl, .5, "#fff"))
    return "".join(o)


def _tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(dark_ground((0, 0, w, top_free + 1), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .16, ph * .24)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .2)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    under, frame, clip_d, (X, Y, W, H) = _cartouche_open(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(under)
    o.append(scene(clip_d, X, Y, W, H, "tall", seed, ctx.get("date", "")))
    o.append(frame)
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, max(12, ph * .05))
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.25, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    s = min(bh * .55 / 6, 1.6)
    o.append(_strokes(_text_lines("PSYCHO", cx, cy + ch * .47, s, 2.6, centre), 1.5 if s > 1.2 else 1.))
    tw_ = (6 * 4 + 5 * 2.6) * s / 2 + 7
    bc = cy + ch * .47
    side_l = []
    for off in (-.32, -.1, .12, .34):
        for a0, a1 in ((centre[0][0] + 3, cx - tw_), (cx + tw_, centre[-1][0] - 3)):
            pts_ = [(x_, _interp_y(centre, x_) + off * bh) for x_ in [a0 + (a1 - a0) * i / 12 for i in range(13)]]
            side_l.append(pts_)
    o.append(_strokes(side_l, .5))
    dia = []
    for sd in (-1, 1):
        dx_ = cx + sd * (tw_ - 3.5)
        dy_ = _interp_y(centre, dx_)
        dia.append([(dx_ - 2.2, dy_), (dx_, dy_ - 2.2), (dx_ + 2.2, dy_), (dx_, dy_ + 2.2)])
    o.append(_blk(dia))
    # perched crows on the frame's top rail
    cro, feet, fea, eyes = [], [], [], []
    for sd in (-1, 1):
        bxc = cx + sd * pw * .475
        b, f, fe, e = _crow_perched(bxc, py0 - 3.5, min(22., top_free * .95 + 2), -sd)
        cro += b
        feet += f
        fea += fe
        eyes.append(e)
    o.append(_blk(cro))
    o.append(_strokes(feet, 1.))
    o.append(_strokes(fea, .5, "#fff"))
    o.append(_blk([_ell_pts(ex, ey, .6, .6, 6)[:-1] for ex, ey in eyes], "#fff"))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(dark_ground((0, py + 2, w, h - py - 2), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet_film(tx + 1, ty + 1, tw - 2, th - 2))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(_uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 4
    if h < 110:
        body = _band(w, h, seed, ctx)
    elif h <= 260:
        body = _medium(w, h, seed, ctx)
    else:
        body = _tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
