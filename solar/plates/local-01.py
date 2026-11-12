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
    o.append(f'<path d="M{_n(x0)},{_n(y0)}H{_n(x1)}V{_n(y1)}H{_n(x0)}z" fill="#fff"/>')
    o.append(f'<path d="M{_n(x0)},{_n(y0)}H{_n(x1)}V{_n(y1)}H{_n(x0)}z" fill="url(#s2o)"/>')
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
    thai_chili(cv, cx - a * .44, ytop + ydep * .95, a * .2, -.15, random.Random(seed + 6))
    o.append(cv.svg())
    return "".join(o)


def thai_chili(cv, x, y, L, ang, rng):
    """Easter egg: a prik kee noo, the little Thai chili, lying among the walnuts: a slim curved
    pod, glossy, shaded along its belly, with its star calyx and crooked stem."""
    pts = [(x + math.cos(ang + .35 * t * t) * L * t, y + math.sin(ang + .35 * t * t) * L * t) for t in [j / 12 for j in range(13)]]
    wf = lambda t: max(.35, L * .11 * (1 - t ** 1.6))
    Lt, Rt = _offset(pts, lambda t, i: wf(t))
    cv.obj([Lt + Rt[::-1]], 1.)
    cv.hair(C.hatch_poly(Rt + [(a[0] * .5 + b[0] * .5, a[1] * .5 + b[1] * .5) for a, b in zip(pts, Rt)][::-1], math.degrees(ang) + 60, 1.5, rng.random()))
    cv.hair([(a[0] * .6 + b[0] * .4, a[1] * .6 + b[1] * .4) for a, b in zip(pts, Lt)][2:-3])
    cx_, cy_ = pts[0]
    cv.obj([[(cx_ + L * .1 * math.cos(ang + math.pi + k * .9 - 1.8), cy_ + L * .1 * math.sin(ang + math.pi + k * .9 - 1.8)) for k in range(5)] + [(cx_, cy_)]], .5)
    cv.line([(cx_, cy_), (cx_ - L * .12 * math.cos(ang - .5), cy_ - L * .12 * math.sin(ang - .5)), (cx_ - L * .2 * math.cos(ang - .1), cy_ - L * .22 * math.sin(ang - .1))])


def medallion_walnuts(cx, cy, rx, ry, seed):
    """For the short band: a green walnut and a split one, a leaflet behind, on stipple."""
    o = [f'<path d="{_d(_ell(cx, cy, rx + 1, ry + 1, 48), True)}" fill="#fff"/>',
         f'<path d="{_d(_ell(cx, cy, rx + 1, ry + 1, 48), True)}" fill="url(#s2o)"/>']
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


# ---------------------------------------------------------------------------------------------
# the coast sheet: Pelican's IPA and Public Coast's peach sour and fresh-hop hazy
# ---------------------------------------------------------------------------------------------

