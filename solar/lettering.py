"""Hand-lettered headlines: an original engraver's roundhand, composed afresh for every headline.

    from solar.lettering import headline
    svg = headline("Is the mountain out?", width=506, size=30)

`headline(text, width, size, seed=0)` returns one self-contained SVG string: filled outlines only (no <text>, no
fonts, no external references), at most `width` CSS px wide, with `width`/`height` attributes in CSS px and a
matching viewBox. `size` is the type size it stands in for; the lettering's x-height is about half of it.

How it is drawn. Every letter is a skeleton: a few smooth pen paths through hand-placed points, in units of the
x-height, upright. Nothing here is taken from a font or a specimen: the shapes are drawn for this module, in the
manner of copperplate roundhand and banknote script (a pointed pen held on a slant: weight comes from pressure,
so strokes moving down the slant swell and strokes moving up or across are hairlines). A headline is composed
letter by letter: lowercase letters join with hairline connectors from one letter's exit to the next one's entry,
each word starts with a short lead-in, and the last letter may finish with a small flick. The pen is then
followed along each path and the outline of the swelling stroke is written out as a filled path.

Lettered for itself. The text seeds everything that is not fixed: the slant, the width, the weight and contrast,
ascender and descender length, which alternate of each letter is used (a letter is never drawn the same way twice
in a row), a small tremor in every point, a slight rise and fall of the baseline, and the underline flourish.
Two headlines therefore never look like one font repeated, and the same headline always comes out the same.

Legibility comes first: a large x-height against short ascenders and descenders, a moderate slant, open counters,
roman-structured capitals, hairlines that never drop under about one device pixel at 2x, generous word spaces,
and flourishes kept below the words, clear of every letter. One or two lines; a long headline is set smaller
before it is ever set on three.

Pure Python (no numpy), importable on its own: the Morning and Evening Editions both call it.
"""
import hashlib
import math
import random
import unicodedata

__all__ = ["headline", "Unsupported"]


class Unsupported(ValueError):
    """The text has a character the hand has no letter for (the caller keeps its type instead)."""


# ---------------------------------------------------------------- the hand
# Units: x-height = 1, baseline y = 0, y up, upright (the slant is applied when a headline is composed).
# A glyph: "s" = the joined strokes in pen order (the first one's start is the entry, the last one's end is the
# exit), "x" = strokes made after (dots, crossbars, hairline crossings), "e" = the direction a connector arrives
# in, "j" = False when nothing joins out of the letter (the next letter starts with its own lead-in),
# "a" = advance (default: right-most point + .06), "lead" = False when a word-initial letter needs no lead-in.
# A stroke is "x,y x,y ..." through which a smooth pen path runs; a prefix "h:" draws it as a hairline whatever
# its direction, "m:" at half pressure.

def _turn(x, top=1.0):
    """A stem from `top` down to the baseline turning out into the exit hairline."""
    return f"{x:.2f},{top:.2f} {x:.2f},0.30 {x + .01:.2f},0.10 {x + .09:.2f},0.00 {x + .20:.2f},0.03 {x + .31:.2f},0.16"


LOOP = "0.02,0.70 0.16,1.10 0.30,1.48 0.36,1.74 0.30,1.85 0.20,1.80 0.15,1.52 0.13,1.20"   # looped ascender, to (0.13,1.2)
PLAIN = "0.08,1.70 0.16,1.82 0.18,1.70 0.16,1.40 0.14,1.20"                                  # plain ascender with a tick
ARCH = "{x0:.2f},0.42 {a:.2f},0.80 {b:.2f},0.99 {c:.2f},0.95 {x1:.2f},0.70"


def _arch(x0, x1):
    return ARCH.format(x0=x0, a=x0 + .07, b=x0 + .21, c=x1 - .08, x1=x1)


OVAL = "0.52,0.86 0.40,0.99 0.20,0.95 0.06,0.72 0.03,0.40 0.10,0.12 0.26,0.00 0.44,0.06 0.56,0.28"

G = {}


def g(ch, s, x=(), e=(0.35, 1.0), j=True, a=None, lead=True):
    G.setdefault(ch, []).append({"s": s, "x": list(x), "e": e, "j": j, "a": a, "lead": lead})


# lowercase -----------------------------------------------------------------------------------------------
g("a", [OVAL, _turn(0.60)], e=(1.0, 0.12))
g("a", ["0.54,0.84 0.44,0.98 0.22,0.96 0.07,0.74 0.04,0.38 0.12,0.10 0.28,0.00 0.46,0.08 0.58,0.30", _turn(0.61)], e=(1.0, 0.12))
g("b", [LOOP + " 0.12,0.0", "0.12,0.46 0.22,0.84 0.38,1.00 0.54,0.92 0.60,0.62 0.55,0.26 0.40,0.03 0.24,0.00 0.13,0.08"], e=(0.5, 1.0), j=False)
g("b", [PLAIN + " 0.12,0.0", "0.12,0.46 0.22,0.84 0.38,1.00 0.54,0.92 0.60,0.62 0.55,0.26 0.40,0.03 0.24,0.00 0.13,0.08"], e=(0.4, 1.0), j=False)
g("c", ["0.40,0.82 0.50,0.92 0.42,1.00 0.24,0.96 0.08,0.72 0.04,0.38 0.12,0.10 0.28,0.00 0.44,0.04 0.58,0.18"], e=(1.0, 0.12))
g("c", ["0.46,0.88 0.36,1.00 0.18,0.92 0.05,0.64 0.05,0.30 0.15,0.07 0.31,0.00 0.47,0.05 0.59,0.19"], e=(1.0, 0.12))
g("d", [OVAL, _turn(0.60, 1.82)], e=(1.0, 0.12))
g("d", [OVAL, "0.36,1.62 0.50,1.80 0.62,1.82 0.62,1.60 " + _turn(0.60, 1.2)[10:]], e=(1.0, 0.12))
g("e", ["0.05,0.36 0.30,0.50 0.47,0.72 0.45,0.93 0.31,0.99 0.13,0.84 0.04,0.52 0.07,0.18 0.21,0.01 0.40,0.02 0.56,0.17"], e=(1.0, 0.45))
g("e", ["0.05,0.40 0.28,0.52 0.44,0.74 0.42,0.94 0.28,0.98 0.12,0.82 0.05,0.50 0.08,0.17 0.22,0.01 0.41,0.03 0.57,0.19"], e=(1.0, 0.35))
g("g", [OVAL, "0.62,1.00 0.60,0.10 0.58,-0.40 0.48,-0.70 0.32,-0.78 0.20,-0.66 0.28,-0.42 0.50,-0.16 0.72,0.04 0.86,0.18"], e=(1.0, 0.12))
g("g", [OVAL, "0.62,1.00 0.60,0.10 0.57,-0.42 0.46,-0.72 0.28,-0.76 0.16,-0.62 0.30,-0.36 0.56,-0.12 0.76,0.06 0.88,0.20"], e=(1.0, 0.12))
g("h", [LOOP + " 0.12,0.0", _arch(0.12, 0.62) + " " + _turn(0.62, 0.40)[10:]], e=(0.5, 1.0))
g("h", [PLAIN + " 0.12,0.0", _arch(0.12, 0.62) + " " + _turn(0.62, 0.40)[10:]], e=(0.4, 1.0))
g("i", [_turn(0.12)], x=["0.20,1.42 0.17,1.30"], e=(0.35, 1.0))
g("i", [_turn(0.12)], x=["0.21,1.40 0.16,1.31"], e=(0.25, 1.0))
g("j", ["0.14,1.00 0.12,0.10 0.10,-0.40 0.02,-0.70 -0.12,-0.78 -0.22,-0.66 -0.10,-0.40 0.12,-0.14 0.32,0.04 0.46,0.18"],
  x=["0.22,1.42 0.19,1.30"], e=(0.35, 1.0))
