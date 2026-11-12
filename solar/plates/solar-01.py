"""solar-01 "Solar right now": the sun riding its best-hours arc over Parker's ground-mounted
panel array on Sauvie Island, the Columbia and Mt. Hood behind, set in the house Codex frame.
Easter egg: Parker's dog asleep in the sun on the grass by the front row of panels."""
import sys
import math
import random
import re
import engraving_codex as C

PI = math.pi


# ------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------

def _clip_half(poly, k, v, keep_less):
    """Sutherland-Hodgman against the axis line coord[k] = v."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ia = (a[k] <= v) if keep_less else (a[k] >= v)
        ib = (b[k] <= v) if keep_less else (b[k] >= v)
        if ia:
            out.append(a)
        if ia != ib:
            t = (v - a[k]) / (b[k] - a[k])
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _band(poly, y0, y1):
    p = _clip_half(poly, 1, y0, False)
    return _clip_half(p, 1, y1, True) if len(p) > 2 else []


def _quad(p0, p1, p2, p3, u, v):
    """Bilinear point in quad p0(top-left) p1(top-right) p2(bottom-right) p3(bottom-left)."""
    tx, ty = p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u
    bx, by = p3[0] + (p2[0] - p3[0]) * u, p3[1] + (p2[1] - p3[1]) * u
    return (tx + (bx - tx) * v, ty + (by - ty) * v)


def _circ(cx, cy, r, n=40, a0=0., a1=2 * PI):
    return C._ell_pts(cx, cy, r, r, n, a0, a1)


def _best_window(ctx):
    s = (ctx or {}).get("sample", "") or ""
    m = re.search(r"Best\s+(\d{1,2})\s*(am|pm)\s*[–\-]\s*(\d{1,2})\s*(am|pm)", s)
    if not m:
        return 10., 13.

    def hr(n, ap):
        n = int(n) % 12
        return n + (12 if ap == "pm" else 0)
    a, b = hr(m.group(1), m.group(2)), hr(m.group(3), m.group(4))
    return (float(a), float(b)) if b > a else (10., 13.)


# ------------------------------------------------------------------------------------------
# the vignette: sun over the panels
# ------------------------------------------------------------------------------------------

def _scene(cv, field, X0, Y0, W, H, ctx, seed, detail=2):
    """Fill the field polygon (bbox X0,Y0,W,H) completely: no white left but highlights."""
    rng = random.Random(seed)
    best0, best1 = _best_window(ctx)
    yH = Y0 + H * (.6 if detail else .62)          # horizon
    river = H * (.06 if detail else .0)
    cxm = X0 + W / 2

    # --- sky: ruled, darkest at the top, hazy at the horizon --------------------------------
    cv.obj([field], 0)
    for y0, y1, p in ((Y0 - 2, Y0 + H * .2, 1.5), (Y0 + H * .2, Y0 + H * .46, 2.), (Y0 + H * .46, yH + 1, 3.)):
        b = _band(field, y0, y1)
        if len(b) > 2:
            cv.hair(C.hatch_poly(b, 0, p, phase=.25))
    if detail:
        b = _band(field, Y0 - 2, Y0 + H * .12)
        if len(b) > 2:
            cv.hair(C.hatch_poly(b, 70, 3))

    # --- the sun's path (6 am .. 6 pm) with hour ticks; best window carved heavy ---------
    arx, ary = W * .44, (yH - Y0) * .7

    def arc_pt(hr, k=1.):
        a = PI + PI * (hr - 6) / 12.
        return (cxm + arx * k * math.cos(a), yH + ary * k * math.sin(a))
    if detail:
        dots = [arc_pt(6 + 12 * i / 120.) for i in range(121)]
        cv.obj([], 0)
        for i in range(0, 120, 3):
            cv.hair([dots[i], dots[i + 1]])
        for hr in range(7, 18):
            p0, p1 = arc_pt(hr, .965), arc_pt(hr, 1.035)
            (cv.line if hr % 3 == 0 else cv.hair)([p0, p1])
        for k in (.985, 1.015):
            seg = [arc_pt(best0 + (best1 - best0) * i / 30., k) for i in range(31)]
            cv.line(seg)

    # --- the sun, at the middle of the best window, rayed --------------------------------
    sun_hr = (best0 + best1) / 2.
    sx, sy = arc_pt(sun_hr)
    sr = max(5., min(W, H) * (.085 if detail else .14))
    if not detail:
        sx, sy = cxm, Y0 + H * .36
    nr = 28 if detail else 16
    for i in range(nr):
        a = 2 * PI * (i + .5) / nr
        long_ = i % 2 == 0
        r0, r1 = sr * 1.22, sr * (2.35 if long_ else 1.75)
        hw = (2 * PI / nr) * .32 * (1 if long_ else .8)
        if long_ and detail:
            pts_l, pts_r = [], []
            for j in range(9):
                t = j / 8.
                rr = r0 + (r1 - r0) * t
                wob = .12 * math.sin(t * 2.5 * PI) * (1 - t)
                w_ = hw * (1 - t * .92)
                pts_l.append((sx + rr * math.cos(a - w_ + wob), sy + rr * math.sin(a - w_ + wob)))
                pts_r.append((sx + rr * math.cos(a + w_ + wob), sy + rr * math.sin(a + w_ + wob)))
            poly = pts_l + pts_r[::-1]
        else:
            poly = [(sx + r0 * math.cos(a - hw), sy + r0 * math.sin(a - hw)),
                    (sx + r1 * math.cos(a), sy + r1 * math.sin(a)),
                    (sx + r0 * math.cos(a + hw), sy + r0 * math.sin(a + hw))]
        cv.obj([poly], .5)
        cv.hair([(sx + (r0 + 1) * math.cos(a), sy + (r0 + 1) * math.sin(a)),
                 (sx + r1 * .92 * math.cos(a), sy + r1 * .92 * math.sin(a))])
        if long_:
            cv.hair([(sx + (r0 + 1) * math.cos(a + hw * .5), sy + (r0 + 1) * math.sin(a + hw * .5)),
                     (sx + (r0 + (r1 - r0) * .55) * math.cos(a + hw * .2), sy + (r0 + (r1 - r0) * .55) * math.sin(a + hw * .2))])
    disc = _circ(sx, sy, sr * 1.12, 48)
    cv.obj([disc], 1.)
    ring = _circ(sx, sy, sr, 48)
    cv.line(ring + [ring[0]])
    if detail:
        for k in (.78, .56):
            c = _circ(sx, sy, sr * k, 40)
            cv.hair(c + [c[0]])
        cres = (_circ(sx, sy, sr * .97, 24, -.35 * PI, .85 * PI)
                + _circ(sx - sr * .28, sy - sr * .28, sr * .86, 24, .85 * PI, -.35 * PI))
        cv.hair(C.hatch_poly(cres, -45, 1.5))
        cv.hair(C.hatch_poly(_circ(sx, sy, sr * .95, 32), 0, 3, phase=.5))
    else:
        cres = (_circ(sx, sy, sr * .97, 20, -.35 * PI, .85 * PI)
                + _circ(sx - sr * .3, sy - sr * .3, sr * .86, 20, .85 * PI, -.35 * PI))
        cv.hair(C.hatch_poly(cres, -45, 2))
        cv.hair(C.hatch_poly(_circ(sx, sy, sr * .95, 24), 0, 3, phase=.5))

    # --- Mt. Hood and the far ridge -------------------------------------------------------
    if detail:
        hx = X0 + W * .76
        hy = yH - H * .2
        mt = [(hx - W * .3, yH + 1), (hx - W * .14, yH - H * .07), (hx - W * .05, hy + H * .06),
              (hx - W * .015, hy + H * .01), (hx, hy), (hx + W * .02, hy + H * .015),
              (hx + W * .08, hy + H * .09), (hx + W * .2, yH - H * .05), (hx + W * .32, yH + 1)]
        cv.obj([mt], 1.)
        east = [(hx, hy), (hx + W * .02, hy + H * .015), (hx + W * .08, hy + H * .09),
                (hx + W * .2, yH - H * .05), (hx + W * .32, yH + 1), (hx + W * .03, yH + 1),
                (hx + W * .01, hy + H * .08)]
        cv.hair(C.hatch_poly(east, 60, 1.5))
        for t in (.25, .45, .62):
            gx = hx - W * .05 * t * 2.2
            cv.hair([(hx - W * .004, hy + H * .01), (gx, hy + H * (.05 + t * .09))])
        low = _band(mt, hy + H * .115, yH + 1)
        if len(low) > 2:
            cv.hair(C.hatch_poly(low, 80, 1.5))
            cv.hair(C.hatch_poly(low, -30, 3))
        lit = [(hx - W * .3, yH + 1), (hx - W * .14, yH - H * .07), (hx - W * .05, hy + H * .06),
               (hx - W * .015, hy + H * .01), (hx, hy), (hx + W * .01, hy + H * .08), (hx + W * .03, yH + 1)]
        cv.hair(C.hatch_poly(_band(lit, hy, hy + H * .115), -25, 3))
        ridge = [(X0 - 2, yH + 1), (X0 - 2, yH - H * .05)]
        for i in range(25):
            t = i / 24.
            x = X0 + W * .62 * t
            ridge.append((x, yH - H * (.05 + .025 * math.sin(t * 7 + 1) + .012 * math.sin(t * 23))))
        ridge.append((X0 + W * .62, yH + 1))
        cv.obj([ridge], .5)
        cv.hair(C.hatch_poly(ridge, 90, 1.5))
        cv.hair(C.hatch_poly(ridge, 30, 2))

    # --- the Columbia: water lines broken by the sun's glitter path ------------------------
    if river > 2:
        rv = [(X0 - 3, yH), (X0 + W + 3, yH), (X0 + W + 3, yH + river), (X0 - 3, yH + river)]
        cv.obj([rv], 0)
        y = yH + 1.
        while y < yH + river - .5:
            x = X0 - 3
            while x < X0 + W + 3:
                L = rng.uniform(6, 18)
                g = 1.8 if abs(x - sx) > W * .08 else rng.uniform(2.5, 5)
                cv.hair([(x, y), (min(x + L, X0 + W + 3), y)])
                x += L + g
            y += 1.5
        shx = X0 + W * .66
        hull = [(shx - 8, yH + 1.2), (shx + 9, yH + 1.2), (shx + 7, yH + 3.6), (shx - 6.5, yH + 3.6)]
        cv.obj([hull], 0)
        cv.line(C.hatch_poly(hull, 0, 1.))
        cab = [(shx - 4, yH - 2.5), (shx + 4, yH - 2.5), (shx + 4, yH + 1.2), (shx - 4, yH + 1.2)]
        cv.obj([cab], .5)
        cv.hair(C.hatch_poly(cab, 90, 1.5))
        cv.line([(shx + 1, yH - 2.5), (shx + 1, yH - 6)])

    # --- the island ground: perspective furrows and rows ----------------------------------
    gy = yH + river
    land = [(X0 - 3, gy), (X0 + W + 3, gy), (X0 + W + 3, Y0 + H + 3), (X0 - 3, Y0 + H + 3)]
    cv.obj([land], .5 if river else 1.)
    vx = sx
    n_f = 30 if detail else 16
    for i in range(n_f + 1):
        bx = X0 - W * .6 + W * 2.2 * i / n_f
        t0 = .12
        cv.hair([(vx + (bx - vx) * t0, gy + (Y0 + H + 3 - gy) * t0), (bx, Y0 + H + 3)])
    yy, step = gy + 1.2, 1.4
    while yy < Y0 + H + 3:
        cv.hair([(X0 - 3, yy), (X0 + W + 3, yy)])
        yy += step
        step *= 1.22 if detail else 1.35

    # --- the barn (left, mid-distance) ----------------------------------------------------
    if detail:
        bx0, bw_, bh_ = X0 + W * .08, W * .17, H * .1
        by1 = gy + H * .055
        wall = [(bx0, by1 - bh_), (bx0 + bw_, by1 - bh_), (bx0 + bw_, by1), (bx0, by1)]
        roof = [(bx0 - 2, by1 - bh_), (bx0 + bw_ * .5, by1 - bh_ - H * .07), (bx0 + bw_ + 2, by1 - bh_)]
        tx, ty = bx0 + bw_ + W * .05, gy + H * .01
        cv.obj([[(tx - 1, ty), (tx + 1, ty), (tx + .8, ty - H * .08), (tx - .6, ty - H * .08)]], .5)
        for k, (ox, oy, rr) in enumerate(((-.03, -.13, .05), (.025, -.15, .055), (0, -.2, .05), (-.01, -.09, .045))):
            bx_, by_, R_ = tx + W * ox, ty + H * oy, W * rr
            crown = [(bx_ + R_ * math.cos(a) * (1 + .13 * math.sin(a * 6 + k)), by_ + R_ * .85 * math.sin(a) * (1 + .13 * math.cos(a * 5 + k)))
                     for a in [2 * PI * i / 36 for i in range(36)]]
            cv.obj([crown], .5)
            cv.hair(C.hatch_poly(crown, 0, 2))
            shade = [(x_, y_) for x_, y_ in crown if (x_ - bx_) + (y_ - by_) * .5 > -R_ * .1]
            if len(shade) > 2:
                cv.hair(C.hatch_poly(shade, 60, 1.5))
        cv.obj([wall], 1.)
        cv.hair(C.hatch_poly(wall, 90, 2))
        door = [(bx0 + bw_ * .35, by1 - bh_ * .7), (bx0 + bw_ * .65, by1 - bh_ * .7), (bx0 + bw_ * .65, by1), (bx0 + bw_ * .35, by1)]
        cv.obj([door], 1.)
        cv.hair([[door[0], door[2]], [door[1], door[3]]])
        cv.obj([roof], 1.)
        cv.hair(C.hatch_poly(roof, 0, 1.5))
        cv.hair(C.hatch_poly(roof, 35, 3))

    # --- the panel array: rows of racked panels facing the sun ----------------------------
    rows = ([(.29, .99, .69, .755, 7), (.13, 1.03, .80, .88, 8)] if detail else
            [(.06, .94, .72, .86, 6)])
    for ri, (u0, u1, v0, v1, ncol) in enumerate(rows):
        xl, xr = X0 + W * u0, X0 + W * u1
        yt, yb = Y0 + H * v0, Y0 + H * v1
        ins = (xr - xl) * .03
        p0, p1, p2, p3 = (xl + ins, yt), (xr - ins, yt), (xr, yb), (xl, yb)
        thick = max(1.2, (yb - yt) * .1)
        sh = [(xl + 2, yb), (xr, yb), (xr + 3, yb + (yb - yt) * .5), (xl + 4, yb + (yb - yt) * .5)]
        cv.obj([sh], 0)
        cv.hair(C.hatch_poly(sh, 0, 1.5))
        cv.hair(C.hatch_poly(sh, -30, 1.5))
        cv.obj([], 0)
        for lu in (.06, .35, .65, .94):
            lx = xl + (xr - xl) * lu
            cv.line([(lx, yb + thick), (lx + 1.5, yb + (yb - yt) * .42)])
        rail = [p3, p2, (p2[0], p2[1] + thick), (p3[0], p3[1] + thick)]
        face = [p0, p1, p2, p3]
        cv.obj([face, rail], 1.)
        cv.line(C.hatch_poly(rail, 0, 1.))
        nrow = 2
        g = .9
        for ci in range(ncol):
            for rj in range(nrow):
                q0 = _quad(p0, p1, p2, p3, ci / ncol, rj / nrow)
                q1 = _quad(p0, p1, p2, p3, (ci + 1) / ncol, rj / nrow)
                q2 = _quad(p0, p1, p2, p3, (ci + 1) / ncol, (rj + 1) / nrow)
                q3 = _quad(p0, p1, p2, p3, ci / ncol, (rj + 1) / nrow)
                cell = [(q0[0] + g, q0[1] + g * .8), (q1[0] - g, q1[1] + g * .8),
                        (q2[0] - g, q2[1] - g * .8), (q3[0] + g, q3[1] - g * .8)]
                lit = abs((ci + .5) / ncol - ((sx - xl) / (xr - xl)) + (rj - .5) * .08) < (.06 if detail else .09)
                if lit:
                    cv.hair(C.hatch_poly(cell, 45, 3.))
                else:
                    cv.hair(C.hatch_poly(cell, 0, 1.5, phase=.25))
                    cv.hair(C.hatch_poly(cell, 90, 1.5))
                    if detail:
                        a = _quad(q0, q1, q2, q3, .5, .08)
                        b = _quad(q0, q1, q2, q3, .5, .92)
                        cv.line([a, b])
        cv.line([p0, p1])

    # --- Easter egg: Parker's dog, curled asleep in the sun by the front row --------------
    if detail:
        dx, dy = X0 + W * .36, Y0 + H * .945
        s = max(.9, W / 125.)
        body = [(dx + 9 * s * math.cos(a), dy + 4.2 * s * math.sin(a) - 1.2 * s * math.sin(a) ** 2)
                for a in [2 * PI * i / 32 for i in range(32)]]
        cv.obj([body], 1.)
        for k in range(5):
            r_ = .35 + .14 * k
            arc = [(dx + 9 * s * r_ * math.cos(a), dy + 4.2 * s * r_ * math.sin(a) - .6 * s)
                   for a in [PI * (1.05 + .9 * j / 10) for j in range(11)]]
            cv.hair(arc)
        cv.hair(C.hatch_poly([(dx - 9 * s, dy), (dx + 9 * s, dy), (dx + 8 * s, dy + 3.5 * s), (dx - 8 * s, dy + 3.5 * s)], 0, 1.5))
        tail = [(dx + 8 * s + 2.5 * s * math.cos(a), dy + 1.5 * s + 2.5 * s * math.sin(a)) for a in [-PI * .5 + PI * 1.2 * j / 10 for j in range(11)]]
        cv.line(tail)
        hx_, hy_ = dx - 8.2 * s, dy + .6 * s
        head = [(hx_ + 3.4 * s * math.cos(a), hy_ + 2.7 * s * math.sin(a)) for a in [2 * PI * i / 20 for i in range(20)]]
        cv.obj([head], 1.)
        cv.hair(C.hatch_poly(head, 60, 1.5))
        snout = [(hx_ - 3 * s, hy_ - .2 * s), (hx_ - 6 * s, hy_ + .6 * s), (hx_ - 5.8 * s, hy_ + 2.2 * s), (hx_ - 2.4 * s, hy_ + 2.2 * s)]
        cv.obj([snout], 1.)
        cv.line([(hx_ - 6 * s, hy_ + .7 * s), (hx_ - 5.4 * s, hy_ + 1.2 * s)])
        ear = [(hx_ + .4 * s, hy_ - 2.4 * s), (hx_ + 3.2 * s, hy_ - 1.6 * s), (hx_ + 2.6 * s, hy_ + 2.4 * s), (hx_ + .4 * s, hy_ + 1 * s)]
        cv.obj([ear], 1.)
        cv.line(C.hatch_poly(ear, 0, 1.))
        cv.line([(hx_ - 1.6 * s, hy_ - .3 * s), (hx_ - .4 * s, hy_ - .1 * s)])


def _vignette(ctx, seed, detail=2):
    def fill(field, X0, Y0, W, H):
        cv = C.Canvas()
        _scene(cv, field, X0, Y0, W, H, ctx, seed, detail)
        return cv.svg()
    return fill


def _field_clip(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _sun_eye(cx, cy, r):
    """A small rayed sun rosette (banner, tablet)."""
    cv = C.Canvas()
    n = 12
    for i in range(n):
        a = 2 * PI * i / n
        hw = PI / n * .55
        poly = [(cx + r * .55 * math.cos(a - hw), cy + r * .55 * math.sin(a - hw)),
                (cx + r * math.cos(a), cy + r * math.sin(a)),
                (cx + r * .55 * math.cos(a + hw), cy + r * .55 * math.sin(a + hw))]
        cv.obj([poly], .5)
        cv.hair([(cx + r * .6 * math.cos(a), cy + r * .6 * math.sin(a)), (cx + r * .9 * math.cos(a), cy + r * .9 * math.sin(a))])
    cv.obj([_circ(cx, cy, r * .55, 24)], 1.)
    cv.hair(C.hatch_poly(_circ(cx + r * .1, cy + r * .1, r * .4, 16), -45, 1.5))
    return cv.svg()


# ------------------------------------------------------------------------------------------
# layouts (adapted from the house frame so the cartouche field is fully engraved)
# ------------------------------------------------------------------------------------------

def _cart_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a + .5, b + .5), (cx - a, cy - b, 2 * a, 2 * b)


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("sb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fx, fy = rx - 3.5, ry - 3.5
    field = C._ell_pts(cx, cy, fx, fy, 64)
    body = _vignette(ctx, seed, 0)(field, cx - fx, cy - fy, 2 * fx, 2 * fy)
    o.append(_field_clip(C._uid("sbf", w, h, seed), C._d(field, True, 0), body))
    o.append(f'<path d="{C._d(field, True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{C._n(h - .5)}h{C._n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.5)
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
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("sm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    field, (X0, Y0, W, H) = _cart_field(cx, cy, cw, ch)
    body = _vignette(ctx, seed, 2)(field, X0, Y0, W, H)
    o.append(_field_clip(C._uid("smf", w, h, seed), C._d(field, True, 0), body))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tablet_cells(x, y, w, h):
    """The pedestal's sunk tablet engraved as a long strip of solar cells, a sun at its centre."""
    cv = C.Canvas()
    box = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([box], 1.)
    cv.hair(C.hatch_poly(box, 0, 1.5))
    n = max(6, int(w / (h * 1.1)))
    g = 1.2
    cw = w / n
    for i in range(n):
        if abs((i + .5) - n / 2) < .8:
            continue
        cell = [(x + i * cw + g, y + g), (x + (i + 1) * cw - g, y + g), (x + (i + 1) * cw - g, y + h - g), (x + i * cw + g, y + h - g)]
        cv.obj([cell], .5)
        cv.hair(C.hatch_poly(cell, 90, 1.5))
        cv.line([(x + (i + .5) * cw, y + g), (x + (i + .5) * cw, y + h - g)])
    return cv.svg() + _sun_eye(x + w / 2, y + h / 2, h * .62)


