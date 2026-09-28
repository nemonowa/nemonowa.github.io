---
name: blender-cloud-render
description: "Claude CodeのクラウドセッションでBlenderを使って3Dモデルの編集・レンダリング・アニメーション作成を行う際に必ず使用するスキル。GUIが存在しないヘッドレス環境で、MCPサーバーを介さず`blender --background --python`を直接呼び出すワークフローを提供する。ユーザーが「Blenderでモデルを作って/直して」「シーンをレンダリングして」「.blendファイルを操作して」「MMDモデルを調整して」などと言った場合、特にそれがクラウドセッション/リモートサンドボックス上での作業である場合は、このスキルを必ず参照すること。"
---

# Blender Cloud Render(ヘッドレス運用スキル)

Claude Codeのクラウドセッション(claude.ai/code等)はGUIを持たないUbuntu 24.04のVMなので、
Blenderを開いてアドオンをインストールする通常のワークフローは使えない。

**重要な方針転換**: 当初は`minihellboy/claude-blender`のようなMCPサーバー経由でBlenderを
常駐プロセスとして操作する方式を想定していたが、Setup scriptの安定稼働・ポート待受・
セッション間の再起動などの管理コストが高く、実運用では機能しなかった。
**代わりに、都度 `blender --background <file.blend> --python <script.py>` を
Bashツールで直接実行し、bpyスクリプトでシーンを操作してPNGに書き出し、
Readツールで画像を確認する」というシンプルな方式が確実に動作する。本スキルはこちらを正式な手順とする。**

## 基本ワークフロー

1. **スクリプトを書く**: 操作したい内容(マテリアル修正、ライト配置、レンダリング等)を
   1つのPythonスクリプトとしてスクラッチパッドに書く(`bpy`を直接操作)。
2. **ヘッドレス実行**:
   ```bash
   blender --background path/to/model.blend --python /path/to/script.py 2>&1 | tail -N
   ```
   `--background`必須。GUIが無いので`--python-expr`で短いワンライナーも可。
3. **画像で確認**: スクリプト内で`bpy.ops.render.render(write_still=True)`してPNGに書き出し、
   Readツールで**必ず目視確認する**。「エラーなく実行できた」は成功の証拠にならない。
   構図のズレ、白飛び、テクスチャ欠落、不自然な陰影は画像を見て初めて分かる。
4. **保存**: 確認が取れたら`bpy.ops.wm.save_as_mainfile(filepath=...)`で元ファイルに上書き保存。
5. **反復**: 3〜4を繰り返し、都度スクラッチパッドに軽量プレビュー(EEVEE・低解像度・低サンプル)を
   出力して素早く確認する。最終版のみCyclesで高解像度レンダリングする。

この方式はMCPサーバーのプロセス管理が不要で、セッションが再起動しても
Blender本体さえインストール済みならそのまま動く。

## 初回セットアップ

### Cloud environmentの「Setup script」欄

`scripts/cloud_setup_script.sh` の内容をそのままコピーして、クラウド環境設定ダイアログの
Setup script欄に貼り付けるようユーザーに案内する。内容の要点(すべて実運用で踏んだ
トラブルの対処を含む):

- **ベースイメージ内蔵のPPA(deadsnakes, ondrej/php)を先頭で除去**してから`apt-get update`。
  これを怠ると`ppa.launchpadcontent.net`への403エラーでSetup script全体がexit code 100で
  失敗する(このネットワークポリシーでは当該PPAへのアクセスが許可されていない)。
  `.list`形式だけでなく`.sources`(deb822)形式でも定義されうるため、拡張子を決め打ちせず
  内容に`ppa.launchpadcontent.net`を含むファイルを検出して削除すること。
- `apt-get install -y blender` でBlender本体を導入(Ubuntu標準リポジトリ版で十分)。
- **`libegl1 libgl1 libglx0`を追加インストール**。これが無いとEEVEE/Cyclesの
  ヘッドレスレンダリングが`Couldn't open libEGL.so.1`で失敗する。
- **`python3-numpy`を追加インストール**。MMDモデルを扱う場合`mmd_tools`アドオンが
  numpyに依存しており、無いとアドオン有効化時に`ModuleNotFoundError: No module named 'numpy'`
  で失敗する。Blenderのapt版は内蔵Pythonではなくシステムpython3を使うため、
  `pip install numpy`ではなく`apt install python3-numpy`が正解(pipは
  `externally-managed-environment`エラーで弾かれる)。
- MMDモデル(.pmx/.vmd等)を扱う場合は`mmd_tools`アドオンも導入する(下記参照)。

### mmd_toolsアドオンの導入(MMD/PMXモデルを扱う場合のみ)

Blenderにデフォルトでは入っていない。`MMD-Blender/blender_mmd_tools`リポジトリから、
**使用中のBlenderバージョンに対応するタグ**を選んでクローンすること。バージョン不一致だと
importエラーで有効化に失敗する(例: mainブランチはBlender 4.2+専用で、
Ubuntu標準リポジトリのBlender 4.0.2では`poll_file_object_drop`のImportErrorになる)。