g("k", [LOOP + " 0.12,0.0", "0.12,0.42 0.24,0.82 0.40,0.99 0.52,0.92 0.46,0.70 0.24,0.54 0.40,0.50 0.50,0.32 0.51,0.10 0.59,0.00 0.71,0.04 0.82,0.16"], e=(0.5, 1.0))
g("k", [PLAIN + " 0.12,0.0", "0.12,0.42 0.24,0.82 0.40,0.99 0.52,0.92 0.46,0.70 0.24,0.54 0.40,0.50 0.50,0.32 0.51,0.10 0.59,0.00 0.71,0.04 0.82,0.16"], e=(0.4, 1.0))
g("l", [LOOP + " 0.12,0.30 0.13,0.10 0.21,0.00 0.32,0.03 0.43,0.16"], e=(0.5, 1.0))
g("l", [PLAIN + " 0.12,0.30 0.13,0.10 0.21,0.00 0.32,0.03 0.43,0.16"], e=(0.4, 1.0))
g("m", ["0.12,1.00 0.12,0.0", _arch(0.12, 0.56) + " 0.56,0.0", _arch(0.56, 1.00) + " " + _turn(1.0, 0.40)[10:]], e=(0.3, 1.0))
g("n", ["0.12,1.00 0.12,0.0", _arch(0.12, 0.62) + " " + _turn(0.62, 0.40)[10:]], e=(0.3, 1.0))
g("n", ["0.13,1.00 0.12,0.0", "0.12,0.48 0.18,0.82 0.34,1.00 0.52,0.96 0.60,0.72 " + _turn(0.61, 0.40)[10:]], e=(0.3, 1.0))
g("o", ["0.48,0.95 0.32,1.00 0.14,0.89 0.04,0.58 0.07,0.22 0.21,0.02 0.38,0.01 0.52,0.17 0.58,0.50 0.55,0.80 0.47,0.96", "h:0.47,0.96 0.60,0.90 0.76,0.88"], e=(1.0, 0.12))
g("o", ["0.50,0.93 0.34,1.00 0.15,0.90 0.05,0.60 0.06,0.24 0.19,0.03 0.37,0.00 0.52,0.15 0.59,0.48 0.56,0.80 0.48,0.95", "h:0.48,0.95 0.62,0.92 0.78,0.92"], e=(1.0, 0.12))
g("p", ["0.14,1.00 0.12,-0.78", "0.13,0.42 0.22,0.82 0.38,0.99 0.54,0.92 0.60,0.62 0.55,0.26 0.40,0.03 0.24,0.02 0.14,0.12"], e=(0.3, 1.0), j=False)
g("q", [OVAL, "0.62,1.00 0.60,0.0 0.58,-0.78"], e=(1.0, 0.12), j=False)
g("r", ["0.12,1.00 0.12,0.0", "0.12,0.44 0.20,0.80 0.34,0.98 0.48,0.98 0.56,0.88"], e=(0.3, 1.0))
g("r", ["0.10,1.00 0.12,0.0", "0.12,0.50 0.22,0.86 0.36,1.00 0.50,0.97 0.57,0.86"], e=(0.3, 1.0))
g("s", ["0.52,0.84 0.44,0.98 0.24,0.98 0.12,0.82 0.18,0.64 0.38,0.50 0.52,0.30 0.46,0.08 0.26,0.00 0.08,0.08"], e=(0.5, 1.0), j=False)
g("f", [LOOP + " 0.12,0.0 0.11,-0.48 0.15,-0.72 0.25,-0.74 0.29,-0.56 0.21,-0.28 0.12,-0.02 0.26,0.08 0.40,0.18"],
  x=["m:-0.04,0.98 0.20,1.00 0.42,1.02"], e=(0.5, 1.0))
g("f", ["0.56,1.62 0.48,1.80 0.32,1.84 0.20,1.68 0.16,1.30 0.14,0.50 0.12,-0.30 0.06,-0.66 -0.06,-0.76 -0.14,-0.66"],
  x=["m:-0.04,0.98 0.20,1.00 0.42,1.02"], e=(0.4, 1.0), j=False)
g("s", ["0.50,0.82 0.42,0.98 0.22,0.96 0.12,0.78 0.22,0.60 0.42,0.46 0.52,0.26 0.42,0.05 0.22,0.00 0.06,0.10"], e=(0.5, 1.0), j=False)
g("t", ["0.16,1.48 " + _turn(0.12)[10:]], x=["h:-0.04,0.96 0.20,1.00 0.40,1.02"], e=(0.25, 1.0))
g("t", ["0.17,1.42 " + _turn(0.12)[10:]], x=["h:0.00,0.98 0.22,1.00 0.40,0.99"], e=(0.25, 1.0))
g("u", ["0.12,1.00 0.12,0.30 0.14,0.09 0.24,0.00 0.38,0.06 0.50,0.30 0.56,0.62 0.60,1.00", _turn(0.60)], e=(0.3, 1.0))
g("v", ["0.06,1.00 0.18,0.62 0.28,0.22 0.32,0.0", "0.32,0.0 0.42,0.30 0.53,0.68 0.57,0.96", "h:0.57,0.96 0.66,0.90 0.80,0.90"], e=(0.3, 1.0))
g("w", ["0.06,1.00 0.16,0.50 0.22,0.0", "h:0.22,0.0 0.32,0.40 0.42,0.86", "0.42,0.86 0.48,0.40 0.54,0.0",
        "0.54,0.0 0.64,0.30 0.74,0.68 0.78,0.96", "h:0.78,0.96 0.88,0.90 1.02,0.90"], e=(0.3, 1.0))
g("x", ["0.04,0.84 0.14,0.98 0.24,0.92 0.32,0.60 0.40,0.22 0.48,0.03 0.60,0.04 0.69,0.17"], x=["h:0.58,0.98 0.34,0.50 0.06,0.02"], e=(0.5, 1.0))
g("y", ["0.12,1.00 0.12,0.30 0.14,0.09 0.24,0.00 0.38,0.06 0.50,0.30 0.56,0.62 0.60,1.00",
        "0.60,1.00 0.58,0.10 0.56,-0.40 0.46,-0.70 0.30,-0.78 0.18,-0.66 0.26,-0.42 0.48,-0.16 0.70,0.04 0.84,0.18"], e=(0.3, 1.0))
g("z", ["h:0.06,0.86 0.20,0.99 0.40,0.97 0.56,0.98", "0.56,0.98 0.30,0.50 0.04,0.02", "h:0.04,0.02 0.24,0.07 0.40,-0.01 0.58,0.07"], e=(0.4, 1.0))

