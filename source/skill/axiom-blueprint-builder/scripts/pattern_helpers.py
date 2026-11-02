"""平面の文様・曼荼羅・魔法陣・レリーフのための補助関数（Build と併用）。

使い方の流れ（references/patterns.md に根拠と失敗談）
  A. 参考画像を再現する:  estimate_block_px → sample_grid → classify → fold_d2 → to_build
  B. 魔法陣・幾何学文様を式で作る: f(x,z)->ブロック名 を書き、paint(b, f, R) で敷く（対称は『第1象限で評価→折り返し』fold4 か、
     連続関数を直接評価）。ルーンは place_runes/rune_hit、星形は star_segments+seg_dist、花弁は petal_hit。
  C. 色違い(四季)にする: recolor(cls, names, {旧: 新})。形は変えず、濃→淡の並びを保つ。
  D. 空中のレリーフ: put_relief(b, rx, ry, rz, cell_fn) で『(z方向の層, ブロック)』のリストを積む（縁の段差・葉脈の盛り上がり）。
  確認は render_top(grid, 'top.png') で上から見た図を出し、必ず view で目視する（プレビューは等角なので文様の崩れに気づきにくい）。

座標の約束: 平面は x=東, z=南(画像の下)。angle は atan2(dz,dx)（度）で x 軸から z 方向へ増える＝画面上は時計回り。
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = math.radians


# ============================ A. 画像 → 格子 ============================
def estimate_block_px(rgb):
    """真上〜やや斜めから撮ったブロック絵の『1ブロックのピクセル幅』を FFT で推定。rgb は (H,W,3) の numpy 配列。
    戻り値=(幅方向, 高さ方向)。両者がほぼ等しければ正投影に近い。"""
    import numpy as np
    g = rgb.astype(float).mean(2)
    def per(e):
        e = e - e.mean(); k = np.argmax(np.abs(np.fft.rfft(e))[20:300]) + 20
        return len(e) / k
    return per(np.abs(np.diff(g, axis=1)).sum(0)), per(np.abs(np.diff(g, axis=0)).sum(1))


def sample_grid(rgb, n, center_px, block_px, win=4):
    """中心ブロックのピクセル座標 center_px=(cx,cy)、1ブロック幅 block_px で n×n の格子をサンプリング（各セルの中央 (2win+1)² の中央値色）。
    n は奇数にして中心ブロックを n//2 に置く（左右対称の作品は中心列が空気/金ブロックのことが多い）。戻り値=(n,n,3) float。"""
    import numpy as np
    c = n // 2; cells = np.zeros((n, n, 3))
    for j in range(n):
        for i in range(n):
            x = center_px[0] + (i - c) * block_px; y = center_px[1] + (j - c) * block_px
            r = rgb[int(y - win):int(y + win + 1), int(x - win):int(x + win + 1)].reshape(-1, 3)
            cells[j, i] = np.median(r, axis=0) if len(r) else (0, 0, 0)
    return cells


def classify(cells, proto, dark_to=None, dark_sum=340, region_rules=None):
    """各セルを最も近い代表色(proto={名前:(r,g,b)} 先頭を空気に)へ。名前リスト names と整数配列 cls を返す。
    dark_to: 影で暗くなったセルをこの名前へ寄せる（斜め撮りの側面影対策）。
    region_rules: {名前: 許可関数(i,j)->bool}。特定の色（灰色・ガラス等）を許す領域を限定し、乱れを防ぐ。"""
    import numpy as np
    names = list(proto); P = np.array([proto[k] for k in names], float)
    d = ((cells[:, :, None, :] - P[None, None, :, :]) ** 2).sum(3).astype(float)
    if region_rules:
        n = cells.shape[0]
        for nm, ok in region_rules.items():
            idx = names.index(nm)
            for j in range(n):
                for i in range(n):
                    if not ok(i, j): d[j, i, idx] = 1e12
    cls = d.argmin(2)
    if dark_to is not None: cls[cells.sum(2) < dark_sum] = names.index(dark_to)
    return cls, names


