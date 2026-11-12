"""Buttons (Prev / Next page, More, Skip to ...): a plaque with rolled scroll ends, a shell at the head of
the top band, fine scroll top and bottom; a heavier rule under the foot so it sits proud and reads as
pressable."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (7, 16, 7, 16)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("button", w, h, ctx),
                     centre=("shell" if w > 110 else None, None, None, None), ends="roll", raised=True)
    return cv.svg()
