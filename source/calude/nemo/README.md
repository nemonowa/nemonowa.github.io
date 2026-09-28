# nemo(ネモ)3Dモデル

## 収録物
- `nemo.blend` … 2服装を1ファイルに同梱(mmd_tools形式、テクスチャ埋め込み・圧縮保存)
  - コレクション「軍服 (military)」… 既定で表示
  - コレクション「白礼装 (formal)」… 非表示。アウトライナーでチェックを切り替えて表示
- `pmx/military/nemo_military.pmx` … 服装A: 紅い軍服(黒Yシャツ・コンバットズボン・戦闘用ブーツ)
- `pmx/formal/nemo_formal.pmx` … 服装B: 白礼装(詰め襟の上衣・肩ケープ+ロングマント・白の紐靴)。マントは揺れ物(剛体29/ジョイント36)
- `build/` … 素体から全服装を再生成するスクリプト一式(`build_all.sh <作業dir> <出力dir>`)

## 生成手順(build_all.sh)
build1(素体整理・等身・配色・義手) → build2(傷ほか) → build_face(表情・目・輪郭・アホ毛) →
build_base(土台の服。`NEMO_OUTFIT=white`で白礼装版) → build_coat(上着) →
[白礼装のみ] build_cape(肩ケープ・マント・揺れボーン) → build3(MMDボーン化・表情・変換) →
[白礼装のみ] build_physics(剛体・ジョイント) → PMX書出し/再読込 → merge_outfits(2服装を1つの.blendへ) → finalize

## 素体とクレジット(必須表記)
素体に **Seed-san**(VRM公式サンプル, https://github.com/vrm-c/vrm-specification/tree/master/samples/Seed-san)を使用しています。
- Seed-san model by VirtualCast, Inc.
- License: VRM Public License 1.0 (https://vrm.dev/licenses/1.0/) — 改変: 可(改変物の再配布も可) / クレジット表記: 必須

## 仕様
- 身長 約1.76m、A字ポーズ、MMD標準ボーン(nowaと同じ英語名+日本語name_j、センター/グルーブ/足IK/つま先IK)。nowa用VMDをそのまま流用可
- 表情モーフ45種(基本表情は余裕の笑み。真顔・ニヤリウィンク等を追加)
- 左前腕〜指先は義手(黒装甲に赤いライン)。両服装とも袖口に金属ジョイントで接続
