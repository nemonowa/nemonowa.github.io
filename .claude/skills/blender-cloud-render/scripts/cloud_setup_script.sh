#!/bin/bash
set -e

# ベースイメージに含まれる、ネットワークポリシーで許可されていないPPA
# (deadsnakes, ondrej/php等)を検出して削除。.list形式・.sources(deb822)形式どちらでも対応。
# これを怠ると apt-get update が403で失敗し、Setup script全体がexit code 100で落ちる。
for f in /etc/apt/sources.list.d/*; do
  if grep -q "ppa.launchpadcontent.net" "$f" 2>/dev/null; then
    rm -f "$f"
  fi
done

apt-get update

# --- 1. Blender本体(ヘッドレスレンダリングに使用。GUIは不要) ---
apt-get install -y blender

# --- 2. ヘッドレスレンダリングに必要なGLライブラリ ---
# これが無いと EEVEE/Cycles のレンダリングが
# "Couldn't open libEGL.so.1" で失敗する。
apt-get install -y libegl1 libgl1 libglx0

# --- 3. numpy(mmd_toolsアドオンが依存。MMDモデルを扱わないなら省略可) ---
# BlenderのUbuntu標準パッケージは内蔵Pythonではなくシステムpython3を使うため、
# pip install numpy ではなく apt でインストールする(pipは
# externally-managed-environment エラーで弾かれる)。
apt-get install -y python3-numpy

# --- 4. mmd_toolsアドオン(MMD/PMXモデルを扱う場合) ---
# 使用中のBlenderバージョンに対応するタグを選ぶこと。バージョン不一致だと
# import エラーで有効化に失敗する。
#   - v2.10.3(旧系列最終版): ShaderNodeTree.inputs/outputsという
#     Blender 4.0で削除されたAPIに依存しており、既存マテリアルが無い
#     フルインポート(PMX新規変換)では"'ShaderNodeTree' object has no
#     attribute 'outputs'"で失敗する。既存.blendの微修正のみなら動くことがある。
#   - main / v4.5.x以降: Blender 4.2+の`poll_file_object_drop`APIに依存し、
#     4.0系では ImportError で有効化に失敗する。
#   - v4.0.0: 実運用でBlender 4.0.2上での新規PMXインポート・PMX書き出しの
#     両方が動作することを確認済み。ただし「Blender 4.1.1向け」の
#     バージョン警告が出る(動作に影響なし)。scripts/blend_to_mmd.py側で
#     Blender 4.0系のcorner_normals遅延計算に対するworkaroundを入れている。
# 上記の理由から、Blender 4.0系(Ubuntu標準リポジトリ版)では v4.0.0 を使うこと。
MMD_TOOLS_TAG="v4.0.0"
if [ ! -d /tmp/mmd_tools_src ]; then
  git clone --depth 1 https://github.com/MMD-Blender/blender_mmd_tools.git /tmp/mmd_tools_src
fi
cd /tmp/mmd_tools_src
git fetch --tags --depth 1
git checkout "$MMD_TOOLS_TAG"

ADDON_DIR=$(blender --background --python-expr "import bpy; print(bpy.utils.user_resource('SCRIPTS', path='addons'))" 2>&1 | grep '^/')
mkdir -p "$ADDON_DIR"
rm -rf "$ADDON_DIR/mmd_tools"
cp -r mmd_tools "$ADDON_DIR/"

echo "Blender headless setup complete."
echo "使い方: スクリプト冒頭で bpy.ops.preferences.addon_enable(module='mmd_tools') を呼ぶこと"
echo "(セッションを跨ぐと有効化状態は保持されないため、毎回のスクリプトで再度有効化する)"
