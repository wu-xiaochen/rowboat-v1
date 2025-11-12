"""
数据库连接测试
Tests for database connections
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.database import (
    get_mongodb_client,
    get_mongodb_db,
    get_redis_client,
    get_qdrant_client,
    check_mongodb_connection,
    check_redis_connection,
    check_qdrant_connection,
    close_mongodb_connection,
    close_redis_connection,
    close_qdrant_connection,
)


class TestMongoDBConnection:
    """MongoDB连接测试"""
    
    @pytest.mark.asyncio
    async def test_get_mongodb_client(self, monkeypatch):
        """测试：获取MongoDB客户端"""
        # 设置环境变量
        test_env_vars = {
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 清除单例
        from app.core import database
        database._mongodb_client = None
        
        client = await get_mongodb_client()
        
        assert client is not None
        
        # 清理
        await close_mongodb_connection()
    
    @pytest.mark.asyncio
    async def test_get_mongodb_db(self, monkeypatch):
        """测试：获取MongoDB数据库实例"""
        test_env_vars = {
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 清除单例
        from app.core import database
        database._mongodb_client = None
        database._mongodb_db = None
        
        db = await get_mongodb_db()
        
        assert db is not None
        assert db.name == "testdb"
        
        # 清理
        await close_mongodb_connection()
    
    @pytest.mark.asyncio
    async def test_check_mongodb_connection_success(self, monkeypatch):
        """测试：检查MongoDB连接成功"""
        test_env_vars = {
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 清除单例
        from app.core import database
        database._mongodb_client = None
        
        # Mock ping命令
        with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.admin.command = AsyncMock(return_value={"ok": 1})
            mock_client.return_value = mock_instance
            
            # 重新注入mock的客户端
            database._mongodb_client = mock_instance
            
            result = await check_mongodb_connection()
            
            assert result is True
        
        # 清理
        await close_mongodb_connection()


class TestRedisConnection:
    """Redis连接测试"""
    
    @pytest.mark.asyncio
    async def test_get_redis_client(self, monkeypatch):
        """测试：获取Redis客户端"""
        test_env_vars = {
            "REDIS_URL": "redis://test:6379",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 清除单例
        from app.core import database
        database._redis_client = None
        
        client = await get_redis_client()
        
        assert client is not None
        
        # 清理
        await close_redis_connection()
    
    @pytest.mark.asyncio
    async def test_check_redis_connection_success(self, monkeypatch):
        """测试：检查Redis连接成功"""
        test_env_vars = {
            "REDIS_URL": "redis://test:6379",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 清除单例
        from app.core import database
        database._redis_client = None
        
        # Mock ping命令
        with patch("redis.asyncio.Redis.from_url") as mock_redis:
            mock_instance = AsyncMock()
            mock_instance.ping = AsyncMock(return_value=True)
            mock_instance.close = AsyncMock()
            mock_redis.return_value = mock_instance
            
            # 重新注入mock的客户端
            database._redis_client = mock_instance
            
            result = await check_redis_connection()
            
            assert result is True
        
        # 清理
        await close_redis_connection()


class TestQdrantConnection:
    """Qdrant连接测试"""
    
    def test_get_qdrant_client(self, monkeypatch):
        """测试：获取Qdrant客户端"""
        test_env_vars = {
            "QDRANT_URL": "http://test:6333",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 清除单例
        from app.core import database
        database._qdrant_client = None
        
        client = get_qdrant_client()
        
        assert client is not None
        
        # 清理
        close_qdrant_connection()
    
    def test_check_qdrant_connection_success(self, monkeypatch):
        """测试：检查Qdrant连接成功"""
        test_env_vars = {
            "QDRANT_URL": "http://test:6333",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 清除单例
        from app.core import database
        database._qdrant_client = None
        
        # Mock get_collections
        with patch("qdrant_client.QdrantClient") as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.get_collections = MagicMock(return_value=MagicMock(collections=[]))
            mock_qdrant.return_value = mock_instance
            
            # 重新注入mock的客户端
            database._qdrant_client = mock_instance
            
            result = check_qdrant_connection()
            
            assert result is True
        
        # 清理
        close_qdrant_connection()

