-- 创建 rag_knowledge_base 表
CREATE TABLE IF NOT EXISTS `rag_knowledge_base` (
    `id` INT AUTO_INCREMENT COMMENT 'id主键',
    `name` VARCHAR(200) NOT NULL COMMENT '知识库名称',
    `description` TEXT COMMENT '知识库描述',
    `owner_id` VARCHAR(36) NOT NULL COMMENT '所有者用户ID',
    `is_public` SMALLINT DEFAULT 0 COMMENT '是否公开 (0: 私有, 1: 公开)',
    `status` SMALLINT DEFAULT 1 COMMENT '状态 (1: 启用, 0: 禁用)',
    `tenant_id` INT DEFAULT 1 COMMENT '租户id',
    `sort_no` FLOAT DEFAULT 1 COMMENT '排序',
    `del_flag` SMALLINT DEFAULT 0 COMMENT '软删除标记',
    `create_by` VARCHAR(100) DEFAULT '' COMMENT '创建者',
    `create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_by` VARCHAR(100) DEFAULT '' COMMENT '修改者',
    `update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_kb_name_owner` (`name`, `owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户知识库表';

-- 创建 rag_kb_document 表
CREATE TABLE IF NOT EXISTS `rag_kb_document` (
    `id` INT AUTO_INCREMENT COMMENT 'id主键',
    `kb_id` INT NOT NULL COMMENT '知识库ID',
    `document_name` VARCHAR(200) NOT NULL COMMENT '文档名称',
    `file_path` VARCHAR(500) COMMENT '文件存储路径',
    `file_type` VARCHAR(50) COMMENT '文件类型',
    `status` SMALLINT DEFAULT 1 COMMENT '文档处理状态 (1: 待处理, 2: 处理中, 3: 已处理, 4: 处理失败)',
    `doc_metadata` TEXT COMMENT '文档元数据',
    `tenant_id` INT DEFAULT 1 COMMENT '租户id',
    `sort_no` FLOAT DEFAULT 1 COMMENT '排序',
    `del_flag` SMALLINT DEFAULT 0 COMMENT '软删除标记',
    `create_by` VARCHAR(100) DEFAULT '' COMMENT '创建者',
    `create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_by` VARCHAR(100) DEFAULT '' COMMENT '修改者',
    `update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    PRIMARY KEY (`id`),
    FOREIGN KEY (`kb_id`) REFERENCES `rag_knowledge_base`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='知识库文档表';

-- 创建 rag_kb_share_permission 表
CREATE TABLE IF NOT EXISTS `rag_kb_share_permission` (
    `id` INT AUTO_INCREMENT COMMENT 'id主键',
    `kb_id` INT NOT NULL COMMENT '知识库ID',
    `shared_by_id` VARCHAR(36) NOT NULL COMMENT '分享者用户ID',
    `shared_with_id` VARCHAR(36) NOT NULL COMMENT '被分享者用户ID',
    `permission_level` VARCHAR(50) DEFAULT 'read' COMMENT '权限级别 (read, write, admin)',
    `status` SMALLINT DEFAULT 1 COMMENT '分享状态 (1: 有效, 0: 失效)',
    `tenant_id` INT DEFAULT 1 COMMENT '租户id',
    `sort_no` FLOAT DEFAULT 1 COMMENT '排序',
    `del_flag` SMALLINT DEFAULT 0 COMMENT '软删除标记',
    `create_by` VARCHAR(100) DEFAULT '' COMMENT '创建者',
    `create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_by` VARCHAR(100) DEFAULT '' COMMENT '修改者',
    `update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_kb_share` (`kb_id`, `shared_with_id`),
    FOREIGN KEY (`kb_id`) REFERENCES `rag_knowledge_base`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='知识库分享权限表';