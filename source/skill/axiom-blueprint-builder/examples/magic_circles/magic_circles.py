"""魔法陣（幾何学・ルーン）を式で作る例。1層、中心が原点 (0,0,0)。
  python3 magic_circles.py [出力ディレクトリ]   → geometric_circle.bp / rune_circle.bp と、確認用の上面図 PNG を出す
色は PAL を差し替えるだけで変えられる（形は変わらない）。
学び: ①ルーンは『線分を連続座標で回転配置→セルごとに線分距離で塗る』と斜めでも崩れない ②重ね順＝後から描いたものが勝つ
      ③中心の円の中は一度クリアしてから別模様を描く ④線の太さは seg_dist のしきい値 0.5〜0.9（1〜2ブロック幅）。
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from builder import Build
from pattern_helpers import *

# ---------------- 幾何学の魔法陣（紅と金、R=73） ----------------
PAL_GEO = dict(red='red_concrete', org='orange_concrete', yel='yellow_concrete', gold='gold_block', white='white_wool')
def geometric_circle(P=PAL_GEO, R=73):
    S5 = star_segments(57, 12, 5); S4 = star_segments(57, 12, 4)       # 十二芒星 {12/5} と 正三角形4つ {12/4}
    FC = hex_lattice_centers(9.0, 18.5)                                  # フラワー・オブ・ライフ（間隔9、半径9）
    def f(x, z):
        r = math.hypot(x, z); deg = math.degrees(math.atan2(z, x)) % 360; out = None
        if r > R + 0.5: return None
        if r >= 69.8:                                                    # 外縁の鋸歯(10°ごと)
            ph = (deg % 10) / 10.0
            if r - 69.8 < 3.3 * (1 - abs(2 * ph - 1)): out = P['org']
        if abs(r - 69.0) < 1.0: out = P['red']
        if abs(r - 67.2) < 0.5: out = P['gold']
        if 58.6 <= r <= 66.4:                                            # 内側の鋸歯帯(15°ごと、交互)
            sec = int(deg // 15); ph = (deg % 15) / 15.0
            if r - 58.6 < 7.6 * (1 - abs(2 * ph - 1)): out = P['org'] if sec % 2 == 0 else P['yel']
        if abs(r - 58.0) < 0.55: out = P['red']
        for c in (45.0, 33.5):
            if abs(r - c) < 0.5: out = P['gold']
        for (A, B) in S4:
            if seg_dist(x, z, A[0], A[1], B[0], B[1]) < 0.52: out = P['gold']
        for (A, B) in S5:
            if seg_dist(x, z, A[0], A[1], B[0], B[1]) < 0.85: out = P['red']
        for k in range(12):                                              # 頂点の飾り・星の谷の菱形・小円
            vx, vz = 57 * math.cos(D(-90 + 30 * k)), 57 * math.sin(D(-90 + 30 * k)); dd = math.hypot(x - vx, z - vz)
            if dd < 3.6: out = P['red'] if dd > 2.3 else (P['white'] if dd < 1.0 else P['gold'])
            c = D(-75 + 30 * k); px, pz = 47.5 * math.cos(c), 47.5 * math.sin(c)
            if abs(x - px) + abs(z - pz) < 2.6: out = P['yel']
            px, pz = 39.5 * math.cos(c), 39.5 * math.sin(c); dd = math.hypot(x - px, z - pz)
            if dd < 3.6: out = P['org'] if dd > 2.4 else (P['yel'] if dd > 1.0 else P['red'])
        if r <= 27.4:                                                    # 中心: 一旦クリア → フラワー・オブ・ライフ
            out = None
            for (cx, cz) in FC:
                if abs(math.hypot(x - cx, z - cz) - 9.0) < 0.62 and r <= 27.0: out = P['org']
            for (cx, cz) in FC:
                if math.hypot(x - cx, z - cz) < 1.2: out = P['gold']
        if abs(r - 27.6) < 0.95: out = P['red']
        if abs(r - 29.6) < 0.5: out = P['gold']
        if r <= 4.3: out = P['gold'] if r > 1.5 else P['white']
        return out
    return f, R

# ---------------- ルーンの魔法陣（藍と金、R=76） ----------------
PAL_RUNE = dict(lap='lapis_block', blu='blue_concrete', cyn='cyan_concrete', lbl='light_blue_concrete', ww='white_wool', qz='quartz_block',
                gold='gold_block', glass='light_blue_stained_glass')
def rune_circle(P=PAL_RUNE, R=76):
    RA = place_runes(ELDER_FUTHARK, 24, 60.4, 9.7, 1.6, -90)             # 外側: エルダー・フサルク24字（金）
    RB = place_runes(YOUNGER_FUTHARK, 16, 42.2, 6.7, 1.2, -90)           # 内側: ヤンガー・フサルク16字（白）
    HEX = hexagram_segments(38)
    GR = [P['blu'], P['lap'], P['cyn'], P['lbl'], P['qz'], P['ww']]       # 蓮の花弁: 濃→淡
    def petal(deg, r, ang, r0, r1, wm):
        h = petal_hit(deg, r, ang, r0, r1, wm, tip=0.8)
        if not h: return None
        t, v, w = h
        if v > w - 0.9: return P['lap']
        return GR[min(len(GR) - 1, int(t * (len(GR) - 0.001)))]
    def f(x, z):
        r = math.hypot(x, z); deg = math.degrees(math.atan2(z, x)); out = None
        if r > R + 0.5: return None
        if abs(r - 75.3) < 0.6:
            m = round(deg / 7.5)
            if r * abs(D(deg - m * 7.5)) < 0.8: out = P['glass']
        if abs(r - 73.3) < 1.0: out = P['blu']
        if abs(r - 71.4) < 0.55: out = P['cyn']
        if abs(r - 59.0) < 0.55: out = P['cyn']
        if abs(r - 57.3) < 0.9: out = P['lap']
        if 51.2 <= r <= 56.2:                                            # 装飾環: 区切りに菱形、字の中心に点
            m = round((deg + 90 - 7.5) / 15); c = D(m * 15 + 7.5 - 90)
            dd = abs(x - 53.7 * math.cos(c)) + abs(z - 53.7 * math.sin(c))
            if dd < 3.4: out = P['ww'] if dd < 1.7 else P['cyn']
            m2 = round((deg + 90) / 15); c2 = D(m2 * 15 - 90)
            if math.hypot(x - 53.7 * math.cos(c2), z - 53.7 * math.sin(c2)) < 1.5: out = P['lbl']
        if abs(r - 50.3) < 0.85: out = P['lap']
        if abs(r - 41.0) < 0.55: out = P['cyn']
        if abs(r - 49.2) < 0.5: out = P['cyn']
        if abs(r - 31.0) < 0.5:
            m = round(deg / 7.5)
            if r * abs(D(deg - m * 7.5)) < 0.9: out = P['ww']
        if abs(r - 33.2) < 0.45: out = P['cyn']
        for (A, B) in HEX:
            if seg_dist(x, z, A[0], A[1], B[0], B[1]) < 1.0: out = P['lbl']
        for k in range(6):
            vx, vz = 38 * math.cos(D(-90 + 60 * k)), 38 * math.sin(D(-90 + 60 * k)); dd = math.hypot(x - vx, z - vz)
            if dd < 4.4: out = P['lap'] if dd > 3.0 else (P['ww'] if dd < 1.5 else P['gold'])
            vx, vz = 21.9 * math.cos(D(-60 + 60 * k)), 21.9 * math.sin(D(-60 + 60 * k)); dd = math.hypot(x - vx, z - vz)
            if dd < 2.6: out = P['gold'] if dd < 1.3 else P['lap']
        if abs(r - 19.2) < 0.8: out = P['lap']
        if abs(r - 20.9) < 0.45: out = P['cyn']
        if r <= 18.6:
            for ang, r0, r1, wm in [(a, 5.5, 18.0, 4.4) for a in range(-90, 270, 60)] + [(a, 5.5, 13.5, 2.6) for a in range(-60, 300, 60)]:
                c = petal(deg, r, ang, r0, r1, wm)
                if c: out = c
        if abs(r - 6.2) < 0.7: out = P['lap']
        if r < 5.0: out = P['ww'] if r > 2.4 else P['gold']
        if 59.6 < r < 71.2 and rune_hit(x, z, RA): out = P['gold']       # ルーンは最前面
        if 41.4 < r < 49.2 and rune_hit(x, z, RB): out = P['qz']
        return out
    return f, R

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, gen, title in (('geometric_circle', geometric_circle, '幾何学の魔法陣'), ('rune_circle', rune_circle, 'ルーンの魔法陣')):
        f, R = gen(); b = Build(); grid = paint(b, f, R)
        b.save(os.path.join(out, name + '.bp'), title, author='nemo', tags=['magic circle', 'floor'])
        render_top(grid, os.path.join(out, name + '_top.png'), S=6)
