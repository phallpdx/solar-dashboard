"""music-02 "Drum break of the day": James Brown, Get Up (I Feel Like Being a) Sex Machine, 1970,
drums by John "Jabo" Starks. Tight, simple, relentless.

The plate is a 1970 funk kit engraved inside the house cartouche: a snare in front with the sticks
laid crossed on its head, a hi-hat at the left, a ride cymbal at the right, the bass drum behind
with a rack tom, all on a rug under a stage-light burst. A big pair of drumsticks crosses behind
the cartouche. On tall plates the pedestal tablet carries two bars of the groove in drum notation
(kick on 1 and the and-of-3, snare on 2 and 4, eighth-note hats, with a repeat) and the ribbon is
lettered MCMLXX. Easter eggs: a "P" monogram on the bass-drum head, and Parker's dog asleep on the
rug by the kick."""
import sys
import math
import random
import engraving_codex as C
import engraving_morning as EM

_n, _d, _ell = C._n, C._d, C._ell_pts
PI = math.pi


# ------------------------------------------------------------------------------------------------
# small engraving helpers
# ------------------------------------------------------------------------------------------------

def _solid(cv, poly):
    """Black mass: 1 px lines 0.9 px apart."""
    cv.line(C.hatch_poly(poly, 0, .9, .45))


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _arc(cx, cy, rx, ry, a0, a1, n=24):
    return _ell(cx, cy, rx, ry, n, a0, a1)


def _cyl_lines(cv, cx, top, bot, rx, ry, hl=-.45, dark_from=.78, x0=-1., x1=1.):
    """Vertical shading on a drum shell between y=top and y=bot (front arcs), light from the left:
    open lines (3 px) round the highlight, closing to 1.5 px toward both edges, black at the right."""
    u = x0 + .02
    while u < x1 - .01:
        x = cx + u * rx
        yv = ry * math.sqrt(max(0., 1 - u * u))
        if abs(u - hl) > .07:
            cv.hair([(x, top + yv + .6), (x, bot + yv - .6)])
        d = abs(u - hl)
        pitch = 3. if d < .35 else (2. if d < .7 else 1.5)
        if u > dark_from:
            pitch = 1.5
        u += pitch / rx
    # the shadow side: solid black band
    poly = []
    for i in range(9):
        uu = dark_from + (1 - dark_from) * i / 8 + .06
        uu = min(uu, 1.)
        poly.append((cx + uu * rx, top + ry * math.sqrt(max(0., 1 - uu * uu))))
    for i in range(8, -1, -1):
        uu = min(dark_from + (1 - dark_from) * i / 8 + .06, 1.)
        poly.append((cx + uu * rx, bot + ry * math.sqrt(max(0., 1 - uu * uu))))
    if rx > 14:
        _solid(cv, poly)


