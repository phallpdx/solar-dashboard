# E-ink rules for the Morning Edition art

Target: Kindle Paperwhite 11, Carta 1200, 1236×1648 at 300 ppi, 16 grey levels.
Chrome 75, 618×714 CSS px viewport, DPR 2. **1 CSS px = 2 device px = 0.17 mm.**
The panel shows paper at about L\*85 and black at about L\*17, so each grey step is about 4.5 L\*.

The browser's screen updates go out without the EPDC dither flag. Each 8-bit grey is
posterised to the nearest of 16 levels. Some drivers truncate instead (`v>>4`). Nothing is
dithered, so any value that is not an exact level jumps to a neighbouring level.

Simulator: `simulate.py in.png out.png [--quant round|truncate|ordered|fs|bw] [--prev old.png] [--flash] [--eye]`
Harness: `BASE=http://localhost:8766/kindle/ node shoot.js index index~2 music --ghost --eye [--css ../designer.css]`
(`file:///…html --full` works for loose art.) For pattern metrics, run `make_patterns.py`, then shoot `tp/*.html` to `tpshots/`, then run `analyse.py`, `linecontrast.py` and `inkscore.py`.

---

## 1. Lines and hatching (the most important rules)

| | Use | Never use |
|---|---|---|
| Stroke width | **0.5 CSS (1 dev px)**, **1 CSS (2 dev)**, 1.5 CSS (3 dev) | 0.6, 0.7, **0.75**, **0.8**, 0.9, 1.1, 1.2 … |
| Hatch pitch (line to line) | **1, 1.5, 2, 3 CSS** (2, 3, 4, 6 dev px) | **3.6, 3.4, 3.2, 2.6, 1.75, 1.8 …** |
| Line position (horizontal or vertical) | 0.5-px lines centred at `k·0.5 + 0.25` CSS; 1-px lines centred at `k·0.5` CSS | arbitrary decimals |
| Orthogonal hatch | add `shape-rendering="crispEdges"` | — |

Why: a stroke that does not cover whole device pixels is anti-aliased into a grey fringe.
For example, 0.75 CSS lines never reach black (L\*33 instead of 17). A non-integer pitch makes
every Nth line heavier, because the fractional part beats against the pixel grid. With 3.6 CSS
lines (7.2 dev px) the beat is every 5 lines, an 18-CSS-px stripe that reads as moiré
(`c-offgrid.png`). In the current art, ink purity (the share of inked pixels that are solid black)
is 17–35 % in the engraved plates. The aligned test hatch scores 78 %.

- **Minimum clear gap between parallel lines: 1 dev px (0.5 CSS) for straight crispEdges lines.**
  For anything anti-aliased (curves, diagonals) the minimum is **2 dev px (1 CSS)**. A gap of 1 dev px
  or less fills in to solid or grey mush.
- Make tone with fixed pitch and variable width (bulino), not variable pitch. At a 4-dev pitch,
  widths of 1, 2 and 3 dev give exact 25 %, 50 % and 75 % tones.
- Diagonals: prefer exactly **45°**, at a pitch of 1.5, 2 or 3 CSS with a 0.5 CSS stroke.
  Avoid **1–10° near-horizontal hatch**, because it staircases into long beat bands. 30° and 15° are acceptable.
- Cross-hatch: each layer at a pitch of 3 CSS or more. A cross-hatch at 1.7 CSS and 0.8 CSS fills to a flat dark grey.
- Isolated hairlines: 0.5 CSS black on white is crisp and fine. Do not use grey hairlines:
  `--hair:#5c5c5c` 1 px reads weaker than `#000` at 0.5 px.

## 2. Guilloché

- Strokes 0.5 CSS on white and 1 CSS on black.
- Check the **perpendicular** gap at the steepest point of the wave, not the vertical spacing.
  Neighbouring strands must stay at least 1 CSS apart there:
  `vertical spacing ≥ (1 + stroke) / cos(atan(2π·A/P))`, where A is the amplitude and P is the period in CSS px.
  For example, with A=7 and P=60, the spacing must be at least 2.2 CSS. A spacing of 1.3 CSS (the "before" band)
  turns black at every pinch.
- Rosettes: the number of strands crossing any radius must be no more than **band width in dev px ÷ 3**.
  A 12-CSS-wide ring can hold about 8 crossings. At n=48 the ring turns into a solid black donut (`c-guil.png`).
- Curves are always anti-aliased. Keep their tone light (≤ 35 % ink) so the grey fringes read as engraving, not mud.
- Leave every `<pattern>` tile an integer number of device px: 1, 1.5, 2, 3 or 4 CSS, never 3.6.

## 3. Greys: use only the 16 exact levels

