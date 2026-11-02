"""高レベル建築のための汎用関数（references/advanced_building.md と対で使う）。

分類:
  1. 変換        rotate_state / mirror_state / stamp / transform_be / transform_entity  … 向き情報を保ったまま 90°回転・反転・複製
  2. 曲線        line3d / polyline / catmull_rom / catenary / circle_cells / ellipse_cells / superellipse_cells
  3. 立体(SDF)   sd_* と union/subtract/intersect/smooth_union、fill_sdf（WorldEdit //generate 相当。殻の厚み指定可）
  4. 滑らかな面  smooth_heightfield（高さ関数→フル/ハーフ/階段。曲面屋根・ドーム・地形の縁を「段々」にしない基本技）
                cone_roof / dome_roof / gambrel_roof / mansard_roof
  5. 建築部材    arch_inside（半円〜尖頭〜ランセット）/ opening（奥行きのある窓・扉）/ rose_window / buttress / spire / cornice / pilasters
  6. 質感        value_noise / fbm / ridged / grad_pick（ディザ付きグラデ）/ weather（苔・ひび・欠け）/ edge_trim
  7. 地形・植生  terrain（層つき）/ thermal_erode / poisson_disk / organic_tree
  8. 解析        hidden_cells（見えないブロック）/ palette_stats / bbox
座標は y 上、x 東、z 南（Minecraft と同じ）。回転 turns は「上から見て時計回りの 90° の回数」（north→east→south→west）。
"""
import math, random
from collections import Counter

# ======================================================================= 1. 変換（ブロック状態の回転・反転）
_DIRS = ['north', 'east', 'south', 'west']
_VEC = {'north': (0, -1), 'east': (1, 0), 'south': (0, 1), 'west': (-1, 0)}

def _rot_dir(d, t):
    return _DIRS[(_DIRS.index(d) + t) % 4] if d in _DIRS else d

def _mir_dir(d, axis):
    if axis == 'x': return {'east': 'west', 'west': 'east'}.get(d, d)
    return {'north': 'south', 'south': 'north'}.get(d, d)

_RAIL = {'north_south': ('north', 'south'), 'east_west': ('east', 'west'), 'south_east': ('south', 'east'),
         'south_west': ('south', 'west'), 'north_west': ('north', 'west'), 'north_east': ('north', 'east')}
def _rail_from(a, b):
    for k, v in _RAIL.items():
        if set(v) == {a, b}: return k
    return 'north_south'

def _swap_lr(v): return v.replace('left', '#').replace('right', 'left').replace('#', 'right')

def rotate_state(name, props, turns):
    """(name, (('k','v'),...)) を上から見て時計回り 90°×turns 回した状態にする。
    対応: facing / axis / rotation(0-15) / 柵・壁・板ガラス・蔓・赤石の north..west 接続 / rail shape / orientation(crafter等)"""
    t = turns % 4
    if t == 0: return name, props
    P = dict(props); out = dict(P)
    for k, v in P.items():
        if k == 'facing' or k == 'horizontal_facing': out[k] = _rot_dir(v, t)
        elif k == 'axis' and t % 2 == 1 and v in ('x', 'z'): out[k] = 'z' if v == 'x' else 'x'
        elif k == 'rotation': out[k] = str((int(v) + 4 * t) % 16)
        elif k == 'shape' and v in _RAIL: out[k] = _rail_from(*(_rot_dir(d, t) for d in _RAIL[v]))
        elif k == 'shape' and v.startswith('ascending_'): out[k] = 'ascending_' + _rot_dir(v[10:], t)
        elif k == 'orientation' and '_' in v:
            a, b2 = v.split('_', 1); out[k] = _rot_dir(a, t) + '_' + _rot_dir(b2, t)
    for d in _DIRS:                                   # 側面の接続プロパティを回す
        if d in P: out[_rot_dir(d, t)] = P[d]
    return name, tuple(sorted(out.items()))

def mirror_state(name, props, axis):
    """axis='x' は東西反転（x→-x）、'z' は南北反転。階段の shape・扉の hinge・チェストの type の左右も入れ替える"""
    P = dict(props); out = dict(P)
    for k, v in P.items():
        if k in ('facing', 'horizontal_facing'): out[k] = _mir_dir(v, axis)
        elif k == 'rotation': out[k] = str(((16 - int(v)) if axis == 'x' else (8 - int(v))) % 16)
        elif k == 'shape' and ('left' in v or 'right' in v): out[k] = _swap_lr(v)
        elif k == 'hinge': out[k] = 'right' if v == 'left' else 'left'
        elif k == 'type' and v in ('left', 'right'): out[k] = _swap_lr(v)
        elif k == 'shape' and v in _RAIL: out[k] = _rail_from(*(_mir_dir(d, axis) for d in _RAIL[v]))
        elif k == 'shape' and v.startswith('ascending_'): out[k] = 'ascending_' + _mir_dir(v[10:], axis)
        elif k == 'orientation' and '_' in v:
            a, b2 = v.split('_', 1); out[k] = _mir_dir(a, axis) + '_' + _mir_dir(b2, axis)
    for d in _DIRS:
        if d in P: out[_mir_dir(d, axis)] = P[d]
    return name, tuple(sorted(out.items()))

def _xf_point(x, z, turns, mirror, origin, center=False):
    """ブロック座標（center=False）または実数座標（center=True）を変換。ブロックは中心(+.5)基準で回して整合をとる"""
    ox, oz = origin; c = 0 if center else 0.5
    X, Z = x + c - ox, z + c - oz
    if mirror == 'x': X = -X
    elif mirror == 'z': Z = -Z
    for _ in range(turns % 4): X, Z = -Z, X
    X, Z = X + ox, Z + oz
    return (X, Z) if center else (math.floor(X), math.floor(Z))

