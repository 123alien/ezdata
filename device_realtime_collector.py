# -*- coding: utf-8 -*-
import os
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
from requests.adapters import HTTPAdapter, Retry
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError


# -------------------------- 配置参数 --------------------------
BASE_URL = os.getenv("IOT_BASE_URL", "http://www.xzdiot.online:11110/hb/servlet/App")
ORG_NUM = os.getenv("IOT_ORG_NUM", "1000")
DEVICES = os.getenv("IOT_DEVICES", "WIFI2025062501,WIFI2025062502,WIFI2025062503,XZD20250731,XZD20250732").split(",")
INTERVAL_SECONDS = int(os.getenv("IOT_INTERVAL_SECONDS", "60"))  # 采集间隔，默认60秒
CRON_TIMES = os.getenv("IOT_CRON_TIMES", "").strip()  # 逗号分隔，如 "08:00,20:00"

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DB = os.getenv("MONGO_DB", "ezdata")
MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")

SNAPSHOT_COLL = os.getenv("SNAPSHOT_COLL", "env_device_snapshot")
FACTOR_COLL = os.getenv("FACTOR_COLL", "env_device_factor_snapshot")


# -------------------------- 日志配置 --------------------------
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("device_realtime_collector")
logger.setLevel(logging.INFO)

log_file = os.getenv("IOT_LOG_FILE", "device_data.log")
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
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") if time_str else None
    except (ValueError, TypeError):
        return None


def to_float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


def get_mongo_client() -> MongoClient:
    params = {"host": MONGO_HOST, "port": MONGO_PORT}
    if MONGO_USERNAME and MONGO_PASSWORD:
        params.update(username=MONGO_USERNAME, password=MONGO_PASSWORD, authSource=MONGO_AUTH_SOURCE)
    return MongoClient(**params)


def fetch_device_data(device_num: str) -> Optional[Dict[str, Any]]:
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
    try:
        db[FACTOR_COLL].create_index({"device_num": 1, "factor_name": 1, "update_time": -1}, unique=True)
        db[FACTOR_COLL].create_index({"update_time": -1})
        db[SNAPSHOT_COLL].create_index({"device_num": 1, "update_time": -1})
    except Exception as e:
        logger.warning(f"创建索引警告: {e}")


def persist_one(data: Dict[str, Any], device_num: str, db) -> bool:
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
        "update_time": to_dt(rec.get("updatetime")),
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
        logger.info(f"设备 {device_num} 保存成功, 快照ID: {snapshot_id}, 因子数: {len(ops)}")
        return True
    except PyMongoError as e:
        logger.error(f"设备 {device_num} 数据保存失败: {e}")
        return False


def collect_once():
    client = get_mongo_client()
    try:
        db = client[MONGO_DB]
        ensure_indexes(db)
        success = 0
        for device in DEVICES:
            data = fetch_device_data(device)
            if data and persist_one(data, device, db):
                success += 1
        logger.info(f"本轮完成，成功 {success}/{len(DEVICES)} 台设备")
    finally:
        client.close()


def main():
    if CRON_TIMES:
        try:
            import schedule  # 按需导入，避免在仅调用 collect_once 时缺依赖
        except ImportError:
            logger.error("缺少 schedule 依赖，回退为间隔模式运行。pip install schedule 可启用定时计划")
            CRON_TIMES_LOCAL = None
            pass
        else:
            CRON_TIMES_LOCAL = CRON_TIMES
        if not CRON_TIMES_LOCAL:
            logger.info(f"启动采集：设备={len(DEVICES)}，间隔={INTERVAL_SECONDS}s，目标库={MONGO_DB}")
            collect_once()
            while True:
                time.sleep(INTERVAL_SECONDS)
                collect_once()
            return
        times = [t.strip() for t in CRON_TIMES.split(',') if t.strip()]
        for t in times:
            try:
                schedule.every().day.at(t).do(collect_once)
                logger.info(f"已注册定时任务：每天 {t} 采集一次")
            except Exception as e:
                logger.error(f"注册定时任务失败 {t}: {e}")
        logger.info(f"启动采集（按固定时间）：设备={len(DEVICES)}，时间点={times}，目标库={MONGO_DB}")
        # 立即执行一次以确认配置
        collect_once()
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        logger.info(f"启动采集：设备={len(DEVICES)}，间隔={INTERVAL_SECONDS}s，目标库={MONGO_DB}")
        collect_once()  # 启动即跑
        while True:
            time.sleep(INTERVAL_SECONDS)
            collect_once()


if __name__ == "__main__":
    main()


