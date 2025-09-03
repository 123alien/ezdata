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


TRUSTRAG_BASE_URL_DEFAULT = "http://localhost:8217"
TRUSTRAG_TIMEOUT_SECONDS = 30


def _get_trustrag_base_url() -> str:
    return current_app.config.get("TRUSTRAG_BASE_URL", TRUSTRAG_BASE_URL_DEFAULT)


def _resolve_namespace_by_dataset(dataset_id: Any) -> Optional[str]:
    """根据 dataset_id 解析 namespace：优先从绑定表查，没有就返回 None。"""
    try:
        from web_apps import db
        from web_apps.rag.kb_models import KnowledgeBaseBinding

        binding = (
            db.session.query(KnowledgeBaseBinding)
            .filter(
                KnowledgeBaseBinding.kb_id == dataset_id,
                KnowledgeBaseBinding.del_flag == 0,
            )
            .first()
        )
        if binding:
            return binding.namespace
        return None
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
    return jwt.encode(payload, secret_key, algorithm="HS256")


def _build_minio_file_url(file_name: str) -> str:
    base_url = current_app.config.get("TRUSTRAG_MINIO_BASE_URL", "http://localhost:9000")
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

        # 从 meta_data 中提取文件名（与 rag_service.train_document 逻辑一致）
        upload_file_path = (meta_data or {}).get("upload_file")
        file_name = upload_file_path.split("/")[-1] if upload_file_path else None
        if not file_name:
            return {"success": False, "message": "meta_data 中未找到 upload_file，无法构建 Minio URL"}

        file_url = _build_minio_file_url(file_name)

        token = _generate_sso_token(user_id=user_id, tenant_id=tenant_id, dataset_id=dataset_id, namespace=namespace)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "namespace": namespace,
            "documents": [
                {
                    "doc_id": file_name,
                    "title": file_name,
                    "url": file_url,
                    "metadata": {"dataset_id": dataset_id},
                }
            ],
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