def transform_blocks(B, turns=0, mirror=None, origin=(0.5, 0.5), shift=(0, 0, 0)):
    """{(x,y,z): (name, props)} を反転→回転→平行移動。origin=(x,z) は回転の中心の実座標。
    既定 (0.5,0.5)＝ブロック(0,0)の中心なので、部品の (0,y,0) は回しても (0,y,0) のまま（=shift の位置）に残る"""
    out = {}
    for (x, y, z), (n, p) in B.items():
        if mirror: n, p = mirror_state(n, p, mirror)
        n, p = rotate_state(n, p, turns)
        X, Z = _xf_point(x, z, turns, mirror, origin)
        out[(X + shift[0], y + shift[1], Z + shift[2])] = (n, p)
    return out

def transform_be(BE, turns=0, mirror=None, origin=(0.5, 0.5), shift=(0, 0, 0)):
    out = []
    for (x, y, z, tag) in BE:
        X, Z = _xf_point(x, z, turns, mirror, origin); out.append((X + shift[0], y + shift[1], Z + shift[2], tag))
    return out

def transform_entity(e, turns=0, mirror=None, origin=(0.5, 0.5), shift=(0, 0, 0)):
    """エンティティの Pos と Rotation(yaw) を変換（yaw: 0=南 90=西 180=北 270=東、時計回りに +90）"""
    e = dict(e)
    if 'Pos' in e:
        x, y, z = e['Pos'][1][1]
        X, Z = _xf_point(x, z, turns, mirror, origin, center=True)
        e['Pos'] = (9, (6, [X + shift[0], y + shift[1], Z + shift[2]]))
    if 'Rotation' in e:
        yaw, pitch = e['Rotation'][1][1]
        if mirror == 'x': yaw = -yaw
        elif mirror == 'z': yaw = 180 - yaw
        e['Rotation'] = (9, (5, [float((yaw + 90 * turns) % 360), pitch]))
    return e

def stamp(b, part, at=(0, 0, 0), turns=0, mirror=None, origin=(0.5, 0.5), only_empty=False):
    """部品 part（Build か {(x,y,z):state}）を b に複製。部品の (0,0,0) が at に来て、そこを軸に回る。
    BE/ENT も一緒に運ぶ。家・塔・街灯などのモジュールを並べる基本"""
    B = part.B if hasattr(part, 'B') else part
    for k, v in transform_blocks(B, turns, mirror, origin, at).items():
        if only_empty and k in b.B: continue
        b.B[k] = v
    if getattr(part, 'BE', None):
        b.BE = getattr(b, 'BE', []) + transform_be(part.BE, turns, mirror, origin, at)
    if getattr(part, 'ENT', None):
        b.ENT = getattr(b, 'ENT', []) + [transform_entity(e, turns, mirror, origin, at) for e in part.ENT]

# ======================================================================= 2. 曲線
def line3d(a, b2):
    """整数格子の3D直線。隣り合う点は必ず面で接する（6近傍で連続。ロープ・梁・斜めの柱が途切れない）"""
    a = [float(v) for v in a]; b2 = [float(v) for v in b2]
    n = int(max(abs(b2[i] - a[i]) for i in range(3)) * 3) + 1
    pts = [tuple(int(round(v)) for v in a)]
    for i in range(1, n + 1):
        t = i / n; p = [int(round(a[k] + (b2[k] - a[k]) * t)) for k in range(3)]
        q = list(pts[-1])
        for k in range(3):                 # 1軸ずつ動かして角でつなぐ
            if q[k] != p[k]:
                q[k] = p[k]
                if tuple(q) != pts[-1]: pts.append(tuple(q))
    return pts

def polyline(pts):
    out = []
    for a, b2 in zip(pts, pts[1:]):
        for p in line3d(a, b2):
            if not out or out[-1] != p: out.append(p)
    return out

