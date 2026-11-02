"""スペースシャトル オービタ 1ブロック=1m。+z=機首、-z=尾部、+x=左舷(port)、y=0 が胴体中心。胴体 y:-3..3(幅7)、貨物室ドア全開、ODS(ISS接続)付き。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
from space_helpers import *
from interior_helpers import *
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)
b = Build(); b.BE = []

WHITE = ('smooth_quartz', 'white_concrete', .35)
def wm(x, y, z): return WHITE[1] if noise(x, y, z, 3.2) > WHITE[2] else WHITE[0]
# ---- 胴体断面表 z:(半幅, 上端y, 下端y)  z=0 尾 … 36 機首
P = {}
for z in range(0, 27): P[z] = (3, 3, -3)
for z in range(27, 32): P[z] = (3, 4, -3)            # 操縦室の盛り上がり
P.update({32: (3, 3, -3), 33: (3, 3, -2), 34: (2, 2, -2), 35: (2, 1, -1), 36: (1, 0, -1)})
def inside(x, y, z):
    hw, yt, yb = P[z]; cy = (yt+yb)/2; ay = (yt-yb)/2+.5; ax = hw+.5
    return (abs(x)/ax)**4+(abs(y-cy)/ay)**4 <= 1.0
S = {(x, y, z) for z in P for x in range(-4, 5) for y in range(-5, 6) if inside(x, y, z)}
# ---- 操縦室の内部（z25..33）を侵食で抜く／貨物室(z6..23)は上が開いた溝
INT = {c for c in S if 25 <= c[2] <= 33 and all((c[0]+d[0], c[1]+d[1], c[2]+d[2]) in S for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)))}
BAY = {(x, y, z) for x in range(-2, 3) for y in range(-2, 4) for z in range(6, 24)}
for (x, y, z) in S:
    if (x, y, z) in INT or (x, y, z) in BAY: continue
    hw, yt, yb = P[z]
    if y <= yb or z >= 35: m = 'black_concrete'
    else: m = wm(x, y, z)
    b.put(x, y, z, m)
# 角の面取り階段（胴体の4隅）
for z in P:
    hw, yt, yb = P[z]
    if z in (6, 23) or 6 < z < 23: pass
    for sx in (-1, 1):
        for (yy, half, nm) in ((yt, 'bottom', 'smooth_quartz_stairs'), (yb, 'top', 'polished_blackstone_stairs')):
            if (sx*hw, yy, z) not in S and not (6 <= z <= 23 and yy == yt):
                b.put(sx*hw, yy, z, nm, **ST('west' if sx > 0 else 'east', half))
            elif 6 <= z <= 23 and yy == yt:
                b.put(sx*hw, yy, z, 'light_gray_concrete')            # 貨物室の縁（ヒンジ線）

# ---- 貨物室ドア（全開）：左右に外へ倒した放熱パネル
for s in (-1, 1):
    for x in range(4, 8):
        for z in range(6, 24):
            b.put(s*x, 3, z, 'light_gray_concrete' if z in (6, 23, 11, 15, 19) or x == 7 else 'white_concrete')
# ---- 翼（デルタ）：上面白・下面黒・前縁グレー
LE = {4: 24, 5: 17, 6: 15, 7: 14, 8: 13, 9: 12, 10: 11, 11: 10}; TE = {4: 1, 5: 1, 6: 2, 7: 2, 8: 3, 9: 3, 10: 4, 11: 5}
for s in (-1, 1):
    for x in range(4, 12):
        for z in range(TE[x], LE[x]+1):
            edge = z >= LE[x]-0
            b.put(s*x, -3, z, 'black_concrete'); b.put(s*x, -2, z, 'gray_concrete' if edge else ('light_gray_concrete' if z <= TE[x]+1 and x >= 5 else wm(s*x, -2, z)))
# ---- 垂直尾翼 / OMSポッド / SSME / ボディフラップ
for y in range(4, 15):
    zl = round(16-(y-4)*1.1); zt = round(2-(y-4)*0.2)
    for z in range(zt, zl+1):
        for x in ((-1, 0, 1) if y <= 7 else (0,)): b.put(x, y, z, 'light_gray_concrete' if z <= zt+1 else wm(x, y, z))
for s in (-1, 1):
    for x in (1, 2, 3):
        for z in range(0, 6): b.put(s*x, 4, z, wm(s*x, 4, z)); (b.put(s*x, 5, z, wm(s*x, 5, z)) if z <= 5 and x < 3 else None)
    for z in (-1, -2): b.put(s*2, 4, z, 'gray_concrete')
    b.put(s*3, 5, 1, 'black_concrete'); b.put(s*3, 5, 3, 'black_concrete')
for x in range(-3, 4): b.box(x, -4, 0, x, -4, 1, 'black_concrete')
def nozzle(cx, cy):
    for z, r, hollow in ((-1, 1.3, False), (-2, 1.7, True), (-3, 1.95, True)):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                d = (dx*dx+dy*dy) ** .5
                if d <= r and not (hollow and d < r-1.0): b.put(cx+dx, cy+dy, z, 'gray_concrete' if hollow else 'black_concrete')
for c in ((0, 1), (-2, -2), (2, -2)): nozzle(*c)

# ---- 操縦室の内装・窓・ハッチ
for x in range(-2, 3):
    for z in range(26, 34):
        if (x, 0, z) in INT and (x, z) != (2, 29): b.put(x, 0, z, 'light_gray_concrete')           # フライトデッキの床
for y in range(-2, 2): b.put(2, y, 29, 'ladder', facing='west', waterlogged='false')                # 上下のはしご
for sx in (-1, 1): b.put(sx, 1, 30, 'smooth_quartz_stairs', **ST('north', 'bottom'))                  # 操縦席
b.box(-2, 1, 32, 2, 1, 32, 'black_concrete'); b.box(-2, 2, 32, 2, 2, 32, 'gray_concrete')           # 計器盤
for x in (-1, 0, 1):
    for y in (3,):
        for z in (32, 33): b.put(x, y, z, 'glass')                                                    # 風防(上)
    for y in (1, 2): b.put(x, y, 34, 'glass')                                                         # 風防(前)
for sx in (-1, 1): b.put(sx, 4, 29, 'glass'); b.put(sx*3, 1, 30, 'glass'); [b.put(sx, y, 24, 'glass') for y in (1, 2)]  # 天窓・側窓・貨物室を覗く後窓
for z in (30, 31): b.box(2, -2, z, 2, -1, z, 'iron_block')                                            # ロッカー
b.put(3, -2, 27, 'birch_door', facing='east', half='lower', hinge='left', open='false', powered='false')   # 左舷ハッチ
b.put(3, -1, 27, 'birch_door', facing='east', half='upper', hinge='left', open='false', powered='false')
b.box(4, -3, 26, 6, -3, 28, 'light_gray_concrete')                                                    # 乗降ステップ
# ---- ODS（軌道船ドッキング装置）：貨物室前方の縦円筒。天頂の ISS 接続リングへ
tube(b, 'y', 0, 21, -3, 4, ('smooth_quartz', 'light_gray_concrete', .3))
for sx in (-2, 2):
    for sz in (19, 23):
        for y in range(-3, 5): b.put(sx, y, sz, 'smooth_quartz')       # 軸yの円筒は角が空くので、ここでは四角に埋める
for x in range(-2, 3):
    for z in range(19, 24): b.put(x, -3, z, 'black_concrete')
b.ring(-1, 20, 1, 22, 5, 'iron_block'); b.put(0, 5, 21, 'iron_bars', **FN)
for y in range(-2, 4): b.put(1, y, 21, 'ladder', facing='west', waterlogged='false')
# ---- ロボットアーム Canadarm（15m）：左舷縁から立ち上げた姿勢
b.box(3, 4, 17, 4, 5, 18, 'iron_block'); b.box(3, 6, 17, 3, 11, 17, 'light_gray_concrete'); b.box(3, 12, 17, 4, 13, 18, 'iron_block')
b.box(5, 12, 17, 7, 12, 17, 'light_gray_concrete'); b.box(8, 12, 17, 9, 13, 18, 'iron_block'); b.put(10, 12, 17, 'black_concrete')
# ---- 照明
for p in [(0, 3, 28), (0, 3, 30)]: b.put(*p, 'end_rod', facing='down')
for p in [(0, -1, 27), (0, -1, 31)]: b.put(*p, 'end_rod', facing='down')
b.put(0, 3, 21, 'end_rod', facing='down')
for p in [(3, 1, 7), (-3, 1, 7), (3, 1, 16), (-3, 1, 16), (0, 4, 35)]: b.put(*p, 'sea_lantern')
# ---- ハッチ（操縦室⇔ODS）
for z in (23, 24): b.clear(-1, -2, z, 1, -1, z)

# ---- 本と看板
BOOKS = [
 ('シャトル 1/1m ガイド', ['スペースシャトル\\nオービタ(Discovery型)\\n1ブロック=1m\\n\\n全長 37.24m→37\\n翼幅 23.79m→23\\n全高 約17.9m→18\\n機体幅 6.9m→7\\n\\n+z=機首 +x=左舷',
   '歩けるルート\\n入口: 左舷のドア\\nミッドデッキ→はしご→フライトデッキ\\n奥のハッチ→ODS(ISS接続)→はしごで上へ\\n貨物室は開放(宇宙空間)',
   '外から見る所\\n貨物室ドア全開\\nカナダアーム(15m)\\nOMSポッド・垂直尾翼\\nSSME×3(正三角形)\\n白=上面 黒=耐熱タイル\\n灰=翼前縁']),
 ('寸法表', ['実寸(m)→ブロック\\n全長 37.24→37\\n翼幅 23.79→23\\n機体幅 6.9→7\\n全高 17.86→18\\n貨物室 18.38×4.57\\n→内寸 18×5\\nアーム 約15→15']),
 ('丸めと省略', ['丸めた点\\n・貨物室内寸を5ブロックにし、殻1で外幅7\\n・翼は厚み2ブロック\\n・降着装置・タイルは省略\\n・主翼の形は近似\\n・アームは立ち上げた姿勢\\n・ODSは簡略化']),
 ('シャトル豆知識', ['初飛行 1981年4月\\n(Columbia STS-1)\\n最終飛行 2011年7月\\n(Atlantis STS-135)\\n\\n通常の乗員 5〜7名\\n貨物室ドア1枚に放熱パネル4枚\\n(NASA/ESA/Wikipedia)'])]
for bk in BOOKS: bk[1][:] = [p.replace('\\\\n', '\n') for p in bk[1]]
LEC = [(-2, -2, 25), (-2, -2, 27), (-2, -2, 29), (-2, -2, 31)]
CMD = [lectern_with_book(b, x, y, z, 'east', t, pg) for (t, pg), (x, y, z) in zip(BOOKS, LEC)]
wall_sign(b, -2, -1, 26, 'east', ['MIDDECK', 'ミッドデッキ', '入口は左舷ドア', ''])
wall_sign(b, -2, 1, 28, 'east', ['FLIGHT DECK', 'フライトデッキ', '操縦席×2', ''])
wall_sign(b, -1, 0, 20, 'south', ['ODS', 'ISS接続装置', 'はしごで上へ', ''])
open(os.path.join(OUT, 'shuttle_books_commands.txt'), 'w', encoding='utf8').write('# スペースシャトル 1/1m の本(26.3 /give)\n' + '\n\n'.join(CMD) + '\n')

# ---- 検証
mn = [min(k[i] for k in b.B) for i in range(3)]; mx = [max(k[i] for k in b.B) for i in range(3)]
print('size', [mx[i]-mn[i]+1 for i in range(3)], 'origin offset', mn)
ALLOWED = [((-2, -2, 25), (2, 3, 33)), ((-1, -2, 20), (1, 3, 22)), ((-1, -2, 23), (1, -1, 24))]
res = check_interior(b, (0, -2, 26), ALLOWED, dict(middeck=(0, -2, 26), flightdeck=(0, 1, 30), ods_top=(0, 3, 21), ods_floor=(0, -2, 21)))
print('内部: 密閉=%s セル=%d 未到達=%s' % (res['sealed'], res['cells'], res['unreachable']))
if not res['sealed']: print('漏れ経路:', res['leak_path'])
b.save(os.path.join(OUT, 'Shuttle_Orbiter_1m.bp'), 'スペースシャトル オービタ (1block=1m)', tags=['space', 'shuttle', 'scale-1m'])
for (x, y, z) in LEC: b.put(x, y, z, 'lectern', facing='east', has_book='false', powered='false')
b.BE = []
b.save(os.path.join(OUT, 'Shuttle_Orbiter_1m_noBE.bp'), 'スペースシャトル オービタ (1block=1m, BEなし)', tags=['space', 'shuttle', 'scale-1m'])