def haystack(cv, x, base, H, W, rng):
    """Haystack Rock with the Needles: a broad basalt dome cut in contour lines that follow its
    flanks, crossed on the shadow side, white ledges catching the light, a grass cap and birds."""
    n = 32
    prof = []
    for j in range(n + 1):
        t = j / n
        lift = math.sin(PI * t) ** .75 * (1 - .18 * t) * (1 + .05 * math.sin(9 * t + 1.3) + .03 * math.sin(17 * t))
        prof.append((x - W / 2 + W * t, base - H * lift))
    rock = [(x - W / 2 - 2, base + 1)] + prof + [(x + W / 2 + 2, base + 1)]
    cv.obj([rock], 1.)
    for k in range(1, 10):
        f = 1 - k * .09
        cl = [(x - W * .12 + (px - x + W * .12) * f, base - (base - py) * f ** .5) for px, py in prof]
        cut = [q for q in cl if q[0] > x - W * .3 + k * W * .03]
        (cv.line if k > 6 else cv.hair)(cut)
    sh = [(x + W * .02, base)] + [q for q in prof if q[0] > x] + [(x + W / 2, base)]
    cv.hair(C.hatch_poly(sh, 65, 2, rng.random()))
    cv.hair(C.hatch_poly([(x - W * .5, base)] + [q for q in prof if q[0] <= x] + [(x, base)], 100, 3, rng.random()))
    cv.hair(C.hatch_poly([(x + W * .22, base)] + [q for q in prof if q[0] > x + W * .22] + [(x + W / 2, base)], -40, 2, rng.random()))
    for _ in range(7):
        lx = x + W * rng.uniform(-.32, .2)
        ly = base - H * rng.uniform(.12, .65)
        lw = W * rng.uniform(.05, .11)
        cv.obj([[(lx, ly), (lx + lw, ly - .6), (lx + lw * .9, ly + 1.4), (lx + lw * .1, ly + 1.6)]], 0)
        cv.line([(lx, ly + 1.6), (lx + lw * .9, ly + 1.4)])
    top = min(prof, key=lambda q: q[1])
    cv.hair([[(top[0] + dx, top[1] + 1.4 + abs(dx) * .15), (top[0] + dx + .6, top[1] - .6 + abs(dx) * .15)]
             for dx in [W * (-.2 + .03 * i) for i in range(14)]])
    for nx, nh, nw in ((x + W * .66, H * .38, W * .1), (x + W * .8, H * .22, W * .08)):
        nd = [(nx - nw / 2, base + 1), (nx - nw * .3, base - nh * .6), (nx - nw * .05, base - nh), (nx + nw * .2, base - nh * .8),
              (nx + nw / 2, base + 1)]
        cv.obj([nd], 1.)
        cv.hair(C.hatch_poly([(nx, base), (nx - nw * .05, base - nh), (nx + nw * .2, base - nh * .8), (nx + nw / 2, base)], 75, 1.5))
    for _ in range(5):
        gx, gy = x + W * rng.uniform(-.5, .6), base - H * rng.uniform(1.05, 1.35)
        g = max(1.5, W * .03)
        cv.line([(gx - g, gy - g * .2), (gx - g * .4, gy - g * .45), (gx, gy), (gx + g * .4, gy - g * .45), (gx + g, gy - g * .2)])


def pelican(cv, x, y, s, rng):
    """A brown pelican gliding left to right, neck drawn back, bill along the breast: the far wing
    foreshortened above, the near wing a long bowed blade with fingered primaries, all cut dark."""
    def P_(px, py):
        return (x + px * s, y + py * s)
    far = [P_(-.2, -.3), P_(-.9, -1.05), P_(-1.7, -1.45), P_(-1.95, -1.4), P_(-1.5, -1.0), P_(-.7, -.35)]
    cv.obj([far], 1.)
    cv.hair(C.hatch_poly(far, 40, 1.5, rng.random()))
    body = [P_(-1.4, -.05), P_(-.9, -.32), P_(.3, -.42), P_(1.0, -.3), P_(1.2, -.05), P_(.7, .25), P_(-.5, .22)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly(body, 80, 2, rng.random()))
    cv.line([P_(-1.3, .02), P_(-.4, .2), P_(.6, .22)])
    near = [P_(.35, -.2), P_(-.4, .0), P_(-1.4, .25), P_(-2.4, .38), P_(-3.1, .42)]
    for f in range(5):
        near.append(P_(-3.25 + f * .16, .5 + f * .07))
    near += [P_(-2.4, .6), P_(-1.3, .5), P_(-.3, .3)]
    cv.obj([near], 1.)
    cv.hair(C.hatch_poly(near, 8, 1.5, rng.random()))
    cv.hair(C.hatch_poly(near, -50, 2, rng.random()))
    cv.line([P_(.2, -.12), P_(-1.2, .3), P_(-2.6, .45)])
    neck = [P_(.9, -.3), P_(1.25, -.62), P_(1.6, -.6), P_(1.68, -.38), P_(1.35, -.05), P_(1.05, .05)]
    cv.obj([neck], 1.)
    cv.hair(C.hatch_poly(neck, 60, 3, .5))
    bill = [P_(1.55, -.62), P_(3.1, -.2), P_(3.15, -.08), P_(2.2, .12), P_(1.45, .05)]
    cv.obj([bill], 1.)
    cv.hair(C.hatch_poly([P_(1.6, -.25), P_(3.05, -.12), P_(2.2, .1), P_(1.5, .03)], 0, 1.5))
    cv.line([P_(1.6, -.4), P_(3.1, -.14)])
    cv.obj([C._ell_pts(*P_(1.48, -.48), max(.7, s * .08), max(.7, s * .08), 8)[:-1]], .5)
    cv.line([P_(-1.4, -.05), P_(-1.75, .02), P_(-1.4, .12)])


