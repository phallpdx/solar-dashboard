"""markets-02 -- How markets look.
The New York Stock Exchange portico (six fluted columns, carved pediment, the flag on its staff)
under a ruled sky, with the S&P 500's candlestick climb (up 11% on the year) rising behind it to an
arrow. Two bull's horns grow out of the cartouche's shoulders into the acanthus. Small gold bars
and an oil barrel sit on the steps. Easter egg: a "P" monogram cut into the pediment, where the
NYSE's sculpture group would be, with a tiny pair of crossed drumsticks beneath it.
"""
import sys
import math
import random
import engraving_codex as C
from engraving_codex import Canvas, hatch_poly, _n, _d, _ell_pts

PI = math.pi


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _clip_path(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _series(seed, n):
    """A rising daily series ending near the top: up ~11% on the year, a dip near the end."""
    rng = random.Random(seed)
    v, out = 0.0, []
    for i in range(n + 1):
        t = i / n
        drift = 1.0 / n
        v += drift + rng.uniform(-.06, .06)
        if .7 < t < .82:
            v -= .05
        out.append(v)
    lo, hi = min(out), max(out)
    return [(x - lo) / (hi - lo or 1) for x in out]


# ------------------------------------------------------------------ the vignette
def vignette(field, box, seed, small=False):
    """field: closed polygon of the whole engraved field; box (x, y, w, h) its clear rect."""
    x, y, w, h = box
    fx0 = min(p[0] for p in field)
    fx1 = max(p[0] for p in field)
    fy0 = min(p[1] for p in field)
    fy1 = max(p[1] for p in field)
    FW, FH = fx1 - fx0, fy1 - fy0
    cx = (fx0 + fx1) / 2
    cv = Canvas()

    # sky: ruled, lighter (wider) toward the horizon, denser at the top
    cv.obj([field], 0)
    ground_y = y + h * (.94 if not small else .96)
    sky = [(fx0, fy0), (fx1, fy0), (fx1, ground_y), (fx0, ground_y)]
    split = fy0 + FH * .28
    cv.hair(hatch_poly(rect(fx0, fy0, FW, split - fy0), 0, 1.5, .25))
    cv.hair(hatch_poly(rect(fx0, split, FW, ground_y - split), 0, 2, .25))

    # candlestick chart rising behind the exchange
    n = 11 if small else 16
    ser = _series(seed, n)
    cx0, cx1 = fx0 + FW * .04, fx1 - FW * .12
    cy_lo, cy_hi = y + h * .55, fy0 + FH * .1
    step = (cx1 - cx0) / n
    bw = max(2.5, step * .62)
    pts = []
    for i in range(n + 1):
        px = cx0 + i * step
        o_ = ser[i - 1] if i else ser[0] - .05
        c_ = ser[i]
        yo = cy_lo + (cy_hi - cy_lo) * o_
        yc = cy_lo + (cy_hi - cy_lo) * c_
        pts.append((px, yc))
        top, bot = min(yo, yc) - step * .5, max(yo, yc) + step * .5
        body = rect(px - bw / 2, min(yo, yc), bw, max(3., abs(yc - yo)))
        cv.obj([body], 1.)
        cv.hair([(px, top), (px, min(yo, yc))])
        cv.hair([(px, max(yo, yc) + max(0, 1.5 - abs(yc - yo))), (px, bot)])
        if c_ < o_ or (i and ser[i] < ser[i - 1]):  # down day: cut solid
            cv.line(hatch_poly(body, 0, 1., .5))
    # trend line + arrow head
    cv.obj([], 0)
    cv.heavy(pts)
    ex, ey = pts[-1]
    a = math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0])
    L = 7 if small else 11
    tip = (ex + L * math.cos(a), ey + L * math.sin(a))
    head = [tip, (ex + L * .35 * math.cos(a + 2.2), ey + L * .35 * math.sin(a + 2.2)),
            (ex + L * .35 * math.cos(a - 2.2), ey + L * .35 * math.sin(a - 2.2))]
    cv.obj([head], 1.)
    cv.line(hatch_poly(head, 0, 1., .5))

    # ---- the exchange portico
    bwid = min(FW * .7, h * 1.3)
    bx0, bx1 = cx - bwid / 2, cx + bwid / 2
    steps_h = h * .07
    base_y = ground_y
    stylo = base_y - steps_h
    ent_h = h * .085
    col_top = y + h * .4
    ped_top = col_top - ent_h - h * .16
    # recess behind the columns: dark, cross-ruled
    rec = rect(bx0 + bwid * .04, col_top, bwid * .92, stylo - col_top)
    cv.obj([rec], 1.)
    cv.hair(hatch_poly(rec, 0, 1.5, .5))
    cv.hair(hatch_poly(rec, 90, 3, 1))
    # doors: three tall black openings
    for k in (-1, 0, 1):
        dx = cx + k * bwid * .3
        dw = bwid * .07
        door = rect(dx - dw / 2, stylo - (stylo - col_top) * .55, dw, (stylo - col_top) * .55)
        cv.obj([door], .5)
        cv.line(hatch_poly(door, 0, 1., .5))
    # columns
    ncol = 6
    cw = bwid * .075
    for i in range(ncol):
        px = bx0 + bwid * (.08 + .84 * i / (ncol - 1))
        shaft = [(px - cw * .5, stylo - cw * .25), (px - cw * .44, col_top + cw * .55),
                 (px + cw * .44, col_top + cw * .55), (px + cw * .5, stylo - cw * .25)]
        cv.obj([shaft], 1.)
        nf = 3 if small else 5
        for j in range(1, nf):
            t = j / nf
            cv.hair([(px - cw * .5 + cw * t, stylo - cw * .3), (px - cw * .44 + cw * .88 * t, col_top + cw * .6)])
        # shadow on the right of the drum
        sh = [(px + cw * .12, stylo - cw * .25), (px + cw * .14, col_top + cw * .55),
              (px + cw * .44, col_top + cw * .55), (px + cw * .5, stylo - cw * .25)]
        cv.hair(hatch_poly(sh, 90, 1.5 if not small else 2, .25))
        # base
        b1 = rect(px - cw * .7, stylo - cw * .3, cw * 1.4, cw * .3)
        cv.obj([b1], .5)
        cv.hair(hatch_poly(rect(px, stylo - cw * .3, cw * .7, cw * .3), 0, 1.5, .25))
        # capital: abacus + volutes
        cap = [(px - cw * .78, col_top), (px + cw * .78, col_top), (px + cw * .5, col_top + cw * .6),
               (px - cw * .5, col_top + cw * .6)]
        cv.obj([cap], 1.)
        for s in (-1, 1):
            cv.hair(_ell_pts(px + s * cw * .45, col_top + cw * .28, cw * .18, cw * .18, 10))
        cv.hair(hatch_poly([(px, col_top), (px + cw * .78, col_top), (px + cw * .5, col_top + cw * .6),
                            (px, col_top + cw * .6)], 90, 1.5, .25))
    # entablature: architrave, frieze, cornice
    ent = rect(bx0 - bwid * .02, col_top - ent_h, bwid * 1.04, ent_h)
    cv.obj([ent], 1.)
    cv.hair([(bx0 - bwid * .02, col_top - ent_h * .35), (bx1 + bwid * .02, col_top - ent_h * .35)])
    cv.hair([(bx0 - bwid * .02, col_top - ent_h * .55), (bx1 + bwid * .02, col_top - ent_h * .55)])
    cv.hair(hatch_poly(rect(bx0 - bwid * .02, col_top - ent_h * .35, bwid * 1.04, ent_h * .35), 0, 1.5, .25))
    # dentils
    ndt = int(bwid / 4)
    for i in range(ndt):
        dx = bx0 + bwid * (i + .5) / ndt
        cv.line([(dx, col_top - ent_h * .9), (dx, col_top - ent_h * .62)])
    cor = rect(bx0 - bwid * .05, col_top - ent_h - 2.5, bwid * 1.1, 2.5)
    cv.obj([cor], 1.)
    cv.hair(hatch_poly(cor, 0, 1.5, .25))
    # pediment
    pb = col_top - ent_h - 2.5
    ped = [(bx0 - bwid * .05, pb), (cx, ped_top), (bx1 + bwid * .05, pb)]
    cv.obj([ped], 1.)
    inn = [(bx0 + bwid * .05, pb - 1.5), (cx, ped_top + (pb - ped_top) * .28), (bx1 - bwid * .05, pb - 1.5)]
    cv.obj([inn], 1.)
    cv.hair(hatch_poly(inn, 0, 1.5, .5))
    cv.hair(hatch_poly(inn, 60, 3, .5))
    # raking cornice shading
    cv.hair(hatch_poly([(cx, ped_top), (bx1 + bwid * .05, pb), (bx1 - bwid * .05, pb - 1.5),
                        (cx, ped_top + (pb - ped_top) * .28)], 90, 1.5, .25))
    # P monogram medallion in the tympanum (Easter egg)
    mr = (pb - ped_top) * .3
    mx, my = cx, pb - mr - 2.2
    disc = _ell_pts(mx, my, mr, mr, 28)
    cv.obj([disc], 1.)
    if mr > 3.5:
        s = mr / 6.
        stem = rect(mx - 2.2 * s, my - 4 * s, 1.4 * s, 8 * s)
        bowl_o = _ell_pts(mx - .4 * s, my - 1.6 * s, 2.6 * s, 2.4 * s, 20, -PI / 2, PI / 2)
        cv.heavy([(mx - 1.6 * s, my - 4 * s)] + bowl_o + [(mx - 1.6 * s, my + .8 * s)])
        cv.heavy([(mx - 1.5 * s, my - 4 * s), (mx - 1.5 * s, my + 4 * s)])
        # crossed drumsticks under the P
        for sg in (-1, 1):
            cv.line([(mx - sg * 4.2 * s, my + 4.6 * s), (mx + sg * 4.2 * s, my + 1.4 * s)])
        cv.hair(stem[:0])
    # flagstaff + flag on the apex
    fs_top = ped_top - h * (.17 if not small else .12)
    flag_cv = cv
    if small:
        flag_cv = Canvas()  # the flag would swamp the little medallion: draw it nowhere
    _flag(flag_cv, cx, ped_top, fs_top, bwid, h)
    _steps_and_street(cv, locals())
    if not small:
        _props(cv, locals())
    return cv.svg()


