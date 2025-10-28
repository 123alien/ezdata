# 门禁数据接入RAG知识库指南

## 概述
将MongoDB中的门禁通行记录导出为Excel文件，然后上传到RAG知识库，使AI助手能够查询门禁数据。

## 前提条件
1. MongoDB中有门禁数据（`door_access_logs` 集合）
2. 已创建RAG知识库（可选：创建独立namespace）
3. 后端已支持Excel文件解析

## 步骤

### 1. 导出数据

**方法：通过数据查询界面导出**

1. 打开"数据中心 > 数据查询"
2. 选择"门禁数据"数据模型
3. 点击"查询"加载数据
4. 调整分页大小（建议设置为1000+以导出更多数据）
5. 点击工具栏的"导出数据"按钮
6. 下载生成的Excel文件

**说明**：界面导出会包含当前查询到的所有数据，适合小批量导出。

### 2. 上传到知识库
1. 进入"RAG > 我的知识库"
2. 选择或创建目标知识库
3. 点击"文档管理" → "上传文档"
4. 选择刚导出的Excel文件（`.xlsx`）
5. 等待上传完成

### 3. 同步到TrustRAG（可选）
1. 点击"一键同步到TrustRAG"
2. 确保已创建namespace绑定
3. 等待同步完成

### 4. 验证查询
在NextChat或AI助手中测试：
- "昨天有哪些门禁通行记录？"
- "查询张三的通行记录"
- "最近一小时有多少人次通过门禁？"

## 数据格式说明

### Excel列结构
| 列名 | 说明 | 示例 |
|------|------|------|
| 姓名 | 通行人员姓名 | 张三 |
| 姓名ID | 人员ID | 12345 |
| 门禁名称 | 门禁设备名称 | 大门 |
| 门禁ID | 门禁设备ID | door_001 |
| 访问时间 | 通行时间 | 2024-10-28 14:30:00 |
| 备注 | 备注信息 | 正常通行 |

### MongoDB数据结构
```json
{
  "member_xm": "张三",
  "member_id": "12345",
  "door_name": "大门",
  "door_id": "door_001",
  "visit_time": ISODate("2024-10-28T14:30:00Z"),
  "remark": "正常通行",
  "created_at": ISODate("2024-10-28T14:30:05Z")
}
```

## 注意事项
1. Excel文件大小建议不超过5MB（约5000条记录）
2. 定期更新：建议每天或每周导出一次最新数据
3. 隐私保护：敏感信息请先脱敏
4. TrustRAG索引：首次同步后需要等待索引构建完成

## 高级用法

### 自动化导出脚本
可以创建定时任务，自动导出最新数据：

```bash
# 添加到crontab
0 1 * * * cd /path/to/ezdata && python export_door_to_excel.py
```

### 数据范围筛选
导出特定时间范围的数据：

```python
# 最近7天
from datetime import datetime, timedelta
end_time = datetime.now()
start_time = end_time - timedelta(days=7)

records = collection.find({
    'visit_time': {
        '$gte': start_time,
        '$lte': end_time
    }
}).sort('visit_time', -1).limit(5000)
```

