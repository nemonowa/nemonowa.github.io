# 高レベル建築の技法と汎用関数（2026-11 調査）

大きな建築・「本格的に」「プロっぽく」と言われた建築の前に読む。関数は `scripts/advanced_helpers.py`、全部を使った実例は `examples/advanced_showcase/showcase.py`。
確度：◎=公式/一次資料、○=複数の二次資料が一致、△=経験則・推論（このスキルで実際に作って確かめたものは「実践」と書く）。

---

## 0. 優先順位（何から決めるか）
1. **シルエット**（遠くから見た輪郭）→ 2. **形と縮尺** → 3. **パレット** → 4. **奥行き** → 5. **ディテール**。
   - ○ 形が素材より重要。形と縮尺を決めてから装飾ブロックを入れる。遠くから見て平らな箇所に階段・柵を足して輪郭を崩す（複数の建築ガイドが一致）。
   - ○ WesterosCraft の Fundamentals は「ブロックの変化・配置・基礎・ファサード・屋根・内装」の順で構成されている（[westeroscraft.com/docs/building/fundamentals](https://www.westeroscraft.com/docs/building/fundamentals)）。
2. コードでは「地形 → 外殻（SDF/箱）→ 開口 → 屋根（高さ場）→ 奥行き部材 → 植栽 → 風化 → 最後に通路の空気確保」の順に書く（後置きが勝つ）。

## 1. 縮尺と比率
- △ 階高は 4〜5 ブロック（床1＋天井高3〜4）。教会・広間は 8〜14。扉は 2 高、大扉は 3×4〜3×6 の尖頭。
- △ 棟を中央に置くなら幅は**奇数**（既存の research_notes §E と同じ）。
- ○ 実物大の目安：ノートルダムの 1:1 再現作品が 67×109×139 ブロック・約7.7万ブロックと公表（[BuiltByBit](https://builtbybit.com/resources/notre-dame-of-paris.114522/)）。大聖堂を「それっぽく」作るなら幅 20〜30・長さ 50〜100 が下限。
- △ 小さすぎる建築では尖頭アーチ・バラ窓が潰れる：尖頭窓は幅3以上・高さ6以上、バラ窓は半径5以上（実践：半径4では柄が出なかった）。

## 2. パレット・グラデーション・風化
- ○ **グラデーションは最重要のディテール技法**（WesterosCraft：“the single most important detailing technique” [gradients](https://westeroscraft.com/docs/building/fundamentals/gradients)）。Conquest Reforged も奥行きの表現にグラデが不可欠と書く（[conquestreforged.com/guides/gradients](https://www.conquestreforged.com/guides/gradients)）。
- ○ 暗いブロックは遠く・奥に見える → 平らな面でもグラデで奥行きが出る。小さい建築では急な色の切り替えが目立つので段数を増やす。
- △ 主材 60％・副材 30％・差し色 10％を目安に `palette_stats()` で確認。
- 実装：
  - `grad_pick(palette, t, x,y,z, jitter)`：t（高さ・中心からの距離など 0..1）で並びを選び、**3D ノイズの塊でディザ**（ごま塩にしない）。壁は「下＝暗く粗い（丸石）→ 上＝明るく滑らか（磨き安山岩）」。
  - `weather(b, amount)`：下の方・北面ほど苔、それ以外はひび。階段やハーフの向きは保ったまま材質だけ変える（`WEATHER` 表に追加可）。
- △ 風化は amount 0.2〜0.4。強すぎると主役のシルエットが汚れる（既存 SKILL.md「垂れもの・苔は控えめ」と同じ）。

## 3. 地形
- ○ 定番の流れ：**ブラシで骨格 → 高さマップで整える → 侵食で角を落とし古びさせる**。侵食をかけすぎると山頂が台地（メサ）状に潰れる（WorldPainter の解説 [cypaint.com](https://cypaint.com/article/how-to-build-a-mountain-in-world-painter)）。
- ○ 大規模な地形は WesterosCraft でも Axiom で作っている（[westeroscraft.com/docs/building/tools/axiom](https://westeroscraft.com/docs/building/tools/axiom)）。
- 実装：`fbm2`（なだらか）/`ridged2`（山脈・尾根）で高さ → `thermal_erode(H, talus)`（崖の角を崩す）→ `terrain(..., layers, smooth_top=(stair,slab))`（草→土→石の層、端数 .5 以上の列は階段/ハーフ）。島の輪郭は `mask` にノイズを足す。
- △ 敷地は先に平らにし、基礎ブロック（磨き安山岩など）で「土を見せない」（research_notes §E）。

## 4. 奥行き・ファサード
- ○ **レイヤリング**：素材を前後に重ねて実物の取り合いを真似る。トラップドアの庇、窓台の階段/ハーフ、ハーフで壁を分節。軒の出が影の線を作る。
- ○ **ジェッティ（上階の張り出し）**：16世紀の木骨造で流行（Minecraft 公式記事 [PixlPlex's palace](https://www.minecraft.net/ja-jp/article/peruse-pixlplex-s-perfect-palace)）。下階を石、上階を明るい木骨にすると締まる。
- 実装（`advanced_helpers`）：
  - `opening(b, x,y,z, normal, w,h, depth, sharp, glass, frame, sill, keystone, wall_t)`：**窓は外面から 1 マス奥**にガラス（影ができる）、額縁 1 マス外、窓台＝逆さ階段、頂部に要石。`glass=None` で扉・回廊。
  - `arch_inside(u,v, half_w, spring, sharp)`：sharp=1 半円 / 1.3〜1.6 ゴシック尖頭 / 2 正三角形 / 3 ランセット / 0 四角。迫元は頂部が h になるよう自動計算（立ち上がり=√(2ar−a²)）。
  - `pilasters`（付け柱で壁にリズム）、`cornice`（軒蛇腹＝逆さ階段を外へ）、`buttress(..., flying_to=)`（控え壁と**フライング・バットレス**）。
- ○ ゴシックの記号：尖頭アーチ・**フライング・バットレス**（シルエットの決め手）・**バラ窓**・十字形の平面・リブ・尖塔。窓は細く高く、桟に柵（[Cal Poly ガイド](https://grandavehousing.calpoly.edu/blog/minecraft-european-architecture-a-builders-guide-1764800794)、[exitlag 教会ガイド](https://www.exitlag.com/blog/minecraft-church/)）。
  - `rose_window(R, petals)` を `paint_plane` で鉛直面に塗る。外枠・中間輪・内側の放射桟・半ピッチずらした外側の桟。R≥12 で外周に小円。
  - `spire(cx,y0,cz, r,h, mat, sides=8)`：八角の中空尖塔。頂部に避雷針（lightning_rod）を立てると細さが出る。

## 5. 屋根（もっとも差がつく部分）
- ○ **平らな屋根は初心者建築の一番の目印**。階段で勾配、**軒の出 1〜2**、**壁より暗い屋根材**で屋根を独立した要素に見せる（[gamertagmythras.com](https://gamertagmythras.com/blog/minecraft/minecraft-building-tips)）。屋根形式：切妻・十字切妻・曲面。
- 実装の核心：**`smooth_heightfield(b, cells, h, full, stair, slab)`**
  - 屋根面を「高さ関数 h(x,z)」で書き、半ブロック単位で丸めて**フル / 上り階段 / 下ハーフ**を自動で選ぶ。外隅・入隅の階段 shape は `fix_stair_corners` がゲームと同じ規則（背面の階段→outer、前面→inner、左右は反時計回り側が left）で決める。
  - これ1つで：切妻（h=棟高−|x|）、寄棟（h=棟高−max(|x|,|z|)）、`cone_roof`（円錐）、`dome_roof`（ドーム・`onion` で玉ねぎ）、`gambrel_roof`（腰折れ）、`mansard_roof`（マンサード）、反り屋根（h に (d/W)^1.5 などを掛ける）、なだらかな丘。
- △ 円錐屋根は高さ/半径 1.5〜3 が中世の塔らしい。ドームは rise=r（半球）〜1.3r。
- 既存の `arch_helpers.tile_roof / gable_roof`（1:2 勾配・和風の軒反り）は和風建築で引き続き使う。

## 6. 構成・モジュール・繰り返し
- **部品化と回転複製**：`stamp(b, part, at, turns, mirror)` は部品の (0,0,0) を at に置いて回す。階段・扉・柵・レール・看板の向き、BE、エンティティ（Pos と yaw）まで正しく変換する。
  - ブロック状態の変換規則（`rotate_state/mirror_state`）：facing を時計回り（north→east→south→west）／axis x↔z／rotation(0–15) +4／柵・壁・板ガラスの north..west 接続を回す／レールの shape／ミラーでは階段の shape・扉の hinge・チェストの type の left↔right を交換。
  - △ Axiom の「任意角回転」は向き情報が崩れる恐れ（research_notes §A）。コード側で 90° 単位に回して書き出すのが安全。
- **同じ部品を並べすぎない**：回転・反転・材質の差し替え・欠けを混ぜる（3種以上の変種）。
- **配置**：`poisson_disk(x0,z0,x1,z1, r)` で木・岩・家を「均等すぎず固まりすぎず」。道・川・城壁の平面線形は `catmull_rom`（制御点を通る）。
- **ロープ・吊り橋・飾り紐**：`catenary(a, b, sag)` → `polyline` で格子化（6近傍で途切れない）。鎖は進行方向から axis を決める（例 showcase §5）。

## 7. 有機物（樹木・岩・雲）
- ○ 幹は**根元を太く上で細く**（階段・ハーフで丸める）。枝の密度は樹種で変える（オーク=細かく多い、トウヒ=長く幹に沿う）。傾いた木は傾く側に下枝を1本、枝の大半は傾く方向へ。大枝は全方向に小枝を出してどの角度からも密に見せる。樹冠の輪郭は不規則に、オークは下より上へ広がる。浮いた葉は最後に刈る（[PlanetMinecraft 樹木チュートリアル](https://www.planetminecraft.com/blog/how-to-make-custom-trees-/) ほか複数）。
- ○ 実物の写真を参照してから作る。森は1本ずつでなく WorldPainter 等で配置（大量配置の定石）。
- 実装：`organic_tree(b, x,y,z, height, spread, trunk_r, depth, lean, leaf_r)`：再帰分岐（各段 2〜3 本・上向きに曲がる）、ベジェの tube で先細り、先端に殻状の葉の塊、根張り4本。`lean=(dx,dz)` で傾ける。
- 岩・雲・有機的な建築：`sd_smooth_union`（なめらかに融合）＋`sd_displace`（fbm で表面を揺らす）→ `fill_sdf(shell=2)` で殻だけ。

## 8. 式で形を作る（SDF / WorldEdit //generate 相当）
- ◎ WorldEdit の `//generate` は**ブロックごとに式を評価し、内側で正・外側で 0 以下**になる式で形を作る。トーラス・傾いた円柱・波など「式で書ける形なら何でも」。`-h` で中空（[WorldEdit docs: Generation](https://worldedit.enginehub.org/en/7.3.19/usage/generation/)）。
- このスキルの `fill_sdf` は符号が逆（**内側が負**の距離関数）で、`shell=厚み` が `-h` に当たる。部品：`sd_sphere/ellipsoid/box(round_)/cylinder/cone/torus/capsule`、合成 `sd_union/intersect/subtract/smooth_union/displace`。
- 例：アーチ橋＝`sd_subtract(sd_box(...), sd_cylinder(axis='x'))`、要塞の稜堡＝`sd_intersect` で多角柱、浮島の底＝`sd_displace(sd_cone(...))`。

## 9. 手続き生成の知見（GDMC など）
- ○ GDMC（AI による集落生成コンテスト）の評価軸は **美観・物語性・機能性・地形への適応**（[GDMC 関連](https://science.ecosyste.ms/projects/19172)）。→ 生成物でも「地形に沿わせる」「使える（歩ける・入れる）」「由来の物語」を意識する。
- ○ Wave Function Collapse で建物・階の間取りを作る例がある（MGAIA-Minecraft、2024 の GDMC 作品）。固定セル（中庭など）を先に置いて周りを生成できる。一方、素の WFC は集落生成には不向きという研究もある（[Trinity Univ. 論文](https://digitalcommons.trinity.edu/compsci_honors/69)）。→ このスキルでは「部品（stamp）＋ルール（間隔・向き・地形）」の方が扱いやすい（△）。

## 10. 負荷と軽量化
- `hidden_cells(b)`：6面とも不透明フルブロックに囲まれた見えないセル。内部空間の無い塊（山・城壁の芯）の中身を抜くとブロック数とビューア容量が大きく減る。**内部のある建物・ダンジョンには使わない**（BFS 検査が壊れる）。
- 樹冠・ドームは殻（既存の `Build.shell`、`fill_sdf(shell=)`）。

## 11. 仕上げのチェックリスト（実装と対応）
- [ ] 遠景2方向でシルエットに凹凸がある（尖塔・煙突・ドーマー・バットレス）
- [ ] 屋根に勾配と軒の出、壁より暗い材（`smooth_heightfield`）
- [ ] 窓は 1 マス奥、窓台と額縁（`opening(depth=1, sill=, frame=)`）
- [ ] 壁は下から上へグラデ（`grad_pick`）、付け柱か控え壁でリズム
- [ ] 基礎で土を隠す。地形の縁は階段/ハーフでなだらか（`terrain(smooth_top=)`）
- [ ] 部品の繰り返しは回転・反転・変種（`stamp`）
- [ ] 風化は控えめ（`weather(amount≤0.4)`）、主役を隠さない
- [ ] `palette_stats` で主材が 60％前後
- [ ] プレビュー（`render_preview.py --yaw 0/1/2/3 --scale 12〜16`）で拡大して窓・屋根の向き・柄を確認（実践：灰色ガラスは灰色の壁に埋もれて見えなかった → 色ガラスか暗いガラスで抜く）

## 関数早見表（`scripts/advanced_helpers.py`）
| 分類 | 関数 |
|---|---|
| 変換 | `rotate_state` `mirror_state` `transform_blocks` `transform_be` `transform_entity` `stamp` |
| 曲線 | `line3d` `polyline` `catmull_rom` `catenary` `circle_cells` `ellipse_cells` `superellipse_cells` |
| SDF | `sd_sphere` `sd_ellipsoid` `sd_box` `sd_cylinder` `sd_cone` `sd_torus` `sd_capsule` `sd_union` `sd_intersect` `sd_subtract` `sd_smooth_union` `sd_displace` `fill_sdf` |
| 面・屋根 | `smooth_heightfield` `fix_stair_corners` `cone_roof` `dome_roof` `gambrel_roof` `mansard_roof` |
| 部材 | `arch_inside` `opening` `rose_window` `paint_plane` `buttress` `spire` `cornice` `pilasters` |
| 質感 | `value_noise2/3` `fbm2` `fbm3` `ridged2` `grad_pick` `weather`(`WEATHER`) `edge_trim` |
| 地形・植生 | `terrain` `thermal_erode` `poisson_disk` `organic_tree` |
| 解析 | `bbox` `hidden_cells` `palette_stats` |
