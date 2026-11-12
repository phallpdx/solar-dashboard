"""Shared plumbing for the frame families: band widths, seeds, the canvas."""
import os
import sys

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _here not in sys.path:
    sys.path.insert(0, _here)
try:
    import scroll  # noqa: E402  (pure standard library; nothing to install)
except Exception as e:  # pragma: no cover - loud, so CI logs can be grepped
    sys.stderr.write("SCROLL FALLBACK: solar/scroll.py failed to import (%r)\n" % (e,))
    raise


def ctx_of(ctx):
    return dict(ctx or {})


def seed_of(family, w, h, ctx):
    return (family, ctx.get("seed", 0), round(w), round(h))


def band(ctx, default):
    b = ctx.get("band")
    if b is None:
        return tuple(default)
    if isinstance(b, (int, float)):
        return (b, b, b, b)
    return tuple(b)


def canvas(w, h):
    return scroll.Canvas(w, h)
