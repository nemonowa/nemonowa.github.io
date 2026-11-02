"""社殿・東屋・蔵・小堂・手水舎・太鼓橋（すべて内装つき）"""
from lib import *
from pagoda import KIDAN

def platform(b, x0, z0, x1, z1, top=1, edge='polished_andesite'):
    for x in range(x0, x1+1):
        for z in range(z0, z1+1):
            for y in range(-3, top+1): b.put(x, y, z, pick(KIDAN, x, y, z))
            if x in (x0, x1) or z in (z0, z1): b.put(x, top, z, edge)
            for y in range(top+1, top+30): b.rm(x, y, z)

def steps(b, x0, x1, z, y, face='north'):
    for x in range(x0, x1+1): b.put(x, y, z, 'stone_brick_stairs', **ST(face)); b.put(x, y-1, z+1, 'stone_brick_stairs', **ST(face))

# ------------------------------------------------------------------ 社殿（浅草寺風：朱塗り＋入母屋＋唐破風の向拝）
def shrine(b, SX, SZ):
    hx, hz = 6, 4
    platform(b, SX-8, SZ-6, SX+8, SZ+9, 1)
    steps(b, SX-2, SX+2, SZ+10, 1)
    for s in (-3, 3): toro(b, SX+s*2+(1 if s > 0 else -1), 1, SZ+11)
    for dx in range(-hx, hx+1):
        for dz in range(-hz, hz+1):
            x, z = SX+dx, SZ+dz; edge = max(abs(dx)*hz, abs(dz)*hx) == hx*hz and (abs(dx) == hx or abs(dz) == hz)
            b.put(x, 2, z, 'dark_oak_planks' if edge else pick([('spruce_planks', 70), ('dark_oak_planks', 30)], x, 2, z))
            if not edge: continue
            post = abs(dx) in (hx, 3, 0) and abs(dz) == hz or abs(dx) == hx and dz in (-hz, 0, hz)
            pane = PANE_X if abs(dz) == hz else PANE_Z
            for y in range(3, 7):
                if post: b.put(x, y, z, 'red_concrete')
                elif y == 3: b.put(x, y, z, 'red_concrete')
                elif y == 6: b.put(x, y, z, 'red_terracotta' if False else 'red_concrete')
                else: b.put(x, y, z, 'white_stained_glass_pane', **pane)
            if post: b.put(x, 7, z, 'gold_block')
    for dx in range(-2, 3):                                  # 正面の出入口
        for y in range(3, 6): b.rm(SX+dx, y, SZ+hz)
    tile_roof(b, SX, SZ, 7, 9, 7, fill_r=3)
    gable_roof(b, SX, SZ, 7, 4, SZ+4, SZ+9, axis='z', end_mat='white_concrete', end_at=SZ+9, fill_r=4)
    b.put(SX, 11, SZ+9, 'gold_block'); b.put(SX, 10, SZ+9, 'red_concrete')        # 唐破風の金具と懸魚
    for s in (-3, 3):                                         # 向拝の柱
        for y in range(2, 7): b.put(SX+s, y, SZ+8, 'red_concrete')
        b.put(SX+s, 7, SZ+8, 'gold_block'); b.put(SX+s, 1, SZ+8, 'black_concrete')
    # 天井
    for dx in range(-hx+1, hx):
        for dz in range(-hz+1, hz): b.put_if_empty(SX+dx, 8, SZ+dz, 'dark_oak_planks' if dx % 2 == 0 else 'spruce_planks')
    # --- 内装：内陣の壇・神輿・赤絨毯・燈籠
    for dx in range(-3, 4):
        for dz in (-3, -2, -1): b.put(SX+dx, 3, SZ+dz, 'dark_oak_planks')
        b.put(SX+dx, 3, SZ, 'dark_oak_stairs', **ST('north'))
    for dx in range(-1, 2):
        for dz in (-3, -2):
            b.put(SX+dx, 4, SZ+dz, 'dark_oak_planks')
            for y in (5, 6): b.put(SX+dx, y, SZ+dz, 'red_concrete')
            b.put(SX+dx, 7, SZ+dz, 'deepslate_tile_slab', **SL)
    for y in (5, 6): b.put(SX, y, SZ-2, 'gold_block')
    for s in (-3, 3): b.put(SX+s, 4, SZ-2, 'white_candle', candles='4', lit='true', waterlogged='false'); b.put(SX+s, 4, SZ-3, 'lantern', hanging='false', waterlogged='false')
    for dz in range(1, 5): b.put(SX, 3, SZ+dz, 'red_carpet')
    for s in (-4, 4):
        b.put(SX+s, 3, SZ+1, 'decorated_pot'); b.put(SX+s, 3, SZ+2, 'decorated_pot'); b.put(SX+s, 3, SZ+3, 'chiseled_bookshelf', facing='west' if s > 0 else 'east')
        b.put(SX+s//2*1, 3, SZ+3, 'red_carpet'); b.put(SX+s//2, 3, SZ+2, 'red_carpet')
    for (dx, dz) in ((-4, -2), (4, -2), (-4, 2), (4, 2), (0, 2)): lantern_hang(b, SX+dx, 7, SZ+dz, 1)
    for s in (-5, 5): b.put(SX+s, 3, SZ-3, 'barrel', facing='up', open='false')
    # 向拝：賽銭箱・鈴・提灯
    b.put(SX, 2, SZ+7, 'barrel', facing='up', open='false'); b.put(SX, 3, SZ+7, 'dark_oak_trapdoor', facing='north', half='bottom', open='false', powered='false', waterlogged='false')
    b.put(SX, 6, SZ+7, 'iron_chain', axis='y', waterlogged='false'); b.put(SX, 5, SZ+7, 'bell', attachment='ceiling', facing='north', powered='false')
    for s in (-2, 2): lantern_hang(b, SX+s, 7, SZ+8, 2)
    for dx in (-2, 0, 2): b.put(SX+dx, 7, SZ+7, 'dark_oak_planks')

# ------------------------------------------------------------------ 東屋（開放的な大屋根・囲炉裏・茶の間）
def pavilion(b, CX, CZ):
    platform(b, CX-6, CZ-5, CX+6, CZ+5, 1)
    steps(b, CX-1, CX+1, CZ+6, 1)
    for dx in range(-4, 5):
        for dz in range(-3, 4):
            ring = abs(dx) == 4 or abs(dz) == 3
            b.put(CX+dx, 2, CZ+dz, 'dark_oak_planks' if ring else ('bamboo_planks' if ((dx >> 1)+dz) % 2 == 0 else 'bamboo_mosaic'))
    for (dx, dz) in ((-4, -3), (4, -3), (-4, 3), (4, 3), (0, -3), (0, 3), (-4, 0), (4, 0)):
        for y in range(3, 8): b.put(CX+dx, y, CZ+dz, 'dark_oak_log', axis='y')
    for dx in range(-4, 5):                                   # 梁
        for dz in (-3, 3): b.put(CX+dx, 8, CZ+dz, 'dark_oak_planks')
    for dz in range(-3, 4):
        for dx in (-4, 4): b.put(CX+dx, 8, CZ+dz, 'dark_oak_planks')
    for dx in range(-3, 4):                                   # 奥の壁（障子と板壁）
        if dx == 0: continue
        for y in range(3, 8):
            if y in (3, 7): b.put(CX+dx, y, CZ-3, 'dark_oak_planks')
            else: b.put(CX+dx, y, CZ-3, 'white_stained_glass_pane', **PANE_X)
    for dz in range(-2, 3):
        for dx in (-4, 4):
            if dz != 0: b.put(CX+dx, 3, CZ+dz, 'dark_oak_fence', **FN)
    for dx in range(-3, 4):
        if abs(dx) > 1 and dx != 0: b.put(CX+dx, 3, CZ+3, 'dark_oak_fence', **FN)
    tile_roof(b, CX, CZ, 8, 7, 6, fill_r=3)
    for dx in range(-3, 4):
        for dz in range(-2, 3): b.put_if_empty(CX+dx, 8, CZ+dz, 'spruce_planks' if (dx+dz) % 2 else 'dark_oak_planks')
    # 内装：囲炉裏と自在鉤の釜、座布団、床の間、書棚
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1): b.put(CX+dx, 2, CZ+dz, 'smooth_stone')
    b.put(CX, 2, CZ, 'campfire', facing='north', lit='true', signal_fire='false', waterlogged='false')
    for y in range(4, 8): b.put(CX, y, CZ, 'iron_chain', axis='y', waterlogged='false')
    b.put(CX, 3, CZ, 'cauldron')
    for (dx, dz) in ((-2, 0), (2, 0), (0, 2), (0, -2), (-2, 2), (2, 2)): b.put(CX+dx, 3, CZ+dz, 'red_carpet' if (dx+dz) % 4 == 0 else 'white_carpet')
    for dx in (-3, 3):
        for y in (3, 4): b.put(CX+dx, y, CZ-2, 'bookshelf')
    b.put(CX, 3, CZ-2, 'dark_oak_slab', **SL); b.put(CX, 4, CZ-2, 'decorated_pot'); b.put(CX-1, 3, CZ-2, 'potted_cherry_sapling')
    b.put(CX, 5, CZ-2, 'white_wall_banner', facing='south')
    for (dx, dz) in ((-3, -2), (3, -2), (-3, 2), (3, 2)): lantern_hang(b, CX+dx, 7, CZ+dz, 1)
    b.put(CX+3, 3, CZ+1, 'spruce_fence', **FN); b.put(CX+3, 4, CZ+1, 'spruce_pressure_plate', powered='false'); b.put(CX+2, 3, CZ+1, 'white_carpet')

