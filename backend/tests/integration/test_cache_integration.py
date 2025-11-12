"""
缓存集成测试
Integration tests for Cache functionality in Repositories
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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

from app.repositories.projects import ProjectsRepository
from app.repositories.api_keys import APIKeysRepository
from app.models.schemas import Project, Workflow
from app.models.api_key import APIKey


class TestProjectsRepositoryCache:
    """ProjectsRepository缓存测试"""
    
    @pytest.mark.asyncio
    async def test_get_by_id_cache_hit(self):
        """测试：从缓存获取项目"""
        repo = ProjectsRepository()
        
        # Mock缓存服务
        with patch.object(repo.cache_service, 'get') as mock_get:
            cached_project = {
                "id": "proj123",
                "name": "测试项目",
                "createdAt": datetime.now().isoformat(),
                "createdByUserId": "user123",
                "secret": "secret123",
                "draftWorkflow": {"agents": [], "prompts": [], "tools": []},
                "liveWorkflow": {"agents": [], "prompts": [], "tools": []},
            }
            mock_get.return_value = cached_project
            
            # Mock数据库（不应被调用）
            with patch("app.repositories.projects.get_mongodb_db") as mock_db:
                result = await repo.get_by_id("proj123")
                
                # 验证从缓存获取
                assert result is not None
                assert result.id == "proj123"
                # 验证数据库未被调用
                mock_db.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_by_id_cache_miss(self):
        """测试：缓存未命中，从数据库获取并缓存"""
        repo = ProjectsRepository()
        
        # Mock缓存服务（未命中）
        with patch.object(repo.cache_service, 'get') as mock_get, \
             patch.object(repo.cache_service, 'set') as mock_set:
            mock_get.return_value = None
            
            # Mock数据库
            with patch("app.repositories.projects.get_mongodb_db") as mock_db:
                mock_collection = AsyncMock()
                mock_doc = {
                    "id": "proj123",
                    "name": "测试项目",
                    "createdAt": datetime.now(),
                    "createdByUserId": "user123",
                    "secret": "secret123",
                    "draftWorkflow": {"agents": [], "prompts": [], "tools": []},
                    "liveWorkflow": {"agents": [], "prompts": [], "tools": []},
                }
                mock_collection.find_one = AsyncMock(return_value=mock_doc)
                mock_db.return_value = {"projects": mock_collection}
                
                result = await repo.get_by_id("proj123")
                
                # 验证结果
                assert result is not None
                # 验证已存入缓存
                mock_set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_cache_invalidation(self):
        """测试：更新项目时清除缓存"""
        repo = ProjectsRepository()
        
        # Mock数据库更新
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
            mock_collection.find_one = AsyncMock(return_value={
                "id": "proj123",
                "name": "新项目名",
                "createdAt": datetime.now(),
                "createdByUserId": "user123",
                "secret": "secret123",
                "draftWorkflow": {"agents": [], "prompts": [], "tools": []},
                "liveWorkflow": {"agents": [], "prompts": [], "tools": []},
            })
            mock_db.return_value = {"projects": mock_collection}
            
            # Mock缓存服务
            with patch.object(repo.cache_service, 'delete') as mock_delete:
                project = Project(
                    id="proj123",
                    name="新项目名",
                    created_at=datetime.now(),
                    created_by_user_id="user123",
                    secret="secret123",
                    draft_workflow=Workflow(agents=[], prompts=[], tools=[]),
                    live_workflow=Workflow(agents=[], prompts=[], tools=[]),
                )
                
                await repo.update("proj123", project)
                
                # 验证缓存被清除
                mock_delete.assert_called_once_with("project:proj123")


class TestAPIKeysRepositoryCache:
    """APIKeysRepository缓存测试"""
    
    @pytest.mark.asyncio
    async def test_get_by_key_hash_cache_hit(self):
        """测试：从缓存获取API Key"""
        repo = APIKeysRepository()
        
        # Mock缓存服务
        with patch.object(repo.cache_service, 'get') as mock_get:
            cached_key = {
                "id": "key123",
                "projectId": "proj123",
                "name": "测试Key",
                "key": "hashed_key",
                "keyPrefix": "abcd1234",
                "createdByUserId": "user123",
                "createdAt": datetime.now().isoformat(),
                "isActive": True,
            }
            mock_get.return_value = cached_key
            
            # Mock数据库（不应被调用）
            with patch("app.repositories.api_keys.get_mongodb_db") as mock_db:
                result = await repo.get_by_key_hash("hashed_key")
                
                # 验证从缓存获取
                assert result is not None
                assert result.id == "key123"
                # 验证数据库未被调用
                mock_db.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_last_used_cache_invalidation(self):
        """测试：更新最后使用时间时清除缓存"""
        repo = APIKeysRepository()
        
        # Mock数据库
        with patch("app.repositories.api_keys.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_collection.find_one = AsyncMock(return_value={
                "id": "key123",
                "key": "hashed_key",
            })
            mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
            mock_db.return_value = {"api_keys": mock_collection}
            
            # Mock缓存服务
            with patch.object(repo.cache_service, 'delete') as mock_delete:
                await repo.update_last_used("key123")
                
                # 验证缓存被清除
                mock_delete.assert_called_once_with("api_key:hashed_key")

