"""和風の小物と樹木（石灯籠・鳥居・竹・松・桜）。arch_helpers の G（地表）を使う。"""
from arch_helpers import *

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

