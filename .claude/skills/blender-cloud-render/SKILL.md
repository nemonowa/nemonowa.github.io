---
name: blender-cloud-render
description: "Claude CodeのクラウドセッションでBlenderを使って3Dシーンを作成・レンダリングする際に必ず使用するスキル。GUIが存在しないヘッドレス環境でminihellboy/claude-blender(MCP)を使ってBlenderを操作し、レンダリング画像を見ながら反復調整するワークフローを提供する。ユーザーが「Blenderでモデルを作って」「シーンをレンダリングして」「3Dモデルを作成して」「.blendファイルを操作して」などと言った場合、特にそれがクラウドセッション/リモートサンドボックス上での作業である場合は、GUIが使えない前提でこのスキルを必ず参照すること。初回セットアップがまだの場合は、このスキルのセットアップスクリプトを案内すること。"
---

# Blender Cloud Render(ヘッドレス運用スキル)

Claude Codeのクラウドセッション(claude.ai/code、`claude --cloud`等)はGUIを持たないUbuntu 24.04のVMなので、
Blenderを開いてアドオンをインストールする通常のワークフローは使えない。このスキルは
**minihellboy/claude-blender**をヘッドレスモードで動かし、「作る→レンダリングして見る→直す」の
反復ループをクラウドセッション内で成立させるための手順をまとめたもの。

## このスキルが前提とすること

- セッションはUbuntu 24.04のVM、目安で4 vCPU / 16GB RAM / 30GBディスク
- シェルには直接入れず、ClaudeがVM上でコマンドを代行実行する
- ネットワークは「Trusted」レベルでよい(`archive.ubuntu.com`、`github.com`、`pypi.org`はすべて標準許可済み)
- GUIビューポートは存在しないので、`blender_screenshot`(ビューポートキャプチャ)や`blender_undo`は使えない。
  代わりに`blender_render`でPNGに書き出し、その画像を見て判断すること

## 初回セットアップ(未設定なら案内する)

### 1. Cloud environmentの「Setup script」欄に登録するスクリプト

`scripts/cloud_setup_script.sh` の内容をそのままコピーして、クラウド環境設定ダイアログの
Setup script欄に貼り付けるようユーザーに案内する。内容の要点:

- `apt-get install -y blender` でBlender本体を導入(Ubuntuのリポジトリに含まれるバージョンでよい。ヘッドレスレンダリングには十分)
- `uv`をインストールし、`minihellboy/claude-blender`を`/opt/claude-blender`にクローンして`uv sync`
- 5分以内に終わるよう、重い処理は並列化してある

### 2. 作業リポジトリに `.mcp.json` を追加してコミット

作業対象のリポジトリのルートに以下を追加し、コミットしておく(プロジェクトスコープのMCP設定は
単一リポジトリのセッションで自動的に読み込まれる)。

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["run", "--project", "/opt/claude-blender", "claude-blender"],
      "env": {
        "BLENDER_HOST": "127.0.0.1",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

### 3. 作業リポジトリに `SessionStart` フックを追加

ヘッドレスBlenderのTCPサーバーはプロセスなので、環境キャッシュには残らない(ファイルは残るがプロセスは
残らない)。**セッションが始まるたびに起動し直す**必要がある。`.claude/settings.json` に以下を追加する。

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "bash /opt/claude-blender/scripts/start_blender_headless.sh"
          }
        ]
      }
    ]
  }
}
```

`scripts/start_blender_headless.sh`(このスキルに同梱)は、クラウドセッションでのみ
(`CLAUDE_CODE_REMOTE=true`のときだけ)バックグラウンドでヘッドレスBlenderを起動し、
ポート9876が開くまで数秒待ってから終了する。ローカル環境では何もしない。

上記の3点は初回だけ整えれば、Setup scriptの内容は環境キャッシュに残り、`.mcp.json`とフックは
リポジトリの一部としてコミット済みなので、以後のセッションでは自動的に有効になる。

## 毎回の作業フロー(セットアップ済みの場合)

1. **疎通確認**: 作業を始める前に `blender_ping` を呼んで応答を確認する。応答がなければ
   ヘッドレスサーバーが起動していない可能性が高いので、
   `bash /opt/claude-blender/scripts/start_blender_headless.sh` を実行してから再試行する。
2. **シーン構築**: `blender_add_object` や `blender_execute`(任意のbpyコード)でオブジェクト・
   マテリアル・ライトを組み立てる。複雑な操作をする前は `blender_checkpoint` を打っておく
   (GUIのUndoが使えないぶん、ここでの巻き戻しが頼りになる)。
3. **カメラを合わせる**: `blender_frame_camera` で対象物にカメラを自動フィットさせる。
4. **ドラフトレンダリング**: `blender_render` をまず**EEVEE・低解像度・低サンプル**の
   デフォルト設定で呼び、返ってきたPNGを実際に見て評価する。Claudeは数値チェック
   (「エラーなく実行できた」)だけで満足せず、必ず画像を見てから次に進むこと。
   ボルトの位置がずれている、ライティングが暗すぎる、オブジェクトが重なっている、
   といった問題は数値では検出できず、レンダリング画像を見て初めて分かる。
5. **反復**: 画像を見て気になった点(構図、色、影の付き方など)を指摘し、
   `blender_execute`や`blender_modify_object`で修正 → 再度`blender_render` → 目視確認、を
   ユーザーが満足するまで繰り返す。
6. **最終レンダリング**: 見た目が決まったら、必要に応じてCyclesに切り替えて解像度・サンプル数を
   上げた最終レンダリングを行う。ただしVMのリソース上限(4 vCPU/16GB RAM)を踏まえ、
   サンプル数・解像度を段階的に上げてタイムアウトしないか様子を見ること。
7. **保存とエクスポート**: `blender_save`で.blendを保存、必要なら`blender_export`でGLB/FBX等に
   書き出す。**VMはセッション終了で消えるので、成果物(.blend、レンダリング画像、GLB等)は
   作業リポジトリにコミットして持ち帰ること。**

## 注意点・トラブルシューティング

- **`blender_screenshot`や`blender_undo`はGUI専用**: ヘッドレス環境では動作しない
  (READMEにも明記されている)。ビューポートではなく`blender_render`の結果で判断する。
- **ポート競合**: セッション再開(resume)時に前のBlenderプロセスが残っていることがある。
  `blender_ping`が失敗する場合は起動スクリプトを再実行すればよい(スクリプト側で
  既存プロセスの有無を見て安全に再起動するようになっている)。
- **重いCyclesレンダリングでタイムアウトする場合**: サンプル数と解像度を下げる、
  タイル/デノイズ設定を調整する、あるいはEEVEEで最終出力までまかなうことを検討する。
- **ローカルAI系ツール(Shap-E, TripoSR等)は今回のセットアップには含めていない**:
  必要になった場合は`pip install torch diffusers transformers trimesh`等を追加の
  Setup scriptとして案内すること(重いモデルのダウンロードが発生するため、
  5分制限に収まるか確認が必要)。