def fold_d2(cls, air=0):
    """左右・上下の鏡像4セルで多数決して対称化（読み取りノイズ除去）。中心は (n//2,n//2)。同数なら空気以外を優先（細線の欠け対策）。"""
    from collections import Counter
    n = cls.shape[0]; c = n // 2; out = cls.copy()
    for j in range(c + 1):
        for i in range(c + 1):
            pts = [(c + sj * j, c + si * i) for si in (1, -1) for sj in (1, -1)]
            cnt = Counter(int(cls[p]) for p in pts)
            best = max(cnt.items(), key=lambda kv: (kv[1], kv[0] != air))[0]
            for p in pts: out[p] = best
    return out


def recolor(cls, names, mapping):
    """色違い版: mapping={元の名前:新しい名前}。戻り値=(cls, newnames)。形・並びはそのまま。"""
    new = [mapping.get(n, n) for n in names]
    return cls, new


def to_build(b, cls, names, y=0, skip='air'):
    """(n,n) の分類を Build に置く。中心ブロックが原点 (0,y,0)。"""
    n = cls.shape[0]; c = n // 2
    for j in range(n):
        for i in range(n):
            nm = names[int(cls[j, i])]
            if nm != skip: b.put(i - c, y, j - c, nm)


# ============================ B. 幾何 ============================
def angd(a, b):
    """度の角度差の絶対値（0〜180）"""
    return abs(((a - b + 180) % 360) - 180)


def seg_dist(px, py, ax, ay, bx, by):
    """点から線分への距離（線の太さ判定に。しきい値 0.5〜0.9 が 1〜2 ブロック幅）"""
    vx, vy = bx - ax, by - ay; L = vx * vx + vy * vy
    t = max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L)) if L else 0
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def polygon_points(rv, n, off=-90):
    """正n角形の頂点。off=-90 で頂点が北（画面上）。"""
    return [(rv * math.cos(D(off + 360 * k / n)), rv * math.sin(D(off + 360 * k / n))) for k in range(n)]


def star_segments(rv, n, m, off=-90):
    """正n芒星 {n/m} の線分リスト [((x0,z0),(x1,z1))…]。{8/3}八芒星・{12/5}十二芒星・{6/2}六芒星(=2個の三角形)など。"""
    pts = polygon_points(rv, n, off)
    return [(pts[k], pts[(k + m) % n]) for k in range(n)]


def hexagram_segments(rv, off=-90):
    """六芒星＝上向き三角形＋下向き三角形"""
    a = polygon_points(rv, 3, off); b = polygon_points(rv, 3, off + 60)
    return [(a[k], a[(k + 1) % 3]) for k in range(3)] + [(b[k], b[(k + 1) % 3]) for k in range(3)]


def petal_hit(th, r, psi, r0, r1, wmax, tip=0.6):
    """極座標の花弁（葉）判定。th=点の角度(度), r=半径, psi=花弁の中心角(度), r0〜r1=根元〜先端, wmax=最大の半幅(ブロック)。
    先端が尖る（tip<1 で丸く膨らむ根元）。当たれば (t,v,w)=(0..1の長さ位置, 中心線からの距離, その位置の半幅)、外れれば None。
    t と v で『中心線だけ別色』『先端だけ別色』が書ける。"""
    t = (r - r0) / (r1 - r0)
    if not 0 <= t <= 1: return None
    d = angd(th, psi)
    if d > 60: return None
    w = wmax * (math.sin(math.pi * t ** tip) ** 0.9)
    v = r * math.sin(D(d))
    return (t, v, w) if v <= w else None


