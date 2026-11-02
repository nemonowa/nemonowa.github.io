"""最小のダンジョン例：入口(隠し蓋+ハシゴ) → 棘の穴 → 溶岩の渡り → 宝物庫(宝箱+スポナー)。
実行: python3 examples/example_dungeon.py out.bp   （scripts を sys.path に入れて動く）
流れ: 地形 → Dungeon.carve → spike_pit/lava_lake → line(密閉) → 仕掛け → check_leaks → solve → render_map → 保存(BlockEntities付き)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from dungeon_kit import *

out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/example_dungeon.bp'
b = Build()
# 1) 地形：石の塊（x0..49, z0..29, y-14..-1）＋芝(y=0)
for x in range(50):
    for z in range(30):
        for y in range(-14, 0): b.put(x, y, z, pick([('stone', 60), ('andesite', 20), ('tuff', 20)], x, y, z))
        b.put(x, 0, z, 'grass_block', snowy='false')
FY = -7                                     # 歩く高さ（床ブロックは y=-8）
dg = Dungeon(b, line_skip_y=1)
# 2) 掘る
dg.carve(3, FY, 3, 9, -3, 9)                # A 玄室
dg.carve(6, -2, 9, 6, 0, 9)                 # 入口の縦穴（地表まで）
dg.carve(10, FY, 5, 14, -5, 7)              # 回廊
dg.carve(15, FY, 3, 25, -3, 9)              # B 棘の穴の間
dg.spike_pit(17, 3, 18, 9, y_floor=-8, depth=3, bridge_cells=[(17, 6), (18, 6)])
dg.carve(26, FY, 6, 27, FY+1, 6)            # 扉1 の通路（幅1）
dg.carve(28, FY, 5, 29, -5, 7)
dg.carve(30, FY, 3, 40, -3, 9)              # C 溶岩の渡り
dg.lava_lake(33, 3, 37, 9, y_surface=-8, depth=2)
dg.carve(39, FY, 10, 39, FY+1, 11)          # 扉2 の通路（幅1）
dg.carve(33, FY, 12, 43, -3, 20)            # D 宝物庫
# 3) 内張り（密閉）
dg.line()
# 4) 仕掛け
dg.ladder(6, FY, 0, 9, 'north'); dg.hatch(6, 0, 9)                       # 入口：ハシゴ＋面一の蓋
for (x, z) in ((4, 4), (8, 4), (4, 8), (8, 8)): dg.lantern(x, -3, z)
dg.door_levers(26, FY, 6, 'east')                  # 扉1（両側に壁レバー）
for (x, z) in ((34, 6), (36, 6)): b.put(x, -8, z, 'polished_blackstone')  # 溶岩の飛び石（隙間1マス）
dg.lantern(31, -3, 6); dg.lantern(39, -3, 6)
dg.door_levers(39, FY, 10, 'south')               # 扉2（両側に壁レバー）
dg.chest(42, FY, 19, 'north', loot='rich', tag='宝物庫')
for y in (FY, FY+1, FY+2): b.put(38, y, 16, 'stone_bricks')
dg.spawner(38, FY+1, 16, 'zombie')                                       # 暗い部屋のスポナー
# 5) 検証
print('密閉チェック(0が合格):', dg.check_leaks()); print('扉・レバーチェック(空が合格):', dg.check_doors()); print('戻り検査(空が合格):', dg.check_return((6, FY, 6)))
r = dg.solve(start=(6, FY, 6)); print('開いた扉', len(r['opened']), '/', r['doors'], ' 到達できた宝箱', r['chests_ok'], '/', r['chests'])
print('マップ:', dg.render_map(out.replace('.bp', '_map.png'), FY, (0, 49), (0, 29), title='example dungeon'))
# 6) 保存（宝箱の中身・スポナーを BlockEntities として書く）
b.BE = dg.block_entities()
b.save(out, 'Example Dungeon', author='nemo', tags=['dungeon', 'example'])
