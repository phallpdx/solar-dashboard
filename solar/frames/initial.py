"""Engraved initial square (drop cap): a square of fine scroll, a volute in every corner, the centre white
for one Literata capital set by the page."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (14, 14, 14, 14)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("initial", w, h, ctx), centre=(None,) * 4)
    return cv.svg()
