#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrustRAG API 客户端示例
通过EZDATA后端转发网关访问TrustRAG服务
"""

import requests
import json
from typing import Dict, Any, Optional

class TrustRAGClient:
    """TrustRAG API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        初始化客户端
        
        Args:
            base_url: EZDATA后端服务地址
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TrustRAG-Client/1.0'
        })
    
    def _make_request(self, endpoint: str, method: str = 'POST', data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            endpoint: API端点
            method: HTTP方法
            data: 请求数据
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}/api/external/rag{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=30)
            else:
                response = self.session.post(url, json=data, timeout=30)
            
            response.raise_for_status()
            
            # 处理纯文本响应
            if response.headers.get('content-type', '').startswith('text/plain'):
                return {"text": response.text}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"请求失败: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析失败: {str(e)}"}
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        return self._make_request('/health', method='GET')
    
    def initialize(self) -> Dict[str, Any]:
        """
        初始化RAG系统
        
        Returns:
            初始化结果
        """
        return self._make_request('/initialize', method='POST')
    
    def chat(self, message: str) -> Dict[str, Any]:
        """
        聊天接口
        
        Args:
            message: 用户消息
            
        Returns:
            聊天响应
        """
        data = {"message": message}
        return self._make_request('/chat', method='POST', data=data)
    
    def text_query(self, query: str) -> str:
        """
        纯文本查询
        
        Args:
            query: 查询内容
            
        Returns:
            纯文本响应
        """
        data = {"query": query}
        result = self._make_request('/text', method='POST', data=data)
        return result.get('text', '') if isinstance(result, dict) else str(result)
    
    def openai_chat(self, messages: list, model: str = 'trustrag', 
                   temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        OpenAI兼容接口
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            纯文本响应
        """
        data = {
            "messages": messages,
            "model": model,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        result = self._make_request('/v1/chat/completions', method='POST', data=data)
        return result.get('text', '') if isinstance(result, dict) else str(result)
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.7) -> Dict[str, Any]:
        """
        知识检索
        
        Args:
            query: 检索查询
            top_k: 返回结果数量
            threshold: 相似度阈值
            
        Returns:
            检索结果
        """
        data = {
            "query": query,
            "top_k": top_k,
            "threshold": threshold
        }
        return self._make_request('/search', method='POST', data=data)
    
    def search_text(self, query: str) -> str:
        """
        纯文本知识检索
        
        Args:
            query: 检索查询
            
        Returns:
            纯文本检索结果
        """
        data = {"query": query}
        result = self._make_request('/search_text', method='POST', data=data)
        return result.get('text', '') if isinstance(result, dict) else str(result)
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            状态信息
        """
        return self._make_request('/status', method='GET')
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试连接
        
        Returns:
            测试结果
        """
        return self._make_request('/test', method='POST')

def main():
    """使用示例"""
    # 创建客户端
    client = TrustRAGClient()
    
    print("=== TrustRAG API 客户端测试 ===\n")
    
    # 1. 健康检查
    print("1. 健康检查:")
    health = client.health_check()
    print(json.dumps(health, ensure_ascii=False, indent=2))
    print()
    
    # 2. 获取状态
    print("2. 服务状态:")
    status = client.get_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    print()
    
    # 3. 测试连接
    print("3. 连接测试:")
    test = client.test_connection()
    print(json.dumps(test, ensure_ascii=False, indent=2))
    print()
    
    # 4. 聊天测试
    print("4. 聊天测试:")
    chat_result = client.chat("汽车保养需要注意什么？")
    print(json.dumps(chat_result, ensure_ascii=False, indent=2))
    print()
    
    # 5. 文本查询测试
    print("5. 文本查询测试:")
    text_result = client.text_query("如何更换机油？")
    print(text_result)
    print()
    
    # 6. 知识检索测试
    print("6. 知识检索测试:")
    search_result = client.search("轮胎保养", top_k=3)
    print(json.dumps(search_result, ensure_ascii=False, indent=2))
    print()
    
    # 7. OpenAI兼容接口测试
    print("7. OpenAI兼容接口测试:")
    messages = [
        {"role": "user", "content": "汽车日常维护有哪些要点？"}
    ]
    openai_result = client.openai_chat(messages)
    print(openai_result)
    print()

if __name__ == "__main__":
    main()
