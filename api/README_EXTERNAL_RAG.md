# TrustRAG 外部集成方案

## 📋 概述

本文档描述了如何将 TrustRAG 服务集成到 EZDATA 系统中，实现无缝的外部 RAG 服务接入。

## 🏗️ 架构设计

### 后端转发网关方案

```
前端 (Vue.js) 
    ↓
EZDATA 后端 (Flask) 
    ↓ (转发)
TrustRAG 服务 (http://localhost:8217)
```

**优势：**
- ✅ 前端无需修改，保持现有API调用方式
- ✅ 统一的错误处理和响应格式
- ✅ 支持认证和权限控制
- ✅ 便于监控和日志记录
- ✅ 可以添加缓存和限流

## 🚀 快速开始

### 1. 启动 TrustRAG 服务

```bash
# 激活虚拟环境
source trustrag/bin/activate

# 启动API服务
python testapi.py
```

### 2. 启动 EZDATA 后端

```bash
cd api
python app.py
```

### 3. 测试连接

```bash
# 测试健康检查
curl http://localhost:8001/api/external/rag/health

# 测试聊天功能
curl -X POST http://localhost:8001/api/external/rag/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "汽车保养需要注意什么？"}'
```

## 📡 API 接口

### 基础接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 健康检查 | GET | `/api/external/rag/health` | 检查TrustRAG服务状态 |
| 初始化 | POST | `/api/external/rag/initialize` | 初始化RAG系统 |
| 状态查询 | GET | `/api/external/rag/status` | 获取服务详细信息 |
| 连接测试 | POST | `/api/external/rag/test` | 测试所有功能 |

### 查询接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 聊天 | POST | `/api/external/rag/chat` | 简化聊天接口 |
| 文本查询 | POST | `/api/external/rag/text` | 纯文本查询 |
| OpenAI兼容 | POST | `/api/external/rag/v1/chat/completions` | OpenAI格式接口 |
| 知识检索 | POST | `/api/external/rag/search` | 知识库检索 |
| 文本检索 | POST | `/api/external/rag/search_text` | 纯文本检索 |

## 💻 使用示例

### Python 客户端

```python
from external_rag_client import TrustRAGClient

# 创建客户端
client = TrustRAGClient("http://localhost:8001")

# 健康检查
health = client.health_check()
print("健康状态:", health)

# 聊天查询
result = client.chat("汽车保养需要注意什么？")
print("查询结果:", result)

# 文本查询
text = client.text_query("如何更换机油？")
print("文本结果:", text)

# 知识检索
search = client.search("轮胎保养", top_k=3)
print("检索结果:", search)
```

### JavaScript 客户端

```javascript
// 基础配置
const BASE_URL = 'http://localhost:8001/api/external/rag';

// 健康检查
async function checkHealth() {
    const response = await fetch(`${BASE_URL}/health`);
    return await response.json();
}

// 聊天查询
async function chat(message) {
    const response = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });
    return await response.json();
}

// 文本查询
async function textQuery(query) {
    const response = await fetch(`${BASE_URL}/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });
    return await response.text();
}

// 使用示例
async function main() {
    // 检查状态
    const health = await checkHealth();
    console.log('健康状态:', health);
    
    // 发送查询
    const result = await chat('汽车保养需要注意什么？');
    console.log('查询结果:', result);
}
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8001/api/external/rag/health

# 聊天查询
curl -X POST http://localhost:8001/api/external/rag/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "汽车保养需要注意什么？"}'

# 文本查询
curl -X POST http://localhost:8001/api/external/rag/text \
     -H "Content-Type: application/json" \
     -d '{"query": "如何更换机油？"}'

# 知识检索
curl -X POST http://localhost:8001/api/external/rag/search \
     -H "Content-Type: application/json" \
     -d '{"query": "轮胎保养", "top_k": 3}'

# 连接测试
curl -X POST http://localhost:8001/api/external/rag/test
```

## 🔧 配置说明

### TrustRAG 服务配置

在 `api/web_apps/rag/views/external_api_views.py` 中：

```python
# TrustRAG服务配置
TRUSTRAG_BASE_URL = "http://localhost:8217"
TRUSTRAG_TIMEOUT = 30  # 30秒超时
```

### 环境变量配置

可以在 `api/dev.env` 中添加：

```bash
# TrustRAG 服务配置
TRUSTRAG_BASE_URL=http://localhost:8217
TRUSTRAG_TIMEOUT=30
```

## 🔍 监控和调试

### 日志查看

```bash
# 查看后端日志
tail -f api/logs/app.log

# 查看TrustRAG日志
tail -f trustrag.log
```

### 状态监控

```bash
# 检查服务状态
curl http://localhost:8001/api/external/rag/status

# 测试连接
curl -X POST http://localhost:8001/api/external/rag/test
```

### 性能监控

- **响应时间**: 通常 2-5 秒
- **并发能力**: 建议 10-20 请求/秒
- **超时设置**: 30 秒

## ⚠️ 注意事项

### 1. 服务依赖

- TrustRAG 服务必须正常运行在 `http://localhost:8217`
- 确保 TrustRAG 服务已正确初始化
- 检查网络连接和防火墙设置

### 2. 错误处理

- 网络超时：30秒自动超时
- 连接失败：返回详细错误信息
- 服务异常：自动重试机制

### 3. 安全考虑

- 当前版本无认证机制
- 生产环境建议添加 API 密钥
- 考虑添加请求限流

### 4. 性能优化

- 可以添加响应缓存
- 考虑连接池优化
- 监控内存和CPU使用

## 🐛 故障排除

### 常见问题

**1. 连接失败**
```bash
# 检查TrustRAG服务状态
curl http://localhost:8217/health

# 检查端口占用
netstat -tulpn | grep 8217
```

**2. 超时错误**
```bash
# 增加超时时间
# 修改 TRUSTRAG_TIMEOUT 值

# 检查网络延迟
ping localhost
```

**3. 响应格式错误**
```bash
# 检查TrustRAG响应格式
curl -X POST http://localhost:8217/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "test"}'
```

**4. 初始化失败**
```bash
# 手动初始化TrustRAG
curl -X POST http://localhost:8217/initialize

# 检查模型文件
ls -la autodl-tmp/Qwen/Qwen2.5-7B-Instruct/
```

## 📈 扩展功能

### 1. 缓存机制

可以添加 Redis 缓存来提高响应速度：

```python
# 缓存配置
CACHE_ENABLED = True
CACHE_TTL = 3600  # 1小时
```

### 2. 限流控制

添加请求限流保护：

```python
# 限流配置
RATE_LIMIT = "100/hour"  # 每小时100次
```

### 3. 负载均衡

支持多个 TrustRAG 实例：

```python
# 负载均衡配置
TRUSTRAG_INSTANCES = [
    "http://localhost:8217",
    "http://localhost:8218",
    "http://localhost:8219"
]
```

### 4. 监控告警

集成监控系统：

```python
# 监控配置
METRICS_ENABLED = True
ALERT_THRESHOLD = 5.0  # 5秒响应时间告警
```

## 📞 技术支持

### 联系方式

- **项目地址**: EZDATA + TrustRAG
- **文档版本**: 1.0.0
- **集成方案**: 后端转发网关

### 更新日志

**v1.0.0** (2024-08-30)
- 初始版本发布
- 支持所有 TrustRAG 接口
- 提供完整的客户端示例
- 实现后端转发网关方案

---

*最后更新时间: 2024-08-30*
