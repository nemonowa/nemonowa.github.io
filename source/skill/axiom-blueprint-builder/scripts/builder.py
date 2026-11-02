"""建築をプログラムで組み立てるためのヘルパー群。

  from builder import *
  b = Build()
  b.box(-3,0,-3,3,0,3,'stone_bricks')
  b.put(0,1,0,'oak_stairs',**ST('north'))
  b.save('/mnt/user-data/outputs/x.bp','名前',tags=['sample'])

方針:
- 座標は y が上、+z を「正面（南）」にする習慣にしておくとプレビューと説明が楽。
- 後から put したものが勝つ。「地形→構造→装飾→植栽→最後に空気を削る」の順で書く。
- 状態(プロパティ)は必ず正しく。不明なら references/techniques.md の『ブロック状態の落とし穴』を見る。
- 保存は既定で Minecraft 26.3 の Axiom 形式（bplib.FORMAT=2, DataVersion 5023）。chain→iron_chain などの改名は保存時に自動変換。
"""
import math, random
from bplib import write_bp, verify
from colors import unknown

# ---------------------------------------------------------------- 状態ヘルパー
SL = dict(type='bottom', waterlogged='false')          # 下ハーフ
SLT = dict(type='top', waterlogged='false')            # 上ハーフ
FN = dict(east='false', west='false', north='false', south='false', waterlogged='false')   # 柵/板ガラス（接続なし）
PANE_X = dict(east='true', west='true', north='false', south='false', waterlogged='false')
PANE_Z = dict(east='false', west='false', north='true', south='true', waterlogged='false')
WALL = dict(east='none', west='none', north='none', south='none', up='true', waterlogged='false')
LEAF = dict(distance='7', persistent='true', waterlogged='false')   # 葉は persistent=true 必須（消えないように）
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
DIR = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
def ST(facing, half='bottom', shape='straight'):
    """階段。facing=段の高い側（上り方向）"""
    return dict(facing=facing, half=half, shape=shape, waterlogged='false')
def DOOR(facing, half, hinge='left', open_='false'):
    return dict(facing=facing, half=half, hinge=hinge, open=open_, powered='false')

# ---------------------------------------------------------------- ノイズ
def h3(x, y, z):
    """座標ハッシュ（決定的な疑似乱数 0..65535）。材料のばらし・配置の間引きに使う"""
    return ((x*73856093) ^ (y*19349663) ^ (z*83492791)) & 0xffff
def noise(x, y, z, s=7.0):
    """なめらかな -1..1 の値。苔の分布、地形の起伏、輪郭の揺らぎに使う"""
    return (math.sin(x/s*1.7+math.cos(z/s*1.3)) + math.sin(z/s*1.9+y/s*.7) + math.sin(y/s*1.1+x/s*.5))/3
def pick(weights, x, y, z):
    """weights=[('name',重み),...] から座標ハッシュで選ぶ（材料ミックス）"""
    tot = sum(w for _, w in weights); r = h3(x, y, z) % tot; acc = 0
    for n, w in weights:
        acc += w
        if r < acc: return n

def bez(p0, p1, p2, p3, t):
    u = 1-t; return [u**3*a+3*u*u*t*b+3*u*t*t*c+t**3*d for a, b, c, d in zip(p0, p1, p2, p3)]

