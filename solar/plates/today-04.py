"""today-04 - "Coming up for you" (Parker's calendar). Today: Trail Blazers vs. Oklahoma City
Thunder at the Moda Center, 7 pm, with two more Blazers road games later in the week.

The plate is a night game engraved in the house acanthus: a basketball dropping into a hoop and
net under a ruled night sky. Tall plates add Mt. Hood on the horizon with a Thunder bolt striking
behind it, a ribbon banner lettered RIP CITY, and a pedestal whose tablet is engraved as a
seven-day calendar strip with a tiny ball on each Blazers game day parsed from the page.
The two main volutes curl into basketballs instead of drilled eyes.
Easter egg: Parker's crossed drumsticks lying on the court under the hoop.
The moon phase follows ctx["date"].
"""
import sys
import math
import random
import re
import datetime
import engraving_codex as C

_n = C._n
_d = C._d
E = C._ell_pts
PI = math.pi
TAU = 2 * PI

# page background hatch (the Kindle page's "\" ruling) so no bare paper shows round the plate
_BG = ('<defs><pattern id="t4bg" width="3" height="3" patternUnits="userSpaceOnUse">'
       f'<path d="{C._diag(3, True)}" stroke="#000" stroke-width=".5"/></pattern></defs>')


def _bg(w, h):
    return _BG + f'<path d="M0,0H{_n(w)}V{_n(h)}H0z" fill="url(#t4bg)" stroke="none"/>'


# ----------------------------------------------------------------------------------------------
# the page's week: which of the next 7 days carry a Blazers game
# ----------------------------------------------------------------------------------------------

_MON = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def _week(ctx):
    try:
        d0 = datetime.date.fromisoformat((ctx or {}).get("date", "")[:10])
    except Exception:
        d0 = datetime.date(2026, 11, 11)
    s = (ctx or {}).get("sample", "") or ""
    pat = re.compile(r"\b(Today|Tomorrow|(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), "
                     r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2}))\b")
    ms = list(pat.finditer(s))
    games = set()
    for i, m in enumerate(ms):
        seg = s[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(s)]
        if m.group(1) == "Today":
            off = 0
        elif m.group(1) == "Tomorrow":
            off = 1
        else:
            try:
                dd = datetime.date(d0.year, _MON[m.group(2)], int(m.group(3)))
                if dd < d0 - datetime.timedelta(days=200):
                    dd = datetime.date(d0.year + 1, dd.month, dd.day)
                off = (dd - d0).days
            except Exception:
                continue
        if 0 <= off < 7 and re.search(r"Blazers|Trail", seg):
            games.add(off)
    if not games and "Blazers" in s:
        games.add(0)
    return d0, games


def _moon(d0):
    """phase 0..1 (0 new, .5 full) from a known new moon."""
    ref = datetime.date(2026, 1, 18)
    return ((d0 - ref).days / 29.530588) % 1.


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def _seg_circle(p, u, c, r):
    """parameter interval of line p + t*u (u unit) inside circle (c, r), or None."""
    dx, dy = p[0] - c[0], p[1] - c[1]
    b = dx * u[0] + dy * u[1]
    cc = dx * dx + dy * dy - r * r
    disc = b * b - cc
    if disc <= 0:
        return None
    s = math.sqrt(disc)
    return (-b - s, -b + s)


def _sphere_shade(cv, cx, cy, r, light=(-.6, -.7), tiers=((.3, 2., 32), (.62, 2., -38), (.85, 1.5, 32))):
    """Crescent shading of a sphere: for each tier (shift, pitch, angle) hatch the part of the
    disc outside the disc shifted toward the light by shift*r."""
    L = math.hypot(*light)
    lx, ly = light[0] / L, light[1] / L
    for sh, pitch, ang in tiers:
        a = math.radians(ang)
        u = (math.cos(a), math.sin(a))
        v = (-u[1], u[0])
        c2 = (cx + lx * sh * r, cy + ly * sh * r)
        r2 = r * (1 + sh * .15)
        k = -r
        while k <= r:
            p = (cx + v[0] * k, cy + v[1] * k)
            s = _seg_circle(p, u, (cx, cy), r - .6)
            if s:
                t = _seg_circle(p, u, c2, r2)
                segs = [s] if not t else [(s[0], min(s[1], t[0])), (max(s[0], t[1]), s[1])]
                for a0, a1 in segs:
                    if a1 - a0 > .8:
                        cv.hair([(p[0] + u[0] * a0, p[1] + u[1] * a0), (p[0] + u[0] * a1, p[1] + u[1] * a1)])
            k += pitch


