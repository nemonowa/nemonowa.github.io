"""advanced_helpers の総合例：丘の上のゴシック礼拝堂＋円塔＋ドームの洗礼堂＋大木＋街灯の並木。
使っている技法（references/advanced_building.md の節番号）:
  地形=fbm+熱侵食+なめらかな縁(§3) / 壁=下から上へのグラデ(§2) / 尖頭アーチの窓を奥行き1で・窓台つき(§4)
  控え壁とフライング・バットレス(§4) / バラ窓(§4) / 屋根=高さ場→階段・ハーフ(§5) / 円錐屋根・ドーム(§5)
  尖塔(§4) / 部品を回転・反転して複製(stamp, §6) / 懸垂線のロープ(§6) / 風化(§2) / 有機的な大木(§7)
  python3 showcase.py OUT.bp
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from builder import *
import advanced_helpers as A

out = sys.argv[1] if len(sys.argv) > 1 else 'advanced_showcase.bp'
b = Build(); b.BE = []; b.ENT = []

# ---------------------------------------------------------------- 1) 地形：fbm の丘 → 熱侵食 → 縁をなめらかに
R = 34
H = {(x, z): 2.5 + 3.0 * A.fbm2(x / 18, z / 18, 4, seed=3) - 0.004 * (x * x + z * z) for x in range(-R, R + 1) for z in range(-R, R + 1)}
A.thermal_erode(H, iters=15, talus=0.9)
plat = lambda x, z: -14 <= x <= 14 and -20 <= z <= 22                 # 建物の敷地は平らに
hgt = lambda x, z: 3.0 if plat(x, z) else min(H[(x, z)], 2.6 + 0.08 * max(abs(x) - 14, abs(z - 1) - 21, 0) ** 1.2)
mask = lambda x, z: math.hypot(x, z * .9) < R - 1 + 2 * A.fbm2(x / 6, z / 6, 2, seed=9)
A.terrain(b, -R, -R, R, R, hgt, layers=(('grass_block', 1), (lambda x, y, z: pick([('dirt', 3), ('coarse_dirt', 1)], x, y, z), 2)),
          deep=lambda x, y, z: pick([('stone', 4), ('andesite', 2), ('tuff', 1)], x, y, z), base=-6, mask=mask,
          smooth_top=('mossy_cobblestone_stairs', 'mossy_cobblestone_slab'))
for x in range(-14, 15):                                                 # 敷地の基礎（土を見せない）
    for z in range(-20, 23): b.put(x, 3, z, 'polished_andesite' if (x + z) % 2 else 'andesite')

# ---------------------------------------------------------------- 2) 礼拝堂：身廊 x:-5..5, z:-14..12、壁高 12
X0, X1, Z0, Z1, Y0, WH = -5, 5, -14, 12, 4, 12
wall = lambda x, y, z: A.grad_pick(['cobblestone', 'stone_bricks', 'stone_bricks', 'polished_andesite'], (y - Y0) / WH, x, y, z, jitter=.22)
for x in range(X0, X1 + 1):
    for z in range(Z0, Z1 + 1):
        if x in (X0, X1) or z in (Z0, Z1):
            for y in range(Y0, Y0 + WH): b.put(x, y, z, wall(x, y, z))
for x in range(X0 + 1, X1):
    for z in range(Z0 + 1, Z1): b.put(x, Y0 - 1, z, 'polished_deepslate' if (x + z) % 2 else 'polished_diorite')
# 側面の尖頭窓（ベイごと）＋控え壁＋フライング・バットレス
for z in range(Z0 + 3, Z1 - 1, 4):
    for side, nrm in ((X0, 'west'), (X1, 'east')):
        A.opening(b, side, Y0 + 3, z, nrm, w=3, h=7, sharp=1.6, glass='blue_stained_glass_pane', sill='stone_brick_stairs', frame='polished_andesite')
        bz = z + 2
        if bz < Z1: A.buttress(b, side, Y0, bz, nrm, height=WH - 2, depth=3, mat='stone_bricks', cap='stone_brick_stairs', flying_to=Y0 + WH - 1)
# 正面（南 z=Z1）：扉と上のバラ窓
A.opening(b, 0, Y0, Z1, 'south', w=3, h=6, sharp=1.5, glass=None, frame='polished_deepslate', keystone='chiseled_stone_bricks')
b.put(0, Y0, Z1 - 1, 'dark_oak_door', **DOOR('north', 'lower')); b.put(0, Y0 + 1, Z1 - 1, 'dark_oak_door', **DOOR('north', 'upper'))
b.put(-1, Y0, Z1 - 1, 'dark_oak_door', **DOOR('north', 'lower', hinge='right')); b.put(-1, Y0 + 1, Z1 - 1, 'dark_oak_door', **DOOR('north', 'upper', hinge='right'))
b.put(1, Y0, Z1 - 1, 'dark_oak_door', **DOOR('north', 'lower', hinge='left')); b.put(1, Y0 + 1, Z1 - 1, 'dark_oak_door', **DOOR('north', 'upper', hinge='left'))
for x in range(X0, X1 + 1):                                              # 正面の破風（屋根の三角）を壁で立ち上げる
    for y in range(Y0 + WH, Y0 + WH + 7 - abs(x)): b.put(x, y, Z1, wall(x, y, Z1))
A.paint_plane(b, A.rose_window(5, petals=10), 5, (0, Y0 + WH, Z1 + 1), axis='z',
              mats={'frame': 'polished_andesite', 'glass': 'purple_stained_glass', 'hub': 'yellow_stained_glass'})
# 屋根：高さ場（棟が x=0、勾配1）→ 階段とハーフで面を作る。軒の出 1
A.smooth_heightfield(b, [(x, z) for x in range(X0 - 1, X1 + 2) for z in range(Z0 - 1, Z1 + 2)],
                     lambda x, z: Y0 + WH + (X1 + 1.5 - abs(x)), 'deepslate_tiles', 'deepslate_tile_stairs', 'deepslate_tile_slab', fill_down=2)
for x in range(X0 - 1, X1 + 2):                                          # 妻側の軒先に逆さ階段（影）
    b.put(x, Y0 + WH - 1, Z0 - 1, 'stone_brick_stairs', facing='south', half='top', shape='straight', waterlogged='false')
# 交差部の塔と八角尖塔
for x in range(-2, 3):
    for z in range(-6, -1):
        for y in range(Y0 + WH + 6, Y0 + WH + 12):
            if x in (-2, 2) or z in (-6, -2): b.put(x, y, z, 'stone_bricks')
A.spire(b, 0, Y0 + WH + 12, -4, 3.4, 16, lambda x, y, z: pick([('deepslate_tiles', 3), ('cobbled_deepslate', 1)], x, y, z), sides=8, cap='lightning_rod')

# ---------------------------------------------------------------- 3) 円塔（北西）と円錐屋根
TX, TZ, TR = -11, -16, 3
for y in range(Y0, Y0 + 18):
    for x, z in A.circle_cells(TR):
        b.put(TX + x, y, TZ + z, wall(TX + x, y, TZ + z))
for y in range(Y0 + 4, Y0 + 16, 5): b.rm(TX + TR, y, TZ); b.rm(TX + TR, y + 1, TZ)      # 細い窓
A.cone_roof(b, TX, TZ, Y0 + 18, TR, 11, 'spruce_planks', 'spruce_stairs', 'spruce_slab', overhang=1)

# ---------------------------------------------------------------- 4) 洗礼堂（北東）：円形の胴＋ドーム（銅）
DX, DZ, DR = 10, -14, 4
for y in range(Y0, Y0 + 7):
    for x, z in A.circle_cells(DR): b.put(DX + x, y, DZ + z, 'calcite' if y < Y0 + 6 else 'polished_diorite')
A.dome_roof(b, DX, DZ, Y0 + 7, DR + 1, rise=6, full='waxed_weathered_copper', stair='waxed_weathered_cut_copper_stairs', slab='waxed_weathered_cut_copper_slab', onion=0.5)

# ---------------------------------------------------------------- 5) 街灯（部品を1つ作り、曲線に沿って回転・反転しながら複製）＋懸垂線の飾り紐
lamp = Build()
lamp.put(0, 0, 0, 'stone_brick_wall', **WALL); lamp.box(0, 1, 0, 0, 3, 0, 'dark_oak_fence', **FN)
lamp.put(1, 3, 0, 'dark_oak_fence', **FN); lamp.put(1, 2, 0, 'lantern', hanging='true', waterlogged='false')
path = A.catmull_rom([(0, 13), (2, 20), (-6, 27), (-14, 30)], step=0.5)
for i, (px, pz) in enumerate(path):
    for dx in (-1, 0, 1):
        X, Z = int(round(px)) + dx, int(round(pz))
        y = int(math.floor(hgt(X, Z)))
        if b.get(X, y, Z) in ('grass_block', 'dirt', 'coarse_dirt'): b.put(X, y, Z, 'dirt_path')
posts = []
for k, (px, pz) in enumerate(path[6::9]):
    X, Z = int(round(px)) + 3, int(round(pz)); y = int(math.floor(hgt(X, Z))) + 1
    A.stamp(b, lamp, at=(X, y, Z), turns=2 if k % 2 else 0, mirror=None); posts.append((X, y + 3, Z))
for a_, c_ in zip(posts, posts[1:]):
    pts = A.polyline([tuple(int(round(v)) for v in q) for q in A.catenary(a_, c_, 1.2)])
    for p, q in zip(pts, pts[1:] + pts[-1:]):
        ax = 'y' if q[1] != p[1] else ('x' if q[0] != p[0] else 'z')
        if b.empty(*p): b.put(*p, 'iron_chain', axis=ax, waterlogged='false')

# ---------------------------------------------------------------- 6) 大木（西）
A.organic_tree(b, -22, 3, 8, height=18, trunk_r=2.2, depth=3, seed=5, log='oak_log', wood='oak_wood', leaves='oak_leaves', leaf_r=4.0)

# ---------------------------------------------------------------- 7) 風化・統計・保存
A.weather(b, amount=0.35, seed=2)
for row in A.palette_stats(b, 8): print('  ', row)
b.save(out, '高度な建築ショーケース（礼拝堂・円塔・ドーム・大木）', tags=['showcase', 'gothic', 'advanced'])
