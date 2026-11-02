"""浮遊島＋聖樹の幹と地下のダンジョン（テーマ切替）。
  python3 island_dungeon.py --theme spring|summer|autumn [--out ディレクトリ]
出力: <theme>_island_dungeon.bp（宝箱・スポナー入り）/ _noBE.bp（保険）/ 攻略マップPNG 4枚 / コマンド集。
構成（座標は島の広場の床 y=0、広場の中心 (0,4)、聖樹の幹 (0,-27)）:
  島 …… 6つの楕円の合成で輪郭、底は逆円錐＋鍾乳石。広場に紋様、南に月門と参道、東に遺跡、北に聖樹、周りに立石と小島。
  ダンジョン …… 入口は聖樹の南面の扉 → 根の間(幹の根元) ┬ 梯子の縦穴で幹を登る(小部屋A/B/C → 樹冠の間)
                                                        └ 螺旋で地下へ(入口の間 → 根の迷路 → 試練の間[棘の穴・溶岩] → 螺旋 → 地下墓所[溶岩の堀+島] → 梯子 → 宝物庫)
                 帰りの近道(試練の間の東の扉+両側の壁レバー → 入口の間)。検証: 密閉0・全扉が開く・全宝箱に到達。
設計の根拠と失敗談は references/island_dungeon.md。素材と意匠は themes.py。
"""
import sys, os, math, random, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from builder import *
from dungeon_kit import Dungeon, DIRS6
from pattern_helpers import seg_dist
from themes import THEMES

ap = argparse.ArgumentParser(); ap.add_argument('--theme', default='summer', choices=list(THEMES)); ap.add_argument('--out', default='.')
args = ap.parse_args(); T = THEMES[args.theme]; os.makedirs(os.path.join(args.out, 'samples'), exist_ok=True)
D = math.radians
b = Build(); G = {}

# ============================ 1. 地形 ============================
BLOBS = [(0, 2, 40, 38, 1.0), (-27, -12, 19, 17, .85), (29, -12, 18, 16, .85), (15, 29, 15, 12, .7), (-21, 27, 14, 12, .7), (0, -36, 17, 12, .95)]
PC = (0, 4)                                                    # 広場の中心
def field(x, z):
    v = -9
    for cx, cz, rx, rz, k in BLOBS: v = max(v, k * (1 - ((x - cx) / rx) ** 2 - ((z - cz) / rz) ** 2))
    return v + 0.10 * noise(x, 0, z, 6)
FLATS = [(21, 37, -11, 5, 4)]                                  # 遺跡の床 (x0,x1,z0,z1,なだらかにする幅)
def top(x, z):
    h = 1.7 * noise(x, 0, z, 10) + 0.8 * noise(x * 1.7, 9, z * 1.7, 4)
    w = min(1.0, max(0, (math.hypot(x - PC[0], z - PC[1]) - 19) / 8))        # 広場の周りは平ら
    if z > 10: w = min(w, max(0, (abs(x) - 3) / 4))                            # 参道も平ら
    for x0, x1, z0, z1, m in FLATS:
        w = min(w, max(0, (math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1)) - 1) / m))
    return int(round(h * w + 3.4 * math.exp(-((x) ** 2 + (z + 27) ** 2) / 70)))  # 聖樹の丘(+3)
bottoms = {}
for x in range(-62, 63):
    for z in range(-62, 62):
        v = field(x, z)
        if v <= 0.03: continue
        yt = top(x, z); G[(x, z)] = yt
        dep = max(3, int(30 * max(v, 0) ** 0.62 * 1.1 + 2.5 * noise(x, 5, z, 4))); bottoms[(x, z)] = yt - dep - 1
        for y in range(yt - dep, yt + 1):
            if y == yt: n, p = T.surface(v, x, y, z)
            elif y >= yt - 3 and v > 0.22: n, p = pick([('dirt', 78), ('coarse_dirt', 14), ('rooted_dirt', 8)], x, y, z), {}
            elif y >= yt - 2: n, p = pick(T.rim_mix, x, y, z), {}
            elif y > -9: n, p = pick(T.mid_mix, x, y, z), {}
            else: n, p = pick(T.deep_mix, x, y, z), {}
            b.put(x, y, z, n, **p)
for (x, z), yb in list(bottoms.items()):                       # 底: 鍾乳石と光る結晶
    hh = h3(x, 7, z)
    if hh % 53 == 0:
        L = 4 + hh % 9
        for k in range(L): b.put(x, yb - k, z, 'dripstone_block')
        b.put(x, yb - L, z, 'pointed_dripstone', thickness='tip', vertical_direction='down', waterlogged='false')
    if hh % 29 == 0: T.under(b, x, yb, z)
