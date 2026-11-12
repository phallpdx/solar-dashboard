"""Section divider (instead of a bare rule): an acanthus fleuron at the centre of a fine double rule, and a
fine scroll growing out of it to both sides, dying away (narrowing) toward the ends."""
from ._common import scroll, ctx_of, seed_of, canvas


def insets(w, h, ctx=None):
    return (0, 0, 0, 0)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    cv = canvas(w, h)
    sd = seed_of("divider", w, h, ctx)
    rng = scroll.rng_for("div", sd)
    f = scroll._f
    cy = h / 2
    cv.add("R05", "M0 %sH%s" % (f(round(cy * 2) / 2 + 0.25), f(w)))
    # three tapering stretches of scroll each side, each on its own dark ground
    mid = h * 1.4
    for side in (-1, 1):
        x0 = w / 2 + side * mid / 2
        span = w / 2 - mid / 2
        stretches = ((0.0, 0.42, h - 1), (0.42, 0.72, h * 0.72), (0.72, 0.92, h * 0.5))
        for k, (a, b, H) in enumerate(stretches):
            if H < 4:
                continue
            ua, ub = x0 + side * span * a, x0 + side * span * b
            pts = [(ua, cy), (ub, cy)] if side > 0 else [(ub, cy), (ua, cy)]
            run = scroll.Run(pts, H)
            scroll.strip(cv, run, (sd, side, k), flip=side < 0, ground=True)
    cv.add("M", "M%s %sH%sV%sH%sZ" % (f(w / 2 - mid / 2), f(0.5), f(w / 2 + mid / 2), f(h - 0.5), f(w / 2 - mid / 2)))
    scroll.fleuron(cv, w / 2, h - 1, h * 0.9, up=(0, -1), rng=rng)
    return cv.svg()
