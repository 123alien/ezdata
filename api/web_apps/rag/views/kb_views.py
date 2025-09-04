from flask import Blueprint, request, jsonify
from web_apps.rag.services.kb_service import KnowledgeBaseService
from utils.auth import get_auth_token_info
from utils.web_utils import get_req_para

# 创建知识库管理蓝图
kb_bp = Blueprint('kb', __name__)

@kb_bp.route('/create', methods=['POST'])
def create_knowledge_base():
    """创建知识库"""
    try:
        params = get_req_para(request)
        name = params.get('name')
        description = params.get('description', '')
        is_public = params.get('is_public', 0)
        
        if not name:
            return jsonify({
                'code': 400,
                'data': None,
                'msg': '知识库名称不能为空'
            })
        
        # 获取当前用户
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({
                'code': 401,
                'data': None,
                'msg': '用户未登录'
            })
        
        result = KnowledgeBaseService.create_knowledge_base(
            name=name,
            description=description,
            owner_id=current_user.get('id'),
            is_public=is_public
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'msg': f'创建知识库失败: {str(e)}'
        })

@kb_bp.route('/list', methods=['GET'])
def get_knowledge_bases():
    """获取知识库列表"""
    try:
        # 获取当前用户
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({
                'code': 401,
                'data': None,
                'msg': '用户未登录'
            })
        
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        
        result = KnowledgeBaseService.get_user_knowledge_bases(
            user_id=current_user.get('id'),
            page=page,
            size=size
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'msg': f'获取知识库列表失败: {str(e)}'
        })

@kb_bp.route('/update/<kb_id>', methods=['PUT'])
def update_knowledge_base(kb_id):
    """更新知识库"""
    try:
        params = get_req_para(request)
        name = params.get('name')
        description = params.get('description')
        is_public = params.get('is_public')
        
        # 获取当前用户
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({
                'code': 401,
                'data': None,
                'msg': '用户未登录'
            })
        
        result = KnowledgeBaseService.update_knowledge_base(
            kb_id=kb_id,
            name=name,
            description=description,
            is_public=is_public,
            user_id=current_user.get('id')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'msg': f'更新知识库失败: {str(e)}'
        })

@kb_bp.route('/delete/<kb_id>', methods=['DELETE'])
def delete_knowledge_base(kb_id):
    """删除知识库"""
    try:
        # 获取当前用户
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({
                'code': 401,
                'data': None,
                'msg': '用户未登录'
            })
        
        result = KnowledgeBaseService.delete_knowledge_base(
            kb_id=kb_id,
            user_id=current_user.get('id')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'msg': f'删除知识库失败: {str(e)}'
        })

@kb_bp.route('/share', methods=['POST'])
def share_knowledge_base():
    """分享知识库"""
    try:
        params = get_req_para(request)
        kb_id = params.get('kb_id')
        shared_with_id = params.get('shared_with_id')
        permission_level = params.get('permission_level', 'read')
        
        if not kb_id or not shared_with_id:
            return jsonify({
                'code': 400,
                'data': None,
                'msg': '知识库ID和被分享用户ID不能为空'
            })
        
        # 获取当前用户
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({
                'code': 401,
                'data': None,
                'msg': '用户未登录'
            })
        
        result = KnowledgeBaseService.share_knowledge_base(
            kb_id=kb_id,
            shared_with_id=shared_with_id,
            permission_level=permission_level,
            shared_by_id=current_user.get('userId')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'msg': f'分享知识库失败: {str(e)}'
        })

@kb_bp.route('/share/list', methods=['GET'])
def get_share_list():
    """获取我分享出去的列表"""
    try:
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({'code': 401, 'data': None, 'msg': '用户未登录'})

        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        result = KnowledgeBaseService.get_share_list(shared_by_id=current_user.get('userId'), page=page, size=size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'code': 500, 'data': None, 'msg': f'获取分享列表失败: {str(e)}'})

@kb_bp.route('/share/update', methods=['POST', 'PUT'])
def update_share_permission():
    """更新分享权限"""
    try:
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({'code': 401, 'data': None, 'msg': '用户未登录'})
        params = get_req_para(request)
        share_id = params.get('share_id')
        permission_level = params.get('permission_level')
        if not share_id or not permission_level:
            return jsonify({'code': 400, 'data': None, 'msg': '参数不完整'})
        result = KnowledgeBaseService.update_share_permission(share_id=share_id, permission_level=permission_level, shared_by_id=current_user.get('userId'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'code': 500, 'data': None, 'msg': f'更新分享失败: {str(e)}'})

@kb_bp.route('/share/delete', methods=['POST', 'DELETE'])
def revoke_share():
    """撤销分享"""
    try:
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({'code': 401, 'data': None, 'msg': '用户未登录'})
        params = get_req_para(request)
        share_id = params.get('share_id')
        if not share_id:
            return jsonify({'code': 400, 'data': None, 'msg': '参数不完整'})
        result = KnowledgeBaseService.revoke_share(share_id=share_id, shared_by_id=current_user.get('userId'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'code': 500, 'data': None, 'msg': f'撤销分享失败: {str(e)}'})

@kb_bp.route('/shared/list', methods=['GET'])
def get_shared_with_me():
    """获取共享给我的列表"""
    try:
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({'code': 401, 'data': None, 'msg': '用户未登录'})
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        result = KnowledgeBaseService.get_shared_with_me(user_id=current_user.get('userId'), page=page, size=size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'code': 500, 'data': None, 'msg': f'获取失败: {str(e)}'})

@kb_bp.route('/detail/<kb_id>', methods=['GET'])
def get_knowledge_base_detail(kb_id):
    """获取知识库详情"""
    try:
        # 获取当前用户
        current_user = get_auth_token_info()
        if not current_user:
            return jsonify({
                'code': 401,
                'data': None,
                'msg': '用户未登录'
            })
        
        # 这里可以添加获取知识库详情的逻辑
        # 包括文档列表、分享信息等
        
        return jsonify({
            'code': 200,
            'data': {
                'id': kb_id,
                'message': '知识库详情功能待实现'
            },
            'msg': '获取成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'msg': f'获取知识库详情失败: {str(e)}'
        })