# capitals: roman in structure, so a word in capitals still reads ----------------------------------------
C = 1.72
g("A", ["h:-0.06,0.12 0.06,0.02 0.18,0.18 0.42,1.10 0.58,1.72", "0.58,1.72 0.66,0.80 0.70,0.24 0.74,0.04 0.85,0.00 0.97,0.10"],
  x=["h:0.24,0.64 0.48,0.68 0.72,0.68"], e=(1, 0.3), lead=False)
g("B", ["h:0.00,1.44 0.14,1.66 0.36,1.74", "0.34,1.72 0.28,0.80 0.22,0.0",
        "h:0.34,1.72 0.62,1.74 0.82,1.58 0.80,1.30 0.62,1.04 0.36,0.94",
        "0.36,0.94 0.62,0.90 0.84,0.70 0.86,0.36 0.70,0.08 0.44,0.00 0.18,0.02 0.06,0.12"], j=False, lead=False)
g("C", ["0.78,1.42 0.84,1.60 0.70,1.72 0.44,1.66 0.20,1.38 0.06,0.92 0.06,0.42 0.20,0.10 0.44,0.00 0.68,0.08 0.84,0.22"], lead=False)
g("D", ["0.38,1.70 0.32,0.80 0.26,0.08", "h:0.02,1.40 0.18,1.66 0.42,1.74 0.72,1.68 0.92,1.38 0.94,0.90 0.82,0.40 0.60,0.08 0.32,0.00 0.10,0.04 0.04,0.16 0.16,0.20"],
  j=False, lead=False)
g("E", ["0.60,1.46 0.62,1.64 0.48,1.73 0.28,1.66 0.22,1.44 0.32,1.18 0.52,1.02",
        "0.52,1.02 0.26,0.92 0.08,0.64 0.08,0.30 0.22,0.06 0.46,0.00 0.70,0.08 0.84,0.22"], lead=False)
g("F", ["0.50,1.70 0.44,0.80 0.40,0.0"], x=["m:0.14,1.62 0.30,1.70 0.60,1.71 0.96,1.76", "m:0.24,0.86 0.50,0.88 0.78,0.92"], j=False, lead=False, a=0.80)
g("G", ["0.78,1.42 0.84,1.60 0.70,1.72 0.44,1.66 0.20,1.38 0.06,0.92 0.06,0.42 0.20,0.10 0.44,0.00 0.64,0.06 0.76,0.24", "0.80,0.80 0.78,0.40 0.74,0.0"],
  x=["m:0.48,0.78 0.70,0.80 0.94,0.82"], j=False, lead=False)
g("H", ["h:-0.04,1.40 0.12,1.66 0.32,1.72", "0.32,1.72 0.26,0.80 0.20,0.10 0.08,0.00 -0.02,0.08",
        "0.88,1.72 0.82,0.80 0.78,0.20 0.82,0.04 0.93,0.00 1.04,0.10"], x=["h:0.10,0.80 0.50,0.86 0.84,0.90"], lead=False)
g("I", ["0.50,1.72 0.38,0.0"], x=["m:0.18,1.70 0.48,1.72 0.80,1.74", "m:0.06,0.00 0.38,0.01 0.68,0.03"], j=False, lead=False)
g("J", ["0.60,1.72 0.54,0.60 0.48,0.00 0.36,-0.42 0.16,-0.58 0.02,-0.46"], x=["h:0.30,1.70 0.60,1.73 0.84,1.74"], j=False, lead=False)
g("K", ["h:-0.04,1.40 0.12,1.66 0.32,1.72", "0.32,1.72 0.26,0.80 0.20,0.0",
        "h:0.90,1.72 0.62,1.20 0.28,0.84", "0.28,0.84 0.52,0.82 0.64,0.50 0.70,0.16 0.80,0.02 0.94,0.06"], lead=False)
g("L", ["0.60,1.54 0.66,1.72 0.56,1.80 0.42,1.70 0.38,1.30 0.32,0.60 0.22,0.12 0.08,0.00 0.02,0.10 0.16,0.17 0.40,0.07 0.62,0.00 0.84,0.08"], lead=False)
g("M", ["h:-0.04,0.02 0.06,0.30 0.18,1.20 0.24,1.72", "0.24,1.72 0.38,0.80 0.50,0.0", "h:0.50,0.0 0.72,0.80 0.92,1.72",
        "0.92,1.72 0.88,0.80 0.86,0.24 0.89,0.04 1.00,0.00 1.10,0.10"], lead=False)
g("N", ["h:-0.04,0.02 0.06,0.30 0.16,1.20 0.22,1.72", "0.22,1.72 0.48,0.80 0.72,0.0", "h:0.72,0.0 0.82,0.90 0.88,1.60 0.96,1.76 1.04,1.72"],
  j=False, lead=False)
g("O", ["0.52,1.62 0.34,1.72 0.14,1.52 0.04,1.04 0.06,0.44 0.22,0.06 0.44,0.00 0.66,0.20 0.78,0.70 0.76,1.24 0.62,1.60 0.46,1.66 0.42,1.50"],
  j=False, lead=False)
g("P", ["h:0.00,1.42 0.16,1.68 0.38,1.74", "0.38,1.72 0.32,0.80 0.26,0.0", "h:0.38,1.72 0.66,1.74 0.86,1.56 0.84,1.22 0.62,0.96 0.34,0.88"],
  j=False, lead=False)
g("Q", ["0.52,1.62 0.34,1.72 0.14,1.52 0.04,1.04 0.06,0.44 0.22,0.06 0.44,0.00 0.66,0.20 0.78,0.70 0.76,1.24 0.62,1.60 0.46,1.66 0.42,1.50"],
  x=["m:0.34,0.14 0.56,-0.06 0.92,-0.06"], j=False, lead=False)
g("R", ["h:0.00,1.42 0.16,1.68 0.38,1.74", "0.38,1.72 0.32,0.80 0.26,0.0",
        "h:0.38,1.72 0.66,1.74 0.86,1.56 0.84,1.22 0.62,0.96 0.34,0.88",
        "0.36,0.88 0.56,0.82 0.66,0.46 0.70,0.14 0.80,0.00 0.94,0.08"], lead=False)
g("S", ["0.76,1.48 0.70,1.68 0.50,1.74 0.28,1.62 0.22,1.36 0.38,1.04 0.58,0.74 0.64,0.40 0.54,0.10 0.30,0.00 0.10,0.06 0.04,0.22"], j=False, lead=False)
g("T", ["0.56,1.68 0.50,0.90 0.46,0.0"], x=["m:-0.02,1.58 0.10,1.68 0.50,1.70 1.02,1.76"], j=False, lead=False, a=0.74)
g("T", ["0.58,1.66 0.52,0.90 0.47,0.06 0.52,0.00 0.62,0.04"], x=["m:0.00,1.52 0.12,1.70 0.54,1.68 1.00,1.74"], j=False, lead=False, a=0.74)
g("U", ["h:-0.04,1.42 0.12,1.66 0.30,1.72", "0.30,1.72 0.24,0.80 0.22,0.30 0.32,0.04 0.50,0.00 0.66,0.14 0.80,0.60 0.88,1.72",
        "0.88,1.72 0.82,0.60 0.80,0.20 0.85,0.02 0.96,0.00 1.06,0.10"], lead=False)
