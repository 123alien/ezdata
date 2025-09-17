# EzData 一键部署指南（全栈）

## 1) 安装 Docker / Compose（只需一次）
```bash
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER && newgrp docker
```

## 2) 克隆代码（HTTPS 或 SSH 二选一）
```bash
git clone https://github.com/123alien/ezdata.git
# 或：git clone git@github.com:123alien/ezdata.git
cd ezdata
```

## 3) 切到稳定快照（可选，推荐）
```bash
git checkout v20250917-1554
# 或使用你当前分支：git checkout nb-version-branch
```

## 4) 一键部署（全栈）
```bash
cd deploy/docker
./deploy.sh
```
启动完成后访问：
- 前端（Nginx）：http://localhost
- 后端 API：     http://localhost:8001
- 调度：          http://localhost:8002
- MinIO 控制台：  http://localhost:19001（账号 minio / 密码 ezdata123）

## 常用运维
```bash
docker compose ps
docker compose logs -f --tail=200
docker compose restart <service>
docker compose down
```

## 端口或权限问题
- 端口冲突：编辑 `deploy/docker/docker-compose.yml` 的 `ports` 后重启
- ES 权限：首次可执行
```bash
chmod -R 777 /home/dfi/Desktop/ezdata-master/deploy/docker/elasticsearch
```

## 仅后端快速起（开发用）
```bash
cd /home/dfi/Desktop/ezdata-master/api
# 可按需编辑 dev.env
docker compose up -d
```
