from flask import Blueprint, request, jsonify
from web_apps import db
from web_apps.rag.kb_models import KnowledgeBaseBinding, UserKnowledgeBase
from web_apps.rag.services.kb_service import KnowledgeBaseService
from utils.auth import validate_user, get_auth_token_info
from utils.common_utils import gen_json_response

kb_binding_bp = Blueprint('kb_binding', __name__)

@kb_binding_bp.route('/binding', methods=['GET'])
@validate_user
def get_binding():
    """获取知识库绑定信息"""
    try:
        kb_id = request.args.get('kid')
        if not kb_id:
            return gen_json_response(code=400, msg='知识库ID不能为空')
        
        current_user = get_auth_token_info()
        if not current_user:
            return gen_json_response(code=401, msg='用户未登录')
        
        kb_service = KnowledgeBaseService()
        
        # 检查权限
        kb = kb_service.get_knowledge_base_by_id(kb_id)
        if not kb:
            return gen_json_response(code=404, msg='知识库不存在')
        
        if not kb_service.has_permission(kb_id, current_user.get('userId'), 'read'):
            return gen_json_response(code=403, msg='无权限访问此知识库')
        
        # 查询绑定信息
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if binding:
            return gen_json_response(code=200, msg='获取成功', data={
                'id': binding.id,
                'kb_id': binding.kb_id,
                'namespace': binding.namespace,
                'remark': binding.remark,
                'create_time': binding.create_time.strftime('%Y-%m-%d %H:%M:%S') if binding.create_time else None
            })
        else:
            return gen_json_response(code=200, msg='获取成功', data=None)
            
    except Exception as e:
        return gen_json_response(code=500, msg=f'获取绑定信息失败: {str(e)}')

@kb_binding_bp.route('/binding', methods=['POST'])
@validate_user
def create_or_update_binding():
    """创建或更新知识库绑定"""
    try:
        data = request.get_json()
        kb_id = data.get('kb_id')
        namespace = data.get('namespace')
        remark = data.get('remark', '')
        
        if not kb_id or not namespace:
            return gen_json_response(code=400, msg='知识库ID和namespace不能为空')
        
        current_user = get_auth_token_info()
        if not current_user:
            return gen_json_response(code=401, msg='用户未登录')
        
        kb_service = KnowledgeBaseService()
        
        # 检查权限
        kb = kb_service.get_knowledge_base_by_id(kb_id)
        if not kb:
            return gen_json_response(code=404, msg='知识库不存在')
        
        if not kb_service.has_permission(kb_id, current_user.get('userId'), 'write'):
            return gen_json_response(code=403, msg='无权限修改此知识库')
        
        # 检查namespace是否已被其他知识库使用
        existing_binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.namespace == namespace,
            KnowledgeBaseBinding.kb_id != kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if existing_binding:
            return gen_json_response(code=400, msg='该namespace已被其他知识库使用')
        
        # 查找现有绑定
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if binding:
            # 更新现有绑定
            binding.namespace = namespace
            binding.remark = remark
            binding.update_by = current_user.get('username')
            db.session.commit()
            message = '绑定信息更新成功'
        else:
            # 创建新绑定
            binding = KnowledgeBaseBinding(
                kb_id=kb_id,
                namespace=namespace,
                remark=remark,
                create_by=current_user.get('username')
            )
            db.session.add(binding)
            db.session.commit()
            message = '绑定信息创建成功'
        
        return gen_json_response(code=200, msg=message, data={
            'id': binding.id,
            'kb_id': binding.kb_id,
            'namespace': binding.namespace,
            'remark': binding.remark
        })
        
    except Exception as e:
        db.session.rollback()
        return gen_json_response(code=500, msg=f'绑定操作失败: {str(e)}')

@kb_binding_bp.route('/binding/<int:kb_id>', methods=['DELETE'])
@validate_user
def delete_binding(kb_id):
    """删除知识库绑定"""
    try:
        current_user = get_auth_token_info()
        if not current_user:
            return gen_json_response(code=401, msg='用户未登录')
        
        kb_service = KnowledgeBaseService()
        
        # 检查权限
        if not kb_service.has_permission(kb_id, current_user.get('userId'), 'write'):
            return gen_json_response(code=403, msg='无权限修改此知识库')
        
        # 查找并删除绑定
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if not binding:
            return gen_json_response(code=404, msg='绑定信息不存在')
        
        binding.del_flag = 1
        binding.update_by = current_user.get('username')
        db.session.commit()
        
        return gen_json_response(code=200, msg='绑定信息删除成功')
        
    except Exception as e:
        db.session.rollback()
        return gen_json_response(code=500, msg=f'删除绑定失败: {str(e)}')