```bash
git clone --depth 1 https://github.com/MMD-Blender/blender_mmd_tools.git /tmp/mmd_tools_src
cd /tmp/mmd_tools_src && git checkout v2.10.3   # Blender 3.6〜4.0系向け。4.2+ならmainでよい
ADDON_DIR=$(blender --background --python-expr "import bpy; print(bpy.utils.user_resource('SCRIPTS', path='addons'))" 2>&1 | grep -v '^Blender\|^$')
mkdir -p "$ADDON_DIR"
cp -r mmd_tools "$ADDON_DIR/"
```

有効化はスクリプト冒頭で毎回行う(セッションを跨ぐと消えるため):
```python
import bpy
bpy.ops.preferences.addon_enable(module='mmd_tools')
```

## レンダリング設定の勘所

- **カラーマネジメント**: Blender 4.0以降はデフォルトで`AgX`ビュートランスフォームが
  設定済み。これ自体は適切なので変更不要。
- **白飛びの主因はライト強度**: エリアライトの`energy`(W)は、身長1〜2m程度の
  キャラクターに対して**数十W程度**が適正(キー30〜50W、フィル10〜20W、リム15〜25W目安)。
  MCPやテンプレートを参考に数百Wを設定すると、AgXでも白飛びする。実際に600/250/350Wで
  白飛びし、35/12/18Wまで下げて自然な発色になった実績あり。
  白すぎる/眠い絵になったら、まずライトの`energy`を疑うこと。
- **露出とルック**: `scene.view_settings.exposure`を-0.2〜-0.5程度、
  `scene.view_settings.look`を`"AgX - Medium High Contrast"`等に設定すると
  色が締まって見栄えが良くなる(look文字列は`"AgX - "`プレフィックス必須、
  素の`"Medium High Contrast"`だけでは`enum not found`エラーになる)。
- **Cyclesのデノイザーが無い場合がある**: Ubuntu標準リポジトリのBlenderは
  `Build without OpenImageDenoiser`でビルドされていることがある。
  `scene.cycles.use_denoising = True`のままレンダリングすると
  `RuntimeError: Error: Build without OpenImageDenoiser`で落ちるので、
  デノイザーが使えるか不明な場合はまず`False`で試す。ノイズが気になる場合は
  サンプル数を増やす(128サンプル程度でCPUレンダリングなら1カット数分で収まる)。
- **ドラフトはEEVEE、最終はCycles**: `scene.render.engine`を`'BLENDER_EEVEE'`(下書き、
  低サンプルで数秒)→`'CYCLES'`(最終、128サンプル程度)と切り替える。

## MMD/PMX由来モデルを扱う際の典型的な不備と直し方

MikuMikuDance(MMD)からmmd_tools経由でインポートした.blendを修正する場合、
以下は**ほぼ必ず**発生する問題なので、作業前に一通りチェックすること。

1. **テクスチャの絶対パス切れ**: 元制作者のローカルMMDフォルダ
   (`//../3D Objects/MMD/.MikuMikuDance/...`等)を参照したままになっている。
   `bpy.data.images`を走査し、`os.path.basename(img.filepath)`で実際のtx/フォルダ内
   ファイルと突き合わせて`img.filepath`を再設定する。
2. **透過マテリアルの`blend_method`が`OPAQUE`のまま**: ノードのアルファ接続自体は
   正しくても、`mat.blend_method`が`OPAQUE`だとEEVEEがアルファを無視して不透明描画する。
   「_透過」等の名前がつくマテリアルは`'HASHED'`に修正する。
3. **縮退面(ゼロ面積フェイス)**: `bmesh`で`f.calc_area() < 1e-8`なフェイスを検出し、
   `bmesh.ops.dissolve_degenerate()`で除去する。変換時のノイズとして数十枚程度出ることがある。
4. **カメラ・ライトが無い**: mmd_toolsインポート直後のシーンにはカメラもライトも
   無いことが多い。バウンディングボックスから中心・高さを算出してカメラを自動フィットさせ、
   3点照明を追加する。
5. **チェックはするが直さなくてよいもの**: 非マニフォールドエッジ(薄い布地の
   レイヤー構造上、数千〜数万件出るのが正常)、同一座標の重複頂点(UVシーム・パーツ境界で
   意図的に分離されている)は、MMDモデルの構造上正常なので統合・修正不要。

### 配布・実機確認用にテクスチャを埋め込む

外部リンクのままファイルだけ渡すと、別環境でテクスチャが読み込めず単色表示になる。
配布前に必ずパックする:
```python
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=...)
```
埋め込むとファイルサイズが増える(今回の例で約6MB→37MB)。SendUserFileには30MiB制限が
あるため、送信直前に圧縮保存すること:
```python
bpy.ops.wm.save_as_mainfile(filepath="compressed.blend", compress=True)
```
gzip圧縮でも実機のBlenderは拡張子`.blend`のままそのまま開ける。

### ボーン・マテリアル・モーフ名の英語化(命名統一)

MMDモデルは日本語ボーン名が標準。英語化する場合:

