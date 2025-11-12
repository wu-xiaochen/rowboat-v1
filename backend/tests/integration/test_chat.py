"""
聊天端点集成测试
Integration tests for Chat endpoints
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
from app.models.schemas import Project, Workflow, Conversation, Turn, Message, UserMessage, AssistantMessage


class TestChatEndpoints:
    """聊天端点测试"""
    
    @pytest.mark.asyncio
    async def test_chat_non_streaming_success(self):
        """测试：非流式聊天成功"""
        # Mock对话服务
        with patch("app.api.v1.endpoints.chat.get_chat_service") as mock_chat_service:
            mock_service_instance = AsyncMock()
            
            # Mock对话回合事件
            from app.models.chat_schemas import DoneTurnEvent, Turn, TurnInput, ApiReason
            
            mock_turn = Turn(
                id="turn123",
                reason=ApiReason(type="api"),
                input=TurnInput(
                    messages=[
                        UserMessage(role="user", content="你好")
                    ]
                ),
                output=[
                    AssistantMessage(
                        role="assistant",
                        content="你好！有什么可以帮助你的吗？",
                        response_type="external"
                    )
                ],
                created_at=datetime.now().isoformat()
            )
            
            async def mock_run_turn(*args, **kwargs):
                # 模拟流式事件
                yield DoneTurnEvent(
                    type="done",
                    conversation_id="conv123",
                    turn=mock_turn
                )
            
            mock_service_instance.run_turn = mock_run_turn
            mock_chat_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(
                    "/api/v1/proj123/chat",
                    json={
                        "messages": [
                            {"role": "user", "content": "你好"}
                        ],
                        "stream": False
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "turn" in data["data"]
                assert len(data["data"]["turn"]["output"]) > 0
    
    @pytest.mark.asyncio
    async def test_chat_streaming_success(self):
        """测试：流式聊天成功"""
        # Mock对话服务
        with patch("app.api.v1.endpoints.chat.get_chat_service") as mock_chat_service:
            mock_service_instance = AsyncMock()
            
            # Mock流式响应
            from app.models.chat_schemas import MessageTurnEvent, DoneTurnEvent
            
            async def mock_run_turn(*args, **kwargs):
                # 模拟流式事件
                yield MessageTurnEvent(
                    type="message",
                    data=AssistantMessage(
                        role="assistant",
                        content="你好",
                        response_type="external"
                    )
                )
                yield DoneTurnEvent(type="done")
            
            mock_service_instance.run_turn = mock_run_turn
            mock_chat_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(
                    "/api/v1/proj123/chat",
                    json={
                        "messages": [
                            {"role": "user", "content": "你好"}
                        ],
                        "stream": True
                    }
                )
                
                assert response.status_code == 200
                assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_chat_project_not_found(self):
        """测试：聊天失败（项目不存在）"""
        # Mock对话服务返回错误事件
        with patch("app.api.v1.endpoints.chat.get_chat_service") as mock_chat_service:
            mock_service_instance = AsyncMock()
            
            from app.models.chat_schemas import ErrorTurnEvent
            
            async def mock_run_turn(*args, **kwargs):
                # 模拟返回错误事件（项目不存在）
                yield ErrorTurnEvent(
                    type="error",
                    error="项目 nonexistent 不存在",
                    is_billing_error=False
                )
            
            mock_service_instance.run_turn = mock_run_turn
            mock_chat_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/nonexistent/chat",
                    json={
                        "messages": [
                            {"role": "user", "content": "你好"}
                        ],
                        "stream": False
                    }
                )
                
                # 当返回错误事件时，端点会抛出500错误
                assert response.status_code == 500
                data = response.json()
                assert "项目 nonexistent 不存在" in data.get("detail", "")
    
    @pytest.mark.asyncio
    async def test_chat_invalid_request(self):
        """测试：聊天失败（无效请求）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 缺少必需字段
            response = await client.post(
                "/api/v1/proj123/chat",
                json={}
            )
            
            assert response.status_code == 422  # Validation error

