"""Turn the Evening Edition's engraving files into crisp 1-bit PNGs.

The engravings are drawn as SVG, some of them several hundred KB of paths. The
Kindle's old browser is slow to parse and paint that much vector art on every
page turn, so after the pages are built this pass renders each ``art/*.svg`` at
twice its CSS size (one image pixel per e-ink pixel on the Paperwhite), reduces
it to pure black and white, and points the pages at the PNG instead. Every
reference already carries an explicit background size, so nothing else changes.

It needs Playwright and Pillow. When either is missing, or one file fails, the
SVG stays in place and the page still works.

    python -m solar.art_raster _site
"""
import glob
import io
import os
import re
import sys

SCALE = 2          # image pixels per CSS pixel
THRESHOLD = 168    # lighter than this becomes white; keeps anti-aliased hairlines


def _launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        for exe in sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"), reverse=True):
            return p.chromium.launch(executable_path=exe)
        raise


def _size(svg):
    m = re.search(r'<svg[^>]*?\swidth="([\d.]+)"[^>]*?\sheight="([\d.]+)"', svg)
    if not m:
        m = re.search(r'<svg[^>]*?\sheight="([\d.]+)"[^>]*?\swidth="([\d.]+)"', svg)
        return (float(m.group(2)), float(m.group(1))) if m else None
    return float(m.group(1)), float(m.group(2))


def _save(Image, shot, out):
    """Black, white and clear only: ink where the drawing is dark, paper where it is light, and
    nothing at all where the SVG drew nothing, so a frame still lets the ground show through."""
    im = Image.open(io.BytesIO(shot)).convert("RGBA")
    r, g, b, a = im.split()
    grey = Image.merge("RGB", (r, g, b)).convert("L")
    # composite over white first, so a faint anti-aliased edge is judged by how dark it looks
    lum = Image.composite(grey, Image.new("L", im.size, 255), a)
    ink = lum.point(lambda v: 0 if v > THRESHOLD else 1)
    solid = a.point(lambda v: 1 if v >= 128 else 0)
    if solid.getextrema()[0] == 1:  # fully opaque drawing: plain 1-bit
        lum.point(lambda v: 255 if v > THRESHOLD else 0).convert("1").save(out, optimize=True)
        return
    pal = Image.new("P", im.size, 2)  # 0 white, 1 black, 2 clear
    pal.putpalette([255, 255, 255, 0, 0, 0, 255, 255, 255])
    pal.paste(0, mask=solid.point(lambda v: 255 * v))
    both = Image.new("L", im.size, 0)
    both.paste(255, mask=ink.point(lambda v: 255 * v))
    both = Image.composite(both, Image.new("L", im.size, 0), solid.point(lambda v: 255 * v))
    pal.paste(1, mask=both)
    pal.save(out, optimize=True, transparency=2)


def rasterize(evening_dir):
    """Convert art/*.svg under ``evening_dir``; return the names converted."""
    art = os.path.join(evening_dir, "art")
    files = sorted(glob.glob(os.path.join(art, "*.svg")))
    if not files:
        return []
    try:
        from PIL import Image
        from playwright.sync_api import sync_playwright
    except Exception as e:  # pragma: no cover - optional tools
        print(f"art_raster: skipped ({e})")
        return []
    done = []
    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_context(device_scale_factor=SCALE).new_page()
        for f in files:
            try:
                svg = open(f, encoding="utf-8").read()
                wh = _size(svg)
                if not wh:
                    continue
                w, h = wh
                page.set_viewport_size({"width": int(w + 0.999), "height": int(h + 0.999)})
                page.set_content('<body style="margin:0;background:transparent">' + svg + "</body>")
                shot = page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}, omit_background=True)
                _save(Image, shot, f[:-4] + ".png")
                done.append(os.path.basename(f))
            except Exception as e:
                print(f"art_raster: kept {os.path.basename(f)} as SVG ({e})")
        browser.close()
    if not done:
        return []
    names = set(done)
    swap = lambda m: m.group(0)[:-4] + ".png" if m.group(1) in names else m.group(0)
    for path in glob.glob(os.path.join(evening_dir, "*.html")) + glob.glob(os.path.join(evening_dir, "*.css")):
        text = open(path, encoding="utf-8").read()
        new = re.sub(r"art/([A-Za-z0-9_.-]+?\.svg)", swap, text)
        if new != text:
            open(path, "w", encoding="utf-8").write(new)
    for name in done:
        os.remove(os.path.join(art, name))
    return done


def main(site="_site"):
    evening = os.path.join(site, "evening")
    done = rasterize(evening)
    total = sum(os.path.getsize(f) for f in glob.glob(os.path.join(evening, "art", "*.png")))
    print(f"art_raster: {len(done)} engravings as PNG, {total // 1024} KB in all")


if __name__ == "__main__":
    main(*sys.argv[1:2])