def _drum(cv, cx, cy, rx, ry, dep, lugs=5, hoop=None, head_hatch=True, stand=None, seed=0, badge=False):
    """An upright drum: top head centred (cx, cy), radii rx, ry, shell dep deep."""
    hoop = hoop or max(1.6, ry * .22)
    shell = _arc(cx, cy + dep, rx, ry, 0, PI, 30) + _arc(cx, cy, rx, ry, PI, 0, 30)
    cv.obj([shell], 1.)
    _cyl_lines(cv, cx, cy, cy + dep, rx, ry)
    # bottom hoop
    bh = _arc(cx, cy + dep - hoop, rx + .6, ry, 0, PI, 30) + _arc(cx, cy + dep, rx + .6, ry, PI, 0, 30)[::-1][::-1]
    bh = _arc(cx, cy + dep - hoop, rx + .6, ry, 0, PI, 30) + _arc(cx, cy + dep, rx + .6, ry, PI, 0, 30)
    bh = _arc(cx, cy + dep, rx + .6, ry, 0, PI, 30) + _arc(cx, cy + dep - hoop, rx + .6, ry, PI, 0, 30)
    cv.obj([bh], 1.)
    cv.hair(_arc(cx, cy + dep - hoop * .45, rx + .6, ry, .15, PI * .55, 20))
    cv.line(_arc(cx, cy + dep - hoop * .1, rx + .4, ry, .05, PI * .45, 16))
    # lugs and rods
    for k in range(lugs):
        t = PI * (k + .5) / lugs
        lx = cx + rx * math.cos(t)
        ly = cy + ry * math.sin(t)
        fo = math.sin(t) ** .6
        lw = max(1.2, rx * .035) * fo
        lh = dep * .3
        ly0 = ly + dep * .33
        if lw < 1.1:
            continue
        lug = [(lx - lw, ly0 + lw * .6), (lx - lw * .6, ly0), (lx + lw * .6, ly0), (lx + lw, ly0 + lw * .6),
               (lx + lw, ly0 + lh - lw * .6), (lx + lw * .6, ly0 + lh), (lx - lw * .6, ly0 + lh), (lx - lw, ly0 + lh - lw * .6)]
        cv.obj([lug], 1.)
        if lw > 1.5:
            cv.line([(lx + lw * .5, ly0 + .8), (lx + lw * .5, ly0 + lh - .8)])
        cv.obj([], 0)
        cv.line([(lx, ly + hoop * .6), (lx, ly0)])
        cv.line([(lx, ly0 + lh), (lx, ly + dep - hoop * .6)])
    if badge and rx > 22:
        # the maker's badge on the shell, here a P (Easter egg)
        bx, by = cx - rx * .12, cy + ry + dep * .5
        bwid, bhei = max(3.2, rx * .13), max(4., dep * .3)
        cv.obj([_ell(bx, by, bwid, bhei, 20)[:-1]], 1.)
        _P(cv, bx, by, bhei * 1.1)
    # top hoop band
    th = _arc(cx, cy + hoop, rx + .8, ry, 0, PI, 30) + _arc(cx, cy, rx + .8, ry, PI, 0, 30)
    cv.obj([th], 1.)
    cv.hair(_arc(cx, cy + hoop * .5, rx + .8, ry, .12, PI * .6, 24))
    cv.line(_arc(cx, cy + hoop * .9, rx + .6, ry, .05, PI * .4, 16))
    # the head
    head = _ell(cx, cy, rx + .8, ry + .3, 48)[:-1]
    cv.obj([head], 1.)
    inner = _ell(cx, cy, rx - hoop * .7, ry - hoop * .3, 48)[:-1]
    cv.hair(inner + [inner[0]])
    if head_hatch:
        # a coated head: light rules, closer on the far side, a scuffed centre from the rimshots
        cv.hair(C.hatch_poly(inner, -8, 3. if ry > 6 else 2., .5, .4))
        rr = rx * .22
        sc = _ell(cx + rx * .05, cy + ry * .05, rr, rr * ry / rx, 20)[:-1]
        if rr > 4:
            cv.hair(C.hatch_poly(sc, 72, 1.5, .2, .3))
    return shell


def _cymbal(cv, cx, cy, rx, ry, tilt=0., rings=True):
    """A cymbal seen from a little above: lathe-turned rings broken by two highlights, a raised bell."""
    def P(u, v):
        x, y = u * rx, v * ry
        c, s = math.cos(tilt), math.sin(tilt)
        return (cx + x * c - y * s, cy + x * s + y * c)

    body = [P(math.cos(t), math.sin(t)) for t in [2 * PI * i / 60 for i in range(60)]]
    cv.obj([body], 1.)
    # the edge thickness on the near side
    cv.heavy([P(math.cos(t), math.sin(t) + .04) for t in [PI * (.08 + .84 * i / 30) for i in range(31)]])
    if rings:
        n = max(3, int(ry / 1.2))
        for k in range(1, n):
            f = k / n
            seg = []
            for i in range(73):
                t = 2 * PI * i / 72
                hl = math.cos(t + 2.2)
                if (hl > .88 and f > .3) or (hl < -.93 and f > .5):
                    if len(seg) > 1:
                        cv.hair(seg)
                    seg = []
                    continue
                seg.append(P(f * math.cos(t), f * math.sin(t)))
            if len(seg) > 1:
                cv.hair(seg)
    # hammer marks and the shadowed far-right sector
    rng = random.Random(int(cx * 7 + cy))
    for i in range(int(rx * .9)):
        t = rng.uniform(0, 2 * PI)
        f = rng.uniform(.35, .92)
        cv.hair([P(f * math.cos(t), f * math.sin(t)), P((f + .07) * math.cos(t), (f + .07) * math.sin(t))])
    nr = int(rx / 3.5)
    for i in range(nr):
        t = -.8 + 1.3 * i / max(1, nr - 1)
        cv.hair([P(.55 * math.cos(t), .55 * math.sin(t)), P(.97 * math.cos(t), .97 * math.sin(t))])
    bell = [P(.24 * math.cos(t), .28 * math.sin(t) - .1) for t in [2 * PI * i / 30 for i in range(30)]]
    cv.obj([bell], 1.)
    cv.hair([P(.18 * math.cos(t), .22 * math.sin(t) - .1) for t in [PI * (.1 + .8 * i / 12) for i in range(13)]])
    cv.obj([[P(.06 * math.cos(t), .1 * math.sin(t) - .18) for t in [2 * PI * i / 12 for i in range(12)]]], 0)
    _solid(cv, [P(.06 * math.cos(t), .1 * math.sin(t) - .18) for t in [2 * PI * i / 12 for i in range(12)]])


