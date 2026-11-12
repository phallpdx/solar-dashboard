"""A whole-sheet engraved ground in the manner of a gun engraver's scroll panel: a few LARGE
log-spiral scrolls packed across the page, alternating in rotation, each carrying overlapping
acanthus leaves along the outside of its curve, white and modelled (shade cuts only on the shadow
side, a heavier outline below and to the right), set on a dark, quiet cut-away ground of tight
single-direction hatching. Non-repeating: one 618 x 720 composition, seeded.
Hidden in it: a P monogram in one spiral eye, crossed drumsticks in a leaf cluster, a paw print.

    page_ground(seed=0, W=618, H=720) -> svg string
"""
import math
import random


def _f(v):
    s = "%.1f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _pl(pts):
    return "M" + "L".join("%s %s" % (_f(x), _f(y)) for x, y in pts)


def _spiral(cx, cy, r0, th0, turns, sg, k, n=70):
    out = []
    T = turns * 2 * math.pi
    for i in range(n):
        th = T * i / (n - 1)
        r = r0 * math.exp(-k * th)
        a = th0 + sg * th
        out.append((cx + r * math.cos(a), cy + r * math.sin(a), a, r))
    return out


def _leaf(base, ang, L, Wd, lobes, curl, light):
    """An acanthus leaf from base along angle ang: white body, lobed edge, 1px outline, a 1.5px
    heavier edge on the shadow side, and 0.5px shade cuts across the shadow half only."""
    bx, by = base
    n = 16
    mid = []
    for i in range(n + 1):
        t = i / n
        a = ang + curl * t * t
        if not mid:
            mid.append((bx, by))
        else:
            px, py = mid[-1]
            mid.append((px + math.cos(a) * L / n, py + math.sin(a) * L / n))
    left, right = [], []
    for i, (x, y) in enumerate(mid):
        t = i / n
        a = ang + curl * t * t
        nx, ny = -math.sin(a), math.cos(a)
        h = Wd * math.sin(math.pi * min(1, t * 1.08)) ** .7 * (1 - .3 * t) * (.75 + .25 * abs(math.cos(t * math.pi * lobes)))
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))
    body = left + right[::-1]
    # the shadow side is the one facing away from the light (light from upper left)
    lx, ly = light
    sx = left if (left[n // 2][0] - mid[n // 2][0]) * lx + (left[n // 2][1] - mid[n // 2][1]) * ly < 0 else right
    shade = []
    for i in range(2, n - 1):
        mx, my = mid[i]
        ex, ey = sx[i]
        shade.append("M%s %sL%s %s" % (_f(mx + (ex - mx) * .25), _f(my + (ey - my) * .25), _f(ex), _f(ey)))
    return (_pl(body) + "Z", _pl(sx[1:]), "".join(shade), _pl(mid[1:-2]))


def page_ground(seed=0, W=618, H=720):
    rng = random.Random(seed)
    light = (-1.0, -1.0)
    white, out1, out15, hair, stems = [], [], [], [], []
    # scroll centres on a jittered grid: three across, four down, alternating rotation
    cols, rows = 3, 4
    cw, rh = W / cols, H / rows
    k = 0
    eggs = []
    for r in range(rows):
        for c in range(cols):
            cx = cw * (c + .5) + rng.uniform(-18, 18) + (cw * .25 if r % 2 else 0) - cw * .12
            cy = rh * (r + .5) + rng.uniform(-14, 14)
            sg = 1 if (r + c) % 2 == 0 else -1
            R = rng.uniform(.5, .6) * min(cw, rh) * 1.1
            th0 = rng.uniform(0, 2 * math.pi)
            sp = _spiral(cx, cy, R, th0, 1.55, sg, .26)
            # the scroll band: a white ribbon with a 1.5px outline, tapering toward the eye
            for j in range(0, len(sp) - 1, 6):
                seg = sp[j:j + 7]
                w = max(2.5, 11 * (1 - j / len(sp)) ** 1.2)
                d = _pl([(p[0], p[1]) for p in seg])
                stems.append((d, w))
            # shade cut along the inside of the ribbon (shadow side)
            inner = [(x - math.cos(a) * 2.2, y - math.sin(a) * 2.2) for x, y, a, rr in sp[:50]]
            hair.append(_pl(inner))
            ex, ey = sp[-1][0], sp[-1][1]
            eggs.append((ex, ey, k))
            # leaves along the outside of the curve, overlapping
            nl = rng.randint(8, 11)
            for i in range(nl):
                j = int(2 + i * (len(sp) * .7) / nl)
                x, y, a, rr = sp[j]
                tang = a + sg * math.pi / 2
                out_ang = tang - sg * .35 + rng.uniform(-.2, .2)
                L = max(14, rr * rng.uniform(.8, 1.15))
                Wd = L * rng.uniform(.3, .38)
                b, heavy, sh, rib = _leaf((x + math.cos(a) * 3, y + math.sin(a) * 3), out_ang, L, Wd, rng.choice((2.5, 3, 3.5)), -sg * .9, light)
                white.append(b)
                out1.append(b)
                out15.append(heavy)
                hair.append(sh)
                hair.append(rib)
            k += 1
    # eggs: a P in one spiral eye, a paw in another, crossed drumsticks by a third
    egg = []
    if eggs:
        x, y, _ = eggs[4 % len(eggs)]
        egg.append('<circle cx="%s" cy="%s" r="7" fill="#fff" stroke="#000"/>'
                   '<text x="%s" y="%s" font-family="Georgia,serif" font-size="11" font-weight="700" text-anchor="middle">P</text>'
                   % (_f(x), _f(y), _f(x), _f(y + 4)))
        x, y, _ = eggs[7 % len(eggs)]
        egg.append('<circle cx="%s" cy="%s" r="7" fill="#fff" stroke="#000"/>' % (_f(x), _f(y)))
        for dx, dy, rr in ((0, 1.6, 2), (-3, -1.6, 1), (-1, -3, 1), (1, -3, 1), (3, -1.6, 1)):
            egg.append('<circle cx="%s" cy="%s" r="%s"/>' % (_f(x + dx), _f(y + dy), rr))
        x, y, _ = eggs[9 % len(eggs)]
        egg.append('<circle cx="%s" cy="%s" r="9" fill="#fff" stroke="#000"/>'
                   '<path d="M%s %sL%s %sM%s %sL%s %s" stroke="#000" stroke-width="1.5" stroke-linecap="round"/>'
                   '<circle cx="%s" cy="%s" r="1.3"/><circle cx="%s" cy="%s" r="1.3"/>'
                   % (_f(x), _f(y), _f(x - 6), _f(y + 6), _f(x + 5), _f(y - 5), _f(x + 6), _f(y + 6), _f(x - 5), _f(y - 5),
                      _f(x + 5), _f(y - 5), _f(x - 5), _f(y - 5)))
        # a dog's head (profile, ear down, asleep) in one scroll's eye, a heron's head and bill in another
        x, y, _ = eggs[1 % len(eggs)]
        egg.append('<circle cx="%s" cy="%s" r="10" fill="#fff" stroke="#000"/>'
                   '<path d="M%s %sc3-4 9-4 11 0l3 1.5c1 .8.6 2-.6 2.2l-3 .3c-.8 2.6-4 3.8-7 3-2.6-.8-4-3.6-3.4-7z" fill="#fff" stroke="#000"/>'
                   '<path d="M%s %sc-2 2-2.4 5.6-.6 7.6c1.4-.6 2-3.4 1.6-6z"/><circle cx="%s" cy="%s" r="1"/>'
                   '<path d="M%s %sq1.4 .9 2.8 0" fill="none" stroke="#000" stroke-width=".5"/>'
                   % (_f(x), _f(y), _f(x - 7), _f(y - 1), _f(x - 3.5), _f(y - 2.6), _f(x + 7.4), _f(y + .3),
                      _f(x - .2), _f(y - 1.2)))
        x, y, _ = eggs[10 % len(eggs)]
        egg.append('<circle cx="%s" cy="%s" r="10" fill="#fff" stroke="#000"/>'
                   '<path d="M%s %sc0-3 2-5 4.5-5s4 2 4 4l8 1.6l-8 .6c-.4 2-1.4 3-2 4.6c-.8 2-1 3.6-.6 5" fill="#fff" stroke="#000" stroke-linejoin="round"/>'
                   '<circle cx="%s" cy="%s" r=".9"/><path d="M%s %sl-6 2.5" fill="none" stroke="#000" stroke-width=".7" stroke-linecap="round"/>'
                   % (_f(x), _f(y), _f(x - 5), _f(y + 1), _f(x - .2), _f(y - 2.2), _f(x - 2.5), _f(y - 3.4)))
    st = "".join('<path d="%s" stroke="#000" stroke-width="%s"/>' % (d, _f(w + 3)) for d, w in stems)
    st += "".join('<path d="%s" stroke="#fff" stroke-width="%s"/>' % (d, _f(w)) for d, w in stems)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
            '<defs><pattern id="g" width="2" height="2" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">'
            '<path d="M0 .5H2" stroke="#000" stroke-width=".5"/></pattern></defs>'
            '<rect width="%d" height="%d" fill="url(#g)"/>'
            '<g fill="none" stroke-linecap="round" stroke-linejoin="round">%s</g>'
            '<path d="%s" fill="#fff" stroke="#000" stroke-width="1"/>'
            '<path d="%s" fill="none" stroke="#000" stroke-width="1.5" stroke-linecap="round"/>'
            '<path d="%s" fill="none" stroke="#000" stroke-width=".5"/>%s</svg>'
            % (W, H, W, H, W, H, st, "".join(white), "".join(out15), "".join(hair), "".join(egg)))
