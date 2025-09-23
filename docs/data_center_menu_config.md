# 数据中心菜单配置说明

## 菜单结构

```
数据中心 (主菜单)
├── 环境监测设备 (子菜单)
└── 电表设备 (子菜单)
```

## 数据库配置

### 1. 主菜单配置

**数据中心** 主菜单配置：

| 字段 | 值 | 说明 |
|------|-----|------|
| name | 数据中心 | 菜单显示名称 |
| parent_id | 1 | 父级菜单ID（概述菜单） |
| url | /data-center | 路由路径 |
| component | LAYOUT | 布局组件 |
| component_name | DataCenter | 组件名称 |
| redirect | /data-center/environment-monitoring | 默认重定向路径 |
| menu_type | 0 | 主菜单 |
| perms | datacenter:view | 权限标识 |
| icon | ion:server-outline | 图标 |
| is_leaf | 0 | 不是叶子节点（有子菜单） |
| sort_no | 5 | 排序号 |

### 2. 子菜单配置

#### 环境监测设备

| 字段 | 值 | 说明 |
|------|-----|------|
| name | 环境监测设备 | 菜单显示名称 |
| parent_id | @data_center_id | 数据中心菜单ID |
| url | /data-center/environment-monitoring | 路由路径 |
| component | /@/views/dataCenter/EnvironmentMonitoring/index.vue | 组件路径 |
| component_name | EnvironmentMonitoring | 组件名称 |
| menu_type | 1 | 子菜单 |
| perms | datacenter:environment:view | 权限标识 |
| icon | ion:thermometer-outline | 图标 |
| is_leaf | 1 | 是叶子节点 |
| sort_no | 1 | 排序号 |

#### 电表设备

| 字段 | 值 | 说明 |
|------|-----|------|
| name | 电表设备 | 菜单显示名称 |
| parent_id | @data_center_id | 数据中心菜单ID |
| url | /data-center/power-meter | 路由路径 |
| component | /@/views/dataCenter/PowerMeter/index.vue | 组件路径 |
| component_name | PowerMeter | 组件名称 |
| menu_type | 1 | 子菜单 |
| perms | datacenter:powermeter:view | 权限标识 |
| icon | ion:flash-outline | 图标 |
| is_leaf | 1 | 是叶子节点 |
| sort_no | 2 | 排序号 |

## 执行步骤

### 1. 执行SQL脚本

```bash
# 连接到MySQL数据库
mysql -u root -p ezdata

# 执行菜单配置SQL
source add_data_center_menu.sql
```

### 2. 验证菜单配置

```sql
-- 查看数据中心相关菜单
SELECT id, name, parent_id, url, component, icon, sort_no 
FROM sys_permission 
WHERE name LIKE '%数据中心%' OR name LIKE '%环境监测%' OR name LIKE '%电表%' 
ORDER BY sort_no;
```

### 3. 分配角色权限

```sql
-- 给admin角色分配数据中心权限
INSERT INTO sys_role_permission (role_id, permission_id) 
SELECT 1, id FROM sys_permission 
WHERE name IN ('数据中心', '环境监测设备', '电表设备');
```

## 权限配置

### 权限标识说明

- `datacenter:view` - 数据中心查看权限
- `datacenter:environment:view` - 环境监测设备查看权限
- `datacenter:powermeter:view` - 电表设备查看权限

### 角色权限分配

如果需要给特定角色分配权限，可以：

1. 查找角色ID：
```sql
SELECT id, role_name FROM sys_role WHERE role_name = 'admin';
```

2. 分配权限：
```sql
INSERT INTO sys_role_permission (role_id, permission_id) 
SELECT [角色ID], id FROM sys_permission 
WHERE name IN ('数据中心', '环境监测设备', '电表设备');
```

## 前端路由配置

前端路由配置已自动生成在 `web/src/router/routes/modules/dataCenter.ts` 中：

```typescript
const dataCenter: AppRouteModule = {
  path: '/data-center',
  name: 'DataCenter',
  component: LAYOUT,
  redirect: '/data-center/environment-monitoring',
  meta: {
    orderNo: 5,
    icon: 'ion:server-outline',
    title: '数据中心',
    hideChildrenInMenu: false,
  },
  children: [
    {
      path: 'environment-monitoring',
      name: 'EnvironmentMonitoring',
      component: () => import('/@/views/dataCenter/EnvironmentMonitoring/index.vue'),
      meta: {
        title: '环境监测设备',
        icon: 'ion:thermometer-outline',
        hideMenu: false,
      },
    },
    {
      path: 'power-meter',
      name: 'PowerMeter',
      component: () => import('/@/views/dataCenter/PowerMeter/index.vue'),
      meta: {
        title: '电表设备',
        icon: 'ion:flash-outline',
        hideMenu: false,
      },
    },
  ],
};
```

## 注意事项

1. **parent_id 调整**：如果概述菜单的ID不是1，需要调整SQL中的parent_id值
2. **权限系统**：根据实际的权限系统调整角色权限分配方式
3. **图标**：确保使用的图标在系统中可用
4. **组件路径**：确保组件文件路径正确
5. **排序号**：根据实际需求调整sort_no值

## 故障排除

### 菜单不显示
1. 检查parent_id是否正确
2. 检查权限是否已分配给当前用户角色
3. 检查菜单状态是否为有效（status=1）

### 页面无法访问
1. 检查组件路径是否正确
2. 检查路由配置是否正确
3. 检查权限标识是否正确

### 图标不显示
1. 检查图标名称是否正确
2. 确保图标库已正确加载
