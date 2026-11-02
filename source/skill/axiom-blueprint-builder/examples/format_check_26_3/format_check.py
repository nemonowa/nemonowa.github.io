"""26.3 形式の確認用ブループリント（小さな祠＋BE/エンティティ全種）。
実機で貼って確認する項目：宝箱(ルートテーブル)・宝箱(中身直入れ)・スポナー(名前/体力/ドロップ)・書見台の本・看板・防具立て・鉄の鎖(iron_chain)。
  cd scripts && python3 ../examples/format_check_26_3/format_check.py OUT_DIR
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from builder import *
from nbt_helpers import chest_loot, chest_items, spawner, armor_stand, give_book_command
from interior_helpers import lectern_with_book, wall_sign

out = sys.argv[1] if len(sys.argv) > 1 else '.'
b = Build(); b.BE = []; b.ENT = []
b.box(-3, -1, -3, 3, -1, 3, lambda x, y, z: pick([('stone_bricks', 5), ('cracked_stone_bricks', 1), ('mossy_stone_bricks', 1)], x, y, z))
for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
    b.box(x, 0, z, x, 2, z, 'stripped_spruce_log', axis='y')
b.box(-3, 3, -3, 3, 3, 3, 'spruce_planks')
b.roof_layer(0, 0, 4, 3, 3, full='spruce_planks', stair='spruce_stairs')
b.put(0, 2, 0, 'iron_chain', axis='y', waterlogged='false'); b.put(0, 1, 0, 'lantern', hanging='true', waterlogged='false')
# 宝箱2つ・スポナー・書見台・看板
b.put(-2, 0, -2, 'chest', facing='south', type='single', waterlogged='false'); b.BE.append(chest_loot(-2, 0, -2, 'simple_dungeon'))
b.put(2, 0, -2, 'chest', facing='south', type='single', waterlogged='false'); b.BE.append(chest_items(2, 0, -2, [('diamond', 3), ('bread', 16), ('iron_ingot', 8)]))
b.put(0, 0, -2, 'spawner'); b.BE.append(spawner(0, 0, -2, 'zombie', name='番兵', health=40, loot='minecraft:entities/zombie', light=(0, 15)))
cmd = lectern_with_book(b, -2, 0, 2, 'north', '26.3 形式テスト', ['1ページ目\nこの本が読めれば\n書見台BEは成功', '2ページ目'])
wall_sign(b, 2, 1, -3, 'west', ['26.3', 'format check', 'by nemo', ''])
b.ENT.append(armor_stand(2.5, 0, 2.5, name='案内人', yaw=180, gravity=False))
b.save(os.path.join(out, 'format_check_26_3.bp'), '26.3 形式チェック', tags=['test', '26.3'])
open(os.path.join(out, 'format_check_26_3_commands.txt'), 'w', encoding='utf8').write(cmd + '\n')
print(cmd)
