#!/usr/bin/env python3
"""
手动触发文档同步到 TrustRAG
"""
import sys
import os
sys.path.append('/home/dfi/Desktop/ezdata-master/api')

from web_apps import app
from web_apps.rag.services.trustrag_sync_service import bulk_sync_dataset

def main():
    with app.test_request_context():
        dataset_id = "13bbb803053d42eaa335940a16e19c81"
        print(f"开始同步数据集: {dataset_id}")
        
        result = bulk_sync_dataset(dataset_id)
        print(f"同步结果: {result}")
        
        if result.get('success'):
            print(f"成功同步 {result.get('success_count')}/{result.get('total')} 个文档")
        else:
            print(f"同步失败: {result.get('message')}")

if __name__ == "__main__":
    main()
