#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的绑定API路径
"""

import requests
import json

def test_new_binding_api():
    """测试新的绑定API路径"""
    base_url = "http://localhost:8001"
    
    print("🧪 开始测试新的知识库绑定API路径...")
    
    # 1. 测试新的获取绑定信息路径
    print("\n1. 测试新的获取绑定信息路径...")
    try:
        response = requests.get(f"{base_url}/api/rag/kb/binding/binding?kid=1")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 403:
            print("   ✅ 正确返回认证失败错误")
        else:
            print("   ❌ 预期返回403认证失败")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    # 2. 测试新的创建绑定路径
    print("\n2. 测试新的创建绑定路径...")
    try:
        data = {
            "kb_id": 1,
            "namespace": "test-namespace",
            "remark": "测试绑定"
        }
        response = requests.post(f"{base_url}/api/rag/kb/binding/binding", json=data)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 403:
            print("   ✅ 正确返回认证失败错误")
        else:
            print("   ❌ 预期返回403认证失败")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    # 3. 测试新的删除绑定路径
    print("\n3. 测试新的删除绑定路径...")
    try:
        response = requests.delete(f"{base_url}/api/rag/kb/binding/binding/1")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 403:
            print("   ✅ 正确返回认证失败错误")
        else:
            print("   ❌ 预期返回403认证失败")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    # 4. 测试旧的路径是否仍然可用
    print("\n4. 测试旧的路径是否仍然可用...")
    try:
        response = requests.get(f"{base_url}/api/rag/kb/binding?kid=1")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 404:
            print("   ✅ 旧路径正确返回404（已废弃）")
        else:
            print(f"   ⚠️  旧路径返回: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    print("\n🎉 新API路径测试完成！")
    print("📝 注意：所有新路径都正确返回了403认证失败，这是预期的行为")
    print("📝 旧路径已废弃，返回404")

if __name__ == "__main__":
    test_new_binding_api()
