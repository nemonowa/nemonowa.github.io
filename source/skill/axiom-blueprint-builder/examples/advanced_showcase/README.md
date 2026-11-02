# 高度な建築ショーケース

`scripts/advanced_helpers.py` の関数を一通り使った例（約3.4万ブロック、71×51×69 程度）。技法の解説は `references/advanced_building.md`。

```
cd scripts && python3 ../examples/advanced_showcase/showcase.py OUT.bp
python3 render_preview.py OUT.bp out.png --yaw 0 --scale 14
```

| 部位 | 技法・関数 |
|---|---|
| 丘 | `fbm2` → `thermal_erode` → `terrain(smooth_top=)`、輪郭は `mask` にノイズ |
| 礼拝堂の壁 | `grad_pick`（丸石→石レンガ→磨き安山岩） |
| 側窓 | `opening(sharp=1.6, sill=, frame=)` 尖頭・窓台・額縁 |
| 控え壁 | `buttress(flying_to=)` フライング・バットレス |
| 正面 | 扉の尖頭アーチ＋要石、`rose_window` を `paint_plane` |
| 屋根 | `smooth_heightfield`（階段とハーフ、軒の出1） |
| 尖塔 | `spire(sides=8)` ＋避雷針 |
| 円塔 | `circle_cells` ＋ `cone_roof` |
| 洗礼堂 | `dome_roof(onion=0.5)` 銅 |
| 街灯 | 1つ作って `stamp(turns=)` で回転複製、`catmull_rom` の小道、`catenary` の鎖 |
| 大木 | `organic_tree` |
| 仕上げ | `weather(amount=0.35)`、`palette_stats` |
