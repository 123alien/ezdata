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
from sqlalchemy import and_
# 暂时注释掉，避免循环导入
# from web_apps.rag.kb_models import UserKnowledgeBase, KnowledgeBaseShare
# from web_apps import db

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

@external_rag_bp.route('/sso_token', methods=['POST'])
def generate_sso_token():
    """
    生成 SSO token 用于访问 TrustRAG 服务
    自动使用绑定的namespace（如果存在）
    """
    try:
        req_dict = get_req_para()
        dataset_id = req_dict.get('dataset_id')
        namespace = req_dict.get('namespace')
        
        if not dataset_id and not namespace:
            return gen_json_response(code=400, msg="参数错误", data={"detail": "缺少 dataset_id 或 namespace"})
        
        # 获取当前用户信息
        from utils.auth import get_auth_token_info
        user_info = get_auth_token_info()
        if not user_info:
            return gen_json_response(code=401, msg="未授权", data={"detail": "用户未登录"})
        
        user_id = user_info.get('user_id')
        tenant_id = user_info.get('tenant_id', 0)
        
        # 如果没有提供namespace，尝试从绑定表获取
        if not namespace and dataset_id:
            try:
                from web_apps.rag.kb_models import KnowledgeBaseBinding
                from web_apps import db
                
                binding = db.session.query(KnowledgeBaseBinding).filter(
                    KnowledgeBaseBinding.kb_id == dataset_id,
                    KnowledgeBaseBinding.del_flag == 0
                ).first()
                
                if binding:
                    namespace = binding.namespace
                    current_app.logger.info(f"自动使用绑定的namespace: {namespace} for kb_id: {dataset_id}")
                else:
                    return gen_json_response(code=400, msg="绑定信息不存在", data={
                        "detail": f"知识库 {dataset_id} 未绑定TrustRAG namespace，请先创建绑定"
                    })
            except Exception as e:
                current_app.logger.error(f"查询绑定信息失败: {str(e)}")
                return gen_json_response(code=500, msg="查询绑定信息失败", data={"error": str(e)})
        
        # 权限检查
        from web_apps.rag.services.kb_service import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        
        if dataset_id and not kb_service.has_permission(dataset_id, user_id, 'read'):
            return gen_json_response(code=403, msg="权限不足", data={"detail": "无权限访问此知识库"})
        
        permission_level = 'read'
        
        # 生成短期 token（10分钟有效期）
        import jwt
        from datetime import datetime, timedelta
        
        token_payload = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'dataset_id': dataset_id,
            'namespace': namespace,
            'permission_level': permission_level,
            'exp': datetime.utcnow() + timedelta(minutes=10),  # 10分钟过期
            'iat': datetime.utcnow()
        }
        
        # 使用简单的密钥（生产环境应该使用环境变量）
        secret_key = current_app.config.get('SECRET_KEY', 'ezdata-secret-key')
        token = jwt.encode(token_payload, secret_key, algorithm='HS256')
        
        return gen_json_response(code=200, msg="SSO token 生成成功", data={
            'token': token,
            'expires_in': 600,  # 10分钟
            'permission_level': permission_level,
            'dataset_id': dataset_id,
            'namespace': namespace,
        })
        
    except Exception as e:
        return gen_json_response(code=500, msg="SSO token 生成失败", data={"error": str(e)})

@external_rag_bp.route('/ask', methods=['POST'])
def ask_question():
    """
    统一提问接口 - 自动使用绑定的namespace（如果存在）
    """
    try:
        req_dict = get_req_para()
        question = req_dict.get('question')
        dataset_id = req_dict.get('dataset_id')
        namespace = req_dict.get('namespace')
        
        if not question:
            return gen_json_response(code=400, msg="参数错误", data={"detail": "缺少 question 参数"})
        
        if not dataset_id and not namespace:
            return gen_json_response(code=400, msg="参数错误", data={"detail": "缺少 dataset_id 或 namespace"})
        
        # 获取当前用户信息
        from utils.auth import get_auth_token_info
        user_info = get_auth_token_info()
        if not user_info:
            return gen_json_response(code=401, msg="未授权", data={"detail": "用户未登录"})
        
        user_id = user_info.get('user_id')
        
        # 如果没有提供namespace，尝试从绑定表获取
        if not namespace and dataset_id:
            try:
                from web_apps.rag.kb_models import KnowledgeBaseBinding
                from web_apps import db
                
                binding = db.session.query(KnowledgeBaseBinding).filter(
                    KnowledgeBaseBinding.kb_id == dataset_id,
                    KnowledgeBaseBinding.del_flag == 0
                ).first()
                
                if binding:
                    namespace = binding.namespace
                    current_app.logger.info(f"自动使用绑定的namespace: {namespace} for kb_id: {dataset_id}")
                else:
                    return gen_json_response(code=400, msg="绑定信息不存在", data={
                        "detail": f"知识库 {dataset_id} 未绑定TrustRAG namespace，请先创建绑定"
                    })
            except Exception as e:
                current_app.logger.error(f"查询绑定信息失败: {str(e)}")
                return gen_json_response(code=500, msg="查询绑定信息失败", data={"error": str(e)})
        
        # 权限检查
        from web_apps.rag.services.kb_service import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        
        if dataset_id and not kb_service.has_permission(dataset_id, user_id, 'read'):
            return gen_json_response(code=403, msg="权限不足", data={"detail": "无权限访问此知识库"})
        
        # 构建候选请求体（若提供 namespace 则一并传递）
        payloads = [
            ('/ask', { 'question': question, 'dataset_id': dataset_id, 'namespace': namespace, 'user_id': user_id }),
            ('/search_text', { 'query': question, 'dataset_id': dataset_id, 'namespace': namespace, 'user_id': user_id }),
            ('/chat', { 'message': question, 'dataset_id': dataset_id, 'namespace': namespace, 'user_id': user_id }),
            ('/text', { 'content': question, 'dataset_id': dataset_id, 'namespace': namespace, 'user_id': user_id }),
        ]
        
        last_error = None
        for endpoint, body in payloads:
            try:
                result = _make_trustrag_request(endpoint, method='POST', data=body)
                if isinstance(result, dict) and result.get('error'):
                    last_error = result
                    continue
                return gen_json_response(code=200, msg="查询成功", data={
                    'endpoint': endpoint,
                    'result': result
                })
            except Exception as e:
                last_error = {'error': str(e)}
                continue
        
        return gen_json_response(code=502, msg="TrustRAG调用失败", data=last_error or {'detail': 'unknown error'})
        
    except Exception as e:
        return gen_json_response(code=500, msg="查询失败", data={"error": str(e)})
