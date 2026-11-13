"""python3 tools/frames/t.py OUTDIR : quick engine test renders (strips at 24/14/9 px)."""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import scroll
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for H in (24, 14, 9):
    w = 300
    cv = scroll.Canvas(w, H)
    t = time.time()
    scroll.strip(cv, scroll.Run([(0, H / 2), (w, H / 2)], H), seed=H)
    s = cv.svg(); open(f'{out}/strip{H}.svg', 'w').write(s)
    print(H, len(s) // 1024, 'KB', round(time.time() - t, 2))
