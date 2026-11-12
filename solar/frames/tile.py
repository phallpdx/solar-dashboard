"""Stat tile (sunrise, sunset, AQI, UV, tide, kWh): a square-cornered frame, a volute turning each corner,
fine scroll on every side and a rosette boss at the head."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (8, 8, 8, 8)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("tile", w, h, ctx), centre=("rosette", None, None, None))
    return cv.svg()
