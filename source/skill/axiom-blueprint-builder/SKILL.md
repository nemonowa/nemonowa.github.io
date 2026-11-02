---
name: "axiom-blueprint-builder"
description: "Minecraft（26.3 対応）の建築 MOD「Axiom」のブループリント（.bp）を解析・生成し、3Dビューアで公開するスキル。26.3 の新形式（Version 2）で書き、旧形式も読める。参考画像や「〇〇を作って」から建築をプログラムで組み立てて .bp に書き出す／既存の .bp を読んで調べる。ダンジョン（スポナー・宝箱・ルートテーブル・鉄の扉と両側レバー）、巨大な城・城塞都市、宇宙機（ISS・シャトル・宇宙戦艦）、魔法陣・曼荼羅・文様・ルーン、浮遊島・四季の島、内装、実寸再現、ゴシック聖堂・曲面屋根・地形・大木などの高レベル建築（グラデ・奥行き・SDF・回転複製）にも使う。「Axiom」「.bp」「ブループリント」「マイクラの建築」「ダンジョン」「スポナー」「ルートテーブル」「城」「シャトル」「宇宙戦艦」「魔法陣」「曼荼羅」「浮遊島」「26.3」「教会」「大聖堂」「地形」などが出たら、形式名がなくても使う。"
---

# Axiom Blueprint Builder

画像・指示 → Python で建築を組み立て → `.bp` に書き出し → プレビュー画像で自己点検 → 3Dビューアをアーティファクトとして公開、までの一連の流れ。

## Minecraft 26.3 対応（最初に読む）
- **既定の書き出しは 26.3 の Axiom 形式**（Header.Version=Int 2、DataVersion 5023、パレット=文字列 or `{id,properties}`、空き=void_air、BE に `components:{}`、Entities 対応）。ユーザーが 26.3 で保存した実ファイル（`examples/format_check_26_3/sample_26.3.bp`）と構造が一致することを確認済み。仕様は `references/bp_format.md`。
- 旧形式（1.20.4 / Version Long 1）の .bp も `read_bp` で読める。旧形式で書くのは頼まれた時だけ（`b.save(..., fmt=1)`）。
- **改名の自動変換**：`chain`→`iron_chain`（1.21.9）、`grass`→`short_grass`。スクリプトでは新名（`iron_chain`）を使う。
- **BE・エンティティは現行 NBT**（アイテム=`count`+`components`、本=`written_book_content`、テキスト=NBT コンポーネント、属性=`attributes:[{id,base}]`）。ヘルパーは `scripts/nbt_helpers.py`、エンティティは `b.ENT=[…]`。
- 26.2/26.3 の新ブロック（sulfur・cinnabar・poplar・羊毛/コンクリートの階段とハーフ等）は**ID が未確認（△）**。使うなら返答で「名前が違えば置換が必要」と伝えるか、ユーザーの .bp で確かめる。
- 初めて 26.3 形式を渡す時は `examples/format_check_26_3/format_check.py` の出力（宝箱2・スポナー・書見台・看板・防具立て・鉄の鎖入りの小祠）を添え、実機で貼って確認してもらう。

