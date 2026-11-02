"""26.3（DataVersion 5023）向けの BlockEntity / Entity NBT ヘルパー。

根拠: ユーザーが 26.3 の Axiom で保存した実ファイル（スポナー・宝箱・防具立て入り）の NBT をそのまま写した書式。
  - BE: {id, x,y,z, components:{}, ...バニラBE}（x,y,z と components は bplib.write_bp が付ける）
  - スポナーの BE id は 'minecraft:mob_spawner'（ブロック名は spawner）。short 値は型2。
  - テキスト（CustomName 等）は 1.21.5+ の NBT テキストコンポーネント：文字列 or {text:'…', color:'…', bold:1b…}。JSON 文字列ではない。
  - 属性は attributes:[{id:'minecraft:max_health', base:…}]（小文字・1.21+）。
  - エンティティは Entities:[{id, Pos:[d,d,d], Rotation:[f,f], …}]。Pos は BP と同じ座標系（write_bp が最小角基準に直す）。
確度: スポナー・宝箱・防具立ては 26.3 実ファイルで書式確認済み（◎）。書見台の本・看板・額縁・アイテムの components は
      1.20.5+/1.21.5+ のバニラ仕様に基づく（○）。Axiom への貼り付けは未確認なので、/give・/summon コマンドも併せて出す。

使い方:
  from nbt_helpers import *
  b.BE = [chest_loot(x,y,z,'simple_dungeon'), spawner(x,y,z,'zombie', name='番兵', health=40)]
  b.ENT = [armor_stand(x+.5, y, z+.5, name='案内人', yaw=90)]
  b.save(path, '名前')       # Build.save が BE と ENT を書く
"""
import json, random
from bplib import B, Sh, I, F, D, S, C, Ls, hetero_list

# ---------------------------------------------------------------- テキストコンポーネント（NBT）
def text(t, color=None, bold=None, italic=None, plain=False):
    """{text, color, bold, italic} の Compound（26.3 実ファイルの CustomName と同じ形）。plain=True なら文字列 (8,'…')"""
    if plain: return S(t)
    d = {'text': S(t)}
    if color: d['color'] = S(color)
    if bold is not None: d['bold'] = B(bold)
    if italic is not None: d['italic'] = B(italic)
    return (10, d)

def text_list(items):
    """テキストコンポーネントの配列（文字列と Compound が混ざってもよい：異種リスト）"""
    return hetero_list([text(x, plain=True) if isinstance(x, str) else x for x in items])

# ---------------------------------------------------------------- アイテム（1.20.5+ のデータコンポーネント形式）
def item(id_, count=1, components=None, slot=None):
    """{id, count:int, components:{…}}。旧 Count(byte)/tag は使わない"""
    d = {'id': S(id_ if ':' in id_ else 'minecraft:' + id_), 'count': I(count)}
    if components: d['components'] = (10, components)
    if slot is not None: d['Slot'] = B(slot)
    return d

def written_book(title, pages, author='nemo'):
    """minecraft:written_book_content。title/pages は filterable（{raw: …}）。page は文字列テキスト"""
    return item('written_book', 1, {'minecraft:written_book_content': (10, {
        'title': C(raw=S(title)), 'author': S(author), 'generation': I(0), 'resolved': B(1),
        'pages': Ls(10, [{'raw': S(p)} for p in pages])})})

# ---------------------------------------------------------------- ブロックエンティティ
def chest_loot(x, y, z, table='simple_dungeon', seed=None, kind='chest'):
    """宝箱/樽のルートテーブル。table は 'simple_dungeon' でも 'chests/…' でも 'ns:path' でもよい"""
    if ':' not in table:
        if not table.startswith('chests/'): table = 'chests/' + table
        table = 'minecraft:' + table
    d = {'id': S('minecraft:' + kind), 'LootTable': S(table)}
    if seed is not None: d['LootTableSeed'] = (4, int(seed))
    return (x, y, z, d)

def chest_items(x, y, z, items, kind='chest'):
    """中身を直接入れる。items=[('diamond',3), ('iron_ingot',10,{components}), …]（Slot は 0 から順）"""
    lst = []
    for i, it in enumerate(items):
        lst.append(item(it[0], it[1] if len(it) > 1 else 1, it[2] if len(it) > 2 else None, slot=i))
    return (x, y, z, {'id': S('minecraft:' + kind), 'Items': Ls(10, lst)})

def mob(mob_id, name=None, health=None, loot=None, attrs=None, extra=None):
    """スポナー/召喚用のエンティティ NBT（Compound の中身）。attrs={'armor':10, 'movement_speed':.3}"""
    e = {'id': S(mob_id if ':' in mob_id else 'minecraft:' + mob_id)}
    if name: e['CustomName'] = text(name) if isinstance(name, str) else name
    a = dict(attrs or {})
    if health:
        e['Health'] = F(health); a.setdefault('max_health', health)
    if a: e['attributes'] = Ls(10, [{'id': S('minecraft:' + k), 'base': D(v)} for k, v in a.items()])
    if loot: e['DeathLootTable'] = S(loot)
    if extra: e.update(extra)
    return e

