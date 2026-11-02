"""五重塔（法隆寺風）。縮尺：1層=6ブロック、壁の半幅 7/6/6/5/5、軒の出=3、基壇半幅12、相輪15、全高≒51。
内装：1層=四方仏と心柱、2層=茶の間、3層=経蔵、4層=梵鐘、5層=金の祭壇（屋根裏まで吹き抜け）。"""
from lib import *

KIDAN = [('stone_bricks', 40), ('mossy_stone_bricks', 12), ('cobblestone', 14), ('andesite', 14), ('polished_andesite', 10), ('cracked_stone_bricks', 6), ('tuff_bricks', 4)]
WS = [7, 6, 6, 5, 5]          # 壁の半幅
HR = [10, 9, 9, 8, 8]         # 屋根の半幅（軒の出=3）
P = 6                         # 1層の高さ
FY = [2+P*i for i in range(5)]
K = 12                        # 基壇の半幅

def pagoda(b, PX, PZ):
    for x in range(PX-K, PX+K+1):                      # ---- 基壇
        for z in range(PZ-K, PZ+K+1):
            for y in range(-3, 2): b.put(x, y, z, pick(KIDAN, x, y, z))
            if max(abs(x-PX), abs(z-PZ)) == K: b.put(x, 1, z, 'polished_andesite')
            b.rm(x, 2, z)
    for x in range(PX-K, PX+K+1):
        for z in (PZ-K, PZ+K):
            if not (z == PZ+K and abs(x-PX) <= 4): b.put(x, 2, z, 'stone_brick_wall', **WALL)
    for z in range(PZ-K+1, PZ+K):
        for x in (PX-K, PX+K): b.put(x, 2, z, 'stone_brick_wall', **WALL)
    for x in range(PX-4, PX+5):
        b.put(x, 1, PZ+K+1, 'stone_brick_stairs', **ST('north')); b.put(x, 0, PZ+K+2, 'stone_brick_stairs', **ST('north'))
    for s in (-5, 5): b.put(PX+s, 1, PZ+K+1, 'stone_bricks'); b.put(PX+s, 0, PZ+K+2, 'stone_bricks')
    for (dx, dz) in ((-10, 10), (10, 10), (-10, -10), (10, -10)): toro(b, PX+dx, 2, PZ+dz)

    for i in range(5):
        W, fy, hr = WS[i], FY[i], HR[i]
        Wn = WS[i+1] if i < 4 else 0
        top = i == 4
        for dx in range(-W, W+1):                      # 床（畳）と天井
            for dz in range(-W, W+1):
                x, z = PX+dx, PZ+dz; edge = max(abs(dx), abs(dz)) == W
                b.put(x, fy, z, 'dark_oak_planks' if edge else ('bamboo_planks' if ((dx >> 1)+dz) % 2 == 0 else 'bamboo_mosaic'))
                if not top: b.put(x, fy+5, z, 'dark_oak_planks' if (edge or (dx+dz) % 2 == 0) else 'spruce_planks')
        for dx in range(-W, W+1):                      # 壁：柱・腰板・障子窓(fy+1..2・床まで)・長押
            for dz in range(-W, W+1):
                if max(abs(dx), abs(dz)) != W: continue
                x, z = PX+dx, PZ+dz
                post = (abs(dx) == W and abs(dz) == W) or dx == 0 or dz == 0 or (abs(dx) == W and abs(dz) % 4 == 0) or (abs(dz) == W and abs(dx) % 4 == 0)
                pane = PANE_X if abs(dz) == W else PANE_Z
                for y in range(fy+1, fy+5):
                    if post: b.put(x, y, z, 'dark_oak_log', axis='y')
                    elif y in (fy+3, fy+4): b.put(x, y, z, 'dark_oak_planks')
                    else: b.put(x, y, z, 'white_stained_glass_pane', **pane)
        if i == 0:                                     # 出入口（南面・1階のみ）
            for dx in (-1, 0, 1):
                for y in range(fy+1, fy+4): b.rm(PX+dx, y, PZ+W)
                b.put(PX+dx, fy, PZ+W+1, 'dark_oak_stairs', **ST('north'))
        rmax = hr-(Wn+1) if not top else 99           # 屋根：軒先だけ段を付け、内側は平らな帯で次層の壁際へ
        tile_roof(b, PX, PZ, fy+5, hr, hr, rmax=rmax, fill_r=3, hcap=1 if not top else 99)
        for dx in range(-W-1, W+2):                    # 軒下の斗栱
            for dz in range(-W-1, W+2):
                if max(abs(dx), abs(dz)) == W+1: b.put_if_empty(PX+dx, fy+5, PZ+dz, 'dark_oak_slab', **SLT)
        for sx in (-1, 1):                             # 隅の持ち送り
            for sz in (-1, 1):
                for k in (2, 3): b.put_if_empty(PX+sx*(W+k), fy+4, PZ+sz*(W+k), 'dark_oak_stairs', **ST('north' if sz > 0 else 'south', 'top'))

    for i in range(5):                                 # 心柱（3×3）
        fy = FY[i]
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                for y in range(fy, fy+P if i < 4 else fy+10): b.put(PX+dx, y, PZ+dz, 'stripped_dark_oak_log', axis='y')
    for i in range(4):                                 # 階段（偶数層：西壁沿い南上り／奇数層：東壁沿い北上り）
        fy = FY[i]; xs = min(WS[i], WS[i+1])-1
        xsg, zsg = (-1, 1) if i % 2 == 0 else (1, -1)
        x = PX+xsg*xs; face = 'south' if zsg == 1 else 'north'
        for j in range(P):
            z = PZ+zsg*(-3+j); y = fy+1+j
            b.rm(x, y+1, z); b.rm(x, y+2, z)
            b.put(x, y, z, 'spruce_stairs', **ST(face))
        b.put(x-xsg, fy+P+1, PZ+zsg*1, 'dark_oak_fence', **FN)

    # ---- 内装
    def L(dx, dz, y, n, **p): b.put(PX+dx, y, PZ+dz, n, **p)
    def lights(fy, pts):
        for (dx, dz) in pts: L(dx, dz, fy+4, 'iron_chain', axis='y', waterlogged='false'); L(dx, dz, fy+3, 'lantern', hanging='true', waterlogged='false')
    candle = dict(candles='3', lit='true', waterlogged='false')
    fy = FY[0]; n = WS[0]-1                            # 1層：四方仏・書棚・赤絨毯
    for (dx, dz, ax, az) in ((0, 2, 1, 0), (0, -2, 1, 0), (2, 0, 0, 1), (-2, 0, 0, 1)):
        L(dx, dz, fy+1, 'smooth_quartz'); L(dx, dz, fy+2, 'gold_block'); L(dx, dz, fy+3, 'gold_block')
        L(dx+ax, dz+az, fy+1, 'white_candle', **candle); L(dx-ax, dz-az, fy+1, 'white_candle', **candle)
    for dz in range(3, n+1): L(0, dz, fy+1, 'red_carpet')
    for dx in range(-n+2, n-1):
        for y in (fy+1, fy+2, fy+3): L(dx, -n, y, 'bookshelf')
    L(n, -3, fy+1, 'lectern', facing='west', has_book='false', powered='false'); L(n, -2, fy+1, 'barrel', facing='up', open='false')
    L(n, 3, fy+1, 'decorated_pot'); L(n, 4, fy+1, 'potted_cherry_sapling')
    for (dx, dz) in ((-3, 4), (-2, 4), (3, 3), (2, 3), (n-1, -4), (n-1, -5)): L(dx, dz, fy+1, 'red_carpet')
    lights(fy, [(-4, -4), (4, -4), (4, 4), (-4, 4), (0, 4), (0, -4)])
    fy = FY[1]; n = WS[1]-1                            # 2層：茶の間
    for dz in (-1, 0): L(-3, dz, fy+1, 'spruce_fence', **FN); L(-3, dz, fy+2, 'spruce_pressure_plate', powered='false')
    for (dx, dz) in ((-3, -2), (-3, 1), (-2, -1), (-2, 0), (-4, 0)): L(dx, dz, fy+1, 'red_carpet' if (dx+dz) % 2 else 'white_carpet')
    L(3, -3, fy+1, 'campfire', facing='north', lit='true', signal_fire='false', waterlogged='false')
    L(2, -3, fy+1, 'dark_oak_planks'); L(3, -2, fy+1, 'dark_oak_planks'); L(2, -2, fy+1, 'cauldron')
    for dx in (-1, 0, 1): L(dx, -n, fy+1, 'dark_oak_slab', **SL)
    L(0, -n, fy+2, 'decorated_pot'); L(1, -n, fy+2, 'potted_cherry_sapling'); L(-1, -n, fy+2, 'lantern', hanging='false', waterlogged='false')
    L(0, -n, fy+3, 'white_wall_banner', facing='south')
    L(-n, -3, fy+1, 'barrel', facing='up', open='false'); L(-n, -2, fy+1, 'cauldron')
    lights(fy, [(-3, 3), (3, 3), (3, -1), (-3, -3), (0, 3)])
    fy = FY[2]; n = WS[2]-1                            # 3層：経蔵
    for dx in range(-2, 3):
        for y in (fy+1, fy+2, fy+3): L(dx, -n, y, 'bookshelf')
    for dz in range(-3, 3):
        for y in (fy+1, fy+2): L(n, dz, y, 'bookshelf')
    for dx in (-3, 3): L(dx, n, fy+1, 'chiseled_bookshelf', facing='north')
    L(2, -2, fy+1, 'lectern', facing='south', has_book='true', powered='false')
    L(2, 3, fy+1, 'spruce_trapdoor', facing='north', half='bottom', open='false', powered='false', waterlogged='false'); L(2, 3, fy+2, 'white_candle', candles='2', lit='true', waterlogged='false')
    L(-n, -3, fy+1, 'barrel', facing='up', open='false'); L(-n, -2, fy+1, 'barrel', facing='up', open='false')
    lights(fy, [(-3, -3), (3, 3), (-3, 3), (3, -3)])
    fy = FY[3]; n = WS[3]-1                            # 4層：梵鐘と太鼓
    L(-2, -2, fy+4, 'iron_chain', axis='y', waterlogged='false'); L(-2, -2, fy+3, 'bell', attachment='ceiling', facing='north', powered='false')
    L(-3, -3, fy+1, 'barrel', facing='up', open='false'); L(-3, -3, fy+2, 'barrel', facing='up', open='false'); L(-2, -3, fy+1, 'barrel', facing='north', open='false')
    L(0, -3, fy+1, 'note_block'); L(1, -3, fy+1, 'jukebox')
    for dz in (1, 2, 3): L(-3, dz, fy+1, 'red_carpet')
    lights(fy, [(2, 2), (-2, 2), (2, -2)])
    fy = FY[4]                                         # 5層：金の祭壇
    for (dx, dz) in ((-2, -2), (2, 2), (-2, 2), (2, -2)):
        L(dx, dz, fy+1, 'gold_block'); L(dx, dz, fy+2, 'white_candle', candles='4', lit='true', waterlogged='false')
    for dx in (-1, 0, 1): L(dx, 2, fy+1, 'red_carpet')
    for y in (fy+2, fy+3): L(0, 0, y, 'gold_block')
    for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)): lantern_hang(b, PX+dx, fy+7, PZ+dz, 1)

    apex = FY[4]+5+8//2+1                              # 相輪（金の九輪・全長15）
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) == (0, 0): b.put(PX, apex+1, PZ, 'gold_block')
            else: b.put(PX+dx, apex+1, PZ+dz, 'stone_brick_slab', **SL)
    b.put(PX, apex+2, PZ, 'chiseled_stone_bricks')
    for k in range(3, 13): b.put(PX, apex+k, PZ, 'raw_gold_block')
    for n_, k in enumerate(range(4, 12, 2)):
        for dx, dz in (((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) if n_ < 3 else ((0, 0),)): b.put(PX+dx, apex+k, PZ+dz, 'gold_block')
    for k in range(13, 15): b.put(PX, apex+k, PZ, 'gold_block')
    b.put(PX, apex+15, PZ, 'end_rod', facing='up')
    return apex+15
