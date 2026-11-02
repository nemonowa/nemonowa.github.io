# 浮遊島＋聖樹ダンジョン（春・夏・秋）
`python3 island_dungeon.py --theme summer --out /mnt/user-data/outputs` →
`samples/<theme>_island_dungeon.bp`（宝箱・スポナー入り）／`_noBE.bp`／`<theme>_map_L0..L3.png`／`<theme>_commands.txt`。
所要1〜2分。検証結果（密閉・扉・宝箱）が標準出力に出る。素材と意匠は `themes.py`、設計と失敗談は `references/island_dungeon.md`。
142×139×134・約17万〜21万ブロック。BE（宝箱の中身・スポナー）は実機確認済み。扉は両側に壁レバー（`door_levers`）。
