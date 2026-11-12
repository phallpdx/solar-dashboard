"""SECTIONS menu button: compact ears with twin lobes and a waist, each a volute and counter scroll."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (3, 14, 3, 14)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.plaque(cv, 0, 0, w, h, (l, r), t, seed_of("sections", w, h, ctx), kind="scroll")
    return cv.svg()
