"""浮島の地形：ブロブの合成 → 草地/土/岩 → 縁の葉と蔓 → 底の鍾乳"""
from lib import *

# (cx, cz, rx, rz, 最大の深さ)
BLOBS = [(-36,-10,30,24,28), (-56,4,11,11,16), (-1,-9,10,6,7), (28,-16,26,19,16),
         (-18,11,8,7,9), (-8,25,16,13,14), (31,4,6,9,8), (35,28,19,15,14),
         (48,-12,11,15,11),  # 鳥居・祠の張り出し
         (-14,4,8,7,8),      # 太鼓橋の足元
         (-9,-3,8,7,9)]     # 主島と社殿島をつなぐ首
MOUNDS = [(-58,3,7,3), (-47,-26,6,2), (14,-31,5,2), (52,-29,5,2), (-30,10,5,1)]
FLATS = [(-56,-29,-20,4,0),      # 五重塔
         (11,-33,37,-11,0),      # 社殿
         (-17,15,2,33,0),        # 東屋
         (23,18,49,38,0),        # 蔵
         (-24,-25,-15,-15,2),    # 小堂の丘
         (45,-9,53,1,0)]         # 祠

def height(x, z):
    for x0, z0, x1, z1, l in FLATS:
        if x0 <= x <= x1 and z0 <= z <= z1: return l
    h = sum(hh*math.exp(-((x-cx)**2+(z-cz)**2)/(r*r)) for cx, cz, r, hh in MOUNDS)
    return int(round(min(h, 3.2)))

def field(x, z):
    best, md = -9, 10
    for cx, cz, rx, rz, m in BLOBS:
        v = 1-(((x-cx)/rx)**2+((z-cz)/rz)**2)
        if v > best: best, md = v, m
    return best+0.10*noise(x, 0, z, 5.0)+0.05*noise(x*1.9, 3, z*1.9, 2.2), md

ROCK = [('stone', 32), ('andesite', 16), ('tuff', 16), ('cobblestone', 10), ('mossy_cobblestone', 9), ('deepslate', 8), ('cracked_stone_bricks', 3), ('gravel', 3), ('mossy_stone_bricks', 3)]
ROCK_DEEP = [('stone', 24), ('andesite', 12), ('tuff', 20), ('deepslate', 28), ('cobblestone', 8), ('polished_deepslate', 4), ('cobbled_deepslate', 4)]
DIRT = [('dirt', 70), ('coarse_dirt', 20), ('rooted_dirt', 10)]
TOPS = [('grass_block', 86), ('moss_block', 6), ('podzol', 8)]
EDGE_LEAF = [('azalea_leaves', 35), ('oak_leaves', 30), ('flowering_azalea_leaves', 10), ('jungle_leaves', 25)]

def terrain(b):
    for x in range(-72, 64):
        for z in range(-40, 46):
            v, md = field(x, z)
            if v <= 0: continue
            top = height(x, z)
            depth = int(md*1.2*(v**0.62) + 2.5*(noise(x, 5, z, 2.6)+1) + (2 if h3(x, 0, z) % 9 == 0 and v < .5 else 0)) + 1
            G[(x, z)] = top
            edge = v < 0.17
            for y in range(-depth, top+1):
                if y == top:
                    n = pick(TOPS, x, y, z)
                    if n == 'moss_block': b.put(x, y, z, n)
                    else: b.put(x, y, z, n, snowy='false')
                elif y >= top-3: b.put(x, y, z, pick(DIRT, x, y, z))
                else:
                    deep = y < -9
                    n = pick(ROCK_DEEP if deep else ROCK, x, y, z)
                    if y > -8 and noise(x, y, z, 3.0) > .3: n = 'moss_block' if h3(x, y, z) % 3 == 0 else 'mossy_cobblestone'
                    b.put(x, y, z, n)
                if edge and y >= top-3 and h3(x, y, z) % 10 < 7:
                    b.put(x, y, z, pick(EDGE_LEAF, x, y, z), **LEAF)
            if v < 0.6 and h3(x, 9, z) % 17 == 0:                       # 底の鍾乳
                for k in range(1, 3+h3(z, x, 1) % 4): b.put(x, -depth-k, z, pick(ROCK_DEEP, x, -depth-k, z))
                depth += 3
            if v < 0.22 and h3(x, 3, z) % 7 == 0: b.hanging(x, -depth, z, 2+h3(z, 7, x) % 4, 'cave')
            elif v < 0.5 and h3(x, 8, z) % 23 == 0: b.hanging(x, -depth, z, 2+h3(z, 6, x) % 4, 'cave')
            if edge and h3(x, 4, z) % 6 == 0 and top == 0:              # 縁の低木
                b.shell(x, 1, z, 1.7, 1.2, 1.7, lambda X, Y, Z: pick(EDGE_LEAF, X, Y, Z), inner=0.0, lumpy=.3, **LEAF)
