# RAG系统密钥与权限机制详解

## 一、概述

RAG系统采用了**JWT (JSON Web Token)** 作为身份验证和授权机制，通过SSO Token实现与TrustRAG服务的通信。

## 二、密钥系统
应该
### 2.1 密钥配置

#### ezdata后端密钥
- **位置**: `api/config.py` 或环境变量
- **变量名**: `SECRET_KEY`
- **默认值**: `'ezdata-secret-key'` (开发环境)
- **用途**: 用于生成和验证JWT Token

#### TrustRAG服务密钥
- **位置**: `TrustRAG-main/test.py`
- **变量名**: `JWT_SECRET`
- **环境变量**: `EZDATA_SECRET_KEY`
- **默认值**: `'erwqefdscweer)qi'` (需要与ezdata后端一致)
- **用途**: 验证来自ezdata的JWT Token

⚠️ **重要**: 两个服务的密钥必须**完全一致**，否则Token验证会失败！

### 2.2 密钥安全建议

```python
# 生产环境应使用环境变量
import os
SECRET_KEY = os.getenv('EZDATA_SECRET_KEY', 'fallback-key')

# 或者从配置文件读取
# 确保密钥足够复杂（至少32字符）
```

---

## 三、Token生成机制

### 3.1 JWT Token结构

```python
payload = {
    'user_id': '用户ID',           # 用户标识
    'tenant_id': 1,                # 租户ID（多租户隔离）
    'dataset_id': '知识库ID',       # 可选：关联的知识库ID
    'namespace': 'namespace名称',   # TrustRAG命名空间
    'permission_level': 'read',    # 权限级别：read/write/admin
    'exp': '过期时间戳',            # 10分钟后过期
    'iat': '签发时间戳'            # 当前时间
}
```

### 3.2 Token生成位置

#### 1. Web界面访问（`external_api_views.py`）

```python
def _build_auth_headers(dataset_id=None, namespace=None):
    """生成短期SSO Token（10分钟有效期）"""
    user_info = get_auth_token_info()  # 从当前登录session获取
    user_id = user_info.get('user_id')
    tenant_id = user_info.get('tenant_id', 0)
    
    payload = {
        'user_id': user_id,
        'tenant_id': tenant_id,
        'dataset_id': dataset_id,
        'namespace': namespace,
        'permission_level': 'read',  # Web访问默认只读
        'exp': datetime.utcnow() + timedelta(minutes=10),
        'iat': datetime.utcnow(),
    }
    
    secret_key = current_app.config.get('SECRET_KEY', 'ezdata-secret-key')
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}
```

#### 2. 后台同步（`trustrag_sync_service.py`）

```python
def _generate_sso_token(user_id, tenant_id, dataset_id, namespace):
    """生成同步用的SSO Token（写入权限）"""
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "dataset_id": dataset_id,
        "namespace": namespace,
        "permission_level": "write",  # 同步需要写入权限
        "exp": datetime.utcnow() + timedelta(minutes=10),
        "iat": datetime.utcnow(),
    }
    secret_key = current_app.config.get("SECRET_KEY", "ezdata-secret-key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token
```

#### 3. API接口生成（`external_api_views.py`）

```python
@external_rag_bp.route('/sso_token', methods=['POST'])
def generate_sso_token():
    """生成SSO Token接口"""
    # 1. 获取用户信息（必须登录）
    user_info = get_auth_token_info()
    
    # 2. 权限检查
    if not kb_service.has_permission(dataset_id, user_id, 'read'):
        return "权限不足"
    
    # 3. 生成Token
    token_payload = {
        'user_id': user_id,
        'tenant_id': tenant_id,
        'dataset_id': dataset_id,
        'namespace': namespace,  # 自动从绑定表获取
        'permission_level': 'read',
        'exp': datetime.utcnow() + timedelta(minutes=10),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')
    return {'token': token, 'expires_in': 600}
```

---

## 四、Token验证机制

### 4.1 TrustRAG端验证（`test.py`）

```python
def verify_sso(authorization: str) -> dict:
    """验证SSO Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        # 使用相同的密钥验证
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # 检查过期时间
        if payload.get("exp", 0) < int(time.time()):
            raise HTTPException(status_code=401, detail="token expired")
        
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}")
```

### 4.2 Namespace提取

```python
def pick_namespace(body: Optional[dict], payload: dict) -> str:
    """从请求体或Token中提取namespace"""
    # 优先级：请求体 > Token payload
    ns = (body or {}).get("namespace") or payload.get("namespace")
    if not ns:
        raise HTTPException(status_code=400, detail="namespace required")
    return ns
```

---

## 五、权限系统

### 5.1 权限级别

RAG系统定义了三种权限级别：

| 权限级别 | 数值 | 说明 |
|---------|------|------|
| `read` | 1 | 只读权限：可以查询、检索 |
| `write` | 2 | 写入权限：可以上传文档、同步数据 |
| `admin` | 3 | 管理员权限：可以删除、修改配置 |

### 5.2 权限判定逻辑（`kb_service.py`）

```python
def has_permission(kb_id: str, user_id: str, need_level: str = 'read') -> bool:
    """校验用户在知识库上的权限"""
    
    # 1. 所有者检查
    if username and kb.owner_id == username:
        return True  # 所有者拥有所有权限
    
    # 2. 分享权限检查
    level_map = {'read': 1, 'write': 2, 'admin': 3}
    required = level_map.get(need_level, 1)
    
    share = db.session.query(KnowledgeBaseShare).filter(
        KnowledgeBaseShare.kb_id == kb.id,
        KnowledgeBaseShare.shared_with_id == str(user_id),
        KnowledgeBaseShare.status == 1,  # 生效中
        KnowledgeBaseShare.del_flag == 0  # 未删除
    ).first()
    
    if not share:
        return False  # 未分享，无权限
    
    current = level_map.get(share.permission_level or 'read', 1)
    return current >= required  # 当前权限 >= 所需权限
```

