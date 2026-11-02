"""浮遊島ダンジョンの『テーマ』定義（春=桜 / 夏=ひまわり / 秋=楓）。island_dungeon.py が THEMES[名前] を読む。
新しい季節（冬・夜・海…）は、下の SPRING をコピーして値を差し替えるだけ。形（島・幹・ダンジョンの寸法）は共通で、変わるのは素材と意匠:
  地形(地表・岩ミックス・底の灯り) / 広場の床紋様 / 月門・立石・遺跡の素材 / 樹(幹・葉・落ち葉) / 小島・背面レリーフ・飾り / ダンジョンの木部素材
葉ブロックは leaf(X,Y,Z)->(名前, プロパティ)。葉の代わりにウール等（プロパティ無し）も可（秋）。
"""
import sys, os, math, random
from types import SimpleNamespace as NS
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
from builder import *
from pattern_helpers import *

GR = lambda: {'snowy': 'false'}
def _grass(v, x, y, z, rim):
    n = 'grass_block' if v > 0.22 else rim(x, y, z)
    return n, ({'snowy': 'false'} if n in ('grass_block', 'podzol') else {})

# ---------------------------------------------------------------- 春: 桜 ----
def spring_plaza(x, z, PC):
    P12 = polygon_points(14.4, 12); ST5 = [(P12[k], P12[(k + 5) % 12]) for k in range(12)]
    HEX = hexagram_segments(6.6) if False else [(p[k], p[(k + 2) % 6]) for p in (polygon_points(6.6, 6), polygon_points(6.6, 6, 90)) for k in range(6)]
    dx, dz = x - PC[0], z - PC[1]; r = math.hypot(dx, dz)
    if r > 18.4: return None
    out = pick([('stone_bricks', 55), ('mossy_stone_bricks', 17), ('cracked_stone_bricks', 14), ('polished_andesite', 10), ('smooth_quartz', 4)], x, 0, z)
    if r > 15.8 and h3(x, 3, z) % 5 == 0: out = 'moss_block'
    if abs(r - 17.7) < 0.6: out = 'gold_block'
    if abs(r - 16.3) < 0.55: out = 'lapis_block'
    if abs(r - 12.3) < 0.5: out = 'cyan_concrete'
    for (A, B) in ST5:
        if seg_dist(dx, dz, A[0], A[1], B[0], B[1]) < 0.6: out = 'light_blue_concrete'
    for (A, B) in HEX:
        if seg_dist(dx, dz, A[0], A[1], B[0], B[1]) < 0.55: out = 'amethyst_block'
    if abs(r - 8.6) < 0.55: out = 'lapis_block'
    if abs(r - 7.5) < 0.45: out = 'gold_block'
    for k in range(12):
        c = D(-90 + 30 * k + 15); px, pz = 11.2 * math.cos(c), 11.2 * math.sin(c); dd = abs(dx - px) + abs(dz - pz)
        if dd < 2.0: out = 'quartz_block' if dd > 0.9 else 'gold_block'
    for (vx, vz) in P12:
        dd = math.hypot(dx - vx, dz - vz)
        if dd < 2.2: out = 'gold_block' if dd > 1.2 else 'sea_lantern'
    if r < 3.2: out = 'gold_block' if r > 1.6 else 'sea_lantern'
    return out

def spring_back(b, MX=10, MY=60, MZ=-70):
    for x in range(-28, 29):
        for y in range(-28, 29):
            d1 = math.hypot(x, y); d2 = math.hypot(x - 9, y - 3)
            if d1 <= 26 and d2 > 22.5:
                e = min(26 - d1, d2 - 22.5); n = 'calcite' if e < 2.2 else 'sea_lantern'
                for z in (MZ, MZ + 1): b.put(MX + x, MY + y, z, n)
    rs = random.Random(5)
    for _ in range(70):
        x = rs.randint(-70, 75); y = rs.randint(18, 95); z = rs.randint(-85, -45)
        if math.hypot(x - MX, y - MY) < 31: continue
        b.put(x, y, z, 'sea_lantern')
        if rs.random() < .3:
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)): b.put(x + dx, y + dy, z, 'white_stained_glass')

