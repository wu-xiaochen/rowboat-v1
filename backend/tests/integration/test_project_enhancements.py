"""
项目管理增强功能集成测试
Integration tests for project enhancement endpoints
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


class TestProjectEnhancements:
    """项目管理增强功能测试"""
    
    @pytest.mark.asyncio
    async def test_rotate_secret_success(self):
        """测试：旋转Secret成功"""
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo, \
             patch("app.api.v1.endpoints.projects.generate_project_secret") as mock_gen_secret:
            project_id = str(uuid.uuid4())
            new_secret = "new_secret_12345"
            mock_gen_secret.return_value = new_secret
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.exists = AsyncMock(return_value=True)
            mock_repo_instance.update_secret = AsyncMock(return_value=new_secret)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(f"/api/v1/projects/{project_id}/rotate-secret")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "secret" in data["data"]
                assert data["data"]["secret"] == new_secret
                assert "Secret已成功旋转" in data["message"]
    
    @pytest.mark.asyncio
    async def test_rotate_secret_project_not_found(self):
        """测试：旋转Secret - 项目不存在"""
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            project_id = str(uuid.uuid4())
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.exists = AsyncMock(return_value=False)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(f"/api/v1/projects/{project_id}/rotate-secret")
                
                assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_project_name_success(self):
        """测试：更新项目名称成功"""
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            project_id = str(uuid.uuid4())
            new_name = "新项目名称"
            
            updated_project = Project(
                id=project_id,
                name=new_name,
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="secret",
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
            mock_repo_instance.update_name = AsyncMock(return_value=updated_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.put(
                    f"/api/v1/projects/{project_id}/name",
                    json={"name": new_name}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["name"] == new_name
                assert "项目名称已更新" in data["message"]
    
    @pytest.mark.asyncio
    async def test_update_draft_workflow_success(self):
        """测试：保存草稿工作流成功"""
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            project_id = str(uuid.uuid4())
            
            workflow = Workflow(
                agents=[],
                prompts=[],
                tools=[],
                pipelines=[],
                start_agent_name=None,
            )
            
            updated_project = Project(
                id=project_id,
                name="测试项目",
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="secret",
                draftWorkflow=workflow,
                liveWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
            )
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.update_draft_workflow = AsyncMock(return_value=updated_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.put(
                    f"/api/v1/projects/{project_id}/draft-workflow",
                    json={"workflow": workflow.model_dump(by_alias=True)}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "draftWorkflow" in data["data"]
                assert "草稿工作流已保存" in data["message"]
    
    @pytest.mark.asyncio
    async def test_publish_workflow_success(self):
        """测试：发布工作流成功"""
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            project_id = str(uuid.uuid4())
            
            workflow = Workflow(
                agents=[],
                prompts=[],
                tools=[],
                pipelines=[],
                start_agent_name=None,
            )
            
            project = Project(
                id=project_id,
                name="测试项目",
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="secret",
                draftWorkflow=workflow,
                liveWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name=None,
                ),
            )
            
            updated_project = project.model_copy()
            updated_project.live_workflow = workflow
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_id = AsyncMock(return_value=project)
            mock_repo_instance.update_live_workflow = AsyncMock(return_value=updated_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                # 不发送请求体，使用当前draftWorkflow
                response = await client.put(
                    f"/api/v1/projects/{project_id}/live-workflow"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "liveWorkflow" in data["data"]
                assert "工作流已发布" in data["message"]
    
    @pytest.mark.asyncio
    async def test_revert_to_live_workflow_success(self):
        """测试：回滚到生产工作流成功"""
        with patch("app.api.v1.endpoints.projects.ProjectsRepository") as mock_repo:
            project_id = str(uuid.uuid4())
            
            live_workflow = Workflow(
                agents=[],
                prompts=[],
                tools=[],
                pipelines=[],
                start_agent_name=None,
            )
            
            project = Project(
                id=project_id,
                name="测试项目",
                createdAt=datetime.now(),
                createdByUserId="user123",
                secret="secret",
                draftWorkflow=Workflow(
                    agents=[],
                    prompts=[],
                    tools=[],
                    pipelines=[],
                    start_agent_name="different",
                ),
                liveWorkflow=live_workflow,
            )
            
            updated_project = project.model_copy()
            updated_project.draft_workflow = live_workflow.model_copy()
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.revert_to_live_workflow = AsyncMock(return_value=updated_project)
            mock_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(f"/api/v1/projects/{project_id}/revert-to-live")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "draftWorkflow" in data["data"]
                assert "已回滚到生产工作流" in data["message"]