def catmull_rom(ctrl, step=0.35):
    """制御点を通る滑らかな曲線（実数点列）。道・川・城壁の平面線形・尾根線に"""
    P = [ctrl[0]] + list(ctrl) + [ctrl[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        L = math.dist(p1, p2); n = max(2, int(L / step))
        for j in range(n):
            t = j / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(tuple(ctrl[-1])); return out

def catenary(a, b2, sag, n=None, c=1.2):
    """懸垂線（ロープ・吊り橋・鎖・提灯の紐）。sag=中央の垂れ量（ブロック）。実数点列（line3d/polyline で格子化）"""
    L = math.dist((a[0], a[2]), (b2[0], b2[2])); n = n or max(4, int(L * 2))
    out = []
    for i in range(n + 1):
        t = i / n; s_ = (math.cosh(c * (2 * t - 1)) - math.cosh(c)) / (1 - math.cosh(c))     # 端0・中央1
        out.append(tuple(a[k] + (b2[k] - a[k]) * t for k in range(3)))
        out[-1] = (out[-1][0], out[-1][1] - sag * s_, out[-1][2])
    return out

def circle_cells(r, filled=False, thick=1.0):
    """きれいなピクセル円（中心 0,0）。r は実数可。偶数径にしたい時は r に .5 を足して中心を (−.5) ずらして使う"""
    R = int(math.ceil(r)) + 1; out = []
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            d = math.hypot(x, z)
            if d <= r + 0.5 and (filled or d > r + 0.5 - thick): out.append((x, z))
    return out

def ellipse_cells(rx, rz, filled=False, thick=1.0):
    out = []
    for x in range(-int(rx) - 1, int(rx) + 2):
        for z in range(-int(rz) - 1, int(rz) + 2):
            d = math.hypot(x / (rx + .5), z / (rz + .5))
            inner = math.hypot(x / max(.1, rx + .5 - thick), z / max(.1, rz + .5 - thick))
            if d <= 1 and (filled or inner > 1): out.append((x, z))
    return out

def superellipse_cells(rx, rz, n=4.0, filled=True):
    """|x/a|^n+|z/b|^n<=1。n=2 楕円、n=4 角の丸い四角（スタジアム・塔の平面・宇宙船の断面）"""
    out = []
    for x in range(-int(rx) - 1, int(rx) + 2):
        for z in range(-int(rz) - 1, int(rz) + 2):
            v = abs(x / (rx + .5)) ** n + abs(z / (rz + .5)) ** n
            if v <= 1 and (filled or any(abs((x + dx) / (rx + .5)) ** n + abs((z + dz) / (rz + .5)) ** n > 1 for dx, dz in _VEC.values())):
                out.append((x, z))
    return out

# ======================================================================= 3. 立体（符号付き距離関数 SDF）
# 各関数は (x,y,z)->距離（内側が負）。組み合わせて fill_sdf で塗る。
def sd_sphere(c, r): return lambda x, y, z: math.dist((x, y, z), c) - r
def sd_ellipsoid(c, rx, ry, rz):
    return lambda x, y, z: (math.sqrt(((x - c[0]) / rx) ** 2 + ((y - c[1]) / ry) ** 2 + ((z - c[2]) / rz) ** 2) - 1) * min(rx, ry, rz)
def sd_box(c, h, round_=0.0):
    def f(x, y, z):
        q = [abs(p - cc) - hh + round_ for p, cc, hh in zip((x, y, z), c, h)]
        return math.hypot(*[max(v, 0) for v in q]) + min(max(q), 0) - round_
    return f
def sd_cylinder(c, r, h, axis='y'):
    def f(x, y, z):
        p = (x - c[0], y - c[1], z - c[2]); i = 'xyz'.index(axis)
        rad = math.hypot(*[p[k] for k in range(3) if k != i]) - r; ax = abs(p[i]) - h
        return min(max(rad, ax), 0) + math.hypot(max(rad, 0), max(ax, 0))
    return f
def sd_cone(base, r, h):
    """底面中心 base、半径 r、高さ h の円錐（尖塔・屋根）"""
    def f(x, y, z):
        q = math.hypot(x - base[0], z - base[2]); yy = y - base[1]
        if yy < 0: return max(-yy, q - r)
        return max(q - r * (1 - yy / h), yy - h) * (h / math.hypot(h, r))
    return f
def sd_torus(c, R, r, axis='y'):
    def f(x, y, z):
        p = (x - c[0], y - c[1], z - c[2]); i = 'xyz'.index(axis)
        rad = math.hypot(*[p[k] for k in range(3) if k != i])
        return math.hypot(rad - R, p[i]) - r
    return f
def sd_capsule(a, b2, r):
    def f(x, y, z):
        pa = [x - a[0], y - a[1], z - a[2]]; ba = [b2[i] - a[i] for i in range(3)]
        h = max(0, min(1, sum(pa[i] * ba[i] for i in range(3)) / max(1e-9, sum(v * v for v in ba))))
        return math.dist(pa, [ba[i] * h for i in range(3)]) - r
    return f
def sd_union(*fs): return lambda x, y, z: min(f(x, y, z) for f in fs)
def sd_intersect(*fs): return lambda x, y, z: max(f(x, y, z) for f in fs)
def sd_subtract(a, *bs): return lambda x, y, z: max(a(x, y, z), *(-b2(x, y, z) for b2 in bs))
def sd_smooth_union(a, b2, k=3.0):
    """なめらかに融合（岩・雲・有機的な建築・樹の根元）"""
    def f(x, y, z):
        da, db = a(x, y, z), b2(x, y, z); h = max(0, min(1, 0.5 + 0.5 * (db - da) / k))
        return db * (1 - h) + da * h - k * h * (1 - h)
    return f
def sd_displace(f, amp=1.0, scale=6.0, seed=0):
    """表面をノイズで揺らす（岩・崖・雲を自然に）"""
    return lambda x, y, z: f(x, y, z) + amp * fbm3(x / scale, y / scale, z / scale, seed=seed)

def fill_sdf(b, f, bbox, mat, shell=None, **props):
    """bbox=((x0,y0,z0),(x1,y1,z1)) の各ブロック中心で f<=0 を塗る。shell=厚み を渡すと -shell<f<=0 の殻だけ。
    mat は名前か callable(x,y,z)。戻り値は置いたセルのリスト"""
    (x0, y0, z0), (x1, y1, z1) = bbox; out = []
    for x in range(int(x0), int(x1) + 1):
        for y in range(int(y0), int(y1) + 1):
            for z in range(int(z0), int(z1) + 1):
                d = f(x, y, z)
                if d <= 0.0 and (shell is None or d > -shell):
                    b.put(x, y, z, mat(x, y, z) if callable(mat) else mat, **props); out.append((x, y, z))
    return out

# ======================================================================= 4. 滑らかな面（高さ場 → フル/ハーフ/階段）
def smooth_heightfield(b, cells, h, full, stair=None, slab=None, base=None, fill_down=1, only_empty=False):
    """cells の各列 (x,z) について『表面の高さ』h(x,z)（実数。y=h の面まで中身がある）を半ブロック単位で丸めて置く。
      ・n=round(2h) が偶数 → y=n/2-1 までフルブロック
      ・n が奇数          → その上 y=n//2 に、隣により高い列があればその向きへ上る階段、無ければ下ハーフ
    曲面屋根（円錐・ドーム・反り屋根）、丘、ピラミッドの面を『段々』でなく見せる基本技。
    base=中身の下端 y（None なら表面から fill_down 段だけ＝屋根の厚み）。戻り値 {(x,z): n}"""
    cells = list(cells); H = {c: int(round(h(*c) * 2)) for c in cells}
    put = lambda x, y, z, m, **p: (not only_empty or b.empty(x, y, z)) and b.put(x, y, z, m(x, y, z) if callable(m) else m, **p)
    halves = []
    for (x, z), n in H.items():
        top_full = n // 2 - 1
        lo = base if base is not None else top_full - fill_down + 1
        for y in range(lo, top_full + 1): put(x, y, z, full)
        if n % 2 == 0: continue
        y = n // 2; up = None; best = n
        for d, (dx, dz) in _VEC.items():
            m = H.get((x + dx, z + dz))
            if m is not None and m > best: best, up = m, d
        if up and stair: put(x, y, z, stair, facing=up, half='bottom', shape='straight', waterlogged='false'); halves.append((x, y, z))
        elif slab: put(x, y, z, slab, type='bottom', waterlogged='false')
        elif stair: put(x, y, z, full)
    if stair: fix_stair_corners(b, halves)
    return H

def fix_stair_corners(b, cells):
    """階段の shape（inner/outer の left/right）を隣の階段から自動で決める（ゲームの規則を再現）"""
    def st(c):
        v = b.B.get(c)
        return dict(v[1]) if v and v[0].endswith('_stairs') else None
    left_of = {'north': 'west', 'west': 'south', 'south': 'east', 'east': 'north'}
    for c in cells:
        s = st(c)
        if not s: continue
        f = s['facing']; fx, fz = _VEC[f]
        shape = 'straight'
        back = st((c[0] + fx, c[1], c[2] + fz))                  # 高い側（背中）にある階段 → outer
        front = st((c[0] - fx, c[1], c[2] - fz))                 # 低い側（前）にある階段 → inner
        if back and back['half'] == s['half'] and back['facing'] not in (f, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[f]):
            shape = 'outer_left' if back['facing'] == left_of[f] else 'outer_right'
        elif front and front['half'] == s['half'] and front['facing'] not in (f, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[f]):
            shape = 'inner_left' if front['facing'] == left_of[f] else 'inner_right'
        n, p = b.B[c]; P = dict(p); P['shape'] = shape; b.B[c] = (n, tuple(sorted(P.items())))

def cone_roof(b, cx, cz, y0, r, height, full, stair, slab=None, overhang=1, fill_down=2):
    """円錐屋根（塔の帽子）。高さ/半径 = 1.5〜3 が中世の塔らしい"""
    R = r + overhang
    cells = [(cx + x, cz + z) for x, z in circle_cells(R, filled=True)]
    return smooth_heightfield(b, cells, lambda x, z: y0 + max(0.0, (R + .5 - math.hypot(x - cx, z - cz))) * height / (R + .5),
                              full, stair, slab, fill_down=fill_down)

def dome_roof(b, cx, cz, y0, r, rise=None, full='stone', stair=None, slab=None, fill_down=2, onion=0.0):
    """ドーム（rise=高さ。省略で半球）。onion>0 で玉ねぎ形（ロシア・ムガル風の膨らみと尖り）"""
    rise = rise or r
    def h(x, z):
        d = min(1.0, math.hypot(x - cx, z - cz) / (r + .5)); v = math.sqrt(max(0, 1 - d * d))
        if onion: v = v + onion * (1 - d) ** 3 * 1.5
        return y0 + v * rise
    cells = [(cx + x, cz + z) for x, z in circle_cells(r, filled=True)]
    return smooth_heightfield(b, cells, h, full, stair, slab, fill_down=fill_down)

def gambrel_roof(b, x0, x1, z0, z1, y0, full, stair, slab=None, steep=1.6, gentle=0.5, knee=0.45, axis='x', fill_down=2):
    """腰折れ屋根（納屋・オランダ風）。棟は axis 方向。knee=急勾配部の割合"""
    w = (z1 - z0 + 1) / 2 if axis == 'x' else (x1 - x0 + 1) / 2
    def h(x, z):
        d = (z - z0 + .5) if axis == 'x' else (x - x0 + .5); d = min(d, 2 * w - d)
        k = w * knee
        return y0 + (d * steep if d < k else k * steep + (d - k) * gentle)
    cells = [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]
    return smooth_heightfield(b, cells, h, full, stair, slab, fill_down=fill_down)

def mansard_roof(b, x0, x1, z0, z1, y0, full, stair, slab=None, steep=2.0, inset=2, flat_mat=None, fill_down=2):
    """マンサード屋根（パリの屋根）。四方の急勾配＋上の平らな陸屋根"""
    def h(x, z):
        d = min(x - x0 + .5, x1 - x + .5, z - z0 + .5, z1 - z + .5)
        return y0 + min(d, inset) * steep
    cells = [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]
    return smooth_heightfield(b, cells, h, full, stair, slab, fill_down=fill_down)

# ======================================================================= 5. 建築部材
def arch_inside(u, v, half_w, spring, sharp=1.0):
    """開口の内側判定。u=開口中心からの横距離、v=床からの高さ。spring=迫元（アーチの始まり）の高さ。
    sharp=1 半円 / 1.3〜1.6 ゴシックの尖頭 / 2 正三角形尖頭(equilateral) / 3 ランセット。0 なら四角"""
    if v < 0 or abs(u) > half_w + .5: return False
    if v <= spring or sharp <= 0: return True
    a = half_w + .5; r = a * sharp; y = v - spring
    return (u + a - r) ** 2 + y * y <= r * r and (u - a + r) ** 2 + y * y <= r * r

def opening(b, x, y, z, normal, w, h, depth=1, sharp=1.4, spring=None, glass='glass_pane', frame=None, sill=None, keystone=None, wall_t=1):
    """奥行きのある窓・扉を壁に開ける。(x,y,z)=開口の下中央の『壁の外面』セル、normal=壁の外向き（north 等）。
    depth: ガラスを外面から何マス奥に置くか（1〜2 で影ができる）。frame: 外周の額縁ブロック。sill: 窓台（逆さ階段を外に）。
    keystone: 頂部の要石ブロック。glass=None なら抜くだけ（扉・回廊）"""
    nx, nz = _VEC[normal]; tx, tz = -nz, nx                     # 壁に沿う向き
    hw = (w - 1) / 2
    if spring is None:                                              # 頂部が h になるよう迫元を決める（アーチの立ち上がり=√(2ar−a²)）
        a_ = hw + .5; r_ = a_ * max(sharp, 1e-6); spring = h - (math.sqrt(max(0, 2 * a_ * r_ - a_ * a_)) if sharp > 0 else 0)
    cells = [(u, v) for u in range(-int(hw) - 1, int(hw) + 2) for v in range(0, h + 1) if arch_inside(u, v, hw, spring, sharp)]
    for u, v in cells:
        for d in range(0, wall_t):
            b.rm(x + tx * u - nx * d, y + v, z + tz * u - nz * d)
        if glass:
            gd = min(depth, wall_t - 1) if wall_t > 1 else 0
            props = {}
            if 'pane' in glass or 'bars' in glass:
                props = dict(north='false', south='false', east='false', west='false', waterlogged='false')
                props[_rot_dir(normal, 1)] = 'true'; props[_rot_dir(normal, 3)] = 'true'
            b.put(x + tx * u - nx * gd, y + v, z + tz * u - nz * gd, glass, **props)
    if frame:
        S = set(cells)
        for u, v in cells:
            for du, dv in ((1, 0), (-1, 0), (0, 1)):
                if (u + du, v + dv) not in S: b.put(x + tx * (u + du) + nx, y + v + dv, z + tz * (u + du) + nz, frame)
    if sill:
        for u in range(-int(hw), int(hw) + 1):
            b.put(x + tx * u + nx, y - 1, z + tz * u + nz, sill, facing=_rot_dir(normal, 2), half='top', shape='straight', waterlogged='false')
    if keystone:
        top = max(v for u, v in cells if u == 0)
        b.put(x + nx, y + top + 1, z + nz, keystone)
    return cells

def rose_window(R, petals=8, hub=None):
    """バラ窓の分類関数 f(u,v)->'frame'|'glass'|'hub'|None（中心 0,0、半径 R ブロック）。paint_plane で鉛直面に塗る。
    構成（寸法はブロック単位で太さ1）：外枠の輪・中間の輪(0.6R)・内側の放射桟 petals 本・外側は半ピッチずらした桟（トレーサリー）
    R>=12 なら外周に小円（フォイル）も入る。R=5〜7 で花形、R>=9 で本格的"""
    hub = hub if hub is not None else max(1.0, R * 0.18)
    mid = R * 0.6
    def f(u, v):
        rr = math.hypot(u, v)
        if rr > R + 0.5: return None
        if rr > R - 0.5 or abs(rr - mid) < 0.5: return 'frame'
        if rr < hub + 0.5: return 'hub' if rr < hub - 0.5 else 'frame'
        th = math.atan2(v, u); step = 2 * math.pi / petals
        off = 0 if rr < mid else step / 2                                    # 外側は半ピッチずらす
        a = ((th - off) % step); a = min(a, step - a)
        if rr * math.sin(a) < 0.5: return 'frame'                                # 桟まで 0.5 ブロック未満
        if R >= 12 and rr > mid:
            for i in range(petals):
                t = i * step; fx, fz = (R * .8) * math.cos(t), (R * .8) * math.sin(t)
                if abs(math.hypot(u - fx, v - fz) - R * 0.15) < 0.5: return 'frame'
        return 'glass'
    return f

def paint_plane(b, f, R, origin, axis='z', mats=None):
    """分類関数 f(u,v) を鉛直面（axis='z' なら x-y 面を z=一定、'x' なら z-y 面）に塗る。mats={'frame':…, 'glass':…}"""
    ox, oy, oz = origin
    for u in range(-R - 1, R + 2):
        for v in range(-R - 1, R + 2):
            k = f(u, v)
            if k is None or not mats or k not in mats or mats[k] is None: continue
            p = (ox + u, oy + v, oz) if axis == 'z' else (ox, oy + v, oz + u)
            b.put(*p, mats[k])

def buttress(b, x, y0, z, out, height, depth, mat, cap=None, flying_to=None):
    """控え壁（壁から out 方向へ depth 張り出し、上ほど細く）。flying_to=(y) を渡すと上部から壁へ斜めのフライング・バットレス"""
    nx, nz = _VEC[out]
    for d in range(1, depth + 1):
        top = y0 + int(height * (1 - (d - 1) / (depth + 0.5)))
        for y in range(y0, top + 1): b.put(x + nx * d, y, z + nz * d, mat)
        if cap: b.put(x + nx * d, top + 1, z + nz * d, cap, facing=_rot_dir(out, 2), half='bottom', shape='straight', waterlogged='false')
    if flying_to is not None:
        for p in line3d((x + nx * depth, y0 + height, z + nz * depth), (x + nx, flying_to, z + nz)):
            b.put(*p, mat)

def spire(b, cx, y0, cz, r, h, mat, sides=8, rot=22.5, cap=None):
    """多角錐の尖塔（8角形が教会らしい）。中空で軽い"""
    for y in range(h):
        rr = r * (1 - y / h)
        if rr < 0.35: b.put(cx, y0 + y, cz, mat(cx, y0 + y, cz) if callable(mat) else mat); continue
        poly = [(rr * math.cos(math.radians(rot + 360 * i / sides)), rr * math.sin(math.radians(rot + 360 * i / sides))) for i in range(sides)]
        for x in range(-int(r) - 1, int(r) + 2):
            for z in range(-int(r) - 1, int(r) + 2):
                if _in_poly(x, z, poly) and not _in_poly(x, z, [(px * (rr - 1) / rr, pz * (rr - 1) / rr) for px, pz in poly] if rr > 1.2 else []):
                    b.put(cx + x, y0 + y, cz + z, mat(cx + x, y0 + y, cz + z) if callable(mat) else mat)
    if cap: b.put(cx, y0 + h, cz, cap)

def _in_poly(x, z, poly):
    if not poly: return False
    ins = False; j = len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]; xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi + 1e-12) + xi: ins = not ins
        j = i
    return ins