## ファイル構成
- `scripts/bplib.py` — .bp の読み書き（**26.3 形式 v2 を既定で書き、v1/v2 を読む**。NBT（異種リスト・型付き読み込み）、パレット+ビット詰め、gzip、サムネイル、往復検証、`origin=` で原点指定、`entities=`、`paste_air=`）。CLI: `python3 bplib.py a.bp` で形式・DataVersion・BE/エンティティ数まで表示。
- `scripts/nbt_helpers.py` — **26.3 の BE/エンティティ NBT**：`chest_loot` `chest_items` `spawner`（名前・体力・ドロップ・明るさ条件）`mob` `lectern` `sign` `armor_stand` `item_frame` `entity` `give_book_command` `summon_command`、型付きコンストラクタは bplib の `B Sh I F D S C Ls`。
- `scripts/advanced_helpers.py` — **高レベル建築の汎用関数**：向き情報つきの回転・反転・複製（`stamp`）、曲線（`catmull_rom` `catenary` `line3d`）、SDF 立体（`fill_sdf` と `sd_*`）、**高さ場→フル/ハーフ/階段で滑らかな面**（`smooth_heightfield` と円錐・ドーム・腰折れ・マンサード屋根）、尖頭アーチと奥行きのある窓（`opening`）・バラ窓・控え壁/フライング・バットレス・尖塔、ノイズ（`fbm2/3` `ridged2`）とディザ付きグラデ（`grad_pick`）・風化（`weather`）、地形（`terrain` `thermal_erode`）・配置（`poisson_disk`）・大木（`organic_tree`）、解析（`hidden_cells` `palette_stats`）。
- `scripts/builder.py` — 建築ヘルパー（`Build` クラス：box/ring/disk/sphere/**tube(ベジェ)**/**shell(殻)**/hip_roof/roof_layer/flight/hanging/rope/ground_cover/save、状態ヘルパー `ST() SL SLT FN LEAF WALL`、`noise() h3() pick()`）。
- `scripts/arch_helpers.py` — **汎用建築ヘルパー**：`tile_roof`（1:2勾配の寄棟、`hcap` で軒先だけ段差）/ `gable_roof` / `corner_stair`（外隅階段の向き）/ `fix_connections`（フェンス・板・壁の接続を自動補正）/ `lay_path` / `carve_water` / `fence_line`。地表は `G[(x,z)]`。
- `scripts/ancient_helpers.py` — **古代遺跡・幻想の外装**：面のピクセルアート(`paint_face`+有翼太陽/ホルスの目/アンク)・風化・砂の吹き溜まり・スフィンクス(small/great)・塔門・オベリスク・折れ柱・崩れアーチ・ヤシ・環状列石・衛星ピラミッド・浮遊太陽円盤・浮遊遺構・光の亀裂・水晶。
- `scripts/japan_helpers.py` — 和風の小物と樹木：石灯籠・鳥居・竹・松・枝垂れ桜・吊り灯籠。
- `scripts/dungeon_kit.py` — **ダンジョンキット**：`Dungeon`（carve→line→扉＋両側の壁レバー`door_levers`/ハシゴ/隠し蓋/棘の穴/溶岩湖/**迷路`maze`/螺旋階段`spiral`/外への開口`open_end`**/スポナー/宝箱→`check_leaks`→`check_doors`→`check_return`→`solve`(攻略可能性BFS)→`render_map`）、`chest_be`/`spawner_be`（BlockEntities）、`export_commands`（保険のコマンド）。**`section()`＋`line_sections()`**で区画ごとに内張り素材を変える（幹の中=木、地下=石）。
- `scripts/pattern_helpers.py` — **平面の文様・魔法陣・レリーフ**：画像→格子（`estimate_block_px/sample_grid/classify/fold_d2/recolor/to_build`）、幾何（`star_segments/hexagram_segments/petal_hit/hex_lattice_centers/fold4/seg_dist`）、**ルーン**（`ELDER_FUTHARK/YOUNGER_FUTHARK/place_runes/rune_hit`）、楓・モミジ・ひまわりのモチーフ（`lobed_leaf_r/MAPLE5/MOMIJI7/phyllotaxis`）、`paint/render_top/put_relief`。
- `scripts/space_helpers.py` — **宇宙機・円筒構造**：`tube`(直径5・殻1・内部3×3、角を階段で面取り、継手リング、ノイズ混色)/`tube_lights`/`tube_racks`/`lattice_truss`/`solar_wing`/`radiator_panel`。
- `scripts/interior_helpers.py` — **内部の検証と本・看板**：`check_interior`（内部の密閉＋全室の接続をBFSで検査。`b.B` のワールド座標で）/`lectern_with_book`/`wall_sign`/`give_book_command`。
- `scripts/colors.py` — ブロック名→色・形状。プレビュー/サムネ/ビューアで共通。**未定義色はマゼンタ**。
- `scripts/render_preview.py` — 等角PNG（回転・拡大・断面）。
- `scripts/build_viewer.py` — 複数 .bp → 公開用HTML（見える面だけ埋め込み）。ローカル用ビューアの色表同期も。
- `assets/viewer_template.html` — 公開ビューア（一覧・3D回転・断面スライダー・メタデータ・使用ブロック上位）。
- `assets/local_viewer.html` — ユーザーのPCで .bp フォルダを選んで読む単体HTML（JSでパース）。
- `examples/example_pavilion.py` — 最小の完全な例。新規作成はこれをコピーして始める。
- `examples/format_check_26_3/` — **26.3 形式の確認用**（`format_check.py`）とユーザーの 26.3 実ファイル `sample_26.3.bp`（形式の一次資料）。
- `examples/vatican/` — **サン・ピエトロ大聖堂と広場を 1:1（約43万ブロック）**：解析的な立体→厚さ2の殻、内部に面するセルだけ内装材、尖頭ドーム＋リブ、楕円オフセットで柱廊を並べる。実在の大建築を殻で作る雛形。
- `examples/advanced_showcase/` — **高レベル建築の総合例**：丘（fbm＋侵食＋なめらかな縁）の上のゴシック礼拝堂（尖頭窓・控え壁とフライング・バットレス・バラ窓・高さ場の屋根・八角尖塔）、円塔の円錐屋根、玉ねぎドーム、部品の回転複製の街灯と懸垂線の鎖、大木、風化。約3.4万ブロック。
- `examples/pyramid_dungeon/` — **ピラミッド型ダンジョン**（高台＋45°階段ピラミッド＋3層：迷路・棘の穴・溶岩の島・螺旋・ボス・宝物庫。キットの `maze/spiral/open_end` を使用）。
- `examples/example_dungeon.py` — 最小のダンジョン例（隠し蓋→棘の穴→溶岩→宝物庫、宝箱とスポナーをBlockEntitiesで書く、検証とマップまで）。
- `examples/magic_circles/` — **魔法陣（幾何学・ルーン）を式で作る**＋**参考画像（ブロックの文様の写真）→.bp の自動化**（`digitize_image.py`、実例の代表色JSONつき）。
- `examples/floating_japan_island/` — 和風の浮島4つ（五重塔・社殿・東屋・蔵）＋地下ダンジョンの大規模な実例（独自実装。新規はダンジョンキットを使う）。
- `examples/floating_island_dungeon/` — **浮遊島＋聖樹ダンジョンを春・夏・秋のテーマで生成**（`--theme`。宝箱13/扉1を機械検証、攻略マップ、BE入り/なし）。新しい季節は `themes.py` に追記。
- `examples/iss/` — **ISS（1ブロック=1m、8,894ブロック）**：主要モジュール・トラス・太陽電池翼・ロボットアーム・来訪機、内部を歩ける、書見台の本4冊・看板8枚、`check_interior` で検証。宇宙機/円筒構造の雛形。
- `examples/shuttle/` — **スペースシャトル オービタ（1ブロック=1m、2,104ブロック）**：断面表＋超楕円の外形、侵食による内部、デルタ翼、ODS、書見台の本。航空機型の雛形。
- `examples/iss_shuttle/` — **合体シーン（ISS×シャトル、10,601ブロック）**：別スクリプトの Build を exec で取り出して回転・合成、ODS で連絡。
- `examples/wedge_warship/` — **くさび形の巨大宇宙戦艦（オリジナル、約9.2万ブロック）**：列ごとの高さ表で殻1枚、塔・エンジン・格納庫。巨大物の雛形。
- `references/spacecraft.md` — **宇宙機の縮尺方針（直径5への丸め）・調べ方・円筒/ハッチ/縦穴/外部構造の作り方・検証と失敗談・本と看板・航空機型(§9)・別構造物の合体(§10)・巨大艦(§11)**。宇宙ステーション/ロケット/衛星を作る前に読む。
- `references/patterns.md` — **平面文様・魔法陣・ルーン・空中レリーフ**：画像の読み取り手順（ブロック幅・中心・代表色・影/ゴミ対策・対称化）、色違い、式の書き方、ルーンの寸法、レリーフの3層、失敗談。
- `references/island_dungeon.md` — **浮遊島＋聖樹ダンジョン**：寸法表、部屋割りと高さ、幹の最小半径、樹冠の間、検証で見つかった失敗談、季節テーマ表、返答の書き方。
- `references/bp_format.md` — **形式仕様（26.3 の v2 と旧 v1 の差分表つき）**。
- `references/advanced_building.md` — **高レベル建築の技法（出典・確度つき）と汎用関数の対応表**：優先順位（シルエット→形→パレット→奥行き→ディテール）、縮尺、グラデーション、地形の侵食、ファサードの奥行き、ゴシックの記号、屋根、モジュールと回転、有機物、式で形を作る（SDF）、手続き生成（GDMC/WFC）、軽量化、仕上げチェックリスト。
- `references/architecture.md` — **縮尺・屋根・壁の見え方・接地・島の作り方・内装・「個性・歴史・ロマン」の足し方（§9）・浮島の縁と底（§10）・検証の習慣**（根拠の確度つき）。大きな建築・本格的な建築の前に読む。
- `references/dungeon.md` — **ダンジョン設計**：層の寸法、扉+レバー、棘/溶岩/水/迷路、スポナーと自然スポーンの仕様、ルートテーブル、動線、検証手順（公式資料での裏どり済み/未検証を区別）。
- `references/research_notes.md` — **調査メモ（確度つき）**：Axiom 公式ドキュメント（保存先・サブフォルダ・タグ・貼り付けオプション・No Updates）、Minecraft 26.x の版事情と .bp 形式の変化（26.1〜26.3 の新ブロック、iron_chain 改名、コンポーネント/テキストの書式）、レバーと扉の仕様、ダンジョン設計の原則、建築の定石、ルートテーブル名、新ブロック。
- `references/block_entities.md` — **宝箱の中身・スポナー・書見台の本・看板（BlockEntities）と防具立て等（Entities）を 26.3 の NBT で書く方法**と根拠・未確認点。
- `references/techniques.md` — 画像の読み解き、材料ミックス、地形・樹木・和風/中華風・城郭・ネザー、**ブロック状態の落とし穴**。建築を書く前に該当節を読む。

