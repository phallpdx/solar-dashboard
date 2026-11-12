"""news-02 "The big stories": the U.S. Capitol under a glory of rays, framed in house acanthus.

The day's most-covered stories are House business (a new minority leader, a failed impeachment),
so the vignette is the Capitol dome: ribbed and shaded dome, colonnaded drum, portico and wings,
on a ruled lawn between engraved tree clumps, with the sky ruled and a glory of rays behind.
Tall plates add a ribbon of thirteen stars and the day's date in Roman capitals on the pedestal
tablet. Easter egg: Parker's crossed drumsticks lie on the Mall in front of the Capitol (and stand
between the numerals on the tablet).
"""
import sys
import math
import random
import engraving_codex as C

_n, _d, pat = C._n, C._d, C.pat


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _ell(cx, cy, rx, ry, a0=0., a1=2 * math.pi, n=40):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def _vlines(x0, x1, y0, y1, pitch):
    out = []
    x = x0
    while x <= x1 + .01:
        out.append([(x, y0), (x, y1)])
        x += pitch
    return out


def _star(cx, cy, r):
    return [(cx + (r if i % 2 == 0 else r * .42) * math.sin(math.pi * i / 5),
             cy - (r if i % 2 == 0 else r * .42) * math.cos(math.pi * i / 5)) for i in range(10)]


def _drumsticks(cv, cx, cy, L, ang=35):
    """Two crossed drumsticks (tapered shafts, oval tips), drawn into cv."""
    for s in (-1, 1):
        a = math.radians(90 + s * ang)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        b = (cx - ux * L / 2, cy - uy * L / 2)
        t = (cx + ux * L / 2, cy + uy * L / 2)
        wb, wt = max(.9, L * .045), max(.5, L * .02)
        shaft = [(b[0] + vx * wb, b[1] + vy * wb), (t[0] + vx * wt, t[1] + vy * wt),
                 (t[0] - vx * wt, t[1] - vy * wt), (b[0] - vx * wb, b[1] - vy * wb)]
        cv.obj([shaft], .5)
        cv.hair([[(b[0] - vx * wb * .3, b[1] - vy * wb * .3), (t[0] - vx * wt * .3, t[1] - vy * wt * .3)]])
        tr = max(.9, L * .05)
        tip = _ell(t[0] + ux * tr * .8, t[1] + uy * tr * .8, tr, tr, n=12)
        cv.obj([tip], .5)


# ----------------------------------------------------------------------------------------------
# the vignette: the Capitol
# ----------------------------------------------------------------------------------------------