def cornice(b, cells_with_dir, y, stair, under=None):
    """軒蛇腹：外壁の上端に逆さ階段を外向きに一周（cells_with_dir=[(x,z,'north'),…] は張り出す先のセルと外向き）"""
    for x, z, d in cells_with_dir:
        b.put(x, y, z, stair, facing=_rot_dir(d, 2), half='top', shape='straight', waterlogged='false')
        if under: b.put(x, y - 1, z, under, facing=_rot_dir(d, 2), half='top', open='true', powered='false', waterlogged='false')

def pilasters(b, x0, z0, x1, z1, y0, y1, every, mat, out=1):
    """長方形の外壁 (x0..x1, z0..z1) に一定間隔の付け柱（壁面のリズムと影）。角は必ず立てる。out=張り出し"""
    def col(x, z):
        for y in range(y0, y1 + 1): b.put(x, y, z, mat)
    for x in range(x0, x1 + 1):
        if (x - x0) % every == 0 or x == x1: col(x, z0 - out); col(x, z1 + out)
    for z in range(z0, z1 + 1):
        if (z - z0) % every == 0 or z == z1: col(x0 - out, z); col(x1 + out, z)

# ======================================================================= 6. 質感（ノイズ・グラデーション・風化）
def _hash(*v, seed=0):
    h = seed * 374761393
    for a in v: h = (h ^ (int(a) * 668265263)) * 2246822519 & 0xffffffff
    return ((h ^ (h >> 13)) * 3266489917 & 0xffffffff) / 0xffffffff

