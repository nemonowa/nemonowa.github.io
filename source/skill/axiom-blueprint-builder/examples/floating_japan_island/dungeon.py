"""地底寺院「黄泉の回廊」— 主島の地下ダンジョン（ブロックだけで遊べる仕掛け付き）
入口：小堂の床の隠し蓋 → ハシゴ → 玄室(E)
1層(床y=-10): E → 石柱の間(S1:暗闇+棘の穴) → 迷宮(MZ) → 溶岩の渡り(S2) → 深淵の橋(S3) → 螺旋階段
2層(床y=-24): 回廊 → 黄泉の闘技場(ARENA) → 宝物庫 → ハシゴで迷宮へ戻る近道
各関門は「危険地帯を越えてレバーに届く → 鉄の扉が開く」。レバーは扉の隣接マスに置く（赤石配線なし）。"""
from lib import *

FY, CY = -9, -5                      # 1層の空間 y 範囲（床ブロックは y=-10、天井ブロックは y=-4）
DIRS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
WALL_T = [('stone_bricks', 56), ('mossy_stone_bricks', 20), ('cracked_stone_bricks', 10), ('deepslate_bricks', 14)]
CEIL_T = [('stone_bricks', 60), ('mossy_stone_bricks', 14), ('deepslate_tiles', 26)]
CHESTS, SPAWNERS, INFO = [], [], {}  # コマンド出力用


def facing_to(a, b_):
    dx, dz = b_[0]-a[0], b_[1]-a[1]
    return 'east' if dx > 0 else 'west' if dx < 0 else 'south' if dz > 0 else 'north'


