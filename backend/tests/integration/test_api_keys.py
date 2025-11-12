"""
API Key端点集成测试
Integration tests for API Key endpoints
"""

import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

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
from app.models.api_key import APIKey
from datetime import datetime


class TestAPIKeyEndpoints:
    """API Key端点测试"""
    
    @pytest.mark.asyncio
    async def test_create_api_key_success(self):
        """测试：创建API Key成功"""
        # Mock项目存在检查
        with patch("app.api.v1.endpoints.api_keys.ProjectsRepository") as mock_projects_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.exists = AsyncMock(return_value=True)
            mock_projects_repo.return_value = mock_repo_instance
            
            # Mock API Key创建
            with patch("app.api.v1.endpoints.api_keys.APIKeysRepository") as mock_apikeys_repo:
                mock_apikeys_instance = AsyncMock()
                mock_apikeys_instance.create = AsyncMock(return_value=MagicMock())
                mock_apikeys_repo.return_value = mock_apikeys_instance
                
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/projects/proj123/api-keys",
                        json={"name": "测试Key", "projectId": "proj123"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert "key" in data["data"]  # 应该返回明文key
                    assert "keyPrefix" in data["data"]
                    assert data["data"]["name"] == "测试Key"
    
    @pytest.mark.asyncio
    async def test_create_api_key_project_not_found(self):
        """测试：创建API Key失败（项目不存在）"""
        # Mock项目不存在
        with patch("app.api.v1.endpoints.api_keys.ProjectsRepository") as mock_projects_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.exists = AsyncMock(return_value=False)
            mock_projects_repo.return_value = mock_repo_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/projects/nonexistent/api-keys",
                    json={"name": "测试Key", "projectId": "nonexistent"}
                )
                
                assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_api_keys_success(self):
        """测试：获取API Key列表成功"""
        # Mock项目存在检查
        with patch("app.api.v1.endpoints.api_keys.ProjectsRepository") as mock_projects_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.exists = AsyncMock(return_value=True)
            mock_projects_repo.return_value = mock_repo_instance
            
            # Mock API Key列表
            with patch("app.api.v1.endpoints.api_keys.APIKeysRepository") as mock_apikeys_repo:
                mock_api_key = APIKey(
                    id="key123",
                    projectId="proj123",
                    name="测试Key",
                    key="hashed_key",
                    keyPrefix="abcd1234",
                    createdByUserId="user123",
                    createdAt=datetime.now(),
                )
                
                mock_apikeys_instance = AsyncMock()
                mock_apikeys_instance.get_by_project_id = AsyncMock(return_value=[mock_api_key])
                mock_apikeys_repo.return_value = mock_apikeys_instance
                
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/api/v1/projects/proj123/api-keys")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert len(data["data"]) == 1
                    assert data["data"][0]["name"] == "测试Key"
                    assert "key" not in data["data"][0]  # 不应返回完整key
                    assert "keyPrefix" in data["data"][0]
    
    @pytest.mark.asyncio
    async def test_delete_api_key_success(self):
        """测试：删除API Key成功"""
        # Mock API Key存在检查
        with patch("app.api.v1.endpoints.api_keys.APIKeysRepository") as mock_apikeys_repo:
            mock_api_key = APIKey(
                id="key123",
                projectId="proj123",
                name="测试Key",
                key="hashed_key",
                keyPrefix="abcd1234",
                createdByUserId="user123",
                createdAt=datetime.now(),
            )
            
            mock_apikeys_instance = AsyncMock()
            mock_apikeys_instance.get_by_id = AsyncMock(return_value=mock_api_key)
            mock_apikeys_instance.delete = AsyncMock(return_value=True)
            mock_apikeys_repo.return_value = mock_apikeys_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/projects/proj123/api-keys/key123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_api_key_not_found(self):
        """测试：删除API Key失败（不存在）"""
        # Mock API Key不存在
        with patch("app.api.v1.endpoints.api_keys.APIKeysRepository") as mock_apikeys_repo:
            mock_apikeys_instance = AsyncMock()
            mock_apikeys_instance.get_by_id = AsyncMock(return_value=None)
            mock_apikeys_repo.return_value = mock_apikeys_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/projects/proj123/api-keys/nonexistent")
                
                assert response.status_code == 404


class TestAPIKeyAuthentication:
    """API Key认证测试"""
    
    @pytest.mark.asyncio
    async def test_verify_api_key_success(self):
        """测试：API Key验证成功"""
        from app.api.dependencies import verify_api_key
        from app.core.security import generate_api_key, hash_api_key
        
        # 生成测试key
        plain_key = generate_api_key()
        key_hash = hash_api_key(plain_key)
        
        # Mock数据库查询
        with patch("app.api.dependencies.APIKeysRepository") as mock_repo:
            mock_api_key = APIKey(
                id="key123",
                projectId="proj123",
                name="测试Key",
                key=key_hash,
                keyPrefix="abcd1234",
                createdByUserId="user123",
                createdAt=datetime.now(),
                isActive=True,
            )
            
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_key_hash = AsyncMock(return_value=mock_api_key)
            mock_repo_instance.update_last_used = AsyncMock(return_value=True)
            mock_repo.return_value = mock_repo_instance
            
            # 验证
            project_id = await verify_api_key(f"Bearer {plain_key}")
            
            assert project_id == "proj123"
    
    @pytest.mark.asyncio
    async def test_verify_api_key_missing_header(self):
        """测试：缺少Authorization header"""
        from app.api.dependencies import verify_api_key
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)
        
        assert exc_info.value.status_code == 401
        assert "缺少Authorization header" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_api_key_invalid_format(self):
        """测试：Authorization header格式错误"""
        from app.api.dependencies import verify_api_key
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("InvalidFormat")
        
        assert exc_info.value.status_code == 401
        assert "格式错误" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_api_key_invalid_key(self):
        """测试：无效的API Key"""
        from app.api.dependencies import verify_api_key
        from fastapi import HTTPException
        
        # Mock数据库查询返回None
        with patch("app.api.dependencies.APIKeysRepository") as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_key_hash = AsyncMock(return_value=None)
            mock_repo.return_value = mock_repo_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key("Bearer invalid_key")
            
            assert exc_info.value.status_code == 401
            assert "无效的API Key" in exc_info.value.detail

