"""Running head (section name, "Sheet 1 of 3"): small swallow-tail ears, each a volute and counter scroll
with acanthus; head and foot a fine double inlay."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (3, 16, 3, 16)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.plaque(cv, 0, 0, w, h, (l, r), t, seed_of("runhead", w, h, ctx), kind="tail")
    return cv.svg()