def capitol(x, y, w, h, clip_d, seed=0, egg=True):
    """Fill the field (bbox x,y,w,h; outline clip_d) entirely: sky, glory, Capitol, trees, lawn."""
    rng = random.Random(seed)
    cv = C.Canvas()
    small = w < 120
    gy = y + h * (.80 if not small else .84)              # foot of the building
    U = min(w * (.96 if small else .92), (gy - y - max(2., h * .04)) / .47)
    # the dome group is drawn larger than life (K) when the field is tall enough: it is the subject
    K = max(1., min(1.55, ((gy - y - max(2., h * .05)) / U - .11) / .346))
    V = U * K
    cx = x + w / 2
    # --- sky: horizontal ruling, denser at the zenith, lighter at the horizon
    sky = _rect(x - 2, y - 2, x + w + 2, gy + 1)
    cv.obj([sky], 0)
    ylim = y + (gy - y) * .45
    yy = y - 1
    while yy < gy:
        p = 2. if yy < ylim else 3.
        cv.hair([[(x - 2, yy), (x + w + 2, yy)]])
        yy += p
    # --- glory of rays behind the dome
    dome_cy = gy - U * .11 - V * .13
    R0 = V * .17
    nray = max(36, int(2 * math.pi * R0 / 2.2))
    Rmax = max(w, h)
    for i in range(nray):
        a = math.pi + math.pi * (i + .5) / nray * 1.0
        a = -math.pi * (i + .5) / nray
        r1 = Rmax if i % 2 else R0 + (Rmax - R0) * .45
        if i % 4 == 1:
            cv.line([(cx + R0 * math.cos(a), dome_cy + R0 * math.sin(a)),
                     (cx + r1 * math.cos(a), dome_cy + r1 * math.sin(a))])
        else:
            cv.hair([(cx + R0 * math.cos(a), dome_cy + R0 * math.sin(a)),
                     (cx + r1 * math.cos(a), dome_cy + r1 * math.sin(a))])
    # --- tree clumps flanking the building (behind it)
    if not small:
        for side in (-1, 1):
            for k in range(7):
                tx = cx + side * (U * (.34 + .03 * k) + rng.uniform(0, U * .02))
                tr = U * rng.uniform(.035, .055)
                ty = gy - U * .05 - tr * rng.uniform(.2, .9)
                blob = []
                for j in range(28):
                    a = 2 * math.pi * j / 28
                    rr = tr * (1 + .12 * math.sin(a * 5 + k) + .06 * math.sin(a * 9 + 2 * k))
                    blob.append((tx + rr * math.cos(a), ty + rr * .85 * math.sin(a)))
                cv.obj([blob], .5)
                cv.hair(C.hatch_poly(blob, 45 if side > 0 else -45, 2, k * .5))
                lower = [p for p in blob if p[1] > ty - tr * .1]
                if len(lower) > 2:
                    cv.hair(C.hatch_poly(lower + [(tx, ty)], -45 if side > 0 else 45, 2, .7))
    # --- wings
    hw = .5 * U
    wing_top = gy - U * .085
    cen_top = gy - U * .11
    pod = gy - U * .03                                      # podium / rusticated base top
    for side in (-1, 1):
        x0, x1 = sorted((cx + side * hw, cx + side * U * .16))
        wing = _rect(x0, wing_top, x1, gy)
        cv.obj([wing], 1.)
        # rusticated podium: coursing lines
        for k in range(1, 4):
            yk = pod + (gy - pod) * k / 4
            cv.hair([(x0, yk), (x1, yk)])
        cv.line([(x0, pod), (x1, pod)])
        # colonnade: column pairs with shadowed intercolumniation
        pitch = 3. if not small else 3.
        cols = _vlines(x0 + 1.5, x1 - 1.5, wing_top + U * .012, pod, pitch)
        for i, c in enumerate(cols):
            (cv.line if i % 2 == 0 else cv.hair)(c)
        cv.line([(x0, wing_top + U * .012), (x1, wing_top + U * .012)])
        cv.hair(C.hatch_poly(_rect(x0, wing_top, x1, wing_top + U * .012), 0, 1.5))
        # end pavilion
        e0, e1 = sorted((cx + side * hw, cx + side * (hw - U * .06)))
        cv.obj([_rect(e0, wing_top - U * .012, e1, gy)], 1.)
        cv.hair(C.hatch_poly(_rect(e0, wing_top - U * .012, e1, gy), 0, 2 if side < 0 else 3))
        if side < 0:
            cv.hair(C.hatch_poly(_rect(e0, wing_top - U * .012, e1, gy), 90, 3))
        ped = [(e0 - 1, wing_top - U * .012), (e1 + 1, wing_top - U * .012), ((e0 + e1) / 2, wing_top - U * .03)]
        cv.obj([ped], 1.)
        cv.hair(C.hatch_poly(ped, 0, 1.5))
    # central block
    ch_ = max(.17 * U, .155 * V + .015 * U)
    c0, c1 = cx - ch_, cx + ch_
    cb = _rect(c0, cen_top, c1, gy)
    cv.obj([cb], 1.)
    cv.hair(C.hatch_poly(_rect(c0, cen_top, c1, gy), 0, 3))
    cv.line([(c0, pod), (c1, pod)])
    cv.hair(C.hatch_poly(_rect(c0, cen_top, cx - U * .1, gy), 90, 2))
    cv.hair(C.hatch_poly(_rect(cx + U * .1, cen_top, c1, gy), 90, 3))
    # portico
    p0, p1 = cx - U * .1, cx + U * .1
    por_top = cen_top + U * .008
    cv.obj([_rect(p0, por_top, p1, gy)], 1.)
    cols = _vlines(p0 + 1.5, p1 - 1.5, por_top + U * .014, gy - U * .012, 3 if not small else 3)
    for i, c in enumerate(cols):
        cv.heavy(c) if i % 2 == 0 else cv.hair(c)
    cv.hair(C.hatch_poly(_rect(p0, por_top, p1, por_top + U * .014), 0, 1.5))
    # steps
    for k in range(4):
        sy = gy - U * .012 + k * U * .003
        cv.hair([(p0 - k * 2, sy), (p1 + k * 2, sy)])
    pedi = [(p0 - 2, por_top), (p1 + 2, por_top), (cx, por_top - U * .035)]
    cv.obj([pedi], 1.)
    cv.hair(C.hatch_poly(pedi, 0, 1.5))
    tymp = [(p0 + 4, por_top - 1), (p1 - 4, por_top - 1), (cx, por_top - U * .035 + 3)]
    cv.obj([tymp], .5)
    cv.hair(C.hatch_poly(tymp, 90, 3))
    # --- drum (peristyle), attic, dome, lantern
    d_base = cen_top - U * .004
    d0, d1 = cx - V * .155, cx + V * .155
    drum_top = d_base - V * .075
    cv.obj([_rect(d0, drum_top - V * .008, d1, d_base)], 1.)
    cv.hair(C.hatch_poly(_rect(d0, drum_top - V * .008, d1, drum_top), 0, 1.5))
    cols = _vlines(d0 + 1.5, d1 - 1.5, drum_top, d_base - V * .01, 3)
    for i, c in enumerate(cols):
        f = (c[0][0] - cx) / (d1 - d0) * 2               # -1..1 across the drum
        (cv.line if (i % 2 == 0 or f < -.55) else cv.hair)(c)
    cv.hair(C.hatch_poly(_rect(d0, d_base - V * .01, d1, d_base), 0, 1.5))
    # left-side shadow on the drum
    cv.hair(C.hatch_poly(_rect(d0, drum_top, cx - V * .09, d_base - V * .01), 0, 2))
    a0, a1 = cx - V * .125, cx + V * .125
    at_top = drum_top - V * .008 - V * .04
    cv.obj([_rect(a0, at_top, a1, drum_top - V * .008)], 1.)
    cv.hair(C.hatch_poly(_rect(a0, at_top, a1, drum_top - V * .008), 0, 3))
    cv.hair(C.hatch_poly(_rect(a0, at_top, cx - V * .06, drum_top - V * .008), 90, 3, 1.5))
    for wx in _vlines(a0 + 4, a1 - 4, 0, 0, max(6., V * .025)):
        xw = wx[0][0]
        cv.line([(xw, at_top + V * .01), (xw, drum_top - V * .016)])
    # dome
    rx, ry = V * .118, V * .14
    dcy = at_top
    dome = _ell(cx, dcy, rx, ry, math.pi, 2 * math.pi, 48)
    cv.obj([dome + [(cx + rx, dcy), (cx - rx, dcy)]], 1.)
    # shading: contour hatch denser on the left (light from the right)
    for k in range(1, 9):
        t = k / 9.
        y_k = dcy - ry * t
        half = rx * math.sqrt(max(0., 1 - t * t))
        cv.hair([(cx - half, y_k), (cx + half * .2, y_k)])
    for k in range(-7, 8):
        u = k / 8.                              # rib position -1..1
        rib = [(cx + rx * u * math.sqrt(max(0., 1 - (j / 20.) ** 2)), dcy - ry * j / 20.) for j in range(21)]
        (cv.line if k % 2 == 0 else cv.hair)(rib)
    # shadow band on the left of the dome: extra diagonal hatch
    lshade = _ell(cx, dcy, rx, ry, math.pi, 1.5 * math.pi, 20) + [(cx - rx * .45, dcy - ry * .55), (cx - rx * .55, dcy)]
    cv.hair(C.hatch_poly(lshade, 60, 2))
    core = _ell(cx, dcy, rx, ry, math.pi, 1.35 * math.pi, 16) + [(cx - rx * .7, dcy - ry * .45), (cx - rx * .8, dcy)]
    cv.hair(C.hatch_poly(core, -30, 2, 1))
    cv.heavy(_ell(cx, dcy, rx - .8, ry - .8, math.pi, 1.4 * math.pi, 16))
    # windows ring on dome base
    cv.line([(cx - rx * .98, dcy - ry * .18), (cx + rx * .98, dcy - ry * .18)])
    # lantern
    lw, lh = V * .022, V * .045
    ltop = dcy - ry - lh + 1
    lan = _rect(cx - lw, ltop, cx + lw, dcy - ry + 1.5)
    cv.obj([lan], 1.)
    cv.hair(_vlines(cx - lw + 1.2, cx + lw - 1.2, ltop + 1, dcy - ry, 1.5 if lw > 3 else 2))
    cap = _ell(cx, ltop, lw * 1.1, lw * .9, math.pi, 2 * math.pi, 16)
    cv.obj([cap], 1.)
    cv.hair(C.hatch_poly(cap, 0, 1.5))
    # Statue of Freedom
    sh = max(3., V * .025)
    st = [(cx - sh * .18, ltop - lw * .8), (cx + sh * .18, ltop - lw * .8), (cx + sh * .1, ltop - lw * .8 - sh),
          (cx - sh * .1, ltop - lw * .8 - sh)]
    cv.obj([st], 1.)
    cv.heavy([(cx, ltop - lw * .8), (cx, ltop - lw * .8 - sh * 1.15)])
    # --- lawn and the Mall
    lawn = _rect(x - 2, gy, x + w + 2, y + h + 2)
    cv.obj([lawn], 0)
    cv.line([(x - 2, gy), (x + w + 2, gy)])
    yy = gy + 2
    while yy < y + h + 2:
        cv.hair([(x - 2, yy), (x + w + 2, yy)])
        yy += 2. if yy < gy + (h + y - gy) * .5 else 1.5
    # the Mall walk: a light trapezoid of perspective lines into the portico
    mall = [(p0 + 2, gy), (p1 - 2, gy), (cx + w * .22, y + h + 2), (cx - w * .22, y + h + 2)]
    cv.obj([mall], .5)
    for k in range(-4, 5):
        cv.hair([(cx + (p1 - p0 - 4) / 2 * k / 4.5, gy), (cx + w * .22 * k / 4.5, y + h + 2)])
    cv.hair(C.hatch_poly(mall, 0, 3))
    if egg and not small:
        L = max(8., min(18., (y + h - gy) * .8))
        _drumsticks(cv, cx + w * .3, gy + (y + h - gy) * .5, L, 32)
    # windows of the wings: tiny black openings (frontmost)
    blk = []
    if not small:
        for side in (-1, 1):
            x0, x1 = sorted((cx + side * (hw - U * .07), cx + side * U * .18))
            xw = x0 + 1
            while xw < x1 - 2:
                blk.append(f"M{_n(xw)},{_n(pod + 1.5)}h1.2v{_n(max(1.5, (gy - pod) * .45))}h-1.2z")
                xw += 4.5
    cid = C._uid("cap", x, y, w, h, seed)
    body = cv.svg() + (f'<path d="{"".join(blk)}" fill="#000"/>' if blk else "")
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{body}</g>')