def _rot(p, ax, ay, az):
    x, y, z = p
    c, s = math.cos(ax), math.sin(ax)
    y, z = y * c - z * s, y * s + z * c
    c, s = math.cos(ay), math.sin(ay)
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(az), math.sin(az)
    x, y = x * c - y * s, x * s + y * c
    return x, y, z


def ball(cv, cx, cy, r, spin=0., seams=True):
    """An engraved basketball: white sphere, crescent bulino shading away from the upper-left light,
    the two great-circle seams and the two curved side seams, pebble stipple on the lit side."""
    cv.obj([E(cx, cy, r, r, max(16, int(r * 3)))[:-1]], 1.5 if r > 7 else 1.)
    if r > 5:
        _sphere_shade(cv, cx, cy, r)
    else:
        _sphere_shade(cv, cx, cy, r, tiers=((.45, 1.5, 32),))
    if not seams:
        return
    ax, ay, az = .55 + spin * .3, -.5 + spin, .35
    N = 64
    curves = [[(math.cos(TAU * i / N), math.sin(TAU * i / N), 0.) for i in range(N + 1)],
              [(0., math.cos(TAU * i / N), math.sin(TAU * i / N)) for i in range(N + 1)]]
    k = math.radians(52)
    for sx in (-1, 1):
        curves.append([(sx * math.cos(k), math.sin(k) * math.cos(TAU * i / N), math.sin(k) * math.sin(TAU * i / N))
                       for i in range(N + 1)])
    w = cv.heavy if r > 14 else cv.line if r > 4 else cv.hair
    for cu in curves:
        run = []
        for p in cu:
            x, y, z = _rot(p, ax, ay, az)
            if z > .05:
                run.append((cx + r * .97 * x, cy - r * .97 * y))
            else:
                if len(run) > 1:
                    w(run)
                run = []
        if len(run) > 1:
            w(run)
    if r > 10:
        rng = random.Random(int(cx * 7 + cy))
        for _ in range(int(r * 2.2)):
            a = rng.uniform(PI * .9, PI * 1.6)
            rr = r * math.sqrt(rng.uniform(.05, .55))
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            cv.hair([(x, y), (x + .5, y + .2)])