def _flag(cv, cx, ped_top, fs_top, bwid, h):
    cv.obj([], 0)
    cv.line([(cx, ped_top), (cx, fs_top)])
    fl_w, fl_h = bwid * .2, h * .08
    flag = []
    for i in range(13):
        t = i / 12
        flag.append((cx + fl_w * t, fs_top + 1 + math.sin(t * PI * 1.5) * 1.6))
    bot = [(px_, py_ + fl_h) for px_, py_ in flag[::-1]]
    fpoly = flag + bot
    cv.obj([fpoly], 1.)
    for k in range(1, 7):
        t = k / 7
        if k % 2:
            cv.line([(px_, py_ + fl_h * t) for px_, py_ in flag])
    canton = flag[:6] + [(px_, py_ + fl_h * .5) for px_, py_ in flag[:6][::-1]]
    cv.obj([canton], .5)
    cv.hair(hatch_poly(canton, 45, 1.5, .25))
    cv.obj([_ell_pts(cx, fs_top - 1, 1.3, 1.3, 8)], 1.)


def _steps_and_street(cv, v):
    stylo, steps_h, bx0, bx1, bwid = v["stylo"], v["steps_h"], v["bx0"], v["bx1"], v["bwid"]
    fx0, fx1, fy1, ground_y, cx, h = v["fx0"], v["fx1"], v["fy1"], v["ground_y"], v["cx"], v["h"]
    # steps
    for k in range(3):
        sy = stylo + steps_h * k / 3
        st = rect(bx0 - bwid * (.06 + .04 * k), sy, bwid * (1.12 + .08 * k), steps_h / 3)
        cv.obj([st], 1.)
        cv.hair(hatch_poly(rect(st[0][0], sy + steps_h / 3 * .55, bwid * (1.12 + .08 * k), steps_h / 3 * .45), 0, 1.5, .25))
    # ground: the street, ruled in perspective, with cobbles
    gp = [(fx0, ground_y), (fx1, ground_y), (fx1, fy1), (fx0, fy1)]
    cv.obj([gp], 0)
    cv.hair(hatch_poly(gp, 0, 2, .5))
    for i in range(-8, 9):
        cv.hair([(cx + i * bwid * .07, ground_y), (cx + i * bwid * .2, fy1)])
    cv.line([(fx0, ground_y), (fx1, ground_y)])