def dungeon(b):
    D = set()

    def carve(x0, y0, z0, x1, y1, z1):
        for x in range(min(x0, x1), max(x0, x1)+1):
            for y in range(min(y0, y1), max(y0, y1)+1):
                for z in range(min(z0, z1), max(z0, z1)+1):
                    D.add((x, y, z)); b.rm(x, y, z)

    # ================================================================ 1. 掘る
    carve(-24, FY, -23, -18, CY, -19)                    # E 玄室
    carve(-20, -4, -19, -20, 3, -19)                     # 入口の縦穴（小堂の床まで）
    carve(-33, FY, -22, -25, CY, -20)                    # C1 回廊
    carve(-44, FY, -27, -34, CY, -15)                    # S1 石柱の間
    carve(-41, -13, -27, -40, -10, -15)                  # S1 棘の穴 1
    carve(-37, -13, -27, -36, -10, -15)                  # S1 棘の穴 2
    carve(-46, FY, -17, -45, FY+2, -17)                  # 扉1 の通路
    MX0, MZ0 = -57, -18
    carve(MX0, FY, MZ0, MX0+10, CY, MZ0+10)              # MZ 迷宮 11x11
    carve(-46, FY, -9, -46, FY+2, -9)                    # 扉2 の通路
    carve(-45, FY, -12, -31, CY, 0)                      # S2 溶岩の渡り
    carve(-42, -11, -12, -34, -10, 0)                    # 溶岩の湖
    carve(-30, FY, -3, -27, FY+2, -3)                    # 扉3 の通路 → S3
    carve(-26, FY, -8, -18, CY, -2)                      # S3 深淵の橋
    carve(-26, -17, -8, -18, -10, -2)                    # 深淵
    carve(-24, FY, -9, -24, FY+2, -9)                    # 扉4
    RING = [(-24, -10), (-23, -10), (-22, -10), (-22, -11), (-22, -12), (-22, -13), (-22, -14), (-23, -14),
            (-24, -14), (-25, -14), (-26, -14), (-26, -13), (-26, -12), (-26, -11), (-26, -10)]
    for k, (x, z) in enumerate(RING): carve(x, -10-k+1, z, x, -10-k+5, z)    # 螺旋階段
    carve(-29, -23, -11, -27, -19, -9)                   # 2層の回廊
    AX, AZ = -38, -12
    for x in range(AX-9, AX+10):                         # 闘技場（半径8.5）
        for z in range(AZ-9, AZ+10):
            if (x-AX)**2+(z-AZ)**2 <= 72.25: carve(x, -23, z, x, -16, z)
    carve(-47, -23, -12, -47, -21, -12)                  # 宝物庫の扉
    carve(-52, -23, -14, -48, -17, -10)                  # 宝物庫
    carve(-52, -16, -11, -52, -10, -11)                  # 宝物庫→迷宮のハシゴ穴

    # ================================================================ 2. 内張り（石レンガ）：天井・床・壁を1枚張って完全に密閉
    for (x, y, z) in list(D):
        for dx, dy, dz in DIRS:
            n = (x+dx, y+dy, z+dz)
            if n in D or n[1] >= 2: continue
            if dy == -1: nm = 'polished_andesite' if (x+z) % 2 == 0 else pick(WALL_T, *n)
            elif dy == 1: nm = pick(CEIL_T, *n)
            else: nm = pick(WALL_T, *n)
            b.put(*n, nm)

    # ---------------------------------------------------------------- 共通部品
    def lan(x, y, z, soul=False): b.put(x, y, z, 'soul_lantern' if soul else 'lantern', hanging='true', waterlogged='false')
    def chest(x, y, z, face, tag): b.put(x, y, z, 'chest', facing=face, type='single', waterlogged='false'); CHESTS.append((x, y, z, tag))
    def door(x, y, z, face): b.put(x, y, z, 'iron_door', **DOOR(face, 'lower')); b.put(x, y+1, z, 'iron_door', **DOOR(face, 'upper'))
    def lever(x, y, z, face='north'): b.put(x, y, z, 'lever', face='floor', facing=face, powered='false')
    def ladder(x, y0, y1, z, face):
        for y in range(y0, y1+1): b.put(x, y, z, 'ladder', facing=face, waterlogged='false')
    def pillar(x, z, y0, y1, mat='stone_bricks'):
        for y in range(y0, y1+1): b.put(x, y, z, mat)

    # ================================================================ 3. 玄室 E（安全地帯・灯り・目印）
    for x in range(-24, -17): b.put(x, FY, -21, 'red_carpet')
    for (x, z) in ((-23, -22), (-19, -22), (-23, -20), (-19, -20)): lan(x, CY, z)
    toro(b, -18, FY, -23); toro(b, -24, FY, -23)
    b.put(-21, FY, -23, 'lodestone'); INFO['marker'] = (-21, FY, -23)
    b.put(-23, FY, -19, 'barrel', facing='up', open='false'); b.put(-18, FY, -19, 'barrel', facing='up', open='false')
    ladder(-20, FY, 2, -19, 'north')                    # 縦穴のハシゴ（北向き＝南の壁に取り付く）
    b.rm(-20, 4, -19)                                   # 小堂の絨毯を除ける
    b.put(-20, 3, -19, 'dark_oak_trapdoor', facing='north', half='top', open='false', powered='false', waterlogged='false')   # 小堂の床と同じ高さの蓋
    for x in (-27, -30): lan(x, CY, -21)                # C1 の灯り

    # ================================================================ 4. S1 石柱の間（暗闇：自然にモンスターが湧く）
    for (x, z) in ((-39, -24), (-39, -18), (-43, -24), (-43, -21)): pillar(x, z, FY, CY-1)
    for (x, z) in ((-39, -21),): pillar(x, z, FY, CY-1, 'mossy_stone_bricks')
    for (x, z) in ((-39, -24), (-39, -18)): b.put(x, FY+1, z, 'spawner'); SPAWNERS.append((x, FY+1, z, 'zombie' if z < -20 else 'skeleton'))
    for tr in ((-41, -40), (-37, -36)):                  # 棘の穴：底に鍾乳石
        for x in tr:
            for z in range(-27, -14):
                if h3(x, 1, z) % 2 == 0: b.put(x, -13, z, 'pointed_dripstone', thickness='tip', vertical_direction='up', waterlogged='false')
    for x in (-41, -40): b.put(x, -10, -21, 'stone_bricks'); b.rm(x, -13, -21)           # 橋 1（入口の正面）
    for x in (-37, -36): b.put(x, -10, -17, 'cracked_stone_bricks'); b.rm(x, -13, -17)   # 橋 2（ずらして配置）
    for (x, y, z) in ((-44, FY, -27), (-34, FY, -27), (-44, FY, -15), (-34, FY, -15), (-44, CY, -27), (-34, CY, -15)): b.put(x, y, z, 'cobweb')
    chest(-35, FY, -27, 'south', 'S1a'); chest(-44, FY, -26, 'east', 'S1b')
    door(-45, FY, -17, 'east'); lever(-44, FY, -17, 'east')

    # ================================================================ 5. MZ 迷宮（暗闇・一本道の迷路）
    rnd = random.Random(11)
    walls = {(ox, oz) for ox in range(11) for oz in range(11) if ox % 2 == 0 or oz % 2 == 0}
    seen = {(4, 0)}; stack = [(4, 0)]
    while stack:
        i, j = stack[-1]
        nb = [(i+di, j+dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= i+di < 5 and 0 <= j+dj < 5 and (i+di, j+dj) not in seen]
        if not nb: stack.pop(); continue
        ni, nj = rnd.choice(nb); seen.add((ni, nj)); stack.append((ni, nj))
        walls.discard((i+ni+1, j+nj+1))                  # 2つのセルの間の壁を抜く（座標は 2i+1 と 2ni+1 の中点）
    walls.discard((10, 1)); walls.discard((10, 9))       # 入口・出口
    for (ox, oz) in walls:
        for y in range(FY, CY+1): b.put(MX0+ox, y, MZ0+oz, pick(WALL_T, MX0+ox, y, MZ0+oz))
    gx, gz = MX0+9, MZ0+9                                # 出口セル (-48,-9)
    door(-47, FY, -9, 'east'); lever(gx, FY, gz, 'east')
    chest(MX0+5, FY, MZ0+5, 'north', 'MZ')               # 迷路の中心セルの宝箱
    b.put(MX0+5, FY-1, MZ0+7, 'dark_oak_trapdoor', facing='north', half='top', open='false', powered='false', waterlogged='false')   # 宝物庫への近道（床と同じ高さの蓋）
    for (ox, oz) in ((9, 3), (3, 9)): b.put(MX0+ox, FY, MZ0+oz, 'cobweb')

    # ================================================================ 6. S2 溶岩の渡り
    for x in range(-42, -33):
        for z in range(-12, 1):
            for y in (-11, -10): b.put(x, y, z, 'lava', level='0')
    for (x, z) in ((-41, -6), (-39, -6), (-37, -6), (-37, -8), (-35, -8)): b.put(x, -10, z, 'polished_blackstone')          # 正解ルート（隙間1マスのジャンプ）
    for (x, z) in ((-40, -9), (-38, -3), (-36, -4), (-41, -2)): b.put(x, -10, z, 'magma_block')                          # おとり（マグマ）
    for x in (-40, -38, -36): b.put(x, CY, -6, 'iron_chain', axis='y', waterlogged='false'); b.put(x, CY-1, -6, 'iron_chain', axis='y', waterlogged='false'); b.put(x, CY-2, -6, 'lantern', hanging='true', waterlogged='false')
    for (x, z) in ((-44, -10), (-44, -2), (-32, -10), (-32, -2)): lan(x, CY, z)
    chest(-32, FY, -1, 'west', 'S2')
    door(-30, FY, -3, 'east'); lever(-31, FY, -3, 'east')

    # ================================================================ 7. S3 深淵の橋（落ちても水で助かる。ハシゴで戻れる）
    for x in range(-26, -17):
        for z in range(-8, -1):
            for y in (-17, -16, -15): b.put(x, y, z, 'water', level='0')
    for z in (-4, -3, -2): b.put(-26, -10, z, 'stone_bricks')                       # 入口の足場
    for x in (-25, -24): b.put(x, -10, -3, 'cracked_stone_bricks')                  # 橋（東へ）
    for z in range(-7, -3): b.put(-24, -10, z, 'cracked_stone_bricks')              # 橋（北へ）
    for x in (-25, -24, -23): b.put(x, -10, -8, 'stone_bricks')                     # 奥の足場
    ladder(-26, -17, FY, -5, 'east')
    for (x, z) in ((-24, -3), (-24, -6), (-20, -5), (-22, -8)): lan(x, CY, z)
    chest(-23, FY, -8, 'south', 'S3')
    door(-24, FY, -9, 'south'); lever(-24, FY, -8, 'south')

    # ================================================================ 8. 螺旋階段（1層 → 2層）
    for k, (x, z) in enumerate(RING):
        y = -10-k
        if k == 14: b.put(x, y, z, 'polished_andesite')
        else:
            prev = RING[k-1] if k else (x, z+1)
            b.put(x, y, z, 'stone_brick_stairs', **ST(facing_to((x, z), prev)))
        if k in (2, 6, 10, 13): lan(x, y+5, z, soul=(k == 10))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for y in range(-24, -9): b.put(-24+dx, y, -12+dz, 'chiseled_stone_bricks' if y % 4 == 0 else 'stone_bricks')   # 螺旋の芯

    # ================================================================ 9. 2層の回廊 → 闘技場
    for (x, z) in ((-28, -11), (-28, -9)): lan(x, -19, z, soul=True)
    # ---- 闘技場：黄泉の間
    for x in range(AX-9, AX+10):
        for z in range(AZ-9, AZ+10):
            r2 = (x-AX)**2+(z-AZ)**2
            if r2 > 72.25: continue
            b.put(x, -24, z, 'polished_blackstone_bricks' if (x+z) % 2 == 0 else 'deepslate_tiles')
            if r2 <= 6.25: b.put(x, -23, z, 'gilded_blackstone' if r2 <= 1 else 'polished_blackstone')
            if 49 <= r2 <= 56: b.put(x, -24, z, 'blackstone' if (x+z) % 3 else 'crying_obsidian')   # 外周の模様
    for k in range(8):                                   # 8本の柱
        a = k*math.pi/4; px, pz = round(AX+6*math.cos(a)), round(AZ+6*math.sin(a))
        pillar(px, pz, -23, -17, 'polished_blackstone_bricks'); b.put(px, -23, pz, 'chiseled_polished_blackstone'); b.put(px, -17, pz, 'chiseled_polished_blackstone')
        lan(px+(1 if px < AX else -1), -16, pz, soul=True)
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        b.put(AX+dx, -22, AZ+dz, 'soul_campfire', facing='north', lit='true', signal_fire='false', waterlogged='false')
    for dx in (-1, 0, 1):                                # 玉座（北）
        b.put(AX+dx, -23, AZ-7, 'obsidian'); 
        for y in (-22, -21, -20): b.put(AX+dx, y, AZ-8, 'crying_obsidian' if dx == 0 else 'obsidian')
    for dx in (-2, 2): b.put(AX+dx, -23, AZ-7, 'soul_lantern', hanging='false', waterlogged='false')
    for k in range(4):
        a = k*math.pi/2+math.pi/4; cx_, cz_ = round(AX+3.5*math.cos(a)), round(AZ+3.5*math.sin(a))
        for y in (-16, -17, -18): b.put(cx_, y, cz_, 'iron_chain', axis='y', waterlogged='false')
        b.put(cx_, -19, cz_, 'soul_lantern', hanging='true', waterlogged='false')
    INFO['boss'] = (AX, -23, AZ)
    door(-47, -23, -12, 'east'); lever(-46, -23, -12, 'east')       # 宝物庫の扉（闘技場の西の縁）

    # ---- 宝物庫
    for x in range(-52, -47):
        for z in range(-14, -9): b.put(x, -24, z, 'gold_block' if (x+z) % 4 == 0 else 'polished_blackstone_bricks')
    chest(-51, -23, -14, 'south', 'T1'); chest(-50, -23, -14, 'south', 'T2'); chest(-49, -23, -14, 'south', 'T3')
    for (x, z) in ((-48, -14), (-48, -10)): b.put(x, -23, z, 'gold_block'); b.put(x, -22, z, 'soul_lantern', hanging='false', waterlogged='false')
    for (x, z) in ((-50, -12), (-49, -12)): b.put(x, -23, z, 'gold_block')
    b.put(-50, -22, -12, 'emerald_block'); b.put(-51, -23, -10, 'diamond_block')
    ladder(-52, -23, -11, -11, 'east')
    lan(-50, -17, -12, soul=True); lan(-50, -17, -10, soul=True)

    # ================================================================ 10. 密閉チェック
    leaks = 0
    for (x, y, z) in D:
        for dx, dy, dz in DIRS:
            n = (x+dx, y+dy, z+dz)
            if n not in D and n[1] < 2 and b.empty(*n): leaks += 1
    INFO['cells'] = len(D); INFO['leaks'] = leaks
    return D
