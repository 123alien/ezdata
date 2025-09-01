from web_apps import db
from models import BaseModel
from sqlalchemy import UniqueConstraint

class UserKnowledgeBase(BaseModel):
    __tablename__ = 'rag_knowledge_base'
    name = db.Column(db.String(200), nullable=False, comment='知识库名称')
    owner_id = db.Column(db.String(36), nullable=False, comment='所有者用户ID')
    is_public = db.Column(db.SmallInteger, default=0, comment='是否公开 (0: 私有, 1: 公开)')
    status = db.Column(db.SmallInteger, default=1, comment='状态 (1: 启用, 0: 禁用)')
    
    __table_args__ = (
        UniqueConstraint('name', 'owner_id', name='uq_kb_name_owner'),
    )

class KnowledgeBaseDocument(BaseModel):
    __tablename__ = 'rag_kb_document'
    kb_id = db.Column(db.Integer, db.ForeignKey('rag_knowledge_base.id'), nullable=False, comment='知识库ID')
    document_name = db.Column(db.String(200), nullable=False, comment='文档名称')
    file_path = db.Column(db.String(500), nullable=True, comment='文件存储路径')
    file_type = db.Column(db.String(50), nullable=True, comment='文件类型')
    status = db.Column(db.SmallInteger, default=1, comment='文档处理状态 (1: 待处理, 2: 处理中, 3: 已处理, 4: 处理失败)')
    doc_metadata = db.Column(db.Text, nullable=True, comment='文档元数据')

class KnowledgeBaseShare(BaseModel):
    __tablename__ = 'rag_kb_share_permission'
    kb_id = db.Column(db.Integer, db.ForeignKey('rag_knowledge_base.id'), nullable=False, comment='知识库ID')
    shared_by_id = db.Column(db.String(36), nullable=False, comment='分享者用户ID')
    shared_with_id = db.Column(db.String(36), nullable=False, comment='被分享者用户ID')
    permission_level = db.Column(db.String(50), default='read', comment='权限级别 (read, write, admin)')
    status = db.Column(db.SmallInteger, default=1, comment='分享状态 (1: 有效, 0: 失效)')

    __table_args__ = (
        UniqueConstraint('kb_id', 'shared_with_id', name='uq_kb_share'),
    )
