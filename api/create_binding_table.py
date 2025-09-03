#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建知识库绑定表的数据库迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_apps import db
from web_apps.rag.kb_models import KnowledgeBaseBinding

def create_binding_table():
    """创建知识库绑定表"""
    try:
        # 创建表
        db.create_all()
        print("✅ 知识库绑定表创建成功")
        
        # 验证表是否存在
        with db.engine.connect() as conn:
            result = conn.execute("SHOW TABLES LIKE 'rag_kb_binding'")
            if result.fetchone():
                print("✅ 表 'rag_kb_binding' 已存在")
            else:
                print("❌ 表 'rag_kb_binding' 创建失败")
                return False
        
        # 显示表结构
        with db.engine.connect() as conn:
            result = conn.execute("DESCRIBE rag_kb_binding")
            columns = result.fetchall()
            print("\n📋 表结构:")
            for col in columns:
                print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 开始创建知识库绑定表...")
    success = create_binding_table()
    
    if success:
        print("\n🎉 知识库绑定表创建完成！")
    else:
        print("\n💥 知识库绑定表创建失败！")
        sys.exit(1)
