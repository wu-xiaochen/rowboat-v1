"""
API Key数据模型
API Key data models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class APIKey(BaseModel):
    """
    API Key模型
    API Key model for authentication
    """
    id: str
    project_id: str = Field(alias="projectId")
    name: str
    key: str  # 实际的API key（哈希后存储）
    key_prefix: str = Field(alias="keyPrefix")  # key的前缀（用于显示）
    created_by_user_id: str = Field(alias="createdByUserId")
    created_at: datetime = Field(alias="createdAt")
    last_used_at: Optional[datetime] = Field(None, alias="lastUsedAt")
    is_active: bool = Field(default=True, alias="isActive")
    
    class Config:
        populate_by_name = True


class APIKeyCreate(BaseModel):
    """
    创建API Key的请求模型
    API Key creation request model
    """
    name: str
    project_id: str = Field(alias="projectId")
    
    class Config:
        populate_by_name = True


class APIKeyResponse(BaseModel):
    """
    API Key响应模型（包含明文key，仅在创建时返回一次）
    API Key response model with plain key (only returned once on creation)
    """
    id: str
    project_id: str = Field(alias="projectId")
    name: str
    key: str  # 明文key，仅在创建时返回
    key_prefix: str = Field(alias="keyPrefix")
    created_at: datetime = Field(alias="createdAt")
    
    class Config:
        populate_by_name = True