g("V", ["h:-0.04,1.42 0.12,1.66 0.28,1.72", "0.28,1.72 0.36,0.90 0.44,0.0", "h:0.44,0.0 0.70,0.90 0.88,1.60 0.96,1.74 1.04,1.70"],
  j=False, lead=False)
g("W", ["h:-0.04,1.42 0.10,1.66 0.24,1.72", "0.24,1.72 0.30,0.80 0.34,0.0", "h:0.34,0.0 0.50,0.80 0.60,1.40", "0.60,1.40 0.64,0.70 0.70,0.0",
        "h:0.70,0.0 0.92,0.90 1.06,1.60 1.14,1.74 1.22,1.70"], j=False, lead=False)
g("X", ["0.08,1.70 0.20,1.72 0.30,1.50 0.50,0.60 0.62,0.10 0.72,0.00 0.86,0.08"], x=["h:0.86,1.72 0.44,0.86 0.02,0.0"], lead=False)
g("Y", ["0.06,1.70 0.18,1.72 0.30,1.40 0.46,0.88", "0.46,0.88 0.40,0.0"], x=["h:0.94,1.72 0.70,1.30 0.46,0.88"], j=False, lead=False)
g("Z", ["h:0.10,1.50 0.26,1.70 0.84,1.72", "0.84,1.72 0.42,0.84 0.02,0.0", "h:0.02,0.0 0.40,0.06 0.80,0.00 0.96,0.10"], lead=False)
# second hands of the capitals that open headlines most
g("S", ["0.74,1.52 0.72,1.70 0.52,1.74 0.30,1.64 0.24,1.40 0.40,1.08 0.60,0.76 0.66,0.40 0.56,0.10 0.32,0.00 0.10,0.08 0.06,0.26 0.18,0.30"], j=False, lead=False)
g("A", ["h:-0.04,0.10 0.08,0.02 0.20,0.20 0.42,1.10 0.56,1.72", "0.56,1.72 0.64,0.80 0.68,0.24 0.72,0.04 0.83,0.00 0.95,0.10"],
  x=["h:0.20,0.70 0.46,0.64 0.74,0.70"], e=(1, 0.3), lead=False)
g("M", ["h:-0.06,0.10 0.04,0.02 0.12,0.40 0.20,1.20 0.24,1.72", "0.24,1.72 0.38,0.80 0.50,0.0", "h:0.50,0.0 0.72,0.80 0.92,1.72",
        "0.92,1.72 0.88,0.80 0.86,0.24 0.89,0.04 1.00,0.00 1.10,0.10"], lead=False)
g("W", ["0.24,1.72 0.30,0.80 0.34,0.0", "h:0.34,0.0 0.50,0.80 0.60,1.40", "0.60,1.40 0.64,0.70 0.70,0.0",
        "h:0.70,0.0 0.92,0.90 1.04,1.60 1.12,1.74"], x=["h:0.00,1.52 0.10,1.70 0.24,1.72"], j=False, lead=False)

# figures (lining, a little under cap height) -------------------------------------------------------------
N = 1.42
g("0", ["0.48,1.32 0.36,1.42 0.18,1.32 0.06,0.96 0.06,0.40 0.16,0.06 0.32,0.00 0.48,0.12 0.58,0.50 0.58,1.04 0.48,1.32"], j=False, lead=False)
g("1", ["h:0.02,1.06 0.20,1.30 0.40,1.42", "0.40,1.42 0.34,0.70 0.28,0.0"], j=False, lead=False, a=0.52)
g("2", ["0.04,1.10 0.14,1.34 0.34,1.42 0.52,1.32 0.54,1.08 0.36,0.72 0.04,0.04", "h:0.04,0.04 0.24,0.08 0.44,0.00 0.62,0.06"], j=False, lead=False)
g("3", ["h:0.06,1.24 0.22,1.40 0.44,1.40 0.54,1.20", "0.54,1.20 0.42,0.92 0.22,0.82", "h:0.22,0.82 0.42,0.80",
        "0.42,0.80 0.58,0.56 0.56,0.20 0.38,0.00 0.16,0.02 0.04,0.14"], j=False, lead=False)
g("4", ["h:0.48,1.42 0.20,0.86 0.00,0.42", "h:0.00,0.42 0.34,0.43 0.68,0.46", "0.52,1.10 0.48,0.50 0.44,0.0"], j=False, lead=False)
g("5", ["h:0.64,1.42 0.42,1.40 0.22,1.42", "0.22,1.42 0.18,1.10 0.14,0.84", "h:0.14,0.84 0.34,0.90",
        "0.34,0.90 0.56,0.70 0.58,0.28 0.40,0.02 0.18,0.00 0.04,0.14"], j=False, lead=False)
g("6", ["0.54,1.38 0.34,1.28 0.14,0.96 0.06,0.48 0.14,0.08 0.32,0.00 0.50,0.12 0.56,0.42 0.44,0.66 0.24,0.64 0.12,0.44"], j=False, lead=False)
g("7", ["h:0.04,1.30 0.20,1.42 0.44,1.40 0.68,1.42", "0.68,1.42 0.44,0.80 0.24,0.0"], j=False, lead=False)
g("8", ["0.52,1.18 0.42,1.40 0.22,1.40 0.14,1.16 0.32,0.86 0.54,0.56 0.52,0.14 0.32,0.00 0.10,0.10 0.08,0.38 0.30,0.70 0.50,0.98 0.52,1.18"],
  j=False, lead=False)
g("9", ["0.54,1.00 0.40,0.78 0.20,0.80 0.08,1.04 0.18,1.36 0.38,1.42 0.56,1.28 0.56,0.90 0.46,0.32 0.30,0.02 0.08,0.06"], j=False, lead=False)

# punctuation ---------------------------------------------------------------------------------------------
DOT = "0.10,0.12 0.06,0.02"
g(".", [DOT], j=False, lead=False, a=0.20)
g(",", ["0.12,0.12 0.09,0.00 0.02,-0.20"], j=False, lead=False, a=0.20)
g(":", [DOT], x=["0.14,0.84 0.10,0.74"], j=False, lead=False, a=0.24)
g(";", ["0.12,0.12 0.09,0.00 0.02,-0.20"], x=["0.16,0.84 0.12,0.74"], j=False, lead=False, a=0.24)
g("!", ["0.30,1.74 0.22,1.10 0.14,0.42"], x=[DOT], j=False, lead=False, a=0.36)
g("?", ["h:0.04,1.36 0.16,1.66 0.40,1.74 0.56,1.54 0.48,1.24", "0.48,1.24 0.30,1.00 0.22,0.72 0.20,0.44"], x=["0.18,0.12 0.14,0.02"],
  j=False, lead=False, a=0.62)
