"""くさび形の大型宇宙戦艦（オリジナル設計）。1ブロック≒5m（全長320ブロック≒1.6km級）。+z=艦首、-z=艦尾(エンジン)、y=0 が艦底。
外殻のみ（内部は空洞）。艦尾寄りに艦橋塔、艦底に格納庫。"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from builder import *
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)
b = Build()
L, HW0 = 320, 100
hw = lambda z: HW0*(1-z/L)
tb = lambda z: 5+13*(1-z/L)

# ---- 列ごとの上面・下面の高さ
TOP, BOT = {}, {}
for z in range(0, L):
    w = hw(z)
    for x in range(-int(w), int(w)+1):
        d = w-abs(x); ax = abs(x)
        yt = max(1, round(tb(z)*min(1, d/12)))
        if ax < 0.62*w and 10 <= z <= 0.9*L: yt += 5          # 第1段
        if ax < 0.36*w and 10 <= z <= 0.8*L: yt += 5          # 第2段
        if ax < 0.18*w and 40 <= z <= 110: yt += 4            # 塔の台座
        if ax <= 2 and 15 <= z <= 285 and not 55 <= z <= 95: yt -= 4   # 中央の溝
        kw = max(1, 0.14*w); yb = -round(5*(1-ax/kw)) if ax < kw and z > 25 else 0
        TOP[(x, z)] = max(yt, yb+1); BOT[(x, z)] = yb

LIGHT = ['light_gray_concrete']*9+['smooth_stone']
def top_mat(x, z): return 'gray_concrete' if z % 16 == 0 else LIGHT[h3(x//5, 0, z//5) % len(LIGHT)]
def belly_mat(x, z): return 'black_concrete' if z % 16 == 0 else ('gray_concrete' if h3(x//4, 1, z//4) % 3 else 'light_gray_concrete')

for (x, z), yt in TOP.items():
    yb = BOT[(x, z)]
    b.put(x, yt, z, top_mat(x, z)); b.put(x, yb, z, belly_mat(x, z))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (x+dx, z+dz)
        ynt = TOP.get(n, yb-1); ynb = BOT.get(n, yt+1)
        for y in range(ynt+1, yt):                                   # 上面の段差の側壁（窓の灯り付き）
            if y > yb: b.put(x, y, z, 'sea_lantern' if (z+x) % 7 == 0 and (y-ynt) == 2 and yt-ynt >= 4 else 'gray_concrete')
        for y in range(yb+1, ynb):                                   # 下面（キール）の側壁
            if y < yt: b.put(x, y, z, 'gray_concrete')
for x in range(-HW0, HW0+1):                                           # 艦尾の壁
    if (x, 0) in TOP:
        for y in range(BOT[(x, 0)], TOP[(x, 0)]+1):
            b.put(x, y, 0, 'sea_lantern' if (x % 9 == 0 and y % 4 == 2) else ('light_gray_concrete' if y % 4 == 0 else 'gray_concrete'))

# ---- 砲塔の小突起
for (x, z), yt in TOP.items():
    if x % 11 == 0 and z % 13 == 0 and 20 < z < 300 and abs(x) > 3 and hw(z)-abs(x) > 6 and TOP.get((x+1, z)) == yt and TOP.get((x-1, z)) == yt:
        b.box(x-1, yt+1, z-1, x+1, yt+1, z+1, 'gray_concrete'); b.put(x, yt+2, z, 'smooth_stone'); b.put(x, yt+2, z+1, 'iron_bars', **FN)
# ---- 縁の航行灯
for (x, z), yt in TOP.items():
    if hw(z)-abs(x) < 1.5 and z % 9 == 0: b.put(x, yt+1, z, 'sea_lantern')

# ---- 格納庫（艦底の開口。壁と天井、照明）
b.clear(-12, -5, 210, 12, 0, 245)
for x in range(-12, 13):
    for z in range(210, 246):
        b.put(x, 9, z, 'gray_concrete')                                        # 天井
        for y in range(0, 9):
            if x in (-12, 12) or z in (210, 245): b.put(x, y, z, 'gray_concrete')
for z in range(212, 245, 4):
    for x in (-9, 0, 9): b.put(x, 8, z, 'sea_lantern')
for y in (2, 5):
    for z in range(212, 245, 4): b.put(-11, y, z, 'sea_lantern'); b.put(11, y, z, 'sea_lantern')
for z in range(210, 246, 5):
    for x in (-12, 12): b.put(x, 0, z, 'yellow_concrete')                    # 縁取りの警戒色

# ---- 艦橋塔
ty = TOP[(0, 70)]-4+4          # 台座上面
def sphere(cx, cy, cz, r, n):
    for x in range(-r, r+1):
        for y in range(-r, r+1):
            for z in range(-r, r+1):
                if r-1 < (x*x+y*y+z*z)**.5 <= r+.3: b.put(cx+x, cy+y, cz+z, n)
base = TOP[(0, 70)]
for h in range(1, 31):                                          # 首：先細りの柱
    wd = 7-int(h/9); 
    for x in range(-wd, wd+1):
        for z in range(62, 80):
            if abs(x) == wd or z in (62, 79) or h % 6 == 0: b.put(x, base+h, z, 'light_gray_concrete' if h % 6 else 'gray_concrete')
            if (abs(x) == wd and h % 3 == 1 and z % 4 == 0): b.put(x, base+h, z, 'sea_lantern')
ytop = base+30
for k, (wd, z0, z1) in enumerate(((24, 58, 88), (22, 58, 87), (20, 59, 86), (18, 60, 85))):    # 艦橋の頭部（段状）
    for x in range(-wd, wd+1):
        for z in range(z0, z1+1):
            for y in (ytop+k*2, ytop+k*2+1):
                if abs(x) == wd or z in (z0, z1) or y == ytop+k*2+1: b.put(x, y, z, 'light_gray_concrete' if (x+z) % 6 else 'gray_concrete')
for x in range(-21, 22):                                        # 前面の窓列
    for y in (ytop+2, ytop+3): b.put(x, y, 87, 'light_blue_stained_glass' if x % 5 else 'gray_concrete')
for sx in (-1, 1): sphere(sx*14, ytop+11, 66, 5, 'white_concrete'); b.box(sx*14-5, ytop+8, 66-5, sx*14+5, ytop+8, 66+5, 'iron_block') if False else None
for y in range(ytop+9, ytop+22): b.put(0, y, 70, 'iron_bars', **FN)           # アンテナ
b.disk(0, 70, 4, ytop+22, 'light_gray_concrete'); b.put(0, ytop+23, 70, 'sea_lantern')

# ---- エンジン
def engine(cx, cy, r, ln):
    for z in range(-ln, 0):
        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                d = (dx*dx+dy*dy)**.5
                if d <= r and (d > r-1.2 or z in (-ln, -1)): b.put(cx+dx, cy+dy, z, 'black_concrete' if z <= -ln+1 else 'gray_concrete')
    for dx in range(-r, r+1):
        for dy in range(-r, r+1):
            d = (dx*dx+dy*dy)**.5
            if d <= r-2: b.put(cx+dx, cy+dy, -ln+1, 'sea_lantern')
    for k in range(1, 15):                                      # 噴射光の尾
        rr = max(1, r-1.2-k*0.5)
        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                if (dx*dx+dy*dy)**.5 <= rr: b.put(cx+dx, cy+dy, -ln+1-k, 'sea_lantern' if (k <= 2 and (dx*dx+dy*dy)**.5 <= rr-1.5) else 'light_blue_stained_glass')
for cx in (-42, 0, 42): engine(cx, 9, 8, 9)
for cx in (-70, 70): engine(cx, 8, 4, 6)

# ---- 保存
mn = [min(k[i] for k in b.B) for i in range(3)]; mx = [max(k[i] for k in b.B) for i in range(3)]
print('size', [mx[i]-mn[i]+1 for i in range(3)], 'min', mn)
b.save(os.path.join(OUT, 'Wedge_Warship_5m.bp'), 'くさび形大型戦艦 (1block≒5m)', tags=['space', 'warship', 'original'])