def peach(cv, x, y, r, rng):
    """A Willamette peach: a sphere with its cleft, blushed in contour lines on the shadow side."""
    out = C._ell_pts(x, y, r, r * .95, max(24, int(r * 3)))[:-1]
    cv.obj([out], 1.)
    for k in range(1, 7):
        f = k / 7
        arc = [(x + r * math.cos(t) * (1 - f * .12) + r * f * .25, y + r * .95 * math.sin(t) * (1 - f * .1))
               for t in [-PI * .35 + PI * 1.05 * j / 18 for j in range(19)]]
        (cv.line if k > 4 else cv.hair)(arc)
    blush = [(x + r * .9 * math.cos(t), y + r * .85 * math.sin(t)) for t in [PI * (-.3 + 1.0 * j / 14) for j in range(15)]]
    blush += [(x + r * .35 * math.cos(t) + r * .3, y + r * .5 * math.sin(t)) for t in [PI * (.7 - 1.0 * j / 14) for j in range(15)]]
    cv.hair(C.hatch_poly(blush, -40, 1.5, rng.random()))
    cv.line([(x - r * .15, y - r * .9), (x - r * .32, y - r * .3), (x - r * .25, y + r * .35), (x - r * .05, y + r * .85)])
    cv.obj([C._ell_pts(x - r * .3, y - r * .9, r * .12, r * .08, 10)[:-1]], 1.)


def hazy_glass(cv, x, base, H, bw, rng):
    """A stemmed tulip of fresh-hop hazy: the cloudy beer in close rule, a foam head of bubbles
    over the lip, condensation beads and a lit window on the glass."""
    foot_h, stem_h = H * .05, H * .2
    foot = C._ell_pts(x, base - foot_h * .5, bw * .75, foot_h, 24)[:-1]
    cv.obj([foot], 1.)
    cv.hair(C.hatch_poly(foot, 0, 1.5))
    bb = base - foot_h - stem_h
    cv.obj([[(x - 1.2, base - foot_h), (x - 1, bb + 3), (x - 2.2, bb + 1), (x + 2.2, bb + 1), (x + 1, bb + 3), (x + 1.2, base - foot_h)]], 1.)
    cv.hair([(x + .5, base - foot_h - 1), (x + .4, bb + 3)])
    n = 22
    BH = H - foot_h - stem_h
    ks = ((0, .4), (.12, .8), (.38, 1.), (.68, .86), (.86, .78), (1., .9))

    def hw(t):
        for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                u = u * u * (3 - 2 * u)
                return bw * (v0 + (v1 - v0) * u)
        return bw * ks[-1][1]
    right = [(x + hw(i / n), bb - BH * i / n) for i in range(n + 1)]
    glass = right + [(2 * x - p[0], p[1]) for p in right[::-1]]
    cv.obj([glass], 1.)
    head = bb - BH * .8
    beer = [p for p in glass if p[1] >= head]
    cv.hair(C.hatch_poly(beer, 90, 1.5, .3))
    cv.hair(C.hatch_poly([p for p in beer if p[0] > x + bw * .15] + [(x + bw * .15, head)], 25, 3, .5))
    cv.obj([[(x - bw * .55, head + 3), (x - bw * .38, head + 3), (x - bw * .36, bb - 4), (x - bw * .5, bb - 5)]], 0)
    cv.line([(x - hw(.8), head), (x + hw(.8), head)])
    top = bb - BH
    cap = [(x - hw(1) - 1, top + 1)] + [(x + hw(1) * math.cos(t) * 1.05, top - BH * .08 * math.sin(t)) for t in [PI - PI * j / 16 for j in range(17)]] + [(x + hw(1) + 1, top + 1)]
    cv.obj([cap], 1.)
    for _ in range(int(bw * 1.8)):
        fx = x + bw * rng.uniform(-.85, .85)
        fy = rng.uniform(top - BH * .04, head - 1)
        rr = rng.uniform(.6, 1.3)
        cv.hair(C._ell_pts(fx, fy, rr, rr * .8, 8))
    for _ in range(int(BH / 3.5)):
        cx_ = x + bw * rng.uniform(.25, .85)
        cy_ = rng.uniform(head + 2, bb - 3)
        cv.obj([C._ell_pts(cx_, cy_, .9, 1.1, 8)[:-1]], .5)