RQ = "0.30,1.80 0.26,1.66 0.16,1.48"
LQ = "0.18,1.48 0.26,1.66 0.30,1.80"
g("'", [RQ], j=False, lead=False, a=0.32)
g("’", [RQ], j=False, lead=False, a=0.32)
g("‘", ["0.24,1.50 0.20,1.62 0.24,1.80"], j=False, lead=False, a=0.32)
g('"', ["0.30,1.80 0.24,1.50"], x=["0.50,1.80 0.44,1.50"], j=False, lead=False, a=0.54)
g("”", [RQ], x=["0.52,1.80 0.48,1.66 0.38,1.48"], j=False, lead=False, a=0.54)
g("“", ["0.24,1.50 0.20,1.62 0.24,1.80"], x=["0.46,1.50 0.42,1.62 0.46,1.80"], j=False, lead=False, a=0.54)
g("-", ["m:0.04,0.46 0.24,0.50 0.42,0.52"], j=False, lead=False, a=0.46)
g("‐", ["m:0.04,0.46 0.24,0.50 0.42,0.52"], j=False, lead=False, a=0.46)
g("–", ["m:0.04,0.48 0.34,0.50 0.66,0.52"], j=False, lead=False, a=0.72)
g("—", ["m:0.04,0.48 0.50,0.50 0.98,0.52"], j=False, lead=False, a=1.04)
g("&", ["0.88,0.30 0.66,0.04 0.40,0.00 0.14,0.08 0.06,0.36 0.24,0.66 0.52,0.94 0.62,1.24 0.52,1.46 0.34,1.44 0.28,1.20 0.40,0.84 0.62,0.42 0.82,0.10 0.96,0.02 1.06,0.10"],
  j=False, lead=False)
g("(", ["0.54,1.80 0.30,1.40 0.14,0.70 0.20,0.00 0.36,-0.40"], j=False, lead=False, a=0.50)
g(")", ["h:0.10,1.80 0.28,1.40", "0.28,1.40 0.38,0.70 0.26,0.00 0.02,-0.40"], j=False, lead=False, a=0.50)
g("/", ["0.76,1.80 0.40,0.70 0.04,-0.30"], j=False, lead=False, a=0.74)
g("%", ["0.82,1.42 0.40,0.70 0.02,0.00", "0.30,1.40 0.14,1.34 0.10,1.10 0.24,0.98 0.38,1.10 0.36,1.32 0.30,1.40",
        "0.78,0.44 0.62,0.38 0.58,0.14 0.72,0.02 0.86,0.14 0.84,0.36 0.78,0.44"], j=False, lead=False)
g("$", ["0.66,1.20 0.58,1.36 0.38,1.40 0.20,1.28 0.20,1.04 0.40,0.82 0.58,0.56 0.58,0.24 0.40,0.04 0.18,0.04 0.04,0.18"],
  x=["h:0.44,1.62 0.34,-0.20"], j=False, lead=False)
g("#", ["h:0.08,0.98 0.44,1.00 0.80,1.02", "h:0.00,0.46 0.36,0.48 0.72,0.50"], x=["0.40,1.40 0.26,0.06", "0.70,1.40 0.56,0.06"], j=False, lead=False)
g("+", ["h:0.06,0.60 0.36,0.62 0.66,0.64"], x=["0.40,0.96 0.32,0.28"], j=False, lead=False)
g("=", ["h:0.06,0.80 0.36,0.82 0.66,0.84"], x=["h:0.04,0.44 0.34,0.46 0.64,0.48"], j=False, lead=False)
g("·", ["0.16,0.58 0.12,0.48"], j=False, lead=False, a=0.30)
g("•", ["0.18,0.64 0.12,0.42"], j=False, lead=False, a=0.34)
g("…", [DOT], x=["0.34,0.12 0.30,0.02", "0.58,0.12 0.54,0.02"], j=False, lead=False, a=0.70)
g("@", ["0.62,0.84 0.42,0.90 0.30,0.66 0.36,0.40 0.54,0.44 0.64,0.80 0.66,0.44 0.82,0.42 0.92,0.80 0.80,1.22 0.52,1.36 0.22,1.24 0.06,0.84 0.12,0.34 0.38,0.06 0.70,0.06"],
  j=False, lead=False)
g("°", ["0.26,1.62 0.14,1.56 0.12,1.40 0.24,1.32 0.36,1.40 0.34,1.56 0.26,1.62"], j=False, lead=False, a=0.42)
g("*", ["0.30,1.70 0.26,1.20"], x=["h:0.04,1.50 0.50,1.40", "h:0.08,1.30 0.48,1.60"], j=False, lead=False, a=0.54)

# marks over and under (composed: NFD) -------------------------------------------------------------------
MARKS = {"́": "0.30,1.40 0.20,1.22", "̀": "0.14,1.40 0.22,1.22", "̂": "h:0.06,1.22 0.18,1.40 0.30,1.22",
         "̃": "h:0.02,1.26 0.10,1.36 0.22,1.30 0.34,1.36", "̈": "0.12,1.36 0.10,1.26|0.34,1.36 0.32,1.26",
         "̊": "h:0.20,1.44 0.12,1.36 0.18,1.26 0.28,1.32 0.24,1.44", "̌": "h:0.06,1.40 0.18,1.22 0.30,1.40",
         "̧": "h:0.20,0.0 0.26,-0.14 0.16,-0.24 0.06,-0.22", "̄": "h:0.04,1.30 0.34,1.32"}

ALIAS = {"′": "'", "″": '"', " ": " ", " ": " ", " ": " ", "−": "–", "‑": "-",
         "«": '"', "»": '"', "‹": "'", "›": "'", "|": "/", "×": "x", "ı": "i"}


# ---------------------------------------------------------------- geometry

def _pts(s):
    p = 1.0
    if s[:2] in ("h:", "m:"):
        p = 0.0 if s[0] == "h" else 0.5
        s = s[2:]
    return [tuple(float(v) for v in t.split(",")) for t in s.split()], p


def _spline(P, step=0.035):
    """A smooth path through the points (centripetal Catmull-Rom), sampled about every `step` units."""
    if len(P) < 2:
        return list(P)
    if len(P) == 2:
        (x0, y0), (x1, y1) = P
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / step) + 1)
        return [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n + 1)]
    ext = [(2 * P[0][0] - P[1][0], 2 * P[0][1] - P[1][1])] + list(P) + [(2 * P[-1][0] - P[-2][0], 2 * P[-1][1] - P[-2][1])]
    out = [P[0]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]

        def tj(ti, a, b):
            return ti + max(math.hypot(b[0] - a[0], b[1] - a[1]), 1e-6) ** 0.5
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        n = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step) + 1)
        for k in range(1, n + 1):
            t = t1 + (t2 - t1) * k / n
            pt = []
            for d in (0, 1):
                a1 = (t1 - t) / (t1 - t0) * p0[d] + (t - t0) / (t1 - t0) * p1[d]
                a2 = (t2 - t) / (t2 - t1) * p1[d] + (t - t1) / (t2 - t1) * p2[d]
                a3 = (t3 - t) / (t3 - t2) * p2[d] + (t - t2) / (t3 - t2) * p3[d]
                b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
                b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
                pt.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
            out.append(tuple(pt))
    return out


def _bezier(p0, p1, p2, p3, n):
    out = []
    for k in range(n + 1):
        t = k / n
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def _unit(dx, dy):
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


