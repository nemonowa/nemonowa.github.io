"""Axiom ブループリント (.bp) の読み書きライブラリ（依存: Pillow のみ）。Minecraft 26.3 / Axiom の新形式(Version 2)対応。

ファイル構造（共通）:
  u32 magic 0x0AE5BB36
  i32 len + ヘッダNBT（無名ルートCompound）
  i32 len + サムネイルPNG（96x96）
  i32 len + gzip圧縮したブロックNBT
詳細は references/bp_format.md。

形式の違い（実ファイルで確認済み）:
  fmt=1（旧。1.20.4 期 / DataVersion 3700）: Header.Version=Long 1、パレット要素 {Name, Properties}、空き=air、原点=最小角
  fmt=2（新。26.3 / DataVersion 5023）    : Header.Version=Int 2、パレット要素は
        ・プロパティなし → 文字列 'minecraft:dirt'
        ・プロパティあり → {id:'minecraft:chest', properties:{facing:'west',...}}
        ・両者が混ざるセクションは List<Compound> になり、文字列は {'': 'minecraft:dirt'} で包まれる（1.21.5+ の異種リスト）
        空きセルは void_air、セクション座標は負もあり（コピー時の原点基準）。Entities に実体のエンティティNBTが入る。

使い方:
  from bplib import read_bp, write_bp
  bp = read_bp('x.bp')   # dict(header, thumb_png, blocks={(x,y,z):'name[props]'}, raw, fmt, block_entities, entities)
  write_bp('y.bp', blocks, name='名前')                     # 既定=26.3 形式（fmt=2, DataVersion 5023）
  write_bp('y.bp', blocks, name='名前', fmt=1, data_version=3700)   # 旧形式が要る時だけ
blocks は {(x,y,z): ('minecraft:stone', (('k','v'),...))} か {(x,y,z): 'stone[k=v]'} のどちらでもよい。
"""
import struct, gzip, io, math

MAGIC = 0x0AE5BB36
DATA_VERSION = 5023      # Minecraft Java 26.3（ユーザーが 26.3 の Axiom で保存した実ファイルから）
FORMAT = 2               # Axiom の新ブループリント形式（Header.Version=Int 2）
LEGACY_DATA_VERSION = 3700   # 1.20.4。fmt=1 で書くときの既定

EMPTY = ('minecraft:air', 'minecraft:cave_air', 'minecraft:void_air', 'minecraft:structure_void')

# ブロックIDの改名（data_version 以上で書くときに自動で新名へ置換。読むときは旧名→新名へ寄せる）
RENAMES = [
    (3698, {'minecraft:grass': 'minecraft:short_grass'}),          # 1.20.3
    (4541, {'minecraft:chain': 'minecraft:iron_chain'}),           # 1.21.9（銅の鎖の追加に伴う改名）
]

def rename_for(name, data_version):
    """data_version で有効な名前に寄せる（新しい版へは改名、旧形式で書くときは旧名へ戻す）"""
    for dv, m in RENAMES:
        if data_version >= dv and name in m: name = m[name]
    for dv, m in reversed(RENAMES):
        if data_version < dv:
            back = {v: k for k, v in m.items()}
            if name in back: name = back[name]
    return name

# ---------------------------------------------------------------- NBT 読み
class _R:
    def __init__(s, b): s.b = b; s.p = 0
    def r(s, n): v = s.b[s.p:s.p+n]; s.p += n; return v
    def u(s, f): return struct.unpack('>'+f, s.r(struct.calcsize('>'+f)))[0]

