# EzData 项目说明

## 1. 项目概述
EzData 是一套融合物联网数据采集、知识库管理与 RAG 问答能力的企业级数据平台。主要目标是将实时设备数据、业务文档整合到统一知识库中，并通过 TrustRAG 与前端应用（NextChat）为用户提供自然语言检索与分析能力。

## 2. 核心能力
- **数据采集**：支持电表、门禁、环境监测等设备的定时抓取与入库。
- **知识库管理**：自动生成结构化报告，上传/更新文档，并保持与 TrustRAG 的索引同步。
- **智能问答**：基于 TrustRAG 的检索增强生成，向用户提供准确的历史数据查询、指标分析与文档问答。
- **多渠道服务**：提供 Web 管理后台、NextChat 前端，以及对外开放的 REST / OpenAPI 接口。

## 3. 系统架构
- **前端层**
  - `web/`：Vue3 + Vite 管理后台与 NextChat 外接界面。
  - NextChat：通过 `nextchat.env` 配置 TrustRAG API、模型与 SSO Token。
- **后端层**
  - `api/`：Flask 应用，包含文档管理、RAG 接口、同步服务、计划任务等；同时充当 TrustRAG 的代理层。
  - `TrustRAG-main/`：FastAPI 服务，负责混合检索、rerank 与大模型生成。
- **数据层**
  - MySQL：知识库元数据、权限、文档状态。
  - MongoDB：设备原始数据存储。
  - Redis、Elasticsearch、MinIO：辅助缓存、索引及文件存储。
- **自动化脚本**
  - `device_realtime_collector.py`：环境与电表实时采集。
  - `power_meter_daily_collector.py` / `power_meter_kb_sync.py`：电表数据采集与知识库同步。
  - `door_access_collector.py` / `door_access_kb_sync.py`：门禁日志采集与同步。
  - 其他脚本可在 `docs/` 和 `scripts/` 下查阅使用说明。

## 4. 目录结构速览
- `api/`：后端服务、RAG 接口、同步逻辑、文档与脚本。
- `web/`：前端界面与 NextChat 配置。
- `deploy/docker/`：Docker Compose 配置，启动 MySQL、MongoDB、Redis、Elasticsearch、MinIO、NextChat 等依赖。
- `docs/`：JWT 权限说明、RAG 使用指南、OpenAPI 文档等。
- 根目录 `power_meter_*`、`door_access_*`、`device_realtime_collector.py` 等：独立运行的数据采集/同步脚本。

## 5. 运行环境
- 操作系统：推荐 Linux（当前部署为 Ubuntu 20.04 / kernel 5.15）。
- Python：使用 Conda 虚拟环境 `ezdata`，依赖记录在 `requirements.txt`。
- Node.js：前端构建依赖（`web/`）。
- Docker Compose：一键部署 MySQL、MongoDB、Redis、Elasticsearch、MinIO 等基础服务。
- 模型依赖：TrustRAG 需要本地模型（Qwen、BGE 等）及索引文件，可通过环境变量配置路径。

## 6. 数据与知识库流程
1. **采集阶段**：定时脚本读取第三方 API/物联网平台数据，写入 MongoDB。
2. **报告生成**：同步脚本按日期/设备整理数据，生成文本报告（包含设备信息、用电量/通行统计等）。
3. **知识库更新**：将报告作为文档写入 MySQL 知识库，触发训练/索引同步。
4. **TrustRAG 同步**：调用 `/ingest` 接口，将文本增量写入向量索引，确保问答使用最新数据。
5. **问答调用**：前端或外部系统通过 EzData 后端代理到 TrustRAG `/chat`，根据日期、设备过滤逻辑返回结果。

## 7. 关键配置
- `EZDATA_SECRET_KEY`：JWT 密钥，须在 EzData、TrustRAG、NextChat 统一。
- Namespace：电表使用 `dian`，门禁使用 `men`，可在 `KnowledgeBaseBinding` 中自定义。
- `.env` / `*.env`：数据库、第三方 API Token、TrustRAG URL、模型路径等敏感配置。
- `TRUSTRAG_*` 环境变量：指定嵌入、LLM、rerank 模型的本地路径。

## 8. 服务与脚本状态（2025-11-13）
- 常驻脚本（Conda `ezdata` 环境）：
  - `device_realtime_collector.py`
  - `power_meter_daily_collector.py`
  - `power_meter_kb_sync.py`
  - `door_access_collector.py`
  - `door_access_kb_sync.py`
- Docker 依赖：MySQL、MongoDB、Redis、Elasticsearch、MinIO、NextChat 均已启动。
- TrustRAG：运行于 `http://127.0.0.1:8217`，已接入 EzData SSO。

> 当前机器上采集/同步脚本持续运行，清理日志或打包时请避免终止正在写入的文件。

## 9. 运维建议
- **日志管理**：脚本输出建议统一放入 `logs/`，配合 logrotate 定期归档。
- **备份策略**：定期备份 MySQL、MongoDB 数据与 TrustRAG 向量索引；如需迁移，可结合 `PACKAGING_GUIDE.md` 中的打包方案。
- **监控告警**：使用 supervisor/systemd 管理采集脚本；可引入 Prometheus/Grafana 监控脚本状态、数据更新情况。
- **安全加固**：对外暴露服务需配置 HTTPS 与访问控制；敏感配置不要入库到公共仓库。

## 10. 参考文档
- `api/docs/ezdata_api_doc.md`：OpenAPI 接口说明。
- `api/docs/RAG_密钥与权限机制说明.md`：JWT 与权限机制。
- `door_access_to_rag_guide.md`：门禁数据入库与 RAG 集成指南。
- `PACKAGING_GUIDE.md`（另文档）：项目打包与迁移步骤。

如需进一步了解各模块实现，可依次阅读 `api/web_apps/rag/`、采集脚本源码，以及 TrustRAG 的 `nong.py` 主逻辑。欢迎补充业务定制文档，确保交接顺畅。***

