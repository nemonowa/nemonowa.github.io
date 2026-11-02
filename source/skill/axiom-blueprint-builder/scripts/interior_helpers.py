"""内部を持つ大型建築の検証・本/看板ヘルパー。
- check_interior(): 『内部が密閉されているか』『全部屋が歩いて繋がっているか』を Build.B（ワールド座標）で検査。
  ※ .bp を読み戻して検査すると座標が最小角基準になりオフセットを間違えやすい（ISSで実際に誤判定した）。必ず b.B で行う。
- lectern_with_book(): 書見台+written_book の BlockEntity と /give コマンド
- wall_sign(): 文字入りの壁看板（BlockEntity）
書式は 26.3（DataVersion 5023）：本は written_book_content コンポーネント、看板の文字は NBT テキスト（nbt_helpers.py）。
書見台・看板の BE の Axiom 実機読み込みは未確認なので、必ず『BEなし版』と『/give コマンド』を併せて出すこと。
"""
import json
from collections import deque
from builder import *
import nbt_helpers as NH

def _box(b0, b1): return tuple(min(a, c) for a, c in zip(b0, b1)), tuple(max(a, c) for a, c in zip(b0, b1))

def check_interior(b, start, allowed, probes=None, passable=('ladder', 'end_rod', 'lantern'), margin=3):
    """start から空気（と passable ブロック）を6近傍で広げ、allowed（意図した内部の箱 ((x0,y0,z0),(x1,y1,z1)) のリスト）の外に
    出たら漏れ。ハッチで除去した殻の穴・外へ開く意図的な窓付き空間（Cupola 等）も allowed に含めること。
    戻り値 dict(sealed, cells, leak_path(外→内の末尾8点), unreachable[名前]) 。probes={名前:座標}"""
    boxes = [_box(*a) for a in allowed]
    inside = lambda c: any(all(p[0][i] <= c[i] <= p[1][i] for i in range(3)) for p in boxes)
    ok = lambda c: c not in b.B or b.get(*c) in passable or str(b.get(*c)).split('[')[0] in passable
    lo = [min(k[i] for k in b.B)-margin for i in range(3)]; hi = [max(k[i] for k in b.B)+margin for i in range(3)]
    par = {tuple(start): None}; q = deque([tuple(start)]); hit = None
    while q and not hit:
        p = q.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (p[0]+d[0], p[1]+d[1], p[2]+d[2])
            if n in par or not ok(n) or any(n[i] < lo[i] or n[i] > hi[i] for i in range(3)): continue
            par[n] = p; q.append(n)
            if not inside(n): hit = n; break
    path = []
    p = hit
    while p and len(path) < 8: path.append(p); p = par[p]
    miss = [k for k, c in (probes or {}).items() if tuple(c) not in par] if not hit else list((probes or {}).keys())
    return dict(sealed=hit is None, cells=len(par), leak_path=path, unreachable=miss)

def book_page(text): return json.dumps({'text': text}, ensure_ascii=False)   # 旧(1.20.4)形式の JSON 文字列。互換のため残す

def give_book_command(title, pages, author='nemo'):
    """26.3 の /give（written_book_content コンポーネント構文）"""
    return NH.give_book_command(title, pages, author)

def lectern_with_book(b, x, y, z, facing, title, pages, author='nemo'):
    """書見台(has_book=true)と BE を置く。facing は『本を読む人のいる側』（壁際なら部屋の内側）。ページは1枚 約13字×14行まで。
    戻り値は /give コマンド。BEなし版を作るときは has_book='false' で置き直し、b.BE=[] にして保存する。"""
    if not hasattr(b, 'BE'): b.BE = []
    b.put(x, y, z, 'lectern', facing=facing, has_book='true', powered='false')
    b.BE.append(NH.lectern(x, y, z, title, pages, author))
    return give_book_command(title, pages, author)

def wall_sign(b, x, y, z, facing, lines, block='oak_wall_sign', color='black', waxed=True, glow=False):
    """壁看板。facing は看板の向き＝壁から離れる向き（北の壁に貼るなら south）。lines は4行まで"""
    if not hasattr(b, 'BE'): b.BE = []
    b.put(x, y, z, block, facing=facing, waterlogged='false')
    b.BE.append(NH.sign(x, y, z, lines, color=color, glow=glow, waxed=waxed, hanging='hanging' in block))
