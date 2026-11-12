"""river-03 'Fishing the Columbia: Will they bite?' -- master plate.

Subject: the BEST solunar window of the day, dusk on the Columbia off Sauvie Island. The sun sets
behind the island's cottonwoods with today's moon (phase from ctx date) hanging beside it, a
chinook salmon leaps clear of the river in the foreground throwing spray, and (tall/medium) an
angler sits in a drift boat with his dog at the bow. Easter egg: a great blue heron of Sauvie
Island stands in the reeds at the shoreline (and Parker's dog rides the bow).
Tall plates also carry today's tide curve engraved on the ribbon banner, and the pedestal tablet
holds this week's Bonneville run swimming upriver in file: chinook, chum, coho, lamprey, steelhead.

Built on the house library engraving_codex (frame, scrolls, cartouche, banner, pedestal)."""
import sys
import math
import random
import re
import engraving_codex as C

PI = math.pi
TAU = 2 * PI
_n, _d = C._n, C._d


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _interp(table, u):
    if u <= table[0][0]:
        return table[0][1]
    for (u0, v0), (u1, v1) in zip(table, table[1:]):
        if u <= u1:
            t = (u - u0) / (u1 - u0)
            t = t * t * (3 - 2 * t)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def _circle(cx, cy, r, n=None):
    n = n or max(12, int(r * 2.2))
    return [(cx + r * math.cos(TAU * i / n), cy + r * math.sin(TAU * i / n)) for i in range(n)]


def _hlines_in(poly, pitch, y0=None, phase=0.):
    return C.hatch_poly(poly, 0, pitch, phase)


def _depth(i):
    """coarse-to-fine rank of level i (0 coarsest)."""
    for d, m in enumerate((8, 4, 2)):
        if i % m == 0:
            return d
    return 3


# ------------------------------------------------------------------------------------------------
# moon phase from the date (for the crescent in the sky)
# ------------------------------------------------------------------------------------------------

def _moon_phase(date):
    try:
        y, m, d = (int(x) for x in date[:10].split("-"))
    except Exception:
        return .02
    if m < 3:
        y, m = y - 1, m + 12
    a = y // 100
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + 2 - a + a // 4 - 1524.5
    p = ((jd - 2451550.26) / 29.530588) % 1.
    return p


def _moon(cv, cx, cy, r, phase):
    """Dark disc with earthshine cross-hatch and the lit part as a white crescent/gibbous."""
    disc = _circle(cx, cy, r, 40)
    cv.obj([disc], .5)
    cv.hair(C.hatch_poly(disc, 30, 1.5))
    cv.hair(C.hatch_poly(disc, -30, 2))
    k = math.cos(TAU * phase)                 # terminator x-scale
    lit_right = phase < .5
    k = min(k, .2)                            # always show at least a hair crescent
    n = 30
    pts = []
    for i in range(n + 1):
        t = -PI / 2 + PI * i / n
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    for i in range(n + 1):
        t = PI / 2 - PI * i / n
        pts.append((cx + r * k * math.cos(t), cy + r * math.sin(t)))
    if not lit_right:
        pts = [(2 * cx - x, y) for x, y in pts]
    cv.obj([pts], .5)
    # a few contour lines on the lit limb to model it
    for f in (.93,):
        arc = [(cx + r * f * math.cos(t), cy + r * f * math.sin(t)) for t in
               [-PI / 2 * .7 + PI * .7 * i / 16 for i in range(17)]]
        if not lit_right:
            arc = [(2 * cx - x, y) for x, y in arc]
        cv.hair(arc)


# ------------------------------------------------------------------------------------------------
# the salmon
# ------------------------------------------------------------------------------------------------

_PROFILES = {
    # u (tail base 0 -> snout 1): half depth / L
    "chinook": [(0, .05), (.1, .04), (.22, .065), (.38, .105), (.55, .122), (.72, .108),
                (.85, .082), (.95, .045), (1, .008)],
    "coho": [(0, .048), (.1, .038), (.22, .06), (.4, .098), (.56, .11), (.72, .095),
             (.86, .07), (.95, .04), (1, .008)],
    "chum": [(0, .05), (.1, .04), (.22, .066), (.4, .1), (.56, .112), (.72, .1),
             (.86, .075), (.95, .045), (1, .012)],
    "steelhead": [(0, .045), (.1, .036), (.22, .055), (.4, .085), (.56, .095), (.72, .085),
                  (.86, .065), (.95, .038), (1, .01)],
}


