"""local-01 "New to try": New Deal Distillery's Nocino, the 2026 green-walnut liqueur.

The plate is a still life of the Nocino inside the house scroll frame: a dark bottle with a wax
capsule, a cordial glass, green walnuts (one split to show the shell) on an oak board, and a
walnut branch hanging over them. In the frame the volutes curl round green walnuts, so the fruit
grows out of the acanthus. Easter egg: the wax seal on the bottle's neck is stamped with a tiny
"P" monogram (Parker's own bottle)."""
import sys
import math
import random
import engraving_codex as C
import engraving_morning as EM

PI = math.pi
_n, _d, _ell = C._n, C._d, C._ell_pts


# ---------------------------------------------------------------------------------------------
# small geometry helpers
# ---------------------------------------------------------------------------------------------

def _rot(p, c, a):
    s, k = math.sin(a), math.cos(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * k - y * s, c[1] + x * s + y * k)


def _curve(x, y, ang, L, bend, n=24):
    """A gently bending centre line: start (x, y), heading ang (rad), total turn `bend` (rad)."""
    pts = [(x, y)]
    a = ang - bend / 2
    ds = L / n
    for i in range(n):
        a += bend / n
        x += math.cos(a) * ds
        y += math.sin(a) * ds
        pts.append((x, y))
    return pts


