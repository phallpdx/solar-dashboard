"""House demo plate: engraving_codex.frame_plate with a simple placeholder vignette
(a rayed sun rising over ruled hills). Real pages replace _vignette with their own subject."""
import sys
import math
import engraving_codex as C


def _vignette(x, y, w, h):
    """Placeholder subject drawn inside the box the frame hands us."""
    cv = C.Canvas()
    cx, cy = x + w / 2, y + h * .64
    r = min(w, h) * .2
    cv.obj([], 0)
    for i in range(23):
        a = math.pi + math.pi * (i + .5) / 23
        r1 = r * (2.0 if i % 2 else 2.6)
        r1 = min(r1, (cy - y - 2) / max(.2, -math.sin(a)), (w / 2 - 2) / max(.2, abs(math.cos(a))))
        cv.hair([(cx + r * 1.2 * math.cos(a), cy + r * 1.2 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))])
    disc = C._ell_pts(cx, cy, r, r, 40, math.pi, 2 * math.pi)
    cv.obj([disc], 1.)
    cv.hair(C.hatch_poly(disc, 0, 3, .25))
    hills = ([(x, y + h * .74)] + [(x + w * t / 40, y + h * (.68 + .05 * math.sin(t / 40 * 7.5) + .03 * math.sin(t / 40 * 17)))
                                  for t in range(41)] + [(x + w, y + h), (x, y + h)])
    cv.obj([hills], 1.)
    cv.hair(C.hatch_poly(hills, 0, 2, .25))
    return cv.svg()


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", "")))
    return C.frame_plate(w, h, seed, _vignette)