def hoop(cv, bx, by, U, ground_y):
    """Backboard face-on centred at (bx, by) about 1.3U x .82U, its post running down to
    ground_y, the rim below the target square, and a diamond-meshed net."""
    bw, bh = 1.3 * U, .82 * U
    pw = max(3., .13 * U)
    px = bx + bw * .18
    post = [(px, by), (px + pw, by), (px + pw, ground_y), (px, ground_y)]
    cv.obj([post], 1.)
    cv.hair(C.hatch_poly(post, 90, 1.5, phase=.3))
    face = [(bx - bw / 2, by - bh / 2), (bx + bw / 2, by - bh / 2), (bx + bw / 2, by + bh / 2), (bx - bw / 2, by + bh / 2)]
    cv.obj([face], 1.5)
    inn = [(bx - bw / 2 + 2, by - bh / 2 + 2), (bx + bw / 2 - 2, by - bh / 2 + 2),
           (bx + bw / 2 - 2, by + bh / 2 - 2), (bx - bw / 2 + 2, by + bh / 2 - 2)]
    cv.hair([*inn, inn[0]])
    cv.hair(C.hatch_poly(inn, -55, 3 if U < 40 else 2, inset=.4))
    sq = [(bx - .3 * U, by - .02 * U), (bx + .3 * U, by - .02 * U), (bx + .3 * U, by + .38 * U), (bx - .3 * U, by + .38 * U)]
    cv.obj([sq], 1.)
    rx, ry = .4 * U, max(1.8, .1 * U)
    ry0 = by + bh / 2 + ry * .2
    rcx = bx
    br = [(bx - .08 * U, by + .38 * U), (bx + .08 * U, by + .38 * U), (bx + .05 * U, ry0), (bx - .05 * U, ry0)]
    cv.obj([br], 1.)
    cv.hair(C.hatch_poly(br, 0, 1.5))
    cv.obj([], 0)
    cv.heavy([(rcx + rx * math.cos(t), ry0 + ry * math.sin(t)) for t in [PI + PI * i / 24 for i in range(25)]])
    J = 5 if U > 30 else 3
    Nn = 14 if U > 30 else 10
    nh = .62 * U
    net = []
    for j in range(J + 1):
        f = j / J
        row = []
        for i in range(Nn):
            t = TAU * (i + (.5 if j % 2 else 0)) / Nn
            sh = 1 - .38 * f ** .8
            row.append((rcx + rx * sh * math.cos(t), ry0 + nh * f + ry * sh * math.sin(t)))
        net.append(row)
    for j in range(J):
        a, b = net[j], net[j + 1]
        for i in range(Nn):
            if j % 2 == 0:
                q1, q2 = b[(i - 1) % Nn], b[i]
            else:
                q1, q2 = b[i], b[(i + 1) % Nn]
            cv.hair([a[i], q1])
            cv.hair([a[i], q2])
    cv.obj([], 0)
    cv.heavy([(rcx + rx * math.cos(t), ry0 + ry * math.sin(t)) for t in [PI * i / 24 for i in range(25)]])
    cv.line([(rcx + (rx - 1.2) * math.cos(t), ry0 + 1 + ry * .8 * math.sin(t)) for t in [PI * .1 + PI * .8 * i / 16 for i in range(17)]])
    return (rcx, ry0, rx, ry)


def drumsticks(cv, cx, cy, L):
    """Parker's crossed drumsticks: two tapered sticks with olive tips, crossing at (cx, cy)."""
    for s in (-1, 1):
        a = math.radians(-90 + s * 62)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        p0 = (cx - ux * L * .5, cy - uy * L * .5)
        w0, w1 = max(.9, L * .045), max(.5, L * .022)
        poly = [(p0[0] + nx * w0, p0[1] + ny * w0), (p0[0] + ux * L * .9 + nx * w1, p0[1] + uy * L * .9 + ny * w1),
                (p0[0] + ux * L * .9 - nx * w1, p0[1] + uy * L * .9 - ny * w1), (p0[0] - nx * w0, p0[1] - ny * w0)]
        cv.obj([poly], 1. if L > 20 else .5)
        if L > 14:
            cv.hair([(p0[0] - nx * w0 * .3 + ux, p0[1] - ny * w0 * .3 + uy), (p0[0] + ux * L * .88, p0[1] + uy * L * .88)])
        tx, ty = p0[0] + ux * L * .95, p0[1] + uy * L * .95
        tr = max(.9, L * .05)
        cv.obj([[(tx + ux * tr * 1.3 * math.cos(t) - nx * tr * math.sin(t), ty + uy * tr * 1.3 * math.cos(t) - ny * tr * math.sin(t))
                 for t in [TAU * i / 12 for i in range(12)]]], 1. if L > 20 else .5)


def star(cv, x, y, r):
    cv.obj([E(x, y, r * .9, r * .9, 8)[:-1]], 0)
    cv.hair([(x - r, y), (x + r, y)])
    cv.hair([(x, y - r), (x, y + r)])


def bolt(cv, x0, y0, x1, y1, wd, rng):
    """A Thunder bolt from (x0, y0) zig-zagging down to (x1, y1): white with a black shadow edge."""
    n = 5
    pts = [(x0, y0)]
    for i in range(1, n):
        t = i / n
        pts.append((x0 + (x1 - x0) * t + (wd * 1.6 if i % 2 else -wd * 1.6) * rng.uniform(.7, 1.2), y0 + (y1 - y0) * t))
    pts.append((x1, y1))
    Lp = [(p[0] - wd * (1 - i / n) * .9, p[1]) for i, p in enumerate(pts)]
    Rp = [(p[0] + wd * (1 - i / n) * .9, p[1]) for i, p in enumerate(pts)]
    cv.obj([Lp + Rp[::-1][1:]], 1.)
    cv.heavy(Rp[:-1])