def spring_decorate(b, G):
    b.ground_cover(['short_grass', 'short_grass', 'fern', 'lily_of_the_valley', 'azure_bluet', 'cornflower', 'allium', 'blue_orchid', 'pink_tulip', 'flowering_azalea'], every=6)

def spring_litter(b, G, TX, TZ):
    for dx in range(-26, 27):
        for dz in range(-26, 27):
            X, Z = TX + dx, TZ + dz
            if (X, Z) in G and b.get(X, G[(X, Z)], Z) in ('grass_block', 'moss_block') and math.hypot(dx, dz) < 24 and h3(X, 5, Z) % 4 == 0:
                b.put_if_empty(X, G[(X, Z)] + 1, Z, 'pink_petals', facing='north', flower_amount=str(1 + h3(X, 2, Z) % 4))

def spring_crystal(b, x, y, z, h=6):
    for k in range(h): b.put(x, y + k, z, 'amethyst_block')
    b.put(x, y + h, z, 'amethyst_cluster', facing='up', waterlogged='false')
    for (dx, dz, f) in ((1, 0, 'east'), (-1, 0, 'west'), (0, 1, 'south'), (0, -1, 'north')):
        b.put_if_empty(x + dx, y + 1 + (h3(x + dx, y, z + dz) % 3), z + dz, 'amethyst_cluster', facing=f, waterlogged='false')

def _leaf_accent_spring(X, Y, Z, hh, up):
    if up and hh % 9 == 0: return 'pink_wool', {}
    if up and hh % 19 == 1: return 'white_wool', {}
    if hh % 53 == 2: return 'shroomlight', {}
    if hh % 61 == 3: return 'flowering_azalea_leaves', LEAF
    return None

SPRING = NS(
    name='spring', title='月の聖樹(春・桜)',
    surface=lambda v, x, y, z: _grass(v, x, y, z, lambda x, y, z: 'moss_block' if h3(x, y, z) % 3 else 'stone'),
    rim_mix=[('stone', 50), ('andesite', 25), ('mossy_cobblestone', 15), ('cobblestone', 10)],
    mid_mix=[('stone', 40), ('andesite', 20), ('tuff', 18), ('mossy_cobblestone', 6), ('cobblestone', 8), ('calcite', 3), ('dripstone_block', 5)],
    deep_mix=[('tuff', 34), ('deepslate', 30), ('stone', 16), ('cobbled_deepslate', 12), ('calcite', 4), ('amethyst_block', 2), ('dripstone_block', 2)],
    under=lambda b, x, yb, z: (b.put(x, yb - 1, z, 'amethyst_block'), b.put(x, yb - 2, z, pick([('amethyst_cluster', 3), ('large_amethyst_bud', 1)], x, 3, z), facing='down', waterlogged='false')),
    plaza=spring_plaza,
    gate_inner=('gold_block', 'chiseled_quartz_block'), gate_body=[('quartz_block', 45), ('smooth_quartz', 30), ('quartz_bricks', 25)], gate_edge='quartz_pillar', lamp='sea_lantern',
    stone_shaft=[('stone_bricks', 60), ('mossy_stone_bricks', 25), ('cracked_stone_bricks', 15)], stone_base='chiseled_stone_bricks', stone_cap='amethyst_block',
    stone_top=('amethyst_cluster', {'facing': 'up', 'waterlogged': 'false'}), foot=('amethyst_cluster', {'facing': 'up', 'waterlogged': 'false'}),
    ruin_floor=('smooth_quartz', 'polished_andesite'), ruin_col=('quartz_pillar', {'axis': 'y'}), ruin_cap='chiseled_quartz_block', ruin_slab='quartz_slab', ruin_rubble='quartz_block',
    altar=('chiseled_quartz_block', 'smooth_quartz', 'quartz_block', 'chiseled_quartz_block'), relic_shell='amethyst_block', relic_core='sea_lantern',
    trunk_mix=[('cherry_log', 48), ('dark_oak_log', 20), ('stripped_cherry_log', 10), ('cherry_wood', 22)], vein=('pearlescent_froglight', {'axis': 'y'}),
    log_mix=[('cherry_log', 70), ('dark_oak_log', 20), ('cherry_wood', 10)],
    leaf=lambda X, Y, Z, F=None: ('cherry_leaves', LEAF), leaf_accent=_leaf_accent_spring, litter=spring_litter,
    islet_top=lambda x, y, z: ('grass_block', {'snowy': 'false'}), islet_under=('amethyst_cluster', {'facing': 'down', 'waterlogged': 'false'}),
    crystal=spring_crystal, back=spring_back, decorate=spring_decorate,
    tree_wall=[('stripped_cherry_wood', 34), ('cherry_planks', 30), ('dark_oak_planks', 22), ('stripped_dark_oak_log', 14)],
    tree_ceil=[('cherry_planks', 40), ('dark_oak_planks', 30), ('stripped_cherry_wood', 30)], tree_floor=[('spruce_planks', 50), ('dark_oak_planks', 30), ('cherry_planks', 20)],
    spawner_log='cherry_log', canopy_floor=('cherry_planks', 'stripped_cherry_wood'), canopy_door_slab='cherry_slab', door_frame='stripped_cherry_wood',
    canopy_seal=lambda X, Y, Z: (('shroomlight', {}) if h3(X, Y, Z) % 9 == 0 else ('cherry_leaves', LEAF)),
    vault_floor=('gold_block', 'lapis_block'), vault_pillar=('quartz_pillar', {'axis': 'y'}), dais=('chiseled_quartz_block', 'smooth_quartz'),
    deco_up=('amethyst_cluster', {'facing': 'up', 'waterlogged': 'false'}), canopy_light='sea_lantern', mob_zombie='zombie',
)

