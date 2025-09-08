from web_apps.rag.kb_models import UserKnowledgeBase, KnowledgeBaseDocument, KnowledgeBaseShare
from web_apps.rag.db_models import Dataset
from web_apps import db
from utils.common_utils import gen_uuid
from sqlalchemy import and_, or_
from typing import List, Dict, Optional
import json
import logging
from models import User

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    
    @staticmethod
    def create_knowledge_base(name: str, description: str, owner_id: str, is_public: int = 0) -> Dict:
        """创建知识库"""
        try:
            kb = UserKnowledgeBase(
                name=name,
                description=description,
                owner_id=owner_id,
                is_public=is_public,
                status=1
            )
            db.session.add(kb)
            db.session.commit()
            
            return {
                'code': 200,
                'data': {
                    'id': kb.id,
                    'name': kb.name,
                    'description': kb.description,
                    'owner_id': kb.owner_id,
                    'is_public': kb.is_public,
                    'status': kb.status
                },
                'msg': '知识库创建成功'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'code': 500,
                'data': None,
                'msg': f'知识库创建失败: {str(e)}'
            }

    @staticmethod
    def get_knowledge_base_by_id(kb_id: str) -> Optional[UserKnowledgeBase]:
        """根据 KB 整型ID 或 Dataset(UUID) 定位到 UserKnowledgeBase。仅查询，不自动创建。"""
        # KB 数字ID
        if isinstance(kb_id, (int,)) or (isinstance(kb_id, str) and kb_id.isdigit()):
            kb = db.session.query(UserKnowledgeBase).filter(
                UserKnowledgeBase.id == int(kb_id),
                UserKnowledgeBase.del_flag == 0,
            ).first()
            return kb
        # Dataset UUID → 名称+创建者 映射到 KB
        if isinstance(kb_id, str) and len(kb_id) >= 32:
            dataset = db.session.query(Dataset).filter(
                Dataset.id == kb_id,
                Dataset.del_flag == 0,
            ).first()
            if not dataset:
                return None
            kb = db.session.query(UserKnowledgeBase).filter(
                UserKnowledgeBase.name == dataset.name,
                UserKnowledgeBase.owner_id == dataset.create_by,
                UserKnowledgeBase.del_flag == 0,
            ).first()
            return kb
        return None

    @staticmethod
    def has_permission(kb_id: str, user_id: str, need_level: str = 'read') -> bool:
        """校验用户在 KB 上的权限。need_level: read|write|admin
        - owner 拥有 admin
        - 分享表按 permission_level 判定
        """
        kb = KnowledgeBaseService.get_knowledge_base_by_id(kb_id)
        if not kb:
            return False
        # 将 user_id(数字) 转为 username
        username = None
        try:
            uid = int(user_id) if isinstance(user_id, (int, str)) and str(user_id).isdigit() else None
            if uid is not None:
                u = db.session.query(User).filter(User.id == uid).first()
                username = u.username if u else None
        except Exception:
            username = None
        # 所有者
        if username and kb.owner_id == username:
            return True if need_level in ['read', 'write', 'admin'] else False
        # 分享
        level_map = {'read': 1, 'write': 2, 'admin': 3}
        required = level_map.get(need_level, 1)
        share = db.session.query(KnowledgeBaseShare).filter(
            KnowledgeBaseShare.kb_id == kb.id,
            KnowledgeBaseShare.shared_with_id == str(user_id),
            KnowledgeBaseShare.status == 1,
            KnowledgeBaseShare.del_flag == 0,
        ).first()
        if not share:
            return False
        current = level_map.get((share.permission_level or 'read'), 1)
        return current >= required
    
    @staticmethod
    def get_user_knowledge_bases(user_id: str, page: int = 1, size: int = 10) -> Dict:
        """获取用户的知识库列表"""
        try:
            # 获取用户拥有的知识库
            owned_kbs = db.session.query(UserKnowledgeBase).filter(
                and_(
                    UserKnowledgeBase.owner_id == user_id,
                    UserKnowledgeBase.del_flag == 0
                )
            ).all()
            
            # 获取分享给用户的知识库
            shared_kbs = db.session.query(UserKnowledgeBase).join(
                KnowledgeBaseShare,
                UserKnowledgeBase.id == KnowledgeBaseShare.kb_id
            ).filter(
                and_(
                    KnowledgeBaseShare.shared_with_id == user_id,
                    KnowledgeBaseShare.status == 1,
                    UserKnowledgeBase.del_flag == 0
                )
            ).all()
            
            # 合并结果
            all_kbs = list(set(owned_kbs + shared_kbs))
            
            # 分页
            start = (page - 1) * size
            end = start + size
            paged_kbs = all_kbs[start:end]
            
            result = []
            for kb in paged_kbs:
                # 判断权限
                is_owner = kb.owner_id == user_id
                permission = 'admin' if is_owner else 'read'  # 简化处理
                
                result.append({
                    'id': kb.id,
                    'name': kb.name,
                    'description': kb.description,
                    'owner_id': kb.owner_id,
                    'is_public': kb.is_public,
                    'status': kb.status,
                    'permission': permission,
                    'is_owner': is_owner,
                    'create_time': kb.create_time.strftime('%Y-%m-%d %H:%M:%S') if kb.create_time else None
                })
            
            return {
                'code': 200,
                'data': {
                    'records': result,
                    'total': len(all_kbs),
                    'page': page,
                    'size': size
                },
                'msg': '获取成功'
            }
        except Exception as e:
            return {
                'code': 500,
                'data': None,
                'msg': f'获取知识库列表失败: {str(e)}'
            }
    
    @staticmethod
    def update_knowledge_base(kb_id: str, name: str = None, description: str = None, 
                            is_public: int = None, user_id: str = None) -> Dict:
        """更新知识库"""
        try:
            kb = db.session.query(UserKnowledgeBase).filter(
                and_(
                    UserKnowledgeBase.id == kb_id,
                    UserKnowledgeBase.del_flag == 0
                )
            ).first()
            
            if not kb:
                return {
                    'code': 404,
                    'data': None,
                    'msg': '知识库不存在'
                }
            
            # 检查权限
            if str(kb.owner_id) != str(user_id):
                return {
                    'code': 403,
                    'data': None,
                    'msg': '无权限修改此知识库'
                }
            
            # 更新字段
            if name is not None:
                kb.name = name
            if description is not None:
                kb.description = description
            if is_public is not None:
                kb.is_public = is_public
            
            db.session.commit()
            
            return {
                'code': 200,
                'data': {
                    'id': kb.id,
                    'name': kb.name,
                    'description': kb.description,
                    'is_public': kb.is_public
                },
                'msg': '知识库更新成功'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'code': 500,
                'data': None,
                'msg': f'知识库更新失败: {str(e)}'
            }
    
    @staticmethod
    def delete_knowledge_base(kb_id: str, user_id: str) -> Dict:
        """删除知识库"""
        try:
            kb = db.session.query(UserKnowledgeBase).filter(
                and_(
                    UserKnowledgeBase.id == kb_id,
                    UserKnowledgeBase.del_flag == 0
                )
            ).first()
            
            if not kb:
                return {
                    'code': 404,
                    'data': None,
                    'msg': '知识库不存在'
                }
            
            # 检查权限
            if kb.owner_id != user_id:
                return {
                    'code': 403,
                    'data': None,
                    'msg': '无权限删除此知识库'
                }
            
            # 软删除知识库
            kb.del_flag = 1
            
            # 同时将相关分享记录标记为失效
            shares = db.session.query(KnowledgeBaseShare).filter(
                and_(
                    KnowledgeBaseShare.kb_id == kb_id,
                    KnowledgeBaseShare.del_flag == 0
                )
            ).all()
            
            for share in shares:
                share.status = 0  # 标记分享为失效
                share.del_flag = 1  # 软删除分享记录
            
            db.session.commit()
            
            return {
                'code': 200,
                'data': None,
                'msg': f'知识库删除成功，同时失效了 {len(shares)} 个分享记录'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'code': 500,
                'data': None,
                'msg': f'知识库删除失败: {str(e)}'
            }
    
    @staticmethod
    def share_knowledge_base(kb_id: str, shared_with_id: str, permission_level: str, 
                           shared_by_id: str) -> Dict:
        """分享知识库 - 兼容 UUID（旧Dataset）和整数ID（新UserKnowledgeBase）"""
        try:
            logger.info(f"分享知识库请求: kb_id={kb_id}, shared_by_id={shared_by_id}, shared_with_id={shared_with_id}")
            
            # 兼容性处理：支持 UUID 和整数 ID
            kb = None
            
            # 1. 先尝试作为整数 ID 查询（新流程）
            if kb_id.isdigit():
                logger.info(f"尝试作为整数ID查询: {kb_id}")
                
                # 获取用户名：如果shared_by_id是用户ID，需要转换为用户名
                owner_username = shared_by_id
                if isinstance(shared_by_id, (int, str)) and str(shared_by_id).isdigit():
                    from models import User
                    user = db.session.query(User).filter(User.id == int(shared_by_id)).first()
                    if user:
                        owner_username = user.username
                        logger.info(f"用户ID {shared_by_id} 转换为用户名: {owner_username}")
                
                kb = db.session.query(UserKnowledgeBase).filter(
                    and_(
                        UserKnowledgeBase.id == int(kb_id),
                        UserKnowledgeBase.owner_id == owner_username,
                        UserKnowledgeBase.del_flag == 0
                    )
                ).first()
                logger.info(f"整数ID查询结果: {kb is not None}")
            
            # 2. 如果没找到，尝试作为 UUID 查询（旧流程）
            if not kb and len(kb_id) >= 32:  # UUID 长度（可能是32或36位）
                logger.info(f"尝试作为UUID查询: {kb_id}")
                from web_apps.rag.db_models import Dataset
                # 通过 Dataset UUID 找到对应的 UserKnowledgeBase
                # 获取用户名：如果shared_by_id是用户ID，需要转换为用户名
                owner_username = shared_by_id
                if isinstance(shared_by_id, (int, str)) and str(shared_by_id).isdigit():
                    from models import User
                    user = db.session.query(User).filter(User.id == int(shared_by_id)).first()
                    if user:
                        owner_username = user.username
                        logger.info(f"用户ID {shared_by_id} 转换为用户名: {owner_username}")
                
                dataset = db.session.query(Dataset).filter(
                    and_(
                        Dataset.id == kb_id,
                        Dataset.create_by == owner_username,
                        Dataset.del_flag == 0
                    )
                ).first()
                logger.info(f"Dataset查询结果: {dataset is not None}")
                
                if dataset:
                    logger.info(f"Dataset信息: name={dataset.name}, create_by={dataset.create_by}")
                    # 获取用户名：如果shared_by_id是用户ID，需要转换为用户名
                    owner_username = shared_by_id
                    if isinstance(shared_by_id, (int, str)) and str(shared_by_id).isdigit():
                        from models import User
                        user = db.session.query(User).filter(User.id == int(shared_by_id)).first()
                        if user:
                            owner_username = user.username
                            logger.info(f"用户ID {shared_by_id} 转换为用户名: {owner_username}")
                    
                    # 查找是否有对应的 UserKnowledgeBase（通过名称匹配）
                    kb = db.session.query(UserKnowledgeBase).filter(
                        and_(
                            UserKnowledgeBase.name == dataset.name,
                            UserKnowledgeBase.owner_id == owner_username,
                            UserKnowledgeBase.del_flag == 0
                        )
                    ).first()
                    logger.info(f"UserKnowledgeBase查询结果: {kb is not None}")
                    
                    # 如果没找到，自动创建一个对应的 UserKnowledgeBase
                    if not kb:
                        logger.info(f"自动创建UserKnowledgeBase for Dataset {dataset.id}")
                        kb = UserKnowledgeBase(
                            name=dataset.name,
                            description=dataset.name,  # 使用名称作为描述
                            owner_id=owner_username,  # 使用用户名作为owner
                            is_public=0,
                            status=1
                        )
                        db.session.add(kb)
                        db.session.commit()
                        db.session.flush()
                        logger.info(f"自动创建UserKnowledgeBase成功: {kb.id} for Dataset {dataset.id}")
            
            # 3. 如果还没找到，尝试通过Dataset ID查找（处理整数ID但UserKnowledgeBase不存在的情况）
                        if not kb:
                            logger.info(f"尝试通过Dataset ID查找: {kb_id}")
                            from web_apps.rag.db_models import Dataset
                            
                            # 获取用户名：如果shared_by_id是用户ID，需要转换为用户名
                            owner_username = shared_by_id
                            if isinstance(shared_by_id, (int, str)) and str(shared_by_id).isdigit():
                                from models import User
                                user = db.session.query(User).filter(User.id == int(shared_by_id)).first()
                                if user:
                                    owner_username = user.username
                                    logger.info(f"用户ID {shared_by_id} 转换为用户名: {owner_username}")
                            
                            dataset = db.session.query(Dataset).filter(
                                and_(
                                    Dataset.id == kb_id,
                                    Dataset.create_by == owner_username,
                        Dataset.del_flag == 0
                    )
                ).first()
                logger.info(f"Dataset查询结果: {dataset is not None}")
                
                if dataset:
                    logger.info(f"Dataset信息: name={dataset.name}, create_by={dataset.create_by}")
                    # 获取用户名：如果shared_by_id是用户ID，需要转换为用户名
                    owner_username = shared_by_id
                    if isinstance(shared_by_id, (int, str)) and str(shared_by_id).isdigit():
                        from models import User
                        user = db.session.query(User).filter(User.id == int(shared_by_id)).first()
                        if user:
                            owner_username = user.username
                            logger.info(f"用户ID {shared_by_id} 转换为用户名: {owner_username}")
                    
                    # 查找是否有对应的 UserKnowledgeBase（通过名称匹配）
                    kb = db.session.query(UserKnowledgeBase).filter(
                        and_(
                            UserKnowledgeBase.name == dataset.name,
                            UserKnowledgeBase.owner_id == owner_username,
                            UserKnowledgeBase.del_flag == 0
                        )
                    ).first()
                    logger.info(f"UserKnowledgeBase查询结果: {kb is not None}")
                    
                    # 如果没找到，自动创建一个对应的 UserKnowledgeBase
                    if not kb:
                        logger.info(f"自动创建UserKnowledgeBase for Dataset {dataset.id}")
                        kb = UserKnowledgeBase(
                            name=dataset.name,
                            description=dataset.name,  # 使用名称作为描述
                            owner_id=owner_username,  # 使用用户名作为owner
                            is_public=0,
                            status=1
                        )
                        db.session.add(kb)
                        db.session.commit()
                        db.session.flush()
                        logger.info(f"自动创建UserKnowledgeBase成功: {kb.id} for Dataset {dataset.id}")
            
            if not kb:
                logger.error(f"未找到知识库: kb_id={kb_id}, shared_by_id={shared_by_id}")
                return {
                    'code': 404,
                    'data': None,
                    'msg': '知识库不存在或无权限'
                }
            
            # 检查是否已经分享过（使用找到的 kb.id）
            # 注意：不检查del_flag，因为需要处理已删除的记录
            existing_share = db.session.query(KnowledgeBaseShare).filter(
                and_(
                    KnowledgeBaseShare.kb_id == kb.id,
                    KnowledgeBaseShare.shared_with_id == shared_with_id
                )
            ).first()
            
            if existing_share:
                # 更新现有分享
                logger.info(f"更新现有分享记录: ID={existing_share.id}, del_flag={existing_share.del_flag} -> 0, status={existing_share.status} -> 1")
                existing_share.permission_level = permission_level
                existing_share.status = 1
                existing_share.del_flag = 0  # 恢复删除标记
            else:
                # 创建新分享（使用找到的 kb.id）
                share = KnowledgeBaseShare(
                    kb_id=kb.id,
                    shared_by_id=shared_by_id,
                    shared_with_id=shared_with_id,
                    permission_level=permission_level,
                    status=1
                )
                db.session.add(share)
            
            db.session.commit()
            
            return {
                'code': 200,
                'data': None,
                'msg': '知识库分享成功'
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"分享知识库异常: {str(e)}", exc_info=True)
            return {
                'code': 500,
                'data': None,
                'msg': f'知识库分享失败: {str(e)}'
            }

    @staticmethod
    def get_share_list(shared_by_id: str, page: int = 1, size: int = 10) -> Dict:
        """获取我分享出去的知识库列表"""
        try:
            query = db.session.query(KnowledgeBaseShare, UserKnowledgeBase, User).join(
                UserKnowledgeBase, KnowledgeBaseShare.kb_id == UserKnowledgeBase.id
            ).join(
                User, KnowledgeBaseShare.shared_with_id == User.id
            ).filter(
                and_(
                    KnowledgeBaseShare.shared_by_id == shared_by_id,
                    KnowledgeBaseShare.del_flag == 0
                )
            ).order_by(KnowledgeBaseShare.create_time.desc())

            total = query.count()
            start = (page - 1) * size
            items = query.offset(start).limit(size).all()

            records = []
            for share, kb, shared_user in items:
                records.append({
                    'id': share.id,
                    'kb_id': kb.id,
                    'kb_name': kb.name,
                    'shared_with_id': share.shared_with_id,
                    'shared_with_name': shared_user.nickname or shared_user.username,
                    'permission_level': share.permission_level,
                    'status': share.status,
                    'create_time': share.create_time.strftime('%Y-%m-%d %H:%M:%S') if share.create_time else None,
                })

            return {
                'code': 200,
                'data': {
                    'records': records,
                    'total': total,
                    'page': page,
                    'size': size,
                },
                'msg': '获取成功'
            }
        except Exception as e:
            return {
                'code': 500,
                'data': None,
                'msg': f'获取分享列表失败: {str(e)}'
            }

    @staticmethod
    def update_share_permission(share_id: str, permission_level: str, shared_by_id: str) -> Dict:
        """更新分享权限"""
        try:
            share = db.session.query(KnowledgeBaseShare).filter(
                and_(
                    KnowledgeBaseShare.id == share_id,
                    KnowledgeBaseShare.del_flag == 0
                )
            ).first()
            if not share:
                return {'code': 404, 'data': None, 'msg': '分享记录不存在'}

            # 权限校验：只能由分享者修改
            if str(share.shared_by_id) != str(shared_by_id):
                return {'code': 403, 'data': None, 'msg': '无权限修改此分享'}

            share.permission_level = permission_level
            db.session.commit()
            return {'code': 200, 'data': None, 'msg': '权限更新成功'}
        except Exception as e:
            db.session.rollback()
            return {'code': 500, 'data': None, 'msg': f'更新失败: {str(e)}'}

    @staticmethod
    def revoke_share(share_id: str, shared_by_id: str) -> Dict:
        """撤销分享（软删除或置为失效）"""
        try:
            share = db.session.query(KnowledgeBaseShare).filter(
                and_(
                    KnowledgeBaseShare.id == share_id,
                    KnowledgeBaseShare.del_flag == 0
                )
            ).first()
            if not share:
                return {'code': 404, 'data': None, 'msg': '分享记录不存在'}

            if str(share.shared_by_id) != str(shared_by_id):
                return {'code': 403, 'data': None, 'msg': '无权限撤销此分享'}

            share.status = 0
            share.del_flag = 1
            db.session.commit()
            return {'code': 200, 'data': None, 'msg': '已撤销分享'}
        except Exception as e:
            db.session.rollback()
            return {'code': 500, 'data': None, 'msg': f'撤销失败: {str(e)}'}

    @staticmethod
    def get_shared_with_me(user_id: str, page: int = 1, size: int = 10) -> Dict:
        """获取共享给我的知识库列表"""
        try:
            # 先查询分享记录
            shares = db.session.query(KnowledgeBaseShare).filter(
                and_(
                    KnowledgeBaseShare.shared_with_id == user_id,
                    KnowledgeBaseShare.status == 1,
                    KnowledgeBaseShare.del_flag == 0,
                )
            ).order_by(KnowledgeBaseShare.create_time.desc()).all()
            
            records = []
            for share in shares:
                # 查找对应的知识库
                kb = db.session.query(UserKnowledgeBase).filter(
                    and_(
                        UserKnowledgeBase.id == share.kb_id,
                        UserKnowledgeBase.del_flag == 0
                    )
                ).first()
                
                if not kb:
                    continue
                
                # 查找分享者信息
                shared_by_user = None
                if share.shared_by_id.isdigit():
                    # 如果是数字，按用户ID查找
                    shared_by_user = db.session.query(User).filter(User.id == int(share.shared_by_id)).first()
                else:
                    # 如果是字符串，按用户名查找
                    shared_by_user = db.session.query(User).filter(User.username == share.shared_by_id).first()
                
                if shared_by_user:
                    # 查找对应的Dataset ID
                    dataset = db.session.query(Dataset).filter(
                        Dataset.name == kb.name,
                        Dataset.create_by == kb.owner_id,
                        Dataset.del_flag == 0
                    ).first()
                    
                    records.append({
                        'id': share.id,
                        'kb_id': kb.id,
                        'kb_name': kb.name,
                        'dataset_id': dataset.id if dataset else None,  # 添加Dataset ID
                        'shared_by_id': share.shared_by_id,
                        'shared_by_name': shared_by_user.nickname or shared_by_user.username,
                        'permission_level': share.permission_level,
                        'create_time': share.create_time.strftime('%Y-%m-%d %H:%M:%S') if share.create_time else None,
                    })
            
            # 分页处理
            total = len(records)
            start = (page - 1) * size
            end = start + size
            paginated_records = records[start:end]

            return {
                'code': 200,
                'data': {
                    'records': paginated_records,
                    'total': total,
                    'page': page,
                    'size': size,
                },
                'msg': '获取成功'
            }
        except Exception as e:
            return {'code': 500, 'data': None, 'msg': f'获取失败: {str(e)}'}