- **ボーン**: `pose_bone.mmd_bone.name_e`にmmd_tools側の英訳が入っていることが多いが、
  **空文字や重複(スカート・内スカート・リボンフリルが全て`Skirt_x_y`になる等)がある**ため
  機械的に使わず、カテゴリで衝突を避けつつ辞書変換で補完する。
  リネームは**Armature Edit Mode**で`edit_bone.name = "new_name"`を実行すると、
  **頂点グループ名は自動的に追従してリネームされる**(Blenderの仕様、手動リネーム不要)。
  ボーンコンストレイントの`subtarget`やアクションのFカーブ`data_path`も自動修正される。
- **マテリアル・モーフ**: `mmd_material.name_e`や`morph.name_e`は空/重複/日本語のままの
  ことが多く信頼できないため、独自辞書で変換するのが確実。
  頂点モーフをリネームする際は`key_blocks[name].name`(シェイプキー本体)を変更すれば、
  `mmd_root.vertex_morphs`側の登録名やグループモーフのメンバー参照(`d.name`)は
  **自動的に追従する**(mmd_tools側がシェイプキー名を動的参照しているため、手動同期不要)。
  UVモーフだけは関連頂点グループが`UV_<モーフ名>+X`/`-X`/`+Y`/`-Y`という命名規則で
  紐づいているため、モーフ名を変える際はこれらの頂点グループ名も合わせてリネームすること。
- **リネーム後は必ず検証する**: コンストレイントの`subtarget`が存在するボーンを
  指しているか、頂点グループがボーン名と対応しているか、アクションのFカーブ`data_path`が
  有効なボーン/プロパティを指しているかをスクリプトでチェックし、その後レンダーして
  見た目が変わっていないことを確認する。

## アニメーション作成

- **表情**: mmd_toolsの`mmd_root.vertex_morphs`/`uv_morphs`/`group_morphs`が
  既存であればそれを使う。頂点モーフはシェイプキーそのものなので、
  `key_blocks[name].value`にキーフレームを打てば動く(`keyframe_insert(data_path="value", frame=N)`)。
  MMDモデルは目・口周りのモーフ変位が意図的に小さい(0.003〜0.006程度)ことがあり、
  「アニメが効いていないように見える」ことがあるが、これはバグではなく仕様であることが多い。
  怪しい場合は`kb.data`と`basis.data`の座標差(delta)を計測して実際の変位量を確認すること。
- **ボーンモーション**: `pose_bone.rotation_euler`にキーフレームを打つ。ただしMMD由来の
  リグはローカル軸が直感的でない(ボーンロールが独特)ことが多く、汎用的な角度指定では
  ポーズが破綻しやすい。角度を大きく動かす前に少量で試してレンダー確認し、
  リグの実際の回転方向を把握してから本番角度を詰めること。
- **配布モーション(VMD)の流用は著作権に注意**: MMDコミュニティのVMD配布は個別の
  利用規約(クレジット必須・二次配布禁止等)が一般的で、CC0/商用可を明記したものは稀。
  出典不明なVMDをそのまま公開リポジトリに組み込まない。権利関係が不明な場合は
  ユーザーに確認するか、Mixamo(要リターゲット)や新規作成を提案する。

## 大きいバイナリファイルの取り扱い

- `.blend`は数十MB規模になりやすい。SendUserFileは30MiB制限があるため、
  送信前に`compress=True`保存を検討する。
- リポジトリへのコミットも同様にサイズに注意。テクスチャ埋め込み後は
  特にサイズが増えるので、変更内容とサイズ増加をコミットメッセージに明記しておくと親切。

## 注意点・トラブルシューティングまとめ

| 症状 | 原因 | 対処 |
|---|---|---|
| Setup scriptがexit code 100 | ベースイメージのPPAが403 | 先頭でPPAファイルを検出・削除してから`apt-get update` |
| `Couldn't open libEGL.so.1` | GL関連ライブラリ不足 | `apt-get install -y libegl1 libgl1 libglx0` |
| mmd_tools有効化で`ModuleNotFoundError: numpy` | システムpython3にnumpyが無い | `apt-get install -y python3-numpy`(pipは使わない) |
| mmd_tools有効化で`ImportError: poll_file_object_drop`等 | Blenderバージョンとmmd_toolsのバージョン不一致 | 使用中のBlenderに対応するタグをcheckoutする |
| レンダリングが`Build without OpenImageDenoiser`で失敗 | Cyclesデノイザー非搭載ビルド | `scene.cycles.use_denoising = False` |
| レンダリングが白飛びする | エリアライトのenergyが桁違いに大きい | 数十W程度まで下げる。AgX任せにしない |
| 実機で単色/テクスチャなし表示になる | テクスチャが外部リンクのまま | `bpy.ops.file.pack_all()`で埋め込む |
| SendUserFileが30MiB超で失敗 | .blendが大きい | `compress=True`で圧縮保存してから送信 |
| ボーンリネーム後に壊れていないか不安 | - | コンストレイント・頂点グループ・Fカーブの整合性チェックスクリプトを走らせ、レンダーで目視確認 |
