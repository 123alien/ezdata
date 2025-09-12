#!/usr/bin/env python3
"""
测试文档同步到 TrustRAG 的功能
"""
import os
import sys
import requests
import json

# 添加项目路径
sys.path.append('/home/dfi/Desktop/ezdata-master/api')

def test_document_sync():
    """测试文档同步功能"""
    
    # 1. 创建一个测试文档
    test_doc_path = "/tmp/test_carbon_finance.txt"
    with open(test_doc_path, 'w', encoding='utf-8') as f:
        f.write("""
碳金融是指与碳排放权交易、碳减排项目融资、碳资产管理等相关的金融服务。

碳金融的主要内容包括：
1. 碳交易：包括碳排放权交易、碳配额交易等
2. 碳基金：专门投资于碳减排项目的基金
3. 碳债券：为碳减排项目融资的债券产品
4. 碳保险：为碳减排项目提供风险保障的保险产品

碳金融的发展意义：
- 推动绿色低碳发展
- 促进经济结构转型升级
- 支持碳达峰、碳中和目标实现
- 创新金融服务模式

碳金融在中国的发展现状：
中国已建立全国碳排放权交易市场，覆盖电力、钢铁、建材、有色、石化、化工、造纸、航空等重点行业。
        """)
    
    print(f"✓ 创建测试文档: {test_doc_path}")
    
    # 2. 模拟文档同步
    try:
        from web_apps.rag.services.trustrag_sync_service import sync_created_document
        
        # 模拟 meta_data
        meta_data = {
            "upload_file": test_doc_path
        }
        
        # 调用同步函数
        result = sync_created_document("9efa3da0ac9a48138f052f62834f3eec", meta_data)
        print(f"同步结果: {result}")
        
        if result.get("success"):
            print("✓ 文档同步成功！")
        else:
            print(f"✗ 文档同步失败: {result.get('message')}")
            
    except Exception as e:
        print(f"✗ 同步异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 测试 TrustRAG 问答
    try:
        import jwt
        import time
        
        # 生成 token
        payload = {
            'user_id': 'admin',
            'tenant_id': 0,
            'dataset_id': '9efa3da0ac9a48138f052f62834f3eec',
            'namespace': 'ezdata-admin-test',
            'permission_level': 'read',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time())
        }
        token = jwt.encode(payload, 'erwqefdscweer)qi', algorithm='HS256')
        
        # 测试问答
        response = requests.post(
            "http://localhost:8217/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json={
                "message": "什么是碳金融",
                "namespace": "ezdata-admin-test"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ TrustRAG 回答: {result.get('response', '无回答')}")
        else:
            print(f"✗ TrustRAG 请求失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"✗ 问答测试异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理测试文件
    try:
        os.remove(test_doc_path)
        print("✓ 清理测试文件")
    except:
        pass

if __name__ == "__main__":
    test_document_sync()
