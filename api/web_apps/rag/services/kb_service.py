from web_apps.rag.kb_models import UserKnowledgeBase, KnowledgeBaseDocument, KnowledgeBaseShare
from web_apps import db
from utils.common_utils import gen_uuid
from sqlalchemy import and_, or_
from typing import List, Dict, Optional
import json
from models import User

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
            
            # 软删除
            kb.del_flag = 1
            db.session.commit()
            
            return {
                'code': 200,
                'data': None,
                'msg': '知识库删除成功'
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
        """分享知识库"""
        try:
            # 检查知识库是否存在且用户有权限
            kb = db.session.query(UserKnowledgeBase).filter(
                and_(
                    UserKnowledgeBase.id == kb_id,
                    UserKnowledgeBase.owner_id == shared_by_id,
                    UserKnowledgeBase.del_flag == 0
                )
            ).first()
            
            if not kb:
                return {
                    'code': 404,
                    'data': None,
                    'msg': '知识库不存在或无权限'
                }
            
            # 检查是否已经分享过
            existing_share = db.session.query(KnowledgeBaseShare).filter(
                and_(
                    KnowledgeBaseShare.kb_id == kb_id,
                    KnowledgeBaseShare.shared_with_id == shared_with_id,
                    KnowledgeBaseShare.del_flag == 0
                )
            ).first()
            
            if existing_share:
                # 更新现有分享
                existing_share.permission_level = permission_level
                existing_share.status = 1
            else:
                # 创建新分享
                share = KnowledgeBaseShare(
                    kb_id=kb_id,
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
            query = db.session.query(KnowledgeBaseShare, UserKnowledgeBase, User).join(
                UserKnowledgeBase, KnowledgeBaseShare.kb_id == UserKnowledgeBase.id
            ).join(
                User, KnowledgeBaseShare.shared_by_id == User.id
            ).filter(
                and_(
                    KnowledgeBaseShare.shared_with_id == user_id,
                    KnowledgeBaseShare.status == 1,
                    KnowledgeBaseShare.del_flag == 0,
                    UserKnowledgeBase.del_flag == 0,
                )
            ).order_by(KnowledgeBaseShare.create_time.desc())

            total = query.count()
            start = (page - 1) * size
            items = query.offset(start).limit(size).all()

            records = []
            for share, kb, shared_by_user in items:
                records.append({
                    'id': share.id,
                    'kb_id': kb.id,
                    'kb_name': kb.name,
                    'shared_by_id': share.shared_by_id,
                    'shared_by_name': shared_by_user.nickname or shared_by_user.username,
                    'permission_level': share.permission_level,
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
            return {'code': 500, 'data': None, 'msg': f'获取失败: {str(e)}'}
