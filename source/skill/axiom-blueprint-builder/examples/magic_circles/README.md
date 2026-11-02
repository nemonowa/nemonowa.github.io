# 平面の文様・魔法陣
- `magic_circles.py [出力dir]` — 幾何学の魔法陣（紅と金・十二芒星＋フラワー・オブ・ライフ）とルーンの魔法陣（藍と金・エルダー/ヤンガー・フサルク）を .bp と上面図PNGに出力。色は `PAL_*` を替えるだけ。
- `digitize_image.py image proto.json out.bp [--fold --dark 色 --outer 色,色 --tips 色]` — ブロック絵の真上写真 → .bp。`proto_purple_mandala.json` は実例（紫の曼荼羅の代表色）。
- 手順・失敗談: `references/patterns.md`。ヘルパー: `scripts/pattern_helpers.py`（自己テスト: `python3 pattern_helpers.py`）。