# ---------------------------------------------------------------- 秋: 楓 ----
_YF = [('yellow_wool', 34), ('honeycomb_block', 22), ('orange_wool', 30), ('yellow_terracotta', 14)]
_OF = [('orange_wool', 40), ('orange_terracotta', 20), ('raw_copper_block', 9), ('red_wool', 17), ('honeycomb_block', 14)]
_RF = [('red_wool', 32), ('nether_wart_block', 38), ('red_terracotta', 14), ('orange_wool', 16)]
def autumn_leaf(X, Y, Z, Y0=4):
    hh = h3(X, Y, Z)
    if hh % 67 == 2: return 'shroomlight', {}
    v = noise(X, Y, Z, 6) + 0.045 * (Y - (Y0 + 34)) + (hh % 7 - 3) * 0.045      # 上ほど黄、下ほど赤
    return pick(_YF if v > 0.42 else (_OF if v > -0.22 else _RF), X, Y, Z), {}

def autumn_plaza(x, z, PC):
    dx, dz = x - PC[0], z - PC[1]; r = math.hypot(dx, dz)
    if r > 18.4: return None
    al = math.degrees(math.atan2(dx, -dz))                                       # 北=0°、東が正
    out = pick([('stone_bricks', 42), ('polished_granite', 18), ('cracked_stone_bricks', 12), ('mossy_stone_bricks', 8), ('polished_andesite', 12), ('granite', 8)], x, 0, z)
    if r > 15.6 and h3(x, 3, z) % 6 == 0: out = pick([('orange_terracotta', 1), ('red_terracotta', 1), ('yellow_terracotta', 1)], x, 1, z)
    if abs(r - 17.7) < 0.6: out = 'gold_block'
    if abs(r - 16.3) < 0.55: out = 'orange_concrete'
    lr = lobed_leaf_r(al, MAPLE5)
    if r <= lr:
        f = r / lr
        out = 'yellow_concrete' if f < 0.28 else ('orange_concrete' if f < 0.58 else ('red_concrete' if f < 0.86 else 'red_nether_bricks'))
        for (psi, L, w) in MAPLE5:
            if angd(al, psi) * math.pi / 180 * r < 0.55 and 2.0 < r < L * 0.92 and f < 0.9: out = 'gold_block'      # 葉脈
    if abs(dx) < 0.6 and 2.2 < dz < 15.4 and r > lr - 0.3: out = 'brown_concrete'                                    # 葉柄
    for k in range(8):
        c = D(22.5 + 45 * k); dd = math.hypot(dx - 15.5 * math.cos(c), dz - 15.5 * math.sin(c))
        if dd < 1.5: out = 'gold_block' if dd > 0.8 else 'shroomlight'
    if r < 1.6: out = 'shroomlight'
    return out

