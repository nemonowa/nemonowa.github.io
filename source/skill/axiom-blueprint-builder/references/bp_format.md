# Axiom .bp ファイル形式（Minecraft 26.3 対応版）

`scripts/bplib.py` がすべて実装している。根拠：
- **新形式（v2）**：ユーザーが **Minecraft 26.3 の Axiom で実際に保存した .bp**（`examples/format_check_26_3/sample_26.3.bp`、スポナー・宝箱・防具立て入り）をバイト単位で解析（◎ 2026-11-02）。`bplib` で読み→書き直した結果は、キー順・セクション順・パレット順以外は同一。
- **旧形式（v1）**：1.20.4 期の実ファイル20件の解析と往復テスト（◎）。

## 全体構造（ビッグエンディアン。v1/v2 共通）

| 項目 | 型 | 内容 |
|---|---|---|
| magic | u32 | `0x0AE5BB36` |
| header_len + header | i32 + bytes | 無名ルートの**非圧縮** NBT Compound |
| thumb_len + thumb | i32 + bytes | PNG（96×96） |
| block_len + block | i32 + bytes | **gzip 圧縮**された NBT Compound |

## ヘッダ NBT

| キー | v2（26.3） | v1（旧） | 備考 |
|---|---|---|---|
| Name | String | String | 日本語OK |
| Author | String | String | 26.3 実例は `argonaute_nemo`。スキルの既定は `nemo` |
| Tags | List<String>（空なら List<End>） | 同 | |
| **Version** | **Int 2** | Long 1 | **型が違う**。v2 は Int |
| BlockCount | Int | Int | 空き（void_air）以外の数。ContainsAir=1 なら air も数える |
| ContainsAir | Byte 0 | Byte 0 | |
| LockedThumbnail | Byte 0 | Byte 0 | |
| ThumbnailYaw / ThumbnailPitch | Float 135 / 30 | 同 | |

## ブロック NBT

```
{ DataVersion: Int  (26.3 = 5023 / 1.20.4 = 3700),
  BlockRegion: List<Compound> [
     { X: Int, Y: Int, Z: Int,                // 16³ セクション座標（ブロック座標 >> 4）。v2 は負もある
       BlockStates: { palette: <下記>, data: LongArray } } ],
  BlockEntities: List<Compound>,
  Entities: List<Compound> }
```

### パレット（ここが v1 と v2 で違う）
| | v1 | v2（26.3） |
|---|---|---|
| プロパティなし | `{Name:'minecraft:dirt'}` | **文字列** `'minecraft:dirt'` |
| プロパティあり | `{Name:'minecraft:chest', Properties:{facing:'west',…}}` | **`{id:'minecraft:chest', properties:{facing:'west',…}}`**（小文字） |
| 混在するセクション | — | 1.21.5+ の**異種リスト**：`List<Compound>` になり、文字列要素は **`{'': 'minecraft:dirt'}`**（空キーの Compound）で包まれる |
| 全部プロパティなし | — | `List<String>` |
| 空きセル | `minecraft:air`（0番） | **`minecraft:void_air`**（どこに入るかは不定。bplib は0番に置く） |

- セクション内インデックス = `y*256 + z*16 + x`。1要素のビット数 = `max(4, ceil(log2(パレット長)))`、1 long に `64//bits` 個を下位から詰め、long を跨がない（1.16+）。long は符号付き。v2 実例も同じ（4bit・256 long）。
- 読むときは `air / cave_air / void_air / structure_void` を空き扱い（`read_bp(keep_air=True)` で明示的な air を残せる）。

### 座標の原点
- v2 実例はセクション座標に負（Y=-1, Z=-1）があり、ブロックはコピー時の原点（Axiom のクリップボード基準）からの相対座標。**最小角＝原点とは限らない**。
- `write_bp(origin=…)`：`'min'`（既定。従来どおり最小角を 0）／`'bottom_center'`（底面中心を 0。回転の軸が中央になる）／`'keep'`（渡した座標のまま）／`(x,y,z)`。BlockEntities の x,y,z と Entities の Pos も同じだけずらす。

## BlockEntities（26.3 実例）
```
{ id:'minecraft:mob_spawner', x:Int, y:Int, z:Int, components:{},           // スポナーの BE id は mob_spawner（ブロック名は spawner）
  SpawnData:{ entity:{ id:'minecraft:zombie', CustomName:{text:'被害者Z'}, Health:Float 100,
                       attributes:[{id:'minecraft:max_health', base:100}, …], DeathLootTable:'ns:path', CanPickUpLoot:1b } },
  SpawnPotentials:[], SpawnCount:Short 4, SpawnRange:Short 4, RequiredPlayerRange:Short 16, MaxNearbyEntities:Short 6,
  MinSpawnDelay:Short 200, MaxSpawnDelay:Short 800, Delay:Short 371 }
{ id:'minecraft:chest', x, y, z, components:{}, Items:[] }
```
- **全 BE に `components:{}`** が付く（bplib は v2 で自動付与）。座標は BP 内の相対座標（ブロックと同じ座標系）。
- テキストは **NBT のテキストコンポーネント**（`CustomName:{text:'…', color:'dark_gray', bold:1b, italic:0b}`）。1.20.4 の JSON 文字列ではない。
- 属性は小文字の `attributes:[{id, base}]`。
- 書き方の詳細・ヘルパーは `block_entities.md` と `scripts/nbt_helpers.py`。

## Entities（26.3 実例。v2 で初めて実物を確認）
```
{ id:'minecraft:armor_stand', Pos:[Double 0.5, 0.0, -0.5], Rotation:[Float 90, 0], Motion:[0d,0d,0d],
  UUID:IntArray[4], CustomName:{text:'解放されたSK', color:'dark_gray', bold:1b, italic:0b},
  Tags:[…], NoGravity:1b, ShowArms:1b, Invisible:0b, Small:0b, NoBasePlate:0b, Health:20f, attributes:[…], … }
```
- `Pos` はブロックと同じ座標系の実数（ブロック中央は +0.5）。完全なエンティティ NBT（Brain・fall_distance 等）が入るが、書くときは id/Pos/Rotation と必要なキーだけでよい（△：最小構成での貼り付けは実機未確認）。
- 貼り付け時は Axiom の **Paste Entities** を有効にする（research_notes §A）。

## 検証のしかた
- `python3 scripts/bplib.py file.bp` → 形式（v1/v2）・DataVersion・BlockCount 一致・サイズ・最小角・BE/エンティティ数を表示。
- `Build.save()` は書き出し直後に `verify()` で往復チェックする。
- 手持ちの .bp の DataVersion は `read_bp(p)['data_version']`。26.3 は 5023。

## ブロック名の改名（bplib.RENAMES で自動変換）
| 版（DataVersion） | 旧 → 新 |
|---|---|
| 1.20.3（3698） | `grass` → `short_grass` |
| 1.21.9（4541〜） | `chain` → `iron_chain`（銅の鎖の追加に伴う。○ 複数の変換ツール・Wiki） |
- 書き出す DataVersion に合わせて自動で新名へ（旧形式 fmt=1 で書くときは旧名へ戻す）。読むときは新名へ寄せる。
