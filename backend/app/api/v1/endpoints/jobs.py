"""
任务管理端点
Jobs management endpoints
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query

from app.api import ResponseModel
from app.models.schemas import Job
from app.models.job_requests import JobFiltersRequest
from app.repositories.jobs import JobsRepository

router = APIRouter(prefix="/{project_id}/jobs", tags=["Jobs"])


@router.get("", response_model=dict)
async def list_jobs(
    project_id: str,
    status: Optional[str] = Query(None, description="任务状态过滤"),
    recurringJobRuleId: Optional[str] = Query(None, description="周期性任务规则ID"),
    composioTriggerDeploymentId: Optional[str] = Query(None, description="Composio触发器部署ID"),
    createdAfter: Optional[str] = Query(None, description="创建时间起始（ISO格式）"),
    createdBefore: Optional[str] = Query(None, description="创建时间结束（ISO格式）"),
    cursor: Optional[str] = Query(None, description="分页游标"),
    limit: int = Query(50, ge=1, le=50, description="返回的最大记录数（最多50）"),
):
    """
    获取任务列表
    List jobs
    严格复刻原项目：使用_id作为游标，返回ListedJobItem（只包含部分字段）
    
    Args:
        project_id: 项目ID
        status: 任务状态过滤（pending/running/completed/failed）
        recurringJobRuleId: 周期性任务规则ID
        composioTriggerDeploymentId: Composio触发器部署ID
        createdAfter: 创建时间起始（ISO格式）
        createdBefore: 创建时间结束（ISO格式）
        cursor: 分页游标（可选）
        limit: 返回的最大记录数（最多50）
        
    Returns:
        任务列表（分页结果）
    """
    repo = JobsRepository()
    
    # 构建过滤条件
    filters: Dict[str, Any] = {}
    if status:
        filters["status"] = status
    if recurringJobRuleId:
        filters["recurringJobRuleId"] = recurringJobRuleId
    if composioTriggerDeploymentId:
        filters["composioTriggerDeploymentId"] = composioTriggerDeploymentId
    if createdAfter:
        filters["createdAfter"] = createdAfter
    if createdBefore:
        filters["createdBefore"] = createdBefore
    
    # 获取任务列表
    result = await repo.list(project_id, filters=filters if filters else None, cursor=cursor, limit=limit)
    
    # 转换为响应格式
    jobs_data = result["items"]
    
    return ResponseModel.success(
        data={
            "items": jobs_data,
            "nextCursor": result["nextCursor"],
        },
        message="任务列表获取成功"
    )


@router.get("/{job_id}", response_model=dict)
async def get_job(
    project_id: str,
    job_id: str,
):
    """
    获取任务详情
    Get job details
    严格复刻原项目：先fetch，然后验证项目归属
    
    Args:
        project_id: 项目ID
        job_id: 任务ID
        
    Returns:
        任务详情
    """
    repo = JobsRepository()
    
    # 获取任务（原项目先fetch）
    job = await repo.fetch(job_id)
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {job_id} 不存在"
        )
    
    # 验证任务属于该项目
    if job.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {job_id} 不存在"
        )
    
    return ResponseModel.success(
        data=job.model_dump(by_alias=True),
        message="任务详情获取成功"
    )