def hex_lattice_centers(spacing, rmax):
    """フラワー・オブ・ライフ等の六角格子の中心。半径=spacing の円を各中心に描くと『生命の花』になる。"""
    out = []
    for a in range(-6, 7):
        for b in range(-6, 7):
            x = spacing * (a + 0.5 * b); y = spacing * (math.sqrt(3) / 2 * b)
            if math.hypot(x, y) <= rmax: out.append((x, y))
    return out


def fold4(x, z):
    """D4 対称（上下左右＋斜め）の基本領域 a>=b>=0 に畳む。f(*fold4(x,z)) と書けば完全な8回対称になる。"""
    a, b = abs(x), abs(z)
    return (b, a) if b > a else (a, b)


def paint(b, f, R, y=0, margin=2):
    """f(x,z)->ブロック名|None を (-R-margin..R+margin) の全セルで評価して置く。戻り値=置いたセルの dict {(x,z):名}（render_top 用）。"""
    grid = {}
    for z in range(-R - margin, R + margin + 1):
        for x in range(-R - margin, R + margin + 1):
            n = f(x, z)
            if n: b.put(x, y, z, n); grid[(x, z)] = n
    return grid


def render_top(grid, path, S=8, bg=(205, 212, 218)):
    """{(x,z):ブロック名} を colors.py の色で上から見た PNG にする（文様確認用）。"""
    import numpy as np
    from PIL import Image
    import colors
    xs = [k[0] for k in grid]; zs = [k[1] for k in grid]
    x0, x1, z0, z1 = min(xs) - 2, max(xs) + 2, min(zs) - 2, max(zs) + 2
    img = np.full(((z1 - z0 + 1) * S, (x1 - x0 + 1) * S, 3), bg, np.uint8)
    for (x, z), nm in grid.items():
        c = colors.col(nm)
        img[(z - z0) * S:(z - z0 + 1) * S, (x - x0) * S:(x - x0 + 1) * S] = ((c >> 16) & 255, (c >> 8) & 255, c & 255)
    Image.fromarray(img).save(path)
    return path


