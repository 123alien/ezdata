# -*- coding: utf-8 -*-
"""
电表数据同步到知识库
每天将电表数据同步到"电表"知识库（更新同一文档）
"""
import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目路径
base_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(base_dir, 'api')
sys.path.insert(0, api_dir)
os.chdir(api_dir)  # 切换到api目录

from web_apps import app, db
from web_apps.rag.db_models import Document
from web_apps.rag.kb_models import KnowledgeBaseBinding
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

# 同步配置
SYNC_INTERVAL = int(os.getenv("POWER_METER_SYNC_INTERVAL", "86400"))  # 默认24小时（1天）同步一次
DATA_LIMIT = int(os.getenv("POWER_METER_SYNC_DATA_LIMIT", "500"))  # 每次同步的数据条数（一天的数据）
SYNC_TIME = os.getenv("POWER_METER_SYNC_TIME", "02:00")  # 默认每天凌晨2点同步

# 日志配置
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("power_meter_kb_sync")
logger.setLevel(logging.INFO)

log_file = os.getenv("POWER_METER_SYNC_LOG_FILE", "power_meter_kb_sync.log")
file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
console_handler = logging.StreamHandler()
fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(fmt)
console_handler.setFormatter(fmt)
logger.handlers = [file_handler, console_handler]


def get_mongo_client() -> MongoClient:
    """获取MongoDB客户端"""
    params = {"host": MONGO_HOST, "port": MONGO_PORT}
    if MONGO_USERNAME and MONGO_PASSWORD:
        params.update(username=MONGO_USERNAME, password=MONGO_PASSWORD, authSource=MONGO_AUTH_SOURCE)
    return MongoClient(**params)


