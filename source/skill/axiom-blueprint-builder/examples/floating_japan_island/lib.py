"""和風の島用ヘルパー。屋根・樹木・鳥居・灯籠・池・道。"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
from builder import *

G = {}   # (x,z) -> 地表の y
def gy(x, z): return G.get((int(x), int(z)))

# ---------------------------------------------------------------- 屋根
SLAB_T = [('deepslate_tile_slab', 70), ('deepslate_brick_slab', 20), ('polished_deepslate_slab', 10)]
STAIR_T = [('deepslate_tile_stairs', 68), ('deepslate_brick_stairs', 22), ('polished_deepslate_stairs', 10)]

def corner_stair(dx, dz):
    """寄棟の角（外角）。高い1/4が内側（中心側）を向くように facing/shape を選ぶ"""
    if dx < 0: return 'east', ('outer_right' if dz < 0 else 'outer_left')
    return 'west', ('outer_left' if dz < 0 else 'outer_right')

def _roof_cell(b, x, z, y0, r, ridge, f, sh, fill_r, under, fill_to=None):
    top = y0 + r // 2 + 1
    if ridge or r % 2:
        b.put(x, top, z, pick(SLAB_T, x, top, z), **SL); lo = top
    else:
        lo = y0 + r // 2
        b.put(x, lo, z, pick(STAIR_T, x, lo, z), **ST(f, 'bottom', sh))
    if r <= fill_r:
        for yy in range(y0, lo): b.put(x, yy, z, under)

def tile_roof(b, cx, cz, y0, hx, hz, rmax=99, fill_r=3, under='dark_oak_planks', up=True, lant=True, hcap=99):
    """寄棟/宝形。傾斜は1:2（階段→スラブ→階段…）。外縁 r=0 から内へ。隅は外角階段で反りを足す"""
    rr = min(hx, hz)
    for dx in range(-hx, hx+1):
        for dz in range(-hz, hz+1):
            ex, ez = hx-abs(dx), hz-abs(dz); r = min(ex, ez)
            if r > rmax: continue
            if r > hcap:                       # 平らな帯（スラブ）
                x, z = cx+dx, cz+dz; top = y0+hcap//2+1
                b.put(x, top, z, pick(SLAB_T, x, top, z), **SL)
                for yy in range(y0, top): b.put(x, yy, z, under)
                continue
            if ex == ez: f, sh = corner_stair(dx, dz)
            elif ex < ez: f, sh = ('east' if dx < 0 else 'west'), 'straight'
            else: f, sh = ('south' if dz < 0 else 'north'), 'straight'
            _roof_cell(b, cx+dx, cz+dz, y0, r, r == rr, f, sh, fill_r, under)
    if up:
        for sx in (-1, 1):
            for sz in (-1, 1):
                X, Z = cx+sx*hx, cz+sz*hz
                b.put(X, y0+1, Z, 'deepslate_tile_slab', **SL)
                if lant:
                    b.put(X, y0-1, Z, 'iron_chain', axis='y', waterlogged='false')
                    b.put(X, y0-2, Z, 'lantern', hanging='true', waterlogged='false')

def gable_roof(b, cx, cz, y0, hw, a0, a1, axis='x', end_mat=None, end_at=None, fill_r=3, under='dark_oak_planks'):
    """切妻。axis='x' なら棟が x 方向に a0..a1、断面は z 方向（中心 cz、半幅 hw）。end_at の面に妻壁(end_mat)を詰める"""
    for a in range(a0, a1+1):
        for d in range(-hw, hw+1):
            r = hw-abs(d)
            if axis == 'x': x, z, f = a, cz+d, ('south' if d < 0 else 'north')
            else: x, z, f = cx+d, a, ('east' if d < 0 else 'west')
            _roof_cell(b, x, z, y0, r, r == hw, f, 'straight', fill_r, under)
            if end_mat and a == end_at:
                top = y0 + r // 2 + (1 if (r == hw or r % 2) else 0)
                for yy in range(y0, top): b.put(x, yy, z, end_mat)

# ---------------------------------------------------------------- 小物
def toro(b, x, y, z, tall=1):
    """石灯籠。y は置く段（地表の1つ上）"""
    b.put(x, y, z, 'stone_bricks')
    for k in range(tall): b.put(x, y+1+k, z, 'stone_brick_wall', **WALL)
    t = y+1+tall
    b.put(x, t, z, 'lantern', hanging='false', waterlogged='false')
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)):
        b.put(x+dx, t+1, z+dz, 'stone_brick_slab', **SL)
    b.put(x, t+2, z, 'stone_brick_wall', **WALL)

def lantern_hang(b, x, y, z, n=1):
    for k in range(n): b.put(x, y-k, z, 'iron_chain', axis='y', waterlogged='false')
    b.put(x, y-n, z, 'lantern', hanging='true', waterlogged='false')

def torii(b, x, y, z, axis='x', w=3, h=8, mat='red_concrete', cap='black_concrete'):
    """鳥居。axis='x' なら x 方向に開く（柱が x±w）。y=柱の足元"""
    def P(a, yy, off=0):
        return (x+a, yy, z+off) if axis == 'x' else (x+off, yy, z+a)
    for s in (-w, w):
        for yy in range(y, y+h): b.put(*P(s, yy), mat)
        b.put(*P(s, y), 'black_concrete')
    for a in range(-w, w+1): b.put(*P(a, y+h-3), mat)                 # 貫
    for a in range(-w-1, w+2): b.put(*P(a, y+h-1), mat)               # 島木
    for a in range(-w-2, w+3): b.put(*P(a, y+h), cap)                  # 笠木
    for a in (-w-3, w+3): b.put(*P(a, y+h+1), 'black_concrete_powder' if False else 'deepslate_tile_slab', **SL)   # 反り上がった両端
    for a in range(-w-1, w+2): b.put(*P(a, y+h+1), 'deepslate_tile_slab', **SL)
    b.put(*P(0, y+h-2), 'dark_oak_planks')                              # 額束

def bamboo(b, x, y, z, h):
    for k in range(h):
        top = h-1-k
        lv = 'large' if top <= 1 else ('small' if top == 2 else 'none')
        b.put_if_empty(x, y+k, z, 'bamboo', age='1' if k >= h-3 else '0', leaves=lv, stage='0')

def grove(b, cx, cz, rx, rz, n, seed=1, hmin=6, hmax=13):
    rnd = random.Random(seed)
    for _ in range(n):
        x = int(cx+rnd.uniform(-rx, rx)); z = int(cz+rnd.uniform(-rz, rz))
        if gy(x, z) is None: continue
        y = G[(x, z)]
        if b.get(x, y, z) not in ('grass_block', 'moss_block', 'podzol'): continue
        bamboo(b, x, y+1, z, rnd.randint(hmin, hmax))

LEAF_PINE = lambda x, y, z: pick([('dark_oak_leaves', 50), ('spruce_leaves', 35), ('azalea_leaves', 15)], x, y, z)
LEAF_OAK = lambda x, y, z: pick([('oak_leaves', 45), ('azalea_leaves', 25), ('flowering_azalea_leaves', 8), ('jungle_leaves', 22)], x, y, z)

def pine(b, x, z, h=9, pads=4, wide=1.0):
    """松（黒松風）：ねじれた幹＋雲形の葉のかたまり"""
    y = G[(x, z)]+1; rnd = random.Random(x*977+z*31)
    p = lambda k: (x+rnd.uniform(-k, k), 0, z+rnd.uniform(-k, k))
    a, c, d = p(2.5), p(3), p(2.5)
    trunk = lambda X, Y, Z: pick([('dark_oak_log', 55), ('spruce_log', 35), ('stripped_dark_oak_log', 10)], X, Y, Z)
    end = b.tube((x, y, z), (a[0], y+h*.3, a[2]), (c[0], y+h*.65, c[2]), (d[0], y+h, d[2]), 1.5, 0.8, trunk, axis='y')
    for i in range(pads):
        t = .42+.58*i/max(1, pads-1)
        px = x+(end[0]-x)*t+rnd.uniform(-3, 3)*wide; pz = z+(end[2]-z)*t+rnd.uniform(-3, 3)*wide
        py = y+h*t+rnd.uniform(-.5, 1)
        b.tube((x+(end[0]-x)*t, y+h*t-1, z+(end[2]-z)*t), (px, py-1, pz), (px, py-1, pz), (px, py-1, pz), .8, .7, trunk, axis='y')
        rx = (4.2-1.0*(i/ max(1, pads-1)))*wide
        b.shell(px, py+1, pz, rx, 1.9, rx, LEAF_PINE, inner=0.0, lumpy=.35, **LEAF)

def tree(b, x, z, h=6, r=3.4):
    y = G[(x, z)]+1
    for k in range(h): b.put(x, y+k, z, 'oak_log', axis='y')
    b.shell(x, y+h, z, r, r*.8, r, LEAF_OAK, inner=.3, lumpy=.3, **LEAF)

def sakura(b, x, z, h=10, spr=7.0, seed=0):
    """枝垂れ桜：太めの幹と枝、殻の樹冠、垂れ下がる花房、散った花びら"""
    y0 = G[(x, z)]+1; rnd = random.Random(x*131+z*7+seed)
    log = lambda X, Y, Z: pick([('cherry_log', 78), ('stripped_cherry_log', 8), ('cherry_wood', 14)], X, Y, Z)
    q = lambda k: rnd.uniform(-k, k)
    top = b.tube((x, y0-1, z), (x+q(2), y0+h*.35, z+q(2)), (x+q(3), y0+h*.7, z+q(3)), (x+q(2.5), y0+h, z+q(2.5)), 1.7, 1.0, log, axis='y')
    leaves = []
    lobes = [(0, 2, 0, spr, spr*.5)] + [(spr*.6*math.cos(a), 0, spr*.6*math.sin(a), spr*.62, spr*.38) for a in (0.4, 1.97, 3.54, 5.11)]
    for ox, oy, oz, rx, ry in lobes:
        cx, cy, cz = top[0]+ox, top[1]+oy, top[2]+oz
        leaves += b.shell(cx, cy, cz, rx, ry, rx, lambda X, Y, Z: 'cherry_leaves', inner=.52, lumpy=.25, **LEAF)
        # 太い枝
        if ox or oz: b.tube(top, (top[0]+ox*.3, top[1]-1, top[2]+oz*.3), (cx-ox*.2, cy-2, cz-oz*.2), (cx, cy-1, cz), 1.0, .6, log, axis='y')
    ls = set(leaves)
    for (X, Y, Z) in leaves:
        if (X, Y-1, Z) not in ls and h3(X, Y, Z) % 4 == 0:
            for k in range(1, 2+h3(Z, X, Y) % 3):
                if b.empty(X, Y-k, Z): b.put(X, Y-k, Z, 'cherry_leaves', **LEAF)
    R = int(spr)+2
    for dx in range(-R, R+1):
        for dz in range(-R, R+1):
            X, Z = x+dx, z+dz
            if (X, Z) in G and b.get(X, G[(X, Z)], Z) in ('grass_block', 'moss_block', 'podzol') and h3(X, 5, Z) % 6 == 0 and math.hypot(dx, dz) < spr:
                b.put_if_empty(X, G[(X, Z)]+1, Z, 'pink_petals', facing='north', flower_amount=str(1+h3(X, 2, Z) % 4))
    return top

# ---------------------------------------------------------------- 水・道
def _near(pts, x, z):
    best = 1e9
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        dx, dz = bx-ax, bz-az; L = dx*dx+dz*dz or 1
        t = max(0, min(1, ((x-ax)*dx+(z-az)*dz)/L))
        best = min(best, math.hypot(x-(ax+t*dx), z-(az+t*dz)))
    return best

def lay_path(b, pts, w=3.0, extra=None):
    mix = [('andesite', 34), ('stone', 20), ('polished_andesite', 18), ('gravel', 12), ('cobblestone', 8), ('tuff', 8)]
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    for x in range(int(min(xs)-w-2), int(max(xs)+w+3)):
        for z in range(int(min(zs)-w-2), int(max(zs)+w+3)):
            if (x, z) not in G: continue
            d = _near(pts, x, z)
            if d <= w/2 + 0.35*noise(x, 1, z, 3.0):
                y = G[(x, z)]
                b.put(x, y, z, pick(mix, x, y, z)); b.rm(x, y+1, z)

def carve_water(b, cells, rim=True):
    cs = set(cells)
    for (x, z) in cs:
        y = G[(x, z)]
        b.put(x, y, z, 'water', level='0'); b.put(x, y-1, z, 'water', level='0'); b.put(x, y-2, z, pick([('clay', 50), ('gravel', 30), ('dirt', 20)], x, y, z))
        b.rm(x, y+1, z)
    if rim:
        for (x, z) in cs:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                X, Z = x+dx, z+dz
                if (X, Z) in cs or (X, Z) not in G: continue
                y = G[(X, Z)]
                if b.get(X, y, Z) in ('grass_block', 'moss_block', 'podzol', 'dirt'):
                    b.put(X, y, Z, pick([('mossy_cobblestone', 30), ('stone', 20), ('cobblestone', 15), ('moss_block', 20), ('andesite', 15)], X, y, Z))
    return cs

def stream_cells(pts, w, region=None):
    out = []
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    for x in range(int(min(xs)-w-2), int(max(xs)+w+3)):
        for z in range(int(min(zs)-w-2), int(max(zs)+w+3)):
            if (x, z) in G and _near(pts, x, z) <= w/2 + 0.3*noise(x, 2, z, 2.5): out.append((x, z))
    return out

def pond_cells(cx, cz, rx, rz):
    return [(x, z) for x in range(int(cx-rx-2), int(cx+rx+3)) for z in range(int(cz-rz-2), int(cz+rz+3))
            if (x, z) in G and ((x-cx)/rx)**2+((z-cz)/rz)**2+0.25*noise(x, 4, z, 2.5) <= 1]

def fence_line(b, pts, y, mat='dark_oak_fence', post_every=0):
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        n = int(max(abs(bx-ax), abs(bz-az)))
        for i in range(n+1):
            x = round(ax+(bx-ax)*i/max(1, n)); z = round(az+(bz-az)*i/max(1, n))
            yy = G[(x, z)]+1 if y is None and (x, z) in G else y
            if yy is None: continue
            b.put_if_empty(x, yy, z, mat, **FN)

# ---------------------------------------------------------------- 接続状態の自動補正
SOLIDISH = ('planks', 'log', 'wood', 'stone', 'brick', 'concrete', 'terracotta', 'wool', 'deepslate', 'quartz', 'andesite', 'granite', 'diorite',
            'tuff', 'dirt', 'grass_block', 'sandstone', 'gold_block', 'mud', 'moss_block', 'hay', 'barrel', 'bookshelf', 'leaves')
NOTSOLID = ('slab', 'stairs', 'fence', 'wall', 'pane', 'bars', 'door')
def fix_connections(b):
    D = {'east': (1, 0), 'west': (-1, 0), 'north': (0, -1), 'south': (0, 1)}
    solid = lambda n: any(k in n for k in SOLIDISH) and not any(k in n for k in NOTSOLID)
    for (x, y, z), (n, p) in list(b.B.items()):
        base = n[10:]
        kind = None
        if base.endswith('_fence'): kind = 'fence'
        elif base.endswith('_pane') or base == 'iron_bars': kind = 'pane'
        elif base.endswith('_wall') and 'banner' not in base: kind = 'wall'
        if not kind: continue
        props = dict(p)
        for d, (dx, dz) in D.items():
            nb = b.get(x+dx, y, z+dz)
            ok = bool(nb) and (nb == base or solid(nb) or (kind == 'pane' and (nb.endswith('_pane') or nb == 'iron_bars')) or (kind == 'wall' and nb.endswith('_wall')))
            props[d] = ('low' if ok else 'none') if kind == 'wall' else ('true' if ok else 'false')
        b.B[(x, y, z)] = (n, tuple(sorted(props.items())))