# ---------------------------------------------------------------- Build
class Build:
    def __init__(s): s.B = {}
    # 基本
    def put(s, x, y, z, n, **p):
        s.B[(int(x), int(y), int(z))] = (n if ':' in n else 'minecraft:'+n, tuple(sorted((k, str(v)) for k, v in p.items())))
    def get(s, x, y, z):
        v = s.B.get((int(x), int(y), int(z))); return v[0][10:] if v else None
    def rm(s, x, y, z): s.B.pop((int(x), int(y), int(z)), None)
    def empty(s, x, y, z): return (int(x), int(y), int(z)) not in s.B
    def put_if_empty(s, x, y, z, n, **p):
        if s.empty(x, y, z): s.put(x, y, z, n, **p)
    # 形
    def box(s, x0, y0, z0, x1, y1, z1, n, **p):
        for x in range(min(x0, x1), max(x0, x1)+1):
            for y in range(min(y0, y1), max(y0, y1)+1):
                for z in range(min(z0, z1), max(z0, z1)+1):
                    s.put(x, y, z, n(x, y, z) if callable(n) else n, **p)
    def clear(s, x0, y0, z0, x1, y1, z1):
        for x in range(min(x0, x1), max(x0, x1)+1):
            for y in range(min(y0, y1), max(y0, y1)+1):
                for z in range(min(z0, z1), max(z0, z1)+1): s.rm(x, y, z)
    def ring(s, x0, z0, x1, z1, y, n, **p):
        for x in range(x0, x1+1):
            for z in range(z0, z1+1):
                if x in (x0, x1) or z in (z0, z1): s.put(x, y, z, n(x, y, z) if callable(n) else n, **p)
    def disk(s, cx, cz, r, y, n, hollow=False, **p):
        for x in range(-int(r)-1, int(r)+2):
            for z in range(-int(r)-1, int(r)+2):
                d = math.hypot(x, z)
                if d <= r+.3 and (not hollow or d > r-1+.3): s.put(cx+x, y, cz+z, n(cx+x, y, cz+z) if callable(n) else n, **p)
    def sphere(s, cx, cy, cz, r, n, **p):
        ri = int(math.ceil(r))
        for dx in range(-ri, ri+1):
            for dy in range(-ri, ri+1):
                for dz in range(-ri, ri+1):
                    if dx*dx+dy*dy+dz*dz <= r*r:
                        X, Y, Z = int(round(cx+dx)), int(round(cy+dy)), int(round(cz+dz))
                        s.put(X, Y, Z, n(X, Y, Z) if callable(n) else n, **p)
    def tube(s, p0, p1, p2, p3, r0, r1, n, **p):
        """ベジェ曲線に沿って半径 r0→r1 の球を打つ。枝・根・尾・煙・パイプに万能"""
        L = sum(math.dist(bez(p0, p1, p2, p3, i/20), bez(p0, p1, p2, p3, (i+1)/20)) for i in range(20))
        k = max(4, int(L/0.7))
        for i in range(k+1):
            t = i/k; s.sphere(*bez(p0, p1, p2, p3, t), r0+(r1-r0)*t, n, **p)
        return bez(p0, p1, p2, p3, 1)
    def shell(s, cx, cy, cz, rx, ry, rz, n, inner=0.45, lumpy=0.2, skip=None, **p):
        """楕円体の殻（樹冠・ドーム・傘）。中身を詰めないのでブロック数と描画が軽い"""
        placed = []
        for dx in range(-int(rx)-2, int(rx)+3):
            for dz in range(-int(rz)-2, int(rz)+3):
                for dy in range(-int(ry)-3, int(ry)+3):
                    X, Y, Z = int(round(cx+dx)), int(round(cy+dy)), int(round(cz+dz))
                    d = (dx/rx)**2+(dz/rz)**2+((dy*(1.6 if dy < 0 else 1))/ry)**2 + lumpy*noise(X, Y, Z, 2.5)
                    if inner < d <= 1 and not (skip and (X, Y, Z) in skip):
                        s.put(X, Y, Z, n(X, Y, Z) if callable(n) else n, **p); placed.append((X, Y, Z))
        return placed
    # 建築部材
    def roof_layer(s, cx, cz, y, hx, hz, full='deepslate_tiles', stair='deepslate_tile_stairs', skip=None, hollow=False):
        """寄棟の1段。縁は内向きの階段、角はフルブロック。skip=(ax,az) の内側は置かない（上階の床が入る）"""
        for x in range(-hx, hx+1):
            for z in range(-hz, hz+1):
                ex, ez = abs(x) == hx, abs(z) == hz
                if skip and abs(x) <= skip[0] and abs(z) <= skip[1]: continue
                if hollow and not (ex or ez): continue
                if ex and ez: s.put(cx+x, y, cz+z, full)
                elif ez: s.put(cx+x, y, cz+z, stair, **ST('south' if z < 0 else 'north'))
                elif ex: s.put(cx+x, y, cz+z, stair, **ST('east' if x < 0 else 'west'))
                else: s.put(cx+x, y, cz+z, full)
    def hip_roof(s, cx, cz, y, hx, hz, full='deepslate_tiles', stair='deepslate_tile_stairs', slab='deepslate_tile_slab', upturn=True):
        """寄棟/宝形屋根を一気に。upturn=Trueで隅を反らせる（和風・中華風）"""
        if upturn:
            for sx in (-1, 1):
                for sz in (-1, 1): s.put(cx+sx*(hx+1), y+1, cz+sz*(hz+1), slab, **SL)
        k = 0
        while hx-k >= 0 and hz-k >= 0:
            s.roof_layer(cx, cz, y+k, hx-k, hz-k, full, stair, hollow=True); k += 1
        for x in range(-(hx-k+1) if hx > hz else 0, (hx-k+2) if hx > hz else 1):
            s.put(cx+x, y+k, cz, slab, **SL)
        return y+k
    def flight(s, x0, z, y0, n, facing='east'):
        """まっすぐな階段。y0 から n 段、facing 方向へ上る。頭上3マスを空ける"""
        dx, dz = DIR[facing]
        for i in range(n):
            x, zz = x0+dx*i, z+dz*i
            s.put(x, y0+i, zz, 'spruce_stairs', **ST(facing))
            for k in (1, 2, 3): s.rm(x, y0+i+k, zz)
    def hanging(s, x, y, z, length, kind='weeping'):
        """垂れ下がる蔓。kind: weeping(赤) / cave(グロウベリー緑) / twisting(上向き)。途中で物に当たったら止める"""
        for k in range(1, length+1):
            Y = y-k if kind != 'twisting' else y+k
            nxt = Y-1 if kind != 'twisting' else Y+1
            if not s.empty(x, Y, z): break
            last = k == length or not s.empty(x, nxt, z)
            if kind == 'weeping': s.put(x, Y, z, 'weeping_vines' if last else 'weeping_vines_plant', **({'age': '25'} if last else {}))
            elif kind == 'twisting': s.put(x, Y, z, 'twisting_vines' if last else 'twisting_vines_plant', **({'age': '25'} if last else {}))
            else: s.put(x, Y, z, 'cave_vines' if last else 'cave_vines_plant', berries='true' if h3(x, Y, z) % 3 == 0 else 'false', **({'age': '25'} if last else {}))
            if last: break
    def rope(s, a, b, sag, lantern_every=5):
        """2点間に垂れた鎖を渡し、提灯を吊るす"""
        n = int(math.dist(a, b)*1.6)
        for i in range(n+1):
            t = i/n; x = a[0]+(b[0]-a[0])*t; z = a[2]+(b[2]-a[2])*t; y = a[1]+(b[1]-a[1])*t-sag*4*t*(1-t)
            X, Y, Z = int(round(x)), int(round(y)), int(round(z))
            if s.empty(X, Y, Z):
                s.put(X, Y, Z, 'iron_chain', axis='x' if abs(b[0]-a[0]) > abs(b[2]-a[2]) else 'z', waterlogged='false')
                if i % lantern_every == 2 and s.empty(X, Y-1, Z): s.put(X, Y-1, Z, 'lantern', hanging='true', waterlogged='false')
    def ground_cover(s, plants, every=7, on=('grass_block', 'moss_block', 'podzol')):
        """地表の最上段に草花を散らす。plants=['short_grass','fern',...]"""
        top = {}
        for (x, y, z) in s.B:
            if y > top.get((x, z), -999): top[(x, z)] = y
        for (x, z), y in top.items():
            if s.get(x, y, z) in on and h3(x, y, z) % every == 0:
                n = plants[h3(z, y, x) % len(plants)]
                extra = {'facing': 'north', 'flower_amount': str(1+h3(x, 1, z) % 4)} if n == 'pink_petals' else {}
                s.put(x, y+1, z, n, **extra)
    # 出力
    def save(s, path, name, author='nemo', tags=('sample',), **kw):
        """kw は bplib.write_bp へ（fmt=2 既定=26.3形式 / origin='min'|'bottom_center'|'keep' / paste_air / data_version）。
        s.BE（ブロックエンティティ）と s.ENT（エンティティ）があれば一緒に書く"""
        miss = unknown(v[0] for v in s.B.values())
        if miss: print('[colors] 未定義の色（プレビューでマゼンタ表示）:', miss)
        n = write_bp(path, s.B, name, author=author, tags=tags, block_entities=getattr(s, 'BE', None),
                     entities=getattr(s, 'ENT', None), **kw)
        ok, cnt, _ = verify(path, n)
        ys = [k[1] for k in s.B]
        print(f'{name}: {n} blocks, height {max(ys)-min(ys)+1}, verify={"OK" if ok else "NG"} -> {path}')
        return n
