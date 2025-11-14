# EzData API 接口文档

## 项目概述

EzData 是一个数据平台，提供数据源管理、数据模型、ETL、知识库（RAG）、LLM 集成、设备监控等功能。

**基础URL**: `http://localhost:8001`

**认证方式**: JWT Token（在请求头中携带 `X-Access-Token`）

---

## 目录

1. [认证接口](#认证接口)
2. [数据模型接口](#数据模型接口)
3. [RAG 知识库接口](#rag-知识库接口)
4. [设备监控接口](#设备监控接口)
5. [系统管理接口](#系统管理接口)
6. [通用响应格式](#通用响应格式)

---

## 认证接口

### 1. 用户登录
- **接口**: `POST /api/sys/user/login`
- **描述**: 用户登录，获取访问令牌
- **请求参数**:
  ```json
  {
    "username": "admin",
    "password": "123456"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "message": "操作成功",
    "result": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "userInfo": {
        "id": 1,
        "username": "admin",
        "realname": "管理员"
      }
    }
  }
  ```

### 2. 获取用户信息
- **接口**: `GET /api/sys/user/getUserInfo`
- **描述**: 获取当前登录用户信息
- **请求头**: `X-Access-Token: <token>`
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "id": 1,
      "username": "admin",
      "realname": "管理员",
      "avatar": ""
    }
  }
  ```

---

## 数据模型接口

### 1. 查询数据模型列表
- **接口**: `GET /api/datamodel/list`
- **描述**: 获取数据模型列表
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  - `page`: 页码（默认1）
  - `pagesize`: 每页条数（默认10）
  - `name`: 模型名称（可选，模糊匹配）
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "records": [
        {
          "id": "uuid",
          "name": "环境监测数据",
          "code": "env_monitoring",
          "description": "环境监测设备数据",
          "model_type": "mongodb"
        }
      ],
      "total": 10
    }
  }
  ```

### 2. 查询数据模型数据
- **接口**: `POST /api/datamodel/query`
- **描述**: 查询指定数据模型的数据
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  ```json
  {
    "id": "数据模型ID",
    "page": 1,
    "pagesize": 100,
    "filters": {
      "field_name": "value"
    }
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "records": [...],
      "total": 100,
      "fields": [...]
    }
  }
  ```

### 3. 获取设备指标数据
- **接口**: `POST /api/datamodel/dashboard/device-metrics`
- **描述**: 获取设备的实时指标数据
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  ```json
  {
    "deviceName": "XZD20250734",
    "start": 1698768000000,
    "end": 1698854400000
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "deviceName": "XZD20250734",
      "series": {
        "power": [
          {"t": 1698768000000, "v": 100.5}
        ]
      },
      "units": {
        "power": "kW"
      }
    }
  }
  ```

### 4. 设备指标预测
- **接口**: `POST /api/datamodel/dashboard/device-prediction`
- **描述**: 对设备指标进行LSTM预测
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  ```json
  {
    "deviceName": "XZD20250734",
    "metric": "power",
    "start": 1698768000000,
    "end": 1698854400000,
    "predictionSteps": 36
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "deviceName": "XZD20250734",
      "predictions": {
        "power": {
          "predictions": [100.5, 101.2, ...],
          "trend": 0.15,
          "confidence": 0.85,
          "method": "lstm"
        }
      }
    }
  }
  ```

---

## RAG 知识库接口

### 1. 知识库列表
- **接口**: `GET /api/rag/kb/list`
- **描述**: 获取知识库列表
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  - `page`: 页码
  - `pagesize`: 每页条数
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "records": [
        {
          "id": "uuid",
          "name": "电表知识库",
          "description": "电表相关文档和数据",
          "owner_id": "admin"
        }
      ],
      "total": 5
    }
  }
  ```

### 2. 文档列表
- **接口**: `GET /api/rag/document/list`
- **描述**: 获取指定知识库的文档列表
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  - `dataset_id`: 知识库ID
  - `page`: 页码
  - `pagesize`: 每页条数
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "records": [
        {
          "id": "uuid",
          "name": "电表数据-2025-11-02",
          "dataset_id": "kb_uuid",
          "status": 3,
          "create_time": "2025-11-02 14:49:46"
        }
      ],
      "total": 10
    }
  }
  ```

### 3. 上传文档
- **接口**: `POST /api/rag/document/add`
- **描述**: 上传文档到知识库
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  ```json
  {
    "dataset_id": "知识库ID",
    "name": "文档名称",
    "document_type": "upload_file",
    "meta_data": {
      "upload_file": "/path/to/file.pdf"
    }
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "message": "添加成功"
  }
  ```

### 4. 批量同步到 TrustRAG
- **接口**: `POST /api/rag/document/sync/bulk`
- **描述**: 将知识库的所有文档批量同步到 TrustRAG
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  ```json
  {
    "dataset_id": "知识库ID"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "total": 5,
      "success_count": 5,
      "namespace": "dian",
      "results": [...]
    }
  }
  ```

### 5. 生成 SSO Token
- **接口**: `POST /api/rag/external/sso_token`
- **描述**: 生成用于访问 TrustRAG 的 SSO Token
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  ```json
  {
    "dataset_id": "知识库ID"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "token": "eyJhbGciOiJIUzI1NiIs...",
      "expires_in": 600,
      "permission_level": "read",
      "namespace": "dian"
    }
  }
  ```

### 6. RAG 聊天接口
- **接口**: `POST /api/rag/external/chat`
- **描述**: 与 RAG 系统进行对话
- **请求头**: `X-Access-Token: <token>`
- **请求参数**:
  ```json
  {
    "query": "01室今天的用电量是多少？",
    "dataset_id": "知识库ID",
    "mode": "auto"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "code": 200,
    "result": {
      "reply": "01室今天的用电量是20.00 kWh",
      "sources": ["电表数据-2025-11-02"]
    }
  }
  ```

---

## 设备监控接口

### 1. 获取设备列表
- **接口**: `GET /api/datamodel/list`
- **描述**: 获取所有设备数据模型
- **请求头**: `X-Access-Token: <token>`

### 2. 获取设备实时数据
- **接口**: `POST /api/datamodel/query`
- **描述**: 查询设备实时数据
- **请求参数**: 参见"数据模型接口 - 查询数据模型数据"

### 3. 设备告警策略
- **接口**: `GET /api/alert_strategy/list`
- **描述**: 获取设备告警策略列表
- **请求头**: `X-Access-Token: <token>`

---

## 系统管理接口

### 1. 数据字典
- **接口**: `GET /api/sys/dict/list`
- **描述**: 获取数据字典列表

### 2. 系统日志
- **接口**: `GET /api/system/log/query`
- **描述**: 查询系统日志

### 3. 文件上传
- **接口**: `POST /api/sys/oss/file/upload`
- **描述**: 上传文件到对象存储

---

## 通用响应格式

所有接口返回统一的 JSON 格式：

### 成功响应
```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "result": {
    // 具体数据
  },
  "timestamp": 1698768000000
}
```

### 错误响应
```json
{
  "success": false,
  "code": 400,
  "message": "参数错误",
  "result": null,
  "timestamp": 1698768000000
}
```

### 常见状态码
- `200`: 成功
- `400`: 参数错误
- `401`: 未授权（未登录或token过期）
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 认证说明

### Token 获取
1. 调用登录接口获取 token
2. 在后续请求中携带 token

### Token 使用
在请求头中添加：
```
X-Access-Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token 过期
- Token 默认有效期为 7 天
- 过期后需要重新登录

---

## 完整 API 清单

### 系统管理 (/api/sys)
- `POST /api/sys/user/login` - 用户登录
- `POST /api/sys/user/logout` - 用户登出
- `GET /api/sys/user/getUserInfo` - 获取用户信息
- `GET /api/sys/user/list` - 用户列表
- `POST /api/sys/user/add` - 添加用户
- `POST /api/sys/user/edit` - 编辑用户
- `POST /api/sys/user/delete` - 删除用户
- `GET /api/sys/permission/list` - 权限列表
- `GET /api/sys/role/list` - 角色列表
- `GET /api/sys/sysDepart/list` - 部门列表
- `GET /api/sys/dict/list` - 数据字典列表
- `POST /api/sys/oss/file/upload` - 文件上传

### 数据源管理 (/api/datasource)
- `GET /api/datasource/list` - 数据源列表
- `POST /api/datasource/add` - 添加数据源
- `POST /api/datasource/edit` - 编辑数据源
- `POST /api/datasource/delete` - 删除数据源
- `POST /api/datasource/test` - 测试数据源连接

### 数据模型 (/api/datamodel)
- `GET /api/datamodel/list` - 数据模型列表
- `GET /api/datamodel/tree` - 数据模型树
- `POST /api/datamodel/add` - 添加数据模型
- `POST /api/datamodel/edit` - 编辑数据模型
- `POST /api/datamodel/delete` - 删除数据模型
- `POST /api/datamodel/query` - 查询模型数据
- `POST /api/datamodel/dashboard/device-metrics` - 获取设备指标数据
- `POST /api/datamodel/dashboard/device-prediction` - 设备指标预测

### 数据接口 (/api/data_interface)
- `GET /api/data_interface/query` - 数据接口查询（支持 api_key 认证）
- `GET /api/data_interface/list` - 数据接口列表

### RAG 知识库 (/api/rag)
- `GET /api/rag/kb/list` - 知识库列表
- `POST /api/rag/kb/add` - 添加知识库
- `POST /api/rag/kb/edit` - 编辑知识库
- `POST /api/rag/kb/delete` - 删除知识库
- `GET /api/rag/dataset/list` - 数据集列表
- `GET /api/rag/document/list` - 文档列表
- `POST /api/rag/document/add` - 添加文档
- `POST /api/rag/document/edit` - 编辑文档
- `POST /api/rag/document/delete` - 删除文档
- `POST /api/rag/document/train` - 训练文档
- `POST /api/rag/document/sync/bulk` - 批量同步到 TrustRAG
- `GET /api/rag/chunk/list` - 文档片段列表
- `GET /api/rag/kb/binding/list` - 知识库绑定列表
- `POST /api/rag/kb/binding/add` - 添加知识库绑定

### RAG 外部接口 (/api/rag/external)
- `POST /api/rag/external/sso_token` - 生成 SSO Token
- `POST /api/rag/external/chat` - RAG 聊天
- `POST /api/rag/external/search` - RAG 检索
- `GET /api/rag/external/health` - TrustRAG 健康检查
- `POST /api/rag/external/test` - TrustRAG 功能测试

### 任务调度 (/api/task)
- `GET /api/task/list` - 任务列表
- `POST /api/task/add` - 添加任务
- `POST /api/task/edit` - 编辑任务
- `POST /api/task/delete` - 删除任务
- `POST /api/task/execute` - 执行任务

### 调度器 (/api/scheduler)
- `GET /api/scheduler/job/list` - 定时任务列表
- `POST /api/scheduler/job/add` - 添加定时任务
- `POST /api/scheduler/job/pause` - 暂停定时任务
- `POST /api/scheduler/job/resume` - 恢复定时任务

### LLM 集成 (/api/llm)
- `POST /api/llm/chat` - LLM 对话
- `GET /api/llm/chat_app/list` - 聊天应用列表
- `POST /api/llm/chat_app/add` - 添加聊天应用

### 告警管理 (/api/alert)
- `GET /api/alert/list` - 告警记录列表
- `GET /api/alert_strategy/list` - 告警策略列表
- `POST /api/alert_strategy/add` - 添加告警策略
- `POST /api/alert_strategy/edit` - 编辑告警策略

---

## 核心数据模型

### 用户 (User)
```json
{
  "id": 1,
  "username": "admin",
  "realname": "管理员",
  "password": "加密后的密码",
  "avatar": "头像URL",
  "status": 1,
  "create_time": "2025-10-01 00:00:00"
}
```

### 数据模型 (DataModel)
```json
{
  "id": "uuid",
  "name": "环境监测数据",
  "code": "env_monitoring",
  "model_type": "mongodb",
  "datasource_id": "数据源ID",
  "table_name": "env_device_factor_snapshot",
  "description": "环境监测设备数据"
}
```

### 知识库 (KnowledgeBase)
```json
{
  "id": "uuid",
  "name": "电表知识库",
  "description": "电表相关文档和数据",
  "owner_id": "admin",
  "create_time": "2025-10-27 07:21:27"
}
```

### 文档 (Document)
```json
{
  "id": "uuid",
  "dataset_id": "知识库ID",
  "name": "电表数据-2025-11-02",
  "document_type": "upload_file",
  "status": 3,
  "meta_data": {
    "upload_file": "/tmp/file.txt",
    "data_count": 327
  }
}
```

### 知识库绑定 (KnowledgeBaseBinding)
```json
{
  "id": "uuid",
  "kb_id": "知识库ID",
  "namespace": "dian",
  "description": "绑定到TrustRAG的dian命名空间"
}
```

---

## 使用示例

### 示例1：登录并查询设备数据
```bash
# 1. 登录
curl -X POST http://localhost:8001/api/sys/user/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'

# 2. 使用返回的token查询设备数据
curl -X POST http://localhost:8001/api/datamodel/query \
  -H "Content-Type: application/json" \
  -H "X-Access-Token: <your_token>" \
  -d '{"id":"datamodel_id","page":1,"pagesize":100}'
```

### 示例2：使用 RAG 查询电表数据
```bash
# 1. 生成 SSO Token
curl -X POST http://localhost:8001/api/rag/external/sso_token \
  -H "Content-Type: application/json" \
  -H "X-Access-Token: <your_token>" \
  -d '{"dataset_id":"kb_id"}'

# 2. 使用 RAG 聊天
curl -X POST http://localhost:8001/api/rag/external/chat \
  -H "Content-Type: application/json" \
  -H "X-Access-Token: <your_token>" \
  -d '{"query":"01室今天的用电量是多少？","dataset_id":"kb_id"}'
```

---

## 附录

### API 模块说明

| 模块 | URL前缀 | 描述 |
|------|---------|------|
| 系统管理 | `/api/sys` | 用户、角色、权限管理 |
| 数据源 | `/api/datasource` | 数据源连接管理 |
| 数据模型 | `/api/datamodel` | 数据模型定义和查询 |
| 数据接口 | `/api/data_interface` | 对外数据接口 |
| RAG知识库 | `/api/rag` | 知识库和文档管理 |
| RAG外部 | `/api/rag/external` | TrustRAG集成接口 |
| 任务 | `/api/task` | 任务管理 |
| 调度器 | `/api/scheduler` | 定时任务调度 |
| LLM | `/api/llm` | LLM对话和应用 |
| 告警 | `/api/alert` | 设备告警管理 |
| 大屏 | `/api/screen` | 数据大屏配置 |
| 代码生成 | `/api/code_generator` | 代码生成器 |

### 数据模型类型
- `mysql`: MySQL数据库表
- `mongodb`: MongoDB集合
- `api`: 外部API接口
- `file`: 文件数据源

### 文档状态
- `1`: 待训练
- `2`: 训练中
- `3`: 训练成功
- `4`: 训练失败

---

**生成时间**: 2025-11-02
**版本**: 1.0.0