def _rod(cv, x0, y0, x1, y1, w=2.):
    """A chrome stand tube: white with a black shadow line."""
    a = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(a) * w / 2, math.cos(a) * w / 2
    cv.obj([[(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]], 1. if w > 1.6 else .5)
    if w > 2.4:
        cv.line([(x0 - nx * .35, y0 - ny * .35), (x1 - nx * .35, y1 - ny * .35)])


def _tripod(cv, x, ytop, yfloor, spread):
    for sx in (-1, 0, 1):
        if sx == 0:
            cv.obj([], 0)
            cv.line([(x, ytop), (x + .5, yfloor - 2)])
            continue
        _rod(cv, x, ytop, x + sx * spread, yfloor, 1.4)
    cv.obj([], 0)
    cv.line([(x - spread * .45, ytop + (yfloor - ytop) * .45), (x + spread * .45, ytop + (yfloor - ytop) * .45)])


def _stick(cv, x0, y0, x1, y1, w, seed=0):
    """A hickory drumstick from butt (x0, y0) to tip (x1, y1), w px across at the butt: tapered,
    grained, shadowed along its lower side, ending in an oval bead."""
    n = 24
    pts = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    ws = [w / 2 * (1 if i / n < .55 else 1 - .62 * C._smooth(.55, 1, i / n)) for i in range(n + 1)]
    R = C._Rib(pts, ws, ws)
    side = 1 if R.N[0][1] > 0 else -1          # the side facing down gets the shadow
    cv.obj([R.outline()], 1.)
    for s in (.45, .7):
        cv.hair(R.contour(-s * side, .02, .97, minw=1.4))
    cv.hair(R.contour(.15 * side, .05, .5, minw=2.5))
    C._shadow(cv, R, side, w * .28, -.05, 1.05)
    rng = random.Random(seed)
    if w > 4:
        for k in range(3):
            u = rng.uniform(.1, .6)
            cv.hair([R.at(u, -.1 * side), R.at(u + .08, .15 * side)])
    a = math.atan2(y1 - y0, x1 - x0)
    br = max(1.4, w * .42)
    bx, by = x1 + math.cos(a) * br * .9, y1 + math.sin(a) * br * .9
    bead = [(bx + math.cos(a) * br * 1.25 * math.cos(t) - math.sin(a) * br * math.sin(t),
             by + math.sin(a) * br * 1.25 * math.cos(t) + math.cos(a) * br * math.sin(t)) for t in [2 * PI * i / 20 for i in range(20)]]
    cv.obj([bead], 1.)
    if br > 2.2:
        cv.hair([(bx + side * -math.sin(a) * br * .3, by + side * math.cos(a) * br * .3),
                 (bx + math.cos(a) * br, by + math.sin(a) * br)])


def _dog(cv, x, y, s):
    """Parker's dog asleep on the rug, curled, head on its paws, facing left; about 30*s wide,
    resting on y."""
    # haunch and back: one rounded mound, fur laid in arcs that follow the curl
    body = ([(x + 13 * s * math.cos(t), y - 7.5 * s * math.sin(t)) for t in [PI * i / 30 for i in range(31)]])
    cv.obj([body], 1.)
    for k, f in enumerate((.9, .76, .62, .48)):
        arc = [(x + 1.5 * s + 11.5 * s * f * math.cos(t), y - 7 * s * f * math.sin(t)) for t in [PI * (.08 + .5 * i / 16) for i in range(17)]]
        cv.hair(arc)
    cv.hair(C.hatch_poly([(x - 4 * s, y), (x + 13 * s, y), (x + 11 * s, y - 4 * s), (x - 1 * s, y - 4.5 * s)], 20, 1.5))
    # the haunch line and the hind paw
    cv.line([(x + 9 * s + 4.5 * s * math.cos(t), y - 3.2 * s - 4 * s * math.sin(t)) for t in [PI * (.15 + .75 * i / 12) for i in range(13)]])
    # tail curled round the front
    tail = [(x + 12.5 * s, y - 1.5 * s), (x + 10 * s, y + .6 * s), (x + 2 * s, y + 1.2 * s), (x - 6 * s, y + .8 * s), (x - 9 * s, y - .4 * s)]
    cv.obj([], 0)
    cv.heavy(tail)
    # front paws stretched under the chin
    paw = _ell(x - 9 * s, y - 1.2 * s, 5 * s, 1.5 * s, 16)[:-1]
    cv.obj([paw], 1.)
    cv.hair([(x - 13 * s, y - 1 * s), (x - 11.5 * s, y - .2 * s)])
    # head resting on the paws
    head = _ell(x - 10 * s, y - 5.2 * s, 4.8 * s, 3.8 * s, 24)[:-1]
    cv.obj([head], 1.)
    cv.hair(C.hatch_poly(head, 70, 1.5, inset=.5)[:len(C.hatch_poly(head, 70, 1.5)) // 2])
    snout = [(x - 13 * s, y - 6.6 * s), (x - 17.2 * s, y - 4.4 * s), (x - 17 * s, y - 2.6 * s), (x - 12.6 * s, y - 2.4 * s)]
    cv.obj([snout], 1.)
    _solid(cv, _ell(x - 16.8 * s, y - 4 * s, .9 * s, .8 * s, 8)[:-1])
    cv.line([(x - 12.4 * s, y - 5.6 * s), (x - 10.6 * s, y - 5.2 * s)])        # the closed eye
    ear = [(x - 9.6 * s, y - 8.8 * s), (x - 6 * s, y - 8 * s), (x - 5.6 * s, y - 3.4 * s), (x - 7.6 * s, y - 2.6 * s)]
    cv.obj([ear], 1.)
    _solid(cv, ear)


def _letters(s, cx, cy, h, track=1.3):
    polys, wd = EM._text_polys(s, cx, cy - h / 2, h, track)
    return polys


def _P(cv, cx, cy, h):
    """The P monogram, cap height h, centred."""
    polys, _ = EM._text_polys("P", cx, cy - h / 2, h, 1.)
    cv.heavy(polys)


# ------------------------------------------------------------------------------------------------
# backgrounds
# ------------------------------------------------------------------------------------------------

def _burst(cv, field, cx, cy, R, n=28, floor_y=None):
    """Stage-light burst: alternating ruled and cross-hatched rays from (cx, cy)."""
    cv.obj([field], 0)
    for i in range(n):
        a0 = 2 * PI * i / n
        a1 = 2 * PI * (i + 1) / n
        r0 = 6.
        wedge = [(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                 (cx + R * math.cos(a1), cy + R * math.sin(a1)), (cx + r0 * math.cos(a1), cy + r0 * math.sin(a1))]
        am = (a0 + a1) / 2
        if i % 2:
            cv.hair(C.hatch_poly(wedge, math.degrees(am), 2., .5))
            cv.hair(C.hatch_poly(wedge, math.degrees(am) + 90, 3., .5))
        else:
            cv.hair(C.hatch_poly(wedge, math.degrees(am) + 90, 3., 1.))
    cv.line(_ell(cx, cy, 5.5, 5.5, 20))


def _rug(cv, x0, x1, y0, y1, cx):
    """Floor boards in perspective and an oval rug with a patterned border."""
    floor = _rect(x0, y0, x1 - x0, y1 - y0)
    cv.obj([floor], 0)
    cv.hair(C.hatch_poly(floor, 0, 1.5))
    vy = y0 - (y1 - y0) * 3
    for k in range(-14, 15):
        xb = cx + k * (x1 - x0) / 9
        cv.line([(cx + (xb - cx) * .28, y0 + .5), (xb, y1)])
    cv.obj([], 0)
    cv.heavy([(x0, y0), (x1, y0)])
    rw, rh = (x1 - x0) * .44, (y1 - y0) * .55
    rcy = y0 + (y1 - y0) * .55
    rug = _ell(cx, rcy, rw, rh, 60)[:-1]
    cv.obj([rug], 1.)
    cv.hair(C.hatch_poly(rug, 30, 3.))
    cv.hair(C.hatch_poly(rug, -30, 3.))
    for f in (.86, .8):
        cv.line(_ell(cx, rcy, rw * f, rh * f, 60))
    # fringe
    for i in range(0, 60, 2):
        t = 2 * PI * i / 60
        if math.sin(t) > .2:
            px, py = cx + rw * math.cos(t), rcy + rh * math.sin(t)
            cv.hair([(px, py), (px + 2.2 * math.cos(t), py + 2.2 * math.sin(t))])
    return rcy, rw, rh


# ------------------------------------------------------------------------------------------------
# the vignettes
# ------------------------------------------------------------------------------------------------

def _kit(field, bx0, by0, bw, bh, seed):
    """The full kit, composed in the box (bx0, by0, bw, bh), drawn back to front."""
    cv = C.Canvas()
    cx = bx0 + bw / 2
    floor = by0 + bh * .76
    _burst(cv, field, cx + bw * .05, by0 + bh * .02, max(bw, bh) * 1.2, 32)
    _rug(cv, bx0 - 10, bx0 + bw + 10, floor, by0 + bh + 10, cx)
    R = min(bw * .27, bh * .33)
    bxc, byc = cx + bw * .07, floor + R * .05 - R
    # ride cymbal on its stand, right, behind the bass drum
    rx_, ry_ = bxc + R * 1.25, byc - R * 1.05
    _tripod(cv, rx_ + R * .1, byc, floor + R * .15, R * .32)
    _rod(cv, rx_ + R * .1, byc, rx_, ry_, 2.)
    _cymbal(cv, rx_, ry_, R * .82, R * .2, -.14)
    # bass drum: shell seen past the front hoop at the right
    sh = _ell(bxc + R * .2, byc, R, R, 64)[:-1]
    cv.obj([sh], 1.)
    cv.hair(C.hatch_poly(sh, 90, 1.5))
    cv.hair(C.hatch_poly(sh, 0, 3.))
    for k in range(5):
        t = -PI / 2 + PI * (k + .5) / 5
        lx, ly = bxc + R * .2 + R * .96 * math.cos(t), byc + R * .96 * math.sin(t)
        cv.obj([_rect(lx - 1.5, ly - 3, 3.4, 6)], 1.)
        cv.line([(lx + 1, ly - 2), (lx + 1, ly + 2)])
    # spurs
    for sx in (-1, 1):
        _rod(cv, bxc + sx * R * .82, byc + R * .3, bxc + sx * R * 1.18, floor + R * .12, 1.6)
    hoop = _ell(bxc, byc, R, R, 72)[:-1]
    cv.obj([hoop], 1.5)
    r = R * .985
    while r > R * .88:                        # the wooden hoop: grained rings
        cv.hair(_arc(bxc, byc, r, r, -PI * .55, PI * 1.3, 60))
        r -= 1.6
    cv.line(_arc(bxc, byc, R * .96, R * .96, -.2, PI * .8, 30))
    for k in range(8):                        # claws
        t = 2 * PI * (k + .5) / 8
        px, py = bxc + R * .93 * math.cos(t), byc + R * .93 * math.sin(t)
        cv.obj([_ell(px, py, 2.2, 2.2, 10)[:-1]], 1.)
        _solid(cv, _ell(px + .6, py + .6, 1.2, 1.2, 8)[:-1])
    head = _ell(bxc, byc, R * .875, R * .875, 72)[:-1]
    cv.obj([head], 1.)
    # the head: ruled, darker into the lower right (light from upper left)
    cv.hair(C.hatch_poly(head, 0, 3.))
    low = [(bxc + R * .875 * math.cos(t), byc + R * .875 * math.sin(t)) for t in [-.5 + 2.6 * i / 30 for i in range(31)]]
    cv.hair(C.hatch_poly(low, 0, 3., 1.5))
    cv.hair(C.hatch_poly(low, 60, 3.))
    # the badge with the P monogram (Easter egg)
    br = R * .3
    badge = _ell(bxc, byc, br, br, 40)[:-1]
    cv.obj([badge], 1.5)
    cv.hair(_ell(bxc, byc, br - 2, br - 2, 40))
    inb = _ell(bxc, byc, br - 3.5, br - 3.5, 40)[:-1]
    cv.hair(C.hatch_poly(inb, 45, 3.))
    pr = _ell(bxc, byc, br * .55, br * .62, 30)[:-1]
    cv.obj([pr], 1.)
    _P(cv, bxc, byc, br * .85)
    # rack tom on the shell
    tx, ty = bxc - R * .3, byc - R * 1.18
    _rod(cv, bxc - R * .05, byc - R * .9, tx + R * .1, ty + R * .3, 2.4)
    _drum(cv, tx, ty, R * .42, R * .13, R * .42, 4)
    # the dog asleep on the rug by the kick (Easter egg)
    _dog(cv, bxc + R * 1.2, floor + R * .45, max(.8, R / 36))
    # hi-hat at the left
    hx, hy = bx0 + bw * .16, byc - R * .55
    _tripod(cv, hx, hy + R * .9, floor + R * .25, R * .35)
    _rod(cv, hx, hy, hx, hy + R * .9, 2.)
    _cymbal(cv, hx, hy + R * .1, R * .55, R * .13, 0.)
    _cymbal(cv, hx, hy - R * .02, R * .55, R * .13, 0.)
    cv.obj([_rect(hx - 1, hy - R * .3, 2, R * .28)], .5)
    # snare in front
    sx_, sy_ = cx - bw * .12, byc + R * .52
    srx, sry, sdep = R * .66, R * .2, R * .4
    for k, a in enumerate((-.5, .5, 0.)):
        _rod(cv, sx_ + a * srx * .2, sy_ + sdep + 2, sx_ + a * srx * 1.15, floor + R * .5 + (k == 2) * R * .08, 1.6)
    _drum(cv, sx_, sy_, srx, sry, sdep, 6, seed=seed)
    # the sticks crossed on the snare head
    _stick(cv, sx_ - srx * 1.15, sy_ + sry * .9, sx_ + srx * .55, sy_ - sry * 1.6, max(2.6, R * .07), seed)
    _stick(cv, sx_ + srx * 1.1, sy_ + sry * .7, sx_ - srx * .5, sy_ - sry * 1.7, max(2.6, R * .07), seed + 1)
    return cv.svg()


def _snare_only(field, bx0, by0, bw, bh, seed, hat=True):
    """The snare with crossed sticks (and a hi-hat if there is room), for medium and band plates."""
    cv = C.Canvas()
    cx = bx0 + bw / 2
    _burst(cv, field, cx, by0 + bh * .1, max(bw, bh) * 1.3, 24)
    floor = by0 + bh * .86
    fl = _rect(bx0 - 20, floor, bw + 40, bh)
    cv.obj([fl], 0)
    cv.hair(C.hatch_poly(fl, 0, 1.5))
    cv.obj([], 0)
    cv.heavy([(bx0 - 20, floor), (bx0 + bw + 20, floor)])
    hat = hat and bw > 110
    srx = min(bw * (.3 if hat else .36), bh * .5)
    sry, sdep = srx * .3, srx * .55
    sx_ = cx + (bw * .1 if hat else 0)
    sy_ = floor - sdep - sry - srx * .35
    if hat:
        hx = bx0 + bw * .2
        hy = sy_ + sry * .1
        _tripod(cv, hx, hy + srx * .8, floor, srx * .4)
        _rod(cv, hx, hy, hx, hy + srx * .8, 1.6)
        _cymbal(cv, hx, hy + srx * .1, srx * .62, srx * .14, 0.)
        _cymbal(cv, hx, hy - srx * .02, srx * .62, srx * .14, 0.)
    for k, a in enumerate((-.6, .6, 0.)):
        _rod(cv, sx_ + a * srx * .2, sy_ + sdep + 2, sx_ + a * srx * 1.05, floor, 1.4)
    _drum(cv, sx_, sy_, srx, sry, sdep, 5 if srx > 30 else 4, seed=seed, badge=True)
    sw = max(2., srx * .1)
    _stick(cv, sx_ - srx * 1.25, sy_ + sry * 1.2, sx_ + srx * .65, sy_ - sry * 1.9, sw, seed)
    _stick(cv, sx_ + srx * 1.25, sy_ + sry * 1.1, sx_ - srx * .6, sy_ - sry * 2., sw, seed + 1)
    return cv.svg()


def _clipped(cid, field, body):
    return f'<clipPath id="{cid}"><path d="{_d(field, True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _vignette(field, seed, kind):
    xs = [p[0] for p in field]
    ys = [p[1] for p in field]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    if kind == "kit":
        body = _kit(field, x0 + (x1 - x0) * .04, y0 + (y1 - y0) * .1, (x1 - x0) * .92, (y1 - y0) * .84, seed)
    else:
        body = _snare_only(field, x0, y0, x1 - x0, y1 - y0, seed, kind == "trio")
    return _clipped(C._uid("v", x0, y0, x1, y1, seed), field, body)


def _field(cx, cy, w, h):
    """The cartouche field inside its bead row (mirrors codex.cartouche's geometry)."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a - 5.5, b - 5.5, n=120)


# ------------------------------------------------------------------------------------------------
# crossed sticks behind the cartouche; the groove on the tablet; MCMLXX on the ribbon
# ------------------------------------------------------------------------------------------------

def _big_sticks(cx, cy, span, rise, w, seed):
    cv = C.Canvas()
    for sx in (-1, 1):
        _stick(cv, cx - sx * span, cy + rise, cx + sx * span * .92, cy - rise * .92, w, seed + sx)
    return cv.svg()


def _groove(tx, ty, tw, th):
    """Two bars of the Sex Machine groove in drum notation, engraved on the tablet."""
    o = []
    o.append(f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 4)}v{_n(th - 4)}h{_n(-(tw - 4))}z" fill="{C.pat("S")}" stroke="#000" stroke-width=".5"/>')
    sp = min(3., (th - 4) / 8.4)
    if sp < 1.6:
        return "".join(o)
    top = ty + th / 2 - 2 * sp + sp * 1.2
    xl, xr = tx + tw * .06, tx + tw * .94
    staff = "".join(f"M{_n(xl)},{_n(top + k * sp)}H{_n(xr)}" for k in range(5))
    heads, xs_, stems, beams = [], [], [], []
    # percussion clef
    heads.append(_d(_rect(xl + 3, top + sp, 1.2, sp * 2), True, 0))
    heads.append(_d(_rect(xl + 5.2, top + sp, 1.2, sp * 2), True, 0))
    x_start = xl + 12
    bar_w = (xr - 8 - x_start) / 2
    hits = {0: ("k",), 2: ("s",), 5: ("k",), 6: ("s",)}
    for bar in range(2):
        bx = x_start + bar * bar_w
        step = bar_w / 8
        for e in range(8):
            x = bx + step * (e + .5)
            # hi-hat cross above the top line
            hy = top - sp
            r = sp * .45
            xs_.append(f"M{_n(x - r)},{_n(hy - r)}l{_n(2 * r)},{_n(2 * r)}M{_n(x - r)},{_n(hy + r)}l{_n(2 * r)},{_n(-2 * r)}")
            low = hy
            for k in hits.get(e, ()) + ((("g",) if (bar == 1 and e == 7) else ())):
                yy = top + (3.5 if k == "k" else 1.5) * sp
                if k == "g":
                    yy = top + 1.5 * sp
                rx, ry = sp * .62, sp * .45
                heads.append(_d(_ell(x - rx * .2, yy, rx, ry, 10)[:-1], True, 0))
                low = max(low, yy)
            stems.append(f"M{_n(x + sp * .45)},{_n(low)}V{_n(top - sp * 3.2)}")
        for g in range(2):
            x0 = bx + step * (g * 4 + .5) + sp * .45
            x1 = bx + step * (g * 4 + 3.5) + sp * .45
            yb = top - sp * 3.2
            beams.append(_d([(x0, yb), (x1, yb), (x1, yb + 1.4), (x0, yb + 1.4)], True, 0))
        staff += f"M{_n(bx + bar_w)},{_n(top)}V{_n(top + 4 * sp)}"
    # repeat sign at the end
    xe = x_start + 2 * bar_w
    heads.append(_d(_rect(xe + 2.5, top, 1.4, 4 * sp), True, 0))
    for yy in (top + 1.5 * sp, top + 2.5 * sp):
        heads.append(_d(_ell(xe - 1.5, yy, .8, .8, 8)[:-1], True, 0))
    o.append(f'<path d="{_d(_rect(xl - 2, top - sp * 3.8, xr - xl + 4, sp * 8.2), True, 0)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{staff}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(stems)}{"".join(xs_)}" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(heads)}{"".join(beams)}" fill="#000" stroke="none"/>')
    return "".join(o)


def _banner_letters(centre, h):
    xs = [p[0] for p in centre]
    cx = (xs[0] + xs[-1]) / 2
    cyf = lambda x: min(centre, key=lambda p: abs(p[0] - x))[1]
    polys = _letters("MCMLXX", cx, 0, h, 2.2)
    out = []
    for pl in polys:
        out.append([(x, y + cyf(x)) for x, y in pl])
    dots = []
    wd = max(p[0] for pl in polys for p in pl) - cx
    for sx in (-1, 1):
        x = cx + sx * (wd + h * .9)
        y = cyf(x)
        dots.append(_d(_ell(x, y, h * .16, h * .16, 8)[:-1], True, 0))
    return (f'<path d="{"".join(_d(p, False, 0) for p in out)}" stroke="#000" stroke-width="1"/>'
            f'<path d="{"".join(dots)}" fill="#000" stroke="none"/>')


# ------------------------------------------------------------------------------------------------
# layouts (house frame, adapted: the field fully engraved, no blank tablet, no bare paper)
# ------------------------------------------------------------------------------------------------

def _layout_band(w, h, seed):
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
    field = _ell(cx, cy, rx - 4.5, ry - 4.5, 72)[:-1]
    o.append(_vignette(field, seed, "snare"))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .4, gh * 1.45)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    # the sticks crossed behind the cartouche, butts and tips breaking out of it
    o.append(C._clip(C._uid("ms", w, h, seed), 0, gy0, w, gh,
                     _big_sticks(cx, cy, cw * .62, gh * .42, max(4., gh * .045), seed)))
    c, _, _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    field = _field(cx, cy, cw, gh + 4)
    o.append(_vignette(field, seed, "trio" if gh > 150 else "snare"))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .025, 11.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .66
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .17, ph * .24)
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    o.append(C._clip(C._uid("ts", w, h, seed), px0, py0, pw, ph,
                     _big_sticks(cx, cy + ch * .05, cw * .6, ch * .5, max(5., ch * .03), seed)))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    field = _field(cx, cy, cw, ch)
    o.append(_vignette(field, seed, "kit" if ch > 200 else "trio"))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .18 + top_free, 52), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_letters(centre, bh * .52))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    # the ground carries on behind the pedestal and frieze, so no bare paper is left at the sides
    o.append(C.dark_ground((0, py0 + ph, w, h - py0 - ph), "G"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    fh_ = th / .6
    o.append(_groove(tx, ty - fh_ * .14, tw, fh_ * .88))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
