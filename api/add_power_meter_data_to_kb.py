# -*- coding: utf-8 -*-
"""
将电表数据作为文档添加到"电表"知识库
"""
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_apps import app, db
from web_apps.rag.db_models import Document
from web_apps.rag.kb_models import KnowledgeBaseBinding
from web_apps.rag.services.rag_service import train_document
from web_apps.rag.services.trustrag_sync_service import sync_created_document
from utils.common_utils import gen_uuid
from pymongo import MongoClient

# MongoDB配置
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "admin123")
MONGO_DB = os.getenv("MONGO_DB", "ezdata")
MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")

# 集合名称
SNAPSHOT_COLL = "power_meter_daily_snapshot"
FACTOR_COLL = "power_meter_daily_factor_snapshot"


def get_mongo_client() -> MongoClient:
    """获取MongoDB客户端"""
    params = {"host": MONGO_HOST, "port": MONGO_PORT}
    if MONGO_USERNAME and MONGO_PASSWORD:
        params.update(username=MONGO_USERNAME, password=MONGO_PASSWORD, authSource=MONGO_AUTH_SOURCE)
    return MongoClient(**params)


def fetch_power_meter_data(limit: int = 100) -> List[Dict[str, Any]]:
    """从MongoDB获取电表数据"""
    client = get_mongo_client()
    try:
        db_mongo = client[MONGO_DB]
        
        # 获取最新的快照数据，按时间倒序
        snapshots = list(db_mongo[SNAPSHOT_COLL].find().sort("update_time", -1).limit(limit))
        
        data_list = []
        for snapshot in snapshots:
            device_num = snapshot.get("device_num")
            device_name = snapshot.get("device_name", device_num)
            update_time = snapshot.get("update_time")
            
            # 获取对应的因子数据（功率值）
            factors = list(db_mongo[FACTOR_COLL].find({
                "device_num": device_num,
                "update_time": update_time
            }))
            
            power_data = {}
            for factor in factors:
                factor_name = factor.get("factor_name")
                factor_value = factor.get("factor_value")
                if factor_name == "功率" or factor.get("factor_code") == "power":
                    power_data["power"] = factor_value
                    power_data["unit"] = factor.get("factor_unit", "kW")
            
            if power_data:
                data_list.append({
                    "device_num": device_num,
                    "device_name": device_name,
                    "update_time": update_time.strftime("%Y-%m-%d %H:%M:%S") if update_time else "",
                    "power": power_data.get("power"),
                    "unit": power_data.get("unit", "kW")
                })
        
        return data_list
    finally:
        client.close()