def _tag(r, t, typed=False):
    """typed=True なら (型番号, 値) の組で返す（読み込んだ BE/エンティティを型を保ったまま書き戻すため）"""
    if t == 1: v = r.u('b')
    elif t == 2: v = r.u('h')
    elif t == 3: v = r.u('i')
    elif t == 4: v = r.u('q')
    elif t == 5: v = r.u('f')
    elif t == 6: v = r.u('d')
    elif t == 7: n = r.u('i'); v = r.r(n)
    elif t == 8: n = r.u('H'); v = r.r(n).decode('utf8', 'replace')
    elif t == 9:
        et = r.u('b'); n = r.u('i'); items = [_tag(r, et, typed) for _ in range(n)]
        if typed: return (9, (et, [i[1] for i in items]))
        return items
    elif t == 10:
        d = {}
        while True:
            et = r.u('b')
            if et == 0: break
            k = _tag(r, 8); d[k] = _tag(r, et, typed)
        v = d
    elif t == 11: n = r.u('i'); v = list(struct.unpack('>%di' % n, r.r(4*n)))
    elif t == 12: n = r.u('i'); v = list(struct.unpack('>%dq' % n, r.r(8*n)))
    else: raise ValueError('bad tag %d' % t)
    return (t, v) if typed else v

def nbt_read(b, typed=False):
    r = _R(b); t = r.u('b'); _tag(r, 8); return _tag(r, t, typed)

def untyped(tv):
    """(型, 値) 形式 → 素の Python 値"""
    t, v = tv
    if t == 10: return {k: untyped(x) for k, x in v.items()}
    if t == 9: return [untyped((v[0], x)) for x in v[1]]
    return v

# ---------------------------------------------------------------- NBT 書き（型付き値 (type, value)）
def _s(x): b = x.encode(); return struct.pack('>H', len(b)) + b
def _payload(t, v):
    if t == 1: return struct.pack('>b', v)
    if t == 2: return struct.pack('>h', v)
    if t == 3: return struct.pack('>i', v)
    if t == 4: return struct.pack('>q', v)
    if t == 5: return struct.pack('>f', v)
    if t == 6: return struct.pack('>d', v)
    if t == 7: return struct.pack('>i', len(v)) + bytes(v)
    if t == 8: return _s(v)
    if t == 9:
        et, items = v
        return struct.pack('>bi', et if items else 0, len(items)) + b''.join(_payload(et, i) for i in items)
    if t == 10:
        return b''.join(struct.pack('>b', tt) + _s(k) + _payload(tt, vv) for k, (tt, vv) in v.items()) + b'\0'
    if t == 11: return struct.pack('>i', len(v)) + struct.pack('>%di' % len(v), *v)
    if t == 12: return struct.pack('>i', len(v)) + struct.pack('>%dq' % len(v), *v)
    raise ValueError(t)
def nbt_root(compound): return b'\x0a' + _s('') + _payload(10, compound)

def hetero_list(items):
    """1.21.5+ の異種リスト。items=[(型,値),...]。全部同じ型ならそのまま、混ざるなら Compound 以外を {'': 値} で包む"""
    types = {t for t, _ in items}
    if len(types) <= 1:
        return (9, (items[0][0] if items else 0, [v for _, v in items]))
    return (9, (10, [v if t == 10 else {'': (t, v)} for t, v in items]))

# 便利な型付きコンストラクタ（BE/エンティティを書くとき用）
def B(v): return (1, int(v))
def Sh(v): return (2, int(v))
def I(v): return (3, int(v))
def L(v): return (4, int(v))
def F(v): return (5, float(v))
def D(v): return (6, float(v))
def S(v): return (8, str(v))
def C(**kw): return (10, kw)
def Ls(t, items): return (9, (t, list(items)))

# ---------------------------------------------------------------- ブロック状態の正規化
def _norm(v):
    """-> ('minecraft:name', (('k','v'),...))"""
    if isinstance(v, str):
        name, props = v, ()
        if '[' in v:
            name, rest = v.split('[', 1)
            props = tuple(sorted(tuple(kv.split('=', 1)) for kv in rest.rstrip(']').split(',') if kv))
        if ':' not in name: name = 'minecraft:' + name
        return (name, props)
    name, props = v
    if ':' not in name: name = 'minecraft:' + name
    return (name, tuple(sorted((k, str(val)) for k, val in props)))

