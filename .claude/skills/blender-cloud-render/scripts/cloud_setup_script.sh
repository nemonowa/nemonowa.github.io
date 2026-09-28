#!/bin/bash
set -e

# ベースイメージに含まれる、ネットワークポリシーで許可されていないPPA
# (deadsnakes, ondrej/php)を検出して削除。.list形式・.sources(deb822)形式どちらでも対応。
for f in /etc/apt/sources.list.d/*; do
  if grep -q "ppa.launchpadcontent.net" "$f" 2>/dev/null; then
    rm -f "$f"
  fi
done

# --- 1. Blender本体(ヘッドレスレンダリングに使用。GUIは不要) ---
apt-get update
apt-get install -y blender

# --- 2. uv (Pythonパッケージマネージャ) ---
pip install uv --break-system-packages || true

# --- 3. minihellboy/claude-blender を取得してMCPサーバーの依存関係を用意 ---
if [ ! -d /opt/claude-blender ]; then
  git clone https://github.com/minihellboy/claude-blender /opt/claude-blender
fi
cd /opt/claude-blender
uv sync

# --- 4. セッション開始時に使うヘッドレス起動スクリプトを配置 ---
# (start_blender_headless.sh の内容。SessionStart フックから呼び出す)
cat > /opt/claude-blender/scripts/start_blender_headless.sh << 'HEADLESS_EOF'
#!/bin/bash
# クラウドセッションでのみ動作。ローカル実行時は何もしない。
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

PORT=9876

# 既存プロセスがポートを掴んでいれば健全性を確認し、応答がなければ掃除してから再起動
if lsof -i :"$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
  if timeout 2 bash -c "echo > /dev/tcp/127.0.0.1/$PORT" 2>/dev/null; then
    echo "Blender headless server already running on port $PORT."
    exit 0
  fi
  fuser -k "$PORT"/tcp 2>/dev/null || true
  sleep 1
fi

cd /opt/claude-blender
nohup blender --background --python scripts/headless_blender.py -- --port "$PORT" \
  > /tmp/claude_blender_headless.log 2>&1 &
disown

# ポートが開くまで最大15秒待つ
for i in $(seq 1 15); do
  if timeout 1 bash -c "echo > /dev/tcp/127.0.0.1/$PORT" 2>/dev/null; then
    echo "Blender headless server is up on port $PORT."
    exit 0
  fi
  sleep 1
done

echo "WARNING: Blender headless server did not come up within 15s. Check /tmp/claude_blender_headless.log"
exit 0
HEADLESS_EOF

chmod +x /opt/claude-blender/scripts/start_blender_headless.sh

echo "Blender headless setup complete."
