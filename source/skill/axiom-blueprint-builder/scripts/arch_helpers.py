"""汎用の建築ヘルパー（builder.Build と併用）。
- tile_roof / gable_roof : 1:2 勾配（階段→スラブ→階段…）の寄棟・切妻。角は外角階段(outer)で反りを付ける。hcap で「軒先だけ段差、内側は平らな帯」にできる。
- fix_connections       : フェンス/ガラス板/鉄格子/壁の east/west/north/south を隣接から自動補正（書き出し直前に1回呼ぶ）。
- lay_path / carve_water / stream_cells / pond_cells / fence_line : 地表(G)に沿った道・水・柵。terrain 生成時に G[(x,z)]=地表y を登録しておく。
使い方: `from arch_helpers import *`（scripts を sys.path に入れる）。屋根素材は SLAB_T / STAIR_T を書き換えて変える。
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from builder import *

G = {}   # (x,z) -> 地表の y（terrain 生成側で登録する）
def gy(x, z): return G.get((int(x), int(z)))

# ---------------------------------------------------------------- 屋根
# 屋根素材は下の2つのリストを書き換えて変える（例: SLAB_T[:] = [('spruce_slab',100)]; STAIR_T[:] = [('spruce_stairs',100)]）
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


# ---------------------------------------------------------------- 浮島（縁・底・小島）
BANDS_MESA = ['sandstone', 'orange_terracotta', 'sandstone', 'yellow_terracotta', 'red_sandstone', 'white_terracotta', 'sandstone', 'terracotta', 'brown_terracotta']

def band(x, y, z, bands=None, scale=2):
    """縞状の地層（メサ風）。y と ノイズで縞を波打たせる"""
    bands = bands or BANDS_MESA
    return bands[((y+int(3*noise(x, 0, z, 10.0)))//scale) % len(bands)]

def floating_islet(b, cx, cy, cz, r, top=None, bands=None, seed=0, register=True, taper=1.25):
    """小さな浮島：円錐状に細る底＋縞模様の地層＋最下層は砂にしない（重力ブロックが落ちないため）。cy=地表の y。
    G に地表を登録するので palm()/ruined_column()/ruin_arch() 等をそのまま置ける。戻り値: [(x,z)]"""
    top = top or [('sand', 70), ('sandstone', 30)]
    cells = []
    for dx in range(-r-3, r+4):
        for dz in range(-r-3, r+4):
            d = math.hypot(dx, dz); rr = r*(1+0.2*noise(cx+dx*0.9, cy, cz+dz*0.9, 2.4))
            if d > rr: continue
            t = 1-d/rr; x, z = cx+dx, cz+dz
            depth = int(1.5+taper*r*(t**0.8)+1.2*(noise(x, cy, z, 1.8)+1))      # 先端が針にならない丸い鉢型
            for k in range(depth+1):
                y = cy-k; bottom = depth-k          # bottom=0 が最下層
                if k == 0: nm = pick(top, x, y, z)
                elif k == 1 and bottom >= 2: nm = 'sand' if h3(x, y, z) % 2 else 'sandstone'
                else: nm = band(x, y, z, bands)
                b.put(x, y, z, nm)
            if register: G[(x, z)] = cy
            cells.append((x, z))
    return cells
