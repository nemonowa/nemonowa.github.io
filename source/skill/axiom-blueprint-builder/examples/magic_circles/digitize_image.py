"""ブロックで作られた平面の文様の画像（真上から）→ .bp。 参考画像の再現用。
  python3 digitize_image.py image.jpg proto.json out.bp [--n 117] [--block-px 17.2] [--center 1026,1009] [--fold] [--dark purple_concrete] [--outer 色名,色名] [--tips 色名]
proto.json = {"air":[205,212,218], "purple_concrete":[100,36,158], …}  先頭が空気(背景)。代表色は画像の各ブロックから実測する
（色は光と影で変わるので、置きたい実ブロックの色ではなく『画像の中の見え方』で書く）。--n/--block-px/--center を省くと自動推定。
手順と失敗談は references/patterns.md。まず --report で分類結果と上面図を確認してから本番を出す。
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
import numpy as np
from PIL import Image
from builder import Build
from pattern_helpers import *

ap = argparse.ArgumentParser()
ap.add_argument('image'); ap.add_argument('proto'); ap.add_argument('out')
ap.add_argument('--n', type=int); ap.add_argument('--block-px', type=float); ap.add_argument('--center')
ap.add_argument('--fold', action='store_true', help='左右上下の鏡像で多数決して対称化')
ap.add_argument('--dark'); ap.add_argument('--report', action='store_true')
ap.add_argument('--tips', help='中心軸の先端(軸上かつ半径82%以上)にだけ許す色名(カンマ区切り)。四方の先端飾りなど')
ap.add_argument('--outer', help='外周(半径72%以上)にだけ許す色名(カンマ区切り)。縁のガラスや先端の灰色が内側にゴミとして出るのを防ぐ')
a = ap.parse_args()
rgb = np.array(Image.open(a.image).convert('RGB'))
proto = {k: tuple(v) for k, v in json.load(open(a.proto)).items()}
bg = np.array(list(proto.values())[0], float)
fg = np.abs(rgb.astype(float) - bg).sum(2) > 40
ys, xs = np.where(fg)
bpx = a.block_px or float(np.mean(estimate_block_px(rgb)))
cx, cy = (map(float, a.center.split(',')) if a.center else ((xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2))
n = a.n or (int(round((xs.max() - xs.min()) / bpx)) | 1)       # 奇数に
print(f'block={bpx:.2f}px  center=({cx:.0f},{cy:.0f})  n={n}')
cells = sample_grid(rgb, n, (cx, cy), bpx)
rules = {}
c0 = n // 2
if a.outer:
    rules.update({nm: (lambda i, j: ((i - c0) ** 2 + (j - c0) ** 2) ** 0.5 >= 0.72 * c0) for nm in a.outer.split(',')})
if a.tips:
    rules.update({nm: (lambda i, j: (abs(i - c0) <= 1 or abs(j - c0) <= 1) and ((i - c0) ** 2 + (j - c0) ** 2) ** 0.5 >= 0.82 * c0) for nm in a.tips.split(',')})
rules = rules or None
cls, names = classify(cells, proto, dark_to=a.dark, region_rules=rules)
if a.fold: cls = fold_d2(cls)
b = Build(); to_build(b, cls, names)
grid = {(k[0], k[2]): v[0] for k, v in b.B.items()}
render_top(grid, os.path.splitext(a.out)[0] + '_top.png', S=8)
print('blocks', len(b.B), {nm: int((cls == i).sum()) for i, nm in enumerate(names) if i})
if not a.report: b.save(a.out, os.path.splitext(os.path.basename(a.out))[0], author='nemo', tags=['pattern', 'floor'])