# ============================ ルーン文字 ============================
def _S(a, b, c, d): return ((a, b), (c, d))
# 線分の座標は u:0..4(幅), v:0..8(高さ)。字形は簡略化（ジェラ ᛃ・ペルスロ ᛈ などは近似）。
ELDER_FUTHARK = [   # ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ ᛁ ᛃ ᛇ ᛈ ᛉ ᛊ ᛏ ᛒ ᛖ ᛗ ᛚ ᛜ ᛞ ᛟ
    [_S(2, 0, 2, 8), _S(2, 6, 4, 8), _S(2, 3, 4, 5)],
    [_S(.5, 0, .5, 8), _S(.5, 8, 3.5, 5), _S(3.5, 5, 3.5, 0)],
    [_S(1, 0, 1, 8), _S(1, 6.5, 3.5, 4.3), _S(3.5, 4.3, 1, 2)],
    [_S(1, 0, 1, 8), _S(1, 8, 3.5, 5.7), _S(1, 5.5, 3.5, 3.2)],
    [_S(1, 0, 1, 8), _S(1, 8, 3.5, 6), _S(3.5, 6, 1, 4), _S(1, 4, 3.5, 0)],
    [_S(3.5, 8, .5, 4), _S(.5, 4, 3.5, 0)],
    [_S(.3, .3, 3.7, 7.7), _S(.3, 7.7, 3.7, .3)],
    [_S(1, 0, 1, 8), _S(1, 8, 3.5, 6), _S(3.5, 6, 1, 4)],
    [_S(.5, 0, .5, 8), _S(3.5, 0, 3.5, 8), _S(.5, 5, 3.5, 3)],
    [_S(2, 0, 2, 8), _S(.4, 2.5, 3.6, 5.5)],
    [_S(2, 0, 2, 8)],
    [_S(2, 8, .5, 6), _S(.5, 6, 2, 4), _S(2, 4, 3.5, 2), _S(3.5, 2, 2, 0)],
    [_S(2, 0, 2, 8), _S(2, 8, 3.6, 6.8), _S(2, 0, .4, 1.2)],
    [_S(.5, 0, .5, 8), _S(.5, 8, 3.5, 6.5), _S(3.5, 6.5, .5, 4.5)],
    [_S(2, 0, 2, 8), _S(2, 4, .3, 8), _S(2, 4, 3.7, 8)],
    [_S(3.5, 8, .5, 5.5), _S(.5, 5.5, 3.5, 2.5), _S(3.5, 2.5, .5, 0)],
    [_S(2, 0, 2, 8), _S(.3, 5.5, 2, 8), _S(2, 8, 3.7, 5.5)],
    [_S(.5, 0, .5, 8), _S(.5, 8, 3.5, 6), _S(3.5, 6, .5, 4), _S(.5, 4, 3.5, 2), _S(3.5, 2, .5, 0)],
    [_S(.5, 0, .5, 8), _S(3.5, 0, 3.5, 8), _S(.5, 8, 2, 5.5), _S(3.5, 8, 2, 5.5)],
    [_S(.5, 0, .5, 8), _S(3.5, 0, 3.5, 8), _S(.5, 8, 3.5, 3.5), _S(3.5, 8, .5, 3.5)],
    [_S(1, 0, 1, 8), _S(1, 8, 3.5, 5.5)],
    [_S(2, 8, .3, 4), _S(.3, 4, 2, 0), _S(2, 0, 3.7, 4), _S(3.7, 4, 2, 8)],
    [_S(.5, 0, .5, 8), _S(3.5, 0, 3.5, 8), _S(.5, 8, 3.5, 0), _S(.5, 0, 3.5, 8)],
    [_S(2, 5, .5, 6.5), _S(.5, 6.5, 2, 8), _S(2, 8, 3.5, 6.5), _S(3.5, 6.5, 2, 5), _S(2, 5, .5, 0), _S(2, 5, 3.5, 0)],
]
YOUNGER_FUTHARK = [  # ᚠ ᚢ ᚦ ᚬ ᚱ ᚴ ᚼ ᚾ ᛁ ᛅ ᛋ ᛏ ᛒ ᛘ ᛚ ᛦ
    ELDER_FUTHARK[0], ELDER_FUTHARK[1], ELDER_FUTHARK[2],
    [_S(1, 0, 1, 8), _S(1, 8, 3.5, 5.5)], ELDER_FUTHARK[4], [_S(1, 0, 1, 8), _S(1, 5, 3.5, 8)],
    [_S(.5, 0, .5, 8), _S(3.5, 0, 3.5, 8), _S(.5, 4, 3.5, 4)], ELDER_FUTHARK[9], ELDER_FUTHARK[10],
    [_S(2, 0, 2, 8), _S(2, 5, 3.6, 7)], [_S(3, 8, 1, 5.2), _S(1, 5.2, 3, 3), _S(3, 3, 1, 0)],
    ELDER_FUTHARK[16], ELDER_FUTHARK[17], ELDER_FUTHARK[19], ELDER_FUTHARK[20],
    [_S(2, 0, 2, 8), _S(2, 4, .3, 0), _S(2, 4, 3.7, 0)],
]


def place_runes(runes, n, r0, H, su, theta0=-90):
    """円環に n 個のルーンを配置。r0=底辺の半径、H=高さ(ブロック)、su=幅の倍率(1.0で幅4)、theta0=最初の字の角度(度、-90=真上)。
    頂部が外向き・時計回りに読む向き。戻り値=[(角度rad, [世界座標の線分…]), …]（中心原点）。斜め配置は連続座標のまま線分距離で
    塗るのでどの角度でも欠けにくい。字数 n が runes より多ければ循環。"""
    out = []
    for k in range(n):
        segs = runes[k % len(runes)]
        th = D(theta0 + k * 360.0 / n); nx, ny = math.cos(th), math.sin(th); tx, ty = -math.sin(th), math.cos(th)
        ws = []
        for (a, b) in segs:
            pts = []
            for (u, v) in (a, b):
                U = (u - 2) * su; V = r0 + v * H / 8.0
                pts.append((nx * V + tx * U, ny * V + ty * U))
            ws.append((pts[0], pts[1]))
        out.append((th, ws))
    return out


