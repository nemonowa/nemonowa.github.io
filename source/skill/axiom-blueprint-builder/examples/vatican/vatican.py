"""バチカン：サン・ピエトロ大聖堂＋サン・ピエトロ広場（＋システィーナ礼拝堂・使徒宮殿の簡略形）。1ブロック=1m。
座標: +x=東（広場・テヴェレ川側）、+z=南、y=上。大聖堂の交差部（ドーム中心）を (0,0)、広場の歩行面を y=0、聖堂の床を y=F。
実寸（資料・近似）:
  ファサード 幅約115m・高さ約45m / 身廊 幅26m・高さ45m / ドーム内径約42m・床→十字架頂部 136.6m
  広場 楕円の最大幅240m・柱284本(4列) / オベリスク 約25m（台座と十字架込み約41m）/ システィーナ礼拝堂 40.9×13.4×20.7m
  python3 vatican.py OUT_DIR
"""
import sys, os, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from builder import *
import advanced_helpers as A
from interior_helpers import lectern_with_book, wall_sign

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
T0 = time.time()
b = Build(); b.BE = []
F = 4                                   # 聖堂の床（歩行面）
put = b.put
TRAV = lambda x, y, z: pick([('smooth_sandstone', 7), ('cut_sandstone', 2), ('sandstone', 1)], x, y, z)   # トラバーチン
PAVE = lambda x, y, z: pick([('tuff', 3), ('andesite', 2), ('cobbled_deepslate', 1)], x, y, z)          # サンピエトリーニ
LEAD, LEAD_ST, LEAD_SL = 'polished_andesite', 'polished_andesite_stairs', 'polished_andesite_slab'      # 鉛葺き

# ===================================================================== 1. 聖堂本体（解析的な立体 → 厚さ2の殻）
def outer(x, y, z):
    if y < -1: return False
    if y <= F + 45:
        if -45 <= x <= 45 and -45 <= z <= 45: return True                       # ミケランジェロのギリシア十字の本体
        if x < -45 and math.hypot(x + 45, z) <= 22.5: return True               # 西・北・南のアプス
        if z < -45 and math.hypot(x, z + 45) <= 22.5: return True
        if z > 45 and math.hypot(x, z - 45) <= 22.5: return True
        if 45 < x <= 123 and -40 <= z <= 40: return True                        # マデルノの身廊
    if 123 < x <= 138 and -57 <= z <= 57 and y <= F + 41: return True           # 前廊＋ファサード（アティックまで）
    return False

def vault(c, half, spring): return spring + math.sqrt(max(0.0, half * half - c * c))
PORTALS = [(0, 12), (-12, 10), (12, 10), (-22, 10), (22, 10)]                    # (z中心, 高さ)
def inner(x, y, z):
    if y < F: return False
    h = y - F
    if abs(z) <= 13 and -45 <= x <= 123 and y <= vault(z, 13.5, F + 30): return True          # 身廊＋西腕（半円筒ヴォールト）
    if abs(x) <= 13 and abs(z) <= 45 and y <= vault(x, 13.5, F + 30): return True             # 翼廊
    for cx, cz in ((-45, 0), (0, -45), (0, 45)):                                              # アプスの半ドーム
        d = math.hypot(x - cx, z - cz)
        if d <= 13.5 and ((cx and x < cx) or (cz < 0 and z < cz) or (cz > 0 and z > cz)) and y <= F + 30 + math.sqrt(max(0, 13.5**2 - d * d)): return True
    if math.hypot(x, z) <= 21 and y <= F + 47: return True                                    # 交差部（ドームへ抜ける）
    if 50 <= x <= 119 and 17 <= abs(z) <= 34 and h <= 20: return True                         # 側廊
    if 50 <= x <= 119 and 13 < abs(z) < 17 and (x - 50) % 12 >= 3 and A.arch_inside(((x - 50) % 12) - 7, h, 3.5, 13, 1.0): return True   # 身廊のアーケード
    if 126 <= x <= 135 and abs(z) <= 36 and h <= 17: return True                              # 前廊（ポルティコ）
    if 126 <= x <= 135 and abs(z) <= 30 and 20 <= h <= 27: return True                        # 祝福のロッジア
    if 124 <= x <= 125 and (abs(z) <= 3 and h <= 10 or abs(abs(z) - 22) <= 2 and h <= 8): return True   # 前廊→身廊・側廊の扉
    if 120 <= x <= 123 and abs(abs(z) - 22) <= 2 and h <= 8: return True
    if 136 <= x <= 138:                                                                        # ファサードの5つの入口
        for zc, hh in PORTALS:
            if A.arch_inside(z - zc, h, 2, hh - 3, 1.0) and h <= hh: return True
    return False

