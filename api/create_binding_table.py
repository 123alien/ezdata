#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建知识库绑定表的数据库迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_apps import app, db
from web_apps.rag.kb_models import KnowledgeBaseBinding
from sqlalchemy import text

def create_binding_table():
    """创建知识库绑定表"""
    try:
        with app.app_context():
            # 创建表
            db.create_all()
            print("✅ 知识库绑定表创建成功")
            
            # 验证表是否存在
            try:
                # 尝试查询表，如果能查询说明表存在
                db.session.execute(text("SELECT 1 FROM rag_kb_binding LIMIT 1"))
                print("✅ 表 'rag_kb_binding' 已存在")
            except Exception as e:
                print(f"❌ 表 'rag_kb_binding' 创建失败: {str(e)}")
                return False
            
            # 显示表结构
            try:
                result = db.session.execute(text("DESCRIBE rag_kb_binding"))
                columns = result.fetchall()
                print("\n📋 表结构:")
                for col in columns:
                    print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")
            except Exception as e:
                print(f"⚠️  无法显示表结构: {str(e)}")
            
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
