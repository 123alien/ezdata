#!/bin/bash
set -euo pipefail

ROOT_DIR="/home/dfi/Desktop/ezdata-master"
cd "$ROOT_DIR"

# 启动后端（虚拟环境 + nohup）
source "$ROOT_DIR/ezdata/bin/activate"
export read_env=1 ENV=dev.env

cd "$ROOT_DIR/api"
nohup python web_api.py > "$ROOT_DIR/web_api.out" 2>&1 & echo $! > "$ROOT_DIR/web_api.pid"
sleep 1
nohup python scheduler_api.py > "$ROOT_DIR/scheduler_api.out" 2>&1 & echo $! > "$ROOT_DIR/scheduler_api.pid"
sleep 1

# 启动前端（nohup）
cd "$ROOT_DIR/web"
if command -v pnpm >/dev/null 2>&1; then
  nohup pnpm dev > "$ROOT_DIR/web_dev.out" 2>&1 & echo $! > "$ROOT_DIR/web_dev.pid"
else
  nohup npm run dev > "$ROOT_DIR/web_dev.out" 2>&1 & echo $! > "$ROOT_DIR/web_dev.pid"
fi

echo "已启动：\n - 后端: http://localhost:8001 \n - 调度: http://localhost:8002 \n - 前端: http://localhost:8080"

