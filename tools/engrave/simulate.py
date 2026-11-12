#!/usr/bin/env python3
"""
E-ink simulator for Kindle Paperwhite 11 (Carta 1200, 1236x1648 @300ppi, 16 grey levels).

What it models
  1. Chrome renders RGB at DPR 2 -> the X server / framebuffer is 8-bit grey (Y8).
     We convert with Rec.601 luma (what the Kindle's 8bpp fb conversion uses).
  2. The EPDC (MediaTek hwtcon on PW11) drives the panel with a GC16/GL16 waveform:
     only the top 4 bits matter. The browser's screen updates are sent WITHOUT the
     dither flag, so 8-bit -> 16 levels is a plain quantise (posterise), not a dither.
       --quant round      nearest of the 16 levels 0x00,0x11..0xFF  (default)
       --quant truncate   v>>4 (old i.MX EPDC behaviour, darkens by up to 1 step)
       --quant ordered    8x8 Bayer ordered dither to 16 levels (hw dither flag;
                          what KOReader requests for images; NOT what the browser gets)
       --quant fs         Floyd-Steinberg to 16 levels (software dither, for comparison)
       --quant bw         A2/DU 2-level (fast-refresh/scroll waveform: what you see
                          while a page is being flicked or animated)
  3. Panel tone: level 0..15 maps ~linearly in L* from black L*~17 to paper L*~85,
     with a faint warm paper tint. Pure #000 is the only way to reach the deep black.
  4. Optical: a tiny blur (front-light guide + cover lens, sigma ~0.35 dev px).
  5. Ghosting (--prev): the previous sheet leaves a residue after a non-flashing
     (GL16 / REAGL) update. Residue ~4-8% of the L* difference, strongest where the
     old image was solid black and the new one is white. --flash clears it.
  6. Dot gain (--gain): dark pigment spreads ~1/2 px (fringe fields between electrodes),
     so 1-px WHITE features inside black fill in; 1-px black lines on white survive.
  7. --eye: also write a "reading distance" version (Gaussian blur ~1 arcmin at 30cm)
     where sub-resolution hatching averages to tone and any moire shows up as beats.

Usage
  simulate.py in.png out.png [--quant round] [--prev old.png [--ghost 0.06]] [--eye]
                              [--crop x,y,w,h] [--zoom 3] [--side-by-side]
"""
import sys, argparse
import numpy as np
from PIL import Image, ImageFilter

L_BLACK, L_WHITE = 17.0, 85.0          # Carta 1200 measured-ish (GC16, front light off)
PAPER_TINT = np.array([1.0, 0.992, 0.965])  # very slight warm paper