class _Fish:
    def __init__(self, bx, by, th0, L, bend, flip, kind):
        self.bx, self.by, self.th0, self.L = bx, by, th0, L
        self.k = bend / L
        self.flip = flip
        self.prof = _PROFILES[kind]

    def hh(self, u):
        return _interp(self.prof, u) * self.L

    def spine(self, u):
        s = u * self.L
        th = self.th0 + self.k * s if u > 0 else self.th0
        if u <= 0:
            return self.bx + math.cos(self.th0) * s, self.by + math.sin(self.th0) * s, th
        if abs(self.k) < 1e-6:
            return self.bx + math.cos(th) * s, self.by + math.sin(th) * s, th
        k = self.k
        x = self.bx + (math.sin(self.th0 + k * s) - math.sin(self.th0)) / k
        y = self.by - (math.cos(self.th0 + k * s) - math.cos(self.th0)) / k
        return x, y, th

    def P(self, u, off):
        x, y, th = self.spine(u)
        return (x + math.sin(th) * off * self.flip, y - math.cos(th) * off * self.flip)

    def S(self, u, s):
        return self.P(u, s * self.hh(u))


def salmon(cv, bx, by, th0, L, bend=0., flip=1, kind="chinook", seed=0, detail=1.):
    """An engraved salmon. (bx, by) the tail base; th0 heading there (rad); L body length
    (snout to tail base); bend total curvature (rad); flip=-1 for a fish heading left so the
    back stays up. Draw order: fins behind, body, pectoral, eye."""
    F = _Fish(bx, by, th0, L, bend, flip, kind)
    rng = random.Random(seed)
    P, S, hh = F.P, F.S, F.hh
    fine = L > 70

    def fin(base0, base1, tip_pts, rays=5, dark=False):
        poly = [base0] + tip_pts + [base1]
        cv.obj([poly], .5 if L < 60 else 1.)
        m = len(tip_pts)
        nr = rays if L > 40 else 2
        for i in range(nr):
            t = (i + .5) / nr
            b = (base0[0] + (base1[0] - base0[0]) * t, base0[1] + (base1[1] - base0[1]) * t)
            e = tip_pts[min(m - 1, int(t * m))]
            cv.hair([b, (b[0] + (e[0] - b[0]) * .92, b[1] + (e[1] - b[1]) * .92)])
        if dark:
            cv.hair(C.hatch_poly(poly, math.degrees(th0) + 60, 1.5))

    # --- tail (behind body)
    h0 = hh(0)
    tl = L * .21
    tail = [P(.03, h0 * .9), P(-.08, L * .1), P(-tl / L, L * .155), P(-.16, L * .07), P(-.12, 0),
            P(-.16, -L * .07), P(-tl / L, -L * .155), P(-.08, -L * .1), P(.03, -h0 * .9)]
    cv.obj([tail], .5 if L < 60 else 1.)
    for i in range(9 if fine else 5):
        t = i / (8 if fine else 4)
        e = P(-tl / L + (.09 * (1 - abs(2 * t - 1))), L * .155 * (1 - 2 * t))
        cv.hair([P(.02, 0), e])
    if fine:
        cv.hair(C.hatch_poly(tail, math.degrees(th0) - 50, 2))
    # tail spots
    for _ in range(int(9 * detail) if L > 40 else 0):
        a = rng.uniform(.25, .95) * rng.choice((-1, 1))
        q = P(-rng.uniform(.04, .17), L * .13 * a)
        cv.heavy([q, (q[0] + .3, q[1] + .2)])

    # --- dorsal, adipose, anal, pelvic fins (behind)
    fin(S(.6, .93), S(.44, .93), [P(.56, hh(.56) + L * .07), P(.47, hh(.47) + L * .09), P(.42, hh(.42) + L * .05)], 6)
    fin(S(.23, .9), S(.18, .9), [P(.18, hh(.18) + L * .035)], 2)
    fin(S(.32, -.93), S(.22, -.93), [P(.27, -hh(.27) - L * .07), P(.2, -hh(.2) - L * .06)], 5)
    fin(S(.52, -.93), S(.45, -.93), [P(.45, -hh(.45) - L * .07), P(.42, -hh(.42) - L * .045)], 4)

    # --- body
    n = 44
    top = [S(i / n, 1) for i in range(n + 1)]
    bot = [S(1 - i / n, -1) for i in range(n + 1)]
    body = top + bot[1:-1]
    cv.obj([body], 1. if L > 30 else .5)
    hmax = max(hh(i / 20) for i in range(21))
    pitch = 1.5
    nl = max(6, int(2 * hmax / pitch))
    if nl % 2:
        nl += 1
    for i in range(1, nl):
        s = 1 - 2 * i / nl
        d = _depth(i)
        # back dark (every level), flank every 2nd, belly every 4th (silver)
        if s < -.45 and d > 1:
            continue
        if -.45 <= s < .25 and d > 2:
            continue
        need = pitch * nl / 2 / (2 ** (3 - d)) * .95
        u0, u1 = .03, (.97 if s > .25 else .8)
        run = []
        for j in range(61):
            u = u0 + (u1 - u0) * j / 60
            if hh(u) >= need and abs(s) < .985:
                run.append(S(u, s))
            elif run:
                if len(run) > 1:
                    cv.hair(run)
                run = []
        if len(run) > 1:
            cv.hair(run)
    # the dark back: a second, crossing layer of short strokes laid along the scale rows
    if L > 30:
        q = hmax / L
        for sign, lo, hi, sp in ((1, .42, .97, 2.2), (1, -.42, .4, 3.4), (-1, -.42, .4, 3.4)):
            v = -.2
            while v < 1.2:
                seg = []
                for j in range(11):
                    s2 = lo + (hi - lo) * j / 10
                    u = v + sign * s2 * q * 1.1
                    if .07 < u < (.79 if s2 < .3 else .9) and hh(u) > hmax * .45:
                        seg.append(S(u, s2))
                    elif len(seg) > 1:
                        cv.hair(seg)
                        seg = []
                    else:
                        seg = []
                if len(seg) > 1:
                    cv.hair(seg)
                v += sp / L
    # lateral line
    cv.line([S(u / 30 * .76 + .05, .1) for u in range(31)])
    # spots on the back
    for _ in range(int(22 * detail) if L > 40 else 4):
        u, s = rng.uniform(.1, .8), rng.uniform(.35, .9)
        q = S(u, s)
        cv.heavy([q, (q[0] + .3, q[1] + .2)])
    # gill cover
    gill = [S(.8 - .035 * math.sin(PI * j / 12), .85 - 1.7 * j / 12) for j in range(13)]
    cv.line(gill)
    if L > 40:
        gill2 = [S(.84 - .025 * math.sin(PI * j / 10), .5 - 1.2 * j / 10) for j in range(11)]
        cv.hair(gill2)
    # mouth / kype
    cv.line([S(1., -.05), P(.93, -hh(.93) * .3), P(.86, -hh(.86) * .4)])
    # --- pectoral (over body)
    pb = S(.78, -.55)
    pe = [P(.66, -hh(.66) * 1.1), P(.7, -hh(.7) * 1.25)]
    cv.obj([[S(.8, -.4)] + pe + [S(.76, -.7)]], .5)
    for t in (.25, .5, .75):
        cv.hair([pb, (pe[0][0] * (1 - t) + pe[1][0] * t, pe[0][1] * (1 - t) + pe[1][1] * t)])
    # --- eye
    er = max(1.2, L * .022)
    ec = S(.915, .3)
    cv.obj([_circle(ec[0], ec[1], er, 16)], .5 if L < 60 else 1.)
    cv.heavy([(ec[0] - .2, ec[1]), (ec[0] + .2, ec[1] + .1)])
    if er > 2:
        cv.line([(ec[0] - er * .35, ec[1] - er * .2), (ec[0] + er * .35, ec[1] + er * .2)])
    return F


