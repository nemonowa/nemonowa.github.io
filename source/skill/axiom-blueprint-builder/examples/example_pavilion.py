"""最小の完全な例：小島＋東屋＋桜＋提灯の綱。
python3 examples/example_pavilion.py  →  /mnt/user-data/outputs/example_pavilion.bp
新しい建築はこのファイルをコピーして書き換えるのが早い。"""
import sys, math, random
sys.path.insert(0, __file__.rsplit('/', 2)[0] + '/scripts')
from builder import *
b = Build(); rnd = random.Random(1)

# 1) 地形：ノイズで縁を揺らした円盤。上面=草、下に土と石
for x in range(-16, 17):
    for z in range(-16, 17):
        d = math.hypot(x, z) + 1.5*noise(x, 0, z, 4)
        if d > 15: continue
        depth = int((1-d/15)*6) + 1
        for y in range(-depth, 1):
            b.put(x, y, z, 'grass_block' if y == 0 else ('dirt' if y > -3 else 'stone'), **({'snowy': 'false'} if y == 0 else {}))

# 2) 東屋：基壇→柱→寄棟屋根（隅の反り）
b.box(-4, 1, -4, 4, 1, 4, 'smooth_stone')
for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
    b.box(x, 2, z, x, 5, z, 'stripped_dark_oak_log', axis='y')
b.box(-3, 6, -3, 3, 6, 3, 'dark_oak_planks')
b.hip_roof(0, 0, 7, 5, 5, full='deepslate_tiles', stair='deepslate_tile_stairs', slab='deepslate_tile_slab')
b.put(0, 5, 0, 'lantern', hanging='true', waterlogged='false')
for x in (-1, 0, 1): b.put(x, 1, 5, 'stone_brick_stairs', **ST('north'))   # 正面(+z)の石段

# 3) 桜：ベジェの幹＋殻状の樹冠＋花びら
top = b.tube((-9, 1, -8), (-9, 5, -8), (-7, 8, -9), (-6, 11, -8), 1.6, 0.8, 'cherry_log', axis='y')
leaves = b.shell(top[0], top[1]+2, top[2], 6, 3.5, 6, lambda x, y, z: 'cherry_leaves', **LEAF)
for (x, y, z) in leaves:
    if h3(x, y, z) % 23 == 0: b.hanging(x, y, z, 3, 'weeping')

# 4) 提灯の綱
b.rope((top[0], top[1], top[2]), (3, 6, -3), sag=2)

# 5) 下草
b.ground_cover(['short_grass', 'fern', 'pink_petals', 'short_grass', 'lily_of_the_valley'], every=5)

b.save('/mnt/user-data/outputs/example_pavilion.bp', '東屋の小島', tags=['sample', 'example'])
