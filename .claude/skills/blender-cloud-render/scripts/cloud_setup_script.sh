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
# import エラーで有効化に失敗する。Ubuntu標準リポジトリのBlender(4.0系)には
# v2.10.3系が対応。Blender 4.2+ を別途導入する場合は main ブランチでよい。
MMD_TOOLS_TAG="v2.10.3"
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