def value_noise2(x, z, seed=0):
    xi, zi = math.floor(x), math.floor(z); fx, fz = x - xi, z - zi
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = _hash(xi, zi, seed=seed); b2 = _hash(xi + 1, zi, seed=seed); c = _hash(xi, zi + 1, seed=seed); d = _hash(xi + 1, zi + 1, seed=seed)
    return (a + (b2 - a) * sx + (c - a) * sz + (a - b2 - c + d) * sx * sz) * 2 - 1

def value_noise3(x, y, z, seed=0):
    xi, yi, zi = math.floor(x), math.floor(y), math.floor(z); f = [x - xi, y - yi, z - zi]
    s = [t * t * (3 - 2 * t) for t in f]; acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (s[0] if dx else 1 - s[0]) * (s[1] if dy else 1 - s[1]) * (s[2] if dz else 1 - s[2])
                acc += w * _hash(xi + dx, yi + dy, zi + dz, seed=seed)
    return acc * 2 - 1

def fbm2(x, z, octaves=4, seed=0, lac=2.0, gain=0.5):
    """フラクタルノイズ（-1..1 付近）。地形の起伏・材料の塊・輪郭の揺らぎに"""
    a, f, s, n = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves): s += a * value_noise2(x * f, z * f, seed + o * 17); n += a; a *= gain; f *= lac
    return s / n