# ------------------------------------------------------------------ 蔵（酒蔵：黒瓦の大屋根・ロフト・樽・米俵）
def storehouse(b, DX, DZ):
    hx, hz = 7, 4
    platform(b, DX-9, DZ-6, DX+9, DZ+6, 1)
    steps(b, DX-1, DX+1, DZ+7, 1)
    for dx in range(-hx, hx+1):
        for dz in range(-hz, hz+1):
            x, z = DX+dx, DZ+dz; edge = abs(dx) == hx or abs(dz) == hz
            b.put(x, 2, z, pick([('packed_mud', 45), ('mud_bricks', 20), ('coarse_dirt', 20), ('dark_oak_planks', 15)], x, 2, z) if not edge else 'dark_oak_planks')
            if not edge: continue
            post = abs(dx) == hx and abs(dz) == hz or dx % 4 == 0 and abs(dz) == hz or abs(dx) == hx and dz in (-hz, 0, hz)
            for y in range(3, 8):
                if post: b.put(x, y, z, 'dark_oak_log', axis='y')
                elif y == 5 and abs(dz) == hz and dx % 4 == 2: b.put(x, y, z, 'iron_bars')
                else: b.put(x, y, z, pick([('dark_oak_planks', 62), ('spruce_planks', 20), ('stripped_dark_oak_log', 10), ('mud_bricks', 8)], x, y, z) if y < 7 else 'dark_oak_planks')
    for dx in (-1, 0, 1):
        for y in range(3, 7): b.rm(DX+dx, y, DZ+hz)
    tile_roof(b, DX, DZ, 8, 10, 7, fill_r=3)
    # ロフト（東半分）とハシゴ
    for dx in range(2, hx):
        for dz in range(-hz+1, hz):
            if (dx, dz) != (3, -3): b.put(DX+dx, 6, DZ+dz, 'spruce_planks')
    for dz in range(-hz+1, hz): b.put(DX+2, 7, DZ+dz, 'dark_oak_fence', **FN)
    for y in range(3, 8): b.put(DX+3, y, DZ-3, 'ladder', facing='south', waterlogged='false')
    for dx in range(4, 7): b.put(DX+dx, 7, DZ-3, 'hay_block', axis='x'); b.put(DX+dx, 7, DZ+2, 'chest', facing='north', type='single', waterlogged='false')
    b.put(DX+6, 7, DZ, 'barrel', facing='up', open='false'); b.put(DX+6, 8, DZ, 'lantern', hanging='false', waterlogged='false')
    # 一階：酒樽の列・米俵・長持・道具
    for dx in range(-6, 0):
        b.put(DX+dx, 3, DZ-3, 'barrel', facing='up', open='false')
        if dx < -3: b.put(DX+dx, 4, DZ-3, 'barrel', facing='up', open='false')
        if dx < -5: b.put(DX+dx, 5, DZ-3, 'barrel', facing='up', open='false')
    b.put(DX-6, 6, DZ-3, 'lantern', hanging='false', waterlogged='false')
    for dx in range(-6, -3):
        for dz in (2, 3): b.put(DX+dx, 3, DZ+dz, 'hay_block', axis='y')
    for dx in range(-6, -4): b.put(DX+dx, 4, DZ+3, 'hay_block', axis='y')
    for dx in range(3, 7): b.put(DX+dx, 3, DZ+3, 'chest', facing='north', type='single', waterlogged='false') if dx % 2 else None
    b.put(DX-4, 3, DZ+3, 'grindstone', face='floor', facing='north'); b.put(DX-3, 3, DZ+3, 'composter'); b.put(DX-2, 3, DZ+3, 'loom', facing='north')
    b.put(DX-6, 3, DZ, 'cauldron'); b.put(DX-6, 3, DZ-1, 'decorated_pot')
    for (dx, dz) in ((4, 0), (6, 2), (5, -2)): lantern_hang(b, DX+dx, 5, DZ+dz, 1)
    for (dx, dz) in ((-4, 0), (-6, 1)): b.put(DX+dx, 3, DZ+dz, 'lantern', hanging='false', waterlogged='false') if False else None
    for s in (-5, 5): b.put(DX+s, 2, DZ+hz+2, 'barrel', facing='up', open='false')          # 軒先の樽
    toro(b, DX-8, 1, DZ+8); toro(b, DX+8, 1, DZ+8)

