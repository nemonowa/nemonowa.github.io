# 26.3 形式チェック

- `sample_26.3.bp` — ユーザーが Minecraft 26.3 の Axiom で保存した実ファイル（スポナー・宝箱・土・防具立て）。.bp 新形式（Version 2）の一次資料。`python3 scripts/bplib.py examples/format_check_26_3/sample_26.3.bp` で中身を確認できる。
- `format_check.py` — スキルの書き出しを実機で確かめるための小さな祠（7×6×7、166ブロック）。宝箱（ルートテーブル）・宝箱（中身直入れ）・スポナー（名前/体力/ドロップ/明るさ条件）・書見台の本・壁看板・防具立て（エンティティ）・鉄の鎖（iron_chain）を含む。

```
cd scripts && python3 ../examples/format_check_26_3/format_check.py OUT_DIR
```
貼るときは Axiom の Paste Entities を有効にする。確認してほしい点：宝箱を開けると中身が生成される／スポナーの回転するモブがゾンビ・名前「番兵」／書見台に本／看板の文字／防具立て「案内人」／ランタンを吊る鎖。
