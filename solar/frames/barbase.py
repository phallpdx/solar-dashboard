"""Base under the hourly temperature bars: an engraved plinth.  A bright fillet on top, a running fine
scroll band below it with a shell at the centre, a volute console closing each end.  No slot."""
from ._common import scroll, ctx_of, seed_of, canvas


def insets(w, h, ctx=None):
    return (0, 0, 0, 0)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    cv = canvas(w, h)
    rng = scroll.rng_for("base", seed_of("barbase", w, h, ctx))
    e = h * 1.1
    cv.add("K", "M%s 0H%sV%sH%sZ" % (scroll._f(e), scroll._f(w - e), h, scroll._f(e)))
    H = h - 3.5
    run = scroll.Run([(e, 2 + H / 2), (w - e, 2 + H / 2)], H)
    scroll._compose_side(cv, run, ("base", ctx.get("seed", 0)), "shell" if H >= 6 else None, 1, motif_min=6)
    cv.over("R1", "M%s .5H%s" % (scroll._f(e - 1), scroll._f(w - e + 1)))
    cv.over("S1", "M%s 1.5H%s" % (scroll._f(e), scroll._f(w - e)))
    cv.over("R05", "M%s %sH%s" % (scroll._f(e), h - 0.25, scroll._f(w - e)))
    for left in (True, False):
        X = e * 0.5 if left else w - e * 0.5
        cv.circle("K", X, h / 2, h * 0.5)
        scroll.volute(cv, X, h / 2, h * 0.46, -1 if left else 1, 0.0 if left else 3.14159, rng, wmax=1.0)
    return cv.svg()