def _props(cv, v):
    bx0, bx1, bwid, ground_y, h = v["bx0"], v["bx1"], v["bwid"], v["ground_y"], v["h"]
    # gold bars stacked at left of the steps, an oil barrel at right
    if True:
        gx = bx0 - bwid * .17
        gb = h * .045
        for r_, n_ in ((0, 3), (1, 2), (2, 1)):
            for j in range(n_):
                xx = gx + (j - n_ / 2) * gb * 2.1 + r_ * 0
                yy = ground_y - gb * (r_ + 1)
                bar = [(xx, yy + gb), (xx + gb * .35, yy), (xx + gb * 1.75, yy), (xx + gb * 2.1, yy + gb)]
                cv.obj([bar], 1.)
                cv.hair(hatch_poly([(xx + gb * 1.4, yy + gb), (xx + gb * 1.75, yy), (xx + gb * 2.1, yy + gb)], 90, 1.5, .25))
        ox = bx1 + bwid * .12
        bh_, bwd = h * .12, h * .075
        barrel = rect(ox, ground_y - bh_, bwd, bh_)
        cv.obj([barrel], 1.)
        for t in (.25, .75):
            cv.line([(ox, ground_y - bh_ * t), (ox + bwd, ground_y - bh_ * t)])
        cv.hair(hatch_poly(rect(ox + bwd * .62, ground_y - bh_, bwd * .38, bh_), 90, 1.5, .25))
        drop = [(ox + bwd / 2 + 2.4 * math.cos(t), ground_y - bh_ * .5 + 2.4 * math.sin(t)) for t in
                [i / 10 * PI for i in range(11)]] + [(ox + bwd / 2, ground_y - bh_ * .5 - 5)]
        cv.obj([drop], .5)
        cv.line(hatch_poly(drop, 0, 1., .5))


