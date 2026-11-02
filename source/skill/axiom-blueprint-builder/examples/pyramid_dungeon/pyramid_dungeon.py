"""砂漠に浮かぶ高台のピラミッド型ダンジョン「王の墓所」。axiom-blueprint-builder スキルの arch_helpers / dungeon_kit を使用。
外観：1:1の階段で滑らかに見える 4面ピラミッド（底辺69×69・高さ34）＋金の頂点＋入口の前庭と参道・オベリスク。
内部（3層）：
 L0 床y=0 : 玄室(安全) → 石柱の間(暗闇・棘の穴2本・スポナー2基) → 砂の迷宮(DFS迷路) → 螺旋階段(上り9段)
 L1 床y=9 : 溶岩の渡り（北の足場→飛び石→中央の島）。島の螺旋階段(上り8段)が王の間へ
 L2 床y=17: 王の間（ボス）＋ 鉄の扉とレバーで開く宝物庫
各関門は「危険地帯を越えてレバーに届く→鉄の扉が開く」。"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
from arch_helpers import *
from dungeon_kit import *
from ancient_helpers import *

b = Build()
B = 34                                   # ピラミッドの半幅(底)
half = lambda y: B+1-y                   # 高さ y(1..B) の半幅
R = 60                                   # 高台の半径（参道・塔門・巨大スフィンクス・オアシスの敷地）

# ================================================================ 1. 高台（砂漠の浮島）— 縁と底を「浮いている」ように作る
SANDS = [('sand', 70), ('sandstone', 22), ('smooth_sandstone', 8)]
RIMTOP = [('sandstone', 46), ('cut_sandstone', 24), ('smooth_sandstone', 14), ('red_sandstone', 10), ('terracotta', 6)]
DEEP = [('stone', 26), ('tuff', 30), ('andesite', 20), ('blackstone', 8), ('terracotta', 16)]
BOT = {}
def R_eff(x, z):                                          # 輪郭を揺らす（張り出し最大+12%、くびれ最大-4%）
    r = math.hypot(x, z) or 1.0
    n = noise(x/r*2.4+7, 1.0, z/r*2.4+3, 1.0)+0.4*noise(x/r*5.1, 2.0, z/r*5.1, 1.0)
    return R*(1+0.12*max(-0.33, min(1.0, n)))
def field(x, z):
    r = math.hypot(x, z)
    return 1-(r/R_eff(x, z))**2 + 0.04*noise(x, 0, z, 5.0) + 0.02*noise(x*2, 3, z*2, 3.0)
RIM_W = 0.17
for x in range(-R-10, R+11):
    for z in range(-R-10, R+11):
        v = field(x, z)
        if v <= 0: continue
        inside = max(abs(x), abs(z)) <= 40
        top = 0 if inside else max(0, int(round(2.6*noise(x, 9, z, 9.0)+0.8)))     # 外側は砂丘の起伏
        if not inside and v < RIM_W: top -= int(round(2.2*(1-v/RIM_W)**1.3))       # 縁はなだらかに下がる
        rho = math.sqrt(max(0.0, 1-v))                                              # ≒ 中心からの距離比
        spike = 3 if (h3(x, 0, z) % 11 == 0 and v < 0.5) else 0
        depth = max(2, int(4+36*(1-rho)**0.75+3*noise(x, 5, z, 3.4)+1.6*noise(x, 6, z, 1.5))+spike)   # 急な逆円錐＋縁の厚み4
        G[(x, z)] = top
        for y in range(-depth, top+1):
            k = top-y; bottom = y+depth
            if k == 0: nm = pick(SANDS if v >= 0.2 else RIMTOP, x, y, z)             # 縁は岩の帯が見える
            elif k <= 2 and bottom >= 2 and v >= 0.2: nm = pick([('sand', 60), ('sandstone', 40)], x, y, z)
            elif y < -15 and h3(x, y, z) % 3: nm = pick(DEEP, x, y, z)
            else: nm = band(x, y, z)                                                # 縞状の地層
            b.put(x, y, z, nm)
        if depth > 10:                                                              # 底の洞窟・えぐれ
            for y in range(-depth+3, -8):
                if noise(x*0.9, y*1.7, z*0.9, 4.5) > 0.55: b.rm(x, y, z)
        L = 0
        if v < 0.6 and h3(x, 9, z) % 9 == 0:                                        # 垂れ下がる岩のつらら
            L = 3+h3(z, x, 1) % 8
            for k in range(1, L+1): b.put(x, -depth-k, z, pick(DEEP, x, -depth-k, z) if k > 2 else band(x, -depth-k, z))
        BOT[(x, z)] = -depth-L
rngc = random.Random(8)
for _ in range(34):                                                                  # 底から垂れる大きな岩塊（中心寄りほど長い）
    cxn, czn = rngc.randint(-44, 44), rngc.randint(-44, 44)
    if (cxn, czn) not in G or field(cxn, czn) < 0.25: continue
    base = BOT[(cxn, czn)]; Lg = rngc.randint(7, 16)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (cxn+dx, czn+dz) not in BOT: continue
            Ld = Lg-3*(abs(dx)+abs(dz)); yb = BOT[(cxn+dx, czn+dz)]
            for kk in range(1, max(0, Ld)+1): b.put(cxn+dx, yb-kk, czn+dz, pick(DEEP, cxn, yb-kk, czn) if kk > 2 else band(cxn+dx, yb-kk, czn+dz))
            BOT[(cxn+dx, czn+dz)] = min(BOT[(cxn+dx, czn+dz)], yb-max(0, Ld))
for _ in range(45):                                                                  # 縁の岩だまり・転石
    ang = random.random()*math.tau; rr_ = R*random.uniform(0.9, 1.08)
    x, z = round(rr_*math.cos(ang)), round(rr_*math.sin(ang))
    if (x, z) in G and 0.04 < field(x, z) < 0.22 and max(abs(x), abs(z)) > 40:
        b.shell(x, G[(x, z)]+1, z, random.uniform(1.2, 2.4), random.uniform(1.0, 1.8), random.uniform(1.2, 2.4), lambda X, Y, Z: pick(RIMTOP, X, Y, Z), inner=0.0, lumpy=.4)

# ================================================================ 2. ピラミッド本体（階段で滑らかな45°）
FACE = [('sandstone_stairs', 55), ('smooth_sandstone_stairs', 45)]
BAND = 'red_sandstone_stairs'               # 8段ごとの赤い帯（正面からの見栄え）
for y in range(1, B+1):
    h = half(y)
    for x in range(-h, h+1):
        for z in range(-h, h+1):
            if max(abs(x), abs(z)) < h:
                b.put(x, y, z, 'sandstone'); continue
            nm = BAND if y % 8 == 0 else pick(FACE, x, y, z)
            if abs(x) == h and abs(z) == h: f, sh = corner_stair(x, z); b.put(x, y, z, nm, **ST(f, 'bottom', sh))
            elif abs(x) == h: b.put(x, y, z, nm, **ST('east' if x < 0 else 'west'))
            else: b.put(x, y, z, nm, **ST('south' if z < 0 else 'north'))
weather_faces(b, B)
b.put(0, B, 0, 'gold_block'); b.put(0, B+1, 0, 'gold_block'); b.put(0, B+2, 0, 'lightning_rod', facing='up', powered='false', waterlogged='false')
# 舗装の広場（y=0）
for x in range(-41, 42):
    for z in range(-41, 42):
        if (x, z) in G and field(x, z) > 0.12 and max(abs(x), abs(z)) <= 40: b.put(x, 0, z, 'smooth_sandstone' if (x//2+z//2) % 2 == 0 else 'cut_sandstone')

# ================================================================ 3. ダンジョン
SW = [('cut_sandstone', 46), ('sandstone', 22), ('smooth_sandstone', 22), ('chiseled_sandstone', 10)]
SC = [('cut_sandstone', 55), ('sandstone', 25), ('smooth_sandstone', 20)]
SF = [('smooth_sandstone', 50), ('cut_sandstone', 50)]
dg = Dungeon(b)
# ---- 掘る
dg.carve(-1, 1, 24, 1, 4, 36)                       # 入口の通路（外の前庭まで）
dg.open_end([(x, y, 37) for x in range(-1, 2) for y in range(1, 5)])
dg.carve(-7, 1, 14, 7, 5, 23)                       # E 玄室
dg.carve(-1, 1, 11, 1, 4, 13)                       # 玄室→石柱の間
dg.carve(-10, 1, -8, 10, 5, 10)                     # S1 石柱の間
dg.spike_pit(-10, 4, 10, 5, y_floor=0, depth=3, bridge_cells=[(-7, 4), (-7, 5)])
dg.spike_pit(-10, -2, 10, -1, y_floor=0, depth=3, bridge_cells=[(7, -2), (7, -1)])
dg.carve(-5, 1, -9, -5, 3, -9)                      # 扉1 の通路
M = dg.maze(-6, -22, 6, 6, 1, 5, entrance=('S', 0), exit_=('E', 5), seed=3, min_path=22)   # 砂の迷宮 13×13
dg.carve(7, 1, -11, 7, 3, -11)                      # 扉2 の先
dg.carve(8, 1, -11, 8, 5, -11)                      # 螺旋の入口セル
SA = dg.spiral(9, -11, 0, 9, entry=(8, -11), up=True, rot=-1, stair='sandstone_stairs', pillar='cut_sandstone', floor='cut_sandstone')
dg.carve(9, 10, -9, 9, 12, -9)                      # 螺旋の着地 → 溶岩の間（北の壁を抜く）
dg.carve(-12, 10, -8, 12, 14, 8)                    # L1 溶岩の間
for (x0, z0, x1, z1) in ((-12, -5, 12, 0), (-12, 1, -3, 5), (3, 1, 12, 5), (-12, 6, 12, 8)):   # 溶岩の湖（中央の島 x-2..2,z1..5 を残す）
    dg.lava_lake(x0, z0, x1, z1, y_surface=9, depth=2)
SB = dg.spiral(0, 3, 9, 8, entry=(0, 2), up=True, rot=-1, stair='sandstone_stairs', pillar='chiseled_sandstone', floor='cut_sandstone')
dg.carve(-7, 18, -7, 7, 25, 7)                      # L2 王の間
dg.carve(-4, 18, -11, 4, 21, -9)                    # 宝物庫
dg.carve(0, 18, -8, 0, 20, -8)                      # 宝物庫の扉
# ---- 内張り（密閉）
dg.line(wall=SW, ceil=SC, floor=SF)

# ---- 仕掛け・装飾
lan = dg.lantern
# 入口〜玄室（明るい安全地帯）
for z in (27, 31, 35): lan(0, 4, z)
for (x, z) in ((-5, 16), (5, 16), (-5, 21), (5, 21)): lan(x, 5, z)
for (x, z) in ((-3, 18), (3, 18)):
    for y in range(1, 6): b.put(x, y, z, 'chiseled_sandstone' if y in (1, 5) else 'cut_sandstone')
for x in (-6, 6): b.put(x, 1, 15, 'campfire', facing='south', lit='true', signal_fire='false', waterlogged='false')
b.put(-6, 1, 22, 'lodestone'); MARKER = (-6, 1, 22)
for x in range(-1, 2):
    for z in range(15, 24): b.put(x, 1, z, 'red_carpet') if z % 2 else None
for z in range(24, 36): b.put(0, 1, z, 'red_carpet') if z % 2 else None
b.put(-6, 1, 20, 'barrel', facing='up', open='false'); b.put(6, 1, 20, 'barrel', facing='up', open='false')
# S1 石柱の間（暗い。スポナー2基。宝箱2つは棘の穴を越えた奥）
for (x, z) in ((-9, 9), (9, 9), (-9, 6), (9, 6), (0, 7), (-3, -5), (3, -5)):
    for y in range(1, 6): b.put(x, y, z, 'cut_sandstone' if y not in (1, 5) else 'chiseled_sandstone')
for (x, z, mob) in ((-3, 2, 'husk'), (3, 2, 'skeleton')):
    for y in range(1, 6): b.put(x, y, z, 'cut_sandstone')
    b.put(x, 1, z, 'chiseled_sandstone'); dg.spawner(x, 3, z, mob)
for (x, y, z) in ((-10, 5, -8), (10, 5, -8), (-10, 5, 10), (10, 5, 10), (-4, 1, 8), (5, 1, -4)): b.put(x, y, z, 'cobweb')
dg.chest(-10, 1, -8, 'south', loot='easy', tag='S1a'); dg.chest(10, 1, -8, 'south', loot='easy', tag='S1b')
dg.door_levers(-5, 1, -9, 'south')
# 砂の迷宮（暗い。奥のセルに宝箱。ゴール=出口の扉の隣にレバー）
cx_, cz_ = M['cellxz'](2, 2); dg.chest(cx_, 1, cz_, 'north', loot='jungle', tag='MZ')
for (i, j) in ((4, 1), (1, 4)): x, z = M['cellxz'](i, j); b.put(x, 1, z, 'cobweb')
gx, gz = M['goal']; ex, ez = M['exit']
dg.door_levers(ex, 1, ez, 'east')
lan(7, 3, -11)
# L1 溶岩の間
for (x, z) in ((0, -4), (0, -2), (0, 0)): b.put(x, 9, z, 'polished_blackstone')                  # 飛び石（隙間1マス）
for (x, z) in ((3, -4), (-3, -3), (5, -1), (-5, -2), (2, 6), (-3, 7), (6, 4), (-6, 3)): b.put(x, 9, z, 'magma_block')   # おとり
for (x, z) in ((-8, -7), (0, -7), (8, -7), (-6, 2), (6, 2), (-2, 5), (2, 5)): lan(x, 14, z)
dg.chest(2, 10, 5, 'west', loot='gold', tag='L1')
# L2 王の間
for (x, z) in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
    for y in range(18, 26): b.put(x, y, z, 'chiseled_sandstone' if y in (18, 25) else 'cut_sandstone')
for x in range(-2, 3):
    for z in range(-5, 0): b.put(x, 18, z, 'cut_sandstone')
for x in (-1, 0, 1):
    for z in (-4, -3, -2): b.put(x, 19, z, 'gold_block')
b.put(0, 19, -3, 'lapis_block')
for (x, z) in ((-2, -5), (2, -5), (-2, -1), (2, -1)): b.put(x, 19, z, 'soul_campfire', facing='north', lit='true', signal_fire='false', waterlogged='false')
for (x, z) in ((-6, -6), (6, -6), (-6, 6), (6, 6), (0, -4), (-6, 0), (6, 0)): lan(x, 25, z, soul=True)
dg.door_levers(0, 18, -8, 'south')
for x, loot, tag in ((-3, 'rich', 'T1'), (0, 'end', 'T2'), (3, 'ancient', 'T3')): dg.chest(x, 18, -11, 'south', loot=loot, tag=tag)
for (x, z) in ((-4, -9), (4, -9)): b.put(x, 18, z, 'gold_block'); b.put(x, 19, z, 'soul_lantern', hanging='false', waterlogged='false')
b.put(-1, 18, -11, 'emerald_block'); b.put(1, 18, -11, 'diamond_block')
for x in range(-2, 3):                               # 螺旋の吹き抜けの縁に低い壁（落下防止。登り口側は空ける）
    for z in range(1, 6):
        if (x in (-2, 2) or z in (1, 5)) and (x, z) not in ((-2, 2), (-1, 1)): b.put(x, 18, z, 'sandstone_wall', **WALL)
BOSS = (0, 18, 0)

# ================================================================ 4. 外観：歴史・神話・幻想
near_dg = lambda x, y, z: any((x+i, y+j, z+k) in dg.D for i in (-3, 0, 3) for j in (-3, 0, 3) for k in (-3, 0, 3))
# 4-1 四面のレリーフ（階段の素材差し替え）：南=有翼の太陽、東西=ホルスの目、北=アンク。中央に金と青緑の「太陽の道」
paint_face(b, B, 'S', winged_sun(12), 7)
for sd in ('E', 'W'): paint_face(b, B, sd, eye_of_horus(), 8)
paint_face(b, B, 'N', ankh(), 8); paint_face(b, B, 'N', ankh()[:0] or ['G.G'], 22)
for sd, top in (('S', 18), ('E', 19), ('W', 19), ('N', 21)): paint_face(b, B, sd, ['GTG']*(B-1-top), top+1)
# 4-2 光の亀裂（東西の面に走る、封印の割れ目）
glow_vein(b, B, 'E', -9, 3, 26, seed=2, skip=near_dg); glow_vein(b, B, 'W', 9, 3, 26, seed=5, skip=near_dg)
# 4-3 砂に埋もれた麓（西と北）と、麓の折れた列柱・倒れた柱
sand_drift(b, B, 'W', peak=10, width=18, length=16, seed=1, center=-4); sand_drift(b, B, 'N', peak=8, width=16, length=14, seed=2, center=8)
rnd = random.Random(11)
for (x, z, h, br, fl) in ((-27, 41, 8, 3, ('x', 4)), (-21, 44, 8, 0, None), (27, 42, 8, 5, ('z', 3)), (22, 45, 8, 2, None), (-38, 20, 7, 4, ('x', 5)), (38, 17, 7, 6, None), (-39, -4, 7, 3, ('z', 4)), (39, -14, 7, 1, None), (-31, 36, 6, 6, None)):
    if (x, z) in G: ruined_column(b, x, z, h, br, fl)
# 4-4 参道：舗装・スフィンクス・列柱・魂の火・オベリスク
for z in range(37, 55):
    for x in range(-4, 5):
        if (x, z) in G and field(x, z) > 0.1: b.put(x, 0, z, 'gold_block' if abs(x) == 4 and z % 6 == 0 else ('cut_sandstone' if (x+z) % 2 == 0 else 'smooth_sandstone'))
for (x, z) in ((-4, 42), (4, 42), (-4, 47), (4, 47)): b.put(x, 1, z, 'soul_campfire', facing='south', lit='true', signal_fire='false', waterlogged='false')
sphinx(b, -7, 1, 39, 'S'); sphinx(b, 7, 1, 39, 'S')                                     # 参道の番人
sphinx(b, 34, 1, 44, 'W', 'great'); sphinx(b, -34, 1, 44, 'E', 'great')                 # 巨大スフィンクス（参道を向く）
for (mx_, mz_, mh) in ((-37, -33, 8), (-48, -22, 5), (38, -34, 7), (47, -22, 5)): mini_pyramid(b, mx_, mz_, mh)   # 衛星ピラミッド
for (x, z) in ((-11, 42), (11, 42), (-11, 47), (11, 47)): ruined_column(b, x, z, 9, 0)
obelisk(b, -13, 1, 38, 15); obelisk(b, 13, 1, 38, 15)
# 4-5 塔門（パイロン）：参道の入口
pylon(b, 5, 51, side=1); pylon(b, -5, 51, side=-1)
for x in range(-5, 6):
    for y in (13, 14): b.put(x, y, 52, 'cut_sandstone' if y == 13 else 'chiseled_sandstone')       # まぐさ
for x in (-1, 0, 1): b.put(x, 15, 52, 'gold_block')
b.put(0, 16, 52, 'shroomlight')
# 4-6 入口の通路の飾り（金のまぐさ・青い柱）
for x in range(-2, 3): b.put(x, 5, 36, 'gold_block'); b.put(x, 6, 36, 'chiseled_sandstone')
for y in range(1, 5): b.put(-2, y, 36, 'lapis_block' if y % 2 else 'gold_block'); b.put(2, y, 36, 'lapis_block' if y % 2 else 'gold_block')
# 4-6b 儀式の遺構：星の環状列石・永遠の炎の祭壇・崩れたアーチ
stone_circle(b, -31, -42, r=9, n=8, h=6)
for (ax_, az_, axis) in ((40, 6, 'z'), (-43, 10, 'z'), (22, -44, 'x'), (-12, 49, 'x'), (47, 22, 'z')): ruin_arch(b, ax_, az_, axis, 5, 7)
# 4-7 オアシスとヤシ
for (ox, oz) in ((46, 8), (-47, -16)):
    carve_water(b, pond_cells(ox, oz, 4.2, 3.4))
    for k in range(6):
        a = k*math.tau/6+0.3; px, pz = round(ox+6.2*math.cos(a)), round(oz+5.4*math.sin(a))
        if (px, pz) in G and b.get(px, G[(px, pz)], pz) in ('sand', 'sandstone'): palm(b, px, pz, rnd.randint(7, 10), seed=k)
for _ in range(300):                                 # サボテン・枯れ木
    x, z = rnd.randint(-58, 58), rnd.randint(-58, 58)
    if (x, z) not in G or max(abs(x), abs(z)) <= 41 or field(x, z) < 0.15: continue
    y = G[(x, z)]
    if b.get(x, y, z) != 'sand' or not b.empty(x, y+1, z): continue
    if rnd.random() < 0.4:
        for k in range(rnd.randint(1, 3)): b.put(x, y+1+k, z, 'cactus', age='0')
    else: b.put(x, y+1, z, 'dead_bush')
# 4-8 幻想：頂に浮かぶ太陽円盤・浮遊遺構・底に垂れる水晶
floating_sun_disc(b, 0, 49, 0, 5.4); floating_ruins(b, 0, 0, 42, 62, 14, 26, 8)
for (x, y, z) in ((0, B+3, 0),):
    for yy in range(B+3, 45): b.put(x, yy, z, 'end_rod', facing='up')
amethyst_underside(b, BOT, every=17)

# 4-9 周囲に浮かぶ小島（浮遊感）：遠くへ行くほど高低差をつけ、ヤシ・遺構・オベリスク・水晶を載せる
rnd2 = random.Random(21)
ISLETS = [(18, 86, -6, 9, 'palm'), (60, 90, 5, 5, 'column'), (104, 84, -13, 8, 'arch'), (148, 92, 2, 10, 'ruin'), (200, 88, -9, 6, 'palm'),
          (246, 84, 7, 4, 'column'), (292, 92, -4, 8, 'obelisk'), (338, 86, -15, 5, 'crystal')]
PLACED = []                                              # (x, z, 半径)：浮島・浮岩どうしが縦に重なって「柱」に見えないよう、水平距離で避ける
for k, (adeg, dist, cy, r_, deco) in enumerate(ISLETS):
    cxi = round(dist*math.cos(math.radians(adeg))); czi = round(dist*math.sin(math.radians(adeg))); PLACED.append((cxi, czi, r_))
    floating_islet(b, cxi, cy, czi, r_, seed=k)
    if deco == 'palm':
        for j in range(3): palm(b, cxi+rnd2.randint(-2, 2), czi+rnd2.randint(-2, 2), rnd2.randint(6, 8), seed=j) if (cxi, czi) in G else None
    elif deco == 'column': ruined_column(b, cxi, czi, 7, 2, ('x', 3), y0=cy+1)
    elif deco == 'arch': ruin_arch(b, cxi-2, czi, 'x', 4, 6)
    elif deco == 'obelisk': obelisk(b, cxi, cy+1, czi, 9)
    elif deco == 'ruin':
        for (ox, oz, hh) in ((-3, -3, 7), (3, -3, 5), (-3, 3, 6), (3, 3, 3)): ruined_column(b, cxi+ox, czi+oz, hh, 0, None, y0=cy+1)
        for ox in range(-3, 4): b.put(cxi+ox, cy+8, czi-3, 'cut_sandstone_slab', **SL) if ox % 3 else None
        b.put(cxi, cy+1, czi, 'soul_campfire', facing='north', lit='true', signal_fire='false', waterlogged='false')
    elif deco == 'crystal':
        for (ox, oz) in ((0, 0), (1, 0), (-1, 1), (0, -1)): b.put(cxi+ox, cy+1, czi+oz, 'amethyst_block'); b.put(cxi+ox, cy+2, czi+oz, 'amethyst_cluster', facing='up', waterlogged='false')
    for _ in range(3):                                   # 底から垂れる小さな岩のつらら
        px, pz = cxi+rnd2.randint(-r_//2, r_//2), czi+rnd2.randint(-r_//2, r_//2)
        yb = cy
        while b.get(px, yb-1, pz): yb -= 1
        for kk in range(rnd2.randint(2, 5)): b.put(px, yb-1-kk, pz, band(px, yb-1-kk, pz))
for _ in range(40):                                       # 浮かぶ小岩（さらに遠景）。既存の浮島・浮岩と水平に離す
    if len(PLACED) >= len(ISLETS)+14: break
    adeg = rnd2.uniform(0, 360); dist = rnd2.uniform(72, 106); cy = rnd2.randint(-22, 14); rk = rnd2.randint(2, 4)
    cxi = round(dist*math.cos(math.radians(adeg))); czi = round(dist*math.sin(math.radians(adeg)))
    if any(math.hypot(cxi-px, czi-pz) < pr+rk+6 for (px, pz, pr) in PLACED): continue
    PLACED.append((cxi, czi, rk)); floating_islet(b, cxi, cy, czi, rk, seed=rnd2.randint(0, 99), taper=1.5)

# 4-9b 雲：島の下・周囲に浮かぶ白い雲の塊（高度感）
for _ in range(16):
    adeg = rnd2.uniform(0, 360); dist = rnd2.uniform(20, 100); cyc = rnd2.randint(-70, -38)
    cxc = dist*math.cos(math.radians(adeg)); czc = dist*math.sin(math.radians(adeg))
    for (ox, oy, oz, rx, rz) in ((0, 0, 0, rnd2.uniform(6, 11), rnd2.uniform(5, 9)), (rnd2.uniform(-6, 6), 1, rnd2.uniform(-5, 5), rnd2.uniform(3, 6), rnd2.uniform(3, 5)), (rnd2.uniform(-7, 7), 0, rnd2.uniform(-6, 6), rnd2.uniform(3, 6), rnd2.uniform(3, 5))):
        b.shell(cxc+ox, cyc+oy, czc+oz, rx, 1.8, rz, lambda X, Y, Z: 'white_wool', inner=0.0, lumpy=.3)
# 4-10 支え：地表が下がった縁で、構造物の真下が空洞にならないよう埋める
for (x, z), tp in list(G.items()):
    if tp < 0 and (b.get(x, 1, z) or b.get(x, 0, z)):
        for y in range(tp+1, 1): b.put_if_empty(x, y, z, 'sandstone')

# ================================================================ 5. 検証
fix_connections(b)
leaks = dg.check_leaks(); door_bad = dg.check_doors(); print('扉・レバーチェック(空が合格):', door_bad); ret_bad = dg.check_return((0, 1, 18)); print('戻り検査(空が合格):', ret_bad); assert not ret_bad
r = dg.solve(start=(0, 1, 18))
reach = r['reached']
print('密閉チェック(0が合格):', leaks)
print('開いた扉', len(r['opened']), '/', r['doors'], ' 宝箱', r['chests_ok'], '/', r['chests'], '  迷路の解の長さ', M['path_len'], ' seed', M['seed'])
print('王の間(ボス位置)に到達:', BOSS in reach, '  宝物庫の中:', (0, 18, -10) in reach, '  溶岩の島:', (0, 10, 3) in reach or (1, 10, 3) in reach)
print('スポナー', [(x, y, z, m) for (x, y, z, m, kw) in dg.spawners])

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/pyramid_dungeon.bp'
    tags = ['pyramid', 'dungeon', 'desert', 'egypt', 'interior']
    b.BE = []; b.save(out, 'ピラミッドダンジョン「王の墓所」', author='nemo', tags=tags)
    if len(sys.argv) > 2:
        b.BE = dg.block_entities(); b.save(sys.argv[2], 'ピラミッドダンジョン「王の墓所」（宝箱・スポナー入り）', author='nemo', tags=tags+['nbt']); print('block entities:', len(b.BE))
    from PIL import Image, ImageDraw
    levels = [(1, (-14, 14), (-26, 38), 'L0 (floor y=0): 玄室→石柱の間→迷宮→螺旋'), (10, (-14, 14), (-14, 14), 'L1 (floor y=9): 溶岩の渡り→中央の島の螺旋'), (18, (-9, 9), (-13, 9), 'L2 (floor y=17): 王の間と宝物庫')]
    imgs = []
    for i, (ys_, xr, zr, t) in enumerate(levels):
        p = f'/tmp/pyr_map{i}.png'; dg.render_map(p, ys_, xr, zr, S=14, title=''); imgs.append(Image.open(p))
    W = sum(im.width for im in imgs)+20*(len(imgs)-1); H = max(im.height for im in imgs)
    sheet = Image.new('RGB', (W, H), (0, 0, 0)); x = 0
    for im in imgs: sheet.paste(im, (x, 0)); x += im.width+20
    sheet.save('/tmp/pyr_maps.png'); print('maps', sheet.size)
    xs = [k[0] for k in b.B]; ys = [k[1] for k in b.B]; zs = [k[2] for k in b.B]
    print('extent', min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