def format_data_as_text(data_list: List[Dict[str, Any]]) -> str:
    """将电表数据格式化为文本"""
    if not data_list:
        return "暂无电表数据"
    
    lines = ["电表数据汇总", "=" * 60]
    lines.append(f"数据记录数: {len(data_list)}")
    lines.append(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # 按设备分组
    devices = {}
    for item in data_list:
        device_num = item.get("device_num")
        if device_num not in devices:
            devices[device_num] = {
                "name": item.get("device_name", device_num),
                "records": []
            }
        devices[device_num]["records"].append(item)
    
    # 格式化输出
    for device_num, device_info in devices.items():
        lines.append(f"\n设备编号: {device_num}")
        lines.append(f"设备名称: {device_info['name']}")
        lines.append(f"记录数: {len(device_info['records'])}")
        lines.append("")
        lines.append("历史数据:")
        for record in sorted(device_info['records'], key=lambda x: x.get('update_time', ''), reverse=True):
            power = record.get('power')
            unit = record.get('unit', 'kW')
            time_str = record.get('update_time', '')
            if power is not None:
                lines.append(f"  时间: {time_str}, 功率: {power:.2f} {unit}")
        lines.append("")
    
    return "\n".join(lines)


def add_power_meter_data_to_kb():
    """将电表数据添加到知识库"""
    with app.app_context():
        try:
            # 1. 找到"电表"知识库
            binding = db.session.query(KnowledgeBaseBinding).filter(
                KnowledgeBaseBinding.namespace == "dian",
                KnowledgeBaseBinding.del_flag == 0
            ).first()
            
            if not binding:
                print("❌ 未找到namespace 'dian'的绑定")
                return False
            
            dataset_id = binding.kb_id
            print(f"✅ 找到知识库ID: {dataset_id}")
            
            # 2. 从MongoDB获取电表数据
            print("正在从MongoDB读取电表数据...")
            data_list = fetch_power_meter_data(limit=100)
            
            if not data_list:
                print("❌ 未找到电表数据")
                return False
            
            print(f"✅ 读取到 {len(data_list)} 条电表数据记录")
            
            # 3. 格式化数据为文本
            content = format_data_as_text(data_list)
            
            # 4. 创建文档
            doc_name = f"电表数据-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            doc_id = gen_uuid(res_type='base')
            
            # 创建一个临时文本文件来保存内容
            temp_file_path = f"/tmp/power_meter_data_{doc_id}.txt"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            document = Document(
                id=doc_id,
                dataset_id=dataset_id,
                document_type="upload_file",  # 使用upload_file类型，避免WebsiteInfo验证错误
                name=doc_name,
                status=1,  # 待训练
                meta_data=json.dumps({
                    "upload_file": temp_file_path,
                    "source": "power_meter_mongodb",
                    "data_count": len(data_list),
                    "created_at": datetime.now().isoformat()
                }, ensure_ascii=False),
                create_by="admin",
                create_time=datetime.now()
            )
            
            db.session.add(document)
            db.session.commit()
            db.session.flush()
            print(f"✅ 创建文档成功: {doc_name} (ID: {doc_id})")
            
            # 5. 训练文档（会触发本地索引）
            print("正在训练文档...")
            try:
                train_document(doc_id, metadata={"user_name": "admin"})
                print("✅ 文档训练成功")
            except Exception as e:
                print(f"⚠️ 文档训练失败: {e}，但会继续同步到TrustRAG")
            
            # 6. 同步到TrustRAG（使用mock request context）
            print("正在同步到TrustRAG...")
            try:
                from flask import Flask, has_request_context
                from utils.auth import get_auth_token_info
                
                # 创建一个临时的request context来模拟用户登录
                with app.test_request_context('/'):
                    # 模拟用户信息（如果需要）
                    # 这里不设置用户信息，让sync_created_document使用默认值
                    meta_data = json.loads(document.meta_data)
                    
                    # 直接调用同步服务，绕过request context检查
                    from web_apps.rag.services.trustrag_sync_service import _resolve_namespace_by_dataset, _generate_sso_token, _build_minio_file_url
                    import requests
                    
                    namespace = _resolve_namespace_by_dataset(dataset_id)
                    if namespace:
                        # 读取文件内容
                        upload_file_path = meta_data.get("upload_file")
                        raw_text = None
                        if upload_file_path and os.path.exists(upload_file_path):
                            try:
                                with open(upload_file_path, 'r', encoding='utf-8') as f:
                                    raw_text = f.read()
                            except Exception:
                                pass
                        
                        # 生成token（使用默认用户信息）
                        user_id = ""
                        tenant_id = 1
                        token = _generate_sso_token(user_id, tenant_id, dataset_id, namespace)
                        
                        # 调用TrustRAG API
                        base_url = app.config.get("TRUSTRAG_BASE_URL", "http://127.0.0.1:8217")
                        headers = {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        }
                        
                        if raw_text:
                            body = {
                                "namespace": namespace,
                                "raw_text": raw_text,
                            }
                        else:
                            file_name = upload_file_path.split('/')[-1]
                            file_url = _build_minio_file_url(file_name)
                            body = {
                                "namespace": namespace,
                                "documents": [{"url": file_url}],
                            }
                        
                        url = f"{base_url.rstrip('/')}/ingest"
                        resp = requests.post(url, json=body, headers=headers, timeout=30)
                        ok = 200 <= resp.status_code < 300
                        
                        if ok:
                            print(f"✅ 同步到TrustRAG成功 (namespace: {namespace})")
                        else:
                            print(f"⚠️ 同步到TrustRAG失败: {resp.status_code} {resp.text}")
                    else:
                        print(f"⚠️ 未找到namespace绑定")
            except Exception as e:
                print(f"⚠️ 同步到TrustRAG失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 7. 清理临时文件（可选，保留文件也可）
            # os.remove(temp_file_path)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("将电表数据作为文档添加到'电表'知识库")
    print("=" * 60)
    print()
    
    success = add_power_meter_data_to_kb()
    
    if success:
        print()
        print("=" * 60)
        print("✅ 操作完成！")
        print("=" * 60)
        print()
        print("📝 文档已添加到知识库，可以通过以下方式使用：")
        print("   1. 在Web界面 'RAG > 我的知识库' 中查看文档")
        print("   2. 在 'RAG > 外部服务' 中使用namespace 'dian' 进行问答")
        print("   3. 可以查询电表数据相关问题")
    else:
        print()
        print("❌ 操作失败，请检查错误信息")

