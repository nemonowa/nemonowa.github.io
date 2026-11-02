"""ダンジョン作成キット（Build と併用）。
流れ: carve（空間を掘る）→ line（内張りで密閉）→ 仕掛け・宝箱・照明 → check_leaks → solve（攻略可能性の検証）→ render_map（攻略マップ）→ block_entities / export_commands。

重要な約束（references/dungeon.md に根拠つき）
- 扉は「鉄の扉 + 隣接マスのレバー」。**レバーは必ず扉の両側（行きと帰り）に、床ではなく壁に付ける**（`door_levers()` が両側を自動で置く）。片側だけだと戻れなくなる。赤石配線は使わない。
- 隠し蓋は トラップドア half='top'（床面と面一）＋その下にハシゴ。
- 水の中にレバー/ボタン/感圧板/カーペット/松明/赤石は置かない（水で壊れる）。
- 溶岩は床面と面一（床ブロックの y に置く）。水平にしか広がらないので、壁・床で囲えば流れ出ない。
- 宝箱の中身・スポナーは BlockEntities（block_entities()）で BP に直接書ける。
"""
import sys, os, math, random
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from builder import *

AXIS = dict(east=(1, 0), west=(-1, 0), south=(0, 1), north=(0, -1))
DIRNAME = {v: k for k, v in AXIS.items()}
DIRS6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
WALL_T = [('stone_bricks', 56), ('mossy_stone_bricks', 20), ('cracked_stone_bricks', 10), ('deepslate_bricks', 14)]
CEIL_T = [('stone_bricks', 60), ('mossy_stone_bricks', 14), ('deepslate_tiles', 26)]

# 1.20.4 で確認済みの宝箱ルートテーブル（minecraft:chests/...）
LOOT = dict(easy='simple_dungeon', jungle='jungle_temple', gold='ruined_portal', mansion='woodland_mansion',
            rich='bastion_treasure', end='end_city_treasure', ancient='ancient_city', village='village/village_plains_house',
            mineshaft='abandoned_mineshaft', desert='desert_pyramid', library='stronghold_library',
            # 以下は Paper の LootTables 列挙／Minecraft Wiki の一覧にある名前（○。ルートテーブル名として存在する。実機での中身確認は未）
            ice_box='ancient_city_ice_box', bastion_bridge='bastion_bridge', bastion_stable='bastion_hoglin_stable', bastion='bastion_other',
            buried='buried_treasure', igloo='igloo_chest', outpost='pillager_outpost', nether_bridge='nether_bridge',
            shipwreck='shipwreck_supply', shipwreck_treasure='shipwreck_treasure', shipwreck_map='shipwreck_map',
            stronghold='stronghold_corridor', stronghold_cross='stronghold_crossing', ruin_small='underwater_ruin_small', ruin_big='underwater_ruin_big',
            jungle_trap='jungle_temple_dispenser', bonus='spawn_bonus_chest',
            trial_supply='trial_chambers/supply', trial_reward='trial_chambers/reward', trial_corridor='trial_chambers/corridor',
            trial_entrance='trial_chambers/entrance', trial_intersection='trial_chambers/intersection')


def facing_to(a, b_):
    """セル a(x,z) から b_(x,z) へ向かう水平方向名（階段の facing=上る方向 に使う）"""
    dx, dz = b_[0]-a[0], b_[1]-a[1]
    return 'east' if dx > 0 else 'west' if dx < 0 else 'south' if dz > 0 else 'north'


# ---------------------------------------------------------------- ブロックエンティティ（NBT）
def chest_be(x, y, z, loot='simple_dungeon'):
    """宝箱：LootTable を書く。loot は LOOT のキーでも 'chests/…' でもよい"""
    path = LOOT.get(loot, loot)
    if not path.startswith('chests/'): path = 'chests/' + path
    return (x, y, z, {'id': (8, 'minecraft:chest'), 'LootTable': (8, 'minecraft:' + path)})


