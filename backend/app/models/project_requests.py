"""
项目请求模型
Project request models
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """项目创建请求模型"""
    name: str = Field(..., description="项目名称")
    created_by_user_id: Optional[str] = Field(
        None,
        alias="createdByUserId",
        description="创建者用户ID（可选，默认'system'）"
    )
    
    class Config:
        populate_by_name = True


class ProjectUpdateRequest(BaseModel):
    """项目更新请求模型"""
    name: Optional[str] = Field(None, description="项目名称")
    webhook_url: Optional[str] = Field(None, alias="webhookUrl", description="Webhook URL")
    draft_workflow: Optional[dict] = Field(None, alias="draftWorkflow", description="草稿工作流")
    live_workflow: Optional[dict] = Field(None, alias="liveWorkflow", description="生产工作流")
    
    class Config:
        populate_by_name = True