def solid(x, y, z): return outer(x, y, z) and not inner(x, y, z)
PROBES = [(d * s, 0, 0) for d in (1, 2) for s in (1, -1)] + [(0, d * s, 0) for d in (1, 2) for s in (1, -1)] + [(0, 0, d * s) for d in (1, 2) for s in (1, -1)]

FLOOR = lambda x, z: ('polished_granite' if (abs(z) <= 13 and math.hypot((x % 14) - 7, z) <= 2.6) else
                      'polished_andesite' if x % 7 == 0 or z % 7 == 0 else 'polished_diorite')
def ceiling(x, y, z): return 'gold_block' if (x % 5 == 0 or z % 5 == 0) and y > F + 24 else 'smooth_quartz'
n_body = 0
for x in range(-68, 139):
    for z in range(-68, 69):
        if not outer(x, 0, z): continue
        for y in range(-1, F + 46):
            if not solid(x, y, z): continue
            ext = intr = False
            for dx, dy, dz in PROBES:
                X, Y, Z = x + dx, y + dy, z + dz
                if inner(X, Y, Z): intr = True
                elif not outer(X, Y, Z): ext = True
            if not (ext or intr): continue                                    # 見えない芯は置かない
            if intr and y == F - 1 and inner(x, y + 1, z): m = FLOOR(x, z)
            elif intr and inner(x, y - 1, z): m = ceiling(x, y, z)
            elif ext: m = TRAV(x, y, z)
            else: m = 'smooth_quartz' if y < F + 3 or (x + z) % 9 else 'polished_diorite'
            put(x, y, z, m); n_body += 1
print('body', n_body, f'{time.time()-T0:.0f}s')

# ---- 外壁の付け柱・窓・コーニス（外周の一つ外側のセルを使う）
def ring_cells():
    out = []
    for x in range(-69, 140):
        for z in range(-69, 70):
            if outer(x, F + 20, z): continue
            for d, (dx, dz) in A._VEC.items():
                if outer(x + dx, F + 20, z + dz): out.append((x, z, d)); break   # d = 壁へ向かう向き
    return out
RING = ring_cells()
def wall_s(x, z, d):
    for cx, cz, ax in ((-45, 0, 'w'), (0, -45, 'n'), (0, 45, 's')):
        if (ax == 'w' and x < -45) or (ax == 'n' and z < -45) or (ax == 's' and z > 45):
            return int(round(math.atan2(z - cz, x - cx) * 22.5))
    return z if d in ('east', 'west') else x
for (x, z, d) in RING:
    if x >= 124: continue                                   # ファサードは別に作る
    s = wall_s(x, z, d) % 10; dx, dz = A._VEC[d]
    for y in range(-1, 2): put(x, y, z, 'stone_bricks')                                  # 基壇
    if s in (0, 1):                                                                      # 巨大な付け柱（コリント式）
        for y in range(2, F + 37): put(x, y, z, 'smooth_sandstone')
        for y in range(F + 37, F + 40): put(x, y, z, 'chiseled_sandstone' if y == F + 38 else 'cut_sandstone')
    put(x, F + 40, z, 'smooth_sandstone'); put(x, F + 41, z, 'smooth_sandstone_slab', type='bottom', waterlogged='false')   # コーニス
    if s in (4, 5):                                                                      # 2段の窓（1マス奥にガラス）
        for (y0, y1) in ((F + 7, F + 17), (F + 26, F + 33)):
            for y in range(y0, y1):
                if b.get(x + dx, y, z + dz):
                    b.rm(x + dx, y, z + dz)
                    if b.get(x + 2 * dx, y, z + 2 * dz): put(x + 2 * dx, y, z + 2 * dz, 'light_gray_stained_glass')
            put(x, y1, z, 'smooth_sandstone_slab', type='top', waterlogged='false')                # 窓の庇
# 屋上の手すり
for x in range(-68, 124):
    for z in range(-68, 69):
        if outer(x, F + 45, z) and not all(outer(x + dx, F + 45, z + dz) for dx, dz in A._VEC.values()):
            put(x, F + 46, z, 'sandstone_wall', **WALL)

# ---- 屋根（腕の切妻を高さ場で。勾配 0.5、鉛葺き）
def roof_h(x, z):
    h = 0.0
    if -60 <= x <= 123: h = max(h, 0.5 * max(0, 17.5 - abs(z)))
    if abs(z) <= 60: h = max(h, 0.5 * max(0, 17.5 - abs(x)))
    return F + 46 + h
cells = [(x, z) for x in range(-60, 124) for z in range(-60, 61)
         if (abs(z) <= 17 or abs(x) <= 17) and outer(x, F + 45, z) and math.hypot(x, z) > 25.5]
