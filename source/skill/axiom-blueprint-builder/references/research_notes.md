# 調査メモ（2026-10-29 初版、2026-11-02 に 26.3 対応で更新。確度つき）
◎=公式/一次資料、○=複数の二次資料や列挙名、△=推論・記憶（調査では未確認）。実機で確認できたものは「実機」と書く。

## A. Axiom 公式ドキュメント（axiomdocs.moulberry.com。最終更新表記 20/Oct/24 なので古い可能性あり）
- ◎ **ブループリントの作り方**：クリップボードの内容を Ctrl+P → 名前・作者(authors)・タグ・サムネ（回転で生成）を付けて .bp 保存。保存先は `.minecraft/config/axiom/blueprints`（`axiom.hocon` で変更可）。`config/axiom` には blueprints / heightmaps / tool presets の3フォルダ。
- ◎ **サブフォルダ可**：ブループリントのフォルダは入れ子にできる（例：木は trees/ にまとめる）。ブラウザは「Search inside Folders」で再帰検索、タグ・作者・名前でも検索。→ 複数作品を渡す時は**用途別フォルダ＋タグ**で整理する（例：`dungeon/`、`space/`、`pattern/`）。作者は **nemo**。
- ◎ マルチプレイでは、ブループリントをサーバーに保存・ダウンロードでき、サーバーの全員が使える。
- ◎ **貼り付け（Placement）**：Ctrl+V で配置開始 → Gizmo で移動・回転 → Enter か Ctrl+V で確定、Delete/Backspace で取消。Ctrl+R で90°回転、Ctrl+F で反転。オプション：Keep Existing（既存ブロックを上書きしない）／Merge Blocks（形状で合成）／**Paste Air**（空気も貼って既存ブロックを消す）／Paste Entities／Unlock Rotation（任意角）／Snap to ground／Paste Copy／Paste and Select。
  - 使い分け（△推論）：地形の中にダンジョンを埋めるなら **Paste Air**、既存の地形や建物に重ねるなら **Keep Existing**、空中の島はどちらでもよい。
  - 任意角の回転・拡大縮小は Nearest Neighbour / RotSprite / Scale2x という画像処理方式で、階段・扉・レバーなどの**向きの情報が崩れる恐れ**がある（△）。ダンジョンや内装のある作品は90°刻みを勧める。
- ◎ **No Updates**（コンテキストメニュー > Capabilities）：ブロックと隣接ブロックを現状で固定し、形状・隣接更新を止める。非バニラ状態の階段・柵・壁が元に戻るのを防ぐ。→ 貼り付け後に周囲を触る・壊す作業を案内する時に添える。
- ○ 変換系のMOD：LTB（Litematica→.bp。1.21.5〜1.21.11 対応、26.x は別ビルドが必要）、DBTools（blueprint⇄schematic の一括変換）。.bp は Axiom 内部の形式で litematic とパック方式が違う。