`#000000 #111111 #222222 #333333 #444444 #555555 #666666 #777777 #888888 #999999 #aaaaaa #bbbbbb #cccccc #dddddd #eeeeee #ffffff`

These are the only values that render the same under every quantiser: round, truncate and the
hardware dither all leave them untouched (`greys-quant.png`, bottom row of each block). Every other
value lands on a different level depending on the driver.

- **Lighter than `#f8f8f8` disappears.** With a truncating driver, `#f1`–`#f7` also disappear.
  The section `--tint` colours all collapse to `#eeeeee`. `#FFF8E6` and `#FFF8E8` vanish completely,
  and `#FBF0DC`, `#FFF1D6`, `#FFF4DE` and `#F8F2E4` vanish under truncation.
- Do not use `opacity`, `rgba()` or `color-mix` on art. They produce arbitrary values, and so do
  gradients, which posterise into 16 visible bands. If you want a ramp, draw it **deliberately as
  stepped flat bands** of the exact greys. It reads as an engraved tint ramp.
- Recommended underprints (grey plates behind art): `#eeeeee` (faint, about 4 L\* below paper),
  `#dddddd` (9 L\*) and `#cccccc`. Mid-tones should come from hatching, not grey fills.
- Colour: only luma (0.299R + 0.587G + 0.114B) survives. Pick colours whose luma is exactly k×17.

## 4. Text on tint

- Body text (≤ 17 px) goes **only on `#ffffff`, `#eeeeee` or `#dddddd`**, in `#000`.
  `#222` text is fine; `#444` is the lightest you should use, and `#888` is too weak.
- Display text (≥ 20 px bold) may also sit on `#cccccc` or `#bbbbbb`.
- **Never put text on hatching, dot screens or guilloché.** At any pitch it becomes illegible (`c-text.png`).
  Knock out a white or `#eeeeee` cartouche with at least 4 CSS px of padding and a 0.5 px black rule.

## 5. Inverse (black) plates

- Plate fill is **`#000`**. It is the deepest black the panel has, and `#222` is visibly greyer (L\*25 vs 17).
- **White lines must be at least 1 CSS (2 dev px) wide, with black gaps of at least 1 CSS.**
  A 0.5 CSS white line fills in to L\*45 and a 0.75 CSS line to L\*60, so both look like grey threads
  (`c-inverse.png`). Dark pigment spreads into thin white features, and the effect is not symmetrical:
  a 0.5 px black line on white survives.
- White text on black: at least 13 px bold or 16 px regular, with letter-spacing of 0.05em or more.
  Avoid Playfair hairline serifs reversed out of black.
- Inverse guilloché: no more than 12–16 strands across a 30 CSS band, stroke 1 CSS.

## 6. Ghosting and flashes

A page turn without a flash (GL16/REAGL) leaves 4–8 % of the previous sheet showing. The residue is
worst where a black plate or a big headline used to be (`ghost-demo.png`). At present the flash
(a black overlay) runs only every 6th in-page turn.

- **Flash on the turn *after* any sheet that has more than about 5 % black area** (inverse plates,
  black bands, big black medallions, headlines of 40 px or more). Turning *onto* a plate is less
  important because it gets cleaned up by the next flash, but also flash onto a full-bleed plate so its black is uniform.
- Mark such sheets, e.g. `data-flash`, and make `turn()` flash when either the old sheet or the
  new sheet carries the mark, in addition to the every-6 rule.
- Hold the black overlay for **≥ 400 ms** rather than 250 ms. A Carta GC16 frame takes about
  300–450 ms, and a shorter overlay can merge with the next update and fail to clear anything.
  Treat the overlay as the flash: it sets every pixel to the same state.
- Do not put moving or changing content (clocks, tickers) inside dense art. Each partial update ghosts.

## 7. Tricks that make the panel look astonishing

1. **1-device-pixel black lines.** At 85 µm they are finer than a burin line in print. Use
   0.5 CSS with crispEdges on the grid, and with the white gaps rule above they give contrast of
   L\*17 against 85 with no grey.
2. **Deep solid `#000` plates straight after a flash.** That is the panel's blackest, most even state.
   Put the cover plate on the first sheet after navigation.
3. **The 16 exact greys as flat tints.** There is no dither and no noise, so they look like
   silk-screened ink. Layer `#eeeeee` and `#dddddd` underprints under black linework for a banknote feel.
4. **Own the pixels.** For the most complex engravings, render to PNG at **device resolution**
   (2× the CSS box) in Python, already quantised to the 16 levels (threshold line art; no
   smoothing), and serve it at exactly half its pixel size with `image-rendering: pixelated`
   on integer CSS coordinates. What you draw is then exactly what the panel shows.