# ------------------------------------------------------------------ bull's horns on the cartouche
def horns(cx, cy, cw, ch, seed, top):
    """Two shaded bull's horns springing from the cartouche shoulders: out, up, tips turning in."""
    cv = Canvas()
    for side in (-1, 1):
        x0 = cx + side * cw * .33
        y0 = cy - ch * .36
        ln = 30
        L = min(cw * .3, (y0 - top) * 1.5)
        wd = cw * .055
        pts = [(x0, y0)]
        hd = 0. if side > 0 else 180.
        for i in range(ln):
            t = i / ln
            hd -= side * (130. / ln) * (.4 + 1.2 * t)
            r = math.radians(hd)
            px, py = pts[-1]
            pts.append((px + L / ln * math.cos(r), py + L / ln * math.sin(r)))
        left, right = [], []
        for i, (px, py) in enumerate(pts):
            j = min(i, ln - 1)
            dx, dy = pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]
            m = math.hypot(dx, dy) or 1
            nx, ny = -dy / m, dx / m
            ww = wd * (1 - i / ln) ** .9 + .3
            left.append((px + nx * ww, py + ny * ww))
            right.append((px - nx * ww, py - ny * ww))
        poly = left + right[::-1]
        cv.obj([poly], 1.)
        # growth rings near the root
        for i in range(1, int(ln * .45), 2):
            cv.hair([left[i], right[i]])
        # the underside (outer edge of the bend) shaded dark, lines along the form
        under = right if side > 0 else left
        for f in (.15, .35, .52, .66, .78, .88):
            ln_ = []
            for i in range(int(ln * (.97 - f * .25))):
                px, py = pts[i]
                ux, uy = under[i]
                ln_.append((px + (ux - px) * f, py + (uy - py) * f))
            cv.hair(ln_)
        # black polished tip
        tipp = [left[i] for i in range(int(ln * .78), ln + 1)] + [right[i] for i in range(ln, int(ln * .78) - 1, -1)]
        cv.obj([tipp], 1.)
        cv.line(hatch_poly(tipp, 0, 1., .5))
        cv.hair(hatch_poly(tipp, 90, 1., .5))
    return cv.svg()