def momiji_relief_cell(dx, dy, SC=1.25):
    dx, dy = dx / SC, dy / SC; r = math.hypot(dx, dy); al = math.degrees(math.atan2(dx, dy)); out = []
    lr = lobed_leaf_r(al, MOMIJI7, base=6.0, power=1.25, floor=0.16, serration=0.045, freq=26)
    veins = []
    for (psi, L, w) in MOMIJI7:
        a = D(psi); ux, uy = math.sin(a), math.cos(a); veins.append((0, 0, ux * L * .92, uy * L * .92))
        for fr in (.38, .62):
            for sg in (-1, 1):
                a2 = D(psi + sg * 38); veins.append((ux * L * fr, uy * L * fr, ux * L * fr + math.sin(a2) * L * .26, uy * L * fr + math.cos(a2) * L * .26))
    if r <= lr:
        f = r / lr
        base = 'honeycomb_block' if f < .34 else ('orange_concrete' if f < .64 else ('red_concrete' if f < .88 else 'nether_wart_block'))
        out.append((0, base))
        if lr - r > 1.3: out.append((1, base))
        if (any(seg_dist(dx, dy, *v) < .62 for v in veins) and r > 1.0) or r < 3.0: out.append((2, 'shroomlight'))
    if abs(dx) < .9 and -15 < dy <= 2: out += [(0, 'brown_concrete'), (1, 'brown_concrete')]
    return out

def autumn_back(b, RX=10, RY=58, RZ=-72):
    put_relief(b, RX, RY, RZ, momiji_relief_cell, range(-40, 41), range(-26, 40))

def autumn_decorate(b, G):
    b.ground_cover(['orange_carpet', 'red_carpet', 'yellow_carpet', 'brown_carpet', 'short_grass', 'fern', 'pumpkin', 'brown_mushroom', 'red_mushroom', 'orange_carpet', 'red_carpet', 'short_grass'],
                   every=4, on=('grass_block', 'podzol', 'coarse_dirt', 'rooted_dirt'))

def autumn_litter(b, G, TX, TZ):
    for dx in range(-26, 27):
        for dz in range(-26, 27):
            X, Z = TX + dx, TZ + dz
            if (X, Z) in G and b.get(X, G[(X, Z)], Z) in ('grass_block', 'podzol', 'coarse_dirt', 'rooted_dirt') and math.hypot(dx, dz) < 25 and h3(X, 5, Z) % 3 == 0:
                b.put_if_empty(X, G[(X, Z)] + 1, Z, pick([('orange_carpet', 3), ('red_carpet', 3), ('yellow_carpet', 3), ('brown_carpet', 1)], X, 2, Z))

def _candle(color, n=3): return (color + '_candle', {'candles': str(n), 'lit': 'true', 'waterlogged': 'false'})
def autumn_crystal(b, x, y, z, h=6):
    for k in range(h): b.put(x, y + k, z, 'copper_block' if k % 3 == 0 else 'raw_copper_block')
    b.put(x, y + h, z, 'shroomlight')
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b.put_if_empty(x + dx, y, z + dz, 'orange_candle', candles=str(1 + h3(x + dx, y, z + dz) % 4), lit='true', waterlogged='false')

