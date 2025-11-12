"""
项目管理端点集成测试
Integration tests for Project management endpoints
"""

import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
import uuid

# 设置环境变量
os.environ.update({
    "APP_NAME": "测试应用",
    "API_PORT": "8001",
    "DEBUG": "true",
    "ENVIRONMENT": "test",
    "LLM_API_KEY": "test-llm-key",
    "LLM_BASE_URL": "https://test-llm.com",
    "LLM_MODEL_ID": "test-model",
    "EMBEDDING_MODEL": "test-embedding",
    "EMBEDDING_PROVIDER_BASE_URL": "https://test-embedding.com",
    "EMBEDDING_PROVIDER_API_KEY": "test-embedding-key",
    "COMPOSIO_API_KEY": "test-composio-key",
    "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
    "REDIS_URL": "redis://test:6379",
    "QDRANT_URL": "http://test:6333",
    "USE_RAG": "true",
    "USE_COMPOSIO_TOOLS": "true",
})

from app.main import app
from app.models.schemas import Project, Workflow


class TestProjectEndpoints:
    """项目管理端点测试"""
    
    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """测试：创建项目成功"""
        # Mock项目创建
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_project = Project(
                id=str(uuid.uuid4()),
                name="测试项目",
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="test_secret",
                draftWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
                liveWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
            )
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.create = AsyncMock(return_value=mock_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/projects",
                    json={"name": "测试项目", "createdByUserId": "user123"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "id" in data["data"]
                assert "secret" in data["data"]  # 创建时返回secret
                assert data["data"]["name"] == "测试项目"
                assert data["data"]["createdByUserId"] == "user123"
    
    @pytest.mark.asyncio
    async def test_create_project_with_default_user_id(self):
        """测试：创建项目（使用默认用户ID）"""
        # Mock项目创建
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_project = Project(
                id=str(uuid.uuid4()),
                name="测试项目",
                createdAt=datetime.now(),
                createdByUserId="system",
                secret="test_secret",
                draftWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
                liveWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
            )
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.create = AsyncMock(return_value=mock_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/projects",
                    json={"name": "测试项目"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                # 验证使用默认用户ID
                mock_repo_instance.create.assert_called_once()
                call_args = mock_repo_instance.create.call_args[0][0]
                assert call_args.created_by_user_id == "system"
    
    @pytest.mark.asyncio
    async def test_get_project_success(self):
        """测试：获取项目详情成功"""
        # Mock项目查询
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_project = Project(
                id="proj123",
                name="测试项目",
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="test_secret",
                draftWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
                liveWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
            )
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_id = AsyncMock(return_value=mock_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/projects/proj123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["id"] == "proj123"
                assert data["data"]["name"] == "测试项目"
                assert "secret" not in data["data"]  # 不应返回secret
                assert "draftWorkflow" in data["data"]
                assert "liveWorkflow" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self):
        """测试：获取项目详情失败（不存在）"""
        # Mock项目不存在
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_id = AsyncMock(return_value=None)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/projects/nonexistent")
                
                assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_projects_success(self):
        """测试：获取项目列表成功"""
        # Mock项目列表查询
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_project = Project(
                id="proj123",
                name="测试项目",
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="test_secret",
                draftWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
                liveWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
            )
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_user_id = AsyncMock(return_value=[mock_project])
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/projects",
                    params={"createdByUserId": "user123"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == 1
                assert data["data"][0]["name"] == "测试项目"
                assert "secret" not in data["data"][0]  # 不应返回secret
    
    @pytest.mark.asyncio
    async def test_list_projects_missing_user_id(self):
        """测试：获取项目列表失败（缺少用户ID）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/projects")
            
            assert response.status_code == 400
            data = response.json()
            # FastAPI验证错误可能返回不同的格式
            assert response.status_code == 400
            # 验证错误信息包含相关提示
            assert "createdByUserId" in str(data) or "必需" in str(data)
    
    @pytest.mark.asyncio
    async def test_update_project_success(self):
        """测试：更新项目成功"""
        # Mock项目查询和更新
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            existing_project = Project(
                id="proj123",
                name="旧项目名",
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="test_secret",
                draftWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
                liveWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
            )
            
            updated_project = Project(
                id="proj123",
                name="新项目名",
                createdAt=existing_project.created_at,
                lastUpdatedAt=datetime.now(),
                createdByUserId="user123",
                secret="test_secret",
                draftWorkflow=existing_project.draft_workflow,
                liveWorkflow=existing_project.live_workflow,
            )
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_id = AsyncMock(return_value=existing_project)
            mock_repo_instance.update = AsyncMock(return_value=updated_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/projects/proj123",
                    json={"name": "新项目名"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["name"] == "新项目名"
    
    @pytest.mark.asyncio
    async def test_update_project_not_found(self):
        """测试：更新项目失败（不存在）"""
        # Mock项目不存在
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_id = AsyncMock(return_value=None)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/projects/nonexistent",
                    json={"name": "新项目名"}
                )
                
                assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_project_success(self):
        """测试：删除项目成功"""
        # Mock项目删除
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.exists = AsyncMock(return_value=True)
            mock_repo_instance.delete = AsyncMock(return_value=True)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/projects/proj123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_project_not_found(self):
        """测试：删除项目失败（不存在）"""
        # Mock项目不存在
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.exists = AsyncMock(return_value=False)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/projects/nonexistent")
                
                assert response.status_code == 404

