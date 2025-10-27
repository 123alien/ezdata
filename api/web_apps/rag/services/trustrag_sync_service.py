"""
TrustRAG 同步服务

职责：
- 根据 dataset_id（等同于前端“我的知识库”的ID）解析 namespace（优先绑定表）
- 生成短期 SSO Token（与 external_api_views 保持一致的 HS256）
- 组织文档信息，调用 TrustRAG /ingest 接口实现实时同步

注意：
- Minio 直读：通过文件名拼接公开URL http://localhost:9000/ezdata/<file_name>
  可通过 Flask config 覆盖：TRUSTRAG_MINIO_BASE_URL、TRUSTRAG_MINIO_BUCKET
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import requests
import jwt

from flask import current_app


TRUSTRAG_BASE_URL_DEFAULT = "http://127.0.0.1:8217"
TRUSTRAG_TIMEOUT_SECONDS = 30
TRUSTRAG_DEFAULT_NAMESPACE = "ezdata-test"


def _get_trustrag_base_url() -> str:
    return current_app.config.get("TRUSTRAG_BASE_URL", TRUSTRAG_BASE_URL_DEFAULT)


def _resolve_namespace_by_dataset(dataset_id: Any) -> Optional[str]:
    """根据 dataset_id(UUID) 解析 namespace：
    1) 通过 Dataset(id) 找到 name/create_by
    2) 映射到 UserKnowledgeBase(name, owner_id)
    3) 用 UserKnowledgeBase.id 去查 KnowledgeBaseBinding.kb_id
    4) 如果上述方法失败，尝试直接通过数据集ID查找绑定关系
    """
    try:
        from web_apps import db
        from web_apps.rag.db_models import Dataset
        from web_apps.rag.kb_models import KnowledgeBaseBinding, UserKnowledgeBase

        # 方法1：通过数据集名称和创建者查找知识库
        dataset = (
            db.session.query(Dataset)
            .filter(Dataset.id == dataset_id, Dataset.del_flag == 0)
            .first()
        )
        if dataset:
            kb = (
                db.session.query(UserKnowledgeBase)
                .filter(
                    UserKnowledgeBase.name == dataset.name,
                    UserKnowledgeBase.owner_id == dataset.create_by,
                    UserKnowledgeBase.del_flag == 0,
                )
                .first()
            )
            if kb:
                binding = (
                    db.session.query(KnowledgeBaseBinding)
                    .filter(
                        KnowledgeBaseBinding.kb_id == kb.id,
                        KnowledgeBaseBinding.del_flag == 0,
                    )
                    .first()
                )
                if binding and binding.namespace:
                    return binding.namespace

        # 方法2：直接通过数据集ID查找绑定关系（新增）
        # 假设数据集ID直接对应知识库ID，或者通过其他方式关联
        try:
            # 尝试将数据集ID转换为整数（如果是数字的话）
            kb_id = int(dataset_id) if dataset_id.isdigit() else None
            if kb_id:
                binding = (
                    db.session.query(KnowledgeBaseBinding)
                    .filter(
                        KnowledgeBaseBinding.kb_id == kb_id,
                        KnowledgeBaseBinding.del_flag == 0,
                    )
                    .first()
                )
                if binding and binding.namespace:
                    current_app.logger.info(f"Found binding for dataset {dataset_id} -> kb_id {kb_id} -> namespace {binding.namespace}")
                    return binding.namespace
        except (ValueError, TypeError):
            pass

        # 方法3：不再使用自动回退到默认命名空间的逻辑
        # 这样可以避免不同知识库的文档被错误地上传到同一个命名空间
        # 用户必须明确配置绑定关系才能同步到 TrustRAG

        # 回退到全局默认命名空间，确保一键同步可用
        default_namespace = current_app.config.get("TRUSTRAG_DEFAULT_NAMESPACE", TRUSTRAG_DEFAULT_NAMESPACE)
        current_app.logger.info(f"Using default namespace {default_namespace} for dataset {dataset_id}")
        return default_namespace
    except Exception as e:
        current_app.logger.error(f"resolve namespace failed: {e}")
        return None


def _generate_sso_token(user_id: Any, tenant_id: Any, dataset_id: Any, namespace: str) -> str:
    """生成与 external_api_views 一致的短期 SSO Token (10 分钟)。"""
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "dataset_id": dataset_id,
        "namespace": namespace,
        "permission_level": "write",
        "exp": datetime.utcnow() + timedelta(minutes=10),
        "iat": datetime.utcnow(),
    }
    secret_key = current_app.config.get("SECRET_KEY", "ezdata-secret-key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def _build_minio_file_url(file_name: str) -> str:
    base_url = current_app.config.get("TRUSTRAG_MINIO_BASE_URL", "http://127.0.0.1:9000")
    bucket = current_app.config.get("TRUSTRAG_MINIO_BUCKET", "ezdata")
    # 简单拼接：适用于公开读或本地联调
    return f"{base_url.rstrip('/')}/{bucket}/{file_name}"


def sync_created_document(dataset_id: Any, meta_data: Dict[str, Any]) -> Dict[str, Any]:
    """在文档新增后调用，自动同步到 TrustRAG。

    期望 meta_data 示例（upload_file 模式）：
    {
      "upload_file": "/path/to/file.pdf"  # 服务端保存路径，我们会提取文件名并拼装成 Minio URL
    }
    """
    try:
        from utils.auth import get_auth_token_info

        user_info = get_auth_token_info() or {}
        user_id = user_info.get("user_id") or user_info.get("id") or ""
        tenant_id = user_info.get("tenant_id", 0)

        namespace = _resolve_namespace_by_dataset(dataset_id)
        if not namespace:
            return {"success": False, "message": "未绑定 TrustRAG namespace，已跳过同步"}

        # 从 meta_data 中提取文件路径
        upload_file_path = (meta_data or {}).get("upload_file")
        if not upload_file_path:
            return {"success": False, "message": "meta_data 中未找到 upload_file"}

        # 直传文本优先；若为二进制则改用 Minio URL
        file_name = upload_file_path.split('/')[-1]
        raw_text: Optional[str] = None
        
        # 对于 .docx 等二进制文件，直接使用 MinIO URL，不尝试读取本地文件
        if file_name.lower().endswith(('.docx', '.pdf', '.xlsx', '.pptx')):
            raw_text = None
        else:
            try:
                with open(upload_file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
            except (UnicodeDecodeError, FileNotFoundError):
                raw_text = None

        token = _generate_sso_token(user_id=user_id, tenant_id=tenant_id, dataset_id=dataset_id, namespace=namespace)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if raw_text is not None:
            body = {
                "namespace": namespace,
                "raw_text": raw_text,
            }
        else:
            # 构造公开可读的 Minio URL，让 TrustRAG 自行下载（支持 PDF/Word 等）
            file_url = _build_minio_file_url(file_name)
            body = {
                "namespace": namespace,
                "documents": [{"url": file_url}],
            }

        url = f"{_get_trustrag_base_url().rstrip('/')}/ingest"
        resp = requests.post(url, json=body, headers=headers, timeout=TRUSTRAG_TIMEOUT_SECONDS)
        ok = 200 <= resp.status_code < 300
        if not ok:
            current_app.logger.warning(
                f"TrustRAG /ingest failed: {resp.status_code} {resp.text} body={body}"
            )
        return {
            "success": ok,
            "status_code": resp.status_code,
            "result": (resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text),
        }
    except Exception as e:
        current_app.logger.error(f"sync_created_document error: {e}")
        return {"success": False, "message": str(e)}



def sync_deleted_document(dataset_id: Any, meta_data: Dict[str, Any]) -> Dict[str, Any]:
    """在文档删除后调用，通知 TrustRAG 删除对应文档。

    期望 meta_data 中同样包含 upload_file（与新增保持一致），我们以文件名作为 doc_id。
    """
    try:
        namespace = _resolve_namespace_by_dataset(dataset_id)
        if not namespace:
            return {"success": False, "message": "未绑定 TrustRAG namespace，已跳过删除同步"}

        upload_file_path = (meta_data or {}).get("upload_file")
        file_name = upload_file_path.split("/")[-1] if upload_file_path else None
        if not file_name:
            return {"success": False, "message": "meta_data 中未找到 upload_file，无法定位删除文档"}

        # 使用相同的 SSO 令牌，权限置为 admin 以保证删除权限
        token = _generate_sso_token(user_id="system", tenant_id=0, dataset_id=dataset_id, namespace=namespace)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {"namespace": namespace, "doc_ids": [file_name]}
        url = f"{_get_trustrag_base_url().rstrip('/')}/ingest/delete"
        resp = requests.post(url, json=body, headers=headers, timeout=TRUSTRAG_TIMEOUT_SECONDS)
        ok = 200 <= resp.status_code < 300
        if not ok:
            current_app.logger.warning(
                f"TrustRAG /ingest/delete failed: {resp.status_code} {resp.text} body={body}"
            )
        return {
            "success": ok,
            "status_code": resp.status_code,
            "result": (resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text),
        }
    except Exception as e:
        current_app.logger.error(f"sync_deleted_document error: {e}")
        return {"success": False, "message": str(e)}


def sync_edited_document(dataset_id: Any, meta_data: Dict[str, Any]) -> Dict[str, Any]:
    """在文档编辑后调用，策略：直接再次调用 /ingest 进行覆盖/重入库。"""
    return sync_created_document(dataset_id=dataset_id, meta_data=meta_data)


def bulk_sync_dataset(dataset_id: Any) -> Dict[str, Any]:
    """对已有文档进行一键回填同步到 TrustRAG。

    返回每个文档的同步结果统计。
    """
    try:
        from web_apps import db
        from web_apps.rag.db_models import Document
        from utils.common_utils import parse_json

        docs = (
            db.session.query(Document)
            .filter(Document.dataset_id == dataset_id, Document.del_flag == 0)
            .all()
        )

        results = []
        for d in docs:
            meta = parse_json(d.meta_data)
            res = sync_created_document(dataset_id=dataset_id, meta_data=meta)
            results.append({"doc_id": d.id, **res})

        success_count = sum(1 for r in results if r.get("success"))
        return {"success": True, "total": len(results), "success_count": success_count, "results": results}
    except Exception as e:
        current_app.logger.error(f"bulk_sync_dataset error: {e}")
        return {"success": False, "message": str(e)}