スクリプトは `/mnt/skills/.../scripts` から作業ディレクトリへコピーして使う（`cp -r <skill>/scripts /home/claude/bp && cd /home/claude/bp`）。**古い版の scripts を使い回さず、必ずスキル最新版をコピーする**（26.3 形式の書き出し、扉の両側レバー `door_levers`/`check_doors` などは新しい版にしかない）。

## 手順

### A. 既存 .bp の解析（zip が来たら）
1. 展開し、Axiom のファイル名エスケープ `#Uxxxx` を `chr(int(xxxx,16))` で日本語に戻す。
2. `read_bp()` で全件読み、名前・作者・タグ・サイズ・ブロック数・DataVersion を確認（ヘッダ BlockCount と一致すればパース成功）。
3. `build_viewer.py out.html --archive <dir>` → Artifact で publish。
4. 形式（`bp['fmt']`：1=旧/2=26.3）と DataVersion（`bp['data_version']`、26.3=5023）を確認。ユーザーの版が 26.3 なら既定のまま、違う版なら `b.save(..., data_version=…)`（旧形式なら `fmt=1`）で揃える。BE・エンティティは `bp['block_entities']` / `bp['entities']`（型付き）で取り出して再利用できる。

### B. 画像・指示から建築を作る
1. **読み解く**（techniques.md §1）：比率→ブロック寸法、主要パーツ、3〜5色の配色、見えない部分の解釈。リアルな題材（城・寺など）で「本格的に」と言われたら web_search で実物の技法を調べ、引用して説明に使う。
2. **スクリプトを書く**：`examples/example_pavilion.py` を雛形に、順番は「地形 → 構造体 → 開口(rm) → 屋根 → 内装 → 装飾 → 植栽 → 最後に通路の空気確保」。後置きが勝つので、植物や蔓は `put_if_empty`/`empty()` で既存を壊さない。
3. **パラメータ化**：大きさ・色・本数を変数にしておくと「もっと大きく」「色を濃く」に即応できる。乱数は `random.Random(seed)` と `h3()` で決定的に。
4. **保存**：`b.save(path, 名前, tags=[...])` が自動で往復検証し、未定義色ブロックを警告する。警告が出たら `colors.py` の KEYWORDS 先頭に追加。
5. **自己点検（必須）**：`render_preview.py` で2方向（`--yaw 0` と `2`）を描き、`view` で見る。小さい建築は `--scale 12〜16`。内装は `--clip` で断面。チェック項目：シルエットが参考に似ているか／マゼンタがないか／垂れものや苔が多すぎて主役を隠していないか／開口が埋まっていないか／浮いたブロック。直して再生成を1〜3回。
6. **出力先**：`/mnt/user-data/outputs/samples/<名前>.bp`。present_files で渡す。

