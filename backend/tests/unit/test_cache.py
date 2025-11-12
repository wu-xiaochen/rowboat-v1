"""
缓存服务单元测试
Unit tests for Cache Service
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

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

from app.core.cache import CacheService, get_cache_service


class TestCacheService:
    """缓存服务测试"""
    
    @pytest.fixture
    def cache_service(self):
        """创建CacheService实例"""
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service):
        """测试：缓存未命中"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=None)
            mock_redis.return_value = mock_client
            
            result = await cache_service.get("test_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_cache_hit_string(self, cache_service):
        """测试：缓存命中（字符串）"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value="test_value")
            mock_redis.return_value = mock_client
            
            result = await cache_service.get("test_key")
            assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_cache_hit_json(self, cache_service):
        """测试：缓存命中（JSON）"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            test_data = {"key": "value", "number": 123}
            mock_client.get = AsyncMock(return_value=json.dumps(test_data))
            mock_redis.return_value = mock_client
            
            result = await cache_service.get("test_key")
            assert result == test_data
    
    @pytest.mark.asyncio
    async def test_set_cache_string(self, cache_service):
        """测试：设置缓存（字符串）"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            mock_client.setex = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client
            
            result = await cache_service.set("test_key", "test_value", ttl=300)
            assert result is True
            mock_client.setex.assert_called_once_with("test_key", 300, "test_value")
    
    @pytest.mark.asyncio
    async def test_set_cache_dict(self, cache_service):
        """测试：设置缓存（字典）"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            mock_client.setex = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client
            
            test_data = {"key": "value", "number": 123}
            result = await cache_service.set("test_key", test_data, ttl=300)
            assert result is True
            # 验证JSON序列化
            call_args = mock_client.setex.call_args
            assert call_args[0][0] == "test_key"
            assert call_args[0][1] == 300
            assert json.loads(call_args[0][2]) == test_data
    
    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_service):
        """测试：删除缓存"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            mock_client.delete = AsyncMock(return_value=1)
            mock_redis.return_value = mock_client
            
            result = await cache_service.delete("test_key")
            assert result is True
            mock_client.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache_service):
        """测试：按模式删除缓存"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            # Mock scan_iter
            async def mock_scan_iter(match):
                keys = ["project:1", "project:2", "project:3"]
                for key in keys:
                    if match.replace("*", "") in key:
                        yield key
            
            mock_client.scan_iter = mock_scan_iter
            mock_client.delete = AsyncMock(return_value=3)
            mock_redis.return_value = mock_client
            
            result = await cache_service.delete_pattern("project:*")
            assert result == 3
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, cache_service):
        """测试：缓存错误处理（不应影响主流程）"""
        with patch("app.core.cache.get_redis_client") as mock_redis:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Redis error"))
            mock_redis.return_value = mock_client
            
            # 应该返回None而不是抛出异常
            result = await cache_service.get("test_key")
            assert result is None
    
    def test_get_project_key(self, cache_service):
        """测试：获取项目缓存键"""
        key = cache_service.get_project_key("proj123")
        assert key == "project:proj123"
    
    def test_get_api_key_key(self, cache_service):
        """测试：获取API Key缓存键"""
        key = cache_service.get_api_key_key("key_hash_123")
        assert key == "api_key:key_hash_123"
    
    def test_get_conversation_key(self, cache_service):
        """测试：获取对话缓存键"""
        key = cache_service.get_conversation_key("conv123")
        assert key == "conversation:conv123"
    
    def test_get_cache_service_singleton(self):
        """测试：缓存服务单例模式"""
        service1 = get_cache_service()
        service2 = get_cache_service()
        assert service1 is service2

