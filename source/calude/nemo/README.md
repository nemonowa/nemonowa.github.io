# nemo(ネモ)3Dモデル

- `nemo.blend` … mmd_tools形式のMMDモデル(テクスチャ埋め込み・gzip圧縮保存)
- `pmx/nemo.pmx` + `pmx/textures/` … MikuMikuDance用PMX
- `build/` … 素体から再生成するスクリプト(build1: 素体整理・等身・配色・義手 / build2: 刺繍・ブーツ・肩章・襟・傷 / build_face: クール表情の焼き込み・つり目・輪郭・瞳・アホ毛/跳ね毛 / build3: 義手模様ベイク・MMDボーン化・表情・mmd_tools変換)

## 素体とクレジット(必須表記)

素体に **Seed-san**(VRM公式サンプル, https://github.com/vrm-c/vrm-specification/tree/master/samples/Seed-san)を使用しています。

- Seed-san model by VirtualCast, Inc.
- License: VRM Public License 1.0 (https://vrm.dev/licenses/1.0/)
  - 改変: 可(改変物の再配布も可) / クレジット表記: 必須

## 仕様

- 身長 約1.76m(nowaの約1.1倍)、A字ポーズ、MMD標準ボーン(nowaと同じ英語名＋日本語name_j、センター/グルーブ/足IK/つま先IK)
- nowa用VMDをそのまま流用可能(`vmd_to_action.py`で確認済み)
- 表情モーフ: まばたき/ウィンク/ウィンク右/笑い/あいうえお/上/下/怒り/困る/にこり 等(計43)
- 左前腕〜指先: 黒装甲に赤いパネルライン(テクスチャにベイク済み)
- 髪の揺れ物(剛体物理)は未設定