def spawner(x, y, z, entity='zombie', count=4, near=6, rng=4, player=16, delay=(200, 800), light=None, potentials=None, **mobkw):
    """スポナー BE（26.3 実ファイルと同じキー・型）。entity は mob id か mob() の戻り値。
    light=(min,max) で custom_spawn_rules.block_light_limit（明るい部屋でも湧かせる）。
    potentials=[(weight, mob()), …] で複数種。既定値は 26.3 実ファイルの値（4体・近傍6・範囲4・16m・200〜800tick）"""
    ent = entity if isinstance(entity, dict) else mob(entity, **mobkw)
    data = {'entity': (10, ent)}
    if light: data['custom_spawn_rules'] = (10, {'block_light_limit': (10, {'min_inclusive': I(light[0]), 'max_inclusive': I(light[1])})})
    pots = [{'weight': I(w), 'data': (10, {'entity': (10, e)})} for w, e in (potentials or [])]
    return (x, y, z, {'id': S('minecraft:mob_spawner'), 'SpawnData': (10, data), 'SpawnPotentials': Ls(10, pots),
                      'SpawnRange': Sh(rng), 'RequiredPlayerRange': Sh(player), 'MaxNearbyEntities': Sh(near),
                      'SpawnCount': Sh(count), 'MinSpawnDelay': Sh(delay[0]), 'MaxSpawnDelay': Sh(delay[1]), 'Delay': Sh(20)})

def lectern(x, y, z, title, pages, author='nemo'):
    """書見台の BE（Book は 1.20.5+ のアイテム形式）。ブロックは lectern[facing,has_book=true,powered=false] を別に置く"""
    return (x, y, z, {'id': S('minecraft:lectern'), 'Page': I(0), 'Book': (10, written_book(title, pages, author))})

def sign(x, y, z, lines, color='black', glow=False, waxed=True, back=None, hanging=False):
    """看板 BE。messages は4つのテキストコンポーネント（1.21.5+ は NBT。プレーン文字列でよい）"""
    def side(ls, c, g):
        ls = (list(ls) + [''] * 4)[:4]
        return (10, {'color': S(c), 'has_glowing_text': B(1 if g else 0), 'messages': text_list(ls)})
    return (x, y, z, {'id': S('minecraft:hanging_sign' if hanging else 'minecraft:sign'), 'is_waxed': B(1 if waxed else 0),
                      'front_text': side(lines, color, glow), 'back_text': side(back or [], 'black', False)})

# ---------------------------------------------------------------- エンティティ（Entities 欄）
def _uuid(seed):
    r = random.Random(seed); return [r.randint(-2**31, 2**31-1) for _ in range(4)]

def entity(id_, x, y, z, yaw=0.0, pitch=0.0, uuid_seed=None, **nbt):
    """汎用エンティティ。x,y,z はワールド座標（ブロック中央に立たせるなら +0.5）。nbt は型付き値"""
    e = {'id': S(id_ if ':' in id_ else 'minecraft:' + id_), 'Pos': Ls(6, [float(x), float(y), float(z)]),
         'Rotation': Ls(5, [float(yaw), float(pitch)]), 'Motion': Ls(6, [0.0, 0.0, 0.0])}
    if uuid_seed is not None: e['UUID'] = (11, _uuid(uuid_seed))
    e.update(nbt)
    return e

def armor_stand(x, y, z, name=None, yaw=0.0, invisible=False, small=False, arms=True, no_base=False, gravity=True, tags=(), **nbt):
    """防具立て（26.3 実ファイルの書式）。name は文字列か text(...)。yaw: 0=南,90=西,180=北,-90=東"""
    kw = {'Invisible': B(invisible), 'Small': B(small), 'ShowArms': B(arms), 'NoBasePlate': B(no_base), 'NoGravity': B(not gravity)}
    if name is not None:
        kw['CustomName'] = text(name) if isinstance(name, str) else name; kw['CustomNameVisible'] = B(1)
    if tags: kw['Tags'] = Ls(8, list(tags))
    kw.update(nbt)
    return entity('armor_stand', x, y, z, yaw=yaw, **kw)

def item_frame(x, y, z, facing, held=None, glow=False, fixed=True, invisible=False):
    """額縁。x,y,z は額縁のあるブロック座標（中心に置く）。facing: 0=下 1=上 2=北 3=南 4=西 5=東（壁から離れる向き）"""
    off = {2: (0, 0, .46875), 3: (0, 0, -.46875), 4: (.46875, 0, 0), 5: (-.46875, 0, 0), 0: (0, .46875, 0), 1: (0, -.46875, 0)}[facing]
    kw = {'Facing': B(facing), 'Fixed': B(fixed), 'Invisible': B(invisible), 'TileX': I(x), 'TileY': I(y), 'TileZ': I(z)}
    if held: kw['Item'] = (10, item(*held) if isinstance(held, tuple) else item(held))
    return entity('glow_item_frame' if glow else 'item_frame', x+.5+off[0], y+.5+off[1], z+.5+off[2], **kw)

# ---------------------------------------------------------------- コマンド（BE が読めなかった時の保険。26.3 の SNBT 書式）
def _snbt_str(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def give_book_command(title, pages, author='nemo'):
    """1.20.5+ の /give（コンポーネント構文）。ページは文字列テキスト"""
    return ('/give @p written_book[written_book_content={title:%s,author:%s,pages:[%s]}]'
            % (_snbt_str(title), _snbt_str(author), ','.join(_snbt_str(p) for p in pages)))

def summon_command(mob_id, rel=(0, 0, 0), name=None, health=None):
    parts = []
    if name: parts.append('CustomName:%s' % _snbt_str(name))
    if health: parts += ['Health:%sf' % float(health), 'attributes:[{id:"minecraft:max_health",base:%s}]' % float(health)]
    return '/summon minecraft:%s ~%d ~%d ~%d {%s}' % (mob_id, rel[0], rel[1], rel[2], ','.join(parts + ['PersistenceRequired:1b']))