### I. 高レベル建築（「本格的に」「プロっぽく」「大聖堂」「街並み」「地形ごと」）
1. `references/advanced_building.md` を読み、§0 の順（シルエット→形→パレット→奥行き→ディテール）で設計を決める。`examples/advanced_showcase/showcase.py` を雛形にする。
2. 地形は `fbm2/ridged2` → `thermal_erode` → `terrain(smooth_top=)`。敷地は平らにして基礎ブロックで土を隠す。
3. 外殻は箱か `fill_sdf`。壁の材は `grad_pick`（下ほど暗く粗く）。開口は `opening(depth=1, sill=, frame=)`、ゴシックなら `sharp=1.4〜2`・`buttress(flying_to=)`・`rose_window`。
4. **屋根は必ず `smooth_heightfield` 系**（切妻・寄棟は高さ関数、塔は `cone_roof`、ドームは `dome_roof`）。軒の出 1、壁より暗い材。
5. 繰り返す部品（家・街灯・柱・窓）は1つ作って `stamp(turns, mirror)` で回して並べる。配置は `poisson_disk`、道は `catmull_rom`、紐は `catenary`。
6. 最後に `weather(amount≤0.4)`、`palette_stats` で主材 60％前後を確認、`render_preview --yaw 0..3 --scale 12〜16` で拡大点検（窓が壁色に埋もれていないか、屋根の階段の向き、バラ窓の柄）。
7. 返答では使った技法を advanced_building.md の出典つきで短く説明する。

