"""Table head row: rolled volute ears at both ends, a fine double inlay along the head and foot, one closed
band (no floating lines)."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (3, 20, 3, 20)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.plaque(cv, 0, 0, w, h, (l, r), t, seed_of("tablehead", w, h, ctx), kind="roll")
    return cv.svg()