class _Pen:
    """A pointed pen on a slant: strokes are sampled paths with a pressure; ink() turns them into outlines."""

    def __init__(self, slant, heavy, hair):
        self.ax = (math.sin(slant), math.cos(slant))   # the slant axis, pointing up
        self.heavy, self.hair = heavy, hair
        self.strokes = []   # (points, widths)

    def stroke(self, pts, pressure=1.0, taper=True):
        if len(pts) < 2:
            return
        ws = []
        n = len(pts)
        for i in range(n):
            a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
            tx, ty = _unit(b[0] - a[0], b[1] - a[1])
            s = max(0.0, -(tx * self.ax[0] + ty * self.ax[1]))
            ws.append(self.hair + (self.heavy - self.hair) * pressure * s ** 1.7)
        ws = [(ws[max(0, i - 1)] + 2 * ws[i] + ws[min(n - 1, i + 1)]) / 4 for i in range(n)]
        if taper and n > 4:   # a shaded stroke swells in and out of its ends: it is not cut off square
            L = 0.0
            acc = [0.0]
            for i in range(1, n):
                L += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
                acc.append(L)
            r = self.heavy * 1.1
            for i in range(n):
                k = min(1.0, acc[i] / r, (L - acc[i]) / r) if L > 2 * r else 1.0
                ws[i] = self.hair + (ws[i] - self.hair) * (0.55 + 0.45 * k)
        self.strokes.append((pts, ws))

    def shaped(self, pts, ws):
        self.strokes.append((pts, ws))


def _outline(pts, ws):
    """The filled outline of one stroke: both sides of the pen, with round ends; counter-clockwise."""
    n = len(pts)
    L, R = [], []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tx, ty = _unit(b[0] - a[0], b[1] - a[1])
        nx, ny = -ty, tx
        h = ws[i] / 2
        L.append((pts[i][0] + nx * h, pts[i][1] + ny * h))
        R.append((pts[i][0] - nx * h, pts[i][1] - ny * h))

    return L + _arc(pts[-1], pts[-2], ws[-1]) + R[::-1] + _arc(pts[0], pts[1], ws[0])


def _arc(p, q, w):
    """Half a circle round the end point p of a stroke (q its neighbour), from one side of the pen to the other."""
    tx, ty = _unit(p[0] - q[0], p[1] - q[1])
    nx, ny = -ty, tx
    out = []
    for k in range(1, 6):
        t = math.pi * k / 6
        c, s = math.cos(t), math.sin(t)
        # t points away from the stroke; at the end n is the stroke's left, at the start its right
        out.append((p[0] + (nx * c + tx * s) * w / 2, p[1] + (ny * c + ty * s) * w / 2))
    return out


def _area(poly):
    return sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly))) / 2


def _simplify(poly, tol):
    """Douglas-Peucker on a closed outline."""
    if len(poly) < 8:
        return poly

    def rdp(P):
        if len(P) < 3:
            return P
        (x0, y0), (x1, y1) = P[0], P[-1]
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy)
        best, idx = -1.0, 0
        for i in range(1, len(P) - 1):
            x, y = P[i]
            dist = abs(dy * x - dx * y + x1 * y0 - y1 * x0) / d if d > 1e-9 else math.hypot(x - x0, y - y0)
            if dist > best:
                best, idx = dist, i
        if best <= tol:
            return [P[0], P[-1]]
        return rdp(P[:idx + 1])[:-1] + rdp(P[idx:])
    h = len(poly) // 2
    return rdp(poly[:h + 1])[:-1] + rdp(poly[h:] + [poly[0]])[:-1]


# ---------------------------------------------------------------- composing

def _hash(text, seed):
    return int(hashlib.sha1(f"{seed}\x00{text}".encode("utf-8")).hexdigest()[:12], 16)


class _Hand:
    """One headline's hand: everything that is not fixed, drawn once from the headline's own seed."""

    def __init__(self, rng):
        self.rng = rng
        self.slant = math.radians(rng.uniform(16.0, 21.0))
        self.wide = rng.uniform(1.08, 1.18)
        self.heavy = rng.uniform(0.21, 0.25)
        self.hair = rng.uniform(0.050, 0.062)
        self.asc = rng.uniform(0.86, 1.0)      # ascender / cap scale above the x-height
        self.desc = rng.uniform(0.86, 1.0)
        self.track = rng.uniform(0.09, 0.14)
        self.space = rng.uniform(0.66, 0.76)
        self.tremor = rng.uniform(0.006, 0.013)
        self.wave = (rng.uniform(0.008, 0.02), rng.uniform(2.2, 4.5), rng.uniform(0, 6.28))
        self.lead = rng.choice(["short", "short", "long"])
        self.flick = rng.random() < 0.6
        self.last = {}

    def pick(self, ch):
        alts = G[ch]
        if len(alts) == 1:
            return alts[0]
        prev = self.last.get(ch)
        choices = [a for a in range(len(alts)) if a != prev] if prev is not None and self.rng.random() < 0.8 else range(len(alts))
        k = self.rng.choice(list(choices))
        self.last[ch] = k
        return alts[k]

    def warp(self, x, y):
        if y > 1.0:
            y = 1.0 + (y - 1.0) * self.asc
        elif y < 0.0:
            y = y * self.desc
        return x * self.wide, y


def _glyphs(text):
    """The text as (char, marks) units, or Unsupported."""
    out = []
    for ch in text:
        ch = ALIAS.get(ch, ch)
        if ch in G or ch == " ":
            out.append((ch, []))
            continue
        d = unicodedata.normalize("NFD", ch)
        base, marks = d[0], [m for m in d[1:]]
        base = ALIAS.get(base, base)
        if base in G and all(m in MARKS for m in marks):
            out.append((base, marks))
            continue
        if ch in "        ":
            out.append((" ", []))
            continue
        raise Unsupported(f"no letter for {ch!r}")
    return out


def _word_units(text):
    words, cur = [], []
    for u in _glyphs(text):
        if u[0] == " ":
            if cur:
                words.append(cur)
                cur = []
        else:
            cur.append(u)
    if cur:
        words.append(cur)
    return words