# ----------------------------------------------------------------------------------------------
# lettering: the date in Roman capitals, as engraved strokes
# ----------------------------------------------------------------------------------------------

def _roman(n):
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
                 (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s
            n -= v
    return out


_GW = {"I": .34, "V": .8, "X": .8, "M": 1.05, "L": .62, "C": .78, "D": .82}


def _glyph(ch, x, y, h):
    """Strokes (thick, thin) for a Roman capital at x (left), baseline y, cap height h."""
    w = _GW[ch] * h
    thick, thin, serif = [], [], []
    t, b = y - h, y
    if ch == "I":
        thick.append([(x + w / 2, t), (x + w / 2, b)])
        serif += [[(x, t), (x + w, t)], [(x, b), (x + w, b)]]
    elif ch == "V":
        thick.append([(x + w * .12, t), (x + w / 2, b)])
        thin.append([(x + w * .88, t), (x + w / 2, b)])
        serif += [[(x, t), (x + w * .28, t)], [(x + w * .74, t), (x + w, t)]]
    elif ch == "X":
        thick.append([(x + w * .12, t), (x + w * .88, b)])
        thin.append([(x + w * .88, t), (x + w * .12, b)])
        serif += [[(x, t), (x + w * .3, t)], [(x + w * .7, t), (x + w, t)],
                  [(x, b), (x + w * .3, b)], [(x + w * .7, b), (x + w, b)]]
    elif ch == "M":
        thin.append([(x + w * .1, t), (x + w * .1, b)])
        thick.append([(x + w * .1, t), (x + w / 2, b)])
        thin.append([(x + w / 2, b), (x + w * .9, t)])
        thick.append([(x + w * .9, t), (x + w * .9, b)])
        serif += [[(x, b), (x + w * .22, b)], [(x + w * .76, b), (x + w, b)]]
    elif ch == "L":
        thick.append([(x + w * .2, t), (x + w * .2, b), (x + w, b)])
        serif += [[(x, t), (x + w * .42, t)]]
    elif ch == "C":
        thick.append(_ell(x + w * .55, y - h / 2, w * .45, h / 2, math.pi * .3, math.pi * 1.7, 16))
    elif ch == "D":
        thick.append([(x + w * .15, t), (x + w * .15, b)])
        thin.append([(x + w * .15, t)] + _ell(x + w * .4, y - h / 2, w * .55, h / 2, -math.pi / 2, math.pi / 2, 14)
                    + [(x + w * .15, b)])
    return thick, thin, serif, w


def date_tablet(tx, ty, tw, th, date):
    """Fill the pedestal tablet: a mid-ruled sunk field with the date in engraved Roman capitals,
    the groups divided by tiny crossed drumsticks."""
    try:
        yy, mm, dd = (int(v) for v in date.split("-"))
    except Exception:
        yy, mm, dd = 2026, 1, 1
    groups = [_roman(dd), _roman(mm), _roman(yy)]
    ch = min(th * .62, 14.)
    gap = ch * 1.5
    trk = ch * .16
    total = sum(sum(_GW[c] * ch + trk for c in g) - trk for g in groups) + gap * 2
    x = tx + (tw - total) / 2
    base = ty + th / 2 + ch / 2
    thick, thin = [], []
    cv = C.Canvas()
    for gi, g in enumerate(groups):
        for c in g:
            a, b, s, w = _glyph(c, x, base, ch)
            thick += a
            thin += b + s
            x += w + trk
        x -= trk
        if gi < 2:
            _drumsticks(cv, x + gap / 2, base - ch / 2, ch * 1.05, 30)
            x += gap
    def dd_(pls):
        return "".join(_d(p, tol=0) for p in pls)
    halo = dd_(thick + thin)
    return (f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-(tw - 3))}z" fill="{pat("L")}"/>'
            f'<path d="{halo}" stroke="#fff" stroke-width="4" stroke-linecap="square"/>'
            f'<path d="{dd_(thick)}" stroke="#000" stroke-width="1.5" stroke-linecap="butt"/>'
            f'<path d="{dd_(thin)}" stroke="#000" stroke-width="1" stroke-linecap="butt"/>' + cv.svg())


