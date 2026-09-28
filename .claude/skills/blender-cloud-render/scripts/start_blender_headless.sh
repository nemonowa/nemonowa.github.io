#!/bin/bash
# 参照用コピー。実体は cloud_setup_script.sh が /opt/claude-blender/scripts/ に生成する。
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
