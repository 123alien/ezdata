# 知识库-TrustRAG Namespace 绑定功能

## 功能概述

本功能实现了 ezdata 知识库与 TrustRAG 外部服务的 namespace 一对一绑定，使用户可以：

1. **自动映射**: 选择知识库时自动填入对应的 TrustRAG namespace
2. **权限控制**: 基于知识库权限控制绑定操作
3. **无缝集成**: 在提问和SSO token生成时自动使用绑定的namespace

## 数据库表结构

### rag_kb_binding 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键ID |
| kb_id | Integer | 知识库ID (外键) |
| namespace | String(255) | TrustRAG namespace |
| remark | String(500) | 备注说明 |
| create_by | String(36) | 创建者用户ID |
| create_time | DateTime | 创建时间 |
| update_by | String(36) | 更新者用户ID |
| update_time | DateTime | 更新时间 |
| del_flag | SmallInteger | 删除标志 (0: 正常, 1: 已删除) |

## API 接口

### 1. 获取绑定信息

```
GET /api/rag/kb/binding?kid={knowledge_base_id}
```

**权限要求**: 对指定知识库有读取权限

**响应示例**:
```json
{
  "success": true,
  "result": {
    "id": 1,
    "kb_id": 1,
    "namespace": "my-namespace",
    "remark": "测试绑定",
    "create_time": "2024-01-01 12:00:00"
  }
}
```

### 2. 创建/更新绑定

```
POST /api/rag/kb/binding
```

**请求体**:
```json
{
  "kb_id": 1,
  "namespace": "my-namespace",
  "remark": "测试绑定"
}
```

**权限要求**: 对指定知识库有写入权限

**响应示例**:
```json
{
  "success": true,
  "message": "绑定信息创建成功",
  "result": {
    "id": 1,
    "kb_id": 1,
    "namespace": "my-namespace",
    "remark": "测试绑定"
  }
}
```

### 3. 删除绑定

```
DELETE /api/rag/kb/binding/{kb_id}
```

**权限要求**: 对指定知识库有写入权限

**响应示例**:
```json
{
  "success": true,
  "message": "绑定信息删除成功"
}
```

## 前端集成

### 1. 绑定弹窗组件

使用 `BindingModal.vue` 组件来管理绑定：

```vue
<BindingModal
  v-model:open="bindingModalVisible"
  :kb-data="currentBindingKb"
  @success="handleBindingSuccess"
/>
```

### 2. 自动回填功能

在"外部RAG服务"页面，选择知识库时会自动填入绑定的namespace：

```typescript
const onDatasetChange = async (value: string) => {
  // ... 其他逻辑
  
  // 自动获取绑定的namespace
  if (value) {
    const res = await getKnowledgeBaseBinding({ kid: value });
    if (res.success && res.result) {
      namespace.value = res.result.namespace;
    }
  }
};
```

## 使用流程

### 1. 创建绑定

1. 在"我的知识库"页面，点击"绑定索引"按钮
2. 在弹出的绑定弹窗中填写 TrustRAG namespace
3. 可选择添加备注说明
4. 点击"创建"按钮完成绑定

### 2. 使用绑定

1. 在"外部RAG服务"页面选择知识库
2. 系统自动填入绑定的namespace
3. 生成SSO token或提问时会自动使用该namespace

### 3. 管理绑定

- **编辑**: 在绑定弹窗中修改namespace或备注
- **删除**: 在绑定弹窗中点击"删除绑定"按钮

## 权限控制

- **读取权限**: 可以查看绑定信息
- **写入权限**: 可以创建、编辑、删除绑定
- **权限检查**: 基于知识库的分享权限进行控制

## 错误处理

### 常见错误

1. **绑定信息不存在**
   ```
   错误: 知识库 1 未绑定TrustRAG namespace，请先创建绑定
   解决: 在知识库管理页面创建绑定
   ```

2. **权限不足**
   ```
   错误: 无权限修改此知识库
   解决: 联系知识库所有者提升权限
   ```

3. **Namespace冲突**
   ```
   错误: 该namespace已被其他知识库使用
   解决: 使用唯一的namespace名称
   ```

## 开发说明

### 1. 创建数据库表

```bash
cd api
python create_binding_table.py
```

### 2. 测试功能

```bash
cd api
python test_binding.py
```

### 3. 重启服务

修改代码后需要重启后端服务：

```bash
cd api
conda activate ezdata
python web_api.py
```

## 注意事项

1. **唯一性**: 每个namespace只能绑定到一个知识库
2. **权限**: 绑定操作需要相应的知识库权限
3. **清理**: 删除知识库时会自动清理相关绑定
4. **审计**: 所有绑定操作都会记录操作者和时间

## 扩展功能

未来可以考虑添加：

1. **批量绑定**: 支持批量导入namespace映射
2. **同步状态**: 与TrustRAG服务同步namespace状态
3. **历史记录**: 记录绑定的变更历史
4. **自动发现**: 自动发现TrustRAG中的可用namespace
