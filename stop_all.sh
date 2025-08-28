#!/bin/bash
set -euo pipefail

ROOT_DIR="/home/dfi/Desktop/ezdata-master"
cd "$ROOT_DIR"

for f in web_dev.pid web_api.pid scheduler_api.pid; do
  if [ -f "$f" ]; then
    kill "$(cat "$f")" 2>/dev/null || true
    rm -f "$f"
  fi
done

echo "已停止 前端/后端/调度 进程"

