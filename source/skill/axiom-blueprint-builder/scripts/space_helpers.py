"""宇宙ステーション・宇宙船向けヘルパー（ISS 1block=1m で実践）。
使い方: from space_helpers import *   （builder.py と同じ場所に置く）
- tube(): 直径5(外径)・殻厚1・内部3x3 の円筒モジュール。角は階段で面取り。軸は x/y/z。両端はキャップ（継手リング付き）
- tube_lights()/tube_racks(): 内部の照明(end_rod)と壁際ラック（中央1列の通路を残す）
- lattice_truss(): 角柱＋枠＋面中央の格子で作るトラス
- solar_wing(): 太陽電池翼（青パネル＋マスト＋金の縁＋ハブ間隔）
- radiator_panel(): 白パネルと灰色の枠線
座標は呼び出し側のワールド座標。断面は (u,v)、軸方向 a。PT(ax,cu,cv,du,dv,a) が3D座標に変換する。
"""
from builder import *

def PT(ax, cu, cv, du, dv, a):
    """断面座標→3D。ax='z': (u,v)=(x,y) / 'x': (u,v)=(z,y) / 'y': (u,v)=(x,z)"""
    return {'z': (cu+du, cv+dv, a), 'x': (a, cv+dv, cu+du), 'y': (cu+du, a, cv+dv)}[ax]

def tube(b, ax, cu, cv, a0, a1, mat, hollow=True, ring='iron_block', seam='light_gray_concrete',
         stair='smooth_quartz_stairs', seam_every=4):
    """円筒モジュール。mat は文字列 か (基調, 混ぜる素材, 閾値) のタプル（ノイズの塊で混ぜる＝ごま塩にならない）。
    角の階段: 軸 z → facing は x方向(west/east)、軸 x → z方向(north/south)。上半分の角は half=bottom、下半分は half=top。
    facing は『高い側が向く向き』なので、角(du>0)は内側(-u)を向ける。軸 y は面取り不可なので角を空ける。"""
    for a in range(a0, a1+1):
        cap = a in (a0, a1)
        for du in range(-2, 3):
            for dv in range(-2, 3):
                x, y, z = PT(ax, cu, cv, du, dv, a)
                inner = abs(du) <= 1 and abs(dv) <= 1
                if inner and hollow and not cap: continue
                if abs(du) == 2 and abs(dv) == 2:
                    if ax == 'y': continue
                    f = ('west' if du > 0 else 'east') if ax == 'z' else ('north' if du > 0 else 'south')
                    b.put(x, y, z, stair, **ST(f, 'bottom' if dv > 0 else 'top'))
                    continue
                if cap and not inner: m = ring
                elif seam and (a-a0) % seam_every == 0 and not inner: m = seam
                elif isinstance(mat, tuple): m = mat[1] if noise(x, y, z, 3.2) > mat[2] else mat[0]
                else: m = mat
                b.put(x, y, z, m)

def tube_lights(b, ax, cu, cv, a0, a1, step=3):
    """天井中央に end_rod を下向きで。真上に殻がある所だけ（ハッチ穴の上には置かない）"""
    for a in range(a0+2, a1-1, step):
        x, y, z = PT(ax, cu, cv, 0, 1, a)
        if b.get(*PT(ax, cu, cv, 0, 2, a)) and b.empty(x, y, z): b.put(x, y, z, 'end_rod', facing='down')

def tube_racks(b, ax, cu, cv, a0, a1, mats=('iron_block', 'gray_concrete'), gap_every=3):
    """壁際(du=±1, 床〜腰)にラック。3列ごとに1列あけ、中央(du=0)の通路は必ず残す。書見台などを置く隙間にもなる"""
    for a in range(a0, a1+1):
        if (a-a0) % gap_every == gap_every-1: continue
        for du in (-1, 1):
            for dv in (-1, 0):
                p = PT(ax, cu, cv, du, dv, a)
                if b.empty(*p): b.put(*p, mats[0] if du < 0 else mats[1])

def lattice_truss(b, x0, x1, cz, cy, bay=4, longeron='light_gray_concrete', frame='iron_block'):
    """x 方向のトラス(5x5断面)。角に縦材、bay ごとに枠、枠の中間に面中央の iron_bars（交差点の見立て）"""
    for x in range(x0, x1+1):
        for dz in (-2, 2):
            for dy in (-2, 2): b.put(x, cy+dy, cz+dz, longeron)
        if (x-x0) % bay == 0:
            for dz in range(-2, 3):
                for dy in range(-2, 3):
                    if abs(dz) == 2 or abs(dy) == 2: b.put(x, cy+dy, cz+dz, frame)
        elif (x-x0) % bay == bay//2:
            for dz, dy in ((0, 2), (0, -2), (2, 0), (-2, 0)): b.put(x, cy+dy, cz+dz, 'iron_bars', **FN)

def solar_wing(b, x0, y, z0, z1, width=12, hub=(36, 38), panel='blue_concrete', line='lapis_block',
               edge='raw_gold_block', mast='light_gray_concrete'):
    """太陽電池翼（長さ方向 z、幅方向 x、厚み1）。中央2列がマスト、両縁と先端は金色、5ごとに濃い線。hub 範囲は空ける"""
    mid = width//2
    for x in range(x0, x0+width):
        k = x-x0
        for z in range(z0, z1+1):
            if hub[0] <= z <= hub[1]: continue
            if k in (mid-1, mid): m = mast
            elif k in (0, width-1) or z in (z0, z1): m = edge
            elif z % 5 == 0 or k in (2, width-3): m = line
            else: m = panel
            b.put(x, y, z, m)

def radiator_panel(b, xs, zs, y, panel='white_concrete', frame='light_gray_concrete', frame_x=(), every=4):
    """平らな白いラジエータ。xs/zs は range か (最小,最大)。frame_x の x と縁・every ごとの z を枠線に"""
    xs = range(xs[0], xs[1]+1) if isinstance(xs, tuple) else xs
    zs = range(zs[0], zs[1]+1) if isinstance(zs, tuple) else zs
    zl = (min(zs), max(zs))
    for x in xs:
        for z in zs:
            b.put(x, y, z, frame if x in frame_x or z in zl or z % every == 0 else panel)