### D. ダンジョン・仕掛け・NBT を作る（頼まれたら）
1. `references/dungeon.md` と `examples/example_dungeon.py` を読む。**深さマップ → 部屋割り**を先に決める（掘れる深さ、層間の岩3枚、溶岩/水の下の岩）。
2. 立体が上に狭まる建物（ピラミッド等）は `references/dungeon.md §7` と `examples/pyramid_dungeon/` を参照。順序：地形 → **接地チェック** → `Dungeon.carve` → `spike_pit`/`lava_lake` → `line()`（内張りで密閉）→ 仕掛け・宝箱・スポナー・照明 → `check_leaks()==0` → `solve()`（全扉が開き全宝箱に到達できること）→ `render_map()` で各階の平面図。
3. 仕掛けは**ブロックだけで成立**させる：鉄の扉＋**扉の両側（行きも帰りも）に壁付けレバー**（`dg.door_levers()`。床置き・片側だけは禁止。赤石配線なし）／隠し蓋=トラップドア half=top＋ハシゴ／水の中にレバー等を置かない／溶岩は床面と面一。
4. 宝箱・スポナーは **BlockEntities**（`b.BE = dg.block_entities()` → `b.save`）。**宝箱のルートテーブルとスポナーは実機（Axiom）で読み込み確認済み**（旧形式で確認。26.3 形式は実ファイルと同じキー・型で書いている）なので BE入りを主に出す（BEなし版は書見台・看板など未確認のBEを含む時、頼まれた時だけ）。名前・体力つきのスポナーは `nbt_helpers.spawner(name=, health=)`。ボスは /summon コマンド（`export_commands`）か、26.3 形式なら `b.ENT` にエンティティとして入れる（未確認なので /summon も併記）。
5. 自然スポーンは「ブロック光0・プレイヤーから24ブロック以上」なので、小さなダンジョンはスポナーを置く。スポナーの湧き箱は壁を貫通する（9×3×9）ことに注意。
6. 返答では、攻略順・仕掛け・コマンド/NBTが要る部分・未検証点（モブの湧き、書見台・看板のBE）を正直に書く。