def mt_hood(cv, x0, x1, base, peak_x, peak_h):
    """Mt. Hood: snow-white cone, shadowed east flank ruled down the slope, glacier ridges on the
    lit face, a dark forested apron."""
    px, py = peak_x, base - peak_h
    wl, wr = peak_h * 1.3, peak_h * 1.5
    left = [(px - wl * t ** 1.15, py + peak_h * t) for t in [i / 16 for i in range(17)]]
    right = [(px + wr * t ** 1.1, py + peak_h * t) for t in [i / 16 for i in range(17)]]
    cv.obj([[(px - 1, py - .5), (px + 1.5, py)] + right[1:] + left[::-1][:-1]], 1.)
    for k in range(1, 9):
        f = k / 9
        cv.hair([(px + 1 + wr * .1 * f, py + 2 + peak_h * .05 * f), (px + wr * .55 * f + 2, base - 1)])
    cv.hair(C.hatch_poly([(px + 1, py + 1), (px + wr * .5, base), (px + wr, base)], 70, 2, inset=.3))
    for k in range(1, 5):
        f = k / 5
        cv.hair([(px - 1 - wl * .06 * f, py + 3 + peak_h * .08 * f), (px - wl * .35 * f, py + peak_h * (.45 + .1 * f))])
    fy = base - peak_h * .22
    fpoly = [(x0, fy + 2)]
    rng = random.Random(int(px))
    x = x0
    while x < x1:
        hh = rng.uniform(2.5, 5.)
        fpoly += [(x + 1.2, fy - hh), (x + 2.4, fy + rng.uniform(-.5, 1.))]
        x += 2.4
    fpoly += [(x1, base), (x0, base)]
    cv.obj([fpoly], .5)
    cv.hair(C.hatch_poly(fpoly, 0, 1.5))
    cv.hair(C.hatch_poly(fpoly, 60, 3))


def arena(cv, x0, x1, base, hh):
    """The Moda Center: a glass drum under a shallow domed roof, mullions ruled upright, lit."""
    w = x1 - x0
    roof = [(x0 + w * .04 + (w * .92) * i / 20, base - hh * (.72 + .28 * math.sin(PI * i / 20))) for i in range(21)]
    body = [(x0, base), (x0 + w * .04, base - hh * .72)] + roof[1:-1] + [(x1 - w * .04, base - hh * .72), (x1, base)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly(body, 90, 2, inset=.3))
    cv.line([(x0 + w * .02, base - hh * .36), (x1 - w * .02, base - hh * .36)])
    cv.heavy(roof)
    rp = [(p[0], p[1] - 1.2) for p in roof]
    cv.hair(rp)


def moon(cv, x, y, r, phase):
    cv.obj([E(x, y, r, r, 24)[:-1]], 1.)
    k = math.cos(phase * TAU)
    waxing = phase < .5
    yy = -r + .75
    while yy <= r:
        hw = math.sqrt(max(0., r * r - yy * yy))
        term = hw * k
        a0, a1 = (-hw, term) if waxing else (-term, hw)
        if a1 - a0 > .8:
            cv.hair([(x + a0 + .3, y + yy), (x + a1 - .3, y + yy)])
        yy += 1.5


# ----------------------------------------------------------------------------------------------
# the vignette: a night game
# ----------------------------------------------------------------------------------------------

def _sky_rules(x0, x1, y0, y_h):
    """graded night sky: horizontal rules densening upward."""
    d = []
    yy = y_h - 2
    while yy > y0:
        f = (y_h - yy) / max(1., y_h - y0)
        d.append(f"M{_n(x0)},{_n(yy)}H{_n(x1)}")
        yy -= 2 if f < .25 else 1.5
    return "".join(d)


