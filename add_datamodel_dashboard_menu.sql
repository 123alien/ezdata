-- 添加数据模型看板菜单到 sys_permission 表
-- 假设概述菜单的 parent_id 是 1（需要根据实际情况调整）

-- 1. 先查找概述菜单的 ID
-- SELECT id, name, parent_id FROM sys_permission WHERE name LIKE '%概述%' OR name LIKE '%dashboard%';

-- 2. 添加数据模型看板菜单（概述菜单的 parent_id 是 1）
INSERT INTO sys_permission (
    id,
    name,
    parent_id,
    url,
    component,
    component_name,
    redirect,
    menu_type,
    perms,
    perms_type,
    always_show,
    icon,
    is_route,
    is_leaf,
    keep_alive,
    hidden,
    hide_tab,
    rule_flag,
    status,
    internal_or_external,
    sort_no,
    del_flag,
    create_by,
    create_time,
    update_by,
    update_time
) VALUES (
    NULL,  -- 使用AUTO_INCREMENT
    '数据模型看板',
    1,  -- 父级ID，概述菜单的ID是1
    '/dashboard/datamodel',
    '/@/views/dashboard/DataModelDashboard.vue',
    'DataModelDashboard',
    '',
    1,  -- 子菜单
    'datamodel:dashboard',
    1,  -- 显示
    1,  -- 聚合子路由
    'ion:bar-chart-outline',
    1,  -- 是路由菜单
    1,  -- 是叶子节点
    1,  -- 缓存页面
    0,  -- 不隐藏路由
    0,  -- 不隐藏tab
    0,  -- 不添加数据权限
    1,  -- 有效
    0,  -- 内部打    0.5, -- 排序号，放在首页和工作台之间
    0,  -- 未删除
    'admin',
    NOW(),
    'admin',
    NOW()
);

-- 3. 如果需要给角色分配权限，可以执行以下查询
-- 查找角色ID
-- SELECT id, role_name FROM sys_role WHERE role_name = 'admin';

-- 给角色分配菜单权限（假设admin角色ID是1）
-- UPDATE sys_role SET permissions = JSON_ARRAY_APPEND(permissions, '$', (SELECT id FROM sys_permission WHERE name = '数据模型看板' ORDER BY create_time DESC LIMIT 1)) WHERE id = 1;