5. **Bulino tone at a fixed pitch.** Vary line width in whole device pixels for shading: crisp, and free of moiré.
6. Keep total black coverage on reading sheets under about 25 %. Heavy black sheets need a flash and slow the turn.

## 8. Worst problems in the current art (Nov 12, 04:40 snapshot)

1. **Off-grid pitches and fractional strokes everywhere.** In `designer.css`, 275 `<pattern>` tiles use
   3.6, 3.4 and 3.2 CSS tiles, and strokes include 0.8, 0.9 and 1.1. `orn/*.svg` has 3408 strokes
   at 0.8, 1490 at 1.1, 1038 at 0.9 and 391 at 0.7. On the panel these become grey, beaded lines that beat in weight.
   Solid-black share of ink: cover-a 24 %, cover-b 22 %, frame panels 17 %, almanac plate 35 %,
   almanac headpiece 21 %, almanac preview 7 %.
2. **Sky and water hatching at variable fractional pitch** (cover plates and the almanac bridge).
   Line minima range from 38 to 144 of 255 within a single area, so the lines swing from black to
   mid-grey in visible bands. Cross-hatched mountain shadows at about 1.7 CSS go to flat mud.
3. **Dense rosettes and the narrow banknote bands in `frame-panels`** fill in to dark grey solids.
4. **Ghosting:** after a sheet with a black plate (music, end), the next partial turn keeps the plate
   and headline. The 250 ms overlay that flashes only every 6 turns is not enough.
5. **Grey hairlines and frames:** `--hair:#5c5c5c` and the `#222` strokes in `frame-*.svg` are not
   on-level and read weaker than a 0.5 px `#000` line.
6. **Colour section tints** all collapse to one `#eeeeee`. Two of them vanish outright, and four more
   vanish on a truncating driver.

## 9. Mechanical enforcement: `snap_svg.py`

`snap(svg_text, display_width=None, name="")` and the CLI `snap_svg.py --inplace --backup-dir orig f.svg …`
use the standard library only. It snaps stroke widths in **displayed** CSS px to 0.5/1/1.5
(heavier strokes to the nearest 0.5), colours to the 16 greys, and opacity onto white. It snaps
userSpaceOnUse pattern tiles to 1/1.5/2/3 CSS px (larger tiles to the nearest 0.5) and adds crispEdges
to axis-aligned pattern hatching. Geometry is left alone. Display width comes from the name:
emblem 200, headpiece/plate/tailpiece 560, cover 570, frame 618.

What it measurably fixes: on-grid pattern hatching. inst-bars went from 15 % to 63 % solid black.
What it cannot fix: lines whose **positions** are off-grid. A 0.5 CSS (1 dev px) curve or diagonal
at an arbitrary offset is split into two 50 % greys, so it is **never black**. Thin AA strokes
therefore read lighter after snapping: the cover went from 24 % to 12 % solid black. With `--fine-max 0.6`,
strokes of 0.6 CSS or more go to 1 CSS. That doubles solid black (cover 46 %, almanac plate 57 %) but
fills in hatching tighter than 2 CSS. **Correction to §1: 0.5 CSS is crisp only on the grid
(crispEdges, or centred at k·0.5+0.25). Curves and diagonals that must read black need 1 CSS
with a 1 CSS gap. Otherwise accept them as grey "light lines".** Engravers should call `snap()`
at the end of their generators. A file regenerated after snapping loses the snap; the in-place CLI
skips files that are already snapped and refreshes `orig/` from fresh ones.

## Files

- `snap_svg.py` (enforcer), `snap_engravers.py` (runs every engraver module with sample args, writing `snapped/*.orig|snap.svg`), `snap-cover-compare.png`
- `simulate.py` (panel model), `shoot.js` (harness), `make_patterns.py` and `tp/` (test pages), `tpshots/`
- `analyse.py`, `linecontrast.py`, `inkscore.py` (metrics), `crops.py` (zoomed crops of browser vs e-ink)
- `ba-sim.png` and `ba-zoom.png`: before/after of the same motifs (hatch, cross-hatch, guilloché, rosette, inverse plate, text on tint)
- `c-offgrid.png`, `c-guil.png`, `c-inverse.png`, `c-text.png`: failure modes, with the browser on top and e-ink below
- `greys-quant.png`: a smooth gradient, off-palette greys and the 16 exact greys under round, truncate, ordered and FS
- `ghost-demo.png`: a partial update after a plate, compared with the same update after a flash
- `shots/`: designer preview pages (raw, eink and eye versions); `art/`: engravers' plates simulated

Model caveats: the L\* endpoints, 6 % ghost and 0.45 dot-gain values are estimates from Carta
behaviour, not measurements of this unit. Check one test page on the real Kindle (open
`tp/01-hatch-aligned.html` and `tp/06-inverse.html`) before you rely on borderline cases.