def _offset(cl, wf):
    """Left/right edges of a centre line with half-width wf(t)."""
    n = len(cl)
    L, R = [], []
    for i in range(n):
        a, b = cl[max(0, i - 1)], cl[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        w = wf(i / (n - 1), i)
        L.append((cl[i][0] + nx * w, cl[i][1] + ny * w))
        R.append((cl[i][0] - nx * w, cl[i][1] - ny * w))
    return L, R


# ---------------------------------------------------------------------------------------------
# the walnut vocabulary
# ---------------------------------------------------------------------------------------------

def leaflet(cv, x, y, ang, L, W, bend=.25, flipshade=False, rng=None):
    """One walnut leaflet: a long serrated lance with midrib, paired veins, the shadow half
    hatched along the veins and the lit half ruled lightly near the rib only."""
    rng = rng or random.Random(1)
    cl = _curve(x, y, ang, L, bend, max(10, int(L / 2.5)))
    n = len(cl)

    def wf(t, i):
        w = W * math.sin(PI * min(1, t ** .8)) ** .85
        if .1 < t < .94 and L > 18:
            w *= 1 + (.07 if i % 2 else -.04)
        return w
    Lft, Rgt = _offset(cl, wf)
    poly = Lft + Rgt[::-1]
    cv.obj([poly], 1.)
    sh, li = (Rgt, Lft) if not flipshade else (Lft, Rgt)
    half = cl + sh[::-1]
    deg = math.degrees(ang + bend * .2)
    side = 1 if not flipshade else -1
    cv.hair(C.hatch_poly(half, deg - side * 38, 1.5, rng.random()))
    # a darker band under the rib on the shadow side
    inner = [((c[0] * .55 + s[0] * .45), (c[1] * .55 + s[1] * .45)) for c, s in zip(cl, sh)]
    cv.line(inner[2:-3])
    # lit half: light rule next to the rib, the outer half stays as highlight with veins
    mid = [((c[0] * .55 + s[0] * .45), (c[1] * .55 + s[1] * .45)) for c, s in zip(cl, li)]
    cv.hair(C.hatch_poly(cl + mid[::-1], deg + side * 38, 3, rng.random()))
    # veins: forward-swept from the rib to the edge, both sides
    k = 3
    while k < n - 3:
        for edge in (Lft, Rgt):
            j = min(n - 1, k + 3)
            cv.hair([cl[k], ((cl[k][0] + edge[j][0]) / 2 * .4 + edge[j][0] * .6 - edge[j][0] * .0,
                             (cl[k][1] + edge[j][1]) / 2 * .4 + edge[j][1] * .6),
                     edge[j]])
        k += 3
    cv.line(cl[1:-2])


def compound_leaf(cv, x, y, ang, L, pairs=3, scale=1., bend=.4, rng=None, droop=1):
    """A pinnate walnut leaf: a rachis with `pairs` pairs of leaflets and one at the tip."""
    rng = rng or random.Random(2)
    rach = _curve(x, y, ang, L, bend, 30)
    lw = max(1.1, 1.4 * scale)
    Lr, Rr = _offset(rach, lambda t, i: lw * (1 - .5 * t))
    # leaflets laid from the tip back so the ones nearer the twig lie on top
    ll = L * .48 * scale
    tip = rach[-1]
    a_t = math.atan2(rach[-1][1] - rach[-2][1], rach[-1][0] - rach[-2][0])
    leaflet(cv, tip[0], tip[1], a_t, ll * 1.05, ll * .2, bend * .4, rng.random() < .5, rng)
    for p in range(pairs, 0, -1):
        t = p / (pairs + .6)
        i = int(t * (len(rach) - 1))
        a = math.atan2(rach[i + 1][1] - rach[i][1], rach[i + 1][0] - rach[i][0])
        size = ll * (.62 + .38 * t)
        for sgn in (-1, 1):
            spread = sgn * (.95 - .25 * t) * rng.uniform(.9, 1.1)
            leaflet(cv, rach[i][0], rach[i][1], a + spread, size, size * .2,
                    -sgn * .35 * droop, sgn < 0, rng)
    cv.obj([Lr + Rr[::-1]], 1.)
    cv.line(Rr[1:-1])


def twig(cv, pts, w0, w1):
    """A woody twig: rib with bark lines and a shaded underside."""
    Lt, Rt = _offset(pts, lambda t, i: w0 + (w1 - w0) * t)
    cv.obj([Lt + Rt[::-1]], 1.)
    for f in (.2, .4, .58, .72, .84):
        cv.hair([(a[0] * (1 - f) + b[0] * f, a[1] * (1 - f) + b[1] * f) for a, b in zip(pts, Rt)][1:-1])
    for f in (.45, .8):
        cv.hair([(a[0] * (1 - f) + b[0] * f, a[1] * (1 - f) + b[1] * f) for a, b in zip(pts, Lt)][2:-2])
    cv.line([(a[0] * .15 + b[0] * .85, a[1] * .15 + b[1] * .85) for a, b in zip(pts, Rt)][1:-1])
    # bark nicks on the lit side
    for i in range(2, len(pts) - 2, 3):
        a, b = pts[i], Lt[i]
        cv.hair([(a[0] * .4 + b[0] * .6, a[1] * .4 + b[1] * .6), (a[0] * .1 + b[0] * .9, a[1] * .1 + b[1] * .9)])


def walnut(cv, cx, cy, r, tilt=0., rng=None, light=(-.6, -.7)):
    """A green walnut in its husk: an oval fruit modelled with meridians that thicken and crowd
    into the shadowed limb, a cross-hatched crescent, a clean highlight, a few lenticel ticks and
    the stalk stub on top."""
    rng = rng or random.Random(3)
    rx, ry = r, r * 1.08
    c0 = (cx, cy)
    out = [_rot(p, c0, tilt) for p in _ell(cx, cy, rx, ry, max(24, int(r * 3)))[:-1]]
    cv.obj([out], 1.)
    hx, hy = -.38, -.42   # highlight centre (unit coords)
    nm = max(6, int(r / 1.25))
    for k in range(1, nm):
        s = -1 + 2 * k / nm
        seg, segs = [], []
        for j in range(25):
            t = PI * j / 24
            ux, uy = s * math.sin(t), -math.cos(t)
            if (ux - hx) ** 2 / .09 + (uy - hy) ** 2 / .07 < 1 or abs(uy) > .97:
                if len(seg) > 1:
                    segs.append(seg)
                seg = []
                continue
            seg.append(_rot((cx + rx * ux, cy + ry * uy), c0, tilt))
        if len(seg) > 1:
            segs.append(seg)
        if s > .45:
            cv.line(segs)
        elif s > -.5 or k % 2 == 0:
            cv.hair(segs)
    # the shadowed crescent: lower right limb, crossed
    cres = []
    for j in range(25):
        t = -PI * .2 + PI * 1.2 * j / 24
        cres.append(_rot((cx + rx * .98 * math.cos(t), cy + ry * .98 * math.sin(t)), c0, tilt))
    for j in range(24, -1, -1):
        t = -PI * .2 + PI * 1.2 * j / 24
        cres.append(_rot((cx + rx * .66 * math.cos(t) - rx * .2, cy + ry * .7 * math.sin(t) - ry * .18), c0, tilt))
    cv.hair(C.hatch_poly(cres, -35 + math.degrees(tilt), 2, .3))
    cv.heavy([_rot((cx + rx * .93 * math.cos(t), cy + ry * .93 * math.sin(t)), c0, tilt)
              for t in [-PI * .05 + PI * .75 * j / 14 for j in range(15)]])
    # lenticels: short ticks on the lit half
    for _ in range(max(2, int(r * .55))):
        a = rng.uniform(0, 2 * PI)
        q = math.sqrt(rng.random()) * .75
        ux, uy = q * math.cos(a), q * math.sin(a)
        if ux * light[0] + uy * light[1] > .05 and (ux - hx) ** 2 / .09 + (uy - hy) ** 2 / .07 > 1.2:
            p = _rot((cx + rx * ux, cy + ry * uy), c0, tilt)
            cv.hair([p, (p[0] + .8, p[1] + .3)])
    top = _rot((cx, cy - ry), c0, tilt)
    cv.obj([_ell(top[0], top[1] + .6, max(1.4, r * .2), max(.8, r * .1), 12)[:-1]], 1.)
    return top


def hop_cone(cv, cx, cy, L, W, tilt=0., rng=None):
    """A hop cone (Cascade, fresh from the bine): rows of pointed bracts overlapping downward,
    each with its midrib and a hatched shadow on the side away from the light."""
    rng = rng or random.Random(5)
    c0 = (cx, cy)
    rows = max(4, int(L / max(3.2, W * .38)))
    top = cy - L / 2
    stem = [_rot((cx, top - L * .12), c0, tilt), _rot((cx, top + 1), c0, tilt)]
    cv.obj([], 0)
    cv.heavy([stem])
    bh = L / rows * 1.55
    for i in range(rows - 1, -1, -1):
        t = (i + .5) / rows
        prof = math.sin(PI * min(1, .12 + .95 * t)) ** .7
        half = W / 2 * prof
        y = top + L * t
        cols = (-1, 0, 1) if half > 4 else (-.5, .5)
        for j, cc in enumerate(sorted(cols, key=lambda c: -abs(c))):
            bx = cx + cc * half * .62 + (.18 * half if i % 2 else 0) * (1 if cc <= 0 else -1) * .5
            bw = half * (.62 if cc else .75)
            if bw < 1.5:
                continue
            br = [(bx - bw, y - bh * .5), (bx - bw * .8, y), (bx - bw * .35, y + bh * .38), (bx, y + bh * .55),
                  (bx + bw * .35, y + bh * .38), (bx + bw * .8, y), (bx + bw, y - bh * .5)]
            br = [_rot(p, c0, tilt) for p in br]
            cv.obj([br], 1.)
            mid = [_rot((bx, y - bh * .1), c0, tilt), _rot((bx + .2, y + bh * .45), c0, tilt)]
            cv.hair(mid)
            shade = [_rot(p, c0, tilt) for p in [(bx + .3, y - bh * .5), (bx + bw, y - bh * .5), (bx + bw * .8, y),
                                                 (bx + bw * .35, y + bh * .38), (bx + .3, y + bh * .5)]]
            if cc >= 0:
                cv.hair(C.hatch_poly(shade, 70 + math.degrees(tilt), 1.5, rng.random()))
            else:
                cv.hair(C.hatch_poly(shade, 70 + math.degrees(tilt), 3, rng.random()))
    return stem[0]


def split_walnut(cv, cx, cy, r, rng=None):
    """A green walnut with its husk peeled back: the wrinkled shell inside, with its seam."""
    rng = rng or random.Random(4)
    walnut(cv, cx, cy, r, 0, rng)
    # the opened husk: a dark ring, then the shell
    sr = r * .74
    cv.obj([_ell(cx + r * .08, cy - r * .05, sr + 1.6, sr * 1.08 + 1.6, 30)[:-1]], 0)
    q = sr + 1.2
    while q > sr - .2:
        cv.line(_ell(cx + r * .08, cy - r * .05, q, q * 1.08, 30))
        q -= .8
    sx, sy = cx + r * .08, cy - r * .05
    shell = _ell(sx, sy, sr, sr * 1.08, 30)[:-1]
    cv.obj([shell], 1.)
    # wrinkles: wavy meridians, plus a shaded side
    for k in range(-3, 4):
        s = k / 4
        pts = []
        for j in range(17):
            t = PI * j / 16
            wob = .09 * sr * math.sin(j * 1.9 + k * 2.3)
            pts.append((sx + sr * s * math.sin(t) + wob, sy - sr * 1.08 * math.cos(t)))
        cv.hair(pts[1:-1])
    for j in range(5):
        t = .3 + j * .45
        cv.hair([(sx + sr * .5 * math.cos(t), sy + sr * .5 * math.sin(t)),
                 (sx + sr * .85 * math.cos(t + .3), sy + sr * .9 * math.sin(t + .3))])
    cres = [(sx + sr * math.cos(t), sy + sr * 1.08 * math.sin(t)) for t in [PI * (-.3 + .9 * i / 16) for i in range(17)]]
    cres += [(sx + sr * .55 * math.cos(t) + sr * .2, sy + sr * .8 * math.sin(t)) for t in [PI * (.6 - .9 * i / 16) for i in range(17)]]
    cv.hair(C.hatch_poly(cres, 45, 1.5))
    cv.heavy([(sx, sy - sr * 1.08), (sx - sr * .06, sy), (sx, sy + sr * 1.08)])


def tiny_p(cv, x, y, h):
    """The Easter egg: a little engraved P, centred on (x, y), cap height h."""
    k = h
    stem = [(x - .25 * k, y - .5 * k), (x - .25 * k, y + .5 * k)]
    bowl = [(x - .25 * k, y - .5 * k)] + [(x - .05 * k + .3 * k * math.sin(PI * i / 10), y - .5 * k + .25 * k * (1 - math.cos(PI * i / 10))) for i in range(11)] + [(x - .25 * k, y)]
    cv.line(stem)
    cv.line(bowl)
    cv.hair([(x - .42 * k, y + .5 * k), (x - .08 * k, y + .5 * k)])


def letters(cv, s, x, y, h, w=1.):
    polys, width = EM._text_polys(s, x, y, h, 1.3, True)
    (cv.line if w >= 1 else cv.hair)(polys)
    return width


# ---------------------------------------------------------------------------------------------
# the bottle, the glass, the board
# ---------------------------------------------------------------------------------------------

def _bottle_hw(t, hw):
    """Half width of the bottle at height fraction t (0 base, 1 top)."""
    neck = hw * .27
    if t < .04:
        return hw * (.9 + 2.5 * t)
    if t < .56:
        return hw
    if t < .72:
        u = (t - .56) / .16
        return neck + (hw - neck) * (.5 + .5 * math.cos(PI * u)) ** .9
    if t < .885:
        return neck * (1 + .06 * (t - .72) / .16)
    if t < .905:
        return neck * 1.28   # the lip ring
    return neck * 1.22       # wax capsule


def bottle(cv, x, base, H, hw, rng):
    n = 70
    ts = [i / n for i in range(n + 1)]
    R = [(x + _bottle_hw(t, hw), base - t * H) for t in ts]
    Lp = [(x - _bottle_hw(t, hw), base - t * H) for t in ts]
    body = R + Lp[::-1]
    cv.obj([body], 1.5)
    # dark glass: form lines that follow the profile; a highlight band left, a reflection right
    # dark glass: 1.5 px lines 2.5 px apart (60 %); the core shadow and far rim solid
    def run(s, lo=.012, hi=.885, w=1.):
        pts = [(x + s * _bottle_hw(t, hw) * .97, base - t * H) for t in ts if lo < t < hi]
        (cv.line if w == 1. else cv.heavy)(pts)
    s = -1.
    step = 2.5 / hw
    while s <= 1.:
        if not (-.7 < s < -.38) and not (.12 < s < .2):
            dense = s > .32 or s < -.86
            run(s, hi=.885, w=1.5)
            if dense:
                run(s + step * .5, hi=.62, w=1.5)
        s += step
    # the neck stays dark: fill it between the shoulder and the lip
    for s in (-.9, -.25, .25, .7, .9):
        run(s, lo=.6, hi=.885)
    # the highlight band: one hair down its middle, broken
    cv.hair([(x - .5 * hw, base - t * H) for t in ts if .08 < t < .3])
    cv.hair([(x - .5 * hw, base - t * H) for t in ts if .48 < t < .6])
    cv.hair([(x - .48 * _bottle_hw(t, hw), base - t * H) for t in ts if .6 < t < .85])
    # base: a curved heel
    cv.heavy(_ell(x, base - H * .012, hw * .92, hw * .12, 30, 0, PI))
    # the label
    ly0, ly1 = base - .44 * H, base - .14 * H
    lab = [(x - hw + .5, ly0)] + [(x - hw + 2 * hw * i / 20 - .5 * (i == 20) + .5 * (i == 0),
                                   ly0 + hw * .1 * math.sin(PI * i / 20)) for i in range(21)][1:] + \
          [(x + hw - .5, ly1)] + [(x + hw - 2 * hw * i / 20, ly1 + hw * .1 * math.sin(PI * i / 20)) for i in range(21)][1:]
    cv.obj([lab], 1.)
    cv.hair(C.hatch_poly(lab, 0, 3, .5))
    # curvature shade on the label's right
    cv.hair(C.hatch_poly([(x + hw * .55, ly0), (x + hw, ly0), (x + hw, ly1 + hw * .1), (x + hw * .55, ly1 + hw * .1)], 90, 1.5))
    cv.line(C.hatch_poly([(x + hw * .82, ly0), (x + hw, ly0), (x + hw, ly1 + hw * .1), (x + hw * .82, ly1 + hw * .1)], 90, 1.5, .75))
    # border rules
    m = hw * .14
    cv.hair([(x - hw + m, ly0 + m), (x + hw - m, ly0 + m)])
    cv.hair([(x - hw + m, ly1 - m + hw * .1), (x + hw - m, ly1 - m + hw * .1)])
    # lettering: NOCINO, a sprig, the year
    lh = (ly1 - ly0)
    capw = hw * 1.5
    ch = min(lh * .17, capw / 6.4 / .78)
    # white plate for letters so they read
    tw = ch * 6.3 * .78
    tb = [(x - tw / 2 - 1.5, ly0 + lh * .32 - 1.5), (x + tw / 2 + 1.5, ly0 + lh * .32 - 1.5),
          (x + tw / 2 + 1.5, ly0 + lh * .32 + ch + 1.5), (x - tw / 2 - 1.5, ly0 + lh * .32 + ch + 1.5)]
    cv.obj([tb], 0)
    letters(cv, "NOCINO", x, ly0 + lh * .32, ch, 1)
    yb = ly0 + lh * .62
    tb2 = [(x - ch * 2.3, yb - 1), (x + ch * 2.3, yb - 1), (x + ch * 2.3, yb + ch * .8 + 1), (x - ch * 2.3, yb + ch * .8 + 1)]
    cv.obj([tb2], 0)
    letters(cv, "2026", x, yb, ch * .8, .5)
    # a walnut leaf sprig across the top of the label
    cv.hair([(x - hw * .5, ly0 + lh * .2), (x, ly0 + lh * .14), (x + hw * .5, ly0 + lh * .2)])
    cv.line(_ell(x, ly0 + lh * .15, 1.2, 1.2, 8))
    # the lip ring and wax capsule with drips
    t0, t1 = .885, .905
    neck = hw * .27
    cap = [(x - neck * 1.22, base - .905 * H)]
    nd = 6
    for i in range(nd + 1):
        u = i / nd
        drip = (.03 + .025 * rng.random()) if i % 2 else 0
        cap.append((x - neck * 1.22 + 2 * neck * 1.22 * u, base - (.905 - drip) * H))
    cap += [(x + neck * 1.22, base - H), (x - neck * 1.22, base - H)]
    cap = [cap[0]] + cap[1:-2] + [(x + neck * 1.22, base - .985 * H)] + \
        [(x + neck * 1.22 * math.cos(PI * i / 8), base - .985 * H - neck * .5 * math.sin(PI * i / 8)) for i in range(9)]
    cv.obj([cap], 1.)
    yy = base - .99 * H
    while yy < base - .905 * H + .03 * H:
        cv.line([(x - neck * 1.22, yy), (x + neck * 1.22, yy)])
        yy += .8
    cv.obj([[(x - neck * .7, base - .975 * H), (x - neck * .35, base - .975 * H),
             (x - neck * .35, base - .92 * H), (x - neck * .7, base - .92 * H)]], 0)
    cv.hair([(x - neck * .52, base - .97 * H), (x - neck * .52, base - .925 * H)])
    ring = [(x - neck * 1.32, base - t1 * H), (x + neck * 1.32, base - t1 * H),
            (x + neck * 1.32, base - t0 * H), (x - neck * 1.32, base - t0 * H)]
    cv.obj([ring], 1.)
    cv.hair(C.hatch_poly(ring, 90, 1.5, .4))
    # the seal: a wax disc on the neck, stamped with P  (the Easter egg)
    sr = max(3.2, neck * 1.05)
    sx, sy = x + neck * .1, base - .8 * H
    cv.obj([_ell(sx, sy, sr, sr, 18)[:-1]], 1.)
    cv.hair(_ell(sx, sy, sr - 1.1, sr - 1.1, 18))
    tiny_p(cv, sx, sy, sr * .95)


def cordial(cv, x, base, H, bw, rng):
    """A stemmed cordial glass, the dark liqueur in its bowl."""
    foot_h = H * .06
    stem_t = H * .45
    bowl_b = base - stem_t
    rim = base - H
    # foot
    foot = _ell(x, base - foot_h * .5, bw * .9, foot_h, 28)[:-1]
    cv.obj([foot], 1.)
    cv.hair(C.hatch_poly(foot, 0, 1.5))
    # stem with a knop
    st = [(x - 1.2, base - foot_h), (x - 1, bowl_b + 4), (x - 2.4, bowl_b + 2), (x - 1.5, bowl_b),
          (x + 1.5, bowl_b), (x + 2.4, bowl_b + 2), (x + 1, bowl_b + 4), (x + 1.2, base - foot_h)]
    cv.obj([st], 1.)
    cv.hair([(x + .6, base - foot_h - 1), (x + .5, bowl_b + 4)])
    # bowl: a tulip
    n = 20
    bowl_r = [(x + bw * math.sin(PI / 2 * (i / n)) ** .7 * (1 - .12 * (i / n) ** 3), bowl_b - (bowl_b - rim) * (i / n)) for i in range(n + 1)]
    bowl = bowl_r + [(2 * x - p[0], p[1]) for p in bowl_r[::-1]]
    cv.obj([bowl], 1.)
    lvl = bowl_b - (bowl_b - rim) * .62
    liq = [p for p in bowl if p[1] >= lvl - .01]
    hw_l = max(p[0] for p in bowl_r if p[1] >= lvl) - x
    liq = [(x - hw_l, lvl)] + [p for p in bowl_r[::-1] if p[1] > lvl][::-1][::-1]
    liq = [(x + hw_l, lvl)] + [p for p in bowl_r if p[1] > lvl][::-1] + [(2 * x - p[0], p[1]) for p in bowl_r if p[1] > lvl] + [(x - hw_l, lvl)]
    cv.line(C.hatch_poly(liq, 0, 1.5, .2))
    cv.hair(C.hatch_poly(liq, 80, 3))
    cv.line(_ell(x, lvl, hw_l, 1.2, 22))
    # empty glass above: thin ruling so it isn't blank paper; a highlight left
    air = [p for p in bowl if p[1] < lvl]
    cv.hair(C.hatch_poly([(x - hw_l, lvl)] + [(2 * x - p[0], p[1]) for p in bowl_r if p[1] < lvl] +
                         [p for p in bowl_r if p[1] < lvl][::-1] + [(x + hw_l, lvl)], 90, 3, 1.))
    cv.line(_ell(x, rim, bw * .88, 1.6, 26))
    cv.obj([[(x - bw * .62, lvl + 2), (x - bw * .48, lvl + 2), (x - bw * .4, bowl_b - 2), (x - bw * .55, bowl_b - 3)]], 0)


def board(cv, x0, x1, ytop, ydepth, yfront, rng):
    """The oak board: a top in perspective with grain and knots, a dark front edge."""
    top = [(x0, ytop), (x1, ytop), (x1, ytop + ydepth), (x0, ytop + ydepth)]
    cv.obj([top], 1.)
    y = ytop + 1.6
    k = 0
    while y < ytop + ydepth - .8:
        ph = rng.random() * 6
        pts = [(xx, y + .5 * math.sin(xx * .05 + ph) + .35 * math.sin(xx * .17 + k)) for xx in range(int(x0), int(x1) + 1, 3)]
        cv.hair(pts)
        y += 2. + (k % 3 == 0) * 1.
        k += 1
    for _ in range(2):
        kx = rng.uniform(x0 + 20, x1 - 20)
        ky = ytop + ydepth * rng.uniform(.3, .7)
        cv.obj([_ell(kx, ky, 4.5, 1.6, 16)[:-1]], 0)
        cv.hair(_ell(kx, ky, 4.2, 1.4, 16))
        cv.line(_ell(kx, ky, 1.6, .6, 10))
    front = [(x0, ytop + ydepth), (x1, ytop + ydepth), (x1, yfront), (x0, yfront)]
    cv.obj([front], 1.)
    yy = ytop + ydepth + 2.2
    while yy < yfront:
        cv.line([(x0, yy), (x1, yy)])
        yy += 1.5
    cv.heavy([(x0, ytop + ydepth + .8), (x1, ytop + ydepth + .8)])


def pot_still(cv, x, base, a, b):
    """New Deal's copper pot still in the background: a riveted onion pot, a helmet and the swan
    neck (lyne arm) rising out of the field; copper shown in mid-tone form lines."""
    pr = a * .34
    H = b * .62
    n = 40

    def prof(t):
        if t < .55:
            return pr * (.82 + .18 * math.sin(PI * (t / .55) * .9 + .2))
        u = (t - .55) / .45
        return pr * .14 + (pr * .97 - pr * .14) * (.5 + .5 * math.cos(PI * u)) ** 1.1
    R = [(x + prof(i / n), base - H * i / n) for i in range(n + 1)]
    L = [(x - prof(i / n), base - H * i / n) for i in range(n + 1)]
    cv.obj([R + L[::-1]], 1.)
    k = 0
    s = -.96
    while s < .97:
        pts = [(x + s * prof(i / n), base - H * i / n) for i in range(n + 1)]
        if s > .35:
            cv.line(pts[1:-1])
        elif not (-.55 < s < -.25):
            cv.hair(pts[1:-1])
        s += 2.2 / pr
        k += 1
    # riveted seam and the belly band
    for tt in (.18, .42):
        yy = base - H * tt
        cv.line([(x + prof(tt) * math.sin(PI * (j / 24 - .5)), yy + 1.6 * math.cos(PI * (j / 24 - .5))) for j in range(25)])
        for j in range(1, 12):
            u = math.sin(PI * (j / 12 - .5))
            cv.line([(x + prof(tt) * u - .3, yy + 1.6 * math.cos(PI * (j / 12 - .5)) - 1.6),
                     (x + prof(tt) * u + .3, yy + 1.6 * math.cos(PI * (j / 12 - .5)) - 1.6)])
    # the helmet (a ball) and the swan neck leaving the field
    hy = base - H - pr * .3
    hr = pr * .36
    arm = [(x, hy)] + [(x - pr * .2 - pr * 1.7 * j / 10, hy - pr * .55 - pr * .5 * (j / 10) ** .7) for j in range(11)]
    Lr, Rr = _offset(arm, lambda t, i: pr * (.11 - .04 * t))
    cv.obj([Lr + Rr[::-1]], 1.)
    for f in (.3, .6, .85):
        cv.hair([(p[0] * (1 - f) + q[0] * f, p[1] * (1 - f) + q[1] * f) for p, q in zip(arm, Lr)][1:])
    cv.line([(p[0] * .1 + q[0] * .9, p[1] * .1 + q[1] * .9) for p, q in zip(arm, Lr)][1:])
    ball = _ell(x, hy, hr, hr * .9, 26)[:-1]
    cv.obj([ball], 1.)
    for j in range(1, 7):
        s = -1 + 2 * j / 7
        pts = [(x + s * hr * math.sin(PI * i / 12), hy - hr * .9 * math.cos(PI * i / 12)) for i in range(13)]
        (cv.line if s > .3 else cv.hair)(pts[1:-1])
    cv.obj([[(x - pr * .16, base - H - 1), (x + pr * .16, base - H - 1), (x + pr * .16, hy + hr * .8), (x - pr * .16, hy + hr * .8)]], 1.)
    cv.hair(C.hatch_poly([(x, base - H - 1), (x + pr * .16, base - H - 1), (x + pr * .16, hy + hr * .8), (x, hy + hr * .8)], 90, 1.5))


def shadow_on(cv, x0, x1, y, depth):
    """A cast shadow lying on the board to the right of an object."""
    poly = [(x0, y), (x1, y - depth * .4), (x1 + depth * 1.2, y - depth * .1), (x0 + 4, y + depth * .3)]
    cv.hair(C.hatch_poly(poly, 0, 1.5, .5))
    cv.hair(C.hatch_poly(poly, 70, 3))


# ---------------------------------------------------------------------------------------------
# the vignettes
# ---------------------------------------------------------------------------------------------

def still_life(cx, cy, a, b, seed):
    """The Nocino still life in a field of half-axes a x b centred on (cx, cy). Returns SVG
    (caller clips to the field)."""
    rng = random.Random(seed)
    o = []
    x0, x1, y0, y1 = cx - a - 2, cx + a + 2, cy - b - 2, cy + b + 2
    # wall: a light ruled ground, darker toward the edges (a vignette of tone)
    o.append(f'<path d="M{_n(x0)},{_n(y0)}H{_n(x1)}V{_n(y1)}H{_n(x0)}z" fill="{C.pat("L")}"/>')
    edge = (_d(C._superellipse(cx, cy, a + 4, b + 4), True, .1) +
            _d(C._superellipse(cx, cy - b * .08, a * .82, b * .78)[::-1], True, .1))
    o.append(f'<path d="{edge}" fill="{C.pat("D")}" fill-rule="evenodd"/>')
    cv = C.Canvas()
    ytop = cy + b * .42
    ydep = b * .16
    # the distillery's pot still stands behind, at the left
    pot_still(cv, cx - a * .56, ytop + ydep * .3, a, b)
    # the branch hangs from the upper right, in front of the still
    br = _curve(cx + a * 1.1, cy - b * .5, PI * 1.1, a * 1.55, .55, 30)
    lr = random.Random(seed + 7)
    compound_leaf(cv, br[22][0], br[22][1], -PI * .95, a * .7, 2, .95, -.6, lr)
    compound_leaf(cv, br[27][0], br[27][1], PI * .62, b * .56, 2, .95, .45, lr)
    compound_leaf(cv, br[5][0], br[5][1], PI * .55, b * .8, 2, 1., -.35, lr)
    twig(cv, br, a * .05, a * .025)
    # a cluster of green walnuts hanging close under the twig
    wr = a * .13
    sp = br[13]
    for (dx, dy, k) in ((-.9, 1.25, 11), (.95, 1.45, 9)):
        hx, hy = sp[0] + dx * wr, sp[1] + dy * wr + wr * .2
        cv.obj([[(sp[0] - 1.2, sp[1]), (sp[0] + 1.2, sp[1]), (hx + 1, hy - wr * .9), (hx - 1, hy - wr * .9)]], 1.)
        walnut(cv, hx, hy, wr, -.25 * dx, random.Random(seed + k))
    compound_leaf(cv, br[12][0], br[12][1], PI * .3, b * .7, 2, .9, .5, lr)
    # the board
    board(cv, x0, x1, ytop, ydep, y1, rng)
    # bottle and glass
    bx = cx - a * .14
    H = b * 1.38
    hw = a * .22
    shadow_on(cv, bx + hw * .6, bx + hw * 2.8, ytop + ydep * .62, ydep * .7)
    gx = cx + a * .5
    shadow_on(cv, gx, gx + a * .3, ytop + ydep * .8, ydep * .4)
    bottle(cv, bx, ytop + ydep * .62, H, hw, rng)
    cordial(cv, gx, ytop + ydep * .85, b * .52, a * .13, rng)
    # walnuts on the board: a whole one left, a split one at the bottle's foot, a fallen leaflet
    leaflet(cv, cx - a * .95, ytop + ydep * .9, -.12, a * .45, a * .08, .2, False, rng)
    walnut(cv, cx - a * .62, ytop + ydep * .55 - a * .11, a * .12, -.3, random.Random(seed + 3))
    hop_cone(cv, cx + a * .8, ytop + ydep * .45 - a * .06, a * .26, a * .15, 1.35, random.Random(seed + 8))
    split_walnut(cv, cx + a * .17, ytop + ydep * 1.05 - a * .12, a * .13, random.Random(seed + 5))
    o.append(cv.svg())
    return "".join(o)


def medallion_walnuts(cx, cy, rx, ry, seed):
    """For the short band: a green walnut and a split one, a leaflet behind, on stipple."""
    o = [f'<path d="{_d(_ell(cx, cy, rx + 1, ry + 1, 48), True)}" fill="{C.pat("L")}"/>']
    cv = C.Canvas()
    rr = min(ry * .42, rx * .3)
    leaflet(cv, cx - rx * .95, cy + ry * .1, -.35, rx * 1.25, ry * .2, .5, False, random.Random(seed))
    leaflet(cv, cx + rx * .95, cy + ry * .15, PI + .35, rx * 1.1, ry * .18, -.5, True, random.Random(seed + 1))
    walnut(cv, cx - rr * .9, cy + ry * .05, rr, -.25, random.Random(seed + 2))
    split_walnut(cv, cx + rr * .95, cy + ry * .12, rr * 1.02, random.Random(seed + 3))
    o.append(cv.svg())
    return "".join(o)


# ---------------------------------------------------------------------------------------------
# layouts (house layouts, with walnuts grown into the volutes and the field engraved edge to edge)
# ---------------------------------------------------------------------------------------------

def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _cart_axes(w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


def _volute_walnuts(cv, units, seed):
    """Green walnuts nested in the eyes of the big volutes: the fruit grows out of the scroll."""
    for k, (vx, vy, r) in enumerate(units):
        if k % 2 == 0:
            walnut(cv, vx, vy, r * .23, .3, random.Random(seed + 40 + k))
        else:
            hop_cone(cv, vx, vy + r * .04, r * .58, r * .36, -.25, random.Random(seed + 40 + k))


def layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 130)
    o.append(C._clip(C._uid("lb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    d = _d(_ell(cx, cy, rx - 3.6, ry - 3.6, 64), True)
    o.append(_field_clip(C._uid("lbf", w, h, seed), d, medallion_walnuts(cx, cy, rx - 4, ry - 4, seed)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.5)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    units = []
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
        units.append((vx, vy, r))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(10 * density), edge=.7, cv=cv)
    cv.extend(main)
    _volute_walnuts(cv, units, seed)
    o.append(C._clip(C._uid("lm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_axes(cw, gh + 4)
    o.append(_field_clip(C._uid("lmf", w, h, seed), inner, still_life(cx, cy, a, b, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, density=1.):
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
    cw, ch = pw * .46, ph * .62
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    units = []
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
        units.append((vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
        units.append((vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(8 * density), edge=.6, cv=cv)
    cv.extend(main)
    _volute_walnuts(cv, units, seed)
    o.append(C._clip(C._uid("lt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_axes(cw, ch)
    o.append(_field_clip(C._uid("ltf", w, h, seed), inner, still_life(cx, cy, a, b, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    # the ribbon, lettered NOCINO
    bh = min(16, ph * .05)
    bsvg, face = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lc = C.Canvas()
    lc.obj([], 0)
    word = "NEW DEAL · NOCINO · PORTLAND"
    capH = bh * .5
    polys, width = EM._text_polys(word, 0, 0, capH, 1.3, False)
    fx0, fx1 = face[0][0], face[-1][0]
    off = (fx0 + fx1) / 2 - width / 2

    def face_y(xx):
        f = (xx - fx0) / (fx1 - fx0) * (len(face) - 1)
        i = max(0, min(len(face) - 2, int(f)))
        return face[i][1] + (face[i + 1][1] - face[i][1]) * (f - i)
    lc.line([[(px + off, face_y(px + off) - capH / 2 + py) for px, py in p] for p in polys])
    o.append(lc.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: engraved, not blank: a walnut garland round the batch year
    o.append(tablet(tx, ty, tw, th, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("lf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def tablet(tx, ty, tw, th, seed):
    """Fill the pedestal's sunk tablet: light ruled ground, the year in the middle, a garland of
    walnut leaflets and nuts running out to both ends."""
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z" fill="{C.pat("L")}"/>']
    cv = C.Canvas()
    cx, cy = tx + tw / 2, ty + th / 2
    rng = random.Random(seed + 77)
    ch = min(th * .42, 9)
    for side in (-1, 1):
        x = cx + side * ch * 3.4
        k = 0
        while abs(x - cx) < tw / 2 - 8:
            ang = (0 if side > 0 else PI) + (.35 if k % 2 else -.35)
            leaflet(cv, x, cy, ang, th * .9, th * .17, (.4 if k % 2 else -.4) * side, k % 2 == 0, rng)
            x += side * th * .55
            k += 1
        cv.hair([(cx + side * ch * 3.2, cy), (x - side * th * .4, cy)])
    for side in (-1, 1):
        walnut(cv, cx + side * ch * 2.9, cy, th * .2, 0, random.Random(seed + 90 + side))
    tb = [(cx - ch * 2.2, cy - ch / 2 - 1.5), (cx + ch * 2.2, cy - ch / 2 - 1.5), (cx + ch * 2.2, cy + ch / 2 + 1.5), (cx - ch * 2.2, cy + ch / 2 + 1.5)]
    cv.obj([tb], 0)
    cv.hair(C.hatch_poly(tb, 0, 3, 1.4))
    letters(cv, "2026", cx, cy - ch / 2, ch, 1)
    o.append(cv.svg())
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 31 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = layout_band(w, h, seed)
    elif h <= 260:
        body = layout_medium(w, h, seed)
    else:
        body = layout_tall(w, h, seed, .95)
    # any paper the frame leaves (above the crest, beside the frieze) takes the page's own
    # diagonal ground, so the plate grows out of the page with no blank white
    ground = f'<path d="M0,0H{_n(w)}V{_n(h)}H0z" fill="{C.pat("D")}"/>'
    return C.svg_doc(w, h, ground + body)