def ribbon_stars(centre, h):
    """Thirteen black stars along the ribbon face."""
    n = len(centre) - 1
    stars = []
    for k in range(13):
        t = (k + .5) / 13
        i = min(n - 1, int(t * n))
        f = t * n - i
        px = centre[i][0] + (centre[i + 1][0] - centre[i][0]) * f
        py = centre[i][1] + (centre[i + 1][1] - centre[i][1]) * f
        stars.append(_d(_star(px, py + .3, h * .3), True, 0))
    return f'<path d="{"".join(stars)}" fill="#000"/>'


# ----------------------------------------------------------------------------------------------
# layouts (house layouts, adapted so no ground is left white)
# ----------------------------------------------------------------------------------------------

def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.dark_ground((0, 0, w, h), "M"))
    o.append(f'<path d="M0,0h{_n(w)}v{_n(top)}h{_n(-w)}z" fill="#fff"/>')
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 4, ry - 4
    o.append(capitol(cx - fx, cy - fy, 2 * fx, 2 * fy, _d(_ell(cx, cy, fx, fy, n=64), True), seed, egg=False))
    o.append(f'<path d="{_d(_ell(cx, cy, fx, fy, n=64), True)}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0 - 1, w, gh + 2), "G"))
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .07), rmax=r * .8,
                   max_n=int(10 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    bb = _bbox(cx, cy, cw, gh + 4)
    o.append(capitol(*bb, field, seed))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _bbox(cx, cy, w, h):
    """The cartouche field's bounding box (mirrors C.cartouche's geometry)."""
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return cx - a, cy - b, 2 * a, 2 * b


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    em = min(12., 6 + h * .02)
    o.append(C.dark_ground((0, 0, w, h), "M"))          # no bare paper anywhere
    o.append(f'<path d="M0,0h{_n(w)}v{_n(em + 1)}h{_n(-w)}z" fill="#fff"/>')
    o.append(C.egg_and_dart(0, 0, w, em))
    top_free = em + 6
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .62
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = C.Canvas(), C.Canvas()
    r1 = min(pw * .17, ph * .25)
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .04), rmax=r1 * .9,
                   max_n=int(9 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free + em, pw, ph + top_free - em, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    o.append(capitol(*_bbox(cx, cy, cw, ch), field, seed))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 56), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.35, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(ribbon_stars(centre, bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(date_tablet(tx, ty, tw, th, (ctx or {}).get("date", "")))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