A.smooth_heightfield(b, cells, roof_h, LEAD, LEAD_ST, LEAD_SL, fill_down=1)

# ===================================================================== 2. ファサード（マデルノ）
FX = 138
for i, (x0, x1) in enumerate(((139, 143), (144, 147), (148, 151), (152, 155))):
    top = 3 - i
    for x in range(x0, x1 + 1):
        for z in range(-48, 49):
            for y in range(-1, top + 1): put(x, y, z, 'smooth_sandstone' if y == top else 'sandstone')
        if x == x1 and top >= 0:
            for z in range(-48, 49): put(x + 1, top, z, 'smooth_sandstone_stairs', facing='west', half='bottom', shape='straight', waterlogged='false') if x1 < 155 else None
COLS = [6.5, 17, 27, 37]                                       # 8本の巨大円柱（±）
PIL = [47, 56]                                                 # 4本の付け柱（±）
for zc in [s * c for c in COLS for s in (1, -1)]:
    for y in range(F, F + 27):
        for dx, dz in A.circle_cells(1.5, filled=True):
            m = 'cut_sandstone' if y in (F, F + 25, F + 26) else 'smooth_sandstone'
            if y == F + 25: m = 'chiseled_sandstone'
            put(140 + dx, y, int(round(zc)) + dz, m)
for zc in [s * c for c in PIL for s in (1, -1)]:
    for y in range(F, F + 27):
        for dz in (0, 1): put(139, y, zc + dz - (1 if zc > 0 else 0), 'chiseled_sandstone' if y == F + 25 else 'smooth_sandstone')
for x in range(138, 143):                                      # エンタブラチュア（突き出して影）
    for z in range(-57, 58):
        for y in range(F + 27, F + 31): put(x, y, z, 'smooth_sandstone' if y != F + 29 else 'cut_sandstone')
    for z in range(-57, 58): put(143, F + 30, z, 'smooth_sandstone_stairs', facing='west', half='top', shape='straight', waterlogged='false')
for z in range(-15, 16):                                       # 中央の三角破風
    top = F + 31 + int((15 - abs(z)) * 0.45)
    for x in range(139, 142):
        for y in range(F + 31, top + 1): put(x, y, z, 'smooth_sandstone')
    put(142, top, z, 'smooth_sandstone_slab', type='bottom', waterlogged='false')
for z in range(-57, 58):                                       # アティックの上のバルストレード
    put(138, F + 42, z, 'sandstone_wall', **WALL)
for zc, hh in PORTALS:                                         # 入口の上の窓（祝福のロッジア）と要石
    A.opening(b, FX, F + 19, zc, 'east', w=5, h=7, sharp=1.0, glass='glass_pane' if zc else None, frame='smooth_quartz', wall_t=2)
    put(FX + 1, F + hh + 1, zc, 'chiseled_sandstone')
for x in range(139, 142):                                      # 中央ロッジアのバルコニー
    for z in range(-4, 5): put(x, F + 18, z, 'smooth_sandstone_slab', type='top', waterlogged='false')
for z in range(-4, 5): put(141, F + 19, z, 'sandstone_wall', **WALL)
for zc in (-50, -42, -32, 32, 42, 50):                         # アティックの小窓
    for y in range(F + 33, F + 38): b.rm(FX, y, zc); put(FX - 1, y, zc, 'light_gray_stained_glass')
for s in (1, -1):                                              # 両端の時計（ヴァラディエ）
    zc = s * 52
    for (u, v) in A.circle_cells(3.6, filled=True):
        r = math.hypot(u, v)
        put(FX + 1, F + 36 + v, zc + u, 'gold_block' if r > 3.0 else 'white_concrete')
    for k in range(3): put(FX + 2, F + 36 + k, zc, 'black_concrete')
    for k in range(2): put(FX + 2, F + 36, zc + s * (k + 1), 'black_concrete')
STATUES = [0] + [s * v for v in (4.5, 9, 13.5, 18, 22.5, 27) for s in (1, -1)]   # キリスト・洗礼者ヨハネ・11使徒の13体
def statue(x, y, z, big=False):
    put(x, y, z, 'smooth_quartz')
    for k in range(1, 4 if big else 2): put(x, y + k, z, 'quartz_pillar', axis='y')
    put(x, y + (4 if big else 2), z, 'calcite')
for zc in STATUES: statue(138, F + 42, int(round(zc)), big=True)

