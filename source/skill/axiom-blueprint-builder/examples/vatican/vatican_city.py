"""バチカン市国の全域（1ブロック=1m）。vatican.py の大聖堂・広場に、ユーザー提供の地図から読んだ
庭園・建物（美術館・使徒宮殿・行政庁ほか）・城壁・地形を足す。
  python3 vatican_city.py MAP.png OUT_DIR
地図→世界座標は mapgrid.py（ドーム中心とオベリスクの2点合わせ）。地形は西（庭園の丘）ほど高い近似。
"""
import sys, os, math, time, random
from collections import deque
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
MAP = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- 1. 大聖堂と広場（vatican.py の 1〜5・7 を実行。6=仮の宮殿、8=検証、9=保存は使わない）
src = open(os.path.join(HERE, 'vatican.py'), encoding='utf8').read()
cut = lambda s, a, b_: s[:s.index(a)] + s[s.index(b_):]
src = cut(src, '# ===================================================================== 6.', '# ===================================================================== 7.')
src = src[:src.index('# ===================================================================== 8.')]
sys.argv = [sys.argv[0], OUT]
G_ = {'__file__': os.path.join(HERE, 'vatican.py'), '__name__': 'vatican_base'}
exec(compile(src, 'vatican.py', 'exec'), G_)
b, A, put, pick, LEAF, WALL, TRAV, F = G_['b'], G_['A'], G_['put'], G_['pick'], G_['LEAF'], G_['WALL'], G_['TRAV'], G_['F']
T0 = time.time()

# ---------------------------------------------------------------- 2. 地図 → 区分格子
from mapgrid import MapGrid
M = MapGrid(MAP)
X0, X1, Z0, Z1 = M.world_bounds()
CL = {(x, z): M.at(x, z) for x in range(X0, X1 + 1) for z in range(Z0, Z1 + 1)}
# 国外＝格子の外周から「out」をたどれるセル。内側の灰色（道路の描線など）は敷地に含める
outside = set(); q = deque(k for k in CL if (k[0] in (X0, X1) or k[1] in (Z0, Z1)) and CL[k] == 'out')
outside.update(q)
while q:
    p = q.popleft()
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (p[0] + dx, p[1] + dz)
        if n in CL and n not in outside and CL[n] == 'out': outside.add(n); q.append(n)
for k, v in CL.items():
    if v == 'out' and k not in outside: CL[k] = 'ground'
# 本体（広場を含む連結成分）だけを残す：凡例や題字を除く
TERR = set(); q = deque([(200, 0)]); TERR.add((200, 0))
while q:
    p = q.popleft()
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (p[0] + dx, p[1] + dz)
        if n in CL and n not in TERR and n not in outside: TERR.add(n); q.append(n)
print('map cells', len(TERR), 'bounds', X0, X1, Z0, Z1, f'{time.time()-T0:.0f}s')

# 既存モデル（聖堂・広場・回廊）の足もと＋2 は地図から作らない
occ = {(x, z) for (x, y, z) in b.B if -1 <= y <= 30}
OCC = set()
for (x, z) in occ:
    for dx in range(-2, 3):
        for dz in range(-2, 3): OCC.add((x + dx, z + dz))
SIS = (60, 100, -74, -61)                                       # システィーナ礼拝堂（地図から読んだ位置。手で作る）
in_sis = lambda x, z: SIS[0] - 1 <= x <= SIS[1] + 1 and SIS[2] - 1 <= z <= SIS[3] + 1

# ---------------------------------------------------------------- 3. 地形（バチカンの丘：西・北西ほど高い。最大 +34m）
def Gf(x, z):
    g = 0.075 * max(0, -x - 70) + 0.022 * max(0, -z - 140)
    g = min(34.0, g)
    if g > 3: g += 1.5 * A.fbm2(x / 45, z / 45, 3, seed=4)
    return g
GH = {k: int(round(Gf(*k))) for k in TERR}

