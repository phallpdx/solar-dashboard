"""Small horizontal gauge (rain %, solar kWh): a white tube between fine double inlay lines, capped at each
end by a round ear holding a volute.  The slot is white for the page's own fill."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (2, 14, 2, 14)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.plaque(cv, 0, 0, w, h, (l, r), t, seed_of("gauge", w, h, ctx), kind="round")
    return cv.svg()
