# ピラミッド型ダンジョン「王の墓所」（スキルのキットだけで作った実例）
`python3 pyramid_dungeon.py out.bp [out_nbt.bp]` — 2本目を渡すと宝箱ルートテーブル/スポナー入り版も出力。検証結果（密閉・扉・宝箱・ボス到達）と各階マップ(/tmp/pyr_maps.png)も出る。
- 外観：高台＋階段で滑らかな45°ピラミッド（底辺69・高さ34）。四面のレリーフ（南=有翼の太陽、東西=ホルスの目、北=アンク）、スフィンクスの参道・塔門・オベリスク、風化と砂に埋もれた麓、折れ柱・崩れアーチ、星の環状列石、衛星ピラミッド、オアシス、頂上に浮かぶ太陽円盤と浮遊遺構、光の亀裂、底の水晶（`ancient_helpers` を使用）。
- 内部3層：L0 玄室→石柱の間(棘の穴×2・スポナー×2)→砂の迷宮(DFS)→螺旋↑ / L1 溶岩の渡り→中央の島の螺旋↑ / L2 王の間＋宝物庫。
- 使ったキット：`Dungeon.carve/spike_pit/lava_lake/maze/spiral/open_end/line/door/lever/chest/spawner/check_leaks/solve/render_map`、`arch_helpers.corner_stair`。
- 設計メモは `references/dungeon.md §7`（ピラミッド／上階ほど狭い立体の設計）。
- 浮島の縁と底：輪郭の揺らぎ・縁の傾斜・縞状地層の急な逆円錐・つらら/岩塊/洞窟・周囲の小島(`floating_islet`)・雲・支えパス（`references/architecture.md §10`）。
