from flask import Blueprint, request, jsonify
from web_apps import db
from web_apps.rag.kb_models import KnowledgeBaseBinding, UserKnowledgeBase
from web_apps.rag.services.kb_service import KnowledgeBaseService
from utils.auth import validate_user, get_auth_token_info
from utils.common_utils import gen_json_response

kb_binding_bp = Blueprint('kb_binding', __name__)

# 辅助：判断当前用户是否为数据集的拥有者（兼容 create_by 记录为用户ID或用户名）
def _owns_dataset(current_user: dict, ds) -> bool:
    try:
        if ds is None:
            return False
        cu_id = str(current_user.get('userId')) if current_user else ''
        cu_name = str(current_user.get('username')) if current_user else ''
        ds_owner = str(getattr(ds, 'create_by', ''))
        # 兼容 create_by 可能为数字ID或用户名
        return ds_owner in (cu_id, cu_name)
    except Exception:
        return False

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
        # 兼容：kb_id 可为 KB 整数ID，或 Dataset(UUID)
        kb = kb_service.get_knowledge_base_by_id(kb_id)
        ds = None
        if not kb:
            # 尝试按 Dataset(UUID) 解析
            try:
                from web_apps.rag.db_models import Dataset
                ds = db.session.query(Dataset).filter(Dataset.id == kb_id, Dataset.del_flag == 0).first()
            except Exception:
                ds = None
            # 若仍无 KB，但存在 Dataset，放宽为“按 Dataset UUID 查询绑定”，权限基于 Dataset 所有权
            if not kb and not ds:
                return gen_json_response(code=404, msg='知识库不存在')
        
        # 权限：若解析出 KB，用 KB 校验；否则（仅有 Dataset）用 Dataset.create_by 与当前用户匹配
        if kb is not None:
            permitted = kb_service.has_permission(kb.id, current_user.get('userId'), 'read')
        else:
            permitted = _owns_dataset(current_user, ds)
        if not permitted:
            return gen_json_response(code=403, msg='无权限访问此知识库')
        
        # 兼容按 dataset(UUID) 绑定或按 KB 主键绑定
        is_uuid_like = isinstance(kb_id, str) and len(kb_id) >= 32
        store_kb_id = kb_id if is_uuid_like else (kb.id if kb else kb_id)

        # 查询绑定信息（按实际落库的 kb_id 查询）
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == store_kb_id,
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
        # 兼容：kb_id 可为 KB 整数ID，或 Dataset(UUID)
        kb = kb_service.get_knowledge_base_by_id(kb_id)
        ds = None
        if not kb:
            try:
                from web_apps.rag.db_models import Dataset
                ds = db.session.query(Dataset).filter(Dataset.id == kb_id, Dataset.del_flag == 0).first()
            except Exception:
                ds = None
            if not kb and not ds:
                return gen_json_response(code=404, msg='知识库不存在')
        
        if kb is not None:
            permitted = kb_service.has_permission(kb.id, current_user.get('userId'), 'write')
        else:
            permitted = _owns_dataset(current_user, ds)
        if not permitted:
            return gen_json_response(code=403, msg='无权限修改此知识库')
        
        # 绑定粒度：优先以 dataset(UUID) 为唯一键，避免同一用户不同数据集产生误判
        from re import fullmatch
        is_uuid_like = isinstance(kb_id, str) and len(kb_id) >= 32
        store_kb_id = kb_id if is_uuid_like else (kb.id if kb else kb_id)

        # 检查namespace是否已被其他知识库使用（仅检查有效记录）
        existing_binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.namespace == namespace,
            KnowledgeBaseBinding.kb_id != store_kb_id,
            KnowledgeBaseBinding.del_flag == 0
        ).first()
        
        if existing_binding:
            return gen_json_response(code=400, msg='该namespace已被其他知识库使用')
        
        # 查找是否已经存在该 KB/dataset 的绑定（包含已软删除的记录，避免唯一键冲突）
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == store_kb_id
        ).first()
        
        if binding:
            # 更新已有记录（若之前被软删则恢复）
            binding.namespace = namespace
            binding.remark = remark
            binding.update_by = current_user.get('username')
            binding.del_flag = 0
            db.session.commit()
            message = '绑定信息更新成功'
        else:
            # 创建新绑定
            binding = KnowledgeBaseBinding(
                kb_id=store_kb_id,
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

@kb_binding_bp.route('/binding/<kb_id>', methods=['DELETE'])
@validate_user
def delete_binding(kb_id):
    """删除知识库绑定"""
    try:
        current_user = get_auth_token_info()
        if not current_user:
            return gen_json_response(code=401, msg='用户未登录')
        
        kb_service = KnowledgeBaseService()

        # 将传入的 kb_id 兼容为“真实的 KB 主键ID”
        resolved_kb = kb_service.get_knowledge_base_by_id(kb_id)
        ds = None
        if not resolved_kb:
            try:
                from web_apps.rag.db_models import Dataset
                ds = db.session.query(Dataset).filter(Dataset.id == kb_id, Dataset.del_flag == 0).first()
            except Exception:
                ds = None
            if not resolved_kb and not ds:
                return gen_json_response(code=404, msg='知识库不存在')

        # 权限校验基于真实 KB
        if resolved_kb is not None:
            permitted = kb_service.has_permission(resolved_kb.id, current_user.get('userId'), 'write')
        else:
            permitted = _owns_dataset(current_user, ds)
        if not permitted:
            return gen_json_response(code=403, msg='无权限修改此知识库')

        # 与创建/查询保持一致：若传入的是 dataset(UUID) 则按 UUID 存/查/删
        is_uuid_like = isinstance(kb_id, str) and len(kb_id) >= 32
        store_kb_id = kb_id if is_uuid_like else (resolved_kb.id if resolved_kb else kb_id)

        # 查找并删除绑定（按实际落库的 kb_id 查询）
        binding = db.session.query(KnowledgeBaseBinding).filter(
            KnowledgeBaseBinding.kb_id == store_kb_id,
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