AUTUMN = NS(**{**SPRING.__dict__,
    'name': 'autumn', 'title': '紅葉の楓島',
    'surface': lambda v, x, y, z: _grass(v, x, y, z, lambda x, y, z: 'granite' if h3(x, y, z) % 3 else 'stone') if v <= 0.22 else
               (pick([('grass_block', 38), ('podzol', 38), ('coarse_dirt', 14), ('rooted_dirt', 10)], x, y, z), {'snowy': 'false'}),
    'rim_mix': [('stone', 40), ('granite', 25), ('andesite', 15), ('cobblestone', 10), ('coarse_dirt', 10)],
    'mid_mix': [('stone', 34), ('granite', 22), ('andesite', 16), ('tuff', 12), ('cobblestone', 6), ('mossy_cobblestone', 4), ('dripstone_block', 4), ('red_sandstone', 2)],
    'deep_mix': [('tuff', 30), ('deepslate', 28), ('granite', 14), ('stone', 14), ('cobbled_deepslate', 10), ('raw_copper_block', 2), ('dripstone_block', 2)],
    'under': lambda b, x, yb, z: (b.put(x, yb - 1, z, 'raw_copper_block'), b.put(x, yb - 2, z, 'shroomlight')),
    'plaza': autumn_plaza,
    'gate_inner': ('gold_block', 'cut_copper'), 'gate_body': [('dark_oak_planks', 40), ('spruce_planks', 35), ('mangrove_planks', 25)], 'gate_edge': 'stripped_dark_oak_log', 'lamp': 'shroomlight',
    'stone_shaft': [('granite', 40), ('stone_bricks', 35), ('polished_granite', 25)], 'stone_base': 'chiseled_stone_bricks', 'stone_cap': 'copper_block',
    'stone_top': _candle('orange', 4), 'foot': _candle('red'),
    'ruin_floor': ('smooth_red_sandstone', 'polished_granite'), 'ruin_col': ('cut_red_sandstone', {}), 'ruin_cap': 'chiseled_red_sandstone', 'ruin_slab': 'cut_red_sandstone_slab', 'ruin_rubble': 'red_sandstone',
    'altar': ('chiseled_red_sandstone', 'smooth_red_sandstone', 'red_sandstone', 'chiseled_red_sandstone'), 'relic_shell': 'orange_stained_glass', 'relic_core': 'shroomlight',
    'trunk_mix': [('spruce_log', 42), ('dark_oak_log', 30), ('stripped_spruce_log', 8), ('spruce_wood', 20)], 'vein': ('ochre_froglight', {'axis': 'y'}),
    'log_mix': [('spruce_log', 60), ('dark_oak_log', 28), ('spruce_wood', 12)],
    'leaf': lambda X, Y, Z, F=None: autumn_leaf(X, Y, Z), 'leaf_accent': lambda *a: None, 'litter': autumn_litter,
    'islet_top': lambda x, y, z: (pick([('grass_block', 50), ('podzol', 50)], x, y, z), {'snowy': 'false'}), 'islet_under': ('shroomlight', {}),
    'crystal': autumn_crystal, 'back': autumn_back, 'decorate': autumn_decorate,
    'tree_wall': [('stripped_spruce_wood', 34), ('spruce_planks', 30), ('dark_oak_planks', 22), ('stripped_dark_oak_log', 14)],
    'tree_ceil': [('spruce_planks', 40), ('dark_oak_planks', 30), ('stripped_spruce_wood', 30)], 'tree_floor': [('spruce_planks', 50), ('dark_oak_planks', 30), ('jungle_planks', 20)],
    'spawner_log': 'spruce_log', 'canopy_floor': ('spruce_planks', 'stripped_spruce_wood'), 'canopy_door_slab': 'spruce_slab', 'door_frame': 'stripped_spruce_wood',
    'canopy_seal': lambda X, Y, Z: ('shroomlight', {}) if h3(X, Y, Z) % 9 == 0 else autumn_leaf(X, Y, Z),
    'vault_floor': ('gold_block', 'copper_block'), 'vault_pillar': ('stripped_spruce_log', {'axis': 'y'}), 'dais': ('chiseled_red_sandstone', 'smooth_red_sandstone'),
    'deco_up': _candle('orange'), 'canopy_light': 'shroomlight', 'mob_zombie': 'zombie',
})

