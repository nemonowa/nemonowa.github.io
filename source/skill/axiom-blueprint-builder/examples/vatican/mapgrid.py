"""バチカン市国の地図（ユーザー提供の画像）を 1m 格子の区分に変換する。
区分: out(国外) / ground(敷地・道・中庭) / green(庭園) / bld(その他の建物) / mus(美術館) / red(聖堂と広場) / border(境界線)
地図座標→世界座標は、ドーム中心(363,334)とオベリスク(552,341)の2点で合わせる（距離 323m → 1.71 m/px、2.1° 回転）。
"""
import math
from PIL import Image

PROTO = {
    'out': [(228, 228, 228), (216, 216, 216), (204, 204, 204), (240, 240, 240), (192, 192, 192), (180, 180, 180)],
    'ground': [(252, 240, 195), (240, 240, 192), (252, 252, 204), (240, 228, 192), (228, 240, 180), (254, 248, 200), (250, 245, 215)],
    'green': [(156, 192, 120), (168, 192, 132), (141, 171, 109), (156, 180, 120), (168, 180, 120), (144, 168, 108), (180, 192, 132)],
    'bld': [(192, 156, 132), (180, 144, 120), (180, 156, 120), (200, 165, 140)],
    'mus': [(204, 180, 108), (227, 200, 131), (216, 190, 120), (200, 170, 100)],
    'red': [(204, 96, 108), (233, 135, 136), (220, 110, 115), (240, 160, 160)],
    'border': [(128, 80, 112), (144, 96, 128), (160, 112, 144), (112, 64, 96)],
}
DOME, OBEL, DIST = (363.0, 334.0), (552.0, 341.0), 323.0

class MapGrid:
    def __init__(self, path):
        im = Image.open(path).convert('RGB'); self.W, self.H = im.size
        px = im.load()
        raw = [[None] * self.H for _ in range(self.W)]
        for x in range(self.W):
            for y in range(self.H):
                r, g, b = px[x, y]
                if r + g + b < 380 and not (r > g + 30 and b > g + 10): raw[x][y] = None          # 文字（暗い）
                elif b > r + 25 and b > g and b > 180: raw[x][y] = 'water'
                else:
                    best = min(((sum((a - c) ** 2 for a, c in zip((r, g, b), p)), k) for k, ps in PROTO.items() for p in ps))
                    raw[x][y] = best[1]
        # 文字の穴を周囲の多数決で埋める（2回）
        for _ in range(2):
            new = [col[:] for col in raw]
            for x in range(self.W):
                for y in range(self.H):
                    if raw[x][y] is not None: continue
                    cnt = {}
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            X, Y = x + dx, y + dy
                            if 0 <= X < self.W and 0 <= Y < self.H and raw[X][Y]: cnt[raw[X][Y]] = cnt.get(raw[X][Y], 0) + 1
                    if cnt: new[x][y] = max(cnt, key=cnt.get)
            raw = new
        self.cls = raw
        self.s = math.dist(DOME, OBEL) / DIST
        self.th = math.atan2(OBEL[1] - DOME[1], OBEL[0] - DOME[0])

    def to_px(self, x, z):
        c, s = math.cos(self.th), math.sin(self.th)
        return DOME[0] + (x * c - z * s) * self.s, DOME[1] + (x * s + z * c) * self.s

    def at(self, x, z):
        u, v = self.to_px(x, z); X, Y = int(round(u)), int(round(v))
        if not (0 <= X < self.W and 0 <= Y < self.H): return 'out'
        return self.cls[X][Y] or 'out'

    def world_bounds(self):
        xs, zs = [], []
        c, s = math.cos(self.th), math.sin(self.th)
        for X in range(self.W):
            for Y in range(self.H):
                if self.cls[X][Y] not in (None, 'out'):
                    u, v = (X - DOME[0]) / self.s, (Y - DOME[1]) / self.s
                    xs.append(u * c + v * s); zs.append(-u * s + v * c)
        return int(min(xs)) - 3, int(max(xs)) + 3, int(min(zs)) - 3, int(max(zs)) + 3