# ---------------------------------------------------------------- 4. 建物（地図の「建物」「美術館」と、聖堂の付属で未モデル化の赤い区画）
def bld_class(k):
    v = CL[k]
    if k in OCC or in_sis(*k): return None
    if v in ('bld', 'mus'): return v
    if v == 'red': return 'bld'                                   # 聖具室など
    return None
seen = set(); comps = []
for k in TERR:
    if k in seen or not bld_class(k): continue
    cl = bld_class(k); comp = []; q = deque([k]); seen.add(k)
    while q:
        p = q.popleft(); comp.append(p)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (p[0] + dx, p[1] + dz)
            if n in TERR and n not in seen and bld_class(n) == cl: seen.add(n); q.append(n)
    if len(comp) >= 25: comps.append((cl, comp))
print('buildings', len(comps), f'{time.time()-T0:.0f}s')

PAL = [('smooth_sandstone', 'cut_sandstone'), ('white_terracotta', 'smooth_sandstone'), ('yellow_terracotta', 'smooth_sandstone'),
       ('smooth_sandstone', 'white_terracotta'), ('white_terracotta', 'terracotta')]
BLD_CELLS = set()
for i, (cl, comp) in enumerate(comps):
    S = set(comp); BLD_CELLS |= S
    cx = sum(p[0] for p in comp) / len(comp); cz = sum(p[1] for p in comp) / len(comp)
    base = min(GH[p] for p in comp)
    if math.hypot(cx - 185, cz + 95) < 60 and cl == 'bld': H = 30                   # 使徒宮殿
    elif cl == 'mus': H = 22
    else: H = 12 if len(comp) < 400 else 16 if len(comp) < 1500 else 20
    wall_m, base_m = ('smooth_sandstone', 'cut_sandstone') if cl == 'mus' else PAL[(i * 7 + len(comp)) % len(PAL)]
    # 縁からの距離（屋根の寄棟用）
    D = {}; q = deque()
    for p in comp:
        if any((p[0] + dx, p[1] + dz) not in S for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))): D[p] = 1; q.append(p)
    while q:
        p = q.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (p[0] + dx, p[1] + dz)
            if n in S and n not in D: D[n] = D[p] + 1; q.append(n)
    for p in comp:
        x, z = p
        put(x, base - 1, z, 'polished_andesite')                                    # 床
        if D[p] != 1: continue
        low = min([GH.get((x + dx, z + dz), base) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))] + [base])
        for y in range(low - 1, base - 1): put(x, y, z, base_m)                    # 斜面側の基礎
        nz = (x, z + 1) not in S or (x, z - 1) not in S
        u = x if nz else z
        for y in range(base, base + H):
            fl = (y - base) % 5
            win = u % 4 == 1 and fl in (2, 3) and y > base + 1 and y < base + H - 1
            put(x, y, z, 'gray_stained_glass' if win else (base_m if y < base + 4 else wall_m))
        put(x, base + H - 1, z, 'cut_sandstone' if cl == 'mus' else base_m)        # 軒の帯
    A.smooth_heightfield(b, comp, lambda x, z, base=base, H=H, D=D: base + H + min(D[(x, z)], 6) * 0.5,
                         'bricks', 'brick_stairs', 'brick_slab', fill_down=1)
print('buildings placed', len(b.B), f'{time.time()-T0:.0f}s')

