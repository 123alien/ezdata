from flask import Blueprint, request, jsonify
from web_apps import db
from web_apps.rag.kb_models import KnowledgeBaseBinding, UserKnowledgeBase
from web_apps.rag.services.kb_service import KnowledgeBaseService
from web_apps.utils.auth import login_required, get_current_user
from web_apps.utils.common_utils import success_response, error_response

kb_binding_bp = Blueprint('kb_binding', __name__)

@kb_binding_bp.route('/binding', methods=['GET'])
@login_required
def get_binding():
    """获取知识库绑定信息"""
    try:
        kb_id = request.args.get('kid')
        if not kb_id:
            return error_response('知识库ID不能为空')
        
        current_user = get_current_user()
        kb_service = KnowledgeBaseService()
        
        # 检查权限
        kb = kb_service.get_knowledge_base_by_id(kb_id)
        if not kb:
            return error_response('知识库不存在')
        
        if not kb_service.has_permission(kb_id, current_user['id'], 'read'):
            return error_response('无权限访问此知识库')
        
        # 查询绑定信息
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if binding:
            return success_response({
                'id': binding.id,
                'kb_id': binding.kb_id,
                'namespace': binding.namespace,
                'remark': binding.remark,
                'create_time': binding.create_time.strftime('%Y-%m-%d %H:%M:%S') if binding.create_time else None
            })
        else:
            return success_response(None)
            
    except Exception as e:
        return error_response(f'获取绑定信息失败: {str(e)}')

@kb_binding_bp.route('/binding', methods=['POST'])
@login_required
def create_or_update_binding():
    """创建或更新知识库绑定"""
    try:
        data = request.get_json()
        kb_id = data.get('kb_id')
        namespace = data.get('namespace')
        remark = data.get('remark', '')
        
        if not kb_id or not namespace:
            return error_response('知识库ID和namespace不能为空')
        
        current_user = get_current_user()
        kb_service = KnowledgeBaseService()
        
        # 检查权限
        kb = kb_service.get_knowledge_base_by_id(kb_id)
        if not kb:
            return error_response('知识库不存在')
        
        if not kb_service.has_permission(kb_id, current_user['id'], 'write'):
            return error_response('无权限修改此知识库')
        
        # 检查namespace是否已被其他知识库使用
        existing_binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.namespace == namespace,
            KnowledgeBaseBinding.kb_id != kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if existing_binding:
            return error_response('该namespace已被其他知识库使用')
        
        # 查找现有绑定
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if binding:
            # 更新现有绑定
            binding.namespace = namespace
            binding.remark = remark
            binding.update_by = current_user['id']
            db.session.commit()
            message = '绑定信息更新成功'
        else:
            # 创建新绑定
            binding = KnowledgeBaseBinding(
                kb_id=kb_id,
                namespace=namespace,
                remark=remark,
                create_by=current_user['id']
            )
            db.session.add(binding)
            db.session.commit()
            message = '绑定信息创建成功'
        
        return success_response({
            'id': binding.id,
            'kb_id': binding.kb_id,
            'namespace': binding.namespace,
            'remark': binding.remark
        }, message)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'绑定操作失败: {str(e)}')

@kb_binding_bp.route('/binding/<int:kb_id>', methods=['DELETE'])
@login_required
def delete_binding(kb_id):
    """删除知识库绑定"""
    try:
        current_user = get_current_user()
        kb_service = KnowledgeBaseService()
        
        # 检查权限
        if not kb_service.has_permission(kb_id, current_user['id'], 'write'):
            return error_response('无权限修改此知识库')
        
        # 查找并删除绑定
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if not binding:
            return error_response('绑定信息不存在')
        
        binding.del_flag = 1
        binding.update_by = current_user['id']
        db.session.commit()
        
        return success_response(None, '绑定信息删除成功')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除绑定失败: {str(e)}')