## B. Minecraft の版と .bp の形式（2026-11-02 更新）
- ◎ **ユーザーの 26.3 実ファイル**：Axiom の .bp は Header.Version=**Int 2**、DataVersion=**5023**、パレットは「文字列 or {id, properties}」の異種リスト、空き=void_air、セクション座標に負あり、BE に components:{}、Entities に防具立て（詳細 `bp_format.md`）。**スキルの既定はこの形式で書く**（`bplib.FORMAT=2`）。旧形式（Version Long 1 / {Name,Properties} / DataVersion 3700）も読める・`fmt=1` で書ける。
- ○ 26.x の流れ：26.1「Tiny Takeover」（2026-03。子供モブの刷新・ゴールデンタンポポ）→ 26.2「Chaos Cubed」（2026-06-16。硫黄の洞窟・Sulfur/Cinnabar の建材一式＝通常・磨き・レンガ・模様入り、各ハーフ/階段/壁、Sulfur Spike、Potent Sulfur）→ 26.3「Wilderness Bound」（2026-09。Dappled Forest・**ポプラ(poplar)の木材一式**と赤/橙/黄の葉、棚茸(shelf mushroom)、**羊毛の階段・ハーフ**、クッション、**コンクリートの階段・ハーフ**、藁のベッド、赤い低木、Abandoned Camps）（[Beebom](https://beebom.com/minecraft-26-3-wilderness-bound-update-live-now/)、[ggservers 26.2](https://ggservers.com/blog/minecraft-java-edition-26-2-everything-you-need-to-know-about-the-chaos-cubed-update/)、[bisecthosting Dappled Forest](https://www.bisecthosting.com/blog/minecraft-dappled-forest-guide-poplar-trees-blocks-more)）。
  - △ **新ブロックの ID は一次資料で確認できていない**（`poplar_planks` `cinnabar_bricks` `white_wool_stairs` `red_concrete_slab` などは命名規則からの推測）。使う前にユーザーの手持ち .bp かゲーム内 F3 で確認。`colors.py` の `KEYWORDS_26` に仮の色を入れてある。
- ◎/○ **1.21.9（銅の時代）で `chain` → `iron_chain` に改名**（変換ツール nucleation の v4541 データ変換、yog の rename 表、Wiki）。同時に銅の鎖・銅の格子・銅のランタン・銅の松明・銅のチェスト・銅のゴーレム像・木の棚（shelf）が追加。`bplib.RENAMES` が自動変換する。
- ○ 1.20.5 以降、アイテムは NBT の `tag` ではなく**データコンポーネント**（`count:int, components:{…}`）。1.21.5 以降、テキストは JSON 文字列でなく **NBT のテキストコンポーネント**、リストは**異種混在可**（Compound 以外は `{'':値}` で包む）。看板の messages は文字列か Compound（[MC-279252](https://bugs.mojang.com/browse/MC-279252)）。
- 実機：旧形式で書いた宝箱の LootTable とスポナーは正しく読み込まれた（2026-10-29）。26.3 形式で書いた BP は `examples/format_check_26_3` で確認してもらう（未確認）。

## C. レバーと鉄の扉（Minecraft Wiki「Lever」）
- ◎ レバーが ON の間：隣接する**機械部品**（扉・ピストン・ランプ等）を作動させる／**取り付け先ブロックを強く動力化**する（取り付け先が完全な不透明ブロックのときだけ）／隣接する赤石粉に動力を渡す。
- → 扉の隣のマスの壁に付けたレバーは扉に直接効く。扉の隣の**壁ブロック**に付けたレバーは、そのブロックが動力化されて扉に効く（このときは石レンガ等の完全ブロックに付ける。階段・ハーフ・ガラスは不可）。
- 実機：床置き・片側だけだと帰りにくいという指摘を受けた → **両側・壁付け**が規約（`door_levers`、`check_doors`、`check_return`）。

## D. ダンジョン設計の原則（Boss Keys（GMTK）、Boris the Brave「Lock and Key Dungeons」、Solarus フォーラム「Dungeon Design as Lesson Planning」、Cyclic Dungeon Generation）
- ○ **施錠を先に、鍵は後に**：鍵を見つけてから錠を探すより、先に錠を見て鍵を探しに行くほうが満足度が高い。錠はプレイヤーの道中に置く。
- ○ **錠と鍵が遠いほど難しい**：序盤は近く、終盤は遠く。鍵を取った後は、**ループで錠の近くへ戻す**（長い廊下の端に鍵があり、取ったら全部歩いて戻る＝最悪のバックトラック）。
- ○ **枝分かれと隠し近道**：クリティカルパスから部屋を枝分かれさせると一本道に見えない。隠し近道は発見の喜びを作り、直線性を隠す。
- ○ 近道（帰りの道）は**必ず一度は通る場所**に置き、プレイヤーが頭の地図に入れられるようにする。
- ○ **ミッショングラフ**（部屋・錠・鍵・宝の依存関係）を作ると設計とバックトラックが見える。→ 返答に「入口→錠→鍵→宝」の順を書く。
- 自分の規約：扉は**両側にレバー**（行きも帰りも開く）。生成後に `check_doors()` と `check_return(start)` が空であること。

## E. 建築の定石（二次資料が多数一致。WesterosCraft の建築ガイド、MCBuildSchool、各ガイド）
- ○ 順序は**形 → パレット → 奥行き → 屋根 → ディテール**。ディテールは形が決まってから。
- ○ パレットは**3〜5ブロック**。同系色で質感の違うブロックを混ぜる（石なら 石レンガ・丸石・安山岩）。3種でも十分。多すぎない。
- ○ **平らな壁を避ける**：1ブロックの凹凸、窓枠、柱、梁、軒、階段・ハーフで影を作る。ドアは少し内側に引き、上に逆さ階段を置くと奥行きが出る。
- ○ **屋根**：初心者建築の見分けどころ。傾斜＋軒の出。棟を中央で合わせるには**奇数幅**。大きな屋根にはドーマー。屋根も3〜4種のブロックを混ぜる。**外側の屋根ブロックが室内から見えない**ようにする。
- ○ **グラデーション**：隣り合う順に少しずつ変える。意図的に破る箇所を作り、ランダムな「ごま塩」（splatter）と区別する。ノイズで駆動するグラデは3D ノイズの値でブロックの並びを選ぶ方式。
- ○ **明暗のコントラスト**：内部も含め、明るい面と暗い面を作らないと「ただの色の塊」に見える。
- ○ 家の下に土を露出させない（基礎を作る）。全面を同じ寸法にしない。装飾の入れすぎ（階段・トラップドアの乱用）は視覚的ノイズ。

## F. ルートテーブル名（Paper の `LootTables` 列挙と Minecraft Wiki の一覧）
- ○ 宝箱：`abandoned_mineshaft` / `ancient_city` / `ancient_city_ice_box` / `bastion_bridge` / `bastion_hoglin_stable` / `bastion_other` / `bastion_treasure` / `buried_treasure` / `desert_pyramid` / `end_city_treasure` / `igloo_chest` / `jungle_temple` / `jungle_temple_dispenser` / `nether_bridge` / `pillager_outpost` / `ruined_portal` / `shipwreck_map|supply|treasure` / `simple_dungeon` / `spawn_bonus_chest` / `stronghold_corridor|crossing|library` / `underwater_ruin_big|small` / `woodland_mansion`。
- ○ 1.21 の試練の間：`trial_chambers/…`（entrance・corridor・intersection・supply・reward 等）。報酬は宝箱でなく**ヴォルト**（ブロック）が主。`dungeon_kit.LOOT` に別名で登録済み（名前は列挙名からで、実機の中身確認は未）。
- 実機で中身を確認済みなのは、ユーザーが使った既存の別名（`simple_dungeon` 等）。

## G. 新しいブロック（建築の素材の幅）
- ○ 1.21：凝灰岩（tuff）一式（階段・ハーフ・壁・磨き・レンガ・彫刻）、銅の彫刻ブロック・ドア・トラップドア・電球・格子。1.21.9「銅の時代」：銅のチェスト（酸化・ワックス掛けあり）ほか。パレオーク（pale_oak）も新しい木材。
- △（記憶。調査では未確認）：樹脂（resin）レンガ、落ち葉（leaf_litter）、ワイルドフラワー等。`colors.py` には色を足したが、実機での名前は要確認。
- ○ 26.2：Sulfur（黄）と Cinnabar（深紅）の建材一式。26.3：ポプラ（明るい灰色の木材）、羊毛・コンクリートの階段とハーフ（色の段差を滑らかにでき、グラデーションや曲面屋根に有効）。ID は △（§B）。
- 高レベル建築の技法と汎用関数は `advanced_building.md`。