def state_str(name, props):
    n = name.replace('minecraft:', '')
    return n + ('[' + ','.join(f'{k}={v}' for k, v in props) + ']' if props else '')

def _pal_entry(p):
    """パレット要素（v1/v2 のどちらでも）→ (name, props)"""
    if isinstance(p, str): return p, ()
    if '' in p and len(p) == 1: return p[''], ()                     # 異種リストで包まれた文字列
    name = p.get('id') or p.get('Name')
    props = p.get('properties') or p.get('Properties') or {}
    return name, tuple(sorted(props.items()))

# ---------------------------------------------------------------- 読み込み
def read_bp(path, keep_air=False):
    """keep_air=True なら明示的な air も blocks に残す（Paste Air 用の空気を調べるとき）。void_air/structure_void は常に空き扱い"""
    d = open(path, 'rb').read(); r = _R(d)
    if r.u('I') != MAGIC: raise ValueError('Axiom .bp ではありません')
    header = nbt_read(r.r(r.u('i')))
    thumb = r.r(r.u('i'))
    body = gzip.decompress(r.r(r.u('i')))
    raw = nbt_read(body)
    traw = nbt_read(body, typed=True)[1]
    dv = raw.get('DataVersion', 0)
    blocks = {}
    for reg in raw['BlockRegion']:
        X, Y, Z = reg['X']*16, reg['Y']*16, reg['Z']*16
        st = reg['BlockStates']
        pal = []
        for p in st['palette']:
            n, pr = _pal_entry(p)
            pal.append(None if (n in EMPTY and not (keep_air and n == 'minecraft:air')) else state_str(rename_for(n, 10**9), pr))
        data = st.get('data', [])
        if len(pal) == 1 or not data:
            idx = [0]*4096
        else:
            bits = max(4, math.ceil(math.log2(len(pal)))); per = 64 // bits; m = (1 << bits) - 1; idx = []
            for Lg in data:
                Lg &= (1 << 64) - 1
                for k in range(per): idx.append((Lg >> (k*bits)) & m)
        for i in range(4096):
            s = pal[idx[i]]
            if s is None: continue
            blocks[(X+(i & 15), Y+(i >> 8), Z+((i >> 4) & 15))] = s
    v = header.get('Version', 1)
    fmt = 2 if (v >= 2 or any(isinstance(p, str) or 'id' in p or '' in p for reg in raw['BlockRegion'] for p in reg['BlockStates']['palette'])) else 1
    return dict(header=header, thumb_png=thumb, blocks=blocks, raw=raw, fmt=fmt, data_version=dv,
                block_entities=traw.get('BlockEntities', (9, (10, [])))[1][1],     # 型付き Compound のリスト（そのまま書き戻せる）
                entities=traw.get('Entities', (9, (10, [])))[1][1])

# ---------------------------------------------------------------- サムネイル（等角投影）
def make_thumbnail(blocks, size=96):
    from PIL import Image, ImageDraw
    from colors import col
    S_ = 4; img = Image.new('RGBA', (size*S_, size*S_), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    occ = set(blocks)
    keys = [k for k in blocks if not all(n in occ for n in ((k[0]+1, k[1], k[2]), (k[0], k[1]+1, k[2]), (k[0], k[1], k[2]+1)))]
    if not keys: keys = list(blocks)
    keys.sort(key=lambda k: (k[0]+k[2], k[1]))
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]; zs = [k[2] for k in keys]
    W = max(max(xs)-min(xs)+max(zs)-min(zs), (max(ys)-min(ys))*1.3) + 2
    t = size*S_/W*0.62
    pts = [((x-z)*t*.866, (x+z)*t*.5-y*t) for x, y, z in keys]
    ox = size*S_/2-(min(p[0] for p in pts)+max(p[0] for p in pts))/2
    oy = size*S_/2-(min(p[1] for p in pts)+max(p[1] for p in pts))/2
    for k, (px, py) in zip(keys, pts):
        h = col(blocks[k][0] if isinstance(blocks[k], tuple) else blocks[k]); c = (h >> 16, h >> 8 & 255, h & 255)
        cx, cy = px+ox, py+oy; w = t*.866; hh = t*.5
        sh = lambda f: tuple(int(v*f) for v in c)
        d.polygon([(cx-w, cy), (cx, cy+hh), (cx, cy+hh+t), (cx-w, cy+t)], sh(.7))
        d.polygon([(cx+w, cy), (cx, cy+hh), (cx, cy+hh+t), (cx+w, cy+t)], sh(.85))
        d.polygon([(cx, cy-hh), (cx+w, cy), (cx, cy+hh), (cx-w, cy)], c)
    img = img.resize((size, size), Image.LANCZOS); bio = io.BytesIO(); img.save(bio, 'PNG', optimize=True)
    return bio.getvalue()