def _letters(s, cx, cy, hgt):
    import engraving_morning as M
    polys, _w = M._text_polys(s, cx, cy - hgt / 2, hgt, 1.6, True)
    return polys


# ------------------------------------------------------------------ plate
def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    state = {}

    def fill(x, y, bw, bh):
        cx, cy = x + bw / 2, y + bh / 2
        if h < 110:
            k = .7071
            rx, ry = bw / 2 / k + 5 - 4, bh / 2 / k + 5 - 4
            field = _ell_pts(cx, cy, rx, ry, 64)
            small = True
        else:
            k = 2 ** (-1 / 2.6)
            a, b = bw / 2 / k + 6, bh / 2 / k + 6
            field = C._superellipse(cx, cy, a, b)
            small = False
        body = vignette(field, (x, y, bw, bh), seed, small)
        state["field"] = field
        return _clip_path(C._uid("mk", w, h, seed), _d(field, True, 0), body)

    svg = C.frame_plate(w, h, seed, fill, density=.85 if h > 260 else 1.)
    f = state["field"]
    fx0 = min(p[0] for p in f); fx1 = max(p[0] for p in f)
    fy0 = min(p[1] for p in f); fy1 = max(p[1] for p in f)
    extra = ""
    if 110 <= h <= 260:
        em = min(12., 6 + h * .025)
        hcw, hch = (fx1 - fx0) * 1.15, (fy1 - fy0) * 1.15
        extra += horns((fx0 + fx1) / 2, (fy0 + fy1) / 2, hcw, hch, seed, em + 2)
    elif h > 260:
        # re-derive the tall layout's banner and pedestal tablet to engrave them
        ped_h = min(max(h * .17, 48), 86.)
        top_free = min(h * .055, 26.)
        ph = h - top_free - ped_h + ped_h * .3
        pw = w - 12
        cw, ch = pw * .44, ph * .58
        cy = top_free + ph * .45
        _b, centre = C.ribbon_banner(w / 2, cy + ch * .47, cw * 1.4, min(16, ph * .05), .04, 0)
        bh = min(16, ph * .05)
        cv = Canvas()
        cv.obj([], 0)
        ymd = (ctx.get("date") or "2026-11-11").split("-")
        txt = " · ".join(_roman(int(v)) for v in (ymd[1], ymd[2], ymd[0]))
        mid = centre[len(centre) // 2]
        cv.line(_letters(txt, mid[0], mid[1] + .3, bh * .5))
        _p, (tx, ty, tw, th) = C.pedestal(0, h - ped_h, w, ped_h, 0)
        tab = rect(tx + 3, ty + 3, tw - 5, th - 5)
        cv.obj([tab], 0)
        cv.hair(hatch_poly(tab, 0, 2, .5))
        ser = _series(seed + 1, 30)
        pts = [(tx + 8 + (tw - 40) * i / 30, ty + th - 3.5 - (th - 7) * v) for i, v in enumerate(ser)]
        area = pts + [(pts[-1][0], ty + th - 2), (pts[0][0], ty + th - 2)]
        cv.obj([area], 0)
        cv.hair(hatch_poly(area, 90, 1.5, .5))
        cv.obj([], 0)
        cv.heavy(pts)
        ex, ey = pts[-1]
        cv.obj([[(ex + 7, ey - 3), (ex - 1, ey - 5), (ex + 1, ey + 2)]], 1.)
        cv.line(hatch_poly([(ex + 7, ey - 3), (ex - 1, ey - 5), (ex + 1, ey + 2)], 0, 1., .5))
        extra += cv.svg()
    return svg.replace("</svg>", extra + "</svg>")


def _roman(n):
    out = ""
    for v, r in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
                 (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += r
            n -= v
    return out