BAYER8 = np.array([[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],
                   [12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
                   [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],
                   [15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]], float)

def to_y8(img):
    img = img.convert('RGBA')
    bg = Image.new('RGBA', img.size, (255,255,255,255)); bg.alpha_composite(img)
    a = np.asarray(bg.convert('RGB'), dtype=np.float64)
    return 0.299*a[...,0] + 0.587*a[...,1] + 0.114*a[...,2]

def quantise(y, mode='round'):
    """y: float 0..255  ->  int levels 0..15"""
    if mode == 'round':    return np.clip(np.rint(y/17.0), 0, 15).astype(np.int16)
    if mode == 'truncate': return np.clip(np.floor(y/16.0), 0, 15).astype(np.int16)
    if mode == 'bw':       return np.where(y >= 128, 15, 0).astype(np.int16)
    if mode == 'ordered':
        h, w = y.shape
        t = (np.tile(BAYER8, (h//8+1, w//8+1))[:h,:w] + 0.5)/64.0 - 0.5
        return np.clip(np.floor(y/17.0 + 0.5 + t), 0, 15).astype(np.int16)
    if mode == 'fs':
        e = y.astype(np.float64)/17.0; h, w = e.shape
        out = np.zeros_like(e, dtype=np.int16)
        for r in range(h):   # serpentine
            rng = range(w) if r%2==0 else range(w-1,-1,-1); d = 1 if r%2==0 else -1
            row = e[r]; nxt = e[r+1] if r+1 < h else None
            for c in rng:
                q = min(15, max(0, int(row[c]+0.5))); out[r,c] = q; err = row[c]-q
                if 0 <= c+d < w: row[c+d] += err*7/16
                if nxt is not None:
                    if 0 <= c-d < w: nxt[c-d] += err*3/16
                    nxt[c] += err*5/16
                    if 0 <= c+d < w: nxt[c+d] += err*1/16
        return out
    raise ValueError(mode)

def level_to_L(q):
    return L_BLACK + (L_WHITE - L_BLACK) * (q.astype(np.float64)/15.0)

def L_to_srgb(L):
    Y = np.where(L > 8, ((L+16)/116.0)**3, L/903.3)
    s = np.where(Y <= 0.0031308, 12.92*Y, 1.055*np.power(np.clip(Y,0,1), 1/2.4) - 0.055)
    return np.clip(s, 0, 1)

def L_to_Y(L):
    return np.where(L > 8, ((L+16)/116.0)**3, L/903.3)

def Y_to_L(Y):
    Y = np.clip(Y, 1e-6, 1)
    return np.where(Y > 0.008856, 116*np.cbrt(Y)-16, 903.3*Y)

def dot_gain(L, g=0.45):
    """Fringe-field / particle-spread dot gain: dark pigment creeps ~1/2 px into
    neighbouring white pixels. Asymmetric: an isolated 1-px WHITE line in black loses a
    lot of reflectance, a 1-px black line on white barely changes."""
    if g <= 0: return L
    Y = L_to_Y(L); Yw, Yb = L_to_Y(np.array(L_WHITE)), L_to_Y(np.array(L_BLACK))
    w = (Y - Yb) / (Yw - Yb)                       # 0 = black .. 1 = white
    p = np.pad(w, 1, mode='edge')
    nb = (p[:-2,:-2]+p[:-2,1:-1]+p[:-2,2:]+p[1:-1,:-2]+p[1:-1,2:]+p[2:,:-2]+p[2:,1:-1]+p[2:,2:]) / 8.0
    w2 = w * (1 - g*(1-nb)**1.5)
    return Y_to_L(Yb + w2*(Yw-Yb))

def render(L, blur=0.35):
    rgb = (L_to_srgb(L)[..., None] * PAPER_TINT * 255.0)
    im = Image.fromarray(np.clip(np.rint(rgb),0,255).astype(np.uint8), 'RGB')
    return im.filter(ImageFilter.GaussianBlur(blur)) if blur > 0 else im

def simulate(img, quant='round', prev=None, ghost=0.06, flash=False, blur=0.35, gain=0.45):
    q = quantise(to_y8(img), quant)
    L = level_to_L(q)
    if prev is not None and not flash:
        qp = quantise(to_y8(prev.resize(img.size)), 'round'); Lp = level_to_L(qp)
        # residue is stronger dark->light (black particles lag) than light->dark
        k = np.where(Lp < L, ghost*1.3, ghost*0.6)
        L = L + k*(Lp - L)
    return render(dot_gain(L, gain), blur), q

def eye_view(sim, sigma=1.1):
    return sim.convert('L').filter(ImageFilter.GaussianBlur(sigma)).convert('RGB')

def stats(q):
    h = np.bincount(q.ravel(), minlength=16) / q.size
    return ' '.join(f'{i:x}:{h[i]*100:4.1f}' for i in range(16) if h[i] >= 0.001)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--quant', default='round', choices=['round','truncate','ordered','fs','bw'])
    ap.add_argument('--prev'); ap.add_argument('--ghost', type=float, default=0.06)
    ap.add_argument('--flash', action='store_true')
    ap.add_argument('--blur', type=float, default=0.35)
    ap.add_argument('--gain', type=float, default=0.45, help='dot gain (dark spread), 0 disables')
    ap.add_argument('--eye', action='store_true')
    ap.add_argument('--crop'); ap.add_argument('--zoom', type=int, default=1)
    ap.add_argument('--side-by-side', action='store_true', help='original | simulated')
    a = ap.parse_args()
    img = Image.open(a.inp)
    if a.crop:
        x,y,w,h = map(int, a.crop.split(',')); img = img.crop((x,y,x+w,y+h))
    prev = Image.open(a.prev) if a.prev else None
    if prev is not None and a.crop: prev = prev.crop((x,y,x+w,y+h))
    sim, q = simulate(img, a.quant, prev, a.ghost, a.flash, a.blur, a.gain)
    out = sim
    if a.side_by_side:
        o = img.convert('RGB'); out = Image.new('RGB', (o.width*2+8, o.height), (128,128,128))
        out.paste(o, (0,0)); out.paste(sim, (o.width+8, 0))
    if a.zoom > 1: out = out.resize((out.width*a.zoom, out.height*a.zoom), Image.NEAREST)
    out.save(a.out)
    if a.eye:
        e = eye_view(sim); e.save(a.out.rsplit('.',1)[0] + '-eye.png')
    print(f'{a.out}: levels% {stats(q)}')

if __name__ == '__main__':
    main()
