#!/usr/bin/env python3
"""
执行菜单SQL脚本
"""
import pymysql
import sys

# 数据库连接配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'ezdata123',
    'database': 'ezdata',
    'charset': 'utf8mb4'
}

def execute_sql():
    """执行SQL脚本"""
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 读取SQL文件
        with open('add_datamodel_dashboard_menu.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（按分号分割）
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        # 执行每个SQL语句
        for sql in sql_statements:
            if sql:
                print(f"执行SQL: {sql[:100]}...")
                cursor.execute(sql)
                connection.commit()
                print("✓ 执行成功")
        
        # 验证插入结果
        cursor.execute("SELECT id, name, parent_id, url FROM sys_permission WHERE name = '数据模型看板'")
        result = cursor.fetchone()
        
        if result:
            print(f"✓ 菜单添加成功！ID: {result[0]}, 名称: {result[1]}, 父级ID: {result[2]}, 路径: {result[3]}")
        else:
            print("✗ 菜单添加失败，未找到记录")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"✗ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    execute_sql()
