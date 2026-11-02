import sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from world import *
from pagoda import pagoda
from buildings import *
from dungeon import dungeon, CHESTS, SPAWNERS, INFO

b = Build(); rnd = random.Random(7)
terrain(b)

# ---- 道（石畳）
MAIN = [(-38,5),(-30,8),(-22,6),(-17,1),(-11,1),(-8,-5),(-3,-8),(4,-8),(10,-10),(14,-10),(22,-11),(30,-9),(40,-8),(46,-12),(46,-27)]
lay_path(b, MAIN, 3.4)
lay_path(b, [(-27,9),(-25,16),(-20,24),(-14,31),(-8,32)], 3.0)                     # 東屋へ
lay_path(b, [(30,-9),(31,0),(31,8),(25,17),(22,27),(26,36),(36,36)], 3.0)          # 蔵へ
lay_path(b, [(24,-11),(24,-11)], 5.0)                                              # 社殿前の広場
lay_path(b, [(46,-8),(49,-7)], 2.6)
lay_path(b, [(-22,5),(-22,-2),(-21,-10),(-20,-16)], 2.4)                         # 小堂への小径
# ---- 水（小川・池）
carve_water(b, stream_cells([(-17,-14),(-13,-10),(-12,-5),(-13.5,0),(-14,4),(-17,8),(-19,11)], 2.6))
carve_water(b, pond_cells(-19, 12, 4.5, 3.2))
carve_water(b, pond_cells(38, -14, 6.5, 4))
for (x, z) in pond_cells(38, -14, 6, 3.5):
    if h3(x, 1, z) % 7 == 0 and b.get(x, G[(x, z)], z) == 'water': b.put_if_empty(x, G[(x, z)]+1, z, 'lily_pad')
for (x, z) in pond_cells(-19, 12, 4, 3):
    if h3(x, 1, z) % 6 == 0 and b.get(x, G[(x, z)], z) == 'water': b.put_if_empty(x, G[(x, z)]+1, z, 'lily_pad')

# ---- 建物
pagoda(b, -38, -12)
shrine(b, 24, -22)
pavilion(b, -8, 24)
storehouse(b, 36, 28)
small_hall(b, -20, -20, 2, 2, 2, post='dark_oak_log', panel='white_concrete', roof_hr=3)
small_hall(b, 49, -5, 0, 2, 2, post='red_concrete', panel='red_concrete', roof_hr=2)
temizuya(b, 34, -5)
taiko_bridge(b, -17, 0)
torii(b, 46, 1, -16, axis='x', w=3, h=7); torii(b, 46, 1, -23, axis='x', w=3, h=7)
for z in range(-8, -3): pass

# ---- 灯籠
def toro_at(x, z):
    if (x, z) in G and b.get(x, G[(x, z)], z) not in ('water',) and b.empty(x, G[(x, z)]+1, z): toro(b, x, G[(x, z)]+1, z)
for p in [(-45,5),(-31,5),(-24,9),(-9,3),(8,-12),(16,-8),(30,-12),(42,-10),(48,-18),(13,-24),(-9,25),(24,34),(-20,-12)]: toro_at(*p)

# ---- 植栽
sakura(b, -21, 5, 9, 5.8); sakura(b, 10, -14, 8, 5.2); sakura(b, 52, -19, 9, 5.5)
for (x, z, h, w) in [(0,-12,9,1.0),(-26,11,8,1.0),(-47,9,8,.9),(8,-25,8,1.0),(37,-27,8,1.0),(-16,17,8,1.0),(50,-12,7,.9),(24,34,7,.9),(-34,12,7,.9)]:
    if (x, z) in G: pine(b, x, z, h=h, pads=4, wide=w)
for (x, z, h) in [(-20,-24,6),(-4,-3,6),(18,-6,6),(50,-20,6),(46,-3,5),(26,24,6),(-54,-14,7),(-12,34,5),(14,-27,6),(-8,-22,6)]:
    if (x, z) in G and b.get(x, G[(x, z)], z) == 'grass_block': tree(b, x, z, h, 3.2)
