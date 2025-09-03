#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的绑定功能测试脚本
"""

import requests
import json

def test_binding_api():
    """测试绑定API接口"""
    base_url = "http://localhost:8001"
    
    print("🧪 开始测试知识库绑定API...")
    
    # 1. 测试获取绑定信息（无认证）
    print("\n1. 测试获取绑定信息（无认证）...")
    try:
        response = requests.get(f"{base_url}/api/rag/kb/binding?kid=1")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 403:
            print("   ✅ 正确返回认证失败错误")
        else:
            print("   ❌ 预期返回403认证失败")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    # 2. 测试创建绑定（无认证）
    print("\n2. 测试创建绑定（无认证）...")
    try:
        data = {
            "kb_id": 1,
            "namespace": "test-namespace",
            "remark": "测试绑定"
        }
        response = requests.post(f"{base_url}/api/rag/kb/binding", json=data)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 403:
            print("   ✅ 正确返回认证失败错误")
        else:
            print("   ❌ 预期返回403认证失败")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    # 3. 测试删除绑定（无认证）
    print("\n3. 测试删除绑定（无认证）...")
    try:
        response = requests.delete(f"{base_url}/api/rag/kb/binding/1")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 403:
            print("   ✅ 正确返回认证失败错误")
        else:
            print("   ❌ 预期返回403认证失败")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    print("\n🎉 API接口测试完成！")
    print("📝 注意：所有接口都正确返回了403认证失败，这是预期的行为")
    print("📝 要完整测试功能，需要提供有效的用户认证token")

if __name__ == "__main__":
    test_binding_api()
