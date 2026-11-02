"""ISS × スペースシャトル 合体シーン（1ブロック=1m）。シャトルの ODS を ISS の Harmony 前方 PMA-2 に接続。
向き: 貨物室がISS側(-z)、尾部=天底(-y)、機首=天頂(+y)（STS-110 事前報道の姿勢）。軸の入れ替え: X=ox, Y=oz-21, Z=56-oy。"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(SK, 'scripts'))
from space_helpers import *
from interior_helpers import *
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

def run(path, tmp, marker):
    src = open(path, encoding='utf8').read(); src = src[:src.index(marker)]
    g = {'__file__': path, '__name__': 'sub'}; sys.argv = [sys.argv[0], tmp]
    exec(compile(src, path, 'exec'), g); return g
gi = run(os.path.join(SK, 'examples', 'iss', 'iss.py'), '/tmp/_iss', "b.save(os.path.join(OUT, 'ISS_1m.bp')")
gs = run(os.path.join(SK, 'examples', 'shuttle', 'shuttle.py'), '/tmp/_sh', "# ---- 本と看板")
b, sh = gi['b'], gs['b']

# 1. 合体のため、ISS 前方の Dragon と Harmony 天底の Cygnus を外す
b.clear(-3, -3, 51, 3, 3, 58); b.clear(-3, -9, 42, 3, -3, 48)
# 2. シャトルを回して取り込む（階段・はしご・看板・ドア等は向きが表せないので外観用に置換）
def conv(name, props):
    n = name[10:]
    if n.endswith('_stairs') or n in ('ladder', 'end_rod', 'lectern') or n.endswith('_sign'): return None
    if n.endswith('_door'): return 'smooth_quartz', {}
    return n, dict(props)
over = 0
for (ox, oy, oz), (name, props) in sh.B.items():
    r = conv(name, props)
    if r is None: continue
    p = (ox, oz-21, 56-oy)
    if p in b.B: over += 1
    b.put(*p, r[0], **r[1])
print('ISSと重なったセル数:', over)
# 3. 船内への穴は閉じ、PMA-2⇔ODS だけを開ける
b.box(-1, 2, 57, 1, 3, 58, 'smooth_quartz')
b.clear(-1, -1, 50, 1, 1, 50); b.clear(-1, -1, 52, 1, 1, 52); b.clear(0, 0, 51, 0, 0, 51)
for z in (54, 57): b.put(0, 1, z, 'end_rod', facing='down')
# 4. ODS 内の本と看板
pages = ['合体シーン\n\nISSの Harmony 前方\n(PMA-2)にシャトルの\nODSを接続\n\n向き: 尾部=地球側(下)\n貨物室=ISS側\n機首=天頂(上)',
         '歩けるのはここまで\nISS各モジュール→PMA-2\n→ODS(ここ)\n\nシャトル船内は向きの都合で入れません\n(単体版は歩けます)',
         '省略・近似\n・Dragon/Cygnusは外した\n・尾翼がHarmony下に\n伸びる\n・ロール方向は簡略化\n・角の面取りは省略\n(出典: NASA/ESA/SFN)']
extra_cmd = lectern_with_book(b, -1, -1, 55, 'east', 'ISS×シャトル 合体', pages)
wall_sign(b, -1, 0, 55, 'east', ['ODS', 'シャトル側', 'ISSと接続中', ''])
# 5. 検証
ALLOWED = gi['ALLOWED'] + [((-1, -1, 50), (1, 1, 58))]
PROBES = dict(gi['PROBES']); PROBES.update(ODS_mid=(0, 0, 55), ODS_end=(0, -1, 58))
res = check_interior(b, (0, 0, 37), ALLOWED, PROBES)
print('内部: 密閉=%s セル数=%d 未到達=%s' % (res['sealed'], res['cells'], res['unreachable']))
if not res['sealed']: print('漏れ経路(外→内):', res['leak_path'])
mn = [min(k[i] for k in b.B) for i in range(3)]; mx = [max(k[i] for k in b.B) for i in range(3)]
print('size', [mx[i]-mn[i]+1 for i in range(3)], 'min', mn)
open(os.path.join(OUT, 'iss_shuttle_books_commands.txt'), 'w', encoding='utf8').write(
    '# ISS×シャトル 合体シーンの本(26.3 /give)\n' + '\n\n'.join(gi['BOOK_CMD'] + [extra_cmd]) + '\n')
b.save(os.path.join(OUT, 'ISS_Shuttle_1m.bp'), 'ISS × スペースシャトル 合体 (1block=1m)', tags=['space', 'iss', 'shuttle', 'scale-1m'])
for (lx, lz, fc) in gi['LEC']: b.put(lx, -1, lz, 'lectern', facing=fc, has_book='false', powered='false')
b.put(-1, -1, 55, 'lectern', facing='east', has_book='false', powered='false')
b.BE = []
b.save(os.path.join(OUT, 'ISS_Shuttle_1m_noBE.bp'), 'ISS × スペースシャトル 合体 (1block=1m, BEなし)', tags=['space', 'iss', 'shuttle', 'scale-1m'])