def lamprey(cv, x, y, L, seed=0):
    """Pacific lamprey: an eel-like body with a sucker disc, gill pores and a low dorsal fin."""
    pts_t, pts_b = [], []
    n = 30
    for i in range(n + 1):
        u = i / n
        cy = y + math.sin(u * TAU * 1.1 + seed) * L * .04
        hh = L * .045 * (1 - (1 - u) ** 6) * (1 - u ** 8 * .5)
        pts_t.append((x + u * L, cy - hh))
        pts_b.append((x + u * L, cy + hh))
    body = pts_t + pts_b[::-1]
    cv.obj([body], .5)
    cv.hair(C.hatch_poly(body, 75, 1.5))
    cv.hair([(px, py + 1) for px, py in pts_t[2:-2]])
    for k in range(7):
        q = pts_t[n - 5 - k // 2]
        cv.heavy([(x + L * (.82 - k * .025), q[1] + L * .035), (x + L * (.82 - k * .025) + .2, q[1] + L * .035)])


# ------------------------------------------------------------------------------------------------
# the small figures: heron, boat with angler and dog
# ------------------------------------------------------------------------------------------------

def heron(cv, x, y, h):
    """A great blue heron standing at (x, y) (feet), h tall, facing left."""
    U = lambda p: (x + (p[0] - .5) * h, y + (p[1] - 1) * h)
    legs = [[(.52, .62), (.5, 1.)], [(.58, .62), (.6, .98)]]
    cv.obj([], 0)
    for l in legs:
        cv.line([U(p) for p in l])
    body = [(.92, .58), (.78, .44), (.6, .4), (.55, .3), (.6, .2), (.56, .1), (.48, .04), (.42, .05),
            (.12, .085), (.4, .1), (.44, .14), (.5, .2), (.46, .3), (.44, .44), (.5, .6), (.66, .64)]
    poly = [U(p) for p in body]
    cv.obj([poly], .5)
    cv.hair(C.hatch_poly(poly, 15, 1.5))
    cv.hair([U((.47, .045)), U((.6, .02)), U((.68, .05))])      # crest plume
    if h > 25:
        cv.hair(C.hatch_poly([U(p) for p in [(.6, .42), (.9, .58), (.62, .6)]], -40, 1.5))


def dog(cv, x, y, h, face=1):
    """Parker's dog sitting (feet at x, y), h tall, facing `face` (+1 right)."""
    pts = [(-.2, 1.), (-.28, .78), (-.22, .55), (-.05, .38), (.02, .2), (.0, .06), (.08, 0.),
           (.14, .08), (.2, .07), (.3, .12), (.42, .17), (.44, .25), (.28, .3), (.2, .34),
           (.2, .5), (.24, .78), (.26, 1.)]
    poly = [(x + p[0] * h * face, y + (p[1] - 1) * h) for p in pts]
    cv.obj([poly], .5)
    cv.hair(C.hatch_poly(poly, 70, 1.5))
    cv.hair([(x - .32 * h * face, y - .05 * h), (x - .5 * h * face, y - .2 * h)])   # tail


def boat(cv, x, y, w, seed=0):
    """A drift boat seen side-on with the angler seated aft and the dog at the bow.
    (x, y) the waterline centre; w its length. Returns the rod tip."""
    h = w * .2
    hull = []
    for i in range(21):
        t = i / 20
        hull.append((x - w / 2 + w * t, y - h * (.55 + .45 * abs(2 * t - 1) ** 2.2)))
    for i in range(21):
        t = 1 - i / 20
        hull.append((x - w * .38 + w * .76 * t, y + h * .1 * math.sin(PI * t)))
    # angler (behind hull top)
    ax, ay = x - w * .12, y - h * .55
    bodyp = [(ax - w * .05, ay), (ax - w * .045, ay - h * .9), (ax - w * .02, ay - h * 1.25),
             (ax + w * .03, ay - h * 1.25), (ax + w * .055, ay - h * .8), (ax + w * .05, ay)]
    cv.obj([bodyp], .5)
    cv.hair(C.hatch_poly(bodyp, 80, 1.5))
    hx, hy = ax + w * .005, ay - h * 1.55
    cv.obj([_circle(hx, hy, h * .3, 12)], .5)
    cv.hair(C.hatch_poly(_circle(hx, hy, h * .3, 12), 0, 1.5))
    brim = [(hx - h * .55, hy - h * .12), (hx + h * .55, hy - h * .12), (hx + h * .35, hy - h * .28),
            (hx + h * .25, hy - h * .55), (hx - h * .25, hy - h * .55), (hx - h * .35, hy - h * .28)]
    cv.obj([brim], .5)
    cv.hair(C.hatch_poly(brim, 0, 1.5))
    # rod: from hands sweeping up and back over the stern, line down to the water
    hand = (ax + w * .06, ay - h * .75)
    tip = (x - w * .62, y - h * 3.4)
    rod = []
    for i in range(13):
        t = i / 12
        rod.append((hand[0] + (tip[0] - hand[0]) * t, hand[1] + (tip[1] - hand[1]) * t - h * .9 * math.sin(PI * t) * t))
    cv.line(rod[:5])
    cv.hair(rod[4:])
    # line: catenary down to the river
    end = (tip[0] - w * .12, y + h * .1)
    cv.hair([(tip[0] + (end[0] - tip[0]) * t, tip[1] + (end[1] - tip[1]) * t ** 1.6) for t in [i / 10 for i in range(11)]])
    # dog at the bow (the Easter egg)
    dog(cv, x + w * .3, y - h * .62, h * 1.25, 1)
    cv.obj([hull], 1.)
    cv.hair(C.hatch_poly(hull, 0, 1.5))
    cv.hair(C.hatch_poly(hull, 60, 3))
    cv.line([hull[k] for k in range(21)])
    # gunwale highlight band
    cv.obj([[(p[0], p[1]) for p in hull[2:19]] + [(p[0], p[1] + h * .28) for p in hull[18:1:-1]]], 0)
    cv.hair([(p[0], p[1] + h * .14) for p in hull[3:18]])
    return end


# ------------------------------------------------------------------------------------------------
# the scene: dusk on the Columbia
# ------------------------------------------------------------------------------------------------

def _wavy(x0, x1, y, amp, wl, ph, step=3.):
    n = max(2, int((x1 - x0) / step))
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin((x0 + (x1 - x0) * i / n) / wl + ph)) for i in range(n + 1)]