# ---------------------------------------------------------------- 書き出し
def _palette_nbt(pal, fmt):
    if fmt == 1:
        return (9, (10, [{'Name': (8, n), **({'Properties': (10, {k: (8, vv) for k, vv in p})} if p else {})} for n, p in pal]))
    items = [(8, n) if not p else (10, {'id': (8, n), 'properties': (10, {k: (8, vv) for k, vv in p})}) for n, p in pal]
    return hetero_list(items)

def write_bp(path, blocks, name, author='nemo', tags=(), data_version=None, thumb_png=None, block_entities=None,
             entities=None, fmt=FORMAT, origin='min', paste_air=False):
    """blocks: {(x,y,z): state}。戻り値=ブロック数（ヘッダ BlockCount）。
    fmt=2（既定）: 26.3 の Axiom 形式。fmt=1: 旧形式。
    origin='min'   : 最小角を (0,0,0) に寄せる（従来どおり。貼り付け位置＝最小角）
           'bottom_center': 底面の中心を (0,0,0) に（Axiom は相対座標をそのまま使うので、中心基準で回しやすい）
           'keep'  : 渡した座標のまま（負の座標も可。26.3 の実ファイルもコピー時の原点基準で負座標を含む）
           (x,y,z) : その点を原点に
    paste_air=True: blocks 内の明示的な 'air' を残し ContainsAir=1 で書く（Paste Air なしでも地形を削れる。実機未確認△）
    block_entities: [(x,y,z, {型付きNBT}), ...]（ワールド座標。対応ブロックの無い座標は捨てる）
    entities: [{型付きNBT（Pos は (6,…) の3要素 List<Double>、ワールド座標）}, ...]"""
    if data_version is None: data_version = DATA_VERSION if fmt >= 2 else LEGACY_DATA_VERSION
    Bk = {}
    for k, v in blocks.items():
        n = _norm(v)
        if n[0] in EMPTY and not (paste_air and n[0] == 'minecraft:air'): continue
        Bk[k] = (rename_for(n[0], data_version), n[1])
    if not Bk: raise ValueError('ブロックがありません')
    xs = [k[0] for k in Bk]; ys = [k[1] for k in Bk]; zs = [k[2] for k in Bk]
    if origin == 'min': mx, my, mz = min(xs), min(ys), min(zs)
    elif origin == 'bottom_center': mx, my, mz = (min(xs)+max(xs))//2, min(ys), (min(zs)+max(zs))//2
    elif origin == 'keep': mx = my = mz = 0
    else: mx, my, mz = origin
    Bk = {(x-mx, y-my, z-mz): v for (x, y, z), v in Bk.items()}
    secs = {}
    for (x, y, z), v in Bk.items(): secs.setdefault((x >> 4, y >> 4, z >> 4), {})[(x & 15, y & 15, z & 15)] = v
    filler = ('minecraft:void_air', ()) if fmt >= 2 else ('minecraft:air', ())
    regions = []
    for (sx, sy, sz), m in sorted(secs.items()):
        pal = [filler] + sorted(set(m.values()) - {filler})      # 0番=空き（v2 は void_air。サンプルと同じ）
        idx = {p: i for i, p in enumerate(pal)}
        bits = max(4, math.ceil(math.log2(len(pal)))); per = 64 // bits   # 1.16+：エントリは long を跨がない
        arr = [0]*4096
        for (x, y, z), v in m.items(): arr[y*256+z*16+x] = idx[v]       # index = y*256 + z*16 + x
        longs = []
        for i in range(0, 4096, per):
            Lg = 0
            for k, a in enumerate(arr[i:i+per]): Lg |= a << (k*bits)
            if Lg >= 1 << 63: Lg -= 1 << 64
            longs.append(Lg)
        regions.append({'X': (3, sx), 'Y': (3, sy), 'Z': (3, sz),
                        'BlockStates': (10, {'palette': _palette_nbt(pal, fmt), 'data': (12, longs)})})
    bes = []
    for (x, y, z, tag) in (block_entities or []):
        rx, ry, rz = x-mx, y-my, z-mz
        if (rx, ry, rz) not in Bk: continue
        tag = dict(tag)
        if fmt >= 2: tag.setdefault('components', (10, {}))          # 26.3 の実ファイルは常に components:{} を持つ
        bes.append({**tag, 'x': (3, rx), 'y': (3, ry), 'z': (3, rz)})
    ents = []
    for e in (entities or []):
        e = dict(e)
        if 'Pos' in e:
            px, py, pz = e['Pos'][1][1]
            e['Pos'] = (9, (6, [float(px-mx), float(py-my), float(pz-mz)]))
        ents.append(e)
    body = nbt_root({'DataVersion': (3, data_version), 'BlockRegion': (9, (10, regions)),
                     'BlockEntities': (9, (10, bes)), 'Entities': (9, (10, ents))})
    png = thumb_png or make_thumbnail(Bk)
    count = len(Bk)
    hdr = nbt_root({'ThumbnailYaw': (5, 135.0), 'ContainsAir': (1, 1 if paste_air and any(v[0] == 'minecraft:air' for v in Bk.values()) else 0),
                    'Version': (3, 2) if fmt >= 2 else (4, 1), 'LockedThumbnail': (1, 0),
                    'BlockCount': (3, count), 'Author': (8, author), 'Tags': (9, (8, list(tags))),
                    'Name': (8, name), 'ThumbnailPitch': (5, 30.0)})
    gz = gzip.compress(body)
    with open(path, 'wb') as f:
        f.write(struct.pack('>I', MAGIC) + struct.pack('>i', len(hdr)) + hdr + struct.pack('>i', len(png)) + png
                + struct.pack('>i', len(gz)) + gz)
    return count

def verify(path, expected_count=None):
    """書き出し後の往復チェック。ヘッダの BlockCount と実ブロック数を比較する（ContainsAir=1 なら air も数える）"""
    bp = read_bp(path, keep_air=True); n = len(bp['blocks'])
    ok = bp['header'].get('BlockCount') == n and (expected_count is None or expected_count == n)
    return ok, n, bp['header']

def describe(path):
    bp = read_bp(path); h = bp['header']; bl = bp['blocks']
    xs = [k[0] for k in bl] or [0]; ys = [k[1] for k in bl] or [0]; zs = [k[2] for k in bl] or [0]
    return (f"{path}: '{h.get('Name')}' by {h.get('Author')} tags={h.get('Tags')} fmt=v{bp['fmt']} (Header.Version={h.get('Version')}) "
            f"DataVersion={bp['data_version']} blocks={len(bl)} header={h.get('BlockCount')} "
            f"size={(max(xs)-min(xs)+1, max(ys)-min(ys)+1, max(zs)-min(zs)+1)} min={(min(xs), min(ys), min(zs))} "
            f"BE={len(bp['block_entities'])} entities={len(bp['entities'])}")

if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]: print(describe(p))