### E. 実在の大型構造物・宇宙機を実寸（1ブロック=1m 等）で作る（頼まれたら）
1. `references/spacecraft.md` と `examples/iss/iss.py` を読む（航空機型は `examples/shuttle/`、合体は `examples/iss_shuttle/`、巨大艦は `examples/wedge_warship/`）。**縮尺を先に宣言**し、実寸表（一次資料）を web_search/web_fetch で取って「実寸→ブロック数」の表を作る。丸め（円筒直径5、ノードは奇数長など）は返答に書く。
2. 順序：主軸のモジュール列（`tube`）→ 放射状・縦のモジュール → トラス/翼/ラジエータ → アーム・来訪機 → 装飾 → ラック/照明/ハシゴ/窓 → **ハッチ（両側の殻を抜く）** → 看板・書見台。
3. **`check_interior` で密閉と全室の接続を検査**（装飾を足すたびに再実行）。`b.B` のワールド座標で行う（.bp を読み戻すと座標がずれて誤判定する）。
4. 全景2〜4方向とズーム（`--clip` は最小角基準）で確認。モジュール列だけ見たい時は y を絞る。
5. ゲーム内の解説は書見台の本（概要・寸法表・丸めと省略・豆知識）と看板。**BE入り版/BEなし版/`/give` コマンド集の3点**を出す。実機未確認（書見台・看板のBE、ハシゴ・看板の吸着）を正直に伝える（宝箱・スポナーのBEは実機確認済み）。
6. 資料で確定できなかった点（向き・位置・来訪機の時期）は「近似・一例」と明記する。

### F. 魔法陣・曼荼羅・文様・レリーフ（頼まれたら）
1. `references/patterns.md` を読む。**参考画像があるなら**（ブロックで作った文様の真上写真）`examples/magic_circles/digitize_image.py` で再現する：ブロック幅の推定 → 中心と n → サンプリング → 代表色(proto)で分類 → 対称化。まず `--report` で分類を確認し、元画像と並べて目視。色違い（自然色・四季）は `recolor` で形を保ったまま。
2. **画像が無い／『似た柄で』『魔法陣を』**なら式で作る：`magic_circles.py` を雛形に、外輪→帯→星→飾り→中心の順に重ねる（後勝ち）。ルーンは `place_runes`（高さ9以上で判読可）。星は {12/5} など、花は `petal_hit`、フラワー・オブ・ライフは `hex_lattice_centers`。
3. **必ず `render_top` の上面図を `view`**。等角プレビューでは文様の崩れが分かりにくい。モチーフの寸法は『太く・大きく』から（細すぎて楓に見えなかった失敗あり）。
4. 空中の大きな円盤・レリーフは `put_relief`（奥/中/手前の3層、葉脈や種は光るブロックで盛る）。1層のままでよい作品に高さを勝手に足さない。
5. 返答：外から内への構成・配色（ブロック名）・斜め線が階段状になる点・ルーン字形は近似・ブロックの当て込みは推測、を書く。

### G. 浮遊島・聖樹・四季テーマのダンジョン島（頼まれたら）
1. `references/island_dungeon.md` と `examples/floating_island_dungeon/` を読む。『同様に〇〇の島を』は **`themes.py` に新テーマを足し、`island_dungeon.py --theme` で再生成**する（形・ダンジョン・検証はそのまま使える）。
2. 季節の意匠は4点：樹冠の色・広場の床紋様（桜=魔法陣／楓=楓の葉／ひまわり）・背面レリーフ・地表と小物（浜辺・落ち葉・ひまわり畑・雲海）。葉をウール等で作るなら殻のプロパティは {}。
3. 出力は **BE入り版・BEなし版・攻略マップ・コマンド集**。`check_leaks==0`／全扉が開く／全宝箱に到達 を返答に書く。実機未確認（スポナーの貫通、植物ブロック）を正直に。宝箱・スポナーのBEは実機確認済み。
4. 依頼が『背面のレリーフだけ差し替え』のような部分変更なら、テーマの `back` 関数だけ替えて再生成（1〜2分）。

