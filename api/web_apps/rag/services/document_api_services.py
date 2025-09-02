'''
文档管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.rag.db_models import Document, Dataset
from web_apps.rag.kb_models import KnowledgeBaseShare
from tasks.data_tasks import self_train_rag_data

    
def serialize_document_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'dataset_id', 'document_type', 'name', 'meta_data', 'chunk_strategy', 'status', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description']:
            if k in ['meta_data', 'chunk_strategy']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['meta_data', 'chunk_strategy']:
            dic[k] = json.loads(dic[k])
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'name']:
            if k in ['meta_data', 'chunk_strategy']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
        
    return dic

    
class DocumentApiService(object):
    def __init__(self):
        pass
        
    @staticmethod
    def _has_dataset_permission(user_info, dataset_id, need_level: str) -> bool:
        """检查用户对数据集的权限。need_level: 'read'|'write'|'admin'"""
        if not user_info:
            return False
        # owner 优先
        is_owned = db.session.query(Dataset).filter(
            Dataset.id == dataset_id, Dataset.create_by == user_info.get('username'), Dataset.del_flag == 0
        ).first() is not None
        if is_owned:
            return True
        # 分享权限等级
        level_map = {'read': 1, 'write': 2, 'admin': 3}
        required = level_map.get(need_level, 1)
        share = db.session.query(KnowledgeBaseShare).filter(
            KnowledgeBaseShare.kb_id == dataset_id,
            KnowledgeBaseShare.shared_with_id == str(user_info.get('id')),
            KnowledgeBaseShare.status == 1,
            KnowledgeBaseShare.del_flag == 0
        ).first()
        if not share:
            return False
        current = level_map.get(share.permission_level or 'read', 1)
        return current >= required

    @staticmethod
    def get_obj_list(req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(Document)

        # 基于数据集的可见性做权限约束：仅本人创建的数据集或被分享的数据集
        user_info = get_auth_token_info()
        if user_info:
            # 允许：本人创建的数据集
            own_dataset_ids = [i.id for i in db.session.query(Dataset).filter(
                Dataset.create_by == user_info.get('username'), Dataset.del_flag == 0
            ).all()]
            # 允许：分享给我的数据集
            shared_dataset_ids = [i.kb_id for i in db.session.query(KnowledgeBaseShare).filter(
                KnowledgeBaseShare.shared_with_id == str(user_info.get('id')),
                KnowledgeBaseShare.status == 1, KnowledgeBaseShare.del_flag == 0
            ).all()]
            allow_dataset_ids = list(set(own_dataset_ids + shared_dataset_ids))
            if allow_dataset_ids:
                query = query.filter(Document.dataset_id.in_(allow_dataset_ids))
            else:
                # 无权限可见任何文档
                query = query.filter(Document.id == None)
        
        # 名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(Document.name.like("%" + name + "%"))

        # 文档类型 查询逻辑
        document_type = req_dict.get('document_type', '')
        if document_type != '':
            query = query.filter(Document.document_type == document_type)

        # 所属数据集 查询逻辑
        dataset_id = req_dict.get('dataset_id', '')
        if dataset_id != '':
            # 额外校验 dataset_id 是否在可见范围
            if user_info:
                if not DocumentApiService._has_dataset_permission(user_info, dataset_id, 'read'):
                    return gen_json_response(code=403, msg='无权限查看该数据集文档')
            query = query.filter(Document.dataset_id == dataset_id)

        # 状态 查询逻辑
        status = req_dict.get('status', '')
        if status != '':
            query = query.filter(Document.status == status)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_document_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    
    @staticmethod
    def get_obj_all_list(req_dict):
        '''
        获取全量列表
        '''
        query = get_base_query(Document)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_document_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    @staticmethod
    def get_obj_detail(req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Document).filter(
            Document.id == obj_id,
            Document.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        # 权限校验：仅本人或被分享的数据集下的文档可见
        user_info = get_auth_token_info()
        if user_info and not DocumentApiService._has_dataset_permission(user_info, obj.dataset_id, 'read'):
            return gen_json_response(code=403, msg='无权限访问该文档')
        dic = serialize_document_model(obj, ser_type='detail')
        return gen_json_response(data=dic)

    @staticmethod
    def train_obj(req_dict):
        '''
        训练知识库
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Document).filter(Document.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        # 训练文档
        user_info = get_auth_token_info()
        # 直接调用训练函数，绕过Celery避免EntryPoints问题
        from web_apps.rag.services.rag_service import train_document
        try:
            # 设置用户信息到metadata中
            metadata = {'user_name': user_info['username']}
            train_document(obj.id, metadata=metadata)
            return gen_json_response(msg='训练任务已启动', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'训练任务启动失败: {str(e)}', extends={'success': False})

    @staticmethod
    def add_obj(req_dict):
        '''
        添加
        '''
        
        # 权限：仅本人数据集可新增（共享只读/读写策略可在此拓展）
        user_info = get_auth_token_info()
        dataset_id = req_dict.get('dataset_id')
        if user_info and dataset_id:
            # 需要 write 权限
            if not DocumentApiService._has_dataset_permission(user_info, dataset_id, 'write'):
                return gen_json_response(code=403, msg='无权限在该数据集下新增文档')

        obj = Document()
        for key in req_dict:
            if key in ['meta_data', 'chunk_strategy']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        # 训练文档
        user_info = get_auth_token_info()
        # 直接调用训练函数，绕过Celery避免EntryPoints问题
        from web_apps.rag.services.rag_service import train_document
        try:
            train_document(obj.id, metadata={'user_name': user_info['username']})
            return gen_json_response(msg='添加成功', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'添加成功但训练任务启动失败: {str(e)}', extends={'success': True})
    
    @staticmethod
    def edit_obj(req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        
        obj = db.session.query(Document).filter(Document.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        # 权限：需要 write
        user_info = get_auth_token_info()
        if user_info and not DocumentApiService._has_dataset_permission(user_info, obj.dataset_id, 'write'):
            return gen_json_response(code=403, msg='无权限编辑该文档')
        for key in req_dict:
            if key in ['meta_data', 'chunk_strategy']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    @staticmethod
    def delete_obj(req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(Document).filter(Document.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        # 权限：需要 write
        user_info = get_auth_token_info()
        if user_info and not DocumentApiService._has_dataset_permission(user_info, del_obj.dataset_id, 'write'):
            return gen_json_response(code=403, msg='无权限删除该文档')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    @staticmethod
    def delete_batch(req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(Document).filter(Document.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