def fetch_recent_power_meter_data(since_time: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
    """从MongoDB获取最新的电表数据"""
    client = get_mongo_client()
    try:
        db_mongo = client[MONGO_DB]
        
        # 构建查询条件
        query = {}
        if since_time:
            query["update_time"] = {"$gte": since_time}
        
        # 获取最新的快照数据，按时间倒序
        snapshots = list(db_mongo[SNAPSHOT_COLL].find(query).sort("update_time", -1).limit(limit))
        
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


def sync_to_kb(data_list: List[Dict[str, Any]]) -> bool:
    """将电表数据同步到知识库（更新同一文档）"""
    with app.app_context():
        try:
            # 1. 找到"电表"知识库
            binding = db.session.query(KnowledgeBaseBinding).filter(
                KnowledgeBaseBinding.namespace == "dian",
                KnowledgeBaseBinding.del_flag == 0
            ).first()
            
            if not binding:
                logger.warning("未找到namespace 'dian'的绑定")
                return False
            
            dataset_id = binding.kb_id
            
            # 2. 查找或创建固定的电表数据文档
            doc_name = "电表数据实时汇总"
            existing_doc = db.session.query(Document).filter(
                Document.dataset_id == dataset_id,
                Document.name == doc_name,
                Document.del_flag == 0
            ).first()
            
            if existing_doc:
                # 更新现有文档
                doc_id = existing_doc.id
                logger.info(f"找到现有文档: {doc_name} (ID: {doc_id})，将更新内容")
                
                # 获取所有历史数据（包括新数据）
                all_data = fetch_recent_power_meter_data(limit=DATA_LIMIT * 2)
                content = format_data_as_text(all_data)
                
                # 更新临时文本文件
                temp_file_path = f"/tmp/power_meter_data_{doc_id}.txt"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 更新文档元数据
                meta_data = json.loads(existing_doc.meta_data) if existing_doc.meta_data else {}
                meta_data.update({
                    "upload_file": temp_file_path,
                    "source": "power_meter_mongodb_realtime",
                    "data_count": len(all_data),
                    "last_updated": datetime.now().isoformat(),
                    "update_count": meta_data.get("update_count", 0) + 1
                })
                existing_doc.meta_data = json.dumps(meta_data, ensure_ascii=False)
                existing_doc.update_time = datetime.now()
                existing_doc.status = 1  # 重新标记为待训练
                db.session.commit()
                db.session.flush()
                logger.info(f"更新文档成功: {doc_name}，数据量: {len(all_data)}")
            else:
                # 创建新文档
                logger.info(f"未找到现有文档，创建新文档: {doc_name}")
                doc_id = gen_uuid(res_type='base')
                
                # 格式化数据为文本
                content = format_data_as_text(data_list)
                
                # 创建临时文本文件
                temp_file_path = f"/tmp/power_meter_data_{doc_id}.txt"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                document = Document(
                    id=doc_id,
                    dataset_id=dataset_id,
                    document_type="upload_file",
                    name=doc_name,
                    status=1,  # 待训练
                    meta_data=json.dumps({
                        "upload_file": temp_file_path,
                        "source": "power_meter_mongodb_realtime",
                        "data_count": len(data_list),
                        "created_at": datetime.now().isoformat(),
                        "update_count": 1
                    }, ensure_ascii=False),
                    create_by="admin",
                    create_time=datetime.now()
                )
                
                db.session.add(document)
                db.session.commit()
                db.session.flush()
                logger.info(f"创建文档成功: {doc_name} (ID: {doc_id})")
            
            # 4. 同步到TrustRAG
            try:
                from web_apps.rag.services.trustrag_sync_service import _resolve_namespace_by_dataset, _generate_sso_token, _build_minio_file_url
                import requests
                
                namespace = _resolve_namespace_by_dataset(dataset_id)
                if namespace:
                    # 读取文件内容
                    raw_text = None
                    if os.path.exists(temp_file_path):
                        try:
                            with open(temp_file_path, 'r', encoding='utf-8') as f:
                                raw_text = f.read()
                        except Exception:
                            pass
                    
                    # 生成token
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
                        file_name = temp_file_path.split('/')[-1]
                        file_url = _build_minio_file_url(file_name)
                        body = {
                            "namespace": namespace,
                            "documents": [{"url": file_url}],
                        }
                    
                    url = f"{base_url.rstrip('/')}/ingest"
                    resp = requests.post(url, json=body, headers=headers, timeout=30)
                    ok = 200 <= resp.status_code < 300
                    
                    if ok:
                        logger.info(f"同步到TrustRAG成功 (namespace: {namespace})")
                    else:
                        logger.warning(f"同步到TrustRAG失败: {resp.status_code} {resp.text}")
                else:
                    logger.warning("未找到namespace绑定")
            except Exception as e:
                logger.error(f"同步到TrustRAG失败: {e}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"同步失败: {e}", exc_info=True)
            return False


def sync_loop():
    """主同步循环（每天执行一次）"""
    try:
        import schedule
    except ImportError:
        logger.error("缺少 schedule 依赖，请安装: pip install schedule")
        return
    
    # 注册每天定时同步任务
    schedule.every().day.at(SYNC_TIME).do(sync_once)
    logger.info(f"已注册定时任务：每天 {SYNC_TIME} 同步电表数据到知识库")
    
    # 主循环
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


def sync_once():
    """执行一次同步"""
    try:
        current_time = datetime.now()
        logger.info(f"开始同步 - 时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取所有历史数据（一天的数据）
        data_list = fetch_recent_power_meter_data(limit=DATA_LIMIT)
        
        if data_list:
            logger.info(f"找到 {len(data_list)} 条数据，开始同步到知识库...")
            success = sync_to_kb(data_list)
            if success:
                logger.info(f"同步成功，已同步 {len(data_list)} 条数据")
            else:
                logger.warning("同步失败")
        else:
            logger.info("未找到数据，跳过本次同步")
            
    except Exception as e:
        logger.error(f"同步出错: {e}", exc_info=True)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("电表数据同步服务启动")
    logger.info(f"同步时间: 每天 {SYNC_TIME}（北京时间）")
    logger.info(f"每次同步数据量: {DATA_LIMIT} 条")
    logger.info(f"目标数据库: {MONGO_DB}")
    logger.info(f"目标知识库: namespace 'dian'")
    logger.info("=" * 60)
    
    # 检查是否需要立即执行一次同步
    now = datetime.now()
    sync_hour, sync_minute = map(int, SYNC_TIME.split(':'))
    if now.hour == sync_hour and now.minute == sync_minute:
        logger.info(f"当前时间为同步时间 {now.strftime('%H:%M')}，立即执行一次")
        sync_once()
    else:
        next_sync = datetime.now().replace(hour=sync_hour, minute=sync_minute, second=0, microsecond=0)
        if next_sync <= now:
            next_sync += timedelta(days=1)
        wait_seconds = (next_sync - now).total_seconds()
        logger.info(f"当前时间 {now.strftime('%H:%M')}，下次同步时间: {next_sync.strftime('%Y-%m-%d %H:%M')}")
    
    sync_loop()


if __name__ == "__main__":
    main()

