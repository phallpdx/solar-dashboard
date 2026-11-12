"""Roads and mountains: Mt. Hood rising over a winding road, engraved inside the house cartouche.

The road S-curves up out of the foreground toward the mountain between ruled fields and
fir-crowned foothills; the Grasshopper Fire's smoke curls off a ridge to the east; the moon
hangs in the ruled sky at today's phase. Easter egg: the roadside route shield reads "P".
"""
import sys
import math
import datetime
import engraving_codex as C

_K_CART = 2 ** (-1 / 2.6)


# ----------------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------------

def _catmull(pts, n=12):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(pts[-1])
    return out


def _resample(pl, n):
    L = [0.]
    for a, b in zip(pl, pl[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = L[-1] or 1.
    out, j = [], 0
    for i in range(n + 1):
        s = tot * i / n
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        seg = (L[j + 1] - L[j]) or 1.
        t = (s - L[j]) / seg
        a, b = pl[j], pl[j + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _moon_phase(date):
    try:
        d = datetime.date.fromisoformat(date[:10])
    except Exception:
        d = datetime.date(2026, 11, 11)
    days = (d - datetime.date(2000, 1, 6)).days + .5 - .76
    return (days / 29.530589) % 1.


def _hash(s):
    h = 2166136261
    for ch in s:
        h = ((h ^ ord(ch)) * 16777619) & 0xffffffff
    return h


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def _scene(X0, Y0, W, H, ctx):
    """Draw the roads-and-mountain vignette over the box (X0, Y0, W, H); returns SVG fragments
    (unclipped; the caller clips them to the cartouche field)."""
    def P(u, v):
        return (X0 + u * W, Y0 + v * H)

    def poly(uv):
        return [P(u, v) for u, v in uv]

    seed = _hash((ctx or {}).get("date", ""))
    cv = C.Canvas()
    small = H < 70

    # sky: ruled lines, closer at the zenith, opening toward the horizon glow
    sky = poly([(-.05, -.05), (1.05, -.05), (1.05, .8), (-.05, .8)])
    cv.obj([sky], 0)
    yy = Y0 - 2
    while yy < Y0 + H * .8:
        v = (yy - Y0) / H
        cv.hair([(X0 - 3, yy), (X0 + W + 3, yy)])
        yy += 1.5 if v < .22 else (2. if v < .42 else 3.)

    # moon at today's phase
    ph = _moon_phase((ctx or {}).get("date", ""))
    mr = max(4.5, min(W, H) * .075)
    mx, my = P(.17, .2)
    disc = C._ell_pts(mx, my, mr, mr, 40)
    cv.obj([disc], 0)
    extra = [f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="{mr:.1f}" stroke="#000" stroke-width="1" fill="none"/>']
    # terminator: lit fraction from phase; shadow polygon = dark limb + terminator ellipse
    k = math.cos(ph * 2 * math.pi)            # 1 new, -1 full
    waxing = ph < .5
    side = -1 if waxing else 1                # shadow on the left when waxing
    limb = [(mx + side * mr * abs(math.sin(t)), my - mr * math.cos(t)) for t in [i * math.pi / 20 for i in range(21)]]
    term = [(mx + side * mr * k * math.sin(t), my - mr * math.cos(t)) for t in [math.pi - i * math.pi / 20 for i in range(21)]]
    shadow = limb + term
    if abs(C._area(shadow)) > 1:
        cv.hair(C.hatch_poly(shadow, 0, 1.5, .4))
        cv.hair(C.hatch_poly(shadow, 60, 2, .3))
    for i in range(5):  # maria
        a = (seed >> i) % 360
        rr = mr * (.25 + .12 * (i % 3))
        cx, cy = mx + mr * .45 * math.cos(math.radians(a + i * 70)), my + mr * .45 * math.sin(math.radians(a + i * 70))
        cv.hair([C._ell_pts(cx, cy, rr * .5, rr * .35, 8) + [C._ell_pts(cx, cy, rr * .5, rr * .35, 8)[0]]])

    # wildfire smoke billowing off an eastern ridge and leaning west on the wind (Grasshopper Fire)
    if not small:
        sx, sy = P(.95, .52)
        m = 26
        cen, wid = [], []
        for i in range(m + 1):
            t = i / m
            cen.append((sx - W * .16 * t ** 1.6, sy - H * .5 * t + H * .04 * t * t))
            wid.append(H * (.012 + .07 * t ** .8))
        nrm = []
        for i in range(m + 1):
            a, b = cen[max(0, i - 1)], cen[min(m, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            dl = math.hypot(dx, dy) or 1.
            nrm.append((-dy / dl, dx / dl))
        def edge(sgn, ph0):
            out = []
            for i in range(m + 1):
                t = i / m
                bump = 1 + .28 * abs(math.sin(t * 9 + ph0))
                r = wid[i] * bump
                out.append((cen[i][0] + nrm[i][0] * r * sgn, cen[i][1] + nrm[i][1] * r * sgn))
            return out
        le, re_ = edge(1, .4), edge(-1, 1.9)
        cap = [(cen[m][0] + wid[m] * 1.2 * math.cos(a), cen[m][1] + wid[m] * 1.05 * math.sin(a))
               for a in [math.atan2(-nrm[m][1], -nrm[m][0]) - k * math.pi / 10 for k in range(11)]]
        plume = le + cap[::-1] + re_[::-1]
        cv.obj([plume], .5)
        # billow lines following the plume, crowded on its shadowed (east) side
        for j in range(1, 40):
            off = j * 1.6
            run = []
            for i in range(m + 1):
                lim = wid[i] * 1.25
                if off > lim * (1.45 if j % 3 else 1.7):
                    if len(run) > 1:
                        cv.hair(run)
                    run = []
                    continue
                d = -wid[i] * 1.2 + off
                run.append((cen[i][0] + nrm[i][0] * d, cen[i][1] + nrm[i][1] * d))
            if len(run) > 1:
                cv.hair(run)
        # curls inside the billows
        for i in range(6, m, 5):
            r = wid[i] * .45
            cx, cy = cen[i][0] - nrm[i][0] * wid[i] * .2, cen[i][1] - nrm[i][1] * wid[i] * .2
            cv.hair([(cx + r * math.cos(a) * (1 - a / 12), cy + r * .8 * math.sin(a) * (1 - a / 12)) for a in [k * .35 for k in range(16)]])
        for j in range(5):
            fx = sx - 4 + j * 2
            cv.line([(fx, sy + 2), (fx + .8, sy - 1.5 - (j % 2) * 2)])

    # Mt. Hood
    prof = [(-.05, .66), (.12, .6), (.22, .53), (.31, .45), (.37, .39), (.41, .345), (.44, .33),
            (.47, .27), (.505, .2), (.535, .15), (.556, .115), (.572, .1), (.585, .108), (.61, .14),
            (.645, .2), (.69, .265), (.735, .32), (.8, .385), (.87, .44), (.95, .49), (1.05, .54)]
    mtn = poly(prof + [(1.05, .82), (-.05, .82)])
    cv.obj([mtn], 1.)
    # ridge dividing the shadowed west face from the lit east face
    div = [(.572, .1), (.565, .16), (.56, .22), (.545, .3), (.53, .38), (.5, .47), (.47, .58), (.44, .7)]
    lefts = [p for p in prof if p[0] < .572]
    shadow_face = poly(lefts + [(.572, .1)] + div[1:] + [(-.05, .82)])
    cv.hair(C.hatch_poly(shadow_face, -55, 1.5, .2))
    lower_shadow = poly([(-.05, .5), (.5, .5)] + [(.5, .47), (.47, .58), (.44, .7)] + [(-.05, .82)])
    cv.hair(C.hatch_poly(lower_shadow, 20, 2, .6))
    # the dark undercut along the ridge (shadow side) - a heavy line
    cv.heavy(_catmull([P(*q) for q in div[:6]], 6))
    # snowline on the lit face
    sl = []
    for i in range(15):
        u = .53 + i * .04
        v = .42 + .08 * i / 14 + .025 * math.sin(i * 2.3 + seed % 7)
        sl.append((u, v))
    lit_lower = poly([(.5, .47)] + sl + [(1.05, .82), (.44, .82), (.47, .58)])
    cv.hair(C.hatch_poly(lit_lower, -20, 2, .5))
    cv.hair(C.hatch_poly(lit_lower, 30, 3, .5))
    # lit snow face: sparse lines parallel to the east ridge
    lit_snow = poly([(.572, .1), (.585, .108), (.61, .14), (.645, .2), (.69, .265), (.735, .32), (.8, .385),
                     (.87, .44), (.95, .49), (1.05, .54), (1.05, .62)] + sl[::-1] + [(.53, .38), (.545, .3), (.56, .22), (.565, .16)])
    cv.hair(C.hatch_poly(lit_snow, 34, 3, .9))
    # couloirs and glacier tongues running down the lit face
    for i in range(6):
        u0, v0 = .575 + i * .025, .13 + i * .045
        pts = []
        for j in range(9):
            t = j / 8
            pts.append(P(u0 + .03 * t + .006 * math.sin(t * 6 + i), v0 + (.24 - i * .015) * t))
        cv.line(pts[: 5 + (i % 3)])
        cv.hair(pts[4:])
    # rock bands (Illumination Rock and Steel Cliff): short heavy ticks
    for (u, v, L) in ((.46, .29, .03), (.505, .23, .02), (.6, .175, .018), (.66, .26, .022), (.53, .32, .02)):
        a, b = P(u, v), P(u + L * .5, v + L * 1.3)
        cv.heavy([a, b])

    # back foothills with fir tree crowns
    def ridge(v0, amp, freq, ph0, u0=-.05, u1=1.05):
        pts = []
        n = 40
        for i in range(n + 1):
            u = u0 + (u1 - u0) * i / n
            pts.append((u, v0 + amp * (math.sin(u * freq + ph0) * .6 + math.sin(u * freq * 2.7 + ph0 * 2) * .4)))
        return pts

    back = ridge(.62, .025, 9, seed % 5)
    backp = poly(back + [(1.05, .85), (-.05, .85)])
    cv.obj([backp], 1.)
    cv.hair(C.hatch_poly(backp, 0, 2, .7))
    cv.hair(C.hatch_poly(backp, -40, 3, .3))

    def firs(edge_uv, size, step_px, dark=1.):
        line = _resample([P(u, v) for u, v in edge_uv], max(4, int(W / step_px)))
        out = []
        for i, (x, y) in enumerate(line):
            s = size * (.8 + .4 * (((seed >> (i % 16)) & 3) / 3))
            out.append(_tree(x, y + s * .25, s))
        return out

    for tr in firs(back, max(4., H * .07), 3.6):
        cv.obj([tr], .5)
        cv.hair(C.hatch_poly(tr, 0, 1.5, .3))

    # front hills: darker, cross-hatched, crowned by larger firs
    front = ridge(.7, .03, 6.5, seed % 3 + 1)
    frontp = poly(front + [(1.05, .9), (-.05, .9)])
    cv.obj([frontp], 1.)
    cv.hair(C.hatch_poly(frontp, 0, 1.5, .2))
    cv.hair(C.hatch_poly(frontp, 50, 2, .5))
    for tr in firs([q for q in front if q[0] < .4], max(5., H * .11), 5.5) + firs([q for q in front if q[0] > .58], max(5., H * .11), 5.5):
        cv.obj([tr], .5)
        cv.line(C.hatch_poly(tr, 0, 1., .3))

    # foreground fields, ruled in perspective
    ground = poly([(-.05, .74), (1.05, .74), (1.05, 1.05), (-.05, 1.05)])
    cv.obj([ground], 1.)
    yy = Y0 + H * .755
    step = 1.5
    while yy < Y0 + H * 1.05:
        cv.hair([(X0 - 3, yy), (X0 + W + 3, yy)])
        yy += step
        step = min(4., step * 1.12)
    # field boundaries: hedgerows curving away in perspective, tufts of meadow grass
    for (ua, ub, va) in ((.05, -.3, .76), (.3, .1, .76), (.75, 1.2, .77)):
        hed = [P(ua + (ub - ua) * t * t, va + (1.08 - va) * t) for t in [k / 10 for k in range(11)]]
        cv.line(hed)
    for (ua, ub, va) in ((.05, -.3, .76), (.3, .1, .76), (.75, 1.2, .77)):
        for k in range(1, 6):
            t = k / 6
            x, y = P(ua + (ub - ua) * t * t, va + (1.08 - va) * t)
            r = .8 + 2.2 * t
            bush = C._ell_pts(x, y - r * .6, r, r * .75, 12)
            cv.obj([bush], .5)
            cv.hair(C.hatch_poly(bush, 0, 1.5, .2))
    # the road: an S-curve rising to the foot of the mountain
    ctrl = [(.66, 1.08), (.6, .96), (.42, .88), (.47, .8), (.57, .75), (.53, .69), (.46, .655), (.47, .62)]
    cl = _resample(_catmull([P(*q) for q in ctrl], 10), 90)
    n = len(cl)
    def hw(i):
        t = i / (n - 1)
        return W * (.11 * (1 - t) ** 1.5 + .004)
    L, R, N = [], [], []
    for i in range(n):
        a = cl[max(0, i - 1)]
        b = cl[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        dl = math.hypot(dx, dy) or 1.
        nx, ny = -dy / dl, dx / dl
        N.append((nx, ny))
        L.append((cl[i][0] + nx * hw(i), cl[i][1] + ny * hw(i)))
        R.append((cl[i][0] - nx * hw(i), cl[i][1] - ny * hw(i)))
    road = L + R[::-1]
    # shoulders: a dark ditch line just outside each edge
    sh = [(cl[i][0] + N[i][0] * hw(i) * 1.25, cl[i][1] + N[i][1] * hw(i) * 1.25) for i in range(n)]
    shr = [(cl[i][0] - N[i][0] * hw(i) * 1.25, cl[i][1] - N[i][1] * hw(i) * 1.25) for i in range(n)]
    shoulder = sh + shr[::-1]
    cv.obj([shoulder], 0)
    cv.hair(C.hatch_poly(shoulder, 90, 1.5, .4))
    cv.obj([road], 1.)
    # asphalt: lines running with the road, dropped where they would crowd
    for s in (-.82, -.6, -.36, .36, .6, .82):
        run = []
        for i in range(n):
            if hw(i) * .22 < 1.4:
                break
            run.append((cl[i][0] + N[i][0] * hw(i) * s, cl[i][1] + N[i][1] * hw(i) * s))
        if len(run) > 1:
            cv.hair(run)
    # centre dashes, shrinking with distance
    i = 0
    while i < n - 2:
        dash = max(1, int(6 * (1 - i / n)))
        seg = cl[i:i + dash + 1]
        if hw(i) > 2.2:
            cv.heavy(seg) if hw(i) > 6 else cv.line(seg)
        i += dash * 2
    # guard posts along the outside of the near curve
    for i in range(3, n // 2, 6):
        x, y = sh[i] if i < n // 4 else shr[i]
        s = hw(i) * .25 + 1
        cv.obj([[(x - .6, y - s), (x + .6, y - s), (x + .6, y), (x - .6, y)]], .5)

    # Easter egg: a roadside route shield carrying a "P"
    if not small:
        bx, by = P(.86, .84)
        s = max(6., H * .1)
        cv.line([(bx, by), (bx, by + s * 1.1)])
        shield = [(bx - s * .5, by - s * 1.05), (bx - s * .2, by - s * .95), (bx, by - s * 1.1), (bx + s * .2, by - s * .95),
                  (bx + s * .5, by - s * 1.05), (bx + s * .48, by - s * .45)]
        shield += [(bx + s * .48 * math.cos(t), by - s * .45 + s * .5 * math.sin(t)) for t in [i * math.pi / 8 for i in range(1, 8)]]
        shield += [(bx - s * .48, by - s * .45)]
        cv.obj([shield], 1.)
        # the P: stem and bowl
        cv.heavy([(bx - s * .14, by - s * .2), (bx - s * .14, by - s * .82)])
        bowl = [(bx - s * .14, by - s * .82)] + [(bx - s * .02 + s * .2 * math.sin(t), by - s * .63 - s * .19 * math.cos(t))
                                                for t in [i * math.pi / 8 for i in range(9)]] + [(bx - s * .14, by - s * .44)]
        cv.line(bowl)
    return cv.svg() + ''.join(extra)


def _tree(x, y, s):
    """A fir silhouette: a tiered spire with drooping boughs, base centred at (x, y)."""
    pts = [(x, y - s * 1.5)]
    tiers = 3
    for k in range(tiers):
        t1 = (k + 1) / tiers
        wd = s * (.18 + .32 * t1)
        yy = y - s * 1.5 + s * 1.45 * t1
        pts.append((x + wd, yy))
        if k < tiers - 1:
            pts.append((x + wd * .45, yy - s * .08))
    pts.append((x + s * .08, y))
    pts.append((x - s * .08, y))
    right = pts[1:-2]
    left = [(2 * x - px, py) for px, py in right[::-1]]
    return [pts[0]] + right + [pts[-2], pts[-1]] + left


# ----------------------------------------------------------------------------------------------
# plate
# ----------------------------------------------------------------------------------------------

def plate(w, h, ctx):
    ctx = ctx or {}
    seed = _hash(ctx.get("date", "") + "roads") % 100000
    extra = []

    def fill(ix, iy, iw, ih):
        cx, cy = ix + iw / 2, iy + ih / 2
        if h < 110:
            rx = iw / 2 / .7071 + 5
            ry = ih / 2 / .7071 + 5
            field = C._ell_pts(cx, cy, rx - 2.5, ry - 2.5, 64)
        else:
            a = iw / 2 / _K_CART + 6
            b = ih / 2 / _K_CART + 6
            field = C._superellipse(cx, cy, a - 5, b - 5)
        xs = [p[0] for p in field]
        ys = [p[1] for p in field]
        X0, Y0, X1, Y1 = min(xs), min(ys), max(xs), max(ys)
        cid = C._uid("roads", w, h, seed)
        fd = C._d(field, True, 0)
        body = _scene(X0, Y0, X1 - X0, Y1 - Y0, ctx)
        return (f'<clipPath id="{cid}"><path d="{fd}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
                f'<path d="{fd}" fill="none" stroke="#000" stroke-width="1"/>')

    doc = C.frame_plate(w, h, seed, fill)
    if h > 260:
        top_free = min(h * .055, 26.)
        under = C.dark_ground((0, 0, w, top_free + 2), "L")
        doc = doc.replace("</defs>", "</defs>" + under, 1)
        doc = doc.replace("</svg>", _tall_overlays(w, h) + "</svg>")
    return doc


def _tall_overlays(w, h):
    """Engrave the two blanks the house tall frame leaves: the ribbon face and the pedestal tablet."""
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    py0 = top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    o = []
    # ribbon face: ruled shading following its arch, with a tiny route of dashes along the middle
    bw, bh = cw * 1.4, min(16, ph * .05)
    face_w = bw * .7
    by = cy + ch * .47
    n = 60
    cen = [(cx - face_w / 2 + face_w * i / n, by - .04 * bw * math.sin(math.pi * i / n)) for i in range(n + 1)]
    lines = []
    for off in (-.42, -.26, .26, .42, .56):
        lines.append(C._d([(x, y + off * bh) for x, y in cen[1:-1]], tol=.2))
    dash = []
    for i in range(3, n - 3, 3):
        dash.append(C._d([cen[i], cen[i + 1]], tol=0))
    o.append(f'<path d="{"".join(lines)}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="{"".join(dash)}" stroke="#000" stroke-width="1.5" fill="none"/>')
    # pedestal tablet: the Cascade skyline from home, St. Helens, Adams, Hood, Jefferson
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    kb = max(5, min(10, ped_h * .11))
    slab = ped_h * .42
    top = slab * .22
    fy = py + kb + top
    fh = slab - top
    th, tw = fh * .6, w * .56
    tx, ty = (w - tw) / 2, fy + (fh - th) / 2
    x0, y0, x1, y1 = tx + 2.5, ty + 2.5, tx + tw - 1, ty + th - 1
    cv = C.Canvas()
    box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    cv.obj([box], 0)
    cv.hair(C.hatch_poly(box, 0, 2, .5))
    TW, TH = x1 - x0, y1 - y0
    peaks = [(.16, .3, .07, "flat"), (.4, .14, .09, "dome"), (.62, .02, .075, "sharp"), (.84, .24, .06, "sharp")]
    base = y1 - TH * .18
    for u, v, half, kind in peaks:
        px, pk = x0 + u * TW, y0 + v * TH
        hw = half * TW * .5
        if kind == "flat":
            prof = [(px - hw, base), (px - hw * .25, pk + TH * .06), (px + hw * .12, pk), (px + hw * .3, pk + TH * .02), (px + hw, base)]
        elif kind == "dome":
            prof = [(px - hw, base)] + [(px + hw * .5 * math.cos(t), pk + (base - pk) * .45 * (1 - math.sin(t)))
                                        for t in [math.pi * k / 10 for k in range(10, -1, -1)]] + [(px + hw, base)]
        else:
            prof = [(px - hw, base), (px - hw * .3, pk + (base - pk) * .45), (px, pk), (px + hw * .35, pk + (base - pk) * .4), (px + hw, base)]
        cv.obj([prof], 1.)
        left = [q for q in prof if q[0] <= px] + [(px, base)]
        cv.hair(C.hatch_poly(left, -60, 1.5, .3))
    hills = [(x0, base - 1)] + [(x0 + TW * k / 30, base - 1 - TH * .06 * math.sin(k * 1.3)) for k in range(31)] + [(x1, y1), (x0, y1)]
    cv.obj([hills], 1.)
    cv.line(C.hatch_poly(hills, 0, 1.0, .4))
    o.append(cv.svg())
    return "".join(o)