# ---------------------------------------------------------------- 5. システィーナ礼拝堂（40.9×13.4×高さ20.7m、レンガ、胸壁）
x0, x1, z0, z1 = SIS
for x in range(x0, x1 + 1):
    for z in range(z0, z1 + 1):
        put(x, -1, z, 'polished_diorite' if (x + z) % 3 else 'red_terracotta')
        wall = x in (x0, x1) or z in (z0, z1)
        if wall:
            for y in range(0, 21): put(x, y, z, 'bricks' if y > 2 else 'stone_bricks')
            if (x + z) % 2 == 0: put(x, 21, z, 'bricks')
        else:
            put(x, 20, z, 'light_blue_terracotta' if (x // 4 + z // 4) % 2 else 'yellow_terracotta')   # 天井画の見立て
            put(x, 21, z, 'brick_slab', type='bottom', waterlogged='false')
for x in range(x0 + 4, x1 - 2, 6):
    for z, n_ in ((z0, 'north'), (z1, 'south')): A.opening(b, x, 12, z, n_, w=2, h=6, sharp=1.0, glass='glass_pane')
for y in range(0, 4): b.rm(x1, y, (z0 + z1) // 2); b.rm(x1, y, (z0 + z1) // 2 + 1)

# ---------------------------------------------------------------- 6. 地面（庭園・中庭・道）と城壁
def near_green(x, z, r=4):
    c = n = 0
    for dx in range(-r, r + 1, 2):
        for dz in range(-r, r + 1, 2):
            v = CL.get((x + dx, z + dz))
            if v: n += 1; c += v == 'green'
    return c / max(1, n)
# 城壁：国境から内側3マス（既存モデルの近く・広場の東は除く）
dist_out = {}; q = deque()
for k in TERR:
    if any((k[0] + dx, k[1] + dz) not in TERR for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))): dist_out[k] = 1; q.append(k)
while q:
    p = q.popleft()
    if dist_out[p] >= 2: continue
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (p[0] + dx, p[1] + dz)
        if n in TERR and n not in dist_out: dist_out[n] = dist_out[p] + 1; q.append(n)
def is_wall(k):
    return k in dist_out and k not in OCC and k not in BLD_CELLS and not in_sis(*k) and not (k[0] > 120 and -150 < k[1] < 160)
GREEN = []
for k in TERR:
    if k in OCC or k in BLD_CELLS or in_sis(*k): continue
    x, z = k; g = GH[k]; v = CL[k]
    low = min(GH.get((x + dx, z + dz), g) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    if is_wall(k):
        top = g + 9
        for y in range(min(low, g) - 1, top): put(x, y, z, pick([('mud_bricks', 2), ('bricks', 1), ('stone_bricks', 1)], x, y, z))
        if dist_out[k] == 2: put(x, top - 1, z, 'stone_brick_slab', type='top', waterlogged='false')
        if dist_out[k] == 1 and (x + z) % 2 == 0: put(x, top, z, 'bricks')
        continue
    if v == 'green': m = 'grass_block'; GREEN.append(k)
    elif v == 'water': m = 'water'
    else:
        m = ('gravel' if (x * 7 + z * 13) % 5 else 'dirt_path') if near_green(x, z) > 0.45 else \
            pick([('polished_andesite', 2), ('smooth_stone', 2), ('stone_bricks', 1)], x, g, z)
    for y in range(min(low, g) - 1, g - 1): put(x, y, z, 'dirt' if v == 'green' else 'stone')
    if m == 'water':
        put(x, g - 2, z, 'smooth_sandstone'); put(x, g - 1, z, 'water', level='0')
    else: put(x, g - 1, z, m, **({'snowy': 'false'} if m == 'grass_block' else {}))
print('ground', len(b.B), f'{time.time()-T0:.0f}s')

# ---------------------------------------------------------------- 7. 樹木（イタリアカサマツ・イトスギ・トキワガシ）を庭園に散らす
GS = set(GREEN)
pts = A.poisson_disk(X0, Z0, X1, Z1, 7.5, seed=11)
nt = 0
for (x, z) in pts:
    if (x, z) not in GS or any((x + dx, z + dz) not in GS for dx in (-2, 0, 2) for dz in (-2, 0, 2)): continue
    g = GH[(x, z)]; r = A._hash(x, z, seed=5); nt += 1
    if r < 0.45:                                                   # 傘状のカサマツ
        h = 8 + int(r * 8)
        for y in range(g, g + h): put(x, y, z, 'spruce_log', axis='y')
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                d = math.hypot(dx, dz)
                if d <= 4.8:
                    put(x + dx, g + h, z + dz, 'jungle_leaves' if d > 2 else 'spruce_leaves', **LEAF)
                    if d <= 3.2: put(x + dx, g + h + 1, z + dz, 'jungle_leaves', **LEAF)
    elif r < 0.7:                                                  # 細長いイトスギ
        h = 9 + int((r - .45) * 20)
        for y in range(g, g + h):
            put(x, y, z, 'spruce_leaves', **LEAF)
            if y < g + h - 2:
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if y > g + 1: put(x + dx, y, z + dz, 'spruce_leaves', **LEAF)
        put(x, g, z, 'spruce_log', axis='y')
    else:                                                          # 丸いトキワガシ
        for y in range(g, g + 4): put(x, y, z, 'dark_oak_log', axis='y')
        b.shell(x, g + 5, z, 3.3, 2.6, 3.3, 'dark_oak_leaves', inner=.35, lumpy=.3, **LEAF)
print('trees', nt, f'{time.time()-T0:.0f}s')

# ---------------------------------------------------------------- 8. 目印：ヘリポート・聖ヨハネの塔・ヴァチカン放送の送信塔
def gnd(x, z): return GH.get((x, z), 0)
hx, hz = -520, 32                                                  # ヘリポート（西の先端）
if (hx, hz) in TERR:
    g = gnd(hx, hz)
    for u, v in A.circle_cells(10, filled=True):
        put(hx + u, g - 1, hz + v, 'white_concrete' if math.hypot(u, v) > 9 else 'smooth_stone')
        for y in range(g, g + 3): b.rm(hx + u, y, hz + v)
    for d in range(-4, 5): put(hx - 3, g - 1, hz + d, 'white_concrete'); put(hx + 3, g - 1, hz + d, 'white_concrete')
    for d in range(-3, 4): put(hx + d, g - 1, hz, 'white_concrete')
tx, tz = -440, 70                                                  # 聖ヨハネの塔（城壁の円塔）
g = gnd(tx, tz)
for y in range(g - 2, g + 18):
    for u, v in A.circle_cells(7): put(tx + u, y, tz + v, pick([('stone_bricks', 3), ('andesite', 1)], tx + u, y, tz + v))
for u, v in A.circle_cells(7.5, filled=True): put(tx + u, g + 18, tz + v, 'stone_brick_slab', type='bottom', waterlogged='false')
rx, rz = -385, 95                                                  # 送信塔（格子の鉄塔）
g = gnd(rx, rz); RH = 55
for y in range(g, g + RH):
    w = 4 * (1 - (y - g) / RH) + 0.6
    for sx in (-1, 1):
        for sz in (-1, 1): put(rx + int(round(sx * w)), y, rz + int(round(sz * w)), 'iron_bars', east='false', west='false', north='false', south='false', waterlogged='false')
    if (y - g) % 6 == 0:
        W_ = int(round(w))
        for d in range(-W_, W_ + 1):
            for p in ((rx + d, rz - W_), (rx + d, rz + W_), (rx - W_, rz + d), (rx + W_, rz + d)): put(p[0], y, p[1], 'iron_bars', east='true', west='true', north='true', south='true', waterlogged='false')
put(rx, g + RH, rz, 'red_concrete'); put(rx, g + RH + 1, rz, 'redstone_lamp', lit='true')
print('landmarks', len(b.B), f'{time.time()-T0:.0f}s')

# ---------------------------------------------------------------- 9. 保存
tags = ['vatican', 'city', 'basilica', 'landmark', 'scale-1m', 'interior', 'map']
n = b.save(os.path.join(OUT, 'Vatican_City_1m.bp'), 'バチカン市国 全域 (1block=1m)', tags=tags, origin='bottom_center')
BE = b.BE; b.BE = []
b.put(130, F, 6, 'lectern', facing='west', has_book='false', powered='false')
b.save(os.path.join(OUT, 'Vatican_City_1m_noBE.bp'), 'バチカン市国 全域 (1block=1m, BEなし)', tags=tags, origin='bottom_center')
xs = [k[0] for k in b.B]; ys = [k[1] for k in b.B]; zs = [k[2] for k in b.B]
print('size', max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1, f'{time.time()-T0:.0f}s')
for row in A.palette_stats(b, 12): print('  ', row)
