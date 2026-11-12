"""The cover's date banner: the showpiece.  A swallow-tailed plaque, each tail holding a large volute;
a fleuron rising at the centre of the head band, a shell at the centre of the foot, fine scroll flowing
out from both to the tails."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (9, 26, 9, 26)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("banner", w, h, ctx), centre=("fleuron", None, "shell", None),
                     ends="tail")
    return cv.svg()
