# -*- coding: utf-8 -*-
"""
电表采集脚本
每小时整点采集一次电表数据（北京时间）
"""
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import requests
from requests.adapters import HTTPAdapter, Retry
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError


# -------------------------- 配置参数 --------------------------
BASE_URL = os.getenv("IOT_BASE_URL", "http://www.xzdiot.online:11110/hb/servlet/App")
ORG_NUM = os.getenv("IOT_ORG_NUM", "1000")

# 电表设备编号（可根据实际情况调整）
POWER_METER_DEVICES = os.getenv(
    "POWER_METER_DEVICES",
    "XZD20250731,XZD20250732,XZD20250734"  # 07室电表,08室电表,01室电表
).split(",")

# 采集时间点（24小时制）
# 已改为每分钟采集一次，不再使用定点时间
COLLECTION_TIMES = []

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "admin123")
MONGO_DB = os.getenv("MONGO_DB", "ezdata")
MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")

# 电表定点采集使用独立集合
SNAPSHOT_COLL = os.getenv("POWER_METER_SNAPSHOT_COLL", "power_meter_daily_snapshot")
FACTOR_COLL = os.getenv("POWER_METER_FACTOR_COLL", "power_meter_daily_factor_snapshot")


# -------------------------- 日志配置 --------------------------
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("power_meter_daily_collector")
logger.setLevel(logging.INFO)

log_file = os.getenv("POWER_METER_LOG_FILE", "power_meter_daily.log")
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


def to_dt(time_str: Optional[str]) -> Optional[datetime]:
    """转换时间字符串为datetime对象"""
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") if time_str else None
    except (ValueError, TypeError):
        return None


def to_float(v: Any) -> Optional[float]:
    """转换为float类型"""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


def get_mongo_client() -> MongoClient:
    """获取MongoDB客户端"""
    params = {"host": MONGO_HOST, "port": MONGO_PORT}
    if MONGO_USERNAME and MONGO_PASSWORD:
        params.update(username=MONGO_USERNAME, password=MONGO_PASSWORD, authSource=MONGO_AUTH_SOURCE)
    return MongoClient(**params)


def fetch_device_data(device_num: str) -> Optional[Dict[str, Any]]:
    """获取设备实时数据"""
    params = {"action": "actualtimeData", "orgNum": ORG_NUM, "devicenum": device_num}
    try:
        r = session.post(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json() if "json" in r.headers.get("Content-Type", "").lower() else json.loads(r.text)
        if not isinstance(data, dict) or data.get("state") != 0 or not data.get("msg"):
            logger.warning(f"设备 {device_num} 未返回有效数据")
            return None
        return data
    except Exception as e:
        logger.error(f"设备 {device_num} 请求失败: {e}")
        return None


def ensure_indexes(db):
    """确保MongoDB索引存在"""
    try:
        db[FACTOR_COLL].create_index({"device_num": 1, "factor_name": 1, "update_time": -1}, unique=True)
        db[FACTOR_COLL].create_index({"update_time": -1})
        db[SNAPSHOT_COLL].create_index({"device_num": 1, "update_time": -1})
    except Exception as e:
        logger.warning(f"创建索引警告: {e}")


def persist_one(data: Dict[str, Any], device_num: str, db) -> bool:
    """保存单条设备数据"""
    if not data or not data.get("msg"):
        return False
    rec = data["msg"][0]

    snapshot_data = {
        "device_num": rec.get("deviceNum") or rec.get("deviceNumber"),
        "device_name": rec.get("deviceName"),
        "org_num": rec.get("organizationNum"),
        "org_name": rec.get("organizationName"),
        "longitude": rec.get("longitude"),
        "latitude": rec.get("latitude"),
        "is_online": rec.get("isOnLine"),
        "address": rec.get("address"),
        "update_time": to_dt(rec.get("savetime")),
        "raw_json": data,
        "created_at": datetime.now(),
    }

    if not snapshot_data["device_num"] or not snapshot_data["update_time"]:
        return False

    try:
        snap_res = db[SNAPSHOT_COLL].insert_one(snapshot_data)
        snapshot_id = snap_res.inserted_id

        ops: List[UpdateOne] = []
        for f in rec.get("factorList", []):
            doc = {
                "snapshot_id": snapshot_id,
                "device_num": snapshot_data["device_num"],
                "factor_name": f.get("name"),
                "factor_code": f.get("code"),
                "factor_unit": f.get("factorUnit"),
                "factor_value": to_float(f.get("value")),
                "update_time": snapshot_data["update_time"],
                "created_at": datetime.now(),
            }
            if not (doc["device_num"] and doc["factor_name"] and doc["update_time"]):
                continue
            filt = {
                "device_num": doc["device_num"],
                "factor_name": doc["factor_name"],
                "update_time": doc["update_time"],
            }
            ops.append(UpdateOne(filt, {"$set": doc, "$setOnInsert": {"first_seen_at": datetime.now()}}, upsert=True))

        if ops:
            db[FACTOR_COLL].bulk_write(ops, ordered=False)
        logger.info(f"电表 {device_num} 保存成功, 快照ID: {snapshot_id}, 因子数: {len(ops)}")
        return True
    except PyMongoError as e:
        logger.error(f"电表 {device_num} 数据保存失败: {e}")
        return False


def collect_all_power_meters():
    """采集所有电表数据"""
    client = get_mongo_client()
    try:
        db = client[MONGO_DB]
        ensure_indexes(db)
        success = 0
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"开始采集电表数据 - 时间: {current_time}")
        
        for device_num in POWER_METER_DEVICES:
            device_num = device_num.strip()
            if not device_num:
                continue
            logger.info(f"正在采集电表: {device_num}")
            data = fetch_device_data(device_num)
            if data and persist_one(data, device_num, db):
                success += 1
        
        logger.info(f"电表采集完成 - 时间: {current_time}, 成功: {success}/{len(POWER_METER_DEVICES)}")
        return success
    except Exception as e:
        logger.error(f"采集过程出错: {e}", exc_info=True)
        return 0
    finally:
        client.close()


def main():
    """主函数：每小时整点采集一次（北京时间）"""
    try:
        import schedule
    except ImportError:
        logger.error("缺少 schedule 依赖，请安装: pip install schedule")
        return
    
    logger.info(f"电表定点采集服务已启动（每小时整点采集一次）")
    logger.info(f"电表设备: {POWER_METER_DEVICES}")
    logger.info(f"采集频率: 每小时整点（北京时间）")
    logger.info(f"目标数据库: {MONGO_DB}")
    logger.info("=" * 60)
    
    # 注册每小时整点的定时任务
    # schedule库使用本地时间，如果服务器是UTC，需要调整
    schedule.every().hour.at(":00").do(collect_all_power_meters)
    logger.info("已注册定时任务：每小时整点采集电表数据")
    
    # 立即执行一次（如果当前是整点）
    now = datetime.now()
    if now.minute == 0:
        logger.info(f"当前时间为整点 {now.strftime('%H:%M')}，立即执行一次")
        collect_all_power_meters()
    else:
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        wait_seconds = (next_hour - now).total_seconds()
        logger.info(f"当前时间 {now.strftime('%H:%M')}，等待到下一个整点（{next_hour.strftime('%H:%M')}）")
    
    # 主循环
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    main()

