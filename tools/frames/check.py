"""python3 tools/frames/check.py DIR : audit rendered frames (DIR/*.svg + DIR/*.png at DPR 2).

Per file: KB, stroke widths, forbidden markup, black share of the band (opaque pixels outside the slot),
black share of the whole box, largest white square outside the slot (CSS px), and whether the slot is
clean white.  The slot rect is read from a  data-slot="x y w h"  attribute on the <svg> if present.
"""
import sys, os, re, glob
from PIL import Image
import numpy as np

def audit(svgp):
    s = open(svgp).read()
    png = svgp[:-4] + '.png'
    iss = []
    kb = len(s.encode()) / 1024
    if kb > 200: iss.append('%.0fKB' % kb)
    widths = set(re.findall(r'stroke-width:([\d.]+)', s)) | set(re.findall(r'stroke-width="([\d.]+)"', s))
    bad = [w for w in widths if float(w) not in (0.5, 1.0, 1.5)]
    if bad: iss.append('stroke ' + ','.join(bad))
    if re.search(r'<(text|mask|filter|foreignObject)|transform|dasharray|<image', s): iss.append('forbidden markup')
    a = np.asarray(Image.open(png).convert('RGBA')).astype(float)
    H, W = a.shape[:2]
    alpha = a[..., 3] / 255
    lum = (a[..., :3].mean(-1) / 255) * alpha + (1 - alpha)  # over white
    ink = (lum < 0.5) & (alpha > 0.5)
    m = re.search(r'data-slot="([\d. ]+)"', s)
    slot = np.zeros((H, W), bool)
    if m:
        x, y, w, h = [float(v) * 2 for v in m.group(1).split()]
        slot[int(round(y)):int(round(y + h)), int(round(x)):int(round(x + w))] = True
        sl = lum[slot]
        if sl.size and (sl < 0.98).mean() > 0.001: iss.append('slot not clean (%.2f%%)' % ((sl < 0.98).mean() * 100))
    band = (alpha > 0.5) & ~slot
    bshare = ink[band].mean() if band.any() else 0
    wshare = ink.mean()
    if bshare > 0.45: iss.append('band black %.0f%%' % (bshare * 100))
    # largest all-white square outside the slot (opaque white), via DP
    white = (lum > 0.9) & (alpha > 0.5) & ~slot
    dp = np.zeros((H + 1, W + 1), int); best = 0
    for i in range(H):
        row = white[i]; prev = dp[i]; cur = dp[i + 1]
        for j in np.nonzero(row)[0]:
            v = min(prev[j], prev[j + 1], cur[j]) + 1
            cur[j + 1] = v
            if v > best: best = v
    if best / 2 > 12: iss.append('white patch %.0fpx' % (best / 2))
    edge_alpha = max(alpha[0, 0], alpha[0, -1], alpha[-1, 0], alpha[-1, -1])
    return dict(kb=kb, band=bshare, whole=wshare, white=best / 2, corner_alpha=edge_alpha, issues=iss)

if __name__ == '__main__':
    bad = 0
    for p in sorted(glob.glob(os.path.join(sys.argv[1], '*.svg'))):
        r = audit(p)
        print('%-28s %6.1fKB band %3.0f%% whole %3.0f%% white %4.1fpx  %s' % (
            os.path.basename(p), r['kb'], r['band'] * 100, r['whole'] * 100, r['white'], '; '.join(r['issues']) or 'ok'))
        bad += bool(r['issues'])
    sys.exit(1 if bad else 0)