def _set_word(hand, word, x0, final):
    """Lay out one word from pen position x0 (units, upright): returns (strokes, x_end).
    strokes: [(points, pressure, taper)] in upright units, before the slant."""
    rng = hand.rng
    out = []
    x = x0
    prev_exit = None   # (point, direction) when the previous letter joins out
    jit = hand.tremor

    def J(p):
        return (p[0] + rng.uniform(-jit, jit), p[1] + rng.uniform(-jit, jit))

    for n, (ch, marks) in enumerate(word):
        gl = hand.pick(ch)
        lower = ch.isalpha() and ch.islower()
        strokes = []
        maxx = 0.0
        for k, s in enumerate(gl["s"] + gl["x"]):
            for part in s.split("|"):
                P, pr = _pts(part)
                P = _spline([hand.warp(*J(p)) for p in P])
                maxx = max([maxx] + [p[0] for p in P]) if k < len(gl["s"]) else maxx
                strokes.append((P, pr, k < len(gl["s"])))
        adv = (gl["a"] * hand.wide if gl["a"] is not None else maxx + 0.06) + hand.track
        if n and word[n - 1][0].isupper() and not G[word[n - 1][0]][0]["j"]:
            x += 0.08   # a little air after a capital that does not join
        if ch in ".,:;!?'’”\"" and n:
            x -= hand.track + 0.02   # punctuation sits close to its word
        placed = [([(p[0] + x, p[1]) for p in P], pr, main) for P, pr, main in strokes]
        chain = [s for s in placed if s[2]]
        entry = chain[0][0][0]
        edir = _unit(gl["e"][0], gl["e"][1])
        if prev_exit is not None and lower:
            (px, py), (dx, dy) = prev_exit
            dist = math.hypot(entry[0] - px, entry[1] - py)
            k = 0.42 * dist
            pts = _bezier((px, py), (px + dx * k, py + dy * k), (entry[0] - edir[0] * k, entry[1] - edir[1] * k), entry,
                          max(4, int(dist / 0.035)))
            out.append((pts, 0.0, False))
        elif lower and gl["lead"] and gl["e"][1] > 0.3 and not (n and word[n - 1][0].isupper()):
            # a word's lead-in: a hairline from the baseline into the first stroke (shorter inside a word)
            ln = (0.30 if hand.lead == "short" else 0.42) if n == 0 else 0.20
            sx, sy = entry[0] - ln - 0.05 * entry[1], max(0.0, min(entry[1] - 0.55, 0.1))
            if entry[1] < 0.6:
                sx, sy = entry[0] - ln * 0.8, 0.0
            k = 0.45 * math.hypot(entry[0] - sx, entry[1] - sy)
            pts = _bezier((sx, sy), (sx + k * 0.9, sy + k * 0.05), (entry[0] - edir[0] * k, entry[1] - edir[1] * k), entry,
                          max(4, int(k / 0.03)))
            out.append((pts, 0.0, False))
        for P, pr, main in placed:
            out.append((P, pr, True))
        for m in marks:
            top = max(p[1] for P, _, _ in placed for p in P)
            lift = max(0.0, top - 1.05) if ch not in "ij" else 0.0
            if m == "̧":
                lift = 0.0
            mx = x + (adv - hand.track) / 2 - 0.18
            for part in MARKS[m].split("|"):
                P, pr = _pts(part)
                out.append((_spline([(p[0] * hand.wide + mx, p[1] + lift) for p in P]), pr, True))
        last = chain[-1][0]
        if gl["j"] and len(last) > 1:
            d = _unit(last[-1][0] - last[-2][0], last[-1][1] - last[-2][1])
            prev_exit = (last[-1], d)
        else:
            prev_exit = None
        if n == len(word) - 1 and final and gl["j"] and hand.flick and len(last) > 1 and last[-1][1] < 0.5:
            (px, py), (dx, dy) = last[-1], _unit(last[-1][0] - last[-2][0], last[-1][1] - last[-2][1])
            pts = _bezier((px, py), (px + dx * 0.16, py + dy * 0.16), (px + 0.26, py + 0.30), (px + 0.30, py + 0.44), 8)
            out.append((pts, 0.0, False))
            adv = max(adv, px - x + 0.34)
        x += adv
    return out, x


def _slant_pts(P, sl, wave):
    a, f, ph = wave
    t = math.tan(sl)
    return [(x + y * t, y + a * math.sin(x / f * 6.283 + ph)) for x, y in P]


class _Set:
    def __init__(self, text, size, seed):
        self.text = " ".join(text.split())
        self.rng = random.Random(_hash(self.text, seed))
        self.hand = _Hand(self.rng)
        self.size = size
        self.words = _word_units(self.text)
        if not self.words:
            raise Unsupported("nothing to letter")
        # every word once, at the origin: its strokes (upright, units) and its advance
        self.set = []
        for i, w in enumerate(self.words):
            strokes, end = _set_word(self.hand, w, 0.0, i == len(self.words) - 1)
            if G[w[-1][0]][0]["j"]:
                end += 0.12   # an exit stroke reaches into the gap: give the next word that much more room
            ink = [(x + y * math.tan(self.hand.slant)) for P, _, _ in strokes for x, y in P]
            self.set.append((strokes, end, min(ink), max(ink)))

    def line(self, idx):
        """Words idx laid out side by side: (strokes, ink_left, ink_right) in units, slanted."""
        out, x = [], 0.0
        for n, i in enumerate(idx):
            strokes, end, a, b = self.set[i]
            if n:   # a word's lead-in reaches back into the gap: the gap grows by most of it
                x += self.hand.space + 1.0 * max(0.0, -a)
            for P, pr, main in strokes:
                out.append(([(p[0] + x, p[1]) for p in P], pr, main))
            x += end
        sl = [(_slant_pts(P, self.hand.slant, self.hand.wave), pr, main) for P, pr, main in out]
        xs = [p[0] for P, _, _ in sl for p in P]
        return sl, min(xs), max(xs)

    def width(self, idx):
        _, a, b = self.line(idx)
        return b - a


def _breaks(st, max_units):
    """Words into one line, else two balanced lines, else three: [[word idx...]], widest line in units."""
    n = len(st.words)
    allw = list(range(n))
    one = st.width(allw)
    if one <= max_units or n == 1:
        return [allw], one
    best = None
    for k in range(1, n):
        a, b = st.width(list(range(k))), st.width(list(range(k, n)))
        score = max(a, b) + 0.15 * abs(a - b)
        if best is None or score < best[0]:
            best = (score, [list(range(k)), list(range(k, n))], max(a, b))
    return best[1], best[2]


def _breaks3(st):
    n = len(st.words)
    best = None
    for k in range(1, n - 1):
        for m in range(k + 1, n):
            ws = [st.width(list(range(0, k))), st.width(list(range(k, m))), st.width(list(range(m, n)))]
            score = max(ws) + 0.1 * (max(ws) - min(ws))
            if best is None or score < best[0]:
                best = (score, [list(range(0, k)), list(range(k, m)), list(range(m, n))], max(ws))
    return best[1], best[2]


# ---------------------------------------------------------------- flourishes