def spawner_be(x, y, z, mob='zombie', count=2, near=5, rng=6, player=14, delay=(200, 600), light=None):
    """スポナー。BE の id は minecraft:mob_spawner（ブロック名は minecraft:spawner）。
    1.18+ の形式 SpawnData:{entity:{id}} / SpawnPotentials:[{weight,data:{entity,custom_spawn_rules}}]（26.3 実ファイルでも同じキー・型）。
    名前・体力・ドロップを付けたい時は nbt_helpers.spawner(…, name=, health=, loot=) を使う。
    light=(min,max) を渡すと custom_spawn_rules.block_light_limit で明るい部屋でも湧く（既定は mob 本来の湧き条件）。"""
    ent = (10, {'id': (8, 'minecraft:' + mob)})
    data = {'entity': ent}
    if light: data['custom_spawn_rules'] = (10, {'block_light_limit': (10, {'min_inclusive': (3, light[0]), 'max_inclusive': (3, light[1])})})
    return (x, y, z, {'id': (8, 'minecraft:mob_spawner'),
                      'SpawnData': (10, dict(data)),
                      'SpawnPotentials': (9, (10, [{'weight': (3, 1), 'data': (10, data)}])),
                      'SpawnRange': (2, rng), 'RequiredPlayerRange': (2, player), 'MaxNearbyEntities': (2, near),
                      'SpawnCount': (2, count), 'MinSpawnDelay': (2, delay[0]), 'MaxSpawnDelay': (2, delay[1]), 'Delay': (2, 20)})