# ===================================================================== 3. ドーム（ミケランジェロ／デッラ・ポルタ）と小ドーム
D0 = F + 46
for x in range(-30, 31):
    for z in range(-30, 31):
        d = math.hypot(x, z); th = math.degrees(math.atan2(z, x)) % 360
        k_ang = (th + 11.25) % 22.5 - 11.25                          # 最寄りの控え柱からの角度
        tang = d * math.sin(math.radians(k_ang))
        for y in range(D0, F + 68):                                  # ドラム（厚さ4）
            if 21.5 < d <= 25.5:
                win = abs(d * math.sin(math.radians((th % 22.5) - 11.25))) <= 1.5 and F + 52 <= y <= F + 61
                if win:
                    if d <= 22.7: put(x, y, z, 'light_gray_stained_glass')
                else: put(x, y, z, TRAV(x, y, z))
            elif 25.5 < d <= 29 and abs(tang) <= 2.0:                   # 16組の対の円柱（控え柱）
                put(x, y, z, 'quartz_pillar' if d > 28 and abs(tang) >= 0.8 else 'smooth_sandstone', **({'axis': 'y'} if d > 28 and abs(tang) >= 0.8 else {}))
        if 21.5 < d <= 29.5:                                          # 突出したコーニス
            put(x, F + 68, z, 'smooth_sandstone'); put(x, F + 69, z, 'smooth_sandstone_slab', type='bottom', waterlogged='false')
        if 21.5 < d <= 24.5:                                          # アティック
            for y in range(F + 69, F + 76):
                small_win = abs(d * math.sin(math.radians((th % 22.5) - 11.25))) <= 0.8 and F + 71 <= y <= F + 73
                put(x, y, z, 'gray_stained_glass' if small_win and d <= 22.5 else TRAV(x, y, z)) if not (small_win and d > 22.5) else None
# 外殻：尖頭気味の回転体（a=24.5、頂部 F+112）。高さ場で表面を階段/ハーフに、下は厚さ2で埋める
a_, base_ = 24.5, F + 76
R_ = ((F + 112 - base_) ** 2 + a_ ** 2) / (2 * a_)
prof = lambda d: base_ + math.sqrt(max(0, R_ ** 2 - (d + R_ - a_) ** 2)) if d <= a_ else base_
dome_cells = [(x, z) for x, z in A.circle_cells(24, filled=True)]
H = A.smooth_heightfield(b, dome_cells, lambda x, z: prof(math.hypot(x, z)), LEAD, LEAD_ST, LEAD_SL, fill_down=1)
for (x, z), n in H.items():
    d = math.hypot(x, z); top = n // 2 - 1
    lo = int(prof(d + 2.2)) - 1 if d + 2.2 <= a_ else base_
    for y in range(min(lo, top), top + 1):
        if b.empty(x, y, z): put(x, y, z, LEAD)
for (x, y, z), v in list(b.B.items()):                                # 16本のリブ（白い石）
    if y < base_ or math.hypot(x, z) > 25: continue
    th = math.degrees(math.atan2(z, x)) % 22.5
    if math.hypot(x, z) * math.sin(math.radians(min(th, 22.5 - th))) < 0.75 and v[0].startswith('minecraft:polished_andesite'):
        b.B[(x, y, z)] = (v[0].replace('polished_andesite', 'smooth_quartz'), v[1])
# 内殻（青と金のモザイク）と頂部の眼窓
for x in range(-21, 22):
    for z in range(-21, 22):
        d = math.hypot(x, z)
        if d > 21 or d < 4: continue
        yi = F + 72 + int(math.sqrt(max(0, 21 ** 2 - d * d)) * 1.15)
        th = math.degrees(math.atan2(z, x)) % 22.5
        rib = d * math.sin(math.radians(min(th, 22.5 - th))) < 0.6
        for y in (yi, yi + 1): put(x, y, z, 'gold_block' if rib or abs(d - 12) < .5 else 'light_blue_terracotta')
# ランタン
L0 = F + 112
for x in range(-7, 8):
    for z in range(-7, 8):
        d = math.hypot(x, z); th = math.degrees(math.atan2(z, x)) % 45
        for y in range(L0, L0 + 10):
            if 3.5 < d <= 4.5 and not (min(th, 45 - th) > 12 and L0 + 2 <= y <= L0 + 7): put(x, y, z, 'smooth_sandstone')
            if 5 < d <= 6 and min(th, 45 - th) < 6: put(x, y, z, 'quartz_pillar', axis='y')
        if d <= 6.5: put(x, L0 + 10, z, 'smooth_sandstone')
        if d <= 5.5 and d > 4.5: put(x, L0 - 1, z, 'smooth_sandstone')