### H. 巨大な城・城塞都市（歩ける内装＋多層の地下ダンジョン）（頼まれたら）
『ダークソウルのような重厚な城』『城壁の上や中も通れる』『主塔にバルコニー』『地下にスポナーと宝箱のダンジョン』の依頼で実績のある進め方（約119万ブロックで往復検証OK、全宝箱・全扉に到達確認済み、利用者から「GOOD」）。
1. **構成と順序**（後置きが勝つので固定する）：地形・都市 → 城の外殻（城壁・塔・主塔・門楼）→ **動線**（回廊・階段・螺旋・城壁歩廊・扉）→ **内装**（家具）→ 地下ダンジョン → `fix_connections` → 宝箱・スポナー(BE)の配置は**最後**。BE は座標にブロックが無いと捨てられ、後から壁や家具で上書きされるので、`castle_loot()` のように最後に置き、「BEの座標にブロックがあるか」を検査する。
2. **歩行性を先に設計**：城壁の内側に回廊レーン（幅2・高さ4）を取り、城壁の上は歩廊（足元を一定の高さに）、隅塔・中間塔・門楼は螺旋階段で壁上と屋上へ。主塔は層ごとに（大広間→中二階→北回廊→上層の間→鐘楼→環状バルコニー）扉と螺旋で繋ぐ。バルコニーは手すり（壁ブロック）＋ランタン、足元の下に持ち送り（階段・逆さ階段）を回して見栄えを出す。
3. **螺旋階段の作法**：1段ごとに1マスの階段を3×3外周（8マス）で回す。階段の facing は上る方向。**階段の頭上は3マス空ける**（BFS・実歩行とも）ため、最上階の床リングは階段より先の4マスだけ置く（5マス置くと最上段が塞がる）。着床の段は床ブロックの高さ=足元-1。井戸型（大広間の床から地下へ）は外周を石レンガで固め、広間側は欄干1マス開けで入口を作る。
4. **家具は空きセルにだけ置く**（`pf()`＝empty のときだけ置き、置けなかった数を数える）。宝箱の前は塞がない（書見台は宝箱の前でなく両脇へ）。壁掛け旗は壁の内側でなく歩ける側に向けて貼る。ケーキ・頭骨・玄武岩などは `colors.py` 未定義だとプレビューがマゼンタになる（ゲームでは無害）。
5. **地下は階層ごとにテーマを変える**：`Dungeon` を継承して `line()` を差し替え、y から階層を判定して壁・床・天井のパレットを切り替える（L1=苔石レンガ/L2=ブラックストーン/L3=ディープスレート/L4=磨きブラックストーン＋金入り）。階層は12ブロック間隔（天井・床・上下の岩が十分に取れる）、層間は `dg.spiral` で繋ぐ。地表側に出る井戸の穴は `open_end` で『わざと開けた』と登録し、`line_skip_y` で地表を内張りしない。
6. **ダンジョンの小物**：休憩地点（焚き火＋上向きの避雷針＋ろうそく。通路の脇の隅に置く）、石棺（石レンガ3＋スラブ＋頭骨）、霧の門に見立てた蜘蛛の巣（頭上 y+3 の層だけ。足元に置くと歩行検査が通れない）、鍛冶台・砥石・大釜。ボス部屋は溶岩の堀＋十字橋、手前の扉は **`door_levers` で両側に壁レバー**。
7. **機械検査（必須。各回の再生成で）**：`dg.solve()` で扉が全部開き宝箱に全部到達／`check_leaks()==0`／`check_doors()==[]`／城側の宝箱到達／主要地点（城壁歩廊・塔頂・中二階・バルコニー・鐘楼）に到達。城側は NONSOLID に `dark_oak_door, banner, skull, candle, trapdoor` を足してからBFS。階層ごとの平面図（`render_map`）と、屋内は上面図（y範囲を絞って描く）で目視。
8. **出力**：BE入り `.bp` ＋ BEなし `.bp` ＋ 保険コマンド（原点=最小角、ボスは /summon）の3点。ビューアは外観の見える面だけを埋め込むので**内装・地下は映らない**（返答に書く）。
9. **返答で正直に**：BE の実機読み込み（宝箱・スポナーは確認済み、それ以外は未確認）／スポナーはプレイヤーが近いときだけ動く・光量条件／溶岩・ブレイズ・焚き火は危険／ブロック数が多く貼り付けが重い／入口（大広間の井戸）と階層の順。

### C. ビューアに載せる（毎回）
```
python3 build_viewer.py /mnt/user-data/outputs/axiom_blueprints.html \
   --samples <新しい順に .bp を並べる> --archive <ユーザーの手持ちdir> \
   --sync-local /mnt/user-data/outputs/axiom_bp_viewer.html
```
- 初回は Artifact publish、2回目以降は**同じ url を渡して更新**（一覧の先頭に新作が来るよう samples の順を新しい順に）。
- ローカル用ビューアは「ブラウザは同じフォルダを勝手に読めない」ので、フォルダ選択/ファイル選択/ドラッグ&ドロップで読む方式。Axiom の保存先は `%userprofile%\AppData\Roaming\.minecraft\config\axiom\blueprints`（AppData は隠しフォルダ。選択ダイアログのアドレス欄に貼り付けるよう案内）。

