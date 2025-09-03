# 知识库绑定功能测试指南

## 🚀 当前状态

✅ **后端服务**: 正常运行在 `http://localhost:8001`
✅ **前端服务**: 正常运行在 `http://localhost:5177`
✅ **数据库表**: `rag_kb_binding` 表已创建
✅ **API接口**: 绑定相关接口已注册并可访问

## 🧪 测试步骤

### 1. 启动服务

#### 后端服务
```bash
cd /home/dfi/Desktop/ezdata-master/api
conda activate ezdata
python web_api.py
```

#### 前端服务
```bash
cd /home/dfi/Desktop/ezdata-master/web
npm run dev
```

### 2. 验证服务状态

#### 检查后端
```bash
curl http://localhost:8001/api/rag/kb/binding?kid=1
# 预期返回: {"code": 403, "msg": "用户验证失败"}
```

#### 检查前端
```bash
curl http://localhost:5177
# 预期返回: HTML页面内容
```

### 3. 前端功能测试

#### 访问知识库管理页面
1. 打开浏览器访问: `http://localhost:5177`
2. 登录系统（需要有效的用户账号）
3. 导航到: `RAG管理` → `知识库管理` → `我的知识库`

#### 测试绑定功能
1. 在知识库列表中点击"绑定索引"按钮
2. 在弹出的绑定弹窗中填写:
   - **TrustRAG Namespace**: 输入一个唯一的namespace（如：`my-test-namespace`）
   - **备注说明**: 输入描述信息（可选）
3. 点击"创建"按钮
4. 验证是否成功创建绑定

#### 测试自动回填功能
1. 导航到: `RAG管理` → `外部RAG服务`
2. 在"选择知识库"下拉框中选择已绑定的知识库
3. 验证"TrustRAG Namespace"输入框是否自动填入绑定的namespace

### 4. API接口测试

#### 使用测试脚本
```bash
cd /home/dfi/Desktop/ezdata-master/api
python test_binding_simple.py
```

#### 手动测试（需要认证token）
```bash
# 获取绑定信息
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8001/api/rag/kb/binding?kid=1"

# 创建绑定
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"kb_id": 1, "namespace": "test-namespace", "remark": "测试"}' \
     "http://localhost:8001/api/rag/kb/binding"

# 删除绑定
curl -X DELETE -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8001/api/rag/kb/binding/1"
```

## 🔍 故障排除

### 常见问题

#### 1. 前端编译错误
**错误**: `v-model cannot be used on a prop`
**解决**: 已修复，使用 `:open="open"` 替代 `v-model:open="open"`

#### 2. 后端导入错误
**错误**: `ModuleNotFoundError: No module named 'web_apps.utils'`
**解决**: 已修复，使用正确的导入路径 `utils.auth` 和 `utils.common_utils`

#### 3. 数据库表创建失败
**错误**: `Working outside of application context`
**解决**: 已修复，在Flask应用上下文中创建表

#### 4. 前端代理错误
**错误**: `ECONNREFUSED 127.0.0.1:8001`
**解决**: 确保后端服务在8001端口正常运行

### 调试技巧

#### 检查后端日志
```bash
cd /home/dfi/Desktop/ezdata-master/api
tail -f logs/app.log
```

#### 检查前端控制台
1. 打开浏览器开发者工具
2. 查看Console标签页的错误信息
3. 查看Network标签页的API请求状态

#### 检查数据库
```bash
cd /home/dfi/Desktop/ezdata-master/api
conda activate ezdata
python -c "
from web_apps import app, db
from web_apps.rag.kb_models import KnowledgeBaseBinding
with app.app_context():
    bindings = db.session.query(KnowledgeBaseBinding).all()
    print(f'找到 {len(bindings)} 个绑定')
    for b in bindings:
        print(f'ID: {b.id}, KB: {b.kb_id}, Namespace: {b.namespace}')
"
```

## 📋 测试检查清单

- [ ] 后端服务启动成功
- [ ] 前端服务启动成功
- [ ] 数据库表创建成功
- [ ] API接口可访问（返回认证错误是正常的）
- [ ] 前端页面可访问
- [ ] 绑定弹窗组件正常显示
- [ ] 创建绑定功能正常
- [ ] 自动回填功能正常
- [ ] 权限控制正常

## 🎯 下一步

1. **用户认证**: 实现完整的用户登录和token管理
2. **权限测试**: 测试不同用户角色的权限控制
3. **集成测试**: 测试与TrustRAG服务的完整集成
4. **性能测试**: 测试大量数据下的性能表现
5. **错误处理**: 测试各种异常情况的处理

## 📞 技术支持

如果遇到问题，请：
1. 检查服务状态
2. 查看错误日志
3. 确认配置正确
4. 联系开发团队
