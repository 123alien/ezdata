# -*- coding: utf-8 -*-
"""
门禁数据采集器
独立运行的门禁通行记录采集系统
"""

import os
import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import requests
from requests.adapters import HTTPAdapter, Retry
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError


# -------------------------- 门禁配置参数 --------------------------
DOOR_YARD_SN = os.getenv("DOOR_YARD_SN", "795670416473092096")
DOOR_SECRET_KEY = os.getenv("DOOR_SECRET_KEY", "92835cf352bb5ac8eb6ef8a9953aaa2d")
DOOR_BASE_URL = os.getenv("DOOR_BASE_URL", "http://openapi.andudu.net/log/door-log-list")
DOOR_INTERVAL_HOURS = int(os.getenv("DOOR_INTERVAL_HOURS", "1"))  # 门禁数据采集间隔，默认1小时
DOOR_PER_PAGE = int(os.getenv("DOOR_PER_PAGE", "100"))  # 每页记录数

# MongoDB配置（使用ezdata数据库）
DOOR_MONGO_HOST = os.getenv("DOOR_MONGO_HOST", "localhost")
DOOR_MONGO_PORT = int(os.getenv("DOOR_MONGO_PORT", "27017"))
DOOR_MONGO_USERNAME = os.getenv("DOOR_MONGO_USERNAME", "admin")
DOOR_MONGO_PASSWORD = os.getenv("DOOR_MONGO_PASSWORD", "admin123")
DOOR_MONGO_DB = os.getenv("DOOR_MONGO_DB", "ezdata")
DOOR_MONGO_AUTH_SOURCE = os.getenv("DOOR_MONGO_AUTH_SOURCE", "admin")

# 门禁数据集合
DOOR_LOG_COLL = os.getenv("DOOR_LOG_COLL", "door_access_logs")


# -------------------------- 日志配置 --------------------------
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("door_access_collector")
logger.setLevel(logging.INFO)

log_file = os.getenv("DOOR_LOG_FILE", "door_access.log")
file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
console_handler = logging.StreamHandler()
fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(fmt)
console_handler.setFormatter(fmt)
logger.handlers = [file_handler, console_handler]


# -------------------------- HTTP 会话 --------------------------
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))


def create_link_string(param_map, key):
    """创建待加密字符串"""
    if not param_map:
        return ""

    # 按key排序
    sorted_params = sorted(param_map.items())

    # 拼接字符串
    param_list = []
    for k, v in sorted_params:
        if v and k != "sign":  # 排除空值和sign参数
            param_list.append(f"{k}={v}")

    # 添加key
    param_list.append(f"key={key}")

    return "&".join(param_list)


def md5_encode(src):
    """MD5加密字符串"""
    if not src:
        return ""

    try:
        md5_hash = hashlib.md5()
        md5_hash.update(src.encode('utf-8'))
        return md5_hash.hexdigest().lower()
    except Exception as e:
        logger.error(f"MD5加密错误: {e}")
        return ""


def to_dt(time_str: Optional[str]) -> Optional[datetime]:
    """转换时间字符串为datetime对象"""
    if not time_str:
        return None
    try:
        # 支持多种时间格式
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        return None
    except (ValueError, TypeError):
        return None


def get_mongo_client() -> MongoClient:
    """获取MongoDB客户端"""
    params = {"host": DOOR_MONGO_HOST, "port": DOOR_MONGO_PORT}
    if DOOR_MONGO_USERNAME and DOOR_MONGO_PASSWORD:
        params.update(username=DOOR_MONGO_USERNAME, password=DOOR_MONGO_PASSWORD, authSource=DOOR_MONGO_AUTH_SOURCE)
    return MongoClient(**params)


def ensure_door_indexes(db):
    """确保门禁数据索引"""
    try:
        db[DOOR_LOG_COLL].create_index({"visit_time": -1})
        db[DOOR_LOG_COLL].create_index({"member_xm": 1, "visit_time": -1})
        db[DOOR_LOG_COLL].create_index({"door_name": 1, "visit_time": -1})
        db[DOOR_LOG_COLL].create_index({"created_at": -1})
    except Exception as e:
        logger.warning(f"创建门禁索引警告: {e}")


