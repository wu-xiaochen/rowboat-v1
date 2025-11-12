"""
API集成测试
API integration tests
"""

import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

# 在导入app之前设置环境变量
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


class TestRootEndpoint:
    """根端点测试"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """测试：根端点返回欢迎信息"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "欢迎使用" in data["message"]
            assert data["data"]["name"] == "测试应用"
            assert data["data"]["version"] == "1.0.0"


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    @pytest.mark.asyncio
    async def test_health_check_all_services_ok(self):
        """测试：健康检查（所有服务正常）"""
        # Mock数据库连接检查
        with patch("app.api.v1.endpoints.health.check_mongodb_connection", new=AsyncMock(return_value=True)), \
             patch("app.api.v1.endpoints.health.check_redis_connection", new=AsyncMock(return_value=True)), \
             patch("app.api.v1.endpoints.health.check_qdrant_connection", return_value=True):
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["status"] == "healthy"
                assert data["data"]["services"]["mongodb"] == "connected"
                assert data["data"]["services"]["redis"] == "connected"
    
    @pytest.mark.asyncio
    async def test_health_check_with_failures(self):
        """测试：健康检查（部分服务失败）"""
        # Mock数据库连接检查（Redis失败）
        with patch("app.api.v1.endpoints.health.check_mongodb_connection", new=AsyncMock(return_value=True)), \
             patch("app.api.v1.endpoints.health.check_redis_connection", new=AsyncMock(return_value=False)), \
             patch("app.api.v1.endpoints.health.check_qdrant_connection", return_value=True):
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["status"] == "degraded"
                assert data["data"]["services"]["redis"] == "disconnected"
    
    @pytest.mark.asyncio
    async def test_ping_endpoint(self):
        """测试：ping端点"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/ping")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["ping"] == "pong"


class TestInfoEndpoint:
    """API信息端点测试"""
    
    @pytest.mark.asyncio
    async def test_get_api_info(self):
        """测试：获取API信息"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/info")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == "测试应用"
            assert data["data"]["version"] == "1.0.0"
            assert data["data"]["api_version"] == "v1"
            assert "llm_provider" in data["data"]
            assert "embedding_provider" in data["data"]