def rune_hit(x, z, placed, theta0=-90, thick=0.85):
    """点 (x,z) がルーンの線上か（その点が属する字だけ調べる）。thick=0.85 で太め（1〜2ブロック幅）。"""
    n = len(placed)
    th = math.atan2(z, x)
    k = round((th - D(theta0)) / (2 * math.pi / n)) % n
    for (p, q) in placed[k][1]:
        if seg_dist(x, z, p[0], p[1], q[0], q[1]) < thick: return True
    return False


# ============================ モチーフ(楓・ひまわり) ============================
# (中心角°, 長さ, 半幅°)  角度は『上=0°、東が正』
MAPLE5 = [(0, 14.8, 32), (58, 12.8, 36), (-58, 12.8, 36), (122, 9.2, 32), (-122, 9.2, 32)]      # 楓(5裂)
MOMIJI7 = [(0, 25, 21), (37, 22.5, 20), (-37, 22.5, 20), (74, 17.5, 19), (-74, 17.5, 19), (112, 11.5, 17), (-112, 11.5, 17)]  # モミジ(7裂・細く尖る)


def lobed_leaf_r(al, lobes, base=4.4, power=0.55, floor=0.30, serration=0.07, freq=17):
    """掌状に裂けた葉の外形半径。al=上を0°・東が正の角度(度)。各 lobe は余弦の山、縁にギザギザ。
    広い楓は power≈0.55/floor 0.30、細く尖るモミジは power≈1.25/floor 0.16。lobes 間の谷は base まで落ちる。"""
    best = base
    for (psi, L, w) in lobes:
        t = angd(al, psi) / w
        if t < 1:
            rk = L * (floor + (1 - floor) * math.cos(t * math.pi / 2) ** power) * (1 + serration * math.sin(D(al) * freq))
            best = max(best, rk)
    return best


def phyllotaxis(n_max, scale=0.64, golden=137.508):
    """ひまわりの種の螺旋（フェルマー螺旋）。{(x,z)整数:番号} を返す。scale=0.64 で半径≈8 に 190 粒。"""
    out = {}
    for n in range(1, n_max):
        rr = scale * math.sqrt(n); a = D(n * golden)
        out[(round(rr * math.cos(a)), round(rr * math.sin(a)))] = n
    return out


def put_relief(b, rx, ry, rz, cell_fn, xr, yr):
    """空中の板状レリーフ（xy 平面、南向き=+z が表）。cell_fn(dx,dy)->[(zオフセット, ブロック名)…]（dy は上が +）。
    zオフセット 0=奥の板、1=中、2=手前（葉脈・種を盛り上がらせる）。xr, yr は range。戻り値=置いたブロック数。"""
    n = 0
    for dx in xr:
        for dy in yr:
            for (zo, nm) in cell_fn(dx, dy):
                b.put(rx + dx, ry + dy, rz + zo, nm); n += 1
    return n


if __name__ == '__main__':      # 動作確認: python3 pattern_helpers.py
    assert abs(angd(10, 350) - 20) < 1e-9
    assert len(ELDER_FUTHARK) == 24 and len(YOUNGER_FUTHARK) == 16
    segs = star_segments(10, 12, 5); assert len(segs) == 12
    assert 3 <= lobed_leaf_r(0, MAPLE5) <= 15
    pl = place_runes(ELDER_FUTHARK, 24, 20, 9, 1.4); assert len(pl) == 24
    print('pattern_helpers OK  runes:', sum(rune_hit(x, z, pl) for x in range(-30, 31) for z in range(-30, 31)), 'cells')