### 5.3 Token中的权限使用

```python
# Token中携带permission_level
payload = {
    'permission_level': 'read',  # 或 'write' / 'admin'
    # ... 其他字段
}

# TrustRAG可以根据permission_level限制操作
# 例如：只有write权限才能调用/ingest接口
if payload.get('permission_level') != 'write':
    raise HTTPException(status_code=403, detail="insufficient permission")
```

---

## 六、Namespace机制

### 6.1 Namespace作用

- **数据隔离**: 每个namespace有独立的向量索引和文档存储
- **权限隔离**: 不同namespace可以有不同的访问控制
- **多租户支持**: 通过tenant_id + namespace实现多租户隔离

### 6.2 Namespace绑定（`rag_kb_binding`表）

```sql
-- 知识库与namespace一对一绑定
CREATE TABLE rag_kb_binding (
    id INT PRIMARY KEY,
    kb_id VARCHAR(36),      -- 知识库ID
    namespace VARCHAR(255), -- TrustRAG命名空间
    del_flag TINYINT,       -- 删除标志
    ...
);
```

### 6.3 自动解析Namespace

```python
def _resolve_namespace_by_dataset(dataset_id: str) -> Optional[str]:
    """根据知识库ID自动解析namespace"""
    sql = """
        SELECT namespace 
        FROM rag_kb_binding 
        WHERE kb_id = :dataset_id AND del_flag = 0
    """
    result = db.session.execute(sql, {"dataset_id": dataset_id}).first()
    return result.namespace if result else None
```

---

## 七、完整流程示例

### 7.1 用户查询流程

```
1. 用户登录ezdata系统
   ↓
2. 前端调用 /api/rag/external/sso_token
   - 自动获取当前登录用户信息
   - 根据dataset_id查询绑定的namespace
   - 检查用户权限（has_permission）
   - 生成JWT Token（10分钟有效期）
   ↓
3. 前端使用Token访问TrustRAG
   GET /chat?message=xxx
   Headers: Authorization: Bearer <token>
   ↓
4. TrustRAG验证Token
   - 验证签名（使用JWT_SECRET）
   - 检查过期时间
   - 提取namespace和permission_level
   ↓
5. 根据namespace加载对应的RAG实例
   - 每个namespace有独立的索引路径
   - indexs/{namespace}/dense_cache
   ↓
6. 执行检索和生成
   - 使用对应的向量索引
   - 返回结果
```

### 7.2 文档同步流程

```
1. 用户在ezdata上传文档
   ↓
2. 后台调用sync_created_document
   - 解析namespace（从绑定表）
   - 生成write权限的Token
   ↓
3. 调用TrustRAG /ingest接口
   POST /ingest
   Headers: Authorization: Bearer <write_token>
   Body: {
       "namespace": "dian",
       "raw_text": "...",
       "source": "文档名"
   }
   ↓
4. TrustRAG验证Token
   - 检查permission_level是否为write
   - 验证namespace
   ↓
5. 索引更新
   - 将文档分块
   - 更新对应namespace的向量索引
```

---

## 八、安全建议

### 8.1 密钥管理

1. **生产环境**: 使用环境变量或密钥管理服务
2. **定期轮换**: 定期更换密钥，同时更新两个服务
3. **最小权限**: Token中只包含必要的权限级别

### 8.2 Token安全

1. **短期有效**: Token有效期设置为10分钟（当前配置）
2. **HTTPS传输**: 生产环境必须使用HTTPS
3. **过期检查**: 严格检查exp字段，防止过期Token使用

### 8.3 权限控制

1. **默认最小权限**: Web访问默认使用read权限
2. **写入权限分离**: 同步操作使用独立的write Token
3. **权限验证**: 在Token验证时同时检查权限级别

---

## 九、常见问题

### Q1: Token验证失败

**原因**:
- 密钥不一致（ezdata和TrustRAG的密钥不同）
- Token过期（10分钟有效期）
- Token格式错误

**解决**:
```python
# 检查两个服务的密钥是否一致
# ezdata: config.get('SECRET_KEY')
# TrustRAG: JWT_SECRET
```

### Q2: 权限不足

**原因**:
- Token中permission_level低于所需权限
- 用户未分享知识库权限

**解决**:
```python
# 检查知识库分享记录
SELECT * FROM rag_kb_share 
WHERE kb_id = ? AND shared_with_id = ? AND status = 1
```

### Q3: Namespace未找到

**原因**:
- 知识库未绑定namespace
- 绑定记录被删除（del_flag=1）

**解决**:
```python
# 检查绑定记录
SELECT * FROM rag_kb_binding 
WHERE kb_id = ? AND del_flag = 0
```

---

## 十、总结

RAG系统的密钥和权限机制核心要点：

1. **密钥一致性**: ezdata和TrustRAG必须使用相同的JWT密钥
2. **Token有效期**: 短期有效（10分钟），提高安全性
3. **权限分级**: read/write/admin三级权限，细粒度控制
4. **Namespace隔离**: 每个知识库对应一个namespace，数据完全隔离
5. **自动绑定**: 系统自动从绑定表解析namespace，简化使用

通过这套机制，实现了安全、灵活、可扩展的RAG服务访问控制。