# ---------------------------------------------------------------- 夏: ひまわり ----
def summer_plaza(x, z, PC):
    dx, dz = x - PC[0], z - PC[1]; r = math.hypot(dx, dz)
    if r > 18.4: return None
    th = math.degrees(math.atan2(dz, dx)) % 360
    out = pick([('smooth_sandstone', 30), ('cut_sandstone', 24), ('sandstone', 16), ('stone_bricks', 14), ('mossy_stone_bricks', 8), ('polished_andesite', 8)], x, 0, z)
    if r > 15.6 and h3(x, 3, z) % 6 == 0: out = 'moss_block'
    if abs(r - 17.7) < 0.6: out = 'gold_block'
    if abs(r - 16.3) < 0.55: out = 'lime_concrete'
    for k in range(16):                                                        # 内側の花弁(橙)
        h = petal_hit(th, r, 22.5 * k + 11.25, 5.4, 11.6, 1.9)
        if h: out = 'honeycomb_block' if h[1] > 0.5 else 'orange_concrete'
    for k in range(16):                                                        # 外側の花弁(黄・中心線と先端が橙)
        h = petal_hit(th, r, 22.5 * k, 7.0, 14.8, 2.35)
        if h:
            t, v, w = h; out = 'yellow_concrete'
            if (v < 0.55 and 0.12 < t < 0.88) or t > 0.9: out = 'orange_concrete'
    if r <= 6.2:                                                               # 種(螺旋)
        ph = math.sin(r * 2.3 + D(th) * 5)
        out = 'brown_concrete' if ph > 0.25 else ('black_concrete' if ph < -0.55 else 'brown_terracotta')
        if abs(r - 6.0) < 0.45: out = 'orange_terracotta'
    if r < 1.6: out = 'shroomlight'
    for k in range(8):
        c = D(22.5 + 45 * k); dd = math.hypot(dx - 15.4 * math.cos(c), dz - 15.4 * math.sin(c))
        if dd < 1.5: out = 'gold_block' if dd > 0.8 else 'sea_lantern'
    return out

_SEEDS = phyllotaxis(190)
def sunflower_relief_cell(dx, dy):
    r = math.hypot(dx, dy); th = math.degrees(math.atan2(dy, dx)) % 360; out = []
    def leaf(cx, cy, rx, ry, ang):
        a = D(ang); u = (dx - cx) * math.cos(a) + (dy - cy) * math.sin(a); v = -(dx - cx) * math.sin(a) + (dy - cy) * math.cos(a)
        return (u / rx) ** 2 + (v / ry) ** 2, v
    if abs(dx) <= 1.3 and -50 <= dy < -22: out += [(0, 'green_concrete'), (1, 'green_concrete')]
    for (cx, cy, rx, ry, ang) in ((-8, -36, 9, 4.2, 28), (8, -42, 9, 4.2, 152)):
        q, v = leaf(cx, cy, rx, ry, ang)
        if q <= 1:
            out = [(0, 'lime_concrete')] + ([(1, 'lime_concrete')] if q < .7 else []) + ([(2, 'green_concrete')] if abs(v) < .6 else [])
    inner = None
    for k in range(26):
        h = petal_hit(th, r, 360 / 26 * k + 6.9, 9.0, 20.0, 2.0)
        if h: inner = h
    if inner and r > 9: out = [(0, 'orange_concrete')] + ([(1, 'honeycomb_block')] if inner[1] < inner[2] - 1.0 else [])
    for k in range(26):
        h = petal_hit(th, r, 360 / 26 * k, 9.5, 24.8, 2.5)
        if h:
            t, v, w = h; out = [(0, 'yellow_concrete')] + ([(1, 'yellow_concrete')] if v < w - 1.0 else []) + ([(2, 'orange_concrete')] if v < .55 and .12 < t < .9 else [])
    if r <= 10.3:
        out = [(0, 'brown_concrete')] + ([(1, 'orange_terracotta')] if 8.2 <= r <= 10.3 else [])
        n = _SEEDS.get((round(dx), round(dy)))
        if n and r < 8.3:
            out.append((1, 'black_concrete'))
            if n % 4 == 0: out.append((2, 'shroomlight'))
    return out