A.dome_roof(b, 0, 0, L0 + 11, 5, rise=5, full=LEAD, stair=LEAD_ST, slab=LEAD_SL)
for y in range(L0 + 16, L0 + 18): put(0, y, 0, 'smooth_quartz')
b.sphere(0, L0 + 19, 0, 1.2, 'gold_block')
for y in range(L0 + 20, L0 + 25): put(0, y, 0, 'gold_block')       # 十字架（頂部 = 床から約136m）
for dz in (-1, 1, -2, 2): put(0, L0 + 23, dz, 'gold_block')
# 小ドーム4つ（ヴィニョーラ）
for cx, cz in ((28, 31), (28, -31), (-28, 31), (-28, -31)):
    for x, z in A.circle_cells(6):
        for y in range(F + 46, F + 54): put(cx + x, y, cz + z, TRAV(cx + x, y, cz + z) if (y - F) % 8 != 5 or (x + z) % 3 else 'gray_stained_glass')
    for x, z in A.circle_cells(6.8, filled=True): put(cx + x, F + 54, cz + z, 'smooth_sandstone')
    A.dome_roof(b, cx, cz, F + 55, 6, rise=7, full=LEAD, stair=LEAD_ST, slab=LEAD_SL)
    for y in range(F + 62, F + 66): put(cx, y, cz, 'smooth_sandstone' if y < F + 65 else 'gold_block')
    put(cx, F + 66, cz, 'gold_block'); put(cx, F + 67, cz, 'gold_block')
print('basilica done', len(b.B), f'{time.time()-T0:.0f}s')

# ===================================================================== 4. 内部：バルダッキーノ・司教座の栄光・照明
for (cx, cz) in ((-5, -5), (-5, 5), (5, -5), (5, 5)):              # ねじれ柱（ブロンズ＋金のらせん）
    for y in range(F, F + 19):
        for dx, dz in A.circle_cells(0.9, filled=True):
            ang = (math.degrees(math.atan2(dz, dx)) - y * 45) % 360
            put(cx + dx, y, cz + dz, 'gold_block' if (dx or dz) and ang < 50 else 'polished_blackstone')
for x in range(-6, 7):
    for z in range(-6, 7):
        put(x, F + 19, z, 'polished_blackstone')
        if max(abs(x), abs(z)) == 6:
            put(x, F + 20, z, 'gold_block'); put(x, F + 18, z, 'brown_wool' if (x + z) % 2 else 'gold_block')
for k in range(5):                                                  # 天蓋の上の渦巻き
    for s in (1, -1):
        put(s * (5 - k), F + 21 + k, 0, 'polished_blackstone'); put(0, F + 21 + k, s * (5 - k), 'polished_blackstone')