def scene(x, y, W, H, ctx, mode, seed=0):
    """The river at the dusk bite, filling the box x, y, W, H completely (no white). The caller
    clips it to the field. mode: 'band', 'medium' or 'tall'. Returns a Canvas."""
    rng = random.Random(seed)
    cv = C.Canvas()
    x1, y1 = x + W, y + H
    small = mode == "band"
    yh = y + H * (.5 if small else .5)               # horizon (far shore waterline)
    box = [(x, y), (x1, y), (x1, y1), (x, y1)]

    # sky: fine rules at the zenith opening toward the horizon, broken round the setting sun
    sx, sr = x + W * (.3 if not small else .27), H * (.1 if not small else .14)
    sy = yh - H * .07
    R2 = sr * (2.5 if not small else 2.1)
    cv.obj([box], 0)
    yy = y + .5
    while yy < yh:
        t = (yy - y) / max(1, yh - y)
        pitch = 1.5 if t < .6 else (2 if t < .85 else 3)
        dy = yy - sy
        if abs(dy) < R2:
            dx = math.sqrt(R2 * R2 - dy * dy)
            if sx - dx > x:
                cv.hair([(x, yy), (sx - dx, yy)])
            if sx + dx < x1:
                cv.hair([(sx + dx, yy), (x1, yy)])
        else:
            cv.hair([(x, yy), (x1, yy)])
        yy += pitch
    # sun rays
    nr = 44 if not small else 30
    for i in range(nr):
        a = PI + PI * 1.1 * (i + .5) / nr - PI * .05
        r0 = sr * 1.25
        r1 = R2 * (1. if i % 2 else .8)
        cv.hair([(sx + r0 * math.cos(a), sy + r0 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    # the sun disc in fine horizontal rules
    disc = _circle(sx, sy, sr, 40)
    cv.obj([disc], .5)
    cv.hair(C.hatch_poly(disc, 0, 2 if small else 3, .5))
    # moon: today's phase
    ph = _moon_phase((ctx or {}).get("date", ""))
    mr = H * (.055 if not small else .085)
    _moon(cv, x + W * (.72 if not small else .74), y + H * (.2 if not small else .26), mr, ph)
    if not small:
        for k in range(7):     # a few early stars in the darker sky
            px, py = x + W * rng.uniform(.5, .97), y + H * rng.uniform(.06, .32)
            if math.hypot(px - (x + W * .72), py - (y + H * .2)) > mr * 2.5:
                cv.obj([[(px - 1.6, py), (px, py - 1.6), (px + 1.6, py), (px, py + 1.6)]], 0)
                cv.hair([[(px - 1.8, py), (px + 1.8, py)], [(px, py - 1.8), (px, py + 1.8)]])

    # distant hills (Tualatin / Coast Range), light ruling
    hill = [(x, yh - H * .05)]
    for i in range(41):
        t = i / 40
        hill.append((x + W * t, yh - H * (.075 + .05 * math.sin(t * 5.3 + 1) + .025 * math.sin(t * 13 + seed % 7))))
    hill += [(x1, yh), (x, yh)]
    cv.obj([hill], .5)
    cv.hair(C.hatch_poly(hill, 0, 1.5, .25))
    # Sauvie Island cottonwoods: a dark bumpy tree line
    trees = [(x, yh)]
    th = H * (.06 if not small else .07)
    for i in range(int(W / 2.5) + 1):
        t = i / int(W / 2.5)
        px = x + W * t
        bump = abs(math.sin(px / (3.2 if small else 4.3) + seed)) ** .6
        tall = .55 + .45 * math.sin(px / 21. + 1.3) ** 2
        if abs(px - sx) < sr * 1.2:
            tall *= .55
        trees.append((px, yh - th * (.35 + .65 * bump * tall)))
    trees += [(x1, yh + 1.5), (x, yh + 1.5)]
    cv.obj([trees], .5)
    cv.hair(C.hatch_poly(trees, 0, 1.5))
    cv.hair(C.hatch_poly(trees, 90, 1.5, .75))

    # the river: wavy rules, close under the far shore, opening toward us; sun glitter column
    cv.obj([[(x, yh + 1), (x1, yh + 1), (x1, y1), (x, y1)]], .5)
    yy = yh + 2.5
    j = 0
    while yy < y1 + 1:
        t = (yy - yh) / max(1, y1 - yh)
        pitch = 1.5 if t < .25 else 2
        amp = .25 + .45 * t
        line = _wavy(x, x1, yy, amp, 7 + 9 * t, j * 1.7 + seed, 2.5)
        # glitter under the sun: break the rule into dashes
        gw = sr * (1.1 + .9 * t)
        segs, cur = [], []
        for p in line:
            inside = abs(p[0] - sx) < gw
            if inside and rng.random() < .35 * (1 - .6 * t):
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1:
            segs.append(cur)
        for sgm in segs:
            cv.hair(sgm)
        yy += pitch
        j += 1

    # reeds and the heron at the near left shore (Easter egg: Sauvie Island's great blue heron)
    hx = x + W * (.12 if not small else .2)
    hy = yh + H * (.13 if not small else .16)
    hh = H * (.17 if not small else .27)
    reeds = [(hx - hh * 1.2, hy + 2), (hx + hh * .8, hy + 2), (hx + hh * .5, hy - 1), (hx - hh * .9, hy - 1)]
    heron(cv, hx, hy, hh)
    cv.obj([], 0)
    for i in range(9 if not small else 5):
        rx = hx - hh * 1.1 + i * hh * .24 + rng.uniform(-1, 1)
        rh = hh * rng.uniform(.25, .6)
        lean = rng.uniform(-.25, .25) * rh
        cv.hair([(rx, hy + 2), (rx + lean * .5, hy + 2 - rh * .6), (rx + lean, hy + 2 - rh)])
    for k in range(3):
        cv.hair(_wavy(hx - hh * 1.2, hx + hh * .9, hy + 3 + k * 1.6, .3, 3, k, 2))

    # the boat with the angler and his dog (not in the small band)
    if True:
        bw = W * (.26 if not small else .2)
        bxc, byc = x + W * (.7 if not small else .78), yh + H * (.12 if not small else .1)
        end = boat(cv, bxc, byc, bw, seed)
        for k in range(3):    # its wake / reflection rules
            cv.obj([], 0)
            cv.hair(_wavy(bxc - bw * .5, bxc + bw * .5, byc + 2 + k * 2, .5, 3, k, 2))

    # the leaping chinook, spray and rings where it broke the surface
    if small:
        L = min(H * .9, W * .36)
        fx, fy = x + W * .66, y + H * .88
        th0, bend = -2.25, -1.25
    else:
        L = min(W * .5, H * .78)
        fx, fy = x + W * .74, y + H * .9
        th0, bend = -2.3, -1.25
    wy = fy + H * .06
    # rings on the water first (under the spray)
    cv.obj([], 0)
    for k in range(4 if not small else 3):
        rx, ry = L * (.18 + .13 * k), L * (.03 + .02 * k)
        ring = [(fx + rx * math.cos(TAU * i / 40), wy + ry * math.sin(TAU * i / 40)) for i in range(41)]
        cv.line(ring[:21]) if k == 0 else cv.hair(ring[:21])
    salmon(cv, fx, fy, th0, L, bend, -1, "chinook", seed, 1.)
    # spray: droplets flung off the tail and rising sheets
    for i in range(16 if not small else 8):
        a = -PI / 2 + rng.uniform(-1.1, 1.1)
        d = L * rng.uniform(.1, .3)
        px, py = fx + d * math.cos(a) + L * .05, wy - L * .04 + d * math.sin(a) * .9
        r = rng.uniform(.8, 1.6) if not small else rng.uniform(.6, 1.)
        cv.obj([_circle(px, py, r, 8)], .5)
    for i in range(7 if not small else 4):
        a0 = -PI / 2 + (i - 3) * .32
        pts = [(fx + L * .04 + math.cos(a0) * L * .12 * t, wy - math.sin(-a0) * L * .2 * t + L * .1 * t * t)
               for t in [k / 8 for k in range(9)]]
        cv.hair(pts)
    return cv


# ------------------------------------------------------------------------------------------------
# tide curve for the ribbon, and the run of fish for the tablet
# ------------------------------------------------------------------------------------------------

def _tides(ctx):
    """[(hour, ft)] from the page text 'tide turning (low 0.1 ft) 12:32-3:46 am' rows (midpoint
    of each window); falls back to a typical day."""
    s = (ctx or {}).get("sample", "") or ""
    out = []
    for m in re.finditer(r"\((low|high)\s+(-?[\d.]+)\s*ft\)[^\d]{0,40}?(\d{1,2}):(\d\d)\s*(am|pm)?\s*[–-]\s*(\d{1,2}):(\d\d)\s*(am|pm)", s):
        def hr(h, mi, ap):
            h = int(h) % 12 + (12 if ap == "pm" else 0)
            return h + int(mi) / 60
        ap2 = m.group(8)
        a = hr(m.group(3), m.group(4), m.group(5) or ap2)
        b = hr(m.group(6), m.group(7), ap2)
        if b < a:
            b += 24 if ap2 == "am" else 12
        out.append(((a + b) / 2, float(m.group(2))))
    if len(out) < 2:
        out = [(2.1, .1), (7.2, 1.7), (13.4, .7), (19.5, 3.3)]
    return out


def _tide_at(tides, hr):
    pts = sorted(tides)
    if hr <= pts[0][0]:
        a, b = (pts[0][0] - 6.2, pts[1][1]), pts[0]
    elif hr >= pts[-1][0]:
        a, b = pts[-1], (pts[-1][0] + 6.2, pts[-2][1])
    else:
        a, b = next((p, q) for p, q in zip(pts, pts[1:]) if p[0] <= hr <= q[0])
    t = (hr - a[0]) / max(.1, b[0] - a[0])
    return a[1] + (b[1] - a[1]) * (1 - math.cos(PI * t)) / 2


def ribbon_tide(face, h, ctx):
    """Engrave today's tide curve along the ribbon face (centre points), with the water under it
    in vertical rules and the sky above in light horizontal rules -- the banner's 'lettering'."""
    if not face or h < 8:
        return ""
    tides = _tides(ctx)
    lo, hi = min(t[1] for t in tides) - .3, max(t[1] for t in tides) + .3
    n = len(face) - 1
    cv = C.Canvas()
    cv.obj([], 0)
    curve = []
    fill = []
    for i in range(n + 1):
        cxp, cyp = face[i]
        hr = 24 * i / n
        v = (_tide_at(tides, hr) - lo) / (hi - lo)
        yv = cyp + h * (.3 - .6 * v)
        curve.append((cxp, yv))
    cv.line(curve)
    # water: vertical rules from curve down to the lower face edge
    x0, x1 = face[0][0], face[-1][0]
    xx = x0 + 1
    while xx < x1 - 1:
        f = (xx - x0) / (x1 - x0) * n
        i = min(n - 1, int(f))
        t = f - i
        cy = face[i][1] * (1 - t) + face[i + 1][1] * t
        yc = curve[i][1] * (1 - t) + curve[i + 1][1] * t
        cv.hair([(xx, yc + 1.2), (xx, cy + h * .38)])
        cv.hair([(xx, cy - h * .38), (xx, cy - h * .38 + .01)]) if False else None
        xx += 2
    # sky: two light rules above the curve
    for k in (-.3, -.15):
        seg = []
        for i in range(n + 1):
            yy = face[i][1] + h * k
            if yy < curve[i][1] - 1.2:
                seg.append((face[i][0], yy))
            elif len(seg) > 1:
                cv.hair(seg)
                seg = []
            else:
                seg = []
        if len(seg) > 1:
            cv.hair(seg)
    # hour ticks along the top and the high-tide marks
    for hr in range(0, 25, 3):
        i = int(round(hr / 24 * n))
        cv.hair([(face[i][0], face[i][1] - h * .42), (face[i][0], face[i][1] - h * .3)])
    for hr, ft in tides:
        if 0 <= hr <= 24:
            f = hr / 24 * n
            i = min(n, int(round(f)))
            q = curve[i]
            cv.heavy([(q[0], q[1]), (q[0] + .2, q[1])])
    return cv.svg()


def tablet_run(tx, ty, tw, th, seed=0):
    """The tablet: this week's run over Bonneville swimming upriver in file on ruled water."""
    cv = C.Canvas()
    box = [(tx + 1, ty + 1), (tx + tw - 1, ty + 1), (tx + tw - 1, ty + th - 1), (tx + 1, ty + th - 1)]
    cv.obj([box], 0)
    yy = ty + 2.5
    while yy < ty + th - 1:
        cv.hair(_wavy(tx + 1.5, tx + tw - 1.5, yy, .35, 4, yy, 3))
        yy += 3
    L = min(th * 3.3, tw / 6.6)
    order = [("chinook", 1.05), ("chum", .95), ("coho", .9), ("lamprey", .85), ("steelhead", .92)]
    gap = (tw - sum(L * s for _, s in order) * 1.25) / (len(order) + 1)
    px = tx + gap + L * .25
    for i, (kind, s) in enumerate(order):
        cy = ty + th * .55 + (i % 2 - .5) * th * .08
        if kind == "lamprey":
            lamprey(cv, px, cy, L * s, seed)
        else:
            salmon(cv, px, cy, 0., L * s, .06 * (1 if i % 2 else -1), 1, kind, seed + i, .5)
        px += L * s * 1.25 + gap
    return cv.svg()


# ------------------------------------------------------------------------------------------------
# assembly on the house frame
# ------------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, fill_fn):
    """engraving_codex._layout_band with a wider medallion so the river scene has room."""
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.1, 168)
    o.append(C._clip(C._uid("rvb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .72, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    o.append(fill_fn(0, 0, 0, 0))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "")
    seed = sum(map(ord, date))
    cap = {}
    o_cart, o_rib, o_ped = C.cartouche, C.ribbon_banner, C.pedestal

    def cart(cx, cy, cw, ch, *a, **k):
        r = o_cart(cx, cy, cw, ch, *a, **k)
        bw = max(5., min(cw, ch) * .07)
        A, B = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
        cap["field"] = (cx - A, cy - B, 2 * A, 2 * B, r[2])
        return r

    def rib(cx, cy, rw, rh, *a, **k):
        r = o_rib(cx, cy, rw, rh, *a, **k)
        cap["rib"] = (r[1], rh)
        return r

    def ped(*a, **k):
        r = o_ped(*a, **k)
        cap["tab"] = r[1]
        return r

    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")

    def vignette(ix, iy, iw, ih):
        if mode == "band":
            top = 7.
            gh = h - top - 2
            gap = min(gh * 2.1, 168)
            cx, cy, rx, ry = w / 2, top + gh / 2, gap / 2 - 2, gh / 2 - 3
            fx, fy, fw, fh = cx - rx, cy - ry, 2 * rx, 2 * ry
            clip = _d(C._ell_pts(cx, cy, rx, ry, 64), True, 0)
        else:
            fx, fy, fw, fh, clip = cap["field"]
        cid = "rv3f%d%d" % (int(w), int(h))
        body = scene(fx, fy, fw, fh, ctx, mode, seed).svg()
        return (f'<clipPath id="{cid}"><path d="{clip}"/></clipPath>'
                f'<g clip-path="url(#{cid})">{body}</g>')

    C.cartouche, C.ribbon_banner, C.pedestal = cart, rib, ped
    try:
        if mode == "band":
            svg = C.svg_doc(w, h, _layout_band(w, h, seed, vignette))
        else:
            svg = C.frame_plate(w, h, seed, vignette, density=.85 if h > 260 else 1.)
    finally:
        C.cartouche, C.ribbon_banner, C.pedestal = o_cart, o_rib, o_ped

    extra = []
    if mode == "tall" and "field" in cap:
        # a pair of chinook leap out of the leafwork either side of the cartouche
        fx, fy, fw, fh, _ = cap["field"]
        cv = C.Canvas()
        L = min(fw * .5, fh * .55)
        for side in (-1, 1):
            bx = w / 2 + side * (fw / 2 + L * .42)
            by = fy + fh * .74
            if side < 0:
                salmon(cv, bx, by, -2.05, L, -1.15, -1, "chinook", seed + 11, 1.)
            else:
                salmon(cv, bx, by, -PI + 2.05, L, 1.15, 1, "chinook", seed + 12, 1.)
        extra.append(cv.svg())
    if mode == "tall":
        if "rib" in cap:
            extra.append(ribbon_tide(cap["rib"][0], cap["rib"][1], ctx))
        if "tab" in cap:
            extra.append(tablet_run(*cap["tab"], seed=seed))
    if extra:
        svg = svg[:-6] + "".join(extra) + "</svg>"
    if mode == "tall":
        # the free margin above the panel takes the page's own 45-degree ruling, so no white shows
        i = svg.index("</defs>") + 7
        svg = svg[:i] + f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("D")}" stroke="none"/>' + svg[i:]
    return svg
