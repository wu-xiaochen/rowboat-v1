"""
任务管理功能集成测试
Integration tests for Jobs management endpoints
严格复刻原项目逻辑的测试
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime
from bson import ObjectId

from app.main import app
from app.models.schemas import Job, JobStatus, JobInput, JobOutput, Reason, ReasonType
from typing import Dict, Any


@pytest.mark.asyncio
async def test_list_jobs_success():
    """测试获取任务列表成功"""
    # Mock Repository
    mock_jobs = [
        {
            "id": str(ObjectId()),
            "projectId": "test_project_id",
            "status": "pending",
            "reason": {"type": "api"},
            "createdAt": datetime.now().isoformat(),
            "updatedAt": None,
        },
        {
            "id": str(ObjectId()),
            "projectId": "test_project_id",
            "status": "completed",
            "reason": {"type": "recurring_job_rule", "ruleId": "rule123"},
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        },
    ]
    
    mock_list_result = {
        "items": mock_jobs,
        "nextCursor": None,
    }
    
    with patch("app.api.v1.endpoints.jobs.JobsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list = AsyncMock(return_value=mock_list_result)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/jobs"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "nextCursor" in data["data"]
        assert len(data["data"]["items"]) == 2
        assert data["data"]["items"][0]["status"] == "pending"
        
        # 验证Repository被调用
        mock_repo_instance.list.assert_called_once()
        call_args = mock_repo_instance.list.call_args
        assert call_args[0][0] == "test_project_id"  # 第一个位置参数是project_id


@pytest.mark.asyncio
async def test_list_jobs_with_filters():
    """测试带过滤条件的任务列表"""
    # Mock Repository
    mock_jobs = [
        {
            "id": str(ObjectId()),
            "projectId": "test_project_id",
            "status": "completed",
            "reason": {"type": "api"},
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }
    ]
    
    mock_list_result = {
        "items": mock_jobs,
        "nextCursor": None,
    }
    
    with patch("app.api.v1.endpoints.jobs.JobsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list = AsyncMock(return_value=mock_list_result)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/jobs",
                params={"status": "completed", "limit": 50}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["status"] == "completed"
        
        # 验证Repository被调用时传递了过滤条件
        mock_repo_instance.list.assert_called_once()
        call_args = mock_repo_instance.list.call_args
        assert call_args[0][0] == "test_project_id"
        if call_args[1] and "filters" in call_args[1]:
            assert call_args[1]["filters"]["status"] == "completed"


@pytest.mark.asyncio
async def test_list_jobs_with_cursor():
    """测试带游标的任务列表"""
    # Mock Repository
    mock_jobs = [
        {
            "id": str(ObjectId()),
            "projectId": "test_project_id",
            "status": "pending",
            "reason": {"type": "api"},
            "createdAt": datetime.now().isoformat(),
            "updatedAt": None,
        }
    ]
    
    mock_list_result = {
        "items": mock_jobs,
        "nextCursor": str(ObjectId()),
    }
    
    with patch("app.api.v1.endpoints.jobs.JobsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list = AsyncMock(return_value=mock_list_result)
        mock_repo_class.return_value = mock_repo_instance
        
        cursor = str(ObjectId())
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/jobs",
                params={"cursor": cursor, "limit": 50}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["nextCursor"] is not None
        
        # 验证Repository被调用时传递了cursor
        mock_repo_instance.list.assert_called_once()
        call_args = mock_repo_instance.list.call_args
        assert call_args[0][0] == "test_project_id"
        assert call_args[1]["cursor"] == cursor


@pytest.mark.asyncio
async def test_get_job_success():
    """测试获取任务详情成功"""
    # Mock Repository
    mock_job_id = str(ObjectId())
    mock_job = Job(
        id=mock_job_id,
        projectId="test_project_id",
        status=JobStatus.PENDING,
        reason=Reason(type=ReasonType.USER_MESSAGE),  # 使用有效的ReasonType
        input=JobInput(messages=[]),
        output=None,
        workerId=None,
        lastWorkerId=None,
        createdAt=datetime.now(),
        updatedAt=None,
    )
    
    with patch("app.api.v1.endpoints.jobs.JobsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=mock_job)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                f"/api/v1/test_project_id/jobs/{mock_job_id}"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == mock_job_id
        assert data["data"]["projectId"] == "test_project_id"
        assert data["data"]["status"] == "pending"
        
        # 验证Repository被调用
        mock_repo_instance.fetch.assert_called_once_with(mock_job_id)


@pytest.mark.asyncio
async def test_get_job_not_found():
    """测试获取不存在的任务"""
    with patch("app.api.v1.endpoints.jobs.JobsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=None)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/jobs/non_existent_id"
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_get_job_project_mismatch():
    """测试获取不属于该项目的任务"""
    mock_job_id = str(ObjectId())
    mock_job = Job(
        id=mock_job_id,
        projectId="other_project_id",  # 不同的项目ID
        status=JobStatus.PENDING,
        reason=Reason(type=ReasonType.USER_MESSAGE),  # 使用有效的ReasonType
        input=JobInput(messages=[]),
        output=None,
        workerId=None,
        lastWorkerId=None,
        createdAt=datetime.now(),
        updatedAt=None,
    )
    
    with patch("app.api.v1.endpoints.jobs.JobsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=mock_job)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                f"/api/v1/test_project_id/jobs/{mock_job_id}"
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

