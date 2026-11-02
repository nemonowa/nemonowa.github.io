"""等角投影のPNGプレビュー。生成直後に必ず view で目視確認する（形・色抜け・はみ出し）。

python3 render_preview.py in.bp out.png [--yaw 0..3] [--scale 6] [--clip x0,y0,z0,x1,y1,z1]
  --yaw   0: +x+z 側から（正面=+z が左下に見える） 1,2,3: 90°ずつ回転
  --scale ブロック1個のピクセル幅。小さい建築は 12〜16、巨大建築は 5〜6
  --clip  断面表示。ファイル内座標（最小角=0）で範囲を指定。内装の確認に使う
マゼンタのブロックは colors.py に色がない＝ KEYWORDS に追加する。
"""
import sys, argparse
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from PIL import Image, ImageDraw
from bplib import read_bp
from colors import col
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--yaw', type=int, default=0); ap.add_argument('--scale', type=float, default=0)
ap.add_argument('--clip'); ap.add_argument('--bg', default='#9cc7e8')
a = ap.parse_args()
bl = read_bp(a.src)['blocks']
if a.clip:
    x0, y0, z0, x1, y1, z1 = map(int, a.clip.split(','))
    bl = {k: v for k, v in bl.items() if x0 <= k[0] <= x1 and y0 <= k[1] <= y1 and z0 <= k[2] <= z1}
rot = [lambda x, y, z: (x, y, z), lambda x, y, z: (-z, y, x), lambda x, y, z: (-x, y, -z), lambda x, y, z: (z, y, -x)][a.yaw % 4]
bl = {rot(*k): v for k, v in bl.items()}
vis = [k for k in bl if not all(n in bl for n in ((k[0]+1, k[1], k[2]), (k[0], k[1]+1, k[2]), (k[0], k[1], k[2]+1)))]
vis.sort(key=lambda k: (k[0]+k[2], k[1]))
xs = [k[0] for k in vis]; ys = [k[1] for k in vis]; zs = [k[2] for k in vis]
span = max(max(xs)-min(xs)+max(zs)-min(zs), (max(ys)-min(ys))*1.3)+4
t = a.scale or max(3, min(16, 1500/span))
W, H = 1800, 1400
img = Image.new('RGB', (W, H), a.bg); D = ImageDraw.Draw(img)
px = [(x-z)*t*.866 for x, y, z in vis]; py = [(x+z)*t*.5-y*t for x, y, z in vis]
ox = W/2-(min(px)+max(px))/2; oy = H/2-(min(py)+max(py))/2
for k, X, Y in zip(vis, px, py):
    h = col(bl[k]); c = (h >> 16, h >> 8 & 255, h & 255); cx, cy = X+ox, Y+oy; w = t*.866; hh = t*.5
    D.polygon([(cx-w, cy), (cx, cy+hh), (cx, cy+hh+t), (cx-w, cy+t)], tuple(int(v*.7) for v in c))
    D.polygon([(cx+w, cy), (cx, cy+hh), (cx, cy+hh+t), (cx+w, cy+t)], tuple(int(v*.85) for v in c))
    D.polygon([(cx, cy-hh), (cx+w, cy), (cx, cy+hh), (cx-w, cy)], c)
img.save(a.out); print('saved', a.out, 'visible faces', len(vis))