def hop_bine(cv, x, y0, y1, seed):
    """The bine climbing the right edge: a twining stem, leaves and cones hanging."""
    rng = random.Random(seed)
    L = y1 - y0
    pts = [(x + L * .03 * math.sin((y1 - yy) * .08), yy) for yy in [y1 - L * j / 30 for j in range(31)]]
    twig(cv, pts, 1.8, 1.)
    for k, j in enumerate((5, 11, 17, 23, 28)):
        px, py = pts[j]
        sd = -1 if k % 2 == 0 else 1
        base_a = PI * .85 if sd < 0 else PI * .15
        for la in (-.55, .55, 0):
            leaflet(cv, px, py, base_a + la, L * .11 * (1 - abs(la) * .35), L * .04, .25 * sd, sd > 0, rng)
        if k % 2 == 0:
            hop_cone(cv, px - L * .05, py + L * .08, L * .14, L * .075, .2, random.Random(seed + j))


def _water(cv, x0, x1, hz, by, rng):
    """The Pacific: rows of wavelets, small and close at the horizon, larger toward the beach,
    their troughs cut and their crests left white."""
    yy, step = hz + 1., 1.2
    while yy < by - 1:
        f = (yy - hz) / max(1, by - hz)
        wl = 4 + 14 * f
        xx = x0 + rng.uniform(-wl, 0)
        while xx < x1:
            L = wl * rng.uniform(.7, 1.3)
            dip = .4 + 1.4 * f
            arc = [(xx + L * j / 6, yy + dip * math.sin(PI * j / 6)) for j in range(7)]
            (cv.line if (rng.random() < .25 + .3 * f) else cv.hair)(arc)
            xx += L + rng.uniform(.5, 3) * (1 + f * 2)
        yy += step
        step = min(3., 1.2 + 2.2 * f)