## 品質のコツ（要点。詳細は techniques.md）
- 単色の塊にしない：必ず2〜4種のミックス＋ノイズのかたまり。
- 大きな樹冠・ドームは**殻**で作る（中身を詰めない）。ブロック数・ビューア容量・ゲームの負荷すべてに効く。
- 主役（幹の文様、入口、塔の頂部）を隠す要素は間引く。垂れもの・苔・花は控えめから始める。
- 発光ブロックを配置しておく（shroomlight/froglight/lantern）。夜でも映える。
- 階段の facing は「上る方向（高い側が向く向き）」。葉は persistent=true。ドアは上下2つ。（§9）
- **接地**：建物のフットプリント+2 を島の内側に収める（`references/architecture.md §4`）。**縮尺**は絶対値でなく比率（1層高÷屋根幅 など）で参考画像に合わせ、2方向のプレビューで測り直す。
- **壁が見えない時**は軒の出を減らす/壁を高く/窓を床まで下げる。軒の出×tan(視点仰角) が壁を隠す。
- 溶岩・火を使ったら説明で注意喚起。水は通常含めない（海上配置前提なら y=0=海面で設計）。

- **内部のある建築は必ず機械検査**：密閉（漏れなし）と全部屋の到達性。見た目だけでは分からない（`check_interior`）。
- **混色は塊で**：ブロック単位の乱択ではなくノイズの塊で2色混ぜる（ごま塩を避ける）。
- **文様は上面図で確認**（等角では崩れが見えない）。ルーンは線分を連続座標で回転配置してから塗る。コンクリートパウダー・砂は落ちるので使わない。
- **鉄の扉は必ず両側に壁レバー**（`door_levers`）。片側だけだと反対側から開けられず帰れなくなる（実機でユーザーに指摘された）。レバーなどの貼り物は**床ではなく壁**に付ける。生成後は `check_doors()==[]` と `check_return(start)==[]`（扉の両側から歩いてレバーに届く）を確認し、返答に書く。
- **巨大建築は『家具は空きセルのみ』『BEは最後に置いて存在検査』『螺旋階段の頭上3マス』**（H節）。
- **原点**：既定は最小角（`origin='min'`）。中心で回したい・貼り付け位置を中央にしたいなら `b.save(..., origin='bottom_center')`。
- **作者は常に `nemo`**（`write_bp` / `Build.save` の既定値。書見台の本の著者欄も nemo）。別名を頼まれた時だけ変える。
- **幹や壁の中に部屋を取る時は最小半径から逆算**（壁＋内張りで +1.5）。梯子の真上の葉まで抜く。トラップドアの蓋は検証が通れない（穴＋ハシゴ）。

## 返答の書き方
- 何を作ったか（サイズ・ブロック数・ファイル容量）→ 参考から再現した要素 → 解釈で補った部分 → 注意点（ゲーム内未検証、負荷、溶岩）→ 調整の提案、の順で簡潔に。
- 技法を調べた場合は出典を引用付きで示す。
- **Axiom での貼り方を一言添える**（`references/research_notes.md §A`）：Ctrl+V → Enter。地形に埋めるなら Paste Air、重ねるなら Keep Existing。回転は90°刻み（任意角は向き情報が崩れる恐れ）。周囲を触るなら No Updates。ファイルは用途別フォルダ＋タグで渡す。
- 宝箱のルートテーブルとスポナーのBlockEntitiesは実機で読み込み確認済み（旧形式）。26.3 形式での読み込み・書見台・看板のBE・エンティティ・ハシゴ・看板の吸着・26.2/26.3 の新ブロックIDなど**確認していない部分だけ**を正直に伝え、必要ならユーザーに実機確認を依頼する（`format_check_26_3` を添える）。
- 調べた仕様（スポナー・湧き条件・ルートテーブル等）は、確度（公式/二次資料/経験則）を区別して伝える。
