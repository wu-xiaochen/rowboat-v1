"""
项目管理端点
Project management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
import uuid

from app.api import ResponseModel
from app.api.dependencies import verify_api_key, get_optional_api_key
from app.models.schemas import Project, Workflow
from app.models.project_requests import ProjectCreateRequest, ProjectUpdateRequest
from app.repositories.projects import ProjectsRepository
from app.core.security import generate_project_secret

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_default_workflow() -> Workflow:
    """
    获取默认空工作流
    Get default empty workflow
    
    Returns:
        默认工作流
    """
    return Workflow(
        agents=[],
        prompts=[],
        tools=[],
        pipelines=[],
        start_agent_name=None,
    )


@router.post("", response_model=dict)
async def create_project(
    request: ProjectCreateRequest,
    # 暂时不强制API Key验证，允许创建项目
    # project_id: Optional[str] = Depends(get_optional_api_key)
):
    """
    创建项目
    Create a new project
    
    Args:
        request: 项目创建请求
        
    Returns:
        创建的项目对象
    """
    # 生成项目ID和Secret
    project_id = str(uuid.uuid4())
    secret = generate_project_secret()
    
    # 使用默认空工作流
    default_workflow = get_default_workflow()
    
    # 创建项目对象
    project = Project(
        id=project_id,
        name=request.name,
        createdAt=datetime.now(),
        createdByUserId=request.created_by_user_id or "system",
        secret=secret,
        draftWorkflow=default_workflow,
        liveWorkflow=default_workflow,
    )
    
    # 保存到数据库
    repo = ProjectsRepository()
    created_project = await repo.create(project)
    
    # 返回响应（包含secret，仅在创建时返回）
    return ResponseModel.success(
        data={
            "id": created_project.id,
            "name": created_project.name,
            "secret": secret,  # 仅在创建时返回secret
            "createdAt": created_project.created_at.isoformat(),
            "createdByUserId": created_project.created_by_user_id,
            "webhookUrl": created_project.webhook_url,
        },
        message="项目创建成功"
    )


@router.get("", response_model=dict)
async def list_projects(
    created_by_user_id: Optional[str] = Query(None, alias="createdByUserId"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    # 暂时不强制API Key验证
    # project_id: Optional[str] = Depends(get_optional_api_key)
):
    """
    获取项目列表
    List projects
    
    Args:
        created_by_user_id: 创建者用户ID（必需，用于筛选）
        skip: 跳过的记录数
        limit: 返回的最大记录数
        
    Returns:
        项目列表
    """
    if not created_by_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="createdByUserId参数是必需的"
        )
    
    repo = ProjectsRepository()
    
    # 根据用户ID获取项目列表
    projects = await repo.get_by_user_id(created_by_user_id, skip=skip, limit=limit)
    
    # 转换为响应格式（不包含secret和完整workflow）
    projects_data = [
        {
            "id": project.id,
            "name": project.name,
            "createdAt": project.created_at.isoformat(),
            "lastUpdatedAt": project.last_updated_at.isoformat() if project.last_updated_at else None,
            "createdByUserId": project.created_by_user_id,
            "webhookUrl": project.webhook_url,
        }
        for project in projects
    ]
    
    return ResponseModel.success(
        data=projects_data,
        message="项目列表获取成功"
    )


@router.get("/{project_id}", response_model=dict)
async def get_project(
    project_id: str,
    # 验证API Key（可选，因为某些场景可能需要公开访问）
    # verified_project_id: Optional[str] = Depends(get_optional_api_key)
):
    """
    获取项目详情
    Get project details
    
    Args:
        project_id: 项目ID
        
    Returns:
        项目详情（不包含secret）
    """
    repo = ProjectsRepository()
    project = await repo.get_by_id(project_id)
    
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 不存在"
        )
    
    # 返回项目详情（不包含secret）
    return ResponseModel.success(
        data={
            "id": project.id,
            "name": project.name,
            "createdAt": project.created_at.isoformat(),
            "lastUpdatedAt": project.last_updated_at.isoformat() if project.last_updated_at else None,
            "createdByUserId": project.created_by_user_id,
            "webhookUrl": project.webhook_url,
            "draftWorkflow": project.draft_workflow.model_dump(by_alias=True),
            "liveWorkflow": project.live_workflow.model_dump(by_alias=True),
            "composioConnectedAccounts": project.composio_connected_accounts,
            "customMcpServers": project.custom_mcp_servers,
        },
        message="项目详情获取成功"
    )


@router.put("/{project_id}", response_model=dict)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    # 验证API Key（可选）
    # verified_project_id: Optional[str] = Depends(get_optional_api_key)
):
    """
    更新项目
    Update a project
    
    Args:
        project_id: 项目ID
        request: 项目更新请求
        
    Returns:
        更新后的项目
    """
    repo = ProjectsRepository()
    
    # 获取现有项目
    existing_project = await repo.get_by_id(project_id)
    if existing_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 不存在"
        )
    
    # 更新项目字段（仅更新提供的字段）
    updated_data = existing_project.model_dump(by_alias=True)
    
    # 更新提供的字段
    if request.name is not None:
        updated_data["name"] = request.name
    if request.webhook_url is not None:
        updated_data["webhookUrl"] = request.webhook_url
    if request.draft_workflow is not None:
        # 将dict转换为Workflow对象
        updated_data["draftWorkflow"] = request.draft_workflow
    if request.live_workflow is not None:
        # 将dict转换为Workflow对象
        updated_data["liveWorkflow"] = request.live_workflow
    
    # 确保ID不变
    updated_data["id"] = project_id
    
    # 转换workflow dict为Workflow对象
    if isinstance(updated_data.get("draftWorkflow"), dict):
        updated_data["draftWorkflow"] = Workflow(**updated_data["draftWorkflow"])
    if isinstance(updated_data.get("liveWorkflow"), dict):
        updated_data["liveWorkflow"] = Workflow(**updated_data["liveWorkflow"])
    
    # 创建更新后的项目对象
    updated_project = Project(**updated_data)
    
    # 保存更新
    result = await repo.update(project_id, updated_project)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="项目更新失败"
        )
    
    # 返回更新后的项目（不包含secret）
    return ResponseModel.success(
        data={
            "id": result.id,
            "name": result.name,
            "createdAt": result.created_at.isoformat(),
            "lastUpdatedAt": result.last_updated_at.isoformat() if result.last_updated_at else None,
            "createdByUserId": result.created_by_user_id,
            "webhookUrl": result.webhook_url,
            "draftWorkflow": result.draft_workflow.model_dump(by_alias=True),
            "liveWorkflow": result.live_workflow.model_dump(by_alias=True),
        },
        message="项目更新成功"
    )


@router.delete("/{project_id}", response_model=dict)
async def delete_project(
    project_id: str,
    # 验证API Key（可选）
    # verified_project_id: Optional[str] = Depends(get_optional_api_key)
):
    """
    删除项目
    Delete a project
    
    Args:
        project_id: 项目ID
        
    Returns:
        删除结果
    """
    repo = ProjectsRepository()
    
    # 验证项目是否存在
    if not await repo.exists(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 不存在"
        )
    
    # 删除项目
    success = await repo.delete(project_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="项目删除失败"
        )
    
    return ResponseModel.success(
        message="项目删除成功"
    )