def summer_back(b, RX=10, RY=70, RZ=-72):
    put_relief(b, RX, RY, RZ, sunflower_relief_cell, range(-30, 31), range(-50, 30))

def _cloud(b, cx, cy, cz, rx, ry, rz, seed):
    r = random.Random(seed)
    for _ in range(7):
        px, py, pz = cx + r.uniform(-rx, rx) * .7, cy + r.uniform(-ry, ry) * .4, cz + r.uniform(-rz, rz) * .7
        a, bb, c = r.uniform(.45, .8) * rx, r.uniform(.5, .9) * ry, r.uniform(.45, .8) * rz
        for x in range(int(px - a) - 1, int(px + a) + 2):
            for y in range(int(py - bb) - 1, int(py + bb) + 2):
                for z in range(int(pz - c) - 1, int(pz + c) + 2):
                    if ((x - px) / a) ** 2 + ((y - py) / bb) ** 2 * 1.4 + ((z - pz) / c) ** 2 <= 1 and b.empty(x, y, z): b.put(x, y, z, 'white_wool')

def summer_decorate(b, G):
    b.ground_cover(['short_grass', 'short_grass', 'fern', 'dandelion', 'poppy', 'cornflower', 'oxeye_daisy', 'azure_bluet', 'blue_orchid', 'lily_of_the_valley'], every=6)
    top = {}
    for (x, y, z) in list(b.B):
        if y > top.get((x, z), -999): top[(x, z)] = y
    for (x, z), y in top.items():                                              # ひまわり畑(二段の植物: lower+upper)
        if b.get(x, y, z) == 'grass_block' and noise(x, 0, z, 7) > -0.15 and h3(x, y, z) % 3 == 0 and b.empty(x, y + 1, z) and b.empty(x, y + 2, z):
            b.put(x, y + 1, z, 'sunflower', half='lower'); b.put(x, y + 2, z, 'sunflower', half='upper')
    for k, c in enumerate(((-78, 34, -18, 16, 6, 10), (78, 46, -8, 14, 5, 10), (-50, 70, 54, 13, 5, 9), (66, 18, 62, 15, 6, 10), (-4, 88, -52, 15, 5, 9),
                           (-86, 8, 22, 14, 5, 9), (10, -56, 12, 26, 7, 20), (-48, -46, -26, 16, 6, 12), (46, -44, 26, 14, 5, 10))):
        _cloud(b, *c, k + 3)

def summer_crystal(b, x, y, z, h=6):
    for k in range(h): b.put(x, y + k, z, 'prismarine_bricks' if k % 3 else 'dark_prismarine')
    b.put(x, y + h, z, 'sea_lantern')
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b.put_if_empty(x + dx, y, z + dz, 'yellow_candle', candles=str(1 + h3(x + dx, y, z + dz) % 4), lit='true', waterlogged='false')

_LEAF_SUMMER = lambda X, Y, Z: pick([('oak_leaves', 44), ('jungle_leaves', 30), ('birch_leaves', 22), ('azalea_leaves', 4)], X, Y, Z)
def _leaf_accent_summer(X, Y, Z, hh, up):
    if up and hh % 23 == 0: return 'yellow_wool', {}
    if hh % 71 == 2: return 'verdant_froglight', {'axis': 'y'}
    return None

