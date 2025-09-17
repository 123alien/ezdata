# 项目数据库与存储总结

## MySQL（关系型，主业务库）
- 端口/目录: 3306；`deploy/docker/mysql/`
- 用途：
  - 用户、权限、菜单、租户等系统元数据
  - 数据模型与字段、数据接口配置
  - 任务与调度元数据、执行记录
  - RAG 绑定关系等业务表（如 `rag_kb_binding`）
- 备份建议：停服务或一致性快照；本项目已支持按卷打包 tar.gz 方案

## MongoDB（文档/时序，采集数据）
- 端口/目录: 27017；`deploy/docker/mongodb/`
- 用途：
  - 设备/物联网采集原始快照与时序数据
  - 示例字段：`device_num / factor_code / factor_value / update_time`
- 优势：结构灵活、写入快，适合高频数据落盘

## Redis（缓存/队列）
- 端口: 6379（AOF 持久化）
- 用途：
  - API 缓存（如 AkShare K 线默认参数等）
  - Celery broker 与短期消息
- 默认密码：`ezdata123`（见 compose）

## MinIO（对象存储）
- 端口/目录: 9000（API）、19001（Console）；`deploy/docker/minio/`
- 用途：
  - 文件/文档存储（知识库文档、ETL 产物）
  - TrustRAG 通过公有/签名 URL 抓取文件进行索引
- 注意：公有桶便于 RAG 拉取；外网时关注最小权限和凭证管理

## Elasticsearch（检索/日志/索引）
- 端口/目录: 9200/9300；`deploy/docker/elasticsearch/`
- 用途：
  - 日志、检索类能力
  - 可作为文本/向量索引的底座（当前版本主要由 TrustRAG 负责向量）
- 部署注意：首次可能需 `chmod -R 777 deploy/docker/elasticsearch`

## TrustRAG（外部服务，非本仓容器）
- 作用：
  - 基于 MinIO 文件与命名空间（namespace）完成嵌入/检索
  - 与后端通过 JWT SSO、命名空间、MinIO URL 交互
- 资源：GPU/显存敏感；索引变化可能需要重启加载

---

## 数据流向（简述）
- 文件/文档 → MinIO（对象） → TrustRAG 建索引/检索
- 结构化配置/元数据/调度 → MySQL
- 设备/时序数据 → MongoDB
- 队列/缓存 → Redis
- 日志/检索 → Elasticsearch

---

## 备份与恢复（要点）
- 备份：已在 `/home/dfi/backup` 生成 mysql/mongodb/minio/elasticsearch 对应的 `*-backup-YYYYMMDD-HHMM.tar.gz`
- 恢复（以 MySQL 为例）：
  1. `docker compose down`
  2. 清空 `deploy/docker/mysql/`
  3. `tar -xzf /home/dfi/backup/mysql-backup-YYYYMMDD-HHMM.tar.gz -C deploy/docker`
  4. `docker compose up -d`

---

## 端口/路径速查
| 组件 | 端口 | 数据目录 |
|---|---|---|
| MySQL | 3306 | `deploy/docker/mysql/` |
| MongoDB | 27017 | `deploy/docker/mongodb/` |
| Redis | 6379 | N/A（AOF 持久化） |
| MinIO | 9000 / 19001 | `deploy/docker/minio/` |
| Elasticsearch | 9200 / 9300 | `deploy/docker/elasticsearch/` |