def fbm3(x, y, z, octaves=3, seed=0):
    a, f, s, n = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves): s += a * value_noise3(x * f, y * f, z * f, seed + o * 17); n += a; a *= .5; f *= 2
    return s / n

def ridged2(x, z, octaves=4, seed=0):
    """稜線ノイズ（0..1）。山脈・岩の尾根・ひび割れ"""
    a, f, s, n = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves): s += a * (1 - abs(value_noise2(x * f, z * f, seed + o * 31))) ** 2; n += a; a *= .5; f *= 2
    return s / n

def grad_pick(palette, t, x, y, z, jitter=0.18, scale=3.0, seed=0):
    """グラデーション：t(0..1) を palette の位置に写し、塊ノイズで境界をディザする（ごま塩にしない）。
    例: 壁の下から上へ ['cobblestone','stone_bricks','andesite','polished_andesite']"""
    t = t + jitter * fbm3(x / scale, y / scale, z / scale, 2, seed)
    i = int(max(0, min(len(palette) - 1, round(t * (len(palette) - 1)))))
    return palette[i]

WEATHER = {'stone_bricks': ['mossy_stone_bricks', 'cracked_stone_bricks'], 'cobblestone': ['mossy_cobblestone', 'mossy_cobblestone'],
           'stone_brick_stairs': ['mossy_stone_brick_stairs', 'mossy_stone_brick_stairs'], 'stone_brick_slab': ['mossy_stone_brick_slab', 'mossy_stone_brick_slab'],
           'stone_brick_wall': ['mossy_stone_brick_wall', 'mossy_stone_brick_wall'], 'deepslate_bricks': ['cracked_deepslate_bricks', 'cracked_deepslate_bricks'],
           'deepslate_tiles': ['cracked_deepslate_tiles', 'cracked_deepslate_tiles'], 'polished_blackstone_bricks': ['cracked_polished_blackstone_bricks'] * 2,
           'nether_bricks': ['cracked_nether_bricks'] * 2, 'bricks': ['mud_bricks', 'mud_bricks'], 'sandstone': ['smooth_sandstone', 'cut_sandstone'],
           'tuff_bricks': ['chiseled_tuff_bricks', 'tuff'], 'copper_block': ['exposed_copper', 'weathered_copper'],
           'cut_copper': ['exposed_cut_copper', 'weathered_cut_copper']}

