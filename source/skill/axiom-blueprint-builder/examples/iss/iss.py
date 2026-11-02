"""ISS (国際宇宙ステーション) 1ブロック=1m。+z=進行方向(前)、+y=天頂、port=+x / starboard=-x。
主軸 y=0,x=0。トラス中心 z=37 (Destiny 中央) / y=6。"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from space_helpers import *
from interior_helpers import *
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out')      # 出力先ディレクトリ
os.makedirs(OUT, exist_ok=True)
b = Build(); b.BE = []

US = ('smooth_quartz', 'white_concrete', .35)          # (基調, 塊で混ぜる素材, 閾値)
RU = ('smooth_quartz', 'light_gray_concrete', .15)
GOLD = ('smooth_sandstone', 'smooth_quartz', .25)
PMA = ('light_gray_concrete', 'gray_concrete', .55)

def soyuz(cx, cz, y0, d):
    Y = lambda k: y0+d*k
    for k in range(7):
        m = 'iron_block' if k == 0 else 'smooth_quartz' if k < 5 else ('smooth_sandstone' if k == 5 else 'gray_concrete')
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if k in (1, 2, 6) and dx and dz: continue          # 軌道モジュール(球)・エンジンは角を落とす
                b.put(cx+dx, Y(k), cz+dz, m)
    for s_ in (-1, 1):
        for i in range(2, 6): b.box(cx+s_*i, Y(5), cz-1, cx+s_*i, Y(5), cz+1, 'blue_concrete')
        b.put(cx+s_*2, Y(5), cz, 'iron_block')

# ============================================================ 与圧モジュール（主軸 z）
b.box(-1, -1, 0, 1, 1, 2, 'light_gray_concrete'); b.box(-1, -1, 0, 1, 1, 0, 'iron_block')   # Zvezda 後方ドッキング部
tube(b, 'z', 0, 0, 3, 12, RU)          # Zvezda (13m: 後部3+本体10)
tube(b, 'z', 0, 0, 13, 25, GOLD)       # Zarya 12.6m
tube(b, 'z', 0, 0, 26, 27, PMA)        # PMA-1
tube(b, 'z', 0, 0, 28, 32, US)         # Unity 5.5m
tube(b, 'z', 0, 0, 33, 41, US)         # Destiny 8.5m
tube(b, 'z', 0, 0, 42, 48, US)         # Harmony 6.1m(中心合わせで7)
tube(b, 'z', 0, 0, 49, 50, PMA)        # PMA-2 + IDA-2
tube(b, 'x', 30, 0, -8, -3, US)        # Quest (starboard)
tube(b, 'z', 5, 0, 27, 33, US)         # Tranquility (port)
tube(b, 'z', 5, 0, 34, 40, US)         # Leonardo PMM (Tranquility 前方)
b.box(4, -1, 23, 6, 1, 26, 'smooth_sandstone'); b.box(4, -1, 23, 6, 1, 23, 'iron_block')   # BEAM (後方)
b.box(8, -1, 29, 11, 1, 31, 'smooth_quartz')                                              # Bishop airlock
tube(b, 'x', 45, 0, -9, -3, US)        # Columbus (starboard)
tube(b, 'x', 45, 0, 3, 13, US)         # Kibo PM (port) 11m
tube(b, 'y', 6, 45, 3, 6, US)          # Kibo ELM-PS (PM の天頂)
tube(b, 'y', 0, 45, 3, 4, PMA)         # Harmony 天頂 PMA-3/IDA-3
tube(b, 'y', 0, 10, -15, -3, RU)       # Nauka (Zvezda 天底、13m)
for x in (14, 19):                  # Kibo 曝露部 JEM-EF (格子の台)
    for z in range(43, 48):
        for y in range(-2, 3):
            if abs(z-45) == 2 or abs(y) == 2: b.put(x, y, z, 'iron_block')
for x in range(14, 20):
    for z in (43, 47):
        for y in (-2, 2): b.put(x, y, z, 'light_gray_concrete')
b.box(15, -1, 44, 16, 1, 46, 'gray_concrete'); b.box(17, 0, 44, 18, 1, 46, 'smooth_quartz')
# 小さな与圧モジュール(3x3固体): Poisk / Rassvet
b.box(-1, 3, 9, 1, 6, 11, 'light_gray_concrete'); b.box(-1, -8, 18, 1, -3, 20, 'light_gray_concrete')
# Prichal (Nauka 底の球状ノード)
for dx in range(-3, 4):
    for dy in range(-3, 4):
        for dz in range(-3, 4):
            r = (dx*dx+dy*dy+dz*dz) ** .5
            if 1.7 < r <= 2.6: b.put(dx, -19+dy, 10+dz, 'light_gray_concrete' if (dx+dy+dz) % 3 else 'iron_block')
# Cupola (Tranquility 天底)
for dx in (-1, 0, 1):
    for dz in (-1, 0, 1):
        if (dx, dz) != (0, 0): b.put(5+dx, -3, 30+dz, 'glass' if 0 in (dx, dz) else 'iron_block')
        b.put(5+dx, -4, 30+dz, 'glass' if (dx, dz) == (0, 0) else 'light_gray_concrete')

# ============================================================ 来訪機
b.box(-1, -1, -3, 1, 1, -1, 'smooth_quartz'); b.box(-1, -1, -5, 1, 1, -4, 'light_gray_concrete'); b.box(-1, -1, -7, 1, 1, -6, 'gray_concrete')
for s in (-1, 1):
    for i in range(2, 6): b.box(s*i, 0, -6, s*i, 0, -5, 'blue_concrete')          # Progress
soyuz(0, 10, 7, 1); soyuz(0, 19, -9, -1)                                            # Soyuz ×2 (Poisk / Rassvet)
b.box(-1, -1, 51, 1, 1, 51, 'gray_concrete'); b.box(-1, -1, 52, 1, 1, 52, 'black_concrete'); b.box(-1, -1, 53, 1, 1, 53, 'white_concrete')
tube(b, 'z', 0, 0, 54, 55, 'white_concrete', hollow=False, ring='white_concrete', seam=None)
tube(b, 'z', 0, 0, 56, 56, 'black_concrete', hollow=False, ring='black_concrete', seam=None)
tube(b, 'z', 0, 0, 57, 58, 'white_concrete', hollow=False, ring='white_concrete', seam=None)      # Crew Dragon
for z in (57, 58):
    for y in (-1, 0, 1): b.put(2, y, z, 'black_concrete'); b.put(-2, y, z, 'black_concrete')

# ============================================================ トラス・太陽電池翼・ラジエータ
CZ, CY = 37, 6
lattice_truss(b, -48, 48, CZ, CY)
for x in range(-5, 6):                                   # S0 の面板
    for dz in (-1, 0, 1):
        for dy in (-2, 2): b.put(x, CY+dy, CZ+dz, 'white_concrete')
for x in (-1, 1):
    for dz in (-2, 2): b.put(x, 3, CZ+dz, 'iron_block')  # S0 支柱(Destiny との接続)

def sarray(x0):
    solar_wing(b, x0, CY, 1, 73)
    b.box(x0+5, CY-1, 35, x0+6, CY+1, 39, 'iron_block')
for x0 in (26, 43, -37, -54): sarray(x0)

for s in (1, -1):                                        # 熱制御ラジエータ(P1/S1、後方へ23m)
    radiator_panel(b, range(s*8, s*19, s), (12, 34), CY, frame_x=(s*11, s*15))
    b.box(s*8, CY-1, 35, s*18, CY+1, 35, 'iron_block')

# Z1 トラス + Ku バンドアンテナ
for dx in (-2, 2):
    for dz in (-2, 2): b.box(dx, 3, 30+dz, dx, 7, 30+dz, 'iron_block')
for y in (3, 7): b.ring(-2, 28, 2, 32, y, 'light_gray_concrete')
b.box(-1, 4, 29, 1, 5, 31, 'gray_concrete'); b.box(0, 8, 30, 0, 9, 30, 'iron_block'); b.disk(0, 30, 2, 10, 'white_concrete')
# ELC / AMS
b.box(-27, 9, 35, -23, 12, 39, 'light_gray_concrete'); b.box(-26, 12, 36, -24, 12, 38, 'iron_block')   # AMS-02
for s in (1, -1): b.box(s*23, 1, 35, s*27, 3, 39, 'gray_concrete'); b.box(s*24, 2, 36, s*26, 2, 38, 'smooth_quartz')
b.box(23, 9, 35, 27, 11, 39, 'gray_concrete')
# Zvezda の太陽電池 (左右 13m)
for s in (1, -1):
    for x in range(3, 16):
        for z in range(5, 9): b.put(s*x, 0, z, 'raw_gold_block' if x in (3, 15) or z in (5, 8) else 'blue_concrete')

# Canadarm2 (MBS + 17m アームを L 字に)
b.box(-5, 5, 40, -3, 7, 42, 'iron_block'); b.box(-5, 8, 40, -4, 9, 41, 'gray_concrete')
b.box(-5, 10, 41, -5, 14, 41, 'light_gray_concrete'); b.box(-5, 15, 40, -4, 16, 41, 'iron_block')
b.box(-5, 15, 42, -5, 15, 46, 'light_gray_concrete'); b.box(-5, 15, 47, -4, 16, 48, 'iron_block'); b.box(-5, 15, 49, -5, 15, 49, 'black_concrete')


# ============================================================ 細部
def box_(*a): b.box(*a)
# Zvezda: 後部エンジン2基・通信アンテナ
for sx in (-1, 1):
    b.box(min(sx*3, sx*4), -1, 3, max(sx*3, sx*4), 0, 4, 'gray_concrete'); b.box(min(sx*3, sx*4), -1, 2, max(sx*3, sx*4), 0, 2, 'black_concrete')
for y in (3, 4): b.put(0, y, 6, 'iron_bars', **FN)
b.disk(0, 6, 1, 5, 'white_concrete')
# Zarya: 側面ラジエータ(白+金の枠)
for sx in (-1, 1):
    for z in range(14, 20): b.box(sx*3, -1, z, sx*3, 1, z, 'light_gray_concrete' if z in (14, 19) else 'white_concrete')
    for x in range(3, 13):
        for z in range(20, 23): b.put(sx*x, 0, z, 'raw_gold_block' if x in (3, 12) or z in (20, 22) else 'blue_concrete')
# Unity 天底カバー / PMA-2 の IDA 金リング
b.box(-1, -2, 29, 1, -2, 31, 'iron_block')
for du in range(-2, 3):
    for dv in range(-2, 3):
        if (abs(du) == 2) != (abs(dv) == 2) or (abs(du) == 2 and abs(dv) < 2): b.put(du, dv, 50, 'raw_gold_block')
# Kibo: ロボットアーム(JEM-RMS)と曝露部の実験装置
b.box(10, 3, 45, 11, 4, 46, 'iron_block'); b.box(12, 3, 45, 18, 3, 45, 'light_gray_concrete'); b.box(15, 3, 45, 16, 4, 46, 'iron_block'); b.put(19, 3, 45, 'black_concrete')
b.box(15, 3, 43, 16, 4, 44, 'gray_concrete'); b.box(17, 3, 47, 18, 4, 47, 'smooth_quartz'); b.box(14, -3, 44, 16, -3, 46, 'gray_concrete'); b.box(17, -3, 44, 18, -3, 45, 'smooth_quartz')
# Columbus: 外部実験プラットフォーム
b.box(-11, -1, 44, -10, 1, 46, 'gray_concrete'); b.box(-11, 2, 44, -10, 2, 46, 'smooth_quartz'); b.box(-12, 0, 45, -12, 0, 45, 'iron_block')
# Nauka: 欧州ロボットアーム ERA(11m)と関節
b.box(3, -14, 10, 3, -4, 10, 'light_gray_concrete')
for y in (-4, -9, -14): b.box(3, y, 9, 4, y, 11, 'iron_block')
# Prichal に Progress(天底向き)
for k in range(7):
    m = 'iron_block' if k == 0 else 'smooth_quartz' if k < 3 else ('light_gray_concrete' if k < 5 else 'gray_concrete')
    b.box(-1, -22-k, 9, 1, -22-k, 11, m)
for sx in (-1, 1):
    for i in range(2, 6): b.box(sx*i, -26, 9, sx*i, -26, 11, 'blue_concrete')
# Cygnus: Harmony 天底(与圧部+円形アレイ)
for du in range(-2, 3):
    for dv in range(-2, 3):
        if abs(du) + abs(dv) < 4: b.put(du, -3, 45+dv, 'iron_block')
b.box(-1, -7, 44, 1, -4, 46, 'smooth_quartz'); b.box(-1, -9, 44, 1, -8, 46, 'gray_concrete')
for sx in (-1, 1):
    b.put(sx*2, -8, 45, 'iron_block')
    for dy in range(-3, 4):
        for dz in range(-3, 4):
            if (dy*dy+dz*dz) ** .5 <= 2.7: b.put(sx*3, -8+dy, 45+dz, 'blue_concrete' if (dy*dy+dz*dz) ** .5 > .8 else 'iron_block')
# Dragon の尾翼
for z in (57, 58): b.put(0, 3, z, 'white_concrete'); b.put(0, -3, z, 'white_concrete')
# トラス: SARJ(回転関節)リング・アンモニアタンク・太陽電池翼の端灯
for sx in (-1, 1):
    for x in (21, 22):
        for dz in range(-4, 5):
            for dy in range(-4, 5):
                if 2.7 < (dz*dz+dy*dy) ** .5 <= 3.8: b.put(sx*x, CY+dy, CZ+dz, 'iron_block' if x == 21 else 'gray_concrete')
    b.box(sx*10, 1, 36, sx*12, 3, 38, 'gray_concrete'); b.box(sx*10, 3, 37, sx*12, 3, 37, 'iron_block')
for x0 in (26, 43, -37, -54):
    for z in (1, 73): b.put(x0+5, CY, z, 'sea_lantern'); b.put(x0+6, CY, z, 'sea_lantern')
# 内部: 実験ラック(通路は中央1列を確保)
tube_racks(b, 'z', 0, 0, 34, 40); tube_racks(b, 'z', 0, 0, 14, 24); tube_racks(b, 'x', 45, 0, -8, -5); tube_racks(b, 'x', 45, 0, 5, 12)


# ============================================================ 追加の作り込み(第2弾)
# Dextre (Canadarm2 先端): 胴 2x2x2 + 腕2本 + 工具箱
b.box(-5, 15, 50, -4, 16, 51, 'iron_block'); b.box(-5, 13, 50, -4, 14, 51, 'gray_concrete')
for xx in (-6, -3): b.box(xx, 12, 50, xx, 16, 50, 'light_gray_concrete'); b.put(xx, 11, 50, 'black_concrete')
# PVR (太陽電池翼付け根の光起電力ラジエータ、トラス後面から下へ垂れる白板)
for x0 in (26, 43, -37, -54):
    for x in range(x0+4, x0+8):
        for y in range(CY-13, CY-1): b.put(x, y, 34, 'light_gray_concrete' if (y-CY) % 3 == 0 else 'white_concrete')
# HTV-X (Unity 天底、8m×4.4m: 与圧部3 + サービス部2 + 非与圧貨物3)
tube(b, 'y', 0, 30, -5, -3, ('smooth_quartz', 'white_concrete', .4), hollow=False)
tube(b, 'y', 0, 30, -7, -6, 'gray_concrete', hollow=False, ring='gray_concrete', seam=None)
for a in (-8, -10):
    for du in range(-2, 3):
        for dv in range(-2, 3):
            if (abs(du) == 2) != (abs(dv) == 2) or (abs(du) == 2 and abs(dv) < 2): b.put(*PT('y', 0, 30, du, dv, a), 'light_gray_concrete')
for du, dv in ((2, 0), (-2, 0), (0, 2), (0, -2)): b.put(*PT('y', 0, 30, du, dv, -9), 'iron_block')
for sx in (-1, 1):
    for i in range(3, 8): b.box(sx*i, -6, 29, sx*i, -6, 31, 'blue_concrete')
    b.put(sx*2, -6, 30, 'iron_block')

# ============================================================ ゲーム内の本(書見台)と看板
AUTH = 'Claude'
BOOKS = [
 ('ISS 1/1m ガイド', ['ISS 国際宇宙ステーション\n1ブロック=1m\n\nトラス全幅 109m\n太陽電池翼 73×12m ×4組\n\n+z=進行方向(前)\n+x=左舷  -x=右舷\n+y=天頂',
   '歩けるルート\nZvezda→Zarya→Unity→Destiny(ここ)→Harmony\n\nUnity: 右Quest 左Tranquility\nHarmony: 右Columbus 左Kibo 上PMA-3',
   'Tranquility の床穴→Cupola(窓)\nTranquility前方→Leonardo\nZvezda 床穴→Nauka(ハシゴ)\n\nZvezda: 寝室(ベッド4)\nPoisk/Rassvet: 縦穴(ハシゴ)\nPrichal・来訪機は外観のみ',
   '外から見る所\nトラス:Destiny上\nラジエータ:後方23m\nCanadarm2+Dextre\nKibo腕と曝露部\nNaukaのERA\nDragon(前) Cygnus/HTV-X(下)\nProgress(後・Prichal)']),
 ('モジュール寸法表', ['実寸(m)→ブロック\nZvezda 13.1→13\nZarya 12.6→13\nUnity 5.49→5\nDestiny 8.53→9\nNode2 6.1→7\nQuest 5.5→6\nColumbus 6.87→7',
   'Kibo PM 11.2→11\nKibo EF 6→6\nELM-PS 3.9→4\nNauka 13.0→13\nCupola 1.5→2\nZ1 4.9→5\nS0 13.4→13\nCanadarm2 17.6→17',
   '直径4.1〜4.6m\n→5ブロック(殻1m・内部3×3)\n\n翼 1枚35m\n翼幅 73.2→73\n翼の幅 約11.6→12\n\nトラス 97m\n(+翼幅で109m)']),
 ('丸めと省略', ['丸めた点\n・直径は5ブロック\n・ノード(Unity/Harmony)は中心合わせで奇数長\n・太陽電池は厚み1ブロック\n・Soyuz/Dragon等は外観のみ',
   '想定・近似\n・来訪機は一例(同時接続は時期で変わる)\n・ラジエータは後方展開\n・PVRの向きは近似\n・HTV-X: 8m×4.4m Unity天底',
   '出典\nDLR "Data and modules"\nNASA / Wikipedia\nJAXA(HTV-X)\n\n作成: Claude']),
 ('ISS 豆知識', ['軌道\n高度 約400km\n傾斜 51.6度\n周期 約90分\n\n質量 約450t\n発電 110kW\n(DLR)',
   '規模(DLR)\n幅109m 長さ80m\n奥行88m 高さ45m\n居住・作業空間\n約1,200m3\n\nこのBPは\n109×81×45']),
]
LEC = [(-1, 36, 'east'), (1, 36, 'west'), (-1, 39, 'east'), (1, 39, 'west')]
BOOK_CMD = [lectern_with_book(b, lx, -1, lz, fc, title, pages, AUTH) for (title, pages), (lx, lz, fc) in zip(BOOKS, LEC)]
SIGNS = [((-1, 1, 7), 'east', ['Zvezda', '13.1m→13', '2000年', 'ロシア居住棟']), ((-1, 1, 19), 'east', ['Zarya (FGB)', '12.6m→13', '1998年', '最初の部品']),
         ((-1, 1, 35), 'east', ['Destiny', '8.53m→9', '2001年', '米国実験棟']), ((-6, 1, 29), 'south', ['Quest', '5.5m→6', '2001年', 'エアロック']),
         ((6, 1, 30), 'west', ['Tranquility', 'Node 3', '2010年', '下にCupola']), ((-1, 1, 43), 'east', ['Harmony', '6.1m→7', '2007年', 'Node 2']),
         ((-6, 1, 44), 'south', ['Columbus', '6.87m→7', '2008年', '欧州実験棟']), ((9, 1, 44), 'south', ['Kibo PM', '11.2m→11', '2008年', '日本実験棟'])]
for (sx_, sy_, sz_), fc, lines in SIGNS: wall_sign(b, sx_, sy_, sz_, fc, lines)
open(os.path.join(OUT, 'iss_books_commands.txt'), 'w', encoding='utf8').write(
    '# ISS 1/1m の本(Minecraft 26.3 の /give コマンド)。書見台に入らない場合はこちらで本を入手できます。\n' + '\n\n'.join(BOOK_CMD) + '\n')


# ============================================================ 作り込み(第3弾)
# Poisk / Rassvet を縦穴(ハシゴ)で歩けるように。Zvezda 天井・Zarya 床から出入り
b.clear(0, 3, 10, 0, 5, 10); b.clear(0, 2, 10, 0, 2, 10)
for y in range(2, 6): b.put(0, y, 10, 'ladder', facing='north', waterlogged='false')
b.put(1, 4, 10, 'sea_lantern')
b.clear(0, -7, 19, 0, -3, 19); b.clear(0, -2, 19, 0, -2, 19)
for y in range(-7, -1): b.put(0, y, 19, 'ladder', facing='north', waterlogged='false')
b.put(1, -5, 19, 'sea_lantern')
# EVA 手すり(Zvezda/Zarya 天面)
HR = dict(north='true', south='true', east='false', west='false', waterlogged='false')
for sx in (-1, 1):
    for z in list(range(4, 9))+list(range(14, 25)): b.put(sx, 3, z, 'iron_bars', **HR)
# Kibo 曝露部: 実験装置・アンテナ・エアロック台
b.box(14, 3, 46, 14, 3, 47, 'gray_concrete'); b.box(19, 3, 43, 19, 3, 44, 'iron_block'); b.box(15, -3, 43, 15, -3, 43, 'smooth_quartz')
b.disk(18, 45, 1, 5, 'white_concrete'); b.put(18, 4, 45, 'iron_bars', **FN)
b.box(20, -1, 44, 21, 1, 46, 'smooth_quartz'); b.box(20, 0, 45, 21, 0, 45, 'black_concrete')     # エアロック台の先端
# 外部ライト(投光器)
for p in [(1, 2, 4), (-1, 2, 4), (1, 2, 16), (-1, 2, 22), (1, 2, 43), (-1, 2, 47), (5, 9, 37), (-5, 9, 37), (-4, 8, 42), (0, 3, 51), (5, 3, 39)]:
    b.put(*p, 'sea_lantern')


# ============================================================ 内部の作り込み(第4弾)
for z0 in (4, 7):                                   # Zvezda 乗員居室(ベッド4台、通路は中央を確保)
    for sx in (-1, 1):
        b.put(sx, -1, z0, 'white_bed', facing='south', occupied='false', part='foot')
        b.put(sx, -1, z0+1, 'white_bed', facing='south', occupied='false', part='head')
tube_racks(b, 'z', 5, 0, 35, 39); tube_racks(b, 'x', 30, 0, -7, -4)   # Leonardo(補給品) / Quest(機器)
for z in range(13, 49):                             # 床の誘導ライン(Zarya→Harmony)
    if z not in (19, 26, 27) and b.get(0, -2, z) and b.get(0, -2, z) != 'glass': b.put(0, -2, z, 'gray_concrete')

# ============================================================ 開口(ハッチ)・内部照明・窓・ハシゴ
for z in (12, 13, 25, 26, 27, 28, 32, 33, 41, 42, 48, 49): b.clear(-1, -1, z, 1, 1, z)
for x in (-2, -3, 2, 3): b.clear(x, -1, 29, x, 1, 31) if abs(x) in (2, 3) and x in (-2, -3, 2, 3) else None
for z in (33, 34): b.clear(4, -1, z, 6, 1, z)
b.clear(4, -2, 29, 6, -2, 31)
for x in (-2, -3, 2, 3): b.clear(x, -1, 44, x, 1, 46)
for y in (2, 3): b.clear(-1, y, 44, 1, y, 46)
for y in (2, 3): b.clear(5, y, 44, 7, y, 46)
for y in (-2, -3): b.clear(-1, y, 9, 1, y, 11)
for (ax, cu, cv, a0, a1) in [('z', 0, 0, 3, 12), ('z', 0, 0, 13, 25), ('z', 0, 0, 28, 32), ('z', 0, 0, 33, 41), ('z', 0, 0, 42, 48),
                             ('x', 30, 0, -8, -3), ('z', 5, 0, 27, 33), ('z', 5, 0, 34, 40), ('x', 45, 0, -9, -3), ('x', 45, 0, 3, 13)]:
    tube_lights(b, ax, cu, cv, a0, a1)
for y in range(-14, 1): b.put(1, y, 10, 'ladder', facing='west', waterlogged='false')       # Nauka 昇降ハシゴ
for y in (-12, -8, -4): b.put(-1, y, 10, 'end_rod', facing='east')
for z in (5, 8): b.put(2, 0, z, 'glass'); b.put(-2, 0, z, 'glass')                            # Zvezda 窓
b.put(0, -2, 37, 'glass')                                                                      # Destiny 地球観測窓

# ============================================================ 検証: 内部の密閉と全モジュールの接続（b.B のワールド座標で検査）
ALLOWED = [((-1,-1,3),(1,1,12)),((-1,-1,13),(1,1,50)),((-8,-1,29),(-3,1,31)),((3,-1,27),(7,1,40)),((-9,-1,43),(-3,1,47)),((3,-1,43),(13,1,47)),((-1,3,43),(1,4,47)),((4,3,44),(8,6,46)),((-1,-15,9),(1,-3,11)),((-2,-1,28),(2,1,32)),((-3,-1,29),(3,1,31)),((-3,-1,44),(3,1,46)),((-1,2,44),(1,2,46)),((5,2,44),(7,2,46)),((-1,-3,9),(1,-2,11)),((4,-3,29),(6,-2,31)),((4,-1,33),(6,1,34)),((0,2,10),(0,5,10)),((0,-7,19),(0,-2,19))]   # 意図した内部空間＋ハッチで開けた殻の穴（外へ開く Cupola 空間も含む）
PROBES = dict(Zvezda=(0, 0, 5), Zarya=(0, 0, 20), Unity=(0, 0, 30), Quest=(-6, 0, 30), Tranquility=(5, 0, 30), Leonardo=(5, 0, 37),
              Harmony=(0, 0, 45), Columbus=(-6, 0, 45), Kibo=(10, 0, 45), ELM=(6, 4, 45), PMA3=(0, 3, 45), Nauka=(0, -14, 10),
              Cupola=(5, -3, 30), Poisk=(0, 4, 10), Rassvet=(0, -6, 19))
res = check_interior(b, (0, 0, 37), ALLOWED, PROBES)
print('内部: 密閉=%s セル数=%d 未到達=%s' % (res['sealed'], res['cells'], res['unreachable']))
if not res['sealed']: print('漏れ経路(外→内):', res['leak_path'])

b.save(os.path.join(OUT, 'ISS_1m.bp'), 'ISS 国際宇宙ステーション (1block=1m)', tags=['space', 'iss', 'scale-1m'])
for (lx, lz, fc) in LEC: b.put(lx, -1, lz, 'lectern', facing=fc, has_book='false', powered='false')
b.BE = []
b.save(os.path.join(OUT, 'ISS_1m_noBE.bp'), 'ISS 国際宇宙ステーション (1block=1m, BEなし)', tags=['space', 'iss', 'scale-1m'])
xs = [k[0] for k in b.B]; ys = [k[1] for k in b.B]; zs = [k[2] for k in b.B]
print('size x/y/z =', max(xs)-min(xs)+1, max(ys)-min(ys)+1, max(zs)-min(zs)+1)

