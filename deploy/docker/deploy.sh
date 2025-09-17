#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT_DIR"

export COMPOSE_PROJECT_NAME=ezdata

echo "[1/3] 检查环境文件 deploy.env ..."
if [ ! -f deploy.env ]; then
  echo "未找到 deploy.env，复制示例为 deploy.env 并继续"
  cp -f deploy.env deploy.env.bak 2>/dev/null || true
fi

echo "[2/3] 启动/更新全栈服务 (MySQL/Mongo/MinIO/ES/Nginx/后端/调度) ..."
docker compose pull || true
docker compose up -d

echo "[3/3] 健康检查 ..."
docker compose ps

echo
echo "服务访问地址："
echo "- 前端:      http://localhost"
echo "- 后端 API: http://localhost:8001"
echo "- 调度:      http://localhost:8002"
echo "- MinIO:     http://localhost:19001 (user=minio, pass=ezdata123)"
echo "- Elastic:   http://localhost:9200"
echo
echo "日志查看： docker compose logs -f --tail=200"
echo "停止：     docker compose down"
echo "仅重启某项：docker compose restart <service>  (如 api/web/scheduler/mysql 等)"