def scene(x, y, w, h, clip_d, ctx, mode):
    """Everything inside the medallion/cartouche field (clip_d), composed in the box x,y,w,h."""
    rng = random.Random(sum(map(ord, (ctx or {}).get("date", ""))))
    d0, _ = _week(ctx)
    cid = C._uid("t4s", x, y, w, h)
    o = [f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">']
    wide = w / max(h, 1) > 1.6
    if mode == "short":
        U = min(w / 4.4, h / 2.0)
        hz = y + h * .74
    elif mode == "medium":
        U = min(w / 3.1, h / 2.1)
        hz = y + h * .74
    else:
        U = min(w / 2.8, h / 2.6)
        hz = y + h * .7
    X0, X1, Y0, Y1 = x - 40, x + w + 40, y - 40, y + h + 40
    o.append(f'<path d="{_sky_rules(X0, X1, Y0, hz)}" stroke="#000" stroke-width=".5" fill="none"/>')
    cv = C.Canvas()
    if mode != "short":
        mr = max(4., U * .17)
        moon(cv, x + w * .08 + mr, y + mr + 3, mr, _moon(d0))
        for i in range(9 if mode == "tall" else 5):
            star(cv, x + w * rng.uniform(.05, .95), y + (hz - y) * rng.uniform(.04, .55), rng.choice((1.5, 2., 2.5)))
        if mode == "tall":
            bolt(cv, x + w * .3, y - 2, x + w * .3, hz - (hz - y) * .44, max(3., U * .08), rng)
            mt_hood(cv, X0, X1, hz, x + w * .34, (hz - y) * .46)
            arena(cv, x + w * .02, x + w * .32, hz, (hz - y) * .2)
        else:
            mt_hood(cv, X0, X1, hz, x + w * .3, (hz - y) * .42)
    else:
        for i in range(4):
            star(cv, x + w * (.12 + .1 * i) + rng.uniform(-3, 3), y + h * rng.uniform(.1, .32), 1.5)
        bolt(cv, x + w * .22, y - 2, x + w * .2, hz - (hz - y) * .5, 2., rng)
        mt_hood(cv, X0, X1, hz, x + w * .2, (hz - y) * .58)
        arena(cv, x + w * .3, x + w * .5, hz, (hz - y) * .3)
    # the court: hardwood planks in perspective
    floor = [(X0, hz), (X1, hz), (X1, Y1), (X0, Y1)]
    cv.obj([floor], 1.)
    vx, vy = x + w * .5, hz - h * .9
    t = (hz - vy) / (Y1 - vy)
    pl = U * (.2 if mode != "short" else .28)
    prng = random.Random(7)
    for k in range(-40, 41):
        fx = x + w / 2 + k * pl
        a, b = (vx + (fx - vx) * t, hz), (fx, Y1)
        cv.hair([a, b])
        # wood grain: a wandering line down the middle of each plank, joints staggered
        fx2 = fx + pl * .5
        a2 = (vx + (fx2 - vx) * t, hz)
        g = []
        for j in range(13):
            s = j / 12
            gx = a2[0] + (fx2 - a2[0]) * s + math.sin(s * 9 + k) * pl * .12 * s
            g.append((gx, hz + (Y1 - hz) * s))
        cv.hair(g)
        for _ in range(2):
            s = prng.uniform(.15, .95)
            q0 = (a[0] + (b[0] - a[0]) * s, hz + (Y1 - hz) * s)
            fx3 = fx + pl
            a3 = (vx + (fx3 - vx) * t, hz)
            q1 = (a3[0] + (fx3 - a3[0]) * s, hz + (Y1 - hz) * s)
            cv.line([q0, q1])
    cv.hair([(X0, hz + 1.5), (X1, hz + 1.5)])
    bx = x + w * (.74 if wide else .7)
    by = max(y + (h * .26 if mode != "tall" else h * .3), y + .45 * U)
    # the three-point arc, a white painted band across the boards
    ac = (bx, hz + U * .2)
    A, B = U * 1.9, (y + h + 10 - hz) * .75
    outer = [(ac[0] + (A + 1.6) * math.cos(th), ac[1] + (B + 1.2) * math.sin(th)) for th in [PI * i / 40 for i in range(41)]]
    inner = [(ac[0] + A * math.cos(th), ac[1] + B * math.sin(th)) for th in [PI * i / 40 for i in range(41)]]
    cv.obj([outer + inner[::-1]], .5)
    rcx, ry0, rx, ry = hoop(cv, bx, by, U, hz + U * .12)
    # the ball arcing in from the left with a dotted trail
    br = .36 * U
    bxc, byc = rcx - rx * .15, ry0 - br * 1.25
    sx0, sy0 = x + w * .08, hz - U * .15
    apex = max(min(byc - U * .3, y + U * .9), y + U * .55)
    trail = []
    for i in range(9):
        t = .46 + i / 8 * .4
        px = sx0 + (bxc - sx0) * t
        # parabola through start, apex, end
        py = (1 - t) ** 2 * sy0 + 2 * (1 - t) * t * (2 * apex - (sy0 + byc) / 2) + t * t * byc
        trail.append((px, py))
    for i, (tx_, ty_) in enumerate(trail[:-1]):
        rr = .6 + 1.2 * i / len(trail) * (U / 40)
        cv.obj([E(tx_, ty_, rr + .8, rr + .8, 10)[:-1]], 0)
        q = rr
        while q > .2:
            cv.line(E(tx_, ty_, q, q, 10))
            q -= .8
    sh = E(bxc + U * .1, hz + U * .25, br * 1.1, br * .25, 18)[:-1]
    cv.obj([sh], 0)
    cv.line(C.hatch_poly(sh, 0, 1.))
    ball(cv, bxc, byc, br, rng.uniform(-.3, .3))
    # Easter egg: crossed drumsticks on the boards
    dl = U * (.6 if mode == "short" else .5)
    if mode == "short":
        drumsticks(cv, x + w * .36, hz + dl * .32, dl * .85)
    else:
        drumsticks(cv, x + w * .22, min(hz + dl * .55, y + h - dl * .45), dl)
    o.append(cv.svg())
    o.append("</g>")
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# lettering, drawn as paths
# ----------------------------------------------------------------------------------------------

def _c_pts():
    return [(.42 + .42 * math.cos(t), .5 - .5 * math.sin(t)) for t in [.8 + (TAU - 1.6) * i / 20 for i in range(21)]]


_BOWL = [(0, 1), (0, 0), (.55, 0), (.72, .1), (.75, .26), (.7, .4), (.55, .5), (0, .5)]
_GLY = {
    "R": (.8, [_BOWL, [(.38, .5), (.8, 1)], [(-.14, 0), (.1, 0)], [(-.14, 1), (.16, 1)], [(.66, 1), (.94, 1)]]),
    "I": (.0, [[(0, 0), (0, 1)], [(-.15, 0), (.15, 0)], [(-.15, 1), (.15, 1)]]),
    "P": (.75, [_BOWL, [(-.14, 0), (.1, 0)], [(-.14, 1), (.16, 1)]]),
    "C": (.84, [_c_pts(), [(.73, .14), (.74, .3)]]),
    "T": (.8, [[(0, .18), (0, 0), (.8, 0), (.8, .18)], [(.4, 0), (.4, 1)], [(.24, 1), (.56, 1)]]),
    "Y": (.8, [[(0, 0), (.4, .52), (.8, 0)], [(.4, .52), (.4, 1)], [(-.12, 0), (.12, 0)], [(.68, 0), (.92, 0)],
               [(.24, 1), (.56, 1)]]),
    " ": (.4, []),
}


def letter_on(centre, text, cap, track=.32):
    """Letter `text` along the banner's face centre line, cap px high, centred, as one path."""
    S = [0.]
    for i in range(1, len(centre)):
        S.append(S[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    tot = S[-1]
    adv = [(_GLY[ch][0] + track) * cap for ch in text]
    s = (tot - (sum(adv) - track * cap)) / 2

    def at(sv):
        for i in range(1, len(S)):
            if S[i] >= sv:
                t = (sv - S[i - 1]) / max(1e-6, S[i] - S[i - 1])
                p = (centre[i - 1][0] + (centre[i][0] - centre[i - 1][0]) * t,
                     centre[i - 1][1] + (centre[i][1] - centre[i - 1][1]) * t)
                return p, math.atan2(centre[i][1] - centre[i - 1][1], centre[i][0] - centre[i - 1][0])
        return centre[-1], 0.
    d = []
    for ch, ad in zip(text, adv):
        wch, strokes = _GLY[ch]
        p, a = at(s + wch * cap / 2)
        ca, sa = math.cos(a), math.sin(a)
        for st in strokes:
            pts = [((u - wch / 2) * cap, (v - .5) * cap) for u, v in st]
            d.append(_d([(p[0] + px * ca - py * sa, p[1] + px * sa + py * ca) for px, py in pts], tol=0))
        s += ad
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width="1.5" stroke-linecap="square"/>'


# ----------------------------------------------------------------------------------------------
# the calendar tablet
# ----------------------------------------------------------------------------------------------

def week_tablet(tx, ty, tw, th, ctx):
    """The pedestal's tablet as the page's week: seven sunk day cells, today framed double, a
    basketball in every cell with a Blazers game, weekdays ruled upright and weekends across."""
    d0, games = _week(ctx)
    cv = C.Canvas()
    pad = 3
    cw = (tw - pad * 8) / 7
    o = [f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="{C.pat("X")}" stroke="#000" stroke-width="1"/>']
    for i in range(7):
        x0 = tx + pad + i * (cw + pad)
        y0, y1 = ty + pad, ty + th - pad
        cell = [(x0, y0), (x0 + cw, y0), (x0 + cw, y1), (x0, y1)]
        cv.obj([cell], 1.5 if i == 0 else 1.)
        if i == 0:
            cv.line([(x0 + 2, y0 + 2), (x0 + cw - 2, y0 + 2), (x0 + cw - 2, y1 - 2), (x0 + 2, y1 - 2), (x0 + 2, y0 + 2)])
        wd = (d0 + datetime.timedelta(days=i)).weekday()
        cy = (y0 + y1) / 2
        if i in games:
            r = min((y1 - y0) * .38, cw * .2)
            inner = [(x0 + 3.5, y0 + 3.5), (x0 + cw - 3.5, y0 + 3.5), (x0 + cw - 3.5, y1 - 3.5), (x0 + 3.5, y1 - 3.5)]
            cv.hair(C.hatch_poly(inner, 0, 1.5))
            ball(cv, x0 + cw / 2, cy, r, i * .4)
        else:
            cv.hair(C.hatch_poly(cell, 0 if wd >= 5 else 90, 2, inset=1.5))
    o.append(cv.svg())
    return "".join(o)


# ----------------------------------------------------------------------------------------------
# layouts (the house layouts, copied so the field, the eyes and the tablet are ours)
# ----------------------------------------------------------------------------------------------

def _pair_unit(cv, cx, cy, r, side, rng, a_out=0., turns=1.4, tail=.9, up=True, fronds=3, eye_ball=False):
    if up:
        a0, flip = (90 + a_out, True) if side < 0 else (90 - a_out, False)
    else:
        a0, flip = (-90 - a_out, False) if side < 0 else (-90 + a_out, True)
    tb = -.5 if up else .5
    C._volute(cv, cx, cy, r, a0, turns, flip, rng, tail, tb, r * .15, fronds)
    if eye_ball:
        ex, ey = C.volute_spine(cx, cy, r, a0, turns, flip, tail, tb)[-1]
        ball(cv, ex, ey, max(3.5, r * .16), side * .5)


def layout_band(w, h, seed, ctx):
    o = [_bg(w, h)]
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.5, 180)
    o.append(C._clip(C._uid("b4", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = _d(E(cx, cy, rx - 4.5, ry - 4.5, 64), True)
    o.append(scene(cx - rx + 6, cy - ry + 4, 2 * rx - 12, 2 * ry - 6, field, ctx, "short"))
    o.append(f'<path d="{_d(E(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = [_bg(w, h)]
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
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        _pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True, eye_ball=True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m4", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), inner = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene(ix - 4, iy - 2, iw + 8, ih + 4, inner, ctx, "medium"))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = [_bg(w, h)]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True, eye_ball=True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        _pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t4", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, (ix, iy, iw, ih), inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(scene(ix - 6, iy - 6, iw + 12, ih + 12, inner, ctx, "tall"))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(letter_on(centre, "RIP CITY", bh * .58, .42))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(week_tablet(tx, ty, tw, th, ctx))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f4", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 4
    if h < 110:
        body = layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = layout_medium(w, h, seed, ctx)
    else:
        body = layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
