# -*- coding: utf-8 -*-
"""
门禁数据同步到知识库
每天将门禁数据同步到"门禁"知识库（更新同一文档）
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
from web_apps.rag.db_models import Dataset
from utils.common_utils import gen_uuid
from pymongo import MongoClient

# MongoDB配置
MONGO_HOST = os.getenv("DOOR_MONGO_HOST", os.getenv("MONGO_HOST", "localhost"))
MONGO_PORT = int(os.getenv("DOOR_MONGO_PORT", os.getenv("MONGO_PORT", "27017")))
MONGO_USERNAME = os.getenv("DOOR_MONGO_USERNAME", os.getenv("MONGO_USERNAME", "admin"))
MONGO_PASSWORD = os.getenv("DOOR_MONGO_PASSWORD", os.getenv("MONGO_PASSWORD", "admin123"))
MONGO_DB = os.getenv("DOOR_MONGO_DB", os.getenv("MONGO_DB", "ezdata"))
MONGO_AUTH_SOURCE = os.getenv("DOOR_MONGO_AUTH_SOURCE", os.getenv("MONGO_AUTH_SOURCE", "admin"))

# 集合名称
DOOR_LOG_COLL = os.getenv("DOOR_LOG_COLL", "door_access_logs")

# 同步配置
SYNC_TIME = os.getenv("DOOR_SYNC_TIME", "02:30")  # 默认每天凌晨2:30同步
DATA_LIMIT = int(os.getenv("DOOR_SYNC_DATA_LIMIT", "0"))  # 0表示同步所有数据
MAX_DOC_SIZE = int(os.getenv("DOOR_MAX_DOC_SIZE", "80000"))  # 单个文档最大字符数（约8万字符），超过后创建新文档

# 日志配置
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("door_access_kb_sync")
logger.setLevel(logging.INFO)

log_file = os.getenv("DOOR_SYNC_LOG_FILE", "door_access_kb_sync.log")
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


def fetch_door_access_data(limit: int = 0) -> List[Dict[str, Any]]:
    """从MongoDB获取门禁数据
    limit=0 表示获取所有数据
    """
    client = get_mongo_client()
    try:
        db_mongo = client[MONGO_DB]
        
        # 获取门禁记录，按时间倒序
        if limit > 0:
            logs = list(db_mongo[DOOR_LOG_COLL].find().sort("visit_time", -1).limit(limit))
        else:
            # 获取所有数据
            logs = list(db_mongo[DOOR_LOG_COLL].find().sort("visit_time", -1))
        
        data_list = []
        for log in logs:
            data_list.append({
                "member_xm": log.get("member_xm", ""),
                "member_id": log.get("member_id", ""),
                "door_name": log.get("door_name", ""),
                "door_id": log.get("door_id", ""),
                "visit_time": log.get("visit_time").strftime("%Y-%m-%d %H:%M:%S") if log.get("visit_time") else "",
                "remark": log.get("remark", "")
            })
        
        return data_list
    finally:
        client.close()


def format_data_as_text(data_list: List[Dict[str, Any]]) -> str:
    """将门禁数据格式化为文本，包含统计信息"""
    if not data_list:
        return "暂无门禁数据"
    
    lines = ["门禁通行数据汇总报告", "=" * 60]
    lines.append(f"数据记录数: {len(data_list)}")
    lines.append(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # 按日期分组
    daily_data = {}
    for item in data_list:
        time_str = item.get('visit_time', '')
        if not time_str:
            continue
        try:
            record_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            date_key = record_time.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(item)
        except:
            continue
    
    # 按日期分组统计
    lines.append("【每日通行统计】")
    if daily_data:
        for date_key in sorted(daily_data.keys(), reverse=True):
            day_records = daily_data[date_key]
            
            # 统计信息
            total_count = len(day_records)
            unique_members = len(set(r.get('member_xm', '') for r in day_records if r.get('member_xm')))
            unique_doors = len(set(r.get('door_name', '') for r in day_records if r.get('door_name')))
            
            # 按人员统计
            member_count = {}
            for r in day_records:
                member = r.get('member_xm', '未知')
                if member:
                    member_count[member] = member_count.get(member, 0) + 1
            
            # 按门禁统计
            door_count = {}
            for r in day_records:
                door = r.get('door_name', '未知')
                if door:
                    door_count[door] = door_count.get(door, 0) + 1
            
            lines.append(f"\n日期: {date_key}")
            lines.append(f"  总通行次数: {total_count}")
            lines.append(f"  通行人员数: {unique_members}")
            lines.append(f"  使用门禁数: {unique_doors}")
            lines.append("")
            
            # 人员通行排行（前10名）
            if member_count:
                lines.append(f"  人员通行排行（前10名）:")
                sorted_members = sorted(member_count.items(), key=lambda x: x[1], reverse=True)[:10]
                for member, count in sorted_members:
                    lines.append(f"    {member}: {count}次")
                lines.append("")
            
            # 门禁使用排行
            if door_count:
                lines.append(f"  门禁使用统计:")
                sorted_doors = sorted(door_count.items(), key=lambda x: x[1], reverse=True)
                for door, count in sorted_doors:
                    lines.append(f"    {door}: {count}次")
                lines.append("")
            
            # 显示最近的通行记录（前20条）
            lines.append(f"  最近通行记录（前20条）:")
            sorted_day_records = sorted(day_records, key=lambda x: x.get('visit_time', ''), reverse=True)
            for record in sorted_day_records[:20]:
                member = record.get('member_xm', '未知')
                door = record.get('door_name', '未知')
                time_str = record.get('visit_time', '')
                remark = record.get('remark', '')
                lines.append(f"    {time_str} - {member} 通过 {door}" + (f" ({remark})" if remark else ""))
            lines.append("")
    else:
        lines.append("暂无按日期分组的数据")
    
    # 添加查询说明
    lines.append("=" * 60)
    lines.append("【查询说明】")
    lines.append("1. 可以查询：'某人在某一天的通行记录'，例如：'张三在2025-10-31的通行记录'")
    lines.append("2. 可以查询：'某人在某天的通行次数'，例如：'李四在2025-10-31通行了几次'")
    lines.append("3. 可以查询：'某门禁在某天的使用情况'，例如：'主入口在2025-10-31的通行记录'")
    lines.append("4. 可以查询：'某天总共有多少人通行'，例如：'2025-10-31有多少人通行'")
    lines.append("5. 可以查询：'某天哪个门禁使用最多'，例如：'2025-10-31哪个门禁使用最频繁'")
    lines.append("")
    lines.append("【查询示例】")
    lines.append("- '张三在2025年10月31日的通行记录'")
    lines.append("- '李四今天通行了几次？'")
    lines.append("- '主入口在2025-10-31的通行情况'")
    lines.append("- '昨天有多少人通行？'")
    lines.append("- '哪个门禁使用最频繁？'")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def ensure_kb_binding():
    """确保门禁知识库和namespace绑定存在（使用已存在的绑定）"""
    with app.app_context():
        try:
            namespace = "men"
            
            # 首先查找已存在的绑定
            existing_binding = db.session.query(KnowledgeBaseBinding).filter(
                KnowledgeBaseBinding.namespace == namespace,
                KnowledgeBaseBinding.del_flag == 0
            ).first()
            
            if existing_binding:
                dataset_id = existing_binding.kb_id
                dataset = db.session.query(Dataset).filter(Dataset.id == dataset_id).first()
                logger.info(f"找到已存在的绑定: namespace '{namespace}' -> 知识库 '{dataset.name if dataset else dataset_id}' (ID: {dataset_id})")
                return dataset_id
            
            # 如果不存在，查找或创建知识库
            kb_name = "门禁数据"
            existing_kb = db.session.query(Dataset).filter(
                Dataset.name == kb_name,
                Dataset.del_flag == 0
            ).first()
            
            if existing_kb:
                dataset_id = existing_kb.id
                logger.info(f"找到已存在的知识库: {kb_name} (ID: {dataset_id})")
            else:
                dataset = Dataset(
                    id=gen_uuid(res_type='base'),
                    name=kb_name,
                    built_in=0,
                    status=1,
                    create_by='admin',
                    create_time=datetime.now()
                )
                db.session.add(dataset)
                db.session.commit()
                dataset_id = dataset.id
                logger.info(f"创建知识库成功: {kb_name} (ID: {dataset_id})")
            
            # 创建绑定
            binding = KnowledgeBaseBinding(
                kb_id=dataset_id,
                namespace=namespace,
                remark="门禁数据知识库",
                create_by='admin',
                create_time=datetime.now()
            )
            db.session.add(binding)
            db.session.commit()
            logger.info(f"绑定创建成功: 绑定到 namespace {namespace}")
            return dataset_id
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"确保知识库绑定失败: {e}")
            import traceback
            traceback.print_exc()
            return None


def split_data_by_date_and_size(data_list: List[Dict[str, Any]], max_size: int) -> List[tuple]:
    """按日期范围和文档大小分割数据
    返回: [(日期范围字符串, [数据列表]), ...]
    例如: [("2025-10-01至2025-10-15", [数据]), ("2025-10-16至2025-10-31", [数据])]
    """
    if not data_list:
        return []
    
    # 按日期分组
    daily_groups = {}
    for item in data_list:
        time_str = item.get('visit_time', '')
        if not time_str:
            continue
        try:
            record_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            date_key = record_time.strftime("%Y-%m-%d")
            if date_key not in daily_groups:
                daily_groups[date_key] = []
            daily_groups[date_key].append(item)
        except:
            continue
    
    if not daily_groups:
        return [("全部数据", data_list)]
    
    # 按日期排序
    sorted_dates = sorted(daily_groups.keys())
    
    # 合并日期范围，确保每个范围的数据不超过max_size
    result = []
    current_range_start = None
    current_range_end = None
    current_chunk = []
    
    for date_key in sorted_dates:
        day_data = daily_groups[date_key]
        
        # 测试添加当天数据后是否超过限制
        test_chunk = current_chunk + day_data
        test_content = format_data_as_text(test_chunk)
        
        if len(test_content) > max_size and current_chunk:
            # 当前范围已满，保存并开始新范围
            range_str = f"{current_range_start}至{current_range_end}" if current_range_start == current_range_end else f"{current_range_start}至{current_range_end}"
            result.append((range_str, current_chunk))
            
            # 开始新范围
            current_range_start = date_key
            current_range_end = date_key
            current_chunk = day_data
        else:
            # 继续当前范围
            if current_range_start is None:
                current_range_start = date_key
            current_range_end = date_key
            current_chunk = test_chunk
    
    # 添加最后一个范围
    if current_chunk:
        range_str = f"{current_range_start}至{current_range_end}" if current_range_start == current_range_end else f"{current_range_start}至{current_range_end}"
        result.append((range_str, current_chunk))
    
    return result


def sync_to_kb(data_list: List[Dict[str, Any]]) -> bool:
    """将门禁数据同步到知识库（自动分文档）"""
    with app.app_context():
        try:
            # 1. 确保知识库和绑定存在
            dataset_id = ensure_kb_binding()
            if not dataset_id:
                logger.warning("无法获取知识库ID")
                return False
            
            # 2. 获取所有历史数据
            all_data = fetch_door_access_data(limit=DATA_LIMIT)
            if not all_data:
                logger.warning("未找到数据")
                return False
            
            logger.info(f"准备同步 {len(all_data)} 条数据")
            
            # 3. 按日期范围和大小分割数据
            date_chunks = split_data_by_date_and_size(all_data, MAX_DOC_SIZE)
            logger.info(f"数据已分割为 {len(date_chunks)} 个文档块（按日期范围）")
            
            # 4. 为每个chunk创建或更新文档
            success_count = 0
            for idx, (date_range, chunk) in enumerate(date_chunks):
                # 格式化chunk数据
                content = format_data_as_text(chunk)
                actual_size = len(content)
                
                # 文档名称：包含日期范围，便于RAG检索
                doc_name = f"门禁通行数据-{date_range}"
                
                # 查找或创建文档
                existing_doc = db.session.query(Document).filter(
                    Document.dataset_id == dataset_id,
                    Document.name == doc_name,
                    Document.del_flag == 0
                ).first()
                
                if existing_doc:
                    doc_id = existing_doc.id
                    logger.info(f"更新文档 {idx+1}/{len(date_chunks)}: {doc_name} (大小: {actual_size} 字符)")
                else:
                    doc_id = gen_uuid(res_type='base')
                    logger.info(f"创建文档 {idx+1}/{len(date_chunks)}: {doc_name} (大小: {actual_size} 字符)")
                
                # 创建临时文本文件
                temp_file_path = f"/tmp/door_access_data_{doc_id}.txt"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                if existing_doc:
                    # 更新现有文档
                    meta_data = json.loads(existing_doc.meta_data) if existing_doc.meta_data else {}
                    meta_data.update({
                        "upload_file": temp_file_path,
                        "source": "door_access_mongodb_realtime",
                        "data_count": len(chunk),
                        "document_size": actual_size,
                        "chunk_index": idx,
                        "last_updated": datetime.now().isoformat(),
                        "update_count": meta_data.get("update_count", 0) + 1
                    })
                    existing_doc.meta_data = json.dumps(meta_data, ensure_ascii=False)
                    existing_doc.update_time = datetime.now()
                    existing_doc.status = 1
                    db.session.commit()
                    db.session.flush()
                else:
                    # 创建新文档
                    document = Document(
                        id=doc_id,
                        dataset_id=dataset_id,
                        document_type="upload_file",
                        name=doc_name,
                        status=1,
                        meta_data=json.dumps({
                            "upload_file": temp_file_path,
                            "source": "door_access_mongodb_realtime",
                            "data_count": len(chunk),
                            "document_size": actual_size,
                            "chunk_index": idx,
                            "created_at": datetime.now().isoformat(),
                            "update_count": 1
                        }, ensure_ascii=False),
                        create_by="admin",
                        create_time=datetime.now()
                    )
                    db.session.add(document)
                    db.session.commit()
                    db.session.flush()
                
                # 5. 同步到TrustRAG
                try:
                    from web_apps.rag.services.trustrag_sync_service import _resolve_namespace_by_dataset, _generate_sso_token, _build_minio_file_url
                    import requests
                    
                    namespace = _resolve_namespace_by_dataset(dataset_id)
                    if namespace:
                        raw_text = None
                        if os.path.exists(temp_file_path):
                            try:
                                with open(temp_file_path, 'r', encoding='utf-8') as f:
                                    raw_text = f.read()
                            except Exception:
                                pass
                        
                        user_id = ""
                        tenant_id = 1
                        token = _generate_sso_token(user_id, tenant_id, dataset_id, namespace)
                        
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
                            logger.info(f"文档 {idx+1}/{len(date_chunks)} 同步到TrustRAG成功")
                            success_count += 1
                        else:
                            logger.warning(f"文档 {idx+1}/{len(date_chunks)} 同步到TrustRAG失败: {resp.status_code}")
                    else:
                        logger.warning("未找到namespace绑定")
                except Exception as e:
                    logger.error(f"文档 {idx+1}/{len(date_chunks)} 同步到TrustRAG失败: {e}")
            
            logger.info(f"同步完成: {success_count}/{len(date_chunks)} 个文档成功")
            return success_count > 0
            
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
    logger.info(f"已注册定时任务：每天 {SYNC_TIME} 同步门禁数据到知识库")
    
    # 主循环
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


def sync_once():
    """执行一次同步"""
    try:
        current_time = datetime.now()
        logger.info(f"开始同步 - 时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取所有历史数据（limit=0表示获取所有）
        data_list = fetch_door_access_data(limit=DATA_LIMIT)
        
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
    logger.info("门禁数据同步服务启动")
    logger.info(f"同步时间: 每天 {SYNC_TIME}（北京时间）")
    if DATA_LIMIT > 0:
        logger.info(f"每次同步数据量: 最多 {DATA_LIMIT} 条")
    else:
        logger.info(f"每次同步数据量: 所有历史数据")
    logger.info(f"单个文档最大大小: {MAX_DOC_SIZE} 字符（超过后自动创建新文档）")
    logger.info(f"目标数据库: {MONGO_DB}")
    logger.info(f"目标知识库: namespace 'men'")
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