def weather(b, amount=0.25, moss_low=True, seed=0, table=WEATHER, cells=None):
    """風化：下の方・北面・水平な上面ほど苔、角と高所はひび。amount=0..1。状態（階段の向き等）は保つ"""
    ys = [k[1] for k in b.B]; y0, y1 = min(ys), max(ys) + 1
    for k in list(cells or b.B):
        v = b.B.get(k)
        if not v: continue
        n = v[0].replace('minecraft:', '')
        if n not in table: continue
        x, y, z = k
        low = 1 - (y - y0) / (y1 - y0) if moss_low else 0.5
        north = 0.15 if (x, y, z - 1) not in b.B else 0
        score = 0.55 * fbm3(x / 4, y / 4, z / 4, 2, seed) + 0.6 * low + north - (1 - amount) * 0.9
        if score > 0.15:
            alt = table[n][0 if low > 0.4 else 1]
            b.B[k] = ('minecraft:' + alt, v[1])

def edge_trim(b, cells, mat_stair, mat_slab=None):
    """上面の縁（空気に面した外周）にハーフ/階段を足して輪郭を柔らかく（壁の頂部・岩の縁・テラス）"""
    S = set(cells)
    for (x, y, z) in cells:
        if (x, y + 1, z) in b.B: continue
        for d, (dx, dz) in _VEC.items():
            if (x + dx, y, z + dz) not in S and (x + dx, y, z + dz) not in b.B and (x + dx, y - 1, z + dz) in b.B:
                if mat_slab: b.put(x + dx, y, z + dz, mat_slab, type='bottom', waterlogged='false')
                else: b.put(x + dx, y, z + dz, mat_stair, facing=_rot_dir(d, 2), half='bottom', shape='straight', waterlogged='false')

# ======================================================================= 7. 地形・植生
def terrain(b, x0, z0, x1, z1, height, layers=(('grass_block', 1), ('dirt', 3)), deep='stone', base=None, mask=None, smooth_top=None):
    """高さ関数 height(x,z)→実数（最上段ブロックの y）で地形を作る。layers=上から順の (ブロック, 厚さ)。
    base=下端（None なら最低点-3）。mask(x,z)→bool で範囲を絞る（島の輪郭など）。
    smooth_top=(stair, slab) で端数 .5 以上の列に階段/ハーフを足して斜面をなめらかに（低い丘・砂丘・土手）"""
    cols = {(x, z): height(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1) if not mask or mask(x, z)}
    if not cols: return {}
    lo = base if base is not None else int(min(cols.values())) - 3
    for (x, z), h in cols.items():
        top = int(math.floor(h)) if not smooth_top else int(round((h + 1) * 2)) // 2 - 1
        for depth, y in enumerate(range(top, lo - 1, -1)):
            acc = 0; m = deep
            for mat, t in layers:
                if depth < acc + t: m = mat; break
                acc += t
            b.put(x, y, z, m(x, y, z) if callable(m) else m)
    if smooth_top:
        top_mat = layers[0][0] if layers else deep
        smooth_heightfield(b, list(cols), lambda x, z: cols[(x, z)] + 1, top_mat, smooth_top[0], smooth_top[1], fill_down=0, only_empty=True)
    return cols

def thermal_erode(H, iters=20, talus=1.2, rate=0.4):
    """熱侵食（崖の角を崩して自然な斜面に）。H={(x,z):高さ} を書き換えて返す。talus=安定角（高低差）"""
    for _ in range(iters):
        D = {}
        for (x, z), h in H.items():
            for dx, dz in _VEC.values():
                n = (x + dx, z + dz)
                if n in H and h - H[n] > talus:
                    m = (h - H[n] - talus) * rate / 4; D[(x, z)] = D.get((x, z), 0) - m; D[n] = D.get(n, 0) + m
        for k, v in D.items(): H[k] += v
    return H