def fetch_door_logs_by_time(start_time: str, end_time: str) -> List[Dict[str, Any]]:
    """获取指定时间范围内的门禁记录"""
    all_records = []
    page = 1

    while True:
        # 构建请求参数
        params = {
            "yard_sn": DOOR_YARD_SN,
            "member_type": "1",
            "timestamp": str(int(time.time() * 1000)),
            "page": page,
            "per_page": DOOR_PER_PAGE,
            "start_time": start_time,
            "end_time": end_time
        }

        # 生成签名
        sign_string = create_link_string(params, DOOR_SECRET_KEY)
        sign = md5_encode(sign_string)
        params["sign"] = sign

        logger.info(f"获取门禁数据第 {page} 页，时间范围: {start_time} 到 {end_time}")

        try:
            # 发送POST请求
            response = session.post(
                DOOR_BASE_URL,
                json=params,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if result.get("code") != 200:
                logger.error(f"门禁数据第 {page} 页请求失败: {result.get('msg', '未知错误')}")
                break

            current_data = result.get("data", [])
            if not current_data:
                logger.info(f"门禁数据第 {page} 页无数据，获取完成")
                break

            all_records.extend(current_data)
            logger.info(f"门禁数据第 {page} 页获取成功，本页记录数: {len(current_data)}")

            if len(current_data) < DOOR_PER_PAGE:
                logger.info(f"门禁数据已获取最后一页，获取完成")
                break

            page += 1
            time.sleep(0.1)  # 避免请求过于频繁

        except Exception as e:
            logger.error(f"门禁数据第 {page} 页请求失败: {e}")
            break

    logger.info(f"门禁数据获取完成，总记录数: {len(all_records)}")
    return all_records


def persist_door_logs(logs: List[Dict[str, Any]], db) -> bool:
    """保存门禁记录到数据库"""
    if not logs:
        return True

    try:
        ops: List[UpdateOne] = []
        
        for log in logs:
            # 处理时间字段
            visit_time = to_dt(log.get('visit_time'))
            if not visit_time:
                continue

            doc = {
                "member_xm": log.get('member_xm'),
                "member_id": log.get('member_id'),
                "door_name": log.get('door_name'),
                "door_id": log.get('door_id'),
                "visit_time": visit_time,
                "remark": log.get('remark'),
                "raw_data": log,
                "created_at": datetime.now(),
            }

            # 使用visit_time作为唯一标识，避免重复插入
            filt = {
                "member_xm": doc["member_xm"],
                "door_name": doc["door_name"],
                "visit_time": doc["visit_time"],
            }
            
            ops.append(UpdateOne(
                filt, 
                {"$set": doc, "$setOnInsert": {"first_seen_at": datetime.now()}}, 
                upsert=True
            ))

        if ops:
            result = db[DOOR_LOG_COLL].bulk_write(ops, ordered=False)
            logger.info(f"门禁数据保存成功，插入/更新记录数: {result.upserted_count + result.modified_count}")
            return True
        else:
            logger.warning("没有有效的门禁记录需要保存")
            return False

    except PyMongoError as e:
        logger.error(f"门禁数据保存失败: {e}")
        return False


def collect_door_logs_once():
    """执行一次门禁数据采集"""
    # 计算时间范围（最近1小时）
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=DOOR_INTERVAL_HOURS)
    
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"开始采集门禁数据，时间范围: {start_time_str} 到 {end_time_str}")

    client = get_mongo_client()
    try:
        db = client[DOOR_MONGO_DB]
        ensure_door_indexes(db)
        
        # 获取门禁数据
        logs = fetch_door_logs_by_time(start_time_str, end_time_str)
        
        # 保存到数据库
        if logs:
            success = persist_door_logs(logs, db)
            if success:
                logger.info(f"门禁数据采集完成，处理记录数: {len(logs)}")
            else:
                logger.error("门禁数据保存失败")
        else:
            logger.info("本次采集没有新的门禁记录")
            
    finally:
        client.close()


def main():
    """主函数"""
    logger.info(f"启动门禁数据采集器，采集间隔: {DOOR_INTERVAL_HOURS}小时")
    
    # 立即执行一次
    collect_door_logs_once()
    
    # 循环执行
    while True:
        time.sleep(DOOR_INTERVAL_HOURS * 3600)  # 转换为秒
        collect_door_logs_once()


if __name__ == "__main__":
    main()
