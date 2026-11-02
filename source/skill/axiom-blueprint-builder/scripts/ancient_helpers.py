"""古代遺跡・幻想風の外装ヘルパー（スフィンクス・オベリスク・塔門・列柱・ヤシ・砂の吹き溜まり・光の亀裂・浮遊太陽円盤・面のピクセルアート）。
ピラミッド等に「歴史・神話・ロマン」を足すための部品。arch_helpers と併用（G=地表）。
面のピクセルアートは『外周リングの階段ブロックの素材を差し替える』方式（形は崩れない）。"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arch_helpers import *

# ---------------------------------------------------------------- 面のピクセルアート
# 凡例：階段素材（遠目でも色が出る）。'.'=差し替えなし
PIX = dict(G='cut_copper_stairs', T='oxidized_cut_copper_stairs', D='dark_prismarine_stairs', R='red_sandstone_stairs',
           W='quartz_stairs', K='blackstone_stairs', Y='smooth_sandstone_stairs', P='purpur_stairs')

def winged_sun(wing=12, disc=3.6):
    """有翼の太陽円盤：中央に赤い円盤(金縁)と蛇、左右に5段の羽（藍/青緑/金/青緑/藍、先端は白）"""
    W = 2*(wing+5)+1; H = 11; cx, cy = W//2, H//2
    g = [['.']*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            r = math.hypot(x-cx, (y-cy)*1.0)
            if r <= disc: g[y][x] = 'G' if r > disc-1.1 else 'R'
    for dy, col in zip(range(-2, 3), 'DTGTD'):
        L = wing-abs(dy)*2+2
        for i in range(L):
            for s in (-1, 1):
                x = cx+s*(int(disc)+1+i); y = cy+dy
                if 0 <= x < W: g[y][x] = 'W' if i >= L-2 else col
    g[cy-int(disc)-1][cx-1] = g[cy-int(disc)-1][cx+1] = 'K'          # 蛇(ウラエウス)の目
    return [''.join(r) for r in g]

def eye_of_horus(W=21, H=12):
    """ホルスの目：白目・青緑の虹彩・黒の縁取り・金の眉・渦巻きの尾"""
    cx, cy = W//2, 4; g = [['.']*W for _ in range(H)]
    for x in range(W):
        c = (x-cx)/(W/2-1); h = round(3.2*(1-c*c))
        for dy in range(-h, h+1):
            g[cy+dy][x] = 'K' if abs(dy) == h else 'W'
        if h >= 1: g[cy-h-2][x] = 'G' if abs(c) < .85 else '.'     # 眉
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx*dx+dy*dy <= 5: g[cy+dy][cx+dx] = 'T'
    g[cy][cx] = 'K'
    for i in range(3): g[cy+3+i][cx+1] = 'K'                          # 涙の筋
    for i in range(4): g[cy+5][cx+1+i] = 'K'
    g[cy+6][cx+4] = 'G'; g[cy+7][cx+4] = 'G'
    return [''.join(r) for r in g]

def ankh():
    return ["..GGGGG..", ".GG...GG.", ".G.....G.", ".G.....G.", ".GG...GG.", "..GGGGG..", "....G....", "GGGGGGGGG", "....G....", "....G....", "....G....", "....G....", "....G...."]

def paint_face(b, B, side, rows, y_bottom, legend=PIX, skip=None):
    """正方形ピラミッド(階段リング方式)の面に rows(文字列の配列。上の行が上)を描く。
    side='S'(+z)/'N'/'E'/'W'。B=底辺半幅（半幅 h(y)=B+1-y）。rows の中心を面の中央に合わせる。skip(x,y,z)->True なら描かない"""
    H = len(rows); W = len(rows[0])
    for ri, row in enumerate(rows):
        y = y_bottom+(H-1-ri); h = B+1-y
        for ci, ch in enumerate(row):
            if ch == '.' or ch not in legend: continue
            u = ci-W//2
            if abs(u) >= h: continue
            x, z, f = {'S': (u, h, 'north'), 'N': (-u, -h, 'south'), 'E': (h, -u, 'west'), 'W': (-h, u, 'east')}[side]
            if skip and skip(x, y, z): continue
            b.put(x, y, z, legend[ch], **ST(f))

def weather_faces(b, B, rate=(0.04, 0.03, 0.02), seed=3):
    """外殻の風化：階段をスラブ/立方体/刻み石に置換してまだらにする（角セルは除外）"""
    rnd = random.Random(seed)
    for y in range(1, B+1):
        h = B+1-y
        for u in range(-h+1, h):
            for (x, z) in ((u, h), (u, -h), (h, u), (-h, u)):
                r = rnd.random()
                if r < rate[0]: b.put(x, y, z, 'sandstone_slab', **SL)
                elif r < rate[0]+rate[1]: b.put(x, y, z, 'sandstone')
                elif r < sum(rate): b.put(x, y, z, 'cut_sandstone')

def sand_drift(b, B, side, peak=8, width=14, length=16, seed=1, center=0):
    """麓に積もった砂（面に張り付く吹き溜まり）。side='W'/'N'/'E'/'S'。"""
    rnd = random.Random(seed)
    for t in range(-width, width+1):
        pk = peak*math.exp(-(t/ (width*0.55))**2)+rnd.uniform(-.6, .6)
        for d in range(-length//2, length+1):
            S = pk-0.5*abs(d)
            for y in range(1, int(S)+1):
                x, z = {'W': (-B-1-d+ 0, t+center), 'E': (B+1+d, t+center), 'N': (t+center, -B-1-d), 'S': (t+center, B+1+d)}[side]
                if (x, z) not in G: continue
                n = b.get(x, y, z)
                if n is None or 'stairs' in n or n in ('sandstone_slab',): b.put(x, y, z, 'sand')

# ---------------------------------------------------------------- スフィンクス
def _sphinx_small():
    V = {}
    def fill(us, ws, hs, blk):
        for u in us:
            for w in ws:
                for h in hs: V[(u, w, h)] = blk(u, w, h) if callable(blk) else blk
    fill(range(0, 6), (-1, 0, 1), (0, 1), lambda u, w, h: 'sandstone' if (u+w+h) % 4 else 'cut_sandstone')   # 胴
    fill(range(0, 3), (-1, 0, 1), (2,), 'cut_sandstone')                                                     # 腰
    fill((6,), (-1, 0, 1), (0, 1), 'cut_sandstone')                                                          # 胸
    fill((7, 8, 9), (-1, 1), (0,), 'smooth_sandstone')                                                       # 前足
    fill((7, 8, 9), (0,), (0,), 'cut_sandstone')
    fill((5, 6), (0,), (2, 3), 'sandstone')                                                                  # 首
    fill((5, 6), (-1, 1), (2, 3), lambda u, w, h: 'lapis_block' if h == 2 else 'gold_block')                 # 頭巾の垂れ
    fill((5, 6, 7), (-1, 0, 1), (4, 5, 6), 'gold_block')                                                     # 頭
    fill((5, 6, 7), (-1, 1), (4, 5, 6), lambda u, w, h: 'lapis_block' if (h+u) % 2 else 'gold_block')       # 縞
    fill((7,), (0,), (4, 5), lambda u, w, h: 'chiseled_sandstone' if h == 5 else 'cut_sandstone')            # 顔
    V[(7, -1, 5)] = V[(7, 1, 5)] = 'lapis_block'; V[(7, 0, 6)] = 'red_concrete'                              # 目・ウラエウス
    return V

def _sphinx_great():
    V = {}
    def fill(us, ws, hs, blk):
        for u in us:
            for w in ws:
                for h in hs: V[(u, w, h)] = blk(u, w, h) if callable(blk) else blk
    body = lambda u, w, h: 'sandstone' if (u+w+h) % 5 else 'cut_sandstone'
    fill(range(0, 7), range(-3, 4), range(0, 4), body)                         # 腰（丸い屋根）
    fill(range(0, 7), range(-2, 3), (4,), 'cut_sandstone')
    fill(range(7, 14), range(-2, 3), range(0, 4), body)                        # 背
    fill(range(14, 17), range(-3, 4), range(0, 4), body)                       # 胸
    fill(range(14, 17), range(-2, 3), (4,), 'cut_sandstone')
    for u in range(17, 23):                                                    # 前足（2本、間に隙間）
        for w in (-3, -2, 2, 3):
            V[(u, w, 0)] = 'smooth_sandstone'
            if u < 21: V[(u, w, 1)] = 'sandstone'
    fill(range(14, 17), range(-1, 2), range(5, 8), 'sandstone')                # 首
    fill(range(14, 18), (-3, -2, 2, 3), range(4, 9), lambda u, w, h: 'lapis_block' if (h+u) % 2 else 'gold_block')   # 頭巾の垂れ
    fill(range(14, 19), range(-2, 3), range(8, 13), 'gold_block')              # 頭
    fill(range(14, 19), (-2, 2), range(8, 13), lambda u, w, h: 'lapis_block' if (h+u) % 2 else 'gold_block')        # 縞
    fill((19,), range(-1, 2), range(8, 11), 'cut_sandstone')                  # 顔面（前に張り出す）
    fill((19,), (0,), (10, 11), 'chiseled_sandstone')
    for h in (8, 9): V[(18, 0, h)] = 'chiseled_sandstone'
    V[(19, -1, 10)] = V[(19, 1, 10)] = 'lapis_block'                          # 目
    V[(19, 0, 9)] = 'terracotta'                                               # 鼻
    V[(18, 0, 13)] = 'red_concrete'; V[(17, 0, 13)] = 'gold_block'            # ウラエウス
    fill(range(-1, 0), (0,), range(0, 2), 'sandstone')                         # 尾
    return V

def sphinx(b, x, y, z, face='S', size='small', plinth=True):
    """スフィンクス。face=頭の向き('N','S','E','W')。size='small'(長さ10) / 'great'(長さ23・高さ14)。y=足元（地面の上）"""
    V = _sphinx_small() if size == 'small' else _sphinx_great()
    us = [k[0] for k in V]; ws = [k[1] for k in V]
    def xz(u, w): return {'S': (x+w, z+u), 'N': (x+w, z-u), 'E': (x+u, z+w), 'W': (x-u, z+w)}[face]
    if plinth:                                                                 # 台座
        for u in range(min(us)-1, max(us)+2):
            for w in range(min(ws)-1, max(ws)+2):
                X, Z = xz(u, w); b.put(X, y-1, Z, 'red_sandstone' if (u+w) % 3 else 'smooth_red_sandstone') if (X, Z) in G else None
    for (u, w, h), blk in V.items():
        X, Z = xz(u, w); b.put(X, y+h, Z, blk)

def mini_pyramid(b, cx, cz, half, y0=1, weather=True):
    """衛星ピラミッド（階段の45°）。ギザの小ピラミッド群のように本体の脇へ"""
    rnd = random.Random(cx*7+cz)
    for k in range(half):
        h = half-k; y = y0+k
        for x in range(-h, h+1):
            for z in range(-h, h+1):
                X, Z = cx+x, cz+z
                if max(abs(x), abs(z)) < h: b.put(X, y, Z, 'sandstone'); continue
                nm = 'sandstone_stairs' if not (weather and rnd.random() < .08) else 'cut_sandstone'
                if abs(x) == h and abs(z) == h: f, sh = corner_stair(x, z); b.put(X, y, Z, nm, **ST(f, 'bottom', sh)) if 'stairs' in nm else b.put(X, y, Z, nm)
                elif abs(x) == h: b.put(X, y, Z, nm, **ST('east' if x < 0 else 'west')) if 'stairs' in nm else b.put(X, y, Z, nm)
                else: b.put(X, y, Z, nm, **ST('south' if z < 0 else 'north')) if 'stairs' in nm else b.put(X, y, Z, nm)
    b.put(cx, y0+half, cz, 'gold_block')

def pylon(b, cx, z, y0=1, wid=7, depth=3, height=16, side=1):
    """塔門の片側の塔（外側へ傾く台形）。side=±1 で左右。正面に金の太陽円盤と旗竿"""
    for k in range(height):
        inset = k//6                                                           # 6段ごとに内側が1縮む（battered）
        for dx in range(inset, wid):
            for dz in range(depth):
                x = cx+side*dx; blk = 'chiseled_sandstone' if k in (5, 11, height-1) else ('smooth_sandstone' if (dx+k) % 4 else 'cut_sandstone')
                b.put(x, y0+k, z+dz, blk)
    mid = cx+side*(wid//2)                                                     # 正面の太陽円盤
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            b.put(mid+dx, y0+8+dy, z-1, 'gold_block' if (dx, dy) != (0, 0) else 'shroomlight')
    for k in range(7): b.put(cx+side*(wid-1), y0+height+k, z+1, 'end_rod', facing='up')       # 旗竿
    for k in range(3): b.put(cx+side*(wid-1)+(-side if k else 0), y0+height+5+(k//2), z+1, 'red_concrete') if k else None
    b.put(cx+side*(wid-2), y0+height+5, z+1, 'red_concrete'); b.put(cx+side*(wid-2), y0+height+4, z+1, 'red_concrete')

# ---------------------------------------------------------------- オベリスク・柱・ヤシ
def obelisk(b, x, y, z, h=14, gold='gold_block'):
    for dx in range(-2, 3):
        for dz in range(-2, 3): b.put(x+dx, y, z+dz, 'cut_sandstone'); b.put(x+dx, y+1, z+dz, 'chiseled_sandstone') if max(abs(dx), abs(dz)) == 2 else None
    for dx in range(-1, 2):
        for dz in range(-1, 2): b.put(x+dx, y+1, z+dz, 'smooth_sandstone')
    for k in range(h):
        wdt = 1 if k < h*0.55 else 0
        for dx in range(-wdt, wdt+1):
            for dz in range(-wdt, wdt+1): b.put(x+dx, y+2+k, z+dz, 'chiseled_sandstone' if k % 4 == 3 else 'cut_sandstone')
    b.put(x, y+2+h, z, gold); b.put(x, y+3+h, z, 'lightning_rod', facing='up', powered='false', waterlogged='false')

def ruined_column(b, x, z, h=7, broken=0, fallen=None, y0=1):
    """列柱。broken=欠け段数、fallen=('x'|'z', 長さ) で倒れた柱頭ブロックを横に転がす"""
    top = y0+h-broken
    for y in range(y0, top):
        b.put(x, y, z, 'chiseled_sandstone' if y in (y0, top-1) else 'cut_sandstone')
    if fallen:
        ax, ln = fallen
        for i in range(ln): b.put(x+(i+1 if ax == 'x' else 0), y0, z+(i+1 if ax == 'z' else 0), 'cut_sandstone')
        b.put(x+(ln+1 if ax == 'x' else 0), y0, z+(ln+1 if ax == 'z' else 0), 'chiseled_sandstone')

def palm(b, x, z, h=9, seed=0):
    y0 = G[(x, z)]+1; rnd = random.Random(x*31+z*7+seed)
    dx, dz = rnd.uniform(-2.2, 2.2), rnd.uniform(-2.2, 2.2)
    top = b.tube((x, y0, z), (x+dx*.3, y0+h*.4, z+dz*.3), (x+dx*.8, y0+h*.8, z+dz*.8), (x+dx, y0+h, z+dz), 1.0, .7,
                 lambda X, Y, Z: pick([('jungle_log', 70), ('stripped_jungle_log', 30)], X, Y, Z), axis='y')
    tx, ty, tz = top
    for k in range(8):                                   # 垂れる葉
        a = k*math.pi/4
        for i in range(1, 6):
            X = round(tx+math.cos(a)*i); Z = round(tz+math.sin(a)*i); Y = round(ty+1.2-0.22*i*i*0.5)
            b.put_if_empty(X, Y, Z, 'jungle_leaves', **LEAF)
    b.put(round(tx), round(ty)+1, round(tz), 'jungle_leaves', **LEAF)

def amethyst_underside(b, bottoms, every=19, seed=2):
    """浮島の底に垂れる水晶（アメジストクラスター。弱く発光）。bottoms={(x,z): 底のy}"""
    rnd = random.Random(seed)
    for (x, z), yb in bottoms.items():
        if h3(x, 7, z) % every == 0:
            nm = rnd.choice(['amethyst_cluster', 'large_amethyst_bud', 'amethyst_cluster'])
            b.put(x, yb-1, z, nm, facing='down', waterlogged='false')
            if rnd.random() < .5: b.put(x, yb, z, 'amethyst_block')

# ---------------------------------------------------------------- 幻想
def floating_sun_disc(b, cx, cy, cz, r=5.3, plane='xy'):
    """宙に浮かぶ太陽円盤（金の外輪＋発光する橙の内輪＋シーランタンの核）。plane='xy'なら南北から見える"""
    for dx in range(-int(r)-1, int(r)+2):
        for dy in range(-int(r)-1, int(r)+2):
            d = math.hypot(dx, dy)
            if d > r: continue
            blk = 'gold_block' if d > r-1.3 else ('shroomlight' if d > 2.4 else 'sea_lantern')
            for t in (0, -1): b.put(cx+dx, cy+dy, cz+t, blk) if plane == 'xy' else b.put(cx+t, cy+dy, cz+dx, blk)

def floating_ruins(b, cx, cz, y0, y1, rmin=13, rmax=22, n=7, seed=4):
    """頂上のまわりに浮かぶ遺構の欠片（砂岩の塊＋金の飾り＋吊り魂灯）"""
    rnd = random.Random(seed)
    for k in range(n):
        a = rnd.uniform(0, math.tau); r = rnd.uniform(rmin, rmax); x, z = cx+r*math.cos(a), cz+r*math.sin(a); y = rnd.uniform(y0, y1)
        s = rnd.uniform(1.6, 3.0)
        b.shell(x, y, z, s*1.3, s*.8, s*1.3, lambda X, Y, Z: pick([('sandstone', 50), ('cut_sandstone', 30), ('smooth_sandstone', 20)], X, Y, Z), inner=0.0, lumpy=.35)
        for i in range(rnd.randint(2, 4)): b.put(round(x+rnd.uniform(-1, 1)), round(y-s*.8-i), round(z+rnd.uniform(-1, 1)), 'sandstone')
        b.put(round(x), round(y+s*.8)+1, round(z), 'gold_block'); b.put(round(x), round(y-s*.8)-3, round(z), 'soul_lantern', hanging='true', waterlogged='false')

def glow_vein(b, B, side, z0, y_from, y_to, wobble=3, seed=1, skip=None, deep=2):
    """面を走る光の亀裂（発光ブロックを外殻から2段奥まで埋める）。skip でダンジョン近傍を避ける"""
    rnd = random.Random(seed); zc = z0
    for y in range(y_from, y_to+1):
        zc += rnd.choice([-1, 0, 0, 1]); zc = max(z0-wobble, min(z0+wobble, zc)); h = B+1-y
        for dz in (0, 1):
            for k in range(deep):
                u = zc+dz
                x, z = {'E': (h-k, u), 'W': (-h+k, u), 'S': (u, h-k), 'N': (u, -h+k)}[side]
                if skip and skip(x, y, z): continue
                b.put(x, y, z, 'shroomlight' if (y+dz+k) % 3 else 'gold_block')


# ---------------------------------------------------------------- 儀式・遺構（ロマン／幻想）
def stone_circle(b, cx, cz, r=9, n=8, h=6, seed=3):
    """星の環状列石：n本の立石（頂に紫水晶）と中央の祭壇、地面を走る発光の放射線。夜に魔法陣のように光る"""
    rnd = random.Random(seed)
    pts = []
    for k in range(n):
        a = k*math.tau/n; x, z = round(cx+r*math.cos(a)), round(cz+r*math.sin(a)); pts.append((x, z))
        if (x, z) not in G: continue
        y0 = G[(x, z)]+1; hh = h+rnd.randint(-1, 1)
        for y in range(y0, y0+hh): b.put(x, y, z, 'chiseled_sandstone' if y in (y0, y0+hh-1) else 'cut_sandstone')
        b.put(x, y0+hh, z, 'amethyst_block'); b.put(x, y0+hh+1, z, 'amethyst_cluster', facing='up', waterlogged='false')
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)): b.put_if_empty(x+dx, y0, z+dz, 'amethyst_cluster', facing='up' if False else ('east' if dx > 0 else 'west' if dx < 0 else 'up'), waterlogged='false') if rnd.random() < .5 else None
        for t in range(1, r):                                               # 中心へ向かう発光の線
            X, Z = round(cx+t*math.cos(a)), round(cz+t*math.sin(a))
            if (X, Z) in G and t % 2 == 0: b.put(X, G[(X, Z)], Z, 'shroomlight' if t % 4 == 0 else 'sea_lantern')
    if (cx, cz) in G:
        y0 = G[(cx, cz)]
        for dx in range(-2, 3):
            for dz in range(-2, 3): b.put(cx+dx, y0, cz+dz, 'lapis_block' if max(abs(dx), abs(dz)) == 2 else 'smooth_sandstone'); b.rm(cx+dx, y0+1, cz+dz)
        b.put(cx, y0+1, cz, 'cut_sandstone'); b.put(cx, y0+2, cz, 'soul_campfire', facing='north', lit='true', signal_fire='false', waterlogged='false')
    return pts

def ruin_arch(b, x, z, axis='x', w=5, h=7, gap_seed=0):
    """崩れかけたアーチ（2本の柱＋欠けたまぐさ）。axis='x' なら x 方向に開く"""
    rnd = random.Random(gap_seed+x*3+z)
    if (x, z) not in G: return
    y0 = G[(x, z)]+1
    for s in (0, w):
        px, pz = (x+s, z) if axis == 'x' else (x, z+s)
        hh = h-rnd.randint(0, 3)
        for y in range(y0, y0+hh): b.put(px, y, pz, 'chiseled_sandstone' if y in (y0, y0+hh-1) else 'cut_sandstone')
    for i in range(1, w):
        if rnd.random() < .6:
            px, pz = (x+i, z) if axis == 'x' else (x, z+i)
            b.put(px, y0+h, pz, 'cut_sandstone_slab', **SL)
            if rnd.random() < .5: b.put(px, y0+h-1, pz, 'chiseled_sandstone')
    if rnd.random() < .7:                                                   # 足元の瓦礫
        for _ in range(4): b.put_if_empty(x+rnd.randint(-2, w+2) if axis == 'x' else x+rnd.randint(-2, 2), y0, z+rnd.randint(-2, 2) if axis == 'x' else z+rnd.randint(-2, w+2), 'cut_sandstone')
