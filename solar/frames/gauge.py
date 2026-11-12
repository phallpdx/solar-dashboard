"""Small horizontal gauge (rain %, solar kWh in the week grid): a thin tube bounded by double inlay lines,
the inside white for the fill drawn by the page; each end capped by a small volute."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (2, 5, 2, 5)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    rng = scroll.rng_for("gauge", seed_of("gauge", w, h, ctx))
    cv.slot = (l, t, w - l - r, h - t - b)
    f = scroll._f
    cv.add("K", "M%s 0H%sV%sH%sZ" % (f(l - 1), f(w - r + 1), h, f(l - 1)))
    cv.over("W", scroll._rect_d(l, t, w - r, h - b))
    cv.over("S1", "M%s %sH%s" % (f(l), f(t - 1), f(w - r)) + "M%s %sH%s" % (f(l), f(h - b + 1), f(w - r)))
    for left in (True, False):
        X = l / 2 if left else w - r / 2
        R = min(h / 2, (l if left else r) / 2 + 0.5)
        cv.circle("K", X, h / 2, R)
        scroll.volute(cv, X, h / 2, R * 0.92, 1 if left else -1, 3.14159 / 2, rng, wmax=1.0)
    return cv.svg()