def _flourish(rng, x0, x1, y, xh, style, heavy, hair):
    """An underline flourish from x0 to x1 (px) at height y (px, y down): [(points, widths)] in px."""
    out = []
    L = x1 - x0
    if L < 3 * xh:
        return out
    bulge = heavy * rng.uniform(0.75, 1.0)

    def swell(pts, peak, at=0.5, sharp=1.4):
        n = len(pts)
        ws = []
        for i in range(n):
            t = i / (n - 1)
            u = t / at if t < at else (1 - t) / (1 - at)
            ws.append(hair + (peak - hair) * max(0.0, math.sin(u * math.pi / 2)) ** sharp)
        return pts, ws

    def curl(cx, cy, r, sign, turns=1.1, start=0.0):
        pts = []
        n = 26
        for k in range(n + 1):
            t = start + turns * 2 * math.pi * k / n
            rr = r * (1 - 0.55 * k / n)
            pts.append((cx + sign * rr * math.cos(t), cy - rr * math.sin(t)))
        return pts
    sag = rng.uniform(0.10, 0.22) * xh
    if style == "rule":
        # a long swelled rule, a little lower in the middle, its ends turned up in small curls
        n = max(12, int(L / 4))
        pts = [(x0 + L * k / n, y + sag * math.sin(math.pi * k / n) - 0.04 * xh * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
        out.append(swell(pts, bulge, at=rng.uniform(0.4, 0.6)))
        r = 0.22 * xh
        for side, (px, py) in ((-1, pts[0]), (1, pts[-1])):
            c = curl(px, py + r, r, side, turns=0.85, start=math.pi / 2)
            out.append((c, [hair] * len(c)))
    elif style == "lozenge":
        # two swelled strokes meeting at a small engraved lozenge in the middle
        mid = (x0 + x1) / 2
        g = 0.36 * xh
        for a, b in ((x0, mid - g), (mid + g, x1)):
            n = max(8, int((b - a) / 4))
            pts = [(a + (b - a) * k / n, y) for k in range(n + 1)]
            out.append(swell(pts, bulge * 0.9, at=0.7 if a == x0 else 0.3, sharp=1.8))
        d = 0.2 * xh
        loz = [(mid - d * 1.6, y), (mid, y - d), (mid + d * 1.6, y), (mid, y + d)]
        out.append(("poly", loz))
    else:
        # "sweep": a hairline from the left that swells as it runs right, ending in a turned-back loop
        n = max(12, int(L / 4))
        pts = [(x0 + L * k / n, y + sag * 0.6 * math.sin(math.pi * k / n)) for k in range(n + 1)]
        out.append(swell(pts, bulge, at=rng.uniform(0.6, 0.75), sharp=1.2))
        r = 0.2 * xh
        px, py = pts[-1]
        c = curl(px, py + r, r, 1, turns=0.9, start=math.pi / 2)
        out.append((c, [hair] * len(c)))
    return out


# ---------------------------------------------------------------- the SVG

def headline(text, width, size, seed=0, align="left", flourish=None, lines_max=2, min_scale=0.72, ink="#000",
             tight=False):
    """`text` hand-lettered as one SVG (str), at most `width` CSS px wide, for type of `size` CSS px.

    align: "left" or "center" (where the lines sit inside the drawing; the drawing is as wide as its widest line
    unless centred, when it is `width` wide; tight=True keeps a centred drawing as narrow as its ink, for a page
    that centres the picture itself and must not lay a box wider than the letters). flourish: None (the headline's own choice), False, or one of
    "rule", "lozenge", "sweep". Raises Unsupported when a character has no letter."""
    return _draw(text, width, size, seed, align, flourish, lines_max, min_scale, ink, tight)[0]


def _draw(text, width, size, seed, align, flourish, lines_max, min_scale, ink, tight=False):
    st = _Set(text, size, seed)
    hand, rng = st.hand, st.rng
    xh0 = size * 0.47
    xh = xh0
    lines, wu = _breaks(st, width / xh)
    if wu * xh > width and lines_max >= 3 and len(st.words) >= 3 and wu * xh * min_scale > width:
        l3, w3 = _breaks3(st)
        if w3 < wu:
            lines, wu = l3, w3
    if wu * xh > width:
        xh = width / wu * 0.995
    xh = max(xh, xh0 * 0.5)
    heavy = max(hand.heavy * xh, 1.6)
    hair = max(hand.hair * xh, 0.8)

    drawn = [st.line(idx) for idx in lines]
    # lines one under the other: as close as the letters allow, never closer than the hand's own spacing
    top_pad = 0.08 * xh
    y_base = None
    bases = []
    for n, (strokes, a, b) in enumerate(drawn):
        tops = [p[1] for P, _, _ in strokes for p in P]
        hi = max(tops)
        if y_base is None:
            y_base = (hi + 0.12) * xh + top_pad
        else:
            # skyline: the gap between this line's ink and the one above, column by column
            need = 0.0
            cols = {}
            for P, _, _ in drawn[n - 1][0]:
                for x, y in P:
                    c = int((x - drawn[n - 1][1]) * 4)
                    cols[c] = min(cols.get(c, 9), y)
            for P, _, _ in strokes:
                for x, y in P:
                    c = int((x - a) * 4)
                    for cc in (c - 1, c, c + 1):
                        if cc in cols:
                            need = max(need, y - cols[cc] + 0.30)
            pitch = max(need, 2.15)
            y_base += pitch * xh
        bases.append(y_base)

    W = max(b - a for _, a, b in drawn) * xh
    pen = _Pen(hand.slant, heavy, hair)
    box_w = width if align == "center" else W
    out_strokes = []
    for (strokes, a, b), yb in zip(drawn, bases):
        lw = (b - a) * xh
        ox = (box_w - lw) / 2 if align == "center" else 0.0
        for P, pr, main in strokes:
            Q = [((x - a) * xh + ox, yb - y * xh) for x, y in P]
            out_strokes.append((Q, pr, main))
    # px space has y down: the pen's "down the slant" is +y
    pen.ax = (math.sin(hand.slant), -math.cos(hand.slant))
    for Q, pr, main in out_strokes:
        pen.stroke(Q, pr, taper=main and pr > 0)

    fl = flourish if flourish is not None else rng.choice(["rule", "lozenge", "sweep", "rule"])
    extra = []
    if fl:
        strokes, a, b = drawn[-1]
        lw = (b - a) * xh
        ox = (box_w - lw) / 2 if align == "center" else 0.0
        frac = rng.uniform(0.55, 0.85) if fl != "lozenge" else rng.uniform(0.4, 0.6)
        span = min(lw * frac, max(lw, 6 * xh))
        if align == "center" or fl == "lozenge":
            x0 = ox + (lw - span) / 2
        else:
            x0 = ox + rng.uniform(0.02, 0.12) * lw
            if x0 + span > ox + lw:
                x0 = ox + lw - span
        x1 = x0 + span
        # just under the lowest ink above the rule's span (a descender sets it lower)
        under = bases[-1] + 0.10 * xh
        for Q, ws in pen.strokes:
            for (x, y), w in zip(Q, ws):
                if x0 - 0.6 * xh <= x <= x1 + 0.6 * xh and y > bases[-1] - 0.5 * xh:
                    under = max(under, y + w / 2)
        y = under + 0.40 * xh
        extra = _flourish(rng, x0, x1, y, xh, fl, heavy, hair)
        for e in extra:
            if e[0] == "poly":
                pass
            else:
                pen.shaped(*e)
    paths = []
    tol = 0.12
    for pts, ws in pen.strokes:
        poly = _outline(pts, ws)
        if _area(poly) < 0:
            poly = poly[::-1]
        paths.append(_simplify(poly, tol))
    for e in extra:
        if e[0] == "poly":
            poly = e[1]
            if _area(poly) < 0:
                poly = poly[::-1]
            paths.append(poly)
    xs = [x for P in paths for x, _ in P]
    ys = [y for P in paths for _, y in P]
    pad = 1.0
    left, top = min(xs) - pad, min(ys) - pad
    vw, vh = max(xs) + pad - left, max(ys) + pad - top
    if align == "center" and vw < width and not tight:   # centred: the drawing is the full width, the words in its middle
        left -= (width - vw) / 2
        vw = width
    # never wider than asked: a flourish or a flick that runs over is drawn a hair smaller, not cut off
    k = min(1.0, width / vw)
    w_out, h_out = math.ceil(vw * k), math.ceil(vh * k)
    d = "".join("M" + "L".join(f"{(x - left) * k:.1f} {(y - top) * k:.1f}" for x, y in P) + "Z" for P in paths)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_out}" height="{h_out}" viewBox="0 0 {w_out} {h_out}">'
           f'<path fill="{ink}" d="{d}"/></svg>')
    return svg, w_out, h_out, len(lines)