put(0, F + 26, 0, 'gold_block'); put(0, F + 27, 0, 'gold_block'); put(0, F + 28, 0, 'gold_block'); put(0, F + 27, 1, 'gold_block'); put(0, F + 27, -1, 'gold_block')
b.box(-1, F, -2, 1, F + 1, 2, 'smooth_quartz')                     # 教皇の祭壇
for (u, v) in A.circle_cells(6, filled=True):                        # 西アプスの「聖霊の窓」と金の光線
    r = math.hypot(u, v); y = F + 22 + v
    if r <= 4: put(-59, y, u, 'yellow_stained_glass'); put(-60, y, u, 'glowstone')
    elif r <= 6 and (int(math.degrees(math.atan2(v, u))) // 15) % 2 == 0: put(-58, y, u, 'gold_block')
b.box(-56, F, -2, -55, F + 6, 2, 'polished_blackstone'); b.box(-56, F + 7, -1, -55, F + 9, 1, 'gold_block')   # 聖ペトロの司教座
for x in range(-56, 120, 10):                                       # 見えない光源（湧き防止）
    for z in (-8, 0, 8):
        if inner(x, F + 6, z) and b.empty(x, F + 6, z): put(x, F + 6, z, 'light', level='15', waterlogged='false')
for x in range(55, 120, 10):
    for z in (-26, 26):
        if b.empty(x, F + 6, z): put(x, F + 6, z, 'light', level='15', waterlogged='false')
for z in (-40, -30, 30, 40):
    if b.empty(0, F + 6, z): put(0, F + 6, z, 'light', level='15', waterlogged='false')

# ===================================================================== 5. サン・ピエトロ広場（ベルニーニ）
XC, AX, BZ = 323, 80, 104                     # 楕円の中心と内側の半径（東西80・南北104 → 柱廊込みで約194×242）
def ell_o(x, z):
    lo, hi = -AX + 0.5, 60.0
    for _ in range(22):
        m = (lo + hi) / 2
        if ((x - XC) / (AX + m)) ** 2 + (z / (BZ + m)) ** 2 > 1: lo = m
        else: hi = m
    return (lo + hi) / 2
X_TRAP = XC - 69                              # 台形広場（ピアッツァ・レッタ）の東端
def trap_hw(x): return 52 + (X_TRAP - x) * (14 / (X_TRAP - 142))
# 舗装（暗い石＋トラバーチンの放射線・楕円の縁取り）
for x in range(142, XC + 100):
    for z in range(-125, 126):
        o = ell_o(x, z)
        in_trap = 156 <= x <= X_TRAP and abs(z) <= trap_hw(x)
        in_oval = o <= 17.5 and (o <= 0 or abs(z) / (BZ + o) >= 0.45)
        in_via = x >= XC and abs(z) <= 52 and x <= XC + 98
        if not (in_trap or in_oval or in_via): continue
        if x < 156 and abs(z) <= 48: continue                     # 正面の段
        r = math.hypot(x - XC, z); th = math.atan2(z, x - XC)
        if o <= 0:
            ray = r * abs(math.sin((th % (math.pi / 8)) - math.pi / 16)) > r * math.sin(math.pi / 16) - 0.6 and r > 9
            m = 'smooth_sandstone' if (ray or -2.5 < o <= -1) else PAVE(x, -1, z)
        elif in_trap: m = 'smooth_sandstone' if (x % 12 == 0 or round(z) % 12 == 0) else PAVE(x, -1, z)
        else: m = 'smooth_sandstone' if o <= 17.5 and abs(z) / (BZ + o) >= 0.45 else PAVE(x, -1, z)
        put(x, -1, z, m)
# 柱廊：4列×各腕36本（放射状にそろう）。t=30°〜150° と 210°〜330°
ROWS = [1.5, 5.5, 11.5, 15.5]
N = 36
col_top = []
for arm in (1, -1):
    for i in range(N):
        t = math.radians(30 + 120 * i / (N - 1))
        for o in ROWS:
            px, pz = XC + (AX + o) * math.cos(t), arm * (BZ + o) * math.sin(t)
            X, Z = int(round(px)), int(round(pz))
            for y in range(0, 13):
                for dx, dz in A.circle_cells(0.9, filled=True):
                    put(X + dx, y, Z + dz, 'cut_sandstone' if y in (0, 12) else 'smooth_sandstone')
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1): put(X + dx, 12, Z + dz, 'cut_sandstone')
            if o == ROWS[0] and i % 2 == 0: col_top.append((px, pz))
for x in range(XC - 100, XC + 100):                                 # エンタブラチュア・屋根・手すり
    for z in range(-125, 126):
        if abs(z) < 50: continue
        o = ell_o(x, z)
        if not (0 <= o <= 17.5 and abs(z) / (BZ + o) >= 0.48): continue
        for y in (13, 14, 15): put(x, y, z, 'cut_sandstone' if y == 14 else 'smooth_sandstone')
        put(x, 16, z, LEAD_SL, type='bottom', waterlogged='false')
        if o < 1 or o > 16.5: put(x, 16, z, 'sandstone_wall', **WALL)
        end = abs(abs(z) / (BZ + o) - 0.5) < 0.025                  # 腕の両端の妻壁（中央の通路はアーチ）
        if end:
            for y in range(0, 13):
                if not (6.5 <= o <= 10.5 and y <= 9): put(x, y, z, 'smooth_sandstone')
for (px, pz) in col_top:                                           # 柱廊の上の聖人像
    statue(int(round(px)), 17, int(round(pz)))