# ------------------------------------------------------------------ 小堂・祠（共通）
def small_hall(b, cx, cz, g, hx=2, hz=2, post='dark_oak_log', panel='white_concrete', roof_hr=2):
    for x in range(cx-hx-1, cx+hx+2):
        for z in range(cz-hz-1, cz+hz+2):
            b.put(x, g, z, pick(KIDAN, x, g, z))
            for y in range(g+1, g+12): b.rm(x, y, z)
    for dx in range(-hx, hx+1):
        for dz in range(-hz, hz+1):
            x, z = cx+dx, cz+dz; edge = abs(dx) == hx or abs(dz) == hz
            b.put(x, g+1, z, 'dark_oak_planks' if edge else 'spruce_planks')
            if not edge: continue
            corner = abs(dx) == hx and abs(dz) == hz
            pane = PANE_X if abs(dz) == hz else PANE_Z
            for y in range(g+2, g+5):
                if corner or dx == 0 and abs(dz) == hz and False: b.put(x, y, z, post, **({'axis': 'y'} if 'log' in post else {}))
                elif y == g+2: b.put(x, y, z, panel)
                elif y == g+3: b.put(x, y, z, 'white_stained_glass_pane', **pane)
                else: b.put(x, y, z, panel)
    b.rm(cx, g+2, cz+hz); b.rm(cx, g+3, cz+hz)
    b.put(cx, g+1, cz+hz+1, 'dark_oak_stairs', **ST('north'))
    tile_roof(b, cx, cz, g+5, hx+roof_hr, hz+roof_hr, fill_r=2, lant=True)
    for dx in range(-hx+1, hx): 
        for dz in range(-hz+1, hz): b.put_if_empty(cx+dx, g+5, cz+dz, 'dark_oak_planks')
    # 祭壇
    b.put(cx, g+2, cz-hz+1, 'stone_bricks'); b.put(cx, g+3, cz-hz+1, 'gold_block')
    for s in (-1, 1): b.put(cx+s, g+2, cz-hz+1, 'white_candle', candles='3', lit='true', waterlogged='false')
    for dz in range(0, hz): b.put(cx, g+2, cz+dz, 'red_carpet')
    lantern_hang(b, cx, g+4, cz, 1)

