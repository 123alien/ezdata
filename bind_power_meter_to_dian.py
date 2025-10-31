# -*- coding: utf-8 -*-
"""
将电表数据接入namespace为"dian"的知识库
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_apps import app, db
from web_apps.rag.db_models import Dataset
from web_apps.rag.kb_models import KnowledgeBaseBinding
from utils.common_utils import gen_uuid
from utils.auth import set_insert_user
from datetime import datetime

def create_power_meter_kb_and_bind():
    """创建电表数据知识库并绑定到namespace 'dian'"""
    with app.app_context():
        try:
            # 1. 检查是否已经存在"电表数据"知识库
            kb_name = "电表数据"
            existing_kb = db.session.query(Dataset).filter(
                Dataset.name == kb_name,
                Dataset.del_flag == 0
            ).first()
            
            if existing_kb:
                dataset_id = existing_kb.id
                print(f"✅ 找到已存在的知识库: {kb_name} (ID: {dataset_id})")
            else:
                # 2. 创建新的Dataset
                dataset = Dataset(
                    id=gen_uuid(res_type='base'),
                    name=kb_name,
                    built_in=0,
                    status=1
                )
                set_insert_user(dataset)  # 设置创建用户
                db.session.add(dataset)
                db.session.commit()
                dataset_id = dataset.id
                print(f"✅ 创建知识库成功: {kb_name} (ID: {dataset_id})")
            
            # 3. 检查是否已经存在绑定
            existing_binding = db.session.query(KnowledgeBaseBinding).filter(
                KnowledgeBaseBinding.kb_id == dataset_id,
                KnowledgeBaseBinding.del_flag == 0
            ).first()
            
            namespace = "dian"
            
            if existing_binding:
                if existing_binding.namespace == namespace:
                    print(f"✅ 绑定已存在: 知识库 '{kb_name}' 已绑定到 namespace '{namespace}'")
                    return dataset_id, namespace
                else:
                    # 更新绑定
                    existing_binding.namespace = namespace
                    existing_binding.remark = f"电表数据知识库 - 绑定时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    existing_binding.update_time = datetime.now()
                    db.session.commit()
                    print(f"✅ 更新绑定成功: 知识库 '{kb_name}' 绑定到 namespace '{namespace}'")
            else:
                # 4. 检查namespace是否已被其他知识库使用
                conflict_binding = db.session.query(KnowledgeBaseBinding).filter(
                    KnowledgeBaseBinding.namespace == namespace,
                    KnowledgeBaseBinding.kb_id != dataset_id,
                    KnowledgeBaseBinding.del_flag == 0
                ).first()
                
                if conflict_binding:
                    print(f"❌ 错误: namespace '{namespace}' 已被其他知识库使用")
                    return None, None
                
                # 5. 创建绑定
                binding = KnowledgeBaseBinding(
                    kb_id=dataset_id,
                    namespace=namespace,
                    remark=f"电表数据知识库 - 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                set_insert_user(binding)
                db.session.add(binding)
                db.session.commit()
                print(f"✅ 绑定创建成功: 知识库 '{kb_name}' 绑定到 namespace '{namespace}'")
            
            return dataset_id, namespace
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 操作失败: {e}")
            import traceback
            traceback.print_exc()
            return None, None

if __name__ == "__main__":
    print("=" * 60)
    print("将电表数据接入namespace为'dian'的知识库")
    print("=" * 60)
    print()
    
    dataset_id, namespace = create_power_meter_kb_and_bind()
    
    if dataset_id and namespace:
        print()
        print("=" * 60)
        print("✅ 操作完成！")
        print(f"   知识库ID: {dataset_id}")
        print(f"   Namespace: {namespace}")
        print("=" * 60)
        print()
        print("📝 接下来可以：")
        print("   1. 在Web界面 'RAG > 我的知识库' 中查看该知识库")
        print("   2. 上传电表数据相关的文档到该知识库")
        print("   3. 在 'RAG > 外部服务' 中使用namespace 'dian' 进行问答")
    else:
        print()
        print("❌ 操作失败，请检查错误信息")