# 直線の回廊（コンスタンティヌスの翼 / カール大帝の翼）
for s in (1, -1):
    for x in range(142, X_TRAP + 2):
        zi = trap_hw(x) + 0.5
        for k in range(0, 10):
            z = s * int(round(zi + k))
            put(x, -1, z, PAVE(x, -1, z))
            if k in (0, 9):
                for y in range(0, 14): put(x, y, z, 'smooth_sandstone' if (k == 0 and x % 6 in (0, 1)) else TRAV(x, y, z))
                if k == 0 and x % 6 == 3:
                    for y in range(4, 10): put(x, y, z, 'light_gray_stained_glass')
            put(x, 14, z, 'smooth_sandstone')
            h = 15 + 0.5 * (4.5 - abs(k - 4.5))
            n2 = int(round(h * 2)); put(x, n2 // 2, z, LEAD_SL, type='bottom', waterlogged='false') if n2 % 2 else put(x, n2 // 2 - 1, z, LEAD)
    for x in range(142, 146):                                       # 聖堂側の連結部
        for z in range(57, 68):
            for y in range(-1, 14): put(x, y, s * z, TRAV(x, y, s * z))
# オベリスク（台座＋ライオン＋花崗岩の柱身＋十字架）
for y in range(0, 3):
    w = 4 - y
    b.box(XC - w, y, -w, XC + w, y, w, 'smooth_sandstone')
b.box(XC - 2, 3, -2, XC + 2, 7, 2, 'polished_granite')
for sx in (-2, 2):
    for sz in (-2, 2): put(XC + sx, 8, sz, 'polished_blackstone_stairs', facing='north', half='bottom', shape='straight', waterlogged='false')
for y in range(8, 32):
    w = 1 if y < 26 else 0
    b.box(XC - w, y, -w, XC + w, y, w, 'granite')
put(XC, 32, 0, 'granite'); put(XC, 33, 0, 'gold_block')
for y in range(34, 40): put(XC, y, 0, 'gold_block')
put(XC, 38, -1, 'gold_block'); put(XC, 38, 1, 'gold_block')
# 2つの噴水（マデルノ／ベルニーニ）と楕円の焦点の円盤
for s in (1, -1):
    fz = s * 74
    for (u, v) in A.circle_cells(8, filled=True):
        r = math.hypot(u, v)
        put(XC + u, -1, fz + v, 'smooth_sandstone')
        if r > 7.0: put(XC + u, 0, fz + v, 'smooth_sandstone')
        elif r > 1.5: put(XC + u, 0, fz + v, 'water', level='0')
    for y in range(0, 6): put(XC, y, fz, 'smooth_sandstone')
    for (u, v) in A.circle_cells(3, filled=True):
        put(XC + u, 6, fz + v, 'smooth_sandstone' if math.hypot(u, v) > 2.2 else 'smooth_sandstone_slab', **({} if math.hypot(u, v) > 2.2 else {'type': 'bottom', 'waterlogged': 'true'}))
    for y in range(7, 9): put(XC, y, fz, 'smooth_sandstone')
    for dx, dz in A._VEC.values(): put(XC + dx, 9, fz + dz, 'smooth_sandstone_slab', type='bottom', waterlogged='true')
    put(XC, 9, fz, 'smooth_sandstone')
    foc = s * int(round(math.sqrt(BZ ** 2 - AX ** 2)))
    for (u, v) in A.circle_cells(1.5, filled=True): put(XC + u, -1, foc + v, 'white_concrete')

# ===================================================================== 6. システィーナ礼拝堂・使徒宮殿（簡略）
SX0, SX1, SZ0, SZ1 = 64, 104, -101, -88                            # 40.9×13.4m、高さ20.7m
for x in range(SX0, SX1 + 1):
    for z in range(SZ0, SZ1 + 1):
        put(x, -1, z, 'polished_diorite' if (x + z) % 3 else 'red_terracotta')
        wall = x in (SX0, SX1) or z in (SZ0, SZ1)
        for y in range(0, 21):
            if wall: put(x, y, z, 'bricks' if y > 2 else 'stone_bricks')
        put(x, 21, z, 'bricks' if wall else 'light_blue_terracotta' if (x // 4 + z // 4) % 2 else 'yellow_terracotta')
        if wall and (x + z) % 2 == 0: put(x, 22, z, 'bricks')            # 銃眼状の頂部
        if not wall: put(x, 22, z, 'brick_slab', type='bottom', waterlogged='false')
for x in range(SX0 + 4, SX1 - 2, 6):                                # 6つずつの窓
    for z, n_ in ((SZ0, 'north'), (SZ1, 'south')):
        A.opening(b, x, 12, z, n_, w=2, h=6, sharp=1.0, glass='glass_pane')
for y in range(0, 3): b.rm(SX1, y, -95); b.rm(SX1, y, -94)          # 入口
# 使徒宮殿（中庭を囲む4翼。教皇の窓は広場側の最上階）
PX0, PX1, PZ0, PZ1, PH = 150, 232, -152, -82, 30
for x in range(PX0, PX1 + 1):
    for z in range(PZ0, PZ1 + 1):
        ring_d = min(x - PX0, PX1 - x, z - PZ0, PZ1 - z)
        if ring_d > 15: continue
        edge = ring_d in (0, 15)
        put(x, -1, z, 'stone_bricks')
        if edge:
            for y in range(0, PH):
                face = (x if z in (PZ0, PZ1) or ring_d == 15 and (z - PZ0 in (15,) or PZ1 - z == 15) else z)
                win = face % 4 == 1 and (y % 6) in (2, 3, 4) and y > 1
                put(x, y, z, 'gray_stained_glass' if win else ('stone_bricks' if y < 6 else 'smooth_sandstone'))
        put(x, PH, z, 'smooth_sandstone')
cells = [(x, z) for x in range(PX0, PX1 + 1) for z in range(PZ0, PZ1 + 1) if min(x - PX0, PX1 - x, z - PZ0, PZ1 - z) <= 15]
A.smooth_heightfield(b, cells, lambda x, z: PH + 1 + 0.5 * min(7.5, abs(min(x - PX0, PX1 - x, z - PZ0, PZ1 - z) - 7.5) * -1 + 7.5),
                     'bricks', 'brick_stairs', 'brick_slab', fill_down=1)
print('square/palace done', len(b.B), f'{time.time()-T0:.0f}s')

# ===================================================================== 7. 案内（前廊の書見台と看板）
BOOK = [('サン・ピエトロ大聖堂', [
    'サン・ピエトロ大聖堂\n（1ブロック=1m）\n\n世界最大級の教会堂。\n交差部の地下に\n使徒ペトロの墓が\nあると伝えられる。',
    '寸法（近似）\nファサード幅 約115m\nファサード高 約45m\n身廊 幅26m 高45m\nドーム内径 約42m\n床→十字架 136.6m',
    '設計の流れ\nブラマンテの計画→\nミケランジェロが\nギリシア十字と\nドームを設計→\nデッラ・ポルタが完成\n→マデルノが身廊と\nファサードを延長。',
    '広場（ベルニーニ）\n楕円の幅 約240m\n4列284本の柱\n中央にオベリスク\n2つの噴水\n楕円の焦点に立つと\n4列が1列に重なる。',
    'この模型の省略\n・内部の礼拝堂や\n　墓碑は省略\n・壁の厚みは2〜3m\n・寸法は資料の\n　近似値で丸めた\n・宮殿とシスティーナは\n　外形のみ簡略'])]
cmds = []
for (title, pages), (x, z) in zip(BOOK, [(130, 6)]):
    cmds.append(lectern_with_book(b, x, F, z, 'west', title, pages))
wall_sign(b, 134, F + 2, -35, 'south', ['SAN PIETRO', '1 block = 1 m', 'by nemo', ''])

# ===================================================================== 8. 検証（広場→正面の段→前廊→身廊→交差部 を歩けるか）
from collections import deque
PASS = ('light', 'water', 'lectern', 'sign', 'wall_sign')
def free(c):
    v = b.B.get(c); return v is None or any(p in v[0] for p in ('light',))
def stand(c):
    v = b.B.get((c[0], c[1] - 1, c[2])); return v is not None and 'water' not in v[0] and 'light' not in v[0]
def bfs(start, goals, box):
    seen = {start}; q = deque([start])
    while q:
        p = q.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in (0, 1, -1):
                n = (p[0] + dx, p[1] + dy, p[2] + dz)
                if n in seen or not (box[0] <= n[0] <= box[1] and box[2] <= n[2] <= box[3]): continue
                if free(n) and free((n[0], n[1] + 1, n[2])) and stand(n) and (dy <= 0 or free((p[0], p[1] + 2, p[2]))):
                    seen.add(n); q.append(n)
    return {k: (g in seen) for k, g in goals.items()}
res = bfs((200, 0, 0), {'前廊': (130, F, 0), '身廊': (90, F, 0), '交差部(祭壇前)': (4, F, -8), '西アプス': (-52, F, 0),
                        '北翼廊': (0, F, -55), '側廊': (90, F, 25), 'オベリスク脇': (XC + 6, 0, 0), 'ロッジアは未接続(上階)': (130, F + 20, 0)},
          (-70, 430, -130, 130))
print('到達:', res)

# ===================================================================== 9. 保存
tags = ['vatican', 'basilica', 'landmark', 'scale-1m', 'interior']
n = b.save(os.path.join(OUT, 'Vatican_StPeter_1m.bp'), 'バチカン：サン・ピエトロ大聖堂と広場 (1block=1m)', tags=tags, origin='bottom_center')
BE = b.BE; b.BE = []
b.put(130, F, 6, 'lectern', facing='west', has_book='false', powered='false')
b.save(os.path.join(OUT, 'Vatican_StPeter_1m_noBE.bp'), 'バチカン：サン・ピエトロ大聖堂と広場 (1block=1m, BEなし)', tags=tags, origin='bottom_center')
b.BE = BE
open(os.path.join(OUT, 'vatican_book_commands.txt'), 'w', encoding='utf8').write('# サン・ピエトロ大聖堂の本（26.3 /give）\n' + '\n'.join(cmds) + '\n')
from collections import Counter
xs = [k[0] for k in b.B]; ys = [k[1] for k in b.B]; zs = [k[2] for k in b.B]
print('size', max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1, 'top y', max(ys), f'{time.time()-T0:.0f}s')
for row in A.palette_stats(b, 10): print('  ', row)
