"""
API Key管理端点
API Key management endpoints
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import uuid

from app.api import ResponseModel
from app.models.api_key import APIKey, APIKeyCreate, APIKeyResponse
from app.repositories.api_keys import APIKeysRepository
from app.repositories.projects import ProjectsRepository
from app.core.security import generate_api_key, hash_api_key, get_key_prefix

router = APIRouter(prefix="/projects/{project_id}/api-keys", tags=["API Keys"])


@router.post("", response_model=dict)
async def create_api_key(project_id: str, api_key_create: APIKeyCreate):
    """
    创建API Key
    Create a new API key for a project
    
    Args:
        project_id: 项目ID
        api_key_create: API Key创建请求
        
    Returns:
        创建的API Key（包含明文key，仅返回一次）
    """
    # 验证项目是否存在
    projects_repo = ProjectsRepository()
    if not await projects_repo.exists(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 不存在"
        )
    
    # 生成API Key
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)
    key_prefix = get_key_prefix(plain_key)
    
    # 创建API Key对象
    api_key = APIKey(
        id=str(uuid.uuid4()),
        projectId=project_id,
        name=api_key_create.name,
        key=key_hash,
        keyPrefix=key_prefix,
        createdByUserId="system",  # TODO: 从认证上下文获取
        createdAt=datetime.now(),
    )
    
    # 保存到数据库
    repo = APIKeysRepository()
    await repo.create(api_key)
    
    # 返回响应（包含明文key）
    response = APIKeyResponse(
        id=api_key.id,
        projectId=api_key.project_id,
        name=api_key.name,
        key=plain_key,  # 仅在创建时返回明文key
        keyPrefix=key_prefix,
        createdAt=api_key.created_at,
    )
    
    return ResponseModel.success(
        data=response.model_dump(by_alias=True),
        message="API Key创建成功"
    )


@router.get("", response_model=dict)
async def list_api_keys(project_id: str):
    """
    获取项目的所有API Key
    List all API keys for a project
    
    Args:
        project_id: 项目ID
        
    Returns:
        API Key列表（不包含完整key）
    """
    # 验证项目是否存在
    projects_repo = ProjectsRepository()
    if not await projects_repo.exists(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 不存在"
        )
    
    # 获取API Key列表
    repo = APIKeysRepository()
    api_keys = await repo.get_by_project_id(project_id)
    
    # 转换为响应格式（移除完整key）
    api_keys_data = [
        {
            "id": key.id,
            "projectId": key.project_id,
            "name": key.name,
            "keyPrefix": key.key_prefix,
            "createdAt": key.created_at.isoformat(),
            "lastUsedAt": key.last_used_at.isoformat() if key.last_used_at else None,
            "isActive": key.is_active,
        }
        for key in api_keys
    ]
    
    return ResponseModel.success(
        data=api_keys_data,
        message="API Key列表获取成功"
    )


@router.delete("/{key_id}", response_model=dict)
async def delete_api_key(project_id: str, key_id: str):
    """
    删除API Key
    Delete an API key
    
    Args:
        project_id: 项目ID
        key_id: API Key ID
        
    Returns:
        删除结果
    """
    # 验证API Key是否存在且属于该项目
    repo = APIKeysRepository()
    api_key = await repo.get_by_id(key_id)
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key {key_id} 不存在"
        )
    
    if api_key.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此API Key"
        )
    
    # 删除API Key
    success = await repo.delete(key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除API Key失败"
        )
    
    return ResponseModel.success(
        message="API Key删除成功"
    )