def temizuya(b, cx, cz):
    for sx in (-2, 2):
        for sz in (-2, 2):
            for y in range(1, 5): b.put(cx+sx, y, cz+sz, 'red_concrete')
    for dx in range(-2, 3):
        for dz in (-2, 2): b.put(cx+dx, 5, cz+dz, 'dark_oak_planks')
    for dz in range(-1, 2):
        for dx in (-2, 2): b.put(cx+dx, 5, cz+dz, 'dark_oak_planks')
    tile_roof(b, cx, cz, 5, 4, 4, fill_r=2, lant=False)
    for dx in (-1, 0, 1): b.put(cx+dx, 1, cz, 'stone_bricks'); b.put(cx+dx, 2, cz, 'cauldron') if dx == 0 else None
    b.put(cx-1, 2, cz, 'bamboo_slab', **SL); b.put(cx+1, 2, cz, 'bamboo_slab', **SL)
    lantern_hang(b, cx, 4, cz+1, 1)

def taiko_bridge(b, bx, bz):
    for d in range(-3, 4):
        for w in range(0, 3):
            x, z = bx+d, bz+w
            if abs(d) <= 1: b.put(x, 1, z, 'red_concrete')
            elif abs(d) == 2: b.put(x, 1, z, 'red_nether_brick_stairs', **ST('east' if d < 0 else 'west'))
            else: b.put(x, 0, z, 'stone_bricks')
    for d in range(-2, 3):
        for z in (bz, bz+2):
            b.put(bx+d, 2, z, 'dark_oak_fence', **FN) if abs(d) < 2 else b.put(bx+d, 2, z, 'red_concrete')
            if abs(d) == 2: b.put(bx+d, 3, z, 'lantern', hanging='false', waterlogged='false')