def coast_life(cx, cy, a, b, seed, mini=False):
    """Sheet two: the Oregon coast at Cannon Beach. Haystack Rock under a Dore sky, a pelican
    gliding over the surf, a peach branch from the left and a hop bine up the right, and on the
    sand in front, a tulip of hazy fresh-hop, peaches and a hop cone."""
    rng = random.Random(seed + 5)
    cv = C.Canvas()
    x0, x1, y0, y1 = cx - a - 2, cx + a + 2, cy - b - 2, cy + b + 2
    hz = cy + b * (.0 if mini else -.12)
    by = cy + b * (.62 if mini else .4)
    cv.obj([[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], 0)
    sh, sl = st_sky(x0, y0, x1, hz + 1, seed + 2, top_dark=.45)
    cv.hair(sh)
    cv.line(sl)
    cv.obj([[(x0, hz), (x1, hz), (x1, by), (x0, by)]], 0)
    _water(cv, x0, x1, hz, by, rng)
    rx_ = cx + a * (.28 if not mini else .15)
    rH = b * (.58 if not mini else .8)
    rW = rH * 1.15
    # surf breaking round the rock
    cv.line([(xx, by - 1.5 - 1.5 * math.sin(xx * .13) ** 2) for xx in range(int(x0), int(x1) + 2, 3)])
    haystack(cv, rx_, by - b * .03, rH, rW, rng)
    foam = [(xx, by - .8 + .8 * math.sin(xx * .31)) for xx in range(int(rx_ - rW * .7), int(rx_ + rW * .9), 2)]
    cv.hair(foam)
    pelican(cv, cx - a * (.5 if not mini else .55), cy - b * (.3 if not mini else .3), a * (.12 if not mini else .06), rng)
    sand = [(x0, by), (x1, by), (x1, y1), (x0, y1)]
    cv.obj([sand], 0)
    for k in range(int((y1 - by) / 2.)):
        yy = by + 1.5 + k * 2. + k * k * .04
        xx = x0
        while xx < x1:
            L = rng.uniform(5, 18)
            refl = abs(xx - rx_) < rW * .45 and yy < by + (y1 - by) * .35
            if not refl or k % 2:
                cv.hair([(xx, yy), (xx + L * .5, yy - .6), (xx + L, yy)])
            elif refl:
                cv.line([(xx, yy), (xx + L, yy)])
            xx += L + rng.uniform(2, 6)
    if mini:
        return cv.svg()
    # the peach branch from the upper left
    br = _curve(x0 - 2, cy - b * .82, .3, a * .95, .8, 28)
    twig(cv, br, a * .035, a * .012)
    for j, ang in ((4, -.9), (8, 1.0), (12, -.6), (17, 1.2), (21, -.3), (25, .6), (27, 0.)):
        leaflet(cv, br[j][0], br[j][1], ang, a * .28, a * .05, .3, j % 2 == 0, rng)
    peach(cv, br[10][0] + 1, br[10][1] + a * .11, a * .095, rng)
    peach(cv, br[19][0] - 1, br[19][1] + a * .1, a * .08, rng)
    # the hop bine up the right edge
    hop_bine(cv, cx + a * .78, cy - b * .8, cy + b * .9, seed + 9)
    # on the sand: the glass, peaches, a hop cone
    gy = cy + b * .86
    gx = cx - a * .18
    hazy_glass(cv, gx, gy, b * .62, a * .15, rng)
    peach(cv, cx - a * .56, gy - a * .11, a * .12, rng)
    peach(cv, cx - a * .37, gy - a * .085, a * .095, rng)
    hop_cone(cv, cx + a * .12, gy - a * .07, a * .24, a * .13, 1.4, random.Random(seed + 8))
    cv.line([(cx - a * .7, gy + .5), (cx + a * .2, gy + .5)])
    return cv.svg()


def _subject(ctx):
    """Which vignette this sheet gets: the coast beers on a later sheet whose page lists them,
    the Nocino still life otherwise."""
    smp = (ctx.get("sample") or "").lower()
    sheet = int(ctx.get("sheet", 0) or 0)
    beer = any(k in smp for k in ("ipa", "hop", "pelican", "peach", "brew", "beer", "sour"))
    return "coast" if sheet >= 1 and (beer or "walnut" not in smp or sheet >= 2) else "nocino"


def _field(fld, mode, seed, subj):
    xs = [q[0] for q in fld]
    ys = [q[1] for q in fld]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    a, b = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
    if subj == "coast":
        return coast_life(cx, cy, a, b, seed, mini=(mode == "band"))
    if mode == "band":
        return medallion_walnuts(cx, cy, a, b, seed)
    return still_life(cx, cy, a, b, seed)


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
    ry = max(4., h / 2 - 8.5) if h >= 40 else max(4., h / 2 - 7.2)
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


def st_dissolve(poly, seed, depth=9., step=1.25):
    """Bewick's dissolving edge: white broken rings laid over the outer few px of a vignette, the
    white taking more of each ring toward the rim, so the cut lines crumble out into the paper."""
    rng = _rnd.Random(seed)
    n = int(depth / step)
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    o = []
    for k in range(n):
        f = 1 - k / n                       # 1 at the rim, toward 0 inside
        g = k * step + .4
        ring = []
        for (x, y) in poly:
            dx, dy = x - cx, y - cy
            L = _m.hypot(dx, dy) or 1
            ring.append((x - dx / L * g, y - dy / L * g))
        segs = []
        for _ in range(4):
            on = rng.uniform(1, 5) * (.3 + 1.9 * f * f)
            off = rng.uniform(3, 9) * (1.3 - f)
            segs += [on, max(.3, off)]
        da = " ".join(_C._n(v) for v in segs)
        o.append(f'<path d="{st_poly_d(ring)}" fill="none" stroke="#fff" stroke-width="{_C._n(step + .25)}" '
                 f'stroke-dasharray="{da}" stroke-dashoffset="{_C._n(rng.uniform(0, 40))}"/>')
    o.append(f'<path d="{st_poly_d(poly)}" fill="none" stroke="#fff" stroke-width="2"/>')
    return "".join(o)


def st_vignette(w, h, seed, hk):
    """The free-standing vignette: the scene itself is the plate, cut to its shape and crumbling
    out into the paper at the rim; any ornament is drawn from the subject (hk['frame'])."""
    shape = hk.get("shape", "oval")
    pad = hk.get("pad", 2.)
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - pad, h / 2 - pad
    rx = min(rx, ry * hk.get("max_aspect", 3.2))
    ph = (seed % 97) * .07
    fld = hk["shape_fn"](cx, cy, rx, ry) if hk.get("shape_fn") else st_shape_pts(shape, cx, cy, rx, ry, 0., 160, ph)
    if shape == "irregular" and not hk.get("shape_fn"):
        s = max(max(abs(q[0] - cx) / (w / 2 - pad) for q in fld), max(abs(q[1] - cy) / (h / 2 - pad) for q in fld))
        fld = [(cx + (q[0] - cx) / s, cy + (q[1] - cy) / s) for q in fld]
    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    o = [f'<path d="{st_rect_d(0, 0, w, h)}" fill="#fff"/>']
    if hk.get("under"):
        o.append(hk["under"](cx, cy, rx, ry, fld, mode))
    o.append(st_clip_poly(f"s2v{w}x{h}", fld, hk["field"](fld, mode)))
    o.append(st_dissolve(fld, seed, hk.get("dissolve", min(7., 3 + min(w, h) * .025))))
    if hk.get("frame"):
        o.append(hk["frame"](cx, cy, rx, ry, fld, mode))
    if hk.get("dedication") and h >= 110:
        dh = min(30., h * .16)
        o.append(f'<path d="{st_ell_d(cx, h - dh / 2 - 1.5, dh * .62, dh * .55)}" fill="#fff"/>')
        o.append(st_dedication(cx, h - 1.5, dh))
    return "".join(o)


def st_plate(w, h, seed, hk):
    base = _C.Canvas
    if hk.get("vignette"):
        return _st_plate(w, h, seed, hk)
    _C.Canvas = StCanvas
    try:
        return _st_plate(w, h, seed, hk)
    finally:
        _C.Canvas = base


def _st_plate(w, h, seed, hk):
    if hk.get("vignette"):
        body = st_vignette(w, h, seed, hk)
    elif h <= 72 and w <= 110 and hk.get("device", True):
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
    seed = sum(map(ord, ctx.get("date", ""))) + 31 * int(ctx.get("sheet", 0) or 0)
    subj = _subject(ctx)
    hk = dict(field=lambda fld, mode: _field(fld, mode, seed, subj), egg=egg_sticks, shape="oval", vignette=True, pad=3., max_aspect=2.1,
              aspect=(1.5 if subj == "nocino" else 1.8), cw=.27, rmin=9., rmax=30.,
              motto=("NOCINO · NEW DEAL · 2026" if subj == "nocino" else "PELICAN · PUBLIC COAST · CANNON BEACH"),
              tablet_lines=(["GREEN-WALNUT LIQUEUR", "SMALL BATCH · PORTLAND"] if subj == "nocino"
                            else ["PEACH SOUR · FRESH HOP HAZY", "CASCADE · MAGNUM · TILLAMOOK"]))
    return st_plate(w, h, seed, hk)
