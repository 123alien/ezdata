#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试知识库绑定功能的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_apps import db
from web_apps.rag.kb_models import KnowledgeBaseBinding, UserKnowledgeBase
from web_apps.rag.services.kb_service import KnowledgeBaseService

def test_binding_operations():
    """测试绑定相关操作"""
    try:
        print("🧪 开始测试知识库绑定功能...")
        
        # 1. 查询现有知识库
        kb_service = KnowledgeBaseService()
        kbs = kb_service.get_my_knowledge_bases('test-user-id')
        print(f"📚 找到 {len(kbs)} 个知识库")
        
        if not kbs:
            print("⚠️  没有找到知识库，无法测试绑定功能")
            return False
        
        # 2. 测试创建绑定
        test_kb = kbs[0]
        print(f"\n🔗 测试为知识库 '{test_kb.kb_name}' (ID: {test_kb.id}) 创建绑定...")
        
        # 检查是否已有绑定
        existing_binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == test_kb.id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if existing_binding:
            print(f"✅ 已存在绑定: namespace='{existing_binding.namespace}', 备注='{existing_binding.remark}'")
        else:
            # 创建新绑定
            new_binding = KnowledgeBaseBinding(
                kb_id=test_kb.id,
                namespace=f"test-namespace-{test_kb.id}",
                remark="测试绑定",
                create_by="test-user-id"
            )
            db.session.add(new_binding)
            db.session.commit()
            print(f"✅ 创建绑定成功: namespace='{new_binding.namespace}'")
        
        # 3. 测试查询绑定
        print(f"\n🔍 测试查询知识库 {test_kb.id} 的绑定信息...")
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == test_kb.id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if binding:
            print(f"✅ 查询成功: namespace='{binding.namespace}', 备注='{binding.remark}'")
        else:
            print("❌ 查询绑定失败")
            return False
        
        # 4. 测试更新绑定
        print(f"\n✏️  测试更新绑定信息...")
        old_namespace = binding.namespace
        binding.namespace = f"updated-{old_namespace}"
        binding.remark = "已更新的测试绑定"
        db.session.commit()
        print(f"✅ 更新成功: namespace='{binding.namespace}'")
        
        # 5. 测试删除绑定
        print(f"\n🗑️  测试删除绑定...")
        binding.del_flag = 1
        db.session.commit()
        print("✅ 删除成功")
        
        # 6. 验证删除
        deleted_binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == test_kb.id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if not deleted_binding:
            print("✅ 删除验证成功")
        else:
            print("❌ 删除验证失败")
            return False
        
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_binding_operations()
    
    if success:
        print("\n🎉 知识库绑定功能测试完成！")
    else:
        print("\n💥 知识库绑定功能测试失败！")
        sys.exit(1)
