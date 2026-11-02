# BlockEntities・Entities（宝箱の中身・スポナー・書見台・看板・防具立て）を BP に書く（26.3 版）

## 根拠
- ◎ **26.3 の実ファイル**（ユーザーが 26.3 の Axiom で保存。`examples/format_check_26_3/sample_26.3.bp`）に、スポナー・宝箱の BE と防具立ての Entity が入っていた。キー・型はそれに合わせている（`bp_format.md`）。
- ◎ Axiom 1.5.0 の更新履歴「Blueprints & Schematics now support saving/pasting Block Entities with NBT」。
- 実機：宝箱の LootTable とスポナーは旧版（1.20.4 形式で書いた BP）でも正しく読み込まれた（ユーザー確認 2026-10-29）。26.3 形式で書いた BP の実機確認は `examples/format_check_26_3/format_check.py` の出力で行う（**未確認**）。

## 書式（26.3 / DataVersion 5023）
- ルートの `BlockEntities: List<Compound>`。各要素 = `id` + `x,y,z`（Int・BP 内の相対座標）+ **`components:{}`** + バニラの BE NBT。`write_bp` が座標の相対化と `components` を付ける。
- ルートの `Entities: List<Compound>`。各要素 = 完全なエンティティ NBT（`id`, `Pos:[d,d,d]`, `Rotation:[f,f]`, `Motion`, `UUID` …）。`Pos` もブロックと同じ相対座標。
- **テキスト**は NBT のテキストコンポーネント（1.21.5+）：`CustomName:{text:'…', color:'…', bold:1b}`。看板の `messages` は4要素（文字列でよい）。旧 1.20.4 の JSON 文字列 `'{"text":"…"}'` は使わない。
- **アイテム**は 1.20.5+ の形式：`{id, count:Int, components:{…}}`（旧 `Count:byte` / `tag:{}` は使わない）。

## ヘルパー（`scripts/nbt_helpers.py`。型付き値は bplib の `B Sh I F D S C Ls`）
| 用途 | 関数 | 備考 |
|---|---|---|
| 宝箱/樽のルートテーブル | `chest_loot(x,y,z,'simple_dungeon', kind='chest')` | 'chests/…' や 'ns:path' も可 |
| 中身を直接 | `chest_items(x,y,z,[('diamond',3),…])` | Slot は 0 から |
| スポナー | `spawner(x,y,z,'zombie', name=, health=, loot=, attrs=, light=(0,15), potentials=)` | 既定値は 26.3 実例（4体・近傍6・範囲4・16m・200〜800tick）。short は型2 |
| モブの NBT | `mob('zombie', name, health, loot, attrs)` | `attributes:[{id,base}]` |
| 書見台の本 | `lectern(x,y,z,title,pages)` | `Book:{id:'minecraft:written_book',count:1,components:{'minecraft:written_book_content':{title:{raw},author,generation,resolved,pages:[{raw:'…'}]}}}` |
| 看板 | `sign(x,y,z,lines,color,glow,waxed,hanging=)` | 吊り看板は id `minecraft:hanging_sign` |
| 防具立て | `armor_stand(x,y,z,name,yaw,invisible,small,arms,gravity,tags)` | 26.3 実例と同じキー |
| 額縁 | `item_frame(x,y,z,facing,held)` | △ 未確認 |
| 汎用エンティティ | `entity(id,x,y,z,yaw,pitch,**nbt)` | |
| 保険コマンド | `give_book_command(title,pages)` / `summon_command(mob,rel,name,health)` | 26.3 の SNBT（コンポーネント構文） |

- 既存の `dungeon_kit.chest_be / spawner_be`、`interior_helpers.lectern_with_book / wall_sign` はそのまま使える（内部で 26.3 形式を書く）。
- `Build` に `b.BE=[…]`（BE）と `b.ENT=[…]`（エンティティ）を入れて `b.save()`。

```python
from builder import *
from nbt_helpers import chest_loot, spawner, armor_stand
b = Build(); b.BE = []; b.ENT = []
b.put(0,0,0,'spawner');  b.BE.append(spawner(0,0,0,'zombie', name='番兵', health=40, light=(0,15)))
b.put(0,0,1,'chest', facing='west', type='single', waterlogged='false'); b.BE.append(chest_loot(0,0,1,'simple_dungeon'))
b.ENT.append(armor_stand(0.5, 1, -0.5, name='案内人', yaw=90))
b.save('x.bp', '例')
```

## 検証
- `read_bp(p)['block_entities']` / `['entities']` は**型付き**で返る（そのまま `write_bp` に渡せる）。各 BE の座標にブロックがあるかを突き合わせる（無い座標の BE は `write_bp` が捨てる → 家具や壁で上書きしていないか確認。城の H 節）。
- 実機で確認してほしい点を返答に書く：26.3 形式での宝箱・スポナー（旧形式では確認済み）、書見台の本、看板、エンティティ（Paste Entities が必要）。

## 書見台・看板の BEなし版
- 書見台を `has_book=false` で置き直し、`b.BE=[]` にして別ファイルへ保存。本は `/give` コマンドで渡す（`give_book_command`）。
- `/give @p written_book[written_book_content={title:"…",author:"nemo",pages:["…","…"]}]`（26.3。文字列ページはそのままテキストになる）。

## 旧形式で書く必要があるとき
- `b.save(path, name, fmt=1)`（DataVersion 3700）。BE は今の書式（components 形式のアイテム）のままなので、1.20.4 の本は `tag` 形式で別途書く必要がある。原則として 26.3 形式で書く。