print('terrain', len(b.B), 'blocks;', len(G), 'columns')

# ============================ 2. 構造物（広場・参道・月門・立石・遺跡） ============================
for x in range(-20, 21):
    for z in range(-16, 24):
        n = T.plaza(x, z, PC)
        if n and (x, z) in G: b.put(x, 0, z, n); G[(x, z)] = 0
for z in range(21, 48):                                        # 参道
    for x in range(-2, 3):
        if (x, z) in G:
            n = 'stone_bricks' if abs(x) < 2 else 'mossy_stone_bricks'
            b.put(x, 0, z, pick([(n, 70), ('cracked_stone_bricks', 12), ('mossy_stone_bricks', 10), ('polished_andesite', 8)], x, 0, z))
    if z % 7 == 3:
        for sx in (-3, 3):
            if (sx, z) in G:
                for y in (1, 2): b.put(sx, y, z, 'stone_brick_wall', **WALL)
                b.put(sx, 3, z, 'lantern', hanging='false', waterlogged='false')
GZ, GY, RIN, ROUT = 28, 6.6, 5.7, 8.0                          # 月門: 縦の輪。足元は y>=1 を開け、床の高さ0は参道
for x in range(-10, 11):
    for y in range(-2, 16):
        dd = math.hypot(x, y - GY)
        if dd < RIN or dd > ROUT or y <= 0: continue
        sec = int((math.degrees(math.atan2(y - GY, x)) % 360) // 15)
        for z in (GZ - 1, GZ, GZ + 1):
            if dd < RIN + 0.95: n, p = T.gate_inner[sec % 2], {}
            elif dd > ROUT - 0.9: n, p = T.gate_edge, {'axis': 'x' if abs(y - GY) < abs(x) * 0.6 else 'y'}
            else: n, p = pick(T.gate_body, x, y, z), {}
            b.put(x, y, z, n, **p)
        if sec % 3 == 1 and RIN + 1.0 < dd < ROUT - 1.0 and h3(x, y, 0) % 2 == 0:
            for z in (GZ - 1, GZ, GZ + 1): b.put(x, y, z, T.lamp)
for x in range(-10, 11):
    for z in range(GZ - 2, GZ + 3):
        if 3 <= abs(x) <= 9 and (x, z) in G: b.put(x, 0, z, 'polished_andesite')
for sx in (-1, 1):
    for dz in (-2, 2):
        X, Z = sx * 10, GZ + dz
        if (X, Z) in G:
            for y in range(1, 4): b.put(X, y, Z, 'stone_brick_wall', **WALL)
            b.put(X, 4, Z, 'lantern', hanging='false', waterlogged='false')
STONES = []                                                     # 立石（南の月門側を除く）
for k in range(9):
    a = D(360 * k / 9 + 10)
    if abs(((math.degrees(a) - 90 + 180) % 360) - 180) < 28: continue
    x = round(PC[0] + 23 * math.cos(a)); z = round(PC[1] + 23 * math.sin(a))
    if (x, z) not in G or field(x, z) < 0.25: continue
    y0 = G[(x, z)] + 1; hh = 7 + h3(x, 1, z) % 4
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (x + dx, z + dz) in G: b.put(x + dx, y0, z + dz, T.stone_base)
    for y in range(y0 + 1, y0 + hh):
        b.put(x, y, z, T.lamp if (y - y0) % 4 == 0 and 0 < y - y0 < hh - 1 else pick(T.stone_shaft, x, y, z))
    b.put(x, y0 + hh, z, T.stone_cap); b.put(x, y0 + hh + 1, z, T.stone_top[0], **T.stone_top[1])
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if h3(x + dx, y0, z + dz) % 3 == 0: b.put_if_empty(x + dx * 2, y0, z + dz * 2, T.foot[0], **T.foot[1])
    STONES.append((x, z))
FX0, FX1, FZ0, FZ1 = 21, 37, -11, 5                             # 東の遺跡
for x in range(FX0, FX1 + 1):
    for z in range(FZ0, FZ1 + 1):
        if (x, z) not in G: continue
        h = h3(x, 0, z) % 100
        n = 'moss_block' if h < 9 else ('grass_block' if h < 14 else (T.ruin_floor[0] if (x + z) % 2 == 0 else T.ruin_floor[1]))
        b.put(x, 0, z, n, **({'snowy': 'false'} if n == 'grass_block' else {})); G[(x, z)] = 0
RCOL = [(x, z) for x in (22, 26, 30, 34, 36) for z in (-9, 3) if (x, z) in G]
for (x, z) in RCOL:
    hh = [9, 9, 8, 5, 3, 9, 6][h3(x, 2, z) % 7]
    for y in range(1, hh + 1):
        n, p = (T.ruin_cap, {}) if (y == 1 or (y == hh and hh >= 8)) else T.ruin_col
        if h3(x, y, z) % 7 == 0 and y > 2: n, p = 'mossy_stone_bricks', {}
        b.put(x, y, z, n, **p)
    if hh >= 8: b.put(x, hh + 1, z, T.ruin_slab, **SL)
    else:
        for _ in range(3): b.put_if_empty(x + ((h3(x, hh, z) >> 3) % 5 - 2), 1, z + ((h3(z, x, 3) >> 2) % 5 - 2), T.ruin_rubble)
        if hh >= 3: b.put_if_empty(x, hh + 1, z, T.foot[0], **T.foot[1])
for z in (-9, 3):                                                # まぐさ
    for x in range(22, 36):
        if b.get(x, 10, z) == T.ruin_slab and b.get(x + 4, 10, z) == T.ruin_slab:
            for xx in range(x + 1, x + 4): b.put(xx, 10, z, 'stone_brick_slab' if xx % 2 else T.ruin_slab, **SL)
for x in range(FX0, FX1 + 1):                                    # 奥の崩れた壁
    hh = 2 + h3(x, 5, 0) % 5 if h3(x, 6, 0) % 6 else 0
    for y in range(1, hh + 1): b.put(x, y, FZ0 - 1, pick([('stone_bricks', 50), ('mossy_stone_bricks', 35), ('cracked_stone_bricks', 15)], x, y, 0))
AX, AZ, HY = 29, -3, 8                                           # 祭壇と浮かぶ『心』
for dx in range(-2, 3):
    for dz in range(-2, 3): b.put(AX + dx, 1, AZ + dz, T.altar[0] if max(abs(dx), abs(dz)) == 2 else T.altar[1])
for dx in range(-1, 2):
    for dz in range(-1, 2): b.put(AX + dx, 2, AZ + dz, T.altar[2])
b.put(AX, 3, AZ, T.altar[3])
for sx, sz in ((2, 2), (-2, 2), (2, -2), (-2, -2)): b.put(AX + sx, 2, AZ + sz, 'end_rod', facing='up')
b.shell(AX, HY, AZ, 2.6, 3.6, 2.6, lambda X, Y, Z: T.relic_shell, inner=0.0, lumpy=.15); b.sphere(AX, HY, AZ, 1.4, T.relic_core)
for dy in (-5, 5): b.put(AX, HY + dy, AZ, 'end_rod', facing='up' if dy > 0 else 'down')
for k in range(8):
    a = k * math.pi / 4; b.put(round(AX + 3.4 * math.cos(a)), HY + (k % 2) * 2 - 1, round(AZ + 3.4 * math.sin(a)), 'end_rod', facing='up')
print('structures', len(b.B))

# ============================ 3. 聖樹（幹は直立・太め: 内部をダンジョンにするため） ============================
TX, TZ = 0, -27; Y0 = G[(TX, TZ)] + 1; H = 46
def trad(yy): t = yy / H; return 4.3 + 2.0 * (1 - t) ** 1.5 + 3.0 * math.exp(-yy / 3.2)    # 最小でも 4.3（内部の部屋と縦穴の壁を確保）
LOG = lambda X, Y, Z: pick(T.log_mix, X, Y, Z)
LP = T.leaf(0, 0, 0)[1]                                          # 葉のプロパティ（葉ブロックならLEAF、ウール等なら{}）
for yy in range(-3, H + 1):
    r = trad(max(yy, 0)); R = int(r) + 2
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            ang = math.atan2(dz, dx); rr = r * (1 + 0.12 * math.sin(ang * 5 + yy / 8.0)); d = math.hypot(dx, dz)
            if d > rr: continue
            X, Y, Z = TX + dx, Y0 + yy, TZ + dz
            if math.sin(ang * 3 + yy * 0.35) * math.cos(ang * 2 - yy * 0.2) > 0.9 and d > rr - 1.3 and yy > 1: b.put(X, Y, Z, T.vein[0], **T.vein[1])
            else: b.put(X, Y, Z, pick(T.trunk_mix, X, Y, Z), axis='y')
rr_ = random.Random(11)
for k in range(9):                                               # 根
    a = k * math.tau / 9 + rr_.uniform(-.2, .2); L = rr_.uniform(15, 22)
    b.tube((TX + 5 * math.cos(a), Y0 + 4, TZ + 5 * math.sin(a)), (TX + 9 * math.cos(a + .15), Y0 + 3, TZ + 9 * math.sin(a + .15)),
           (TX + (L - 5) * math.cos(a - .2), Y0 - 1, TZ + (L - 5) * math.sin(a - .2)), (TX + L * math.cos(a), Y0 - 2, TZ + L * math.sin(a)), 2.2, 0.7, LOG, axis='y')
ends = []
for k in range(7):                                               # 枝
    a = k * math.tau / 7 + 0.3; yy = 22 + (k * 5) % 11; L = rr_.uniform(13, 19)
    e = b.tube((TX, Y0 + yy, TZ), (TX + L * .3 * math.cos(a), Y0 + yy + 5, TZ + L * .3 * math.sin(a)), (TX + L * .7 * math.cos(a), Y0 + yy + 3, TZ + L * .7 * math.sin(a)),
               (TX + L * math.cos(a), Y0 + yy + rr_.uniform(8, 14), TZ + L * math.sin(a)), 2.4, .9, LOG, axis='y'); ends.append(e)
LOBES_T = [(TX, Y0 + H + 4, TZ, 16, 8.5)] + [(e[0], e[1] + 2, e[2], 11, 6.5) for e in ends] + [(TX + 19 * math.cos(k * math.tau / 6 + .5), Y0 + 29 + (k % 2) * 3, TZ + 19 * math.sin(k * math.tau / 6 + .5), 8, 5) for k in range(6)]
leaves = set()
for (cx, cy, cz, rx, ry) in LOBES_T:                              # 樹冠は『殻』（中は空洞 → 樹冠の間にできる）
    for p in b.shell(cx, cy, cz, rx, ry, rx, lambda X, Y, Z: T.leaf(X, Y, Z)[0], inner=0.5, lumpy=.3, **LP): leaves.add(p)
for (X, Y, Z) in sorted(leaves):
    hh = h3(X, Y, Z); up = (X, Y + 1, Z) not in leaves; dn = (X, Y - 1, Z) not in leaves
    acc = T.leaf_accent(X, Y, Z, hh, up)
    if acc: b.put(X, Y, Z, acc[0], **acc[1])
    if dn and hh % 5 == 0:
        for k in range(1, 2 + hh % 3):
            if b.empty(X, Y - k, Z): nm, pr = T.leaf(X, Y - k, Z); b.put(X, Y - k, Z, nm, **pr)
    if dn and hh % 41 == 0 and Y < Y0 + 36: b.hanging(X, Y - 1, Z, 5 + hh % 9, 'cave')
    if dn and hh % 101 == 0 and Y < Y0 + 38:
        for k in range(1, 3 + hh % 5):
            if b.empty(X, Y - k, Z): b.put(X, Y - k, Z, 'iron_chain', axis='y', waterlogged='false')
        if b.empty(X, Y - (3 + hh % 5), Z): b.put(X, Y - (3 + hh % 5), Z, 'lantern', hanging='true', waterlogged='false')
T.litter(b, G, TX, TZ)
def mini_tree(x, y0, z, h=9, spr=5.0, seed=0):
    r = random.Random(x * 37 + z * 11 + seed); q = lambda k: r.uniform(-k, k)
    tp = b.tube((x, y0, z), (x + q(1.5), y0 + h * .35, z + q(1.5)), (x + q(2), y0 + h * .7, z + q(2)), (x + q(2), y0 + h, z + q(2)), 1.3, .7, LOG, axis='y')
    ls = b.shell(tp[0], tp[1] + 1, tp[2], spr, spr * .6, spr, lambda X, Y, Z: T.leaf(X, Y, Z)[0], inner=.45, lumpy=.3, **LP); S = set(ls)
    for (X, Y, Z) in ls:
        hh = h3(X, Y, Z); acc = T.leaf_accent(X, Y, Z, hh, (X, Y + 1, Z) not in S)
        if acc and acc[0] != 'shroomlight': b.put(X, Y, Z, acc[0], **acc[1])
        elif (X, Y - 1, Z) not in S and hh % 4 == 0 and b.empty(X, Y - 1, Z): nm, pr = T.leaf(X, Y - 1, Z); b.put(X, Y - 1, Z, nm, **pr)
    return tp
for (x, z, h) in ((-30, -8, 10), (-24, -19, 9), (-35, -15, 11), (-19, -5, 8), (-37, -3, 10), (-27, 3, 9), (36, -24, 9), (14, -22, 8), (-14, -24, 9)):
    if (x, z) in G and field(x, z) > 0.3: mini_tree(x, G[(x, z)] + 1, z, h, 5.2 + h3(x, 0, z) % 3 * .5)
for (sx, sz), e in zip(STONES[:6], ends[:6]):                     # 立石と枝を結ぶ提灯の綱
    b.rope((sx, G[(sx, sz)] + 1 + 7 + h3(sx, 1, sz) % 4 + 2, sz), (round(e[0]), round(e[1]) - 3, round(e[2])), 3.5)
print('tree', len(b.B))

# ============================ 4. ダンジョン「聖樹の根と心」 ============================
dg = Dungeon(b)
CX, CZ = TX, TZ; FLOORY = Y0 - 1; FY1, FY2, FY3 = -9, -18, -27           # 各層の歩く高さ（層間に岩3枚以上: 深さ実測済み）
ROOT_W = [('dark_oak_planks', 26), ('mangrove_planks', 22), ('stripped_dark_oak_log', 16), ('mud_bricks', 22), ('rooted_dirt', 14)]
ROOT_C = [('dark_oak_planks', 40), ('mangrove_planks', 30), ('mud_bricks', 30)]
ROOT_F = [('coarse_dirt', 30), ('mud_bricks', 30), ('dark_oak_planks', 25), ('rooted_dirt', 15)]
STONE_W = [('stone_bricks', 50), ('mossy_stone_bricks', 22), ('cracked_stone_bricks', 10), ('deepslate_bricks', 18)]
STONE_C = [('stone_bricks', 55), ('mossy_stone_bricks', 15), ('deepslate_tiles', 30)]
STONE_F = [('polished_andesite', 40), ('stone_bricks', 40), ('mossy_stone_bricks', 20)]
def deco(x, y, z): b.put(x, y, z, T.deco_up[0], **T.deco_up[1])
zout = next(z for z in range(CZ + 3, CZ + 14) if b.empty(0, Y0 + 1, z))     # 幹の南面の外（扉の外側）
with dg.section('tree'):
    dg.disc(CX, CZ, 3.5, Y0, Y0 + 4)                              # 根の間
    dg.carve(0, Y0, CZ + 3, 0, Y0 + 2, zout - 1); dg.open_end([(0, y, zout) for y in range(Y0, Y0 + 3)])   # 幹の扉の通路
    dg.carve(CX + 2, Y0 + 5, CZ, CX + 2, Y0 + H, CZ)              # 幹を貫く梯子の縦穴（中心から2。最小の幹半径4.3に対し壁を含め3で収まる）
    for ys in (Y0 + 13, Y0 + 25, Y0 + 36): dg.disc(CX, CZ, 2.2, ys, ys + 3)   # 小部屋 A,B,C
with dg.section('root'):
    HALL_SPIRAL = dg.spiral(CX, CZ, FLOORY, FLOORY - (FY1 - 1), (CX, CZ + 1), up=False, rot=-1, stair='dark_oak_stairs', pillar='stripped_dark_oak_log', floor='dark_oak_planks')
    dg.disc(CX, CZ, 3.5, FY1, FY1 + 4); dg.carve(0, FY1, CZ + 3, 0, FY1 + 4, CZ + 4)     # 入口の間 → 迷路
    MZ = dg.maze(-9, -22, 9, 8, FY1, FY1 + 4, ('N', 4), ('S', 4), seed=3, min_path=40, wall=ROOT_W)
    dg.carve(0, FY1, -5, 0, FY1 + 4, -4)                          # 迷路の出口 → 試練の間
with dg.section('stone'):
    dg.carve(-8, FY1, -3, 8, FY1 + 4, 12)                         # 試練の間
    dg.spike_pit(-8, 1, 8, 3, y_floor=FY1 - 1, depth=3, bridge_cells=[(0, 1), (0, 2), (0, 3)])
    dg.lava_lake(-8, 5, 8, 8, y_surface=FY1 - 1, depth=2)         # 飛び石は1マス空け（ジャンプで越える）
    for z in (6, 8): b.put(0, FY1 - 1, z, 'polished_blackstone')
    dg.spiral(0, 10, FY1 - 1, 9, (0, 9), up=False, rot=-1)
    dg.disc(0, 4, 11, FY2, FY2 + 4)                               # 地下墓所
    dg.lava_lake(-5, -4, 5, 6, y_surface=FY2 - 1, depth=1)        # 溶岩は1層（直下の宝物庫の天井を3枚確保）
    dg.carve(0, FY3, 1, 0, FY2 - 2, 1)                            # 島の穴 → 宝物庫への縦穴
    dg.carve(-4, FY3, -3, 4, FY3 + 4, 5)                          # 宝物庫
    dg.carve(9, FY1, -1, 10, FY1 + 4, -1); dg.carve(10, FY1, -27, 10, FY1 + 4, -2); dg.carve(4, FY1, -27, 9, FY1 + 4, -27)   # 帰りの近道
prot = dg.line_sections({'tree': (T.tree_wall, T.tree_ceil, T.tree_floor), 'root': (ROOT_W, ROOT_C, ROOT_F), 'stone': (STONE_W, STONE_C, STONE_F)})
print('内張りが突き出す(元が空気だった)セル:', len(prot), prot[:6])      # 幹の外へ出ていないかの目安。数個なら扉枠など
for y in range(Y0, Y0 + H + 1):                                    # ハシゴの裏の壁（ホールの中は壁が無いので置く）
    if (CX + 3, y, CZ) in dg.D: b.put(CX + 3, y, CZ, T.tree_wall[0][0])
dg.ladder(CX + 2, Y0, Y0 + H, CZ, 'west')
for (ys, mob, loot) in ((Y0 + 13, 'cave_spider', 'easy'), (Y0 + 25, 'skeleton', 'jungle'), (Y0 + 36, T.mob_zombie, 'gold')):
    dg.chest(CX - 2, ys, CZ, 'east', loot=loot, tag=f'幹 y{ys}')
    b.put(CX, ys, CZ - 2, T.spawner_log, axis='y'); b.put(CX, ys + 2, CZ - 2, T.spawner_log, axis='y')
    dg.spawner(CX, ys + 1, CZ - 2, mob, light=(0, 15), near=4, count=2)
    dg.lantern(CX, ys + 3, CZ); dg.lantern(CX + 1, ys + 3, CZ + 1)
for (x, z) in ((CX - 3, CZ), (CX, CZ - 3), (CX, CZ + 3)): dg.lantern(x, Y0 + 4, z)
for dx in (-1, 1):                                                 # 扉の枠
    for y in range(Y0, Y0 + 3):
        if b.empty(dx, y, zout - 1): b.put(dx, y, zout - 1, T.door_frame)
for dx in (-1, 0, 1): b.put_if_empty(dx, Y0 + 3, zout - 1, T.canopy_door_slab, **SL)
b.put(0, Y0 + 3, zout, 'lantern', hanging='true', waterlogged='false')
for (x, z) in ((CX - 3, CZ), (CX + 3, CZ)): dg.lantern(x, FY1 + 4, z)
cxz = MZ['cellxz']
for (i, j, loot) in ((0, 0, 'jungle'), (8, 0, 'gold'), (0, 7, 'easy')):    # 迷路の隅の宝箱
    x, z = cxz(i, j); dg.chest(x, FY1, z, 'south' if j < 4 else 'north', loot=loot, tag=f'迷路({i},{j})')
for (i, j) in ((2, 3), (6, 2), (4, 6), (7, 7), (1, 5)): x, z = cxz(i, j); dg.lantern(x, FY1 + 4, z)
for (x, z) in ((-7, -2), (7, -2), (-7, 4), (7, 4), (-7, 10), (7, 9), (0, -3)): dg.lantern(x, FY1 + 4, z)
for y in (FY1, FY1 + 1, FY1 + 2): b.put(-6, y, -1, 'stone_bricks')
dg.spawner(-6, FY1 + 1, -1, 'skeleton', light=(0, 15), near=4, count=2)
dg.chest(6, FY1, 11, 'north', loot='gold', tag='試練の間')
dg.door_levers(6, FY1, -27, 'east')         # 近道: 扉の両側に壁レバー（行きも帰りも開く）
for (x, z) in ((10, -10), (10, -20), (8, -27)): dg.lantern(x, FY1 + 4, z)
for x in range(-3, 4):                                              # 墓所の島(7x7)と飛び石
    for z in range(-2, 5):
        b.put(x, FY2 - 1, z, 'polished_blackstone_bricks'); b.put(x, FY2 - 2, z, 'polished_blackstone_bricks'); b.rm(x, FY2, z)
for (x, z) in ((0, -3), (0, 5), (-4, 1), (4, 1)): b.put(x, FY2 - 1, z, 'polished_blackstone'); b.put(x, FY2 - 2, z, 'polished_blackstone')
b.rm(0, FY2 - 1, 1); b.rm(0, FY2 - 2, 1); dg.ladder(0, FY3, FY2 - 1, 1, 'north')    # 穴は『開けっぱなし』（トラップドアはBFSが通れない）
for k in range(8):
    a = k * math.pi / 4 + math.pi / 8; x = round(8 * math.cos(a)); z = 4 + round(8 * math.sin(a))
    for y in range(FY2, FY2 + 5): b.put(x, y, z, 'chiseled_stone_bricks' if y in (FY2, FY2 + 4) else 'stone_bricks')
for (x, z) in ((0, -6), (0, 9), (-7, 1), (7, 1), (-6, 8), (6, 8), (-6, -3), (6, -3)):
    if (x, FY2 + 4, z) in dg.D: dg.lantern(x, FY2 + 4, z)
for y in (FY2, FY2 + 1, FY2 + 2): b.put(-9, y, 4, 'stone_bricks'); b.put(9, y, 4, 'stone_bricks')
dg.spawner(-9, FY2 + 1, 4, T.mob_zombie, light=(0, 15), near=4, count=2); dg.spawner(9, FY2 + 1, 4, 'skeleton', light=(0, 15), near=4, count=2)
dg.chest(2, FY2, 0, 'west', loot='rich', tag='墓所の島'); dg.chest(-2, FY2, 2, 'east', loot='gold', tag='墓所の島2'); deco(2, FY2, 3); deco(-2, FY2, -1)
for y in range(FY3, FY3 + 5): b.put(0, y, 2, T.vault_pillar[0], **T.vault_pillar[1])      # 梯子の裏の柱
for (x, z) in ((-4, -3), (4, -3), (-4, 5), (4, 5)):
    for y in range(FY3, FY3 + 4): b.put(x, y, z, T.vault_pillar[0], **T.vault_pillar[1])
for x in range(-3, 4):
    for z in range(-2, 5):
        if (x, z) not in ((0, 1), (0, 2)) and max(abs(x), abs(z - 1)) == 3: b.put(x, FY3 - 1, z, T.vault_floor[0] if (x + z) % 2 == 0 else T.vault_floor[1])
dg.chest(-3, FY3, -2, 'south', loot='rich', tag='宝物庫A'); dg.chest(3, FY3, -2, 'south', loot='ancient', tag='宝物庫B'); dg.chest(0, FY3, 4, 'north', loot='end', tag='宝物庫C')
for (x, z) in ((-2, 1), (2, 1), (0, -2)): deco(x, FY3, z)
for (x, z) in ((-2, -1), (2, -1), (-2, 3), (2, 3)): dg.lantern(x, FY3 + 4, z)
# ---- 樹冠の間（幹の頂部。殻の空洞に床を張り、切り抜いた葉の隙間を塞ぐ） ----
PY = Y0 + H; CAN = set()
for x in range(-9, 10):
    for z in range(-9, 10):
        d = math.hypot(x, z)
        if d <= 8.3:
            X, Z = CX + x, CZ + z
            if (X, Z) != (CX + 2, CZ): b.put(X, PY, Z, T.canopy_floor[0] if d < 7.3 else T.canopy_floor[1])
            for y in range(PY + 1, PY + 9): b.rm(X, y, Z); CAN.add((X, y, Z))       # 梯子の真上の葉も必ず抜く（抜き忘れると宝箱に到達できない）
dg.D.update(CAN)
for (x, y, z) in sorted(CAN):
    for dx, dy, dz in DIRS6:
        n = (x + dx, y + dy, z + dz)
        if n in CAN or (n[0] == CX + 2 and n[2] == CZ and n[1] <= PY): continue
        if b.empty(*n): nm, pr = T.canopy_seal(*n); b.put(*n, nm, **pr)
for dx in range(-1, 2):
    for dz in range(-1, 2): b.put(CX + dx, PY + 1, CZ + dz, T.dais[0] if dx == 0 and dz == 0 else T.dais[1])
dg.chest(CX, PY + 2, CZ, 'south', loot='ancient', tag='樹冠の心')
for (dx, dz) in ((2, 2), (-2, 2), (2, -2), (-2, -2), (0, 3), (0, -3), (3, 0), (-3, 0)): deco(CX + dx, PY + 1, CZ + dz)
for k in range(8): b.put(round(CX + 4.5 * math.cos(k * math.pi / 4)), PY + 1, round(CZ + 4.5 * math.sin(k * math.pi / 4)), 'end_rod', facing='up')
b.put(CX, PY + 5, CZ, T.canopy_light); b.sphere(CX, PY + 5, CZ, 1.2, T.canopy_light)
for (dx, dz) in ((3, 3), (-3, 3), (3, -3), (-3, -3), (0, 6), (0, -6), (6, 0), (-6, 0)):
    tp = max((y for (x, y, z) in CAN if x == CX + dx and z == CZ + dz), default=None)
    if tp: b.put(CX + dx, tp, CZ + dz, 'lantern', hanging='true', waterlogged='false')
# ---- 検証 ----
leaks = dg.check_leaks(); door_bad = dg.check_doors(); print('扉・レバーチェック(空が合格):', door_bad); ret_bad = dg.check_return((0, Y0, zout + 1)); print('戻り検査(空が合格):', ret_bad); assert not ret_bad; r = dg.solve(start=(0, Y0, zout + 1))
missing = [c for c in dg.chests if not any((c[0] + dx, c[1], c[2] + dz) in r['reached'] for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
print(f"密閉チェック(0が合格): {leaks} / 扉 {len(r['opened'])}/{r['doors']} 開く / 宝箱 {r['chests_ok']}/{r['chests']} 到達 / 未到達: {[(c[0], c[1], c[2], c[3]) for c in missing]}")
pre = os.path.join(args.out, T.name + '_map_')
dg.render_map(pre + 'L0_root_hall.png', Y0, (CX - 8, CX + 8), (CZ - 8, CZ + 10), S=22, title='Root hall y=%d' % Y0)
dg.render_map(pre + 'L1_maze.png', FY1, (-12, 12), (-33, 14), S=16, title='L1 maze / trial y=%d' % FY1)
dg.render_map(pre + 'L2_crypt.png', FY2, (-13, 13), (-9, 17), S=20, title='L2 crypt y=%d' % FY2)
dg.render_map(pre + 'L3_vault.png', FY3, (-6, 6), (-5, 7), S=30, title='L3 vault y=%d' % FY3)
dg.export_commands(os.path.join(args.out, T.name + '_commands.txt'), (0, 0, 0), boss=(0, FY2, 1, 'wither_skeleton'))

# ============================ 5. 小島・背面レリーフ・飾り ============================
def islet(cx, cy, cz, r):
    for x in range(-r - 2, r + 3):
        for z in range(-r - 2, r + 3):
            d = math.hypot(x, z) + 1.3 * noise(x + cx, 0, z + cz, 3)
            if d > r: continue
            dep = int(r * 1.9 * (1 - d / r) ** 0.8) + 1
            for k in range(dep + 1):
                y = cy - k
                if k == 0: n, p = T.islet_top(x + cx, y, z + cz)
                elif k < 3: n, p = 'dirt', {}
                else: n, p = pick([('stone', 40), ('andesite', 25), ('tuff', 20), ('deepslate', 15)], x + cx, y, z + cz), {}
                b.put(cx + x, y, cz + z, n, **p)
            if h3(x + cx, 2, z + cz) % 6 == 0 and dep > 3: b.put(cx + x, cy - dep - 1, cz + z, T.islet_under[0], **T.islet_under[1])
def post(x, y, z, h=3):
    for k in range(h): b.put(x, y + k, z, 'stone_brick_wall', **WALL)
    b.put(x, y + h, z, 'lantern', hanging='false', waterlogged='false')
ISL = [(-50, 13, 18, 9), (54, 22, 4, 7), (-42, 30, -32, 8), (42, 9, 42, 6), (-14, 48, 40, 5), (60, -6, -30, 6)]
for (x, y, z, r) in ISL: islet(x, y, z, r)
mini_tree(-50, 14, 18, 9, 5.0, 1); post(-46, 14, 22); post(-54, 14, 14)
T.crystal(b, 54, 23, 4, 8); T.crystal(b, 51, 23, 7, 4); T.crystal(b, 57, 23, 2, 5)
for k in range(4): post(-42 + (k % 2) * 6 - 3, 31, -32 + (k // 2) * 6 - 3, 2)
T.crystal(b, -42, 31, -32, 7); post(42, 10, 42, 2); mini_tree(40, 10, 44, 6, 3.5, 3); T.crystal(b, -14, 49, 40, 6); mini_tree(60, -5, -30, 8, 4.5, 5); post(63, -5, -27)
for (a, c) in (((-46, 17, 22), (-33, 4, 10)), ((51, 26, 4), (40, 4, -2)), ((42, 13, 42), (32, 4, 34)), ((-42, 34, -29), (-30, 4, -12))):
    if (c[0], c[2]) in G: post(c[0], c[1] - 3, c[2], 3)
    b.rope(a, c, 3.0)                                               # 小島と本島を結ぶ提灯の綱
T.back(b)                                                           # 背面の大きなレリーフ（月/楓/ひまわり）
rs = random.Random(5)                                               # 光の粒（蛍）。ダンジョンの空洞(dg.D)には置かない
for _ in range(220):
    X, Y, Z = int(TX + rs.uniform(-30, 30)), int(Y0 + rs.uniform(4, 48)), int(TZ + rs.uniform(-26, 34))
    if (X, Y, Z) not in dg.D and b.empty(X, Y, Z) and all(b.empty(X + dx, Y + dy, Z + dz) for dx, dy, dz in DIRS6): b.put(X, Y, Z, 'end_rod', facing='up')
T.decorate(b, G)

# ============================ 6. 保存（BE入り／BEなし） ============================
BE = dg.block_entities()
b.BE = BE; b.save(os.path.join(args.out, 'samples', f'{T.name}_island_dungeon.bp'), T.title + 'ダンジョン(BE入り)', author='nemo', tags=['fantasy', 'island', 'dungeon', T.name])
b.BE = []; b.save(os.path.join(args.out, 'samples', f'{T.name}_island_dungeon_noBE.bp'), T.title + 'ダンジョン(BEなし)', author='nemo', tags=['fantasy', 'island', 'dungeon', T.name])
print('BlockEntities:', len(BE))