class Dungeon:
    def __init__(self, b, line_skip_y=None):
        self.b = b; self.D = set(); self.chests = []; self.spawners = []; self.doors = []; self.levers = []; self.door_axis = {}; self.lever_info = {}
        self.line_skip_y = line_skip_y     # この y 以上のセルは内張りしない（地上の建物に触れないため）
        self.no_line = set()               # 内張りしないセル（外へ開く入口の外側など）。check_leaks でも無視される
        self._post = []                    # line() の後に置く部品（螺旋階段の段など。内張りに上書きされないため）

    # ---- 掘る
    def carve(self, x0, y0, z0, x1, y1, z1):
        for x in range(min(x0, x1), max(x0, x1)+1):
            for y in range(min(y0, y1), max(y0, y1)+1):
                for z in range(min(z0, z1), max(z0, z1)+1):
                    self.D.add((x, y, z)); self.b.rm(x, y, z)

    def disc(self, cx, cz, r, y0, y1):
        for x in range(int(cx-r)-1, int(cx+r)+2):
            for z in range(int(cz-r)-1, int(cz+r)+2):
                if (x-cx)**2+(z-cz)**2 <= r*r: self.carve(x, y0, z, x, y1, z)

    # ---- 内張り（天井・床・壁を1枚張って密閉。外の岩はそのまま）
    def line(self, wall=WALL_T, ceil=CEIL_T, floor=None):
        for (x, y, z) in list(self.D):
            for dx, dy, dz in DIRS6:
                n = (x+dx, y+dy, z+dz)
                if n in self.D or n in self.no_line or (self.line_skip_y is not None and n[1] >= self.line_skip_y): continue
                if dy == -1: nm = ('polished_andesite' if (x+z) % 2 == 0 else pick(wall, *n)) if floor is None else pick(floor, *n)
                elif dy == 1: nm = pick(ceil, *n)
                else: nm = pick(wall, *n)
                self.b.put(*n, nm)
        for (x, y, z, nm, p) in self._post: self.b.put(x, y, z, nm, **p)
        self._post = []

    # ---- 区画ごとに素材を変えて内張り（幹の中は木、地下は石、など）
    def section(self, name):
        """`with dg.section('tree'): …` の間に掘ったセルを区画 name として記録する。\n        同じ区画名で何度でも使える。素材は line_sections() で区画ごとに指定する。"""
        dg = self
        class _Section:
            def __enter__(s): s.before = set(dg.D)
            def __exit__(s, *a): dg.__dict__.setdefault('sections', {}).setdefault(name, set()).update(dg.D - s.before)
        return _Section()

    def line_sections(self, styles):
        """styles={区画名:(wall, ceil, floor)} 。各リストは pick() 用の [(ブロック名, 重み)…]。未指定の区画は line() の既定。\n        戻り値=『内張りの時点で空気だった』セルのリスト（幹・壁の外へ内張りが突き出す場所の候補。幹の部屋では 0〜数個が目安、多ければ部屋が外壁に近すぎる）。\n        内部で _post（螺旋の階段など）も書き出すので line() の代わりに1回だけ呼ぶ。"""
        protruding = []
        for name, cells in self.__dict__.get('sections', {}).items():
            wall, ceil, floor = styles.get(name, (WALL_T, CEIL_T, None))
            for (x, y, z) in sorted(cells):
                for dx, dy, dz in DIRS6:
                    n = (x+dx, y+dy, z+dz)
                    if n in self.D or n in self.no_line or (self.line_skip_y is not None and n[1] >= self.line_skip_y): continue
                    if self.b.empty(*n): protruding.append(n)
                    if dy == -1: nm = ('polished_andesite' if (x+z) % 2 == 0 else pick(wall, *n)) if floor is None else pick(floor, *n)
                    elif dy == 1: nm = pick(ceil, *n)
                    else: nm = pick(wall, *n)
                    self.b.put(*n, nm)
        for (x, y, z, nm, p) in self._post: self.b.put(x, y, z, nm, **p)
        self._post = []
        return protruding

    def check_leaks(self):
        """掘った空間の6近傍が空（外気）のまま残っていないか。0 が合格"""
        n = 0
        for (x, y, z) in self.D:
            for dx, dy, dz in DIRS6:
                m = (x+dx, y+dy, z+dz)
                if m not in self.D and m not in self.no_line and not (self.line_skip_y is not None and m[1] >= self.line_skip_y) and self.b.empty(*m): n += 1
        return n

    # ---- 開口（外へ通じる入口）：外側の隣接セルを内張り対象から外す
    def open_end(self, cells):
        """入口の外側など『わざと外気に開ける』セルを登録（line しない・漏れ判定から除外）"""
        self.no_line.update(cells)

    # ---- 迷路（セル格子＋DFS。入口/出口は外壁を抜く）
    def maze(self, x0, z0, cx, cz, y0, y1, entrance, exit_, seed=1, min_path=0, wall=None):
        """外寸 (2cx+1)×(2cz+1)。セル中心は奇数オフセット。entrance/exit_=(side,idx) side∈'N','S','E','W'、idx=その辺に沿ったセル番号。
        min_path 以上の長さの解になる seed を探索する。壁はこの場で置く（line より前に呼ぶ）。
        戻り値: dict(start,goal,entrance,exit,path_len,seed,cell(i,j)->(x,z) 用の関数 cellxz)"""
        W, H = 2*cx+1, 2*cz+1
        wall = wall or WALL_T
        self.carve(x0, y0, z0, x0+W-1, y1, z0+H-1)
        def cell(side, idx):
            return {'N': (idx, 0), 'S': (idx, cz-1), 'W': (0, idx), 'E': (cx-1, idx)}[side]
        def opening(side, idx):
            return {'N': (2*idx+1, 0), 'S': (2*idx+1, H-1), 'W': (0, 2*idx+1), 'E': (W-1, 2*idx+1)}[side]
        si, sj = cell(*entrance); gi, gj = cell(*exit_)
        for sd in range(seed, seed+400):
            rnd = random.Random(sd)
            walls = {(ox, oz) for ox in range(W) for oz in range(H) if ox % 2 == 0 or oz % 2 == 0}
            seen = {(si, sj)}; stack = [(si, sj)]; depth = {(si, sj): 0}
            while stack:
                i, j = stack[-1]
                nb = [(i+di, j+dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= i+di < cx and 0 <= j+dj < cz and (i+di, j+dj) not in seen]
                if not nb: stack.pop(); continue
                ni, nj = rnd.choice(nb); seen.add((ni, nj)); stack.append((ni, nj)); depth[(ni, nj)] = depth[(i, j)]+1
                walls.discard((i+ni+1, j+nj+1))
            if depth[(gi, gj)] >= min_path: break
        eo, xo = opening(*entrance), opening(*exit_)
        walls.discard(eo); walls.discard(xo)
        for (ox, oz) in walls:
            for y in range(y0, y1+1): self.b.put(x0+ox, y, z0+oz, pick(wall, x0+ox, y, z0+oz))
        xz = lambda i, j: (x0+2*i+1, z0+2*j+1)
        return dict(start=xz(si, sj), goal=xz(gi, gj), entrance=(x0+eo[0], z0+eo[1]), exit=(x0+xo[0], z0+xo[1]),
                    path_len=depth[(gi, gj)], seed=sd, cellxz=xz)

    # ---- 3×3 の螺旋階段（中心は柱）。ほぼ 3×3 の敷地で 8段ごとに1周
    RING8 = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]   # 時計回り（z+ が南）
    def spiral(self, cx, cz, y0, n, entry, up=True, rot=-1, headroom=5, stair='stone_brick_stairs', pillar='stone_bricks', floor='stone_bricks'):
        """entry=(x,z)：環上の入口セル（床 y0 の平らなセル。呼び出し側で掘って床を作る）。
        k=1..n の段は entry から rot(+1=時計回り/-1=反時計)方向へ、y0±k に階段ブロック。
        着地セルは k=n+1 番目の環セルで、床ブロックは y0±n（→ 次の階の床の高さ）。
        上り(up=True)は階段の facing=進む先のセル、下りは facing=前のセル。段と着地床は line() の後に置かれる。
        戻り値: dict(landing=(x,z), floor_y)"""
        e = self.RING8.index((entry[0]-cx, entry[1]-cz))
        sg = 1 if up else -1
        for k in range(1, n+1):
            i = (e+rot*k) % 8; x, z = cx+self.RING8[i][0], cz+self.RING8[i][1]; y = y0+sg*k
            tgt = self.RING8[(i+rot) % 8] if up else self.RING8[(i-rot) % 8]
            face = facing_to((x, z), (cx+tgt[0], cz+tgt[1]))
            self.carve(x, y+1, z, x, y+headroom, z)
            self._post.append((x, y, z, stair, ST(face)))
        i = (e+rot*(n+1)) % 8; lx, lz = cx+self.RING8[i][0], cz+self.RING8[i][1]; ly = y0+sg*n
        self.carve(lx, ly+1, lz, lx, ly+headroom, lz); self._post.append((lx, ly, lz, floor, {}))
        for y in range(min(y0, ly)+1, max(y0, ly)+1): self._post.append((cx, y, cz, pillar, {}))
        return dict(landing=(lx, lz), floor_y=ly)

    # ---- 部品
    def lantern(self, x, y, z, soul=False):            # 天井に吊る（直上が天井ブロックのとき）
        self.b.put(x, y, z, 'soul_lantern' if soul else 'lantern', hanging='true', waterlogged='false')

    def chest(self, x, y, z, face='north', loot='easy', tag=None):
        self.b.put(x, y, z, 'chest', facing=face, type='single', waterlogged='false'); self.chests.append((x, y, z, tag or loot, loot))

    def door(self, x, y, z, face):                       # y=下半分の高さ。face は通路の軸方向（東西の通路なら east/west、南北なら north/south）
        self.b.put(x, y, z, 'iron_door', **DOOR(face, 'lower')); self.b.put(x, y+1, z, 'iron_door', **DOOR(face, 'upper'))
        self.doors.append((x, y, z)); self.door_axis[(x, y, z)] = AXIS[face]

    def lever(self, x, y, z, face, attach=None):         # 壁付け専用。face=壁から離れる向き（ハシゴと同じ）。背後 (x-fx, y, z-fz) が壁ブロックであること
        fx, fz = AXIS[face]; ax, az = (x-fx, z-fz) if attach is None else attach
        self.b.put(x, y, z, 'lever', face='wall', facing=face, powered='false')
        self.levers.append((x, y, z)); self.lever_info[(x, y, z)] = (face, (ax, y, az))

    def door_levers(self, x, y, z, face):
        """鉄の扉＋**両側**の壁レバー（行きも帰りも開けられる）。レバーは目の高さ（y+1）で、扉の隣の通路マスの側壁に付ける。
        側壁が無い（部屋に面した扉など）側は、扉と同じ壁面の扉の隣の壁ブロックに付ける。どちらも作れなければ ValueError。"""
        self.door(x, y, z, face); ax, az = AXIS[face]; px, pz = -az, ax
        for sgn in (1, -1):
            done = False
            cx, cz = x+ax*sgn, z+az*sgn                          # 扉の隣の通路マス
            for q in (1, -1):                                    # 1) 通路マスの側壁
                if self._free_cell(cx, y+1, cz) and self._wall_cell(cx+px*q, y+1, cz+pz*q):
                    self.lever(cx, y+1, cz, DIRNAME[(-px*q, -pz*q)]); done = True; break
            if done: continue
            for q in (1, -1):                                    # 2) 扉と同じ壁面の、扉の隣の壁ブロック
                wx, wz = x+px*q, z+pz*q
                if self._wall_cell(wx, y+1, wz) and self._free_cell(wx+ax*sgn, y+1, wz+az*sgn):
                    self.lever(wx+ax*sgn, y+1, wz+az*sgn, DIRNAME[(ax*sgn, az*sgn)], attach=(wx, wz)); done = True; break
            if not done: raise ValueError(f'door_levers: 扉 {(x, y, z)} の {"前" if sgn > 0 else "後"}側にレバーを付ける壁が無い')

    # レバーを付けられない／動力を伝えられない（完全な不透明ブロックでない）もの。階段・ハーフ・ガラス・葉・柵・壁など
    NOT_STURDY = ('stairs', 'slab', 'glass', 'leaves', 'fence', '_wall', 'pane', 'bars', 'trapdoor', 'door', 'chain', 'lantern', 'torch', 'carpet',
                  'pot', 'sign', 'banner', 'head', 'skull', 'button', 'ladder', 'vine', 'scaffolding', 'candle', 'fire', 'lava', 'water', 'cobweb',
                  'lectern', 'chest', 'bed', 'anvil', 'spawner', 'lever', 'campfire', 'dripstone', 'rail', 'flower', 'grass', 'fern', 'sapling', 'ice',
                  'soul_sand', 'mud', 'honey', 'slime', 'cake', 'hopper', 'cauldron', 'enchanting', 'end_rod', 'lightning_rod', 'amethyst_cluster', 'bell')

    def _wall_cell(self, x, y, z):
        """レバーを付けられる『面が固い』壁ブロックか（石レンガなどの完全ブロック）。階段・ハーフ・ガラス等は不可（Wiki: レバーが強く動力を渡すのは完全な不透明ブロックの取り付け先だけ）"""
        n = self.b.get(x, y, z)
        return bool(n) and not any(k in n.replace('minecraft:', '') for k in self.NOT_STURDY)

    def _free_cell(self, x, y, z):
        return self.b.get(x, y, z) is None

    def check_doors(self):
        """扉とレバーの約束を機械検査して問題の一覧を返す（空なら合格）。
        ① 扉の両側にレバーがある ② レバーは壁付け（face=wall）で背後が固体 ③ レバーは扉に隣接する（レバー自身か取り付け先が扉に接する）"""
        bad = []
        for d in self.doors:
            ax, az = self.door_axis.get(d, (0, 0)); x, y, z = d
            for sgn in (1, -1):
                ok = False
                for l in self.levers:
                    lx, ly, lz = l
                    if ly in (y, y+1) and (lx-x)*ax+(lz-z)*az == sgn and abs((lx-x)*az)+abs((lz-z)*ax) <= 1 and self._powers(l, d): ok = True
                if not ok: bad.append(f'扉{d}: {"前" if sgn > 0 else "後"}側にレバーが無い（片側だけだと帰れない）')
        for l, (face, att) in self.lever_info.items():
            n = self.b.get(*l)
            if not (n and 'lever' in n): bad.append(f'レバー{l}: ブロックが無い'); continue
            if not self._wall_cell(*att): bad.append(f'レバー{l}: 背後{att}が壁ブロックではない（床置き・空中は不可）')
        for l in self.levers:
            if l not in self.lever_info: bad.append(f'レバー{l}: 壁付けの lever() で作られていない')
        return bad

    def check_return(self, start):
        """『帰れる』の機械検査。各扉について、扉を閉じたまま（他の扉は開けた状態で）扉の両側それぞれから歩いて、その側のレバーの足元に着けるかを調べる。
        戻り値は問題の一覧（空なら合格）。扉の片側にレバーが無い／レバーの前に危険地帯があって届かない、を検出する。"""
        bad = []
        for d in self.doors:
            ax, az = self.door_axis.get(d, (0, 0)); x, y, z = d
            od = set(self.doors) - {d}
            for sgn in (1, -1):
                st = (x+ax*sgn, y, z+az*sgn)
                R = self._bfs(st, od) if self._free(st[0], st[1], st[2], od) else set()
                ok = any(self._powers(l, d) and (l[0], l[1]-1, l[2]) in R and (l[0]-x)*ax+(l[2]-z)*az == sgn for l in self.levers)
                if not ok: bad.append(f'扉{d}: {"前" if sgn > 0 else "後"}側から歩いてレバーに届かない（反対側から来ると戻れない）')
        return bad

    def _powers(self, l, d):
        """レバー l が扉 d（下半分 d・上半分 d+1）に動力を渡すか。レバー自身、または取り付け先の壁ブロックが扉に面で接する"""
        att = self.lever_info.get(l, (None, None))[1]
        cells = [l] + ([att] if att else [])
        return any(abs(c[0]-h[0])+abs(c[1]-h[1])+abs(c[2]-h[2]) == 1 for c in cells for h in (d, (d[0], d[1]+1, d[2])))

    def ladder(self, x, y0, y1, z, face):                # face=「壁から離れる向き」（南の壁に付けるなら 'north'）
        for y in range(y0, y1+1): self.b.put(x, y, z, 'ladder', facing=face, waterlogged='false')

    def hatch(self, x, y, z, face='north'):               # 床面と面一の隠し蓋（下にハシゴ）
        self.b.put(x, y, z, 'dark_oak_trapdoor', facing=face, half='top', open='false', powered='false', waterlogged='false')

    def spawner(self, x, y, z, mob='zombie', **kw):
        self.b.put(x, y, z, 'spawner'); self.spawners.append((x, y, z, mob, kw))

    def spike_pit(self, x0, z0, x1, z1, y_floor, depth, density=2, bridge_cells=()):
        """棘の穴：床を落として底に鍾乳石(pointed_dripstone)。着地すると落下距離が2倍で判定される（要注意）。"""
        self.carve(x0, y_floor-depth+1, z0, x1, y_floor, z1)
        for x in range(min(x0, x1), max(x0, x1)+1):
            for z in range(min(z0, z1), max(z0, z1)+1):
                if h3(x, 1, z) % density == 0: self.b.put(x, y_floor-depth+1, z, 'pointed_dripstone', thickness='tip', vertical_direction='up', waterlogged='false')
        for (x, z) in bridge_cells:
            self.b.rm(x, y_floor-depth+1, z); self.b.put(x, y_floor, z, 'cracked_stone_bricks')

    def lava_lake(self, x0, z0, x1, z1, y_surface, depth=2):
        """溶岩の湖：床面(y_surface)と面一。底(y_surface-depth)は line() が作る"""
        self.carve(x0, y_surface-depth+1, z0, x1, y_surface, z1)
        for x in range(min(x0, x1), max(x0, x1)+1):
            for z in range(min(z0, z1), max(z0, z1)+1):
                for y in range(y_surface-depth+1, y_surface+1): self.b.put(x, y, z, 'lava', level='0')

    # ---- 出力
    def block_entities(self, default_loot='village'):
        be = []
        for (x, y, z, tag, loot) in self.chests: be.append(chest_be(x, y, z, loot))
        for (x, y, z, mob, kw) in self.spawners: be.append(spawner_be(x, y, z, mob, **kw))
        return be

    def export_commands(self, path, marker, boss=None):
        """NBT を使わない場合の保険：マーカー座標(MX MY MZ)基準の /data merge・/setblock コマンド集"""
        MX, MY, MZ = marker; L = ['# MX MY MZ を マーカーブロックの座標に置換してから実行', '']
        for (x, y, z, tag, loot) in self.chests:
            L.append(f'execute positioned MX MY MZ run data merge block ~{x-MX} ~{y-MY} ~{z-MZ} {{LootTable:"minecraft:chests/{LOOT.get(loot, loot)}"}}  # {tag}')
        for (x, y, z, mob, kw) in self.spawners:
            L.append(f'execute positioned MX MY MZ run setblock ~{x-MX} ~{y-MY} ~{z-MZ} minecraft:spawner{{SpawnData:{{entity:{{id:"minecraft:{mob}"}}}}}} replace')
        if boss: L.append(f'execute positioned MX MY MZ run summon minecraft:{boss[3]} ~{boss[0]-MX} ~{boss[1]-MY} ~{boss[2]-MZ} {{PersistenceRequired:1b}}')
        open(path, 'w', encoding='utf8').write('\n'.join(L)+'\n')

    # ---- 攻略可能性の検証（歩行・1〜2マスのジャンプ・ハシゴ・扉とレバーの段階解放）
    NONSOLID = ('ladder', 'lever', 'carpet', 'lantern', 'chain', 'cobweb', 'iron_door', 'campfire', 'pointed_dripstone', 'lava', 'water', 'vine', 'lily', 'torch', 'button')
    HAZ = ('lava', 'pointed_dripstone', 'campfire', 'magma')

    def _solid(s, x, y, z, od):
        n = s.b.get(x, y, z)
        if n is None: return False
        if 'iron_door' in n: return (x, y, z) not in od and (x, y-1, z) not in od
        return not any(k in n for k in s.NONSOLID)

    def _free(s, x, y, z, od):
        n = s.b.get(x, y, z)
        return not s._solid(x, y, z, od) and not (n and any(k in n for k in s.HAZ))

    def _sup(s, x, y, z, od):
        n = s.b.get(x, y, z)
        return bool(n and 'ladder' in n) or s._solid(x, y-1, z, od)

    def _bfs(s, start, od):
        seen = {start}; q = deque([start])
        while q:
            x, y, z = q.popleft(); cand = []
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cand += [(x+dx, ny, z+dz) for ny in (y, y+1, y-1, y-2, y-3)]
                cand += [(x+dx*k, ny, z+dz*k) for k in (2, 3) for ny in (y, y+1, y-1)]
            n0 = s.b.get(x, y, z)
            if n0 and 'ladder' in n0: cand += [(x, y+1, z), (x, y-1, z)]
            for (nx, ny, nz) in cand:
                if (nx, ny, nz) in seen: continue
                if not (s._free(nx, ny, nz, od) and s._free(nx, ny+1, nz, od) and s._sup(nx, ny, nz, od)): continue
                if ny > y and not s._free(x, y+2, z, od): continue
                dist = abs(nx-x)+abs(nz-z)
                if dist > 1:
                    sx = (nx > x)-(nx < x); sz = (nz > z)-(nz < z)
                    if not all(s._free(x+sx*t, y, z+sz*t, od) and s._free(x+sx*t, y+1, z+sz*t, od) for t in range(1, dist)): continue
                    if abs(ny-y) >= 2: continue
                seen.add((nx, ny, nz)); q.append((nx, ny, nz))
        return seen

    def solve(self, start):
        """start=(x,y,z)（足元）。戻り値: dict(opened, doors, chests_ok, chests, reached(set))。
        扉は「隣接レバーに到達できたら開く」として不動点まで反復する。"""
        od = set(); order = []
        while True:
            R = self._bfs(start, od); new = False
            for d in self.doors:
                if d in od: continue
                # レバーは壁の目の高さ（足元は1つ下）。足元がそこへ着ければ引ける。動力は _powers で判定
                if any(self._powers(l, d) and (l[0], l[1]-1, l[2]) in R for l in self.levers):
                    od.add(d); order.append(d); new = True
            if not new: break
        ok = [c for c in self.chests if any((c[0]+dx, c[1], c[2]+dz) in R for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        return dict(opened=order, doors=len(self.doors), chests_ok=len(ok), chests=len(self.chests), reached=R)

    # ---- 攻略マップ（真上から。y_stand=歩く高さ）
    def render_map(self, path, y_stand, xs, zs, S=14, title=''):
        from PIL import Image, ImageDraw
        b = self.b
        def color(x, z):
            n = b.get(x, y_stand, z)
            if n:
                for k, c in (('lava', (240, 100, 20)), ('water', (60, 120, 230)), ('chest', (235, 195, 40)), ('iron_door', (210, 40, 40)), ('lever', (255, 255, 255)),
                             ('ladder', (150, 95, 40)), ('trapdoor', (150, 95, 40)), ('pointed_dripstone', (170, 120, 90)), ('cobweb', (240, 240, 240)), ('spawner', (80, 200, 220)),
                             ('stairs', (175, 175, 175)), ('lantern', (255, 205, 100)), ('magma', (200, 70, 20))):
                    if k in n: return c
                return (60, 60, 66)
            nf = b.get(x, y_stand-1, z)
            if nf is None: return (22, 22, 26)
            for k, c in (('lava', (240, 100, 20)), ('water', (60, 120, 230)), ('stairs', (175, 175, 175))):
                if k in nf: return c
            return (206, 201, 190)
        W = (xs[1]-xs[0]+1)*S; H = (zs[1]-zs[0]+1)*S
        im = Image.new('RGB', (W, H+24), (18, 18, 22)); d = ImageDraw.Draw(im)
        for x in range(xs[0], xs[1]+1):
            for z in range(zs[0], zs[1]+1):
                d.rectangle([(x-xs[0])*S, (z-zs[0])*S+24, (x-xs[0]+1)*S-1, (z-zs[0]+1)*S+22], fill=color(x, z))
        d.text((6, 6), title, fill=(255, 255, 255)); im.save(path); return im.size