def _layout_tall(w, h, seed, ctx, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.dark_ground((0, 0, w, top_free), "L"))
    o.append(f'<path d="M{C._n(px0 - 3.5)},{C._n(py0 - 3.5)}h{C._n(pw + 7)}v{C._n(ph + 7)}h{C._n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{C._n(px0 - 1.5)},{C._n(py0 - 1.5)}h{C._n(pw + 3)}v{C._n(ph + 3)}h{C._n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .18, ph * .25)
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("st", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    field, (X0, Y0, W, H) = _cart_field(cx, cy, cw, ch)
    body = _vignette(ctx, seed, 2)(field, X0, Y0, W, H)
    o.append(_field_clip(C._uid("stf", w, h, seed), C._d(field, True, 0), body))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    face = [(p[0], p[1] - bh / 2 + 1.2) for p in centre] + [(p[0], p[1] + bh / 2 - 1.2) for p in centre[::-1]]
    fcv = C.Canvas()
    fcv.obj([], 0)
    fcv.hair(C.hatch_poly(face, 0, 2, inset=.5))
    o.append(fcv.svg())
    for i in range(3, len(centre) - 3, 6):
        o.append(_sun_eye(centre[i][0], centre[i][1], bh * .34))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet_cells(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh - 2), "G"))
        o.append(C._clip(C._uid("sf", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=3)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{C._n(h - 1.5)}h{C._n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx, 1.)
    return C.svg_doc(w, h, body)