grove(b, -57, 2, 6, 6, 40, 1); grove(b, -52, -24, 6, 3, 22, 2); grove(b, -46, -8, 3, 5, 10, 3); grove(b, -26, -28, 4, 2, 10, 4)
grove(b, 10, -30, 4, 3, 12, 5); grove(b, 34, -32, 4, 2, 10, 6); grove(b, -16, 30, 3, 3, 9, 7); grove(b, 22, 24, 3, 4, 8, 8); grove(b, 50, 30, 4, 4, 12, 9)
fence_line(b, [(-62,10),(-52,13),(-44,14)], None); fence_line(b, [(-15,36),(-2,36)], None); fence_line(b, [(24,38),(40,40)], None)
# 蔵の前の彼岸花と石
for _ in range(90):
    x, z = 36+rnd.randint(-14, 14), 28+rnd.randint(6, 12)
    if (x, z) in G and b.get(x, G[(x, z)], z) in ('grass_block', 'moss_block', 'podzol'): b.put_if_empty(x, G[(x, z)]+1, z, rnd.choice(['red_tulip', 'poppy', 'poppy']))
# 紫陽花（青い花）を塔の脇に
for _ in range(40):
    x, z = -58+rnd.randint(0, 6), -12+rnd.randint(0, 8)
    if (x, z) in G and b.get(x, G[(x, z)], z) == 'grass_block': b.put_if_empty(x, G[(x, z)]+1, z, rnd.choice(['cornflower', 'azure_bluet', 'blue_orchid']))
b.ground_cover(['short_grass', 'short_grass', 'fern', 'poppy', 'cornflower', 'azure_bluet', 'lily_of_the_valley', 'pink_petals', 'red_tulip', 'oxeye_daisy'], every=6)

# ---- 接地チェック：構造物の下に岩盤が無い柱は下へ補強（0が理想）
fixed = 0
for (x, y, z), (n, p) in list(b.B.items()):
    if y == 1 and n[10:] in ('stone_bricks', 'mossy_stone_bricks', 'cobblestone', 'andesite', 'polished_andesite', 'cracked_stone_bricks', 'tuff_bricks'):
        if not b.get(x, -5, z):
            fixed += 1
            for yy in range(-2, -7, -1): b.put_if_empty(x, yy, z, pick(ROCK, x, yy, z))
print('接地補強した柱:', fixed)
D = dungeon(b)
print('dungeon cells', INFO['cells'], 'leaks', INFO['leaks'], 'marker', INFO['marker'])
fix_connections(b)
LOOT = {'S1a': 'chests/simple_dungeon', 'S1b': 'chests/simple_dungeon', 'MZ': 'chests/jungle_temple', 'S2': 'chests/ruined_portal',
        'S3': 'chests/woodland_mansion', 'T1': 'chests/bastion_treasure', 'T2': 'chests/end_city_treasure', 'T3': 'chests/ancient_city'}
def build_block_entities():
    """ダンジョンの宝箱=ルートテーブル、スポナー=モブ設定。蔵の宝箱は村のルートテーブル。"""
    be = []; tagged = {(x, y, z): t for (x, y, z, t) in CHESTS}
    for (x, y, z), (n, p) in b.B.items():
        if n == 'minecraft:chest':
            loot = LOOT.get(tagged.get((x, y, z)), 'chests/village/village_plains_house')
            be.append((x, y, z, {'id': (8, 'minecraft:chest'), 'LootTable': (8, 'minecraft:' + loot)}))
    for (x, y, z, mob) in SPAWNERS:
        ent = (10, {'id': (8, 'minecraft:' + mob)})
        be.append((x, y, z, {'id': (8, 'minecraft:mob_spawner'),
            'SpawnData': (10, {'entity': ent}),
            'SpawnPotentials': (9, (10, [{'weight': (3, 1), 'data': (10, {'entity': ent})}])),
            'SpawnRange': (2, 6), 'RequiredPlayerRange': (2, 14), 'MaxNearbyEntities': (2, 5), 'SpawnCount': (2, 2),
            'MinSpawnDelay': (2, 200), 'MaxSpawnDelay': (2, 600), 'Delay': (2, 20)}))
    return be

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/island.bp'
    tags = ['japanese', 'pagoda', 'shrine', 'floating', 'interior', 'dungeon']
    b.BE = []
    b.save(out, '浮遊する和の島', author='nemo', tags=tags)
    if len(sys.argv) > 2:                                   # NBT入り版（宝箱ルートテーブル＋スポナー設定）
        b.BE = build_block_entities()
        b.save(sys.argv[2], '浮遊する和の島（宝箱・スポナー入り）', author='nemo', tags=tags+['nbt'])
        print('block entities:', len(b.BE))
    xs = [k[0] for k in b.B]; ys = [k[1] for k in b.B]; zs = [k[2] for k in b.B]
    print('extent', min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
