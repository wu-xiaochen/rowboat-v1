"""
数据源管理端点
Data Sources management endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from datetime import datetime
import uuid

from app.api import ResponseModel
from app.models.schemas import DataSource, DataSourceStatus
from app.models.data_source_requests import (
    DataSourceCreateRequest,
    DataSourceUpdateRequest,
    DataSourceToggleRequest,
)
from app.repositories.data_sources import DataSourcesRepository

router = APIRouter(prefix="/{project_id}/data-sources", tags=["Data Sources"])


@router.post("", response_model=dict)
async def create_data_source(
    project_id: str,
    request: DataSourceCreateRequest,
):
    """
    创建数据源
    Create a new data source
    严格复刻原项目：status逻辑（文件类型不能设置status，其他类型可以）
    
    Args:
        project_id: 项目ID
        request: 数据源创建请求
        
    Returns:
        创建的数据源对象
    """
    # 确定status（原项目逻辑：文件类型不能设置status）
    _status = DataSourceStatus.PENDING
    if request.status and request.data.get("type") not in ["files_local", "files_s3"]:
        # 只有非文件类型才能设置status
        _status = request.status
    
    # 构建创建数据（原项目CreateSchema）
    create_data = {
        "projectId": project_id,
        "name": request.name,
        "description": request.description,
        "data": request.data,  # 使用请求中的data（包含type和其他字段）
        "status": _status,
    }
    
    # 保存到数据库（Repository会生成ObjectId并设置默认值）
    repo = DataSourcesRepository()
    created_source = await repo.create(create_data)
    
    return ResponseModel.success(
        data=created_source.model_dump(by_alias=True),
        message="数据源已创建"
    )


@router.get("", response_model=dict)
async def list_data_sources(
    project_id: str,
    active: Optional[bool] = Query(None, description="过滤激活状态"),
    deleted: Optional[bool] = Query(None, description="是否包含已删除的数据源"),
    cursor: Optional[str] = Query(None, description="分页游标"),
    limit: int = Query(50, ge=1, le=50, description="返回的最大记录数（最多50）"),
):
    """
    获取数据源列表
    List data sources
    严格复刻原项目：循环获取所有数据（直到cursor为null），默认排除deleted
    
    Args:
        project_id: 项目ID
        active: 过滤激活状态（可选）
        deleted: 是否包含已删除的数据源（可选）
        cursor: 分页游标（可选）
        limit: 返回的最大记录数（最多50）
        
    Returns:
        数据源列表（原项目返回所有数据，不是分页）
    """
    repo = DataSourcesRepository()
    
    # 构建过滤条件（原项目ListFiltersSchema）
    filters: Dict[str, Any] = {}
    if active is not None:
        filters["active"] = active
    if deleted is not None:
        filters["deleted"] = deleted
    
    # 原项目逻辑：循环获取所有数据（直到cursor为null）
    all_sources = []
    current_cursor = cursor
    while True:
        result = await repo.list(project_id, filters=filters, cursor=current_cursor, limit=limit)
        all_sources.extend(result["items"])
        current_cursor = result["nextCursor"]
        if not current_cursor:
            break
    
    # 转换为响应格式
    sources_data = [
        source.model_dump(by_alias=True)
        for source in all_sources
    ]
    
    return ResponseModel.success(
        data=sources_data,  # 原项目返回数组，不是对象
        message="数据源列表获取成功"
    )


@router.get("/{source_id}", response_model=dict)
async def get_data_source(
    project_id: str,
    source_id: str,
):
    """
    获取数据源详情
    Get data source details
    
    Args:
        project_id: 项目ID
        source_id: 数据源ID
        
    Returns:
        数据源详情
    """
    repo = DataSourcesRepository()
    data_source = await repo.fetch(source_id)
    
    if data_source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    # 验证数据源属于该项目
    if data_source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    return ResponseModel.success(
        data=data_source.model_dump(by_alias=True),
        message="数据源详情获取成功"
    )


@router.put("/{source_id}", response_model=dict)
async def update_data_source(
    project_id: str,
    source_id: str,
    request: DataSourceUpdateRequest,
):
    """
    更新数据源
    Update a data source
    严格复刻原项目：只更新description字段，bumpVersion=true
    
    Args:
        project_id: 项目ID
        source_id: 数据源ID
        request: 数据源更新请求（原项目只允许更新description）
        
    Returns:
        更新后的数据源
    """
    repo = DataSourcesRepository()
    
    # 获取现有数据源（原项目先fetch）
    existing_source = await repo.fetch(source_id)
    if existing_source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    # 验证数据源属于该项目
    if existing_source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    # 构建更新数据（原项目UpdateSchema只允许更新description）
    update_data: Dict[str, Any] = {}
    if request.description is not None:
        update_data["description"] = request.description
    
    # 原项目不允许更新name和data，只允许更新description
    # 如果请求中包含name或data，忽略它们
    
    # 更新数据源（bumpVersion=true）
    result = await repo.update(source_id, update_data, bump_version=True)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据源更新失败"
        )
    
    return ResponseModel.success(
        data=result.model_dump(by_alias=True),
        message="数据源更新成功"
    )


@router.delete("/{source_id}", response_model=dict)
async def delete_data_source(
    project_id: str,
    source_id: str,
):
    """
    删除数据源
    Delete a data source
    严格复刻原项目：先fetch，然后update status为deleted（软删除），不是真正的delete
    
    Args:
        project_id: 项目ID
        source_id: 数据源ID
        
    Returns:
        删除结果
    """
    repo = DataSourcesRepository()
    
    # 获取现有数据源（原项目先fetch）
    existing_source = await repo.fetch(source_id)
    if existing_source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    # 验证数据源属于该项目
    if existing_source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    # 软删除：update status为deleted（原项目Use Case逻辑）
    update_data = {
        "status": DataSourceStatus.DELETED,
        "attempts": 0,
        "billingError": None,
    }
    result = await repo.update(source_id, update_data, bump_version=True)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据源删除失败"
        )
    
    return ResponseModel.success(
        message="数据源删除成功"
    )


@router.post("/{source_id}/toggle", response_model=dict)
async def toggle_data_source(
    project_id: str,
    source_id: str,
    request: DataSourceToggleRequest,
):
    """
    切换数据源状态
    Toggle data source active status
    严格复刻原项目：先fetch，然后update active字段
    
    Args:
        project_id: 项目ID
        source_id: 数据源ID
        request: 切换状态请求
        
    Returns:
        更新后的数据源
    """
    repo = DataSourcesRepository()
    
    # 获取现有数据源（原项目先fetch）
    existing_source = await repo.fetch(source_id)
    if existing_source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    # 验证数据源属于该项目
    if existing_source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据源 {source_id} 不存在"
        )
    
    # 更新active状态（原项目只更新active字段，不bumpVersion）
    update_data = {"active": request.active}
    updated_source = await repo.update(source_id, update_data, bump_version=False)
    
    if updated_source is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据源状态切换失败"
        )
    
    return ResponseModel.success(
        data=updated_source.model_dump(by_alias=True),
        message=f"数据源已{'激活' if request.active else '禁用'}"
    )

