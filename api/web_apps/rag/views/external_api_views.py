'''
外部RAG API转发网关 - 转发到TrustRAG服务
'''
from flask import jsonify, request, current_app
from flask import Blueprint
from utils.web_utils import get_req_para, validate_params
from utils.common_utils import gen_json_response
import requests
import json
import traceback
from datetime import datetime

external_rag_bp = Blueprint('external_rag', __name__)

# TrustRAG服务配置
TRUSTRAG_BASE_URL = "http://localhost:8217"
TRUSTRAG_TIMEOUT = 30  # 30秒超时

def _make_trustrag_request(endpoint, method='POST', data=None, headers=None):
    """
    向TrustRAG服务发送请求
    """
    try:
        url = f"{TRUSTRAG_BASE_URL}{endpoint}"
        
        # 设置默认请求头
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        # 发送请求
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=TRUSTRAG_TIMEOUT)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=TRUSTRAG_TIMEOUT)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 根据端点返回不同格式
        if endpoint in ['/v1/chat/completions', '/text']:
            return response.text
        else:
            return response.json()
            
    except requests.exceptions.Timeout:
        return {"error": "请求超时", "detail": "TrustRAG服务响应超时"}
    except requests.exceptions.ConnectionError:
        return {"error": "连接失败", "detail": "无法连接到TrustRAG服务"}
    except requests.exceptions.RequestException as e:
        return {"error": "请求失败", "detail": str(e)}
    except Exception as e:
        return {"error": "未知错误", "detail": str(e)}

