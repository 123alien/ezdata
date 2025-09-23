-- 添加数据中心菜单配置到 sys_permission 表
-- 假设概述菜单的 parent_id 是 1（需要根据实际情况调整）

-- 1. 先查找概述菜单的 ID
-- SELECT id, name, parent_id FROM sys_permission WHERE name LIKE '%概述%' OR name LIKE '%dashboard%';

-- 2. 添加数据中心主菜单
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
    '数据中心',
    1,  -- 父级ID，概述菜单的ID是1
    '/data-center',
    'LAYOUT',
    'DataCenter',
    '/data-center/environment-monitoring',
    0,  -- 主菜单
    'datacenter:view',
    1,  -- 显示
    1,  -- 聚合子路由
    'ion:server-outline',
    1,  -- 是路由菜单
    0,  -- 不是叶子节点（有子菜单）
    1,  -- 缓存页面
    0,  -- 不隐藏路由
    0,  -- 不隐藏tab
    0,  -- 不添加数据权限
    1,  -- 有效
    0,  -- 内部路由
    5,  -- 排序号，放在数据模型看板之后
    0,  -- 未删除
    'admin',
    NOW(),
    'admin',
    NOW()
);

-- 3. 获取数据中心菜单的ID（用于子菜单的parent_id）
SET @data_center_id = LAST_INSERT_ID();

-- 4. 添加环境监测设备子菜单
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
    '环境监测设备',
    @data_center_id,  -- 父级ID，数据中心菜单的ID
    '/data-center/environment-monitoring',
    '/@/views/dataCenter/EnvironmentMonitoring/index.vue',
    'EnvironmentMonitoring',
    '',
    1,  -- 子菜单
    'datacenter:environment:view',
    1,  -- 显示
    0,  -- 不聚合子路由
    'ion:thermometer-outline',
    1,  -- 是路由菜单
    1,  -- 是叶子节点
    1,  -- 缓存页面
    0,  -- 不隐藏路由
    0,  -- 不隐藏tab
    0,  -- 不添加数据权限
    1,  -- 有效
    0,  -- 内部路由
    1,  -- 排序号，第一个子菜单
    0,  -- 未删除
    'admin',
    NOW(),
    'admin',
    NOW()
);

-- 5. 添加电表设备子菜单
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
    '电表设备',
    @data_center_id,  -- 父级ID，数据中心菜单的ID
    '/data-center/power-meter',
    '/@/views/dataCenter/PowerMeter/index.vue',
    'PowerMeter',
    '',
    1,  -- 子菜单
    'datacenter:powermeter:view',
    1,  -- 显示
    0,  -- 不聚合子路由
    'ion:flash-outline',
    1,  -- 是路由菜单
    1,  -- 是叶子节点
    1,  -- 缓存页面
    0,  -- 不隐藏路由
    0,  -- 不隐藏tab
    0,  -- 不添加数据权限
    1,  -- 有效
    0,  -- 内部路由
    2,  -- 排序号，第二个子菜单
    0,  -- 未删除
    'admin',
    NOW(),
    'admin',
    NOW()
);

-- 6. 如果需要给角色分配权限，可以执行以下查询
-- 查找角色ID
-- SELECT id, role_name FROM sys_role WHERE role_name = 'admin';

-- 给角色分配菜单权限（假设admin角色ID是1）
-- 注意：这里需要根据实际的权限系统来调整，可能需要更新角色权限表

-- 示例：给admin角色分配数据中心权限
-- INSERT INTO sys_role_permission (role_id, permission_id) 
-- SELECT 1, id FROM sys_permission WHERE name IN ('数据中心', '环境监测设备', '电表设备');

-- 7. 验证菜单是否添加成功
-- SELECT id, name, parent_id, url, component, icon, sort_no FROM sys_permission WHERE name LIKE '%数据中心%' OR name LIKE '%环境监测%' OR name LIKE '%电表%' ORDER BY sort_no;