SUMMER = NS(**{**SPRING.__dict__,
    'name': 'summer', 'title': '夏のひまわり島',
    'surface': lambda v, x, y, z: _grass(v, x, y, z, lambda x, y, z: pick([('sandstone', 45), ('cut_sandstone', 30), ('smooth_sandstone', 25)], x, y, z)),   # 縁は砂浜
    'rim_mix': [('sandstone', 45), ('stone', 25), ('andesite', 15), ('cut_sandstone', 15)],
    'mid_mix': [('stone', 38), ('andesite', 20), ('tuff', 14), ('diorite', 8), ('calcite', 8), ('sandstone', 6), ('dripstone_block', 6)],
    'deep_mix': [('tuff', 32), ('deepslate', 28), ('stone', 16), ('cobbled_deepslate', 10), ('calcite', 6), ('prismarine', 4), ('dripstone_block', 4)],
    'under': lambda b, x, yb, z: (b.put(x, yb - 1, z, 'prismarine'), b.put(x, yb - 2, z, 'sea_lantern')),
    'plaza': summer_plaza,
    'gate_inner': ('gold_block', 'dark_prismarine'), 'gate_body': [('prismarine_bricks', 45), ('prismarine', 30), ('calcite', 25)], 'gate_edge': 'quartz_pillar', 'lamp': 'sea_lantern',
    'stone_shaft': [('cut_sandstone', 55), ('smooth_sandstone', 25), ('sandstone', 20)], 'stone_base': 'chiseled_sandstone', 'stone_cap': 'gold_block',
    'stone_top': _candle('yellow', 4), 'foot': _candle('lime'),
    'ruin_floor': ('smooth_sandstone', 'cut_sandstone'), 'ruin_col': ('cut_sandstone', {}), 'ruin_cap': 'chiseled_sandstone', 'ruin_slab': 'cut_sandstone_slab', 'ruin_rubble': 'sandstone',
    'altar': ('chiseled_sandstone', 'smooth_sandstone', 'sandstone', 'chiseled_sandstone'), 'relic_shell': 'yellow_stained_glass', 'relic_core': 'glowstone',
    'trunk_mix': [('oak_log', 40), ('jungle_log', 30), ('stripped_oak_log', 10), ('oak_wood', 20)], 'vein': ('verdant_froglight', {'axis': 'y'}),
    'log_mix': [('oak_log', 55), ('jungle_log', 30), ('oak_wood', 15)],
    'leaf': lambda X, Y, Z, F=None: (_LEAF_SUMMER(X, Y, Z), LEAF), 'leaf_accent': _leaf_accent_summer, 'litter': lambda b, G, TX, TZ: None,
    'islet_top': lambda x, y, z: ('grass_block', {'snowy': 'false'}), 'islet_under': ('sea_lantern', {}),
    'crystal': summer_crystal, 'back': summer_back, 'decorate': summer_decorate,
    'tree_wall': [('stripped_jungle_wood', 34), ('jungle_planks', 30), ('dark_oak_planks', 22), ('stripped_dark_oak_log', 14)],
    'tree_ceil': [('jungle_planks', 40), ('dark_oak_planks', 30), ('stripped_jungle_wood', 30)], 'tree_floor': [('spruce_planks', 50), ('dark_oak_planks', 30), ('jungle_planks', 20)],
    'spawner_log': 'jungle_log', 'canopy_floor': ('jungle_planks', 'stripped_jungle_wood'), 'canopy_door_slab': 'jungle_slab', 'door_frame': 'stripped_jungle_wood',
    'canopy_seal': lambda X, Y, Z: ('verdant_froglight', {'axis': 'y'}) if h3(X, Y, Z) % 9 == 0 else (pick([('oak_leaves', 50), ('jungle_leaves', 30), ('birch_leaves', 20)], X, Y, Z), LEAF),
    'vault_floor': ('gold_block', 'prismarine_bricks'), 'vault_pillar': ('quartz_pillar', {'axis': 'y'}), 'dais': ('chiseled_sandstone', 'smooth_sandstone'),
    'deco_up': _candle('yellow'), 'canopy_light': 'glowstone', 'mob_zombie': 'husk',
})

THEMES = {'spring': SPRING, 'autumn': AUTUMN, 'summer': SUMMER}
if __name__ == '__main__': print({k: v.title for k, v in THEMES.items()})