def poisson_disk(x0, z0, x1, z1, r, seed=0, k=20):
    """最小間隔 r のランダム点（Bridson）。木・岩・街灯・家の配置を『均等すぎず、固まりすぎず』に"""
    rng = random.Random(seed); cs = r / math.sqrt(2); G = {}
    def ok(p):
        gx, gz = int((p[0] - x0) / cs), int((p[1] - z0) / cs)
        for i in range(gx - 2, gx + 3):
            for j in range(gz - 2, gz + 3):
                q = G.get((i, j))
                if q and math.dist(p, q) < r: return False
        return x0 <= p[0] <= x1 and z0 <= p[1] <= z1
    p0 = (rng.uniform(x0, x1), rng.uniform(z0, z1)); pts = [p0]; act = [p0]; G[(int((p0[0] - x0) / cs), int((p0[1] - z0) / cs))] = p0
    while act:
        i = rng.randrange(len(act)); p = act[i]; found = False
        for _ in range(k):
            a = rng.uniform(0, 2 * math.pi); d = rng.uniform(r, 2 * r); q = (p[0] + d * math.cos(a), p[1] + d * math.sin(a))
            if ok(q): pts.append(q); act.append(q); G[(int((q[0] - x0) / cs), int((q[1] - z0) / cs))] = q; found = True; break
        if not found: act.pop(i)
    return [(int(round(x)), int(round(z))) for x, z in pts]

def organic_tree(b, x, y, z, height=14, spread=0.55, trunk_r=1.6, depth=3, seed=0, log='oak_log', wood='oak_wood',
                 leaves='oak_leaves', leaf_r=3.2, lean=(0.0, 0.0)):
    """再帰的な枝分かれの大木（幹は先細り、枝は上向きに曲がり、先端に葉の塊=殻）。b は builder.Build（tube/shell を使う）"""
    from builder import LEAF
    rng = random.Random(seed); tips = []
    def grow(p, dirv, L, r, lvl):
        end = (p[0] + dirv[0] * L, p[1] + dirv[1] * L, p[2] + dirv[2] * L)
        c1 = (p[0] + dirv[0] * L * .35, p[1] + dirv[1] * L * .35, p[2] + dirv[2] * L * .35)
        c2 = (end[0] - dirv[0] * L * .3 + rng.uniform(-1, 1), end[1] - dirv[1] * L * .3 + rng.uniform(0, 1.5), end[2] - dirv[2] * L * .3 + rng.uniform(-1, 1))
        b.tube(p, c1, c2, end, r, max(0.5, r * .65), wood if lvl else log, **({} if lvl else {'axis': 'y'}))
        if lvl >= depth or r < 0.6: tips.append(end); return
        n = rng.choice((2, 3, 3)); base = rng.uniform(0, 2 * math.pi)
        for i in range(n):
            a = base + 2 * math.pi * i / n + rng.uniform(-.4, .4); s = spread * rng.uniform(.8, 1.2)
            d = (dirv[0] * (1 - s) + math.cos(a) * s, dirv[1] * (1 - s * .5) + .25, dirv[2] * (1 - s) + math.sin(a) * s)
            m = math.sqrt(sum(v * v for v in d)); d = tuple(v / m for v in d)
            grow(end, d, L * rng.uniform(.55, .75), r * .62, lvl + 1)
    d0 = (lean[0], 1.0, lean[1]); m = math.sqrt(sum(v * v for v in d0))
    grow((x, y, z), tuple(v / m for v in d0), height * .55, trunk_r, 0)
    for t in tips:
        b.shell(t[0], t[1] + .8, t[2], leaf_r * rng.uniform(.85, 1.2), leaf_r * .7, leaf_r * rng.uniform(.85, 1.2), leaves, inner=.3, lumpy=.35, **LEAF)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):                  # 根張り
        b.tube((x, y + 1, z), (x + dx * 1.5, y + .5, z + dz * 1.5), (x + dx * 2.5, y, z + dz * 2.5), (x + dx * 3.5, y - .5, z + dz * 3.5), trunk_r * .7, .5, wood)
    return tips

# ======================================================================= 8. 解析
def bbox(b):
    ks = list(b.B); return tuple(min(k[i] for k in ks) for i in range(3)), tuple(max(k[i] for k in ks) for i in range(3))

OPAQUE_SKIP = ('glass', 'pane', 'leaves', 'stairs', 'slab', 'fence', 'wall', 'door', 'trapdoor', 'lantern', 'torch', 'chain', 'bars', 'water', 'lava', 'ice', 'carpet', 'sign', 'button', 'lever', 'rail', 'ladder', 'vine', 'flower', 'grass', 'fern', 'chest', 'spawner')
def hidden_cells(b, keep=lambda n: False):
    """6面すべて不透明フルブロックに囲まれたセル（外から見えない）。内装の無い巨大な塊の中身を抜いて軽くする時に。
    ※ 宝箱・スポナーなど keep(name) が True のものは除外。内部空間のある建物には使わない"""
    def opaque(c):
        v = b.B.get(c); return bool(v) and not any(s in v[0] for s in OPAQUE_SKIP)
    out = []
    for (x, y, z), v in b.B.items():
        if keep(v[0]): continue
        if opaque((x, y, z)) and all(opaque((x + dx, y + dy, z + dz)) for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
            out.append((x, y, z))
    return out

def palette_stats(b, top=12):
    """使用ブロックの割合。『主材 60 / 副材 30 / 差し色 10』の目安から外れていないかを見る"""
    c = Counter(v[0].replace('minecraft:', '') for v in b.B.values()); n = sum(c.values())
    return [(k, v, round(100 * v / n, 1)) for k, v in c.most_common(top)]
