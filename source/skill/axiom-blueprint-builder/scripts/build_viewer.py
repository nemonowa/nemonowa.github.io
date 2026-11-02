"""複数の .bp を1枚のHTMLビューア（three.js）にまとめる。公開用（Artifact）に使う。

python3 build_viewer.py OUT.html --samples DIR_OR_FILES... [--archive DIR_OR_FILES...]
  --samples  生成した建築（一覧上部「SAMPLES」に NEW 付きで並ぶ。指定順＝表示順）
  --archive  ユーザーの手持ち建築（下部「ARCHIVE」）
  --sync-local PATH  ローカル用ビューア(assets/local_viewer.html)の色表を colors.py に同期して PATH に書き出す

データは「外から見える面」だけに間引いて埋め込む（6方向すべて不透明ブロックに囲まれたものを除外）。
葉は不透明扱いで間引く（殻状に作るのが前提）。ガラス・水・氷は半透明。HTMLは16MB以下に収めること。
"""
import sys, os, json, base64, argparse, collections, re, struct
HERE = __file__.rsplit('/', 1)[0]; sys.path.insert(0, HERE)
from bplib import read_bp
from colors import col, shape, INVISIBLE, KEYWORDS, KEYWORDS_26

def files(items):
    out = []
    for it in items or []:
        if os.path.isdir(it): out += [os.path.join(it, f) for f in sorted(os.listdir(it)) if f.endswith('.bp')]
        else: out.append(it)
    return out

def entry(path, sample):
    bp = read_bp(path); h = bp['header']; bl = bp['blocks']
    occ = {k for k, s in bl.items() if shape(s.split('[')[0], s) == 0 and 'glass' not in s and s.split('[')[0] not in INVISIBLE | {'water'}}
    cnt = collections.Counter(s.split('[')[0] for s in bl.values())
    xs = [k[0] for k in bl] or [0]; ys = [k[1] for k in bl] or [0]; zs = [k[2] for k in bl] or [0]
    mx, my, mz = min(xs), min(ys), min(zs); pal = {}; v = []
    for (x, y, z), s in bl.items():
        n = s.split('[')[0]
        if n in INVISIBLE: continue
        if all(p in occ for p in ((x+1, y, z), (x-1, y, z), (x, y+1, z), (x, y-1, z), (x, y, z+1), (x, y, z-1))): continue
        key = (n, shape(n, s))
        if key not in pal: pal[key] = len(pal)
        v += [x-mx, y-my, z-mz, pal[key]]
    return dict(sample=sample, name=h.get('Name') or os.path.basename(path), file=os.path.basename(path), author=h.get('Author'),
                tags=h.get('Tags', []), ver=h.get('Version'), count=h.get('BlockCount', len(bl)),
                size=[max(xs)-mx+1, max(ys)-my+1, max(zs)-mz+1], thumb=base64.b64encode(bp['thumb_png']).decode(),
                yaw=round(h.get('ThumbnailYaw', 0), 1), pitch=round(h.get('ThumbnailPitch', 0), 1),
                top=cnt.most_common(12), kinds=len(cnt), pal=[[n, '#%06x' % col(n), sh] for (n, sh) in pal],
                **({'vb': base64.b64encode(struct.pack('<%dh' % len(v), *v)).decode()} if len(v) > 400000 else {'v': v}))   # 大きいものは Int16 の base64（約2/3）

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--samples', nargs='*'); ap.add_argument('--archive', nargs='*')
ap.add_argument('--sync-local')
a = ap.parse_args()
data = [entry(p, True) for p in files(a.samples)] + [entry(p, False) for p in files(a.archive)]
tpl = open(os.path.join(HERE, '..', 'assets', 'viewer_template.html'), encoding='utf8').read()
html = tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
open(a.out, 'w', encoding='utf8').write(html)
print('viewer:', a.out, f'{len(html)/1e6:.1f} MB', len(data), 'files')
if len(html) > 15e6: print('!! 16MB上限に近い。巨大建築は別ページに分けるか、葉を殻状にして減らす')
if a.sync_local:
    v = open(os.path.join(HERE, '..', 'assets', 'local_viewer.html'), encoding='utf8').read()
    line = 'const CK=' + json.dumps([[k, '#%06x' % c] for k, c in KEYWORDS_26 + KEYWORDS]) + ';'
    v = re.sub(r'const CK=\[.*?\];', lambda m: line, v, count=1)
    open(a.sync_local, 'w', encoding='utf8').write(v); print('local viewer:', a.sync_local)