@external_rag_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查 - 转发到TrustRAG的/health接口
    """
    try:
        result = _make_trustrag_request('/health', method='GET')
        return gen_json_response(code=200, msg="健康检查完成", data=result)
    except Exception as e:
        return gen_json_response(code=500, msg="健康检查失败", data={"error": str(e)})

@external_rag_bp.route('/initialize', methods=['POST'])
def initialize_rag():
    """
    初始化RAG系统 - 转发到TrustRAG的/initialize接口
    """
    try:
        result = _make_trustrag_request('/initialize', method='POST')
        return gen_json_response(code=200, msg="初始化完成", data=result)
    except Exception as e:
        return gen_json_response(code=500, msg="初始化失败", data={"error": str(e)})

@external_rag_bp.route('/chat', methods=['POST'])
def chat():
    """
    简化聊天接口 - 转发到TrustRAG的/chat接口
    """
    try:
        req_dict = get_req_para()
        
        # 支持多种请求格式
        if 'message' in req_dict:
            data = {"message": req_dict['message']}
        elif 'content' in req_dict:
            data = {"message": req_dict['content']}
        elif 'messages' in req_dict:
            data = {"messages": req_dict['messages']}
        else:
            return gen_json_response(code=400, msg="请求参数错误", data={"detail": "缺少message、content或messages参数"})
        
        result = _make_trustrag_request('/chat', method='POST', data=data)
        return gen_json_response(code=200, msg="查询成功", data=result)
    except Exception as e:
        return gen_json_response(code=500, msg="查询失败", data={"error": str(e)})

@external_rag_bp.route('/text', methods=['POST'])
def text_query():
    """
    纯文本接口 - 转发到TrustRAG的/text接口
    """
    try:
        req_dict = get_req_para()
        
        if 'query' not in req_dict:
            return gen_json_response(code=400, msg="请求参数错误", data={"detail": "缺少query参数"})
        
        data = {"query": req_dict['query']}
        result = _make_trustrag_request('/text', method='POST', data=data)
        
        # 返回纯文本结果
        return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return gen_json_response(code=500, msg="查询失败", data={"error": str(e)})

@external_rag_bp.route('/v1/chat/completions', methods=['POST'])
def openai_compatible():
    """
    OpenAI兼容接口 - 转发到TrustRAG的/v1/chat/completions接口
    """
    try:
        req_dict = get_req_para()
        
        # 验证必需参数
        if 'messages' not in req_dict:
            return gen_json_response(code=400, msg="请求参数错误", data={"detail": "缺少messages参数"})
        
        # 构建OpenAI格式的请求
        data = {
            "messages": req_dict['messages'],
            "model": req_dict.get('model', 'trustrag'),
            "stream": req_dict.get('stream', False),
            "temperature": req_dict.get('temperature', 0.7),
            "max_tokens": req_dict.get('max_tokens', 1000)
        }
        
        result = _make_trustrag_request('/v1/chat/completions', method='POST', data=data)
        
        # 返回纯文本结果
        return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return gen_json_response(code=500, msg="查询失败", data={"error": str(e)})

@external_rag_bp.route('/search', methods=['POST'])
def search():
    """
    知识检索接口 - 使用TrustRAG的/chat接口进行检索
    """
    try:
        req_dict = get_req_para()
        
        if 'query' not in req_dict:
            return gen_json_response(code=400, msg="请求参数错误", data={"detail": "缺少query参数"})
        
        # 构建检索请求
        query = req_dict['query']
        top_k = req_dict.get('top_k', 5)
        threshold = req_dict.get('threshold', 0.7)
        
        # 使用chat接口进行检索
        data = {
            "message": f"请检索关于'{query}'的相关信息，返回前{top_k}个最相关的结果"
        }
        
        result = _make_trustrag_request('/chat', method='POST', data=data)
        return gen_json_response(code=200, msg="检索成功", data=result)
    except Exception as e:
        return gen_json_response(code=500, msg="检索失败", data={"error": str(e)})

@external_rag_bp.route('/search_text', methods=['POST'])
def search_text():
    """
    纯文本知识检索接口
    """
    try:
        req_dict = get_req_para()
        
        if 'query' not in req_dict:
            return gen_json_response(code=400, msg="请求参数错误", data={"detail": "缺少query参数"})
        
        # 使用text接口进行检索
        data = {"query": req_dict['query']}
        result = _make_trustrag_request('/text', method='POST', data=data)
        
        # 返回纯文本结果
        return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return gen_json_response(code=500, msg="检索失败", data={"error": str(e)})

@external_rag_bp.route('/status', methods=['GET'])
def get_status():
    """
    获取TrustRAG服务状态
    """
    try:
        # 检查健康状态
        health_result = _make_trustrag_request('/health', method='GET')
        
        status_info = {
            "service": "TrustRAG",
            "base_url": TRUSTRAG_BASE_URL,
            "timestamp": datetime.now().isoformat(),
            "health": health_result,
            "endpoints": {
                "health": f"{TRUSTRAG_BASE_URL}/health",
                "chat": f"{TRUSTRAG_BASE_URL}/chat",
                "text": f"{TRUSTRAG_BASE_URL}/text",
                "openai": f"{TRUSTRAG_BASE_URL}/v1/chat/completions",
                "initialize": f"{TRUSTRAG_BASE_URL}/initialize"
            }
        }
        
        return gen_json_response(code=200, msg="状态查询成功", data=status_info)
    except Exception as e:
        return gen_json_response(code=500, msg="状态查询失败", data={"error": str(e)})

@external_rag_bp.route('/test', methods=['POST'])
def test_connection():
    """
    测试TrustRAG连接和功能
    """
    try:
        test_results = {}
        
        # 测试健康检查
        try:
            health_result = _make_trustrag_request('/health', method='GET')
            test_results['health'] = {"status": "success", "result": health_result}
        except Exception as e:
            test_results['health'] = {"status": "failed", "error": str(e)}
        
        # 测试聊天功能
        try:
            chat_data = {"message": "测试连接"}
            chat_result = _make_trustrag_request('/chat', method='POST', data=chat_data)
            test_results['chat'] = {"status": "success", "result": chat_result}
        except Exception as e:
            test_results['chat'] = {"status": "failed", "error": str(e)}
        
        # 测试文本查询
        try:
            text_data = {"query": "测试查询"}
            text_result = _make_trustrag_request('/text', method='POST', data=text_data)
            test_results['text'] = {"status": "success", "result": text_result[:100] + "..." if len(text_result) > 100 else text_result}
        except Exception as e:
            test_results['text'] = {"status": "failed", "error": str(e)}
        
        return gen_json_response(code=200, msg="连接测试完成", data=test_results)
    except Exception as e:
        return gen_json_response(code=500, msg="连接测试失败", data={"error": str(e)})
